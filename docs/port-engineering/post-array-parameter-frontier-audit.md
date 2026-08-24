# Post-array-parameter frontier audit: Task 60 Sacred Geometry affine centers

This is a read-only long-range projection relative to prepared Tasks 12–59.  The active Task-15 correction is expressly separate and is not merged into counts, contracts, or completion claims.  The derivative ABI hold remains preserved.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 59 | 182 | 184 | 28 |

## Recommendation: `sacred-geometry-affine-centers13-v1`

Admit exactly one factory, `synth/sacredGeometry:sacredGeometry`, under a source-specific affine local-array proof.  This is not general arithmetic indexing, arbitrary local arrays, or a new loop capability.

| field | exact value |
| --- | --- |
| key | `synth/sacredGeometry:sacredGeometry` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/sacredGeometry/sacredGeometry.glsl` |
| source SHA-256 | `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de` |
| source-bound metadata defaults | `{ "animation": 0, "bgColor": [0,0,0], "fgColor": [1,1,1], "geometry": 0, "pulseDepth": 0.15, "rings": 3, "rotation": 0, "scale": 10, "smoothness": 0.02, "speed": 1, "starPoints": 5, "thickness": 0.2 }` |
| define map | `{}` |

`fruitMask` contains the sole array: automatic `vec2 centers[13]` (26 scalar-float lanes, 104 bytes).  It writes `centers[0]` literally, then in two separate exact `k=0..<6` loops writes `centers[1 + k]` and `centers[7 + k]`.  The assignments cover every index `0..12` once.  Later exact `i=0..<13` loops read `centers[i]`; the nested line loop reads `centers[i]` and `centers[j]` under its existing `i,j=0..<13` bounded-loop proof.

This adds only the three pinned index forms for this one source: literal `0`, `1+k`, and `7+k` during initialization, plus direct `i`/`j` reads.  It uses the already-projected bounded-loop/control vocabulary, without merging or relying on the active Task-15 correction.

## Exact admission contract

1. Accept only the key, source digest, empty define map, and source-bound metadata profile above.  Reject source or binding-profile drift before translation.
2. Permit exactly one automatic function-local `std::array<Vec2, 13>` named `centers` in `fruitMask`.  Reject global/static/heap storage, parameter/return/escape/copy behavior, aliases, arrays of another type/extent, additional arrays, and constructors or aggregate assignment.
3. Prove the complete initializer graph exactly: one `centers[0]` write; then one six-trip `k=0..<6` loop whose only indexed write is `centers[1+k]`; then a distinct six-trip `k=0..<6` loop whose only indexed write is `centers[7+k]`.  The three index intervals must be `{0}`, `1..6`, and `7..12`, disjoint and exhaustive.  Reject a changed offset, bound, step, write count, or expression-shaped index.
4. Require definite initialization before every read.  Permit only `centers[i]` in the later exact `i=0..<13` circle loop and only `centers[i]`/`centers[j]` in the existing exact `i,j=0..<13` line loop.  No dynamic write after initialization, no other index variable, no affine read, and no reference/array escape is admitted.
5. Reuse—not broaden—the projected fixed counted-loop/control model for the source's literal loops, `continue`, and `break`; retain its individual and aggregate charge limits.  Preserve existing scalar/vector math, source constants, and normal generator bindings.  Do not add derivatives, sampler/texture profiles, matrices, packed words, image operations, or any resource/stage ABI feature.

## Required tests and oracles

- Acceptance tests lock the key, digest, source-bound defaults, and empty define map; reject every mismatch.
- Structural tests prove one 13-element Vec2 stack array; initializer index sets `{0}`, `1..6`, and `7..12`; exactly 13 writes; no overlap or gap; all later reads at proven `0..12`; and no array copy/escape.
- Runtime tests compare a direct reference for `geometry` fruit and metatron (exercising circles and connecting lines), plus flower, seed, vesica, borromean, triquetra, and star polygon paths.  Include non-square surfaces; both animation-off and ripple/unfold paths; representative rings, star-points, rotations, colors, and thickness/smoothness values; and repeatability.  Check opaque output alpha and the expected 13-circle/78-line behavior in the metatron case.
- Negative tests reject an extent other than 13, a non-Vec2 element, partial/duplicate initialization, `2+k` or a runtime offset, a changed six-trip bound, an affine read, an array parameter/return/alias, an unproved loop/index, derivative syntax, texture/image operations, and every source key other than the allowlisted one.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 60 | 183 | 185 | 27 |

The residual now excludes the prepared fixed local-array family.  It remains deliberately partitioned: derivative-dependent sources stay held; other larger aggregate/sorting and packed-word forms; then matrix/copy-out and resource/stage ABI work.  This one affine-table exception establishes none of those broader features.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count active Task 15, and does not claim an implementation is merged.  The derivative ABI hold is preserved.
