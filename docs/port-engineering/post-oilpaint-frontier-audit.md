# Post-oil-paint frontier audit: Task 29 scalar signed bitwise core

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after the prepared Tasks 12–28.
Derivative semantics remain unavailable pending a deliberately specified
fragment-neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 28 | 147 | 149 | 63 |

## Recommendation: `signed-int-bitwise-core-v1`

The smallest closed next slice is one texture-free generator, not another
resource-sized loop or macro family:

| Key | Exact default defines | Newly admitted typed forms |
| --- | --- | --- |
| `synth/bitwise:bitwise` | `{}` | `int & int -> int`; `int | int -> int`; `int ^ int -> int`; `~int -> int` |

Task 14 supplies the source-qualified `const float PI`; every remaining
operation, conversion, helper, control-flow branch, and interface is already
within the prepared roadmap.  The default source has no sampler,
`texture`/`texelFetch`/`textureLod`, derivative, loop, array, matrix, UBO,
varying, macro, or non-`in` parameter.

The complete new signed-word incidence is deliberately small and auditable:
four scalar XOR expressions, three scalar AND expressions, one scalar OR
expression, and two scalar complements.  Eight occurrences are in
`bitOp(int a, int b, int op, int m)` (the selected-operation branches plus
the final mask); the other two are the `x`/`y` seed XOR assignments in `main`.
The source never shifts a signed value.  This makes it a materially narrower
entry point than `classicNoisedeck/bitEffects`, which also requires a signed
left-shift contract and a six-define configuration.

## Fail-closed typed/emitter/runtime contract

1. Admit exactly `synth/bitwise:bitwise` with the metadata-verified empty
   default-define map.  Its source-constant `PI` is handled solely by the
   existing Task-14 source-const lowering.  Reject every nonempty define map,
   macro fallback, unlisted key, or attempt to add `classicNoisedeck/bitEffects`
   through this slice.
2. Add four exact scalar signed signatures, and no family shorthand:

   ```text
   bitwise_and(int, int) -> int
   bitwise_or(int, int) -> int
   bitwise_xor(int, int) -> int
   bitwise_not(int) -> int
   ```

   Keep the original GLSL operator spelling plus the resolved signature in
   immutable typed IR, with key provenance and source span.  Accept only the
   ten source sites described above: four `^`, three `&`, one `|`, and two
   unary `~`; require all operands/results to be exactly scalar `int`.
3. Model each signed result as its GLSL 32-bit two's-complement bit pattern.
   Implement the four `noexcept` runtime helpers by bit-casting each
   `std::int32_t` operand to `std::uint32_t`, applying the corresponding
   unsigned C++ operation, then bit-casting the word back to `std::int32_t`.
   This avoids implementation-defined signed-word interpretation and does not
   use a signed overflow, signed shift, `bool`, or a floating numeric cast.
4. The emitter dispatches a typed scalar-`int` bit expression directly to the
   matching helper, including unary complement; it must never render the new
   forms as raw C++ signed operators.  Existing non-bitwise `int` arithmetic
   keeps its established checked wrap helpers.  Do not add compound bitwise
   assignments, `<<`/`>>`, masks as a new language primitive, unsigned or
   vector forms, `ivec`/`uvec`, `intBitsToFloat`, or generic operator
   overloading.
5. Cap the slice at one helper named `bitOp`, four scalar `int` parameters,
   ten admitted signed-word expression sites, and call depth one.  Bitwise
   results may feed the selected helper's local `r`, its final scalar mask,
   the two local coordinate assignments, or scalar conversion already present
   in this key; reject result use as a loop bound, index, array extent, LOD,
   sampler coordinate, pointer, reference, persistent state field, or dynamic
   dispatch selector.
6. Emission has only automatic scalar locals and direct calls.  It introduces
   no allocation, map/variant lookup on the hot path, virtual call, function
   pointer, callback, sampler access, or neighbor-pixel read.  `PixelFn`
   remains `noexcept` and allocation-free.

Required positives are direct word-pattern tests for `0`, `1`, `-1`,
`INT32_MIN`, `INT32_MAX`, and distinct high-bit operands, comparing each
helper against the same unsigned-bitcast reference.  Run frozen default-key
oracles through bitOp operations 0–7 and color modes 0–2, including seed and
offset combinations that make the x/y coordinate values negative, plus time
and speed cases that exercise the existing float-to-int conversion path.

Required negatives reject a float, bool, uint, `ivec*`, or `uvec*` operand;
mixed signed/unsigned operands; vector result; `&=`/`|=`/`^=`; any signed
shift; an unapproved `~` target; an eleventh signed-word site; use in a
loop/index/LOD/ABI field; a macro define; source-constant drift; and every
derivative builtin.  Compile emitted C++ with warnings as errors and assert
zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 29 | **148** | **150** | **62** |

## Ranked residual map after Task 29

These remain independent frontiers; signed scalar bitwise support does not
authorize any of them.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need separately validated render scale, texture-dimension/work policy, or a much larger 512-by-512 budget. |
| 3 | Signed-word extensions | `classicNoisedeck/bitEffects` | Still needs signed left shift and its independently pinned macro configuration; neither is included here. |
| 4 | Interface adapters | focusBlur sampler parameters; multi-pass/output flow | Requires a pinned sampler-argument or pass-chain ABI, not a scalar operator change. |
| 5 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage inputs each need their own representation contract. |
| 6 | Arrays and matrices | global arrays, normalMap, kaleido, mat4 effects | Need global lifetime/indexing or broader matrix algebra beyond local scalar words. |
| 7 | General sampling and macro variants | computed/nonzero `textureLod`; nondefault oil MODE values | Need owned mip/filter semantics or an independently audited preprocessor configuration family. |

Task 29 adds exactly one all-default factory with a fully specified scalar
word representation.  The derivative hold and all broader dynamic-loop,
interface, aggregate, matrix, array, sampling, and macro boundaries remain in
place.
