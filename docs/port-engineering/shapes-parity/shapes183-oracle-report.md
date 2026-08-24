# Shapes183 exact-parity oracle

Program `classicNoisedeck/shapes:shapes`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; exact defines
`LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30`.

## Authority

This oracle is produced by the unmodified public canonicalFactory16 from an immutable noisemaker-for-cpu snapshot, executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates. The generator refuses to run unless
`kernelFactories.get(key) === canonicalKernelFactories[key]`, the factory is named
`canonicalFactory16`, its `Function.prototype.toString` SHA-256 is `a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3`, the adapter
table does not own the key, all six pinned CPU files match, and every module in the
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

The program has exactly 18 runtime bindings:
`time`, `seed`, `wrap`, `resolution`, `tileOffset`, `fullResolution`, `loopAScale`, `loopBScale`, `speedA`, `speedB`, `paletteMode`, `paletteOffset`, `paletteAmp`, `paletteFreq`, `palettePhase`, `cyclePalette`, `rotatePalette`, `repeatPalette`.
`LOOP_A_OFFSET` and `LOOP_B_OFFSET` are compile-time defines recorded separately and are never
counted as bindings.

## Render fixtures

| Case | Size | Route | paletteMode | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | ---: | --- | --- |
| oklab-palette-a | 9x5 | full | 2 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | 911d03c1fd327061cb4bb8d41a3b2e7ed9bcb2dfec50776ff03f093dbf50b20d |
| oklab-palette-tiled | 4x6 | tile | 2 | e09d197bc80c78abb192447304c5594aaf665246fc07f4bc64ece2565618d18f | 16c46d29ad434f914b784bebb351f283d4a55129d341d63befa01da8bd862cf8 |
| oklab-palette-extreme | 6x6 | full | 2 | a124bff5cac4af3ef9a1c944917ed92c590461dd8f574b6f651203c8792d0877 | 40bc2f869f9c1382ef613d3c7e510b4bdb312c27c139c7974194e182e7520ab6 |
| oklab-palette-negative-speed | 5x9 | full | 2 | 1a7fc784930cd7fcb51adf9a4ece4824e2c198657d07f4b08ce177efe9ff12e8 | a89d1cf8a0e3baac30d8d8451fbf87cb4cec0f93bad72e79e1ac04d9b5f811d2 |
| diagnostic-palette-hsv | 8x3 | full | 1 | 5c4792a56ee13b0031bbf2e0d22d32af5812f4f7fe3bf0c6bbc0fcaf3b3fa568 | 1b77f7a6812c37b7ee636d7f5361efd3bc70f9a089b366b09ef9c3a9ec6a624f |
| diagnostic-palette-rgb | 4x4 | full | 0 | c71acea4851ef666555705cda29cf71cae187cf8f041f985300840aa91e5bfcf | 95eb46516d39683e44fd4922fbfcd69e07c556cdf03df0287676abcaf39b0642 |

Every case stores exact dimensions, all 18 bindings with every float and vector lane as a
hexadecimal f32 word, the external `runPass` time/seed pair, the complete expected Float32 word
array, the complete independently captured RGBA8 byte array, finite/non-finite lane counts, and a
SHA-256 over each array. Alpha is exactly `0x3f800000` / `255` in every case and every route.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
| palette_mode | OKLab (2) | oklab-palette-a, oklab-palette-tiled, oklab-palette-extreme, oklab-palette-negative-speed |
| palette_mode | HSV (1) | diagnostic-palette-hsv |
| palette_mode | RGB (0) | diagnostic-palette-rgb |
| aspect | landscape | oklab-palette-a, diagnostic-palette-hsv |
| aspect | portrait | oklab-palette-tiled, oklab-palette-negative-speed |
| aspect | square | oklab-palette-extreme, diagnostic-palette-rgb |
| tiling | tiled | oklab-palette-tiled |
| tiling | untiled | oklab-palette-a, oklab-palette-extreme, oklab-palette-negative-speed, diagnostic-palette-hsv, diagnostic-palette-rgb |
| wrap | true | oklab-palette-tiled, oklab-palette-negative-speed, diagnostic-palette-rgb |
| wrap | false | oklab-palette-a, oklab-palette-extreme, diagnostic-palette-hsv |
| speed_sign | positive | oklab-palette-a, oklab-palette-extreme, diagnostic-palette-hsv |
| speed_sign | negative | oklab-palette-tiled, oklab-palette-extreme, oklab-palette-negative-speed, diagnostic-palette-rgb |
| speed_sign | zero | oklab-palette-tiled, diagnostic-palette-hsv, diagnostic-palette-rgb |
| cycle_palette | 0 | oklab-palette-tiled, oklab-palette-negative-speed |
| cycle_palette | 1 | oklab-palette-a, diagnostic-palette-hsv |
| cycle_palette | -1 | oklab-palette-extreme, diagnostic-palette-rgb |
| rotate_repeat | nominal | oklab-palette-a, oklab-palette-tiled |
| rotate_repeat | extrema | oklab-palette-extreme |
| rotate_repeat | identity | oklab-palette-negative-speed, diagnostic-palette-rgb |
| rotate_repeat | negative_rotate_fractional_repeat | diagnostic-palette-hsv |

## Top-down crop normalization

Both runners store rows top-down while GLSL fragment coordinates are bottom-left. The tiled case is a
genuine crop: `tileOffset = (crop_x, full_height - crop_y - tile_height)`. For crop
`(4, 2)` of size
`4x6` from
`11x9`, the tile route binds
`tileOffset` words `0x40800000, 0x3f800000`; the other 16 bindings are held identical.
Tile output equals the corresponding top-down crop of the full-route output exactly:
0 word mismatches and 0 byte mismatches.
Binding raw top-down `crop_y` into `tileOffset.y` instead changes
51 lanes, so the witness is not vacuous.

## One-axis control group on `oklab-palette-a`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| external-pass-extreme | external runPass time/seed words (0x4f000000, 0xcf000000) | identical | identical | pass | 0 |
| bound-time-ten | bound time 0x3f000000 -> 0x41200000 | differs | differs | pass | 135 |
| bound-seed-123 | bound seed int32 3 -> 123 | differs | identical | FAIL | 0 |

## Bound-seed liveness census

| Bound seed | Float32 SHA-256 | Versus baseline |
| --- | --- | --- |
| -2147483648 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| -7 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 0 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 1 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 3 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 123 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 65537 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |
| 2147483647 | aa496f77fee47c501c954dcf186d81bac236191c590388de41ae8c687f43c649 | identical |

At defines LOOP_A_OFFSET=40 / LOOP_B_OFFSET=30 the only main() consumers of the `seed` uniform are the two `offset(...)` calls. Offset 40 dispatches to shape(st, 4, freq*0.5) and offset 30 dispatches to the absolute-distance branch; neither reads its `seed` parameter. The `value()`/`constant()`/`randomFromLatticeWithOffset()` subtree that would consume it is reachable in the conservative call graph but is not entered by a default full render.

**Disagreement with the design.** shapes183-design.md section 4.1 and NEXT_CODING_AGENT_HANDOFF.md section 5 require the bound-seed control to change the output.
The shipped JavaScript materialization does not change. The parity target is the shipped materialization, so the measured result is recorded verbatim and the design expectation is reported as unsatisfiable at the default defines. `seed` remains a required int32 ABI binding.

## Mutation discrimination

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
| shapes-fwdB-column-swap | oklab-palette-a | reaching | differs | 135 |
| shapes-fwdB-column-swap | oklab-palette-tiled | reaching | differs | 72 |
| shapes-fwdB-column-swap | oklab-palette-extreme | reaching | differs | 108 |
| shapes-fwdB-column-swap | oklab-palette-negative-speed | reaching | differs | 135 |
| shapes-fwdB-column-swap | diagnostic-palette-hsv | control | identical | 0 |
| shapes-fwdB-column-swap | diagnostic-palette-rgb | control | identical | 0 |
| shapes-cube-unnarrowed | oklab-palette-a | reaching | differs | 58 |
| shapes-cube-unnarrowed | oklab-palette-tiled | reaching | differs | 19 |
| shapes-cube-unnarrowed | oklab-palette-extreme | reaching | differs | 40 |
| shapes-cube-unnarrowed | oklab-palette-negative-speed | reaching | differs | 63 |
| shapes-cube-unnarrowed | diagnostic-palette-hsv | control | identical | 0 |
| shapes-cube-unnarrowed | diagnostic-palette-rgb | control | identical | 0 |

Both mutants are independent one-anchor/one-replacement rewrites of the canonical factory text,
compiled and rendered by this generator. `--check` fails unless all four reaching OKLab cases differ
for each mutant and both non-reaching diagnostic controls stay byte-identical. No hand-mutated
generated C++ is committed.

## Claim boundaries

- With defines 40/30 the branch containing floatBitsToUint(seedFrac) and the three scalar uint XOR sites is conservative call-graph reachable but is not entered by a normal full render. These full-surface cases must never be cited as proof that branch executed.
- Normalized/typed source, function, interface, and whole-program hashes are the frontend profiles’ authority and are deliberately not restated here.
- The bound `seed` uniform is a required int32 ABI binding but is pixel-inert at the default defines; see seed_liveness_census.

## Regeneration

```sh
node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --self-test
```

Both generators are fail-closed and check mode performs no writes.
