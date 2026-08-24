# Post-resource-bound-loop frontier audit: Task 47 single-pixel reindex reduction

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-46.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 46 | 169 | 171 | 41 |

## Recommendation: `reindex-reduce-single-pixel-budget-v1`

The next smallest exact slice is reindex's terminal statistics reduction. It
adds one key-specific large-work preflight for a verified 1×1 output, not a
general dynamic-loop or texture-resource facility.

| Key | Exact defines | Source SHA-256 | Resource/work contract |
| --- | --- | --- | --- |
| `filter/reindex:nmReindexReduce` | `{}` | `5e9701125522aaa1f838858a7892ac1312f1161608a5f94b494ae64c7db8b7ff` | `statsTex` axes `1..4096`; destination exactly `1x1`; at most `512×512` fetches |

Preflight must require a real `statsTex` surface with positive axes no greater
than 4,096 and a one-by-one destination. With the exact literal
`TILE_SIZE=8`, the source computes `tileCount = ceil(statsTexSize / 8)` by
integer arithmetic. The proven ranges are therefore `tileCount.x/y=1..512`;
the outer and inner `0..<MAX_TILE_DIM` loops (`MAX_TILE_DIM=512`) exit at
those exact limits. The only scan pixel makes
`ceil(width/8) * ceil(height/8)`, at most 262,144, level-zero fetches. Failure
rejects execution; it must not clamp/rewrite dimensions, truncate the scan,
resize or synthesize a surface, or run an implicit pass graph.

The authored initial fragment guard returns a zero vector for any coordinate
other than `(0,0)`; the required `1x1` destination makes the reduction execute
once. The source constants are exact `F32_MAX`, unary-literal `F32_MIN`,
`TILE_SIZE=8`, and `MAX_TILE_DIM=512`, all read-only and lowered only as
automatic immutable locals. The source otherwise uses existing `textureSize`,
level-zero `texelFetch`, scalar `min`/`max`, constructors, assignments, and
structured control flow. It has no derivative, array, matrix, struct,
uniform block, varying, parameter direction, sampler array, `textureLod`, or
mutable global state.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/reindex:nmReindexReduce` with its metadata-verified
   empty define map and pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Add only this key's resource preflight. Preserve immutable input surface
   width/height/identity evidence and output dimensions. Require `statsTex`
   axes in `1..4096` and destination `1x1`; reject missing/non-surface input,
   zero/negative/over-cap dimensions, non-1x1 destination, arithmetic
   overflow, or absent proof. Do not mutate bindings or allocate/interpolate
   intermediates.
3. Permit only the exact source constant declarations and initializer forms:
   two floats (`F32_MAX`, unary `F32_MIN`) and two literal ints (`TILE_SIZE`,
   `MAX_TILE_DIM`). Retain stable symbol identities, literal values/unary
   operation, zero-write/read closures, and automatic-local emission. Reject
   another global type/value/initializer/dependency, array/matrix/struct
   global, static storage, mutable state, or general source-global expansion.
4. Permit the exact nested loop tree: prefix-increment `ty=0..<512`, guarded
   by `ty >= tileCount.y`, containing prefix-increment `tx=0..<512`, guarded
   by `tx >= tileCount.x`. Retain source spans, break locations, tile-count
   formula, row-major coordinate proof
   `ivec2(tx*TILE_SIZE, ty*TILE_SIZE)`, and total charge
   `tileCount.x*tileCount.y <= 262144` in typed IR. Reject a changed header,
   guard/order, nesting, bound, coordinate, dynamic allocation, recursion, or
   loop-return/continue form.
5. Permit exactly the one level-zero `texelFetch(statsTex, sampleCoord, 0)`
   in the inner loop, with `sampleCoord` in-range under the resource proof.
   Reuse existing bottom-left fetch and Float32 result semantics. Emit direct
   automatic locals and structured loops only—no heap, callback, virtual
   dispatch, map, variant, indirect call, pointer/reference escape, or graph
   adapter. This remains the explicit metadata `statsTiles -> global_stats`
   pass; callers orchestrate the surrounding reindex passes. `PixelFn` stays
   `noexcept` and allocation-free.

Required positives are frozen reindex-reduce oracles for 1×1, partial-tile
rectangles, 4,096-axis boundaries, min/max extrema placed in first/last tiles,
and exact 1×1 output. Direct tests must lock source constants, the initial
fragment guard, ceil-tile arithmetic, all loop/break charge cases, final tile
coordinate coverage, 262,144 maximum fetch charge, fetch orientation, and
byte-identical repeated output.

Required negatives reject key/define/hash drift; non-surface, zero, over-cap,
or wrong-output resources; clamp/resize/implicit-pass behavior; a changed
constant/initializer/loop guard/header/nesting/coordinate; charge overflow;
a second sampler/fetch or nonzero/computed LOD; derivative, array, matrix,
aggregate, uniform block, varying, non-`in` parameter, or macro expansion.
Compile generated C++ with warnings as errors and assert zero hot-path
allocations and indirect calls.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 47 | **170** | **172** | **40** |

## Ranked residual map after Task 47

This one large, once-per-pass reduction does not establish arbitrary large
pixel work, general texture-dimension loops, aggregates, or neighboring-pixel
evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | General resource/work policy | other dynamic scans and multi-pixel reductions | Need different dimension provenance, output cardinality, or budget rules. |
| 3 | Larger aggregate and word/index forms | OSD, dither, median, test pattern | Require larger arrays, general indexing/lifetime, sorting, or broader signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 47 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader work, resource, aggregate,
loop, matrix, stage, index, numeric, sampling, and macro boundary.
