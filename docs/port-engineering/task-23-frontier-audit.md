# Projected post-Task-22 remaining-frontier audit

Date: 2026-08-11  
Scope: read-only parser, typed-IR, proof, validator, emitter, pinned-corpus,
canonical-factory, and public-dispatch inspection. No repository file or Git
state was changed. This projection assumes Task 22 is accepted exactly as
briefed: CRT is added with its key-locked six-site compatibility transform and
no general capability, proof, type, operator, builtin, resource, or ABI change.

## Decision

The projected baseline is exact:

| State | Typed factories | Public factories | Publicly unported |
| --- | ---: | ---: | ---: |
| Current accepted Task 21 tree | 115 | 117 | 95 |
| Projected after exact Task 22 CRT | **116** | **118** | **94** |

All 94 projected remaining programs were reparsed with their authoritative
metadata define maps, semantically analyzed, passed through the current proof
attachment chain, and then attempted against the current validator and typed
emitter. The first-blocker census is unchanged except that Degauss and CRT are
no longer in the remaining set.

The best next bounded slice is:

```text
source-global-literal-int-counted-bound-v1
  filter/bloom:ntapGather
  filter/directionalBlur:directionalBlur
  filter/spinBlur:spinBlur
  filter/strokes:stkSmear
  filter/vaseline:upsample
  filter/wind:wind
```

It extends the existing automatic source-constant materialization from
`const float` to one exact form, top-level read-only `const int NAME = INTEGER
LITERAL`, and lets the existing counted-loop proof resolve that stable global
symbol as a bound. It changes no safety cap and adds no new loop syntax. A
diagnostic in-memory macro projection, used only to expose later blockers,
makes all six validate and emit with the current vocabulary.

This is a six-key publication slice, not a claim that every global integer or
every loop is now safe. The projected result would be **122 typed / 124 public
/ 88 unported**.

One apparent seventh match must be held. `filter/reindex:nmReindexStats`
becomes structurally validator/emitter-clean under the same literal-int bound
projection, but its public CPU factory is the hand-written
`reindexStatsFactory`, not `canonicalFactory120`. That adapter applies eager
F32 OKLab/lightness arithmetic and its own tile walk. It needs a separate
public-adapter compatibility audit and oracle; it is not part of Task 23.

## Audit basis and drift boundary

The current Task 21 checkout and projected Task 22 boundary were authenticated
without Git:

| Artifact | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/parser.py` | `1b2114be2712eba63dcb8651323a9387a9f049420ef024e09c57fe8f101849cc` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/frontend/semantic.py` | `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b` |
| `tools/glslcpp/frontend/body_semantic.py` | `4a6dc290c22b6a372d0837040596341a142284fccf42a0eaf7d657a78b419f59` |
| `tools/glslcpp/frontend/loop_proof.py` | `830ed013d791eb201dfbac8f1a65996b6427656a0e2c7dc953df62dd8c3cb6c8` |
| `tools/glslcpp/generate_typed_slice.py` | `ea51119950c7e7262282e57a85db895583125cc76d174d7acff51c57cea4dad1` |
| `tools/glslcpp/emit_typed_cpp.py` | `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11` |
| `tools/glslcpp/typed_slice.json` | `e01050bd3e71df32df522da741a7087896fea500548bebe988f181bee4bfb802` |
| Task 22 brief | `f251e87501abde8305a7c4434ba5c406374d0903ef50d75d8628d286adef478c` |

The current slice contains 115 programs, its generated manifest contains 115,
and the generated public header contains 117 factory declarations. Projecting
only CRT gives 116/118/94 over the 212-program corpus.

Task 23 must hard-gate on accepted Task 22 final evidence and rerun this census.
Task 22 is expected to change the emitter for one authenticated CRT carrier;
any broader effect on a remaining program invalidates this projection.

## Exact first-blocker census for all 94

| First current result | Count |
| --- | ---: |
| Unsupported top-level global declaration | 31 |
| Unproved counted-loop program | 25 |
| `dFdx` derivative | 11 |
| `fwidth` derivative | 5 |
| Counted loop exceeds an existing safety cap | 3 |
| Vector/component index expression | 3 |
| Scalar XOR form outside current overload | 2 |
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
| **Total** | **94** |

Every failure came from the validator except
`mixer/focusBlur:focusBlur`, which passes the validator and fails the emitter
at a user-function `sampler2D` parameter.

### Unsupported top-level globals: 31

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

These are not one capability:

- Sixteen first expose only initialized read-only scalar/vector constants
  beyond `const float`: Bit Effects, Edge, Emboss, FXAA, Glyph Map, the five
  Grade programs, Grain, Scanline Error, Smooth Edge, Snow, Texture, and
  Wobble. Only Smooth Edge is immediately clean after its one literal `const
  vec3`; the others expose later word, indexing, loop, derivative, adapter, or
  sampling work.
- Seven use read-only `const mat3` color transforms: Cell Noise, Color Lab,
  Moodscape, Shape Mixer, Shapes, Adjust, and Colorspace.
- Cell Refract and Kaleido use uninitialized mutable global `float[9]` tables.
- Historic Palette, Normal Map, OSD, Palette, and Spooky Ticker require
  distinct global array/struct/table lifetime and index proofs.
- `synth/shape:shape` uses mutable uninitialized `aspectRatio` and
  `globalCoord`; source-constant work must never admit it.

### Unproved counted loops: 25

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

The minimal subfamilies are:

- Twelve use source-global literal `const int` bounds: Bloom Gather,
  Directional Blur, Dither, Light Leak, Parallax, both Reindex passes, Spin
  Blur, Stroke Smear, Vaseline, Wind, and Mandelbrot. Projecting only the
  constant and its bound resolves six canonical-public programs plus the
  adapter-backed Reindex Stats. Dither retains an unproved loop, Light Leak an
  `out` parameter, Parallax `textureLod`, Reindex Reduce an overlarge/unproved
  scan, and Mandelbrot a safety-charge violation.
- Nine use uniform, texture-size, or otherwise runtime-derived bounds: classic
  Fractal, classic Noise, Blur H/V, Normalize Stats Final, Oil Flatten, Tetra
  Color Array, synth Noise, and Test Pattern. They need enforced runtime work
  budgets, not source-constant recognition.
- Median has four data-dependent `while` loops.
- classic Effects and Zoom Blur use float induction variables.
- Smooth Blend has an early `return` inside its otherwise literal search loop.

The three existing-cap violations remain `synth/gabor:gabor` (effective depth
4), `synth/julia:julia` (1,000 trips), and `synth/newton:newton` (entry charge
8,008). None justifies a global cap increase.

### Derivatives: 16, still held

`dFdx` is first for:

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

`fwidth` is first for:

```text
filter/celShading:celShadingColor
filter/halftone:halftone
filter/stamp:stThreshold
filter/step:step
filter/stipple:stipple
```

This remains an execution-ABI family. A builtin spelling does not supply
quad/neighborhood evaluation, tile-border ownership, scheduling, helper-call
derivatives, or edge semantics. It is high risk despite the large apparent
unlock count and is not a Task 23 candidate.

### Index, word, round, varying, and singleton frontiers

| Family | Exact first-blocked keys | Direct clean result after only that feature |
| --- | --- | --- |
| Literal vector lane indexing | `classicNoisedeck/lensDistortion:lensDistortion`, `filter/prismaticAberration:prismaticAberration` | Both pass after replacing only literal Vec3 indices with equivalent swizzles |
| Induction-indexed vector lanes | `filter/grade:lut` | Still separate: 20 read/write `vec3[i]` sites over proved three-trip loops |
| Scalar XOR | `synth/bitwise:bitwise`, `synth/perlin:perlin` | Perlin passes after only two `uint ^ uint` sites; Bitwise next needs signed `&` and `|` |
| Scalar `round` | `filter/pixelSort:gatherSorted`, `filter/posterize:posterize` | Gather Sorted passes after one scalar site; Posterize next needs `fwidth(vec3)` |
| Varying/stage interface | `filter/grime:grime`, `filter/wormhole:deposit` | Requires stage ownership/interpolation contract; not a declaration-only change |
| Sampler helper parameter | `mixer/focusBlur:focusBlur` | Validator-clean, emitter/ABI blocked |
| Boolean reductions | `filter/extrude:extrude` (`all`), `filter/waves:waves` (`any`) | Separate overload/control semantics |
| Exact numeric builtins | `classicNoisedeck/caustic:caustic` (`floatBitsToUint`), `filter/lighting:lighting` (`reflect`), `synth/curl:curl` (`tanh`) | Each needs its own numeric/overload oracle |
| Function ABI | `filter/rotate:rot` (matrix return), `filter/watercolor:wcSimplify` (`inout`) | Copy/alias/call ABI work |
| Type/resource ABI | `classicNoisedeck/glitch:glitch` (`mat4`), `synth/remap:remap` (uniform block) | Layout and binding work |

The literal-index projection covers exactly 11 sites: eight in Lens
Distortion and three in Prismatic Aberration. All are Vec3 indices with
literal lanes 0, 1, or 2; they include both reads and writes. Grade LUT's 20
induction-indexed sites are not part of that slice.

The round projection is also narrower than its two-key first-blocker count.
The existing native runtime already implements JavaScript-compatible
`floor(value + 0.5)` and has positive and negative half tests. Gather Sorted's
sole round input is a nonnegative normalized x coordinate times `width - 1`.
Posterize remains derivative-blocked after round.

## Risk-adjusted ranking of the next three bounded slices

| Rank | Bounded slice | Directly unlocked | Risk | Rationale |
| ---: | --- | ---: | --- | --- |
| 1 | Literal source-global `const int` plus global-bound counted proof | **6** | Medium | One exact new declaration form, automatic-local materialization, and one proof input; all loop shapes and caps already exist; six public factories are canonical |
| 2 | Literal Vec3 lane indexing, reads and writes | **2** | Low-medium | Eleven exact in-range sites can lower to stable lane access; no dynamic range proof, array ABI, or public adapter |
| 3 | Scalar `round` exposure for Gather Sorted | **1** | Low | Runtime semantics and negative-half tests already exist; one scalar site; no adapter; Posterize remains excluded |

Runner-ups are the one-key Smooth Edge literal-`const vec3` slice, the one-key
Perlin scalar-uint XOR slice, and the one-key Focus Blur sampler-parameter ABI.
Smooth Edge is small but establishes a vector-valued source-global form;
Perlin requires word-semantics review; Focus Blur changes a function/resource
calling convention. The derivative family ranks below all of them on risk.

## Recommended Task 23 exact candidate inspection

### Provenance, factories, and loop charges

| Key | Defines | Raw bytes / SHA-256 | Normalized SHA-256 | Functions | Projected loop proof | Public canonical factory / text SHA-256 |
| --- | --- | --- | --- | ---: | --- | --- |
| `filter/bloom:ntapGather` | `{}` | `2196` / `f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237` | `1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81` | 1 | one loop, 64 trips, depth 1, charge 64 | `canonicalFactory23` / `a737ac48f663f041f763677680ab5d5282482ab6d10143939de055b980c4207c` |
| `filter/directionalBlur:directionalBlur` | `{}` | `1153` / `1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c` | `587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668` | 2 | one loop, 32 trips, depth 1, charge 32 | `canonicalFactory47` / `a3803238488c9bd2fe786b931a0a2ba81a057d02f984017d8e10073c68873344` |
| `filter/spinBlur:spinBlur` | `{}` | `3077` / `a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405` | `b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee` | 3 | one loop, 32 trips, depth 1, charge 32 | `canonicalFactory145` / `c6b97d30339acd21fc01d2d2cd31073c62d2ba82dbb80e95d9457b0f59737547` |
| `filter/strokes:stkSmear` | `{"MODE":0}` | `14787` / `dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db` | `796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15` | 13 | three loops, max depth 2, product 24, charge 72 | `canonicalFactory155` / `8f82fbdc740e4bf5448e53823c833e22f37db0aacadad01bc4983a4e58e72010` |
| `filter/vaseline:upsample` | `{}` | `2524` / `39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461` | `1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93` | 3 | one loop, 32 trips, depth 1, charge 32 | `canonicalFactory170` / `322ba53c3b001878f026c615998086ef7732277b5f2d2401064ea2497cb6113a` |
| `filter/wind:wind` | `{"METHOD":1}` | `3520` / `68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22` | `665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4` | 2 | one loop, 128 trips, depth 1, charge 128 | `canonicalFactory177` / `163a65997398acd140ec10572d9253914d1659fc240187c1eae5a9de354810dd` |

The pinned canonical runtime is
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.
For every row above, public `kernelFactories.get(key)` is the exact same
function object as `canonicalKernelFactories[key]`, and
`canonicalAdapterFactories[key]` is absent. Factory text contains the exact
integer value and counted loop shape from source. The integer values 24, 32,
64, and 128 are exactly represented in both JavaScript Number and C++
`int32_t`.

No hidden public-dispatch compatibility transform was found for these six.
This is stronger than filename inspection: public/canonical function identity
was checked at runtime. It does not replace frozen per-key output and mutation
oracles before implementation.

### The adapter-backed near-match that must remain out

| Field | Reindex Stats value |
| --- | --- |
| Key | `filter/reindex:nmReindexStats` |
| Source SHA-256 | `06525e054fc4910e7bc53345ad656071d2fcb33fc897f4aa35e8fc59b6f0b951` |
| Canonical factory | `canonicalFactory120`; text SHA-256 `0b59d682d882cc0f01348e950c114aaaeb4249f23094741060e482840c7200b3` |
| Public factory | `reindexStatsFactory`; text SHA-256 `bf9edac9f940e4f435ef55712245be8821b5893f04d68af11d32a059cd0d060f` |
| Adapter source | `src/effects/adapters/f32-color.js`; SHA-256 `b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046` |
| Structural projection | two 8-trip loops, depth 2, product 64, entry charge 72; validator/emitter-clean |

The adapter clamps and eagerly F32-rounds sRGB conversion, cube roots, OKLab
matrix arithmetic, extrema, and output storage, and it performs an explicit
top-down-surface/bottom-left-shader coordinate tile walk. Raw canonical
factory output is therefore not an acceptable reference without a dedicated
comparison. Task 23 must reject this key even though the language projection
passes.

## Task 23 proposed proof boundary

A later Task 23 brief may authorize only after accepted Task 22:

1. the six exact keys, source identities, and authoritative define maps in the
   table above;
2. top-level `const int` declarations initialized by exactly one nonnegative
   decimal integer literal, with stable symbol identity, no write/alias/escape,
   and no dependency expression;
3. automatic immutable `int32_t` materialization by reference closure in each
   function that reads the symbol, never namespace/global/function-static
   storage;
4. counted-loop proof lookup of that authenticated global symbol, retaining
   the existing fresh local `int` induction, `<`/`<=`, unit increment,
   break/continue, no loop-return, trip/depth/product/entry-charge, and
   acyclic-call-graph rules;
5. the exact existing limits: at most 128 trips, depth 3, lexical product
   4,096, and entrypoint charge 4,096;
6. direct public-canonical oracles for all six, including early-break extrema,
   default/nondefault uniforms, tiled/full-frame paths where present, complete
   F32 and RGBA8 output, repeat identity, input immutability, fetch/loop-count
   mutations, and Debug/Release/sanitizer/stack/code-shape gates;
7. projected counts 122/124/88 and exact generated isolation from every
   accepted Task 22 block.

It must explicitly exclude `filter/reindex:nmReindexStats`, every other source
global, `const uint`, vector/matrix/array/struct globals, initializer
dependencies, mutable/uninitialized/static globals, dynamic/runtime loop
bounds, new loop forms, safety-cap changes, derivatives, vector indexing,
XOR/round/varying/sampler/function/resource ABI work, compatibility transforms,
and numeric-literal or sampler changes.

The validator and emitter should independently authenticate declaration type,
literal, symbol reads/writes, loop-bound identity, proof metrics, key/source/
defines, and absence of a compatibility carrier. Caller-supplied hashes must
not rescue a forged declaration or proof.

## Audit-only stop

This file selects the Task 23 frontier and proposes its bounded proof surface.
It does not contain a Task 23 implementation design, frozen native oracle, or
implementation brief. Because the selected slice contains six independent
public factories, per-key oracle generation and compatibility-sensitive review
must precede a brief. Stop before implementation.
