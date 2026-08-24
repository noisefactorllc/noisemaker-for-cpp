import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  canonicalAdapterFactories,
  canonicalKernelFactories,
  kernelFactories,
} from '../../../../../noisemaker-for-cpu/src/effects/catalog.js'
import { effectRecords, UPSTREAM_REVISION } from '../../../../../noisemaker-for-cpu/src/effects/generated/upstream-snapshot.js'
import { createCanonicalBindings } from '../../../../../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel, GlslCpuRuntime } from '../../../../../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../../../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../../../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const platformRoot = path.resolve(here, '../../../../..')
const cppRoot = path.join(platformRoot, 'noisemaker-for-cpp')
const cpuRoot = path.join(platformRoot, 'noisemaker-for-cpu')
const outputPath = path.join(here, 'scanline-error-parity-oracles.json')
const reportPath = path.join(here, 'scanline-error-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'scanline_error_frontend_probe.py')
const programKey = 'filter/scanlineError:scanlineError'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/scanlineError/scanlineError.glsl')
const f = Math.fround

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(view) {
  return Buffer.from(view.buffer, view.byteOffset, view.byteLength)
}

function u32Hex(value) {
  return `0x${(value >>> 0).toString(16).padStart(8, '0')}`
}

function f32Bits(value) {
  const lane = new Float32Array([value])
  return u32Hex(new DataView(lane.buffer).getUint32(0, true))
}

// Purpose-built comparer for Scanline Error parity. Equality is raw Float32
// bit equality, including signed zero and NaN payloads. Diagnostics are
// additive: exact bytes and their SHA-256 hashes remain the contract.
function compareFloat32Surfaces(reference, candidate) {
  if (!(reference?.data instanceof Float32Array) || !(candidate?.data instanceof Float32Array)) {
    throw new TypeError('compareFloat32Surfaces requires two Float32 Surface values')
  }
  if (reference.width !== candidate.width || reference.height !== candidate.height || reference.data.length !== candidate.data.length) {
    return {
      exact_f32_bits: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_lanes: Math.max(reference.data.length, candidate.data.length),
      first_mismatch: null,
      max_absolute_difference: null,
    }
  }
  const left = new Uint32Array(reference.data.buffer, reference.data.byteOffset, reference.data.length)
  const right = new Uint32Array(candidate.data.buffer, candidate.data.byteOffset, candidate.data.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] === right[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        lane_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_value: Number.isFinite(reference.data[i]) ? reference.data[i] : String(reference.data[i]),
        candidate_value: Number.isFinite(candidate.data[i]) ? candidate.data[i] : String(candidate.data[i]),
        reference_bits_le: u32Hex(left[i]),
        candidate_bits_le: u32Hex(right[i]),
      }
    }
    const difference = Math.abs(reference.data[i] - candidate.data[i])
    if (Number.isFinite(difference)) maxAbsoluteDifference = Math.max(maxAbsoluteDifference, difference)
  }
  return {
    exact_f32_bits: mismatched === 0,
    dimensions_match: true,
    reference_dimensions: [reference.width, reference.height],
    candidate_dimensions: [candidate.width, candidate.height],
    mismatched_lanes: mismatched,
    first_mismatch: first,
    max_absolute_difference: maxAbsoluteDifference,
  }
}

function compareRgba8Surfaces(reference, candidate) {
  const left = reference.toRgba8()
  const right = candidate.toRgba8()
  if (reference.width !== candidate.width || reference.height !== candidate.height || left.length !== right.length) {
    return {
      exact_rgba8_bytes: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_bytes: Math.max(left.length, right.length),
      first_mismatch: null,
    }
  }
  let mismatched = 0
  let first = null
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] === right[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        byte_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_byte: left[i],
        candidate_byte: right[i],
      }
    }
  }
  return {
    exact_rgba8_bytes: mismatched === 0,
    dimensions_match: true,
    reference_dimensions: [reference.width, reference.height],
    candidate_dimensions: [candidate.width, candidate.height],
    mismatched_bytes: mismatched,
    first_mismatch: first,
  }
}

function compareSurfaces(reference, candidate) {
  return {
    float32: compareFloat32Surfaces(reference, candidate),
    rgba8: compareRgba8Surfaces(reference, candidate),
    candidate_f32_sha256: sha256(bytes(candidate.data)),
    candidate_rgba8_sha256: sha256(bytes(candidate.toRgba8())),
  }
}

function compareU32Words(reference, candidate) {
  if (!(reference instanceof Uint32Array) || !(candidate instanceof Uint32Array)) {
    throw new TypeError('compareU32Words requires Uint32Array values')
  }
  const length = Math.max(reference.length, candidate.length)
  let mismatched = reference.length === candidate.length ? 0 : Math.abs(reference.length - candidate.length)
  let first = reference.length === candidate.length ? null : { index: Math.min(reference.length, candidate.length), reference: null, candidate: null }
  for (let i = 0; i < Math.min(reference.length, candidate.length); i += 1) {
    if (reference[i] === candidate[i]) continue
    mismatched += 1
    if (first === null) first = { index: i, reference: u32Hex(reference[i]), candidate: u32Hex(candidate[i]) }
  }
  return { exact_u32_words: mismatched === 0, compared_words: length, mismatched_words: mismatched, first_mismatch: first }
}

function comparerSelfTests() {
  const shared = new Float32Array(8)
  const oneByTwo = new Surface(1, 2, shared.slice())
  const twoByOne = new Surface(2, 1, shared.slice())
  const mismatch = compareSurfaces(oneByTwo, twoByOne)
  if (mismatch.float32.exact_f32_bits || mismatch.rgba8.exact_rgba8_bytes ||
      mismatch.float32.dimensions_match || mismatch.rgba8.dimensions_match) {
    throw new Error('custom comparer accepted equal-length surfaces with different dimensions')
  }
  return {
    equal_length_dimension_mismatch_rejected_by_float32: !mismatch.float32.exact_f32_bits,
    equal_length_dimension_mismatch_rejected_by_rgba8: !mismatch.rgba8.exact_rgba8_bytes,
  }
}

const provenanceFiles = {
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  adapter_index: ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
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
if (sourceBytes.length !== 13302 || sha256(sourceBytes) !== '66556b29659b479edd397f8e0c87c176cafa7560c426eab8211b6939a08f2198') {
  throw new Error('pinned Scanline Error GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')
if ((sourceText.match(/floatBitsToUint\(/g) ?? []).length !== 3) throw new Error('GLSL floatBitsToUint census drift')

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory129') throw new Error('canonical Scanline Error factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 17646 || sha256(canonicalFactory.toString()) !== 'ea129bebd5933e5bafa69b5906d79622118f1a243137afc365eb775f09f7447f') {
  throw new Error('canonical Scanline Error factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog Scanline Error factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Scanline Error adapter override')

const expectedParams = {
  mode: { type: 'int', default: 1, uniform: 'mode', choices: { scanline: 0, vhs: 1 } },
  timeOffset: { type: 'float', default: 0, uniform: 'timeOffset', min: -10, max: 10 },
  distortion: { type: 'float', default: 1, uniform: 'distortion', min: 0, max: 3 },
  noise: { type: 'float', default: 1, uniform: 'noise', min: 0, max: 3 },
  speed: { type: 'float', default: 1, uniform: 'speed', min: 0, max: 5 },
}
const effect = effectRecords.find((record) => record.id === 'filter/scanlineError')
if (!effect) throw new Error('Scanline Error metadata missing')
for (const [name, expected] of Object.entries(expectedParams)) {
  if (JSON.stringify(effect.params?.[name]) !== JSON.stringify(expected)) throw new Error(`Scanline Error ${name} metadata drift`)
}
if (effect.func !== 'scanlineError' || effect.kind !== 'filter' || effect.namespace !== 'filter' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'scanlineError') {
  throw new Error('Scanline Error effect/pass interface drift')
}

const frontendProcess = spawnSync('python3', [frontendProbePath], { cwd: cppRoot, encoding: 'utf8' })
if (frontendProcess.status !== 0) throw new Error(`frontend proof failed: ${frontendProcess.stderr || frontendProcess.stdout}`)
const frontendProof = JSON.parse(frontendProcess.stdout)
if (frontendProof.nodes?.length !== 3 || frontendProof.current_frontier?.diagnostic_bypass?.validator !== 'pass' || frontendProof.current_frontier?.diagnostic_bypass?.emitter !== 'pass') {
  throw new Error('frontend proof contract drift')
}

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = f((((31 * x + 17 * y + 19 * phase + 3) % 101) + 1) / 103)
      data[i + 1] = f((((13 * x + 43 * y + 23 * phase + 5) % 97) + 2) / 101)
      data[i + 2] = f((((47 * x + 7 * y + 29 * phase + 11) % 89) + 3) / 97)
      data[i + 3] = f((((5 * x + 19 * y + 7 * phase) % 31) + 5) / 41)
    }
  }
  data[0] = -0
  if (data.length >= 12) data[9] = f(-0.25)
  if (data.length >= 20) data[18] = f(1.25)
  return new Surface(width, height, data)
}

const cases = [
  { name: 'scanline-zero-controls', width: 5, height: 4, phase: 1, mode: 0, speed: 0, timeOffset: 0, distortion: 0, noise: 0, time: 0, seed: 0, frame: 0, renderScale: 1, coverage: ['scanline branch', 'zero controls', 'signed-zero input lane', 'post-sample clamp remains observable'] },
  { name: 'scanline-default-still', width: 7, height: 5, phase: 2, mode: 0, speed: 1, timeOffset: 0, distortion: 1, noise: 1, time: 0, seed: 1, frame: 0, renderScale: 1, coverage: ['scanline branch', 'default controls', 'landscape'] },
  { name: 'vhs-default-still', width: 7, height: 5, phase: 3, mode: 1, speed: 1, timeOffset: 0, distortion: 1, noise: 1, time: 0, seed: 0, frame: 0, renderScale: 1, coverage: ['VHS branch', 'three floatBitsToUint sites reachable', 'default controls'] },
  { name: 'vhs-default-extreme-seed-frame', width: 7, height: 5, phase: 3, mode: 1, speed: 1, timeOffset: 0, distortion: 1, noise: 1, time: 0, seed: 4294967295, frame: 4294967295, renderScale: 1, sameAs: 'vhs-default-still', coverage: ['external seed/frame are unused', 'large unsigned inputs'] },
  { name: 'scanline-animated-max-controls', width: 8, height: 6, phase: 4, mode: 0, speed: 5, timeOffset: -10, distortion: 3, noise: 3, time: 0.375, seed: 2147483648, frame: 17, renderScale: 1, coverage: ['scanline animated branch', 'metadata extrema', 'high-bit seed'] },
  { name: 'vhs-animated-max-controls', width: 8, height: 6, phase: 5, mode: 1, speed: 5, timeOffset: 10, distortion: 3, noise: 3, time: 0.375, seed: 2147483648, frame: 17, renderScale: 1, coverage: ['VHS animated branch', 'metadata extrema', 'live bit ingress'] },
  { name: 'vhs-signed-zero-controls', width: 6, height: 4, phase: 6, mode: 1, speed: -0, timeOffset: -0, distortion: 0, noise: 0, time: -0, seed: 1, frame: 1, renderScale: 1, coverage: ['negative zero materialization', 'VHS zero displacement/blend controls'] },
  { name: 'vhs-large-time-offset-ulp', width: 6, height: 5, phase: 7, mode: 1, speed: 1, timeOffset: 1, distortion: 2, noise: 2, time: 16777216, seed: 16777217, frame: 9007199254740991, renderScale: 1, coverage: ['large Float32 time', 'post-binding JS addition', 'large frame'] },
  { name: 'scanline-tiled-noninteger-scale', width: 4, height: 3, phase: 8, mode: 0, speed: 2, timeOffset: -0.25, distortion: 2, noise: 1.5, time: 0.625, seed: 123456789, frame: 9, renderScale: 1.5, tileOffset: [3, 2], fullResolution: [11, 7], coverage: ['tile offset', 'full resolution', 'noninteger renderScale', 'scanline branch'] },
  { name: 'vhs-tiled-noninteger-scale', width: 4, height: 3, phase: 9, mode: 1, speed: 2, timeOffset: 0.25, distortion: 2, noise: 1.5, time: 0.625, seed: 123456789, frame: 9, renderScale: 1.5, tileOffset: [3, 2], fullResolution: [11, 7], coverage: ['tile offset', 'full resolution', 'noninteger renderScale', 'VHS bit ingress'] },
]

function compileMutant(name, from, to) {
  const source = canonicalFactory.toString()
  const pieces = source.split(from)
  if (pieces.length !== 2) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
  const mutatedText = `${pieces[0]}${to}${pieces[1]}`
  const factory = Function(`"use strict"; return (${mutatedText});`)()
  return { name, factory, factory_sha256: sha256(mutatedText), anchor_sha256: sha256(from), replacement_sha256: sha256(to) }
}

const renderMutants = [
  compileMutant('lane-x-bitcast-replaced-by-numeric-conversion', 'floatBitsToUint(p[0])', 'cpu_float(p[0])'),
  compileMutant('lane-y-bitcast-replaced-by-numeric-conversion', 'floatBitsToUint(p[1])', 'cpu_float(p[1])'),
  compileMutant('lane-z-bitcast-replaced-by-numeric-conversion', 'floatBitsToUint(p[2])', 'cpu_float(p[2])'),
  compileMutant('pcg-output-lane-x-replaced-by-y', 'pcg(seed)[0]', 'pcg(seed)[1]'),
  compileMutant('time-offset-ignored', 'var time_value = time + timeOffset;', 'var time_value = time;'),
  compileMutant('mode-branches-inverted', 'if (m == 1) {', 'if (m != 1) {'),
  compileMutant('global-tile-offset-ignored', 'new $runtime.PooledFloat32Array([(gid[0]) + tileOffset[0], (gid[1]) + tileOffset[1]])', 'new $runtime.PooledFloat32Array([(gid[0]), (gid[1])])'),
]

function render(factory, definition) {
  const input = patternedSurface(definition.width, definition.height, definition.phase)
  const before = input.data.slice()
  const uniforms = {
    mode: f(definition.mode),
    speed: f(definition.speed),
    timeOffset: f(definition.timeOffset),
    distortion: f(definition.distortion),
    noise: f(definition.noise),
    renderScale: f(definition.renderScale),
  }
  const tileOffset = definition.tileOffset ? new Float32Array(definition.tileOffset.map(f)) : undefined
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution.map(f)) : undefined
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: definition.frame,
    seed: definition.seed,
    uniforms,
    textures: { inputTex: input },
    tileOffset,
    fullResolution,
  })
  for (const name of ['mode', 'speed', 'timeOffset', 'distortion', 'noise', 'renderScale']) {
    if (f32Bits(bindings[name]) !== f32Bits(uniforms[name])) throw new Error(`${definition.name}: ${name} materialization drift`)
  }
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.seed })
  const after = input.data.slice()
  const immutable = compareU32Words(
    new Uint32Array(before.buffer, before.byteOffset, before.length),
    new Uint32Array(after.buffer, after.byteOffset, after.length),
  )
  if (!immutable.exact_u32_words) throw new Error(`${definition.name}: input texture mutated`)
  return { output, inputBefore: before, inputAfter: after, immutable, bindings }
}

function selectedProbes(surface) {
  const points = [
    ['top-left', 0, 0],
    ['top-right', surface.width - 1, 0],
    ['bottom-left', 0, surface.height - 1],
    ['bottom-right', surface.width - 1, surface.height - 1],
    ['center', Math.floor(surface.width / 2), Math.floor(surface.height / 2)],
  ]
  return points.map(([label, x, y]) => {
    const offset = (y * surface.width + x) * 4
    const values = Array.from(surface.data.slice(offset, offset + 4))
    return { label, at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
  })
}

function outputRecord(surface) {
  let finite = 0
  for (const value of surface.data) if (Number.isFinite(value)) finite += 1
  if (finite !== surface.data.length) throw new Error('nonfinite Scanline Error output from finite legal controls')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: finite,
    nonfinite_lanes: surface.data.length - finite,
    probes: selectedProbes(surface),
  }
}

const directInputWords = [
  0x00000000, 0x80000000, 0x00000001, 0x007fffff,
  0x00800000, 0x3f000000, 0x3f800000, 0xbf800000,
  0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
  0x7fc00001, 0x7fa00001, 0x7fffffff,
]

function buildDirectConversionEvidence() {
  const runtime = new GlslCpuRuntime()
  const records = directInputWords.map((inputWord) => {
    const raw = new Uint32Array([inputWord >>> 0])
    const value = new Float32Array(raw.buffer)[0]
    const actual = runtime.stdlib.floatBitsToUint(value) >>> 0
    const independentBuffer = new ArrayBuffer(4)
    const independentView = new DataView(independentBuffer)
    independentView.setFloat32(0, value, true)
    const independent = independentView.getUint32(0, true)
    if (actual !== independent) throw new Error(`direct floatBitsToUint disagreement for ${u32Hex(inputWord)}`)
    const exponent = (inputWord >>> 23) & 0xff
    const fraction = inputWord & 0x7fffff
    const signalingNan = exponent === 0xff && fraction !== 0 && (fraction & 0x400000) === 0
    return {
      source_word_le: u32Hex(inputWord),
      classification: Number.isNaN(value) ? 'nan' : !Number.isFinite(value) ? (value < 0 ? '-infinity' : '+infinity') : Object.is(value, -0) ? '-zero' : value === 0 ? '+zero' : 'finite',
      materialized_value: Number.isFinite(value) ? value : String(value),
      runtime_word_le: u32Hex(actual),
      independent_dataview_word_le: u32Hex(independent),
      source_word_preserved: actual === (inputWord >>> 0),
      native_parity_required: !signalingNan,
      note: actual !== (inputWord >>> 0) ? 'JavaScript quieted a signaling NaN while materializing the Number; runtime and independent DataView agree on the observable word.' : null,
    }
  })
  const canonicalAll = new Uint32Array(records.map((record) => Number.parseInt(record.runtime_word_le.slice(2), 16)))
  const requiredIndices = records.flatMap((record, index) => record.native_parity_required ? [index] : [])
  const canonical = new Uint32Array(requiredIndices.map((index) => canonicalAll[index]))
  const mutationDefinitions = [
    ['numeric-conversion', 13, (value) => value >>> 0],
    ['erase-negative-zero', 1, (value, word) => Object.is(value, -0) ? 0 : word],
    ['nonfinite-to-zero', 4, (value, word) => Number.isFinite(value) ? word : 0],
    ['float64-low-word', 13, (value) => {
      const storage = new ArrayBuffer(8)
      const view = new DataView(storage)
      view.setFloat64(0, value, true)
      return view.getUint32(0, true)
    }],
  ]
  const mutations = mutationDefinitions.map(([name, expectedMismatches, mutate]) => {
    const candidate = new Uint32Array(requiredIndices.map((index) => {
      const raw = new Uint32Array([directInputWords[index] >>> 0])
      const value = new Float32Array(raw.buffer)[0]
      return mutate(value, canonicalAll[index]) >>> 0
    }))
    const comparison = compareU32Words(canonical, candidate)
    if (comparison.exact_u32_words) throw new Error(`${name}: direct conversion mutation escaped`)
    if (comparison.mismatched_words !== expectedMismatches) throw new Error(`${name}: expected ${expectedMismatches} mismatches, got ${comparison.mismatched_words}`)
    return { name, expected_mismatched_words: expectedMismatches, exact_comparer_discriminated: true, comparison }
  })
  return {
    records,
    native_parity_required_records: records.filter((record) => record.native_parity_required).length,
    aggregate_all_observed_u32_le_sha256: sha256(bytes(canonicalAll)),
    aggregate_runtime_u32_le_sha256: sha256(bytes(canonical)),
    signaling_nan_policy: 'Diagnostic only: JavaScript Number materialization quiets the one signaling-NaN source word. The existing C++ std::bit_cast helper correctly preserves raw float bits and must not be changed; reachable Scanline Error arithmetic cannot produce a signaling NaN.',
    mutations,
  }
}

function buildData() {
  const renderedByName = new Map()
  const caseResults = cases.map((definition) => {
    const canonicalFirst = render(canonicalFactory, definition)
    const canonicalSecond = render(canonicalFactory, definition)
    const repeat = compareSurfaces(canonicalFirst.output, canonicalSecond.output)
    if (!repeat.float32.exact_f32_bits || !repeat.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: repeat mismatch`)
    const publicResult = render(publicFactory, definition)
    const publicComparison = compareSurfaces(canonicalFirst.output, publicResult.output)
    if (!publicComparison.float32.exact_f32_bits || !publicComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: public/direct mismatch`)
    renderedByName.set(definition.name, canonicalFirst.output)

    const mutationComparisons = {}
    for (const mutant of renderMutants) mutationComparisons[mutant.name] = compareSurfaces(canonicalFirst.output, render(mutant.factory, definition).output)
    const beforeBits = new Uint32Array(canonicalFirst.inputBefore.buffer, canonicalFirst.inputBefore.byteOffset, canonicalFirst.inputBefore.length)
    const afterBits = new Uint32Array(canonicalFirst.inputAfter.buffer, canonicalFirst.inputAfter.byteOffset, canonicalFirst.inputAfter.length)
    const record = {
      name: definition.name,
      dimensions: { width: definition.width, height: definition.height },
      controls: {
        mode: f(definition.mode), speed: f(definition.speed), time_offset: f(definition.timeOffset),
        distortion: f(definition.distortion), noise: f(definition.noise), time: f(definition.time),
        time_bits_le: f32Bits(definition.time), external_seed_input: definition.seed,
        uniform_f32_bits_le: {
          mode: f32Bits(definition.mode), speed: f32Bits(definition.speed),
          time_offset: f32Bits(definition.timeOffset), distortion: f32Bits(definition.distortion),
          noise: f32Bits(definition.noise), render_scale: f32Bits(definition.renderScale),
        },
        external_seed_materialized_f32: canonicalFirst.bindings.seed,
        external_seed_materialized_f32_bits_le: f32Bits(canonicalFirst.bindings.seed),
        frame: definition.frame, render_scale: f(definition.renderScale),
        tile_offset: Array.from(canonicalFirst.bindings.tileOffset),
        full_resolution: Array.from(canonicalFirst.bindings.fullResolution),
      },
      coverage: definition.coverage,
      input: {
        f32_sha256_before: sha256(bytes(canonicalFirst.inputBefore)),
        f32_sha256_after: sha256(bytes(canonicalFirst.inputAfter)),
        immutable_exact_bits: compareU32Words(beforeBits, afterBits),
        probes: selectedProbes(new Surface(definition.width, definition.height, canonicalFirst.inputBefore)),
      },
      output: outputRecord(canonicalFirst.output),
      repeat_identity: repeat,
      public_catalog_vs_direct_canonical: publicComparison,
      mutation_comparisons: mutationComparisons,
    }
    return record
  })

  for (const definition of cases) {
    if (!definition.sameAs) continue
    const equality = compareSurfaces(renderedByName.get(definition.sameAs), renderedByName.get(definition.name))
    if (!equality.float32.exact_f32_bits || !equality.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: identity with ${definition.sameAs} failed`)
    caseResults.find((item) => item.name === definition.name).declared_identity = { reference_case: definition.sameAs, comparison: equality }
  }

  const requiredMutations = {
    'lane-x-bitcast-replaced-by-numeric-conversion': ['vhs-default-still'],
    'lane-y-bitcast-replaced-by-numeric-conversion': ['vhs-default-still'],
    'lane-z-bitcast-replaced-by-numeric-conversion': ['vhs-default-still'],
    'pcg-output-lane-x-replaced-by-y': ['vhs-default-still'],
    'time-offset-ignored': ['scanline-animated-max-controls', 'vhs-animated-max-controls'],
    'mode-branches-inverted': ['scanline-default-still', 'vhs-default-still'],
    'global-tile-offset-ignored': ['scanline-tiled-noninteger-scale', 'vhs-tiled-noninteger-scale'],
  }
  const renderMutationSummary = renderMutants.map((mutant) => {
    const witnesses = caseResults.filter((record) => !record.mutation_comparisons[mutant.name].float32.exact_f32_bits).map((record) => record.name)
    for (const required of requiredMutations[mutant.name]) {
      if (!witnesses.includes(required)) throw new Error(`${mutant.name}: required witness ${required} did not diverge`)
    }
    return {
      name: mutant.name,
      factory_sha256: mutant.factory_sha256,
      anchor_sha256: mutant.anchor_sha256,
      replacement_sha256: mutant.replacement_sha256,
      required_witnesses: requiredMutations[mutant.name],
      all_divergent_cases: witnesses,
      exact_comparer_discriminated: witnesses.length > 0,
    }
  })

  return {
    schema: 'noisemaker-for-cpp.scanline-error.pixel-parity-and-float-bits-oracle.v1',
    program_key: programKey,
    corpus_revision: corpusRevision,
    upstream_revision: UPSTREAM_REVISION,
    provenance: {
      node: process.version,
      reference_api: 'canonicalKernelFactories[program_key] via bindGlslKernel and createCanonicalBindings',
      public_api: 'kernelFactories.get(program_key)',
      canonical_factory_name: canonicalFactory.name,
      canonical_factory_to_string_bytes: Buffer.byteLength(canonicalFactory.toString()),
      canonical_factory_to_string_sha256: sha256(canonicalFactory.toString()),
      source_raw_bytes: sourceBytes.length,
      source_sha256: sha256(sourceBytes),
      frontend_probe_path: path.relative(cppRoot, frontendProbePath),
      frontend_probe_sha256: sha256(fs.readFileSync(frontendProbePath)),
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    frontend_proof: frontendProof,
    materialization_contract: {
      float_bits_to_uint: 'Shipped GlslCpuRuntime writes the JavaScript Number into a shared Float32Array and reads the aliased Uint32Array word.',
      signaling_nan: 'Diagnostic-only JavaScript boundary behavior: Number materialization quiets a signaling NaN. It is unreachable from Scanline Error arithmetic and does not override the existing C++ helper contract of preserving raw float bits.',
      f32_bindings: 'effect uniforms, time, seed, tileOffset, and fullResolution are Float32 materialized by createCanonicalBindings or explicit Float32Array construction',
      time_expression: 'time and timeOffset are individually Float32, then canonical generated JavaScript evaluates their addition as a Number local',
      external_seed_frame: 'the program declares neither external seed nor frame; both are intentionally absent from pixel behavior',
      texture_coordinates: 'GLSL fragment coordinates are bottom-left while Surface storage and comparer diagnostics are top-down',
    },
    metadata_contract: expectedParams,
    fixture: {
      input: 'asymmetric colored top-down Float32 RGBA with signed zero and finite out-of-range edge lanes',
      comparer: 'exact Float32-bit and RGBA8-byte custom comparer; hashes remain authoritative',
      repeated_render_count: 2,
    },
    comparer_self_tests: comparerSelfTests(),
    direct_float_bits_to_uint: buildDirectConversionEvidence(),
    cases: caseResults,
    render_mutation_summary: renderMutationSummary,
    contract_negatives: frontendProof.contract_negatives,
  }
}

function makeReport(data) {
  const lines = [
    '# Scanline Error float-bit ingress and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/scanlineError:scanlineError`. Exact Float32 and RGBA8 hashes cover both scanline and VHS paths, including live `floatBitsToUint` execution, tiling, time, and legal control extrema. A separate frontend probe freezes the three-node admission boundary and the captured pre-admission gate chain.', '',
    '## Frozen authority', '',
    `- Upstream snapshot revision: \`${data.upstream_revision}\``,
    `- Corpus revision: \`${data.corpus_revision}\``,
    `- GLSL source: ${data.provenance.source_raw_bytes} bytes, SHA-256 \`${data.provenance.source_sha256}\``,
    `- Canonical factory: \`${data.provenance.canonical_factory_name}\`, ${data.provenance.canonical_factory_to_string_bytes} bytes, SHA-256 \`${data.provenance.canonical_factory_to_string_sha256}\``,
    '- Public catalog identity is exactly the canonical factory; no adapter override exists.', '',
    '## Captured pre-admission C++ frontend boundary', '',
    `- Validator first error: \`${data.frontend_proof.current_frontier.validator_first_error}\``,
    `- Emitter first error: \`${data.frontend_proof.current_frontier.emitter_first_error}\``,
    '- Exactly three `floatBitsToUint(float) -> uint` nodes occur, all in reachable `hashNoise` and all direct children of one `uvec3` constructor.',
    `- Replacing only those three callees in memory exposed validator \`${data.frontend_proof.current_frontier.diagnostic_bypass.validator}\` and emitter \`${data.frontend_proof.current_frontier.diagnostic_bypass.emitter}\` in live typed slice 174; there was no later pre-admission frontend gate.`,
    '- Do not widen or reuse Caustic identity. Add a parallel exact Scanline Error profile, while reusing the existing `noisemaker::float_bits_to_uint` lowering and runtime helper. The global builtin/capability vocabulary remains unchanged; no scalar-XOR profile is needed.', '',
    '## Direct conversion fixtures', '',
    `The ${data.direct_float_bits_to_uint.records.length} raw-word fixtures cover signed zero, subnormals, normal finite values, Float32 extrema, infinities, and multiple NaN payloads. Shipped runtime and an independent little-endian DataView recomputation agree exactly. ${data.direct_float_bits_to_uint.native_parity_required_records} reachable/native-required records have aggregate words SHA-256 \`${data.direct_float_bits_to_uint.aggregate_runtime_u32_le_sha256}\`. The signaling-NaN row is diagnostic only: JavaScript quiets it at the Number boundary, while the existing C++ \`std::bit_cast\` helper correctly preserves raw bits and must not be changed; Scanline Error arithmetic cannot produce a signaling NaN.`, '',
    '## Render cases', '',
    '| Case | Size | Mode | Speed | Offset | Distortion | Noise | Time | Seed | Frame | Tile/full | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |',
  ]
  for (const record of data.cases) {
    const c = record.controls
    lines.push(`| ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${c.mode} | ${c.speed} | ${c.time_offset} | ${c.distortion} | ${c.noise} | ${c.time} | ${c.external_seed_input} | ${c.frame} | ${c.tile_offset.join(',')}/${c.full_resolution.join(',')} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every case requires exact repeated-render identity, exact input-bit immutability, finite output for finite legal controls, and direct-canonical/public-catalog equality. The paired extreme seed/frame case proves those external bindings are unused. Both tile cases require their offset mutation to diverge.', '')
  lines.push('## Mutation discrimination', '', '| Mutation | Required witnesses | All divergent cases |', '| --- | --- | --- |')
  for (const mutation of data.render_mutation_summary) lines.push(`| ${mutation.name} | ${mutation.required_witnesses.join(', ')} | ${mutation.all_divergent_cases.join(', ')} |`)
  lines.push('', 'The native-required direct conversion corpus separately rejects numeric conversion, erasing negative zero, replacing nonfinite bit patterns with zero, and reinterpreting Float64 storage. Frontend contract negatives reject wrong key/profile/hash, a removed site, a swapped child, and an added site.', '')
  lines.push('## Regeneration', '', 'From the repository root. The ordinary checks are durable after production admission; `--live-frontier` is an optional diagnostic that observes the then-current gate without rewriting the frozen live174 evidence:', '', '```sh', 'python3 docs/port-engineering/bitops/scanline-error-parity/scanline_error_frontend_probe.py --check', 'python3 docs/port-engineering/bitops/scanline-error-parity/scanline_error_frontend_probe.py --live-frontier', 'node docs/port-engineering/bitops/scanline-error-parity/scanline_error_parity_oracle_generator.mjs', 'node docs/port-engineering/bitops/scanline-error-parity/scanline_error_parity_oracle_generator.mjs --check', '```', '')
  return `${lines.join('\n')}\n`
}

function sidecar(hash, filePath) {
  return `${hash}  ${path.basename(filePath)}\n`
}

function checkExact(filePath, expected, label) {
  if (!fs.existsSync(filePath) || fs.readFileSync(filePath, 'utf8') !== expected) throw new Error(`${label} drift`)
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = makeReport(data)
const jsonSidecar = sidecar(sha256(json), outputPath)
const reportSidecar = sidecar(sha256(report), reportPath)
const generatorSidecar = sidecar(sha256(fs.readFileSync(generatorPath)), generatorPath)
const probeSidecar = sidecar(sha256(fs.readFileSync(frontendProbePath)), frontendProbePath)

if (process.argv.includes('--check')) {
  checkExact(outputPath, json, 'Scanline Error parity JSON')
  checkExact(reportPath, report, 'Scanline Error parity report')
  checkExact(`${outputPath}.sha256`, jsonSidecar, 'Scanline Error parity JSON sidecar')
  checkExact(`${reportPath}.sha256`, reportSidecar, 'Scanline Error parity report sidecar')
  checkExact(`${generatorPath}.sha256`, generatorSidecar, 'Scanline Error generator sidecar')
  checkExact(`${frontendProbePath}.sha256`, probeSidecar, 'Scanline Error frontend probe sidecar')
  console.log(`Scanline Error parity oracle ok (${data.cases.length} render cases, ${data.direct_float_bits_to_uint.records.length} direct conversion fixtures, ${data.render_mutation_summary.length + data.direct_float_bits_to_uint.mutations.length} mutations)`)
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  fs.writeFileSync(`${outputPath}.sha256`, jsonSidecar)
  fs.writeFileSync(`${reportPath}.sha256`, reportSidecar)
  fs.writeFileSync(`${generatorPath}.sha256`, generatorSidecar)
  fs.writeFileSync(`${frontendProbePath}.sha256`, probeSidecar)
  console.log(outputPath)
  console.log(reportPath)
}
