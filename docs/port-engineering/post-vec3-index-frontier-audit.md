# Post-vec3-index frontier audit: Task 21 constrained geometric builtins

## Projected starting point

This read-only projection uses the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6` after proposed Tasks 12–20.
Derivative semantics remain held: the current pixel ABI provides a single
`PixelContext`, not a neighboring-pixel or fragment-quad contract.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 20 | 137 | 139 | 73 |

## Recommendation: `geometric-reflect-refract-v1`

The next coherent fail-closed slice is the exact scalar-and-`vec3` geometric
builtin family already used by the two now-otherwise-covered programs.  It is
not general vector math: it admits only the four signatures below, at two
metadata-locked keys.

| Key | Exact default defines | Newly required calls |
| --- | --- | --- |
| `classicNoisedeck/shapeMixer:shapeMixer` | `{ "LOOP_OFFSET": 10 }` | `reflect(float,float) -> float`; `reflect(vec3,vec3) -> vec3`; `refract(float,float,float) -> float`; `refract(vec3,vec3,float) -> vec3` |
| `filter/lighting:lighting` | `{}` | `reflect(vec3,vec3) -> vec3` |

`shapeMixer` already depends on the earlier projected matrix3 constants,
Task-18 scalar `floatBitsToUint`/uint XOR, Task-15 counted `i=0..<3` loop,
and Task-20 range-proved `vec3[i]`.  Its two overloaded `blend` helpers need
both reflection and refraction: admitting reflection alone would still leave
the scalar and vector `refract` calls rejected.  `lighting`'s local Sobel
arrays and `i=0..<9` loop are within Task 16 and Task 15, leaving its one
`vec3` reflection call as the geometric frontier.  The third corpus user,
`mixer/distortion:distortion`, remains excluded because it also uses `dFdx`
and `dFdy` under a runtime `antialias` branch.

The existing runtime already contains allocation-free vector implementations
of the GLSL formulas; the work is checked typed admission/emission plus the
scalar counterpart needed by `shapeMixer`.  No texture, LOD, array, matrix,
parameter-direction, UBO, varying, or derivative semantics are expanded.

## Fail-closed typed and runtime contract

1. Add exact builtin-overload tags, not a generic `reflect` or `refract`
   capability.  Accept only:

   ```text
   reflect(float, float) -> float
   reflect(vec3, vec3) -> vec3
   refract(float, float, float) -> float
   refract(vec3, vec3, float) -> vec3
   ```

   Reject `vec2`, `vec4`, mixed widths, integers/booleans, matrices, arrays,
   samplers, structs, all implicit conversions, and every other geometric
   builtin (`faceforward`, `cross` expansion, etc.).
2. Keep the builtin expression's resolved overload tag and materialized input
   type in immutable typed IR.  The validator checks the tag, operand types,
   output type, arity, key, and exact default define map before emission.
   A source token named `reflect` or `refract` is never sufficient authority.
3. Emit the existing `glsl::reflect` / `glsl::refract` vector helper only for
   the admitted `vec3` calls.  It materializes `FloatExpr<3>` operands into
   automatic `Vec3` values, uses the established double-intermediate/f32-lane
   policy, and has no allocation or dynamic dispatch.  For the scalar forms,
   add direct `noexcept` helpers accepting the generated scalar representation
   (`double`) and returning one f32-consumed scalar:

   ```text
   reflect(I, N) = f32(I - 2 * N * I * N)
   k = 1 - eta*eta*(1 - N*I*N*I)
   refract(I, N, eta) = k < 0 ? 0.0f : f32(eta*I - (eta*N*I + sqrt(k))*N)
   ```

   The scalar helpers must first follow the same operand-consumption boundary
   used by existing scalar builtins; `k < 0` returns exactly positive f32 zero,
   matching the GLSL total-internal-reflection branch.  Do not simulate a
   scalar call by allocating a one-lane vector.
4. Retain `PixelFn noexcept`.  Each call is a fixed number of automatic scalar
   or three-lane temporaries; no heap allocation, `std::function`, virtual
   dispatch, binding lookup, string lookup, or mutable shared state is
   introduced in the pixel body.  The one-time factory continues to bind its
   ordinary typed state before rendering.
5. Cap this feature at four admitted geometric call sites per function and
   eight per program, with no nested geometric call argument and no geometric
   result stored in state/array/global memory.  Both selected programs fit;
   unknown or excessive forms fail before C++ generation.

Required positives are frozen canonical renders for the two precise
key/define maps, all `shapeMixer` blend modes 7 and 8 in both its scalar and
RGB paths, and `lighting` reflection with non-axis-aligned normal/incident
vectors.  Unit tests must cover the vector formula, scalar formula, and
refraction's `k < 0`, `k == 0`, and `k > 0` regimes, including f32 bit probes
at the result boundary.  Required negatives reject each wrong width/type,
mixed operands, missing eta, `faceforward`, generic vector admission, a
runtime define mismatch, and `mixer/distortion` without a derivative ABI.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 21 | **139** | **141** | **71** |

## Ranked residual map after Task 21

The following are independent frontier decisions, not a request to combine
them into the geometric-builtin implementation.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Dynamic-loop runtime contracts | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur`, `oilFlatten` | Each needs a distinct bound proof: validated render-scale, texture-size charge, metadata-backed range, a 512² budget, or non-integral induction. |
| 2 | Derivative ABI | halftone, octave warp, stamp threshold, stipple; `mixer/distortion` | `dFdx`/`dFdy`/`fwidth` require a specified neighbor/quad evaluation and border policy; a local substitute is not GLSL-compatible. |
| 3 | Remaining scalar/vector math | `synth/curl:curl` (`tanh(vec3)` plus `mod(vec3,float)`/`mod(vec4,float)`), signed bitwise `bitEffects` | These are different overload and integer-semantics contracts from reflect/refract. |
| 4 | Parameter direction ABI | `filter/watercolor:wcSimplify` (`inout vec3`); fractal helpers in julia/mandelbrot/newton (`out`) | Needs alias-safe C++ reference/result lowering and GLSL argument-evaluation rules. |
| 5 | Structs | `filter/historicPalette`, `filter/palette`, `synth/julia`, `synth/newton` | Needs typed aggregate layout, initialization, passing, and field-access contracts, often alongside other blockers. |
| 6 | UBO and varying ABI | `synth/remap:remap`; `grime`, `texture`, `spookyTicker`, `wobble`, `wormhole:deposit` | Requires std140 binding layout or explicit stage-input ownership in `PixelContext`. |
| 7 | Arrays/general indexing and matrices | global arrays in cellRefract/kaleido; `classicNoisedeck/effects:effects` mat4 | Local fixed arrays and `vec3` lanes do not establish global array lifetime, arbitrary indexing, mat4 algebra, or mutable-state isolation. |
| 8 | General sampling/geometric expansion | nonzero/computed `textureLod`, other sampler kinds, vec2/vec4 geometric calls | Needs a mip/filter policy or another separately reviewed overload set. |

Task 21 thus adds two complete default-configuration factories while retaining
the derivative hold and avoiding an interface or dynamic-loop expansion.
