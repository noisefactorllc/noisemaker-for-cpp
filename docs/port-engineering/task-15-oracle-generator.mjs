import crypto from 'node:crypto'
import fs from 'node:fs'
import { canonicalKernelFactories, createDefaultRegistry, effectCatalog, kernelFactories, kernels } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { CpuRenderer } from '../noisemaker-for-cpu/src/runtime/renderer.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const outputPath = 'docs/port-engineering/task-15-oracles.json'
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

const defines = Object.fromEntries(keys.map((key) => [key, {}]))
for (const key of ['filter/morphology:morphA', 'filter/morphology:morphB']) defines[key] = { SHAPE: 0 }
for (const key of ['filter/relief:rlBlurH', 'filter/relief:rlBlurV', 'filter/scatter:scatterSmooth', 'filter/strokes:stkPost', 'filter/hatch:hatch']) defines[key] = { MODE: 0 }
defines['filter/lowPoly:lowPoly'] = { LP_BORDER: 0, LP_LIGHT: 0 }
defines['filter/oilPaint:oilPost'] = { MODE: 1 }

const coverage = new Map([
  ['filter/normalize:reduce', ['continue', 'rect_16x16', 'sampler_route']],
  ['filter/normalize:reduceMinmax', ['continue', 'rect_16x16', 'sampler_route']],
  ['mixer/cellSplit:cellSplit', ['continue', 'two_sampler_routes']],
  ['filter/craquelure:craquelure', ['nested_depth2']],
  ['filter/lowPoly:lowPoly', ['nested_depth2']],
  ['filter/patchwork:patchwork', ['nested_depth2']],
  ['filter/scatter:scatterSmooth', ['nested_depth2']],
  ['filter/strokes:stkPost', ['nested_depth2']],
  ['filter/oilPaint:oilPost', ['nested_depth2']],
  ['filter/reverb:reverb', ['local_clamp_bound', 'sampler_route']],
  ['mixer/mashup:mashup', ['break', 'all_sampler_routes']],
  ['filter/clouds:clouds', ['break']],
  ['synth/mandala:mandala', ['break']],
  ['synth/subdivide:subdivide', ['break']],
])

const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex')
const renderer = new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories })

// This loop is the normative sampler fixture.  Surface storage is top-down:
// lane offset (y * 11 + x) * 4; assignment to Float32Array is the intentional
// F64-to-F32 boundary before canonical sampling.  `tag` is the 1-based ordinal
// in Object.keys(pass.inputs ?? {}) insertion order for this pass.
function inputSurface(tag) {
  const surface = new Surface(11, 9)
  for (let y = 0; y < 9; y += 1) for (let x = 0; x < 11; x += 1) {
    const lane = (y * 11 + x) * 4
    surface.data[lane] = ((x * 17 + y * 31 + tag * 13) % 101) / 100
    surface.data[lane + 1] = ((x * 7 + y * 19 + tag * 23) % 97) / 96
    surface.data[lane + 2] = ((x * 29 + y * 11 + tag * 5) % 89) / 88
    surface.data[lane + 3] = 0.35 + ((x * 3 + y * 5 + tag) % 13) / 20
  }
  return surface
}

function vector(key, name, overrides = {}) {
  const [effectId, program] = key.split(':')
  const definition = effectCatalog.find((effect) => effect.id === effectId)
  const pass = definition.passes.find((candidate) => candidate.program === program)
  const params = { ...definition.normalizeArguments([]), ...overrides }
  const base = renderer.buildBindings(definition, params, [], null, new Map(), {
    width: 9, height: 7, time: 0.375, frame: 7, seed: 19, externalTextures: {},
  })
  const uniforms = renderer.passUniforms(pass, params, base.uniforms)
  const textures = {}
  let tag = 0
  for (const sampler of Object.keys(pass.inputs ?? {})) textures[sampler] = inputSurface(++tag)

  const render = () => {
    const kernel = bindCanonicalKernel(canonicalKernelFactories[key], {
      width: 9, height: 7, time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19,
      uniforms, textures, tileOffset: [2, 1], fullResolution: [13, 11],
    })
    const output = new Surface(9, 7)
    for (let y = 0; y < 7; y += 1) for (let x = 0; x < 9; x += 1) {
      const pixel = new Float32Array(4)
      kernel({
        fragCoord: new Float32Array([x + 0.5, y + 0.5]),
        uv: new Float32Array([(x + 0.5) / 9, (y + 0.5) / 7]),
        resolution: new Float32Array([9, 7]),
      }, pixel)
      output.data.set(pixel, (y * 9 + x) * 4)
    }
    return output
  }

  const first = render()
  const second = render()
  const f32 = Buffer.from(first.data.buffer, first.data.byteOffset, first.data.byteLength)
  const repeatF32 = Buffer.from(second.data.buffer, second.data.byteOffset, second.data.byteLength)
  const rgba8 = Buffer.from(first.toRgba8())
  const repeatRgba8 = Buffer.from(second.toRgba8())
  if (!f32.equals(repeatF32) || !rgba8.equals(repeatRgba8)) throw new Error(`${key}/${name}: non-deterministic double render`)

  return {
    k: key,
    n: name,
    o: overrides,
    s: Object.keys(textures),
    f: sha256(f32),
    r: sha256(rgba8),
    p: [[0, 0], [4, 3], [8, 6]].map(([x, y]) => Array.from(first.data.slice((y * 9 + x) * 4, (y * 9 + x + 1) * 4)).map((value) => Number(value.toPrecision(9)))),
    c: coverage.get(key) ?? ['counted_for'],
  }
}

const variants = keys.map((key) => vector(key, 'defaults'))
variants.push(vector('filter/reverb:reverb', 'iterations_1', { iterations: 1 }))
variants.push(vector('filter/reverb:reverb', 'iterations_8', { iterations: 8, ridges: true }))

const fixture = {
  w: 9,
  h: 7,
  time: 0.375,
  frame: 7,
  deltaTime: 1 / 60,
  seed: 19,
  tileOffset: [2, 1],
  fullResolution: [13, 11],
  samplers: 'each pass.inputs route is a distinct deterministic 11x9 F32 formula surface',
  contract: {
    sampler_order: 'Object.keys(pass.inputs ?? {}) insertion order; first route tag is 1',
    sampler_storage: 'top-down Float32Array; lane=(y*11+x)*4; every assignment is an F64-to-F32 boundary',
    sampler_extent: [11, 9],
    sampler_lanes: ['((x*17+y*31+tag*13)%101)/100', '((x*7+y*19+tag*23)%97)/96', '((x*29+y*11+tag*5)%89)/88', '0.35+((x*3+y*5+tag)%13)/20'],
    output_storage: 'top-down Surface(9,7); lane=(y*9+x)*4; kernel pixel is Float32Array(4)',
    fragment_inputs: 'fragCoord=Float32Array([x+0.5,y+0.5]); uv=Float32Array([(x+0.5)/9,(y+0.5)/7]); resolution=Float32Array([9,7])',
    checks: 'two renders must have identical F32 bytes and identical Surface.toRgba8 bytes before SHA-256 and probes are recorded',
  },
}

const oracle = {
  schema: 'noisemaker-for-cpp.counted-for-v1.oracle.v3',
  field_legend: {
    k: 'key', n: 'variant name', o: 'parameter overrides', s: 'pass.inputs sampler uniforms',
    f: 'sha256 of 9x7 F32 output bytes', r: 'sha256 of Surface.toRgba8 output bytes',
    p: 'F32 RGBA probes at [0,0],[4,3],[8,6]', c: 'coverage tags',
  },
  provenance: {
    cpu_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
    node: process.version,
    canonical_kernels_sha256: sha256(fs.readFileSync('../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js')),
    binding_module: 'src/csl/glsl-kernel.js:bindCanonicalKernel',
    execution: 'direct factory binding; every variant double-rendered and byte-compared',
    generator: 'docs/port-engineering/task-15-oracle-generator.mjs',
  },
  fixture,
  counts: { keys: 36, variants: variants.length, typed: 107, public: 109, remaining: 103 },
  defines,
  variants,
}

function invariant(previous) {
  if (!previous) return { prior: 'none', vectors: variants.length }
  const old = new Map(previous.variants.map((item) => [`${item.k}/${item.n}`, item]))
  if (old.size !== variants.length) throw new Error(`vector count drift: ${old.size} -> ${variants.length}`)
  for (const next of variants) {
    const prior = old.get(`${next.k}/${next.n}`)
    if (!prior || prior.f !== next.f || prior.r !== next.r || JSON.stringify(prior.p) !== JSON.stringify(next.p)) throw new Error(`oracle vector drift: ${next.k}/${next.n}`)
  }
  return { prior: 'verified', vectors: variants.length }
}

const previous = fs.existsSync(outputPath) ? JSON.parse(fs.readFileSync(outputPath, 'utf8')) : null
const result = invariant(previous)
const payload = `${JSON.stringify(oracle)}\n`
if (process.argv.includes('--write')) fs.writeFileSync(outputPath, payload)
if (process.argv.includes('--check') && previous && fs.readFileSync(outputPath, 'utf8') !== payload) throw new Error('oracle file is not the generator output; rerun with --write')
console.log(JSON.stringify({ ...result, output: outputPath, written: process.argv.includes('--write'), oracle_sha256: sha256(payload) }))
