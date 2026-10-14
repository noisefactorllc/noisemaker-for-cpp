# Derivative cluster (15 programs) oracle report

Hermetic JS oracle for the 15 GLSL programs blocked on dFdx/dFdy/fwidth that are about to be ported from noisemaker-for-cpu to noisemaker-for-cpp. Ground truth for bit-exact C++ parity tests.

Total cases: **57** (45 closure-exercising + 12 antialias-off diagnostic). Antialias-ON cases: **36**.

## Define-as-binding note

halftone (MODE, PATTERN), pondRipples (STYLE, WRAP), and stipple (MODE) pin compile-time GLSL #defines that the JS reference reads as ordinary $bindings[...] lookups (no preprocessor in JS) -- every case for these three programs supplies the define at its generate_typed_slice._defaults()-authorized value via `uniforms`, verified live against the real _defaults() output (see report) and against the factory text actually containing the $bindings["<NAME>"] read (loadProgram()). Omitting these would silently select the wrong runtime branch, not fail loudly.

## Per-program summary

| Program | Family | Ordinals (active) | Has antialias | Cases | Diagnostic | Sign-flip divergent/reaching | Sign-flip expected-zero | Lane-transpose divergent/reaching |
| --- | --- | ---: | --- | ---: | ---: | --- | --- | --- |
| bulge | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| celShadingColor | fwidth | 1 | true | 4 | 1 | 0/3 | true | 3/3 |
| halftone | fwidth | 4 | false | 3 | 0 | 0/3 | true | 3/3 |
| lens | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| lensWarp | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| octaveWarp | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| pinch | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| polar | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| pondRipples | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| spiral | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| stThreshold | fwidth | 1 | false | 3 | 0 | 0/3 | true | 3/3 |
| step | fwidth | 1 | true | 4 | 1 | 0/3 | true | 3/3 |
| stipple | fwidth | 1 | false | 3 | 0 | 0/3 | true | 3/3 |
| tunnel | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |
| warp | dFdxDFdy | 2 | true | 4 | 1 | 3/3 | false | 3/3 |

## `filter/bulge:bulge` (bulge)

Source: `bulge/bulge.glsl` (2352 bytes, `87f26ffa13ffe946d94d92a00bd45ca3a9787b9ee402dfe04ebc3d4a911eb170`). Canonical factory `canonicalFactory25` (`0915a49efe3abce961e815de418a0e21aa7a200088b7e77902f1d92e59b5a83f`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| strong-bulge-repeat-rotated | 6x5 | false | true | 2 | `128d040fd0e496ae...` | `c7ad7100281f73c9...` |
| gentle-pinch-clamp | 5x6 | false | true | 2 | `2393936088839862...` | `65ec9ef562a2efb9...` |
| tiled-mirror | 7x4 | false | true | 2 | `b03c1eb2060106d7...` | `cf358a097aea8961...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `b714344bb0bfd6e0...` | `f65ecfab50311b87...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/celShading:celShadingColor` (celShadingColor)

Source: `celShading/celShadingColor.glsl` (2780 bytes, `90fa87484d3549bdaa2ddca4836a7ca8602ad4f1f30aa87a72841d4e013521f4`). Canonical factory `canonicalFactory27` (`0ff2c4c917b1dd0136c48788aa792e29f783a8e9be167bc50cd6390978b579c4`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| sharp-levels-warm-light | 6x5 | false | true | 1 | `23410eafb8a4eedd...` | `0bd57f2632857441...` |
| soft-levels-cool-light | 5x6 | false | true | 1 | `89b27cb65b628992...` | `852a2ac8a2293d34...` |
| tiled-extreme-levels | 7x4 | false | true | 1 | `97bb51e512857026...` | `ba24cfa77eca196b...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `cc3fc89ea953ca0e...` | `51933064c67af747...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 1 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/halftone:halftone` (halftone)

Source: `halftone/halftone.glsl` (8440 bytes, `063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7`). Canonical factory `canonicalFactory65` (`bd871eab3baf361602c23965acf45f463ef9cb9b230bbb4ec5dd70496cd87626`). Authorized defines: `{"MODE":0,"PATTERN":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| classic-screen-angles | 6x5 | false | true | 4 | `a1375400a114b717...` | `d7755d2c29c8ad78...` |
| coarse-soft-screen | 5x6 | false | true | 4 | `13bda3b1ec2b2af5...` | `af86936d44bb597e...` |
| tiled-fine-crisp-screen | 7x4 | false | true | 4 | `a460399d7e7ad78f...` | `4ff575f9f5d075bd...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/lens:lens` (lens)

Source: `lens/lens.glsl` (2909 bytes, `6633d8c7b1ab23600cb25bb87f3f67c5d1d148b0626169f24de520fbce9e64a5`). Canonical factory `canonicalFactory71` (`34b7d733404af7dbeca09a83530e773f8c0cff1abf50ce8ffc65df51d6ab45ff`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| strong-barrel | 6x5 | false | true | 2 | `db64101e6a803d72...` | `92363914d522c6b7...` |
| pincushion-no-aspect | 5x6 | false | true | 2 | `024c4ccd5ad352e7...` | `466dd812d6947abb...` |
| tiled-mild-barrel | 7x4 | false | true | 2 | `2e5adfd910e1dda6...` | `dbc4e0adb8d4e4e2...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `024bc8fde73f1271...` | `1a8bb24a53443b3f...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/lensWarp:lensWarp` (lensWarp)

Source: `lensWarp/lensWarp.glsl` (4033 bytes, `543b53a26b14dfdcf979e2601eaad32d6ec683c41427301b851173334a670480`). Canonical factory `canonicalFactory73` (`abd3e31cb7da4d67d87c9b00b86fb74a5c9b433c7e6d9ab95e63191469795d77`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| fast-strong-warp | 6x5 | false | true | 2 | `0a5450124d5f85b7...` | `b43e2554dabf8a59...` |
| slow-gentle-warp | 5x6 | false | true | 2 | `08e609ca2c424605...` | `87bbb13cc567b012...` |
| tiled-static-warp | 7x4 | false | true | 2 | `e23a736ec7f8df52...` | `55073bf9b690c59f...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `2cd90ca6810dc230...` | `226b7e74db5797d7...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/octaveWarp:octaveWarp` (octaveWarp)

Source: `octaveWarp/octaveWarp.glsl` (4889 bytes, `193ed3406281cde12a460560438c9ce839f07e9f7a96f11aac50c23d3a31039f`). Canonical factory `canonicalFactory88` (`180c70dd5605e464aea56920b4c8ec7eec3245db5e40194c8146a64beebf43aa`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| many-octaves-strong | 6x5 | false | true | 2 | `2a3285b842e42795...` | `0e535e68f23583bd...` |
| single-octave-mild | 5x6 | false | true | 2 | `86efa9ddbde566bc...` | `34aaecacdc908fa2...` |
| tiled-clamp-warp | 7x4 | false | true | 2 | `cc18b6af8e96c373...` | `074c5d8fb36afe25...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `1034f0b3a30e343a...` | `07d358cf3c98b110...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/pinch:pinch` (pinch)

Source: `pinch/pinch.glsl` (2296 bytes, `031405e087822fd10b07d972e53f2f6d2da95f67d9c56605cbc104e0b955d71c`). Canonical factory `canonicalFactory100` (`7b53ce4a42fce3b2b90e4b2e84f69d33d385833e30f38a2b8bec900c28b36d32`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| deep-pinch-mirror | 6x5 | false | true | 2 | `b41c88436f482e10...` | `570c35beba5064b0...` |
| shallow-pinch-repeat | 5x6 | false | true | 2 | `b17dfb9cfed0d979...` | `7f788d5c0b7f9ead...` |
| tiled-clamp-pinch | 7x4 | false | true | 2 | `359bc7ba62c98775...` | `4e211b9d1ec340c2...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `6ca041af896619b4...` | `af5820a1644a0249...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/polar:polar` (polar)

Source: `polar/polar.glsl` (2027 bytes, `391b82e45bc2ea9799de1a200afbd735af96ad15627695d46cfc8caa1298a36d`). Canonical factory `canonicalFactory111` (`6cf35ee99e5ab1746648a23353317055420233b45f860e6ab7d2068beace0748`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| polar-mode-spin | 6x5 | false | true | 2 | `b8a2937aeadd0ff0...` | `a5b2c8c37c8955d4...` |
| vortex-mode-still | 5x6 | false | true | 2 | `03bbb0371776244f...` | `230ba3f9f15fd72c...` |
| tiled-vortex-drift | 7x4 | false | true | 2 | `fe08438aa09a785d...` | `e215cfadc2682ef9...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `1887c0d221714f14...` | `fef2b72f49511671...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/pondRipples:pondRipples` (pondRipples)

Source: `pondRipples/pondRipples.glsl` (5187 bytes, `2958de77f0cdf2a21a00d1505ea75f26df5b66dd7f2cb98431e27178d3386c3d`). Canonical factory `canonicalFactory112` (`02203f5598dd7338d1901521a2741ce9987bf014e5544c6598316494f34a1fb6`). Authorized defines: `{"STYLE":2,"WRAP":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| many-ridges-strong-outward | 6x5 | false | true | 2 | `961b89d7734213eb...` | `61a730e741966861...` |
| few-ridges-mild-inward | 5x6 | false | true | 2 | `79515be98a68cdef...` | `43b61f1c3e6a8c34...` |
| tiled-static-ripples | 7x4 | false | true | 2 | `b1b3784afdc9f06d...` | `a99dd09ef1f0d745...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `4716624ea0810bb9...` | `1ad3dd8118f2849f...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/spiral:spiral` (spiral)

Source: `spiral/spiral.glsl` (2869 bytes, `3d609c5028c859d82c060af21b0675dd0dd0ec6f720dbc9e3b3b21a65893ef4a`). Canonical factory `canonicalFactory143` (`a7f7bb7a38e6e81d0d5e3346252b8f722da22bbc9e72407d77ede091136e252b`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| tight-fast-spiral | 6x5 | false | true | 2 | `10c57a63fe3636c0...` | `44a98b28bd6a5cdf...` |
| loose-slow-spiral | 5x6 | false | true | 2 | `592d469cccd16dee...` | `ea5105292da9e6bc...` |
| tiled-clamp-spiral | 7x4 | false | true | 2 | `3bb855cb4e8e7279...` | `2e1cd49bee844cbb...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `3088ea7095f94ece...` | `48f7429e8f2b5673...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/stamp:stThreshold` (stThreshold)

Source: `stamp/stThreshold.glsl` (3467 bytes, `d93168982b13907e32e1264c021c39f9d434ae122efd7d11898733293ee5da94`). Canonical factory `canonicalFactory147` (`66a9f063457ec317b557c9a5c6fde25f1d30d1b8c9e5433de269826e1d4c4c8e`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| ragged-torn-edges | 6x5 | false | true | 1 | `3915f7bc1de212e6...` | `6becee4b4ad80257...` |
| clean-iso-line | 5x6 | false | true | 1 | `5d27231ea8cd2a51...` | `fc4159352266a3ab...` |
| tiled-high-balance | 7x4 | false | true | 1 | `d66c600813bb458d...` | `12f034215220c32e...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/step:step` (step)

Source: `step/step.glsl` (709 bytes, `4f5680a9b25a2c12cecdcef3cc1ba106c2ee7a8390790544a3425890153cb7bf`). Canonical factory `canonicalFactory148` (`29448cafeecb2459fa5a3f9d87d35504130d27a35e8aa3e4d5d4fde8a50a92d5`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| low-threshold | 6x5 | false | true | 1 | `8bd4ac1fba191f42...` | `bbb48f936a0dd3af...` |
| high-threshold | 5x6 | false | true | 1 | `2581aafae2f55010...` | `38cb3076e2e9c64d...` |
| tiled-mid-threshold | 7x4 | false | true | 1 | `6bbc1a3c2c1acdaf...` | `c3315432f842b982...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `5acfb6e0fdd1cf07...` | `93b3d445b7d07b42...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 1 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/stipple:stipple` (stipple)

Source: `stipple/stipple.glsl` (8490 bytes, `69d75b6fab4281fe0a0997eaf6b7b81e5ab30f0da5dfec9255c9dbb6e914c609`). Canonical factory `canonicalFactory149` (`ac82012ece03dfd1aafbae2fe6ccfeb9b71775033c2a47b6b0b18a78baa99c91`). Authorized defines: `{"MODE":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| small-cells-jitter | 6x5 | false | true | 1 | `d88029c56c5fc0e4...` | `9f9b464da96f3bf3...` |
| large-cells | 5x6 | false | true | 1 | `3bfa80eaee357ac9...` | `503338d9f0778dbe...` |
| tiled-fine-cells | 7x4 | false | true | 1 | `7acb7f7648d59004...` | `900b705aeee20643...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/tunnel:tunnel` (tunnel)

Source: `tunnel/tunnel.glsl` (3062 bytes, `c0ebe43eead7a1c040dd4a37162d634fe4b1a93ea0b8704bac502fbc5a978193`). Canonical factory `canonicalFactory163` (`ddf2adbde6aac7eb3d8bf123dbaa32bf39a04b5005e561306a5b68075777ed7a`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| hexagon-fast-spin | 6x5 | false | true | 2 | `badcb2d69d408179...` | `6c1240780534cfb4...` |
| circle-reverse-vignette | 5x6 | false | true | 2 | `3211993255d31203...` | `fa536b18979d5e13...` |
| tiled-square-tunnel | 7x4 | false | true | 2 | `0d4ce82b6c8f23a1...` | `02a97358520a37da...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `9e7b9d72ae968074...` | `a93801dc18be4e91...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/warp:warp` (warp)

Source: `warp/warp.glsl` (3095 bytes, `f3034ac02a2926b819ff874d2d1d0d3dacebf2b7a409c983237d6a71865942ee`). Canonical factory `canonicalFactory169` (`c87b88745cdd30f4dbad852171c9ad6282112b82ad73f69471e064b9e5d4c20f`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| strong-warp-repeat | 6x5 | false | true | 2 | `84bf4367a19a1212...` | `2815fd319ca4fcfa...` |
| mild-warp-mirror | 5x6 | false | true | 2 | `88d9bc2592c68f5b...` | `120d1a95eeb2949b...` |
| tiled-clamp-warp | 7x4 | false | true | 2 | `2352f8d82313946a...` | `eb7b54259fab4380...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `ffa4e02b611e65b1...` | `2fbaac23b41ec1f5...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## Negative closure

- **antialias_off_would_be_worthless_if_undetected**: refused -- every case independently asserts ordinal_count_observed against ordinal_count_expected (0 vs 2/1/4) at build time; an oracle accidentally rendered with derivatives disabled everywhere would fail the build, not ship silently.
- **sign_flip_zero_on_fwidth_programs_treated_as_bug**: forbidden -- it is a proven bit-exact invariant (|x|+|y| unchanged under simultaneous negation of both terms), asserted, not hidden; see mutations.sign_flip.expected_zero per program.
- **reusing_grade_clusters_luma_weights_or_index_mutation_shapes**: not applicable -- this cluster has no per-program constant global or indexed local array; its two mutations (sign_flip, lane_transpose) target the ONE shared mechanism (glsl-runtime.js wrapDerivatives) all 15 programs route through, verified applicable to every program rather than assumed.

