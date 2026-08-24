# Task 26 Smooth Edge LUMA_WEIGHTS public-canonical oracle report

Cases: **8**  
Mutations and controls: **11**

Public dispatch is the exact canonical factory and has no adapter. Every case repeats byte-identically, preserves its input, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.

## Cases

| Case | Size | smoothType | Threshold bits | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | ---: | --- | --- | --- |
| pass-through-modular-tile | 8x5 | 0 | 0x3e6b851f | `ffaf80acb8db7b255eaf329399e44b5a562a19e82125b19317d436bb07f8fa4b` | `b3fd913a3458127e8f606cdcdd40aa5204835b0219b6feb1e749993a7bd9a8ad` |
| edge-modular-type1 | 9x6 | 1 | 0x3e3851ec | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| edge-modular-type2-same-branch | 9x6 | 2 | 0x3e3851ec | `af1d4152b362120f0fa863602de3a5a01e4bf59f393f37058e879d8498909469` | `475820bc2a2eaeffb822f1506b7afffcd4aa8cd9eb4a9c442f27f9eab1c9d2b5` |
| threshold-one-ulp-below | 5x5 | 1 | 0x3dfc0d11 | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold-exact | 5x5 | 1 | 0x3dfc0d12 | `c70f0d59488dda2bde1da6463690f63f9d85f22a7ee827dd1bba3f93829adb04` | `66517cf5c7e0d30c1671d3f8d13eea7ab9a83748f82ef4780817cf4b0f30f098` |
| threshold-one-ulp-above | 5x5 | 1 | 0x3dfc0d13 | `2173d5ef284d8e03867fa476c6cdc4c7ca81948e5244655b7f920b9bbbb84f39` | `7efb4ab7603eea21de958ddfbafc97719d99c62e2c1a63ea1153bfea396dc8a1` |
| single-pixel-clamped-neighbors | 1x1 | 1 | 0x38d1b717 | `7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e` | `e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332` |
| asymmetric-cardinal-lanes | 5x5 | 1 | 0x3df5c28f | `ffc9c67a9151cfb6b03cb934d9ffb3704a29069cc65e9f3ab91f4535d18fd2ee` | `861c828b629ccf0413f0f4e23f345240720a961d7ca093563523178e30856fdb` |

## Mutation and control results

| Mutation/control | Hazard | Expectation | Divergent cases | Max changed F32 lanes | Max changed RGBA8 bytes |
| --- | --- | --- | ---: | ---: | ---: |
| red-value-0.299-to-0.3 | value/lane-0 | diverge | 1/8 | 6 | 6 |
| green-value-0.587-to-0.6 | value/lane-1 | diverge | 3/8 | 6 | 6 |
| blue-value-0.114-to-0.2 | value/lane-2 | diverge | 4/8 | 6 | 6 |
| red-blue-lane-order-swap | lane-order | diverge | 5/8 | 16 | 16 |
| vec3-type-to-scalar | type/arity | diverge | 7/8 | 50 | 50 |
| vec3-to-vec4-extra-lane-control | type/arity-observably-inert | identity-structural-reject | 0/8 | 0 | 0 |
| const-storage-to-cross-call-mutation | storage/write/lifetime | diverge | 5/8 | 23 | 23 |
| resolved-read-replaced-by-rgb-self-dot | read/site/parent | diverge | 4/8 | 22 | 22 |
| helper-local-exact-f32-materialization | authorized-ownership/materialization | identity-authorized-lowering | 0/8 | 0 | 0 |
| helper-local-source-double-array | materialization/F32-boundary | diverge | 2/8 | 6 | 6 |
| main-owned-exact-f32-vector-control | wrong-owner-observably-inert | identity-structural-reject | 0/8 | 0 | 0 |

The exact helper-local Float32 materialization is byte-identical and is the only authorized ownership lowering. The vec4-extra-lane and main-owned controls are also observably identical, proving output parity cannot replace structural type/arity/owner authentication. Source-double helper materialization diverges at the frozen F32 threshold boundary.

