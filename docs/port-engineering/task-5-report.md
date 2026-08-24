# Task 5 report: deterministic AOT kernel and pass-runner proof

## Scope delivered

- Added the native `KernelState` / `BoundKernel` seam and the `run_pass` raster loop.
- Added the pinned `a024dc3a960cc44af454abc7aebce50456c194e6` fixtures, their schema-1 manifest, and a standard-library-only `tools/glslcpp` lexer, normalizer, parser, typed emitter, and write/check command.
- Committed generated `synth_solid.cpp`, `filter_invert.cpp`, and the generated manifest. The generated manifest records the supplied raw and stripped fixture hashes plus output hashes: filter `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`, solid `51d8bc5e7138b1f2b35b6762dbb7d6ae70d09a1c7e0a4a70440d878609c7763b`.
- Added typed public factories and end-to-end coverage for solid, invert, coordinate orientation, bind-time failures, generator determinism, fixture tampering, unsupported calls, and generated-source runtime constraints.

## Honest red/green evidence

1. RED: after `tests/test_kernel.cpp` and its CMake entry, `cmake --build build --parallel` failed with `noisemaker/kernel.hpp file not found`.
   GREEN: after `kernel.hpp` / `kernel.cpp`, the same build plus `build/noisemaker-cpu-tests` passed 47 tests.
2. RED: after `tests/test_pass_runner.cpp` and its CMake entry, the build failed with `noisemaker/pass_runner.hpp file not found`.
   GREEN: after `pass_runner.hpp` / `pass_runner.cpp`, the same build plus test binary passed 49 tests.
3. RED: after `tests/test_generated_kernels.cpp` and its CMake entry, the build failed with `noisemaker/generated/catalog.hpp file not found`.
4. RED: the first `python3 tests/test_generator.py` failed because committed generated outputs did not exist. Its initial broad source-body assertion also caught the required factory-time `bindings` access; the test was narrowed to the pixel-function body, which is the stated no-lookup contract.
5. RED: after the first generator write, CMake failed because a `State` deriving from `KernelState` is not an aggregate and cannot use designated initialization. The emitter was changed to emit a typed constructor and positional `std::make_shared` arguments.
6. GREEN final commands and results:
   - `python3 tests/test_generator.py` — 3 tests passed.
   - `python3 tools/glslcpp/generate_kernels.py --check` — passed.
   - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug` — configured.
   - `cmake --build build --parallel` — built.
   - `build/noisemaker-cpu-tests` — 55 named tests passed.
   - `ctest --test-dir build --output-on-failure` — 1/1 passed.

## Provenance and generator boundaries

- Fixture validation recomputes raw SHA-256 and `bytes.strip()` SHA-256 before parsing. The checked-in source lock supplies the revision; this task does not assert any sibling working-tree cleanliness or HEAD state.
- The normalized AST supports only declarations, assignments, `if`/`else`, binary arithmetic/equality, members/swizzles, and `vec2`, `vec4`, `textureSize`, `texture`, and `min` calls exercised by the two fixtures. Any other top-level form, statement, expression, swizzle, or call raises `GeneratorError` with the program key and location/context. There is no hand-authored generated kernel fallback.
- The CMake graph contains only C++ sources and zlib. It neither finds nor runs the developer tool and has no network, Node, or sibling-repository dependency.

## Remaining concerns before catalog scale-up

- This is deliberately a two-program parser/emitter subset; control flow, function definitions, matrices, arrays, derivative operations, texture modes, and the broader GLSL builtin surface still need incremental contracts before enabling more effects.
- The sampler pointer is intentionally non-owning, matching existing `Bindings`; callers must retain source surfaces through rendering.
- Generated output source is deterministic and checked, but only this bounded fixture manifest is currently admitted.

## Fix round 1: generator write and provenance hardening

- Manifest outputs are now checked before any output path is constructed: each must be a non-reserved, bare `.cpp` filename with no POSIX/Windows separator, absolute form, or traversal component. Outputs must be unique, and the resolved final path must be an immediate child of `src/generated`.
- `--write` now generates and validates all bytes first, rejects any unexpected file/directory/symlink in an existing generated tree, stages the complete replacement directory, swaps it through a private backup, and restores the previous tree if the staged swap fails. Generator-owned stage/backup directories are the only directories removed.
- `--check` recursively scans the generated tree and rejects nested directories/files and any symlink, rather than ignoring non-top-level drift.
- `pass_bindings` must be a string-to-string mapping exactly matching the parsed uniform names/types. The validated mapping is the factory-emission input; its entries and program records are sorted for deterministic output independent of JSON map/program-list order.

### Fix-round red/green evidence

1. RED: after adding traversal, duplicate-output, transaction rollback, empty-target, nested-tree, symlink, binding name/type, reversed-program, and reversed-binding-table tests, `python3 tests/test_generator.py` had 6 failures and 1 error. It demonstrated unchecked traversal/reserved/absolute/duplicate outputs, non-transactional writes, ignored nested entries, and rejected reordered programs.
2. RED: after the first hardening implementation, the same Python test had 3 failures: generated golden output ordering had changed, the injected directory-swap predicate needed resolved temporary paths, and the nested-directory diagnostic had become more specific. The predicate/diagnostic test expectations were corrected to test behavior, then generated outputs were regenerated.
3. RED: the explicit reversed binding-table test then failed because `State`/factory field order followed JSON mapping insertion order. The emitter was changed to iterate the validated binding table in sorted-name order.
4. GREEN final commands and results:
   - `python3 tests/test_generator.py` — 7 tests passed.
   - `python3 tools/glslcpp/generate_kernels.py --check` — passed.
   - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug` — configured.
   - `cmake --build build --parallel` — built.
   - `build/noisemaker-cpu-tests` — 55 named tests passed.
   - `ctest --test-dir build --output-on-failure` — 1/1 passed.

The backslash-specific member of the output-name table was added after the shared bare-filename validator was green; it therefore lacks its own original red run, although the same table's traversal/reserved/absolute cases failed before that validator existed.

## Fix round 2: Windows filename safety

- `_validate_output_name` now rejects `:` (including alternate data stream forms) and uses an explicit case-insensitive Windows device-name set for `CON`, `PRN`, `AUX`, `NUL`, `CLOCK$`, `COM1`–`COM9`, and `LPT1`–`LPT9`, including extension forms such as `CON.cpp` and `NUL.cpp`.
- RED: extending the pre-write/no-mutation table with `foo:bar.cpp`, `CON.cpp`, and `NUL.cpp` made `python3 tests/test_generator.py` fail those three subtests because all were previously accepted.
- GREEN: the same Python suite passed 7 tests after the validator change. `generate_kernels.py --check`, Debug CMake configure/build, 55 named C++ tests, and CTest 1/1 all passed.

## Fix round 3: Windows superscript device aliases

- Replaced the partial inline device construction with a stable module-level Windows reserved-device basename set. It retains the standard devices and adds `COM¹`/`COM²`/`COM³` plus `LPT¹`/`LPT²`/`LPT³`, including extension forms.
- RED: adding direct pre-write/no-mutation cases for all six superscript aliases made the Python developer test fail those six subtests before the set expansion.
- GREEN: Python 7/7, generator `--check`, Debug CMake configure/build, 55 named C++ tests, and CTest 1/1 passed.
