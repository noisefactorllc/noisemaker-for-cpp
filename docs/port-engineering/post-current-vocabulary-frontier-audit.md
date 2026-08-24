# Post-current-vocabulary frontier audit: Task 40 fixed `const int` loop bound

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-39.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 39 | 161 | 163 | 49 |

## Recommendation: `vaseline-const-int-loop-bound-v1`

The next smallest exact slice is one all-default program whose only new form
is a source-qualified, literal initialized `const int` used by an already
projected fixed counted loop:

| Key | Exact defines | Source SHA-256 | Exact new declaration |
| --- | --- | --- | --- |
| `filter/vaseline:upsample` | `{}` | `39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461` | `const int TAP_COUNT = 32` |

`TAP_COUNT` has exactly two reads, both in `main`: the upper bound of
`for (int i = 0; i < TAP_COUNT; i++)`, and `float(TAP_COUNT)` in the local
`t` expression. The loop is the existing Task-15 shape: fresh `int i`, literal
zero initializer, strict `<`, post-increment, no `break`/`continue`/return,
and exactly 32 charged visits. The value cannot affect allocation, indexing,
recursion, sampler choice, a texture coordinate extent, or another call
boundary.

The source's other three top-level declarations are already-admitted literal
`const float` values: `RADIUS = 48.0`, `GOLDEN_ANGLE = 2.39996323`, and
`BRIGHTNESS_ADJUST = 0.15`. All four declarations are read only in `main` and
must lower as automatic immutable locals, never namespace, function-static,
or mutable shared state. The program otherwise uses only prior forms: one
level-zero `texelFetch(sampler2D, ivec2, 0) -> vec4`, one `texture`, one
`textureSize`, local arithmetic/control flow, and the existing
`abs`/`clamp`/`cos`/`exp`/`max`/`mix`/`sin`/`smoothstep`/`sqrt` builtin paths.
It has no derivative, array, matrix, struct, uniform block, varying,
`out`/`inout` helper parameter, `textureLod`, boolean-vector, or dynamic loop
form.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/vaseline:upsample` with the metadata-verified empty
   define map and the pinned source hash above. Reject another key, a
   nonempty/absent/additional define, source rewrite, macro expansion,
   compatibility transform, or numeric-literal exception.
2. Permit exactly one new source global declaration: the literal,
   source-qualified `const int TAP_COUNT = 32`. Retain its declaration and
   symbol identities, `int` type, literal value, zero-write proof, reader
   functions, and declared constant value in immutable typed IR. Reject a
   `uint`/`bool`/float/vector/matrix/array/struct/sampler global through this
   new path, an initializer expression/dependency, a non-32 value, a forward
   reference, a write or alias, a second `const int`, and global/static C++
   materialization.
3. Permit `TAP_COUNT` reads only as the exact loop upper bound and the direct
   operand of `float(TAP_COUNT)` in `t = float(i) / float(TAP_COUNT)`. Reuse
   the Task-15 checked loop proof: `i=0..<32`, one lexical level, exactly 32
   visits, and no loop control statement. Reject a different comparison or
   update, an altered bound/value, a dynamic/unproved arithmetic bound, use as
   an index/allocation/recursion control, a second loop, or a converted value
   escaping this expression.
4. Reuse existing source-const lowering for the three named `const float`
   literals and emit all four values as `const` automatic locals in `main` in
   source order. Preserve Float32 literal/materialization rules for the float
   values and ordinary checked `std::int32_t` representation for `TAP_COUNT`.
   Reject mutable storage, pointer/reference escape, or any general
   scalar-global vocabulary expansion.
5. Preserve the exact authored interface: `inputTex`, `resolution`,
   `tileOffset`, `fullResolution`, `renderScale`, and `alpha`. Reuse current
   level-zero integer-fetch, normalized sampling, and texture-size behavior;
   missing or wrong-typed binding fails before invocation. Do not introduce
   allocation, dynamic dispatch, callback, map, variant, virtual call, or
   render-graph adapter. `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen vaseline oracles for alpha zero (the early
return) and positive alpha, tile and full-frame coordinates, non-square
textures, low/high render scale, high-contrast inputs, and edge samples. Direct
tests must lock the literal value and source-order constant injection, the two
and only two `TAP_COUNT` reads, conversion provenance, all 32 loop iterations,
one texture and one level-zero fetch path, and byte-identical repeated output.

Required negatives reject a changed const type/value/initializer/read site, a
second global int, any global array or mutable/static storage, a changed loop
header or visit charge, a dynamic bound/index, nonzero/computed LOD, added
builtin or sampler form, derivative builtin, array, matrix, aggregate,
uniform block, varying, non-`in` parameter, key/define/hash drift, and every
unlisted macro configuration. Compile generated C++ with warnings as errors
and assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 40 | **162** | **164** | **48** |

## Ranked residual map after Task 40

This one-key integer-constant/loop-bound proof does not establish general
source globals, uniform-driven work, or neighboring-pixel evaluation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource and dynamic-work contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Render-scale, texture-dimension, or charged-work bounds need independently enforced runtime proofs. |
| 3 | Global arrays and word/index forms | normalMap, OSD, dither, glyph map, test pattern | Require aggregate lifetime, initialization, range, and signed-word contracts beyond one literal int. |
| 4 | Matrix, aggregate, and stage interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton, remap/grime/texture | Need separate layout, copy-out, binding, or stage-ownership contracts. |
| 5 | Sampling and numeric extensions | nonconstant `textureLod`, remaining scalar bitwise paths | Need independent mip/filter or two's-complement rules. |

Task 40 adds one hash-pinned typed factory while preserving the derivative
hold and every broader global, loop, array, matrix, aggregate, stage, index,
numeric, sampling, and macro boundary.
