#!/usr/bin/env node
// Cellrefract186 canonical JavaScript oracle generator
// (`classicNoisedeck/cellRefract:cellRefract`, typed row 186).
//
// Authority: the unmodified public canonical factory `canonicalFactory3` from
// an immutable snapshot of `noisemaker-for-cpu`, executed through the pinned
// `bindCanonicalKernel` / `GlslCpuRuntime` / `runPass` path. No C++ output
// participates in any expected array. A locally reimplemented formula is not an
// oracle and is never used here.
//
// This program exists to pin the materialization of five MUTABLE UNINITIALIZED
// file-scope `float[9]` tables (`emboss`, `sharpen`, `blur`, `edge`, `edge2`):
//   * they are plain JS `Array`s of Numbers -- doubles, never narrowed to f32;
//   * `loadKernels` re-writes all 45 elements before any possible read, once
//     per pixel, from `main`;
//   * at the frozen defines {KERNEL: 0, SHAPE: 1} the tables are WRITE-ONLY:
//     their only readers live inside `convolutionKernel`'s KERNEL != 0
//     branches, which `main` never enters at KERNEL = 0. No table-content
//     mutant is pixel-discriminable; that is MEASURED here (0 changed lanes on
//     every case) and the tables' protection is structural, not pixel-led.
//
// The render cases instead discriminate the REACHABLE path: `smin`, the prng
// chain, the aspect ratio, and the wrap arms -- each verified bit-differing
// before it was budgeted, per cellrefract-design.md section 7. A NON-reaching
// control mutant inside a KERNEL != 0 branch is measured invariant everywhere;
// that invariance is the witness that the JS runtime skip matches the
// normalizer's strip.
//
//   node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'cellrefract186-oracles.json')
const reportPath = path.join(here, 'cellrefract-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_cellrefract_native_oracle_include.py')

const schema = 'noisemaker-for-cpp.cellrefract186.pixel-parity.v1'
const schemaVersion = 1
const programKey = 'classicNoisedeck/cellRefract:cellRefract'
const effectKey = 'classicNoisedeck/cellRefract'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const defines = { KERNEL: 0, SHAPE: 1 }
const factoryName = 'canonicalFactory3'
const factoryTextSha256 = '329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3'
const nextFactoryName = 'canonicalFactory4'

// The live checkout is DERIVED, never hardcoded: a machine-specific absolute
// path in a checked-in gate is unrunnable on any other machine and leaks a home
// directory into the repository. `NOISEMAKER_FOR_CPU` overrides; otherwise the
// conventional sibling layout under $HOME is used.
const liveCpuCheckoutResolution =
  'process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu'
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU
  ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
// With neither variable set the live-checkout guard below would be skipped
// entirely and `--check` would pass with no guard at all. Refuse to run instead
// of degrading to an inert guard.
if (liveCpuCheckout === null) {
  throw new Error('cannot resolve the live noisemaker-for-cpu checkout: set NOISEMAKER_FOR_CPU or HOME. '
    + 'Running without it would silently disable the live-checkout refusal.')
}

// Neither the `--cpu-root` argument nor the live-checkout path is recorded
// verbatim. The import closure and the six pinned file hashes authenticate the
// snapshot completely; the literal path authenticates nothing and would bind
// `--check` to one ephemeral directory on one machine.
const cpuRootPlaceholder = '<immutable-cpu-snapshot-root>'
const liveCheckoutPlaceholder = '<live-noisemaker-for-cpu-checkout>'
const sourceRelative = `tools/glslcpp/corpus/${corpusRevision}/sources/classicNoisedeck/cellRefract/cellRefract.glsl`
const sourceBytesExpected = 13719
const sourceSha256Expected = 'aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70'

// Exactly fifteen runtime bindings, in GLSL declaration order. KERNEL and
// SHAPE are compile-time defines in the corpus (recorded separately) that the
// JavaScript materializes as runtime bindings bound at the frozen define
// values; they are never counted here. `resolution` and `effectWidth` are
// declared but unread at the frozen defines; they remain required ABI bindings
// and are not "cleaned up".
const bindingNames = Object.freeze([
  'inputTex', 'time', 'seed', 'resolution', 'tileOffset', 'fullResolution',
  'scale', 'cellScale', 'cellSmooth', 'variation', 'speed', 'refractAmt',
  'direction', 'wrap', 'effectWidth',
])
const bindingAbi = Object.freeze({
  inputTex: 'sampler2D', time: 'number', seed: 'int32', resolution: 'Vec2',
  tileOffset: 'Vec2', fullResolution: 'Vec2', scale: 'number',
  cellScale: 'number', cellSmooth: 'number', variation: 'number',
  speed: 'number', refractAmt: 'number', direction: 'number', wrap: 'int32',
  effectWidth: 'number',
})
const vecLanes = Object.freeze({ Vec2: 2 })

const pinnedCpuFiles = Object.freeze({
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
})

// Two distinct adapter tables, and both must be checked.
//
// `check_corpus._ADAPTERS` (the Python-side eligibility table) decides whether a
// program is in the `fractal` eligibility limbo. It is READ FROM THE LIVE
// `check_corpus.py` below, never transcribed: a frozen copy compared against
// another frozen copy proves nothing, and would stay green if
// `classicNoisedeck/cellRefract` were ever added to the real table.
const corpusAdapterSourceRelative = 'tools/glslcpp/check_corpus.py'
const corpusAdapterCensusExpected = Object.freeze([
  'classicNoisedeck/fractal:fractal', 'filter/historicPalette:historicPalette',
  'filter/palette:palette', 'synth/julia:julia',
])
// `canonicalAdapterFactories` (the JavaScript-side override table) is a larger,
// separate set. It is pinned by census here so a new override cannot silently
// take over this key.
const canonicalAdapterKeys = Object.freeze([
  'classicNoisedeck/bitEffects:bitEffects', 'classicNoisedeck/fractal:fractal',
  'filter/crt:crt', 'filter/historicPalette:historicPalette',
  'filter/median:median', 'filter/palette:palette',
  'filter/pixelSort:luminance', 'filter/reindex:nmReindexApply',
  'filter/reindex:nmReindexStats', 'filter/snow:snow', 'synth/julia:julia',
])

const f = Math.fround
const channels = ['r', 'g', 'b', 'a']

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytesOf(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function words(view) { return new Uint32Array(view.buffer, view.byteOffset, view.length) }
function f32Bits(value) { return u32Hex(words(new Float32Array([value]))[0]) }
function packWords(hexWords) {
  return Buffer.concat(hexWords.map((word) => {
    const buffer = Buffer.alloc(4)
    buffer.writeUInt32LE(Number(word), 0)
    return buffer
  }))
}
function f32Vector(values, lanes) {
  if (!Array.isArray(values) || values.length !== lanes
      || values.some((item) => typeof item !== 'number' || !Number.isFinite(item))) {
    throw new Error(`vector must be ${lanes} finite lanes: ${JSON.stringify(values)}`)
  }
  return new Float32Array(values.map(f))
}
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function verifySidecar(target) {
  const sidecar = sidecarPath(target)
  if (!fs.existsSync(target) || !fs.existsSync(sidecar)) throw new Error(`missing checked asset or sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecar, 'utf8') !== sidecarText(target, payload)) throw new Error(`checksum sidecar drift: ${target}`)
  return payload
}

// ---------------------------------------------------------------------------
// Arguments
// ---------------------------------------------------------------------------

const argv = process.argv.slice(2)
const write = argv.includes('--write')
const check = argv.includes('--check')
if (write === check) throw new Error('choose exactly one of --write or --check')
const cpuRootIndex = argv.indexOf('--cpu-root')
if (cpuRootIndex < 0 || cpuRootIndex + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
for (const [index, token] of argv.entries()) {
  if (index === cpuRootIndex || index === cpuRootIndex + 1) continue
  if (token !== '--write' && token !== '--check') throw new Error(`unexpected argument: ${token}`)
}
const cpuRootArgument = argv[cpuRootIndex + 1]
if (!fs.existsSync(cpuRootArgument) || !fs.statSync(cpuRootArgument).isDirectory()) {
  throw new Error(`--cpu-root is not a directory: ${cpuRootArgument}`)
}
const cpuRoot = fs.realpathSync(cpuRootArgument)
const liveCpuReal = liveCpuCheckout !== null && fs.existsSync(liveCpuCheckout)
  ? fs.realpathSync(liveCpuCheckout)
  : null
const beneath = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`)
if (liveCpuReal !== null && (cpuRoot === liveCpuReal || beneath(liveCpuReal, cpuRoot) || beneath(cpuRoot, liveCpuReal))) {
  throw new Error('--cpu-root must be an immutable snapshot, never the live noisemaker-for-cpu checkout')
}
if (beneath(cppRoot, cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')

// ---------------------------------------------------------------------------
// Provenance: pinned hashes, closed import graph, real-path confinement
// ---------------------------------------------------------------------------

for (const [name, [relative, expected]] of Object.entries(pinnedCpuFiles)) {
  const actual = sha256(fs.readFileSync(path.join(cpuRoot, relative)))
  if (actual !== expected) throw new Error(`${name} provenance drift: ${actual}`)
}

const entryRelatives = [
  'src/effects/catalog.js',
  'src/effects/generated/upstream-snapshot.js',
  'src/csl/glsl-kernel.js',
  'src/csl/glsl-runtime.js',
  'src/runtime/pass-runner.js',
  'src/runtime/surface.js',
]
const specifierPatterns = [
  /\bfrom\s*['"]([^'"\n]+)['"]/g,
  /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
  /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
]
function confine(candidate, why) {
  const real = fs.realpathSync(candidate)
  if (!beneath(cpuRoot, real)) throw new Error(`${why}: import escapes the immutable snapshot: ${real}`)
  if (liveCpuReal !== null && beneath(liveCpuReal, real)) throw new Error(`${why}: import resolved into the live checkout: ${real}`)
  return real
}
const importClosure = new Map()
{
  const stack = entryRelatives.map((relative) => confine(path.join(cpuRoot, relative), 'entry'))
  while (stack.length > 0) {
    const file = stack.pop()
    if (importClosure.has(file)) continue
    const payload = fs.readFileSync(file)
    importClosure.set(file, sha256(payload))
    const text = payload.toString('utf8')
    for (const pattern of specifierPatterns) {
      pattern.lastIndex = 0
      let match = pattern.exec(text)
      while (match !== null) {
        const specifier = match[1]
        if (specifier.startsWith('node:')) { match = pattern.exec(text); continue }
        if (!specifier.startsWith('./') && !specifier.startsWith('../') && !specifier.startsWith('/')) {
          throw new Error(`bare module specifier "${specifier}" in ${path.relative(cpuRoot, file)}`)
        }
        const resolved = specifier.startsWith('/') ? specifier : path.resolve(path.dirname(file), specifier)
        if (!fs.existsSync(resolved)) throw new Error(`unresolvable import "${specifier}" in ${path.relative(cpuRoot, file)}`)
        stack.push(confine(resolved, path.relative(cpuRoot, file)))
        match = pattern.exec(text)
      }
    }
  }
}
const importClosureRecords = [...importClosure.entries()]
  .map(([file, hash]) => ({ relative_path_from_noisemaker_for_cpu: path.relative(cpuRoot, file), sha256: hash }))
  .sort((left, right) => (left.relative_path_from_noisemaker_for_cpu < right.relative_path_from_noisemaker_for_cpu ? -1 : 1))

// Every CPU module is loaded through `confine`, so a resolution or module-cache
// hit anywhere outside the immutable snapshot is a hard failure.
const load = (relative) => import(pathToFileURL(confine(path.join(cpuRoot, relative), 'load')).href)
const { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { effectRecords, UPSTREAM_REVISION } = await load('src/effects/generated/upstream-snapshot.js')
const { bindCanonicalKernel, createCanonicalBindings } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')

if (process.version !== authorityNode) throw new Error(`Node authority drift: ${process.version}`)
if (UPSTREAM_REVISION !== upstreamRevisionExpected) throw new Error('upstream revision drift')

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function') throw new Error('canonical cellRefract factory missing')
if (publicFactory !== canonicalFactory) throw new Error('public cellRefract factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('unexpected cellRefract adapter override')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected cellRefract adapter override value')
// Parse `_ADAPTERS` out of the live check_corpus.py rather than trusting a copy.
const corpusAdapterKeys = (() => {
  const sourcePath = path.join(cppRoot, corpusAdapterSourceRelative)
  const text = fs.readFileSync(sourcePath, 'utf8')
  const opener = '_ADAPTERS = frozenset({'
  const start = text.indexOf(opener)
  if (start < 0) throw new Error(`${corpusAdapterSourceRelative}: _ADAPTERS frozenset literal not found`)
  const end = text.indexOf('})', start)
  if (end < 0) throw new Error(`${corpusAdapterSourceRelative}: _ADAPTERS literal is unterminated`)
  const body = text.slice(start + opener.length, end)
  if (/[^\s"',:/A-Za-z0-9_.-]/.test(body)) {
    throw new Error(`${corpusAdapterSourceRelative}: _ADAPTERS literal is not a plain string set`)
  }
  const keys = [...body.matchAll(/"([^"\n]+)"/g)].map((match) => match[1])
  if (keys.length === 0) throw new Error(`${corpusAdapterSourceRelative}: _ADAPTERS parsed empty`)
  if (new Set(keys).size !== keys.length) throw new Error(`${corpusAdapterSourceRelative}: _ADAPTERS has duplicates`)
  return keys.sort()
})()
{
  const expected = [...corpusAdapterCensusExpected].sort()
  if (corpusAdapterKeys.length !== expected.length
      || corpusAdapterKeys.some((key, index) => key !== expected[index])) {
    throw new Error(`check_corpus._ADAPTERS census drift: ${corpusAdapterKeys.join(', ')}`)
  }
}
if (corpusAdapterKeys.includes(programKey)) throw new Error('classicNoisedeck/cellRefract:cellRefract must not be corpus-adapter-routed')
if (canonicalAdapterKeys.includes(programKey)) throw new Error('classicNoisedeck/cellRefract:cellRefract must not be adapter-routed')
{
  const observed = Object.keys(canonicalAdapterFactories).sort()
  const expected = [...canonicalAdapterKeys].sort()
  if (observed.length !== expected.length || observed.some((key, index) => key !== expected[index])) {
    throw new Error(`adapter table census drift: ${observed.join(', ')}`)
  }
}
if (canonicalFactory.name !== factoryName) throw new Error(`canonical cellRefract factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) throw new Error(`canonical cellRefract factory text drift: ${sha256(canonicalText)}`)

const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf(`function ${nextFactoryName}`, sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('canonical cellRefract factory source slice missing')
const canonicalSlice = canonicalKernelsSource.slice(sliceStart, sliceEnd)

// ---------------------------------------------------------------------------
// The materialization this package exists to pin, read from the shipped JS
// ---------------------------------------------------------------------------

const tableNames = Object.freeze(['emboss', 'sharpen', 'blur', 'edge', 'edge2'])
const kernelTables = Object.freeze({
  emboss: [-2, -1, 0, -1, 1, 1, 0, 1, 2],
  sharpen: [-1, 0, -1, 0, 5, 0, -1, 0, -1],
  blur: [1, 2, 1, 2, 4, 2, 1, 2, 1],
  edge: [-1, -1, -1, -1, 8, -1, -1, -1, -1],
  edge2: [-1, 0, -1, 0, 4, 0, -1, 0, -1],
})
// Occurrences of each table identifier in the whole factory, counted with word
// boundaries: declaration + nine `loadKernels` stores + whole-array reads
// inside `convolutionKernel`'s KERNEL != 0 branches (and nowhere else). `edge`
// is NEVER read anywhere, not even in stripped code.
const tableOccurrenceCensus = Object.freeze({ emboss: 11, sharpen: 11, blur: 11, edge: 10, edge2: 12 })

for (const name of tableNames) {
  const declaration = `var ${name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];`
  const occurrences = canonicalText.split(declaration).length - 1
  if (occurrences !== 1) throw new Error(`${name} mutable-global declaration census drift: matched ${occurrences} times`)
  if (declaration.includes('Float32Array')) throw new Error(`${name} declaration became a Float32Array`)
  const identifier = new RegExp(`\\b${name}\\b`, 'g')
  const count = (canonicalText.match(identifier) ?? []).length
  if (count !== tableOccurrenceCensus[name]) {
    throw new Error(`${name} identifier census drift: ${count} occurrences, expected ${tableOccurrenceCensus[name]}`)
  }
  // The 45 writer stores: every (table, index, value) triple appears exactly
  // once as a literal store inside loadKernels.
  for (const [index, value] of kernelTables[name].entries()) {
    const statement = `${name}[${index}] = ${value};`
    const stores = canonicalText.split(statement).length - 1
    if (stores !== 1) throw new Error(`${name}[${index}] store census drift: matched ${stores} times`)
  }
}
{
  const storeCount = tableNames.reduce((total, name) => total + kernelTables[name].length, 0)
  if (storeCount !== 45) throw new Error(`loadKernels store census drift: ${storeCount}`)
}
// The defines are runtime bindings in the JavaScript, at the frozen values.
for (const [name, value] of [['SHAPE', defines.SHAPE], ['KERNEL', defines.KERNEL]]) {
  const declaration = `var ${name} = $bindings["${name}"];`
  if (canonicalText.split(declaration).length - 1 !== 1) {
    throw new Error(`${name} runtime-binding declaration census drift`)
  }
  void value
}
// `loadKernels` is called exactly once, from `main`, as a bare void call.
if (canonicalText.split('loadKernels();').length - 1 !== 1) throw new Error('loadKernels() call census drift')
// The write sites are plain literal stores; no compound or indirect writes.
for (const operator of ['+=', '-=', '*=', '/=', '++', '--']) {
  for (const name of tableNames) {
    const pattern = new RegExp(`\\b${name}\\[[^\\]]*\\]\\s*(?:${operator.replace(/[+*\/-]/g, (c) => `\\${c}`)})`, 'g')
    if (pattern.test(canonicalText)) throw new Error(`${name} carries a compound write`)
  }
}

const sourcePath = path.join(cppRoot, sourceRelative)
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error('pinned cellRefract GLSL source drift')
}

const effect = effectRecords.find((item) => item.id === effectKey)
if (!effect || effect.func !== 'cellRefract' || effect.kind !== 'filter') throw new Error('cellRefract metadata drift')
if (effect.passes?.length !== 1 || effect.passes[0]?.program !== 'cellRefract') throw new Error('cellRefract pass interface drift')
if (effect.passes[0]?.inputs?.inputTex !== 'inputTex') throw new Error('cellRefract input interface drift')
if (Object.keys(effect.textures ?? {}).length !== 0 || effect.externalTexture !== null) throw new Error('cellRefract must have no textures')
if (effect.params?.shape?.default !== defines.SHAPE || effect.params?.shape?.define !== 'SHAPE'
    || effect.params?.kernel?.default !== defines.KERNEL || effect.params?.kernel?.define !== 'KERNEL') {
  throw new Error('cellRefract default define drift')
}

// ---------------------------------------------------------------------------
// Exact comparer and its self-tests
// ---------------------------------------------------------------------------

function mismatchRecord(index, width, expectedWords, actualWords, expectedBytes, actualBytes, kind) {
  const pixel = Math.floor(index / 4)
  return {
    kind,
    lane_or_byte_index: index,
    top_down_xy: [pixel % width, Math.floor(pixel / width)],
    channel: channels[index % 4],
    expected_word: index < expectedWords.length ? u32Hex(expectedWords[index]) : null,
    actual_word: index < actualWords.length ? u32Hex(actualWords[index]) : null,
    expected_byte: index < expectedBytes.length ? expectedBytes[index] : null,
    actual_byte: index < actualBytes.length ? actualBytes[index] : null,
  }
}

function compareExact(actual, expected, label) {
  if (!(actual?.data instanceof Float32Array)) throw new TypeError(`${label}: actual must be a Float32 Surface`)
  const expectedWords = expected?.float_words
  const expectedBytes = expected?.rgba8
  if (!(expectedWords instanceof Uint32Array) || !(expectedBytes instanceof Uint8Array)) {
    throw new TypeError(`${label}: independent expected arrays required`)
  }
  const base = {
    label,
    expected_dimensions: [expected.width, expected.height],
    actual_dimensions: [actual.width, actual.height],
  }
  if (actual.width !== expected.width || actual.height !== expected.height) {
    return { exact: false, rejected_before_iteration: true, reason: 'dimensions', ...base, first_mismatch: null }
  }
  const exactCount = expected.width * expected.height * 4
  const actualWords = words(actual.data)
  if (expectedWords.length !== exactCount || actualWords.length !== exactCount) {
    return { exact: false, rejected_before_iteration: true, reason: 'lane-count', ...base,
      expected_lane_count: expectedWords.length, actual_lane_count: actualWords.length, first_mismatch: null }
  }
  if (expectedBytes.length !== exactCount) {
    return { exact: false, rejected_before_iteration: true, reason: 'byte-count', ...base,
      expected_byte_count: expectedBytes.length, actual_byte_count: exactCount, first_mismatch: null }
  }
  const actualBytes = actual.toRgba8()
  if (actualBytes.length !== exactCount) {
    return { exact: false, rejected_before_iteration: true, reason: 'byte-count', ...base,
      expected_byte_count: expectedBytes.length, actual_byte_count: actualBytes.length, first_mismatch: null }
  }
  let changedLanes = 0
  let firstFloat = null
  for (let index = 0; index < exactCount; index += 1) {
    if (actualWords[index] === expectedWords[index]) continue
    changedLanes += 1
    firstFloat ??= mismatchRecord(index, expected.width, expectedWords, actualWords, expectedBytes, actualBytes, 'float32')
  }
  let changedBytes = 0
  let firstByte = null
  for (let index = 0; index < exactCount; index += 1) {
    if (actualBytes[index] === expectedBytes[index]) continue
    changedBytes += 1
    firstByte ??= mismatchRecord(index, expected.width, expectedWords, actualWords, expectedBytes, actualBytes, 'rgba8')
  }
  return { exact: changedLanes === 0 && changedBytes === 0, rejected_before_iteration: false, ...base,
    changed_lane_count: changedLanes, changed_rgba8_byte_count: changedBytes,
    first_mismatch: firstFloat ?? firstByte, first_float32_mismatch: firstFloat, first_rgba8_mismatch: firstByte }
}

function requireExact(actual, expected, label) {
  const result = compareExact(actual, expected, label)
  if (!result.exact) throw new Error(`${label}: ${JSON.stringify(result)}`)
  return { exact: true, changed_lane_count: 0, changed_rgba8_byte_count: 0,
    expected_dimensions: result.expected_dimensions, actual_dimensions: result.actual_dimensions }
}

function expectedRecord(surface) {
  return { width: surface.width, height: surface.height,
    float_words: words(surface.data).slice(), rgba8: new Uint8Array(surface.toRgba8()) }
}

function comparerSelfTests() {
  const expectReject = (result, reason) => {
    if (result.exact || !result.rejected_before_iteration || result.reason !== reason) {
      throw new Error(`cellRefract comparer did not preflight ${reason}`)
    }
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  expectReject(compareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape'), 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32'
      || !bytesOf(plusZero.toRgba8()).equals(bytesOf(minusZero.toRgba8()))) {
    throw new Error('cellRefract comparer missed signed zero')
  }
  const nanAData = new Float32Array(4)
  const nanBData = new Float32Array(4)
  new Uint32Array(nanAData.buffer).set([0x7fc00001, 0, 0, 0x3f800000])
  new Uint32Array(nanBData.buffer).set([0x7fc00002, 0, 0, 0x3f800000])
  const nanA = new Surface(1, 1, nanAData)
  const nanB = new Surface(1, 1, nanBData)
  const nanPayload = compareExact(nanB, expectedRecord(nanA), 'self/nan-payload')
  if (nanPayload.exact || nanPayload.first_mismatch?.kind !== 'float32'
      || !bytesOf(nanA.toRgba8()).equals(bytesOf(nanB.toRgba8()))) {
    throw new Error('cellRefract comparer missed NaN payload')
  }
  const finalLane = compareExact(new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)])),
    expectedRecord(plusZero), 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch?.channel !== 'a'
      || finalLane.first_mismatch?.lane_or_byte_index !== 3) {
    throw new Error('cellRefract comparer missed final alpha lane')
  }
  const byteExpected = expectedRecord(plusZero)
  byteExpected.rgba8[3] ^= 1
  const byteOnly = compareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch?.channel !== 'a') {
    throw new Error('cellRefract comparer missed independent byte mismatch')
  }
  for (const [label, mutated, reason] of [
    ['short-lanes', { ...expectedRecord(plusZero), float_words: new Uint32Array(3) }, 'lane-count'],
    ['long-lanes', { ...expectedRecord(plusZero), float_words: new Uint32Array(5) }, 'lane-count'],
    ['short-bytes', { ...expectedRecord(plusZero), rgba8: new Uint8Array(3) }, 'byte-count'],
    ['long-bytes', { ...expectedRecord(plusZero), rgba8: new Uint8Array(5) }, 'byte-count'],
  ]) expectReject(compareExact(plusZero, mutated, `self/${label}`), reason)
  return {
    equal_area_different_shape_rejected_before_access: true,
    signed_zero_rejected_with_equal_rgba8: true,
    distinct_quiet_nan_payload_rejected_with_equal_rgba8: true,
    final_float32_alpha_lane_reported: true,
    independent_final_rgba8_byte_reported: true,
    expected_lane_and_byte_count_short_and_long_rejected_before_iteration: true,
    signed_zero_first_mismatch: signedZero.first_mismatch,
    nan_payload_first_mismatch: nanPayload.first_mismatch,
    final_lane_first_mismatch: finalLane.first_mismatch,
    byte_only_first_mismatch: byteOnly.first_mismatch,
  }
}

// ---------------------------------------------------------------------------
// Input textures
//
// Every lane is a small dyadic rational, so every value is exact in binary32
// AND in binary64. That keeps the input itself from being a source of rounding
// that the reader would have to disentangle from the program's own. Alpha is
// exactly 1 in every lane of both patterns; the program copies the sampled
// alpha straight through, so every output alpha is exactly 0x3f800000/255.
// ---------------------------------------------------------------------------

const patterns = {
  ramp: (x, y) => [((3 * x + 5 * y) % 8) / 8, ((x + 3 * y) % 4) / 4, ((5 * x + y) % 16) / 16, 1],
  contrast: (x, y) => [(x % 4) < 2 ? 0 : 1, ((x + y) % 3 === 0) ? 0 : 1, y % 2, 1],
}

function makeInput(width, height, patternName) {
  const pattern = patterns[patternName]
  if (typeof pattern !== 'function') throw new Error(`unknown input pattern ${patternName}`)
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      // Surface rows are stored top-down; GLSL texture space is bottom-up, so
      // the pattern is evaluated in texture coordinates and stored flipped.
      const textureY = height - 1 - y
      const rgba = pattern(x, textureY)
      if (!Array.isArray(rgba) || rgba.length !== 4) throw new Error(`${patternName}: pattern must yield 4 lanes`)
      for (const [lane, value] of rgba.entries()) {
        if (typeof value !== 'number' || !Number.isFinite(value)) {
          throw new Error(`${patternName}: non-finite input lane at ${x},${y},${lane}`)
        }
        if (!Object.is(f(value), value)) {
          throw new Error(`${patternName}: input lane ${value} at ${x},${y},${lane} is not exactly f32-representable`)
        }
        data[(y * width + x) * 4 + lane] = value
      }
    }
  }
  return new Surface(width, height, data)
}

// ---------------------------------------------------------------------------
// Case definitions
// ---------------------------------------------------------------------------

// The tiled case is a genuine top-down crop window of a larger full render, per
// the Shapes' amended crop contract: tileOffset.y is
// `full_height - crop_y - tile_height`, never raw crop_y. NOTE, and this is a
// measured discovery recorded below: unlike `synth/shape`, this program's
// `localUV` subtracts `tileOffset` again before sampling, so the tile route is
// NOT a pixel-identical crop of the full route for this shader. The cells
// field itself IS world-aligned (proven below by an instrumented probe); only
// the final texture sample differs.
const cropRect = { crop_x: 4, crop_y: 2, tile_width: 4, tile_height: 6, full_width: 11, full_height: 9 }
const fullInput = makeInput(cropRect.full_width, cropRect.full_height, 'ramp')

const cases = [
  {
    name: 'cells-wrap-mirror',
    coverage: ['control-group anchor', 'the wrap == 0 mirror arm', 'landscape 16x9, aspect 16/9 not exactly f32-representable',
      'cellSmooth 40 so smin takes the h-quadratic branch', 'variation 30 mid arm', 'time 0.5 * floor(speed) 2 = 1 is integral, so the motion phase is zero (see time_speed_phase_census)',
      'witnesses smin-h-quadratic-dropped, prng-pcg-constant-perturbed, aspect-ratio-inverted, wrap-arm-swapped'],
    width: 16, height: 9, time: 0.5, seed: 7, wrap: 0,
    scale: 50, cellScale: 75, cellSmooth: 40, variation: 30,
    speed: 2, refractAmt: 55, direction: 90, pattern: 'ramp',
  },
  {
    name: 'cells-wrap-repeat',
    coverage: ['the wrap == 1 repeat arm', 'landscape 16x9', 'contrast input pattern',
      'cellSmooth 40 so smin takes the h-quadratic branch', 'variation 30 mid arm',
      'time 1.25 * floor(speed) 3 = 3.75 is non-integral, so the motion phase is live',
      'witnesses smin-h-quadratic-dropped, prng-pcg-constant-perturbed, aspect-ratio-inverted, wrap-arm-swapped'],
    width: 16, height: 9, time: 1.25, seed: 19, wrap: 1,
    scale: 50, cellScale: 75, cellSmooth: 40, variation: 30,
    speed: 3, refractAmt: 55, direction: 45, pattern: 'contrast',
  },
  {
    name: 'cells-extreme-variation',
    coverage: ['variation 100, the maximum of the variation arm', 'cellSmooth 0 so smin takes the k == 0.0 min branch',
      'square 12x12, aspect exactly 1.0 (non-reaching control for aspect-ratio-inverted)',
      'scale 80 / cellScale 99 extremes', 'speed 5, the maximum',
      'time 2.5 * floor(speed) 5 = 12.5 is non-integral, so the motion phase is live',
      'witnesses prng-pcg-constant-perturbed, wrap-arm-swapped; control for smin-h-quadratic-dropped'],
    width: 12, height: 12, time: 2.5, seed: 31, wrap: 0,
    scale: 80, cellScale: 99, cellSmooth: 0, variation: 100,
    speed: 5, refractAmt: 80, direction: 180, pattern: 'ramp',
  },
  {
    name: 'tile-crop-translation',
    coverage: ['tile route through the Shapes-amended crop offset rule', 'the wrap == 1 repeat arm on an interior window where no coordinate leaves [0, 1) (control for wrap-arm-swapped)',
      'cellSmooth 40 so smin takes the h-quadratic branch (the smallest smin witness)',
      'fullResolution 11x9 differs from the destination 4x6', 'time 0.25 * floor(speed) 2 = 0.5 is non-integral, so the motion phase is live',
      'witnesses smin-h-quadratic-dropped, prng-pcg-constant-perturbed, aspect-ratio-inverted'],
    width: cropRect.tile_width, height: cropRect.tile_height,
    time: 0.25, seed: 5, wrap: 1,
    scale: 50, cellScale: 75, cellSmooth: 40, variation: 30,
    speed: 2, refractAmt: 55, direction: 90, pattern: 'ramp',
    tileOffset: [cropRect.crop_x, cropRect.full_height - cropRect.crop_y - cropRect.tile_height],
    fullResolution: [cropRect.full_width, cropRect.full_height],
    input: fullInput,
  },
]
if (cases.length !== 4) throw new Error(`cellRefract fixture census drift: ${cases.length}`)
if (new Set(cases.map((item) => item.name)).size !== cases.length) throw new Error('duplicate cellRefract case name')
for (const definition of cases) {
  for (const field of ['width', 'height']) {
    if (!Number.isInteger(definition[field]) || definition[field] <= 0) {
      throw new Error(`${definition.name}: ${field} must be a positive integer`)
    }
  }
  for (const field of ['time', 'scale', 'cellScale', 'cellSmooth', 'variation', 'speed', 'refractAmt', 'direction']) {
    const value = definition[field]
    if (typeof value !== 'number' || !Number.isFinite(value) || f(value) !== value) {
      throw new Error(`${definition.name}: ${field} must be an exact f32 number`)
    }
  }
  for (const field of ['seed', 'wrap']) {
    if (!Number.isInteger(definition[field])) throw new Error(`${definition.name}: ${field} must be an integer`)
  }
  if (definition.input === undefined && typeof patterns[definition.pattern] !== 'function') {
    throw new Error(`${definition.name}: unknown pattern`)
  }
}

// ---------------------------------------------------------------------------
// Rendering through the pinned public path
// ---------------------------------------------------------------------------

function uniformsFor(definition) {
  return {
    SHAPE: defines.SHAPE,
    KERNEL: defines.KERNEL,
    time: exactF32(definition.time, `${definition.name}.time`),
    seed: definition.seed,
    wrap: definition.wrap,
    scale: exactF32(definition.scale, `${definition.name}.scale`),
    cellScale: exactF32(definition.cellScale, `${definition.name}.cellScale`),
    cellSmooth: exactF32(definition.cellSmooth, `${definition.name}.cellSmooth`),
    variation: exactF32(definition.variation, `${definition.name}.variation`),
    speed: exactF32(definition.speed, `${definition.name}.speed`),
    refractAmt: exactF32(definition.refractAmt, `${definition.name}.refractAmt`),
    direction: exactF32(definition.direction, `${definition.name}.direction`),
    effectWidth: exactF32(definition.effectWidth ?? 0, `${definition.name}.effectWidth`),
    ...(definition.extraUniforms ?? {}),
  }
}

function exactF32(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${label}: finite number required`)
  return f(value)
}

function bindingOptions(definition) {
  const uniforms = uniformsFor(definition)
  if (definition.omitKernel) delete uniforms.KERNEL
  return {
    width: definition.width,
    height: definition.height,
    time: exactF32(definition.time, `${definition.name}.time`),
    seed: 1,
    uniforms,
    textures: { inputTex: definition.input ?? makeInput(definition.width, definition.height, definition.pattern) },
    tileOffset: f32Vector(definition.tileOffset ?? [0, 0], 2),
    fullResolution: f32Vector(definition.fullResolution ?? [definition.width, definition.height], 2),
  }
}

// `bindCanonicalKernel` is the pinned public entry point; it composes
// `createCanonicalBindings` and `bindGlslKernel` from the frozen snapshot.
function render(factory, definition) {
  const options = bindingOptions(definition)
  const input = options.textures.inputTex
  const inputBefore = words(input.data).slice()
  const callerVectors = {
    tileOffset: options.tileOffset, fullResolution: options.fullResolution,
  }
  const before = Object.fromEntries(Object.entries(callerVectors).map(([name, value]) => [name, words(value).slice()]))
  const bindings = createCanonicalBindings(options)
  const output = new Surface(definition.width, definition.height)
  runPass({
    kernel: bindCanonicalKernel(factory, options),
    destination: output,
    time: definition.externalTime ?? 0,
    seed: definition.externalSeed ?? 1,
  })
  const inputAfter = words(input.data)
  if (inputBefore.some((word, index) => word !== inputAfter[index])) {
    throw new Error(`${definition.name}: the input texture was mutated by the render`)
  }
  for (const [name, value] of Object.entries(callerVectors)) {
    const after = words(value)
    if (before[name].some((word, index) => word !== after[index])) throw new Error(`${definition.name}: caller vector ${name} mutated`)
  }
  return { output, input, bindings, options }
}

function digests(surface) {
  return { f32_sha256: sha256(bytesOf(surface.data)), rgba8_sha256: sha256(bytesOf(surface.toRgba8())) }
}

function surfaceRecord(surface) {
  const rawWords = words(surface.data)
  const rgba8 = surface.toRgba8()
  const finite = surface.data.filter(Number.isFinite).length
  const alphaWords = new Set()
  const alphaBytes = new Set()
  for (let index = 3; index < rawWords.length; index += 4) {
    alphaWords.add(u32Hex(rawWords[index]))
    alphaBytes.add(rgba8[index])
  }
  if (alphaWords.size !== 1 || !alphaWords.has('0x3f800000')) {
    throw new Error(`alpha float words are not uniformly 0x3f800000: ${[...alphaWords].join(',')}`)
  }
  if (alphaBytes.size !== 1 || !alphaBytes.has(255)) {
    throw new Error(`alpha RGBA8 bytes are not uniformly 255: ${[...alphaBytes].join(',')}`)
  }
  if (finite !== surface.data.length) throw new Error('non-finite output lane')
  return {
    width: surface.width,
    height: surface.height,
    f32_words_le: Array.from(rawWords, u32Hex),
    f32_sha256: sha256(bytesOf(surface.data)),
    rgba8_bytes: Array.from(rgba8),
    rgba8_sha256: sha256(bytesOf(rgba8)),
    finite_lane_count: finite,
    nonfinite_lane_count: surface.data.length - finite,
    alpha_f32_word: '0x3f800000',
    alpha_rgba8_byte: 255,
  }
}

function inputRecord(surface) {
  const rawWords = words(surface.data)
  return {
    width: surface.width,
    height: surface.height,
    row_order: 'top-down storage; the GLSL texture origin is bottom-left and texture() flips',
    f32_words_le: Array.from(rawWords, u32Hex),
    f32_sha256: sha256(bytesOf(surface.data)),
    every_lane_exactly_f32_representable: true,
  }
}

function bindingRecords(definition, resolvedBindings, input) {
  const out = {}
  for (const name of bindingNames) {
    const abi = bindingAbi[name]
    if (abi === 'sampler2D') {
      out[name] = { abi, width: input.width, height: input.height, f32_sha256: sha256(bytesOf(input.data)) }
      continue
    }
    const value = resolvedBindings[name]
    if (abi === 'int32') {
      if (!Number.isInteger(value) || value < -2147483648 || value > 2147483647) throw new Error(`${name}: not an int32`)
      out[name] = { abi, value }
    } else if (abi === 'number') {
      if (typeof value !== 'number' || f(value) !== value) throw new Error(`${name}: not an exact f32 scalar`)
      out[name] = { abi, f32_value: value, f32_word_le: f32Bits(value) }
    } else {
      const lanes = vecLanes[abi]
      if (!(value instanceof Float32Array) || value.length !== lanes) throw new Error(`${name}: not a ${abi}`)
      out[name] = { abi, f32_values: Array.from(value), f32_words_le: Array.from(words(value), u32Hex) }
    }
  }
  if (Object.keys(out).length !== bindingNames.length) throw new Error('binding census drift')
  return out
}

function externalRecord(definition) {
  const time = f(definition.externalTime ?? 0)
  const seed = f(definition.externalSeed ?? 1)
  return {
    time: { f32_value: time, f32_word_le: f32Bits(time) },
    seed: { f32_value: seed, f32_word_le: f32Bits(seed) },
  }
}

const canonicalExpected = new Map()
const renderCases = cases.map((definition) => {
  const canonical = render(canonicalFactory, definition)
  const repeat = render(canonicalFactory, definition)
  const publicRoute = render(publicFactory, definition)
  if (canonical.output.data.buffer === repeat.output.data.buffer
      || canonical.output.data.buffer === publicRoute.output.data.buffer) {
    throw new Error(`${definition.name}: routes share output backing storage`)
  }
  const expected = expectedRecord(canonical.output)
  const repeatIdentity = requireExact(repeat.output, expected, `${definition.name}/canonical-repeat`)
  const publicIdentity = requireExact(publicRoute.output, expected, `${definition.name}/public-canonical`)
  canonicalExpected.set(definition.name, expected)
  return {
    name: definition.name,
    coverage: definition.coverage,
    route: definition.tileOffset ? 'tile' : 'full',
    width: definition.width,
    height: definition.height,
    input_texture: inputRecord(canonical.input),
    bindings: bindingRecords(definition, canonical.bindings, canonical.input),
    external_pass: externalRecord(definition),
    output_expected: surfaceRecord(canonical.output),
    canonical_repeat: repeatIdentity,
    public_canonical: publicIdentity,
  }
})

// ---------------------------------------------------------------------------
// Mutant compilation
// ---------------------------------------------------------------------------

// A ledger mutant is one anchor, one replacement, unless an ordered `anchors`
// list is given; each anchor must still match exactly once.
function compileMutant(spec) {
  let mutatedText = canonicalText
  const anchors = spec.anchors ?? [[spec.anchor, spec.replacement]]
  const occurrences = []
  for (const [anchor, replacement] of anchors) {
    const count = mutatedText.split(anchor).length - 1
    if (count !== 1) throw new Error(`${spec.name}: mutation anchor matched ${count} times`)
    occurrences.push(count)
    mutatedText = mutatedText.replace(anchor, replacement)
  }
  if (mutatedText === canonicalText) throw new Error(`${spec.name}: mutation is a no-op rewrite`)
  return {
    anchors,
    occurrences,
    mutatedText,
    factory: Function(`"use strict"; return (${mutatedText});`)(),
  }
}

function mutantIdentity(spec, compiled) {
  return {
    anchor_count: compiled.anchors.length,
    anchor_sha256: compiled.anchors.map(([anchor]) => sha256(anchor)),
    replacement_sha256: compiled.anchors.map(([, replacement]) => sha256(replacement)),
    anchor_occurrences: compiled.occurrences,
    mutated_factory_sha256: sha256(compiled.mutatedText),
  }
}

function measureAcrossCases(factory, label) {
  return cases.map((definition) => {
    const output = render(factory, definition).output
    const comparison = compareExact(output, canonicalExpected.get(definition.name), `${label}/${definition.name}`)
    return {
      case: definition.name,
      differs: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      changed_rgba8_byte_count: comparison.changed_rgba8_byte_count ?? 0,
      ...digests(output),
      first_mismatch: comparison.first_float32_mismatch ?? null,
    }
  })
}

// ---------------------------------------------------------------------------
// The mutation ledger
//
// Every entry was verified bit-differing on at least one case BEFORE it was
// budgeted (cellrefract-design.md section 7). All four target the REACHABLE
// path at the frozen defines; their witness sets overlap BY CONSTRUCTION (any
// case with displacement, aspect != 1, and cellSmooth > 0 discriminates
// several at once), which is disclosed rather than engineered away: these are
// not four competing materializations of one contract -- each pins a different
// function on the reachable path -- so the per-case table, not disjointness,
// is what attributes a divergence.
// ---------------------------------------------------------------------------

const sminReturn = 'return min(a, b) - ((h * h) * k) * (0.25);'
const prngReturn = 'return pcg(cpu_uvec3_vec3(p)).map(function (_) {return cpu_float(cpu_float(_) / cpu_float(4294967296));});'
const aspectCall = 'var d = cells(new $runtime.PooledFloat32Array([st[0] * (fullResolution[0] / fullResolution[1]), st[1]]), freq, cellSize);'

const mutantSpecs = [
  {
    name: 'smin-h-quadratic-dropped',
    target: 'smin\'s smooth-min term `min(a,b) - h*h*k*0.25`: the h-quadratic is dropped',
    contract: 'the smooth-min blend of neighbouring cell distances; affects every case with cellSmooth > 0',
    anchor: sminReturn,
    replacement: 'return min(a, b);',
    reaching: 'cases with cellSmooth > 0 (k = cellSmooth * 0.01 != 0); the k == 0.0 branch of cells-extreme-variation cannot see it',
    expected: {
      'cells-wrap-mirror': true,
      'cells-wrap-repeat': true,
      'cells-extreme-variation': false,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'prng-pcg-constant-perturbed',
    target: 'prng\'s pcg-output normalizer: the divisor 4294967296 (2^32) is halved to 2147483648',
    contract: 'the prng chain (pcg3d then / 2^32) feeds every cell point offset; the whole cells field moves',
    anchor: prngReturn,
    replacement: 'return pcg(cpu_uvec3_vec3(p)).map(function (_) {return cpu_float(cpu_float(_) / cpu_float(2147483648));});',
    reaching: 'every case: the initial st offset, r1, r2, and the point base all flow through prng',
    expected: {
      'cells-wrap-mirror': true,
      'cells-wrap-repeat': true,
      'cells-extreme-variation': true,
      'tile-crop-translation': true,
    },
    note: 'A near-ULP perturbation of the same constant (4294967295) is measured invariant on every '
      + 'case -- see prng_near_ulp_invariance. The divisor had to move by a factor of two before any '
      + 'sample crossed a texel boundary, because texture() is nearest-sampling and absorbs '
      + 'sub-texel perturbations. The chain is still exactly pinned by the halved-divisor witness.',
  },
  {
    name: 'aspect-ratio-inverted',
    target: 'the aspect ratio applied to st.x before cells: fullResolution[0] / fullResolution[1] inverted',
    contract: 'the x-scaling of the cell field; a square destination (aspect exactly 1.0) cannot see an inversion',
    anchor: aspectCall,
    replacement: 'var d = cells(new $runtime.PooledFloat32Array([st[0] * (fullResolution[1] / fullResolution[0]), st[1]]), freq, cellSize);',
    reaching: 'cases whose fullResolution aspect is not exactly 1.0',
    expected: {
      'cells-wrap-mirror': true,
      'cells-wrap-repeat': true,
      'cells-extreme-variation': false,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'wrap-arm-swapped',
    target: 'the two wrap arms: the wrap == 0 (mirror) and wrap == 1 (repeat) conditions are exchanged',
    contract: 'abs(mod(st + 1, 2) - 1) versus fract(st); identical on [0, 1) and different outside it',
    anchors: [
      ['if (wrap == 0) {', 'if (__cellrefract_wrap_swap) {'],
      ['if (wrap == 1) {', 'if (wrap == 0) {'],
      ['if (__cellrefract_wrap_swap) {', 'if (wrap == 1) {'],
    ],
    reaching: 'cases where the refraction displacement pushes some st outside [0, 1); an interior tile '
      + 'window never leaves [0, 1) and cannot see the swap',
    expected: {
      'cells-wrap-mirror': true,
      'cells-wrap-repeat': true,
      'cells-extreme-variation': true,
      'tile-crop-translation': false,
    },
  },
]

const mutationLedger = mutantSpecs.map((spec) => {
  if (Object.keys(spec.expected).length !== cases.length) {
    throw new Error(`${spec.name}: expected discrimination table does not cover every case`)
  }
  const compiled = compileMutant(spec)
  const results = measureAcrossCases(compiled.factory, spec.name).map((result) => {
    const expected = spec.expected[result.case]
    if (typeof expected !== 'boolean') throw new Error(`${spec.name}: no expectation for ${result.case}`)
    if (result.differs !== expected) {
      throw new Error(`${spec.name}: case ${result.case} expected discriminates=${expected} but measured `
        + `${result.differs}; a flipped case is a stop condition, not something to re-baseline`)
    }
    return { expected_discriminates: expected, ...result }
  })
  if (!results.some((result) => result.differs)) throw new Error(`${spec.name}: no case discriminates this mutant`)
  return {
    name: spec.name,
    target: spec.target,
    contract: spec.contract,
    reaching: spec.reaching,
    ...(spec.note ? { note: spec.note } : {}),
    classification: 'rendered canonical-JS one-anchor/one-replacement mutant (the wrap swap uses an ordered three-anchor chain through a unique temp identifier)',
    ...mutantIdentity(spec, compiled),
    witness_cases: results.filter((result) => result.differs).map((result) => result.case),
    control_cases: results.filter((result) => !result.differs).map((result) => result.case),
    results,
  }
})

// ---------------------------------------------------------------------------
// The NON-reaching control: a mutant inside a KERNEL != 0 branch.
//
// `convolutionKernel`'s KERNEL == 4 arm reads the emboss table. At the frozen
// KERNEL = 0 main() never calls convolutionKernel at all, so swapping the
// table the dead arm reads MUST change nothing anywhere. That invariance is
// the pixel witness that the JavaScript runtime skip (bound KERNEL = 0) agrees
// with the corpus normalizer's strip (KERNEL = 0 removed the call).
// ---------------------------------------------------------------------------

const nonreachingSpec = {
  name: 'kernel4-arm-emboss-to-sharpen',
  target: 'inside convolutionKernel\'s KERNEL == 4 branch: convolve(localUV, emboss, false) is redirected to sharpen',
  contract: 'dead at KERNEL = 0: main()\'s `if (KERNEL != 0)` block is skipped, so convolutionKernel is never called',
  anchor: 'return convolve(localUV, emboss, false);',
  replacement: 'return convolve(localUV, sharpen, false);',
}
const nonreachingCompiled = compileMutant(nonreachingSpec)
const nonreachingRows = measureAcrossCases(nonreachingCompiled.factory, nonreachingSpec.name)
if (nonreachingRows.some((row) => row.differs)) {
  throw new Error('the KERNEL != 0 branch control mutant diverged at KERNEL = 0; the runtime skip does '
    + 'not match the normalizer strip and the whole frozen-define premise is wrong')
}
const nonreachingControl = {
  status: 'proven-invariant-everywhere',
  design_reference: 'cellrefract-design.md section 7, non-reaching control',
  rendered_mutant: { name: nonreachingSpec.name, ...mutantIdentity(nonreachingSpec, nonreachingCompiled), rows: nonreachingRows },
  rendered_divergences: nonreachingRows.reduce((total, row) => total + row.changed_lane_count, 0),
  claim: 'The divergence channel through convolutionKernel EXISTS in the JavaScript (see '
    + 'kernel_liveness_census: KERNEL = 1/4/7 with effectWidth != 0 change hundreds of lanes) but is '
    + 'CLOSED at the frozen define. The port has no KERNEL binding at all; a port that accidentally '
    + 'emitted a live KERNEL != 0 path would diverge from this oracle on every case, and a port that '
    + 'wrongly stripped the reachable path would fail the ledger mutants. This control proves the '
    + 'oracle itself can tell the two apart.',
}

// ---------------------------------------------------------------------------
// The write-only tables axis: no table-content mutant is pixel-discriminable.
//
// The five tables' only readers live in convolutionKernel's KERNEL != 0
// branches (edge is never read anywhere at all). At the frozen defines the
// tables are write-only, so changing a stored constant cannot move a pixel.
// This is MEASURED, not assumed: the mutant below rewrites emboss[0] = -2 to
// -7 and renders every case. Design section 7 forbids budgeting a table mutant
// and this is not one -- it is the recorded reason why none is budgeted.
// ---------------------------------------------------------------------------

const tableSpec = {
  name: 'kernel-table-emboss0-perturbed',
  anchor: 'emboss[0] = -2;',
  replacement: 'emboss[0] = -7;',
}
const tableCompiled = compileMutant(tableSpec)
const tableRows = measureAcrossCases(tableCompiled.factory, tableSpec.name)
if (tableRows.some((row) => row.differs)) {
  throw new Error('a kernel-table content mutant diverged at KERNEL = 0; the tables are not write-only '
    + 'and design section 7\'s satisfiability analysis is wrong')
}
const writeOnlyTablesAxis = {
  status: 'cannot-diverge-do-not-ship',
  design_reference: 'cellrefract-design.md sections 1 and 7',
  element_count: 45,
  elements: kernelTables,
  identifier_occurrence_census: tableOccurrenceCensus,
  occurrence_rule: 'declaration + nine loadKernels stores + whole-array arguments inside '
    + 'convolutionKernel\'s KERNEL != 0 branches; edge is never read anywhere (10 occurrences, '
    + 'declaration + stores only), edge2 twice (12), the others once each (11)',
  rendered_mutant: { name: tableSpec.name, ...mutantIdentity(tableSpec, tableCompiled), rows: tableRows },
  rendered_divergences: tableRows.reduce((total, row) => total + row.changed_lane_count, 0),
  claim: 'Every one of the 45 stored constants is a small integer exactly representable in binary32 '
    + 'AND binary64, and no reader executes at KERNEL = 0, so no value in this program distinguishes '
    + 'std::array<double, 9> from std::array<float, 9> and no table CONTENT mutation can move a pixel. '
    + 'The double element contract and the exact 45 (table, index, value) triples are proven '
    + 'STRUCTURALLY -- by the emitted native type, by the JavaScript being plain Arrays, and by the '
    + 'frontend profile\'s frozen store census -- and a green pixel run is not evidence for them. '
    + 'Shipping a table mutant as a control would be shipping a mutant that cannot diverge.',
}

// ---------------------------------------------------------------------------
// prng near-ULP invariance: why the ledger mutant uses a factor-of-two divisor
// ---------------------------------------------------------------------------

const nearUlpSpec = {
  name: 'prng-divisor-ulp-perturbed',
  anchor: prngReturn,
  replacement: 'return pcg(cpu_uvec3_vec3(p)).map(function (_) {return cpu_float(cpu_float(_) / cpu_float(4294967295));});',
}
const nearUlpCompiled = compileMutant(nearUlpSpec)
const nearUlpRows = measureAcrossCases(nearUlpCompiled.factory, nearUlpSpec.name)
if (nearUlpRows.some((row) => row.differs)) {
  throw new Error('the near-ULP prng perturbation diverged; the nearest-sampling quantization argument is wrong')
}
const prngNearUlpInvariance = {
  status: 'measured-invariant',
  rendered_mutant: { name: nearUlpSpec.name, ...mutantIdentity(nearUlpSpec, nearUlpCompiled), rows: nearUlpRows },
  rendered_divergences: nearUlpRows.reduce((total, row) => total + row.changed_lane_count, 0),
  reason: 'texture() is nearest-sampling: the output depends only on which texel localUV lands in. A '
    + '2^-32 relative perturbation of every prng output moves samples by far less than a texel, so '
    + 'the image is bit-identical. The pcg chain is nonetheless exactly pinned, by '
    + 'prng-pcg-constant-perturbed\'s factor-of-two witness.',
}

// ---------------------------------------------------------------------------
// Tile-vs-full translation: the Shapes-amended crop offset rule, measured.
//
// Design section 7 assumed the Shapes crop contract carries over (tile output
// == top-down crop of full output). MEASURED: it does NOT. This shader's
// localUV subtracts tileOffset again before sampling, so the tile samples the
// input in destination-local coordinates while the cells field stays
// world-aligned. Both facts are measured below: the d-field probe (publish d
// through fragColor) is an exact crop (0 mismatches); the final colour is not.
// The tile route is pinned as its own parity case either way.
// ---------------------------------------------------------------------------

const tileCaseName = 'tile-crop-translation'
const tileDefinition = cases.find((item) => item.name === tileCaseName)
const fullRouteDefinition = {
  ...tileDefinition,
  name: `${tileCaseName}/full-route`,
  width: cropRect.full_width,
  height: cropRect.full_height,
  tileOffset: [0, 0],
  fullResolution: [cropRect.full_width, cropRect.full_height],
}
const fullRoute = render(canonicalFactory, fullRouteDefinition)
const fullWords = words(fullRoute.output.data)
const fullBytes = fullRoute.output.toRgba8()
const tileOutput = canonicalExpected.get(tileCaseName)
let cropWordMismatches = 0
let cropByteMismatches = 0
let cropFirstMismatch = null
for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
  for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
    for (let channel = 0; channel < 4; channel += 1) {
      const tileIndex = ((ty * cropRect.tile_width) + tx) * 4 + channel
      const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4 + channel
      if (tileOutput.float_words[tileIndex] !== fullWords[fullIndex]) {
        cropWordMismatches += 1
        cropFirstMismatch ??= {
          top_down_xy: [tx, ty], channel: channels[channel],
          tile_word: u32Hex(tileOutput.float_words[tileIndex]), full_word: u32Hex(fullWords[fullIndex]),
        }
      }
      if (tileOutput.rgba8[tileIndex] !== fullBytes[fullIndex]) cropByteMismatches += 1
    }
  }
}
if (cropWordMismatches === 0) {
  throw new Error('the tile route IS an exact crop of the full route; the measured non-identity record '
    + 'and its mechanistic explanation must be re-derived')
}
if (cropWordMismatches === cropRect.tile_width * cropRect.tile_height * 4) {
  throw new Error('the tile route shares no lane with the crop of the full route; the routes are unrelated')
}

// The raw-crop-y trap: binding raw top-down crop_y into tileOffset.y must
// differ from the correct tile (the Shapes witness, still non-vacuous here).
const rawCropYDefinition = { ...tileDefinition, name: `${tileCaseName}/raw-crop-y-trap`,
  tileOffset: [cropRect.crop_x, cropRect.crop_y] }
const rawCropYOutput = render(canonicalFactory, rawCropYDefinition).output
const rawCropYComparison = compareExact(rawCropYOutput, tileOutput, 'translation/raw-crop-y-trap')
if (rawCropYComparison.exact) throw new Error('raw top-down crop_y trap is indistinguishable; the witness is vacuous')

// Mechanistic proof, part 1: publish the cells field d through fragColor on
// both routes. The tile d must be an EXACT crop of the full d -- globalCoord
// carries the world position through tileOffset.
const publishAnchor = '(fragColor[0] = color[0], fragColor[1] = color[1], fragColor[2] = color[2], fragColor[3] = color[3], fragColor);'
const dProbeSpec = {
  name: 'dfield-probe',
  anchors: [[publishAnchor, '(fragColor[0] = d, fragColor[1] = d, fragColor[2] = d, fragColor[3] = 1, fragColor);']],
}
const dProbe = compileMutant(dProbeSpec)
const fullD = render(dProbe.factory, fullRouteDefinition).output
const tileD = render(dProbe.factory, tileDefinition).output
const fullDWords = words(fullD.data)
const tileDWords = words(tileD.data)
let dFieldMismatches = 0
for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
  for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
    for (let channel = 0; channel < 4; channel += 1) {
      const tileIndex = ((ty * cropRect.tile_width) + tx) * 4 + channel
      const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4 + channel
      if (tileDWords[tileIndex] !== fullDWords[fullIndex]) dFieldMismatches += 1
    }
  }
}
if (dFieldMismatches !== 0) {
  throw new Error('the cells field is not world-aligned through tileOffset; the non-identity explanation must be re-derived')
}

// Mechanistic proof, part 2: publish localUV on both routes. The tile localUV
// is the full localUV minus tileOffset/textureSize, so it is never equal.
const uvProbeSpec = {
  name: 'localuv-probe',
  anchors: [[publishAnchor, '(fragColor[0] = localUV[0], fragColor[1] = localUV[1], fragColor[2] = 0, fragColor[3] = 1, fragColor);']],
}
const uvProbe = compileMutant(uvProbeSpec)
const fullUV = render(uvProbe.factory, fullRouteDefinition).output
const tileUV = render(uvProbe.factory, tileDefinition).output
const fullUVWords = words(fullUV.data)
const tileUVWords = words(tileUV.data)
let uvEqualLanes = 0
let uvComparedLanes = 0
for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
  for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
    for (let channel = 0; channel < 2; channel += 1) {
      const tileIndex = ((ty * cropRect.tile_width) + tx) * 4 + channel
      const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4 + channel
      uvComparedLanes += 1
      if (tileUVWords[tileIndex] === fullUVWords[fullIndex]) uvEqualLanes += 1
    }
  }
}
if (uvEqualLanes !== 0) {
  throw new Error('a tile localUV lane equals the full-route lane; the translation account must be re-derived')
}

const tileTranslation = {
  case: tileCaseName,
  rect: cropRect,
  tile_offset_rule: 'tileOffset = (crop_x, full_height - crop_y - tile_height)',
  tile_offset_f32_words_le: Array.from(words(f32Vector([cropRect.crop_x,
    cropRect.full_height - cropRect.crop_y - cropRect.tile_height], 2)), u32Hex),
  full_route_expected: surfaceRecord(fullRoute.output),
  design_expectation: 'cellrefract-design.md section 7 assumed the Shapes-amended crop contract carries '
    + 'over: tile output == top-down crop of full output, compared exactly.',
  measured: 'the tile output is NOT a crop of the full output',
  word_mismatches: cropWordMismatches,
  byte_mismatches: cropByteMismatches,
  is_exact_crop: false,
  first_mismatch: cropFirstMismatch,
  why: 'globalCoord = gl_FragCoord + tileOffset carries the world position into st and the cells '
    + 'field, exactly as in Shapes. But this shader then computes localUV = (st * fullResolution - '
    + 'tileOffset) / textureSize, and st * fullResolution - tileOffset cancels back to gl_FragCoord: '
    + 'the tile samples the input in DESTINATION-LOCAL coordinates, a constant tileOffset/texSize '
    + 'translation away from the full route\'s sample. Both halves are measured below.',
  d_field_alignment_witness: {
    classification: 'instrumented canonical-JS probe factory; NOT a parity array and never compared to a rendered shade',
    probe: { name: dProbeSpec.name, ...mutantIdentity(dProbeSpec, dProbe) },
    rule: 'fragColor publishes the cells field d on both routes; the tile d must equal the top-down crop of the full d exactly',
    exact_word_mismatches: dFieldMismatches,
    full_route_d_words_le: Array.from(fullDWords, u32Hex),
    full_route_d_sha256: sha256(bytesOf(fullD.data)),
    tile_d_words_le: Array.from(tileDWords, u32Hex),
    tile_d_sha256: sha256(bytesOf(tileD.data)),
  },
  local_uv_translation_witness: {
    classification: 'instrumented canonical-JS probe factory; NOT a parity array and never compared to a rendered shade',
    probe: { name: uvProbeSpec.name, ...mutantIdentity(uvProbeSpec, uvProbe) },
    rule: 'fragColor publishes localUV.xy on both routes; the tile lane is the full lane translated by '
      + '-tileOffset/textureSize, so NO lane (of the x/y pairs compared) may be equal',
    compared_lane_count: uvComparedLanes,
    equal_lane_count: uvEqualLanes,
    full_route_uv_words_le: Array.from(fullUVWords, u32Hex),
    full_route_uv_sha256: sha256(bytesOf(fullUV.data)),
    tile_uv_words_le: Array.from(tileUVWords, u32Hex),
    tile_uv_sha256: sha256(bytesOf(tileUV.data)),
  },
  raw_crop_y_trap: {
    tile_offset_f32_words_le: Array.from(words(f32Vector([cropRect.crop_x, cropRect.crop_y], 2)), u32Hex),
    differs_from_correct_tile: true,
    changed_lane_count: rawCropYComparison.changed_lane_count,
    first_mismatch: rawCropYComparison.first_float32_mismatch,
  },
  consequence: 'The tile route is pinned as its own parity case and the full 11x9 route is stored beside '
    + 'it; a native port must reproduce BOTH. No crop identity may be asserted for this program, and '
    + 'the native test must not compare the tile against a crop of the full route.',
}

// ---------------------------------------------------------------------------
// One-axis control group on cells-wrap-mirror (the kernel-zero-invariance axis)
// ---------------------------------------------------------------------------

const anchorName = 'cells-wrap-mirror'
const controlAnchor = cases.find((item) => item.name === anchorName)
const controlBaselineExpected = canonicalExpected.get(anchorName)

function controlRow(name, overrides, expectation, axis, note) {
  const definition = { ...controlAnchor, ...overrides, name: `${anchorName}/${name}` }
  const rendered = render(canonicalFactory, definition)
  const comparison = compareExact(rendered.output, controlBaselineExpected, `control/${name}`)
  const observed = comparison.exact ? 'identical' : 'differs'
  return {
    name,
    axis,
    expectation,
    observed,
    pass: observed === expectation,
    changed_lane_count: comparison.changed_lane_count ?? 0,
    changed_rgba8_byte_count: comparison.changed_rgba8_byte_count ?? 0,
    first_mismatch: comparison.first_float32_mismatch ?? null,
    external_pass: externalRecord(definition),
    bindings: bindingRecords(definition, rendered.bindings, rendered.input),
    output: surfaceRecord(rendered.output),
    note,
  }
}

const controlGroup = {
  anchor: anchorName,
  baseline: {
    external_pass: externalRecord(controlAnchor),
    f32_sha256: renderCases[0].output_expected.f32_sha256,
    rgba8_sha256: renderCases[0].output_expected.rgba8_sha256,
  },
  controls: [
    controlRow('external-pass-extreme', { externalTime: 2147483648, externalSeed: -2147483648 },
      'identical', 'external runPass time/seed words (0x4f000000, 0xcf000000)',
      'the factory reads $bindings only; runPass context time/seed are never consumed'),
    controlRow('kernel-binding-unbound', { omitKernel: true },
      'identical', 'the KERNEL runtime binding: bound 0 versus absent entirely (undefined)',
      'THE kernel-zero-invariance axis. `var KERNEL = $bindings["KERNEL"]` resolves to undefined '
        + 'when the binding is absent, and `undefined != 0` is false, so main() skips the KERNEL '
        + 'block exactly as it does at the frozen bound value. The port has NO KERNEL binding at '
        + 'all; this axis asserts the absence of a divergence channel. See kernel_liveness_census '
        + 'for the live half.'),
    controlRow('bound-time-live', { time: 0.3 },
      'differs', 'bound time 0x3f000000 -> 0x3e99999a',
      'the live half of the time axis: 0.3 * floor(speed 2) = 0.6 is non-integral, so the sin/cos '
        + 'motion phase moves. See time_speed_phase_census for the integrality rule'),
    controlRow('effect-width-extreme', { effectWidth: 7 },
      'identical', 'bound effectWidth 0 -> 7',
      'effectWidth is read only inside main()\'s KERNEL != 0 block and in convolve, both skipped at '
        + 'KERNEL = 0. It stays a required number ABI binding; see binding_inertness_census'),
  ],
}
{
  const external = controlGroup.controls[0]
  const kernel = controlGroup.controls[1]
  if (external.observed !== 'identical') {
    throw new Error('external runPass time/seed changed the output; the shader-owned uniforms do not dominate')
  }
  if (kernel.observed !== 'identical') {
    throw new Error('an unbound KERNEL changed the output; the kernel-zero-invariance axis failed')
  }
}
for (const control of controlGroup.controls) {
  if (!control.pass) throw new Error(`control ${control.name} expected ${control.expectation} but observed ${control.observed}`)
}

// ---------------------------------------------------------------------------
// KERNEL liveness census (Shapes section 11 pattern)
//
// The invariance above is only meaningful because the channel is real: bind
// KERNEL != 0 with effectWidth != 0 and the branch tree wakes up, reads the
// kernel tables through convolve, and changes hundreds of lanes. The frozen
// case set never binds either; these probes are synthetic ABI coverage, never
// parity cases.
// ---------------------------------------------------------------------------

const kernelProbeDefinitions = [
  { label: 'unbound', overrides: { omitKernel: true } },
  { label: '0', overrides: {} },
  { label: '1-with-effectwidth-4', overrides: { extraUniforms: { KERNEL: 1, effectWidth: 4 } } },
  { label: '4-with-effectwidth-4', overrides: { extraUniforms: { KERNEL: 4, effectWidth: 4 } } },
  { label: '7-with-effectwidth-4', overrides: { extraUniforms: { KERNEL: 7, effectWidth: 4 } } },
]
const kernelLivenessCensus = {
  probe_case: anchorName,
  rule: 'KERNEL is a runtime binding in the JavaScript, bound at the frozen define 0 on every parity '
    + 'case. The axis is closed there and open the moment a non-zero KERNEL meets a non-zero '
    + 'effectWidth -- the same branch tree the corpus normalizer strips. The port carries no KERNEL '
    + 'binding, so a port that accidentally leaves the channel open diverges from these very cases.',
  probes: kernelProbeDefinitions.map(({ label, overrides }) => {
    const definition = { ...controlAnchor, ...overrides, name: `kernel-probe-${label}` }
    const output = render(canonicalFactory, definition).output
    const comparison = compareExact(output, controlBaselineExpected, `kernel-probe/${label}`)
    return {
      kernel: label,
      differs_from_baseline: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
    }
  }),
}
{
  const [unbound, zero] = kernelLivenessCensus.probes
  if (unbound.differs_from_baseline || zero.differs_from_baseline) {
    throw new Error('KERNEL unbound/0 probes differ from the baseline; the frozen case set is not at KERNEL = 0')
  }
  if (unbound.f32_sha256 !== zero.f32_sha256) {
    throw new Error('KERNEL unbound and KERNEL 0 produced different images; the invariance axis failed')
  }
  if (!kernelLivenessCensus.probes.slice(2).every((probe) => probe.differs_from_baseline)) {
    throw new Error('a KERNEL != 0 probe is invariant; the liveness census is vacuous')
  }
}

// ---------------------------------------------------------------------------
// Binding inertness census: resolution and effectWidth
// ---------------------------------------------------------------------------

const inertBindings = ['resolution', 'effectWidth']
const bindingInertnessCensus = {
  probe_case: anchorName,
  rule: 'a binding is recorded inert only after the anchor case is re-rendered with deliberately '
    + 'extreme values and compared exactly. Inertness is a parity assertion: a port that wrongly made '
    + 'one of these live would differ from an oracle that is invariant.',
  inert: inertBindings.map((name) => {
    const probes = (name === 'resolution'
      ? [[131072.1, 0.3], [1, 1], [-16, -9]]
      : [7, 10, -3]).map((value) => {
      const definition = {
        ...controlAnchor,
        name: `${anchorName}/${name}-${JSON.stringify(value)}`,
        extraUniforms: { [name]: name === 'resolution' ? f32Vector(value, 2) : f(value) },
      }
      const output = render(canonicalFactory, definition).output
      const comparison = compareExact(output, controlBaselineExpected, `inertness/${name}`)
      return {
        value,
        differs_from_baseline: !comparison.exact,
        changed_lane_count: comparison.changed_lane_count ?? 0,
        f32_sha256: sha256(bytesOf(output.data)),
      }
    })
    return { binding: name, abi: bindingAbi[name], probes, live: probes.some((probe) => probe.differs_from_baseline) }
  }),
  live: ['inputTex', 'time', 'seed', 'tileOffset', 'fullResolution', 'scale', 'cellScale',
    'cellSmooth', 'variation', 'speed', 'refractAmt', 'direction', 'wrap'],
  reason: {
    resolution: 'declared and never referenced anywhere in the factory body (0 lane reads); it stays a '
      + 'required Vec2 ABI binding per the Shapes precedent',
    effectWidth: 'read only inside main()\'s KERNEL != 0 block and inside convolve; both are skipped at '
      + 'the frozen KERNEL = 0, so the reads never execute. It stays a required number ABI binding',
    inputTex: 'the only data input; sampled once per pixel in main and nine times per convolve call',
    time: 'the sin/cos motion phase; live wherever time * floor(speed) is non-integral (see time_speed_phase_census)',
    seed: 'feeds every prng call: the initial st offset, r1, r2, and the point base',
    tileOffset: 'read into globalCoord and subtracted again in localUV',
    fullResolution: 'st = globalCoord / fullResolution and the aspect ratio',
    scale: 'freq = map(scale, 1, 100, 20, 1)',
    cellScale: 'cellSize = map(cellScale, 1, 100, 3, 0.75)',
    cellSmooth: 'smin\'s k = cellSmooth * 0.01',
    variation: 'dist += r1[2] * (variation * 0.01)',
    speed: 'spd = floor(speed) scales the motion phase',
    refractAmt: 'ref = map(refractAmt, 0, 100, 0, 0.125), the displacement magnitude',
    direction: 'refLen = d + direction / 360, the displacement angle',
    wrap: 'selects the mirror/repeat arm, live wherever st leaves [0, 1)',
  },
}
for (const entry of bindingInertnessCensus.inert) {
  if (entry.live) throw new Error(`${entry.binding} is recorded inert but a probe changed the output`)
}
for (const name of inertBindings) {
  // Neither binding is ever lane-indexed; resolution appears only in its own
  // declaration (the var name plus the $bindings key string), and every
  // effectWidth read sits inside the KERNEL != 0 block or convolve, both
  // unreachable at the frozen defines.
  const laneReads = canonicalText.split(`${name}[`).length - 1
  if (laneReads !== 0) throw new Error(`${name} lane-read census drift: ${laneReads}`)
  const identifier = new RegExp(`\\b${name}\\b`, 'g')
  const occurrences = (canonicalText.match(identifier) ?? []).length
  const expectedOccurrences = name === 'resolution' ? 2 : 7
  if (occurrences !== expectedOccurrences) {
    throw new Error(`${name} identifier census drift: ${occurrences}, expected ${expectedOccurrences}`)
  }
}

// ---------------------------------------------------------------------------
// Live-binding liveness census (the counterpart table: each live binding moved)
// ---------------------------------------------------------------------------

const liveBindingProbes = [
  { binding: 'inputTex', overrides: { pattern: 'contrast' },
    note: 'the anchor renders the ramp pattern; switching the input texture to contrast moves the sampled texels' },
  { binding: 'time', overrides: { time: 0.3 } },
  { binding: 'seed', overrides: { seed: 123 } },
  { binding: 'tileOffset', overrides: { tileOffset: [131072.1, 0.3] } },
  { binding: 'fullResolution', overrides: { fullResolution: [1280, 720] } },
  { binding: 'scale', overrides: { scale: 37 } },
  { binding: 'cellScale', overrides: { cellScale: 13 } },
  { binding: 'cellSmooth', overrides: { cellSmooth: 0 } },
  { binding: 'variation', overrides: { variation: 0 } },
  { binding: 'speed', overrides: { speed: 1 } },
  { binding: 'refractAmt', overrides: { refractAmt: 23 } },
  { binding: 'direction', overrides: { direction: 270 } },
  { binding: 'wrap', overrides: { wrap: 1 } },
]
const bindingLivenessCensus = {
  probe_case: anchorName,
  rule: 'the live counterpart of binding_inertness_census: every binding recorded live must move the '
    + 'anchor output under at least one extreme probe, or the census is vacuous',
  probes: liveBindingProbes.map(({ binding, overrides }) => {
    const definition = { ...controlAnchor, ...overrides, name: `${anchorName}/live-${binding}` }
    const output = render(canonicalFactory, definition).output
    const comparison = compareExact(output, controlBaselineExpected, `liveness/${binding}`)
    return {
      binding,
      differs_from_baseline: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
    }
  }),
}
for (const probe of bindingLivenessCensus.probes) {
  if (!probe.differs_from_baseline) {
    throw new Error(`${probe.binding} is recorded live but its probe is invariant; the census is vacuous`)
  }
}

// ---------------------------------------------------------------------------
// time * floor(speed) phase census, and the speed classes
// ---------------------------------------------------------------------------

function phaseIntegral(definition) {
  return Number.isInteger(f(definition.time) * Math.floor(f(definition.speed)))
}
const phaseProbes = [
  { case: anchorName, note: 'time 0.5 * floor(speed 2) = 1 is integral', expectation: 'identical',
    overrides: { time: 1.5 }, noteProbe: 'time 0.5 -> 1.5 keeps time * spd integral (1.5 * 2 = 3)' },
  { case: anchorName, note: 'time 0.3 makes 0.3 * 2 = 0.6 non-integral', expectation: 'differs',
    overrides: { time: 0.3 }, noteProbe: 'time 0.5 -> 0.3' },
  { case: 'cells-wrap-repeat', note: 'time 1.25 * floor(speed 3) = 3.75 is non-integral', expectation: 'differs',
    overrides: { time: 2.0 }, noteProbe: 'time 1.25 -> 2.0 flips 3.75 to the integral 6.0' },
]
const timeSpeedPhaseCensus = {
  rule: 'the motion terms are sin(time * 2pi * floor(speed) + r2) and cos(...): time is inert wherever '
    + 'time * floor(speed) is an integer (the phase is a whole multiple of 2pi) and live elsewhere. '
    + 'The anchor case sits exactly on an integral phase; two probes move it off, one keeps it on.',
  per_case_phase: cases.map((definition) => ({
    case: definition.name,
    time: f(definition.time),
    floor_speed: Math.floor(f(definition.speed)),
    phase: f(definition.time) * Math.floor(f(definition.speed)),
    phase_is_integral: phaseIntegral(definition),
  })),
  probes: phaseProbes.map(({ case: caseName, expectation, overrides, noteProbe }) => {
    const definition = { ...cases.find((item) => item.name === caseName), ...overrides,
      name: `phase-probe-${caseName}-${JSON.stringify(overrides)}` }
    const output = render(canonicalFactory, definition).output
    const comparison = compareExact(output, canonicalExpected.get(caseName), `phase-probe/${caseName}`)
    const observed = comparison.exact ? 'identical' : 'differs'
    if (observed !== expectation) {
      throw new Error(`phase probe on ${caseName} expected ${expectation} but observed ${observed}`)
    }
    return {
      case: caseName,
      overrides,
      note: noteProbe,
      observed,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
    }
  }),
}
if (timeSpeedPhaseCensus.per_case_phase.some((row) => row.phase_is_integral) === false) {
  throw new Error('no case sits on an integral phase; the inert witness is missing')
}

const speedProbeValues = [0, 1, 2, 3, 4, 5]
const speedProbes = speedProbeValues.map((speed) => {
  const output = render(canonicalFactory, { ...controlAnchor, speed, name: `speed-${speed}` }).output
  return { speed, f32_sha256: sha256(bytesOf(output.data)) }
})
const speedClasses = {}
for (const probe of speedProbes) (speedClasses[probe.f32_sha256] ??= []).push(probe.speed)
const speedClassCensus = {
  probe_case: anchorName,
  rule: 'at the anchor\'s integral phase (time 0.5), every even floor(speed) collapses to phase 0 and '
    + 'every odd one to phase pi: exactly two equivalence classes cover the whole 0..5 param range',
  probes: speedProbes,
  distinct_digest_count: Object.keys(speedClasses).length,
  equivalence_classes: Object.values(speedClasses),
}
if (speedClassCensus.distinct_digest_count !== 2) {
  throw new Error(`the speed census found ${speedClassCensus.distinct_digest_count} classes, not the recorded two`)
}
if (speedClassCensus.equivalence_classes.some((cls) => cls.length !== 3)) {
  throw new Error('the speed equivalence classes are not the recorded even/odd triples')
}

// ---------------------------------------------------------------------------
// Fixture assembly
// ---------------------------------------------------------------------------

const caseNames = cases.map((item) => item.name)
function bucketBy(classify) {
  const buckets = {}
  for (const definition of cases) {
    const bucket = classify(definition)
    ;(buckets[bucket] ??= []).push(definition.name)
  }
  return buckets
}
const coverageAxes = {
  wrap_arm: bucketBy((definition) => (definition.wrap === 0 ? 'mirror_wrap_0' : 'repeat_wrap_1')),
  wrap_arm_liveness: bucketBy((definition) =>
    definition.name === 'tile-crop-translation' ? 'inert_interior_window' : 'live_displacement_out_of_unit_range'),
  smin_arm: bucketBy((definition) => (definition.cellSmooth === 0 ? 'k_zero_min_branch' : 'h_quadratic_branch')),
  full_resolution_aspect: bucketBy((definition) => {
    const [w, h] = definition.fullResolution ?? [definition.width, definition.height]
    return w === h ? 'square_aspect_exactly_1' : `aspect_${w}_over_${h}`
  }),
  time_speed_phase: bucketBy((definition) => (phaseIntegral(definition) ? 'integral_motion_phase' : 'non_integral_motion_phase')),
  route: bucketBy((definition) => (definition.tileOffset ? 'tile' : 'full')),
  input_pattern: bucketBy((definition) => definition.pattern),
  variation: bucketBy((definition) => (definition.variation === 100 ? 'maximum_100' : 'mid_30')),
}
for (const [axis, buckets] of Object.entries(coverageAxes)) {
  for (const [bucket, names] of Object.entries(buckets)) {
    if (names.length === 0) throw new Error(`coverage axis ${axis} bucket ${bucket} has no witness`)
    for (const name of names) if (!canonicalExpected.has(name)) throw new Error(`coverage axis ${axis} names unknown case ${name}`)
  }
}

const fixture = {
  schema,
  schema_version: schemaVersion,
  program_key: programKey,
  effect_key: effectKey,
  runtime_key: programKey,
  corpus_revision: corpusRevision,
  upstream_revision: UPSTREAM_REVISION,
  defines,
  runtime_binding_names: [...bindingNames],
  runtime_binding_abi: bindingAbi,
  compile_time_defines_are_not_bindings: true,
  defines_are_runtime_bindings_in_the_javascript: 'KERNEL and SHAPE are preprocessor defines in the '
    + 'corpus (stripped by the normalizer at the frozen values) but plain runtime bindings in the '
    + 'JavaScript factory. Every parity case binds them at exactly the frozen define values, and the '
    + 'kernel-binding-unbound control proves an absent KERNEL behaves identically to KERNEL = 0. The '
    + 'port has no KERNEL or SHAPE binding at all.',
  oracle_authority: `unmodified public ${factoryName} from an immutable noisemaker-for-cpu snapshot, `
    + 'executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates',
  mutable_global_contracts: Object.fromEntries(tableNames.map((name) => [name, {
    javascript_declaration: `var ${name} = [0, 0, 0, 0, 0, 0, 0, 0, 0];`,
    glsl_type: 'float[9], mutable, uninitialized',
    element_materialization: 'plain JS Array of Numbers, NOT a Float32Array',
    numeric_contract: 'doubles, NEVER narrowed to f32',
    native_element_type: 'double',
    writer: 'loadKernels, called once per pixel from main, re-writing all nine elements before any possible read',
    elements: kernelTables[name],
    identifier_occurrences: tableOccurrenceCensus[name],
    reads: name === 'edge'
      ? 'none anywhere, not even in KERNEL != 0 branches'
      : `whole-array arguments inside convolutionKernel's KERNEL != 0 branches only (${tableOccurrenceCensus[name] - 10} read sites)`,
    oracle_discriminable: false,
    why_not_discriminable: 'write-only at the frozen defines; see write_only_tables_axis',
  }])),
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays; never reconstructed from expected words',
    tolerance: 'none',
    comparison_order: 'dimensions, exact expected/actual lane count, exact expected/actual byte count, every Float32 word, every independent RGBA8 byte',
    coordinates: 'all stored rows and first mismatches use top-down storage order and top-down x/y',
    input_textures: 'stored in full as raw little-endian uint32 lane arrays; every input lane is a small '
      + 'dyadic rational and therefore exact in binary32 and binary64',
    alpha: 'the program copies the sampled alpha through; every input alpha is exactly 1, so every '
      + 'output alpha float word is exactly 0x3f800000 and every RGBA8 alpha byte is exactly 255',
  },
  provenance: {
    node_version: process.version,
    generator: {
      relative_path_from_noisemaker_for_cpp: path.relative(cppRoot, generatorPath),
      sha256: sha256(fs.readFileSync(generatorPath)),
    },
    native_include_generator: {
      relative_path_from_noisemaker_for_cpp: path.relative(cppRoot, includeGeneratorPath),
      sha256: sha256(fs.readFileSync(includeGeneratorPath)),
    },
    cpu_snapshot: {
      // Deliberately a placeholder, not the literal `--cpu-root` argument: this
      // document is byte-compared by `--check`, so recording an ephemeral
      // absolute path would bind the gate to one temp directory on one machine.
      argument: cpuRootPlaceholder,
      immutable_snapshot: true,
      live_checkout_rejected: liveCheckoutPlaceholder,
      live_checkout_resolution: liveCpuCheckoutResolution,
      imports_confined_beneath_snapshot: true,
      import_closure_file_count: importClosureRecords.length,
      import_closure: importClosureRecords,
      pinned_files: Object.fromEntries(Object.entries(pinnedCpuFiles)
        .map(([name, [relative, hash]]) => [name, { relative_path_from_noisemaker_for_cpu: relative, sha256: hash }])),
    },
    source: {
      relative_path_from_noisemaker_for_cpp: sourceRelative,
      bytes: sourceBytes.length,
      sha256: sha256(sourceBytes),
      preprocessor_defines: ['KERNEL', 'SHAPE'],
    },
    canonical_factory: {
      name: canonicalFactory.name,
      bytes: Buffer.byteLength(canonicalText),
      sha256: sha256(canonicalText),
      source_slice_bytes: Buffer.byteLength(canonicalSlice),
      source_slice_sha256: sha256(canonicalSlice),
    },
    public_factory_is_canonical_identity: true,
    adapter_override_absent: true,
    adapter_routed_keys: [...canonicalAdapterKeys],
    corpus_adapter_keys: [...corpusAdapterKeys],
    // The path only, never a digest of it: `--check` byte-compares this
    // document, so pinning an unrelated file's hash here would turn any edit to
    // check_corpus.py into a spurious oracle failure. The live parse above is
    // what enforces the census.
    corpus_adapter_source: {
      relative_path_from_noisemaker_for_cpp: corpusAdapterSourceRelative,
      parsed_from_live_source: true,
    },
    metadata: {
      id: effect.id,
      func: effect.func,
      kind: effect.kind,
      pass: effect.passes[0],
      define_params: { shape: effect.params.shape, kernel: effect.params.kernel },
      textures: effect.textures,
      external_texture: effect.externalTexture,
    },
  },
  comparer_self_tests: comparerSelfTests(),
  coverage_axes: coverageAxes,
  render_cases: renderCases,
  tile_translation: tileTranslation,
  control_group: controlGroup,
  kernel_liveness_census: kernelLivenessCensus,
  binding_inertness_census: bindingInertnessCensus,
  binding_liveness_census: bindingLivenessCensus,
  time_speed_phase_census: timeSpeedPhaseCensus,
  speed_class_census: speedClassCensus,
  mutation_ledger: mutationLedger,
  nonreaching_control_mutant: nonreachingControl,
  write_only_tables_axis: writeOnlyTablesAxis,
  prng_near_ulp_invariance: prngNearUlpInvariance,
  mutation_discrimination_contract: {
    per_case: true,
    rule: 'discrimination is frozen and validated PER CASE AND PER MUTANT. A per-mutant summary is not '
      + 'sufficient and is never accepted here. A case that flips is a stop condition.',
    witness_overlap_disclosure: 'Unlike shape184 and normalmap185, whose two ledger mutants were '
      + 'competing materializations of one mechanism, these four mutants pin four DIFFERENT functions '
      + 'on the reachable path (smin, the prng chain, the aspect ratio, the wrap arms). Their witness '
      + 'sets overlap BY CONSTRUCTION -- every case with displacement, aspect != 1, and cellSmooth > 0 '
      + 'discriminates several at once -- and no case set covering this program\'s real behaviour could '
      + 'separate them (a case with zero displacement cannot witness smin or the wrap arms either). '
      + 'Overlap is therefore disclosed, not engineered away: the per-case table, not disjointness, is '
      + 'what attributes a divergence here.',
    witness_sets: Object.fromEntries(mutationLedger.map((mutant) => [mutant.name, {
      witness_cases: [...mutant.witness_cases],
      control_cases: [...mutant.control_cases],
    }])),
    expected: Object.fromEntries(mutantSpecs.map((spec) => [spec.name, spec.expected])),
    excluded_from_ledger: {
      'kernel4-arm-emboss-to-sharpen': 'the non-reaching control: invariant everywhere BY DESIGN; see nonreaching_control_mutant',
      'kernel-table-emboss0-perturbed': 'cannot diverge: the five tables are write-only at KERNEL = 0; see write_only_tables_axis',
      'prng-divisor-ulp-perturbed': 'measured invariant: nearest sampling absorbs a 2^-32 relative perturbation; see prng_near_ulp_invariance',
    },
  },
  claim_boundaries: {
    write_only_tables: writeOnlyTablesAxis.claim,
    nonreaching_control: nonreachingControl.claim,
    tile_translation: 'The Shapes crop contract does NOT carry over to this program: the tile output is '
      + 'not a crop of the full output (measured, with the d-field/localUV probes attributing the '
      + 'difference to localUV\'s -tileOffset term). No native test may assert a crop identity here.',
    effect_width_inert: 'effectWidth is a required number ABI binding whose reads are stripped at '
      + 'KERNEL = 0; it is recorded inert, not deleted.',
    resolution_unread: 'resolution is declared and never read; it stays a required Vec2 ABI binding '
      + 'per the Shapes precedent.',
    fragcolor_persistence: 'fragColor is a factory-scope Float32Array shared across pixels, but main() '
      + 'writes all four of its lanes unconditionally on every path, so cross-pixel persistence is '
      + 'unobservable for this program. loadKernels likewise re-writes all 45 table elements before '
      + 'any possible read, so factory-scope persistence of the tables is unobservable too.',
    synthetic_kernel_probes: 'The KERNEL != 0 liveness probes bind values the shipped parameter set '
      + 'never binds (the kernel param defaults to 0). They cover the ABI and prove the channel real; '
      + 'they are never parity cases and never evidence about production behaviour.',
    normalized_source: 'Normalized/typed source, function, interface, and whole-program hashes are the '
      + 'frontend profiles\' authority and are deliberately not restated here.',
  },
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function reportFor(data) {
  const caseRows = data.render_cases.map((item) =>
    `| ${item.name} | ${item.width}x${item.height} | ${item.route} | ${item.input_texture.width}x${item.input_texture.height} | ${item.output_expected.f32_sha256} | ${item.output_expected.rgba8_sha256} |`).join('\n')
  const coverageRows = Object.entries(data.coverage_axes)
    .map(([axis, buckets]) => Object.entries(buckets)
      .map(([bucket, names]) => `| ${axis} | ${bucket} | ${names.join(', ')} |`).join('\n')).join('\n')
  const controlRows = data.control_group.controls.map((item) =>
    `| ${item.name} | ${item.axis} | ${item.expectation} | ${item.observed} | ${item.pass ? 'pass' : 'FAIL'} | ${item.changed_lane_count} |`).join('\n')
  const mutantRows = data.mutation_ledger.map((mutant) => mutant.results.map((result) =>
    `| ${mutant.name} | ${result.case} | ${result.expected_discriminates ? 'witness' : 'control'} | ${result.differs ? 'differs' : 'identical'} | ${result.changed_lane_count} |`).join('\n')).join('\n')
  const nonreachingRows = data.nonreaching_control_mutant.rendered_mutant.rows.map((row) =>
    `| ${row.case} | ${row.differs ? 'differs' : 'identical'} | ${row.changed_lane_count} |`).join('\n')
  const tableRows = data.write_only_tables_axis.rendered_mutant.rows.map((row) =>
    `| ${row.case} | ${row.differs ? 'differs' : 'identical'} | ${row.changed_lane_count} |`).join('\n')
  const nearUlpRows = data.prng_near_ulp_invariance.rendered_mutant.rows.map((row) =>
    `| ${row.case} | ${row.differs ? 'differs' : 'identical'} | ${row.changed_lane_count} |`).join('\n')
  const kernelRows = data.kernel_liveness_census.probes.map((probe) =>
    `| ${probe.kernel} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')
  const inertRows = data.binding_inertness_census.inert.map((entry) => entry.probes.map((probe) =>
    `| ${entry.binding} | ${JSON.stringify(probe.value)} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')).join('\n')
  const liveRows = data.binding_liveness_census.probes.map((probe) =>
    `| ${probe.binding} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')
  const phaseCaseRows = data.time_speed_phase_census.per_case_phase.map((row) =>
    `| ${row.case} | ${row.time} | ${row.floor_speed} | ${row.phase} | ${row.phase_is_integral ? 'integral' : 'non-integral'} |`).join('\n')
  const phaseProbeRows = data.time_speed_phase_census.probes.map((probe) =>
    `| ${probe.case} | ${JSON.stringify(probe.overrides)} | ${probe.observed} | ${probe.changed_lane_count} |`).join('\n')
  const speedRows = data.speed_class_census.probes.map((probe) => `| ${probe.speed} | ${probe.f32_sha256} |`).join('\n')
  return `# Cellrefract186 exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; exact defines
\`KERNEL=${data.defines.KERNEL}\`, \`SHAPE=${data.defines.SHAPE}\`.

## The contract this program exists to prove

\`classicNoisedeck/cellRefract\` declares five **mutable uninitialized** file-scope \`float[9]\` tables
and a writer function, and the parity target is the transpiler's materialization, not GLSL semantics:

| Table | JavaScript | Writer | Readers | Oracle-discriminable |
| --- | --- | --- | --- | --- |
${tableNames.map((name) => `| \`${name}\` | plain \`Array\` of doubles | \`loadKernels\`, 9 literal stores | ${data.mutable_global_contracts[name].reads} | **no** |`).join('\n')}

The tables are **write-only at the frozen defines**: their only readers live inside
\`convolutionKernel\`'s \`KERNEL != 0\` branches, which \`main\` never enters at \`KERNEL = 0\`. No
table-content mutant can move a pixel, and this package never pretends otherwise:
\`write_only_tables_axis\` renders a table mutant on every case and records
${data.write_only_tables_axis.rendered_divergences} changed lanes. The double element contract and the
exact 45 (table, index, value) triples are proven structurally -- by the emitted native type, by the
JavaScript being plain Arrays, and by the frontend profile's frozen store census. A green pixel run is
not evidence for them.

## Authority

This oracle is produced by the ${data.oracle_authority}. The generator refuses to run unless
\`kernelFactories.get(key) === canonicalKernelFactories[key]\`, the factory is named
\`${factoryName}\`, its \`Function.prototype.toString\` SHA-256 is \`${factoryTextSha256}\`, neither
adapter table owns the key, \`canonicalAdapterFactories\` matches its
${data.provenance.adapter_routed_keys.length}-key census exactly, the key is absent from the
${data.provenance.corpus_adapter_keys.length}-key \`check_corpus._ADAPTERS\` eligibility table
**parsed out of the live \`${data.provenance.corpus_adapter_source.relative_path_from_noisemaker_for_cpp}\`**
rather than transcribed, all six pinned CPU files match, and every module in the
${data.provenance.cpu_snapshot.import_closure_file_count}-file import closure resolves by real path
beneath the immutable snapshot. Bare module specifiers other than \`node:\` builtins are rejected, and
the live checkout is refused as a \`--cpu-root\`.

No absolute path is recorded anywhere in this package. The \`--cpu-root\` argument is stored as
\`${data.provenance.cpu_snapshot.argument}\` and the rejected live checkout as
\`${data.provenance.cpu_snapshot.live_checkout_rejected}\`, resolved at run time from
${data.provenance.cpu_snapshot.live_checkout_resolution}. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings

The program has exactly ${data.runtime_binding_names.length} runtime bindings:
${data.runtime_binding_names.map((name) => `\`${name}\``).join(', ')}. \`KERNEL\` and \`SHAPE\` are
compile-time defines in the corpus that the JavaScript materializes as runtime bindings at the frozen
values; they are never counted as bindings. \`resolution\` is never read and \`effectWidth\`'s reads
are stripped at \`KERNEL = 0\`; both remain required ABI bindings and are recorded inert, not deleted.

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
${caseRows}

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
${data.runtime_binding_names.length} bindings with every float and vector lane as a hexadecimal f32
word, the external \`runPass\` time/seed pair, the complete expected Float32 word array, the complete
independently captured RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each array.
Every input lane is a small dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
${coverageRows}

## Tile translation: the Shapes crop contract does NOT carry over

Design section 7 assumed \`tile-crop-translation\` would satisfy the Shapes-amended crop identity.
**Measured: it does not.** With \`tileOffset = (${data.tile_translation.rect.crop_x},
${data.tile_translation.full_height} - ${data.tile_translation.rect.crop_y} - ${data.tile_translation.rect.tile_height})\`
and the same ${data.tile_translation.rect.full_width}x${data.tile_translation.rect.full_height} input texture on both routes,
${data.tile_translation.word_mismatches} of ${data.tile_translation.rect.tile_width * data.tile_translation.rect.tile_height * 4} Float32 words and
${data.tile_translation.byte_mismatches} RGBA8 bytes differ between the tile output and the top-down crop of the full output
(first mismatch at top-down ${JSON.stringify(data.tile_translation.first_mismatch.top_down_xy)} channel
${data.tile_translation.first_mismatch.channel}: tile ${data.tile_translation.first_mismatch.tile_word} versus full
${data.tile_translation.first_mismatch.full_word}).

${data.tile_translation.why}

Both halves are measured with instrumented probe factories (one anchor, one replacement; never parity
arrays). Publishing the cells field \`d\` on both routes gives
**${data.tile_translation.d_field_alignment_witness.exact_word_mismatches} mismatches** -- the cell field
IS world-aligned through tileOffset. Publishing \`localUV\` gives
**${data.tile_translation.local_uv_translation_witness.equal_lane_count} equal lanes of
${data.tile_translation.local_uv_translation_witness.compared_lane_count}** -- the sample coordinate is a
constant translation away, exactly as the algebra predicts. The raw-crop-y trap still bites:
binding raw top-down \`crop_y\` changes ${data.tile_translation.raw_crop_y_trap.changed_lane_count} lanes.
${data.tile_translation.consequence}

## One-axis control group on \`${data.control_group.anchor}\`: the kernel-zero-invariance axis

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${controlRows}

The \`kernel-binding-unbound\` row is the axis the design asked for: the JS \`KERNEL\` binding is bound
at 0 on every case, and an *absent* KERNEL renders bit-identically (undefined != 0 is false). The port
has no KERNEL binding at all, so this control asserts the absence of a divergence channel.

### KERNEL liveness census

| KERNEL probe | Versus baseline | Changed lanes |
| --- | --- | ---: |
${kernelRows}

${data.kernel_liveness_census.rule}

## Binding inertness and liveness censuses

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
${inertRows}

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
${liveRows}

${data.binding_inertness_census.rule}

## The time * floor(speed) phase rule

| Case | time | floor(speed) | phase | |
| --- | ---: | ---: | ---: | --- |
${phaseCaseRows}

| Probe | Override | Observed | Changed lanes |
| --- | --- | --- | ---: |
${phaseProbeRows}

${data.time_speed_phase_census.rule}

At the anchor's integral phase the whole speed parameter collapses to
${data.speed_class_census.distinct_digest_count} equivalence classes:
${data.speed_class_census.equivalence_classes.map((cls) => `speed ${cls.join('/')}`).join(' and ')}.

| speed | Float32 SHA-256 |
| ---: | --- |
${speedRows}

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
${mutantRows}

All four ledger mutants are one-anchor/one-replacement rewrites of the canonical factory text (the
wrap swap is an ordered three-anchor chain through a unique temp identifier), compiled and rendered by
this generator, and each was **verified bit-differing before it was budgeted**. The expected outcome
is frozen **per case and per mutant**; \`--check\` fails if any single cell flips, in either direction.

${data.mutation_discrimination_contract.witness_overlap_disclosure}

### The non-reaching control: a KERNEL != 0 branch mutant

| Case | Result | Changed lanes |
| --- | --- | ---: |
${nonreachingRows}

${data.nonreaching_control_mutant.claim}

### The write-only tables, measured

| Case | Result | Changed lanes |
| --- | --- | ---: |
${tableRows}

**${data.write_only_tables_axis.claim}**

### The prng near-ULP control

| Case | Result | Changed lanes |
| --- | --- | ---: |
${nearUlpRows}

${data.prng_near_ulp_invariance.reason}

## Claim boundaries

- ${data.claim_boundaries.write_only_tables}
- ${data.claim_boundaries.nonreaching_control}
- ${data.claim_boundaries.tile_translation}
- ${data.claim_boundaries.effect_width_inert}
- ${data.claim_boundaries.resolution_unread}
- ${data.claim_boundaries.fragcolor_persistence}
- ${data.claim_boundaries.synthetic_kernel_probes}
- ${data.claim_boundaries.normalized_source}

## Regeneration

\`\`\`sh
node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/cellrefract-parity/cellrefract186_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_cellrefract_native_oracle_include.py --self-test
\`\`\`

Both generators are fail-closed and check mode performs no writes.
`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)

// No absolute path may appear anywhere in the emitted document. The previous
// packages recorded their run-root and could then only be checked from the one
// temp directory that produced them; this scan is the inherited fix.
// The report is sidecar-verified and byte-compared by `--check` exactly like the
// JSON, so a path leaked into the report ALONE would reproduce the same
// machine-bound gate with neither scanner naming it. Both documents are scanned.
for (const [label, text] of [['JSON', jsonText], ['report', reportText]]) {
  const leaked = /(?:^|["\s])(?:\/Users\/|\/home\/|\/private\/|\/var\/|\/tmp\/|\/opt\/)/.exec(text)
  if (leaked !== null) throw new Error(`the oracle ${label} records an absolute path: ${leaked[0]}`)
  if (text.includes(cpuRoot) || (liveCpuReal !== null && text.includes(liveCpuReal))) {
    throw new Error(`the oracle ${label} records a snapshot or checkout path verbatim`)
  }
}

verifySidecar(generatorPath)
verifySidecar(includeGeneratorPath)
if (write) {
  fs.writeFileSync(outputPath, jsonText)
  fs.writeFileSync(reportPath, reportText)
  fs.writeFileSync(sidecarPath(outputPath), sidecarText(outputPath, Buffer.from(jsonText)))
  fs.writeFileSync(sidecarPath(reportPath), sidecarText(reportPath, Buffer.from(reportText)))
} else {
  verifySidecar(outputPath)
  verifySidecar(reportPath)
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Cellrefract186 oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Cellrefract186 oracle report drift')
}
const controlSummary = controlGroup.controls.map((item) => `${item.name}=${item.observed}`).join(' ')
const ledgerSummary = mutationLedger.map((mutant) => `${mutant.name}:${mutant.witness_cases.length}/${cases.length}`).join(' ')
console.log(`Cellrefract186 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} cases, `
  + `${mutationLedger.length} ledger mutants [${ledgerSummary}], controls [${controlSummary}], `
  + `tile translation measured non-crop (${cropWordMismatches} word mismatches, d-field aligned `
  + `${dFieldMismatches}), tables write-only (${writeOnlyTablesAxis.rendered_divergences} lanes), `
  + `non-reaching control invariant (${nonreachingControl.rendered_divergences} lanes)`)
