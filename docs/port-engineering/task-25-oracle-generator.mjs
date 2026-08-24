import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-25-oracles.json')
const reportPath = path.join(here, 'task-25-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const catalogPath = path.join(cpuRoot, 'src/effects/catalog.js')
const adapterIndexPath = path.join(cpuRoot, 'src/effects/adapters/index.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const catalogSha256 = 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'
const adapterIndexSha256 = '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }

if (sha256(fs.readFileSync(canonicalPath)) !== canonicalSha256) throw new Error('pinned canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== catalogSha256) throw new Error('pinned public catalog drift')
if (sha256(fs.readFileSync(adapterIndexPath)) !== adapterIndexSha256) throw new Error('pinned adapter index drift')

const programs = {
  lens: {
    key: 'classicNoisedeck/lensDistortion:lensDistortion',
    source: 'sources/classicNoisedeck/lensDistortion/lensDistortion.glsl',
    rawBytes: 8269,
    rawSha256: 'f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444',
    normalizedBytes: 7723,
    normalizedSha256: '6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52',
    factoryName: 'canonicalFactory10',
    factorySha256: '151b1e868c7d2f9a446a8778d170260e5003fec540afb2623088bbf34ca8adcf',
    bindings: [
      'inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'fullResolution:vec2@4', 'time:float@5',
      'aspectLens:bool@6', 'shape:int@7', 'tint:vec3@8', 'alpha:float@9', 'vignetteAmt:float@10', 'distortion:float@11',
      'speed:float@12', 'loopScale:float@13', 'aberration:float@14', 'hueRotation:float@15', 'hueRange:float@16', 'mode:int@17',
      'modulate:bool@18', 'blendMode:int@19', 'saturation:float@20', 'passthru:float@21', 'fragColor:vec4@22/out',
    ],
  },
  prism: {
    key: 'filter/prismaticAberration:prismaticAberration',
    source: 'sources/filter/prismaticAberration/prismaticAberration.glsl',
    rawBytes: 4247,
    rawSha256: '513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e',
    normalizedBytes: 3907,
    normalizedSha256: '1c157e7f3dc7c9c122cc185812cd2988a98a52024055a482265bded7561a0860',
    factoryName: 'canonicalFactory117',
    factorySha256: '2eab8943387658c1c28f4e089edd9b248bf441b2b77145ea137c7f979c5def02',
    bindings: [
      'inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'fullResolution:vec2@4', 'time:float@5',
      'aberrationAmt:float@6', 'hueRotation:float@7', 'hueRange:float@8', 'modulate:bool@9', 'saturation:float@10',
      'passthru:float@11', 'fragColor:vec4@12/out',
    ],
  },
}

for (const program of Object.values(programs)) {
  const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, program.source)
  const source = fs.readFileSync(sourcePath)
  if (source.byteLength !== program.rawBytes || sha256(source) !== program.rawSha256) throw new Error(`${program.key}: pinned source drift`)
  program.canonical = canonicalKernelFactories[program.key]
  program.publicFactory = kernelFactories.get(program.key)
  if (program.canonical?.name !== program.factoryName || sha256(Buffer.from(program.canonical.toString())) !== program.factorySha256) throw new Error(`${program.key}: canonical factory drift`)
  if (program.publicFactory !== program.canonical || canonicalAdapterFactories[program.key] !== undefined) throw new Error(`${program.key}: public factory is not direct canonical identity`)
  program.factoryText = program.canonical.toString()
}

const lensChromaticLine = '\thsv[0] = fract(hsv[0] + (1 - (hueRotation / 360)) + (hsv[0] * hueRange) * 0.009999999776482582 + t);'
const lensPrismaticLine = '\thsv[0] = fract(((hsv[0] + 0.125 + (1 - (hueRotation / 360))) * (2 + hueRange * 0.05000000074505806)) + t);'
const saturationLine = '\thsv[1] = 1;'
const lensBlendLine = '\tcolor = [0, 1, 2, null].map(function (idx, i) { return idx == null ? color[i] : this[idx]; }, min(vec3.add([], max(new $runtime.PooledFloat32Array([green[0] - hsv[2], green[1] - hsv[2], green[2] - hsv[2]]), 0), hsv2rgb(hsv)), 1));'

function occurrences(text, needle) { return text.split(needle).length - 1 }
function replaceNth(text, from, to, ordinal) {
  if (ordinal < 1 || occurrences(text, from) < ordinal) throw new Error(`missing occurrence ${ordinal}: ${from}`)
  let seen = 0
  return text.replaceAll(from, match => { seen += 1; return seen === ordinal ? to : match })
}
function mutate(program, from, to, ordinal = 1) {
  const text = replaceNth(program.factoryText, from, to, ordinal)
  if (text === program.factoryText) throw new Error('mutation made no change')
  return (0, eval)(`(${text})`)
}

if (occurrences(programs.lens.factoryText, lensChromaticLine) !== 1 || occurrences(programs.lens.factoryText, lensPrismaticLine) !== 1 || occurrences(programs.lens.factoryText, saturationLine) !== 2 || occurrences(programs.lens.factoryText, lensBlendLine) !== 1) throw new Error('Lens main-site factory shape drift')
if (occurrences(programs.prism.factoryText, lensPrismaticLine) !== 1 || occurrences(programs.prism.factoryText, saturationLine) !== 1) throw new Error('Prismatic main-site factory shape drift')

const mutations = [
  {
    id: 'lens-236-write-lane0-to-lane1', program: 'lens', sourceSpan: '236:9-236:15', role: 'direct-= lvalue', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.lens, lensChromaticLine, '\thsv[1] = fract(hsv[0] + (1 - (hueRotation / 360)) + (hsv[0] * hueRange) * 0.009999999776482582 + t);'),
  },
  {
    id: 'lens-236-first-read-lane0-to-lane1', program: 'lens', sourceSpan: '236:24-236:30', role: 'RHS read', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.lens, lensChromaticLine, '\thsv[0] = fract(hsv[1] + (1 - (hueRotation / 360)) + (hsv[0] * hueRange) * 0.009999999776482582 + t);'),
  },
  {
    id: 'lens-236-second-read-lane0-to-lane2', program: 'lens', sourceSpan: '236:65-236:71', role: 'RHS read', sourceLane: 0, wrongLane: 2,
    factory: mutate(programs.lens, lensChromaticLine, '\thsv[0] = fract(hsv[0] + (1 - (hueRotation / 360)) + (hsv[2] * hueRange) * 0.009999999776482582 + t);'),
  },
  {
    id: 'lens-237-write-lane1-to-lane2', program: 'lens', sourceSpan: '237:9-237:15', role: 'direct-= lvalue', sourceLane: 1, wrongLane: 2,
    factory: mutate(programs.lens, saturationLine, '\thsv[2] = 1;', 1),
  },
  {
    id: 'lens-247-write-lane0-to-lane1', program: 'lens', sourceSpan: '247:9-247:15', role: 'direct-= lvalue', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.lens, lensPrismaticLine, '\thsv[1] = fract(((hsv[0] + 0.125 + (1 - (hueRotation / 360))) * (2 + hueRange * 0.05000000074505806)) + t);'),
  },
  {
    id: 'lens-247-read-lane0-to-lane1', program: 'lens', sourceSpan: '247:26-247:32', role: 'RHS read', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.lens, lensPrismaticLine, '\thsv[0] = fract(((hsv[1] + 0.125 + (1 - (hueRotation / 360))) * (2 + hueRange * 0.05000000074505806)) + t);'),
  },
  {
    id: 'lens-248-write-lane1-to-lane2', program: 'lens', sourceSpan: '248:9-248:15', role: 'direct-= lvalue', sourceLane: 1, wrongLane: 2,
    factory: mutate(programs.lens, saturationLine, '\thsv[2] = 1;', 2),
  },
  {
    id: 'lens-260-read-splat-lane2-to-lane1', program: 'lens', sourceSpan: '260:46-260:52', role: 'sole vec3 splat-input read', sourceLane: 2, wrongLane: 1,
    factory: mutate(programs.lens, lensBlendLine, lensBlendLine.replaceAll('hsv[2]', 'hsv[1]')),
    generatedOccurrences: 3,
  },
  {
    id: 'prism-131-write-lane0-to-lane1', program: 'prism', sourceSpan: '131:5-131:11', role: 'direct-= lvalue', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.prism, lensPrismaticLine, '\thsv[1] = fract(((hsv[0] + 0.125 + (1 - (hueRotation / 360))) * (2 + hueRange * 0.05000000074505806)) + t);'),
  },
  {
    id: 'prism-131-read-lane0-to-lane1', program: 'prism', sourceSpan: '131:22-131:28', role: 'RHS read', sourceLane: 0, wrongLane: 1,
    factory: mutate(programs.prism, lensPrismaticLine, '\thsv[0] = fract(((hsv[1] + 0.125 + (1 - (hueRotation / 360))) * (2 + hueRange * 0.05000000074505806)) + t);'),
  },
  {
    id: 'prism-132-write-lane1-to-lane2', program: 'prism', sourceSpan: '132:5-132:11', role: 'direct-= lvalue', sourceLane: 1, wrongLane: 2,
    factory: mutate(programs.prism, saturationLine, '\thsv[2] = 1;'),
  },
]

function inputSurface(width, height, phase) {
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

const cases = [
  {
    name: 'lens-chromatic-add-static', program: 'lens', width: 11, height: 7, phase: 1, time: f(0.1875),
    uniforms: { aspectLens: false, shape: 3, tint: new Float32Array([f(0.17), f(0.41), f(0.73)]), alpha: f(23), vignetteAmt: f(-34), distortion: f(-47), speed: f(31), loopScale: f(67), aberration: f(72), hueRotation: f(47), hueRange: f(83), mode: 0, modulate: false, blendMode: 0, saturation: f(19), passthru: f(61) },
    coverage: ['Lens mode=0 chromatic branch', 'blendMode=0 add branch', 'static t=0', 'source sites 236W/236R1/236R2/237W'],
  },
  {
    name: 'lens-chromatic-alpha-modulated', program: 'lens', width: 10, height: 8, phase: 2, time: f(0.4375),
    uniforms: { aspectLens: true, shape: 7, tint: new Float32Array([f(0.79), f(0.13), f(0.37)]), alpha: f(57), vignetteAmt: f(41), distortion: f(64), speed: f(-28), loopScale: f(43), aberration: f(91), hueRotation: f(213), hueRange: f(46), mode: 0, modulate: true, blendMode: 1, saturation: f(-27), passthru: f(36) },
    coverage: ['Lens mode=0 chromatic branch', 'blendMode=1 alpha branch', 'modulated t=time', 'source lane-2 splat site 260R'],
  },
  {
    name: 'lens-prismatic-add-static', program: 'lens', width: 9, height: 9, phase: 3, time: f(0.28125),
    uniforms: { aspectLens: true, shape: 1, tint: new Float32Array([f(0.31), f(0.67), f(0.11)]), alpha: f(38), vignetteAmt: f(-63), distortion: f(-81), speed: f(54), loopScale: f(79), aberration: f(63), hueRotation: f(129), hueRange: f(71), mode: 1, modulate: false, blendMode: 0, saturation: f(44), passthru: f(74) },
    coverage: ['Lens mode=1 prismatic branch', 'blendMode=0 add branch', 'static t=0', 'source sites 247W/247R/248W'],
  },
  {
    name: 'lens-prismatic-alpha-modulated', program: 'lens', width: 12, height: 6, phase: 4, time: f(0.59375),
    uniforms: { aspectLens: false, shape: 9, tint: new Float32Array([f(0.23), f(0.89), f(0.53)]), alpha: f(69), vignetteAmt: f(58), distortion: f(76), speed: f(-61), loopScale: f(28), aberration: f(84), hueRotation: f(301), hueRange: f(58), mode: 1, modulate: true, blendMode: 1, saturation: f(-52), passthru: f(47) },
    coverage: ['Lens mode=1 prismatic branch', 'blendMode=1 alpha branch', 'modulated t=time', 'source lane-2 splat site 260R'],
  },
  {
    name: 'prism-static-origin-tile', program: 'prism', width: 10, height: 7, phase: 5, time: f(0.34375), tileOffset: new Float32Array([0, 0]), fullResolution: new Float32Array([10, 7]),
    uniforms: { aberrationAmt: f(77), hueRotation: f(73), hueRange: f(86), modulate: false, saturation: f(29), passthru: f(68) },
    coverage: ['Prismatic static t=0', 'origin tile', 'source sites 131W/131R/132W', 'textureSize path'],
  },
  {
    name: 'prism-modulated-offset-tile', program: 'prism', width: 9, height: 6, phase: 6, time: f(0.65625), tileOffset: new Float32Array([4, 3]), fullResolution: new Float32Array([17, 13]),
    uniforms: { aberrationAmt: f(93), hueRotation: f(247), hueRange: f(63), modulate: true, saturation: f(-41), passthru: f(39) },
    coverage: ['Prismatic modulated t=time', 'nonzero asymmetric tile offset/full resolution', 'source sites 131W/131R/132W', 'textureSize path'],
  },
]

function render(factory, definition) {
  const input = inputSurface(definition.width, definition.height, definition.phase)
  const original = new Float32Array(input.data)
  const kernel = bindCanonicalKernel(factory, {
    width: definition.width, height: definition.height, time: definition.time, frame: 37, deltaTime: f(1 / 60), seed: f(43),
    uniforms: definition.uniforms, textures: { inputTex: input }, tileOffset: definition.tileOffset, fullResolution: definition.fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output, time: definition.time, seed: f(43) })
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
    const first = render(programs[definition.program].canonical, definition)
    const second = render(programs[definition.program].canonical, definition)
    if (!sameBytes(first.input.data, second.input.data) || !sameBytes(first.output.data, second.output.data)) throw new Error(`${definition.name}: repeat mismatch`)
    reference.set(definition.name, first.output)
    return {
      name: definition.name, program: programs[definition.program].key, dimensions: { width: definition.width, height: definition.height },
      tile_offset: Array.from(definition.tileOffset ?? new Float32Array(2)), full_resolution: Array.from(definition.fullResolution ?? new Float32Array([definition.width, definition.height])),
      time: definition.time, uniforms: Object.fromEntries(Object.entries(definition.uniforms).map(([k, v]) => [k, ArrayBuffer.isView(v) ? Array.from(v) : v])), coverage: definition.coverage,
      input: { f32_sha256: sha256(bytes(first.input.data)), probes: probes(first.input) }, output: outputRecord(first.output), repeat_identity: true, input_immutable: true,
    }
  })

  const mutationResults = mutations.map(mutation => {
    const activeCases = cases.filter(c => c.program === mutation.program)
    const results = activeCases.map(definition => ({ case: definition.name, ...diff(reference.get(definition.name), render(mutation.factory, definition).output) }))
    if (!results.some(result => !result.same_f32_bytes)) throw new Error(`${mutation.id}: no F32 divergence in active cases`)
    return { id: mutation.id, program: programs[mutation.program].key, source_span: mutation.sourceSpan, role: mutation.role, source_lane: mutation.sourceLane, wrong_lane: mutation.wrongLane, generated_occurrences_for_one_source_site: mutation.generatedOccurrences ?? 1, case_results: results }
  })

  return {
    schema: 'noisemaker-for-cpp.task25.literal-vec3-lane-index.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, public_api: 'kernelFactories.get(key)', canonical_identity: true, adapter_entries_absent: true, canonical_kernels_sha256: canonicalSha256, public_catalog_sha256: catalogSha256, adapter_index_sha256: adapterIndexSha256 },
    profile: { name: 'literal-vec3-lane-index-v1', keys: Object.values(programs).map(p => p.key).sort(), selected_source_sites: 11, direct_plain_assignment_lvalues: 6, reads: 5, lane_incidence_0_1_2: [7, 3, 1], dynamic_or_generic_vector_index_capability: false },
    programs: Object.fromEntries(Object.entries(programs).map(([name, p]) => [name, { key: p.key, source: p.source, raw_source_bytes: p.rawBytes, raw_source_sha256: p.rawSha256, normalized_source_bytes: p.normalizedBytes, normalized_source_sha256: p.normalizedSha256, defines: {}, canonical_factory_name: p.factoryName, canonical_factory_to_string_sha256: p.factorySha256, public_factory_is_canonical_identity: true, adapter_entry_absent: true, bindings: p.bindings, resources: name === 'lens' ? { samplers: 1, ordinary_uniforms: 20, outputs: 1, uses_texture: true, uses_derivatives: false, static_texture_sites: 3, dynamic_texture_calls_per_pixel: 3, texture_size_calls_per_pixel: 0 } : { samplers: 1, ordinary_uniforms: 10, outputs: 1, uses_texture: true, uses_derivatives: false, static_texture_sites: 3, dynamic_texture_calls_per_pixel: 3, texture_size_calls_per_pixel: 1 } }])),
    fixture: { input: 'top-down asymmetric deterministic F32 RGBA modular field', fragment_origin: 'bottom-left runPass coordinates', tiled_prismatic_case: true, verification: 'fresh double render, immutable input, finite full output, F32/RGBA8 hashes and five probes' },
    cases: caseResults,
    mutations: mutationResults,
  }
}

function buildReport(data) {
  const lines = [
    '# Task 25 literal vec3 lane public-canonical oracle report', '',
    `Cases: **${data.cases.length}**  `, `Authenticated source sites: **${data.profile.selected_source_sites}**  `, `One-site wrong-lane mutations: **${data.mutations.length}**`, '',
    'Both public dispatch entries are the exact canonical factory objects and have no adapters. Every case repeats byte-identically, preserves its input, produces only finite lanes, and records full F32/RGBA8 hashes plus five probes.', '',
    '## Cases', '', '| Case | Program | Size | Tile / full | Output F32 SHA-256 | Output RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |',
  ]
  for (const c of data.cases) lines.push(`| ${c.name} | ${c.program} | ${c.dimensions.width}x${c.dimensions.height} | ${c.tile_offset.join(',')} / ${c.full_resolution.join(',')} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Exact-site mutation sensitivity', '', '| Mutation | Span / role | Source lane -> wrong lane | Divergent active cases | Max changed F32 lanes | Max changed RGBA8 bytes |', '| --- | --- | --- | ---: | ---: | ---: |')
  for (const m of data.mutations) lines.push(`| ${m.id} | ${m.source_span} / ${m.role} | ${m.source_lane} -> ${m.wrong_lane} | ${m.case_results.filter(x => !x.same_f32_bytes).length}/${m.case_results.length} | ${Math.max(...m.case_results.map(x => x.different_f32_lanes))} | ${Math.max(...m.case_results.map(x => x.different_rgba8_bytes))} |`)
  lines.push('', 'Each mutation changes exactly one authenticated source index role. The Lens line-260 scalar splat is one source read even though the canonical JavaScript factory expands it to three `hsv[2]` reads; its mutation changes those three generated occurrences together. These controls do not authorize generic or dynamic vector indexing.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') { fs.writeFileSync(jsonPath, json); fs.writeFileSync(reportPath, report); process.stdout.write('wrote task-25-oracles.json and task-25-oracle-report.md\n') }
else if (process.argv.length === 3 && process.argv[2] === '--check') { if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error('task-25-oracles.json drift'); if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error('task-25-oracle-report.md drift'); process.stdout.write('ok task-25-oracles.json and task-25-oracle-report.md\n') }
else throw new Error('usage: node task-25-oracle-generator.mjs [--write|--check]')
