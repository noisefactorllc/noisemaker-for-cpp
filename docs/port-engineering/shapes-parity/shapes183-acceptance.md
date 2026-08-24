# Shapes183 acceptance record

`classicNoisedeck/shapes:shapes` accepted as typed row 183 on 2026-08-16.
This is the durable summary; the working run root it was produced in has been
deleted, per the storage gate.

## Final state

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 22,728 | `8fb3b8bc876c380a0c406fdae8e81b74d4499924cf301ed7a980c450f7ccfe0a` |
| `src/typed_generated/typed_slice.cpp` | 1,819,738 | `b3b53be504f0e84879d443418f6fe17af5d0605c9589c64e4a21d4e19f803cf5` |
| `src/typed_generated/typed_manifest.json` | 292,207 | `5281d964596734fc447c4d0450906bc2c7fbd6ee7b7e1e971b8ee563c62daab0` |
| `include/noisemaker/generated/catalog.hpp` | 16,926 | `44b05685a3bdd263df1bd8834b8f994e6fc63b1a7717b2111b06e74272411be0` |

183 typed rows, 185 catalog entries, 184 of 212 ported, 28 genuinely unported.
Sorted 183-key SHA-256
`b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b` — computed
over the sorted keys joined by `\n` **with a trailing newline**.

Shapes carries **four** carriers at typed ordinal 8:

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "program_key": "classicNoisedeck/shapes:shapes",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1",
  "linear_srgb_lane_index_profile": "linear-srgb-shapes-lane-index-v1",
  "shapes_float_bits_ingress_profile": "shapes-float-bits-ingress-v1",
  "shapes_rvalue_assign_profile": "shapes-rvalue-assign-v1"
}
```

## Gates

| Gate | Result |
| --- | --- |
| `check_corpus --check` | exit 0 |
| `check_semantics --check` | exit 0, 212 programs |
| `generate_kernels --check` | exit 0 |
| `generate_typed_slice --check` | exit 0, **183 programs** |
| Full Python `unittest discover` | **441 tests**, 1 failure — a copy-path artifact, verified passing on the live tree (see below) |
| Native Debug | **242 PASS / 0 FAIL**, ctest 1/1, 0 warnings |
| Native Release | **242 PASS / 0 FAIL**, ctest 1/1, 0 warnings |
| ASan + UBSan | **242 PASS / 0 FAIL**, ctest 1/1, **zero ASan and zero UBSan diagnostics** |
| Assembly, ARM64 + x86_64 | clean in pixel scope on both; zero fused FP across all 53 namespace functions |
| Historical 183 → 182 reconstruction | **exact** — all three pre-change hashes byte-for-byte, all 182 surviving blocks unchanged |
| Repository storage audit | 0 added, 0 changed outside the retained-product allowlist |

All three build lanes carry `-std=c++20 -Wall -Wextra -Wpedantic -Werror
-ffp-contract=off`, verified by reading `flags.make` rather than the CMake
invocation.

**No LeakSanitizer claim is made.** On Apple `detect_leaks=0` means LSan did not
run.

**The one Python failure was not a regression.** `test_emboss_color_style …
test_oracle_include_and_frontend_probe_no_write_checks` fails when the suite runs
from a relocated copy, because `emboss_parity_oracle_generator.mjs` resolves the
JavaScript reference as a **sibling of the repository root** via a hardcoded
`../../../../../noisemaker-for-cpu`. Verified passing on the live tree in 1.1 s.
Recorded as a standing trap in `../REMAINING-EFFECTS.md`.

**The known pre-existing `synth/bitwise` signed-overflow UBSan diagnostic
(`../DEFECTS-FOUND.md` item 4) did not reproduce** in the sanitizer lane; both
bitwise tests ran and passed. Nothing appeared, so there was nothing to confirm
as the same diagnostic — it is **not** claimed fixed and item 4 keeps no
resolution marker.

## What the slice changed about the design

Three amendments, all in `shapes183-design.md`. Each records something the
design asserted that implementation disproved:

- **§11** — the bound-`seed` control the design demanded is *unsatisfiable*. At
  defines 40/30, `seed` reaches nothing live; the shader documents this at
  `shapes.glsl:12-19`. The axis is recorded and proven **invariant** instead,
  which is a genuine parity assertion rather than a waived test.
- **§12** — a fourth closure was required for `float angle = rot *= PI;`.
  `assign` was already in the frozen 44-entry vocabulary; the gap was purely a
  missing `assign` arm in the emitter's expression dispatcher. The lowering was
  settled by reading the shipped JS, which keeps the rvalue form **while four
  sibling factories fold it**.
- **§13** — the assembly gate is clean *conditionally*. `typed_8::value`
  contains a real jump table that stays out of pixel scope only because the
  defines are frozen at 40/30.

Sections 1-10 of the design are unedited apart from one inline retraction
marker, so the frozen GO review remains auditable against them.

## Review coverage

Every piece of work in this slice was independently reviewed, and every review
verified by execution rather than by reading:

| Task | Verdict |
| --- | --- |
| Oracle package (phase 1) | Spec ✅ / approved, 3 Minor |
| Profile closures (two) | Spec ✅ / approved, 3 Minor |
| Third closure (rvalue assign) | Spec ✅ / approved after 1 fix round |
| Integration and schema | reviewed |
| Native parity (phase 2) | Spec ✅ / approved, 3 Minor; 2 fixed, 1 deferred |
| Sanitizer + assembly | PASS |

Reviewers defeated old code rather than reading new tests: the materializer
fixes were verified by reconstructing the pre-fix logic and confirming both new
scenarios were *accepted* by it; the crop translation was re-derived from the
generated `.inc` alone (0 mismatches at correct rows, 51 at flipped rows); the
census tightening was proved non-widening across 150 synthetic combinations.

## The last barrier locked

The integration review found the one remaining unlocked barrier in the slice:
the widened emitter `assign` arm was **correctly gated but had no regression
lock**. The gate rejects a foreign rvalue assignment today — proven both
directions — but nothing caught the gate being *removed*.

`tests/test_typed_generator.py::test_typed_emitter_refuses_raw_or_unsupported_nodes_with_program_span`
now carries a case rendering
`out vec4 fragColor; void main() { float b = 1.0; float a = b *= 3.0; fragColor = vec4(a); }`
and asserting `TypedEmissionError` matching
`unsupported-assign:1:.*unsupported typed expression assign`.

Proven load-bearing by removing the identity gate in a scratch copy:

| with the gate REMOVED | result |
| --- | --- |
| `generate_typed_slice.py --check` | **exit 0** — the gate is invisible to it |
| `tests.test_shapes_rvalue_assign` (30 tests) | **OK** — never calls the emitter |
| **the new case** | **FAILED** |

Restoring the emitter byte-identically returns it to OK. Both things that might
otherwise have been cited as coverage demonstrably do not cover it. This is why
the standard in this project is to delete the check rather than mutate the
input — the sixth vacuity the method has caught in this slice.

## A note on lost evidence, and why it was not regenerated

The owned run root was deleted before the integration review had reported,
which was a controller error. It took with it a 729-line implementer report
(RED boundary, the 42:19 block and its resolution, four-carrier wiring, the
seven-node ledger, the fail-closed matrix, 41/41 projected state, the
reconstruction, and the full step-6 classification record) and the associated
probe scripts and transcripts.

**It was deliberately not regenerated.** Every load-bearing claim in that report
was independently re-derived from scratch by the review — which recomputed all
nine acceptance numbers, re-ran the historical reconstruction itself, built its
own 11-case fail-closed matrix, instrumented the real generation to confirm the
seven-node ledger, and independently classified 13 repair sites before looking
at the edits. An independent re-derivation is stronger evidence than the
implementer's own narrative of the same work, so regenerating the probes would
have been re-work producing weaker evidence than what already exists here and in
the design amendments.

The operational lesson is recorded in `../REMAINING-EFFECTS.md`: a slice is not
done until every dispatched review has reported, and a shared run root must
never be deleted while any agent might still be reading it.

## Codebase-wide gap surfaced by this slice

**No closure in this codebase locks its carrier-guard messages.** The integration
review found that no test references any of the four new guard strings
(`exact Shapes float-bit ingress profile carrier required`, `Shapes rvalue-assign
profile metadata mismatch`, and the others), nor either RED-preflight rejection.
The guards demonstrably fail closed — verified by an 11-case matrix from the
implementer and an independent 16-case reproduction from the reviewer — but both
live in throwaway probes.

This is **not** specific to Shapes. Scanline Error, Caustic, Linear sRGB, and
Glyph Map all have zero test references to their equivalent guard messages. The
slice matched codebase convention rather than departing from it, which is why it
was not treated as a defect here.

Worth a dedicated pass: every carrier guard should have a test asserting its
specific message, so that a guard silently rewritten or removed turns something
red. Today the only thing standing behind them is that someone once ran a probe.

## Deferred, with reasons

- **Oracle JSON `claim_boundaries` omits the rvalue lowering.** Adding it would
  move the JSON hash, force a `kOracleSha256` edit, and retire the clean "the
  delta is only two provenance digest strings" proof used to confirm nothing
  regressed. The boundary is stated in the C++ source comment and the oracle
  report. Trading a verified provenance proof for a redundant restatement is a
  bad trade.
- **Two censuses walk only `function.body`**, so a node in a global declaration
  initializer is covered by coarse hashes but not by the census. Inherited from
  the `scanline_error_float_bits_ingress_profile.py` precedent both were modelled
  on — systemic across at least three modules, needing a dedicated pass. The
  *new* third closure does walk global initializers and does not inherit the gap.
- **`glsl::Vec<N,T>::Vec(const FloatExpr<N>&)` lacks `noexcept`**
  (`glsl_types.hpp:164`), putting an LSDA and terminate landing pad in 51
  functions including other programs' `pixel`. Pre-existing, systemic, and a
  cheap broad cleanup for someone.
- **Two sub-Minor items on the third closure**: one hole covered by a unit
  assertion where its sibling got an end-to-end test, and a dead `parent`
  argument at `shapes_rvalue_assign_profile.py:394`.
