# Post-palette-table frontier audit: Task 55 sharpen local arrays

This is a read-only long-range projection relative to the prepared Tasks 12–54.  It deliberately does **not** merge, count, or otherwise treat the active Task-15 correction as completed.  The derivative ABI hold remains in force.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 54 | 177 | 179 | 33 |

## Recommendation: `sharpen-fixed-nine-tap-local-arrays-v1`

Admit exactly one factory, `filter/sharpen:sharpen`, and no broader local-array, dynamic-index, convolution, or texture-profile capability.

| field | exact value |
| --- | --- |
| key | `filter/sharpen:sharpen` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/sharpen/sharpen.glsl` |
| source SHA-256 | `c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` |
| metadata defaults | `{ "amount": 1 }` |
| define map | `{}` |

This shader has two automatic function-local arrays: `float kernel[9]` and `vec2 offsets[9]`.  Each receives a literal write at every index from `0` through `8`; the sole indexed reads occur in `for (int i = 0; i < 9; i++)`.  The loop reads `offsets[i]` and `kernel[i]` once per trip while accumulating the nine-tap convolution.  The pre-loop source sample supplies the output alpha; the loop performs nine ordinary texture samples.

The proof is deliberately narrower than a generic array feature.  It reuses only the already-projected fixed literal nine-trip loop shape and admits these two named arrays for this one source identity.  It does not rely on the active Task-15 correction and does not expand its counts or contracts.

## Exact admission contract

1. Accept only the key, source digest, empty define map, and metadata profile above.  A source, metadata, or define mismatch rejects before translation.
2. Permit exactly two automatic function-local fixed arrays in the entry function: `std::array<float, 9>` for `kernel` and `std::array<Vec2, 9>` for `offsets`.  They remain stack-local (27 scalar-float lanes, 108 bytes total); no heap allocation, global/static storage, array parameter, return, copy-out, alias, or general array lowering is admitted.
3. Require definite assignment by literal index before the indexed loop: each array gets one write at each index `0..8`, with no duplicate or computed write index.  The kernel sequence is `[-1, 0, -1, 0, 5, 0, -1, 0, -1]`.  The offsets are the nine exact combinations of `-texelSize`, zero, and `+texelSize` in raster order.
4. Prove the sole loop induction variable starts at zero, has guard `i < 9`, increments by one, and therefore ranges only over `0..8` for exactly nine trips.  Allow only one `kernel[i]` and one `offsets[i]` read in that loop; no other dynamic array index or indexed mutation is accepted.
5. Preserve the existing ordinary sampler and `gl_FragCoord` lowering.  The translated body must retain one original-color sample for alpha plus the nine convolution samples, the `amount * renderScale` offset factor, and `clamp(conv, 0, 1)` RGB output.  No sampler array, LOD/gradient query, image operation, derivative, texture profile change, or new resource ABI is admitted.

## Required tests and oracles

- Accept this exact source/profile and reject a changed digest, non-empty define map, or parameter-default mismatch.
- Compile-time structural oracle: exactly two automatic arrays, both extent nine; 18 literal indexed writes; and one proved nine-trip loop with only the two permitted indexed reads.
- Runtime oracle: compare reference and generated output for a non-square image, a one-pixel image, edge/corner impulse patterns, a flat field, `amount` values `0` and `1`, and representative non-unit `renderScale` values.  Require alpha to equal the pre-loop original sample and RGB to match the clamped nine-tap reference.
- Negative corpus: reject a computed array write index, an array extent other than nine, partial initialization, a second indexed loop, a dynamic index outside the proved induction variable, an array escape, a sampler array, a texture LOD/gradient call, derivative syntax, or any additional source key.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 55 | 178 | 180 | 32 |

The next frontier remains intentionally ranked by narrow proof burden: derivative-dependent shaders stay held; then more complicated array/index forms (including variable-length, multidimensional, or packed-index variants); then matrix/copy-out or resource-ABI cases; then broader texture-profile work.  None of those capabilities is implied by this one-key admission.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter Task 15, and does not claim an implementation has been merged.  The derivative ABI hold is preserved.
