# Tetra Color Array pixel-parity oracle

Frozen JavaScript ground truth for `filter/tetraColorArray:tetraColorArray`, rendered through the canonical noisemaker-for-cpu factory. Float32 hashes are exact byte contracts; RGBA8 hashes are a second exact byte contract. The custom comparer only adds diagnostics and does not relax either contract.

## Coverage

- Color modes: 0, 1, 2, 3
- Color counts: 2, 3, 4, 6, 8
- Position modes: auto, manual
- Smoothness: 2 zero cases and 6 nonzero cases
- Explicitly discriminated wrap seams: 5 cases
- Alpha values (including both endpoints): 0, 0.5, 0.65, 1

Every case passes exact repeated-render identity, input immutability, finite-output, source-alpha preservation, and public-catalog-versus-direct-canonical equality. Non-RGB, manual-position, nonzero-smoothness, and count-above-two cases also carry a deliberately changed control render that is required to diverge.

## Cases

| Case | Mode | Count | Positions | Smoothness | Alpha | Wrap seam | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| count2-rgb-auto-hard-alpha0 | 0 | 2 | auto | 0 | 0 | false | `3dcff2fb3dd719685b5dace289a83c43e26ce71864629731ba1b16050efa7d59` | `fa791a7ffb1b338671bd88b623129369ae3d851d8ea22010b55460a713f9c40b` |
| count2-hsv-manual-wrap-alpha1 | 1 | 2 | manual | 0.8 | 1 | true | `21820ad3eeec664df6e39a4811a492ec5df321987d40de9074efdafbdc6c2196` | `5f0ab6f8bdac32ef8a7452e5193123dd89e4844c8d38d0e4899ca6d3c919ab0d` |
| count3-oklab-auto-smooth-alpha1 | 2 | 3 | auto | 0.55 | 1 | true | `7f6dd145d388035d887ab8f7354ea5f8ac112308ab2af4cd450acfb9109952f7` | `b093599bf67fbec5910b217f3a5e21b3eb3d45df0675fb81ea366444165f9abe` |
| count4-oklch-manual-smooth-alpha-half | 3 | 4 | manual | 0.6 | 0.5 | false | `7bfa0f3bb354a40e96ac684b626f9297372099758275fc3b68c8e4b5e15e3497` | `84e3a53f2b74c8e0ad8ceb1eb56dd676dce0e362c5a7b2d178c18e5dcfce2204` |
| count6-rgb-manual-hard-alpha1 | 0 | 6 | manual | 0 | 1 | false | `6ae31270aefed639e9a3d991343814acea31aefef0402195b0176c7e464a560e` | `9cfbaf480e5c6e50bff9b9532e44024e05d456986554ada3b58874c914362e88` |
| count6-oklch-auto-wrap-alpha1 | 3 | 6 | auto | 0.9 | 1 | true | `86af3fa97c866fe0a27ebf45fd4c42be707cdff39c4c794b8599efd4b1602df4` | `faaa9d3df47b396be35a389966886f5dfee0f1baf5d0c8204089a24b429b82e3` |
| count8-hsv-auto-wrap-alpha1 | 1 | 8 | auto | 1 | 1 | true | `b8564076387d982b669758eb32157354426136d75960178737a23d7a0be44acd` | `b0a1523f18451dae0757764e66b7db512a4d0dc3e8611aeb57047736fc09b164` |
| count8-oklab-manual-wrap-alpha065 | 2 | 8 | manual | 0.5 | 0.65 | true | `80ce433ab64d14a0d0caaae7623bb087e8480937004565adeb777465afd0c008` | `185fcc2dcec8bac35addd0dcc7797a31d6e356ec1ae0fc45f590a0cb015fe9e9` |

## Probe and determinism contract

- Each output records exact Float32 values and little-endian bits at both sides of the `fract` wrap seam, three interior transition points, and one asymmetric colored-input point.
- The top-row seam probes are driven by grayscale luminances 0 and 1; the shader maps them to opposite sides of the repeated gradient seam. Every case marked as a wrap case is required to differ at those seam lanes from its otherwise-identical `smoothness=0` control.
- Each render uses seed 4242, time 0, frame 37, and delta time 1/60. No elapsed timing or host-specific path is serialized.
- The generator rejects drift in the canonical/public/adapter/runtime files, canonical factory body, GLSL source, catalog identity, adapter absence, and authoritative `colorCount` metadata contract.

## Reference provenance

- Upstream snapshot revision: `c51037ad9e60850b74490c01a9eecf08c7d28e8c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source SHA-256: `68c7cabce311a0a05ba116ce8d34bd5e70e0c09bfb8eab06c93f4f9e01fa5438`
- Canonical factory SHA-256: `839315b44a68ea9c712dca226754ea55c2283f6ea0ef30d4c79cd831f97036ff`
- Node reference engine used to freeze this file: `v24.7.0`
