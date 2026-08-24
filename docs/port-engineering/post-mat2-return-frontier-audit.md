# Post-`mat2`-return frontier audit: Task 33 literal `vec3` lane indexing

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12-32.
The derivative ABI remains unavailable: the current per-pixel execution model
does not define fragment-neighborhood, border, or scheduling semantics.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 32 | 151 | 153 | 59 |

## Recommendation: `literal-vec3-lane-index-v1`

The next smallest coherent representation slice is the two all-default
programs that use only literal bracket selection of a main-local `vec3`.
They otherwise pass the current typed capability audit once each bracket node
is canonically represented as the already-supported equivalent swizzle.

| Key | Exact default defines | Exact bracket-lane inventory |
| --- | --- | --- |
| `classicNoisedeck/lensDistortion:lensDistortion` | `{}` | main-local `hsv`: five lane-0, two lane-1, one lane-2 selections |
| `filter/prismaticAberration:prismaticAberration` | `{}` | main-local `hsv`: two lane-0, one lane-1 selections |

All eleven indices resolve to scalar integer literals in `{0,1,2}` over the
same resolved local `vec3` symbol.  The first key has no derivatives and uses
the lanes for hue adjustment in both its chromatic and prismatic branches; its
only lane-2 read feeds `vec3(hsv[2])`.  The second is the prismatic-only path.
Neither source has an array, matrix, vector-parameter, vector global, UBO,
varying, loop, or derivative hidden behind this gate.  Their source `#define`
text is pinned corpus input, while both authoritative metadata define maps are
empty.

A read-only typed-IR probe replaced only these verified index nodes in memory
with their exact `x`/`y`/`z` swizzle equivalents.  Both programs then passed
the capability validator and rendered through the typed emitter.  The emitted
write form is the existing compile-time `glsl::set_swizzle<I>(hsv, ...)`; no
runtime subscript, bounds check, allocation, or new vector runtime is needed.
The corpus has one other literal-vector-index user,
`classicNoisedeck/colorLab:colorLab`, already consumed by the earlier
matrix/vector-index slice.  This task is not authorization to generalize that
prior key-scoped contract.

## Fail-closed typed/emitter/runtime contract

1. Admit exactly the two sorted keys above and only their metadata-verified
   `{}` define maps.  Reject every other key, define map, source rewrite, or
   macro-configuration request.
2. Admit an index expression only when its resolved base is the named
   automatic `vec3 hsv` symbol in `main` of one of those keys, its resolved
   index is an integer literal exactly `0`, `1`, or `2`, and its result type is
   `float`.  Keep the base symbol ID, literal value, source span, lvalue/rvalue
   category, and selected lane in immutable typed IR.  The exact per-key
   inventories above are part of the validator gate.
3. Permit these selections only as ordinary scalar rvalues or the direct left
   side of `=`.  Retain the current assignment evaluation order and Float32
   materialization boundary.  Reject compound assignment, pre/post increment,
   address/reference escape, passing a lane as an `out`/`inout` actual, aliases,
   or storing an indexed expression for later mutation.
4. Canonicalize a checked lane to the corresponding existing swizzle form:
   `0 -> x`, `1 -> y`, and `2 -> z`.  The emitter must consume that checked
   typed record and emit `glsl::swizzle<I>(...)` for reads and
   `glsl::set_swizzle<I>(...)` for writes.  Do not lower to a runtime
   `operator[]`, an unchecked source expression, pointer arithmetic, or a new
   general indexing helper.
5. Reject vector widths other than `vec3`; any nonliteral, negative, or
   out-of-range index; local/parameter/uniform/global bases other than the
   admitted `hsv`; nested indexing; arrays; matrices; structs; sampler
   indexing; vector construction from an index; and all derivative builtins.
   No capability for dynamic vector indexing, array indexing, matrix indexing,
   or general lvalue indexing is added.

Required positives are frozen lens-distortion oracles covering both `mode`
branches, asymmetric/non-square input geometry, animated and stationary hue
paths, and the output blend alternatives; and prismatic-aberration oracles
covering hue rotation/range, modulation, saturation, passthrough, and boundary
sampling.  Direct typed/emitter tests must assert the exact 8/3 inventories,
the three literal-to-swizzle mappings, scalar reads, and `set_swizzle` writes.

Required negatives reject lane `-1` or `3`, a uint/float expression used as an
index, a dynamic local or uniform index, `vec2`/`vec4`, an array/matrix/struct
base, an index on a parameter/global/uniform, compound or increment writes,
an extra index site, nonempty defines, another program key, and every
derivative builtin.  Compile the generated C++ with warnings as errors and
assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 33 | **153** | **155** | **57** |

## Ranked residual map after Task 33

This literal, local lane form does not establish general indexing or any
neighboring-pixel semantics.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` need an explicit neighborhood, border, and scheduling contract. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Require independently validated render scale, texture-dimension/work policy, or a much larger work budget. |
| 3 | General indexing and aggregates | dynamic vector lanes, global arrays, normalMap, kaleido | Need range, lifetime, definite-initialization, and alias rules beyond one literal local lane. |
| 4 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage ownership remain distinct ABIs. |
| 5 | General matrix and sampler adapters | mat4 effects, matrix parameters/indexing, pass chains, sampler arrays | Need dimensions/layouts or resource ownership/call-ABI rules beyond automatic local values. |
| 6 | Numeric, sampling, and macro extensions | nonconstant signed shifts, vector round, computed/nonzero `textureLod`, nondefault oil `MODE` | Each needs its own word, vector-numeric, mip/filter, or preprocessor contract. |

Task 33 adds two all-default typed factories while preserving the derivative
hold and every broader indexing, resource, aggregate, stage, matrix, sampler,
numeric, sampling, and macro boundary.
