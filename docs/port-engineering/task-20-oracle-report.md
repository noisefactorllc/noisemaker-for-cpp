# Task 20 frozen external oracle report

The Task 20 direct canonical oracle contract is frozen for exactly
`synth/sacredGeometry:sacredGeometry` and the proposed
`fixed-affine-centers13-v1` profile.

The generator binds the pinned `canonicalFactory283` directly through
`canonicalKernelFactories` + `bindCanonicalKernel` + `runPass` + `Surface`.
It does not reimplement center initialization, geometry functions, animation,
or output mixing. Every canonical case renders twice into fresh destinations
and must have identical F32 and RGBA8 bytes before it is frozen.

Artifacts:

- `task-20-oracle-generator.mjs` — SHA-256
  `77ed9b8e0ac61ef45c27a4bdb14a5cfbd1f58c2577f23c81934672af20f442b0`
- `task-20-oracles.json` — SHA-256
  `e7371f587324a899428d62d23eb933cfd1d08a19df80584ab85e5197658be0c4`

With `CPU_ROOT` and `CPU_LEDGER` set to the authenticated CPU root and matching
ledger, `node docs/port-engineering/task-20-oracle-generator.mjs --cpu-root "$CPU_ROOT" --ledger "$CPU_LEDGER" --check`
passes and prints `ok task-20-oracles.json`.

## Frozen provenance and fixture

The JSON locks:

- corpus revision `a1a3fa2a84223dfc1f5ec2c7a54a6f4269139c15`;
- raw source SHA-256
  `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de`;
- normalized source SHA-256
  `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3`;
- canonical generated-file SHA-256
  `80b2e701426a5003d9ef44dce09de1f601f4c8cd1e4bff1f0c4d2b607e95e91c`;
- exact factory-text SHA-256
  `48de593c3096b18f8ca98518fac3f1055cdc3746883860273b5b1d82e374ef37`;
- empty runtime define map, the exact 17-uniform binding order, source output
  `fragColor:vec4@18`, no samplers, and metadata route `color -> outputTex`.

The non-square output is 37x23, stored top-down. `runPass` retains its GLSL
bottom-left fragment coordinates. Render context is:

```text
resolution       [37,23]       [0x42140000,0x41b80000]
tileOffset       [5,7]         [0x40a00000,0x40e00000]
fullResolution   [53,41]       [0x42540000,0x42240000]
aspect           53/41 f32     1.2926828861236572 / 0x3fa576a2
frame            11
deltaTime        0.01666666753590107 / 0x3c888889
seed             23 / 0x41b80000
ordinary time    0.3375000059604645 / 0x3eaccccd
unfold time      0.4124999940395355 / 0x3ed33333
```

The main nondefault control profile uses `scale=18.25f`,
`rotation=17.375f`, `thickness=0.34f`, `smoothness=0.0275f`, `rings=4`,
`starPoints=7`, `speed=2.75f`, and `pulseDepth=0.31f`. Foreground is
`[0.92f,0.67f,0.21f]`; background is `[0.07f,0.16f,0.31f]`. Exact values and
F32 words are stored per case. The default Flower control instead freezes the
source metadata defaults. Star Polygon uses `scale=10.75f` so the finite
integer-remainder comparison is visibly sampled rather than all background.

Nine fixed top-down probes are stored for every case at `(0,0)`, `(10,9)`,
`(16,11)`, `(18,11)`, `(20,15)`, `(28,5)`, `(32,9)`, `(35,21)`, and `(36,22)`.
Each probe contains numeric values (or explicit `NaN`) and little-endian F32
words.

## Frozen canonical cases

The `background/foreground/mixed` column is an exact F32 pixel count. All
ordinary cases have 851 opaque pixels and finite lanes. The Star row is the
canonical exception described below: all 2,553 RGB lanes are qNaN and all 851
alpha lanes are exactly 1.

| Case | F32 SHA-256 | RGBA8 SHA-256 | background/foreground/mixed | nonfinite RGB lanes |
| --- | --- | --- | ---: | ---: |
| `geometry-0-flower-default-control` | `fc5265d3605f4fea4fdcda273bdd06e683cb9786673f1dba7f3294c6e084c0b8` | `839c10ec3273b8bc4fc9c3245b49fc513803e1fe58c4c3bd89e70f6464a8fb11` | 433/249/169 | 0 |
| `geometry-1-fruit-animation-off` | `f11ad8eb98bce19933227fb38ab0c4888df7ea876a38f911f508db88a6089a62` | `52a90288985c5e7cb3c455b58ffb64b6c365335aecc7200d8f8bfe5bbb9f6b6e` | 616/132/103 | 0 |
| `geometry-3-metatron-animation-off` | `7b29aafc75000b7da82a15ad30b77e1046340451ec9ad8be93c69db397dcd36c` | `116f61afd10ccf1dba02786e751ea58399b278a66766ca242b2f6b63aefc9dee` | 120/290/441 | 0 |
| `geometry-1-fruit-ripple` | `0530845ee4f2637154a532cd32668da5cf9560ecd6e7396c24fba2a2f975d970` | `3c8fd01ab01d1a258ca14115f9816810d4d3ebd35e08c4fa4dba2880f90fb3b0` | 460/223/168 | 0 |
| `geometry-3-metatron-unfold` | `7684e6eb202d4ad871d475f4634fae90208090eeb88475c8fce32f89a65c6fed` | `9411d0e41a6081c706b5ad6f7e0cfdfc33dc306f51416fdbe2b6203b84c244da` | 134/0/717 | 0 |
| `geometry-4-seed-rotate` | `9e34c924e1f3877083934d62aac1d722e53cd979307641d0b63f858cb10c0497` | `8d3e2cd198ebe8257530c38512354b19116ca879fa27eceeea1665cc24970a71` | 74/489/288 | 0 |
| `geometry-5-vesica-pulse` | `32992d8b303d92fefb2d5e7383bde606e53d6dec07a0fa12b4ca49c2f0659b83` | `683413061c05ef1c86080fb336366ccf444ffcc36af68492b5a355a222d8b381` | 851/0/0 | 0 |
| `geometry-5-vesica-pulse-visible-scale-16` | `b7f5cda337223fc06bd2f6e95d50266fdb4b41565b6bab3dfa574652592c0cba` | `29a84ec3bfb586b33ed25b67a3306468bbaac9b25f0725fc40504688847352f7` | 696/73/82 | 0 |
| `geometry-6-borromean-ripple` | `5fc17595d0d0a1f82a2792e73486691370a8b0ca8402f61c8c14dadbacf41961` | `2e10fb5660e04c7523c7bf29df18c0d39dd9e9e3be8ea925db194ab2978832c5` | 542/174/135 | 0 |
| `geometry-7-star-animation-off` | `2582e12629310c9fbd4781a158fd7f77512709b7b081bfb5ca00f38efde57879` | `0ca995365b120c89a3dbf0f3def90f25c768c1f6af5556f57d15ef2fda197ebe` | 0/0/851 | 2,553 |
| `geometry-8-triquetra-rotate` | `10c62c72cc22fdbffd860bd02913473826c46b8d4be9d216fa7ceb38d7219c0a` | `290bff21210403c0b559f347a081b0e58e88d1e904dee1f85d528248f1fc3f1f` | 848/0/3 | 0 |

This covers every metadata geometry choice and every animation code across the
matrix. The original Vesica case is exact background; the scale-16 witness
has foreground and mixed pixels. The four array-path cases distinguish animation-off circles,
Metatron's complete graph, distance-sensitive Ripple, and distance/line
visibility-sensitive Unfold.

## Affine-array mutation adequacy

Mutants are built by counted, exact replacements in a copy of the pinned
factory text. They never replace the reference factory. Each mutant is also
rendered through every non-array geometry case, and all seven non-array controls
must remain byte-identical. The JSON records mutated hashes, byte/lane counts,
maximum finite difference, nonfinite transitions, and exact replacement text.

| Mutation | Required detecting cases | Observed F32 lane differences |
| --- | --- | --- |
| center `[0,0] -> [0.375,-0.25]` | Fruit off; Metatron off | 570; 914 |
| inner store `1+k -> 2+k` | Metatron off; Fruit Ripple | 2,553; 111 |
| outer store `7+k -> 6+k` | Metatron off; Fruit Ripple | 2,553; 111 |
| distance read `centers[i] -> centers[0]` | Fruit Ripple; Metatron Unfold | 837; 111 |
| circle-position read `centers[i] -> centers[0]` | Fruit off; Metatron off | 264; 177 |
| line endpoint `centers[j] -> centers[12]` | Metatron off; Metatron Unfold | 1,431; 1,776 |
| inner-ring index permutation | Metatron off; Metatron Unfold | 89; 116 |

The `1+k -> 2+k` and `7+k -> 6+k` mutants deliberately create one duplicate
center and one zero-filled missing center. Fruit animation-off is identical at
this resolution because the lost outline is covered by the symmetric union;
Fruit Ripple distinguishes both with 111 changed F32 lanes. Metatron detects
both strongly: the duplicate centers introduce a degenerate pair and canonical
NaN propagation, changing all 2,553 RGB lanes. The proof cannot rely only on
that NaN amplification, so the finite Fruit Ripple result is also mandatory.

The index-permutation stress keeps the exact six inner vectors but rotates
their array identities. Fruit off and Fruit Ripple remain byte-identical, as
expected for a set of circles. Metatron changes only 89/116 F32 lanes and zero
RGBA8 bytes because endpoint orientation and F32 evaluation order expose tiny
differences. This is direct evidence that RGBA8 is inadequate and that runtime
oracles cannot prove exact affine index spelling or initializer order. The
source/typed structural proof remains mandatory.

Together the finite mutations establish that the fixture observes center 0,
both affine rings, both `centers[i]` circle roles, and the `centers[j]` nested
line role wherever symmetry allows. The complete/disjoint-write and exact
source-shape claims still come from the Task 20 structural proof, not pixels.

## Newly discovered whole-program compatibility blocker

The branch matrix invalidates the earlier audit statement that no non-array
compatibility transform is needed.

At raw source line 276 / normalized line 260, `starPolygonMask` declares:

```glsl
int j = (i + 2) - ((i + 2) / n) * n;
```

The intended GLSL integer division computes `(i+2) % n`. Current typed C++
will likewise use truncating `std::int32_t` division. The pinned canonical
factory instead emits:

```js
var j = (i + 2) - ((i + 2) / n) * n;
```

JavaScript performs Number division and does not truncate. On the first loop
iteration, `2 - (2/n)*n` is positive zero for every metadata `starPoints`
choice 5 through 12. Thus `a == b`, `dot(ba,ba) == 0`, the segment projection
contains `0/0`, and qNaN propagates through the SDF, outline, `m`, clamp, and
color mix. Direct canonical output for all 851 pixels is:

```text
R/G/B = qNaN, little-endian F32 word 0x7fc00000
A     = 1.0,  little-endian F32 word 0x3f800000
RGBA8 = [0,0,0,255]
```

The JSON verifies that same canonical F32/RGBA8 hash for every
`starPoints=5..12`. It also constructs an audit-only intended-integer control
by replacing the one factory expression with `(i+2) % n`. For `starPoints=7`
the finite control hashes are:

```text
F32    155585055be5f51240ef2b5e2cd6c62cbd1e21ba1465502052e04b3ca842ff18
RGBA8  ba1edb9f2de0b7d4af5bd22d566dceced832bdf7a4a229f7af2acbb1bb287046
```

It produces 172 non-background pixels (88 exact foreground, 84 mixed), while
all 2,553 RGB lanes differ from the canonical qNaN output. Separate finite
control hashes and metrics for all eight metadata `starPoints` values are
frozen in the JSON.

Therefore Task 20 is not sound as an array-only addition. Before publishing
the whole factory, it must either:

1. add an exact key/source/function/span-bound transform that preserves the
   canonical Number-division behavior for this one `j@107` declaration and
   prove the resulting qNaN path against the frozen Star matrix; or
2. leave `synth/sacredGeometry:sacredGeometry` unported.

The transform must not change integer division globally. A broad change would
corrupt normal GLSL integer semantics in unrelated programs. A direct
geometry-7 qNaN shortcut is also too weak unless its equivalence is proved for
the entire accepted binding domain; the source-site Number-division transform
is the closer canonical model. Sanitizer/release runs must explicitly allow
the proved floating `0/0` while still rejecting memory or integer undefined
behavior.

## Acceptance consequence

The affine `vec2[13]` fixture is adequate: all required center and read roles
have finite, direct-canonical sensitivity, repeat identity, exact F32 hashes,
and top-down probes. However, the complete public key cannot pass bitwise
whole-program parity until the Star Polygon Number-division mismatch is
handled. The correct Task 20 gate is therefore:

```text
fixed-affine-centers13-v1
+ exact starPolygonMask Number-division compatibility transform
+ all frozen canonical cases and mutation checks
```

An array-only implementation that renders finite Star Polygon geometry would
be more mathematically sensible but would not match the pinned canonical
runtime and must fail the Task 20 external oracle.
