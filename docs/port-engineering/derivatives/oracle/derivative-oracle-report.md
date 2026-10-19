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

Source: `bulge/bulge.glsl` (2352 bytes, `87f26ffa13ffe946d94d92a00bd45ca3a9787b9ee402dfe04ebc3d4a911eb170`). Canonical factory `canonicalFactory25` (`ad820a9b1bafa9d9d6ee161a391d5441bd91d9b5994f80436fada0760c6df60e`). Authorized defines: `{}`.

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

Source: `celShading/celShadingColor.glsl` (2780 bytes, `90fa87484d3549bdaa2ddca4836a7ca8602ad4f1f30aa87a72841d4e013521f4`). Canonical factory `canonicalFactory27` (`8deff4d60013a32e2d4deac8c2bfde9f9415ba4484b9f69ae0a25ed2d484a4c8`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| sharp-levels-warm-light | 6x5 | false | true | 1 | `40b4e31d630cd45d...` | `0bd57f2632857441...` |
| soft-levels-cool-light | 5x6 | false | true | 1 | `e10525fd0ba2a937...` | `852a2ac8a2293d34...` |
| tiled-extreme-levels | 7x4 | false | true | 1 | `94ce502bcf3b895c...` | `ba24cfa77eca196b...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `cc3fc89ea953ca0e...` | `51933064c67af747...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 1 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/halftone:halftone` (halftone)

Source: `halftone/halftone.glsl` (8440 bytes, `063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7`). Canonical factory `canonicalFactory65` (`7c57e26e7d9cbf9858ee1c57dfeeea298781d885e72ce4612ba12de1be274069`). Authorized defines: `{"MODE":0,"PATTERN":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| classic-screen-angles | 6x5 | false | true | 4 | `7823336de297ed64...` | `e4e654d55a67c928...` |
| coarse-soft-screen | 5x6 | false | true | 4 | `475b152dbac70784...` | `fed14d8d8b881c99...` |
| tiled-fine-crisp-screen | 7x4 | false | true | 4 | `6e5091b45ba47874...` | `4ff575f9f5d075bd...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/lens:lens` (lens)

Source: `lens/lens.glsl` (2909 bytes, `6633d8c7b1ab23600cb25bb87f3f67c5d1d148b0626169f24de520fbce9e64a5`). Canonical factory `canonicalFactory71` (`705cc5f478e67cf82e0c1d62d806fdd01f350eb56a382b1b948f66da0a052e52`). Authorized defines: `{}`.

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

Source: `lensWarp/lensWarp.glsl` (4033 bytes, `543b53a26b14dfdcf979e2601eaad32d6ec683c41427301b851173334a670480`). Canonical factory `canonicalFactory73` (`d1da5952b0adda8365c05b3baa70eb77744fa2c6bf469a824891c3cf533044a3`). Authorized defines: `{}`.

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

Source: `octaveWarp/octaveWarp.glsl` (4889 bytes, `193ed3406281cde12a460560438c9ce839f07e9f7a96f11aac50c23d3a31039f`). Canonical factory `canonicalFactory88` (`7f3ecff906753d556989a8f6fcc7cc9055790603fc6c83087f8db9cff4284f97`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| many-octaves-strong | 6x5 | false | true | 2 | `2a3285b842e42795...` | `0e535e68f23583bd...` |
| single-octave-mild | 5x6 | false | true | 2 | `e4195741bc2b2bf6...` | `5aa05bb83f0d1dfd...` |
| tiled-clamp-warp | 7x4 | false | true | 2 | `cc18b6af8e96c373...` | `074c5d8fb36afe25...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `1034f0b3a30e343a...` | `07d358cf3c98b110...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/pinch:pinch` (pinch)

Source: `pinch/pinch.glsl` (2296 bytes, `031405e087822fd10b07d972e53f2f6d2da95f67d9c56605cbc104e0b955d71c`). Canonical factory `canonicalFactory100` (`0855996afb913b3b1640161d6cb76a79521aaa4a8ab0037b01486e0ac634b7a0`). Authorized defines: `{}`.

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

Source: `polar/polar.glsl` (2027 bytes, `391b82e45bc2ea9799de1a200afbd735af96ad15627695d46cfc8caa1298a36d`). Canonical factory `canonicalFactory111` (`410f9789cb15574a10d62e3fb84c63651c45e7e4408dd39717c24d87ece2cf78`). Authorized defines: `{}`.

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

Source: `pondRipples/pondRipples.glsl` (5187 bytes, `2958de77f0cdf2a21a00d1505ea75f26df5b66dd7f2cb98431e27178d3386c3d`). Canonical factory `canonicalFactory112` (`47668715f2eefab5cadbd8cda7b087c4d17a2de7d17ed72e1e349d844e290f61`). Authorized defines: `{"STYLE":2,"WRAP":0}`.

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

Source: `spiral/spiral.glsl` (2869 bytes, `3d609c5028c859d82c060af21b0675dd0dd0ec6f720dbc9e3b3b21a65893ef4a`). Canonical factory `canonicalFactory143` (`4286be014346159fbd42eaede57be293b4a3af6316ed04d4f1bbeaa120b5317e`). Authorized defines: `{}`.

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

Source: `stamp/stThreshold.glsl` (3467 bytes, `d93168982b13907e32e1264c021c39f9d434ae122efd7d11898733293ee5da94`). Canonical factory `canonicalFactory147` (`6b09d743f1e2ef5c524cf295a2f653e1e1fda00cb75e7b7fd40faca67e5c2ae9`). Authorized defines: `{}`.

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

Source: `step/step.glsl` (709 bytes, `4f5680a9b25a2c12cecdcef3cc1ba106c2ee7a8390790544a3425890153cb7bf`). Canonical factory `canonicalFactory148` (`d4082a2d93c2267e09906832e0536b6715779a9a6098146e44f92c7a85f1d084`). Authorized defines: `{}`.

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

Source: `stipple/stipple.glsl` (8490 bytes, `69d75b6fab4281fe0a0997eaf6b7b81e5ab30f0da5dfec9255c9dbb6e914c609`). Canonical factory `canonicalFactory149` (`22368bbd125d9556b77c83d46dbd606b67682208d620e8538306ec9badfe5250`). Authorized defines: `{"MODE":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| small-cells-jitter | 6x5 | false | true | 1 | `d88029c56c5fc0e4...` | `9f9b464da96f3bf3...` |
| large-cells | 5x6 | false | true | 1 | `f60abc7fc1e4d6ed...` | `503338d9f0778dbe...` |
| tiled-fine-cells | 7x4 | false | true | 1 | `1d0f1f2744f7ae93...` | `900b705aeee20643...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/tunnel:tunnel` (tunnel)

Source: `tunnel/tunnel.glsl` (3062 bytes, `c0ebe43eead7a1c040dd4a37162d634fe4b1a93ea0b8704bac502fbc5a978193`). Canonical factory `canonicalFactory163` (`5f60bd8a8a391d6878fb618dea961fb0ecb5d5254c5fcd090019154575300c3b`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| hexagon-fast-spin | 6x5 | false | true | 2 | `0e2c69ddbddb25c9...` | `6c1240780534cfb4...` |
| circle-reverse-vignette | 5x6 | false | true | 2 | `88c208d9876bd053...` | `fa536b18979d5e13...` |
| tiled-square-tunnel | 7x4 | false | true | 2 | `0d4ce82b6c8f23a1...` | `02a97358520a37da...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `5072c32f16d812ff...` | `a93801dc18be4e91...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 3 | 1 | 0 | nonzero |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/warp:warp` (warp)

Source: `warp/warp.glsl` (3095 bytes, `f3034ac02a2926b819ff874d2d1d0d3dacebf2b7a409c983237d6a71865942ee`). Canonical factory `canonicalFactory169` (`469faed930de1421264adbb8fd5614b706e8b3cd5f0a0aedb9f1135b360e0095`). Authorized defines: `{}`.

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

