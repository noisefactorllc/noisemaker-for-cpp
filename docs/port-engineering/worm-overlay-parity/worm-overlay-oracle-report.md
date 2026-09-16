# canonical CPU worm-overlay oracle report

Ground truth is `renderCanonicalWormOverlay` (`src/effects/cpu/worm-overlay.js`), imported and called directly -- never reimplemented for golden values.

Total cases: **48** (16 case definitions x 3 effect ids).

## Provenance

| File | sha256 |
| --- | --- |
| worm-overlay.js | `4b180a359e477061ef18532707e9516a662c6463e179246dd5f4e118563f208d` |
| surface.js | `0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59` |

Text-surgery self-check: **PASS -- extracted-from-source-text runtime reproduces the real imported renderCanonicalWormOverlay byte-for-byte on every case (asserted at build time)**

## Mutations

| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | ---: | ---: | ---: | ---: |
| rng-multiplier-tampered | 48 | 46 | 0 | 0 |
| normal-sqrt-log-sign-flip | 48 | 46 | 0 | 0 |
| smoothstep-linear | 48 | 36 | 0 | 0 |
| draw-blend-ignores-destination | 48 | 46 | 0 | 0 |
| obedient-unruly-swapped | 48 | 45 | 0 | 0 |
| final-quantization-removed | 48 | 46 | 0 | 0 |
| kink-angle-doubled | 48 | 43 | 0 | 0 |
| scratches-obedient-unruly-labels-swapped | 16 | 15 | 32 | 0 |

- **rng-multiplier-tampered**: the LCG step multiplier is changed, desynchronizing every subsequent draw
- **normal-sqrt-log-sign-flip**: Box-Muller normal() drops the negation on the log term
- **smoothstep-linear**: valueNoiseField uses a linear (not smoothstep) interpolation weight
- **draw-blend-ignores-destination**: alpha compositing drops the destination-blend term (paints flat color)
- **obedient-unruly-swapped**: the 'obedient' shared-rotation branch's condition is inverted
- **final-quantization-removed**: the 1/255-step quantization pass is skipped, leaving raw float32 accumulation
- **kink-angle-doubled**: the flow-field kink contribution to the turn angle is doubled
- **scratches-obedient-unruly-labels-swapped**: scratches' per-layer 'obedient'/'unruly' dispatch is swapped (layerSeed%2===0 now means unruly)

## RNG direct rows

9 seeds x 8 draws each, using the REAL extracted `SeededRng` class (see `worm-overlay-oracles.json` for the full table).

## Noise-field direct rows

2 (width,height,frequency,seed) combinations.

## Cases

| Case | Effect | Size | Seed | Density | Output SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| default-17x11 | filter/fibers | 17x11 | 1 | 1 | `9dbfb238ed2804f6...` |
| tiny-1x1 | filter/fibers | 1x1 | 1 | 1 | `374708fff7719dd5...` |
| tiny-2x2 | filter/fibers | 2x2 | 3 | 0.01 | `f5a5fd42d16a2030...` |
| wide-33x9 | filter/fibers | 33x9 | 7 | 0.5 | `736b116a14baecb7...` |
| tall-9x33 | filter/fibers | 9x33 | 7 | 0.5 | `ef0e23a0045ce3e5...` |
| moderate-64x48 | filter/fibers | 64x48 | 42 | 1 | `1460db1b93101f13...` |
| falsy-seed-zero | filter/fibers | 16x16 | 0 | 1 | `47b053c16459ce82...` |
| falsy-seed-nan | filter/fibers | 16x16 | NaN | 1 | `47b053c16459ce82...` |
| negative-seed | filter/fibers | 20x12 | -5 | 0.3 | `4bad1d769b8b4fe4...` |
| fractional-seed | filter/fibers | 20x12 | 1.6180339887 | 0.3 | `c2307cf247e38db9...` |
| tiny-fractional-seed | filter/fibers | 20x12 | 0.0001 | 0.3 | `8fdf3db29d7fb27a...` |
| huge-seed | filter/fibers | 20x12 | 123456789012 | 0.3 | `df4f5ca215ced01c...` |
| zero-density | filter/fibers | 24x16 | 5 | 0 | `ba7904267efbb615...` |
| large-density | filter/fibers | 24x16 | 5 | 5 | `fd88ea74c17d3871...` |
| sweep-a | filter/fibers | 11x23 | 13 | 0.7 | `5d8bb85a29f9e07d...` |
| sweep-b | filter/fibers | 40x40 | 99 | 0.2 | `6ce487a66e0290c7...` |
| default-17x11 | filter/scratches | 17x11 | 1 | 1 | `7d827426e4910f93...` |
| tiny-1x1 | filter/scratches | 1x1 | 1 | 1 | `5f4a53a54a552d71...` |
| tiny-2x2 | filter/scratches | 2x2 | 3 | 0.01 | `8d22dc482ca823e4...` |
| wide-33x9 | filter/scratches | 33x9 | 7 | 0.5 | `8f6fa06dae8e13d4...` |
| tall-9x33 | filter/scratches | 9x33 | 7 | 0.5 | `b042b7f9192f4e87...` |
| moderate-64x48 | filter/scratches | 64x48 | 42 | 1 | `9026cc6ccadab292...` |
| falsy-seed-zero | filter/scratches | 16x16 | 0 | 1 | `22e583b8ad934614...` |
| falsy-seed-nan | filter/scratches | 16x16 | NaN | 1 | `22e583b8ad934614...` |
| negative-seed | filter/scratches | 20x12 | -5 | 0.3 | `0bbcf5c74e462393...` |
| fractional-seed | filter/scratches | 20x12 | 1.6180339887 | 0.3 | `e9b723fbe76dca2a...` |
| tiny-fractional-seed | filter/scratches | 20x12 | 0.0001 | 0.3 | `cf08e74cd7b0b9f1...` |
| huge-seed | filter/scratches | 20x12 | 123456789012 | 0.3 | `cffe99d6c6acbb13...` |
| zero-density | filter/scratches | 24x16 | 5 | 0 | `108497d06b6527ce...` |
| large-density | filter/scratches | 24x16 | 5 | 5 | `3b8add6e009dfd9b...` |
| sweep-a | filter/scratches | 11x23 | 13 | 0.7 | `2cfaa2db5dab3861...` |
| sweep-b | filter/scratches | 40x40 | 99 | 0.2 | `5711252483fb7f68...` |
| default-17x11 | filter/strayHair | 17x11 | 1 | 1 | `edd84973556d32d5...` |
| tiny-1x1 | filter/strayHair | 1x1 | 1 | 1 | `529d1a93eb68c327...` |
| tiny-2x2 | filter/strayHair | 2x2 | 3 | 0.01 | `d441f49d0c83f541...` |
| wide-33x9 | filter/strayHair | 33x9 | 7 | 0.5 | `3db17c0f9a762c31...` |
| tall-9x33 | filter/strayHair | 9x33 | 7 | 0.5 | `20f6ef58e6ff55c2...` |
| moderate-64x48 | filter/strayHair | 64x48 | 42 | 1 | `2f89e55708b00b70...` |
| falsy-seed-zero | filter/strayHair | 16x16 | 0 | 1 | `bb2b8f46ada71987...` |
| falsy-seed-nan | filter/strayHair | 16x16 | NaN | 1 | `bb2b8f46ada71987...` |
| negative-seed | filter/strayHair | 20x12 | -5 | 0.3 | `c204f3ae1d5ae1c5...` |
| fractional-seed | filter/strayHair | 20x12 | 1.6180339887 | 0.3 | `ea9d068e2b623858...` |
| tiny-fractional-seed | filter/strayHair | 20x12 | 0.0001 | 0.3 | `3b83a66d54cfa54f...` |
| huge-seed | filter/strayHair | 20x12 | 123456789012 | 0.3 | `35ea24c3efc44424...` |
| zero-density | filter/strayHair | 24x16 | 5 | 0 | `3c78fa2d530ea5a1...` |
| large-density | filter/strayHair | 24x16 | 5 | 5 | `3c78fa2d530ea5a1...` |
| sweep-a | filter/strayHair | 11x23 | 13 | 0.7 | `7695e2b7c47af6af...` |
| sweep-b | filter/strayHair | 40x40 | 99 | 0.2 | `41d22a4dd4e150e8...` |

