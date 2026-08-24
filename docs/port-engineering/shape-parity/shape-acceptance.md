# synth/shape acceptance record

`synth/shape:shape` accepted as typed row 184, ordinal 181, on 2026-08-16.
**185 of 212 programs ported.** First program of the mutable-global mechanism.

## Final state

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 22,993 | `c03ba30a9bc74697e5db1a9524a047a1dab1b0718ef72f0d4d772327a83f87d2` |
| `src/typed_generated/typed_slice.cpp` | 1,873,454 | `addad95f46f88f3e12234f6905dfa4c5e72222e3fe0dcf118803b99e8ccb4340` |
| `src/typed_generated/typed_manifest.json` | 293,950 | `59e59bd2f8c8d7864304c57e03c12af160c7ad906ff27066d6a7c1127b7de8d5` |
| `include/noisemaker/generated/catalog.hpp` | 17,008 | `8b3b033780f20f1e9d2085ae74f84e87f2258c3eb7518a18c8b6a9dd0fa1bd1e` |

184 typed rows, 186 catalog entries, 28 corpus keys absent from the slice.
Sorted typed-key SHA-256
`026637ff3fec7a9282d4dea84af058acd95612a9f86afff59294062f7f639aec` — over the
sorted keys joined by `\n` **with a trailing newline**.

The slice row carries two carriers:

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "mutable_global_frame_profile": "mutable-global-frame-shape-v1",
  "program_key": "synth/shape:shape",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1"
}
```

## Gates

| Gate | Result |
| --- | --- |
| `check_corpus` / `check_semantics` (212) / `generate_kernels` / `generate_typed_slice` (184) | all exit 0 |
| `tests.test_typed_generator` | 187 / 0 |
| Eight focused test modules | 159 / 159 |
| `tests.test_mutable_global_frame` | 75 / 0 |
| Full Python `unittest discover` | **528 tests, 527 pass**; the single failure is a copy artifact, verified passing live in 1.0 s (see below) |
| Native Debug / Release | **250 PASS / 0 FAIL** each, ctest 1/1, zero warnings |
| ASan + UBSan | **250 PASS / 0 FAIL**, ctest 1/1, **zero ASan and zero UBSan diagnostics** |
| Assembly, ARM64 + x86_64 | clean in pixel scope on both |
| Historical 184 → 183 reconstruction | **exact**; 183/183 surviving blocks byte-identical |

All build lanes carry `-std=c++20 -Wall -Wextra -Wpedantic -Werror
-ffp-contract=off`, verified by reading `flags.make`. **No LeakSanitizer claim**
— `detect_leaks=0` on Apple. `DEFECTS-FOUND.md` item 4 did not reproduce and is
**not** claimed fixed.

## What this program proves

The mechanism exists because two mutable file-scope globals declared one line
apart have **different numeric contracts**: `aspectRatio` is a plain JS Number,
a double never narrowed to f32; `globalCoord` is a `Float32Array` narrowed per
lane. The port must preserve that asymmetry.

It is proven three independent ways:

1. **Structurally** — the closure locks each contract separately, with 29 of 29
   predicates shown load-bearing by source-level deletion.
2. **By oracle** — two mutants with **disjoint witness sets**;
   `shape-globalcoord-unnarrowed` discriminates 1 of 8 cells,
   `shape-aspect-f32-narrowed` 4 of 8. Disjointness is enforced, because a
   shared witness could not attribute a divergence to either contract.
3. **At instruction level** — `pixel` and `shape` contain **zero hardware
   narrowing instructions**. All narrowing routes through the enumerable `f32()`
   helper (22 calls in `pixel`, 7 in `shape`, identical on both arches) and
   `aspectRatio` passes through none of them.

The state proof — the crux — is that both globals have exactly two writes, both
unconditional top-level statements of `main`, with seven reads and no call node
between, so the write dominates every read on every reachable path. Verified
independently by parse, by review, and by the emitted `Frame` being stack-only
at a fixed offset with no static storage emitted for either former global.

## The design was wrong three times, and each correction is recorded

- **Amendment 1** — §1.5 conflated two adapter tables. `check_corpus._ADAPTERS`
  has four keys; `canonicalAdapterFactories` has eleven. Absence from one
  implies nothing about the other; both are now censused. Also: the
  extreme-tile-offset bindability question, listed as unverified, is **resolved
  — it binds**, with 384 witness words shipped so the native phase could prove
  the binding path before a kernel existed.
- **Amendment 2** — two hazards for the array form: `out`/`inout` call arguments
  are an unmodelled mutation path, and failure messages carry a module-level
  profile name that will mislabel the sibling program's failures.
- **Amendment 3** — the assembly gate is clean *conditionally*.
  `typed_181::value` contains a real jump table that stays out of pixel scope
  only because the defines are frozen at 40/30.

## Reviews

Every piece independently reviewed; every review verified by execution.

| Task | Verdict |
| --- | --- |
| Profile closure | Spec ✅ / approved after 1 fix round (3 Important, 3 Minor) |
| Oracle package | Spec ✅ / approved after 1 fix round (3 Important, 3 Minor) |
| Integration | Spec ✅ / **no code defect**; 2 Important + 4 Minor, all claim-accuracy |
| Native parity | Spec ✅ / approved after 1 fix round (1 Important, 4 Minor) |
| Sanitizer + assembly | GO |

Reviewers reproduced rather than read: the historical reconstruction was re-run
independently (catching the reviewer's *own* false mismatch from a block-splitter
bug); the bindability witness was reproduced with a purpose-built C++ probe and
re-derived arithmetically from the raster convention; the materializer fixes were
proven by reconstructing pre-fix logic and confirming it accepted what the fix
rejects; and the liveness probe's premise was verified by confirming
`fullResolution[0]` reaches output through exactly one path.

## A defect this slice fixed beyond its own scope

Both oracle packages — this one and the previous program's — recorded their
run-root snapshot path as provenance, and `--check` byte-compares the
regenerated JSON. Those permanently-checked-in gates could therefore only pass
from the exact machine-specific temp directory that produced them. Verified
broken on a clean path, then fixed at the root: a stable placeholder replaces
the path, the live-checkout location derives from `NOISEMAKER_FOR_CPU` or
`$HOME`, and both materializers now reject any absolute-looking string anywhere
in the document. **Both gates now pass from an arbitrary fresh snapshot path and
still refuse the live checkout** — confirmed independently. Repo-wide
absolute-path files went from 11 to 8.

## Deferred, with reasons

- **Collision chains are mostly unreachable.** Sweeping all 32 sibling profiles:
  all are rejected, but this mechanism's own message answers only 12 of 32 at
  the validator and 6 of 32 at the emitter. Roughly twenty clauses per chain are
  individually unreachable. Inherited across every mechanism in the file;
  recorded as a project-wide trap rather than fixed here.
- **Four changed-lane counts are transcribed from report markdown**, not emitted
  into the `.inc`. A regeneration would leave a stale literal reading as a
  native regression. Generator-lane work.
- **The `out`/`inout` mutation path and the profile-name message prefix** —
  Amendment 2. Both bite the array form, neither bites today.
- **One aspect ledger cell** (`shape-extreme-tile-offset`) has no native
  explanation; reproducing the oracle's measurement needs the mutant. Recorded
  as a boundary, not claimed.

## The one Python failure, and why it is not a regression

`test_emboss_color_style … test_oracle_include_and_frontend_probe_no_write_checks`
fails when the suite runs from a relocated copy, and it did so here for a
**different reason than in the previous slice**. Last time the copy had no
sibling `noisemaker-for-cpu` and the import failed. This time the sibling was
placed deliberately — and the generator's `git rev-parse HEAD` against that copy
failed instead, because the `rsync` excluded `.git`, producing
`JavaScript authority commit drift`. That message reads like a genuine
provenance failure, which is exactly why it must be checked rather than assumed.

Verified passing on the live tree in 1.0 s. Both manifestations are recorded in
`../REMAINING-EFFECTS.md`: a validation copy must reproduce everything the
oracles reach for — sibling layout *and* version-control metadata.

## Claim boundaries

Full-surface parity is **not** evidence that `randomFromLatticeWithOffset`, the
three scalar-uint-XOR sites, or the circles/rings/diamonds/value arms executed —
all are unreachable at defines 40/30. Structural authentication, mutation
coverage and the direct numeric tests carry that proof.
