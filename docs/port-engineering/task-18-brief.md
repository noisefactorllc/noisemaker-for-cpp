# Task 18 frozen implementation brief

Status: corrected design independently APPROVED with no remaining P0-P3; implementation remains gated on Task 17 acceptance.

## Exact scope and count

Add one source-locked capability, `fixed-grid-counter-store-v1`, for exactly:

- `filter/celShading:celShadingEdges`
- `filter/outline:outlineSobel`

Conditional on the accepted Task 17 baseline, this moves the generated slice from 110 typed / 112 public / 100 publicly unported to 112 typed / 114 public / 98 publicly unported.

This is not generic array, dynamic-index, nested-loop-counter, or postfix-expression support.

## Source, defines, bindings, and provenance

Every retained canonical define tuple is exactly empty. Both validation and emission must independently hash retained raw and normalized source provenance and require empty immutable defines; caller-supplied digests are only additional gates.

- Cel raw/normalized SHA-256: `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` / `c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e`.
- Cel bindings: `tileOffset:vec2@1`, `fullResolution:vec2@2`, `colorTex:sampler2D@3/S1`, `edgeWidth:float@4`, `edgeThreshold:float@5`, `renderScale:float@6`.
- Outline raw/normalized SHA-256: `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` / `fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d`.
- Outline bindings: `tileOffset:vec2@1`, `fullResolution:vec2@2`, `valueTexture:sampler2D@3/S1`, `sobelMetric:float@4`, `thickness:float@5`, `renderScale:float@6`.

All bindings remain required and exactly typed. These pass factories do not claim either whole multi-pass effect.

## Immutable proof contract

Attach one frozen program-level proof after counted-loop and Task 16/17 proof attachment. Clear and independently reconstruct it at validator and emitter boundaries from exact typed structure and retained provenance.

For each source-specific profile prove:

1. The sole admitted array is one writable function-local `float[9] samples` declaration with no source initializer, parameter/return/global/qualifier/copy/alias/escape/call use.
2. A fresh writable local `int idx` is initialized exactly to zero immediately before the initialization grid and has no alternate writes or unaccounted reads.
3. The normal path contains exact lexical loops `ky=-1; ky<=1; ++ky` and nested `kx=-1; kx<=1; ++kx`. The prefix updates are typed `unary` nodes and are source locked; postfix replacements must reject. Each loop has three trips; lexical product is nine; existing program entrypoint charge remains 12.
4. Every inner-loop visit contains exactly one direct `samples[idx] = scalar` store followed immediately by one standalone discarded `idx++`. No branch, return, break, continue, second store/update, reorder, or intervening statement can skip or multiply either operation.
5. The store RHS matches the exact source-specific Cel luminosity/wrapped fetch or Outline scalar wrapped fetch tree and cannot read/write `samples` or `idx`.
6. The counter interval at stores is exactly 0 through 8; after the grid `idx` is exactly 9 and never indexes again. Prefix/decrement/compound/expression-valued post or other counter use rejects.
7. The only later array reads are literal signed-int indices `{0,1,2,3,5,6,7,8}` in the exact authored Sobel sum expressions. No dynamic read or index 4 read is admitted, but all nine stores remain mandatory.
8. Whole-program census accounts for every array-typed expression, every occurrence of the array/counter symbols, and every index expression. Exact body/control hierarchy, symbols, types, operators, store/update order, read expressions, resource interface, source digests, and empty define tuple are source locked.
9. The pre-array early-return branch remains exact: after `textureSize`, if either dimension is zero, assign `fragColor=vec4(0.0)` and return. This path constructs no table and performs no fetch/grid work. A return inside or bypass into the grid rejects.
10. Forged typed trees retaining authentic raw/normalized source, defines, spans, symbols, and supplied proof must reject at both boundaries when any declaration, predicate, loop, store, RHS, update, order, literal read, early-return, or control fact changes.

## Exact native lowering and hot path

Lower only the proved local declaration to:

```cpp
std::array<double, 9> samples{};
```

Use direct `samples[static_cast<std::size_t>(idx)]` for the proved dynamic stores and direct `samples[N]` for proved literal reads. Do not use `.at()`, generalize index emission, or add a throwing path in `noexcept` pixel code. The array is value initialized to match canonical JavaScript Number-array zero fill; `float` storage is forbidden because it creates a noncanonical F32 boundary.

Pixel work remains fixed: nine level-zero fetches, eighteen wrap helper calls, nine stores, nine discarded counter increments, and literal reads. No allocation, string/map/variant work, callback, virtual dispatch, new runtime dependency, or resource ABI change is permitted. Raw table payload is 72 bytes; report Debug/Release compiler `.su` frame evidence separately.

## Explicit exclusions

- Task 17 literal-store/direct-induction-read tables remain a separate capability.
- `classicNoisedeck/refract:refract`: array parameter ownership/alias ABI.
- `synth/sacredGeometry:sacredGeometry`: affine `vec2[13]` initialization and 13×13 reads.
- Every other array type/extent/profile, generic counter/store, partial initialization, array ABI, index form, postfix expression, or program key.

## Frozen external oracle

- Risk audit SHA-256: `45e7efad86d2b390068052bdec914a413bf3540ac8f5af6cf53ed1290a28cbda`.
- Oracle generator SHA-256: `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`.
- Oracle JSON SHA-256: `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`.
- Oracle report SHA-256: `16199e11d4ec8af8c4c5ecf86748d16573c2f53c61ed4e3bd4c79acec8a710f3`.
- Corrected scope/proof rereview SHA-256: `9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`.

The generator binds pinned canonical CPU factories directly, double-renders, and must pass `--check` without writes. Six cases use 7×5 top-down F32 input, 9×7 output, `tileOffset=[3,2]`, `fullResolution=[12,10]`, and exact F32 width/thickness `2.299999952316284` (`0x40133333`):

- Cel threshold 0.18f: F32 `d86694f5c5a05c094b1dc9d4302b0b98cbe3044e5ce22587fdf6dd80f77d27a7`, RGBA8 `966ca81461240fb6c35316537f631f3b74b6d0a33a7b538d05ddd12e241347e9`.
- Cel threshold 0.6f: F32 `048acf6f8feb3be40c9be548bc64eaeadc6de78366a61b778c899eb463575ac0`, RGBA8 `8d0418a7e7b046d582cafcfbbe95b1bf2c05478929a57719ab52a345de1091e5`.
- Outline metric 1: F32 `2e62cf4918bb2da1def8b146c4e33ef009d6c6ef05f96bf2d0fd2be4e7679a7f`, RGBA8 `a877af8b8229c67295f3c17123cbaa5a540e59e81a3f95af9db601be5b2eca90`.
- Outline metric 2: F32 `afac987ef587a22d89ed00f619edb97e29d321fb2cc57667ceea89c0d78744b0`, RGBA8 `e01ac082638be9679283946c758e093c5ea966bc79b8acdf14d8ee1213f084f8`.
- Outline metric 3: F32 `33eb93deef5ea41a7f085c4d3e9d8f4d5c3b4353b8490f0b9e0bbd2466c1d1ff`, RGBA8 `8c3a62bd220bf6321d1127ab2cb1823522ffe38e9e07f985af9aceb9e64a253c`.
- Outline metric 4: F32 `a4293babe12252aa6e0f4c4b50f6242ef4a1060297a40a1da12a549ea9c77047`, RGBA8 `db8a0a072ec1c5e85d8678100929a1ef5ecf5c6ffc88217536354d06f4a11f74`.

Use exact recorded F32 uniform bits for 2.3, 0.18, and 0.6. Metric 4 must retain the canonical F32 divisor `1.4140000343322754`; F32 hashes/probes are authoritative where RGBA8 clamps or rounds.

The public canonical and native APIs reject zero-sized surfaces, and native bindings/samplers retain concrete positive `Surface*` values. No zero-dimension sampler injection or new test/runtime/resource seam is authorized. The source early return is therefore verified structurally at both proof boundaries and in emitted-code dominance/order tests: the exact zero-dimension predicate, zero assignment, and return must precede every array declaration, fetch, grid loop, store, and counter increment. Forged IR that moves, removes, weakens, or bypasses that branch must reject. This documents the public-API-unreachable branch without changing `Surface` or pretending to execute it.

## Required acceptance evidence

- Semantic/proof positives for exact Cel/Outline profiles and immutable provenance.
- Both-boundary tamper negatives for every proof fact above, wrong key/raw/normalized/defines, same-normalized irrelevant define, changed-normalized define, stale/forged proof, bindings, and all exclusions.
- Exact emitter spellings, store-before-increment order, direct proved indexing, zero initialization, `noexcept`, and absence of `.at()`, allocation, callbacks, or dynamic dispatch.
- Required binding failure matrices; adjacent Refract/Sacred profiles remain excluded.
- All six frozen F32/RGBA8 cases, probe bits, orientation, and repeatability; both-boundary structural and emitted-code dominance tests for the public-API-unreachable zero-dimension early return.
- Full Python suite; all corpus/semantic/generator drift gates; Task 15–18 oracle `--check` gates.
- Fresh strict Debug/Release builds, direct native suite, CTest, generated hot-loop inspection, and `-fstack-usage` evidence.
- Exact counts 112 typed / 114 public / 98 publicly unported.

No Git command, branch, worktree, commit, push, or pull request is authorized.
