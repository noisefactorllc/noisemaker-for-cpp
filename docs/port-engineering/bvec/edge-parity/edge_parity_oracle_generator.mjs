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
const outputPath = path.join(here, 'edge-parity-oracles.json')
const reportPath = path.join(here, 'edge-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'edge_frontend_probe.py')
const programKey = 'filter/edge:edge'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/edge/edge.glsl')
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

// Purpose-built Edge comparer. Float32 equality is raw lane-bit equality,
// including signed zero and NaN payloads. RGBA8 is a second exact contract,
// never a replacement for Float32 parity.
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
  if (reference.width !== candidate.width || reference.height !== candidate.height) {
    return {
      exact_rgba8_bytes: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_bytes: Math.max(reference.data.length, candidate.data.length),
      first_mismatch: null,
    }
  }
  const left = reference.toRgba8()
  const right = candidate.toRgba8()
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
  return { exact_rgba8_bytes: mismatched === 0, dimensions_match: true, mismatched_bytes: mismatched, first_mismatch: first }
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
  if (reference.length !== candidate.length) {
    return { exact_u32_words: false, mismatched_words: Math.max(reference.length, candidate.length), first_mismatch: null }
  }
  let mismatched = 0
  let first = null
  for (let i = 0; i < reference.length; i += 1) {
    if (reference[i] === candidate[i]) continue
    mismatched += 1
    if (first === null) first = { index: i, reference: u32Hex(reference[i]), candidate: u32Hex(candidate[i]) }
  }
  return { exact_u32_words: mismatched === 0, mismatched_words: mismatched, first_mismatch: first }
}

function comparerSelfTests() {
  const oneByTwo = new Surface(1, 2, new Float32Array(8))
  const twoByOne = new Surface(2, 1, new Float32Array(8))
  const dimensions = compareSurfaces(oneByTwo, twoByOne)
  if (dimensions.float32.exact_f32_bits || dimensions.rgba8.exact_rgba8_bytes) throw new Error('custom comparer accepted dimension mismatch')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareSurfaces(plusZero, minusZero)
  if (signedZero.float32.exact_f32_bits || !signedZero.rgba8.exact_rgba8_bytes || signedZero.float32.first_mismatch?.channel !== 'r') {
    throw new Error('custom comparer did not expose signed-zero Float32 difference')
  }
  return {
    equal_length_dimension_mismatch_rejected: true,
    signed_zero_float32_mismatch_rejected: true,
    rgba8_quantization_does_not_replace_float32_contract: true,
    signed_zero_first_mismatch: signedZero.float32.first_mismatch,
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
if (sourceBytes.length !== 6530 || sha256(sourceBytes) !== '841f9f547d06aace8444953f401009abd02758f9dff271097b2799424c1db5d0') throw new Error('pinned Edge GLSL source drift')
const sourceText = sourceBytes.toString('utf8')
if ((sourceText.match(/bvec3/g) ?? []).length !== 3 || (sourceText.match(/greaterThanEqual/g) ?? []).length !== 1 || (sourceText.match(/lessThan\(/g) ?? []).length !== 1) {
  throw new Error('Edge bvec3 source census drift')
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory49') throw new Error('canonical Edge factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 9011 || sha256(canonicalFactory.toString()) !== '57375f0b17f6b90c541fc264b4e5233674eef6e6a496307e6a047138db1a2bb8') {
  throw new Error('canonical Edge factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public Edge factory is not canonical identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Edge adapter override')

const expectedParams = {
  kernel: { type: 'int', default: 1, uniform: 'kernel', choices: { fine: 0, bold: 1, contour: 2 } },
  level: { type: 'float', default: 50, uniform: 'level', min: 0, max: 100 },
  contourSide: { type: 'int', default: 0, uniform: 'contourSide', choices: { lower: 0, upper: 1 } },
  size: { type: 'int', default: 1, uniform: 'size', choices: { kernel5x5: 1, kernel7x7: 2 } },
  channel: { type: 'int', default: 0, uniform: 'channel', choices: { color: 0, luminance: 1 } },
  amount: { type: 'float', default: 100, uniform: 'amount', min: 0, max: 500 },
  invert: { type: 'int', default: 0, uniform: 'invert', choices: { off: 0, on: 1 } },
  threshold: { type: 'float', default: 0, uniform: 'threshold', min: 0, max: 100 },
  blend: { type: 'int', default: 6, uniform: 'blend', choices: { add: 0, darken: 1, difference: 2, dodge: 3, lighten: 4, multiply: 5, normal: 6, overlay: 7, screen: 8 } },
  mix: { type: 'float', default: 100, uniform: 'mixAmt', min: 0, max: 100 },
}
const effect = effectRecords.find((record) => record.id === 'filter/edge')
if (!effect) throw new Error('Edge metadata missing')
for (const [name, expected] of Object.entries(expectedParams)) {
  for (const [field, value] of Object.entries(expected)) {
    if (JSON.stringify(effect.params?.[name]?.[field]) !== JSON.stringify(value)) throw new Error(`Edge ${name}.${field} metadata drift`)
  }
}
if (effect.func !== 'edge' || effect.kind !== 'filter' || effect.namespace !== 'filter' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'edge') throw new Error('Edge effect/pass interface drift')

const frontendProcess = spawnSync('python3', [frontendProbePath], { cwd: cppRoot, encoding: 'utf8' })
if (frontendProcess.status !== 0) throw new Error(`frontend proof failed: ${frontendProcess.stderr || frontendProcess.stdout}`)
const frontendProof = JSON.parse(frontendProcess.stdout)
if (frontendProof.bvec3_nodes?.length !== 12 || frontendProof.bvec3_swizzles?.length !== 6 || frontendProof.captured_pre_admission_frontier?.diagnostic_bypass?.validator !== 'pass' || frontendProof.captured_pre_admission_frontier?.diagnostic_bypass?.emitter !== 'pass' || frontendProof.current_profile_frontier?.profile_admission?.validator !== 'pass' || frontendProof.current_profile_frontier?.profile_admission?.emitter !== 'pass') {
  throw new Error('Edge frontend proof contract drift')
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

function contourSurface(level57Witness = false) {
  const width = 7
  const height = 7
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = f(x / 6)
      data[i + 1] = f(y / 6)
      data[i + 2] = f(((3 * x + 5 * y + 1) % 11) / 10)
      data[i + 3] = f((x + y + 2) / 16)
    }
  }
  if (level57Witness) {
    // Center components equal canonical vec3(level/100), which is f32(0.57).
    // Cardinal neighbors straddle that value in every lane. This distinguishes
    // the shipped f32 broadcast from a wrong Vec3-vs-retained-double compare.
    const set = (x, y, rgba) => data.set(rgba.map(f), (y * width + x) * 4)
    const threshold = f(0.57)
    set(3, 3, [threshold, threshold, threshold, 0.75])
    set(3, 2, [0.56, 0.58, 0.55, 0.5])
    set(3, 4, [0.58, 0.56, 0.59, 0.5])
    set(2, 3, [0.55, 0.59, 0.58, 0.5])
    set(4, 3, [0.59, 0.55, 0.56, 0.5])
  }
  return new Surface(width, height, data)
}

function buildLevel57FixtureEvidence() {
  const surface = contourSurface(true)
  const rgbAt = (x, y) => Array.from(surface.data.slice((y * surface.width + x) * 4, (y * surface.width + x) * 4 + 3))
  const sourceThreshold = 57 / 100
  const materializedThreshold = f(sourceThreshold)
  const center = rgbAt(3, 3)
  const neighbors = [
    ['north-top-down', 3, 2],
    ['south-top-down', 3, 4],
    ['west', 2, 3],
    ['east', 4, 3],
  ].map(([name, x, y]) => ({ name, top_down_xy: [x, y], rgb: rgbAt(x, y) }))
  const lanes = ['r', 'g', 'b'].map((channel, index) => {
    const values = neighbors.map((item) => item.rgb[index])
    return {
      channel,
      center_equals_materialized_threshold: Object.is(center[index], materializedThreshold),
      has_neighbor_below_materialized_threshold: values.some((value) => value < materializedThreshold),
      has_neighbor_above_retained_double_threshold: values.some((value) => value > sourceThreshold),
    }
  })
  if (!(materializedThreshold < sourceThreshold) || lanes.some((lane) => !lane.center_equals_materialized_threshold || !lane.has_neighbor_below_materialized_threshold || !lane.has_neighbor_above_retained_double_threshold)) {
    throw new Error('level-57 Float32 broadcast fixture lost equality or mixed-neighbor discrimination')
  }
  return {
    source_level: 57,
    retained_double_threshold: sourceThreshold,
    retained_double_threshold_text: sourceThreshold.toPrecision(17),
    materialized_vec3_threshold_f32: materializedThreshold,
    materialized_vec3_threshold_f32_bits_le: f32Bits(materializedThreshold),
    center_top_down_xy: [3, 3],
    center_rgb: center,
    center_rgb_f32_bits_le: center.map(f32Bits),
    cardinal_neighbors: neighbors,
    per_lane_proof: lanes,
  }
}

const base = { size: 1, renderScale: 1, invert: 0, threshold: 0, amount: 100, mixAmt: 100, level: 50, contourSide: 0, time: 0, frame: 0, externalSeed: 0 }
const cases = [
  { name: 'fine-color-radius-two', width: 9, height: 7, phase: 1, ...base, kernel: 0, channel: 0, blend: 6, coverage: ['fine cross kernel', 'color convolution', 'radius two'] },
  { name: 'bold-color-radius-three', width: 9, height: 7, phase: 2, ...base, kernel: 1, channel: 0, blend: 6, size: 2, coverage: ['bold full kernel', 'color convolution', 'radius three'] },
  { name: 'fine-luma-threshold-invert', width: 8, height: 6, phase: 3, ...base, kernel: 0, channel: 1, blend: 2, threshold: 37, invert: 1, amount: 175, mixAmt: 63, coverage: ['luma convolution', 'threshold', 'invert', 'difference blend', 'partial mix'] },
  { name: 'radius-one-scale-zero', width: 6, height: 5, phase: 4, ...base, kernel: 1, channel: 0, blend: 6, renderScale: 0, coverage: ['int radius expression', 'minimum reachable radius one'] },
  { name: 'amount-zero-normal', width: 6, height: 5, phase: 5, ...base, kernel: 1, channel: 0, blend: 6, amount: 0, coverage: ['zero amount'] },
  { name: 'mix-zero-input-identity', width: 6, height: 5, phase: 6, ...base, kernel: 1, channel: 0, blend: 8, mixAmt: 0, coverage: ['zero mix', 'input identity'] },
  { name: 'contour-color-lower', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 0, level: 50, coverage: ['bvec3 lower relation', 'componentwise crossings', 'bvec3 constructor and lane reads'] },
  { name: 'contour-color-upper', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 1, level: 50, coverage: ['bvec3 upper relation', 'componentwise crossings'] },
  { name: 'contour-color-lower-level57-f32-equality', width: 7, height: 7, special: 'contour57', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 0, level: 57, coverage: ['lower strict equality at f32(level/100)', 'neighbors on both threshold sides', 'FloatExpr rhs must narrow through Vec3'] },
  { name: 'contour-color-upper-level57-f32-equality', width: 7, height: 7, special: 'contour57', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 1, level: 57, coverage: ['upper inclusive equality at f32(level/100)', 'neighbors on both threshold sides', 'FloatExpr rhs must narrow through Vec3'] },
  { name: 'contour-color-upper-level-zero', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 1, level: 0, coverage: ['upper equality boundary', 'level minimum'] },
  { name: 'contour-color-lower-level-hundred', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 0, blend: 6, contourSide: 0, level: 100, coverage: ['lower strict boundary', 'level maximum'] },
  { name: 'contour-luma-lower', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 1, blend: 6, contourSide: 0, level: 43, coverage: ['scalar luma lower contour', 'bvec3 branch skipped'] },
  { name: 'contour-luma-upper', width: 7, height: 7, special: 'contour', ...base, kernel: 2, channel: 1, blend: 6, contourSide: 1, level: 57, coverage: ['scalar luma upper contour', 'bvec3 branch skipped'] },
  ...Array.from({ length: 9 }, (_, blend) => ({
    name: `blend-${blend}`,
    width: 5,
    height: 4,
    phase: 10 + blend,
    ...base,
    kernel: blend % 2,
    channel: blend % 3 === 0 ? 1 : 0,
    blend,
    threshold: blend === 3 ? 22 : 0,
    amount: 80 + blend * 13,
    mixAmt: 71,
    coverage: [`blend mode ${blend}`, 'alpha preservation'],
  })),
  { name: 'external-context-base', width: 8, height: 5, phase: 30, ...base, kernel: 1, channel: 0, blend: 7, coverage: ['external context identity reference'] },
  { name: 'external-context-extreme', width: 8, height: 5, phase: 30, ...base, kernel: 1, channel: 0, blend: 7, time: 16777216, frame: 4294967295, externalSeed: 4294967295, sameAs: 'external-context-base', coverage: ['time/frame/pass seed unused'] },
]

function compileMutant(name, from, to) {
  const source = canonicalFactory.toString()
  const pieces = source.split(from)
  if (pieces.length !== 2) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
  const mutatedText = `${pieces[0]}${to}${pieces[1]}`
  return {
    name,
    factory: Function(`"use strict"; return (${mutatedText});`)(),
    factory_sha256: sha256(mutatedText),
    anchor_sha256: sha256(from),
    replacement_sha256: sha256(to),
  }
}

function compileMutantAll(name, from, to, expectedOccurrences) {
  const source = canonicalFactory.toString()
  const pieces = source.split(from)
  if (pieces.length !== expectedOccurrences + 1) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
  const mutatedText = pieces.join(to)
  return {
    name,
    factory: Function(`"use strict"; return (${mutatedText});`)(),
    factory_sha256: sha256(mutatedText),
    anchor_sha256: sha256(from),
    replacement_sha256: sha256(to),
  }
}

const renderMutants = [
  compileMutant('upper-relational-inverted', 'upperSide ? greaterThanEqual(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl])) : lessThan(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl]))', 'upperSide ? lessThan(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl])) : lessThan(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl]))'),
  compileMutant('lower-relational-inverted', 'upperSide ? greaterThanEqual(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl])) : lessThan(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl]))', 'upperSide ? greaterThanEqual(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl])) : greaterThanEqual(centerRGB, new $runtime.PooledFloat32Array([lvl, lvl, lvl]))'),
  compileMutant('red-center-side-read-from-green', 'centerOnSide[0] && (upperSide ?', 'centerOnSide[1] && (upperSide ?'),
  compileMutant('green-crossing-output-read-from-blue', 'crossing[1] ? 0 : 1', 'crossing[2] ? 0 : 1'),
  compileMutant('contour-side-forced-lower', 'useLuma, contourSide > 0.5)', 'useLuma, false)'),
  compileMutant('contour-level-divisor-changed', 'level / 100, useLuma', 'level / 99, useLuma'),
  compileMutantAll('contour-rhs-f32-broadcast-bypassed', 'new $runtime.PooledFloat32Array([lvl, lvl, lvl])', 'lvl', 2),
  compileMutant('contour-dispatch-disabled', 'if (kernelType == 2) {', 'if (kernelType == 3) {'),
  compileMutant('channel-branch-inverted', 'var useLuma = channel > 0.5;', 'var useLuma = channel <= 0.5;'),
  compileMutant(
    'center-self-splat-simultaneous',
    '(centerSample[0] = dot(centerSample, LUMA), centerSample[1] = dot(centerSample, LUMA), centerSample[2] = dot(centerSample, LUMA), centerSample)',
    '(centerSample.fill(dot(centerSample, LUMA)), centerSample)'),
]

function makeInput(definition) {
  if (definition.special === 'contour') return contourSurface()
  if (definition.special === 'contour57') return contourSurface(true)
  return patternedSurface(definition.width, definition.height, definition.phase)
}

function render(factory, definition) {
  const input = makeInput(definition)
  const before = input.data.slice()
  const uniforms = {
    kernel: definition.kernel,
    size: definition.size,
    renderScale: f(definition.renderScale),
    blend: definition.blend,
    invert: definition.invert,
    channel: definition.channel,
    threshold: f(definition.threshold),
    amount: f(definition.amount),
    mixAmt: f(definition.mixAmt),
    level: f(definition.level),
    contourSide: definition.contourSide,
  }
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: definition.frame,
    seed: definition.externalSeed,
    uniforms,
    textures: { inputTex: input },
  })
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.externalSeed })
  const after = input.data.slice()
  const immutable = compareU32Words(
    new Uint32Array(before.buffer, before.byteOffset, before.length),
    new Uint32Array(after.buffer, after.byteOffset, after.length),
  )
  if (!immutable.exact_u32_words) throw new Error(`${definition.name}: input mutated`)
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
  let nonfinite = 0
  for (const value of surface.data) if (!Number.isFinite(value)) nonfinite += 1
  if (nonfinite !== 0) throw new Error('nonfinite Edge output')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    probes: selectedProbes(surface),
  }
}

const directDefinitions = [
  ['all-below', [0, -1, 0.25], [0.5, 0.5, 0.5]],
  ['all-above', [1, 2, 0.75], [0.5, 0.5, 0.5]],
  ['mixed', [0.25, 0.5, 0.75], [0.5, 0.5, 0.5]],
  ['equal', [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]],
  ['signed-zero', [-0, 0, -0], [0, -0, 0]],
  ['infinities', [Number.NEGATIVE_INFINITY, Number.POSITIVE_INFINITY, 1], [0, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]],
  ['nan-left', [Number.NaN, 1, -1], [0, 0, 0]],
  ['nan-right', [0, 1, -1], [Number.NaN, Number.NaN, Number.NaN]],
  ['f32-neighbors', [f(0.49999997), f(0.5), f(0.50000006)], [f(0.5), f(0.5), f(0.5)]],
]

const floatExprRhsDefinitions = [
  ['level57-broadcast', 57 / 100],
  ['level70-broadcast', 70 / 100],
  ['level90-broadcast', 90 / 100],
]

function adjacentF32(value, direction) {
  if (!Number.isFinite(value)) throw new TypeError('adjacentF32 requires finite input')
  const lane = new Float32Array([value])
  if (Object.is(lane[0], -0)) lane[0] = 0
  const words = new Uint32Array(lane.buffer)
  if (direction < 0) words[0] += lane[0] > 0 ? -1 : 1
  else words[0] += lane[0] >= 0 ? 1 : -1
  return lane[0]
}

function buildFloatExprRhsEvidence(runtime) {
  const expectedBytes = []
  const rawScalarBytes = []
  const records = floatExprRhsDefinitions.map(([name, sourceRhs]) => {
    const narrowedRhs = f(sourceRhs)
    if (!(narrowedRhs < sourceRhs)) throw new Error(`${name}: fixture rhs does not round downward to f32`)
    const left = new Float32Array([
      adjacentF32(narrowedRhs, -1),
      narrowedRhs,
      adjacentF32(narrowedRhs, 1),
    ])
    const canonicalRhs = new Float32Array([narrowedRhs, narrowedRhs, narrowedRhs])
    const canonicalLess = Array.from(runtime.stdlib.lessThan(left, canonicalRhs), Boolean)
    const canonicalGreaterEqual = Array.from(runtime.stdlib.greaterThanEqual(left, canonicalRhs), Boolean)
    const rawScalarLess = Array.from(runtime.stdlib.lessThan(left, sourceRhs), Boolean)
    const rawScalarGreaterEqual = Array.from(runtime.stdlib.greaterThanEqual(left, sourceRhs), Boolean)
    const independentLess = Array.from(left, (value) => value < narrowedRhs)
    const independentGreaterEqual = Array.from(left, (value) => value >= narrowedRhs)
    if (JSON.stringify(canonicalLess) !== JSON.stringify(independentLess) || JSON.stringify(canonicalGreaterEqual) !== JSON.stringify(independentGreaterEqual)) {
      throw new Error(`${name}: canonical Vec3 broadcast disagreement`)
    }
    if (JSON.stringify(canonicalLess) === JSON.stringify(rawScalarLess) || JSON.stringify(canonicalGreaterEqual) === JSON.stringify(rawScalarGreaterEqual)) {
      throw new Error(`${name}: raw retained-double rhs mutation escaped`)
    }
    for (const value of [...canonicalLess, ...canonicalGreaterEqual]) expectedBytes.push(value ? 1 : 0)
    for (const value of [...rawScalarLess, ...rawScalarGreaterEqual]) rawScalarBytes.push(value ? 1 : 0)
    return {
      name,
      native_calls_required: [
        `glsl::lessThan(glsl::Vec3(left), glsl::FloatExpr<3>(${sourceRhs}))`,
        `glsl::greaterThanEqual(glsl::Vec3(left), glsl::FloatExpr<3>(${sourceRhs}))`,
      ],
      source_rhs_double: sourceRhs,
      source_rhs_double_text: sourceRhs.toPrecision(17),
      materialized_vec3_rhs_f32: narrowedRhs,
      materialized_vec3_rhs_f32_bits_le: f32Bits(narrowedRhs),
      left_f32: Array.from(left),
      left_f32_bits_le: Array.from(left, f32Bits),
      expected_less_than_after_vec3_materialization: canonicalLess,
      expected_greater_than_equal_after_vec3_materialization: canonicalGreaterEqual,
      rejected_raw_scalar_less_than: rawScalarLess,
      rejected_raw_scalar_greater_than_equal: rawScalarGreaterEqual,
      equality_lane_index: 1,
      equality_lane_discriminates_raw_scalar: (
        canonicalLess[1] !== rawScalarLess[1]
        && canonicalGreaterEqual[1] !== rawScalarGreaterEqual[1]),
    }
  })
  const expected = Uint8Array.from(expectedBytes)
  const rawScalar = Uint8Array.from(rawScalarBytes)
  if (bytes(expected).equals(bytes(rawScalar))) throw new Error('aggregate FloatExpr rhs mutation escaped')
  return {
    contract: 'For the authenticated Edge calls, construct glsl::Vec3 from the FloatExpr<3> right operand before lane comparison. This reproduces canonical new PooledFloat32Array([lvl,lvl,lvl]); comparing Vec3 lanes directly to retained doubles is rejected.',
    actual_native_test_requirement: 'Production native tests must call the real width-3 overloads with Vec3 left operands and FloatExpr<3> right operands, including source rhs 57/100.',
    records,
    aggregate_expected_boolean_bytes_sha256: sha256(expected),
    rejected_raw_scalar_boolean_bytes_sha256: sha256(rawScalar),
    raw_scalar_mutation_discriminated: true,
  }
}

function buildDirectBvecEvidence() {
  const runtime = new GlslCpuRuntime()
  const words = []
  const records = directDefinitions.map(([name, leftValues, rightValues]) => {
    const left = new Float32Array(leftValues)
    const right = new Float32Array(rightValues)
    const less = Array.from(runtime.stdlib.lessThan(left, right), Boolean)
    const greaterEqual = Array.from(runtime.stdlib.greaterThanEqual(left, right), Boolean)
    const independentLess = Array.from(left, (value, index) => value < right[index])
    const independentGreaterEqual = Array.from(left, (value, index) => value >= right[index])
    if (JSON.stringify(less) !== JSON.stringify(independentLess) || JSON.stringify(greaterEqual) !== JSON.stringify(independentGreaterEqual)) {
      throw new Error(`${name}: independent bvec relational disagreement`)
    }
    const selectedUpper = greaterEqual
    const selectedLower = less
    const crossingUpper = selectedUpper.map((onSide, index) => onSide && !less[index])
    const crossingLower = selectedLower.map((onSide, index) => onSide && greaterEqual[index])
    for (const value of [...less, ...greaterEqual, ...crossingUpper, ...crossingLower]) words.push(value ? 1 : 0)
    return {
      name,
      left_f32_bits_le: Array.from(left, f32Bits),
      right_f32_bits_le: Array.from(right, f32Bits),
      less_than: less,
      greater_than_equal: greaterEqual,
      selected_upper: selectedUpper,
      selected_lower: selectedLower,
      constructed_crossing_upper: crossingUpper,
      constructed_crossing_lower: crossingLower,
    }
  })
  const reference = Uint8Array.from(words)
  const swappedRelations = Uint8Array.from(reference, (_, index) => {
    const slot = index % 12
    if (slot < 3) return reference[index + 3]
    if (slot < 6) return reference[index - 3]
    return reference[index]
  })
  const laneBroadcast = Uint8Array.from(reference, (_, index) => {
    const row = Math.floor(index / 12) * 12
    const group = Math.floor((index % 12) / 3) * 3
    return reference[row + group]
  })
  if (bytes(reference).equals(bytes(swappedRelations)) || bytes(reference).equals(bytes(laneBroadcast))) throw new Error('direct bvec mutation escaped')
  return {
    semantics: 'The shipped runtime relational helpers compare each Float32 lane with native JavaScript < or >=, return numeric 0/1 lanes, and the canonical Edge factory stores/reads those lanes through Float32-backed bvec materialization.',
    records,
    aggregate_boolean_bytes_sha256: sha256(reference),
    mutations: [
      { name: 'less-and-greater-equal-swapped', candidate_sha256: sha256(swappedRelations), discriminated: true },
      { name: 'each-bvec-broadcast-from-lane-zero', candidate_sha256: sha256(laneBroadcast), discriminated: true },
    ],
    vec3_float_expr_rhs: buildFloatExprRhsEvidence(runtime),
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
    return {
      name: definition.name,
      dimensions: { width: definition.width, height: definition.height },
      controls: {
        kernel: definition.kernel,
        size: definition.size,
        render_scale: f(definition.renderScale),
        blend: definition.blend,
        invert: definition.invert,
        channel: definition.channel,
        threshold: f(definition.threshold),
        amount: f(definition.amount),
        mix: f(definition.mixAmt),
        level: f(definition.level),
        contour_side: definition.contourSide,
        time: f(definition.time),
        frame: definition.frame,
        external_pass_seed: definition.externalSeed,
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
  })

  for (const definition of cases) {
    if (!definition.sameAs) continue
    const equality = compareSurfaces(renderedByName.get(definition.sameAs), renderedByName.get(definition.name))
    if (!equality.float32.exact_f32_bits || !equality.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: identity with ${definition.sameAs} failed`)
    caseResults.find((item) => item.name === definition.name).declared_identity = { reference_case: definition.sameAs, comparison: equality }
  }

  const requiredWitnesses = {
    'upper-relational-inverted': ['contour-color-upper'],
    'lower-relational-inverted': ['contour-color-lower'],
    'red-center-side-read-from-green': ['contour-color-lower', 'contour-color-upper'],
    'green-crossing-output-read-from-blue': ['contour-color-lower', 'contour-color-upper'],
    'contour-side-forced-lower': ['contour-color-upper'],
    'contour-level-divisor-changed': ['contour-color-lower', 'contour-color-upper'],
    'contour-rhs-f32-broadcast-bypassed': ['contour-color-lower-level57-f32-equality', 'contour-color-upper-level57-f32-equality'],
    'contour-dispatch-disabled': ['contour-color-lower', 'contour-luma-upper'],
    'channel-branch-inverted': ['fine-color-radius-two', 'fine-luma-threshold-invert', 'contour-color-lower', 'contour-luma-lower'],
    'center-self-splat-simultaneous': ['fine-luma-threshold-invert', 'blend-0', 'blend-3', 'blend-6'],
  }
  const renderMutationSummary = renderMutants.map((mutant) => {
    const witnesses = caseResults.filter((record) => !record.mutation_comparisons[mutant.name].float32.exact_f32_bits).map((record) => record.name)
    for (const required of requiredWitnesses[mutant.name]) {
      if (!witnesses.includes(required)) throw new Error(`${mutant.name}: required witness ${required} did not diverge; got ${witnesses.join(', ')}`)
    }
    let frozenFirstMismatch
    if (mutant.name === 'center-self-splat-simultaneous') {
      if (JSON.stringify(witnesses) !== JSON.stringify(requiredWitnesses[mutant.name])) throw new Error(`${mutant.name}: exact four-case witness set drift: ${witnesses.join(', ')}`)
      const mismatch = caseResults.find((record) => record.name === 'fine-luma-threshold-invert').mutation_comparisons[mutant.name].float32.first_mismatch
      const expected = { lane_index: 25, pixel_index: 6, top_down_xy: [6, 0], channel: 'g', reference_bits_le: '0x3ef9ec6f', candidate_bits_le: '0x3e69ed28' }
      for (const [key, value] of Object.entries(expected)) {
        if (JSON.stringify(mismatch?.[key]) !== JSON.stringify(value)) throw new Error(`${mutant.name}: frozen first mismatch ${key} drift`)
      }
      frozenFirstMismatch = expected
    }
    return {
      name: mutant.name,
      factory_sha256: mutant.factory_sha256,
      anchor_sha256: mutant.anchor_sha256,
      replacement_sha256: mutant.replacement_sha256,
      required_witnesses: requiredWitnesses[mutant.name],
      all_divergent_cases: witnesses,
      exact_comparer_discriminated: witnesses.length > 0,
      ...(frozenFirstMismatch ? { frozen_first_mismatch: frozenFirstMismatch } : {}),
    }
  })

  return {
    schema: 'noisemaker-for-cpp.edge.pixel-parity-and-bvec3-oracle.v1',
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
      generator_path: path.relative(cppRoot, generatorPath),
      generator_sha256: sha256(fs.readFileSync(generatorPath)),
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    frontend_proof: frontendProof,
    metadata_contract: expectedParams,
    fixture: {
      patterned_input: 'asymmetric colored top-down Float32 RGBA with signed zero and finite out-of-range lanes',
      contour_input: '7x7 component-distinct ramps plus a level-57 fixture whose center is exactly f32(0.57) and whose cardinal neighbors lie on both threshold sides',
      comparer: 'exact Float32-bit and RGBA8-byte custom comparer with first pixel/channel diagnostics',
      repeated_render_count: 2,
      level57_threshold_contract: buildLevel57FixtureEvidence(),
    },
    comparer_self_tests: comparerSelfTests(),
    direct_bvec3_relational_and_storage: buildDirectBvecEvidence(),
    cases: caseResults,
    render_mutation_summary: renderMutationSummary,
    contract_negatives: frontendProof.contract_negatives,
  }
}

function makeReport(data) {
  const lines = [
    '# Edge bvec3 and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/edge:edge`. Exact Float32 and RGBA8 hashes cover both convolution kernels, both channel modes, both contour sides, threshold/invert/mix, all nine blend modes, control boundaries, repeatability, and input immutability. The typed-frontend probe freezes the exact stored `bvec3` closure and canonical lane-sequential center self-splat.', '',
    '## Frozen authority', '',
    `- Upstream snapshot revision: \`${data.upstream_revision}\``,
    `- Corpus revision: \`${data.corpus_revision}\``,
    `- GLSL source: ${data.provenance.source_raw_bytes} bytes, SHA-256 \`${data.provenance.source_sha256}\``,
    `- Canonical factory: \`${data.provenance.canonical_factory_name}\`, ${data.provenance.canonical_factory_to_string_bytes} bytes, SHA-256 \`${data.provenance.canonical_factory_to_string_sha256}\``,
    '- Public catalog identity is exactly the canonical factory; no adapter override exists.', '',
    '## Captured pre-admission C++ frontend boundary', '',
    `- Validator first error: \`${data.frontend_proof.captured_pre_admission_frontier.validator_first_error}\``,
    `- Emitter first error: \`${data.frontend_proof.captured_pre_admission_frontier.emitter_first_error}\``,
    `- Exactly ${data.frontend_proof.bvec3_nodes.length} bvec3-typed nodes and ${data.frontend_proof.bvec3_swizzles.length} lane reads exist, all inside reachable \`contourConv\`.`,
    `- The historical in-process global-widening diagnostic rendered ${data.frontend_proof.captured_pre_admission_frontier.diagnostic_bypass.rendered_cpp_bytes} bytes, SHA-256 \`${data.frontend_proof.captured_pre_admission_frontier.diagnostic_bypass.rendered_cpp_sha256}\`; this frozen record is not current admission evidence.`, '',
    '## Current exact-profile C++ frontend boundary', '',
    `- Without the profile, validator first error: \`${data.frontend_proof.current_profile_frontier.validator_first_error}\``,
    `- Without the profile, emitter first error: \`${data.frontend_proof.current_profile_frontier.emitter_first_error}\``,
    `- The exact profile makes both independent authorities pass without widening global vocabularies; rendered C++ is ${data.frontend_proof.current_profile_frontier.profile_admission.rendered_cpp_bytes} bytes, SHA-256 \`${data.frontend_proof.current_profile_frontier.profile_admission.rendered_cpp_sha256}\`.`,
    `- The center self-splat assignment is source-authenticated at \`${data.frontend_proof.center_splat.assignment_span}\`, SHA-256 \`${data.frontend_proof.center_splat.assignment_sha256}\`, including its complete five-statement ancestry and target/constructor/dot child identities.`,
    '- Do not widen the global type or builtin vocabularies. The validator and emitter independently re-authenticate the key/hash/interface, all typed nodes and lane reads, the center-splat route, and the absence of any extra admitted site.', '',
    '## Runtime shape', '',
    '- `glsl::BVec3` already exists. Edge additionally needs exact-profile-only `greaterThanEqual(Vec3, FloatExpr<3>)` and `lessThan(Vec3, FloatExpr<3>)` lowering, constrained to width 3 rather than widening Extrude’s width-2 helpers.',
    '- The FloatExpr right operand must first materialize through `glsl::Vec3`, narrowing every retained-double lane to Float32 exactly as canonical `new PooledFloat32Array([lvl, lvl, lvl])` does. Direct comparison against the retained double is observably wrong and explicitly rejected.',
    '- Canonical JavaScript stores `dot(centerSample, LUMA)` into lanes 0, 1, and 2 sequentially; each later dot observes earlier Float32 stores. The C++ lowering is exactly three contiguous ordered `set_swizzle<0/1/2>` calls. A simultaneous whole-Vec splat is rejected.',
    `- ${data.direct_bvec3_relational_and_storage.records.length} general direct fixtures cover mixed/equal lanes, signed zero, infinities, NaNs, and adjacent Float32 values. Their relational/selection/construction bytes hash to \`${data.direct_bvec3_relational_and_storage.aggregate_boolean_bytes_sha256}\`.`,
    `- ${data.direct_bvec3_relational_and_storage.vec3_float_expr_rhs.records.length} native-style Vec3/FloatExpr fixtures require calls to the actual overload shape. Expected boolean bytes hash to \`${data.direct_bvec3_relational_and_storage.vec3_float_expr_rhs.aggregate_expected_boolean_bytes_sha256}\`; the rejected raw-double comparison hashes to \`${data.direct_bvec3_relational_and_storage.vec3_float_expr_rhs.rejected_raw_scalar_boolean_bytes_sha256}\`.`, '',
    '## Render cases', '',
    '| Case | Size | Kernel | Channel | Side | Level | Blend | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |',
  ]
  for (const record of data.cases) {
    const c = record.controls
    lines.push(`| ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${c.kernel} | ${c.channel} | ${c.contour_side} | ${c.level} | ${c.blend} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every case requires exact repeated-render identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. The external-context pair must remain exactly identical.', '')
  lines.push('## Mutation discrimination', '', '| Mutation | Required witnesses | All divergent cases |', '| --- | --- | --- |')
  for (const mutation of data.render_mutation_summary) lines.push(`| ${mutation.name} | ${mutation.required_witnesses.join(', ')} | ${mutation.all_divergent_cases.join(', ')} |`)
  const selfSplat = data.render_mutation_summary.find((item) => item.name === 'center-self-splat-simultaneous')
  lines.push('', `The simultaneous center-splat mutant diverges in exactly four cases. Its first frozen mismatch is lane ${selfSplat.frozen_first_mismatch.lane_index}, top-down (${selfSplat.frozen_first_mismatch.top_down_xy.join(',')}), channel ${selfSplat.frozen_first_mismatch.channel}: canonical ${selfSplat.frozen_first_mismatch.reference_bits_le}, simultaneous ${selfSplat.frozen_first_mismatch.candidate_bits_le}.`, '')
  lines.push('Frontend negatives reject wrong profile/key/hash, both relational substitutions, two bvec lane-route changes, an extra stored bvec3 site, a reversed center-splat dot route, and an extra self-splat. The whole-program, interface, and exact node/ancestry hashes make unrelated source drift fail closed.', '')
  lines.push('## Regeneration', '', 'From the repository root:', '', '```sh', 'python3 docs/port-engineering/bvec/edge-parity/edge_frontend_probe.py --check', 'python3 docs/port-engineering/bvec/edge-parity/edge_frontend_probe.py --live-frontier', 'node docs/port-engineering/bvec/edge-parity/edge_parity_oracle_generator.mjs', 'node docs/port-engineering/bvec/edge-parity/edge_parity_oracle_generator.mjs --check', '```', '')
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
  checkExact(outputPath, json, 'Edge oracle JSON')
  checkExact(reportPath, report, 'Edge oracle report')
  checkExact(`${outputPath}.sha256`, jsonSidecar, 'Edge oracle JSON sidecar')
  checkExact(`${reportPath}.sha256`, reportSidecar, 'Edge oracle report sidecar')
  checkExact(`${generatorPath}.sha256`, generatorSidecar, 'Edge generator sidecar')
  checkExact(`${frontendProbePath}.sha256`, probeSidecar, 'Edge frontend probe sidecar')
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  fs.writeFileSync(`${outputPath}.sha256`, jsonSidecar)
  fs.writeFileSync(`${reportPath}.sha256`, reportSidecar)
  fs.writeFileSync(`${generatorPath}.sha256`, generatorSidecar)
  fs.writeFileSync(`${frontendProbePath}.sha256`, probeSidecar)
}

console.log(`Edge parity oracle ok (${data.cases.length} render cases, ${data.direct_bvec3_relational_and_storage.records.length + data.direct_bvec3_relational_and_storage.vec3_float_expr_rhs.records.length} direct fixtures, ${data.render_mutation_summary.length + data.direct_bvec3_relational_and_storage.mutations.length + 1 + data.contract_negatives.length} mutations/negative gates)`)
