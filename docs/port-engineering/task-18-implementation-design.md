# Task 18 Fixed Grid Counter Store Implementation Design

> **For agentic workers:** REQUIRED SUB-SKILLS: use `superpowers:test-driven-development` for every implementation step and `superpowers:verification-before-completion` before any acceptance claim. Do not create a branch, worktree, commit, push, pull request, or invoke Git directly or indirectly.

**Goal:** Add exactly `filter/celShading:celShadingEdges` and `filter/outline:outlineSobel` through one source-locked `fixed-grid-counter-store-v1` capability, producing 112 typed and 114 public kernels while leaving 98 pinned corpus programs publicly unported.

**Architecture:** Add a second, independent fixed-array proof family. Its frozen program-level record authenticates the two complete typed programs, the pre-array zero-dimension return, one zero-initialized `float[9] samples` local, a fresh `int idx=0`, the exact prefix-updated 3-by-3 loop nest, one source-specific dynamic store immediately followed by one discarded postfix increment per inner visit, and the exact later literal Sobel reads. Semantic analysis attaches the proof after counted-loop, Task 16 counter, and Task 17 fixed-table proof attachment. Validator and emitter each discard and reconstruct all dependent proofs before authorizing only the recorded declaration, dynamic lvalue store, discarded update statement, and literal rvalue reads.

**Tech stack:** frozen Python dataclasses and typed GLSL IR; exact source-specific structural matchers plus hard-coded typed-function and whole-program SHA-256 locks; the existing typed C++20 emitter; `std::array<double, 9>`; native C++ F32/RGBA oracle tests; AppleClang `-fstack-usage`; fresh CMake Debug and Release builds.

## Hard gates and scope

- Task 17 was explicitly accepted by the controller during this design pass; no Task 18 implementation begins until the controller separately authorizes it.
- Before implementation, resolve the Task 18 brief identity discrepancy documented under **Hidden blockers**. The implementation must name one exact approved brief hash.
- The only new capability is `fixed-grid-counter-store-v1`; the only new keys are the two named above, both with exactly `{}` defines.
- Do not broaden Task 16's `discarded-local-counter-statement-v1` proof. Task 18's `idx++` is authorized by the new source-specific program proof and by no generic postfix path.
- Do not broaden Task 17's `fixed-nine-local-literal-init-counted-read-v1` proof. Task 17 continues to own only its literal stores and direct induction reads.
- Do not add array types or `index`/`post` to the general language vocabulary. Do not admit Refract, Sacred Geometry, another extent/type/key, generic nested counter stores, partial initialization, array parameters/returns/copies/aliases/escapes, dynamic reads, or expression-valued postfix.
- Preserve strict `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`, the current resource ABI, and `noexcept` pixel functions.
- No heap allocation, per-pixel string/map/variant work, callback, virtual dispatch, throwing bounds check, runtime dependency, or zero-size sampler/runtime/test seam.

## Frozen design inputs

- Current brief bytes: SHA-256 `11628e7d2aa25450e2988e35614c931094d4254f216f374e23a78b2401aa0684`.
- Independently approved brief bytes named by the re-review: SHA-256 `8ea81afc0f9488c533bafc372ea92565f2237ee0e473ebef313503b940d8719b`.
- Risk audit: `45e7efad86d2b390068052bdec914a413bf3540ac8f5af6cf53ed1290a28cbda`.
- Oracle report: `16199e11d4ec8af8c4c5ecf86748d16573c2f53c61ed4e3bd4c79acec8a710f3`.
- Oracle JSON: `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`.
- Oracle generator: `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`.
- Initial scope/proof review: `bc27eaa3db334e6912574429d94f1d6a50f7ed5995170881a6ba67f70ba3edc7`.
- Corrected approving re-review: `9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`.

Source locks owned by the new proof module:

| Key | Raw SHA-256 | Normalized SHA-256 | Source profile |
| --- | --- | --- | --- |
| `filter/celShading:celShadingEdges` | `9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e` | `c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e` | `cel-shading-edges-3x3-v1` |
| `filter/outline:outlineSobel` | `cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d` | `fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d` | `outline-sobel-3x3-v1` |

The proof module hashes retained `raw_source` and normalized `source` itself and requires `preprocessor_defines == ()`. The caller-supplied manifest digest remains an additional equality gate, never the source of authority.

## File map

### Create

- `tools/glslcpp/frontend/fixed_grid_counter_store_proof.py` — Task 18 keys/digests, source-specific structural reconstruction, exact occurrence census, typed-function and whole-program hard locks, and immutable proof construction.

### Modify

- `tools/glslcpp/frontend/typed_ir.py` — add Task 18 frozen proof records and append `fixed_grid_counter_store_proof` to `TypedProgram`.
- `tools/glslcpp/frontend/semantic.py` — attach Task 18 only after counted-loop, Task 16, and Task 17 proofs are present.
- `tools/glslcpp/generate_typed_slice.py` — add the capability, two-boundary reconstruction, proof-derived declaration/store/read/update authorization, exact 112-key schema gate, and catalog generation.
- `tools/glslcpp/emit_typed_cpp.py` — independently reconstruct the proof and lower only its array declaration, dynamic store lvalue, literal reads, and discarded `idx++`.
- `tools/glslcpp/typed_slice.json` — append the capability and add the two sorted `{}` entries.
- `tests/test_semantic.py` — exact positive proof/body/census/provenance assertions.
- `tests/test_typed_generator.py` — TDD positives, both-boundary tamper matrix, exclusions, emitted order/dominance, schema/count/drift assertions.
- `tests/test_generated_kernels.cpp` — 114-key catalog, two factory declarations, exact required-binding failure matrices, and adjacent exclusions.
- `tests/test_typed_slice.cpp` — the six frozen external-oracle cases, all probe bits, top-down orientation, and repeat identity.
- `src/typed_generated/typed_slice.cpp` — generator-owned output only.
- `src/typed_generated/typed_manifest.json` — generator-owned output only.
- `include/noisemaker/generated/catalog.hpp` — generator-owned output only.

### Do not modify

- `CMakeLists.txt`; stack flags are configure-time measurement flags.
- `include/noisemaker/glsl_runtime.hpp`, `Surface`, `Sampler2D`, bindings, the pass runner, or any runtime/resource/test seam.
- Pinned corpus sources, generated canonical JS, Task 15–17 oracle artifacts, or hand-written kernels.

## Frozen typed-IR records

Append records shaped as follows to `tools/glslcpp/frontend/typed_ir.py`. Keep every record `@dataclass(frozen=True, slots=True)` and use `SourceSpan` rather than offsets copied into mutable containers.

```python
@dataclass(frozen=True, slots=True)
class FixedGridLiteralReadProof:
    array_symbol_id: int
    literal_index: int
    index_span: SourceSpan
    expression_role: str       # "sobel-gx" or "sobel-gy"
    role_ordinal: int           # exact left-to-right position, 0..5

@dataclass(frozen=True, slots=True)
class FixedGridCounterStoreProof:
    proof_kind: str
    source_profile: str
    main_signature_id: int
    main_body_statement_count: int
    define_contract: tuple[PreprocessorDefine, ...]

    dimension_symbol_id: int
    dimension_symbol_name: str
    texture_size_statement_index: int
    early_return_statement_index: int
    early_return_span: SourceSpan
    zero_predicate_span: SourceSpan
    zero_assignment_span: SourceSpan
    zero_return_span: SourceSpan
    early_return_profile: str
    dominates_array: bool
    dominates_fetch: bool
    dominates_grid: bool
    dominates_store: bool
    dominates_counter_update: bool

    array_symbol_id: int
    array_symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_element_type: str
    array_declaration_statement_index: int
    array_declaration_span: SourceSpan

    counter_symbol_id: int
    counter_symbol_name: str
    counter_type: str
    counter_declaration_statement_index: int
    counter_declaration_span: SourceSpan
    counter_initializer_span: SourceSpan
    counter_initial_value: int

    outer_loop_statement_index: int
    outer_loop_span: SourceSpan
    outer_induction_symbol_id: int
    inner_loop_span: SourceSpan
    inner_induction_symbol_id: int
    loop_update_expression_kind: str
    loop_start: int
    loop_bound: int
    loop_comparison: str
    per_loop_trip_count: int
    lexical_product: int
    entrypoint_charge: int
    outer_body_statement_count: int
    inner_body_statement_count: int

    dynamic_store_statement_span: SourceSpan
    dynamic_store_index_span: SourceSpan
    dynamic_store_rhs_span: SourceSpan
    store_rhs_profile: str
    counter_update_statement_span: SourceSpan
    counter_update_expression_span: SourceSpan
    counter_update_source_kind: str
    counter_update_operator: str
    counter_update_value_discarded: bool
    store_precedes_update: bool
    store_lower_bound: int
    store_upper_bound: int
    store_count: int
    counter_final_value: int

    literal_reads: tuple[FixedGridLiteralReadProof, ...]
    literal_read_profile: str
    literal_read_count: int
    literal_read_unique_indices: tuple[int, ...]
    literal_read_occurrence_counts: tuple[tuple[int, int], ...]
    array_declaration_count: int
    array_reference_count: int
    array_typed_expression_count: int
    index_expression_count: int
    counter_declaration_count: int
    counter_reference_count: int
    no_array_initializer: bool
    no_copy_alias_escape_or_abi_use: bool
    no_alternate_array_write: bool
    no_alternate_counter_use: bool
    no_dynamic_read: bool
    no_index_after_grid: bool
    raw_payload_bytes: int
    typed_ir_sha256: str
    whole_program_sha256: str
```

Append to `TypedProgram`, after `fixed_nine_table_proof`, to preserve prior positional construction:

```python
fixed_grid_counter_store_proof: FixedGridCounterStoreProof | None = None
```

The record deliberately carries both reconstructible facts and the two hard-lock digests. The hard-coded expected digests prevent an attacker from changing the typed tree and recomputing a self-consistent proof; the explicit facts make the admitted capability reviewable and give each validator/emitter operation an exact authorization descriptor.

## Exact current structural profiles

Stable symbol IDs below are fresh-parse diagnostics, not standalone authority. The matcher binds them to exact symbols, spans, storage, types, parents, and full-program locks.

| Fact | Cel | Outline |
| --- | --- | --- |
| Global declaration IDs | tileOffset 1, fullResolution 2, colorTex 3, edgeWidth 4, edgeThreshold 5, renderScale 6, fragColor 7 | tileOffset 1, fullResolution 2, valueTexture 3, sobelMetric 4, thickness 5, renderScale 6, fragColor 7 |
| Helper functions | getLuminosity id 11, wrapCoord id 13 | distanceMetric id 13, wrapCoord id 15 |
| Main | id 12, 13 body statements | id 14, 14 body statements |
| Builtin | gl_FragCoord id 14 | gl_FragCoord id 16 |
| Dimension local | texSize id 16, body 1 | dimensions id 21, body 1 |
| Early return | body 2 | body 2 |
| Array | samples id 19, body 5 | samples id 25, body 6 |
| Counter | idx id 20, body 6 | idx id 26, body 7 |
| Outer/inner loops | body 7; ky 21, kx 22 | body 8; ky 27, kx 28 |
| Inner-body locals | sampleX 23, sampleY 24, texel 25 | sampleX 29, sampleY 30 |
| Inner-body count | 5: three declarations, store, update | 4: two declarations, store, update |
| Later scalars | gx 26, gy 27, magnitude 28, edge 29 | gx 31, gy 32, magnitude 33, normalized 34 |

Exact retained `local_type_names`:

```python
# Cel
('int', 'vec2', 'ivec2', 'ivec2', 'int', 'float', 'int', 'int',
 'int', 'int', 'int', 'vec4', 'float', 'float', 'float', 'float')

# Outline
('int', 'float', 'float', 'float', 'vec2', 'ivec2', 'ivec2', 'int',
 'int', 'float', 'int', 'int', 'int', 'int', 'int', 'float', 'float',
 'float', 'float')
```

Both program loop summaries must remain: two proved loops, zero unproved loops, maximum effective depth two, maximum lexical product nine, entrypoint charge 12, acyclic call graph. Each loop itself is `start=-1`, `bound=1`, comparison `<=`, update `++`, trip count three; the outer proof has lexical depth one/product three and the inner proof depth two/product nine. The source matcher additionally requires each header update expression itself to be `TypedExpression(kind="unary", operator="++")`; the generic loop proof's update string is insufficient because it intentionally loses prefix/postfix spelling.

Current post-Task-17 fingerprints measured read-only are:

| Key | `sha256(repr(functions))` | Whole profile excluding only Task 18 proof |
| --- | --- | --- |
| Cel | `3581b9006260f19fd8519172628a5de1b3b81edd123279ad81f30906dc9d8e50` | `ba5adfa3c30ba1290dbd5382c1158d3f695245428403054b42fe5012b51dfcc4` |
| Outline | `af33cbbba839cfb7ea71ce64a57805d31aba97edbe487095df7b89e44dbdb1ac` | `66c92544399ae3ca62dcd2ad35454e0ab86005474e5032a999d48ea3ca7c8c3c` |

These are provisional measurements until Task 17 acceptance and the approved-brief hash gate are resolved. At implementation start, reproduce them from a fresh parse. If either differs, stop and audit the accepted baseline; do not merely update constants. Once reconciled, freeze them as `_TYPED_IR_LOCKS` and `_WHOLE_PROGRAM_LOCKS`.

The whole-program profile is exactly:

```python
(
    program.key, program.source, program.raw_source,
    program.declarations, program.functions, program.resources,
    program.body_status, program.local_type_names,
    program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols,
    program.counted_loop_proof, program.preprocessor_defines,
    program.fixed_nine_table_proof,
)
```

It excludes only `fixed_grid_counter_store_proof`, the proof currently being rebuilt. Including Task 17's proof field locks the full post-Task-17 semantic state even though it must be `None` for these two keys.

## Source-specific reconstruction algorithm

Implement `prove_fixed_grid_counter_store(program: TypedProgram) -> FixedGridCounterStoreProof | None` and `source_provenance_error(program, source_hash)` in the new module.

1. Return `None` unless the key is exactly Cel or Outline and defines are empty. Independently require raw, normalized, and supplied raw digests to match the key's constants.
2. Require the exact typed-function fingerprint and exact whole-program fingerprint before deriving any authorization.
3. Require exact ordered declarations, resources, and function set. Resources are exact uniforms in source order, one exact sampler, output `fragColor`, `uses_texture=True`, and `uses_derivatives=False`. No struct, UBO, varying, global/parameter/return array, extra global, overload, or prototype is accepted.
4. Require exactly one defined `void main()` and the exact main body count. Match every top-level main statement, not only the array neighborhood. Cel's ordered main roles are `globalCoord`, `texSize`, early return, `coord`, `offset`, `samples`, `idx`, grid, `gx`, `gy`, `magnitude`, `edge`, output. Outline's are `globalCoord`, `dimensions`, early return, `coord`, `metric`, `offset`, `samples`, `idx`, grid, `gx`, `gy`, `magnitude`, `normalized`, output. Exact full-function locks supplement these named structural checks.
5. Match the early return at body index 2. Its condition tree must be the source-ordered binary `||` of `(dimension.x == int 0)` and `(dimension.y == int 0)`, using the exact dimension symbol from body index 1. Its sole block has exactly two children: plain `fragColor = vec4(0.0)` followed by an empty `return`. Require body index 2 to precede the array, grid, every `texelFetch`, dynamic store, and counter update. Reject a missing/moved/reordered/negated/weakened predicate, changed dimension/symbol/literal/operator/output, added branch child, return expression, bypass, or any array/fetch/grid work in or before the branch.
6. Require the sole admitted array declaration at Cel body 5 / Outline body 6: one writable function-local symbol named `samples`, exact type `float[9]`, no initializer child, no qualifier/parameter/return/global role, and no multi-declaration packing. Its native element type is exactly `double`, extent nine, raw payload 72 bytes.
7. Require an immediately following single declaration of fresh writable local `int idx`, initialized by exact signed-int literal `0`. It must be Cel body 6 / Outline body 7, with no expression wrapper, conversion, alternate symbol identity, or nonzero/dynamic initializer.
8. Match the outer loop at Cel body 7 / Outline body 8. Its initializer declares only `int ky=-1`; condition is exact `ky <= 1`; update is exact prefix typed `unary ++ky`; body is one block containing only the inner loop. Match inner `int kx=-1; kx<=1; ++kx` identically. Require the existing loop proofs and program summary facts listed above. Reject postfix header updates even though the generic counted proof would retain the same `update="++"`.
9. Require exact inner-body statement counts. Match the source-specific prelude in order:
   - Cel: `sampleX = wrapCoord(coord.x + kx * offset, texSize.x)`, `sampleY = wrapCoord(coord.y + ky * offset, texSize.y)`, `texel = texelFetch(colorTex, ivec2(sampleX, sampleY), 0)`.
   - Outline: the same `sampleX`/`sampleY` shapes against `dimensions`, with no separate texel local.
   Match all stable IDs, call signature IDs, typed operators, constructor/builtin overloads, literal level zero, swizzles, and spans. There is no condition, return, break, continue, nested third loop, or extra statement.
10. Match the next inner child as one plain `=` assignment. Its lvalue is exactly `index(id(samples), id(idx))`; both symbols and the index-expression span are recorded. Its RHS is exact:
    - Cel profile `cel-wrapped-fetch-luminosity-v1`: `getLuminosity(texel.rgb)` using the immediately preceding `vec4 texel`.
    - Outline profile `outline-wrapped-fetch-red-v1`: `texelFetch(valueTexture, ivec2(sampleX, sampleY), int 0).r`.
    Recursively prove the RHS contains no `samples` or `idx` reference or write.
11. Match the immediately following and final inner child as one expression statement containing source `TypedExpression(kind="post", operator="++")` over the exact `idx` ID. Its value is discarded because the post node is the entire expression statement. Record both statement and expression spans. Reject prefix, decrement, compound assignment, use inside another expression, target change, reorder, intervention, duplication, or deletion.
12. Derive rather than assume the interval: outer/inner trip counts are 3×3, there is exactly one store then one update on every inner visit, and the counter starts zero. Record store values 0 through 8, count nine, and final counter nine. Require no path skips/multiplies the pair and no `idx` use after the grid.
13. Match the exact authored Sobel reads, in left-to-right expression-tree order:

```text
gx: samples[0], samples[2], samples[3], samples[5], samples[6], samples[8]
gy: samples[0], samples[1], samples[2], samples[6], samples[7], samples[8]
```

   Every index is an exact signed-int literal node whose source text/value equals the listed digit. Record 12 read occurrences, unique indices `(0,1,2,3,5,6,7,8)`, and occurrence counts `((0,2),(1,1),(2,2),(3,1),(5,1),(6,2),(7,1),(8,2))`. Index 4 is never read, but store completeness remains nine.
14. Match the entire `gx` and `gy` arithmetic trees, including unary minus, coefficient literals `2.0`, operators, grouping, result types, and symbols. Match the remainder of each program as part of the complete body profile, including Cel luminosity/smoothstep and Outline `distanceMetric`/clamp. This prevents an authentic-source forged tree from changing an RHS or post-grid consumer while retaining the same index census.
15. Run a context-aware recursive census over declarations, functions, statements, and expressions. The exact totals per program are:
    - one array declaration node;
    - 13 array base-ID references: one dynamic store plus 12 literal reads;
    - 14 array-typed expressions when the declaration is included;
    - 13 index expressions: one dynamic lvalue plus 12 literal rvalues;
    - one counter declaration and exactly two counter ID references: the dynamic store subscript and discarded update;
    - zero other array/counter occurrence, initializer, copy, alias, call, return, constructor, member/swizzle, nested index, alternate write, dynamic read, or post-grid counter use.
16. Construct and return the immutable proof only after every check and both hard locks pass. Do not accept a digest supplied inside an existing proof as authority.

## Semantic attachment and dependent-proof order

Keep analysis order explicit in `semantic.py`:

```text
BodyAnalyzer.functions
  -> attach_counted_loop_proofs
  -> attach_discarded_local_counter_proofs (Task 16 only)
  -> construct TypedProgram with both fixed proof fields None
  -> attach/reconstruct fixed_nine_table_proof (Task 17)
  -> attach/reconstruct fixed_grid_counter_store_proof (Task 18)
```

Use `dataclasses.replace` to attach each program-level proof. Task 18's whole-program lock sees the already attached Task 17 field. Do not place Task 18 evidence on `TypedStatement.counter_proof`; that field remains exclusively Task 16.

## Validator boundary

In `tools/glslcpp/generate_typed_slice.py`:

1. Append `FIXED_GRID_CAPABILITY` to `APPROVED_CAPABILITIES` and exclude it from `_BUILTINS`. Leave `APPROVED_TYPES` and operator vocabularies unchanged.
2. Run Task 18's independent provenance check before traversal.
3. Reconstruct dependencies in order from untrusted `typed` data:

```python
counted = attach_counted_loop_proofs(typed.functions, typed.key)
counters = attach_discarded_local_counter_proofs(counted, typed.key)
base = dataclasses.replace(
    typed, functions=counters,
    fixed_nine_table_proof=None,
    fixed_grid_counter_store_proof=None)
fixed_nine = prove_fixed_nine_local_tables(base)
with_fixed_nine = dataclasses.replace(base, fixed_nine_table_proof=fixed_nine)
fixed_grid = prove_fixed_grid_counter_store(with_fixed_nine)
```

   Compare the supplied counted, Task 16, Task 17, and Task 18 proofs to these independently reconstructed values. For a Task 18 key, require exact non-`None` Task 18 proof; for every other key, reject a present Task 18 proof. Never reuse the supplied Task 18 proof while computing its expected value.
4. Build four proof-derived authorizers after successful reconstruction:
   - exact array declaration `(array ID, declaration span, "float[9]")`;
   - exact dynamic store lvalue `(array ID, idx ID, index span, assignment statement span)`;
   - exact literal rvalue occurrences `(array ID, literal value, index span, role, ordinal)`;
   - exact discarded post statement `(idx ID, post span, statement span)`.
5. Keep array rejection fail-closed. `reject_type` accepts an array only for the exact proved declaration or the exact base ID inside one authorized index occurrence. Arrays elsewhere remain unsupported.
6. Make expression validation context-aware for this capability. On an assignment, validate the left with `context="lvalue"` and right with `context="rvalue"`. The Task 18 dynamic index is accepted only in the exact lvalue descriptor. Task 18 literal indices are accepted only in exact rvalue descriptors. Never call a generic index admission path.
7. In statement validation, recognize Task 18's exact discarded post descriptor before ordinary expression traversal, validate its target/type/operator/span against the reconstructed proof, add the new capability to `used`, and return. Every other `post`, including identical syntax under another key or span, remains rejected. Existing Task 16 statement-proof handling remains separate.
8. Add the capability to `used` only through one of these verified Task 18 operations. Existing exact declared-versus-used comparison then rejects missing schema capability and accidental unused capability drift.

## Emitter boundary and lowering

In `tools/glslcpp/emit_typed_cpp.py`:

1. Mirror the validator's independent source check and dependency reconstruction in `_validate_fixed_grid_counter_store`. Perform it after counted-loop, Task 16, and Task 17 validation. Store authorization maps only after exact equality succeeds.
2. Extend `_proved_array` by using two separate capability-specific lookups or add `_task18_array`; do not merge proof semantics by type. Task 17 and Task 18 must remain distinguishable in diagnostics and authorization.
3. Lower the exact Task 18 declaration to the existing declaration style with mandatory value initialization:

```cpp
[[maybe_unused]] std::array<double, 9> samples{};
```

   Reject initializer children, a mismatched symbol/type/span/name, or any second array. Never use `float`, an uninitialized array, a C array, `std::vector`, or heap storage.
4. Extend `lvalue()` only for the exact proved dynamic store. Emit its target without recursively rendering an arbitrary index tree:

```cpp
samples[static_cast<std::size_t>(idx)]
```

5. Extend rvalue `expression()` only for one exact recorded literal-read occurrence. Emit `samples[0]` through `samples[8]` directly from the proved literal. Do not admit `samples[idx]` as an rvalue, index 4, `.at()`, or an arbitrary computed expression.
6. In `statement()`, special-case only the exact reconstructed post statement and emit:

```cpp
++idx;
```

   Rewriting source postfix to prefix is semantics-preserving only because the proof establishes a standalone discarded result. Do not add `post` to general expression emission or reuse Task 16's statement annotation.
7. Preserve source order. In the emitted namespace, the zero-dimension `if`, zero output, and `return;` must appear before `samples{}`, the grid loops, `texel_fetch`, dynamic store, and `++idx`; the store must appear immediately before `++idx`; every literal read must appear after the grid.
8. Keep pixel `noexcept`. Add no `.at(`, `try`, `catch`, `throw`, `new`, `malloc`, `std::function`, callback, virtual call, or runtime container. `<array>` already exists in the generated translation unit; `std::size_t` is already available through current includes, so do not add an unrelated runtime dependency.

## Both-boundary fail-closed TDD matrix

Add focused tests before implementation and observe RED. Use one helper that submits every forged `TypedProgram` independently to `validate_capabilities(..., source_hash=...)` and `render_typed_cpp(...)`, requiring the Task 18 malformed/provenance diagnostic at both boundaries. Unless the test is specifically provenance, retain authentic raw/normalized source, defines, spans, symbols, and supplied proof to demonstrate structural reconstruction rather than source-string trust.

### Positive semantic/proof cases

- Both exact keys attach one proof with the right profile, declaration/body positions, source locks, empty defines, exact bindings/resources, loop proofs, RHS profile, interval 0..8/final 9, 12 literal reads and occurrence counts, exact census totals, payload 72, and both hard-lock hashes.
- The proof is frozen and rebuilding from a fresh parse produces equality.
- Existing Task 16 and Task 17 proofs remain byte-for-byte/equality stable for their keys, and Task 18 keys have neither Task 16 statement proofs nor Task 17 program proof.

### Provenance, identity, and interface tampering

- Wrong key; Cel/Outline key/source swap; wrong supplied digest; mutated retained raw bytes; mutated normalized bytes.
- `{"UNRELATED": 1}` with unchanged normalized source; `{"GL_ES": 1}` with changed normalization; replaced/cleared define provenance; forged proof define contract.
- Cleared proof, stale proof, proof copied from the other profile, one changed proof field, and an attacker-updated proof digest after a typed-tree mutation.
- Missing, reordered, renamed, duplicated, extra, wrong-type, wrong-storage uniform/output declaration; resource tuple-only mutation; wrong sampler/output; `uses_texture`/`uses_derivatives` mutation; extra global, function, prototype, struct, UBO, or varying.

### Early-return and whole-control tampering

- Delete/move the early branch; move it after array/grid; swap its block children; delete/replace return; add a return expression or third child.
- Change `||` to `&&`; change either `==`/zero/member/dimension symbol; negate the predicate; change the output/constructor/literal; place a fetch, array declaration, grid/store/update, or bypassing control before/inside it.
- Insert a return/break/continue/if/third loop into the grid, outer body, or inner body; move a post-grid read into the grid or a store out of it.

### Array and counter declaration tampering

- Extent 8/10/13; element `float` changed to `int`, `uint`, `vec2`, or `vec3`; array renamed, const, global, parameter, return, multi-declaration, initialized, copied, assigned as a value, passed, returned, aliased, constructed, escaped, nested-indexed, member/swizzled, or duplicated.
- `idx` missing/reordered/not immediately before grid; wrong name/type/storage/symbol; initial -1/1/dynamic/conversion/expression; second declaration; alternate read/write; post-grid use.

### Grid, store, RHS, and update tampering

- Either loop start/bound/comparison/induction/order/nesting changes; trip 2/4; inner/outer swapped; different induction ID; any header postfix update, decrement, compound update, or altered loop proof/summary/charge.
- Store missing/duplicated/reordered/moved; wrong target/base/index symbol/span; literal/computed/different dynamic index; compound assignment; second store; intervening statement before update.
- Cel prelude/RHS mutation: sample coordinate symbol/operator/member, wrap arguments/order, texel type/sampler/level, luminosity call/signature, or `.rgb` swizzle.
- Outline prelude/RHS mutation: coordinate/dimension symbol, sampler/level, `ivec2` shape, or `.r` lane.
- `idx++` missing/duplicated/reordered/retargeted; prefix `++idx`; `idx--`; `idx += 1`; expression-valued post; update placed in a conditional; extra update.

### Literal-read and post-grid tampering

- Delete/duplicate/reorder/change any of the 12 occurrences; use index 4, -1, 9, uint, dynamic, `1+1`, or forged literal metadata; change gx/gy role or operator/coefficient/unary minus.
- Dynamic read after grid, literal write after grid, read before all stores, second consumer loop, or array/counter reference hidden in another expression.
- Change Cel magnitude/smoothstep/output or Outline distanceMetric/metric-4 divisor/clamp/output while retaining source bytes. Full-function and whole-program locks must reject even if the array census is unchanged.

### Adjacent corpus exclusions

- Analyze but continue to reject `classicNoisedeck/refract:refract` and `synth/sacredGeometry:sacredGeometry` at validator and emitter.
- Confirm Task 17 Sharpen/Sobel continue to require their own capability, and no Task 18 authorizer accepts their arrays/indices.
- Confirm no non-Task-18 program can carry a forged Task 18 proof or exact-looking discarded post.

## Exact emitter and dominance tests

For each emitted Task 18 namespace, assert:

- exactly one `std::array<double, 9> samples{};` and no `std::array<float`, C array, `.at(`, `std::vector`, allocation, callback, dynamic dispatch, exception syntax, or resource/runtime change;
- exactly one source-site spelling `samples[static_cast<std::size_t>(idx)] = ...;`, immediately followed by `++idx;` in the inner body;
- 12 direct literal `samples[N]` read occurrences with the frozen occurrence counts and no `samples[4]` read;
- exact prefix `++ky` and `++kx` loop headers and three-trip bounds;
- pixel function remains `noexcept`;
- string positions satisfy `texture_size < if < zero-output < return < samples{} < outer-for < texel_fetch < dynamic-store < ++idx < gx/first-literal-read`. Perform this independently for Cel and Outline. This is the authorized evidence for the public-API-unreachable zero-dimension path; do not construct or inject zero-sized samplers.

## Allowlist, counts, catalog, and bindings

After proof/validator/emitter tests are green:

1. Append `fixed-grid-counter-store-v1` to `tools/glslcpp/typed_slice.json`'s exact capability list.
2. Insert sorted program records with `{}` defines:
   - Cel follows `filter/celShading:celShadingBlend`.
   - Outline Sobel lies between `filter/outline:outlineBlend` and `filter/outline:outlineValueMap`.
3. Change exact typed count gates 110 -> 112, public catalog 112 -> 114, and unported 100 -> 98. Keep the complete expected-key fixtures sorted and unique.
4. Run `python3 tools/glslcpp/generate_typed_slice.py --write` once. Never hand-edit the three owned generated files.
5. Assert the generated manifest adds only the two keys, exact raw source digests, `{}` defines, and exact source-order binding signatures.

In `tests/test_generated_kernels.cpp`, add a Task 18 factory declaration array of exactly:

```cpp
&noisemaker::generated::bind_filter_celShading_celShadingEdges
&noisemaker::generated::bind_filter_outline_outlineSobel
```

For each key, construct one complete binding set, then omit each required name and replace each with the wrong binding kind one at a time. Every omission/wrong kind throws `KernelBindingError`; unrelated uniform/texture extras do not prevent success.

- Cel required order/types: `tileOffset:Vec2`, `fullResolution:Vec2`, `colorTex:Surface`, `edgeWidth:number`, `edgeThreshold:number`, `renderScale:number`.
- Outline required order/types: `tileOffset:Vec2`, `fullResolution:Vec2`, `valueTexture:Surface`, `sobelMetric:number`, `thickness:number`, `renderScale:number`.

Keep `classicNoisedeck/refract:refract` and `synth/sacredGeometry:sacredGeometry` absent and throwing `std::invalid_argument` through generic `generated::bind`. Cel/Outline Task 18 keys move from that exclusion list into the sorted catalog.

## Six native external-oracle cases

Add a dedicated `task18_formula_surface()` rather than reusing Task 16's 11x9 fixture. Construct top-down 7x5 `std::vector<float>` data. Each assignment crosses the float boundary:

```cpp
R = float(0.035 + (((17*x + 31*y + 13) % 101) / 100.0) * 0.22)
G = float(0.020 + ((( 7*x + 19*y + 23) %  97) /  96.0) * 0.26)
B = float(0.010 + (((29*x + 11*y +  5) %  89) /  88.0) * 0.20)
A = float(0.350 + ((( 3*x +  5*y +  1) %  13) /  20.0))
```

For every render use fresh input and bindings, output 9x7, `tileOffset=Vec2(3,2)`, `fullResolution=Vec2(12,10)`, `renderScale=1.0f`, time `0.375f`, seed `19.0f`, frame `7`, and delta `1.0f/60.0f`. Width/thickness is exact `uint_bits_to_float(0x40133333)`. Thresholds are exact `0x3e3851ec` and `0x3f19999a`; metric uniforms are exact F32 1, 2, 3, 4. The default `glsl-f32` literal contract must convert Outline's source `1.414` to the canonical F32 value `1.4140000343322754` in the metric-4 behavior.

Freeze all complete-frame hashes and the 12 lane words at top-down probes `(0,0)`, `(4,3)`, `(8,6)`:

| Case | F32 SHA-256 | RGBA8 SHA-256 | Probe words, four lanes per point |
| --- | --- | --- | --- |
| Cel threshold 0.18f | `d86694f5c5a05c094b1dc9d4302b0b98cbe3044e5ce22587fdf6dd80f77d27a7` | `966ca81461240fb6c35316537f631f3b74b6d0a33a7b538d05ddd12e241347e9` | `3f074202`×3,`3f800000`; `3d038558`×3,`3f800000`; `00000000`×3,`3f800000` |
| Cel threshold 0.6f | `048acf6f8feb3be40c9be548bc64eaeadc6de78366a61b778c899eb463575ac0` | `8d0418a7e7b046d582cafcfbbe95b1bf2c05478929a57719ab52a345de1091e5` | all three probes `00000000`×3,`3f800000` |
| Outline metric 1 | `2e62cf4918bb2da1def8b146c4e33ef009d6c6ef05f96bf2d0fd2be4e7679a7f` | `a877af8b8229c67295f3c17123cbaa5a540e59e81a3f95af9db601be5b2eca90` | `3f6dc0cd`×3,`3f800000`; `3f800000`×4; `3f64f78a`×3,`3f800000` |
| Outline metric 2 | `afac987ef587a22d89ed00f619edb97e29d321fb2cc57667ceea89c0d78744b0` | `e01ac082638be9679283946c758e093c5ea966bc79b8acdf14d8ee1213f084f8` | all probes `3f800000`×4 |
| Outline metric 3 | `33eb93deef5ea41a7f085c4d3e9d8f4d5c3b4353b8490f0b9e0bbd2466c1d1ff` | `8c3a62bd220bf6321d1127ab2cb1823522ffe38e9e07f985af9aceb9e64a253c` | `3f6809d4`×3,`3f800000`; `3f800000`×4; `3f5f06f7`×3,`3f800000` |
| Outline metric 4 | `a4293babe12252aa6e0f4c4b50f6242ef4a1060297a40a1da12a549ea9c77047` | `db8a0a072ec1c5e85d8678100929a1ef5ecf5c6ffc88217536354d06f4a11f74` | same selected probe words as metric 3; full-frame F32 hash distinguishes the divisor path |

For every case, render twice from fresh surfaces, require complete F32 bytes and RGBA8 bytes equal before hashing, assert 9x7 dimensions, both hashes, and all probe words. The asymmetric top-down storage/bottom-left fragment convention and output-larger-than-input wrapping are part of the oracle; do not transpose or reuse a differently sized fixture.

Do not implement the oracle report's superseded zero-sampler injection paragraph. The later corrected brief and approving re-review explicitly forbid such a seam and replace it with structural reconstruction plus emitted dominance/order evidence.

## Debug/Release stack workflow

The raw logical table payload is exactly `9 * sizeof(double) = 72` bytes per pixel. It is not a frame-size limit. Measure the full compiler-reported frame in both fresh configurations without modifying project flags:

```sh
cmake -S . -B build-task18-debug \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS="-fstack-usage -fstack-size-section"
cmake --build build-task18-debug -j 8

cmake -S . -B build-task18-release \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-fstack-usage -fstack-size-section"
cmake --build build-task18-release -j 8
```

For each configuration:

1. Locate `CMakeFiles/noisemaker-cpu.dir/src/typed_generated/typed_slice.cpp.su` with `find`.
2. Map the sorted generated source markers to the Cel/Outline `typed_N::pixel` qualified names. Do not assume Task 17 namespace numbers: adding Cel near the front shifts later generated namespaces. Confirm names from the generated source and `.su` together.
3. Record each `.su` byte count and classification (`static`, `dynamic`, or `bounded`) separately for Cel and Outline.
4. Cross-check the typed-slice object with `xcrun llvm-objdump --stack-sizes` when Mach-O stack-size decoding is available. Treat `.su` as primary if the installed objdump cannot decode it.
5. Report 72-byte logical payload separately from Debug/Release whole-frame sizes. Do not add a cap without a separate reviewed decision.
6. Inspect both emitted pixel bodies in Debug and Release source/object evidence for direct array access, store/update order, `noexcept`, and absence of allocation/throw paths.

## Verification sequence

Run from `.` and preserve the Task 17 baseline.

```sh
# Frozen external gates; all are read-only.
node docs/port-engineering/task-15-oracle-generator.mjs --check
node docs/port-engineering/task-16-oracle-generator.mjs --check
node docs/port-engineering/task-17-oracle-generator.mjs --check
node docs/port-engineering/task-18-oracle-generator.mjs --check

# Focused and full Python proof/generator suites.
python3 -m unittest tests.test_semantic tests.test_typed_generator
python3 -m unittest discover -s tests -p 'test_*.py'

# Corpus and generated drift gates.
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check

# Direct native and CTest in both fresh instrumented builds.
./build-task18-debug/noisemaker-cpu-tests
ctest --test-dir build-task18-debug --output-on-failure
./build-task18-release/noisemaker-cpu-tests
ctest --test-dir build-task18-release --output-on-failure
```

Acceptance evidence must report:

- original RED failures before each production slice and GREEN focused reruns;
- all Python tests and all four drift gates;
- all Task 15–18 oracle `--check` results;
- fresh strict Debug and Release build success, direct native suite, and CTest;
- exact six-oracle hashes, probes, orientation, and double-render identity;
- exact 112 typed / 114 public / 98 public-unported counts;
- Task 18 emitted dominance/order and forbidden-construct scan;
- Cel and Outline Debug/Release `.su` frames plus separate 72-byte payload.

## Implementation task order

### Task 1: Resolve gates and freeze expected profiles

- [ ] Obtain explicit Task 17 acceptance.
- [ ] Obtain controller ratification of the current Task 18 brief hash or restore/review the exact approved bytes.
- [ ] Recompute raw/normalized, typed-function, and whole-program fingerprints from the accepted baseline; stop on drift.
- [ ] Record the accepted hashes in focused RED tests before writing proof code.

### Task 2: Add RED semantic proof tests, then proof records/reconstruction

- [ ] Add positives for exact profile/body/loops/early return/store/update/read census.
- [ ] Add representative RED mutations for every structural group.
- [ ] Add frozen dataclasses and the new proof module.
- [ ] Attach after Task 17 proof and make focused semantic tests GREEN.

### Task 3: Make validator reconstruction fail closed

- [ ] Add the complete both-boundary helper and first run validator cases RED.
- [ ] Reconstruct counted -> Task 16 -> Task 17 -> Task 18 from cleared fields.
- [ ] Add declaration, dynamic-lvalue, literal-rvalue, and discarded-statement authorizers.
- [ ] Run every validator tamper/exclusion test GREEN and rerun Task 16/17 tamper suites.

### Task 4: Add exact emitter lowering

- [ ] Add RED exact spelling, precision, update-order, dominance, and forbidden-construct tests.
- [ ] Mirror independent proof reconstruction in `_Emitter`.
- [ ] Emit only zero-initialized double array, proved dynamic lvalue, proved literal reads, and discarded increment.
- [ ] Run emitter and both-boundary tests GREEN.

### Task 5: Add only the two allowlist/catalog entries

- [ ] Update count/key expectations RED.
- [ ] Add capability and two sorted `{}` records.
- [ ] Regenerate the three generator-owned artifacts once.
- [ ] Run manifest/catalog/generated drift tests GREEN.

### Task 6: Wire exact bindings and six native oracles

- [ ] Add binding omission/wrong-kind/extras tests RED, then make them GREEN with generated factories.
- [ ] Add the exact 7x5 fixture, six cases, hashes, probe words, and double-render checks RED then GREEN.
- [ ] Keep zero-dimension verification structural/emitted only.

### Task 7: Full acceptance and measurement

- [ ] Run Task 15–18 oracle checks, all Python suites, and all drift gates.
- [ ] Configure/build/run fresh instrumented Debug and Release suites plus CTest.
- [ ] Inspect emitted hot loops and record exact `.su` evidence.
- [ ] Report exact counts and residuals without invoking Git.

## Hidden blockers and risks

1. **Task 17 acceptance is resolved.** The controller explicitly accepted Task 17 during this design pass. Reconfirm the measured post-Task-17 fingerprints at implementation start; unexpected drift remains stop-worthy.
2. **The current brief is not the byte sequence approved by the re-review.** The current file hashes to `11628e...`, while the approving re-review freezes `8ea81a...`. The present brief also cites the later re-review and declares approval, so at least an administrative post-review edit occurred. Content inspection shows the corrected prefix-loop and no-zero-seam requirements, but provenance policy forbids treating this as automatically benign. Implementation requires an explicit ratification of `11628e...` or a newly reviewed/restored exact brief.
3. **The oracle report contains superseded zero-size guidance.** It asks for native zero-width/height sampler injection, while the later corrected brief and approving re-review prohibit any seam and require structural/emitted dominance only. Follow the later approved correction; do not implement the report's stale paragraph.
4. **Generic counted-loop proof loses prefix/postfix spelling.** Task 18 must inspect exact `unary` header expressions in addition to `CountedLoopProof`; otherwise a forged postfix header could pass.
5. **A census without full-program hard locks is insufficient.** Authentic retained source plus forged typed functions/resources can be made internally self-consistent. Explicit structural matchers, fixed expected function fingerprints, and a whole-program fingerprint excluding only the proof being rebuilt are all required at both boundaries.
6. **Statement context matters.** The same `samples[idx]` shape must be allowed only as the proved lvalue store; the same literal shape only at its exact rvalue occurrences. A generic index renderer would silently broaden the language.
7. **Postfix authorization must remain statement-local.** Emitting `++idx` is valid only because the exact source post result is discarded. Reusing Task 16's general-looking field or admitting `post` expression traversal would authorize unintended semantics.
8. **Zero initialization and double storage are observable contracts.** `std::array<float,9>` creates an extra F32 boundary; an uninitialized array diverges from canonical zero fill and risks undefined behavior. Exact emitted-type tests are mandatory even though all nine stores are proved.
9. **Stack payload is not stack frame.** The only pre-measurement value is 72 bytes of logical table data. Debug/Release compiler frames must be recorded separately, and generated namespace indices must be rediscovered after catalog insertion.

## Design conclusion

Task 18 is implementable without a runtime, resource ABI, zero-size seam, or general language expansion. The minimum coherent implementation is one new source-specific program proof, four proof-gated lowering operations, two sorted allowlist entries, exact binding tests, and the six frozen native oracles. There is no technical blocker in the canonical programs, and Task 17 acceptance is resolved. Implementation remains procedurally blocked only on exact ratification of the current Task 18 brief bytes and separate controller authorization to begin.
