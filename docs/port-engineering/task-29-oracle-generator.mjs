import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'task-29-oracles.json')
const key = 'mixer/focusBlur:focusBlur'
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = `tools/glslcpp/corpus/${revision}/sources/mixer/focusBlur/focusBlur.glsl`
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function sameBytes(a, b) { return Buffer.compare(bytes(a.data), bytes(b.data)) === 0 }

const provenance = {
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
  source_sha256: 'dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1',
  canonical_factory_name: 'canonicalFactory195',
  canonical_factory_to_string_sha256: 'fb4c02c763ef42000b13bba3945cf4fd15e177a2ab2827372ce3b96aa3a778ff',
}

if (sha256(fs.readFileSync(canonicalPath)) !== provenance.canonical_kernels_sha256) throw new Error('canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== provenance.public_catalog_sha256) throw new Error('catalog drift')
if (sha256(fs.readFileSync(adapterPath)) !== provenance.adapter_index_sha256) throw new Error('adapter registry drift')
if (sha256(fs.readFileSync(sourcePath)) !== provenance.source_sha256) throw new Error('source drift')
const canonical = canonicalKernelFactories[key]
if (canonical?.name !== provenance.canonical_factory_name || sha256(canonical.toString()) !== provenance.canonical_factory_to_string_sha256) throw new Error('factory drift')
if (kernelFactories.get(key) !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    data[i] = f((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
    data[i + 1] = f((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
    data[i + 2] = f((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
    data[i + 3] = f((((7 * x + 11 * y + phase) % 29) + (phase ? 2 : 13)) / 43)
  }
  return new Surface(width, height, data)
}

const cases = [
  { name: 'depth-a-default', width: 6, height: 5, phaseA: 0, phaseB: 1, uniforms: { focalDistance: f(50), aperture: f(4), sampleBias: f(12), depthSource: 0 }, coverage: ['scene=B depth=A', 'default numeric controls', 'asymmetric alpha'] },
  { name: 'depth-b-default', width: 6, height: 5, phaseA: 0, phaseB: 1, uniforms: { focalDistance: f(50), aperture: f(4), sampleBias: f(12), depthSource: 1 }, coverage: ['scene=A depth=B', 'reversed borrowed arguments'] },
  { name: 'metadata-minima', width: 7, height: 4, phaseA: 2, phaseB: 3, uniforms: { focalDistance: f(1), aperture: f(1), sampleBias: f(2), depthSource: 0 }, coverage: ['metadata minima', 'landscape'] },
  { name: 'metadata-maxima', width: 5, height: 7, phaseA: 4, phaseB: 5, uniforms: { focalDistance: f(100), aperture: f(10), sampleBias: f(64), depthSource: 1 }, coverage: ['metadata maxima', 'portrait', 'large clamped offsets'] },
  { name: 'borrowed-alias-same-surface', width: 5, height: 4, phaseA: 6, phaseB: 6, alias: true, uniforms: { focalDistance: f(35), aperture: f(3), sampleBias: f(9), depthSource: 0 }, coverage: ['same Surface aliases both const references', 'no ownership transfer'] },
  { name: 'tiled-global-coordinate', width: 4, height: 6, phaseA: 7, phaseB: 8, tileOffset: new Float32Array([5, 3]), fullResolution: new Float32Array([13, 11]), uniforms: { focalDistance: f(72), aperture: f(6), sampleBias: f(21), depthSource: 0 }, coverage: ['nonzero tile offset', 'larger full resolution', 'scene uv differs from depth uv'] },
]

function render(definition) {
  const inputTex = patternedSurface(definition.width, definition.height, definition.phaseA)
  const tex = definition.alias ? inputTex : patternedSurface(definition.width, definition.height, definition.phaseB)
  const kernel = bindCanonicalKernel(canonical, {
    width: definition.width, height: definition.height,
    uniforms: definition.uniforms, textures: { inputTex, tex },
    tileOffset: definition.tileOffset, fullResolution: definition.fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output })
  return output
}

function probe(surface, x, y) {
  const i = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(i, i + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}

function result(surface) {
  const rgba = surface.toRgba8()
  let nonfinite = 0
  for (const lane of surface.data) if (!Number.isFinite(lane)) nonfinite += 1
  return {
    f32_sha256: sha256(bytes(surface.data)), rgba8_sha256: sha256(bytes(rgba)),
    finite_lanes: surface.data.length - nonfinite, nonfinite_lanes: nonfinite,
    probes: [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]].map(([x, y]) => probe(surface, x, y)),
  }
}

function trackedLane(surface, index, role, counters) {
  counters[`${role}_lane_reads`] += 1
  return surface.data[index]
}

function directMix(scene, depth, counters) {
  counters.mix_calls += 1
  const sceneIndex = 0
  const depthIndex = (depth.width * depth.height - 1) * 4
  const a = f(trackedLane(scene, sceneIndex, 'scene', counters) + f(trackedLane(depth, depthIndex + 1, 'depth', counters) * f(2)))
  const b = f(a + f(trackedLane(scene, sceneIndex + 3, 'scene', counters) * f(4)))
  return f(b + f(trackedLane(depth, depthIndex + 3, 'depth', counters) * f(8)))
}

const directDefinitions = [
  { id: 0, name: 'exact-depth-a-const-refs', phaseA: 0, phaseB: 1, accepted: true, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'const Surface&', scene_source: 'tex', depth_source: 'inputTex' } },
  { id: 1, name: 'exact-depth-b-const-refs', phaseA: 0, phaseB: 1, accepted: true, declared: { branch_slot: 'depthSource!=0/else', abi_spelling: 'const Surface&', scene_source: 'inputTex', depth_source: 'tex' } },
  { id: 2, name: 'exact-alias-const-refs', phaseA: 6, phaseB: 6, accepted: true, alias: true, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'const Surface&', scene_source: 'inputTex', depth_source: 'inputTex' } },
  { id: 3, name: 'owning-value-copies', phaseA: 0, phaseB: 1, accepted: false, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'Surface', scene_source: 'tex', depth_source: 'inputTex' } },
  { id: 4, name: 'mutable-references', phaseA: 0, phaseB: 1, accepted: false, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'Surface&', scene_source: 'tex', depth_source: 'inputTex' } },
  { id: 5, name: 'nullable-pointers-nonnull', phaseA: 0, phaseB: 1, accepted: false, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'const Surface*', scene_source: 'tex', depth_source: 'inputTex' } },
  { id: 6, name: 'wrong-order-depth-a-const-refs', phaseA: 0, phaseB: 1, accepted: false, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'const Surface&', scene_source: 'inputTex', depth_source: 'tex' } },
  { id: 7, name: 'nullable-pointer-null-depth', phaseA: 0, phaseB: 1, accepted: false, declared: { branch_slot: 'depthSource==0/then', abi_spelling: 'const Surface*', scene_source: 'tex', depth_source: null } },
]

const handledDirectModeIds = new Set()

function freshCounters() {
  return {
    mode_dispatches: 0, const_ref_bindings: 0, value_copy_bindings: 0,
    mutable_ref_bindings: 0, nullable_pointer_bindings: 0,
    pointer_null_checks: 0, pointer_dereferences: 0,
    surface_copy_allocations: 0, copied_f32_lanes: 0,
    writable_probes: 0, scene_lane_reads: 0, depth_lane_reads: 0,
    mix_calls: 0,
  }
}

function surfaceCopy(source, ownedCopies, sourceNames, counters) {
  const copy = new Surface(source.width, source.height, new Float32Array(source.data))
  ownedCopies.add(copy)
  sourceNames.set(copy, sourceNames.get(source))
  counters.surface_copy_allocations += 1
  counters.copied_f32_lanes += copy.data.length
  return copy
}

function markHandled(id, counters) {
  if (handledDirectModeIds.has(id)) throw new Error(`direct ABI mode ${id} executed twice`)
  handledDirectModeIds.add(id)
  counters.mode_dispatches += 1
}

function executeDirectMode(definition, inputTex, tex, ownedCopies, sourceNames, counters) {
  switch (definition.id) {
    case 0:
      markHandled(0, counters)
      counters.const_ref_bindings += 2
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'const Surface&', scene: tex, depth: inputTex }
    case 1:
      markHandled(1, counters)
      counters.const_ref_bindings += 2
      return { branchSlot: 'depthSource!=0/else', abiSpelling: 'const Surface&', scene: inputTex, depth: tex }
    case 2:
      markHandled(2, counters)
      counters.const_ref_bindings += 2
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'const Surface&', scene: inputTex, depth: inputTex }
    case 3: {
      markHandled(3, counters)
      counters.value_copy_bindings += 2
      const scene = surfaceCopy(tex, ownedCopies, sourceNames, counters)
      const depth = surfaceCopy(inputTex, ownedCopies, sourceNames, counters)
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'Surface', scene, depth }
    }
    case 4:
      markHandled(4, counters)
      counters.mutable_ref_bindings += 2
      tex.data[0] = f(tex.data[0])
      counters.writable_probes += 1
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'Surface&', scene: tex, depth: inputTex }
    case 5: {
      markHandled(5, counters)
      counters.nullable_pointer_bindings += 2
      const scenePointer = { pointee: tex }, depthPointer = { pointee: inputTex }
      counters.pointer_null_checks += 2
      if (scenePointer.pointee === null || depthPointer.pointee === null) throw new Error('nonnull pointer mode unexpectedly null')
      counters.pointer_dereferences += 2
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'const Surface*', scene: scenePointer.pointee, depth: depthPointer.pointee }
    }
    case 6:
      markHandled(6, counters)
      counters.const_ref_bindings += 2
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'const Surface&', scene: inputTex, depth: tex }
    case 7: {
      markHandled(7, counters)
      counters.nullable_pointer_bindings += 2
      const scenePointer = { pointee: tex }, depthPointer = { pointee: null }
      counters.pointer_null_checks += 2
      if (scenePointer.pointee === null) throw new Error('scene pointer unexpectedly null')
      counters.pointer_dereferences += 1
      return { branchSlot: 'depthSource==0/then', abiSpelling: 'const Surface*', scene: scenePointer.pointee, depth: depthPointer.pointee }
    }
  }
  throw new Error(`invalid direct ABI mode ${definition.id}`)
}

function directRecord(definition) {
  const inputTex = patternedSurface(4, 3, definition.phaseA)
  const tex = definition.alias ? inputTex : patternedSurface(4, 3, definition.phaseB)
  const ownedCopies = new Set()
  const sourceNames = new Map([[inputTex, 'inputTex']])
  if (tex !== inputTex) sourceNames.set(tex, 'tex')
  const counters = freshCounters()
  const execution = executeDirectMode(definition, inputTex, tex, ownedCopies, sourceNames, counters)
  const { scene, depth } = execution
  const value = depth === null ? f(-1) : directMix(scene, depth, counters)
  const observed = {
    branch_slot: execution.branchSlot,
    abi_spelling: execution.abiSpelling,
    scene_source: sourceNames.get(scene),
    depth_source: depth === null ? null : sourceNames.get(depth),
    scene_aliases_input: scene === inputTex,
    scene_aliases_tex: scene === tex,
    depth_aliases_input: depth === inputTex,
    depth_aliases_tex: depth === tex,
    scene_depth_alias: scene === depth,
    scene_owned_copy: ownedCopies.has(scene),
    depth_owned_copy: ownedCopies.has(depth),
    owned_copy_count: ownedCopies.size,
    null_taken: depth === null,
    counters,
  }
  const structuralSignature = {
    branch_slot: observed.branch_slot, abi_spelling: observed.abi_spelling,
    scene_source: observed.scene_source, depth_source: observed.depth_source,
    scene_aliases_input: observed.scene_aliases_input,
    scene_aliases_tex: observed.scene_aliases_tex,
    depth_aliases_input: observed.depth_aliases_input,
    depth_aliases_tex: observed.depth_aliases_tex,
    scene_depth_alias: observed.scene_depth_alias,
    scene_owned_copy: observed.scene_owned_copy,
    depth_owned_copy: observed.depth_owned_copy,
    owned_copy_count: observed.owned_copy_count,
    null_taken: observed.null_taken,
    counters: observed.counters,
  }
  return {
    id: definition.id, name: definition.name, accepted: definition.accepted,
    declared: definition.declared, observed,
    structural_signature: structuralSignature,
    structural_signature_sha256: sha256(JSON.stringify(structuralSignature)),
    result: { mixed_f32: value, mixed_f32_bits_le: f32Bits(value) },
  }
}

function build() {
  const records = cases.map(definition => {
    const first = render(definition), second = render(definition)
    if (!sameBytes(first, second)) throw new Error(`${definition.name}: repeat mismatch`)
    return {
      name: definition.name, dimensions: { width: definition.width, height: definition.height },
      source_phases: { inputTex: definition.phaseA, tex: definition.phaseB },
      borrowed_alias: Boolean(definition.alias), uniforms: definition.uniforms,
      tile_offset: Array.from(definition.tileOffset ?? new Float32Array(2)),
      full_resolution: Array.from(definition.fullResolution ?? new Float32Array([definition.width, definition.height])),
      coverage: definition.coverage, repeat_identity: true, output: result(first),
    }
  })
  if (records[0].output.f32_sha256 === records[1].output.f32_sha256) throw new Error('depth-source argument order is not discriminated')
  const directBorrowModes = directDefinitions.map(directRecord)
  const declaredModeIds = directDefinitions.map(item => item.id)
  const handledModeIds = [...handledDirectModeIds].sort((a, b) => a - b)
  const observedModeIds = directBorrowModes.map(item => item.id)
  const exactModeIds = directDefinitions.map((_, ordinal) => ordinal)
  if (JSON.stringify(declaredModeIds) !== JSON.stringify(exactModeIds)) throw new Error('direct ABI declaration ids are not exhaustive/contiguous')
  if (JSON.stringify(declaredModeIds) !== JSON.stringify(handledModeIds) || JSON.stringify(declaredModeIds) !== JSON.stringify(observedModeIds)) throw new Error('declared != handled != observed direct ABI modes')
  for (const item of directBorrowModes) {
    for (const field of ['branch_slot', 'abi_spelling', 'scene_source', 'depth_source']) {
      if (item.declared[field] !== item.observed[field]) throw new Error(`${item.name}: declared ${field} did not match execution witness`)
    }
    if (item.observed.counters.mode_dispatches !== 1) throw new Error(`${item.name}: switch arm did not execute exactly once`)
  }
  const expectedCounters = [
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
    [0, 2, 0, 0, 0, 0, 2, 96, 0, 2, 2, 1],
    [0, 0, 2, 0, 0, 0, 0, 0, 1, 2, 2, 1],
    [0, 0, 0, 2, 2, 2, 0, 0, 0, 2, 2, 1],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1],
    [0, 0, 0, 2, 2, 1, 0, 0, 0, 0, 0, 0],
  ]
  const counterFields = ['const_ref_bindings', 'value_copy_bindings', 'mutable_ref_bindings', 'nullable_pointer_bindings', 'pointer_null_checks', 'pointer_dereferences', 'surface_copy_allocations', 'copied_f32_lanes', 'writable_probes', 'scene_lane_reads', 'depth_lane_reads', 'mix_calls']
  directBorrowModes.forEach((item, ordinal) => {
    const actual = counterFields.map(field => item.observed.counters[field])
    if (JSON.stringify(actual) !== JSON.stringify(expectedCounters[ordinal])) throw new Error(`${item.name}: execution counters drift`)
  })
  if (!directBorrowModes[3].observed.scene_owned_copy || !directBorrowModes[3].observed.depth_owned_copy || directBorrowModes[3].observed.scene_aliases_tex || directBorrowModes[3].observed.depth_aliases_input) throw new Error('value-copy mode did not own and use independent Surface copies')
  if (!directBorrowModes[2].observed.scene_depth_alias || !directBorrowModes[2].observed.scene_aliases_input || !directBorrowModes[2].observed.scene_aliases_tex) throw new Error('alias mode did not execute with one shared Surface')
  if (directBorrowModes[0].result.mixed_f32_bits_le === directBorrowModes[6].result.mixed_f32_bits_le) throw new Error('wrong depth-a resource order is not value-discriminating')
  const semanticSignatures = directBorrowModes.map(item => item.structural_signature_sha256)
  if (new Set(semanticSignatures).size !== directBorrowModes.length) throw new Error('direct ABI semantic structural signatures are not pairwise unique')
  let invalidModeError = null
  try {
    const invalidCounters = freshCounters(), invalidOwned = new Set(), invalidNames = new Map()
    const invalidInput = patternedSurface(1, 1, 0), invalidTex = patternedSurface(1, 1, 1)
    invalidNames.set(invalidInput, 'inputTex'); invalidNames.set(invalidTex, 'tex')
    executeDirectMode({ id: 8 }, invalidInput, invalidTex, invalidOwned, invalidNames, invalidCounters)
  } catch (error) { invalidModeError = error.message }
  if (invalidModeError !== 'invalid direct ABI mode 8') throw new Error('invalid direct ABI enum was not rejected after full switch')
  const switchCaseIds = [...executeDirectMode.toString().matchAll(/case (\d+):/g)].map(match => Number(match[1]))
  if (JSON.stringify(switchCaseIds) !== JSON.stringify(declaredModeIds)) throw new Error('direct ABI switch arms do not exactly cover declarations')
  return {
    schema: 'noisemaker-for-cpp.task-29.focus-blur-oracles.v1',
    corpus_revision: revision, provenance: { ...provenance, node: process.version, public_identity: true, adapter_absent: true },
    program: {
      key, defines: {}, profile: 'focus-blur-borrowed-sampler-parameters-v1',
      helper: 'vec4 applyFocusBlur(sampler2D sceneTex, sampler2D depthTex, vec2 uv)',
      borrowed_abi: 'const Surface&; setup-owned Surface lifetime; no helper retention or mutation',
      call_order: { depthSource_0: ['tex', 'inputTex', 'uv'], depthSource_else: ['inputTex', 'tex', 'uv'] },
      loop: { trips_per_call: 64, max_calls_per_pixel: 1 },
      texture_sites: 4, texture_size_sites: 4, max_texture_reads_per_pixel: 67,
    },
    fixture: { source_pattern: 'deterministic top-down F32 RGBA phase pattern', output: 'top-down F32 RGBA Surface', fragment_origin: 'bottom-left runPass coordinates' },
    cases: records,
    direct_borrow_harness: {
      declared_mode_ids: declaredModeIds, handled_mode_ids: handledModeIds,
      observed_mode_ids: observedModeIds, switch_case_ids: switchCaseIds,
      declared_equals_handled_equals_observed: true,
      semantic_signature_fields_exclude: ['id', 'name', 'accepted', 'mixed_f32', 'mixed_f32_bits_le'],
      semantic_signature_count: semanticSignatures.length,
      semantic_signature_unique_count: new Set(semanticSignatures).size,
      invalid_enum: { id: 8, rejected: true, error: invalidModeError },
      source_sha256: {
        declarations: sha256(JSON.stringify(directDefinitions)),
        dispatch_switch: sha256(executeDirectMode.toString()),
        tracked_mix: sha256(`${trackedLane.toString()}\n${directMix.toString()}`),
        record_and_witness: sha256(directRecord.toString()),
        copy_implementation: sha256(surfaceCopy.toString()),
      },
    },
    direct_borrow_modes: directBorrowModes,
    negative_closure: {
      writable_sampler_parameter: 'reject', retained_surface_reference: 'reject', nullable_surface: 'reject', sampler_array: 'reject', sampler_return: 'reject', sampler_in_state_via_helper: 'reject', arbitrary_sampler_parameter_program: 'reject', changed_call_order_or_aliasing: 'reject', derivative_or_lod_expansion: 'reject', nonempty_defines: 'reject', owning_surface_copy: 'reject', second_sampler_helper: 'reject', stored_borrow: 'reject',
    },
  }
}

const payload = `${JSON.stringify(build(), null, 2)}\n`
if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== payload) throw new Error('Task29 Focus Blur oracle fixture drift')
  console.log(`Task29 Focus Blur oracle fixture ok (${cases.length} public cases, ${directDefinitions.length} direct modes)`)
} else {
  fs.writeFileSync(outPath, payload)
  console.log(outPath)
}
