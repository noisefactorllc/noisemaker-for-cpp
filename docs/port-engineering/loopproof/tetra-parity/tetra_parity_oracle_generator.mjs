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
const outputPath = path.join(here, 'tetra-parity-oracles.json')
const reportPath = path.join(here, 'tetra-parity-oracle-report.md')
const programKey = 'filter/tetraColorArray:tetraColorArray'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/tetraColorArray/tetraColorArray.glsl')
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

// Purpose-built parity comparer: equality is Float32 bit equality, including
// signed zero and NaN payloads. Diagnostics are additive and never replace the
// byte/hash contract.
function compareFloat32Buffers(reference, candidate) {
  if (!(reference instanceof Float32Array) || !(candidate instanceof Float32Array)) {
    throw new TypeError('compareFloat32Buffers requires two Float32Array values')
  }
  if (reference.length !== candidate.length) {
    return {
      exact_f32_bits: false,
      reference_lanes: reference.length,
      candidate_lanes: candidate.length,
      mismatched_lanes: Math.max(reference.length, candidate.length),
      first_mismatch_lane: 0,
      max_absolute_difference: null,
    }
  }
  const referenceBits = new Uint32Array(reference.buffer, reference.byteOffset, reference.length)
  const candidateBits = new Uint32Array(candidate.buffer, candidate.byteOffset, candidate.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let i = 0; i < reference.length; i += 1) {
    if (referenceBits[i] === candidateBits[i]) continue
    mismatched += 1
    if (first === null) first = i
    const difference = Math.abs(reference[i] - candidate[i])
    if (Number.isFinite(difference)) maxAbsoluteDifference = Math.max(maxAbsoluteDifference, difference)
  }
  return {
    exact_f32_bits: mismatched === 0,
    reference_lanes: reference.length,
    candidate_lanes: candidate.length,
    mismatched_lanes: mismatched,
    first_mismatch_lane: first,
    max_absolute_difference: maxAbsoluteDifference,
  }
}

function compareRgba8Buffers(reference, candidate) {
  if (reference.length !== candidate.length) throw new Error('RGBA8 length mismatch')
  let mismatched = 0
  let first = null
  for (let i = 0; i < reference.length; i += 1) {
    if (reference[i] === candidate[i]) continue
    mismatched += 1
    if (first === null) first = i
  }
  return { exact_rgba8_bytes: mismatched === 0, mismatched_bytes: mismatched, first_mismatch_byte: first }
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
if (sourceBytes.length !== 9754 || sha256(sourceBytes) !== '68c7cabce311a0a05ba116ce8d34bd5e70e0c09bfb8eab06c93f4f9e01fa5438') {
  throw new Error('pinned tetraColorArray GLSL source drift')
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory158') throw new Error('canonical factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 10795 || sha256(canonicalFactory.toString()) !== '839315b44a68ea9c712dca226754ea55c2283f6ea0ef30d4c79cd831f97036ff') {
  throw new Error('canonical factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected tetraColorArray adapter override')

const effect = effectRecords.find((record) => record.id === 'filter/tetraColorArray')
if (!effect) throw new Error('tetraColorArray metadata record missing')
const colorCountMetadata = effect.params?.colorCount
if (JSON.stringify(colorCountMetadata) !== JSON.stringify({ type: 'int', default: 6, uniform: 'colorCount', min: 2, max: 8 })) {
  throw new Error(`colorCount metadata drift: ${JSON.stringify(colorCountMetadata)}`)
}

const uniformTypes = {
  colorMode: 'int', colorCount: 'int', positionMode: 'int',
  color0: 'vec3', color1: 'vec3', color2: 'vec3', color3: 'vec3',
  color4: 'vec3', color5: 'vec3', color6: 'vec3', color7: 'vec3',
  pos0: 'float', pos1: 'float', pos2: 'float', pos3: 'float',
  pos4: 'float', pos5: 'float', pos6: 'float', pos7: 'float',
  repeat: 'float', offset: 'float', smoothness: 'float', alpha: 'float', rotation: 'int',
}

const palette = [
  [0.96, 0.04, 0.18], [0.98, 0.72, 0.06], [0.12, 0.88, 0.26], [0.05, 0.35, 0.96],
  [0.74, 0.08, 0.94], [0.08, 0.90, 0.82], [0.96, 0.96, 0.90], [0.04, 0.03, 0.08],
]

const targetLuminances = [0, 0.005, 0.03, 0.12, 0.22, 0.34, 0.50, 0.66, 0.78, 0.88, 0.96, 0.995, 1]
const probePoints = [
  ['wrap-low', 0, 0], ['wrap-high', 12, 0], ['transition-low', 3, 0],
  ['transition-middle', 6, 0], ['transition-high', 9, 0], ['colored-interior', 5, 2],
]

function typedUniforms(raw) {
  const out = {}
  for (const [name, value] of Object.entries(raw)) {
    const type = uniformTypes[name]
    if (!type) throw new Error(`unknown uniform ${name}`)
    if (type === 'int') out[name] = value | 0
    else if (type === 'float') out[name] = f(value)
    else if (type === 'vec3') out[name] = new Float32Array(value.map(f))
    else throw new Error(`unsupported uniform type ${type}`)
  }
  return out
}

function completeUniforms(definition) {
  const positions = definition.positions ?? [0, 0.14, 0.29, 0.43, 0.57, 0.71, 0.86, 1]
  const raw = {
    colorMode: definition.colorMode,
    colorCount: definition.colorCount,
    positionMode: definition.positionMode,
    repeat: definition.repeat ?? 1,
    offset: definition.offset ?? 0,
    smoothness: definition.smoothness,
    alpha: definition.alpha,
    rotation: 0,
  }
  for (let i = 0; i < 8; i += 1) {
    raw[`color${i}`] = palette[i]
    raw[`pos${i}`] = positions[i] ?? 1
  }
  return typedUniforms(raw)
}

function inputSurface(width, height, phase) {
  if (width !== targetLuminances.length) throw new Error('input width must retain the pinned luminance probe row')
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      if (y === 0) {
        const luminance = f(targetLuminances[x])
        data[i] = luminance
        data[i + 1] = luminance
        data[i + 2] = luminance
      } else {
        data[i] = f((((37 * x + 17 * y + 13 * phase) % 101) + 1) / 103)
        data[i + 1] = f((((19 * x + 43 * y + 23 * phase) % 97) + 2) / 101)
        data[i + 2] = f((((61 * x + 29 * y + 31 * phase) % 89) + 3) / 97)
      }
      data[i + 3] = f((((7 * x + 11 * y + phase) % 29) + 7) / 41)
    }
  }
  return new Surface(width, height, data)
}

const cases = [
  { name: 'count2-rgb-auto-hard-alpha0', height: 3, phase: 1, colorMode: 0, colorCount: 2, positionMode: 0, smoothness: 0, alpha: 0 },
  { name: 'count2-hsv-manual-wrap-alpha1', height: 4, phase: 2, colorMode: 1, colorCount: 2, positionMode: 1, positions: [0.08, 0.90, 1, 1, 1, 1, 1, 1], smoothness: 0.8, alpha: 1, wrapSeam: true },
  { name: 'count3-oklab-auto-smooth-alpha1', height: 5, phase: 3, colorMode: 2, colorCount: 3, positionMode: 0, smoothness: 0.55, alpha: 1, wrapSeam: true },
  { name: 'count4-oklch-manual-smooth-alpha-half', height: 6, phase: 4, colorMode: 3, colorCount: 4, positionMode: 1, positions: [0, 0.18, 0.67, 1, 1, 1, 1, 1], smoothness: 0.6, alpha: 0.5 },
  { name: 'count6-rgb-manual-hard-alpha1', height: 4, phase: 5, colorMode: 0, colorCount: 6, positionMode: 1, positions: [0, 0.08, 0.23, 0.47, 0.81, 1, 1, 1], smoothness: 0, alpha: 1 },
  { name: 'count6-oklch-auto-wrap-alpha1', height: 5, phase: 6, colorMode: 3, colorCount: 6, positionMode: 0, smoothness: 0.9, alpha: 1, wrapSeam: true },
  { name: 'count8-hsv-auto-wrap-alpha1', height: 6, phase: 7, colorMode: 1, colorCount: 8, positionMode: 0, smoothness: 1, alpha: 1, wrapSeam: true },
  { name: 'count8-oklab-manual-wrap-alpha065', height: 5, phase: 8, colorMode: 2, colorCount: 8, positionMode: 1, positions: [0.06, 0.14, 0.26, 0.39, 0.55, 0.70, 0.84, 0.93], smoothness: 0.5, alpha: 0.65, wrapSeam: true },
]

function assertObservedBindings(bindings, uniforms, definition) {
  for (const [name, intended] of Object.entries(uniforms)) {
    const observed = bindings[name]
    if (ArrayBuffer.isView(intended)) {
      if (!compareFloat32Buffers(intended, observed).exact_f32_bits) throw new Error(`${definition.name}: binding drift for ${name}`)
    } else if (uniformTypes[name] === 'int') {
      if (observed !== intended) throw new Error(`${definition.name}: integer binding drift for ${name}`)
    } else if (f32Bits(observed) !== f32Bits(intended)) {
      throw new Error(`${definition.name}: scalar binding drift for ${name}`)
    }
  }
}

function render(factory, definition, uniforms, input) {
  const before = input.data.slice()
  const bindings = createCanonicalBindings({
    width: input.width,
    height: input.height,
    time: 0,
    frame: 37,
    deltaTime: f(1 / 60),
    seed: f(4242),
    uniforms,
    textures: { inputTex: input },
  })
  assertObservedBindings(bindings, uniforms, definition)
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(input.width, input.height)
  runPass({ kernel, destination: output, time: 0, seed: f(4242) })
  const immutability = compareFloat32Buffers(before, input.data)
  if (!immutability.exact_f32_bits) throw new Error(`${definition.name}: input texture mutated`)
  return output
}

function probe(surface, label, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { label, at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}

function selectedProbes(surface) {
  return probePoints.map(([label, x, y]) => probe(surface, label, x, Math.min(y, surface.height - 1)))
}

function outputRecord(surface) {
  let nonfinite = 0
  for (const value of surface.data) if (!Number.isFinite(value)) nonfinite += 1
  if (nonfinite !== 0) throw new Error('nonfinite output')
  const rgba8 = surface.toRgba8()
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(rgba8)),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    discriminating_probes: selectedProbes(surface),
  }
}

function compareSurfaces(reference, candidate) {
  return {
    float32: compareFloat32Buffers(reference.data, candidate.data),
    rgba8: compareRgba8Buffers(reference.toRgba8(), candidate.toRgba8()),
    candidate_f32_sha256: sha256(bytes(candidate.data)),
    candidate_rgba8_sha256: sha256(bytes(candidate.toRgba8())),
  }
}

function seamDifference(reference, candidate) {
  const seamLanes = []
  for (const x of [0, reference.width - 1]) {
    for (let lane = 0; lane < 4; lane += 1) seamLanes.push((x * 4) + lane)
  }
  let mismatched = 0
  for (const lane of seamLanes) if (f32Bits(reference.data[lane]) !== f32Bits(candidate.data[lane])) mismatched += 1
  return { compared_top_row_wrap_lanes: seamLanes.length, mismatched_f32_lanes: mismatched }
}

function plainUniforms(uniforms) {
  return Object.fromEntries(Object.entries(uniforms).map(([name, value]) => [name, ArrayBuffer.isView(value) ? Array.from(value) : value]))
}

function buildData() {
  const caseResults = cases.map((definition) => {
    const width = targetLuminances.length
    const input = inputSurface(width, definition.height, definition.phase)
    const inputBefore = input.data.slice()
    const uniforms = completeUniforms(definition)
    const canonical = render(canonicalFactory, definition, uniforms, input)
    const repeated = render(canonicalFactory, definition, uniforms, input)
    const repeatComparison = compareSurfaces(canonical, repeated)
    if (!repeatComparison.float32.exact_f32_bits || !repeatComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: repeat render mismatch`)

    const publicOutput = render(publicFactory, definition, uniforms, input)
    const catalogComparison = compareSurfaces(canonical, publicOutput)
    if (!catalogComparison.float32.exact_f32_bits || !catalogComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: public/catalog render mismatch`)

    const controls = {}
    if (definition.colorMode !== 0 && definition.alpha !== 0) {
      const control = render(canonicalFactory, definition, typedUniforms({ ...plainUniforms(uniforms), colorMode: 0 }), input)
      controls.rgb_mode = compareSurfaces(canonical, control)
      if (controls.rgb_mode.float32.exact_f32_bits) throw new Error(`${definition.name}: colorMode branch was not discriminated`)
    }
    if (definition.positionMode === 1 && definition.alpha !== 0) {
      const control = render(canonicalFactory, definition, typedUniforms({ ...plainUniforms(uniforms), positionMode: 0 }), input)
      controls.auto_position = compareSurfaces(canonical, control)
      if (controls.auto_position.float32.exact_f32_bits) throw new Error(`${definition.name}: manual position branch was not discriminated`)
    }
    if (definition.smoothness > 0 && definition.alpha !== 0) {
      const control = render(canonicalFactory, definition, typedUniforms({ ...plainUniforms(uniforms), smoothness: 0 }), input)
      controls.zero_smoothness = compareSurfaces(canonical, control)
      controls.zero_smoothness.wrap_seam = seamDifference(canonical, control)
      if (controls.zero_smoothness.float32.exact_f32_bits) throw new Error(`${definition.name}: smoothness branch was not discriminated`)
      if (definition.wrapSeam && controls.zero_smoothness.wrap_seam.mismatched_f32_lanes === 0) throw new Error(`${definition.name}: wrap seam was not discriminated`)
    }
    if (definition.colorCount > 2 && definition.alpha !== 0) {
      const control = render(canonicalFactory, definition, typedUniforms({ ...plainUniforms(uniforms), colorCount: definition.colorCount - 1 }), input)
      controls.count_minus_one = compareSurfaces(canonical, control)
      if (controls.count_minus_one.float32.exact_f32_bits) throw new Error(`${definition.name}: colorCount was not discriminated`)
    }

    if (definition.alpha === 0) {
      const alphaZeroComparison = compareFloat32Buffers(inputBefore, canonical.data)
      if (!alphaZeroComparison.exact_f32_bits) throw new Error(`${definition.name}: alpha=0 did not preserve the exact input`)
      controls.alpha_zero_input_identity = alphaZeroComparison
    }
    for (let i = 3; i < canonical.data.length; i += 4) {
      if (f32Bits(canonical.data[i]) !== f32Bits(inputBefore[i])) throw new Error(`${definition.name}: source alpha lane changed`)
    }

    return {
      name: definition.name,
      dimensions: { width, height: definition.height },
      seed: 4242,
      time: 0,
      uniforms: plainUniforms(uniforms),
      coverage: {
        color_mode: definition.colorMode,
        color_count: definition.colorCount,
        position_mode: definition.positionMode === 0 ? 'auto' : 'manual',
        smoothness: definition.smoothness,
        wrap_seam_discriminated: Boolean(definition.wrapSeam),
        alpha: definition.alpha,
      },
      input: {
        f32_sha256_before: sha256(bytes(inputBefore)),
        f32_sha256_after: sha256(bytes(input.data)),
        immutable: compareFloat32Buffers(inputBefore, input.data),
        probes: selectedProbes(input),
      },
      output: outputRecord(canonical),
      repeat_identity: repeatComparison,
      public_catalog_vs_direct_canonical: catalogComparison,
      discriminating_controls: controls,
    }
  })

  const dimensions = {
    color_modes: [...new Set(caseResults.map((record) => record.coverage.color_mode))].sort(),
    color_counts: [...new Set(caseResults.map((record) => record.coverage.color_count))].sort((a, b) => a - b),
    position_modes: [...new Set(caseResults.map((record) => record.coverage.position_mode))].sort(),
    smoothness_zero_cases: caseResults.filter((record) => record.coverage.smoothness === 0).length,
    smoothness_nonzero_cases: caseResults.filter((record) => record.coverage.smoothness > 0).length,
    wrap_seam_cases: caseResults.filter((record) => record.coverage.wrap_seam_discriminated).length,
    alpha_values: [...new Set(caseResults.map((record) => record.coverage.alpha))].sort((a, b) => a - b),
  }
  if (JSON.stringify(dimensions.color_modes) !== '[0,1,2,3]') throw new Error('incomplete colorMode coverage')
  if (JSON.stringify(dimensions.color_counts) !== '[2,3,4,6,8]') throw new Error('incomplete colorCount coverage')
  if (JSON.stringify(dimensions.position_modes) !== '["auto","manual"]') throw new Error('incomplete positionMode coverage')
  if (!dimensions.alpha_values.includes(0) || !dimensions.alpha_values.includes(1)) throw new Error('alpha endpoints missing')
  if (!dimensions.smoothness_zero_cases || !dimensions.smoothness_nonzero_cases || !dimensions.wrap_seam_cases) throw new Error('smoothness/wrap coverage missing')

  return {
    schema: 'noisemaker-for-cpp.tetra-color-array.pixel-parity-oracle.v1',
    program_key: programKey,
    corpus_revision: corpusRevision,
    upstream_revision: UPSTREAM_REVISION,
    provenance: {
      node: process.version,
      reference_api: 'canonicalKernelFactories[program_key] via bindGlslKernel and createCanonicalBindings',
      public_api: 'kernelFactories.get(program_key)',
      canonical_factory_name: canonicalFactory.name,
      canonical_factory_to_string_sha256: sha256(canonicalFactory.toString()),
      source_raw_bytes: sourceBytes.length,
      source_sha256: sha256(sourceBytes),
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    metadata_contract: { parameter: 'colorCount', type: 'int', minimum: 2, default: 6, maximum: 8 },
    fixture: {
      input: '13-wide top row of pinned grayscale wrap/transition probes plus asymmetric colored rows; top-down Float32 RGBA',
      target_top_row_luminances: targetLuminances,
      fragment_origin: 'bottom-left GLSL coordinates over top-down Surface storage',
      comparer: 'exact Float32 bit comparer with mismatch diagnostics; RGBA8 byte comparer; hashes remain authoritative',
      repeated_render_count: 2,
    },
    coverage_summary: dimensions,
    cases: caseResults,
  }
}

function makeReport(data) {
  const lines = [
    '# Tetra Color Array pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `filter/tetraColorArray:tetraColorArray`, rendered through the canonical noisemaker-for-cpu factory. Float32 hashes are exact byte contracts; RGBA8 hashes are a second exact byte contract. The custom comparer only adds diagnostics and does not relax either contract.', '',
    '## Coverage', '',
    `- Color modes: ${data.coverage_summary.color_modes.join(', ')}`,
    `- Color counts: ${data.coverage_summary.color_counts.join(', ')}`,
    `- Position modes: ${data.coverage_summary.position_modes.join(', ')}`,
    `- Smoothness: ${data.coverage_summary.smoothness_zero_cases} zero cases and ${data.coverage_summary.smoothness_nonzero_cases} nonzero cases`,
    `- Explicitly discriminated wrap seams: ${data.coverage_summary.wrap_seam_cases} cases`,
    `- Alpha values (including both endpoints): ${data.coverage_summary.alpha_values.join(', ')}`, '',
    'Every case passes exact repeated-render identity, input immutability, finite-output, source-alpha preservation, and public-catalog-versus-direct-canonical equality. Non-RGB, manual-position, nonzero-smoothness, and count-above-two cases also carry a deliberately changed control render that is required to diverge.', '',
    '## Cases', '',
    '| Case | Mode | Count | Positions | Smoothness | Alpha | Wrap seam | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | ---: | ---: | --- | ---: | ---: | --- | --- | --- |',
  ]
  for (const record of data.cases) {
    const c = record.coverage
    lines.push(`| ${record.name} | ${c.color_mode} | ${c.color_count} | ${c.position_mode} | ${c.smoothness} | ${c.alpha} | ${c.wrap_seam_discriminated} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', '## Probe and determinism contract', '')
  lines.push('- Each output records exact Float32 values and little-endian bits at both sides of the `fract` wrap seam, three interior transition points, and one asymmetric colored-input point.')
  lines.push('- The top-row seam probes are driven by grayscale luminances 0 and 1; the shader maps them to opposite sides of the repeated gradient seam. Every case marked as a wrap case is required to differ at those seam lanes from its otherwise-identical `smoothness=0` control.')
  lines.push('- Each render uses seed 4242, time 0, frame 37, and delta time 1/60. No elapsed timing or host-specific path is serialized.')
  lines.push('- The generator rejects drift in the canonical/public/adapter/runtime files, canonical factory body, GLSL source, catalog identity, adapter absence, and authoritative `colorCount` metadata contract.', '')
  lines.push('## Reference provenance', '')
  lines.push(`- Upstream snapshot revision: \`${data.upstream_revision}\``)
  lines.push(`- Corpus revision: \`${data.corpus_revision}\``)
  lines.push(`- GLSL source SHA-256: \`${data.provenance.source_sha256}\``)
  lines.push(`- Canonical factory SHA-256: \`${data.provenance.canonical_factory_to_string_sha256}\``)
  lines.push(`- Node reference engine used to freeze this file: \`${data.provenance.node}\``)
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = makeReport(data)

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outputPath) || fs.readFileSync(outputPath, 'utf8') !== json) throw new Error('tetra parity JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('tetra parity report drift')
  console.log(`tetra parity oracle ok (${data.cases.length} cases, Float32+RGBA8 exact contracts)`)
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  console.log(outputPath)
  console.log(reportPath)
}
