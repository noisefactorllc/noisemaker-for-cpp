#!/usr/bin/env node
// Authenticated filter/osd pixel oracle. This package is intentionally
// independent of typed-kernel generation and never edits generated outputs.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'osd-oracles.json')
const reportPath = path.join(here, 'osd-oracle-report.md')
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/osd/osd.glsl'
const sourcePath = path.join(cppRoot, sourceRelative)
const programKey = 'filter/osd:osd'
const authorityNode = 'v24.7.0'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const factoryName = 'canonicalFactory94'
const factoryBytesExpected = 5894
const factoryShaExpected = '9920f7a4d629d468a2d9ac8cbe319d28d385bd9561c06bb0772e5ce6204f528b'
const sourceBytesExpected = 6164
const sourceShaExpected = 'c45adaf30ecef6fb7f83a4f3995e671df0caaa47bfeceba8bb9bfe2c07427443'

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
  const leaf = path.resolve(candidate)
  try { if (fs.lstatSync(leaf).isSymbolicLink()) throw new Error(`${label} must not be a symlink: ${candidate}`) }
  catch (error) { if (error?.code === 'ENOENT') return; throw error }
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
    const file = stack.pop()
    if (closure.has(file)) continue
    const text = fs.readFileSync(file, 'utf8')
    dynamicPattern.lastIndex = 0
    let dynamic = dynamicPattern.exec(text)
    while (dynamic) {
      const literal = dynamic[1].trim()
      if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) throw new Error(`nonliteral dynamic import in ${path.relative(root, file)}`)
      enqueue(literal.slice(1, -1), file)
      dynamic = dynamicPattern.exec(text)
    }
    closure.set(file, sha256(Buffer.from(text)))
    for (const pattern of importPatterns) {
      pattern.lastIndex = 0
      let match = pattern.exec(text)
      while (match) { enqueue(match[1], file); match = pattern.exec(text) }
    }
  }
  return [...closure.entries()].map(([file, digest]) => ({ relative_path: path.relative(root, file), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
}
function verifyClosure(root, expected = expectedClosure) {
  const actual = discoverClosure(root)
  const expectedRecords = expected.map(([relative_path, digest]) => ({ relative_path, sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
  if (JSON.stringify(actual) !== JSON.stringify(expectedRecords)) throw new Error(`CPU import closure mismatch: expected ${expectedRecords.length}, found ${actual.length}`)
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
for (const [index, token] of argv.entries()) if (index !== cpuRootIndex && index !== cpuRootIndex + 1 && token !== mode) throw new Error(`unexpected argument: ${token}`)
const cpuRootArgument = argv[cpuRootIndex + 1]
rejectSymlinkLeaf(cpuRootArgument, '--cpu-root')
if (!fs.existsSync(cpuRootArgument) || !fs.statSync(cpuRootArgument).isDirectory()) throw new Error(`--cpu-root is not a directory: ${cpuRootArgument}`)
const cpuRoot = fs.realpathSync(cpuRootArgument)
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
if (!liveCpuCheckout || !fs.existsSync(liveCpuCheckout) || !fs.statSync(liveCpuCheckout).isDirectory()) throw new Error(`live noisemaker-for-cpu checkout does not exist: ${liveCpuCheckout ?? '<unset>'}`)
rejectSymlinkLeaf(liveCpuCheckout, 'NOISEMAKER_FOR_CPU')
const liveCpuReal = fs.realpathSync(liveCpuCheckout)
if (beneath(liveCpuReal, cpuRoot) || beneath(cpuRoot, liveCpuReal)) throw new Error('--cpu-root must be an immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')
verifyClosure(cpuRoot)

const load = (relative) => import(pathToFileURL(confine(cpuRoot, path.join(cpuRoot, relative), 'load')).href)
const { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { UPSTREAM_REVISION } = await load('src/effects/generated/upstream-snapshot.js')
const { createCanonicalBindings } = await load('src/csl/glsl-kernel.js')
const { bindGlslKernel } = await load('src/csl/glsl-runtime.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
if (process.version !== authorityNode || UPSTREAM_REVISION !== upstreamRevisionExpected) throw new Error('OSD authority drift')
const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== factoryName || Buffer.byteLength(canonicalText) !== factoryBytesExpected || sha256(canonicalText) !== factoryShaExpected) throw new Error('canonical OSD factory drift')
if (publicFactory !== canonicalFactory) throw new Error('public OSD factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('OSD adapter override present')
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceShaExpected) throw new Error('OSD source provenance drift')

const f32 = Math.fround
const bindingAbi = { inputTex: 'sampler2D', resolution: 'Vec2', tileOffset: 'Vec2', fullResolution: 'Vec2', renderScale: 'number', alpha: 'number', seed: 'number', speed: 'number', time: 'number', corner: 'int32' }
const sourceUniformAbi = { inputTex: 'sampler2D', resolution: 'vec2', tileOffset: 'vec2', fullResolution: 'vec2', renderScale: 'float', alpha: 'float', seed: 'float', speed: 'float', time: 'float', corner: 'int' }
const cases = [
  { name: 'alpha-zero', width: 4, height: 3, renderScale: 1, alpha: 0, seed: 1, speed: 0, time: 0, corner: 3, tileOffset: [0, 0], fullResolution: [4, 3], phase: 1 },
  { name: 'corner-top-left', width: 64, height: 48, renderScale: 1, alpha: .75, seed: 1, speed: 0, time: 0, corner: 0, tileOffset: [0, 0], fullResolution: [64, 48], phase: 2 },
  { name: 'corner-top-right', width: 64, height: 48, renderScale: 1, alpha: .75, seed: 4, speed: 1, time: .25, corner: 1, tileOffset: [0, 0], fullResolution: [64, 48], phase: 3 },
  { name: 'corner-bottom-left', width: 64, height: 48, renderScale: 1, alpha: .5, seed: 7, speed: 2, time: .5, corner: 2, tileOffset: [0, 0], fullResolution: [64, 48], phase: 4 },
  { name: 'corner-bottom-right', width: 64, height: 48, renderScale: 1, alpha: 1, seed: 17, speed: 3, time: .75, corner: 3, tileOffset: [0, 0], fullResolution: [64, 48], phase: 5 },
  { name: 'fallback-tile', width: 24, height: 20, renderScale: 1, alpha: .8, seed: 23, speed: .75, time: .44, corner: 3, tileOffset: [4, 3], fullResolution: [0, 0], phase: 6 },
  { name: 'scaled-glyph-hash', width: 160, height: 120, renderScale: 2, alpha: .65, seed: 99, speed: 5, time: .33, corner: 3, tileOffset: [2, 1], fullResolution: [160, 120], phase: 7 },
]

function inputSurface(definition) {
  const data = new Float32Array(definition.width * definition.height * 4)
  for (let i = 0; i < data.length; i += 4) {
    const p = i / 4; const x = p % definition.width; const y = Math.floor(p / definition.width)
    data[i] = f32(((x * 17 + y * 11 + definition.phase) % 23) / 22)
    data[i + 1] = f32(((x * 7 + y * 19 + definition.phase * 2) % 29) / 28)
    data[i + 2] = f32(((x * 13 + y * 5 + definition.phase * 3) % 31) / 30)
    data[i + 3] = f32(.4 + ((x + y + definition.phase) % 5) / 10)
  }
  return new Surface(definition.width, definition.height, data)
}
function inputFixture(definition) {
  const surface = inputSurface(definition)
  const data = new Uint8Array(surface.toRgba8())
  return { phase: definition.phase, f32_words_le: Array.from(words(surface.data), u32Hex), f32_sha256: sha256(bytes(surface.data)), rgba8_bytes: Array.from(data), rgba8_sha256: sha256(data) }
}
function render(factory, definition) {
  const inputTex = inputSurface(definition)
  const before = new Uint32Array(words(inputTex.data))
  const output = new Surface(definition.width, definition.height)
  const bindings = createCanonicalBindings({ width: definition.width, height: definition.height, time: f32(definition.time), seed: definition.seed, uniforms: { alpha: f32(definition.alpha), corner: definition.corner, speed: f32(definition.speed), renderScale: f32(definition.renderScale) }, textures: { inputTex }, tileOffset: new Float32Array(definition.tileOffset.map(f32)), fullResolution: new Float32Array(definition.fullResolution.map(f32)) })
  const kernel = bindGlslKernel(factory, bindings)
  runPass({ kernel, destination: output, time: definition.time, seed: definition.seed })
  const after = words(inputTex.data)
  if (before.some((word, index) => word !== after[index])) throw new Error(`${definition.name}: input mutated`)
  return { output, input: inputTex, inputImmutable: true, inputLifetimeStable: true }
}
function compare(reference, candidate) {
  const left = words(reference.data); const right = words(candidate.data)
  const dimensionsMatch = reference.width === candidate.width && reference.height === candidate.height
  const laneCountMatch = left.length === right.length
  let mismatchedLanes = Math.abs(left.length - right.length); let firstMismatch = null
  const common = Math.min(left.length, right.length)
  for (let i = 0; i < common; i += 1) if (left[i] !== right[i]) { mismatchedLanes += 1; if (!firstMismatch) firstMismatch = { lane_index: i, bits_reference: u32Hex(left[i]), bits_candidate: u32Hex(right[i]) } }
  const leftBytes = new Uint8Array(reference.toRgba8()); const rightBytes = new Uint8Array(candidate.toRgba8())
  const rgbaCountMatch = leftBytes.length === rightBytes.length
  let mismatchedBytes = Math.abs(leftBytes.length - rightBytes.length); let firstRgbaMismatch = null
  const commonBytes = Math.min(leftBytes.length, rightBytes.length)
  for (let i = 0; i < commonBytes; i += 1) if (leftBytes[i] !== rightBytes[i]) { mismatchedBytes += 1; if (!firstRgbaMismatch) firstRgbaMismatch = { byte_index: i, byte_reference: leftBytes[i], byte_candidate: rightBytes[i] } }
  return { exact: dimensionsMatch && laneCountMatch && mismatchedLanes === 0 && rgbaCountMatch && mismatchedBytes === 0, dimensions_match: dimensionsMatch, lane_count_match: laneCountMatch, mismatched_lanes: mismatchedLanes, exact_f32_bits: dimensionsMatch && laneCountMatch && mismatchedLanes === 0, rgba8_count_match: rgbaCountMatch, mismatched_bytes: mismatchedBytes, exact_rgba8_bytes: rgbaCountMatch && mismatchedBytes === 0, first_mismatch: firstMismatch, first_rgba8_mismatch: firstRgbaMismatch }
}
function fakeSurface(width, height, wordsList, rgba) {
  const bytesView = Uint8Array.from(rgba)
  const data = new Float32Array(new Uint32Array(wordsList).buffer)
  return { width, height, data, toRgba8: () => bytesView }
}
function comparerSelfTests() {
  const good = compare(fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]), fakeSurface(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]))
  const dimensions = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(2, 1, [0, 0, 0, 0], [0, 0, 0, 0]))
  const short = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0], [0, 0, 0, 0]))
  const long = compare(fakeSurface(1, 1, [0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]))
  const rgba = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0, 0, 0, 0], [1, 0, 0, 0]))
  const signedZero = compare(fakeSurface(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x80000000, 0, 0, 0], [0, 0, 0, 0]))
  const nanPayload = compare(fakeSurface(1, 1, [0x7fc00001, 0, 0, 0], [0, 0, 0, 0]), fakeSurface(1, 1, [0x7fc00002, 0, 0, 0], [0, 0, 0, 0]))
  return { good_equal: good.exact, dimensions_mismatch: !dimensions.exact && !dimensions.dimensions_match, short_lane_count: !short.exact && !short.lane_count_match, long_lane_count: !long.exact && !long.lane_count_match, rgba8_mismatch: !rgba.exact && !rgba.exact_rgba8_bytes, signed_zero_rejected: !signedZero.exact && !signedZero.exact_f32_bits, nan_payload_rejected: !nanPayload.exact && !nanPayload.exact_f32_bits }
}

const comparerTests = comparerSelfTests()
if (!Object.values(comparerTests).every(Boolean)) throw new Error('strict comparer self-tests failed')
const referenceSurfaces = new Map()
const renderCases = cases.map((definition) => {
  const first = render(canonicalFactory, definition)
  const second = render(publicFactory, definition)
  const repeat = compare(first.output, second.output)
  if (!repeat.exact) throw new Error(`${definition.name}: public/direct/repeat mismatch`)
  const fixture = inputFixture(definition)
  const outputBytes = new Uint8Array(first.output.toRgba8())
  referenceSurfaces.set(definition.name, first.output)
  return { name: definition.name, width: definition.width, height: definition.height, controls: { renderScale: definition.renderScale, alpha: definition.alpha, seed: definition.seed, speed: definition.speed, time: definition.time, corner: definition.corner, tileOffset: definition.tileOffset, fullResolution: definition.fullResolution }, input: fixture, output_f32_words_le: Array.from(words(first.output.data), u32Hex), output_f32_sha256: sha256(bytes(first.output.data)), output_rgba8_bytes: Array.from(outputBytes), output_rgba8_sha256: sha256(outputBytes), input_immutable_exact_bits: first.inputImmutable, input_lifetime_stable: first.inputLifetimeStable, public_direct_repeat_exact: repeat.exact }
})

const mutations = [
  { name: 'alpha-control-axis', anchor: 'var blend_alpha = clamp(alpha, 0, 1);', replacement: 'var blend_alpha = 1;' , witnesses: ['corner-bottom-left'] },
  { name: 'glyph-digit-index', anchor: 'var digit = digit_hash % 10|0;', replacement: 'var digit = 8;', witnesses: ['scaled-glyph-hash'] },
  { name: 'bitwise-scanline-mask', anchor: 'var scanline = 1 - (0.029999999329447746 * blend_alpha) * (cpu_float((globalCoord[1] / scanlineStep) & 1));', replacement: 'var scanline = 1 - (0.029999999329447746 * blend_alpha) * 0;', witnesses: ['corner-bottom-right'] },
  { name: 'panel-pad-geometry', anchor: 'var panel_pad = GAP * 2;', replacement: 'var panel_pad = GAP;', witnesses: ['corner-bottom-right'] },
  { name: 'tile-offset', anchor: 'var globalCoord = ivec2.add([], coord, cpu_ivec2_vec2(tileOffset));', replacement: 'var globalCoord = coord;', witnesses: ['fallback-tile'] },
  { name: 'texel-fetch-coordinate', anchor: 'var texel = texelFetch(inputTex, coord, 0);', replacement: 'var texel = texelFetch(inputTex, texDims, 0);', witnesses: ['corner-bottom-right'] },
]
function compileFactory(text) { return Function(`return (${text})`)() }
const mutationLedger = mutations.map((mutation) => {
  if (!canonicalText.includes(mutation.anchor)) throw new Error(`mutation anchor absent: ${mutation.name}`)
  const mutatedText = canonicalText.replace(mutation.anchor, mutation.replacement)
  const factory = compileFactory(mutatedText)
  const requiredResults = mutation.witnesses.map((name) => {
    const definition = cases.find((item) => item.name === name)
    const mutated = render(factory, definition).output
    const result = compare(referenceSurfaces.get(name), mutated)
    if (result.mismatched_lanes === 0 || result.mismatched_bytes === 0) throw new Error(`${mutation.name}: witness ${name} is not divergent`)
    return { case: name, mismatched_lanes: result.mismatched_lanes, mismatched_bytes: result.mismatched_bytes, first_mismatch: result.first_mismatch, first_rgba8_mismatch: result.first_rgba8_mismatch }
  })
  return { name: mutation.name, anchor_text: mutation.anchor, replacement_text: mutation.replacement, anchor_sha256: sha256(Buffer.from(mutation.anchor)), replacement_sha256: sha256(Buffer.from(mutation.replacement)), mutated_factory_sha256: sha256(Buffer.from(mutatedText)), required_witnesses: mutation.witnesses, required_witness_results: requiredResults }
})

const sourceFunction = Function.prototype.toString.call(inputSurface)
const document = {
  schema: 'noisemaker-for-cpp.osd.pixel-parity.v1', program_key: programKey,
  provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source_relative: sourceRelative, source_bytes: sourceBytesExpected, source_sha256: sourceShaExpected, factory_name: factoryName, factory_bytes: factoryBytesExpected, factory_sha256: factoryShaExpected, import_closure: verifyClosure(cpuRoot) },
  factory: { name: factoryName, text_sha256: factoryShaExpected, public_direct_identity: publicFactory === canonicalFactory, adapter_override: false },
  source_uniform_abi: sourceUniformAbi, runtime_binding_abi: bindingAbi,
  input_fixture: { schema: 'noisemaker-for-cpp.osd.input-texture.v1', source_function: 'inputSurface', source_function_sha256: sha256(Buffer.from(sourceFunction)), coordinate_order: 'x-fastest row-major', component_order: ['r', 'g', 'b', 'a'], formulas: ['f32(((x * 17 + y * 11 + phase) % 23) / 22)', 'f32(((x * 7 + y * 19 + phase * 2) % 29) / 28)', 'f32(((x * 13 + y * 5 + phase * 3) % 31) / 30)', 'f32(.4 + ((x + y + phase) % 5) / 10)'] },
  render_cases: renderCases, comparer_self_tests: comparerTests,
  behavioral_mutation_ledger: mutationLedger,
  mutation_contract: { behavioral_names: mutations.map((item) => item.name), witnesses: Object.fromEntries(mutations.map((item) => [item.name, item.witnesses])) },
}
rejectAbsolute(document)
const serialized = `${JSON.stringify(document, null, 2)}\n`
const report = `# OSD pixel oracle\n\nThis package freezes the canonical \`filter/osd:osd\` factory from the immutable CPU authority. It covers four corner modes, alpha-zero early return, full-resolution fallback with tile offset, renderScale, glyph hash/indexing, integer texture fetch, scanline bitwise masking, and panel geometry.\n\n- Schema: \`${document.schema}\`\n- Cases: ${renderCases.length}\n- Behavioral mutations: ${mutationLedger.length}; every mutation has an actual float32 and RGBA8 witness.\n- Float32 comparison is exact little-endian word equality; RGBA8 comparison is exact byte equality.\n- Run with: \`node osd_oracle_generator.mjs --check --cpu-root \$NOISEMAKER_CPU_ROOT\`\n- Materialize with: \`python3 -B tools/glslcpp/generate_osd_native_oracle_include.py --check\`\n\nThe input fixture is source-bound by function text hash and frozen independently as Float32 words and RGBA8 bytes. The input Surface is checked for exact bitwise immutability and retained across repeat renders.\n`
function writeChecked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(sidecarPath(target), sidecarText(target, payload)) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); writeChecked(outputPath, Buffer.from(serialized)); writeChecked(reportPath, Buffer.from(report)); const generatorPath = fileURLToPath(import.meta.url); fs.writeFileSync(sidecarPath(generatorPath), sidecarText(generatorPath, fs.readFileSync(generatorPath))); console.log(`${renderCases.length} cases, ${mutationLedger.length} behavioral mutations written`) }
else { const existing = verifySidecar(outputPath).toString('utf8'); const existingReport = verifySidecar(reportPath).toString('utf8'); if (existing !== serialized) throw new Error('OSD oracle JSON drift; run --write only with authority approval'); if (existingReport !== report) throw new Error('OSD oracle report drift'); console.log(`${renderCases.length} cases, ${mutationLedger.length} behavioral mutations, ${Object.keys(comparerTests).length} strict comparer self-tests`) }

if (mode === '--self-test') {
  const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'osd-oracle-'))
  fs.cpSync(cpuRoot, clone, { recursive: true })
  const dependency = path.join(clone, 'src/csl/runtime.js')
  fs.appendFileSync(dependency, '\n// deliberate OSD oracle dependency mutation\n')
  let modifiedRejected = false
  try { verifyClosure(clone) } catch { modifiedRejected = true }
  if (!modifiedRejected) throw new Error('modified import dependency accepted')
  let missingRejected = false
  try { verifyClosure(cpuRoot, expectedClosure.slice(0, -1)) } catch { missingRejected = true }
  if (!missingRejected) throw new Error('missing import-closure entry accepted')
  fs.rmSync(clone, { recursive: true, force: true })
  console.log('modified import dependency rejected')
  console.log('missing import-closure entry rejected')
  console.log('public/direct/repeat identity verified')
  console.log('strict comparer self-tests verified')
  for (const mutation of mutationLedger) console.log(`factory mutation witness: ${mutation.name}`)
}
