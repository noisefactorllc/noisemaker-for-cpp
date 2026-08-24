# Post-local-array frontier audit: Task 56 Sobel fixed tables

This is a read-only long-range projection relative to prepared Tasks 12–55.  The active Task-15 correction is deliberately neither merged into this projection nor counted as complete.  Fragment derivatives remain held behind their separate ABI/design boundary.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 55 | 178 | 180 | 32 |

## Recommendation: `sobel-three-local-nine-tap-tables-v1`

Admit exactly one factory, `filter/sobel:sobel`, with no general expansion of arrays, indexing, convolution, or sampler behavior.

| field | exact value |
| --- | --- |
| key | `filter/sobel:sobel` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/sobel/sobel.glsl` |
| source SHA-256 | `ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` |
| metadata defaults | `{ "alpha": 1, "amount": 1 }` |
| define map | `{}` |

The source has exactly three automatic, function-local arrays: `float sobel_x[9]`, `float sobel_y[9]`, and `vec2 offsets[9]`.  Every element of every array is written at a literal index `0..8` before the sole indexed loop.  The loop `for (int i = 0; i < 9; i++)` reads each table only at `i`, makes one ordinary convolution texture sample per trip, and accumulates `convX` and `convY`.

This is narrower than the general fixed-local-array proposal: Task 56 admits only these names, element types, extents, initializer graphs, and the single proved induction use for this pinned source.  It builds on the existing projected nine-trip proof used by Task 55, but does not merge or depend on the active Task-15 correction.

## Exact admission contract

1. Accept only the key, pinned source digest, empty define map, and metadata defaults above.  Reject source drift, any define, or a changed/missing `alpha` or `amount` profile before translation.
2. Permit exactly three automatic entry-function arrays: `std::array<float, 9>` named `sobel_x`; `std::array<float, 9>` named `sobel_y`; and `std::array<Vec2, 9>` named `offsets`.  Their total footprint is 36 scalar-float lanes (144 bytes).  Reject global/static storage, heap allocation, arrays in parameters/returns, aliases, copies, aggregate assignment, extra arrays, or a different extent/type.
3. Prove definite assignment for all 27 table elements before the loop, with exactly one literal-index write at each index `0..8` and no computed write index.  The X sequence is `[1, 0, -1, 2, 0, -2, 1, 0, -1]`; the Y sequence is `[1, 2, 1, 0, 0, 0, -1, -2, -1]`; the offset table is the exact raster-ordered combinations of `-texelSize`, zero, and `+texelSize`.
4. Prove `i` starts at zero, has guard `i < 9`, increments by one, and therefore makes exactly nine trips with interval `0..8`.  Permit on each trip exactly one read from `offsets[i]`, `sobel_x[i]`, and `sobel_y[i]`; reject every other dynamic array read, write, or index expression.
5. Preserve current ordinary sampler and `gl_FragCoord` lowering: one original-color sample and nine convolution samples, with the offset factor `amount * renderScale`.  Preserve `distance(convX, convY)`, RGB multiplication by that scalar, and `mix(origColor.rgb, result, alpha)` while output alpha remains `origColor.a`.  No sampler array, texture LOD/gradient operation, image operation, new resource ABI, derivative, or texture-profile feature is admitted.

## Required tests and oracles

- Acceptance tests must lock the key/digest/defaults/empty define map; reject every profile or identity mismatch.
- Structural tests must prove exactly three automatic arrays of extent nine, 27 literal writes, full definite initialization, and one exact nine-trip `i` loop with only the three allowed indexed reads.
- Runtime tests must compare a reference Sobel implementation with generated output on a non-square input, a one-pixel input, edge and corner impulses, flat color, asymmetric RGB content, `amount` values `0`, `1`, and an in-range non-unit value, plus `alpha` values `0`, `1`, and an interior value.  They must verify output alpha is the original sample alpha, not the blend control.
- Negative tests must reject partial or duplicate initialization, a nonliteral/affine write index, a second index loop, a changed loop bound/step, an array escape, a sampler array, texture LOD/gradient syntax, derivative syntax, and every source key other than the allowlisted one.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 56 | 179 | 181 | 31 |

The remaining work stays ranked by independent proof burden: derivative-dependent sources remain held; then local-array cases with distinct indexing/control or parameter/escape shapes; then larger aggregate, sorting, packed-word, matrix/copy-out, and resource-ABI cases.  This one-key Sobel admission implies none of those capabilities.

## Boundary statement

This is planning evidence only.  It makes no repository change, does not alter or count the active Task-15 correction, and does not claim an implementation is merged.  The derivative ABI hold remains preserved.
