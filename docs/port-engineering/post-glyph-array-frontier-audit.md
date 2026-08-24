# Post-glyph-array frontier audit: Task 49 wobble stage coordinate

## Relative long-range projected starting point

This is a read-only long-range projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, relative to prepared Tasks 12-48.
The active Task-15 correction is deliberately not merged into these counts or
contracts. Derivative semantics remain held: the execution ABI has no
fragment-neighbor, border, or scheduling contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 48 | 171 | 173 | 39 |

## Recommendation: `wobble-v-texcoord-and-const-vec3-v1`

The next smallest exact slice is `filter/wobble:wobble`. It establishes one
read-only fragment-stage coordinate, `v_texCoord`, and exactly three immutable
source constants needed by the existing bounded wobble program. It has no
loop, derivative, aggregate/index, parameter-direction, matrix, uniform-block,
or multi-pixel dependency. The current runner already carries the needed
per-pixel value as `PixelContext::uv`; this slice gives that value a single
hash-pinned GLSL interface spelling rather than creating a general stage system.

| Key | Exact defines | Source SHA-256 | Stage input | Source constants |
| --- | --- | --- | --- | --- |
| `filter/wobble:wobble` | `{}` | `1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc` | `in vec2 v_texCoord` | `TAU=6.28318530717959`, `X_NOISE_SEED=vec3(17,29,11)`, `Y_NOISE_SEED=vec3(41,23,7)` |

The metadata pass binds `inputTex`, `time`, `speed`, `range`, and `wrap`; its
declared defaults are respectively inherited time, `5`, `0.5`, and `0`.
`v_texCoord` has exactly one value source: `context.uv`, whose existing runner
definition is the bottom-left pixel center `(fragCoord.xy / resolution)`.
It is read only twice in `main`: once to form `sampleCoord` and once through
that coordinate's single `texture(inputTex, sampleCoord)` sample. It must not
be interpolated, synthesized from a second texture, or made bindable by caller
data.

The source's PRNG reuses existing unsigned-vector arithmetic, lane writes,
unsigned vector right shift/XOR, scalar casts, and exact `uint` wrap behavior.
The signed `int(wrap)` only selects mirror/repeat/clamp. The two seed vectors
are passed only by value to `simplexRandom`; they have no write, address,
array, struct, or resource escape. `TAU` is consumed only in `sin`/`cos`.

## Fail-closed typed/emitter/runtime contract

1. Admit only `filter/wobble:wobble` with the metadata-verified empty define
   map and pinned source hash above. Reject another key, a nonempty/absent/
   additional define, source rewrite, macro expansion, compatibility transform,
   or numeric-literal exception.
2. Admit exactly one interface declaration: read-only fragment input
   `in vec2 v_texCoord`. Lower it directly to `context.uv` at the existing
   bottom-left pixel-center precision boundary. Reject another interface name,
   type, direction, stage, qualifier, array/interface block, write, function
   parameter escape, binding override, or derived-coordinate replacement.
3. Admit only the three source constants named above, retaining their stable
   symbols, exact types, ordered three-lane literal initializers, and
   `glsl-f32` conversion boundary in typed IR. Materialize them as automatic
   immutable `float`/`glsl::Vec3` values in the generated pixel path; do not
   emit namespace/function-static storage, heap allocation, pointers,
   references, or a general source-global/vector-constant facility.
4. Reuse the established `uvec3` PRNG and scalar conversion contracts only for
   the authored `pcg`, `hash31`, `noise3d`, `simplexRandom`, and `applyWrap`
   call graph. Preserve unsigned 32-bit wrap and the nonnegative float-to-uint
   conversion branches verbatim. Reject scalar word extensions, a new word
   operator, signed shift, bitwise-not/or/and, new vector width, or any
   additional global/source constant.
5. Bind only the authored input sampler and four pass uniforms, preserve
   nearest bottom-left ordinary `texture` sampling and the existing `PixelFn`
   `noexcept`/allocation-free ABI. Reject `textureLod`, texel fetch changes,
   additional samplers, sampler arrays, mutable state, loops, derivative,
   matrix, struct, uniform block, `out`/`inout`, discard, or neighbor/resource
   scheduling behavior.

Required positives are frozen wobble oracles for all three wrap modes,
time/speed/range extrema and interior values, non-square and one-pixel axes,
input alpha preservation, every seed-vector lane, and repeated/tiled output.
Direct tests must lock the single interface binding to `context.uv`, pixel
center orientation, the three ordered source constants, source-f32 literal
bits, one sampler binding, and byte-identical repeated output. Compile emitted
C++ with warnings as errors and assert zero hot-path allocations and indirect
calls.

Required negatives reject interface/global/literal/call-graph drift; a second
varying; interpolation or caller-supplied stage data; vector-constant mutation
or escape; a new unsigned/signed word operator; array/index, struct, matrix,
uniform block, parameter direction, loop, derivative, nonzero/computed LOD,
additional sampler, key/define/hash/macro, or numeric-contract drift.

## Relative projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Relative after Task 49 | **172** | **174** | **38** |

## Ranked residual map after Task 49

This one source-coordinate alias does not establish general stage interfaces,
scalar-word hashing, source aggregates, arbitrary indexing, derivative
semantics, or multi-pixel work.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Scalar word and larger aggregate/index forms | spookyTicker, dither, median, test pattern | Need scalar unsigned hash/mask rules, more arrays/indexing/lifetime, sorting, or broader signed-word contracts. |
| 3 | Matrix, struct, copy-out, and block interfaces | historicPalette/palette, Julia/Mandelbrot/Newton, remap | Need aggregate layout, parameter direction, copy-out, or uniform-block contracts. Mandelbrot alone has six `out` results, `MAX_ITER=500`, and `log`. |
| 4 | Broader stage and texture pathways | grime, texture, wormhole deposit | Need additional stage/resource inputs, scalar-word or bit-reinterpretation rules, loops, or feedback ownership. |
| 5 | General work and resource policy | dynamic multi-pixel scans | Need distinct dimension provenance, output cardinality, and budget rules. |

Task 49 adds one hash-pinned typed factory in this relative projection while
preserving the derivative hold and every broader interface, word, aggregate,
index, work, resource, sampling, numeric, and macro boundary.
