# Post-const-`vec3` frontier audit: Task 35 exact OKLab `mat3` constants

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-34.
Derivative semantics remain unavailable: independent per-pixel calls do not
define fragment-neighborhood, border, or execution-order behavior.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 34 | 154 | 156 | 56 |

## Recommendation: `oklab-forward-mat3-reuse-v1`

The next smallest coherent slice is two all-default programs that reuse the
already-projected Task-17 `mat3 × vec3`, source-local matrix, and Task-20
range-proved `vec3[i]` paths.  Their only remaining representation gap is the
two source-const forward OKLab matrices.

| Key | Exact default defines | Exact source constants |
| --- | --- | --- |
| `filter/adjust:adjust` | `{}` | `const mat3 fwdA`, `const mat3 fwdB` |
| `filter/colorspace:colorspace` | `{}` | `const mat3 fwdA`, `const mat3 fwdB` |

Both keys have the exact same two 9-scalar column-major constructors and the
same `linearToSrgb` helper body as already-admitted
`classicNoisedeck/colorLab:colorLab`.  The two programs differ only in their
otherwise-supported outer effect logic.  Both have a prior Task-14 scalar
`TAU` const, no derivatives, no array, UBO, varying, struct, matrix parameter,
matrix index, matrix return, matrix arithmetic, non-`in` parameter, or
nonempty metadata define.

The admitted constructors, in source child order, are exactly:

```text
fwdA = mat3(1.0, 1.0, 1.0,
            0.3963377774, -0.1055613458, -0.0894841775,
            0.2158037573, -0.0638541728, -1.2914855480)
fwdB = mat3(4.0767245293, -1.2681437731, -0.0041119885,
            -3.3072168827, 2.6093323231, -0.7034763098,
            0.2307590544, -0.3411344290, 1.7068625689)
```

`linear_srgb_from_oklab(in vec3 c)` performs the only matrix operations:
`fwdA * c`, followed by `fwdB * (lms * lms * lms)`.  The identical
`linearToSrgb(in vec3 linear)` body is a single Task-15 `i = 0; i < 3; ++i`
loop with five Task-20-proved `vec3[i]` reads/writes and the same
definite-initialization proof previously accepted for ColorLab.  This is an
allowlist expansion over existing runtime/emitter paths, not a new matrix or
indexing family.

## Fail-closed typed/emitter/runtime contract

1. Admit only the two sorted keys above with their metadata-verified `{}`
   define maps.  Reject every other key, nonempty define map, source rewrite,
   macro configuration, or matrix-constant profile.
2. Each key must contain exactly the two source-qualified, initialized,
   read-only top-level `mat3` declarations named `fwdA` and `fwdB`, with the
   exact ordered finite scalar constructor children shown above.  Retain stable
   symbols, source spans, constructor type, and all nine ordered children in
   immutable typed IR.  Reject a third matrix, a different name/value/order,
   diagonal or vector-column constructor, conversion, dependency, forward
   reference, non-finite result, or write.
3. Permit use of those matrices only in the resolved helper
   `vec3 linear_srgb_from_oklab(in vec3)`: exactly two `mat3 * vec3`
   expressions, with `fwdA` then `fwdB`, and no matrix value escaping that
   helper.  Reject matrix uniform/global mutation, array/struct member,
   parameter, return, index, add/subtract/divide, vector-matrix product,
   matrix-matrix product, `mat2`, and `mat4`.
4. Reuse the existing Task-14/17 function-local closure lowering.  Materialize
   each matrix as an automatic `const glsl::Mat3` in the helper that reads it,
   with the GLSL column order preserved as three `glsl::Vec3` columns.  Reuse
   the existing `Mat3 * Vec3` implementation and Float32 construction
   boundary.  Emit no C++ namespace/global/static/function-static matrix,
   heap allocation, pointer/reference matrix, dynamic dispatch, callback,
   map, or variant.
5. Reuse, but do not broaden, the existing `linearToSrgb` proof: its one
   induction symbol has interval `0..2`; `linear` is an initialized `in vec3`;
   every `srgb[i]` lane is written on all paths before return.  Reject a
   changed loop/range, additional index, vector width other than `vec3`,
   computed index, alias, `out`/`inout`, array/matrix index, or any derivative
   builtin.

Required positives are frozen colorspace oracles for HSV, OKLab, and OKLCH
modes; and adjust oracles for off/HSV/OKLab/OKLCH, hue-range/rotation,
saturation, brightness, contrast, non-square inputs, and tile offsets.
Direct tests must lock the two constructor lane orders, distinguish
column-major from row-major multiplication, assert helper-only local closure
injection, and replay all three `linearToSrgb` iterations.

Required negatives reject every excluded matrix form/use, altered literal or
column order, a third matrix, global/static lowering, a changed loop/index
proof, nonempty defines, another key, and all derivative builtins.  Compile
generated C++ with warnings as errors and assert zero hot-path allocations and
indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 35 | **156** | **158** | **54** |

## Ranked residual map after Task 35

This exact forward-matrix reuse does not authorize a general matrix/global
feature or neighborhood-aware execution.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | Other matrix/global forms | fractal alternate matrix construction, mat4 effects, computed/vector globals, global arrays | Need different constructors/dimensions, lifetime, mutation, or array/indexing rules. |
| 4 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage ownership are separate ABIs. |
| 5 | General indexing and sampler adapters | dynamic vector/matrix indexing, pass chains, sampler arrays | Need broader range/lvalue or resource ownership/call-ABI contracts. |
| 6 | Numeric, sampling, and macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil `MODE` | Each needs its own word, vector-numeric, mip/filter, or preprocessor contract. |

Task 35 adds two all-default typed factories while preserving the derivative
hold and every broader matrix, global, resource, aggregate, stage, indexing,
numeric, sampling, and macro boundary.
