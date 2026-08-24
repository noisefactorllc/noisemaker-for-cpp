import crypto from 'node:crypto'
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
import { bindGlslKernel } from '../../../../../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../../../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../../../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const platformRoot = path.resolve(here, '../../../../..')
const cppRoot = path.join(platformRoot, 'noisemaker-for-cpp')
const cpuRoot = path.join(platformRoot, 'noisemaker-for-cpu')
const outputPath = path.join(here, 'grain-parity-oracles.json')
const reportPath = path.join(here, 'grain-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const programKey = 'filter/grain:grain'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/grain/grain.glsl')
const f = Math.fround

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(view) {
  return Buffer.from(view.buffer, view.byteOffset, view.byteLength)
}

function f32Bits(value) {
  const lane = new Float32Array([value])
  return `0x${new DataView(lane.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}

function u32Hex(value) {
  return `0x${(value >>> 0).toString(16).padStart(8, '0')}`
}

// Purpose-built comparer for Grain parity. Equality is raw Float32 bit
// equality, including signed zero and NaN payloads. Pixel/channel diagnostics
// are additive and never replace the exact bytes and SHA-256 contracts.
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
  const a = new Uint32Array(reference.data.buffer, reference.data.byteOffset, reference.data.length)
  const b = new Uint32Array(candidate.data.buffer, candidate.data.byteOffset, candidate.data.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] === b[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        lane_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_value: reference.data[i],
        candidate_value: candidate.data[i],
        reference_bits_le: u32Hex(a[i]),
        candidate_bits_le: u32Hex(b[i]),
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
  const a = reference.toRgba8()
  const b = candidate.toRgba8()
  if (a.length !== b.length) throw new Error('RGBA8 length mismatch')
  let mismatched = 0
  let first = null
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] === b[i]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(i / 4)
      first = {
        byte_index: i,
        pixel_index: pixel,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][i % 4],
        reference_byte: a[i],
        candidate_byte: b[i],
      }
    }
  }
  return { exact_rgba8_bytes: mismatched === 0, mismatched_bytes: mismatched, first_mismatch: first }
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
    throw new TypeError('compareU32Words requires two Uint32Array values')
  }
  if (reference.length !== candidate.length) {
    return { exact_u32_words: false, mismatched_words: Math.max(reference.length, candidate.length), first_mismatch: 0 }
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
if (sourceBytes.length !== 8796 || sha256(sourceBytes) !== '6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0') {
  throw new Error('pinned Grain GLSL source drift')
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory65') throw new Error('canonical Grain factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 9702 || sha256(canonicalFactory.toString()) !== '36a15bacaf42ebe94dc587fdc77cb56a5c714cae51fd40c7f7a6a187794ef44f') {
  throw new Error('canonical Grain factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog Grain factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Grain adapter override')

const effect = effectRecords.find((record) => record.id === 'filter/grain')
if (!effect) throw new Error('Grain metadata record missing')
const expectedParams = {
  alpha: { type: 'float', default: 0.25, uniform: 'alpha', min: 0, max: 1 },
  pause: { type: 'boolean', default: false, uniform: 'pause' },
}
for (const [name, expected] of Object.entries(expectedParams)) {
  const actual = effect.params?.[name]
  for (const [field, value] of Object.entries(expected)) {
    if (actual?.[field] !== value) throw new Error(`Grain ${name}.${field} metadata drift`)
  }
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
  // Exact-bit edge values ensure the immutability check is not merely a
  // numerical-equality check. The active cases also retain asymmetric color.
  data[0] = -0
  if (data.length >= 12) data[9] = f(-0.25)
  if (data.length >= 20) data[18] = f(1.25)
  return new Surface(width, height, data)
}

const cases = [
  { name: 'amount-zero-input-identity', width: 5, height: 3, phase: 1, alpha: 0, pause: 0, time: 0, frame: 0, seed: 0, renderScale: 1, coverage: ['amount/alpha minimum', 'exact input identity', 'zero seed'] },
  { name: 'base-time0-frame0-seed0', width: 7, height: 5, phase: 2, alpha: 0.25, pause: 0, time: 0, frame: 0, seed: 0, renderScale: 1, coverage: ['default amount', 'time zero', 'frame zero', 'landscape'] },
  { name: 'base-time0-frame-max-seed-max', width: 7, height: 5, phase: 2, alpha: 0.25, pause: 0, time: 0, frame: 4294967295, seed: 4294967295, renderScale: 1, sameAs: 'base-time0-frame0-seed0', coverage: ['external seed/frame identity', 'extreme seed', 'extreme frame'] },
  { name: 'animated-time-eighth', width: 7, height: 5, phase: 3, alpha: 1, pause: 0, time: 0.125, frame: 17, seed: 2147483648, renderScale: 1, coverage: ['nonzero time', 'amount/alpha maximum', 'high-bit external seed'] },
  { name: 'pause-reference-time0', width: 7, height: 5, phase: 3, alpha: 1, pause: 0, time: 0, frame: 17, seed: 2147483648, renderScale: 1, coverage: ['pause equality reference'] },
  { name: 'paused-nonzero-time', width: 7, height: 5, phase: 3, alpha: 1, pause: 1, time: 0.125, frame: 99, seed: 1, renderScale: 1, sameAs: 'pause-reference-time0', coverage: ['paused time', 'nonzero seed'] },
  { name: 'scale-clamped-zero', width: 4, height: 9, phase: 4, alpha: 0.75, pause: 0, time: 0.03125, frame: 3, seed: 4660, renderScale: 0, coverage: ['noiseScale/renderScale below clamp', 'portrait'] },
  { name: 'scale-one-control', width: 4, height: 9, phase: 4, alpha: 0.75, pause: 0, time: 0.03125, frame: 3, seed: 4660, renderScale: 1, sameAs: 'scale-clamped-zero', coverage: ['noiseScale/renderScale clamp boundary'] },
  { name: 'scale-noninteger', width: 11, height: 3, phase: 5, alpha: 0.5, pause: 0, time: 0.375, frame: 4, seed: 305419896, renderScale: 1.5, coverage: ['noninteger scale', 'wide non-square', 'edge pixels'] },
  { name: 'scale-large-tiled-round-half', width: 3, height: 4, phase: 6, alpha: 1, pause: 0, time: 0.625, frame: 5, seed: 4294967295, renderScale: 50, tileOffset: [3, 1], fullResolution: [5.5, 5.5], coverage: ['large scale', 'tile offset', 'positive round ties', 'edge global pixels'] },
  { name: 'carry-in-bounds-then-oob', width: 3, height: 1, phase: 7, alpha: 1, pause: 0, time: 0, frame: 0, seed: 0, renderScale: 1, tileOffset: [1, 0], fullResolution: [2, 1], coverage: ['first pixel in bounds', 'later pixels out of bounds', 'bound fragColor carry-forward'] },
  { name: 'fresh-first-pixel-oob', width: 3, height: 1, phase: 8, alpha: 1, pause: 0, time: 0, frame: 0, seed: 0, renderScale: 1, tileOffset: [2, 0], fullResolution: [2, 1], coverage: ['fresh bound kernel', 'first pixel out of bounds', 'zero-initialized fragColor'] },
  { name: 'full-resolution-x-zero-fallback', width: 4, height: 2, phase: 9, alpha: 0.625, pause: 0, time: 0.0625, frame: 0, seed: 0, renderScale: 1, fullResolution: [0, 99], coverage: ['fullResolution.x <= 0', 'resolution fallback', 'finite output'] },
  { name: 'repeated-bound-kernel-first-pixel-oob', width: 1, height: 2, bindWidth: 1, bindHeight: 1, passes: [{ width: 1, height: 1 }, { width: 1, height: 2 }], phase: 10, alpha: 1, pause: 0, time: 0, frame: 0, seed: 0, renderScale: 1, fullResolution: [1, 1], coverage: ['same bound kernel across runPass calls', 'second pass first pixel out of bounds', 'prior-pass fragColor carry-forward'] },
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
  compileMutant('xor-lane0-seed-omitted', '(cell[0]|0) ^ seed', '(cell[0]|0)'),
  compileMutant('xor-lane1-replaced-by-add', '(cell[1]|0) ^ (cpu_umul(seed, 2654435769) + 2135587861)', '((cell[1]|0) + (cpu_umul(seed, 2654435769) + 2135587861))'),
  compileMutant('xor-lane2-replaced-by-or', '(cell[2]|0) ^ (cpu_umul(seed, 1663821211) + 1542469173)', '((cell[2]|0) | (cpu_umul(seed, 1663821211) + 1542469173))'),
  compileMutant('wrong-round-positive-ties-truncate', 'max(round(value), 0)|0', 'max(Math.trunc(value), 0)|0'),
  compileMutant('base-seed-omitted', 'var BASE_SEED = 4660;', 'var BASE_SEED = 0;'),
  compileMutant('time-omitted-when-running', 'var effective_time = pause > 0.5 ? 0 : time;', 'var effective_time = pause > 0.5 ? 0 : 0;'),
  compileMutant('monochrome-channel-coupling-broken', 'new $runtime.PooledFloat32Array([noise_value, noise_value, noise_value])', 'new $runtime.PooledFloat32Array([noise_value, 0, noise_value])'),
]

function render(factory, definition) {
  const bindWidth = definition.bindWidth ?? definition.width
  const bindHeight = definition.bindHeight ?? definition.height
  const passes = definition.passes ?? [{ width: definition.width, height: definition.height }]
  const input = patternedSurface(bindWidth, bindHeight, definition.phase)
  const before = input.data.slice()
  const uniforms = {
    alpha: f(definition.alpha),
    pause: f(definition.pause),
    renderScale: f(definition.renderScale),
  }
  const tileOffset = definition.tileOffset ? new Float32Array(definition.tileOffset.map(f)) : undefined
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution.map(f)) : undefined
  const bindings = createCanonicalBindings({
    width: bindWidth,
    height: bindHeight,
    time: definition.time,
    frame: definition.frame,
    seed: definition.seed,
    uniforms,
    textures: { inputTex: input },
    tileOffset,
    fullResolution,
  })
  if (f32Bits(bindings.alpha) !== f32Bits(uniforms.alpha) || f32Bits(bindings.pause) !== f32Bits(uniforms.pause) || f32Bits(bindings.renderScale) !== f32Bits(uniforms.renderScale)) {
    throw new Error(`${definition.name}: uniform materialization drift`)
  }
  const kernel = bindGlslKernel(factory, bindings)
  const outputs = passes.map((pass) => {
    const output = new Surface(pass.width, pass.height)
    runPass({ kernel, destination: output, time: definition.time, seed: definition.seed })
    return output
  })
  const output = outputs.at(-1)
  const inputAfter = input.data.slice()
  const immutable = compareU32Words(
    new Uint32Array(before.buffer, before.byteOffset, before.length),
    new Uint32Array(inputAfter.buffer, inputAfter.byteOffset, inputAfter.length),
  )
  if (!immutable.exact_u32_words) throw new Error(`${definition.name}: input texture mutated`)
  return { output, outputs, inputBefore: before, inputAfter, immutable, bindings }
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
  if (nonfinite !== 0) throw new Error('nonfinite Grain output')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    probes: selectedProbes(surface),
  }
}

function pcgCanonical(words) {
  const out = new Uint32Array(words)
  out[0] = (Math.imul(out[0], 1664525) + 1013904223) >>> 0
  out[1] = (Math.imul(out[1], 1664525) + 1013904223) >>> 0
  out[2] = (Math.imul(out[2], 1664525) + 1013904223) >>> 0
  out[0] = (out[0] + Math.imul(out[1], out[2])) >>> 0
  out[1] = (out[1] + Math.imul(out[2], out[0])) >>> 0
  out[2] = (out[2] + Math.imul(out[0], out[1])) >>> 0
  out[0] = (out[0] ^ (out[0] >>> 16)) >>> 0
  out[1] = (out[1] ^ (out[1] >>> 16)) >>> 0
  out[2] = (out[2] ^ (out[2] >>> 16)) >>> 0
  out[0] = (out[0] + Math.imul(out[1], out[2])) >>> 0
  out[1] = (out[1] + Math.imul(out[2], out[0])) >>> 0
  out[2] = (out[2] + Math.imul(out[0], out[1])) >>> 0
  return out
}

function hashWordsJs(cell, seed, mutation = 'none') {
  const uSeed = seed >>> 0
  const mul1 = mutation === 'coalesced-number-multiply' ? uSeed * 2654435769 : Math.imul(uSeed, 2654435769) >>> 0
  const mul2 = mutation === 'coalesced-number-multiply' ? uSeed * 1663821211 : Math.imul(uSeed, 1663821211) >>> 0
  const sourceSeed = mutation === 'narrow-seed-to-u16' ? uSeed & 0xffff : uSeed
  const words = new Uint32Array([
    (cell[0] | 0) ^ sourceSeed,
    (cell[1] | 0) ^ (mul1 + 2135587861),
    (cell[2] | 0) ^ (mul2 + 1542469173),
  ])
  if (mutation === 'signed-xor-propagates-to-arithmetic-shift') {
    const out = new Int32Array(words)
    out[0] = (Math.imul(out[0], 1664525) + 1013904223) | 0
    out[1] = (Math.imul(out[1], 1664525) + 1013904223) | 0
    out[2] = (Math.imul(out[2], 1664525) + 1013904223) | 0
    out[0] = (out[0] + Math.imul(out[1], out[2])) | 0
    out[1] = (out[1] + Math.imul(out[2], out[0])) | 0
    out[2] = (out[2] + Math.imul(out[0], out[1])) | 0
    out[0] = out[0] ^ (out[0] >> 16)
    out[1] = out[1] ^ (out[1] >> 16)
    out[2] = out[2] ^ (out[2] >> 16)
    out[0] = (out[0] + Math.imul(out[1], out[2])) | 0
    out[1] = (out[1] + Math.imul(out[2], out[0])) | 0
    out[2] = (out[2] + Math.imul(out[0], out[1])) | 0
    return { hashed: words, pcg: new Uint32Array(out.buffer.slice(0)) }
  }
  if (mutation === 'reorder-pcg-mix-stage') {
    const out = new Uint32Array(words)
    out[0] = (Math.imul(out[0], 1664525) + 1013904223) >>> 0
    out[1] = (Math.imul(out[1], 1664525) + 1013904223) >>> 0
    out[2] = (Math.imul(out[2], 1664525) + 1013904223) >>> 0
    out[1] = (out[1] + Math.imul(out[2], out[0])) >>> 0
    out[0] = (out[0] + Math.imul(out[1], out[2])) >>> 0
    out[2] = (out[2] + Math.imul(out[0], out[1])) >>> 0
    out[0] = (out[0] ^ (out[0] >>> 16)) >>> 0
    out[1] = (out[1] ^ (out[1] >>> 16)) >>> 0
    out[2] = (out[2] ^ (out[2] >>> 16)) >>> 0
    out[0] = (out[0] + Math.imul(out[1], out[2])) >>> 0
    out[1] = (out[1] + Math.imul(out[2], out[0])) >>> 0
    out[2] = (out[2] + Math.imul(out[0], out[1])) >>> 0
    return { hashed: words, pcg: out }
  }
  return { hashed: words, pcg: pcgCanonical(words) }
}

function hashWordsBigInt(cell, seed) {
  const mask = 0xffffffffn
  const u = (value) => Number(BigInt.asUintN(32, BigInt(value)))
  const s = BigInt(seed >>> 0)
  const lane0 = BigInt.asUintN(32, BigInt(cell[0] | 0)) ^ s
  const lane1 = BigInt.asUintN(32, BigInt(cell[1] | 0)) ^ (((s * 0x9e3779b9n) + 0x7f4a7c15n) & mask)
  const lane2 = BigInt.asUintN(32, BigInt(cell[2] | 0)) ^ (((s * 0x632be59bn) + 0x5bf03635n) & mask)
  return new Uint32Array([u(lane0), u(lane1), u(lane2)])
}

const directDefinitions = [
  { cell: [0, 0, 0], seed: 0 },
  { cell: [1, -1, 2], seed: 1 },
  { cell: [-2147483648, 2147483647, -1], seed: 0x1234 },
  { cell: [2147483647, -2147483648, 65537], seed: 0x7fffffff },
  { cell: [-17, 33, -65536], seed: 0x80000000 },
  { cell: [-1, -1, -1], seed: 0xffffffff },
]

function buildDirectEvidence() {
  const records = directDefinitions.map((definition) => {
    const canonical = hashWordsJs(definition.cell, definition.seed)
    const independent = hashWordsBigInt(definition.cell, definition.seed)
    const materialization = compareU32Words(canonical.hashed, independent)
    if (!materialization.exact_u32_words) throw new Error('BigInt uint-XOR recompute disagrees with canonical JS materialization')
    return {
      cell_i32: definition.cell,
      seed_u32: definition.seed,
      seed_hex: u32Hex(definition.seed),
      scalar_xor_signed_numbers_before_uvec3: [
        (definition.cell[0] | 0) ^ (definition.seed >>> 0),
        (definition.cell[1] | 0) ^ ((Math.imul(definition.seed >>> 0, 2654435769) >>> 0) + 2135587861),
        (definition.cell[2] | 0) ^ ((Math.imul(definition.seed >>> 0, 1663821211) >>> 0) + 1542469173),
      ],
      hashed_u32: Array.from(canonical.hashed),
      hashed_hex: Array.from(canonical.hashed, u32Hex),
      independent_bigint_materialization: materialization,
      pcg_u32: Array.from(canonical.pcg),
      pcg_hex: Array.from(canonical.pcg, u32Hex),
      noise_x_f32: f(canonical.pcg[0] * f(1 / 4294967296)),
      noise_x_f32_bits_le: f32Bits(canonical.pcg[0] * f(1 / 4294967296)),
    }
  })

  const canonicalHashed = new Uint32Array(records.flatMap((record) => record.hashed_u32))
  const canonicalPcg = new Uint32Array(records.flatMap((record) => record.pcg_u32))
  const mutations = ['signed-xor-propagates-to-arithmetic-shift', 'narrow-seed-to-u16', 'coalesced-number-multiply', 'reorder-pcg-mix-stage'].map((name) => {
    const mutated = directDefinitions.map((definition) => hashWordsJs(definition.cell, definition.seed, name))
    const hashed = new Uint32Array(mutated.flatMap((item) => Array.from(item.hashed)))
    const pcg = new Uint32Array(mutated.flatMap((item) => Array.from(item.pcg)))
    const hashedComparison = compareU32Words(canonicalHashed, hashed)
    const pcgComparison = compareU32Words(canonicalPcg, pcg)
    if (!['signed-xor-propagates-to-arithmetic-shift', 'reorder-pcg-mix-stage'].includes(name) && hashedComparison.exact_u32_words) throw new Error(`${name}: direct hash mutation was not discriminated`)
    if (pcgComparison.exact_u32_words) throw new Error(`${name}: direct PCG mutation was not discriminated`)
    return { name, required_to_diverge: true, hashed_words: hashedComparison, pcg_words: pcgComparison }
  })
  return {
    records,
    aggregate_hashed_u32_le_sha256: sha256(bytes(canonicalHashed)),
    aggregate_pcg_u32_le_sha256: sha256(bytes(canonicalPcg)),
    mutations,
  }
}

function buildRoundEvidence() {
  const values = [-1.5, -0.5, -0, 0, 0.5, 1.5, 2.5, 16777215.5]
  return values.map((value) => {
    const rounded = Math.round(value)
    const clamped = Math.max(rounded, 0)
    return {
      input: value,
      input_f32: f(value),
      input_f32_bits_le: f32Bits(value),
      math_round: rounded,
      math_round_is_negative_zero: Object.is(rounded, -0),
      math_round_f32_bits_le: f32Bits(rounded),
      as_u32_before_constructor: clamped | 0,
      as_u32_word: (clamped | 0) >>> 0,
      as_u32_hex: u32Hex(clamped | 0),
    }
  })
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
      binding_dimensions: {
        width: definition.bindWidth ?? definition.width,
        height: definition.bindHeight ?? definition.height,
      },
      pass_dimensions: (definition.passes ?? [{ width: definition.width, height: definition.height }]).map(({ width, height }) => ({ width, height })),
      controls: {
        amount_alias_alpha: f(definition.alpha),
        pause: f(definition.pause),
        time: f(definition.time),
        frame: definition.frame,
        external_seed_input: definition.seed,
        external_seed_materialized_f32: canonicalFirst.bindings.seed,
        external_seed_materialized_f32_bits_le: f32Bits(canonicalFirst.bindings.seed),
        noise_scale_alias_render_scale: f(definition.renderScale),
        tile_offset: Array.from(canonicalFirst.bindings.tileOffset),
        full_resolution: Array.from(canonicalFirst.bindings.fullResolution),
      },
      coverage: definition.coverage,
      input: {
        f32_sha256_before: sha256(bytes(canonicalFirst.inputBefore)),
        f32_sha256_after: sha256(bytes(canonicalFirst.inputAfter)),
        immutable_exact_bits: compareU32Words(beforeBits, afterBits),
        probes: selectedProbes(new Surface(
          definition.bindWidth ?? definition.width,
          definition.bindHeight ?? definition.height,
          canonicalFirst.inputBefore,
        )),
      },
      output: outputRecord(canonicalFirst.output),
      pass_outputs: canonicalFirst.outputs.map(outputRecord),
      repeat_identity: repeat,
      public_catalog_vs_direct_canonical: publicComparison,
      mutation_comparisons: mutationComparisons,
    }
    if (definition.alpha === 0 && record.input.f32_sha256_before !== record.output.f32_sha256) throw new Error('alpha zero did not preserve exact input bits')
    return record
  })

  for (const definition of cases) {
    if (!definition.sameAs) continue
    const equality = compareSurfaces(renderedByName.get(definition.sameAs), renderedByName.get(definition.name))
    if (!equality.float32.exact_f32_bits || !equality.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: declared identity with ${definition.sameAs} failed`)
    caseResults.find((item) => item.name === definition.name).declared_identity = { reference_case: definition.sameAs, comparison: equality }
  }

  const requiredRenderMutations = {
    'xor-lane0-seed-omitted': ['base-time0-frame0-seed0', 'animated-time-eighth'],
    'xor-lane1-replaced-by-add': ['base-time0-frame0-seed0', 'animated-time-eighth'],
    'xor-lane2-replaced-by-or': ['base-time0-frame0-seed0', 'animated-time-eighth'],
    'wrong-round-positive-ties-truncate': ['scale-large-tiled-round-half'],
    'base-seed-omitted': ['base-time0-frame0-seed0'],
    'time-omitted-when-running': ['animated-time-eighth'],
    'monochrome-channel-coupling-broken': ['animated-time-eighth'],
  }
  const renderMutationSummary = renderMutants.map((mutant) => {
    const witnesses = caseResults.filter((record) => !record.mutation_comparisons[mutant.name].float32.exact_f32_bits).map((record) => record.name)
    for (const required of requiredRenderMutations[mutant.name]) {
      if (!witnesses.includes(required)) throw new Error(`${mutant.name}: required witness ${required} did not diverge`)
    }
    return {
      name: mutant.name,
      factory_sha256: mutant.factory_sha256,
      anchor_sha256: mutant.anchor_sha256,
      replacement_sha256: mutant.replacement_sha256,
      required_witnesses: requiredRenderMutations[mutant.name],
      all_divergent_cases: witnesses,
      exact_comparer_discriminated: witnesses.length > 0,
    }
  })

  return {
    schema: 'noisemaker-for-cpp.grain.pixel-parity-and-scalar-xor-oracle.v1',
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
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    frozen_scalar_xor_sites: [
      { lane: 0, glsl_span: '52:9-52:28', expression: 'uint(cell.x) ^ seed', node_sha256: '8100d099ade3c7427e31bcc6b4c1822d85e30488125a7a6d797225ee82184d11' },
      { lane: 1, glsl_span: '53:9-53:58', expression: 'uint(cell.y) ^ (seed * 0x9e3779b9u + 0x7f4a7c15u)', node_sha256: 'e5192eea3ce29a2f70cbce14e54e8be3126f57aa33cfd15d13114a5e503a1d49' },
      { lane: 2, glsl_span: '54:9-54:58', expression: 'uint(cell.z) ^ (seed * 0x632be59bu + 0x5bf03635u)', node_sha256: 'efc0ca3f7acee72aa885b6d83d857d3a728a14c27f11de37db485f427e309b8a' },
    ],
    materialization_contract: {
      scalar_xor: 'JavaScript ToInt32 operands/result, immediately materialized lane-wise by cpu_uvec3 as >>> 0',
      unsigned_multiply: 'Math.imul(left, right) >>> 0 before add/XOR',
      float32: 'typed bindings and Surface stores use Math.fround/Float32Array materialization',
      round: 'canonical CPU runtime uses Math.round; positive ties go toward +Infinity; negative half can produce -0 before clamp/int materialization',
      amount_alias: 'Grain exposes alpha; this oracle labels it amount only as a cross-port semantic alias',
      noise_scale_alias: 'Grain reads infrastructure renderScale and clamps it to at least 1; there is no effect-level noiseScale parameter',
      colored_mode: 'unreachable: canonical Grain has no colored control and broadcasts one scalar noise_value to RGB',
      external_seed_and_frame: 'unreachable in the render: canonical Grain uses BASE_SEED=0x1234 and reads neither binding',
    },
    metadata_contract: expectedParams,
    fixture: {
      input: 'asymmetric colored top-down Float32 RGBA with signed zero and finite out-of-range edge lanes',
      fragment_origin: 'bottom-left GLSL coordinates over top-down Surface storage',
      comparer: 'exact Float32-bit and RGBA8-byte custom comparer; hashes remain authoritative',
      repeated_render_count: 2,
      bound_kernel_pass_sequence: 'cases with pass_dimensions length > 1 bind once and invoke the same kernel for every listed pass',
    },
    round_materialization: buildRoundEvidence(),
    direct_scalar_recompute: buildDirectEvidence(),
    cases: caseResults,
    render_mutation_summary: renderMutationSummary,
    unreachable_traps: [
      'External seed and frame omission cannot be a pixel mutation witness because this canonical program does not read either binding; paired renders prove identity.',
      'A signed scalar XOR result and its immediate cpu_uvec3 unsigned materialization have identical low 32 bits; the authenticated parent role is structural, not pixel-observable.',
      'Negative-half and negative-zero round distinctions are erased by max(..., 0), integer materialization, and max(as_u32(...), 1) before any render coordinate uses them; direct round evidence freezes the intermediate behavior.',
      'There is no colored/monochrome branch to toggle. A mutation that breaks the fixed scalar-to-RGB broadcast is required to diverge instead.',
    ],
  }
}

function makeReport(data) {
  const lines = [
    '# Grain scalar-XOR and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/grain:grain`. The oracle combines direct unsigned-word recomputation of the three scalar XOR sites with canonical/public pixel renders. Float32 hashes and RGBA8 hashes are exact byte contracts; the custom comparer adds diagnostics without weakening those contracts.', '',
    '## Frozen identities', '',
    `- Upstream snapshot revision: \`${data.upstream_revision}\``,
    `- Corpus revision: \`${data.corpus_revision}\``,
    `- GLSL source SHA-256: \`${data.provenance.source_sha256}\``,
    `- Canonical factory: \`${data.provenance.canonical_factory_name}\`, ${data.provenance.canonical_factory_to_string_bytes} bytes, SHA-256 \`${data.provenance.canonical_factory_to_string_sha256}\``,
    '- Public catalog identity is exactly the canonical factory; no adapter override exists.', '',
    '## Semantic contract', '',
    '- Exactly three reachable scalar XOR sites are frozen, at GLSL spans `52:9-52:28`, `53:9-53:58`, and `54:9-54:58`.',
    '- JavaScript scalar `^` produces a signed int32 number. The immediate `cpu_uvec3` parent then applies `>>> 0` lane-wise, so the observable word is exact unsigned 32-bit XOR.',
    '- Unsigned multiplies are `Math.imul(... ) >>> 0`; the direct fixtures independently recompute the lane words with BigInt modulo 2^32 and require exact agreement.',
    '- `Math.round` and `as_u32` intermediates are frozen explicitly, including positive ties, negative half, and negative zero. Negative distinctions are not render-reachable after the canonical clamps.',
    '- `alpha` is the effect-level amount. `renderScale` is the closest noise-scale control but is an infrastructure binding, not an effect parameter. Grain has no colored control: it broadcasts one scalar noise value to RGB.', '',
    '## Render cases', '',
    '| Case | Size | Alpha | Pause | Time | Frame | External seed | Render scale | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |',
  ]
  for (const record of data.cases) {
    const c = record.controls
    lines.push(`| ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${c.amount_alias_alpha} | ${c.pause} | ${c.time} | ${c.frame} | ${c.external_seed_input} | ${c.noise_scale_alias_render_scale} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every case requires exact repeat identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. Declared frame/seed, pause/time, and renderScale-clamp identity pairs are checked bit-for-bit.', '')
  lines.push('## Mutation discrimination', '')
  lines.push('| Mutation | Required witness cases | All divergent cases |')
  lines.push('| --- | --- | --- |')
  for (const mutation of data.render_mutation_summary) {
    lines.push(`| ${mutation.name} | ${mutation.required_witnesses.join(', ')} | ${mutation.all_divergent_cases.join(', ')} |`)
  }
  lines.push('', 'The direct scalar corpus separately rejects letting the signed XOR intermediate escape into arithmetic shifts, seed narrowing, coalescing wrapped multiplication into ordinary Number multiplication, and reordering the sequential PCG mix stage. Each rejection is an exact `Uint32Array` word comparison.', '')
  lines.push('## Deliberate unreachable traps', '')
  for (const trap of data.unreachable_traps) lines.push(`- ${trap}`)
  lines.push('', 'These are reported as unreachable instead of manufacturing a false pixel witness. Structural authentication must still freeze the immediate unsigned constructor parent and the fact that the owner is reachable from `main`.', '')
  lines.push('## Regeneration', '', 'From `/Users/aayars/platform/noisemaker-for-cpp`:', '', '```sh', 'node docs/port-engineering/bitops/grain-parity/grain_parity_oracle_generator.mjs', 'node docs/port-engineering/bitops/grain-parity/grain_parity_oracle_generator.mjs --check', '```', '')
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
const generatorHash = sha256(fs.readFileSync(generatorPath))
const jsonSidecar = sidecar(sha256(json), outputPath)
const reportSidecar = sidecar(sha256(report), reportPath)
const generatorSidecar = sidecar(generatorHash, generatorPath)

if (process.argv.includes('--check')) {
  checkExact(outputPath, json, 'Grain parity JSON')
  checkExact(reportPath, report, 'Grain parity report')
  checkExact(`${outputPath}.sha256`, jsonSidecar, 'Grain parity JSON sidecar')
  checkExact(`${reportPath}.sha256`, reportSidecar, 'Grain parity report sidecar')
  checkExact(`${generatorPath}.sha256`, generatorSidecar, 'Grain parity generator sidecar')
  console.log(`Grain parity oracle ok (${data.cases.length} render cases, ${data.direct_scalar_recompute.records.length} direct uint fixtures, ${data.render_mutation_summary.length + data.direct_scalar_recompute.mutations.length} mutations)`)
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  fs.writeFileSync(`${outputPath}.sha256`, jsonSidecar)
  fs.writeFileSync(`${reportPath}.sha256`, reportSidecar)
  fs.writeFileSync(`${generatorPath}.sha256`, generatorSidecar)
  console.log(outputPath)
  console.log(reportPath)
}
