# Post-sampler-parameter frontier audit: Task 32 direct `mat2` helper return

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12–31.
Derivative semantics remain unavailable pending a deliberately specified
fragment-neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 31 | 150 | 152 | 60 |

## Recommendation: `rotate-mat2-return-v1`

The next smallest exact slice is the sole corpus helper that returns a `mat2`.
The existing emitter already represents `mat2` construction and `mat2 * vec2`;
the missing capability is only this returned automatic matrix value.

| Key | Exact default defines | Exact admitted helper |
| --- | --- | --- |
| `filter/rotate:rot` | `{}` | `mat2 rotate2D(in float angle)` returning `mat2(c, -s, s, c)` |

Task 14 supplies the read-only `TAU` constant.  `rotate2D` has one float input,
two local float values (`c=cos(angle)`, `s=sin(angle)`), and the one exact
four-scalar `mat2` constructor.  `main` calls it once and immediately uses the
result as the left operand of the already-supported `mat2 * vec2` operation.
The pass otherwise has ordinary input texture sampling, level-zero
`textureSize`, vec2 `mod`, scalar/vector arithmetic, and control flow.  It has
no derivative, loop, array, UBO, varying, macro, matrix parameter, matrix
global, matrix index, or non-`in` parameter.

The corpus search finds no other `mat2`-returning helper, so this is a
one-key/one-signature representation extension rather than general matrix
function support.  A read-only emitter probe already produces a legal
`glsl::Mat2 rotate2D(... )` declaration, definition, and direct call; the
current validator's blanket matrix-return rejection is the remaining gate.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/rotate:rot` with the metadata-verified empty define
   map.  Reject every define, unlisted key, macro form, or another matrix
   return candidate.
2. Permit exactly this resolved user signature:

   ```text
   mat2 rotate2D(float) -> mat2
   ```

   Its sole parameter is `in float`; retain the function/signature IDs, source
   span, and return type in immutable typed IR.  Reject overloads, recursion,
   matrix/scalar/vector return alternatives, a matrix parameter, `out` or
   `inout`, function pointer, matrix local passed across another call, and a
   second matrix-returning helper.
3. The helper body must have exactly two fresh local float symbols initialized
   by `cos(angle)` and `sin(angle)`, then return the exact constructor
   `mat2(c, -s, s, c)`.  Retain the constructor's four ordered scalar children
   in typed IR so the C++ emitter cannot reinterpret GLSL's column-major
   layout.  Reject a diagonal constructor, fewer/more children, matrix
   arithmetic inside the helper, a dynamic index, or a returned matrix local
   assembled by another route.
4. Allow exactly one call of that signature in `main`, with the resolved
   scalar angle expression, as the direct left operand of `mat2 * vec2`.
   Materialize the returned `glsl::Mat2` by value at the existing constructor
   f32 boundary and use the current column-major `Mat2 * Vec2` implementation.
   Reject storing the result in state, returning/passing it onward, multiplying
   a vector by it, matrix add/subtract/divide, matrix-matrix multiplication,
   `mat3`/`mat4`, matrix uniform/global/array/struct fields, or a second call.
5. Emit `glsl::Mat2` by value in the generated helper prototype and definition;
   no heap allocation, pointer/reference return, static/global matrix, virtual
   dispatch, callback, variant/map lookup, or new runtime matrix class is
   introduced.  `PixelFn` remains `noexcept` and allocation-free.

Required positives are frozen rotate oracles at the default settings and all
three runtime wrap values, with stationary and animated speed/time cases and
non-square quadrant-marked inputs.  Add direct f32 tests for the four emitted
constructor lanes and a known angle/vector multiply, asserting the existing
column-major arrangement is retained.  Emitter tests must capture the exact
`glsl::Mat2 rotate2D` declaration, definition, constructor ordering, and its
single direct matrix-vector call.

Required negatives reject a `mat3`/`mat4` return, matrix parameter, scalar or
vector return, overloaded/recursive helper, a local matrix return, alternate
constructor ordering, matrix index, matrix arithmetic, multiple call sites,
state escape, nonempty defines, and every derivative builtin.  Compile
generated C++ with warnings as errors and assert zero hot-path allocations and
indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 32 | **151** | **153** | **59** |

## Ranked residual map after Task 32

These remain independent frontiers; one returned `mat2` does not establish
general matrix or interface support.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need separately validated render scale, texture-dimension/work policy, or a much larger 512-by-512 budget. |
| 3 | General matrix forms | mat3/mat4 programs, matrix parameters, matrix indexing/arithmetic | Need dimensions, layouts, operators, and lifetime rules beyond this direct value return. |
| 4 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage inputs each need their own representation contract. |
| 5 | General sampler/interface adapters | pass chaining, sampler arrays, arbitrary sampler parameters | Need ownership, aliasing, and call-ABI rules beyond Task 31's two direct read-only references. |
| 6 | Arrays and global state | normalMap, kaleido, global arrays | Need global lifetime/indexing and isolation rules beyond automatic locals. |
| 7 | Numeric/sampling/macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil MODE | Need independent word, vector-numeric, mip/filter, or preprocessor contracts. |

Task 32 adds one all-default typed factory while retaining the derivative hold
and all broader resource, matrix, aggregate, stage, array, sampler, numeric,
sampling, and macro boundaries.
