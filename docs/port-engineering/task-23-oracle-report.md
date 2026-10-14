# Task 23 six-key public-canonical oracle report

Corpus revision: `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`
Cases: **19**  
Mutations: **12**

Every public factory was runtime-proved identical to its pinned canonical factory; no selected key has an adapter entry. All cases repeat byte-identically with immutable input and finite output.

## Programs

| Key | Factory | Global bound | Loop charge | Pre -> post function hash | Interface hash |
| --- | --- | --- | ---: | --- | --- |
| `filter/bloom:ntapGather` | `canonicalFactory22` | `MAX_TAPS@8=64` | 64 | `a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163` -> `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` | `b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8` |
| `filter/directionalBlur:directionalBlur` | `canonicalFactory45` | `N@6=32` | 32 | `8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa` -> `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` | `3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858` |
| `filter/spinBlur:spinBlur` | `canonicalFactory142` | `N@9=32` | 32 | `d99d37c65d0e13b943da42d43913c27e60e969c974729378ceb4f889ce01b3d4` -> `3739290914b415422318656c5809fe10566698f72cf4cb3a483cbed8233f1fa4` | `c37de59496abc0f87e9f304c31bcbd71695b720c40b3bbaeacbc9ccc4aa9d561` |
| `filter/strokes:stkSmear` | `canonicalFactory152` | `MAX_TAPS@8=24` | 72 | `5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9` -> `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` | `8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef` |
| `filter/vaseline:upsample` | `canonicalFactory167` | `TAP_COUNT@8=32` | 32 | `9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374` -> `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` | `fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e` |
| `filter/wind:wind` | `canonicalFactory174` | `MAX_STEPS@8=128` | 128 | `214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d` -> `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` | `455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85` |

## Cases

| Key / case | Size | Output F32 SHA-256 | RGBA8 SHA-256 | Changed lanes |
| --- | --- | --- | --- | ---: |
| `filter/bloom:ntapGather` / bloom-one-tap-zero-radius | 11x7 | `d8bad1a2b5985a0aca4b2f38784960af56d3086b632c1102e0e44aa9dd700cc6` | `33dc54a5807ab8f07dfe1c28e07ae47810b6bb9d68e35f5495ed22cfdaeddf38` | 74 |
| `filter/bloom:ntapGather` / bloom-seven-taps-tiled | 11x7 | `3a78a002b48288114cae835018bc89df13c80d4fae6631f5816d1670ebe11939` | `4954e6734cd197c8f205e0eb230daa676db0886e1e5ff5525e382884b7970ff6` | 305 |
| `filter/bloom:ntapGather` / bloom-max-taps | 11x7 | `fca0a971b81cbf542f1083bcde6cc970b09f04f367888f4a7412ce327547d2e4` | `55bc0f334ac3b8313a5a01900769d309fdecf70b43636b91384d1e2470780e49` | 305 |
| `filter/directionalBlur:directionalBlur` / directional-zero-distance | 11x7 | `e326961f52b1f78facce16e21f4a2c4d03ea712811be91f38404bb755ae0910a` | `447bfb78702aca0f4967c3f998e3a91688f3dd650b51a4e1d2fe0c8e6476d5e0` | 234 |
| `filter/directionalBlur:directionalBlur` / directional-positive-angle | 11x7 | `9c653e16170894e23b1e58d77d63270e952bbd6b27982b0297b67d4f3b33bc54` | `27c5bfd69d6cb1377a3255322d8b07c36c082f64cb498c4c193be9ec9a438333` | 308 |
| `filter/directionalBlur:directionalBlur` / directional-negative-angle-wide | 9x13 | `a6f637d11c5f594beafce91b71ddee9bc3386e22b45a9435607f139a8d15ad05` | `f7b981084e886fb04195c1ee3d5bb13a48f56524ad9055f6b95768a9dfb7b19f` | 468 |
| `filter/spinBlur:spinBlur` / spin-zero-amount-centered | 11x7 | `e326961f52b1f78facce16e21f4a2c4d03ea712811be91f38404bb755ae0910a` | `447bfb78702aca0f4967c3f998e3a91688f3dd650b51a4e1d2fe0c8e6476d5e0` | 234 |
| `filter/spinBlur:spinBlur` / spin-positive-tiled-offcenter | 11x7 | `2d757900af1b181228524ce588fe22bcf6ffa133b3375a56cac667f9f70ce124` | `c1804d12be653ffee800c7790e5cf1291cb122f960dcab4e3bf6b7a952fada30` | 307 |
| `filter/spinBlur:spinBlur` / spin-negative-portrait | 9x13 | `f1288bf89e80f24a7fe72b00d6d8978163d884fae36f63639aa88cbc0bbe1ef1` | `50bb149de75acd1994ecd68a692b423791a455ad8ab4defdacfa4c9e8a27f85e` | 468 |
| `filter/strokes:stkSmear` / strokes-short-low-balance | 17x13 | `9de17b56ee236c2b808c4f6ecc81c618a30c704b82b9cc31369acd361511d39e` | `f533dbcb847d0ebc47cfc374f910760c7681524192b69675f017efa12d67b1e7` | 663 |
| `filter/strokes:stkSmear` / strokes-long-high-balance-tiled | 17x13 | `24000eef8b51dd4f528eba4b16b58418187723ca4c0468cd7dedd31cd98fe927` | `2961ab4382160479a4fcc6471b2aeb950560df7b7d8fcbb638dcd14664dd05a3` | 663 |
| `filter/strokes:stkSmear` / strokes-long-low-balance | 17x13 | `525ea125b28ef809a2ae14c5037c1572a564076ae56f728beb9d6c8a4ab22f43` | `d402486896fd76c8a5e83bc569836d08a6d2e30a51ed7497bfcd10edc77eb794` | 648 |
| `filter/vaseline:upsample` / vaseline-alpha-zero-copy | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/vaseline:upsample` / vaseline-mid-alpha-tiled | 11x7 | `50b1c88e9553fd64eb1e1046451b2baa073e646ec04f8d2f91bbe6ce39d22e08` | `ca62da554643982645425e88764c4b0f2c523f22c5fa878967e78347f0b3ce61` | 228 |
| `filter/vaseline:upsample` / vaseline-alpha-clamped-high | 9x13 | `30a1cd6db1a99acad1d136a95026b5925234620d1585ffc55436d814d39b868d` | `d4a73bf8d550e0af758813c2445e7a1b39fdb070a81a9990011315e5b6d3251f` | 348 |
| `filter/wind:wind` / wind-strength-zero-copy | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/wind:wind` / wind-tiny-positive-no-march | 11x7 | `3b956defac9db931c6a7b4b89c3d2496605c5ebaaa873368b3883f9775a8ec43` | `a550154d87fb9c52ce2d8b06aa6beea3928718fe79fbbe10626ebea9e17a27d2` | 0 |
| `filter/wind:wind` / wind-left-medium-tiled | 11x7 | `524d7f4ef225d9e3a5dcb586cb9743fa28d0c2e4b8cf9ad1528f66d4e6ba486c` | `55fd1cca149dd565901d7adbba336dc7ba215c65b1f2159c2b0a93823b569888` | 60 |
| `filter/wind:wind` / wind-right-full-strength | 13x9 | `96d7b19fb9eba8c3edddbeaecddc3e8c0b2fe8498eba3476b868508a16816f9d` | `54a6bd0f5988b108bcc825a0dacbe922e86de45e06586a23c3953a8b8930d028` | 202 |

## Mutation sensitivity

| Key / mutation | Required divergent cases | Maximum changed F32 lanes | Maximum changed RGBA8 bytes |
| --- | --- | ---: | ---: |
| `filter/bloom:ntapGather` / bloom-global-bound-64-to-8 | bloom-max-taps | 231 | 227 |
| `filter/bloom:ntapGather` / bloom-tap-count-forced-one | bloom-seven-taps-tiled, bloom-max-taps | 231 | 231 |
| `filter/directionalBlur:directionalBlur` / directional-global-bound-32-to-8 | directional-positive-angle, directional-negative-angle-wide | 468 | 466 |
| `filter/directionalBlur:directionalBlur` / directional-jitter-disabled | directional-positive-angle, directional-negative-angle-wide | 424 | 411 |
| `filter/spinBlur:spinBlur` / spin-global-bound-32-to-8 | spin-positive-tiled-offcenter, spin-negative-portrait | 468 | 453 |
| `filter/spinBlur:spinBlur` / spin-jitter-disabled | spin-positive-tiled-offcenter, spin-negative-portrait | 415 | 401 |
| `filter/strokes:stkSmear` / strokes-global-bound-24-to-8 | strokes-long-high-balance-tiled, strokes-long-low-balance | 663 | 572 |
| `filter/strokes:stkSmear` / strokes-field-selection-forced-135 | strokes-short-low-balance, strokes-long-low-balance | 657 | 650 |
| `filter/vaseline:upsample` / vaseline-global-bound-32-to-8 | vaseline-mid-alpha-tiled, vaseline-alpha-clamped-high | 348 | 318 |
| `filter/vaseline:upsample` / vaseline-edge-mask-forced-zero | vaseline-mid-alpha-tiled, vaseline-alpha-clamped-high | 348 | 340 |
| `filter/wind:wind` / wind-global-bound-128-to-16 | wind-left-medium-tiled, wind-right-full-strength | 101 | 100 |
| `filter/wind:wind` / wind-direction-forced-right | wind-left-medium-tiled | 149 | 147 |

## Held boundary

`filter/reindex:nmReindexStats` is structurally adjacent but uses the public `reindexStatsFactory` eager-F32 adapter. It is not represented by these direct-canonical outputs and remains excluded.

