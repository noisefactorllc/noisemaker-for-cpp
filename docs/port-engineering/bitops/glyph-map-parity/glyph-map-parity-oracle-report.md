# Glyph Map signed-shift, mask, and pixel-parity oracle

Frozen JavaScript ground truth for `filter/glyphMap:glyphMap`. Exact Float32 and RGBA8 hashes cover canonical and public execution, every glyph, both color branches, control boundaries, variant selection, tiling, repeatability, and input immutability. A separate typed-frontend proof freezes the exact global/shift/mask/return identities.

## Frozen authority

- Upstream snapshot revision: `117a236679d1db3ab8f0e278230ece277b57564c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source: 7838 bytes, SHA-256 `853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1`
- Canonical factory: `canonicalFactory58`, 6749 bytes, SHA-256 `2f26c6821b4cddd8eca6f742b5c6f9b4fb2aafc7660f9421965abb4af11d8028`
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
| 1 | `...../..#../...../...../...../...../.....` | `03ae0abbf0da0386fc09e377bb5e82d5f19c283ca586216dd3680f7ea6e16b65` | `17305802881ecef394cdbb7be61caee780d4b5bdf10dc2e8619a7a0db5ce32cd` |
| 2 | `...../..#../...../...../...../..#../.....` | `8453ed73c09872f08102668ebe674326d603e32b10849efe3c1d715143b7777d` | `1fda35a2206959fe6bbd112b78e76b57107ee74f5f60d81d281b0d03e0070795` |
| 3 | `...../...../...../.###./...../...../.....` | `150a477920ceb0ecad2d1297138779a1637afc2988c21aeb4f7fca705a9fd432` | `526921e76956e28c6a03224801017297f8402fd81dd0dd28df064ceca0c5cbc6` |
| 4 | `...../..#../..#../.###./..#../..#../.....` | `574e8b083f86bdb83e794e4836c345e7aeab7fb70ac6930747c6c6f09a8bd102` | `ee5d1fd73dcca1ad412196be4df2b886084c25fc5c1b0e36037028afd1f239a1` |
| 5 | `...../...../.###./...../.###./...../.....` | `bbdbba8a94bf363b999229c4b62dd169a09acfa2010944c83a5ec113c2d61f13` | `9828a085d506a32ea879d8d634939422d8d33c984d283e007dd557969f6abc15` |
| 6 | `...../.#.#./..#../.###./..#../.#.#./.....` | `c87d8a875afaccde3dc6eeb7bf49f92e037a1aea222f874d5f64bff63459c8f4` | `90f3a87a801356e400b429b3b89ccf289618c71b6cd9f4d73762d7185f5e7af1` |
| 7 | `...../.###./.#.#./.#.#./.###./...../.....` | `72e77304d18653c6fc109987019be28efa831081e1fdf21e48d9d4e5951acbc0` | `de95ce6103b64bc6364e85872924f353b16757b90d4d94633b01aaa566931507` |
| 8 | `...../.#.#./.#.#./..#../.#.#./.#.#./.....` | `8f56b489556e131f7ce9855545d2644614a746d3f54482d36d77e65169ff0da6` | `ec2d93425e5d63e3026e5ca04d8d7c5826ccf50bd19b58246b04061e4a1b7939` |
| 9 | `...../.#.#./#####/.#.#./#####/.#.#./.....` | `3065c9ee828abc3ae6575738664923eb33264c74a84737f0e1ba7a8bfa1db4b8` | `b7c7792493cc1f6e6a1d3003e8f361584cc633408884a1cbe597012b95e6f456` |
| 10 | `...../#..##/.#.##/.#..#/..#../##.#./##..#` | `64ac8cf85cc476b380b5104832688f0e84e672613a0684877d04f891aee66cc9` | `67a1eb93c52ecd64a770d24e84a9c70a31ec701cc63a282721372fd0c93f41f3` |
| 11 | `...../#...#/#...#/#####/#...#/.#.#./..#..` | `4035df02a3329685d83bec3a634e6224c875ad32078b5861ae2c9ea5708102ec` | `6a005d8e07e3b2bb2951d86c09196c62e1f08ae5a90b7fdc23ad481eb63ee105` |
| 12 | `...../.#.#./##.##/#.#.#/#.#.#/#...#/#...#` | `069b4cc8d035b31146ea5ce59a3a7805608ebf158870b75b403e44ebef9327b2` | `8a8bb2c74ad6a866090921887b7959ca7a8ca55a80c372106b84d149e30d0b56` |
| 13 | `...../#...#/#...#/#.#.#/#.#.#/##.##/#...#` | `8004c32f1e2a19a13594bcd6f8aeb2c85d729c983cbd1a9c3b240f15ea045ce9` | `11d16e20ba71e8b306681f632bcbcd1b45e2743ab3fb52dce4bb347cd7afe2f0` |
| 14 | `.###./#..../#.##./#.#.#/#.###/#...#/.###.` | `83acd171a379f2c9a35e448e7a210cf67409c7e328653c29877b34112b8d104d` | `73e784cacb7015d99ad838825a55efa439e34eaa916b61a815f9a7e759936338` |
| 15 | `#####/#####/#####/#####/#####/#####/#####` | `48b453891479327f14f3e45e21a23a415ba3af378f3da919cd912a48866e472c` | `c713f7a6cbdfb091d09ee4264823c7bd5c8dd48e1cfa457a6bf255a7bc444ee5` |

## General render cases

| Case | Size | Cell | Seed | Mode | Scale | Tile/full | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| mono-min-cell-pattern | 19x15 | 4 | 1 | 0 | 1 | 0,0/19,15 | `2490a0308c6d434f91531923046200c057cadf783248d659fd654e290c11a69e` | `34c63f6bc50823bf299d1c30bbe0f9f1bad440c90c26addbf73887136fd377f7` |
| rgb-default-pattern | 19x15 | 16 | 1 | 1 | 1 | 0,0/19,15 | `897ebf5620d8271196b4ed3e692f7c924a5174823b738a785eaca60e7f02be6f` | `44396746d97926eeabefefa71fcbc7d815d5c2bfdae49297aa9f416eb7a4b38e` |
| rgb-variant-two-seed | 23x17 | 7 | 2 | 1 | 1 | 0,0/23,17 | `6b796e2f4cb920e6326beee29e3dbeea76407b0c00263ea853c8eb19b909c7bd` | `665252f326c0a17dd7a90211161413113e0313ca6e5bc31bdd0cdbce8eeea585` |
| scale-zero-cs-one | 7x11 | 4 | 100 | 0 | 0 | 0,0/7,11 | `07110a6cdf3075fb98f5d1bbda4b7cbd75ded61cc45de1c6b09c0135ed605ef2` | `ca25b6a4fd644d91e92e434e4a20b59bff22f682816906de24a0103e40936f61` |
| tiled-noninteger-scale | 11x9 | 7 | 37 | 1 | 1.5 | 7,5/31,23 | `772482a71743a25db150987804364e53b1147e14733ed091a2255b11ec1f7423` | `6cb74296f58e2607ced03baf74360c8ece50ef9723cc1d4f7a27ffc4268efc79` |
| tiled-cs-cap-1024 | 5x7 | 32 | 3 | 0 | 32 | 1,1/9,9 | `4d2dc9cdbac54d7b6c8800a91bf969ea3d08dd32c24eaa6a0387a7f40e35f88d` | `3957236455d5befc513321b54222c48f168471ba09faadc9d4d8854812b88c0a` |
| tiled-cs-cap-512 | 5x7 | 32 | 3 | 0 | 16 | 1,1/9,9 | `4d2dc9cdbac54d7b6c8800a91bf969ea3d08dd32c24eaa6a0387a7f40e35f88d` | `3957236455d5befc513321b54222c48f168471ba09faadc9d4d8854812b88c0a` |
| external-context-base | 13x8 | 5 | 11 | 1 | 1 | 0,0/13,8 | `881b37251f44e58c02d27dce296e99e026f79ffa4866007bb5c1672fb6265c64` | `d30e30a5e0ef342f1837e3b34443b5076d660db0ce4e382e9ce6aba3e596a735` |
| external-context-extreme | 13x8 | 5 | 11 | 1 | 1 | 0,0/13,8 | `881b37251f44e58c02d27dce296e99e026f79ffa4866007bb5c1672fb6265c64` | `d30e30a5e0ef342f1837e3b34443b5076d660db0ce4e382e9ce6aba3e596a735` |

Every render case requires exact repeated-run identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. The cap pair and external-context pair are required exact identities.

## Render mutation discrimination

| Mutation | Expected render relation | Required witnesses | All divergent cases |
| --- | --- | --- | --- |
| mask-and-replaced-by-or | diverge | glyph-01-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| right-shift-replaced-by-left | diverge | glyph-03-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| mask-materialized-before-shift | diverge | glyph-03-full-cell, glyph-14-full-cell | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| arithmetic-shift-replaced-by-logical | equal-under-authenticated-range |  | (none, required) |
| color-mode-branch-inverted | diverge | mono-min-cell-pattern, rgb-default-pattern | mono-min-cell-pattern, rgb-default-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, external-context-base, external-context-extreme, glyph-01-full-cell, glyph-02-full-cell, glyph-03-full-cell, glyph-04-full-cell, glyph-05-full-cell, glyph-06-full-cell, glyph-07-full-cell, glyph-08-full-cell, glyph-09-full-cell, glyph-10-full-cell, glyph-11-full-cell, glyph-12-full-cell, glyph-13-full-cell, glyph-14-full-cell |
| variant-two-decrement-omitted | diverge | rgb-variant-two-seed | mono-min-cell-pattern, rgb-variant-two-seed, scale-zero-cs-one, tiled-noninteger-scale, external-context-base, external-context-extreme |

Frontend contract negatives reject wrong key/profile/hash, global value drift, mask/count drift, an extra signed shift, and return-route drift.

## Regeneration

From the repository root. Ordinary checks remain durable after admission; `--live-frontier` separately observes the current production gate:

```sh
python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --check
python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --live-frontier
node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs
node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs --check
```

