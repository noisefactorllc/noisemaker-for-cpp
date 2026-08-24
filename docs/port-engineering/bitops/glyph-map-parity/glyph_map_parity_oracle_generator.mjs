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
import { bindGlslKernel } from '../../../../../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../../../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../../../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const platformRoot = path.resolve(here, '../../../../..')
const cppRoot = path.join(platformRoot, 'noisemaker-for-cpp')
const cpuRoot = path.join(platformRoot, 'noisemaker-for-cpu')
const outputPath = path.join(here, 'glyph-map-parity-oracles.json')
const reportPath = path.join(here, 'glyph-map-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'glyph_map_frontend_probe.py')
const programKey = 'filter/glyphMap:glyphMap'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/glyphMap/glyphMap.glsl')
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

function i32FromWord(value) {
  return value | 0
}

function f32Bits(value) {
  const lane = new Float32Array([value])
  return u32Hex(new DataView(lane.buffer).getUint32(0, true))
}

// Purpose-built Glyph Map comparer. Float32 equality is raw lane-bit equality,
// including signed zero and NaN payloads. Pixel/channel diagnostics never
// weaken the exact byte and SHA-256 contracts.
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
  if (!(reference instanceof Uint32Array) || !(candidate instanceof Uint32Array)) {
    throw new TypeError('compareU32Words requires two Uint32Array values')
  }
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
  if (dimensions.float32.exact_f32_bits || dimensions.rgba8.exact_rgba8_bytes) {
    throw new Error('custom comparer accepted an equal-length dimension mismatch')
  }
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
if (sourceBytes.length !== 7838 || sha256(sourceBytes) !== '853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1') {
  throw new Error('pinned Glyph Map GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')
if ((sourceText.match(/row >> \(4 - x\)/g) ?? []).length !== 1 || (sourceText.match(/\) & 1/g) ?? []).length !== 1) {
  throw new Error('Glyph Map scalar bit-expression source census drift')
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory58') throw new Error('canonical Glyph Map factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 6749 || sha256(canonicalFactory.toString()) !== '2f26c6821b4cddd8eca6f742b5c6f9b4fb2aafc7660f9421965abb4af11d8028') {
  throw new Error('canonical Glyph Map factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog Glyph Map factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Glyph Map adapter override')

const expectedParams = {
  cellSize: { type: 'int', default: 16, uniform: 'cellSize', min: 4, max: 32 },
  colorMode: { type: 'int', default: 1, uniform: 'colorMode', choices: { mono: 0, rgb: 1 } },
  seed: { type: 'int', default: 1, uniform: 'seed', min: 1, max: 100 },
}
const effect = effectRecords.find((record) => record.id === 'filter/glyphMap')
if (!effect) throw new Error('Glyph Map metadata record missing')
for (const [name, expected] of Object.entries(expectedParams)) {
  for (const [field, value] of Object.entries(expected)) {
    if (JSON.stringify(effect.params?.[name]?.[field]) !== JSON.stringify(value)) throw new Error(`Glyph Map ${name}.${field} metadata drift`)
  }
}
if (effect.func !== 'glyphMap' || effect.kind !== 'filter' || effect.namespace !== 'filter' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'glyphMap') {
  throw new Error('Glyph Map effect/pass interface drift')
}

const frontendProcess = spawnSync('python3', [frontendProbePath], { cwd: cppRoot, encoding: 'utf8' })
if (frontendProcess.status !== 0) throw new Error(`frontend proof failed: ${frontendProcess.stderr || frontendProcess.stdout}`)
const frontendProof = JSON.parse(frontendProcess.stdout)
if (frontendProof.nodes?.length !== 2 || frontendProof.global_constant?.read_count !== 3 || frontendProof.current_frontier?.diagnostic_bypass?.validator !== 'pass' || frontendProof.current_frontier?.diagnostic_bypass?.emitter !== 'pass') {
  throw new Error('Glyph Map frontend proof contract drift')
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

function flatGlyphSurface(width, height, glyphIndex) {
  const value = f(glyphIndex === 15 ? 1 : (glyphIndex + 0.25) / 16)
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i += 4) {
    data[i] = value
    data[i + 1] = value
    data[i + 2] = value
    data[i + 3] = f(((i / 4) % 17 + 1) / 19)
  }
  data[3] = -0
  return new Surface(width, height, data)
}

const generalCases = [
  { name: 'mono-min-cell-pattern', width: 19, height: 15, phase: 1, cellSize: 4, seed: 1, colorMode: 0, renderScale: 1, time: 0, frame: 0, externalSeed: 0, coverage: ['mono branch', 'minimum cell size', 'multiple cells', 'landscape'] },
  { name: 'rgb-default-pattern', width: 19, height: 15, phase: 2, cellSize: 16, seed: 1, colorMode: 1, renderScale: 1, time: 0, frame: 0, externalSeed: 0, coverage: ['RGB branch', 'default controls', 'asymmetric color'] },
  { name: 'rgb-variant-two-seed', width: 23, height: 17, phase: 3, cellSize: 7, seed: 2, colorMode: 1, renderScale: 1, time: 0, frame: 0, externalSeed: 1, coverage: ['variant decrement path', 'multiple cell hashes'] },
  { name: 'scale-zero-cs-one', width: 7, height: 11, phase: 4, cellSize: 4, seed: 100, colorMode: 0, renderScale: 0, time: 0.5, frame: 17, externalSeed: 99, coverage: ['max metadata seed', 'renderScale zero', 'cs minimum one', 'portrait'] },
  { name: 'tiled-noninteger-scale', width: 11, height: 9, phase: 5, cellSize: 7, seed: 37, colorMode: 1, renderScale: 1.5, time: 0.25, frame: 9, externalSeed: 123456789, tileOffset: [7, 5], fullResolution: [31, 23], coverage: ['tile offset', 'sample UV clamp', 'noninteger renderScale'] },
  { name: 'tiled-cs-cap-1024', width: 5, height: 7, phase: 6, cellSize: 32, seed: 3, colorMode: 0, renderScale: 32, time: 0, frame: 0, externalSeed: 1, tileOffset: [1, 1], fullResolution: [9, 9], sameAs: 'tiled-cs-cap-512', coverage: ['tiled cell-size cap above boundary'] },
  { name: 'tiled-cs-cap-512', width: 5, height: 7, phase: 6, cellSize: 32, seed: 3, colorMode: 0, renderScale: 16, time: 0, frame: 0, externalSeed: 1, tileOffset: [1, 1], fullResolution: [9, 9], coverage: ['tiled cell-size cap boundary'] },
  { name: 'external-context-base', width: 13, height: 8, phase: 7, cellSize: 5, seed: 11, colorMode: 1, renderScale: 1, time: 0, frame: 0, externalSeed: 0, coverage: ['external context identity reference'] },
  { name: 'external-context-extreme', width: 13, height: 8, phase: 7, cellSize: 5, seed: 11, colorMode: 1, renderScale: 1, time: 16777216, frame: 4294967295, externalSeed: 4294967295, sameAs: 'external-context-base', coverage: ['time/frame/external pass seed unused'] },
]

const glyphCases = Array.from({ length: 16 }, (_, glyphIndex) => ({
  name: `glyph-${glyphIndex.toString().padStart(2, '0')}-full-cell`,
  width: 35,
  height: 35,
  flatGlyph: glyphIndex,
  cellSize: 35,
  seed: 3,
  colorMode: 0,
  renderScale: 1,
  time: 0,
  frame: 0,
  externalSeed: 0,
  coverage: [`glyph index ${glyphIndex}`, 'variant zero at sole cell', 'all x=0..4', 'all y=0..6'],
}))

const cases = [...generalCases, ...glyphCases]

function compileMutant(name, from, to, expectedRenderRelation = 'diverge') {
  const source = canonicalFactory.toString()
  const pieces = source.split(from)
  if (pieces.length !== 2) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
  const mutatedText = `${pieces[0]}${to}${pieces[1]}`
  const factory = Function(`"use strict"; return (${mutatedText});`)()
  return { name, factory, expectedRenderRelation, factory_sha256: sha256(mutatedText), anchor_sha256: sha256(from), replacement_sha256: sha256(to) }
}

const bitLine = 'var bit = (row >> (4 - x)) & 1;'
const renderMutants = [
  compileMutant('mask-and-replaced-by-or', bitLine, 'var bit = (row >> (4 - x)) | 1;'),
  compileMutant('right-shift-replaced-by-left', bitLine, 'var bit = (row << (4 - x)) & 1;'),
  compileMutant('mask-materialized-before-shift', bitLine, 'var bit = (row & 1) >> (4 - x);'),
  compileMutant('arithmetic-shift-replaced-by-logical', bitLine, 'var bit = (row >>> (4 - x)) & 1;', 'equal-under-authenticated-range'),
  compileMutant('color-mode-branch-inverted', 'if (colorMode > 0) {', 'if (colorMode <= 0) {'),
  compileMutant('variant-two-decrement-omitted', 'glyphIdx = glyphIdx - 1;', 'glyphIdx = glyphIdx;'),
]

function makeInput(definition) {
  return definition.flatGlyph === undefined
    ? patternedSurface(definition.width, definition.height, definition.phase)
    : flatGlyphSurface(definition.width, definition.height, definition.flatGlyph)
}

function render(factory, definition) {
  const input = makeInput(definition)
  const before = input.data.slice()
  const uniforms = {
    cellSize: definition.cellSize,
    seed: definition.seed,
    colorMode: definition.colorMode,
    renderScale: f(definition.renderScale),
  }
  const tileOffset = definition.tileOffset ? new Float32Array(definition.tileOffset.map(f)) : undefined
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution.map(f)) : undefined
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: definition.frame,
    seed: definition.externalSeed,
    uniforms,
    textures: { inputTex: input },
    tileOffset,
    fullResolution,
  })
  if (bindings.cellSize !== definition.cellSize || bindings.seed !== definition.seed || bindings.colorMode !== definition.colorMode || f32Bits(bindings.renderScale) !== f32Bits(uniforms.renderScale)) {
    throw new Error(`${definition.name}: uniform materialization drift`)
  }
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.externalSeed })
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
  let nonfinite = 0
  for (const value of surface.data) if (!Number.isFinite(value)) nonfinite += 1
  if (nonfinite !== 0) throw new Error('nonfinite Glyph Map output')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    probes: selectedProbes(surface),
  }
}

function extractGlyphRows(surface) {
  if (surface.width !== 35 || surface.height !== 35) throw new Error('glyph row extraction requires a 35x35 single-cell render')
  const rows = []
  for (let logicalRow = 0; logicalRow < 7; logicalRow += 1) {
    const topDownY = logicalRow * 5 + 2
    let row = ''
    for (let x = 0; x < 5; x += 1) {
      const topDownX = x * 7 + 3
      const value = surface.data[(topDownY * 35 + topDownX) * 4]
      if (value !== 0 && value !== 1) throw new Error(`glyph extraction saw non-binary value ${value}`)
      row += value === 1 ? '#' : '.'
    }
    rows.push(row)
  }
  return rows
}

const directDefinitions = [
  [0x00000000, 0, 0x00000001],
  [0x00000001, 0, 0x00000001],
  [0x7fffffff, 1, 0x00000001],
  [0x80000000, 0, 0x00000001],
  [0x80000000, 1, 0x00000001],
  [0x80000000, 31, 0x00000001],
  [0xffffffff, 1, 0x00000001],
  [0xffffffff, 31, 0x00000001],
  [0xffffffff, 32, 0x00000001],
  [0xffffffff, 33, 0x00000001],
  [0xffffffff, -1, 0x00000001],
  [0x80000001, 4, 0x00000001],
  [0xf0000000, 4, 0x000000ff],
  [0x12345678, 4, 0x000000ff],
  [0x12345678, 36, 0x000000ff],
  [0xaaaaaaaa, 63, 0x55555555],
  [0xdeadbeef, 4294967295, 0xffffffff],
]

const narrowingDefinitions = [
  ['positive-zero', 0],
  ['negative-zero', -0],
  ['positive-one', 1],
  ['negative-one', -1],
  ['positive-fraction-truncates', 3.9],
  ['negative-fraction-truncates', -3.9],
  ['int32-max', 2147483647],
  ['int32-sign-bit', 2147483648],
  ['uint32-max', 4294967295],
  ['uint32-wrap', 4294967296],
  ['uint32-wrap-plus-one', 4294967297],
  ['negative-int32-underflow', -2147483649],
  ['negative-uint32-wrap-minus-one', -4294967297],
  ['nan', Number.NaN],
  ['positive-infinity', Number.POSITIVE_INFINITY],
  ['negative-infinity', Number.NEGATIVE_INFINITY],
]

function independentToUint32(value) {
  if (!Number.isFinite(value) || value === 0) return 0
  const truncated = value < 0 ? Math.ceil(value) : Math.floor(value)
  const modulus = 4294967296
  return ((truncated % modulus) + modulus) % modulus
}

function buildNumericNarrowingEvidence() {
  const canonicalWords = new Uint32Array(narrowingDefinitions.length)
  const records = narrowingDefinitions.map(([name, value], index) => {
    const actualUint = value >>> 0
    const actualInt = value | 0
    const independentUint = independentToUint32(value)
    const independentInt = independentUint >= 2147483648 ? independentUint - 4294967296 : independentUint
    if (actualUint !== independentUint || actualInt !== independentInt) throw new Error(`${name}: independent ToInt32/ToUint32 disagreement`)
    canonicalWords[index] = actualUint
    return {
      name,
      input_number: Number.isFinite(value) ? value : String(value),
      input_is_negative_zero: Object.is(value, -0),
      javascript_to_int32_number: actualInt,
      javascript_to_uint32_number: actualUint,
      shared_low_word_le: u32Hex(actualUint),
      independent_to_int32_number: independentInt,
      independent_to_uint32_number: independentUint,
    }
  })
  const roundFirst = new Uint32Array(narrowingDefinitions.map(([, value]) => Number.isFinite(value) ? Math.round(value) >>> 0 : 0))
  const saturate = new Uint32Array(narrowingDefinitions.map(([, value]) => {
    if (!Number.isFinite(value)) return 0
    const truncated = value < 0 ? Math.ceil(value) : Math.floor(value)
    return Math.min(4294967295, Math.max(0, truncated)) >>> 0
  }))
  const float32First = new Uint32Array(narrowingDefinitions.map(([, value]) => Math.fround(value) >>> 0))
  const mutations = [
    ['round-instead-of-truncate', roundFirst],
    ['saturate-instead-of-modulo', saturate],
    ['float32-narrow-before-to-int32', float32First],
  ].map(([name, candidate]) => {
    const comparison = compareU32Words(canonicalWords, candidate)
    if (comparison.exact_u32_words) throw new Error(`${name}: numeric narrowing mutation escaped`)
    return { name, exact_comparer_discriminated: true, comparison }
  })
  return {
    semantics: 'ECMAScript bitwise operands truncate toward zero, reduce modulo 2^32, expose signed ToInt32 or unsigned ToUint32 numeric views over the same low word, and map nonfinite values to zero.',
    records,
    aggregate_low_words_le_sha256: sha256(bytes(canonicalWords)),
    mutations,
  }
}

function bigintArithmeticShift(word, count) {
  const signed = BigInt.asIntN(32, BigInt(word >>> 0))
  const effective = Number(BigInt.asUintN(32, BigInt(count)) & 31n)
  return Number(BigInt.asUintN(32, signed >> BigInt(effective)))
}

function bigintMask(word, mask) {
  return Number(BigInt.asUintN(32, BigInt(word >>> 0) & BigInt(mask >>> 0)))
}

function buildDirectEvidence() {
  const canonicalShift = new Uint32Array(directDefinitions.length)
  const canonicalMasked = new Uint32Array(directDefinitions.length)
  const records = directDefinitions.map(([leftWord, count, maskWord], index) => {
    const actualShift = (leftWord | 0) >> count
    const independentShiftWord = bigintArithmeticShift(leftWord, count)
    if ((actualShift >>> 0) !== independentShiftWord) throw new Error(`independent arithmetic shift disagreement at direct fixture ${index}`)
    const actualMasked = actualShift & (maskWord | 0)
    const independentMaskedWord = bigintMask(independentShiftWord, maskWord)
    if ((actualMasked >>> 0) !== independentMaskedWord) throw new Error(`independent mask disagreement at direct fixture ${index}`)
    canonicalShift[index] = actualShift >>> 0
    canonicalMasked[index] = actualMasked >>> 0
    return {
      index,
      left_word_le: u32Hex(leftWord),
      left_i32: leftWord | 0,
      source_shift_count: count,
      effective_shift_count: count >>> 0 & 31,
      mask_word_le: u32Hex(maskWord),
      mask_i32: maskWord | 0,
      javascript_arithmetic_shift_i32: actualShift,
      javascript_arithmetic_shift_word_le: u32Hex(actualShift),
      independent_bigint_shift_word_le: u32Hex(independentShiftWord),
      javascript_masked_i32: actualMasked,
      javascript_masked_word_le: u32Hex(actualMasked),
      independent_bigint_masked_word_le: u32Hex(independentMaskedWord),
    }
  })

  const logicalShift = new Uint32Array(directDefinitions.map(([word, count]) => word >>> count))
  const maskBeforeShift = new Uint32Array(directDefinitions.map(([word, count, mask]) => ((word | 0) & (mask | 0)) >> count))
  const maskAsOr = new Uint32Array(directDefinitions.map(([word, count, mask]) => (((word | 0) >> count) | (mask | 0)) >>> 0))
  const maskAsXor = new Uint32Array(directDefinitions.map(([word, count, mask]) => (((word | 0) >> count) ^ (mask | 0)) >>> 0))
  const clampedCount = new Uint32Array(directDefinitions.map(([word, count]) => {
    const clamped = Math.max(0, Math.min(31, count))
    return bigintArithmeticShift(word, clamped)
  }))
  const mutations = [
    ['arithmetic-shift-replaced-by-logical', canonicalShift, logicalShift],
    ['mask-materialized-before-shift', canonicalMasked, maskBeforeShift],
    ['mask-and-replaced-by-or', canonicalMasked, maskAsOr],
    ['mask-and-replaced-by-xor', canonicalMasked, maskAsXor],
    ['javascript-count-mask-replaced-by-clamp', canonicalShift, clampedCount],
  ].map(([name, reference, candidate]) => {
    const comparison = compareU32Words(reference, candidate)
    if (comparison.exact_u32_words) throw new Error(`${name}: direct mutation escaped`)
    return { name, exact_comparer_discriminated: true, comparison }
  })

  return {
    semantics: {
      operand_narrowing: 'JavaScript bitwise operators apply ToInt32 to the left/mask operands; records begin from exact low-32-bit words and expose the signed Number views.',
      right_shift: 'JavaScript >> is sign-propagating arithmetic shift.',
      shift_count: 'JavaScript applies ToUint32 to the count and masks it with 31, including negative and counts >= 32.',
      result: 'Both >> and & produce signed int32 Number results; word fields preserve their exact two-complement bits.',
      materialization_order: '(row >> count) & mask; shifting the masked row is a distinct rejected computation.',
    },
    records,
    aggregate_shift_u32_le_sha256: sha256(bytes(canonicalShift)),
    aggregate_masked_u32_le_sha256: sha256(bytes(canonicalMasked)),
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
    return {
      name: definition.name,
      dimensions: { width: definition.width, height: definition.height },
      controls: {
        cell_size: definition.cellSize,
        effect_seed: definition.seed,
        color_mode: definition.colorMode,
        render_scale: f(definition.renderScale),
        render_scale_bits_le: f32Bits(definition.renderScale),
        time: f(definition.time),
        frame: definition.frame,
        external_pass_seed: definition.externalSeed,
        tile_offset: Array.from(canonicalFirst.bindings.tileOffset),
        full_resolution: Array.from(canonicalFirst.bindings.fullResolution),
      },
      coverage: definition.coverage,
      target_glyph_index: definition.flatGlyph ?? null,
      extracted_glyph_top_down_rows: definition.flatGlyph === undefined ? null : extractGlyphRows(canonicalFirst.output),
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

  const requiredRenderWitnesses = {
    'mask-and-replaced-by-or': ['glyph-01-full-cell', 'glyph-14-full-cell'],
    'right-shift-replaced-by-left': ['glyph-03-full-cell', 'glyph-14-full-cell'],
    'mask-materialized-before-shift': ['glyph-03-full-cell', 'glyph-14-full-cell'],
    'color-mode-branch-inverted': ['mono-min-cell-pattern', 'rgb-default-pattern'],
    'variant-two-decrement-omitted': ['rgb-variant-two-seed'],
  }
  const renderMutationSummary = renderMutants.map((mutant) => {
    const witnesses = caseResults.filter((record) => !record.mutation_comparisons[mutant.name].float32.exact_f32_bits).map((record) => record.name)
    if (mutant.expectedRenderRelation === 'equal-under-authenticated-range') {
      if (witnesses.length !== 0) throw new Error(`${mutant.name}: arithmetic/logical shifts diverged despite nonnegative range proof`)
    } else {
      for (const required of requiredRenderWitnesses[mutant.name]) {
        if (!witnesses.includes(required)) throw new Error(`${mutant.name}: required witness ${required} did not diverge`)
      }
    }
    return {
      name: mutant.name,
      expected_render_relation: mutant.expectedRenderRelation,
      factory_sha256: mutant.factory_sha256,
      anchor_sha256: mutant.anchor_sha256,
      replacement_sha256: mutant.replacement_sha256,
      required_witnesses: requiredRenderWitnesses[mutant.name] ?? [],
      all_divergent_cases: witnesses,
      exact_comparer_discriminated: witnesses.length > 0,
    }
  })

  const glyphTruthTable = caseResults.filter((record) => record.target_glyph_index !== null).map((record) => ({
    glyph_index: record.target_glyph_index,
    top_down_rows: record.extracted_glyph_top_down_rows,
    f32_sha256: record.output.f32_sha256,
    rgba8_sha256: record.output.rgba8_sha256,
  }))
  if (glyphTruthTable.length !== 16 || glyphTruthTable[0].top_down_rows.some((row) => row !== '.....') || glyphTruthTable[15].top_down_rows.some((row) => row !== '#####')) {
    throw new Error('full glyph truth-table boundary coverage drift')
  }

  return {
    schema: 'noisemaker-for-cpp.glyph-map.pixel-parity-and-signed-shift-oracle.v1',
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
    javascript_materialization_contract: {
      glyph_expression: '(row >> (4 - x)) & 1',
      range: 'render-reachable row is 0..31 and x is 0..4, hence count is 0..4',
      narrowing: 'the shipped factory uses native JavaScript >> and &, which ToInt32 both operands and produce a signed int32 Number',
      shift: 'native >> is arithmetic/sign-propagating; >>> is not used',
      render_equivalence_boundary: 'because render-reachable row is nonnegative, >> and >>> are pixel-equivalent; direct signed fixtures are authoritative for the language distinction',
      cpp_scope: 'admit the exact authenticated nonnegative node only; this oracle does not authorize general negative signed right shift',
      texture_coordinates: 'GLSL fragment coordinates are bottom-left while Surface/comparer diagnostics are top-down',
    },
    metadata_contract: expectedParams,
    fixture: {
      general_input: 'asymmetric colored top-down Float32 RGBA with signed zero and finite out-of-range edge lanes',
      glyph_input: 'one 35x35 constant-luma cell per glyph index, seed 3 giving variant zero at cell (0,0)',
      comparer: 'exact Float32-bit and RGBA8-byte custom comparer with first pixel/channel diagnostics',
      repeated_render_count: 2,
    },
    comparer_self_tests: comparerSelfTests(),
    numeric_narrowing: buildNumericNarrowingEvidence(),
    direct_signed_shift_and_mask: buildDirectEvidence(),
    glyph_truth_table: glyphTruthTable,
    cases: caseResults,
    render_mutation_summary: renderMutationSummary,
    contract_negatives: frontendProof.contract_negatives,
  }
}

function makeReport(data) {
  const lines = [
    '# Glyph Map signed-shift, mask, and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/glyphMap:glyphMap`. Exact Float32 and RGBA8 hashes cover canonical and public execution, every glyph, both color branches, control boundaries, variant selection, tiling, repeatability, and input immutability. A separate typed-frontend proof freezes the exact global/shift/mask/return identities.', '',
    '## Frozen authority', '',
    `- Upstream snapshot revision: \`${data.upstream_revision}\``,
    `- Corpus revision: \`${data.corpus_revision}\``,
    `- GLSL source: ${data.provenance.source_raw_bytes} bytes, SHA-256 \`${data.provenance.source_sha256}\``,
    `- Canonical factory: \`${data.provenance.canonical_factory_name}\`, ${data.provenance.canonical_factory_to_string_bytes} bytes, SHA-256 \`${data.provenance.canonical_factory_to_string_sha256}\``,
    '- Public catalog identity is exactly the canonical factory; no adapter override exists.', '',
    '## Captured C++ frontend boundary', '',
    `- Validator and emitter first error: \`${data.frontend_proof.current_frontier.validator_first_error}\``,
    `- Replacing only the exact mask node exposes \`${data.frontend_proof.current_frontier.after_mask_bypass_validator}\`.`,
    `- Replacing only both scalar bit operators in memory makes validator and emitter pass; the diagnostic C++ is ${data.frontend_proof.current_frontier.diagnostic_bypass.rendered_cpp_bytes} bytes with SHA-256 \`${data.frontend_proof.current_frontier.diagnostic_bypass.rendered_cpp_sha256}\`.`,
    '- The proposed `glyph-map-nonnegative-int-shift-v1` profile authenticates `GLYPH_COUNT`, its three reads, the sole signed shift, its literal-one mask parent, the local `bit` materialization, and the direct `float(bit)` return. It does not establish general signed shifting or masking.', '',
    '## JavaScript signed-word contract', '',
    `The ${data.numeric_narrowing.records.length} numeric fixtures freeze ToInt32/ToUint32 truncation, modulo wrap, signed/unsigned views, signed zero, and nonfinite-to-zero behavior; their low words hash to \`${data.numeric_narrowing.aggregate_low_words_le_sha256}\`. Mutations reject rounding, saturation, and premature Float32 narrowing.`,
    '',
    `The ${data.direct_signed_shift_and_mask.records.length} word fixtures cover bit-31 clear/set words, -1, counts 0/1/31/32/33/-1/2^32-1, and nontrivial masks. Shipped JavaScript and independent BigInt two-complement recomputation agree exactly. Shift words hash to \`${data.direct_signed_shift_and_mask.aggregate_shift_u32_le_sha256}\`; post-mask words hash to \`${data.direct_signed_shift_and_mask.aggregate_masked_u32_le_sha256}\`. Direct mutations reject logical shift, masking before shifting, OR/XOR masks, and count clamping.`,
    '',
    'Pixel renders intentionally cannot distinguish `>>` from `>>>`: authenticated glyph rows are nonnegative 0..31 and counts are 0..4. The logical-shift render mutant must therefore remain exactly equal while the direct signed fixtures must diverge. That division is part of the contract, not a coverage gap.', '',
    '## Full glyph truth table (top-down rendered rows)', '',
    '| Glyph | Rows | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| ---: | --- | --- | --- |',
  ]
  for (const glyph of data.glyph_truth_table) lines.push(`| ${glyph.glyph_index} | \`${glyph.top_down_rows.join('/')}\` | \`${glyph.f32_sha256}\` | \`${glyph.rgba8_sha256}\` |`)
  lines.push('', '## General render cases', '', '| Case | Size | Cell | Seed | Mode | Scale | Tile/full | Float32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |')
  for (const record of data.cases.filter((item) => item.target_glyph_index === null)) {
    const c = record.controls
    lines.push(`| ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${c.cell_size} | ${c.effect_seed} | ${c.color_mode} | ${c.render_scale} | ${c.tile_offset.join(',')}/${c.full_resolution.join(',')} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every render case requires exact repeated-run identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. The cap pair and external-context pair are required exact identities.', '')
  lines.push('## Render mutation discrimination', '', '| Mutation | Expected render relation | Required witnesses | All divergent cases |', '| --- | --- | --- | --- |')
  for (const mutation of data.render_mutation_summary) lines.push(`| ${mutation.name} | ${mutation.expected_render_relation} | ${mutation.required_witnesses.join(', ')} | ${mutation.all_divergent_cases.join(', ') || '(none, required)'} |`)
  lines.push('', 'Frontend contract negatives reject wrong key/profile/hash, global value drift, mask/count drift, an extra signed shift, and return-route drift.', '')
  lines.push('## Regeneration', '', 'From the repository root. Ordinary checks remain durable after admission; `--live-frontier` separately observes the current production gate:', '', '```sh', 'python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --check', 'python3 docs/port-engineering/bitops/glyph-map-parity/glyph_map_frontend_probe.py --live-frontier', 'node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs', 'node docs/port-engineering/bitops/glyph-map-parity/glyph_map_parity_oracle_generator.mjs --check', '```', '')
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
  checkExact(outputPath, json, 'Glyph Map parity JSON')
  checkExact(reportPath, report, 'Glyph Map parity report')
  checkExact(`${outputPath}.sha256`, jsonSidecar, 'Glyph Map parity JSON sidecar')
  checkExact(`${reportPath}.sha256`, reportSidecar, 'Glyph Map parity report sidecar')
  checkExact(`${generatorPath}.sha256`, generatorSidecar, 'Glyph Map generator sidecar')
  checkExact(`${frontendProbePath}.sha256`, probeSidecar, 'Glyph Map frontend probe sidecar')
  console.log(`Glyph Map parity oracle ok (${data.cases.length} render cases, ${data.numeric_narrowing.records.length + data.direct_signed_shift_and_mask.records.length} direct fixtures, ${data.render_mutation_summary.length + data.numeric_narrowing.mutations.length + data.direct_signed_shift_and_mask.mutations.length} mutations)`)
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
