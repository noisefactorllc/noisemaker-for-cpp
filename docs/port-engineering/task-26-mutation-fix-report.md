# Task 26 mutation-harness review repair

## Result

The three Important findings in `task-26-implementation-review.md` are repaired in test scope only. Production and generated source were not changed. No Git operation was performed.

Review input SHA-256: `747be8af4589a75db01e09665ea77da15cad740bfa2bcf860deaefae6918b90d`

## I1: executable mutation paths

- The test-only renderer now has an exhaustive `Task26Mutation` switch. An out-of-range enum throws `std::invalid_argument` before pass-through or rendering.
- `vec4_extra` constructs a four-lane render-owned weight value and the luminance path consumes lanes 0 through 2.
- `helper_local_exact_f32` constructs the exact three F32 weights inside every luminance invocation.
- `main_owned_exact_f32` constructs the exact three F32 weights once in the render owner and passes them as an explicit helper argument.
- A separate `Task26MutationPath` witness is assigned explicitly per switch arm, rather than echoing the input enum. The native test authenticates all eleven paths and the three ownership/materialization/count contracts.
- The existing 88-row mutation comparison remains the output oracle for every mutation/case pair.

RED evidence:

1. Before fail-closed dispatch, Debug CTest failed `typed_task26_mutation_harness_rejects_an_unhandled_mode` with `expected exception std::invalid_argument`.
2. Before the witness implementation existed, compilation failed four call sites with `use of undeclared identifier 'task26_mutation_render_with_witness'`.

GREEN evidence: final Debug, Release, and sanitizer-enabled CTest runs all pass, including all 88 frozen mutation rows.

## I2: faithful negative closure

- Source path and declaration span are now separate single-axis mutations.
- The mislabeled parameter-owner case is now accurately named `parameter-name`.
- Function ownership is tested coherently by changing the luminance signature ID and resolving all five main calls to that new owner.
- The write mutation uses an analyzer-derived assignment expression statement whose target is the declaration-backed `LUMA_WEIGHTS` read and whose RHS is the typed initializer.
- The reference-escape mutation uses an analyzer-derived call statement, a resolvable helper signature with an `inout vec3` parameter, and the declaration-backed read as its argument.
- Every negative candidate has an explicit structural precondition assertion before profile, validator, and emitter rejection are tested.

RED evidence: independent review found compound/mislabeled/shape-forged candidates and no per-candidate structural witnesses. GREEN evidence: the repaired exhaustive closure test passes its structural preconditions and all three rejection boundaries.

## I3: executable-table authentication

- Python now parses the executable initializers for `kTask26NativeCases`, `kTask26MutationNames`, and `kTask26MutationResults`.
- Every executable field is compared with the authenticated frozen JSON: 8 complete case rows, 11 ordered mutation names, and 88 complete mutation-result rows.
- The `Task26Mutation` enum order and explicit switch-case order are each compared one-to-one with the expected eleven implementation identifiers. The native execution witness confirms the corresponding runtime path.
- Three sensitivity subtests alter one executable case, name, or result field while leaving the embedded JSON untouched; each altered source is rejected by the executable transcription gate.

RED evidence: the test-first parser stub failed with `KeyError: 'cases'`. GREEN evidence: executable parsing, exact comparisons, mapping checks, and all three tamper subtests pass.

## Verification

- Task 26 Python slice: 7 tests, `OK` (`109.375s`).
- Final focused repaired Python tests: 2 tests, `OK` (`0.309s`).
- Debug native build and CTest: 1/1 passed (`1.86s`).
- Release native build and CTest: 1/1 passed (`0.43s`).
- ASan/UBSan CTest with `ASAN_OPTIONS=detect_leaks=0`: 1/1 passed (`5.99s`).
- LeakSanitizer assessment with `detect_leaks=1`: platform aborts immediately with `AddressSanitizer: detect_leaks is not supported on this platform`; this is an environment limitation, not a test failure masked by the passing ASan/UBSan run.

## Final SHA-256

- `tests/test_generated_kernels.cpp`: `cc86c7d7e9ac23548e3a7679bcd06618e4f29a179b9ef37e7aab4796bfa24b52`
- `tests/test_typed_generator.py`: `fa87e65b014415e8eda4ccc86b45ed0b301b5f3c77fe3d9eac3d4ef66ee25765`
- `src/typed_generated/typed_slice.cpp`: `df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38` (unchanged)
- `src/typed_generated/typed_manifest.json`: `e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def` (unchanged)
- `include/noisemaker/generated/catalog.hpp`: `557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d` (unchanged)
- `docs/port-engineering/task-26-oracles.json`: `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9` (unchanged)

The review's Minor loader-message issue was not changed because this repair was bounded to the three Important findings and preserving production/generated scope.
