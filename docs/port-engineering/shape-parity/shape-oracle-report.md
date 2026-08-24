# Shape184 exact-parity oracle

Program `synth/shape:shape`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; exact defines
`LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30`.

## The two contracts this program exists to prove

`synth/shape` declares two mutable uninitialized file-scope globals with **different** numeric
contracts, and the parity target is the transpiler's materialization, not GLSL semantics:

| Global | JavaScript | Contract | Mutant | Discriminable |
| --- | --- | --- | --- | --- |
| `aspectRatio` | `var aspectRatio = 0;` | plain Number, a **double**, never narrowed to f32 | `shape-aspect-f32-narrowed` | yes |
| `globalCoord` | `new Float32Array([0, 0])` | **f32 lanes**, every lane store narrows | `shape-globalcoord-unnarrowed` | yes |

A port that types `aspectRatio` as `float` because GLSL says `float` diverges, and a port that
keeps `globalCoord` in double lanes diverges. Both halves have a render witness here.

The shipped binding set also contains an unrelated `aspectRatio` uniform. The factory-scope
`var aspectRatio` shadows it and it is never read; the generator fails closed if that ever changes.

## Authority

This oracle is produced by the unmodified public canonicalFactory274 from an immutable noisemaker-for-cpu snapshot, executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates. The generator refuses to run unless
`kernelFactories.get(key) === canonicalKernelFactories[key]`, the factory is named
`canonicalFactory274`, its `Function.prototype.toString` SHA-256 is `870d97a811e5720f827f5616057483a43b27224240ac95c04a8084dd257a6125`, neither
adapter table owns the key, `canonicalAdapterFactories` matches its
11-key census exactly, the key is absent from the
4-key `check_corpus._ADAPTERS` eligibility table
**parsed out of the live `tools/glslcpp/check_corpus.py`**
rather than transcribed, all six pinned CPU files match, and every module in the
22-file import closure resolves by real path beneath the immutable snapshot.
Bare module specifiers other than `node:` builtins are rejected, and the live checkout is refused as
a `--cpu-root`.

No absolute path is recorded anywhere in this package. The `--cpu-root` argument is stored as
`<immutable-cpu-snapshot-root>` and the rejected live checkout as
`<live-noisemaker-for-cpu-checkout>`, resolved at run time from
process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu. The import closure and the six pinned
hashes authenticate the snapshot completely, so the literal path authenticates nothing while binding
`--check` to one directory on one machine. The gate therefore passes against a valid snapshot at any
path.

## Bindings

The program has exactly 10 runtime bindings:
`time`, `seed`, `wrap`, `resolution`, `tileOffset`, `fullResolution`, `loopAScale`, `loopBScale`, `speedA`, `speedB`.
`LOOP_A_OFFSET` and `LOOP_B_OFFSET` are compile-time defines recorded separately and are never
counted as bindings. `resolution` is declared and never read by the program; it remains a required
ABI binding and is not "cleaned up".

## Render fixtures

| Case | Size | Route | wrap | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| shape-landscape-16x9 | 16x9 | full | false | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | b6f413f381f5b34eb8efa7bc85159a77f93d22f7acb372f6b2fba0c8323dc1fa |
| shape-crop-1280x720 | 40x24 | tile | true | 9f66e527ca97201a6c5102999729ec5bfc8a314996c490597dd118686403323e | 9ed74f1e20549dc9a27a6e909e88bc951c10bed98231afec30b0edbf1332a496 |
| shape-square-12 | 12x12 | full | false | 1ca0bdd331d7d5cf01ef1547409e69041db30cc85fc73db32fa887205941d6e5 | 5c34887d8c665b5573f4cb645244da4d75288dc740a79688520b8edd0b914b72 |
| shape-portrait-9x16 | 9x16 | full | true | c4577f3982aea3b2f1d8f4f8c26ddb2b2a9d4ac89cb05e7eff9143606226ec14 | 2f123fabb539f5d5aedacef067557cd8364ed81f2b7c23e1ebcda5ed97d702f2 |
| shape-zero-speeds | 16x9 | full | false | c8a0219b9191bba318304cfa5bb6861d98b9dbcb3bbcfd4171ca4048ffe60f57 | a240facb7a0d5897b5826bfa52dee1963929a424e1e2d78dd2f72cd5a85cbcdf |
| shape-wrap-live-37-61 | 4x6 | tile | true | a8aeffa8f49441b080e1606d1e5a2d87bc195a924efb659cc47b276803e37acf | c870f2fde9212887b9b0a31a8f70bdc42ef1e32b1dc26dfaab72d1a14111072f |
| shape-negative-speeds | 16x9 | full | false | 6012d8a139bc7cd486e97d4f24a950062f3f281a30055983ca153eb2d859ae52 | 7a4bed09b7ee38b7549e6a48be7746c2e187c44519987003eaef46efb9b33884 |
| shape-extreme-tile-offset | 16x12 | tile | false | 36228ff8361dcca60ecf28957962cbeb159c1fb36f525c0d73e17d8d46ed5941 | 1cf291f20b67654f0c4098ec22a8a5078b905912d0f158e91302307fee8dc177 |

Every case stores exact dimensions, all 10 bindings with every float and vector lane as a
hexadecimal f32 word, the external `runPass` time/seed pair, the complete expected Float32 word
array, the complete independently captured RGBA8 byte array, finite/non-finite lane counts, and a
SHA-256 over each array. Alpha is exactly `0x3f800000` / `255` in every case and every route.

### Deviations from `shape-design.md` section 6.2, and why

All eight design cases are present and every coverage claim they carry is honoured. Four deviations,
each recorded here rather than absorbed silently.

| Design | Shipped as | Change | Reason |
| --- | --- | --- | --- |
| `shape-landscape-64x36` | `shape-landscape-16x9` | 2,304 px to 144 px | 64/36 and 16/9 are the same rational, so the `aspectRatio` double is bit-identical. The control group renders four one-axis variants of the anchor, so the anchor's area is multiplied by five in the stored document. |
| `shape-square-48` | `shape-square-12` | 2,304 px to 144 px | ratio is exactly 1.0 either way; this is a non-reaching control |
| `shape-portrait-36x64` | `shape-portrait-9x16` | 2,304 px to 144 px | ratio is exactly 0.5625 either way; this is a non-reaching control |
| `shape184_*` filenames (design section 6) | `shape_*` | `shape_oracle_generator.mjs`, `shape-oracles.json`, `shape-oracle-report.md`, `tests/oracles/shape_expected.inc` | the unversioned names were specified for this package; the C++ namespace remains `shape184_oracle` and the schema remains `…shape184.pixel-parity.v1`, so the typed-row identity is unchanged |
| `shape-crop-1280x720` full route | stored as the 40x24 **crop window** only | the whole 1280x720 array is not stored | the proof needs only the window (3,840 words + 3,840 bytes, the size of a tile array), so the full route is rendered in memory, compared, and discarded. The translation is re-derived from the stored window, and `shape-wrap-live-37-61` additionally re-derives its tile from a stored 11x9 full route. |

The design warns that two cases with the same aspect ratio can differ in whether they discriminate,
so none of these substitutions is assumed to inherit its coverage. Every one is **re-measured** by
this generator on every run, and the per-case ledger below is what `--check` enforces.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
| aspect_exactly_f32_representable | no | shape-landscape-16x9, shape-crop-1280x720, shape-wrap-live-37-61, shape-negative-speeds, shape-zero-speeds, shape-extreme-tile-offset |
| aspect_exactly_f32_representable | yes | shape-square-12, shape-portrait-9x16 |
| aspect_shape | landscape | shape-landscape-16x9, shape-crop-1280x720, shape-zero-speeds, shape-negative-speeds, shape-extreme-tile-offset |
| aspect_shape | portrait | shape-portrait-9x16 |
| aspect_shape | square | shape-square-12 |
| aspect_shape | tile_portrait_of_landscape_full | shape-wrap-live-37-61 |
| tiling | tiled | shape-crop-1280x720, shape-wrap-live-37-61, shape-extreme-tile-offset |
| tiling | untiled | shape-landscape-16x9, shape-square-12, shape-portrait-9x16, shape-zero-speeds, shape-negative-speeds |
| wrap | true | shape-crop-1280x720, shape-portrait-9x16, shape-wrap-live-37-61 |
| wrap | false | shape-landscape-16x9, shape-square-12, shape-zero-speeds, shape-negative-speeds, shape-extreme-tile-offset |
| wrap_liveness | live_non_integral_lf | shape-wrap-live-37-61 |
| wrap_liveness | inert_integral_lf | shape-landscape-16x9, shape-crop-1280x720, shape-portrait-9x16, shape-zero-speeds, shape-negative-speeds, shape-extreme-tile-offset |
| wrap_liveness | inert_wrap_false_non_integral_lf | shape-square-12 |
| speed_a_sign | positive | shape-landscape-16x9, shape-crop-1280x720, shape-portrait-9x16, shape-wrap-live-37-61, shape-extreme-tile-offset |
| speed_a_sign | negative | shape-square-12, shape-negative-speeds |
| speed_a_sign | zero | shape-zero-speeds |
| speed_b_sign | positive | shape-landscape-16x9, shape-crop-1280x720, shape-square-12, shape-extreme-tile-offset |
| speed_b_sign | negative | shape-portrait-9x16, shape-wrap-live-37-61, shape-negative-speeds |
| speed_b_sign | zero | shape-zero-speeds |

## Top-down crop normalization

Both runners store rows top-down while GLSL fragment coordinates are bottom-left. The
`shape-wrap-live-37-61` case is a genuine crop: `tileOffset = (crop_x, full_height - crop_y - tile_height)`. For crop
`(4, 2)` of size
`4x6` from
`11x9`, the tile route binds
`tileOffset` words `0x40800000, 0x3f800000`; the other 8 bindings are held identical.
Tile output equals the corresponding top-down crop of the full-route output exactly:
0 word mismatches and 0 byte mismatches.
Binding raw top-down `crop_y` into `tileOffset.y` instead changes
72 lanes, so the witness is not vacuous.

`shape-crop-1280x720` proves the same rule at production scale. Its full
`1280x720` route is rendered in
memory and discarded; only the
`40x24`
window it yields is stored, and the tile equals it exactly:
0 word mismatches and
0 byte mismatches. Binding raw
`crop_y` there changes 2880 lanes.
The full 1280x720 route is rendered in memory and discarded; storing all 3,686,400 Float32 lanes is not viable, but the proof needs only the 40x24 window, which is stored above and re-derived against the tile array by the materializer. st = globalCoord / fullResolution[1] is two orders of magnitude larger here than in the 11x9 proof, so a translation defect that only appears at large fullResolution is caught by this case.

## One-axis control group on `shape-landscape-16x9`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| external-pass-extreme | external runPass time/seed words (0x4f000000, 0xcf000000) | identical | identical | pass | 0 |
| bound-time-ten | bound time 0x3f000000 -> 0x41200000 | differs | differs | pass | 423 |
| bound-seed-123 | bound seed int32 3 -> 123 | identical | identical | pass | 0 |
| bound-wrap-true | bound wrap false -> true | identical | identical | pass | 0 |

## Bound-seed liveness census

| Bound seed | Float32 SHA-256 | Versus baseline |
| --- | --- | --- |
| -2147483648 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| -7 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 0 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 1 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 3 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 123 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 65537 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |
| 2147483647 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc | identical |

At defines LOOP_A_OFFSET=40 / LOOP_B_OFFSET=30 the only main() consumers of the `seed` uniform are the two offset(...) calls. Offset 40 selects the `loopOffset >= 40 && loopOffset <= 120` arm, which dispatches shape(st, sides, freq*0.5) and never reads seedVal; offset 30 selects the absolute-distance arm, which also never reads seedVal. Every seed consumer listed above sits behind the 300..380 arm, which these defines do not select.

shape-design.md section 4.2 records bound `seed` as proven invariant at 40/30 and explicitly instructs this package NOT to require it to differ. The eight probes above are the measurement backing that instruction.

## Bound-wrap liveness census

| Case | loopAScale / loopBScale | lf_a / lf_b | lf | wrap flipped | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| shape-landscape-16x9 | 1 / 1 | 6 / 6 | integral | identical | 0 |
| shape-wrap-live-37-61 | 37 / 61 | 4.181818181818182 / 2.9696969696969697 | non-integral | differs | 69 |

wrap only reaches the output through `lf = floor(lf)`. It is inert wherever lf = map(loopScale, 1, 100, 6, 1) is already integral and live wherever it is not.

## Speed sign/zero census on `shape-landscape-16x9`

| speedA | speedB | Float32 SHA-256 |
| ---: | ---: | --- |
| 50 | 50 | 68d140d08cf71256a2853a547239992b10af044e130641c3eebb007b95365edc |
| 50 | 0 | df6c831cc234d36717b7cd07a7bd9f43458892e88a1c1557212d71097a656d97 |
| 0 | 50 | e7b3638c1010c1265eb1f4c55e94552d772efaacf91811788a0f83295f1341a2 |
| -50 | 50 | 062335c6ff1ef2ed1069c2d10783c2c91381f9f24793c400bb94d59a1b825692 |
| 50 | -50 | bc47a6defafdc93c4a9cdc2f0cef96e52f31601e18378f4d9bc70f1544a6ce4b |
| -50 | -50 | c983b9637878234758355f205a70d060cd429f6d626767ce6219b23e4eb6dd4c |
| 0 | 0 | c8a0219b9191bba318304cfa5bb6861d98b9dbcb3bbcfd4171ca4048ffe60f57 |
| -50 | 0 | c198207b5040d116e33aeed98356216e55d10b916afe348859e519e31c87d31a |
| 0 | -50 | 878ede338316903a086b09bf04b619d699a020d771b3a927a9587c9b07c9cafd |

All 9 combinations are pairwise distinct.

## globalCoord witness census

| tileOffset | f32 words | Result | Changed lanes |
| --- | --- | --- | ---: |
| [0, 0] | 0x00000000, 0x00000000 | no | 0 |
| [8.25, 4.5] | 0x41040000, 0x40900000 | no | 0 |
| [1048576.5, 0] | 0x49800004, 0x00000000 | no | 0 |
| [16777216, 0] | 0x4b800000, 0x00000000 | discriminates | 36 |
| [131072.1, 0] | 0x48000006, 0x00000000 | no | 0 |
| [131072.1, 0.3] | 0x48000006, 0x3e99999a | discriminates | 24 |

the f32-lane contract on globalCoord is only observable where gl_FragCoord.xy + tileOffset leaves the exactly-representable f32 range; ordinary tile offsets leave it unwitnessed

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
| shape-aspect-f32-narrowed | shape-landscape-16x9 | witness | differs | 42 |
| shape-aspect-f32-narrowed | shape-crop-1280x720 | witness | differs | 393 |
| shape-aspect-f32-narrowed | shape-square-12 | control | identical | 0 |
| shape-aspect-f32-narrowed | shape-portrait-9x16 | control | identical | 0 |
| shape-aspect-f32-narrowed | shape-zero-speeds | control | identical | 0 |
| shape-aspect-f32-narrowed | shape-wrap-live-37-61 | witness | differs | 9 |
| shape-aspect-f32-narrowed | shape-negative-speeds | witness | differs | 18 |
| shape-aspect-f32-narrowed | shape-extreme-tile-offset | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-landscape-16x9 | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-crop-1280x720 | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-square-12 | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-portrait-9x16 | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-zero-speeds | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-wrap-live-37-61 | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-negative-speeds | control | identical | 0 |
| shape-globalcoord-unnarrowed | shape-extreme-tile-offset | witness | differs | 144 |

Both mutants are independent one-anchor/one-replacement rewrites of the canonical factory text,
compiled and rendered by this generator. The expected outcome is frozen **per case and per mutant**;
`--check` fails if any single cell flips, in either direction. The native implementation must match
only the unmutated oracle, and no hand-mutated generated C++ is committed.

## Native binding witness for the globalCoord contract

`shape-design.md` section 12 could not determine whether `shape-extreme-tile-offset` survives the
C++ binding path. **It does.** `globalcoord_native_binding_witness` stores
384 f32 words -- `globalCoord.x` and
`globalCoord.y` for each of the 16x12
pixels -- produced by an instrumented probe factory built from the canonical text by one
anchor/one replacement. It is never compared to a rendered shade and is not a parity array. Phase 2
binds `tileOffset` to words `0x48000006, 0x3e99999a`, evaluates
`glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset)`, and must reproduce every word.

## Claim boundaries

- With defines 40/30 the randomFromLatticeWithOffset body, its three scalar uint XOR sites, and the circles/rings/diamonds/value arms are conservative call-graph reachable but are not entered by a normal full render. These full-surface cases must never be cited as proof that any of them executed.
- Normalized/typed source, function, interface, and whole-program hashes are the frontend profiles’ authority and are deliberately not restated here.
- The bound `seed` uniform is a required int32 ABI binding but is pixel-inert at the default defines; see seed_liveness_census. It is recorded as proven invariant, not waived.
- The bound `wrap` uniform is live only where lf is non-integral. Exactly one case witnesses the live half; see wrap_liveness_census.
- The globalCoord f32-lane contract is witnessed by exactly one render case, shape-extreme-tile-offset. It is NOT a structural-only claim: the case is expressible end-to-end through the C++ binding ABI, and globalcoord_native_binding_witness carries the per-pixel lane words phase 2 must reproduce.
- shape-crop-1280x720 exercises the tileOffset rule at 1280x720 but its full route is not stored; the translation proof is carried by shape-wrap-live-37-61.

## Regeneration

```sh
node docs/port-engineering/shape-parity/shape_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/shape-parity/shape_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --self-test
```

Both generators are fail-closed and check mode performs no writes.
