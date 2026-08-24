# Task 16 implementation report

Status: APPROVED after independent re-review; no remaining P0-P3 findings.

## Frozen scope

- Added exactly `filter/pixelSort:computeRank` to the typed/AOT C++ slice.
- Typed programs: 108; public catalog entries: 110; unsupported programs remaining: 102.
- Runtime binding surface: exactly one sampler, `lumTex`; no uniforms.
- The adjacent `filter/pixelSort:gatherSorted` program remains rejected.
- No shared `Surface` ABI or runtime dependency changes.

Frozen brief SHA-256: `3e803c0b7748a79b19ec58784f4fd2085ad1f0375e93c3f04971b96f31bcbcbf`.

## Proof and lowering

The frontend now attaches an immutable `DiscardedLocalCounterProof` only after proving the exact source-independent statement shape used by `computeRank`: a local integer counter, a counted loop, and an expression-statement post-increment whose value is discarded. The generator validator and emitter discard the supplied proof, independently recompute it from the typed tree, and require the raw and normalized source locks. The emitter additionally hashes `TypedProgram.source` itself.

Only the proved statement is lowered to `++brighterCount;`. Generic postfix increment remains unsupported. The emitted hot loop contains no dynamic map, string, variant, heap allocation, or dynamic dispatch.

Malformed-child, adjacent-mutation, source-tamper, and frozen-proof-tamper cases fail closed in both validation and emission tests.

The first independent acceptance review found that a forged in-memory typed tree could retain authentic source bytes, digests, spans, symbols, and proof fields while weakening the counter predicate. The corrected recomputation now binds the exact direct `main`/loop hierarchy, `NUM_SAMPLES == 32`, canonical loop header, `sampleX == x` skip predicate, full `otherLum > myLum || (otherLum == myLum && sampleX < x)` update predicate, stable symbol identities/operators, and the four-statement loop-body order. Regression cases for predicate truncation, outer-operator replacement, inclusive tie comparison, and loop-body reordering now fail at both validator and emitter boundaries.

## Oracle evidence

- Oracle generator SHA-256: `bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`.
- Frozen oracle JSON SHA-256: `878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`.
- Three source-runtime variants cover formula behavior, flat ties, and width one.
- Width-one output bits include `0x7fc00000` for the blue lane, preserving the canonical quiet NaN instead of repairing the zero denominator.
- `node task-16-oracle-generator.mjs --check`: pass.
- Prior Task 15 frozen oracle: 38 vectors, SHA-256 `e001c89f58ac970206a50dbf0974ce096e6fd71b5a3f2e389e315b0cfb16bdc8`, pass.

## Verification evidence

- Python unit suite: 89 tests, pass in the independent post-fix re-review.
- Pinned corpus check: pass.
- Semantic check: 212 program bodies, pass.
- Legacy generated-kernel drift check: pass.
- Typed-slice drift check: 108 programs, pass.
- Fresh Debug configure/build with AppleClang 16 and strict warnings: pass.
- Fresh Release configure/build with AppleClang 16 and strict warnings: pass.
- Direct native suite: 98 tests, pass in both configurations.
- CTest: 1/1 pass in both configurations.
- Post-review P1 regression: 4/4 focused tests pass; typed drift, frozen oracle, and native 98-test suite remain green with byte-identical generated C++.
- Independent final re-review: APPROVED; report SHA-256 `0a1bd75cc4953c68a73b1520aef74db35e8458729e2d8f01e209d30f4335aa3c`.
- Debug build directory: `/tmp/noisemaker-cpp-task16-debug-b5VUdj`.
- Release build directory: `/tmp/noisemaker-cpp-task16-release-FX8sqy`.

Strict native flags remained `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.

## Artifact hashes

- `tools/glslcpp/frontend/local_counter_proof.py`: `e051ca93ec5b84a874ba8591a4b153f8f1c96eb51d64d41e2de847aee1b8b787`
- `tools/glslcpp/frontend/typed_ir.py`: `4ae5c9740083c2b46a1a6842c7476557ab95f64a6ab7236721791849b612d16b`
- `tools/glslcpp/frontend/semantic.py`: `a6064b6926be3d7bb2556c29800e4607ea47457ef740dbe539e7fa99cc92381c`
- `tools/glslcpp/generate_typed_slice.py`: `c9b914a57dc028b460517ff205b15f9ca9f4f640706f96fc7f43cca509dff752`
- `tools/glslcpp/emit_typed_cpp.py`: `3e13ee763a5cada0a1cec03aecebb43875c69450d4fc3578821170b5ce907d96`
- `tools/glslcpp/typed_slice.json`: `4145bae4fd967934b24c0f1f4d56fc5adacee0039a2f66bc45ffd380859b8ee2`
- `src/typed_generated/typed_slice.cpp`: `d609c3df83ebe23a5148dfb3b3ad94129862b8705da5c1709f22a8f518885527`
- `src/typed_generated/typed_manifest.json`: `bb32947264d8e318a8e4ed544b3b7b7c3db4c83cd74298c38fd5caa34eadbf54`
- `tests/test_semantic.py`: `9ef0fd45e244a16ff45de453010a3bb94fd066a6fc075d1734965ef0318e5d1e`
- `tests/test_typed_generator.py`: `2ca00c72517da88bd660ae7d18813e23d7cad1ac9fb686e52a38f796a59ca5d5`
- `tests/test_generated_kernels.cpp`: `b0443cc409567b58060dd199b1a6b6cf13ed51fdc90c3a58f6c98737f1e4464b`
- `tests/test_typed_slice.cpp`: `179df56c6cec4f74d2245459d1f472c3a522eed435db3bb2f2574b10e2144fd6`

## Scope hygiene

No debug print, `TODO`, or `FIXME` marker was found in the Task 16 implementation and test surface. No Git command, branch, worktree, commit, push, or pull request was used.
