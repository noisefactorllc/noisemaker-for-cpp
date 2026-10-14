# Shape Mixer182 exact-parity oracle

Program `classicNoisedeck/shapeMixer:shapeMixer`; corpus revision `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`; exact define `LOOP_OFFSET=10`.

## Result

The clean canonical JavaScript authority produced 42 fixtures: 20 mode-matrix cases and 22 focused cases. Every fixture stores complete independent input and output Float32 words, canonical RGBA8 bytes, filters, bindings, probes, finite census, and canonical-repeat/public-canonical identity. Input pre/post SHA-256 and immutability are frozen independently for canonical, canonical-repeat, and public-catalog routes. No C++ output contributes expected data.

The JavaScript comparer rejects shape and payload-count mismatch before iteration, then checks every raw Float32 word and every independently supplied RGBA8 byte. Signed zero, distinct quiet-NaN payloads, the final alpha lane, and a byte-only mismatch are self-tested.

## Render fixtures

| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| mode-0-scalar | 7x5 | e381b30b5d7eb8cd55a3201f748342f4c0c5536aaee9bb9ad7a0b4905050fdf2 | 9a30cd4b47a69c5a4531d0b847c7018e37f8efe1d14fb982714599fb0d054157 |
| mode-0-vector | 8x6 | 3687b94b30e7e20554cf0ab62e62490331532691ba32023aefa0ac1f623ae2b0 | 27cfd3519e733b3a194a12c768c736e3911d40844ade8fa5e7b49a33c3e07e5a |
| mode-1-scalar | 7x5 | f8b097f035a14ac9665fea1fc340a532e793a1f37f1aada7ce6e53ee8b7fa7a8 | a973b32fc02e37d126c93f79098e4a4994ef65a41ff91e57c912a53c7bb3264f |
| mode-1-vector | 8x6 | 3b45a4b839a0aeb54be74b88f6c97a21dd51e05974a1de089b64ee3e199d2a14 | 01a48bc1a669ce2c76020b05f439a5845406c6574bcd1ee75470fee26e18b4c6 |
| mode-2-scalar | 7x5 | 32c9783ae9227c0ff7987df718c3e1ea1599f5ccf4af09168676426d3d54d664 | 6dfade1fb1a2203343a464496f2980ad7abb7ba9e2ace3032552209d16356b74 |
| mode-2-vector | 8x6 | 0584dc8ebf7993739acce1194547458e61bd0a17c9ffa89f3afbe1ffa95d43d3 | a04e1cc82a1431a0e27e4ea5b31d23408d0f70db71ec2625f3df947ac3d3eaba |
| mode-3-scalar | 7x5 | 897aadd230aa229207e28542e03e862da38f424174651ba264c20716773254fe | 9b1c4c0b021b6d00c8643fe279fbd8606b3737d2bf71c5cdec14b300bd89a62a |
| mode-3-vector | 8x6 | f251993620139111b8385251ec5c406df8aadc0757ecdce35651f8e0b9beaad9 | 4165a62903feb736ef41129b38bb6dcd005d5f3eeaf429393fe374cf0ac9a4f7 |
| mode-4-scalar | 7x5 | 4d885f29e95cdd701fce9281f2cda4992ac17014e6d408f19f28700e7f9d7ae2 | c90c28ec13817ce657ac651fb59b855b4693a7818aeeaeab48d3dc60efc85518 |
| mode-4-vector | 8x6 | 08b8eb84303da84724ee37e44e1647464c04cf1be504332d6912f0af83bd1e91 | d98a053c17f65a0ab897ef39e5b393f77926e4cef9b2ce35d3c70b13723dbc99 |
| mode-5-scalar | 7x5 | 60ff63914a364b7297d5a06bb303e80810496c7795823ff7a2f5a15bf57355bc | b6adb542f964270a5f8688698deefcd9c748afe34df7e915c0ec99074dcd765d |
| mode-5-vector | 8x6 | 0608cbc0a803de11e107eb734f32923d87a9c946a3910d61870f5446d9292a09 | 58a34a0b614dac8d4ccb351a6c6a47ea0cf61b460990dd591bb29797d175009a |
| mode-6-scalar | 7x5 | 14c503fd4b43cdd874fb962522969cb535ec7a27f357042a943ab9ac98cf1ba9 | ea564fe3f645c33ce9cf08667a678f7eaf81f5353166826b2ec8a28e2c580356 |
| mode-6-vector | 8x6 | 04e6e17700c774af6d562ee1ea5cd78e3f32c55a317a43814bfb9d312a0492ef | cfb278713eb2b3a2d87f26a2614958a79d7a14b7f2e6376afd954a3282598de2 |
| mode-7-scalar | 7x5 | b0594a0dec868586e2dfceb33c0acc5eba9eb97b682762b39a664da18835e0da | 544909bdbb1ed37267d6d115020c68ad1a952042d8576e0bc02129f1cace1d77 |
| mode-7-vector | 8x6 | 4f4488ccb72afb7bad6ba3122a9c2e0787fc38d64fdcd59f546d207a41b3202d | f4ff179e88695e4f25b2bd046dc79a7e2188980eab1a1dbc49cfbadf1b460a31 |
| mode-8-scalar | 7x5 | d1a7e488d78370dd37ace36373fd7d0c06a7d968ab7f28cb5ead3be173748f52 | 942ac1cad7b576f8ede600f0a4f39e802abf15faf64def94e8f8e4cc507fe68f |
| mode-8-vector | 8x6 | 07837386af5c8398d7b903121062b03837769799a82955460b37f5949ea57514 | f1f3748cea433cfd5772da5add933c1e6ff98c05e1c79e227929d236fe82e0b2 |
| mode-9-scalar | 7x5 | 5f20841a7c1987afda142fb8745bdb39207e2064b72d32c34b939a00dd8da4f2 | aff43ed2e0a260edf41b28f5bd3f35dddd8ab2ba2b6be0eda73b035f8bff6b93 |
| mode-9-vector | 8x6 | 2b35cddab542e1eff36eb184b0946fa9a23fe18635e24e3ba717dd6f3b83aa4c | bc5f8fcf615371c3a848b09061d40a32e9af0c34b651a43d67caa502cc111951 |
| palette-hsv | 9x5 | 4cae8c338a9c4e4d3dbe4cd7b6912d8df190f75edb8c77d38d6b25ce96168861 | 6bbd8056a77e645bb58f8e0d171c2a331ebf7b1e25777481815ca92d9f532326 |
| palette-oklab-lanes | 5x9 | 8783d94db5f1282fc631b3ab242dfce84ae8ead06fe04e6e8d9bb2a9472acc32 | 6de014554fa9fe093a5b0202a0baea1fd6de35439ca1c30adf9d682de443915a |
| palette-rgb-extremes | 9x5 | db875bd9b785d5694d89285911cb12b637d31f1e3b85b31dc78c95d6fa77938a | 006fb1fd8aae7368d4fc31074bc086d0dd5034a9a55909cdc6255d6f50af740d |
| animate-minus | 9x5 | 570be662d2bf14790f7456cb9b332a60813f89a46e2ff59c1b37c25393544257 | 4c9b73749883e65032d6b2db8fd7b27f96b3dafdc357da88bfc88b28ae9971ac |
| animate-zero | 9x5 | a3db2d109237bf74030a10ec2beb4f691ebfe01db1cb6bcea11813798a2d7cd3 | 80e12262217fe1addefec1c9da11a830b032693a27f7a4aba9bd6a1549827587 |
| animate-plus | 9x5 | cedad02cbe6beb39321b8bd5fdaf99d0ed241365373ef08085d3efa6d8706204 | 34165f2b7d7949be38f6bc4fcd1759e7092162bea64d218b2299c5b61def4b51 |
| cycle-minus | 9x5 | 503ad3736bd2a53df61dd6fd25913b6afdf83a52f7704db22f9863d91c46fe15 | 7513fece717234de5d5637ea24cd9009d337054b12923a81d3a956cbb69e4aea |
| cycle-zero | 9x5 | 4085cb2380be25a223e13651c6acf1c79ae807241350dfe60b486fe52bb47e32 | 27541812f9952ebb3ac3ae7bcb39b10db39aab26ea6534500b2d6f4cad5d6955 |
| cycle-plus | 9x5 | ef2ad5cd078b7b2e227c38fe1a448807a3e11ee85b6ac16f31883d12c67e7580 | ff88889920936efd656ad97c6239ea3565b67f448e317f7b79c8b7dee769e64e |
| levels-one-scalar | 9x5 | a2f31238f59900e13980e4b67c153a7ca7402da1b587bc843e58881dad7f67c4 | e3c671208c2e2a11bcbcecd077245dbf7d2341cf1c504a629314cde51d6183b8 |
| levels-fractional-vector | 9x5 | f5df63e2373d301ec4ba1c7fd3f99ad1802fe76c88f11eeefc6d03d2e30816b9 | 86f8ee61953e0eb52338f9c6fdb1bf924b85dfea701fc4ee80c656f685399e55 |
| loopscale-min | 9x5 | 33680fa1e55befebfdebf7c2ac901dfea85fce6e27586569558662a8527f7260 | f1afe1c4ec1c1cb0282a621ece6959f8967afaeb7422da4da27806d2bb8c6c32 |
| loopscale-max | 9x5 | 62d91a84004cccc436bc478f91eba37b3e0d4d2c87e341c2d80b083e2e0a96ff | 7677c029f362905eca89e7f71a2cd666680fd6cd67ca4c07fe53ad8ce724c09f |
| dead-random-neg-nowrap | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-neg-wrap | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-nowrap | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| dead-random-max-wrap | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| tiled-fractional-ratio | 6x4 | 173c9a2afde09711fb19b566aca05e4560048f20544842a318cea65ab84370ee | 9608fcc149e6b0b5fd62024ac6f7915e0146c6e45412222fcedb94806b0e488f |
| sampler-edge-y | 9x7 | b3bfed94d3c8496dfd8f0bb53ca580d46e854b359071ac495a1b966b6f53f522 | 45d08a2f048bfe356e95c5a2e37d7379ae25f9cf728f287d5c851131b6905c46 |
| alpha-three-way | 3x1 | 5f94ac5cbb2d60e7b6244d78311cf476c1b2de8ec4ab5f9ee027ae9e36611e15 | 5a036fe39aea50f76164efc7fd360d59c87e0a8562d2eb32adf4e303c0d285ef |
| external-context-base | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |
| external-context-extreme | 9x5 | b8f87b87fe6511918c68f725585440d0a5413a24d50571c7a3849ce94ef6f153 | 5e610b33742becc1d774ff351eab56c6a0a4675c3d4202b0e0933f19a150831f |

## Rendered behavioral mutations

| Mutation | Required witnesses | Changed lanes at first witness | First top-down x,y/channel |
| --- | --- | ---: | --- |
| vector-reflect-scale-sign | mode-7-vector | 144 | 0,0/r |
| vector-reflect-subtract-to-add | mode-7-vector | 144 | 0,0/r |
| vector-reflect-reversed-output-operands | mode-7-vector | 144 | 0,0/r |
| vector-reflect-defensive-normal-normalization | mode-7-vector | 144 | 0,0/r |
| vector-reflect-omit-product-f32 | mode-7-vector | 58 | 0,0/r |
| scalar-reflect-mathematical-dot | mode-7-scalar | 105 | 0,0/r |
| scalar-reflect-factor-association | mode-7-scalar | 105 | 0,0/r |
| vector-refract-wrong-k-formula | mode-8-vector, animate-minus, animate-plus | 144 | 0,0/r |
| vector-refract-omit-left-f32 | mode-8-vector | 56 | 0,0/r |
| vector-refract-omit-right-f32 | mode-8-vector | 62 | 0,0/r |
| scalar-refract-mathematical-dot | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-eta-association | mode-8-scalar | 105 | 0,0/r |
| scalar-refract-omit-left-f32 | mode-8-scalar | 10 | 5,0/g |
| scalar-refract-omit-right-f32 | mode-8-scalar | 34 | 0,0/r |
| scalar-refract-omit-final-f32 | mode-8-scalar | 13 | 0,0/r |
| wide-mod-reversed-operands | mode-5-vector | 144 | 0,0/r |
| wide-mod-unmaterialized-divisor | mode-5-vector | 62 | 0,0/b |
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
