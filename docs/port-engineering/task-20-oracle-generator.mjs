import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-20-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision)
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const key = 'synth/sacredGeometry:sacredGeometry'
const source = 'sources/synth/sacredGeometry/sacredGeometry.glsl'
const expectedRawSha256 = '24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de'
const expectedNormalizedSha256 = '6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3'
const expectedCanonicalKernelsSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const expectedFactorySha256 = 'b4ed8af983d8bda5d48e05d418458c2fc82170f745b021199df7f7095fadb2f2'

const f = Math.fround
const dimensions = Object.freeze({ output: [37, 23], tileOffset: [5, 7], fullResolution: [53, 41] })
const context = Object.freeze({ time: f(0.3375), unfoldTime: f(0.4125), frame: 11, deltaTime: f(1 / 60), seed: f(23) })
const probeCoordinates = Object.freeze([
  [0, 0], [10, 9], [16, 11], [18, 11], [20, 15], [28, 5], [32, 9], [35, 21], [36, 22],
])
const floatUniformNames = new Set(['scale', 'rotation', 'thickness', 'smoothness', 'speed', 'pulseDepth'])
const intUniformNames = new Set(['geometry', 'rings', 'starPoints', 'animation'])
const vectorUniformNames = new Set(['fgColor', 'bgColor'])

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

const rawSource = fs.readFileSync(path.join(corpus, source))
if (sha256(rawSource) !== expectedRawSha256) throw new Error('pinned Sacred Geometry source digest drift')
const canonicalKernels = fs.readFileSync(canonicalKernelsPath)
if (sha256(canonicalKernels) !== expectedCanonicalKernelsSha256) throw new Error('pinned canonical-kernels.js digest drift')
const canonicalFactory = canonicalKernelFactories[key]
if (typeof canonicalFactory !== 'function') throw new Error(`missing canonical factory ${key}`)
const canonicalFactoryText = canonicalFactory.toString()
if (sha256(Buffer.from(canonicalFactoryText, 'utf8')) !== expectedFactorySha256) throw new Error('pinned Sacred Geometry factory digest drift')

const defaults = Object.freeze({
  scale: f(10), rotation: f(0), thickness: f(0.2), smoothness: f(0.02),
  geometry: 0, rings: 3, starPoints: 5, animation: 0,
  speed: f(1), pulseDepth: f(0.15),
  fgColor: new Float32Array([1, 1, 1]), bgColor: new Float32Array([0, 0, 0]),
})
const nondefault = Object.freeze({
  scale: f(18.25), rotation: f(17.375), thickness: f(0.34), smoothness: f(0.0275),
  rings: 4, starPoints: 7, speed: f(2.75), pulseDepth: f(0.31),
  fgColor: new Float32Array([f(0.92), f(0.67), f(0.21)]),
  bgColor: new Float32Array([f(0.07), f(0.16), f(0.31)]),
})

const caseDefinitions = Object.freeze([
  {
    name: 'geometry-0-flower-default-control', time: context.time,
    uniforms: { ...defaults },
    coverage: ['metadata-defaults', 'geometry-0-flower', 'non-array-control', 'nested-q-r-13x13', 'animation-off'],
  },
  {
    name: 'geometry-1-fruit-animation-off', time: context.time,
    uniforms: { ...nondefault, geometry: 1, animation: 0 },
    coverage: ['center-zero', 'inner-affine-ring-1-plus-k', 'outer-affine-ring-7-plus-k', 'circle-i-read-sites', 'drawLines-false'],
  },
  {
    name: 'geometry-3-metatron-animation-off', time: context.time,
    uniforms: { ...nondefault, geometry: 3, animation: 0 },
    coverage: ['all-13-centers', 'circle-i-read-sites', 'nested-i-j-13x13', 'j-less-than-or-equal-i-continue', '78-unordered-line-pairs', 'centers-i-and-j-line-reads'],
  },
  {
    name: 'geometry-1-fruit-ripple', time: context.time,
    uniforms: { ...nondefault, geometry: 1, animation: 4 },
    coverage: ['all-13-centers', 'distance-read-controls-ripple-phase', 'nondefault-speed-pulseDepth-time', 'F32-center-lane-sensitivity'],
  },
  {
    name: 'geometry-3-metatron-unfold', time: context.unfoldTime,
    uniforms: { ...nondefault, geometry: 3, animation: 5 },
    coverage: ['all-13-centers', 'distance-read-controls-unfold', 'circleUnfoldRange-0.6f', 'lineVis-unfoldVis-0.65f', '78-line-pairs'],
  },
  {
    name: 'geometry-4-seed-rotate', time: context.time,
    uniforms: { ...nondefault, geometry: 4, animation: 1 },
    coverage: ['geometry-4-seed', 'non-array-control', 'main-rotate-animation'],
  },
  {
    name: 'geometry-5-vesica-pulse', time: context.time,
    uniforms: { ...nondefault, geometry: 5, animation: 2 },
    coverage: ['geometry-5-vesica', 'non-array-control', 'main-pulse-animation'],
  },
  {
    name: 'geometry-6-borromean-ripple', time: context.time,
    uniforms: { ...nondefault, geometry: 6, animation: 4 },
    coverage: ['geometry-6-borromean', 'non-array-control', 'three-trip-loop', 'ripple-animation'],
  },
  {
    name: 'geometry-7-star-animation-off', time: context.time,
    uniforms: { ...nondefault, scale: f(10.75), geometry: 7, animation: 0, starPoints: 7 },
    expectedNonfiniteRgb: true,
    coverage: ['geometry-7-starPolygon', 'non-array-control', 'nondefault-starPoints', '12-trip-loop-with-break', 'animation-off', 'canonical-untruncated-integer-division-produces-degenerate-i0-segment', 'all-RGB-canonical-qNaN-alpha-one'],
  },
  {
    name: 'geometry-8-triquetra-rotate', time: context.time,
    uniforms: { ...nondefault, geometry: 8, animation: 1 },
    coverage: ['geometry-8-triquetra', 'non-array-control', 'main-rotate-animation'],
  },
])

function uniformRecord(name, value) {
  if (floatUniformNames.has(name)) return { glsl_type: 'float', value, f32_bits_le: f32Bits(value) }
  if (intUniformNames.has(name)) return { glsl_type: 'int', value }
  if (vectorUniformNames.has(name)) {
    const values = Array.from(value)
    return { glsl_type: 'vec3', values, f32_bits_le: values.map(f32Bits) }
  }
  throw new Error(`unrecorded uniform ${name}`)
}

function recordedUniforms(uniforms) {
  return Object.fromEntries(Object.entries(uniforms).map(([name, value]) => [name, uniformRecord(name, value)]))
}

function render(factory, definition) {
  const [width, height] = dimensions.output
  const kernel = bindCanonicalKernel(factory, {
    width, height, time: definition.time, frame: context.frame, deltaTime: context.deltaTime,
    seed: context.seed, tileOffset: new Float32Array(dimensions.tileOffset),
    fullResolution: new Float32Array(dimensions.fullResolution), uniforms: definition.uniforms,
  })
  const destination = new Surface(width, height)
  runPass({ kernel, destination, time: definition.time, seed: context.seed })
  return destination
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at: [x, y], values: values.map(printable), f32_bits_le: values.map(f32Bits) }
}

function surfaceMetrics(surface, uniforms) {
  let finiteLanes = 0
  let nonfiniteRgbLanes = 0
  let alphaOnePixels = 0
  let backgroundPixels = 0
  let foregroundPixels = 0
  let mixedPixels = 0
  let minRgb = Infinity
  let maxRgb = -Infinity
  const bg = uniforms.bgColor
  const fg = uniforms.fgColor
  for (let pixel = 0; pixel < surface.width * surface.height; pixel += 1) {
    const offset = pixel * 4
    const rgb = surface.data.subarray(offset, offset + 3)
    for (const lane of surface.data.subarray(offset, offset + 4)) if (Number.isFinite(lane)) finiteLanes += 1
    for (const lane of rgb) if (!Number.isFinite(lane)) nonfiniteRgbLanes += 1
    if (surface.data[offset + 3] === 1) alphaOnePixels += 1
    const isBackground = rgb.every((lane, index) => lane === bg[index])
    const isForeground = rgb.every((lane, index) => lane === fg[index])
    if (isBackground) backgroundPixels += 1
    else if (isForeground) foregroundPixels += 1
    else mixedPixels += 1
    for (const lane of rgb) if (Number.isFinite(lane)) { minRgb = Math.min(minRgb, lane); maxRgb = Math.max(maxRgb, lane) }
  }
  return {
    pixels: surface.width * surface.height,
    finite_lanes: finiteLanes,
    nonfinite_rgb_lanes: nonfiniteRgbLanes,
    alpha_exactly_one_pixels: alphaOnePixels,
    exact_background_pixels: backgroundPixels,
    exact_foreground_pixels: foregroundPixels,
    mixed_rgb_pixels: mixedPixels,
    min_rgb: minRgb === Infinity ? 'no-finite-rgb' : minRgb,
    max_rgb: maxRgb === -Infinity ? 'no-finite-rgb' : maxRgb,
  }
}

const canonicalSurfaces = new Map()
function caseResult(definition) {
  const first = render(canonicalFactory, definition)
  const second = render(canonicalFactory, definition)
  const firstRgba8 = first.toRgba8()
  const secondRgba8 = second.toRgba8()
  if (!sameBytes(first.data, second.data) || !sameBytes(firstRgba8, secondRgba8)) {
    throw new Error(`${definition.name}: canonical repeat was not byte-identical`)
  }
  const metrics = surfaceMetrics(first, definition.uniforms)
  if (metrics.alpha_exactly_one_pixels !== metrics.pixels) {
    throw new Error(`${definition.name}: non-opaque alpha`)
  }
  if (definition.expectedNonfiniteRgb) {
    if (metrics.nonfinite_rgb_lanes !== metrics.pixels * 3 || metrics.finite_lanes !== metrics.pixels) {
      throw new Error(`${definition.name}: expected exact all-RGB-NaN canonical profile`)
    }
  } else if (metrics.finite_lanes !== metrics.pixels * 4 || metrics.nonfinite_rgb_lanes !== 0) {
    throw new Error(`${definition.name}: unexpected nonfinite lane`)
  }
  if (!definition.expectedNonfiniteRgb && (metrics.exact_background_pixels === metrics.pixels || metrics.mixed_rgb_pixels === 0)) {
    throw new Error(`${definition.name}: background-dominated or binary-only fixture`)
  }
  canonicalSurfaces.set(definition.name, first)
  return {
    name: definition.name,
    key,
    time: { value: definition.time, f32_bits_le: f32Bits(definition.time) },
    uniforms: recordedUniforms(definition.uniforms),
    coverage: definition.coverage,
    f32_sha256: sha256(bytes(first.data)),
    rgba8_sha256: sha256(bytes(firstRgba8)),
    probes: probeCoordinates.map(([x, y]) => probe(first, x, y)),
    metrics,
    repeat_identity: { f32_bytes: true, rgba8_bytes: true },
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

const mutationDefinitions = Object.freeze([
  {
    name: 'center-zero-value-offset',
    contract: 'changes the explicit center[0] vector from [0,0] to [0.375,-0.25] without changing array shape',
    replacements: [{
      from: '(centers[0][0] = 0, centers[0][1] = 0, centers[0]);',
      to: '(centers[0][0] = 0.375, centers[0][1] = -0.25, centers[0]);', count: 1,
    }],
    mustDiverge: ['geometry-1-fruit-animation-off', 'geometry-3-metatron-animation-off'],
  },
  {
    name: 'inner-affine-store-1-plus-k-to-2-plus-k',
    contract: 'leaves index 1 zero-filled, overlaps index 7, and removes one inner-ring center',
    replacements: [{ from: 'centers[1 + k]', to: 'centers[2 + k]', count: 3 }],
    mustDiverge: ['geometry-3-metatron-animation-off', 'geometry-1-fruit-ripple'],
  },
  {
    name: 'outer-affine-store-7-plus-k-to-6-plus-k',
    contract: 'overlaps index 6, leaves index 12 zero-filled, and removes one outer-ring center',
    replacements: [{ from: 'centers[7 + k]', to: 'centers[6 + k]', count: 3 }],
    mustDiverge: ['geometry-3-metatron-animation-off', 'geometry-1-fruit-ripple'],
  },
  {
    name: 'circle-distance-read-i-to-zero',
    contract: 'replaces only length(centers[i]) with length(centers[0])',
    replacements: [{ from: 'length(centers[i])', to: 'length(centers[0])', count: 1 }],
    mustDiverge: ['geometry-1-fruit-ripple', 'geometry-3-metatron-unfold'],
  },
  {
    name: 'circle-position-read-i-to-zero',
    contract: 'replaces only the circle SDF endpoint centers[i] with centers[0]',
    replacements: [{ from: 'vec2.subtract([], p, centers[i])', to: 'vec2.subtract([], p, centers[0])', count: 1 }],
    mustDiverge: ['geometry-1-fruit-animation-off', 'geometry-3-metatron-animation-off'],
  },
  {
    name: 'line-endpoint-read-j-to-twelve',
    contract: 'replaces only the line endpoint centers[j] with in-range centers[12], collapsing the complete pair graph without degenerate self-lines',
    replacements: [{ from: 'lineSegmentSDF(p, centers[i], centers[j])', to: 'lineSegmentSDF(p, centers[i], centers[12])', count: 1 }],
    mustDiverge: ['geometry-3-metatron-animation-off', 'geometry-3-metatron-unfold'],
  },
  {
    name: 'inner-ring-index-permutation-symmetry-stress',
    contract: 'permutes the same six inner-ring vectors across indices; Fruit is set-symmetric while Metatron can expose endpoint-order F32 differences',
    replacements: [{ from: 'centers[1 + k]', to: 'centers[1 + ((k + 1) % 6)]', count: 3 }],
    mustDiverge: ['geometry-3-metatron-animation-off'],
    mustMatch: ['geometry-1-fruit-animation-off', 'geometry-1-fruit-ripple'],
  },
])

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
  for (let index = 0; index < referenceBytes.length; index += 1) {
    if (referenceBytes[index] !== mutatedBytes[index]) f32ByteDifferences += 1
  }
  for (let index = 0; index < reference.data.length; index += 1) {
    if (!Object.is(reference.data[index], mutated.data[index])) {
      f32LaneDifferences += 1
      if (Number.isFinite(reference.data[index]) && Number.isFinite(mutated.data[index])) {
        maxAbsoluteDifference = Math.max(maxAbsoluteDifference, Math.abs(reference.data[index] - mutated.data[index]))
      } else {
        nonfiniteLaneTransitions += 1
      }
    }
  }
  for (let index = 0; index < referenceRgba8.length; index += 1) {
    if (referenceRgba8[index] !== mutatedRgba8[index]) rgba8ByteDifferences += 1
  }
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

function integerDivisionCompatibilityResult() {
  const starCase = caseDefinitions.find(item => item.name === 'geometry-7-star-animation-off')
  const reference = canonicalSurfaces.get(starCase.name)
  const replacement = {
    from: 'var j = (i + 2) - ((i + 2) / n) * n;',
    to: 'var j = (i + 2) % n;',
    count: 1,
  }
  const { factory, applied } = replacedFactory('star-intended-integer-remainder', [replacement])
  const intended = render(factory, starCase)
  const intendedMetrics = surfaceMetrics(intended, starCase.uniforms)
  if (intendedMetrics.nonfinite_rgb_lanes !== 0 || intendedMetrics.finite_lanes !== intendedMetrics.pixels * 4
      || intendedMetrics.alpha_exactly_one_pixels !== intendedMetrics.pixels) {
    throw new Error('star intended-integer-remainder control was not finite and opaque')
  }
  const difference = diffSummary(reference, intended)
  if (difference.same_f32_bytes || difference.nonfinite_lane_transitions !== intendedMetrics.pixels * 3) {
    throw new Error('star integer-division compatibility probe did not expose all canonical NaN RGB lanes')
  }
  const starPointsMatrix = []
  for (let starPoints = 5; starPoints <= 12; starPoints += 1) {
    const matrixCase = { ...starCase, uniforms: { ...starCase.uniforms, starPoints } }
    const canonical = starPoints === 7 ? reference : render(canonicalFactory, matrixCase)
    const canonicalMetrics = surfaceMetrics(canonical, matrixCase.uniforms)
    const intendedControl = starPoints === 7 ? intended : render(factory, matrixCase)
    const controlMetrics = surfaceMetrics(intendedControl, matrixCase.uniforms)
    if (canonicalMetrics.nonfinite_rgb_lanes !== canonicalMetrics.pixels * 3
        || canonicalMetrics.alpha_exactly_one_pixels !== canonicalMetrics.pixels) {
      throw new Error(`starPoints=${starPoints}: canonical qNaN profile drift`)
    }
    if (controlMetrics.nonfinite_rgb_lanes !== 0 || controlMetrics.finite_lanes !== controlMetrics.pixels * 4
        || controlMetrics.exact_background_pixels === controlMetrics.pixels || controlMetrics.mixed_rgb_pixels === 0) {
      throw new Error(`starPoints=${starPoints}: intended integer remainder control is not informative`)
    }
    starPointsMatrix.push({
      starPoints,
      canonical_f32_sha256: sha256(bytes(canonical.data)),
      canonical_rgba8_sha256: sha256(bytes(canonical.toRgba8())),
      canonical_nonfinite_rgb_lanes: canonicalMetrics.nonfinite_rgb_lanes,
      intended_control_f32_sha256: sha256(bytes(intendedControl.data)),
      intended_control_rgba8_sha256: sha256(bytes(intendedControl.toRgba8())),
      intended_control_metrics: controlMetrics,
      difference: diffSummary(canonical, intendedControl),
    })
  }
  return {
    source_site: { raw_line: 276, normalized_line: 260, expression: 'int j = (i + 2) - ((i + 2) / n) * n' },
    canonical_factory_expression: replacement.from,
    intended_integer_remainder_control_expression: replacement.to,
    replacement: applied[0],
    canonical_observation: 'JavaScript Number division is not truncated; at i=0, 2-(2/n)*n is +0 for n=7, producing a degenerate a==b segment and qNaN propagation into every RGB lane.',
    native_risk: 'the current typed C++ expression uses int32 operands and truncating C++ integer division, computes the intended remainder, and therefore emits finite star geometry instead of canonical qNaN RGB',
    required_action: 'add an exact key/source/function/span compatibility transform that preserves canonical Number-division behavior, or keep this key unported; do not broaden integer-division semantics globally',
    canonical_qnan_f32_bits_le: '0x7fc00000',
    intended_control_metrics: intendedMetrics,
    intended_control_probes: probeCoordinates.map(([x, y]) => probe(intended, x, y)),
    difference,
    metadata_starPoints_5_through_12: starPointsMatrix,
  }
}

const arrayCaseNames = new Set([
  'geometry-1-fruit-animation-off', 'geometry-3-metatron-animation-off',
  'geometry-1-fruit-ripple', 'geometry-3-metatron-unfold',
])
const nonArrayCaseNames = caseDefinitions.map(item => item.name).filter(name => !arrayCaseNames.has(name))

function mutationResult(definition) {
  const { factory, applied } = replacedFactory(definition.name, definition.replacements)
  const results = []
  const identicalControls = []
  for (const caseDefinition of caseDefinitions) {
    const reference = canonicalSurfaces.get(caseDefinition.name)
    const mutated = render(factory, caseDefinition)
    const diff = diffSummary(reference, mutated)
    if (arrayCaseNames.has(caseDefinition.name)) results.push({ case: caseDefinition.name, ...diff })
    else if (diff.same_f32_bytes && diff.same_rgba8_bytes) identicalControls.push(caseDefinition.name)
    else throw new Error(`${definition.name}: unexpectedly changed non-array control ${caseDefinition.name}`)
  }
  for (const name of definition.mustDiverge ?? []) {
    const result = results.find(item => item.case === name)
    if (!result || result.same_f32_bytes) throw new Error(`${definition.name}: required F32 divergence missing for ${name}`)
  }
  for (const name of definition.mustMatch ?? []) {
    const result = results.find(item => item.case === name)
    if (!result || !result.same_f32_bytes || !result.same_rgba8_bytes) throw new Error(`${definition.name}: required symmetry identity missing for ${name}`)
  }
  if (identicalControls.length !== nonArrayCaseNames.length) throw new Error(`${definition.name}: incomplete non-array control identity`)
  return {
    name: definition.name,
    contract: definition.contract,
    replacements: applied,
    required_divergence_cases: definition.mustDiverge ?? [],
    required_identity_cases: definition.mustMatch ?? [],
    array_case_results: results,
    non_array_controls_byte_identical: identicalControls,
  }
}

function build() {
  const cases = caseDefinitions.map(caseResult)
  const integerDivisionCompatibility = integerDivisionCompatibilityResult()
  const mutations = mutationDefinitions.map(mutationResult)
  return `${JSON.stringify({
    schema: 'noisemaker-for-cpp.task20-fixed-affine-centers13.canonical-oracles.v1',
    corpus_revision: corpusRevision,
    provenance: {
      node: process.version,
      api: 'canonicalKernelFactories+bindCanonicalKernel+runPass+Surface',
      canonical_kernels_path: 'src/effects/generated/canonical-kernels.js',
      canonical_kernels_sha256: expectedCanonicalKernelsSha256,
      factory_name: 'canonicalFactory273',
      factory_to_string_sha256: expectedFactorySha256,
      factory_hash_contract: 'SHA-256 of exact UTF-8 Function.prototype.toString() for canonicalKernelFactories[key]',
      generator: 'task-20-oracle-generator.mjs',
      reference_only: 'all expected images come from the pinned direct canonical CPU factory; mutations are eval-created copies of that exact factory text with counted replacements',
    },
    program: {
      key, source, raw_source_sha256: expectedRawSha256,
      normalized_source_sha256: expectedNormalizedSha256,
      defines: {},
      uniform_binding_signature: [
        'resolution:vec2@1', 'tileOffset:vec2@2', 'fullResolution:vec2@3', 'aspect:float@4',
        'scale:float@5', 'rotation:float@6', 'thickness:float@7', 'smoothness:float@8',
        'geometry:int@9', 'rings:int@10', 'starPoints:int@11', 'animation:int@12',
        'speed:float@13', 'pulseDepth:float@14', 'time:float@15', 'fgColor:vec3@16', 'bgColor:vec3@17',
      ],
      output_signature: 'fragColor:vec4@18',
      pass_route: { inputs: {}, outputs: { color: 'outputTex' }, uniforms: {} },
      samplers: [],
    },
    fixture: {
      output: { width: dimensions.output[0], height: dimensions.output[1], storage: 'top-down Surface Float32Array; lane=(y*width+x)*4' },
      fragment_origin: 'bottom-left: runPass uses fragCoord=(x+0.5,height-y-0.5)',
      resolution: { values: dimensions.output, f32_bits_le: dimensions.output.map(f32Bits) },
      tileOffset: { values: dimensions.tileOffset, f32_bits_le: dimensions.tileOffset.map(f32Bits) },
      fullResolution: { values: dimensions.fullResolution, f32_bits_le: dimensions.fullResolution.map(f32Bits) },
      aspect: { value: f(dimensions.output[0] / dimensions.output[1]), f32_bits_le: f32Bits(f(dimensions.output[0] / dimensions.output[1])), source: 'createCanonicalBindings width/height' },
      frame: context.frame,
      deltaTime: { value: context.deltaTime, f32_bits_le: f32Bits(context.deltaTime) },
      seed: { value: context.seed, f32_bits_le: f32Bits(context.seed) },
      probe_coordinates: probeCoordinates,
      array_execution: {
        initialization: 'centers[0], centers[1+k] for k=0..5, centers[7+k] for k=0..5; 13 F32 vec2 writes total',
        fruit: '13 circle iterations, 26 center reads, no line grid',
        metatron: '13 circle iterations plus 13x13 line grid; j<=i continues 91 times, accepts 78 pairs, total 182 center reads',
      },
      verification: 'each canonical case double-renders with fresh destinations and requires identical F32/RGBA8 bytes and exact opaque alpha; ordinary branches require all-finite non-background mixed output, while geometry 7 requires the pinned all-RGB-qNaN canonical profile',
    },
    cases,
    integer_division_compatibility: integerDivisionCompatibility,
    mutation_sensitivity: {
      purpose: 'demonstrate that the frozen fixture detects center value, both affine initialization regions, both circle read roles, and the nested j endpoint where observable; exact source-shape proof remains mandatory for symmetry-equivalent changes',
      array_cases: Array.from(arrayCaseNames),
      non_array_controls: nonArrayCaseNames,
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
  throw new Error('usage: node task-20-oracle-generator.mjs [--write|--check]')
}
