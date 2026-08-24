# Post-source-array frontier audit: Task 44 direct local `out` pair

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-43.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 43 | 165 | 167 | 45 |

## Recommendation: `light-leak-direct-out-pair-v1`

The next smallest exact slice is one all-default program whose sole new ABI
form is a direct two-result helper call. Its fixed `POINT_COUNT` loop reuses
the prior literal source-`const int` and counted-loop contracts.

| Key | Exact defines | Source SHA-256 | Exact new signature |
| --- | --- | --- | --- |
| `filter/lightLeak:lightLeak` | `{}` | `61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb` | `void voronoiCell(in vec2, in float, in float, out vec3, out float)` |

`voronoiCell` has three ordinary `in` values followed by exact `out vec3
cell_color` and `out float cell_dist`. The callee never reads either output
parameter and assigns each exactly once after its loop. The two calls in
`main` pass distinct fresh local pairs, in order:
`(base_cell, base_dist)` and `(warp_cell, warp_dist)`. There is no alias,
swizzle/index lvalue, expression temporary, repeated output argument,
recursion, return value, or further output-parameter call.

The source constants are literal `TAU` (one `main` read) and literal
`POINT_COUNT = 6` (one bound read in `voronoiCell`). The helper loop is the
existing `i=0..<6` form with no loop control and six visits; two direct calls
give at most 12 charged visits per pixel. The source otherwise reuses existing
`uvec3` bitwise PRNG, level-zero `texelFetch`, `textureSize`, constructors,
ordinary arithmetic/control flow, and current builtin signatures. It has no
derivative, array, matrix, struct, uniform block, varying, sampler parameter,
`textureLod`, boolean vector, or dynamic loop.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/lightLeak:lightLeak` with its metadata-verified empty
   define map and the pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Permit only the resolved `voronoiCell` signature shown above, with exactly
   three `in` parameters followed by `out vec3` then `out float`. Retain the
   function/signature/parameter identities, directions, types, positions,
   spans, and direct callee write proof in immutable typed IR. Reject an
   overload, reordered/different parameter, `inout`, another `out` helper,
   nonvoid result, recursion, an output read, conditional/multiple/missing
   write, or a call from another function.
3. Permit exactly two calls in `main`, with their ordered input arguments and
   the two exact, pairwise-distinct automatic local lvalue pairs
   `(base_cell, base_dist)` and `(warp_cell, warp_dist)`. Prove no source or
   C++ alias, repeated target, swizzle/index/member lvalue, implicit
   conversion, pointer/reference escape, or use-before-return. Reject a
   temporary, uniform/global/array/parameter target, nested call, result
   forwarding, or a third call.
4. Emit the one helper as a direct `void` C++ function with ordinary
   `glsl::Vec3&` and `float&` output references; preserve source argument
   evaluation order and local storage. Do not create a tuple/struct return,
   heap object, dynamic output container, global/static state, callback,
   virtual dispatch, map, variant, or indirect call.
5. Reuse source-constant lowering only for literal `TAU` and `POINT_COUNT=6`.
   Retain the one `i=0..<6` loop proof, no loop control, and the 12-visit
   call-graph charge. Bind only the authored interface: `inputTex`,
   `resolution`, `tileOffset`, `fullResolution`, `alpha`, `color`, `speed`,
   `seed`, and `time`; missing or wrong-typed values fail before invocation.
   `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen light-leak oracles for alpha zero and one,
time/speed/seed variation, multiple colors, both Voronoi call results,
tile/full-frame coordinates, non-square inputs, and texture-edge fetches.
Direct tests must lock the signature/order, exact one-write-per-output proof,
two distinct lvalue pairs, six-visit helper and 12-visit call-graph charges,
source-constant injection, output write-back values, and byte-identical repeat
rendering.

Required negatives reject a signature/order/direction drift, an output read,
missing/multiple/conditional write, alias/repeated/nonlocal/temporary target,
extra or nested call, output result escape, recursive helper, const/loop/hash
drift, derivative, array, matrix, aggregate, uniform block, varying, sampler
parameter, nonzero/computed LOD, or key/define/macro drift. Compile generated
C++ with warnings as errors and assert zero hot-path allocations and indirect
calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 44 | **166** | **168** | **44** |

## Ranked residual map after Task 44

This two-local write-back rule does not establish general parameter mutation,
aggregate results, dynamic work, or neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Larger aggregate and word/index forms | OSD, dither, median, test pattern | Require larger arrays, general indexing/lifetime, sorting, or broader signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 44 adds one hash-pinned typed factory while preserving the derivative
hold and every broader parameter, aggregate, loop, array, matrix, stage,
index, numeric, sampling, and macro boundary.
