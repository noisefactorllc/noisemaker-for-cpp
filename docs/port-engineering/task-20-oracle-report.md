# Task 20 frozen external oracle report

The Task 20 direct canonical oracle contract is frozen for exactly
`synth/sacredGeometry:sacredGeometry` and the proposed
`fixed-affine-centers13-v1` profile. No repository file was changed and no Git
command was used.

The generator binds the pinned `canonicalFactory273` directly through
`canonicalKernelFactories` + `bindCanonicalKernel` + `runPass` + `Surface`.
It does not reimplement center initialization, geometry functions, animation,
or output mixing. Every canonical case renders twice into fresh destinations
and must have identical F32 and RGBA8 bytes before it is frozen.

Artifacts:

- `task-20-oracle-generator.mjs` — SHA-256
  `4e9bead18c312cbf0aa5b3239bb575cfaec3ddd40cb246f3d47e8f3ccd49f75e`
- `task-20-oracles.json` — SHA-256
  `1f71fc6fb2f91f0c3b660decda30d533ecca20070bb318cc9757242be3499d03`

`node docs/port-engineering/task-20-oracle-generator.mjs --check`
passes and prints `ok task-20-oracles.json`.

## Frozen provenance and fixture

The JSON locks:

- corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`;
- raw source SHA-256
  `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de`;
- normalized source SHA-256
  `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3`;
- canonical generated-file SHA-256
  `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`;
- exact factory-text SHA-256
  `b4ed8af983d8bda5d48e05d418458c2fc82170f745b021199df7f7095fadb2f2`;
- empty runtime define map, the exact 17-uniform binding order, source output
  `fragColor:vec4@18`, no samplers, and metadata route `color -> outputTex`.

The non-square output is 37x23, stored top-down. `runPass` retains its GLSL
bottom-left fragment coordinates. Render context is:

```text
resolution       [37,23]       [0x42140000,0x41b80000]
tileOffset       [5,7]         [0x40a00000,0x40e00000]
fullResolution   [53,41]       [0x42540000,0x42240000]
aspect           37/23 f32     1.60869562625885 / 0x3fcde9bd
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
| `geometry-0-flower-default-control` | `f21a1640b99f9261e057803162a58a10421ef8215e986ac32a5db139772e5fc7` | `5924cef44fee78454a1b0de3ad2d6ee3f6e58a5781d33d6ada23a0f3ebd94695` | 523/195/133 | 0 |
| `geometry-1-fruit-animation-off` | `53a248d64b3e0ddd6ec1e3b0cb464f0a34a7537b195b6101ae491ed5237527bd` | `65c56e8163f4771fa4b84f9491683b268f3f690244da038aa159017491446418` | 622/120/109 | 0 |
| `geometry-3-metatron-animation-off` | `a59f25d73a50ea89aaecef886f6716d0160e1daff66e2c2d0d903db4b78a9768` | `1bcedeeb940061ff65ecd623ed9403bc7cb527f0aeb0aa109280d94377365b56` | 125/252/474 | 0 |
| `geometry-1-fruit-ripple` | `4860d797929366c4653b781be06b0e1ff71e50536bb8ed520451d36696353b97` | `6008029ea08dd02986f54f779201b757973456d8fe110b60c279e8f25ab2ceaf` | 500/192/159 | 0 |
| `geometry-3-metatron-unfold` | `b230927f646ca19eec5da4afd377b834bcfba868f6ee4ac2c4c9cd2ca704b6d9` | `a8a85901eb46162d910c494f18d1d55ddd6f6c137fc01184e4502d8e6e6e00bf` | 139/0/712 | 0 |
| `geometry-4-seed-rotate` | `aefe8af6e96a502a31f955c69d048fb0b3ea6509fcb7cbc812fe3a858c17057a` | `fb99a8983f2d2d8e7068a63741090d35687a42fac360e67c3e76398a311ff4cc` | 124/443/284 | 0 |
| `geometry-5-vesica-pulse` | `0c64d5b84edde6e6c8ef3fb5a69a96c188cd0aa9a4061e27ace4d346d155ef11` | `3eec9bdd7df95c1027b106df8cddf374f7301379d8c19f1c0093d13873fa96cb` | 845/0/6 | 0 |
| `geometry-6-borromean-ripple` | `0927349a467756276ad2818fad4726061093fbeada54bb67b5441c184948d368` | `0b04d4b45240d9359b1aa049e791321be93f0512c42858d33f4d8460b2d87599` | 588/143/120 | 0 |
| `geometry-7-star-animation-off` | `2582e12629310c9fbd4781a158fd7f77512709b7b081bfb5ca00f38efde57879` | `0ca995365b120c89a3dbf0f3def90f25c768c1f6af5556f57d15ef2fda197ebe` | 0/0/851 | 2,553 |
| `geometry-8-triquetra-rotate` | `6b3b4a906ffa5238c87f3516f92c26f61d8a4e4b51ae0b33db8535ea2946eeaf` | `dad1ab989e22377d728fee5d982a9f1f9186580e5e4227f6c313db218ce52905` | 805/22/24 | 0 |

This covers every metadata geometry choice and every animation code across the
matrix. The four array-path cases distinguish animation-off circles,
Metatron's complete graph, distance-sensitive Ripple, and distance/line
visibility-sensitive Unfold.

## Affine-array mutation adequacy

Mutants are built by counted, exact replacements in a copy of the pinned
factory text. They never replace the reference factory. Each mutant is also
rendered through every non-array geometry case, and all six non-array controls
must remain byte-identical. The JSON records mutated hashes, byte/lane counts,
maximum finite difference, nonfinite transitions, and exact replacement text.

| Mutation | Required detecting cases | Observed F32 lane differences |
| --- | --- | --- |
| center `[0,0] -> [0.375,-0.25]` | Fruit off; Metatron off | 567; 863 |
| inner store `1+k -> 2+k` | Metatron off; Fruit Ripple | 2,553; 84 |
| outer store `7+k -> 6+k` | Metatron off; Fruit Ripple | 2,553; 84 |
| distance read `centers[i] -> centers[0]` | Fruit Ripple; Metatron Unfold | 955; 117 |
| circle-position read `centers[i] -> centers[0]` | Fruit off; Metatron off | 330; 210 |
| line endpoint `centers[j] -> centers[12]` | Metatron off; Metatron Unfold | 1,431; 1,755 |
| inner-ring index permutation | Metatron off; Metatron Unfold | 82; 110 |

The `1+k -> 2+k` and `7+k -> 6+k` mutants deliberately create one duplicate
center and one zero-filled missing center. Fruit animation-off is identical at
this resolution because the lost outline is covered by the symmetric union;
Fruit Ripple distinguishes both with 84 changed F32 lanes. Metatron detects
both strongly: the duplicate centers introduce a degenerate pair and canonical
NaN propagation, changing all 2,553 RGB lanes. The proof cannot rely only on
that NaN amplification, so the finite Fruit Ripple result is also mandatory.

The index-permutation stress keeps the exact six inner vectors but rotates
their array identities. Fruit off and Fruit Ripple remain byte-identical, as
expected for a set of circles. Metatron changes only 82/110 F32 lanes and zero
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
F32    0c8a428114ff71c11358e12f90578b72ddb686609a0165caae15b758d5793a54
RGBA8  32a173d00b4f39b2716bf4ea8deb6f8717e8722bf1cec3f43204c74bb50ea988
```

It produces 141 non-background pixels (74 exact foreground, 67 mixed), while
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
