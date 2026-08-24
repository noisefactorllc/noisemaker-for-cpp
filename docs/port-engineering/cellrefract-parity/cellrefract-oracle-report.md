# Cellrefract186 exact-parity oracle

Program `classicNoisedeck/cellRefract:cellRefract`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; exact defines
`KERNEL=0`, `SHAPE=1`.

## The contract this program exists to prove

`classicNoisedeck/cellRefract` declares five **mutable uninitialized** file-scope `float[9]` tables
and a writer function, and the parity target is the transpiler's materialization, not GLSL semantics:

| Table | JavaScript | Writer | Readers | Oracle-discriminable |
| --- | --- | --- | --- | --- |
| `emboss` | plain `Array` of doubles | `loadKernels`, 9 literal stores | whole-array arguments inside convolutionKernel's KERNEL != 0 branches only (1 read sites) | **no** |
| `sharpen` | plain `Array` of doubles | `loadKernels`, 9 literal stores | whole-array arguments inside convolutionKernel's KERNEL != 0 branches only (1 read sites) | **no** |
| `blur` | plain `Array` of doubles | `loadKernels`, 9 literal stores | whole-array arguments inside convolutionKernel's KERNEL != 0 branches only (1 read sites) | **no** |
| `edge` | plain `Array` of doubles | `loadKernels`, 9 literal stores | none anywhere, not even in KERNEL != 0 branches | **no** |
| `edge2` | plain `Array` of doubles | `loadKernels`, 9 literal stores | whole-array arguments inside convolutionKernel's KERNEL != 0 branches only (2 read sites) | **no** |

The tables are **write-only at the frozen defines**: their only readers live inside
`convolutionKernel`'s `KERNEL != 0` branches, which `main` never enters at `KERNEL = 0`. No
table-content mutant can move a pixel, and this package never pretends otherwise:
`write_only_tables_axis` renders a table mutant on every case and records
0 changed lanes. The double element contract and the
exact 45 (table, index, value) triples are proven structurally -- by the emitted native type, by the
JavaScript being plain Arrays, and by the frontend profile's frozen store census. A green pixel run is
not evidence for them.

## Authority

This oracle is produced by the unmodified public canonicalFactory3 from an immutable noisemaker-for-cpu snapshot, executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates. The generator refuses to run unless
`kernelFactories.get(key) === canonicalKernelFactories[key]`, the factory is named
`canonicalFactory3`, its `Function.prototype.toString` SHA-256 is `329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`, neither
adapter table owns the key, `canonicalAdapterFactories` matches its
11-key census exactly, the key is absent from the
4-key `check_corpus._ADAPTERS` eligibility table
**parsed out of the live `tools/glslcpp/check_corpus.py`**
rather than transcribed, all six pinned CPU files match, and every module in the
22-file import closure resolves by real path
beneath the immutable snapshot. Bare module specifiers other than `node:` builtins are rejected, and
the live checkout is refused as a `--cpu-root`.

No absolute path is recorded anywhere in this package. The `--cpu-root` argument is stored as
`<immutable-cpu-snapshot-root>` and the rejected live checkout as
`<live-noisemaker-for-cpu-checkout>`, resolved at run time from
process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings

The program has exactly 15 runtime bindings:
`inputTex`, `time`, `seed`, `resolution`, `tileOffset`, `fullResolution`, `scale`, `cellScale`, `cellSmooth`, `variation`, `speed`, `refractAmt`, `direction`, `wrap`, `effectWidth`. `KERNEL` and `SHAPE` are
compile-time defines in the corpus that the JavaScript materializes as runtime bindings at the frozen
values; they are never counted as bindings. `resolution` is never read and `effectWidth`'s reads
are stripped at `KERNEL = 0`; both remain required ABI bindings and are recorded inert, not deleted.

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| cells-wrap-mirror | 16x9 | full | 16x9 | 6645a5d6dfb3c9cadf61a8c15426df8f6a710c2c2c923a173731ef22843e49b1 | d67d11b35c0d759f4fae31f41dca85473cca90720dc8318d3597269b0a28972a |
| cells-wrap-repeat | 16x9 | full | 16x9 | eb6c1ce645113984f491b21273eea71b15a619368df5068bff76e801149a16c9 | 973b45e9205e9dd4149d30ab2792b8859604871088e9afc3175686dba1632470 |
| cells-extreme-variation | 12x12 | full | 12x12 | 8d79520f9f8dfccf4a41d8179cccd0d5e869c9ce4e64da9919124a568faea17e | af3f47b1f83fb6e4a8a6beec0d5e1f6cc7e2709d70ed02bedde30824baef705c |
| tile-crop-translation | 4x6 | tile | 11x9 | 61da9800d075d8fe87be903cb29b773a661989b8f6f658e3c1a4995ad047786b | 0e704c1dbc261af080ce058e1c64ee8342236b99aa1bf7dda6cd311796523119 |

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
15 bindings with every float and vector lane as a hexadecimal f32
word, the external `runPass` time/seed pair, the complete expected Float32 word array, the complete
independently captured RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each array.
Every input lane is a small dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
| wrap_arm | mirror_wrap_0 | cells-wrap-mirror, cells-extreme-variation |
| wrap_arm | repeat_wrap_1 | cells-wrap-repeat, tile-crop-translation |
| wrap_arm_liveness | live_displacement_out_of_unit_range | cells-wrap-mirror, cells-wrap-repeat, cells-extreme-variation |
| wrap_arm_liveness | inert_interior_window | tile-crop-translation |
| smin_arm | h_quadratic_branch | cells-wrap-mirror, cells-wrap-repeat, tile-crop-translation |
| smin_arm | k_zero_min_branch | cells-extreme-variation |
| full_resolution_aspect | aspect_16_over_9 | cells-wrap-mirror, cells-wrap-repeat |
| full_resolution_aspect | square_aspect_exactly_1 | cells-extreme-variation |
| full_resolution_aspect | aspect_11_over_9 | tile-crop-translation |
| time_speed_phase | integral_motion_phase | cells-wrap-mirror |
| time_speed_phase | non_integral_motion_phase | cells-wrap-repeat, cells-extreme-variation, tile-crop-translation |
| route | full | cells-wrap-mirror, cells-wrap-repeat, cells-extreme-variation |
| route | tile | tile-crop-translation |
| input_pattern | ramp | cells-wrap-mirror, cells-extreme-variation, tile-crop-translation |
| input_pattern | contrast | cells-wrap-repeat |
| variation | mid_30 | cells-wrap-mirror, cells-wrap-repeat, tile-crop-translation |
| variation | maximum_100 | cells-extreme-variation |

## Tile translation: the Shapes crop contract does NOT carry over

Design section 7 assumed `tile-crop-translation` would satisfy the Shapes-amended crop identity.
**Measured: it does not.** With `tileOffset = (4,
undefined - 2 - 6)`
and the same 11x9 input texture on both routes,
70 of 96 Float32 words and
70 RGBA8 bytes differ between the tile output and the top-down crop of the full output
(first mismatch at top-down [0,0] channel
r: tile 0x3f000000 versus full
0x3f200000).

globalCoord = gl_FragCoord + tileOffset carries the world position into st and the cells field, exactly as in Shapes. But this shader then computes localUV = (st * fullResolution - tileOffset) / textureSize, and st * fullResolution - tileOffset cancels back to gl_FragCoord: the tile samples the input in DESTINATION-LOCAL coordinates, a constant tileOffset/texSize translation away from the full route's sample. Both halves are measured below.

Both halves are measured with instrumented probe factories (one anchor, one replacement; never parity
arrays). Publishing the cells field `d` on both routes gives
**0 mismatches** -- the cell field
IS world-aligned through tileOffset. Publishing `localUV` gives
**0 equal lanes of
48** -- the sample coordinate is a
constant translation away, exactly as the algebra predicts. The raw-crop-y trap still bites:
binding raw top-down `crop_y` changes 47 lanes.
The tile route is pinned as its own parity case and the full 11x9 route is stored beside it; a native port must reproduce BOTH. No crop identity may be asserted for this program, and the native test must not compare the tile against a crop of the full route.

## One-axis control group on `cells-wrap-mirror`: the kernel-zero-invariance axis

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| external-pass-extreme | external runPass time/seed words (0x4f000000, 0xcf000000) | identical | identical | pass | 0 |
| kernel-binding-unbound | the KERNEL runtime binding: bound 0 versus absent entirely (undefined) | identical | identical | pass | 0 |
| bound-time-live | bound time 0x3f000000 -> 0x3e99999a | differs | differs | pass | 267 |
| effect-width-extreme | bound effectWidth 0 -> 7 | identical | identical | pass | 0 |

The `kernel-binding-unbound` row is the axis the design asked for: the JS `KERNEL` binding is bound
at 0 on every case, and an *absent* KERNEL renders bit-identically (undefined != 0 is false). The port
has no KERNEL binding at all, so this control asserts the absence of a divergence channel.

### KERNEL liveness census

| KERNEL probe | Versus baseline | Changed lanes |
| --- | --- | ---: |
| unbound | identical | 0 |
| 0 | identical | 0 |
| 1-with-effectwidth-4 | differs | 400 |
| 4-with-effectwidth-4 | differs | 359 |
| 7-with-effectwidth-4 | differs | 336 |

KERNEL is a runtime binding in the JavaScript, bound at the frozen define 0 on every parity case. The axis is closed there and open the moment a non-zero KERNEL meets a non-zero effectWidth -- the same branch tree the corpus normalizer strips. The port carries no KERNEL binding, so a port that accidentally leaves the channel open diverges from these very cases.

## Binding inertness and liveness censuses

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
| resolution | [131072.1,0.3] | identical | 0 |
| resolution | [1,1] | identical | 0 |
| resolution | [-16,-9] | identical | 0 |
| effectWidth | 7 | identical | 0 |
| effectWidth | 10 | identical | 0 |
| effectWidth | -3 | identical | 0 |

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
| inputTex | differs | 406 |
| time | differs | 267 |
| seed | differs | 292 |
| tileOffset | differs | 371 |
| fullResolution | differs | 355 |
| scale | differs | 265 |
| cellScale | differs | 324 |
| cellSmooth | differs | 79 |
| variation | differs | 56 |
| speed | differs | 262 |
| refractAmt | differs | 384 |
| direction | differs | 409 |
| wrap | differs | 21 |

a binding is recorded inert only after the anchor case is re-rendered with deliberately extreme values and compared exactly. Inertness is a parity assertion: a port that wrongly made one of these live would differ from an oracle that is invariant.

## The time * floor(speed) phase rule

| Case | time | floor(speed) | phase | |
| --- | ---: | ---: | ---: | --- |
| cells-wrap-mirror | 0.5 | 2 | 1 | integral |
| cells-wrap-repeat | 1.25 | 3 | 3.75 | non-integral |
| cells-extreme-variation | 2.5 | 5 | 12.5 | non-integral |
| tile-crop-translation | 0.25 | 2 | 0.5 | non-integral |

| Probe | Override | Observed | Changed lanes |
| --- | --- | --- | ---: |
| cells-wrap-mirror | {"time":1.5} | identical | 0 |
| cells-wrap-mirror | {"time":0.3} | differs | 267 |
| cells-wrap-repeat | {"time":2} | differs | 138 |

the motion terms are sin(time * 2pi * floor(speed) + r2) and cos(...): time is inert wherever time * floor(speed) is an integer (the phase is a whole multiple of 2pi) and live elsewhere. The anchor case sits exactly on an integral phase; two probes move it off, one keeps it on.

At the anchor's integral phase the whole speed parameter collapses to
2 equivalence classes:
speed 0/2/4 and speed 1/3/5.

| speed | Float32 SHA-256 |
| ---: | --- |
| 0 | 6645a5d6dfb3c9cadf61a8c15426df8f6a710c2c2c923a173731ef22843e49b1 |
| 1 | f6c7d449234025598fb1dec9de37611d0d05208df00d4af8876faf86f90ba001 |
| 2 | 6645a5d6dfb3c9cadf61a8c15426df8f6a710c2c2c923a173731ef22843e49b1 |
| 3 | f6c7d449234025598fb1dec9de37611d0d05208df00d4af8876faf86f90ba001 |
| 4 | 6645a5d6dfb3c9cadf61a8c15426df8f6a710c2c2c923a173731ef22843e49b1 |
| 5 | f6c7d449234025598fb1dec9de37611d0d05208df00d4af8876faf86f90ba001 |

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
| smin-h-quadratic-dropped | cells-wrap-mirror | witness | differs | 79 |
| smin-h-quadratic-dropped | cells-wrap-repeat | witness | differs | 20 |
| smin-h-quadratic-dropped | cells-extreme-variation | control | identical | 0 |
| smin-h-quadratic-dropped | tile-crop-translation | witness | differs | 13 |
| prng-pcg-constant-perturbed | cells-wrap-mirror | witness | differs | 257 |
| prng-pcg-constant-perturbed | cells-wrap-repeat | witness | differs | 160 |
| prng-pcg-constant-perturbed | cells-extreme-variation | witness | differs | 310 |
| prng-pcg-constant-perturbed | tile-crop-translation | witness | differs | 44 |
| aspect-ratio-inverted | cells-wrap-mirror | witness | differs | 270 |
| aspect-ratio-inverted | cells-wrap-repeat | witness | differs | 196 |
| aspect-ratio-inverted | cells-extreme-variation | control | identical | 0 |
| aspect-ratio-inverted | tile-crop-translation | witness | differs | 32 |
| wrap-arm-swapped | cells-wrap-mirror | witness | differs | 21 |
| wrap-arm-swapped | cells-wrap-repeat | witness | differs | 11 |
| wrap-arm-swapped | cells-extreme-variation | witness | differs | 54 |
| wrap-arm-swapped | tile-crop-translation | control | identical | 0 |

All four ledger mutants are one-anchor/one-replacement rewrites of the canonical factory text (the
wrap swap is an ordered three-anchor chain through a unique temp identifier), compiled and rendered by
this generator, and each was **verified bit-differing before it was budgeted**. The expected outcome
is frozen **per case and per mutant**; `--check` fails if any single cell flips, in either direction.

Unlike shape184 and normalmap185, whose two ledger mutants were competing materializations of one mechanism, these four mutants pin four DIFFERENT functions on the reachable path (smin, the prng chain, the aspect ratio, the wrap arms). Their witness sets overlap BY CONSTRUCTION -- every case with displacement, aspect != 1, and cellSmooth > 0 discriminates several at once -- and no case set covering this program's real behaviour could separate them (a case with zero displacement cannot witness smin or the wrap arms either). Overlap is therefore disclosed, not engineered away: the per-case table, not disjointness, is what attributes a divergence here.

### The non-reaching control: a KERNEL != 0 branch mutant

| Case | Result | Changed lanes |
| --- | --- | ---: |
| cells-wrap-mirror | identical | 0 |
| cells-wrap-repeat | identical | 0 |
| cells-extreme-variation | identical | 0 |
| tile-crop-translation | identical | 0 |

The divergence channel through convolutionKernel EXISTS in the JavaScript (see kernel_liveness_census: KERNEL = 1/4/7 with effectWidth != 0 change hundreds of lanes) but is CLOSED at the frozen define. The port has no KERNEL binding at all; a port that accidentally emitted a live KERNEL != 0 path would diverge from this oracle on every case, and a port that wrongly stripped the reachable path would fail the ledger mutants. This control proves the oracle itself can tell the two apart.

### The write-only tables, measured

| Case | Result | Changed lanes |
| --- | --- | ---: |
| cells-wrap-mirror | identical | 0 |
| cells-wrap-repeat | identical | 0 |
| cells-extreme-variation | identical | 0 |
| tile-crop-translation | identical | 0 |

**Every one of the 45 stored constants is a small integer exactly representable in binary32 AND binary64, and no reader executes at KERNEL = 0, so no value in this program distinguishes std::array<double, 9> from std::array<float, 9> and no table CONTENT mutation can move a pixel. The double element contract and the exact 45 (table, index, value) triples are proven STRUCTURALLY -- by the emitted native type, by the JavaScript being plain Arrays, and by the frontend profile's frozen store census -- and a green pixel run is not evidence for them. Shipping a table mutant as a control would be shipping a mutant that cannot diverge.**

### The prng near-ULP control

| Case | Result | Changed lanes |
| --- | --- | ---: |
| cells-wrap-mirror | identical | 0 |
| cells-wrap-repeat | identical | 0 |
| cells-extreme-variation | identical | 0 |
| tile-crop-translation | identical | 0 |

texture() is nearest-sampling: the output depends only on which texel localUV lands in. A 2^-32 relative perturbation of every prng output moves samples by far less than a texel, so the image is bit-identical. The pcg chain is nonetheless exactly pinned, by prng-pcg-constant-perturbed's factor-of-two witness.

## Claim boundaries

- Every one of the 45 stored constants is a small integer exactly representable in binary32 AND binary64, and no reader executes at KERNEL = 0, so no value in this program distinguishes std::array<double, 9> from std::array<float, 9> and no table CONTENT mutation can move a pixel. The double element contract and the exact 45 (table, index, value) triples are proven STRUCTURALLY -- by the emitted native type, by the JavaScript being plain Arrays, and by the frontend profile's frozen store census -- and a green pixel run is not evidence for them. Shipping a table mutant as a control would be shipping a mutant that cannot diverge.
- The divergence channel through convolutionKernel EXISTS in the JavaScript (see kernel_liveness_census: KERNEL = 1/4/7 with effectWidth != 0 change hundreds of lanes) but is CLOSED at the frozen define. The port has no KERNEL binding at all; a port that accidentally emitted a live KERNEL != 0 path would diverge from this oracle on every case, and a port that wrongly stripped the reachable path would fail the ledger mutants. This control proves the oracle itself can tell the two apart.
- The Shapes crop contract does NOT carry over to this program: the tile output is not a crop of the full output (measured, with the d-field/localUV probes attributing the difference to localUV's -tileOffset term). No native test may assert a crop identity here.
- effectWidth is a required number ABI binding whose reads are stripped at KERNEL = 0; it is recorded inert, not deleted.
- resolution is declared and never read; it stays a required Vec2 ABI binding per the Shapes precedent.
- fragColor is a factory-scope Float32Array shared across pixels, but main() writes all four of its lanes unconditionally on every path, so cross-pixel persistence is unobservable for this program. loadKernels likewise re-writes all 45 table elements before any possible read, so factory-scope persistence of the tables is unobservable too.
- The KERNEL != 0 liveness probes bind values the shipped parameter set never binds (the kernel param defaults to 0). They cover the ABI and prove the channel real; they are never parity cases and never evidence about production behaviour.
- Normalized/typed source, function, interface, and whole-program hashes are the frontend profiles' authority and are deliberately not restated here.

## Regeneration

```sh
node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --self-test
```

Both generators are fail-closed and check mode performs no writes.
