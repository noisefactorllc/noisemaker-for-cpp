# Task 25 literal vec3 lane public-canonical oracle report

Cases: **6**  
Authenticated source sites: **11**  
One-site wrong-lane mutations: **11**

Both public dispatch entries are the exact canonical factory objects and have no adapters. Every case repeats byte-identically, preserves its input, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.

## Cases

| Case | Program | Size | Tile / full | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| lens-chromatic-add-static | classicNoisedeck/lensDistortion:lensDistortion | 11x7 | 0,0 / 11,7 | `40ec6e6bcca21c55b0abe81eca5760b2e623aad76678b49b070d350d0fe49948` | `de4b64895586ce7dc92352820b5c64d5660dc1d722bd8c5392e42568385ec4b8` |
| lens-chromatic-alpha-modulated | classicNoisedeck/lensDistortion:lensDistortion | 10x8 | 0,0 / 10,8 | `3c4ff034284a714a545a35106c98e7d93398fb800f7bee2dbccffb08592a5e61` | `18b8e022320da7b278ae2935b8602f50ebcf30cfc1e5eb058e932f8d05666ada` |
| lens-prismatic-add-static | classicNoisedeck/lensDistortion:lensDistortion | 9x9 | 0,0 / 9,9 | `0ed06880cce85cebb134fbc0cb2b5710a4a3e08dc336512e31cbaf2a5ec77688` | `204fe8f73e191091c231f159d147cb10df17b9bc88abc44c6baa75da7684b05e` |
| lens-prismatic-alpha-modulated | classicNoisedeck/lensDistortion:lensDistortion | 12x6 | 0,0 / 12,6 | `7fe6ac9ba3bf66f5f3f747f635b6ce5bd9d7e1d184678a74ba1d69cc14b18b76` | `4b8ffb755c45fa8b37e686ff71fd61f66c120eeaf2644b6d871e01b6a728521b` |
| prism-static-origin-tile | filter/prismaticAberration:prismaticAberration | 10x7 | 0,0 / 10,7 | `daad9591d01855520a052fd2d89ed2e9ed32da2d93421a041e40d58b5389daff` | `5f73c9a1151a312569107b68abd705555f7d2c5540c8e3ea44abd7891a9a3640` |
| prism-modulated-offset-tile | filter/prismaticAberration:prismaticAberration | 9x6 | 4,3 / 17,13 | `dbc929af7ba49e768bd39a0188e0f9b9426581ba564c856e6289531304c8b216` | `5f141b94b43d85418de325137173a181d705f50574f4d1ca78e01972a1044447` |

## Exact-site mutation sensitivity

| Mutation | Span / role | Source lane -> wrong lane | Divergent active cases | Max changed F32 lanes | Max changed RGBA8 bytes |
| --- | --- | --- | ---: | ---: | ---: |
| lens-236-write-lane0-to-lane1 | 236:9-236:15 / direct-= lvalue | 0 -> 1 | 2/4 | 20 | 20 |
| lens-236-first-read-lane0-to-lane1 | 236:24-236:30 / RHS read | 0 -> 1 | 2/4 | 24 | 24 |
| lens-236-second-read-lane0-to-lane2 | 236:65-236:71 / RHS read | 0 -> 2 | 2/4 | 20 | 20 |
| lens-237-write-lane1-to-lane2 | 237:9-237:15 / direct-= lvalue | 1 -> 2 | 2/4 | 231 | 231 |
| lens-247-write-lane0-to-lane1 | 247:9-247:15 / direct-= lvalue | 0 -> 1 | 2/4 | 180 | 179 |
| lens-247-read-lane0-to-lane1 | 247:26-247:32 / RHS read | 0 -> 1 | 2/4 | 175 | 172 |
| lens-248-write-lane1-to-lane2 | 248:9-248:15 / direct-= lvalue | 1 -> 2 | 2/4 | 216 | 215 |
| lens-260-read-splat-lane2-to-lane1 | 260:46-260:52 / sole vec3 splat-input read | 2 -> 1 | 2/4 | 206 | 206 |
| prism-131-write-lane0-to-lane1 | 131:5-131:11 / direct-= lvalue | 0 -> 1 | 2/2 | 122 | 119 |
| prism-131-read-lane0-to-lane1 | 131:22-131:28 / RHS read | 0 -> 1 | 2/2 | 133 | 131 |
| prism-132-write-lane1-to-lane2 | 132:5-132:11 / direct-= lvalue | 1 -> 2 | 2/2 | 158 | 157 |

Each mutation changes exactly one authenticated source index role. The Lens line-260 scalar splat is one source read even though the canonical JavaScript factory expands it to three `hsv[2]` reads; its mutation changes those three generated occurrences together. These controls do not authorize generic or dynamic vector indexing.

