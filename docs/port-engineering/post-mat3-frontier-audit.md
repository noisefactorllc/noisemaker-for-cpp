# Post-mat3 frontier audit: Task 18 scalar float bits and uint XOR

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after the proposed Task 17
matrix3 slice.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 17 | 124 | 126 | 86 |

Fragment derivatives remain explicitly out of scope until a quad/neighborhood
execution model is designed.  With that boundary held, the best coherent next
slice is **`scalar-float-bits-xor-v1`**: exact IEEE-754 binary32
reinterpretation from `float` to `uint`, plus scalar `uint ^ uint`.

## Exact Task 18 slice

| Program key | Exact default defines | Why it becomes clean |
| --- | --- | --- |
| `classicNoisedeck/caustic:caustic` | `{ "NOISE_TYPE": 10 }` | Uses `floatBitsToUint(seedFrac)` and scalar XOR to seed its existing `uvec3` PRNG path. |
| `classicNoisedeck/moodscape:moodscape` | `{ "COLOR_MODE": 2, "NOISE_TYPE": 10 }` | Task 17 supplies its matrix3/vector-index subset; this task supplies the remaining float-bit seed and scalar XOR. |
| `classicNoisedeck/shapes:shapes` | `{ "LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30 }` | Same scalar float-bit/XOR PRNG seed shape; Task 17 supplies the matrix3/vector-index portion. |
| `filter/scanlineError:scanlineError` | `{}` | Uses scalar `floatBitsToUint` to construct a seed; its vector shift/XOR operations are already in the typed slice. |

The four use the same exact newly admitted AST/type combinations:

```glsl
uint bits = floatBitsToUint(float_value);  // float -> uint only
uint mixed = (bits * uint_literal) ^ uint_literal;  // uint ^ uint only
```

Their `uvec3 >> uint`, `uvec3 ^ uvec3`, and `uvec3 ^= uvec3` expressions are
already covered by the existing uint-vector-bitwise contract.  No Task 18 key
uses scalar signed bitwise operations, scalar shifts, scalar `&`/`|`,
`uintBitsToFloat`, half packing, or a vector overload of `floatBitsToUint`.

Diagnostic replay after the prior projected slices finds no later frontend
blocker for these four at the define maps shown above.  The keys are therefore
the complete Task 18 allowlist, not a general admission of every source that
mentions bit conversion.

## Fail-closed runtime and emitter contract

1. Admit exactly the builtin signature `uint floatBitsToUint(float)`.  Reject
   vector overloads, `uintBitsToFloat`, `intBitsToFloat`, `floatBitsToInt`,
   `packHalf2x16`, and `unpackHalf2x16`.
2. Before reinterpretation, materialize the GLSL operand as binary32.  Emit
   `noisemaker::float_bits_to_uint(noisemaker::f32(value))`, backed by the
   existing `std::bit_cast<std::uint32_t>` implementation.  This is a bit
   reinterpretation, not numeric conversion; preserve zero signs, infinities,
   and NaN payload bits as represented by the materialized `float`.
3. Admit only `uint ^ uint -> uint` in addition to the already-approved vector
   bitwise forms.  Emit operands narrowed to `std::uint32_t` and XOR those
   words directly (or through a scalar `glsl::bitwise_xor` helper).  Do not
   broaden signed integer bitwise rules, scalar shifts, masks, or compound
   scalar bitwise assignment.
4. Restrict this slice to local `uint` temporaries and rvalues; no uniform
   `uint`, array, pointer, reference, global mutable word state, or stateful
   PRNG abstraction.  C++ unsigned wraparound remains defined; no heap or
   per-pixel dynamic allocation is introduced.
5. Keep the allowlist sorted and exact, with each define map validated against
   pinned metadata.  Reject a mismatch rather than silently falling back to a
   shader-source `#ifndef` default.

Required tests should include golden bit patterns for `+0.0`, `-0.0`, one
normal finite value, `+infinity`, and a controlled NaN bit pattern; scalar XOR
with high-bit words; and the four frozen default program oracles.  Negatives
must reject every excluded overload/operator and a numeric cast substituted
for bit reinterpretation.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 18 | **128** | **130** | **82** |

## Ranked residual map

Counts below describe immediately visible primary clusters after the projected
Task 18 boundary; categories overlap downstream and are not a promise that a
single broad feature ports every member.

| Rank | Frontier | Direct-looking keys / scale | Why deferred after Task 18 |
| ---: | --- | --- | --- |
| 1 | Range-proved dynamic `vec3[i]` beyond the Task 17 matrix allowlist | six grade passes: `filter/grade:creative`, `hslSecondary`, `lut`, `primary`, `vignette`, `wheels` | Productive but separate from bit semantics; requires a general lvalue/rvalue vector-index proof and source-const/vector lowering audit. |
| 2 | Derivatives | four otherwise-ready keys: `halftone`, `octaveWarp`, `stamp:stThreshold`, `stipple` | Not safe under the current per-pixel ABI; no quad or neighbor semantics. |
| 3 | Bounded dynamic loops | blur H/V, `normalize:statsFinal`, `tetraColorArray`, `nmReindexReduce`, `zoomBlur` | Bounds derive from render scale, texture size, metadata-only runtime ranges, an excessive 512² charge, or float induction. |
| 4 | Miscellaneous scalar/vector builtins | isolated `all`, `ceil`, `reflect`, `round`, `tanh`; plus later scalar `&`/`|`/shift needs | These have disjoint numerical and emitter contracts; bundling them would be capability sprawl. |
| 5 | Remaining matrix family | five mat3-first residuals and `classicNoisedeck/effects:effects` mat4 | Needs `floatBitsToUint` plus other blockers, dynamic loops, `reflect`, alternate constructors, or mat4/global-array support. |
| 6 | Texture LOD | `filter/parallax:parallax` is representative | Requires an explicit mip-level/sampling contract; `textureLod(...,0)` should not be assumed equivalent without pinning sampling behavior. |
| 7 | ABI features | structs (`synth/julia`, `synth/newton`), `out`/`inout` helper parameters, UBO (`synth/remap`), varyings (`filter/grime`, `filter/texture`) | These change calling convention, binding layout, or stage-interface semantics rather than local expression lowering. |
| 8 | mat4/general arrays | `classicNoisedeck/effects:effects` and classic global-array programs | Requires mutable shared/global data or broader matrix algebra and therefore remains explicitly outside local-stack contracts. |

Examples deliberately excluded from Task 18: `classicNoisedeck/bitEffects` also
needs signed `int` `&`, `|`, `^`, and `<<`; `classicNoisedeck/noise` and
`synth/noise` retain octave-derived loop bounds; `classicNoisedeck/shapeMixer`
still needs `reflect`; `classicNoisedeck/kaleido` retains global mutable arrays;
`filter/grime` has a varying interface; and `filter/median` has independent
semantic/type diagnostics.  This keeps the bit contract small, reviewable,
and semantically exact.
