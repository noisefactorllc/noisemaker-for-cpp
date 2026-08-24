# Task 16 final acceptance review

## Decision

**NOT APPROVED — P1 found.**

The normal generated artifact, catalog wiring, native tests, and frozen oracle
fixtures are coherent.  However, the new `computeRank` admission rule does not
meet the brief's fail-closed requirement for a forged/stale typed IR: both the
validator and C++ emitter accept a semantically altered `if` predicate when the
original source text, source hash, spans, symbols, and recomputed proof fields
are retained.

## P1 — counter-proof admission is not locked to the exact required control predicate

**Affected boundaries:** `tools/glslcpp/generate_typed_slice.py` validation and
`tools/glslcpp/emit_typed_cpp.py` emission, through
`tools/glslcpp/frontend/local_counter_proof.py`.

The frozen brief requires admission to be locked to the exact key, source
digest, define map, function, statement, **and control shape**, and requires
both boundaries to reject stale, forged, or mismatched evidence.  The current
proof proves only a broad shape: an initialized integer local, a direct postfix
increment in a one-arm conditional, enclosed by one 32-trip loop.  It records
the conditional span but does not inspect or pin its predicate.  Validator and
emitter each recompute that same permissive proof and compare it to mutable
proof data; neither compares the typed control subtree to an immutable,
source-specific expected profile.

### Reproduction

1. Parse and semantically analyze the canonical
   `filter/pixelSort:computeRank` source.
2. Make an in-memory `dataclasses.replace` copy of only the `if` statement at
   source line 33, replacing its condition
   `otherLum > myLum || (otherLum == myLum && sampleX < x)` with its first,
   still-well-typed child, `otherLum > myLum`.
3. Preserve the `TypedProgram.source`, raw source hash, normalized source
   digest, statement spans, symbol IDs, loop, declaration, and increment.
4. Invoke `validate_capabilities(...,
   source_hash=COMPUTE_RANK_RAW_SHA256)` and then `render_typed_cpp(...)`.

Observed result:

```
VALIDATOR ACCEPTED forged altered conditional
EMITTER ACCEPTED forged altered conditional False
```

The trailing `False` is the result of checking whether emitted C++ still
contains `sampleX < x`; it does not.  Thus the forged program changes flat-tie
ordering behavior while passing the stated admission boundaries.  This is P1,
not P0, because the attack requires an invalidly modified internal typed IR;
nevertheless that is exactly the evidence-tampering case the Task 16 contract
explicitly says must fail closed.

### Required correction and regression

Pin an immutable, source-specific structural profile at both boundaries rather
than accepting any loop/conditional with matching generic proof metadata.  At
minimum, validate the exact enclosing predicate and stable symbols/operators:
the outer `||`, left `otherLum > myLum`, and right
`otherLum == myLum && sampleX < x`, together with the direct function-body and
loop/conditional hierarchy.  Compare supplied and reconstructed proof data to
that profile; spans alone are not sufficient because they can be preserved by a
forged tree.

Add the reproduction above as a regression: mutate only that typed conditional
while retaining original source bytes, digests, spans, symbol IDs, and proof
fields, and assert that **both** `validate_capabilities` and `render_typed_cpp`
reject it.  A complementary test should cover an increment relocated into a
different admissible-looking conditional/loop position.

## Verified positive evidence

All of the following were inspected without repository writes or Git:

- Frozen Task 16 brief SHA-256:
  `3e803c0b7748a79b19ec58784f4fd2085ad1f0375e93c3f04971b96f31bcbcbf`.
- Frozen proof-design review SHA-256:
  `c542998fe640321670117b8c6494f5de11d1adcf19b4ab74788b3e496cf5b8ed`.
- Task implementation report SHA-256:
  `db8884fb98ab12859c5e351b129211a49ec64383f08f54d8b8157fac50cfd4c0`.
- Oracle fixture SHA-256:
  `878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`;
  generator SHA-256:
  `bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`.
  `node docs/port-engineering/task-16-oracle-generator.mjs --check`
  returned `ok task-16-oracles.json`.
- `python3 tools/glslcpp/generate_typed_slice.py --check` returned
  `typed slice ok (108 programs)`.
- `python3 -m unittest tests.test_typed_generator -q` completed successfully.
- The current `./build/noisemaker-cpu-tests` run completed with **98 PASS**,
  including the external `computeRank` oracle cases and width-one quiet-NaN
  checks.
- The typed slice has 108 programs; the native catalog test asserts the
  required 110 public programs, which yields the required 102 unported keys
  from the 212-key canonical corpus.  It also exercises the exact `lumTex`
  sampler-only binding and rejects a uniform named `lumTex`.
- Normal generated `computeRank` code has the required local integer counter,
  fixed 32-trip loop, direct increment, rank calculation, float division for
  the blue coordinate, `noexcept`, and no allocations or virtual calls in the
  hot path.  Its width-one float blue value is the required quiet NaN before
  RGBA8 conversion maps NaN to zero.

## Review scope

This is an acceptance review of the frozen Task 16 artifacts and current
workspace implementation.  No source, test, generated, build, or repository
metadata files were changed; this report is the sole review artifact.
