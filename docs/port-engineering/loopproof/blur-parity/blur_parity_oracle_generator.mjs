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
const outputPath = path.join(here, 'blur-parity-oracles.json')
const reportPath = path.join(here, 'blur-parity-oracle-report.md')
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'

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

function f64Bits(value) {
  const lane = new Float64Array([value])
  return `0x${new DataView(lane.buffer).getBigUint64(0, true).toString(16).padStart(16, '0')}`
}

function nextDown(value) {
  if (Number.isNaN(value) || value === -Infinity) return value
  if (value === 0) return -Number.MIN_VALUE
  const lane = new Float64Array([value])
  const bits = new BigUint64Array(lane.buffer)
  bits[0] += value > 0 ? -1n : 1n
  return lane[0]
}

// Purpose-built exact comparer for blur parity. Equality is raw Float32 bit
// equality (including signed zero and NaN payloads). Pixel/channel diagnostics
// are additive; they never weaken the byte and SHA-256 contracts.
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
  const referenceBits = new Uint32Array(reference.data.buffer, reference.data.byteOffset, reference.data.length)
  const candidateBits = new Uint32Array(candidate.data.buffer, candidate.data.byteOffset, candidate.data.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let i = 0; i < reference.data.length; i += 1) {
    if (referenceBits[i] === candidateBits[i]) continue
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
        reference_bits_le: `0x${referenceBits[i].toString(16).padStart(8, '0')}`,
        candidate_bits_le: `0x${candidateBits[i].toString(16).padStart(8, '0')}`,
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

const provenanceFiles = {
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  adapter_index: ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', '8579de7f8d3ff35a71c35c2c5e32296d0f71ffef1e790db9736f99ab04969936'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
  sampler: ['src/runtime/sampler.js', '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328'],
}

for (const [name, [relativePath, expectedHash]] of Object.entries(provenanceFiles)) {
  const actualHash = sha256(fs.readFileSync(path.join(cpuRoot, relativePath)))
  if (actualHash !== expectedHash) throw new Error(`${name} provenance drift: ${actualHash}`)
}

const effect = effectRecords.find((record) => record.id === 'filter/blur')
if (!effect) throw new Error('filter/blur metadata record missing')

const immediatelyBelow64 = nextDown(64)

const programs = [
  {
    id: 'blurH',
    key: 'filter/blur:blurH',
    axis: 'radiusX',
    sourceFile: 'blurH.glsl',
    sourceBytes: 1120,
    sourceSha256: 'c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc',
    factoryName: 'canonicalFactory24',
    factoryBytes: 2056,
    factorySha256: 'a735ebfa7bbdfd8da062c52f46dd2c3143be5526dfb2be805581437d21134d99',
    axisOffsetAnchor: 'var offset = new $runtime.PooledFloat32Array([(i) * texelSize[0], 0]);',
    axisOffsetMutation: 'var offset = new $runtime.PooledFloat32Array([0, (i) * texelSize[1]]);',
    cases: [
      { name: 'radius0-axis0-nearest', width: 9, height: 5, phase: 1, axisValue: 0, scale: 1, filter: 'nearest' },
      { name: 'radius0-scale0-linear-degenerate-width', width: 1, height: 7, phase: 2, axisValue: 50, scale: 0, filter: 'linear' },
      { name: 'radius1-axis1-nearest', width: 11, height: 6, phase: 3, axisValue: 1, scale: 1, filter: 'nearest' },
      { name: 'radius3-fractional-scale-linear', width: 10, height: 7, phase: 4, axisValue: 7, scale: 0.5, filter: 'linear' },
      { name: 'radius12-intermediate-nearest', width: 13, height: 8, phase: 5, axisValue: 12.75, scale: 1, filter: 'nearest' },
      { name: 'radius50-axis-max-linear', width: 14, height: 9, phase: 6, axisValue: 50, scale: 1, filter: 'linear' },
      { name: 'radius12-degenerate-width-nearest', width: 1, height: 8, phase: 7, axisValue: 24, scale: 0.5, filter: 'nearest' },
      { name: 'radius63-binary64-nextdown-large-scale', width: 8, height: 6, phase: 8, axisValue: 1, scale: immediatelyBelow64, filter: 'nearest', binary64Discriminator: 'correct-accept-operand-quantized-reject' },
    ],
  },
  {
    id: 'blurV',
    key: 'filter/blur:blurV',
    axis: 'radiusY',
    sourceFile: 'blurV.glsl',
    sourceBytes: 1118,
    sourceSha256: 'cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b',
    factoryName: 'canonicalFactory25',
    factoryBytes: 2056,
    factorySha256: '439400fdbb3496fb6399769f5652ab7eb57f71a8e3d770bbdd111c8d2220f796',
    axisOffsetAnchor: 'var offset = new $runtime.PooledFloat32Array([0, (i) * texelSize[1]]);',
    axisOffsetMutation: 'var offset = new $runtime.PooledFloat32Array([(i) * texelSize[0], 0]);',
    cases: [
      { name: 'radius0-axis0-nearest', width: 6, height: 9, phase: 11, axisValue: 0, scale: 1, filter: 'nearest' },
      { name: 'radius0-scale0-linear-degenerate-height', width: 7, height: 1, phase: 12, axisValue: 50, scale: 0, filter: 'linear' },
      { name: 'radius1-axis1-nearest', width: 6, height: 11, phase: 13, axisValue: 1, scale: 1, filter: 'nearest' },
      { name: 'radius3-fractional-scale-linear', width: 7, height: 10, phase: 14, axisValue: 7, scale: 0.5, filter: 'linear' },
      { name: 'radius12-intermediate-nearest', width: 8, height: 13, phase: 15, axisValue: 12.75, scale: 1, filter: 'nearest' },
      { name: 'radius50-axis-max-linear', width: 9, height: 14, phase: 16, axisValue: 50, scale: 1, filter: 'linear' },
      { name: 'radius12-degenerate-height-nearest', width: 8, height: 1, phase: 17, axisValue: 24, scale: 0.5, filter: 'nearest' },
      { name: 'radius63-binary64-nextdown-large-scale', width: 6, height: 8, phase: 18, axisValue: 1, scale: immediatelyBelow64, filter: 'nearest', binary64Discriminator: 'correct-accept-operand-quantized-reject' },
    ],
  },
]

function admitBinary64(axisValue, scale) {
  if (typeof axisValue !== 'number' || typeof scale !== 'number') return { accepted: false, reason: 'bindings must be numbers' }
  if (!Number.isFinite(axisValue) || axisValue < 0 || axisValue > 50) return { accepted: false, reason: 'axis must be finite and in [0,50]' }
  if (!Number.isFinite(scale) || scale < 0) return { accepted: false, reason: 'renderScale must be finite and nonnegative' }
  const product = axisValue * scale
  if (!(product >= 0 && product < 64)) return { accepted: false, reason: 'binary64 product must be in [0,64)', product }
  return { accepted: true, reason: null, product, radius: Math.trunc(product), maximum_visits: Math.trunc(product) > 0 ? 2 * Math.trunc(product) + 1 : 0 }
}

// Deliberately faulty boundary model: quantize each operand to Float32, then
// multiply those quantized values using JavaScript's binary64 arithmetic. This
// is distinct from the pixel mutation that rounds only the completed product.
function admitFaultyFloat32OperandsBinary64Product(axisValue, scale) {
  if (typeof axisValue !== 'number' || typeof scale !== 'number') return { accepted: false }
  const axisF32 = Math.fround(axisValue)
  const scaleF32 = Math.fround(scale)
  const product = axisF32 * scaleF32
  const accepted = Number.isFinite(axisF32) && axisF32 >= 0 && axisF32 <= 50 && Number.isFinite(scaleF32) && scaleF32 >= 0 && product >= 0 && product < 64
  return { accepted, axis_f32: axisF32, scale_f32: scaleF32, product, radius: accepted ? Math.trunc(product) : null }
}

const boundaryDefinitions = [
  { name: 'axis-zero', axisValue: 0, scale: 1, expected: true, expectedRadius: 0 },
  { name: 'scale-zero', axisValue: 50, scale: 0, expected: true, expectedRadius: 0 },
  { name: 'radius-one', axisValue: 1, scale: 1, expected: true, expectedRadius: 1 },
  { name: 'fractional-truncates-to-three', axisValue: 7, scale: 0.5, expected: true, expectedRadius: 3 },
  { name: 'metadata-axis-maximum', axisValue: 50, scale: 1, expected: true, expectedRadius: 50 },
  { name: 'immediately-below-64-operand-quantized-false-reject', axisValue: 1, scale: immediatelyBelow64, expected: true, expectedRadius: 63, operandQuantizedExpected: false },
  { name: 'exactly-64', axisValue: 1, scale: 64, expected: false },
  { name: 'exactly-64-operand-quantized-false-accept', axisValue: 50, scale: 1.28, expected: false, operandQuantizedExpected: true },
  { name: 'negative-axis', axisValue: -Number.MIN_VALUE, scale: 1, expected: false },
  { name: 'axis-above-metadata-max', axisValue: nextDown(51), scale: 1, expected: false },
  { name: 'negative-scale', axisValue: 1, scale: -Number.MIN_VALUE, expected: false },
  { name: 'axis-positive-infinity', axisValue: Infinity, scale: 1, expected: false },
  { name: 'scale-positive-infinity', axisValue: 1, scale: Infinity, expected: false },
  { name: 'axis-nan', axisValue: Number.NaN, scale: 1, expected: false },
  { name: 'scale-nan', axisValue: 1, scale: Number.NaN, expected: false },
]

function verifyProgram(program) {
  const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/blur', program.sourceFile)
  const source = fs.readFileSync(sourcePath)
  if (source.length !== program.sourceBytes || sha256(source) !== program.sourceSha256) throw new Error(`${program.id}: pinned GLSL source drift`)

  const canonical = canonicalKernelFactories[program.key]
  const publicFactory = kernelFactories.get(program.key)
  if (!canonical || canonical.name !== program.factoryName) throw new Error(`${program.id}: canonical factory identity drift`)
  const factoryText = canonical.toString()
  if (Buffer.byteLength(factoryText) !== program.factoryBytes || sha256(factoryText) !== program.factorySha256) throw new Error(`${program.id}: canonical factory body drift`)
  if (publicFactory !== canonical) throw new Error(`${program.id}: public catalog factory is not the canonical factory identity`)
  if (canonicalAdapterFactories[program.key] !== undefined) throw new Error(`${program.id}: unexpected adapter override`)

  const metadata = effect.params?.[program.axis]
  const expectedMetadata = { type: 'float', default: 5, uniform: program.axis, min: 0, max: 50, zero: 0 }
  if (JSON.stringify(metadata) !== JSON.stringify(expectedMetadata)) throw new Error(`${program.id}: ${program.axis} metadata drift`)
  return { ...program, canonical, publicFactory, factoryText, sourcePath }
}

const verifiedPrograms = programs.map(verifyProgram)

function patternedSurface(width, height, phase, filter) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      // Asymmetric channels plus explicit edge impulses distinguish horizontal
      // from vertical offsets and make clamp-to-edge behavior visible.
      data[i] = Math.fround((((31 * x + 17 * y + 19 * phase + 3) % 101) + 1) / 103)
      data[i + 1] = Math.fround((((13 * x + 43 * y + 23 * phase + 5) % 97) + 2) / 101)
      data[i + 2] = Math.fround((((47 * x + 7 * y + 29 * phase + 11) % 89) + 3) / 97)
      data[i + 3] = Math.fround((((5 * x + 19 * y + 7 * phase) % 31) + 5) / 41)
      if (x === 0) data[i] = Math.fround(0.97 - 0.013 * (y % 5))
      if (x === width - 1) data[i + 1] = Math.fround(0.91 - 0.017 * (y % 7))
      if (y === 0) data[i + 2] = Math.fround(0.89 - 0.011 * (x % 6))
      if (y === height - 1) data[i + 3] = Math.fround(0.87 - 0.019 * (x % 4))
    }
  }
  const surface = new Surface(width, height, data)
  if (filter === 'linear') surface.filter = 'linear'
  return surface
}

function makeBindings(program, definition, input) {
  const uniforms = { [program.axis]: definition.axisValue, renderScale: definition.scale }
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    uniforms,
    textures: { inputTex: input },
    tileOffset: new Float32Array([2.25, -1.5]),
    fullResolution: new Float32Array([definition.width + 5, definition.height + 7]),
    time: 0,
  })
  if (!Object.is(bindings[program.axis], definition.axisValue)) throw new Error(`${program.id}/${definition.name}: axis binding lost binary64 identity`)
  if (!Object.is(bindings.renderScale, definition.scale)) throw new Error(`${program.id}/${definition.name}: renderScale binding lost binary64 identity`)
  if (bindings.inputTex !== input) throw new Error(`${program.id}/${definition.name}: sampler binding identity changed`)
  return bindings
}

function render(program, definition, factory, input) {
  const before = input.data.slice()
  const bindings = makeBindings(program, definition, input)
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: 0, seed: 2718 })
  const beforeSurface = new Surface(input.width, input.height, before)
  const immutable = compareFloat32Surfaces(beforeSurface, input)
  if (!immutable.exact_f32_bits) throw new Error(`${program.id}/${definition.name}: input texture mutated`)
  return output
}

function probe(surface, label, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { label, at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}

function probes(surface) {
  const points = [
    ['top-left-edge', 0, 0],
    ['top-right-edge', surface.width - 1, 0],
    ['bottom-left-edge', 0, surface.height - 1],
    ['bottom-right-edge', surface.width - 1, surface.height - 1],
    ['center', Math.floor(surface.width / 2), Math.floor(surface.height / 2)],
  ]
  return points.map(([label, x, y]) => probe(surface, label, x, y))
}

function outputRecord(surface) {
  let nonfinite = 0
  for (const value of surface.data) if (!Number.isFinite(value)) nonfinite += 1
  if (nonfinite !== 0) throw new Error('blur output contains nonfinite lanes')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    edge_and_center_probes: probes(surface),
  }
}

function replaceExactlyOnce(text, anchor, replacement, id) {
  if (text.split(anchor).length - 1 !== 1) throw new Error(`${id}: mutation anchor missing or non-unique`)
  return text.replace(anchor, replacement)
}

function evaluatedFactory(text) {
  return (0, eval)(`(${text})`)
}

function mutationsFor(program) {
  const radiusDeclaration = `var radius = ${program.axis} * renderScale|0;`
  const sampleAnchor = 'texture(inputTex, new $runtime.PooledFloat32Array([uv[0] + offset[0], uv[1] + offset[1]])).map(function (_) {return _ * weight;}).reduce((res,el,i)=>(res[i] += el, res), sum);'
  return [
    {
      id: `${program.id}-oracle-a-upper-off-by-one`,
      kind: 'trip_count_off_by_one',
      anchor: 'for (var i = -radius; i <= radius; i++) {',
      replacement: 'for (var i = -radius; i < radius; i++) {',
      description: 'Supplied Oracle A mutation: omit the +radius tap.',
    },
    {
      id: `${program.id}-oracle-a-upper-minus-two`,
      kind: 'trip_count_swap',
      anchor: 'for (var i = -radius; i <= radius; i++) {',
      replacement: 'for (var i = -radius; i <= radius - 2; i++) {',
      description: 'Supplied Oracle A mutation: omit the two highest positive taps.',
    },
    {
      id: `${program.id}-axis-swap`,
      kind: 'axis_swap',
      anchor: program.axisOffsetAnchor,
      replacement: program.axisOffsetMutation,
      description: 'Transpose the authored blur axis.',
    },
    {
      id: `${program.id}-coordinate-wrap-instead-of-clamp`,
      kind: 'coordinate_wrap',
      anchor: sampleAnchor,
      replacement: 'texture(inputTex, new $runtime.PooledFloat32Array([((uv[0] + offset[0]) % 1 + 1) % 1, ((uv[1] + offset[1]) % 1 + 1) % 1])).map(function (_) {return _ * weight;}).reduce((res,el,i)=>(res[i] += el, res), sum);',
      description: 'Modulo-wrap normalized coordinates before the canonical clamp sampler. This discriminates coordinate addressing and does not claim full bilinear repeat interpolation.',
    },
    {
      id: `${program.id}-radius-ceil`,
      kind: 'altered_truncation',
      anchor: radiusDeclaration,
      replacement: `var radius = Math.ceil(${program.axis} * renderScale)|0;`,
      description: 'Replace JS ToInt32 truncation with ceil.',
    },
    {
      id: `${program.id}-float32-rounded-product`,
      kind: 'float32_rounded_product',
      anchor: radiusDeclaration,
      replacement: `var radius = Math.fround(${program.axis} * renderScale)|0;`,
      description: 'Round the binary64 product to Float32 before integer conversion.',
    },
  ]
}

function buildBoundaryRecords() {
  const records = boundaryDefinitions.map((definition) => {
    const correct = admitBinary64(definition.axisValue, definition.scale)
    const faulty = admitFaultyFloat32OperandsBinary64Product(definition.axisValue, definition.scale)
    if (correct.accepted !== definition.expected) throw new Error(`${definition.name}: binary64 boundary expectation failed`)
    if (definition.expectedRadius !== undefined && correct.radius !== definition.expectedRadius) throw new Error(`${definition.name}: expected radius ${definition.expectedRadius}, got ${correct.radius}`)
    if (definition.operandQuantizedExpected !== undefined && faulty.accepted !== definition.operandQuantizedExpected) throw new Error(`${definition.name}: operand-quantized/binary64-product discriminator expectation failed`)
    return {
      name: definition.name,
      axis_value: Number.isFinite(definition.axisValue) ? definition.axisValue : String(definition.axisValue),
      axis_f64_bits_le: f64Bits(definition.axisValue),
      render_scale: Number.isFinite(definition.scale) ? definition.scale : String(definition.scale),
      render_scale_f64_bits_le: f64Bits(definition.scale),
      binary64_contract: correct,
      faulty_float32_operands_binary64_product_contract: faulty,
      classifications_diverge: correct.accepted !== faulty.accepted || (correct.accepted && faulty.accepted && correct.radius !== faulty.radius),
    }
  })
  const discriminators = records.filter((record) => record.classifications_diverge)
  if (discriminators.length < 2) throw new Error('both directions of operand-quantized/binary64-product boundary misclassification must be discriminated')
  return records
}

function buildProgram(program) {
  const caseRecords = program.cases.map((definition) => {
    const contract = admitBinary64(definition.axisValue, definition.scale)
    if (!contract.accepted) throw new Error(`${program.id}/${definition.name}: accepted render case failed contract`)
    const input = patternedSurface(definition.width, definition.height, definition.phase, definition.filter)
    const inputBefore = input.data.slice()
    const direct = render(program, definition, program.canonical, input)
    const repeated = render(program, definition, program.canonical, input)
    const repeat = compareSurfaces(direct, repeated)
    if (!repeat.float32.exact_f32_bits || !repeat.rgba8.exact_rgba8_bytes) throw new Error(`${program.id}/${definition.name}: repeat render mismatch`)
    const publicOutput = render(program, definition, program.publicFactory, input)
    const publicEquality = compareSurfaces(direct, publicOutput)
    if (!publicEquality.float32.exact_f32_bits || !publicEquality.rgba8.exact_rgba8_bytes) throw new Error(`${program.id}/${definition.name}: public/direct mismatch`)

    return {
      name: definition.name,
      dimensions: { width: definition.width, height: definition.height },
      uniforms: { [program.axis]: definition.axisValue, renderScale: definition.scale },
      uniform_f64_bits_le: { [program.axis]: f64Bits(definition.axisValue), renderScale: f64Bits(definition.scale) },
      admitted_contract: contract,
      float32_boundary_discriminator: definition.binary64Discriminator ?? null,
      sampler: { filter: definition.filter, wrap: 'clamp-to-edge' },
      input: {
        f32_sha256_before: sha256(bytes(inputBefore)),
        f32_sha256_after: sha256(bytes(input.data)),
        immutable: compareFloat32Surfaces(new Surface(input.width, input.height, inputBefore), input),
        edge_and_center_probes: probes(input),
      },
      output: outputRecord(direct),
      repeat_identity: repeat,
      public_catalog_vs_direct_canonical: publicEquality,
    }
  })

  const mutationRecords = mutationsFor(program).map((mutation) => {
    const mutatedText = replaceExactlyOnce(program.factoryText, mutation.anchor, mutation.replacement, mutation.id)
    const factory = evaluatedFactory(mutatedText)
    const results = caseRecords.map((record, index) => {
      const definition = program.cases[index]
      const input = patternedSurface(definition.width, definition.height, definition.phase, definition.filter)
      const candidate = render(program, definition, factory, input)
      const referenceInput = patternedSurface(definition.width, definition.height, definition.phase, definition.filter)
      const reference = render(program, definition, program.canonical, referenceInput)
      const comparison = compareSurfaces(reference, candidate)
      return { case: definition.name, radius: record.admitted_contract.radius, comparison }
    })
    const divergent = results.filter((record) => !record.comparison.float32.exact_f32_bits).length
    const divergentRgba8 = results.filter((record) => !record.comparison.rgba8.exact_rgba8_bytes).length
    if (divergent === 0) throw new Error(`${mutation.id}: no exact Float32 divergence`)
    if (divergentRgba8 === 0) throw new Error(`${mutation.id}: no exact RGBA8 divergence`)
    return {
      id: mutation.id,
      kind: mutation.kind,
      anchor: mutation.anchor,
      mutated: mutation.replacement,
      description: mutation.description,
      cases_compared: results.length,
      divergent_f32_cases: divergent,
      divergent_rgba8_cases: divergentRgba8,
      case_results: results,
    }
  })

  return {
    key: program.key,
    axis_binding: program.axis,
    source_file: program.sourceFile,
    source_raw_bytes: program.sourceBytes,
    source_sha256: program.sourceSha256,
    canonical_factory_name: program.factoryName,
    canonical_factory_to_string_sha256: program.factorySha256,
    public_is_canonical: true,
    adapter_override: null,
    cases: caseRecords,
    mutations: mutationRecords,
  }
}

function buildData() {
  const boundaryRecords = buildBoundaryRecords()
  const programRecords = Object.fromEntries(verifiedPrograms.map((program) => [program.id, buildProgram(program)]))
  const allCases = Object.values(programRecords).flatMap((program) => program.cases)
  const radii = [...new Set(allCases.map((record) => record.admitted_contract.radius))].sort((a, b) => a - b)
  for (const required of [0, 1, 3, 12, 50, 63]) if (!radii.includes(required)) throw new Error(`required radius ${required} missing`)
  if (!allCases.some((record) => record.sampler.filter === 'nearest') || !allCases.some((record) => record.sampler.filter === 'linear')) throw new Error('nearest/linear filter coverage incomplete')
  if (!allCases.some((record) => record.dimensions.width === 1) || !allCases.some((record) => record.dimensions.height === 1)) throw new Error('valid degenerate-axis dimension coverage incomplete')

  return {
    schema: 'noisemaker-for-cpp.blur.binary64-boundary-and-pixel-parity-oracle.v1',
    corpus_revision: corpusRevision,
    upstream_revision: UPSTREAM_REVISION,
    provenance: {
      node: process.version,
      reference_api: 'canonicalKernelFactories[key] via createCanonicalBindings, bindGlslKernel, and runPass',
      public_api: 'kernelFactories.get(key)',
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    binding_contract: {
      numeric_domain: 'JavaScript Number / IEEE-754 binary64',
      axis: 'finite and in [0,50]',
      render_scale: 'finite and nonnegative',
      product: 'binary64 axis * renderScale, accepted only in [0,64)',
      conversion: 'truncation toward zero; accepted radius 0..63',
      maximum_loop_visits: 127,
      rejection_policy: 'reject; never clamp, substitute, or Float32-round',
      boundary_cases: boundaryRecords,
    },
    fixture: {
      input: 'asymmetric deterministic Float32 RGBA with distinct left/right/top/bottom edge signals',
      comparer: 'purpose-built exact Float32 pixel/channel comparer and exact RGBA8 comparer; hashes remain authoritative',
      sampler_filters: ['nearest', 'linear'],
      sampler_wrap: 'clamp-to-edge',
      probes: ['four edge corners', 'center'],
      repeat_render_count: 2,
    },
    coverage_summary: {
      programs: Object.keys(programRecords),
      accepted_cases: allCases.length,
      accepted_radii: radii,
      rejected_boundary_cases: boundaryRecords.filter((record) => !record.binary64_contract.accepted).length,
      float32_operand_quantization_discriminators: boundaryRecords.filter((record) => record.classifications_diverge).map((record) => record.name),
      mutations: Object.values(programRecords).reduce((total, program) => total + program.mutations.length, 0),
    },
    programs: programRecords,
  }
}

function makeReport(data) {
  const lines = [
    '# Blur binary64 boundary and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/blur:blurH` and `filter/blur:blurV`. Float32 and RGBA8 hashes are exact byte contracts. The custom comparer adds first-pixel/channel diagnostics without relaxing exact equality.', '',
    '## Binding boundary', '',
    'The admitted radius is computed from the original JavaScript Number (IEEE-754 binary64) bindings. The selected axis must be finite and in `[0,50]`; `renderScale` must be finite and nonnegative; their binary64 product must be in `[0,64)`. Truncation toward zero then yields radius `0..63`, so the symmetric loop performs at most 127 visits. Values at or above 64 are rejected, never clamped.', '',
    '| Boundary | Axis | Scale | Binary64 accepted | Radius | Faulty operand-Float32/product-binary64 accepted | Discriminator |',
    '| --- | ---: | ---: | --- | ---: | --- | --- |',
  ]
  for (const record of data.binding_contract.boundary_cases) {
    lines.push(`| ${record.name} | ${record.axis_value} | ${record.render_scale} | ${record.binary64_contract.accepted} | ${record.binary64_contract.radius ?? '-'} | ${record.faulty_float32_operands_binary64_product_contract.accepted} | ${record.classifications_diverge} |`)
  }
  lines.push('', 'The boundary table models a specific fault: quantize both operands to Float32, then multiply those quantized values in binary64. Its two explicit threshold discriminators run in opposite directions: the binary64 value immediately below 64 is valid radius 63 even though operand quantization produces 64, while `50 * 1.28` is exactly 64 in binary64 and must be rejected even though the quantized operands multiply to less than 64. The separate pixel mutation named `float32-rounded-product` keeps the original operands and rounds only the completed product.', '')
  lines.push('## Pixel cases', '', '| Program | Case | Size | Filter | Radius | Float32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | ---: | --- | --- |')
  for (const [id, program] of Object.entries(data.programs)) {
    for (const record of program.cases) {
      lines.push(`| ${id} | ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${record.sampler.filter} | ${record.admitted_contract.radius} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
    }
  }
  lines.push('', 'Every accepted case passes exact repeated-render identity, exact input immutability, finite output, and public-catalog-versus-direct-canonical equality. The fixture covers radius 0, 1, intermediate values, metadata maximum 50, and boundary maximum 63; zero, fractional, ordinary, and large scales; nearest and linear input filters; non-square images; valid 1-pixel axes; and four clamp-to-edge corners plus a center probe.', '')
  lines.push('## Mutation discrimination', '', '| Program | Mutation | Kind | Divergent Float32 cases | Divergent RGBA8 cases | Compared cases |', '| --- | --- | --- | ---: | ---: | ---: |')
  for (const [id, program] of Object.entries(data.programs)) {
    for (const mutation of program.mutations) lines.push(`| ${id} | ${mutation.id} | ${mutation.kind} | ${mutation.divergent_f32_cases} | ${mutation.divergent_rgba8_cases} | ${mutation.cases_compared} |`)
  }
  lines.push('', 'Both original Oracle A loop mutations are retained for each axis. Additional exact controls transpose the blur axis, modulo-wrap coordinates before the canonical clamp sampler, replace truncation with ceil, and round the completed binary64 product to Float32 before integer conversion. The coordinate-wrap control is intentionally not described as a complete bilinear repeat sampler. Every mutation is machine-required to diverge under both exact Float32 and exact RGBA8 comparison on at least one frozen case.', '')
  lines.push('## Provenance', '')
  lines.push(`- Upstream snapshot revision: \`${data.upstream_revision}\``)
  lines.push(`- Corpus revision: \`${data.corpus_revision}\``)
  for (const [id, program] of Object.entries(data.programs)) {
    lines.push(`- ${id} GLSL SHA-256: \`${program.source_sha256}\`; canonical factory SHA-256: \`${program.canonical_factory_to_string_sha256}\``)
  }
  lines.push(`- Node reference engine used to freeze this file: \`${data.provenance.node}\``)
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = makeReport(data)

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outputPath) || fs.readFileSync(outputPath, 'utf8') !== json) throw new Error('blur parity JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('blur parity report drift')
  console.log(`blur parity oracle ok (${data.coverage_summary.accepted_cases} cases, ${data.coverage_summary.mutations} mutations, binary64 boundary checked)`)
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  console.log(outputPath)
  console.log(reportPath)
}
