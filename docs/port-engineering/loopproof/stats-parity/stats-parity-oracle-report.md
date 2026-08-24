# Normalize statsFinal pixel/resource oracle

Frozen JavaScript ground truth for `filter/normalize:statsFinal`, rendered through the canonical noisemaker-for-cpu factory into the only authorized destination extent, `1x1`. Float32 hashes and RGBA8 hashes are exact byte contracts. The custom comparer adds first-pixel/channel diagnostics without weakening those contracts.

## Closed runtime contract

- `inputTex` width and height are safe integers in `1..64`.
- The two axis bounds mathematically imply an input product and maximum level-zero integer fetch count of at most 4,096; the oracle does not claim a separately reachable product guard.
- Destination extent is exactly `1x1`. This oracle freezes that acceptance requirement, but does not execute the future C++ allocation seam; native tests must prove rejection occurs before result-Surface construction.
- At `64x64`, lexical loop product and fetches are 4,096 while the repository proof metric is separately `entrypoint_charge = 64 * (1 + 64) = 4,160`.

## Positive parity cases

| Case | Input | Product/fetches | Proof charge | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| single-texel-adversarial-unused-lanes | 1x1 | 1 | 2 | `c5388b9fc592e7411c6d80da7035a80e6082599ee271d1a7a55d7d568dc44e69` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| one-by-sixty-four-y-boundary | 1x64 | 64 | 128 | `f175c2aed0170d8817d291bbad3ecaceb15ba9962db1e4ec5b07cf0d87aa43b6` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| sixty-four-by-one-x-boundary | 64x1 | 64 | 65 | `f175c2aed0170d8817d291bbad3ecaceb15ba9962db1e4ec5b07cf0d87aa43b6` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| sixty-four-square-full-resource-boundary | 64x64 | 4096 | 4160 | `f175c2aed0170d8817d291bbad3ecaceb15ba9962db1e4ec5b07cf0d87aa43b6` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| sixty-three-by-sixty-four-near-product-boundary | 63x64 | 4032 | 4096 | `f175c2aed0170d8817d291bbad3ecaceb15ba9962db1e4ec5b07cf0d87aa43b6` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| thirty-seven-by-fifty-three-nonsquare | 37x53 | 1961 | 2014 | `f175c2aed0170d8817d291bbad3ecaceb15ba9962db1e4ec5b07cf0d87aa43b6` | `7a7bf454c5f3cb1b9d9a20f81417f98d976fe3b3dd52c1b9968f02e89e7e8a2f` |
| all-positive-r-all-negative-g-initializer-trap | 11x9 | 99 | 108 | `6dfbe5a1fc56b0949daadc52c2f5dc15894865f4ac8445e5f50a7ede2f1954ac` | `276fb09e87557828828162c889e2e0a308a0f769d13668478c24df9d5994542f` |

Every positive case passes exact repeat identity, public-catalog/direct-canonical equality, exact-bit input immutability, an independent bottom-left row-major reduction, and nearest/linear plus clamp/repeat/mirror state invariance. Filtering and wrapping are not sampling choices for this shader: its sole read is in-bounds `texelFetch(..., 0)`.

Adversarial coverage includes ignored-lane NaN/infinity, relevant-lane infinities that cannot win the finite extrema, negative/positive extrema, all-positive R with all-negative G, both degenerate axes, the full `64x64` boundary, a near-product boundary, and a representative non-square surface.

## Rejected resource shapes

| Case | Input | Output | Reason |
| --- | ---: | ---: | --- |
| zero-input-width | 0x1 | 1x1 | input width must be in [1,64] |
| zero-input-height | 1x0 | 1x1 | input height must be in [1,64] |
| input-width-65 | 65x1 | 1x1 | input width must be in [1,64] |
| input-height-65 | 1x65 | 1x1 | input height must be in [1,64] |
| huge-safe-input-axes-rejected-before-product | 4294967296x4294967296 | 1x1 | input width must be in [1,64] |
| output-two-by-one | 64x64 | 2x1 | output extent must be exactly 1x1 |
| output-one-by-two | 64x64 | 1x2 | output extent must be exactly 1x1 |
| output-zero-width | 64x64 | 0x1 | output extent must be exactly 1x1 |
| output-zero-height | 64x64 | 1x0 | output extent must be exactly 1x1 |
| input-width-negative-one | -1x1 | 1x1 | input width must be in [1,64] |
| input-height-negative-one | 1x-1 | 1x1 | input height must be in [1,64] |
| output-width-negative-one | 1x1 | -1x1 | output extent must be exactly 1x1 |
| output-height-negative-one | 1x1 | 1x-1 | output extent must be exactly 1x1 |
| input-width-fractional | 1.5x1 | 1x1 | input width must be a safe integer |
| input-height-fractional | 1x1.5 | 1x1 | input height must be a safe integer |
| output-width-fractional | 1x1 | 1.5x1 | output width must be a safe integer |
| output-height-fractional | 1x1 | 1x1.5 | output height must be a safe integer |
| input-width-nan | NaNx1 | 1x1 | input width must be a safe integer |
| input-height-nan | 1xNaN | 1x1 | input height must be a safe integer |
| output-width-nan | 1x1 | NaNx1 | output width must be a safe integer |
| output-height-nan | 1x1 | 1xNaN | output height must be a safe integer |
| input-width-positive-infinity | +Infinityx1 | 1x1 | input width must be a safe integer |
| input-height-positive-infinity | 1x+Infinity | 1x1 | input height must be a safe integer |
| output-width-positive-infinity | 1x1 | +Infinityx1 | output width must be a safe integer |
| output-height-positive-infinity | 1x1 | 1x+Infinity | output height must be a safe integer |
| input-width-negative-infinity | -Infinityx1 | 1x1 | input width must be a safe integer |
| input-height-negative-infinity | 1x-Infinity | 1x1 | input height must be a safe integer |
| output-width-negative-infinity | 1x1 | -Infinityx1 | output width must be a safe integer |
| output-height-negative-infinity | 1x1 | 1x-Infinity | output height must be a safe integer |
| input-width-unsafe-integer | 9007199254740992x1 | 1x1 | input width must be a safe integer |
| input-height-unsafe-integer | 1x9007199254740992 | 1x1 | input height must be a safe integer |
| output-width-unsafe-integer | 1x1 | 9007199254740992x1 | output width must be a safe integer |
| output-height-unsafe-integer | 1x1 | 1x9007199254740992 | output height must be a safe integer |

Invalid coverage includes -1, fractional, NaN, positive infinity, negative infinity, and an unsafe integer independently in all four input/output axis positions. The huge-safe-axis case is explicitly rejected by the per-axis cap before multiplication; no product-overflow coverage is claimed. No rejected case constructs a Surface or pixel fixture; rejected pixels are not part of the contract.

## Mutation discrimination

| Mutation | Class | Pixel-divergent cases | Actual fetch-trace-divergent cases | Discriminator |
| --- | --- | ---: | ---: | --- |
| drop-last-row | row_loop_off_by_one | 6/7 | 7/7 | exact Float32 pixel bits |
| drop-last-column | column_loop_off_by_one | 7/7 | 7/7 | exact Float32 pixel bits |
| y-bound-uses-width-lane | wrong_axis_seed | 2/7 | 5/7 | exact Float32 pixel bits |
| x-bound-uses-height-lane | wrong_axis_seed | 2/7 | 5/7 | exact Float32 pixel bits |
| skip-first-column | skipped_texel | 7/7 | 7/7 | exact Float32 pixel bits |
| extra-clamped-column | extra_texel_resource_charge | 0/7 | 7/7 | actual instrumented pre-clamp texelFetch trace (pixel reduction is intentionally idempotent) |
| swap-fetch-coordinate-axes | wrong_fetch_coordinate | 4/7 | 6/7 | exact Float32 pixel bits |
| zero-min-initializer | normalization_arithmetic_trap | 1/7 | 0/7 | exact Float32 pixel bits |
| zero-max-initializer | normalization_arithmetic_trap | 1/7 | 0/7 | exact Float32 pixel bits |
| min-consumes-green-lane | normalization_lane_trap | 7/7 | 0/7 | exact Float32 pixel bits |
| max-consumes-red-lane | normalization_lane_trap | 7/7 | 0/7 | exact Float32 pixel bits |

The trace evidence is observed from canonical and evaluated-mutant factories through a real `GlslCpuRuntime` whose sole wrapped stdlib operation records each actual pre-clamp coordinate, sampler identity, and LOD before delegating to the pinned implementation. It is not predicted from mutation ids.

The extra-column mutation is intentionally output-idempotent because an out-of-range integer fetch clamps to an edge texel already included in a min/max reduction. For every case, the actual trace contains exactly `height * (width + 1)` fetches, exactly one extra `[width,y]` coordinate per row, only `inputTex`, and only LOD 0. Its 64x64 resource count is 4,160 fetches and its proof charge would be 4,224; those are distinct from the canonical 4,096 fetches and 4,160 proof charge. Passing the unmutated canonical trace to the same assertion is required to fail in every case.

## Determinism and provenance

- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- Upstream snapshot revision: `c51037ad9e60850b74490c01a9eecf08c7d28e8c`
- GLSL source SHA-256: `0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa`
- Canonical factory SHA-256: `07eb7daea90fd057b232093fe2912b663ec6b780178d09ddf8212d15ea932172`
- Node reference engine used to freeze this file: `v24.7.0`
- All Float32 hashes are explicitly serialized little-endian lane by lane; RGBA8 hashes use their natural byte order.
- The generator pins the canonical/public/adapter/runtime files, factory body, source body, exact factory identity, and absence of an adapter override. `--check` verifies JSON, report, and all SHA-256 sidecars byte-for-byte.
