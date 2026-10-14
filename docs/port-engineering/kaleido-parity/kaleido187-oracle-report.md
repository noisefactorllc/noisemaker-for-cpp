# Kaleido187 exact-parity oracle

This package authenticates `classicNoisedeck/kaleido:kaleido` against the unmodified public `canonicalFactory9` in an immutable CPU snapshot.

## Decisions

- Frozen defines: DIRECTION=2, KERNEL=0, LOOP_OFFSET=10, METRIC=0; factory text SHA-256 is `4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3`.
- The authenticated native expected-rejection table derives the pinned GLSL uniform declarations and canonical createCanonicalBindings return surface. Each row is pending shared native integration; no canonical JavaScript rejection is claimed.
- The five mutable float[9] tables are plain JavaScript arrays and write-only at the accepted defines. Their pixel mutation is explicitly an invariant control, not structural-carrier evidence.
- No tile/crop identity is claimed. All stored expected values are raw float32 words plus independently captured RGBA8 bytes with zero tolerance.

## Cases and controls

- 4 full-route cases cover kaleido sides, wrap arms, time, speed, loopScale, seed, and distinct dyadic input gradients.
- Repeatability, input immutability, independent output storage, public/direct factory identity, and KERNEL omitted-vs-zero identity are measured.
- KERNEL nonzero with effectWidth changed 60 float32 lanes; this is a liveness probe, not a frozen parity case.
- Mutants are recorded per case. XOR sites and table values are runtime-dead/write-only controls at the frozen define.

## Provenance locks

- Corpus revision `0ed489ec46842bffba33ee2ec65a218b6dda51f5`; source `18a201e5189430578a2cd1d03cea911957a08f3bd7f3e74e78b97eb9f946ed52`; CPU import closure is confined to the immutable snapshot.
- The complete 23-file CPU import closure is frozen by path and SHA-256; any modified, missing, or extra dependency fails closed.
- Live/foreign imports, adapter routing, absolute-looking provenance strings, schema drift, and sidecar drift fail closed.

## TDD evidence

- RED: `pytest -q tests/test_kaleido_oracle.py` failed before package files existed (2 failures: missing generator and missing check path).
- GREEN: the same test is run after generation, followed by generator `--check` and materializer `--self-test`/`--check`.

- Verification hygiene: after the initial RED probe left repo-local pytest/bytecode residue, Python bytecode, pytest cache, temporary files, and regeneration cache were redirected under worker temp roots; the exact residue is left for controller cleanup while workers quiesce.

## Files and hashes

- Oracle JSON SHA-256: `0085bccb32ba5d490c1a345ee2046aa489ea57dc1cbc61a4d6f230e84ee3065d` (sidecar is authoritative for the exact bytes).
- kaleido187_oracle_generator.mjs: 39443 bytes, SHA-256 `9bc1ef25409815451b1392e500625762a41b3f6cd9618e2c12fefbd403b220e3`
- kaleido187-oracles.json: 46926 bytes, SHA-256 `0085bccb32ba5d490c1a345ee2046aa489ea57dc1cbc61a4d6f230e84ee3065d`
- generate_kaleido_native_oracle_include.py: 50686 bytes, SHA-256 `ee517c6dc63ff6368bf76abb818c7453583666b3f4921b71563c20b3f6a265a5`
- kaleido187_expected.inc: 17892 bytes, SHA-256 `ee5483eaa8c0999d8e6a6417abe3c1353bae229260dec93ba6ca9c8170dff5a8`
- Generator, report, native materializer, include, and each sidecar are generated/checked as one package.

## Concerns

- The nonzero KERNEL probe exercises an authority path outside the frozen corpus define only to prove that the channel is closed at KERNEL=0.
- ABI evidence is a complete native-consumable preflight table: every required binding has one concrete missing case and one wrong native variant/value, all pending shared native integration.

