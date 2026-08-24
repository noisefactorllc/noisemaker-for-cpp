# Projected post-Task-20 remaining-frontier audit

Date: 2026-08-10  
Scope: read-only corpus/typed-frontend/emitter inspection; no repository edits
and no Git commands. Projection assumes Task 19 and Task 20 are fully accepted,
including Task 20's exact Star Polygon Number-division compatibility transform.

## Result and Task 21 recommendation

The projected baseline is exact:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Post-Task-20 assumption | 114 | 116 | 96 |

The 212-program manifest consists of the 114 projected typed factories, the
two separately maintained public factories (`filter/invert:inv` and
`synth/solid:solid`), and 96 remaining programs.

Exactly two of those 96 already pass the current capability validator and
typed C++ emitter without adding a capability, proof kind, compatibility
transform, numeric-literal exception, loop rule, type, operator, builtin, or
ABI form:

```text
filter/crt:crt
filter/degauss:degauss
```

Task 19 and Task 20 do not unlock any other key: their array/parameter/index
proofs are source-key locked to Refract and Sacred Geometry. The correct
smallest Task 21 is therefore exactly:

```text
current-vocabulary-degauss-v1
  filter/degauss:degauss
```

| Projected Task 21 result | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Add Degauss only | **115** | **117** | **95** |

CRT is the only equal-language runner-up, but it should remain a separate
later one-key slice. Degauss is 10,803 raw source bytes, 17 functions, and
31,531 bytes in an in-memory typed emission. CRT is 19,560 raw source bytes,
35 functions, and 54,637 emitted bytes. Bundling them would double the oracle
and review surface without proving any shared new language feature.

## How the 96-key census was recomputed

Every manifest source not in the current 112-key typed allowlist, the two
planned Task 19/20 keys, or the two separately public legacy keys was parsed
with its authoritative metadata define map and semantically analyzed. The
current validator was then run with the complete current capability
vocabulary; programs that passed were also rendered in memory through the
typed emitter. No output was written to the repository.

This is a sound post-Task-20 projection because both planned array profiles
are exact-key exceptions rather than additions to the general approved type
or index vocabulary. Sacred Geometry's Star transform is likewise exact to
that key/function/span. Removing those two planned keys leaves every other
program's current first blocker unchanged.

The census is first-blocker based. Families can overlap: for example a source
may fail loop proof before its unsupported source `const int` declaration is
visited. The detailed family discussion below records those overlaps rather
than pretending each key has only one eventual requirement.

## Exact first-blocker census

| First current result | Count |
| --- | ---: |
| Current vocabulary validates and emits | 2 |
| Unsupported top-level global declaration | 31 |
| Unproved counted-loop program | 25 |
| `dFdx` derivative | 11 |
| `fwidth` derivative | 5 |
| Counted loop exceeds an existing safety cap | 3 |
| Vector/component index expression | 3 |
| Scalar/vector XOR form outside current overload | 2 |
| `round` builtin | 2 |
| Varying/stage interface | 2 |
| Sampler parameter reaches emitter type gap | 1 |
| `all` builtin | 1 |
| `any` builtin | 1 |
| `floatBitsToUint` builtin | 1 |
| `reflect` builtin | 1 |
| `tanh` builtin | 1 |
| Matrix return ABI | 1 |
| `inout` parameter ABI | 1 |
| `mat4` type | 1 |
| Uniform block/resource ABI | 1 |
| **Total** | **96** |

### Current-language clean (2)

```text
filter/crt:crt
filter/degauss:degauss
```

### Unsupported top-level global declaration (31)

```text
classicNoisedeck/bitEffects:bitEffects
classicNoisedeck/cellNoise:cellNoise
classicNoisedeck/cellRefract:cellRefract
classicNoisedeck/colorLab:colorLab
classicNoisedeck/kaleido:kaleido
classicNoisedeck/moodscape:moodscape
classicNoisedeck/shapeMixer:shapeMixer
classicNoisedeck/shapes:shapes
filter/adjust:adjust
filter/colorspace:colorspace
filter/edge:edge
filter/emboss:emboss
filter/fxaa:fxaa
filter/glyphMap:glyphMap
filter/grade:creative
filter/grade:hslSecondary
filter/grade:primary
filter/grade:vignette
filter/grade:wheels
filter/grain:grain
filter/historicPalette:historicPalette
filter/normalMap:normalMap
filter/osd:osd
filter/palette:palette
filter/scanlineError:scanlineError
filter/smooth:smoothEdge
filter/snow:snow
filter/spookyTicker:spookyTicker
filter/texture:texture
filter/wobble:wobble
synth/shape:shape
```

This group separates into five bounded forms:

- 16 have only initialized read-only `const int`, `const uint`, and/or
  `const vec3` beyond the current `const float` rule: Bit Effects, Edge,
  Emboss, FXAA, Glyph Map, the five Grade keys, Grain, Scanline Error,
  Smooth Edge, Snow, Texture, and Wobble.
- Seven have read-only `const mat3` color transforms: Cell Noise, Color Lab,
  Moodscape, Shape Mixer, Shapes, Adjust, and Colorspace.
- Cell Refract and Kaleido have uninitialized global `float[9]` tables.
- Historic Palette, Normal Map, OSD, Palette, and Spooky Ticker have global
  array/struct table profiles with distinct element/index/lifetime proofs.
- `synth/shape:shape` has mutable uninitialized `aspectRatio`/`globalCoord`
  state and must not be admitted as a source-constant feature.

### Unproved counted-loop program (25)

```text
classicNoisedeck/effects:effects
classicNoisedeck/fractal:fractal
classicNoisedeck/noise:noise
filter/bloom:ntapGather
filter/blur:blurH
filter/blur:blurV
filter/directionalBlur:directionalBlur
filter/dither:dither
filter/lightLeak:lightLeak
filter/median:median
filter/normalize:statsFinal
filter/oilPaint:oilFlatten
filter/parallax:parallax
filter/reindex:nmReindexReduce
filter/reindex:nmReindexStats
filter/smooth:smoothBlend
filter/spinBlur:spinBlur
filter/strokes:stkSmear
filter/tetraColorArray:tetraColorArray
filter/vaseline:upsample
filter/wind:wind
filter/zoomBlur:zoomBlur
synth/mandelbrot:mandelbrot
synth/noise:noise
synth/testPattern:testPattern
```

The unproved loops are not one feature:

- Twelve programs use source `const int` bounds not recognized by the current
  local-bound proof: Bloom Gather, Directional Blur, Dither, Light Leak,
  Parallax, both Reindex passes, Spin Blur, Stroke Smear, Vaseline, Wind, and
  Mandelbrot. Several have later blockers; this is not a twelve-key unlock.
- Nine use uniform, resource-size, or other runtime-derived bounds: the three
  loop helpers in classic Fractal as one program, classic Noise, Blur H/V,
  Normalize Stats Final, Oil Flatten, Tetra Color Array, synth Noise, and Test
  Pattern.
- `filter/median:median` has four data-dependent `while` loops used for
  partition/sort work.
- classic Effects and Filter Zoom Blur use `float` induction variables.
- Smooth Blend's otherwise literal `i=1..32` search loop contains an early
  `return`, which the current counted-loop proof correctly refuses.

### Derivative ABI (16)

`dFdx` first blockers (11):

```text
filter/bulge:bulge
filter/lens:lens
filter/lensWarp:lensWarp
filter/octaveWarp:octaveWarp
filter/pinch:pinch
filter/polar:polar
filter/pondRipples:pondRipples
filter/spiral:spiral
filter/tunnel:tunnel
filter/warp:warp
mixer/distortion:distortion
```

`fwidth` first blockers (5):

```text
filter/celShading:celShadingColor
filter/halftone:halftone
filter/stamp:stThreshold
filter/step:step
filter/stipple:stipple
```

These remain an execution-ABI family, not a builtin-name addition. They need
neighbor evaluation, tile-border ownership, scheduling, and derivative-mode
oracles. Task 21 must not touch them.

### Counted loops over an existing safety cap (3)

```text
synth/gabor:gabor
synth/julia:julia
synth/newton:newton
```

Gabor reaches effective depth 4 (current limit 3). Julia has a 1,000-trip
individual loop (current per-loop limit 128). Newton reaches entrypoint charge
8,008 (current limit 4,096). These need source-specific performance/preflight
profiles, not a global cap increase.

### Indexed vector lanes (3)

```text
classicNoisedeck/lensDistortion:lensDistortion
filter/grade:lut
filter/prismaticAberration:prismaticAberration
```

Lens Distortion and Prismatic Aberration use literal `hsv[0..2]` component
writes/reads. LUT uses induction-indexed Vec3 lanes across several three-trip
loops. Neither form follows from Task 19/20 array indexing; vector lane
indexing needs its own lvalue/range/materialization proof.

### Remaining exact first blockers

| Family | Exact keys |
| --- | --- |
| Unsupported `^` overload | `synth/bitwise:bitwise`, `synth/perlin:perlin` |
| `round` | `filter/pixelSort:gatherSorted`, `filter/posterize:posterize` |
| Varying/stage interface | `filter/grime:grime`, `filter/wormhole:deposit` |
| Sampler function parameter (validator passes; emitter cannot spell it) | `mixer/focusBlur:focusBlur` |
| `all` | `filter/extrude:extrude` |
| `any` | `filter/waves:waves` |
| `floatBitsToUint` | `classicNoisedeck/caustic:caustic` |
| `reflect` | `filter/lighting:lighting` |
| `tanh` | `synth/curl:curl` |
| Matrix return | `filter/rotate:rot` |
| `inout` parameter | `filter/watercolor:wcSimplify` |
| `mat4` | `classicNoisedeck/glitch:glitch` |
| Uniform block | `synth/remap:remap` |

## Bounded next-family map

The first-blocker table should be implemented as narrow families, not one
expanding vocabulary batch:

| Risk | Candidate family | Exact near-term members | Boundary |
| ---: | --- | --- | --- |
| 1 | Already admitted vocabulary | Degauss, then CRT | Allowlist/provenance/oracle work only; no language change |
| 2 | Source-qualified immutable scalar/vector constants plus source-const loop bounds | A diagnostic in-memory constant projection leaves Bloom Gather, Directional Blur, Reindex Stats, Smooth Edge, Spin Blur, Stroke Smear, Vaseline, and Wind validator/emitter-clean | Must inject immutable automatic locals by dependency closure; never C++ static/global; source-specific loop proof remains separate |
| 3 | Small pure builtin/overload additions | `round`, `all`, `any`, `reflect`, `tanh`, narrow scalar XOR/bit conversion | Separate overload, F32, signed-word, and canonical-runtime contracts; do not bundle by syntax count |
| 4 | Bounded vector-lane indexing | Lens Distortion and Prismatic first; LUT separately | Literal versus induction index and writable-lane proof are distinct |
| 5 | Function/stage ABI | Focus Blur sampler parameter; Rotate matrix return; Watercolor `inout`; Grime/Wormhole varyings; Remap uniform block | Each changes ownership/calling/render-stage contracts |
| 6 | Dynamic/large work | resource/uniform loops, Median, Gabor/Julia/Newton | Binding preflight, exact charge, early-return, and hot-path measurement required |
| 7 | Aggregate tables/matrices/mutable globals | palette/glyph/normal-map/classic tables, `mat3`/`mat4`, synth Shape state | Layout, initialization, copy/escape, and concurrency proofs |
| 8 | Derivative execution ABI | the 16 derivative-first keys | Preserve hold until neighbor/border/scheduling semantics exist |

The diagnostic constant projection used macros only to expose later blockers;
it is not an implementation proposal and was never written to disk. A real
source-constant feature must retain stable typed symbols and canonical F32
storage/materialization behavior.

## Task 21 exact profile: Degauss

### Provenance

| Field | Locked value |
| --- | --- |
| Key/runtime key | `filter/degauss:degauss` |
| Source | `sources/filter/degauss/degauss.glsl` |
| Raw bytes / SHA-256 | `10803` / `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` |
| Normalized bytes / SHA-256 | `10512` / `7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560` |
| Runtime defines | `{}` |
| Numeric literal contract | `glsl-f32` |
| Compatibility transform | none |
| Canonical factory | `canonicalFactory45`; factory-text SHA-256 `f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38` |
| Canonical generated runtime | `src/effects/generated/canonical-kernels.js`; SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Typed shape | 17 functions; zero loops; acyclic call graph; no derivatives/varyings/blocks/arrays/matrices |
| Function tuple fingerprint | `f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a` |
| Whole-program fingerprint | `73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d` |

The fingerprint is a drift alarm over the current typed representation, not a
replacement for source/factory/binding hashes.

### Exact bindings and metadata

```text
TAU:const float@1 (source global, not a binding)
inputTex:sampler2D@2/S1
resolution:vec2@3
tileOffset:vec2@4
fullResolution:vec2@5
time:float@6
displacement:float@7
speed:float@8
seed:int@9
direction:float@10
fragColor:vec4@11 (output)
```

Pass route is `inputTex <- inputTex`, `fragColor -> outputTex`; pass aliases
are identity mappings for `direction`, `displacement`, `seed`, and `speed`.
Metadata defaults are `direction=0`, `displacement=0.0625`, `seed=1`, and
`speed=1`. Resolution, tile/full resolution, and time are runtime bindings.

### Why no new capability is needed

Current validation and typed emission both pass directly. The source uses one
already-admitted source `const float`, ordinary scalar/vector functions and
constructors, `uint`/integer vector conversions, scalar integer `%`, level-zero
`texelFetch`, supported builtins, conditionals/returns, and assignments. It
has no loop, array, derivative, matrix, struct, varying, uniform block, sampler
parameter, or non-`in` helper argument.

Canonical `wrap_index` also uses JavaScript `%`. Its live inputs are clamped
nonnegative `x0+1`/`y0+1` with positive texture dimensions, so it does not
introduce Sacred Geometry's untruncated-division issue or a negative-remainder
difference. All conditions are scalar; there is no typed-array Boolean
truthiness hazard. No compatibility transform is justified by inspection.

The normal nonzero-displacement path performs one original level-zero fetch
and calls `warped_channel_value` for channels 0, 1, and 2. Each call samples a
four-fetch wrapped bilinear footprint, for 13 dynamic level-zero fetches per
pixel. With nonzero time and speed, each channel evaluates both base and time
simplex noise. This is compute-heavy but fixed work: there is no unbounded loop,
allocation, recursion, or indirect call.

### Required Task 21 verification

Freeze direct canonical-factory oracles before implementation. At minimum:

1. `displacement=0` must take the exact-copy early return.
2. Nonzero displacement with `time=0` or `speed=0` must exercise the base-noise
   path without the second time-noise evaluation.
3. Nonzero time/speed with a nondefault F32 displacement, seed, and positive
   and negative direction must exercise all three channel calls.
4. Include tiled (`fullResolution` larger than output, nonzero `tileOffset`)
   and untiled cases so both maximum-displacement branches run.
5. Use asymmetric non-square F32 input with edge/corner contrast so all four
   bilinear fetches and wrap-around are observable. Include nontrivial alpha:
   the normal path clamps original alpha while the zero-displacement path
   returns it unchanged.

Record source/canonical hashes, exact binding order, all uniform F32 words,
top-down storage and bottom-left fragment coordinates, F32/RGBA8 hashes,
lane-bit probes, repeat identity, and mutation sensitivity for channel order,
wrap indices, displacement clamp, direction rotation, and alpha. Compile and
test debug/release with sanitizers; assert no hot-path allocation or indirect
dispatch. RGBA8 alone is insufficient.

Negative tests must reject key/source/factory/define/binding drift, a sampler
slot/type mismatch, nonzero `texelFetch` LOD, a changed `%` site/type, added
loop/array/derivative/matrix/stage construct, a compatibility transform entry,
or any attempt to let this allowlist addition admit another key.

## Runner-up profile, explicitly not Task 21: CRT

CRT also passes current validation and emission, but its independent risk
profile merits a separate oracle/review:

| Field | Locked value |
| --- | --- |
| Key | `filter/crt:crt` |
| Source | `sources/filter/crt/crt.glsl` |
| Raw bytes / SHA-256 | `19560` / `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c` |
| Normalized bytes / SHA-256 | `18054` / `acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe` |
| Defines / transform | `{}` / none |
| Canonical factory | `canonicalFactory44`; factory-text SHA-256 `6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303` |
| Shape/fingerprints | 35 functions, zero loops; function tuple `f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72`; whole program `f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc` |

Its bindings are `inputTex:sampler2D@4/S1`, `resolution:vec2@5`,
`tileOffset:vec2@6`, `fullResolution:vec2@7`, `time:float@8`,
`speed:float@9`, `seed:int@10`, `alpha:float@11`, and
`renderScale:float@12`, with `fragColor:vec4@88`. Source constants are
`PI@1`, `TAU@2`, and `INV_THREE@3`. Metadata defaults are `alpha=0.5`,
`seed=1`, and `speed=1`; render scale and coordinate values are runtime-owned.

The canonical compiler explicitly renames the source's `float time=time`,
`float speed=speed`, and later `float alpha=base_sample.w` locals to
`_local_time_1`, `_local_speed_1`, and `_local_alpha_1`. The current emitter
has corresponding stable-symbol shadow handling, but this and CRT's much
larger chained noise/color path require dedicated alias-sensitive oracles.
That is a verification burden, not a new general capability, and is why CRT is
not bundled into Task 21.

## Task 21 exclusions

Task 21 must add only Degauss to the sorted typed/public catalog and retain the
current capability/type/operator/builtin lists unchanged. It does not include
CRT, any global-constant generalization, source-const loop bounds, vector
indexing, new builtin, dynamic/large loop, sampler parameter, matrix/aggregate,
varying/uniform-block/stage ABI, derivative execution, or another array
profile. It must not alter Task 19/20 proofs or Sacred Geometry's exact Star
compatibility transform.

If direct canonical Degauss oracles uncover a semantic mismatch, stop and
reclassify it; do not add a speculative transform or silently bundle CRT to
preserve the projected count.
