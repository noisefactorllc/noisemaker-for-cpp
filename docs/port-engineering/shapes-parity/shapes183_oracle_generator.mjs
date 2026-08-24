#!/usr/bin/env node
// Shapes183 canonical JavaScript oracle generator.
//
// Authority: the unmodified public canonical factory `canonicalFactory16` from
// an immutable snapshot of `noisemaker-for-cpu`, executed through the pinned
// `bindCanonicalKernel` / `GlslCpuRuntime` / `runPass` path. No C++ output
// participates in any expected array. A locally reimplemented formula is not
// an oracle and is never used here.
//
//   node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = path.resolve(here, '../../..')
const generatorPath = fileURLToPath(import.meta.url)
const outputPath = path.join(here, 'shapes183-oracles.json')
const reportPath = path.join(here, 'shapes183-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_shapes_native_oracle_include.py')

const schema = 'noisemaker-for-cpp.shapes183.pixel-parity.v1'
const schemaVersion = 1
const programKey = 'classicNoisedeck/shapes:shapes'
const effectKey = 'classicNoisedeck/shapes'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'
const authorityNode = 'v24.7.0'
const defines = { LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 }
const factoryName = 'canonicalFactory16'
const factoryTextSha256 = 'a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3'
// The live checkout is DERIVED, never hardcoded: a machine-specific absolute
// path in a checked-in gate is unrunnable on any other machine and leaks a home
// directory into the repository. `NOISEMAKER_FOR_CPU` overrides; otherwise the
// conventional sibling layout under $HOME is used.
const liveCpuCheckoutResolution =
  'process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu'
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU
  ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)

// Neither the `--cpu-root` argument nor the live-checkout path is recorded
// verbatim. The import closure and the six pinned file hashes authenticate the
// snapshot completely; the literal path authenticates nothing and would bind
// `--check` to one ephemeral directory on one machine.
const cpuRootPlaceholder = '<immutable-cpu-snapshot-root>'
const liveCheckoutPlaceholder = '<live-noisemaker-for-cpu-checkout>'
const sourceRelative = `tools/glslcpp/corpus/${corpusRevision}/sources/classicNoisedeck/shapes/shapes.glsl`
const sourceBytesExpected = 21289
const sourceSha256Expected = '60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0'

// Exactly eighteen runtime bindings. LOOP_A_OFFSET/LOOP_B_OFFSET are
// compile-time defines recorded separately and are never counted here.
const bindingNames = Object.freeze([
  'time', 'seed', 'wrap', 'resolution', 'tileOffset', 'fullResolution',
  'loopAScale', 'loopBScale', 'speedA', 'speedB', 'paletteMode',
  'paletteOffset', 'paletteAmp', 'paletteFreq', 'palettePhase',
  'cyclePalette', 'rotatePalette', 'repeatPalette',
])
const bindingAbi = Object.freeze({
  time: 'number', seed: 'int32', wrap: 'bool', resolution: 'Vec2',
  tileOffset: 'Vec2', fullResolution: 'Vec2', loopAScale: 'number',
  loopBScale: 'number', speedA: 'number', speedB: 'number',
  paletteMode: 'int32', paletteOffset: 'Vec3', paletteAmp: 'Vec3',
  paletteFreq: 'Vec3', palettePhase: 'Vec3', cyclePalette: 'int32',
  rotatePalette: 'number', repeatPalette: 'number',
})

const pinnedCpuFiles = Object.freeze({
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
})

const f = Math.fround
const channels = ['r', 'g', 'b', 'a']

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytesOf(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
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
if (typeof canonicalFactory !== 'function') throw new Error('canonical Shapes factory missing')
if (publicFactory !== canonicalFactory) throw new Error('public Shapes factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('unexpected Shapes adapter override')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Shapes adapter override value')
if (canonicalFactory.name !== factoryName) throw new Error(`canonical Shapes factory name drift: ${canonicalFactory.name}`)
const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) throw new Error(`canonical Shapes factory text drift: ${sha256(canonicalText)}`)

const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf('function canonicalFactory17', sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('canonical Shapes factory source slice missing')
const canonicalSlice = canonicalKernelsSource.slice(sliceStart, sliceEnd)

const sourcePath = path.join(cppRoot, sourceRelative)
const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== sourceBytesExpected || sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error('pinned Shapes GLSL source drift')
}

const effect = effectRecords.find((item) => item.id === effectKey)
if (!effect || effect.func !== 'shapes' || effect.kind !== 'generator') throw new Error('Shapes metadata drift')
if (effect.passes?.length !== 1 || effect.passes[0]?.program !== 'shapes') throw new Error('Shapes pass interface drift')
if (Object.keys(effect.textures ?? {}).length !== 0 || effect.externalTexture !== null) throw new Error('Shapes must have no textures')
if (effect.params?.loopAOffset?.default !== defines.LOOP_A_OFFSET
    || effect.params?.loopAOffset?.define !== 'LOOP_A_OFFSET'
    || effect.params?.loopBOffset?.default !== defines.LOOP_B_OFFSET
    || effect.params?.loopBOffset?.define !== 'LOOP_B_OFFSET') {
  throw new Error('Shapes default define drift')
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
      throw new Error(`Shapes comparer did not preflight ${reason}`)
    }
  }
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  expectReject(compareExact(new Surface(2, 1, new Float32Array(8)), shapeExpected, 'self/shape'), 'dimensions')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareExact(minusZero, expectedRecord(plusZero), 'self/signed-zero')
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32'
      || !bytesOf(plusZero.toRgba8()).equals(bytesOf(minusZero.toRgba8()))) {
    throw new Error('Shapes comparer missed signed zero')
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
    throw new Error('Shapes comparer missed NaN payload')
  }
  const finalLane = compareExact(new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)])),
    expectedRecord(plusZero), 'self/final-lane')
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch.channel !== 'a'
      || finalLane.first_mismatch.lane_or_byte_index !== 3) {
    throw new Error('Shapes comparer missed final alpha lane')
  }
  const byteExpected = expectedRecord(plusZero)
  byteExpected.rgba8[3] ^= 1
  const byteOnly = compareExact(plusZero, byteExpected, 'self/final-byte')
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch.channel !== 'a') {
    throw new Error('Shapes comparer missed independent byte mismatch')
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

const basePalette = {
  paletteOffset: [0.17, 0.43, 0.79], paletteAmp: [0.61, -0.27, 0.38],
  paletteFreq: [0.75, 1.5, -0.625], palettePhase: [0.125, -0.375, 0.6875],
}
const extremePalette = {
  paletteOffset: [-1.25, 0.5, 2], paletteAmp: [1.75, -0.625, 0.03125],
  paletteFreq: [-2.5, 3.25, 0.125], palettePhase: [1.5, -1.75, 0.33333334],
}
const productPalette = {
  paletteOffset: [0.83, 0.6, 0.63], paletteAmp: [0.5, 0.5, 0.5],
  paletteFreq: [1, 1, 1], palettePhase: [0.3, 0.1, 0],
}

// The tiled case is a genuine top-down crop of a larger full render. Its
// tileOffset.y is `full_height - crop_y - tile_height`, never raw crop_y.
const cropRect = { crop_x: 4, crop_y: 2, tile_width: 4, tile_height: 6, full_width: 11, full_height: 9 }

const cases = [
  {
    name: 'oklab-palette-a',
    coverage: ['OKLab palette (paletteMode 2)', 'landscape 9x5', 'untiled full route',
      'wrap false', 'both speeds positive', 'cyclePalette +1', 'nominal rotate/repeat',
      'control-group anchor'],
    width: 9, height: 5, time: 0.5, seed: 3, wrap: false,
    loopAScale: 37.25, loopBScale: 12.5, speedA: 45, speedB: 17.5,
    paletteMode: 2, cyclePalette: 1, rotatePalette: 23.75, repeatPalette: 2.5,
    ...basePalette,
  },
  {
    name: 'oklab-palette-tiled',
    coverage: ['OKLab palette (paletteMode 2)', 'portrait 4x6 tile', 'tiled route',
      'wrap true', 'negative speedA', 'zero speedB', 'cyclePalette 0',
      'top-down crop translation witness'],
    width: cropRect.tile_width, height: cropRect.tile_height, time: 0.125, seed: -7, wrap: true,
    loopAScale: 8.75, loopBScale: 62.25, speedA: -45, speedB: 0,
    paletteMode: 2, cyclePalette: 0, rotatePalette: 61.5, repeatPalette: 4,
    ...basePalette,
    tileOffset: [cropRect.crop_x, cropRect.full_height - cropRect.crop_y - cropRect.tile_height],
    fullResolution: [cropRect.full_width, cropRect.full_height],
    crop: cropRect,
  },
  {
    name: 'oklab-palette-extreme',
    coverage: ['OKLab palette (paletteMode 2)', 'square 6x6', 'untiled full route',
      'wrap false', 'speedA +100 / speedB -100 extrema', 'cyclePalette -1',
      'rotate 100 / repeat 10 extrema', 'INT32_MAX seed', 'negative bound time',
      'out-of-gamut palette vectors'],
    width: 6, height: 6, time: -3.75, seed: 2147483647, wrap: false,
    loopAScale: 100, loopBScale: 1, speedA: 100, speedB: -100,
    paletteMode: 2, cyclePalette: -1, rotatePalette: 100, repeatPalette: 10,
    ...extremePalette,
  },
  {
    name: 'oklab-palette-negative-speed',
    coverage: ['OKLab palette (paletteMode 2)', 'portrait 5x9', 'untiled full route',
      'wrap true', 'both speeds negative', 'cyclePalette 0',
      'loopAScale minimum / loopBScale maximum', 'rotate 0 / repeat 1'],
    width: 5, height: 9, time: 2.25, seed: 123, wrap: true,
    loopAScale: 1, loopBScale: 100, speedA: -100, speedB: -0.5,
    paletteMode: 2, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1,
    ...basePalette,
  },
  {
    name: 'diagnostic-palette-hsv',
    coverage: ['HSV palette (paletteMode 1)', 'landscape 8x3', 'untiled full route',
      'wrap false', 'zero speedA', 'positive speedB', 'cyclePalette +1',
      'negative rotate / fractional repeat', 'zero seed',
      'non-reaching mutant control'],
    width: 8, height: 3, time: 0.75, seed: 0, wrap: false,
    loopAScale: 55.5, loopBScale: 3.25, speedA: 0, speedB: 25,
    paletteMode: 1, cyclePalette: 1, rotatePalette: -40, repeatPalette: 0.5,
    ...basePalette,
  },
  {
    name: 'diagnostic-palette-rgb',
    coverage: ['RGB palette (paletteMode 0)', 'square 4x4', 'untiled full route',
      'wrap true', 'zero speedA', 'negative speedB', 'cyclePalette -1',
      'INT32_MIN seed', 'product-default palette vectors',
      'non-reaching mutant control'],
    width: 4, height: 4, time: 1.5, seed: -2147483648, wrap: true,
    loopAScale: 22.5, loopBScale: 47.75, speedA: 0, speedB: -62.5,
    paletteMode: 0, cyclePalette: -1, rotatePalette: 0, repeatPalette: 1,
    ...productPalette,
  },
]
if (cases.length !== 6) throw new Error(`Shapes fixture census drift: ${cases.length}`)
if (new Set(cases.map((item) => item.name)).size !== cases.length) throw new Error('duplicate Shapes case name')

// ---------------------------------------------------------------------------
// Rendering through the pinned public path
// ---------------------------------------------------------------------------

function uniformsFor(definition) {
  return {
    LOOP_A_OFFSET: defines.LOOP_A_OFFSET,
    LOOP_B_OFFSET: defines.LOOP_B_OFFSET,
    time: f(definition.time),
    seed: definition.seed,
    wrap: definition.wrap,
    loopAScale: f(definition.loopAScale),
    loopBScale: f(definition.loopBScale),
    speedA: f(definition.speedA),
    speedB: f(definition.speedB),
    paletteMode: definition.paletteMode,
    paletteOffset: f32Vector(definition.paletteOffset),
    paletteAmp: f32Vector(definition.paletteAmp),
    paletteFreq: f32Vector(definition.paletteFreq),
    palettePhase: f32Vector(definition.palettePhase),
    cyclePalette: definition.cyclePalette,
    rotatePalette: f(definition.rotatePalette),
    repeatPalette: f(definition.repeatPalette),
  }
}

function bindingOptions(definition) {
  return {
    width: definition.width,
    height: definition.height,
    time: f(definition.time),
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
  const callerVectors = {
    tileOffset: options.tileOffset,
    fullResolution: options.fullResolution,
    paletteOffset: options.uniforms.paletteOffset,
    paletteAmp: options.uniforms.paletteAmp,
    paletteFreq: options.uniforms.paletteFreq,
    palettePhase: options.uniforms.palettePhase,
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
      const lanes = abi === 'Vec2' ? 2 : 3
      if (!(value instanceof Float32Array) || value.length !== lanes) throw new Error(`${name}: not a ${abi}`)
      out[name] = { abi, f32_values: Array.from(value), f32_words_le: Array.from(words(value), u32Hex) }
    }
  }
  if (Object.keys(out).length !== 18) throw new Error('binding census drift')
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
// Top-down crop identity for the tiled case
// ---------------------------------------------------------------------------

const tiledDefinition = cases.find((item) => item.name === 'oklab-palette-tiled')
const fullRouteDefinition = {
  ...tiledDefinition,
  name: 'oklab-palette-tiled/full-route',
  width: cropRect.full_width,
  height: cropRect.full_height,
  tileOffset: [0, 0],
  fullResolution: [cropRect.full_width, cropRect.full_height],
}
const fullRoute = render(canonicalFactory, fullRouteDefinition)
const fullWords = words(fullRoute.output.data)
const fullBytes = fullRoute.output.toRgba8()
const tileWords = words(canonicalOutputs.get('oklab-palette-tiled').data)
const tileBytes = canonicalOutputs.get('oklab-palette-tiled').toRgba8()
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
const rawCropYDefinition = { ...tiledDefinition, name: 'oklab-palette-tiled/raw-crop-y-trap',
  tileOffset: [cropRect.crop_x, cropRect.crop_y] }
const rawCropYOutput = render(canonicalFactory, rawCropYDefinition).output
const rawCropYComparison = compareExact(rawCropYOutput, canonicalExpected.get('oklab-palette-tiled'),
  'crop/raw-crop-y-trap')
if (rawCropYComparison.exact) throw new Error('raw top-down crop_y trap is indistinguishable; the crop witness is vacuous')

const cropIdentity = {
  case: 'oklab-palette-tiled',
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
}

// ---------------------------------------------------------------------------
// One-axis control group on oklab-palette-a
// ---------------------------------------------------------------------------

const controlAnchor = cases.find((item) => item.name === 'oklab-palette-a')
const controlBaselineExpected = canonicalExpected.get('oklab-palette-a')

function controlRow(name, overrides, expectation, axis, note) {
  const definition = { ...controlAnchor, ...overrides, name: `oklab-palette-a/${name}` }
  const rendered = render(canonicalFactory, definition)
  const output = rendered.output
  const comparison = compareExact(output, controlBaselineExpected, `control/${name}`)
  const record = surfaceRecord(output)
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
    output: record,
    note,
  }
}

const controlGroup = {
  anchor: 'oklab-palette-a',
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
      'bound time is live through the speedA/speedB offset terms and the cyclePalette +1 branch'),
    controlRow('bound-seed-123', { seed: 123 }, 'differs', 'bound seed int32 3 -> 123',
      'design expectation; see seed_liveness_census for the measured result'),
  ],
}
if (controlGroup.controls[0].observed !== 'identical') {
  throw new Error('external runPass time/seed changed the output; the shader-owned uniforms do not dominate')
}
if (controlGroup.controls[1].observed !== 'differs') {
  throw new Error('bound time did not change the output')
}

// ---------------------------------------------------------------------------
// Bound-seed liveness census (measured, not assumed)
// ---------------------------------------------------------------------------

const seedProbeValues = [-2147483648, -7, 0, 1, 3, 123, 65537, 2147483647]
const seedProbes = seedProbeValues.map((seed) => {
  const output = render(canonicalFactory, { ...controlAnchor, seed, name: `seed-probe-${seed}` }).output
  const comparison = compareExact(output, controlBaselineExpected, `seed-probe/${seed}`)
  return { seed, f32_sha256: sha256(bytesOf(output.data)), differs_from_baseline: !comparison.exact,
    changed_lane_count: comparison.changed_lane_count ?? 0 }
})
const seedLivenessCensus = {
  probe_case: 'oklab-palette-a',
  probes: seedProbes,
  bound_seed_changes_output: seedProbes.some((probe) => probe.differs_from_baseline),
  reason: 'At defines LOOP_A_OFFSET=40 / LOOP_B_OFFSET=30 the only main() consumers of the '
    + '`seed` uniform are the two `offset(...)` calls. Offset 40 dispatches to shape(st, 4, freq*0.5) '
    + 'and offset 30 dispatches to the absolute-distance branch; neither reads its `seed` parameter. '
    + 'The `value()`/`constant()`/`randomFromLatticeWithOffset()` subtree that would consume it is '
    + 'reachable in the conservative call graph but is not entered by a default full render.',
  design_expectation: 'shapes183-design.md section 4.1 and NEXT_CODING_AGENT_HANDOFF.md section 5 '
    + 'require the bound-seed control to change the output',
  disagreement: 'The shipped JavaScript materialization does not change. The parity target is the '
    + 'shipped materialization, so the measured result is recorded verbatim and the design expectation '
    + 'is reported as unsatisfiable at the default defines. `seed` remains a required int32 ABI binding.',
}

// ---------------------------------------------------------------------------
// Mutation discrimination, generated rather than asserted
// ---------------------------------------------------------------------------

const mutantSpecs = [
  {
    name: 'shapes-fwdB-column-swap',
    target: 'linear_srgb_from_oklab final fwdB matrix multiply',
    anchor: 'this[j*3+i] * v[j]} return sum; }, fwdB);',
    replacement: 'this[i*3+j] * v[j]} return sum; }, fwdB);',
    reaching: 'paletteMode == 2 only',
  },
  {
    name: 'shapes-cube-unnarrowed',
    target: 'linear_srgb_from_oklab cube-of-lms Float32 staging',
    anchor: 'return (new $runtime.PooledFloat32Array([(lms[0] * lms[0]) * lms[0], (lms[1] * lms[1]) * lms[1], (lms[2] * lms[2]) * lms[2]]))',
    replacement: 'return ([(lms[0] * lms[0]) * lms[0], (lms[1] * lms[1]) * lms[1], (lms[2] * lms[2]) * lms[2]])',
    reaching: 'paletteMode == 2 only',
  },
]
const reachingCases = ['oklab-palette-a', 'oklab-palette-tiled', 'oklab-palette-extreme', 'oklab-palette-negative-speed']
const nonReachingCases = ['diagnostic-palette-hsv', 'diagnostic-palette-rgb']

const mutationLedger = mutantSpecs.map((spec) => {
  const occurrences = canonicalText.split(spec.anchor).length - 1
  if (occurrences !== 1) throw new Error(`${spec.name}: mutation anchor matched ${occurrences} times`)
  const mutatedText = canonicalText.replace(spec.anchor, spec.replacement)
  const factory = Function(`"use strict"; return (${mutatedText});`)()
  const results = cases.map((definition) => {
    const output = render(factory, definition).output
    const comparison = compareExact(output, canonicalExpected.get(definition.name), `${spec.name}/${definition.name}`)
    return {
      case: definition.name,
      reaching: reachingCases.includes(definition.name),
      differs: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count ?? 0,
      changed_rgba8_byte_count: comparison.changed_rgba8_byte_count ?? 0,
      f32_sha256: sha256(bytesOf(output.data)),
      rgba8_sha256: sha256(bytesOf(output.toRgba8())),
      first_mismatch: comparison.first_float32_mismatch ?? null,
    }
  })
  for (const result of results) {
    if (result.reaching && !result.differs) throw new Error(`${spec.name}: reaching case ${result.case} did not discriminate`)
    if (!result.reaching && result.differs) throw new Error(`${spec.name}: non-reaching control ${result.case} changed`)
  }
  return {
    name: spec.name,
    target: spec.target,
    reaching: spec.reaching,
    classification: 'rendered canonical-JS one-anchor/one-replacement mutant',
    anchor_sha256: sha256(spec.anchor),
    replacement_sha256: sha256(spec.replacement),
    mutated_factory_sha256: sha256(mutatedText),
    anchor_occurrences: occurrences,
    results,
  }
})

// ---------------------------------------------------------------------------
// Fixture assembly
// ---------------------------------------------------------------------------

const coverageAxes = {
  palette_mode: { 'OKLab (2)': reachingCases, 'HSV (1)': ['diagnostic-palette-hsv'], 'RGB (0)': ['diagnostic-palette-rgb'] },
  aspect: {
    landscape: ['oklab-palette-a', 'diagnostic-palette-hsv'],
    portrait: ['oklab-palette-tiled', 'oklab-palette-negative-speed'],
    square: ['oklab-palette-extreme', 'diagnostic-palette-rgb'],
  },
  tiling: { tiled: ['oklab-palette-tiled'], untiled: cases.map((item) => item.name).filter((name) => name !== 'oklab-palette-tiled') },
  wrap: {
    'true': ['oklab-palette-tiled', 'oklab-palette-negative-speed', 'diagnostic-palette-rgb'],
    'false': ['oklab-palette-a', 'oklab-palette-extreme', 'diagnostic-palette-hsv'],
  },
  speed_sign: {
    positive: ['oklab-palette-a', 'oklab-palette-extreme', 'diagnostic-palette-hsv'],
    negative: ['oklab-palette-tiled', 'oklab-palette-extreme', 'oklab-palette-negative-speed', 'diagnostic-palette-rgb'],
    zero: ['oklab-palette-tiled', 'diagnostic-palette-hsv', 'diagnostic-palette-rgb'],
  },
  cycle_palette: {
    '-1': ['oklab-palette-extreme', 'diagnostic-palette-rgb'],
    '0': ['oklab-palette-tiled', 'oklab-palette-negative-speed'],
    '1': ['oklab-palette-a', 'diagnostic-palette-hsv'],
  },
  rotate_repeat: {
    nominal: ['oklab-palette-a', 'oklab-palette-tiled'],
    extrema: ['oklab-palette-extreme'],
    identity: ['oklab-palette-negative-speed', 'diagnostic-palette-rgb'],
    negative_rotate_fractional_repeat: ['diagnostic-palette-hsv'],
  },
  bound_seed: Object.fromEntries(cases.map((item) => [item.name, item.seed])),
  bound_time_f32_word: Object.fromEntries(cases.map((item) => [item.name, f32Bits(item.time)])),
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
  oracle_authority: 'unmodified public canonicalFactory16 from an immutable noisemaker-for-cpu snapshot, '
    + 'executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates',
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
  mutation_ledger: mutationLedger,
  mutation_discrimination_contract: {
    reaching_cases: reachingCases,
    non_reaching_cases: nonReachingCases,
    rule: 'every reaching OKLab case must differ for every mutant; every non-reaching control must be byte-identical',
  },
  claim_boundaries: {
    dead_hash_branch: 'With defines 40/30 the branch containing floatBitsToUint(seedFrac) and the three '
      + 'scalar uint XOR sites is conservative call-graph reachable but is not entered by a normal full '
      + 'render. These full-surface cases must never be cited as proof that branch executed.',
    normalized_source: 'Normalized/typed source, function, interface, and whole-program hashes are the '
      + 'frontend profiles’ authority and are deliberately not restated here.',
    bound_seed: 'The bound `seed` uniform is a required int32 ABI binding but is pixel-inert at the '
      + 'default defines; see seed_liveness_census.',
  },
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function reportFor(data) {
  const caseRows = data.render_cases.map((item) =>
    `| ${item.name} | ${item.width}x${item.height} | ${item.route} | ${item.bindings.paletteMode.value} | ${item.output_expected.f32_sha256} | ${item.output_expected.rgba8_sha256} |`).join('\n')
  const coverageRows = Object.entries(data.coverage_axes)
    .filter(([axis]) => axis !== 'bound_seed' && axis !== 'bound_time_f32_word')
    .map(([axis, buckets]) => Object.entries(buckets)
      .map(([bucket, names]) => `| ${axis} | ${bucket} | ${names.join(', ')} |`).join('\n')).join('\n')
  const controlRows = data.control_group.controls.map((item) =>
    `| ${item.name} | ${item.axis} | ${item.expectation} | ${item.observed} | ${item.pass ? 'pass' : 'FAIL'} | ${item.changed_lane_count} |`).join('\n')
  const mutantRows = data.mutation_ledger.map((mutant) => mutant.results.map((result) =>
    `| ${mutant.name} | ${result.case} | ${result.reaching ? 'reaching' : 'control'} | ${result.differs ? 'differs' : 'identical'} | ${result.changed_lane_count} |`).join('\n')).join('\n')
  const seedRows = data.seed_liveness_census.probes.map((probe) =>
    `| ${probe.seed} | ${probe.f32_sha256} | ${probe.differs_from_baseline ? 'differs' : 'identical'} |`).join('\n')
  return `# Shapes183 exact-parity oracle

Program \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`; exact defines
\`LOOP_A_OFFSET=${data.defines.LOOP_A_OFFSET}\`, \`LOOP_B_OFFSET=${data.defines.LOOP_B_OFFSET}\`.

## Authority

This oracle is produced by the ${data.oracle_authority}. The generator refuses to run unless
\`kernelFactories.get(key) === canonicalKernelFactories[key]\`, the factory is named
\`${factoryName}\`, its \`Function.prototype.toString\` SHA-256 is \`${factoryTextSha256}\`, the adapter
table does not own the key, all six pinned CPU files match, and every module in the
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
counted as bindings.

## Render fixtures

| Case | Size | Route | paletteMode | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | ---: | --- | --- |
${caseRows}

Every case stores exact dimensions, all ${data.runtime_binding_names.length} bindings with every float and vector lane as a
hexadecimal f32 word, the external \`runPass\` time/seed pair, the complete expected Float32 word
array, the complete independently captured RGBA8 byte array, finite/non-finite lane counts, and a
SHA-256 over each array. Alpha is exactly \`0x3f800000\` / \`255\` in every case and every route.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
${coverageRows}

## Top-down crop normalization

Both runners store rows top-down while GLSL fragment coordinates are bottom-left. The tiled case is a
genuine crop: \`${data.crop_identity.tile_offset_rule}\`. For crop
\`(${data.crop_identity.rect.crop_x}, ${data.crop_identity.rect.crop_y})\` of size
\`${data.crop_identity.rect.tile_width}x${data.crop_identity.rect.tile_height}\` from
\`${data.crop_identity.rect.full_width}x${data.crop_identity.rect.full_height}\`, the tile route binds
\`tileOffset\` words \`${data.crop_identity.tile_offset_f32_words_le.join(', ')}\`; the other ${data.crop_identity.held_identical_bindings.length} bindings are held identical.
Tile output equals the corresponding top-down crop of the full-route output exactly:
${data.crop_identity.exact_word_mismatches} word mismatches and ${data.crop_identity.exact_byte_mismatches} byte mismatches.
Binding raw top-down \`crop_y\` into \`tileOffset.y\` instead changes
${data.crop_identity.raw_crop_y_trap.changed_lane_count} lanes, so the witness is not vacuous.

## One-axis control group on \`oklab-palette-a\`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
${controlRows}

## Bound-seed liveness census

| Bound seed | Float32 SHA-256 | Versus baseline |
| --- | --- | --- |
${seedRows}

${data.seed_liveness_census.reason}

**Disagreement with the design.** ${data.seed_liveness_census.design_expectation}.
${data.seed_liveness_census.disagreement}

## Mutation discrimination

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
${mutantRows}

Both mutants are independent one-anchor/one-replacement rewrites of the canonical factory text,
compiled and rendered by this generator. \`--check\` fails unless all four reaching OKLab cases differ
for each mutant and both non-reaching diagnostic controls stay byte-identical. No hand-mutated
generated C++ is committed.

## Claim boundaries

- ${data.claim_boundaries.dead_hash_branch}
- ${data.claim_boundaries.normalized_source}
- ${data.claim_boundaries.bound_seed}

## Regeneration

\`\`\`sh
node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_shapes_native_oracle_include.py --self-test
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
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Shapes183 oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Shapes183 oracle report drift')
}
const controlSummary = controlGroup.controls.map((item) => `${item.name}=${item.observed}`).join(' ')
console.log(`Shapes183 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} cases, `
  + `${mutationLedger.length} mutants, controls [${controlSummary}], `
  + `crop exact, alpha 0x3f800000/255`)
