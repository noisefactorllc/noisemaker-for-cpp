#!/usr/bin/env node
// Wobble canonical JavaScript oracle generator (`filter/wobble:wobble`, typed
// row 189 -- the first varying-admission program).
//
// Authority: the unmodified public canonical factory `canonicalFactory178`
// from an immutable snapshot of `noisemaker-for-cpu`, executed through the
// pinned `bindCanonicalKernel` / `GlslCpuRuntime` / `runPass` path. No C++
// output participates in any expected array. A locally reimplemented formula
// is not an oracle and is never used here.
//
// This program exists to pin the VARYING materialization: wobble declares
// `in vec2 v_texCoord;` (raw wobble.glsl:14) and reads it exactly once, in
// main, as `vec2 sampleCoord = v_texCoord + offset;`. The JavaScript has no
// vertex stage and never interpolates: `beginPixel` hardcodes
// `this.varyings.v_texCoord[0] = uv[0]` / `[1] = uv[1]` (glsl-runtime.js),
// and the canonical kernel copies the slot per pixel via
// `v_texCoord.set($runtime.varyings["v_texCoord"])`. `v_texCoord` IS
// `context.uv` -- the pixel center's destination-local coordinate,
// `F32((x + 0.5) * (1 / width))` / `F32((height - y - 0.5) * (1 / height))`
// (pass-runner.js). Every case below is bound through that exact path; there
// is no varying binding to set and none is ever set by hand.
//
// The `range = 0` case is the purpose-built discriminator: `r = max(range, 0)`
// makes `offsetScale = r * (0.01 + speed * 0.02)` exactly zero, so
// `offset` is +-0 and `sampleCoord` degenerates to a pure pass-through of
// `applyWrap(v_texCoord)`, which is the identity on the open unit interval
// for all three wrap arms. Any materialization error -- lane order swapped,
// y orientation flipped, f32 drift -- lands exactly there. Measured: the two
// varying mutants are the ONLY ledger mutants that move a lane on that case.
//
// The tile-vs-full crop identity is PROBED, not assumed (the cellRefract
// section 15 lesson): measured NON-identity on both the live-clamp arm and
// the range-zero arm, with the mechanism attributed by instrumented
// sampleCoord probes. wobble has no tileOffset/fullResolution bindings at
// all, so no offset rule exists to get right or wrong -- the non-identity is
// purely the destination-local `v_texCoord`.
//
//   node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'wobble-oracles.json')
const reportPath = path.join(here, 'wobble-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_wobble_native_oracle_include.py')

const schema = 'noisemaker-for-cpp.wobble189.pixel-parity.v1'
const schemaVersion = 1
const programKey = 'filter/wobble:wobble'
const effectKey = 'filter/wobble'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const defines = {}
const factoryName = 'canonicalFactory178'
const factoryTextSha256 = 'e09f2ef4c49b33b06febfac20d4eeea3563270f6edab6cb1f6761f2dd20759d4'
const nextFactoryName = 'canonicalFactory179'
// Cross-validation of the Function.prototype.toString pinning method: the
// same snapshot must reproduce cellRefract's frozen factory-text digest
// (cellrefract186 oracle, factoryTextSha256) or the method -- not the
// snapshot -- is untrustworthy and this generator refuses to run.
const crossValidationFactoryKey = 'classicNoisedeck/cellRefract:cellRefract'
const crossValidationFactorySha256 = '329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3'

// The live checkout is DERIVED, never hardcoded: a machine-specific absolute
// path in a checked-in gate is unrunnable on any other machine and leaks a
// home directory into the repository. `NOISEMAKER_FOR_CPU` overrides;
// otherwise the conventional sibling layout under $HOME is used.
const liveCpuCheckoutResolution =
  'process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu'
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU
  ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
if (liveCpuCheckout === null) {
  throw new Error('cannot resolve the live noisemaker-for-cpu checkout: set NOISEMAKER_FOR_CPU or HOME. '
    + 'Running without it would silently disable the live-checkout refusal.')
}

// Neither the `--cpu-root` argument nor the live-checkout path is recorded
// verbatim. The import closure and the six pinned file hashes authenticate
// the snapshot completely; the literal path authenticates nothing and would
// bind `--check` to one ephemeral directory on one machine.
const cpuRootPlaceholder = '<immutable-cpu-snapshot-root>'
const liveCheckoutPlaceholder = '<live-noisemaker-for-cpu-checkout>'
const sourceRelative = `tools/glslcpp/corpus/${corpusRevision}/sources/filter/wobble/wobble.glsl`
const sourceBytesExpected = 3105
const sourceSha256Expected = '1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc'

// Exactly five runtime bindings, in GLSL declaration order. wobble has NO
// preprocessor defines. `wrap` is a float uniform in the GLSL narrowed at use
// (`int mode = int(wrap);`, `wrap|0` in the JavaScript -- ToInt32 of the same
// Number), not an int32 binding.
const bindingNames = Object.freeze(['inputTex', 'time', 'speed', 'range', 'wrap'])
const bindingAbi = Object.freeze({
  inputTex: 'sampler2D', time: 'number', speed: 'number', range: 'number', wrap: 'number',
})

const pinnedCpuFiles = Object.freeze({
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
})

// Two distinct adapter tables, and both must be checked. This file is the ONE
// live C++ repository source this generator reads (the eligibility census);
// it never consults typed-slice state.
const corpusAdapterSourceRelative = 'tools/glslcpp/check_corpus.py'
const corpusAdapterCensusExpected = Object.freeze([
  'classicNoisedeck/fractal:fractal', 'filter/historicPalette:historicPalette',
  'filter/palette:palette', 'synth/julia:julia',
])
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
if (typeof canonicalFactory !== 'function') throw new Error('canonical wobble factory missing')
if (publicFactory !== canonicalFactory) throw new Error('public wobble factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('unexpected wobble adapter override')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected wobble adapter override value')
// The cross-validation: this snapshot + this method must reproduce cellRefract's
// frozen factory-text digest before the wobble pin below is worth anything.
{
  const crossFactory = canonicalKernelFactories[crossValidationFactoryKey]
  if (typeof crossFactory !== 'function') throw new Error('cross-validation cellRefract factory missing')
  const crossDigest = sha256(Function.prototype.toString.call(crossFactory))
  if (crossDigest !== crossValidationFactorySha256) {
    throw new Error(`factory-text pinning method cross-validation failed: cellRefract digest ${crossDigest}`)
  }
}
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
if (corpusAdapterKeys.includes(programKey)) throw new Error('filter/wobble:wobble must not be corpus-adapter-routed')
if (canonicalAdapterKeys.includes(programKey)) throw new Error('filter/wobble:wobble must not be adapter-routed')
{
  const observed = Object.keys(canonicalAdapterFactories).sort()
  const expected = [...canonicalAdapterKeys].sort()
  if (observed.length !== expected.length || observed.some((key, index) => key !== expected[index])) {
    throw new Error(`adapter table census drift: ${observed.join(', ')}`)
  }
}
if (canonicalFactory.name !== factoryName) throw new Error(`canonical wobble factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) throw new Error(`canonical wobble factory text drift: ${sha256(canonicalText)}`)

const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf(`function ${nextFactoryName}`, sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('canonical wobble factory source slice missing')
const canonicalSlice = canonicalKernelsSource.slice(sliceStart, sliceEnd)

// ---------------------------------------------------------------------------
// The varying materialization this package exists to pin, read from the
// shipped JS -- the declaration, the per-pixel copy, the runtime alias, and
// the pixel-loop numeric contract, each asserted against the pinned files.
// ---------------------------------------------------------------------------

const varyingName = 'v_texCoord'
const varyingDeclarationJs = `var ${varyingName} = new Float32Array([0, 0]);`
const varyingCopyJs = `${varyingName}.set($runtime.varyings["${varyingName}"])`
const varyingDeclarationGlsl = 'in vec2 v_texCoord;'
// declaration + both identifiers on the copy line + both reads in the
// sampleCoord line = 5 word-bounded occurrences in the whole factory.
const varyingOccurrenceCensus = 5
const runtimeVaryingSlotJs = 'v_texCoord: new Float32Array(2),'
const runtimeVaryingAliasJs = [
  'this.varyings.v_texCoord[0] = uv[0]',
  'this.varyings.v_texCoord[1] = uv[1]',
]
const passRunnerUvJs = ['uv[0] = fx * inverseWidth', 'uv[1] = fy * inverseHeight']
const varyingReadExpression = 'v_texCoord[0] + offset[0], v_texCoord[1] + offset[1]'

{
  if (canonicalText.split(varyingDeclarationJs).length - 1 !== 1) {
    throw new Error('varying slot declaration census drift')
  }
  if (canonicalText.split(varyingCopyJs).length - 1 !== 1) {
    throw new Error('varying per-pixel copy census drift')
  }
  const identifier = new RegExp(`\\b${varyingName}\\b`, 'g')
  const count = (canonicalText.match(identifier) ?? []).length
  if (count !== varyingOccurrenceCensus) {
    throw new Error(`varying identifier census drift: ${count} occurrences, expected ${varyingOccurrenceCensus}`)
  }
  if (canonicalText.split(varyingReadExpression).length - 1 !== 1) {
    throw new Error('varying read-site census drift: the single read is not the sampleCoord constructor')
  }
  // The slot must NOT be a pooled array (the normalMap section 15 pool-safety
  // lesson): it is a factory-scope allocation, aliased in place each pixel.
  // Only the slot's own lines are checked -- the single READ site builds a
  // pooled sampleCoord, which is exactly what the authority does.
  for (const line of [varyingDeclarationJs, varyingCopyJs]) {
    if (line.includes('Pooled')) throw new Error('the varying slot is pooled; the alias-in-place contract is wrong')
  }
  const runtimeSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.glsl_runtime[0]), 'utf8')
  if (runtimeSource.split(runtimeVaryingSlotJs).length - 1 !== 1) {
    throw new Error('runtime varying slot census drift')
  }
  for (const line of runtimeVaryingAliasJs) {
    if (runtimeSource.split(line).length - 1 !== 1) throw new Error(`runtime varying alias census drift: ${line}`)
  }
  const passRunnerSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.pass_runner[0]), 'utf8')
  for (const line of passRunnerUvJs) {
    // Twice: once in runPass, once in the byte-identical runPassAsync loop.
    const occurrences = passRunnerSource.split(line).length - 1
    if (occurrences !== 2) throw new Error(`pass-runner uv census drift: ${occurrences} of ${line}`)
  }
}

const sourcePath = path.join(cppRoot, sourceRelative)
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error('pinned wobble GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')
if (sourceText.split(varyingDeclarationGlsl).length - 1 !== 1) {
  throw new Error('the raw GLSL varying declaration census drifted')
}
const wrapArms = ['if (mode == 0) {', 'if (mode == 1) {']
for (const arm of wrapArms) {
  if (canonicalText.split(arm).length - 1 !== 1) throw new Error(`applyWrap arm census drift: ${arm}`)
}
if (canonicalText.split('wrap|0').length - 1 !== 1) throw new Error('the wrap|0 ToInt32 narrowing census drifted')

const effect = effectRecords.find((item) => item.id === effectKey)
if (!effect || effect.func !== 'wobble' || effect.kind !== 'filter') throw new Error('wobble metadata drift')
if (effect.passes?.length !== 1 || effect.passes[0]?.program !== 'wobble') throw new Error('wobble pass interface drift')
if (effect.passes[0]?.inputs?.inputTex !== 'inputTex') throw new Error('wobble input interface drift')
if (Object.keys(effect.textures ?? {}).length !== 0 || effect.externalTexture !== null) throw new Error('wobble must have no textures')
if (effect.params?.speed?.default !== 5 || effect.params?.range?.default !== 0.5
    || effect.params?.wrap?.default !== 0 || effect.params?.wrap?.choices?.mirror !== 0
    || effect.params?.wrap?.choices?.repeat !== 1 || effect.params?.wrap?.choices?.clamp !== 2) {
  throw new Error('wobble default parameter drift')
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
      throw new Error(`wobble comparer did not preflight ${reason}`)
    }
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  expectReject(compareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape'), 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32'
      || !bytesOf(plusZero.toRgba8()).equals(bytesOf(minusZero.toRgba8()))) {
    throw new Error('wobble comparer missed signed zero')
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
    throw new Error('wobble comparer missed NaN payload')
  }
  const finalLane = compareExact(new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)])),
    expectedRecord(plusZero), 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch?.channel !== 'a'
      || finalLane.first_mismatch?.lane_or_byte_index !== 3) {
    throw new Error('wobble comparer missed final alpha lane')
  }
  const byteExpected = expectedRecord(plusZero)
  byteExpected.rgba8[3] ^= 1
  const byteOnly = compareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch?.channel !== 'a') {
    throw new Error('wobble comparer missed independent byte mismatch')
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
// exactly 1 in every lane of both patterns; wobble copies the sampled alpha
// straight through (`fragColor = sampled`), so every output alpha is exactly
// 0x3f800000/255.
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

// The tile case is a smaller destination over the SAME full-size input
// texture. wobble has NO tileOffset/fullResolution bindings -- there is no
// world-position carrier anywhere in the program -- so the tile-vs-full crop
// question is purely whether destination-local `v_texCoord` samples the same
// texels as the full route's corresponding pixels. Measured below: it does
// not, on either the live-clamp arm or the range-zero arm.
const cropRect = { crop_x: 3, crop_y: 2, tile_width: 5, tile_height: 6, full_width: 11, full_height: 9 }
const fullInput = makeInput(cropRect.full_width, cropRect.full_height, 'ramp')

const cases = [
  {
    name: 'range-zero-passthrough',
    coverage: ['the purpose-built varying discriminator: range = 0 pins offset to +-0',
      'sampleCoord degenerates to applyWrap(v_texCoord), the identity on the open unit interval for every wrap arm',
      'any varying materialization error (lane swap, y flip, f32 drift) lands exactly here',
      'landscape 16x9', 'speed 5 and time 0.75: the whole noise path still executes, its result multiplied by zero',
      'witnesses varying-lane-swapped and varying-y-unflipped; control case for every non-varying mutant'],
    width: 16, height: 9, time: 0.75, speed: 5, range: 0, wrap: 0, pattern: 'ramp',
  },
  {
    name: 'live-mirror-max-range',
    coverage: ['the wrap = 0 mirror arm with a real fold: offset x 0.0450 exceeds the 0.03125 half-texel margin',
      'range at the shipped maximum 5; speed 2; the control-group anchor',
      'contrast input pattern', 'landscape 16x9',
      'witnesses every ledger mutant (the two varying mutants, the offset sign, the wrap arms, the speed fold, the pcg divisor)'],
    width: 16, height: 9, time: 1.25, speed: 2, range: 5, wrap: 0, pattern: 'contrast',
  },
  {
    name: 'live-repeat-portrait',
    coverage: ['the wrap = 1 repeat arm with a real fold: offset y -0.0679 exceeds the 0.03125 half-texel margin',
      'range at the shipped maximum 5; speed 4, distinct from the mirror case',
      'portrait 9x16 destination (distinct uv grid, not a resized rerun)', 'ramp input pattern',
      'witnesses every ledger mutant'],
    width: 9, height: 16, time: 0.5, speed: 4, range: 5, wrap: 1, pattern: 'ramp',
  },
  {
    name: 'tile-crop-translation',
    coverage: ['the wrap = 2 clamp arm with real saturation: offset y -0.2273 crosses far beyond the 0.0833 margin',
      'the tile route: a 5x6 destination over the same full 11x9 input',
      'speed 5, time 0.375', 'the measured non-crop tile case (see tile_translation)',
      'witnesses the varying mutants, the offset sign, the speed fold, and the pcg divisor; control case for wrap-arm-swapped (clamp is the fall-through arm)'],
    width: cropRect.tile_width, height: cropRect.tile_height,
    time: 0.375, speed: 5, range: 5, wrap: 2,
    input: fullInput,
  },
]
if (cases.length !== 4) throw new Error(`wobble fixture census drift: ${cases.length}`)
if (new Set(cases.map((item) => item.name)).size !== cases.length) throw new Error('duplicate wobble case name')
for (const definition of cases) {
  for (const field of ['width', 'height']) {
    if (!Number.isInteger(definition[field]) || definition[field] <= 0) {
      throw new Error(`${definition.name}: ${field} must be a positive integer`)
    }
  }
  for (const field of ['time', 'speed', 'range', 'wrap']) {
    const value = definition[field]
    if (typeof value !== 'number' || !Number.isFinite(value) || f(value) !== value) {
      throw new Error(`${definition.name}: ${field} must be an exact f32 number`)
    }
  }
  if (definition.input === undefined && typeof patterns[definition.pattern] !== 'function') {
    throw new Error(`${definition.name}: unknown pattern`)
  }
}

// ---------------------------------------------------------------------------
// Rendering through the pinned public path
//
// The varying is bound IMPLICITLY: runPass computes context.uv per pixel and
// beginPixel aliases it into the runtime's v_texCoord slot; the canonical
// kernel copies the slot once per pixel. No code below ever touches a varying
// value, and no varying binding exists to set.
// ---------------------------------------------------------------------------

function uniformsFor(definition) {
  const uniforms = {
    time: f(definition.time),
    speed: f(definition.speed),
    range: f(definition.range),
    wrap: f(definition.wrap),
  }
  if (definition.omitWrap) delete uniforms.wrap
  return uniforms
}

function bindingOptions(definition) {
  return {
    width: definition.width,
    height: definition.height,
    // `time` at the options level and in `uniforms` are the same value: the
    // canonical binding builder resolves `...uniforms` first and then the
    // options-level `time` over it, so setting only one silently rebinds to
    // the default 0. Both are set, to the same exact f32.
    time: f(definition.time),
    seed: 1,
    uniforms: uniformsFor(definition),
    textures: { inputTex: definition.input ?? makeInput(definition.width, definition.height, definition.pattern) },
  }
}

function render(factory, definition) {
  const options = bindingOptions(definition)
  const input = options.textures.inputTex
  const inputBefore = words(input.data).slice()
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
    if (value === undefined && name === 'wrap' && definition.omitWrap) {
      // The one-axis unbound-wrap control: the binding is deliberately absent,
      // which the authority resolves as `undefined | 0 === 0` (mirror).
      out[name] = { abi, unbound: true, resolved_toint32_mode: 0 }
      continue
    }
    if (typeof value !== 'number' || f(value) !== value) throw new Error(`${name}: not an exact f32 scalar`)
    const record = { abi, f32_value: value, f32_word_le: f32Bits(value) }
    if (name === 'wrap') record.toint32_mode = value | 0
    out[name] = record
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
    route: definition.input ? 'tile' : 'full',
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
// budgeted (varying-design.md section 7, the normalMap section 11/12
// discipline). The two varying mutants are the strongest discriminators and
// are the ONLY ones that move a lane on range-zero-passthrough -- measured,
// not assumed. The remaining four pin the non-varying path (the offset sign,
// the wrap arms, the speed fold into the noise coordinates, and the hash31 /
// pcg chain). Their witness sets overlap by construction; the per-case table,
// not disjointness, attributes a divergence.
// ---------------------------------------------------------------------------

const sampleCoordLine = 'var sampleCoord = new $runtime.PooledFloat32Array([v_texCoord[0] + offset[0], v_texCoord[1] + offset[1]]);'
const offsetLine = 'var offset = new $runtime.PooledFloat32Array([(xRandom - 0.5) * offsetScale, (yRandom - 0.5) * offsetScale]);'
const zFoldLine = 'var z = cos(angle) * spd + seed[0] + spd * 0.31700000166893005;'
const hashReturnLine = 'return cpu_float(pcg(seed)[0]) / 4294967296;'

const mutantSpecs = [
  {
    name: 'varying-lane-swapped',
    target: 'the single varying read: `v_texCoord[0] + offset[0], v_texCoord[1] + offset[1]` becomes lane-swapped `v_texCoord[1] + offset[0], v_texCoord[0] + offset[1]`',
    contract: 'the LANE ORDER of the v_texCoord == context.uv aliasing (glsl-runtime.js writes [0] from uv[0] and [1] from uv[1]); a port that loads the lanes crossed fails here on every case, maximally on the pass-through case',
    anchor: sampleCoordLine,
    replacement: 'var sampleCoord = new $runtime.PooledFloat32Array([v_texCoord[1] + offset[0], v_texCoord[0] + offset[1]]);',
    reaching: 'every case: the read executes unconditionally in main',
    expected: {
      'range-zero-passthrough': true,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'varying-y-unflipped',
    target: 'the y orientation of the alias: `v_texCoord[1]` is read as `1 - v_texCoord[1]`, i.e. the coordinate treated as top-down',
    contract: 'the BOTTOM-UP orientation of context.uv (pass-runner computes uv[1] from height - y - 0.5); a port that forgets the y flip fails everywhere, and on the pass-through case the flip difference is maximal',
    anchor: sampleCoordLine,
    replacement: 'var sampleCoord = new $runtime.PooledFloat32Array([v_texCoord[0] + offset[0], 1 - v_texCoord[1] + offset[1]]);',
    reaching: 'every case: the read executes unconditionally in main',
    expected: {
      'range-zero-passthrough': true,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'offset-sign-flipped',
    target: 'the warp offset direction: `(xRandom - 0.5) * offsetScale` becomes `(0.5 - xRandom) * offsetScale` on both lanes',
    contract: 'the sign of the uniform-per-frame offset; pins the warp path independently of the varying. At range = 0 the offset is +-0 and the flip is unobservable -- the measured control row',
    anchor: offsetLine,
    replacement: 'var offset = new $runtime.PooledFloat32Array([(0.5 - xRandom) * offsetScale, (0.5 - yRandom) * offsetScale]);',
    reaching: 'every case with range > 0; algebraically dead at range = 0',
    expected: {
      'range-zero-passthrough': false,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'wrap-arm-swapped',
    target: 'the two wrap conditions in applyWrap: the wrap == 0 (mirror) and wrap == 1 (repeat) arms are exchanged (an ordered three-anchor chain through a unique temp identifier)',
    contract: 'abs(mod(uv + 1, 2) - 1) versus fract(uv): identical on the open unit interval and different outside it; the wrap == 2 clamp case is the fall-through arm and cannot see the swap; the range-zero case never leaves the interval',
    anchors: [
      ['if (mode == 0) {', 'if (__wobble_wrap_swap) {'],
      ['if (mode == 1) {', 'if (mode == 0) {'],
      ['if (__wobble_wrap_swap) {', 'if (mode == 1) {'],
    ],
    reaching: 'cases where the offset pushes some sampleCoord outside [0, 1) AND the selected arm is 0 or 1',
    expected: {
      'range-zero-passthrough': false,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': false,
    },
  },
  {
    name: 'speed-fold-phase-shifted',
    target: 'the speed folding into the noise coordinates: `spd * 0.317...` in simplexRandom\'s z becomes `spd * 0.817...` (a half-lattice-cell shift)',
    contract: 'the JS comment\'s contract that speed is folded into the noise input so the output varies with speed even at time = 0; a near-ULP shift is absorbed by nearest sampling (see uv_subtexel_invariance) so the shift is a half noise cell',
    anchor: zFoldLine,
    replacement: 'var z = cos(angle) * spd + seed[0] + spd * 0.81700000166893005;',
    reaching: 'every case with range > 0; the shifted noise is still multiplied by offsetScale = 0 at range = 0',
    expected: {
      'range-zero-passthrough': false,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': true,
    },
  },
  {
    name: 'hash31-pcg-divisor-halved',
    target: 'hash31\'s pcg-output normalizer: the divisor 4294967296 (2^32) is halved to 2147483648 (the cellrefract prng-pcg-constant-perturbed shape)',
    contract: 'the noise3d lattice chain (pcg3d then / 2^32) that feeds every simplexRandom value and therefore both offset lanes; the design\'s "noise3d-lattice perturbation" mutant',
    anchor: hashReturnLine,
    replacement: 'return cpu_float(pcg(seed)[0]) / 2147483648;',
    reaching: 'every case with range > 0; the perturbed noise is still multiplied by offsetScale = 0 at range = 0',
    expected: {
      'range-zero-passthrough': false,
      'live-mirror-max-range': true,
      'live-repeat-portrait': true,
      'tile-crop-translation': true,
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
    classification: 'rendered canonical-JS one-anchor/one-replacement mutant (the wrap swap uses an ordered three-anchor chain through a unique temp identifier)',
    ...mutantIdentity(spec, compiled),
    witness_cases: results.filter((result) => result.differs).map((result) => result.case),
    control_cases: results.filter((result) => !result.differs).map((result) => result.case),
    results,
  }
})

// ---------------------------------------------------------------------------
// The sub-texel uv perturbation: measured invariant, dropped from the ledger.
//
// nearest sampling (sampleNearestBottomLeft) reads only the texel that
// sampleCoord lands in, so a 1e-7 perturbation of both uv lanes moves no
// sample by a texel width (the smallest is 1/16 here). The cellrefract
// prng_near_ulp_invariance lesson, re-measured for wobble's own sampler path.
// The uv materialization is nonetheless exactly pinned, by the two varying
// ledger mutants.
// ---------------------------------------------------------------------------

const nearUlpSpec = {
  name: 'uv-subtexel-perturbed',
  anchor: sampleCoordLine,
  replacement: 'var sampleCoord = new $runtime.PooledFloat32Array([v_texCoord[0] + offset[0] + 9.999999717180685e-8, v_texCoord[1] + offset[1] + 9.999999717180685e-8]);',
}
const nearUlpCompiled = compileMutant(nearUlpSpec)
const nearUlpRows = measureAcrossCases(nearUlpCompiled.factory, nearUlpSpec.name)
if (nearUlpRows.some((row) => row.differs)) {
  throw new Error('the sub-texel uv perturbation diverged; the nearest-sampling quantization argument is wrong '
    + 'and the mutant belongs in the ledger')
}
const uvSubtexelInvariance = {
  status: 'measured-invariant',
  rendered_mutant: { name: nearUlpSpec.name, ...mutantIdentity(nearUlpSpec, nearUlpCompiled), rows: nearUlpRows },
  rendered_divergences: nearUlpRows.reduce((total, row) => total + row.changed_lane_count, 0),
  reason: 'texture() is nearest-sampling (sampleNearestBottomLeft): the output depends only on which texel '
    + 'sampleCoord lands in. A 1e-7 perturbation of both uv lanes moves samples by far less than the smallest '
    + 'texel width in this fixture set (1/16), so every image is bit-identical. The uv materialization is pinned '
    + 'instead by varying-lane-swapped and varying-y-unflipped, whose perturbations are texel-scale by construction.',
}

// ---------------------------------------------------------------------------
// Dead-code census: there is NO non-reaching control for wobble.
//
// cellrefract's control mutated a branch the normalizer strips at the frozen
// define. wobble has no defines and no dead branch: all six functions are
// called unconditionally from main (varying-design.md section 1.3), and
// applyWrap's three arms are runtime-selected, each live in this case set.
// The per-case control rows of the ledger (range-zero for the four non-varying
// mutants) are ALGEBRAIC cancellations -- the code executes, its result is
// multiplied by offsetScale = 0 -- and are recorded as exactly that, never as
// skip/strip agreements.
// ---------------------------------------------------------------------------

const deadCodeCensus = {
  status: 'no-dead-code-exists',
  design_reference: 'varying-design.md section 1.3 (all six functions reachable) and section 7',
  claim: 'wobble has no non-executing construct at any binding: main calls simplexRandom (twice), noise3d, '
    + 'hash31, pcg and applyWrap unconditionally, and each applyWrap arm is selected by the wrap binding '
    + '(mirror/repeat/clamp all appear in this case set). A cellrefract-style branch-control mutant cannot '
    + 'exist here. The range-zero control rows in the mutation ledger are algebraic cancellations (the noise '
    + 'and warp code EXECUTES and its result is multiplied by zero), not runtime-skip versus normalizer-strip '
    + 'agreements, and the oracle never presents them as such.',
}

// ---------------------------------------------------------------------------
// Tile-vs-full translation: measured NON-identity on both arms, with the
// mechanism attributed by instrumented sampleCoord probes.
// ---------------------------------------------------------------------------

const tileCaseName = 'tile-crop-translation'
const tileDefinition = cases.find((item) => item.name === tileCaseName)
const fullRouteDefinition = {
  ...tileDefinition,
  name: `${tileCaseName}/full-route`,
  width: cropRect.full_width,
  height: cropRect.full_height,
}

// Accepts a Surface or an expected record; both carry the same arrays.
function surfaceViews(surface) {
  if (surface?.data instanceof Float32Array) {
    return { wordView: words(surface.data), byteView: surface.toRgba8() }
  }
  if (surface?.float_words instanceof Uint32Array && surface?.rgba8 instanceof Uint8Array) {
    return { wordView: surface.float_words, byteView: surface.rgba8 }
  }
  throw new TypeError('a Surface or an expected record is required')
}

function cropMismatches(tileOutput, fullOutput) {
  let wordMismatches = 0
  let byteMismatches = 0
  let firstMismatch = null
  const tileWords = surfaceViews(tileOutput).wordView
  const fullWords = surfaceViews(fullOutput).wordView
  const tileBytes = surfaceViews(tileOutput).byteView
  const fullBytes = surfaceViews(fullOutput).byteView
  for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
    for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
      for (let channel = 0; channel < 4; channel += 1) {
        const tileIndex = ((ty * cropRect.tile_width) + tx) * 4 + channel
        const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4 + channel
        if (tileWords[tileIndex] !== fullWords[fullIndex]) {
          wordMismatches += 1
          firstMismatch ??= {
            top_down_xy: [tx, ty], channel: channels[channel],
            tile_word: u32Hex(tileWords[tileIndex]), full_word: u32Hex(fullWords[fullIndex]),
          }
        }
        if (tileBytes[tileIndex] !== fullBytes[fullIndex]) byteMismatches += 1
      }
    }
  }
  return { wordMismatches, byteMismatches, firstMismatch }
}

// The live-clamp arm (the stored tile parity case).
const fullRoute = render(canonicalFactory, fullRouteDefinition)
const tileOutput = canonicalExpected.get(tileCaseName)
const liveCrop = cropMismatches(tileOutput, fullRoute.output)

// The range-zero arm, probed separately (varying-design.md section 7: the one
// arm where an identity was plausibly sound -- it is not).
const zeroTileDefinition = { ...tileDefinition, name: `${tileCaseName}/range-zero-tile`, time: 0.75, speed: 5, range: 0, wrap: 0 }
const zeroFullDefinition = { ...fullRouteDefinition, name: `${tileCaseName}/range-zero-full`, time: 0.75, speed: 5, range: 0, wrap: 0 }
const zeroTileRoute = render(canonicalFactory, zeroTileDefinition)
const zeroFullRoute = render(canonicalFactory, zeroFullDefinition)
const zeroCrop = cropMismatches(zeroTileRoute.output, zeroFullRoute.output)

const totalCropLanes = cropRect.tile_width * cropRect.tile_height * 4
for (const [arm, crop] of [['live-clamp', liveCrop], ['range-zero', zeroCrop]]) {
  if (crop.wordMismatches === 0) {
    throw new Error(`the ${arm} tile route IS an exact crop of the full route; the measured non-identity record `
      + 'must be re-derived')
  }
  if (crop.wordMismatches === totalCropLanes) {
    throw new Error(`the ${arm} tile route shares no lane with the crop of the full route; the routes are unrelated`)
  }
}

// Mechanism probes: publish the post-wrap sampleCoord (the coordinate that
// feeds texture()) on both routes, for both arms. The equal-lane counts are
// recorded as measured -- f32 coincidences (e.g. (2 + 0.5) / 5 = 0.5 =
// (3 + 2 + 0.5) / 11 on the x lane) and, on the live arm, clamp saturation
// collapsing distinct folded coordinates to the same 0/1 word.
const publishAnchor = '(fragColor[0] = sampled[0], fragColor[1] = sampled[1], fragColor[2] = sampled[2], fragColor[3] = sampled[3], fragColor);'
const uvProbeSpec = {
  name: 'samplecoord-probe',
  anchors: [[publishAnchor, '(fragColor[0] = sampleCoord[0], fragColor[1] = sampleCoord[1], fragColor[2] = 0, fragColor[3] = 1, fragColor);']],
}
const uvProbe = compileMutant(uvProbeSpec)
function sampleCoordWitness(tileDef, fullDef) {
  const tileProbe = render(uvProbe.factory, tileDef).output
  const fullProbe = render(uvProbe.factory, fullDef).output
  const tileWordsProbe = words(tileProbe.data)
  const fullWordsProbe = words(fullProbe.data)
  const tileSha = sha256(bytesOf(tileProbe.data))
  const fullSha = sha256(bytesOf(fullProbe.data))
  let equalXLanes = 0
  let equalYLanes = 0
  const compared = cropRect.tile_width * cropRect.tile_height
  for (let ty = 0; ty < cropRect.tile_height; ty += 1) {
    for (let tx = 0; tx < cropRect.tile_width; tx += 1) {
      const tileIndex = ((ty * cropRect.tile_width) + tx) * 4
      const fullIndex = (((cropRect.crop_y + ty) * cropRect.full_width) + (cropRect.crop_x + tx)) * 4
      if (tileWordsProbe[tileIndex] === fullWordsProbe[fullIndex]) equalXLanes += 1
      if (tileWordsProbe[tileIndex + 1] === fullWordsProbe[fullIndex + 1]) equalYLanes += 1
    }
  }
  return {
    classification: 'instrumented canonical-JS probe factory; NOT a parity array and never compared to a rendered shade',
    probe: { name: uvProbeSpec.name, ...mutantIdentity(uvProbeSpec, uvProbe) },
    rule: 'fragColor publishes the post-wrap sampleCoord on both routes; the counts of lanes whose f32 words COINCIDE are recorded as measured',
    compared_pairs_per_lane: compared,
    equal_x_lanes: equalXLanes,
    equal_y_lanes: equalYLanes,
    tile_words_le: Array.from(tileWordsProbe, u32Hex),
    tile_sha256: tileSha,
    full_route_words_le: Array.from(fullWordsProbe, u32Hex),
    full_route_sha256: fullSha,
  }
}
const liveUvWitness = sampleCoordWitness(tileDefinition, fullRouteDefinition)
const zeroUvWitness = sampleCoordWitness(zeroTileDefinition, zeroFullDefinition)
for (const [arm, witness] of [['live-clamp', liveUvWitness], ['range-zero', zeroUvWitness]]) {
  if (witness.equal_x_lanes + witness.equal_y_lanes === witness.compared_pairs_per_lane * 2) {
    throw new Error(`the ${arm} sampleCoord probe found every lane equal; the non-identity mechanism must be re-derived`)
  }
}

const tileTranslation = {
  case: tileCaseName,
  rect: cropRect,
  design_expectation: 'varying-design.md section 7: probe before asserting. The Shapes crop identity was NOT '
    + 'assumed; the range = 0 arm was named the one plausibly-sound arm and probed separately.',
  measured: 'the tile output is NOT a crop of the full output, on either arm',
  live_clamp_arm: {
    tile_bindings: 'speed 5, range 5, wrap 2, time 0.375',
    word_mismatches: liveCrop.wordMismatches,
    byte_mismatches: liveCrop.byteMismatches,
    is_exact_crop: false,
    first_mismatch: liveCrop.firstMismatch,
  },
  range_zero_arm: {
    tile_bindings: 'speed 5, range 0, wrap 0, time 0.75 (the discriminator bindings on the same rectangle)',
    word_mismatches: zeroCrop.wordMismatches,
    byte_mismatches: zeroCrop.byteMismatches,
    is_exact_crop: false,
    first_mismatch: zeroCrop.firstMismatch,
    full_route_expected: surfaceRecord(zeroFullRoute.output),
    tile_expected: surfaceRecord(zeroTileRoute.output),
  },
  full_route_expected: surfaceRecord(fullRoute.output),
  why: 'wobble has NO tileOffset or fullResolution bindings -- unlike cellRefract or the Shapes programs, there '
    + 'is no world-position carrier anywhere in the shader. The only spatial input is v_texCoord, which the '
    + 'JavaScript materializes as context.uv: the pixel center of the DESTINATION grid. A 5x6 tile over the '
    + 'same 11x9 input therefore samples the input at ((tx + 0.5) / 5, (6 - ty - 0.5) / 6) while the full '
    + 'route\'s corresponding pixel samples at ((3 + tx + 0.5) / 11, (9 - (2 + ty) - 0.5) / 9): different '
    + 'coordinates, different texels, no offset rule exists that could align them. The sampleCoord probes '
    + 'below attribute the difference exactly there, on both arms.',
  live_clamp_samplecoord_witness: liveUvWitness,
  range_zero_samplecoord_witness: zeroUvWitness,
  consequence: 'The tile route is pinned as its own parity case and both full-route surfaces are stored beside '
    + 'it; a native port must reproduce all of them. No crop identity may be asserted for this program on any '
    + 'arm, and the native test must not compare the tile against a crop of either full-route surface.',
}

// ---------------------------------------------------------------------------
// One-axis control group on live-mirror-max-range (the anchor)
// ---------------------------------------------------------------------------

const anchorName = 'live-mirror-max-range'
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
    f32_sha256: renderCases[1].output_expected.f32_sha256,
    rgba8_sha256: renderCases[1].output_expected.rgba8_sha256,
  },
  controls: [
    controlRow('external-pass-extreme', { externalTime: 2147483648, externalSeed: -2147483648 },
      'identical', 'external runPass time/seed words (0x4f000000, 0xcf000000)',
      'the factory reads $bindings only; runPass context time/seed are never consumed'),
    controlRow('wrap-binding-unbound', { omitWrap: true, wrap: 0 },
      'identical', 'the wrap runtime binding: bound 0 versus absent entirely (undefined)',
      'THE ToInt32-narrowing axis. `var wrap = $bindings["wrap"]` resolves to undefined when the binding is '
        + 'absent, and `undefined | 0 === 0` selects the mirror arm exactly as the bound 0 does. The port '
        + 'always binds wrap; this control records the narrowing semantics of the authority.'),
    controlRow('wrap-binding-fractional-0.5', { wrap: 0.5 },
      'identical', 'bound wrap 0 (0x00000000) -> 0.5 (0x3f000000), ToInt32(0.5) === 0',
      'the narrowing is TRUNCATION toward zero, not rounding: 0.5 would round to 1 and select repeat, which '
        + 'measurably differs (see wrap-binding-fractional-1.5). The GLSL is `int mode = int(wrap);`'),
    controlRow('wrap-binding-fractional-1.5', { wrap: 1.5 },
      'differs', 'bound wrap 0 -> 1.5, ToInt32(1.5) === 1 selects repeat',
      'the live half of the same axis: truncation of 1.5 selects the repeat arm and moves the folded pixels'),
    controlRow('bound-time-live', { time: 2.5 },
      'differs', 'bound time 0x3fa00000 -> 0x40200000',
      'the time axis: the noise phase t = time + speed * 0.1 moves both simplexRandom values and therefore '
        + 'the offset; inert only at range = 0 (see range_zero_inertness_census)'),
  ],
}
{
  const external = controlGroup.controls[0]
  const unbound = controlGroup.controls[1]
  const half = controlGroup.controls[2]
  if (external.observed !== 'identical') {
    throw new Error('external runPass time/seed changed the output; the shader-owned uniforms do not dominate')
  }
  if (unbound.observed !== 'identical' || half.observed !== 'identical') {
    throw new Error('the wrap ToInt32-narrowing axis failed: an unbound or truncated wrap must behave as bound 0')
  }
}
for (const control of controlGroup.controls) {
  if (!control.pass) throw new Error(`control ${control.name} expected ${control.expectation} but observed ${control.observed}`)
}

// ---------------------------------------------------------------------------
// Binding liveness census on the anchor
// ---------------------------------------------------------------------------

const liveBindingProbes = [
  { binding: 'inputTex', overrides: { pattern: 'ramp' },
    note: 'the anchor renders the contrast pattern; switching the input texture to ramp moves the sampled texels' },
  { binding: 'time', overrides: { time: 2.5 }, note: 'the noise phase t = time + speed * 0.1' },
  { binding: 'speed', overrides: { speed: 3 }, note: 'the noise coordinates AND offsetScale = range * (0.01 + speed * 0.02)' },
  { binding: 'range', overrides: { range: 1 }, note: 'offsetScale scales both offset lanes' },
  { binding: 'wrap', overrides: { wrap: 1 }, note: 'mirror -> repeat on the x-folded pixels' },
]
const bindingLivenessCensus = {
  probe_case: anchorName,
  rule: 'every binding recorded live must move the anchor output under at least one extreme probe, or the census is vacuous',
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
// The range-zero inertness census: time, speed, and wrap are inert with
// offsetScale == 0, with witnesses; range is the discriminator binding.
// ---------------------------------------------------------------------------

const zeroCaseName = 'range-zero-passthrough'
const zeroAnchor = cases.find((item) => item.name === zeroCaseName)
const zeroBaselineExpected = canonicalExpected.get(zeroCaseName)
const zeroInertProbes = [
  { binding: 'time', overrides: { time: 99.5 }, note: 'the noise phase moves, the offset stays (noise - 0.5) * 0 = +-0' },
  { binding: 'speed', overrides: { speed: 0 }, note: 'spd, the noise coordinates, and offsetScale all move; the product stays zero' },
  { binding: 'wrap', overrides: { wrap: 2 }, note: 'all three arms are the identity on the open unit interval, and no coordinate leaves it' },
]
const rangeZeroInertnessCensus = {
  probe_case: zeroCaseName,
  rule: 'at range = 0, r = max(range, 0) = 0 makes offsetScale = 0 and offset = (+-0, +-0), so sampleCoord '
    + 'degenerates to applyWrap(v_texCoord) -- the pure varying pass-through. Every scalar binding except '
    + 'inputTex and range itself is output-inert, measured here with extreme probes. range is THE '
    + 'discriminator binding: 0 -> 4 wakes the warp path.',
  inert: zeroInertProbes.map(({ binding, overrides }) => {
    const definition = { ...zeroAnchor, ...overrides, name: `${zeroCaseName}/inert-${binding}` }
    const output = render(canonicalFactory, definition).output
    const comparison = compareExact(output, zeroBaselineExpected, `zero-inertness/${binding}`)
    return {
      binding,
      differs_from_baseline: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
    }
  }),
  range_discriminator: (() => {
    const definition = { ...zeroAnchor, range: 4, name: `${zeroCaseName}/range-4` }
    const output = render(canonicalFactory, definition).output
    const comparison = compareExact(output, zeroBaselineExpected, 'zero-inertness/range')
    return {
      binding: 'range',
      differs_from_baseline: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
    }
  })(),
}
for (const probe of rangeZeroInertnessCensus.inert) {
  if (probe.differs_from_baseline) {
    throw new Error(`${probe.binding} is recorded inert on the range-zero case but a probe changed the output`)
  }
}
if (!rangeZeroInertnessCensus.range_discriminator.differs_from_baseline) {
  throw new Error('range does not wake the warp path from the range-zero case; the discriminator premise is wrong')
}

// ---------------------------------------------------------------------------
// The defaults inertness census: at the SHIPPED DEFAULTS on a 16x9, every
// scalar binding is output-inert. Measured, with the structural margin bound.
// ---------------------------------------------------------------------------

const defaultsDefinition = { name: 'defaults', width: 16, height: 9, time: 1.0, speed: 5, range: 0.5, wrap: 0, pattern: 'ramp' }
const defaultsOutput = render(canonicalFactory, defaultsDefinition)
const defaultsExpected = expectedRecord(defaultsOutput.output)
const defaultsOffsetProbe = (() => {
  const offsetProbeSpec = {
    name: 'offset-probe',
    anchors: [[publishAnchor, '(fragColor[0] = offset[0], fragColor[1] = offset[1], fragColor[2] = offsetScale, fragColor[3] = 1, fragColor);']],
  }
  return compileMutant(offsetProbeSpec)
})()
const defaultsOffsets = render(defaultsOffsetProbe.factory, defaultsDefinition).output
const defaultsInertProbes = [
  { binding: 'time', overrides: [{ time: 1.7 }, { time: 4.25 }] },
  { binding: 'speed', overrides: [{ speed: 0 }, { speed: 2 }] },
  { binding: 'range', overrides: [{ range: 0 }, { range: 5 }] },
  { binding: 'wrap', overrides: [{ wrap: 1 }, { wrap: 2 }] },
]
const defaultsInertnessCensus = {
  probe_case: 'defaults (speed 5, range 0.5, wrap 0, time 1.0, 16x9)',
  rule: 'the shipped defaults on a 16x9 destination leave EVERY scalar binding output-inert: the maximum '
    + 'possible offset magnitude is 0.5 * range * (0.01 + 0.02 * speed) = 0.5 * 0.5 * 0.11 = 0.0275, below '
    + 'the 0.5 / 16 = 0.03125 half-texel margin, so no sample crosses a texel boundary under ANY defaults '
    + 'binding pair. The effect becomes output-active only at larger range/speed (the anchor) or on finer '
    + 'grids. This is a measured parity fact, not a defect report: a port that differs here differs from '
    + 'an oracle that is invariant.',
  offset_f32_words_le: Array.from(words(defaultsOffsets.data).slice(0, 3), u32Hex),
  baseline_f32_sha256: sha256(bytesOf(defaultsOutput.output.data)),
  baseline_rgba8_sha256: sha256(bytesOf(defaultsOutput.output.toRgba8())),
  probes: defaultsInertProbes.map(({ binding, overrides }) => ({
    binding,
    probes: overrides.map((override) => {
      const definition = { ...defaultsDefinition, ...override, name: `defaults/${binding}-${JSON.stringify(override)}` }
      const output = render(canonicalFactory, definition).output
      const comparison = compareExact(output, defaultsExpected, `defaults-inertness/${binding}`)
      return {
        override,
        differs_from_baseline: !comparison.exact,
        changed_lane_count: comparison.changed_lane_count ?? 0,
        f32_sha256: sha256(bytesOf(output.data)),
      }
    }),
  })),
}
for (const entry of defaultsInertnessCensus.probes) {
  for (const probe of entry.probes) {
    if (probe.differs_from_baseline) {
      throw new Error(`at the shipped defaults, ${entry.binding} moved the output; the defaults census is wrong`)
    }
  }
}

// ---------------------------------------------------------------------------
// The wrap-arm census: offsets, half-texel margins, and the measured liveness
// of switching the wrap binding on every case (both alternate arms), with the
// mirror<->clamp edge-texel alias recorded where it occurs.
// ---------------------------------------------------------------------------

const wrapArmCensus = {
  rule: 'a wrap switch can only change the output where some pixel\'s sampleCoord leaves [0, 1): on the open '
    + 'unit interval all three arms are the identity (mirror\'s mod arithmetic cancels exactly, and nearest '
    + 'sampling absorbs the sub-ULP arm differences elsewhere). The offset is uniform per frame, so crossing '
    + 'happens on lane L exactly when |offset_L| exceeds the half-texel margin 0.5 / size_L. CAVEAT, measured '
    + 'on the mirror row: a SHALLOW crossing (within one texel of the edge) makes mirror and clamp read the '
    + 'SAME edge texel (mirror reflects back into it, clamp pins to it), so that pair can agree despite the '
    + 'crossing. Each row records both alternate arms as measured.',
  rows: cases.map((definition) => {
    const offsets = render(defaultsOffsetProbe.factory, definition).output
    const offsetWords = Array.from(words(offsets.data).slice(0, 2), u32Hex)
    const margins = [0.5 / definition.width, 0.5 / definition.height]
    const offsetValues = [offsets.data[0], offsets.data[1]]
    const crosses = [Math.abs(offsetValues[0]) > margins[0], Math.abs(offsetValues[1]) > margins[1]]
    const alternates = [1, 2].map((delta) => {
      const wrap = (definition.wrap + delta) % 3
      const probeDefinition = { ...definition, wrap, name: `${definition.name}/wrap-${wrap}` }
      const output = render(canonicalFactory, probeDefinition).output
      const comparison = compareExact(output, canonicalExpected.get(definition.name), `wrap-census/${definition.name}/${wrap}`)
      return {
        wrap_binding: wrap,
        arm: wrap === 0 ? 'mirror' : wrap === 1 ? 'repeat' : 'clamp',
        differs_from_case: !comparison.exact,
        changed_lane_count: comparison.changed_lane_count ?? 0,
        f32_sha256: sha256(bytesOf(output.data)),
      }
    })
    return {
      case: definition.name,
      wrap_binding: definition.wrap,
      arm: definition.wrap === 0 ? 'mirror' : definition.wrap === 1 ? 'repeat' : 'clamp',
      offset_f32_words_le: offsetWords,
      half_texel_margins: margins,
      lane_crosses_boundary: crosses,
      any_crossing: crosses[0] || crosses[1],
      alternates,
    }
  }),
}
{
  const byCase = new Map(wrapArmCensus.rows.map((row) => [row.case, row]))
  const zero = byCase.get(zeroCaseName)
  if (zero.any_crossing || zero.alternates.some((alt) => alt.differs_from_case)) {
    throw new Error('the range-zero case must have zero offset and invariant wrap switches')
  }
  const mirror = byCase.get(anchorName)
  if (!mirror.lane_crosses_boundary[0] || mirror.lane_crosses_boundary[1]) {
    throw new Error('the mirror anchor crossing census drifted; re-freeze from measurement')
  }
  // The measured alias: mirror x-crossing is shallow, so mirror vs clamp agree.
  const mirrorToClamp = mirror.alternates.find((alt) => alt.wrap_binding === 2)
  const mirrorToRepeat = mirror.alternates.find((alt) => alt.wrap_binding === 1)
  if (mirrorToClamp.differs_from_case || !mirrorToRepeat.differs_from_case) {
    throw new Error('the mirror anchor wrap-switch census drifted; re-freeze from measurement')
  }
  const repeat = byCase.get('live-repeat-portrait')
  if (repeat.lane_crosses_boundary[0] || !repeat.lane_crosses_boundary[1]
      || repeat.alternates.some((alt) => !alt.differs_from_case)) {
    throw new Error('the repeat case must cross on y only and differ under both alternates')
  }
  const tile = byCase.get(tileCaseName)
  if (tile.lane_crosses_boundary[0] || !tile.lane_crosses_boundary[1]
      || tile.alternates.some((alt) => !alt.differs_from_case)) {
    throw new Error('the tile case must cross deeply on y and differ under both alternates')
  }
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
const wrapRowByCase = new Map(wrapArmCensus.rows.map((row) => [row.case, row]))
function crossingKind(definition) {
  const row = wrapRowByCase.get(definition.name)
  if (!row.any_crossing) return 'no_crossing_wrap_identity'
  const [x, y] = row.lane_crosses_boundary
  return x && y ? 'both_lanes_cross' : x ? 'x_lane_crosses' : 'y_lane_crosses'
}
const coverageAxes = {
  wrap_arm: bucketBy((definition) => (definition.wrap === 0 ? 'mirror_wrap_0' : definition.wrap === 1 ? 'repeat_wrap_1' : 'clamp_wrap_2')),
  wrap_crossing: bucketBy(crossingKind),
  route: bucketBy((definition) => (definition.input ? 'tile' : 'full')),
  input_pattern: bucketBy((definition) => definition.pattern ?? 'full-ramp'),
  destination_shape: bucketBy((definition) => `${definition.width}x${definition.height}`),
  range: bucketBy((definition) => (definition.range === 0 ? 'zero_pure_passthrough' : 'maximum_5')),
  speed: bucketBy((definition) => `speed_${definition.speed}`),
  varying_discriminator: bucketBy((definition) => (definition.range === 0 ? 'pure_pass_through' : 'offset_live')),
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
  wrap_binding_narrowing: '`wrap` is a float uniform in the GLSL (`uniform float wrap;`) narrowed at use '
    + '(`int mode = int(wrap);`, `wrap|0` in the JavaScript -- ToInt32 of the same Number), never an int32 '
    + 'binding. The control group pins the narrowing: an absent wrap behaves as mirror (undefined | 0 === 0) '
    + 'and 0.5 truncates to mirror while 1.5 truncates to repeat.',
  oracle_authority: `unmodified public ${factoryName} from an immutable noisemaker-for-cpu snapshot, `
    + 'executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates',
  varying_materialization: {
    glsl_declaration: varyingDeclarationGlsl,
    glsl_declaration_site: 'raw wobble.glsl line 14, the only file-scope varying; one read, zero writes, in main',
    javascript_slot_declaration: varyingDeclarationJs,
    javascript_slot_kind: 'factory-scope Float32Array, NOT pooled (the normalMap section 15 pool lesson); zero-initialised',
    per_pixel_copy: varyingCopyJs,
    runtime_alias: 'GlslCpuRuntime.beginPixel hardcodes `this.varyings.v_texCoord[0] = uv[0]` and `[1] = uv[1]` '
      + '-- v_texCoord IS context.uv, with no vertex stage and no interpolation anywhere in the CPU reference',
    numeric_contract: 'per-lane f32, single narrowing, double product: F32((x + 0.5) * (1 / width)) and '
      + 'F32((height - y - 0.5) * (1 / height)) (pass-runner.js); all downstream copies are f32 to f32',
    read_expression: varyingReadExpression,
    identifier_occurrences: varyingOccurrenceCensus,
    runtime_slot_line: runtimeVaryingSlotJs,
    runtime_alias_lines: runtimeVaryingAliasJs,
    pass_runner_uv_lines: passRunnerUvJs,
    bound_by: 'implicit: the pass runner computes context.uv and beginPixel aliases it; no varying binding '
      + 'exists and none is ever set by the oracle',
    discriminators: ['varying-lane-swapped', 'varying-y-unflipped'],
    discriminator_case: zeroCaseName,
  },
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays; never reconstructed from expected words',
    tolerance: 'none',
    comparison_order: 'dimensions, exact expected/actual lane count, exact expected/actual byte count, every Float32 word, every independent RGBA8 byte',
    coordinates: 'all stored rows and first mismatches use top-down storage order and top-down x/y',
    input_textures: 'stored in full as raw little-endian uint32 lane arrays; every input lane is a small '
      + 'dyadic rational and therefore exact in binary32 and binary64',
    alpha: 'the program copies the sampled alpha through (`fragColor = sampled`); every input alpha is exactly '
      + '1, so every output alpha float word is exactly 0x3f800000 and every RGBA8 alpha byte is exactly 255',
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
      preprocessor_defines: [],
    },
    canonical_factory: {
      name: canonicalFactory.name,
      bytes: Buffer.byteLength(canonicalText),
      sha256: sha256(canonicalText),
      source_slice_bytes: Buffer.byteLength(canonicalSlice),
      source_slice_sha256: sha256(canonicalSlice),
    },
    factory_text_method_cross_validation: {
      factory: crossValidationFactoryKey,
      sha256: crossValidationFactorySha256,
      claim: 'the same snapshot and the same Function.prototype.toString method must reproduce cellrefract186\'s '
        + 'frozen factory-text digest, or the pinning method -- not just this package -- is untrustworthy',
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
      params: effect.params,
      textures: effect.textures,
      external_texture: effect.externalTexture,
    },
  },
  comparer_self_tests: comparerSelfTests(),
  coverage_axes: coverageAxes,
  render_cases: renderCases,
  tile_translation: tileTranslation,
  control_group: controlGroup,
  binding_liveness_census: bindingLivenessCensus,
  range_zero_inertness_census: rangeZeroInertnessCensus,
  defaults_inertness_census: defaultsInertnessCensus,
  wrap_arm_census: wrapArmCensus,
  mutation_ledger: mutationLedger,
  mutation_discrimination_contract: {
    per_case: true,
    rule: 'discrimination is frozen and validated PER CASE AND PER MUTANT. A per-mutant summary is not '
      + 'sufficient and is never accepted here. A case that flips is a stop condition.',
    witness_overlap_disclosure: 'The two varying mutants are competing probes of one materialization (lane '
      + 'order versus y orientation) and the four path mutants pin different functions (offset sign, wrap '
      + 'arms, speed fold, pcg chain); witness sets overlap BY CONSTRUCTION on the live cases. Overlap is '
      + 'disclosed, not engineered away: the per-case table, not disjointness, is what attributes a divergence. '
      + 'The load-bearing separation is structural and measured: on range-zero-passthrough ONLY the two varying '
      + 'mutants move a lane -- the pure discriminator the design asked for.',
    witness_sets: Object.fromEntries(mutationLedger.map((mutant) => [mutant.name, {
      witness_cases: [...mutant.witness_cases],
      control_cases: [...mutant.control_cases],
    }])),
    expected: Object.fromEntries(mutantSpecs.map((spec) => [spec.name, spec.expected])),
    excluded_from_ledger: {
      'uv-subtexel-perturbed': 'measured invariant on every case: nearest sampling absorbs a 1e-7 uv perturbation; see uv_subtexel_invariance',
    },
  },
  uv_subtexel_invariance: uvSubtexelInvariance,
  dead_code_census: deadCodeCensus,
  claim_boundaries: {
    varying_materialization: 'The oracle pins the v_texCoord == context.uv aliasing pixel-exactly through the '
      + 'pass-runner path; the port-side admission (v_texCoord lowering to context.uv) is validated against '
      + 'these arrays, not against any typed-slice state.',
    tile_translation: 'No crop identity holds for this program on ANY arm, including range = 0: the tile route '
      + 'is pinned as its own parity case with both full-route surfaces stored beside it. The mechanism is '
      + 'pure destination-local v_texCoord (wobble has no tileOffset/fullResolution bindings at all).',
    range_zero_discriminator: 'range = 0 is the pure varying pass-through; the two varying mutants are the only '
      + 'ledger mutants that move a lane there, and every other mutant is a measured control row on that case.',
    defaults_inert: 'At the shipped defaults on a 16x9 every scalar binding is output-inert (the offset is '
      + 'structurally below the half-texel margin). Recorded as a parity fact with the bound, not as a defect.',
    wrap_narrowing: 'wrap is a float binding narrowed by ToInt32 at use; an absent wrap is mirror and 0.5 is '
      + 'mirror while 1.5 is repeat (measured controls).',
    no_dead_code: 'wobble has no non-executing construct at any binding; the cellrefract-style branch control '
      + 'does not exist here and the range-zero control rows are algebraic cancellations, never presented as '
      + 'skip/strip agreements.',
    subtexel_invariance: 'Nearest sampling absorbs sub-texel uv perturbations; the uv materialization is pinned '
      + 'by the two varying mutants, not by sub-ULP probes.',
    synthetic_probes: 'The defaults, wrap-switch, inertness, and liveness probes bind values outside the frozen '
      + 'case set (and outside the shipped defaults, for the extremes). They cover the ABI and prove channels '
      + 'real; they are never parity cases and never evidence about production behaviour.',
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
  const nearUlpRows = data.uv_subtexel_invariance.rendered_mutant.rows.map((row) =>
    `| ${row.case} | ${row.differs ? 'differs' : 'identical'} | ${row.changed_lane_count} |`).join('\n')
  const liveRows = data.binding_liveness_census.probes.map((probe) =>
    `| ${probe.binding} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')
  const zeroRows = [...data.range_zero_inertness_census.inert, data.range_zero_inertness_census.range_discriminator].map((probe) =>
    `| ${probe.binding} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')
  const defaultsRows = data.defaults_inertness_census.probes.map((entry) => entry.probes.map((probe) =>
    `| ${entry.binding} | ${JSON.stringify(probe.override)} | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')).join('\n')
  const wrapRows = data.wrap_arm_census.rows.map((row) => {
    const [ox, oy] = row.offset_f32_words_le
    const margins = row.half_texel_margins.map((m) => m.toPrecision(6)).join(' / ')
    const alts = row.alternates.map((alt) => `${alt.arm}:${alt.differs_from_case ? `differs(${alt.changed_lane_count})` : 'identical'}`).join(', ')
    return `| ${row.case} | ${row.arm} | ${ox} / ${oy} | ${margins} | ${row.lane_crosses_boundary.map((c) => c ? 'yes' : 'no').join(' / ')} | ${alts} |`
  }).join('\n')
  const cropArm = (arm) => `| ${arm.word_mismatches} of ${data.tile_translation.rect.tile_width * data.tile_translation.rect.tile_height * 4} | ${arm.byte_mismatches} | ${JSON.stringify(arm.first_mismatch.top_down_xy)} ${arm.first_mismatch.channel} | ${arm.tile_word ?? arm.first_mismatch.tile_word} vs ${arm.full_word ?? arm.first_mismatch.full_word} |`
  return `# Wobble exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; no preprocessor defines.
This is the first **varying-admission** oracle: the parity target is the materialization of
\`in vec2 v_texCoord;\` (raw \`wobble.glsl:14\`), which the JavaScript equates with \`context.uv\` -- the
pixel center's destination-local coordinate, aliased per pixel by \`beginPixel\` and copied by the canonical
kernel. There is no vertex stage, no interpolation, and no varying binding; every expected array below is
bound implicitly through the pinned pass-runner path.

## The contract this program exists to prove

| Fact | Value |
| --- | --- |
| GLSL declaration | \`${data.varying_materialization.glsl_declaration}\` (raw line 14; one read, zero writes) |
| JavaScript slot | \`${data.varying_materialization.javascript_slot_declaration}\` (factory scope, NOT pooled) |
| Per-pixel copy | \`${data.varying_materialization.per_pixel_copy}\` |
| Runtime alias | \`this.varyings.v_texCoord[0] = uv[0]\` / \`[1] = uv[1]\` in \`beginPixel\` |
| Numeric contract | ${data.varying_materialization.numeric_contract} |
| Discriminator case | \`${data.varying_materialization.discriminator_case}\` (range = 0: pure \`texture(inputTex, applyWrap(v_texCoord))\` pass-through) |

At \`range = 0\`, \`offsetScale = r * (0.01 + speed * 0.02) = 0\` pins the offset to +-0 and every wrap arm is
the identity on the open unit interval, so the case degenerates to a pure pass-through of the varying.
**Measured: the two varying mutants are the ONLY ledger mutants that move a lane there.** Any materialization
error -- lane order, y orientation, f32 drift -- lands exactly on that case.

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

The \`Function.prototype.toString\` pinning method is itself cross-validated at every run: the same snapshot
must reproduce cellrefract186's frozen factory-text digest
\`${data.provenance.factory_text_method_cross_validation.sha256}\` or this generator refuses to start.

No absolute path is recorded anywhere in this package. The \`--cpu-root\` argument is stored as
\`${data.provenance.cpu_snapshot.argument}\` and the rejected live checkout as
\`${data.provenance.cpu_snapshot.live_checkout_rejected}\`, resolved at run time from
${data.provenance.cpu_snapshot.live_checkout_resolution}. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings

The program has exactly ${data.runtime_binding_names.length} runtime bindings:
${data.runtime_binding_names.map((name) => `\`${name}\``).join(', ')}. There are no preprocessor defines.
${data.wrap_binding_narrowing}

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
${caseRows}

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
${data.runtime_binding_names.length} bindings with every float lane as a hexadecimal f32 word, the external
\`runPass\` time/seed pair, the complete expected Float32 word array, the complete independently captured
RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each array. Every input lane is a small
dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
${coverageRows}

## Tile translation: probed before asserting, and NO crop identity holds on any arm

Per the cellrefract section 15 lesson the crop question was probed, not assumed, and the range = 0 arm
(the design's "plausibly sound" arm) was probed separately. **Measured: the tile output is not a crop of
the full output on either arm.**

| Arm | Word mismatches | Byte mismatches | First mismatch (top-down) |
| --- | --- | --- | --- |
| live clamp (the stored tile case) ${cropArm(data.tile_translation.live_clamp_arm)}
| range zero (probed separately) ${cropArm(data.tile_translation.range_zero_arm)}

${data.tile_translation.why}

The sampleCoord probes publish the post-wrap coordinate that feeds \`texture()\` on both routes: on the
live-clamp arm **${data.tile_translation.live_clamp_samplecoord_witness.equal_x_lanes} x-lanes and
${data.tile_translation.live_clamp_samplecoord_witness.equal_y_lanes} y-lanes of
${data.tile_translation.live_clamp_samplecoord_witness.compared_pairs_per_lane}** coincide as f32 words; on the
range-zero arm **${data.tile_translation.range_zero_samplecoord_witness.equal_x_lanes} and
${data.tile_translation.range_zero_samplecoord_witness.equal_y_lanes}**. The coincidences are exact f32
equalities (e.g. \`(2 + 0.5) / 5 = 0.5 = (3 + 2 + 0.5) / 11\`) and, on the live arm, clamp saturation
collapsing distinct folded coordinates to the same 0/1 word -- not evidence of alignment.
${data.tile_translation.consequence}

## One-axis control group on \`${data.control_group.anchor}\`: the wrap ToInt32-narrowing axis

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${controlRows}

The \`wrap-binding-unbound\` and fractional-wrap rows pin \`wrap|0\` (the GLSL \`int mode = int(wrap);\`):
\`undefined | 0 === 0\` and \`ToInt32(0.5) === 0\` select mirror exactly as the bound 0 does, while
\`ToInt32(1.5) === 1\` selects repeat and measurably differs. The port always binds \`wrap\`; these rows
record the authority's narrowing semantics.

## Binding liveness census (anchor)

| Binding | Versus baseline | Changed lanes |
| --- | --- | ---: |
${liveRows}

## The range-zero inertness census

| Binding | Versus baseline | Changed lanes |
| --- | --- | ---: |
${zeroRows}

${data.range_zero_inertness_census.rule}

## The defaults inertness census: at the shipped defaults, every scalar binding is inert

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
${defaultsRows}

${data.defaults_inertness_census.rule}

## The wrap-arm census

| Case | Arm | offset words | half-texel margins | lane crosses | Alternates |
| --- | --- | --- | --- | --- | --- |
${wrapRows}

${data.wrap_arm_census.rule}

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
${mutantRows}

All six ledger mutants are one-anchor/one-replacement rewrites of the canonical factory text (the wrap swap
is an ordered three-anchor chain through a unique temp identifier), compiled and rendered by this generator,
and each was **verified bit-differing before it was budgeted**. The expected outcome is frozen **per case
and per mutant**; \`--check\` fails if any single cell flips, in either direction.

${data.mutation_discrimination_contract.witness_overlap_disclosure}

### The sub-texel uv control

| Case | Result | Changed lanes |
| --- | --- | ---: |
${nearUlpRows}

${data.uv_subtexel_invariance.reason}

### The dead-code census

${data.dead_code_census.claim}

## Claim boundaries

- ${data.claim_boundaries.varying_materialization}
- ${data.claim_boundaries.tile_translation}
- ${data.claim_boundaries.range_zero_discriminator}
- ${data.claim_boundaries.defaults_inert}
- ${data.claim_boundaries.wrap_narrowing}
- ${data.claim_boundaries.no_dead_code}
- ${data.claim_boundaries.subtexel_invariance}
- ${data.claim_boundaries.synthetic_probes}
- ${data.claim_boundaries.normalized_source}

## Regeneration

\`\`\`sh
node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/varying-parity/wobble_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_wobble_native_oracle_include.py --self-test
\`\`\`

Both generators are fail-closed and check mode performs no writes.
`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)

// No absolute path may appear anywhere in the emitted document. The report is
// sidecar-verified and byte-compared by `--check` exactly like the JSON, so a
// path leaked into the report ALONE would reproduce the same machine-bound
// gate with neither scanner naming it. Both documents are scanned.
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
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Wobble oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Wobble oracle report drift')
}
const controlSummary = controlGroup.controls.map((item) => `${item.name}=${item.observed}`).join(' ')
const ledgerSummary = mutationLedger.map((mutant) => `${mutant.name}:${mutant.witness_cases.length}/${cases.length}`).join(' ')
console.log(`Wobble oracle ${write ? 'written' : 'checked'}: ${renderCases.length} cases, `
  + `${mutationLedger.length} ledger mutants [${ledgerSummary}], controls [${controlSummary}], `
  + `tile non-crop on both arms (clamp ${liveCrop.wordMismatches}/, range-zero ${zeroCrop.wordMismatches} `
  + `of ${totalCropLanes} words), sub-texel uv invariant (${uvSubtexelInvariance.rendered_divergences} lanes), `
  + `defaults all-scalar-inert, cellRefract toString cross-validation reproduced`)
