import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'focus-blur-oracles.json')
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
  return {
    schema: 'noisemaker-for-cpp.future-precompute.focus-blur-oracles.v1',
    corpus_revision: revision, provenance: { ...provenance, node: process.version, public_identity: true, adapter_absent: true },
    program: {
      key, defines: {}, profile_candidate: 'focus-blur-borrowed-sampler-parameters-v1',
      helper: 'vec4 applyFocusBlur(sampler2D sceneTex, sampler2D depthTex, vec2 uv)',
      borrowed_abi_candidate: 'const Surface&; setup-owned Surface lifetime; no helper retention or mutation',
      call_order: { depthSource_0: ['tex', 'inputTex', 'uv'], depthSource_else: ['inputTex', 'tex', 'uv'] },
      loop: { trips_per_call: 64, max_calls_per_pixel: 1 },
      max_texture_reads_per_pixel: 67,
    },
    fixture: { source_pattern: 'deterministic top-down F32 RGBA phase pattern', output: 'top-down F32 RGBA Surface', fragment_origin: 'bottom-left runPass coordinates' },
    cases: records,
    negative_closure: {
      writable_sampler_parameter: 'reject', retained_surface_reference: 'reject', nullable_surface: 'reject', sampler_array: 'reject', sampler_return: 'reject', sampler_in_state_via_helper: 'reject', arbitrary_sampler_parameter_program: 'reject', changed_call_order_or_aliasing: 'reject', derivative_or_lod_expansion: 'reject', nonempty_defines: 'reject',
    },
  }
}

const payload = `${JSON.stringify(build(), null, 2)}\n`
if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== payload) throw new Error('focus-blur oracle fixture drift')
  console.log(`focus-blur oracle fixture ok (${cases.length} cases)`)
} else {
  fs.writeFileSync(outPath, payload)
  console.log(outPath)
}
