# Task 19 implementation report

Task 19 implements exactly `fixed-array-in-parameter-v1` for
`classicNoisedeck/refract:refract`, with the schema-locked compatibility
transform `refract-truthy-vector-conditional-noop-v1`.

No Git command or indirect Git invocation was used. No branch, worktree,
commit, push, pull request, runtime/Surface ABI seam, or Task 20 work was
created.

## Implemented boundary

- Added an exact pre-tree compatibility transform that authenticates the raw
  source, normalized source, interface, complete pre-transform function tree,
  and complete pre-transform program profile. It rewrites only the four
  canonical truthy typed-array conditional sites at blend modes 2, 3, 7, and
  15 to the source-equivalent `middle = middle` form, then authenticates the
  complete post-transform tree.
- Added a frozen, indivisible post-transform ownership proof. It authenticates
  the complete interface and program, one `float[9]` input parameter, three
  fresh local tables, all 27 literal stores, all three induction reads, the
  two whole-array calls, the exact nine-trip loop and mode-one call order, the
  four compatibility sites, and the 35/32/30 array expression/reference/index
  census.
- Validator and emitter independently clear and reconstruct counted-loop,
  Task 16, Task 17, Task 18, then Task 19 proof state. Only the proof-recorded
  parameter, declarations, direct arguments, literal-index lvalues, and
  induction-index rvalues are authorized.
- Lowering is Refract-local `Kernel9 = std::array<double, 9>` and
  `Offsets9 = std::array<glsl::Vec2, 9>`, with exact 72-byte static assertions,
  one `const Kernel9&` parameter ABI, zero-initialized caller/callee tables,
  direct literal indices, and `std::size_t` induction conversions. No generic
  array type was admitted to the emitter.
- Canonical generator-owned output now exposes 113 typed / 115 public / 97
  publicly unported programs. Sacred Geometry remains excluded.

## TDD RED evidence

1. The transform test failed with unsupported compatibility transform before
   the exact transform module and dispatch were added.
2. The semantic proof test failed with a missing Task 19 proof module/field
   before the typed-IR records and structural proof were added.
3. The boundary/code-shape test failed first on unsupported `float[9]`
   parameter validation, then on emitter `function_type(float[9])`, before the
   exact validator and parameter-specific emitter authorization landed.
4. The expanded structural mutation test covers authentic, cleared, stale,
   and attacker-updated carried proofs at both validator and emitter
   boundaries. Its matrix includes source/factory provenance; complete
   interface/resource identity; every compatibility-site component; caller,
   parameter, and offset type/identity/ownership/read/write/escape cases; all
   nine offset values; loop header/proof/body/control cases; main reachability
   and liveness; forbidden ABI spellings; and cross-proof substitution.

Each production slice was made GREEN before moving to the next slice.

## Fresh verification

- Complete Python discovery after the final mutation and exclusion matrix: 106
  tests passed in 302.627 seconds (302.84 seconds wall clock).
- `check_corpus.py --check`: `check_corpus: ok`.
- `check_semantics.py --check`: bodies ok, 212 programs.
- `generate_kernels.py --check`: exit 0.
- `generate_typed_slice.py --check`: typed slice ok, 113 programs.
- Task 15 oracle check: 38 vectors, unchanged frozen SHA.
- Task 16 oracle check: `ok task-16-oracles.json`.
- Task 17 oracle check: `ok task-17-oracles.json`.
- Task 18 oracle check: `ok task-18-oracles.json`.
- Task 19 oracle check: `ok task-19-oracles.json`.
- Fresh AppleClang 16 Debug and Release configure/builds in
  `/tmp/noisemaker-for-cpp-task19-verify-debug` and
  `/tmp/noisemaker-for-cpp-task19-verify-release`, with
  `-fstack-usage -fstack-size-section`: both exit 0 under strict project flags;
  both CTest suites pass 1/1.
- Fresh AppleClang 16 combined ASan/UBSan Debug configure/build in
  `/tmp/noisemaker-for-cpp-task19-sanitize`: exit 0; CTest passes 1/1 with no
  sanitizer finding.
- All eight named Task 19 F32/RGBA hashes, twelve probe words per case, 9x7
  shape, and fresh double-render identity pass. The four truthy no-op modes
  remain four separately named fixtures.
- The catalog requires every one of eleven Refract bindings with exact types,
  accepts unrelated bindings, and contains one sorted Refract factory entry.

## Stack evidence

Compiler `.su` evidence is static in both configurations:

| Function | Raw table payload | Debug frame | Release frame |
| --- | ---: | ---: | ---: |
| `typed_2::pixel` | none owned directly | 1056 bytes static | 224 bytes static |
| `typed_2::derivX` | 72 bytes | 224 bytes static | 144 bytes static |
| `typed_2::derivY` | 72 bytes | 224 bytes static | 144 bytes static |
| `typed_2::convolve` | 72 bytes | 1072 bytes static | 224 bytes static |

The caller and callee raw simultaneous payload is 144 bytes. `derivX` and
`derivY` execute serially, so their 72-byte caller tables are not summed. The
maximum compiler-reported call-path totals are 2352 bytes Debug and 592 bytes
Release (`pixel` + one derivative helper + `convolve`).

## Changed repository files and SHA-256

- `include/noisemaker/generated/catalog.hpp` `e2cebba621536551273af01e3d77f400229dad5c7fcafb42da86cef8abb4083b`
- `src/typed_generated/typed_manifest.json` `2cd0c5b012de594317719b04b8b8337517aad75953d0d5b54d2804eb9467a543`
- `src/typed_generated/typed_slice.cpp` `96ff2647e44fe3d13a8c4e49161c3c1b1b55f00005063186d641bec46da8559b`
- `tests/test_generated_kernels.cpp` `31da5ef4151d2919cf1694db1b125f84df01ed9a9b69d8f809a1d6e14e3228ab`
- `tests/test_semantic.py` `53192b002dfb17490f679341411c4862e4e08930116d1dfb66b61543933e4b27`
- `tests/test_typed_generator.py` `a84a807593f8a8d9e424ecb57f5c629497d454482d96ed14f143e36a96f51fa3`
- `tests/test_typed_slice.cpp` `9a6a323c12ad652fb056a24c95b007c6ece9336de4a44388448067176d5d725a`
- `tools/glslcpp/emit_typed_cpp.py` `05d69d2f43894c57b13040c0db29e4f507f3fa3dae575cee0d263a8f3df95222`
- `tools/glslcpp/frontend/fixed_array_in_parameter_proof.py` `fd27f974b6d34c32cd0837948cdc93b9683afb1d61fe3881ca5841d55b10d468`
- `tools/glslcpp/frontend/refract_compatibility.py` `4bb1384ea020f03c91ae28c6d3498f0b5525318fc7ba0a2c4eb926866e1a7050`
- `tools/glslcpp/frontend/typed_ir.py` `5182d170c230f273f332d1abe1e333a39d3511016a3d2bbf7d63a886dd38ffdb`
- `tools/glslcpp/generate_typed_slice.py` `f571f48592932352c6d3164e496851ad8a8084e50044bc1994c81a4cf6a7f493`
- `tools/glslcpp/typed_slice.json` `7c4180c73fc0afd15b4f879115f2ab963605a95b165b065d0dfc28cf7167c800`

## Residuals

No known Task 19 correctness, scope, determinism, allocation, ABI, sanitizer,
or stack residual. The canonical factory text is not retained in typed IR; its
frozen SHA is carried by the proof and independently exercised through the
exact eleven-binding catalog test and eight native oracle fixtures.
