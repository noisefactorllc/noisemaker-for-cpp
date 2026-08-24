# Task 17 final acceptance review

## Decision

**NOT APPROVED.** One P1 boundary-authentication defect and one P2 frozen-scope
violation remain.

Repository review was read-only. I invoked no Git command and changed no
repository file. This document is the only file written.

## P1 — the source-locked proof omits globals/resources, so forged IR can widen bindings and admit a global array

The frozen contract requires exact ordered globals/resources, exact required
bindings, no resource ABI change, and no global array. Both the corrected brief
and approved implementation design make those requirements explicit. The
implementation authenticates only `repr(program.functions)` against a
hard-coded digest:

- `tools/glslcpp/frontend/fixed_nine_table_proof.py:47-48` hashes only the
  function tuple.
- `prove_fixed_nine_local_tables` accepts only `(functions, key, defines)` at
  lines 64-72; it cannot inspect declarations, resources, builtins, outputs,
  or other program-level state.
- Its claimed census at lines 133-147 walks only top-level `main.body`
  expressions plus selected loop-body expressions. It is not a recursive
  whole-program declaration/index census.
- Validator array admission at
  `tools/glslcpp/generate_typed_slice.py:706-711` permits every `float[9]` or
  `vec2[9]` typed occurrence whenever any fixed-nine proof is present.
- Validator global checks skip all uniform/output declarations at lines
  804-810, then accept those storage classes generically at lines 872-877.
- Emitter global validation likewise skips every uniform/output declaration at
  `tools/glslcpp/emit_typed_cpp.py:215-222`, and emission derives the State ABI
  and binding lookups directly from the unauthenticated declarations at lines
  905-916 and 938-945.

### Exact reproduction 1: extra required uniform

For each canonical Task 17 `TypedProgram`, I cloned the authentic `amount`
declaration and span, changed only its symbol ID/name to a fresh
`forgedExtra`, appended it to `program.declarations`, appended the same name to
`program.resources.uniforms`, and retained the authentic raw source,
normalized source, empty defines, functions, counted-loop proof, fixed-nine
proof, and all original spans.

The mutation was equivalent to:

```python
basis = next(d for d in program.declarations if d.symbol.name == "amount")
symbol = dataclasses.replace(
    basis.symbol,
    id=max(d.symbol.id for d in program.declarations) + 10000,
    name="forgedExtra",
)
extra = dataclasses.replace(basis, symbol=symbol)
resources = dataclasses.replace(
    program.resources,
    uniforms=program.resources.uniforms + ("forgedExtra",),
)
forged = dataclasses.replace(
    program,
    declarations=program.declarations + (extra,),
    resources=resources,
)
```

Observed for both `filter/sharpen:sharpen` and `filter/sobel:sobel`:

```text
validator ACCEPT
emitter   ACCEPT
```

The emitted C++ materially widens the required binding interface:

```text
double forgedExtra;
... bindings.get_number("forgedExtra") ...
```

For Sharpen it generated a six-argument State instead of the frozen five; for
Sobel it generated seven instead of six. This is not merely inert metadata: a
caller with the canonical binding set would now fail at bind time.

Changing only `program.resources.uniforms` (without a declaration change) was
also accepted by both boundaries for both keys, proving that the retained
resource contract is not authenticated or even cross-checked.

### Exact reproduction 2: forbidden global array

For each key I reused the canonical first local array's authentic `float[9]`
type and span, gave a fresh symbol the `output` storage class, appended a
`TypedDeclaration` to `program.declarations`, and added its name to
`program.resources.outputs`. Source, functions, proofs, and provenance stayed
authentic.

```text
filter/sharpen:sharpen: validator ACCEPT; emitter ACCEPT
filter/sobel:sobel:     validator ACCEPT; emitter ACCEPT
```

The emitter silently omitted `forgedGlobalArray` from C++, but both typed
boundaries admitted a program containing the expressly forbidden global
array. This directly disproves the required whole-program array census.

### Why the body itself resists forged proof fields

I separately mutated, for both keys:

- a scalar table RHS literal;
- an offset-table RHS expression;
- loop/convolution body role ordering.

For the scalar mutation I tried the old authentic proof, a cleared proof, and
a forged proof whose `typed_ir_sha256` was updated to the changed function
tuple. For the other mutations I supplied the correspondingly updated forged
fingerprint. Validator and emitter rejected every case with `malformed
fixed-nine local-table proof`. The hard-coded function digests at
`fixed_nine_table_proof.py:35-38` therefore prevent an attacker from merely
recomputing the stored proof after changing function-body IR.

That function-only lock does not repair the P1: the approved proof is
program-level specifically because it must authenticate globals/resources as
well as local statements.

### Required remediation

Reconstruct the Task 17 proof from the complete clean `TypedProgram`, not just
`functions`. At both validator and emitter boundaries require the exact
ordered declaration tuple, symbol types/storage/names, exact
`ResourceRequirements` including `uses_texture=True` and
`uses_derivatives=False`, exact outputs/builtins/interfaces, and absence of
all extra globals. Array/type/index admission must be per reconstructed proof
site/ID, not the current blanket “proof exists and type is float[9]/vec2[9]”
rule. Add both-boundary negatives for extra/reordered/renamed/wrong-type
uniform/output declarations, forged resource tuples, and global arrays.

## P2 — `catalog.hpp` was modified despite an explicit frozen do-not-modify rule

The approved implementation design says under **Do not modify**:

```text
include/noisemaker/generated/catalog.hpp; Task 17 can bind through the existing
public generated::bind(key, bindings) catalog API, matching Task 16.
```

The implementation report nevertheless lists that header as changed, and the
current file adds direct declarations at
`include/noisemaker/generated/catalog.hpp:51` and `:56`. The new native test at
`tests/test_generated_kernels.cpp:268-273` depends on those direct declarations
instead of the approved string-key `generated::bind` path.

Remove the two header declarations and exercise the existing public catalog
API, or obtain and freeze an explicit design amendment before acceptance.

## Passing evidence and bounded checks

- Canonical Task 17 Python selection: **5/5 passed**.
- `python3 -m tools.glslcpp.generate_typed_slice --check`:
  `typed slice ok (110 programs)`.
- Existing instrumented Debug and Release native binaries: both complete
  suites exited 0, including exact Task 17 bindings and all four Task 17
  external oracle cases.
- `node docs/port-engineering/task-17-oracle-generator.mjs --check`:
  `ok task-17-oracles.json`.
- Independent counts: **110 typed / 112 public / 100 public-unported**, with
  each Task 17 key present exactly once in typed and public catalogs.
- Generated Sharpen slice: one `std::array<double, 9>{}`, one
  `std::array<glsl::Vec2, 9>{}`, two direct `[i]` reads, no `.at(`, no
  `std::vector`.
- Generated Sobel slice: two `std::array<double, 9>{}`, one
  `std::array<glsl::Vec2, 9>{}`, three direct `[i]` reads, no `.at(`, no
  `std::vector`.
- Provenance canonicalization is key-sorted and type-tagged, checks `bool`
  before `int`, rejects non-finite floats, and copies caller items before
  normalization (`tools/glslcpp/frontend/__init__.py:15-34`). The canonical
  provenance negatives pass.
- Compiler stack evidence is reproducible in the checked instrumented
  artifacts with `-fstack-usage -fstack-size-section`:
  - Sharpen `typed_63::pixel`: Debug **1280**, Release **304** bytes.
  - Sobel `typed_68::pixel`: Debug **1744**, Release **432** bytes.
  - Raw table payload remains separately **144 / 216** bytes.

The passing canonical tests do not cover either accepted forged-program
reproduction above. `tests/test_typed_generator.py:93-114` only tampers with a
stored proof field; it does not mutate function IR, declarations, resources,
or array placement.

## Artifact and changed-scope hashes

Frozen inputs rechecked:

- Corrected brief:
  `2306280acb661199c07cb2ad8e6607393129469b09d1d0976ed1bb7428719ba7`
- Approved scope/proof rereview:
  `a00cb56743aa9cd3218226854a1b0dbf676f7fc5e2a356925b75fe07325fbc50`
- Implementation report:
  `fabc1f978ceeceb92fbbe0db716b4372715399309c527edf770124bdfca31e6d`
- Oracle generator:
  `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`
- Oracle JSON:
  `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`

All fourteen repository-file hashes listed in the implementation report match
the current files byte-for-byte. Because Git was prohibited, I did not use VCS
state to infer whether that list is exhaustive; the report itself establishes
the frozen-scope violation by declaring `catalog.hpp` changed.

