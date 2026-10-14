# Glyph Map signed-shift, mask, and pixel-parity oracle

Frozen JavaScript ground truth for `filter/glyphMap:glyphMap`. Exact Float32 and RGBA8 hashes cover canonical and public execution, every glyph, both color branches, control boundaries, variant selection, tiling, repeatability, and input immutability. A separate typed-frontend proof freezes the exact global/shift/mask/return identities.

## Frozen authority

- Upstream snapshot revision: `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`
- Corpus revision: `6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d`
- GLSL source: 8145 bytes, SHA-256 `dc0af9a6a6fb4d0cd62ea25c4508a714a36a1dc66923f5578d91ac190d9f4dd6`
- Canonical factory: `canonicalFactory56`, 6826 bytes, SHA-256 `da7f49bffd02ea705db223296a620e20183b4b307fc8b5f0e0c505dd2045320c`
- Public catalog identity is exactly the canonical factory; no adapter override exists.

## Captured C++ frontend boundary

- Validator and emitter first error: `filter/glyphMap:glyphMap:287:16: unsupported binary operator &`
- Replacing only the exact mask node exposes `filter/glyphMap:glyphMap:287:16: unsupported binary operator >>`.
- Replacing only both scalar bit operators in memory makes validator and emitter pass; the diagnostic C++ is 17616 bytes with SHA-256 `ad46bd52432aef3e6921cd6dd7328830f03824af7ca2f4749995aaea10b17cab`.
- The proposed `glyph-map-nonnegative-int-shift-v1` profile authenticates `GLYPH_COUNT`, its three reads, the sole signed shift, its literal-one mask parent, the local `bit` materialization, and the direct `float(bit)` return. It does not establish general signed shifting or masking.

## JavaScript signed-word contract

The 16 numeric fixtures freeze ToInt32/ToUint32 truncation, modulo wrap, signed/unsigned views, signed zero, and nonfinite-to-zero behavior; their low words hash to `9d30a2d9a1479ccf1e23114f6ce4819b1412084579beba2042ec74d0febeabd9`. Mutations reject rounding, saturation, and premature Float32 narrowing.

The 17 word fixtures cover bit-31 clear/set words, -1, counts 0/1/31/32/33/-1/2^32-1, and nontrivial masks. Shipped JavaScript and independent BigInt two-complement recomputation agree exactly. Shift words hash to `2b22d478a1214a652dc3f2aa55095651cc8c0b17b0426c0fa2c6dd826e250646`; post-mask words hash to `d615140ff9a4eeae4dd1cb88e956cb85da369b982dbaa75c7888e8c194dbbdea`. Direct mutations reject logical shift, masking before shifting, OR/XOR masks, and count clamping.

Pixel renders intentionally cannot distinguish `>>` from `>>>`: authenticated glyph rows are nonnegative 0..31 and counts are 0..4. The logical-shift render mutant must therefore remain exactly equal while the direct signed fixtures must diverge. That division is part of the contract, not a coverage gap.

## Full glyph truth table (top-down rendered rows)

| Glyph | Rows | Float32 SHA-256 | RGBA8 SHA-256 |
| ---: | --- | --- | --- |
| 0 | `...../...../...../...../...../...../.....` | `0c29310078fd3de814bc8589145111ad99bcfcff8555a328f3a91a119d8e5538` | `bfc4362e6c3dc214f069838333c33bde4e95fb054b44fca5c8a76ac93edc4674` |
| 1 | `...../...../...../...../...../..#../.....` | `668b7f438fabaa8eaa516c410e060960018f44a007a0a406e7ad46da7c6c40ea` | `ac2673931dd46fd476e2ec417ba289e82374ec7f45567ec674f2dc39eda11218` |
| 2 | `...../..#../...../...../...../..#../.....` | `8453ed73c09872f08102668ebe674326d603e32b10849efe3c1d715143b7777d` | `1fda35a2206959fe6bbd112b78e76b57107ee74f5f60d81d281b0d03e0070795` |
| 3 | `...../...../...../.###./...../...../.....` | `150a477920ceb0ecad2d1297138779a1637afc2988c21aeb4f7fca705a9fd432` | `526921e76956e28c6a03224801017297f8402fd81dd0dd28df064ceca0c5cbc6` |
| 4 | `...../..#../..#../.###./..#../..#../.....` | `574e8b083f86bdb83e794e4836c345e7aeab7fb70ac6930747c6c6f09a8bd102` | `ee5d1fd73dcca1ad412196be4df2b886084c25fc5c1b0e36037028afd1f239a1` |
| 5 | `...../...../.###./...../.###./...../.....` | `bbdbba8a94bf363b999229c4b62dd169a09acfa2010944c83a5ec113c2d61f13` | `9828a085d506a32ea879d8d634939422d8d33c984d283e007dd557969f6abc15` |
| 6 | `...../.#.#./..#../.###./..#../.#.#./.....` | `c87d8a875afaccde3dc6eeb7bf49f92e037a1aea222f874d5f64bff63459c8f4` | `90f3a87a801356e400b429b3b89ccf289618c71b6cd9f4d73762d7185f5e7af1` |
| 7 | `...../...../.###./.#.#./.#.#./.###./.....` | `a9011cf8f20fde6e3d897bbc1015fbe0fd20669086ab2bc34f9daf689d95208a` | `0d6a3900aeaa89c4bb6e5171f706c82c691b0ec6e1b00660c4e3f140536ee03f` |
| 8 | `...../.#.#./.#.#./..#../.#.#./.#.#./.....` | `8f56b489556e131f7ce9855545d2644614a746d3f54482d36d77e65169ff0da6` | `ec2d93425e5d63e3026e5ca04d8d7c5826ccf50bd19b58246b04061e4a1b7939` |
| 9 | `...../.#.#./#####/.#.#./#####/.#.#./.....` | `3065c9ee828abc3ae6575738664923eb33264c74a84737f0e1ba7a8bfa1db4b8` | `b7c7792493cc1f6e6a1d3003e8f361584cc633408884a1cbe597012b95e6f456` |
| 10 | `##..#/##.#./..#../.#..#/.#.##/#..##/.....` | `c3850922a03fbf4aa57952072f213a581803333de198cf7488f6fe10836242a1` | `a8749bef27e341d40808678befabf247f801702fcfc8dd28a32ed9010140b666` |
| 11 | `..#../.#.#./#...#/#####/#...#/#...#/.....` | `80209cf9cba6032fc6fb924a3818252cc17f9ce91f8ee5ce1c2d76ff82766d5a` | `f40d2675d754bc443d64233555cbb4b6e78c9bc217feb9adf9299113d3b68625` |
| 12 | `#...#/#...#/#.#.#/#.#.#/##.##/.#.#./.....` | `a3ce9067248c8006304cf98be6f54fbae26b185afae0c25cd96ce1c5b49eeb76` | `1a0cdc8d035fbac27c26f01e2837885f67e72d163452a633ad76bffd084f8ee9` |
| 13 | `#...#/##.##/#.#.#/#.#.#/#...#/#...#/.....` | `fdc1bf4c112f3da4333237acd78e4c70c985333cca9f01497cee2f7ff8231108` | `aa1d81a7ba0b6099377dc4d042a824bd7a3facdfaa15b42f5d0505bfb4d812ab` |
| 14 | `.###./#...#/#.###/#.#.#/#.##./#..../.###.` | `f92c8752d5c6b24ad28fb157eac3e9b3963657aa32ce01fea34138729fa0dc9f` | `c857cafe54e7a457185fa438453f68173b8d93615dac568ee9bca94749fff097` |
| 15 | `#####/#####/#####/#####/#####/#####/#####` | `48b453891479327f14f3e45e21a23a415ba3af378f3da919cd912a48866e472c` | `c713f7a6cbdfb091d09ee4264823c7bd5c8dd48e1cfa457a6bf255a7bc444ee5` |

## General render cases

| Case | Size | Cell | Seed | Mode | Scale | Tile/full | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| mono-min-cell-pattern | 19x15 | 4 | 1 | 0 | 1 | 0,0/19,15 | `afb5fb5d45bfab209c8ff417e4124ad4d08c92cb5faa597f990f7189af4f7e15` | `e58c2a636885b780fdc28dc4d7474ca0993b73d1cb1765ced83660d85900f1a8` |
| rgb-default-pattern | 19x15 | 16 | 1 | 1 | 1 | 0,0/19,15 | `0cd79cc961dcaf65bc9f0d64b3cc9dd8747314b8a3331f9213099323d9e96874` | `a446cf3e64af0c587d8ffa667f1f17db451032d05927c44e384e8f917a23006d` |
| rgb-variant-two-seed | 23x17 | 7 | 2 | 1 | 1 | 0,0/23,17 | `1f4d11179bb37180a7d3cb249cc769545fe72ed2fef14eb3393bd0e351773459` | `b7cb96cca9d6d904f0b82861fcf6303c6dfbe4289b387e04cb2a63ca4d05b2b8` |
| scale-zero-cs-one | 7x11 | 4 | 100 | 0 | 0 | 0,0/7,11 | `07110a6cdf3075fb98f5d1bbda4b7cbd75ded61cc45de1c6b09c0135ed605ef2` | `ca25b6a4fd644d91e92e434e4a20b59bff22f682816906de24a0103e40936f61` |
| tiled-noninteger-scale | 11x9 | 7 | 37 | 1 | 1.5 | 7,5/31,23 | `cde28f5e6763a126eb508615e1c55d89ea5165d91fbff5dafa68cd1740e58f83` | `4461316b3dfd9735e3682c4983b656b64addd9ca104c047a720815cfaf7267bc` |
| origin-tile-zero-offset | 520x256 | 32 | 37 | 1 | 32 | 0,0/1040,256 | `238f1d8557d1fb13585de360a50784cf9774e93925fcd7b6e8fd83a75633ec27` | `87f51a4f06952bf95fd5199677c905b6e52753f5e211a97caa43e727640fdbe3` |
| untiled-zero-offset-control | 520x256 | 32 | 37 | 1 | 32 | 0,0/520,256 | `7147bb96771ec90d144627719eb082f0afd59b773b9da3e9dc110d85a19753c8` | `f383b8064ad4d438e012f5dc3e5e31ae605c16d93171fa1c0f66315af0673a82` |
| tiled-cs-cap-1024 | 5x7 | 32 | 3 | 0 | 32 | 1,1/9,9 | `4d2dc9cdbac54d7b6c8800a91bf969ea3d08dd32c24eaa6a0387a7f40e35f88d` | `3957236455d5befc513321b54222c48f168471ba09faadc9d4d8854812b88c0a` |
| tiled-cs-cap-512 | 5x7 | 32 | 3 | 0 | 16 | 1,1/9,9 | `4d2dc9cdbac54d7b6c8800a91bf969ea3d08dd32c24eaa6a0387a7f40e35f88d` | `3957236455d5befc513321b54222c48f168471ba09faadc9d4d8854812b88c0a` |
| external-context-base | 13x8 | 5 | 11 | 1 | 1 | 0,0/13,8 | `f3bfc940931b619015adbfa9b58505a0ec88f5deef4ec24eb6d96b0a104d3820` | `465c23c9a9838b5abd00e89874b7e2bf6b6c6a49a470311e44fb38c9ed316686` |
| external-context-extreme | 13x8 | 5 | 11 | 1 | 1 | 0,0/13,8 | `f3bfc940931b619015adbfa9b58505a0ec88f5deef4ec24eb6d96b0a104d3820` | `465c23c9a9838b5abd00e89874b7e2bf6b6c6a49a470311e44fb38c9ed316686` |

Every render case requires exact repeated-run identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. The cap pair and external-context pair are required exact identities.

## Render mutation discrimination

| Mutation | Expected render relation | Required witnesses | All divergent cases |
| --- | --- | --- | --- |
| mask-and-replaced-by-or | diverge | glyph-01-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, origin-tile-zero-offset, untiled-zero-offset-control, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| right-shift-replaced-by-left | diverge | glyph-03-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, origin-tile-zero-offset, untiled-zero-offset-control, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| mask-materialized-before-shift | diverge | glyph-03-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, origin-tile-zero-offset, untiled-zero-offset-control, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| arithmetic-shift-replaced-by-logical | equal-under-authenticated-range |  | (none, required) |
| color-mode-branch-inverted | diverge | mono-min-cell-pattern, rgb-default-pattern | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, origin-tile-zero-offset, untiled-zero-offset-control, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| variant-two-decrement-omitted | diverge | rgb-variant-two-seed | mono-min-cell-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, origin-tile-zero-offset, untiled-zero-offset-control, external-context-base, external-context-extreme |
| origin-tile-reverts-to-offset-detection | diverge | origin-tile-zero-offset | origin-tile-zero-offset |

Frontend contract negatives reject wrong key/profile/hash, global value drift, mask/count drift, an extra signed shift, and return-route drift.

## Regeneration

From the repository root. Ordinary checks remain durable after admission; `--live-frontier` separately observes the current production gate:

```sh
python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --check
python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --live-frontier
node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs --write --cpu-root <authenticated-archive> --ledger <archive-ledger>
node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs --check --cpu-root <authenticated-archive> --ledger <archive-ledger>
```

