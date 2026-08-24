#!/usr/bin/env node
// Normalmap185 canonical JavaScript oracle generator (`filter/normalMap:normalMap`).
//
// Authority: the unmodified public canonical factory `canonicalFactory86` from
// an immutable snapshot of `noisemaker-for-cpu`, executed through the pinned
// `bindCanonicalKernel` / `GlslCpuRuntime` / `runPass` path. No C++ output
// participates in any expected array. A locally reimplemented formula is not an
// oracle and is never used here.
//
// This program exists to prove the materialization of three CONST file-scope
// tables that the GLSL declares as `const ivec2[9]` / `const float[9]`:
//   * `SOBEL_X_KERNEL` / `SOBEL_Y_KERNEL` are plain JS `Array`s -- doubles,
//     never narrowed to f32. The native element type is `double`.
//   * `SOBEL_OFFSETS` elements are runtime `ivec2` objects built through
//     `cpu_ivec2`, i.e. POOLED `Int32Array`s protected by `beginPixel`'s
//     signed base index. A `PooledFloat32Array` table would NOT survive; see
//     `pooled_table_hazard`.
// Neither float table is oracle-discriminable as a double (every element is
// exactly representable in binary32), so that half is proven structurally and
// recorded as a claim boundary -- never by a green pixel run.
//
//   node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'normalmap-oracles.json')
const reportPath = path.join(here, 'normalmap-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_normalmap_native_oracle_include.py')

const schema = 'noisemaker-for-cpp.normalmap185.pixel-parity.v1'
const schemaVersion = 1
const programKey = 'filter/normalMap:normalMap'
const effectKey = 'filter/normalMap'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const factoryName = 'canonicalFactory86'
const factoryTextSha256 = '9b1348836825b6efe90109747ca5ef341651527077d8ad7dbbcbc7080369842a'
const nextFactoryName = 'canonicalFactory87'

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
const sourceRelative = `tools/glslcpp/corpus/${corpusRevision}/sources/filter/normalMap/normalMap.glsl`
const sourceBytesExpected = 4017
const sourceSha256Expected = '384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb'
const sourceLinesExpected = 155

// Exactly five runtime bindings, in GLSL declaration order. The program has NO
// preprocessor defines; `defines` is recorded as an empty object rather than
// omitted so a future define cannot appear unremarked.
const bindingNames = Object.freeze(['tileOffset', 'fullResolution', 'inputTex', 'size', 'motion'])
const bindingAbi = Object.freeze({
  tileOffset: 'Vec2', fullResolution: 'Vec2', inputTex: 'sampler2D', size: 'Vec4', motion: 'Vec4',
})
const vecLanes = Object.freeze({ Vec2: 2, Vec4: 4 })

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
// `check_corpus._ADAPTERS` (the Python-side eligibility table) is READ FROM THE
// LIVE `check_corpus.py` below, never transcribed: a frozen copy compared
// against another frozen copy proves nothing, and would stay green if
// `filter/normalMap` were ever added to the real table.
const corpusAdapterSourceRelative = 'tools/glslcpp/check_corpus.py'
const corpusAdapterCensusExpected = Object.freeze([
  'classicNoisedeck/fractal:fractal', 'filter/historicPalette:historicPalette',
  'filter/palette:palette', 'synth/julia:julia',
])
// `canonicalAdapterFactories` (the JavaScript-side override table) is a larger,
// separate set, pinned by census so a new override cannot silently take the key.
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
if (typeof canonicalFactory !== 'function') throw new Error('canonical normalMap factory missing')
if (publicFactory !== canonicalFactory) throw new Error('public normalMap factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('unexpected normalMap adapter override')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected normalMap adapter override value')
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
if (corpusAdapterKeys.includes(programKey)) throw new Error('filter/normalMap:normalMap must not be corpus-adapter-routed')
if (canonicalAdapterKeys.includes(programKey)) throw new Error('filter/normalMap:normalMap must not be adapter-routed')
{
  const observed = Object.keys(canonicalAdapterFactories).sort()
  const expected = [...canonicalAdapterKeys].sort()
  if (observed.length !== expected.length || observed.some((key, index) => key !== expected[index])) {
    throw new Error(`adapter table census drift: ${observed.join(', ')}`)
  }
}
if (canonicalFactory.name !== factoryName) throw new Error(`canonical normalMap factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) throw new Error(`canonical normalMap factory text drift: ${sha256(canonicalText)}`)

const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf(`function ${nextFactoryName}`, sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('canonical normalMap factory source slice missing')
const canonicalSlice = canonicalKernelsSource.slice(sliceStart, sliceEnd)

// ---------------------------------------------------------------------------
// The materialization this package exists to pin, read from the shipped JS
// ---------------------------------------------------------------------------

const offsetsDeclaration = 'var SOBEL_OFFSETS = [cpu_ivec2(-1, -1), cpu_ivec2(0, -1), cpu_ivec2(1, -1), '
  + 'cpu_ivec2(-1, 0), cpu_ivec2(0, 0), cpu_ivec2(1, 0), cpu_ivec2(-1, 1), cpu_ivec2(0, 1), cpu_ivec2(1, 1)];'
const xKernelDeclaration = 'var SOBEL_X_KERNEL = [0.5, 0, -0.5, 1, 0, -1, 0.5, 0, -0.5];'
const yKernelDeclaration = 'var SOBEL_Y_KERNEL = [0.5, 1, 0.5, 0, 0, 0, -0.5, -1, -0.5];'
const asU32Declaration = 'function as_u32 (value) {\n  \treturn max(round(value), 0)|0;\n  };'
const finalTexelStatement = 'var texel = texelFetch(inputTex, cpu_ivec2_vec2('
  + 'new $runtime.PooledFloat32Array([global_id[0], global_id[1]])), 0);'
const accumulatorStatements = '\tdx += value * SOBEL_X_KERNEL[i];\n  \tdy += value * SOBEL_Y_KERNEL[i];'
const mainOpener = '  function main () {\n'
const fragColorDeclaration = 'var fragColor = new Float32Array([0, 0, 0, 0]);'
const fragColorWrite = '(fragColor[0] = x_value, fragColor[1] = y_value, fragColor[2] = z_value, '
  + 'fragColor[3] = texel[3], fragColor);'

for (const [label, fragment] of [
  ['SOBEL_OFFSETS', offsetsDeclaration],
  ['SOBEL_X_KERNEL', xKernelDeclaration],
  ['SOBEL_Y_KERNEL', yKernelDeclaration],
  ['as_u32', asU32Declaration],
  ['final texelFetch', finalTexelStatement],
  ['accumulator', accumulatorStatements],
  ['main opener', mainOpener],
  ['fragColor declaration', fragColorDeclaration],
  ['fragColor write', fragColorWrite],
  ['CHANNEL_COUNT', 'var CHANNEL_COUNT = 4;'],
  ['CHANNEL_CAP', 'var CHANNEL_CAP = 4;'],
]) {
  const occurrences = canonicalText.split(fragment).length - 1
  if (occurrences !== 1) throw new Error(`${label} census drift: matched ${occurrences} times`)
}

// The tables are plain JS Arrays -- doubles. `Float32Array` anywhere in these
// three declarations would silently change the element contract.
for (const declaration of [offsetsDeclaration, xKernelDeclaration, yKernelDeclaration]) {
  if (declaration.includes('Float32Array')) throw new Error('a const table declaration became a Float32Array')
}
const xKernelElements = [0.5, 0, -0.5, 1, 0, -1, 0.5, 0, -0.5]
const yKernelElements = [0.5, 1, 0.5, 0, 0, 0, -0.5, -1, -0.5]
const offsetElements = [[-1, -1], [0, -1], [1, -1], [-1, 0], [0, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]
if (xKernelDeclaration !== `var SOBEL_X_KERNEL = [${xKernelElements.join(', ')}];`) {
  throw new Error('SOBEL_X_KERNEL element census drift')
}
if (yKernelDeclaration !== `var SOBEL_Y_KERNEL = [${yKernelElements.join(', ')}];`) {
  throw new Error('SOBEL_Y_KERNEL element census drift')
}
if (offsetsDeclaration !== `var SOBEL_OFFSETS = [${offsetElements.map(([x, y]) => `cpu_ivec2(${x}, ${y})`).join(', ')}];`) {
  throw new Error('SOBEL_OFFSETS element census drift')
}
// Amendment 11: X viewed as 3x3 is exactly the transpose of Y.
for (let row = 0; row < 3; row += 1) {
  for (let column = 0; column < 3; column += 1) {
    if (!Object.is(xKernelElements[3 * row + column], yKernelElements[3 * column + row])) {
      throw new Error('SOBEL_X_KERNEL is no longer the exact transpose of SOBEL_Y_KERNEL; '
        + 'amendment 11 rests on this identity')
    }
  }
}
const kernelElements = [...xKernelElements, ...yKernelElements]
if (kernelElements.length !== 18) throw new Error('kernel element census drift')
const inexactKernelElements = kernelElements.filter((element) => !Object.is(f(element), element))

const sourcePath = path.join(cppRoot, sourceRelative)
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error('pinned normalMap GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')
const sourceLines = sourceText.split('\n').length
if (sourceLines - 1 !== sourceLinesExpected) throw new Error(`pinned normalMap GLSL line census drift: ${sourceLines - 1}`)
if (/^\s*#\s*(?:define|ifdef|ifndef|if|else|elif|endif)\b/m.test(sourceText.replace(/^#version[^\n]*\n/, ''))) {
  throw new Error('normalMap GLSL grew a preprocessor conditional or define')
}

const effect = effectRecords.find((item) => item.id === effectKey)
if (!effect || effect.func !== 'normalMap' || effect.kind !== 'filter') throw new Error('normalMap metadata drift')
if (effect.passes?.length !== 1 || effect.passes[0]?.program !== 'normalMap') throw new Error('normalMap pass interface drift')
if (Object.keys(effect.params ?? {}).length !== 0) throw new Error('normalMap grew a param; `size` may no longer be the zero vec4')
if (Object.keys(effect.textures ?? {}).length !== 0 || effect.externalTexture !== null) throw new Error('normalMap texture metadata drift')
if (effect.passes[0]?.inputs?.inputTex !== 'inputTex') throw new Error('normalMap input interface drift')

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
      throw new Error(`normalMap comparer did not preflight ${reason}`)
    }
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  expectReject(compareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape'), 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32'
      || !bytesOf(plusZero.toRgba8()).equals(bytesOf(minusZero.toRgba8()))) {
    throw new Error('normalMap comparer missed signed zero')
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
    throw new Error('normalMap comparer missed NaN payload')
  }
  const finalLane = compareExact(new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)])),
    expectedRecord(plusZero), 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch.channel !== 'a'
      || finalLane.first_mismatch.lane_or_byte_index !== 3) {
    throw new Error('normalMap comparer missed final alpha lane')
  }
  const byteExpected = expectedRecord(plusZero)
  byteExpected.rgba8[3] ^= 1
  const byteOnly = compareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch.channel !== 'a') {
    throw new Error('normalMap comparer missed independent byte mismatch')
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
// AND in binary64. That matters: it keeps the input itself from being a source
// of rounding that the reader would have to disentangle from the program's own.
// ---------------------------------------------------------------------------

const patterns = {
  // Opaque gradient. Alpha is exactly 1 in every opaque pattern; see
  // `alpha_construction` in the coverage axes for why that is load-bearing.
  ramp: (x, y) => [((3 * x + 5 * y) % 8) / 8, ((x + 3 * y) % 4) / 4, ((5 * x + y) % 16) / 16, 1],
  // Hard column/row edges so `clamp01` saturates at both 0 and 1.
  contrast: (x, y) => [(x % 4) < 2 ? 0 : 1, ((x + y) % 3 === 0) ? 0 : 1, y % 2, 1],
  // Deliberately outside [0, 1], including exact -0, to reach `clamp(texel.xyz,
  // 0, 1)` and `cbrt_safe`'s negative-sign arm.
  wide: (x, y) => [(((7 * x + 11 * y) % 13) - 6) / 4, (((x + 5 * y) % 11) - 3) / 4,
    ((x + y) % 5 === 0) ? -0 : ((3 * x + y) % 9) / 4, 1],
  // Constant value map, varying alpha: dx and dy are exactly +0 at every pixel.
  flat: (x, y) => [0.25, 0.5, 0.75, ((3 * x + 7 * y) % 8) / 8],
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

// `filter/normalMap` declares NO params, so the shipped `createCanonicalBindings`
// leaves `size` as the zero vec4 on every production render. Cases that bind a
// non-zero `size` are therefore SYNTHETIC ABI coverage, exactly as
// `shape-extreme-tile-offset` was, and they are labelled as such.
const cases = [
  {
    name: 'normalmap-default-16x9',
    coverage: ['control-group anchor', 'production binding set: size is the zero vec4',
      'channelCount collapses to 1 so value_map_component returns texel.x',
      'landscape 16x9', 'wrap_coord exercised on all four borders',
      'opaque input: alpha is exactly 1 in every lane', 'witnesses normalmap-sobel-x-y-swapped'],
    width: 16, height: 9, pattern: 'ramp', production_binding_set: true,
  },
  {
    name: 'normalmap-default-7x5',
    coverage: ['production binding set', 'odd dimensions in both axes',
      'the smallest surface where every wrap_coord corner is distinct',
      'opaque input', 'witnesses normalmap-sobel-x-y-swapped'],
    width: 7, height: 5, pattern: 'ramp', production_binding_set: true,
  },
  {
    name: 'normalmap-high-contrast-8x6',
    coverage: ['production binding set', 'clamp01 saturates at both 0 and 1',
      'x_value and y_value both pinned at the clamp bounds somewhere',
      'opaque input', 'witnesses normalmap-sobel-x-y-swapped'],
    width: 8, height: 6, pattern: 'contrast', production_binding_set: true,
  },
  {
    name: 'normalmap-channelcount-2-8x6',
    coverage: ['synthetic size.z = 2',
      'the `channelCount == 2` arm of value_map_component, which is a distinct SOURCE path that '
      + 'returns texel.x and is therefore BYTE-IDENTICAL to the channelCount <= 1 arm; see '
      + 'value_map_arm_census. It is not coverage of a second value map',
      'unreachable through the shipped binding set', 'opaque input',
      'witnesses normalmap-sobel-x-y-swapped'],
    width: 8, height: 6, pattern: 'ramp', size: [0, 0, 2, 0],
  },
  {
    name: 'normalmap-channelcount-3-oklab-8x6',
    coverage: ['synthetic size.z = 3', 'the oklab_l_component / srgb_to_linear / cbrt_safe subtree',
      'the only cases whose value map leaves the dyadic grid',
      'witnesses the double accumulator census', 'opaque input',
      'witnesses normalmap-sobel-x-y-swapped'],
    width: 8, height: 6, pattern: 'ramp', size: [0, 0, 3, 0],
  },
  {
    name: 'normalmap-channelcount-4-clamped-8x6',
    coverage: ['synthetic size.z = 4',
      'the `channelCount == 4` arm, whose clamp(texel.xyz, 0, 1) is measured REDUNDANT: '
      + 'oklab_l_component clamps each channel itself, so this arm is byte-identical to arm three '
      + 'even here. See value_map_arm_census',
      'the only case whose input lanes leave [0, 1], which is what reaches srgb_to_linear\'s low arm',
      'exact -0 input lanes reach cbrt_safe\'s value == 0 arm',
      'witnesses the double accumulator census', 'opaque input',
      'witnesses normalmap-sobel-x-y-swapped'],
    width: 8, height: 6, pattern: 'wide', size: [0, 0, 4, 0],
  },
  {
    name: 'normalmap-explicit-size-larger-8x6',
    coverage: ['synthetic size.xy = (11, 8) larger than the 8x6 texture',
      'wrap_coord limits exceed the texture, so texelFetch clamps at the borders',
      'the width == 0 / height == 0 textureSize fallbacks are NOT taken',
      'no pixel takes the early return', 'opaque input',
      'witnesses normalmap-sobel-x-y-swapped'],
    width: 8, height: 6, pattern: 'ramp', size: [11, 8, 1, 0],
  },
  {
    name: 'normalmap-flat-alpha-8x6',
    coverage: ['constant value map: dx and dy are exactly +0 at every pixel',
      'the only case whose alpha is not uniformly 1',
      'non-reaching control for normalmap-sobel-x-y-swapped',
      'the sole witness for normalmap-alpha-source-transposed'],
    width: 8, height: 6, pattern: 'flat', production_binding_set: true,
  },
]
if (cases.length !== 8) throw new Error(`normalMap fixture census drift: ${cases.length}`)
if (new Set(cases.map((item) => item.name)).size !== cases.length) throw new Error('duplicate normalMap case name')
for (const definition of cases) {
  for (const field of ['width', 'height']) {
    const value = definition[field]
    if (!Number.isInteger(value) || value <= 0) throw new Error(`${definition.name}: ${field} must be a positive integer`)
  }
  if (typeof patterns[definition.pattern] !== 'function') throw new Error(`${definition.name}: unknown pattern`)
  const size = definition.size ?? [0, 0, 0, 0]
  if (!Array.isArray(size) || size.length !== 4) throw new Error(`${definition.name}: size must be a vec4`)
  const zeroSize = size.every((lane) => Object.is(lane, 0))
  if (zeroSize !== (definition.production_binding_set === true)) {
    throw new Error(`${definition.name}: production_binding_set must be exactly "size is the zero vec4"`)
  }
}

// ---------------------------------------------------------------------------
// Rendering through the pinned public path
// ---------------------------------------------------------------------------

function uniformsFor(definition) {
  return {
    size: f32Vector(definition.size ?? [0, 0, 0, 0], 4),
    motion: f32Vector(definition.motion ?? [0, 0, 0, 0], 4),
  }
}

function bindingOptions(definition) {
  const uniforms = uniformsFor(definition)
  return {
    width: definition.width,
    height: definition.height,
    uniforms,
    textures: { inputTex: makeInput(definition.width, definition.height, definition.pattern) },
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
    size: options.uniforms.size, motion: options.uniforms.motion,
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
  return {
    width: surface.width,
    height: surface.height,
    f32_words_le: Array.from(rawWords, u32Hex),
    f32_sha256: sha256(bytesOf(surface.data)),
    rgba8_bytes: Array.from(rgba8),
    rgba8_sha256: sha256(bytesOf(rgba8)),
    finite_lane_count: finite,
    nonfinite_lane_count: surface.data.length - finite,
    distinct_alpha_f32_word_count: alphaWords.size,
    alpha_f32_words_le: [...alphaWords].sort(),
    distinct_alpha_rgba8_byte_count: alphaBytes.size,
  }
}

function inputRecord(surface) {
  const rawWords = words(surface.data)
  return {
    width: surface.width,
    height: surface.height,
    row_order: 'top-down storage; the GLSL texture origin is bottom-left and texelFetch flips',
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
    const lanes = vecLanes[abi]
    if (!(value instanceof Float32Array) || value.length !== lanes) throw new Error(`${name}: not a ${abi}`)
    out[name] = { abi, f32_values: Array.from(value), f32_words_le: Array.from(words(value), u32Hex) }
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
  const record = surfaceRecord(canonical.output)
  if (record.nonfinite_lane_count !== 0) throw new Error(`${definition.name}: non-finite output lane`)
  const opaque = definition.pattern !== 'flat'
  if (opaque && (record.distinct_alpha_f32_word_count !== 1 || record.alpha_f32_words_le[0] !== '0x3f800000')) {
    throw new Error(`${definition.name}: an opaque case must carry a uniform 0x3f800000 alpha lane`)
  }
  if (!opaque && record.distinct_alpha_f32_word_count < 2) {
    throw new Error(`${definition.name}: the varying-alpha case must carry more than one alpha word`)
  }
  return {
    name: definition.name,
    coverage: definition.coverage,
    route: definition.production_binding_set === true ? 'production-binding-set' : 'synthetic-size',
    width: definition.width,
    height: definition.height,
    input_pattern: definition.pattern,
    opaque_input: opaque,
    input_texture: inputRecord(canonical.input),
    bindings: bindingRecords(definition, canonical.bindings, canonical.input),
    external_pass: externalRecord(definition),
    output_expected: record,
    canonical_repeat: repeatIdentity,
    public_canonical: publicIdentity,
  }
})

// ---------------------------------------------------------------------------
// Mutant compilation
// ---------------------------------------------------------------------------

// A ledger mutant is one anchor, one replacement. A probe may use an ordered
// list of anchors; each must still match exactly once, and probes are never
// compared against a parity array.
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
// The disjoint mutation ledger
// ---------------------------------------------------------------------------

const swapReplacement = 'var SOBEL_X_KERNEL = [0.5, 1, 0.5, 0, 0, 0, -0.5, -1, -0.5];\n  '
  + 'var SOBEL_Y_KERNEL = [0.5, 0, -0.5, 1, 0, -1, 0.5, 0, -0.5];'
const mutantSpecs = [
  {
    name: 'normalmap-sobel-x-y-swapped',
    target: 'the two const float[9] tables: SOBEL_X_KERNEL and SOBEL_Y_KERNEL, swapped',
    contract: 'the two kernel tables are distinct and each is paired with the right accumulator',
    anchor: `${xKernelDeclaration}\n  ${yKernelDeclaration}`,
    replacement: swapReplacement,
    reaching: 'every case whose value map is not constant, i.e. every case where dx != dy somewhere',
    expected: {
      'normalmap-default-16x9': true,
      'normalmap-default-7x5': true,
      'normalmap-high-contrast-8x6': true,
      'normalmap-channelcount-2-8x6': true,
      'normalmap-channelcount-3-oklab-8x6': true,
      'normalmap-channelcount-4-clamped-8x6': true,
      'normalmap-explicit-size-larger-8x6': true,
      'normalmap-flat-alpha-8x6': false,
    },
  },
  {
    name: 'normalmap-alpha-source-transposed',
    target: 'the final texelFetch coordinate, built through a PooledFloat32Array -> ivec2 conversion',
    contract: 'the output alpha lane is the OWN pixel\'s texel.w, fetched at (global_id.x, global_id.y) '
      + 'in that lane order',
    anchor: finalTexelStatement,
    replacement: 'var texel = texelFetch(inputTex, cpu_ivec2_vec2('
      + 'new $runtime.PooledFloat32Array([global_id[1], global_id[0]])), 0);',
    reaching: 'only a case whose input alpha is not uniform; every opaque case fetches alpha 1 at any coordinate',
    expected: {
      'normalmap-default-16x9': false,
      'normalmap-default-7x5': false,
      'normalmap-high-contrast-8x6': false,
      'normalmap-channelcount-2-8x6': false,
      'normalmap-channelcount-3-oklab-8x6': false,
      'normalmap-channelcount-4-clamped-8x6': false,
      'normalmap-explicit-size-larger-8x6': false,
      'normalmap-flat-alpha-8x6': true,
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
    classification: 'rendered canonical-JS one-anchor/one-replacement mutant',
    ...mutantIdentity(spec, compiled),
    witness_cases: results.filter((result) => result.differs).map((result) => result.case),
    control_cases: results.filter((result) => !result.differs).map((result) => result.case),
    results,
  }
})
{
  const sets = mutationLedger.map((mutant) => new Set(mutant.witness_cases))
  for (let left = 0; left < sets.length; left += 1) {
    for (let right = left + 1; right < sets.length; right += 1) {
      const shared = [...sets[left]].filter((name) => sets[right].has(name))
      if (shared.length > 0) {
        throw new Error(`${mutationLedger[left].name} and ${mutationLedger[right].name} share witnesses `
          + `(${shared.join(', ')}); a divergence would not be attributable to one contract`)
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Amendment 11: the two mutants section 7 asked for are bit-identical
// ---------------------------------------------------------------------------

const transposedSpec = {
  name: 'normalmap-offsets-transposed',
  anchor: offsetsDeclaration,
  replacement: `var SOBEL_OFFSETS = [${offsetElements.map(([x, y]) => `cpu_ivec2(${y}, ${x})`).join(', ')}];`,
}
const transposedCompiled = compileMutant(transposedSpec)
const swapCompiled = compileMutant(mutantSpecs[0])
const transposeRows = cases.map((definition) => {
  const transposed = render(transposedCompiled.factory, definition).output
  const swapped = render(swapCompiled.factory, definition).output
  const against = compareExact(transposed, expectedRecord(swapped), `transpose-equivalence/${definition.name}`)
  const versusCanonical = compareExact(transposed, canonicalExpected.get(definition.name), `transpose-vs-canonical/${definition.name}`)
  if (!against.exact) {
    throw new Error(`${definition.name}: normalmap-offsets-transposed is NOT bit-identical to `
      + 'normalmap-sobel-x-y-swapped; amendment 11 has been invalidated and the mutant plan must be redesigned')
  }
  return {
    case: definition.name,
    identical_to_sobel_x_y_swapped: true,
    changed_lane_count_against_swap: against.changed_lane_count ?? 0,
    changed_lane_count_against_canonical: versusCanonical.changed_lane_count ?? 0,
    differs_from_canonical: !versusCanonical.exact,
    ...digests(transposed),
  }
})
const transposeEquivalenceProof = {
  retracted_mutant: transposedSpec.name,
  retained_mutant: mutantSpecs[0].name,
  ...mutantIdentity(transposedSpec, transposedCompiled),
  algebra: 'SOBEL_X_KERNEL viewed as 3x3 is exactly the transpose of SOBEL_Y_KERNEL (X[3r+c] == Y[3c+r] '
    + 'for all nine, checked elementwise by this generator). Transposing every offset permutes the sample '
    + 'list by the involution s(3r+c) = 3c+r, so dx\' = SUM X[s(j)]*v_j = SUM Y[j]*v_j = dy. The two '
    + 'mutants are therefore the same function of the input.',
  measured: 'bit-identical on every case, in Float32 words and in RGBA8 bytes',
  rows: transposeRows,
  consequence: 'design section 7 asked for both. Two mutants that cannot be told apart cannot attribute a '
    + 'divergence to a contract, so only normalmap-sobel-x-y-swapped is carried in the disjoint ledger. '
    + 'This proof is what justifies dropping the other, and it is re-measured on every run rather than '
    + 'asserted in prose.',
  non_vacuous: transposeRows.some((row) => row.differs_from_canonical),
}
if (!transposeEquivalenceProof.non_vacuous) {
  throw new Error('the transpose-equivalence proof is vacuous: neither mutant differs from canonical anywhere')
}

// ---------------------------------------------------------------------------
// Kernel-table mutants that are NOT in the disjoint ledger
//
// Design amendment 11 suggests replacing the retracted mutant with a
// kernel-element perturbation. Measured here, each candidate's witness set
// CONTAINS normalmap-sobel-x-y-swapped's -- identically for the negation,
// strictly for the perturbation -- so neither can be a second DISJOINT ledger
// entry on any case set that also covers the program's real behaviour. They are shipped as a census with per-case results, and the
// ledger's second slot is filled by a mutant on a different contract entirely,
// which is what amendment 11's own criterion -- "something no offset
// permutation can produce" -- admits.
// ---------------------------------------------------------------------------

const kernelCensusSpecs = [
  {
    name: 'normalmap-sobel-x-negated',
    anchor: xKernelDeclaration,
    replacement: 'var SOBEL_X_KERNEL = [-0.5, -0, 0.5, -1, -0, 1, -0.5, -0, 0.5];',
    note: 'negates every SOBEL_X_KERNEL element; moves x_value, leaves y_value, and leaves z_value '
      + 'wherever abs(dx) is unchanged. On this case set its witness set is measured IDENTICAL to the '
      + 'retained ledger mutant\'s, which is stronger than a superset: it is wholly indiscriminable '
      + 'from it here.',
  },
  {
    name: 'normalmap-sobel-x1-perturbed',
    anchor: xKernelDeclaration,
    replacement: 'var SOBEL_X_KERNEL = [0.5, 0.25, -0.5, 1, 0, -1, 0.5, 0, -0.5];',
    note: 'amendment 11\'s suggested replacement, SOBEL_X_KERNEL[1] = 0.25; its measured witness set '
      + 'is a strict superset of the retained ledger mutant\'s -- it additionally witnesses the flat '
      + 'case, where the added 0.25 * v_1 term moves x_value away from the constant 0.5',
  },
]
const kernelTableMutantCensus = {
  purpose: 'kernel-table mutants measured per case but deliberately NOT in the disjoint ledger, because '
    + 'each shares witnesses with normalmap-sobel-x-y-swapped and could not attribute a divergence',
  in_disjoint_ledger: false,
  mutants: kernelCensusSpecs.map((spec) => {
    const compiled = compileMutant(spec)
    const results = measureAcrossCases(compiled.factory, spec.name)
    if (!results.some((result) => result.differs)) throw new Error(`${spec.name}: cannot diverge anywhere`)
    const witnesses = results.filter((result) => result.differs).map((result) => result.case)
    const ledgerWitnesses = new Set(mutationLedger[0].witness_cases)
    // Containment is what disqualifies a candidate from the disjoint ledger, and
    // it is NOT strict for every candidate: `normalmap-sobel-x-negated` witnesses
    // exactly the retained mutant's seven cases. Recording that as a strict
    // superset would understate it -- on this case set the two are wholly
    // indiscriminable. The relation is measured, not described.
    const contains = [...ledgerWitnesses].every((name) => witnesses.includes(name))
    return {
      name: spec.name,
      note: spec.note,
      ...mutantIdentity(spec, compiled),
      witness_cases: witnesses,
      control_cases: results.filter((result) => !result.differs).map((result) => result.case),
      contains_retained_ledger_witnesses: contains,
      witness_relation: !contains ? 'incomparable'
        : witnesses.length === ledgerWitnesses.size ? 'identical' : 'strict-superset',
      results,
    }
  }),
}
for (const mutant of kernelTableMutantCensus.mutants) {
  if (!mutant.contains_retained_ledger_witnesses) {
    throw new Error(`${mutant.name}: the recorded reason for keeping it out of the disjoint ledger no longer holds`)
  }
}
if (!kernelTableMutantCensus.mutants.some((mutant) => mutant.witness_relation === 'identical')) {
  throw new Error('no kernel-census mutant is witness-identical to the retained ledger mutant; the '
    + 'recorded relations must be re-derived rather than carried forward')
}

// ---------------------------------------------------------------------------
// Amendment 12: the round axis is structurally unsatisfiable, proven invariant
// ---------------------------------------------------------------------------

const roundSpec = {
  name: 'normalmap-round-half-away',
  anchor: asU32Declaration,
  replacement: 'function as_u32 (value) {\n  \treturn max((value < 0 ? -Math.round(-value) : Math.round(value)), 0)|0;\n  };',
}
const roundCompiled = compileMutant(roundSpec)
const roundRows = measureAcrossCases(roundCompiled.factory, roundSpec.name)
if (roundRows.some((row) => row.differs)) {
  throw new Error('normalmap-round-half-away diverged; amendment 12 records the discriminating domain as '
    + 'provably empty, so a divergence means the clamp argument no longer holds')
}
const roundScan = (() => {
  const asU32 = (value) => Math.max(Math.round(value), 0) | 0
  const halfAway = (value) => Math.max(value < 0 ? -Math.round(-value) : Math.round(value), 0) | 0
  let samples = 0
  let rounderDisagreements = 0
  let asU32Divergences = 0
  const record = (value) => {
    samples += 1
    const nearest = Math.round(value)
    const away = value < 0 ? -Math.round(-value) : Math.round(value)
    if (!Object.is(nearest, away)) rounderDisagreements += 1
    if (!Object.is(asU32(value), halfAway(value))) asU32Divergences += 1
  }
  for (let index = -10000; index <= 10000; index += 1) { record(index / 2); record(index / 4) }
  for (const value of [0, -0, 0.5, -0.5, 1.5, -1.5, 2.5, -2.5, 8388608, 8388608.5, -8388608.5,
    8388607.5, -8388607.5, 16777216, -16777216, 2147483647, -2147483648, NaN, Infinity, -Infinity]) record(value)
  return { samples, rounder_disagreements: rounderDisagreements, as_u32_divergences: asU32Divergences }
})()
if (roundScan.rounder_disagreements === 0) throw new Error('the round scan found no rounder disagreement; it is vacuous')
if (roundScan.as_u32_divergences !== 0) throw new Error('the round scan found an as_u32 divergence; amendment 12 is wrong')
const asU32CallSites = (() => {
  const sites = [
    ['sanitize_channelCount', 'var count = as_u32(raw_value);'],
    ['main/width', 'var width = as_u32(size[0]);'],
    ['main/height', 'var height = as_u32(size[1]);'],
  ]
  for (const [label, fragment] of sites) {
    const occurrences = canonicalText.split(fragment).length - 1
    if (occurrences !== 1) throw new Error(`as_u32 call-site census drift at ${label}: ${occurrences}`)
  }
  // Exactly three CALL sites. The declaration is written `as_u32 (value)` with a
  // space, so it never matches this split and is deliberately not counted here.
  const total = canonicalText.split('as_u32(').length - 1
  if (total !== sites.length) throw new Error(`as_u32 call-site count drift: ${total}`)
  return sites.map(([label, fragment]) => ({ label, statement: fragment }))
})()
const asU32RoundAxis = {
  status: 'unsatisfiable-control-proven-invariant',
  design_reference: 'normalmap-design.md amendment 12, following shapes183-design.md section 11',
  declaration: 'function as_u32 (value) { return max(round(value), 0)|0; }',
  call_sites: asU32CallSites,
  call_site_count: asU32CallSites.length,
  why_empty: 'Math.round and round-half-away-from-zero differ ONLY on negative half-integers, and every '
    + 'negative result is collapsed by the max(..., 0) clamp. The discriminating domain is empty because '
    + 'of the clamp, not because this oracle\'s bindings happen to miss it, so no binding set can make '
    + 'this mutant discriminate.',
  scalar_scan: roundScan,
  rendered_mutant: { name: roundSpec.name, ...mutantIdentity(roundSpec, roundCompiled), rows: roundRows },
  rendered_divergences: roundRows.reduce((total, row) => total + row.changed_lane_count, 0),
  claim: 'This oracle package can prove NOTHING WHATSOEVER about the round contract for this program. The '
    + 'axis is recorded and proven invariant; it is not waived, and it is not evidence.',
}

// ---------------------------------------------------------------------------
// Design section 9: no f32-narrowing mutant is available on the kernel tables
// ---------------------------------------------------------------------------

const narrowingSpec = {
  name: 'normalmap-kernel-tables-f32-narrowed',
  anchor: `${xKernelDeclaration}\n  ${yKernelDeclaration}`,
  replacement: `${xKernelDeclaration.slice(0, -1)}.map(Math.fround);\n  ${yKernelDeclaration.slice(0, -1)}.map(Math.fround);`,
}
const narrowingCompiled = compileMutant(narrowingSpec)
const narrowingRows = measureAcrossCases(narrowingCompiled.factory, narrowingSpec.name)
if (narrowingRows.some((row) => row.differs)) {
  throw new Error('the kernel-table narrowing mutant diverged; design section 9 records every element as '
    + 'exactly representable in binary32, so a divergence means the tables changed')
}
const kernelTableNarrowingAxis = {
  status: 'cannot-diverge-do-not-ship',
  element_count: kernelElements.length,
  elements: { SOBEL_X_KERNEL: xKernelElements, SOBEL_Y_KERNEL: yKernelElements },
  every_element_exactly_f32_representable: inexactKernelElements.length === 0,
  inexact_elements: inexactKernelElements,
  rendered_mutant: { name: narrowingSpec.name, ...mutantIdentity(narrowingSpec, narrowingCompiled), rows: narrowingRows },
  rendered_divergences: narrowingRows.reduce((total, row) => total + row.changed_lane_count, 0),
  claim: 'Every element of both tables (0.5, 0, 1 and their negations) is exactly representable in binary32 '
    + 'AND binary64, so no value in this program distinguishes std::array<double, 9> from '
    + 'std::array<float, 9>. The double contract is proven STRUCTURALLY -- by the emitted native type and '
    + 'by the JS being a plain Array rather than a Float32Array -- and a green pixel run is not evidence '
    + 'for it. Shipping such a mutant as a control would be shipping a mutant that cannot diverge.',
}
if (!kernelTableNarrowingAxis.every_element_exactly_f32_representable) {
  throw new Error('a kernel element is no longer exactly f32-representable; design section 9 must be revisited')
}

// ---------------------------------------------------------------------------
// Per-pixel re-evaluation equivalence (design 3.1, as amended by 15)
//
// `source_global_locals` emits admitted globals as const locals INSIDE the pixel
// body, so the port re-evaluates all three tables per pixel. That is a proof
// obligation, not an assumption: this mutant performs exactly that rewrite in
// the JavaScript and must render bit-identically on every case.
// ---------------------------------------------------------------------------

const reevalSpec = {
  name: 'normalmap-tables-reevaluated-per-pixel',
  anchor: mainOpener,
  replacement: `${mainOpener}  \t${offsetsDeclaration}\n  \t${xKernelDeclaration}\n  \t${yKernelDeclaration}\n`,
}
const reevalCompiled = compileMutant(reevalSpec)
const reevalRows = measureAcrossCases(reevalCompiled.factory, reevalSpec.name)
if (reevalRows.some((row) => row.differs)) {
  throw new Error('re-evaluating the three tables per pixel changed the output; the port\'s '
    + 'source_global_locals rewrite is NOT observationally equivalent for this program')
}
const perPixelReevaluationEquivalence = {
  status: 'measured-equivalent',
  rewrite: 'shadow all three factory-scope tables with identical declarations at the top of main()',
  rendered_mutant: { name: reevalSpec.name, ...mutantIdentity(reevalSpec, reevalCompiled), rows: reevalRows },
  rendered_divergences: reevalRows.reduce((total, row) => total + row.changed_lane_count, 0),
  operative_reason: 'Design amendment 15 retracts section 3.1\'s reason. Literal-only initializers are '
    + 'NECESSARY BUT NOT SUFFICIENT. The operative reason is ELEMENT MATERIALIZATION: SOBEL_X_KERNEL and '
    + 'SOBEL_Y_KERNEL are plain Number arrays, and SOBEL_OFFSETS holds pooled Int32Arrays whose pool index '
    + 'beginPixel restores to a snapshotted base. See pooled_table_hazard.',
}

// ---------------------------------------------------------------------------
// Amendment 15: the pooled-table hazard, executed against the pinned runtime
// ---------------------------------------------------------------------------

const poolProbeSpec = {
  name: 'normalmap-pooled-table-probe',
  anchors: [
    [yKernelDeclaration, `${yKernelDeclaration}\n  var POOL_FLOAT_TABLE = [new $runtime.PooledFloat32Array([111, 222]), `
      + 'new $runtime.PooledFloat32Array([333, 444])];\n  var POOL_INT_TABLE = [cpu_ivec2(-11, -22), cpu_ivec2(-33, -44)];'],
    [fragColorWrite, '(fragColor[0] = POOL_FLOAT_TABLE[0][0], fragColor[1] = POOL_FLOAT_TABLE[1][1], '
      + 'fragColor[2] = POOL_INT_TABLE[0][0], fragColor[3] = POOL_INT_TABLE[1][1], fragColor);'],
  ],
}
const poolProbeCompiled = compileMutant(poolProbeSpec)
const poolProbeCase = { name: 'pooled-table-probe', width: 2, height: 2, pattern: 'ramp', production_binding_set: true }
const poolProbeSurface = render(poolProbeCompiled.factory, poolProbeCase).output
const poolProbeLanes = Array.from(poolProbeSurface.data)
const poolFloatSurvived = poolProbeLanes.every((value, index) =>
  (index % 4 === 0 ? value === 111 : index % 4 === 1 ? value === 444 : true))
const poolIntSurvived = poolProbeLanes.every((value, index) =>
  (index % 4 === 2 ? value === -11 : index % 4 === 3 ? value === -44 : true))
if (poolFloatSurvived) {
  throw new Error('a factory-scope PooledFloat32Array table survived the render; amendment 15\'s hazard '
    + 'argument no longer holds and the element-type allowlist must be re-derived')
}
if (!poolIntSurvived) {
  throw new Error('the factory-scope pooled ivec2 table did NOT survive the render; SOBEL_OFFSETS itself '
    + 'would be clobbered and this program\'s parity would not be reproducible per pixel')
}
const pooledTableHazard = {
  status: 'hazard-reproduced',
  design_reference: 'normalmap-design.md amendment 15',
  mechanism: 'beginPixel snapshots signedBaseIndices on first call and resets the integer index to that '
    + 'base (glsl-runtime.js:132-137), so a factory-scope pooled Int32Array survives. The float pool has '
    + 'no such base -- beginPixel does this.indices.fill(0) -- so the first per-pixel scratch allocation '
    + 'aliases and overwrites a factory-scope PooledFloat32Array.',
  probe: { name: poolProbeSpec.name, ...mutantIdentity(poolProbeSpec, poolProbeCompiled) },
  classification: 'instrumented canonical-JS probe factory; NOT a parity array and never compared to a rendered shade',
  published_lanes: 'r = POOL_FLOAT_TABLE[0][0] (initialized 111), g = POOL_FLOAT_TABLE[1][1] (initialized 444), '
    + 'b = POOL_INT_TABLE[0][0] (initialized -11), a = POOL_INT_TABLE[1][1] (initialized -44)',
  probe_geometry: [poolProbeCase.width, poolProbeCase.height],
  observed_lanes: poolProbeLanes,
  observed_f32_words_le: Array.from(words(poolProbeSurface.data), u32Hex),
  pooled_float_table_survived: poolFloatSurvived,
  pooled_int_table_survived: poolIntSurvived,
  element_type_allowlist: ['float', 'int', 'uint', 'ivec2', 'ivec3', 'ivec4', 'uvec2', 'uvec3', 'uvec4'],
  claim: 'This mechanism must NOT be extended to a float-vector element type (vec2[N], vec3[N], vec4[N] '
    + 'const globals) without re-deriving the pool argument from glsl-runtime.js. The predicate set would '
    + 'admit such a table and the port would silently disagree with the authority. The element-type check '
    + 'must be an allowlist, never a denylist and never "any approved type".',
}

// ---------------------------------------------------------------------------
// The double accumulator (design amendment 16, final bullet)
// ---------------------------------------------------------------------------

const accumulatorSpec = {
  name: 'normalmap-accumulator-f32-narrowed',
  anchor: accumulatorStatements,
  replacement: '\tdx = Math.fround(dx + value * SOBEL_X_KERNEL[i]);\n  '
    + '\tdy = Math.fround(dy + value * SOBEL_Y_KERNEL[i]);',
}
const accumulatorCompiled = compileMutant(accumulatorSpec)
const accumulatorRows = measureAcrossCases(accumulatorCompiled.factory, accumulatorSpec.name)
const accumulatorWitnesses = accumulatorRows.filter((row) => row.differs).map((row) => row.case)
if (accumulatorWitnesses.length === 0) {
  throw new Error('the accumulator narrowing mutant diverged nowhere; the double-accumulation claim has no witness')
}
const accumulatorDoubleCensus = {
  purpose: 'design amendment 16 records `dx += value * SOBEL_X_KERNEL[i]` as raw double accumulation with '
    + 'no per-step F32, unlike everything routed through $runtime. Unlike the kernel-element type, this '
    + 'half IS oracle-discriminable, and it is measured here.',
  in_disjoint_ledger: false,
  overlaps: 'every witness below is also a witness of normalmap-sobel-x-y-swapped, so this census is NOT '
    + 'attributive on its own. It is recorded because a green parity run on its witness cases is real '
    + 'evidence that the native accumulator is a double.',
  rendered_mutant: { name: accumulatorSpec.name, ...mutantIdentity(accumulatorSpec, accumulatorCompiled), rows: accumulatorRows },
  witness_cases: accumulatorWitnesses,
  control_cases: accumulatorRows.filter((row) => !row.differs).map((row) => row.case),
  reason: 'The witnesses are exactly the cases whose value map leaves the dyadic grid. Every input lane is '
    + 'a small dyadic rational and both kernels are powers of two, so on the channelCount <= 2 arms every '
    + 'partial sum is exact in binary32 as well as binary64 and narrowing changes nothing. The oklab arms '
    + 'produce full-precision doubles, where narrowing each step is observable.',
}

// ---------------------------------------------------------------------------
// What each value_map_component arm is actually worth
//
// `channelCount == 2` returns `texel.x`, exactly like the `<= 1` arm. It is a
// distinct SOURCE path, not a distinct behaviour, and saying so is not enough:
// the equivalence is measured here so nothing downstream reads the case as
// coverage of a second value map. The same sweep shows where arms 3 and 4 DO
// separate -- only when the input leaves [0, 1] and `clamp(texel.xyz, 0, 1)`
// bites.
// ---------------------------------------------------------------------------

const armSweepPatterns = ['ramp', 'wide']
const armSweepValues = [0, 1, 2, 3, 4]
const valueMapArmCensus = {
  probe_geometry: [8, 6],
  arms: armSweepValues,
  sweeps: armSweepPatterns.map((pattern) => {
    const rows = armSweepValues.map((channel) => {
      const definition = {
        name: `arm-sweep-${pattern}-${channel}`, width: 8, height: 6, pattern,
        size: [0, 0, channel, 0], production_binding_set: channel === 0,
      }
      const output = render(canonicalFactory, definition).output
      return { size_z: channel, resolved_channel_count: channel <= 1 ? 1 : channel, ...digests(output) }
    })
    const classes = {}
    for (const row of rows) (classes[row.f32_sha256] ??= []).push(row.size_z)
    return {
      input_pattern: pattern,
      input_range: pattern === 'wide' ? 'lanes outside [0, 1]' : 'lanes inside [0, 1]',
      rows,
      equivalence_classes: Object.values(classes),
    }
  }),
  rule: 'value_map_component has FIVE source arms and exactly TWO behaviours. size.z 0, 1 and 2 collapse '
    + 'because both the `<= 1` and the `== 2` arm return texel.x. size.z 3 and 4 collapse because arm 4\'s '
    + 'clamp(texel.xyz, 0, 1) is REDUNDANT: oklab_l_component already applies clamp01 to each channel '
    + 'before srgb_to_linear, so pre-clamping the argument cannot change the result -- measured '
    + 'byte-identical even on an input whose lanes leave [0, 1].',
  measured_behaviour_count: 2,
  redundant_clamp: 'the `channelCount == 4` arm\'s clamp(texel.xyz, vec3(0), vec3(1)) is idempotent with '
    + 'oklab_l_component\'s own per-channel clamp01 and changes no pixel. The channelCount-4 case is '
    + 'still the only case whose input lanes leave [0, 1] and include exact -0, which is what reaches '
    + 'srgb_to_linear\'s low arm and cbrt_safe\'s value == 0 arm; it is NOT coverage of a distinct '
    + 'value map.',
}
{
  const digestFor = (pattern, channel) => valueMapArmCensus.sweeps
    .find((sweep) => sweep.input_pattern === pattern).rows
    .find((row) => row.size_z === channel).f32_sha256
  for (const pattern of armSweepPatterns) {
    for (const channel of [1, 2]) {
      if (digestFor(pattern, channel) !== digestFor(pattern, 0)) {
        throw new Error(`value_map arm ${channel} is no longer byte-identical to the <= 1 arm on ${pattern}; `
          + 'the channelCount-2 case would then be covering a second value map and must be relabelled')
      }
    }
    if (digestFor(pattern, 3) === digestFor(pattern, 0)) {
      throw new Error(`value_map arm 3 collapsed onto the texel.x arms on ${pattern}`)
    }
    // Arm 4 pre-clamps an argument that oklab_l_component clamps again, so it
    // must agree with arm 3 EVERYWHERE -- including on the out-of-range input,
    // which is the only place a non-redundant clamp could show itself.
    if (digestFor(pattern, 4) !== digestFor(pattern, 3)) {
      throw new Error(`value_map arms 3 and 4 differ on ${pattern}; oklab_l_component's per-channel `
        + 'clamp01 no longer makes the channelCount == 4 pre-clamp redundant, and the census reason '
        + 'must be re-derived')
    }
  }
  // Pin the reason in the source, not only in the measurement.
  for (const fragment of ['var r = srgb_to_linear(clamp01(rgb[0]));',
    'var g = srgb_to_linear(clamp01(rgb[1]));', 'var b = srgb_to_linear(clamp01(rgb[2]));']) {
    if (canonicalText.split(fragment).length - 1 !== 1) {
      throw new Error(`oklab_l_component per-channel clamp01 census drift: ${fragment}`)
    }
  }
}

// ---------------------------------------------------------------------------
// fragColor persistence: quarantined, because the native pixel ABI cannot
// currently express it
// ---------------------------------------------------------------------------

const fragColorResetSpec = {
  name: 'normalmap-fragcolor-reset-per-pixel',
  anchor: mainOpener,
  replacement: `${mainOpener}  \tfragColor[0] = 0; fragColor[1] = 0; fragColor[2] = 0; fragColor[3] = 0;\n`,
}
const fragColorResetCompiled = compileMutant(fragColorResetSpec)
const smearDefinition = {
  name: 'normalmap-early-return-smear-8x6',
  width: 8, height: 6, pattern: 'flat', size: [5, 6, 1, 0],
}
const smearRendered = render(canonicalFactory, smearDefinition).output
const smearExpected = expectedRecord(smearRendered)
const smearRepeat = render(canonicalFactory, smearDefinition).output
requireExact(smearRepeat, smearExpected, 'fragcolor-persistence/canonical-repeat')
const smearReset = render(fragColorResetCompiled.factory, smearDefinition).output
const smearResetComparison = compareExact(smearReset, smearExpected, 'fragcolor-persistence/reset')
if (smearResetComparison.exact) {
  throw new Error('resetting fragColor per pixel did not change the early-return configuration; the '
    + 'persistence witness is vacuous')
}
const smearFullyCovered = render(canonicalFactory, { ...smearDefinition, name: 'smear/full-coverage', size: [8, 6, 1, 0] }).output
const smearCoverageComparison = compareExact(smearFullyCovered, smearExpected, 'fragcolor-persistence/full-coverage')
if (smearCoverageComparison.exact) {
  throw new Error('binding size.x = 8 instead of 5 produced the same image; no pixel took the early return')
}
const fragColorPersistenceWitness = {
  status: 'quarantined-not-a-parity-case',
  case: smearDefinition.name,
  width: smearDefinition.width,
  height: smearDefinition.height,
  size_binding_f32_words_le: Array.from(words(f32Vector(smearDefinition.size, 4)), u32Hex),
  input_texture: inputRecord(makeInput(smearDefinition.width, smearDefinition.height, smearDefinition.pattern)),
  output_expected: surfaceRecord(smearRendered),
  contract: 'fragColor is a factory-scope `new Float32Array([0, 0, 0, 0])`. It is NOT reset per pixel, so '
    + 'a pixel that takes main()\'s early return writes the PREVIOUS pixel\'s colour. With size.x = 5 on '
    + 'an 8-wide surface, the last three columns of every row smear the last rendered pixel of that row.',
  reset_mutant: {
    name: fragColorResetSpec.name,
    ...mutantIdentity(fragColorResetSpec, fragColorResetCompiled),
    changed_lane_count: smearResetComparison.changed_lane_count,
    changed_rgba8_byte_count: smearResetComparison.changed_rgba8_byte_count,
    first_mismatch: smearResetComparison.first_float32_mismatch,
    ...digests(smearReset),
  },
  full_coverage_control: {
    size_binding_f32_words_le: Array.from(words(f32Vector([8, 6, 1, 0], 4)), u32Hex),
    differs_from_early_return_render: !smearCoverageComparison.exact,
    changed_lane_count: smearCoverageComparison.changed_lane_count,
    ...digests(smearFullyCovered),
  },
  reachability: 'UNREACHABLE through the shipped binding set. `filter/normalMap` declares no params, so '
    + 'createCanonicalBindings leaves `size` as the zero vec4 and width/height always come from '
    + 'textureSize(inputTex, 0); global_id is then always in range. Only a host that binds a non-zero '
    + '`size` smaller than the destination reaches the early return.',
  native_expressible: false,
  native_reason: 'src/pass_runner.cpp declares `glsl::Vec4 output;` INSIDE the per-pixel loop and the '
    + 'emitted `pixel()` assigns `output` only on the path that reaches the end of main(). A bare `return;` '
    + 'therefore leaves `output` default-initialized -- and glsl::Vec holds `std::array<T, N> lanes_{}`, a '
    + 'default member initializer, so the defaulted constructor VALUE-initializes and the lanes read as '
    + 'exactly zero. This is a PARITY divergence, not undefined behaviour and not a read of an '
    + 'uninitialized object: JavaScript writes the previous pixel\'s colour where native writes '
    + '(0, 0, 0, 0). The arrays are published so the boundary is visible and testable, NOT so a parity '
    + 'test can be written against them unchanged.',
  why_not_a_ledger_mutant: 'normalmap-fragcolor-reset-per-pixel would be an ideal second disjoint ledger '
    + 'entry -- its only witness is this configuration -- but putting it in the ledger would gate the slice '
    + 'on a native ABI gap that is out of this package\'s scope. It is recorded in full instead.',
}

// ---------------------------------------------------------------------------
// One-axis control group and the binding inertness census
// ---------------------------------------------------------------------------

const anchorName = 'normalmap-default-16x9'
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
    controlRow('motion-extreme', { motion: [1, -1, 1024, -0.5] },
      'identical', 'bound motion vec4 (0,0,0,0) -> (1,-1,1024,-0.5)',
      'motion is a declared uniform the program never reads. It is proven invariant, not deleted: '
      + 'it remains a required vec4 ABI binding'),
    controlRow('tile-offset-extreme', { tileOffset: [131072.1, 0.3] },
      'identical', 'bound tileOffset (0,0) -> (131072.1, 0.3)',
      'tileOffset reaches only `globalCoord`, which main() computes and never reads. The extreme value '
      + 'is the one that discriminated the globalCoord f32-lane contract in Shape184; here it is inert, '
      + 'which is what makes the emitted [[maybe_unused]] local correct'),
    controlRow('full-resolution-extreme', { fullResolution: [1280, 720] },
      'identical', 'bound fullResolution (16,9) -> (1280,720)',
      'fullResolution is a declared uniform the program never reads'),
    controlRow('size-w-extreme', { size: [0, 0, 0, 12345.5] },
      'identical', 'bound size.w 0 -> 12345.5 with size.xyz held at zero',
      'size.w is never read; size.xy select the dimension fallback and size.z the channel count'),
    controlRow('size-z-three', { size: [0, 0, 3, 0] },
      'differs', 'bound size.z 0 -> 3',
      'the live half of the size axis: channelCount 1 -> 3 switches value_map_component to the '
      + 'oklab_l_component arm'),
    controlRow('size-xy-smaller', { size: [8, 9, 0, 0] },
      'differs', 'bound size.xy (0,0) -> (8,9) on a 16-wide surface',
      'the early-return half of the size axis: columns 8..15 stop being rendered and inherit the '
      + 'previous pixel. See fragcolor_persistence_witness'),
  ],
}
for (const control of controlGroup.controls) {
  if (!control.pass) {
    throw new Error(`control ${control.name} expected ${control.expectation} but observed ${control.observed}`)
  }
}

const inertBindings = ['motion', 'fullResolution', 'tileOffset']
const bindingInertnessCensus = {
  probe_case: anchorName,
  rule: 'a binding is recorded inert only after the anchor case is re-rendered with a deliberately extreme '
    + 'value and compared exactly. Inertness is a parity assertion: a port that wrongly made one of these '
    + 'live would differ from an oracle that is invariant.',
  inert: inertBindings.map((name) => {
    const probes = (name === 'motion'
      ? [[1, -1, 1024, -0.5], [-2147483648, 2147483647, 0.5, -0.5], [1e-30, -1e30, 3, 4]]
      : name === 'fullResolution' ? [[1280, 720], [1, 1], [131072.1, 0.3]]
        : [[131072.1, 0.3], [-16, -9], [1e30, -1e-30]]).map((value) => {
      const definition = { ...controlAnchor, [name]: value, name: `${anchorName}/${name}-${value.join('-')}` }
      const output = render(canonicalFactory, definition).output
      const comparison = compareExact(output, controlBaselineExpected, `inertness/${name}`)
      return {
        value,
        f32_words_le: Array.from(words(f32Vector(value, vecLanes[bindingAbi[name]])), u32Hex),
        differs_from_baseline: !comparison.exact,
        changed_lane_count: comparison.changed_lane_count ?? 0,
        f32_sha256: sha256(bytesOf(output.data)),
      }
    })
    return { binding: name, abi: bindingAbi[name], probes, live: probes.some((probe) => probe.differs_from_baseline) }
  }),
  live: ['inputTex', 'size'],
  reason: {
    motion: 'declared and never referenced anywhere in the factory body',
    fullResolution: 'declared and never referenced anywhere in the factory body',
    tileOffset: 'read exactly once, into `globalCoord`, which main() never reads again',
    size: 'size.xy override the textureSize dimension fallback and size.z selects the channel-count arm; '
      + 'size.w is never read',
    inputTex: 'the only data input',
  },
}
for (const entry of bindingInertnessCensus.inert) {
  if (entry.live) throw new Error(`${entry.binding} is recorded inert but a probe changed the output`)
}
for (const name of inertBindings) {
  const referenced = canonicalText.split(`${name}[`).length - 1
  // tileOffset is read twice, both lanes, into the single `globalCoord`
  // statement that main() never reads again. The others are never read at all.
  const expectedReferences = name === 'tileOffset' ? 2 : 0
  if (referenced !== expectedReferences) {
    throw new Error(`${name} lane-read census drift: ${referenced} reads, expected ${expectedReferences}`)
  }
}

// ---------------------------------------------------------------------------
// Fixture assembly
// ---------------------------------------------------------------------------

const caseNames = cases.map((item) => item.name)

// Two axes are MEASURED off the stored outputs rather than asserted, because a
// coverage label nobody re-derives is exactly the kind of claim this project
// keeps finding stale.
function saturationBucket(name) {
  const expected = canonicalExpected.get(name)
  let low = false
  let high = false
  for (let index = 0; index < expected.float_words.length; index += 1) {
    if (index % 4 > 1) continue // only x_value and y_value pass through clamp01 with a live gradient
    const word = u32Hex(expected.float_words[index])
    if (word === '0x00000000') low = true
    if (word === '0x3f800000') high = true
  }
  if (low && high) return 'saturates_at_both_bounds'
  if (low || high) return 'saturates_at_one_bound'
  return 'interior_only'
}
function wrapLimits(definition) {
  const size = definition.size ?? [0, 0, 0, 0]
  const width = Math.max(Math.round(f(size[0])), 0) | 0
  const height = Math.max(Math.round(f(size[1])), 0) | 0
  return `${width === 0 ? definition.width : width}x${height === 0 ? definition.height : height}`
}
function bucketBy(classify) {
  const buckets = {}
  for (const definition of cases) {
    const bucket = classify(definition)
    ;(buckets[bucket] ??= []).push(definition.name)
  }
  return buckets
}

const coverageAxes = {
  binding_set: {
    production_size_is_the_zero_vec4: caseNames.filter((name) =>
      cases.find((item) => item.name === name).production_binding_set === true),
    synthetic_non_zero_size: caseNames.filter((name) =>
      cases.find((item) => item.name === name).production_binding_set !== true),
  },
  channel_count_arm: {
    'one (texel.x, the only production-reachable arm)': ['normalmap-default-16x9', 'normalmap-default-7x5',
      'normalmap-high-contrast-8x6', 'normalmap-explicit-size-larger-8x6', 'normalmap-flat-alpha-8x6'],
    'two (texel.x again: a distinct source path, byte-identical to the <= 1 arm)':
      ['normalmap-channelcount-2-8x6'],
    'three (oklab on raw texel.xyz)': ['normalmap-channelcount-3-oklab-8x6'],
    'four (oklab again: the pre-clamp is redundant, byte-identical to arm three)':
      ['normalmap-channelcount-4-clamped-8x6'],
  },
  dimension_source: {
    textureSize_fallback: caseNames.filter((name) => name !== 'normalmap-explicit-size-larger-8x6'),
    explicit_size_xy: ['normalmap-explicit-size-larger-8x6'],
  },
  // Measured from the stored x_value/y_value lanes, not asserted.
  clamp01_saturation: bucketBy((definition) => saturationBucket(definition.name)),
  input_range: {
    inside_unit_interval: caseNames.filter((name) => name !== 'normalmap-channelcount-4-clamped-8x6'),
    outside_unit_interval_including_negative_zero: ['normalmap-channelcount-4-clamped-8x6'],
  },
  alpha_construction: {
    uniform_one: caseNames.filter((name) => name !== 'normalmap-flat-alpha-8x6'),
    varying: ['normalmap-flat-alpha-8x6'],
  },
  gradient_liveness: {
    dx_and_dy_both_live: caseNames.filter((name) => name !== 'normalmap-flat-alpha-8x6'),
    dx_and_dy_exactly_plus_zero: ['normalmap-flat-alpha-8x6'],
  },
  // The wrap_coord moduli, derived from size.xy with the textureSize fallback.
  // The program reads no `resolution` binding at all, so surface aspect is not
  // a semantic axis here; the wrap limits are.
  wrap_limits: bucketBy(wrapLimits),
}
if (Object.keys(coverageAxes.clamp01_saturation).length < 2) {
  throw new Error('every case lands in the same clamp01 saturation bucket; the axis is not covered')
}
if (Object.keys(coverageAxes.wrap_limits).length < 3) {
  throw new Error('fewer than three distinct wrap_coord moduli are covered')
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
  defines: {},
  preprocessor_define_count: 0,
  runtime_binding_names: [...bindingNames],
  runtime_binding_abi: bindingAbi,
  oracle_authority: `unmodified public ${factoryName} from an immutable noisemaker-for-cpu snapshot, `
    + 'executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates',
  const_global_table_contracts: {
    SOBEL_OFFSETS: {
      javascript_declaration: offsetsDeclaration,
      glsl_type: 'const ivec2[9]',
      element_materialization: 'runtime ivec2 objects built through cpu_ivec2, i.e. POOLED Int32Arrays '
        + 'protected by beginPixel\'s snapshotted signed base index',
      numeric_contract: 'exact int32 lanes; no narrowing question arises',
      native_element_type: 'glsl::IVec2',
      oracle_discriminable: true,
      discriminating_mutant: 'normalmap-sobel-x-y-swapped (via the transpose identity) and '
        + 'normalmap-offsets-transposed, which are the same function; see transpose_equivalence_proof',
    },
    SOBEL_X_KERNEL: {
      javascript_declaration: xKernelDeclaration,
      glsl_type: 'const float[9]',
      element_materialization: 'plain JS Array of Numbers, NOT a Float32Array',
      numeric_contract: 'doubles, NEVER narrowed to f32',
      native_element_type: 'double',
      oracle_discriminable: false,
      discriminating_mutant: null,
      why_not_discriminable: 'every element is exactly representable in binary32; see kernel_table_narrowing_axis',
    },
    SOBEL_Y_KERNEL: {
      javascript_declaration: yKernelDeclaration,
      glsl_type: 'const float[9]',
      element_materialization: 'plain JS Array of Numbers, NOT a Float32Array',
      numeric_contract: 'doubles, NEVER narrowed to f32',
      native_element_type: 'double',
      oracle_discriminable: false,
      discriminating_mutant: null,
      why_not_discriminable: 'every element is exactly representable in binary32; see kernel_table_narrowing_axis',
    },
    transpose_identity: 'SOBEL_X_KERNEL viewed as 3x3 is exactly the transpose of SOBEL_Y_KERNEL. Checked '
      + 'elementwise by the generator, because two of design section 7\'s three mutants rest on it.',
  },
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays; never reconstructed from expected words',
    tolerance: 'none',
    comparison_order: 'dimensions, exact expected/actual lane count, exact expected/actual byte count, every Float32 word, every independent RGBA8 byte',
    coordinates: 'all stored rows and first mismatches use top-down storage order and top-down x/y',
    input_textures: 'stored in full as raw little-endian uint32 lane arrays; every input lane is a small '
      + 'dyadic rational and therefore exact in binary32 and binary64',
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
      lines: sourceLines - 1,
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
  control_group: controlGroup,
  binding_inertness_census: bindingInertnessCensus,
  transpose_equivalence_proof: transposeEquivalenceProof,
  kernel_table_mutant_census: kernelTableMutantCensus,
  kernel_table_narrowing_axis: kernelTableNarrowingAxis,
  as_u32_round_axis: asU32RoundAxis,
  per_pixel_reevaluation_equivalence: perPixelReevaluationEquivalence,
  pooled_table_hazard: pooledTableHazard,
  accumulator_double_census: accumulatorDoubleCensus,
  value_map_arm_census: valueMapArmCensus,
  fragcolor_persistence_witness: fragColorPersistenceWitness,
  mutation_ledger: mutationLedger,
  mutation_discrimination_contract: {
    per_case: true,
    rule: 'discrimination is frozen and validated PER CASE AND PER MUTANT. A per-mutant summary is not '
      + 'sufficient and is never accepted here. A case that flips is a stop condition.',
    disjoint_witness_requirement: 'The ledger mutants must have DISJOINT witness sets. They carry '
      + 'different contracts -- the kernel tables versus the alpha source coordinate -- and a case that '
      + 'witnessed both could not attribute a divergence to one of them. This is enforced, not merely '
      + 'observed: the generator throws and the materializer rejects the document if any case appears in '
      + 'two witness sets.',
    disjointness_construction: 'Disjointness is engineered and stated, not accidental. Every kernel '
      + 'witness case carries a uniformly opaque input, so transposing the alpha-source coordinate fetches '
      + 'alpha 1 either way; the one case with a varying alpha has a constant value map, so dx and dy are '
      + 'exactly +0 and swapping the kernels is a no-op. Both halves are re-measured every run.',
    witness_sets: Object.fromEntries(mutationLedger.map((mutant) => [mutant.name, {
      witness_cases: [...mutant.witness_cases],
      control_cases: [...mutant.control_cases],
    }])),
    expected: Object.fromEntries(mutantSpecs.map((spec) => [spec.name, spec.expected])),
    excluded_from_ledger: {
      'normalmap-offsets-transposed': 'bit-identical to normalmap-sobel-x-y-swapped; see transpose_equivalence_proof',
      'normalmap-sobel-x-negated': 'witness set measured IDENTICAL to the retained ledger mutant\'s -- wholly indiscriminable from it here; see kernel_table_mutant_census',
      'normalmap-sobel-x1-perturbed': 'witness set measured a strict superset of the retained ledger mutant\'s; see kernel_table_mutant_census',
      'normalmap-round-half-away': 'structurally unsatisfiable; see as_u32_round_axis',
      'normalmap-kernel-tables-f32-narrowed': 'cannot diverge; see kernel_table_narrowing_axis',
      'normalmap-accumulator-f32-narrowed': 'shares witnesses with the retained ledger mutant; see accumulator_double_census',
      'normalmap-fragcolor-reset-per-pixel': 'its only configuration is not natively expressible today; see fragcolor_persistence_witness',
    },
  },
  claim_boundaries: {
    kernel_double_type: kernelTableNarrowingAxis.claim,
    round_contract: asU32RoundAxis.claim,
    per_pixel_reevaluation: perPixelReevaluationEquivalence.operative_reason,
    float_vector_tables: pooledTableHazard.claim,
    production_reachability: 'filter/normalMap declares no params, so `size` is the zero vec4 on every '
      + 'shipped render. channelCount is therefore always 1, the whole oklab_l_component / srgb_to_linear '
      + '/ cbrt_safe subtree and the channelCount 2/3/4 arms are dynamically dead, and main()\'s early '
      + 'return is unreachable. The synthetic-size cases here cover the ABI, not the shipped route, and '
      + 'must never be cited as evidence about production behaviour.',
    fragcolor_persistence: 'fragColor\'s cross-pixel persistence is real in the JavaScript and is stored '
      + 'in fragcolor_persistence_witness, but the native pixel ABI cannot express it today. It is NOT a '
      + 'parity case and NOT a ledger mutant.',
    normalized_source: 'Normalized/typed source, function, interface, and whole-program hashes are the '
      + 'frontend profiles\' authority and are deliberately not restated here.',
  },
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function reportFor(data) {
  const caseRows = data.render_cases.map((item) =>
    `| ${item.name} | ${item.width}x${item.height} | ${item.route} | ${item.input_pattern} | `
    + `${item.output_expected.f32_sha256} | ${item.output_expected.rgba8_sha256} |`).join('\n')
  const coverageRows = Object.entries(data.coverage_axes)
    .map(([axis, buckets]) => Object.entries(buckets)
      .map(([bucket, names]) => `| ${axis} | ${bucket} | ${names.join(', ')} |`).join('\n')).join('\n')
  const controlRows = data.control_group.controls.map((item) =>
    `| ${item.name} | ${item.axis} | ${item.expectation} | ${item.observed} | ${item.pass ? 'pass' : 'FAIL'} | ${item.changed_lane_count} |`).join('\n')
  const mutantRows = data.mutation_ledger.map((mutant) => mutant.results.map((result) =>
    `| ${mutant.name} | ${result.case} | ${result.expected_discriminates ? 'witness' : 'control'} | ${result.differs ? 'differs' : 'identical'} | ${result.changed_lane_count} |`).join('\n')).join('\n')
  const censusRows = data.kernel_table_mutant_census.mutants.map((mutant) => mutant.results.map((result) =>
    `| ${mutant.name} | ${result.case} | ${result.differs ? 'differs' : 'identical'} | ${result.changed_lane_count} |`).join('\n')).join('\n')
  const censusRelationRows = data.kernel_table_mutant_census.mutants.map((mutant) =>
    `| ${mutant.name} | ${mutant.witness_cases.length} | ${mutant.witness_relation} |`).join('\n')
  const armRows = data.value_map_arm_census.sweeps.map((sweep) => sweep.rows.map((row) =>
    `| ${sweep.input_pattern} (${sweep.input_range}) | ${row.size_z} | ${row.resolved_channel_count} | ${row.f32_sha256} |`).join('\n')).join('\n')
  const transposeRowsText = data.transpose_equivalence_proof.rows.map((row) =>
    `| ${row.case} | ${row.changed_lane_count_against_swap} | ${row.changed_lane_count_against_canonical} |`).join('\n')
  const inertRows = data.binding_inertness_census.inert.map((entry) => entry.probes.map((probe) =>
    `| ${entry.binding} | [${probe.value.join(', ')}] | ${probe.differs_from_baseline ? 'differs' : 'identical'} | ${probe.changed_lane_count} |`).join('\n')).join('\n')
  const accumulatorRowsText = data.accumulator_double_census.rendered_mutant.rows.map((row) =>
    `| ${row.case} | ${row.differs ? 'differs' : 'identical'} | ${row.changed_lane_count} |`).join('\n')
  return `# Normalmap185 exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; **no preprocessor defines**.

## The contracts this program exists to prove

\`filter/normalMap\` declares three **const** file-scope tables, and the parity target is the
transpiler's materialization, not GLSL semantics:

| Table | GLSL | JavaScript | Contract | Oracle-discriminable |
| --- | --- | --- | --- | --- |
| \`SOBEL_OFFSETS\` | \`const ivec2[9]\` | \`[cpu_ivec2(...), ...]\` | pooled \`Int32Array\` elements, exact int32 | yes |
| \`SOBEL_X_KERNEL\` | \`const float[9]\` | plain \`Array\` | **doubles**, never narrowed to f32 | **no** |
| \`SOBEL_Y_KERNEL\` | \`const float[9]\` | plain \`Array\` | **doubles**, never narrowed to f32 | **no** |

The two float tables are **not** oracle-discriminable, and this package never pretends otherwise.
Every element (\`0.5\`, \`0\`, \`1\` and their negations) is exactly representable in binary32 as well
as binary64, so no value in this program separates \`std::array<double, 9>\` from
\`std::array<float, 9>\`. \`kernel_table_narrowing_axis\` renders the narrowing mutant on every case
and records ${data.kernel_table_narrowing_axis.rendered_divergences} changed lanes: it **cannot
diverge**, so it is not shipped as a control. The double contract is proven structurally, by the
emitted native type and by the JavaScript being a plain \`Array\`. A green parity run is not evidence
for it.

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
beneath the immutable snapshot. Bare module specifiers other than \`node:\` builtins are rejected,
and the live checkout is refused as a \`--cpu-root\`.

No absolute path is recorded anywhere in this package. The \`--cpu-root\` argument is stored as
\`${data.provenance.cpu_snapshot.argument}\` and the rejected live checkout as
\`${data.provenance.cpu_snapshot.live_checkout_rejected}\`, resolved at run time from
${data.provenance.cpu_snapshot.live_checkout_resolution}. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings, and what production actually binds

The program has exactly ${data.runtime_binding_names.length} runtime bindings:
${data.runtime_binding_names.map((name) => `\`${name}\``).join(', ')}. There are no compile-time
defines.

\`filter/normalMap\` declares **no params**, so \`createCanonicalBindings\` leaves \`size\` as the
zero vec4 on every shipped render. Three consequences, all recorded as claim boundaries rather than
discovered later: \`channelCount\` is always 1, the entire \`oklab_l_component\` /
\`srgb_to_linear\` / \`cbrt_safe\` subtree is dynamically dead, and \`main()\`'s early return is
unreachable. Cases that bind a non-zero \`size\` are **synthetic ABI coverage** and are labelled
\`synthetic-size\` in the table below.

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
${caseRows}

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
${data.runtime_binding_names.length} bindings with every vector lane as a hexadecimal f32 word, the
external \`runPass\` time/seed pair, the complete expected Float32 word array, the complete
independently captured RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each
array. Every input lane is a small dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
${coverageRows}

## One-axis control group on \`${data.control_group.anchor}\`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${controlRows}

## Binding inertness census

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
${inertRows}

${data.binding_inertness_census.rule}

## Amendment 11: two of design section 7's three mutants are the same function

| Case | Lanes differing from \`normalmap-sobel-x-y-swapped\` | Lanes differing from canonical |
| --- | ---: | ---: |
${transposeRowsText}

${data.transpose_equivalence_proof.algebra}

${data.transpose_equivalence_proof.consequence}

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
${mutantRows}

Both ledger mutants are independent one-anchor/one-replacement rewrites of the canonical factory
text, compiled and rendered by this generator. The expected outcome is frozen **per case and per
mutant**; \`--check\` fails if any single cell flips, in either direction.

${data.mutation_discrimination_contract.disjoint_witness_requirement}

${data.mutation_discrimination_contract.disjointness_construction}

### Kernel-table mutants deliberately kept out of the disjoint ledger

| Mutant | Case | Result | Changed lanes |
| --- | --- | --- | ---: |
${censusRows}

| Mutant | Witness count | Relation to \`normalmap-sobel-x-y-swapped\`'s witness set |
| --- | ---: | --- |
${censusRelationRows}

Amendment 11 suggests replacing the retracted mutant with a kernel-element perturbation. Measured,
each candidate's witness set **contains** \`normalmap-sobel-x-y-swapped\`'s, and the two rows are not
the same relation: the perturbation is a genuine strict superset, while
\`normalmap-sobel-x-negated\` witnesses **exactly the same seven cases** -- on this case set it is
wholly indiscriminable from the retained mutant, which is stronger than a superset, not weaker.
Either way neither can be a second *disjoint* ledger entry on any case set that also covers the
program's real behaviour. Both relations are re-derived from the stored rows on every run. They ship
as a census with per-case results, and the ledger's second slot is filled by a mutant on a different
contract entirely -- which is what amendment 11's own criterion, "something no offset permutation can
produce", admits.

## The \`as_u32\` round axis is unsatisfiable, and proven invariant

\`as_u32\` has **${data.as_u32_round_axis.call_site_count} call sites**, not one:
${data.as_u32_round_axis.call_sites.map((site) => `\`${site.statement}\``).join(', ')}.

${data.as_u32_round_axis.why_empty}

A ${data.as_u32_round_axis.scalar_scan.samples}-sample scan over half-integers, quarter-integers,
ties, signed zero, NaN, the infinities and the 2^23 boundary finds
**${data.as_u32_round_axis.scalar_scan.rounder_disagreements} values where the two rounders
disagree** and **${data.as_u32_round_axis.scalar_scan.as_u32_divergences} divergences in
\`as_u32\`**. The rendered \`${data.as_u32_round_axis.rendered_mutant.name}\` mutant changes
${data.as_u32_round_axis.rendered_divergences} lanes across every case.

**${data.claim_boundaries.round_contract}**

## Per-pixel re-evaluation is measured equivalent

${data.per_pixel_reevaluation_equivalence.rewrite}: ${data.per_pixel_reevaluation_equivalence.rendered_divergences}
changed lanes across every case.

${data.per_pixel_reevaluation_equivalence.operative_reason}

## Amendment 15: the pooled-table hazard, reproduced

${data.pooled_table_hazard.mechanism}

An instrumented probe factory declares a factory-scope \`PooledFloat32Array\` table beside a pooled
\`ivec2\` table and publishes both. Observed lanes:
\`${data.pooled_table_hazard.observed_lanes.slice(0, 4).join(', ')}\` --
the float table has been clobbered from its \`111\` / \`444\` initializers, while the integer table
still reads \`-11\` / \`-44\`.

**${data.pooled_table_hazard.claim}**

## What each \`value_map_component\` arm is worth

| Input | \`size.z\` | Resolved channelCount | Float32 SHA-256 |
| --- | ---: | ---: | --- |
${armRows}

${data.value_map_arm_census.rule}

Five source arms, **two** behaviours. \`normalmap-channelcount-2-8x6\` pins a distinct **source path**
whose output is byte-identical to the \`channelCount <= 1\` arm, and \`normalmap-channelcount-4-clamped-8x6\`
pins one that is byte-identical to arm three: ${data.value_map_arm_census.redundant_clamp}
Neither is coverage of a second value map, and the generator throws if either equivalence stops
holding or if \`oklab_l_component\`'s three per-channel \`clamp01\` calls disappear.

## The double accumulator

| Case | Result | Changed lanes |
| --- | --- | ---: |
${accumulatorRowsText}

${data.accumulator_double_census.reason}

${data.accumulator_double_census.overlaps}

## \`fragColor\` persistence, quarantined

${data.fragcolor_persistence_witness.contract}

${data.fragcolor_persistence_witness.reachability}

**${data.fragcolor_persistence_witness.native_reason}**

The configuration's complete expected arrays are stored under
\`fragcolor_persistence_witness\` and emitted into the native include behind
\`kFragColorPersistenceNativelyExpressible = false\`, so the boundary is visible rather than silently
absent. ${data.fragcolor_persistence_witness.why_not_a_ledger_mutant}

## Claim boundaries

- ${data.claim_boundaries.kernel_double_type}
- ${data.claim_boundaries.round_contract}
- ${data.claim_boundaries.per_pixel_reevaluation}
- ${data.claim_boundaries.float_vector_tables}
- ${data.claim_boundaries.production_reachability}
- ${data.claim_boundaries.fragcolor_persistence}
- ${data.claim_boundaries.normalized_source}

## Regeneration

\`\`\`sh
node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --self-test
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
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Normalmap185 oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Normalmap185 oracle report drift')
}
const controlSummary = controlGroup.controls.map((item) => `${item.name}=${item.observed}`).join(' ')
const ledgerSummary = mutationLedger.map((mutant) => `${mutant.name}:${mutant.witness_cases.length}/${cases.length}`).join(' ')
console.log(`Normalmap185 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} cases, `
  + `${mutationLedger.length} disjoint ledger mutants [${ledgerSummary}], controls [${controlSummary}], `
  + `round axis invariant (${roundScan.rounder_disagreements}/${roundScan.samples} rounder disagreements, `
  + `0 as_u32 divergences), tables cannot narrow, per-pixel re-evaluation equivalent`)
