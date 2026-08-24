import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-21-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision)
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const key = 'filter/degauss:degauss'
const source = 'sources/filter/degauss/degauss.glsl'
const expectedRawBytes = 10803
const expectedRawSha256 = '915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c'
const expectedNormalizedSha256 = '7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560'
const expectedCanonicalKernelsSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const expectedFactorySha256 = 'f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38'
const expectedFunctionTupleFingerprint = 'f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a'
const expectedWholeProgramFingerprint = '73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d'

const f = Math.fround
const frame = 17
const deltaTime = f(1 / 60)
const runtimeSeed = f(29)
const inputDescription = 'top-down Float32Array at each case size: R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=(((5*x+7*y+3)%23)-5)/12; every lane assignment crosses the Float32Array boundary'
const sourceFunctions = Object.freeze([
  'as_u32', 'clamp01', 'wrap_index', 'wrap_float', 'freq_for_shape',
  'normalized_sine', 'periodic_value', 'mod289_vec3', 'mod289_vec4',
  'permute', 'taylor_inv_sqrt', 'simplex_noise', 'compute_noise_value',
  'singularity_mask', 'sample_bilinear', 'warped_channel_value', 'main',
])

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) {
  const values = new Float32Array([value])
  return `0x${new DataView(values.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}
function printable(value) {
  if (Number.isNaN(value)) return 'NaN'
  if (value === Infinity) return '+Infinity'
  if (value === -Infinity) return '-Infinity'
  return value
}
function countOccurrences(value, needle) { return value.split(needle).length - 1 }
function scalarRecord(value, glslType = 'float') {
  return glslType === 'int' ? { glsl_type: 'int', value } : { glsl_type: 'float', value, f32_bits_le: f32Bits(value) }
}
function vec2Record(value) { return { glsl_type: 'vec2', values: Array.from(value), f32_bits_le: Array.from(value, f32Bits) } }

const rawSource = fs.readFileSync(path.join(corpus, source))
if (rawSource.byteLength !== expectedRawBytes || sha256(rawSource) !== expectedRawSha256) throw new Error('pinned Degauss source drift')
const canonicalKernels = fs.readFileSync(canonicalKernelsPath)
if (sha256(canonicalKernels) !== expectedCanonicalKernelsSha256) throw new Error('pinned canonical-kernels.js drift')
const canonicalFactory = canonicalKernelFactories[key]
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== 'canonicalFactory45') throw new Error(`missing pinned canonical factory ${key}`)
const canonicalFactoryText = canonicalFactory.toString()
if (sha256(Buffer.from(canonicalFactoryText, 'utf8')) !== expectedFactorySha256) throw new Error('pinned Degauss factory drift')
for (const name of sourceFunctions) {
  if (countOccurrences(canonicalFactoryText, `function ${name} (`) !== 1) throw new Error(`pinned function shape drift: ${name}`)
}

const defaults = Object.freeze({
  displacement: f(0.0625), speed: f(1), seed: 1, direction: f(0),
})

const caseDefinitions = Object.freeze([
  {
    name: 'displacement-zero-exact-copy-tiled', size: [13, 9], tileOffset: [7, 11], fullResolution: [41, 29], time: f(0.375),
    uniforms: { ...defaults, displacement: f(0) },
    coverage: ['displacement-equals-zero-early-return', 'exact-F32-copy-including-out-of-range-alpha', 'tiled-context-bound-but-not-reached'],
    exactCopy: true,
  },
  {
    name: 'default-landscape-untiled-center-mask', size: [13, 9], tileOffset: [0, 0], fullResolution: [13, 9], time: f(0.375),
    uniforms: { ...defaults },
    coverage: ['metadata-defaults', 'landscape-frequency-branch', 'untiled-cap-branch', 'exact-center-mask-zero-early-return', 'normal-path-around-center'],
    exactCenterCopy: true,
  },
  {
    name: 'nondefault-landscape-tiled-negative-direction', size: [13, 9], tileOffset: [7, 11], fullResolution: [41, 29], time: f(0.4375),
    uniforms: { displacement: f(0.1875), speed: f(1.75), seed: 37, direction: f(-137.25) },
    coverage: ['landscape-frequency-branch', 'tiled-cap-branch', 'negative-direction', 'nondefault-seed', 'base-and-time-simplex-noise', 'three-channel-warp'],
  },
  {
    name: 'nondefault-portrait-tiled-positive-direction', size: [9, 13], tileOffset: [5, 3], fullResolution: [23, 37], time: f(0.6125),
    uniforms: { displacement: f(0.25), speed: f(2), seed: 100, direction: f(180) },
    coverage: ['portrait-frequency-branch', 'tiled-cap-branch', 'positive-direction-boundary', 'nondefault-seed', 'base-and-time-simplex-noise'],
  },
  {
    name: 'speed-zero-nonzero-time', size: [13, 9], tileOffset: [4, 6], fullResolution: [31, 25], time: f(0.875),
    uniforms: { displacement: f(0.09375), speed: f(0), seed: 19, direction: f(33.25) },
    coverage: ['speed-equals-zero-short-circuit', 'base-simplex-only', 'nonzero-time', 'positive-direction', 'tiled-cap-branch'],
  },
  {
    name: 'time-zero-positive-speed', size: [13, 9], tileOffset: [3, 2], fullResolution: [29, 21], time: f(0),
    uniforms: { displacement: f(0.140625), speed: f(1.5), seed: 53, direction: f(-61.5) },
    coverage: ['time-equals-zero-short-circuit', 'base-simplex-only', 'nonzero-speed', 'negative-direction', 'tiled-cap-branch'],
  },
  {
    name: 'full-resolution-zero-fallback-landscape', size: [13, 9], tileOffset: [2, 1], fullResolution: [0, 0], time: f(0.3125),
    uniforms: { displacement: f(0.125), speed: f(1.25), seed: 11, direction: f(72.5) },
    coverage: ['fullResolution-x-not-positive-fallback-to-resolution', 'landscape-frequency-branch', 'renderScale-one', 'untiled-cap-branch'],
  },
  {
    name: 'square-frequency-equality', size: [11, 11], tileOffset: [3, 2], fullResolution: [31, 31], time: f(0.55),
    uniforms: { displacement: f(0.21875), speed: f(0.75), seed: 71, direction: f(-180) },
    coverage: ['square-frequency-equality-branch', 'tiled-cap-branch', 'negative-direction-boundary', 'base-and-time-simplex-noise'],
  },
  {
    name: 'untiled-over-cap-binding-domain-diagnostic', size: [13, 9], tileOffset: [0, 0], fullResolution: [13, 9], time: f(0.46875),
    uniforms: { displacement: f(1.75), speed: f(1.25), seed: 29, direction: f(90) },
    coverage: ['direct-binding-domain-diagnostic', 'untiled-maxOffsetPixels-13', 'maxAllowedDisplacement-one', 'displacement-clamped-from-1.75-to-1', 'wrap-heavy-bilinear-footprints'],
  },
])

function makeInput(width, height) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const lane = (y * width + x) * 4
      data[lane] = ((17 * x + 31 * y + 13) % 101) / 100
      data[lane + 1] = ((7 * x + 19 * y + 23) % 97) / 96
      data[lane + 2] = ((29 * x + 11 * y + 5) % 89) / 88
      data[lane + 3] = (((5 * x + 7 * y + 3) % 23) - 5) / 12
    }
  }
  return new Surface(width, height, data)
}

function probeCoordinates(width, height) {
  const points = [
    [0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1],
    [Math.floor(width / 2), Math.floor(height / 2)], [1, 1], [width - 2, height - 2],
    [Math.floor(width * 0.7), Math.floor(height * 0.3)],
  ]
  return points.filter(([x, y], index) => points.findIndex(([a, b]) => a === x && b === y) === index)
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at_top_down_xy: [x, y], values: values.map(printable), f32_bits_le: values.map(f32Bits) }
}

function render(factory, definition) {
  const [width, height] = definition.size
  const input = makeInput(width, height)
  const tileOffset = new Float32Array(definition.tileOffset)
  const fullResolution = new Float32Array(definition.fullResolution)
  const kernel = bindCanonicalKernel(factory, {
    width, height, time: definition.time, frame, deltaTime, seed: runtimeSeed,
    tileOffset, fullResolution, uniforms: definition.uniforms, textures: { inputTex: input },
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: definition.time, seed: runtimeSeed })
  return { input, output: destination }
}

function surfaceMetrics(input, output) {
  let finiteLanes = 0
  let nonfiniteLanes = 0
  let changedF32Lanes = 0
  let changedRgbPixels = 0
  let exactInputPixels = 0
  let alphaPreservedPixels = 0
  let alphaEqualsClampedInputPixels = 0
  let alphaOutOfUnitIntervalPixels = 0
  let minOutput = Infinity
  let maxOutput = -Infinity
  for (let pixel = 0; pixel < output.width * output.height; pixel += 1) {
    const offset = pixel * 4
    let exactPixel = true
    let changedRgb = false
    for (let lane = 0; lane < 4; lane += 1) {
      const actual = output.data[offset + lane]
      const original = input.data[offset + lane]
      if (Number.isFinite(actual)) finiteLanes += 1
      else nonfiniteLanes += 1
      if (f32Bits(actual) !== f32Bits(original)) { changedF32Lanes += 1; exactPixel = false }
      if (lane < 3 && f32Bits(actual) !== f32Bits(original)) changedRgb = true
      if (Number.isFinite(actual)) { minOutput = Math.min(minOutput, actual); maxOutput = Math.max(maxOutput, actual) }
    }
    if (exactPixel) exactInputPixels += 1
    if (changedRgb) changedRgbPixels += 1
    const alpha = output.data[offset + 3]
    const inputAlpha = input.data[offset + 3]
    if (f32Bits(alpha) === f32Bits(inputAlpha)) alphaPreservedPixels += 1
    const clampedAlpha = f(Math.min(Math.max(inputAlpha, 0), 1))
    if (f32Bits(alpha) === f32Bits(clampedAlpha)) alphaEqualsClampedInputPixels += 1
    if (alpha < 0 || alpha > 1) alphaOutOfUnitIntervalPixels += 1
  }
  return {
    pixels: output.width * output.height,
    finite_lanes: finiteLanes,
    nonfinite_lanes: nonfiniteLanes,
    changed_f32_lanes_from_same_top_down_input_position: changedF32Lanes,
    changed_rgb_pixels_from_same_top_down_input_position: changedRgbPixels,
    exact_input_pixels: exactInputPixels,
    alpha_preserved_from_input_pixels: alphaPreservedPixels,
    alpha_equal_clamped_input_pixels: alphaEqualsClampedInputPixels,
    alpha_out_of_unit_interval_pixels: alphaOutOfUnitIntervalPixels,
    min_output_lane: minOutput,
    max_output_lane: maxOutput,
  }
}

function recordedUniforms(uniforms) {
  return {
    displacement: scalarRecord(uniforms.displacement),
    speed: scalarRecord(uniforms.speed),
    seed: scalarRecord(uniforms.seed, 'int'),
    direction: scalarRecord(uniforms.direction),
  }
}

const canonicalSurfaces = new Map()
function caseResult(definition) {
  const first = render(canonicalFactory, definition)
  const second = render(canonicalFactory, definition)
  const firstRgba8 = first.output.toRgba8()
  const secondRgba8 = second.output.toRgba8()
  if (!sameBytes(first.input.data, second.input.data) || !sameBytes(first.output.data, second.output.data)
      || !sameBytes(firstRgba8, secondRgba8)) throw new Error(`${definition.name}: canonical repeat was not byte-identical`)
  const metrics = surfaceMetrics(first.input, first.output)
  if (metrics.nonfinite_lanes !== 0 || metrics.finite_lanes !== metrics.pixels * 4) throw new Error(`${definition.name}: unexpected nonfinite output`)
  if (definition.exactCopy && !sameBytes(first.input.data, first.output.data)) throw new Error(`${definition.name}: displacement-zero output was not an exact F32 copy`)
  if (definition.exactCenterCopy) {
    const [width, height] = definition.size
    const center = (Math.floor(height / 2) * width + Math.floor(width / 2)) * 4
    if (!sameBytes(first.input.data.subarray(center, center + 4), first.output.data.subarray(center, center + 4))) {
      throw new Error(`${definition.name}: exact center mask-zero pixel did not preserve input`)
    }
  }
  if (!definition.exactCopy && metrics.changed_rgb_pixels_from_same_top_down_input_position === 0) throw new Error(`${definition.name}: nonzero displacement fixture is not informative`)
  const points = probeCoordinates(...definition.size)
  canonicalSurfaces.set(definition.name, first.output)
  return {
    name: definition.name,
    key,
    dimensions: { width: definition.size[0], height: definition.size[1] },
    tileOffset: vec2Record(new Float32Array(definition.tileOffset)),
    fullResolution: vec2Record(new Float32Array(definition.fullResolution)),
    time: scalarRecord(definition.time),
    uniforms: recordedUniforms(definition.uniforms),
    coverage: definition.coverage,
    input: {
      f32_sha256: sha256(bytes(first.input.data)), rgba8_sha256: sha256(bytes(first.input.toRgba8())),
      probes: points.map(([x, y]) => probe(first.input, x, y)),
    },
    output: {
      f32_sha256: sha256(bytes(first.output.data)), rgba8_sha256: sha256(bytes(firstRgba8)),
      probes: points.map(([x, y]) => probe(first.output, x, y)), metrics,
    },
    repeat_identity: { input_f32_bytes: true, output_f32_bytes: true, output_rgba8_bytes: true },
  }
}

function replacedFactory(name, replacements) {
  let text = canonicalFactoryText
  const applied = []
  for (const { from, to, count } of replacements) {
    const actual = countOccurrences(text, from)
    if (actual !== count) throw new Error(`${name}: replacement count ${actual}, expected ${count}`)
    text = text.split(from).join(to)
    applied.push({ from, to, exact_replacement_count: count })
  }
  return { factory: (0, eval)(`(${text})`), applied }
}

function diffSummary(reference, mutated) {
  const referenceBytes = bytes(reference.data)
  const mutatedBytes = bytes(mutated.data)
  const referenceRgba8 = reference.toRgba8()
  const mutatedRgba8 = mutated.toRgba8()
  let f32ByteDifferences = 0
  let f32LaneDifferences = 0
  let rgba8ByteDifferences = 0
  let maxAbsoluteDifference = 0
  let nonfiniteLaneTransitions = 0
  for (let index = 0; index < referenceBytes.length; index += 1) if (referenceBytes[index] !== mutatedBytes[index]) f32ByteDifferences += 1
  for (let index = 0; index < reference.data.length; index += 1) {
    if (f32Bits(reference.data[index]) !== f32Bits(mutated.data[index])) {
      f32LaneDifferences += 1
      if (Number.isFinite(reference.data[index]) && Number.isFinite(mutated.data[index])) {
        maxAbsoluteDifference = Math.max(maxAbsoluteDifference, Math.abs(reference.data[index] - mutated.data[index]))
      } else nonfiniteLaneTransitions += 1
    }
  }
  for (let index = 0; index < referenceRgba8.length; index += 1) if (referenceRgba8[index] !== mutatedRgba8[index]) rgba8ByteDifferences += 1
  return {
    same_f32_bytes: f32ByteDifferences === 0,
    same_rgba8_bytes: rgba8ByteDifferences === 0,
    different_f32_bytes: f32ByteDifferences,
    different_f32_lanes: f32LaneDifferences,
    different_rgba8_bytes: rgba8ByteDifferences,
    max_absolute_f32_difference: maxAbsoluteDifference,
    nonfinite_lane_transitions: nonfiniteLaneTransitions,
    mutated_f32_sha256: sha256(mutatedBytes),
    mutated_rgba8_sha256: sha256(bytes(mutatedRgba8)),
  }
}

const allNonzeroCases = caseDefinitions.filter(item => !item.exactCopy).map(item => item.name)
const activeTimeCases = caseDefinitions.filter(item => !item.exactCopy && item.time !== 0 && item.uniforms.speed !== 0).map(item => item.name)
const shortCircuitCases = ['displacement-zero-exact-copy-tiled', 'speed-zero-nonzero-time', 'time-zero-positive-speed']
const mutationDefinitions = Object.freeze([
  {
    name: 'channel-order-red-zero-to-blue-two',
    contract: 'changes only the red warped_channel_value selector from channel 0 to channel 2',
    replacements: [{ from: 'var red = warped_channel_value(0, coord, base_pos, width_f, height_f, freq, clampedDisplacement, mask, time, speed);', to: 'var red = warped_channel_value(2, coord, base_pos, width_f, height_f, freq, clampedDisplacement, mask, time, speed);', count: 1 }],
    mustDiverge: ['nondefault-landscape-tiled-negative-direction', 'nondefault-portrait-tiled-positive-direction'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'direction-rotation-disabled',
    contract: 'sets dirRad to zero while retaining all noise and sampling work',
    replacements: [{ from: 'var dirRad = (direction * TAU) / 360;', to: 'var dirRad = 0;', count: 1 }],
    mustDiverge: ['nondefault-landscape-tiled-negative-direction', 'nondefault-portrait-tiled-positive-direction'],
    mustMatch: ['displacement-zero-exact-copy-tiled', 'default-landscape-untiled-center-mask'],
  },
  {
    name: 'wrap-index-next-neighbor-clamped',
    contract: 'replaces positive modulo wrapping of x1/y1 with last-index clamping',
    replacements: [{ from: 'var wrapped = value % limit;', to: 'var wrapped = min(value, limit - 1);', count: 1 }],
    mustDiverge: ['untiled-over-cap-binding-domain-diagnostic'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'wrap-float-coordinate-clamped',
    contract: 'replaces periodic floating coordinate wrapping with clamping inside the last texel',
    replacements: [{ from: 'var result = value - (floor(value / limit)) * limit;', to: 'var result = clamp(value, 0, limit - 0.0009765625);', count: 1 }],
    mustDiverge: ['untiled-over-cap-binding-domain-diagnostic'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'bilinear-fx-forced-zero',
    contract: 'removes horizontal interpolation while retaining the four canonical fetches',
    replacements: [{ from: 'var fx = clamp(wrapped_x - (x0), 0, 1);', to: 'var fx = 0;', count: 1 }],
    mustDiverge: ['nondefault-landscape-tiled-negative-direction', 'untiled-over-cap-binding-domain-diagnostic'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'bilinear-fy-forced-zero',
    contract: 'removes vertical interpolation while retaining the four canonical fetches',
    replacements: [{ from: 'var fy = clamp(wrapped_y - (y0), 0, 1);', to: 'var fy = 0;', count: 1 }],
    mustDiverge: ['nondefault-portrait-tiled-positive-direction', 'untiled-over-cap-binding-domain-diagnostic'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'time-noise-branch-disabled',
    contract: 'disables only the second simplex/time-noise branch',
    replacements: [{ from: 'if ((speed != 0) && (time != 0)) {', to: 'if (false) {', count: 1 }],
    mustDiverge: activeTimeCases,
    mustMatch: shortCircuitCases,
  },
  {
    name: 'singularity-mask-forced-one',
    contract: 'forces the main-path mask to one after retaining singularity_mask call-site shape as an exact replacement target',
    replacements: [{ from: 'var mask = singularity_mask(uv, width_f, height_f);', to: 'var mask = 1;', count: 1 }],
    mustDiverge: ['default-landscape-untiled-center-mask', 'nondefault-landscape-tiled-negative-direction'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'alpha-clamp-disabled',
    contract: 'preserves original alpha on the normal path instead of clamp01',
    replacements: [{ from: 'var alpha = clamp01(original[3]);', to: 'var alpha = original[3];', count: 1 }],
    mustDiverge: allNonzeroCases,
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'displacement-cap-disabled',
    contract: 'uses the bound displacement directly instead of min(displacement,maxAllowedDisplacement)',
    replacements: [{ from: 'var clampedDisplacement = min(displacement, maxAllowedDisplacement);', to: 'var clampedDisplacement = displacement;', count: 1 }],
    mustDiverge: ['untiled-over-cap-binding-domain-diagnostic'],
    mustMatch: caseDefinitions.filter(item => item.name !== 'untiled-over-cap-binding-domain-diagnostic').map(item => item.name),
  },
  {
    name: 'simplex-amplitude-42-to-41',
    contract: 'changes the final simplex_noise amplitude only',
    replacements: [{ from: 'return 42 * ((m0sq * m0sq) * (dot(g0n, x0)) + (m1sq * m1sq) * (dot(g1n, x1)) + (m2sq * m2sq) * (dot(g2n, x2)) + (m3sq * m3sq) * (dot(g3n, x3)));', to: 'return 41 * ((m0sq * m0sq) * (dot(g0n, x0)) + (m1sq * m1sq) * (dot(g1n, x1)) + (m2sq * m2sq) * (dot(g2n, x2)) + (m3sq * m3sq) * (dot(g3n, x3)));', count: 1 }],
    mustDiverge: ['nondefault-landscape-tiled-negative-direction', 'speed-zero-nonzero-time', 'time-zero-positive-speed'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
  {
    name: 'frequency-axes-unswapped',
    contract: 'uses freq.x for x and freq.y for y instead of the canonical cross-axis mapping',
    replacements: [{ from: 'var freq_x = max(freq[1], 1);\n  \tvar freq_y = max(freq[0], 1);', to: 'var freq_x = max(freq[0], 1);\n  \tvar freq_y = max(freq[1], 1);', count: 1 }],
    mustDiverge: ['nondefault-landscape-tiled-negative-direction', 'nondefault-portrait-tiled-positive-direction'],
    mustMatch: ['displacement-zero-exact-copy-tiled', 'square-frequency-equality'],
  },
  {
    name: 'seed-offset-disabled',
    contract: 'sets compute_noise_value seed_offset to zero while preserving channel offsets',
    replacements: [{ from: 'var seed_offset = (seed) * 73;', to: 'var seed_offset = 0;', count: 1 }],
    mustDiverge: ['default-landscape-untiled-center-mask', 'nondefault-landscape-tiled-negative-direction', 'nondefault-portrait-tiled-positive-direction'],
    mustMatch: ['displacement-zero-exact-copy-tiled'],
  },
])

function mutationResult(definition) {
  const { factory, applied } = replacedFactory(definition.name, definition.replacements)
  const results = []
  for (const caseDefinition of caseDefinitions) {
    const reference = canonicalSurfaces.get(caseDefinition.name)
    const mutated = render(factory, caseDefinition).output
    results.push({ case: caseDefinition.name, ...diffSummary(reference, mutated) })
  }
  for (const name of definition.mustDiverge ?? []) {
    const result = results.find(item => item.case === name)
    if (!result || result.same_f32_bytes) throw new Error(`${definition.name}: required F32 divergence missing for ${name}`)
  }
  for (const name of definition.mustMatch ?? []) {
    const result = results.find(item => item.case === name)
    if (!result || !result.same_f32_bytes || !result.same_rgba8_bytes) throw new Error(`${definition.name}: required byte identity missing for ${name}`)
  }
  return {
    name: definition.name,
    contract: definition.contract,
    replacements: applied,
    required_divergence_cases: definition.mustDiverge ?? [],
    required_identity_cases: definition.mustMatch ?? [],
    case_results: results,
  }
}

function build() {
  const cases = caseDefinitions.map(caseResult)
  const mutations = mutationDefinitions.map(mutationResult)
  return `${JSON.stringify({
    schema: 'noisemaker-for-cpp.task21-degauss.direct-canonical-oracles.v1',
    corpus_revision: corpusRevision,
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: expectedCanonicalKernelsSha256,
      factory_name: canonicalFactory.name,
      factory_to_string_sha256: expectedFactorySha256,
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-21-oracle-generator.mjs',
      reference_only: 'all frozen expected outputs come from the pinned direct canonical CPU factory; mutation outputs are eval-created copies of that exact factory text with counted replacements',
    },
    program: {
      key, source, raw_source_bytes: expectedRawBytes, raw_source_sha256: expectedRawSha256,
      normalized_source_sha256: expectedNormalizedSha256, defines: {}, numeric_literal_contract: 'glsl-f32',
      compatibility_transform: 'none',
      typed_shape: { source_functions: sourceFunctions, function_count: 17, loops: 0, call_graph: 'acyclic' },
      function_tuple_fingerprint: expectedFunctionTupleFingerprint,
      whole_program_fingerprint: expectedWholeProgramFingerprint,
      uniform_binding_signature: [
        'TAU:const float@1', 'inputTex:sampler2D@2/S1', 'resolution:vec2@3', 'tileOffset:vec2@4',
        'fullResolution:vec2@5', 'time:float@6', 'displacement:float@7', 'speed:float@8',
        'seed:int@9', 'direction:float@10',
      ],
      output_signature: 'fragColor:vec4@11',
      pass_route: { inputs: { inputTex: 'inputTex' }, outputs: { fragColor: 'outputTex' }, uniforms: { direction: 'direction', displacement: 'displacement', seed: 'seed', speed: 'speed' } },
      metadata_defaults: recordedUniforms(defaults),
      normal_path_dynamic_fetches_per_pixel: { original_texelFetch: 1, three_bilinear_calls: 12, total: 13, lod: 0 },
    },
    fixture: {
      input: { construction: inputDescription, storage: 'top-down Surface Float32Array; lane=(y*width+x)*4; dimensions equal each output case' },
      output: { storage: 'top-down Surface Float32Array; lane=(y*width+x)*4' },
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      sampler_orientation: 'input storage is top-down; canonical texelFetch maps GLSL bottom-left integer coordinates through Surface sampling',
      float_bytes: 'host little-endian Float32Array bytes; probe words use little-endian Uint32',
      context: { frame, deltaTime: scalarRecord(deltaTime), runtime_seed: scalarRecord(runtimeSeed) },
      verification: 'every canonical case double-renders with fresh input and destination surfaces and requires identical input F32, output F32, and output RGBA8 bytes before hashing; every output lane must be finite',
      note: 'the over-cap case deliberately exercises the direct binding domain outside the metadata UI maximum; it is a branch diagnostic, not a metadata-valid preset',
    },
    cases,
    mutation_sensitivity: {
      purpose: 'prove the frozen fixture is sensitive to channel order, seed/simplex/time noise, shape frequency mapping, mask, direction, displacement cap, floating and integer wrap, both bilinear axes, and alpha behavior across the 17-function acyclic helper graph',
      mutations,
    },
  }, null, 2)}\n`
}

const expected = build()
if (process.argv.length === 2) {
  process.stdout.write(expected)
} else if (process.argv.length === 3 && process.argv[2] === '--write') {
  fs.writeFileSync(outputPath, expected, 'utf8')
  process.stdout.write(`wrote ${path.basename(outputPath)}\n`)
} else if (process.argv.length === 3 && process.argv[2] === '--check') {
  const actual = fs.readFileSync(outputPath, 'utf8')
  if (actual !== expected) throw new Error(`${outputPath} is not the exact frozen canonical oracle output`)
  process.stdout.write(`ok ${path.basename(outputPath)}\n`)
} else {
  throw new Error('usage: node task-21-oracle-generator.mjs [--write|--check]')
}
