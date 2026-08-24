# Post-local-`const int` frontier audit: Task 42 glyph bit extraction

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-41.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 41 | 163 | 165 | 47 |

## Recommendation: `glyph-map-nonnegative-int-shift-v1`

The next smallest exact slice is one all-default program. It reuses the
source-constant integer lowering and existing scalar `int & int` path; its
only new operation is one range-proved signed right shift:

| Key | Exact defines | Source SHA-256 | Exact new operation |
| --- | --- | --- | --- |
| `filter/glyphMap:glyphMap` | `{}` | `853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1` | `row >> (4 - x)`, then existing `& 1` |

The only top-level source constant is literal `const int GLYPH_COUNT = 16`.
It has exactly three reads in `main`: the divisor conversion for `glyphIdx`,
the `GLYPH_COUNT - 1` clamp cap, and the matching branch bound. It
reuses the Task-40 automatic immutable constant lowering; no general global
state is admitted.

The single signed shift is in `glyphPixel`. On every path that reaches it,
`row` is an initialized nonnegative five-bit glyph row (`0..31`), and `x`
comes only from `gx = clamp(..., 0, 4)` at the sole call site. Consequently
the exact right operand `4 - x` is `0..4`. The shift is therefore defined as
the ordinary nonnegative `std::int32_t` shift, cannot inspect a sign bit, and
is semantically the same as zero-fill for these operands. Its result feeds
only the existing scalar expression `(row >> (4 - x)) & 1`, converted once to
the return float. No shifted value is stored, indexed, returned as an integer,
or used for control/loop/allocation/resource selection.

The source otherwise uses existing `uvec3 >> uint`/XOR PRNG operations,
constructors, ordinary `in` helpers, local arithmetic/control flow, and
`clamp`/`dot`/`floor`/`fract`/`length`/`max`/`min`/`texture`/`textureSize`.
It has no loop, derivative, array, matrix, struct, uniform block, varying,
`out`/`inout` helper parameter, `textureLod`, boolean vector, or sampler
array.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/glyphMap:glyphMap` with its metadata-verified empty
   define map and the pinned source hash above. Reject another key,
   nonempty/absent/additional defines, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Reuse source-constant lowering only for exact literal `const int
   GLYPH_COUNT = 16`. Retain declaration/symbol identity, literal value,
   zero-write proof, three resolved reads, and automatic-local materialization
   in immutable typed IR. Reject another type/value/initializer/read site, a
   second global integer, global array/matrix/struct/sampler state, alias or
   write, and namespace/function-static/mutable C++ storage.
3. Permit exactly one resolved `int >> int -> int` node, at the pinned
   `glyphPixel` source span, with left symbol `row` and right expression
   `4 - x`. Carry the `[0,31]` left and `[0,4]` right interval proofs, unique
   caller identity, and exact parent `& 1` node in typed IR. Emit the checked
   `std::int32_t` shift directly. Reject negative/signed-unknown operands,
   a count outside `0..30`, `<<`, scalar `uint` shift, vector shift, another
   signed shift, a shifted value used anywhere else, or a generic
   two's-complement/implementation-defined shift policy.
4. Reuse the prior scalar `int & int -> int` lowering only for the immediate
   literal-one mask of that shift. The result must convert directly to the
   float returned by `glyphPixel`; reject another mask, `|`, `^`, `~`, compound
   assignment, storage/escape, dynamic indexing, or a changed return route.
5. Bind only the authored interface: `inputTex`, `tileOffset`,
   `fullResolution`, `renderScale`, `cellSize`, `seed`, and `colorMode`.
   Missing or wrong-typed values fail before invocation. Emit no allocation,
   static/mutable state, pointer/reference escape, virtual dispatch, callback,
   map, variant, indirect call, or render-graph adapter; `PixelFn` remains
   `noexcept` and allocation-free.

Required positives are frozen glyph-map oracles for all cell sizes, tiled and
full-frame coordinates, each glyph index/variant/color mode, non-square
inputs, and boundary glyph cells. Direct tests must lock every reachable row
pattern, `x=0..4` shift-count truth table, exact low-bit mask result, the sole
shift node and parent, `GLYPH_COUNT` declaration/read identities, and
byte-identical repeated output.

Required negatives reject global constant drift, a second global int, any
unproved/negative signed shift operand or out-of-range count, left shift,
vector/uint shift, another bitwise form or result escape, loop, derivative,
array, matrix, aggregate, uniform block, varying, sampler array,
non-`in` parameter, nonzero/computed LOD, or key/define/hash/macro drift.
Compile generated C++ with warnings as errors and assert zero hot-path
allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 42 | **164** | **166** | **46** |

## Ranked residual map after Task 42

This one nonnegative glyph-row shift does not establish general signed-word
semantics, general source constants, or neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Global arrays and broader word/index forms | normalMap, OSD, dither, test pattern | Require aggregate lifetime, initialization, range, or general signed-word contracts. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 42 adds one hash-pinned typed factory while preserving the derivative
hold and every broader global, word, loop, array, matrix, aggregate, stage,
index, numeric, sampling, and macro boundary.
