# Post-OKLab-`mat3`-reuse frontier audit: Task 36 edge `bvec3` contour path

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-35.
Derivative semantics remain held: the current execution ABI has no specified
fragment-neighborhood, border, or scheduling model.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 35 | 156 | 158 | 54 |

## Recommendation: `edge-contour-bvec3-v1`

The next smallest exact slice is the one all-default program whose remaining
post-Task-34/35 gap is a fixed three-lane boolean contour calculation:

| Key | Exact default defines | Exact new typed forms |
| --- | --- | --- |
| `filter/edge:edge` | `{}` | one `greaterThanEqual(vec3,vec3) -> bvec3`, one `lessThan(vec3,vec3) -> bvec3`, and one `bvec3(bool,bool,bool)` |

The existing fixed-loop path already covers its nested `dy=-3..3` and
`dx=-3..3` convolution (49 charged visits).  Task 34's source-local constant
path covers exactly `const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722)`, read as
the second `dot` operand five times in `contourConv` and three times in
`main`.  An in-memory audit that exposes only the global and already-admitted
loop forms reaches `bvec3` as the first and sole later type gate.  The source
has no derivative, array, matrix, struct, UBO, varying, sampler parameter,
non-`in` parameter, or nonempty metadata define.

Inside `contourConv`, the exact shape is:

```glsl
bvec3 centerOnSide = upperSide
    ? greaterThanEqual(centerRGB, vec3(lvl))
    : lessThan(centerRGB, vec3(lvl));
bvec3 crossing = bvec3(/* exact r, g, b scalar boolean clauses */);
return vec3(crossing.r ? 0.0 : 1.0,
            crossing.g ? 0.0 : 1.0,
            crossing.b ? 0.0 : 1.0);
```

There are exactly two relational builtin nodes and one boolean-vector
constructor; `crossing` is read only by those three literal component swizzles.
This is a key-locked, lane-explicit comparison profile, not general boolean
vector, relational, or aggregate support.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/edge:edge` with the metadata-verified empty define map.
   Reject every other key, define map, source rewrite, or macro configuration.
2. Reuse the Task-34 local-constant mechanism only for source-qualified
   `const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722)`.  Preserve the three
   ordered Float32 constructor children and stable symbol identity; prove zero
   writes.  Materialize one automatic `const glsl::Vec3 LUMA` at the entry of
   each reader, exactly `contourConv` and `main`; do not emit static/global
   storage or a general vector-global facility.
3. Permit only these two resolved relational signatures, each once and only as
   the two arms of `upperSide ? ... : ...` for `centerOnSide`:

   ```text
   greaterThanEqual(vec3 centerRGB, vec3(lvl)) -> bvec3
   lessThan(vec3 centerRGB, vec3(lvl)) -> bvec3
   ```

   Retain operand/result types, resolved symbol IDs, call spans, and branch
   position in typed IR.  Reject `equal`, `notEqual`, `greaterThan`,
   `lessThanEqual`, `all`, `any`, scalar/vector overload variation, other
   widths, calls in another function, or a second relational site.
4. Permit exactly two automatic `bvec3` locals: `centerOnSide` from that
   conditional and `crossing` from one three-child `bvec3(bool,bool,bool)`
   constructor.  Each constructor child must be the corresponding literal
   `r`, `g`, or `b` component of `centerOnSide` conjoined with the source's
   scalar neighborhood comparison clause.  Permit `crossing` only in the
   three ordered `r/g/b` conditional result lanes.  Reject bvec globals,
   uniforms, parameters, arrays, returns, assignments after initialization,
   indexing, conversion, copy/escape, or any bool-vector operation elsewhere.
5. Emit lane-explicit, allocation-free code: construct `glsl::BVec3` from the
   three Float32-materialized scalar comparisons and use the existing
   compile-time swizzle helpers for components.  Do not introduce a dynamic
   boolean container, unchecked indexing, pointer/reference escape, virtual
   dispatch, callback, map, variant, or per-pixel allocation.  `PixelFn`
   remains `noexcept`.

Required positives are frozen edge oracles for contour (`kernel == 2`) with
both `useLuma` branches and both contour sides; the eight other blend modes;
radius clamps at 0, interior, and 3; threshold/invert/mix boundaries; and
non-square inputs.  Direct tests must assert the two comparison truth tables,
the `r/g/b` constructor order, source-local `LUMA` injection in both reader
functions, and output channel isolation for channel mode.

Required negatives reject every excluded relational builtin/width, a second
bvec declaration or constructor, an alternate component order, dynamic index,
bvec write/escape, nonliteral or altered `LUMA`, nonempty defines, another
key, loop-bound changes, and every derivative builtin.  Compile generated C++
with warnings as errors and assert zero hot-path allocations and indirect
calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 36 | **157** | **159** | **53** |

## Ranked residual map after Task 36

This exact bvec contour path does not define general relational/vector-state
behavior or neighboring-pixel execution.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | General boolean/global/indexing forms | general bvec relations/reductions, computed vector globals, global arrays, dynamic vector/matrix indexing | Need broader type, initialization, range, lifetime, and aliasing rules. |
| 4 | Matrix and aggregate interfaces | fractal alternate matrix construction, mat4 effects, historicPalette/palette, Julia/Mandelbrot/Newton | Need different matrix/aggregate layout, copy-out, and lifetime contracts. |
| 5 | Stage/resource interfaces | remap UBO; grime/texture varyings; pass chains and sampler arrays | Need std140, stage ownership, or resource call-ABI rules. |
| 6 | Numeric, sampling, and macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil `MODE` | Each needs its own word, vector-numeric, mip/filter, or preprocessor contract. |

Task 36 adds one all-default typed factory while preserving the derivative
hold and every broader boolean, global, resource, matrix, aggregate, stage,
indexing, numeric, sampling, and macro boundary.
