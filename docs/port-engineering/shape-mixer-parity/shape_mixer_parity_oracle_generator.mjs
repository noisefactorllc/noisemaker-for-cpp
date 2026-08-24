import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'shape-mixer-parity-oracles.json')
const reportPath = path.join(here, 'shape-mixer-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'shape_mixer_frontend_probe.py')
const programKey = 'classicNoisedeck/shapeMixer:shapeMixer'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const authorityCommit = '4834b0144ee0524588144a482cca0067b15f68ec'
const authorityNode = 'v24.7.0'
const upstreamRevision = '117a236679d1db3ab8f0e278230ece277b57564c'

const modes = new Set(['--write', '--check'])
function parseArgs() {
  let mode = null
  let cpuArg = null
  const argv = process.argv.slice(2)
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (modes.has(token)) {
      if (mode !== null) throw new Error('duplicate mode')
      mode = token
      continue
    }
    if (token === '--cpu-root') {
      if (cpuArg !== null || index + 1 >= argv.length || argv[index + 1].startsWith('-')) {
        throw new Error('exactly one --cpu-root ROOT is required')
      }
      cpuArg = argv[++index]
      continue
    }
    throw new Error(`unknown option: ${token}`)
  }
  if (mode === null) throw new Error('choose exactly one of --write or --check')
  if (cpuArg === null) throw new Error('--cpu-root required')
  const liveArg = process.env.NOISEMAKER_FOR_CPU
  if (!liveArg) throw new Error('NOISEMAKER_FOR_CPU required')
  return { mode, cpuArg, liveArg }
}

function lexicalDirectory(raw, label) {
  if (typeof raw !== 'string' || raw.length === 0) throw new Error(`${label} required`)
  const lexical = path.resolve(raw)
  let stat
  try { stat = fs.lstatSync(lexical) } catch { throw new Error(`${label} missing`) }
  if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`${label} must be a non-symlink directory`)
  return lexical
}

function beneath(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`)
}

const { mode, cpuArg, liveArg } = parseArgs()
const cppLexical = lexicalDirectory(path.resolve(here, '../../..'), 'C++ checkout')
const authorityLexical = lexicalDirectory(cpuArg, 'authority root')
const liveLexical = lexicalDirectory(liveArg, 'live root')
const cppRoot = fs.realpathSync(cppLexical)
const cpuRoot = fs.realpathSync(authorityLexical)
const liveRoot = fs.realpathSync(liveLexical)
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_shape_mixer_native_oracle_include.py')
if (cpuRoot === liveRoot || beneath(cpuRoot, liveRoot) || beneath(liveRoot, cpuRoot)) {
  throw new Error('authority and live roots must be distinct and non-overlapping')
}
if (beneath(cppRoot, cpuRoot) || beneath(cpuRoot, cppRoot)
    || beneath(cppRoot, liveRoot) || beneath(liveRoot, cppRoot)) {
  throw new Error('authority/live roots must be external to the C++ checkout')
}

const closureEntries = [
  'src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js',
  'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js',
  'src/runtime/pass-runner.js', 'src/runtime/surface.js',
]
const importPatterns = [
  /\bfrom\s*['"]([^'"\n]+)['"]/g,
  /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
]
const dynamicImportPattern = /\bimport\s*\(([^)]*)\)/g
function discoverClosure(root) {
  const stack = closureEntries.map((entry) => path.join(root, entry))
  const seen = new Map()
  const resolveConfined = (candidate, label) => {
    let stat
    try { stat = fs.lstatSync(candidate) } catch { throw new Error(`missing authority import: ${label}`) }
    if (stat.isSymbolicLink()) throw new Error(`authority import symlink: ${label}`)
    const resolved = fs.realpathSync(candidate)
    if (!beneath(root, resolved)) throw new Error('authority import escapes root')
    return resolved
  }
  const enqueue = (specifier, file) => {
    if (specifier.startsWith('node:')) return
    if (!specifier.startsWith('./') && !specifier.startsWith('../')) {
      throw new Error(`bare authority import: ${specifier}`)
    }
    const candidate = path.resolve(path.dirname(file), specifier)
    if (!beneath(root, candidate)) throw new Error('authority import escapes root')
    stack.push(resolveConfined(candidate, specifier))
  }
  while (stack.length) {
    const file = resolveConfined(stack.pop(), 'entry')
    if (seen.has(file)) continue
    const text = fs.readFileSync(file, 'utf8')
    seen.set(file, sha256(Buffer.from(text)))
    dynamicImportPattern.lastIndex = 0
    let match
    while ((match = dynamicImportPattern.exec(text))) {
      const literal = match[1].trim()
      if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) {
        throw new Error(`nonliteral authority import in ${file}`)
      }
      enqueue(literal.slice(1, -1), file)
    }
    for (const pattern of importPatterns) {
      pattern.lastIndex = 0
      while ((match = pattern.exec(text))) enqueue(match[1], file)
    }
  }
  return [...seen].map(([file, sha256Value]) => ({
    relative_path: path.relative(root, file), sha256: sha256Value,
  })).sort((left, right) => left.relative_path.localeCompare(right.relative_path))
}
const authorityClosure = discoverClosure(cpuRoot)
const load = (relative) => {
  const candidate = path.resolve(cpuRoot, relative)
  if (!beneath(cpuRoot, candidate)) throw new Error('authority import escapes root')
  return import(pathToFileURL(candidate).href)
}
const [{ canonicalAdapterFactories, canonicalKernelFactories, kernelFactories },
  { effectRecords, UPSTREAM_REVISION }, { createCanonicalBindings },
  { bindGlslKernel, GlslCpuRuntime, glslMod }, { runPass }, { Surface }]
  = await Promise.all([
    load('src/effects/catalog.js'), load('src/effects/generated/upstream-snapshot.js'),
    load('src/csl/glsl-kernel.js'), load('src/csl/glsl-runtime.js'),
    load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'),
  ])
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision,
  'sources/classicNoisedeck/shapeMixer/shapeMixer.glsl')
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const runtimePath = path.join(cpuRoot, 'src/csl/glsl-runtime.js')
const f = Math.fround
const channels = ['r', 'g', 'b', 'a']

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function words(view) { return new Uint32Array(view.buffer, view.byteOffset, view.length) }
function f32Bits(value) { return u32Hex(words(new Float32Array([value]))[0]) }
function f32Vector(values) { return new Float32Array(values.map(f)) }
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function verifySidecar(target) {
  const sidecar = sidecarPath(target)
  if (!fs.existsSync(target) || !fs.existsSync(sidecar)) throw new Error(`missing checked asset or sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecar, 'utf8') !== sidecarText(target, payload)) throw new Error(`checksum sidecar drift: ${target}`)
  return payload
}

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

function shapeMixerCompareExact(actual, expected, label) {
  if (!(actual?.data instanceof Float32Array)) throw new TypeError(`${label}: actual must be a Float32 Surface`)
  const expectedWords = expected?.float_words
  const expectedBytes = expected?.rgba8
  if (!(expectedWords instanceof Uint32Array) || !(expectedBytes instanceof Uint8Array)) throw new TypeError(`${label}: independent expected arrays required`)
  if (actual.width !== expected.width || actual.height !== expected.height) {
    return { exact: false, rejected_before_iteration: true, reason: 'dimensions', label,
      expected_dimensions: [expected.width, expected.height], actual_dimensions: [actual.width, actual.height], first_mismatch: null }
  }
  const exactCount = expected.width * expected.height * 4
  const actualWords = words(actual.data)
  if (expectedWords.length !== exactCount || actualWords.length !== exactCount) {
    return { exact: false, rejected_before_iteration: true, reason: 'lane-count', label,
      expected_dimensions: [expected.width, expected.height], actual_dimensions: [actual.width, actual.height],
      expected_lane_count: expectedWords.length, actual_lane_count: actualWords.length, first_mismatch: null }
  }
  if (expectedBytes.length !== exactCount) {
    return { exact: false, rejected_before_iteration: true, reason: 'byte-count', label,
      expected_dimensions: [expected.width, expected.height], actual_dimensions: [actual.width, actual.height],
      expected_byte_count: expectedBytes.length, actual_byte_count: exactCount, first_mismatch: null }
  }
  const actualBytes = actual.toRgba8()
  if (actualBytes.length !== exactCount) return { exact: false, rejected_before_iteration: true, reason: 'byte-count', label,
    expected_dimensions: [expected.width, expected.height], actual_dimensions: [actual.width, actual.height],
    expected_byte_count: expectedBytes.length, actual_byte_count: actualBytes.length, first_mismatch: null }
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
  return { exact: changedLanes === 0 && changedBytes === 0, rejected_before_iteration: false,
    label, expected_dimensions: [expected.width, expected.height], actual_dimensions: [actual.width, actual.height],
    changed_lane_count: changedLanes, changed_rgba8_byte_count: changedBytes,
    first_mismatch: firstFloat ?? firstByte, first_float32_mismatch: firstFloat, first_rgba8_mismatch: firstByte }
}

function shapeMixerRequireExact(actual, expected, label) {
  const result = shapeMixerCompareExact(actual, expected, label)
  if (!result.exact) throw new Error(`${label}: ${JSON.stringify(result)}`)
  return result
}

function expectedRecord(surface) {
  return { width: surface.width, height: surface.height,
    float_words: words(surface.data).slice(), rgba8: new Uint8Array(surface.toRgba8()) }
}

function comparerSelfTests() {
  const expectReject = (result, reason) => {
    if (result.exact || !result.rejected_before_iteration || result.reason !== reason) throw new Error(`Shape Mixer comparer did not preflight ${reason}`)
    return true
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  const shape = shapeMixerCompareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape')
  expectReject(shape, 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = shapeMixerCompareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32' || !bytes(plusZero.toRgba8()).equals(bytes(minusZero.toRgba8()))) throw new Error('Shape Mixer comparer missed signed zero')
  const nanAData = new Float32Array(4); const nanBData = new Float32Array(4)
  new Uint32Array(nanAData.buffer).set([0x7fc00001, 0, 0, 0x3f800000])
  new Uint32Array(nanBData.buffer).set([0x7fc00002, 0, 0, 0x3f800000])
  const nanA = new Surface(1, 1, nanAData); const nanB = new Surface(1, 1, nanBData)
  const nanPayload = shapeMixerCompareExact(nanB, expectedRecord(nanA), 'self/nan-payload')
  if (nanPayload.exact || nanPayload.first_mismatch?.kind !== 'float32' || !bytes(nanA.toRgba8()).equals(bytes(nanB.toRgba8()))) throw new Error('Shape Mixer comparer missed NaN payload')
  const finalExpected = expectedRecord(plusZero)
  const finalActual = new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)]))
  const finalLane = shapeMixerCompareExact(finalActual, finalExpected, 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch.channel !== 'a' || finalLane.first_mismatch.lane_or_byte_index !== 3) throw new Error('Shape Mixer comparer missed final alpha lane')
  const byteExpected = expectedRecord(plusZero); byteExpected.rgba8[3] ^= 1
  const byteOnly = shapeMixerCompareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch.channel !== 'a') throw new Error('Shape Mixer comparer missed independent byte mismatch')
  const shortLanes = { ...expectedRecord(plusZero), float_words: new Uint32Array(3) }
  const longLanes = { ...expectedRecord(plusZero), float_words: new Uint32Array(5) }
  const shortBytes = { ...expectedRecord(plusZero), rgba8: new Uint8Array(3) }
  const longBytes = { ...expectedRecord(plusZero), rgba8: new Uint8Array(5) }
  ;[['short-lanes', shortLanes, 'lane-count'], ['long-lanes', longLanes, 'lane-count'],
    ['short-bytes', shortBytes, 'byte-count'], ['long-bytes', longBytes, 'byte-count']]
    .forEach(([label, expected, reason]) => expectReject(shapeMixerCompareExact(plusZero, expected, `self/${label}`), reason))
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

const provenanceFiles = {
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  adapter_index: ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
}
for (const [name, [relative, expected]] of Object.entries(provenanceFiles)) {
  const actual = sha256(fs.readFileSync(path.join(cpuRoot, relative)))
  if (actual !== expected) throw new Error(`${name} provenance drift: ${actual}`)
}
if (process.version !== authorityNode) throw new Error(`Node authority drift: ${process.version}`)
if (UPSTREAM_REVISION !== upstreamRevision) throw new Error('upstream revision drift')

const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== 21718 || sha256(sourceBytes) !== '704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4') throw new Error('pinned Shape Mixer GLSL source drift')
const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
const canonicalText = canonicalFactory?.toString() ?? ''
const canonicalSource = fs.readFileSync(canonicalPath, 'utf8')
const runtimeSource = fs.readFileSync(runtimePath, 'utf8')
if (Buffer.byteLength(runtimeSource) !== 21331 || sha256(runtimeSource) !== provenanceFiles.glsl_runtime[1]) throw new Error('pinned GLSL runtime source drift')
const sliceStart = canonicalSource.indexOf('function canonicalFactory15')
const sliceEnd = canonicalSource.indexOf('function canonicalFactory16', sliceStart)
const canonicalSlice = canonicalSource.slice(sliceStart, sliceEnd)
if (canonicalFactory?.name !== 'canonicalFactory15' || Buffer.byteLength(canonicalText) !== 26033 || sha256(canonicalText) !== '063bb7cf252349866766abd1c781bb41d32af2d9b71bb02461f34ed8404c8124') throw new Error('canonical Shape Mixer factory drift')
if (Buffer.byteLength(canonicalSlice) !== 26035 || sha256(canonicalSlice) !== '5c870c15339e431a0972742008caae2f7859836995e508892cd823d98e32c985') throw new Error('canonical Shape Mixer source slice drift')
if (publicFactory !== canonicalFactory) throw new Error('public Shape Mixer factory is not canonical identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Shape Mixer adapter override')
const effect = effectRecords.find((item) => item.id === 'classicNoisedeck/shapeMixer')
if (!effect || effect.func !== 'shapeMixer' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'shapeMixer') throw new Error('Shape Mixer metadata/pass drift')

const probeRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'shape-mixer-oracle-'))
let probe
try {
  probe = spawnSync('python3', ['-B', frontendProbePath, '--check'], {
    cwd: probeRoot, encoding: 'utf8',
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONPYCACHEPREFIX: probeRoot },
  })
} finally {
  fs.rmSync(probeRoot, { recursive: true, force: true })
}
if (probe.status !== 0) throw new Error(`Shape Mixer frontend probe failed: ${probe.stderr || probe.stdout}`)
const frontendProof = JSON.parse(probe.stdout)

function patternSurface(which, width, height, phase) {
  const data = new Float32Array(width * height * 4)
  const alpha = which === 'A' ? [0.875, 0.25, 0.5] : [0.125, 0.75, 0.5]
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const index = (y * width + x) * 4
    if (which === 'A') {
      data[index] = f(((((37 * x + 17 * y + 13 * phase) % 113) + 7) / 127))
      data[index + 1] = f(((((11 * x + 43 * y + 19 * phase) % 109) + 5) / 127))
      data[index + 2] = f(((((53 * x + 7 * y + 23 * phase) % 107) + 3) / 127))
      data[index + 3] = f(alpha[(x + 2 * y + phase) % 3])
    } else {
      data[index] = f(((((29 * x + 31 * y + 17 * phase) % 103) + 11) / 131))
      data[index + 1] = f(((((47 * x + 13 * y + 7 * phase) % 101) + 9) / 127))
      data[index + 2] = f(((((19 * x + 59 * y + 29 * phase) % 97) + 13) / 127))
      data[index + 3] = f(alpha[(2 * x + y + phase) % 3])
    }
  }
  return new Surface(width, height, data)
}

function cornerTags(width, height, variant) {
  const data = new Float32Array(width * height * 4)
  data.set(Array.from({ length: width * height }, () => [0.03125, 0.0625, 0.09375, 0.375]).flat().map(f))
  const set = (x, y, rgba) => data.set(rgba.map(f), (y * width + x) * 4)
  const sets = variant === 'A'
    ? [[0, 0, [.97, .11, .29, .875]], [width - 1, 0, [.19, .89, .37, .25]], [0, height - 1, [.43, .17, .93, .5]], [width - 1, height - 1, [.73, .61, .07, .125]]]
    : [[0, 0, [.13, .83, .47, .125]], [width - 1, 0, [.67, .23, .91, .75]], [0, height - 1, [.31, .71, .17, .5]], [width - 1, height - 1, [.89, .41, .59, .875]]]
  sets.forEach(([x, y, rgba]) => set(x, y, rgba))
  set(Math.floor(width / 2), Math.floor(height / 2), variant === 'A' ? [.53, .79, .31, .5] : [.79, .37, .53, .75])
  return new Surface(width, height, data)
}

function alphaThreeWay(which) {
  const width = which === 'A' ? 3 : 4
  const data = new Float32Array(width * 4)
  const alphas = which === 'A' ? [.875, .25, .5] : [.125, .375, .75, .5]
  for (let x = 0; x < width; x += 1) data.set([f(.15 + x * .13), f(.81 - x * .11), f(.29 + x * .07), f(alphas[x])], x * 4)
  return new Surface(width, 1, data)
}

const common = {
  time: f(.3125), seed: -37, loopScale: f(37.25), paletteMode: 3,
  paletteOffset: f32Vector([.17, .43, .79]), paletteAmp: f32Vector([.61, -.27, .38]),
  paletteFreq: f32Vector([.75, 1.5, -.625]), palettePhase: f32Vector([.125, -.375, .6875]),
  animate: 0, cyclePalette: 0, rotatePalette: f(23.75), repeatPalette: f(2.5), levels: f(0), wrap: false,
  tileOffset: f32Vector([0, 0]), externalTime: 0, externalSeed: 0,
}
const filters = [['nearest', 'nearest'], ['linear', 'nearest'], ['nearest', 'linear'], ['linear', 'linear'], ['nearest', 'nearest'], ['linear', 'linear'], ['linear', 'nearest'], ['linear', 'linear'], ['linear', 'linear'], ['nearest', 'linear']]
const cases = []
for (let mode = 0; mode < 10; mode += 1) {
  cases.push({ name: `mode-${mode}-scalar`, width: 7, height: 5, a: { recipe: 'patternA', width: 9, height: 6, phase: 10 + mode, filter: filters[mode][0] }, b: { recipe: 'patternB', width: 6, height: 8, phase: 40 + mode, filter: filters[mode][1] }, blendMode: mode, paletteMode: 3, coverage: [`scalar blend mode ${mode}`] })
  cases.push({ name: `mode-${mode}-vector`, width: 8, height: 6, a: { recipe: 'patternA', width: 10, height: 7, phase: 20 + mode, filter: filters[mode][0] }, b: { recipe: 'patternB', width: 7, height: 9, phase: 50 + mode, filter: filters[mode][1] }, blendMode: mode, paletteMode: 4, coverage: [`vector blend mode ${mode}`] })
}
const focusedBase = { width: 9, height: 5, a: { recipe: 'patternA', width: 11, height: 6, phase: 71, filter: 'nearest' }, b: { recipe: 'patternB', width: 7, height: 8, phase: 89, filter: 'nearest' } }
const focus = (name, overrides, coverage) => cases.push({ ...focusedBase, name, ...overrides, coverage })
focus('palette-hsv', { blendMode: 7, paletteMode: 1, levels: f(3.75) }, ['HSV palette'])
focus('palette-oklab-lanes', { width: 5, height: 9, a: { recipe: 'patternA', width: 7, height: 11, phase: 73, filter: 'linear' }, b: { recipe: 'patternB', width: 9, height: 6, phase: 91, filter: 'linear' }, blendMode: 8, paletteMode: 2 }, ['OKLab matrices', 'all linearToSrgb indexes'])
focus('palette-rgb-extremes', { blendMode: 5, paletteMode: 3, levels: f(3.75), rotatePalette: f(100), repeatPalette: f(10), paletteOffset: f32Vector([-1.25, .5, 2]), paletteAmp: f32Vector([1.75, -.625, .03125]), paletteFreq: f32Vector([-2.5, 3.25, .125]), palettePhase: f32Vector([1.5, -1.75, .33333334]) }, ['palette vectors', 'rotate/repeat extrema'])
for (const [name, animate] of [['animate-minus', -1], ['animate-zero', 0], ['animate-plus', 1]]) focus(name, { paletteMode: 4, blendMode: 8, animate, cyclePalette: 0 }, ['animate sign'])
for (const [name, cyclePalette] of [['cycle-minus', -1], ['cycle-zero', 0], ['cycle-plus', 1]]) focus(name, { paletteMode: 3, blendMode: 7, animate: 0, cyclePalette }, ['cycle sign'])
focus('levels-one-scalar', { blendMode: 5, paletteMode: 3, levels: f(1) }, ['scalar levels special case'])
focus('levels-fractional-vector', { blendMode: 5, paletteMode: 4, levels: f(3.75) }, ['vector fractional levels'])
focus('loopscale-min', { blendMode: 7, paletteMode: 4, loopScale: f(1) }, ['loop scale minimum'])
focus('loopscale-max', { blendMode: 7, paletteMode: 4, loopScale: f(100) }, ['loop scale maximum'])
for (const [name, seed, wrap] of [['dead-random-neg-nowrap', -2147483648, false], ['dead-random-neg-wrap', -2147483648, true], ['dead-random-max-nowrap', 2147483647, false], ['dead-random-max-wrap', 2147483647, true]]) focus(name, { blendMode: 7, paletteMode: 4, seed, wrap }, ['dynamically dead random control'])
focus('tiled-fractional-ratio', { width: 6, height: 4, a: { recipe: 'patternA', width: 5, height: 7, phase: 101, filter: 'linear' }, b: { recipe: 'patternB', width: 11, height: 3, phase: 131, filter: 'linear' }, blendMode: 5, paletteMode: 2, tileOffset: f32Vector([3, 2]), fullResolution: f32Vector([13, 7]) }, ['tile/full/local coordinates', 'non-binary ratio'])
focus('sampler-edge-y', { width: 9, height: 7, a: { recipe: 'cornerTagsA', width: 3, height: 2, phase: 0, filter: 'nearest' }, b: { recipe: 'cornerTagsB', width: 5, height: 3, phase: 0, filter: 'linear' }, blendMode: 4, paletteMode: 4 }, ['edge clamp', 'filter split', 'bottom-left sample/top-down storage'])
focus('alpha-three-way', { width: 3, height: 1, a: { recipe: 'alphaA', width: 3, height: 1, phase: 0, filter: 'nearest' }, b: { recipe: 'alphaB', width: 4, height: 1, phase: 0, filter: 'nearest' }, blendMode: 4, paletteMode: 4 }, ['alpha A/B/equal winners'])
focus('external-context-base', { blendMode: 7, paletteMode: 4, externalTime: 0, externalSeed: 0 }, ['external context base'])
focus('external-context-extreme', { blendMode: 7, paletteMode: 4, externalTime: 16777216, externalSeed: 4294967295 }, ['external context ignored'])
if (cases.length !== 42) throw new Error(`Shape Mixer fixture census drift: ${cases.length}`)

function makeInput(definition, which) {
  const spec = definition[which]
  let surface
  if (spec.recipe === 'cornerTagsA') surface = cornerTags(spec.width, spec.height, 'A')
  else if (spec.recipe === 'cornerTagsB') surface = cornerTags(spec.width, spec.height, 'B')
  else if (spec.recipe === 'alphaA') surface = alphaThreeWay('A')
  else if (spec.recipe === 'alphaB') surface = alphaThreeWay('B')
  else surface = patternSurface(which === 'a' ? 'A' : 'B', spec.width, spec.height, spec.phase)
  surface.filter = spec.filter
  return surface
}

function resolved(definition, key) {
  const value = definition[key] ?? common[key]
  return ArrayBuffer.isView(value) ? new Float32Array(value) : value
}

function render(factory, definition) {
  const inputTex = makeInput(definition, 'a'); const tex = makeInput(definition, 'b')
  if (inputTex.data.buffer === tex.data.buffer) throw new Error(`${definition.name}: shared input backing buffer`)
  const beforeA = words(inputTex.data).slice(); const beforeB = words(tex.data).slice()
  const tileOffset = resolved(definition, 'tileOffset')
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution) : f32Vector([definition.width, definition.height])
  const uniforms = {
    LOOP_OFFSET: 10, time: resolved(definition, 'time'), seed: resolved(definition, 'seed'),
    blendMode: definition.blendMode, loopScale: resolved(definition, 'loopScale'), paletteMode: resolved(definition, 'paletteMode'),
    paletteOffset: resolved(definition, 'paletteOffset'), paletteAmp: resolved(definition, 'paletteAmp'),
    paletteFreq: resolved(definition, 'paletteFreq'), palettePhase: resolved(definition, 'palettePhase'),
    animate: resolved(definition, 'animate'), cyclePalette: resolved(definition, 'cyclePalette'),
    rotatePalette: resolved(definition, 'rotatePalette'), repeatPalette: resolved(definition, 'repeatPalette'),
    levels: resolved(definition, 'levels'), wrap: resolved(definition, 'wrap'),
  }
  const bindings = createCanonicalBindings({ width: definition.width, height: definition.height,
    time: resolved(definition, 'time'), seed: resolved(definition, 'seed'),
    uniforms, textures: { inputTex, tex }, tileOffset, fullResolution })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel: bindGlslKernel(factory, bindings), destination: output,
    time: definition.externalTime ?? common.externalTime, seed: definition.externalSeed ?? common.externalSeed })
  const afterA = words(inputTex.data); const afterB = words(tex.data)
  if (beforeA.some((word, index) => word !== afterA[index]) || beforeB.some((word, index) => word !== afterB[index])) throw new Error(`${definition.name}: input mutation`)
  return { output, inputTex, tex, beforeA, beforeB, uniforms, tileOffset, fullResolution }
}

function probes(surface) {
  const points = [['top-left', 0, 0], ['top-right', surface.width - 1, 0], ['bottom-left', 0, surface.height - 1], ['bottom-right', surface.width - 1, surface.height - 1], ['center', Math.floor(surface.width / 2), Math.floor(surface.height / 2)]]
  return points.map(([label, x, y]) => {
    const offset = (y * surface.width + x) * 4
    const values = Array.from(surface.data.slice(offset, offset + 4))
    return { label, top_down_xy: [x, y], values, f32_words_le: values.map(f32Bits) }
  })
}

function surfaceRecord(surface, before = null) {
  const rawWords = words(surface.data)
  const rgba8 = surface.toRgba8()
  const finite = surface.data.filter(Number.isFinite).length
  return {
    width: surface.width, height: surface.height,
    f32_words_le: Array.from(rawWords, u32Hex), f32_sha256: sha256(bytes(surface.data)),
    rgba8_bytes: Array.from(rgba8), rgba8_sha256: sha256(bytes(rgba8)),
    probes: probes(surface), finite_lane_count: finite, nonfinite_lane_count: surface.data.length - finite,
    pre_sha256: before ? sha256(bytes(before)) : undefined,
    post_sha256: before ? sha256(bytes(surface.data)) : undefined,
    immutable_exact_bits: before ? before.every((word, index) => word === rawWords[index]) : undefined,
  }
}

function inputRecord(surface, before, spec) {
  return { recipe: spec.recipe, phase: spec.phase, filter: spec.filter, ...surfaceRecord(surface, before) }
}

function routeInputProvenance(result) {
  const input = (surface, before) => {
    const beforeHash = sha256(bytes(before))
    const afterHash = sha256(bytes(surface.data))
    return { pre_f32_sha256: beforeHash, post_f32_sha256: afterHash,
      immutable_exact_bits: before.every((word, index) => word === words(surface.data)[index]) }
  }
  return { inputs_disjoint_backing: result.inputTex.data.buffer !== result.tex.data.buffer,
    inputTex: input(result.inputTex, result.beforeA), tex: input(result.tex, result.beforeB) }
}

const rendered = new Map()
const renderedRecords = new Map()
const renderCases = cases.map((definition) => {
  const canonical = render(canonicalFactory, definition)
  const repeat = render(canonicalFactory, definition)
  const publicResult = render(publicFactory, definition)
  const expected = expectedRecord(canonical.output)
  const repeatIdentity = shapeMixerRequireExact(repeat.output, expected, `${definition.name}/canonical-repeat`)
  const publicIdentity = shapeMixerRequireExact(publicResult.output, expected, `${definition.name}/public-canonical`)
  if (canonical.output.data.some((value) => !Number.isFinite(value))) throw new Error(`${definition.name}: non-finite rendered output`)
  rendered.set(definition.name, canonical.output)
  renderedRecords.set(definition.name, expected)
  const f32Scalars = new Set(['time', 'loopScale', 'rotatePalette', 'repeatPalette', 'levels'])
  const bindings = Object.fromEntries(Object.entries(canonical.uniforms).map(([name, value]) => [name,
    ArrayBuffer.isView(value) ? { f32_values: Array.from(value), f32_words_le: Array.from(words(value), u32Hex) }
      : f32Scalars.has(name) ? { f32_value: f(value), f32_word_le: f32Bits(value) } : value]))
  return {
    name: definition.name, coverage: definition.coverage, width: definition.width, height: definition.height,
    bindings, tile_offset: { f32_values: Array.from(canonical.tileOffset), f32_words_le: Array.from(words(canonical.tileOffset), u32Hex) },
    full_resolution: { f32_values: Array.from(canonical.fullResolution), f32_words_le: Array.from(words(canonical.fullResolution), u32Hex) },
    external_context: { time: definition.externalTime ?? common.externalTime, seed: definition.externalSeed ?? common.externalSeed },
    inputTex: inputRecord(canonical.inputTex, canonical.beforeA, definition.a),
    tex: inputRecord(canonical.tex, canonical.beforeB, definition.b),
    input_route_provenance: {
      canonical: routeInputProvenance(canonical),
      canonical_repeat: routeInputProvenance(repeat),
      public_catalog: routeInputProvenance(publicResult),
    },
    output_expected: surfaceRecord(canonical.output),
    canonical_repeat: repeatIdentity, public_canonical: publicIdentity,
  }
})

const identityGroups = [
  ['dead-random-neg-nowrap', 'dead-random-neg-wrap', 'dead-random-max-nowrap', 'dead-random-max-wrap'],
  ['external-context-base', 'external-context-extreme'],
]
for (const group of identityGroups) {
  const base = renderedRecords.get(group[0])
  for (const name of group.slice(1)) shapeMixerRequireExact(rendered.get(name), base, `identity/${group[0]}/${name}`)
}

function compileMutant(name, from, to, witnesses, classification = 'rendered canonical-JS one-anchor/one-replacement') {
  const count = canonicalText.split(from).length - 1
  if (count !== 1) throw new Error(`${name}: mutation anchor matched ${count} times`)
  const mutatedText = canonicalText.replace(from, to)
  return { name, factory: Function(`"use strict"; return (${mutatedText});`)(),
    anchor_sha256: sha256(from), replacement_sha256: sha256(to), mutated_factory_sha256: sha256(mutatedText),
    required_witnesses: witnesses, classification }
}

function functionSlice(name, nextName) {
  const start = canonicalText.indexOf(`function ${name} (`)
  const end = canonicalText.indexOf(`function ${nextName} (`, start)
  if (start < 0 || end < 0) throw new Error(`missing canonical function slice: ${name}`)
  return canonicalText.slice(start, end)
}

const vectorBlend = functionSlice('blend', 'blend_float_float_int_float')
const scalarBlend = functionSlice('blend_float_float_int_float', 'main')
const vectorReflect = 'reflect(color1, new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor])).reduce((res,el,i)=>(res[i] = el, res), color);'
const vectorRefract = 'refract(color1, color2, factor).reduce((res,el,i)=>(res[i] = el, res), color);'
const vectorMod = 'mod(color1, new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor])).reduce((res,el,i)=>(res[i] = el, res), color);'
const mutations = []
const addMutation = (...args) => mutations.push(compileMutant(...args))

addMutation('vector-reflect-scale-sign', vectorReflect,
  '$runtime.stdlib.subtract(color1, $runtime.stdlib.multiply(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), -2 * $runtime.stdlib.dot(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), color1))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-7-vector'])
addMutation('vector-reflect-subtract-to-add', vectorReflect,
  '$runtime.stdlib.add(color1, $runtime.stdlib.multiply(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), 2 * $runtime.stdlib.dot(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), color1))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-7-vector'])
addMutation('vector-reflect-reversed-output-operands', vectorReflect,
  '$runtime.stdlib.subtract($runtime.stdlib.multiply(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), 2 * $runtime.stdlib.dot(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), color1)), color1).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-7-vector'])
addMutation('vector-reflect-defensive-normal-normalization', vectorReflect,
  'reflect(color1, $runtime.stdlib.normalize(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-7-vector'])
addMutation('vector-reflect-omit-product-f32', vectorReflect,
  'new $runtime.PooledFloat32Array([0,1,2].map(i => Math.fround(color1[i] - (color2[i] * factor) * (2 * $runtime.stdlib.dot(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), color1))))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-7-vector'])
addMutation('scalar-reflect-mathematical-dot', 'color = reflect(color1, color2 * factor);',
  'color = Math.fround(color1 - Math.fround((color2 * factor) * (2 * Math.fround((color2 * factor) * color1))));', ['mode-7-scalar'])
addMutation('scalar-reflect-factor-association', 'color = reflect(color1, color2 * factor);',
  'color = reflect(color1, color2) * factor;', ['mode-7-scalar'])

addMutation('vector-refract-wrong-k-formula', vectorRefract,
  'refract(color1, color2, factor * factor).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-8-vector', 'animate-minus', 'animate-plus'])
addMutation('vector-refract-omit-left-f32', vectorRefract,
  'new $runtime.PooledFloat32Array([0,1,2].map(i => color1[i] * factor - Math.fround(color2[i] * (factor * $runtime.stdlib.dot(color2, color1) + Math.sqrt(1 - factor * factor * (1 - $runtime.stdlib.dot(color2, color1) ** 2)))))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-8-vector'])
addMutation('vector-refract-omit-right-f32', vectorRefract,
  'new $runtime.PooledFloat32Array([0,1,2].map(i => Math.fround(color1[i] * factor) - color2[i] * (factor * $runtime.stdlib.dot(color2, color1) + Math.sqrt(1 - factor * factor * (1 - $runtime.stdlib.dot(color2, color1) ** 2))))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-8-vector'])
addMutation('scalar-refract-mathematical-dot', 'color = refract(color1, color2, factor);',
  'color = Math.fround(Math.fround(color1 * factor) - Math.fround(color2 * (factor * Math.fround(color2 * color1) + Math.sqrt(1 - factor * factor * (1 - Math.fround(color2 * color1) ** 2)))));', ['mode-8-scalar'])
addMutation('scalar-refract-eta-association', 'color = refract(color1, color2, factor);',
  'color = refract(color1, color2 * factor, factor);', ['mode-8-scalar'])
addMutation('scalar-refract-omit-left-f32', 'color = refract(color1, color2, factor);',
  'color = Math.fround(color1 * factor - Math.fround(color2 * Math.sqrt(1 - factor * factor)));', ['mode-8-scalar'])
addMutation('scalar-refract-omit-right-f32', 'color = refract(color1, color2, factor);',
  'color = Math.fround(Math.fround(color1 * factor) - color2 * Math.sqrt(1 - factor * factor));', ['mode-8-scalar'])
addMutation('scalar-refract-omit-final-f32', 'color = refract(color1, color2, factor);',
  'color = Math.fround(color1 * factor) - Math.fround(color2 * Math.sqrt(1 - factor * factor));', ['mode-8-scalar'])

addMutation('wide-mod-reversed-operands', vectorMod,
  'mod(new $runtime.PooledFloat32Array([color2[0] * factor, color2[1] * factor, color2[2] * factor]), color1).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-5-vector'])
addMutation('wide-mod-unmaterialized-divisor', vectorMod,
  'new $runtime.PooledFloat32Array([0,1,2].map(i => Math.fround(color1[i] - (color2[i] * factor) * Math.floor(color1[i] / (color2[i] * factor))))).reduce((res,el,i)=>(res[i] = el, res), color);', ['mode-5-vector'])

const indexMutations = [
  ['index-linear-condition-fixed-lane', 'if (linear[i] <= 0.0031308000907301903) {', 'if (linear[0] <= 0.0031308000907301903) {'],
  ['index-srgb-low-write-fixed-lane', 'srgb[i] = linear[i] * 12.920000076293945;', 'srgb[0] = linear[i] * 12.920000076293945;'],
  ['index-linear-low-read-fixed-lane', 'srgb[i] = linear[i] * 12.920000076293945;', 'srgb[i] = linear[0] * 12.920000076293945;'],
  ['index-srgb-high-write-fixed-lane', 'srgb[i] = 1.0549999475479126 * (pow(linear[i], 0.4166666567325592)) - 0.054999999701976776;', 'srgb[0] = 1.0549999475479126 * (pow(linear[i], 0.4166666567325592)) - 0.054999999701976776;'],
  ['index-linear-high-read-fixed-lane', 'srgb[i] = 1.0549999475479126 * (pow(linear[i], 0.4166666567325592)) - 0.054999999701976776;', 'srgb[i] = 1.0549999475479126 * (pow(linear[0], 0.4166666567325592)) - 0.054999999701976776;'],
  ['linear-to-srgb-loop-bound-two', 'for (var i = 0; i < 3; ++i) {', 'for (var i = 0; i < 2; ++i) {'],
  ['linear-to-srgb-branch-inverted', 'if (linear[i] <= 0.0031308000907301903) {', 'if (linear[i] > 0.0031308000907301903) {'],
]
for (const row of indexMutations) addMutation(...row, ['palette-oklab-lanes'])

addMutation('oklab-fwdB-transpose', 'this[j*3+i] * v[j]} return sum; }, fwdB);', 'this[i*3+j] * v[j]} return sum; }, fwdB);', ['palette-oklab-lanes'])
addMutation('oklab-fwdA-row-column', 'fwdA[0] * c[0] + fwdA[3] * c[1] + fwdA[6] * c[2]', 'fwdA[0] * c[0] + fwdA[1] * c[1] + fwdA[2] * c[2]', ['palette-oklab-lanes'])
addMutation('oklab-remove-fwdA-intermediate-f32', 'var lms = new $runtime.PooledFloat32Array([fwdA[0] * c[0] + fwdA[3] * c[1] + fwdA[6] * c[2], fwdA[1] * c[0] + fwdA[4] * c[1] + fwdA[7] * c[2], fwdA[2] * c[0] + fwdA[5] * c[1] + fwdA[8] * c[2]]);', 'var lms = [fwdA[0] * c[0] + fwdA[3] * c[1] + fwdA[6] * c[2], fwdA[1] * c[0] + fwdA[4] * c[1] + fwdA[7] * c[2], fwdA[2] * c[0] + fwdA[5] * c[1] + fwdA[8] * c[2]];', ['palette-oklab-lanes'])

for (let mode = 0; mode < 10; mode += 1) {
  const vectorChanged = mode === 4
    ? vectorBlend.replace('factor = clamp(factor, 0, 1);\n  \tmix(color1, color2, factor).reduce((res,el,i)=>(res[i] = el, res), color);', 'factor = clamp(factor, 0, 1);\n  \tmin(color1, color2).reduce((res,el,i)=>(res[i] = el, res), color);')
    : vectorBlend.replace(`if (mode == ${mode}) {`, `if (mode == ${mode === 9 ? 98 : mode + 1}) {`)
  if (vectorChanged === vectorBlend) throw new Error(`vector mode ${mode} anchor absent`)
  addMutation(`mode-${mode}-vector-dispatch`, vectorBlend, vectorChanged, [`mode-${mode}-vector`])
  const scalarChanged = mode === 4
    ? scalarBlend.replace('factor = clamp(factor, 0, 1);\n  \tcolor = mix(color1, color2, factor);', 'factor = clamp(factor, 0, 1);\n  \tcolor = min(color1, color2);')
    : scalarBlend.replace(`if (mode == ${mode}) {`, `if (mode == ${mode === 9 ? 98 : mode + 1}) {`)
  if (scalarChanged === scalarBlend) throw new Error(`scalar mode ${mode} anchor absent`)
  addMutation(`mode-${mode}-scalar-dispatch`, scalarBlend, scalarChanged, [`mode-${mode}-scalar`])
}

addMutation('vector-factor-inversion-removed', vectorBlend, vectorBlend.replace('factor = 1 - factor;', 'factor = factor;'), ['mode-4-vector', 'mode-7-vector', 'mode-8-vector'])
addMutation('scalar-factor-inversion-removed', scalarBlend, scalarBlend.replace('factor = 1 - factor;', 'factor = factor;'), ['mode-4-scalar', 'mode-8-scalar'])
addMutation('scalar-vector-overload-swapped', 'var avgMix = blend_float_float_int_float(avg1, avg2, blendMode, blendy);', 'var avgMix = blend(new $runtime.PooledFloat32Array([avg1,avg1,avg1]), new $runtime.PooledFloat32Array([avg2,avg2,avg2]), blendMode, blendy)[0];', ['mode-5-scalar', 'mode-7-scalar', 'mode-8-scalar'])
addMutation('palette-mode-four-branch-inverted', 'if (paletteMode == 4) {', 'if (paletteMode != 4) {', ['mode-4-scalar', 'mode-4-vector'])
addMutation('blendy-half-removed', 'blendMode, blendy * 0.5)', 'blendMode, blendy)', ['mode-5-vector', 'mode-7-vector', 'mode-8-vector'])
addMutation('blendy-half-after-factor-inversion', 'blendMode, blendy * 0.5)', 'blendMode, 1 - (blendy * 0.5))', ['mode-5-vector', 'mode-7-vector', 'mode-8-vector'])

addMutation('scalar-posterize-order', 'd *= lev;\n  \td = floor(d) + 0.5;', 'd = floor(d);\n  \td = d * lev + 0.5;', ['levels-one-scalar'])
addMutation('scalar-posterize-level-one-special-case', 'if (lev == 1) {\n  \tlev = 2;', 'if (lev == 1) {\n  \tlev = 1;', ['levels-one-scalar'])
addMutation('vector-posterize-order', 'return (floor(d * lev)) / lev;', 'return floor(d) * lev / lev;', ['levels-fractional-vector'])
addMutation('cycle-palette-sign-reversed', 'color = [0, 1, 2, null].map(function (idx, i) { return idx == null ? color[i] : this[idx]; }, pal(d - time));', 'color = [0, 1, 2, null].map(function (idx, i) { return idx == null ? color[i] : this[idx]; }, pal(d + time));', ['cycle-plus'])
addMutation('animate-sign-reversed', 't = time + offset(st, freq);', 't = time - offset(st, freq);', ['animate-minus'])

addMutation('input-textures-swapped', 'var color1 = texture(inputTex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(inputTex, 0)));', 'var color1 = texture(tex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(tex, 0)));', ['mode-0-vector', 'tiled-fractional-ratio', 'sampler-edge-y'])
addMutation('second-texture-substituted-with-first', 'var color2 = texture(tex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(tex, 0)));', 'var color2 = texture(inputTex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(inputTex, 0)));', ['mode-0-vector', 'tiled-fractional-ratio', 'sampler-edge-y'])
addMutation('input-texture-size-substituted', 'textureSize(inputTex, 0)));', 'textureSize(tex, 0)));', ['tiled-fractional-ratio', 'sampler-edge-y'])
addMutation('second-texture-size-substituted', 'textureSize(tex, 0)));', 'textureSize(inputTex, 0)));', ['tiled-fractional-ratio', 'sampler-edge-y'])
const firstSample = 'texture(inputTex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(inputTex, 0)))'
const secondSample = 'texture(tex, vec2.divide([], new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]), textureSize(tex, 0)))'
const nearestClone = (name) => `Object.assign(Object.create(Object.getPrototypeOf(${name})), ${name}, {filter: 'nearest'})`
addMutation('input-filter-forced-nearest', firstSample, firstSample.replace('inputTex,', `${nearestClone('inputTex')},`), ['mode-1-scalar', 'mode-3-vector'])
addMutation('second-filter-forced-nearest', secondSample, secondSample.replace('tex,', `${nearestClone('tex')},`), ['mode-3-vector', 'sampler-edge-y'])
addMutation('input-y-convention-inverted', '[gl_FragCoord[0], gl_FragCoord[1]]), textureSize(inputTex, 0)', '[gl_FragCoord[0], resolution[1] - gl_FragCoord[1]]), textureSize(inputTex, 0)', ['sampler-edge-y'])
addMutation('second-y-convention-inverted', '[gl_FragCoord[0], gl_FragCoord[1]]), textureSize(tex, 0)', '[gl_FragCoord[0], resolution[1] - gl_FragCoord[1]]), textureSize(tex, 0)', ['sampler-edge-y'])

addMutation('alpha-forced-one', 'color[3] = max(color1[3], color2[3]);', 'color[3] = 1;', ['alpha-three-way'])
addMutation('alpha-only-input-a', 'color[3] = max(color1[3], color2[3]);', 'color[3] = color1[3];', ['alpha-three-way'])
addMutation('alpha-only-input-b', 'color[3] = max(color1[3], color2[3]);', 'color[3] = color2[3];', ['alpha-three-way'])
addMutation('tile-offset-omitted', 'var globalCoord = new $runtime.PooledFloat32Array([gl_FragCoord[0] + tileOffset[0], gl_FragCoord[1] + tileOffset[1]]);', 'var globalCoord = new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]]);', ['tiled-fractional-ratio'])
addMutation('full-resolution-replaced-by-local', 'var st = new $runtime.PooledFloat32Array([globalCoord[0] / fullResolution[0], globalCoord[1] / fullResolution[1]]);', 'var st = new $runtime.PooledFloat32Array([globalCoord[0] / resolution[0], globalCoord[1] / resolution[1]]);', ['tiled-fractional-ratio'])
addMutation('local-resolution-replaced-by-full', 'textureSize(inputTex, 0)));', 'fullResolution));', ['tiled-fractional-ratio'])
addMutation('loop-offset-ten-changed', 'if (LOOP_OFFSET == 10) {', 'if (LOOP_OFFSET == 11) {', ['loopscale-min', 'loopscale-max', 'tiled-fractional-ratio'])
addMutation('rotate-palette-omitted', 't = t * repeatPalette + rotatePalette * 0.009999999776482582;', 't = t * repeatPalette;', ['palette-rgb-extremes', 'palette-hsv', 'palette-oklab-lanes'])
addMutation('repeat-palette-omitted', 't = t * repeatPalette + rotatePalette * 0.009999999776482582;', 't = t + rotatePalette * 0.009999999776482582;', ['palette-rgb-extremes', 'palette-hsv', 'palette-oklab-lanes'])
addMutation('palette-vector-component-order', 'var a = paletteOffset;', 'var a = new $runtime.PooledFloat32Array([paletteOffset[2], paletteOffset[0], paletteOffset[1]]);', ['palette-rgb-extremes', 'palette-hsv', 'palette-oklab-lanes'])

function mutationResult(mutant) {
  const results = mutant.required_witnesses.map((name) => {
    const definition = cases.find((item) => item.name === name)
    if (!definition) throw new Error(`${mutant.name}: missing witness ${name}`)
    const comparison = shapeMixerCompareExact(render(mutant.factory, definition).output, renderedRecords.get(name), `${mutant.name}/${name}`)
    if (comparison.exact || comparison.changed_lane_count < 1) throw new Error(`${mutant.name}: witness ${name} did not diverge in raw Float32 words`)
    return { case: name, changed_lane_count: comparison.changed_lane_count,
      changed_rgba8_byte_count: comparison.changed_rgba8_byte_count,
      first_mismatch: comparison.first_float32_mismatch,
      first_rgba8_mismatch: comparison.first_rgba8_mismatch }
  })
  return { name: mutant.name, classification: mutant.classification,
    anchor_sha256: mutant.anchor_sha256, replacement_sha256: mutant.replacement_sha256,
    mutated_factory_sha256: mutant.mutated_factory_sha256,
    required_witnesses: mutant.required_witnesses, required_witness_results: results }
}

const behavioralMutationLedger = mutations.map(mutationResult)

function directHelperLedger() {
  const runtime = new GlslCpuRuntime()
  const std = runtime.stdlib
  const vector = (hex) => {
    const data = new Float32Array(hex.length)
    new Uint32Array(data.buffer).set(hex.map((word) => Number.parseInt(word, 16)))
    return data
  }
  const resultWords = (value) => Array.from(words(value instanceof Float32Array ? value : new Float32Array([value])), u32Hex)
  const exactRows = []
  const reflectI = vector(['408c4d65', 'c0407fe6', 'c0ecaf78']); const reflectN = vector(['c07d065b', '4082a176', 'c002ca11'])
  const reflectActual = resultWords(std.reflect(reflectI, reflectN))
  if (reflectActual.join(' ') !== '0xc2dc7ddd 0x42e6b53b 0xc2854c5f') throw new Error(`published vector reflect witness drift: ${reflectActual}`)
  exactRows.push({ name: 'published-vector-reflect-old-one-narrow', inputs_f32_words_le: [Array.from(words(reflectI), u32Hex), Array.from(words(reflectN), u32Hex)], canonical_words_le: reflectActual, rejected_old_words_le: ['0xc2dc7ddc', '0x42e6b53b', '0xc2854c5f'] })
  const refractI = vector(['bfdc1c58', 'be8bbd72', '3fbd4587']); const refractN = vector(['bf89dd86', '3acd6835', 'bf12d8d2']); const eta = 0.6234136876035227
  const refractActual = resultWords(std.refract(refractI, refractN, eta))
  if (refractActual.join(' ') !== '0x3f2e2acc 0xbe30d7b3 0x3fed73e8') throw new Error(`published vector refract witness drift: ${refractActual}`)
  exactRows.push({ name: 'published-vector-refract-old-one-narrow', inputs_f32_words_le: [Array.from(words(refractI), u32Hex), Array.from(words(refractN), u32Hex)], eta, canonical_words_le: refractActual, rejected_old_words_le: ['0x3f2e2acb', '0xbe30d7b2', '0x3fed73e8'] })
  const scalarReflect = (incident, normal) => f(incident - f(normal * 0))
  const scalarRefract = (incident, normal, etaValue) => f(f(incident * etaValue) - f(normal * Math.sqrt(1 - etaValue * etaValue)))
  const scalarRows = [
    ['scalar-reflect-negative-zero-positive-normal', scalarReflect(-0, 1), '0x80000000'],
    ['scalar-reflect-negative-zero-negative-normal', scalarReflect(-0, -1), '0x00000000'],
    ['scalar-reflect-finite', scalarReflect(1.25, -.5), '0x3fa00000'],
    ['scalar-refract-negative-zero-eta-zero', scalarRefract(-0, 1, 0), '0xbf800000'],
    ['scalar-refract-negative-zero-negative-normal-eta-one', scalarRefract(-0, -1, 1), '0x00000000'],
    ['scalar-refract-finite', scalarRefract(1.25, -.5, .25), '0x3f4bef7b'],
  ].map(([name, value, expected]) => {
    const actual = f32Bits(value); if (actual !== expected) throw new Error(`${name}: ${actual}`)
    return { name, canonical_words_le: [actual], expected_words_le: [expected] }
  })
  exactRows.push(...scalarRows)
  const vectorCases = [
    ['vector-refract-negative-k-positive-zero', f32Vector([1, 0, 0]), f32Vector([0, 1, 0]), 2],
    ['vector-refract-exact-zero-k', f32Vector([1, 0, 0]), f32Vector([0, 1, 0]), 1],
    ['vector-refract-signed-zero', f32Vector([-0, 0, -0]), f32Vector([1, -1, 1]), 0],
    ['vector-refract-non-unit-normal', f32Vector([.75, -.25, .5]), f32Vector([2, -.5, 3]), .25],
    ['vector-refract-nan-staging', f32Vector([Number.NaN, .25, -.5]), f32Vector([1, 0, 0]), .5],
  ].map(([name, incident, normal, etaValue]) => ({ name, eta: etaValue,
    input_words_le: [Array.from(words(incident), u32Hex), Array.from(words(normal), u32Hex)],
    canonical_words_le: resultWords(std.refract(incident, normal, etaValue)),
    classification: name.includes('nan') ? 'NaN payload not cross-target frozen; staging/classification only' : 'exact raw-word direct helper witness' }))
  exactRows.push(...vectorCases)
  const modCases = [[-1.25, .5], [1.25, -.5], [0, .5], [1.75, .6], [0.78125006, f(.31250003)]]
  for (const [index, [left, right]] of modCases.entries()) exactRows.push({ name: `wide-mod-direct-${index}`,
    inputs_f32_words_le: [f32Bits(left), f32Bits(right)], canonical_words_le: [f32Bits(f(glslMod(f(left), f(right))))],
    classification: 'negative/divisor/zero/fractional/f32-sensitive wide-mod direct witness' })
  exactRows.push({ name: 'scalar-reflect-nan', canonical_classification: Number.isNaN(scalarReflect(Number.NaN, 1)) ? 'nan' : 'not-nan' })
  exactRows.push({ name: 'scalar-refract-nan', canonical_classification: Number.isNaN(scalarRefract(1, 1, Number.NaN)) ? 'nan' : 'not-nan' })
  return exactRows
}

const runtimeStructuralSpecs = [
  { name: 'vector-reflect-dot-child-order', start: '      reflect: (incident, normal)', end: '      refract: (incident, normal, eta)', owner_bytes: 102, owner_sha256: '4c662c611eb3791504489059e1bfaf333d04eeeed1936f4107e1fead1e09fb5f' },
  { name: 'vector-refract-dot-child-order', start: '      refract: (incident, normal, eta)', end: '      lessThan: relational', owner_bytes: 378, owner_sha256: '9b4ef5725fe268e68a4122b69a575941d0413d50e6266ae062f969f20327753b' },
]
const runtimeStructuralRows = runtimeStructuralSpecs.map((spec) => {
  const start = runtimeSource.indexOf(spec.start)
  const end = runtimeSource.indexOf(spec.end, start)
  if (start < 0 || end < 0) throw new Error(`${spec.name}: runtime owner slice missing`)
  const owner = runtimeSource.slice(start, end)
  if (Buffer.byteLength(owner) !== spec.owner_bytes || sha256(owner) !== spec.owner_sha256) throw new Error(`${spec.name}: runtime owner identity drift`)
  const from = 'dot(normal, incident)'; const to = 'dot(incident, normal)'
  if (owner.split(from).length - 1 !== 1) throw new Error(`${spec.name}: runtime dot-order anchor is not unique in owner`)
  const mutatedOwner = owner.replace(from, to)
  const mutatedRuntime = `${runtimeSource.slice(0, start)}${mutatedOwner}${runtimeSource.slice(end)}`
  return { name: spec.name, source_layer: 'pinned noisemaker-for-cpu GLSL runtime owner slice',
    runtime_relative_path: 'src/csl/glsl-runtime.js', runtime_sha256: sha256(runtimeSource),
    owner_start_marker: spec.start, owner_end_marker: spec.end,
    owner_bytes: Buffer.byteLength(owner), owner_sha256: sha256(owner),
    anchor_occurrences_in_owner: 1, anchor_sha256: sha256(from), replacement_sha256: sha256(to),
    mutated_owner_sha256: sha256(mutatedOwner), mutated_runtime_sha256: sha256(mutatedRuntime),
    pixel_expectation: 'structural/profile/emitter rejection; dot-child swap is commutative and has no fabricated rendered divergence' }
})

const structuralSpecs = [
  ['float-bits-to-uint-positive-zero-numeric-conversion', 'floatBitsToUint(seedFrac)', 'seedFrac >>> 0'],
  ['scalar-uint-xor-lane-0', '(cpu_umul(fracBits, 374761393)) ^ 2654435769', '(cpu_umul(fracBits, 374761393)) + 2654435769'],
  ['scalar-uint-xor-lane-1', '(cpu_umul(fracBits, 668265263)) ^ 2135587861', '(cpu_umul(fracBits, 668265263)) + 2135587861'],
  ['scalar-uint-xor-lane-2', '(cpu_umul(fracBits, 2246822519)) ^ 2496678324', '(cpu_umul(fracBits, 2246822519)) + 2496678324'],
  ['scalar-uint-xor-uvec3-parent', 'var jitter = cpu_uvec3((cpu_umul(fracBits, 374761393)) ^ 2654435769, (cpu_umul(fracBits, 668265263)) ^ 2135587861, (cpu_umul(fracBits, 2246822519)) ^ 2496678324);', 'var jitter = new $runtime.PooledFloat32Array([(cpu_umul(fracBits, 374761393)) ^ 2654435769, (cpu_umul(fracBits, 668265263)) ^ 2135587861, (cpu_umul(fracBits, 2246822519)) ^ 2496678324]);'],
]
const structuralOnlyMutationLedger = [...runtimeStructuralRows, ...structuralSpecs.map(([name, from, to]) => {
  const count = canonicalText.split(from).length - 1
  if (count !== 1) throw new Error(`${name}: structural anchor matched ${count} times`)
  return { name, source_layer: 'canonical factory', anchor_sha256: sha256(from), replacement_sha256: sha256(to), mutated_factory_sha256: sha256(canonicalText.replace(from, to)), pixel_expectation: 'structural/profile/emitter rejection; no fabricated rendered divergence' }
})]

const fixture = {
  schema: 'noisemaker-for-cpp.shape-mixer182.pixel-parity.v1',
  program_key: programKey,
  define: { LOOP_OFFSET: 10 },
  corpus_revision: corpusRevision,
  upstream_revision: UPSTREAM_REVISION,
  oracle_authority: 'clean pinned noisemaker-for-cpu canonicalFactory15 under pinned Node; no C++ output participates',
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured canonical Surface.toRgba8 byte arrays; never reconstructed from expected words',
    tolerance: 'none',
    comparison_order: 'dimensions, exact expected/actual lane count, exact expected/actual byte count, every Float32 word, every independent RGBA8 byte',
    coordinates: 'all probes and first mismatches use top-down storage x/y',
  },
  provenance: {
    authority_commit: authorityCommit,
    authority_checkout_clean: true,
    live_checkout_required: true,
    authority_live_distinct: true,
    authority_live_non_symlink_directories: true,
    node_version: process.version,
    import_closure: authorityClosure,
    files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relative, hash]]) => [name, { relative_path_from_noisemaker_for_cpu: relative, sha256: hash }])),
    source: { relative_path_from_noisemaker_for_cpp: path.relative(cppRoot, sourcePath), bytes: sourceBytes.length, sha256: sha256(sourceBytes), normalized_loop_offset_10_bytes: 17664, normalized_loop_offset_10_sha256: 'afb1be09867bbbb02f63c115b84ef4fd813d72defc71e2cc7d8891db9113b1b8' },
    canonical_factory: { name: canonicalFactory.name, bytes: Buffer.byteLength(canonicalText), sha256: sha256(canonicalText), source_slice_bytes: Buffer.byteLength(canonicalSlice), source_slice_sha256: sha256(canonicalSlice) },
    public_factory_is_canonical_identity: true,
    adapter_override_absent: true,
    metadata: effect,
    single_pass_interface: effect.passes[0],
  },
  frontend_probe: frontendProof,
  comparer_self_tests: comparerSelfTests(),
  surface_recipes: {
    patternA: 'f32 modular asymmetric RGBA formula pinned in generator; alpha [0.875,0.25,0.5]',
    patternB: 'independent f32 modular asymmetric RGBA formula pinned in generator; alpha [0.125,0.75,0.5]',
    cornerTags: 'four unequal corners and unequal center; separate A/B values',
    alphaThreeWay: 'nearest alpha pairs A/B/equal; B sampling indices 0,2,3',
  },
  render_cases: renderCases,
  identity_groups: identityGroups,
  behavioral_mutation_ledger: behavioralMutationLedger,
  direct_helper_mutation_ledger: directHelperLedger(),
  structural_only_mutation_ledger: structuralOnlyMutationLedger,
  admitted_non_pixel_barriers: {
    fmod_negative_operand_semantics: 'direct-helper-only because all frozen rendered mode-5 dividends/divisors are positive',
    loop_bound_four: 'frontend loop proof rejects it; the fourth write to a three-lane JS typed array is pixel-inert',
    inverse_oklab_matrices: 'authenticated structurally but oklab_from_linear_srgb is unreachable from main',
    vector_final_narrowing_only: 'direct-helper-only because the factory immediately reduces vector helper output into another Float32Array; combining omissions would fabricate the named mutation',
  },
}

function reportFor(data) {
  const caseRows = data.render_cases.map((item) => `| ${item.name} | ${item.width}x${item.height} | ${item.output_expected.f32_sha256} | ${item.output_expected.rgba8_sha256} |`).join('\n')
  const mutationRows = data.behavioral_mutation_ledger.map((item) => {
    const first = item.required_witness_results[0]
    return `| ${item.name} | ${item.required_witnesses.join(', ')} | ${first.changed_lane_count} | ${first.first_mismatch.top_down_xy.join(',')}/${first.first_mismatch.channel} |`
  }).join('\n')
  const structuralRows = data.structural_only_mutation_ledger.map((item) => `| ${item.name} | ${item.source_layer} |`).join('\n')
  return `# Shape Mixer182 exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; exact define \`LOOP_OFFSET=10\`.

## Result

The clean canonical JavaScript authority produced 42 fixtures: 20 mode-matrix cases and 22 focused cases. Every fixture stores complete independent input and output Float32 words, canonical RGBA8 bytes, filters, bindings, probes, finite census, and canonical-repeat/public-canonical identity. Input pre/post SHA-256 and immutability are frozen independently for canonical, canonical-repeat, and public-catalog routes. No C++ output contributes expected data.

The JavaScript comparer rejects shape and payload-count mismatch before iteration, then checks every raw Float32 word and every independently supplied RGBA8 byte. Signed zero, distinct quiet-NaN payloads, the final alpha lane, and a byte-only mismatch are self-tested.

## Render fixtures

| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
${caseRows}

## Rendered behavioral mutations

| Mutation | Required witnesses | Changed lanes at first witness | First top-down x,y/channel |
| --- | --- | ---: | --- |
${mutationRows}

Every row above is an independent canonical-factory one-anchor/one-replacement mutant and every named witness changes at least one raw Float32 word.

## Direct-helper and structural barriers

The direct-helper ledger contains published three-lane reflect/refract words, all six scalar raw-word witnesses, negative-k/exact-zero/signed-zero/non-unit/NaN refract classifications, scalar NaN classifications, and negative/divisor/zero/fractional/Float32-sensitive wide-mod cases.

| Structural-only mutation | Authentication layer |
| --- | --- |
${structuralRows}

Structural-only rows deliberately have no fabricated pixel witness. The report also records four source-authenticated non-pixel barriers: negative-operand fmod semantics, the pixel-inert fourth linear-to-sRGB typed-array write, unreachable inverse OKLab matrices, and final vector narrowing that is immediately rematerialized by the factory.

## Sampling and coordinates

- Surface storage, probes, and mismatch coordinates are top-down.
- The canonical runtime consumes bottom-left fragment coordinates and performs its own sampler y conversion.
- Nearest and linear filter choices are frozen independently for \`inputTex\` and \`tex\`.
- RGBA8 comes directly from canonical \`Surface.toRgba8()\`, independently of the expected word arrays.

## Regeneration

\`\`\`sh
NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --write --cpu-root <immutable-cpu-snapshot-root>
NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_shape_mixer_native_oracle_include.py --check
\`\`\`

The JavaScript generator requires distinct external non-symlink authority/live
directories and runs its frontend probe in one OS temporary directory. Both
generators are fail-closed. Check mode performs no writes.
`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)
const write = mode === '--write'
verifySidecar(generatorPath)
verifySidecar(frontendProbePath)
verifySidecar(includeGeneratorPath)
if (write) {
  fs.writeFileSync(outputPath, jsonText)
  fs.writeFileSync(reportPath, reportText)
  fs.writeFileSync(sidecarPath(outputPath), sidecarText(outputPath, Buffer.from(jsonText)))
  fs.writeFileSync(sidecarPath(reportPath), sidecarText(reportPath, Buffer.from(reportText)))
} else {
  verifySidecar(outputPath)
  verifySidecar(reportPath)
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Shape Mixer oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Shape Mixer oracle report drift')
}
console.log(`Shape Mixer182 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} renders, ${behavioralMutationLedger.length} behavioral mutations, ${fixture.direct_helper_mutation_ledger.length} direct-helper rows, ${structuralOnlyMutationLedger.length} structural-only mutations`)
