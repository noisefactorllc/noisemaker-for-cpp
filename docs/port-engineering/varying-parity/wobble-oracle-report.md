# Wobble exact-parity oracle

Program `filter/wobble:wobble`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; no preprocessor defines.
This is the first **varying-admission** oracle: the parity target is the materialization of
`in vec2 v_texCoord;` (raw `wobble.glsl:14`), which the JavaScript equates with `context.uv` -- the
pixel center's destination-local coordinate, aliased per pixel by `beginPixel` and copied by the canonical
kernel. There is no vertex stage, no interpolation, and no varying binding; every expected array below is
bound implicitly through the pinned pass-runner path.

## The contract this program exists to prove

| Fact | Value |
| --- | --- |
| GLSL declaration | `in vec2 v_texCoord;` (raw line 14; one read, zero writes) |
| JavaScript slot | `var v_texCoord = new Float32Array([0, 0]);` (factory scope, NOT pooled) |
| Per-pixel copy | `v_texCoord.set($runtime.varyings["v_texCoord"])` |
| Runtime alias | `this.varyings.v_texCoord[0] = uv[0]` / `[1] = uv[1]` in `beginPixel` |
| Numeric contract | per-lane f32, single narrowing, double product: F32((x + 0.5) * (1 / width)) and F32((height - y - 0.5) * (1 / height)) (pass-runner.js); all downstream copies are f32 to f32 |
| Discriminator case | `range-zero-passthrough` (range = 0: pure `texture(inputTex, applyWrap(v_texCoord))` pass-through) |

At `range = 0`, `offsetScale = r * (0.01 + speed * 0.02) = 0` pins the offset to +-0 and every wrap arm is
the identity on the open unit interval, so the case degenerates to a pure pass-through of the varying.
**Measured: the two varying mutants are the ONLY ledger mutants that move a lane there.** Any materialization
error -- lane order, y orientation, f32 drift -- lands exactly on that case.

## Authority

This oracle is produced by the unmodified public canonicalFactory178 from an immutable noisemaker-for-cpu snapshot, executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates. The generator refuses to run unless
`kernelFactories.get(key) === canonicalKernelFactories[key]`, the factory is named
`canonicalFactory178`, its `Function.prototype.toString` SHA-256 is `e09f2ef4c49b33b06febfac20d4eeea3563270f6edab6cb1f6761f2dd20759d4`, neither
adapter table owns the key, `canonicalAdapterFactories` matches its
11-key census exactly, the key is absent from the
4-key `check_corpus._ADAPTERS` eligibility table
**parsed out of the live `tools/glslcpp/check_corpus.py`**
rather than transcribed, all six pinned CPU files match, and every module in the
22-file import closure resolves by real path
beneath the immutable snapshot. Bare module specifiers other than `node:` builtins are rejected, and
the live checkout is refused as a `--cpu-root`.

The `Function.prototype.toString` pinning method is itself cross-validated at every run: the same snapshot
must reproduce cellrefract186's frozen factory-text digest
`329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3` or this generator refuses to start.

No absolute path is recorded anywhere in this package. The `--cpu-root` argument is stored as
`<immutable-cpu-snapshot-root>` and the rejected live checkout as
`<live-noisemaker-for-cpu-checkout>`, resolved at run time from
process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings

The program has exactly 5 runtime bindings:
`inputTex`, `time`, `speed`, `range`, `wrap`. There are no preprocessor defines.
`wrap` is a float uniform in the GLSL (`uniform float wrap;`) narrowed at use (`int mode = int(wrap);`, `wrap|0` in the JavaScript -- ToInt32 of the same Number), never an int32 binding. The control group pins the narrowing: an absent wrap behaves as mirror (undefined | 0 === 0) and 0.5 truncates to mirror while 1.5 truncates to repeat.

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| range-zero-passthrough | 16x9 | full | 16x9 | 1da28f42701d2f0b3325201dc4869112047f54c1b78e992eed5a3820c4e82ebe | 39dc033dc02a77ce97e057e05912b51ac5bcb7acf51980503bb05b30250c6fe3 |
| live-mirror-max-range | 16x9 | full | 16x9 | a2772468330300c2827bef94dccb35d0101269fcbf79d3abe2f8cd19a824607e | fdfddb9211aae2b6097642fac7a897090ac4fb6b86a47d989f95cd6ec48537cd |
| live-repeat-portrait | 9x16 | full | 9x16 | f9547b0ecf99638980cf22f4c6e287fde150730df1ca32792ff13d3d96a76f7d | 5aa658f36c813d511f2a9b6bce6cb74ff353b4b919349cd9b5ea4e86de6e4ed3 |
| tile-crop-translation | 5x6 | tile | 11x9 | cf530344553cb802cf6a749d32942f4f8b6ffb9927029c62ceac00299f5545da | 9ca8b308321524538f829fbe30cd9a7c725f14d04c2a89c78719f8e9cda5a3a4 |

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
5 bindings with every float lane as a hexadecimal f32 word, the external
`runPass` time/seed pair, the complete expected Float32 word array, the complete independently captured
RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each array. Every input lane is a small
dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
| wrap_arm | mirror_wrap_0 | range-zero-passthrough, live-mirror-max-range |
| wrap_arm | repeat_wrap_1 | live-repeat-portrait |
| wrap_arm | clamp_wrap_2 | tile-crop-translation |
| wrap_crossing | no_crossing_wrap_identity | range-zero-passthrough |
| wrap_crossing | x_lane_crosses | live-mirror-max-range |
| wrap_crossing | y_lane_crosses | live-repeat-portrait, tile-crop-translation |
| route | full | range-zero-passthrough, live-mirror-max-range, live-repeat-portrait |
| route | tile | tile-crop-translation |
| input_pattern | ramp | range-zero-passthrough, live-repeat-portrait |
| input_pattern | contrast | live-mirror-max-range |
| input_pattern | full-ramp | tile-crop-translation |
| destination_shape | 16x9 | range-zero-passthrough, live-mirror-max-range |
| destination_shape | 9x16 | live-repeat-portrait |
| destination_shape | 5x6 | tile-crop-translation |
| range | zero_pure_passthrough | range-zero-passthrough |
| range | maximum_5 | live-mirror-max-range, live-repeat-portrait, tile-crop-translation |
| speed | speed_5 | range-zero-passthrough, tile-crop-translation |
| speed | speed_2 | live-mirror-max-range |
| speed | speed_4 | live-repeat-portrait |
| varying_discriminator | pure_pass_through | range-zero-passthrough |
| varying_discriminator | offset_live | live-mirror-max-range, live-repeat-portrait, tile-crop-translation |

## Tile translation: probed before asserting, and NO crop identity holds on any arm

Per the cellrefract section 15 lesson the crop question was probed, not assumed, and the range = 0 arm
(the design's "plausibly sound" arm) was probed separately. **Measured: the tile output is not a crop of
the full output on either arm.**

| Arm | Word mismatches | Byte mismatches | First mismatch (top-down) |
| --- | --- | --- | --- |
| live clamp (the stored tile case) | 74 of 120 | 74 | [0,0] r | 0x3f400000 vs 0x3e800000 |
| range zero (probed separately) | 75 of 120 | 75 | [0,0] r | 0x3ec00000 vs 0x3f600000 |

wobble has NO tileOffset or fullResolution bindings -- unlike cellRefract or the Shapes programs, there is no world-position carrier anywhere in the shader. The only spatial input is v_texCoord, which the JavaScript materializes as context.uv: the pixel center of the DESTINATION grid. A 5x6 tile over the same 11x9 input therefore samples the input at ((tx + 0.5) / 5, (6 - ty - 0.5) / 6) while the full route's corresponding pixel samples at ((3 + tx + 0.5) / 11, (9 - (2 + ty) - 0.5) / 9): different coordinates, different texels, no offset rule exists that could align them. The sampleCoord probes below attribute the difference exactly there, on both arms.

The sampleCoord probes publish the post-wrap coordinate that feeds `texture()` on both routes: on the
live-clamp arm **6 x-lanes and
5 y-lanes of
30** coincide as f32 words; on the
range-zero arm **6 and
0**. The coincidences are exact f32
equalities (e.g. `(2 + 0.5) / 5 = 0.5 = (3 + 2 + 0.5) / 11`) and, on the live arm, clamp saturation
collapsing distinct folded coordinates to the same 0/1 word -- not evidence of alignment.
The tile route is pinned as its own parity case and both full-route surfaces are stored beside it; a native port must reproduce all of them. No crop identity may be asserted for this program on any arm, and the native test must not compare the tile against a crop of either full-route surface.

## One-axis control group on `live-mirror-max-range`: the wrap ToInt32-narrowing axis

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| external-pass-extreme | external runPass time/seed words (0x4f000000, 0xcf000000) | identical | identical | pass | 0 |
| wrap-binding-unbound | the wrap runtime binding: bound 0 versus absent entirely (undefined) | identical | identical | pass | 0 |
| wrap-binding-fractional-0.5 | bound wrap 0 (0x00000000) -> 0.5 (0x3f000000), ToInt32(0.5) === 0 | identical | identical | pass | 0 |
| wrap-binding-fractional-1.5 | bound wrap 0 -> 1.5, ToInt32(1.5) === 1 selects repeat | differs | differs | pass | 9 |
| bound-time-live | bound time 0x3fa00000 -> 0x40200000 | differs | differs | pass | 211 |

The `wrap-binding-unbound` and fractional-wrap rows pin `wrap|0` (the GLSL `int mode = int(wrap);`):
`undefined | 0 === 0` and `ToInt32(0.5) === 0` select mirror exactly as the bound 0 does, while
`ToInt32(1.5) === 1` selects repeat and measurably differs. The port always binds `wrap`; these rows
record the authority's narrowing semantics.

## Binding liveness census (anchor)

| Binding | Versus baseline | Changed lanes |
| --- | --- | ---: |
| inputTex | differs | 408 |
| time | differs | 211 |
| speed | differs | 206 |
| range | differs | 153 |
| wrap | differs | 9 |

## The range-zero inertness census

| Binding | Versus baseline | Changed lanes |
| --- | --- | ---: |
| time | identical | 0 |
| speed | identical | 0 |
| wrap | identical | 0 |
| range | differs | 384 |

at range = 0, r = max(range, 0) = 0 makes offsetScale = 0 and offset = (+-0, +-0), so sampleCoord degenerates to applyWrap(v_texCoord) -- the pure varying pass-through. Every scalar binding except inputTex and range itself is output-inert, measured here with extreme probes. range is THE discriminator binding: 0 -> 4 wakes the warp path.

## The defaults inertness census: at the shipped defaults, every scalar binding is inert

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
| time | {"time":1.7} | identical | 0 |
| time | {"time":4.25} | identical | 0 |
| speed | {"speed":0} | identical | 0 |
| speed | {"speed":2} | identical | 0 |
| range | {"range":0} | identical | 0 |
| range | {"range":5} | identical | 0 |
| wrap | {"wrap":1} | identical | 0 |
| wrap | {"wrap":2} | identical | 0 |

the shipped defaults on a 16x9 destination leave EVERY scalar binding output-inert: the maximum possible offset magnitude is 0.5 * range * (0.01 + 0.02 * speed) = 0.5 * 0.5 * 0.11 = 0.0275, below the 0.5 / 16 = 0.03125 half-texel margin, so no sample crosses a texel boundary under ANY defaults binding pair. The effect becomes output-active only at larger range/speed (the anchor) or on finer grids. This is a measured parity fact, not a defect report: a port that differs here differs from an oracle that is invariant.

## The wrap-arm census

| Case | Arm | offset words | half-texel margins | lane crosses | Alternates |
| --- | --- | --- | --- | --- | --- |
| range-zero-passthrough | mirror | 0x80000000 / 0x00000000 | 0.0312500 / 0.0555556 | no / no | repeat:identical, clamp:identical |
| live-mirror-max-range | mirror | 0x3d382af4 / 0x3cf51948 | 0.0312500 / 0.0555556 | yes / no | repeat:differs(9), clamp:identical |
| live-repeat-portrait | repeat | 0xbd43cac2 / 0xbd8b0eaa | 0.0555556 / 0.0312500 | no / yes | clamp:differs(27), mirror:differs(27) |
| tile-crop-translation | clamp | 0xbdb84bc8 / 0xbe68c9ff | 0.100000 / 0.0833333 | no / yes | mirror:differs(15), repeat:differs(15) |

a wrap switch can only change the output where some pixel's sampleCoord leaves [0, 1): on the open unit interval all three arms are the identity (mirror's mod arithmetic cancels exactly, and nearest sampling absorbs the sub-ULP arm differences elsewhere). The offset is uniform per frame, so crossing happens on lane L exactly when |offset_L| exceeds the half-texel margin 0.5 / size_L. CAVEAT, measured on the mirror row: a SHALLOW crossing (within one texel of the edge) makes mirror and clamp read the SAME edge texel (mirror reflects back into it, clamp pins to it), so that pair can agree despite the crossing. Each row records both alternate arms as measured.

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
| varying-lane-swapped | range-zero-passthrough | witness | differs | 361 |
| varying-lane-swapped | live-mirror-max-range | witness | differs | 200 |
| varying-lane-swapped | live-repeat-portrait | witness | differs | 372 |
| varying-lane-swapped | tile-crop-translation | witness | differs | 84 |
| varying-y-unflipped | range-zero-passthrough | witness | differs | 288 |
| varying-y-unflipped | live-mirror-max-range | witness | differs | 66 |
| varying-y-unflipped | live-repeat-portrait | witness | differs | 432 |
| varying-y-unflipped | tile-crop-translation | witness | differs | 80 |
| offset-sign-flipped | range-zero-passthrough | control | identical | 0 |
| offset-sign-flipped | live-mirror-max-range | witness | differs | 222 |
| offset-sign-flipped | live-repeat-portrait | witness | differs | 432 |
| offset-sign-flipped | tile-crop-translation | witness | differs | 70 |
| wrap-arm-swapped | range-zero-passthrough | control | identical | 0 |
| wrap-arm-swapped | live-mirror-max-range | witness | differs | 9 |
| wrap-arm-swapped | live-repeat-portrait | witness | differs | 27 |
| wrap-arm-swapped | tile-crop-translation | control | identical | 0 |
| speed-fold-phase-shifted | range-zero-passthrough | control | identical | 0 |
| speed-fold-phase-shifted | live-mirror-max-range | witness | differs | 222 |
| speed-fold-phase-shifted | live-repeat-portrait | witness | differs | 432 |
| speed-fold-phase-shifted | tile-crop-translation | witness | differs | 80 |
| hash31-pcg-divisor-halved | range-zero-passthrough | control | identical | 0 |
| hash31-pcg-divisor-halved | live-mirror-max-range | witness | differs | 279 |
| hash31-pcg-divisor-halved | live-repeat-portrait | witness | differs | 432 |
| hash31-pcg-divisor-halved | tile-crop-translation | witness | differs | 90 |

All six ledger mutants are one-anchor/one-replacement rewrites of the canonical factory text (the wrap swap
is an ordered three-anchor chain through a unique temp identifier), compiled and rendered by this generator,
and each was **verified bit-differing before it was budgeted**. The expected outcome is frozen **per case
and per mutant**; `--check` fails if any single cell flips, in either direction.

The two varying mutants are competing probes of one materialization (lane order versus y orientation) and the four path mutants pin different functions (offset sign, wrap arms, speed fold, pcg chain); witness sets overlap BY CONSTRUCTION on the live cases. Overlap is disclosed, not engineered away: the per-case table, not disjointness, is what attributes a divergence. The load-bearing separation is structural and measured: on range-zero-passthrough ONLY the two varying mutants move a lane -- the pure discriminator the design asked for.

### The sub-texel uv control

| Case | Result | Changed lanes |
| --- | --- | ---: |
| range-zero-passthrough | identical | 0 |
| live-mirror-max-range | identical | 0 |
| live-repeat-portrait | identical | 0 |
| tile-crop-translation | identical | 0 |

texture() is nearest-sampling (sampleNearestBottomLeft): the output depends only on which texel sampleCoord lands in. A 1e-7 perturbation of both uv lanes moves samples by far less than the smallest texel width in this fixture set (1/16), so every image is bit-identical. The uv materialization is pinned instead by varying-lane-swapped and varying-y-unflipped, whose perturbations are texel-scale by construction.

### The dead-code census

wobble has no non-executing construct at any binding: main calls simplexRandom (twice), noise3d, hash31, pcg and applyWrap unconditionally, and each applyWrap arm is selected by the wrap binding (mirror/repeat/clamp all appear in this case set). A cellrefract-style branch-control mutant cannot exist here. The range-zero control rows in the mutation ledger are algebraic cancellations (the noise and warp code EXECUTES and its result is multiplied by zero), not runtime-skip versus normalizer-strip agreements, and the oracle never presents them as such.

## Claim boundaries

- The oracle pins the v_texCoord == context.uv aliasing pixel-exactly through the pass-runner path; the port-side admission (v_texCoord lowering to context.uv) is validated against these arrays, not against any typed-slice state.
- No crop identity holds for this program on ANY arm, including range = 0: the tile route is pinned as its own parity case with both full-route surfaces stored beside it. The mechanism is pure destination-local v_texCoord (wobble has no tileOffset/fullResolution bindings at all).
- range = 0 is the pure varying pass-through; the two varying mutants are the only ledger mutants that move a lane there, and every other mutant is a measured control row on that case.
- At the shipped defaults on a 16x9 every scalar binding is output-inert (the offset is structurally below the half-texel margin). Recorded as a parity fact with the bound, not as a defect.
- wrap is a float binding narrowed by ToInt32 at use; an absent wrap is mirror and 0.5 is mirror while 1.5 is repeat (measured controls).
- wobble has no non-executing construct at any binding; the cellrefract-style branch control does not exist here and the range-zero control rows are algebraic cancellations, never presented as skip/strip agreements.
- Nearest sampling absorbs sub-texel uv perturbations; the uv materialization is pinned by the two varying mutants, not by sub-ULP probes.
- The defaults, wrap-switch, inertness, and liveness probes bind values outside the frozen case set (and outside the shipped defaults, for the extremes). They cover the ABI and prove channels real; they are never parity cases and never evidence about production behaviour.
- Normalized/typed source, function, interface, and whole-program hashes are the frontend profiles' authority and are deliberately not restated here.

## Regeneration

```sh
node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --self-test
```

Both generators are fail-closed and check mode performs no writes.
