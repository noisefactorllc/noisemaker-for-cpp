# Task 17 frozen implementation brief

Status: corrected frozen design after a pre-implementation P2 review; implementation may begin only after independent re-review.

## Exact scope and count

Add one source-locked capability, `fixed-nine-local-literal-init-counted-read-v1`, for exactly:

- `filter/sharpen:sharpen`
- `filter/sobel:sobel`

Conditional on the accepted Task 16 baseline, this moves the generated slice from 108 typed / 110 public / 102 publicly unported to 110 typed / 112 public / 100 publicly unported.

The new capability is not a general array or index language.

## Source, defines, and bindings

Every define map is exactly `{}`.

- Sharpen raw/normalized SHA-256: `c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` / `1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0`.
- Sharpen binding order: `tileOffset:vec2@1`, `fullResolution:vec2@2`, `inputTex:sampler2D@3/S1`, `amount:float@4`, `renderScale:float@5`.
- Sobel raw/normalized SHA-256: `ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` / `d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c`.
- Sobel binding order: `tileOffset:vec2@1`, `fullResolution:vec2@2`, `inputTex:sampler2D@3/S1`, `amount:float@4`, `renderScale:float@5`, `alpha:float@6`.

Required bindings remain exact and fail closed. `tileOffset`, `fullResolution`, and `renderScale` are runtime bindings, not inferred defaults.

## Immutable proof contract

First extend parser-to-typed provenance so every `TypedProgram` immutably retains both the original raw source and the runtime define map in a canonical type-tagged form. Canonical define entries must be key-sorted and distinguish `bool`, `int`, finite `float`, and `str` values; no caller-owned mutable mapping may survive. Existing normalized `TypedProgram.source` remains separately retained.

Add a frozen typed-IR array proof that is attached after counted-loop proofs and independently cleared/recomputed at both validation and emission boundaries. For each Task 17 key, both boundaries must directly hash the retained raw source, directly hash the retained normalized source, and require the retained canonical define tuple to be exactly empty. A caller-supplied hash may remain an additional generator gate but is not authority for either typed boundary. A supplied proof, source spelling, regex, span, stable-looking symbol number, or externally supplied digest is never sufficient authority.

The source-specific profile must prove:

1. The only admitted arrays are function-local, size-nine, uninitialized declarations of `float[9]` or `vec2[9]`: Sharpen `kernel`, `offsets`; Sobel `sobel_x`, `sobel_y`, `offsets`.
2. No array parameter, return, global, qualifier, aggregate initializer, copy, alias, escape, or call argument exists.
3. Each admitted array receives exactly one direct write to every literal signed-int index 0 through 8, with no duplicates, omissions, out-of-range index, dynamic index, or intervening branch/loop/return/break/continue.
4. All initialization writes occur before the sole reading loop; there is no read before completion and no write after completion.
5. The sole reads are exactly the source-specific array/role set and use the existing counted-loop induction symbol directly: `i=0; i<9; i++`, nine trips, depth one, interval 0 through 8.
6. The loop body/control hierarchy, read expressions, symbol identities, and operators match the exact Sharpen or Sobel source profile. A forged typed tree that retains authentic source bytes, hashes, spans, and proof fields but changes array declarations, stores, reads, index expressions, ordering, or control must be rejected by both boundaries.
7. Scalar table values are never introduced as a new F32 storage boundary. Vector table values retain the canonical F32 lane boundary.
8. Parsing the canonical raw source with an irrelevant extra define such as `{"UNRELATED": 1}` must remain distinguishable even when its normalized source is byte-identical. A define affecting preprocessing, such as `{"GL_ES": 1}`, and a forged raw-source/define provenance record must also reject at both boundaries.

## Exact native lowering

Lower only proved declarations and index operations:

```cpp
std::array<double, 9> kernel{};
std::array<double, 9> sobel_x{};
std::array<double, 9> sobel_y{};
std::array<glsl::Vec2, 9> offsets{};
```

Use direct `operator[]` only for proved literal stores and proved induction reads. Do not use `.at()`, introduce a throwing path, or catch bounds failures inside `noexcept` pixel code. Value initialization is mandatory to match canonical zero-fill even though complete initialization is separately proved.

The raw table payload is 144 bytes for Sharpen and 216 bytes for Sobel. Measure compiler stack usage or actual frame size in both Debug and Release; report the tool/flags and distinguish raw table payload from full frame size. No heap allocation, per-pixel string/map/variant work, callback, virtual dispatch, resource ABI change, or runtime JS/Python/Qt dependency is permitted.

## Explicit exclusions

- `filter/celShading:celShadingEdges` and `filter/outline:outlineSobel`: dynamic nested-loop `samples[idx]` stores and body counter increment.
- `classicNoisedeck/refract:refract`: array parameter ABI/alias contract.
- `synth/sacredGeometry:sacredGeometry`: `vec2[13]`, affine initialization, nested reads.
- Every other type, extent, aggregate initializer, index expression, array value, function boundary, or program key.

## Frozen external oracle

- Risk audit SHA-256: `17692e3784ad64a4a283f7509b8cabe65521cabe282d5a78d6e6ade17be24937`.
- Oracle generator SHA-256: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`.
- Oracle JSON SHA-256: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`.
- Oracle report SHA-256: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`.

The oracle generator must continue to pass `--check` without writes. It binds the pinned canonical CPU factory directly and double-renders fresh surfaces.

The four frozen cases are:

- Sharpen default: F32 `54bffb81920b79c85198238c2fcd4f52b94ae25ca208747fb0048f24a71b05ec`, RGBA8 `d1bd7b35b2890258c385d294879556b4586d33f4af29feeeb7be5a4931ec2094`.
- Sharpen amount F32 2.3: F32 `53f12c6e6047f31edb9e157202674a405489df96dd995adcc3bf4aea5a20128f`, RGBA8 `560e7225289764f8d2c108b3f0746859ceb38ce4dee47753710d6d18473101e3`.
- Sobel default alpha one: F32 `df429cbfeb9dc04d3e5f9099ded0daae9ee7077a9121e325a11fb0cd9ac380dd`, RGBA8 `6841efab285a153de30bebaad4a6550107a1de719c37337a159ef07667d76777`.
- Sobel amount F32 2.3, alpha zero: F32 `f7e50759990c46d868b22bdf83241e3866b14a6406fee043b8cad46cbea6b1d8`, RGBA8 `05f02465cc5eacd61320b5d1b304f4b8face9993f604f540466d9582075bb3e0`.

The non-default amount must be bound as exact F32 `2.299999952316284` (`0x40133333`), not a JS double `2.3`. Sobel alpha-one F32 values can exceed one; F32 hashes and probes are authoritative because RGBA8 saturation hides that range.

## Required regression and acceptance evidence

- Parser/semantic provenance tests for exact retained raw source and canonical immutable type-tagged define tuples, including key-order stability and bool/int distinction.
- Validator and emitter negatives for wrong key/digest/defines, same-normalized `{"UNRELATED": 1}`, changed-normalized `{"GL_ES": 1}`, forged raw-source/define provenance, every excluded declaration/type/extent/storage/initializer, missing/duplicate/nonliteral/out-of-range write, read before completion, post-completion write, dynamic or altered index, wrong induction/bound/update, second/nested reading loop, control bypass, array call/copy/return/escape, stale/forged proof, and exact source-profile tampering with source bytes retained.
- Emitter assertions for exact zero-initialized `std::array<double, 9>` and `std::array<glsl::Vec2, 9>`, direct proved indexing, no `.at()`, no allocation, and preserved `noexcept`.
- Exact required binding tests and continued rejection of all four adjacent array profiles.
- All four frozen F32/RGBA8 oracle cases, probe bits, orientation, and repeatability in native tests.
- Full Python suite; every corpus/semantic/generator drift gate; Task 15, Task 16, and Task 17 frozen-oracle `--check` gates.
- Fresh strict Debug and Release builds with `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`; direct native suite and CTest in both.
- Exact catalog counts 110 typed / 112 public / 100 publicly unported.
- Debug and Release stack evidence plus static inspection of generated hot loops.

No Git command, branch, worktree, commit, push, or pull request is authorized.
