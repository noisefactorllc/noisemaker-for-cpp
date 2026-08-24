# Progress checkpoint — global admission + mat3 design

## Status: in progress, checkpoint 1

## Confirmed facts so far

1. **Table verification**: `census/relaxed_global_probe.json` (25 rows) exactly
   reproduces the task's blocker table when tallied by second-blocker string:
   mat3=7, write-to-const-global=3, round=3, varying=3, `&`=2, struct=2,
   bvec3=1, float[9]=1, ivec2[9]=1, int[80]=1, floatBitsToUint=1. Total 25.
   Source rows: `docs/port-engineering/census/relaxed_global_probe.json`.
   Still need: re-run this probe myself against the LIVE tree (not just trust
   the frozen census JSON) to confirm it still holds after derivatives landed
   (typed count now 154, was 131 at census time).

2. **Admission loop location**: `tools/glslcpp/generate_typed_slice.py`
   lines 2078-2126 (`admitted_globals` loop). Only admits:
   - declarations in `admitted_literal_ints` (const int, only for programs in
     `SOURCE_GLOBAL_LITERAL_INT_KEYS`)
   - two identity-authorized luma-weights declarations
   - else requires `storage == "const" and type == FLOAT and initializer is
     not None`, else `"unsupported global declaration"`.
   This loop **never calls `used.add`** (vocabulary-free), confirming the
   roadmap's claim. This is the mechanism to widen.

3. **Separate, later, unconditional matrix-global rejection**: lines
   2161-2166, applies to ALL declarations regardless of whether admitted
   above: `reject_type(declaration.type, declaration)` (checks
   `APPROVED_TYPES`, line 244, currently 16 entries, no mat3) THEN an
   independent `if declaration.type.kind == "matrix": raise
   "unsupported global matrix declaration"`. This is layer 2 — confirmed by
   `census/relaxed2_mat3_probe.json`: all 7 mat3 programs hit exactly this
   message after only the admission loop (layer 1) was relaxed.

4. **Layer 3** (after both admission-loop AND the matrix-kind reject are
   patched, per `census/relaxed3_mat3_probe.json`):
   - 6 programs (cellNoise, colorLab, moodscape, shapes, adjust, colorspace)
     hit `unsupported typed expression index` — i.e. matrix indexing
     (`m[0]`, `m[i]`) has **no proof/authorization path at all**. The
     `index` node handler (lines 2294-2357) only recognizes array-declaration
     proofs (fixed-nine, fixed-grid, task19, task20) or the identity-listed
     `authorized_grade_index_sites`. None apply to matrices.
   - `shapeMixer` instead hits `unsupported builtin reflect` — `reflect` is
     **absent from `_BUILTINS`/`APPROVED_CAPABILITIES` entirely** (not just
     unadmitted-by-identity like round/tanh).

5. **Frozen-44 vocabulary confirmed by direct count**: `APPROVED_CAPABILITIES`
   (line 220-231) has exactly 44 entries. `APPROVED_TYPES` (line 242-245) is a
   SEPARATE, differently-sized (16-entry) list gating GLSL *types*, not
   capabilities — adding `"mat3"` there does NOT touch the frozen 44. The
   existing precedent (`round`, `tanh`, `floatBitsToUint`, `all`+
   `lessThanEqual`, and now `dFdx`/`dFdy`/`fwidth`) shows builtins can be
   admitted by **node identity** (an authenticated per-program profile listing
   exact AST node objects) without growing the 44. Matrix indexing and
   `reflect` must follow the same pattern.

6. **Exact site inventory, validator** (`tools/glslcpp/generate_typed_slice.py`):
   - L244 `APPROVED_TYPES` tuple — add `"mat3"`.
   - L2161-2166 unconditional matrix-kind global rejection.
   - L2176-2184 construct validator — mat2(4 floats) only; needs mat3(9 floats).
   - L2185-2223 binary-expression validator — matrix binary allows only
     `mat2 * vec2` (L2220-2223, tags `used.add("mat2-vector-multiply")`).
   - L2294-2357 index validator — no matrix path (see #4).
   - L2431-2433 function return-type ban on `kind=="matrix"`.
   - L2443-2444 function parameter-type ban on `kind=="matrix"`.
   - `reflect` missing from `_BUILTINS`/`APPROVED_CAPABILITIES` (L220-241) —
     needs node-identity admission, not vocabulary growth.

7. **Exact site inventory, emitter** (`tools/glslcpp/emit_typed_cpp.py`):
   - L93-99 `_TYPES` dict — add `"mat3": "glsl::Mat3"`.
   - L1296-1325 Rotate's `matrix_return_program` gate — fires only when some
     function actually RETURNS a matrix type; none of the 7 target programs
     do, so this gate is orthogonal/inactive for this slice (verify: none of
     cellNoise/colorLab/moodscape/shapeMixer/shapes/adjust/colorspace declare
     a mat-returning function).
   - L1342-1370 construct emission — mat2 4-float case only (L1346-1351);
     needs mat3 9-float case emitting `glsl::Mat3(Vec3(...), Vec3(...),
     Vec3(...))`.
   - L1382-1392 index emission — needs a matrix-index identity-authorized
     path mirroring `_proved_grade_index`.
   - L1448-1450 binary matrix emission — mat2*vec2 only; needs mat3*vec3 (and
     mat3*mat3 for Slice C if pursued).
   - L1903-1932 matrix-return-function checks — Rotate-only, same as #2 above.

8. **`glsl::Mat<N>` is confirmed already fully generic**
   (`include/noisemaker/glsl_types.hpp`):
   - L221 `template<size_t N> class Mat`
   - L264 `using Mat2=Mat<2>; using Mat3=Mat<3>; using Mat4=Mat<4>;`
   - L231-232 `Mat<N>*Vec<N,float>` and `Vec<N,float>*Mat<N>`: accumulate in
     `double sum`, narrow ONCE via `noisemaker::f32(sum)` per output
     component. Matrix-vector narrowing-safe by construction (matches JS
     scalar-narrow-once pattern IF JS does the same — see #9, still checking).
   - L235 `Mat<N>*Mat<N>`: `result[column] = a * b[column]` — i.e. each
     column of the product is itself a `Mat<N>*Vec<N,float>`, so it also
     narrows via `f32(sum)` once per element, using the ALREADY-f32-narrowed
     columns of `a` and `b` as inputs to the next dot product.

9. **IMPORTANT — checking the "matrix-matrix never narrows in JS" claim
   directly against LIVE JS source, and so far it looks WRONG or at least
   incomplete as stated in the roadmap.** Read
   `../noisemaker-for-cpu/src/csl/glsl-runtime.js` `matrixMult` (L276-306):
   - `alloc(length)` (L120-124) returns a **`Float32Array`** from a pool, not
     a plain `Array`. (Contradicts roadmap's "accumulates into a plain
     Array".)
   - Both the matrix-vector branch (L281-291) and the matrix-matrix branch
     (L294-305) accumulate `sum` as a local JS number (implicit double) and
     explicitly call `F32(sum)` (== `Math.fround`) before storing into the
     Float32Array `out`. So BOTH branches narrow once per output element —
     structurally identical to what C++ `Mat<N>` does.
   - Only **2** call sites of `matrixMult(` exist in the entire compiled
     `canonical-kernels.js` (lines 2919, 3263), both of the chained form
     `matrixMult(matrixMult(T, Q), S)` — i.e. matrix*matrix*matrix, not
     matrix*vector. Need to identify which factories/programs these belong
     to (suspect `glitch`, per roadmap, and one more — investigating).
   - **No matrixMult() call in canonical-kernels.js is a plain single
     matrix*vector call.** This means matrix-vector multiplies for the
     census's Slice-B candidates are NOT materialized as `matrixMult()`
     calls at all — the transpiler must be inlining them as unrolled scalar
     arithmetic (dot products written out by hand), which is the "parity
     target is glsl-transpiler's materialization, not GLSL semantics" hazard
     from the roadmap. STILL NEED: find the actual inlined-arithmetic shape
     for each of the 7 target programs' matrix ops in canonical-kernels.js
     and confirm per-site whether/where narrowing happens, since the
     generic `matrixMult` helper analysis above may not even be what's
     emitted for these programs.

## Checkpoint 2 — deep findings that CORRECT the roadmap/census

10. **Re-ran layers 1-3 against the LIVE tree (154 typed, not the 131-typed
    frozen census snapshot): byte-identical results**, including exact
    line:column numbers. `probe_layers123.json` confirms
    `census/relaxed_global_probe.json`, `relaxed2_mat3_probe.json`,
    `relaxed3_mat3_probe.json` all still hold. Frozen-vocabulary count
    independently re-verified by direct enumeration: `APPROVED_CAPABILITIES`
    (generate_typed_slice.py L220-231) has exactly 44 entries; `APPROVED_TYPES`
    (L242-245) is a separate 16-entry list, unaffected by the 44-freeze.

11. **MAJOR CORRECTION to the roadmap/census: the "matrix indexing" blocker
    behind 6 of the 7 programs is NOT matrix indexing at all.** Traced the
    exact source line for every one of cellNoise/colorLab/moodscape/shapes/
    adjust/colorspace's `unsupported typed expression index` blocker (layer
    3) down to the real preprocessed source line (line numbers shift vs. the
    raw corpus file because `#ifdef GL_ES`/`precision`/`#endif` lines are
    physically deleted, not blanked, during preprocessing -- had to fetch
    `parse_program(...)["source"]` directly rather than trust raw-file `grep
    -n`). Every one of the 6 is `linear[i]` / `srgb[i]` inside a **byte-
    identical shared helper `vec3 linearToSrgb(vec3 linear)`** (sha256
    `aa5ce4bbf69fa6b1...`, confirmed identical across ALL 7 programs
    including shapeMixer): a `for (int i=0;i<3;++i)` loop dynamically
    indexing a **vec3 by its own loop counter**, not a matrix at all. This
    has NOTHING to do with mat3/Mat<N> support -- it is a separate, smaller,
    highly reusable capability (dynamic vec3-lane index bounded by a proven
    counted-for loop 0..2), structurally similar to (but distinct from) the
    existing `literal_vec3_lane_index_profile` and grade's
    `grade_index_expression_profile` node-identity mechanisms. colorLab
    additionally has a mirror-image `srgbToLinear` (same shape, one more
    site). Confirmed reusable/shared: same profile could cover all 6 (7
    once shapeMixer's prerequisite chain is cleared -- see #13).

12. **Reachability confirms `moodscape`'s ENTIRE matrix+hash closure is
    dead** at its authorized `_defaults()` defines: neither
    `linear_srgb_from_oklab` nor `oklab_from_linear_srgb` nor the
    `randomFromLatticeWithOffset`-borne `floatBitsToUint` call is in
    `main()`'s reachable-function set. This corroborates the earlier "Matrix
    dispatch -- 6 real targets, not 9" study's dead-code finding
    independently via live BFS. **Correct fix for moodscape is a
    provably-dead exemption, not real mat3/vec3-index/floatBitsToUint
    support** -- building the real mechanisms would be strictly more work
    than proving the closure unreachable and exempting it.
    `adjust`/`colorspace` by contrast have ZERO non-reachable matrix-
    touching functions -- fully live, need the real mechanism.

13. **MAJOR CORRECTION: `shapeMixer` is not a 1-builtin fix (`reflect`) --
    it is at least a 5-deep bespoke chain, unrelated to mat3.** Peeled
    layer-by-layer with a debug build (`generate_typed_slice_relaxed3_debug.py`,
    confirmed via a print instrumented at the index-check site that ZERO
    index nodes are visited before the first error -- proving the reported
    order is real, not a probe artifact): `typed.functions` is sorted
    **alphabetically**, and `blend` (containing `reflect`/`refract`/
    `mod(vec3,vec3)`) sorts before `linearToSrgb`, which is why those surface
    first even though `linearToSrgb`'s vec3-index gate is equally live in
    shapeMixer. Chain found so far: mat3 admission -> `reflect` (L672) ->
    `refract` (same fn, next branch) -> `mod(vec3,vec3)` overload (not in the
    admitted `{(float,float),(vec2,float),(vec2,vec2)}` tuple) -> the shared
    `linearToSrgb` vec3-index gate (now confirmed shared, not unique) ->
    `floatBitsToUint` in `randomFromLatticeWithOffset` (reachable=True,
    unlike moodscape) -> almost certainly the scalar-uint-XOR bitwise gate
    next (roadmap's bitwise section independently names
    `randomFromLatticeWithOffset` as shared across
    `bitEffects/kaleido/shapeMixer/shapes/synth/shape`) -- **did not fully
    exhaust the chain, stopped after 5 confirmed distinct capability gates**.
    **Recommendation: exclude shapeMixer from the mat3-admission slice
    entirely** -- its blockers are overwhelmingly NOT about matrices.

14. **`shapes` also needs the shared `randomFromLatticeWithOffset`
    `floatBitsToUint` site, and it IS reachable=True** (unlike moodscape) --
    so `shapes` genuinely needs floatBitsToUint node-identity admission
    (existing mechanism, just needs its authorized-identity list extended)
    on top of mat3 + the shared vec3-index profile. Likely also needs the
    bitwise-XOR capability per the same shared helper -- not yet confirmed
    layer-by-layer for `shapes` specifically (time-boxed).

15. **`cellNoise`, `filter/adjust`, `filter/colorspace` are the clean core.**
    With ONLY (a) global admission widened for mat3, (b) mat3 construct/
    binary/index handling added, and (c) the new shared vec3-loop-index
    profile, these 3 reach full **VALIDATOR-PASS** (`probe_layer4.json`).
    The only remaining failure at that point is the EMITTER's OWN,
    structurally-identical, not-yet-widened admission loop
    (`emit_typed_cpp.py` `_validate_source_globals`, L844-900) --
    confirming it needs the identical widening applied a second time,
    independently, in the emitter.
    - `cellNoise` additionally has `rotate2D` (mat2, not mat3) among its
      matrix-touching functions but it is NOT reachable from main -- inert,
      no interaction with this work.
    - `colorLab` needs the vec3-index profile applied TWICE (linearToSrgb
      AND its mirror srgbToLinear, same shape).

16. **Global-declaration type/initializer inventory, exhaustive, all 25
    programs** (`probe_global_inventory.json`, via direct AST walk, not
    inference):
    - **const int**, literal or `literal +/- literal` initializer:
      bitEffects (2), glyphMap (1), historicPalette (1), osd (4), palette
      (4), spookyTicker (4), texture (1) -- 7 programs, ints always exact
      (no narrowing risk).
    - **const uint**, literal (including hex `0x1234u`) initializer: fxaa
      (1), grain (6), normalMap (2), snow (1) -- 4 programs, also exact.
    - **const vec3**, `vec3(float,float,float)` construct from 3 float
      literals: edge (1), emboss (1, and this program's REAL second blocker
      is unrelated -- see below), fxaa (1), scanlineError (6),  snow (3),
      wobble (2) -- 6 programs. Each component is an independent literal,
      narrows identically in both languages -- no narrowing risk.
    - **const mat3** (7 programs, see above) -- 4 mat3 globals each
      (fwdA/fwdB/invB/invA) except adjust/colorspace which only declare
      fwdA/fwdB (their invA/invB-needing `oklab_from_linear_srgb` is dead).
    - **const array** at GLOBAL scope: `normalMap` (`ivec2[9]`, `float[9]`
      x2, all with full literal-list constructors) -- genuine global fixed-
      size array consts, a DIFFERENT capability from the const-scalar
      widening (needs an admission proof shaped like the existing
      `fixed_nine_table_proof`/task19 family, generalized to GLOBAL rather
      than local scope). `osd`/`spookyTicker` (`const int[80] GLYPHS`) same
      story, bigger table.
    - **const struct-array**: `historicPalette`
      (`const HistoricPalette[21] PALETTES`), `palette`
      (`const PaletteEntry[55] PALETTES`) -- blocked on struct support
      entirely (`typed.structs` is unconditionally rejected,
      generate_typed_slice.py ~L2155), out of scope for ANY global-admission
      widening; needs its own struct-type mechanism first.
    - **`filter/emboss`'s real second blocker is NOT its global** (`const
      vec3 LUMA`, trivially admitted by the vec3 widening) **but an
      unrelated LOCAL** `float kernel[9];` inside `colorDefaultEmboss`
      (line 27 preprocessed) -- needs the EXISTING `fixed_nine_table_proof`
      mechanism's `SOURCE_LOCKS` extended to this program, not new global-
      admission machinery. The 25-program "global declaration family" label
      is a *methodology* artifact (whatever fails right after global-
      admission is relaxed), not a guarantee every listed blocker is really
      about globals.
    - **Mutable (non-const) globals -- confirmed correctly excluded**:
      `cellRefract`/`kaleido` declare non-const `float emboss[9]` (etc.,
      5 arrays each) with NO initializer, populated by scattered assignment
      statements inside `main()`; `synth/shape` declares non-const `float
      aspectRatio`/`vec2 globalCoord` similarly assigned once in `main()`
      and read by helpers as ersatz shared state. These must **stay
      rejected** by preserving `storage == "const"` as a hard requirement
      in the widened admission loop -- admitting them is a categorically
      different, much riskier "mutable module-level scratch state" feature
      (cross-function reentrant state), not const-global widening.

## Next steps
- Identify factory numbers for cellNoise/colorLab/moodscape/shapeMixer/
  shapes/adjust/colorspace in canonical-kernels.js; read their actual mat3
  arithmetic (inlined or matrixMult-based).
- Identify the 2 chained-matrixMult factories (candidates: glitch and one
  other) and confirm whether they are among the 7 census targets or a
  DIFFERENT set (matrix Slice-B/C precompute referenced 5 narrowing-safe
  programs + glitch for Slice C — need to reconcile with the 7-program
  census cluster, which may not be the same set as the precompute's).
- Reachability + discriminability per program (main() call graph at
  `_defaults()`).
- Write `global-admission-design.md`.
- Write probe scripts + JSON + .sha256 sidecars, re-running against live tree.
