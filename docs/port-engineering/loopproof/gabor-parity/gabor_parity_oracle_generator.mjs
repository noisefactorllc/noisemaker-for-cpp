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
const outputPath = path.join(here, 'gabor-parity-oracles.json')
const reportPath = path.join(here, 'gabor-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const proofProbePath = path.join(here, 'gabor_loop_proof_probe.py')
const programKey = 'synth/gabor:gabor'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/synth/gabor/gabor.glsl')
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

// Purpose-built comparer for Gabor parity. Equality is raw Float32 bit
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
if (sourceBytes.length !== 3870 || sha256(sourceBytes) !== '91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5') {
  throw new Error('pinned Gabor GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory249') throw new Error('canonical Gabor factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 4405 || sha256(canonicalFactory.toString()) !== '1a761bd2b1ab87e781ca4d7a1fc622ed450035b9695115a84e59fb36e6718c57') {
  throw new Error('canonical Gabor factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog Gabor factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Gabor adapter override')

const expectedParams = {
  scale: { type: 'float', default: 75, uniform: 'scale', min: 1, max: 100 },
  orientation: { type: 'float', default: 0, uniform: 'orientation', min: -180, max: 180 },
  bandwidth: { type: 'float', default: 75, uniform: 'bandwidth', min: 1, max: 100 },
  isotropy: { type: 'float', default: 0, uniform: 'isotropy', min: 0, max: 100 },
  density: { type: 'int', default: 3, uniform: 'density', min: 1, max: 8 },
  octaves: { type: 'int', default: 1, uniform: 'octaves', min: 1, max: 5 },
  speed: { type: 'int', default: 1, uniform: 'speed', min: 0, max: 5, zero: 0 },
  seed: { type: 'int', default: 1, uniform: 'seed', min: 1, max: 100 },
}
const effect = effectRecords.find((record) => record.id === 'synth/gabor')
if (!effect) throw new Error('Gabor metadata record missing')
for (const [name, expected] of Object.entries(expectedParams)) {
  const actual = effect.params?.[name]
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`Gabor ${name} metadata drift: ${JSON.stringify(actual)}`)
}
if (effect.func !== 'gabor' || effect.kind !== 'generator' || effect.namespace !== 'synth' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'gabor') {
  throw new Error('Gabor effect/pass interface drift')
}

const expectedUniformDeclarations = [
  ['resolution', 'vec2'], ['tileOffset', 'vec2'], ['fullResolution', 'vec2'],
  ['time', 'float'], ['seed', 'float'], ['scale', 'float'], ['orientation', 'float'],
  ['bandwidth', 'float'], ['isotropy', 'float'], ['density', 'float'],
  ['octaves', 'float'], ['speed', 'float'],
]
for (const [name, type] of expectedUniformDeclarations) {
  const anchor = `uniform ${type} ${name};`
  if (sourceText.split(anchor).length !== 2) throw new Error(`Gabor uniform declaration drift for ${name}`)
}
if (sourceText.split('out vec4 fragColor;').length !== 2) throw new Error('Gabor output declaration drift')

const proofAnchors = [
  ['dy-loop', 'for (int dy = -1; dy <= 1; dy++) {'],
  ['dx-loop', 'for (int dx = -1; dx <= 1; dx++) {'],
  ['impulse-loop', 'for (int k = 0; k < 8; k++) {'],
  ['impulse-break', 'if (k >= impulses) break;'],
  ['octave-loop', 'for (int i = 0; i < 5; i++) {'],
  ['octave-break', 'if (i >= oct) break;'],
  ['helper-call', 'value += amplitude * gaborNoise('],
]
for (const [name, anchor] of proofAnchors) {
  if (sourceText.split(anchor).length !== 2) throw new Error(`Gabor proof anchor drift for ${name}`)
}

const loopProof = {
  profile_scope: programKey,
  authorized_defines: {},
  loop_count: 4,
  unproved_loop_count: 0,
  call_graph_acyclic: true,
  lexical_loops: [
    { owner: 'gaborNoise', span: '49:5-79:6', induction: 'dy', trip_count: 3, lexical_depth: 1, effective_depth: 2, lexical_product: 72, entrypoint_charge: 425 },
    { owner: 'gaborNoise', span: '50:9-78:10', induction: 'dx', trip_count: 3, lexical_depth: 2, effective_depth: 3, lexical_product: 72, entrypoint_charge: 425 },
    { owner: 'gaborNoise', span: '54:13-77:14', induction: 'k', trip_count: 8, lexical_depth: 3, effective_depth: 4, lexical_product: 72, entrypoint_charge: 425 },
    { owner: 'main', span: '104:5-113:6', induction: 'i', trip_count: 5, lexical_depth: 1, effective_depth: 1, lexical_product: 5, entrypoint_charge: 425 },
  ],
  aggregate: {
    max_effective_depth: 4,
    max_lexical_product: 72,
    entrypoint_charge: 425,
  },
  charge_derivation: {
    helper_nested_charge: '3 + (3 * 3) + (3 * 3 * 8) = 84',
    main_entrypoint_charge: '5 + (5 * 84) = 425',
  },
  admission_decision: {
    global_effective_depth_limit_before_port: 3,
    required_program_scoped_effective_depth_limit: 4,
    historical_product_and_charge_cap: 4096,
    live_2026_08_14_trip_count_cap: 512,
    live_2026_08_14_lexical_product_cap: 262144,
    live_2026_08_14_entrypoint_charge_cap: 262656,
    max_lexical_product_below_4096: true,
    entrypoint_charge_below_4096: true,
    only_required_numeric_widening: 'effective depth 3 -> 4 for this authenticated program only',
  },
  live_preimplementation_probe_2026_08_14: {
    generate_typed_slice_sha256: '7426b00b882ea106d8eb0dea3c7eb8ca2fd0dc538ab95041174da5e4634de579',
    emit_typed_cpp_sha256: '085920debee8f1bfc0964303c90876cfc5f6ecf089c921daf3b0963fb8f815be',
    validator: 'synth/gabor:gabor:54:13: unsupported counted-for safety charge',
    isolated_patch: '3 -> 4 in proof.effective_depth and max_effective_depth comparisons, both authorities; no other predicate changed',
    depth4_only_relaxed_validator: 'PASS',
    depth4_only_relaxed_emitter: 'PASS',
    emitted_cpp_bytes: 12483,
    emitted_cpp_sha256: '8eaf3ab53ae3a162c5ea7b0ff0a125cb14bce0f79d3adbaebc586e1ff97c826f',
  },
}

function independentlyRecomputeLoopProof() {
  const run = spawnSync('python3', [proofProbePath, '--json'], {
    cwd: cppRoot,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024,
  })
  if (run.status !== 0) throw new Error(`independent Gabor loop-proof probe failed: ${run.stderr || run.stdout}`)
  const proof = JSON.parse(run.stdout)
  const expectedSummary = {
    loop_count: loopProof.loop_count,
    unproved_loop_count: loopProof.unproved_loop_count,
    max_effective_depth: loopProof.aggregate.max_effective_depth,
    max_lexical_product: loopProof.aggregate.max_lexical_product,
    entrypoint_charge: loopProof.aggregate.entrypoint_charge,
    call_graph_acyclic: loopProof.call_graph_acyclic,
  }
  for (const [name, expected] of Object.entries(expectedSummary)) {
    if (proof.summary[name] !== expected) throw new Error(`independent Gabor aggregate proof disagrees for ${name}`)
  }
  const actualCore = proof.loops.map((item) => [item.owner, item.span, item.trip_count, item.lexical_depth, item.effective_depth, item.lexical_product, item.entrypoint_charge])
  const expectedCore = loopProof.lexical_loops.map((item) => [item.owner, item.span, item.trip_count, item.lexical_depth, item.effective_depth, item.lexical_product, item.entrypoint_charge])
  if (JSON.stringify(actualCore) !== JSON.stringify(expectedCore)) throw new Error('independent Gabor loop tuples disagree')
  if (proof.derived.helper_nested_charge !== 84 || proof.derived.main_entrypoint_charge !== 425 || !proof.derived.only_depth_exceeds_three) {
    throw new Error('independent Gabor charge derivation disagrees')
  }
  return proof
}

const cases = [
  {
    name: 'default-landscape', width: 5, height: 4, time: 0, frame: 0, externalSeed: 999,
    uniforms: { scale: 75, orientation: 0, bandwidth: 75, isotropy: 0, density: 3, octaves: 1, speed: 1, seed: 1 },
    coverage: ['metadata defaults', 'single octave', 'anisotropic fixed orientation', 'time zero'],
  },
  {
    name: 'max-depth-density-octaves', width: 4, height: 3, time: 0.125, frame: 17, externalSeed: 7,
    uniforms: { scale: 1, orientation: 180, bandwidth: 1, isotropy: 100, density: 8, octaves: 5, speed: 5, seed: 100 },
    coverage: ['effective depth four', '72 helper iterations', 'five helper calls', 'all valid maxima'],
  },
  {
    name: 'minimum-work-speed-zero-time-a', width: 3, height: 5, time: 0, frame: 2, externalSeed: 1,
    uniforms: { scale: 100, orientation: -180, bandwidth: 100, isotropy: 0, density: 1, octaves: 1, speed: 0, seed: 37 },
    coverage: ['minimum density', 'minimum octaves', 'speed zero', 'portrait', 'valid parameter extrema'],
  },
  {
    name: 'minimum-work-speed-zero-time-b', width: 3, height: 5, time: 0.9875, frame: 4294967295, externalSeed: 4294967295,
    uniforms: { scale: 100, orientation: -180, bandwidth: 100, isotropy: 0, density: 1, octaves: 1, speed: 0, seed: 37 },
    sameAs: 'minimum-work-speed-zero-time-a',
    coverage: ['speed-zero time identity', 'unused frame identity', 'effect seed overrides external seed'],
  },
  {
    name: 'intermediate-anisotropic', width: 6, height: 2, time: 0.375, frame: 23, externalSeed: 888,
    uniforms: { scale: 33.25, orientation: 37.5, bandwidth: 42, isotropy: 40, density: 5, octaves: 3, speed: 2, seed: 17 },
    coverage: ['intermediate controls', 'partial early breaks', 'nonzero animation', 'wide canvas'],
  },
  {
    name: 'opposite-angle-random-orientation', width: 2, height: 6, time: 0.0625, frame: 5, externalSeed: 3,
    uniforms: { scale: 54, orientation: -73, bandwidth: 88, isotropy: 100, density: 6, octaves: 4, speed: 3, seed: 63 },
    coverage: ['isotropy maximum ignores base angle in blend', 'partial maximum loops', 'tall canvas'],
  },
  {
    name: 'tile-full-reference', width: 7, height: 5, time: 0.21875, frame: 31, externalSeed: 42,
    uniforms: { scale: 62, orientation: 91, bandwidth: 36, isotropy: 57, density: 7, octaves: 4, speed: 4, seed: 29 },
    coverage: ['full-resolution reference', 'non-square coordinate normalization'],
  },
  {
    name: 'tile-3x2-bottom-offset-2x1', width: 3, height: 2, time: 0.21875, frame: 31, externalSeed: 4242,
    tileOffset: [2, 1], fullResolution: [7, 5],
    uniforms: { scale: 62, orientation: 91, bandwidth: 36, isotropy: 57, density: 7, octaves: 4, speed: 4, seed: 29 },
    tileOf: 'tile-full-reference',
    coverage: ['tileOffset', 'fullResolution', 'bottom-left fragment origin', 'external seed override identity'],
  },
]

function compileMutant(name, from, to) {
  const source = canonicalFactory.toString()
  const pieces = source.split(from)
  if (pieces.length !== 2) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
  const mutatedText = `${pieces[0]}${to}${pieces[1]}`
  const factory = Function(`"use strict"; return (${mutatedText});`)()
  return { name, factory, factory_sha256: sha256(mutatedText), anchor_sha256: sha256(from), replacement_sha256: sha256(to) }
}

function sourceMutation(name, from, to, expected) {
  const pieces = sourceText.split(from)
  if (pieces.length !== 2) throw new Error(`${name}: GLSL mutation anchor matched ${pieces.length - 1} times`)
  const mutated = `${pieces[0]}${to}${pieces[1]}`
  const mutatedHash = sha256(mutated)
  if (mutatedHash === sha256(sourceBytes)) throw new Error(`${name}: GLSL mutation retained canonical hash`)
  return {
    name,
    kind: 'source-mutation',
    anchor_sha256: sha256(from),
    replacement_sha256: sha256(to),
    mutated_source_sha256: mutatedHash,
    expected,
  }
}

const renderMutants = [
  compileMutant('octave-loop-five-reduced-to-four', 'for (var i = 0; i < 5; i++) {', 'for (var i = 0; i < 4; i++) {'),
  compileMutant('impulse-loop-eight-reduced-to-seven', 'for (var k = 0; k < 8; k++) {', 'for (var k = 0; k < 7; k++) {'),
  compileMutant('density-break-removed', 'if (k >= impulses) {\n  \tbreak;\n  \t};', 'if (false) {\n  \tbreak;\n  \t};'),
  compileMutant('octave-break-removed', 'if (i >= oct) {\n  \tbreak;\n  \t};', 'if (false) {\n  \tbreak;\n  \t};'),
  compileMutant(
    'octave-coordinate-update-before-sample',
    'var fi = (i);\n  \tvalue += amplitude * (gaborNoise(pOct, octFreq, octSigma, baseAngle, iso, impulses, t + fi * 3.700000047683716, seed + fi * 17));\n  \ttotalAmp += amplitude;\n  \tamplitude *= 0.5;\n  \tpOct = new $runtime.PooledFloat32Array([pOct[0] * 2, pOct[1] * 2]);',
    'var fi = (i);\n  \tpOct = new $runtime.PooledFloat32Array([pOct[0] * 2, pOct[1] * 2]);\n  \tvalue += amplitude * (gaborNoise(pOct, octFreq, octSigma, baseAngle, iso, impulses, t + fi * 3.700000047683716, seed + fi * 17));\n  \ttotalAmp += amplitude;\n  \tamplitude *= 0.5;',
  ),
  compileMutant('inner-sum-premature-f32', 'sum += (weight * envelope) * cos(phase);', 'sum = Math.fround(sum + (weight * envelope) * cos(phase));'),
  compileMutant(
    'octave-sum-premature-f32',
    'value += amplitude * (gaborNoise(pOct, octFreq, octSigma, baseAngle, iso, impulses, t + fi * 3.700000047683716, seed + fi * 17));',
    'value = Math.fround(value + amplitude * (gaborNoise(pOct, octFreq, octSigma, baseAngle, iso, impulses, t + fi * 3.700000047683716, seed + fi * 17)));',
  ),
  compileMutant('octave-coordinate-doubling-removed', 'pOct = new $runtime.PooledFloat32Array([pOct[0] * 2, pOct[1] * 2]);', 'pOct = new $runtime.PooledFloat32Array([pOct[0], pOct[1]]);'),
  compileMutant('octave-amplitude-decay-removed', 'amplitude *= 0.5;', 'amplitude *= 1;'),
  compileMutant('normalization-removed', 'value /= totalAmp;', 'value = value;'),
  compileMutant('full-resolution-y-replaced-by-x', 'globalCoord[0] / fullResolution[1], globalCoord[1] / fullResolution[1]', 'globalCoord[0] / fullResolution[0], globalCoord[1] / fullResolution[0]'),
  compileMutant('tile-offset-removed', 'gl_FragCoord[0] + tileOffset[0], gl_FragCoord[1] + tileOffset[1]', 'gl_FragCoord[0], gl_FragCoord[1]'),
  compileMutant('time-binding-ignored', 'var t = (time * 6.2831854820251465) * spd;', 'var t = 0;'),
  compileMutant('effect-seed-ignored', 'seed + fi * 17', '1 + fi * 17'),
  compileMutant('orientation-ignored', 'var baseAngle = (orientation * 3.1415927410125732) / 180;', 'var baseAngle = 0;'),
  compileMutant('isotropy-ignored', 'var iso = isotropy / 100;', 'var iso = 0;'),
]

function typedUniforms(raw) {
  return {
    scale: f(raw.scale),
    orientation: f(raw.orientation),
    bandwidth: f(raw.bandwidth),
    isotropy: f(raw.isotropy),
    density: raw.density | 0,
    octaves: raw.octaves | 0,
    speed: raw.speed | 0,
    seed: f(raw.seed),
  }
}

function render(factory, definition) {
  const uniforms = typedUniforms(definition.uniforms)
  const tileOffset = definition.tileOffset ? new Float32Array(definition.tileOffset.map(f)) : undefined
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution.map(f)) : undefined
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: definition.frame,
    seed: definition.externalSeed,
    uniforms,
    tileOffset,
    fullResolution,
  })
  for (const [name, intended] of Object.entries(uniforms)) {
    if (name === 'density' || name === 'octaves' || name === 'speed') {
      if (bindings[name] !== intended) throw new Error(`${definition.name}: integer binding drift for ${name}`)
    } else if (f32Bits(bindings[name]) !== f32Bits(intended)) {
      throw new Error(`${definition.name}: scalar binding drift for ${name}`)
    }
  }
  // Effect-level seed is deliberately passed via uniforms and must override
  // the infrastructure seed option before the canonical factory captures it.
  if (f32Bits(bindings.seed) !== f32Bits(uniforms.seed)) throw new Error(`${definition.name}: effect seed did not override external seed`)
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.externalSeed })
  return { output, bindings }
}

function selectedProbes(surface) {
  const points = [
    ['top-left', 0, 0],
    ['top-right', surface.width - 1, 0],
    ['bottom-left', 0, surface.height - 1],
    ['bottom-right', surface.width - 1, surface.height - 1],
    ['center', Math.floor(surface.width / 2), Math.floor(surface.height / 2)],
  ]
  const seen = new Set()
  return points.filter(([, x, y]) => {
    const key = `${x},${y}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  }).map(([label, x, y]) => {
    const offset = (y * surface.width + x) * 4
    const values = Array.from(surface.data.slice(offset, offset + 4))
    return { label, at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
  })
}

function outputRecord(surface) {
  let nonfinite = 0
  let nonGrayPixels = 0
  let nonOpaquePixels = 0
  for (let i = 0; i < surface.data.length; i += 4) {
    const r = surface.data[i]
    const g = surface.data[i + 1]
    const b = surface.data[i + 2]
    const a = surface.data[i + 3]
    if (![r, g, b, a].every(Number.isFinite)) nonfinite += [r, g, b, a].filter((value) => !Number.isFinite(value)).length
    if (f32Bits(r) !== f32Bits(g) || f32Bits(r) !== f32Bits(b)) nonGrayPixels += 1
    if (f32Bits(a) !== f32Bits(1)) nonOpaquePixels += 1
  }
  if (nonfinite !== 0) throw new Error('nonfinite Gabor output for valid controls')
  if (nonGrayPixels !== 0) throw new Error('Gabor output is not exact grayscale')
  if (nonOpaquePixels !== 0) throw new Error('Gabor output is not exact opaque alpha')
  return {
    f32_sha256: sha256(bytes(surface.data)),
    rgba8_sha256: sha256(bytes(surface.toRgba8())),
    finite_lanes: surface.data.length,
    nonfinite_lanes: nonfinite,
    exact_grayscale_pixels: surface.width * surface.height,
    exact_opaque_pixels: surface.width * surface.height,
    probes: selectedProbes(surface),
  }
}

function cropBottomLeftTile(full, tileOffset, tileWidth, tileHeight) {
  const xStart = tileOffset[0]
  const topDownYStart = full.height - tileOffset[1] - tileHeight
  const data = new Float32Array(tileWidth * tileHeight * 4)
  for (let y = 0; y < tileHeight; y += 1) {
    for (let x = 0; x < tileWidth; x += 1) {
      const sourceOffset = ((topDownYStart + y) * full.width + xStart + x) * 4
      const targetOffset = (y * tileWidth + x) * 4
      data.set(full.data.subarray(sourceOffset, sourceOffset + 4), targetOffset)
    }
  }
  return new Surface(tileWidth, tileHeight, data)
}

function buildPrngNormalizationEvidence() {
  const glslUintMax = 0xffffffff
  const canonicalDenominator = f(glslUintMax)
  if (canonicalDenominator !== 4294967296 || f32Bits(canonicalDenominator) !== '0x4f800000') {
    throw new Error('GLSL uint-max Float32 materialization drift')
  }
  const words = [0, 1, 0x7fffffff, 0x80000000, 0xffffff00, 0xffffffff]
  const records = words.map((word) => {
    const numerator = f(word >>> 0)
    const canonical = f(numerator / canonicalDenominator)
    const integerDenominatorControl = f(numerator / glslUintMax)
    return {
      word_u32: word >>> 0,
      word_hex: u32Hex(word),
      numerator_f32: numerator,
      numerator_f32_bits_le: f32Bits(numerator),
      canonical_normalized_f32: canonical,
      canonical_normalized_f32_bits_le: f32Bits(canonical),
      integer_denominator_control_f32: integerDenominatorControl,
      integer_denominator_control_f32_bits_le: f32Bits(integerDenominatorControl),
      final_f32_difference_observable: f32Bits(canonical) !== f32Bits(integerDenominatorControl),
    }
  })
  if (records.some((record) => record.final_f32_difference_observable)) {
    throw new Error('PRNG denominator structural-only classification drift')
  }
  return {
    glsl_source_literal: '0xffffffffu',
    canonical_float32_denominator: canonicalDenominator,
    canonical_float32_denominator_bits_le: f32Bits(canonicalDenominator),
    integer_u32_max_control: glslUintMax,
    final_f32_distinction_observable_in_frozen_words: false,
    records,
  }
}

function buildData() {
  const independentLoopProof = independentlyRecomputeLoopProof()
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

    return {
      name: definition.name,
      dimensions: { width: definition.width, height: definition.height },
      controls: {
        ...typedUniforms(definition.uniforms),
        time: f(definition.time),
        frame: definition.frame,
        external_seed_input: definition.externalSeed,
        effective_seed_binding: canonicalFirst.bindings.seed,
        tile_offset: Array.from(canonicalFirst.bindings.tileOffset),
        full_resolution: Array.from(canonicalFirst.bindings.fullResolution),
      },
      coverage: definition.coverage,
      output: outputRecord(canonicalFirst.output),
      repeat_identity: repeat,
      public_catalog_vs_direct_canonical: publicComparison,
      mutation_comparisons: mutationComparisons,
    }
  })

  for (const definition of cases) {
    const record = caseResults.find((item) => item.name === definition.name)
    if (definition.sameAs) {
      const equality = compareSurfaces(renderedByName.get(definition.sameAs), renderedByName.get(definition.name))
      if (!equality.float32.exact_f32_bits || !equality.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: declared identity with ${definition.sameAs} failed`)
      record.declared_identity = { reference_case: definition.sameAs, comparison: equality }
    }
    if (definition.tileOf) {
      const cropped = cropBottomLeftTile(renderedByName.get(definition.tileOf), definition.tileOffset, definition.width, definition.height)
      const equality = compareSurfaces(cropped, renderedByName.get(definition.name))
      if (!equality.float32.exact_f32_bits || !equality.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: tile/full continuity failed`)
      record.tile_continuity = {
        full_reference_case: definition.tileOf,
        full_top_down_crop_origin: [definition.tileOffset[0], cases.find((item) => item.name === definition.tileOf).height - definition.tileOffset[1] - definition.height],
        comparison: equality,
      }
    }
  }

  const requiredRenderMutations = {
    'octave-loop-five-reduced-to-four': ['max-depth-density-octaves'],
    'impulse-loop-eight-reduced-to-seven': ['max-depth-density-octaves'],
    'density-break-removed': ['default-landscape', 'minimum-work-speed-zero-time-a'],
    'octave-break-removed': ['default-landscape', 'intermediate-anisotropic'],
    'octave-coordinate-update-before-sample': ['max-depth-density-octaves'],
    'inner-sum-premature-f32': ['max-depth-density-octaves'],
    'octave-sum-premature-f32': ['max-depth-density-octaves'],
    'octave-coordinate-doubling-removed': ['max-depth-density-octaves'],
    'octave-amplitude-decay-removed': ['max-depth-density-octaves'],
    'normalization-removed': ['max-depth-density-octaves', 'intermediate-anisotropic'],
    'full-resolution-y-replaced-by-x': ['default-landscape', 'tile-full-reference'],
    'tile-offset-removed': ['tile-3x2-bottom-offset-2x1'],
    'time-binding-ignored': ['max-depth-density-octaves', 'intermediate-anisotropic'],
    'effect-seed-ignored': ['max-depth-density-octaves', 'intermediate-anisotropic'],
    'orientation-ignored': ['intermediate-anisotropic'],
    'isotropy-ignored': ['max-depth-density-octaves', 'intermediate-anisotropic'],
  }
  const renderMutationSummary = renderMutants.map((mutant) => {
    const witnesses = caseResults.filter((record) => !record.mutation_comparisons[mutant.name].float32.exact_f32_bits).map((record) => record.name)
    for (const required of requiredRenderMutations[mutant.name]) {
      if (!witnesses.includes(required)) throw new Error(`${mutant.name}: required witness ${required} did not diverge; observed ${witnesses.join(', ') || 'none'}`)
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

  const sourceContractNegatives = [
    { name: 'wrong-program-key', kind: 'profile-negative', mutation: 'apply the profile to synth/julia:julia', expected: 'reject before proof admission' },
    { name: 'nonempty-define-map', kind: 'profile-negative', mutation: 'add any preprocessor define', expected: 'reject; canonical define map is exactly empty' },
    sourceMutation('source-comment-byte-drift', 'Gabor noise — sparse convolution', 'Gabor noise - sparse convolution', 'reject by raw source SHA-256 before proof admission'),
    sourceMutation('inner-bound-nine', 'for (int k = 0; k < 8; k++) {', 'for (int k = 0; k < 9; k++) {', 'reject authenticated source/loop tuple; lexical product 81 and derived charge 470 are both below 4096 but are not authorized'),
    sourceMutation('outer-bound-six', 'for (int i = 0; i < 5; i++) {', 'for (int i = 0; i < 6; i++) {', 'reject authenticated source/loop tuple; derived charge 510 remains below 4096 but is not authorized'),
    sourceMutation(
      'neighbor-order-swap',
      'for (int dy = -1; dy <= 1; dy++) {\n        for (int dx = -1; dx <= 1; dx++) {',
      'for (int dx = -1; dx <= 1; dx++) {\n        for (int dy = -1; dy <= 1; dy++) {',
      'reject authenticated source even though the aggregate proof numbers remain unchanged',
    ),
    sourceMutation('remove-density-break', 'if (k >= impulses) break;', 'if (false) break;', 'reject authenticated source; valid low-density pixel witnesses diverge'),
    sourceMutation('remove-octave-break', 'if (i >= oct) break;', 'if (false) break;', 'reject authenticated source; valid low-octave pixel witnesses diverge'),
    { name: 'global-depth-four', kind: 'profile-negative', mutation: 'raise the validator depth cap for every program', expected: 'reject design; widening must be keyed to this exact program/source/proof' },
  ]

  return {
    schema: 'noisemaker-for-cpp.gabor.pixel-parity-and-loop-depth-oracle.v1',
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
      proof_probe: {
        path: 'docs/port-engineering/loopproof/gabor-parity/gabor_loop_proof_probe.py',
        sha256: sha256(fs.readFileSync(proofProbePath)),
      },
      cpu_files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, hash]]) => [name, { path: relativePath, sha256: hash }])),
    },
    interface_contract: {
      effect: { id: effect.id, namespace: effect.namespace, func: effect.func, kind: effect.kind },
      pass: effect.passes[0],
      params: expectedParams,
      uniforms: expectedUniformDeclarations.map(([name, type]) => ({ name, type })),
      outputs: [{ name: 'fragColor', type: 'vec4' }],
      samplers: [],
      authorized_defines: {},
      public_factory_is_direct_canonical_identity: true,
      adapter_override_absent: true,
    },
    counted_loop_proof: loopProof,
    independent_frontend_loop_proof: independentLoopProof,
    materialization_contract: {
      prng_u32_divisor: 'GLSL float(0xffffffffu) materializes as Float32 4294967296 in canonical JS, not the integer 4294967295; direct evidence freezes the intermediate because final Float32 PRNG lanes erase this one-unit denominator distinction',
      scalar_accumulators: 'sum, value, amplitude, and totalAmp remain JavaScript Number until an explicit Float32Array write; premature Math.fround is observable',
      vectors: 'vec2/vec3/uvec3 constructors and vector arithmetic materialize through typed arrays/runtime helpers',
      constants: 'PI, TAU, 0.15, 0.05, 0.35, and 3.7 are the Float32-materialized literals embedded in canonicalFactory249',
      output: 'Float32 Surface stores after logistic normalization; exact grayscale RGB and alpha 1',
      coordinates: 'top-down Surface traversal supplies bottom-left gl_FragCoord; tileOffset is added before division by fullResolution.y',
      effect_seed: 'uniforms.seed overrides the infrastructure seed option and is consumed by the shader',
      frame: 'unreachable: the canonical factory does not capture or read frame',
    },
    fixture: {
      input: 'none; Gabor is a generator',
      comparer: 'exact Float32-bit and RGBA8-byte custom comparer; hashes remain authoritative',
      repeated_render_count: 2,
      valid_parameter_domain_only: true,
      tile_continuity: '3x2 bottom-left tile at offset (2,1) must equal top-down crop origin (2,2) from the 7x5 full render',
    },
    direct_prng_normalization: buildPrngNormalizationEvidence(),
    cases: caseResults,
    render_mutation_summary: renderMutationSummary,
    source_contract_negatives: sourceContractNegatives,
    unreachable_traps: [
      'Replacing the Float32 denominator 4294967296 with the Number 4294967295 produces the same final Float32 normalized PRNG lanes for the frozen uint corpus; the exact intermediate literal/materialization is structural, not a manufactured pixel witness.',
      'Frame and the infrastructure seed option are not captured by canonicalFactory249. The paired valid render proves identity while the effect-level seed uniform remains pixel-observable.',
    ],
    implementation_acceptance: [
      'Authenticate the exact program key, source SHA-256, empty define map, four loop tuples, and acyclic call graph before allowing effective depth four.',
      'Keep the ordinary global effective-depth limit at three; authorize four only for this exact Gabor profile in both generator and emitter validators.',
      'Do not widen trip-count, lexical-depth, lexical-product, or entrypoint-charge limits for Gabor.',
      'Require exact Float32 bytes and exact RGBA8 bytes for every case, exact repeat identity, canonical/public equality, and exact tile/full continuity.',
      'Reject every source/profile negative and require every listed pixel mutation to have its named exact-bit witness.',
    ],
  }
}

function makeReport(data) {
  const lines = [
    '# Gabor loop-depth and pixel-parity oracle', '',
    'Frozen JavaScript ground truth for `synth/gabor:gabor`. The package authenticates the canonical source/factory/interface, freezes the sole counted-loop admission need, and records exact Float32 and RGBA8 render contracts. The custom comparer provides first-pixel diagnostics without weakening byte equality.', '',
    '## Admission result', '',
    '- The live pre-port validator rejects at `54:13` with `unsupported counted-for safety charge`.',
    '- All four loops are proved and the counted-loop call graph is acyclic.',
    '- The helper nest has trip counts 3 x 3 x 8, maximum lexical product 72, and helper charge 84. The five-trip main loop calls that helper, yielding entrypoint charge `5 + 5 x 84 = 425`.',
    '- Maximum effective depth is four: main loop depth one plus the helper\'s lexical depth three. Maximum lexical depth remains three.',
    '- Both 72 and 425 are below the requested 4096 reference cap. The live 2026-08-14 generic constants have since expanded to 262,144 (product) and 262,656 (charge), so the hard-coded depth-three predicate is still the only failing numeric gate.',
    '- An isolated re-probe that changed only the effective-depth predicate from three to four passed the real validator and the independent emitter gate; emitted output was 12,483 bytes with SHA-256 `8eaf3ab53ae3a162c5ea7b0ff0a125cb14bce0f79d3adbaebc586e1ff97c826f`.',
    '- Required production design: a source-authenticated, program-scoped effective-depth-four profile in both authorities. No global cap and no other numeric limit should move.', '',
    '## Frozen identities', '',
    `- Upstream snapshot revision: \`${data.upstream_revision}\``,
    `- Corpus revision: \`${data.corpus_revision}\``,
    `- GLSL source: ${data.provenance.source_raw_bytes} bytes, SHA-256 \`${data.provenance.source_sha256}\``,
    `- Canonical factory: \`${data.provenance.canonical_factory_name}\`, ${data.provenance.canonical_factory_to_string_bytes} bytes, SHA-256 \`${data.provenance.canonical_factory_to_string_sha256}\``,
    '- Public catalog identity is exactly the canonical factory; no adapter override exists.',
    '- The canonical define map is exactly empty. The pass has no samplers and writes only `fragColor`.', '',
    '## Render cases', '',
    '| Case | Size | Density | Octaves | Speed | Time | Seed | Tile offset | Float32 SHA-256 | RGBA8 SHA-256 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |',
  ]
  for (const record of data.cases) {
    const c = record.controls
    lines.push(`| ${record.name} | ${record.dimensions.width}x${record.dimensions.height} | ${c.density} | ${c.octaves} | ${c.speed} | ${c.time} | ${c.seed} | ${c.tile_offset.join(',')} | \`${record.output.f32_sha256}\` | \`${record.output.rgba8_sha256}\` |`)
  }
  lines.push('', 'Every valid-domain case requires finite exact-grayscale output with exact alpha one, exact repeated-render identity, and direct-canonical/public-catalog equality. The paired speed-zero cases prove time identity and unused frame/external-seed identity. The tile case must exactly equal the corresponding bottom-left-origin crop from the full render.', '')
  lines.push('## Materialization traps', '')
  lines.push('- Canonical JS converts GLSL `float(0xffffffffu)` to Float32 4294967296. Direct word fixtures freeze that intermediate. Using Number 4294967295 happens to round every frozen normalized result to the same Float32 lane, so this is explicitly structural rather than assigned a false pixel witness.')
  lines.push('- Scalar Gabor and octave accumulators stay JavaScript Number values until vector/Surface materialization. Premature Float32 narrowing is rejected separately at each accumulation layer.')
  lines.push('- Octave state updates are order-sensitive. Advancing `pOct` before rather than after the current sample is rejected by exact pixels; swapping neighbor traversal is separately rejected by source authentication.')
  lines.push('- `fullResolution.y`, bottom-left `gl_FragCoord`, and `tileOffset` jointly define coordinates. The exact tile/full continuity check freezes all three.')
  lines.push('- The effect-level `seed` uniform overrides the infrastructure seed option. `frame` is not read by this factory; the identity pair records that instead of inventing a false witness.', '')
  lines.push('## Mutation discrimination', '')
  lines.push('| Mutation | Required exact-bit witnesses | All divergent cases |')
  lines.push('| --- | --- | --- |')
  for (const mutation of data.render_mutation_summary) {
    lines.push(`| ${mutation.name} | ${mutation.required_witnesses.join(', ')} | ${mutation.all_divergent_cases.join(', ')} |`)
  }
  lines.push('', 'The nine source/profile negatives separately reject wrong key, define or byte drift, changed bounds/breaks/order, and a global depth-cap widening. Source authentication is required even when a mutation remains numerically below a generic budget.', '')
  lines.push('## Regeneration', '', 'From the `noisemaker-for-cpp` repository root:', '', '```sh', 'node docs/port-engineering/loopproof/gabor-parity/gabor_parity_oracle_generator.mjs', 'node docs/port-engineering/loopproof/gabor-parity/gabor_parity_oracle_generator.mjs --check', '```', '')
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
const proofProbeHash = sha256(fs.readFileSync(proofProbePath))
const jsonSidecar = sidecar(sha256(json), outputPath)
const reportSidecar = sidecar(sha256(report), reportPath)
const generatorSidecar = sidecar(generatorHash, generatorPath)
const proofProbeSidecar = sidecar(proofProbeHash, proofProbePath)

if (process.argv.includes('--check')) {
  checkExact(outputPath, json, 'Gabor parity JSON')
  checkExact(reportPath, report, 'Gabor parity report')
  checkExact(`${outputPath}.sha256`, jsonSidecar, 'Gabor parity JSON sidecar')
  checkExact(`${reportPath}.sha256`, reportSidecar, 'Gabor parity report sidecar')
  checkExact(`${generatorPath}.sha256`, generatorSidecar, 'Gabor parity generator sidecar')
  checkExact(`${proofProbePath}.sha256`, proofProbeSidecar, 'Gabor loop-proof probe sidecar')
  console.log(`Gabor parity oracle ok (${data.cases.length} render cases, ${data.render_mutation_summary.length} pixel mutations, ${data.source_contract_negatives.length} source/profile negatives)`)
} else {
  fs.writeFileSync(outputPath, json)
  fs.writeFileSync(reportPath, report)
  fs.writeFileSync(`${outputPath}.sha256`, jsonSidecar)
  fs.writeFileSync(`${reportPath}.sha256`, reportSidecar)
  fs.writeFileSync(`${generatorPath}.sha256`, generatorSidecar)
  fs.writeFileSync(`${proofProbePath}.sha256`, proofProbeSidecar)
  console.log(outputPath)
  console.log(reportPath)
}
