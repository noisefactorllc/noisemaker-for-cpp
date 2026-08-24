# Post-radius-preflight frontier audit: Task 46 bounded reduce-texture scan

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-45.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 45 | 168 | 170 | 42 |

## Recommendation: `normalize-stats-final-resource-bound-v1`

The next smallest exact slice is the one-pixel terminal scan of normalize's
reduction chain. It introduces a key-specific input/output resource preflight,
not a general texture-dimension loop feature.

| Key | Exact defines | Source SHA-256 | Resource contract |
| --- | --- | --- | --- |
| `filter/normalize:statsFinal` | `{}` | `0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa` | `inputTex` width/height in `1..64`; destination exactly `1x1` |

Before binding this factory, preflight must inspect the actual `inputTex`
surface and destination. It accepts only positive input dimensions no greater
than 64 in either axis and a destination whose dimensions are exactly one by
one. Thus `inSize = textureSize(inputTex, 0)` gives exact nested loops
`y=0..<inSize.y` and `x=0..<inSize.x`, with `1..4096` level-zero integer
fetches in the only destination-pixel invocation. A failure rejects the pass;
it must not clamp dimensions, truncate the scan, resize surfaces, substitute a
value, or invoke an implicit render graph.

The source has no globals, helper functions, arrays, matrices, structs,
varyings, uniform blocks, parameter directions, derivatives, sampler arrays,
`textureLod`, or dynamic allocation. Its only operations are existing
`textureSize(sampler2D,0)`, `texelFetch(sampler2D,ivec2,0)`, scalar `min` and
`max`, constructors, assignments, and ordinary local loop/control flow.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/normalize:statsFinal` with its metadata-verified empty
   define map and pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Add only this key's resource preflight. Retain immutable evidence for input
   surface width, height, format/identity handle, output width/height, and the
   accepted bounds `1..64` / `1x1`. Reject missing/non-surface input, zero or
   negative dimensions, an axis over 64, non-1x1 destination, overflow, or
   proof absence. Do not mutate a binding or allocate/interpolate an
   intermediate surface.
3. Permit only the exact pair of nested loops whose fresh `int` induction
   values range from zero to the two checked `textureSize` lanes. Retain
   source spans, `inSize` symbol identity, inner/outer relationship, exact
   strict bounds and increments, and product charge `width*height <= 4096` in
   typed IR. Reject a loop outside this tree, altered header/control, swapped
   resource/bound provenance, loop return/break/continue, dynamic allocation,
   recursion, or a total charge above 4,096.
4. Permit exactly one level-zero `texelFetch(inputTex, ivec2(x,y), 0)` in the
   inner loop, with the coordinate range proved by the preflight dimensions.
   Reuse existing bottom-left integer-fetch semantics and Float32 result
   materialization. Reject another sampler/class, nonliteral/nonzero LOD,
   changed coordinate construction, texture sampling substitution, or a
   resource operation selected by loop data.
5. Emit only automatic scalar locals and a direct structured loop; no heap,
   static/global mutable state, pointer/reference escape, callback, virtual
   dispatch, map, variant, indirect call, or adapter. This factory is the
   metadata terminal pass (`reduce2 -> stats`) only; callers still orchestrate
   normalize's explicit `reduce`, `reduceMinmax`, `statsFinal`, and `apply`
   passes. `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen terminal-stats oracles for 1x1, rectangular,
and 64x64 input surfaces; mixed min/max placements; alpha/other unused lanes;
negative and positive extrema; and exact 1x1 output. Direct tests must lock
input/destination preflight acceptance, the `width*height` charge, complete
row-major coordinate coverage, bottom-left fetch orientation, scalar min/max
accumulators, and byte-identical repeated output.

Required negatives reject any key/define/hash drift, non-surface or
wrong-sized input/destination, every cap violation, attempted clamp/resize or
implicit pass execution, changed loop nesting/header/charge, a second fetch
or sampler, nonzero/computed LOD, derivative, array, matrix, aggregate,
uniform block, varying, parameter direction, sampler array, or macro
expansion. Compile generated C++ with warnings as errors and assert zero
hot-path allocations and indirect calls.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 46 | **169** | **171** | **41** |

## Ranked residual map after Task 46

This bounded terminal reduction does not establish arbitrary texture-size
loops, large work budgets, aggregate/state features, or neighboring-pixel
evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Larger work and resource contracts | `nmReindexReduce`, other render-scale or texture-dimension scans | Need a distinct work budget, dimension provenance, or pass policy. |
| 3 | Larger aggregate and word/index forms | OSD, dither, median, test pattern | Require larger arrays, general indexing/lifetime, sorting, or broader signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 46 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader resource, work, aggregate,
loop, matrix, stage, index, numeric, sampling, and macro boundary.
