# Task 18 implementation report

Task 18 implements exactly `fixed-grid-counter-store-v1` for:

- `filter/celShading:celShadingEdges`
- `filter/outline:outlineSobel`

No Git command or indirect Git invocation was used. No branch, worktree, commit,
push, pull request, runtime/Surface ABI seam, or Task 19 work was created.

## Implemented boundary

- Added a frozen program-level proof with independent raw/normalized source
  locks, empty define contract, typed-function lock, and whole-program lock.
- The proof structurally authenticates the exact zero-dimension early return,
  prefix-updated `ky`/`kx` 3-by-3 loops, zero-initialized `float[9] samples`,
  fresh `int idx=0`, one dynamic store followed immediately by discarded
  `idx++`, interval 0..8/final 9, and all 12 exact authored literal Sobel reads.
- Validator and emitter clear and reconstruct counted-loop, Task 16, Task 17,
  then Task 18 proof state independently. They authorize only the exact array
  declaration, dynamic lvalue store, discarded update statement, and literal
  rvalue read sites.
- Lowering is exactly zero-initialized `std::array<double, 9> samples{}` with
  `samples[static_cast<std::size_t>(idx)]` stores and direct `samples[N]`
  reads. Pixel functions remain `noexcept`; no `.at()`, allocation, callback,
  virtual dispatch, or exception path was added.
- Canonical generator-owned output now exposes 112 typed / 114 public / 98
  publicly unported programs. Refract and Sacred Geometry remain excluded.

## TDD RED evidence

1. Semantic proof test failed for both keys because `TypedProgram` had no
   `fixed_grid_counter_store_proof`.
2. Validator/emitter tests failed on unsupported `float[9]` and lacked Task 18
   provenance/profile diagnostics.
3. Schema/count test failed on capability-vocabulary drift before the new
   capability and keys were added.
4. Strict native build failed only because the generated catalog lacked the
   two Task 18 factory declarations; the new native oracle translation unit
   compiled cleanly.

Each slice was made GREEN before moving to the next production slice.

## Fresh verification

- Focused semantic/validator/emitter/catalog tests: 5/5 passed.
- Focused forged early predicate, postfix loop header, dynamic store index,
  prefix counter update, index-4 read, stale/cleared proof, resource drift,
  and Refract/Sacred both-boundary tests: passed.
- Complete Python discovery after final test changes: 101 tests passed in
  247.956 seconds.
- `check_corpus.py --check`: `check_corpus: ok`.
- `check_semantics.py --check`: bodies ok, 212 programs.
- `generate_kernels.py --check`: exit 0.
- `generate_typed_slice.py --check`: typed slice ok, 112 programs.
- Task 15 oracle check: 38 vectors, unchanged frozen SHA.
- Task 16 oracle check: `ok task-16-oracles.json`.
- Task 17 oracle check: `ok task-17-oracles.json`.
- Task 18 oracle check: `ok task-18-oracles.json`.
- Fresh AppleClang 16 Debug and Release configure/build with
  `-fstack-usage -fstack-size-section`: both exit 0 under strict project flags.
- Debug direct native executable: all cases passed; Debug CTest 1/1 passed.
- Release direct native executable: all cases passed; Release CTest 1/1 passed.
- All six Task 18 F32/RGBA hashes, twelve probe words per case, 9x7 shape,
  top-down orientation, and fresh double-render identity passed in both builds.
- Independent final read-only review after the expanded tamper/dominance test
  matrix: APPROVED with no P0-P3 findings.

## Stack evidence

Compiler `.su` evidence is static in both configurations:

| Kernel | Namespace | Raw table payload | Debug frame | Release frame |
| --- | --- | ---: | ---: | ---: |
| Cel edges | `typed_7::pixel` | 72 bytes | 688 bytes static | 272 bytes static |
| Outline Sobel | `typed_37::pixel` | 72 bytes | 640 bytes static | 176 bytes static |

The 72-byte payload is reported separately from whole compiler frames.

## Changed repository files and SHA-256

- `include/noisemaker/generated/catalog.hpp` `0e43446f32f9ec121901f728819e25aabda2c84e9a7d28a8438a84cc4b37a79d`
- `src/typed_generated/typed_manifest.json` `4bd7470b0db62c9971bf79a94b771270405ae674075a477369cee143c19ed112`
- `src/typed_generated/typed_slice.cpp` `0a4fd8992ebbc4e143f1de4b911ee70399ad17b2aa3d6fee188ac210f83e109b`
- `tests/test_generated_kernels.cpp` `0a1247db251ab467b5caddf9f9d1ccd769ea4b2cc02724a223fe78762da8940c`
- `tests/test_semantic.py` `627c1dffaefac2fd944c1c2de322870f464414685c75183c8337e3028e77a179`
- `tests/test_typed_generator.py` `39d473b75278840fe9b8bb1dcc641ff3d6a8cd17b8094e6436537b0016a08df0`
- `tests/test_typed_slice.cpp` `88915e2b7e5f568686280b5a26a9bc5b585a4afa5e22e424158e9d7c2db221d4`
- `tools/glslcpp/emit_typed_cpp.py` `14203c862a8aa1ee480d3316acaddf0669772eace17ddb4b528def73ea4c0c6b`
- `tools/glslcpp/frontend/fixed_grid_counter_store_proof.py` `2bada0deacf426f29a85a1d747eba6e62ff5c37b4d428a4a4ab40fc44aa3ffa1`
- `tools/glslcpp/frontend/semantic.py` `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b`
- `tools/glslcpp/frontend/typed_ir.py` `39d834a483bd1f45985a1af14c68281034f7e4fa23b33097d2443547bfa73acd`
- `tools/glslcpp/generate_typed_slice.py` `f414800b4d983c17e8f487043d0298b4ebf0ec18431aceb9c25750067598216d`
- `tools/glslcpp/typed_slice.json` `163a714fa7369d91405fb9b14614005b9c6c9d6ed550a8916bd43a2edb4513bc`

## Residuals

No known Task 18 correctness, scope, determinism, allocation, ABI, or stack
residual. The authored zero-dimension branch is public-API unreachable by
design and is therefore covered by exact proof reconstruction plus emitted
dominance/order assertions, without an unauthorized runtime/test seam.
