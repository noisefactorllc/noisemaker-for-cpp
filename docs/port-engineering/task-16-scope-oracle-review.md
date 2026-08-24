# Task 16 scope and oracle review

Date: 2026-08-10  
Scope: read-only challenge of `task-16-implementation-risk-audit.md`; no repository file changed.

## Verdict: APPROVED WITH REQUIRED ORACLE CORRECTION

Conditional on the Task 15 counted-loop/`continue` baseline, the smallest
new language surface is indeed the single, value-discarded body statement
`brighterCount++` in `filter/pixelSort:computeRank`.  It does **not** require
arrays, dynamic indices, storage/alias rules, parameters, or a generic postfix
expression feature.  The proposed formula oracle is not valid, however, and
must be replaced before implementation or acceptance.  A width-one numerical
boundary is also absent from the proposal.

## Rechecked identity and public boundary

| Item | Verified value |
| --- | --- |
| Pinned revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key / pass | `filter/pixelSort:computeRank`, pass 3 `computeRank` |
| Source SHA-256 | `6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4` |
| Define map | exactly `{}` |
| Bindings | one sampler only: `lumTex:sampler2D@1/S1` |
| Metadata route | `lumTex <- luminance`, output `fragColor -> rank` |
| Pass uniforms | exactly `{}`; effect-level `alpha`, `angled`, `darkest`, and `wrap` do not bind this pass |
| Canonical kernels SHA-256 | `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |

The public catalog addition must expose this one factory only.  It must not
advertise the six-pass `filter/pixelSort` effect as ported: `prepare`,
`luminance`, `findBrightest`, `gatherSorted`, and `finalize` remain separate
programs and the later graph requires their surfaces.

## Why one bounded counter statement is sufficient

The exact source has:

- function-local `const int NUM_SAMPLES = 32` at line 25;
- function-local `int brighterCount = 0` at line 26;
- one body-level postfix at line 35, nested beneath the one 32-trip loop and
  the predicate at lines 33-34;
- no other write to `brighterCount`, no indexed operand, no escape, and no
  use of the postfix value;
- an existing `continue` at line 31.  Native C++ `for (...; ...; ++s)` keeps
  the required iteration increment after `continue`, so it can only reduce,
  not multiply, counter updates.

Thus the exact interval is `[0,32]`; `++brighterCount;` is observationally
equivalent to the discarded postfix statement.  The emitter must recognize
only a proof-attached expression statement with the stable local symbol ID,
not make `post` generally admissible.  It must reject prefix/decrement,
non-statement use, another operand/location/key, changed initialization,
another write, or a stale/forged proof at both validation and emission.

The source also needs no new precision rule: fetched R lanes are already F32
surface values, comparisons and scalar local arithmetic follow the existing
canonical-Number/double-temporary policy, and final `vec4` storage is F32.
Keep level-zero `texelFetch`, signed integer `(s * width) / 32`, and the exact
strict-then-equality tie predicate unchanged.

## Required safety and precision boundary

The proposed review omitted that the source writes blue as
`float(x) / float(width - 1)`, not `x / width`.  A valid `Surface` may have
width one.  In that case the canonical factory deliberately produces a quiet
NaN blue lane (`0 / 0`), while rank and luminance remain defined.  Do not add
a clamp, early return, or denominator rewrite: each would alter the oracle.

The canonical `Surface` domain is positive integral dimensions with at most
`16,777,216` pixels.  That bound also keeps `31 * width` within signed int32
for this loop.  C++ currently permits larger positive surfaces and emits
`texture_size` via a narrowing `size_t -> int32_t` cast.  Before Task 16 is
claimed safe beyond the canonical domain, either enforce the same runtime
dimension contract centrally or document the factory/run-pass precondition:
both sampler and destination dimensions are positive, each product is at most
16,777,216, and each dimension fits int32.  This is an existing runtime
boundary, not authorization to broaden Task 16 with an ad hoc feature-local
allocation or ABI change.

## Oracle review

The `flat-tie` candidate is confirmed by a fresh direct render using the
pinned `canonicalKernelFactories`, `bindCanonicalKernel`, `runPass`, and
`Surface` APIs.  It correctly tests the equality arm, `sampleX < x`, skips,
and positive counter values:

| Variant | F32 SHA-256 | RGBA8 SHA-256 | probes `(0,0)`, `(4,3)`, `(8,6)` |
| --- | --- | --- | --- |
| flat-tie, 9x7 output and 11x9 all-`[.5,.25,.75,1]` `lumTex` | `37826c52ed556af08540665ec5435fd99188af1aeb525900647b710f0ecf800f` | `472adcee73849262e3cc7ce4a7bcfdfbb2e4191f7c51e6d49ab4e02404e8d753` | `[0,.5,0,1]`; `[.375,.5,.4000000059604645,1]`; `[.75,.5,.800000011920929,1]` |

The stated formula construction in the input audit also was independently
rendered as written: 11x9 top-down F32 lanes `R=((17x+31y+13)%101)/100`,
`G=((7x+19y+23)%97)/96`, `B=((29x+11y+5)%89)/88`, and
`A=.35+((3x+5y+1)%13)/20`, with its listed 9x7 context.  It does **not** yield
the input audit's formula hash or endpoint probes.  Replace that row with:

| Variant | F32 SHA-256 | RGBA8 SHA-256 | probes `(0,0)`, `(4,3)`, `(8,6)` |
| --- | --- | --- | --- |
| formula, construction above | `b232b1b98b9d973eed9b21ffabfe2039974f4e431269fe05d1ed9741b0e06bf3` | `f9021ce571b2f8234509a7df8f9ec2379cb91db4aa56c42dab39f3a0657cfce6` | `[.28125,.75,0,1]`; `[.53125,.3400000035762787,.4000000059604645,1]`; `[0,.9399999976158142,.800000011920929,1]` |

The discrepancy is not a harmless rounding difference: it changes rank and
luminance at two probes.  The corrected formula plus flat-tie cover strict
greater-than, equality tie-breaking, skipped samples, zero rank, and positive
rank.  Require the frozen fixture to record top-down storage and the
bottom-left fragment convention explicitly; the differing endpoints make
that orientation observable.

Add this third, separate degenerate canonical oracle rather than silently
excluding width one:

| Variant | Fixture | F32 SHA-256 | RGBA8 SHA-256 | exact lane bits |
| --- | --- | --- | --- | --- |
| width-one | 1x1 output and 1x1 `lumTex=[.5,.25,.75,1]` | `24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c` | `1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e` | `0x00000000, 0x3f000000, 0x7fc00000, 0x3f800000` |

The native test should assert `std::isnan(blue)` and, where raw F32 hashing is
part of the frozen cross-runtime contract, the canonical `0x7fc00000` payload.
It should separately assert the RGBA8 conversion maps the NaN lane to zero.

## Exact implementation tests

1. Capability/IR negative matrix: all rejected postfix shapes and operands;
   source/key/digest/define/binding mismatches; stale or forged proof; second
   write; nonzero initialization; changed loop bound; and an expression-valued
   postfix must fail before C++ emission.
2. Generation assertion: emitted code for this key contains exactly a local
   `std::int32_t brighterCount = 0` and the proved `++brighterCount;`, while
   a generic post-expression remains rejected.  Keep `continue;` inside the
   native `for` and no heap/ABI change.
3. Binding negatives: absent `lumTex` and a wrong-kind replacement fail.  The
   shared `Bindings` object permits unrelated extras, so the precise factory
   assertion is instead that generated state reads only `lumTex` and no
   effect-level pixel-sort parameter; extras must neither become state fields
   nor affect output.
4. Differential release and debug tests: corrected formula, flat-tie, and
   width-one F32/RGBA8 hashes plus probes; double-render identity for all
   finite fixtures; width-one NaN/byte conversion checks; and a non-square
   sampler/output fixture to retain orientation and texture-size coverage.
5. Catalog checks: only this key is added, counts move by exactly one typed
   and one public entry from the accepted Task 15 baseline, and no whole
   pixel-sort workflow claim or generated factory for the five sibling passes
   is introduced.
