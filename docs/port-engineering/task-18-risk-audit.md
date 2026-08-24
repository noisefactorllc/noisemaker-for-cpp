# Task 18 implementation-risk audit: fixed 3-by-3 counter-filled tables

Date: 2026-08-10  
Scope: projected post-Task-17 baseline (110 typed / 112 public), read-only
inspection of the pinned corpus and canonical CPU implementation. No
repository file was changed and no Git command was used.

## Recommendation

The smallest coherent next slice is the exact two-key,
source-identity-locked capability:

```text
fixed-grid-counter-store-v1
  filter/celShading:celShadingEdges
  filter/outline:outlineSobel
```

Both programs have exactly one local `float[9] samples` table, initialized by
the same 3-by-3 literal nested grid and a fresh `int idx=0`: each of nine
inner-loop visits performs one `samples[idx] = scalar` store followed by a
discarded `idx++`. After the grid they use only literal array reads. The pair
shares the new proof obligation that Task 17 deliberately did not admit: a
dynamic local array store whose index is a bounded visit counter.

The remaining source differences (Cel's RGB luminosity helper and smoothstep,
Outline's scalar fetch and metric helper) already pass the existing capability
frontier. They do not justify splitting the counter/table contract. There is
no smaller safety blocker within this pair, provided the capability remains
source-key-specific and does not turn Task 16's special postfix handling into
a general `post` expression feature.

## Counts and provenance lock

The projected baseline is 110 typed / 112 public over the 212-program pinned
manifest. Adding exactly this pair produces 112 typed / 114 public / 98
publicly unported programs. This remains a projection until Task 17 is
accepted; it is not permission to add the entries now.

| Key | Raw / normalized SHA-256 | Defines | Exact binding signature | Pass route and source-bound defaults |
| --- | --- | --- | --- | --- |
| `filter/celShading:celShadingEdges` | `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` / `c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e` | `{}` | `tileOffset:vec2@1, fullResolution:vec2@2, colorTex:sampler2D@3/S1, edgeWidth:float@4, edgeThreshold:float@5, renderScale:float@6` | `colorTex <- celShadingColorTex`, `fragColor -> celShadingEdgeTex`; `edgeWidth=1`, `edgeThreshold=0.15`, runtime `renderScale=1` |
| `filter/outline:outlineSobel` | `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` / `fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d` | `{}` | `tileOffset:vec2@1, fullResolution:vec2@2, valueTexture:sampler2D@3/S1, sobelMetric:float@4, thickness:float@5, renderScale:float@6` | `valueTexture <- outlineValueMap`, `color -> outlineEdges`; metadata `shape=1 -> sobelMetric`, `thickness=1`, runtime `renderScale=1` |

Both are `vec4` outputs. The first has canonical factory text hash
`62ffbbb0f46ac845179fef5e8d702874bdbeeac527a38abc35896c68dfa1b3d8`;
the second `5e19c5a1f4f2644b0d29981976c70741dcc1af4054a9608375a42e17644047b8`.
Task 18 should inherit Task 17's provenance philosophy, not its source
identity: bind its own raw and normalized source hashes, factory hash,
canonical runtime file hash, exact define map, binding order/types, frozen
oracles, and independently recomputed IR proof.

## Exact control, counter, and index proof

In the typed IR after counted-loop proof attachment, both array paths have:

| Program | Array / counter IDs in current parse | Loop facts | Store and post |
| --- | --- | --- | --- |
| Cel | `samples` id 19 `float[9]`; `idx` id 20; `ky` id 21; `kx` id 22 | outer and inner loops each `-1 <= value <= 1`, three trips; lexical product 9; recorded entrypoint charge 12 | `samples[idx]` then discarded `idx++` in the inner body |
| Outline | `samples` id 25 `float[9]`; `idx` id 26; `ky` id 27; `kx` id 28 | same literal grid, product 9, entrypoint charge 12 | same store-then-post ordering |

Those numeric symbol IDs are parse-local diagnostics only. Admission must
bind the immutable local identities produced by the fresh analysis, exact
source/profile identity, and structural control ancestry. It must prove:

1. `samples` is the only function-local `float[9]` accepted by this profile;
   it has no initializer, parameter/return/global/storage/alias/copy/escape.
   `idx` is a fresh writable `int`, initialized exactly to zero.
2. The sole dynamic index is precisely the `idx` identity at the one direct
   lvalue `samples[idx]`. At every store the counter interval is `[0,8]`.
   The store's scalar right side may use the source's existing fetch/helper
   expression, but cannot read/write `samples` or `idx`.
3. The lexical nested loops are exactly `ky=-1; ky<=1; ++ky` and within it
   `kx=-1; kx<=1; ++kx`, with no break/continue/return/conditional path in
   either body that can omit a store or post. Each of the nine visits has one
   store followed immediately by one value-discarded `idx++`; after the grid
   `idx` is exactly 9 and is never used as an array index again.
4. No alternate `idx` writes, reads-as-a-value, compound update, prefix/decrement,
   expression-valued postfix, second dynamic index, array call/return, or
   dynamic array read is admitted. Recompute this proof at validation and
   emitter boundaries; reject stale, forged, mismatched, or absent proof.

The `samples` literal read set in each program is
`{0,1,2,3,5,6,7,8}` across the two Sobel sums. Index 4 is not read, but the
contract should still require all nine stores: the exact grid proof provides
simple full definite initialization and prevents a later source mutation from
silently relying on zero fill.

## Early return and hot-path constraints

Each main function first obtains `textureSize` and has an early
`fragColor=vec4(0.0); return;` when either dimension is zero. The array and
counter declarations are after that branch. The proof must therefore model two
paths: the early return owns no array, while every normal-path pixel completes
all nine stores before the literal reads. Do not reject the pre-array return
merely because it is a return; do reject a return, break, continue, or
condition that enters/bypasses the initialization grid.

`Surface` normally requires positive dimensions in both runtimes, so this
branch is not reachable through ordinary public construction. It remains
source semantics and an important proof boundary; no Task 18 change should
invent zero-sized storage or optimize away the branch based on an assumption.

Pixel execution is fixed-cost: nine `texelFetch` calls, 18 `wrapCoord` helper
calls, nine stores, one post per store, and literal scalar reads. Preserve the
existing modulo/wrap and level-zero fetch semantics. The observed loop proof
has lexical product nine and entrypoint charge 12; any projected cost cap
must retain both quantities rather than confusing the 3+9 proof charge with
the nine actual inner visits.

## Canonical precision and C++ lowering

Both canonical factories allocate `samples` as a zero-filled plain JavaScript
Number array:

```js
var samples = [0, 0, 0, 0, 0, 0, 0, 0, 0];
```

Fetched scalar lanes and Cel's luminosity helper originate at F32 vector
boundaries, but the scalar array itself is ordinary Number storage. To retain
the current canonical scalar-temporary policy and zero-fill behavior, lower
only the proved profile to:

```cpp
std::array<double, 9> samples{};
```

Not `std::array<float,9>` (which adds a noncanonical F32 scalar storage
boundary), not uninitialized storage (which diverges from canonical zero-fill
and risks undefined behavior), and not `std::vector`/heap allocation. Direct
`samples[static_cast<std::size_t>(idx)]` is acceptable only after the store
interval proof; do not use `at()` because an exception path conflicts with
the allocation-free `noexcept` pixel contract. The raw table payload is 72
bytes per pixel invocation. Actual whole-frame stack usage remains
compiler/ABI dependent and must be measured in debug and release.

## Exclusions

- Do not admit generic arrays, generic dynamic indexing, arbitrary counters,
  other sizes/types, partial initialization, nested data structures, array
  parameter/return ABI, or generic postfix statements.
- Task 17's literal-init/direct-induction-read pair remains separate: its
  table writes are static and it has no visit-counter store.
- `classicNoisedeck/refract:refract` needs array-parameter ownership/alias
  rules; `synth/sacredGeometry:sacredGeometry` needs affine `vec2[13]`
  initialization and a 13-by-13 read grid.
- No full Cel Shading or Outline effect is newly ported: this adds only these
  pass factories, not their sibling passes/workflows.

## Required verification

1. Validator/proof negatives for wrong key/digest/defines/bindings, missing
   pre-array early-return shape, altered loop bounds/order/nesting, skipped or
   reordered store/post, `idx` nonzero/dynamic initialization, duplicate or
   missing store, out-of-range interval, counter value use, dynamic read,
   wrong lvalue, prefix/decrement/compound post, and stale/forged proof.
2. Emitter checks for only these two profiles, `std::array<double,9>{}`,
   direct proved indexing, no `at`, no heap/ABI/resource changes, retained
   `noexcept`, and source-order store before increment.
3. Frozen direct canonical oracles per key with non-square F32 textures,
   nonzero tile/full resolution, edgeWidth/thickness values that exercise
   wrapped negative and positive offsets, Cel edge thresholds around the
   smoothstep boundary, and Outline metrics 1, 2, 3, and 4 (especially the
   canonical F32 `1.4140000343322754` metric-4 divisor). Record F32 and
   RGBA8 hashes, lane-bit probes, orientation, canonical/source hashes, and
   repeat identity.
4. Differential debug/release native tests plus stack measurement. Confirm
   projected counts 112 typed / 114 public / 98 unported and that neither
   whole workflow nor adjacent array user is added.

