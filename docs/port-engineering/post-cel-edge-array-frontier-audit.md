# Post-Cel-edge-array frontier audit: Task 58 Outline Sobel indexed samples

This is a read-only long-range projection relative to prepared Tasks 12–57.  The active Task-15 correction remains separate and is not merged into this projection's counts, contracts, or completion state.  Fragment derivatives remain held behind their separate ABI boundary.

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| after Task 57 | 180 | 182 | 30 |

## Recommendation: `outline-sobel-fixed-grid-index-counter-v1`

Admit exactly one factory, `filter/outline:outlineSobel`.  It is not a generic expansion of arrays, post-increment, nested-loop indexing, multi-pass ownership, or metric dispatch.

| field | exact value |
| --- | --- |
| key | `filter/outline:outlineSobel` |
| source | `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/outline/outlineSobel.glsl` |
| source SHA-256 | `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` |
| source-bound metadata defaults | `{ "shape": 1, "thickness": 1 }` |
| define map | `{}` |

The source has exactly one automatic function-local `float samples[9]` and one `int idx = 0`.  Its outer `ky=-1..1` and inner `kx=-1..1` loops make nine raster-ordered inner visits.  Each visit writes `samples[idx]` from a wrapped bottom-left `texelFetch` and then executes `idx++`; the later Sobel expressions read only literal entries.  This is the same proof class as Task 57 but remains separately pinned to this source identity and initializer/use graph.

`distanceMetric` receives the local `int(sobelMetric)` and selects the existing Euclidean/default, Manhattan, Chebyshev, or Octagram scalar expression.  The Task 58 array admission does not generalize function dispatch or multi-pass behavior: its input is the already-bound `outlineValueMap` pass texture, and only this program key is admitted.

## Exact admission contract

1. Accept only the pinned key, source digest, empty define map, and source-bound defaults above.  Reject any identity/profile drift before translation.  Preserve metadata-to-uniform binding for `shape -> sobelMetric` and `thickness -> thickness`.
2. Permit exactly one entry-function automatic `std::array<float, 9>` named `samples` and one fresh `std::int32_t idx` initialized to zero.  Reject global/static or heap storage, array parameter/return/escape/copy, aliases, extra arrays, and all other dynamically indexed aggregates.
3. Prove the exact two-level loop form: `ky` starts at `-1`, guards `<= 1`, increments by one; `kx` starts at `-1`, guards `<= 1`, increments by one.  There must be exactly nine inner visits, no `break`/`continue`, no conditional bypass of the store, and no competing write to `idx`.
4. On each inner visit, prove `idx` is one of `0..8` before the sole `samples[idx]` write, then the standalone `idx++` produces `1..9`.  Require each element to be definitely assigned exactly once before later literal Sobel reads; reject dynamic reads, every computed/affine index, counter escape, or use after the loop.
5. Preserve current `textureSize`, zero-dimension early return, scalar integer `%` wrapping, bottom-left `texelFetch`, scalar conversion, `abs`, `sqrt`, `max`, and `clamp` lowering.  Retain all four exact `distanceMetric` result branches and the opaque `vec4(normalized, normalized, normalized, 1.0)` output.  Do not add sampler arrays, LOD/gradient/image operations, derivative behavior, resource ABI changes, or a multi-pass scheduler feature.

## Required tests and oracles

- Acceptance tests lock the source identity/defaults/empty defines and reject mismatch at the factory boundary.
- Structural tests prove one nine-float automatic array; `idx=0`; two exact three-trip axes; nine ordered dynamic writes covering `0..8`; final `idx=9`; full definite assignment; and later literal-only Sobel reads.
- Runtime tests compare an independent reference over non-square and one-pixel textures, corner/edge wrap probes, asymmetric scalar value-map data, thickness values at and within the configured range, and all shape codes `1`, `2`, `3`, and `4`.  Verify each distance metric branch, bottom-left fetch orientation, zero-dimension output, opaque alpha, and repeated-render determinism.
- Negative tests reject a different array extent/type/name, a partial or duplicate store, any altered loop bound/step/direction, `idx += n`, a counter expression use/escape, a dynamic read, an array escape, sampler-array or LOD/gradient syntax, derivative syntax, a new pass resource, and every source key other than the allowlisted pass.

## Residual frontier after this slice

| projection point | typed factories | public factories | unported long-range keys |
| --- | ---: | ---: | ---: |
| relative after Task 58 | 181 | 183 | 29 |

The residual remains consciously split: derivative-dependent programs stay held; then different local-array forms (parameter/escape, affine tables, and larger structures); then sorting, packed-word, matrix/copy-out, and resource/stage ABI work.  This one intermediate-pass admission implies none of those wider features.

## Boundary statement

This audit is planning evidence only.  It makes no repository change, does not alter or count active Task 15, and does not claim an implementation is merged.  The derivative ABI hold is preserved.
