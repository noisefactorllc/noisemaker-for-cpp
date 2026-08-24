import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-16-oracles.json')
const key = 'filter/pixelSort:computeRank'
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/pixelSort/computeRank.glsl')
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(value) {
  return Buffer.from(value.buffer, value.byteOffset, value.byteLength)
}

function sameBytes(left, right) {
  return left.byteLength === right.byteLength && Buffer.compare(bytes(left), bytes(right)) === 0
}

function f32Bits(value) {
  const values = new Float32Array([value])
  return `0x${new DataView(values.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}

function printable(value) {
  if (Number.isNaN(value)) return 'NaN'
  if (value === Infinity) return 'Infinity'
  if (value === -Infinity) return '-Infinity'
  return value
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return {
    at: [x, y],
    values: values.map(printable),
    f32_bits_le: values.map(f32Bits),
  }
}

function formulaSurface() {
  const width = 11
  const height = 9
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

function flatTieSurface() {
  const width = 11
  const height = 9
  const data = new Float32Array(width * height * 4)
  for (let lane = 0; lane < data.length; lane += 4) data.set([0.5, 0.25, 0.75, 1], lane)
  return new Surface(width, height, data)
}

function widthOneSurface() {
  return new Surface(1, 1, new Float32Array([0.5, 0.25, 0.75, 1]))
}

function render(lumTex, width, height) {
  const factory = canonicalKernelFactories[key]
  if (typeof factory !== 'function') throw new Error(`missing canonical factory ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width,
    height,
    time: 0.375,
    frame: 7,
    deltaTime: 1 / 60,
    seed: 19,
    tileOffset: new Float32Array([2, 1]),
    fullResolution: new Float32Array([13, 11]),
    textures: { lumTex },
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: 0.375, seed: 19 })
  return destination
}

function caseResult(name, makeSampler, width, height, coverage, construction) {
  const first = render(makeSampler(), width, height)
  const second = render(makeSampler(), width, height)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${name}: canonical repeat was not byte-identical`)
  }
  const probes = width === 1 ? [probe(first, 0, 0)] : [probe(first, 0, 0), probe(first, 4, 3), probe(first, 8, 6)]
  return {
    name,
    output: { width, height, storage: 'top-down Float32Array; lane=(y*width+x)*4' },
    sampler: construction,
    coverage,
    f32_sha256: sha256(bytes(first.data)),
    rgba8_sha256: sha256(bytes(firstRgba8)),
    probes,
    repeat_identity: { f32_bytes: true, rgba8_bytes: true },
  }
}

function build() {
  const source = fs.readFileSync(sourcePath)
  const canonical = fs.readFileSync(canonicalKernelsPath)
  const factory = canonicalKernelFactories[key]
  const document = {
    schema: 'noisemaker-for-cpp.task16-canonical-oracles.v1',
    program: {
      key,
      corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
      source: 'sources/filter/pixelSort/computeRank.glsl',
      source_sha256: sha256(source),
      defines: {},
      binding_signature: ['lumTex:sampler2D@1/S1'],
      output: 'fragColor:vec4',
    },
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: sha256(canonical),
      factory_to_string_sha256: sha256(Buffer.from(factory.toString(), 'utf8')),
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-16-oracle-generator.mjs',
    },
    execution: {
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      output_storage: 'top-down Surface Float32Array',
      sampler_storage: 'top-down Surface Float32Array; texelFetch uses GLSL bottom-left coordinates',
      float_bytes: 'host little-endian Float32Array bytes, with probe bits read little-endian',
      context: { time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19, tileOffset: [2, 1], fullResolution: [13, 11] },
      verification: 'each case is independently double-rendered; F32 and RGBA8 byte arrays must match before hashes are recorded',
    },
    cases: [
      caseResult('formula', formulaSurface, 9, 7,
        ['strict-otherLum-greater-than', 'continue-skip', 'zero-and-positive-rank', 'non-square-sampler-output', 'orientation'],
        {
          width: 11,
          height: 9,
          construction: 'R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=0.35+((3*x+5*y+1)%13)/20; each assignment stores to Float32Array',
        }),
      caseResult('flat-tie', flatTieSurface, 9, 7,
        ['equal-luminance-tie-break', 'sampleX-less-than-x', 'continue-skip', 'zero-and-positive-rank', 'non-square-sampler-output'],
        { width: 11, height: 9, construction: 'every texel is Float32Array [0.5,0.25,0.75,1]' }),
      caseResult('width-one', widthOneSurface, 1, 1,
        ['width-minus-one-zero-denominator', 'quiet-nan-blue-lane', 'all-samples-continue'],
        { width: 1, height: 1, construction: 'the single texel is Float32Array [0.5,0.25,0.75,1]' }),
    ],
  }
  return `${JSON.stringify(document, null, 2)}\n`
}

const expected = build()
if (process.argv.length === 2) {
  process.stdout.write(expected)
} else if (process.argv.length === 3 && process.argv[2] === '--check') {
  const existing = fs.readFileSync(outputPath, 'utf8')
  if (existing !== expected) throw new Error(`${outputPath} is not the exact frozen canonical oracle output`)
  process.stdout.write(`ok ${path.basename(outputPath)}\n`)
} else {
  throw new Error('usage: node task-16-oracle-generator.mjs [--check]')
}
