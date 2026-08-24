# Final rereview of the amended Task 21 Degauss brief and implementation design

## Decision

**APPROVED.** The refrozen Task 21 brief at SHA-256
`bf6a223b076b0c3cac93b2a05d3c428b4ba39ab2fe88fe6bc712c3a0a76e6418`
fully corrects the sole remaining namespace-isolation P2. The implementation
design at SHA-256
`cb89295d7647b9414dc4fadfcd0ed1b0350e300b2c8e08aec5e2c3540b4bb068`
faithfully implements the amended contract. There is no P0, P1, P2, or P3
scope, semantic, oracle, implementation-design, verification, or baseline
finding.

This was a read-only review. I used no Git command, changed no repository file,
and updated only this requested review artifact outside the repository.

## Reviewed identities

| Artifact | Recomputed SHA-256 |
| --- | --- |
| Refrozen `task-21-brief.md` | `bf6a223b076b0c3cac93b2a05d3c428b4ba39ab2fe88fe6bc712c3a0a76e6418` |
| `task-21-implementation-design.md` | `cb89295d7647b9414dc4fadfcd0ed1b0350e300b2c8e08aec5e2c3540b4bb068` |
| `task-21-frontier-audit.md` | `2f4665fa7a7d6471291030c02b3e259a797a95d33dd15dabd3b10433749ec7b0` |
| `task-21-oracle-generator.mjs` | `0c1f12904e1c17a39c61055596be9f0d46ecded252a9d5c7cf1339653472c5c9` |
| `task-21-oracles.json` | `bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38` |
| `task-21-oracle-report.md` | `4196f7a238c63eadb2e167b3f76528b620cea56fabad999525c8fbc5826f02fc` |
| Accepted `task-20-report.md` | `83d0624bd21f581593d7b011fdff8757191ae466b8b84174b6a1eec5cb7b81f2` |
| Task 20 final acceptance review | `b1ee7af7b8ecf7144209a77141448b5b55093f5987d82bbc5dfe37d82f4c750f` |

The direct oracle generator passes `--check`, and its stdout hashes to the exact
frozen JSON identity. The corpus, semantics, generated-kernel, and typed-slice
drift checks pass on the accepted Task 20 baseline.

## Namespace-isolation P2 resolution

The refrozen brief corrects every relevant occurrence of the former impossible
raw-body identity requirement:

- the closed-world exclusion matrix requires raw byte identity for the 19
  pre-Degauss blocks, ordinal-normalized identity for all 114 prior blocks, and
  no normalization of whitespace, literals, comments, factories, or code;
- the slice/generation gate splits C++ at exact `// Typed IR program:` markers,
  applies the same 19/114 contract, and fails every other byte drift;
- the generated-code verification section states the exact comparison on the
  accepted Task 20 and Task 21 outputs and explains the unavoidable sorted-key
  renumbering; and
- completion evidence repeats the same exact requirements.

The implementation design is equally precise. Degauss is inserted at ordinal
19. The 19 blocks at prior indices 0-18 remain raw-identical; all 114 prior
blocks must match after replacing only `typed_[0-9]+` namespace ordinals with
one sentinel; all other differences fail. It explicitly forbids changing the
generator/emitter namespace scheme. This is executable and matches accepted
Task 20's bounded isolation model.

The two earlier P2 corrections also remain intact: the corpus command uses
`--check`, and typed source `main@56` remains distinct from generated/native
`pixel`. Current in-memory emission has one `void pixel`, no C++ `main`, and one
`integer_mod`; the typed tree has one `texelFetch(..., 0)` in source `main` and
four in `sample_bilinear`.

## Accepted baseline and exact inventory

Current inventory is exactly 114 typed / 116 public / 96 unported / 212 corpus.
Adding Degauss alone yields exactly 115/117/95/212. The brief's 117-key catalog
is sorted, unique, equals the accepted catalog plus Degauss, places Degauss at
typed ordinal 19 between Craquelure and Deriv, and excludes CRT.

The implementation design owns exactly these eight repository files, whose
accepted pre-Task21 hashes all match the checkout:

| File | Accepted SHA-256 |
| --- | --- |
| `tools/glslcpp/typed_slice.json` | `bf86b4e7e5e26a89a27f23009eb5a7589618ec54b469b79ffa4cad343f66ccb0` |
| `tools/glslcpp/generate_typed_slice.py` | `ff9cc618c98255ed71714c0384e5f64b613a09f5540457cca4e38b133ad62594` |
| `tests/test_typed_generator.py` | `ece8739c40e37e7e9ac42054d4c647a1f4cdb2543bbd92ed0c2ec0dec275fb27` |
| `tests/test_typed_slice.cpp` | `acfe7fe5483188b3936eb3d02b15f1187f185c2474f341996ce4d764f07b31a0` |
| `tests/test_generated_kernels.cpp` | `fba30769e2ac4e66a173a9fc1c61c2ec920483c6b3b347e9377242d5c6b3035d` |
| `src/typed_generated/typed_slice.cpp` | `3b56d4f69b4477c7306ac659ec6a59c64f0a929d72a56921c28eb9961e82eef8` |
| `src/typed_generated/typed_manifest.json` | `8840aedc26a73c2af8e871cac4a2a41ffb8f107dbaea870902e9b22340614f41` |
| `include/noisemaker/generated/catalog.hpp` | `292c212ffb77e2bc597749899c7211a8134027f556c6b6f5eb03412a037aef6a` |

All twelve protected semantic/IR/emitter/proof/compatibility/runtime/CMake
anchor hashes listed by the design also match. The design requires before/after
hashes for the eight owned paths, a protected census, and failure if any path
outside the inventory changes.

## Source profile and least privilege

Independent current parsing reproduces:

| Lock | Recomputed value |
| --- | --- |
| Raw source | 10,803 bytes; `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` |
| Normalized source | 10,512 bytes; `7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560` |
| Function tuple | 17 functions; `f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a` |
| Whole profile | `73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d` |
| Interface profile | `6ceb3a3a3c7b0263b29d9950790bbe24b186759a4048b593b0a5447b733ae227` |
| Loop/proofs | zero loops, acyclic; Task 17-20 proof fields all `None` |

All 17 function IDs, names, statement counts, and hashes match. The current
vocabulary payload recomputes to
`dd4e14138c6ac72bbc37785faf361660edb418c38afabaf115d5b49d79999b4a`.
The exact Degauss tree validates and emits under that accepted vocabulary.

The design uses a private hard-coded Degauss publication profile, not an ambient
language feature. It authenticates exact corpus entry, source, typed tree,
interface, declarations, resources, metadata, loop state, empty defines,
`glsl-f32`, no transform, and all foreign proofs `None`. Generic validation and
emission remain unchanged. No capability, transform, proof, numeric exception,
type, operator, builtin, loop rule, emitter, typed IR, semantic rule, runtime,
sampler, Surface, resource ABI, CMake entry, dependency, or new file is added.

## TDD, negative, native, and resource gates

The implementation sequence is complete and fail-closed:

- authenticated preflight precedes edits;
- RED/GREEN stages separately establish profile, publication/catalog, and
  binding/native parity behavior;
- the negative matrix covers identity/schema/metadata/interface/resource/tree
  drift, all four foreign proofs, attacker-updated local hashes, every binding
  omission/type mismatch, foreign-key profile reuse, and current-vocabulary
  controls;
- all thirteen canonical semantic mutations have exact function-scoped typed
  locators, while the external oracle retains authority for textual mutation
  counts and divergence/identity surfaces;
- binding tests cover exactly one sampler, three Vec2, four number, and one int
  input; every missing/wrong type rejects and an unrelated extra binding remains
  accepted;
- all nine direct-canonical cases lock complete F32/RGBA8 hashes, eight probes,
  metrics, repeatability, input immutability, top-down/bottom-left orientation,
  finite/copy/alpha behavior, and exact binding/context words;
- generated-body checks scope `pixel` and reachable helpers, forbid a generated
  C++ `main`, require five static level-zero fetch sites, one/13 dynamic fetch
  bounds, and exactly one integer remainder route; and
- fresh Debug, Release, ASan/UBSan, `.su` stack, disassembly/relocation, prior
  oracle, full Python/native, deterministic generation, rollback/tamper, and
  final independent-review gates are mandatory.

The brief and implementation design are ready for Task 21 implementation on the
accepted Task 20 baseline.
