# Glitch exact-parity oracle

Program `classicNoisedeck/glitch:glitch`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`.

## Result

The currently shipped JavaScript reference materializes every matrix-product element through `F32(sum)` into a pooled `Float32Array`. The exact target is column-major, left-associated `(T*Q)*S`, with a float32 store after `T*Q` and after the final product. The older plain-Array/no-intermediate-narrowing claim is stale and is actively rejected by this package.

The reachable matrix closure is exactly three `mat4` constructors, two nested `mat4*mat4` nodes, and one `vec4*mat4` node, all in the live `bicubic` function. The captured pre-admission frontier rejects the first `mat4` type before reaching constructor or binary dispatch; `--live-frontier` observes later progress separately.

## Exact contract

- Float output uses raw little-endian float32 lane words; there is no tolerance.
- RGBA8 output uses exact encoded bytes and never substitutes for Float32 parity.
- The custom comparer rejects equal-byte-length dimension mismatches, distinguishes +0 from -0, and reports the first top-down pixel/channel and both lane words.
- Every render is repeated, compared through the public-catalog identity, checked finite, and proves input-surface immutability.

## Direct matrix fixtures

| Case | Left-associated SHA-256 | Right-association mismatched lanes | Unrounded-intermediate mismatched lanes |
| --- | --- | ---: | ---: |
| identity-q | d0a0329be70a2c456732dd1ceb4013d481b04cc3a5ea3a9d67b594de16ab2244 | 0 | 0 |
| fractional-q | b65c9f13623dcf8acd325f14a056a0cf747a0772d4ebb529984dfeadc75c03a5 | 4 | 3 |
| wide-dynamic-q | daf3699fafcc2b273320b3fb6a463bd224e6e8bf8af792ee293279ba78252bb9 | 3 | 1 |
| pcg-shaped-q-a | 303e734d9d4eea2c089fafe3e9cb805226c952ff357bdf8357384c9838831768 | 1 | 1 |
| pcg-shaped-q-b | 98ca17191f978d3fceaa784be9010cfaf5b7a4736766a41b030c4edb5f88c94c | 1 | 0 |

These fixtures call the real shipped `GlslCpuRuntime.stdlib.matrixMult` and independently compare it with a literal `F32(sum)` implementation. Crafted fractional/dynamic-range matrices discriminate both association and the obsolete unrounded-intermediate model.

## Render fixtures

| Case | Size | Seed | Scanlines | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | --- | --- |
| matrix-masked-control | 9x7 | 1 | 0 | 1e776477dd2da5104f3eac46869dc98102ad0a0b78f48c1d51a4f6790248c6f7 | 1a4f5661a45951cbaf878d33c9943d7d71c5b48c6dc8ca901ef9656f86623a2c |
| scanlines-max-seed-one | 11x9 | 1 | 100 | eca7362b1e4bb76bde5e1362b9604b13b99e8687322286404840e06e1e6a025c | ad299db45fd9c554329c00be568b49dfb7dbee05e1f0892ff5cc9e18f6fabc06 |
| scanlines-mid-seed-thirty-seven | 13x10 | 37 | 77 | 69b006f96a7b75f8df07554bafb16f4cef429595fadc3a4f9a0a7327bd4a4df2 | 3d6fc212add720a6bb7c7ae376c3740a18c6d466c7075cdef3cd72a4ec818885 |
| scanlines-min-nonzero | 17x6 | 100 | 1 | fb29b6c883d9d9d7caa9aa86df2875148f27829a47d80c48dc74095741b64216 | b2f3551a4e0f53b877e9d7dd85eaa24b77171c4858421f733ec593e0c5dd3346 |
| aspect-negative-lens-vignette | 7x12 | 99 | 91 | 9e33b34d8ed5598dc4ed4f0ca2834fcc5fdd292c3f5a66c52901109b79372e41 | 7699f12dcc86c580b19fd378f2b6408d3ba6f31b397bb32cebb6fdcadd25243e |
| snow-upper-midpoint | 8x8 | 2 | 63 | aef210055aa6d23610938f0f9d1fd6d7410220986fe0eace79ec10338c15ab15 | 10827bec46c22fdea66e08b7aff06a39b5f43c3ee338f67a137efe3b0977bd6e |
| snow-saturated-tiled | 6x5 | 73 | 88 | ecac2d53127699c55cf7ab9e1e542c68a4ea8ee06b163a0eff677e4fd13567a7 | 46223df666bb4b8b51651fdb54e97604523820660adcd9c4e659c8e3a9b7f103 |
| fractional-full-resolution-tile | 5x9 | 41 | 56 | 50dc57be0409f64be04e8d9dd6188fa57ca38682b021161d4b626fde3faa2c6a | a963dbd08e968e47e9129966bec4ceafffab4801a69e594e320406b42f6f341c |

The suite covers matrix-masked control, maximum and minimum nonzero scanline influence, seed/time extremes, both aspect-lens states, both distortion branches, both vignette branches, all three snow regions, and tiled full-resolution coordinates.

## Render mutation discrimination

| Mutation | Required witnesses | All Float32-divergent cases | All RGBA8-divergent cases |
| --- | --- | --- | --- |
| right-associated-chain | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | (none; Float32 remains authoritative) |
| missing-intermediate-f32-stores | scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette | scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint | (none; Float32 remains authoritative) |
| reverse-inner-operands | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |
| swap-basis-matrices | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |
| omit-basis-products | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |

The matrix-masked control must remain exact for every mutant. The active-scanline witnesses distinguish wrong association, missing intermediate float32 stores, reversed inner operands, swapped basis matrices, and omitted basis products. RGBA8 is recorded but Float32 bits are the binding contract.

## Frontend fail-closed proof

`glitch_matrix_frontend_probe.py` authenticates the exact source/key/profile/hash, all matrix nodes and spans, nested left-association, constructor arities, symbol route, full call-graph reachability, and return route. Its negatives reject wrong key/profile/hash, coefficient drift, association drift, operand-order drift, extra matrix use, constructor arity drift, vector/matrix orientation drift, and bicubic return-route drift.

## Provenance observation

The shared JS tree changed during package assembly: `upstream-snapshot.js` was first observed at `8579de7f8d3ff35a71c35c2c5e32296d0f71ffef1e790db9736f99ab04969936` and then at the consumed/pinned `e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090`. The canonical kernels, public catalog, GLSL runtime/kernel, pass runner, Surface implementation, canonical Glitch factory, and pinned Glitch GLSL bytes remained identical across both observations. The final self-check uses an external temporary fixture root represented by `<external-temp-root>`; a later change in any relevant artifact is a hard failure.

## Regeneration

From the repository root:

```sh
NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>
PYTHONDONTWRITEBYTECODE=1 python3 -B docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_glitch_native_oracle_include.py --check
```

The generator verifies pinned source/runtime/catalog/factory hashes before executing the real unmodified canonical factory. `--check` regenerates the JSON and report in memory and requires byte-for-byte identity.
