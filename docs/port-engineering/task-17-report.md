# Task 17 implementation report

Status: complete within the approved Task 17 scope. No Git command, branch,
worktree, pull request, Task 18 change, or unrelated source change was made.

## Scope and provenance

- Corrected brief SHA-256: `2306280acb661199c07cb2ad8e6607393129469b09d1d0976ed1bb7428719ba7`
- Approved scope/proof rereview SHA-256: `a00cb56743aa9cd3218226854a1b0dbf676f7fc5e2a356925b75fe07325fbc50`
- Risk audit SHA-256: `17692e3784ad64a4a283f7509b8cabe65521cabe282d5a78d6e6ade17be24937`
- Final acceptance review SHA-256: `da55d697e37c933d9531229fef2aca885519c75ccf44938546afffe27d7b7f74`
- Amended implementation design SHA-256: `538a6ca49b0dc729d3b287dd091cf01ada6e80f0f5473a0dc6b247f638bbb8cf`
- Oracle generator SHA-256: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`
- Oracle JSON SHA-256: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`
- Oracle report SHA-256: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`
- Oracle generator check: `ok task-17-oracles.json`

Pinned source locks are enforced independently at validator and emitter
boundaries, using retained raw source, normalized source, immutable canonical
type-tagged defines, and the caller source hash as an additional generator
gate. Sharpen retains raw/normalized SHA-256
`c9a9b196e61a2904b37ad89c7fc46bee1b40b6bba81293dde3d7cd37527773e7` /
`1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0`;
Sobel retains
`ef459738b931929a65422df36f852da4e7cbe4e90387690bea747a34a2e52f84` /
`d8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c`.

## Implementation

- Added capability `fixed-nine-local-literal-init-counted-read-v1`.
- Added exact frozen proofs for Sharpen's `kernel`/`offsets` and Sobel's
  `sobel_x`/`sobel_y`/`offsets`, including complete literal stores, exact
  counted reads, no escape, a hard-coded function-body fingerprint, and a
  separately hard-locked whole-program profile covering declarations,
  resources, body status, local types, structs, UBOs, interfaces, builtins,
  counted-loop proof, functions, raw/normalized source, and defines.
- Validator and emitter each reconstruct the proof from a clean complete
  `TypedProgram`; retained, cleared, and attacker-updated proofs cannot widen
  bindings/resources or admit a forged global array.
- Array authorization is per exact proved local declaration and exact proved
  store/read index descriptor `(array ID, index/induction ID, span)`. Proof
  presence alone never admits an array type, global, or index.
- Lowered only proved tables to zero-initialized stack storage:
  `std::array<double, 9>` and `std::array<glsl::Vec2, 9>`.
- Emission uses direct `operator[]`; there is no `.at()`, dynamic array, or
  table heap allocation.
- Added typed factories for `filter/sharpen:sharpen` and
  `filter/sobel:sobel`, exact binding validation, catalog ordering, adjacent
  exclusions, and four canonical external byte oracles.
- Amended the implementation design to resolve its P2 contradiction:
  `include/noisemaker/generated/catalog.hpp` is now rendered, drift-checked,
  and written by the canonical typed-slice generator, including both normal
  Task 17 public declarations.
- Counts are 110 typed programs, 112 public factories, and 100 publicly
  unported corpus programs.

## Verification

- TDD RED: five initial Task 17 tests failed for missing provenance/proof
  fields and unsupported `float[9]`, before production support was added.
- Original Task 17 TDD RED remains recorded above. Final-review P1 TDD RED:
  both validator and emitter accepted all three forgeries for both keys, 12
  failed boundary assertions total, before whole-program authentication.
- Final-review P1 GREEN: exact extra-uniform-plus-resources, resources-only,
  and global-array-output forgeries reject for both keys and both boundaries
  with retained, cleared, and attacker-updated proof variants.
- Full Python semantic/generator suite: 80 tests passed in 209.123 seconds.
- Focused final Task 17/P1/P2 Python suite: 7 tests passed in 0.404 seconds.
- Canonical generator check: `typed slice ok (110 programs)`.
- Debug rebuild succeeded; native test 1/1 passed, 0 failures, 0.98 seconds.
- Release rebuild succeeded; native test 1/1 passed, 0 failures, 0.35 seconds.
- The four native cases match exact F32 hashes, RGBA8 hashes, all twelve probe
  words each, and double-render repeatability.

Stack instrumentation used AppleClang 16 with `-fstack-usage` and
`-fstack-size-section` in fresh `build-task17-debug` and
`build-task17-release` directories:

| Kernel | Raw table payload | Debug pixel frame | Release pixel frame |
|---|---:|---:|---:|
| Sharpen | 144 bytes | 1280 bytes | 304 bytes |
| Sobel | 216 bytes | 1744 bytes | 432 bytes |

The frame figures are compiler-reported whole pixel-function frames; the raw
payload figures are the exact table bytes alone.

## Changed repository files and SHA-256

- `include/noisemaker/generated/catalog.hpp` `06e648562b2da1ff19ba4fdba68b9f90876bf9adcb945d7091debe5765e81fd5`
- `src/typed_generated/typed_manifest.json` `b86ea6e923898815f9ceb22488659fd11f5ea87fef841932e5a0d3e24b15d103`
- `src/typed_generated/typed_slice.cpp` `c4fc6ba0f23b1f673c6a9c95aa94bd60775396c362c71956a9ed53c185a38039`
- `tests/test_generated_kernels.cpp` `0d06498b25e98499ef4e1aaf636588ad2b45c53b6910cab30683f8a00cda71af`
- `tests/test_semantic.py` `fa099608b4dd47e3e968577d396130592a4406643bbf8e9cc4470d97c9debba4`
- `tests/test_typed_generator.py` `fa60b12fcf49544f02f19fe9a6d94361718bd29ef4b9e8043000e8c18ab01aaf`
- `tests/test_typed_slice.cpp` `253254aca171d3ca9e771bd5e74f78ca21cfe120c8ed6b834ff84b409dfaec26`
- `tools/glslcpp/emit_typed_cpp.py` `7bc08b82ba5ee83e3b9556f00bae7e6732ec21e192dc08a3e10a190eda93b5bc`
- `tools/glslcpp/frontend/__init__.py` `8394bad8c4b9c60a71614ec5915b11f5478650fd3696ad7e6e74b23e201976d4`
- `tools/glslcpp/frontend/fixed_nine_table_proof.py` `712a98e5130545f6f3884a965e2e096bc07fa0fe0ed88b1549ff6733ecac85b1`
- `tools/glslcpp/frontend/semantic.py` `81cad0ae9f5438a734841a0f94e6237f3788117f7c94a25a77237c6f16e09edf`
- `tools/glslcpp/frontend/typed_ir.py` `618cbd0e4559c00df0b578a77776e79b8200d79e41a79861bb434f8f11efca8b`
- `tools/glslcpp/generate_typed_slice.py` `2e024a4db471f34ea5c918aacf13e0ad9172fee21f0aeae1bd3c489723388826`
- `tools/glslcpp/typed_slice.json` `2cdde3dbb6bc8323202dae060dbf30841d95fc1cfe3fbeac82c26f9016671960`

Residuals: no known Task 17 correctness or scope residual. Debug frames include
uninlined helper temporaries and are intentionally reported separately from
the bounded raw table payload.
