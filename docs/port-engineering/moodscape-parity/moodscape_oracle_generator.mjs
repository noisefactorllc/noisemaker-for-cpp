#!/usr/bin/env node
// Authenticated canonical CPU oracle for classicNoisedeck/moodscape:moodscape.
// The authority is imported only after its complete literal closure is pinned.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const key = 'classicNoisedeck/moodscape:moodscape'
const effect = 'classicNoisedeck/moodscape'
const corpus = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourceRelative = `tools/glslcpp/corpus/${corpus}/sources/classicNoisedeck/moodscape/moodscape.glsl`
const outPath = path.join(here, 'moodscape-oracles.json')
const reportPath = path.join(here, 'moodscape-oracle-report.md')
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const f = Math.fround
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength)
const words = value => Array.from(new Uint32Array(value.buffer, value.byteOffset, value.byteLength / 4), x => `0x${(x >>> 0).toString(16).padStart(8, '0')}`)
const equal = (a, b) => a.length === b.length && a.every((x, i) => x === b[i])
const countDiff = (a, b) => a.reduce((n, x, i) => n + (x !== b[i] ? 1 : 0), 0)
const beneath = (a, b) => a === b || b.startsWith(`${a}${path.sep}`)

function rejectSymlink(candidate, label) {
  const resolved = path.resolve(candidate)
  try {
    if (fs.lstatSync(resolved).isSymbolicLink()) throw Error(`${label} must not be a symlink: ${candidate}`)
  } catch (error) {
    if (error?.code === 'ENOENT') return
    throw error
  }
}

const factoryShaExpected = '70db1168604045e22ac0c74f4b58a96d5e4ed2c6e107ec2fe3b2beab08ca479d'
const sourceShaExpected = 'a2580a36096208dd7a63965d2b277be9356f29a8d3af634d1736df9142db1a44'
const expectedClosure = Object.freeze([
  ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  ['src/csl/runtime.js', 'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee'],
  ['src/effects/adapters/bit-effects.js', '5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7'],
  ['src/effects/adapters/crt.js', 'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc'],
  ['src/effects/adapters/f32-color.js', 'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046'],
  ['src/effects/adapters/fractal.js', '0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29'],
  ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  ['src/effects/adapters/julia.js', '0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5'],
  ['src/effects/adapters/median.js', 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583'],
  ['src/effects/adapters/palette.js', '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'],
  ['src/effects/adapters/snow.js', '202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366'],
  ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  ['src/effects/definition.js', 'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02'],
  ['src/effects/generated/canonical-adapter-data.js', 'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab'],
  ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  ['src/effects/generated/kernels.js', 'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01'],
  ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
  ['src/effects/registry.js', '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'],
  ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  ['src/runtime/sampler.js', '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328'],
  ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
])

const argv = process.argv.slice(2)
const modes = argv.filter(x => x === '--write' || x === '--check' || x === '--self-test')
if (modes.length !== 1) throw Error('choose exactly one of --write, --check, or --self-test')
const mode = modes[0]
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || !argv[ci + 1]) throw Error('--cpu-root <immutable snapshot> is required')
const cpuArg = path.resolve(argv[ci + 1])
rejectSymlink(cpuArg, '--cpu-root')
let cpuStat
try { cpuStat = fs.lstatSync(cpuArg) } catch { throw Error(`immutable CPU authority does not exist: ${cpuArg}`) }
if (!cpuStat.isDirectory() || cpuStat.isSymbolicLink()) throw Error('--cpu-root must be a non-symlink directory')
const cpuRoot = fs.realpathSync(cpuArg)
const liveArg = process.env.NOISEMAKER_FOR_CPU
if (liveArg) rejectSymlink(liveArg, 'NOISEMAKER_FOR_CPU')
if (!liveArg || !fs.existsSync(liveArg) || !fs.statSync(liveArg).isDirectory()) throw Error(`live noisemaker-for-cpu checkout does not exist: ${liveArg ?? '<unset>'}`)
let liveIdentity
try { liveIdentity = JSON.parse(fs.readFileSync(path.join(liveArg, 'package.json'), 'utf8')).name } catch { throw Error('NOISEMAKER_FOR_CPU is not a noisemaker-for-cpu checkout') }
if (liveIdentity !== 'noisemaker-cpu') throw Error('NOISEMAKER_FOR_CPU is not a noisemaker-for-cpu checkout')
const live = fs.realpathSync(liveArg)
if (beneath(live, cpuRoot) || beneath(cpuRoot, live)) throw Error('authority must be an external immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot) || beneath(cpuRoot, cppRoot)) throw Error('authority must be external to the C++ repository')

function importClosure() {
  const patterns = [/\bfrom\s*['"]([^'"\n]+)['"]/g, /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g, /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm]
  const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
  const stack = entries.map(relative => path.join(cpuRoot, relative)); const seen = new Map()
  while (stack.length) {
    const candidate = stack.pop(); rejectSymlink(candidate, 'import closure file')
    let resolved
    try { resolved = fs.realpathSync(candidate) } catch { throw Error(`missing import closure file: ${candidate}`) }
    if (!beneath(cpuRoot, resolved) || beneath(live, resolved)) throw Error('import escaped immutable snapshot')
    if (seen.has(resolved)) continue
    const payload = fs.readFileSync(resolved); const text = payload.toString('utf8'); seen.set(resolved, sha(payload))
    if (/\bimport\s*\(\s*(?!['"])/.test(text)) throw Error(`nonliteral dynamic import: ${path.relative(cpuRoot, resolved)}`)
    for (const pattern of patterns) {
      pattern.lastIndex = 0; let match
      while ((match = pattern.exec(text))) {
        const specifier = match[1]
        if (specifier.startsWith('node:')) continue
        if (specifier.startsWith('/')) throw Error(`absolute module specifier ${specifier}`)
        if (!specifier.startsWith('./') && !specifier.startsWith('../')) throw Error(`bare module specifier ${specifier}`)
        const next = path.resolve(path.dirname(resolved), specifier)
        rejectSymlink(next, 'import closure file')
        let nextResolved
        try { nextResolved = fs.realpathSync(next) } catch { throw Error(`import closure escaped or missing: ${specifier}`) }
        if (!beneath(cpuRoot, nextResolved) || beneath(live, nextResolved)) throw Error(`import escaped immutable snapshot: ${specifier}`)
        stack.push(nextResolved)
      }
    }
  }
  return [...seen].map(([file, hash]) => [path.relative(cpuRoot, file), hash]).sort((a, b) => a[0].localeCompare(b[0]))
}
const actualClosure = importClosure(); const expectedClosureSorted = [...expectedClosure].sort((a, b) => a[0].localeCompare(b[0]))
if (JSON.stringify(actualClosure) !== JSON.stringify(expectedClosureSorted)) throw Error(`CPU import closure mismatch: ${JSON.stringify(actualClosure)}`)
for (const [relative, expected] of expectedClosureSorted) if (sha(fs.readFileSync(path.join(cpuRoot, relative))) !== expected) throw Error(`pinned CPU provenance drift: ${relative}`)

const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{ canonicalKernelFactories, canonicalAdapterFactories, kernelFactories }, { bindCanonicalKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js')])
if (process.version !== 'v24.7.0') throw Error('Moodscape authority Node drift')
const canonical = canonicalKernelFactories[key]; const publicFactory = kernelFactories.get(key)
if (typeof canonical !== 'function' || publicFactory !== canonical || canonicalAdapterFactories[key] !== undefined) throw Error('canonical/public factory identity or adapter ownership drift')
if (canonical.name !== 'canonicalFactory11' || sha(canonical.toString()) !== factoryShaExpected) throw Error('canonical factory text drift')
const sourceBytes = fs.readFileSync(path.join(cppRoot, sourceRelative))
if (sourceBytes.length !== 19559 || sha(sourceBytes) !== sourceShaExpected) throw Error('corpus source drift')

const runtimeBindingNames = ['NOISE_TYPE', 'COLOR_MODE', 'time', 'seed', 'wrap', 'resolution', 'tileOffset', 'fullResolution', 'noiseScale', 'refractAmt', 'speed', 'hueRotation', 'hueRange', 'intensity', 'ridges']
const runtimeBindingAbi = { NOISE_TYPE: 'int32', COLOR_MODE: 'int32', time: 'float', seed: 'int32', wrap: 'bool', resolution: 'Vec2', tileOffset: 'Vec2', fullResolution: 'Vec2', noiseScale: 'float', refractAmt: 'float', speed: 'float', hueRotation: 'float', hueRange: 'float', intensity: 'float', ridges: 'bool' }
const sourceUniformAbi = { time: 'float', seed: 'int', wrap: 'bool', resolution: 'vec2', tileOffset: 'vec2', fullResolution: 'vec2', noiseScale: 'float', refractAmt: 'float', speed: 'float', hueRotation: 'float', hueRange: 'float', intensity: 'float', ridges: 'bool' }
const cases = [
  { name: 'default-public', width: 4, height: 3, time: 0.25, seed: 44, tileOffset: [0, 0], fullResolution: [4, 3], noiseScale: 85, refractAmt: 5, speed: 25, hueRotation: 180, hueRange: 25, intensity: 0, ridges: true, wrap: true },
  { name: 'tiny-origin', width: 1, height: 1, time: 0, seed: 0, tileOffset: [0, 0], fullResolution: [1, 1], noiseScale: 1, refractAmt: 0, speed: 0, hueRotation: 0, hueRange: 0, intensity: -100, ridges: false, wrap: false },
  { name: 'negative-intensity', width: 6, height: 5, time: -1.5, seed: 7, tileOffset: [0, 0], fullResolution: [6, 5], noiseScale: 42, refractAmt: 67, speed: 100, hueRotation: 35, hueRange: 90, intensity: -75, ridges: true, wrap: false },
  { name: 'tile-offset', width: 5, height: 4, time: 2.75, seed: 91, tileOffset: [2, 1], fullResolution: [11, 9], noiseScale: 100, refractAmt: 33, speed: 13, hueRotation: 270, hueRange: 55, intensity: 40, ridges: false, wrap: true },
  { name: 'hue-extremes', width: 7, height: 3, time: 19.25, seed: 3, tileOffset: [0, 0], fullResolution: [7, 3], noiseScale: 12, refractAmt: 100, speed: 1, hueRotation: 359, hueRange: 100, intensity: 100, ridges: true, wrap: false },
  { name: 'zero-speed', width: 3, height: 2, time: 0.125, seed: 214, tileOffset: [1, 0], fullResolution: [8, 7], noiseScale: 2, refractAmt: 1, speed: 0, hueRotation: 90, hueRange: 1, intensity: 1, ridges: false, wrap: true },
]

function snapshotValue(value) {
  if (value instanceof Float32Array) return { type: 'Float32Array', words: words(value), bytes: Array.from(bytes(value)) }
  if (Array.isArray(value)) return value.map(snapshotValue)
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => [k, snapshotValue(v)]))
  return value
}
function snapshotControls(bindings, options) { return snapshotValue({ bindings, options }) }
function assertControlsUnchanged(before, bindings, options, label) { if (JSON.stringify(before) !== JSON.stringify(snapshotControls(bindings, options))) throw Error(`${label}: controls or typed-array bits mutated`) }
function record(surface) { const rb = Array.from(surface.toRgba8()); return { f32_words_le: words(surface.data), f32_sha256: sha(bytes(surface.data)), rgba8_bytes: rb, rgba8_sha256: sha(Buffer.from(rb)) } }
function strictCompare(a, b) {
  if (a.width !== b.width || a.height !== b.height) throw Error('dimensions mismatch before lane access')
  const aw = a.data instanceof Float32Array ? words(a.data) : (a.expected?.f32_words_le ?? a.f32_words_le); const bw = b.data instanceof Float32Array ? words(b.data) : (b.expected?.f32_words_le ?? b.f32_words_le)
  const ar = a.data instanceof Float32Array ? Array.from(a.toRgba8()) : (a.expected?.rgba8_bytes ?? a.rgba8_bytes); const br = b.data instanceof Float32Array ? Array.from(b.toRgba8()) : (b.expected?.rgba8_bytes ?? b.rgba8_bytes)
  const expectedCount = a.width * a.height * 4
  if (!Array.isArray(aw) || !Array.isArray(bw) || aw.length !== expectedCount || bw.length !== expectedCount) throw Error('Float32 count mismatch before element access')
  if (!Array.isArray(ar) || !Array.isArray(br) || ar.length !== expectedCount || br.length !== expectedCount) throw Error('RGBA8 count mismatch before element access')
  const changedFloat32 = countDiff(aw, bw); const changedRgba8 = countDiff(ar, br)
  return { exact: changedFloat32 === 0 && changedRgba8 === 0, changed_float32_lanes: changedFloat32, changed_rgba8_bytes: changedRgba8 }
}
function render(spec, candidate = canonical) {
  const tileOffset = new Float32Array(spec.tileOffset.map(f)); const fullResolution = new Float32Array(spec.fullResolution.map(f)); const resolution = new Float32Array([spec.width, spec.height])
  const bindings = { NOISE_TYPE: 10, COLOR_MODE: 2, time: f(spec.time), seed: spec.seed, wrap: spec.wrap, resolution, tileOffset, fullResolution, noiseScale: f(spec.noiseScale), refractAmt: f(spec.refractAmt), speed: f(spec.speed), hueRotation: f(spec.hueRotation), hueRange: f(spec.hueRange), intensity: f(spec.intensity), ridges: spec.ridges }
  const options = { width: spec.width, height: spec.height, time: bindings.time, seed: bindings.seed, wrap: bindings.wrap, resolution, tileOffset, fullResolution, uniforms: bindings }; const before = snapshotControls(bindings, options)
  const output = new Surface(spec.width, spec.height); const kernel = bindCanonicalKernel(candidate, options); runPass({ kernel, destination: output, tileRows: 2 }); assertControlsUnchanged(before, bindings, options, spec.name)
  return { output, bindings, options, controlsBefore: before }
}
function comparerSelfTests() {
  const good = { width: 1, height: 1, f32_words_le: ['0x3f800000', '0x00000000', '0x00000000', '0x3f800000'], rgba8_bytes: [255, 0, 0, 255] }; const clone = (v, c = {}) => ({ ...v, f32_words_le: [...v.f32_words_le], rgba8_bytes: [...v.rgba8_bytes], ...c }); const rejected = (fn, phrase) => { try { fn(); return false } catch (error) { return !phrase || String(error.message).includes(phrase) } }; let touched = false
  const dimensions = { width: 2, height: 1, get f32_words_le() { touched = true; return [] }, rgba8_bytes: [] }; const plusZero = clone(good, { f32_words_le: ['0x00000000', ...good.f32_words_le.slice(1)] }); const minusZero = clone(good, { f32_words_le: ['0x80000000', ...good.f32_words_le.slice(1)] }); const nanA = clone(good, { f32_words_le: ['0x7fc00001', ...good.f32_words_le.slice(1)] }); const nanB = clone(good, { f32_words_le: ['0x7fc00002', ...good.f32_words_le.slice(1)] }); const rgbaMismatch = clone(good, { rgba8_bytes: [255, 0, 0, 254] }); const controls = { data: new Float32Array([1, 2]) }; const before = snapshotControls(controls, {}); controls.data[0] = 3; let controlMutationRejected = false; try { assertControlsUnchanged(before, controls, {}, 'self-test') } catch { controlMutationRejected = true }
  return { good: strictCompare(good, clone(good)).exact, dimensions_before_access: rejected(() => strictCompare(good, dimensions), 'dimensions') && !touched, f32_short_count: rejected(() => strictCompare(good, clone(good, { f32_words_le: [] })), 'Float32 count'), f32_long_count: rejected(() => strictCompare(good, clone(good, { f32_words_le: [...good.f32_words_le, '0x00000000'] })), 'Float32 count'), rgba8_short_count: rejected(() => strictCompare(good, clone(good, { rgba8_bytes: [] })), 'RGBA8 count'), rgba8_long_count: rejected(() => strictCompare(good, clone(good, { rgba8_bytes: [...good.rgba8_bytes, 0] })), 'RGBA8 count'), signed_zero: strictCompare(plusZero, minusZero).exact === false, nan_payload: strictCompare(nanA, nanB).exact === false, rgba_mismatch: strictCompare(good, rgbaMismatch).exact === false, control_mutation_rejected: controlMutationRejected }
}
const rendered = cases.map(spec => { const first = render(spec); const second = render(spec); const firstRecord = record(first.output); const secondRecord = record(second.output); const comparison = strictCompare({ width: first.output.width, height: first.output.height, expected: firstRecord }, { width: second.output.width, height: second.output.height, expected: secondRecord }); if (!comparison.exact) throw Error(`${spec.name}: repeat mismatch`); if (first.output === second.output || first.output.data.buffer === second.output.data.buffer) throw Error(`${spec.name}: output storage is not independent`); return { ...spec, expected: firstRecord, f32_byte_count: firstRecord.f32_words_le.length * 4, rgba8_byte_count: firstRecord.rgba8_bytes.length, repeat: { exact: true, dimensions: true, f32_words: true, rgba8_bytes: true }, storage: { distinct_surface_objects: true, distinct_f32_backing_stores: true }, controls_snapshot: { unchanged: true, typed_array_bits_unchanged: true } } })

const baseFactoryText = canonical.toString(); const mutations = [
  ['noise-frequency', 'xFreq = map(noiseScale, 1, 100, 1, 0.25);', 'xFreq = map(noiseScale, 1, 100, 1, 0.5);'], ['refract-amount', 'var ref = map(refractAmt, 0, 100, 0, 2.5);', 'var ref = map(refractAmt, 0, 100, 0, 1.5);'], ['hue-range-factor', 'color[0] = (color[0] * hueRange) * 0.009999999776482582;', 'color[0] = (color[0] * hueRange) * 0.019999999552965164;'], ['simplex-speed-factor', 'var scaledTime10 = ((simplexValue(st, xFreq, yFreq, s + 50, time)) * speed) * 0.0024999999441206455;', 'var scaledTime10 = ((simplexValue(st, xFreq, yFreq, s + 50, time)) * speed) * 0.004999999888241291;'], ['brightness-map', 'var bright = map(intensity, -100, 100, -0.4000000059604645, 0.4000000059604645);', 'var bright = map(intensity, -100, 100, -0.20000000298023224, 0.20000000298023224);'],
]
const mutationLedger = await Promise.all(mutations.map(async ([name, anchor, replacement]) => { if (baseFactoryText.split(anchor).length !== 2) throw Error(`mutation anchor cardinality: ${name}`); const text = baseFactoryText.replace(anchor, replacement); const module = await import(`data:text/javascript;base64,${Buffer.from(`${text}\nexport { canonicalFactory11 as moodscapeFactory }`).toString('base64')}`); const mutant = module.moodscapeFactory; const rows = rendered.map(spec => { const reference = render(spec).output; const candidate = render(spec, mutant).output; const result = strictCompare({ width: reference.width, height: reference.height, expected: record(reference) }, { width: candidate.width, height: candidate.height, expected: record(candidate) }); return { case: spec.name, exact: result.exact, changed_float32_lanes: result.changed_float32_lanes, changed_rgba8_bytes: result.changed_rgba8_bytes } }); const required = rows.filter(row => row.changed_float32_lanes > 0 && row.changed_rgba8_bytes > 0).map(row => row.case); if (!required.length) throw Error(`${name}: no positive F32/RGBA8 witness`); return { name, anchor, replacement, anchor_sha256: sha(anchor), replacement_sha256: sha(replacement), mutated_factory_sha256: sha(text), independent: true, anchor_cardinality: 1, witnesses: required, results: rows } }))
const comparer = comparerSelfTests(); if (!Object.values(comparer).every(Boolean)) throw Error('comparer self-tests failed')
const document = { schema: 'noisemaker-for-cpp.moodscape.pixel-parity.v1', schema_version: 1, program_key: key, effect_key: effect, runtime_key: key, corpus_revision: corpus, upstream_revision: UPSTREAM_REVISION, defines: { NOISE_TYPE: 10, COLOR_MODE: 2 }, exactness_contract: { float32: 'raw little-endian uint32 words; signed zero and NaN payloads significant', rgba8: 'complete independent RGBA8 bytes', tolerance: 'none', comparison: 'dimensions, counts, every uint32 word, every RGBA8 byte' }, comparer_self_tests: comparer, authority: { node_version: process.version, oracle: 'unmodified canonical Moodscape factory from immutable CPU snapshot', cpu_root_argument: '<immutable-cpu-snapshot-root>', immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, closure_cardinality: actualClosure.length, import_closure: actualClosure.map(([relative_path, sha256]) => ({ relative_path, sha256 })) }, factory: { name: canonical.name, text_sha256: factoryShaExpected, public_factory_is_canonical_identity: true, canonical_adapter_factories_own_key: false }, provenance: { source: { relative_path: sourceRelative, bytes: sourceBytes.length, sha256: sha(sourceBytes) }, generator: { relative_path: 'docs/port-engineering/moodscape-parity/moodscape_oracle_generator.mjs' }, materializer: { relative_path: 'tools/glslcpp/generate_moodscape_native_oracle_include.py' } }, runtime_binding_names: runtimeBindingNames, runtime_binding_abi: runtimeBindingAbi, source_uniform_abi: sourceUniformAbi, output_abi: { name: 'fragColor', source_type: 'vec4', runtime_type: 'Vec4', role: 'output' }, render_cases: rendered, mutation_anchor_cardinality: { total: mutationLedger.length, anchors: Object.fromEntries(mutationLedger.map(item => [item.name, item.anchor_cardinality])) }, mutation_ledger: mutationLedger, claim_boundaries: { canonical_factory_only: true, typed_slice_landing: false, shared_emitter_modified: false, samplers: false, input_textures: false } }
const payload = Buffer.from(`${JSON.stringify(document, null, 2)}\n`)
const report = Buffer.from('# Moodscape pixel-parity oracle\n\nAuthenticated canonical CPU oracle for **' + key + '** with fixed defines NOISE_TYPE=10 and COLOR_MODE=2. The authority is imported only after a recursively traversed, realpath-confined, literal-import closure of ' + actualClosure.length + ' hash-pinned files is authenticated. Bare, escaping, missing, symlinked, and nonliteral imports fail before authority import.\n\nThe exact ordered ABI contains the two fixed defines followed by the thirteen source uniforms and binds only the fragColor output; there are no samplers or input textures. Each of six cases executes twice in one process. The comparer checks dimensions and counts before lane access, then every raw little-endian Float32 word and every RGBA8 byte. Distinct surfaces and backing stores, typed-array bits, and all controls are snapshotted and verified unchanged.\n\nFive source mutations are authenticated by exact anchor, replacement, factory, cardinality, independence, and positive Float32/RGBA8 witnesses. The package claims no typed-slice or native integration.\n\n## Reproduction\n\n    NOISEMAKER_FOR_CPU=/Users/aayars/platform/noisemaker-for-cpu node docs/port-engineering/moodscape-parity/moodscape_oracle_generator.mjs --check --cpu-root /private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu\n    PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_moodscape_native_oracle_include.py --check\n')
function checked(file, expected) { if (!fs.existsSync(file) || !equal([...fs.readFileSync(file)], [...expected])) throw Error(`drift: ${file}`) }
function selfTest() { const checks = [['closure cardinality', actualClosure.length === expectedClosure.length], ['closure exact', JSON.stringify(actualClosure) === JSON.stringify(expectedClosureSorted)], ['comparer self-tests', Object.values(comparer).every(Boolean)], ['repeat and storage', rendered.every(item => item.repeat.exact && item.storage.distinct_surface_objects && item.storage.distinct_f32_backing_stores && item.controls_snapshot.unchanged)], ['mutation witnesses', mutationLedger.length === 5 && mutationLedger.every(item => item.independent && item.anchor_cardinality === 1 && item.witnesses.length > 0 && item.witnesses.every(name => item.results.find(row => row.case === name)?.changed_float32_lanes > 0 && item.results.find(row => row.case === name)?.changed_rgba8_bytes > 0))]]; checks.forEach(([name, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}`)); if (!checks.every(([, ok]) => ok)) throw Error('Moodscape oracle self-test failed') }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(outPath, payload); fs.writeFileSync(`${outPath}.sha256`, `${sha(payload)}  moodscape-oracles.json\n`); fs.writeFileSync(reportPath, report); fs.writeFileSync(`${reportPath}.sha256`, `${sha(report)}  moodscape-oracle-report.md\n`); console.log(`moodscape oracle written (${rendered.length} cases, ${mutationLedger.length} mutations)`) } else { checked(outPath, payload); checked(reportPath, report); if (mode === '--self-test') { selfTest(); console.log('strict comparer, authority, and mutation witnesses verified') } else console.log('moodscape oracle check passed') }
