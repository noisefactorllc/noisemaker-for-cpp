# Task 28 Rotate `mat2` Return Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use
> `superpowers:subagent-driven-development`. Apply strict TDD, preserve review
> checkpoints, and run no Git operation.

**Goal:** Add only `filter/rotate:rot` with exact public pixel parity and an
identity-locked by-value `mat2` helper return.

**Architecture:** Add one standalone authentication profile and one optional
per-row carrier. Validator and emitter authenticate independently; validator
bypasses only its blanket matrix-return rejection for the exact function
object. Existing emitter/runtime matrix construction and multiplication stay
unchanged.

**Tech stack:** Python typed GLSL frontend/generator, generated C++20,
AppleClang/CMake/CTest, Node public CPU oracle.

## Global constraints

- Frozen brief SHA-256:
  `57291c23f8c42145efa25cda83efeb962ef82bb53849242aa1585d9224d3dbcd`.
- Exact program/profile only: `filter/rotate:rot` /
  `rotate-mat2-return-v1`, defines `{}`, `glsl-f32`.
- No parser, typed-IR, runtime, CMake, corpus, existing profile, compatibility,
  adapter, branch, worktree, PR, commit, push, or deployment change.
- Owned files are only the new profile; generator; emitter; slice spec; two
  test files; and three canonical generated artifacts.
- Stop on any frozen source/tree/interface/factory/oracle/Task27 drift.

## File map

- Create `tools/glslcpp/frontend/rotate_mat2_return_profile.py`: exact
  authenticator and identity apply.
- Modify `tools/glslcpp/generate_typed_slice.py`: import, schema/census,
  pipeline wiring, validator carrier and one exact return bypass, manifest.
- Modify `tools/glslcpp/emit_typed_cpp.py`: independent carrier authentication
  and mandatory/exclusive closure; no expression/function emission change.
- Modify `tools/glslcpp/typed_slice.json`: one sorted Rotate row.
- Modify `tests/test_typed_generator.py`: profile, matrices, negative closure,
  exact generation, isolation, table transcription/tampering, census updates.
- Modify `tests/test_generated_kernels.cpp`: six public cases, ABI failures,
  six-mode direct matrix harness and witnesses.
- Regenerate `src/typed_generated/typed_slice.cpp`,
  `src/typed_generated/typed_manifest.json`, and
  `include/noisemaker/generated/catalog.hpp` canonically.

### Task 1: Freeze preflight and write the failing profile test

**Produces:** authenticated exact objects or a fail-closed `ValueError`.

- [ ] Verify all Task28 artifact sidecars, run recomputation, oracle `--check`,
  corpus `--check`, generator `--check`, current hashes/counts, and fresh
  warnings-as-errors Debug CTest.
- [ ] Add a focused test that imports
  `authenticate_rotate_mat2_return`/`apply_rotate_mat2_return`, supplies exact
  Rotate, and asserts returned tuple object identities `(helper, constructor,
  call, parent)` plus `apply(...) is program`.
- [ ] Run it and preserve RED as missing module.
- [ ] Implement constants `PROFILE = "rotate-mat2-return-v1"` and
  `ROTATE_KEY = "filter/rotate:rot"`, typed traversal utilities, independent
  whole/interface/profile fingerprints, and:

```python
def authenticate_rotate_mat2_return(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> tuple[TypedFunction, TypedExpression, TypedExpression, TypedExpression]:
    ...

def apply_rotate_mat2_return(
    program: TypedProgram,
    source_hash: str | None,
    profile: str | None,
) -> TypedProgram:
    authenticate_rotate_mat2_return(program, source_hash, profile)
    return program
```

- [ ] Authenticate every brief coordinate: raw/normalized bytes and hashes,
  exact empty define tuple, complete function/interface/whole fingerprints,
  declarations/resources/loop proof, exact helper/signature/parameter/body,
  `c`/`s` declarations and builtins, return statement, constructor path and
  all child identities, single call and exact direct parent, exactly two
  matrix expressions, one matrix return, and zero matrix parameters.
- [ ] Reject caller source-hash mismatch and require frozen profile tuple hash
  `2cfd54ec...`; never trust a supplied fingerprint.
- [ ] Run focused GREEN plus tests with wrong key/profile/hash/define and a
  recursively reconstructed equal tree that authenticates its own objects.

### Task 2: Schema, census, and pipeline identity wiring

**Produces:** exactly one authenticated carrier in the generation pipeline.

- [ ] Add the exact sorted row to a test-local spec first and assert the loader
  REDs on unknown row field.
- [ ] Extend the allowed row-key schema by optional
  `rotate_mat2_return_profile`; require one census tuple exactly
  `(filter/rotate:rot, rotate-mat2-return-v1, {})`.
- [ ] Enforce Rotate-without-carrier, foreign carrier, duplicate carrier, wrong
  type/value/defines, and coexistence with each existing carrier as errors.
- [ ] Add the real sorted row and assert exact 128 count, ordinal 67,
  neighbors, and projected ordered hash.
- [ ] In generation, obtain the carrier, call `apply_rotate_mat2_return` after
  Perlin, and require returned identity. Pass the carrier independently to
  validator and emitter and add it only to Rotate's manifest row.
- [ ] Preserve all top-level spec/manifest vocabulary and every existing row.

### Task 3: Narrow validator admission

**Produces:** exact Rotate passes, every other matrix return remains rejected.

- [ ] Call `validate_capabilities(...,
  rotate_mat2_return_profile="rotate-mat2-return-v1")` in a focused test and
  preserve RED as unexpected keyword (or the unchanged matrix-return error).
- [ ] Add the optional keyword. At initialization require exact key, hash,
  empty defines, `glsl-f32`, and no other profile/compatibility carrier; call
  the authenticator and retain exact objects.
- [ ] If the exact Rotate tree lacks the carrier, reject before generic
  validation. If a foreign tree has it, reject.
- [ ] In the function loop, replace the blanket rejection only with:

```python
if function.return_type.kind == "matrix" and function is not authorized_helper:
    raise GeneratorError(...)
```

- [ ] Continue `reject_type`, parameter, statement, and expression traversal.
  Record exact constructor/call/parent visits using object identity; require
  one visit to each at completion.
- [ ] Run the mandatory carrier table and exhaustive single-axis matrix through
  profile and validator separately.

### Task 4: Independent emitter authorization without semantic changes

**Produces:** existing exact C++ spelling, now authorized only by carrier.

- [ ] Call `render_typed_cpp` with the carrier and preserve RED as unexpected
  keyword or mandatory-carrier failure.
- [ ] Add the optional field to `_Emitter` and keyword to
  `render_typed_cpp`. In `__post_init__`, require exact exclusive metadata and
  independently authenticate; exact Rotate without carrier and foreign carrier
  both fail.
- [ ] During existing traversal, record the exact helper/constructor/call/
  parent identities and require one emission of each. Do not add a matrix
  rendering branch: current `function_type`, `mat2` constructor, binary `*`,
  call, prototype, definition, and return emission are already correct.
- [ ] Assert exact generated shapes:

```cpp
[[nodiscard]] glsl::Mat2 rotate2D(..., double angle) noexcept;
return glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c));
uv = glsl::Vec2((rotate2D(state, context, ...) * uv));
```

- [ ] Assert exactly one declaration, definition, constructor, call, and
  direct `Mat2 * Vec2`; no pointer/reference return, sret spelling, static/
  global matrix, helper-local matrix, heap, callback, or indirect dispatch.
- [ ] Run every single-axis candidate through emitter independently, including
  forged old-object authorization on a reconstructed tree.

### Task 5: Exhaustive non-vacuous negative closure

**Produces:** at least 45 named one-axis candidates with exact preconditions.

- [ ] Build candidates for every axis enumerated in the brief. For each row,
  assert candidate differs, assert its named coordinate changed, assert all
  protected coordinates are equal, then separately require profile,
  validator, and emitter rejection.
- [ ] Require candidate-key set equals precondition-key set; a missing or extra
  precondition is a test failure.
- [ ] Include analyzer-produced matrix alternatives and dataclass replacements;
  do not patch hashes without changing authenticated content.
- [ ] Cover exact/absent/foreign/mutated trees crossed with exact/absent/
  foreign carriers, all existing carrier combinations, wrong caller hash, and
  the equal reconstructed-tree identity boundary.
- [ ] Add a code-shape mutation matrix for alternate constructor order, local
  return, second call, stored result, vector-matrix, row-major custom lowering,
  and generic matrix helper; every mode must produce a distinct candidate text
  before rejection.

### Task 6: Canonical generation and real prior-state isolation

**Produces:** exactly one generated program/binder/catalog entry.

- [ ] Run canonical generation before binder tests and preserve RED where the
  missing generated binder/entry is referenced.
- [ ] Regenerate using the normal generator. Assert 128 program blocks, one
  Rotate source/hash comment, carrier manifest field, binder declaration, and
  catalog mapping; public count 130 and unported 82.
- [ ] Start reconstruction from the actual live post-Task28 spec, remove only
  Rotate, prove exactly 127 rows and Task27 ordered hash, then run the real
  generation pipeline. Authenticate exact Task27 artifact hashes from the
  brief.
- [ ] Compare all 127 prior blocks after only namespace-ordinal normalization,
  all 127 prior manifest rows after only common output-hash exclusion, exact
  header delta, and all 129 historical public mappings. Prove no historical
  row owns the new carrier and no historical block gains matrix-return code.
- [ ] Update historical phase tests by explicitly removing later programs to
  reconstruct their phase. Never change a frozen earlier expected count to
  describe the current tree.

### Task 7: Public pixels, bindings, and executable matrix table

**Produces:** exact public parity plus direct matrix-layout/value-return proof.

- [ ] Add the frozen non-square quadrant input builder and all six case rows to
  C++. Include every executable field in named structs, not implicit loop
  position.
- [ ] Before hashes, assert exact output dimensions, input immutability, repeat
  identity, finite lane count, direct/public binder identity, and exact input
  hash/probes. Then assert full F32/RGBA8 hashes and five output probes.
- [ ] Test each required binding missing and wrong-typed independently.
- [ ] Define six explicit matrix modes with frozen numeric IDs and strings.
  Implement one switch arm per mode, no shared fallthrough, with `default`
  throwing. Each returns a witness containing mode ID/string, direct/local
  return-shape, four actual matrix lane bits, and two product bits.
- [ ] Use actual `glsl::Mat2`/`Vec2` operations for exact, transpose, diagonal,
  wrong-sign, and local-return modes. Row-major mode explicitly executes its
  wrong indexing. Local-return must construct a local and return it by value.
- [ ] Execute all 36 row/mode pairs. Assert frozen bits, divergence of every
  incorrect mode, exact/local value identity plus different witness, and
  invalid-enum rejection.
- [ ] Python parses case structs, mode enum, mode names, all switch arms,
  expected matrices/products, and witnesses one-to-one with the JSON. For each
  field, mutate only that C++ literal/token and prove table authentication
  fails while JSON bytes/hash remain unchanged.

### Task 8: Full verification and handoff

**Produces:** reviewed, evidence-backed Task28 completion with no Git action.

- [ ] Run Task28 oracle `--check`, corpus/generator checks, focused Task28
  tests, full Python discovery, and all prior Task15-28 oracle checks.
- [ ] Fresh Debug and Release warnings-as-errors configure/build/CTest outside
  stale build trees.
- [ ] Fresh ASan/UBSan build/CTest with halt-on-error. Preserve the first Apple
  `detect_leaks` unsupported diagnostic, then retry only with leak detection
  disabled if encountered.
- [ ] Measure `-fstack-usage` for `rotate2D`, `pixel`, maximum Rotate helper in
  Debug/Release/sanitized builds and set explicit final-code bounds.
- [ ] Inspect Release AArch64 symbol range/relocations. Require direct
  four-float return (expected `s0`-`s3`, no hidden sret pointer), fixed frame,
  direct `bl rotate2D` or proven inlining, exact cos/sin calls and sign/lane
  moves, no heap/VLA/alloca/exception/virtual/callback/indirect dispatch in
  `rotate2D` or `pixel`. Binder setup allocation remains setup-only.
- [ ] Record final owned-file hashes, counts, isolation evidence, RED/GREEN,
  oracle/ABI/stack/disassembly results in a Task28 implementation report.
- [ ] Dispatch independent implementation review. Address every Critical or
  Important finding with TDD and scoped re-review before accepting Task28.

## Self-review

The plan covers source/public/tree authentication, exact carrier isolation,
validator and emitter independence, exhaustive one-axis preconditions,
non-vacuous mutations, every executable table field/tamper, real Task27
reconstruction, pixel parity, ABI, sanitizers, stack, disassembly, and prior
oracles. No placeholder, runtime change, or Git step remains.
