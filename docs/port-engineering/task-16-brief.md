# Task 16 — bounded discarded local-counter statement v1

## Baseline and scope

Build on the independently approved Task 15 tree: 107 typed factories, 109
public factories, and 103 of the 212 pinned corpus programs still publicly
unported. Add exactly one typed/public factory:

```text
filter/pixelSort:computeRank
```

The resulting counts must be exactly 108 typed, 110 public, and 102 unported.
The source is pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, path
`sources/filter/pixelSort/computeRank.glsl`, raw SHA-256
`6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4`,
and authoritative define map `{}`.

This task adds only a proof-attached, value-discarded local integer postfix
statement. It does not add arrays, indexing, generic postfix/prefix
expressions, new parameter directions, resource-derived loop bounds, a
render-graph adapter, or the complete pixel-sort workflow. The other five
pixel-sort factories remain independently ported or unported exactly as their
catalog entries state.

## Exact admitted statement and proof

The only new source form is line 35's standalone `brighterCount++` inside the
existing proved loop and conditional. Retain a frozen proof on the containing
typed statement with at least:

- stable target symbol ID and exact signed-int local type;
- exact zero initializer identity and location;
- exact update expression and discarded-value statement identity;
- containing loop induction/proof identity;
- one maximum update per loop visit;
- lower/upper interval `0..32`;
- proof kind identifying this narrow local-counter contract.

The proof must establish that `brighterCount` is a fresh writable local, its
only post-initialization write is this statement, the statement is reached at
most once per visit of the exact 32-trip `s=0..<NUM_SAMPLES` loop, and the
counter cannot escape, alias, index storage, or affect another loop bound.
The existing `continue` may only reduce executions. The postfix value is
discarded, so the emitter may lower it to `++brighterCount;`.

Construct the proof from typed IR and stable symbols, not source text. The
capability validator must recompute it; the typed C++ emitter must recompute
it independently and reject absent, stale, forged, or mismatched evidence.
Admission is additionally locked to this exact key, source digest, define
map, function, statement, and control shape. Do not add `post` to the generic
expression emitter.

Reject body `++x`, `x--`, `x += 1`, another target, expression-valued postfix,
postfix in a call or arithmetic expression, postfix outside the proved
conditional/loop, nonzero or dynamic initialization, a second write or
update, a changed bound or multiplicity, an overflowed interval, and operands
that are float, uint, const, parameter, uniform, global, induction variable,
member, swizzle, or index. Reject the same malformed frozen records at both
validator and emitter boundaries.

## Existing semantics that must remain exact

Preserve the authored 32-sample loop, native `continue`, level-zero integer
`texelFetch`, signed integer `sampleX = (s * width) / NUM_SAMPLES`, strict
greater-than followed by `otherLum == myLum && sampleX < x`, and explicit
float conversion for normalized rank. The source writes blue as
`float(x) / float(width - 1)`; at width one this is canonical `0/0` and must
produce quiet NaN, not a clamp, early return, or rewritten denominator.

Canonical JavaScript Surface inputs are positive integral dimensions with at
most 16,777,216 pixels. Task 16 verification stays within that domain, which
also keeps `31 * width` inside signed int32. This task does not broaden the
repository by changing the shared Surface ABI or limits.

Pixel execution remains `noexcept` and allocation-free. The new state is one
automatic `std::int32_t`; no heap allocation, per-pixel map/string/variant,
callback, virtual dispatch, static/shared mutable state, or resource ABI
change is permitted.

## Binding and public boundary

The exact generated state/binder signature is one sampler:

```text
lumTex:sampler2D@1/S1
```

There are no pass uniforms. Missing `lumTex` and a wrong-kind substitute must
fail at bind time. Unrelated extra bindings remain ignored by the shared
name-keyed binding API and must not create state fields or affect output.

The public catalog must add only `filter/pixelSort:computeRank`. Do not claim
the complete six-pass effect is executable as a graph.

## Frozen external oracle contract

Freeze exactly the artifact produced by
`docs/port-engineering/task-16-oracle-generator.mjs` at
`docs/port-engineering/task-16-oracles.json`. Its `--check` mode must
verify the existing canonical JSON byte contract without writing. Provenance
must include the pinned source hash, canonical-kernels SHA-256
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`,
Node version, and the exact canonical APIs used.

The frozen generator SHA-256 is
`bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`;
the frozen JSON SHA-256 is
`878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`.

The three variants are:

1. `formula`: 9x7 output and top-down 11x9 F32 `lumTex`, with R
   `((17x+31y+13)%101)/100`, G `((7x+19y+23)%97)/96`, B
   `((29x+11y+5)%89)/88`, and A `.35+((3x+5y+1)%13)/20`. Expected F32 hash
   `b232b1b98b9d973eed9b21ffabfe2039974f4e431269fe05d1ed9741b0e06bf3`
   and RGBA8 hash
   `f9021ce571b2f8234509a7df8f9ec2379cb91db4aa56c42dab39f3a0657cfce6`.
2. `flat-tie`: 9x7 output and 11x9 `lumTex` filled with exact
   `[.5,.25,.75,1]`. Expected F32 hash
   `37826c52ed556af08540665ec5435fd99188af1aeb525900647b710f0ecf800f`
   and RGBA8 hash
   `472adcee73849262e3cc7ce4a7bcfdfbb2e4191f7c51e6d49ab4e02404e8d753`.
3. `width-one`: 1x1 output and 1x1 `lumTex` containing the same exact flat
   texel. Expected F32 hash
   `24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c`,
   RGBA8 hash
   `1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e`,
   and exact lane bits `00000000 3f000000 7fc00000 3f800000`.

For the finite 9x7 variants, require exact little-endian Float32 hash, exact
RGBA8 hash, probes at `(0,0)`, `(4,3)`, `(8,6)`, and immediate repeat bytes.
Record top-down storage and bottom-left fragment coordinates explicitly. For
width one, also assert native `std::isnan(blue)`, exact canonical NaN payload,
RGBA8 NaN-to-zero conversion, and repeat bytes.

## Verification and stop boundary

Add parser/semantic/proof-tamper/emitter negatives for every adjacent form,
generated-source assertions for exactly one `++brighterCount;`, exact binder
and catalog/count tests, and the three external oracle cases. Preserve all
prior oracle suites and immutable two-factory hashes.

Run the complete Python suite, corpus/semantic/generated drift gates, oracle
`--check`, and fresh strict Debug and Release builds/tests with
`-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`. Stop for independent
review before any later array/index task.
