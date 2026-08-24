# Task 27 Perlin Scalar Uint XOR Implementation Design

## Status and authority

**IMPLEMENTATION READY.** This design adds only
`synth/perlin:perlin` under `perlin-scalar-uint-xor-v1`. It authorizes no Git,
publication, deployment, branch, worktree, or pull request operation.

Frozen authorities:

| Artifact | SHA-256 |
| --- | --- |
| `task-27-frontier-audit.md` | `da7ea68d62f05dc0710ab2aa2f0c825614625d1155f1aafdb4cbf5f6fdc07d8d` |
| `task-27-recomputed.json` | `5273b52fe99259f7be1bc1e66513fb3d6731dc240873884c35780bedea3b5231` |
| `task-27-oracle-generator.mjs` | `95e9c5da0d0284f33ffcd0579c014ef29a7761785fed30d4047a75a1107dfd1e` |
| `task-27-oracles.json` | `27e12edfdec79a9f1ad9c07d3d076da2553e36f63d8c9a5ac43c1bc1592bcc54` |
| `task-27-oracle-report.md` | `9686b2107312f327ce898d438fe849b7bc7298158885d252210e76a72a3721b2` |

The complete source/tree/profile contract is in `task-27-brief.md`. Any
source, typed-tree, public factory, define, count, order, oracle, or accepted
Task 26 drift is a hard stop requiring a refreshed package.

## Scope and non-goals

Implement one identity profile that authenticates exactly the outer and inner
scalar `uint ^ uint` nodes in `hash3` and permits validator/emitter handling of
only those two object identities. Emit direct C++20 `std::uint32_t` XOR.

Do not change:

- parser, typed IR, semantic analyzer, corpus, metadata defaults, or defines;
- the approved type/operator/capability vocabulary;
- runtime headers/sources, `glsl::bitwise_xor`, vector shifts/XOR, numeric
  helpers, binding ABI, CMake, or compiler flags;
- existing compatibility/custom-comparer/Gather/literal-Vec3/Smooth profiles;
- source-global, loop, array, matrix, sampler, derivative, varying, or adapter
  support;
- the `DIMENSIONS=2` default or add a `DIMENSIONS=3` row/profile;
- any existing program's semantics or public catalog entry.

## Baseline and projected catalog gate

Implementation start must reproduce:

```text
corpus                    212
typed                     126
public                    128
unported                   84
typed SHA   01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76
public SHA  d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3
```

After adding only Perlin:

```text
typed                     127
public                    129
unported                   83
Perlin typed position     123
typed SHA   ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72
public SHA  37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883
```

Tests compare explicit ordered lists and neighbors, not digests alone.

## New exact profile module

Add `tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py` with only:

```python
PROFILE = "perlin-scalar-uint-xor-v1"
PERLIN_KEY = "synth/perlin:perlin"

def authenticate_perlin_scalar_uint_xor(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[TypedExpression, TypedExpression]:
    """Return the exact outer and inner scalar XOR objects."""

def apply_perlin_scalar_uint_xor(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> TypedProgram:
    authenticate_perlin_scalar_uint_xor(program, source_hash, profile)
    return program
```

The authenticator independently verifies every frozen brief identity:

- exact profile, key, caller source hash, 10,882 raw bytes/hash, 4,875
  normalized bytes/hash, and exact one-item `DIMENSIONS=2` define tuple;
- `body_status == "analyzed"`, all unrelated optional proof carriers absent,
  exact 17 declarations/resources/interface, 13-function tuple, whole-program
  and interface fingerprints;
- exact `hash3` signature 49, parameter, eleven statements/body hash, return
  statement and float-constructor parent;
- exact outer/inner paths, spans, hashes, kinds, `^` operators, rvalue
  categories, `uint` results, two `uint` operands, operand swizzle hashes and
  order, and parent child-role 0 at each level;
- exactly two scalar `^` nodes program-wide, no scalar signed/mixed site, and
  unchanged existing vector compound-XOR/shift nodes;
- independently recomputed call graph, exact reachable IDs
  `(45,46,48,50,51,52,53,54,55,56)`, exact unreachable IDs `(47,49,57)`,
  exactly three `grad3 -> hash3` static calls, no reachable call to 49, and
  exact loop proof 2/0/1/8/28/acyclic;
- frozen profile tuple SHA-256
  `bc712abd28da325cb3f3d162a6b542b9c28a7491564c44a90a6b090af39c0cbf`.

It returns the exact visited expression objects. Dataclass-equal reconstructed
programs are allowed only if their values independently match every frozen
identity; caller object lineage is not authority. `apply` is an identity
transform and must return the same `TypedProgram` object.

No registry, proof dataclass, IR field, hash-prefix match, global site map, or
generic scalar authorization is added.

## Slice schema, loader, and ordering

Add exactly one sorted row:

```json
{
  "defines": {"DIMENSIONS": 2},
  "perlin_scalar_uint_xor_profile": "perlin-scalar-uint-xor-v1",
  "program_key": "synth/perlin:perlin"
}
```

Extend only the per-program row schema with optional
`perlin_scalar_uint_xor_profile`. Require exactly one such carrier; exact key,
profile string, and define map; no carrier on another key; no Perlin row
without it; no second carrier; and no coexistence with compatibility,
custom-comparer, Gather, literal-Vec3, or Smooth carriers.

Keep all top-level schema arrays/maps byte-semantically unchanged. Do not add
`^` or a scalar-bitwise capability: `^` is already in the syntax vocabulary,
and the exact site profile supplies the missing authorization.

The generated manifest adds
`"perlin_scalar_uint_xor_profile": "perlin-scalar-uint-xor-v1"` only on the
Perlin row. The public header adds only
`bind_synth_perlin_perlin(const glsl::Bindings&)`. Public catalog count becomes
129 only because the 127 typed entries join the two existing manual entries.

## Pipeline order

For each selected program preserve the current order, appending Perlin's
identity step after Smooth:

1. parse/analyze exact source and metadata default defines;
2. existing compatibility transform;
3. existing Lens pre-authentication;
4. existing fixed-array/fixed-affine proof attachment;
5. existing Gather identity handling;
6. existing literal-Vec3 transform;
7. existing Smooth identity handling;
8. Perlin identity authentication using its row carrier;
9. independent capability-validator authentication;
10. independent emitter authentication;
11. render and record manifest metadata.

Require `profiled is typed` at step 8. Perlin must remain disjoint from every
other program/profile and must not rely on validator success as emitter proof.

## Validator implementation

Add keyword-only `perlin_scalar_uint_xor_profile: str | None = None` to
`validate_capabilities`. At initialization:

- if present, require exact Perlin key, `glsl-f32`, no compatibility or other
  per-program carrier, exact `DIMENSIONS=2`, exact caller source hash, and
  successful profile authentication;
- retain a tuple/set of the exact outer and inner returned objects;
- if the exact Perlin tree has no carrier, reject before it can pass through
  any generic path;
- if a foreign tree has the carrier, reject even if it contains similar XOR.

In binary-expression validation, handle an object-identity match before the
existing vector-XOR type rule. Reverify binary `^`, two children, and exact
`uint/uint -> uint`; then accept only that object. Every other scalar `^`
continues to fail. The existing vector branch and capability accounting remain
unchanged. Do not add a new approved capability or interpret
`uint-vector-bitwise` as generic scalar authority.

At validation completion, require that traversal visited both authenticated
objects exactly once and no extra scalar XOR. This catches a carrier that is
valid at initialization but bypassed or duplicated later.

Mandatory carrier matrix:

| Tree | Carrier | Result |
| --- | --- | --- |
| exact Perlin | absent | reject |
| exact Perlin | exact | accept unchanged |
| exact Perlin | foreign | reject |
| foreign/mutated | exact | reject |
| foreign/mutated | absent | retain prior result, never gain scalar XOR |

## Emitter implementation and code shape

Add the same keyword-only argument to `render_typed_cpp` and `_Emitter`. In
`_Emitter.__post_init__`, independently authenticate and store the exact outer
and inner objects, with the same metadata exclusivity and mandatory-carrier
rules as the validator.

In `_Emitter.expression`, before the existing vector-XOR lowering:

```python
if value is one of the two authenticated Perlin scalar sites:
    require exact '^' and uint/uint -> uint
    return f"({expression(left)} ^ {expression(right)})"
```

Do not call `glsl::bitwise_xor`; do not add a scalar overload/helper; do not
rewrite the AST; do not flatten/reassociate. The final generator-native line
must be equivalent to:

```cpp
return (static_cast<double>(float(((glsl::swizzle<0>(q) ^
    glsl::swizzle<1>(q)) ^ glsl::swizzle<2>(q)))) /
    static_cast<double>(static_cast<float>(4294967295.0)));
```

Code-shape assertions must prove exactly two direct scalar XOR tokens in the
`hash3` return, left nesting and exact operands, no scalar bitwise helper call,
unchanged vector `glsl::bitwise_xor` use, unchanged float boundary/denominator,
and zero scalar XOR in every historical generated block.

Emitter completion requires both authenticated objects were emitted exactly
once. Direct calls to emitter with valid validator history but missing/foreign
emitter carrier must still reject.

## Generated isolation

Generation must produce one new typed program block and binder, one manifest
row, one header declaration, and one catalog row. Because insertion at ordinal
123 renumbers later `typed_N` namespaces, isolation tests must extract blocks
by program-key comments and canonicalize only the generated namespace ordinal
and common monolithic output hash. After that normalization:

- all 126 historical program blocks are byte-identical;
- all 126 historical manifest rows are semantically identical;
- all historical binder names and catalog key/factory mappings are identical;
- only Perlin owns the new carrier field;
- no generated historical block gains direct scalar XOR;
- no runtime/header/CMake/parser/IR/corpus file changes.

Generator `--check` must pass immediately after canonical regeneration.

## Native public render parity

Transcribe all eight oracle cases exactly into `tests/test_generated_kernels.cpp`:

1. mono default shape;
2. RGB four octaves;
3. ridged six octaves;
4. one domain-warp iteration;
5. four domain warps plus ridges;
6. nonzero tile offset/larger full resolution;
7. speed-zero/nonzero-time control;
8. full-resolution fallback.

Bind all fourteen native uniforms with exact types. `DIMENSIONS` is a compile-
time row define and is not a native runtime binding. For every case assert:

- exact width and height before any hash comparison;
- repeat-identical full F32 bytes;
- exact full F32 SHA-256, full RGBA8 SHA-256, and all five frozen probes;
- finite lane count equals `width * height * 4`;
- alpha behavior and case-specific controls;
- no texture dependency.

The public factory object is direct canonical/no-adapter in the JS oracle. The
native catalog must contain exactly one `synth/perlin:perlin` mapping to
`bind_synth_perlin_perlin` and preserve all 128 historical public mappings.

Binder negative tests remove each required binding one at a time and supply a
wrong variant type one at a time. All must throw `KernelBindingError`. Unknown
catalog key remains the existing `std::invalid_argument` behavior. No hidden
defaulting or `DIMENSIONS` runtime lookup is allowed.

## Direct unsigned-word and unreachable-site tests

Public pixels cannot test `hash3`. Add an explicit test-local native evaluator
whose exact path is:

```cpp
std::uint32_t inner = a ^ b;
std::uint32_t word = inner ^ c;
float numerator = static_cast<float>(word);
double ratio = static_cast<double>(numerator) /
               static_cast<double>(static_cast<float>(4294967295.0));
```

Execute all twelve frozen triples and compare inner/result hex words,
numerator F32 bits, and ratio F64 bits. At least the frozen high-bit rows must
differ from signed-JS numerator bits, proving the source-typed decision.

Use an explicit enum/switch for six distinct executable modes:

- exact left-associated XOR;
- outer OR;
- inner OR;
- outer AND;
- inner AND;
- right-associated XOR.

Each switch arm must be explicit; `default` throws. A witness structure records
which arm ran, intermediate word, result word, and association. Tests compare
every frozen mutation word, require OR/AND divergence coverage, require value
identity but distinct witness for right-associated XOR, and reject an invalid
enum. No mode may fall through to baseline. This prevents the vacuous-control
failure previously caught in Task 26.

Separately authenticate the four public mutated factories as output-identical
on all eight default cases. Treat that identity only as evidence that `hash3`
is unreachable. It never weakens structural rejection.

Python tests parse the executable C++ case table, word table, mode enum/switch,
expected outputs, and witnesses, compare them one-to-one with the frozen JSON,
and demonstrate that single-field tampering of each table fails while the
embedded oracle JSON is unchanged.

## Exhaustive negative closure

Construct analyzer-produced or `dataclasses.replace` single-axis candidates
with explicit preconditions proving only the intended coordinate changed.
Pass every candidate separately through profile, validator, and emitter.
Cover at least:

- missing/wrong/foreign carrier; foreign key; wrong source path/hash; raw or
  normalized byte change; missing/renamed/reordered/extra define; define value
  3; source-double numeric mode; any combined profile carrier;
- declaration/interface/resource reorder, type/name/storage/binding/output
  mutation; added sampler/texture/derivative/varying/struct/UBO;
- function count/order/ID/name/signature/return/parameter/body/hash mutation;
  moving sites to another function or statement; changed call graph,
  reachability partition, loop proof, recursion, or added reachable call to 49;
- outer/inner missing, duplicate, swapped, moved, re-associated, wrong parent
  role, wrong parent constructor, wrong path/span/hash/category;
- `|`, `&`, `+`, signed `int`, mixed `int/uint`, vector/scalar, changed operand
  lane/order/symbol, third scalar XOR, or equal-looking non-authorized object;
- emitter helper lowering, `glsl::bitwise_xor` scalar use, a generic scalar
  overload, tree rewriting, or any `DIMENSIONS=3` attempt.

All candidates must reach the intended structural precondition before the
rejection assertion. Do not rely on an earlier unrelated error.

## TDD sequence and required RED evidence

Record command, expected failure, and unedited failing output before each
production change:

1. **Profile RED:** tests import/authenticate exact and mutated Perlin. Initial
   failure: missing profile module. Implement only exact authenticator/identity
   apply.
2. **Schema RED:** add the planned 127th row and census/order/carrier tests.
   Initial failure: unknown row field/wrong count. Implement only narrow loader
   schema and exact census.
3. **Validator RED:** call validator on exact program/carrier. Initial failure:
   unexpected keyword or unsupported scalar XOR. Add independent validator
   authentication/object admission.
4. **Emitter RED:** call emitter directly with exact program/carrier and assert
   direct nested spelling. Initial failure: unexpected keyword or unsupported
   scalar XOR. Add independent emitter authentication/lowering.
5. **Generation RED:** generate 127 blocks and isolation/manifest assertions.
   Initial failure: carrier not wired or Perlin block absent. Wire pipeline and
   manifest only.
6. **Native catalog/word RED:** add binder, eight public cases, twelve words,
   six-mode witnesses, and frozen-table transcription tests before canonical
   regeneration. Initial failure: missing binder/catalog row and executable
   native cases. Regenerate only after Python generator tests are green.

No production change is accepted without its preceding RED and focused GREEN.

## ABI, warnings, sanitizer, stack, and disassembly gates

Build fresh Debug and Release trees using existing C++20 flags
`-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`; run CTest in both. Run a
fresh ASan/UBSan build and CTest with halt-on-error; on Apple leak-sanitizer
unsupported failure, preserve the first log and rerun only with
`detect_leaks=0`. No sanitizer finding is acceptable.

The profile projection compiled cleanly under AppleClang 16. Observed
per-function stack usage was:

| Function | Debug | Release |
| --- | ---: | ---: |
| `hash3` | 576 B | 64 B |
| `pixel` | 608 B | 96 B |
| maximum relevant helper | 464 B | 144 B |

These are planning observations, not final evidence. Final generated code must
be measured anew with `-fstack-usage`. Stop if `hash3` exceeds 640/96 B,
`pixel` exceeds 704/128 B, or any Perlin helper exceeds 640/192 B in
Debug/Release. No VLA, `alloca`, heap allocation, exception path, callback,
virtual/indirect call, or per-pixel dynamic state may appear.

Release disassembly must isolate generated `hash3` and prove:

- the terminal scalar reduction is exactly two sequential word XOR (`eor` on
  AArch64), followed by unsigned word-to-float conversion (`ucvtf`), not signed
  conversion;
- the existing vector mix has its distinct three lane XORs;
- no scalar helper symbol/call/relocation was introduced;
- `grad3` retains exactly three direct calls to `hash3`, while the resolved
  `pixel` call graph has none;
- no dynamic stack adjustment beyond the fixed frame and no indirect call in
  the relevant generated functions.

The binder's one `std::make_shared<State>` allocation is existing setup-time
ABI and is outside per-pixel/helper prohibitions.

## Full verification order

After focused GREEN:

1. `python3 tools/glslcpp/check_corpus.py --check`;
2. `python3 tools/glslcpp/generate_typed_slice.py --check`;
3. focused profile/validator/emitter/generation/transcription tests;
4. full Python unittest discovery;
5. fresh Debug build and CTest;
6. fresh Release build and CTest;
7. fresh ASan/UBSan build and CTest;
8. stack/disassembly inspection;
9. all Task 15 through Task 27 oracle generators with `--check`;
10. exact counts/order/hashes/manifest/catalog and historical-block isolation;
11. repository-scope/file-hash audit;
12. independent implementation review and fix/re-review until zero
    Critical/Important findings.

## Owned files and stop rule

Task 27 may modify exactly:

```text
tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py   (new)
tools/glslcpp/generate_typed_slice.py
tools/glslcpp/emit_typed_cpp.py
tools/glslcpp/typed_slice.json
tests/test_typed_generator.py
tests/test_generated_kernels.cpp
src/typed_generated/typed_slice.cpp                       (generated)
src/typed_generated/typed_manifest.json                   (generated)
include/noisemaker/generated/catalog.hpp                  (generated)
```

`tests/test_typed_slice.cpp` is a frozen unchanged sentinel. All runtime,
public API other than the generated binder declaration, CMake, corpus,
documentation, and prior-profile files are forbidden. Unexpected drift,
required out-of-list edits, oracle inconsistency, or a newly exposed blocker
stops implementation for a new bounded review.
