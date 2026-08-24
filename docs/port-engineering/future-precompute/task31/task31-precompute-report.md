# Task 31 next-slice precompute — Curl vs. Caustic vs. Lighting

Read-only analysis. Revision probed: `a024dc3a960cc44af454abc7aebce50456c194e6`
(same corpus snapshot as the roadmap and Task 30). Starting state confirmed by
re-running the real pipeline against the current tree: **130 typed / 132
public / 80 publicly unported**, sorted-typed-key SHA-256
`d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904` (computed
directly from `tools/glslcpp/typed_slice.json` as it exists today, after
Task 30 Extrude). No file under `.`
was written — verified with `find . -type f -newer <session-start marker>`
returning nothing outside `__pycache__`. Every claim below traces to a command
actually run (`probe_task31.py`, `runtime_gap_check.py`, both saved alongside
this report with `.sha256` sidecars) or a `file:line` actually read.

## TL;DR ranking

1. **`classicNoisedeck/caustic:caustic`** — winner. Two admission gates
   (`floatBitsToUint`, then scalar `uint ^ uint`), both clear completely: the
   probe script drove the pipeline all the way to a full, successful render
   (`emitter: pass`, 33,146 bytes of C++) with no third gate. Everything lives
   in one function. Zero loops in the reachable graph. The scalar-XOR half
   needs literally no new C++ runtime code (native `^` on `uint32_t`), and
   there is a working, nearly-directly-reusable template for the
   authentication shape (`perlin_scalar_uint_xor_profile.py`).
2. **`synth/curl:curl`** — very close second, same size class. Two admission
   gates (`tanh`, then `mod(vec3,float)`/`mod(vec4,float)` overloads) also
   clear completely to a full render (15,659 bytes). Slightly larger blast
   radius: the closure spans 4 functions instead of 1, and fixing `mod`
   touches a **shared, already-in-use** runtime template (5 overloads
   currently pinned to `requires(N==2)`) rather than adding one net-new
   function, so review has to confirm nothing else in the admitted corpus
   depends on `mod`'s current 2-lane-only shape.
3. **`filter/lighting:lighting`** — real work, not a Task-30-sized slice. The
   `reflect` gate is as mechanical as Curl/Caustic's builtins (the C++ runtime
   already implements `reflect` generically for any `N`, so it needs zero new
   runtime code). But the second gate — three `float[9]`/`vec2[9]` local
   tables inside a **helper function**, not `main` — cannot be admitted by
   any builtin/type toggle. The only sanctioned array mechanism in this
   codebase, `prove_fixed_nine_local_tables()`, hardcodes searching the
   function literally named `main`
   (`tools/glslcpp/frontend/fixed_nine_table_proof.py:93`). Lighting's tables
   live in `calculateNormal()`. Reuse therefore requires generalizing that
   shared proof function itself — a change that also has to keep Sharpen's
   and Sobel's existing whole-program lock hashes passing — not just adding a
   third dict entry the way the roadmap's §6 "new fingerprint only" line
   assumed (that line was written about `emboss`, not `lighting`; the two are
   not equivalent).

## Per-candidate evidence

All three identity tables were produced by `probe_task31.py::identity_row`,
which copies the `_whole`/`_interface` field order verbatim from
`tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py` so the
hashes are directly comparable to Task 30's report.

### `synth/curl:curl`

| Field | Value |
|---|---|
| Raw bytes / SHA-256 | 7,290 / `33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce` (matches manifest) |
| Normalized bytes / SHA-256 | 4,673 / `405774c12a29bff814b92ffbe2cc5f3b267367aa40832befc59b509573be91e9` |
| Defines | `{'OCTAVES': 1, 'OUTPUT_MODE': 3, 'RIDGES': True}` |
| Function count | 7 |
| Whole-program SHA-256 | `a7c44947e08fdf478857d1f9c400cd5072df99a14ae4d63aebcbd6d1fc1d9374` |
| Interface SHA-256 | `0ff5180a4e2bbbf81e9a2705e99a155d9e9c378fbcbe5729eaa43a941c0227ae` |
| Loop-proof tuple `(count, unproved, max_depth, max_lexical_product, entrypoint_charge, acyclic)` | `(1, 0, 1, 1, 12, True)` |
| Resources `(uniforms, samplers, outputs, uses_texture, uses_derivatives)` | `(8 uniforms, [], ['fragColor'], False, False)` |

**Current gates** (unmodified pipeline, re-run today):
- Validator's first blocker: `synth/curl:curl:196:12: unsupported builtin tanh`
- Emitter's first blocker (independent walk order): `synth/curl:curl:32:12: unsupported builtin mod overload`

**Full second-order chain** (`probe_task31.py::probe_curl_chain`):

| Step | Patch applied | Validator | Emitter |
|---|---|---|---|
| 0 | none | `tanh` at 196:12 | `mod overload` at 32:12 |
| 1 | admit `tanh` | `mod overload` at 32:12 | `mod overload` at 32:12 |
| 2 | admit `tanh` + relax `mod` overload allowlist to add `(vec3,float)`,`(vec4,float)` | **pass** | **pass** (15,659 bytes) |

The chain terminates at step 2 with a full, successful render. This
**confirms and completes** the older ranked-handoff's claim ("next gates are
`mod(vec3,float)` and `mod(vec4,float)`") against the current tree — the claim
was exactly right, and once both are admitted nothing else blocks Curl.

**New AST closure** — exactly 4 nodes, 2 distinct capability shapes, spanning
4 functions:

| Owner function | Span | Kind | Types |
|---|---|---|---|
| `main` | 196:12-196:34 | `tanh(vec3)->vec3` | `[vec3]` |
| `permute(vec3)` | 32:12-32:47 | `mod(vec3,float)->vec3` | `[vec3, float]` |
| `permute(vec4)` | 35:12-35:47 | `mod(vec4,float)->vec4` | `[vec4, float]` |
| `simplex3D` | 65:9-65:22 | `mod(vec3,float)->vec3` | `[vec3, float]` |

No other `mod`/`tanh` site exists anywhere in the reachable graph (step 2's
full pass proves this — any extra site would have raised).

**Runtime gap** (`runtime_gap_check.py`, `include/noisemaker/glsl_runtime.hpp`):
- `tanh`: **absent entirely.** JS reference (`glsl-runtime.js:352`) is
  `tanh: unary(Math.tanh)`. C++ needs one scalar overload
  (`glsl::tanh(double)`, mirroring `sin`/`cos`/`sqrt` at lines 36-48) plus one
  macro line (`NOISEMAKER_GLSL_UNARY_VECTOR(tanh)`) to get the vector form —
  the exact same 2-line pattern as any of the 9 existing unary-vector
  builtins.
- `mod(vec3,float)`/`mod(vec4,float)`: `mod` **already exists** but all 5
  vector template overloads (`glsl_runtime.hpp:66-71`) are constrained
  `requires(N == 2)`. This is a **modification of a shared, already-admitted
  template** (used by every program that currently calls `mod(vec2,...)`),
  not a new function — relax the constraint to `N==2||N==3||N==4` (or drop it)
  on all 5 lines. Low risk (adding instantiations doesn't change existing
  `N==2` behavior) but it is the one place Curl's fix touches code shared with
  other already-shipped programs, which Caustic's fix never does.

### `classicNoisedeck/caustic:caustic`

| Field | Value |
|---|---|
| Raw bytes / SHA-256 | 15,645 / `161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d` (matches manifest) |
| Normalized bytes / SHA-256 | 7,999 / `b4a45216e62c5facade77e64925075e736ee3ed0eb7b1798bc777ba1bb714b83` |
| Defines | `{'NOISE_TYPE': 10}` |
| Function count | 22 |
| Whole-program SHA-256 | `b0ffb30caee0d301f54d42892a6e70619fd4cf1e4c19d5fc3f399b3bfc598624` |
| Interface SHA-256 | `094c31b573c08cfdf9e3c76e766c4b4ca96a2df12d6a1629f18b141624464b50` |
| Loop-proof tuple | `(0, 0, 0, 0, 0, True)` — **zero loops** in the reachable graph under the default `NOISE_TYPE=10` |
| Resources | `(11 uniforms, [], ['fragColor'], False, False)` |

**Current gates:**
- Validator and emitter agree exactly (unusual — Curl and Lighting's
  validator/emitter disagreed on the first blocker; Caustic's don't):
  `classicNoisedeck/caustic:caustic:192:21: unsupported builtin floatBitsToUint`

**Full second-order chain** (`probe_task31.py::probe_caustic_chain`):

| Step | Patch applied | Validator | Emitter |
|---|---|---|---|
| 0 | none | `floatBitsToUint` at 192:21 | `floatBitsToUint` at 192:21 |
| 1 | admit `floatBitsToUint` | `unsupported binary operator ^` at 195:10 | same |
| 2 | admit `floatBitsToUint` + admit scalar `uint^uint` (diagnostic operator-level patch, mirroring the already-shipped Perlin scalar-XOR shape) | **pass** | **pass** (33,146 bytes) |

Also terminates cleanly at step 2 with a full successful render — **no third
gate**. This directly answers the prompt's "how much is reusable" question:
see below.

**New AST closure** — exactly 4 nodes, all inside **one** function
(`randomFromLatticeWithOffset`, id 94):

| Span | Kind | Types |
|---|---|---|
| 192:21-192:46 | `floatBitsToUint(float)->uint` | `[float]` |
| 195:10-195:46 | `uint ^ uint -> uint` | `[uint, uint]` |
| 196:10-196:46 | `uint ^ uint -> uint` | `[uint, uint]` |
| 197:10-197:47 | `uint ^ uint -> uint` | `[uint, uint]` |

Source shape (`caustic.glsl:220-229`, raw file numbering — differs from the
in-pipeline spans above because of preprocessor normalization under
`NOISE_TYPE=10`, confirmed by direct execution rather than assumed):
```glsl
uint fracBits = floatBitsToUint(seedFrac);
uvec3 jitter = uvec3(
    (fracBits * 374761393u) ^ 0x9E3779B9u,
    (fracBits * 668265263u) ^ 0x7F4A7C15u,
    (fracBits * 2246822519u) ^ 0x94D049B4u
);
uvec3 state = uvec3(xBits, yBits, seedBits) ^ jitter;   // already-supported uvec3^uvec3, NOT part of this closure
```
The trailing `uvec3 ^ uvec3` is already legal today (vector XOR is already
admitted); only the three **scalar** `uint ^ uint` XORs feeding `jitter`'s
components are new.

**Runtime gap:**
- `floatBitsToUint`: **absent entirely** (new, ~1 line:
  `std::bit_cast<std::uint32_t>(float)`). JS reference is a shared
  `Float32Array`/`Uint32Array` buffer alias (`glsl-runtime.js:411-414`).
- Scalar `uint ^ uint`: **zero new runtime code.** It's the native C++ `^`
  operator on `std::uint32_t` — confirmed directly: the diagnostic probe's
  emitter branch emits a bare `(left ^ right)` C++ expression (no
  `glsl::bitwise_xor()` call, unlike the vector case) and the emitter still
  reports `pass`.

**Perlin-XOR machinery reuse — precise answer to the prompt's question.**
`tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py` is wired into
`gen.py`/`emit.py` via its own `perlin_scalar_uint_xor_profile: str | None`
kwarg, exactly parallel to how Extrude's
`extrude_bvec2_relational_reduction_profile` kwarg is wired (both files follow
identical shape: `_whole`/`_interface` helpers with the same field order, an
`authenticate_*` function that checks raw/normalized bytes+hash, defines,
function count, whole/interface hash, loop-proof tuple, then walks the tree
and asserts exact object identity + span + SHA on every XOR/relational node,
raising on anything unexpected).
- **What's reusable (~100%, as a template):** the entire *pattern* — a new
  `caustic_scalar_uint_xor_profile.py` module can be built by copying
  Perlin's file almost verbatim: same helper functions, same authenticate
  signature, same "collect every XOR site in the whole program and assert the
  count/identity/ancestry" strategy, same `_OPTIONAL_PROOF_FIELDS` absence
  check, same wiring shape into both `gen.py` and `emit.py`.
  `floatBitsToUint` also needs authenticating alongside it (Perlin's XORs
  don't originate from a `floatBitsToUint` call, so that half of Caustic's
  profile has no direct precedent to copy — it's a one-node
  builtin-identity check, structurally simple but net-new).
- **What's NOT reusable (0%, as data):** every single hash, span, function
  id, and reachability set in `perlin_scalar_uint_xor_profile.py`
  (`PERLIN_KEY`, `_RAW_SHA256`, `hash3`'s function id 49, the exact call
  graph `(45,46,48,50,51,52,53,54,55,56)` vs `(47,49,57)`, etc.) is
  Perlin-specific and would need computing fresh for Caustic — a completely
  different program with different function ids, different spans, a
  different call graph, and 3 XOR sites instead of Perlin's 2.
  Concretely: Caustic's task is "write a new profile module using Perlin's
  as a structural template," not "extend or parameterize Perlin's module" —
  there is no shared dict/constant a Caustic entry could be appended to (unlike
  Sharpen→Sobel inside `fixed_nine_table_proof.py`, which genuinely is one
  shared module with per-key dictionaries).

### `filter/lighting:lighting`

| Field | Value |
|---|---|
| Raw bytes / SHA-256 | 6,049 / `a0601f7012f385c14c1bdb9f462e5dcb303fe05cfbb4645484d5d1bd629e1a4f` (matches manifest) |
| Normalized bytes / SHA-256 | 4,997 / `c35208b3f864c1a3a75e0aa1f500fab3391c3bef31c6e80da153f04e02b6f343` |
| Defines | `{}` |
| Function count | 6 |
| Whole-program SHA-256 | `a24152ae1a234052831e0ab0761aa1b5389ed6aa9a3ea59b5ae1a09216c6220b` |
| Interface SHA-256 | `ee35749b616ce087ae1b837c9f5da32f1e27b795904edc8ed19249451551fc2d` |
| Loop-proof tuple | `(1, 0, 1, 9, 9, True)` — one proved 9-trip loop (the Sobel convolution) |
| Resources | `(16 uniforms, ['inputTex','heightMap'], ['fragColor'], True, False)` |

**Current gates:**
- Validator and emitter agree: `filter/lighting:lighting:93:26: unsupported builtin reflect`

**Full second-order chain** (`probe_task31.py::probe_lighting_chain`):

| Step | Patch applied | Validator | Emitter |
|---|---|---|---|
| 0 | none | `reflect` at 93:26 | `reflect` at 93:26 |
| 1 | admit `reflect` | `unsupported typed type float[9]` at 40:11 | `unsupported fixed-nine array declaration` at 40:11 |
| 2 | **diagnostic only** — steps 1 + bypass `reject_type`'s array-kind rejection for exactly `float[9]`/`vec2[9]`, validator side only | `unsupported typed expression index` at 41:5 | `unsupported fixed-nine array declaration` at 40:11 (unchanged — no emitter-side toggle exists) |

Step 2 is explicitly diagnostic, not a real capability. It proves the chain
**does not terminate by admission alone**: even bypassing the declaration
type check surfaces a *further*, separate gate (indexed writes into the
array, `sobel_x[0] = -1.0;` etc.) that the same mechanism also blocks, and the
emitter has no equivalent toggle at all — `_validate_source_globals`-style
inline relaxation doesn't apply here because fixed-nine arrays are gated by a
**whole-program structural proof**
(`prove_fixed_nine_local_tables()`/`SOURCE_LOCKS`), not an inline type check.

**Structural comparison to the live Sharpen/Sobel proof** — read directly
from `filter/lighting/lighting.glsl:41-76` vs. `filter/sobel/sobel.glsl:28-58`:

```glsl
// Lighting (inside helper calculateNormal(), NOT main):
float sobel_x[9];
sobel_x[0] = -1.0; sobel_x[1] = 0.0; sobel_x[2] = 1.0; ... sobel_x[8] = 1.0;
float sobel_y[9];
sobel_y[0] = -1.0; ... sobel_y[8] = 1.0;
vec2 offsets[9];
offsets[0] = vec2(-sampleSize.x, -sampleSize.y); ... offsets[8] = vec2(sampleSize.x, sampleSize.y);
for (int i = 0; i < 9; i++) {
    float height = getHeight(uv + offsets[i]);
    dx += height * sobel_x[i];
    dy += height * sobel_y[i];
}
```
```glsl
// Sobel (inside main() directly):
float sobel_x[9];
sobel_x[0] = 1.0; ... sobel_x[8] = -1.0;
float sobel_y[9];
sobel_y[0] = 1.0; ... sobel_y[8] = -1.0;
vec2 offsets[9];
offsets[0] = vec2(-texelSize.x, -texelSize.y); ... offsets[8] = vec2(texelSize.x, texelSize.y);
for (int i = 0; i < 9; i++) {
    vec3 texSample = texture(...).rgb;
    convX += texSample * sobel_x[i];
    convY += texSample * sobel_y[i];
}
```
The **shape is identical**: three 9-element tables (`float`, `float`, `vec2`,
literally the same variable names `sobel_x`/`sobel_y`/`offsets`), each
declared then filled by exactly 9 sequential literal-indexed stores (0..8),
then read exactly once per array inside one `for (i=0; i<9; i++)` loop
indexed by the induction variable — precisely the shape
`prove_fixed_nine_local_tables()` already proves and precisely the shape
`SOBEL_KEY`'s existing `_PROFILES` entry describes
(`("sobel_x","float",6),("sobel_y","float",16),("offsets","vec2",26)`).

**The one real difference, and why it's not "new fingerprint only":** every
structural check in `prove_fixed_nine_local_tables()`
(`tools/glslcpp/frontend/fixed_nine_table_proof.py:80-188`) operates on
`main.body[...]` — line 93 filters `functions` down to
`function.name == "main"` before indexing into its body at all. Lighting's
three tables live inside `calculateNormal()`, a helper called exactly once
from `main`. Reusing this machinery for Lighting therefore requires:
1. Generalizing `prove_fixed_nine_local_tables()` (and its
   `_whole_program_fingerprint`/`source_provenance_error` callers in
   `generate_typed_slice.py:1656-1673` and `emit_typed_cpp.py`) to search a
   named non-`main` function, not just append Lighting to the existing
   `_PROFILES`/`SOURCE_LOCKS`/`_LOOP_INDEX`/`_BODY_COUNT`/`_PAYLOAD`/
   `_LOOP_READS`/`_TYPED_IR_LOCKS`/`_WHOLE_PROGRAM_LOCKS` dictionaries (which
   *would* be sufficient if the tables were in `main`, as the roadmap's §6
   line about "new fingerprint only" assumes for `emboss` — not verified here,
   out of scope, but structurally plausible since `emboss`'s global-family
   context in the roadmap gives no evidence it's a helper-function case).
2. Doing so without breaking Sharpen's and Sobel's existing
   `_WHOLE_PROGRAM_LOCKS`/`_TYPED_IR_LOCKS` hashes, since both keep shipping
   through the same shared module.
3. Separately re-authenticating `reflect` at 93:26 (mechanical, same shape as
   Curl's `tanh`/Caustic's `floatBitsToUint` — zero runtime work, since
   `reflect` is already implemented generically for any `N` in
   `glsl_runtime.hpp:94-97`).

This is real generalization work inside a shared module used by two already-
shipped programs, not a same-day fingerprint-only addition — it is a
materially bigger task than Curl or Caustic.

**New AST closure** (declarations only shown; the full closure needed for a
real proof also includes all 27 literal-index store statements and all 3
loop-body reads per array, matching Sobel's existing 43-statement `main`-body
proof in size):

| Owner function | Span | Kind | Type |
|---|---|---|---|
| `applyReflection` | 93:26-93:51 | `reflect(vec3,vec3)->vec3` | — |
| `calculateNormal` | 40:11-40:21 | `float[9]` decl (`sobel_x`) | array |
| `calculateNormal` | 46:11-46:21 | `float[9]` decl (`sobel_y`) | array |
| `calculateNormal` | 51:10-51:20 | `vec2[9]` decl (`offsets`) | array |

## "Do not batch" pairwise analysis

| Pair | Shared types/semantics/runtime helpers? | Verdict |
|---|---|---|
| Curl + Caustic | None. Curl is `float`-vector math (`tanh`, `mod`); Caustic is `uint` bit-twiddling (`floatBitsToUint`, scalar `^`). No shared runtime function, no shared type, no shared AST shape. | Do not batch. Both are individually small (comparable to Extrude), but every prior task in this codebase (`round`/gather-sorted, Perlin XOR, Focus Blur sampler, Rotate mat2, Extrude bvec2, smooth-edge weights, lens-distortion comparer, literal-vec3-lane-index) is exactly **one program per profile module**. Combining two programs into one task breaks that precedent for no shared-mechanism benefit — pick one. |
| Curl + Lighting | None directly. Curl doesn't touch arrays; Lighting doesn't touch `mod`/`tanh`. Both eventually need a builtin admitted (`tanh` vs `reflect`) but that's the only surface similarity, and it's too thin to justify shared scaffolding. | Do not batch — different size classes entirely (Lighting needs the array-proof generalization; Curl doesn't). |
| Caustic + Lighting | None. Caustic is scalar-uint bitwise; Lighting is `float`/`vec2` fixed-size local tables plus one `reflect` call. No overlap in types, operators, or runtime helpers. | Do not batch — Lighting's real cost is the `prove_fixed_nine_local_tables()` generalization, which has nothing to do with Caustic's XOR profile. |

No pair shares enough to justify combining; every candidate should ship (if
ever) as its own single-key task, consistent with this codebase's established
one-profile-per-program pattern.

## Projected post-task state for the winner (Caustic)

Method (fully mechanical, reproducible from `tools/glslcpp/typed_slice.json`):
1. Read current typed keys, sort them.
2. Insert `"classicNoisedeck/caustic:caustic"`, re-sort.
3. `sha256("\n".join(sorted_keys) + "\n")` → new typed-list hash.
4. Public set = typed keys ∪ `{"filter/invert:inv", "synth/solid:solid"}`,
   sorted, same hashing scheme → new public-list hash.
5. Unported = 212 (total corpus) − public count.

| Metric | Before | After (Caustic added) |
|---|---|---|
| Typed count | 130 | **131** |
| Public count | 132 | **133** |
| Publicly unported | 80 | **79** |
| Sorted typed-key SHA-256 | `d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904` | `0741bca3f0bd8cc577a42824cd9da480fb462f36f6e5f5ed65e92b2ad95c3060` |
| Sorted public-key SHA-256 | `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056` | `64e2b0677d3e3bc70de1f34d2b389d6fb50ec7a71278676f1f65c53bab1829f5` |

Caustic's zero-based ordinal in the new sorted typed list: **0** — it becomes
the alphabetically first typed key (`classicNoisedeck/caustic:caustic` sorts
before the current first entry, `classicNoisedeck/coalesce:coalesce`).
Neighbours: **left = none** (new first element), **right =
`classicNoisedeck/coalesce:coalesce`**.

For reference, the same computation for the runner-up (Curl), in case the
operator prefers it: typed 131, public 133, unported 79 (same counts —
either single addition moves the totals identically), ordinal **120**,
neighbours `synth/cell:cell` (left) / `synth/gradient:gradient` (right),
sorted typed-key SHA-256
`ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2`, sorted
public-key SHA-256 `29da87160abcee096a3c5f1c27e1b39381664ad3a7b71342c62a4b2c5e434f8c`.

## Biggest surprise

Both Curl and Caustic's full second-order chains **terminate in a complete,
successful render** after exactly two admission-only patches — there is no
third gate for either. The task brief flagged Curl and Caustic as needing a
"full chain" walk precisely because the old ranked-handoff only checked one
step past the first blocker; running it all the way through on the current
tree shows both are actually *fully* mechanical two-capability closures, not
open-ended. Lighting, by contrast, looked like the most self-contained
"reuse an existing proof" story going in (a `fixed_nine_table_proof.py`
already exists and covers exactly this table shape) but turns out to be the
one candidate that cannot be closed by admission and needs real surgery on
shared proof code used by two already-shipped programs, because its tables
live inside a helper function rather than `main`.

## Artifact inventory

| Artifact | Purpose | SHA-256 |
|---|---|---|
| `probe_task31.py` | Identity capture + full second-order gate-chain probes for all three candidates (monkeypatch/restore technique) | see `probe_task31.py.sha256` |
| `task31-probe-output.json` | Raw JSON output of the above (identity, first gates, full chains, AST closures) | see `task31-probe-output.json.sha256` |
| `runtime_gap_check.py` | Exact `include/noisemaker/glsl_runtime.hpp` / JS-reference grep evidence for tanh/mod/reflect/floatBitsToUint | see `runtime_gap_check.py.sha256` |
| `runtime-gap-check-output.json` | Raw JSON output of the above | see `runtime-gap-check-output.json.sha256` |
| `task31-precompute-report.md` | This report | see `task31-precompute-report.md.sha256` |

All commands were re-run against the live tree during this session; nothing
here depends on the stale 127-typed `candidate-analysis.json` /
`ranked-handoff.md` from the prior precompute pass, though this report's
findings for Curl/Caustic/Lighting's *first* gates are consistent with that
older document's projections where it made any (it did not attempt a full
chain for any of the three).
