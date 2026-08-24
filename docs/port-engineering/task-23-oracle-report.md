# Task 23 six-key public-canonical oracle report

Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`  
Cases: **19**  
Mutations: **12**

Every public factory was runtime-proved identical to its pinned canonical factory; no selected key has an adapter entry. All cases repeat byte-identically with immutable input and finite output.

## Programs

| Key | Factory | Global bound | Loop charge | Pre -> post function hash | Interface hash |
| --- | --- | --- | ---: | --- | --- |
| `filter/bloom:ntapGather` | `canonicalFactory23` | `MAX_TAPS@8=64` | 64 | `a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163` -> `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` | `b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8` |
| `filter/directionalBlur:directionalBlur` | `canonicalFactory47` | `N@6=32` | 32 | `8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa` -> `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` | `3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858` |
| `filter/spinBlur:spinBlur` | `canonicalFactory145` | `N@9=32` | 32 | `f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8` -> `974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51` | `4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723` |
| `filter/strokes:stkSmear` | `canonicalFactory155` | `MAX_TAPS@8=24` | 72 | `5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9` -> `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` | `8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef` |
| `filter/vaseline:upsample` | `canonicalFactory170` | `TAP_COUNT@8=32` | 32 | `9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374` -> `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` | `fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e` |
| `filter/wind:wind` | `canonicalFactory177` | `MAX_STEPS@8=128` | 128 | `214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d` -> `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` | `455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85` |

## Cases

| Key / case | Size | Output F32 SHA-256 | RGBA8 SHA-256 | Changed lanes |
| --- | --- | --- | --- | ---: |
| `filter/bloom:ntapGather` / bloom-one-tap-zero-radius | 11x7 | `d8bad1a2b5985a0aca4b2f38784960af56d3086b632c1102e0e44aa9dd700cc6` | `33dc54a5807ab8f07dfe1c28e07ae47810b6bb9d68e35f5495ed22cfdaeddf38` | 74 |
| `filter/bloom:ntapGather` / bloom-seven-taps-tiled | 11x7 | `3a78a002b48288114cae835018bc89df13c80d4fae6631f5816d1670ebe11939` | `4954e6734cd197c8f205e0eb230daa676db0886e1e5ff5525e382884b7970ff6` | 305 |
| `filter/bloom:ntapGather` / bloom-max-taps | 11x7 | `fca0a971b81cbf542f1083bcde6cc970b09f04f367888f4a7412ce327547d2e4` | `55bc0f334ac3b8313a5a01900769d309fdecf70b43636b91384d1e2470780e49` | 305 |
| `filter/directionalBlur:directionalBlur` / directional-zero-distance | 11x7 | `e326961f52b1f78facce16e21f4a2c4d03ea712811be91f38404bb755ae0910a` | `447bfb78702aca0f4967c3f998e3a91688f3dd650b51a4e1d2fe0c8e6476d5e0` | 234 |
| `filter/directionalBlur:directionalBlur` / directional-positive-angle | 11x7 | `9c653e16170894e23b1e58d77d63270e952bbd6b27982b0297b67d4f3b33bc54` | `27c5bfd69d6cb1377a3255322d8b07c36c082f64cb498c4c193be9ec9a438333` | 308 |
| `filter/directionalBlur:directionalBlur` / directional-negative-angle-wide | 9x13 | `b07c7d0b6be5cfce0cc26d4654ad7842a1280a34caac5305e2c058514faf9b99` | `6ef88dd589a2cba9277457f4ee68decf5b2e13ff9e390521be4206bc27d0f9c3` | 468 |
| `filter/spinBlur:spinBlur` / spin-zero-amount-centered | 11x7 | `e326961f52b1f78facce16e21f4a2c4d03ea712811be91f38404bb755ae0910a` | `447bfb78702aca0f4967c3f998e3a91688f3dd650b51a4e1d2fe0c8e6476d5e0` | 234 |
| `filter/spinBlur:spinBlur` / spin-positive-tiled-offcenter | 11x7 | `2d757900af1b181228524ce588fe22bcf6ffa133b3375a56cac667f9f70ce124` | `c1804d12be653ffee800c7790e5cf1291cb122f960dcab4e3bf6b7a952fada30` | 307 |
| `filter/spinBlur:spinBlur` / spin-negative-portrait | 9x13 | `f1288bf89e80f24a7fe72b00d6d8978163d884fae36f63639aa88cbc0bbe1ef1` | `50bb149de75acd1994ecd68a692b423791a455ad8ab4defdacfa4c9e8a27f85e` | 468 |
| `filter/strokes:stkSmear` / strokes-short-low-balance | 17x13 | `ff124225064ed241b397649ca6624e57b3c66a871c6128ede19a0354e1443d08` | `e2480b24cb15b066368e55a2955840c685ba21761f4502d393c028858862b47a` | 663 |
| `filter/strokes:stkSmear` / strokes-long-high-balance-tiled | 17x13 | `583c5be9cd435f813f503ef05ae11d6c4d1b2ad14b59d5568ec6344c090bd784` | `aacc2091593c4135b919b1075a754d9ec5d23cfac42ebf6054bef9920e5e014b` | 663 |
| `filter/strokes:stkSmear` / strokes-long-low-balance | 17x13 | `fa624645ccad58eef5b5cd262e13cddb3c8e3914266ae8f8b842f8110811b5a4` | `e35243670cfa194abd1a0f9c746850f8e56a40f8e34fefc0e0a569328a4ef6a1` | 642 |
| `filter/vaseline:upsample` / vaseline-alpha-zero-copy | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/vaseline:upsample` / vaseline-mid-alpha-tiled | 11x7 | `50b1c88e9553fd64eb1e1046451b2baa073e646ec04f8d2f91bbe6ce39d22e08` | `ca62da554643982645425e88764c4b0f2c523f22c5fa878967e78347f0b3ce61` | 228 |
| `filter/vaseline:upsample` / vaseline-alpha-clamped-high | 9x13 | `30a1cd6db1a99acad1d136a95026b5925234620d1585ffc55436d814d39b868d` | `d4a73bf8d550e0af758813c2445e7a1b39fdb070a81a9990011315e5b6d3251f` | 348 |
| `filter/wind:wind` / wind-strength-zero-copy | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/wind:wind` / wind-tiny-positive-no-march | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/wind:wind` / wind-left-medium-tiled | 11x7 | `790daf758cea1a795359037e8dd8269944c679f3d6adc4f89efcdd1358778a5f` | `55fd1cca149dd565901d7adbba336dc7ba215c65b1f2159c2b0a93823b569888` | 60 |
| `filter/wind:wind` / wind-right-full-strength | 13x9 | `c7fa5be06406852310e48ae0679414b1b04cc2baa22fec3d8c6d2719d949f968` | `54a6bd0f5988b108bcc825a0dacbe922e86de45e06586a23c3953a8b8930d028` | 202 |

## Mutation sensitivity

| Key / mutation | Required divergent cases | Maximum changed F32 lanes | Maximum changed RGBA8 bytes |
| --- | --- | ---: | ---: |
| `filter/bloom:ntapGather` / bloom-global-bound-64-to-8 | bloom-max-taps | 231 | 227 |
| `filter/bloom:ntapGather` / bloom-tap-count-forced-one | bloom-seven-taps-tiled, bloom-max-taps | 231 | 231 |
| `filter/directionalBlur:directionalBlur` / directional-global-bound-32-to-8 | directional-positive-angle, directional-negative-angle-wide | 468 | 466 |
| `filter/directionalBlur:directionalBlur` / directional-jitter-disabled | directional-positive-angle, directional-negative-angle-wide | 424 | 411 |
| `filter/spinBlur:spinBlur` / spin-global-bound-32-to-8 | spin-positive-tiled-offcenter, spin-negative-portrait | 468 | 453 |
| `filter/spinBlur:spinBlur` / spin-jitter-disabled | spin-positive-tiled-offcenter, spin-negative-portrait | 415 | 401 |
| `filter/strokes:stkSmear` / strokes-global-bound-24-to-8 | strokes-long-high-balance-tiled, strokes-long-low-balance | 663 | 570 |
| `filter/strokes:stkSmear` / strokes-field-selection-forced-135 | strokes-short-low-balance, strokes-long-low-balance | 657 | 649 |
| `filter/vaseline:upsample` / vaseline-global-bound-32-to-8 | vaseline-mid-alpha-tiled, vaseline-alpha-clamped-high | 348 | 318 |
| `filter/vaseline:upsample` / vaseline-edge-mask-forced-zero | vaseline-mid-alpha-tiled, vaseline-alpha-clamped-high | 348 | 340 |
| `filter/wind:wind` / wind-global-bound-128-to-16 | wind-left-medium-tiled, wind-right-full-strength | 101 | 100 |
| `filter/wind:wind` / wind-direction-forced-right | wind-left-medium-tiled | 149 | 147 |

## Held boundary

`filter/reindex:nmReindexStats` is structurally adjacent but uses the public `reindexStatsFactory` eager-F32 adapter. It is not represented by these direct-canonical outputs and remains excluded.

