# Task 13 planning: `texelFetch` frontier

## Model and method

This is a read-only projection of the post-Task12 state, not an implementation-state claim: 57 typed corpus programs plus immutable legacy public factories for `filter/invert:inv` and `synth/solid:solid`, for 59 public factories and 153 public-unported corpus programs. I provisionally admitted exactly the Task12 `mod` capability/signatures, then parsed every one of those 153 programs with authoritative metadata defaults, ran the typed capability validator, and ran the typed emitter. The groups below are first blockers after that model.

## Recommendation: Task 13 should add exactly eight `texelFetch` programs

This is the largest coherent low-risk frontier that completes individual executable factories without broadening unrelated language features. The existing native sampler already exposes `texel_fetch_bottom_left`; Task 13 only needs a schema-locked `texelFetch` capability, the exact emitter spelling/wrapper, and narrow typed call validation. It does not require loops, arrays/indexing, globals, matrices, structs, UBOs, varyings, derivatives, out/inout, or a render graph.

### Exact new keys and authoritative default define maps

All maps are exactly `{}`:

- `filter/bloom:brightPass` — `{}`
- `filter/bloom:composite` — `{}`
- `filter/fibers:fibersBlend` — `{}`
- `filter/normalize:apply` — `{}`
- `filter/pixelSort:luminance` — `{}`
- `filter/reindex:nmReindexApply` — `{}`
- `filter/scratches:scratchesBlend` — `{}`
- `filter/strayHair:strayHairBlend` — `{}`

### Required semantics and limits

- Admit only `texelFetch(sampler2D, ivec2, int)` returning `vec4`, with the third argument restricted to the pinned level-zero form. Reject texture arrays, other sampler classes, floating coordinates, non-ivec2 coordinates, nonzero/mip selection, `textureLod`, and all unrelated builtin expansion.
- Emit a dedicated typed helper calling the existing `texel_fetch_bottom_left(surface, x, y)` primitive and return a `glsl::Vec4`. Preserve its bottom-left integer-coordinate convention, top-down `Surface` storage conversion, edge clamping, and Float32 stored lanes; do not substitute normalized `texture()` sampling.
- Preserve the scalar/vector boundary already established by the frontend: integer `ivec2` coordinates stay integer through fetch. Do not coerce `ivec2` uniforms to canonical float vectors; `filter/strayHair:strayHairBlend` specifically declares integer `tileOffset` and `fullResolution` and also requires `renderScale`.
- Schema and emitter tests must be fail-closed for every malformed arity/type and verify no accidental admission of `textureLod`, `texelFetch` mip levels, derivatives, loops, or indexing. Runtime tests must lock negative/out-of-range coordinate clamping, bottom-left row selection, alpha, and byte-identical Float32 output.

### Binding and effect-graph caveats

The factories are individually executable only when callers supply the metadata-declared intermediate surfaces; Task 13 must not add adapters or claim whole-effect completion.

- `filter/bloom:brightPass` is bloom pass 1 of 3 (`inputTex -> _brightTex`); `filter/bloom:composite` is pass 3 and needs `inputTex` plus caller-supplied `bloomTex`. The unported `ntapGather` middle pass remains blocked by globals.
- `filter/normalize:apply` is pass 4 and needs `inputTex` plus caller-supplied 1x1 `statsTex`; its reduce/stats producers remain loop-blocked.
- `filter/pixelSort:luminance` is pass 2 and reads caller-supplied prepared input; the remaining pixel-sort pipeline still has globals and loops.
- `filter/reindex:nmReindexApply` is pass 3 and needs `inputTex`, caller-supplied 1x1 `statsTex`, and `uDisplacement`; its stats/reduce producers remain global-blocked.
- `filter/fibers:fibersBlend`, `filter/scratches:scratchesBlend`, and `filter/strayHair:strayHairBlend` are single blend passes needing `inputTex`, `overlayTex`, and `alpha` (plus the integer-system binding caveat for strayHair).

### Secondary blockers deliberately excluded

The other two post-Task12 `texelFetch`-first programs are excluded because adding only fetch immediately exposes loops:

- `filter/pixelSort:computeRank` — `{}` — bounded sample loop.
- `filter/pixelSort:gatherSorted` — `{}` — bounded rank-search loop.

## Post-Task12 first-blocker audit (153 public-unported programs)

### texelFetch (10)

- `filter/bloom:brightPass`
- `filter/bloom:composite`
- `filter/fibers:fibersBlend`
- `filter/normalize:apply`
- `filter/pixelSort:computeRank`
- `filter/pixelSort:gatherSorted`
- `filter/pixelSort:luminance`
- `filter/reindex:nmReindexApply`
- `filter/scratches:scratchesBlend`
- `filter/strayHair:strayHairBlend`

### loops (41)

- `filter/chrome:chBlurH`
- `filter/chrome:chBlurV`
- `filter/craquelure:craquelure`
- `filter/grade:lut`
- `filter/hatch:hatch` — `{"MODE":0}`
- `filter/highPass:hpBlurH`
- `filter/highPass:hpBlurV`
- `filter/morphology:morphA` — `{"SHAPE":0}`
- `filter/morphology:morphB` — `{"SHAPE":0}`
- `filter/normalize:reduce`
- `filter/normalize:reduceMinmax`
- `filter/normalize:statsFinal`
- `filter/oilPaint:oilPost` — `{"MODE":1}`
- `filter/patchwork:patchwork`
- `filter/photocopy:pcBlurH`
- `filter/photocopy:pcBlurV`
- `filter/pixelSort:findBrightest`
- `filter/plasticWrap:pwBlurH`
- `filter/plasticWrap:pwBlurV`
- `filter/relief:rlBlurH` — `{"MODE":0}`
- `filter/relief:rlBlurV` — `{"MODE":0}`
- `filter/reverb:reverb`
- `filter/scatter:scatterSmooth` — `{"MODE":0}`
- `filter/stamp:stBlurH`
- `filter/stamp:stBlurV`
- `filter/stamp:stThreshold`
- `filter/stipple:stipple` — `{"MODE":0}`
- `filter/strokes:stkPost` — `{"MODE":0}`
- `filter/unsharpMask:usmBlurH`
- `filter/unsharpMask:usmBlurV`
- `filter/wormhole:blend`
- `filter/zoomBlur:zoomBlur`
- `mixer/focusBlur:focusBlur`
- `mixer/mashup:mashup`
- `mixer/shadow:shadow`
- `synth/cell:cell`
- `synth/curl:curl` — `{"OCTAVES":1,"OUTPUT_MODE":3,"RIDGES":true}`
- `synth/gabor:gabor`
- `synth/gradient:gradient`
- `synth/mandala:mandala`
- `synth/sacredGeometry:sacredGeometry`

### arrays/indexing (13)

- `classicNoisedeck/cellRefract:cellRefract` — `{"KERNEL":0,"SHAPE":1}`
- `classicNoisedeck/effects:effects` — `{"EFFECT":0,"FLIP":0}`
- `classicNoisedeck/kaleido:kaleido` — `{"DIRECTION":2,"KERNEL":0,"LOOP_OFFSET":10,"METRIC":0}`
- `classicNoisedeck/lensDistortion:lensDistortion`
- `classicNoisedeck/refract:refract`
- `filter/celShading:celShadingEdges`
- `filter/median:median` — `{"RADIUS":3}`
- `filter/osd:osd`
- `filter/outline:outlineSobel`
- `filter/prismaticAberration:prismaticAberration`
- `filter/sharpen:sharpen`
- `filter/sobel:sobel`
- `synth/testPattern:testPattern`

### globals (58)

- `classicNoisedeck/bitEffects:bitEffects` — `{"COLOR_SCHEME":20,"FORMULA":0,"INTERP":0,"MASK_COLOR_SCHEME":1,"MASK_FORMULA":10,"MODE":1}`
- `filter/adjust:adjust`
- `filter/bloom:ntapGather`
- `filter/blur:blurH`
- `filter/blur:blurV`
- `filter/celShading:celShadingColor`
- `filter/clouds:clouds`
- `filter/colorspace:colorspace`
- `filter/crt:crt`
- `filter/degauss:degauss`
- `filter/directionalBlur:directionalBlur`
- `filter/dither:dither`
- `filter/edge:edge`
- `filter/emboss:emboss` — `{"STYLE":0}`
- `filter/extrude:extrude` — `{"DEPTH_SOURCE":0,"EXTRUDE_TYPE":0}`
- `filter/fxaa:fxaa`
- `filter/glyphMap:glyphMap`
- `filter/grade:creative`
- `filter/grade:hslSecondary`
- `filter/grade:primary`
- `filter/grade:vignette`
- `filter/grade:wheels`
- `filter/grain:grain`
- `filter/halftone:halftone` — `{"MODE":0,"PATTERN":0}`
- `filter/lens:lens`
- `filter/lightLeak:lightLeak`
- `filter/lowPoly:lowPoly` — `{"LP_BORDER":0,"LP_LIGHT":0}`
- `filter/normalMap:normalMap`
- `filter/octaveWarp:octaveWarp`
- `filter/parallax:parallax`
- `filter/pixelSort:finalize`
- `filter/pixelSort:prepare`
- `filter/polar:polar`
- `filter/posterize:posterize`
- `filter/reindex:nmReindexReduce`
- `filter/reindex:nmReindexStats`
- `filter/rotate:rot`
- `filter/scanlineError:scanlineError`
- `filter/skew:skew`
- `filter/smooth:smoothBlend`
- `filter/smooth:smoothEdge`
- `filter/snow:snow`
- `filter/spinBlur:spinBlur`
- `filter/strokes:stkSmear` — `{"MODE":0}`
- `filter/tetraColorArray:tetraColorArray`
- `filter/tetraCosine:tetraCosine`
- `filter/tile:tile`
- `filter/tunnel:tunnel`
- `filter/vaseline:upsample`
- `filter/wind:wind` — `{"METHOD":1}`
- `mixer/cellSplit:cellSplit`
- `synth/bitwise:bitwise`
- `synth/mandelbrot:mandelbrot`
- `synth/noise:noise` — `{"LOOP_OFFSET":300,"NOISE_TYPE":10}`
- `synth/osc2d:osc2d`
- `synth/perlin:perlin` — `{"DIMENSIONS":2}`
- `synth/shape:shape` — `{"LOOP_A_OFFSET":40,"LOOP_B_OFFSET":30}`
- `synth/subdivide:subdivide`

### matrices beyond mat2 (8)

- `classicNoisedeck/cellNoise:cellNoise`
- `classicNoisedeck/colorLab:colorLab`
- `classicNoisedeck/fractal:fractal`
- `classicNoisedeck/glitch:glitch`
- `classicNoisedeck/moodscape:moodscape` — `{"COLOR_MODE":2,"NOISE_TYPE":10}`
- `classicNoisedeck/noise:noise` — `{"COLOR_MODE":6,"LOOP_OFFSET":300,"METRIC":0,"NOISE_TYPE":10,"REFRACT_MODE":2}`
- `classicNoisedeck/shapeMixer:shapeMixer` — `{"LOOP_OFFSET":10}`
- `classicNoisedeck/shapes:shapes` — `{"LOOP_A_OFFSET":40,"LOOP_B_OFFSET":30}`

### derivatives (8)

- `filter/bulge:bulge`
- `filter/lensWarp:lensWarp`
- `filter/pinch:pinch`
- `filter/pondRipples:pondRipples` — `{"STYLE":2,"WRAP":0}`
- `filter/spiral:spiral`
- `filter/step:step`
- `filter/warp:warp`
- `mixer/distortion:distortion`

### other builtins (4)

- `classicNoisedeck/caustic:caustic` — `{"NOISE_TYPE":10}`
- `filter/lighting:lighting`
- `filter/oilPaint:oilFlatten` — `{"MODE":1}`
- `filter/waves:waves`

### structs (4)

- `filter/historicPalette:historicPalette`
- `filter/palette:palette`
- `synth/julia:julia`
- `synth/newton:newton`

### UBOs (1)

- `synth/remap:remap`

### parameters (1)

- `filter/watercolor:wcSimplify`

### varyings (5)

- `filter/grime:grime`
- `filter/spookyTicker:spookyTicker`
- `filter/texture:texture` — `{"MODE":3}`
- `filter/wobble:wobble`
- `filter/wormhole:deposit`

## Projected counts after Task 13

- Typed corpus programs: `57 + 8 = 65`.
- Public catalog factories: `65 + 2 immutable legacy = 67`.
- Public-unported corpus programs: `212 - 67 = 145`.

The next remaining large frontiers are globals (58), loops (43 after the two texelFetch cases are reclassified), arrays/indexing (13), derivatives (8), matrices beyond mat2 (8), then smaller unrelated builtin/struct/interface groups. None should be folded into the fetch-only task.
