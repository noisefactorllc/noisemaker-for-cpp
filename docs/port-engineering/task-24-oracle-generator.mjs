import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-24-oracles.json')
const reportPath = path.join(here, 'task-24-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourceRelative = 'sources/filter/pixelSort/gatherSorted.glsl'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, sourceRelative)
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const key = 'filter/pixelSort:gatherSorted'
const factoryName = 'canonicalFactory107'
const factorySha256 = '6f4021f01bc289554506215c3f01d716b4fcbf2b458527d02f1a0888d7eecb7c'
const originalLine = 'var brightestX = round(brightestXNorm * (cpu_float(width - 1)))|0;'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function scalar(value) { return { value, f32_bits_le: f32Bits(value), negative_zero: Object.is(value, -0) } }

if (sha256(fs.readFileSync(canonicalPath)) !== canonicalSha256) throw new Error('pinned canonical runtime drift')
const source = fs.readFileSync(sourcePath)
if (source.byteLength !== 1896 || sha256(source) !== 'a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386') throw new Error('pinned source drift')
const canonical = canonicalKernelFactories[key]
const publicFactory = kernelFactories.get(key)
if (canonical?.name !== factoryName || sha256(Buffer.from(canonical.toString())) !== factorySha256) throw new Error('canonical factory drift')
if (publicFactory !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')
const factoryText = canonical.toString()
if (factoryText.split(originalLine).length - 1 !== 1) throw new Error('round site factory drift')

function preparedSurface(width, height) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    data[i] = ((37 * x + 17 * y + 11) % 113) / 112
    data[i + 1] = ((19 * x + 29 * y + 7) % 109) / 108
    data[i + 2] = ((53 * x + 13 * y + 3) % 107) / 106
    data[i + 3] = (((7 * x + 5 * y + 2) % 19) - 4) / 11
  }
  return new Surface(width, height, data)
}

function rankSurface(width, height) {
  const data = new Float32Array(width * height * 4)
  const denominator = Math.max(1, width - 1)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    const permutation = (x * 23 + y * 11 + 5) % width
    data[i] = permutation / denominator
    data[i + 1] = ((x * 7 + y * 3) % width) / denominator
    data[i + 2] = x / denominator
    data[i + 3] = 1
  }
  return new Surface(width, height, data)
}

function brightestSurface(values) {
  const data = new Float32Array(values.length * 4)
  for (let y = 0; y < values.length; y += 1) {
    data[y * 4] = values[y]
    data[y * 4 + 3] = 1
  }
  return new Surface(1, values.length, data)
}

const cases = [
  { name: 'normalized-positive-zero', width: 9, brightest: [f(0), f(0), f(0), f(0)], coverage: ['normalized-domain', 'positive-zero', 'round-to-zero', '64-trip-loop'] },
  { name: 'normalized-negative-zero-control', width: 9, brightest: [f(-0), f(-0), f(-0), f(-0)], coverage: ['signed-zero-control', 'immediate-int-erases-sign', 'same-output-as-positive-zero', '64-trip-loop'] },
  { name: 'normalized-half-boundaries', width: 9, brightest: [f(2.499 / 8), f(2.5 / 8), f(2.501 / 8), f(1), f(1 / 8)], coverage: ['below-half', 'exact-half-up', 'above-half', 'upper-endpoint', 'normalized-domain'] },
  { name: 'normalized-wide-67', width: 67, brightest: [f(0), f(0.25), f(0.5), f(0.75), f(1)], coverage: ['width-above-loop-count', 'sparse-64-sample-search', 'normalized-domain', 'endpoints-and-halves'] },
]

const exclusionCases = [
  { name: 'excluded-negative-half', width: 9, brightest: [f(-0.5 / 8), f(-0.5 / 8)], coverage: ['outside-normalized-domain', 'Math.round-negative-zero', 'immediate-int-erases-sign'] },
  { name: 'excluded-out-of-range-wrap', width: 9, brightest: [f(536870912), f(536870912)], coverage: ['outside-normalized-domain', 'JavaScript-ToInt32-wrap', 'native-int32-clamp-diverges'] },
]

const replacements = {
  floor: 'var brightestX = floor(brightestXNorm * (cpu_float(width - 1)))|0;',
  ceil: 'var brightestX = Math.ceil(brightestXNorm * (cpu_float(width - 1)))|0;',
  native_floor_half_clamp: 'var brightestX = Math.max(-2147483648, Math.min(2147483647, Math.trunc(floor((brightestXNorm * (cpu_float(width - 1))) + 0.5))));',
  std_round_away: 'var roundInput = brightestXNorm * (cpu_float(width - 1)); var brightestX = Math.trunc(Math.sign(roundInput) * Math.floor(Math.abs(roundInput) + 0.5));',
}

function mutatedFactory(replacement) { return (0, eval)(`(${factoryText.replace(originalLine, replacement)})`) }
const factories = {
  canonical,
  floor: mutatedFactory(replacements.floor),
  ceil: mutatedFactory(replacements.ceil),
  native_floor_half_clamp: mutatedFactory(replacements.native_floor_half_clamp),
  std_round_away: mutatedFactory(replacements.std_round_away),
  loop8: (0, eval)(`(${factoryText.replace('var NUM_SAMPLES = 64;', 'var NUM_SAMPLES = 8;')})`),
}

function render(factory, definition) {
  const height = definition.brightest.length
  const prepared = preparedSurface(definition.width, height)
  const rank = rankSurface(definition.width, height)
  const brightest = brightestSurface(definition.brightest)
  const originals = [prepared, rank, brightest].map(surface => new Float32Array(surface.data))
  const kernel = bindCanonicalKernel(factory, {
    width: definition.width, height, time: f(0.375), frame: 24, deltaTime: f(1 / 60), seed: f(43),
    uniforms: {}, textures: { preparedTex: prepared, rankTex: rank, brightestTex: brightest },
  })
  const output = new Surface(definition.width, height)
  runPass({ kernel, destination: output, time: f(0.375), seed: f(43) })
  for (let i = 0; i < originals.length; i += 1) if (!sameBytes([prepared, rank, brightest][i].data, originals[i])) throw new Error(`${definition.name}: input ${i} mutated`)
  return { prepared, rank, brightest, output }
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

function caseResult(definition, surfaces) {
  const first = render(canonical, definition)
  const second = render(canonical, definition)
  for (const name of ['prepared', 'rank', 'brightest', 'output']) if (!sameBytes(first[name].data, second[name].data)) throw new Error(`${definition.name}: repeat mismatch ${name}`)
  surfaces.set(definition.name, first.output)
  return {
    name: definition.name, dimensions: { width: definition.width, height: definition.brightest.length }, coverage: definition.coverage,
    brightest_rows: definition.brightest.map(scalar),
    inputs: {
      prepared_f32_sha256: sha256(bytes(first.prepared.data)), rank_f32_sha256: sha256(bytes(first.rank.data)), brightest_f32_sha256: sha256(bytes(first.brightest.data)),
      prepared_probes: probes(first.prepared), rank_probes: probes(first.rank), brightest_probes: probes(first.brightest),
    },
    output: outputRecord(first.output), repeat_identity: true, all_inputs_immutable: true,
  }
}

function mutationResults(name, factory, definitions, surfaces) {
  return { name, case_results: definitions.map(definition => ({ case: definition.name, ...diff(surfaces.get(definition.name), render(factory, definition).output) })) }
}

function requireDivergence(mutation, names) { for (const name of names) if (mutation.case_results.find(x => x.case === name)?.same_f32_bytes !== false) throw new Error(`${mutation.name}: missing divergence ${name}`) }
function requireIdentity(mutation, names) { for (const name of names) { const x = mutation.case_results.find(x => x.case === name); if (!x?.same_f32_bytes || !x.same_rgba8_bytes) throw new Error(`${mutation.name}: missing identity ${name}`) } }

function buildData() {
  const normativeSurfaces = new Map(), exclusionSurfaces = new Map()
  const normativeCases = cases.map(definition => caseResult(definition, normativeSurfaces))
  const exclusions = exclusionCases.map(definition => caseResult(definition, exclusionSurfaces))
  if (!sameBytes(normativeSurfaces.get('normalized-positive-zero').data, normativeSurfaces.get('normalized-negative-zero-control').data)) throw new Error('positive/negative zero outputs differ')

  const floorMutation = mutationResults('round-replaced-by-floor', factories.floor, cases, normativeSurfaces)
  requireDivergence(floorMutation, ['normalized-half-boundaries', 'normalized-wide-67'])
  const ceilMutation = mutationResults('round-replaced-by-ceil', factories.ceil, cases, normativeSurfaces)
  requireDivergence(ceilMutation, ['normalized-half-boundaries'])
  const loopMutation = mutationResults('sample-loop-64-to-8', factories.loop8, cases, normativeSurfaces)
  requireDivergence(loopMutation, ['normalized-wide-67'])
  const nativeMutation = mutationResults('native-floor-plus-half-with-int32-clamp', factories.native_floor_half_clamp, cases, normativeSurfaces)
  requireIdentity(nativeMutation, cases.map(x => x.name))

  const negativeNative = mutationResults('negative-half-native-floor-plus-half-control', factories.native_floor_half_clamp, [exclusionCases[0]], exclusionSurfaces)
  requireIdentity(negativeNative, [exclusionCases[0].name])
  const stdRound = mutationResults('negative-half-std-round-away-from-zero-control', factories.std_round_away, [exclusionCases[0]], exclusionSurfaces)
  requireDivergence(stdRound, [exclusionCases[0].name])
  const outOfRangeNative = mutationResults('out-of-range-native-int32-clamp-control', factories.native_floor_half_clamp, [exclusionCases[1]], exclusionSurfaces)
  requireDivergence(outOfRangeNative, [exclusionCases[1].name])

  return {
    schema: 'noisemaker-for-cpp.task24-gather-sorted-round-to-int.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, public_api: 'kernelFactories.get(key)', canonical_identity: true, adapter_entry_absent: true, canonical_kernels_sha256: canonicalSha256 },
    program: {
      key, source: sourceRelative, raw_source_bytes: 1896, raw_source_sha256: 'a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386', normalized_source_bytes: 1185, normalized_source_sha256: '28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9', defines: {},
      profile: 'gather-sorted-round-to-int-v1', unrestricted_round_capability: false, canonical_factory_name: factoryName, canonical_factory_to_string_sha256: factorySha256,
      bindings: ['preparedTex:sampler2D@1/S1', 'rankTex:sampler2D@2/S2', 'brightestTex:sampler2D@3/S3'], output: 'fragColor:vec4@4',
      resources: { samplers: 3, outputs: 1, uses_texture: true, uses_derivatives: false, static_texelFetch_sites: 3, dynamic_texelFetch_per_pixel: 66, textureSize_calls_per_pixel: 1 },
      loop: { count: 1, bound_kind: 'local-const-literal', bound: 64, trip_count: 64, lexical_depth: 1, effective_depth: 1, lexical_product: 64, entrypoint_charge: 64, call_graph_acyclic: true },
    },
    fixture: { prepared: 'top-down F32 deterministic RGBA modular field', rank: 'top-down F32 deterministic per-row rank permutation', brightest: '1xheight F32 R values with other color lanes zero and alpha one', fragment_origin: 'bottom-left runPass coordinates', verification: 'fresh double render, immutable three inputs, finite full output, F32/RGBA8 hashes and probes' },
    normative_domain: 'brightestTex.r is normalized to [0,1] and dimensions fit signed int32; negative zero is an explicit sign-erasure control',
    cases: normativeCases,
    cross_case_controls: [{ name: 'positive-vs-negative-zero-erased-by-immediate-int', same_f32_bytes: true, same_rgba8_bytes: true }],
    mutations: [floorMutation, ceilMutation, loopMutation, nativeMutation],
    exclusions: {
      contract: 'not native parity acceptance cases; these freeze why the exact profile cannot authorize generic round or out-of-range conversion',
      cases: exclusions,
      controls: [negativeNative, stdRound, outOfRangeNative],
    },
  }
}

function buildReport(data) {
  const lines = ['# Task 24 Gather Sorted public-canonical oracle report', '', `Normative cases: **${data.cases.length}**  `, `Normative mutations: **${data.mutations.length}**  `, `Exclusion controls: **${data.exclusions.controls.length}**`, '', 'Public dispatch is the exact canonical factory and has no adapter. Every normative and exclusion case repeats byte-identically with immutable inputs and finite output.', '', '## Normative cases', '', '| Case | Size | Brightest rows | Output F32 SHA-256 | Output RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- |']
  for (const c of data.cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.brightest_rows.map(x => `${x.value}${x.negative_zero ? '(-0)' : ''}`).join(', ')} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Normative mutation sensitivity', '', '| Mutation | Maximum changed F32 lanes | Maximum changed RGBA8 bytes |', '| --- | ---: | ---: |')
  for (const m of data.mutations) lines.push(`| ${m.name} | ${Math.max(...m.case_results.map(x => x.different_f32_lanes))} | ${Math.max(...m.case_results.map(x => x.different_rgba8_bytes))} |`)
  lines.push('', '## Exclusion controls', '', '| Case | Purpose | Output F32 SHA-256 |', '| --- | --- | --- |')
  for (const c of data.exclusions.cases) lines.push(`| ${c.name} | ${c.coverage.join(', ')} | \`${c.output.f32_sha256}\` |`)
  lines.push('', '| Control mutation | Case | Same F32 | Changed F32 lanes | Changed RGBA8 bytes |', '| --- | --- | --- | ---: | ---: |')
  for (const m of data.exclusions.controls) for (const c of m.case_results) lines.push(`| ${m.name} | ${c.case} | ${c.same_f32_bytes} | ${c.different_f32_lanes} | ${c.different_rgba8_bytes} |`)
  lines.push('', 'The negative-half control proves immediate integer consumption erases JavaScript negative zero; an away-from-zero `std::round` model diverges. The out-of-range control proves JavaScript `|0` wrapping diverges from the native int32 clamp. Neither exclusion expands the normalized bounded native parity contract.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') { fs.writeFileSync(jsonPath, json); fs.writeFileSync(reportPath, report); process.stdout.write('wrote task-24-oracles.json and task-24-oracle-report.md\n') }
else if (process.argv.length === 3 && process.argv[2] === '--check') { if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error('task-24-oracles.json drift'); if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('task-24-oracle-report.md drift'); process.stdout.write('ok task-24-oracles.json and task-24-oracle-report.md\n') }
else throw new Error('usage: node task-24-oracle-generator.mjs [--write|--check]')
