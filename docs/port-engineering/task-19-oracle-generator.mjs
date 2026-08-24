import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-19-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6')
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const dimensions = Object.freeze({ input: [11, 9], output: [9, 7], tileOffset: [128, 64], fullResolution: [1024, 768] })
const inputDescription = 'top-down 11x9 Float32Array: R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=0.25+((3*x+5*y+1)%13)/20; every lane assignment crosses the Float32Array boundary'

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
      data[lane] = ((17 * x + 31 * y + 13) % 101) / 100
      data[lane + 1] = ((7 * x + 19 * y + 23) % 97) / 96
      data[lane + 2] = ((29 * x + 11 * y + 5) % 89) / 88
      data[lane + 3] = 0.25 + ((3 * x + 5 * y + 1) % 13) / 20
    }
  }
  return new Surface(width, height, data)
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at: [x, y], values: values.map(printable), f32_bits_le: values.map(f32Bits) }
}

function render(uniforms) {
  const key = 'classicNoisedeck/refract:refract'
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

function caseResult(name, uniforms, coverage) {
  const first = render(uniforms)
  const second = render(uniforms)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${name}: canonical repeat was not byte-identical`)
  }
  return {
    name,
    key: 'classicNoisedeck/refract:refract',
    uniforms: Object.fromEntries(Object.entries(uniforms).map(([uniform, value]) => [uniform, uniformRecord(value)])),
    coverage,
    f32_sha256: sha256(bytes(first.data)),
    rgba8_sha256: sha256(bytes(firstRgba8)),
    probes: [probe(first, 0, 0), probe(first, 4, 3), probe(first, 8, 6)],
    repeat_identity: { f32_bytes: true, rgba8_bytes: true },
  }
}

function sourceInfo() {
  const key = 'classicNoisedeck/refract:refract'
  const source = 'sources/classicNoisedeck/refract/refract.glsl'
  const raw = fs.readFileSync(path.join(corpus, source))
  const factory = canonicalKernelFactories[key]
  return {
    key,
    source,
    raw_source_sha256: sha256(raw),
    normalized_source_sha256: 'bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e',
    defines: {},
    binding_signature: [
      'inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'fullResolution:vec2@4',
      'time:float@5', 'mode:int@6', 'amount:float@7', 'direction:float@8', 'blendMode:int@9', 'mixAmt:float@10', 'wrap:int@11',
    ],
    factory_to_string_sha256: sha256(Buffer.from(factory.toString(), 'utf8')),
  }
}

function build() {
  const mirror = { mode: 1, amount: Math.fround(13.7), direction: Math.fround(37.25), blendMode: 5, mixAmt: Math.fround(23.4), wrap: 0 }
  const repeat = { mode: 1, amount: Math.fround(29.9), direction: Math.fround(137.6), blendMode: 13, mixAmt: Math.fround(50), wrap: 1 }
  const clamp = { mode: 1, amount: Math.fround(73.4), direction: Math.fround(271.125), blendMode: 17, mixAmt: Math.fround(78.9), wrap: 2 }
  const modeZero = { mode: 0, amount: Math.fround(43.2), direction: Math.fround(19.75), blendMode: 10, mixAmt: Math.fround(50), wrap: 0 }
  const truthyTypedArrayCase = (blendMode) => ({
    mode: 1, amount: Math.fround(29.9), direction: Math.fround(137.6),
    blendMode, mixAmt: Math.fround(50), wrap: 1,
  })
  return `${JSON.stringify({
    schema: 'noisemaker-for-cpp.task19-fixed-array-in-parameter.canonical-oracles.v1',
    corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: sha256(fs.readFileSync(canonicalKernelsPath)),
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-19-oracle-generator.mjs',
    },
    programs: [sourceInfo()],
    fixture: {
      input: { width: dimensions.input[0], height: dimensions.input[1], construction: inputDescription },
      output: { width: dimensions.output[0], height: dimensions.output[1], storage: 'top-down Surface Float32Array; lane=(y*width+x)*4' },
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      sampler_coordinates: 'input storage is top-down; texture() follows canonical GLSL bottom-left sampling',
      float_bytes: 'host little-endian Float32Array bytes; probe words use little-endian Uint32',
      context: {
        time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19,
        tileOffset: dimensions.tileOffset, fullResolution: dimensions.fullResolution,
        resolution: dimensions.output,
        displacement_budget: { max: 0.25, expression: '256.0 / max(fullResolution.x, fullResolution.y)' },
      },
      array_execution: 'mode=1 invokes derivX then derivY; each fully initializes its distinct Number kernel[9], calls convolve once, and convolve fully initializes offset[9] before i=0..8 reads offset[i] once and kernel[i] twice.',
      vector_equality_compatibility: {
        affected_blend_modes: [2, 3, 7, 15],
        canonical_behavior: 'Each generated condition is a PooledFloat32Array of lane comparisons. JavaScript treats that object as truthy, selects the bare true-arm vector, performs no reduce/write into middle, and leaves middle at its zero-filled value.',
        required_native_post_transform: 'For exactly the four source/key/signature/guard/predicate/arm shapes recorded by this profile, the selected blendMode branch must leave middle unchanged. A scalar Vec equality ternary assignment is forbidden.',
        source_predicates: {
          2: '(color2 == vec4(0.0)) ? color2 : max(1.0 - ((1.0 - color1) / color2), vec4(0.0))',
          3: '(color2 == vec4(1.0)) ? color2 : min(color1 / (1.0 - color2), vec4(1.0))',
          7: '(color2 == vec4(1.0)) ? color2 : min(color1 * color1 / (1.0 - color2), vec4(1.0))',
          15: '(color1 == vec4(1.0)) ? color1 : min(color2 * color2 / (1.0 - color1), vec4(1.0))',
        },
      },
      verification: 'each case double-renders with fresh F32 input and destination surfaces and requires identical F32 and RGBA8 bytes before hashing',
    },
    cases: [
      caseResult('mode-1-mirror-difference-mix-under-half', mirror, [
        'mode-1-derivX-then-derivY', 'two-distinct-fully-initialized-kernel9-callers', 'convolve-all-nine-offset-and-kernel-reads',
        'wrap-mirror', 'blendMode-5-difference', 'mixAmt-under-half', 'amount-13.7f-floor-map-to-2', 'unclamped-displacement-branch',
      ]),
      caseResult('mode-1-repeat-overlay-mix-half', repeat, [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-repeat',
        'blendMode-13-overlay', 'mixAmt-exact-half', 'amount-29.9f-floor-map-to-5', 'clamped-displacement-branch',
      ]),
      caseResult('mode-1-clamp-softlight-mix-over-half', clamp, [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-clamp',
        'blendMode-17-soft-light', 'mixAmt-over-half', 'amount-73.4f-floor-map-to-14', 'clamped-displacement-branch',
      ]),
      caseResult('mode-0-mirror-mix-control', modeZero, [
        'mode-0-no-derivX-or-derivY-call', 'wrap-mirror', 'blendMode-10-mix', 'mixAmt-exact-half',
        'amount-43.2f-floor-map-to-8', 'clamped-displacement-branch',
      ]),
      caseResult('mode-1-blendMode-2-truthy-typed-array-noop', truthyTypedArrayCase(2), [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-repeat',
        'source-color2-equals-vec4-zero', 'typed-array-object-condition-is-truthy', 'middle-remains-zero-filled',
        'scalarized-Vec-equality-would-diverge', 'mixAmt-exact-half-exposes-middle',
      ]),
      caseResult('mode-1-blendMode-3-truthy-typed-array-noop', truthyTypedArrayCase(3), [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-repeat',
        'source-color2-equals-vec4-one', 'typed-array-object-condition-is-truthy', 'middle-remains-zero-filled',
        'scalarized-Vec-equality-would-diverge', 'mixAmt-exact-half-exposes-middle',
      ]),
      caseResult('mode-1-blendMode-7-truthy-typed-array-noop', truthyTypedArrayCase(7), [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-repeat',
        'source-color2-equals-vec4-one', 'typed-array-object-condition-is-truthy', 'middle-remains-zero-filled',
        'scalarized-Vec-equality-would-diverge', 'mixAmt-exact-half-exposes-middle',
      ]),
      caseResult('mode-1-blendMode-15-truthy-typed-array-noop', truthyTypedArrayCase(15), [
        'mode-1-derivX-then-derivY', 'convolve-all-nine-offset-and-kernel-reads', 'wrap-repeat',
        'source-color1-equals-vec4-one', 'typed-array-object-condition-is-truthy', 'middle-remains-zero-filled',
        'scalarized-Vec-equality-would-diverge', 'mixAmt-exact-half-exposes-middle',
      ]),
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
  throw new Error('usage: node task-19-oracle-generator.mjs [--check]')
}
