# cellRefract186 — acceptance record

`classicNoisedeck/cellRefract:cellRefract` accepted as typed row 186
(2026-08-17), namespace `typed_2` between `cellNoise` (`typed_1`) and
`coalesce` (`typed_3`). First program of the **mutable uninitialized global
`float[9]` array** mechanism (`mutable-global-nine-array-cellrefract-v1` in
`tools/glslcpp/frontend/mutable_global_array_profile.py`, dict-keyed shared
module) plus the per-key `cellrefract-convolve-v1` record in the dict-keyed
`fixed_array_in_parameter_proof.py`. Design
`cellrefract-design.md` §§1-10 with Amendments §§11-17 (authoritative);
frozen GO review `cellrefract-design-review.md`.

## Slice row

```json
{
  "defines": {"KERNEL": 0, "SHAPE": 1},
  "mutable_global_array_profile": "mutable-global-nine-array-cellrefract-v1",
  "program_key": "classicNoisedeck/cellRefract:cellRefract"
}
```

## Post-slice artifacts (quoted from the generated files at regeneration;
re-quoted once after the Amendment §17 lowering correction)

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 23,429 | `ffaff05c37d718e0e3b7bae6fe2da5a46c44599410a8d88db419cae136b5ec5f` |
| `src/typed_generated/typed_slice.cpp` | 1,923,368 | `124bffb1052c1000027359771553d168ed42cbab5fcf341f769c076e7b1f6884` |
| `src/typed_generated/typed_manifest.json` | 297,339 | `08737353b0c00bfe3833adbc207238ae2b13b139b70240851c493661ec58a838` |
| `include/noisemaker/generated/catalog.hpp` | 17,204 | `9b79eb4219f9dfbc086ecde62d6a5a3a726458cf1072a9cc44de33f42a52284c` |

Census: 186 typed rows; 188 catalog binds; corpus keys absent 26; genuinely
unported 25 (`wormhole:deposit` remains the one public-outside-slice);
sorted 186-key SHA-256 (trailing newline) `1f4e8a51182aa8d71954a48f0b810b4732478e6e61ed14241c37446278102c21`;
define-bearing rows 28; capabilities 44 / types 17 unchanged;
`factories.size()` assertion 187U → 188U (`tests/test_generated_kernels.cpp`).

## Gates

- **Generator gates**: `check_corpus`, `check_semantics`,
  `generate_kernels`, `generate_typed_slice` — all `--check` exit 0 at 186
  programs, re-verified after the §17 correction.
- **Focused Python** (five touched modules):
  `test_typed_generator` + `test_mutable_global_array` + `test_semantic` +
  `test_mutable_global_frame` + `test_const_global_table` — 592/592.
- **Full Python** (module-count-asserting scratch runner, 21 modules): 908
  tests, 2 failures — **both proven to be the runner harness's own
  environment bug** (`TMPDIR` expansion ran in a fresh shell and pointed the
  two `clang++`-spawning native-sensitivity tests at a nonexistent path;
  both tests pass in 6.4 s in isolation under correct env). A second rerun
  with correct env raced the parallel kaleido187 landing mid-run and is
  discarded; the 186-state's module-level truth is the 7 repaired modules
  green in isolation (84/84) plus the wave-end combined suite at 187+
  programs. No repo test failed at the 186 state.
- **Native**: Debug / Release / ASan+UBSan each **262 PASS / 0 FAIL**,
  ctest 1/1; zero sanitizer diagnostics (no LeakSanitizer claim —
  `detect_leaks=0` on Apple); `-Wall -Wextra -Wpedantic -Werror
  -ffp-contract=off` confirmed in `flags.make` for both configs.
- **x86_64** (Release): 260 PASS / 2 FAIL — both failures **pre-existing at
  HEAD `8edff08`** (254/2 at HEAD; the +6 are this slice's tests, green on
  x86_64). Root cause measured and banked in
  `../x86-64-divergences/x86-64-divergences-report.md`: hardware NaN sign
  (`divsd` `0xffc00000` vs `fdiv` `0x7fc00000`) at two division sites, and
  **the JS authority itself produces the same arch-dependent bytes** (x86_64
  node reproduces the port's values; arm64 node reproduces the pins;
  kernel identity proven across runs). Classification: inherent cross-arch
  materialization; recommended repair is per-arch dual-pinning, recorded
  not fixed (pre-dates this slice).
- **Oracle provenance**: `cellrefract186_oracle_generator.mjs --check`
  green from the snapshot (4 cases, 4 ledger mutants, controls, tile
  non-crop 70/96); include materializer `--check` + `--self-test` (81
  checks) green; refusals of live-checkout/containment verified; six CPU
  file pins matched before pinning.
- **Native parity**: six `typed_cellrefract186_*` tests — exact float32
  word + RGBA8 parity on all four independent JS oracle cases
  (public/direct/repeat routes, independent buffers), custom-comparer
  self-tests, the 15-binding ABI matrix (omit + wrong variant each, extras
  neutral, immutability, input-digest gate), the §15 measured tile
  non-crop re-derived natively (70/70, raw-crop-y trap 47), inert-binding
  and phase axes, mutant-ledger necessary conditions.
- **Assembly**: GO on ARM64 and x86_64 (demangled resolution, per-arch
  patterns). Pixel scope = `pixel` → `cells` (+ inlined `map`/`prng`/`pcg`/
  `smin`): zero indirect branches, zero jump tables anywhere in the TU on
  either arch, zero multiply-add-family fused FP TU-wide (the
  `-ffp-contract=off` witness), fixed-size frames, no allocation/virtual/
  container/string work, binder machinery outside pixel scope. **The Frame
  is dead-store-eliminated**: `loadKernels` has zero callers TU-wide, the
  360-byte alloca never materializes (96/104-byte pixel frames), and the
  dead `frame` argument's registers are never written — the disassembly is
  an independent compiler-level witness for the write-only/read-census-empty
  property. typed_2's single systemic `___clang_call_terminate` pad sits in
  `hsv2rgb` (dead at the frozen defines; the known non-noexcept-Vec
  condition). 13 unrelated `fnmul` elsewhere in the TU reported for
  strict-family honesty (not fp-contract artifacts).
- **Historical reconstruction 186 → 185**: pre-slice baselines verified
  byte-for-byte against HEAD first; removing only the cellRefract row
  recovered all four 185-state hashes exactly (`69deb0c8…`, `e7b52cd1…`,
  `de223751…`, `4c30f680…`), prior 185-key SHA `75ea3f39…`, set difference
  exactly cellRefract, 185/185 surviving blocks byte-identical after
  `typed_N` normalization; splitter sanity-checked on an unchanged adjacent
  pair first.

## Claim boundaries

1. **The five kernel tables are write-only at the frozen defines** and
   their readers, `convolve`, and the local-table helpers are unreachable:
   no oracle case can discriminate any mutation of their contents. Their
   protection is structural (per-lock RED/GREEN identity locks +
   delete-the-check sweeps at both the profile and proof modules), and the
   assembly independently witnesses the elimination. Amendment §17's two
   rvalue compound assigns are in the same class.
2. **The tile route is a measured non-crop of the full route** (Amendment
   §15; mechanism proven). The crop identity is program-shaped; citing this
   slice as precedent for a universal crop contract is forbidden.
3. The mutant ledger's four kept mutants intentionally share witness sets
   (they pin different reachable functions); no disjointness requirement,
   unlike shape/normalMap. The near-ULP `prng` divisor axis is invariant
   everywhere and is recorded, not budgeted.
4. `resolution` and `effectWidth` are measured inert at the frozen defines
   (0 lane-reads); they remain required ABI bindings and are ABI-tested.
5. The 186-state full-suite figure carries the harness caveat above; the
   authoritative full-suite figure for this slice's tree is the wave-end
   combined run at 187+ programs.

## Process record

Ten dispatched lanes; every dispatched review reported before this record
was written (design GO review; three-design review of the follow-on
preparations; delete-the-check sweeps per module). Controller errors this
slice, corrected: the §17 arm's first lowering reused the scalar compound
form and did not compile for vec targets (caught by the native lane in a
scratch build, fixed at the emitter, re-quoted pins); two artifact pins
were re-quoted after the fix (never hand-computed). Parallel-lane races
(kaleido's record flipping the live census during verification; Lane I's
rerun racing the kaleido landing) were recognized and contained by the
landed/prepared split and by discarding the raced run — the wave model's
known cost, paid knowingly.
