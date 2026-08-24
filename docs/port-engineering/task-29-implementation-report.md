# Task 29 implementation report: Focus Blur borrowed-sampler ABI

Date: 2026-08-12
Author: continuation agent (handoff from `NEXT_CODING_AGENT_HANDOFF.md`)

## Result

Task 29 is implementation-complete and fully gated. The blocker described in
the handoff — 20 stale Task 25–28 stage failures in full Python discovery — is
resolved. Full discovery is green with no failures.

Accepted state:

| Quantity | Value |
|---|---:|
| Typed programs | 129 |
| Public programs | 131 |
| Publicly unported | 81 |
| Corpus programs | 212 |
| Focus Blur public ordinal | 110 |

Ordered-list hashes (unchanged from the accepted design):

- typed `c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9`
- public `2325f8d06d182800af90cd1b0b67efe9d3058d3682f0ceb4d3f5168ff4af5e16`

## Work performed in this session

The prior session's Python-test owner had already completed the integration
repair; its process did not survive the handoff, so its edit was verified
forensically rather than by supervision. No Git was used.

1. **Verified the repair's file scope by hash, not by claim.** Every production
   file still matches the handoff checkpoint table byte-for-byte. Only
   `tests/test_typed_generator.py` changed (`047f4eef…` → `ca259317…`). This
   confirms the "Python-only repair" claim independently and establishes that
   the recorded Debug/Release/sanitizer lanes were not invalidated by
   production drift.

2. **Ran full Python discovery uninterrupted.** 186 tests, 1026.547 s, `OK`,
   exit 0.

3. **Ran the corpus/generator/oracle gate** with per-command exit-code capture
   (no shell loop returning only the last status).

4. **Ran fresh Debug, Release, and ASan/UBSan lanes** in newly created build
   directories.

5. **Corrected one honesty defect in the native tests** (below).

6. **Censused the entire remaining frontier** to replace per-program guesswork
   with measured data (`docs/port-engineering/frontier-census.json`,
   `frontier_census.py`).

## Defect found and fixed: an overstated native counter test

`tests/test_generated_kernels.cpp` contained:

```
TEST(typed_task29_selected_focus_path_executes_sixty_seven_reads_and_size_queries)
```

This test does **not** instrument the generated Focus Blur kernel. It calls
`task29_trace_selected_focus_path`, a hand-written reference model that mirrors
the kernel's sampling structure through the real sampler API and counts its own
calls. The generated kernel exposes no interception point, so a genuine dynamic
measurement is not available without changing production code for test
purposes, which would be worse.

The 67/67 figure itself is correct — verified by reading the emitted code
directly. `applyFocusBlur` performs one depth `sample_texture` plus one inside
the authenticated 64-trip loop, and `pixel` performs the two alpha-source
sites, each paired with a `texture_size` call: 1 + 64 + 2 = 67 of each per
pixel. But the figure is **derived**, and the test name asserted it as
**measured**. The handoff explicitly forbids inferring semantics from
structure while presenting it as direct evidence.

Fix applied (test-file only, no production change):

- Renamed the test to
  `typed_task29_reference_trace_model_matches_derived_sixty_seven_read_profile`.
- Documented at the reference model's definition exactly what it does and does
  not prove, and named the three artifacts that carry the real evidence:
  the Python-pinned static site counts, the counted-loop proof, and the
  six pixel fixtures against the independent JavaScript oracle.

The test name was confirmed not to be load-bearing before renaming: the Python
transcription test pins the *function* name `task29_trace_selected_focus_path`
(in `dispatch_suffix`), not the test name, and no whole-file hash of
`tests/test_generated_kernels.cpp` is asserted anywhere.

## Parity evidence chain

Focus Blur's semantic parity does not rest on the counters. The chain is:

1. `task-29-oracle-generator.mjs` is hermetic and reproduces under `--check`.
2. `task-29-oracles.json` is hash-pinned
   (`b16c120e2331d87b61b98154d63954ad52ff328f149ebeb67b66321b73bde0a3`).
3. `test_task29_cpp_tables_switch_helpers_and_witnesses_are_exact_frozen_transcription`
   asserts the native C++ fixture tables are an exact transcription of that
   JSON — the independence link.
4. The native fixtures execute the generated kernel and compare F32/RGBA8
   hashes, dimensions, finite lanes, and five pixel probes per case.

## Verification (all fresh, this session)

### Full Python discovery

```text
Ran 186 tests in 1026.547s
OK
EXIT=0
```

### Focused Task 29 class, after the native-test fix

```text
Ran 7 tests in 82.259s
OK
```

### Corpus, generator, and oracle gate

```text
check_corpus --check                  exit=0 PASS   (check_corpus: ok)
check_semantics --check               exit=0 PASS   (bodies ok, 212 programs)
generate_typed_slice --check          exit=0 PASS   (typed slice ok, 129 programs)
generate_kernels --check              exit=0 PASS
oracle task-15 … task-29 --check      exit=0 PASS   (15 of 15)
failures=0
```

### Native lanes

```text
debug configure/build/ctest           exit=0 PASS
release configure/build/ctest         exit=0 PASS
sanitize configure/build              exit=0 PASS
sanitize run                          exit=0 PASS
failures=0
```

Sanitizer procedure preserved: attempt 1 ran with `detect_leaks=1` and aborted
with exit 134 and the platform message `AddressSanitizer: detect_leaks is not
supported on this platform`. The prescribed leak-disabled retry then passed
with exit 0. The first attempt was not skipped.

Native run after the rename: exit 0, including

```text
PASS typed_task29_focus_blur_public_oracles_are_exact_repeatable_finite_nonmutating_and_lifetime_safe
PASS typed_task29_focus_blur_binding_abi_rejects_every_missing_and_wrong_input
PASS typed_task29_direct_borrow_switch_executes_eight_distinct_fail_closed_modes
PASS typed_task29_reference_trace_model_matches_derived_sixty_seven_read_profile
```

### Task 28 reconstruction (checklist item 8)

Covered by
`test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation`,
green inside the 186. It removes only Focus Blur from the current pipeline via
`mock.patch` of `load_slice` (necessary because `load_slice` pins the live
129-program list and its hash) and asserts byte-identical Task 28 outputs:

- `src/typed_generated/typed_slice.cpp` `b53e020b…900763e`
- `src/typed_generated/typed_manifest.json` `612d3522…c91de044e`
- `include/noisemaker/generated/catalog.hpp` `372d1f69…b85135a4ac`

It further asserts 129 vs 128 emitted blocks, that the sole difference is
Focus Blur, and that every retained block is ordinal-normalized identical.

## Known limitation, documented rather than concealed

`docs/port-engineering/task-29-recompute.py --check` now exits 1 with
`StopIteration` at line 464. Confirmed first-hand this session. The frozen
design-time script enumerates the *unsupported* frontier and looks Focus Blur
up within it; now that Focus is supported it is absent, so the lookup raises.
This is an expected consequence of a design-time artifact outliving its design
phase, not a regression. The frozen artifact and its sidecar are left
unmodified; no false live-pass is claimed.

## Final file hashes

| File | SHA-256 |
|---|---|
| `tools/glslcpp/frontend/focus_blur_borrowed_sampler_profile.py` | `cc0f9333b3b3064d985276af0199720a2da68fd27d0328cac6d565bbee1076b5` |
| `tools/glslcpp/generate_typed_slice.py` | `fad0a79dd514ce590182bbb37e02cd02090b15d1e88c7cb21c93d68fa9617145` |
| `tools/glslcpp/emit_typed_cpp.py` | `fe0ba3939ac94c0d09af2c17a206db997fe258ab2bb43a39851e3d4447864426` |
| `tools/glslcpp/typed_slice.json` | `1a9525a4854180a94430cfbb8e260f498d5c8a583d5e3b8d3ec030f317f3417b` |
| `src/typed_generated/typed_slice.cpp` | `358847db37675afd7f173341c66f71527af04c8ac817efddcc7d4b7cf31551aa` |
| `src/typed_generated/typed_manifest.json` | `01bfe3c139e8352ad04ac87ed5817715166dff371e983361f8cbb7fefe650351` |
| `include/noisemaker/generated/catalog.hpp` | `2d32511c858a5caeedb7c4fe1b2d985191e639a9e4ed1d98ca9219a60b668304` |
| `tests/test_typed_generator.py` | `ca259317ad873384ca2b1c9c4bc45d7f0ffcd43a49027a148eb8fdf14e2a50f3` |
| `tests/test_generated_kernels.cpp` | `d4ee41faf19f62f6a2ea85cec2887be0fef059ccc07b10177f232be8952f2d80` |

Every production file is byte-identical to the handoff checkpoint. The two
test files changed: `test_typed_generator.py` by the prior session's
integration repair, `test_generated_kernels.cpp` by this session's honesty fix.

## Frontier state after Task 29

83 corpus programs remain outside the typed slice. Two of them
(`filter/invert:inv`, `synth/solid:solid`) are the older manually ported public
programs and already pass validator and emitter, leaving exactly 81 genuinely
unported — reconciling independently with the handoff's count.

Measured blocker distribution is in `frontier-census.json`; the family analysis
and recommended order are in `roadmap/remaining-capability-roadmap.md`.

---

## Addendum: post-review fixes and final acceptance

The independent implementation rereview
(`task-29-implementation-rereview.md`, SHA-256
`f7bb88c37fd9946f88d2b179ae7324a51ebb25549c73b2ff27d9e631a2d26c76`) returned
**ACCEPT** with 0 Critical, 0 Important, 2 Minor, 1 Nit. It independently
re-derived the load-bearing claims rather than reading this report: it
reproduced the ABI-leak rejection live, called the emitter bypassing the
validator entirely, cross-checked every frozen historical hash against Task
26/27/28 documents authored before Task 29 existed, ran the 89-axis mutation
test and both real byte-reconstruction tests live, hand-counted the 67/67
derivation, and did two fresh from-scratch builds (Release `-Werror`;
Debug + ASan/UBSan), 143/143 native tests passing in each.

Actions taken on its findings:

- **N1 (Nit) — fixed.** The reference-model disclosure comment sat ~400 lines
  above the `TEST()` that relies on it. A pointer comment now sits directly on
  the test.
- **M1 (Minor) — documented, not silently left.** Three pre-existing tests
  (`test_task21_degauss_exclusions_remain_closed`,
  `test_task22_crt_exclusions_remain_closed`,
  `test_task26_loader_admits_only_exact_smooth_carrier_and_census`) have
  task-numbered names implying historical reconstruction, but exclude only the
  two most-recently-added generalized-profile programs, leaving later
  additions such as `synth/perlin:perlin` present. Confirmed pre-existing and
  mechanically extended, not introduced by Task 29. Each now carries a comment
  stating it is **not** a historical reconstruction and pointing to the tests
  that genuinely are. The assertions themselves were not weakened.
- **M2 (Minor) — no action, by design.** `task-29-recompute.py --check`
  surfaces its expected failure as a raw `StopIteration`. It is a frozen
  design-time artifact and was correctly left untouched.

### Publication blocker found and fixed during hygiene audit

Nine tests in `tests/test_typed_generator.py` read frozen oracle fixtures from
`docs/port-engineering/`, a machine-local scratch directory. On a fresh
public clone — or in CI — those tests would fail outright, since the evidence
directory does not exist outside this workstation.

Fixed by vendoring the seven fixtures into `tests/oracles/` (552 KB total,
byte-identical: task-29's `b16c120e…` matches the hash the test already
asserts) and repointing all nine reads to `REPOSITORY / "tests/oracles/…"`.
No expected hash changed; the tests pin exactly the same bytes.

### Final verification after all fixes

```text
Full Python discovery:  Ran 186 tests in 1091.339s  OK  EXIT=0
Native (Debug):         143/143 PASS, exit 0
Example target:         builds -Werror, renders 256x256 PNG, 131 catalog kernels
```

### Final hashes after post-review fixes

| File | SHA-256 |
|---|---|
| `tests/test_typed_generator.py` | `6579e0e9eaa82b659588eaddfaccb5e91582c78e380cea9ffc727e29eea25261` |
| `tests/test_generated_kernels.cpp` | `9cde5366e0699580eb68c5cddb593cf6ad1a4d8445ff5611dcb35ddc8a385424` |

All seven production files remain byte-identical to the handoff checkpoint;
their hashes are unchanged from the table above.

**Task 29 is accepted.**
