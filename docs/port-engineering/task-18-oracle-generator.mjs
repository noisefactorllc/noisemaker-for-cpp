import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-18-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6')
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const dimensions = Object.freeze({ input: [7, 5], output: [9, 7], tileOffset: [3, 2], fullResolution: [12, 10] })
const inputDescription = 'top-down 7x5 Float32Array: R=0.035+(((17*x+31*y+13)%101)/100)*0.22; G=0.02+(((7*x+19*y+23)%97)/96)*0.26; B=0.01+(((29*x+11*y+5)%89)/88)*0.20; A=0.35+((3*x+5*y+1)%13)/20; every lane assignment crosses the Float32Array boundary'

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const values = new Float32Array([value]); return `0x${new DataView(values.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function printable(value) { return Number.isNaN(value) ? 'NaN' : value }
function uniformRecord(value) { return { value, f32_bits_le: f32Bits(value) } }

function makeInput() {
  const [width, height] = dimensions.input
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const lane = (y * width + x) * 4
      data[lane] = 0.035 + (((17 * x + 31 * y + 13) % 101) / 100) * 0.22
      data[lane + 1] = 0.02 + (((7 * x + 19 * y + 23) % 97) / 96) * 0.26
      data[lane + 2] = 0.01 + (((29 * x + 11 * y + 5) % 89) / 88) * 0.20
      data[lane + 3] = 0.35 + ((3 * x + 5 * y + 1) % 13) / 20
    }
  }
  return new Surface(width, height, data)
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at: [x, y], values: values.map(printable), f32_bits_le: values.map(f32Bits) }
}

function render(key, uniforms, textureName) {
  const factory = canonicalKernelFactories[key]
  if (typeof factory !== 'function') throw new Error(`missing canonical factory ${key}`)
  const [width, height] = dimensions.output
  const kernel = bindCanonicalKernel(factory, {
    width,
    height,
    time: 0.375,
    frame: 7,
    deltaTime: 1 / 60,
    seed: 19,
    tileOffset: new Float32Array(dimensions.tileOffset),
    fullResolution: new Float32Array(dimensions.fullResolution),
    uniforms,
    textures: { [textureName]: makeInput() },
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: 0.375, seed: 19 })
  return destination
}

function caseResult(name, key, uniforms, textureName, coverage) {
  const first = render(key, uniforms, textureName)
  const second = render(key, uniforms, textureName)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${name}: canonical repeat was not byte-identical`)
  }
  return {
    name,
    key,
    uniforms: Object.fromEntries(Object.entries(uniforms).map(([uniform, value]) => [uniform, uniformRecord(value)])),
    coverage,
    f32_sha256: sha256(bytes(first.data)),
    rgba8_sha256: sha256(bytes(firstRgba8)),
    probes: [probe(first, 0, 0), probe(first, 4, 3), probe(first, 8, 6)],
    repeat_identity: { f32_bytes: true, rgba8_bytes: true },
  }
}

function sourceInfo(key, source, normalizedSha256, bindings) {
  const raw = fs.readFileSync(path.join(corpus, source))
  const factory = canonicalKernelFactories[key]
  return {
    key,
    source,
    raw_source_sha256: sha256(raw),
    normalized_source_sha256: normalizedSha256,
    defines: {},
    binding_signature: bindings,
    factory_to_string_sha256: sha256(Buffer.from(factory.toString(), 'utf8')),
  }
}

function build() {
  const widthOrThickness = Math.fround(2.3)
  const lowThreshold = Math.fround(0.18)
  const highThreshold = Math.fround(0.6)
  const unitScale = Math.fround(1)
  const metrics = [1, 2, 3, 4].map(Math.fround)
  return `${JSON.stringify({
    schema: 'noisemaker-for-cpp.task18-fixed-grid-counter-store.canonical-oracles.v1',
    corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: sha256(fs.readFileSync(canonicalKernelsPath)),
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-18-oracle-generator.mjs',
    },
    programs: [
      sourceInfo('filter/celShading:celShadingEdges', 'sources/filter/celShading/celShadingEdges.glsl',
        'c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e',
        ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'colorTex:sampler2D@3/S1', 'edgeWidth:float@4', 'edgeThreshold:float@5', 'renderScale:float@6']),
      sourceInfo('filter/outline:outlineSobel', 'sources/filter/outline/outlineSobel.glsl',
        'fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d',
        ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'valueTexture:sampler2D@3/S1', 'sobelMetric:float@4', 'thickness:float@5', 'renderScale:float@6']),
    ],
    fixture: {
      input: { width: dimensions.input[0], height: dimensions.input[1], construction: inputDescription },
      output: { width: dimensions.output[0], height: dimensions.output[1], storage: 'top-down Surface Float32Array; lane=(y*width+x)*4' },
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      sampler_coordinates: 'input storage is top-down; texelFetch follows canonical GLSL bottom-left coordinates',
      wrap_coverage: 'output 9x7 against input 7x5 and int(2.299999952316284*1)=2 forces both negative and positive wrapCoord residues',
      float_bytes: 'host little-endian Float32Array bytes; probe words use little-endian Uint32',
      context: { time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19, tileOffset: dimensions.tileOffset, fullResolution: dimensions.fullResolution, renderScale: uniformRecord(unitScale) },
      verification: 'each case double-renders with fresh F32 input and destination surfaces and requires identical F32 and RGBA8 bytes before hashing',
      zero_size_early_return: {
        status: 'not executable through public canonical Surface/runPass',
        reason: 'Surface and createCanonicalBindings require strictly positive width and height, so a zero-sized input cannot be constructed or bound through this API.',
        native_requirement: 'Add isolated native tests with a zero-width sampler and then a zero-height sampler while invoking a normal positive destination pixel; each must return exactly vec4(0.0), make no fetches, and bypass the samples/idx grid. Do not emulate this with invalid ordinary Surface construction.',
      },
    },
    cases: [
      caseResult('cel-width-2.3f-threshold-0.18f', 'filter/celShading:celShadingEdges',
        { edgeWidth: widthOrThickness, edgeThreshold: lowThreshold, renderScale: unitScale }, 'colorTex',
        ['non-default-F32-edgeWidth', 'smoothstep-low-interior-high-output-range', 'all-nine-counter-filled-luminosity-reads', 'negative-and-positive-wrapCoord', 'RGB-lane-read']),
      caseResult('cel-width-2.3f-threshold-0.6f', 'filter/celShading:celShadingEdges',
        { edgeWidth: widthOrThickness, edgeThreshold: highThreshold, renderScale: unitScale }, 'colorTex',
        ['second-non-default-F32-threshold', 'smoothstep-boundary-contrast', 'all-nine-counter-filled-luminosity-reads', 'negative-and-positive-wrapCoord']),
      ...metrics.map((sobelMetric) => caseResult(`outline-metric-${sobelMetric}-thickness-2.3f`, 'filter/outline:outlineSobel',
        { sobelMetric, thickness: widthOrThickness, renderScale: unitScale }, 'valueTexture',
        [`metric-${sobelMetric}`, 'non-default-F32-thickness', 'all-nine-counter-filled-scalar-reads', 'negative-and-positive-wrapCoord', 'R-lane-read', sobelMetric === 4 ? 'octagram-1.4140000343322754-divisor' : 'distanceMetric-branch'])),
    ],
  }, null, 2)}\n`
}

const expected = build()
if (process.argv.length === 2) {
  process.stdout.write(expected)
} else if (process.argv.length === 3 && process.argv[2] === '--check') {
  const actual = fs.readFileSync(outputPath, 'utf8')
  if (actual !== expected) throw new Error(`${outputPath} is not the exact frozen canonical oracle output`)
  process.stdout.write(`ok ${path.basename(outputPath)}\n`)
} else {
  throw new Error('usage: node task-18-oracle-generator.mjs [--check]')
}
