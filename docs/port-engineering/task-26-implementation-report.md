# Task 26 implementation report

Date: 2026-08-11  
Repository: `.`  
Program: `filter/smooth:smoothEdge`  
Profile: `smooth-edge-luma-weights-v1`  
Status: complete; all required local validation gates pass

## Scope and controls

Task 26 adds exactly one typed program and a source-locked identity profile for Smooth Edge's sole source `const vec3 LUMA_WEIGHTS`. The lowering is helper-local automatic `const glsl::Vec3`; it does not add a generic source-global Vec3 capability.

The implementation used no Git command. No branch, worktree, pull request, commit, push, publication, or deployment was created or attempted.

The frozen design package was authenticated before the first RED:

| Artifact | SHA-256 |
| --- | --- |
| `task-26-frontier-audit.md` | `f0971b7cc06b9758975f6d856950c9a5067a2fd9ea71e4c68e46edc699bdf6f6` |
| `task-26-brief.md` | `5df8328d28859ced1b0782008087902fbd9bb6bc23bbdcfe28e71c72d1c1e975` |
| `task-26-oracle-generator.mjs` | `43300fee88354bcce9d1294071858fce432e2297ce1dd3dcccfed524ba2268f9` |
| `task-26-oracles.json` | `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9` |
| `task-26-oracle-report.md` | `b3e4a175ea95fe4bdd3319a11996451551ab9a3281412d10aa856f906515f816` |
| `task-26-artifact-repair-report.md` | `6334ea50c9b9b7ed6d272bafd2309e9b3e865667cf89c8d26228e6476c461545` |
| `task-26-implementation-design-final.md` | `784e4f8588f51cca22167364e60f3e669246f8847706ce22233c40414c94e8b5` |
| `task-26-design-preflight-report.md` | `af681234f4f5798be1baa0e29597b7d3175b659c9e9c8fd9025148cc43735b4b` |

The refreshed Task 25 baseline also passed before editing: 125 typed, 127 public, 85 unported, 212 corpus; ordered-key hashes `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4` and `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`; generator checks green; fresh Debug CTest 1/1 green.

## Implementation

- Added `tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py` with the exact two-constant public surface and identity-returning apply function required by the design.
- Locked the key, caller hash, raw and normalized bytes/hashes, empty defines, whole/interface/function hashes, zero-loop acyclic proof, exact declaration/initializer/lane shapes and F32 words, exact helper/read path and owner, dot parent/child roles, one resolved read, five helper calls, six `texelFetch` sites, and one `textureSize` site.
- Added only the exact sorted Smooth row and profile carrier to `typed_slice.json`; loader schema requires exactly one carrier on exactly this key, empty defines, and the 126-program census.
- Added independent validator and emitter authentication. Neither authority trusts the other. Each admits only the exact declaration object returned by its own authenticator and rejects carrier conflicts.
- Kept the apply stage identity-only and added a generation-driver identity guard. The profile does not rewrite typed IR.
- Emitted the source declaration only inside `typed_77::luminance`, before the dot expression:

```cpp
const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>(
    static_cast<float>(0.299),
    static_cast<float>(0.587),
    static_cast<float>(0.114));
```

- Regenerated the canonical typed C++, manifest, and public catalog/header through `generate_typed_slice.py --write`; generated files were not hand-edited.
- Added a hermetic native table for all eight frozen cases and all 88 results from the eleven mutations/controls. The 88,903-byte frozen JSON is split into three independently compiled raw-string chunks below the implementation limit and a Python test reassembles it byte-exactly.

## Strict TDD evidence

Production support was added only after each focused RED was observed:

| Step | Focused RED | Observed failure | GREEN |
| --- | --- | --- | --- |
| 1. Profile | `test_task26_profile_authenticates_exact_identity_and_rejects_mutations` | `ModuleNotFoundError` for the absent Smooth profile module | Exact profile/authenticator added; focused test passed |
| 2. Schema | `test_task26_loader_admits_only_exact_smooth_carrier_and_census` | `GeneratorError: typed slice programs are invalid` | Exact row field/carrier/census support added; focused test passed |
| 3. Authorities | `test_task26_validator_and_emitter_independently_authorize_exact_declaration` | unexpected `smooth_edge_luma_weights_profile` keyword | Independent validator/emitter authentication and object admission added; focused test passed |
| 4. Generation | `test_task26_generation_adds_only_smooth_block_manifest_and_catalog` | Smooth carrier was not propagated through generation | Ordered identity apply, validation/emission wiring, and manifest propagation added; focused isolation test passed |
| 5. Native catalog | direct/public Smooth binder test compiled before regeneration | compiler reported no member `bind_filter_smooth_smoothEdge` | canonical regeneration added the binder/key; build and CTest passed |

The generation-isolation test builds a current 126-program output and an in-memory prior 125-program projection. After normalizing only `typed_[0-9]+`, all 125 historical blocks are identical. The manifest delta is one Smooth row/profile field, and the catalog/header delta is one key and one binder.

Additional native-test diagnostics were also resolved from evidence:

- Clang rejected one 88,904-character raw literal because implementations need only support 65,536 characters. A new transcription test first required multiple chunks, then the table was split into three and remained byte-exact.
- The first native input SHA mismatch localized one hand-transcribed boundary lane. The source value `0.21995927393436432` is F32 word `0x3e613d01`, not `0x3e6137c6`; correcting that test-fixture word made all native and mutation hashes pass. Production code was unchanged.

## Negative closure

`test_task26_exhaustive_profile_validator_and_emitter_negative_closure` passed in 0.247 seconds. It exercises 44 distinct one-field structural mutations at all three boundaries, covering program/source/define/proof state; resource and declaration-backed interface order/name/id; declaration identity, position, storage, type, writability and span; initializer kind/arity/lane spelling/order/F32 value; function id/name/signature/owner/body; read cardinality/owner/path/symbol; dot parent/child roles; write/escape shapes; and helper call census.

The same test separately proves:

- exact tree + absent carrier: reject;
- exact tree + exact carrier/hash: accept unchanged;
- forged Smooth tree + absent carrier: reject;
- forged Smooth tree + exact carrier: reject;
- wrong caller hash and foreign-key carrier: reject;
- Smooth carrier combined with source-double numeric mode, compatibility transform, custom comparer, source-global-int, Gather, or literal-Vec3 carrier: reject independently in validator and emitter;
- no `static`, `thread_local`, state, namespace/global, heap, `alloca`, container/table, or lambda-capture materialization.

`test_task26_generation_driver_rejects_identity_forgery_after_profile_apply` also passed and proved that an equal-but-distinct program object returned by a forged apply stage is rejected as `Smooth Edge LUMA weights identity profile mutated program`.

## Oracle and native results

The embedded table is an exact transcription of frozen oracle SHA-256 `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9`. Explicit locks confirm public factory identity, adapter absence, source path, profile, canonical factory hash `732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e`, and absence of generic const-Vec3 capability.

Fresh native tests passed all of the following:

- exact 128-key sorted public catalog and direct/public Smooth binder exposure;
- exact five-binding ABI (`tileOffset`, `fullResolution`, `inputTex`, `smoothType`, `threshold`), with every missing/wrong type rejected and extra bindings accepted on both paths;
- eight cases rendered twice through public dispatch and once through the direct binder;
- exact dimensions, full F32 hash, RGBA8 hash, five probes, finite counts, repeat identity, direct/public parity, and input immutability for every case;
- exact pass-through RGBA/alpha, edge alpha, threshold boundary, nonzero type identity, bottom-left/top-down coordinate behavior, and 1x1 clamping;
- all 88 frozen mutation/control results, including complete candidate hashes, byte/lane difference counts, and maximum absolute differences.

## Final verification

Canonical checks:

```text
node docs/port-engineering/task-26-oracle-generator.mjs --check
ok task-26-oracles.json and task-26-oracle-report.md

python3 tools/glslcpp/check_corpus.py --check
check_corpus: ok

python3 tools/glslcpp/check_semantics.py --check
check_semantics: bodies ok (212 programs)

python3 tools/glslcpp/generate_kernels.py --check
exit 0

python3 tools/glslcpp/generate_typed_slice.py --check
generate_typed_slice: typed slice ok (126 programs)

python3 -m py_compile tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py tools/glslcpp/generate_typed_slice.py tools/glslcpp/emit_typed_cpp.py tests/test_typed_generator.py
exit 0

python3 -m unittest discover -s tests -p 'test_*.py'
Ran 164 tests in 1404.327s
OK
```

Every frozen Task 15 through Task 26 oracle generator passed in `--check` mode. Task 15 reported 38 vectors and oracle SHA-256 `e001c89f58ac970206a50dbf0974ce096e6fd71b5a3f2e389e315b0cfb16bdc8`; Tasks 16–22 each reported their oracle JSON green; Tasks 23–26 reported both JSON and report green.

Independent census recomputation:

```text
typed=126 public=128 unported=84 corpus=212
typed ordered-key SHA-256  01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76
public ordered-key SHA-256 d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3
positions: Lens=2 Gather=52 Prismatic=59 Smooth=77
sorted and unique: true
```

Fresh isolated native trees used Apple Clang 16, Ninja, `-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`:

| Tree | Result |
| --- | --- |
| Debug `/tmp/noisemaker-for-cpp-task26-debug.o4dhvb` | configure/build exit 0; CTest 1/1 passed in 4.24s |
| Release `/tmp/noisemaker-for-cpp-task26-release.Vf381D` | configure/build exit 0; CTest 1/1 passed in 1.04s |
| ASan/UBSan `/tmp/noisemaker-for-cpp-task26-sanitize.P904oq` | configure/build exit 0; first run preserved `detect_leaks is not supported on this platform`; required retry with `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1` passed 1/1 in 9.83s |

## Stack and disassembly

Compiler `.su` records:

| Build | `typed_77::luminance` | `typed_77::pixel` | Worst non-inlined pixel/helper chain |
| --- | ---: | ---: | ---: |
| Debug | 96 B static | 896 B static | 992 B |
| Release | 64 B static | 176 B static | 240 B |
| ASan/UBSan | 288 B dynamic | 2,432 B dynamic | instrumentation-inflated; not production static-stack evidence |

Both production chains are far below the 16 KiB limit.

Release `nm -C`, `otool -tvV`, and `otool -rv` evidence scoped to `typed_77` shows:

- standalone `luminance` and `pixel` symbols exist;
- `pixel` has no relocation to `luminance`, so its five source calls are inlined;
- one exact 0.299/0.587/0.114 materialization triplet is hoisted and reused in the inlined edge path; F32 words independently recompute to `0x3e991687`, `0x3f1645a2`, `0x3de978d5` and feed the multiply/add dot sequence;
- exactly six `texel_fetch_bottom_left` relocations occur: one after the `smoothType == 0` branch and five on the edge path;
- helper/pixel have fixed prologues (64 B and 176 B in Release), no dynamic stack adjustment, indirect branch, recursion, global weight load/dynamic initializer, heap allocation, or exception relocation;
- binder `shared_ptr` allocation machinery is present only outside the helper/pixel proof, as expected.

## Generated code shape and hashes

Independent generated-block audit:

```text
Smooth block bytes: 4427
LUMA_WEIGHTS declarations: 1
dot reads: 1
fetch sites: 6
textureSize sites: 1
helper-local: true
absent from pixel: true
absent from State: true
forbidden storage/allocation/container pattern: false
```

Final owned-file hashes:

| Path | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/smooth_edge_luma_weights_profile.py` | `6b25894bf5ded5b915f601b6f55f4a64f338889fba4f990e00bc882293bf1ea8` |
| `tools/glslcpp/generate_typed_slice.py` | `04914609adcef2c1f5b5ffcdae322ebad66fbad0c418b83a306b2707addb29a1` |
| `tools/glslcpp/emit_typed_cpp.py` | `11fc8432478ec887562c873062fdb60a026b8878164db5c1240fcda65fa29cf5` |
| `tools/glslcpp/typed_slice.json` | `a717f8d076dc3b921c657340eb81ab0313d275cd2cf911c467c568696cb88935` |
| `tests/test_typed_generator.py` | `bf43b5cc230cdf267b548a78702283078e6a8be94f7a259c9feb1fbf886f425a` |
| `tests/test_generated_kernels.cpp` | `e17ecab5c7d2f73df451d81ed0120588e60669ccf7eb1bb26608d643afc24374` |
| `src/typed_generated/typed_slice.cpp` | `df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38` |
| `src/typed_generated/typed_manifest.json` | `e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def` |
| `include/noisemaker/generated/catalog.hpp` | `557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d` |

`tests/test_typed_slice.cpp` was not changed and remains SHA-256 `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6`. Frozen forbidden baselines also remained unchanged: `include/noisemaker/glsl_types.hpp` `37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8`, `tests/test_glsl_types.cpp` `f4d28da8bbbb80c79037419a8f997d7724eeaf81426ffa9320265cf64cfae818`, and the existing Lens comparer profile `06c6e8a8d5947fb446f1572e3486add5942e37a5c6a42527a85563238ff3dd27`.

## Final assessment

Task 26 is locally complete. The exact Smooth Edge source/global/read identity is authenticated at separate profile, validator, emitter, and driver boundaries; generation changes only Smooth semantics; all frozen public/native oracle evidence matches; full Python, Debug, Release, sanitizer, stack, disassembly, and prior-oracle gates pass. There are no implementation blockers. The only environmental caveat is unsupported LeakSanitizer on this Apple host, explicitly preserved and handled by the required ASan/UBSan retry without leak detection.
