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

- Corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; source `3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9`; CPU import closure is confined to the immutable snapshot.
- The complete 22-file CPU import closure is frozen by path and SHA-256; any modified, missing, or extra dependency fails closed.
- Live/foreign imports, adapter routing, absolute-looking provenance strings, schema drift, and sidecar drift fail closed.

## TDD evidence

- RED: `pytest -q tests/test_kaleido_oracle.py` failed before package files existed (2 failures: missing generator and missing check path).
- GREEN: the same test is run after generation, followed by generator `--check` and materializer `--self-test`/`--check`.

- Verification hygiene: after the initial RED probe left repo-local pytest/bytecode residue, Python bytecode, pytest cache, temporary files, and regeneration cache were redirected under worker temp roots; the exact residue is left for controller cleanup while workers quiesce.

## Files and hashes

- Oracle JSON SHA-256: `c5ec36429d5dc64ab9f058277ec763e2badb5fd3828aa351fb9342e9d8b109a5` (sidecar is authoritative for the exact bytes).
- kaleido187_oracle_generator.mjs: 39006 bytes, SHA-256 `f3d07209a319154ee0a3077eec79ca32b9e57013a8f06082d0b0266a94229b24`
- kaleido187-oracles.json: 46493 bytes, SHA-256 `c5ec36429d5dc64ab9f058277ec763e2badb5fd3828aa351fb9342e9d8b109a5`
- generate_kaleido_native_oracle_include.py: 50312 bytes, SHA-256 `aaa2a4d8d4a7be740645212f5527518c3ae46f23d0503605c084453dc81e6d7b`
- kaleido187_expected.inc: 17892 bytes, SHA-256 `3bacea2893d622e894cf66b52c2974757a8667546b7a081ba536ef2f325fb304`
- Generator, report, native materializer, include, and each sidecar are generated/checked as one package.

## Concerns

- The nonzero KERNEL probe exercises an authority path outside the frozen corpus define only to prove that the channel is closed at KERNEL=0.
- ABI evidence is a complete native-consumable preflight table: every required binding has one concrete missing case and one wrong native variant/value, all pending shared native integration.

