# Post-literal-`vec3`-index frontier audit: Task 34 helper-local `vec3` const

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-33.
Derivative semantics remain held: a per-pixel invocation cannot reproduce
fragment-neighborhood, border, or scheduling behavior.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 33 | 153 | 155 | 57 |

## Recommendation: `smooth-edge-luma-const-vec3-v1`

The next smallest exact slice is one all-default program with one immutable
source vector constant:

| Key | Exact default defines | Exact admitted declaration | Exact use |
| --- | --- | --- | --- |
| `filter/smooth:smoothEdge` | `{}` | `const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114)` | one read in `float luminance(in vec3 rgb)` as `dot(rgb, LUMA_WEIGHTS)` |

The initializer is a direct three-finite-float constructor, has no dependency,
and whole-program typed-symbol inspection finds no write.  `main` never reads
the constant directly; the helper is the only use, so it needs one automatic
function-local materialization.  The pass otherwise already validates through
the current vocabulary: one input sampler, level-zero `textureSize` and
`texelFetch`, integer-coordinate clamp arithmetic, scalar/vector math,
control flow, and a vec4 output.  It has no derivative, loop, array, matrix,
struct, UBO, varying, macro define, sampler parameter, or non-`in` parameter.

A read-only probe that admitted only this exact const form emitted:

```cpp
const glsl::Vec3 LUMA_WEIGHTS =
    glsl::FloatExpr<3>(static_cast<float>(0.299),
                       static_cast<float>(0.587),
                       static_cast<float>(0.114));
```

at the entry of `luminance`, then emitted the existing direct `glsl::dot`
call.  A complementary validator probe treating only that declaration as an
already-bound value passed every later capability gate.  No new vector runtime
or runtime indexing is required.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/smooth:smoothEdge` with its metadata-verified empty
   define map.  Reject every other key, nonempty define map, source rewrite,
   or macro-configuration request.
2. Admit exactly one top-level source-qualified `const vec3`, with stable
   symbol name `LUMA_WEIGHTS`, the exact direct initializer
   `vec3(0.299, 0.587, 0.114)`, and three finite scalar float literals in that
   order.  Preserve declaration/source spans, symbol identity, constructor
   type, and ordered children in immutable typed IR.  Reject a scalar splat,
   vector/cast expression, swizzle, binary expression, builtin/call,
   dependency, forward reference, duplicate declaration, or any other global
   type or name.
3. A whole-program stable-symbol audit must prove that no direct/compound
   assignment, increment/decrement, swizzle/index/member write, `out`/`inout`
   escape, or address/reference escape targets the admitted declaration.  Its
   only permitted read is the resolved second argument of `dot(rgb,
   LUMA_WEIGHTS)` in `luminance(in vec3)`.
4. At every function that reads the admitted symbol, emit one ordinary C++
   `const glsl::Vec3` at function entry from the typed constructor children;
   for this key that is `luminance` only.  Preserve the existing Float32
   constructor boundary.  Emit no namespace/global/static/function-static
   object, runtime lookup, pointer/reference binding, allocation, virtual
   dispatch, callback, map, or variant in the pixel path.
5. Do not generalize source globals.  Reject other `vec3` constants (including
   computed seeds), `vec2`/`vec4`, bool/int/uint, arrays, matrices, structs,
   samplers, uniform globals, mutable/uninitialized globals, globals used by
   `main`, and all derivative builtins.  Existing earlier key-scoped scalar
   constant and matrix contracts remain independently bounded.

Required positives are frozen smooth-edge oracles for `smoothType == 0`
pass-through and nonzero edge-map paths, low/high threshold boundaries,
non-square input dimensions, and all four clamped neighbor directions.  Add
direct typed/emitter tests that lock the one declaration, exact three lane
bits/order, helper-only closure injection, direct `dot`, and absence of a
C++ global/static symbol.  Binding tests retain the existing required
`inputTex`, `tileOffset`, `fullResolution`, `smoothType`, and `threshold`
contracts.

Required negatives reject a different name/type/arity/literal, a computed or
dependent initializer, a second vector const, an unused/main-level use, every
write or escape path, a nonempty define map, another key, an array/matrix
global, and every derivative builtin.  Compile generated C++ with warnings as
errors and assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 34 | **154** | **156** | **56** |

## Ranked residual map after Task 34

This one literal helper-local constant establishes neither general source
globals nor neighbor-aware execution.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` need explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Require independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | General global and aggregate representation | other vector constants, global arrays, normalMap, kaleido, historicPalette, palette | Need generalized initializer, lifetime, indexing, aggregate layout, and isolation rules. |
| 4 | Matrix and general indexing forms | adjust/colorspace mat3 constants, mat4 effects, dynamic vector/matrix indexing | Need dimension/layout/operator and range/lvalue rules beyond one literal vec3 closure. |
| 5 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage ownership are separate ABIs. |
| 6 | Numeric, sampling, and macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil `MODE` | Each needs its own word, vector-numeric, mip/filter, or preprocessor contract. |

Task 34 adds one all-default typed factory while preserving the derivative
hold and every broader global, resource, aggregate, stage, matrix, indexing,
numeric, sampling, and macro boundary.
