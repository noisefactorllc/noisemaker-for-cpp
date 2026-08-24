import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  canonicalAdapterFactories,
  canonicalKernelFactories,
  kernelFactories,
} from '../../../../../noisemaker-for-cpu/src/effects/catalog.js'
import { UPSTREAM_REVISION } from '../../../../../noisemaker-for-cpu/src/effects/generated/upstream-snapshot.js'
import { createCanonicalBindings } from '../../../../../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel, GlslCpuRuntime } from '../../../../../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../../../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../../../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const platformRoot = path.resolve(here, '../../../../..')
const cppRoot = path.join(platformRoot, 'noisemaker-for-cpp')
const cpuRoot = path.join(platformRoot, 'noisemaker-for-cpu')
const outputPath = path.join(here, 'stats-parity-oracles.json')
const reportPath = path.join(here, 'stats-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const programKey = 'filter/normalize:statsFinal'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/normalize/statsFinal.glsl')
const f = Math.fround

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(view) {
  return Buffer.from(view.buffer, view.byteOffset, view.byteLength)
}

const hostIsLittleEndian = new Uint8Array(new Uint32Array([0x01020304]).buffer)[0] === 0x04

// Float32 SHA-256 contracts are always serialized lane-by-lane in little
// endian order, independent of the generator host's native byte order. The
// raw lane bytes are preserved, including signed zero and NaN payload bits.
function float32LittleEndianBytes(view) {
  if (!(view instanceof Float32Array)) throw new TypeError('Float32 little-endian serialization requires Float32Array')
  const source = bytes(view)
  if (hostIsLittleEndian) return Buffer.from(source)
  const output = Buffer.alloc(source.length)
  for (let offset = 0; offset < source.length; offset += 4) {
    output[offset] = source[offset + 3]
    output[offset + 1] = source[offset + 2]
    output[offset + 2] = source[offset + 1]
    output[offset + 3] = source[offset]
  }
  return output
}

function f32Bits(value) {
  const lane = new DataView(new ArrayBuffer(4))
  lane.setFloat32(0, value, true)
  return `0x${lane.getUint32(0, true).toString(16).padStart(8, '0')}`
}

function compareFloat32Buffers(reference, candidate, width = 1) {
  if (!(reference instanceof Float32Array) || !(candidate instanceof Float32Array)) {
    throw new TypeError('compareFloat32Buffers requires two Float32Array values')
  }
  if (reference.length !== candidate.length) {
    return {
      exact_f32_bits: false,
      reference_lanes: reference.length,
      candidate_lanes: candidate.length,
      mismatched_lanes: Math.max(reference.length, candidate.length),
      first_mismatch: null,
      max_absolute_difference: null,
    }
  }
  const a = new Uint32Array(reference.buffer, reference.byteOffset, reference.length)
  const b = new Uint32Array(candidate.buffer, candidate.byteOffset, candidate.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let i = 0; i < reference.length; i += 1) {
    if (a[i] === b[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        lane_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % width, Math.floor(pixel / width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_value: reference[i],
        candidate_value: candidate[i],
        reference_bits_le: `0x${a[i].toString(16).padStart(8, '0')}`,
        candidate_bits_le: `0x${b[i].toString(16).padStart(8, '0')}`,
      }
    }
    const difference = Math.abs(reference[i] - candidate[i])
    if (Number.isFinite(difference)) maxAbsoluteDifference = Math.max(maxAbsoluteDifference, difference)
  }
  return {
    exact_f32_bits: mismatched === 0,
    reference_lanes: reference.length,
    candidate_lanes: candidate.length,
    mismatched_lanes: mismatched,
    first_mismatch: first,
    max_absolute_difference: maxAbsoluteDifference,
  }
}

function compareRgba8Buffers(reference, candidate, width = 1) {
  if (reference.length !== candidate.length) throw new Error('RGBA8 length mismatch')
  let mismatched = 0
  let first = null
  for (let i = 0; i < reference.length; i += 1) {
    if (reference[i] === candidate[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        byte_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % width, Math.floor(pixel / width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_byte: reference[i],
        candidate_byte: candidate[i],
      }
    }
  }
  return { exact_rgba8_bytes: mismatched === 0, mismatched_bytes: mismatched, first_mismatch: first }
}

function compareSurfaces(reference, candidate) {
  if (reference.width !== candidate.width || reference.height !== candidate.height) {
    return {
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      float32: null,
      rgba8: null,
    }
  }
  return {
    dimensions_match: true,
    reference_dimensions: [reference.width, reference.height],
    candidate_dimensions: [candidate.width, candidate.height],
    float32: compareFloat32Buffers(reference.data, candidate.data, reference.width),
    rgba8: compareRgba8Buffers(reference.toRgba8(), candidate.toRgba8(), reference.width),
    candidate_f32_sha256: sha256(float32LittleEndianBytes(candidate.data)),
    candidate_rgba8_sha256: sha256(bytes(candidate.toRgba8())),
  }
}

function requireExact(label, comparison) {
  if (!comparison.dimensions_match || !comparison.float32.exact_f32_bits || !comparison.rgba8.exact_rgba8_bytes) {
    throw new Error(`${label}: ${JSON.stringify(comparison)}`)
  }
}

const provenanceFiles = {
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  adapter_index: ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', '8579de7f8d3ff35a71c35c2c5e32296d0f71ffef1e790db9736f99ab04969936'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
}

for (const [name, [relativePath, expectedHash]] of Object.entries(provenanceFiles)) {
  const actualHash = sha256(fs.readFileSync(path.join(cpuRoot, relativePath)))
  if (actualHash !== expectedHash) throw new Error(`${name} provenance drift: ${actualHash}`)
}

const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== 959 || sha256(sourceBytes) !== '0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa') {
  throw new Error('pinned statsFinal GLSL source drift')
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory90') throw new Error('canonical factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 1062 || sha256(canonicalFactory.toString()) !== '07eb7daea90fd057b232093fe2912b663ec6b780178d09ddf8212d15ea932172') {
  throw new Error('canonical factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected statsFinal adapter override')

function resourceContract(inputWidth, inputHeight, outputWidth, outputHeight) {
  if (!Number.isSafeInteger(inputWidth)) return { accepted: false, reason: 'input width must be a safe integer' }
  if (inputWidth < 1 || inputWidth > 64) return { accepted: false, reason: 'input width must be in [1,64]' }
  if (!Number.isSafeInteger(inputHeight)) return { accepted: false, reason: 'input height must be a safe integer' }
  if (inputHeight < 1 || inputHeight > 64) return { accepted: false, reason: 'input height must be in [1,64]' }
  if (!Number.isSafeInteger(outputWidth)) return { accepted: false, reason: 'output width must be a safe integer' }
  if (!Number.isSafeInteger(outputHeight)) return { accepted: false, reason: 'output height must be a safe integer' }
  if (outputWidth !== 1 || outputHeight !== 1) return { accepted: false, reason: 'output extent must be exactly 1x1' }
  const fetches = inputWidth * inputHeight
  return {
    accepted: true,
    reason: null,
    input_axes: [inputWidth, inputHeight],
    output_extent: [outputWidth, outputHeight],
    canonical_lexical_product: fetches,
    canonical_maximum_texel_fetches: fetches,
    canonical_entrypoint_proof_charge: inputHeight * (1 + inputWidth),
  }
}

const caseDefinitions = [
  { name: 'single-texel-adversarial-unused-lanes', width: 1, height: 1, phase: 1, minAt: [0, 0], maxAt: [0, 0], filter: 'nearest', wrap: 'clamp', adversarialUnused: true },
  { name: 'one-by-sixty-four-y-boundary', width: 1, height: 64, phase: 2, minAt: [0, 0], maxAt: [0, 63], filter: 'linear', wrap: 'repeat' },
  { name: 'sixty-four-by-one-x-boundary', width: 64, height: 1, phase: 3, minAt: [0, 0], maxAt: [63, 0], filter: 'nearest', wrap: 'mirror' },
  { name: 'sixty-four-square-full-resource-boundary', width: 64, height: 64, phase: 4, minAt: [0, 0], maxAt: [63, 63], filter: 'linear', wrap: 'repeat', relevantInfinities: true },
  { name: 'sixty-three-by-sixty-four-near-product-boundary', width: 63, height: 64, phase: 5, minAt: [62, 0], maxAt: [0, 63], filter: 'nearest', wrap: 'clamp' },
  { name: 'thirty-seven-by-fifty-three-nonsquare', width: 37, height: 53, phase: 6, minAt: [0, 26], maxAt: [36, 27], filter: 'linear', wrap: 'mirror' },
  { name: 'all-positive-r-all-negative-g-initializer-trap', width: 11, height: 9, phase: 7, minAt: [0, 8], maxAt: [10, 0], filter: 'nearest', wrap: 'repeat', arithmeticTrap: true },
]

function makeInput(definition) {
  const { width, height, phase } = definition
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      if (definition.arithmeticTrap) {
        data[i] = f(0.25 + ((x * 11 + y * 7 + phase) % 61) / 100)
        data[i + 1] = f(-0.95 + ((x * 5 + y * 13 + phase) % 41) / 100)
      } else {
        data[i] = f(-3.5 + ((x * 17 + y * 29 + phase * 7) % 211) / 23)
        data[i + 1] = f(-4.25 + ((x * 31 + y * 11 + phase * 5) % 197) / 19)
      }
      data[i + 2] = f(((x * 7 + y * 19 + phase) % 101) / 37 - 1)
      data[i + 3] = f(((x * 23 + y * 3 + phase) % 89) / 41)
    }
  }
  const minOffset = (definition.minAt[1] * width + definition.minAt[0]) * 4
  const maxOffset = (definition.maxAt[1] * width + definition.maxAt[0]) * 4
  data[minOffset] = definition.arithmeticTrap ? f(0.125) : f(-123.75)
  data[maxOffset + 1] = definition.arithmeticTrap ? f(-0.125) : f(456.5)
  if (definition.adversarialUnused) {
    data[0] = f(-17.25)
    data[1] = f(33.5)
    data[2] = Number.NaN
    data[3] = Number.POSITIVE_INFINITY
  }
  if (definition.relevantInfinities) {
    const plus = (17 * width + 13) * 4
    const minus = (19 * width + 29) * 4
    data[plus] = Number.POSITIVE_INFINITY
    data[minus + 1] = Number.NEGATIVE_INFINITY
    data[plus + 2] = Number.NEGATIVE_INFINITY
    data[minus + 3] = Number.NaN
  }
  const surface = new Surface(width, height, data)
  surface.filter = definition.filter
  surface.wrap = definition.wrap
  return surface
}

function independentReduce(surface) {
  let minValue = 100000
  let maxValue = -100000
  for (let shaderY = 0; shaderY < surface.height; shaderY += 1) {
    const topDownY = surface.height - 1 - shaderY
    for (let x = 0; x < surface.width; x += 1) {
      const offset = (topDownY * surface.width + x) * 4
      minValue = Math.min(minValue, surface.data[offset])
      maxValue = Math.max(maxValue, surface.data[offset + 1])
    }
  }
  return new Float32Array([minValue, maxValue, 0, 1])
}

function tracedKernel(factory, bindings, input, trace) {
  const runtime = new GlslCpuRuntime()
  const realTexelFetch = runtime.stdlib.texelFetch
  runtime.stdlib = Object.freeze({
    ...runtime.stdlib,
    texelFetch(sampler, coordinate, lod) {
      trace.push({
        pre_clamp_coordinate: [Number(coordinate[0]), Number(coordinate[1])],
        sampler_identity: sampler === input ? 'inputTex' : 'foreign',
        lod: Number(lod),
      })
      return realTexelFetch(sampler, coordinate, lod)
    },
  })
  const kernel = factory(Object.freeze({ ...bindings }), runtime)
  if (typeof kernel !== 'function') throw new TypeError('traced GLSL factory must return a pixel kernel')
  if (factory.usesDerivatives) throw new Error('statsFinal unexpectedly requires derivative wrapping')
  return kernel
}

function render(factory, input, options = {}) {
  const before = input.data.slice()
  const bindings = createCanonicalBindings({
    width: 1,
    height: 1,
    time: 0,
    frame: 41,
    deltaTime: f(1 / 60),
    seed: f(991),
    textures: { inputTex: input },
  })
  if (bindings.inputTex !== input) throw new Error('inputTex binding identity drift')
  if (f32Bits(bindings.resolution[0]) !== f32Bits(1) || f32Bits(bindings.resolution[1]) !== f32Bits(1)) throw new Error('destination resolution binding drift')
  const trace = []
  const kernel = options.trace ? tracedKernel(factory, bindings, input, trace) : bindGlslKernel(factory, bindings)
  const output = new Surface(1, 1)
  runPass({ kernel, destination: output, time: 0, seed: f(991) })
  const immutability = compareFloat32Buffers(before, input.data, input.width)
  if (!immutability.exact_f32_bits) throw new Error(`input mutation: ${JSON.stringify(immutability)}`)
  return { output, immutability, fetch_trace: trace }
}

function cloneWithSampler(input, filter, wrap) {
  const copy = new Surface(input.width, input.height, input.data.slice())
  copy.filter = filter
  copy.wrap = wrap
  return copy
}

function outputRecord(surface) {
  const values = Array.from(surface.data)
  if (values.some((value) => !Number.isFinite(value))) throw new Error('statsFinal output contains a nonfinite lane')
  return {
    f32_sha256: sha256(float32LittleEndianBytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    values,
    f32_bits_le: values.map(f32Bits),
    finite_lanes: values.filter(Number.isFinite).length,
    nonfinite_lanes: values.filter((value) => !Number.isFinite(value)).length,
    probe: { at_top_down_xy: [0, 0], values, f32_bits_le: values.map(f32Bits) },
  }
}

function mutateFactory(anchor, replacement) {
  const text = canonicalFactory.toString()
  if (text.split(anchor).length - 1 !== 1) throw new Error(`mutation anchor not unique: ${anchor}`)
  return (0, eval)(`(${text.replace(anchor, replacement)})`)
}

const mutations = [
  { id: 'drop-last-row', kind: 'row_loop_off_by_one', anchor: 'for (var y = 0; y < inSize[1]; y++) {', replacement: 'for (var y = 0; y < inSize[1] - 1; y++) {' },
  { id: 'drop-last-column', kind: 'column_loop_off_by_one', anchor: 'for (var x = 0; x < inSize[0]; x++) {', replacement: 'for (var x = 0; x < inSize[0] - 1; x++) {' },
  { id: 'y-bound-uses-width-lane', kind: 'wrong_axis_seed', anchor: 'for (var y = 0; y < inSize[1]; y++) {', replacement: 'for (var y = 0; y < inSize[0]; y++) {' },
  { id: 'x-bound-uses-height-lane', kind: 'wrong_axis_seed', anchor: 'for (var x = 0; x < inSize[0]; x++) {', replacement: 'for (var x = 0; x < inSize[1]; x++) {' },
  { id: 'skip-first-column', kind: 'skipped_texel', anchor: 'for (var x = 0; x < inSize[0]; x++) {', replacement: 'for (var x = 1; x < inSize[0]; x++) {' },
  { id: 'extra-clamped-column', kind: 'extra_texel_resource_charge', anchor: 'for (var x = 0; x < inSize[0]; x++) {', replacement: 'for (var x = 0; x <= inSize[0]; x++) {', structuralOnly: true },
  { id: 'swap-fetch-coordinate-axes', kind: 'wrong_fetch_coordinate', anchor: 'texelFetch(inputTex, cpu_ivec2(x, y), 0)', replacement: 'texelFetch(inputTex, cpu_ivec2(y, x), 0)' },
  { id: 'zero-min-initializer', kind: 'normalization_arithmetic_trap', anchor: 'var minVal = 100000;', replacement: 'var minVal = 0;' },
  { id: 'zero-max-initializer', kind: 'normalization_arithmetic_trap', anchor: 'var maxVal = -100000;', replacement: 'var maxVal = 0;' },
  { id: 'min-consumes-green-lane', kind: 'normalization_lane_trap', anchor: 'minVal = min(minVal, color[0]);', replacement: 'minVal = min(minVal, color[1]);' },
  { id: 'max-consumes-red-lane', kind: 'normalization_lane_trap', anchor: 'maxVal = max(maxVal, color[1]);', replacement: 'maxVal = max(maxVal, color[0]);' },
]

function traceBytes(trace) {
  return Buffer.from(JSON.stringify(trace))
}

function summarizeFetchTrace(trace) {
  return {
    observed_fetch_count: trace.length,
    trace_sha256: sha256(traceBytes(trace)),
    first_fetch: trace[0] ?? null,
    last_fetch: trace.at(-1) ?? null,
    sampler_identities: [...new Set(trace.map((entry) => entry.sampler_identity))].sort(),
    lod_values: [...new Set(trace.map((entry) => entry.lod))].sort((a, b) => a - b),
  }
}

function compareFetchTraces(reference, candidate) {
  let firstMismatch = null
  const shared = Math.min(reference.length, candidate.length)
  for (let i = 0; i < shared; i += 1) {
    if (JSON.stringify(reference[i]) === JSON.stringify(candidate[i])) continue
    firstMismatch = { fetch_index: i, reference_fetch: reference[i], candidate_fetch: candidate[i] }
    break
  }
  if (firstMismatch === null && reference.length !== candidate.length) {
    firstMismatch = { fetch_index: shared, reference_fetch: reference[shared] ?? null, candidate_fetch: candidate[shared] ?? null }
  }
  return {
    exact_fetch_trace: firstMismatch === null,
    reference: summarizeFetchTrace(reference),
    candidate: summarizeFetchTrace(candidate),
    first_mismatch: firstMismatch,
  }
}

function assertCanonicalTrace(trace, input, label) {
  if (trace.length !== input.width * input.height) throw new Error(`${label}: canonical traced fetch count mismatch`)
  let index = 0
  for (let y = 0; y < input.height; y += 1) {
    for (let x = 0; x < input.width; x += 1) {
      const entry = trace[index++]
      if (entry.pre_clamp_coordinate[0] !== x || entry.pre_clamp_coordinate[1] !== y || entry.sampler_identity !== 'inputTex' || entry.lod !== 0) {
        throw new Error(`${label}: canonical trace mismatch at fetch ${index - 1}: ${JSON.stringify(entry)}`)
      }
    }
  }
}

function assertExtraColumnTrace(canonicalTrace, mutatedTrace, input, label) {
  const expectedMutatedFetches = input.height * (input.width + 1)
  if (mutatedTrace.length !== expectedMutatedFetches) throw new Error(`${label}: expected ${expectedMutatedFetches} actual mutated fetches, observed ${mutatedTrace.length}`)
  const extras = []
  let index = 0
  for (let y = 0; y < input.height; y += 1) {
    for (let x = 0; x <= input.width; x += 1) {
      const entry = mutatedTrace[index++]
      if (entry.pre_clamp_coordinate[0] !== x || entry.pre_clamp_coordinate[1] !== y || entry.sampler_identity !== 'inputTex' || entry.lod !== 0) {
        throw new Error(`${label}: actual extra-column trace mismatch at fetch ${index - 1}: ${JSON.stringify(entry)}`)
      }
      if (x === input.width) extras.push({ fetch_index: index - 1, ...entry })
    }
  }
  if (extras.length !== input.height) throw new Error(`${label}: expected one observed extra fetch per row`)
  if (compareFetchTraces(canonicalTrace, mutatedTrace).exact_fetch_trace) throw new Error(`${label}: mutated trace unexpectedly equals canonical trace`)
  return {
    canonical_observed_fetches: canonicalTrace.length,
    mutated_observed_fetches: mutatedTrace.length,
    mutated_lexical_product: expectedMutatedFetches,
    mutated_entrypoint_proof_charge: input.height * (1 + input.width + 1),
    observed_extra_fetches: extras,
  }
}

const invalidAxisValues = [
  ['negative-one', -1],
  ['fractional', 1.5],
  ['nan', Number.NaN],
  ['positive-infinity', Number.POSITIVE_INFINITY],
  ['negative-infinity', Number.NEGATIVE_INFINITY],
  ['unsafe-integer', Number.MAX_SAFE_INTEGER + 1],
]

const negativeDefinitions = [
  { name: 'zero-input-width', inputWidth: 0, inputHeight: 1, outputWidth: 1, outputHeight: 1 },
  { name: 'zero-input-height', inputWidth: 1, inputHeight: 0, outputWidth: 1, outputHeight: 1 },
  { name: 'input-width-65', inputWidth: 65, inputHeight: 1, outputWidth: 1, outputHeight: 1 },
  { name: 'input-height-65', inputWidth: 1, inputHeight: 65, outputWidth: 1, outputHeight: 1 },
  { name: 'huge-safe-input-axes-rejected-before-product', inputWidth: 4294967296, inputHeight: 4294967296, outputWidth: 1, outputHeight: 1 },
  { name: 'output-two-by-one', inputWidth: 64, inputHeight: 64, outputWidth: 2, outputHeight: 1 },
  { name: 'output-one-by-two', inputWidth: 64, inputHeight: 64, outputWidth: 1, outputHeight: 2 },
  { name: 'output-zero-width', inputWidth: 64, inputHeight: 64, outputWidth: 0, outputHeight: 1 },
  { name: 'output-zero-height', inputWidth: 64, inputHeight: 64, outputWidth: 1, outputHeight: 0 },
]
for (const [suffix, value] of invalidAxisValues) {
  negativeDefinitions.push(
    { name: `input-width-${suffix}`, inputWidth: value, inputHeight: 1, outputWidth: 1, outputHeight: 1 },
    { name: `input-height-${suffix}`, inputWidth: 1, inputHeight: value, outputWidth: 1, outputHeight: 1 },
    { name: `output-width-${suffix}`, inputWidth: 1, inputHeight: 1, outputWidth: value, outputHeight: 1 },
    { name: `output-height-${suffix}`, inputWidth: 1, inputHeight: 1, outputWidth: 1, outputHeight: value },
  )
}

function dimensionToken(value) {
  if (Number.isNaN(value)) return 'NaN'
  if (value === Number.POSITIVE_INFINITY) return '+Infinity'
  if (value === Number.NEGATIVE_INFINITY) return '-Infinity'
  return value
}

function buildData() {
  const cases = caseDefinitions.map((definition) => {
    const contract = resourceContract(definition.width, definition.height, 1, 1)
    if (!contract.accepted) throw new Error(`${definition.name}: positive contract rejected`)
    const input = makeInput(definition)
    const inputBefore = input.data.slice()
    const direct = render(canonicalFactory, input, { trace: true })
    assertCanonicalTrace(direct.fetch_trace, input, definition.name)
    const repeated = render(canonicalFactory, input)
    const publicRender = render(publicFactory, input)
    const repeatIdentity = compareSurfaces(direct.output, repeated.output)
    const publicEquality = compareSurfaces(direct.output, publicRender.output)
    requireExact(`${definition.name}: repeat`, repeatIdentity)
    requireExact(`${definition.name}: public`, publicEquality)

    const independent = new Surface(1, 1, independentReduce(input))
    const independentEquality = compareSurfaces(direct.output, independent)
    requireExact(`${definition.name}: independent reduction`, independentEquality)

    const samplerVariants = []
    for (const [filter, wrap] of [['nearest', 'clamp'], ['linear', 'repeat'], ['linear', 'mirror']]) {
      const variant = cloneWithSampler(input, filter, wrap)
      const rendered = render(canonicalFactory, variant)
      const comparison = compareSurfaces(direct.output, rendered.output)
      requireExact(`${definition.name}: texelFetch sampler invariance ${filter}/${wrap}`, comparison)
      samplerVariants.push({ filter, wrap, comparison })
    }

    return {
      name: definition.name,
      input_dimensions: [definition.width, definition.height],
      output_dimensions: [1, 1],
      eligible_for_native_binding: true,
      sampler_state: { filter: definition.filter, wrap: definition.wrap, relevance: 'ignored by level-zero integer texelFetch; exact invariance is verified below' },
      contract,
      input: {
        f32_sha256_before: sha256(float32LittleEndianBytes(inputBefore)),
        f32_sha256_after: sha256(float32LittleEndianBytes(input.data)),
        immutable: direct.immutability,
        contains_nonfinite_unused_lanes: input.data.some((value, i) => i % 4 >= 2 && !Number.isFinite(value)),
        contains_infinite_reduction_lanes: input.data.some((value, i) => i % 4 < 2 && !Number.isFinite(value)),
      },
      output: outputRecord(direct.output),
      actual_canonical_fetch_trace: summarizeFetchTrace(direct.fetch_trace),
      repeat_identity: repeatIdentity,
      public_catalog_vs_direct_canonical: publicEquality,
      independent_row_major_bottom_left_reduction: independentEquality,
      texel_fetch_filter_wrap_invariance: samplerVariants,
    }
  })

  const mutationResults = mutations.map((mutation) => {
    const factory = mutateFactory(mutation.anchor, mutation.replacement)
    const neutralizedFactory = mutation.structuralOnly ? mutateFactory(mutation.anchor, mutation.anchor) : null
    let divergentCases = 0
    let traceDivergentCases = 0
    const caseResults = caseDefinitions.map((definition, index) => {
      const input = makeInput(definition)
      const canonical = new Surface(1, 1, new Float32Array(cases[index].output.values))
      const canonicalObserved = render(canonicalFactory, input, { trace: true })
      const mutatedObserved = render(factory, input, { trace: true })
      assertCanonicalTrace(canonicalObserved.fetch_trace, input, `${mutation.id}/${definition.name}`)
      const pixelComparison = compareSurfaces(canonical, mutatedObserved.output)
      const fetchTraceComparison = compareFetchTraces(canonicalObserved.fetch_trace, mutatedObserved.fetch_trace)
      if (!pixelComparison.float32.exact_f32_bits) divergentCases += 1
      if (!fetchTraceComparison.exact_fetch_trace) traceDivergentCases += 1
      let extraColumnAccounting = null
      let neutralizedSourceMutationRejected = null
      if (mutation.structuralOnly) {
        if (!pixelComparison.float32.exact_f32_bits || !pixelComparison.rgba8.exact_rgba8_bytes) throw new Error(`${mutation.id}/${definition.name}: extra clamped fetch unexpectedly changes pixels`)
        extraColumnAccounting = assertExtraColumnTrace(canonicalObserved.fetch_trace, mutatedObserved.fetch_trace, input, `${mutation.id}/${definition.name}`)
        try {
          // Evaluate the factory after an explicitly neutralized textual
          // replacement, trace its real execution, and require the actual
          // observation assertion to reject it. No mutation id participates.
          const neutralizedObserved = render(neutralizedFactory, input, { trace: true })
          assertExtraColumnTrace(canonicalObserved.fetch_trace, neutralizedObserved.fetch_trace, input, `${mutation.id}/${definition.name}/neutralized`)
          neutralizedSourceMutationRejected = false
        } catch {
          neutralizedSourceMutationRejected = true
        }
        if (!neutralizedSourceMutationRejected) throw new Error(`${mutation.id}/${definition.name}: neutralized source mutation self-test passed unexpectedly`)
      }
      return {
        case: definition.name,
        pixel_comparison: pixelComparison,
        actual_fetch_trace_comparison: fetchTraceComparison,
        extra_column_accounting: extraColumnAccounting,
        neutralized_source_mutation_rejected: neutralizedSourceMutationRejected,
      }
    })
    if (mutation.structuralOnly) {
      if (traceDivergentCases !== caseDefinitions.length) throw new Error(`${mutation.id}: actual resource/fetch trace mutation not discriminated in every case`)
    } else if (divergentCases === 0) {
      throw new Error(`${mutation.id}: no pixel-level divergence`)
    }
    return {
      id: mutation.id,
      kind: mutation.kind,
      discriminator: mutation.structuralOnly ? 'actual instrumented pre-clamp texelFetch trace (pixel reduction is intentionally idempotent)' : 'exact Float32 pixel bits',
      divergent_pixel_cases: divergentCases,
      divergent_actual_fetch_trace_cases: traceDivergentCases,
      case_results: caseResults,
    }
  })

  const negatives = negativeDefinitions.map((definition) => {
    const result = resourceContract(definition.inputWidth, definition.inputHeight, definition.outputWidth, definition.outputHeight)
    if (result.accepted) throw new Error(`${definition.name}: negative resource contract accepted`)
    return {
      name: definition.name,
      input_dimensions: [dimensionToken(definition.inputWidth), dimensionToken(definition.inputHeight)],
      output_dimensions: [dimensionToken(definition.outputWidth), dimensionToken(definition.outputHeight)],
      result,
    }
  })

  const boundary = resourceContract(64, 64, 1, 1)
  if (!boundary.accepted || boundary.canonical_lexical_product !== 4096 || boundary.canonical_maximum_texel_fetches !== 4096 || boundary.canonical_entrypoint_proof_charge !== 4160) {
    throw new Error(`64x64 accounting drift: ${JSON.stringify(boundary)}`)
  }
  if (!cases.some((record) => record.input_dimensions[0] === 1 && record.input_dimensions[1] === 1)) throw new Error('missing 1x1 case')
  if (!cases.some((record) => record.input_dimensions[0] === 1 && record.input_dimensions[1] === 64)) throw new Error('missing 1x64 case')
  if (!cases.some((record) => record.input_dimensions[0] === 64 && record.input_dimensions[1] === 1)) throw new Error('missing 64x1 case')
  if (!cases.some((record) => record.input_dimensions[0] === 64 && record.input_dimensions[1] === 64)) throw new Error('missing 64x64 case')
  if (!cases.some((record) => record.input_dimensions[0] !== record.input_dimensions[1] && record.input_dimensions[0] > 1 && record.input_dimensions[1] > 1)) throw new Error('missing representative non-square case')

  return {
    schema: 'noisemaker-for-cpp.normalize-stats-final.pixel-resource-oracle.v1',
    program_key: programKey,
    corpus_revision: corpusRevision,
    upstream_revision: UPSTREAM_REVISION,
    provenance: {
      node: process.version,
      reference_api: 'canonicalKernelFactories[program_key] via bindGlslKernel/createCanonicalBindings; destination is exactly 1x1',
      public_api: 'kernelFactories.get(program_key)',
      canonical_factory_name: canonicalFactory.name,
      canonical_factory_bytes: Buffer.byteLength(canonicalFactory.toString()),
      canonical_factory_to_string_sha256: sha256(canonicalFactory.toString()),
      source_raw_bytes: sourceBytes.length,
      source_sha256: sha256(sourceBytes),
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    resource_contract: {
      profile: 'normalize-stats-final-resource-bound-v1',
      input_axes_inclusive: [1, 64],
      maximum_lexical_product: 4096,
      maximum_level_zero_texel_fetches: 4096,
      exact_output_extent: [1, 1],
      native_output_preflight_acceptance_requirement: 'future C++ run_pass must reject a non-1x1 destination before constructing its result Surface',
      oracle_scope_note: 'this JavaScript oracle models the closed extent and freezes negative values; it does not execute or prove the future native allocation-order seam',
      boundary_accounting_64x64: boundary,
      product_note: 'the 1..64 per-axis contract mathematically implies product <=4096; no separate product-overflow branch is reachable or claimed',
      accounting_note: 'canonical lexical product and actual fetches are 4096; canonical CountedLoopProof entrypoint charge is independently 64*(1+64)=4160; the extra-column mutation instead has 4160 actual fetches and proof charge 4224',
    },
    fixture: {
      layout: 'top-down Float32 RGBA Surface; canonical texelFetch traverses shader-y bottom-up and x left-to-right',
      reduction: 'minimum R and maximum G only; B/A are ignored',
      sampler_semantics: 'texelFetch(inputTex, ivec2(x,y),0) is integer, level-zero, in-bounds, and independent of normalized filtering/wrap state',
      nonfinite_policy: 'NaN is confined to ignored B/A lanes; infinities in R/G are admitted only where other finite extrema keep the output finite',
      comparer: 'exact Float32-bit and RGBA8-byte comparer with pixel/channel mismatch diagnostics; Float32 hashes serialize every lane explicitly little-endian',
      repeated_render_count: 2,
    },
    cases,
    contract_negatives: negatives,
    mutations: mutationResults,
    invariant_audit: {
      accepted_cases: cases.length,
      rejected_contract_cases: negatives.length,
      all_outputs_exactly_1x1: cases.every((record) => JSON.stringify(record.output_dimensions) === '[1,1]'),
      all_inputs_immutable: cases.every((record) => record.input.immutable.exact_f32_bits),
      all_repeat_exact: cases.every((record) => record.repeat_identity.float32.exact_f32_bits && record.repeat_identity.rgba8.exact_rgba8_bytes),
      all_public_direct_exact: cases.every((record) => record.public_catalog_vs_direct_canonical.float32.exact_f32_bits && record.public_catalog_vs_direct_canonical.rgba8.exact_rgba8_bytes),
      all_independent_reduce_exact: cases.every((record) => record.independent_row_major_bottom_left_reduction.float32.exact_f32_bits),
      all_filter_wrap_variants_exact: cases.every((record) => record.texel_fetch_filter_wrap_invariance.every((variant) => variant.comparison.float32.exact_f32_bits && variant.comparison.rgba8.exact_rgba8_bytes)),
      all_outputs_finite: cases.every((record) => record.output.nonfinite_lanes === 0),
      mutation_count: mutationResults.length,
      all_mutations_discriminated: mutationResults.every((record) => record.divergent_pixel_cases > 0 || record.divergent_actual_fetch_trace_cases === cases.length),
      all_extra_column_neutralizations_rejected: mutationResults.filter((record) => record.id === 'extra-clamped-column').every((record) => record.case_results.every((result) => result.neutralized_source_mutation_rejected)),
    },
  }
}

function makeReport(data) {
  const lines = [
    '# Normalize statsFinal pixel/resource oracle', '',
    'Frozen JavaScript ground truth for `filter/normalize:statsFinal`, rendered through the canonical noisemaker-for-cpu factory into the only authorized destination extent, `1x1`. Float32 hashes and RGBA8 hashes are exact byte contracts. The custom comparer adds first-pixel/channel diagnostics without weakening those contracts.', '',
    '## Closed runtime contract', '',
    '- `inputTex` width and height are safe integers in `1..64`.',
    '- The two axis bounds mathematically imply an input product and maximum level-zero integer fetch count of at most 4,096; the oracle does not claim a separately reachable product guard.',
    '- Destination extent is exactly `1x1`. This oracle freezes that acceptance requirement, but does not execute the future C++ allocation seam; native tests must prove rejection occurs before result-Surface construction.',
    '- At `64x64`, lexical loop product and fetches are 4,096 while the repository proof metric is separately `entrypoint_charge = 64 * (1 + 64) = 4,160`.', '',
    '## Positive parity cases', '',
    '| Case | Input | Product/fetches | Proof charge | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | ---: | ---: | ---: | --- | --- |',
  ]
  for (const record of data.cases) {
    lines.push(`| ${record.name} | ${record.input_dimensions.join('x')} | ${record.contract.canonical_maximum_texel_fetches} | ${record.contract.canonical_entrypoint_proof_charge} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every positive case passes exact repeat identity, public-catalog/direct-canonical equality, exact-bit input immutability, an independent bottom-left row-major reduction, and nearest/linear plus clamp/repeat/mirror state invariance. Filtering and wrapping are not sampling choices for this shader: its sole read is in-bounds `texelFetch(..., 0)`.', '')
  lines.push('Adversarial coverage includes ignored-lane NaN/infinity, relevant-lane infinities that cannot win the finite extrema, negative/positive extrema, all-positive R with all-negative G, both degenerate axes, the full `64x64` boundary, a near-product boundary, and a representative non-square surface.', '')
  lines.push('## Rejected resource shapes', '', '| Case | Input | Output | Reason |', '| --- | ---: | ---: | --- |')
  for (const record of data.contract_negatives) lines.push(`| ${record.name} | ${record.input_dimensions.join('x')} | ${record.output_dimensions.join('x')} | ${record.result.reason} |`)
  lines.push('', 'Invalid coverage includes -1, fractional, NaN, positive infinity, negative infinity, and an unsafe integer independently in all four input/output axis positions. The huge-safe-axis case is explicitly rejected by the per-axis cap before multiplication; no product-overflow coverage is claimed. No rejected case constructs a Surface or pixel fixture; rejected pixels are not part of the contract.', '')
  lines.push('## Mutation discrimination', '', '| Mutation | Class | Pixel-divergent cases | Actual fetch-trace-divergent cases | Discriminator |', '| --- | --- | ---: | ---: | --- |')
  for (const record of data.mutations) lines.push(`| ${record.id} | ${record.kind} | ${record.divergent_pixel_cases}/${data.cases.length} | ${record.divergent_actual_fetch_trace_cases}/${data.cases.length} | ${record.discriminator} |`)
  lines.push('', 'The trace evidence is observed from canonical and evaluated-mutant factories through a real `GlslCpuRuntime` whose sole wrapped stdlib operation records each actual pre-clamp coordinate, sampler identity, and LOD before delegating to the pinned implementation. It is not predicted from mutation ids.', '')
  lines.push('The extra-column mutation is intentionally output-idempotent because an out-of-range integer fetch clamps to an edge texel already included in a min/max reduction. For every case, the actual trace contains exactly `height * (width + 1)` fetches, exactly one extra `[width,y]` coordinate per row, only `inputTex`, and only LOD 0. Its 64x64 resource count is 4,160 fetches and its proof charge would be 4,224; those are distinct from the canonical 4,096 fetches and 4,160 proof charge. Passing the unmutated canonical trace to the same assertion is required to fail in every case.', '')
  lines.push('## Determinism and provenance', '')
  lines.push(`- Corpus revision: \`${data.corpus_revision}\``)
  lines.push(`- Upstream snapshot revision: \`${data.upstream_revision}\``)
  lines.push(`- GLSL source SHA-256: \`${data.provenance.source_sha256}\``)
  lines.push(`- Canonical factory SHA-256: \`${data.provenance.canonical_factory_to_string_sha256}\``)
  lines.push(`- Node reference engine used to freeze this file: \`${data.provenance.node}\``)
  lines.push('- All Float32 hashes are explicitly serialized little-endian lane by lane; RGBA8 hashes use their natural byte order.')
  lines.push('- The generator pins the canonical/public/adapter/runtime files, factory body, source body, exact factory identity, and absence of an adapter override. `--check` verifies JSON, report, and all SHA-256 sidecars byte-for-byte.')
  return `${lines.join('\n')}\n`
}

function sidecarText(filePath, content) {
  return `${sha256(content)}  ${path.basename(filePath)}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = makeReport(data)
const artifacts = [
  [outputPath, json],
  [reportPath, report],
]
const sidecars = [
  [`${outputPath}.sha256`, sidecarText(outputPath, json)],
  [`${reportPath}.sha256`, sidecarText(reportPath, report)],
  [`${generatorPath}.sha256`, sidecarText(generatorPath, fs.readFileSync(generatorPath))],
]

if (process.argv.includes('--check')) {
  for (const [filePath, expected] of [...artifacts, ...sidecars]) {
    if (!fs.existsSync(filePath) || fs.readFileSync(filePath, 'utf8') !== expected) throw new Error(`stats parity artifact drift: ${path.basename(filePath)}`)
  }
  console.log(`stats parity oracle ok (${data.cases.length} cases, ${data.mutations.length} mutations, ${data.contract_negatives.length} contract negatives)`)
} else {
  for (const [filePath, content] of artifacts) fs.writeFileSync(filePath, content)
  for (const [filePath, content] of sidecars) fs.writeFileSync(filePath, content)
  for (const [filePath] of [...artifacts, ...sidecars]) console.log(filePath)
}
