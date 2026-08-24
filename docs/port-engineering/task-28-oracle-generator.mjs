import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-28-oracles.json')
const reportPath = path.join(here, 'task-28-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const catalogPath = path.join(cpuRoot, 'src/effects/catalog.js')
const adapterIndexPath = path.join(cpuRoot, 'src/effects/adapters/index.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const catalogSha256 = 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'
const adapterIndexSha256 = '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'
const key = 'filter/rotate:rot'
const sourceRelative = 'sources/filter/rotate/rot.glsl'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, sourceRelative)
const factoryName = 'canonicalFactory127'
const factorySha256 = '4dd2ffadbcf25ec3f88c090b014da6cd3ee7faa3ddea970f21714c873dfcf903'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function occurrences(text, needle) { return text.split(needle).length - 1 }
function replaceExact(text, from, to) {
  if (occurrences(text, from) !== 1) throw new Error(`factory shape drift for ${from}`)
  return text.replace(from, to)
}
function evaluated(text) { return (0, eval)(`(${text})`) }

if (sha256(fs.readFileSync(canonicalPath)) !== canonicalSha256) throw new Error('pinned canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== catalogSha256) throw new Error('pinned public catalog drift')
if (sha256(fs.readFileSync(adapterIndexPath)) !== adapterIndexSha256) throw new Error('pinned adapter index drift')
const source = fs.readFileSync(sourcePath)
if (source.byteLength !== 1197 || sha256(source) !== 'c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f') throw new Error('pinned source drift')
const canonical = canonicalKernelFactories[key]
const publicFactory = kernelFactories.get(key)
if (canonical?.name !== factoryName || sha256(Buffer.from(canonical.toString())) !== factorySha256) throw new Error('canonical factory drift')
if (publicFactory !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')

const factoryText = canonical.toString()
const constructorLine = '\treturn new $runtime.PooledFloat32Array([c, -s, s, c]);'
const multiplyLine = '\tuv.map(function (x, i, v) { var sum = 0; for (var j = 0; j < 2; j++) {sum += this[j*2+i] * v[j]} return sum; }, rotate2D((-angle * TAU) / 360)).reduce((res,el,i)=>(res[i] = el, res), uv);'
if (occurrences(factoryText, constructorLine) !== 1 || occurrences(factoryText, multiplyLine) !== 1) throw new Error('Rotate factory shape drift')
const renderMutations = [
  { id: 'transpose-constructor', hazard: 'constructor-lane-order', expectation: 'diverge', factory: evaluated(replaceExact(factoryText, constructorLine, '\treturn new $runtime.PooledFloat32Array([c, s, -s, c]);')) },
  { id: 'quarter-turn-constructor', hazard: 'constructor-child-identity', expectation: 'diverge', factory: evaluated(replaceExact(factoryText, constructorLine, '\treturn new $runtime.PooledFloat32Array([s, -c, c, s]);')) },
  { id: 'diagonal-constructor', hazard: 'constructor-arity-semantics', expectation: 'diverge', factory: evaluated(replaceExact(factoryText, constructorLine, '\treturn new $runtime.PooledFloat32Array([c, 0, 0, c]);')) },
  { id: 'row-major-multiply', hazard: 'matrix-layout', expectation: 'diverge', factory: evaluated(replaceExact(factoryText, multiplyLine, multiplyLine.replace('this[j*2+i]', 'this[i*2+j]'))) },
  { id: 'helper-local-return', hazard: 'return-expression-shape', expectation: 'identity-but-structurally-reject', factory: evaluated(replaceExact(factoryText, constructorLine, '\tvar returnedMatrix = new $runtime.PooledFloat32Array([c, -s, s, c]);\n\treturn returnedMatrix;')) },
]

function quadrantInput(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  const bases = [
    [0.82, 0.11, 0.19, 0.31], [0.13, 0.77, 0.23, 0.47],
    [0.17, 0.29, 0.88, 0.63], [0.91, 0.73, 0.09, 0.79],
  ]
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const quadrant = (y >= Math.floor(height / 2) ? 2 : 0) + (x >= Math.floor(width / 2) ? 1 : 0)
    const base = bases[quadrant]
    const i = (y * width + x) * 4
    data[i] = f(base[0] + (((x * 7 + y * 3 + phase) % 9) - 4) / 200)
    data[i + 1] = f(base[1] + (((x * 2 + y * 11 + phase * 2) % 11) - 5) / 220)
    data[i + 2] = f(base[2] + (((x * 13 + y * 5 + phase * 3) % 13) - 6) / 240)
    data[i + 3] = f(base[3] + (((x * 3 + y * 7 + phase) % 7) - 3) / 180)
  }
  return new Surface(width, height, data)
}

const cases = [
  { name: 'mirror-zero-stationary', width: 11, height: 7, phase: 1, time: f(0), rotation: f(0), wrap: 0, speed: 0, coverage: ['mirror', 'zero angle', 'stationary', 'non-square quadrant input'] },
  { name: 'repeat-quarter-turn-stationary', width: 9, height: 6, phase: 2, time: f(0.375), rotation: f(90), wrap: 1, speed: 0, coverage: ['repeat', '90 degrees', 'nonzero inert time', 'non-square quadrant input'] },
  { name: 'clamp-negative-oblique-stationary', width: 12, height: 7, phase: 3, time: f(0), rotation: f(-43.25), wrap: 2, speed: 0, coverage: ['clamp', 'negative oblique angle', 'stationary', 'non-square quadrant input'] },
  { name: 'mirror-positive-animation', width: 10, height: 6, phase: 4, time: f(0.1875), rotation: f(17.5), wrap: 0, speed: 2, coverage: ['mirror', 'positive speed', 'animated angle', 'non-square quadrant input'] },
  { name: 'repeat-negative-animation', width: 13, height: 8, phase: 5, time: f(0.3125), rotation: f(-122.75), wrap: 1, speed: -3, coverage: ['repeat', 'negative speed', 'animated angle', 'non-square quadrant input'] },
  { name: 'clamp-large-angle-animation', width: 8, height: 5, phase: 6, time: f(0.53125), rotation: f(179.5), wrap: 2, speed: 4, coverage: ['clamp', 'large accumulated angle', 'animated angle', 'non-square quadrant input'] },
]

function render(factory, definition) {
  const input = quadrantInput(definition.width, definition.height, definition.phase)
  const original = new Float32Array(input.data)
  const kernel = bindCanonicalKernel(factory, {
    width: definition.width, height: definition.height, time: definition.time, frame: 41,
    deltaTime: f(1 / 60), seed: f(29),
    uniforms: { rotation: definition.rotation, wrap: definition.wrap, speed: definition.speed },
    textures: { inputTex: input },
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: f(29) })
  if (!sameBytes(input.data, original)) throw new Error(`${definition.name}: input mutated`)
  return { input, output }
}
function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}
function probes(surface) {
  return [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]].map(([x, y]) => probe(surface, x, y))
}
function outputRecord(output) {
  const rgba = output.toRgba8()
  let nonfinite = 0
  for (const value of output.data) if (!Number.isFinite(value)) nonfinite += 1
  if (nonfinite) throw new Error('nonfinite output')
  return { f32_sha256: sha256(bytes(output.data)), rgba8_sha256: sha256(bytes(rgba)), probes: probes(output), finite_lanes: output.data.length, nonfinite_lanes: nonfinite }
}
function diff(reference, candidate) {
  const rb = bytes(reference.data), cb = bytes(candidate.data), rr = reference.toRgba8(), cr = candidate.toRgba8()
  let differentF32Lanes = 0, differentRgba8 = 0, maxAbs = 0
  for (let i = 0; i < reference.data.length; i += 1) if (f32Bits(reference.data[i]) !== f32Bits(candidate.data[i])) { differentF32Lanes += 1; maxAbs = Math.max(maxAbs, Math.abs(reference.data[i] - candidate.data[i])) }
  for (let i = 0; i < rr.length; i += 1) if (rr[i] !== cr[i]) differentRgba8 += 1
  return { same_f32_bytes: Buffer.compare(rb, cb) === 0, same_rgba8_bytes: differentRgba8 === 0, different_f32_lanes: differentF32Lanes, different_rgba8_bytes: differentRgba8, max_abs_f32_delta: maxAbs, candidate_f32_sha256: sha256(cb), candidate_rgba8_sha256: sha256(bytes(cr)) }
}

const directModes = [
  { id: 0, name: 'exact-direct-return-column-major', association: 'direct-return' },
  { id: 1, name: 'transposed-constructor', association: 'direct-return' },
  { id: 2, name: 'row-major-multiply', association: 'direct-return' },
  { id: 3, name: 'diagonal-constructor', association: 'direct-return' },
  { id: 4, name: 'wrong-sine-sign', association: 'direct-return' },
  { id: 5, name: 'helper-local-return', association: 'local-return' },
]
const directInputs = [
  [0, 1.25, -0.75], [Math.PI / 6, 1, 2], [-Math.PI / 2, -2.5, 0.5],
  [Math.PI, 0.125, -3], [0.7, 7.25, -1.5], [-2.3, -0.375, 4.5],
]
function directRecord([angle0, x0, y0]) {
  const angle = f(angle0), x = f(x0), y = f(y0), c = f(Math.cos(angle)), s = f(Math.sin(angle))
  const evaluate = (mode) => {
    let lanes
    if (mode.name === 'transposed-constructor') lanes = [c, s, f(-s), c]
    else if (mode.name === 'diagonal-constructor') lanes = [c, f(0), f(0), c]
    else if (mode.name === 'wrong-sine-sign') lanes = [c, s, s, c]
    else lanes = [c, f(-s), s, c]
    const rowMajor = mode.name === 'row-major-multiply'
    const out0 = f((rowMajor ? lanes[0] * x + lanes[1] * y : lanes[0] * x + lanes[2] * y))
    const out1 = f((rowMajor ? lanes[2] * x + lanes[3] * y : lanes[1] * x + lanes[3] * y))
    return { mode_id: mode.id, mode_name: mode.name, return_shape: mode.association, matrix_lanes_column_major: lanes, matrix_lane_f32_bits_le: lanes.map(f32Bits), product: [out0, out1], product_f32_bits_le: [f32Bits(out0), f32Bits(out1)] }
  }
  return { input: { angle_radians: angle, angle_f32_bits_le: f32Bits(angle), vector: [x, y], vector_f32_bits_le: [f32Bits(x), f32Bits(y)] }, cos_f32_bits_le: f32Bits(c), sin_f32_bits_le: f32Bits(s), modes: directModes.map(evaluate) }
}

function buildData() {
  const reference = new Map()
  const caseResults = cases.map(definition => {
    const first = render(canonical, definition), second = render(canonical, definition)
    if (!sameBytes(first.input.data, second.input.data) || !sameBytes(first.output.data, second.output.data)) throw new Error(`${definition.name}: repeat mismatch`)
    reference.set(definition.name, first.output)
    return {
      name: definition.name, dimensions: { width: definition.width, height: definition.height }, phase: definition.phase,
      time: definition.time, uniforms: { rotation: definition.rotation, wrap: definition.wrap, speed: definition.speed }, coverage: definition.coverage,
      input: { f32_sha256: sha256(bytes(first.input.data)), probes: probes(first.input) }, output: outputRecord(first.output), repeat_identity: true, input_immutable: true,
    }
  })
  const mutationResults = renderMutations.map(mutation => {
    const results = cases.map(definition => ({ case: definition.name, ...diff(reference.get(definition.name), render(mutation.factory, definition).output) }))
    const diverges = results.some(row => !row.same_f32_bytes)
    if ((mutation.expectation === 'diverge') !== diverges) throw new Error(`${mutation.id}: mutation expectation failed`)
    return { id: mutation.id, hazard: mutation.hazard, expectation: mutation.expectation, case_results: results }
  })
  const directCases = directInputs.map(directRecord)
  for (const row of directCases) {
    const exact = row.modes[0]
    const local = row.modes[5]
    if (exact.product_f32_bits_le.join() !== local.product_f32_bits_le.join() || exact.matrix_lane_f32_bits_le.join() !== local.matrix_lane_f32_bits_le.join()) throw new Error('local-return value control drift')
  }
  for (const name of ['transposed-constructor', 'row-major-multiply', 'diagonal-constructor', 'wrong-sine-sign']) {
    if (!directCases.some(row => row.modes.find(x => x.mode_name === name).product_f32_bits_le.join() !== row.modes[0].product_f32_bits_le.join())) throw new Error(`${name}: direct table lacks divergence`)
  }
  return {
    schema: 'noisemaker-for-cpp.task28.rotate-mat2-return.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, public_api: 'kernelFactories.get(key)', canonical_identity: true, adapter_entry_absent: true, canonical_kernels_sha256: canonicalSha256, public_catalog_sha256: catalogSha256, adapter_index_sha256: adapterIndexSha256 },
    program: {
      key, source: sourceRelative, raw_source_bytes: 1197, raw_source_sha256: 'c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f', normalized_source_bytes: 964, normalized_source_sha256: 'e0e2b723289b08cbfcd6f1fc0a8481869e674de3cfedc0ec5df6d96f64748bb5', defines: {}, profile: 'rotate-mat2-return-v1', canonical_factory_name: factoryName, canonical_factory_to_string_sha256: factorySha256,
      binding_signature: ['inputTex:sampler2D@1/S1', 'rotation:float@2', 'wrap:int@3', 'speed:int@4', 'time:float@5'], output: 'fragColor:vec4@6',
      matrix_contract: { helper: 'mat2 rotate2D(in float angle)', constructor: 'mat2(c, -s, s, c)', layout: 'two column vectors [c,-s] and [s,c]', return: 'automatic glsl::Mat2 by value', use: 'one direct mat2 * vec2 call' },
    },
    fixture: { input: 'top-down non-square quadrant-marked deterministic F32 RGBA field', fragment_origin: 'bottom-left runPass coordinates', verification: 'fresh double render, immutable input, finite full output, F32/RGBA8 hashes and five probes' },
    cases: caseResults, public_factory_mutations: mutationResults,
    direct_matrix_modes: directModes, direct_matrix_cases: directCases,
    direct_harness_contract: { explicit_enum_switch_arms: 6, default_throws: true, records_both_mode_id_and_mode_name: true, exact_and_helper_local_are_value_identical_but_have_distinct_return_shape_witnesses: true },
    negative_closure: { any_other_key_or_define_map: 'reject', any_other_matrix_return_or_parameter: 'reject', helper_overload_or_recursion: 'reject', changed_constructor_child_or_order_or_arity: 'reject', returned_local_or_state_escape: 'reject', second_call_or_non_direct_use: 'reject', row_major_or_vector_matrix_or_matrix_matrix: 'reject', mat3_or_mat4: 'reject', generic_matrix_return_capability: 'forbidden' },
  }
}

function buildReport(data) {
  const lines = [
    '# Task 28 Rotate mat2 return public-canonical oracle report', '',
    `Public render cases: **${data.cases.length}**  `, `Public factory mutations: **${data.public_factory_mutations.length}**  `, `Direct matrix inputs/modes: **${data.direct_matrix_cases.length} / ${data.direct_matrix_modes.length}**`, '',
    'The public dispatch is the exact canonical factory and has no adapter. Every case uses a non-square quadrant-marked input, repeats byte-identically, preserves input bytes, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.', '',
    '## Public render cases', '', '| Case | Size | Wrap / speed | Output F32 SHA-256 | Output RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- |',
  ]
  for (const c of data.cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.uniforms.wrap} / ${c.uniforms.speed} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Public mutation sensitivity', '', '| Mutation | Hazard | Divergent cases |', '| --- | --- | ---: |')
  for (const m of data.public_factory_mutations) lines.push(`| ${m.id} | ${m.hazard} | ${m.case_results.filter(x => !x.same_f32_bytes).length}/${m.case_results.length} |`)
  lines.push('', 'The helper-local-return control is value-identical but structurally distinct. Every value/layout mutation diverges in at least one case.', '', '## Direct matrix-value contract', '', '| Angle/vector | Exact lanes | Exact product |', '| --- | --- | --- |')
  for (const c of data.direct_matrix_cases) lines.push(`| ${c.input.angle_radians}; ${c.input.vector.join(', ')} | ${c.modes[0].matrix_lane_f32_bits_le.join(', ')} | ${c.modes[0].product_f32_bits_le.join(', ')} |`)
  lines.push('', 'The native suite must execute all six named switch modes, authenticate both numeric mode IDs and names, record distinct return-shape witnesses, reject an invalid enum, and compare every matrix lane and product bit pattern. Python must transcribe and tamper-check every executable case and mode-table field.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') { fs.writeFileSync(jsonPath, json); fs.writeFileSync(reportPath, report); process.stdout.write('wrote task-28-oracles.json and task-28-oracle-report.md\n') }
else if (process.argv.length === 3 && process.argv[2] === '--check') { if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error('task-28-oracles.json drift'); if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('task-28-oracle-report.md drift'); process.stdout.write('ok task-28-oracles.json and task-28-oracle-report.md\n') }
else throw new Error('usage: node task-28-oracle-generator.mjs [--write|--check]')
