# Task 19 Fixed Array Input Parameter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add exactly `classicNoisedeck/refract:refract` as the sole `fixed-array-in-parameter-v1` program, with its four canonical-JavaScript compatibility no-ops, exact caller/callee array ownership proof, const-reference C++ ABI, and all eight frozen native oracles.

**Architecture:** Keep the existing generic GLSL parser and semantic analyzer unchanged in meaning. After analysis, apply one source-locked Refract compatibility transform, then attach one indivisible post-transform proof that owns the compatibility sites, both caller `Kernel9` tables, the callee `Kernel9` parameter, the callee `Offsets9` table, their exact calls/indices/control ancestry, and the ABI authorization. Validator and emitter independently rebuild counted-loop, Task 16, Task 17, Task 18, and then Task 19 evidence from the retained transformed tree; proof metadata and caller-supplied digests are comparison gates, never authority.

**Tech Stack:** Python 3 frozen dataclasses and typed IR, schema-locked JSON generation, C++20 `std::array`, AppleClang 16 strict Debug/Release builds, the existing native test harness, ASan/UBSan, and compiler `.su` stack records.

## Global Constraints

- Task 18 is now fully accepted; this former gate is cleared.
- No Git command, indirect Git invocation, branch, worktree, commit, push, or pull request is authorized.
- Do not change the runtime, `Surface`, sampler, binding, or resource ABI.
- Admit only `classicNoisedeck/refract:refract`; do not create generic fixed-array, generic array-parameter, pointer, span, template, aliasing, `out`/`inout`, array-return, multidimensional, nested, struct-array, different-extent, or different-element support.
- Preserve Task 17, Task 18, and Sacred Geometry as separate capabilities and profiles.
- Measure before and after; native parity is bitwise F32 first, with RGBA8 as a second check.
- The frozen corrected brief is `docs/port-engineering/task-19-brief.md`, SHA-256 `3eeb2700218edef4edf39060bd3d881c23f90b352608f1894e9c7271f8ed48de`.
- Frozen supporting artifacts are: risk audit `cba1e6b5c9e8f5d95dda761b07c46798e9bdb9ee92a231cdff504e804f8b880e`, generator `a9ff40af61e15c6a73c34a8b844ca2f41da5be1d2ae85e957d2805a8da0d7a30`, JSON `169cb5607777051de3962fdbedd32d7dab4ac2095d6b356041c48bccc3c41c88`, and report `ad053999676b49e0c75907bf66c2ec12678d99934571bfde7d1ebdcd1a113b1d`.
- The final brief-only re-review is approved: `docs/port-engineering/task-19-scope-proof-final-rereview.md`, SHA-256 `e928933336415c89554c6ebe5544b3fc7200c54efc66e80d82785ab228ebf2de`.

---

## Frozen baseline and exact locks

The implementation must freeze these values as named constants and tests, not recalculate and paste new values after implementation drift:

| Lock | Exact value |
| --- | --- |
| Program key | `classicNoisedeck/refract:refract` |
| Raw source SHA-256 | `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2` |
| Normalized source SHA-256 | `bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e` |
| Runtime defines | exactly `()` / `{}` |
| Canonical factory text SHA-256 | `b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6` |
| Pre-transform function tuple SHA-256 | `ccde114d367313d1feb218c7f956df4059534b5c139c757a30ae156292e9cc09` |
| Pre-transform whole-program SHA-256 | `0b2ebb355e506de21ffd829a72302494bd8c77d7bd35fb7f7a5e4b3407ce7003` |
| Interface profile SHA-256 | `36d7815ce5aa9efedf3144e199ae7b49dc5819c751475b815708424269033229` |
| Post-transform function tuple SHA-256 | `4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188` |
| Post-transform whole-program SHA-256 | `93329ab73d54ff1eb3b8ec43da8570365d58de8caaa1a36252ef1ad30a709de2` |

The post-transform values above use one exact representation: each affected assignment retains its statement, assignment, target, and spans, but replaces the conditional RHS with the same typed `middle` identifier as the LHS, producing `middle = middle`. This is the established emitter-compatible no-op representation. If implementation uses any other representation, stop and re-review the design instead of silently changing these locks.

The retained declaration/interface order is exactly:

```text
inputTex:sampler2D@1/S1
resolution:vec2@2
tileOffset:vec2@3
fullResolution:vec2@4
time:float@5
mode:int@6
amount:float@7
direction:float@8
blendMode:int@9
mixAmt:float@10
wrap:int@11
fragColor:vec4 output@12
```

Resources must remain `uniforms=(inputTex,resolution,tileOffset,fullResolution,time,mode,amount,direction,blendMode,mixAmt,wrap)`, `samplers=(inputTex)`, `outputs=(fragColor)`, `uses_texture=True`, and `uses_derivatives=False`. The exact function order/signature IDs are `blend#35`, `blendOverlay#36`, `blendSoftLight#37`, `convolve#38`, `derivX#39`, `derivY#40`, `desaturate#41`, `main#42`, `map#43`, and `periodicFunction#44`.

## Exact compatibility transform

Create transform name `refract-truthy-vector-conditional-noop-v1`. Its order is fixed:

```text
read pinned source -> parse -> analyze and attach existing loop/Task16/17/18 evidence
-> authenticate raw source, normalized source, empty defines, key, interface,
   pre-transform whole-program hash, and pre-transform function hash
-> prove and rewrite exactly four Refract sites
-> authenticate post-transform function hash
-> attach fixed-array-in-parameter-v1 proof
-> validate capabilities
-> emit C++
```

The transform must select the sole defined `vec3 blend(vec4 color1, vec4 color2)` function, its sole fresh uninitialized local `vec4 middle`, and the exact nested `else if` chain with authored mode sequence `0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18`. It rewrites only these normalized-tree sites (raw authored lines are 127, 130, 142, and 166):

| Retained span line | Mode | Predicate | True arm | Exact false tree |
| ---: | ---: | --- | --- | --- |
| 120 | 2 | `color2 == vec4(0.0)` | `color2` | `max(1.0 - ((1.0 - color1) / color2), vec4(0.0))` |
| 123 | 3 | `color2 == vec4(1.0)` | `color2` | `min(color1 / (1.0 - color2), vec4(1.0))` |
| 135 | 7 | `color2 == vec4(1.0)` | `color2` | `min((color1 * color1) / (1.0 - color2), vec4(1.0))` |
| 159 | 15 | `color1 == vec4(1.0)` | `color1` | `min((color2 * color2) / (1.0 - color1), vec4(1.0))` |

Match symbol IDs, types, constructor arity, literal spelling/value, operators, builtin signature IDs, assignment target, statement/assignment/condition/arm spans, guard ancestry, function signature, and the exact false-expression tree. Require the multiset `[(2,color2,0,max),(3,color2,1,min),(7,color2,1,min),(15,color1,1,min)]` once each. Zero, partial, duplicate, extra, reordered-control, or near matches fail. Do not call or reuse generic vector equality semantics.

## Exact proof records and census

### New typed-IR interfaces

Add these frozen records to `tools/glslcpp/frontend/typed_ir.py`:

```python
@dataclass(frozen=True, slots=True)
class RefractCompatibilitySiteProof:
    blend_mode: int
    guard_span: SourceSpan
    assignment_statement_span: SourceSpan
    assignment_span: SourceSpan
    target_symbol_id: int
    source_symbol_id: int
    equality_constant: float
    false_builtin: str
    original_condition_span: SourceSpan
    original_false_span: SourceSpan
    transformed_rhs_span: SourceSpan

@dataclass(frozen=True, slots=True)
class FixedArrayOwnedTableProof:
    role: str
    owner_signature_id: int
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_alias: str
    declaration_statement_index: int
    declaration_span: SourceSpan
    literal_store_statement_indices: tuple[int, ...]
    literal_store_spans: tuple[SourceSpan, ...]
    literal_index_spans: tuple[SourceSpan, ...]
    literal_indices: tuple[int, ...]
    number_values: tuple[float, ...] | None
    induction_read_spans: tuple[SourceSpan, ...]

@dataclass(frozen=True, slots=True)
class FixedArrayParameterProof:
    owner_signature_id: int
    parameter_ordinal: int
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    direction: str
    native_abi: str
    induction_read_spans: tuple[SourceSpan, ...]
    reads_per_iteration: int
    direct_call_spans: tuple[SourceSpan, ...]
    direct_argument_spans: tuple[SourceSpan, ...]

@dataclass(frozen=True, slots=True)
class FixedArrayInParameterProof:
    proof_kind: str
    source_profile: str
    raw_source_sha256: str
    normalized_source_sha256: str
    canonical_factory_sha256: str
    define_contract: tuple[PreprocessorDefine, ...]
    binding_signature: tuple[str, ...]
    compatibility_sites: tuple[RefractCompatibilitySiteProof, ...]
    kernel_alias: str
    offsets_alias: str
    caller_tables: tuple[FixedArrayOwnedTableProof, ...]
    parameter: FixedArrayParameterProof
    offset_table: FixedArrayOwnedTableProof
    convolve_loop_span: SourceSpan
    induction_symbol_id: int
    loop_trip_count: int
    lexical_product: int
    entrypoint_charge: int
    main_signature_id: int
    mode_one_span: SourceSpan
    main_derivative_call_spans: tuple[SourceSpan, ...]
    array_parameter_count: int
    array_declaration_count: int
    array_typed_expression_count: int
    array_identifier_reference_count: int
    literal_store_count: int
    induction_read_count: int
    index_expression_count: int
    whole_array_argument_count: int
    array_call_count: int
    no_alias_copy_escape_return_or_post_call_use: bool
    complete_initialization_dominates_reads: bool
    caller_tables_never_simultaneously_live: bool
    parameter_read_only_and_synchronous: bool
    mode_zero_array_free: bool
    raw_simultaneous_payload_bytes: int
    interface_sha256: str
    typed_ir_sha256: str
    whole_program_sha256: str
```

Append `fixed_array_in_parameter_proof: FixedArrayInParameterProof | None = None` to `TypedProgram`. The proof module must expose:

```python
CAPABILITY = "fixed-array-in-parameter-v1"
REFRACT_KEY = "classicNoisedeck/refract:refract"

def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None: ...

def prove_fixed_array_in_parameter(
    program: TypedProgram,
) -> FixedArrayInParameterProof | None: ...

def attach_fixed_array_in_parameter_proof(
    program: TypedProgram,
) -> TypedProgram: ...
```

`attach_fixed_array_in_parameter_proof` first clears only its own field, proves the passed post-transform tree, and installs the returned proof. It returns the input with a `None` Task 19 field for every other key. Do not call it from `analyze_program`: the raw analyzed Refract tree is intentionally pre-transform. Call it only after compatibility transformation in generation and explicitly in focused tests.

### Hard-coded structural profile

The proof must reconstruct these exact facts, not infer a broader pattern:

- `convolve#38` is `vec3(vec2 uv#18, in float[9] kernel#19, bool divide#20)` with 17 top-level statements. `offset#51` is statement 2; literal stores 0..8 are statements 3..11; `kernelWeight` and `conv` are statements 12 and 13; the sole loop is statement 14; the divide conditional is 15; return is 16.
- `offset#51` has exact `Offsets9` values from `steps#50`: `(-x,-y)`, `(0,-y)`, `(x,-y)`, `(-x,0)`, `(0,0)`, `(x,0)`, `(-x,y)`, `(0,y)`, `(x,y)`. Each RHS is the exact typed `vec2` constructor tree, and every assignment crosses the F32 `glsl::Vec2` storage boundary.
- The loop is exact `int i#54=0; i<9; ++i`, body count 3, trip count 9, lexical/effective depth 1, lexical product 9, entrypoint charge 18. It reads `offset[i]` once in the texture-coordinate tree, `kernel[i]` once in `conv += color * kernel[i]`, and `kernel[i]` once in `kernelWeight += kernel[i]`.
- `derivX#39` has 13 top-level statements. `deriv_x#57` is statement 1; stores are statements 2..10 with Number values `(0,0,0,0,1,-1,0,0,0)`; statement 11 initializes `s1` with the sole resolved `convolve#38(uv#23, deriv_x#57, divide#24)` call; statement 12 returns `s1`.
- `derivY#40` is analogous with `deriv_y#60`, Number values `(0,0,0,0,1,0,0,-1,0)`, and `convolve#38(uv#26, deriv_y#60, divide#27)`.
- Both caller declarations are fresh, zero-initialized natively, fully written at literal indices 0..8 before their call, and have no read, alias, copy, return, store, further pass, second call, or post-call reference. Their helper activations are serial, so only one 72-byte caller table can coexist with the callee table.
- `main#42` has 14 top-level statements. Statement 8 is the exact `mode==0` / `else if mode==1` chain. The mode-one block has exactly two statements: `derivX#39(inputColor.rgb,uv,false)` followed by `derivY#40(inputColor.rgb,uv,false)`. No array-bearing function is reachable from mode zero.
- `kernel#19` is read-only and nonescaping. Its only two identifier references are the two `kernel[i]` rvalues. It is never an lvalue, whole-value expression, assignment source/target, return, store, callback input, or argument to another call.
- The recursive census is exactly: one array parameter, three local array declarations, 35 array-typed expressions, 32 array identifier references, 27 literal stores, three induction reads, 30 index expressions, two whole-array arguments, and two resolved array-bearing calls. The four identities are only `kernel#19`, `offset#51`, `deriv_x#57`, and `deriv_y#60`.
- The proof reports aliases `Kernel9` and `Offsets9`, parameter ABI `const Kernel9&`, and raw simultaneous table payload 144 bytes. A 216-byte by-value profile is not representable.

The whole-program hash input must be the Task 18 ordering plus its proof field and excluding only the Task 19 proof being reconstructed:

```python
(
    program.key, program.source, program.raw_source, program.declarations,
    program.functions, program.resources, program.body_status,
    program.local_type_names, program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols,
    program.counted_loop_proof, program.preprocessor_defines,
    program.fixed_nine_table_proof,
    program.fixed_grid_counter_store_proof,
)
```

## Exact validator/emitter reconstruction and site authorization

Both `validate_capabilities` and `_Emitter.__post_init__` must use this reconstruction order:

```python
counted = attach_counted_loop_proofs(program.functions, program.key)
counter = attach_discarded_local_counter_proofs(counted, program.key)
base = dataclasses.replace(
    program,
    functions=counter,
    fixed_nine_table_proof=None,
    fixed_grid_counter_store_proof=None,
    fixed_array_in_parameter_proof=None,
)
fixed_nine = prove_fixed_nine_local_tables(base)
fixed_grid = prove_fixed_grid_counter_store(
    dataclasses.replace(base, fixed_nine_table_proof=fixed_nine))
task19 = prove_fixed_array_in_parameter(dataclasses.replace(
    base,
    fixed_nine_table_proof=fixed_nine,
    fixed_grid_counter_store_proof=fixed_grid,
))
```

For the Refract key, independently authenticate `source_provenance_error`, require non-`None` reconstruction, and require exact equality with the carried proof. For all other keys, a non-`None` Task 19 proof is malformed. This rejects raw/untransformed Refract, partial transform, altered no-op, attacker-updated hashes, stale proof, and cleared proof at both boundaries.

Validator authorization is a span-and-role census, not a type-wide exception:

- Permit array declarations only for the three proof-recorded declaration `(symbol, span, type)` triples.
- Permit the array parameter only for the one proof-recorded `(convolve signature, ordinal 1, symbol, span, direction, type)` tuple.
- Permit whole-array identifiers only at the two caller argument spans; the callee parameter is not permitted as a whole value anywhere.
- Permit literal-index lvalues only at the 27 registered store spans.
- Permit induction-index rvalues only at the three registered read spans with `i#54`.
- Reject array types before generic expression handling everywhere else. Add the capability to `used` only when one of those exact sites is consumed.
- Keep ordinary parameter direction rejection unchanged; the one array parameter remains exact direction `in`.

Emitter authorization mirrors those same sites independently:

```cpp
using Kernel9 = std::array<double, 9>;
using Offsets9 = std::array<glsl::Vec2, 9>;
static_assert(sizeof(Kernel9) == 72U);
static_assert(sizeof(Offsets9) == 72U);
```

Emit those aliases only inside the proved Refract namespace. Emit exactly `Kernel9 deriv_x{};`, `Kernel9 deriv_y{};`, and `Offsets9 offset{};`. Add a `function_parameter_type(function, parameter)` helper: it returns `const Kernel9&` only for the proof-recorded `convolve#38` parameter and delegates non-array types to existing `function_type`; any other array parameter raises `TypedEmissionError`. Use it in both helper forward declarations and definitions, yielding two exact occurrences of:

```cpp
[[nodiscard]] glsl::Vec3 convolve(
    [[maybe_unused]] const State& state,
    [[maybe_unused]] const glsl::PixelContext& context,
    [[maybe_unused]] glsl::Vec2 uv,
    [[maybe_unused]] const Kernel9& kernel,
    [[maybe_unused]] bool divide) noexcept;
```

Keep direct `operator[]`: literal stores/reads emit `[0]` through `[8]`; induction reads emit `[static_cast<std::size_t>(i)]` to avoid signed-index warnings. Do not emit `.at()`, raw pointers, spans, vectors, templates, array copies/returns, `new`, callbacks, virtual calls, runtime maps/variants/strings, or throwing code in the Refract pixel/helper namespace. This prohibition is about the new array execution path; the existing generated bind factory continues to use the shared `Bindings`/`make_shared<State>` infrastructure outside that namespace and must not be redesigned in Task 19.

## Both-boundary TDD mutation matrix

Use one helper that produces the authentic transformed-and-attached program, one recursive first-expression mutator, one statement mutator, and one assertion helper that runs both `validate_capabilities(..., source_hash=raw_hash)` and `render_typed_cpp(...)`. Every candidate below must fail both boundaries; for proof modes, test carried authentic proof, cleared proof, stale proof, and an attacker-replaced proof whose `typed_ir_sha256`, `interface_sha256`, and `whole_program_sha256` are updated to hashes of the forged tree.

| Boundary group | Required mutations |
| --- | --- |
| Provenance/identity | wrong key; retained raw source changed; normalized source changed; empty defines replaced by unrelated and source-changing defines; caller source digest changed; factory-hash proof field changed; declaration/binding reordered; uniform type/storage changed; sampler/output/resources changed; `uses_texture`/`uses_derivatives` changed; struct, UBO, varying, or global added |
| Compatibility transform | wrong transform name/key/signature; missing mode 2/3/7/15 site; duplicated site; extra transformed conditional; changed guard mode/order/ancestry; changed target; operand swapped; constant changed; true symbol changed; false builtin changed; any false subtree operator/operand changed; untransformed scalar-vector conditional; one restored conditional; transformed RHS changed from exact self-id |
| Caller declarations/stores | extent 8/10; element `vec2`; initializer added; storage/name/writable/symbol identity changed; store missing/duplicated/reordered; literal index changed, dynamic, or out of range; RHS Number changed; unary `-1.0` changed; conditional/loop/return inserted between declaration, stores, and call; pre-call read; alias/copy; second pass/call; post-call use |
| Call boundary | target/signature changed; array moved from argument two; argument reordered/removed/duplicated; caller array passed to another function; `derivX` uses `deriv_y` or vice versa; call moved before initialization; second `convolve` call |
| Callee parameter | direction `out`/`inout`; extent/element/name/ordinal/signature changed; write/update/index lvalue; whole-value copy/assignment/return/store; pass onward; additional read; literal index; different induction symbol; parameter ABI proof changed to `Kernel9`, `Kernel9&`, pointer, or span |
| Offset table | declaration/extent/element/initializer changed; any of nine constructors, signs, `steps` lane, index, value, order, or span changed; missing/duplicate store; read before full initialization; post-init or in-loop write; escape/pass/return |
| Loop/control | start/bound/comparison/update kind changed; loop proof forged; induction identity changed; trip/depth/product/charge changed; body statement order/count changed; `offset[i]` count not one; `kernel[i]` count not two; break/continue/return/conditional added; loop moved before stores |
| Main reachability/liveness | mode 0/1 guard changed; derivative order reversed; divide changed from false; call moved outside mode one; array helper reachable in mode zero; simultaneous nested derivative activation or retained caller reference |
| Exclusions/regressions | analogous array parameter in another key; other extent/element; nested/multidimensional/struct array fixtures; Sacred Geometry; all Task 17/18 positive fixtures; forged Task 17/18 proof cross-use |

## Frozen eight-case native contract

Add `Task19Case`, `task19_formula_surface()`, and `render_task19()` to `tests/test_typed_slice.cpp`. The input is top-down 11x9 with each assignment cast through `float`:

```cpp
R = static_cast<float>(((17*x + 31*y + 13) % 101) / 100.0);
G = static_cast<float>(((7*x + 19*y + 23) % 97) / 96.0);
B = static_cast<float>(((29*x + 11*y + 5) % 89) / 88.0);
A = static_cast<float>(0.25 + ((3*x + 5*y + 1) % 13) / 20.0);
```

Bind all eleven fields: `inputTex`, `resolution=Vec2(9,7)`, `tileOffset=Vec2(128,64)`, `fullResolution=Vec2(1024,768)`, `time=0.375f`, exact `mode`, F32-bit-derived `amount`, F32-bit-derived `direction`, exact `blendMode`, F32-bit-derived `mixAmt`, and exact `wrap`. Render 9x7 with `run_pass(...,0.375f,19.0f,7U,1.0f/60.0f)`. Double-render each case from fresh input and destination surfaces; compare the complete F32 bytes, complete RGBA8 bytes, shape, repeat identity, and probe pixels 0, 31, and 62.

| Case | mode/amount bits/direction bits/blend/mix bits/wrap | F32 / RGBA8 SHA-256 | 12 probe words |
| --- | --- | --- | --- |
| mirror difference under half | `1/415b3333/42150000/5/41bb3333/0` | `d173f4368e000081b9b3921caccfd02790284c025ad5bd69d605f7310a23e2e2` / `9f345b48aafb6d69ec9d7757a161f86a103e92a7a2efdadd5eba5d3b8b7ad8c3` | `3f306cca 3f05f672 3e8f79f3 3e99999a 3e645a1d 3eb07827 3f3904a8 3eb33333 3f3721d5 3ed1d037 3eb63fad 3f59999a` |
| repeat overlay half | `1/41ef3333/4309999a/13/42480000/1` | `6e02e60356ea964074be3b941e5ef976eeb5dfd4ee12041b8ab5cae484f2dea2` / `e71609cfd1cfba0c3977abceb360939d22638858df33e02b551783f87d0c0fc1` | `3f10a3d7 3ee41c73 3d0ecf57 3e99999a 3f0d013b 3f0a8000 3f7c4c2b 3e800000 3f70068e 3f22638e 3f467ab6 3f59999a` |
| clamp soft-light over half | `1/4292cccd/43879000/17/429dcccd/2` | `3d38aee57222eb8460953f2a1e86418992f60c220b668b357d63f260346db56b` / `25152ac17ca38d55d15e1c7f02c5cea715f659e9f4d2bc04cffbd58b10d4aa86` | `3eaa8a71 3eb61f4d 3da9812c 3e99999a 3da2c5db 3f312337 3f644233 3f59999a 3f2c54bc 3f33d3ae 3f3008d5 3f59999a` |
| mode-zero mirror control | `0/422ccccd/419e0000/10/42480000/0` | `3d791dbae4d93b61ab31f06b88105678c751ea3d369be9705661ed3a29879a0e` / `24841a3ec260bb15d549f066207c52a2e82be2fa22743d81feb1995201f28af9` | `3ee147ae 3ee00000 3e3a2e8c 3e99999a 3eee147a 3f295556 3f045d17 3eb33333 3f43d70a 3f195555 3eb45d18 3eb33333` |
| truthy typed-array no-op, modes 2, 3, 7, 15 (four separate cases) | each `1/41ef3333/4309999a/{2,3,7,15}/42480000/1` | each `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` / `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0` | each `00000000 00000000 00000000 3e99999a 00000000 00000000 00000000 3e800000 00000000 00000000 00000000 3f59999a` |

Do not merge the last four rows into one runtime iteration without four named fixtures; acceptance requires eight named cases. The scalar-boolean mutant hashes remain diagnostic-only and do not enter native expected output.

## File map

- Create `tools/glslcpp/frontend/refract_compatibility.py`: source/pre-tree locks, exact four-site matcher, canonical `middle=middle` rewrite, post-tree check.
- Create `tools/glslcpp/frontend/fixed_array_in_parameter_proof.py`: provenance, hard-coded post-transform whole-program/interface/function locks, recursive census, ownership/liveness/control/call proof, ABI record.
- Modify `tools/glslcpp/frontend/typed_ir.py`: add the four frozen proof record types and trailing Task 19 proof field.
- Modify `tools/glslcpp/generate_typed_slice.py`: import the transform/proof, schema-lock the fifth transform, add the capability, attach proof after transform, rebuild proof in validation, authorize exact sites, update 113-program diagnostics.
- Modify `tools/glslcpp/emit_typed_cpp.py`: independently rebuild Task 19 proof, add exact array declarations/indices/whole arguments, emit Refract-only aliases and exact const-reference parameter ABI.
- Modify `tools/glslcpp/typed_slice.json`: add capability, transform mapping, and sorted Refract key with empty defines.
- Modify `tests/test_semantic.py`: positive post-transform proof, census, ownership, values, loop, liveness, ABI, hashes, and provenance assertions.
- Modify `tests/test_typed_generator.py`: transform exactness; both-boundary mutation matrix; code shape; schema, count, exclusion, generation, and manifest assertions.
- Modify `tests/test_generated_kernels.cpp`: catalog factory declaration plus all eleven required binding missing/wrong-type cases and unrelated-entry acceptance.
- Modify `tests/test_typed_slice.cpp`: exact eight-case native fixture and oracle assertions.
- Regenerate, never hand-edit, `include/noisemaker/generated/catalog.hpp`, `src/typed_generated/typed_manifest.json`, and `src/typed_generated/typed_slice.cpp`.
- Do not modify `CMakeLists.txt`, runtime headers/sources, corpus files, or frozen `/tmp` oracle artifacts.

---

### Task 1: Freeze the Refract compatibility transform

**Files:**
- Create: `tools/glslcpp/frontend/refract_compatibility.py`
- Modify: `tools/glslcpp/generate_typed_slice.py:176-409`
- Test: `tests/test_typed_generator.py` compatibility-transform section

**Interfaces:**
- Produces: `TRANSFORM = "refract-truthy-vector-conditional-noop-v1"` and `apply_refract_truthy_vector_noops(program: TypedProgram) -> TypedProgram`.
- Guarantees: exact pre-lock authentication, four exact structural matches, exact `middle=middle` representation, and post function hash `4c9e125c...`.

- [ ] **Step 1: Write failing transform tests** for the authentic source, exact four no-ops, no emitted vector-equality ternaries, and every compatibility mutation group listed above.
- [ ] **Step 2: Run RED:** `python3 tests/test_typed_generator.py TypedGeneratorTests.test_refract_truthy_vector_conditionals_transform_is_exact_and_source_locked`; expect missing transform/import failures.
- [ ] **Step 3: Implement the transform** with full recursive false-tree checks and exact pre/post hash assertions; dispatch it from `apply_compatibility_transform` without changing existing transforms.
- [ ] **Step 4: Run GREEN:** rerun the exact command and `python3 tests/test_typed_generator.py TypedGeneratorTests.test_compatibility_transform_contract_rejects_extra_keys_and_unknown_modes`.

### Task 2: Add the indivisible post-transform ownership proof

**Files:**
- Create: `tools/glslcpp/frontend/fixed_array_in_parameter_proof.py`
- Modify: `tools/glslcpp/frontend/typed_ir.py:84-245,334-353`
- Test: `tests/test_semantic.py:19-145`

**Interfaces:**
- Consumes: the exact post-transform `TypedProgram` from Task 1.
- Produces: the dataclasses and `attach_fixed_array_in_parameter_proof()` / `prove_fixed_array_in_parameter()` signatures specified above.

- [ ] **Step 1: Write the positive semantic proof test** asserting every exact identity, body index, values tuple, offset tuple, call, census count, ownership boolean, ABI string, 144-byte payload, and lock.
- [ ] **Step 2: Run RED:** `python3 tests/test_semantic.py SemanticTests.test_refract_post_transform_retains_exact_fixed_array_input_parameter_proof`; expect the missing proof field.
- [ ] **Step 3: Implement the proof** using recursive statement/expression walkers, exact structural helpers for declarations/literals/calls/loops/control, and the hard-coded post-transform locks.
- [ ] **Step 4: Run GREEN** with the Step 2 command and the existing Task 17/18 semantic proof tests.

### Task 3: Make validation fail closed at every Task 19 boundary

**Files:**
- Modify: `tools/glslcpp/generate_typed_slice.py:41-83,92-145,730-1135,1144-1180,1299`
- Modify: `tools/glslcpp/typed_slice.json`
- Test: `tests/test_typed_generator.py:27-792,1359-1687`

**Interfaces:**
- Consumes: Task 2 proof.
- Produces: exact capability/site authorization and 113-key schema contract.

- [ ] **Step 1: Add both-boundary mutation tests** covering every row of the mutation matrix and every proof mode; keep validator and emitter assertions paired in the same loop.
- [ ] **Step 2: Run RED:** the new focused mutation tests must fail first at unsupported array parameter or missing proof reconstruction.
- [ ] **Step 3: Add `fixed-array-in-parameter-v1` and exact site sets**, use the reconstruction order above, and allow only registered declarations, arguments, stores, and reads.
- [ ] **Step 4: Add the sorted Refract JSON entry and fifth transform mapping**, update exact schema checks from 112 to 113, exact public/unported arithmetic to 115/97, and CLI text to `typed slice ok (113 programs)`.
- [ ] **Step 5: Run GREEN:** focused mutation, schema, count, Task 17, Task 18, Refract exclusion-replacement, and Sacred Geometry exclusion tests.

### Task 4: Emit only the exact const-reference ABI and direct indices

**Files:**
- Modify: `tools/glslcpp/emit_typed_cpp.py:13-245,518-573,610-625,790-925,1000-1065`
- Test: `tests/test_typed_generator.py`

**Interfaces:**
- Consumes: exact Task 19 proof and registered spans.
- Produces: Refract-only `Kernel9`, `Offsets9`, `const Kernel9&`, zero-initialized tables, and direct indexing.

- [ ] **Step 1: Write RED code-shape tests** asserting aliases/static sizes, exactly one each of `Kernel9 deriv_x{};`, `Kernel9 deriv_y{};`, `Offsets9 offset{};`, two `const Kernel9& kernel` signatures, exact calls, and direct indices; assert absence of by-value/non-const/pointer/span/copy/heap/throwing/scalar-vector-ternary shapes.
- [ ] **Step 2: Run RED:** expect `function_type(float[9])` or unsupported array errors.
- [ ] **Step 3: Implement independent proof reconstruction, parameter-specific type rendering, declaration aliases, and exact index helpers**. Do not add arrays to `_TYPES` or make `function_type` generically understand arrays.
- [ ] **Step 4: Run GREEN** for code-shape plus the complete Task 17/18 emitter tests.

### Task 5: Regenerate the catalog and verify binding ownership

**Files:**
- Modify: `tests/test_generated_kernels.cpp`
- Regenerate: `include/noisemaker/generated/catalog.hpp`
- Regenerate: `src/typed_generated/typed_manifest.json`
- Regenerate: `src/typed_generated/typed_slice.cpp`

**Interfaces:**
- Produces: `bind_classicNoisedeck_refract_refract`, sorted 115-entry public catalog, 113 typed manifest records.

- [ ] **Step 1: Write RED factory/catalog/binding tests**: one factory pointer, exact sorted key, missing and wrong-type rejection for all eleven bindings, and acceptance with unrelated uniform/texture entries.
- [ ] **Step 2: Run RED native compilation** in a temporary Debug build; expect the missing generated factory declaration.
- [ ] **Step 3: Run** `python3 tools/glslcpp/generate_typed_slice.py --write`; inspect the Refract namespace and manifest record before testing.
- [ ] **Step 4: Run** `python3 tools/glslcpp/generate_typed_slice.py --check` and the catalog/binding native tests; expect 113 typed and 115 public.

### Task 6: Wire all eight direct canonical native oracles

**Files:**
- Modify: `tests/test_typed_slice.cpp:2743-end`

**Interfaces:**
- Consumes: the exact fixture bits, hashes, and probes in this plan.
- Produces: `typed_task19_refract_external_oracles_are_exact_and_repeatable` with eight named cases.

- [ ] **Step 1: Add the exact input generator, binding helper, eight fixtures, hashes, probes, shape/orientation checks, and fresh double-render identity.**
- [ ] **Step 2: Run RED before regeneration/emitter completion** and record only the actual mismatch/factory absence, never replace frozen expected hashes.
- [ ] **Step 3: Run the direct native executable in Debug and Release**; require every case to match F32, RGBA8, probes, and repeat identity.
- [ ] **Step 4: Re-run** `node docs/port-engineering/task-19-oracle-generator.mjs --check`; require `ok task-19-oracles.json`.

### Task 7: Full verification, sanitizers, code shape, and stack accounting

**Files:**
- No production files.
- Write the final implementation report only to the task-authorized report path selected by the parent task.

**Interfaces:**
- Produces: reproducible parity, sanitizer, drift, code-shape, and full dynamic stack evidence.

- [ ] **Step 1: Run the full Python suite:** `python3 -m unittest discover -s tests -p 'test_*.py'`.
- [ ] **Step 2: Run every drift gate:**

```bash
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
for task in 15 16 17 18 19; do node "docs/port-engineering/task-${task}-oracle-generator.mjs" --check; done
```

- [ ] **Step 3: Configure strict stack-instrumented builds outside the repository:**

```bash
cmake -S . -B /tmp/noisemaker-for-cpp-task19-debug \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section'
cmake --build /tmp/noisemaker-for-cpp-task19-debug --parallel
/tmp/noisemaker-for-cpp-task19-debug/noisemaker-cpu-tests
ctest --test-dir /tmp/noisemaker-for-cpp-task19-debug --output-on-failure

cmake -S . -B /tmp/noisemaker-for-cpp-task19-release \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-fstack-usage -fstack-size-section'
cmake --build /tmp/noisemaker-for-cpp-task19-release --parallel
/tmp/noisemaker-for-cpp-task19-release/noisemaker-cpu-tests
ctest --test-dir /tmp/noisemaker-for-cpp-task19-release --output-on-failure
```

- [ ] **Step 4: Run supported sanitizers in a separate build:**

```bash
cmake -S . -B /tmp/noisemaker-for-cpp-task19-sanitize \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer' \
  -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build /tmp/noisemaker-for-cpp-task19-sanitize --parallel
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1 \
  /tmp/noisemaker-for-cpp-task19-sanitize/noisemaker-cpu-tests
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1 \
  ctest --test-dir /tmp/noisemaker-for-cpp-task19-sanitize --output-on-failure
```

AppleClang 16 on arm64 Darwin accepts both `-fstack-usage -fstack-size-section` and `-fsanitize=address,undefined`; this was verified read-only with driver `-###`. If leak detection itself is unavailable on the host runtime, rerun ASan/UBSan with `detect_leaks=0`, record that host limitation, and do not label LeakSanitizer as passed.

- [ ] **Step 5: Extract full `.su` evidence** from each build's `typed_slice.cpp*.su`. Record every row whose demangled name is Refract `pixel`, `derivX`, `derivY`, `convolve`, or an optimizer-created/inlined clone, including byte count and compiler `static`/`dynamic` classification.
- [ ] **Step 6: Measure the maximum dynamic mode-one call path.** In a non-inlined build, report:

```text
max(
  frame(pixel) + frame(derivX) + frame(convolve),
  frame(pixel) + frame(derivY) + frame(convolve)
)
```

Do not sum `derivX` and `derivY`; their calls are serial. If Release retains calls, use the same formula with Release frames. If Release inlines one or more helpers, report the containing `pixel`/clone frame and prove containment with both symbol and disassembly evidence:

```bash
nm -nm /tmp/noisemaker-for-cpp-task19-release/CMakeFiles/noisemaker-cpu.dir/src/typed_generated/typed_slice.cpp.o | c++filt | rg 'typed_[0-9]+::(pixel|derivX|derivY|convolve)'
otool -tvV /tmp/noisemaker-for-cpp-task19-release/CMakeFiles/noisemaker-cpu.dir/src/typed_generated/typed_slice.cpp.o | c++filt > /tmp/noisemaker-for-cpp-task19-release/refract-disassembly.txt
rg -n 'typed_[0-9]+::(pixel|derivX|derivY|convolve)|\bbl\b' /tmp/noisemaker-for-cpp-task19-release/refract-disassembly.txt
```

Keep the measured compiler frame/call-chain maximum separate from the proved 144-byte raw live table payload. Also report `sizeof(Kernel9)=72`, `sizeof(Offsets9)=72`, and that by-value would have produced 216 raw simultaneous bytes.

- [ ] **Step 7: Inspect exact generated code shape** within only the Refract namespace: const reference present; two caller zero-inits and one offset zero-init; exact direct indices; exact self-assignment no-ops; no scalar `Vec4 ==` ternary; no by-value array parameter/copy; no pointer/span/vector/heap/throwing/virtual/callback constructs.
- [ ] **Step 8: Run the writing-plans self-review:** map every corrected brief requirement to a task above, scan this implementation and its tests for missing mutation categories, and verify dataclass/type/function names are identical across proof, validator, emitter, and tests.

## Hidden blockers and stop conditions

1. **Post-transform proof ordering is mandatory.** Attaching Task 19 inside `analyze_program` would prove the wrong tree and reopen the untransformed-IR hole. Stop review if implementation does that.
2. **The proposed post-transform hashes depend on exact `middle=middle` representation.** A deleted statement or a different synthetic expression requires renewed design review and new frozen locks; it is not a mechanical substitution.
3. **Generic `reject_type` and `function_type` currently reject array parameters.** The fix must be exact span/signature authorization, not adding `float[9]` to global type vocabulary or `_TYPES`.
4. **Oracle output cannot expose six zero-weight offsets.** The exact values for offset indices 0,1,2,3,6,8 are structural proof obligations; native hashes only prove those reads executed, not that those values influenced output.
5. **Release may inline all three helpers.** A missing standalone `.su` row is not zero stack and not permission to omit evidence; use the containing frame plus `nm`/disassembly evidence.
6. **ASan/UBSan and stack builds must stay separate.** Sanitizer-inflated frames are not acceptance stack measurements.
7. **The generated translation unit contains catalog throwing code outside Refract.** Code-shape absence checks for exceptions/allocation must be scoped to the Refract namespace, while the ABI/copy checks may target the exact helper signature and array names.
8. **All eleven uniforms are required even when source logic does not use `time` materially.** Binding tests must not collapse to metadata defaults; the generated State constructor reads every source uniform.
9. **The canonical factory text is not retained in the C++ typed IR.** Validator/emitter can reconstruct the source/tree/interface proof and compare the profile's frozen factory-hash constant, but they cannot independently re-hash JavaScript factory text without adding a forbidden runtime/repository dependency. Live factory-text authentication remains the direct `/tmp` oracle generator's responsibility and must be reported as such.
10. **The existing bind factory uses maps/variants/strings and `make_shared<State>` before execution.** The brief's no-allocation/no-runtime-container rule must be enforced on the new array lowering and pixel/helper path. Treating it as a ban on the pre-existing bind architecture would require an unauthorized runtime ABI redesign and must stop for scope clarification.
11. **No implementation is complete at generator success alone.** Completion requires both strict configurations, all eight native cases, CTest, sanitizer result, drift/oracle checks, exact code-shape inspection, and full dynamic stack accounting.
