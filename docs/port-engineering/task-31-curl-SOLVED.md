# Task 31 (Curl): SOLVED — 6/6 bit-exact parity

Date: 2026-08-12
Author: integration owner

Supersedes the "undiagnosed parity failure" and "root cause = tanh
implementation" framings. Three distinct causes, found in order. The port's
structure was correct throughout.

## Cause 1 — the oracle never bound `time` (4 of 6 apparent failures)

`createCanonicalBindings` assigns `time: f32(time)` *after* spreading
`...uniforms`, so a `time` passed inside `uniforms` is discarded.
`curl_oracle_generator.mjs:190` passes it that way, so every frozen case is a
`time = 0` render. Detail in `task-31-curl-oracle-defect.md`.

The same applies to `globalTime`, `deltaTime`, `frame`, `resolution`,
`fullResolution`, `tileOffset`, `aspect`, `aspectRatio`.

## Cause 2 — my own probe bug (1 of 6)

The parity probe hardcoded `tileOffset=(0,0)` / `fullResolution=(w,h)` for all
cases, while `seed7-tiled-midtime` needs `[3,2]`/`[13,11]`.

## Cause 3 — THE REAL PORT BUG: unary functions narrow their argument

Once 1 and 2 were corrected, one genuine divergence remained: a single pixel,
one lane, 2 ULP. Layer-by-layer comparison against the live JS factory showed
`p`, `simplex3D`, `fbmSimplex3D` and `curlNoise3D` all **bit-identical**, so the
fault was strictly in the tail.

The JS canonical kernel scalarizes the vector expression:

```js
var cpu_vector_assignment_0 = new $runtime.PooledFloat32Array([
  (tanh(curl[0] * intensity)) * 0.5 + 0.5, ... ])
```

`curl[0] * intensity` is computed in **Number** (double) and handed to
`Math.tanh` unnarrowed; only the *result* is narrowed (`#unary` returns
`F32(operation(value))`).

The C++ runtime's unary-vector macro does the opposite:

```cpp
#define NOISEMAKER_GLSL_UNARY_VECTOR(name) \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const Vec<N,float>& value) {...} \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const FloatExpr<N>& value) { \
    return glsl::name(Vec<N,float>(value)); }   // <-- narrows the ARGUMENT
```

The `FloatExpr` overload materialises the lazy double expression into
`Vec<N,float>` first, so the function sees an f32-rounded argument. Different
input bits, different output bits.

Fixing only that — evaluating each lane's double argument directly, narrowing
only the result — takes Curl from 4/6 to **6/6 bit-exact**.

```
MATCH default-seed0-time0
MATCH seed7-tiled-midtime
MATCH negative-seed-drives-negative-mod-operands
MATCH negative-intensity-flips-tanh-sign
MATCH large-seed-negative-scale-negative-speed
MATCH two-pi-time-near-identity-intensity
6/6
```

### Why 130 shipped programs never exposed this

The argument narrowing is only observable when the JS emitter **scalarizes** a
vector expression, because that is when JS keeps the operand in Number
precision. When JS calls the vector form on a `Float32Array`, it narrows the
operand too and the two agree. Curl is simply the first ported program whose
generated JS scalarizes a unary applied to a non-materialised product.

**This affects every unary in the macro** — `abs`, `atan`, `cos`, `exp`,
`floor`, `radians`, `sign`, `sin`, `sqrt`, `fract` — not just `tanh`. Any future
program with the same shape will hit it.

## Was `tanh` itself wrong? Partly, and it still needs fixing

Separately measured, `std::tanh` disagrees with V8's `Math.tanh` by 1 ULP on
**16.2%** of sampled doubles (V8 uses its own fdlibm port). An fdlibm `tanh`
was written and verified: **0/4000** disagreements on a uniform sweep and
7/30000 (0.023%) on a randomised sweep, versus `std::tanh`'s 16.2%.

For these six Curl cases the argument-narrowing fix alone was sufficient. But
the `std::tanh` gap is real and will surface elsewhere, so the fdlibm port
should still land. Measured disagreement versus V8, inputs verified identical:

| function | disagreement |
|---|---|
| `tanh` | 16.2% |
| `exp` | 10.5% |
| `sin` | 4.2% |
| `cos` | 3.5% |
| `sqrt`, `pow` | 0% |

The residual 0.023% in the fdlibm `tanh` traces to `expm1`: my port is 0.090%
off V8 versus `std::expm1`'s 12.4%, and a high-precision check shows V8 is the
more accurate of the two, so my `expm1` transcription is slightly off. All
fdlibm constants were verified bit-exact, so the discrepancy is in the
algorithm body, not the tables.

## Two harness errors I made (recorded so they are not repeated)

1. A sweep reported 131/400 `tanh` disagreements and, impossibly, 158/400 for
   `sqrt`. Cause: a helper returning `static char buf[32]`, so all seven calls
   in one `printf` shared a buffer. `sqrt` is IEEE-correctly-rounded, so any
   harness reporting `sqrt` disagreement is broken — a useful canary.
2. Ad-hoc probes omitted `-ffp-contract=off`. Without it clang fuses
   `-4.0 + i*0.02` into an FMA and even the *inputs* stop matching JS. Any
   comparison harness must use the library's flags.

## The blanket runtime fix DOES NOT WORK — tested and reverted

Changing the macro's `FloatExpr` overload to stop narrying its argument was
attempted in the repository and **broke three previously-passing programs**:

```text
FAIL typed_math_slice_sixteen_external_oracles_are_repeatable        (filter/lensFlare)
FAIL typed_task14_all_thirty_external_oracles_are_exact_...          (filter/tetraCosine hsv_backward)
FAIL typed_task21_degauss_external_oracles_are_exact_...             (filter/degauss)
```

Reverted immediately; the tree is green again at 150/150 with byte-identical
generated output.

**What this proves:** the correct narrowing is *context-dependent*, and the
C++ runtime alone cannot decide it.

- Where the JS generator emits the **vector** form — `sin(someFloat32Array)` —
  the operand is already f32, so narrowing is correct.
- Where the JS generator **scalarizes** — `tanh(curl[0] * intensity)` inside a
  `new PooledFloat32Array([...])` — the operand stays Number, so narrowing is
  wrong.

The existing overload split (`Vec<N,float>` versus `FloatExpr<N>`) looks like
it should encode exactly that distinction, and for Curl it does. But for
lensFlare, tetraCosine and degauss the C++ emitter passes a `FloatExpr` at a
site where the JS generator materialised an array first. So the two generators
disagree about **where values are materialised**, and that — not the runtime
header — is the real defect.

## Required next steps

1. **Align materialisation points between the two generators.** Determine, for
   each failing site in lensFlare / tetraCosine / degauss, why the C++ emitter
   produces a lazy `FloatExpr` where the JS generator materialises a
   `Float32Array`. Fix the *emitter* so its materialisation decisions mirror
   the JS generator's, then the existing overload split becomes correct and
   both Curl and the three regressions pass simultaneously. Do NOT change the
   runtime macro in isolation — that trade is a strict regression (1 program
   gained, 3 lost).
   Useful starting point: `emit_typed_cpp.py` already has
   `_ordinary_return_scalar_map_chain` logic that decides when to emit
   `glsl::FloatExpr<N>` versus a materialised `Vec`; that is where the
   divergence most likely lives.

### What the JS generator actually does (measured, not assumed)

The JS side is produced by
`noisemaker-for-cpu/scripts/upstream/compile-glsl.js`. Two observed behaviours:

- **Vector unary argument → materialise, then narrow.** e.g. degauss emits
  `floor(new $runtime.PooledFloat32Array([x[0]*k, x[1]*k, x[2]*k]))`. The
  operand is f32 before the unary runs, so the C++ `Vec<N,float>(value)`
  narrowing is *correct* here. This is why the blanket runtime change broke
  degauss, lensFlare and tetraCosine.
- **Scalarised assignment → no argument narrowing.** Curl emits
  `var cpu_vector_assignment_0 = new $runtime.PooledFloat32Array([
   (tanh(curl[0] * intensity)) * 0.5 + 0.5, ...])`, so `tanh` receives a
  Number and only the *result* is narrowed.

**Correction to an earlier guess:** the `cpu_vector_assignment_N` temporary is
NOT produced by `preserveVectorAssignmentReads` (compile-glsl.js:204). That
transform requires the RHS to begin with `vecN(` *and* to reference
`target.[xyzwrgba]`; Curl's `curl = tanh(curl * intensity) * 0.5 + 0.5;`
satisfies neither. The scalarisation therefore comes from a different stage of
that pipeline, and identifying which one is the first task for whoever
continues — the emitter must reproduce that exact decision, not an
approximation of it.
2. Land the fdlibm `tanh` (and finish `expm1`) so transcendentals are
   bit-exact rather than coincidentally close.
3. Fix `curl_oracle_generator.mjs` to bind `time` top-level and re-freeze
   `curl-oracles.json`.
4. Audit every other oracle for the same `time`-binding defect.
5. Then land Curl: profile, both authorities, runtime and slice registration
   are already written and verified.

## Where the scalarisation really comes from — and the right fix

`compile-glsl.js:90-101` delegates to the third-party **`glsl-transpiler`**
package with `optimize: true`:

```js
const compile = GLSL({ version: '300 es', preprocess, optimize: true, ... })
```

The per-lane scalarisation that gives `tanh` an unnarrowed Number operand is
that library's optimiser output, not a local transform. The subsequent local
passes (`preserveVectorAssignmentReads`, `poolLocalVectors`, etc.) only adjust
what it produced.

**Consequence for this port's architecture:** the parity target is not "the
GLSL semantics" — it is *whatever `glsl-transpiler` chose to materialise*.
Narrowing points are therefore a property of a third-party optimiser's
heuristics, and no amount of reasoning from the GLSL source alone will predict
them.

Two viable strategies:

1. **Reverse-engineer the heuristics** into the C++ emitter so its
   materialisation decisions match. Highest fidelity, but it means tracking an
   undocumented third-party optimiser, and any upgrade of that package
   silently changes the target.
2. **Per-program compatibility transform** — the project's existing, proven
   mechanism for exactly this class of JS-quirk matching. `typed_slice.json`
   already carries `compatibility_transforms` for seven programs
   (`coalesce-uv-alias-v1`, `corrupt-sample-uv-alias-v1`,
   `shape-mask-sequential-lanes-v1`, `polygon-zero-smoothing-v1`, and the
   refract / CRT / sacred-geometry entries). Curl would get e.g.
   `curl-scalarized-unary-assignment-v1`, authenticated per-program like every
   other capability, instructing the emitter to lower that one assignment
   per-lane.

**Strategy 2 is recommended.** It is consistent with how every other
JS-behaviour divergence in this project has been handled, it is
identity-scoped so it cannot regress the 130 passing programs (the blanket
runtime change demonstrably did regress three), and it keeps the fix
reviewable and hash-authenticated. Reverse-engineering a third-party optimiser
is a research project; a per-program transform is a task.

The exact lowering is already proven: emitting the assignment per lane with the
unary receiving the unnarrowed double operand yields **6/6 bit-exact**.

## Current tree state

Green and unchanged from accepted Task 30:

```text
generate_typed_slice --check   130 programs, typed_slice.cpp 5765f863…
native                         150/150 PASS, exit 0
glsl_runtime.hpp               17fe7a61… (blanket change reverted)
```

Curl's profile, both authority wirings, the `tanh`/wide-`mod` runtime and the
fdlibm `tanh` prototype are all written and verified; only the emitter-side
lowering decision remains before Curl can land.

---

## LANDED: Curl is ported, 6/6 bit-exact via the real catalog binder

The identity-scoped fix works where the blanket one regressed three programs.

### The fix as shipped

1. **`glsl_runtime.hpp`** gained two things: a scalar
   `tanh(double) -> float` (house convention, narrows only the result), and
   `tanh_lanewise(FloatExpr<N>)`, which evaluates each lane's **double**
   operand directly instead of materialising the argument into
   `Vec<N,float>` first. Both `requires(N == 3)`. The existing `tanh` is
   unchanged, so the 130 previously-passing programs are untouched — this is
   exactly why the blanket macro change failed and this one does not.

2. **`emit_typed_cpp.py`** emits `glsl::tanh_lanewise(...)` for Curl's one
   authenticated node, reached only through the profile's node-identity check.

3. **`curl_oracle_generator.mjs`** now binds `time` as a top-level option, and
   `curl-oracles.json` was regenerated. Six previously-frozen expectations were
   wrong and are corrected:

   | case | old (time=0 artifact) | corrected |
   |---|---|---|
   | seed7-tiled-midtime | `a3da792e…` | `e6f49b49…` |
   | negative-intensity-… | `495aca12…` | `311e9b96…` |
   | large-seed-… | `a138c72b…` | `aa573876…` |
   | two-pi-time-… | `865cfbf1…` | `7a006260…` |

   Oracle now `dc992d217dda4e908b33826dde6da744347a9ff5c5a7a7befd3a43c96949001c`,
   `--check` green twice for determinism, vendored to
   `tests/oracles/task-31-oracles.json`.

### Verification

```text
6/6 bit-exact through noisemaker::generated::bind_synth_curl_curl
   default-seed0-time0                          MATCH
   seed7-tiled-midtime                          MATCH   (tiled: [3,2]/[13,11])
   negative-seed-drives-negative-mod-operands   MATCH
   negative-intensity-flips-tanh-sign           MATCH
   large-seed-negative-scale-negative-speed     MATCH
   two-pi-time-near-identity-intensity          MATCH

check_corpus / check_semantics / generate_kernels   exit 0
generate_typed_slice --check                        131 programs
native                                              150/150 PASS, exit 0
capability vocabulary                               44, `tanh` absent
```

State: **131 typed / 133 public / 79 unported / 212 corpus**,
typed-list `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`.

### Still outstanding for Curl

- Full Python discovery (running) will need the usual live-count integration
  repair to 131/133/79 plus a `Task31CurlVectorMathTests` class.
- The fdlibm `tanh` prototype (0/4000 versus `std::tanh`'s 16.2% disagreement
  with V8) is **not** shipped. Curl passes without it because these six cases
  do not hit a disagreeing input, which is luck rather than a guarantee. It
  should still land, together with finishing `expm1` (currently 0.090% off V8).
- `exp` disagrees with V8 at 10.5% and no shipped program stresses it yet.
