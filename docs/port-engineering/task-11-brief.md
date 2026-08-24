# Task 11 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use test-driven development for every behavior change and verification-before-completion before any completion claim. Work inline in the current checkout; Git, branches, worktrees, commits, and pull requests are prohibited.

**Goal:** Extend the immutable typed GLSL-to-C++ slice from 34 to exactly 44 pinned programs by adding the narrowly bounded uint/uvec, multi-declarator, integer-remainder, and scalar-mat2 language forms needed by ten factories, while retaining exact canonical parity.

**Architecture:** The parser and semantic layer already retain stable immutable typed identities for the required forms. The capability validator will gain explicit schema-locked type, binary-operator, and assignment-operator allowlists so the emitter never infers unsupported behavior. The C++ emitter will lower only the approved type/operator shapes to existing fixed-size runtime values, with minimal runtime additions where exact canonical unsigned wrap/shift or mat2 storage requires them.

**Tech Stack:** Python 3 standard library generator/frontend, generated C++20, fixed-size GLSL runtime types, zlib-only native runtime, CMake/CTest, pinned Node v24.7.0 canonical oracle used read-only during implementation.

## Global Constraints

- Modify only `.`; temporary briefs/reports belong under `docs/port-engineering`.
- Never invoke Git or create a branch, worktree, commit, or pull request.
- Use strict RED/GREEN TDD and `apply_patch`; preserve unrelated work and every approved Task 1-10 artifact.
- Preserve C++20 plus stdlib/zlib only, Python-stdlib-only generation, `-ffp-contract=off`, no fast-math, strict warnings, and all established JS-double/Float32 storage contracts.
- Do not add per-pixel allocation, virtual dispatch, `std::function`, or map/string/variant lookup.
- Do not admit loops, arrays, non-const globals, general matrices, structs, UBOs, derivatives, dynamic indexing, out/inout, varyings, discard, textureLod, texelFetch, or adapters/render graphs.
- All ten additions have authoritative `defines = {}`.

## Exact program contract

Add these exact sorted keys:

1. `classicNoisedeck/splat:splat`
2. `filter/corrupt:corrupt`
3. `filter/flipMirror:flipMirror`
4. `filter/outline:outlineBlend`
5. `filter/outline:outlineValueMap`
6. `filter/spatter:spatter`
7. `filter/tint:colorize`
8. `mixer/blendMode:blendMode`
9. `mixer/centerMask:centerMask`
10. `synth/media:mediaInput`

The typed allowlist becomes exactly 44, the public catalog exactly 46 sorted
unique factories, and exactly 168 of 212 pinned programs remain outside it.

Effect truth:

- `filter/outline:outlineValueMap` is outline pass 0 / stage 1 only.
- `filter/outline:outlineBlend` is outline pass 2 / stage 3 and requires caller-provided `edgesTexture` from the unported `outlineSobel` stage after ValueMap.
- `synth/media:mediaInput` requires caller-provided `imageTex`.
- The other seven factories are single-pass.

## Exact language frontier

### Types and conversions

- Admit scalar `uint` and fixed `uvec2`, `uvec3`, and `uvec4` mappings to `std::uint32_t` and `glsl::UVec2/3/4`.
- Admit typed uint/uvec constructors and conversions required by pinned sources: float/int to uint with existing runtime conversion rules; vector-shaped conversion to uvec with exact lane count; uvec-to-float-vector constructors used by PRNG normalization.
- Admit exactly `mat2`; reject `mat3`, `mat4`, nonsquare matrices, matrix uniforms/parameters, and all other matrix shapes.
- Lower only scalar `mat2(a,b,c,d)` to column-major `glsl::Mat2(glsl::Vec2(f32(a),f32(b)), glsl::Vec2(f32(c),f32(d)))` and only admitted `mat2 * vec2` multiplication.

### Operators

- Add a fail-closed binary-operator whitelist for the previously admitted arithmetic, relational, equality, and short-circuit operators plus integer `%`.
- Admit `>>` and `^` only for exactly typed uint/uvec componentwise forms required by PCG. Shift counts use canonical low-five-bit behavior and unsigned arithmetic wraps modulo 2^32.
- Admit `^=` only for exactly typed uvec targets and values. Preserve existing approved `=`, `+=`, `-=`, `*=`, and `/=` shapes; reject unsupported bitwise, shift, remainder, or compound combinations with program/span diagnostics.
- Do not broaden to scalar/vector `&`, `|`, `<<`, signed shifts, float bitwise operations, or arbitrary bitwise compound assignment.

### Declarations

- Emit every typed declarator in a multi-declarator GLSL statement as its own C++ declaration in source order.
- Register each stable symbol identity before its initializer is emitted so later declarators resolve only already-declared siblings and left-to-right initialization is preserved.
- Cover `spatter`'s `float t2 = ..., t3 = ...` and tint's multi-declarators without string-based source reconstruction.

### Schema vocabulary

Schema-lock the exact 44 programs, exact empty new define maps, and exact new capability/type/operator vocabulary. The chosen vocabulary will explicitly distinguish uint conversions, uvec bitwise operations, integer remainder, multi-declarators, and mat2; type and operator tables must reject additions or reordering. Preserve the scatter-only `source-double` and polygon-only compatibility-transform contracts unchanged.

## TDD execution

### Task 1: Fail-closed schema and frontier tests

**Files:** modify `tests/test_typed_generator.py`, `tools/glslcpp/typed_slice.json`, and `tools/glslcpp/generate_typed_slice.py`.

- [ ] Add RED tests for the exact 44-key allowlist, exact 46-key catalog, exact empty define maps, and schema mutation rejection for type/binary/assignment vocabularies.
- [ ] Add RED typed-source tests exercising uint/uvec constructors and conversions, componentwise `>>`, `^`, `^=`, integer `%`, multi-declarator source order/identity, scalar mat2 construction, and mat2-vector multiplication.
- [ ] Add RED negative cases for signed/float shifts, `<<`, `&`, `|`, unsupported compound bitwise, matrix near-misses, matrix parameters/uniforms, and non-scalar mat2 constructors; require program/line/column diagnostics.
- [ ] Implement only the validator/schema vocabulary required to turn each focused RED green.

### Task 2: Runtime and emitter lowering

**Files:** modify `include/noisemaker/glsl_types.hpp`, `tools/glslcpp/emit_typed_cpp.py`, `tests/test_glsl_runtime.cpp`, and `tests/test_typed_generator.py` as proven necessary.

- [ ] Add RED native vectors for unsigned wrap, componentwise shift-count masking, xor, and compound xor; verify exact hand-derived uint32 lanes.
- [ ] Add RED emission assertions for exact C++ type/constructor/operator spellings, separated multi-declarations, stable later-sibling references, column-major Mat2 construction, and Mat2*Vec2.
- [ ] Implement minimal runtime/operator overloads and emitter mappings; compile synthetic output under the strict project warnings.
- [ ] Run focused Python/native tests after every GREEN and retain the Task10 branch-scope, symbol-bound polygon transform, unary whitelist, vector materialization, and NaN sampler regressions.

### Task 3: Ten-program generation and binding gates

**Files:** modify `tools/glslcpp/typed_slice.json`, `include/noisemaker/generated/catalog.hpp`, regenerate `src/typed_generated/typed_slice.cpp` and `typed_manifest.json`, and modify catalog/binding tests.

- [ ] Add all ten programs with exact `{}` defines and run generation to expose only genuine missing frontier forms.
- [ ] Add declarations for ten typed factories and prove the exact sorted 46-key catalog.
- [ ] Add wrong-type bind failures for every distinct new sampler/uniform signature.
- [ ] Add required-sampler failures for `inputTex`, outline `edgesTexture`, media `imageTex`, and both mixer textures as applicable.

### Task 4: External parity and executable branch matrix

**Files:** modify `tests/test_typed_slice.cpp`; consume `docs/port-engineering/task-11-oracles.json` read-only.

- [ ] Verify the final oracle dataset SHA-256 `e5586ffc4a76fbcc61b2e651b97e850d174cf1db99aa949689a3d8a812914583`, revision, raw source hashes, factory-source hashes, exact bindings, dimensions, and probe layout before freezing fixtures.
- [ ] Add all primary and alternate variants needed to reproduce the dataset's 94 repeat-identical renders, covering every executable branch.
- [ ] For every variant enforce exact little-endian F32 SHA-256, RGBA8 SHA-256, selected float-bit probes, dimensions/orientation/alpha expectations, and byte-identical second render.
- [ ] Diagnose any mismatch at the first differing pixel/bit and add a focused RED regression before changing runtime or emission behavior.

#### Oracle acceptance amendment (2026-08-10)

The root controller superseded the initial 93-variant oracle artifact with the
final 94-variant artifact before acceptance. The initial artifact SHA-256 was
`f61a22328edb365bdd3f8c93916750ce5ef6d081038c04b2e146dd9a23accdb6`.
It was rejected as insufficiently discriminating: corrupt did not exercise the
low-bit branch strongly enough, center-mask and media had avoidable authored
equivalences, outline lacked an exact-red edge sample, and factory-hash
provenance was not stated as exact UTF-8 `Function.prototype.toString()` bytes.

The authorized replacement is
`docs/port-engineering/task-11-oracles.json`, SHA-256
`e5586ffc4a76fbcc61b2e651b97e850d174cf1db99aa949689a3d8a812914583`.
It adds the corrupt `mixedLowBits` case, strengthens the affected fixtures,
states the factory hash contract, and contains 94 variants. Before fixtures
were frozen, the controller independently verified all ten factory hashes and
all pinned raw-source hashes; the oracle worker rendered every variant twice
byte-identically. This amendment changes oracle strength/provenance only, not
the ten-program implementation scope.

### Task 5: Full verification and report

**Files:** create `docs/port-engineering/task-11-report.md`; do not write report material to the repository.

- [ ] Run full Python suites plus corpus, semantic, legacy-generator, and typed-generator checkers; require 212 bodies / 622 metadata candidates / 646 variants.
- [ ] Configure/build/test fresh Debug and Release trees under strict warnings; run the complete native executable and CTest.
- [ ] Verify Task-5 generated hashes and all 34 prior Task8-10 oracle hashes remain exact.
- [ ] Record language boundaries, partial-stage truth, oracle provenance/inputs/hashes/probes/branch coverage, artifact hashes, test counts, and exactly 168 remaining programs in the Task11 report.

## Self-review

- Spec coverage: exact programs/counts, narrow numeric/matrix frontier, negatives, binding gates, partial-stage truth, full oracle matrix, prior-hash preservation, and all acceptance gates are mapped above.
- Placeholder scan: no deferred implementation or unspecified behavior remains.
- Type consistency: runtime mappings, validator types, emitter spellings, binding types, and oracle fixtures all use `std::uint32_t`, `glsl::UVec2/3/4`, and `glsl::Mat2` consistently.
