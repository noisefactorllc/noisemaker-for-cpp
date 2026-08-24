#!/usr/bin/env node
// Authenticated pixel oracle for the CPU Palette adapter.  This package is
// independent of the C++ generator and never edits generated artifacts.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'palette-oracles.json')
const reportPath = path.join(here, 'palette-oracle-report.md')
const programKey = 'filter/palette:palette'
const authorityNode = 'v24.7.0'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const factoryName = 'paletteFactory'
const factoryBytesExpected = 1408
const factoryShaExpected = '547bb6741b27cc12d6ed488cd1bbe12284ab3b916cdaefe1c747a63125523040'
const sourceRelative = 'src/effects/adapters/palette.js'
const sourceBytesExpected = 5283
const sourceShaExpected = '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'

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

const entryFiles = [
  'src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js',
  'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js',
  'src/runtime/pass-runner.js', 'src/runtime/surface.js',
]
const importPatterns = [(/\bfrom\s*['"]([^'"\n]+)['"]/g), (/^[ \t]*import\s+['"]([^'"\n]+)['"]/gm)]
const dynamicPattern = /\bimport\s*\(([^)]*)\)/g
function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function words(view) { return new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function f32Words(values) { const data = new Float32Array(values.map(f32)); return Array.from(words(data), u32Hex) }
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function verifySidecar(target) {
  const sidecar = sidecarPath(target)
  if (!fs.existsSync(target) || !fs.existsSync(sidecar)) throw new Error(`missing sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecar, 'utf8') !== sidecarText(target, payload)) throw new Error(`sidecar drift: ${target}`)
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
  const closure = new Map()
  const stack = entryFiles.map((entry) => confine(root, path.join(root, entry), 'entry'))
  const enqueue = (specifier, file) => {
    if (specifier.startsWith('node:')) return
    if (!specifier.startsWith('./') && !specifier.startsWith('../')) throw new Error(`bare module specifier ${specifier}`)
    stack.push(confine(root, path.resolve(path.dirname(file), specifier), path.relative(root, file)))
  }
  while (stack.length) {
    const file = stack.pop(); if (closure.has(file)) continue
    const text = fs.readFileSync(file, 'utf8')
    dynamicPattern.lastIndex = 0; let dynamic = dynamicPattern.exec(text)
    while (dynamic) {
      const literal = dynamic[1].trim()
      if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) throw new Error(`nonliteral dynamic import in ${path.relative(root, file)}`)
      enqueue(literal.slice(1, -1), file); dynamic = dynamicPattern.exec(text)
    }
    closure.set(file, sha256(Buffer.from(text)))
    for (const pattern of importPatterns) {
      pattern.lastIndex = 0; let match = pattern.exec(text)
      while (match) { enqueue(match[1], file); match = pattern.exec(text) }
    }
  }
  return [...closure.entries()].map(([file, digest]) => ({ relative_path: path.relative(root, file), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
}
function verifyClosure(root, expected = expectedClosure) {
  const actual = discoverClosure(root)
  const wanted = expected.map(([relative_path, digest]) => ({ relative_path, sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) throw new Error(`CPU import closure mismatch: expected ${wanted.length}, found ${actual.length}`)
  return actual
}
function rejectAbsolute(value, label = 'oracle') {
  if (typeof value === 'string') {
    if (value.startsWith('/') || /(?:^|[\\/])(Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute path serialized`)
  } else if (Array.isArray(value)) value.forEach((entry, index) => rejectAbsolute(entry, `${label}[${index}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, entry]) => rejectAbsolute(entry, `${label}.${key}`))
}

const argv = process.argv.slice(2)
const modes = argv.filter((token) => ['--write', '--check', '--self-test'].includes(token))
if (modes.length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const mode = modes[0]
const cpuRootIndex = argv.indexOf('--cpu-root')
if (cpuRootIndex < 0 || cpuRootIndex + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
const cpuRootArgument = argv[cpuRootIndex + 1]
rejectSymlinkLeaf(cpuRootArgument, '--cpu-root')
if (!fs.existsSync(cpuRootArgument) || !fs.statSync(cpuRootArgument).isDirectory()) throw new Error('--cpu-root is not a directory')
const cpuRoot = fs.realpathSync(cpuRootArgument)
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
if (!liveCpuCheckout || !fs.existsSync(liveCpuCheckout)) throw new Error(`live noisemaker-for-cpu checkout does not exist: ${liveCpuCheckout ?? '<unset>'}`)
rejectSymlinkLeaf(liveCpuCheckout, 'NOISEMAKER_FOR_CPU')
const liveCpuReal = fs.realpathSync(liveCpuCheckout)
if (beneath(liveCpuReal, cpuRoot) || beneath(cpuRoot, liveCpuReal) || beneath(cppRoot, cpuRoot)) throw new Error('authority must be an immutable external snapshot')
verifyClosure(cpuRoot)

const load = (relative) => import(pathToFileURL(confine(cpuRoot, path.join(cpuRoot, relative), 'load')).href)
const { canonicalAdapterFactories, kernelFactories } = await load('src/effects/catalog.js')
const { UPSTREAM_REVISION } = await load('src/effects/generated/upstream-snapshot.js')
const { createCanonicalBindings } = await load('src/csl/glsl-kernel.js')
const { bindGlslKernel } = await load('src/csl/glsl-runtime.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
if (process.version !== authorityNode || UPSTREAM_REVISION !== upstreamRevisionExpected) throw new Error('Palette authority drift')
const canonicalFactory = canonicalAdapterFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== factoryName || Buffer.byteLength(canonicalText) !== factoryBytesExpected || sha256(canonicalText) !== factoryShaExpected) throw new Error('Palette factory drift')
if (publicFactory !== canonicalFactory) throw new Error('Palette public/direct factory identity drift')
const sourceBytes = fs.readFileSync(path.join(cpuRoot, sourceRelative))
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceShaExpected) throw new Error('Palette source provenance drift')

const f32 = Math.fround
const runtimeBindingAbi = { inputTex: 'sampler2D', tileOffset: 'Vec2', fullResolution: 'Vec2', paletteIndex: 'int32', rotation: 'int32', offset: 'number', repeat: 'number', alpha: 'number', time: 'number' }
const sourceUniformAbi = { inputTex: 'sampler2D', tileOffset: 'vec2', fullResolution: 'vec2', paletteIndex: 'int', rotation: 'int', offset: 'float', repeat: 'float', alpha: 'float', time: 'float' }
const cases = [
  { name: 'passthrough-zero', width: 4, height: 3, paletteIndex: 0, rotation: 0, offset: 0, repeat: 1, alpha: 1, time: 0, tileOffset: [0, 0], fullResolution: [4, 3], phase: 1 },
  { name: 'passthrough-negative', width: 3, height: 2, paletteIndex: -2, rotation: 0, offset: 9, repeat: 2, alpha: .5, time: .3, tileOffset: [2, 1], fullResolution: [20, 18], phase: 2 },
  { name: 'rgb-alpha-zero', width: 8, height: 6, paletteIndex: 7, rotation: 0, offset: 0, repeat: 1, alpha: 0, time: 0, tileOffset: [0, 0], fullResolution: [8, 6], phase: 3 },
  { name: 'rgb-alpha-full', width: 8, height: 6, paletteIndex: 7, rotation: 0, offset: 37, repeat: 3, alpha: 1, time: 0, tileOffset: [4, 2], fullResolution: [64, 48], phase: 4 },
  { name: 'hsv-backward', width: 7, height: 5, paletteIndex: 12, rotation: -1, offset: 13, repeat: 2, alpha: .65, time: .42, tileOffset: [3, 1], fullResolution: [40, 30], phase: 5 },
  { name: 'hsv-forward', width: 7, height: 5, paletteIndex: 16, rotation: 1, offset: 73, repeat: 4, alpha: .8, time: .71, tileOffset: [1, 4], fullResolution: [32, 32], phase: 6 },
  { name: 'oklab', width: 9, height: 4, paletteIndex: 40, rotation: 0, offset: 25, repeat: 1, alpha: .9, time: .2, tileOffset: [5, 7], fullResolution: [80, 40], phase: 7 },
  { name: 'last-entry', width: 5, height: 4, paletteIndex: 55, rotation: -1, offset: 99, repeat: 10, alpha: .35, time: 1.2, tileOffset: [9, 6], fullResolution: [100, 80], phase: 8 },
]
function inputSurface(definition) {
  const data = new Float32Array(definition.width * definition.height * 4)
  for (let i = 0; i < data.length; i += 4) {
    const p = i / 4; const x = p % definition.width; const y = Math.floor(p / definition.width)
    data[i] = f32(((x * 17 + y * 11 + definition.phase) % 23) / 22)
    data[i + 1] = f32(((x * 7 + y * 19 + definition.phase * 2) % 29) / 28)
    data[i + 2] = f32(((x * 13 + y * 5 + definition.phase * 3) % 31) / 30)
    data[i + 3] = f32(.2 + ((x + y + definition.phase) % 7) / 10)
  }
  return new Surface(definition.width, definition.height, data)
}
function fixture(definition) {
  const input = inputSurface(definition); const rgba = new Uint8Array(input.toRgba8())
  return { f32_words_le: Array.from(words(input.data), u32Hex), f32_sha256: sha256(bytes(input.data)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha256(rgba) }
}
function render(factory, definition) {
  const inputTex = inputSurface(definition); const before = new Uint32Array(words(inputTex.data)); const output = new Surface(definition.width, definition.height)
  const bindings = createCanonicalBindings({ width: definition.width, height: definition.height, time: f32(definition.time), uniforms: { paletteIndex: definition.paletteIndex, rotation: definition.rotation, offset: f32(definition.offset), repeat: f32(definition.repeat), alpha: f32(definition.alpha) }, textures: { inputTex }, tileOffset: new Float32Array(definition.tileOffset.map(f32)), fullResolution: new Float32Array(definition.fullResolution.map(f32)) })
  const kernel = bindGlslKernel(factory, bindings); runPass({ kernel, destination: output, time: definition.time, seed: definition.phase })
  const after = words(inputTex.data); if (before.some((word, index) => word !== after[index])) throw new Error(`${definition.name}: input mutated`)
  return { output, inputImmutable: true, inputLifetimeStable: true }
}
function compare(reference, candidate) {
  const dimensions = reference.width === candidate.width && reference.height === candidate.height
  if (!dimensions) return { exact: false, dimensions_match: false, lane_count_match: false, mismatched_lanes: 0, mismatched_bytes: 0, first_mismatch: null, first_rgba8_mismatch: null }
  const left = words(reference.data), right = words(candidate.data); const lanes = left.length === right.length
  let mismatchedLanes = Math.abs(left.length - right.length), firstMismatch = null; for (let i = 0; i < Math.min(left.length, right.length); i += 1) if (left[i] !== right[i]) { mismatchedLanes += 1; if (!firstMismatch) firstMismatch = { lane_index: i, reference: u32Hex(left[i]), candidate: u32Hex(right[i]) } }
  const lb = new Uint8Array(reference.toRgba8()), rb = new Uint8Array(candidate.toRgba8()); const byteCount = lb.length === rb.length; let mismatchedBytes = Math.abs(lb.length - rb.length), firstByteMismatch = null
  for (let i = 0; i < Math.min(lb.length, rb.length); i += 1) if (lb[i] !== rb[i]) { mismatchedBytes += 1; if (!firstByteMismatch) firstByteMismatch = { byte_index: i, reference: lb[i], candidate: rb[i] } }
  return { exact: dimensions && lanes && mismatchedLanes === 0 && byteCount && mismatchedBytes === 0, dimensions_match: dimensions, lane_count_match: lanes, mismatched_lanes: mismatchedLanes, mismatched_bytes: mismatchedBytes, first_mismatch: firstMismatch, first_rgba8_mismatch: firstByteMismatch }
}
function fakeSurface(width, height, list, rgba) { return { width, height, data: new Float32Array(new Uint32Array(list).buffer), toRgba8: () => Uint8Array.from(rgba) } }
function hostileDimensionGuard() {
  const hostile = { width: 1, height: 1, get data() { throw new Error('lane access before dimension check') }, toRgba8() { throw new Error('rgba access before dimension check') } }
  const other = { width: 2, height: 1, get data() { throw new Error('other lane access before dimension check') }, toRgba8() { throw new Error('other rgba access before dimension check') } }
  return !compare(hostile, other).exact
}
function comparerSelfTests() {
  const good = compare(fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]), fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]))
  const dimensions = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(2, 1, [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]))
  const short = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0], [0, 0, 0, 0]))
  const rgba = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0, 0], [1, 0, 0, 0]))
  const signedZero = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x80000000, 0, 0, 0], [0, 0, 0, 0]))
  const nanPayload = compare(fakeSurface(1, 1, [0x7fc00001, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x7fc00002, 0, 0, 0], [0, 0, 0, 0]))
  return { good_equal: good.exact, dimensions_mismatch: !dimensions.exact && !dimensions.dimensions_match, short_lane_count: !short.exact && !short.lane_count_match, rgba8_mismatch: !rgba.exact && rgba.mismatched_bytes > 0, signed_zero: !signedZero.exact && signedZero.mismatched_lanes > 0, nan_payload: !nanPayload.exact && nanPayload.mismatched_lanes > 0 }
}
const comparerTests = comparerSelfTests(); if (!Object.values(comparerTests).every(Boolean)) throw new Error('Palette strict comparer self-tests failed')
if (!hostileDimensionGuard()) throw new Error('Palette hostile dimension guard failed')
const referenceSurfaces = new Map()
const renderCases = cases.map((definition) => {
  const first = render(canonicalFactory, definition); const second = render(publicFactory, definition); const repeat = compare(first.output, second.output); if (!repeat.exact) throw new Error(`${definition.name}: direct/public mismatch`)
  const rgba = new Uint8Array(first.output.toRgba8()); const input = fixture(definition); referenceSurfaces.set(definition.name, first.output)
  const bindingWords = { inputTex: { width: definition.width, height: definition.height, f32_words_le: input.f32_words_le, f32_sha256: input.f32_sha256 }, tileOffset: { values: definition.tileOffset, f32_words_le: f32Words(definition.tileOffset) }, fullResolution: { values: definition.fullResolution, f32_words_le: f32Words(definition.fullResolution) }, paletteIndex: { value: definition.paletteIndex, int32: definition.paletteIndex | 0, f32_words_le: f32Words([definition.paletteIndex]) }, rotation: { value: definition.rotation, int32: definition.rotation | 0, f32_words_le: f32Words([definition.rotation]) }, offset: { value: definition.offset, f32_words_le: f32Words([definition.offset]) }, repeat: { value: definition.repeat, f32_words_le: f32Words([definition.repeat]) }, alpha: { value: definition.alpha, f32_words_le: f32Words([definition.alpha]) }, time: { value: definition.time, f32_words_le: f32Words([definition.time]) } }
  return { name: definition.name, width: definition.width, height: definition.height, bindings: { paletteIndex: definition.paletteIndex, rotation: definition.rotation, offset: definition.offset, repeat: definition.repeat, alpha: definition.alpha, time: definition.time, tileOffset: definition.tileOffset, fullResolution: definition.fullResolution }, binding_words: bindingWords, input, expected: { f32_words_le: Array.from(words(first.output.data), u32Hex), f32_sha256: sha256(bytes(first.output.data)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha256(rgba) }, input_immutable_exact_bits: first.inputImmutable, input_lifetime_stable: first.inputLifetimeStable, repeat_output_object_distinct: true, repeat_output_data_distinct: first.output.data !== second.output.data }})
const mutations = [
  { name: 'invalid-index-upper-bound', anchor: 'if (paletteIndex <= 0 || paletteIndex > paletteData.length)', replacement: 'if (paletteIndex <= 0 || paletteIndex >= paletteData.length)', witnesses: ['last-entry'] },
  { name: 'palette-index-selection', anchor: 'const entry = paletteData[paletteIndex - 1]', replacement: 'const entry = paletteData[paletteIndex]', witnesses: ['rgb-alpha-full'] },
  { name: 'luminance-red-weight', anchor: 'input[0] * 0.299', replacement: 'input[0] * 0.3', witnesses: ['rgb-alpha-full'] },
  { name: 'luminance-green-weight', anchor: 'input[1] * 0.587', replacement: 'input[1] * 0.58', witnesses: ['rgb-alpha-full'] },
  { name: 'offset-scale', anchor: '$bindings.offset * 0.01', replacement: '$bindings.offset * 0.02', witnesses: ['last-entry'] },
  { name: 'repeat-control', anchor: 'lum * $bindings.repeat', replacement: 'lum * ($bindings.repeat + 1)', witnesses: ['rgb-alpha-full'] },
  { name: 'rotation-backward', anchor: 'if ($bindings.rotation === -1) t += $bindings.time', replacement: 'if ($bindings.rotation === -1) t -= $bindings.time', witnesses: ['hsv-backward'] },
  { name: 'rotation-forward', anchor: 'else if ($bindings.rotation === 1) t -= $bindings.time', replacement: 'else if ($bindings.rotation === 1) t += $bindings.time', witnesses: ['hsv-forward'] },
  { name: 'cosine-frequency', anchor: 'entry[4 + channel] * t', replacement: '(entry[4 + channel] + 1) * t', witnesses: ['rgb-alpha-full'] },
  { name: 'hsv-mode-route', anchor: 'if (mode === 1) hsvToRgb', replacement: 'if (mode === 99) hsvToRgb', witnesses: ['hsv-backward'] },
  { name: 'oklab-mode-route', anchor: 'else if (mode === 2) oklabToRgb', replacement: 'else if (mode === 99) oklabToRgb', witnesses: ['oklab'] },
  { name: 'alpha-mix-control', anchor: 'mix(input[0], color[0], alpha)', replacement: 'mix(input[0], color[0], 1)', witnesses: ['rgb-alpha-zero'] },
  { name: 'output-rounding', anchor: 'Math.fround(mix(input[0], color[0], alpha))', replacement: 'Math.fround(mix(input[0], color[0], alpha) + 0.001)', witnesses: ['rgb-alpha-full'] },
]
async function mutatedFactory(mutation) {
  if (!canonicalText.includes(mutation.anchor)) throw new Error(`mutation anchor absent: ${mutation.name}`)
  const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'palette-oracle-')); const adapterDir = path.join(clone, 'src/effects/adapters'); const generatedDir = path.join(clone, 'src/effects/generated'); fs.mkdirSync(adapterDir, { recursive: true }); fs.mkdirSync(generatedDir, { recursive: true }); fs.writeFileSync(path.join(clone, 'package.json'), '{"type":"module"}\n')
  const mutatedText = canonicalText.replace(mutation.anchor, mutation.replacement); const authoritySource = fs.readFileSync(path.join(cpuRoot, sourceRelative), 'utf8'); const mutatedSource = authoritySource.replace(canonicalText, mutatedText); fs.writeFileSync(path.join(adapterDir, 'palette.js'), mutatedSource); fs.copyFileSync(path.join(cpuRoot, 'src/effects/generated/canonical-adapter-data.js'), path.join(generatedDir, 'canonical-adapter-data.js'))
  const loaded = await import(`${pathToFileURL(path.join(adapterDir, 'palette.js')).href}?mutation=${encodeURIComponent(mutation.name)}`)
  if (typeof loaded.paletteFactory !== 'function') throw new Error(`mutated Palette module exports: ${Object.keys(loaded).join(',')}`)
  return { factory: loaded.paletteFactory, text: mutatedText, cleanup: () => fs.rmSync(clone, { recursive: true, force: true }) }
}
const mutationLedger = []
for (const mutation of mutations) {
  const loaded = await mutatedFactory(mutation); const requiredWitnessResults = []
  for (const name of mutation.witnesses) { const definition = cases.find((item) => item.name === name); const result = compare(referenceSurfaces.get(name), render(loaded.factory, definition).output); if (result.mismatched_lanes === 0 || result.mismatched_bytes === 0) throw new Error(`${mutation.name}: witness ${name} did not diverge`); requiredWitnessResults.push({ case: name, mismatched_lanes: result.mismatched_lanes, mismatched_bytes: result.mismatched_bytes, first_mismatch: result.first_mismatch, first_rgba8_mismatch: result.first_rgba8_mismatch }) }
  mutationLedger.push({ name: mutation.name, source_anchor: mutation.anchor, replacement: mutation.replacement, anchor_sha256: sha256(Buffer.from(mutation.anchor)), replacement_sha256: sha256(Buffer.from(mutation.replacement)), mutated_factory_sha256: sha256(Buffer.from(loaded.text)), required_witnesses: mutation.witnesses, required_witness_results: requiredWitnessResults, independent: true }); loaded.cleanup()
}
const document = { schema: 'noisemaker-for-cpp.palette.pixel-parity.v1', program_key: programKey, provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source: { relative_path: sourceRelative, bytes: sourceBytesExpected, sha256: sourceShaExpected }, cpu_snapshot: { import_closure: verifyClosure(cpuRoot), closure_cardinality: expectedClosure.length, immutable_snapshot: true, live_checkout_rejected: true, realpath_containment_checked: true } }, factory: { name: factoryName, text_bytes: factoryBytesExpected, text_sha256: factoryShaExpected, adapter_own_key: true, public_factory_is_direct_identity: publicFactory === canonicalFactory }, runtime_binding_names: Object.keys(runtimeBindingAbi), runtime_binding_abi: runtimeBindingAbi, source_uniform_abi: sourceUniformAbi, render_cases: renderCases, comparer_self_tests: comparerTests, mutation_ledger: mutationLedger, claim_boundaries: { authority: 'frozen noisemaker-for-cpu snapshot', runtime: 'exact float32 words and RGBA8 bytes', input: 'input Surface immutable and retained across repeats' } }
rejectAbsolute(document)
const serialized = `${JSON.stringify(document, null, 2)}\n`
const report = `# Palette pixel oracle\n\nThis package freezes the direct/public filter/palette:palette CPU adapter from an immutable authority snapshot. It covers passthrough, RGB/HSV/OkLab routes, alpha, offset/repeat, both rotation directions, tile metadata, and input immutability.\n\n- Cases: ${renderCases.length}\n- Semantic mutation witnesses: ${mutationLedger.length}\n- Comparison: exact little-endian Float32 words and exact RGBA8 bytes.\n`
function writeChecked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(sidecarPath(target), sidecarText(target, payload)) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); writeChecked(outputPath, Buffer.from(serialized)); writeChecked(reportPath, Buffer.from(report)); writeChecked(fileURLToPath(import.meta.url), fs.readFileSync(fileURLToPath(import.meta.url))); console.log(`${renderCases.length} cases, ${mutationLedger.length} semantic mutations written`) }
else { if (verifySidecar(outputPath).toString('utf8') !== serialized) throw new Error('Palette oracle JSON drift; run --write only with authority approval'); if (verifySidecar(reportPath).toString('utf8') !== report) throw new Error('Palette oracle report drift'); console.log(`${renderCases.length} cases, ${mutationLedger.length} semantic mutations, ${Object.keys(comparerTests).length} strict comparer self-tests`) }
if (mode === '--self-test') {
  const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'palette-closure-')); fs.cpSync(cpuRoot, clone, { recursive: true }); const dependency = path.join(clone, 'src/csl/runtime.js'); fs.appendFileSync(dependency, '\n// deliberate Palette dependency mutation\n'); let rejected = false; try { verifyClosure(clone) } catch { rejected = true } fs.rmSync(clone, { recursive: true, force: true }); if (!rejected) throw new Error('modified import dependency accepted'); let missing = false; try { verifyClosure(cpuRoot, expectedClosure.slice(0, -1)) } catch { missing = true } if (!missing) throw new Error('missing import closure accepted'); console.log('modified import dependency rejected'); console.log('missing import-closure entry rejected'); console.log('public/direct/repeat identity verified'); console.log('strict comparer self-tests verified'); console.log('dimension validation precedes storage access'); for (const mutation of mutationLedger) console.log(`factory mutation witness: ${mutation.name}`)
}
