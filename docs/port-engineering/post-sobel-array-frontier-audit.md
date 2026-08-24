# Post-Sobel-array frontier audit: Task 57 Cel Shading indexed samples

This is a read-only long-range projection relative to prepared Tasks 12–56.  The active Task-15 correction is explicitly separate: it is not merged into these counts, contracts, or completion claims.  The derivative ABI hold remains unchanged.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 56 | 179 | 181 | 31 |

## Recommendation: `cel-shading-fixed-grid-index-counter-v1`

Admit exactly one factory, `filter/celShading:celShadingEdges`.  This is not a general admission of post-increment, nested-loop indexing, arrays, or coordinate wrapping.

| field | exact value |
| --- | --- |
| key | `filter/celShading:celShadingEdges` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/celShading/celShadingEdges.glsl` |
| source SHA-256 | `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` |
| source-bound metadata defaults | `{ "edgeThreshold": 0.15, "edgeWidth": 1 }` |
| define map | `{}` |

The source declares exactly one automatic function-local array, `float samples[9]`, and one local counter, `int idx = 0`.  Its nested loops traverse `ky=-1..1` and, for each `ky`, `kx=-1..1`, for nine inner trips in raster order.  Each trip writes `samples[idx]` once and then performs the exact statement `idx++`.  The later Sobel formulas read only the literal elements `samples[0]`, `samples[1]`, `samples[2]`, `samples[3]`, `samples[5]`, `samples[6]`, `samples[7]`, and `samples[8]`.

This differs from Task 56's direct `i=0..<9` reads, so its proof is separately pinned: the only dynamic index is a single pre-increment-use counter whose interval is derived from the two exact bounded loops.  It can reuse the long-range fixed-loop model as planning evidence without merging or relying on the still-active Task-15 correction.

## Exact admission contract

1. Accept only the pinned key, source digest, empty define map, and source-bound defaults shown above.  Reject source/metadata drift and any define before translation.  The metadata `edgeWidth` integer default is materialized at its declared binding boundary before use by the source's float uniform.
2. Permit exactly one entry-function automatic array, `std::array<float, 9>` named `samples`, and exactly one fresh local `std::int32_t idx` initialized to zero.  Reject global/static storage, heap allocation, array parameter/return/escape/copy, aliases, extra arrays, or any other counter-based indexed access.
3. Prove the lexical control shape exactly: outer `ky` starts at `-1`, tests `ky <= 1`, and increments by one; inner `kx` starts at `-1`, tests `kx <= 1`, and increments by one.  The inner body has exactly nine aggregate visits in raster order.  Reject changed bounds, step, nesting, `break`, `continue`, a conditionally skipped write, or any competing write to `idx`.
4. At each inner visit, prove `idx` is respectively `0..8` before `samples[idx]` writes the luminosity of the wrapped `texelFetch`; the following standalone `idx++` advances it to `1..9`.  Require every array element be definitely written once before any later read.  No dynamic reads, dynamic writes other than this one store, or use of `idx` after the nine visits is admitted.
5. Preserve the established `textureSize`, bottom-left integer `texelFetch`, scalar `%` wrapping, `sqrt`, and `smoothstep` semantics already used in the projected vocabulary.  Retain the zero-dimension early return, the exact literal Sobel reads, `edgeThreshold * 0.5`/`1.5`, and opaque output `vec4(edge, edge, edge, 1.0)`.  Do not add sampler arrays, texture LOD/gradient operations, image operations, resource ABI changes, derivatives, or a texture-profile capability.

## Required tests and oracles

- Acceptance tests lock the key/source/defaults/empty define map and reject each identity/profile mismatch.
- Structural tests prove one nine-float stack array, one zero-initialized `idx`, both exact three-trip loop axes, exactly nine dynamically indexed writes in order `0..8`, a final `idx` interval of exactly `9`, and full definite initialization before the literal Sobel reads.
- Runtime tests compare a direct reference on non-square and one-pixel textures; wrap-sensitive corner/edge impulses; asymmetric RGB data; several `edgeWidth` values across its metadata range; and threshold values below, inside, and above representative magnitudes.  They must check bottom-left `texelFetch` orientation, exact opaque alpha, zero-sized texture early output, and repeatability.
- Negative tests reject `idx += n`, prefix/postfix use in an expression, a counter that escapes the loop body, an affine or uniform index, duplicate/partial stores, a fourth loop trip, a changed loop direction, a dynamic read, an array escape, derivative syntax, LOD/gradient sampling, and every source key other than the allowlisted one.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 57 | 180 | 182 | 30 |

The residual stays deliberately partitioned: derivative-dependent shaders remain held; then distinct array shapes (including parameter/escape forms and larger/affine tables); then sorting, packed-word, matrix/copy-out, and resource/stage ABI work.  This one-key fixed-grid proof establishes none of those broader capabilities.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count the active Task-15 correction, and does not claim implementation or merge completion.  The derivative ABI hold is preserved.
