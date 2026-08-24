# Blur binary64 boundary and pixel-parity oracle

Frozen JavaScript ground truth for `filter/blur:blurH` and `filter/blur:blurV`. Float32 and RGBA8 hashes are exact byte contracts. The custom comparer adds first-pixel/channel diagnostics without relaxing exact equality.

## Binding boundary

The admitted radius is computed from the original JavaScript Number (IEEE-754 binary64) bindings. The selected axis must be finite and in `[0,50]`; `renderScale` must be finite and nonnegative; their binary64 product must be in `[0,64)`. Truncation toward zero then yields radius `0..63`, so the symmetric loop performs at most 127 visits. Values at or above 64 are rejected, never clamped.

| Boundary | Axis | Scale | Binary64 accepted | Radius | Faulty operand-Float32/product-binary64 accepted | Discriminator |
| --- | ---: | ---: | --- | ---: | --- | --- |
| axis-zero | 0 | 1 | true | 0 | true | false |
| scale-zero | 50 | 0 | true | 0 | true | false |
| radius-one | 1 | 1 | true | 1 | true | false |
| fractional-truncates-to-three | 7 | 0.5 | true | 3 | true | false |
| metadata-axis-maximum | 50 | 1 | true | 50 | true | false |
| immediately-below-64-operand-quantized-false-reject | 1 | 63.99999999999999 | true | 63 | false | true |
| exactly-64 | 1 | 64 | false | - | false | false |
| exactly-64-operand-quantized-false-accept | 50 | 1.28 | false | - | true | true |
| negative-axis | -5e-324 | 1 | false | - | true | true |
| axis-above-metadata-max | 50.99999999999999 | 1 | false | - | false | false |
| negative-scale | 1 | -5e-324 | false | - | true | true |
| axis-positive-infinity | Infinity | 1 | false | - | false | false |
| scale-positive-infinity | 1 | Infinity | false | - | false | false |
| axis-nan | NaN | 1 | false | - | false | false |
| scale-nan | 1 | NaN | false | - | false | false |

The boundary table models a specific fault: quantize both operands to Float32, then multiply those quantized values in binary64. Its two explicit threshold discriminators run in opposite directions: the binary64 value immediately below 64 is valid radius 63 even though operand quantization produces 64, while `50 * 1.28` is exactly 64 in binary64 and must be rejected even though the quantized operands multiply to less than 64. The separate pixel mutation named `float32-rounded-product` keeps the original operands and rounds only the completed product.

## Pixel cases

| Program | Case | Size | Filter | Radius | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| blurH | radius0-axis0-nearest | 9x5 | nearest | 0 | `b17b6bdc9c84a09ac69720787b30466e699fb32300d609856b01d79abc4a9f0a` | `e782ed95cd7c856750ed5efa792b73b455e3fc0715a7b245bd5ce775d6e10224` |
| blurH | radius0-scale0-linear-degenerate-width | 1x7 | linear | 0 | `aa072c86a48a5f79bad3d905351d34d733896c0f20757956e91b87be62c6a7c3` | `b605c4638deae386983ba2273618af669610e13717852bba7305695b99d46094` |
| blurH | radius1-axis1-nearest | 11x6 | nearest | 1 | `52aecddecc780c2efd6b65ce6fd2099c1f0538e96b84cbfaa06712eabba03dac` | `d7dcd3c0bc34dd560ea00302018e658e15f460f569b8f28b3ba334d8af485952` |
| blurH | radius3-fractional-scale-linear | 10x7 | linear | 3 | `44f5d7e5b42713ed789049db9664320d866854e546abaca588661be50392fbb3` | `57270ab45368e4b3cca8973afb993b126dd956704f20e9e499362184d3bdc75b` |
| blurH | radius12-intermediate-nearest | 13x8 | nearest | 12 | `86b83315376daaf25cfdf2df1bb2f1cd5ba1b55d3366bc01b62dce63f93093ec` | `430409232505ddc798afee9ddf1f6c8a10e75944af2cfee6e76ef77723eacf6d` |
| blurH | radius50-axis-max-linear | 14x9 | linear | 50 | `61ac339e9421deb1bdd27bf62d50fa46c48d72fe36bae5defde80f608feccb8d` | `f89bc4abe0687b44cffa24728d63d090f8afd5a5606ed562653b3d61c9efb621` |
| blurH | radius12-degenerate-width-nearest | 1x8 | nearest | 12 | `6da26f0d20495c7ed2f29cdb257f730e35de790d5f03b2b582485df810faa4a2` | `5ee43bf4a139aca1c7f80cf2d7729c0902692ea519a236a872cb7e18cc87c1a3` |
| blurH | radius63-binary64-nextdown-large-scale | 8x6 | nearest | 63 | `36c158dddba082736e74e3746648cebd9934598f1949459b1a932a0eaed8aaa4` | `3ecb38c82328b6767132f5a8c54ddd910849ec6c914dc94008aba8b076210d0e` |
| blurV | radius0-axis0-nearest | 6x9 | nearest | 0 | `e7c833f8f8024d621399538082fb7ca8b9a453abf79444d301d1e2bf9903be52` | `b276d9ad3aee65c7a034a758ebe291ff87b871642e5db493fb75874a2b6a7bdb` |
| blurV | radius0-scale0-linear-degenerate-height | 7x1 | linear | 0 | `b509999a38839830ae90850b329464e118626b3a5f28527c2cab4e9371e17b1e` | `b2d2fc589994cb4c890e1cfb363bcfaf292cf6985ee69b81a56876ed51424ac1` |
| blurV | radius1-axis1-nearest | 6x11 | nearest | 1 | `96fe33249367bcee2eb6c13a7cb109cba31a6e89e099376ea0d4043df8cb7239` | `450917439b4c7c322435a7017d2234546d1c6b8c0aa340ba15de537b71573cd5` |
| blurV | radius3-fractional-scale-linear | 7x10 | linear | 3 | `3234725523110c738c048caf691a2fb3c5467f74d5476831f40db4e4dcb8536b` | `0646166c0d52663c944aab186c1f2090cdee8c44d80782305404b6a924b53bd1` |
| blurV | radius12-intermediate-nearest | 8x13 | nearest | 12 | `f4bad06eac9bf46ba2c2b09428d582be26a14291e273b4216e8965a2e7cd4f23` | `d68bbe0d4924f1f60ca0f7f249de1a485322ac4837ddd2bce695dc7b54047bd3` |
| blurV | radius50-axis-max-linear | 9x14 | linear | 50 | `945685f281d5eabcc9024f56bd45d945ff158693cab161df7504b2054147643e` | `489316672c06530dadf1bb3226851c43854cc12e783349a2d578aaceb4584838` |
| blurV | radius12-degenerate-height-nearest | 8x1 | nearest | 12 | `707fdba9fbc1884765a2b5b4685481108f01cdbd032482427ba92b3b23204696` | `5ef312999a01766bfa2eb37c62e638f234a521b48672c0c2afcb2fb579fd224e` |
| blurV | radius63-binary64-nextdown-large-scale | 6x8 | nearest | 63 | `8fd0516e335d5ee2546aabd239479208047bb825b96f1a25878b0b9a5b925436` | `a7aab16e9cda22abfd65a61a6ec37b54e68d641147baf0cda3a0421dced991d3` |

Every accepted case passes exact repeated-render identity, exact input immutability, finite output, and public-catalog-versus-direct-canonical equality. The fixture covers radius 0, 1, intermediate values, metadata maximum 50, and boundary maximum 63; zero, fractional, ordinary, and large scales; nearest and linear input filters; non-square images; valid 1-pixel axes; and four clamp-to-edge corners plus a center probe.

## Mutation discrimination

| Program | Mutation | Kind | Divergent Float32 cases | Divergent RGBA8 cases | Compared cases |
| --- | --- | --- | ---: | ---: | ---: |
| blurH | blurH-oracle-a-upper-off-by-one | trip_count_off_by_one | 6 | 5 | 8 |
| blurH | blurH-oracle-a-upper-minus-two | trip_count_swap | 6 | 5 | 8 |
| blurH | blurH-axis-swap | axis_swap | 6 | 6 | 8 |
| blurH | blurH-coordinate-wrap-instead-of-clamp | coordinate_wrap | 5 | 5 | 8 |
| blurH | blurH-radius-ceil | altered_truncation | 3 | 3 | 8 |
| blurH | blurH-float32-rounded-product | float32_rounded_product | 1 | 1 | 8 |
| blurV | blurV-oracle-a-upper-off-by-one | trip_count_off_by_one | 6 | 4 | 8 |
| blurV | blurV-oracle-a-upper-minus-two | trip_count_swap | 6 | 5 | 8 |
| blurV | blurV-axis-swap | axis_swap | 6 | 6 | 8 |
| blurV | blurV-coordinate-wrap-instead-of-clamp | coordinate_wrap | 5 | 5 | 8 |
| blurV | blurV-radius-ceil | altered_truncation | 3 | 3 | 8 |
| blurV | blurV-float32-rounded-product | float32_rounded_product | 1 | 1 | 8 |

Both original Oracle A loop mutations are retained for each axis. Additional exact controls transpose the blur axis, modulo-wrap coordinates before the canonical clamp sampler, replace truncation with ceil, and round the completed binary64 product to Float32 before integer conversion. The coordinate-wrap control is intentionally not described as a complete bilinear repeat sampler. Every mutation is machine-required to diverge under both exact Float32 and exact RGBA8 comparison on at least one frozen case.

## Provenance

- Upstream snapshot revision: `c51037ad9e60850b74490c01a9eecf08c7d28e8c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- blurH GLSL SHA-256: `c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc`; canonical factory SHA-256: `a735ebfa7bbdfd8da062c52f46dd2c3143be5526dfb2be805581437d21134d99`
- blurV GLSL SHA-256: `cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b`; canonical factory SHA-256: `439400fdbb3496fb6399769f5652ab7eb57f71a8e3d770bbdd111c8d2220f796`
- Node reference engine used to freeze this file: `v24.7.0`
