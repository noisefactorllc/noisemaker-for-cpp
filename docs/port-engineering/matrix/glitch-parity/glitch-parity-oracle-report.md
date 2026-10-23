# Glitch exact-parity oracle

Program `classicNoisedeck/glitch:glitch`; corpus revision `32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3`.

## Result

The currently shipped JavaScript reference materializes every matrix-product element through `F32(sum)` into a pooled `Float32Array`. The exact target is column-major, left-associated `(T*Q)*S`, with a float32 store after `T*Q` and after the final product. The older plain-Array/no-intermediate-narrowing claim is stale and is actively rejected by this package.

The reachable matrix closure is exactly three `mat4` constructors, two nested `mat4*mat4` nodes, and one `vec4*mat4` node, all in the live `bicubic` function. The current typed frontend authenticates the full bicubic chain and its return route against the exact a1a3 GLSL source. Wrong source hashes and profile carriers fail closed.

## Exact contract

- Float output uses raw little-endian float32 lane words; there is no tolerance.
- RGBA8 output uses exact encoded bytes and never substitutes for Float32 parity.
- The custom comparer rejects equal-byte-length dimension mismatches, distinguishes +0 from -0, and reports the first top-down pixel/channel and both lane words.
- Every render is repeated, compared through the public-catalog identity, checked finite, and proves input-surface immutability.
- Time ingress is checked at one fixed lane: canonical Float32 `0x3f2dfc68`, raw binary64 `0x3f2dfc6e`.

## Direct matrix fixtures

| Case | Left-associated SHA-256 | Right-association mismatched lanes | Unrounded-intermediate mismatched lanes |
| --- | --- | ---: | ---: |
| identity-q | d0a0329be70a2c456732dd1ceb4013d481b04cc3a5ea3a9d67b594de16ab2244 | 0 | 0 |
| fractional-q | b65c9f13623dcf8acd325f14a056a0cf747a0772d4ebb529984dfeadc75c03a5 | 4 | 3 |
| wide-dynamic-q | daf3699fafcc2b273320b3fb6a463bd224e6e8bf8af792ee293279ba78252bb9 | 3 | 1 |
| pcg-shaped-q-a | 303e734d9d4eea2c089fafe3e9cb805226c952ff357bdf8357384c9838831768 | 1 | 1 |
| pcg-shaped-q-b | 98ca17191f978d3fceaa784be9010cfaf5b7a4736766a41b030c4edb5f88c94c | 1 | 0 |

These fixtures call the real shipped `GlslCpuRuntime.stdlib.matrixMult` and independently compare it with a literal `F32(sum)` implementation. Crafted fractional/dynamic-range matrices discriminate both association and the obsolete unrounded-intermediate model.

## Render fixtures

| Case | Size | Seed | Scanlines | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | --- | --- |
| matrix-masked-control | 9x7 | 1 | 0 | 5c37b773a4ee6e5fdca3e7e6f706cef8292843e03346d7a3862a45a9d9faffa4 | 1a4f5661a45951cbaf878d33c9943d7d71c5b48c6dc8ca901ef9656f86623a2c |
| scanlines-max-seed-one | 11x9 | 1 | 100 | e2d5a447f71f71e330c1a754eef4a7ec73d9ff2af2c05a6d7e978ab8607ca34f | 1c6365833f1ab510bac28fff814bb230144809bdf62f61766a8a905534054d38 |
| scanlines-mid-seed-thirty-seven | 13x10 | 37 | 77 | dce3ae02179ebe668671b69358a520c46e20553962f49cbdba81ad4ebd72b552 | 62c9a94a0074c290c83f0f3f339e5407a61fa5a112233360b231fc21e919a1e4 |
| scanlines-min-nonzero | 17x6 | 100 | 1 | 304ea75d40b980e418c4270b105849e7d10e68dfeab1dd4884c8c89abe0bbe1d | 7f51a24b06d6994fa973005b23c73e5764a04f526c586cc7e8a36cd16832f751 |
| aspect-negative-lens-vignette | 7x12 | 99 | 91 | 60cb28c7b54525aee681b2b7336d922031b113daecea7df4c5ac52aa6f5ddf51 | 8db36265535fcc6de70fb9deeb2f69d3037460a9ed8f859d914c313f60f04aa4 |
| snow-upper-midpoint | 8x8 | 2 | 63 | e850ccdebc789265a4f2747f310838db9a2c812f9a66a1746feb080d436c1a61 | 490e98f1cfa649e6273aee5ba49321c570ec6c1ffd33eae2623d169784c8917f |
| snow-saturated-tiled | 6x5 | 73 | 88 | ecac2d53127699c55cf7ab9e1e542c68a4ea8ee06b163a0eff677e4fd13567a7 | 46223df666bb4b8b51651fdb54e97604523820660adcd9c4e659c8e3a9b7f103 |
| fractional-full-resolution-tile | 5x9 | 41 | 56 | c6b566b5a70b290201ef83f064be0f0f3c1b4428868313a30c2bb76c8f522fd3 | 049db190f87941b08b396a4517400b08db275885edfea7a2f5bbf4e6b1479893 |

The suite covers matrix-masked control, maximum and minimum nonzero scanline influence, seed/time extremes, both aspect-lens states, both distortion branches, both vignette branches, all three snow regions, and tiled full-resolution coordinates.

## Render mutation discrimination

| Mutation | Required witnesses | All Float32-divergent cases | All RGBA8-divergent cases |
| --- | --- | --- | --- |
| right-associated-chain | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette | (none; Float32 remains authoritative) |
| missing-intermediate-f32-stores | scanlines-mid-seed-thirty-seven, snow-upper-midpoint | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint | (none; Float32 remains authoritative) |
| reverse-inner-operands | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |
| swap-basis-matrices | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |
| omit-basis-products | scanlines-max-seed-one | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, scanlines-min-nonzero, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile | scanlines-max-seed-one, scanlines-mid-seed-thirty-seven, aspect-negative-lens-vignette, snow-upper-midpoint, fractional-full-resolution-tile |

The matrix-masked control must remain exact for every mutant. The active-scanline witnesses distinguish wrong association, missing intermediate float32 stores, reversed inner operands, swapped basis matrices, and omitted basis products. RGBA8 is recorded but Float32 bits are the binding contract.

## Frontend fail-closed proof

`tools/glslcpp/frontend/glitch_mat4_chain_profile.py` authenticates the exact current source/key/profile/hash, matrix nodes, nested left-association, symbol route, call-graph reachability, and bicubic return route. The oracle generator runs ten fail-closed negatives: wrong profile, key and caller hash, plus coefficient, association, operand-order, matrix-use, constructor-arity, vector-orientation and return-route mutations. Independent profile tests also check these paths.

## Provenance observation

The oracle uses the immutable CPU revision `4307ca9f26fc415e4fc5e75227d429d35cc741cd` and authenticates its import closure, pinned runtime and catalog files, canonical factory text, and the exact a1a3 Glitch GLSL source before rendering.

## Regeneration

From the repository root:

```sh
NOISEMAKER_PYTHON=<python-3.14> NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>
<python-3.14> -B tools/glslcpp/generate_glitch_native_oracle_include.py --check```

The generator verifies pinned source/runtime/catalog/factory hashes before executing the real unmodified canonical factory. `--check` regenerates the JSON and report in memory and requires byte-for-byte identity.
