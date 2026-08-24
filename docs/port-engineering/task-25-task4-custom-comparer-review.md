# Task 25 Task 4 custom comparer review

Date: 2026-08-11  
Repository: `.`  
Review mode: read-only, report inventory only, no Git commands

## Verdicts

- Spec compliance: **PASS**
- Code quality and tests: **PASS WITH MINOR CONCERN**

Finding counts: **Critical 0 / Important 0 / Minor 1**

## Review basis

The implementer report was treated as untrusted. Every reported changed file was inspected directly:

- `include/noisemaker/glsl_types.hpp`
- `tools/glslcpp/frontend/lens_distortion_comparer_profile.py`
- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/emit_typed_cpp.py`
- `tools/glslcpp/typed_slice.json`
- `tests/test_glsl_types.cpp`
- `tests/test_typed_generator.py`
- `tests/test_generated_kernels.cpp`
- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`

The current SHA-256 values of all ten files match the report inventory. The unchanged corpus source was inspected only to confirm the named line-273 risk, and the unchanged pass runner was inspected only to assess the output-dimension test gap described below.

## Spec-compliance evidence

- The named compatibility comparer is explicit about canonical JavaScript typed-array truthiness and explicitly disclaims mathematical equality; it returns true without changing `Vec::operator==` (`include/noisemaker/glsl_types.hpp:121`, `include/noisemaker/glsl_types.hpp:130-137`).
- Its direct C++ test covers equal and unequal vectors and separately retains ordinary equality behavior (`tests/test_glsl_types.cpp:38-47`).
- The profile authenticates the sole Lens key, exact raw and normalized sources, empty defines, interface, pre/final whole trees, sole `main`, exact assignment/mix/conditional/predicate/operands/arms/alpha hashes and spans, and an exact one-site vector-equality conditional census (`tools/glslcpp/frontend/lens_distortion_comparer_profile.py:10-40`, `tools/glslcpp/frontend/lens_distortion_comparer_profile.py:135-210`).
- Generation authenticates the untouched pre-lane tree before applying the existing literal-vec3 lane profile, then validates/emits the combined final tree (`tools/glslcpp/generate_typed_slice.py:1900-1937`, `tools/glslcpp/generate_typed_slice.py:1950-1966`). This is deterministic and keeps Prism lane-only.
- Loader, capability validator, and emitter all reject missing, wrong, or foreign comparer carriers and require the exact Lens comparer/lane-profile pair (`tools/glslcpp/generate_typed_slice.py:591-643`, `tools/glslcpp/generate_typed_slice.py:1297-1318`, `tools/glslcpp/emit_typed_cpp.py:136-169`).
- Emission is authorized by the authenticated predicate object's identity, not by generic equality shape; ordinary binary lowering remains the fallback (`tools/glslcpp/emit_typed_cpp.py:948-968`).
- The generated Lens statement retains `mix`, the predicate call, both conditional arms, and `alpha * 0.01`; the generated file has exactly one comparer call (`src/typed_generated/typed_slice.cpp:822`).
- The generated manifest exposes `custom_comparer_profile` only on the Lens row (`src/typed_generated/typed_manifest.json:167-177`).
- The canonical raw line remains unchanged and hashes to the frozen source identity (`tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/lensDistortion/lensDistortion.glsl:273`).
- Frozen oracle artifacts retain the binding hashes: `task-25-oracles.json` is `09d8d8a...e32e116` and `task-25-oracle-report.md` is `f72b6968...26e11`.
- Focused live verification passed: `python3 -m unittest tests.test_typed_generator.TypedGeneratorTests.test_task25_cpp_native_oracle_table_is_exact_frozen_transcription` (`Ran 1 test`, `OK`). Broad suites were not rerun.

## Findings

### Minor — Native oracle test does not explicitly assert output surface dimensions

`tests/test_generated_kernels.cpp:4229-4230` asserts the input surface width and height. For the rendered output, however, `tests/test_generated_kernels.cpp:4267` checks only `data().size() == width * height * 4`; it never asserts `first.width() == fixture.width` and `first.height() == fixture.height` (nor the corresponding properties for the repeat/direct outputs). The current unchanged `run_pass` implementation constructs the result with the requested width and height, so this is not evidence of a functional dimension defect. It is a small acceptance-test/reporting gap: a transposed or otherwise wrong shape with the same pixel count would not be detected by this fixture, while the binding brief and implementation report explicitly claim dimension verification.

Recommended follow-up: add explicit width/height assertions for `first`, `second`, and `direct` in the six-case oracle test.

## Concerns

No implementation or scope blocker was found. The only concern is the minor missing explicit output-dimension assertion above. No Git, repository mutation, publication, broad-suite rerun, or oracle rewrite was performed.
