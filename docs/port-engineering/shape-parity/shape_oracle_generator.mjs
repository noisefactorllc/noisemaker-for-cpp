#!/usr/bin/env node
// Shape184 canonical JavaScript oracle generator (`synth/shape:shape`).
//
// Authority: the unmodified public canonical factory `canonicalFactory274` from
// an immutable snapshot of `noisemaker-for-cpu`, executed through the pinned
// `bindCanonicalKernel` / `GlslCpuRuntime` / `runPass` path. No C++ output
// participates in any expected array. A locally reimplemented formula is not an
// oracle and is never used here.
//
// This program exists to prove two mutable file-scope globals with DIFFERENT
// numeric contracts:
//   * `aspectRatio` is a plain JS Number -- a double, never narrowed to f32.
//   * `globalCoord` is a Float32Array -- every lane store narrows to f32.
// Both are oracle-discriminable and both carry an independently generated
// mutant here; the discrimination ledger is recorded and validated PER CASE,
// because two cases with the same aspect ratio can differ in whether they
// discriminate.
//
//   node docs/port-engineering/shape-parity/shape_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/shape-parity/shape_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'shape-oracles.json')
const reportPath = path.join(here, 'shape-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_shape_native_oracle_include.py')

const schema = 'noisemaker-for-cpp.shape184.pixel-parity.v1'
const schemaVersion = 1
const programKey = 'synth/shape:shape'
const effectKey = 'synth/shape'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const defines = { LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 }
const factoryName = 'canonicalFactory274'
const factoryTextSha256 = '870d97a811e5720f827f5616057483a43b27224240ac95c04a8084dd257a6125'
const nextFactoryName = 'canonicalFactory275'

// The live checkout is DERIVED, never hardcoded: a machine-specific absolute
// path in a checked-in gate is unrunnable on any other machine and leaks a home
// directory into the repository. `NOISEMAKER_FOR_CPU` overrides; otherwise the
// conventional sibling layout under $HOME is used.
const liveCpuCheckoutResolution =
  'process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu'
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU
  ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)

// Neither the `--cpu-root` argument nor the live-checkout path is recorded
// verbatim. The 22-file import closure and the six pinned file hashes
// authenticate the snapshot completely; the literal path authenticates nothing
// and would bind `--check` to one ephemeral directory on one machine.
const cpuRootPlaceholder = '<immutable-cpu-snapshot-root>'
const liveCheckoutPlaceholder = '<live-noisemaker-for-cpu-checkout>'
const sourceRelative = `tools/glslcpp/corpus/${corpusRevision}/sources/synth/shape/shape.glsl`
const sourceBytesExpected = 15986
const sourceSha256Expected = 'd917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f'

// Exactly ten runtime bindings. LOOP_A_OFFSET/LOOP_B_OFFSET are compile-time
// defines recorded separately and are never counted here. `resolution` is a
// required ABI binding that the program never reads; it is not "cleaned up".
const bindingNames = Object.freeze([
  'time', 'seed', 'wrap', 'resolution', 'tileOffset', 'fullResolution',
  'loopAScale', 'loopBScale', 'speedA', 'speedB',
])
const bindingAbi = Object.freeze({
  time: 'number', seed: 'int32', wrap: 'bool', resolution: 'Vec2',
  tileOffset: 'Vec2', fullResolution: 'Vec2', loopAScale: 'number',
  loopBScale: 'number', speedA: 'number', speedB: 'number',
})

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
// another frozen copy proves nothing, and would stay green if `synth/shape` were
// ever added to the real table.
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
function f32Vector(values) {
  if (!Array.isArray(values) || values.some((item) => typeof item !== 'number' || !Number.isFinite(item))) {
    throw new Error(`vector lanes must be finite numbers: ${JSON.stringify(values)}`)
  }
  return new Float32Array(values.map(f))
}
function exactF32(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${label}: finite number required`)
  return f(value)
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
if (typeof canonicalFactory !== 'function') throw new Error('canonical Shape factory missing')
if (publicFactory !== canonicalFactory) throw new Error('public Shape factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('unexpected Shape adapter override')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Shape adapter override value')
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
if (corpusAdapterKeys.includes(programKey)) throw new Error('synth/shape:shape must not be corpus-adapter-routed')
if (canonicalAdapterKeys.includes(programKey)) throw new Error('synth/shape:shape must not be adapter-routed')
{
  const observed = Object.keys(canonicalAdapterFactories).sort()
  const expected = [...canonicalAdapterKeys].sort()
  if (observed.length !== expected.length || observed.some((key, index) => key !== expected[index])) {
    throw new Error(`adapter table census drift: ${observed.join(', ')}`)
  }
}
if (canonicalFactory.name !== factoryName) throw new Error(`canonical Shape factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) throw new Error(`canonical Shape factory text drift: ${sha256(canonicalText)}`)

const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf(`function ${nextFactoryName}`, sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('canonical Shape factory source slice missing')
const canonicalSlice = canonicalKernelsSource.slice(sliceStart, sliceEnd)

// The shipped binding set contains an unrelated `aspectRatio` uniform. The
// factory declares its own file-scope `var aspectRatio`, which shadows it, so
// the binding is never read. Locking this keeps a future binding rename from
// silently becoming an input.
if (canonicalText.includes('$bindings["aspectRatio"]')) {
  throw new Error('the file-scope aspectRatio no longer shadows the aspectRatio binding')
}
if (canonicalText.includes('$bindings["globalCoord"]')) {
  throw new Error('globalCoord unexpectedly reads a binding')
}
for (const declaration of ['var aspectRatio = 0;', 'var globalCoord = new Float32Array([0, 0]);']) {
  if (canonicalText.split(declaration).length - 1 !== 1) {
    throw new Error(`mutable global declaration census drift: ${declaration}`)
  }
}

const sourcePath = path.join(cppRoot, sourceRelative)
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error('pinned Shape GLSL source drift')
}

const effect = effectRecords.find((item) => item.id === effectKey)
if (!effect || effect.func !== 'shape' || effect.kind !== 'generator') throw new Error('Shape metadata drift')
if (effect.passes?.length !== 1 || effect.passes[0]?.program !== 'shape') throw new Error('Shape pass interface drift')
if (Object.keys(effect.textures ?? {}).length !== 0 || effect.externalTexture !== null) throw new Error('Shape must have no textures')
if (effect.params?.loopAOffset?.default !== defines.LOOP_A_OFFSET
    || effect.params?.loopAOffset?.define !== 'LOOP_A_OFFSET'
    || effect.params?.loopBOffset?.default !== defines.LOOP_B_OFFSET
    || effect.params?.loopBOffset?.define !== 'LOOP_B_OFFSET') {
  throw new Error('Shape default define drift')
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
      throw new Error(`Shape comparer did not preflight ${reason}`)
    }
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  expectReject(compareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape'), 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32'
      || !bytesOf(plusZero.toRgba8()).equals(bytesOf(minusZero.toRgba8()))) {
    throw new Error('Shape comparer missed signed zero')
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
    throw new Error('Shape comparer missed NaN payload')
  }
  const finalLane = compareExact(new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)])),
    expectedRecord(plusZero), 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch.channel !== 'a'
      || finalLane.first_mismatch.lane_or_byte_index !== 3) {
    throw new Error('Shape comparer missed final alpha lane')
  }
  const byteExpected = expectedRecord(plusZero)
  byteExpected.rgba8[3] ^= 1
  const byteOnly = compareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch.channel !== 'a') {
    throw new Error('Shape comparer missed independent byte mismatch')
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
// Case definitions
// ---------------------------------------------------------------------------

// The tiled case on `shape-wrap-live-37-61` is a genuine top-down crop of a
// larger full render. Its tileOffset.y is `full_height - crop_y - tile_height`,
// never raw crop_y.
const cropRect = { crop_x: 4, crop_y: 2, tile_width: 4, tile_height: 6, full_width: 11, full_height: 9 }

// The production-shaped tile case exercises the same rule at a resolution whose
// full route is far too large to store; the translation PROOF lives on
// `shape-wrap-live-37-61`, which stores its full route.
const productionCrop = { crop_x: 100, crop_y: 60, tile_width: 40, tile_height: 24, full_width: 1280, full_height: 720 }

const cases = [
  {
    name: 'shape-landscape-16x9',
    coverage: ['control-group anchor', 'landscape 16x9', 'untiled full route',
      'aspect 16/9 is not exactly f32-representable', 'wrap false with integral lf (wrap-invariant witness)',
      'both speeds positive', 'discriminates shape-aspect-f32-narrowed'],
    width: 16, height: 9, time: 0.5, seed: 3, wrap: false,
    loopAScale: 1, loopBScale: 1, speedA: 50, speedB: 50,
  },
  {
    name: 'shape-crop-1280x720',
    coverage: ['tile route at a production-shaped resolution', 'aspect 1280/720 = 16/9',
      'wrap true with integral lf', 'speedA at the +100 extremum', 'negative bound seed',
      'discriminates shape-aspect-f32-narrowed'],
    width: productionCrop.tile_width, height: productionCrop.tile_height,
    time: 0.125, seed: -7, wrap: true,
    loopAScale: 1, loopBScale: 1, speedA: 100, speedB: 25,
    tileOffset: [productionCrop.crop_x, productionCrop.full_height - productionCrop.crop_y - productionCrop.tile_height],
    fullResolution: [productionCrop.full_width, productionCrop.full_height],
    crop: productionCrop,
  },
  {
    name: 'shape-square-12',
    coverage: ['square 12x12', 'aspect exactly 1.0', 'untiled full route',
      'non-integral lf with wrap false', 'speedA -100 / speedB +100 extrema', 'INT32_MAX seed',
      'non-reaching control for shape-aspect-f32-narrowed'],
    width: 12, height: 12, time: 1.5, seed: 2147483647, wrap: false,
    loopAScale: 50, loopBScale: 20, speedA: -100, speedB: 100,
  },
  {
    name: 'shape-portrait-9x16',
    coverage: ['portrait 9x16', 'aspect exactly 0.5625', 'untiled full route',
      'wrap true', 'positive speedA / negative speedB', 'INT32_MIN seed', 'negative bound time',
      'non-reaching control for shape-aspect-f32-narrowed with a different shape than square'],
    width: 9, height: 16, time: -3.75, seed: -2147483648, wrap: true,
    loopAScale: 1, loopBScale: 1, speedA: 25, speedB: -75,
  },
  {
    name: 'shape-zero-speeds',
    coverage: ['landscape 16x9 with both speeds zero', 'offset() is never called',
      'aspectRatio is written and never read', 'zero seed',
      'non-reaching control for shape-aspect-f32-narrowed'],
    width: 16, height: 9, time: 2.25, seed: 0, wrap: false,
    loopAScale: 1, loopBScale: 1, speedA: 0, speedB: 0,
  },
  {
    name: 'shape-wrap-live-37-61',
    coverage: ['the only case where the wrap axis is live (non-integral lf)',
      'tiled route', 'top-down crop translation witness', 'raw crop_y trap witness',
      'positive speedA / negative speedB', 'aspect 11/9 is not exactly f32-representable',
      'discriminates shape-aspect-f32-narrowed'],
    width: cropRect.tile_width, height: cropRect.tile_height,
    time: 0.25, seed: 5, wrap: true,
    loopAScale: 37, loopBScale: 61, speedA: 50, speedB: -25,
    tileOffset: [cropRect.crop_x, cropRect.full_height - cropRect.crop_y - cropRect.tile_height],
    fullResolution: [cropRect.full_width, cropRect.full_height],
    crop: cropRect,
  },
  {
    name: 'shape-negative-speeds',
    coverage: ['landscape 16x9', 'untiled full route', 'both speeds negative (the speedA<0 / speedB<0 arms)',
      'wrap false', 'discriminates shape-aspect-f32-narrowed'],
    width: 16, height: 9, time: 0.75, seed: 123, wrap: false,
    loopAScale: 1, loopBScale: 1, speedA: -50, speedB: -25,
  },
  {
    name: 'shape-extreme-tile-offset',
    coverage: ['synthetic extreme tileOffset [131072.1, 0.3]',
      'the only case that discriminates shape-globalcoord-unnarrowed',
      'aspect 16/12 = 4/3 but the sampled pixels do not discriminate shape-aspect-f32-narrowed',
      'globalCoord leaves the exactly-representable range'],
    width: 16, height: 12, time: 0.5, seed: 3, wrap: false,
    loopAScale: 1, loopBScale: 1, speedA: 50, speedB: 50,
    tileOffset: [131072.1, 0.3], fullResolution: [16, 12],
  },
]
if (cases.length !== 8) throw new Error(`Shape fixture census drift: ${cases.length}`)
if (new Set(cases.map((item) => item.name)).size !== cases.length) throw new Error('duplicate Shape case name')
for (const definition of cases) {
  for (const field of ['width', 'height', 'time', 'seed', 'loopAScale', 'loopBScale', 'speedA', 'speedB']) {
    const value = definition[field]
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      throw new Error(`${definition.name}: ${field} must be a finite number`)
    }
  }
  if (typeof definition.wrap !== 'boolean') throw new Error(`${definition.name}: wrap must be a boolean`)
  if (!Number.isInteger(definition.seed)) throw new Error(`${definition.name}: seed must be an int32`)
}

// ---------------------------------------------------------------------------
// Rendering through the pinned public path
// ---------------------------------------------------------------------------

function uniformsFor(definition) {
  return {
    LOOP_A_OFFSET: defines.LOOP_A_OFFSET,
    LOOP_B_OFFSET: defines.LOOP_B_OFFSET,
    time: exactF32(definition.time, `${definition.name}.time`),
    seed: definition.seed,
    wrap: definition.wrap,
    loopAScale: exactF32(definition.loopAScale, `${definition.name}.loopAScale`),
    loopBScale: exactF32(definition.loopBScale, `${definition.name}.loopBScale`),
    speedA: exactF32(definition.speedA, `${definition.name}.speedA`),
    speedB: exactF32(definition.speedB, `${definition.name}.speedB`),
  }
}

function bindingOptions(definition) {
  return {
    width: definition.width,
    height: definition.height,
    time: exactF32(definition.time, `${definition.name}.time`),
    seed: definition.seed,
    uniforms: uniformsFor(definition),
    tileOffset: f32Vector(definition.tileOffset ?? [0, 0]),
    fullResolution: f32Vector(definition.fullResolution ?? [definition.width, definition.height]),
  }
}

// `bindCanonicalKernel` is the pinned public entry point; it composes
// `createCanonicalBindings` and `bindGlslKernel` from the frozen snapshot.
function render(factory, definition) {
  const options = bindingOptions(definition)
  const callerVectors = { tileOffset: options.tileOffset, fullResolution: options.fullResolution }
  const before = Object.fromEntries(Object.entries(callerVectors).map(([name, value]) => [name, words(value).slice()]))
  const bindings = createCanonicalBindings(options)
  const output = new Surface(definition.width, definition.height)
  runPass({
    kernel: bindCanonicalKernel(factory, options),
    destination: output,
    time: definition.externalTime ?? 0,
    seed: definition.externalSeed ?? 1,
  })
  for (const [name, value] of Object.entries(callerVectors)) {
    const after = words(value)
    if (before[name].some((word, index) => word !== after[index])) throw new Error(`${definition.name}: caller vector ${name} mutated`)
  }
  return { output, bindings, options, callerVectors }
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

function bindingRecords(definition, resolvedBindings) {
  const uniforms = uniformsFor(definition)
  const source = {
    ...uniforms,
    resolution: resolvedBindings.resolution,
    tileOffset: resolvedBindings.tileOffset,
    fullResolution: resolvedBindings.fullResolution,
    time: resolvedBindings.time,
  }
  const out = {}
  for (const name of bindingNames) {
    const abi = bindingAbi[name]
    const value = source[name]
    if (abi === 'int32') {
      if (!Number.isInteger(value) || value < -2147483648 || value > 2147483647) throw new Error(`${name}: not an int32`)
      out[name] = { abi, value }
    } else if (abi === 'bool') {
      if (typeof value !== 'boolean') throw new Error(`${name}: not a bool`)
      out[name] = { abi, value }
    } else if (abi === 'number') {
      if (typeof value !== 'number' || f(value) !== value) throw new Error(`${name}: not an exact f32 scalar`)
      out[name] = { abi, f32_value: value, f32_word_le: f32Bits(value) }
    } else {
      if (!(value instanceof Float32Array) || value.length !== 2) throw new Error(`${name}: not a ${abi}`)
      out[name] = { abi, f32_values: Array.from(value), f32_words_le: Array.from(words(value), u32Hex) }
    }
  }
  if (Object.keys(out).length !== 10) throw new Error('binding census drift')
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

const canonicalOutputs = new Map()
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
  canonicalOutputs.set(definition.name, canonical.output)
  canonicalExpected.set(definition.name, expected)
  return {
    name: definition.name,
    coverage: definition.coverage,
    route: definition.tileOffset ? 'tile' : 'full',
    width: definition.width,
    height: definition.height,
    bindings: bindingRecords(definition, canonical.bindings),
    external_pass: externalRecord(definition),
    output_expected: surfaceRecord(canonical.output),
    canonical_repeat: repeatIdentity,
    public_canonical: publicIdentity,
  }
})

// ---------------------------------------------------------------------------
// Top-down crop identity, carried by `shape-wrap-live-37-61`
// ---------------------------------------------------------------------------

const cropCaseName = 'shape-wrap-live-37-61'
const tiledDefinition = cases.find((item) => item.name === cropCaseName)
const fullRouteDefinition = {
  ...tiledDefinition,
  name: `${cropCaseName}/full-route`,
  width: cropRect.full_width,
  height: cropRect.full_height,
  tileOffset: [0, 0],
  fullResolution: [cropRect.full_width, cropRect.full_height],
}
const fullRoute = render(canonicalFactory, fullRouteDefinition)
const fullWords = words(fullRoute.output.data)
const fullBytes = fullRoute.output.toRgba8()
const tileWords = words(canonicalOutputs.get(cropCaseName).data)
const tileBytes = canonicalOutputs.get(cropCaseName).toRgba8()
let cropWordMismatches = 0
let cropByteMismatches = 0
for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
  for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
    for (let channel = 0; channel < 4; channel += 1) {
      const tileIndex = ((ty * cropRect.tile_width) + tx) * 4 + channel
      const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4 + channel
      if (tileWords[tileIndex] !== fullWords[fullIndex]) cropWordMismatches += 1
      if (tileBytes[tileIndex] !== fullBytes[fullIndex]) cropByteMismatches += 1
    }
  }
}
if (cropWordMismatches !== 0 || cropByteMismatches !== 0) {
  throw new Error(`top-down crop identity failed: ${cropWordMismatches} words, ${cropByteMismatches} bytes`)
}
const rawCropYDefinition = { ...tiledDefinition, name: `${cropCaseName}/raw-crop-y-trap`,
  tileOffset: [cropRect.crop_x, cropRect.crop_y] }
const rawCropYOutput = render(canonicalFactory, rawCropYDefinition).output
const rawCropYComparison = compareExact(rawCropYOutput, canonicalExpected.get(cropCaseName), 'crop/raw-crop-y-trap')
if (rawCropYComparison.exact) throw new Error('raw top-down crop_y trap is indistinguishable; the crop witness is vacuous')

// ---------------------------------------------------------------------------
// Production-scale crop identity.
//
// `st = globalCoord / fullResolution[1]` differs by two orders of magnitude
// between the 11x9 proof above and 1280x720, so a translation defect that only
// appears at large fullResolution would be invisible without this. The full
// 1280x720 route is rendered in memory and thrown away; only the 40x24 crop
// window it yields is stored, which is the same size as the tile array itself.
// ---------------------------------------------------------------------------

const productionCaseName = 'shape-crop-1280x720'
const productionDefinition = cases.find((item) => item.name === productionCaseName)
const productionFullRoute = render(canonicalFactory, {
  ...productionDefinition,
  name: `${productionCaseName}/full-route`,
  width: productionCrop.full_width,
  height: productionCrop.full_height,
  tileOffset: [0, 0],
  fullResolution: [productionCrop.full_width, productionCrop.full_height],
}).output
const productionFullWords = words(productionFullRoute.data)
const productionFullBytes = productionFullRoute.toRgba8()
const productionTileWords = words(canonicalOutputs.get(productionCaseName).data)
const productionTileBytes = canonicalOutputs.get(productionCaseName).toRgba8()
const productionWindowWords = []
const productionWindowBytes = []
let productionWordMismatches = 0
let productionByteMismatches = 0
for (let ty = 0; ty < productionCrop.tile_height; ty += 1) {
  for (let tx = 0; tx < productionCrop.tile_width; tx += 1) {
    for (let channel = 0; channel < 4; channel += 1) {
      const tileIndex = ((ty * productionCrop.tile_width) + tx) * 4 + channel
      const fullIndex = (((productionCrop.crop_y + ty) * productionCrop.full_width)
        + (productionCrop.crop_x + tx)) * 4 + channel
      productionWindowWords.push(u32Hex(productionFullWords[fullIndex]))
      productionWindowBytes.push(productionFullBytes[fullIndex])
      if (productionTileWords[tileIndex] !== productionFullWords[fullIndex]) productionWordMismatches += 1
      if (productionTileBytes[tileIndex] !== productionFullBytes[fullIndex]) productionByteMismatches += 1
    }
  }
}
if (productionWordMismatches !== 0 || productionByteMismatches !== 0) {
  throw new Error(`production-scale crop identity failed: ${productionWordMismatches} words, `
    + `${productionByteMismatches} bytes`)
}
const productionWindowCount = productionCrop.tile_width * productionCrop.tile_height * 4
if (productionWindowWords.length !== productionWindowCount || productionWindowBytes.length !== productionWindowCount) {
  throw new Error('production crop window lane census drift')
}
{
  const alphaWords = new Set()
  const alphaBytes = new Set()
  for (let index = 3; index < productionWindowCount; index += 4) {
    alphaWords.add(productionWindowWords[index])
    alphaBytes.add(productionWindowBytes[index])
  }
  if (alphaWords.size !== 1 || !alphaWords.has('0x3f800000') || alphaBytes.size !== 1 || !alphaBytes.has(255)) {
    throw new Error('production crop window alpha contract drift')
  }
}
const productionRawCropYOutput = render(canonicalFactory, {
  ...productionDefinition,
  name: `${productionCaseName}/raw-crop-y-trap`,
  tileOffset: [productionCrop.crop_x, productionCrop.crop_y],
}).output
const productionRawCropYComparison = compareExact(productionRawCropYOutput,
  canonicalExpected.get(productionCaseName), 'production-crop/raw-crop-y-trap')
if (productionRawCropYComparison.exact) {
  throw new Error('production-scale raw crop_y trap is indistinguishable; the witness is vacuous')
}
const productionCropIdentity = {
  case: productionCaseName,
  rect: productionCrop,
  tile_offset_rule: 'tileOffset = (crop_x, full_height - crop_y - tile_height)',
  tile_offset_f32_words_le: Array.from(words(f32Vector([productionCrop.crop_x,
    productionCrop.full_height - productionCrop.crop_y - productionCrop.tile_height])), u32Hex),
  full_route_stored: false,
  full_route_crop_window_stored: true,
  full_route_dimensions: [productionCrop.full_width, productionCrop.full_height],
  full_route_f32_sha256: sha256(bytesOf(productionFullRoute.data)),
  full_route_rgba8_sha256: sha256(bytesOf(productionFullBytes)),
  full_route_crop_window: {
    width: productionCrop.tile_width,
    height: productionCrop.tile_height,
    source_origin_xy: [productionCrop.crop_x, productionCrop.crop_y],
    source_full_width: productionCrop.full_width,
    f32_words_le: productionWindowWords,
    f32_sha256: sha256(Buffer.concat(productionWindowWords.map((word) => {
      const buffer = Buffer.alloc(4)
      buffer.writeUInt32LE(Number(word), 0)
      return buffer
    }))),
    rgba8_bytes: productionWindowBytes,
    rgba8_sha256: sha256(Buffer.from(productionWindowBytes)),
    alpha_f32_word: '0x3f800000',
    alpha_rgba8_byte: 255,
  },
  exact_word_mismatches: productionWordMismatches,
  exact_byte_mismatches: productionByteMismatches,
  exact: true,
  raw_crop_y_trap: {
    tile_offset_f32_words_le: Array.from(words(f32Vector([productionCrop.crop_x, productionCrop.crop_y])), u32Hex),
    differs_from_correct_tile: true,
    changed_lane_count: productionRawCropYComparison.changed_lane_count,
    first_mismatch: productionRawCropYComparison.first_float32_mismatch,
  },
  note: 'The full 1280x720 route is rendered in memory and discarded; storing all 3,686,400 '
    + 'Float32 lanes is not viable, but the proof needs only the 40x24 window, which is stored '
    + 'above and re-derived against the tile array by the materializer. st = globalCoord / '
    + 'fullResolution[1] is two orders of magnitude larger here than in the 11x9 proof, so a '
    + 'translation defect that only appears at large fullResolution is caught by this case.',
}

const cropIdentity = {
  case: cropCaseName,
  rect: cropRect,
  tile_offset_rule: 'tileOffset = (crop_x, full_height - crop_y - tile_height)',
  tile_offset_f32_words_le: Array.from(words(f32Vector([cropRect.crop_x, cropRect.full_height - cropRect.crop_y - cropRect.tile_height])), u32Hex),
  held_identical_bindings: bindingNames.filter((name) => name !== 'resolution' && name !== 'tileOffset'),
  full_route_expected: surfaceRecord(fullRoute.output),
  exact_word_mismatches: cropWordMismatches,
  exact_byte_mismatches: cropByteMismatches,
  exact: true,
  raw_crop_y_trap: {
    tile_offset_f32_words_le: Array.from(words(f32Vector([cropRect.crop_x, cropRect.crop_y])), u32Hex),
    differs_from_correct_tile: true,
    changed_lane_count: rawCropYComparison.changed_lane_count,
    first_mismatch: rawCropYComparison.first_float32_mismatch,
  },
  production_shaped_case: productionCropIdentity,
}

// ---------------------------------------------------------------------------
// One-axis control group on shape-landscape-16x9
// ---------------------------------------------------------------------------

const anchorName = 'shape-landscape-16x9'
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
    bindings: bindingRecords(definition, rendered.bindings),
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
      'the factory reads $bindings time/seed only; runPass context time/seed are never consumed'),
    controlRow('bound-time-ten', { time: 10 }, 'differs', 'bound time 0x3f000000 -> 0x41200000',
      'bound time is live through the speedA/speedB offset terms'),
    controlRow('bound-seed-123', { seed: 123 }, 'identical', 'bound seed int32 3 -> 123',
      'measured invariant at defines 40/30; see seed_liveness_census. seed remains a required int32 ABI binding'),
    controlRow('bound-wrap-true', { wrap: true }, 'identical', 'bound wrap false -> true',
      'lf = map(loopAScale=1, 1, 100, 6, 1) = 6.0 is already integral, so floor(lf) is a no-op; '
      + 'see wrap_liveness_census and shape-wrap-live-37-61 for the live half of this pair'),
  ],
}
if (controlGroup.controls[0].observed !== 'identical') {
  throw new Error('external runPass time/seed changed the output; the shader-owned uniforms do not dominate')
}
if (controlGroup.controls[1].observed !== 'differs') {
  throw new Error('bound time did not change the output')
}
for (const control of controlGroup.controls) {
  if (!control.pass) throw new Error(`control ${control.name} expected ${control.expectation} but observed ${control.observed}`)
}

// ---------------------------------------------------------------------------
// Bound-seed liveness census (measured invariant, per shape-design.md 4.2)
// ---------------------------------------------------------------------------

const seedProbeValues = [-2147483648, -7, 0, 1, 3, 123, 65537, 2147483647]
const seedProbes = seedProbeValues.map((seed) => {
  const output = render(canonicalFactory, { ...controlAnchor, seed, name: `seed-probe-${seed}` }).output
  const comparison = compareExact(output, controlBaselineExpected, `seed-probe/${seed}`)
  return { seed, f32_sha256: sha256(bytesOf(output.data)), differs_from_baseline: !comparison.exact,
    changed_lane_count: comparison.changed_lane_count ?? 0 }
})
const seedLivenessCensus = {
  probe_case: anchorName,
  probes: seedProbes,
  bound_seed_changes_output: seedProbes.some((probe) => probe.differs_from_baseline),
  consumers: [
    'offset(): the 300..380 arm forwards seedVal into value(...) as st + seedVal',
    'randomFromLatticeWithOffset(): the scalar uint XOR sites at normalized 97, 98, 99',
    'value(): the interp == 10 and interp == 11 arms',
  ],
  reason: 'At defines LOOP_A_OFFSET=40 / LOOP_B_OFFSET=30 the only main() consumers of the `seed` '
    + 'uniform are the two offset(...) calls. Offset 40 selects the `loopOffset >= 40 && loopOffset '
    + '<= 120` arm, which dispatches shape(st, sides, freq*0.5) and never reads seedVal; offset 30 '
    + 'selects the absolute-distance arm, which also never reads seedVal. Every seed consumer listed '
    + 'above sits behind the 300..380 arm, which these defines do not select.',
  design_agreement: 'shape-design.md section 4.2 records bound `seed` as proven invariant at 40/30 and '
    + 'explicitly instructs this package NOT to require it to differ. The eight probes above are the '
    + 'measurement backing that instruction.',
}
if (seedLivenessCensus.bound_seed_changes_output) {
  throw new Error('bound seed changed the output; shape-design.md section 4.2 records it as invariant at 40/30')
}

// ---------------------------------------------------------------------------
// Bound-wrap liveness census: invariant at integral lf, live at non-integral lf
// ---------------------------------------------------------------------------

function lfFor(scale) { return 6 + (1 - 6) * (scale - 1) / (100 - 1) }

const wrapProbeCases = [anchorName, cropCaseName]
const wrapProbes = wrapProbeCases.map((name) => {
  const definition = cases.find((item) => item.name === name)
  const flipped = render(canonicalFactory, { ...definition, wrap: !definition.wrap, name: `${name}/wrap-flip` }).output
  const comparison = compareExact(flipped, canonicalExpected.get(name), `wrap-probe/${name}`)
  return {
    case: name,
    bound_wrap: definition.wrap,
    loop_a_scale: definition.loopAScale,
    loop_b_scale: definition.loopBScale,
    lf_a: lfFor(definition.loopAScale),
    lf_b: lfFor(definition.loopBScale),
    lf_a_is_integral: Number.isInteger(lfFor(definition.loopAScale)),
    lf_b_is_integral: Number.isInteger(lfFor(definition.loopBScale)),
    flip_differs: !comparison.exact,
    changed_lane_count: comparison.changed_lane_count ?? 0,
    f32_sha256: sha256(bytesOf(flipped.data)),
  }
})
const wrapLivenessCensus = {
  probes: wrapProbes,
  rule: 'wrap only reaches the output through `lf = floor(lf)`. It is inert wherever '
    + 'lf = map(loopScale, 1, 100, 6, 1) is already integral and live wherever it is not.',
  invariant_witness: anchorName,
  live_witness: cropCaseName,
}
{
  const invariant = wrapProbes.find((probe) => probe.case === anchorName)
  const live = wrapProbes.find((probe) => probe.case === cropCaseName)
  if (!invariant.lf_a_is_integral || !invariant.lf_b_is_integral || invariant.flip_differs) {
    throw new Error('the wrap-invariant witness is not invariant')
  }
  if (live.lf_a_is_integral || live.lf_b_is_integral || !live.flip_differs) {
    throw new Error('the wrap-live witness is not live')
  }
}

// ---------------------------------------------------------------------------
// Speed sign/zero census on the anchor: all nine combinations are distinct
// ---------------------------------------------------------------------------

const speedCombinations = [[50, 50], [50, 0], [0, 50], [-50, 50], [50, -50], [-50, -50], [0, 0], [-50, 0], [0, -50]]
const speedProbes = speedCombinations.map(([speedA, speedB]) => {
  const output = render(canonicalFactory, { ...controlAnchor, speedA, speedB, name: `speed-${speedA}-${speedB}` }).output
  return { speedA, speedB, f32_sha256: sha256(bytesOf(output.data)) }
})
const speedSignCensus = {
  probe_case: anchorName,
  probes: speedProbes,
  distinct_digest_count: new Set(speedProbes.map((probe) => probe.f32_sha256)).size,
  rule: 'the speedA and speedB sign/zero arms are pairwise distinct; a collapsed arm is a stop condition',
}
if (speedSignCensus.distinct_digest_count !== speedProbes.length) {
  throw new Error('two speed sign/zero combinations collapsed to the same output')
}

// ---------------------------------------------------------------------------
// Mutation discrimination, generated rather than asserted
// ---------------------------------------------------------------------------

// The two mutants target the two DIFFERENT numeric contracts this program
// exists to prove. Their expected discrimination is frozen PER CASE, because
// two cases with the same aspect ratio can differ in whether they discriminate.
const mutantSpecs = [
  {
    name: 'shape-aspect-f32-narrowed',
    target: 'the `aspectRatio` write in main(): a plain JS Number (double), never narrowed to f32',
    contract: 'aspectRatio is a double; a port that types it float diverges',
    anchor: 'aspectRatio = fullResolution[0] / fullResolution[1];',
    replacement: 'aspectRatio = Math.fround(fullResolution[0] / fullResolution[1]);',
    reaching: 'cases whose aspect ratio is not exactly f32-representable AND that reach an aspectRatio read',
    expected: {
      'shape-landscape-16x9': true,
      'shape-crop-1280x720': true,
      'shape-square-12': false,
      'shape-portrait-9x16': false,
      'shape-zero-speeds': false,
      'shape-wrap-live-37-61': true,
      'shape-negative-speeds': true,
      'shape-extreme-tile-offset': false,
    },
  },
  {
    name: 'shape-globalcoord-unnarrowed',
    target: 'the `globalCoord` declaration: a Float32Array whose every lane store narrows to f32',
    contract: 'globalCoord lanes are f32; a port that keeps them double diverges',
    anchor: 'var globalCoord = new Float32Array([0, 0]);',
    replacement: 'var globalCoord = [0, 0];',
    reaching: 'only tile offsets that push gl_FragCoord.xy + tileOffset out of the exactly-representable range',
    expected: {
      'shape-landscape-16x9': false,
      'shape-crop-1280x720': false,
      'shape-square-12': false,
      'shape-portrait-9x16': false,
      'shape-zero-speeds': false,
      'shape-wrap-live-37-61': false,
      'shape-negative-speeds': false,
      'shape-extreme-tile-offset': true,
    },
  },
]

function compileMutant(spec) {
  const occurrences = canonicalText.split(spec.anchor).length - 1
  if (occurrences !== 1) throw new Error(`${spec.name}: mutation anchor matched ${occurrences} times`)
  const mutatedText = canonicalText.replace(spec.anchor, spec.replacement)
  return { occurrences, mutatedText, factory: Function(`"use strict"; return (${mutatedText});`)() }
}

const mutationLedger = mutantSpecs.map((spec) => {
  if (Object.keys(spec.expected).length !== cases.length) {
    throw new Error(`${spec.name}: expected discrimination table does not cover every case`)
  }
  const { occurrences, mutatedText, factory } = compileMutant(spec)
  const results = cases.map((definition) => {
    const output = render(factory, definition).output
    const comparison = compareExact(output, canonicalExpected.get(definition.name), `${spec.name}/${definition.name}`)
    const differs = !comparison.exact
    const expected = spec.expected[definition.name]
    if (typeof expected !== 'boolean') throw new Error(`${spec.name}: no expectation for ${definition.name}`)
    if (differs !== expected) {
      throw new Error(`${spec.name}: case ${definition.name} expected discriminates=${expected} but measured ${differs}; `
        + 'a flipped case is a stop condition, not something to re-baseline')
    }
    return {
      case: definition.name,
      expected_discriminates: expected,
      differs,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      changed_rgba8_byte_count: comparison.changed_rgba8_byte_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
      rgba8_sha256: sha256(bytesOf(output.toRgba8())),
      first_mismatch: comparison.first_float32_mismatch ?? null,
    }
  })
  if (!results.some((result) => result.differs)) throw new Error(`${spec.name}: no case discriminates this mutant`)
  return {
    name: spec.name,
    target: spec.target,
    contract: spec.contract,
    reaching: spec.reaching,
    classification: 'rendered canonical-JS one-anchor/one-replacement mutant',
    anchor_sha256: sha256(spec.anchor),
    replacement_sha256: sha256(spec.replacement),
    mutated_factory_sha256: sha256(mutatedText),
    anchor_occurrences: occurrences,
    witness_cases: results.filter((result) => result.differs).map((result) => result.case),
    control_cases: results.filter((result) => !result.differs).map((result) => result.case),
    results,
  }
})

// ---------------------------------------------------------------------------
// globalCoord native-binding witness
//
// shape-design.md section 12 could not determine whether the extreme tile
// offset survives the C++ binding path. It does. An instrumented probe factory
// -- one anchor/one replacement, exactly like a mutant, and never a parity
// array -- publishes globalCoord's two f32 lanes per pixel. Phase 2 can bind
// `tileOffset` to the words below, evaluate the emitted
// `glsl::swizzle<0,1>(context.frag_coord) + state.tileOffset`, and compare to
// these words to prove the f32-lane contract has a real native witness.
// ---------------------------------------------------------------------------

const globalCoordProbeSpec = {
  anchor: '(fragColor[0] = color[0], fragColor[1] = color[1], fragColor[2] = color[2], fragColor[3] = color[3], fragColor);',
  replacement: '(fragColor[0] = globalCoord[0], fragColor[1] = globalCoord[1], fragColor[2] = 0, fragColor[3] = 1, fragColor);',
}
const globalCoordProbe = compileMutant({ name: 'globalcoord-probe', ...globalCoordProbeSpec })
const globalCoordCase = cases.find((item) => item.name === 'shape-extreme-tile-offset')
const globalCoordSurface = render(globalCoordProbe.factory, globalCoordCase).output
const globalCoordWords = words(globalCoordSurface.data)
const globalCoordLanes = []
for (let pixel = 0; pixel < globalCoordCase.width * globalCoordCase.height; pixel += 1) {
  globalCoordLanes.push(u32Hex(globalCoordWords[pixel * 4]), u32Hex(globalCoordWords[pixel * 4 + 1]))
}
if (globalCoordLanes.length !== globalCoordCase.width * globalCoordCase.height * 2) {
  throw new Error('globalCoord witness lane census drift')
}
if (globalCoordSurface.data.filter(Number.isFinite).length !== globalCoordSurface.data.length) {
  throw new Error('globalCoord witness produced a non-finite lane')
}
const globalCoordWitness = {
  case: globalCoordCase.name,
  width: globalCoordCase.width,
  height: globalCoordCase.height,
  tile_offset_f32_words_le: Array.from(words(f32Vector(globalCoordCase.tileOffset)), u32Hex),
  probe_anchor_sha256: sha256(globalCoordProbeSpec.anchor),
  probe_replacement_sha256: sha256(globalCoordProbeSpec.replacement),
  probe_factory_sha256: sha256(globalCoordProbe.mutatedText),
  classification: 'instrumented canonical-JS probe factory; NOT a parity array and never compared to a rendered shade',
  lane_order: 'top-down raster order; two lanes per pixel, globalCoord.x then globalCoord.y',
  f32_words_le: globalCoordLanes,
  f32_sha256: sha256(Buffer.concat(globalCoordLanes.map((word) => {
    const buffer = Buffer.alloc(4)
    buffer.writeUInt32LE(Number(word), 0)
    return buffer
  }))),
  native_expression: 'glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset)',
  purpose: 'answers the open question in shape-design.md section 12: whether the extreme tile offset '
    + 'is expressible end-to-end through the C++ binding ABI',
}

// ---------------------------------------------------------------------------
// globalCoord witness census: where the f32-lane contract is and is not visible
// ---------------------------------------------------------------------------

const globalCoordMutantFactory = compileMutant(mutantSpecs[1]).factory
const globalCoordProbeOffsets = [[0, 0], [8.25, 4.5], [1048576.5, 0], [16777216, 0], [131072.1, 0], [131072.1, 0.3]]
const globalCoordCensus = {
  probe_geometry: { width: 8, height: 6, full_resolution: [16, 12] },
  probes: globalCoordProbeOffsets.map((tileOffset) => {
    const definition = { ...controlAnchor, name: `globalcoord-probe-${tileOffset.join('-')}`,
      width: 8, height: 6, tileOffset, fullResolution: [16, 12] }
    const canonical = render(canonicalFactory, definition).output
    const mutated = render(globalCoordMutantFactory, definition).output
    const comparison = compareExact(mutated, expectedRecord(canonical), `globalcoord-census/${tileOffset.join(',')}`)
    return {
      tile_offset: tileOffset,
      tile_offset_f32_words_le: Array.from(words(f32Vector(tileOffset)), u32Hex),
      discriminates: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
    }
  }),
  rule: 'the f32-lane contract on globalCoord is only observable where gl_FragCoord.xy + tileOffset '
    + 'leaves the exactly-representable f32 range; ordinary tile offsets leave it unwitnessed',
}
if (!globalCoordCensus.probes.some((probe) => probe.discriminates)) {
  throw new Error('the globalCoord witness census found no discriminating tile offset')
}
if (globalCoordCensus.probes[0].discriminates) {
  throw new Error('a zero tile offset discriminated the globalCoord mutant; the census is not a control')
}

// ---------------------------------------------------------------------------
// Fixture assembly
// ---------------------------------------------------------------------------

const caseNames = cases.map((item) => item.name)
const coverageAxes = {
  aspect_exactly_f32_representable: {
    'no': ['shape-landscape-16x9', 'shape-crop-1280x720', 'shape-wrap-live-37-61',
      'shape-negative-speeds', 'shape-zero-speeds', 'shape-extreme-tile-offset'],
    'yes': ['shape-square-12', 'shape-portrait-9x16'],
  },
  aspect_shape: {
    landscape: ['shape-landscape-16x9', 'shape-crop-1280x720', 'shape-zero-speeds',
      'shape-negative-speeds', 'shape-extreme-tile-offset'],
    portrait: ['shape-portrait-9x16'],
    square: ['shape-square-12'],
    tile_portrait_of_landscape_full: ['shape-wrap-live-37-61'],
  },
  tiling: {
    tiled: ['shape-crop-1280x720', 'shape-wrap-live-37-61', 'shape-extreme-tile-offset'],
    untiled: caseNames.filter((name) => !['shape-crop-1280x720', 'shape-wrap-live-37-61', 'shape-extreme-tile-offset'].includes(name)),
  },
  wrap: {
    'true': ['shape-crop-1280x720', 'shape-portrait-9x16', 'shape-wrap-live-37-61'],
    'false': ['shape-landscape-16x9', 'shape-square-12', 'shape-zero-speeds',
      'shape-negative-speeds', 'shape-extreme-tile-offset'],
  },
  wrap_liveness: {
    live_non_integral_lf: ['shape-wrap-live-37-61'],
    inert_integral_lf: ['shape-landscape-16x9', 'shape-crop-1280x720', 'shape-portrait-9x16',
      'shape-zero-speeds', 'shape-negative-speeds', 'shape-extreme-tile-offset'],
    inert_wrap_false_non_integral_lf: ['shape-square-12'],
  },
  speed_a_sign: {
    positive: ['shape-landscape-16x9', 'shape-crop-1280x720', 'shape-portrait-9x16',
      'shape-wrap-live-37-61', 'shape-extreme-tile-offset'],
    negative: ['shape-square-12', 'shape-negative-speeds'],
    zero: ['shape-zero-speeds'],
  },
  speed_b_sign: {
    positive: ['shape-landscape-16x9', 'shape-crop-1280x720', 'shape-square-12', 'shape-extreme-tile-offset'],
    negative: ['shape-portrait-9x16', 'shape-wrap-live-37-61', 'shape-negative-speeds'],
    zero: ['shape-zero-speeds'],
  },
  bound_seed: Object.fromEntries(cases.map((item) => [item.name, item.seed])),
  bound_time_f32_word: Object.fromEntries(cases.map((item) => [item.name, f32Bits(f(item.time))])),
}
for (const [axis, buckets] of Object.entries(coverageAxes)) {
  if (axis === 'bound_seed' || axis === 'bound_time_f32_word') continue
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
  oracle_authority: `unmodified public ${factoryName} from an immutable noisemaker-for-cpu snapshot, `
    + 'executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates',
  mutable_global_contracts: {
    aspectRatio: {
      javascript_declaration: 'var aspectRatio = 0;',
      numeric_contract: 'plain JS Number -- a double, NEVER narrowed to f32',
      write_expression: 'aspectRatio = fullResolution[0] / fullResolution[1];',
      mutant: 'shape-aspect-f32-narrowed',
      oracle_discriminable: true,
    },
    globalCoord: {
      javascript_declaration: 'var globalCoord = new Float32Array([0, 0]);',
      numeric_contract: 'Float32Array -- every lane store narrows to f32',
      write_expression: 'globalCoord[0] = gl_FragCoord[0] + tileOffset[0], globalCoord[1] = gl_FragCoord[1] + tileOffset[1]',
      mutant: 'shape-globalcoord-unnarrowed',
      oracle_discriminable: true,
    },
    shadowed_binding: 'createCanonicalBindings supplies an unrelated `aspectRatio` uniform. The '
      + 'factory-scope `var aspectRatio` shadows it and the binding is never read; the generator '
      + 'fails closed if the factory ever reads $bindings["aspectRatio"].',
  },
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays; never reconstructed from expected words',
    tolerance: 'none',
    comparison_order: 'dimensions, exact expected/actual lane count, exact expected/actual byte count, every Float32 word, every independent RGBA8 byte',
    coordinates: 'all stored rows and first mismatches use top-down storage order and top-down x/y',
    alpha: 'every output alpha float word is exactly 0x3f800000 and every RGBA8 alpha byte is exactly 255',
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
      textures: effect.textures,
      external_texture: effect.externalTexture,
    },
  },
  comparer_self_tests: comparerSelfTests(),
  coverage_axes: coverageAxes,
  render_cases: renderCases,
  crop_identity: cropIdentity,
  control_group: controlGroup,
  seed_liveness_census: seedLivenessCensus,
  wrap_liveness_census: wrapLivenessCensus,
  speed_sign_census: speedSignCensus,
  globalcoord_witness_census: globalCoordCensus,
  globalcoord_native_binding_witness: globalCoordWitness,
  mutation_ledger: mutationLedger,
  mutation_discrimination_contract: {
    per_case: true,
    rule: 'discrimination is frozen and validated PER CASE AND PER MUTANT. Two cases with the same '
      + 'aspect ratio can differ in whether they discriminate, so a per-mutant summary is not '
      + 'sufficient and is never accepted here. A case that flips is a stop condition.',
    disjoint_witness_requirement: 'The two mutants must have DISJOINT witness sets. `aspectRatio` '
      + 'and `globalCoord` carry different numeric contracts, and a case that witnesses both could '
      + 'not attribute a divergence to one of them. This is enforced, not merely observed: the '
      + 'materializer rejects the document if any case appears in both witness sets.',
    witness_sets: Object.fromEntries(mutationLedger.map((mutant) => [mutant.name, {
      witness_cases: [...mutant.witness_cases],
      control_cases: [...mutant.control_cases],
    }])),
    expected: Object.fromEntries(mutantSpecs.map((spec) => [spec.name, spec.expected])),
  },
  claim_boundaries: {
    dead_hash_branch: 'With defines 40/30 the randomFromLatticeWithOffset body, its three scalar uint '
      + 'XOR sites, and the circles/rings/diamonds/value arms are conservative call-graph reachable but '
      + 'are not entered by a normal full render. These full-surface cases must never be cited as proof '
      + 'that any of them executed.',
    normalized_source: 'Normalized/typed source, function, interface, and whole-program hashes are the '
      + 'frontend profiles’ authority and are deliberately not restated here.',
    bound_seed: 'The bound `seed` uniform is a required int32 ABI binding but is pixel-inert at the '
      + 'default defines; see seed_liveness_census. It is recorded as proven invariant, not waived.',
    bound_wrap: 'The bound `wrap` uniform is live only where lf is non-integral. Exactly one case '
      + 'witnesses the live half; see wrap_liveness_census.',
    globalcoord_lane_contract: 'The globalCoord f32-lane contract is witnessed by exactly one render '
      + 'case, shape-extreme-tile-offset. It is NOT a structural-only claim: the case is expressible '
      + 'end-to-end through the C++ binding ABI, and globalcoord_native_binding_witness carries the '
      + 'per-pixel lane words phase 2 must reproduce.',
    production_crop_full_route: 'shape-crop-1280x720 exercises the tileOffset rule at 1280x720 but its '
      + 'full route is not stored; the translation proof is carried by shape-wrap-live-37-61.',
  },
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function reportFor(data) {
  const caseRows = data.render_cases.map((item) =>
    `| ${item.name} | ${item.width}x${item.height} | ${item.route} | ${item.bindings.wrap.value} | ${item.output_expected.f32_sha256} | ${item.output_expected.rgba8_sha256} |`).join('\n')
  const coverageRows = Object.entries(data.coverage_axes)
    .filter(([axis]) => axis !== 'bound_seed' && axis !== 'bound_time_f32_word')
    .map(([axis, buckets]) => Object.entries(buckets)
      .map(([bucket, names]) => `| ${axis} | ${bucket} | ${names.join(', ')} |`).join('\n')).join('\n')
  const controlRows = data.control_group.controls.map((item) =>
    `| ${item.name} | ${item.axis} | ${item.expectation} | ${item.observed} | ${item.pass ? 'pass' : 'FAIL'} | ${item.changed_lane_count} |`).join('\n')
  const mutantRows = data.mutation_ledger.map((mutant) => mutant.results.map((result) =>
    `| ${mutant.name} | ${result.case} | ${result.expected_discriminates ? 'witness' : 'control'} | ${result.differs ? 'differs' : 'identical'} | ${result.changed_lane_count} |`).join('\n')).join('\n')
  const seedRows = data.seed_liveness_census.probes.map((probe) =>
    `| ${probe.seed} | ${probe.f32_sha256} | ${probe.differs_from_baseline ? 'differs' : 'identical'} |`).join('\n')
  const wrapRows = data.wrap_liveness_census.probes.map((probe) =>
    `| ${probe.case} | ${probe.loop_a_scale} / ${probe.loop_b_scale} | ${probe.lf_a} / ${probe.lf_b} | ${probe.lf_a_is_integral && probe.lf_b_is_integral ? 'integral' : 'non-integral'} | ${probe.flip_differs ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')
  const speedRows = data.speed_sign_census.probes.map((probe) =>
    `| ${probe.speedA} | ${probe.speedB} | ${probe.f32_sha256} |`).join('\n')
  const witnessRows = data.globalcoord_witness_census.probes.map((probe) =>
    `| [${probe.tile_offset.join(', ')}] | ${probe.tile_offset_f32_words_le.join(', ')} | ${probe.discriminates ? 'discriminates' : 'no'} | ${probe.changed_lane_count} |`).join('\n')
  return `# Shape184 exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; exact defines
\`LOOP_A_OFFSET=${data.defines.LOOP_A_OFFSET}\`, \`LOOP_B_OFFSET=${data.defines.LOOP_B_OFFSET}\`.

## The two contracts this program exists to prove

\`synth/shape\` declares two mutable uninitialized file-scope globals with **different** numeric
contracts, and the parity target is the transpiler's materialization, not GLSL semantics:

| Global | JavaScript | Contract | Mutant | Discriminable |
| --- | --- | --- | --- | --- |
| \`aspectRatio\` | \`var aspectRatio = 0;\` | plain Number, a **double**, never narrowed to f32 | \`shape-aspect-f32-narrowed\` | yes |
| \`globalCoord\` | \`new Float32Array([0, 0])\` | **f32 lanes**, every lane store narrows | \`shape-globalcoord-unnarrowed\` | yes |

A port that types \`aspectRatio\` as \`float\` because GLSL says \`float\` diverges, and a port that
keeps \`globalCoord\` in double lanes diverges. Both halves have a render witness here.

The shipped binding set also contains an unrelated \`aspectRatio\` uniform. The factory-scope
\`var aspectRatio\` shadows it and it is never read; the generator fails closed if that ever changes.

## Authority

This oracle is produced by the ${data.oracle_authority}. The generator refuses to run unless
\`kernelFactories.get(key) === canonicalKernelFactories[key]\`, the factory is named
\`${factoryName}\`, its \`Function.prototype.toString\` SHA-256 is \`${factoryTextSha256}\`, neither
adapter table owns the key, \`canonicalAdapterFactories\` matches its
${data.provenance.adapter_routed_keys.length}-key census exactly, the key is absent from the
${data.provenance.corpus_adapter_keys.length}-key \`check_corpus._ADAPTERS\` eligibility table
**parsed out of the live \`${data.provenance.corpus_adapter_source.relative_path_from_noisemaker_for_cpp}\`**
rather than transcribed, all six pinned CPU files match, and every module in the
${data.provenance.cpu_snapshot.import_closure_file_count}-file import closure resolves by real path beneath the immutable snapshot.
Bare module specifiers other than \`node:\` builtins are rejected, and the live checkout is refused as
a \`--cpu-root\`.

No absolute path is recorded anywhere in this package. The \`--cpu-root\` argument is stored as
\`${data.provenance.cpu_snapshot.argument}\` and the rejected live checkout as
\`${data.provenance.cpu_snapshot.live_checkout_rejected}\`, resolved at run time from
${data.provenance.cpu_snapshot.live_checkout_resolution}. The import closure and the six pinned
hashes authenticate the snapshot completely, so the literal path authenticates nothing while binding
\`--check\` to one directory on one machine. The gate therefore passes against a valid snapshot at any
path.

## Bindings

The program has exactly ${data.runtime_binding_names.length} runtime bindings:
${data.runtime_binding_names.map((name) => `\`${name}\``).join(', ')}.
\`LOOP_A_OFFSET\` and \`LOOP_B_OFFSET\` are compile-time defines recorded separately and are never
counted as bindings. \`resolution\` is declared and never read by the program; it remains a required
ABI binding and is not "cleaned up".

## Render fixtures

| Case | Size | Route | wrap | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
${caseRows}

Every case stores exact dimensions, all ${data.runtime_binding_names.length} bindings with every float and vector lane as a
hexadecimal f32 word, the external \`runPass\` time/seed pair, the complete expected Float32 word
array, the complete independently captured RGBA8 byte array, finite/non-finite lane counts, and a
SHA-256 over each array. Alpha is exactly \`0x3f800000\` / \`255\` in every case and every route.

### Deviations from \`shape-design.md\` section 6.2, and why

All eight design cases are present and every coverage claim they carry is honoured. Four deviations,
each recorded here rather than absorbed silently.

| Design | Shipped as | Change | Reason |
| --- | --- | --- | --- |
| \`shape-landscape-64x36\` | \`shape-landscape-16x9\` | 2,304 px to 144 px | 64/36 and 16/9 are the same rational, so the \`aspectRatio\` double is bit-identical. The control group renders four one-axis variants of the anchor, so the anchor's area is multiplied by five in the stored document. |
| \`shape-square-48\` | \`shape-square-12\` | 2,304 px to 144 px | ratio is exactly 1.0 either way; this is a non-reaching control |
| \`shape-portrait-36x64\` | \`shape-portrait-9x16\` | 2,304 px to 144 px | ratio is exactly 0.5625 either way; this is a non-reaching control |
| \`shape184_*\` filenames (design section 6) | \`shape_*\` | \`shape_oracle_generator.mjs\`, \`shape-oracles.json\`, \`shape-oracle-report.md\`, \`tests/oracles/shape_expected.inc\` | the unversioned names were specified for this package; the C++ namespace remains \`shape184_oracle\` and the schema remains \`…shape184.pixel-parity.v1\`, so the typed-row identity is unchanged |
| \`shape-crop-1280x720\` full route | stored as the 40x24 **crop window** only | the whole 1280x720 array is not stored | the proof needs only the window (3,840 words + 3,840 bytes, the size of a tile array), so the full route is rendered in memory, compared, and discarded. The translation is re-derived from the stored window, and \`shape-wrap-live-37-61\` additionally re-derives its tile from a stored 11x9 full route. |

The design warns that two cases with the same aspect ratio can differ in whether they discriminate,
so none of these substitutions is assumed to inherit its coverage. Every one is **re-measured** by
this generator on every run, and the per-case ledger below is what \`--check\` enforces.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
${coverageRows}

## Top-down crop normalization

Both runners store rows top-down while GLSL fragment coordinates are bottom-left. The
\`${data.crop_identity.case}\` case is a genuine crop: \`${data.crop_identity.tile_offset_rule}\`. For crop
\`(${data.crop_identity.rect.crop_x}, ${data.crop_identity.rect.crop_y})\` of size
\`${data.crop_identity.rect.tile_width}x${data.crop_identity.rect.tile_height}\` from
\`${data.crop_identity.rect.full_width}x${data.crop_identity.rect.full_height}\`, the tile route binds
\`tileOffset\` words \`${data.crop_identity.tile_offset_f32_words_le.join(', ')}\`; the other ${data.crop_identity.held_identical_bindings.length} bindings are held identical.
Tile output equals the corresponding top-down crop of the full-route output exactly:
${data.crop_identity.exact_word_mismatches} word mismatches and ${data.crop_identity.exact_byte_mismatches} byte mismatches.
Binding raw top-down \`crop_y\` into \`tileOffset.y\` instead changes
${data.crop_identity.raw_crop_y_trap.changed_lane_count} lanes, so the witness is not vacuous.

\`shape-crop-1280x720\` proves the same rule at production scale. Its full
\`${data.crop_identity.production_shaped_case.full_route_dimensions.join('x')}\` route is rendered in
memory and discarded; only the
\`${data.crop_identity.production_shaped_case.full_route_crop_window.width}x${data.crop_identity.production_shaped_case.full_route_crop_window.height}\`
window it yields is stored, and the tile equals it exactly:
${data.crop_identity.production_shaped_case.exact_word_mismatches} word mismatches and
${data.crop_identity.production_shaped_case.exact_byte_mismatches} byte mismatches. Binding raw
\`crop_y\` there changes ${data.crop_identity.production_shaped_case.raw_crop_y_trap.changed_lane_count} lanes.
${data.crop_identity.production_shaped_case.note}

## One-axis control group on \`${data.control_group.anchor}\`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${controlRows}

## Bound-seed liveness census

| Bound seed | Float32 SHA-256 | Versus baseline |
| --- | --- | --- |
${seedRows}

${data.seed_liveness_census.reason}

${data.seed_liveness_census.design_agreement}

## Bound-wrap liveness census

| Case | loopAScale / loopBScale | lf_a / lf_b | lf | wrap flipped | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${wrapRows}

${data.wrap_liveness_census.rule}

## Speed sign/zero census on \`${data.speed_sign_census.probe_case}\`

| speedA | speedB | Float32 SHA-256 |
| ---: | ---: | --- |
${speedRows}

All ${data.speed_sign_census.distinct_digest_count} combinations are pairwise distinct.

## globalCoord witness census

| tileOffset | f32 words | Result | Changed lanes |
| --- | --- | --- | ---: |
${witnessRows}

${data.globalcoord_witness_census.rule}

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
${mutantRows}

Both mutants are independent one-anchor/one-replacement rewrites of the canonical factory text,
compiled and rendered by this generator. The expected outcome is frozen **per case and per mutant**;
\`--check\` fails if any single cell flips, in either direction. The native implementation must match
only the unmutated oracle, and no hand-mutated generated C++ is committed.

## Native binding witness for the globalCoord contract

\`shape-design.md\` section 12 could not determine whether \`shape-extreme-tile-offset\` survives the
C++ binding path. **It does.** \`globalcoord_native_binding_witness\` stores
${data.globalcoord_native_binding_witness.f32_words_le.length} f32 words -- \`globalCoord.x\` and
\`globalCoord.y\` for each of the ${data.globalcoord_native_binding_witness.width}x${data.globalcoord_native_binding_witness.height}
pixels -- produced by an instrumented probe factory built from the canonical text by one
anchor/one replacement. It is never compared to a rendered shade and is not a parity array. Phase 2
binds \`tileOffset\` to words \`${data.globalcoord_native_binding_witness.tile_offset_f32_words_le.join(', ')}\`, evaluates
\`${data.globalcoord_native_binding_witness.native_expression}\`, and must reproduce every word.

## Claim boundaries

- ${data.claim_boundaries.dead_hash_branch}
- ${data.claim_boundaries.normalized_source}
- ${data.claim_boundaries.bound_seed}
- ${data.claim_boundaries.bound_wrap}
- ${data.claim_boundaries.globalcoord_lane_contract}
- ${data.claim_boundaries.production_crop_full_route}

## Regeneration

\`\`\`sh
node docs/port-engineering/shape-parity/shape_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/shape-parity/shape_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_shape_native_oracle_include.py --self-test
\`\`\`

Both generators are fail-closed and check mode performs no writes.
`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)

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
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Shape184 oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Shape184 oracle report drift')
}
const controlSummary = controlGroup.controls.map((item) => `${item.name}=${item.observed}`).join(' ')
const ledgerSummary = mutationLedger.map((mutant) => `${mutant.name}:${mutant.witness_cases.length}/${cases.length}`).join(' ')
console.log(`Shape184 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} cases, `
  + `${mutationLedger.length} mutants [${ledgerSummary}], controls [${controlSummary}], `
  + `crop exact, alpha 0x3f800000/255`)
