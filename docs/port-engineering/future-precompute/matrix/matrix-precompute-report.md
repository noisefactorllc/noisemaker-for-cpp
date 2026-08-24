# Matrix generalization precompute — selection evidence and design sketch

READ-ONLY. Nothing was written under `.`
or `../noisemaker-for-cpu`. No `git`, no Python test suite,
no cmake build was run. All work product lives under
`docs/port-engineering/future-precompute/matrix/`. This is a selection
sketch, not an implementation — no generator/emitter/runtime file was edited.

Revision probed: `a024dc3a960cc44af454abc7aebce50456c194e6` (same as
`roadmap2/full-chain-frontier-map.md`, cross-checked against it throughout).
Baseline state: **131 typed / 133 public / 79 unported**, typed-list hash
`ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`.

## 0. Headline correction

`roadmap2/full-chain-frontier-map.md` §4/§6 flags "matrix arithmetic beyond
`mat2*vec2`" as **9 candidates** (`cellNoise, colorLab, effects, glitch,
moodscape, noise, shapes, adjust, colorspace`), "unconfirmed pending [a]
follow-on probe." This report is that follow-on probe.

Result: **the 9 is real as a list of programs whose terminal gate-chain
blocker is a matrix dispatch gap**, confirmed by independent re-run of the
gate-chain engine (below). But applying this codebase's own two mandatory
selection filters (reachability, discriminability — `task-31-target-reselection.md`)
and a Curl-class narrowing-point check (`task-31-curl-SOLVED.md`) cuts this
down hard:

- **2 of 9 (`moodscape`, `noise`) have their ENTIRE new-capability closure
  unreachable from `main` at their authorized define map** — same
  disqualification class as `classicNoisedeck/caustic` and `filter/snow`.
  No amount of matrix generalization can be validated by rendering evidence
  for these two.
- **1 of 9 (`effects`) has its matrix closure (`bicubic`, a mat4 chain)
  ALSO entirely dead**, and additionally needs three unrelated capabilities
  (`loop_proof_bypass`, `mutable_global_admission`, `array_global_admission`)
  just to reach the matrix gate at all. Lowest-value target in the family.
- Of the remaining 6, **3 (`cellNoise`, `colorLab`, `shapes`) are only
  half-reachable**: the "inverse" oklab direction is dead code in all three;
  only the "forward" direction is live.
- **A concrete, verified narrowing-point divergence** (Curl-tanh-class) was
  found in the mat4×mat4×mat4 chained-multiply pattern used by `glitch`
  (live) and `effects` (dead): the JS canonical kernel's `matrixMult` helper
  never narrows its intermediate product to f32, while the C++ runtime's
  generic `Mat<N>*Mat<N>` operator narrows after every column. A naive reuse
  of the existing runtime operator for this pattern would very likely ship a
  bit-inexact `glitch`.

**Honest yield: 6 of 9 programs are landable with real rendering evidence
(or partial rendering evidence) from matrix generalization; only 3 of those
6 (`adjust`, `colorspace`, `glitch`) get their entire matrix closure
validated by full-render parity.** See §6 for the slicing this implies.

## 1. Runtime existence audit (`include/noisemaker/glsl_types.hpp`)

Confirmed by direct read of the whole file (265 lines) plus a full-tree grep
of `include/` and `src/` (excluding `typed_generated/`), not a narrow
two-file grep (per this project's own `float_bits_to_uint`/`glsl_round`
lesson):

```
grep -rn "Mat<\|Mat2\|Mat3\|Mat4\|class Mat" include src --include='*.hpp' --include='*.cpp' | grep -v typed_generated
```

| Symbol | Exists? | Where | Notes |
|---|---|---|---|
| `template<size_t N> class Mat` | **yes, unconstrained over N** | `glsl_types.hpp:220-230` | No `requires` clause restricting N (unlike `lessThanEqual`/`all`, which are `requires(N==2)`). Column-vector constructor (`Mat(Columns&&... columns)`, N columns of `Vec<N,float>`), diagonal-scalar constructor, `operator[]` column indexing, `operator==`. |
| `operator*(Mat<N>, Vec<N,float>)` (matrix·vector) | **yes** | `glsl_types.hpp:231` | `result[row] = f32(Σ_col matrix[col][row]*vector[col])` — accumulates in `double`, narrows once. |
| `operator*(Vec<N,float>, Mat<N>)` (vector·matrix) | **yes** | `glsl_types.hpp:232` | Same accumulate-once-narrow pattern. |
| `operator*(Mat<N>, FloatExpr<N>)` / `(FloatExpr<N>, Mat<N>)` | **yes** | `glsl_types.hpp:233-234` | Narrows the `FloatExpr` argument to `Vec<N,float>` **before** multiplying (see §5 narrowing analysis — correct for the live oklab sites, a real divergence risk for the dead `invA*(...)` site). |
| `operator*(Mat<N>, Mat<N>)` (matrix·matrix) | **yes** | `glsl_types.hpp:235` | `result[col] = a * b[col]`, i.e. narrows to f32 after **every** column — this is the site that diverges from the JS `matrixMult` chain (§5). |
| `Mat2`/`Mat3`/`Mat4` aliases | **yes** | `glsl_types.hpp:264` | `using Mat2=Mat<2>; using Mat3=Mat<3>; using Mat4=Mat<4>;` |
| `UniformValue` variant already carries `Mat2,Mat3,Mat4` | **yes** | `glsl_runtime.hpp:208` | Not previously documented anywhere in the roadmap chain — uniforms can already hold mat3/mat4 values without any runtime change. |
| `inverse`/`transpose`/`determinant` | **no** | confirmed absent, full-tree grep | Not needed by any of the 9 target programs (none call these). |
| `glsl::any`, `notEqual`, `greaterThanEqual`, `lessThan` | **no** | confirmed absent (matches prior roadmap finding) | Unrelated to matrix work, listed for completeness. |

**Confirms and sharpens `full-chain-frontier-map.md` §3's claim**: `Mat<N>`
needs **zero** new runtime code for N=3,4 matrix·vector, vector·matrix, or
matrix·matrix. The only gap is generator/emitter dispatch (§2) — except for
one narrowing-precision wrinkle in the matrix·matrix chain (§5) that *is*
new work, just not "new runtime type."

### Column-major convention check (task requirement: JS Float32Array vs. C++ column-major)

Traced the actual multiply semantics in the vendored `glsl-transpiler`
package (`noisemaker-for-cpu/node_modules/glsl-transpiler/lib/operators.js:186-283`,
`stdlib.js` `matrixMult`/`dot`) against `glsl_types.hpp`'s `operator*`
definitions, component index by component index:

- JS stores a matrix as a flat `Float32Array` filled in **source constructor
  order** (`mat3(x0,y0,z0, x1,y1,z1, x2,y2,z2)` → `[x0,y0,z0,x1,y1,z1,x2,y2,z2]`,
  confirmed in `types.js:463-482`), and every multiply indexes it as
  `mat[col*N + row]` (`operators.js:230`, `:262-263`; `stdlib.js:733`
  `m[l*o+i]`) — i.e. **column-major**, GLSL-standard.
- C++'s `Mat<N>` stores `columns_[col][row]` and its `operator*` accesses
  `matrix[column][row]` — the same column-major layout.
- Both `mat*vec`, `vec*mat`, and `mat*mat` compute the identical summation
  (verified algebraically term-by-term, not just "looks similar"): e.g.
  JS `mat*mat`: `comps[j*len+i] = Σ_o left[len*o+i]*right[j*len+o]`; C++:
  `result[col_j][row_i] = Σ_o a[col_o][row_i]*b[col_j][row_o]` — same o↔row/col
  binding.

**Conclusion: the conventions match exactly. A transposition error is not a
structural risk here** — the existing `Mat<N>` type, used as-is with a
straightforward N-argument column constructor, computes the mathematically
correct (JS-matching) result for construction and all three multiply shapes.
The precision risk found in §5 is a *narrowing-point* issue, not a
*convention* issue.

## 2. Generator/emitter restriction sites (exhaustive, file:line)

### `tools/glslcpp/generate_typed_slice.py`

| # | Site | Current restriction | What's needed |
|---|---|---|---|
| G1 | `APPROVED_TYPES`, L222-225 | Tuple contains `"mat2"` but not `"mat3"`/`"mat4"` | Add `"mat3","mat4"`. This is the generic `reject_type` gate (L1682-1708) — it fires for **every** mat3/mat4-typed AST node (declaration, expression, parameter, return), not just binary/construct sites. Already coded as a table-only probe patch (`matrix_type_admission`, `gate_chain_engine.py:423-432`, `table_deltas={"approved_types": ("mat3","mat4"), "emit_types": {...}}`). |
| G2 | Const-global initializer walker inside `validate_capabilities` (the function whose original text is quoted in `gate_chain_engine.py`'s `global_admission` patch, L148-178) | Originally: `if storage != "const" or declaration.type != FLOAT or ...: raise "unsupported global declaration"`, and the recursive `global_initializer()` only descends into `"literal"` child nodes | Must drop the `FLOAT`-only restriction (any const-typed global, not matrix-specific) **and** recurse into `"construct"` initializer nodes (needed for `mat3(9 floats)`/`mat4(16 floats)` constructor initializers, not just scalar literals) |
| G3 | Global-declaration loop, L1989-1994 (`unsupported global matrix declaration`) | `if declaration.type.kind == "matrix": raise` — blanket ban on **any** matrix global regardless of storage | Needs a `const`-storage exception (`and declaration.symbol.storage != "const"`) — already part of the `global_admission` patch's second `validate_subs` entry |
| G4 | `expression()`'s construct-kind branch, L2004-2010 | `if value.type.display() != "mat2" or len(value.children) != 4 or any(child not float): raise "unsupported matrix constructor"` | Generalize to `display() in {"mat2","mat3","mat4"}` and `len(children) == N*N` where `N = {"mat2":2,"mat3":3,"mat4":4}[display]`, all-float children |
| G5 | `expression()`'s binary-kind branch, L2048-2051 | `if operator != "*" or left_type != "mat2" or right_type != "vec2": raise "unsupported matrix binary expression"` | **The site the roadmap names.** Needs widening to `matN*vecN`, `vecN*matN` for N∈{3,4}, **and separately** `matN*matN` (matrix·matrix — required specifically by `glitch`/`effects`'s bicubic pattern, a materially different operand shape from the other 7 programs, and per §5 needs its own narrowing-safe lowering, not a blanket dispatch widening) |
| G6 | Function return-type check, L2237-2239 | Matrix return banned except the single object-identity `authorized_rotate_helper` | Not required by any of the 9 (verified: no `mat3 f(...)`/`mat4 f(...)` signature exists in any of the 9 programs' matrix-using code — full-tree grep, zero hits) |
| G7 | Function parameter-type check, L2249-2250 | Matrix parameter banned unconditionally, no exception | Not required by any of the 9 (same verification as G6) |

### `tools/glslcpp/emit_typed_cpp.py`

| # | Site | Current restriction | What's needed |
|---|---|---|---|
| E1 | `_TYPES`, L84-90 | `{"mat2": "glsl::Mat2"}` only | Add `"mat3": "glsl::Mat3", "mat4": "glsl::Mat4"` — table-only, mirrors G1 |
| E2 | `expression()`'s `matrix_return_program`/`rotate_expressions` gate, L1156-1174 | Fires only when some function in the program has a matrix return type, in which case every matrix expression must be one of Rotate's 3 pre-authenticated nodes | Doesn't fire for any of the 9 (none declare a matrix-returning function — verified, same as G6) |
| E3 | `expression()`'s construct-kind branch, L1194-1203 | Only lowers `display=="mat2"`, exactly 4 float children, to `glsl::Mat2(Vec2(a,b), Vec2(c,d))` | Generalize: group N*N children into N `glsl::Vec<N,float>` columns, emit `glsl::MatN(VecN(...), VecN(...), ..., VecN(...))` — this exactly matches `Mat<N>`'s already-generic N-column constructor (§1), so the *shape* of the emitted code doesn't change, only N |
| E4 | `expression()`'s binary-kind branch, L1300-1302 | `if "mat" in left_type or "mat" in right_type: if operator != "*" or left_type != "mat2" or right_type != "vec2": raise` | Mirrors G5. For `matN*vecN`/`vecN*matN`: a straightforward widening (§5 shows this is narrowing-safe as-is). For `matN*matN`: **cannot** be a straightforward widening to the generic `operator*(Mat<N>,Mat<N>)` — needs a dedicated, per-program-authenticated lowering that accumulates the whole product chain in `double` and narrows once at the end (§5) |

**Total: 7 generator sites + 4 emitter sites = 11.** Two of the eleven
(G1/E1's table entries, and G3's storage exception) are **already written**
as probe patches in `gate_chain_engine.py` (`matrix_type_admission`,
`global_admission`) — confirmed by reading the patch registrations directly,
not inferred. The binary/construct dispatch widening (G4/G5/E3/E4) has
**no** registered patch anywhere in `gate_chain_engine.py` (`grep -n
"unsupported matrix" gate_chain_engine.py` inside `classify()` returns
nothing) — confirming the roadmap's claim that this generalization was
"identified but not built."

## 3. Affected programs — verified gate chains

`roadmap2/full-chain-frontier-map.md`'s 79-program corpus was cross-checked
(`212 total − 131 typed − 2 free = 79`, `filter/invert:inv`/`synth/solid:solid`
excluded). Filtering `gate-chain-all-output.json`'s 81 rows for any stage
whose blocker message contains "matrix" found **12** rows, not 9:
`cellNoise, colorLab, effects, fractal, glitch, moodscape, noise,
shapeMixer, shapes, adjust, colorspace, dither`. Of these, 3
(`fractal`, `shapeMixer`, `dither`) touch `matrix_type_admission` as a
**non-terminal** stage but are blocked on something else entirely (loop
shape / `mod` overload / loop shape) — correctly excluded from the roadmap's
9. The 9 whose **terminal** (`NO_GENERIC_PATCH`) blocker is
`"unsupported matrix constructor"` or `"unsupported matrix binary
expression"` match the roadmap's list exactly.

**Independent verification**: re-ran `gate_chain_engine.walk_chain()` for
all 9 keys directly (not just re-reading the existing JSON) —
`matrix-gate-chain-rerun.json`. All 9 rows reproduce byte-for-byte
(`final_status`, `terminal_blocker`, and the full ordered `classified_gate`
sequence all match `gate-chain-all-output.json`), and `restored_all: true`
for all 9 in both the original and the rerun. Post-run module-state check
(`gce.gen.APPROVED_TYPES`, `gce.emit._TYPES`) confirms `mat3`/`mat4` are
absent afterward — the harness's in-process monkeypatches left no residue.
No `git`/file-write touched either target repo; `walk_chain` only mutates
Python function objects in-process, inside `try`/`finally`.

| Program | Ordered gate chain (co-requisites → terminal) | Terminal blocker |
|---|---|---|
| `filter/adjust:adjust` | `global_admission` → `matrix_type_admission` → `index_expression_admission` → **matrix binary** | `mat3*vec3` (`fwdA*c`, `fwdB*(...)`) |
| `filter/colorspace:colorspace` | same 3 co-requisites → **matrix binary** | same pattern |
| `classicNoisedeck/cellNoise:cellNoise` | same 3 → **matrix binary** | same pattern (both oklab directions present) |
| `classicNoisedeck/colorLab:colorLab` | same 3 → **matrix binary** | same |
| `classicNoisedeck/shapes:shapes` | same 3 → **matrix binary** | same |
| `classicNoisedeck/moodscape:moodscape` | same 3 → **matrix binary** | same pattern, but closure is dead (§4) |
| `classicNoisedeck/noise:noise` | `loop_proof_bypass` → `global_admission` → `matrix_type_admission` → `builtin:floatBitsToUint` → `scalar_uint_xor_admission` → `index_expression_admission` → **matrix binary** | same oklab pattern, dead (§4), plus 3 unrelated co-requisites for the rest of the program |
| `classicNoisedeck/glitch:glitch` | `matrix_type_admission` → **matrix constructor** | mat4 bicubic (construct **and**, on the next call, matrix·matrix) — cleanest chain, single gate |
| `classicNoisedeck/effects:effects` | `loop_proof_bypass` → `mutable_global_admission` (escalated from `global_admission`) → `array_global_admission` → `matrix_type_admission` → **matrix constructor** | same bicubic pattern as glitch, but dead (§4), plus 3 unrelated co-requisites |

`index_expression_admission` appears as a shared co-requisite for 7 of the
9 (all but `effects`/`glitch`) because all 7 share a byte-identical
`linearToSrgb`/`srgbToLinear` helper pair with a `for (int i=0;i<3;++i) {
if (linear[i] <= ...) srgb[i] = ...; }` loop — confirmed by direct grep of
the corpus source, unrelated to matrices themselves but bundled in the same
color-utility block that was evidently copy-pasted across all 7 programs.

**Answering "how many fully land from matrix generalization alone vs. need
more"**: only `classicNoisedeck/glitch:glitch`'s chain is *purely* a matrix
gate (needs `matrix_type_admission` and nothing else). All other 8 need at
least `global_admission` (already a separate, general-purpose capability
the roadmap ranks earlier, step 2 of its own order) plus, for 7 of them,
`index_expression_admission`; `effects` additionally needs
`loop_proof_bypass` and two global-admission variants. **Matrix
generalization participates in all 9 chains but is the sole remaining
blocker for only 1 of them (`glitch`).**

## 4. Reachability filter (mandatory per `task-31-target-reselection.md`)

`reachability-output.json` (from `roadmap2/`) only covers the 35
mechanically-PASSing programs — none of the 9 matrix programs are in it
(they don't PASS). Built a dedicated call-graph-from-`main` probe
(`matrix_reachability_probe.py`, same technique as
`roadmap2/reachability_probe.py`: walk `call`-node `signature_id`s starting
at `main`), applied it directly to all 9 via `gate_chain_engine.load()`
(pure parse + semantic analysis at each program's authorized define map
from `generate_typed_slice._defaults` — no validator/emitter gating, so it
works regardless of PASS/BLOCKED status; nothing is monkeypatched, so
nothing needs restoring). Full output: `matrix-reachability-output.json`.

| Program | Matrix closure reachable? | Detail |
|---|---|---|
| `filter/adjust:adjust` | **Fully live** (6/6 functions reachable) | Only declares `fwdA`,`fwdB` (no inverse direction in this program at all); both binary sites (`fwdA*c`, `fwdB*(lms³)`) reachable=True |
| `filter/colorspace:colorspace` | **Fully live** (4/4 functions reachable) | Same — only `fwdA`/`fwdB`, both sites reachable |
| `classicNoisedeck/glitch:glitch` | **Fully live** (11/11 functions reachable) | `bicubic` (mat4 construct + mat4×mat4×mat4 + vec4×mat4) fully reachable |
| `classicNoisedeck/cellNoise:cellNoise` | **Half live** | `linear_srgb_from_oklab` (`fwdA*c`, `fwdB*(...)`) reachable=True; `oklab_from_linear_srgb` (`invB*c`, `invA*(...)`) reachable=**False** — `dead_functions` includes it explicitly |
| `classicNoisedeck/colorLab:colorLab` | **Half live** | Same split |
| `classicNoisedeck/shapes:shapes` | **Half live** | Same split |
| `classicNoisedeck/moodscape:moodscape` | **Fully dead** | Both `oklab_from_linear_srgb` and `linear_srgb_from_oklab` are in `dead_functions`; all 4 mat3 binary sites and all 4 mat3 globals (`fwdA/fwdB/invA/invB`) have `any_reference_reachable: False` |
| `classicNoisedeck/noise:noise` | **Fully dead** | Same as moodscape — both oklab functions and all matrix globals unreachable (the reachable `rotate2D`/mat2 site in this program is the pre-existing, already-supported mat2 capability, irrelevant here) |
| `classicNoisedeck/effects:effects` | **Fully dead** | `bicubic` is in `dead_functions` (8/28 functions reachable total — this program is dominated by dead `#elif EFFECT==N` branches at its default define) |

**This is a direct extension of the exact disqualification that hit
`classicNoisedeck/caustic` and `filter/snow`**: `moodscape` and `noise`
cannot have their matrix work validated by any rendering evidence at their
authorized define map — full stop. `effects` is in the same bucket. Per
`task-31-target-reselection.md`'s own standard ("a candidate whose closure
is unreachable at its authorized defines should be deprioritized regardless
of how cheap its gate chain looks"), **these 3 should not be counted as
matrix-capability wins**, leaving 6 real candidates
(`adjust, colorspace, glitch` fully live; `cellNoise, colorLab, shapes`
half-live).

## 5. Discriminability and the narrowing hazard (mandatory per Curl precedent)

### Discriminability of a wrong implementation

All matrix constants involved are genuinely **non-symmetric** 3×3 or 4×4
linear transforms (verified by direct inspection of the constant values,
e.g. `fwdA`'s row/column pair `(0,1)=1.0` vs `(1,0)=0.3963...`; the bicubic
`S`/`T` basis matrices mix `+`/`-` integer coefficients asymmetrically
too), used unconditionally on live per-pixel color/interpolation data. A
transposition, wrong-column, or wrong-sign implementation error would
change essentially every output channel for generic input — this is a
structural argument (matrix asymmetry + direct use in the render path), not
an empirical mutation-test result; no oracle mutation sweep was run (would
require building/running the C++ port, outside this task's read-only scope).
Flagged as **structurally argued, not empirically proven** — consistent
with this project's evidence standard.

### Narrowing-point comparison (JS canonical kernel vs. C++ emitter)

Per `task-31-curl-SOLVED.md`'s finding that narrowing points are a property
of the third-party `glsl-transpiler` package's `optimize:true` heuristics,
not derivable from GLSL semantics alone, this was checked **empirically**:
wrote two minimal GLSL snippets reproducing the exact matrix shapes found in
the 9 programs (the oklab `mat3*vec3` pattern, and the bicubic
`mat4*mat4*mat4`/`vec4*mat4` pattern), ran them through the actual vendored
`glsl-transpiler` package (imported directly from
`noisemaker-for-cpu/node_modules/glsl-transpiler`, read-only) plus the real
`normalizeCanonicalGlsl()` pre-pass (`src/csl/glsl-normalize.js`, also
read-only import), with the identical options
`scripts/upstream/compile-glsl.js` uses (`version:'300 es', optimize:true,
includes:false`, same `uniform`/`varying` renaming). Scripts:
`probe_js_matrix_transpile.mjs`; raw output: `oklab-transpiled.js`,
`bicubic-transpiled.js`.

**Finding A — matrix·vector, simple operand (SAFE, no divergence).**
`invB * c` (c a plain parameter) transpiles to inlined scalar arithmetic:
`invB[0]*c[0] + invB[3]*c[1] + invB[6]*c[2]`, computed in JS `Number`
(double) and narrowed to f32 **once**, only when stored into the enclosing
`new Float32Array([...])`. `fwdB * (lms*lms*lms)` (the live, reachable
half of every 7-program oklab pattern) shows the same shape: the cube is
computed and narrowed into a `Float32Array` first, then the matrix multiply
reads already-f32 elements. **This matches `Mat<N> operator*(Mat<N>,
Vec<N,float>)`'s accumulate-in-double-narrow-once behavior exactly** — the
live half of `adjust`, `colorspace`, `cellNoise`, `colorLab`, `shapes` is
narrowing-safe as verified, not just assumed.

**Finding B — matrix·vector, compound operand (DIVERGENT, but dead code).**
`invA * (sign(lms)*pow(abs(lms), vec3(1/3)))` (the "inverse" oklab
direction, dead in all 5 programs that have it) transpiles the inner
`sign(lms)*pow(...)` product via `vec3.multiply([], sign(lms), pow(...))`
— note the **`[]` first argument is a plain JS `Array`, not a
`Float32Array`** — so that intermediate vector is never narrowed to f32
before being fed into `invA`'s dot-product `.map()`. This diverges from
`operator*(Mat<N>, FloatExpr<N>)`, which narrows its `FloatExpr` argument to
`Vec<N,float>` **before** multiplying (`glsl_types.hpp:233`). This is the
same class of bug as Curl's `tanh` argument-narrowing defect. It is
currently unobservable by rendering (the closure is dead in every program
that has it — §4), but the emitter would still need to structurally lower
it (per this codebase's "authenticate even unreachable sites" precedent
from Curl's dead `permute` overload), so it should not be silently trusted
to the generic runtime operator if it is ever authenticated — flag it
explicitly rather than assume Finding A's safety generalizes.

**Finding C — matrix·matrix chain (DIVERGENT, and LIVE — the important one).**
`mat4 A = T * Q * S;` transpiles to `matrixMult(matrixMult(T, Q), S)`.
Read `matrixMult`'s definition
(`noisemaker-for-cpu/node_modules/glsl-transpiler/lib/stdlib.js:728-739`):
its accumulator `sum` is `double`, but the output is `var out =
Array(m.length)` — **a plain `Array`, never a `Float32Array`**. So
`matrixMult(T, Q)`'s result is never narrowed to f32, and that
full-double-precision intermediate is fed directly into the second
`matrixMult(_, S)` call — **the entire `T*Q*S` chain stays in double
precision until its columns are finally extracted into a `Float32Array` for
the downstream `tv*A` dot products.** The generic C++ runtime
`operator*(Mat<N>,Mat<N>)` does the opposite: `result[col] = a * b[col]`
delegates to `Mat<N>*Vec<N,float>`, which narrows to f32 **after every
column** (`result[row]=f32(sum)`, `glsl_types.hpp:231`). A naive
`(T*Q)*S` implemented by two calls to the existing generic operator would
therefore very likely diverge from the JS reference at the bit level for
some inputs — **and this pattern is fully reachable in `glitch`**, so it is
not a theoretical concern, it is exactly the kind of thing that would show
up as an unexplained few-ULP pixel mismatch during oracle verification,
just like Curl's tanh bug did. **This needs a dedicated, authenticated
lowering — "accumulate the entire product chain in double, narrow once at
the very end" — not a blanket reuse of `operator*(Mat<N>,Mat<N>)` twice.**
Exactly Curl's "Strategy 2: per-program compatibility transform" precedent,
not a blanket runtime change (which Curl's own history shows regressed 3
previously-passing programs when tried).

## 6. Recommended slicing and projected counts

Baseline: **131 typed / 133 public / 79 unported**,
hash `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`.
`public = typed + filter/invert:inv + synth/solid:solid` throughout.

**Slice A — matrix type + global-declaration admission** (G1, G2, G3, E1).
Table additions (`APPROVED_TYPES`, `emit._TYPES`) plus generalizing the
const-global initializer walker to recurse into matrix constructors and
carve a `const`-storage exception in the blanket matrix-global ban. Zero
runtime work, zero programs reach `PASS` on their own (still blocked on
binary/construct dispatch) — pure foundation, prerequisite for every
program in this family.
→ **131/133/79 unchanged.**

**Slice B — matrix·vector multiply + construct generalization** (G4, G5's
vector-only half, E3, E4's vector-only half). Targets exactly Finding A's
narrowing-safe shape. Combined with Slice A and the pre-existing
`index_expression_admission` and `global_admission` capabilities:
- **Fully lands `adjust`, `colorspace`** — both 100% render-reachable, no
  narrowing risk (Finding A verified for their exact code shape).
- **Lands `cellNoise`, `colorLab`, `shapes` with a Curl-style caveat**: the
  live half (`linear_srgb_from_oklab`) validates by full-render parity; the
  dead half (`oklab_from_linear_srgb`) must be authenticated structurally
  only, and — because it hits Finding B's divergent codegen path — needs
  explicit compatibility-transform review before being trusted to the
  generic runtime operator, not silent inheritance of Finding A's safety.
- **Does not land `moodscape`, `noise`** (§4: fully dead closure, same
  disqualification class as Caustic/snow — no rendering evidence can ever
  validate them at today's default defines).
- **Does not land `effects`** (dead closure **and** 3 unrelated
  co-requisite capabilities not touched by this slice).
→ **+5 real programs: 136 typed / 138 public / 74 unported.**

**Slice C — matrix·matrix multiply with narrowing-safe chained-product
lowering** (G5's remaining half, E4's remaining half, **plus new
authenticated codegen**, not a mechanical widening — Finding C). This is
the one slice that is not "table update + type check relaxation"; it needs
an actual new lowering strategy, the matrix-generalization equivalent of
Curl's `tanh_lanewise`.
- **Lands `glitch`** — fully reachable, single-gate chain, and the
  narrowing fix is load-bearing here (§5 Finding C), not optional.
- Does **not** land `effects` (dead `bicubic` closure regardless of this
  slice, plus its 3 unrelated co-requisites are untouched by any matrix
  work).
→ **+1 program: 137 typed / 139 public / 73 unported.**

**Net, corrected verdict**: matrix generalization is real, needs no new
*runtime type*, but is not the clean "+9" the roadmap flagged as pending
confirmation. It is **+5 at Slice B, +6 through Slice C**, with 3 of the
original 9 (`moodscape`, `noise`, `effects`) excluded on reachability
grounds the same way Caustic and snow were excluded from their families,
and one further wrinkle (Finding C) meaning the matrix·matrix half of the
capability is real new engineering, not a mechanical dispatch widening.
`effects` remains a legitimate future target once its three unrelated
capabilities (loop-proof bypass, mutable/array global admission) are
separately landed — at that point it would still only reach *structural*
matrix authentication, never full-render matrix parity, because `bicubic`
is dead code in this program specifically.

## Appendix: files in this directory

- `matrix_reachability_probe.py` (+ `.sha256`) — call-graph-from-`main`
  reachability probe for the 9 matrix programs (§4).
- `matrix-reachability-output.json` (+ `.sha256`) — its output.
- `probe_js_matrix_transpile.mjs` (+ `.sha256`) — standalone JS-transpile
  narrowing-point probe (§5), imports the real vendored `glsl-transpiler`
  and `normalizeCanonicalGlsl` read-only.
- `oklab-transpiled.js`, `bicubic-transpiled.js` (+ `.sha256` each) — raw
  transpiler output backing Findings A/B/C.
- `matrix-gate-chain-rerun.json` (+ `.sha256`) — independent re-run of
  `gate_chain_engine.walk_chain()` for the 9 keys, cross-checked against
  `roadmap2/gate-chain-all-output.json` (§3).
- `matrix-precompute-report.md` (this file, + `.sha256`).
