# Prepared designs review (kaleido / varying / effects) — verdicts GO, GO-WITH-CORRECTIONS, GO-WITH-CORRECTIONS

**Frozen record. Never edit.** Independent review of three
pre-implementation design documents —
`kaleido-parity/kaleido-design.md`, `varying-parity/varying-design.md`,
`effects-parity/effects-design.md` — executed 2026-08-16/17 against the live
`noisemaker-for-cpp` frontend, the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, and the read-only
`noisemaker-for-cpu` JS authority. The reviewer re-derived the checkable
figures through the real modules rather than re-reading the designs'
numbers. Because all three documents are pre-implementation living designs,
every correction below was folded IN PLACE into the doc it amends before
anything could freeze from their tables; each doc's final
`### Independent review (2026-08-17)` section records the verdict, the
corrections applied, and points here. This file freezes the verdicts and
findings as the review returned them.

## 1. `kaleido-parity/kaleido-design.md` — verdict **GO**

Three Minor findings; no Important finding; the mechanism decomposition
stands as written.

1. **§9 test-count bookkeeping (folded at §§0 and 9).** The lock-deletion
   class has **35 test methods** — 29 via `_delete_and_compare` plus the
   direct-scratch tests — not the doc's "a 33-test lock-deletion class" /
   "33 in-suite `_scratch` deletion tests"; and §0's "three new
   admission/surface classes" is **five** classes: Surface 4, Admission 16,
   LockDeletion 35, Ledger 3, Vocabulary 2. Counts corrected.
2. **§5 integration list — a second `_MUTABLE_GLOBAL_ARRAY_DEFINES`
   consumption site (folded at §4.5, the doc's integration list).**
   `load_slice`'s `expected_defines` entry
   `MUTABLE_GLOBAL_ARRAY_CELLREFRACT_KEY: _MUTABLE_GLOBAL_ARRAY_DEFINES` at
   `generate_typed_slice.py:1456` (inside `load_slice`) also becomes
   per-key; missing it fails closed with a schema-drift error. (The doc
   already cites `:611` and the `:1391-1396` census.)
3. **§1 — the convolve read spans (folded at §4.3, where the spans live).**
   `564:25-564:34` / `567:25-567:34` are the **index-expression** spans;
   the `id` nodes are `564:25-564:31` / `567:25-567:31` (same sites; the
   record should freeze which node).

## 2. `varying-parity/varying-design.md` — verdict **GO-WITH-CORRECTIONS**

One Important and three Minor findings.

1. **Important — §1.4's spookyTicker interface SHA-256 has a one-hex-digit
   transcription error.** The measured value is
   `3d84a19370581017b270e9ffd5a4a2794e4976e8047b1427955e38a8f6abf5ce`; the
   doc had `…55e3888f6abf5ce` (char 57 'a' vs '8'). Figure fixed; the
   correction noted in the doc's review section.
2. **Minor — §5.1's module filename.** §5.1 names the module file
   `varying_profile.py`; the LANDED module is
   `tools/glslcpp/frontend/varying_uv_profile.py` (82 tests green, empty
   registry; capability / row-field / kwarg all match the design). §5.1
   amended to make the landed filename authoritative — renaming landed code
   for cosmetics churns the tree.
3. **Minor — the wormhole.cpp scatter-registration citation is
   `src/effects/scatter/wormhole.cpp:173` (inside `register_adapter()`),
   not `:207`.** Fixed.
4. **Minor — §1.7 presents a paraphrase as a quote.** The actual
   `preprocess.py:60` comment is `# codegen maps varyings to ctx.uv`. The
   design now quotes the real comment.

## 3. `effects-parity/effects-design.md` — verdict **GO-WITH-CORRECTIONS**

Three Important findings and several Minor ones.

1. **Important — §1's node census is wrong.** Measured **2,638 nodes / 235
   assigns**; the doc said 3,117/235 — a digit transposition of kaleido's
   3,178. Fixed.
2. **Important — §1's call-graph digest is wrong.** Measured
   `cb421a62eb9d14a121e746b6bffea51e7c188db10230a95f77349bbb2ef2c3da`; the
   doc said `382ce57b…041e` (the edge count 30 is right). Fixed.
3. **Important — a third module carve the ladder could not see.**
   `ceil_admission_profile.py` names `fixed_array_in_parameter_proof` in
   `_OPTIONAL_PROOF_FIELDS` (`:42-46`, checked `:155-157`) and will reject
   effects' row — `ceil-admission-v1: unrelated proof carrier is not
   absent` — until it gets the same per-key carve as the glitch module. The
   §6 ladder bypassed the module authenticator so the lane never saw it.
   Added to §4.5's carrier-side integration list, with the generic family
   lesson stated once: **every companion module freezes its own FAP-absent
   set — check each new companion for the carve (XOR for kaleido; glitch
   AND ceil for effects).**
4. **Minor — three figures.** §3's `canonical-kernels.js` byte count is
   **1,713,290** (not 171,329; the SHA is correct). The emitter
   contract-driven cardinality site is `emit_typed_cpp.py:1954` (not
   `:1955`). Factory7's `loadKernels` is `:2481-2547` (not `:2480-2546`).
   All three fixed.
5. **Minor/scope — §6's "both ladders terminate CLEAN" / "651 lines" are
   lane-measured.** The review confirmed them only through validator rungs
   0-2, emitter rungs 0-2, and the §4.4 fragments (no contradiction found;
   termination not independently re-run). Marked as such in §6.
6. **The `generate_typed_slice.py:1456` `expected_defines`
   second-consumption-site note (same as kaleido's)** added to §4.5's
   validator-side list.

## 4. Cross-document assessment

- **Ordering internally consistent**: kaleido integration → effects →
  varying/wobble, as the three docs each argue.
- **Shared surfaces compatible**: the surfaces the designs share are wired
  compatibly across the three plans.
- **Two recurring misses, stated generically**: (a) the
  `generate_typed_slice.py:1456` `expected_defines`
  `_MUTABLE_GLOBAL_ARRAY_DEFINES` second consumption site inside
  `load_slice`; (b) companion-module absent-set carves — every companion
  module freezes its own FAP-absent set, so each new companion must be
  checked for its carve (XOR for kaleido; glitch AND ceil for effects).
