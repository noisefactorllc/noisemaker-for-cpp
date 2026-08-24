# Task 26 Design Preflight Report

## Result

**DESIGN COMPLETE; IMPLEMENTATION READY.**

The exact bounded design for `filter/smooth:smoothEdge` is complete at:

`docs/port-engineering/task-26-implementation-design-final.md`

No repository file was edited and no Git operation was performed during design/preflight refresh.

The prior frozen-package contradiction is resolved. The repair report at `docs/port-engineering/task-26-artifact-repair-report.md`, SHA-256 `6334ea50c9b9b7ed6d272bafd2309e9b3e865667cf89c8d26228e6476c461545`, records the exact one-field oracle correction from five to six static `texelFetch` sites and independent source/typed-AST recount. Runtime fetch counts remain 1 on pass-through and 5 on the edge path. Recursive comparison preserved all eight cases, eleven mutation/control definitions, and 88 mutation-case results. No implementation blocker remains.

## Required inputs read and validated

| Artifact | SHA-256 / result |
|---|---|
| `POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md` | read in full; no-Git/scope boundary applied |
| `../AGENTS.md` | read; no repository-local override found for the target |
| `task-25-task4-custom-comparer-report.md` | `8b83ce60f54e88d1288003047601efa7ce64025bfb8c6c8129ec11bd2341a070` |
| `task-25-task4-custom-comparer-review.md` | `7b11e7c0bb566f2c6cba627db4d1d1e961d2615da3300241b38f5184f1be7c7f` |
| `task-25-task4-dimension-hardening-rereview.md` | `4380372220b5b3cd63eee27e2e57996e7a8e26bae74747e8f997e18901daf1d5` |
| `task-26-frontier-audit.md` | `f0971b7cc06b9758975f6d856950c9a5067a2fd9ea71e4c68e46edc699bdf6f6` |
| `task-26-brief.md` | `5df8328d28859ced1b0782008087902fbd9bb6bc23bbdcfe28e71c72d1c1e975` |
| `task-26-oracle-generator.mjs` | `43300fee88354bcce9d1294071858fce432e2297ce1dd3dcccfed524ba2268f9` |
| `task-26-oracles.json` | `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9` |
| `task-26-oracle-report.md` | `b3e4a175ea95fe4bdd3319a11996451551ab9a3281412d10aa856f906515f816` |
| `task-26-artifact-repair-report.md` | `6334ea50c9b9b7ed6d272bafd2309e9b3e865667cf89c8d26228e6476c461545` |

Validation command:

```text
node docs/port-engineering/task-26-oracle-generator.mjs --check
ok task-26-oracles.json and task-26-oracle-report.md
```

This proves the corrected generator, JSON, and report agree. The repair report's independent normalized-source and typed-AST recount separately confirms the six-static-site contract.

Task 25 oracle continuity also passed:

- generator `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c`;
- JSON `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116`;
- report `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611`;
- frontier `e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27`;
- brief `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`;
- dimension-hardening report `95cd767cdb550ad89a2b7ce4e6fd7aa587e92feb0ee2bbaf4f0cd58cd53d967d`.

## Refreshed Task 25 gate

Read-only regeneration checks passed:

```text
python3 tools/glslcpp/check_corpus.py --check
check_corpus: ok

python3 tools/glslcpp/generate_typed_slice.py --check
typed slice ok (125 programs)
```

The current-source Debug build in `/tmp/noisemaker-for-cpp-task25-task4-debug` was rerun after the frozen-package repair and passed CTest 1/1 in 1.70 seconds. It compiles the post-review dimension-hardening source.

Independently recomputed current state:

| Measure | Current Task 25 |
|---|---:|
| Typed programs | 125 |
| Public programs | 127 |
| Corpus programs | 212 |
| Unported programs | 85 |
| Lens zero-based position | 2 |
| Gather Sorted zero-based position | 52 |
| Prismatic zero-based position | 59 |
| Typed ordered-key SHA-256 | `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4` |
| Public ordered-key SHA-256 | `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab` |

Current relevant file hashes:

| Path | SHA-256 |
|---|---|
| `include/noisemaker/glsl_types.hpp` | `37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8` |
| `tools/glslcpp/frontend/lens_distortion_comparer_profile.py` | `06c6e8a8d5947fb446f1572e3486add5942e37a5c6a42527a85563238ff3dd27` |
| `tools/glslcpp/generate_typed_slice.py` | `8755d89308684fac7d673b21d7cfa51aebee9da773af0b0c9c6c4dc856bcac54` |
| `tools/glslcpp/emit_typed_cpp.py` | `947f01f759c6b6cbe005b6be6505823fc4fbf7a4c124bdb34637a93727e9fead` |
| `tools/glslcpp/typed_slice.json` | `b4f2dd88fcd316886ba4e7834ad9a35296fd19085bac82d692d1438f43735867` |
| `tests/test_glsl_types.cpp` | `f4d28da8bbbb80c79037419a8f997d7724eeaf81426ffa9320265cf64cfae818` |
| `tests/test_typed_generator.py` | `3b0f55a1b967399bac4ba3efb50586e36a278cd44fb77d54ebf7f0ef2e3b9778` |
| `tests/test_generated_kernels.cpp` | `8fc8674a1029e9161112224ced50c3fb11d2e8b26be0a51070b7191c7bb7f296` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |
| `src/typed_generated/typed_slice.cpp` | `6a76407f7d812b248d4072b324b8ec42ecc561437fd8fb229169bbd94c03d372` |
| `src/typed_generated/typed_manifest.json` | `f595d92d1d0abdda365725c7a6152982a295d4e88c908def2c3f30e42b50a098` |
| `include/noisemaker/generated/catalog.hpp` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |

The `tests/test_generated_kernels.cpp` hash above intentionally supersedes the older comparer report's pre-hardening `630ca223723c93226631951fc242795ab20a283b2c38b1f950d87cee8e08ca76` hash. All other current hashes agree with the frozen comparer baseline. The new Smooth profile module does not yet exist, as expected.

## Task 26 projected gate

Adding only Smooth yields:

| Measure | Projected Task 26 |
|---|---:|
| Typed programs | 126 |
| Public programs | 128 |
| Corpus programs | 212 |
| Unported programs | 84 |
| Smooth zero-based position | 77 |
| Immediate neighbors | Skew 76; Smooth 77; Smoothstep 78 |
| Typed ordered-key SHA-256 | `01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76` |
| Public ordered-key SHA-256 | `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3` |

Lens/Gather/Prismatic remain at 2/52/59.

## Exact Smooth source/tree evidence

| Property | Value |
|---|---|
| Key | `filter/smooth:smoothEdge` |
| Source | `sources/filter/smooth/smoothEdge.glsl` |
| Raw bytes / SHA-256 | 1554 / `b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265` |
| Normalized bytes / SHA-256 | 1235 / `42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c` |
| Functions SHA-256 | `8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc` |
| Whole-program SHA-256 | `5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89` |
| Interface SHA-256 | `9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930` |
| Declaration SHA-256 | `be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27` |
| Current validator result | `filter/smooth:smoothEdge:12:1: unsupported global declaration` |

Declaration 7 is exact readonly `const vec3 LUMA_WEIGHTS` at `12:1-12:53`, initialized at `12:27-12:52` with F32 lanes `0x3e991687`, `0x3f1645a2`, `0x3de978d5`. It has exactly one resolved readonly use, in helper `luminance`; no write or escape exists. The call graph is acyclic with zero loops.

Fresh typed-tree counting found:

- six static `texelFetch` sites: source lines 25 and 31–35;
- dynamic count one on `smoothType == 0`;
- dynamic count five on the nonzero edge branch;
- one static `textureSize` site;
- five static calls from `main` to `luminance`.

This direct source/tree evidence is the repaired contract authority.

## Design decision

Use a single per-program field `smooth_edge_luma_weights_profile` with value `smooth-edge-luma-weights-v1`, exact source/tree authentication, an identity apply step, independent validator authentication, and independent emitter authentication. Reuse the emitter's helper-local source-global closure to emit exactly one automatic const `glsl::Vec3` as the first statement in `luminance`.

Do not introduce a generic constant, generic Vec3 global, new IR field, new capability registry, state member, global/static/thread-local object, or broad parser/emitter support. The exhaustive negative matrix, generation-isolation proof, eight hermetic native cases, eleven mutations, public/direct ABI tests, stack/disassembly proof, sanitizers, and full regression sequence are specified in the design artifact.

## Implementation gate

The frozen-artifact correction and owner refresh are complete. Rerun all preflight hashes and gates before the first RED test; any later source, baseline file, count, order, or hash drift is a stop condition requiring a new bounded review. The authorized owned-file list is exactly the ten paths in the design; `tests/test_typed_slice.cpp` is allowed but expected unchanged. No Git action is part of Task 26.
