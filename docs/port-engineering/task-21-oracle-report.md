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
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Raw source | 10,803 bytes; SHA-256 `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` |
| Normalized source SHA-256 | `7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560` |
| Defines / numeric literals | `{}` / `glsl-f32` |
| Canonical factory | `canonicalFactory45`; `Function.prototype.toString()` SHA-256 `f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38` |
| Canonical generated runtime | SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Typed fingerprints | function tuple `f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a`; whole program `73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d` |
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
| default-landscape-untiled-center-mask | all defaults; landscape; untiled; exact center mask zero | `c6bf433ea90b0c82d842724d8f633fefb8cded8e34ad83b9d3480d98a7051c71` | `9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98` |
| nondefault-landscape-tiled-negative-direction | both noise evaluations; negative direction; seed 37 | `08dbc2988787474877268f9661bbeccbdc88dbd9f43bbfc3240e58120cf363f1` | `16267b09be48cdb9b967ad1e4c203cd2170b940639975ee1cbba75309765db2c` |
| nondefault-portrait-tiled-positive-direction | portrait; direction +180; seed 100 | `86b32d32e970fffccc7049bf9c091f5e8b5e9139af7afd6f7bee6d315636a37f` | `d2aca58372b68e20691c89a7ab278aebf97ffe85ffa35eb3d4bb6414016803d7` |
| speed-zero-nonzero-time | base noise only through `speed == 0` | `2bd1aa43c71d4eaab6298492b9edafd35978cd439eeae2a270968f6210128f37` | `7788b9151bca2f493a0af156b38cc636e14b5f27d4bbed16ed60c4942513dc22` |
| time-zero-positive-speed | base noise only through `time == 0` | `c2f6253b9491350f176470a5be560068fb634e31432d524360d58ee03ed0586f` | `710ce156f4b71dae2d487ac6a78fee5e58ee044fe400eb24740764c1784039b6` |
| full-resolution-zero-fallback-landscape | `fullResolution.x <= 0` fallback; untiled | `15401d32e6befb161651150f044f35496bf741be49872b3869716689131453ff` | `96cbb763c8daf83c9ef99c2972993148a5c2e5231436ebe9c4d4cb581c473a32` |
| square-frequency-equality | exact square branch; direction -180 | `8c09129cc2a75ca01f8a3d774307128cb1c44721c884821f6b22b7cff67e2948` | `8e456f5906aca7993075834d2f3ad09f358f9acaffbfcc4dbc0f113ed4fd94c6` |
| untiled-over-cap-binding-domain-diagnostic | direct displacement 1.75 clamps to 1.0 | `c7983e127a9bc4ed938cff5c316d71ed50f2dfb2126b54718901efd80aae705f` | `40d20fde4f5aab0e0e42a0371d373dbfdb66f62644650bef511ff8ffa3592bda` |

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

Run from any directory:

```sh
node docs/port-engineering/task-21-oracle-generator.mjs --check
```

`--check` regenerates every canonical case and mutation in memory, repeats each
canonical render, revalidates all pinned provenance and source shapes, and
requires exact JSON identity with `task-21-oracles.json`. `--write` is the only
mode that rewrites the JSON artifact. No repository file is read as an expected
image, and no repository file is modified.

At freeze time:

- generator SHA-256: `0c1f12904e1c17a39c61055596be9f0d46ecded252a9d5c7cf1339653472c5c9`
- oracle JSON SHA-256: `bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38`
