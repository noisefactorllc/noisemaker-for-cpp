# Post-median-profile frontier audit: Task 63 Dither frozen Bayer-4 input profile

This is a read-only long-range projection relative to prepared Tasks 12–62.  The active Task-15 correction is separate and is not merged into its counts, contracts, or completion claims.  The derivative ABI hold remains preserved.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 62 | 185 | 187 | 25 |

## Recommendation: `dither-bayer4-input-frozen-profile-v1`

Admit exactly one frozen factory profile for `filter/dither:dither`: its metadata defaults, with `ditherType=1` (Bayer 4×4) and `palette=0` (input).  This is profile specialization before typed emission, not a general dither source, global-matrix, palette-table, error-diffusion, or mutable-state admission.

| field | exact value |
| --- | --- |
| key | `filter/dither:dither` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl` |
| source SHA-256 | `a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb` |
| frozen metadata profile | `{ "levels": 4, "matrixScale": 2, "mix": 1, "palette": 0, "threshold": 0, "type": 1 }` |
| define map | `{}` |

The profile specializer binds those six user parameters as constants before typed emission.  It then proves the `ditherType == DITHER_ERROR_DIFFUSION` arm false, selects `getDitherThreshold`'s `DITHER_BAYER_4X4` arm, selects `palette == PALETTE_INPUT`, and folds the terminal `mix(..., 1.0)` to the dithered RGB result.  All palette tables, bayer2/bayer8/noise/pattern code, PCG, and Floyd–Steinberg state are unreachable and must be removed before capability checking/emission rather than indirectly admitted.

The surviving data feature is exactly the immutable source `bayer4x4` `mat4` literal accessed as `bayer4x4[y & 3][x & 3]`.  Lower it to a source-specific immutable 16-float column-major table, retaining GLSL's first-index column rule and the exact `4*y+x` logical lookup.  `x` and `y` are the existing integer floor coordinates from `globalCoord / (2 * renderScale)`; their low-two-bit masks use the already-projected signed-word semantics, but no other signed bitwise form is admitted here.

## Exact admission contract

1. Accept only the pinned key, digest, empty define map, and six frozen user values above.  The factory must reject attempts to bind a different value, rather than silently compiling a wider profile.  Standard host bindings (`inputTex`, `tileOffset`, `fullResolution`, positive `renderScale`, and time) retain their existing contracts; time is unreachable in this profile.
2. Run a deterministic profile-specialization pass before typed capability validation.  The retained reachable graph is only ordinary sampling; global-coordinate scaling/floor conversion; the Bayer-4 lookup; input-level quantization at four levels; and output alpha preservation.  A surviving reference to `ditherType`, `palette`, a palette helper/table, error diffusion, PCG, mutable `errRow`, another Bayer/pattern arm, or a nonconstant `mixAmount` is a rejection.
3. Permit only one immutable source-qualified 4×4 matrix literal, lowered as a non-addressable `std::array<float,16>` in GLSL column-major order.  Permit only the exact two-stage index `y & 3`, then `x & 3`, with each result `0..3`, and lower its value as the pinned table offset.  Reject matrix arithmetic, other matrix types/constructors, matrix parameters/returns/arrays, generic matrix indexing, mutable/global state, or an array escape.
4. Preserve Float32 materialization for the table literals, `floor`, integer conversion, four-level quantization `floor(dithered*4)/3`, and the source's neutral threshold.  Preserve the sampler coordinate mapping and source alpha exactly.  Do not add scalar/vector round, unsigned conversion/PCG, palettes, texture LOD/gradient/image operations, derivatives, resource/stage ABI behavior, or a general preprocessor/runtime specialization mechanism.

## Required tests and oracles

- Acceptance tests lock the source/key/empty defines/frozen parameter values and reject every attempted profile change, including `type=0/2/7`, non-input palette, non-four levels, or non-unit mix.
- Specialization tests show no residual AST/IR node for the excluded error-diffusion/palette/pattern/PCG branches or their tables, and exactly one 16-float Bayer table with source column order.
- Structural tests prove the signed low-mask intervals `0..3`, exact two-stage table access, no matrix object/arithmetic beyond that lowering, and no mutable/global table state.
- Runtime tests compare an independent 4×4 Bayer reference on non-square surfaces, negative and positive tile offsets, pattern-cell boundaries, asymmetric color and alpha data, multiple valid render scales, and repeated renders.  Verify four-level quantization, output alpha preservation, column-major lookup order, and tile-continuous global alignment.
- Negative tests reject any nonfrozen parameter, an extra reachable source branch, a changed table literal/order, a non-mask index, a matrix operation/escape, palette/error-row state, PCG/word route, derivative syntax, LOD/gradient/image syntax, and every other source key.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 63 | 186 | 188 | 24 |

The residual is deliberately still broader than this profile: fragment derivatives remain held; unfrozen dither/error-diffusion and other mutable aggregate work; wider packed-word contracts; matrices/copy-out; and resource/stage ABI features.  This frozen Bayer profile implies none of those capabilities.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count active Task 15, and does not claim an implementation is merged.  The derivative ABI hold is preserved.
