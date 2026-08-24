import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../../..'))
const outputPath = path.join(here, 'emboss-parity-oracles.json')
const reportPath = path.join(here, 'emboss-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'emboss_frontend_probe.py')
const includeGeneratorPath = path.join(here, 'generate_emboss_native_oracle_include.py')
const programKey = 'filter/emboss:emboss'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const authorityCommit = '4834b0144ee0524588144a482cca0067b15f68ec'
const authorityNode = 'v24.7.0'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/filter/emboss/emboss.glsl')
const f = Math.fround
function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }

const argv = process.argv.slice(2)
const modes = argv.filter((token) => token === '--write' || token === '--check')
if (modes.length !== 1) throw new Error('choose exactly one of --write or --check')
const write = modes[0] === '--write'
const check = modes[0] === '--check'
const cpuRootIndex = argv.indexOf('--cpu-root')
if (cpuRootIndex < 0 || cpuRootIndex + 1 >= argv.length) {
  throw new Error('--cpu-root <immutable snapshot> is required')
}
for (const [index, token] of argv.entries()) {
  if (index === cpuRootIndex || index === cpuRootIndex + 1) continue
  if (token !== '--write' && token !== '--check') {
    throw new Error(`unexpected argument: ${token}`)
  }
}
const cpuRootArgument = argv[cpuRootIndex + 1]
if (!fs.existsSync(cpuRootArgument) || !fs.statSync(cpuRootArgument).isDirectory()) {
  throw new Error(`--cpu-root is not a directory: ${cpuRootArgument}`)
}
const cpuRoot = fs.realpathSync(cpuRootArgument)
const liveCpuCheckout = process.env.NOISEMAKER_FOR_CPU
  ?? (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : null)
if (!liveCpuCheckout) {
  throw new Error(
    'cannot resolve the live noisemaker-for-cpu checkout: '
    + 'set NOISEMAKER_FOR_CPU or HOME')
}
if (!fs.existsSync(liveCpuCheckout)
    || !fs.statSync(liveCpuCheckout).isDirectory()) {
  throw new Error(`live noisemaker-for-cpu checkout does not exist: ${liveCpuCheckout}`)
}
const liveCpuReal = fs.realpathSync(liveCpuCheckout)
function beneath(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`)
}
if (liveCpuReal
    && (beneath(liveCpuReal, cpuRoot) || beneath(cpuRoot, liveCpuReal))) {
  throw new Error(
    '--cpu-root must be an immutable snapshot, never the live '
    + 'noisemaker-for-cpu checkout')
}
if (cpuRoot === cppRoot || beneath(cppRoot, cpuRoot)) {
  throw new Error('--cpu-root must not live inside the C++ repository')
}

function confineCpuImport(candidate, why) {
  const real = fs.realpathSync(candidate)
  if (!beneath(cpuRoot, real)) {
    throw new Error(`${why}: import escapes the immutable snapshot: ${real}`)
  }
  if (liveCpuReal && beneath(liveCpuReal, real)) {
    throw new Error(`${why}: import resolved into the live checkout: ${real}`)
  }
  return real
}

const importSpecifierPatterns = [
  /\bfrom\s*['"]([^'"\n]+)['"]/g,
  /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
  /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
]
const dynamicImportPattern = /\bimport\s*\(([^)]*)\)/g
const cpuEntryRelatives = [
  'src/effects/catalog.js',
  'src/effects/generated/upstream-snapshot.js',
  'src/csl/glsl-kernel.js',
  'src/csl/glsl-runtime.js',
  'src/runtime/pass-runner.js',
  'src/runtime/surface.js',
]
const cpuImportClosure = new Set()
const pendingCpuImports = cpuEntryRelatives.map((relative) =>
  confineCpuImport(path.join(cpuRoot, relative), 'entry'))
while (pendingCpuImports.length) {
  const file = pendingCpuImports.pop()
  if (cpuImportClosure.has(file)) continue
  cpuImportClosure.add(file)
  const text = fs.readFileSync(file, 'utf8')
  dynamicImportPattern.lastIndex = 0
  let dynamicImport = dynamicImportPattern.exec(text)
  while (dynamicImport !== null) {
    const argument = dynamicImport[1].trim()
    if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(argument)) {
      throw new Error(`nonliteral dynamic import in ${path.relative(cpuRoot, file)}`)
    }
    dynamicImport = dynamicImportPattern.exec(text)
  }
  for (const pattern of importSpecifierPatterns) {
    pattern.lastIndex = 0
    let match = pattern.exec(text)
    while (match) {
      const specifier = match[1]
      if (!specifier.startsWith('node:')) {
        if (!specifier.startsWith('./') && !specifier.startsWith('../')) {
          throw new Error(`bare CPU module specifier ${specifier}`)
        }
        const resolved = path.resolve(path.dirname(file), specifier)
        if (!fs.existsSync(resolved)) {
          throw new Error(`unresolvable CPU import ${specifier}`)
        }
        pendingCpuImports.push(confineCpuImport(resolved, file))
      }
      match = pattern.exec(text)
    }
  }
}
const importClosureRecords = [...cpuImportClosure]
  .map((file) => ({
    relative_path_from_noisemaker_for_cpu: path.relative(cpuRoot, file),
    sha256: sha256(fs.readFileSync(file)),
  }))
  .sort((left, right) => left.relative_path_from_noisemaker_for_cpu
    .localeCompare(right.relative_path_from_noisemaker_for_cpu))
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
const actualImportClosure = importClosureRecords.map((entry) => [
  entry.relative_path_from_noisemaker_for_cpu, entry.sha256,
])
if (JSON.stringify(actualImportClosure) !== JSON.stringify(expectedImportClosure)) {
  const expected = new Map(expectedImportClosure)
  const actual = new Map(actualImportClosure)
  const missing = expectedImportClosure.filter(([relative, hash]) => actual.get(relative) !== hash)
  const extra = actualImportClosure.filter(([relative, hash]) => !expected.has(relative))
  throw new Error(`CPU import closure mismatch: missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`)
}

const loadCpu = (relative) => import(pathToFileURL(
  confineCpuImport(path.join(cpuRoot, relative), 'load')).href)
const {
  canonicalAdapterFactories,
  canonicalKernelFactories,
  kernelFactories,
} = await loadCpu('src/effects/catalog.js')
const { effectRecords, UPSTREAM_REVISION } = await loadCpu(
  'src/effects/generated/upstream-snapshot.js')
const { createCanonicalBindings } = await loadCpu('src/csl/glsl-kernel.js')
const { bindGlslKernel } = await loadCpu('src/csl/glsl-runtime.js')
const { runPass } = await loadCpu('src/runtime/pass-runner.js')
const { Surface } = await loadCpu('src/runtime/surface.js')

function bytes(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function f32Bits(value) {
  const lane = new Float32Array([value])
  return u32Hex(new DataView(lane.buffer).getUint32(0, true))
}

function compareFloat32Surfaces(reference, candidate) {
  if (!(reference?.data instanceof Float32Array) || !(candidate?.data instanceof Float32Array)) {
    throw new TypeError('Emboss comparer requires Float32 Surface values')
  }
  if (reference.width !== candidate.width || reference.height !== candidate.height || reference.data.length !== candidate.data.length) {
    return {
      exact_f32_bits: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_lanes: Math.max(reference.data.length, candidate.data.length),
      first_mismatch: null,
    }
  }
  const left = new Uint32Array(reference.data.buffer, reference.data.byteOffset, reference.data.length)
  const right = new Uint32Array(candidate.data.buffer, candidate.data.byteOffset, candidate.data.length)
  let mismatched = 0
  let first = null
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] === right[index]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(index / 4)
      first = {
        lane_index: index,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][index % 4],
        reference_bits_le: u32Hex(left[index]),
        candidate_bits_le: u32Hex(right[index]),
      }
    }
  }
  return {
    exact_f32_bits: mismatched === 0,
    dimensions_match: true,
    reference_dimensions: [reference.width, reference.height],
    candidate_dimensions: [candidate.width, candidate.height],
    mismatched_lanes: mismatched,
    first_mismatch: first,
  }
}

function compareRgba8Surfaces(reference, candidate) {
  if (reference.width !== candidate.width || reference.height !== candidate.height) {
    return { exact_rgba8_bytes: false, dimensions_match: false, mismatched_bytes: Math.max(reference.data.length, candidate.data.length), first_mismatch: null }
  }
  const left = reference.toRgba8()
  const right = candidate.toRgba8()
  let mismatched = 0
  let first = null
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] === right[index]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(index / 4)
      first = {
        byte_index: index,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][index % 4],
        reference_byte: left[index],
        candidate_byte: right[index],
      }
    }
  }
  return { exact_rgba8_bytes: mismatched === 0, dimensions_match: true, mismatched_bytes: mismatched, first_mismatch: first }
}

function compareSurfaces(reference, candidate) {
  return { float32: compareFloat32Surfaces(reference, candidate), rgba8: compareRgba8Surfaces(reference, candidate) }
}

function expectedRecord(surface) {
  return {
    width: surface.width,
    height: surface.height,
    f32_words: new Uint32Array(
      surface.data.buffer,
      surface.data.byteOffset,
      surface.data.length,
    ).slice(),
    rgba8_bytes: surface.toRgba8().slice(),
  }
}

function compareSurfaceToExpected(actual, expected) {
  const dimensionsMatch = actual.width === expected.width && actual.height === expected.height
  const actualWords = new Uint32Array(
    actual.data.buffer,
    actual.data.byteOffset,
    actual.data.length,
  )
  const actualBytes = actual.toRgba8()
  const laneCountMatch = actualWords.length === expected.f32_words.length
  const byteCountMatch = actualBytes.length === expected.rgba8_bytes.length
  if (!dimensionsMatch || !laneCountMatch || !byteCountMatch) {
    return {
      exact: false,
      dimensions_match: dimensionsMatch,
      lane_count_match: laneCountMatch,
      byte_count_match: byteCountMatch,
      first_mismatch: null,
    }
  }
  const channels = ['r', 'g', 'b', 'a']
  for (let index = 0; index < actualWords.length; index += 1) {
    if (actualWords[index] === expected.f32_words[index]) continue
    const pixel = Math.floor(index / 4)
    return {
      exact: false,
      dimensions_match: true,
      lane_count_match: true,
      byte_count_match: true,
      first_mismatch: {
        kind: 'float32',
        top_down_xy: [pixel % expected.width, Math.floor(pixel / expected.width)],
        channel: channels[index % 4],
        expected_word: u32Hex(expected.f32_words[index]),
        actual_word: u32Hex(actualWords[index]),
        expected_byte: expected.rgba8_bytes[index],
        actual_byte: actualBytes[index],
      },
    }
  }
  for (let index = 0; index < actualBytes.length; index += 1) {
    if (actualBytes[index] === expected.rgba8_bytes[index]) continue
    const pixel = Math.floor(index / 4)
    return {
      exact: false,
      dimensions_match: true,
      lane_count_match: true,
      byte_count_match: true,
      first_mismatch: {
        kind: 'rgba8',
        top_down_xy: [pixel % expected.width, Math.floor(pixel / expected.width)],
        channel: channels[index % 4],
        expected_word: u32Hex(expected.f32_words[index]),
        actual_word: u32Hex(actualWords[index]),
        expected_byte: expected.rgba8_bytes[index],
        actual_byte: actualBytes[index],
      },
    }
  }
  return {
    exact: true,
    dimensions_match: true,
    lane_count_match: true,
    byte_count_match: true,
    first_mismatch: null,
  }
}

function comparerSelfTests() {
  const shapeExpected = expectedRecord(new Surface(1, 2, new Float32Array(8)))
  const shape = compareSurfaceToExpected(new Surface(2, 1, new Float32Array(8)), shapeExpected)
  if (shape.exact || shape.dimensions_match) throw new Error('Emboss comparer accepted equal-length shape mismatch')
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareSurfaceToExpected(minusZero, expectedRecord(plusZero))
  if (signedZero.exact || signedZero.first_mismatch?.kind !== 'float32' || !bytes(plusZero.toRgba8()).equals(bytes(minusZero.toRgba8()))) throw new Error('Emboss comparer missed signed zero')
  const nanAData = new Float32Array(4)
  const nanBData = new Float32Array(4)
  new Uint32Array(nanAData.buffer).set([0x7fc00001, 0, 0, 0x3f800000])
  new Uint32Array(nanBData.buffer).set([0x7fc00002, 0, 0, 0x3f800000])
  const nanA = new Surface(1, 1, nanAData)
  const nanB = new Surface(1, 1, nanBData)
  const nanPayload = compareSurfaceToExpected(nanB, expectedRecord(nanA))
  if (nanPayload.exact || nanPayload.first_mismatch?.kind !== 'float32' || !bytes(nanA.toRgba8()).equals(bytes(nanB.toRgba8()))) throw new Error('Emboss comparer missed NaN payload')
  const finalA = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const finalB = new Surface(1, 1, new Float32Array([0, 0, 0, f(0.5)]))
  const finalLane = compareSurfaceToExpected(finalB, expectedRecord(finalA))
  if (finalLane.first_mismatch?.kind !== 'float32' || finalLane.first_mismatch?.channel !== 'a') throw new Error('Emboss comparer missed final lane')
  const byteOnlyExpected = expectedRecord(finalA)
  byteOnlyExpected.rgba8_bytes[byteOnlyExpected.rgba8_bytes.length - 1] ^= 1
  const byteOnly = compareSurfaceToExpected(finalA, byteOnlyExpected)
  if (byteOnly.exact || byteOnly.first_mismatch?.kind !== 'rgba8' || byteOnly.first_mismatch?.channel !== 'a') throw new Error('Emboss expected-data comparer missed byte-only mismatch')
  return {
    equal_length_different_shape_rejected: true,
    signed_zero_rejected_with_equal_rgba8: true,
    distinct_quiet_nan_payload_rejected_with_equal_rgba8: true,
    final_lane_mismatch_rejected: true,
    independently_supplied_byte_only_mismatch_rejected: true,
    signed_zero_first_mismatch: signedZero.first_mismatch,
    nan_payload_first_mismatch: nanPayload.first_mismatch,
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
for (const [name, [relativePath, expectedHash]] of Object.entries(provenanceFiles)) {
  const actualHash = sha256(fs.readFileSync(path.join(cpuRoot, relativePath)))
  if (actualHash !== expectedHash) throw new Error(`${name} provenance drift: ${actualHash}`)
}

if (process.version !== authorityNode) throw new Error(`Node authority drift: ${process.version}`)

const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== 5160 || sha256(sourceBytes) !== '872eff00bdfe411a0dceb66e8b203b5ea1c03015e3eea041d821966354713191') throw new Error('pinned Emboss source drift')
const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
const canonicalText = canonicalFactory?.toString() ?? ''
if (canonicalFactory?.name !== 'canonicalFactory50' || Buffer.byteLength(canonicalText) !== 8336 || sha256(canonicalText) !== '72f7faa20dfbbf43cab7762c484d13d43e7f3b3102d0a5a70494ab0ab19fa79f') throw new Error('canonical Emboss factory drift')
if (publicFactory !== canonicalFactory) throw new Error('public Emboss factory is not canonical identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Emboss adapter override')
if (UPSTREAM_REVISION !== '117a236679d1db3ab8f0e278230ece277b57564c') throw new Error('upstream revision drift')

const effect = effectRecords.find((item) => item.id === 'filter/emboss')
const expectedParams = {
  style: { type: 'int', default: 0, define: 'STYLE', choices: { color: 0, gray: 1 } },
  amount: { type: 'float', default: 1, uniform: 'amount', min: 0.1, max: 5 },
  angle: { type: 'float', default: 135, uniform: 'angle', min: -360, max: 360 },
  height: { type: 'float', default: 1, uniform: 'height', min: 1, max: 10 },
  colorAmount: { type: 'float', default: 100, uniform: 'colorAmount', min: 0, max: 100 },
}
if (!effect || effect.func !== 'emboss' || effect.kind !== 'filter' || effect.namespace !== 'filter' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'emboss') throw new Error('Emboss metadata/pass drift')
for (const [name, expected] of Object.entries(expectedParams)) {
  for (const [field, value] of Object.entries(expected)) {
    if (JSON.stringify(effect.params?.[name]?.[field]) !== JSON.stringify(value)) throw new Error(`Emboss ${name}.${field} metadata drift`)
  }
}

const probe = spawnSync('python3', [frontendProbePath, '--check'], { cwd: cppRoot, encoding: 'utf8' })
if (probe.status !== 0) throw new Error(`Emboss frontend probe failed: ${probe.stderr || probe.stdout}`)
const frontendProof = JSON.parse(probe.stdout)

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const index = (y * width + x) * 4
    data[index] = f((((31 * x + 17 * y + 19 * phase + 3) % 101) + 1) / 103)
    data[index + 1] = f((((13 * x + 43 * y + 23 * phase + 5) % 97) + 2) / 101)
    data[index + 2] = f((((47 * x + 7 * y + 29 * phase + 11) % 89) + 3) / 97)
    data[index + 3] = f((((5 * x + 19 * y + 7 * phase) % 31) + 5) / 41)
  }
  data[0] = -0
  return new Surface(width, height, data)
}

function asymmetricSurface(width, height) {
  const surface = patternedSurface(width, height, 41)
  surface.data.fill(f(0.03125))
  for (let index = 3; index < surface.data.length; index += 4) surface.data[index] = f(0.625)
  const set = (x, y, rgba) => surface.data.set(rgba.map(f), (y * width + x) * 4)
  set(1, 1, [0.97, 0.11, 0.29, 0.23])
  set(width - 2, 1, [0.19, 0.89, 0.37, 0.41])
  set(2, height - 2, [0.43, 0.17, 0.93, 0.59])
  set(width - 3, height - 2, [0.73, 0.61, 0.07, 0.83])
  set(Math.floor(width / 2), Math.floor(height / 2), [0.53, 0.79, 0.31, 0.71])
  return surface
}

function clampSurface(width, height) {
  const surface = patternedSurface(width, height, 57)
  surface.data[0] = f(-1.5)
  surface.data[1] = f(2.25)
  surface.data[2] = f(-0.75)
  surface.data[3] = f(0.3125)
  surface.data[8] = f(3.5)
  surface.data[9] = f(-2.0)
  surface.data[10] = f(1.75)
  surface.data[11] = f(0.6875)
  return surface
}

const base = { amount: 1, angle: 135, embossHeight: 1, colorAmount: 100, renderScale: 1, time: 0, frame: 0, externalSeed: 0 }
const cases = [
  { name: 'full-frame-default-nonsquare', width: 9, height: 6, phase: 1, ...base, coverage: ['full frame', 'default helper', 'non-square'] },
  { name: 'general-angle-only', width: 9, height: 6, phase: 2, ...base, angle: 17.25, coverage: ['general helper by angle only'] },
  { name: 'general-height-only', width: 9, height: 6, phase: 3, ...base, embossHeight: 2, coverage: ['general helper by height only'] },
  { name: 'general-rotation-extreme', width: 5, height: 5, phase: 4, ...base, angle: -315, embossHeight: 10, amount: 5, renderScale: 0.01, coverage: ['rotation', 'height/amount metadata extrema', 'rotatedPx Float32 materialization witness'] },
  { name: 'default-fractional-scale', width: 8, height: 5, phase: 5, filter: 'linear', ...base, amount: 0.1, renderScale: 0.375, coverage: ['default fractional amount/scale', 'linear sampler exposes omitted amount/renderScale'] },
  { name: 'general-fractional-scale', width: 2, height: 2, phase: 6, filter: 'linear', ...base, angle: -360, amount: 0.1, renderScale: 0.375, coverage: ['general fractional amount/scale', 'linear sampler exposes offsetUV Float32 materialization'] },
  { name: 'fullresolution-x-mismatch-only', width: 7, height: 5, phase: 7, filter: 'linear', ...base, angle: 31, fullResolution: [13, 5], coverage: ['tile equality true', 'resolution bvec heterogeneous', 'linear branch-arm discriminator'] },
  { name: 'fullresolution-both-mismatch', width: 7, height: 5, phase: 8, ...base, angle: 31, fullResolution: [13, 11], coverage: ['tile equality true', 'resolution both false'] },
  { name: 'tile-x-offset-only', width: 7, height: 5, phase: 9, ...base, angle: 31, tileOffset: [2, 0], fullResolution: [7, 5], coverage: ['tile bvec heterogeneous', 'resolution equality true'] },
  { name: 'both-frame-terms-false', width: 7, height: 5, phase: 10, ...base, angle: 31, tileOffset: [2, 3], fullResolution: [13, 11], coverage: ['both full-frame terms false'] },
  { name: 'clamp-and-alpha', width: 7, height: 5, special: 'clamp', ...base, coverage: ['negative and above-one RGB', 'nontrivial alpha'] },
  { name: 'coloramount-control-low', width: 8, height: 6, phase: 12, ...base, colorAmount: 0, coverage: ['STYLE0 colorAmount dead-use control'] },
  { name: 'coloramount-control-high', width: 8, height: 6, phase: 12, ...base, colorAmount: 100, sameAs: 'coloramount-control-low', coverage: ['STYLE0 colorAmount dead-use control'] },
  { name: 'external-context-base', width: 8, height: 6, phase: 13, ...base, coverage: ['external context reference'] },
  { name: 'external-context-extreme', width: 8, height: 6, phase: 13, ...base, time: 16777216, frame: 4294967295, externalSeed: 4294967295, sameAs: 'external-context-base', coverage: ['unused external context'] },
  { name: 'default-asymmetric-impulse', width: 5, height: 7, special: 'asymmetric', ...base, amount: 4.999999, renderScale: 0.1, coverage: ['all default table positions', 'default/general Float32 materialization discriminator'] },
  { name: 'general-asymmetric-impulse', width: 9, height: 7, special: 'asymmetric', ...base, angle: 100, embossHeight: 1, amount: 1, coverage: ['all general table positions'] },
]

function compileMutant(name, from, to, requiredWitnesses) {
  const count = canonicalText.split(from).length - 1
  if (count !== 1) throw new Error(`${name}: mutation anchor matched ${count} times`)
  const mutatedText = canonicalText.replace(from, to)
  return {
    name,
    factory: Function(`"use strict"; return (${mutatedText});`)(),
    anchor_sha256: sha256(from),
    replacement_sha256: sha256(to),
    factory_sha256: sha256(mutatedText),
    required_witnesses: requiredWitnesses,
  }
}

const dispatch = 'if ((angle == 135) && (height == 1)) {'
const defaultKernel = 'function colorDefaultEmboss (uv, texelSize) {\n  \tuv = $runtime.copy(uv);\n  \ttexelSize = $runtime.copy(texelSize);\n  \tvar kernel = [0, 0, 0, 0, 0, 0, 0, 0, 0];\n  \tkernel[0] = -2;'
const generalKernel = 'function colorGeneralEmboss (uv, texelSize) {\n  \tuv = $runtime.copy(uv);\n  \ttexelSize = $runtime.copy(texelSize);\n  \tvar kernel = [0, 0, 0, 0, 0, 0, 0, 0, 0];\n  \tkernel[0] = -2;'
const rotated = 'var rotatedPx = new $runtime.PooledFloat32Array([(ct * basePx[0] + st * basePx[1]) * height, (-st * basePx[0] + ct * basePx[1]) * height]);'
const offsetUv = 'var offsetUV = new $runtime.PooledFloat32Array([((rotatedPx[0] * texelSize[0]) * amount) * renderScale, ((rotatedPx[1] * texelSize[1]) * amount) * renderScale]);'
const fullFrame = 'var fullFrame = (all(equal(tileOffset, new $runtime.PooledFloat32Array([0, 0])))) && (all(equal(fullResolution, resolution)));'
const mutants = [
  compileMutant('dispatch-force-general', dispatch, 'if (false) {', ['default-asymmetric-impulse']),
  compileMutant('dispatch-force-default', dispatch, 'if (true) {', ['general-rotation-extreme']),
  compileMutant('dispatch-drop-angle-half', dispatch, 'if (height == 1) {', ['general-angle-only']),
  compileMutant('dispatch-drop-height-half', dispatch, 'if (angle == 135) {', ['general-height-only']),
  compileMutant('dispatch-and-to-or', dispatch, 'if ((angle == 135) || (height == 1)) {', ['general-angle-only']),
  compileMutant('default-kernel-0-minus-one', defaultKernel, defaultKernel.replace('kernel[0] = -2;', 'kernel[0] = -1;'), ['default-asymmetric-impulse']),
  compileMutant('general-kernel-0-minus-one', generalKernel, generalKernel.replace('kernel[0] = -2;', 'kernel[0] = -1;'), ['general-asymmetric-impulse']),
  compileMutant('default-loop-eight', 'for (var i = 0; i < 9; i++) {\n  \tvar texSample', 'for (var i = 0; i < 8; i++) {\n  \tvar texSample', ['default-asymmetric-impulse']),
  compileMutant('general-loop-eight', 'for (var i = 0; i < 9; i++) {\n  \tvar basePx', 'for (var i = 0; i < 8; i++) {\n  \tvar basePx', ['general-asymmetric-impulse']),
  compileMutant('default-offset-0-flip-x', '(offsets[0][0] = -texelSize[0], offsets[0][1] = -texelSize[1], offsets[0]);', '(offsets[0][0] = texelSize[0], offsets[0][1] = -texelSize[1], offsets[0]);', ['default-asymmetric-impulse']),
  compileMutant('general-base-offset-0-flip-x', '(baseOffsetsPx[0][0] = -1, baseOffsetsPx[0][1] = -1, baseOffsetsPx[0]);', '(baseOffsetsPx[0][0] = 1, baseOffsetsPx[0][1] = -1, baseOffsetsPx[0]);', ['general-asymmetric-impulse']),
  compileMutant('general-rotation-y-sign', '(-st * basePx[0] + ct * basePx[1]) * height', '(st * basePx[0] + ct * basePx[1]) * height', ['general-rotation-extreme']),
  compileMutant('rotatedpx-no-f32-array', rotated, 'var rotatedPx = [(ct * basePx[0] + st * basePx[1]) * height, (-st * basePx[0] + ct * basePx[1]) * height];', ['general-rotation-extreme']),
  compileMutant('offsetuv-no-f32-array', offsetUv, 'var offsetUV = [((rotatedPx[0] * texelSize[0]) * amount) * renderScale, ((rotatedPx[1] * texelSize[1]) * amount) * renderScale];', ['general-fractional-scale']),
  compileMutant('default-omit-amount', '[(uv[0] + (offsets[i][0] * amount) * renderScale) * fullResolution[0] - tileOffset[0], (uv[1] + (offsets[i][1] * amount) * renderScale) * fullResolution[1] - tileOffset[1]]', '[(uv[0] + offsets[i][0] * renderScale) * fullResolution[0] - tileOffset[0], (uv[1] + offsets[i][1] * renderScale) * fullResolution[1] - tileOffset[1]]', ['default-fractional-scale']),
  compileMutant('general-omit-amount', offsetUv, 'var offsetUV = new $runtime.PooledFloat32Array([(rotatedPx[0] * texelSize[0]) * renderScale, (rotatedPx[1] * texelSize[1]) * renderScale]);', ['general-fractional-scale']),
  compileMutant('default-omit-render-scale', '[(uv[0] + (offsets[i][0] * amount) * renderScale) * fullResolution[0] - tileOffset[0], (uv[1] + (offsets[i][1] * amount) * renderScale) * fullResolution[1] - tileOffset[1]]', '[(uv[0] + offsets[i][0] * amount) * fullResolution[0] - tileOffset[0], (uv[1] + offsets[i][1] * amount) * fullResolution[1] - tileOffset[1]]', ['default-fractional-scale']),
  compileMutant('general-omit-render-scale', offsetUv, 'var offsetUV = new $runtime.PooledFloat32Array([(rotatedPx[0] * texelSize[0]) * amount, (rotatedPx[1] * texelSize[1]) * amount]);', ['general-fractional-scale']),
  compileMutant('resolution-equal-to-notequal', 'all(equal(fullResolution, resolution))', 'all($runtime.stdlib.notEqual(fullResolution, resolution))', ['fullresolution-both-mismatch']),
  compileMutant('resolution-all-to-any', 'all(equal(fullResolution, resolution))', '$runtime.stdlib.any(equal(fullResolution, resolution))', ['fullresolution-x-mismatch-only']),
  compileMutant('fullframe-and-to-or', fullFrame, fullFrame.replace(' && ', ' || '), ['fullresolution-x-mismatch-only']),
  compileMutant('true-arm-swizzle', 'var colorTexelSize = fullFrame ? texelSize :', 'var colorTexelSize = fullFrame ? new $runtime.PooledFloat32Array([texelSize[1], texelSize[0]]) :', ['full-frame-default-nonsquare']),
  compileMutant('false-arm-use-local-size', 'var colorTexelSize = fullFrame ? texelSize : new $runtime.PooledFloat32Array([1 / fullResolution[0], 1 / fullResolution[1]]);', 'var colorTexelSize = fullFrame ? texelSize : texelSize;', ['both-frame-terms-false']),
  compileMutant('fullframe-force-true', fullFrame, 'var fullFrame = true;', ['both-frame-terms-false']),
  compileMutant('sample-numerator-use-local-size', '(uv[0] + offsetUV[0]) * fullResolution[0]', '(uv[0] + offsetUV[0]) * textureSize(inputTex, 0)[0]', ['both-frame-terms-false']),
  compileMutant('sample-denominator-use-full-size', 'offsetUV[1]) * fullResolution[1] - tileOffset[1]])), textureSize(inputTex, 0)))));', 'offsetUV[1]) * fullResolution[1] - tileOffset[1]])), fullResolution))));', ['both-frame-terms-false']),
  compileMutant('remove-final-clamp', 'new $runtime.PooledFloat32Array([...clamp(result, 0, 1), origColor[3]])', 'new $runtime.PooledFloat32Array([...result, origColor[3]])', ['clamp-and-alpha']),
  compileMutant('alpha-force-one', 'new $runtime.PooledFloat32Array([...clamp(result, 0, 1), origColor[3]])', 'new $runtime.PooledFloat32Array([...clamp(result, 0, 1), 1])', ['clamp-and-alpha']),
  compileMutant('style-zero-to-one', 'if (STYLE == 0) {', 'if (STYLE == 1) {', ['coloramount-control-low', 'coloramount-control-high', 'default-asymmetric-impulse']),
]

const structuralMutations = [
  ['tile-equal-to-notequal', 'equal(tileOffset, new $runtime.PooledFloat32Array([0, 0]))', '$runtime.stdlib.notEqual(tileOffset, new $runtime.PooledFloat32Array([0, 0]))'],
  ['tile-all-to-any', 'all(equal(tileOffset, new $runtime.PooledFloat32Array([0, 0])))', '$runtime.stdlib.any(equal(tileOffset, new $runtime.PooledFloat32Array([0, 0])))'],
  ['true-arm-use-canvas-size', 'fullFrame ? texelSize :', 'fullFrame ? new $runtime.PooledFloat32Array([1 / fullResolution[0], 1 / fullResolution[1]]) :'],
  ['fullframe-force-false', fullFrame, 'var fullFrame = false;'],
].map(([name, from, to]) => {
  const count = canonicalText.split(from).length - 1
  if (count !== 1) throw new Error(`${name}: structural anchor matched ${count} times`)
  return { name, anchor_sha256: sha256(from), replacement_sha256: sha256(to), mutated_factory_sha256: sha256(canonicalText.replace(from, to)), pixel_expectation: 'structurally authenticated rejection; pixel identity is algebraically expected' }
})

function makeInput(definition) {
  let surface
  if (definition.special === 'asymmetric') surface = asymmetricSurface(definition.width, definition.height)
  else if (definition.special === 'clamp') surface = clampSurface(definition.width, definition.height)
  else surface = patternedSurface(definition.width, definition.height, definition.phase)
  if (definition.filter === 'linear') surface.filter = 'linear'
  return surface
}

function render(factory, definition) {
  const input = makeInput(definition)
  const before = new Uint32Array(input.data.buffer, input.data.byteOffset, input.data.length).slice()
  const tileOffset = new Float32Array((definition.tileOffset ?? [0, 0]).map(f))
  const fullResolution = new Float32Array((definition.fullResolution ?? [definition.width, definition.height]).map(f))
  const uniforms = {
    STYLE: 0,
    amount: f(definition.amount),
    angle: f(definition.angle),
    height: f(definition.embossHeight),
    colorAmount: f(definition.colorAmount),
    renderScale: f(definition.renderScale),
  }
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: definition.frame,
    seed: definition.externalSeed,
    uniforms,
    textures: { inputTex: input },
    tileOffset,
    fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel: bindGlslKernel(factory, bindings), destination: output, time: definition.time, seed: definition.externalSeed })
  const after = new Uint32Array(input.data.buffer, input.data.byteOffset, input.data.length)
  if (before.some((word, index) => word !== after[index])) throw new Error(`${definition.name}: input mutated`)
  if (output.data.some((value) => !Number.isFinite(value))) throw new Error(`${definition.name}: non-finite output`)
  return { output, input, inputBefore: before, inputAfter: after }
}

function selectedProbes(surface) {
  const points = [
    ['top-left', 0, 0],
    ['top-right', surface.width - 1, 0],
    ['bottom-left', 0, surface.height - 1],
    ['bottom-right', surface.width - 1, surface.height - 1],
    ['center', Math.floor(surface.width / 2), Math.floor(surface.height / 2)],
  ]
  return points.map(([label, x, y]) => {
    const offset = (y * surface.width + x) * 4
    const values = Array.from(surface.data.slice(offset, offset + 4))
    return { label, top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
  })
}

const rendered = new Map()
const renderCases = cases.map((definition) => {
  const direct = render(canonicalFactory, definition)
  const repeat = render(canonicalFactory, definition)
  const publicResult = render(publicFactory, definition)
  const repeatComparison = compareSurfaces(direct.output, repeat.output)
  const publicComparison = compareSurfaces(direct.output, publicResult.output)
  if (!repeatComparison.float32.exact_f32_bits || !repeatComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: repeat drift`)
  if (!publicComparison.float32.exact_f32_bits || !publicComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: public/direct drift`)
  rendered.set(definition.name, direct.output)
  const rgba8 = direct.output.toRgba8()
  const words = new Uint32Array(direct.output.data.buffer, direct.output.data.byteOffset, direct.output.data.length)
  return {
    name: definition.name,
    width: definition.width,
    height: definition.height,
    input_kind: definition.special ?? 'patterned',
    input_filter: definition.filter ?? 'nearest',
    input_phase: definition.phase ?? 0,
    controls: {
      style: 0,
      amount: f(definition.amount),
      angle: f(definition.angle),
      height: f(definition.embossHeight),
      color_amount: f(definition.colorAmount),
      render_scale: f(definition.renderScale),
      time: f(definition.time),
      frame: definition.frame,
      external_seed: definition.externalSeed,
      tile_offset: Array.from(new Float32Array((definition.tileOffset ?? [0, 0]).map(f))),
      full_resolution: Array.from(new Float32Array((definition.fullResolution ?? [definition.width, definition.height]).map(f))),
    },
    coverage: definition.coverage,
    declared_identity_case: definition.sameAs ?? null,
    input_f32_sha256_before: sha256(bytes(direct.input.data)),
    input_f32_sha256_after: sha256(bytes(direct.input.data)),
    input_immutable_exact_bits: true,
    input_probes: selectedProbes(direct.input),
    output_f32_words_le: Array.from(words, u32Hex),
    output_rgba8_bytes: Array.from(rgba8),
    output_f32_sha256: sha256(bytes(direct.output.data)),
    output_rgba8_sha256: sha256(bytes(rgba8)),
    finite_lane_count: direct.output.data.length,
    nonfinite_lane_count: 0,
    output_probes: selectedProbes(direct.output),
    repeat_identity: repeatComparison,
    public_catalog_vs_direct_canonical: publicComparison,
  }
})

for (const definition of cases) {
  if (!definition.sameAs) continue
  const comparison = compareSurfaces(rendered.get(definition.sameAs), rendered.get(definition.name))
  if (!comparison.float32.exact_f32_bits || !comparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: declared identity failed`)
}

const mutationResults = mutants.map((mutant) => {
  const comparisons = cases.map((definition) => ({ case: definition.name, ...compareSurfaces(rendered.get(definition.name), render(mutant.factory, definition).output) }))
  const requiredResults = []
  for (const witness of mutant.required_witnesses) {
    const comparison = comparisons.find((item) => item.case === witness)
    if (comparison?.float32.exact_f32_bits !== false) throw new Error(`${mutant.name}: witness ${witness} did not diverge`)
    requiredResults.push({
      case: witness,
      changed_lane_count: comparison.float32.mismatched_lanes,
      first_mismatch: comparison.float32.first_mismatch,
      changed_rgba8_byte_count: comparison.rgba8.mismatched_bytes,
      first_rgba8_mismatch: comparison.rgba8.first_mismatch,
    })
  }
  if (mutant.name === 'style-zero-to-one') {
    const low = render(mutant.factory, cases.find((item) => item.name === 'coloramount-control-low')).output
    const high = render(mutant.factory, cases.find((item) => item.name === 'coloramount-control-high')).output
    if (compareSurfaces(low, high).float32.exact_f32_bits) throw new Error('STYLE mutant did not activate colorAmount')
  }
  const firstRequired = requiredResults[0]
  return {
    name: mutant.name,
    factory_sha256: mutant.factory_sha256,
    anchor_sha256: mutant.anchor_sha256,
    replacement_sha256: mutant.replacement_sha256,
    required_witnesses: mutant.required_witnesses,
    required_witness_results: requiredResults,
    divergent_f32_cases: comparisons.filter((item) => !item.float32.exact_f32_bits).map((item) => item.case),
    divergent_rgba8_cases: comparisons.filter((item) => !item.rgba8.exact_rgba8_bytes).map((item) => item.case),
    changed_lane_count_at_first_required_witness: firstRequired.changed_lane_count,
    first_mismatch_at_first_required_witness: firstRequired.first_mismatch,
  }
})

const fixture = {
  schema: 'noisemaker-for-cpp.emboss181.pixel-parity.v1',
  program_key: programKey,
  corpus_revision: corpusRevision,
  upstream_revision: UPSTREAM_REVISION,
  oracle_authority: 'clean pinned noisemaker-for-cpu canonicalFactory50 under pinned Node; no C++ output participates',
  exactness_contract: {
    float32: 'complete raw little-endian uint32 lane arrays; signed zero and NaN payloads are significant',
    rgba8: 'complete independently captured Surface.toRgba8 byte arrays',
    tolerance: 'none',
    comparison_order: 'dimensions, lane count, every Float32 word, independently supplied byte count, every RGBA8 byte',
  },
  provenance: {
    authority_commit: authorityCommit,
    authority_checkout_clean: true,
    node_version: process.version,
    files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, expectedHash]]) => [name, { relative_path_from_noisemaker_for_cpu: relativePath, sha256: expectedHash }])),
    import_closure: importClosureRecords,
    source: { relative_path_from_noisemaker_for_cpp: path.relative(cppRoot, sourcePath), bytes: sourceBytes.length, sha256: sha256(sourceBytes), style0_normalized_bytes: 4052, style0_normalized_sha256: '8f6426db42dac9e25c2051a858616efa79350d4236f5a3f49f7e5a4a5f9a3e3c' },
    canonical_factory: { name: canonicalFactory.name, bytes: Buffer.byteLength(canonicalText), sha256: sha256(canonicalText) },
    public_factory_is_canonical_identity: true,
    adapter_override_absent: true,
    metadata: effect,
    style_define: { exact: 0, gray_style_excluded_from_native_authority: 1 },
    single_pass_interface: effect.passes[0],
  },
  comparer_self_tests: comparerSelfTests(),
  frontend_probe: frontendProof,
  render_cases: renderCases,
  behavioral_mutation_ledger: mutationResults,
  structural_only_mutation_ledger: structuralMutations,
  identity_pairs: [
    ['coloramount-control-low', 'coloramount-control-high'],
    ['external-context-base', 'external-context-extreme'],
  ],
}

function reportFor(data) {
  const caseRows = data.render_cases.map((item) => `| ${item.name} | ${item.width}x${item.height} | ${item.output_f32_sha256} | ${item.output_rgba8_sha256} |`).join('\n')
  const mutationRows = data.behavioral_mutation_ledger.map((item) => `| ${item.name} | ${item.required_witnesses.join(', ')} | ${item.changed_lane_count_at_first_required_witness} | ${item.first_mismatch_at_first_required_witness.top_down_xy.join(',')}/${item.first_mismatch_at_first_required_witness.channel} |`).join('\n')
  const structuralRows = data.structural_only_mutation_ledger.map((item) => `| ${item.name} | ${item.pixel_expectation} |`).join('\n')
  return `# Emboss181 exact-parity oracle\n\nProgram \`${data.program_key}\`; corpus revision \`${data.corpus_revision}\`.\n\n## Result\n\nSeventeen canonical STYLE=0 fixtures store complete Float32 words and independently captured RGBA8 bytes. The suite covers both dispatch helpers, all four full-frame equality combinations, fractional scale, rotation/extrema, clamp/alpha, retained-but-dead colorAmount, external context, and asymmetric table witnesses. No C++ render contributes expected data.\n\n## Exact contract\n\n- Dimensions and lane/byte counts are checked before payloads.\n- Float32 equality is raw-word equality, including signed zero and NaN payloads.\n- RGBA8 is compared separately from independently supplied canonical bytes.\n- Every case proves repeat identity, direct/public identity, finite output, input immutability, hashes, and at least five probes.\n\n## Render fixtures\n\n| Case | Size | Float32 SHA-256 | RGBA8 SHA-256 |\n| --- | --- | --- | --- |\n${caseRows}\n\n## Behavioral mutations\n\n| Mutation | Required witness | Changed lanes at first divergent case | First x,y/channel |\n| --- | --- | ---: | --- |\n${mutationRows}\n\nEach row is an independent exact one-anchor/one-replacement mutant. Every named witness differs in at least one raw Float32 word.\n\n## Structural-only mutations\n\n| Mutation | Contract |\n| --- | --- |\n${structuralRows}\n\nThese four rows are intentionally not assigned false pixel witnesses: their shipped-pixel behavior is algebraically unobservable, while exact source authentication rejects them.\n\n## Regeneration\n\n\`\`\`sh\nnode docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --write\nnode docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --check\npython3 docs/port-engineering/arrays/emboss-parity/generate_emboss_native_oracle_include.py --write\npython3 docs/port-engineering/arrays/emboss-parity/generate_emboss_native_oracle_include.py --check\n\`\`\`\n\nBoth generators validate pinned authority, complete arrays, checksums, the fixture census, and the full mutation ledger before accepting checked output.\n`
}

function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function verifySidecar(target) {
  const sidecar = sidecarPath(target)
  if (!fs.existsSync(target) || !fs.existsSync(sidecar)) throw new Error(`missing checked asset or sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecar, 'utf8') !== sidecarText(target, payload)) throw new Error(`checksum sidecar drift: ${target}`)
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture).replace(
  'emboss_parity_oracle_generator.mjs --write\n'
    + 'node docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --check',
  'emboss_parity_oracle_generator.mjs --write --cpu-root "$NOISEMAKER_CPU_ROOT"\n'
    + 'node docs/port-engineering/arrays/emboss-parity/emboss_parity_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"',
)
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
  if (fs.readFileSync(outputPath, 'utf8') !== jsonText) throw new Error('Emboss oracle JSON drift')
  if (fs.readFileSync(reportPath, 'utf8') !== reportText) throw new Error('Emboss oracle report drift')
}
console.log(`Emboss181 oracle ${write ? 'written' : 'checked'}: ${renderCases.length} renders, ${mutationResults.length} behavioral mutations, ${structuralMutations.length} structural-only mutations`)
