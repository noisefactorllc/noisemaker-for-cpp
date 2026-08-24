# Task 16 final acceptance re-review

## Decision

**APPROVED.** No remaining P0–P3 findings were identified in the corrected
discarded-local-counter admission boundary or in the Task 16 generated/oracle
artifacts reviewed here.

## Resolution of the prior P1

The prior review demonstrated that a forged in-memory typed tree could weaken
the rank-update predicate from

```text
otherLum > myLum || (otherLum == myLum && sampleX < x)
```

to `otherLum > myLum` while retaining authentic source bytes, hashes, spans,
symbols, and stored proof data.  Repeating that mutation against the corrected
implementation now rejects at both independently recomputed boundaries:

```text
validator: REJECTED: filter/pixelSort:computeRank:34:13:
  malformed discarded local-counter proof
emitter: REJECTED: filter/pixelSort:computeRank:34:13:
  malformed discarded local-counter proof
```

`local_counter_proof.py` now admits the proof only when it finds the exact
direct `main` layout: the local declarations and `NUM_SAMPLES = 32`, canonical
`s = 0; s < NUM_SAMPLES; s++` header, four-statement loop body, earlier
`sampleX == x` continue, and the complete `>` / `||` / `==` / `&&` / `<`
predicate over the stable `otherLum`, `myLum`, `sampleX`, and `x` symbols.
It still requires the sole direct discarded post-increment and the existing
counted-loop proof.  Validator and emitter discard/recompute the supplied
counter evidence separately and require equality.

The added tamper regression covers the original predicate truncation, outer
operator replacement, inclusive tie comparison, and loop-body reordering at
**both** validator and emitter boundaries.  The four focused test methods
completed successfully.

## Fresh verification evidence

- `python3 -m unittest discover -s tests -p 'test_*.py' -q`: exit 0.
- Focused counter-proof suite: 4/4 passed, including normal lowering,
  source/frozen-proof tampering, the four forged-control-tree variants, and
  adjacent body mutations.
- The independently rerun original forged-predicate reproduction was rejected
  by both boundaries as shown above.
- `python3 tools/glslcpp/generate_typed_slice.py --check`: `typed slice ok
  (108 programs)`.
- `node docs/port-engineering/task-16-oracle-generator.mjs --check`:
  `ok task-16-oracles.json`.
- Current `./build/noisemaker-cpu-tests`: **98 PASS**, including Task 16
  external formula/flat-tie oracle checks and the exact width-one quiet-NaN
  assertion.
- The generated C++ is byte-identical to the pre-fix Task 16 artifact:
  `src/typed_generated/typed_slice.cpp` SHA-256
  `d609c3df83ebe23a5148dfb3b3ad94129862b8705da5c1709f22a8f518885527`.
  The emitted `computeRank` still has one automatic `std::int32_t`
  `brighterCount`, a fixed 32-trip loop, native `continue`, exact strict/tie
  predicate, `++brighterCount;`, float rank conversion, and the authored
  width-one `float(x) / float(width - 1)` path.

## Artifact integrity

- Frozen brief:
  `3e803c0b7748a79b19ec58784f4fd2085ad1f0375e93c3f04971b96f31bcbcbf`.
- Proof-design review:
  `c542998fe640321670117b8c6494f5de11d1adcf19b4ab74788b3e496cf5b8ed`.
- Updated implementation report:
  `c983cf78624f1ba5b7567a03b4675e570d3ce560378421540b292bedc81fc20d`.
- Frozen oracle JSON:
  `878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`.
- Frozen oracle generator:
  `bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`.
- Corrected proof builder:
  `e051ca93ec5b84a874ba8591a4b153f8f1c96eb51d64d41e2de847aee1b8b787`.
- Updated typed proof record:
  `4ae5c9740083c2b46a1a6842c7476557ab95f64a6ab7236721791849b612d16b`.
- Counter-proof test suite:
  `2ca00c72517da88bd660ae7d18813e23d7cad1ac9fb686e52a38f796a59ca5d5`.

The resulting accounting remains 108 typed programs, 110 public catalog
entries, and 102 of 212 pinned corpus programs unported.  `computeRank`
continues to expose exactly the `lumTex` sampler binding with no pass uniforms,
and `gatherSorted` remains excluded.

## Scope

This was read-only for the repository.  No repository file, build artifact,
or Git state was changed; this `/tmp` review document is the only artifact
written during the re-review.
