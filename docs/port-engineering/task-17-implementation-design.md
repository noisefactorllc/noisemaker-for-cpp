# Task 17 Fixed Nine-Element Local Tables Implementation Design

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:test-driven-development` for every implementation step and `superpowers:verification-before-completion` before any acceptance claim. Do not create a branch, worktree, commit, push, or pull request.

**Goal:** Add exactly `filter/sharpen:sharpen` and `filter/sobel:sobel` through one source-locked `fixed-nine-local-literal-init-counted-read-v1` capability, producing 110 typed and 112 public kernels without admitting a general array/index language.

**Architecture:** Add one frozen, program-level proof reconstructed from typed IR after counted-loop and Task 16 counter proofs. The proof recognizes only the two canonical main-function profiles, records the exact arrays, literal stores, counted reads, and control hierarchy, and is independently cleared/recomputed by validator and emitter. Only expressions covered by that verified proof receive `std::array` declarations or direct `operator[]` lowering.

**Tech Stack:** Python frozen dataclasses and typed GLSL IR, source-specific proof reconstruction, the existing typed C++20 emitter, `std::array`, native C++ oracle tests, AppleClang 16 `-fstack-usage`, CMake Debug/Release builds.

## Global constraints

- Implementation must not start until Task 16 is accepted and the independent Task 17 scope/oracle review approves the frozen contract.
- The only new keys are `filter/sharpen:sharpen` and `filter/sobel:sobel`; define maps are exactly `{}`.
- The capability is exactly `fixed-nine-local-literal-init-counted-read-v1` and must not admit other arrays, extents, indices, aggregate initialization, array ABI, aliasing, copying, or escape.
- Preserve the existing scalar JavaScript Number model with `std::array<double, 9>` and the vector F32-lane boundary with `std::array<glsl::Vec2, 9>`.
- Every array declaration is value-initialized with `{}`. Every proved access uses direct `operator[]`; `.at()` and exception handling are forbidden in `noexcept` pixel code.
- No heap allocation, per-pixel string/map/variant work, callback, virtual dispatch, resource ABI change, or runtime JS/Python/Qt dependency.
- Preserve strict `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off` builds.
- No Git command or indirect Git invocation is authorized.

## Frozen inputs

- Corrected brief SHA-256: `2306280acb661199c07cb2ad8e6607393129469b09d1d0976ed1bb7428719ba7`.
- Pre-correction scope/proof review SHA-256: `14f947fc37f71500c3588e9a2a8232a963e339a5924786be65cde6059b4e56f7`.
- Risk audit SHA-256: `17692e3784ad64a4a283f7509b8cabe65521cabe282d5a78d6e6ade17be24937`.
- Oracle report SHA-256: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`.
- Oracle JSON SHA-256: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`.
- Oracle generator SHA-256: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`.

## File map

**Create**

- `tools/glslcpp/frontend/fixed_nine_table_proof.py` — source-specific constants, exact Sharpen/Sobel typed-tree matchers, whole-program array-use census, proof clearing, and proof attachment.

**Modify**

- `tools/glslcpp/frontend/__init__.py` — freeze the caller's preprocessor define map into parsed-program provenance.
- `tools/glslcpp/frontend/typed_ir.py` — add define provenance and the frozen fixed-table proof records to `TypedProgram`.
- `tools/glslcpp/frontend/semantic.py` — retain define provenance and attach the fixed-table proof after counted-loop and discarded-counter attachment.
- `tools/glslcpp/generate_typed_slice.py` — source/proof validation, capability-specific array/index admission, allowlist count 110, and exact two-key entries.
- `tools/glslcpp/emit_typed_cpp.py` — independent proof reconstruction, zero-initialized `std::array` declarations, and direct proved index lowering.
- `tools/glslcpp/typed_slice.json` — append the capability and add the two sorted `{}` entries.
- `tests/test_semantic.py` — positive immutable proof and define-provenance assertions.
- `tests/test_typed_generator.py` — RED/GREEN boundary tests, full fail-closed mutation matrix, exact emitter spellings, counts, and generated drift expectations.
- `tests/test_generated_kernels.cpp` — 112-key catalog and exact binding-failure coverage.
- `tests/test_typed_slice.cpp` — four frozen Task 17 native oracle cases and adjacent-profile exclusions.
- `src/typed_generated/typed_slice.cpp` — generator-owned output only.
- `src/typed_generated/typed_manifest.json` — generator-owned output only.
- `include/noisemaker/generated/catalog.hpp` — canonical typed-slice generator-owned
  public factory declarations; Task 17 adds the two sorted declarations required
  by the existing catalog contract.

**Do not modify**

- `CMakeLists.txt`; stack flags are measurement-only configure arguments.
- `include/noisemaker/glsl_runtime.hpp`, the sampler/runtime ABI, corpus sources, or existing generated hand-written kernels.

Design amendment after final acceptance review: the earlier prohibition on
`include/noisemaker/generated/catalog.hpp` was inconsistent with the established
public typed-factory generator contract and the corrected brief, which does not
forbid the header. The canonical generator owns and updates this header alongside
`typed_slice.cpp` and `typed_manifest.json`; direct declarations for Sharpen and
Sobel remain required, and tests cover both those declarations and the generic
`generated::bind(key, bindings)` path.

## Frozen typed-IR proof

Add these records to `tools/glslcpp/frontend/typed_ir.py`:

```python
@dataclass(frozen=True, slots=True)
class PreprocessorDefine:
    name: str
    kind: str
    canonical_value: str

@dataclass(frozen=True, slots=True)
class FixedNineArrayProof:
    role: str
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_element_type: str
    declaration_statement_index: int
    declaration_span: SourceSpan
    literal_store_statement_indices: tuple[int, ...]
    literal_store_spans: tuple[SourceSpan, ...]
    literal_store_indices: tuple[int, ...]
    read_spans: tuple[SourceSpan, ...]
    reads_per_iteration: int

@dataclass(frozen=True, slots=True)
class FixedNineLocalTableProof:
    proof_kind: str
    source_profile: str
    main_signature_id: int
    function_body_statement_count: int
    define_contract: tuple[PreprocessorDefine, ...]
    arrays: tuple[FixedNineArrayProof, ...]
    initialization_start_statement_index: int
    initialization_end_statement_index: int
    reading_loop_statement_index: int
    reading_loop_span: SourceSpan
    induction_symbol_id: int
    loop_start: int
    loop_bound: int
    loop_trip_count: int
    index_lower_bound: int
    index_upper_bound: int
    loop_body_statement_count: int
    read_profile: tuple[str, ...]
    array_reference_count: int
    no_read_before_completion: bool
    no_write_after_completion: bool
    no_escape: bool
    raw_table_payload_bytes: int
```

Append to `TypedProgram`:

```python
raw_source: str = ""
preprocessor_defines: tuple[PreprocessorDefine, ...] = ()
fixed_nine_table_proof: FixedNineLocalTableProof | None = None
```

The proof is program-level because it must bind globals/resources/define provenance as well as local statements. Appending fields preserves existing positional constructors.

Expected proof profiles:

| Profile | Main statements | Arrays `(role, body index, stores)` | Read loop | Loop body | Payload |
| --- | ---: | --- | ---: | ---: | ---: |
| `sharpen-v1` | 29 | `kernel` `(6, 7..15)`, `offsets` `(16, 17..25)` | 27 | 2 | 144 |
| `sobel-v1` | 43 | `sobel_x` `(6, 7..15)`, `sobel_y` `(16, 17..25)`, `offsets` `(26, 27..35)` | 38 | 3 | 216 |

`read_profile` is exactly:

```python
# Sharpen
("offsets:texture-coordinate:i", "kernel:conv-multiply:i")

# Sobel
("offsets:texture-coordinate:i",
 "sobel_x:convX-multiply:i",
 "sobel_y:convY-multiply:i")
```

The proof stores stable IDs from the current parse, but IDs alone never authorize emission. The source-specific matcher and whole-program census reconstruct all fields from the immutable typed tree each time.

## Source-specific reconstruction algorithm

Create `attach_fixed_nine_local_table_proof(program: TypedProgram) -> TypedProgram` in `fixed_nine_table_proof.py`.

1. Clear `program.fixed_nine_table_proof` unconditionally with `dataclasses.replace`.
2. Return the clean program unless the key is exactly Sharpen or Sobel.
3. Require `program.preprocessor_defines == ()`, one defined `void main()`, no helper/prototype, no array return/parameter/global, no struct/UBO/varying, and the exact global declaration/resource order. The proof module does not accept a passed digest and does not derive authority from `program.raw_source` or normalized `program.source`; the two boundaries hash both retained strings independently before trusting the structural proof:
   - Sharpen: `tileOffset vec2`, `fullResolution vec2`, `inputTex sampler2D`, `amount float`, `renderScale float`, `fragColor vec4`.
   - Sobel: the same with `alpha float` before `fragColor`.
4. Require exact `ResourceRequirements.uniforms`, `.samplers`, `.outputs`, `uses_texture=True`, and `uses_derivatives=False`.
5. Require the exact main body counts and array declaration positions listed above. Each declaration must be a writable function-local `float[9]` or `vec2[9]`, have a matching `Symbol.type`, and have zero initializer children. Reject const/parameter/global/qualified declarations, any other element/extent, or multi-declaration packing.
6. Match every initialization statement directly in the main sequence. It must be an `expr` containing one plain `=` assignment whose target is `index(id(array), literal-int(k))`. Require `literal == str(k)`, `literal_value == k`, the exact element result type, and `k == 0..8` in order. This simultaneously proves one store per index, no duplicates/omissions, and no branch/loop/control bypass.
7. Match scalar payloads exactly:
   - Sharpen kernel: `[-1,0,-1,0,5,0,-1,0,-1]`.
   - Sobel X: `[1,0,-1,2,0,-2,1,0,-1]`.
   - Sobel Y: `[1,2,1,0,0,0,-1,-2,-1]`.
   Negative values must retain the typed unary-minus/literal tree; do not accept a forged literal with a negative value.
8. Match offsets exactly against the stable `texelSize` symbol as the row-major Cartesian product `(-x,-y), (0,-y), (x,-y), (-x,0), (0,0), (x,0), (-x,y), (0,y), (x,y)`. Require exact `vec2` constructor shape, swizzle, unary-minus, and zero literal nodes.
9. Require the direct reading loop at the exact body index and its existing `CountedLoopProof`: local `i`, initializer `0`, condition `i < 9`, postfix `i++`, literal bound, nine trips, lexical/effective depth one, lexical product nine, and entrypoint charge nine.
10. Match the entire loop body/control hierarchy, not merely the index nodes:
    - First statement is `vec3 texSample = texture(inputTex, ((uv + offsets[i] * amount * renderScale) * fullResolution - tileOffset) / vec2(textureSize(inputTex, 0))).rgb` with exact operators, builtin calls, and stable symbols.
    - Sharpen's second statement is exactly `conv += texSample * kernel[i]`.
    - Sobel's second and third statements are exactly `convX += texSample * sobel_x[i]` and `convY += texSample * sobel_y[i]`.
    - No nested statement, branch, second loop, return, break, or continue is present.
11. Perform a separate recursive whole-program census. Every array-typed expression must be one proved declaration or an exact `id` base of a proved index. Every `index` expression in the program must be one of the 18 Sharpen or 30 Sobel proved accesses. Every occurrence of an admitted array symbol must be accounted for as a declaration, literal-store base, or induction-read base. Reject arrays in calls, constructors, assignments as values, returns, copies, members/swizzles, nested indices, or any unaccounted context.
12. Require all stores to precede the sole reading loop and no store after it. The exact direct sequence proves no read before completion; the census proves no hidden read/write elsewhere.
13. Attach the fully reconstructed proof only after every condition succeeds.

This explicit matcher is preferable to a digest of a runtime-generated profile: expected structure must be hard-coded independently so a forged tree cannot compute its own authority.

## Semantic attachment and define provenance

`parse_program` currently drops both original raw source and `runtime_defines`, which prevents either boundary from independently proving the source/define contract. Add `_freeze_runtime_defines(runtime_defines) -> tuple[PreprocessorDefine, ...]` and return both retained values:

```python
"raw_source": source,
"preprocessor_defines": _freeze_runtime_defines(runtime_defines or {}),
```

The canonicalization is exact and type-tagged:

```python
def _freeze_runtime_defines(values):
    result = []
    for name in sorted(values):
        value = values[name]
        if not isinstance(name, str):
            raise ValueError("runtime define names must be strings")
        if isinstance(value, bool):
            result.append(PreprocessorDefine(name, "bool", "true" if value else "false"))
        elif isinstance(value, int):
            result.append(PreprocessorDefine(name, "int", str(value)))
        elif isinstance(value, float) and math.isfinite(value):
            result.append(PreprocessorDefine(name, "float", value.hex()))
        elif isinstance(value, str):
            result.append(PreprocessorDefine(name, "str", value))
        else:
            raise ValueError("runtime define values must be bool, int, finite float, or str")
    return tuple(result)
```

Checking `bool` before `int` is mandatory because Python booleans subclass integers. Decimal integer strings and `float.hex()` provide deterministic, immutable values and preserve `0.0` versus `-0.0`; raw strings remain exact. Sorting by key makes insertion order irrelevant, and constructing new records ensures no caller-owned mapping/value container survives.

`analyze_program` copies `parsed["raw_source"]` and the tuple to `TypedProgram`. Existing normalized `TypedProgram.source` remains unchanged. Construct the ordinary typed program after:

```text
BodyAnalyzer
  -> attach_counted_loop_proofs
  -> attach_discarded_local_counter_proofs
  -> summarize_counted_loop_proofs
  -> construct TypedProgram
  -> attach_fixed_nine_local_table_proof
```

These are the only new general provenance fields. They do not alter preprocessing behavior or authorize runtime defines. Provenance tests must establish:

- `typed.raw_source` is byte-for-byte the original caller string while `typed.source` remains normalized.
- Define entries are key-sorted and immutable.
- `{"D": True}`, `{"D": 1}`, `{"D": 1.0}`, and `{"D": "1"}` produce distinct records.
- Two maps with opposite insertion order produce equal tuples.
- Finite floats use exact `float.hex()` records; `nan`, `inf`, unsupported values, and non-string keys reject during parsing.
- Parsing either Task 17 source with `{"UNRELATED": 1}` retains identical normalized bytes but a nonempty define tuple; `{"GL_ES": 1}` retains the same raw source but changes normalized bytes. Both variants must be rejected at validator and emitter.

## Validator changes

In `generate_typed_slice.py`:

1. Append `fixed-nine-local-literal-init-counted-read-v1` to `APPROVED_CAPABILITIES` and exclude it from `_BUILTINS`. Do not add `float[9]` or `vec2[9]` to `APPROVED_TYPES`.
2. Add the exact raw/normalized hash table:

```python
{
  "filter/sharpen:sharpen": (
    "c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7",
    "1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0"),
  "filter/sobel:sobel": (
    "ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84",
    "d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c"),
}
```

For either key, directly require `sha256(typed.raw_source)`, `sha256(typed.source)`, and `typed.preprocessor_defines == ()` before capability traversal. Keep the supplied `source_hash` equality as a separate generator-integrity check/comment input, never as source authority.
3. Recompute in sequence: counted loop, Task 16 counter, then fixed-table proof on a `dataclasses.replace` copy of the program containing the recomputed functions and a cleared fixed proof. Compare actual and reconstructed `fixed_nine_table_proof` exactly. A present proof on any other key is malformed.
4. Build immutable authorization maps from the verified proof: array declaration symbol IDs, exact store `(array ID, literal index, span)`, and read `(array ID, induction ID, span)` descriptors.
5. Change `reject_type` only enough to accept an array type when the exact declaration/ID expression is accounted for by those maps. All global, parameter, return, copied, or unproved array types still use the existing unsupported-type diagnostic.
6. Admit `index` only when it matches one exact store/read descriptor. Continue recursively validating the base ID and signed-int index expression, but never add generic index syntax to the capability vocabulary.
7. Add the fixed-table capability to `used` only after a proved declaration/index is encountered. Existing missing-capability logic then fails closed if the schema omits it.

## Emitter changes

In `emit_typed_cpp.py`:

1. Import the fixed-table proof module. In `_Emitter.__post_init__`, validate counted loops, Task 16 counter proof, then the fixed-table proof before source globals. Recompute from the program exactly as the validator does and independently hash `program.raw_source` plus normalized `program.source`, require empty define provenance, and only additionally compare the legacy supplied hash.
2. Retain proof-derived lookup maps on `_Emitter`; never authorize by type alone.
3. Special-case a proved array declaration before `local_type()`:

```cpp
[[maybe_unused]] std::array<double, 9> kernel{};
[[maybe_unused]] std::array<double, 9> sobel_x{};
[[maybe_unused]] std::array<double, 9> sobel_y{};
[[maybe_unused]] std::array<glsl::Vec2, 9> offsets{};
```

The declaration path must reject initializer children even though `{}` is emitted. `<array>` is already included by generated `typed_slice.cpp` for the catalog, so no include expansion is needed.
4. Add an `index` expression branch that emits only proved operations:

```cpp
kernel[0]             // proved literal store target
offsets[i]            // proved counted read
sobel_x[i]
sobel_y[i]
```

Emit the literal value directly as `0` through `8` and the direct local induction name as `i`. Do not call generic `expression()` on an arbitrary subscript tree after authorization.
5. Extend `lvalue()` only for a proved literal-store index. Dynamic or induction-indexed lvalues remain rejected. Proved induction reads are rvalues only.
6. Keep existing assignment precision rules. Scalar array elements are `double`, so scalar table values do not acquire an F32 store. The existing vec2 assignment materialization converts the RHS to `glsl::Vec2`, preserving the F32 lane boundary.
7. Add no bounds checks, `.at()`, `try`, allocation, helper callback, or virtual call. The fixed proof is build-time Python evidence; emitted pixel code contains only local arrays and direct native indexing.

## Fail-closed TDD matrix

Add tests before production changes and observe the expected RED failures. Every forged-tree case keeps authentic retained `TypedProgram.raw_source`, normalized `TypedProgram.source`, spans, and unaffected symbols/proof fields. Provenance-specific cases mutate one retained provenance field while keeping the other fields authentic. Assert rejection by both `validate_capabilities` and `render_typed_cpp`.

### Positive proof and emitter tests

- Both canonical programs receive one proof with exact profile, arrays, positions, induction, reads, payload bytes, and empty define contract.
- Validator and emitter accept only the two exact keys/hashes.
- Emitted declarations match all four exact zero-initialized `std::array` spellings.
- Sharpen has 18 literal stores and two direct induction reads; Sobel has 27 literal stores and three direct induction reads.
- Emitted Task 17 namespaces contain no `.at(`, `std::vector`, `new`, `malloc`, `std::function`, `try`, or `catch`; pixel remains `noexcept`.

### Source, identity, define, and interface negatives

- Wrong key, mutated retained raw source, changed normalized source, swapped Sharpen/Sobel source/key, stale proof, cleared proof, and forged proof fields. A caller-supplied expected raw digest must not rescue mutated `typed.raw_source`.
- Nonempty same-normalized `{"UNRELATED": 1}`, changed-normalized `{"GL_ES": 1}`, changed proof define contract, replaced/removed define provenance after analysis, and a raw-source/define provenance record copied from the other profile.
- Missing/reordered/renamed/wrong-type/wrong-storage required uniform or output; wrong sampler/resource tuple; extra binding declaration.

### Declaration and storage negatives

- Extent 8, 10, or 13; element `int`, `uint`, `vec3`, or the opposite allowed element for a role.
- Global, parameter, return, const, multi-declaration, aggregate initializer, scalar initializer, copied array, alias-like assignment, array constructor, array call argument, array return, member/swizzle/nested-index escape.
- Extra fourth array or missing expected array.

### Initialization negatives

- Missing index, duplicate index, reordered index, index `-1`/`9`, uint literal, dynamic local, `i`, `1+1`, or forged literal metadata.
- Compound assignment, wrong target array, changed scalar payload, changed offset sign/lane/swizzle, RHS type change.
- Read before the ninth store, write after completion, write after the loop, inserted branch/loop/return/break/continue, or relocation of a store into another block while spans remain authentic.

### Reading loop and control negatives

- Initial `i=1`, bound 8/10, `<=`, decrement, prefix update, different induction symbol, `offsets[i+0]`, literal index, uint index, or another local index.
- Missing read, duplicate read, changed role, second reading loop, nested reading loop, loop-body reorder, inserted conditional/control, or array write in the loop.
- Mutate any operator or stable symbol in the exact texture-coordinate expression or convolution update while retaining source bytes and proof.

### Adjacent real-corpus exclusions

Analyze and validate the pinned sources for:

- `filter/celShading:celShadingEdges`
- `filter/outline:outlineSobel`
- `classicNoisedeck/refract:refract`
- `synth/sacredGeometry:sacredGeometry`

Each must still fail at both validator/emitter boundaries and must remain absent from the public catalog.

## Allowlist and generated artifacts

After all proof/validator/emitter tests are green:

1. Add sorted `{}` entries for Sharpen and Sobel to `typed_slice.json`.
2. Change exact typed counts from 108 to 110, public catalog tests from 110 to 112, and publicly unported count from 102 to 100.
3. Update CLI/manifest expectation text to 110 programs.
4. Run `python3 tools/glslcpp/generate_typed_slice.py --write` once; never hand-edit generated output, including `include/noisemaker/generated/catalog.hpp`.
5. Assert the generated manifest contains only the two new keys beyond Task 16 and retains exact binding order from the brief.

## Native binding and oracle wiring

In `tests/test_generated_kernels.cpp`:

- Expand the sorted catalog fixture to 112 and insert Sharpen/Sobel in lexical order.
- For each Task 17 key, start with a complete exact binding set and remove each required name one at a time; every bind must throw `KernelBindingError`.
- Replace each required value with a wrong-kind value one at a time, including a scalar named `inputTex`; every bind must throw.
- Add unrelated extra bindings and prove they do not alter successful binding, matching existing binding semantics.
- Keep all four adjacent profiles absent and returning `std::invalid_argument` from `generated::bind`.

In `tests/test_typed_slice.cpp`:

- Build the frozen 11x9 top-down formula input and render 9x7 output.
- Bind `tileOffset=Vec2(2,1)`, `fullResolution=Vec2(13,11)`, `renderScale=1.0f`, the input sampler, and the case uniforms.
- Bind non-default amount as the exact F32 value `noisemaker::uint_bits_to_float(0x40133333U)` (or equivalent exact-bit helper), never the double literal `2.3`.
- Double-render with fresh input/bindings and compare complete F32 bytes and RGBA8 bytes before hashes.
- Freeze the JSON's three probe pixels `(0,0)`, `(4,3)`, `(8,6)` and all four lane bit patterns for every case.
- Assert these hashes exactly:

| Case | F32 | RGBA8 |
| --- | --- | --- |
| Sharpen default | `54bffb81920b79c85198238c2fcd4f52b94ae25ca208747fb0048f24a71b05ec` | `d1bd7b35b2890258c385d294879556b4586d33f4af29feeeb7be5a4931ec2094` |
| Sharpen 2.3f | `53f12c6e6047f31edb9e157202674a405489df96dd995adcc3bf4aea5a20128f` | `560e7225289764f8d2c108b3f0746859ceb38ce4dee47753710d6d18473101e3` |
| Sobel default alpha one | `df429cbfeb9dc04d3e5f9099ded0daae9ee7077a9121e325a11fb0cd9ac380dd` | `6841efab285a153de30bebaad4a6550107a1de719c37337a159ef07667d76777` |
| Sobel 2.3f alpha zero | `f7e50759990c46d868b22bdf83241e3866b14a6406fee043b8cad46cbea6b1d8` | `05f02465cc5eacd61320b5d1b304f4b8face9993f604f540466d9582075bb3e0` |

Sobel's F32 probes, not RGBA8 saturation, are authoritative for values above one.

## AppleClang stack-usage measurement

Local AppleClang is `16.0.0 (clang-1600.0.26.6)` and advertises both `-fstack-usage` and `-fstack-size-section`. Use fresh build directories; do not change `CMakeLists.txt`:

```sh
cmake -S . -B build-task17-debug \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS="-fstack-usage -fstack-size-section"
cmake --build build-task17-debug -j 8

cmake -S . -B build-task17-release \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-fstack-usage -fstack-size-section"
cmake --build build-task17-release -j 8
```

For each configuration:

1. Locate `CMakeFiles/noisemaker-cpu.dir/src/typed_generated/typed_slice.cpp.su` with `find`.
2. Map generated source markers to the Sharpen/Sobel `typed_N::pixel` qualified names.
3. Record the `.su` byte count and classification (`static`, `dynamic`, or `bounded`) for those exact two pixel functions.
4. Cross-check the typed-slice object with `xcrun llvm-objdump --stack-sizes .../typed_slice.cpp.o` when the Mach-O stack-size section is readable. Treat `.su` as the primary compiler report if the installed objdump cannot decode that section.
5. Record payload separately: Sharpen `9*sizeof(double) + 9*sizeof(glsl::Vec2) = 144` bytes; Sobel `18*sizeof(double) + 9*sizeof(glsl::Vec2) = 216` bytes on the supported target. A native assertion may confirm `sizeof(glsl::Vec2)==8`, but payload is not the full frame.
6. Do not add a frame-size cap until the measured Debug and Release values are reviewed. Report optimizer-elided or scalarized Release storage as measured full-frame behavior, not as a change to the raw logical payload.

## Verification sequence

- [ ] Run the new focused semantic proof tests and observe RED before implementation.
- [ ] Run each validator/emitter mutation group and observe RED before its production change.
- [ ] Run focused tests green after each minimal implementation step.
- [ ] Run `node docs/port-engineering/task-15-oracle-generator.mjs --check`.
- [ ] Run `node docs/port-engineering/task-16-oracle-generator.mjs --check`.
- [ ] Run `node docs/port-engineering/task-17-oracle-generator.mjs --check`.
- [ ] Run `python3 tools/glslcpp/check_corpus.py --check`.
- [ ] Run `python3 tools/glslcpp/check_semantics.py --check`.
- [ ] Run `python3 tools/glslcpp/generate_kernels.py --check`.
- [ ] Run `python3 tools/glslcpp/generate_typed_slice.py --check`.
- [ ] Run the full Python suite.
- [ ] Configure, build, run the direct native binary, and run CTest in fresh strict Debug.
- [ ] Configure, build, run the direct native binary, and run CTest in fresh strict Release.
- [ ] Record 110 typed / 112 public / 100 unported counts.
- [ ] Inspect generated Task 17 hot loops for exact arrays, direct indexing, `noexcept`, and absence of allocation/throwing constructs.
- [ ] Record Debug/Release `.su` stack evidence and raw payload separately.

## Implementation task order

### Task 1: Freeze proof and provenance contracts

- [ ] Add RED semantic tests for exact proof records on both canonical programs and exact empty define provenance.
- [ ] Add RED tests showing a nonempty unused define map prevents proof attachment.
- [ ] Add the typed records and parser provenance.
- [ ] Implement source-specific proof reconstruction and semantic attachment.
- [ ] Run focused semantic tests green.

### Task 2: Make validation fail closed

- [ ] Add RED validator tests for source/key/define/interface drift, declaration/store/read/control mutations, stale proof, and all adjacent exclusions.
- [ ] Add source hashes and independent proof reconstruction to `validate_capabilities`.
- [ ] Admit only proof-described array declarations and index nodes.
- [ ] Run the validator matrix green and re-run all existing Task 16 proof-tamper tests.

### Task 3: Add exact native lowering

- [ ] Add RED emitter tests for both exact `std::array` forms, zero initialization, direct literal/induction indexing, and forbidden constructs.
- [ ] Add emitter proof reconstruction and proof-derived authorization maps.
- [ ] Add the special declaration, expression-index, and lvalue-index lowering.
- [ ] Run emitter negatives and precision assertions green.

### Task 4: Add only the two catalog entries

- [ ] Update schema/count RED tests to 110 typed / 112 public / 100 unported.
- [ ] Add the capability and two sorted keys.
- [ ] Regenerate owned typed outputs once.
- [ ] Run generated drift and exact catalog tests green.

### Task 5: Wire bindings and frozen native oracles

- [ ] Add RED missing/wrong-kind binding tests for every exact binding.
- [ ] Add RED four-case F32/RGBA8/probe/repeatability tests from the frozen JSON.
- [ ] Add the minimal fixtures and bindings.
- [ ] Build and run the focused native cases green.

### Task 6: Run acceptance and stack measurement

- [ ] Run all three oracle `--check` gates and all corpus/semantic/generator drift gates.
- [ ] Run the full Python suite.
- [ ] Run fresh strict Debug direct suite and CTest.
- [ ] Run fresh strict Release direct suite and CTest.
- [ ] Record Debug/Release full-frame `.su` results and 144/216-byte raw payload.
- [ ] Inspect generated hot loops and report exact catalog counts.

## Conflicts and hidden blockers

1. **Independent review is still a hard gate.** This design may be prepared now, but implementation must wait for an approved scope/oracle review and accepted Task 16 baseline.
2. **Raw-source and define provenance are currently absent.** Without retained `raw_source`, emitter can only trust its caller-supplied digest; without the type-tagged `preprocessor_defines`, irrelevant extra defines normalize to identical source. The two proposed frozen fields are the only required typed-program provenance expansion.
3. **A proof limited to array nodes is insufficient.** Task 16's P1 demonstrated that authentic source bytes plus a permissive reconstructed proof can accept forged typed control. Task 17 must hard-code the complete loop-body/read-expression profiles and direct statement positions, then census every array reference.
4. **Stack payload is not frame size.** The 144/216-byte figures cannot be used as a stack cap. AppleClang `-fstack-usage` measurement in both configurations is required; optimization may materially change the full frame.
5. **Scalar precision is easy to regress silently.** `float[9] -> std::array<float,9>` may still pass integral-table cases while violating the canonical storage model. Exact emitted-type assertions are mandatory even though current literals are exactly representable.
6. **Current type vocabulary must remain unchanged.** Adding `float[9]`, `vec2[9]`, or generic `index` to approved vocabularies would broaden the frontier beyond the frozen capability.
7. **No persistent stack flags are needed.** Measurement-only flags should be supplied to fresh CMake build directories; changing project compile flags would be unrelated implementation scope.

## Design conclusion

Task 17 is implementable without runtime or ABI changes. The minimum safe change is retained raw/define provenance, one program-level source-specific proof, two proof-gated emitter operations (array declaration and direct index), two allowlist entries, and frozen native tests. There is no need for general array semantics, checked indexing, heap storage, or changes to the C++ runtime. Implementation remains blocked until the corrected brief receives independent re-review.
