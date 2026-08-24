import { createDefaultRegistry, effectCatalog, kernels } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { CpuRenderer } from '../noisemaker-for-cpu/src/runtime/renderer.js'

const keys = `filter/chrome:chBlurH
filter/chrome:chBlurV
filter/highPass:hpBlurH
filter/highPass:hpBlurV
filter/morphology:morphA
filter/morphology:morphB
filter/photocopy:pcBlurH
filter/photocopy:pcBlurV
filter/plasticWrap:pwBlurH
filter/plasticWrap:pwBlurV
filter/relief:rlBlurH
filter/relief:rlBlurV
filter/stamp:stBlurH
filter/stamp:stBlurV
filter/unsharpMask:usmBlurH
filter/unsharpMask:usmBlurV
filter/craquelure:craquelure
filter/lowPoly:lowPoly
filter/patchwork:patchwork
filter/scatter:scatterSmooth
filter/strokes:stkPost
filter/clouds:clouds
filter/hatch:hatch
filter/oilPaint:oilPost
synth/gradient:gradient
synth/mandala:mandala
synth/subdivide:subdivide
filter/normalize:reduce
filter/normalize:reduceMinmax
filter/wormhole:blend
mixer/shadow:shadow
synth/cell:cell
mixer/mashup:mashup
mixer/cellSplit:cellSplit
filter/pixelSort:findBrightest
filter/reverb:reverb`.trim().split('\n')

const renderer = new CpuRenderer({ registry: createDefaultRegistry(), kernels })
const result = []
for (const key of keys) {
  const [effectId, program] = key.split(':')
  const definition = effectCatalog.find((effect) => effect.id === effectId)
  const pass = definition.passes.find((candidate) => candidate.program === program)
  const params = definition.normalizeArguments([])
  const base = renderer.buildBindings(definition, params, [], null, new Map(), {
    width: 9, height: 7, time: 0.375, frame: 7, seed: 19, externalTextures: {},
  })
  const uniforms = renderer.passUniforms(pass, params, base.uniforms)
  result.push({ key, uniforms })
}
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
