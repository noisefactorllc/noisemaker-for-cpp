# Task 28 Rotate mat2 return public-canonical oracle report

Public render cases: **6**  
Public factory mutations: **5**  
Direct matrix inputs/modes: **6 / 6**

The public dispatch is the exact canonical factory and has no adapter. Every case uses a non-square quadrant-marked input, repeats byte-identically, preserves input bytes, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.

## Public render cases

| Case | Size | Wrap / speed | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- | --- |
| mirror-zero-stationary | 11x7 | 0 / 0 | `3709622bba358109b11d4db19416b92ee536566f831cf0422bf39fab80372304` | `fdd0aaa3a244b6f82bf8cd31d4f721a24a0df27bc8c9c2628df9ec8297e45587` |
| repeat-quarter-turn-stationary | 9x6 | 1 / 0 | `de121a78dbd9dca3da1a045d9745471fd78f259e3299ada738467c2137683d45` | `536341787c2e5ad102b1810fbd5ca8068072ad9a0773f0da59edde5900af1ad7` |
| clamp-negative-oblique-stationary | 12x7 | 2 / 0 | `481e60cd62fd8a220c64bebd9734833db3ce3fee9844ef50b6f03007cb2497f4` | `a89fbf2153c7bfb4f0ea2f0fabcc830e9e60b15f16c389a73bbfd7f498f55a10` |
| mirror-positive-animation | 10x6 | 0 / 2 | `544f50f37cd84a98bb0b935e3fd05fed47a49fc4552171f3293fad060d829190` | `37fdf71d303dcc97f4ba0eb6acf2720da1195974e8689981e653a41d501d20b9` |
| repeat-negative-animation | 13x8 | 1 / -3 | `9e9528a344e390e6503da8731f2b105d422585ed37dd5ab14675a7d5f8c0e8d4` | `9d586478e50550322e3ec8eef0b14bd4efff63b43fb120bad77a8267740f25e1` |
| clamp-large-angle-animation | 8x5 | 2 / 4 | `ecaa74dc28582aa09cc04a51a64e23e3e2a1304f932b0e732f7feb57cc52b7cb` | `92aac1693d164fe1d3c8568a40a1b5c95c6fc46d15234fad379262d222ce8067` |

## Public mutation sensitivity

| Mutation | Hazard | Divergent cases |
| --- | --- | ---: |
| transpose-constructor | constructor-lane-order | 5/6 |
| quarter-turn-constructor | constructor-child-identity | 6/6 |
| diagonal-constructor | constructor-arity-semantics | 5/6 |
| row-major-multiply | matrix-layout | 5/6 |
| helper-local-return | return-expression-shape | 0/6 |

The helper-local-return control is value-identical but structurally distinct. Every value/layout mutation diverges in at least one case.

## Direct matrix-value contract

| Angle/vector | Exact lanes | Exact product |
| --- | --- | --- |
| 0; 1.25, -0.75 | 0x3f800000, 0x80000000, 0x00000000, 0x3f800000 | 0x3fa00000, 0xbf400000 |
| 0.5235987901687622; 1, 2 | 0x3f5db3d7, 0xbf000000, 0x3f000000, 0x3f5db3d7 | 0x3feed9ec, 0x3f9db3d7 |
| -1.5707963705062866; -2.5, 0.5 | 0xb33bbd2e, 0x3f800000, 0xbf800000, 0xb33bbd2e | 0xbefffffc, 0xc0200000 |
| 3.1415927410125732; 0.125, -3 | 0xbf800000, 0x33bbbd2e, 0xb3bbbd2e, 0xbf800000 | 0xbdffffdd, 0x40400000 |
| 0.699999988079071; 7.25, -1.5 | 0x3f43ccb3, 0xbf24eb73, 0x3f24eb73, 0x3f43ccb3 | 0x4092855d, 0xc0ba2bc2 |
| -2.299999952316284; -0.375, 4.5 | 0xbf2a9110, 0x3f3ee68a, 0xbf3ee68a, 0xbf2a9110 | 0xc046c5c2, 0xc051c8cf |

The native suite must execute all six named switch modes, authenticate both numeric mode IDs and names, record distinct return-shape witnesses, reject an invalid enum, and compare every matrix lane and product bit pattern. Python must transcribe and tamper-check every executable case and mode-table field.

