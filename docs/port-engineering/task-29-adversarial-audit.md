# Task 29 adversarial audit: Focus Blur borrowed sampler ABI

## Verdict

**Implementation-ready with a narrow exact profile; no hidden runtime or
emitter blocker was found.** The admissible change is only
`mixer/focusBlur:focusBlur`, with its two exact `in sampler2D` parameters on
`applyFocusBlur#16` emitted as `const Surface&`. This is an emitter ABI profile,
not generic `sampler2D` type support.

The existing future projection was compiled again as C++20 with
`-Wall -Wextra -Werror` at `-O0` and `-O2`. The present validator accepts the
program unchanged; the present emitter stops only at
`unsupported typed type sampler2D`. Temporarily mapping that type to
`const Surface&` proves that current identifier, call, texture, textureSize,
state, binder, and runtime paths need no additional representation.

The frozen identity remains raw SHA-256
`dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1`,
normalized SHA-256
`8b3cfb07882d0e409f617b2f86b02fa54cd36db213a60881370306306306be9f`,
function tuple SHA-256
`95428219c60cd14910f90e572857773e22818bfaf17436f6a249a10b4364c6e3`,
whole-program SHA-256
`96468ba160d253f7d064c2caccd9db686d772a2af94d13ee836996dc488e037b`,
interface SHA-256
`3158dcf83a1d13f84a2d8f3d374d464230ff24b1ed812603cc02fbc96e56be96`,
and exact empty defines. Focus Blur is still absent from the accepted
post-Task-28 typed slice.

## Narrowest safe C++ representation

| Candidate | Finding |
| --- | --- |
| `const Surface&` | **Select.** Non-null by construction, no ownership transfer or copy, accepts two references to the same object, and matches all current sampling helpers. Exact emitted call arguments are direct `*state.tex` / `*state.inputTex` lvalues. |
| `const Surface*` | Reject. It adds an unnecessary nullable state to every helper call and requires dereference policy inside the helper. It does not improve lifetime safety because state already owns non-owning setup pointers. |
| `std::reference_wrapper<const Surface>` or a new sampler wrapper | Reject. It creates a new runtime/ABI type and copying/conversion surface with no semantic benefit for this one synchronous helper. It risks accidentally becoming ambient sampler-value support. |
| `Surface` by value | Reject. It copies pixel storage, destroys resource identity/alias semantics, can allocate/throw, and materially changes cost. |
| `Surface&` | Reject. It grants mutation absent from the source and makes the same-surface case a mutable-alias problem. |

The C++ reference is a synchronous borrow only. It must not be stored, returned,
captured, placed in state, wrapped, converted to a pointer, or used after the
call. The existing `State` continues to contain exactly two setup-owned
`const Surface*` fields. The caller must keep both `Surface` objects alive,
at stable addresses, and unmodified for the lifetime/use of the `BoundKernel`.
Destroying `Bindings` after binding is safe if the surfaces remain alive;
destroying or moving a surface is not. Concurrent external mutation remains a
data race just as it is for every existing bound texture and is not broadened
by this task.

Although frontend `in` parameters are recorded with `writable=True` because
GLSL permits assignment to the local parameter variable, the frozen helper
contains no write to either sampler symbol. The profile must require the exact
canonical symbol records and independently prove the no-write/no-escape use
census; it must not forge `writable=False` in the IR.

## Exact ownership, alias, order, and call ABI

The only admitted helper is normalized signature 16:

```text
vec4 applyFocusBlur(in sampler2D sceneTex,
                    in sampler2D depthTex,
                    in vec2 uv)
```

Its exact parameter records are `(13,sceneTex,sampler2D,parameter,in)`,
`(14,depthTex,sampler2D,parameter,in)`, and
`(15,uv,vec2,parameter,in)`. Recursive expression census finds exactly two
references to symbol 13, two to symbol 14, and one to symbol 15. The sampler
references are solely the sampler operands of one `texture` and one nested
`textureSize` each. Neither sampler is an lvalue target, return value, call
result, aggregate member, local/global declaration, or argument to another
user helper.

`main#19` has exactly four references to uniform `inputTex#1` and four to
uniform `tex#2`. Two exact, mutually exclusive call objects own the resource
permutations:

```text
57:17-57:50  applyFocusBlur(tex#2, inputTex#1, uv#33)
59:17-59:50  applyFocusBlur(inputTex#1, tex#2, uv#33)
```

The remaining two references per uniform are its alpha `texture` and nested
`textureSize` use. There is no dynamic resource lookup in pixel execution.
The existing `State` declaration/binding order is `inputTex`, then `tex`, then
the seven value uniforms. The helper's semantic order is instead `sceneTex`,
then `depthTex`; mapping by ordinal or alphabetic resource order would be a
bug. Authenticate the two parameter objects, both complete call objects, their
complete expression/statement ancestry, exact candidate-owned predicate/if,
then/else branch objects and slots, and exact argument symbol IDs. The C++ order-of-evaluation
rule is harmless only because the admitted arguments are pure dereferenced
lvalues with no mutation.

The same-surface case is valid: both state pointers may have identical values
and both helper references may alias because they are const and reads are
synchronous. It must not be “fixed” by rejecting equal addresses or copying a
surface. `run_pass` creates a fresh output surface, so input/output storage
aliasing is not part of this task; a future caller-supplied destination API
would need a separate snapshot/alias contract.

## Actual resource cost and loop proof

There is one counted loop, `i = 0; i < 64; i++`. Its authenticated start is 0,
exclusive bound is 64, unit update gives exactly 64 trips, lexical/effective
depth is 1, lexical product and entrypoint charge are 64, and the call graph is
acyclic. There is no `break`, `continue`, return, nested loop, recursion, or
second helper call on a selected path. `depthSource == 0` and the `else` are
exclusive.

Maximum texture samples on either pixel path are therefore exactly:

```text
1  depth texture() before the loop
64 scene texture(), one per loop trip
2  alpha texture() in main
--
67 total texture reads per pixel
```

There are also 67 `textureSize` evaluations (one depth, 64 scene, two alpha),
but those query dimensions and are not texel reads. The diagnostic `-O2`
object keeps `applyFocusBlur` as a direct function with a 144-byte ARM64 stack
frame and `pixel` with 112 bytes; no heap operation, exception path, indirect
resource call, or dynamic stack allocation appears. Production stack and
disassembly still need to be measured after canonical regeneration rather
than inheriting these diagnostic figures.

## Hidden-emitter audit

The existing emitter already has every downstream operation needed:

- `name()` maps function parameters through `locals`, so sampler parameters
  emit as `sceneTex` / `depthTex`; it maps sampler uniforms to dereferenced
  `*state.<name>` expressions.
- `texture` and `textureSize` already accept the resulting `const Surface&`.
- helper declarations and definitions already share
  `function_parameter_type()`, which is the narrow insertion point.
- state construction and `Bindings::texture()` already capture the exact
  setup-owned surface addresses; `BoundKernel` owns state, not textures.

The implementation must add an exact carrier and authentication path to both
validator and emitter. It must **not** add `sampler2D` to `_TYPES` or make
`function_type()` generic, because that would silently admit sampler returns,
locals, arbitrary helpers, and future programs. `function_parameter_type()`
should return `const Surface&` only when the function, ordinal, parameter
object, and authenticated profile site all match. Both the forward declaration
and definition must use it. The emitter must count both authorized parameters
and both authorized calls as actually consumed, then reject missing,
duplicated, or foreign authenticated objects at render completion.

`ResourceRequirements` records uniform samplers but not helper-parameter use
roles, so resource metadata alone cannot prove this ABI. A recursive profile
census and exact object authentication are mandatory. Whole-program hashes are
useful locks but are not substitutes for these independently tested facts.

## Required fail-closed tests

### Structural/profile mutations

Use exhaustive one-axis `dataclasses.replace` mutations, verify every mutation
precondition, and require rejection independently by profile, validator, and
emitter. At minimum cover:

- key, raw/normalized source, define name/value/count/order, body status,
  whole/function/interface identity, resource uniform/sampler/output order and
  counts, texture/derivative flags, loop count/unproved/depth/product/charge,
  and call-graph cycle;
- helper/function count/order/IDs/names/spans/return type/body, parameter
  count/order/ID/name/type/storage/direction/writable/span, sampler changed to
  scalar/vector/array, third sampler, sampler return, sampler local/global,
  and sampler inside an aggregate;
- each of the four helper sampler identifier objects: symbol object/ID/name,
  owner, span, category, callee, argument ordinal/type, texture/textureSize
  arity, added LOD/derivative, duplicate/missing use, assignment, pre/post
  update, return, secondary user call, capture/retention, pointer/wrapper
  conversion, and use after the call;
- both `main` call objects and complete ancestry: call count, signature ID,
  span, order, branch ownership/predicate, argument count, argument symbol IDs,
  swapped pair, duplicate `inputTex`, duplicate `tex`, local/conditional/call
  expression argument, predicate replacement/equal reconstruction with an old
  object, branch swap, call outside, call copied into either branch or an
  always-executed location, both calls executed, call-slot swap, or removal;
- foreign key with copied carrier, absent/foreign carrier, wrong caller hash,
  wrong numeric contract, nonempty defines, and coexistence with every other
  exact profile carrier.

Reconstruct an equal-but-not-identical IR and require the authenticator to
return objects owned by that reconstruction. Mock validator/emitter
authentication independently so neither can trust the other's result.

### Generated C++ shape and ABI

Assert exact code shape, not just successful compilation or matching pixels:

- exactly two `const Surface&` sampler parameters in the declaration and two
  in the definition of only `applyFocusBlur`;
- exact calls in both orders using `*state.tex` and `*state.inputTex`;
- state fields remain two `const Surface*`; binding takes exact named resources
  in `inputTex`, `tex` order;
- absence of `Surface` by value, non-const reference, pointer helper parameter,
  `reference_wrapper`, `span`, `shared_ptr<Surface>`, copies, heap calls,
  null checks, dynamic lookup, casts that remove const, retention, and sampler
  return/local/global declarations;
- compile with C++20 warnings-as-errors, then inspect demangled symbols and
  disassembly for reference ABI, one direct helper call site selected by the
  branch, no indirect call/allocation/exception/dynamic stack, and bounded
  Debug/Release/sanitizer frames.

Add a lifetime test that creates both surfaces outside an inner `Bindings`
scope, binds the kernel inside it, destroys `Bindings`, and successfully runs
the kernel afterward under ASan/UBSan. Do not test an expired or moved surface;
that would deliberately invoke undefined behavior rather than validate the
contract.

### Non-vacuous pixel and mutation coverage

Retain all six frozen canonical cases and require dimensions, finite counts,
full F32 hash, RGBA8 hash, probes, and repeat identity. The paired asymmetric
cases already distinguish the two call permutations; the same-surface case
proves permitted aliasing; minima/maxima and tiled geometry cover the numeric
and coordinate extremes.

Every test-only mutation mode must alter a verified code/IR coordinate and
publish a distinct candidate hash or structural counter before its expected
pixel relation is checked. Specifically:

| Mutation | Required relation |
| --- | --- |
| Force both branches to `(tex,inputTex,uv)` | depth-source 0 matches; depth-source 1 diverges on F32 hash and at least one probe. |
| Force both branches to `(inputTex,tex,uv)` | depth-source 1 matches; depth-source 0 diverges. |
| Swap only one call's sampler arguments | The corresponding asymmetric branch diverges; the other branch remains unchanged. |
| Use `depthTex` for the 64 scene reads | All non-alias asymmetric cases designated by the fixture diverge; alias case matches. |
| Use `sceneTex` for the depth read | A designated asymmetric case diverges; exact unaffected controls are enumerated. |
| Drop/duplicate one loop sample or change 64 to 63/65 | Designated cases diverge and the structural read/trip counter changes. |
| Remove either alpha read or use one source twice | Asymmetric-alpha cases diverge in alpha probes; RGB controls remain exact where specified. |
| Same object bound to both names | Both branch orders remain bit-identical to the frozen alias oracle and sanitizers remain clean. |

ABI-negative modes such as by-value, pointer, wrapper, writable reference, or
retention may be pixel-identical; they therefore pass only when their own
structural rejection/shape assertion fires. They must never fall through to a
baseline renderer and be counted as successful “mutations.” Require a handled
mode enum/switch with no default, one execution counter per declared mode,
pairwise-distinct semantic signatures excluding IDs/names/acceptance/results,
and a final assertion that declared modes equal handled modes equal observed
modes. By-value must allocate, own, and read independent Surface copies; all
identity/ownership/null/write/read witnesses are execution-derived. Freeze
switch/witness source hashes and reject invalid enum values.

## Evidence checked

- Corpus source lines 36-70 (raw) / normalized helper 29-46 and main 48-66.
- Current typed AST: exact parameter records, four/four uniform reference
  census, two/two helper sampler reference census, two exact call objects.
- `tools/glslcpp/emit_typed_cpp.py`: `function_parameter_type`, `name`, call,
  texture/textureSize, state, and binder paths.
- `include/noisemaker/glsl_runtime.hpp`, `src/glsl_runtime.cpp`,
  `include/noisemaker/kernel.hpp`, and `src/pass_runner.cpp`: non-owning texture
  lifetime, immutable kernel state, output separation, and pixel scheduling.
- Future projection SHA-256
  `26fe46738b1591c443f6a3f05fea5150b1d2f7e1341fa3ab7d3f3e578caefcca`
  compiled at `-O0` and `-O2` with warnings-as-errors.
- Frozen six-case oracle SHA-256
  `44595fc5d8f98f44587c95137136c5d10993d427ba7e7e88e353f2bcffc11f74`;
  generator SHA-256
  `9c1a4acffaa1bef021953aa3df0313b8fbe7fb88aea635237e4131dce4c39897`.

No repository file or Git state was changed by this audit.
