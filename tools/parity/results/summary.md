# noisemaker-for-cpp DSL parameter/geometry sweep

Generated: 2026-09-16T23:21:25Z
Effects swept: 208 / variants+chains: 4685
Global seed: 20260916  Variants/effect: 20

Comparison covers both RGBA8 (quantized) and float32 (pre-quantization surface) bytes, via an additive `--float32-output` flag added to both drivers for this sweep. A case is `byte_exact` only if both matched; a float32-only divergence (RGBA8 matched, the floats behind it did not) is called out distinctly in its diagnostics.

## Totals (single-effect variants, all effects)

- byte_exact: 2393
- divergent: 74
- both_refused: 0
- cpp_refused_only: 2140
- timeout: 78

## Effects fully byte-exact across all their variants: 91 / 208

classicNoisedeck/bitEffects, classicNoisedeck/coalesce, classicNoisedeck/refract, filter/adjust, filter/bc, filter/blur, filter/bulge, filter/channel, filter/chroma, filter/chromaticAberration, filter/chrome, filter/colorspace, filter/corrupt, filter/crt, filter/degauss, filter/deriv, filter/directionalBlur, filter/edge, filter/flipMirror, filter/fxaa, filter/glowingEdge, filter/glyphMap, filter/grade, filter/grain, filter/grime, filter/highPass, filter/historicPalette, filter/invert, filter/lens, filter/lensWarp, filter/normalMap, filter/normalize, filter/octaveWarp, filter/osd, filter/outline, filter/palette, filter/parallax, filter/patchwork, filter/pinch, filter/pixelSort, filter/pixels, filter/plasticWrap, filter/polar, filter/posterize, filter/prismaticAberration, filter/reindex, filter/repeat, filter/reverb, filter/ridge, filter/rotate, filter/scale, filter/scroll, filter/seamless, filter/sharpen, filter/simpleAberration, filter/sine, filter/skew, filter/smooth, filter/smoothstep, filter/sobel, filter/spinBlur, filter/spiral, filter/spookyTicker, filter/step, filter/tetraCosine, filter/threshold, filter/tile, filter/translate, filter/tunnel, filter/unsharpMask, filter/vaseline, filter/vignette, filter/warp, filter/watercolor, filter/waves, filter/wobble, filter/zoomBlur, mixer/alphaMask, mixer/applyMode, mixer/blendMode, mixer/cellSplit, mixer/centerMask, mixer/channelCombine, mixer/distortion, mixer/focusBlur, mixer/mashup, mixer/thresholdMix, mixer/uvRemap, synth/bitwise, synth/newton, synth/subdivide

## Effects with any divergence: 20

### classicNoisedeck/caustic
- case `classicNoisedeck__caustic__v7` (97x61, time=0.25, seed=829598423)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=3 firstMismatch={'x': 53, 'y': 19, 'channel': 'B', 'expected': -0.004791259765625, 'actual': -0.004795074462890625} expectedSha256=2b52b20ceb78855f2de130361add019a0a8507fbc1b1ecf2492735441af4f942 actualSha256=35fc1c41ec8c1b9ecafaaa9909febf42be79dc3a2db6a1b106a0045ae179f9a1

### classicNoisedeck/glitch
- case `classicNoisedeck__glitch__v2` (97x61, time=0.999, seed=1939239976)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=1 firstMismatch={'x': 90, 'y': 1, 'channel': 'B', 'expected': -0.00010281801223754883, 'actual': -0.00010275840759277344} expectedSha256=03e99bc3365cde88bb4fcf3fa503a488f052e23d25f23c83521dc9271fd74f72 actualSha256=6283c93c8f0a89eb2eda379bd06414dcffdf790ead6f526d7efd2d5e1e21f6fb
  - (4 divergent variants total for this effect)

### filter/clouds
- case `filter__clouds__v4` (128x37, time=0.25, seed=2819820395)
  - dimensions=128x37 expectedLength=18944 actualLength=18944 firstMismatch=offset=4962 x=88 y=9 channel=B expected=178 actual=177 mismatchCount=2 maxDelta=1 expectedSha256=90bd1d54286fb2ad96ced7e33962a1880c6a6c3c8a9e41078d846661881743b4 actualSha256=497824c41fb00aec9894688624ef334b1ee1acb4dab8fc5eb0c7b265e96c5403
  - (4 divergent variants total for this effect)

### filter/craquelure
- case `filter__craquelure__v7` (97x61, time=0.25, seed=178107296)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=2 firstMismatch={'x': 86, 'y': 7, 'channel': 'R', 'expected': 0.11590576171875, 'actual': 0.115966796875} expectedSha256=ecca37eac17067830eb011d0db86a088331fb7bd0078f8f79cf55e5237009d57 actualSha256=c18410b043ec1113ccc863090a84a7cf4aae730c85feb505b6841f258d675a7c
  - (3 divergent variants total for this effect)

### filter/dither
- case `filter__dither__v2` (97x61, time=0.999, seed=4082020649)
  - authority refused this program but the executor rendered bytes
  - (15 divergent variants total for this effect)

### filter/hs
- case `filter__hs__v14` (128x37, time=0.999, seed=1710013041)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=4736 firstMismatch={'x': 0, 'y': 0, 'channel': 'G', 'expected': 0.66650390625, 'actual': 0.666015625} expectedSha256=33f0d7fdf9c8baa3e51284cdf487727687051a1b1e8fc1455579eb67fc3ddb11 actualSha256=0f9a5b6a240ec83ce801f9c3b218b50b40ef7460976594309887316aff061018

### filter/scanlineError
- case `filter__scanlineError__v2` (97x61, time=0.999, seed=2606078826)
  - dimensions=97x61 expectedLength=23668 actualLength=23668 firstMismatch=offset=900 x=31 y=2 channel=R expected=96 actual=95 mismatchCount=92 maxDelta=3 expectedSha256=da5730ba286526d3e9696f6416c7708870ffaee3d3e8692f66905f78b06b5df2 actualSha256=12e383d0c6ca8bc0ccfbea8c9629f608a70ae56a04ac6466fbc61ea4f06d7259
  - (7 divergent variants total for this effect)

### filter/texture
- case `filter__texture__v3` (64x64, time=0.0, seed=3507750515)
  - dimensions=64x64 expectedLength=16384 actualLength=16384 firstMismatch=offset=6372 x=57 y=24 channel=R expected=62 actual=63 mismatchCount=1 maxDelta=1 expectedSha256=d7972332cfd87abf8d8c320ca7ad51a2ea67dd4a9f49639b6e5d850ab0de47e9 actualSha256=fa579ca7890114d09e1a49b555c3bb884552a94e4f0d33cd0a10c2c73ee7c656
  - (2 divergent variants total for this effect)

### mixer/patternMix
- case `mixer__patternMix__v2` (97x61, time=0.999, seed=1269094195)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=161 firstMismatch={'x': 14, 'y': 0, 'channel': 'R', 'expected': 0.00962066650390625, 'actual': 0.009613037109375} expectedSha256=8ee16c7bceb8a3eef3eb50cd47a019938b31a73b27e5ed15a4511b30437d65a0 actualSha256=52c650f2b6c3f56a86dd54bc011d10dbfb6f575fe4c60615f60d33926fc7f334
  - (7 divergent variants total for this effect)

### mixer/shapeMask
- case `mixer__shapeMask__v2` (97x61, time=0.999, seed=1901062360)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=2 firstMismatch={'x': 42, 'y': 35, 'channel': 'R', 'expected': 0.0012331008911132812, 'actual': 0.0012340545654296875} expectedSha256=abb92e86ab639fa80d14e91f7924242c898170f8deba3cd42196fafb0691b6ba actualSha256=4f20d38eb92c3f5c57f9e8c41ebb1b2f9a021cde50c8380eaff18e6a6a41674f
  - (2 divergent variants total for this effect)

### mixer/split
- case `mixer__split__v18` (64x64, time=0.0, seed=611777717)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=8 firstMismatch={'x': 34, 'y': 1, 'channel': 'R', 'expected': 0.00402069091796875, 'actual': 0.004016876220703125} expectedSha256=ad49684fd0012b2c12106da0094b9203731b8e798ba94fac677268efeee75289 actualSha256=9c57966e0a8d1f4d7bae7682de69b6f4b3c6b05be8ba2438296087c4e2fe2b20

### synth/cell
- case `synth__cell__v2` (97x61, time=0.999, seed=1288041878)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=21 firstMismatch={'x': 93, 'y': 15, 'channel': 'R', 'expected': 0.0036029815673828125, 'actual': 0.00360107421875} expectedSha256=494e9b4b792b3fd107803266449048a3d718261dc93f31aae505370ab3340a25 actualSha256=7965cd20527b2bf4e48f0d6c7ffe3b5561d3581776ce8c1c5b127a53a9c9b75a
  - (5 divergent variants total for this effect)

### synth/curl
- case `synth__curl__v18` (64x64, time=0.0, seed=3559289789)
  - dimensions=64x64 expectedLength=16384 actualLength=16384 firstMismatch=offset=7668 x=61 y=29 channel=R expected=222 actual=221 mismatchCount=3 maxDelta=1 expectedSha256=c06ed0957c7c48450484eb99190c1493652b3d0c9d946830fe55ee550b73e5c5 actualSha256=343356603d4eb80f998c3ea5df070a83889b9ef465fbcf8afa5e6d2323289c4f

### synth/gabor
- case `synth__gabor__v2` (97x61, time=0.999, seed=1274574473)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=9 firstMismatch={'x': 71, 'y': 24, 'channel': 'R', 'expected': 0.056640625, 'actual': 0.056671142578125} expectedSha256=c9dc1729482f5d02eb651b6d35a31e3903834b409f53acb4a3d324cce559b114 actualSha256=61e8f02a9a4fec9ba81546c4237d342c23603ea5048175ed4b4d7cbd8a6490f6
  - (4 divergent variants total for this effect)

### synth/julia
- case `synth__julia__v7` (97x61, time=0.25, seed=1405231272)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=15 firstMismatch={'x': 86, 'y': 4, 'channel': 'R', 'expected': 0.395751953125, 'actual': 0.3955078125} expectedSha256=fc5b3f15a4ad4d3ece86b1b424b4560728d88bb61502d3533ab57b079f2c11af actualSha256=51967e22940e9e7f3e7edb15bfb88982c624dcef81a555dc44f092d635b10a40

### synth/mandelbrot
- case `synth__mandelbrot__v14` (128x37, time=0.999, seed=2226964193)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=9 firstMismatch={'x': 41, 'y': 12, 'channel': 'R', 'expected': 0.484130859375, 'actual': 0.48388671875} expectedSha256=b500487707bb7729f9ae79b9a0172509df68d2bc6f33d778be99dee6cede0d00 actualSha256=f89063fb7a1b7d19a1c524852d98077fa395afa06cc526d018ac017484b5a216
  - (2 divergent variants total for this effect)

### synth/modPattern
- case `synth__modPattern__v2` (97x61, time=0.999, seed=1724439628)
  - dimensions=97x61 expectedLength=23668 actualLength=23668 firstMismatch=offset=836 x=15 y=2 channel=R expected=212 actual=213 mismatchCount=78 maxDelta=2 expectedSha256=820ae2ad116635e3ea07c7252de85298fcc1901be3606b0597289cba35152048 actualSha256=e4992243a7dae26436f110cdd1e05f986219be8efbd4478486be021d5da17a39
  - (6 divergent variants total for this effect)

### synth/noise
- case `synth__noise__v3` (64x64, time=0.0, seed=1582816974)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=4 firstMismatch={'x': 17, 'y': 34, 'channel': 'G', 'expected': 0.52490234375, 'actual': 0.525390625} expectedSha256=4fbeee871d0945877ac9e9630b7863fc6964e3de442d9d4a833fe912bddb9ec2 actualSha256=e7315bcc9dc43f2a871764be957700e319691a7d431e9dc001d30ddb32945731

### synth/osc2d
- case `synth__osc2d__v3` (64x64, time=0.0, seed=2956715230)
  - rgba8 byte-exact; float32 surface diverges: mismatchCount=3 firstMismatch={'x': 18, 'y': 27, 'channel': 'R', 'expected': 0.001125335693359375, 'actual': 0.0011243820190429688} expectedSha256=6205df360ff16db1c9d3cb2508ffa89308eb9bac8539a1753877afbd4a7d0c4c actualSha256=3745c3024083b64818b2a024647ceed8dd19a7597e473fd8dc3438683fc3f694
  - (3 divergent variants total for this effect)

### synth/perlin
- case `synth__perlin__v7` (97x61, time=0.25, seed=3381827459)
  - dimensions=97x61 expectedLength=23668 actualLength=23668 firstMismatch=offset=15162 x=7 y=39 channel=B expected=87 actual=88 mismatchCount=1 maxDelta=1 expectedSha256=b14b767713a861e61c5dd2589785c4f78e4da14a79dbd16e8b6636ae4cd2e747 actualSha256=638cb0417c3ef35470976ca2b7838615dea7867fb0f75370ce8a29eb72f103fa
  - (2 divergent variants total for this effect)

## Effects refused by C++ only (JS authority rendered): 100

- classicNoisedeck/caustic: 'parameter interp requests compile define NOISE_TYPE=0 but the generated route bakes NOISE_TYPE=10'
- classicNoisedeck/cellNoise: 'parameter palette selects palette entry 32 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/cellRefract: 'parameter shape requests compile define SHAPE=0 but the generated route bakes SHAPE=1'
- classicNoisedeck/colorLab: 'parameter palette selects palette entry 46 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/composite: 'inputColor: vector has the wrong width'
- classicNoisedeck/effects: 'parameter effect requests compile define EFFECT=220 but the generated route bakes EFFECT=0'
- classicNoisedeck/fractal: 'parameter palette selects palette entry 12 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/kaleido: 'parameter direction requests compile define DIRECTION=1 but the generated route bakes DIRECTION=2'
- classicNoisedeck/lensDistortion: 'tint: vector has the wrong width'
- classicNoisedeck/moodscape: 'parameter interp requests compile define NOISE_TYPE=0 but the generated route bakes NOISE_TYPE=10'
- classicNoisedeck/noise: 'parameter palette selects palette entry 2 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/noise3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/classicNoisedeck__noise3d__default/case.dsl:2:1: Effect pass "classicNoisedeck/noise3d:noise3d" unavailable: missing_backend_program (classicNoisedeck/noise3d:noise3d)'
- classicNoisedeck/shapeMixer: 'parameter palette selects palette entry 41 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/shapes: 'parameter palette selects palette entry 46 and the authority overrides the palette uniforms from its built-in table, which this port has not ported'
- classicNoisedeck/shapes3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/classicNoisedeck__shapes3d__default/case.dsl:2:20: Effect pass "classicNoisedeck/shapes3d:shapes3d" unavailable: missing_backend_program (classicNoisedeck/shapes3d:shapes3d)'
- classicNoisedeck/splat: 'splatColor: vector has the wrong width'
- filter/bloom: 'tint: vector has the wrong width'
- filter/celShading: 'edgeColor: vector has the wrong width'
- filter/colorReplace: 'targetColor: vector has the wrong width'
- filter/convolutionFeedback: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter__convolutionFeedback__default/case.dsl:2:20: Effect pass "filter/convolutionFeedback:cfSharpen" unavailable: missing_backend_program (filter/convolutionFeedback:cfSharpen)'
- filter/emboss: 'parameter style requests compile define STYLE=1 but the generated route bakes STYLE=0'
- filter/extrude: 'parameter type requests compile define EXTRUDE_TYPE=1 but the generated route bakes EXTRUDE_TYPE=0'
- filter/feedback: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter__feedback__default/case.dsl:2:20: Effect pass "filter/feedback:feedback" unavailable: missing_backend_program (filter/feedback:feedback)'
- filter/fibers: 'declared texture requires the canonical CPU worm-overlay adapter'
- filter/halftone: 'inkColor: vector has the wrong width'
- filter/hatch: 'inkColor: vector has the wrong width'
- filter/lensFlare: 'tint: vector has the wrong width'
- filter/lightLeak: 'color: vector has the wrong width'
- filter/lighting: 'diffuseColor: vector has the wrong width'
- filter/lowPoly: 'edgeColor: vector has the wrong width'
- filter/median: 'parameter radius requests compile define RADIUS=3 but the generated route bakes RADIUS=2'
- filter/morphology: 'parameter shape requests compile define SHAPE=1 but the generated route bakes SHAPE=0'
- filter/mosaicTiles: 'backgroundColor: vector has the wrong width'
- filter/motionBlur: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter__motionBlur__default/case.dsl:2:20: Effect pass "filter/motionBlur:motionBlur" unavailable: missing_backend_program (filter/motionBlur:motionBlur)'
- filter/oilPaint: 'parameter mode requests compile define MODE=0 but the generated route bakes MODE=1'
- filter/photocopy: 'inkColor: vector has the wrong width'
- filter/pondRipples: 'parameter style requests compile define STYLE=0 but the generated route bakes STYLE=2'
- filter/relief: 'inkColor: vector has the wrong width'
- filter/scatter: 'parameter mode requests compile define MODE=1 but the generated route bakes MODE=0'
- filter/scratches: 'declared texture requires the canonical CPU worm-overlay adapter'
- filter/snow: 'the authority executes a hand-written CPU adapter for this program and the emitted typed kernel is measured divergent (499 of 748 RGBA8 bytes at 17x11)'
- filter/spatter: 'color: vector has the wrong width'
- filter/stamp: 'inkColor: vector has the wrong width'
- filter/stipple: 'paperColor: vector has the wrong width'
- filter/strayHair: 'declared texture requires the canonical CPU worm-overlay adapter'
- filter/strokes: 'parameter mode requests compile define MODE=1 but the generated route bakes MODE=0'
- filter/temporalAberration: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter__temporalAberration__default/case.dsl:2:20: Effect pass "filter/temporalAberration:temporalAberration" unavailable: missing_backend_program (filter/temporalAberration:temporalAberration)'
- filter/tetraColorArray: 'color0: vector has the wrong width'
- filter/text: 'input resource is not produced'
- filter/texture: 'parameter mode requests compile define MODE=0 but the generated route bakes MODE=3'
- filter/tint: 'color: vector has the wrong width'
- filter/wind: 'parameter method requests compile define METHOD=0 but the generated route bakes METHOD=1'
- filter/wormhole: 'scatter is not enabled in Task 6'
- filter3d/flow3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter3d__flow3d__v0/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- filter3d/palette3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/filter3d__palette3d__v7/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- mixer/shadow: 'color: vector has the wrong width'
- points/attractor: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__attractor__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/buddhabrot: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__buddhabrot__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/dla: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__dla__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/flock: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__flock__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/flow: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__flow__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/heightGrid: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__heightGrid__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/hydraulic: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__hydraulic__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/lenia: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__lenia__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/life: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__life__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/physarum: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__physarum__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- points/physical: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/points__physical__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- render/loopBegin: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__loopBegin__default/case.dsl:2:9: Effect pass "render/loopBegin:loopBegin" unavailable: missing_backend_program (render/loopBegin:loopBegin)'
- render/loopEnd: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__loopEnd__default/case.dsl:2:9: Effect pass "render/loopBegin:loopBegin" unavailable: missing_backend_program (render/loopBegin:loopBegin)'
- render/pointsBillboardRender: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__pointsBillboardRender__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- render/pointsEmit: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__pointsEmit__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- render/pointsRender: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__pointsRender__default/case.dsl:2:9: Effect pass "render/pointsEmit:init" unavailable: missing_backend_program (render/pointsEmit:init)'
- render/render3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__render3d__default/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- render/renderCubemap3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__renderCubemap3d__default/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- render/renderCubemapSurface: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__renderCubemapSurface__default/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- render/renderLandscape3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/render__renderLandscape3d__default/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- synth/cellularAutomata: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth__cellularAutomata__default/case.dsl:2:1: Effect pass "synth/cellularAutomata:caFb" unavailable: missing_backend_program (synth/cellularAutomata:caFb)'
- synth/curl: 'parameter outputMode requests compile define OUTPUT_MODE=0 but the generated route bakes OUTPUT_MODE=3'
- synth/gradient: 'color1: vector has the wrong width'
- synth/mandala: 'fgColor: vector has the wrong width'
- synth/media: 'input resource is not produced'
- synth/mnca: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth__mnca__default/case.dsl:2:1: Effect pass "synth/mnca:mncaFb" unavailable: missing_backend_program (synth/mnca:mncaFb)'
- synth/navierStokes: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth__navierStokes__default/case.dsl:2:1: Effect pass "synth/navierStokes:nsSplat" unavailable: missing_backend_program (synth/navierStokes:nsSplat)'
- synth/pattern: 'fgColor: vector has the wrong width'
- synth/perlin: 'parameter dimensions requests compile define DIMENSIONS=3 but the generated route bakes DIMENSIONS=2'
- synth/polygon: 'fgColor: vector has the wrong width'
- synth/reactionDiffusion: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth__reactionDiffusion__default/case.dsl:2:1: Effect pass "synth/reactionDiffusion:rdFb" unavailable: missing_backend_program (synth/reactionDiffusion:rdFb)'
- synth/remap: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth__remap__default/case.dsl:2:1: Effect pass "synth/remap:remap" unavailable: source_incompatible (pinned source is not raw- or dual-semantic-equivalent)'
- synth/sacredGeometry: 'fgColor: vector has the wrong width'
- synth/shape: 'parameter loopAOffset requests compile define LOOP_A_OFFSET=10 but the generated route bakes LOOP_A_OFFSET=40'
- synth/solid: 'color: vector has the wrong width'
- synth/testPattern: 'the emitted typed kernel is measured divergent from the authority at grid boundaries (2 pixels, 6 of 748 RGBA8 bytes at 17x11)'
- synth3d/cell3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__cell3d__v0/case.dsl:2:1: Effect pass "synth3d/cell3d:precompute" unavailable: missing_backend_program (synth3d/cell3d:precompute)'
- synth3d/cellularAutomata3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__cellularAutomata3d__default/case.dsl:2:1: Effect pass "synth3d/cellularAutomata3d:simulate" unavailable: missing_backend_program (synth3d/cellularAutomata3d:simulate)'
- synth3d/flythrough3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__flythrough3d__default/case.dsl:2:1: Effect pass "synth3d/flythrough3d:precompute" unavailable: missing_backend_program (synth3d/flythrough3d:precompute)'
- synth3d/fractal3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__fractal3d__default/case.dsl:2:1: Effect pass "synth3d/fractal3d:precompute" unavailable: missing_backend_program (synth3d/fractal3d:precompute)'
- synth3d/heightmap3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__heightmap3d__default/case.dsl:2:1: Effect pass "synth3d/heightmap3d:precompute" unavailable: missing_backend_program (synth3d/heightmap3d:precompute)'
- synth3d/noise3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__noise3d__v0/case.dsl:2:1: Effect pass "synth3d/noise3d:precompute" unavailable: missing_backend_program (synth3d/noise3d:precompute)'
- synth3d/reactionDiffusion3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__reactionDiffusion3d__v0/case.dsl:2:1: Effect pass "synth3d/reactionDiffusion3d:simulate" unavailable: missing_backend_program (synth3d/reactionDiffusion3d:simulate)'
- synth3d/shape3d: '/Users/alex/platform/.nm-cpp-work/lanes/sweep/tools/parity/run/scratch/synth3d__shape3d__default/case.dsl:2:1: Effect pass "synth3d/shape3d:precompute" unavailable: missing_backend_program (synth3d/shape3d:precompute)'

## Effects refused by BOTH lanes on every observed variant: 0


## Timeouts: 10 effects had at least one variant exceed the per-case limit

filter3d/flow3d, filter3d/palette3d, points/lenia, render/pointsBillboardRender, render/renderLandscape3d, render/renderLit3d, synth3d/cell3d, synth3d/flythrough3d, synth3d/noise3d, synth3d/reactionDiffusion3d

## Chained (generator -> filter -> mixer) programs: 525 run

- byte_exact: 208
- divergent: 2
- both_refused: 0
- cpp_refused_only: 315
- timeout: 0

Divergent chains (all participating effect ids shown; not attributed to a single effect):
- filter__clouds__chain1: ['synth/curl', 'filter/clouds', 'mixer/thresholdMix']
- filter__clouds__chain2: ['synth/polygon', 'filter/clouds', 'mixer/shadow']

