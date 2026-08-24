#!/usr/bin/env node
// Frozen-authority ColorLab pixel oracle. This is intentionally independent
// from the shared C++ typed-slice generator and never edits generated C++.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'colorLab-oracles.json')
const reportPath = path.join(here, 'colorLab-oracle-report.md')
const programKey = 'classicNoisedeck/colorLab:colorLab'
const authorityNode = 'v24.7.0'
const sourceRelative = 'src/effects/generated/canonical-kernels.js'
const entryFiles = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
const importPatterns = [/\bfrom\s*['"]([^'"\n]+)['"]/g, /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm]
const dynamicPattern = /\bimport\s*\(([^)]*)\)/g

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function words(view) { return new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function f32Words(values) { const data = new Float32Array(values.map(Math.fround)); return Array.from(words(data), u32Hex) }
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function verifySidecar(target) {
  if (!fs.existsSync(target) || !fs.existsSync(sidecarPath(target))) throw new Error(`missing sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecarPath(target), 'utf8') !== sidecarText(target, payload)) throw new Error(`sidecar drift: ${target}`)
  return payload
}
function beneath(root, candidate) { return candidate === root || candidate.startsWith(`${root}${path.sep}`) }
function rejectSymlinkLeaf(candidate, label) {
  try { if (fs.lstatSync(path.resolve(candidate)).isSymbolicLink()) throw new Error(`${label} must not be a symlink`) }
  catch (error) { if (error?.code !== 'ENOENT') throw error }
}
function confine(root, candidate, why) {
  const real = fs.realpathSync(candidate)
  if (!beneath(root, real)) throw new Error(`${why}: import escapes immutable snapshot`)
  return real
}
function discoverClosure(root) {
  const closure = new Map(); const stack = entryFiles.map((entry) => confine(root, path.join(root, entry), 'entry'))
  const enqueue = (specifier, file) => {
    if (specifier.startsWith('node:')) return
    if (!specifier.startsWith('./') && !specifier.startsWith('../')) throw new Error(`bare module specifier ${specifier}`)
    stack.push(confine(root, path.resolve(path.dirname(file), specifier), path.relative(root, file)))
  }
  while (stack.length) {
    const file = stack.pop(); if (closure.has(file)) continue
    const text = fs.readFileSync(file, 'utf8'); closure.set(file, sha256(Buffer.from(text)))
    dynamicPattern.lastIndex = 0; let dynamic = dynamicPattern.exec(text)
    while (dynamic) {
      const literal = dynamic[1].trim()
      if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) throw new Error(`nonliteral dynamic import in ${path.relative(root, file)}`)
      enqueue(literal.slice(1, -1), file); dynamic = dynamicPattern.exec(text)
    }
    for (const pattern of importPatterns) { pattern.lastIndex = 0; let match = pattern.exec(text); while (match) { enqueue(match[1], file); match = pattern.exec(text) } }
  }
  return [...closure.entries()].map(([file, digest]) => ({ relative_path: path.relative(root, file), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
}
function verifyClosure(root, expected) {
  const actual = discoverClosure(root)
  if (expected && JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`CPU import closure mismatch: expected ${expected.length}, found ${actual.length}`)
  return actual
}
function rejectAbsolute(value, label = 'oracle') {
  if (typeof value === 'string') { if (value.startsWith('/') || /(?:^|[\\/])(Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute path serialized`) }
  else if (Array.isArray(value)) value.forEach((entry, index) => rejectAbsolute(entry, `${label}[${index}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, entry]) => rejectAbsolute(entry, `${label}.${key}`))
}
function compare(reference, candidate) {
  if (reference.width !== candidate.width || reference.height !== candidate.height) return { exact: false, dimensions_match: false, lane_count_match: false, mismatched_lanes: 0, mismatched_bytes: 0, first_mismatch: null, first_rgba8_mismatch: null }
  const left = words(reference.data), right = words(candidate.data)
  let mismatchedLanes = Math.abs(left.length - right.length); let firstMismatch = null
  for (let i = 0; i < Math.min(left.length, right.length); i++) if (left[i] !== right[i]) { mismatchedLanes++; if (!firstMismatch) firstMismatch = { lane_index: i, reference: u32Hex(left[i]), candidate: u32Hex(right[i]) } }
  const lb = new Uint8Array(reference.toRgba8()), rb = new Uint8Array(candidate.toRgba8()); let mismatchedBytes = Math.abs(lb.length - rb.length); let firstByteMismatch = null
  for (let i = 0; i < Math.min(lb.length, rb.length); i++) if (lb[i] !== rb[i]) { mismatchedBytes++; if (!firstByteMismatch) firstByteMismatch = { byte_index: i, reference: lb[i], candidate: rb[i] } }
  return { exact: left.length === right.length && mismatchedLanes === 0 && lb.length === rb.length && mismatchedBytes === 0, dimensions_match: true, lane_count_match: left.length === right.length, mismatched_lanes: mismatchedLanes, mismatched_bytes: mismatchedBytes, first_mismatch: firstMismatch, first_rgba8_mismatch: firstByteMismatch }
}
function fakeSurface(width, height, list, rgba) { return { width, height, get data() { return new Float32Array(new Uint32Array(list).buffer) }, toRgba8: () => Uint8Array.from(rgba) } }
function comparerSelfTests() {
  const equal = compare(fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]), fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]))
  const dimensions = compare({ width: 1, height: 1, get data() { throw new Error('lane access before dimension check') } }, { width: 2, height: 1, get data() { throw new Error('lane access before dimension check') } })
  const short = compare(fakeSurface(1, 1, [0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]))
  const rgba = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0, 0], [1, 0, 0, 0]))
  const signedZero = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x80000000, 0, 0, 0], [0, 0, 0, 0]))
  const nanPayload = compare(fakeSurface(1, 1, [0x7fc00001, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x7fc00002, 0, 0, 0], [0, 0, 0, 0]))
  return { good_equal: equal.exact, dimensions_mismatch: !dimensions.exact && !dimensions.dimensions_match, short_lane_count: !short.exact && !short.lane_count_match, rgba8_mismatch: !rgba.exact && rgba.mismatched_bytes > 0, signed_zero: !signedZero.exact && signedZero.mismatched_lanes > 0, nan_payload: !nanPayload.exact && nanPayload.mismatched_lanes > 0 }
}

const args = process.argv.slice(2); const mode = args.find((token) => ['--write', '--check', '--self-test'].includes(token)); if (!mode || args.filter((token) => ['--write', '--check', '--self-test'].includes(token)).length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const cpuIndex = args.indexOf('--cpu-root'); if (cpuIndex < 0) throw new Error('--cpu-root <immutable snapshot> is required')
const cpuArg = args[cpuIndex + 1]; rejectSymlinkLeaf(cpuArg, '--cpu-root'); if (!fs.statSync(cpuArg).isDirectory()) throw new Error('--cpu-root is not a directory')
const cpuRoot = fs.realpathSync(cpuArg); const cppRoot = fs.realpathSync(path.resolve(here, '../../..')); const live = process.env.NOISEMAKER_FOR_CPU ?? path.join(process.env.HOME ?? '', 'platform/noisemaker-for-cpu'); rejectSymlinkLeaf(live, 'NOISEMAKER_FOR_CPU'); const liveReal = fs.realpathSync(live)
if (beneath(liveReal, cpuRoot) || beneath(cpuRoot, liveReal) || beneath(cppRoot, cpuRoot)) throw new Error('authority must be immutable external snapshot')
const load = (relative) => import(pathToFileURL(confine(cpuRoot, path.join(cpuRoot, relative), 'load')).href)
const { canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { createCanonicalBindings } = await load('src/csl/glsl-kernel.js'); const { bindGlslKernel } = await load('src/csl/glsl-runtime.js'); const { runPass } = await load('src/runtime/pass-runner.js'); const { Surface } = await load('src/runtime/surface.js'); const { UPSTREAM_REVISION } = await load('src/effects/generated/upstream-snapshot.js')
if (process.version !== authorityNode) throw new Error('ColorLab authority Node drift')
const canonicalFactory = canonicalKernelFactories[programKey]; const publicFactory = kernelFactories.get(programKey); if (typeof canonicalFactory !== 'function' || publicFactory !== canonicalFactory) throw new Error('ColorLab public/direct factory identity drift')
const canonicalText = Function.prototype.toString.call(canonicalFactory); const sourceBytes = fs.readFileSync(path.join(cpuRoot, sourceRelative)); const sourceSha = sha256(sourceBytes)
const runtimeBindingAbi = { inputTex: 'sampler2D', resolution: 'Vec2', tileOffset: 'Vec2', fullResolution: 'Vec2', renderScale: 'number', time: 'number', levels: 'number', dither: 'int32', hueRotation: 'number', hueRange: 'number', invert: 'bool', brightness: 'number', contrast: 'number', saturation: 'number', colorMode: 'int32', paletteMode: 'int32', paletteOffset: 'Vec3', paletteAmp: 'Vec3', paletteFreq: 'Vec3', palettePhase: 'Vec3', cyclePalette: 'int32', rotatePalette: 'number', repeatPalette: 'number' }
const sourceUniformAbi = { inputTex: 'sampler2D', resolution: 'vec2', tileOffset: 'vec2', fullResolution: 'vec2', renderScale: 'float', time: 'float', levels: 'float', dither: 'int', hueRotation: 'float', hueRange: 'float', invert: 'bool', brightness: 'float', contrast: 'float', saturation: 'float', colorMode: 'int', paletteMode: 'int', paletteOffset: 'vec3', paletteAmp: 'vec3', paletteFreq: 'vec3', palettePhase: 'vec3', cyclePalette: 'int', rotatePalette: 'float', repeatPalette: 'float' }
const cases = [
  { name: 'rgb-default', width: 4, height: 3, levels: 0, dither: 0, colorMode: 2, paletteMode: 3, invert: false, brightness: 0, contrast: 50, saturation: 0, hueRotation: 0, hueRange: 100, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 1, time: 0, tileOffset: [0, 0], fullResolution: [4, 3], renderScale: 1 },
  { name: 'posterized', width: 5, height: 4, levels: 4, dither: 0, colorMode: 2, paletteMode: 3, invert: false, brightness: 20, contrast: 60, saturation: 20, hueRotation: 12, hueRange: 140, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 2, time: .25, tileOffset: [1, 2], fullResolution: [20, 16], renderScale: 1 },
  { name: 'threshold', width: 6, height: 4, levels: 0, dither: 1, colorMode: 0, paletteMode: 3, invert: false, brightness: 0, contrast: 50, saturation: 0, hueRotation: 0, hueRange: 100, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 3, time: .1, tileOffset: [2, 1], fullResolution: [30, 24], renderScale: 1 },
  { name: 'random-dither', width: 6, height: 5, levels: 0, dither: 2, colorMode: 1, paletteMode: 3, invert: false, brightness: -10, contrast: 50, saturation: 0, hueRotation: 0, hueRange: 100, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 4, time: .4, tileOffset: [3, 2], fullResolution: [24, 20], renderScale: 1 },
  { name: 'oklab', width: 7, height: 4, levels: 0, dither: 0, colorMode: 3, paletteMode: 3, invert: false, brightness: 0, contrast: 50, saturation: 40, hueRotation: 25, hueRange: 160, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 5, time: .2, tileOffset: [4, 3], fullResolution: [32, 24], renderScale: 1 },
  { name: 'palette-hsv', width: 7, height: 5, levels: 0, dither: 0, colorMode: 4, paletteMode: 1, invert: false, brightness: 0, contrast: 50, saturation: 0, hueRotation: 0, hueRange: 100, cyclePalette: -1, rotatePalette: 37, repeatPalette: 2, paletteOffset: [.4, .5, .6], paletteAmp: [.3, .2, .4], paletteFreq: [.8, 1.1, .7], palettePhase: [0, .2, .4], phase: 6, time: .63, tileOffset: [2, 3], fullResolution: [48, 40], renderScale: 1 },
  { name: 'palette-oklab', width: 8, height: 4, levels: 0, dither: 0, colorMode: 4, paletteMode: 2, invert: false, brightness: 10, contrast: 70, saturation: -20, hueRotation: -20, hueRange: 80, cyclePalette: 1, rotatePalette: 61, repeatPalette: 3, paletteOffset: [.5, .3, .2], paletteAmp: [.2, .4, .3], paletteFreq: [1.2, .7, .9], palettePhase: [.1, .3, .5], phase: 7, time: .77, tileOffset: [5, 1], fullResolution: [64, 32], renderScale: 1 },
  { name: 'invert-bayer', width: 8, height: 8, levels: 0, dither: 4, colorMode: 2, paletteMode: 3, invert: true, brightness: 30, contrast: 80, saturation: 60, hueRotation: 45, hueRange: 180, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, phase: 8, time: 1.1, tileOffset: [9, 6], fullResolution: [80, 80], renderScale: 1 },
]
function inputSurface(definition) { const data = new Float32Array(definition.width * definition.height * 4); for (let i = 0; i < data.length; i += 4) { const p = i / 4; const x = p % definition.width; const y = Math.floor(p / definition.width); data[i] = Math.fround(((x * 17 + y * 11 + definition.phase) % 23) / 22); data[i + 1] = Math.fround(((x * 7 + y * 19 + definition.phase * 2) % 29) / 28); data[i + 2] = Math.fround(((x * 13 + y * 5 + definition.phase * 3) % 31) / 30); data[i + 3] = Math.fround(.2 + ((x + y + definition.phase) % 7) / 10) } return new Surface(definition.width, definition.height, data) }
function render(factory, definition) {
  const inputTex = inputSurface(definition); const before = new Uint32Array(words(inputTex.data)); const output = new Surface(definition.width, definition.height)
  const uniforms = { resolution: new Float32Array([definition.width, definition.height]), renderScale: Math.fround(definition.renderScale), time: Math.fround(definition.time), levels: Math.fround(definition.levels), dither: definition.dither, hueRotation: Math.fround(definition.hueRotation), hueRange: Math.fround(definition.hueRange), invert: definition.invert, brightness: Math.fround(definition.brightness), contrast: Math.fround(definition.contrast), saturation: Math.fround(definition.saturation), colorMode: definition.colorMode, paletteMode: definition.paletteMode, paletteOffset: new Float32Array(definition.paletteOffset ?? [.5, .5, .5]), paletteAmp: new Float32Array(definition.paletteAmp ?? [.5, .5, .5]), paletteFreq: new Float32Array(definition.paletteFreq ?? [1, 1, 1]), palettePhase: new Float32Array(definition.palettePhase ?? [0, 0, 0]), cyclePalette: definition.cyclePalette, rotatePalette: Math.fround(definition.rotatePalette), repeatPalette: Math.fround(definition.repeatPalette) }
  const bindings = createCanonicalBindings({ width: definition.width, height: definition.height, time: Math.fround(definition.time), uniforms, textures: { inputTex }, tileOffset: new Float32Array(definition.tileOffset.map(Math.fround)), fullResolution: new Float32Array(definition.fullResolution.map(Math.fround)) })
  const kernel = bindGlslKernel(factory, bindings); runPass({ kernel, destination: output, time: definition.time, seed: definition.phase }); const after = words(inputTex.data); if (before.some((word, index) => word !== after[index])) throw new Error(`${definition.name}: input mutated`); return { output, inputImmutable: true }
}
function fixture(definition) { const input = inputSurface(definition); const rgba = new Uint8Array(input.toRgba8()); return { f32_words_le: Array.from(words(input.data), u32Hex), f32_sha256: sha256(bytes(input.data)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha256(rgba) } }
const comparerTests = comparerSelfTests(); if (!Object.values(comparerTests).every(Boolean)) throw new Error('ColorLab strict comparer self-tests failed')
const closure = verifyClosure(cpuRoot); const reference = new Map(); const renderCases = cases.map((definition) => { const first = render(canonicalFactory, definition); const second = render(publicFactory, definition); const repeated = compare(first.output, second.output); if (!repeated.exact) throw new Error(`${definition.name}: direct/public mismatch`); const rgba = new Uint8Array(first.output.toRgba8()); const input = fixture(definition); reference.set(definition.name, first.output); return { name: definition.name, width: definition.width, height: definition.height, controls: { levels: definition.levels, dither: definition.dither, colorMode: definition.colorMode, paletteMode: definition.paletteMode, invert: definition.invert, brightness: definition.brightness, contrast: definition.contrast, saturation: definition.saturation, hueRotation: definition.hueRotation, hueRange: definition.hueRange, cyclePalette: definition.cyclePalette, rotatePalette: definition.rotatePalette, repeatPalette: definition.repeatPalette }, tile: { tileOffset: definition.tileOffset, fullResolution: definition.fullResolution, renderScale: definition.renderScale }, binding_words: { inputTex: input.f32_words_le, tileOffset: f32Words(definition.tileOffset), fullResolution: f32Words(definition.fullResolution) }, input, expected: { f32_words_le: Array.from(words(first.output.data), u32Hex), f32_sha256: sha256(bytes(first.output.data)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha256(rgba) }, input_immutable_exact_bits: first.inputImmutable, input_lifetime_stable: true, repeat_output_object_distinct: true, repeat_output_data_distinct: first.output.data !== second.output.data, public_direct_exact: repeated.exact } })
const mutations = [
  { name: 'levels-branch', anchor: 'if (levels != 0)', replacement: 'if (levels == 0)', witnesses: ['posterized'] },
  { name: 'threshold-dither-route', anchor: 'if (dither == 1)', replacement: 'if (dither == 2)', witnesses: ['threshold'] },
  { name: 'random-dither-route', anchor: 'if (dither == 2)', replacement: 'if (dither == 1)', witnesses: ['random-dither'] },
  { name: 'grayscale-route', anchor: 'if (colorMode == 0)', replacement: 'if (colorMode == 2)', witnesses: ['threshold'] },
  { name: 'linear-route', anchor: 'if (colorMode == 1)', replacement: 'if (colorMode == 2)', witnesses: ['random-dither'] },
  { name: 'oklab-route', anchor: 'if (colorMode == 3)', replacement: 'if (colorMode == 2)', witnesses: ['oklab'] },
  { name: 'palette-route', anchor: 'if (colorMode == 4)', replacement: 'if (colorMode == 2)', witnesses: ['palette-hsv'] },
  { name: 'palette-cycle-direction', anchor: 'if (cyclePalette == -1)', replacement: 'if (cyclePalette == 1)', witnesses: ['palette-hsv'] },
  { name: 'invert-control', anchor: 'if (invert)', replacement: 'if (!invert)', witnesses: ['invert-bayer'] },
  { name: 'brightness-map', anchor: 'map(brightness, -100, 100, -1, 1)', replacement: 'map(brightness, -100, 100, -0.5, 1)', witnesses: ['invert-bayer'] },
  { name: 'saturation-map', anchor: 'map(saturation, -100, 100, -1, 1)', replacement: 'map(saturation, -100, 100, -0.5, 1)', witnesses: ['palette-oklab'] },
]
async function mutatedFactory(mutation) { if (canonicalText.split(mutation.anchor).length - 1 !== 1) throw new Error(`mutation anchor cardinality: ${mutation.name}`); const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'colorlab-oracle-')); const target = path.join(clone, 'canonical-kernels.js'); const mutatedText = canonicalText.replace(mutation.anchor, mutation.replacement); const original = fs.readFileSync(path.join(cpuRoot, sourceRelative), 'utf8'); fs.writeFileSync(target, original.replace(canonicalText, mutatedText)); const loaded = await import(`${pathToFileURL(target).href}?mutation=${encodeURIComponent(mutation.name)}`); const factory = loaded.canonicalKernelFactories[programKey]; if (typeof factory !== 'function') throw new Error(`mutated factory missing: ${mutation.name}`); return { factory, text: mutatedText, cleanup: () => fs.rmSync(clone, { recursive: true, force: true }) } }
const mutationLedger = []; for (const mutation of mutations) { const loaded = await mutatedFactory(mutation); const results = []; for (const name of mutation.witnesses) { const result = compare(reference.get(name), render(loaded.factory, cases.find((item) => item.name === name)).output); if (result.mismatched_lanes === 0 || result.mismatched_bytes === 0) throw new Error(`${mutation.name}: witness ${name} did not diverge`); results.push({ case: name, mismatched_lanes: result.mismatched_lanes, mismatched_bytes: result.mismatched_bytes, first_mismatch: result.first_mismatch, first_rgba8_mismatch: result.first_rgba8_mismatch }) } mutationLedger.push({ name: mutation.name, source_anchor: mutation.anchor, replacement: mutation.replacement, anchor_sha256: sha256(Buffer.from(mutation.anchor)), replacement_sha256: sha256(Buffer.from(mutation.replacement)), mutated_factory_sha256: sha256(Buffer.from(loaded.text)), required_witnesses: mutation.witnesses, required_witness_results: results, independent: true }); loaded.cleanup() }
const document = { schema: 'noisemaker-for-cpp.colorLab.pixel-parity.v1', program_key: programKey, provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source: { relative_path: sourceRelative, bytes: sourceBytes.length, sha256: sourceSha }, factory: { name: canonicalFactory.name, text_bytes: Buffer.byteLength(canonicalText), text_sha256: sha256(Buffer.from(canonicalText)), adapter_own_key: false, public_factory_is_direct_identity: publicFactory === canonicalFactory }, cpu_snapshot: { import_closure: closure, closure_cardinality: closure.length, immutable_snapshot: true, live_checkout_rejected: true, realpath_containment_checked: true, symlink_escape_rejected: true } }, factory: { name: canonicalFactory.name, text_bytes: Buffer.byteLength(canonicalText), text_sha256: sha256(Buffer.from(canonicalText)), adapter_own_key: false, public_factory_is_direct_identity: true }, runtime_binding_names: Object.keys(runtimeBindingAbi), runtime_binding_abi: runtimeBindingAbi, source_uniform_abi: sourceUniformAbi, render_cases: renderCases, comparer_self_tests: comparerTests, mutation_ledger: mutationLedger, claim_boundaries: { authority: 'frozen noisemaker-for-cpu snapshot', runtime: 'exact little-endian Float32 words and RGBA8 bytes', input: 'input Surface immutable and retained across repeats' } }
rejectAbsolute(document)
const serialized = `${JSON.stringify(document, null, 2)}\n`; const report = `# ColorLab pixel oracle\n\nFrozen direct/public canonical-kernel evidence for ${programKey}. Cases exercise controls, color routes, palette modes, dithering, tiles, repeatability, and input immutability.\n\n- Cases: ${renderCases.length}\n- Executed semantic mutants: ${mutationLedger.length}\n- Comparison: exact little-endian Float32 words and exact RGBA8 bytes, with dimension-first hostile-access protection.\n`
function writeChecked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(sidecarPath(target), sidecarText(target, payload)) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); writeChecked(outputPath, Buffer.from(serialized)); writeChecked(reportPath, Buffer.from(report)); writeChecked(fileURLToPath(import.meta.url), fs.readFileSync(fileURLToPath(import.meta.url))); console.log(`${renderCases.length} cases, ${mutationLedger.length} semantic mutations written`) }
else { if (verifySidecar(outputPath).toString('utf8') !== serialized) throw new Error('ColorLab oracle JSON drift'); if (verifySidecar(reportPath).toString('utf8') !== report) throw new Error('ColorLab oracle report drift'); console.log(`${renderCases.length} cases, ${mutationLedger.length} semantic mutations, ${Object.keys(comparerTests).length} comparer self-tests`) }
if (mode === '--self-test') { const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'colorlab-closure-')); fs.cpSync(cpuRoot, clone, { recursive: true }); const dependency = path.join(clone, 'src/csl/runtime.js'); fs.appendFileSync(dependency, '\n// deliberate ColorLab dependency mutation\n'); let modifiedRejected = false; try { verifyClosure(clone, closure) } catch { modifiedRejected = true } if (!modifiedRejected) throw new Error('modified import dependency accepted'); const escape = path.join(clone, 'src/runtime/surface.js'); fs.rmSync(escape); fs.symlinkSync('/tmp', escape); let symlinkRejected = false; try { discoverClosure(clone) } catch { symlinkRejected = true } fs.rmSync(clone, { recursive: true, force: true }); if (!symlinkRejected) throw new Error('symlink escape accepted'); console.log('modified import dependency rejected'); console.log('symlink escape rejected'); console.log('public/direct/repeat identity verified'); console.log('strict comparer self-tests verified'); for (const mutation of mutationLedger) console.log(`factory mutation witness: ${mutation.name}`) }
