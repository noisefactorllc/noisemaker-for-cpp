# Shape Mixer182 exact-parity oracle

Program `classicNoisedeck/shapeMixer:shapeMixer`; corpus revision `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`; exact define `LOOP_OFFSET=10`.

## Result

The clean canonical JavaScript authority produced 42 fixtures: 20 mode-matrix cases and 22 focused cases. Every fixture stores complete independent input and output Float32 words, canonical RGBA8 bytes, filters, bindings, probes, finite census, and canonical-repeat/public-canonical identity. Input pre/post SHA-256 and immutability are frozen independently for canonical, canonical-repeat, and public-catalog routes. No C++ output contributes expected data.

The JavaScript comparer rejects shape and payload-count mismatch before iteration, then checks every raw Float32 word and every independently supplied RGBA8 byte. Signed zero, distinct quiet-NaN payloads, the final alpha lane, and a byte-only mismatch are self-tested.

## Render fixtures

| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| mode-0-scalar | 7x5 | 48c875c1fb9064cd7919504eb009c1bfddafb4f41d695191d350ca94c4881d16 | 9a30cd4b47a69c5a4531d0b847c7018e37f8efe1d14fb982714599fb0d054157 |
| mode-0-vector | 8x6 | c0a23bfdf1d1277b50ef7ccad50e01570824eda9ed9138cb4a6be238817ae7b2 | 27cfd3519e733b3a194a12c768c736e3911d40844ade8fa5e7b49a33c3e07e5a |
| mode-1-scalar | 7x5 | 5702b2b1cee7e32fa4930d2cd5a4b6baad75e810a2bb0b69bb226f8a7c3a0b80 | a973b32fc02e37d126c93f79098e4a4994ef65a41ff91e57c912a53c7bb3264f |
| mode-1-vector | 8x6 | 8b1f8f5378150577c63a431304bacf552d74f828b8d29a5f24a3f1ddc0838f6b | ebe912ddda168d45b5d1977e992e0a5d06e2ee7da11d881d718d45b05c339fd9 |
| mode-2-scalar | 7x5 | a665760b92a3a66d8c42cafd5a01e601b5ce047874aca75ec9201ffeff2503b7 | 6dfade1fb1a2203343a464496f2980ad7abb7ba9e2ace3032552209d16356b74 |
| mode-2-vector | 8x6 | 238262b336d556b39f10d4788a77a111edbd02a95be7d218f2adaeb3ce84e70f | a04e1cc82a1431a0e27e4ea5b31d23408d0f70db71ec2625f3df947ac3d3eaba |
| mode-3-scalar | 7x5 | 89d87b84315c81970e87d165d4021717563577b19802722459fe60f682adca68 | 15179f6c2d355d09d5a99c6cd02ad355ba50caf19d77d678e742676a8443351d |
| mode-3-vector | 8x6 | 0b24a7cc42ecc61f608d6e8722bbcaf715e91c50790655ebfa8901146ec51be3 | 5fc08253c2a78d08c980625aa283ad3747861752edf733d8971404efc36040a7 |
| mode-4-scalar | 7x5 | 78990294eccf64d63d9aee27655f333145f51812bbddf526ed536617eb259e97 | c90c28ec13817ce657ac651fb59b855b4693a7818aeeaeab48d3dc60efc85518 |
| mode-4-vector | 8x6 | a1e24f0f51f3a61983bc75d24a1a66e72d50125d89bd6fc18b71dbd5a401acb8 | d98a053c17f65a0ab897ef39e5b393f77926e4cef9b2ce35d3c70b13723dbc99 |
| mode-5-scalar | 7x5 | e1a1a1544fd956aa924abddfaac081e0b28f88099cb66a93ace866385fedb426 | 0d6917bfcbeca90e20ea0d5a3c506f1d0994b2910fff2b3c8c6be458a73f5358 |
| mode-5-vector | 8x6 | 6711ba5eb91ebd660b5a6b16786a44b796369cc066c1615352d6f6ba70c52492 | 741313a653c2fc614754a3866eb836bcf1268427fb7bfc7907dd3ad116a4d629 |
| mode-6-scalar | 7x5 | f9b8326eedfd4c036b21e9a9ca9bc962221a4fc97991170c0a50626b048b8ad4 | 861f51e717ebd43f930cf07251350d0c9c39334a4a924ece9c7c9fd3f44149be |
| mode-6-vector | 8x6 | 08d8d5ecaa650a495f3d3b9d64a4ac9f2e4561e17c0eed3bc4efe29b933ee3f2 | cfb278713eb2b3a2d87f26a2614958a79d7a14b7f2e6376afd954a3282598de2 |
| mode-7-scalar | 7x5 | c4b156f21c7a8ecfdb76b76d5b47177811d1c19aa10f8e41602e8cf881c9f676 | a30d9eb011e9248ce7035b64e3ed7d37716aa83c1cede02bc4d3234d0f20af30 |
| mode-7-vector | 8x6 | 35d5c7ee1942875ed99bc08ebbc854bcb533d7e16acba4e4569bf2250833404b | 5269591671660badcd429e3f854e4c94e5a6e2815c23971d05e15f7a6ecef7cd |
| mode-8-scalar | 7x5 | 2d40cd22376414b51190bedc674cc4a4180716fb44c8133da450f010f6968111 | be3f844d337a3726aae460ba7d17f075dfdf54cb0ecc688be8c2fccfb8ef3b9e |
| mode-8-vector | 8x6 | be6b350ca2602be9e86a1a59a1c8526966eeb432bd8d6af2a71294873e319b52 | 6a45e9f27c2a12fb0e5e018c61763ef8907a08fabf9802da2728db39dd7311b0 |
| mode-9-scalar | 7x5 | 0d138955a39867b03dbff922edc517e7dc6f6dd9d4e67b17326d1dc45ebef458 | aff43ed2e0a260edf41b28f5bd3f35dddd8ab2ba2b6be0eda73b035f8bff6b93 |
| mode-9-vector | 8x6 | 6c943761e1fc260d96195685ed30b5cb13dde720013e9b6c38dd1ea0365f1ad0 | f5b1d350ab48ce3205359b95faceda3a19ab2535aace670420a6fed624649424 |
| palette-hsv | 9x5 | 4cae8c338a9c4e4d3dbe4cd7b6912d8df190f75edb8c77d38d6b25ce96168861 | 6bbd8056a77e645bb58f8e0d171c2a331ebf7b1e25777481815ca92d9f532326 |
| palette-oklab-lanes | 5x9 | 85b3a061662d88e18f0660ad00fa203adf241d6967a8ed6bb2a155d4651940c4 | 8752722a025a0f80c80a564ca45e5dd52dda8122b67912e29e122a8320278e96 |
| palette-rgb-extremes | 9x5 | db875bd9b785d5694d89285911cb12b637d31f1e3b85b31dc78c95d6fa77938a | 006fb1fd8aae7368d4fc31074bc086d0dd5034a9a55909cdc6255d6f50af740d |
| animate-minus | 9x5 | 10a4869040ad1632d57b776e2b9491f7b0bd81115c61eaf64a2f5ff7c3458144 | 4c9b73749883e65032d6b2db8fd7b27f96b3dafdc357da88bfc88b28ae9971ac |
| animate-zero | 9x5 | 1ec326bbf7e75548b0ef6549852280dce4f9188bd4a1518d320e4583a5fcadc5 | 80e12262217fe1addefec1c9da11a830b032693a27f7a4aba9bd6a1549827587 |
| animate-plus | 9x5 | 2959fdff2b25665fb1177f3acfb3289d3298b0b68098195ae706ba67a0a2c13f | 34165f2b7d7949be38f6bc4fcd1759e7092162bea64d218b2299c5b61def4b51 |
| cycle-minus | 9x5 | 503ad3736bd2a53df61dd6fd25913b6afdf83a52f7704db22f9863d91c46fe15 | 7513fece717234de5d5637ea24cd9009d337054b12923a81d3a956cbb69e4aea |
| cycle-zero | 9x5 | 4085cb2380be25a223e13651c6acf1c79ae807241350dfe60b486fe52bb47e32 | 27541812f9952ebb3ac3ae7bcb39b10db39aab26ea6534500b2d6f4cad5d6955 |
| cycle-plus | 9x5 | ef2ad5cd078b7b2e227c38fe1a448807a3e11ee85b6ac16f31883d12c67e7580 | ff88889920936efd656ad97c6239ea3565b67f448e317f7b79c8b7dee769e64e |
| levels-one-scalar | 9x5 | a2f31238f59900e13980e4b67c153a7ca7402da1b587bc843e58881dad7f67c4 | e3c671208c2e2a11bcbcecd077245dbf7d2341cf1c504a629314cde51d6183b8 |
| levels-fractional-vector | 9x5 | f5df63e2373d301ec4ba1c7fd3f99ad1802fe76c88f11eeefc6d03d2e30816b9 | 86f8ee61953e0eb52338f9c6fdb1bf924b85dfea701fc4ee80c656f685399e55 |
| loopscale-min | 9x5 | 39518fc13aeb127f15f02b19c981f2db9a17a9b0b705394fe29d383796e35567 | f1afe1c4ec1c1cb0282a621ece6959f8967afaeb7422da4da27806d2bb8c6c32 |
| loopscale-max | 9x5 | 49daf5f2e9de1ae0d44438501360774ac7be992db6f5014a5ef7c80507a966fd | 7677c029f362905eca89e7f71a2cd666680fd6cd67ca4c07fe53ad8ce724c09f |
| dead-random-neg-nowrap | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-neg-wrap | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-nowrap | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-wrap | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| tiled-fractional-ratio | 6x4 | efcca3511fa2e0b777da255eae9fae98f18d640992c1e5b4e78734e05d34d9e3 | b033f0138ed061780487c946536c4f50afd544ecee4097a0602ce371e7e463f8 |
| sampler-edge-y | 9x7 | 41e18da5a768dbe4b8e03ef93bcdc917bd57ea9f1615b5386bc492b34048ba18 | 45d08a2f048bfe356e95c5a2e37d7379ae25f9cf728f287d5c851131b6905c46 |
| alpha-three-way | 3x1 | 5f94ac5cbb2d60e7b6244d78311cf476c1b2de8ec4ab5f9ee027ae9e36611e15 | 5a036fe39aea50f76164efc7fd360d59c87e0a8562d2eb32adf4e303c0d285ef |
| external-context-base | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| external-context-extreme | 9x5 | 9cd8516305b61ec046da1b09fe662301ba1e011f29fab7bf637293688824b349 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |

## Rendered behavioral mutations

| Mutation | Required witnesses | Changed lanes at first witness | First top-down x,y/channel |
| --- | --- | ---: | --- |
| vector-reflect-scale-sign | mode-7-vector | 144 | 0,0/r |
| vector-reflect-subtract-to-add | mode-7-vector | 144 | 0,0/r |
| vector-reflect-reversed-output-operands | mode-7-vector | 144 | 0,0/r |
| vector-reflect-defensive-normal-normalization | mode-7-vector | 144 | 0,0/r |
| vector-reflect-omit-product-f32 | mode-7-vector | 40 | 0,0/r |
| scalar-reflect-mathematical-dot | mode-7-scalar | 105 | 0,0/r |
| scalar-reflect-factor-association | mode-7-scalar | 105 | 0,0/r |
| vector-refract-wrong-k-formula | mode-8-vector, animate-minus, animate-plus | 144 | 0,0/r |
| vector-refract-omit-left-f32 | mode-8-vector | 54 | 2,0/g |
| vector-refract-omit-right-f32 | mode-8-vector | 67 | 0,0/r |
| scalar-refract-mathematical-dot | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-eta-association | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-omit-left-f32 | mode-8-scalar | 9 | 1,0/b |
| scalar-refract-omit-right-f32 | mode-8-scalar | 23 | 1,0/r |
| scalar-refract-omit-final-f32 | mode-8-scalar | 17 | 2,0/r |
| wide-mod-reversed-operands | mode-5-vector | 144 | 0,0/r |
| wide-mod-unmaterialized-divisor | mode-5-vector | 64 | 0,0/b |
| index-linear-condition-fixed-lane | palette-oklab-lanes | 37 | 0,0/b |
| index-srgb-low-write-fixed-lane | palette-oklab-lanes | 55 | 0,0/r |
| index-linear-low-read-fixed-lane | palette-oklab-lanes | 31 | 0,0/g |
| index-srgb-high-write-fixed-lane | palette-oklab-lanes | 97 | 0,0/r |
| index-linear-high-read-fixed-lane | palette-oklab-lanes | 59 | 0,0/b |
| linear-to-srgb-loop-bound-two | palette-oklab-lanes | 45 | 0,0/b |
| linear-to-srgb-branch-inverted | palette-oklab-lanes | 135 | 0,0/r |
| oklab-fwdB-transpose | palette-oklab-lanes | 135 | 0,0/r |
| oklab-fwdA-row-column | palette-oklab-lanes | 135 | 0,0/r |
| oklab-remove-fwdA-intermediate-f32 | palette-oklab-lanes | 90 | 0,0/r |
| mode-0-vector-dispatch | mode-0-vector | 144 | 0,0/r |
| mode-0-scalar-dispatch | mode-0-scalar | 105 | 0,0/r |
| mode-1-vector-dispatch | mode-1-vector | 144 | 0,0/r |
| mode-1-scalar-dispatch | mode-1-scalar | 105 | 0,0/r |
| mode-2-vector-dispatch | mode-2-vector | 143 | 0,0/r |
| mode-2-scalar-dispatch | mode-2-scalar | 105 | 0,0/r |
| mode-3-vector-dispatch | mode-3-vector | 144 | 0,0/r |
| mode-3-scalar-dispatch | mode-3-scalar | 105 | 0,0/r |
| mode-4-vector-dispatch | mode-4-vector | 144 | 0,0/r |
| mode-4-scalar-dispatch | mode-4-scalar | 102 | 0,0/r |
| mode-5-vector-dispatch | mode-5-vector | 144 | 0,0/r |
| mode-5-scalar-dispatch | mode-5-scalar | 105 | 0,0/r |
| mode-6-vector-dispatch | mode-6-vector | 144 | 0,0/r |
| mode-6-scalar-dispatch | mode-6-scalar | 105 | 0,0/r |
| mode-7-vector-dispatch | mode-7-vector | 144 | 0,0/r |
| mode-7-scalar-dispatch | mode-7-scalar | 105 | 0,0/r |
| mode-8-vector-dispatch | mode-8-vector | 144 | 0,0/r |
| mode-8-scalar-dispatch | mode-8-scalar | 105 | 0,0/r |
| mode-9-vector-dispatch | mode-9-vector | 144 | 0,0/r |
| mode-9-scalar-dispatch | mode-9-scalar | 105 | 0,0/r |
| vector-factor-inversion-removed | mode-4-vector, mode-7-vector, mode-8-vector | 144 | 0,0/r |
| scalar-factor-inversion-removed | mode-4-scalar, mode-8-scalar | 102 | 0,0/r |
| scalar-vector-overload-swapped | mode-5-scalar, mode-7-scalar, mode-8-scalar | 33 | 0,0/r |
| palette-mode-four-branch-inverted | mode-4-scalar, mode-4-vector | 105 | 0,0/r |
| blendy-half-removed | mode-5-vector, mode-7-vector, mode-8-vector | 127 | 0,0/r |
| blendy-half-after-factor-inversion | mode-5-vector, mode-7-vector, mode-8-vector | 141 | 0,0/r |
| scalar-posterize-order | levels-one-scalar | 9 | 0,2/r |
| scalar-posterize-level-one-special-case | levels-one-scalar | 135 | 0,0/r |
| vector-posterize-order | levels-fractional-vector | 34 | 2,0/r |
| cycle-palette-sign-reversed | cycle-plus | 135 | 0,0/r |
| animate-sign-reversed | animate-minus | 135 | 0,0/r |
| input-textures-swapped | mode-0-vector, tiled-fractional-ratio, sampler-edge-y | 161 | 0,0/r |
| second-texture-substituted-with-first | mode-0-vector, tiled-fractional-ratio, sampler-edge-y | 171 | 0,0/r |
| input-texture-size-substituted | tiled-fractional-ratio, sampler-edge-y | 88 | 0,0/r |
| second-texture-size-substituted | tiled-fractional-ratio, sampler-edge-y | 60 | 0,0/r |
| input-filter-forced-nearest | mode-1-scalar, mode-3-vector | 54 | 2,0/a |
| second-filter-forced-nearest | mode-3-vector, sampler-edge-y | 72 | 0,0/a |
| input-y-convention-inverted | sampler-edge-y | 58 | 0,0/r |
| second-y-convention-inverted | sampler-edge-y | 120 | 0,0/r |
| alpha-forced-one | alpha-three-way | 3 | 0,0/a |
| alpha-only-input-a | alpha-three-way | 2 | 1,0/a |
| alpha-only-input-b | alpha-three-way | 1 | 0,0/a |
| tile-offset-omitted | tiled-fractional-ratio | 63 | 0,0/r |
| full-resolution-replaced-by-local | tiled-fractional-ratio | 66 | 0,0/r |
| local-resolution-replaced-by-full | tiled-fractional-ratio | 74 | 1,0/r |
| loop-offset-ten-changed | loopscale-min, loopscale-max, tiled-fractional-ratio | 134 | 0,0/r |
| rotate-palette-omitted | palette-rgb-extremes, palette-hsv, palette-oklab-lanes | 135 | 0,0/r |
| repeat-palette-omitted | palette-rgb-extremes, palette-hsv, palette-oklab-lanes | 130 | 0,0/r |
| palette-vector-component-order | palette-rgb-extremes, palette-hsv, palette-oklab-lanes | 135 | 0,0/r |

Every row above is an independent canonical-factory one-anchor/one-replacement mutant and every named witness changes at least one raw Float32 word.

## Direct-helper and structural barriers

The direct-helper ledger contains published three-lane reflect/refract words, all six scalar raw-word witnesses, negative-k/exact-zero/signed-zero/non-unit/NaN refract classifications, scalar NaN classifications, and negative/divisor/zero/fractional/Float32-sensitive wide-mod cases.

| Structural-only mutation | Authentication layer |
| --- | --- |
| vector-reflect-dot-child-order | pinned noisemaker-for-cpu GLSL runtime owner slice |
| vector-refract-dot-child-order | pinned noisemaker-for-cpu GLSL runtime owner slice |
| float-bits-to-uint-positive-zero-numeric-conversion | canonical factory |
| scalar-uint-xor-lane-0 | canonical factory |
| scalar-uint-xor-lane-1 | canonical factory |
| scalar-uint-xor-lane-2 | canonical factory |
| scalar-uint-xor-uvec3-parent | canonical factory |

Structural-only rows deliberately have no fabricated pixel witness. The report also records four source-authenticated non-pixel barriers: negative-operand fmod semantics, the pixel-inert fourth linear-to-sRGB typed-array write, unreachable inverse OKLab matrices, and final vector narrowing that is immediately rematerialized by the factory.

## Sampling and coordinates

- Surface storage, probes, and mismatch coordinates are top-down.
- The canonical runtime consumes bottom-left fragment coordinates and performs its own sampler y conversion.
- Nearest and linear filter choices are frozen independently for `inputTex` and `tex`.
- RGBA8 comes directly from canonical `Surface.toRgba8()`, independently of the expected word arrays.

## Regeneration

```sh
NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --write --cpu-root <immutable-cpu-snapshot-root>
NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_shape_mixer_native_oracle_include.py --check
```

The JavaScript generator requires distinct external non-symlink authority/live
directories and runs its frontend probe in one OS temporary directory. Both
generators are fail-closed. Check mode performs no writes.
