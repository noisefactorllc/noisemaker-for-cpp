# `filter/wormhole:deposit` scatter-pass oracle report

Ground truth is `runWormholeDeposit` (`src/effects/cpu/wormhole.js:34-76`), imported and called directly -- never reimplemented for golden values. See `provenance.note` for why the transpiled `deposit.frag` kernel is irrelevant to this port.

Total cases: **62** (14 discrimination-focused, 56 sweep-focused, 3 diagnostic/control).

## Provenance

| File | sha256 |
| --- | --- |
| wormhole.js | `45adb569c80897848b84fc4551eaa14a00c62db99db02ecca98d417f9b74d195` |
| texture-format.js | `10af8fd92813c7872eecf51b203c01a4e6ebc79a4c5fa7d38661a12192efbcfe` |
| surface.js | `0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59` |
| scatter-registry.js | `940ed6fe1b27e826330c7b1c49336126e37a39e29176ee335bb50526dc40c4d2` |
| deposit.frag (corpus a024dc3a960cc44af454abc7aebce50456c194e6) | `156401729b935381b38732d8e84ebdbbe185734e642972fa45533c5ce51a083d` (117 bytes) |

Text-surgery self-check: **PASS -- extracted-from-source-text runtime reproduces the real imported runWormholeDeposit byte-for-byte on every case (asserted at build time)**

## pixelStride rounding-order proof (provable no-op, reported honestly)

Math.fround(1024 * stride) === 1024 * Math.fround(stride) for every sampled stride -- storage order is provably unobservable for this multiplier

Checked over 22 sampled stride values; `all_equal: true`. This is the specific case the task brief warns about: an "obvious" storage-order mutation that turns out to be structurally unobservable (1024 is an exact power of two, so round-then-scale equals scale-then-round). It is reported here as a checked non-discriminator rather than silently dropped.

## Mutations

| Mutation | Kind | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| wrap-mirror-clamp-swap | wrap-dispatch | 38 | 36 | 24 | 0 |
| wrap-else-becomes-clamp | wrap-dispatch | 22 | 21 | 40 | 0 |
| source-row-flip-removed | vertex-id-convention | 55 | 55 | 7 | 0 |
| destination-row-flip-removed | vertex-id-convention | 55 | 55 | 7 | 0 |
| weight-formula-linear | accumulation | 62 | 61 | 0 | 0 |
| float16-truncate-skipped | accumulation | 62 | 61 | 0 | 0 |
| div13-not-frounded | oklab-lightness | 62 | 1 | 0 | 0 |
| oklab-matrix-not-frounded | oklab-lightness | 62 | 1 | 0 | 0 |
| alpha-channel-written | channel-scope | 62 | 62 | 0 | 0 |

- **wrap-mirror-clamp-swap** (wrap-dispatch): Swap the wrapMirror and clamp bodies so wrap===0 clamps and wrap===2 mirrors, leaving the condition checks untouched. Only observable when a case actually needs wrapping (raw pre-wrap destination out of [0,size)).
- **wrap-else-becomes-clamp** (wrap-dispatch): Replace the else-branch wrapRepeat calls with clamp calls, leaving wrap===0/2 untouched. Reaches any case whose resolved wrap value is neither 0 nor 2 and that needs wrapping.
- **source-row-flip-removed** (vertex-id-convention): sourceRow = sourceY instead of height - 1 - sourceY. Reaches any case with height > 1 and nonzero image signal.
- **destination-row-flip-removed** (vertex-id-convention): destinationRow = destinationY instead of height - 1 - destinationY. Reaches any case with height > 1 and nonzero image signal.
- **weight-formula-linear** (accumulation): Replaces the quadratic accumulation weight with a linear one. Reaches any case with nonzero image signal.
- **float16-truncate-skipped** (accumulation): All three RGB accumulate lines drop the float16Truncate() wrapper, storing the raw F32-rounded sum instead of its float16 round-trip.
- **div13-not-frounded** (oklab-lightness): exponent = 1 / 3 (full double precision) instead of div(1, 3) (F32-rounded before use in Math.pow).
- **oklab-matrix-not-frounded** (oklab-lightness): Replaces the add(add(mul(F32(c0),r),mul(F32(c1),g)),mul(F32(c2),b)) chains for l/m/s with plain (c0*r)+(c1*g)+(c2*b) double arithmetic -- same constants, no per-operation F32 rounding.
- **alpha-channel-written** (channel-scope): Adds a 4th accumulate line writing destinationOffset+3, matching the RGB pattern. The reference deliberately leaves alpha alone.

## Wrap function direct rows

wrapRepeat: 18 rows. wrapMirror: 18 rows. Both include negative inputs to pin down JS `%` truncated-toward-zero semantics (see `wormhole-oracles.json` for the full table).

## oklabLightness direct rows

12 rows spanning clamped-negative, clamped->1, zero, unit, and near-boundary inputs.

## Cases

| Case | Size | Purposes | Diagnostic | Wrap | Collisions | Raw OOB (x,y) | Output SHA-256 |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| mirror-collision-oob-6x5 | 6x5 | discrimination,sweep | false | 0 | 10 | 30,30 | `d696cf4206416a07...` |
| repeat-collision-oob-7x4 | 7x4 | discrimination,sweep | false | 1 | 7 | 28,28 | `90be319b7b158243...` |
| clamp-collision-oob-5x9 | 5x9 | discrimination,sweep | false | 2 | 2 | 41,44 | `efe346258aa4f9af...` |
| mirror-negative-stride-negmod-6x6 | 6x6 | discrimination,sweep | false | 0 | 8 | 36,34 | `8b944be57a97a82a...` |
| repeat-negative-stride-negmod-7x5 | 7x5 | discrimination,sweep | false | 1 | 9 | 35,35 | `4e2424b034b53aba...` |
| clamp-negative-stride-5x5 | 5x5 | discrimination,sweep | false | 2 | 1 | 25,25 | `079b39bbdc4f93c4...` |
| wrap-else-arbitrary-value-6x4 | 6x4 | discrimination | false | 7 | 6 | 24,24 | `45dcd9507d8d4b49...` |
| wrap-fractional-truncation-1p9-9x6 | 9x6 | discrimination | false | 1 | 14 | 54,53 | `68754aa3f8ea9826...` |
| wrap-fractional-truncation-2p7-9x6 | 9x6 | discrimination | false | 2 | 1 | 54,53 | `1baeb7968601b6ad...` |
| known-answer-solid-white-1x1 | 1x1 | discrimination,sweep | false | 1 | 0 | 0,0 | `66aa5265fb25a915...` |
| identity-shift-zero-kink-zero-rotation-7x7 | 7x7 | discrimination | true | 1 | 0 | 49,49 | `54213f9d3a55400d...` |
| identity-zero-stride-clamp-7x9 | 7x9 | discrimination | true | 2 | 0 | 0,0 | `f25ab96b319f8e5d...` |
| large-stride-precision-stress-6x6 | 6x6 | discrimination | true | 1 | 7 | 36,36 | `1974b81ea701a165...` |
| high-precision-stride-6x6 | 6x6 | discrimination,sweep | false | 0 | 8 | 36,36 | `be851d00260c6bc3...` |
| sweep-1x1-wrap0-1 | 1x1 | sweep | false | 0 | 0 | 1,1 | `bcf2d6a5123777d0...` |
| sweep-1x1-wrap1-2 | 1x1 | sweep | false | 1 | 0 | 1,1 | `4364246deb0f6fdf...` |
| sweep-1x1-wrap2-3 | 1x1 | sweep | false | 2 | 0 | 1,1 | `9e11831574d48f6b...` |
| sweep-2x3-wrap0-4 | 2x3 | sweep | false | 0 | 2 | 6,6 | `e5cead7a44840e00...` |
| sweep-2x3-wrap1-5 | 2x3 | sweep | false | 1 | 3 | 6,6 | `f4f21b842fbe6661...` |
| sweep-2x3-wrap2-6 | 2x3 | sweep | false | 2 | 1 | 6,6 | `7f9d764d05155953...` |
| sweep-3x2-wrap0-7 | 3x2 | sweep | false | 0 | 2 | 6,6 | `ea1c0dd74950f29b...` |
| sweep-3x2-wrap1-8 | 3x2 | sweep | false | 1 | 2 | 6,6 | `273c3683236cb8d0...` |
| sweep-3x2-wrap2-9 | 3x2 | sweep | false | 2 | 1 | 6,5 | `1e8a9875ae06732e...` |
| sweep-4x4-wrap0-10 | 4x4 | sweep | false | 0 | 6 | 16,15 | `18e623ff28562e8f...` |
| sweep-4x4-wrap1-11 | 4x4 | sweep | false | 1 | 3 | 16,16 | `7a4b40446a5c6a93...` |
| sweep-4x4-wrap2-12 | 4x4 | sweep | false | 2 | 1 | 14,16 | `13e54de94d5723a2...` |
| sweep-5x5-wrap0-13 | 5x5 | sweep | false | 0 | 7 | 25,25 | `39c7f2f241f3d86a...` |
| sweep-5x5-wrap1-14 | 5x5 | sweep | false | 1 | 8 | 25,25 | `3c3af31d962bfbd9...` |
| sweep-5x5-wrap2-15 | 5x5 | sweep | false | 2 | 1 | 25,25 | `766afc44b37c1575...` |
| sweep-6x7-wrap0-16 | 6x7 | sweep | false | 0 | 8 | 41,40 | `e4d84b0702001f6f...` |
| sweep-6x7-wrap1-17 | 6x7 | sweep | false | 1 | 11 | 42,41 | `4e487de6e2123e02...` |
| sweep-6x7-wrap2-18 | 6x7 | sweep | false | 2 | 1 | 41,41 | `aa230af5b54be946...` |
| sweep-7x6-wrap0-19 | 7x6 | sweep | false | 0 | 11 | 37,37 | `640d16414ec2963d...` |
| sweep-7x6-wrap1-20 | 7x6 | sweep | false | 1 | 10 | 40,42 | `e24d4373ac87f70f...` |
| sweep-7x6-wrap2-21 | 7x6 | sweep | false | 2 | 1 | 40,40 | `f97f9e240649d6dc...` |
| sweep-8x8-wrap0-22 | 8x8 | sweep | false | 0 | 18 | 63,64 | `fcb9399e5f7862c1...` |
| sweep-8x8-wrap1-23 | 8x8 | sweep | false | 1 | 17 | 58,60 | `8edead8d6fc523ae...` |
| sweep-8x8-wrap2-24 | 8x8 | sweep | false | 2 | 1 | 63,61 | `7d19b53660b4774c...` |
| sweep-9x13-wrap0-25 | 9x13 | sweep | false | 0 | 34 | 116,115 | `1b337b0ffa495b8c...` |
| sweep-9x13-wrap1-26 | 9x13 | sweep | false | 1 | 30 | 117,117 | `18067082cf89aa2f...` |
| sweep-9x13-wrap2-27 | 9x13 | sweep | false | 2 | 7 | 85,117 | `ca2a05b2dcbc2460...` |
| sweep-13x9-wrap0-28 | 13x9 | sweep | false | 0 | 31 | 116,102 | `af1d2083622dbffa...` |
| sweep-13x9-wrap1-29 | 13x9 | sweep | false | 1 | 31 | 117,115 | `f3d329578536b319...` |
| sweep-13x9-wrap2-30 | 13x9 | sweep | false | 2 | 1 | 112,117 | `e08d8cc19f050af3...` |
| sweep-16x16-wrap0-31 | 16x16 | sweep | false | 0 | 63 | 239,236 | `35be006438657753...` |
| sweep-16x16-wrap1-32 | 16x16 | sweep | false | 1 | 71 | 252,249 | `78a301ff1fd79844...` |
| sweep-16x16-wrap2-33 | 16x16 | sweep | false | 2 | 3 | 248,246 | `b9028100626de9c6...` |
| sweep-17x31-wrap0-34 | 17x31 | sweep | false | 0 | 136 | 382,272 | `e7091aa055a987f5...` |
| sweep-17x31-wrap1-35 | 17x31 | sweep | false | 1 | 141 | 499,504 | `4d0040a2c7c714f6...` |
| sweep-17x31-wrap2-36 | 17x31 | sweep | false | 2 | 15 | 503,498 | `411a59a568ba5acc...` |
| sweep-31x17-wrap0-37 | 31x17 | sweep | false | 0 | 140 | 507,511 | `33f027ea8c51d3fe...` |
| sweep-31x17-wrap1-38 | 31x17 | sweep | false | 1 | 136 | 444,482 | `097dd721e8e9af10...` |
| sweep-31x17-wrap2-39 | 31x17 | sweep | false | 2 | 24 | 404,527 | `057a8c8160c23ecb...` |
| sweep-33x33-wrap0-40 | 33x33 | sweep | false | 0 | 281 | 1087,827 | `33d83e215561d29d...` |
| sweep-33x33-wrap1-41 | 33x33 | sweep | false | 1 | 274 | 1089,1085 | `e227633fdec8c40f...` |
| sweep-33x33-wrap2-42 | 33x33 | sweep | false | 2 | 33 | 795,1089 | `de28ce54f499b2e5...` |
| sweep-5x1-wrap0-43 | 5x1 | sweep | false | 0 | 1 | 4,5 | `5bd3663f9a3db8e3...` |
| sweep-5x1-wrap1-44 | 5x1 | sweep | false | 1 | 2 | 5,5 | `9d6acc57a32597d7...` |
| sweep-5x1-wrap2-45 | 5x1 | sweep | false | 2 | 1 | 5,5 | `77c8ff91f5f05445...` |
| sweep-1x7-wrap0-46 | 1x7 | sweep | false | 0 | 2 | 7,7 | `296e3fd6be1e6cfc...` |
| sweep-1x7-wrap1-47 | 1x7 | sweep | false | 1 | 2 | 7,7 | `2de0384f5bdc48f0...` |
| sweep-1x7-wrap2-48 | 1x7 | sweep | false | 2 | 1 | 7,6 | `1ba6a20814aa6967...` |

