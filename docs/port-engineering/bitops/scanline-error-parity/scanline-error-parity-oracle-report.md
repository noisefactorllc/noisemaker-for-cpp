# Scanline Error float-bit ingress and pixel-parity oracle

Frozen JavaScript ground truth for `filter/scanlineError:scanlineError`. Exact Float32 and RGBA8 hashes cover both scanline and VHS paths, including live `floatBitsToUint` execution, tiling, time, and legal control extrema. A separate frontend probe freezes the three-node admission boundary and the captured pre-admission gate chain.

## Frozen authority

- Upstream snapshot revision: `117a236679d1db3ab8f0e278230ece277b57564c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source: 13302 bytes, SHA-256 `66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198`
- Canonical factory: `canonicalFactory129`, 17646 bytes, SHA-256 `ea129bebd5933e5bafa69b5906d79622118f1a243137afc365eb775f09f7447f`
- Public catalog identity is exactly the canonical factory; no adapter override exists.

## Captured pre-admission C++ frontend boundary

- Validator first error: `filter/scanlineError:scanlineError:234:24: unsupported builtin floatBitsToUint`
- Emitter first error: `filter/scanlineError:scanlineError:234:24: unsupported builtin floatBitsToUint`
- Exactly three `floatBitsToUint(float) -> uint` nodes occur, all in reachable `hashNoise` and all direct children of one `uvec3` constructor.
- Replacing only those three callees in memory exposed validator `pass` and emitter `pass` in live typed slice 174; there was no later pre-admission frontend gate.
- Do not widen or reuse Caustic identity. Add a parallel exact Scanline Error profile, while reusing the existing `noisemaker::float_bits_to_uint` lowering and runtime helper. The global builtin/capability vocabulary remains unchanged; no scalar-XOR profile is needed.

## Direct conversion fixtures

The 15 raw-word fixtures cover signed zero, subnormals, normal finite values, Float32 extrema, infinities, and multiple NaN payloads. Shipped runtime and an independent little-endian DataView recomputation agree exactly. 14 reachable/native-required records have aggregate words SHA-256 `2940cc104d10f8b93089f6a2949153781c348ea11e6965f67fdd22254fc16e8d`. The signaling-NaN row is diagnostic only: JavaScript quiets it at the Number boundary, while the existing C++ `std::bit_cast` helper correctly preserves raw bits and must not be changed; Scanline Error arithmetic cannot produce a signaling NaN.

## Render cases

| Case | Size | Mode | Speed | Offset | Distortion | Noise | Time | Seed | Frame | Tile/full | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| scanline-zero-controls | 5x4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0,0/5,4 | `561b504db5d724dec4199e1c823d1eb29e2d5c02b12756f0813e809bfed00dbf` | `f023b63f1219106a311e471e699d64fb905f1c86a0d4005cc5a4397ce99292a7` |
| scanline-default-still | 7x5 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0,0/7,5 | `0cc937af6ba3be4858a3c2bd54cc2d0805f91b1b299d46764b0d01778ccb2e78` | `a7ba786bf33be952656da1a92093cf9666375c422bae4c31d07034e6dcf71cd2` |
| vhs-default-still | 7x5 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0,0/7,5 | `7dc34b70cc1f670d26ff3347ce7b7c74f2c9196283e491dde5b76fe47ec8ce24` | `5e041a3c129ed5bbe4199ca0cc88adb80b225b49d13c300324344eea4694be25` |
| vhs-default-extreme-seed-frame | 7x5 | 1 | 1 | 0 | 1 | 1 | 0 | 4294967295 | 4294967295 | 0,0/7,5 | `7dc34b70cc1f670d26ff3347ce7b7c74f2c9196283e491dde5b76fe47ec8ce24` | `5e041a3c129ed5bbe4199ca0cc88adb80b225b49d13c300324344eea4694be25` |
| scanline-animated-max-controls | 8x6 | 0 | 5 | -10 | 3 | 3 | 0.375 | 2147483648 | 17 | 0,0/8,6 | `ba301896aa4ab5686d7a8531fbd18f88e4c71dffe43d58ed2c076623b2940d14` | `eba117fe97f00937168a9402caf70c957310f0ce6b1de25a18796e9e8cf7f532` |
| vhs-animated-max-controls | 8x6 | 1 | 5 | 10 | 3 | 3 | 0.375 | 2147483648 | 17 | 0,0/8,6 | `4c11d6923a3e00c18e1b39ceb56de3bb7e0734956c276c6645c66470ccd9f218` | `428023ad927269df7a78eea6f36c890dcb003f1ceb71b2249a0d800cea7f94ea` |
| vhs-signed-zero-controls | 6x4 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0,0/6,4 | `0bde87f5e4280078e397227bd7f1ae9c9d55f2d5d1c39072c635d3183c505e66` | `fd9437bb23f305ed2255aacfc2d73126f1d2c70e3c752ae7ddd02fafa7913d7c` |
| vhs-large-time-offset-ulp | 6x5 | 1 | 1 | 1 | 2 | 2 | 16777216 | 16777217 | 9007199254740991 | 0,0/6,5 | `b732eb09cdab383a50f664179fcce403108336b9865b0614972b68a0e8dcb138` | `7cf174ba6a03e9f7d6f80eafdf43c59ce3cd26d4a8a7d0db978cbba79463ef1c` |
| scanline-tiled-noninteger-scale | 4x3 | 0 | 2 | -0.25 | 2 | 1.5 | 0.625 | 123456789 | 9 | 3,2/11,7 | `f52466ddc0bf6cb3b779c6375b78168c3c5c8327bb20704a305a442517ef554f` | `9e702ed79d7a791c9b9f8de3b8c21c12c0785093bb8fa611606cfc42355dff19` |
| vhs-tiled-noninteger-scale | 4x3 | 1 | 2 | 0.25 | 2 | 1.5 | 0.625 | 123456789 | 9 | 3,2/11,7 | `fda929f088a7de0319de2761527f18f131c037c47128dabdc7263167ea62da0d` | `3fe72e8d9530f59c7852fae8b1b77b2524864ed7eb999d4c06fdd927f1ed5eea` |

Every case requires exact repeated-render identity, exact input-bit immutability, finite output for finite legal controls, and direct-canonical/public-catalog equality. The paired extreme seed/frame case proves those external bindings are unused. Both tile cases require their offset mutation to diverge.

## Mutation discrimination

| Mutation | Required witnesses | All divergent cases |
| --- | --- | --- |
| lane-x-bitcast-replaced-by-numeric-conversion | vhs-default-still | vhs-default-still, vhs-default-extreme-seed-frame, vhs-animated-max-controls, vhs-large-time-offset-ulp, vhs-tiled-noninteger-scale |
| lane-y-bitcast-replaced-by-numeric-conversion | vhs-default-still | vhs-default-still, vhs-default-extreme-seed-frame, vhs-animated-max-controls, vhs-large-time-offset-ulp, vhs-tiled-noninteger-scale |
| lane-z-bitcast-replaced-by-numeric-conversion | vhs-default-still | vhs-default-still, vhs-default-extreme-seed-frame, vhs-animated-max-controls, vhs-large-time-offset-ulp, vhs-tiled-noninteger-scale |
| pcg-output-lane-x-replaced-by-y | vhs-default-still | vhs-default-still, vhs-default-extreme-seed-frame, vhs-animated-max-controls, vhs-large-time-offset-ulp, vhs-tiled-noninteger-scale |
| time-offset-ignored | scanline-animated-max-controls, vhs-animated-max-controls | scanline-animated-max-controls, vhs-animated-max-controls, vhs-large-time-offset-ulp, scanline-tiled-noninteger-scale, vhs-tiled-noninteger-scale |
| mode-branches-inverted | scanline-default-still, vhs-default-still | scanline-zero-controls, scanline-default-still, vhs-default-still, vhs-default-extreme-seed-frame, scanline-animated-max-controls, vhs-animated-max-controls, vhs-signed-zero-controls, vhs-large-time-offset-ulp, scanline-tiled-noninteger-scale, vhs-tiled-noninteger-scale |
| global-tile-offset-ignored | scanline-tiled-noninteger-scale, vhs-tiled-noninteger-scale | scanline-tiled-noninteger-scale, vhs-tiled-noninteger-scale |

The native-required direct conversion corpus separately rejects numeric conversion, erasing negative zero, replacing nonfinite bit patterns with zero, and reinterpreting Float64 storage. Frontend contract negatives reject wrong key/profile/hash, a removed site, a swapped child, and an added site.

## Regeneration

From the repository root. The ordinary checks are durable after production admission; `--live-frontier` is an optional diagnostic that observes the then-current gate without rewriting the frozen live174 evidence:

```sh
python3 docs/port-engineering/bitops/scanline-error-parity/scanline_error_frontend_probe.py --check
python3 docs/port-engineering/bitops/scanline-error-parity/scanline_error_frontend_probe.py --live-frontier
node docs/port-engineering/bitops/scanline-error-parity/scanline_error_parity_oracle_generator.mjs
node docs/port-engineering/bitops/scanline-error-parity/scanline_error_parity_oracle_generator.mjs --check
```

