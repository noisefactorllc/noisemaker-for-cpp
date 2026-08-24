# Post-scalar-bitwise frontier audit: Task 30 default bit-effects profile

## Projected starting point

This is a read-only projection over corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, after prepared Tasks 12–29.
Derivative semantics remain unavailable pending a deliberately specified
fragment-neighborhood/quad ABI.

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 29 | 148 | 150 | 62 |

## Recommendation: `bit-effects-default-profile-v1`

The smallest exact next slice is the default bit-effects generator.  It reuses
the prepared source-constant, float-bit, uint-vector, and Task-29 signed-word
semantics; its sole new emission capability is a key-locked escape for three
GLSL helper names that are C++ alternative-operator keywords.

| Key | Exact default defines | Exact new emitter boundary |
| --- | --- | --- |
| `classicNoisedeck/bitEffects:bitEffects` | `{ "COLOR_SCHEME": 20, "FORMULA": 0, "INTERP": 0, "MASK_COLOR_SCHEME": 1, "MASK_FORMULA": 10, "MODE": 1 }` | signature-identity-based C++ names for `and`, `or`, and `xor` |

The source declares exactly six forbidden C++ helper identifiers: the
`int(int,int)` and `float(float,float)` overloads of each of `and`, `or`, and
`xor`.  Four resolved calls remain after preprocessing at the exact defaults:
`and(int,int)`, `or(int,int)`, `xor(int,int)`, and `xor(float,float)`.
All six declarations still have to receive valid C++ names because the typed
emitter generates every helper definition, including default-dead helpers.

The key has no sampler, texture operation, derivative, loop, array, matrix,
UBO, varying, or `out`/`inout` parameter.  The global constants
`BIT_COUNT=8` and `mask=(1 << BIT_COUNT)-1` are already the Task-14
source-constant form: its range-proved compile-time shift resolves the mask
to the fixed signed 32-bit value 255.  This task does not admit runtime signed
shifts.  Its twelve scalar signed `&`/`|`/`^` sites reuse Task 29's exact
two's-complement word helpers; its float-to-uint bit reinterpretations reuse
Task 18.

## Fail-closed typed/emitter/runtime contract

1. Admit only the named key and only the complete, sorted integer define map
   shown above.  Extend the typed-slice expected default-define table by this
   exact six-entry map while retaining the integer-only define schema.  Reject
   a missing/extra key, changed value, bool/float/string coercion, every
   nondefault configuration, and every other program that uses the same
   spelling or profile shape.
2. Preserve GLSL names and overload identities in immutable typed IR.  At
   C++ emission only, map exactly these six signature IDs to predetermined
   legal identifiers:

   ```text
   and(int,int)       -> bitfx_and_i32
   and(float,float)   -> bitfx_and_f32
   or(int,int)        -> bitfx_or_i32
   or(float,float)    -> bitfx_or_f32
   xor(int,int)       -> bitfx_xor_i32
   xor(float,float)   -> bitfx_xor_f32
   ```

   Use that signature-ID map consistently for prototypes, definitions, and
   calls.  Do not rename a token by text alone, change state/uniform/local
   names, mangle arbitrary GLSL names, or apply the mapping to another key.
3. Allow this profile to consume Task-29 scalar signed `int & int`,
   `int | int`, and `int ^ int` only at its twelve recorded source sites.
   They continue to lower through the existing unsigned-bitcast word helpers;
   do not render raw C++ signed bitwise operations.  No new signed operator,
   unary complement, compound assignment, vector operation, unsigned
   extension, or shift is added by this task.
4. Accept the two constants only through the existing Task-14 checked
   declaration graph.  `BIT_COUNT` must be the literal 8 and `mask` must be
   the exact `(1 << BIT_COUNT)-1` pure constant tree with resolved value 255.
   The emitter materializes their dependency closure as automatic local
   constants in readers; it must not introduce a C++ global/static value or a
   runtime shift.  Reject a different shift count, dynamic operand, mutable
   write, forward reference, or any use of the shift outside this constant
   proof.
5. Cap the identifier escape at three source spellings, six helper
   signatures/definitions, and four emitted resolved calls.  Cap signed-word
   reuse at nine `&`, two `^`, and one `|` scalar-int sites, with no result
   used as a loop bound, index, array extent, LOD, pointer, reference,
   persistent state field, or dispatch table entry.  This prevents the profile
   from becoming a general reserved-name or signed-operator facility.
6. Generated code retains automatic locals and direct statically bound calls.
   It introduces no allocation, variant/map lookup on the hot path, virtual
   dispatch, function pointer, callback, sampler access, or neighbor-pixel
   read.  `PixelFn` remains `noexcept` and allocation-free.

Required positives are a frozen canonical oracle at the exact six defaults,
covering active bit-mask parameters (seed, tiles, complexity, hue range and
rotation) and time/speed values.  Compile the generated C++ with all six
escaped declarations present; emitter tests must assert every prototype,
definition, and the four resolved calls uses the matching `bitfx_*` name, and
that no standalone C++ token `and`, `or`, or `xor` is emitted as an identifier.
Retain Task-14's `BIT_COUNT -> mask == 255` proof and Task-29 word-pattern
tests as dependencies rather than duplicating their runtime policy.

Required negatives reject one or five define values, MODE 0, any nondefault
profile, a fourth reserved spelling, a new overload/signature, text-only
renaming, an identifier collision, an unescaped prototype/definition/call,
signed `<<`/`>>`, a mutable or dynamic `BIT_COUNT`, a runtime use of the
constant shift, a thirteenth signed-word site, vector/unsigned bitwise forms,
and every derivative builtin.  Compile with warnings as errors and assert
zero hot-path allocations and indirect calls.

## Projected counts

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| After Task 30 | **149** | **151** | **61** |

## Ranked residual map after Task 30

These remain independent frontiers; this profile does not authorize general
macro handling, C++ name mangling, or signed-word expansion.

| Rank | Frontier | Visible examples | Why it remains separate |
| ---: | --- | --- | --- |
| 1 | Derivative ABI | halftone, octave warp, stamp threshold, stipple, posterize, mixer distortion | `dFdx`/`dFdy`/`fwidth` require explicit neighborhood, border, and scheduling semantics. |
| 2 | Resource/dynamic loop contracts | blur H/V, `normalize:statsFinal`, `nmReindexReduce` | Need separately validated render scale, texture-dimension/work policy, or a much larger 512-by-512 budget. |
| 3 | Other signed-word forms | nonconstant signed shifts and masks | Need their own shift-count, overflow, and usage contracts; the bit-effects constant shift is already resolved by Task 14. |
| 4 | Interface adapters | focusBlur sampler parameters; multi-pass/output flow | Requires a pinned sampler-argument or pass-chain ABI, not a helper-name escape. |
| 5 | Aggregate and stage interfaces | Julia, Mandelbrot, Newton; historicPalette, palette; remap UBO; grime/texture varyings | Multi-output copy-out, structs, std140, and stage inputs each need their own representation contract. |
| 6 | Arrays and matrices | global arrays, normalMap, kaleido, mat4 effects | Need global lifetime/indexing or broader matrix algebra beyond local word helpers. |
| 7 | General sampling and macro variants | computed/nonzero `textureLod`; nondefault oil MODE values | Need owned mip/filter semantics or an independently audited preprocessor configuration family. |

Task 30 adds exactly one macro-pinned generator with a signature-based C++
identifier escape.  Derivatives and every broader loop, word, interface,
aggregate, array, matrix, sampling, and macro boundary remain held.
