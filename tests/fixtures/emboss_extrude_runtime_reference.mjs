import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const cppRoot = process.cwd()
const cpuRoot = process.env.NOISEMAKER_CPU_ROOT
if (!cpuRoot) throw new Error('NOISEMAKER_CPU_ROOT is required')
const ledger = process.env.NOISEMAKER_CPU_LEDGER ?? `${cpuRoot}.ledger.sha256`
const output = process.env.NOISEMAKER_ORACLE_OUTPUT
const revision = '6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength)
const words = value => Array.from(new Uint32Array(value.buffer, value.byteOffset, value.byteLength / 4),
  word => `0x${(word >>> 0).toString(16).padStart(8, '0')}`)
const f32 = Math.fround

const { authenticateCpuRoot } = await import(pathToFileURL(path.join(cppRoot, 'tools/dsl/corpus_authority.mjs')).href)
authenticateCpuRoot(cpuRoot, ledger)
const loadCpu = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{canonicalKernelFactories, canonicalAdapterFactories, kernelFactories},
  {bindCanonicalKernel}, {runPass}, {Surface}, {UPSTREAM_REVISION}] = await Promise.all([
  loadCpu('src/effects/catalog.js'),
  loadCpu('src/csl/glsl-kernel.js'),
  loadCpu('src/runtime/pass-runner.js'),
  loadCpu('src/runtime/surface.js'),
  loadCpu('src/effects/generated/upstream-snapshot.js'),
])
if (process.version !== 'v26.0.0' || UPSTREAM_REVISION !== revision) {
  throw new Error('CPU runtime or source revision mismatch')
}
const metadata = JSON.parse(fs.readFileSync(path.join(cppRoot, 'tools/glslcpp/corpus', revision, 'metadata.json')))
const identities = [
  { effect: 'filter/emboss', key: 'filter/emboss:emboss', name: 'canonicalFactory48',
    source: 'filter/emboss/emboss.glsl', source_sha256: '872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191',
    defines: { STYLE: [0, 1] } },
  { effect: 'filter/extrude', key: 'filter/extrude:extrude', name: 'canonicalFactory49',
    source: 'filter/extrude/extrude.glsl', source_sha256: '3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29',
    defines: { DEPTH_SOURCE: [0, 1], EXTRUDE_TYPE: [0, 1] } },
]
for (const item of identities) {
  const factory = canonicalKernelFactories[item.key]
  const source = path.join(cppRoot, 'tools/glslcpp/corpus', revision, 'sources', item.source)
  if (typeof factory !== 'function' || factory.name !== item.name ||
      kernelFactories.get(item.key) !== factory || canonicalAdapterFactories[item.key] !== undefined ||
      sha256(fs.readFileSync(source)) !== item.source_sha256) {
    throw new Error(`${item.key}: canonical or source identity mismatch`)
  }
  const effect = metadata.effects[item.effect]
  if (!effect || effect.passes?.length !== 1 || effect.passes[0]?.key !== item.key) {
    throw new Error(`${item.key}: metadata pass mismatch`)
  }
  const actual = Object.fromEntries(Object.entries(effect.params)
    .filter(([, parameter]) => parameter.define)
    .map(([, parameter]) => [parameter.define,
      [...new Set(Object.values(parameter.choices ?? {}))].sort((a, b) => a - b)]))
  if (JSON.stringify(actual) !== JSON.stringify(item.defines)) {
    throw new Error(`${item.key}: declared define domain mismatch`)
  }
  item.factory = factory
  item.factory_sha256 = sha256(factory.toString())
}

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const i = (y * width + x) * 4
    data[i] = f32((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
    data[i + 1] = f32((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
    data[i + 2] = f32((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
    data[i + 3] = f32((((7 * x + 11 * y + phase) % 29) + 5) / 37)
  }
  return new Surface(width, height, data)
}

const geometries = {
  emboss: [
    {name: 'wide', width: 9, height: 6, phase: 3, tileOffset: [0, 0], fullResolution: [9, 6],
      amount: 1.4, angle: 135, heightUniform: 2, colorAmount: 70, renderScale: 1},
    {name: 'tiled', width: 13, height: 9, phase: 4, tileOffset: [3, 2], fullResolution: [20, 15],
      amount: 4.5, angle: -215, heightUniform: 7, colorAmount: 35, renderScale: 0.75},
  ],
  extrude: [
    {name: 'wide', width: 13, height: 9, phase: 1, tileOffset: [0, 0], fullResolution: [13, 9],
      size: 4, depth: 60, solidFront: true},
    {name: 'tiled', width: 9, height: 6, phase: 4, tileOffset: [3, 2], fullResolution: [17, 13],
      size: 5, depth: 85, solidFront: false},
  ],
}
const cases = []
for (const item of identities) {
  const label = item.effect.split('/')[1]
  const options = label === 'emboss'
    ? [{STYLE: 0}, {STYLE: 1}]
    : [{DEPTH_SOURCE: 0, EXTRUDE_TYPE: 0}, {DEPTH_SOURCE: 0, EXTRUDE_TYPE: 1},
       {DEPTH_SOURCE: 1, EXTRUDE_TYPE: 0}, {DEPTH_SOURCE: 1, EXTRUDE_TYPE: 1}]
  for (const geometry of geometries[label]) for (const defines of options) {
    const uniforms = label === 'emboss'
      ? {STYLE: defines.STYLE, amount: f32(geometry.amount), angle: f32(geometry.angle),
         height: f32(geometry.heightUniform), colorAmount: f32(geometry.colorAmount),
         renderScale: f32(geometry.renderScale)}
      : {DEPTH_SOURCE: defines.DEPTH_SOURCE, EXTRUDE_TYPE: defines.EXTRUDE_TYPE,
         size: f32(geometry.size), depth: f32(geometry.depth), solidFront: geometry.solidFront}
    function render() {
      const input = patternedSurface(geometry.width, geometry.height, geometry.phase)
      const before = bytes(input.data).subarray().toString('hex')
      const tileOffset = new Float32Array(geometry.tileOffset)
      const fullResolution = new Float32Array(geometry.fullResolution)
      const options = {width: geometry.width, height: geometry.height,
        uniforms, textures: {inputTex: input}, tileOffset, fullResolution}
      const beforeBindings = JSON.stringify({uniforms, tileOffset: [...tileOffset], fullResolution: [...fullResolution]})
      const output = new Surface(geometry.width, geometry.height)
      runPass({kernel: bindCanonicalKernel(item.factory, options), destination: output})
      if (bytes(input.data).toString('hex') !== before ||
          JSON.stringify({uniforms, tileOffset: [...tileOffset], fullResolution: [...fullResolution]}) !== beforeBindings) {
        throw new Error(`${item.key}: input or binding mutation`)
      }
      const rgba8 = output.toRgba8()
      if (output.data.length !== geometry.width * geometry.height * 4 || rgba8.length !== output.data.length) {
        throw new Error(`${item.key}: output extent mismatch`)
      }
      return {input_sha256: sha256(bytes(input.data)), f32_sha256: sha256(bytes(output.data)),
        rgba8_sha256: sha256(bytes(rgba8)), f32_words_le: words(output.data), rgba8_bytes: [...rgba8]}
    }
    const first = render(), second = render()
    if (JSON.stringify(first) !== JSON.stringify(second)) throw new Error(`${item.key}: repeat mismatch`)
    cases.push({program_key: item.key, geometry: geometry.name, width: geometry.width,
      height: geometry.height, phase: geometry.phase, tileOffset: geometry.tileOffset,
      fullResolution: geometry.fullResolution, defines, uniforms,
      expected: first, repeat_exact: true, input_immutable: true})
  }
}
const result = {schema: 'noisemaker-for-cpp.emboss-extrude.runtime-cpu-oracle.v1',
  cpu_revision: '9f3bd6a', upstream_revision: UPSTREAM_REVISION,
  node_version: process.version, authority_ledger_sha256: sha256(fs.readFileSync(ledger)),
  exactness: 'all raw Float32 words and RGBA8 bytes; no tolerance',
  factories: identities.map(({effect, key, name, source_sha256, factory_sha256, defines}) =>
    ({effect, key, name, source_sha256, factory_sha256, defines})), cases}
if (output) fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n')
else process.stdout.write(JSON.stringify(result, null, 2) + '\n')
