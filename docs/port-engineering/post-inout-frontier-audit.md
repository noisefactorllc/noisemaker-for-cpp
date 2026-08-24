# Post-inout frontier audit: Task 23 key-locked scalar `round`

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after proposed Tasks 12–22.
Derivative semantics remain deliberately unavailable without a fragment
neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 22 | 140 | 142 | 70 |

## Recommendation: `round-float-key-extension-v1`

The next coherent fail-closed slice extends the already-defined Task-19 scalar
`round(float) -> float` rule to two exact default-key programs.  It adds no
runtime primitive and does not turn `round` into an unrestricted builtin.

| Key | Exact default defines | New admitted use |
| --- | --- | --- |
| `filter/fxaa:fxaa` | `{}` | scalar `round` consumed by `uint(max(round(value),0.0))` and `int(round(channel_value))` |
| `filter/snow:snow` | `{}` | scalar `round` consumed by `uint(max(round(value),0.0))` |

Both programs already fit the prior projection: Task 14 supplies their
read-only source constants, and Task 13 supplies level-zero `texelFetch`.
Their scalar control flow, conversions, unsigned arithmetic, vector math, and
ordinary helper calls are already covered.  The newly admitted `round` calls
are scalar only and produce a scalar float before existing conversion rules
consume the result.

The other `round` users are deliberately outside this two-key extension:

| Deferred key | Remaining independent blocker |
| --- | --- |
| `filter/grain:grain` | `uvec3 >> uvec3`, whereas the prior uint vector-shift contract accepts only a scalar `uint` shift amount |
| `filter/posterize:posterize` | `fwidth`, hence the held derivative ABI |
| `filter/normalMap:normalMap` | global fixed arrays and indexing |
| `synth/testPattern:testPattern` | `round(vec2)`, arrays/indexing, and a dynamic bound |

`filter/pixelSort:gatherSorted` remains the Task-19 scalar-round key.  No
vector `round`, integer overload, `roundEven`, or unrelated intrinsic is
added here.

## Fail-closed typed/emitter/runtime contract

1. Keep one exact overload: `round(float) -> float`.  The typed node must
   retain its resolved scalar overload, span, and key provenance.  Reject
   `round(vec2/vec3/vec4)`, `roundEven`, integer/boolean/matrix/array inputs,
   arity drift, or a conversion substituted for the builtin.
2. Extend the scalar-round key allowlist only with the two entries above,
   each with a sorted metadata-verified empty define map.  The Task-19
   `gatherSorted` entry remains separately pinned.  A program with the same
   AST signature but an unlisted key or define map fails validation before
   emission.
3. Reuse the existing `glsl::round(double) noexcept` helper, whose numeric
   policy is the existing GLSL-compatible `floor(x + 0.5)` result.  Preserve
   the established scalar float consumption boundary: materialize the result
   as f32 exactly where the typed expression is consumed by constructor,
   conversion, uniform/state, vector, or output logic.  Do not add a custom
   host-library rounding path or make host tie behavior observable.
4. Emit a direct statically typed call in the generated helper/body.  It
   uses no allocation, state, virtual dispatch, function pointer, variant,
   binding lookup, texture policy change, or neighbor-pixel read.  `PixelFn`
   remains `noexcept` and allocation-free.
5. Cap this extension at two scalar-round call sites per helper and four per
   program; `fxaa` has two and `snow` one.  Reject a nested round argument or
   a round result used as a dynamic index, loop bound, LOD, array extent, or
   ABI field.  Those forms require their own proof contracts.

Required positives are frozen canonical renders for the two keys, including
FXAA threshold/early-return and blend paths, snow alpha-zero/active and
pause/time paths, and scalar values on both sides of each half boundary.
Direct numerical tests must cover negative inputs, signed zero, normal
fractional values, and the f32 conversion boundary into `int`/`uint`.
Required negatives reject vector and integer rounds, a nonempty/incorrect
define map, a third call site, `round` as an unproved loop/index/LOD input,
and the four deferred-key shapes above.  Compile emitted C++ with warnings as
errors and verify the hot-path allocation and indirect-dispatch counters stay
zero.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 23 | **142** | **144** | **68** |

## Ranked residual map after Task 23

These are separate capability decisions; none is implied by extending a
key-locked scalar builtin.

| Rank | Frontier | Visible examples | Why it stays separate |
| ---: | --- | --- | --- |
| 1 | Dynamic-loop/resource contracts | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur`, `oilFlatten` | Requires exact render-scale, texture-size, metadata-range, work-charge, or non-integral-loop proof. |
| 2 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` need quad/neighborhood, border, and execution-order semantics. |
| 3 | Remaining numeric/bit/vector overloads | grain `uvec3 >> uvec3`; curl `tanh(vec3)` plus wider `mod`; signed bitwise bitEffects; vector `round` | Each has a separate overload, wrap/shift, or vector numeric contract. |
| 4 | General `out` ABI and structs | Julia, Mandelbrot, Newton; historicPalette, palette | Needs multi-result copy-out or aggregate layout/passing rules beyond Task 22's two nonalias local references. |
| 5 | UBO/varying data ABI | remap UBO; grime, texture, spookyTicker, wobble, wormhole deposit | Requires std140 layout or a pinned stage-input representation in `PixelContext`. |
| 6 | Arrays/matrices | global arrays in cellRefract/kaleido, normalMap; mat4 effects | Local fixed arrays and local vector lanes do not provide global lifetime, arbitrary indexing, or mat4 algebra. |
| 7 | General sampling | nonzero/computed `textureLod`, other sampler types | Requires owned mip storage and pinned level/filter policy. |

Task 23 therefore consumes two ready scalar-round passes without relaxing the
derivative hold or merging interface, dynamic-loop, array, matrix, or vector
numeric work into an intrinsic allowlist extension.
