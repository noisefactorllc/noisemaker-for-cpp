# Task 26 Implementation Review

Date: 2026-08-11  
Repository: `.`  
Mode: read-only repository review; no Git command, edit, build, or broad-suite rerun

## Verdicts

- **Spec compliance: FAIL — changes required.** The production implementation is narrowly source-locked and the generated Smooth block is correct, but the required hermetic mutation proof and exhaustive negative-closure proof are incomplete.
- **Code quality: FAIL — changes required.** The frozen JSON is duplicated into executable C++ tables without a test that proves those executable tables are the JSON transcription.
- **Finding counts:** Critical 0, Important 3, Minor 1.
- **Acceptance blockers:** I-1, I-2, and I-3 below.

## Spec-compliance findings

### Critical

None.

### Important

#### I-1. Three of the eleven required native mutation/control modes are no-ops, so 24 of the claimed 88 mutation executions do not exercise their named structures

The brief requires an observable `vec4` extra-lane control, an exact helper-local F32 materialization, and an exact F32 vector owned by `main` and passed to the helper (`task-26-brief.md:326-345`). The final design likewise says the test-only harness must cover all eleven controls (`task-26-implementation-design-final.md:329-345`).

The native test declares all three modes in `Task26Mutation` (`tests/test_generated_kernels.cpp:7387-7390`), but `task26_mutation_render` creates one three-lane `weights` array outside the `luminance` lambda for every mode (`tests/test_generated_kernels.cpp:7506-7513`). Its only mode-specific branches implement the three value changes, lane swap, scalar, self-dot, cross-call mutation, and source-double path (`tests/test_generated_kernels.cpp:7514-7546`). There is no branch for `vec4_extra`, `helper_local_exact_f32`, or `main_owned_exact_f32`.

Consequently:

- `vec4_extra` never constructs or consumes a four-lane value;
- `helper_local_exact_f32` still uses the outer three-lane array, not a helper-local materialization;
- `main_owned_exact_f32` is indistinguishable from the same default outer-array fallthrough rather than an explicit main-owned value passed to a helper.

The result loop verifies only that this shared fallthrough matches the prewritten identity rows (`tests/test_generated_kernels.cpp:7656-7690`). Thus all 24 rows for these three modes can pass without proving type/arity or ownership. This defeats the stated purpose of the observably inert structural controls.

**Required fix contract:** implement each enum value as an explicit, structurally distinct path and make unhandled enum values fail. The vec4 path must really materialize/consume four lanes while preserving the frozen identity result; the helper-local path must materialize the exact three F32 words inside the luminance helper; the main-owned path must materialize the exact F32 vector in the caller and explicitly pass it to a non-capturing helper. Re-run all 88 comparisons in Debug, Release, and ASan/UBSan and preserve exact frozen results.

#### I-2. The claimed exhaustive one-field negative-closure matrix does not faithfully instantiate several named rejection dimensions

The implementation report claims 44 distinct one-field mutations covering source path/span, parameter ownership, writes, and reference escape (`task-26-implementation-report.md:68-80`). The test does reject 44 altered objects at all three authorities, but several cases do not establish the claimed dimensions:

- `declaration-span-and-source-path` changes both `program_key` and `start_column` in one candidate (`tests/test_typed_generator.py:10948-10949`, used at `tests/test_typed_generator.py:11029-11032`), so it is not a one-field mutation and cannot independently locate either boundary.
- `parameter-owner` changes a parameter name (`tests/test_typed_generator.py:11090-11094`), not ownership.
- `write` merely relabels the `dot` node as an assignment (`tests/test_typed_generator.py:11114-11116`); it does not construct a valid write to the declaration-backed symbol.
- `reference-escape` merely relabels the `dot` node as a generic call with a forged signature (`tests/test_typed_generator.py:11117-11119`); it does not represent a valid by-reference/out/inout escape of the symbol.

The exact program/function hashes make these malformed changes reject, but that does not prove the specifically required ownership/write/escape closure.

**Required fix contract:** split source-path and span mutations into independent single-axis cases; replace the mislabeled owner/write/escape candidates with internally coherent typed-tree mutations that actually move ownership, write the declaration-backed symbol, and pass it through the IR's reference/out/inout mechanism. Assert the intended structural precondition for every candidate before checking profile, validator, and emitter rejection. If the typed IR cannot express a required shape, stop and revise the approved design rather than counting a different mutation under that label.

### Minor

None.

## Code-quality findings

### Critical

None.

### Important

#### I-3. The transcription test authenticates only an inert embedded JSON copy, not the executable C++ case/name/result tables

The native test has executable tables at `tests/test_generated_kernels.cpp:7243-7268`, `tests/test_generated_kernels.cpp:7283-7294`, and `tests/test_generated_kernels.cpp:7296-7385`. The Python transcription test instead extracts only raw-string chunks between marker comments and compares that reconstructed JSON to the `/tmp` oracle (`tests/test_typed_generator.py:11240-11267`). It never parses or compares the executable `kTask26NativeCases`, `kTask26MutationNames`, or `kTask26MutationResults` arrays.

A focused read-only parser used for this review found that the current 8 cases, 11 names, and 88 result rows do match the frozen JSON. The defect is the missing durable relationship: a future edit can drift an executable expected field while leaving the embedded JSON untouched, and the transcription test will still pass. Combined with I-1, this permits a disconnected expected table and implementation to agree without exercising the frozen control.

**Required fix contract:** eliminate the duplicate authority by generating the executable C++ tables from the authenticated JSON, or extend the Python test to parse every executable field and compare all 8 case rows, all 11 names in order, and all 88 result rows to the JSON. The gate must also prove an exact one-to-one enum/name/implementation mapping so no mode can silently use a default path.

### Minor

#### M-1. The combined loader invariant reports the wrong profile family for Smooth/census failures

The loader combines sortedness, 126-count, typed-key hash, literal-Vec3 carriers, and the Smooth carrier into one condition (`tools/glslcpp/generate_typed_slice.py:654-660`) but always raises `typed slice literal vec3 lane profile drift` (`tools/glslcpp/generate_typed_slice.py:661`). A Smooth carrier or census failure therefore points at an unrelated profile and slows diagnosis.

**Required fix contract:** split the census/key, literal-Vec3 carrier, and Smooth carrier checks and give each a precise error.

## Verified compliant evidence

No finding was found in the production implementation or generated artifact for these required properties:

- The profile is restricted to `filter/smooth:smoothEdge`, authenticates exact source/defines/tree/profile identity, applies without replacing the immutable program object, and is independently authenticated by validator and emitter.
- Emission admits only the authenticated declaration object and lowers it to one automatic helper-local `const glsl::Vec3`; no generic constant/runtime/IR capability was added.
- The generated Smooth block has one helper-local `LUMA_WEIGHTS`, one direct dot read, no State/binder entry for it, six static fetch sites, one texture-size site, and the exact five-binding ABI.
- Current census/catalog state is 126 typed, 128 public, and 84 unported; Smooth is typed namespace position 77.
- Generator isolation evidence and direct inspection show one Smooth block/manifest/catalog addition and no semantic drift in the prior 125 normalized blocks.
- Current owned-file hashes match the implementation report. `tests/test_typed_slice.cpp` and the named forbidden runtime/vector/profile baselines retain their preflight hashes. A timestamp scan of the implementation window found only the nine reported changed owned paths.
- `node docs/port-engineering/task-26-oracle-generator.mjs --check` passed, and `python3 tools/glslcpp/generate_typed_slice.py --check` reported `typed slice ok (126 programs)`.
- Existing fresh Debug/Release/ASan+UBSan logs and build metadata were inspected. They preserve `-ffp-contract=off` and stack instrumentation, show passing final CTest runs, preserve the earlier unsupported leak diagnostic, and show stack records of 96/896 B Debug, 64/176 B Release, and 288/2432 B sanitizer for helper/pixel.
- Release symbol/disassembly inspection confirms standalone helper/pixel symbols, fixed stack, exact weight constants feeding the dot sequence, five inlined helper uses, six fetch calls, and no helper/pixel heap allocation, indirect branch, exception path, recursion, or dynamic stack growth. Binder allocation remains outside that proof.

Per review instructions, broad suites were not rerun. The acceptance failure is limited to the missing/mislabeled proof coverage above; it is not evidence of a production-output mismatch in the current generated Smooth implementation.
