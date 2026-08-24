# Post-smooth-blend frontier audit: Task 38 exact `bvec2` equality reduction

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-37.
Derivative semantics remain held: the execution ABI has no fragment-neighbor,
border, or scheduling specification.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 37 | 158 | 160 | 52 |

## Recommendation: `emboss-full-frame-equal-v1`

The next smallest exact slice is one pinned macro profile that reuses the
projected fixed local arrays, counted loops, helper-local `vec3` const, and
existing `all(bvec2)` reduction. Its only new relation is two direct vec2
equalities which preserve the authored full-frame sampling branch:

| Key | Exact default defines | Exact admitted relation sites |
| --- | --- | --- |
| `filter/emboss:emboss` | `{ "STYLE": 0 }` | `equal(tileOffset, vec2(0.0))`; `equal(fullResolution, resolution)` |

The two results feed exactly:

```glsl
bool fullFrame = all(equal(tileOffset, vec2(0.0)))
              && all(equal(fullResolution, resolution));
```

Both are `equal(vec2,vec2) -> bvec2`; the two existing `all(bvec2) -> bool`
reductions and scalar `&&` then choose the exact `colorTexelSize` expression.
No bvec value escapes, is stored, indexed, returned, or passed to a helper.

Task 16 already covers the two function-local 9-element `float`/`vec2` array
sets and their proved literal/`i=0..<9` reads; Task 15 covers the two nine-trip
loops.  Task 34's source-local vector contract covers exactly
`const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722)`, read only by `grayEmboss`.
The authoritative define map is precisely `{"STYLE":0}`; no other macro
configuration is included. The source has no derivative, UBO, varying, matrix,
struct, sampler parameter, non-`in` parameter, or dynamic loop bound.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/emboss:emboss` with the ordered metadata-verified define
   map `{ "STYLE": 0 }`. Reject absent/nonzero/additional defines, another
   key, a source rewrite, or a macro-family expansion.
2. Permit exactly two resolved builtin nodes of the one signature
   `equal(vec2,vec2) -> bvec2`, both in `main` and only as direct children of
   the two `all(bvec2)` calls above. The first operands/second operands must
   resolve, in order, to `(tileOffset, vec2(0.0))` and
   `(fullResolution, resolution)`. Retain argument symbols, result type,
   source spans, and parent reduction IDs in immutable typed IR.
3. Reuse the existing `all(bvec2) -> bool` path only for those two values and
   permit their conjunction only as the initializer of `fullFrame`. Emit a
   fixed two-lane `glsl::BVec2` equality result and direct boolean reduction;
   preserve Float32 materialization before each lane comparison. Reject
   `notEqual`, ordering relations, `bvec3`/`bvec4`, `any`, other reductions,
   bvec construction, bvec globals/parameters/arrays/returns/indexing, or a
   boolean-vector value outside this expression tree.
4. Reuse Task-34 local const lowering only for the exact literal `LUMA` and
   its `grayEmboss` dot uses. Reuse Task-16's two 9-element automatic arrays
   and Task-15's two `i=0..<9` loops exactly; reject a changed extent/index
   proof, global array, nonlocal array parameter, new loop form, or widened
   source-constant contract.
5. Emit no namespace/global/static mutable state, heap allocation,
   bounds-check slow path, pointer/reference escape, virtual dispatch,
   callback, map, or variant. The generated `PixelFn` remains `noexcept` and
   allocation-free.

Required positives are frozen emboss oracles at `STYLE=0` for a full frame and
tiled subframe (both equality outcomes), the default color path
`angle=135,height=1`, nondefault angle/height, alpha/chroma/amount extremes,
and non-square textures. Direct tests must lock the two lane equality truth
tables, `all` reductions, short-circuit conjunction, `colorTexelSize` branch,
fixed 9-element array initialization/read proofs, and helper-local LUMA
materialization.

Required negatives reject a changed define map, another relation/reduction or
vector width, equality outside `fullFrame`, bvec escape/index/write, altered
array shape/proof, a nonliteral/computed LUMA, another key, and every
derivative builtin. Compile generated C++ with warnings as errors and assert
zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 38 | **159** | **161** | **51** |

## Ranked residual map after Task 38

This two-lane equality/reduction does not establish general boolean vectors,
macro configurations, or neighborhood-aware execution.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | General boolean/global/indexing forms | other equalities/reductions, computed vector globals, global arrays, dynamic vector/matrix indexing | Need broader type, initialization, range, lifetime, and aliasing rules. |
| 4 | Matrix and aggregate interfaces | fractal/mat4, historicPalette/palette, Julia/Mandelbrot/Newton | Need different matrix/aggregate layout, copy-out, and lifetime contracts. |
| 5 | Stage/resource interfaces | remap UBO; grime/texture varyings; pass chains and sampler arrays | Need std140, stage ownership, or resource call-ABI rules. |
| 6 | Numeric, sampling, and macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil `MODE` | Each needs its own word, vector-numeric, mip/filter, or preprocessor contract. |

Task 38 adds one macro-pinned typed factory while preserving the derivative
hold and every broader boolean, macro, global, resource, matrix, aggregate,
stage, indexing, numeric, sampling, and loop boundary.
