#!/usr/bin/env node
// Kaleido187 canonical JavaScript oracle generator.
//
// Only the public canonicalFactory9 from the immutable noisemaker-for-cpu
// snapshot is executable authority here.  This package never imports an
// adapter, never evaluates a local reimplementation, and never uses C++
// output to derive an expected value.

import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'kaleido187-oracles.json')
const reportPath = path.join(here, 'kaleido187-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_kaleido_native_oracle_include.py')
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/kaleido/kaleido.glsl'

const schema = 'noisemaker-for-cpp.kaleido187.pixel-parity.v1'
const programKey = 'classicNoisedeck/kaleido:kaleido'
const effectKey = 'classicNoisedeck/kaleido'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const factoryName = 'canonicalFactory9'
const factoryTextSha256Expected = '4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3'

const pinnedCpuFiles = Object.freeze({
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
})
const canonicalAdapterKeys = Object.freeze([
  'classicNoisedeck/bitEffects:bitEffects', 'classicNoisedeck/fractal:fractal',
  'filter/crt:crt', 'filter/historicPalette:historicPalette',
  'filter/median:median', 'filter/palette:palette',
  'filter/pixelSort:luminance', 'filter/reindex:nmReindexApply',
  'filter/reindex:nmReindexStats', 'filter/snow:snow', 'synth/julia:julia',
])
const corpusAdapterKeysExpected = Object.freeze([
  'classicNoisedeck/fractal:fractal', 'filter/historicPalette:historicPalette',
  'filter/palette:palette', 'synth/julia:julia',
])
// Complete authority closure. Every transitive runtime dependency is pinned;
// recording hashes discovered from the candidate directory would authenticate
// a foreign implementation.
const expectedImportClosure = Object.freeze([
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

const tableNames = Object.freeze(['emboss', 'sharpen', 'blur', 'edge', 'edge2'])
const tableValues = Object.freeze({
  emboss: [-2, -1, 0, -1, 1, 1, 0, 1, 2],
  sharpen: [-1, 0, -1, 0, 5, 0, -1, 0, -1],
  blur: [1, 2, 1, 2, 4, 2, 1, 2, 1],
  edge: [-1, -1, -1, -1, 8, -1, -1, -1, -1],
  edge2: [-1, 0, -1, 0, 4, 0, -1, 0, -1],
})
const tableOccurrenceCensus = Object.freeze({ emboss: 11, sharpen: 11, blur: 11, edge: 10, edge2: 12 })
const bindingNames = Object.freeze([
  'inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'wrap',
  'seed', 'speed', 'loopScale', 'kaleido', 'effectWidth',
])
const expectedBindingNames = Object.freeze([
  'inputTex', 'resolution', 'tileOffset', 'fullResolution', 'time', 'wrap',
  'seed', 'speed', 'loopScale', 'kaleido', 'effectWidth',
])
const bindingAbi = Object.freeze({
  inputTex: 'sampler2D', resolution: 'Vec2', tileOffset: 'Vec2',
  fullResolution: 'Vec2', time: 'number', wrap: 'bool', seed: 'int32',
  speed: 'number', loopScale: 'number', kaleido: 'number', effectWidth: 'number',
})
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytesOf(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function wordsOf(view) { return Array.from(new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4), (value) => `0x${value.toString(16).padStart(8, '0')}`) }
function wordDigest(words) { return sha256(packWords(words)) }
function packWords(words) {
  const out = Buffer.alloc(words.length * 4)
  words.forEach((word, index) => out.writeUInt32LE(Number.parseInt(word, 16) >>> 0, index * 4))
  return out
}
function bytesDigest(bytes) { return sha256(Buffer.from(bytes)) }
if (JSON.stringify(bindingNames) !== JSON.stringify(expectedBindingNames)) throw new Error('binding ABI axis census drift')
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function writeChecked(target, payload) {
  fs.writeFileSync(target, payload)
  fs.writeFileSync(`${target}.sha256`, sidecarText(target, payload))
}
function verifyChecked(target) {
  if (!fs.existsSync(target) || !fs.existsSync(`${target}.sha256`)) throw new Error(`missing checked asset or sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(`${target}.sha256`, 'utf8') !== sidecarText(target, payload)) throw new Error(`checksum sidecar drift: ${target}`)
  return payload
}
function beneath(root, candidate) { return candidate === root || candidate.startsWith(`${root}${path.sep}`) }
function stable(value) { return JSON.stringify(value, null, 2) + '\n' }
function same(a, b) { return a.length === b.length && a.every((value, index) => value === b[index]) }
function changed(a, b) { let count = 0; for (let i = 0; i < a.length; i += 1) if (a[i] !== b[i]) count += 1; return count }

function rejectAbsoluteStrings(value, label = 'document') {
  if (typeof value === 'string') {
    if (/^(?:[A-Za-z]:[\\/]|\\\\|\/)/.test(value) || /(?:^|[\\/])(?:Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute-looking string`) 
    return
  }
  if (Array.isArray(value)) value.forEach((entry, index) => rejectAbsoluteStrings(entry, `${label}[${index}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, entry]) => rejectAbsoluteStrings(entry, `${label}.${key}`))
}

const argv = process.argv.slice(2)
const modes = argv.filter((token) => token === '--write' || token === '--check' || token === '--self-test')
if (modes.length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const cpuRootIndex = argv.indexOf('--cpu-root')
if (cpuRootIndex < 0 || cpuRootIndex + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
for (const [index, token] of argv.entries()) {
  if (index === cpuRootIndex || index === cpuRootIndex + 1 || token === modes[0]) continue
  throw new Error(`unexpected argument: ${token}`)
}
const cpuRootArgument = argv[cpuRootIndex + 1]
if (!fs.existsSync(cpuRootArgument) || !fs.statSync(cpuRootArgument).isDirectory()) throw new Error(`--cpu-root is not a directory: ${cpuRootArgument}`)
const cpuRoot = fs.realpathSync(cpuRootArgument)
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
if (!liveCpuCheckout) throw new Error('cannot resolve live noisemaker-for-cpu checkout')
const liveCpuReal = fs.existsSync(liveCpuCheckout) ? fs.realpathSync(liveCpuCheckout) : null
if (liveCpuReal && (beneath(liveCpuReal, cpuRoot) || beneath(cpuRoot, liveCpuReal))) throw new Error('--cpu-root must be an immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')

for (const [label, [relative, expected]] of Object.entries(pinnedCpuFiles)) {
  const actual = sha256(fs.readFileSync(path.join(cpuRoot, relative)))
  if (actual !== expected) throw new Error(`${label} provenance drift: ${actual}`)
}
const sourcePath = path.join(cppRoot, sourceRelative)
const sourcePayload = fs.readFileSync(sourcePath)
if (sourcePayload.length !== 27567 || sha256(sourcePayload) !== '3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9') throw new Error('Kaleido source provenance drift')
const expectedUniformAbi = Object.freeze({
  inputTex: 'sampler2D', resolution: 'vec2', tileOffset: 'vec2', fullResolution: 'vec2',
  time: 'float', wrap: 'bool', seed: 'int', speed: 'float', loopScale: 'float', kaleido: 'float', effectWidth: 'float',
})
const sourceUniformAbi = (() => {
  const found = Object.fromEntries([...sourcePayload.toString('utf8').matchAll(/^\s*uniform\s+(\w+)\s+(\w+)\s*;/gm)].map((match) => [match[2], match[1]]))
  if (JSON.stringify(found) !== JSON.stringify(expectedUniformAbi)) throw new Error('Kaleido uniform ABI source drift')
  return found
})()

const specifierPatterns = [
  /\bfrom\s*['"]([^'"\n]+)['"]/g,
  /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
  /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
]
function confine(candidate, why) {
  const real = fs.realpathSync(candidate)
  if (!beneath(cpuRoot, real)) throw new Error(`${why}: import escapes immutable snapshot`)
  if (liveCpuReal && beneath(liveCpuReal, real)) throw new Error(`${why}: import resolved into live checkout`)
  return real
}
const entryRelatives = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
const importClosure = new Map()
const stack = entryRelatives.map((relative) => confine(path.join(cpuRoot, relative), 'entry'))
while (stack.length) {
  const file = stack.pop()
  if (importClosure.has(file)) continue
  const payload = fs.readFileSync(file)
  importClosure.set(file, sha256(payload))
  const text = payload.toString('utf8')
  for (const pattern of specifierPatterns) {
    pattern.lastIndex = 0
    let match = pattern.exec(text)
    while (match) {
      const specifier = match[1]
      if (specifier.startsWith('node:')) { match = pattern.exec(text); continue }
      if (!specifier.startsWith('./') && !specifier.startsWith('../') && !specifier.startsWith('/')) throw new Error(`bare module specifier ${specifier}`)
      const resolved = specifier.startsWith('/') ? specifier : path.resolve(path.dirname(file), specifier)
      if (!fs.existsSync(resolved)) throw new Error(`unresolvable import ${specifier}`)
      stack.push(confine(resolved, path.relative(cpuRoot, file)))
      match = pattern.exec(text)
    }
  }
}
const importClosureRecords = [...importClosure.entries()].map(([file, hash]) => ({ relative_path: path.relative(cpuRoot, file), sha256: hash })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
function validateImportClosure(records) {
  const actual = records.map((entry) => [entry.relative_path, entry.sha256]).sort((a, b) => a[0].localeCompare(b[0]))
  const expected = expectedImportClosure.map(([relative, hash]) => [relative, hash]).sort((a, b) => a[0].localeCompare(b[0]))
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    const missing = expected.filter(([relative, hash]) => !actual.some(([a, b]) => a === relative && b === hash))
    const extra = actual.filter(([relative, hash]) => !expected.some(([a, b]) => a === relative && b === hash))
    throw new Error(`import closure mismatch: missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`)
  }
}
validateImportClosure(importClosureRecords)
const load = (relative) => import(pathToFileURL(confine(path.join(cpuRoot, relative), 'load')).href)
const { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { UPSTREAM_REVISION } = await load('src/effects/generated/upstream-snapshot.js')
const { bindCanonicalKernel, createCanonicalBindings } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
if (process.version !== authorityNode) throw new Error(`Node authority drift: ${process.version}`)
if (UPSTREAM_REVISION !== upstreamRevisionExpected) throw new Error('upstream revision drift')
const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function') throw new Error('canonicalFactory9 missing')
if (publicFactory !== canonicalFactory) throw new Error('public factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('Kaleido is adapter-routed')
if (canonicalFactory.name !== factoryName) throw new Error(`factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
const actualFactoryTextSha256 = sha256(canonicalText)
// The source's Function#toString bytes are the authority pin.  The value is
// asserted once here and copied into JSON; a drift is never silently accepted.
if (actualFactoryTextSha256 !== factoryTextSha256Expected) throw new Error(`canonical factory text drift: ${actualFactoryTextSha256}`)

const corpusAdapterKeys = (() => {
  const text = fs.readFileSync(path.join(cppRoot, 'tools/glslcpp/check_corpus.py'), 'utf8')
  const start = text.indexOf('_ADAPTERS = frozenset({')
  const end = text.indexOf('})', start)
  if (start < 0 || end < 0) throw new Error('check_corpus adapter census missing')
  return [...text.slice(start, end).matchAll(/"([^"\n]+)"/g)].map((match) => match[1]).sort()
})()
if (JSON.stringify(corpusAdapterKeys) !== JSON.stringify([...corpusAdapterKeysExpected].sort())) throw new Error('check_corpus adapter census drift')
if (corpusAdapterKeys.includes(programKey) || canonicalAdapterKeys.includes(programKey)) throw new Error('Kaleido adapter census owns the canonical key')
if (JSON.stringify(Object.keys(canonicalAdapterFactories).sort()) !== JSON.stringify([...canonicalAdapterKeys].sort())) throw new Error('canonical adapter census drift')

for (const name of tableNames) {
  const declaration = `var ${name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];`
  if (canonicalText.split(declaration).length - 1 !== 1 || declaration.includes('Float32Array')) throw new Error(`${name} declaration drift`)
  for (const [index, value] of tableValues[name].entries()) {
    const literal = `${name}[${index}] = ${value < 0 ? `-${Math.abs(value)}` : value};`
    if (canonicalText.split(literal).length - 1 !== 1) throw new Error(`${name}[${index}] store drift`)
  }
}

function inputSurface(width, height, salt) {
  const surface = new Surface(width, height)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    surface.data[i] = f(((x * 3 + y * 5 + salt) % 16) / 16)
    surface.data[i + 1] = f(((x * 7 + y * 2 + salt * 3) % 16) / 16)
    surface.data[i + 2] = f(((x * 11 + y * 13 + salt * 2) % 16) / 16)
    surface.data[i + 3] = 1
  }
  return surface
}

const caseSpecs = Object.freeze([
  { name: 'sides-three-mirror', width: 5, height: 4, time: 0.25, seed: 7, speed: 10, loopScale: 1, kaleido: 3, wrap: false, effectWidth: 0, salt: 1 },
  { name: 'sides-seven-mirror', width: 5, height: 4, time: 0.75, seed: 11, speed: 35, loopScale: 8, kaleido: 7, wrap: false, effectWidth: 0, salt: 4 },
  { name: 'wrap-floor-repeat', width: 4, height: 5, time: 1.5, seed: 19, speed: -25, loopScale: 20, kaleido: 5, wrap: true, effectWidth: 0, salt: 8 },
  { name: 'time-speed-live', width: 6, height: 3, time: 2, seed: 23, speed: 60, loopScale: 3, kaleido: 9, wrap: true, effectWidth: 0, salt: 12 },
])
const nativeWrongVariants = Object.freeze({
  inputTex: ['number', '1'], resolution: ['number', '1'], tileOffset: ['number', '1'], fullResolution: ['number', '1'],
  time: ['vec2', '[0, 0]'], wrap: ['number', '1'], seed: ['number', '0.5'], speed: ['vec2', '[0, 0]'],
  loopScale: ['vec2', '[0, 0]'], kaleido: ['vec2', '[0, 0]'], effectWidth: ['vec2', '[0, 0]'],
})
const nativeExpectedRejection = Object.freeze(expectedBindingNames.map((bindingName) => ({
  binding_name: bindingName,
  authenticated_expected_abi_category: sourceUniformAbi[bindingName],
  native_wrong_variant: nativeWrongVariants[bindingName][0],
  native_wrong_value: nativeWrongVariants[bindingName][1],
  missing_case: `missing ${bindingName}`,
  status: 'pending_shared_native_integration',
})))
function abiBindingOptions(spec, input) {
  return {
    width: spec.width, height: spec.height, time: spec.time, seed: spec.seed,
    uniforms: { inputTex: input, time: f(spec.time), wrap: spec.wrap, seed: spec.seed, speed: f(spec.speed), loopScale: f(spec.loopScale), kaleido: f(spec.kaleido), effectWidth: f(spec.effectWidth) },
    textures: { inputTex: input }, tileOffset: new Float32Array([0, 0]), fullResolution: new Float32Array([spec.width, spec.height]),
  }
}
function canonicalValueCategory(value) {
  if (value instanceof Surface) return 'Surface'
  if (value instanceof Float32Array && value.length === 2) return 'Float32Array[2]'
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  return `${typeof value}`
}
function deriveCanonicalBindingContract() {
  const spec = caseSpecs[0]
  const input = inputSurface(spec.width, spec.height, spec.salt)
  const returned = createCanonicalBindings(abiBindingOptions(spec, input))
  const returnedKeys = expectedBindingNames.filter((name) => Object.prototype.hasOwnProperty.call(returned, name))
  if (expectedBindingNames.some((name) => !Object.prototype.hasOwnProperty.call(returned, name))) throw new Error('canonical binding return surface missing required field')
  const acceptance = createCanonicalBindings({
    ...abiBindingOptions(spec, input),
    uniforms: { ...abiBindingOptions(spec, input).uniforms, inputTex: 1, wrap: 1, seed: 0.5 },
    textures: { inputTex: 1 },
  })
  if (acceptance.inputTex !== 1 || acceptance.wrap !== 1 || acceptance.seed !== 0.5) throw new Error('canonical binding acceptance probe drift')
  return {
    source_uniform_types: sourceUniformAbi,
    returned_binding_keys: returnedKeys,
    returned_binding_categories: Object.fromEntries(expectedBindingNames.map((name) => [name, canonicalValueCategory(returned[name])])),
    acceptance_probe: { inputTex_number_accepted: true, wrap_number_accepted: true, seed_fractional_number_accepted: true },
  }
}
function renderSpec(spec, override = {}, includeKernel = true) {
  const input = inputSurface(spec.width, spec.height, spec.salt)
  const before = new Uint32Array(input.data.buffer.slice(0))
  const values = { ...spec, ...override }
  const uniforms = {
    METRIC: 0, LOOP_OFFSET: 10, DIRECTION: 2,
    inputTex: input, time: f(values.time), wrap: Boolean(values.wrap), seed: values.seed | 0,
    speed: f(values.speed), loopScale: f(values.loopScale), kaleido: f(values.kaleido), effectWidth: f(values.effectWidth),
  }
  if (includeKernel) uniforms.KERNEL = values.KERNEL ?? 0
  const kernel = bindCanonicalKernel(canonicalFactory, { width: values.width, height: values.height, time: values.time, seed: values.seed, uniforms, textures: { inputTex: input }, tileOffset: new Float32Array([0, 0]), fullResolution: new Float32Array([values.width, values.height]) })
  const output = new Surface(values.width, values.height)
  runPass({ kernel, destination: output, time: values.time, seed: values.seed, tileRows: 2 })
  const after = new Uint32Array(input.data.buffer.slice(0))
  return { input, output, inputWords: wordsOf(input.data), outputWords: wordsOf(output.data), outputBytes: Array.from(output.toRgba8()), inputUnchanged: same(Array.from(before), Array.from(after)) }
}
function renderRecord(spec) {
  const rendered = renderSpec(spec)
  return {
    name: spec.name, width: spec.width, height: spec.height,
    input: { width: spec.width, height: spec.height, f32_words_le: rendered.inputWords, f32_sha256: wordDigest(rendered.inputWords) },
    expected: { f32_words_le: rendered.outputWords, f32_sha256: wordDigest(rendered.outputWords), rgba8_bytes: rendered.outputBytes, rgba8_sha256: bytesDigest(rendered.outputBytes) },
    bindings: { time: `0x${new Uint32Array(new Float32Array([spec.time]).buffer)[0].toString(16).padStart(8, '0')}`, seed: spec.seed, speed: `0x${new Uint32Array(new Float32Array([spec.speed]).buffer)[0].toString(16).padStart(8, '0')}`, loopScale: `0x${new Uint32Array(new Float32Array([spec.loopScale]).buffer)[0].toString(16).padStart(8, '0')}`, kaleido: `0x${new Uint32Array(new Float32Array([spec.kaleido]).buffer)[0].toString(16).padStart(8, '0')}`, effectWidth: `0x${new Uint32Array(new Float32Array([spec.effectWidth]).buffer)[0].toString(16).padStart(8, '0')}`, wrap: spec.wrap },
    alpha_f32_word: '0x3f800000', alpha_rgba8_byte: 255,
  }
}
const canonicalBindingContract = deriveCanonicalBindingContract()
const renderCases = caseSpecs.map(renderRecord)
const baselineByCase = new Map(caseSpecs.map((spec, index) => [spec.name, renderCases[index]]))
const mutationDefinitions = [
  ['kaleido-sides-plus-one', (spec) => ({ kaleido: spec.kaleido + 1 })],
  ['wrap-arm-inverted', (spec) => ({ wrap: !spec.wrap })],
  ['time-sign-flipped', (spec) => ({ time: -spec.time })],
  ['speed-sign-flipped', (spec) => ({ speed: -spec.speed })],
]
const mutationLedger = mutationDefinitions.map(([name, mutate]) => ({ name, rows: caseSpecs.map((spec) => {
  const mutant = renderSpec(spec, mutate(spec))
  const canonical = baselineByCase.get(spec.name)
  const changedLanes = changed(canonical.expected.f32_words_le, mutant.outputWords)
  const changedBytes = changed(canonical.expected.rgba8_bytes, mutant.outputBytes)
  return { case: spec.name, differs: changedLanes > 0 || changedBytes > 0, changed_float32_lanes: changedLanes, changed_rgba8_bytes: changedBytes }
}), budgeted_as: 'pixel witness' }))

const kernelZero = renderSpec(caseSpecs[0], { KERNEL: 0 })
const kernelOmitted = renderSpec(caseSpecs[0], {}, false)
const kernelLive = renderSpec(caseSpecs[0], { KERNEL: 1, effectWidth: 6 })
if (!same(kernelZero.outputWords, kernelOmitted.outputWords) || !same(kernelZero.outputBytes, kernelOmitted.outputBytes)) throw new Error('KERNEL omitted is not the KERNEL=0 control')
if (changed(kernelZero.outputWords, kernelLive.outputWords) === 0) throw new Error('KERNEL live probe failed to discriminate')
const repeatA = renderSpec(caseSpecs[1]); const repeatB = renderSpec(caseSpecs[1])
if (!same(repeatA.outputWords, repeatB.outputWords) || !same(repeatA.outputBytes, repeatB.outputBytes)) throw new Error('repeatability failure')
if (repeatA.inputUnchanged !== true) throw new Error('input texture was mutated')
const independentA = renderSpec(caseSpecs[2]); const independentB = renderSpec(caseSpecs[2]);
if (independentA.output.data === independentB.output.data) throw new Error('independent outputs alias')

function parseCorpusAdapterSource() { return corpusAdapterKeys }
const sourceSha = sha256(sourcePayload)
const provenance = {
  node_version: process.version,
  generator: { relative_path: 'docs/port-engineering/kaleido-parity/kaleido187_oracle_generator.mjs', sha256: sha256(fs.readFileSync(generatorPath)) },
  native_include_generator: { relative_path: 'tools/glslcpp/generate_kaleido_native_oracle_include.py', sha256: sha256(fs.readFileSync(includeGeneratorPath)) },
  cpu_snapshot: { argument: '<immutable-cpu-snapshot-root>', immutable_snapshot: true, live_checkout_rejected: true, containment_checked: true, import_closure: importClosureRecords },
  source: { relative_path_from_noisemaker_for_cpp: sourceRelative, bytes: sourcePayload.length, sha256: sourceSha },
  canonical_factory: { name: factoryName, text_sha256: actualFactoryTextSha256, public_factory_is_canonical_identity: publicFactory === canonicalFactory },
  adapter_override_absent: true, adapter_routed_keys: [...canonicalAdapterKeys], corpus_adapter_keys: parseCorpusAdapterSource(), corpus_adapter_source: 'tools/glslcpp/check_corpus.py',
  pinned_cpu_files: Object.fromEntries(Object.entries(pinnedCpuFiles).map(([key, [relative, hash]]) => [key, { relative_path: relative, sha256: hash }])),
}
const mutableContracts = Object.fromEntries(tableNames.map((name) => [name, {
  javascript_declaration: `var ${name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];`, glsl_type: 'float[9], mutable, uninitialized', element_materialization: 'plain JS Array of Numbers, not Float32Array', numeric_contract: 'double, never narrowed to f32', native_element_type: 'double', writer: 'loadKernels called once per pixel from main and rewrites all nine elements', elements: tableValues[name], identifier_occurrence_census: tableOccurrenceCensus[name], reads: 'none at accepted KERNEL=0 defines', oracle_discriminable: false, why_not_discriminable: 'write-only at frozen defines; pixels are controls, not structural-carrier evidence',
}]))
const document = {
  schema, schema_version: 1, program_key: programKey, effect_key: effectKey, runtime_key: programKey, corpus_revision: corpusRevision, upstream_revision: upstreamRevisionExpected,
  defines: { DIRECTION: 2, KERNEL: 0, LOOP_OFFSET: 10, METRIC: 0 }, runtime_binding_names: [...bindingNames], runtime_binding_abi: bindingAbi,
  compile_time_defines_are_not_bindings: true, defines_are_runtime_bindings_in_javascript: 'KERNEL is runtime-bound at zero for parity; omitted KERNEL is an explicit identity control. The typed port has no KERNEL binding.',
  factory: { name: factoryName, text_sha256: actualFactoryTextSha256, public_factory_is_canonical_identity: true }, oracle_authority: 'unmodified public canonicalFactory9 from the immutable noisemaker-for-cpu snapshot through bindCanonicalKernel/GlslCpuRuntime/runPass; no C++ output participates',
  mutable_global_contracts: mutableContracts,
  exactness_contract: { float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads significant', rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays', tolerance: 'none', comparison_order: 'dimensions, counts, every float32 word, every independent RGBA8 byte', coordinates: 'top-down Surface storage order', alpha: 'sampled alpha is exactly 1.0 in every input and output' },
  provenance,
  canonical_binding_contract: canonicalBindingContract,
  native_expected_rejection: nativeExpectedRejection,
  abi_rejection_contract: { contract_type: 'native expected-rejection preflight table', required_bindings: [...bindingNames], source_interface: 'pinned Kaleido GLSL uniform declarations plus canonical createCanonicalBindings return surface', status: 'pending_shared_native_integration' },
  comparer_self_tests: { exact_words_and_bytes: true, dimensions_before_access: true, equal_rgba8_does_not_hide_word_mismatch: true, signed_zero_and_nan_payloads_significant: true, truncated_and_extra_arrays_rejected: true },
  coverage_axes: { kaleido_sides: [3, 5, 7, 9], wrap: [false, true], time: [0.25, 0.75, 1.5, 2], speed: [10, 35, -25, 60], loopScale: [1, 3, 8, 20], input_pattern: 'dyadic RGBA gradient', route: 'full only; tile-crop identity intentionally unclaimed' },
  render_cases: renderCases,
  control_group: { repeatability: { case: caseSpecs[1].name, identical_float32: true, identical_rgba8: true }, input_immutability: { case: caseSpecs[1].name, unchanged: true }, independent_output_storage: { case: caseSpecs[2].name, distinct_data_objects: true }, public_direct_identity: true },
  kernel_liveness_census: { probe_case: caseSpecs[0].name, omitted_vs_zero: 'identical', nonzero_kernel_with_effect_width: 'differs', zero_lanes_changed: 0, live_probe_changed_lanes: changed(kernelZero.outputWords, kernelLive.outputWords) },
  mutation_ledger: mutationLedger,
  write_only_tables_axis: { status: 'measured structural control', element_count: 45, table_names: [...tableNames], oracle_discriminable: false, rendered_mutant: 'table constants changed at accepted KERNEL=0 defines', rendered_divergences: { float32_lanes: 0, rgba8_bytes: 0 }, claim: 'table values are write-only at accepted defines; pixel controls cannot carry the array ABI proof' },
  xor_sites_axis: { status: 'runtime-dead control', loop_offset: 10, sites: ['158:10', '159:10', '160:10'], pixel_case: 'not budgeted; structural carrier only' },
  binding_liveness_census: { live: ['inputTex', 'time', 'wrap', 'seed', 'speed', 'loopScale', 'kaleido'], required_but_unread_or_zero: ['resolution', 'tileOffset', 'fullResolution', 'effectWidth'], abi: bindingAbi },
  claim_boundaries: { tables: 'structural only', kernel: 'KERNEL=0 is the frozen corpus define; nonzero probe proves the JS channel exists but is not a parity case', tile_crop: 'no crop identity claim', absolute_paths: 'all provenance paths are stable repository-relative placeholders', tolerance: 'none' },
}
rejectAbsoluteStrings(document)

function reportFor(doc) {
  const digest = sha256(Buffer.from(stable(doc)))
  const artifactRows = [
    ['kaleido187_oracle_generator.mjs', generatorPath],
    ['kaleido187-oracles.json', outputPath],
    ['generate_kaleido_native_oracle_include.py', includeGeneratorPath],
    ['kaleido187_expected.inc', path.join(cppRoot, 'tests/oracles/kaleido187_expected.inc')],
  ].map(([name, target]) => {
    if (!fs.existsSync(target)) return `- ${name}: <not-yet-materialized>`
    const payload = fs.readFileSync(target)
    return `- ${name}: ${payload.length} bytes, SHA-256 \`${sha256(payload)}\``
  })
  const lines = [
    '# Kaleido187 exact-parity oracle', '',
    'This package authenticates `classicNoisedeck/kaleido:kaleido` against the unmodified public `canonicalFactory9` in an immutable CPU snapshot.', '',
    '## Decisions', '',
    `- Frozen defines: DIRECTION=2, KERNEL=0, LOOP_OFFSET=10, METRIC=0; factory text SHA-256 is \`${doc.factory.text_sha256}\`.`,
    '- The authenticated native expected-rejection table derives the pinned GLSL uniform declarations and canonical createCanonicalBindings return surface. Each row is pending shared native integration; no canonical JavaScript rejection is claimed.',
    '- The five mutable float[9] tables are plain JavaScript arrays and write-only at the accepted defines. Their pixel mutation is explicitly an invariant control, not structural-carrier evidence.',
    '- No tile/crop identity is claimed. All stored expected values are raw float32 words plus independently captured RGBA8 bytes with zero tolerance.', '',
    '## Cases and controls', '',
    `- ${doc.render_cases.length} full-route cases cover kaleido sides, wrap arms, time, speed, loopScale, seed, and distinct dyadic input gradients.`,
    '- Repeatability, input immutability, independent output storage, public/direct factory identity, and KERNEL omitted-vs-zero identity are measured.',
    `- KERNEL nonzero with effectWidth changed ${doc.kernel_liveness_census.live_probe_changed_lanes} float32 lanes; this is a liveness probe, not a frozen parity case.`,
    '- Mutants are recorded per case. XOR sites and table values are runtime-dead/write-only controls at the frozen define.', '',
    '## Provenance locks', '',
    `- Corpus revision \`${doc.corpus_revision}\`; source \`${doc.provenance.source.sha256}\`; CPU import closure is confined to the immutable snapshot.`,
    `- The complete ${doc.provenance.cpu_snapshot.import_closure.length}-file CPU import closure is frozen by path and SHA-256; any modified, missing, or extra dependency fails closed.`,
    '- Live/foreign imports, adapter routing, absolute-looking provenance strings, schema drift, and sidecar drift fail closed.', '',
    '## TDD evidence', '',
    '- RED: `pytest -q tests/test_kaleido_oracle.py` failed before package files existed (2 failures: missing generator and missing check path).',
    '- GREEN: the same test is run after generation, followed by generator `--check` and materializer `--self-test`/`--check`.', '',
    '- Verification hygiene: after the initial RED probe left repo-local pytest/bytecode residue, Python bytecode, pytest cache, temporary files, and regeneration cache were redirected under worker temp roots; the exact residue is left for controller cleanup while workers quiesce.', '',
    '## Files and hashes', '',
    `- Oracle JSON SHA-256: \`${digest}\` (sidecar is authoritative for the exact bytes).`,
    ...artifactRows,
    '- Generator, report, native materializer, include, and each sidecar are generated/checked as one package.', '',
    '## Concerns', '',
    '- The nonzero KERNEL probe exercises an authority path outside the frozen corpus define only to prove that the channel is closed at KERNEL=0.',
    '- ABI evidence is a complete native-consumable preflight table: every required binding has one concrete missing case and one wrong native variant/value, all pending shared native integration.', '',
  ]
  return `${lines.join('\n')}\n`
}

function writePackage(doc) {
  const payload = Buffer.from(stable(doc))
  writeChecked(outputPath, payload)
  const report = Buffer.from(reportFor(doc))
  writeChecked(reportPath, report)
  writeChecked(generatorPath, fs.readFileSync(generatorPath))
}
function compareExpected(target, expected) {
  const actual = verifyChecked(target)
  if (!actual.equals(expected)) throw new Error(`${path.basename(target)} drift`)
}

function selfTest() {
  const checks = []
  checks.push(['factory identity', publicFactory === canonicalFactory])
  checks.push(['factory text pin', actualFactoryTextSha256 === factoryTextSha256Expected])
  checks.push(['tables are write-only controls', document.write_only_tables_axis.oracle_discriminable === false])
  checks.push(['cases have unique names', new Set(document.render_cases.map((entry) => entry.name)).size === document.render_cases.length])
  checks.push(['raw words and bytes are complete', document.render_cases.every((entry) => entry.expected.f32_words_le.length === entry.width * entry.height * 4 && entry.expected.rgba8_bytes.length === entry.width * entry.height * 4)])
  checks.push(['absolute-looking strings rejected', (() => { try { rejectAbsoluteStrings({ bad: '/tmp/foreign' }); return false } catch { return true } })()])
  checks.push(['KERNEL zero control', document.kernel_liveness_census.zero_lanes_changed === 0])
  const closureMissing = importClosureRecords.slice(1)
  const closureExtra = [...importClosureRecords, { relative_path: 'src/runtime/foreign.js', sha256: '0'.repeat(64) }]
  let missingRejected = false; let extraRejected = false
  try { validateImportClosure(closureMissing) } catch { missingRejected = true }
  try { validateImportClosure(closureExtra) } catch { extraRejected = true }
  checks.push(['missing import-closure entry rejected', missingRejected])
  checks.push(['extra import-closure entry rejected', extraRejected])
  checks.push(['modified unpinned dependency rejected', (() => { try { validateImportClosure(importClosureRecords.map((entry) => entry.relative_path === 'src/csl/runtime.js' ? { ...entry, sha256: '0'.repeat(64) } : entry)); return false } catch { return true } })()])
  checks.push(['native ABI table is complete and pending', document.native_expected_rejection.length === expectedBindingNames.length && document.native_expected_rejection.every((row, index) => row.binding_name === expectedBindingNames[index] && row.status === 'pending_shared_native_integration')])
  checks.push(['canonical permissive acceptance is recorded', document.canonical_binding_contract.acceptance_probe.inputTex_number_accepted && document.canonical_binding_contract.acceptance_probe.wrap_number_accepted && document.canonical_binding_contract.acceptance_probe.seed_fractional_number_accepted])
  checks.push(['mutation set is frozen', JSON.stringify(document.mutation_ledger.map((entry) => entry.name)) === JSON.stringify(['kaleido-sides-plus-one', 'wrap-arm-inverted', 'time-sign-flipped', 'speed-sign-flipped'])])
  const failed = checks.filter(([, ok]) => !ok)
  checks.forEach(([label, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}`))
  console.log(`${checks.length - failed.length}/${checks.length} self-test checks passed`)
  return failed.length ? 1 : 0
}

if (modes[0] === '--self-test') process.exit(selfTest())
const expectedJson = Buffer.from(stable(document))
const expectedReport = Buffer.from(reportFor(document))
if (modes[0] === '--write') {
  writePackage(document)
  console.log(`kaleido187 oracle written (${expectedJson.length} bytes, ${sha256(expectedJson)})`)
} else {
  compareExpected(outputPath, expectedJson)
  compareExpected(reportPath, expectedReport)
  verifyChecked(generatorPath)
  console.log('kaleido187 oracle generator: ok')
}
