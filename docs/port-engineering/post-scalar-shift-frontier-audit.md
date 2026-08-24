# Post-scalar-shift frontier audit: Task 43 source-constant Sobel arrays

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-42.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 42 | 164 | 166 | 46 |

## Recommendation: `normal-map-source-const-array-v1`

The next smallest exact slice is one all-default Sobel program. It extends
immutable source-constant lowering only to the two literal `uint` declarations
and three fixed, literal-initialized arrays below; all reads reuse the prior
nine-trip induction/index proof.

| Key | Exact defines | Source SHA-256 | Exact source-constant aggregate set |
| --- | --- | --- | --- |
| `filter/normalMap:normalMap` | `{}` | `384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb` | `uint CHANNEL_COUNT=4u`, `uint CHANNEL_CAP=4u`, `ivec2 SOBEL_OFFSETS[9]`, `float SOBEL_X_KERNEL[9]`, `float SOBEL_Y_KERNEL[9]` |

`CHANNEL_COUNT` is source-declared but has no reads and must produce no emitted
local. `CHANNEL_CAP` has exactly two reads in `sanitize_channelCount`, both as
the same literal-four cap. The three arrays have direct literal constructors
with exactly nine children each; their only accesses are the three reads in
`main`, indexed by the fresh `int i` of `for (int i = 0; i < 9; i++)`. The
Task-15 proof gives `i=0..8`, exactly nine visits, no loop control statement,
and no return in the loop. There are no stores, aliases, parameters, returns,
copies, or escape of any source array.

The program otherwise reuses existing `round(float)`, level-zero
`texelFetch(sampler2D, ivec2, 0) -> vec4`, `textureSize`, constructors, local
arithmetic/control flow, and `abs`/`clamp`/`max`/`pow`. It has no derivative,
dynamic loop, sampler array, matrix, struct, uniform block, varying,
`out`/`inout` helper parameter, `textureLod`, boolean vector, or mutable
global state.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/normalMap:normalMap` with its metadata-verified empty
   define map and pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Permit only the exact five source constants named above. Preserve their
   declaration/symbol identities, scalar/element types, literal initializers,
   array length nine, ordered constructor children, dependency/read sets, and
   whole-program zero-write proof in immutable typed IR. Reject another
   scalar type/value, an initializer expression/dependency, mutable/unset
   declaration, array constructor variation, any other extent/rank/element
   type, matrix/struct/sampler array, global array write, global array
   parameter/return/copy, or a general global-array facility.
3. Materialize only the required dependency closure as automatic immutable
   locals: `CHANNEL_CAP` in `sanitize_channelCount`, and the three
   `std::array` values in `main` using their exact source order and Float32/
   integer construction boundaries. Omit unused `CHANNEL_COUNT`. Do not emit
   namespace, function-static, heap, or shared mutable storage.
4. Reuse Task-15/16 indexed-array lowering only for three exact reads:
   `SOBEL_OFFSETS[i]`, `SOBEL_X_KERNEL[i]`, and `SOBEL_Y_KERNEL[i]` in the
   exact `i=0..<9` loop. Retain the `[0,8]` range proof, definite
   initialization, source span, base symbol identity, and nine-visit charge.
   Reject another index/base/read/write, literal or dynamic index change,
   altered loop header/control, array address/reference escape, or bounds
   check/slow path in the hot pixel loop.
5. Bind only the authored interface: `tileOffset`, `fullResolution`,
   `inputTex`, `size`, and `motion`. Missing or wrong-typed values fail before
   invocation, including declared-but-unused `motion`. Reuse existing level-
   zero integer-fetch and texture-size behavior. Add no allocation, dynamic
   dispatch, callback, map, variant, indirect call, pointer/reference escape,
   or render-graph adapter; `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen normal-map oracles for all channel-count
branches, zero/nonzero size fallbacks, wrap boundaries, high-contrast Sobel
directions, alpha preservation, non-square input, and tile offsets. Direct
tests must lock all nine ordered initializer entries of each array, one unused
constant omission, the two cap reads, each of the three `i=0..8` index traces,
the nine-visit loop charge, source-local injection locations, and byte-
identical repeated output.

Required negatives reject any source constant or initializer drift, another
array/global/dependency, element/length/rank change, array read/write/escape
outside the three sites, changed loop/index proof, a vector/matrix aggregate,
nonzero/computed LOD, new sampler form, derivative, dynamic loop, struct,
uniform block, varying, non-`in` parameter, or key/define/hash/macro drift.
Compile generated C++ with warnings as errors and assert zero hot-path
allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 43 | **165** | **167** | **45** |

## Ranked residual map after Task 43

This fixed immutable Sobel table does not establish general source aggregates,
dynamic indexing/work, or neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Larger aggregate and word/index forms | OSD, dither, median, test pattern | Require larger arrays, general indexing/lifetime, sorting, or broader signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 43 adds one hash-pinned typed factory while preserving the derivative
hold and every broader global, aggregate, loop, array, matrix, stage, index,
numeric, sampling, and macro boundary.
