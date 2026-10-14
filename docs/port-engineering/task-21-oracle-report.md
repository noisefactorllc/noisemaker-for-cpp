# Task 21 direct canonical oracle report: Degauss

## Conclusion

The frozen Task 21 oracle is ready for exactly `filter/degauss:degauss`. It is
generated directly from the pinned canonical CPU factory and does not depend on
the C++ implementation. Nine cases cover the exact-copy and mask-zero returns,
normal three-channel processing, metadata defaults, nondefault F32 parameters,
time/speed short circuits, landscape/portrait/square frequency branches,
tiled/untiled/fallback contexts, both direction signs, and the displacement
cap. Thirteen counted factory-text mutations prove sensitivity across the
17-function acyclic helper graph.

No compatibility transform is indicated for this key. In particular, the
canonical `%` site receives only nonnegative next-neighbor indices and positive
limits on live paths, so it has no Sacred Geometry-style division/remainder
compatibility issue.

## Frozen provenance

| Field | Frozen value |
| --- | --- |
| Key | `filter/degauss:degauss` |
| Source | `sources/filter/degauss/degauss.glsl` |
| Corpus revision | `a1a3fa2a84223dfc1f5ec2c7a54a6f4269139c15` |
| Raw source | 11,490 bytes; SHA-256 `cfefff702ef78db421c088a3b679da2c576b7f4484c777f1d414c66aef0c1a1a` |
| Normalized source SHA-256 | `a0a42b0db6bae308295657d5540989bba939ec7cc99f121d97e5d98fd3cca304` |
| Defines / numeric literals | `{}` / `glsl-f32` |
| Canonical factory | `canonicalFactory43`; `Function.prototype.toString()` SHA-256 `2dc66240984430c10a2a417e891517094371b3f2a03574931f50be929399f776` |
| Canonical generated runtime | SHA-256 `80b2e701426a5003d9ef44dce09de1f601f4c8cd1e4bff1f0c4d2b607e95e91c` |
| Typed fingerprints | function tuple `b806b6ce4f98eae3438bc0b01ed3fe0a3aa1f1d1c9a6186c8d18da0675c878d0`; whole program `3079146057f6cc68f832636748032e32777c84b0d2e36a6843ea9c2a0542d3f6` |
| Typed shape | 17 source functions, zero loops, acyclic call graph |
| Compatibility transform | none |

The binding order is frozen as `TAU:const float@1`,
`inputTex:sampler2D@2/S1`, `resolution:vec2@3`, `tileOffset:vec2@4`,
`fullResolution:vec2@5`, `time:float@6`, `displacement:float@7`,
`speed:float@8`, `seed:int@9`, `direction:float@10`, with
`fragColor:vec4@11`. The pass route is `inputTex <- inputTex` and
`fragColor -> outputTex`; aliases for direction, displacement, seed, and speed
are identity mappings.

## Fixture and coverage

Every case creates a fresh asymmetric, edge-contrasting top-down F32 input at
the output size:

```text
R=((17*x+31*y+13)%101)/100
G=((7*x+19*y+23)%97)/96
B=((29*x+11*y+5)%89)/88
A=(((5*x+7*y+3)%23)-5)/12
```

Every lane crosses `Float32Array` storage. Alpha deliberately ranges from
`-0.4166666567f` through `1.4166666269f`, which distinguishes the exact-copy
returns from the normal-path `clamp01`. Output and input storage are top-down;
the runtime supplies bottom-left fragment coordinates. The zero-displacement
case confirms that this orientation mapping returns the exact same 1,872 F32
bytes, including all 50 out-of-range alpha pixels.

| Case | Main distinction | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- |
| displacement-zero-exact-copy-tiled | exact-copy return; nonzero tile/full context | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` | `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| default-landscape-untiled-center-mask | all defaults; landscape; untiled; exact center mask zero | `f866f3855885250a78169a56f32f59b15379152d47eebf1d4e6cec20a0e53b6f` | `9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98` |
| nondefault-landscape-tiled-negative-direction | both noise evaluations; negative direction; seed 37 | `361ac1ef7266451f4e3a4b74f9c1360c4dd9055ca9114877de0d5197614c1dda` | `5dced19d2b93c865bee67ba5833da21085b56d27070dc0c996933582892166ec` |
| nondefault-portrait-tiled-positive-direction | portrait; direction +180; seed 100 | `cb1aa9143d7f05a1d3992467b343d2ff5da4fa546946b4ac33728dca22e3a21c` | `02e75af7adc002d125c875129923831a3db7fbaede316260a3f12176b7b6a5b6` |
| speed-zero-nonzero-time | base noise only through `speed == 0` | `bfe2405b610d0a83dde7ac8a767936da729a0fc404d24b5c5e7f0e125f8e684f` | `3d9e5456a005805257dc4d9dd34d02b25b3278da12abeb67c3066316edcda8d6` |
| time-zero-positive-speed | base noise only through `time == 0` | `350d07667e2df6a2c3eb09b70e17e355072d114bd88a99b01160ffe1ae32974e` | `8bc8e7027373b0ef49c9b26adffe1b6a4958402e50e62494247a12b913e2785d` |
| full-resolution-zero-fallback-landscape | `fullResolution.x <= 0` fallback; untiled | `d14147fa42ecf04d6bcfe69421629d139b0da9e733a0d9bdaee19dc6c86bb534` | `21887cecda8086b36c4f4de752944d228f5abb50f677745a17cb79d82957394f` |
| square-frequency-equality | exact square branch; direction -180 | `bba736cff27c6ad6dadd18a954a08c4b4369032feb596d064f57f1751ab86e8d` | `cb38bf280658b38f4826f8315f6d56c6459d9ab4108d44b875ca72115d8c1ca5` |
| untiled-over-cap-binding-domain-diagnostic | direct displacement 1.75 clamps to 1.0 | `8f70a5e03d90c93dbc18ff768108a638b938781cd464418b5d07dff674a1e55f` | `ee597e5fc86137977db87fc32f06b81e8423820457b5a96f7d8efe5f918bb412` |

The last case is intentionally outside the metadata UI range. It is a direct
binding-domain branch diagnostic, not a metadata-valid preset. Disabling the
cap changes 348 F32 lanes and 346 RGBA8 bytes only in that case; the other eight
cases remain byte-identical.

Each case records all uniform F32 words, dimensions, tile/full vectors, input
F32 and RGBA8 hashes, top-down input/output probes with lane bits, output
metrics, and repeat identity. All 4,228 canonical output lanes are finite. The
normal nonzero path performs 13 level-zero fetches per pixel: one original
fetch plus three four-fetch bilinear samples.

## Mutation sensitivity

All mutations are made against the exact pinned factory text with asserted
replacement counts. A missing or duplicated source shape fails generation.

| Mutation | F32-changing cases / 9 | RGBA8-changing cases / 9 | What it locks |
| --- | ---: | ---: | --- |
| channel-order-red-zero-to-blue-two | 8 | 8 | channel selection and three-channel call order |
| direction-rotation-disabled | 7 | 7 | direction conversion and rotation; default direction-zero identity |
| wrap-index-next-neighbor-clamped | 8 | 8 | positive `%` next-neighbor wrap |
| wrap-float-coordinate-clamped | 8 | 8 | periodic floating sample-position wrap |
| bilinear-fx-forced-zero | 8 | 8 | horizontal interpolation |
| bilinear-fy-forced-zero | 8 | 8 | vertical interpolation |
| time-noise-branch-disabled | 6 | 6 | second simplex evaluation; byte identity for displacement/time/speed short circuits |
| singularity-mask-forced-one | 8 | 8 | mask and exact center behavior |
| alpha-clamp-disabled | 8 | 0 | F32-only alpha contract |
| displacement-cap-disabled | 1 | 1 | cap boundary and eight-case in-range identity control |
| simplex-amplitude-42-to-41 | 8 | 8 | simplex reduction path and its helper chain |
| frequency-axes-unswapped | 7 | 7 | landscape/portrait cross-axis mapping and square identity control |
| seed-offset-disabled | 8 | 8 | integer seed binding and base seed construction |

The alpha mutation is an especially important proof that RGBA8 is
insufficient: it changes 49–53 F32 alpha lanes in every normal-path case but
zero RGBA8 bytes because RGBA8 conversion clamps the same out-of-range values.

## Reproduction and acceptance

Run from the repository root with an authenticated CPU root and matching ledger:

```sh
node docs/port-engineering/task-21-oracle-generator.mjs --cpu-root "$CPU_ROOT" --ledger "$CPU_LEDGER" --check
```

`--check` regenerates every canonical case and mutation in memory, repeats each
canonical render, revalidates all pinned provenance and source shapes, and
requires exact JSON identity with `task-21-oracles.json`. `--write` is the only
mode that rewrites the JSON artifact. No repository file is read as an expected
image, and no repository file is modified.

At freeze time:

- generator SHA-256: `cb1c751b687b6fa4c9a4cadcc780efb7ee85f40bcb70f04b3a03bde5445155b0`
- oracle JSON SHA-256: `ae38195e3d2977f7580f71c4a83310a5265694b1bfce8148131135ab7ed128b2`
