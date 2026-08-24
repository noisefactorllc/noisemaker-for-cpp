# Task 27 Perlin scalar uint XOR public-canonical oracle report

Public render cases: **8**  
Unreachable mutation controls: **4**  
Direct unsigned-word cases: **12**

The public dispatch is the exact canonical factory and has no adapter. Every default `DIMENSIONS=2` case repeats byte-identically and records finite full F32/RGBA8 output hashes plus five probes. The two scalar XOR sites live only in unreachable `hash3`, so public output intentionally cannot authenticate them.

## Public render cases

| Case | Size | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- |
| mono-default-shape | 8x5 | `b018f8cc1fdda9f62e8bf4c98b348cb2ab30d06f7d7431f085fada7e846d5370` | `5e2f72a42f80ea0c4f8d817158bea3192c765447fb7163332762600b7ae30947` |
| rgb-four-octaves | 7x6 | `2fffa3f23b68dd43c770264906426da052343f893116fa083cbb430862ada8e0` | `94a046751fea8a2c23f1832e05cad33037b586c74f2605520a1bf62e8ef86f69` |
| ridged-six-octaves | 6x7 | `3d387b3e9cdb11992f2d5534161a0fe69fbb407d69647b9bddf7a6bf493463f2` | `54aed294f85f2c315738ce0af00de16f207e67185da8a469767dbd5c8b78aeae` |
| single-domain-warp | 9x5 | `25965f069dbd1511129c5e0ffc3a1a7e17c9f0158e113c0ec43c06a010b0941a` | `52bef32bb985f21f8f6502352359bfa37f03dd3bd48c59a60861696f42301bf3` |
| four-domain-warps-ridged | 5x8 | `5ee347f46136546e8a7eaf49930534a6e9f06613f428e3be90b227e9eb9f4242` | `b9f70845a761d8fc419d699931b081955eb49f2df457ea5d4edc769e706d5a22` |
| tiled-full-resolution | 6x4 | `b7e8f598b5bfa125f415c3f1f48639714bfb09ddb15d8c15b3ed90e837682112` | `41c6ba39021f77993884418c097f25b138686797768a6b4f801856edfb126779` |
| speed-zero-time-inert | 4x4 | `333db2d83ff72baa64118005b283482855237626d94bf251f4b341e08a52b11e` | `2a500a663087433951e28b012b09495546d1cccd016aa0d0e1fa75e330573478` |
| full-resolution-fallback | 5x3 | `0b0cc11694cc7fdc5eeed2e0354b8382c94cf3d23d66e47c03477ee0a885d873` | `d617a8636255b0f49ed91dd82b255867fa698497c2286ba707839e98d721eac7` |

## Unreachable mutation controls

| Mutation | Hazard | Default cases changed |
| --- | --- | ---: |
| outer-xor-to-or | outer-operator | 0/8 |
| inner-xor-to-or | inner-operator | 0/8 |
| left-tree-to-right-tree | parent/associativity | 0/8 |
| both-xor-to-add | operator/type-semantics | 0/8 |

All four changed factories are byte-identical on all default cases. This is a required reachability control, not semantic acceptance.

## Direct unsigned-word contract

| Inputs (hex) | Inner XOR | Result XOR | Source unsigned F32 bits | Canonical JS signed F32 bits |
| --- | --- | --- | --- | --- |
| 0x00000000, 0x00000000, 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 | 0x00000000 |
| 0xffffffff, 0x00000000, 0x00000000 | 0xffffffff | 0xffffffff | 0x4f800000 | 0xbf800000 |
| 0x80000000, 0x00000000, 0x00000000 | 0x80000000 | 0x80000000 | 0x4f000000 | 0xcf000000 |
| 0x7fffffff, 0xffffffff, 0x00000000 | 0x80000000 | 0x80000000 | 0x4f000000 | 0xcf000000 |
| 0xaaaaaaaa, 0x55555555, 0xffffffff | 0xffffffff | 0x00000000 | 0x00000000 | 0x00000000 |
| 0x01234567, 0x89abcdef, 0xfedcba98 | 0x88888888 | 0x76543210 | 0x4eeca864 | 0x4eeca864 |
| 0xdeadbeef, 0xcafebabe, 0x8badf00d | 0x14530451 | 0x9ffef45c | 0x4f1ffef4 | 0xcec00217 |
| 0x00000001, 0x00000002, 0x00000004 | 0x00000003 | 0x00000007 | 0x40e00000 | 0x40e00000 |
| 0x80000000, 0x40000000, 0x20000000 | 0xc0000000 | 0xe0000000 | 0x4f600000 | 0xce000000 |
| 0xffffffff, 0xffffffff, 0x80000000 | 0x00000000 | 0x80000000 | 0x4f000000 | 0xcf000000 |
| 0x13579bdf, 0x2468ace0, 0xf0f0f0f0 | 0x373f373f | 0xc7cfc7cf | 0x4f47cfc8 | 0xce60c0e1 |
| 0x0000ffff, 0xffff0000, 0x00ff00ff | 0xffffffff | 0xff00ff00 | 0x4f7f00ff | 0xcb7f0100 |

The native suite must execute these words through an explicit `std::uint32_t` expression and separately prove the generated `hash3` spelling and exact two-node typed-tree closure. Image equality alone is insufficient; `DIMENSIONS=3` remains unauthorized.

