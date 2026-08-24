# Post-zoom frontier audit: Task 27 constrained curl vector math

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–26.
Derivative semantics remain held pending a deliberate neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 26 | 145 | 147 | 65 |

## Recommendation: `curl-vector-mod-tanh-v1`

The next coherent non-derivative builtin slice is the exact vector math family
used by the fixed-default curl generator.  Its existing counted loop is bound
by `OCTAVES=1`; no dynamic loop, interface, array, matrix, or derivative work
is added.

| Key | Exact default defines | Required overloads |
| --- | --- | --- |
| `synth/curl:curl` | `{ "OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": true }` | `mod(vec3,float) -> vec3`; `mod(vec4,float) -> vec4`; `tanh(vec3) -> vec3` |

The source uses `mod(vec3,289.0)` and `mod(vec4,289.0)` only in its two
`permute` overloads, and applies `tanh` only to the final `vec3 curl` value.
Task 12 deliberately admitted only scalar/vec2 `mod`; Task 15 already proves
the `for (int i=0; i<OCTAVES; i++)` loop at exactly one trip for the default
map.  The default `RIDGES=true` also makes this the first selected typed key
whose metadata-derived preprocessor map contains a boolean; the schema must
preserve that exact boolean rather than coercing it to an integer.

## Fail-closed typed/emitter/runtime contract

1. Admit exactly these three builtin signatures and no family-wide shorthand:

   ```text
   mod(vec3, float) -> vec3
   mod(vec4, float) -> vec4
   tanh(vec3) -> vec3
   ```

   Reject vector-vector `mod`, vec2 extensions beyond Task 12, scalar changes,
   `tanh(float)`/`tanh(vec2)`/`tanh(vec4)`, `atanh`, other hyperbolic calls,
   mixed vector widths, matrices, arrays, and every unlisted key.
2. Retain the resolved overload and vector width in immutable typed IR; the
   validator checks the arity, input/output types, default define map, source
   span, and key before emission.  The schema may permit a boolean define
   value only when it is the exact `RIDGES: true` entry for this key; it must
   serialize deterministically as the GLSL token `true` and reject false,
   numeric coercion, unknown booleans, and metadata drift.
3. Extend the existing lane-wise `mod` implementation only for `N==3` and
   `N==4` with a scalar divisor.  Each lane calls the established scalar
   `glsl::mod(double,double)` policy and materializes f32 at the current vector
   boundary.  Do not add a vector divisor overload.  Add `glsl::tanh(double)`
   as `f32(std::tanh(value))` and a `Vec3`/`FloatExpr<3>` lane mapper using
   the same automatic-storage helper pattern as `sin`, `sqrt`, and `floor`.
4. Emit direct statically typed helpers only.  The mod/tanh result is an
   automatic `Vec3`/`Vec4`; there is no heap allocation, `std::variant`, map
   lookup, virtual/function-pointer dispatch, stateful PRNG object, or
   neighbor-pixel access.  `PixelFn` remains `noexcept` and allocation-free.
5. Cap this feature at two scalar-divisor vector-mod sites (one vec3 and one
   vec4) and one `tanh(vec3)` site per program; the selected source fits
   exactly.  Reject nested admitted builtins, dynamic divisors used as a loop
   bound/index/LOD, or reuse of a boolean macro as runtime state.

Required positives are frozen canonical curl renders for time, seed, scale,
speed, and intensity in the exact preprocessed `OUTPUT_MODE=3`, `RIDGES=true`
configuration, with focused f32 bit probes around `tanh` saturation and
positive/negative mod lanes.  Unit tests must compare all vec3/vec4 lanes to scalar `mod`, preserve
the divisor-zero behavior of the existing scalar helper, and cover NaN/large
finite `tanh` inputs.  Required negatives reject every excluded overload,
`RIDGES=false`, integer-coerced `RIDGES`, default-map drift, a fourth vector
math call, and an unbounded OCTAVES value.  Compile emitted C++ with warnings
as errors and assert zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 27 | **146** | **148** | **64** |

## Ranked residual map after Task 27

These are independent frontiers, not authorization to generalize curl's
vector overloads or boolean define handling.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop models | blur H/V, `normalize:statsFinal`, `nmReindexReduce`, oilFlatten | Need render-scale validation, texture-size charge, a 512² work policy, or a ceil-derived bound. |
| 3 | Other word/numeric forms | signed bitEffects, vector `round`, general shifts/masks | Need separate two's-complement, shift-count, or vector numeric contracts. |
| 4 | General output/aggregate ABI | Julia, Mandelbrot, Newton; historicPalette, palette | Multi-output copy-out and struct layout/passing exceed a local builtin slice. |
| 5 | UBO/varying stage data | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit | Requires std140 layout or a pinned stage-input representation in `PixelContext`. |
| 6 | Arrays/matrices | global arrays in cellRefract/kaleido/normalMap and mat4 effects | Needs global lifetime/indexing or mat4 algebra beyond local automatic values. |
| 7 | General sampling | nonzero/computed `textureLod`, other sampler types | Requires owned mip storage and pinned filtering policy. |

Task 27 adds one exact default-configuration factory while retaining the
derivative hold and keeping general vector math, loops, interface, array, and
matrix work independently reviewable.
