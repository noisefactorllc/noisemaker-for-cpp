# Screen-space derivatives (dFdx/dFdy/fwidth) — architecture prototype

Status: **prototype / design document only**. Nothing under
`.` or
`../noisemaker-for-cpu` was modified. All files referenced
below as "read" were opened read-only. No `git`, no cmake build, no Python
test suite was run against either repo.

All line numbers below were read directly from
`../noisemaker-for-cpu/src/csl/glsl-runtime.js` on
2026-08-12 and are quoted verbatim from that file.

---

## 1. The reference algorithm, exactly

### 1.1 Dispatch (lines 408-410)

```js
dFdx: (value) => this.#derivative(value, 'x'),
dFdy: (value) => this.#derivative(value, 'y'),
fwidth: (value) => this.#derivative(value, 'width'),
```

All three builtins funnel into one private method, `#derivative(value, kind)`,
differing only in which of three "kinds" they request.

### 1.2 `#derivative(value, kind)` (lines 448-474)

```js
#derivative(value, kind) {
    const index = this.derivativeIndex++
    if (this.derivativeMode === 'record') {
      this.derivativeRecords[index] = isVector(value) ? Array.from(value) : value
      if (!isVector(value)) return 0
      const out = this.alloc(value.length)
      out.fill(0)
      return out
    }
    if (this.derivativeMode === 'replay') {
      const derivatives = this.derivativeValues[index]
      if (derivatives !== undefined) {
        const selected = kind === 'x' ? derivatives.x : kind === 'y' ? derivatives.y : derivatives.width
        ...
      }
    }
    // fallback (mode === 'approximate', or no wrapping at all)
    if (!isVector(value)) return F32(kind === 'x' ? this.inverseWidth : kind === 'y' ? this.inverseHeight : this.inverseWidth + this.inverseHeight)
    ...
}
```

Key facts:
- **`derivativeIndex` is the ordinal.** It increments on *every* call to
  `#derivative` regardless of `kind`, and is reset to `0` in `beginPixel()`
  (line 138), which every generated kernel calls as its first statement. So
  the ordinal is a per-kernel-invocation call-site counter, not a per-source-line
  identity — call site N is "the N-th dFdx/dFdy/fwidth call executed this
  invocation," in execution order.
- **Record mode**: stores the call's *input value* (not a derivative) at
  `derivativeRecords[index]` and returns a zero-filled dummy of the same
  shape. The kernel keeps running with a bogus (zero) return value from this
  call, which is fine because in record mode nothing downstream of the
  probe is observed except the recorded input.
- **Replay mode**: looks up `derivativeValues[index]` (populated by
  `wrapDerivatives`, see below) and returns the `x`, `y`, or `width` field
  per `kind`, narrowed through `F32` for scalars.
- **Fallback** (`mode === 'approximate'`, the state `wrapDerivatives` leaves
  the runtime in after replay finishes, and also the behavior for a kernel
  that calls a derivative builtin *without* being wrapped at all): a
  constant based on `inverseWidth`/`inverseHeight` (`1/resolution`), **not**
  an actual derivative. This is a legitimate GLSL fallback (some
  implementations return a coarse constant when true derivatives aren't
  available) but is never what a wrapped, `usesDerivatives`-flagged kernel
  actually returns during real rendering — only relevant if a kernel is
  invoked directly without going through `wrapDerivatives`.

### 1.3 `wrapDerivatives(kernel)` (lines 476-546)

This is the actual per-pixel driver. Applied only when `factory.usesDerivatives`
is truthy (line 554: `if (factory.usesDerivatives) kernel = runtime.wrapDerivatives(kernel)`).

**Probe** (lines 479-491): runs the *entire* kernel body once, in `'record'`
mode, at one fragment coordinate:

```js
const probe = (context, x, y) => {
  const fragCoord = new Float32Array([x, y])
  const probeContext = { ...context, fragCoord, uv: new Float32Array([x / resolution[0], y / resolution[1]]) }
  this.derivativeMode = 'record'
  this.derivativeRecords = []
  kernel(probeContext, temporary)
  return this.derivativeRecords
}
```
Every context field except `fragCoord`/`uv` is copied unchanged from the real
pixel's context (`...context`) — same `time`, `seed`, `frame`, `resolution`,
etc. The probe's output color (`temporary`) is discarded; only the recorded
input values matter.

**Quad geometry** (lines 493-503):
```js
const pixelX = Math.floor(context.fragCoord[0] - 0.5)
const pixelY = Math.floor(context.fragCoord[1] - 0.5)
const quadX = pixelX >> 1
const quadY = pixelY >> 1
const key = `${quadX}:${quadY}`
let lanes = cache.get(key)
if (!lanes) {
  const x0 = quadX * 2 + 0.5
  const y0 = quadY * 2 + 0.5
  lanes = [probe(context, x0, y0), probe(context, x0 + 1, y0), probe(context, x0, y0 + 1), probe(context, x0 + 1, y0 + 1)]
  cache.set(key, lanes)
}
```
`pixelX`/`pixelY` recover the integer pixel index from a `n+0.5`-centered
`fragCoord` (standard OpenGL convention). `x0,y0` are exactly the fragCoord of
the quad's bottom-left member pixel; the four probes are evaluated at exactly
the four member pixels' own fragCoords — **no bounds check against the
canvas**. At the right/bottom image edge, `x0+1`/`y0+1` can legitimately be
one pixel past the canvas edge; the probe still runs there (this mirrors real
GPU "helper invocation" behavior for edge fragments in a 2x2 quad and must
not be special-cased away).

**Corner-to-derivative mapping** (lines 505-533):
```js
const xParity = pixelX & 1
const yParity = pixelY & 1
const left = lanes[yParity * 2]
const right = lanes[yParity * 2 + 1]
const bottom = lanes[xParity]
const top = lanes[xParity + 2]
```
With `lanes = [bottomLeft, bottomRight, topLeft, topRight]` (in that
literal order from the probe calls above): `left`/`right` are the two probes
**at the pixel's own row** (`y0` if `yParity==0`, `y0+1` if `yParity==1`) —
this is exactly `dFdx`. `bottom`/`top` are the two probes **at the pixel's
own column** — exactly `dFdy`. This is coarse-derivative sharing: both
pixels in a 2-wide row share the same `dFdx` value; both pixels in a 2-tall
column share the same `dFdy` value — this is standard GPU quad-derivative
behavior, confirmed correct (not accidental) by the prototype's output (see
§4: columns 0/1, 2/3, 4/5, 6/7 share identical `gx`; rows 0/1, 2/3, 4/5, 6/7
share identical `gy`).

Per call-site ordinal `index` (`count = max(left.length, right.length,
bottom.length, top.length)`, lines 511-532):
```js
const leftValue = left[index] ?? fallback        // fallback = 0
const rightValue = right[index] ?? leftValue      // NOT 0 — falls back to leftValue
const bottomValue = bottom[index] ?? fallback
const topValue = top[index] ?? bottomValue         // NOT 0 — falls back to bottomValue
// scalar:
const x = rightValue - leftValue
const y = topValue - bottomValue
// vector (component-wise), plus:
footprint[c] = Math.abs(x[c]) + Math.abs(y[c])
return { x, y, width: footprint }
```
`x = right - left` (a **forward** difference in the +fragCoord.x direction),
`y = top - bottom` (a **forward** difference in +fragCoord.y direction),
`width = |x| + |y|` (Manhattan/L1, the standard `fwidth` definition).
**Sign and origin convention**: this is unambiguous — right always comes
"after" left in fragCoord.x, top always "after" bottom in fragCoord.y,
regardless of which specific corner the *current* pixel happens to be.
Getting this backwards (e.g. computing `left - right`) would silently flip
the sign of every dFdx/dFdy result and only be caught by pixel-level
comparison, exactly as flagged in the task brief.

**Replay** (lines 534-544):
```js
this.derivativeMode = 'replay'
try { kernel(context, out) }
finally {
  this.derivativeMode = 'approximate'
  this.derivativeRecords = null
  this.derivativeValues = null
  const lastX = pixelX === context.resolution[0] - 1
  const firstYInTraversal = pixelY === 0
  if ((xParity === 1 || lastX) && (yParity === 0 || firstYInTraversal)) cache.delete(key)
}
```
The kernel runs a **fifth** time (the "real" invocation, with the pixel's own
true fragCoord/uv), now in replay mode, producing the real output color.
**Cache eviction is traversal-order-dependent** — it assumes a specific
raster order and is a pure performance/memory optimization, not a
correctness requirement (see §5.3 for why the C++ port does not need to
replicate this exact predicate).

### 1.4 Cost per quad
4 probe kernel-body executions (shared across the whole quad) + 1 real replay
kernel-body execution **per output pixel** = for a full 2x2 quad, `4 probes +
4 replays = 8` kernel-body executions for 4 output pixels → **2x** average
kernel-body cost per pixel for a derivative-using kernel, not the "~1.25x"
figure in the task brief. See §6 for the corrected cost accounting (I flag
this as a correction rather than silently matching the assumption, since it's
directly derivable from the reference and load-bearing for capacity
planning).

---

## 2. C++ design constraints and recommended mechanism

### 2.1 The hard constraint
```cpp
// include/noisemaker/kernel.hpp
using PixelFn = void (*)(const KernelState&, const glsl::PixelContext&, glsl::Vec4&) noexcept;
```
`PixelFn` is a **plain function pointer**, not a capturing closure. It cannot
carry extra state in its own type. 131 already-ported programs' generated
`pixel()` bodies (`src/typed_generated/typed_slice.cpp`) must not change one
byte, because `typed_manifest.json` records an `output_sha256` of the emitted
C++ text per program (e.g. `"output_sha256":
"8de4f3843b8183fba5231f795eae3f8e7f95f9d981327a82dc61b194c90fde89"` for
`classicNoisedeck/coalesce:coalesce`) and the surrounding test/proof harness
(`tools/glslcpp/check_semantics.py`, the `validate_current_vocabulary_*`
gates in `generate_typed_slice.py`) is built around exact-match assertions,
not "compiles and passes" fuzziness.

### 2.2 Two options considered

**Option A — thread-local `DerivativeState`.**
A `thread_local` global holds mode/ordinal/records/replay-values; `dFdx`
etc. become free functions taking only the GLSL value, consulting the
thread-local. Zero change to `PixelContext` or the call sites' argument
lists in generated code (`dFdx(value)` stays syntactically identical to a
hypothetical direct port).
- Pro: literally no signature or struct change anywhere; codegen for the
  17 kernels is a 1:1 syntactic mirror of the GLSL.
- Con: hidden global mutable state reachable from a function that also
  claims to be `noexcept` and (per the repo's own architecture notes)
  side-effect-free/re-entrant. Two derivative-using kernels can never run
  concurrently on different threads without per-thread-correct setup
  discipline that's invisible at every call site — a future
  parallelize-`run_pass`-by-row change (not requested now, but plausible
  given `run_pass`'s straightforward nested loop) would need to remember to
  re-bind the thread-local per worker thread, with no compiler-enforced
  reminder. Debuggability suffers: a `DerivativeState` reachable from
  nowhere in the function signature is much harder to unit-test in
  isolation (need to reach into a global to set it up/tear it down around
  each test).

**Option B — state carried through `PixelContext` (recommended).**
Add exactly one new field to `PixelContext`:
```cpp
struct PixelContext {
  Vec2 uv{}; Vec4 frag_coord{}; Vec2 resolution{}; float time{}; float seed{};
  std::uint32_t frame{}; float delta_time{};
  DerivativeState* derivative = nullptr;  // <-- new, non-owning, defaults to null
};
```
`dFdx`/`dFdy`/`fwidth` become free functions taking `(const PixelContext&,
value)` — an explicit extra argument, not a signature change to `PixelFn`
(the context is already a parameter of every `pixel()`). Only the codegen
for the 17 kernels' derivative call sites changes (`dFdx(t)` in GLSL lowers
to `glsl::dFdx(context, t)` in C++, using the `context` identifier that's
already in scope as the function's second parameter) — the other 131
programs' generated text is completely untouched, because they never
reference `context.derivative` or call the new free functions at all.
- Pro: **fully re-entrant / thread-safe by construction** — no hidden
  global, so a future parallel `run_pass` needs no additional discipline;
  each call carries its own state pointer. Trivially unit-testable (build a
  `PixelContext` with a `DerivativeState` on the stack, call `pixel()`
  directly). `nullptr` default means every existing non-derivative call site
  is unaffected and the field costs one pointer-sized slot on a struct
  that's already passed by `const&` (no ABI-breaking size explosion in a
  hot path — `PixelContext` is 40 bytes before this change on a 64-bit
  target; the new pointer makes it 48).
- Con: `run_pass` (or a new sibling function) must know to allocate a
  `DerivativeState` and set `context.derivative` only for kernels flagged
  `uses_derivatives`; slightly more code in the driver than "just wrap the
  kernel" (Option A also needs this, just to set/clear the thread-local
  instead).

**Recommendation: Option B.** It satisfies every constraint the task poses —
no `PixelFn` signature change, no regeneration of the 131 frozen programs —
while being strictly safer (no global mutable state, no thread-local
discipline burden) and more testable than Option A. The `noexcept` marking on
`pixel()` is preserved: reading a pointer and incrementing a counter cannot
throw; the `DerivativeState` methods should be marked `noexcept` themselves
(the prototype does this) and use `assert`/documented UB rather than
exceptions for invariant violations (this matches the existing
`noisemaker::glsl` house style, e.g. `component_min`/`component_max`'s
signed-zero handling has no exception paths either).

---

## 3. Correctness requirements — the 17 programs, checked individually

### 3.1 Locating the actual "17"

The corpus under `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/`
has **211** total `.glsl` sources; `src/typed_generated/typed_manifest.json`
lists **131** already-ported `program_key`s (matches "79 remaining": 211-131=80,
one off from the brief's 79 — plausibly a since-then off-by-one in whichever
external tracker produced "79"; not independently reconcilable from this
read-only vantage point, flagged as unverified rather than papered over).

`grep -rl 'dFdx\|dFdy\|fwidth'` over the corpus's `sources/` tree returns 20
files. Cross-referencing against the 131 ported `source` paths and reading
each real (non-comment) call site narrows this to exactly the set the brief
names:

| Source | Status | Why |
|---|---|---|
| `filter/lowPoly/lowPoly.glsl` | **already ported** (`filter/lowPoly:lowPoly`, in the 131) | `fwidth(distToEdge)` at line 212 sits inside `#if LP_BORDER > 0`; the manifest's pinned `defines` for this program are `{"LP_BORDER": 0, "LP_LIGHT": 0}` (`typed_manifest.json`), a **compile-time** preprocessor default, so the whole block is stripped before parsing ever sees `fwidth`. Confirmed by reading `LP_BORDER`'s `#ifndef`/`#define ... 0` guard at lines 28-29 of the source. |
| `synth/testPattern/testPattern.glsl` | not blocked by derivatives | The only "hit" is a comment: `// Use direct calculation instead of fwidth() for tile-aware rendering.` (line 141) — no actual call. |
| `mixer/distortion/distortion.glsl` | remaining, has genuine `dFdx`/`dFdy` calls (6 call sites, lines 111/112/131/132/168/169), **not part of the 17** | Blocked independently by fixed-size local array declarations/indexing (`float sobel_x[9]; float sobel_y[9]; vec2 offsets[9];` + a `for (int i = 0; i < 9; i++)` loop indexing them, lines 40/46/51/65) — a capability this generator does not yet support for arbitrary local arrays (the manifest's existing array support, e.g. `fixed-array-in-parameter-v1`, is a narrow authenticated pattern for specific already-ported programs, not general local-array codegen). This program needs array support *in addition to* derivative support, so it correctly falls outside a "blocked solely by derivatives" count of 17. |
| the 17 `filter/*` programs listed below | remaining, blocked solely by missing dFdx/dFdy/fwidth (every other builtin/construct they use already has typed-IR support going by their neighbors in the 131) | — |

**The 17** (source path → call kind):
`bulge`, `celShading/celShadingColor` (fwidth, vec3), `halftone` (fwidth,
scalar, ×2 call sites in helper functions), `lens`, `lensWarp`, `octaveWarp`,
`pinch`, `polar`, `pondRipples`, `posterize` (fwidth, vec3), `spiral`,
`stamp/stThreshold` (fwidth, scalar), `step` (fwidth, vec3), `stipple`
(fwidth, scalar), `tunnel`, `warp`, `waves` — all under `filter/`.

### 3.2 Ordinal-count stability — the landmine, checked

Read every real (non-comment, non-preprocessor-eliminated) call site's
enclosing control flow for all 17:

- **14 of 17** (`bulge`, `celShadingColor`, `lens`, `lensWarp`, `octaveWarp`,
  `pinch`, `polar`, `pondRipples`, `posterize`, `spiral`, `step`, `tunnel`,
  `warp`, `waves`) gate their dFdx/dFdy/fwidth call(s) inside `if
  (antialias) { ... }`, where every one of these files independently
  declares `uniform bool antialias;` (verified: `grep -n 'uniform bool
  antialias'` hits in all 14, one per file, e.g. `filter/bulge/bulge.glsl:17`).
- **2 of 17** (`halftone`, `stamp/stThreshold`) call `fwidth` unconditionally
  inside a plain helper function (`halftoneCoverage`, `roundDotCoverage`, and
  the `main()` body of `stThreshold` respectively) — no branch at all.
- **1 of 17** (`stipple`) gates its one real `fwidth` call inside `#if MODE
  == 0` — a **compile-time** preprocessor branch (`MODE` is a pinned
  `#define`, same mechanism as `lowPoly`'s `LP_BORDER`), not a runtime
  condition.

**Why none of these are ordinal-count landmines**: GLSL `uniform`s are
frame-constant — the *same* value for every fragment invocation within one
`run_pass` call, and (critically for `wrapDerivatives`) the *same* value
across all four quad-corner probes and the real replay call, since `probe()`
copies every context field except `fragCoord`/`uv` unchanged from the real
context (`{ ...context, fragCoord, uv }`, line 484) — `antialias` is never
touched. So `if (antialias)` either executes on every one of the 5 kernel
invocations that make up one output pixel (4 probes + 1 replay), or on none
of them; the derivative call count for a given output pixel's full quad is
therefore always self-consistent. `#if MODE == 0` is resolved once at
compile time for the whole pinned program variant, so it can't vary between
invocations either. **The landmine this task warns about — a branch around a
derivative call keyed on a per-pixel *varying* quantity (UV, a texture
sample, `gl_FragCoord`) — does not occur in any of the 17.** That would be
the actual danger case (e.g. `if (uv.x > 0.5) { dFdx(...) }`), because two
probes in the same quad could then take different branches and desynchronize
their ordinal sequences; grep across all 17 for `dFdx\|dFdy\|fwidth` followed
by manual read of every enclosing scope found no such pattern.

One second-order requirement this implies for the C++ side: the quad driver
must copy the *entire* `PixelContext` for a probe except `frag_coord`/`uv`
(mirroring `{ ...context, fragCoord, uv }` exactly) — including any future
per-quad-invariant fields — so that uniform-gated branches stay in lockstep
across all five invocations. The prototype's `probe()` does this via
`PixelContext probe_context = real_context;` followed by overwriting only
`frag_coord`/`uv`.

---

## 4. Prototype — mechanism, verification, and result

All files under `docs/port-engineering/derivatives/`:

| File | Purpose | sha256 sidecar |
|---|---|---|
| `reference_probe.mjs` | Node ESM script; **imports the real, unmodified** `GlslCpuRuntime`/`bindGlslKernel` from `../noisemaker-for-cpu/src/csl/glsl-runtime.js` (read-only), builds a hand-written `usesDerivatives = true` kernel, runs it over an 8x8 grid | `reference_probe.mjs.sha256` |
| `prototype.cpp` | Standalone C++20 implementation of §2's Option B design + the quad driver | `prototype.cpp.sha256` |
| `reference_output.f32` / `.csv` | JS reference's raw output | `.sha256` sidecars |
| `prototype_output.f32` / `.csv` | C++ prototype's raw output | `.sha256` sidecars |

**Kernel under test** (identical in both):
```
float t   = 3*uv.x*uv.x + 5*uv.y*uv.y - 2*uv.x*uv.y;   // every intermediate f32-narrowed
float gx  = dFdx(t);
float gy  = dFdy(t);
vec2  fwv = fwidth(uv);
out = vec4(gx, gy, fwv.x, fwv.y);
```
Chosen to exercise: a scalar derivative call (`dFdx`/`dFdy` on `t`) *and* a
vector derivative call (`fwidth` on `uv`, hitting the vector branch of both
`#derivative`/`derivative_vec2` and the quad math's component-wise path),
over an 8x8 grid using **the same fragCoord convention as
`pass_runner.cpp`** (`frag_coord.y = height - row - 0.5`, i.e. image row 0 =
top = largest fragCoord.y).

**Build**:
```
clang++ -std=c++20 -ffp-contract=off -O2 -Wall -Wextra -o prototype prototype.cpp
```
Compiled clean, zero warnings.

**Run and compare**:
```
$ node reference_probe.mjs
wrote reference_output.f32 and reference_output.csv
expected constants: fwidth(uv).x = 0.125  fwidth(uv).y = 0.125

$ ./prototype
wrote prototype_output.f32 and prototype_output.csv, quad cache entries remaining=0

$ diff reference_output.csv prototype_output.csv   # exit 0, no output
$ cmp reference_output.f32 prototype_output.f32     # exit 0, no output
```
Independent lane-by-lane check (Python, unpacking both 1024-byte files as
256 little-endian float32s):
```
lanes: 256 exact matches: 256 max abs diff: 0.0
```

**Result: bit-exact agreement on all 256 output float32 lanes (8x8 pixels ×
4 channels).** `fwidth(uv)` is exactly `(1/8, 1/8) = (0.125, 0.125)`
everywhere — matches the closed-form expectation (`uv.x` advances by exactly
`1/width` per pixel step, so its coarse derivative is exactly the constant
`1/width`, with no rounding room to disagree in). `dFdx(t)`/`dFdy(t)` are
non-trivial (spatially varying, since `t` is quadratic in `uv`) and share
values in the coarse-quad pattern predicted in §1.3 (columns 0/1 share
`gx`, columns 2/3 share a different `gx`, etc.; rows 0/1, 2/3, ... share
`gy`) — visible directly in `prototype_output.csv`/`reference_output.csv`.
The prototype's `main()` also asserts the quad cache is fully empty
(`cache.empty()`) after a complete raster pass, i.e. every quad's
reference-counted eviction fires exactly once, with no leaked entries.

---

## 5. Integration plan

### 5.1 `resources.uses_derivatives` already exists

Confirmed by reading (not modifying) the generator:
- `tools/glslcpp/frontend/typed_ir.py:535` — `uses_derivatives: bool = False`
  is already a field on the typed IR's `resources` record.
- `tools/glslcpp/frontend/semantic.py:306` — already threads
  `analyzer.uses_derivatives` into the IR construction, alongside
  `analyzer.uses_texture`.
- `tools/glslcpp/generate_typed_slice.py:456,562` and
  `tools/glslcpp/check_semantics.py:138` — already read
  `resources.uses_derivatives` as part of each program's frozen
  "expected resources" tuple in the per-program `validate_current_vocabulary_*`
  gate functions (e.g. `filter/degauss`, `filter/crt` both currently assert
  `uses_derivatives=False` as part of their exact-match resource tuple).

So the flag is **already wired end-to-end and already False everywhere**,
waiting for a producer. What's missing is purely: (a) the semantic analyzer
never sets `analyzer.uses_derivatives = True` because `dFdx`/`dFdy`/`fwidth`
are not yet in its recognized-builtin table (they're currently unknown
identifiers, which is why the task states admitting the names makes the 17
"type-check and emit immediately" — nothing else in the type system is
blocking them); (b) no C++ runtime support exists to actually execute a
derivative call correctly.

### 5.2 Files that would change (production side — not touched by this task)

| File | Change |
|---|---|
| `tools/glslcpp/frontend/semantic.py` (and wherever the builtin-function table lives, likely `types.py`/`lexer.py`/`parser.py`) | Admit `dFdx`, `dFdy`, `fwidth` as recognized builtin calls (1 float or N-vector arg → same-shape return); set `analyzer.uses_derivatives = True` on first sighting, mirroring the existing `analyzer.uses_texture` pattern already threaded at `semantic.py:306`. |
| `tools/glslcpp/emit_typed_cpp.py` | New call-lowering rule: `dFdx(expr)` → `noisemaker::glsl::dFdx(context, expr)` (and `dFdy`/`fwidth` likewise), using the `context` identifier already in scope as `pixel()`'s second parameter. This is the only codegen change and it is purely additive — the emitter's other 131 programs' output is untouched because they never hit this new lowering rule. |
| `include/noisemaker/glsl_runtime.hpp` | Add `DerivativeState`, `DerivativeMode`, `DerivativeSample`/`DerivativeRecord` types and the `dFdx`/`dFdy`/`fwidth` free-function overloads (scalar + `Vec<N,float>` for N in {2,3,4} to cover the vec3 fwidth calls in `celShadingColor`/`posterize`/`step`), plus the new `PixelContext::derivative` pointer field (default `nullptr`). Purely additive; existing struct users are unaffected. |
| `include/noisemaker/kernel.hpp` | Add `bool uses_derivatives() const noexcept;` accessor to `BoundKernel` (backed by a new constructor parameter, defaulted `false` for every existing call site so the 131 non-derivative `BoundKernel` construction sites need no edits — or threaded through `KernelState` if that's a cleaner fit once the real class hierarchy is examined; the prototype does not depend on which, since it hardcodes a single kernel). |
| `src/pass_runner.cpp` | Branch in `run_pass`: unchanged fast path when `!kernel.uses_derivatives()` (byte-for-byte the current loop — zero risk to the 131 programs' behavior or performance); new quad-driven path (this task's prototype's `run_pixel_with_derivatives`, generalized) when `true`. |
| `tools/glslcpp/generate_typed_slice.py` / `check_semantics.py` | Each of the 17 gets its own `validate_current_vocabulary_<name>` gate authored (per this repo's existing one-gate-per-program pattern, e.g. the `degauss`/`crt` examples read above), now asserting `uses_derivatives=True` and the exact expected declaration/resource tuple for that program — this is the bulk of the integration *labor*, not the derivative mechanism itself; 17 individual authenticated-vocabulary proofs, one per program, following the established methodology. |
| `src/typed_generated/typed_slice.cpp` + `typed_manifest.json` | Regenerated only for the 17 newly-admitted programs (their `program_key`s get added; the 131 existing entries and their `output_sha256`s are untouched since the emitter only changes behavior for `dFdx`/`dFdy`/`fwidth` call sites, which the 131 don't contain). |

None of the above files were edited as part of this task — this is a plan,
derived from reading the actual current state of each file.

### 5.3 `run_pass` branch and cache-lifetime policy

The prototype's quad driver uses a **reference-counted** cache eviction
(count the quad's in-bounds member pixels up front; decrement on each
consumption; erase at zero) rather than porting glsl-runtime.js's exact
traversal-order-dependent eviction predicate (lines 541-543: `(xParity===1
|| lastX) && (yParity===0 || firstYInTraversal)`). This is a deliberate,
documented deviation, not an oversight: that predicate is only correct for
JS's specific raster order, whereas `pass_runner.cpp`'s row-major, top-row-first
loop with `frag_coord.y = height - row - 0.5` traverses `pixelY` in
*decreasing* order (row 0 has the largest `pixelY`), the opposite sense from
a naive bottom-up JS scan — porting the JS predicate literally would either
leak cache entries or evict too early depending on exactly how the two
traversal orders line up, and there is no reason to accept that fragility
when a reference-counted scheme is (a) traversal-order-agnostic, (b)
provably correct (each quad's probes computed exactly once, evicted exactly
once its last member pixel is produced, regardless of visit order — verified
in the prototype by the `assert(cache.empty())` after a full raster pass),
and (c) achieves the identical amortization (4 probes shared across up to 4
real pixels).

### 5.4 Per-pixel cost multiplier

Corrected from the task brief's "~1.25x": the real number, derived directly
from §1.4, is **~2x** kernel-body executions per output pixel for a
derivative-using kernel (4 shared probes + 4 replays, amortized over 4
pixels = 8/4 = 2), versus 1x for a non-derivative kernel — still far cheaper
than a naive unshared implementation (5 kernel-body executions per pixel: 4
fresh probes + 1 replay, with no quad-sharing = 5x). This only affects the
17 (eventually more) derivative-flagged programs; the `run_pass` fast path
for the other 131+ programs is untouched and pays zero overhead (branch
predicts correctly, single `bool` check).

---

## 6. Risks and what remains unverified

- **The "79 remaining" / "17 of 79" figures do not fully reconcile from
  what's readable in this repo.** 211 total corpus sources − 131 ported =
  80, not 79. This is one off from the task brief; I could not find a
  tracking document (searched for `*progress*`/`*status*`/`*remaining*`
  filenames and `docs/*.md`) that defines "79" authoritatively, so I'm
  reporting the discrepancy rather than silently forcing a match. The "17"
  figure for derivative-only-blocked programs, by contrast, **is** fully
  reconciled and verified by direct source inspection (§3.1) — every one of
  the 17 filter/* programs has a genuine, non-eliminated `dFdx`/`dFdy`/`fwidth`
  call site, and the two exclusions (`lowPoly`, `testPattern`) and one
  extra (`distortion`, blocked by arrays, not derivatives) are each backed
  by a specific line-numbered piece of evidence above.
- **`vec4` derivative overload untested.** The prototype exercises scalar
  and `vec2` derivative paths (matching `celShadingColor`/`posterize`/`step`'s
  `vec3` usage in spirit, but not literally — I did not build a `vec3` or
  `vec4` test case). The generalization from `vec2` to `Vec<N,float>` in
  §5.2's `include/noisemaker/glsl_runtime.hpp` plan is straightforward
  (the JS reference's vector branch, lines 522-532, is already
  width-generic via `component()`), but should get its own `vec3` prototype
  case before being trusted for `celShadingColor`/`posterize`/`step`
  specifically.
- **Multi-call-site ordinal interleaving is asserted, not stress-tested.**
  The prototype's kernel has exactly 3 derivative call sites, all always
  executed in the same order every invocation (no branch separates them).
  None of the 17 production programs have more than one derivative call
  site reachable per branch (checked in §3.2), so this is expected to be a
  non-issue in practice, but a kernel with e.g. two *sequential* unconditional
  `fwidth` calls at different points (halftone has exactly this —
  `halftoneCoverage` and `roundDotCoverage`, each with their own `fwidth`
  call, both unconditional) was not built into the standalone prototype; the
  ordinal mechanism handles this by construction (each call increments a
  shared counter) but it's worth a dedicated test when this becomes real
  integration work rather than a prototype.
- **No behavior at the image edge was verified against the JS reference.**
  The prototype's 8x8 grid and the reference's 8x8 grid use identical
  dimensions and never actually probe outside `[0, width) x [0, height)`
  in a way that stresses the "probe past the canvas edge" case discussed in
  §1.3/§3.2, because `uv`/`t` here are smooth polynomials with no
  discontinuity — an edge probe would produce a well-defined (if
  off-canvas-sampled) value in both implementations, but I have not run a
  case with, e.g., a `texture()` sample at an out-of-range UV to confirm the
  C++ texture sampler's boundary behavior (wrap/clamp) matches the JS
  sampler's (`sampleBilinear`/`sampleNearestBottomLeft` in
  `src/runtime/sampler.js`) bit-for-bit at a probed-but-off-canvas
  coordinate. This matters for at least `bulge`/`pinch`/`spiral`/etc., which
  all `texture()`-sample using the dFdx/dFdy-derived offset — worth a
  dedicated edge-pixel test before shipping.
- **`BoundKernel`'s actual current constructor/field layout was read only at
  the `kernel.hpp` interface level**, not its `.cpp` implementation (not
  located during this task) — the exact mechanism for storing/threading a
  `uses_derivatives` bool (constructor param vs. derived from `KernelState`
  vs. a parallel lookup) is a recommendation, not a verified-fits-cleanly
  plan, since the constructor's `.cpp` body wasn't read.
- I did not attempt to run any of the 17 real production `.glsl` files
  through this prototype's mechanism — the prototype is a minimal,
  hand-written stand-in kernel chosen to exercise the same runtime paths
  (scalar + vector derivative, coarse-quad sharing, cache eviction), not a
  port of any of the 17. Confidence that the mechanism generalizes to the
  real programs rests on the call-site analysis in §3.2, not an end-to-end
  run of real shader code.
