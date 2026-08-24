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

Source: `bulge/bulge.glsl` (2352 bytes, `87f26ffa13ffe946d94d92a00bd45ca3a9787b9ee402dfe04ebc3d4a911eb170`). Canonical factory `canonicalFactory26` (`48eb3ed665bd4d3f27d5bac68e9474ccc38a75168f46ddb61dadf611fc7903ef`). Authorized defines: `{}`.

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

Source: `celShading/celShadingColor.glsl` (2780 bytes, `90fa87484d3549bdaa2ddca4836a7ca8602ad4f1f30aa87a72841d4e013521f4`). Canonical factory `canonicalFactory28` (`5c10f42ac05d71a35295b6d2e42adbb3c137da8eb1a6b2d5fbfe277f2f5488c9`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| sharp-levels-warm-light | 6x5 | false | true | 1 | `b5ad5619e43ba66b...` | `0bd57f2632857441...` |
| soft-levels-cool-light | 5x6 | false | true | 1 | `1ce63f4d9d8a65dd...` | `852a2ac8a2293d34...` |
| tiled-extreme-levels | 7x4 | false | true | 1 | `97bb51e512857026...` | `ba24cfa77eca196b...` |
| antialias-off-diagnostic | 4x7 | true | false | 0 | `cc3fc89ea953ca0e...` | `51933064c67af747...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 1 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 1 | 0 | nonzero |

## `filter/halftone:halftone` (halftone)

Source: `halftone/halftone.glsl` (8440 bytes, `063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7`). Canonical factory `canonicalFactory67` (`7ddd550b40cc5484a4cac387c2560fe0cbf8d5eb7b30b28a123605d84995b58d`). Authorized defines: `{"MODE":0,"PATTERN":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| classic-screen-angles | 6x5 | false | true | 4 | `25487c0a06d8a246...` | `d7755d2c29c8ad78...` |
| coarse-soft-screen | 5x6 | false | true | 4 | `6f55e86da3a112ad...` | `af86936d44bb597e...` |
| tiled-fine-crisp-screen | 7x4 | false | true | 4 | `b073c98d9bb77308...` | `4ff575f9f5d075bd...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/lens:lens` (lens)

Source: `lens/lens.glsl` (2909 bytes, `6633d8c7b1ab23600cb25bb87f3f67c5d1d148b0626169f24de520fbce9e64a5`). Canonical factory `canonicalFactory74` (`bbee3c76d338b5a7d7013761be6b925f29e8699cc9f8dca06d3d3aa0bef51e41`). Authorized defines: `{}`.

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

Source: `lensWarp/lensWarp.glsl` (4033 bytes, `543b53a26b14dfdcf979e2601eaad32d6ec683c41427301b851173334a670480`). Canonical factory `canonicalFactory76` (`c4d5f24a54342ff9599a85fd2bdf556badce8cf6da7d8397b33518dc321cc4a9`). Authorized defines: `{}`.

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

Source: `octaveWarp/octaveWarp.glsl` (4902 bytes, `ced7dca971a24fb3d8a48641c7bb66c4af637a57984d45ddc9e51f0492a59bea`). Canonical factory `canonicalFactory91` (`122e909b90228a9e22184d3601611091ee5493029d03392966e82591846ccf30`). Authorized defines: `{}`.

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

Source: `pinch/pinch.glsl` (2296 bytes, `031405e087822fd10b07d972e53f2f6d2da95f67d9c56605cbc104e0b955d71c`). Canonical factory `canonicalFactory103` (`9061ee4b7cd062fc06723cd9366777949bcba7c50a7cd6f1fc1c74b9e1d3a355`). Authorized defines: `{}`.

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

Source: `polar/polar.glsl` (2027 bytes, `391b82e45bc2ea9799de1a200afbd735af96ad15627695d46cfc8caa1298a36d`). Canonical factory `canonicalFactory114` (`782461118d560ca22e7a5f4e945a1b3619c5fa381f07a032f5c305c08149aa96`). Authorized defines: `{}`.

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

Source: `pondRipples/pondRipples.glsl` (5187 bytes, `2958de77f0cdf2a21a00d1505ea75f26df5b66dd7f2cb98431e27178d3386c3d`). Canonical factory `canonicalFactory115` (`acd9474e33c243581c29858426ad1ffb107698c42176735c1f7c1b0d03c329b5`). Authorized defines: `{"STYLE":2,"WRAP":0}`.

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

Source: `spiral/spiral.glsl` (2869 bytes, `3d609c5028c859d82c060af21b0675dd0dd0ec6f720dbc9e3b3b21a65893ef4a`). Canonical factory `canonicalFactory146` (`69f34db1db7515a72c87f0d67dea8cc0e08fd067a398b1655b4e5b3fa8541684`). Authorized defines: `{}`.

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

Source: `stamp/stThreshold.glsl` (3467 bytes, `d93168982b13907e32e1264c021c39f9d434ae122efd7d11898733293ee5da94`). Canonical factory `canonicalFactory150` (`3c6a795c3782cf5c3b32b48c5828696df87ed687e585e56c97971604a680aa79`). Authorized defines: `{}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| ragged-torn-edges | 6x5 | false | true | 1 | `a713acec58187054...` | `6becee4b4ad80257...` |
| clean-iso-line | 5x6 | false | true | 1 | `422d4bf0ab1bcbd4...` | `fc4159352266a3ab...` |
| tiled-high-balance | 7x4 | false | true | 1 | `4768703cd00b1179...` | `12f034215220c32e...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/step:step` (step)

Source: `step/step.glsl` (709 bytes, `4f5680a9b25a2c12cecdcef3cc1ba106c2ee7a8390790544a3425890153cb7bf`). Canonical factory `canonicalFactory151` (`a2e3ae28362d275bacdda15b53d62fe97e36c9df45b60075ee65db116a053aba`). Authorized defines: `{}`.

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

Source: `stipple/stipple.glsl` (8490 bytes, `69d75b6fab4281fe0a0997eaf6b7b81e5ab30f0da5dfec9255c9dbb6e914c609`). Canonical factory `canonicalFactory152` (`50e732c0b6904d2397bf28ac9da6184550c06c4dd416ac2d115846feae51694f`). Authorized defines: `{"MODE":0}`.

### Cases

| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| small-cells-jitter | 6x5 | false | true | 1 | `558d41dbe6da042f...` | `a6272d86f087781c...` |
| large-cells | 5x6 | false | true | 1 | `6f8596943639a281...` | `8d1173c5862d82d8...` |
| tiled-fine-cells | 7x4 | false | true | 1 | `7acb7f7648d59004...` | `900b705aeee20643...` |

### Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |
| --- | ---: | ---: | ---: | ---: | --- |
| sign_flip | 3 | 0 | 0 | 0 | ZERO (provable fwidth invariant) |
| lane_transpose | 3 | 3 | 0 | 0 | nonzero |

## `filter/tunnel:tunnel` (tunnel)

Source: `tunnel/tunnel.glsl` (3062 bytes, `c0ebe43eead7a1c040dd4a37162d634fe4b1a93ea0b8704bac502fbc5a978193`). Canonical factory `canonicalFactory166` (`c214607fae06b63d8e77f7b6aadee2b5d5b633f193cc8ee4fa7928d1ab97bf26`). Authorized defines: `{}`.

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

Source: `warp/warp.glsl` (3095 bytes, `f3034ac02a2926b819ff874d2d1d0d3dacebf2b7a409c983237d6a71865942ee`). Canonical factory `canonicalFactory172` (`960469b2bbc57d943e2c7c489860967c2e263eb3fbaa99199154e0e1e750fc68`). Authorized defines: `{}`.

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

