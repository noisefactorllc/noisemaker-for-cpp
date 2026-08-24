import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-17-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6')
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const inputDescription = 'top-down 11x9 Float32Array: R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=0.35+((3*x+5*y+1)%13)/20; every lane assignment crosses the Float32Array boundary'
const dimensions = Object.freeze({ input: [11, 9], output: [9, 7], tileOffset: [2, 1], fullResolution: [13, 11] })

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const values = new Float32Array([value]); return `0x${new DataView(values.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function printable(value) { return Number.isNaN(value) ? 'NaN' : value }

function makeInput() {
  const [width, height] = dimensions.input
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const lane = (y * width + x) * 4
      data[lane] = ((17 * x + 31 * y + 13) % 101) / 100
      data[lane + 1] = ((7 * x + 19 * y + 23) % 97) / 96
      data[lane + 2] = ((29 * x + 11 * y + 5) % 89) / 88
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

function uniformRecord(value) { return { value, f32_bits_le: f32Bits(value) } }

function render(key, uniforms) {
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
    textures: { inputTex: makeInput() },
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: 0.375, seed: 19 })
  return destination
}

function caseResult(name, key, uniforms, coverage) {
  const first = render(key, uniforms)
  const second = render(key, uniforms)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${name}: canonical repeat was not byte-identical`)
  }
  return {
    name,
    key,
    uniforms: Object.fromEntries(Object.entries(uniforms).map(([name, value]) => [name, uniformRecord(value)])),
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
  const sharpenDefault = Math.fround(1)
  const sharpenNonDefault = Math.fround(2.3)
  const sobelDefault = Math.fround(1)
  const sobelNonDefault = Math.fround(2.3)
  const alphaZero = Math.fround(0)
  const alphaOne = Math.fround(1)
  const document = {
    schema: 'noisemaker-for-cpp.task17-fixed-nine-local-tables.canonical-oracles.v1',
    corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: sha256(fs.readFileSync(canonicalKernelsPath)),
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-17-oracle-generator.mjs',
    },
    programs: [
      sourceInfo('filter/sharpen:sharpen', 'sources/filter/sharpen/sharpen.glsl',
        '1a252d3d5efca1c657dcde87953b12c081c586da01d885e24d3b50395ec5abb0',
        ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'inputTex:sampler2D@3/S1', 'amount:float@4', 'renderScale:float@5']),
      sourceInfo('filter/sobel:sobel', 'sources/filter/sobel/sobel.glsl',
        'd8aad0d49bd0b1badd5231b46bb7bd5a35f9eddadd466afd4ac9f1a0fc0cbf0c',
        ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'inputTex:sampler2D@3/S1', 'amount:float@4', 'renderScale:float@5', 'alpha:float@6']),
    ],
    fixture: {
      input: { width: dimensions.input[0], height: dimensions.input[1], construction: inputDescription },
      output: { width: dimensions.output[0], height: dimensions.output[1], storage: 'top-down Surface Float32Array; lane=(y*width+x)*4' },
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      sampler_coordinates: 'input storage is top-down; texture() follows canonical GLSL bottom-left sampling',
      float_bytes: 'host little-endian Float32Array bytes; probe words use little-endian Uint32',
      context: { time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19, tileOffset: dimensions.tileOffset, fullResolution: dimensions.fullResolution, renderScale: uniformRecord(Math.fround(1)) },
      verification: 'each case double-renders with fresh surfaces and requires identical F32 and RGBA8 bytes before hashing',
    },
    cases: [
      caseResult('sharpen-default', 'filter/sharpen:sharpen', { amount: sharpenDefault, renderScale: Math.fround(1) },
        ['default-amount', 'nine-literal-kernel-reads', 'nine-offset-reads', 'non-square-coordinate-path']),
      caseResult('sharpen-amount-2.3f', 'filter/sharpen:sharpen', { amount: sharpenNonDefault, renderScale: Math.fround(1) },
        ['non-default-f32-amount', 'all-nine-offsets', 'F32-vector-offset-storage']),
      caseResult('sobel-default-alpha-one', 'filter/sobel:sobel', { amount: sobelDefault, renderScale: Math.fround(1), alpha: alphaOne },
        ['default-amount', 'alpha-one', 'two-nine-scalar-kernel-reads', 'nine-offset-reads']),
      caseResult('sobel-amount-2.3f-alpha-zero', 'filter/sobel:sobel', { amount: sobelNonDefault, renderScale: Math.fround(1), alpha: alphaZero },
        ['non-default-f32-amount', 'alpha-zero', 'mix-original-path', 'all-nine-offsets']),
    ],
  }
  return `${JSON.stringify(document, null, 2)}\n`
}

const expected = build()
if (process.argv.length === 2) {
  process.stdout.write(expected)
} else if (process.argv.length === 3 && process.argv[2] === '--check') {
  const actual = fs.readFileSync(outputPath, 'utf8')
  if (actual !== expected) throw new Error(`${outputPath} is not the exact frozen canonical oracle output`)
  process.stdout.write(`ok ${path.basename(outputPath)}\n`)
} else {
  throw new Error('usage: node task-17-oracle-generator.mjs [--check]')
}
