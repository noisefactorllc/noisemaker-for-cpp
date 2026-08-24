# Task 12 planning: `mod` frontier

## Scope and method

This is a read-only audit of the pinned corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`. The current typed manifest has 44 programs, leaving 168 of 212 outside the slice. For every remaining program, I parsed it with its authoritative metadata default define map, ran the current typed capability validator, then invoked the typed emitter. Each group below is the *first genuine blocker* reported by that pipeline; it is not a claim that no later blocker exists.

## Recommendation: Task 12 should add exactly 15 programs

Admit the two programs already accepted by the current typed validator/emitter plus the 13 programs that become emitter-clean when only GLSL `mod` is provisionally admitted. This is the largest coherent low-risk slice: one preexisting scalar runtime operation needs an exposed emitter/capability route and vector overloads, but it does not require loops, arrays/indexing, globals, matrices, structs, UBOs/varyings, derivatives, texelFetch, or non-`in` parameters. The typed slice becomes 59 programs; 153 remain outside.

### Exact allowlist entries and default defines

All fifteen authoritative default define maps are exactly `{}`:

- `filter/invert:inv` — `{}`
- `synth/solid:solid` — `{}`
- `classicNoisedeck/coalesce:coalesce` — `{}`
- `classicNoisedeck/composite:composite` — `{}`
- `filter/hs:hs` — `{}`
- `filter/repeat:repeat` — `{}`
- `filter/scale:scale` — `{}`
- `filter/scroll:scroll` — `{}`
- `filter/translate:translate` — `{}`
- `mixer/patternMix:patternMix` — `{}`
- `mixer/shapeMask:shapeMask` — `{}`
- `mixer/split:split` — `{}`
- `mixer/uvRemap:uvRemap` — `{}`
- `synth/modPattern:modPattern` — `{}`
- `synth/pattern:pattern` — `{}`

### Required narrow semantics

- Add one schema-locked `mod` capability and map typed builtin `mod` to `glsl::mod`; retain fail-closed rejection of every other new builtin.
- Preserve GLSL floating `mod(x, y) = x - y * floor(x / y)`, not C/C++ remainder or `std::fmod`. The existing scalar `glsl::mod(double, double)` already delegates to `noisemaker::glsl_mod`; keep its JS-double scalar path rather than adding an accidental early float round.
- Add only componentwise float-vector overloads actually needed by this set (`vec2`/`FloatExpr<2>` with vector or scalar divisor as the typed forms demand). Consume vector lanes at the established float32 boundary and store each result with `f32`, matching the existing `map_float2` convention. Do not generalize integer/vector `%`, arrays, dynamic indexing, or arbitrary new overload families.
- Add RED/GREEN tests for negative operands, non-integer divisors, scalar and vec2 operands, the `abs(mod(v + 1.0, 2.0) - 1.0)` mirror idiom, and per-lane F32 rounding. Add negative emitter/capability tests proving `ceil`, `reflect`, `any`, `floatBitsToUint`, derivatives, and texelFetch remain rejected.
- Regenerate only after the allowlist/schema test proves exactly 59 sorted keys and all new define maps are `{}`.

### Effect-graph / binding caveats

All 15 metadata entries are single-pass, so Task 12 must not introduce an adapter or render graph.

- `classicNoisedeck/coalesce:coalesce` and `classicNoisedeck/composite:composite` each require caller-provided `inputTex` and `tex`; their metadata pass is `render -> outputTex` (with host `mix` mapped to `mixAmt`).
- `mixer/patternMix:patternMix`, `mixer/shapeMask:shapeMask`, `mixer/split:split`, and `mixer/uvRemap:uvRemap` each require both `inputTex` and `tex`; each is a single `render -> outputTex` pass.
- `filter/hs:hs`, `filter/invert:inv`, `filter/repeat:repeat`, `filter/scale:scale`, `filter/scroll:scroll`, and `filter/translate:translate` each require caller-provided `inputTex`; each is a single pass.
- `synth/modPattern:modPattern`, `synth/pattern:pattern`, and `synth/solid:solid` are texture-free generators.

### Why the other ten `mod`-first programs are excluded

After provisionally allowing/emitting `mod`, they immediately hit another unsupported requirement: `classicNoisedeck/caustic:caustic` -> `floatBitsToUint`; `classicNoisedeck/lensDistortion:lensDistortion` and `filter/prismaticAberration:prismaticAberration` -> indexing; `filter/bulge:bulge`, `filter/lensWarp:lensWarp`, `filter/pinch:pinch`, `filter/pondRipples:pondRipples`, `filter/spiral:spiral`, and `filter/warp:warp` -> `dFdx`; `filter/reverb:reverb` -> loop. They are therefore not part of the single-feature Task 12 boundary.

## Complete outside-slice first-blocker audit

### Loops (40)

- `filter/chrome:chBlurH` — `{}`
- `filter/chrome:chBlurV` — `{}`
- `filter/craquelure:craquelure` — `{}`
- `filter/grade:lut` — `{}`
- `filter/hatch:hatch` — `{"MODE":0}`
- `filter/highPass:hpBlurH` — `{}`
- `filter/highPass:hpBlurV` — `{}`
- `filter/morphology:morphA` — `{"SHAPE":0}`
- `filter/morphology:morphB` — `{"SHAPE":0}`
- `filter/normalize:reduce` — `{}`
- `filter/normalize:reduceMinmax` — `{}`
- `filter/normalize:statsFinal` — `{}`
- `filter/oilPaint:oilPost` — `{"MODE":1}`
- `filter/patchwork:patchwork` — `{}`
- `filter/photocopy:pcBlurH` — `{}`
- `filter/photocopy:pcBlurV` — `{}`
- `filter/pixelSort:findBrightest` — `{}`
- `filter/plasticWrap:pwBlurH` — `{}`
- `filter/plasticWrap:pwBlurV` — `{}`
- `filter/relief:rlBlurH` — `{"MODE":0}`
- `filter/relief:rlBlurV` — `{"MODE":0}`
- `filter/scatter:scatterSmooth` — `{"MODE":0}`
- `filter/stamp:stBlurH` — `{}`
- `filter/stamp:stBlurV` — `{}`
- `filter/stamp:stThreshold` — `{}`
- `filter/stipple:stipple` — `{"MODE":0}`
- `filter/strokes:stkPost` — `{"MODE":0}`
- `filter/unsharpMask:usmBlurH` — `{}`
- `filter/unsharpMask:usmBlurV` — `{}`
- `filter/wormhole:blend` — `{}`
- `filter/zoomBlur:zoomBlur` — `{}`
- `mixer/focusBlur:focusBlur` — `{}`
- `mixer/mashup:mashup` — `{}`
- `mixer/shadow:shadow` — `{}`
- `synth/cell:cell` — `{}`
- `synth/curl:curl` — `{"OCTAVES":1,"OUTPUT_MODE":3,"RIDGES":true}`
- `synth/gabor:gabor` — `{}`
- `synth/gradient:gradient` — `{}`
- `synth/mandala:mandala` — `{}`
- `synth/sacredGeometry:sacredGeometry` — `{}`

### Arrays/indexing (11)

- `classicNoisedeck/cellRefract:cellRefract` — `{"KERNEL":0,"SHAPE":1}`
- `classicNoisedeck/effects:effects` — `{"EFFECT":0,"FLIP":0}`
- `classicNoisedeck/kaleido:kaleido` — `{"DIRECTION":2,"KERNEL":0,"LOOP_OFFSET":10,"METRIC":0}`
- `classicNoisedeck/refract:refract` — `{}`
- `filter/celShading:celShadingEdges` — `{}`
- `filter/median:median` — `{"RADIUS":3}`
- `filter/osd:osd` — `{}`
- `filter/outline:outlineSobel` — `{}`
- `filter/sharpen:sharpen` — `{}`
- `filter/sobel:sobel` — `{}`
- `synth/testPattern:testPattern` — `{}`

### Globals (58)

- `classicNoisedeck/bitEffects:bitEffects` — `{"COLOR_SCHEME":20,"FORMULA":0,"INTERP":0,"MASK_COLOR_SCHEME":1,"MASK_FORMULA":10,"MODE":1}`
- `filter/adjust:adjust` — `{}`
- `filter/bloom:ntapGather` — `{}`
- `filter/blur:blurH` — `{}`
- `filter/blur:blurV` — `{}`
- `filter/celShading:celShadingColor` — `{}`
- `filter/clouds:clouds` — `{}`
- `filter/colorspace:colorspace` — `{}`
- `filter/crt:crt` — `{}`
- `filter/degauss:degauss` — `{}`
- `filter/directionalBlur:directionalBlur` — `{}`
- `filter/dither:dither` — `{}`
- `filter/edge:edge` — `{}`
- `filter/emboss:emboss` — `{"STYLE":0}`
- `filter/extrude:extrude` — `{"DEPTH_SOURCE":0,"EXTRUDE_TYPE":0}`
- `filter/fxaa:fxaa` — `{}`
- `filter/glyphMap:glyphMap` — `{}`
- `filter/grade:creative` — `{}`
- `filter/grade:hslSecondary` — `{}`
- `filter/grade:primary` — `{}`
- `filter/grade:vignette` — `{}`
- `filter/grade:wheels` — `{}`
- `filter/grain:grain` — `{}`
- `filter/halftone:halftone` — `{"MODE":0,"PATTERN":0}`
- `filter/lens:lens` — `{}`
- `filter/lightLeak:lightLeak` — `{}`
- `filter/lowPoly:lowPoly` — `{"LP_BORDER":0,"LP_LIGHT":0}`
- `filter/normalMap:normalMap` — `{}`
- `filter/octaveWarp:octaveWarp` — `{}`
- `filter/parallax:parallax` — `{}`
- `filter/pixelSort:finalize` — `{}`
- `filter/pixelSort:prepare` — `{}`
- `filter/polar:polar` — `{}`
- `filter/posterize:posterize` — `{}`
- `filter/reindex:nmReindexReduce` — `{}`
- `filter/reindex:nmReindexStats` — `{}`
- `filter/rotate:rot` — `{}`
- `filter/scanlineError:scanlineError` — `{}`
- `filter/skew:skew` — `{}`
- `filter/smooth:smoothBlend` — `{}`
- `filter/smooth:smoothEdge` — `{}`
- `filter/snow:snow` — `{}`
- `filter/spinBlur:spinBlur` — `{}`
- `filter/strokes:stkSmear` — `{"MODE":0}`
- `filter/tetraColorArray:tetraColorArray` — `{}`
- `filter/tetraCosine:tetraCosine` — `{}`
- `filter/tile:tile` — `{}`
- `filter/tunnel:tunnel` — `{}`
- `filter/vaseline:upsample` — `{}`
- `filter/wind:wind` — `{"METHOD":1}`
- `mixer/cellSplit:cellSplit` — `{}`
- `synth/bitwise:bitwise` — `{}`
- `synth/mandelbrot:mandelbrot` — `{}`
- `synth/noise:noise` — `{"LOOP_OFFSET":300,"NOISE_TYPE":10}`
- `synth/osc2d:osc2d` — `{}`
- `synth/perlin:perlin` — `{"DIMENSIONS":2}`
- `synth/shape:shape` — `{"LOOP_A_OFFSET":40,"LOOP_B_OFFSET":30}`
- `synth/subdivide:subdivide` — `{}`

### Structs (4)

- `filter/historicPalette:historicPalette` — `{}`
- `filter/palette:palette` — `{}`
- `synth/julia:julia` — `{}`
- `synth/newton:newton` — `{}`

### UBOs (1)

- `synth/remap:remap` — `{}`

### Varyings (5)

- `filter/grime:grime` — `{}`
- `filter/spookyTicker:spookyTicker` — `{}`
- `filter/texture:texture` — `{"MODE":3}`
- `filter/wobble:wobble` — `{}`
- `filter/wormhole:deposit` — `{}`

### Derivatives (2)

- `filter/step:step` — `{}`
- `mixer/distortion:distortion` — `{}`

### texelFetch (10)

- `filter/bloom:brightPass` — `{}`
- `filter/bloom:composite` — `{}`
- `filter/fibers:fibersBlend` — `{}`
- `filter/normalize:apply` — `{}`
- `filter/pixelSort:computeRank` — `{}`
- `filter/pixelSort:gatherSorted` — `{}`
- `filter/pixelSort:luminance` — `{}`
- `filter/reindex:nmReindexApply` — `{}`
- `filter/scratches:scratchesBlend` — `{}`
- `filter/strayHair:strayHairBlend` — `{}`

### Matrices beyond mat2 (8)

- `classicNoisedeck/cellNoise:cellNoise` — `{}`
- `classicNoisedeck/colorLab:colorLab` — `{}`
- `classicNoisedeck/fractal:fractal` — `{}`
- `classicNoisedeck/glitch:glitch` — `{}`
- `classicNoisedeck/moodscape:moodscape` — `{"COLOR_MODE":2,"NOISE_TYPE":10}`
- `classicNoisedeck/noise:noise` — `{"COLOR_MODE":6,"LOOP_OFFSET":300,"METRIC":0,"NOISE_TYPE":10,"REFRACT_MODE":2}`
- `classicNoisedeck/shapeMixer:shapeMixer` — `{"LOOP_OFFSET":10}`
- `classicNoisedeck/shapes:shapes` — `{"LOOP_A_OFFSET":40,"LOOP_B_OFFSET":30}`

### Parameters (1)

- `filter/watercolor:wcSimplify` — `{}`

### Builtin mod (23)

- `classicNoisedeck/caustic:caustic` — `{"NOISE_TYPE":10}`
- `classicNoisedeck/coalesce:coalesce` — `{}`
- `classicNoisedeck/composite:composite` — `{}`
- `classicNoisedeck/lensDistortion:lensDistortion` — `{}`
- `filter/bulge:bulge` — `{}`
- `filter/hs:hs` — `{}`
- `filter/lensWarp:lensWarp` — `{}`
- `filter/pinch:pinch` — `{}`
- `filter/pondRipples:pondRipples` — `{"STYLE":2,"WRAP":0}`
- `filter/prismaticAberration:prismaticAberration` — `{}`
- `filter/repeat:repeat` — `{}`
- `filter/reverb:reverb` — `{}`
- `filter/scale:scale` — `{}`
- `filter/scroll:scroll` — `{}`
- `filter/spiral:spiral` — `{}`
- `filter/translate:translate` — `{}`
- `filter/warp:warp` — `{}`
- `mixer/patternMix:patternMix` — `{}`
- `mixer/shapeMask:shapeMask` — `{}`
- `mixer/split:split` — `{}`
- `mixer/uvRemap:uvRemap` — `{}`
- `synth/modPattern:modPattern` — `{}`
- `synth/pattern:pattern` — `{}`

### Other builtins/operators (3)

- `filter/lighting:lighting` — `{}`
- `filter/oilPaint:oilFlatten` — `{"MODE":1}`
- `filter/waves:waves` — `{}`

### No new feature required (already accepted by current validator/emitter) (2)

- `filter/invert:inv` — `{}`
- `synth/solid:solid` — `{}`

## Boundary conclusion

The 15-program `mod` slice is deliberately bounded to the exact renderer-ready set. The remaining categories should be planned as separate feature-frontier tasks; broadening Task 12 to capture adjacent `mod` users would immediately couple it to derivatives, dynamic indexing, bit reinterpretation, or loop semantics.
