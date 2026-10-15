import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-26-oracles.json')
const reportPath = path.join(here, 'task-26-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const catalogPath = path.join(cpuRoot, 'src/effects/catalog.js')
const adapterIndexPath = path.join(cpuRoot, 'src/effects/adapters/index.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const catalogSha256 = 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'
const adapterIndexSha256 = '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'
const key = 'filter/smooth:smoothEdge'
const sourceRelative = 'sources/filter/smooth/smoothEdge.glsl'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, sourceRelative)
const factoryName = 'canonicalFactory140'
const factorySha256 = '732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function nextF32(value, direction) {
  const a = new Float32Array([value])
  const u = new Uint32Array(a.buffer)
  if (value === 0) u[0] = direction > 0 ? 1 : 0x80000001
  else u[0] += (value > 0) === (direction > 0) ? 1 : -1
  return a[0]
}

if (sha256(fs.readFileSync(canonicalPath)) !== canonicalSha256) throw new Error('pinned canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== catalogSha256) throw new Error('pinned public catalog drift')
if (sha256(fs.readFileSync(adapterIndexPath)) !== adapterIndexSha256) throw new Error('pinned adapter index drift')
const source = fs.readFileSync(sourcePath)
if (source.byteLength !== 1554 || sha256(source) !== 'b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265') throw new Error('pinned source drift')
const canonical = canonicalKernelFactories[key]
const publicFactory = kernelFactories.get(key)
if (canonical?.name !== factoryName || sha256(Buffer.from(canonical.toString())) !== factorySha256) throw new Error('canonical factory drift')
if (publicFactory !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')
const factoryText = canonical.toString()

const globalLine = '  var LUMA_WEIGHTS = new Float32Array([0.29899999499320984, 0.5870000123977661, 0.11400000005960464]);'
const helperBlock = `  function luminance (rgb) {
  \trgb = $runtime.copy(rgb);
  \treturn dot(rgb, LUMA_WEIGHTS);
  };`
const mainStart = '  function main () {'
const exactLocalLine = '  \tvar LUMA_WEIGHTS = new Float32Array([0.29899999499320984, 0.5870000123977661, 0.11400000005960464]);'
const mainCallLines = factoryText.split('\n').filter(line => line.includes('= luminance('))

function occurrences(text, needle) { return text.split(needle).length - 1 }
function replaceExact(text, from, to, count = 1) {
  if (occurrences(text, from) !== count) throw new Error(`factory shape drift for ${from}`)
  return text.replace(from, to)
}
if (occurrences(factoryText, globalLine) !== 1 || occurrences(factoryText, helperBlock) !== 1 || occurrences(factoryText, mainStart) !== 1 || mainCallLines.length !== 5) throw new Error('Smooth Edge factory shape drift')

function evaluated(text) { return (0, eval)(`(${text})`) }
function replaceGlobal(replacement) { return evaluated(replaceExact(factoryText, globalLine, replacement)) }
function helperLocalFactory(localLine = exactLocalLine) {
  let text = replaceExact(factoryText, `${globalLine}\n`, '')
  text = replaceExact(text, helperBlock, helperBlock.replace('  \trgb =', `${localLine}\n  \trgb =`))
  return evaluated(text)
}
function mainOwnedFactory() {
  let text = replaceExact(factoryText, `${globalLine}\n`, '')
  text = replaceExact(text, helperBlock, helperBlock.replace('function luminance (rgb)', 'function luminance (rgb, LUMA_WEIGHTS)'))
  text = replaceExact(text, mainStart, `${mainStart}\n${exactLocalLine}`)
  for (const line of mainCallLines) text = replaceExact(text, line, `${line.slice(0, -2)}, LUMA_WEIGHTS);`)
  return evaluated(text)
}

const mutations = [
  { id: 'red-value-0.299-to-0.3', hazard: 'value/lane-0', expectation: 'diverge', factory: replaceGlobal(globalLine.replace('0.29899999499320984', '0.30000001192092896')) },
  { id: 'green-value-0.587-to-0.6', hazard: 'value/lane-1', expectation: 'diverge', factory: replaceGlobal(globalLine.replace('0.5870000123977661', '0.6000000238418579')) },
  { id: 'blue-value-0.114-to-0.2', hazard: 'value/lane-2', expectation: 'diverge', factory: replaceGlobal(globalLine.replace('0.11400000005960464', '0.20000000298023224')) },
  { id: 'red-blue-lane-order-swap', hazard: 'lane-order', expectation: 'diverge', factory: replaceGlobal('  var LUMA_WEIGHTS = new Float32Array([0.11400000005960464, 0.5870000123977661, 0.29899999499320984]);') },
  { id: 'vec3-type-to-scalar', hazard: 'type/arity', expectation: 'diverge', factory: replaceGlobal('  var LUMA_WEIGHTS = 0.29899999499320984;') },
  { id: 'vec3-to-vec4-extra-lane-control', hazard: 'type/arity-observably-inert', expectation: 'identity-structural-reject', factory: replaceGlobal('  var LUMA_WEIGHTS = new Float32Array([0.29899999499320984, 0.5870000123977661, 0.11400000005960464, 0.75]);') },
  {
    id: 'const-storage-to-cross-call-mutation', hazard: 'storage/write/lifetime', expectation: 'diverge',
    factory: evaluated(replaceExact(factoryText, '  \treturn dot(rgb, LUMA_WEIGHTS);', '  \tLUMA_WEIGHTS[0] = Math.fround(LUMA_WEIGHTS[0] + 0.125);\n  \treturn dot(rgb, LUMA_WEIGHTS);')),
  },
  { id: 'resolved-read-replaced-by-rgb-self-dot', hazard: 'read/site/parent', expectation: 'diverge', factory: evaluated(replaceExact(factoryText, '  \treturn dot(rgb, LUMA_WEIGHTS);', '  \treturn dot(rgb, rgb);')) },
  { id: 'helper-local-exact-f32-materialization', hazard: 'authorized-ownership/materialization', expectation: 'identity-authorized-lowering', factory: helperLocalFactory() },
  { id: 'helper-local-source-double-array', hazard: 'materialization/F32-boundary', expectation: 'diverge', factory: helperLocalFactory('  \tvar LUMA_WEIGHTS = [0.299, 0.587, 0.114];') },
  { id: 'main-owned-exact-f32-vector-control', hazard: 'wrong-owner-observably-inert', expectation: 'identity-structural-reject', factory: mainOwnedFactory() },
]

const boundaryA = new Float32Array([0.1850000023841858, 0.3672654628753662, 0.5742971897125244, 0.61])
const boundaryB = new Float32Array([0.09090909361839294, 0.21995927393436432, 0.5, 0.37])
const boundaryThreshold = f(0.12307180464267731)

function modularSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    data[i] = f((((37 * x + 17 * y + 11 + 13 * phase) % 127) + 1) / 129)
    data[i + 1] = f((((19 * x + 43 * y + 7 + 23 * phase) % 113) + 2) / 117)
    data[i + 2] = f((((61 * x + 29 * y + 3 + 31 * phase) % 109) + 3) / 115)
    data[i + 3] = f((((7 * x + 5 * y + 2 + phase) % 23) + 8) / 31)
  }
  return new Surface(width, height, data)
}
function filledSurface(width, height, color) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < width * height; i += 1) data.set(color, i * 4)
  return new Surface(width, height, data)
}
function boundarySurface() {
  const surface = filledSurface(5, 5, boundaryA)
  surface.data.set(boundaryB, ((3 * 5 + 2) * 4))
  return surface
}
function cardinalSurface() {
  const surface = filledSurface(5, 5, new Float32Array([f(0.35), f(0.42), f(0.27), f(0.8)]))
  const put = (x, y, rgba) => surface.data.set(new Float32Array(rgba.map(f)), ((y * 5 + x) * 4))
  put(2, 1, [0.91, 0.08, 0.19, 0.31])
  put(2, 3, [0.13, 0.88, 0.26, 0.47])
  put(1, 2, [0.07, 0.21, 0.96, 0.59])
  put(3, 2, [0.74, 0.63, 0.04, 0.71])
  return surface
}

const cases = [
  { name: 'pass-through-modular-tile', width: 8, height: 5, smoothType: 0, threshold: f(0.23), tileOffset: new Float32Array([4, 3]), fullResolution: new Float32Array([17, 13]), surface: () => modularSurface(8, 5, 1), coverage: ['smoothType==0 early return', 'one fetch', 'exact RGBA including input alpha', 'nonzero tile/full-resolution bindings'] },
  { name: 'edge-modular-type1', width: 9, height: 6, smoothType: 1, threshold: f(0.18), surface: () => modularSurface(9, 6, 2), coverage: ['smoothType nonzero edge path', 'five fetches', 'all cardinal directions', 'non-square'] },
  { name: 'edge-modular-type2-same-branch', width: 9, height: 6, smoothType: 2, threshold: f(0.18), surface: () => modularSurface(9, 6, 2), coverage: ['all nonzero smoothType values share edge path', 'byte identity control against type1'] },
  { name: 'threshold-one-ulp-below', width: 5, height: 5, smoothType: 1, threshold: nextF32(boundaryThreshold, -1), surface: boundarySurface, coverage: ['threshold below exact canonical luma delta', 'step inclusive control'] },
  { name: 'threshold-exact', width: 5, height: 5, smoothType: 1, threshold: boundaryThreshold, surface: boundarySurface, coverage: ['threshold equals canonical F32 luma delta', 'materialization sensitivity', 'step inclusive'] },
  { name: 'threshold-one-ulp-above', width: 5, height: 5, smoothType: 1, threshold: nextF32(boundaryThreshold, 1), surface: boundarySurface, coverage: ['threshold above exact canonical luma delta', 'step false control'] },
  { name: 'single-pixel-clamped-neighbors', width: 1, height: 1, smoothType: 1, threshold: f(0.0001), surface: () => filledSurface(1, 1, new Float32Array([f(0.23), f(0.67), f(0.41), f(0.29)])), coverage: ['all four neighbors clamp to center', 'zero edges', 'alpha forced to one'] },
  { name: 'asymmetric-cardinal-lanes', width: 5, height: 5, smoothType: 1, threshold: f(0.12), surface: cardinalSurface, coverage: ['red/green/blue lane order', 'horizontal/vertical edge channel ownership', 'four distinct cardinal neighbors'] },
]

function render(factory, definition) {
  const input = definition.surface()
  const original = new Float32Array(input.data)
  const kernel = bindCanonicalKernel(factory, {
    width: definition.width, height: definition.height, time: f(0.375), frame: 29, deltaTime: f(1 / 60), seed: f(43),
    uniforms: { smoothType: definition.smoothType, threshold: definition.threshold }, textures: { inputTex: input },
    tileOffset: definition.tileOffset, fullResolution: definition.fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: f(0.375), seed: f(43) })
  if (!sameBytes(input.data, original)) throw new Error(`${definition.name}: input mutated`)
  return { input, output }
}
function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}
function probes(surface) {
  const points = [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]]
  return points.map(([x, y]) => probe(surface, x, y))
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
  let byteDiff = 0, laneDiff = 0, rgbaDiff = 0, maxAbs = 0
  for (let i = 0; i < rb.length; i += 1) if (rb[i] !== cb[i]) byteDiff += 1
  for (let i = 0; i < reference.data.length; i += 1) if (f32Bits(reference.data[i]) !== f32Bits(candidate.data[i])) { laneDiff += 1; maxAbs = Math.max(maxAbs, Math.abs(reference.data[i] - candidate.data[i])) }
  for (let i = 0; i < rr.length; i += 1) if (rr[i] !== cr[i]) rgbaDiff += 1
  return { same_f32_bytes: byteDiff === 0, same_rgba8_bytes: rgbaDiff === 0, different_f32_bytes: byteDiff, different_f32_lanes: laneDiff, different_rgba8_bytes: rgbaDiff, max_absolute_f32_difference: maxAbs, candidate_f32_sha256: sha256(cb), candidate_rgba8_sha256: sha256(bytes(cr)) }
}

function buildData() {
  const reference = new Map()
  const caseResults = cases.map(definition => {
    const first = render(canonical, definition), second = render(canonical, definition)
    if (!sameBytes(first.input.data, second.input.data) || !sameBytes(first.output.data, second.output.data)) throw new Error(`${definition.name}: repeat mismatch`)
    reference.set(definition.name, first.output)
    return {
      name: definition.name, dimensions: { width: definition.width, height: definition.height }, smooth_type: definition.smoothType,
      threshold: { value: definition.threshold, f32_bits_le: f32Bits(definition.threshold) },
      tile_offset: Array.from(definition.tileOffset ?? new Float32Array(2)), full_resolution: Array.from(definition.fullResolution ?? new Float32Array([definition.width, definition.height])), coverage: definition.coverage,
      input: { f32_sha256: sha256(bytes(first.input.data)), probes: probes(first.input) }, output: outputRecord(first.output), repeat_identity: true, input_immutable: true,
    }
  })
  if (!sameBytes(reference.get('edge-modular-type1').data, reference.get('edge-modular-type2-same-branch').data)) throw new Error('nonzero smoothType branch outputs differ')
  const passRecord = caseResults.find(x => x.name === 'pass-through-modular-tile')
  if (passRecord.input.f32_sha256 !== passRecord.output.f32_sha256) throw new Error('pass-through output differs from input')
  const mutationResults = mutations.map(mutation => {
    const results = cases.map(definition => ({ case: definition.name, ...diff(reference.get(definition.name), render(mutation.factory, definition).output) }))
    if (mutation.expectation === 'diverge' && !results.some(x => !x.same_f32_bytes)) throw new Error(`${mutation.id}: missing divergence`)
    if (mutation.expectation.startsWith('identity') && results.some(x => !x.same_f32_bytes || !x.same_rgba8_bytes)) throw new Error(`${mutation.id}: missing identity`)
    return { id: mutation.id, hazard: mutation.hazard, expectation: mutation.expectation, case_results: results }
  })
  const exactBoundary = caseResults.find(x => x.name === 'threshold-exact').output.probes.find(x => x.at_top_down_xy[0] === 2 && x.at_top_down_xy[1] === 2)
  const belowBoundary = caseResults.find(x => x.name === 'threshold-one-ulp-below').output.probes.find(x => x.at_top_down_xy[0] === 2 && x.at_top_down_xy[1] === 2)
  const aboveBoundary = caseResults.find(x => x.name === 'threshold-one-ulp-above').output.probes.find(x => x.at_top_down_xy[0] === 2 && x.at_top_down_xy[1] === 2)
  if (belowBoundary.values[0] !== 1 || exactBoundary.values[0] !== 1 || aboveBoundary.values[0] !== 0) throw new Error('threshold center probe boundary drift')
  return {
    schema: 'noisemaker-for-cpp.task26.smooth-edge-luma-weights.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, public_api: 'kernelFactories.get(key)', canonical_identity: true, adapter_entry_absent: true, canonical_kernels_sha256: canonicalSha256, public_catalog_sha256: catalogSha256, adapter_index_sha256: adapterIndexSha256 },
    program: {
      key, source: sourceRelative, raw_source_bytes: 1554, raw_source_sha256: 'b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265', normalized_source_bytes: 1235, normalized_source_sha256: '42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c', defines: {}, profile: 'smooth-edge-luma-weights-v1', generic_const_vec3_capability: false,
      canonical_factory_name: factoryName, canonical_factory_to_string_sha256: factorySha256,
      binding_signature: ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'inputTex:sampler2D@3/S1', 'smoothType:int@4', 'threshold:float@5'], output: 'fragColor:vec4@6',
      resources: { samplers: 1, ordinary_uniforms: 4, outputs: 1, uses_texel_fetch: true, uses_derivatives: false, static_texel_fetch_sites: 6, dynamic_fetches_pass_through: 1, dynamic_fetches_edge_path: 5, texture_size_calls_per_pixel: 1 },
      source_constant: { symbol: 'LUMA_WEIGHTS', symbol_id: 7, storage: 'const', writable: false, type: 'vec3', declaration_span: '12:1-12:53', raw_line: 19, values: [0.299, 0.587, 0.114], f32_values: [f(0.299), f(0.587), f(0.114)], f32_bits_le: [f32Bits(f(0.299)), f32Bits(f(0.587)), f32Bits(f(0.114))], static_reads: 1, read_owner: 'luminance', read_span: '15:21-15:33', dynamic_reads_pass_through: 0, dynamic_reads_edge_path: 5 },
    },
    fixture: { input: 'top-down deterministic or exact-pattern F32 RGBA Surface', fragment_origin: 'bottom-left runPass coordinates', verification: 'fresh double render, immutable input, finite full output, F32/RGBA8 hashes and five probes' },
    cases: caseResults,
    cross_case_controls: [
      { name: 'pass-through-output-equals-input', same_f32_bytes: true },
      { name: 'smoothType-1-vs-2-same-nonzero-branch', same_f32_bytes: true, same_rgba8_bytes: true },
    ],
    mutations: mutationResults,
  }
}

function buildReport(data) {
  const lines = [
    '# Task 26 Smooth Edge LUMA_WEIGHTS public-canonical oracle report', '',
    `Cases: **${data.cases.length}**  `, `Mutations and controls: **${data.mutations.length}**`, '',
    'Public dispatch is the exact canonical factory and has no adapter. Every case repeats byte-identically, preserves its input, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.', '',
    '## Cases', '', '| Case | Size | smoothType | Threshold bits | Output F32 SHA-256 | Output RGBA8 SHA-256 |', '| --- | --- | ---: | --- | --- | --- |',
  ]
  for (const c of data.cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.smooth_type} | ${c.threshold.f32_bits_le} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Mutation and control results', '', '| Mutation/control | Hazard | Expectation | Divergent cases | Max changed F32 lanes | Max changed RGBA8 bytes |', '| --- | --- | --- | ---: | ---: | ---: |')
  for (const m of data.mutations) lines.push(`| ${m.id} | ${m.hazard} | ${m.expectation} | ${m.case_results.filter(x => !x.same_f32_bytes).length}/${m.case_results.length} | ${Math.max(...m.case_results.map(x => x.different_f32_lanes))} | ${Math.max(...m.case_results.map(x => x.different_rgba8_bytes))} |`)
  lines.push('', 'The exact helper-local Float32 materialization is byte-identical and is the only authorized ownership lowering. The vec4-extra-lane and main-owned controls are also observably identical, proving output parity cannot replace structural type/arity/owner authentication. Source-double helper materialization diverges at the frozen F32 threshold boundary.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') { fs.writeFileSync(jsonPath, json); fs.writeFileSync(reportPath, report); process.stdout.write('wrote task-26-oracles.json and task-26-oracle-report.md\n') }
else if (process.argv.length === 3 && process.argv[2] === '--check') { if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error('task-26-oracles.json drift'); if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('task-26-oracle-report.md drift'); process.stdout.write('ok task-26-oracles.json and task-26-oracle-report.md\n') }
else throw new Error('usage: node task-26-oracle-generator.mjs [--write|--check]')
