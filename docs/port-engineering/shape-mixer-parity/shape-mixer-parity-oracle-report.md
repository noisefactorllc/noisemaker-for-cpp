# Shape Mixer182 exact-parity oracle

Program `classicNoisedeck/shapeMixer:shapeMixer`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; exact define `LOOP_OFFSET=10`.

## Result

The clean canonical JavaScript authority produced 42 fixtures: 20 mode-matrix cases and 22 focused cases. Every fixture stores complete independent input and output Float32 words, canonical RGBA8 bytes, filters, bindings, probes, finite census, and canonical-repeat/public-canonical identity. Input pre/post SHA-256 and immutability are frozen independently for canonical, canonical-repeat, and public-catalog routes. No C++ output contributes expected data.

The JavaScript comparer rejects shape and payload-count mismatch before iteration, then checks every raw Float32 word and every independently supplied RGBA8 byte. Signed zero, distinct quiet-NaN payloads, the final alpha lane, and a byte-only mismatch are self-tested.

## Render fixtures

| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| mode-0-scalar | 7x5 | 4a8e1eb9d999e54c5f34e976bc645544267e556d397f806ff7b7202dde38eadc | 9a30cd4b47a69c5a4531d0b847c7018e37f8efe1d14fb982714599fb0d054157 |
| mode-0-vector | 8x6 | bc6d1eeeec579bc9a9d8f3a50c851883b22ac77866ac494356c3b660bd6f03f0 | 27cfd3519e733b3a194a12c768c736e3911d40844ade8fa5e7b49a33c3e07e5a |
| mode-1-scalar | 7x5 | 64d772c020291f52e7f4afc1f861dc9b655bba0e37b32322174f4e7ad62b97c7 | 4c1c65ba23be20de4175b5f971396050a9a3335a5adbe39f2f61e932342f4808 |
| mode-1-vector | 8x6 | 81e90537ad86d2c2e3c1b588901dab4a67117f9cf65d2337eb8c8790d1196b03 | 01a48bc1a669ce2c76020b05f439a5845406c6574bcd1ee75470fee26e18b4c6 |
| mode-2-scalar | 7x5 | 32c9783ae9227c0ff7987df718c3e1ea1599f5ccf4af09168676426d3d54d664 | 6dfade1fb1a2203343a464496f2980ad7abb7ba9e2ace3032552209d16356b74 |
| mode-2-vector | 8x6 | 84fa995291bf956ee1d7d75a60fd5cd6d62d5878f59535a5102a8aca1131306e | a04e1cc82a1431a0e27e4ea5b31d23408d0f70db71ec2625f3df947ac3d3eaba |
| mode-3-scalar | 7x5 | 4c35dda6904032d948dc520085b2a1a4858ff37ba27d14ca2a48fa13b22e9717 | 9b1c4c0b021b6d00c8643fe279fbd8606b3737d2bf71c5cdec14b300bd89a62a |
| mode-3-vector | 8x6 | 90e648fabe380fdf940faf34e0b30769b92edbc1404eae4cd55f013f3137a5aa | 4165a62903feb736ef41129b38bb6dcd005d5f3eeaf429393fe374cf0ac9a4f7 |
| mode-4-scalar | 7x5 | 6e69f2ad474a5b8484a1b667b1bd0ae465c87189d0af2a364145bcccdf6344ca | c90c28ec13817ce657ac651fb59b855b4693a7818aeeaeab48d3dc60efc85518 |
| mode-4-vector | 8x6 | a4032079c448697f4a20477d8e80aac4e3d35b0a0070c9cc47130f6009603d0e | d98a053c17f65a0ab897ef39e5b393f77926e4cef9b2ce35d3c70b13723dbc99 |
| mode-5-scalar | 7x5 | 2b0d41210d65c2e2903da729273880c82e35485c90e6c080f9edd6ebb70ee5ab | b6adb542f964270a5f8688698deefcd9c748afe34df7e915c0ec99074dcd765d |
| mode-5-vector | 8x6 | 842d58aaf671255a71dce85bb2413f3dee121fa95f934568f03c31f55b1c9c93 | 58a34a0b614dac8d4ccb351a6c6a47ea0cf61b460990dd591bb29797d175009a |
| mode-6-scalar | 7x5 | 668f1aedbb2f7cd60f2dfd8fe7c7ce4d9623920e12449b9d6e0aa3d0b0f85540 | ea564fe3f645c33ce9cf08667a678f7eaf81f5353166826b2ec8a28e2c580356 |
| mode-6-vector | 8x6 | bdb531ecf898460dd2976c61ec8c0541705c0e2fff89fd3fa67f9ec6ed98f8e5 | cfb278713eb2b3a2d87f26a2614958a79d7a14b7f2e6376afd954a3282598de2 |
| mode-7-scalar | 7x5 | b0594a0dec868586e2dfceb33c0acc5eba9eb97b682762b39a664da18835e0da | 544909bdbb1ed37267d6d115020c68ad1a952042d8576e0bc02129f1cace1d77 |
| mode-7-vector | 8x6 | fb680789c9189e3efeedc19de216890f9ee0409e954b35166ff42d92776ce894 | f4ff179e88695e4f25b2bd046dc79a7e2188980eab1a1dbc49cfbadf1b460a31 |
| mode-8-scalar | 7x5 | ecdc13d879b64b8ddac16c03c0d66e43a0eac136a6c6518d0045f49b4b4bd8cb | 942ac1cad7b576f8ede600f0a4f39e802abf15faf64def94e8f8e4cc507fe68f |
| mode-8-vector | 8x6 | e47c1fc24cd37806bfe0953f7b154bced3f4e9252aedfa3038e8bdd70e4e5904 | f1f3748cea433cfd5772da5add933c1e6ff98c05e1c79e227929d236fe82e0b2 |
| mode-9-scalar | 7x5 | 16883924fb81e9c5d22358d05a6a1a735764563ea76d91db1b23a2747b89c1e2 | aff43ed2e0a260edf41b28f5bd3f35dddd8ab2ba2b6be0eda73b035f8bff6b93 |
| mode-9-vector | 8x6 | 8d45bc037163c6c8cc8383851694220be2f9da499f44cb927e3d1410a9f6fcf6 | bc5f8fcf615371c3a848b09061d40a32e9af0c34b651a43d67caa502cc111951 |
| palette-hsv | 9x5 | 4cae8c338a9c4e4d3dbe4cd7b6912d8df190f75edb8c77d38d6b25ce96168861 | 6bbd8056a77e645bb58f8e0d171c2a331ebf7b1e25777481815ca92d9f532326 |
| palette-oklab-lanes | 5x9 | 8783d94db5f1282fc631b3ab242dfce84ae8ead06fe04e6e8d9bb2a9472acc32 | 6de014554fa9fe093a5b0202a0baea1fd6de35439ca1c30adf9d682de443915a |
| palette-rgb-extremes | 9x5 | db875bd9b785d5694d89285911cb12b637d31f1e3b85b31dc78c95d6fa77938a | 006fb1fd8aae7368d4fc31074bc086d0dd5034a9a55909cdc6255d6f50af740d |
| animate-minus | 9x5 | a1468ad006b6425c4ec76c80e1b747b3d2b5499de15de5dae8aa6212ac127456 | 4c9b73749883e65032d6b2db8fd7b27f96b3dafdc357da88bfc88b28ae9971ac |
| animate-zero | 9x5 | c5143d8fa60c3fc5f0708a31504fa10aec41f32f7b5a32d70c52175f6719e542 | 80e12262217fe1addefec1c9da11a830b032693a27f7a4aba9bd6a1549827587 |
| animate-plus | 9x5 | a9a909840015459f4e73a4a1f00decfe11784a39e36b117e052a62375443786a | 34165f2b7d7949be38f6bc4fcd1759e7092162bea64d218b2299c5b61def4b51 |
| cycle-minus | 9x5 | 503ad3736bd2a53df61dd6fd25913b6afdf83a52f7704db22f9863d91c46fe15 | 7513fece717234de5d5637ea24cd9009d337054b12923a81d3a956cbb69e4aea |
| cycle-zero | 9x5 | 4085cb2380be25a223e13651c6acf1c79ae807241350dfe60b486fe52bb47e32 | 27541812f9952ebb3ac3ae7bcb39b10db39aab26ea6534500b2d6f4cad5d6955 |
| cycle-plus | 9x5 | ef2ad5cd078b7b2e227c38fe1a448807a3e11ee85b6ac16f31883d12c67e7580 | ff88889920936efd656ad97c6239ea3565b67f448e317f7b79c8b7dee769e64e |
| levels-one-scalar | 9x5 | a2f31238f59900e13980e4b67c153a7ca7402da1b587bc843e58881dad7f67c4 | e3c671208c2e2a11bcbcecd077245dbf7d2341cf1c504a629314cde51d6183b8 |
| levels-fractional-vector | 9x5 | f5df63e2373d301ec4ba1c7fd3f99ad1802fe76c88f11eeefc6d03d2e30816b9 | 86f8ee61953e0eb52338f9c6fdb1bf924b85dfea701fc4ee80c656f685399e55 |
| loopscale-min | 9x5 | faf5ef2c137c902e97a79a351faeaaed4ebc679699afaa8f667e3e40e0b9f1e2 | f1afe1c4ec1c1cb0282a621ece6959f8967afaeb7422da4da27806d2bb8c6c32 |
| loopscale-max | 9x5 | eb24e5ee05d61c39bdafa4c4fb6f4faad6368f78ef3b6bbb3d852edcf34c7a09 | 7677c029f362905eca89e7f71a2cd666680fd6cd67ca4c07fe53ad8ce724c09f |
| dead-random-neg-nowrap | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-neg-wrap | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-nowrap | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-wrap | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| tiled-fractional-ratio | 6x4 | de0eb6057a44449e0f966dbc8c5088a36fd3790b38f769fc8c9e96b986ab98c6 | 9608fcc149e6b0b5fd62024ac6f7915e0146c6e45412222fcedb94806b0e488f |
| sampler-edge-y | 9x7 | b3bfed94d3c8496dfd8f0bb53ca580d46e854b359071ac495a1b966b6f53f522 | 45d08a2f048bfe356e95c5a2e37d7379ae25f9cf728f287d5c851131b6905c46 |
| alpha-three-way | 3x1 | 5f94ac5cbb2d60e7b6244d78311cf476c1b2de8ec4ab5f9ee027ae9e36611e15 | 5a036fe39aea50f76164efc7fd360d59c87e0a8562d2eb32adf4e303c0d285ef |
| external-context-base | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| external-context-extreme | 9x5 | 30d45ca0c46235fae0dcb262e843c4703a18292cce2e75a6aed35a436439c664 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |

## Rendered behavioral mutations

| Mutation | Required witnesses | Changed lanes at first witness | First top-down x,y/channel |
| --- | --- | ---: | --- |
| vector-reflect-scale-sign | mode-7-vector | 144 | 0,0/r |
| vector-reflect-subtract-to-add | mode-7-vector | 144 | 0,0/r |
| vector-reflect-reversed-output-operands | mode-7-vector | 144 | 0,0/r |
| vector-reflect-defensive-normal-normalization | mode-7-vector | 144 | 0,0/r |
| vector-reflect-omit-product-f32 | mode-7-vector | 59 | 0,0/r |
| scalar-reflect-mathematical-dot | mode-7-scalar | 105 | 0,0/r |
| scalar-reflect-factor-association | mode-7-scalar | 105 | 0,0/r |
| vector-refract-wrong-k-formula | mode-8-vector, animate-minus, animate-plus | 144 | 0,0/r |
| vector-refract-omit-left-f32 | mode-8-vector | 54 | 0,0/r |
| vector-refract-omit-right-f32 | mode-8-vector | 72 | 0,0/r |
| scalar-refract-mathematical-dot | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-eta-association | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-omit-left-f32 | mode-8-scalar | 8 | 6,0/g |
| scalar-refract-omit-right-f32 | mode-8-scalar | 39 | 0,0/r |
| scalar-refract-omit-final-f32 | mode-8-scalar | 13 | 0,0/r |
| wide-mod-reversed-operands | mode-5-vector | 144 | 0,0/r |
| wide-mod-unmaterialized-divisor | mode-5-vector | 63 | 0,0/b |
| index-linear-condition-fixed-lane | palette-oklab-lanes | 37 | 0,0/b |
| index-srgb-low-write-fixed-lane | palette-oklab-lanes | 55 | 0,0/r |
| index-linear-low-read-fixed-lane | palette-oklab-lanes | 31 | 0,0/g |
| index-srgb-high-write-fixed-lane | palette-oklab-lanes | 97 | 0,0/r |
| index-linear-high-read-fixed-lane | palette-oklab-lanes | 59 | 0,0/b |
| linear-to-srgb-loop-bound-two | palette-oklab-lanes | 45 | 0,0/b |
| linear-to-srgb-branch-inverted | palette-oklab-lanes | 135 | 0,0/r |
| oklab-fwdB-transpose | palette-oklab-lanes | 135 | 0,0/r |
| oklab-fwdA-row-column | palette-oklab-lanes | 135 | 0,0/r |
| oklab-remove-fwdA-intermediate-f32 | palette-oklab-lanes | 94 | 0,0/r |
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
| blendy-half-removed | mode-5-vector, mode-7-vector, mode-8-vector | 128 | 0,0/r |
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
| input-filter-forced-nearest | mode-1-scalar, mode-3-vector | 48 | 2,0/a |
| second-filter-forced-nearest | mode-3-vector, sampler-edge-y | 71 | 0,0/a |
| input-y-convention-inverted | sampler-edge-y | 58 | 0,0/r |
| second-y-convention-inverted | sampler-edge-y | 146 | 0,0/r |
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
