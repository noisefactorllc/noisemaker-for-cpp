import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-27-oracles.json')
const reportPath = path.join(here, 'task-27-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const catalogPath = path.join(cpuRoot, 'src/effects/catalog.js')
const adapterIndexPath = path.join(cpuRoot, 'src/effects/adapters/index.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const catalogSha256 = 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'
const adapterIndexSha256 = '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'
const key = 'synth/perlin:perlin'
const sourceRelative = 'sources/synth/perlin/perlin.glsl'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, sourceRelative)
const factoryName = 'canonicalFactory268'
const factorySha256 = '55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function f64Bits(value) { const a = new Float64Array([value]); return `0x${new DataView(a.buffer).getBigUint64(0, true).toString(16).padStart(16, '0')}` }
function hex32(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
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
if (source.byteLength !== 10882 || sha256(source) !== '9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318') throw new Error('pinned source drift')
const canonical = canonicalKernelFactories[key]
const publicFactory = kernelFactories.get(key)
if (canonical?.name !== factoryName || sha256(Buffer.from(canonical.toString())) !== factorySha256) throw new Error('canonical factory drift')
if (publicFactory !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')

const factoryText = canonical.toString()
const xorText = '(q[0] ^ q[1]) ^ q[2]'
if (occurrences(factoryText, xorText) !== 1) throw new Error('Perlin scalar XOR factory shape drift')
const renderMutations = [
  { id: 'outer-xor-to-or', hazard: 'outer-operator', expectation: 'identity-because-unreachable-structural-reject', factory: evaluated(replaceExact(factoryText, xorText, '(q[0] ^ q[1]) | q[2]')) },
  { id: 'inner-xor-to-or', hazard: 'inner-operator', expectation: 'identity-because-unreachable-structural-reject', factory: evaluated(replaceExact(factoryText, xorText, '(q[0] | q[1]) ^ q[2]')) },
  { id: 'left-tree-to-right-tree', hazard: 'parent/associativity', expectation: 'identity-because-unreachable-structural-reject', factory: evaluated(replaceExact(factoryText, xorText, 'q[0] ^ (q[1] ^ q[2])')) },
  { id: 'both-xor-to-add', hazard: 'operator/type-semantics', expectation: 'identity-because-unreachable-structural-reject', factory: evaluated(replaceExact(factoryText, xorText, '(q[0] + q[1]) + q[2]')) },
]

const cases = [
  { name: 'mono-default-shape', width: 8, height: 5, time: f(0), seed: 0, uniforms: { DIMENSIONS: 2, scale: f(25), seed: 0, octaves: 1, colorMode: 0, ridges: 0, warpIterations: 0, warpScale: f(50), warpIntensity: f(50), speed: f(1) }, coverage: ['DIMENSIONS=2', 'mono', 'one octave', 'no warp', 'rectangular'] },
  { name: 'rgb-four-octaves', width: 7, height: 6, time: f(0.125), seed: 17, uniforms: { DIMENSIONS: 2, scale: f(43), seed: 17, octaves: 4, colorMode: 1, ridges: 0, warpIterations: 0, warpScale: f(50), warpIntensity: f(50), speed: f(2) }, coverage: ['RGB channel offsets', 'four octaves', 'time animation'] },
  { name: 'ridged-six-octaves', width: 6, height: 7, time: f(0.625), seed: 99, uniforms: { DIMENSIONS: 2, scale: f(8), seed: 99, octaves: 6, colorMode: 1, ridges: 1, warpIterations: 0, warpScale: f(50), warpIntensity: f(50), speed: f(1) }, coverage: ['ridged branch', 'six public octaves', 'portrait'] },
  { name: 'single-domain-warp', width: 9, height: 5, time: f(0.33), seed: 5, uniforms: { DIMENSIONS: 2, scale: f(72), seed: 5, octaves: 3, colorMode: 1, ridges: 0, warpIterations: 1, warpScale: f(40), warpIntensity: f(65), speed: f(3) }, coverage: ['one warp iteration', 'nonzero intensity', 'three octaves'] },
  { name: 'four-domain-warps-ridged', width: 5, height: 8, time: f(0.91), seed: 64, uniforms: { DIMENSIONS: 2, scale: f(15), seed: 64, octaves: 5, colorMode: 1, ridges: 1, warpIterations: 4, warpScale: f(7), warpIntensity: f(100), speed: f(5) }, coverage: ['four public warp iterations', 'ridged', 'five octaves', 'high speed'] },
  { name: 'tiled-full-resolution', width: 6, height: 4, time: f(0.44), seed: 12, tileOffset: new Float32Array([7, 11]), fullResolution: new Float32Array([19, 17]), uniforms: { DIMENSIONS: 2, scale: f(31), seed: 12, octaves: 2, colorMode: 1, ridges: 0, warpIterations: 2, warpScale: f(80), warpIntensity: f(22), speed: f(2) }, coverage: ['nonzero tile offset', 'larger full resolution', 'two warps'] },
  { name: 'speed-zero-time-inert', width: 4, height: 4, time: f(0.875), seed: 31, uniforms: { DIMENSIONS: 2, scale: f(55), seed: 31, octaves: 3, colorMode: 0, ridges: 0, warpIterations: 0, warpScale: f(50), warpIntensity: f(50), speed: f(0) }, coverage: ['speed zero', 'nonzero time', 'mono'] },
  { name: 'full-resolution-fallback', width: 5, height: 3, time: f(0.2), seed: 3, fullResolution: new Float32Array([0, 0]), uniforms: { DIMENSIONS: 2, scale: f(100), seed: 3, octaves: 1, colorMode: 1, ridges: 0, warpIterations: 0, warpScale: f(50), warpIntensity: f(50), speed: f(1) }, coverage: ['fullResolution.x below one', '1024 fallback', 'scale maximum'] },
]

function render(factory, definition) {
  const kernel = bindCanonicalKernel(factory, {
    width: definition.width, height: definition.height, time: definition.time, frame: 37,
    deltaTime: f(1 / 60), seed: definition.seed, uniforms: definition.uniforms,
    tileOffset: definition.tileOffset, fullResolution: definition.fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.seed })
  return output
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
  return { f32_sha256: sha256(bytes(output.data)), rgba8_sha256: sha256(bytes(rgba)), probes: probes(output), finite_lanes: output.data.length }
}
function diff(reference, candidate) {
  const rb = bytes(reference.data), cb = bytes(candidate.data)
  const rr = reference.toRgba8(), cr = candidate.toRgba8()
  let differentF32 = 0, differentRgba8 = 0, maxAbs = 0
  for (let i = 0; i < reference.data.length; i += 1) if (reference.data[i] !== candidate.data[i]) { differentF32 += 1; maxAbs = Math.max(maxAbs, Math.abs(reference.data[i] - candidate.data[i])) }
  for (let i = 0; i < rr.length; i += 1) if (rr[i] !== cr[i]) differentRgba8 += 1
  return { same_f32_bytes: Buffer.compare(rb, cb) === 0, same_rgba8_bytes: Buffer.compare(bytes(rr), bytes(cr)) === 0, different_f32_lanes: differentF32, different_rgba8_bytes: differentRgba8, max_abs_f32_delta: maxAbs, candidate_f32_sha256: sha256(cb), candidate_rgba8_sha256: sha256(bytes(cr)) }
}

const wordInputs = [
  [0x00000000, 0x00000000, 0x00000000], [0xffffffff, 0x00000000, 0x00000000],
  [0x80000000, 0x00000000, 0x00000000], [0x7fffffff, 0xffffffff, 0x00000000],
  [0xaaaaaaaa, 0x55555555, 0xffffffff], [0x01234567, 0x89abcdef, 0xfedcba98],
  [0xdeadbeef, 0xcafebabe, 0x8badf00d], [0x00000001, 0x00000002, 0x00000004],
  [0x80000000, 0x40000000, 0x20000000], [0xffffffff, 0xffffffff, 0x80000000],
  [0x13579bdf, 0x2468ace0, 0xf0f0f0f0], [0x0000ffff, 0xffff0000, 0x00ff00ff],
]
function wordRecord([a0, b0, c0]) {
  const a = a0 >>> 0, b = b0 >>> 0, c = c0 >>> 0
  const inner = (a ^ b) >>> 0, outer = (inner ^ c) >>> 0
  const signed = (a ^ b) ^ c
  const numerator = f(outer), signedNumerator = f(signed)
  const denominator = f(4294967295)
  return {
    inputs_hex: [hex32(a), hex32(b), hex32(c)], inner_u32_hex: hex32(inner), result_u32_hex: hex32(outer),
    js_signed_result: signed, source_unsigned_numerator_f32: numerator,
    source_unsigned_numerator_f32_bits_le: f32Bits(numerator), canonical_js_signed_numerator_f32_bits_le: f32Bits(signedNumerator),
    denominator_f32_bits_le: f32Bits(denominator), source_typed_ratio: numerator / denominator,
    source_typed_ratio_f64_bits_le: f64Bits(numerator / denominator),
    mutations: {
      outer_or: hex32(inner | c), inner_or: hex32(((a | b) ^ c) >>> 0),
      outer_and: hex32(inner & c), inner_and: hex32(((a & b) ^ c) >>> 0),
      right_associated_xor: hex32((a ^ (b ^ c)) >>> 0),
    },
  }
}

function buildData() {
  const reference = new Map()
  const caseResults = cases.map(definition => {
    const first = render(canonical, definition), second = render(canonical, definition)
    if (!sameBytes(first.data, second.data)) throw new Error(`${definition.name}: repeat mismatch`)
    reference.set(definition.name, first)
    return {
      name: definition.name, dimensions: { width: definition.width, height: definition.height }, time: definition.time,
      seed: definition.seed, uniforms: definition.uniforms,
      tile_offset: Array.from(definition.tileOffset ?? new Float32Array(2)),
      full_resolution: Array.from(definition.fullResolution ?? new Float32Array([definition.width, definition.height])),
      coverage: definition.coverage, output: outputRecord(first), repeat_identity: true,
    }
  })
  const mutationResults = renderMutations.map(mutation => {
    const results = cases.map(definition => ({ case: definition.name, ...diff(reference.get(definition.name), render(mutation.factory, definition)) }))
    if (results.some(x => !x.same_f32_bytes || !x.same_rgba8_bytes)) throw new Error(`${mutation.id}: default path unexpectedly reached scalar XOR`)
    return { id: mutation.id, hazard: mutation.hazard, expectation: mutation.expectation, case_results: results }
  })
  const wordCases = wordInputs.map(wordRecord)
  for (const mode of ['outer_or', 'inner_or', 'outer_and', 'inner_and']) {
    if (!wordCases.some(row => row.mutations[mode] !== row.result_u32_hex)) throw new Error(`${mode}: direct words do not discriminate mutation`)
  }
  if (wordCases.some(row => row.mutations.right_associated_xor !== row.result_u32_hex)) throw new Error('XOR associativity control drift')
  if (!wordCases.some(row => row.source_unsigned_numerator_f32_bits_le !== row.canonical_js_signed_numerator_f32_bits_le)) throw new Error('word table lacks signed/unsigned discriminator')
  return {
    schema: 'noisemaker-for-cpp.task27.perlin-scalar-uint-xor.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, public_api: 'kernelFactories.get(key)', canonical_identity: true, adapter_entry_absent: true, canonical_kernels_sha256: canonicalSha256, public_catalog_sha256: catalogSha256, adapter_index_sha256: adapterIndexSha256 },
    program: {
      key, source: sourceRelative, raw_source_bytes: 10882, raw_source_sha256: '9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318', normalized_source_bytes: 4875, normalized_source_sha256: '88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64', defines: { DIMENSIONS: 2 }, profile: 'perlin-scalar-uint-xor-v1', generic_scalar_bitwise_capability: false, dimensions_3_authorized: false,
      canonical_factory_name: factoryName, canonical_factory_to_string_sha256: factorySha256,
      binding_signature: ['resolution:vec2@1', 'tileOffset:vec2@2', 'fullResolution:vec2@3', 'aspect:float@4', 'time:float@5', 'scale:float@6', 'seed:int@7', 'octaves:int@8', 'colorMode:int@9', 'ridges:int@10', 'warpIterations:int@11', 'warpScale:float@12', 'warpIntensity:float@13', 'speed:float@14'], output: 'fragColor:vec4@15',
      scalar_uint_xor: { static_sites: 2, owner: 'hash3', owner_signature_id: 49, normalized_line: 73, default_entrypoint_reachable: false, source_typed_semantics: 'left-associated std::uint32_t XOR', public_javascript_semantics: 'signed Int32 XOR; not an oracle for future DIMENSIONS=3' },
    },
    fixture: { output: 'top-down F32 RGBA Surface', fragment_origin: 'bottom-left runPass coordinates', verification: 'fresh double render, finite full output, F32/RGBA8 hashes and five probes' },
    cases: caseResults,
    unreachable_mutation_controls: mutationResults,
    direct_unsigned_word_cases: wordCases,
    direct_word_contract: { expression: '(a ^ b) ^ c', operand_and_result_type: 'std::uint32_t', numerator_conversion: 'binary32', denominator_source: '4294967295.0', denominator_f32_bits_le: f32Bits(f(4294967295)), right_association_observably_equivalent_but_structurally_rejected: true },
    negative_closure: { foreign_key: 'reject', missing_or_foreign_profile: 'reject', operator_other_than_exact_two_xor_nodes: 'reject', signed_int_operands_or_result: 'reject', vector_scalar_or_mixed_operands: 'reject', changed_parent_or_owner_or_path: 'reject', defines_other_than_exact_DIMENSIONS_2: 'reject', DIMENSIONS_3: 'reject', generic_scalar_bitwise_helper_or_overload: 'forbidden' },
  }
}

function buildReport(data) {
  const lines = [
    '# Task 27 Perlin scalar uint XOR public-canonical oracle report', '',
    `Public render cases: **${data.cases.length}**  `, `Unreachable mutation controls: **${data.unreachable_mutation_controls.length}**  `, `Direct unsigned-word cases: **${data.direct_unsigned_word_cases.length}**`, '',
    'The public dispatch is the exact canonical factory and has no adapter. Every default `DIMENSIONS=2` case repeats byte-identically and records finite full F32/RGBA8 output hashes plus five probes. The two scalar XOR sites live only in unreachable `hash3`, so public output intentionally cannot authenticate them.', '',
    '## Public render cases', '', '| Case | Size | Output F32 SHA-256 | Output RGBA8 SHA-256 |', '| --- | --- | --- | --- |',
  ]
  for (const c of data.cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Unreachable mutation controls', '', '| Mutation | Hazard | Default cases changed |', '| --- | --- | ---: |')
  for (const m of data.unreachable_mutation_controls) lines.push(`| ${m.id} | ${m.hazard} | ${m.case_results.filter(x => !x.same_f32_bytes).length}/${m.case_results.length} |`)
  lines.push('', 'All four changed factories are byte-identical on all default cases. This is a required reachability control, not semantic acceptance.', '', '## Direct unsigned-word contract', '', '| Inputs (hex) | Inner XOR | Result XOR | Source unsigned F32 bits | Canonical JS signed F32 bits |', '| --- | --- | --- | --- | --- |')
  for (const w of data.direct_unsigned_word_cases) lines.push(`| ${w.inputs_hex.join(', ')} | ${w.inner_u32_hex} | ${w.result_u32_hex} | ${w.source_unsigned_numerator_f32_bits_le} | ${w.canonical_js_signed_numerator_f32_bits_le} |`)
  lines.push('', 'The native suite must execute these words through an explicit `std::uint32_t` expression and separately prove the generated `hash3` spelling and exact two-node typed-tree closure. Image equality alone is insufficient; `DIMENSIONS=3` remains unauthorized.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') { fs.writeFileSync(jsonPath, json); fs.writeFileSync(reportPath, report); process.stdout.write('wrote task-27-oracles.json and task-27-oracle-report.md\n') }
else if (process.argv.length === 3 && process.argv[2] === '--check') { if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error('task-27-oracles.json drift'); if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('task-27-oracle-report.md drift'); process.stdout.write('ok task-27-oracles.json and task-27-oracle-report.md\n') }
else throw new Error('usage: node task-27-oracle-generator.mjs [--write|--check]')
