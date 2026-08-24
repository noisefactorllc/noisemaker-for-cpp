import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'


const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../../..'))
const outputPath = path.join(here, 'glitch-parity-oracles.json')
const reportPath = path.join(here, 'glitch-parity-oracle-report.md')
const generatorPath = fileURLToPath(import.meta.url)
const frontendProbePath = path.join(here, 'glitch_matrix_frontend_probe.py')
const programKey = 'classicNoisedeck/glitch:glitch'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision, 'sources/classicNoisedeck/glitch/glitch.glsl')
const f = Math.fround

// ---------------------------------------------------------------------------
// Arguments and publication-root confinement
// ---------------------------------------------------------------------------

const argv = process.argv.slice(2)
const modes = argv.filter((token) => token === '--write' || token === '--check')
if (modes.length !== 1) throw new Error('choose exactly one of --write or --check')
const mode = modes[0]
const cpuRootIndex = argv.indexOf('--cpu-root')
if (cpuRootIndex < 0 || cpuRootIndex + 1 >= argv.length) {
  throw new Error('--cpu-root <immutable snapshot> is required')
}
for (const [index, token] of argv.entries()) {
  if (index === cpuRootIndex || index === cpuRootIndex + 1) continue
  if (token !== mode) throw new Error(`unexpected argument: ${token}`)
}

function validateRoot(argument, label) {
  const candidate = path.resolve(argument)
  let stat
  try {
    stat = fs.lstatSync(candidate)
  } catch {
    throw new Error(`${label} must be an existing non-symlink directory: ${argument}`)
  }
  if (stat.isSymbolicLink() || !stat.isDirectory()) {
    throw new Error(`${label} must be an existing non-symlink directory: ${argument}`)
  }
  return fs.realpathSync(candidate)
}

const beneath = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`)
const cpuRoot = validateRoot(argv[cpuRootIndex + 1], '--cpu-root')
const liveArgument = process.env.NOISEMAKER_FOR_CPU
if (!liveArgument) throw new Error('NOISEMAKER_FOR_CPU live checkout is required')
const liveRoot = validateRoot(liveArgument, 'NOISEMAKER_FOR_CPU')
let liveIdentity
try {
  liveIdentity = JSON.parse(fs.readFileSync(path.join(liveRoot, 'package.json'), 'utf8')).name
} catch {
  throw new Error('NOISEMAKER_FOR_CPU is not a noisemaker-cpu checkout')
}
if (liveIdentity !== 'noisemaker-cpu') throw new Error('NOISEMAKER_FOR_CPU is not a noisemaker-cpu checkout')
if (cpuRoot === liveRoot || beneath(cpuRoot, liveRoot) || beneath(liveRoot, cpuRoot)) {
  throw new Error('authority and live checkout must be distinct, non-overlapping roots')
}
if (beneath(cppRoot, cpuRoot) || beneath(cpuRoot, cppRoot)
    || beneath(cppRoot, liveRoot) || beneath(liveRoot, cppRoot)) {
  throw new Error('authority and live checkout must be external to the C++ repository')
}

function confine(candidate, why) {
  let stat
  try { stat = fs.lstatSync(candidate) } catch { throw new Error(`${why} is missing: ${candidate}`) }
  if (stat.isSymbolicLink()) throw new Error(`${why} must not be a symlink: ${candidate}`)
  const real = fs.realpathSync(candidate)
  if (!beneath(cpuRoot, real) || beneath(liveRoot, real) || beneath(cppRoot, real)) {
    throw new Error(`${why} escaped the immutable authority: ${real}`)
  }
  return real
}

function importClosure() {
  const patterns = [
    /\bfrom\s*['"]([^'"\n]+)['"]/g,
    /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
    /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
  ]
  const entries = [
    'src/effects/catalog.js',
    'src/effects/generated/upstream-snapshot.js',
    'src/csl/glsl-kernel.js',
    'src/csl/glsl-runtime.js',
    'src/runtime/pass-runner.js',
    'src/runtime/surface.js',
  ]
  const stack = entries.map((relative) => path.join(cpuRoot, relative))
  const seen = new Map()
  while (stack.length) {
    const candidate = stack.pop()
    const resolved = confine(candidate, 'import closure file')
    if (seen.has(resolved)) continue
    const payload = fs.readFileSync(resolved)
    const text = payload.toString('utf8')
    seen.set(resolved, sha256(payload))
    if (/\bimport\s*\(\s*(?!['"])/.test(text)) {
      throw new Error(`nonliteral dynamic import: ${path.relative(cpuRoot, resolved)}`)
    }
    for (const pattern of patterns) {
      pattern.lastIndex = 0
      let match
      while ((match = pattern.exec(text))) {
        const specifier = match[1]
        if (specifier.startsWith('node:')) continue
        if (!specifier.startsWith('./') && !specifier.startsWith('../')) {
          throw new Error(`invalid module specifier ${specifier}`)
        }
        stack.push(path.resolve(path.dirname(resolved), specifier))
      }
    }
  }
  return [...seen].map(([file, hash]) => [path.relative(cpuRoot, file), hash])
    .sort((left, right) => left[0].localeCompare(right[0]))
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex')
}

function bytes(view) {
  return Buffer.from(view.buffer, view.byteOffset, view.byteLength)
}

function u32Hex(value) {
  return `0x${(value >>> 0).toString(16).padStart(8, '0')}`
}

function f32Bits(value) {
  const lane = new Float32Array([value])
  return u32Hex(new DataView(lane.buffer).getUint32(0, true))
}

// Purpose-built Glitch comparer. Float32 equality means raw lane-bit equality,
// including signed zero and NaN payloads. RGBA8 is a separate output contract,
// never a tolerance or a substitute for the Float32 contract.
function compareFloat32Surfaces(reference, candidate) {
  if (!(reference?.data instanceof Float32Array) || !(candidate?.data instanceof Float32Array)) {
    throw new TypeError('compareFloat32Surfaces requires two Float32 Surface values')
  }
  if (reference.width !== candidate.width || reference.height !== candidate.height || reference.data.length !== candidate.data.length) {
    return {
      exact_f32_bits: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_lanes: Math.max(reference.data.length, candidate.data.length),
      first_mismatch: null,
      max_absolute_difference: null,
    }
  }
  const left = new Uint32Array(reference.data.buffer, reference.data.byteOffset, reference.data.length)
  const right = new Uint32Array(candidate.data.buffer, candidate.data.byteOffset, candidate.data.length)
  let mismatched = 0
  let first = null
  let maxAbsoluteDifference = 0
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] === right[index]) continue
    mismatched += 1
    if (first === null) {
      const pixel = Math.floor(index / 4)
      first = {
        lane_index: index,
        pixel_index: pixel,
        top_down_xy: [pixel % reference.width, Math.floor(pixel / reference.width)],
        channel: ['r', 'g', 'b', 'a'][index % 4],
        reference_value: Number.isFinite(reference.data[index]) ? reference.data[index] : String(reference.data[index]),
        candidate_value: Number.isFinite(candidate.data[index]) ? candidate.data[index] : String(candidate.data[index]),
        reference_bits_le: u32Hex(left[index]),
        candidate_bits_le: u32Hex(right[index]),
      }
    }
    const difference = Math.abs(reference.data[index] - candidate.data[index])
    if (Number.isFinite(difference)) maxAbsoluteDifference = Math.max(maxAbsoluteDifference, difference)
  }
  return {
    exact_f32_bits: mismatched === 0,
    dimensions_match: true,
    reference_dimensions: [reference.width, reference.height],
    candidate_dimensions: [candidate.width, candidate.height],
    mismatched_lanes: mismatched,
    first_mismatch: first,
    max_absolute_difference: maxAbsoluteDifference,
  }
}

function compareRgba8Surfaces(reference, candidate) {
  if (reference.width !== candidate.width || reference.height !== candidate.height) {
    return {
      exact_rgba8_bytes: false,
      dimensions_match: false,
      reference_dimensions: [reference.width, reference.height],
      candidate_dimensions: [candidate.width, candidate.height],
      mismatched_bytes: Math.max(reference.data.length, candidate.data.length),
      first_mismatch: null,
    }
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
        pixel_index: pixel,
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
  return {
    float32: compareFloat32Surfaces(reference, candidate),
    rgba8: compareRgba8Surfaces(reference, candidate),
    candidate_f32_sha256: sha256(bytes(candidate.data)),
    candidate_rgba8_sha256: sha256(bytes(candidate.toRgba8())),
  }
}

function compareF32Lanes(reference, candidate) {
  if (reference.length !== candidate.length) {
    return { exact_f32_bits: false, mismatched_lanes: Math.max(reference.length, candidate.length), first_mismatch: null }
  }
  const left = new Float32Array(reference)
  const right = new Float32Array(candidate)
  const leftBits = new Uint32Array(left.buffer)
  const rightBits = new Uint32Array(right.buffer)
  let mismatched = 0
  let first = null
  for (let index = 0; index < left.length; index += 1) {
    if (leftBits[index] === rightBits[index]) continue
    mismatched += 1
    if (first === null) first = {
      lane_index: index,
      reference_value: left[index],
      candidate_value: right[index],
      reference_bits_le: u32Hex(leftBits[index]),
      candidate_bits_le: u32Hex(rightBits[index]),
    }
  }
  return { exact_f32_bits: mismatched === 0, mismatched_lanes: mismatched, first_mismatch: first }
}

function comparerSelfTests() {
  const oneByTwo = new Surface(1, 2, new Float32Array(8))
  const twoByOne = new Surface(2, 1, new Float32Array(8))
  const dimensions = compareSurfaces(oneByTwo, twoByOne)
  if (dimensions.float32.exact_f32_bits || dimensions.rgba8.exact_rgba8_bytes) {
    throw new Error('custom comparer accepted an equal-length dimension mismatch')
  }
  const plusZero = new Surface(1, 1, new Float32Array([0, 0, 0, 1]))
  const minusZero = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]))
  const signedZero = compareSurfaces(plusZero, minusZero)
  if (signedZero.float32.exact_f32_bits || !signedZero.rgba8.exact_rgba8_bytes || signedZero.float32.first_mismatch?.channel !== 'r') {
    throw new Error('custom comparer did not expose signed-zero Float32 difference')
  }
  return {
    equal_length_dimension_mismatch_rejected: true,
    signed_zero_float32_mismatch_rejected: true,
    rgba8_quantization_does_not_replace_float32_contract: true,
    signed_zero_first_mismatch: signedZero.float32.first_mismatch,
  }
}

const provenanceFiles = {
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  glsl_runtime: ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
}

const actualImportClosure = importClosure()
const load = (relative) => import(pathToFileURL(confine(path.join(cpuRoot, relative), 'load')).href)
const [
  { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories },
  { effectRecords, UPSTREAM_REVISION },
  { createCanonicalBindings },
  { bindGlslKernel, GlslCpuRuntime },
  { runPass },
  { Surface },
] = await Promise.all([
  load('src/effects/catalog.js'),
  load('src/effects/generated/upstream-snapshot.js'),
  load('src/csl/glsl-kernel.js'),
  load('src/csl/glsl-runtime.js'),
  load('src/runtime/pass-runner.js'),
  load('src/runtime/surface.js'),
])

for (const [name, [relativePath, expectedHash]] of Object.entries(provenanceFiles)) {
  const actualHash = sha256(fs.readFileSync(path.join(cpuRoot, relativePath)))
  if (actualHash !== expectedHash) throw new Error(`${name} provenance drift: ${actualHash}`)
}

const sourceBytes = fs.readFileSync(sourcePath)
if (sourceBytes.length !== 7894 || sha256(sourceBytes) !== '13d6350eb21cfb5a7c9f0d0a8fffe8e7495068ca2e082d1520ef14ca5b34c134') {
  throw new Error('pinned Glitch GLSL source drift')
}
const sourceText = sourceBytes.toString('utf8')
const sourceCensus = {
  mat4_constructors: (sourceText.match(/mat4\s*\(/g) ?? []).length,
  mat4_declarations: (sourceText.match(/\bmat4\s+[QSTA]\b/g) ?? []).length,
  chained_product: (sourceText.match(/T \* Q \* S/g) ?? []).length,
  vector_matrix_product: (sourceText.match(/tv \* A/g) ?? []).length,
}
if (JSON.stringify(sourceCensus) !== JSON.stringify({ mat4_constructors: 3, mat4_declarations: 4, chained_product: 1, vector_matrix_product: 1 })) {
  throw new Error(`Glitch matrix source census drift: ${JSON.stringify(sourceCensus)}`)
}

const canonicalFactory = canonicalKernelFactories[programKey]
const publicFactory = kernelFactories.get(programKey)
if (!canonicalFactory || canonicalFactory.name !== 'canonicalFactory8') throw new Error('canonical Glitch factory identity drift')
if (Buffer.byteLength(canonicalFactory.toString()) !== 12695 || sha256(canonicalFactory.toString()) !== 'a97f27931e6ef7c2f909b130b17ec9d036ddad3dffe85ef1cec312cea0eef815') {
  throw new Error('canonical Glitch factory body drift')
}
if (publicFactory !== canonicalFactory) throw new Error('public catalog Glitch factory is not the canonical factory identity')
if (canonicalAdapterFactories[programKey] !== undefined) throw new Error('unexpected Glitch adapter override')

const expectedParams = {
  aberration: { type: 'float', default: 0, min: 0, max: 100, uniform: 'aberration' },
  aspectLens: { type: 'boolean', default: false, uniform: 'aspectLens' },
  distortion: { type: 'float', default: 0, min: -100, max: 100, uniform: 'distortion' },
  glitchiness: { type: 'float', default: 0, min: 0, max: 100, uniform: 'glitchiness' },
  scanlinesAmt: { type: 'int', default: 0, min: 0, max: 100, uniform: 'scanlinesAmt' },
  seed: { type: 'int', default: 1, min: 1, max: 100, uniform: 'seed' },
  snowAmt: { type: 'float', default: 0, min: 0, max: 100, uniform: 'snowAmt' },
  vignetteAmt: { type: 'float', default: 0, min: -100, max: 100, uniform: 'vignetteAmt' },
  xChonk: { type: 'int', default: 1, min: 1, max: 100, uniform: 'xChonk' },
  yChonk: { type: 'int', default: 1, min: 1, max: 100, uniform: 'yChonk' },
}
const effect = effectRecords.find((record) => record.id === 'classicNoisedeck/glitch')
if (!effect) throw new Error('Glitch metadata record missing')
for (const [name, expected] of Object.entries(expectedParams)) {
  for (const [field, value] of Object.entries(expected)) {
    if (JSON.stringify(effect.params?.[name]?.[field]) !== JSON.stringify(value)) throw new Error(`Glitch ${name}.${field} metadata drift`)
  }
}
if (effect.func !== 'glitch' || effect.kind !== 'filter' || effect.namespace !== 'classicNoisedeck' || effect.passes?.length !== 1 || effect.passes[0]?.program !== 'glitch') {
  throw new Error('Glitch effect/pass interface drift')
}

const frontendProcess = spawnSync('python3', ['-B', frontendProbePath], {
  cwd: cppRoot,
  encoding: 'utf8',
  env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
})
if (frontendProcess.status !== 0) throw new Error(`frontend proof failed: ${frontendProcess.stderr || frontendProcess.stdout}`)
const frontendProof = JSON.parse(frontendProcess.stdout)
if (frontendProof.matrix_nodes?.constructs?.length !== 3 || frontendProof.matrix_nodes?.matrix_matrix_products?.length !== 2 || frontendProof.matrix_nodes?.vector_matrix_products?.length !== 1 || frontendProof.identity_gate?.negative_count < 9) {
  throw new Error('Glitch frontend proof contract drift')
}

function roundedMatrixMult(left, right) {
  const dimension = left.length === 16 ? 4 : left.length === 9 ? 3 : 2
  const out = new Float32Array(left.length)
  for (let column = 0; column < dimension; column += 1) {
    for (let row = 0; row < dimension; row += 1) {
      let sum = 0
      for (let inner = 0; inner < dimension; inner += 1) sum += left[inner * dimension + row] * right[column * dimension + inner]
      out[column * dimension + row] = f(sum)
    }
  }
  return out
}

function unroundedMatrixMult(left, right) {
  const dimension = left.length === 16 ? 4 : left.length === 9 ? 3 : 2
  const out = Array(left.length)
  for (let column = 0; column < dimension; column += 1) {
    for (let row = 0; row < dimension; row += 1) {
      let sum = 0
      for (let inner = 0; inner < dimension; inner += 1) sum += left[inner * dimension + row] * right[column * dimension + inner]
      out[column * dimension + row] = sum
    }
  }
  return out
}

const T = new Float32Array([1, 0, -3, 2, 0, 0, 3, -2, 0, 1, -2, 1, 0, 0, -1, 1])
const S = new Float32Array([1, 0, 0, 0, 0, 0, 1, 0, -3, 3, -2, -1, 2, -2, 1, 1])
const directDefinitions = [
  ['identity-q', new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])],
  ['fractional-q', new Float32Array(Array.from({ length: 16 }, (_, index) => f((((index * 37 + 11) % 101) - 50) / 47)))],
  ['wide-dynamic-q', new Float32Array([f(2 ** -20), f(-(2 ** 18)), f(1 / 3), f(-1 / 7), f(65537 / 257), f(-8191 / 127), f(Math.PI), f(-Math.E), f(0.1), f(-0.2), f(0.3), f(-0.4), f(12345.75), f(-5432.125), f(1.0000001192092896), f(-0)])],
  ['pcg-shaped-q-a', new Float32Array([0.90234226, 0.17023332, -0.36605406, 0.20132583, 0.39467546, 0.84033585, 0.28744292, -0.11933017, -0.10522521, 0.33574659, -0.18555322, 0.07234118, 0.21773174, -0.48193428, 0.10238845, -0.0572219].map(f))],
  ['pcg-shaped-q-b', new Float32Array([0.0000001192092896, 0.9999999403953552, -0.4999999701976776, 0.5000000596046448, 0.73123455, 0.12873459, -0.30128214, 0.18999107, 0.67182821, 0.42019439, -0.27770087, 0.06194491, 0.55110264, 0.71990323, -0.41116679, 0.14002931].map(f))],
]

const directRuntime = new GlslCpuRuntime()
const directCases = directDefinitions.map(([name, Q]) => {
  directRuntime.indices.fill(0)
  const runtimeFirst = new Float32Array(directRuntime.stdlib.matrixMult(T, Q))
  const runtimeFinal = new Float32Array(directRuntime.stdlib.matrixMult(runtimeFirst, S))
  const expectedFirst = roundedMatrixMult(T, Q)
  const expectedFinal = roundedMatrixMult(expectedFirst, S)
  const runtimeComparison = compareF32Lanes(expectedFinal, runtimeFinal)
  if (!runtimeComparison.exact_f32_bits) throw new Error(`${name}: shipped runtime matrixMult disagrees with direct F32(sum) model`)
  const rightAssociated = roundedMatrixMult(T, roundedMatrixMult(Q, S))
  const unroundedFinal = new Float32Array(unroundedMatrixMult(unroundedMatrixMult(T, Q), S))
  return {
    name,
    q_f32_bits_le: Array.from(new Uint32Array(Q.buffer), u32Hex),
    first_product_f32_bits_le: Array.from(new Uint32Array(expectedFirst.buffer), u32Hex),
    left_associated_f32_bits_le: Array.from(new Uint32Array(expectedFinal.buffer), u32Hex),
    left_associated_f32_sha256: sha256(bytes(expectedFinal)),
    runtime_exact: runtimeComparison,
    right_associated_comparison: compareF32Lanes(expectedFinal, rightAssociated),
    unrounded_intermediate_comparison: compareF32Lanes(expectedFinal, unroundedFinal),
  }
})

if (!directCases.some((item) => !item.right_associated_comparison.exact_f32_bits)) throw new Error('direct cases do not discriminate right association')
if (!directCases.some((item) => !item.unrounded_intermediate_comparison.exact_f32_bits)) throw new Error('direct cases do not discriminate missing intermediate F32 stores')

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = (y * width + x) * 4
      data[index] = f((((31 * x + 17 * y + 19 * phase + 3) % 101) + 1) / 103)
      data[index + 1] = f((((13 * x + 43 * y + 23 * phase + 5) % 97) + 2) / 101)
      data[index + 2] = f((((47 * x + 7 * y + 29 * phase + 11) % 89) + 3) / 97)
      data[index + 3] = f((((5 * x + 19 * y + 7 * phase) % 31) + 5) / 41)
    }
  }
  data[0] = -0
  if (data.length >= 12) data[9] = f(-0.25)
  if (data.length >= 20) data[18] = f(1.25)
  return new Surface(width, height, data)
}

const cases = [
  { name: 'matrix-masked-control', width: 9, height: 7, phase: 1, time: 0, seed: 1, aspectLens: false, xChonk: 1, yChonk: 1, glitchiness: 0, scanlinesAmt: 0, snowAmt: 0, vignetteAmt: 0, aberration: 0, distortion: 0, coverage: ['matrix closure executes but scanline mix masks it', 'default controls'] },
  { name: 'scanlines-max-seed-one', width: 11, height: 9, phase: 2, time: 0.25, seed: 1, aspectLens: false, xChonk: 1, yChonk: 1, glitchiness: 0, scanlinesAmt: 100, snowAmt: 0, vignetteAmt: 0, aberration: 0, distortion: 0, coverage: ['matrix output observable', 'maximum scanline amount', 'landscape'] },
  { name: 'scanlines-mid-seed-thirty-seven', width: 13, height: 10, phase: 3, time: 12.345, seed: 37, aspectLens: false, xChonk: 17, yChonk: 9, glitchiness: 50, scanlinesAmt: 77, snowAmt: 20, vignetteAmt: 25, aberration: 33, distortion: 40, coverage: ['matrix association witness', 'snow lower branch', 'positive lens', 'positive vignette'] },
  { name: 'scanlines-min-nonzero', width: 17, height: 6, phase: 4, time: -3.125, seed: 100, aspectLens: false, xChonk: 100, yChonk: 100, glitchiness: 100, scanlinesAmt: 1, snowAmt: 0, vignetteAmt: 0, aberration: 100, distortion: 100, coverage: ['metadata extrema', 'minimum nonzero matrix contribution', 'wide aspect'] },
  { name: 'aspect-negative-lens-vignette', width: 7, height: 12, phase: 5, time: -0.75, seed: 99, aspectLens: true, xChonk: 53, yChonk: 17, glitchiness: 83, scanlinesAmt: 91, snowAmt: 49, vignetteAmt: -100, aberration: 100, distortion: -100, coverage: ['aspect lens branch', 'negative distortion branch', 'negative vignette branch', 'snow lower boundary'] },
  { name: 'snow-upper-midpoint', width: 8, height: 8, phase: 6, time: 16777216, seed: 2, aspectLens: true, xChonk: 2, yChonk: 3, glitchiness: 2, scanlinesAmt: 63, snowAmt: 75, vignetteAmt: 100, aberration: 1, distortion: -1, coverage: ['snow upper branch below final saturation', 'large exactly represented time', 'square aspect'] },
  { name: 'snow-saturated-tiled', width: 6, height: 5, phase: 7, time: 100000.125, seed: 73, aspectLens: false, xChonk: 31, yChonk: 67, glitchiness: 71, scanlinesAmt: 88, snowAmt: 100, vignetteAmt: 57, aberration: 77, distortion: 0, tileOffset: [7, 11], fullResolution: [19, 23], coverage: ['snow final saturation branch', 'tile offset', 'full-resolution coordinates'] },
  { name: 'fractional-full-resolution-tile', width: 5, height: 9, phase: 8, time: 0.0009765625, seed: 41, aspectLens: true, xChonk: 7, yChonk: 13, glitchiness: 29, scanlinesAmt: 56, snowAmt: 51, vignetteAmt: -33, aberration: 49, distortion: 1, tileOffset: [3, 2], fullResolution: [17, 29], coverage: ['portrait tile', 'snow upper branch just above midpoint', 'near-zero positive lens'] },
]

function compileMutant(name, replacements, expectedWitnesses) {
  let source = canonicalFactory.toString()
  const anchors = []
  for (const [from, to] of replacements) {
    const pieces = source.split(from)
    if (pieces.length !== 2) throw new Error(`${name}: mutation anchor matched ${pieces.length - 1} times`)
    source = `${pieces[0]}${to}${pieces[1]}`
    anchors.push({ from_sha256: sha256(from), to_sha256: sha256(to) })
  }
  return {
    name,
    factory: Function(`"use strict"; return (${source});`)(),
    factory_sha256: sha256(source),
    anchors,
    expected_witnesses: expectedWitnesses,
  }
}

const matrixLine = 'var A = matrixMult(matrixMult(T, Q), S);'
const floatHelper = 'function cpu_float (value) { return $runtime.stdlib.float(value); };'
const unroundedHelper = `function cpu_unrounded_matrix_mult(m, n) {
    var l = m.length === 16 ? 4 : m.length === 9 ? 3 : 2;
    var out = Array(m.length);
    for (var i = 0; i < l; i++) for (var j = 0; j < l; j++) {
      var sum = 0; for (var o = 0; o < l; o++) sum += m[l * o + i] * n[j * l + o]; out[j * l + i] = sum;
    }
    return out;
  }
  ${floatHelper}`

const mutants = [
  compileMutant('right-associated-chain', [[matrixLine, 'var A = matrixMult(T, matrixMult(Q, S));']], ['scanlines-max-seed-one', 'scanlines-mid-seed-thirty-seven']),
  compileMutant('missing-intermediate-f32-stores', [[floatHelper, unroundedHelper], [matrixLine, 'var A = cpu_unrounded_matrix_mult(cpu_unrounded_matrix_mult(T, Q), S);']], ['scanlines-mid-seed-thirty-seven', 'aspect-negative-lens-vignette']),
  compileMutant('reverse-inner-operands', [[matrixLine, 'var A = matrixMult(matrixMult(Q, T), S);']], ['scanlines-max-seed-one']),
  compileMutant('swap-basis-matrices', [[matrixLine, 'var A = matrixMult(matrixMult(S, Q), T);']], ['scanlines-max-seed-one']),
  compileMutant('omit-basis-products', [[matrixLine, 'var A = Q;']], ['scanlines-max-seed-one']),
]

function makeInput(definition) {
  return patternedSurface(definition.width, definition.height, definition.phase)
}

function render(factory, definition) {
  const input = makeInput(definition)
  const before = new Uint32Array(input.data.buffer, input.data.byteOffset, input.data.length).slice()
  const uniforms = {
    aspectLens: definition.aspectLens,
    xChonk: definition.xChonk,
    yChonk: definition.yChonk,
    glitchiness: f(definition.glitchiness),
    scanlinesAmt: definition.scanlinesAmt,
    snowAmt: f(definition.snowAmt),
    vignetteAmt: f(definition.vignetteAmt),
    aberration: f(definition.aberration),
    distortion: f(definition.distortion),
    seed: definition.seed,
  }
  const tileOffset = definition.tileOffset ? new Float32Array(definition.tileOffset.map(f)) : undefined
  const fullResolution = definition.fullResolution ? new Float32Array(definition.fullResolution.map(f)) : undefined
  const bindings = createCanonicalBindings({
    width: definition.width,
    height: definition.height,
    time: definition.time,
    frame: 0,
    seed: 0,
    uniforms,
    textures: { inputTex: input },
    tileOffset,
    fullResolution,
  })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel: bindGlslKernel(factory, bindings), destination: output })
  const after = new Uint32Array(input.data.buffer, input.data.byteOffset, input.data.length)
  if (before.some((word, index) => word !== after[index])) throw new Error(`${definition.name}: render mutated input surface`)
  if (output.data.some((value) => !Number.isFinite(value))) throw new Error(`${definition.name}: render produced a non-finite lane`)
  return { output, input_f32_sha256: sha256(bytes(input.data)), input_immutable: true }
}

const rendered = new Map()
const renderCases = cases.map((definition) => {
  const canonical = render(canonicalFactory, definition)
  const repeat = render(canonicalFactory, definition)
  const publicResult = render(publicFactory, definition)
  const repeated = compareSurfaces(canonical.output, repeat.output)
  const publicComparison = compareSurfaces(canonical.output, publicResult.output)
  if (!repeated.float32.exact_f32_bits || !repeated.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: canonical repeat drift`)
  if (!publicComparison.float32.exact_f32_bits || !publicComparison.rgba8.exact_rgba8_bytes) throw new Error(`${definition.name}: public/canonical drift`)
  rendered.set(definition.name, canonical.output)
  return {
    ...definition,
    effective_tile_offset: definition.tileOffset ?? [0, 0],
    effective_full_resolution: definition.fullResolution ?? [definition.width, definition.height],
    input_f32_sha256: canonical.input_f32_sha256,
    input_immutable: canonical.input_immutable,
    output_f32_bits_le: Array.from(new Uint32Array(canonical.output.data.buffer), u32Hex),
    output_rgba8: Array.from(canonical.output.toRgba8()),
    output_f32_sha256: sha256(bytes(canonical.output.data)),
    output_rgba8_sha256: sha256(bytes(canonical.output.toRgba8())),
    repeated_run: repeated,
    public_catalog: publicComparison,
  }
})

const mutationResults = mutants.map((mutant) => {
  const comparisons = cases.map((definition) => {
    const candidate = render(mutant.factory, definition).output
    return { case: definition.name, ...compareSurfaces(rendered.get(definition.name), candidate) }
  })
  for (const witness of mutant.expected_witnesses) {
    const comparison = comparisons.find((item) => item.case === witness)
    if (!comparison || comparison.float32.exact_f32_bits) throw new Error(`${mutant.name}: required Float32 witness ${witness} did not diverge`)
  }
  const control = comparisons.find((item) => item.case === 'matrix-masked-control')
  if (!control?.float32.exact_f32_bits || !control?.rgba8.exact_rgba8_bytes) throw new Error(`${mutant.name}: matrix-masked control unexpectedly diverged`)
  return {
    name: mutant.name,
    factory_sha256: mutant.factory_sha256,
    anchors: mutant.anchors,
    expected_witnesses: mutant.expected_witnesses,
    divergent_f32_cases: comparisons.filter((item) => !item.float32.exact_f32_bits).map((item) => item.case),
    divergent_rgba8_cases: comparisons.filter((item) => !item.rgba8.exact_rgba8_bytes).map((item) => item.case),
    comparisons,
  }
})

const fixture = {
  schema: 1,
  program_key: programKey,
  corpus_revision: corpusRevision,
  upstream_revision: UPSTREAM_REVISION,
  oracle_authority: 'real unmodified noisemaker-for-cpu canonical factory and shipped GlslCpuRuntime',
  exactness_contract: {
    float32: 'raw little-endian uint32 lane equality; signed zero and NaN payloads are significant',
    rgba8: 'raw encoded byte equality',
    tolerance: 'none',
    diagnostic: 'custom comparer reports first top-down pixel/channel mismatch and both raw lane words',
  },
  source_census: sourceCensus,
  provenance: {
    cpu_root_argument: '<immutable-cpu-snapshot-root>',
    live_checkout_argument: '<live-noisemaker-for-cpu-checkout>',
    import_closure: actualImportClosure,
    files: Object.fromEntries(Object.entries(provenanceFiles).map(([name, [relativePath, expected_sha256]]) => [name, { relative_path_from_noisemaker_for_cpu: relativePath, sha256: expected_sha256 }])),
    glsl_source: { relative_path_from_noisemaker_for_cpp: path.relative(cppRoot, sourcePath), bytes: sourceBytes.length, sha256: sha256(sourceBytes) },
    canonical_factory: { name: canonicalFactory.name, bytes: Buffer.byteLength(canonicalFactory.toString()), sha256: sha256(canonicalFactory.toString()) },
    public_factory_is_canonical_identity: true,
    adapter_override_absent: true,
    moving_tree_observation: {
      first_upstream_snapshot_sha256: '8579de7f8d3ff35a71c35c2c5e32296d0f71ffef1e790db9736f99ab04969936',
      second_and_consumed_upstream_snapshot_sha256: 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090',
      relevant_artifacts_unchanged_across_observations: {
        canonical_kernels_sha256: provenanceFiles.canonical_kernels[1],
        public_catalog_sha256: provenanceFiles.public_catalog[1],
        glsl_runtime_sha256: provenanceFiles.glsl_runtime[1],
        glsl_kernel_sha256: provenanceFiles.glsl_kernel[1],
        pass_runner_sha256: provenanceFiles.pass_runner[1],
        surface_sha256: provenanceFiles.surface[1],
        canonical_factory_sha256: sha256(canonicalFactory.toString()),
        glsl_source_sha256: sha256(sourceBytes),
      },
      policy: 'the generator consumes and pins only the second snapshot; any later relevant-artifact change is a hard provenance failure',
    },
  },
  comparer_self_tests: comparerSelfTests(),
  frontend_proof: frontendProof,
  matrix_semantics: {
    target: 'column-major, left-associated (T*Q)*S; each matrix product element is F32(sum), matching shipped glsl-runtime.js',
    stale_hazard_rejected: 'plain Array / unrounded intermediate matrix products are not the current noisemaker-for-cpu behavior',
    direct_cases: directCases,
  },
  render_cases: renderCases,
  render_mutations: mutationResults,
}

function reportFor(value) {
  const caseRows = value.render_cases.map((item) => `| ${item.name} | ${item.width}x${item.height} | ${item.seed} | ${item.scanlinesAmt} | ${item.output_f32_sha256} | ${item.output_rgba8_sha256} |`).join('\n')
  const mutationRows = value.render_mutations.map((item) => `| ${item.name} | ${item.expected_witnesses.join(', ')} | ${item.divergent_f32_cases.join(', ')} | ${item.divergent_rgba8_cases.join(', ') || '(none; Float32 remains authoritative)'} |`).join('\n')
  const directRows = value.matrix_semantics.direct_cases.map((item) => `| ${item.name} | ${item.left_associated_f32_sha256} | ${item.right_associated_comparison.mismatched_lanes} | ${item.unrounded_intermediate_comparison.mismatched_lanes} |`).join('\n')
  return `# Glitch exact-parity oracle\n\nProgram \`${value.program_key}\`; corpus revision \`${value.corpus_revision}\`.\n\n## Result\n\nThe currently shipped JavaScript reference materializes every matrix-product element through \`F32(sum)\` into a pooled \`Float32Array\`. The exact target is column-major, left-associated \`(T*Q)*S\`, with a float32 store after \`T*Q\` and after the final product. The older plain-Array/no-intermediate-narrowing claim is stale and is actively rejected by this package.\n\nThe reachable matrix closure is exactly three \`mat4\` constructors, two nested \`mat4*mat4\` nodes, and one \`vec4*mat4\` node, all in the live \`bicubic\` function. The captured pre-admission frontier rejects the first \`mat4\` type before reaching constructor or binary dispatch; \`--live-frontier\` observes later progress separately.\n\n## Exact contract\n\n- Float output uses raw little-endian float32 lane words; there is no tolerance.\n- RGBA8 output uses exact encoded bytes and never substitutes for Float32 parity.\n- The custom comparer rejects equal-byte-length dimension mismatches, distinguishes +0 from -0, and reports the first top-down pixel/channel and both lane words.\n- Every render is repeated, compared through the public-catalog identity, checked finite, and proves input-surface immutability.\n\n## Direct matrix fixtures\n\n| Case | Left-associated SHA-256 | Right-association mismatched lanes | Unrounded-intermediate mismatched lanes |\n| --- | --- | ---: | ---: |\n${directRows}\n\nThese fixtures call the real shipped \`GlslCpuRuntime.stdlib.matrixMult\` and independently compare it with a literal \`F32(sum)\` implementation. Crafted fractional/dynamic-range matrices discriminate both association and the obsolete unrounded-intermediate model.\n\n## Render fixtures\n\n| Case | Size | Seed | Scanlines | Float32 SHA-256 | RGBA8 SHA-256 |\n| --- | --- | ---: | ---: | --- | --- |\n${caseRows}\n\nThe suite covers matrix-masked control, maximum and minimum nonzero scanline influence, seed/time extremes, both aspect-lens states, both distortion branches, both vignette branches, all three snow regions, and tiled full-resolution coordinates.\n\n## Render mutation discrimination\n\n| Mutation | Required witnesses | All Float32-divergent cases | All RGBA8-divergent cases |\n| --- | --- | --- | --- |\n${mutationRows}\n\nThe matrix-masked control must remain exact for every mutant. The active-scanline witnesses distinguish wrong association, missing intermediate float32 stores, reversed inner operands, swapped basis matrices, and omitted basis products. RGBA8 is recorded but Float32 bits are the binding contract.\n\n## Frontend fail-closed proof\n\n\`${path.basename(frontendProbePath)}\` authenticates the exact source/key/profile/hash, all matrix nodes and spans, nested left-association, constructor arities, symbol route, full call-graph reachability, and return route. Its negatives reject wrong key/profile/hash, coefficient drift, association drift, operand-order drift, extra matrix use, constructor arity drift, vector/matrix orientation drift, and bicubic return-route drift.\n\n## Provenance observation\n\nThe shared JS tree changed during package assembly: \`upstream-snapshot.js\` was first observed at \`${value.provenance.moving_tree_observation.first_upstream_snapshot_sha256}\` and then at the consumed/pinned \`${value.provenance.moving_tree_observation.second_and_consumed_upstream_snapshot_sha256}\`. The canonical kernels, public catalog, GLSL runtime/kernel, pass runner, Surface implementation, canonical Glitch factory, and pinned Glitch GLSL bytes remained identical across both observations. The final self-check is also run from a frozen sibling copy under \`/tmp\`; a later change in any relevant artifact is a hard failure.\n\n## Regeneration\n\nFrom the repository root:\n\n\`\`\`sh\npython3 docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --check\npython3 docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --live-frontier\nnode docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs\nnode docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check\n\`\`\`\n\nThe generator verifies pinned source/runtime/catalog/factory hashes before executing the real unmodified canonical factory. \`--check\` regenerates the JSON and report in memory and requires byte-for-byte identity.\n`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)
  .replaceAll('The final self-check is also run from a frozen sibling copy under `/tmp`; a later change in any relevant artifact is a hard failure.', 'The final self-check uses an external temporary fixture root represented by `<external-temp-root>`; a later change in any relevant artifact is a hard failure.')
  .replaceAll('python3 docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --check\npython3 docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --live-frontier\nnode docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs\nnode docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check', 'NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>\nPYTHONDONTWRITEBYTECODE=1 python3 -B docs/port-engineering/matrix/glitch-parity/glitch_matrix_frontend_probe.py --check\nPYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_glitch_native_oracle_include.py --check')
const check = mode === '--check'
if (check) {
  for (const [target, generated] of [[outputPath, jsonText], [reportPath, reportText]]) {
    if (!fs.existsSync(target)) throw new Error(`missing generated artifact: ${target}`)
    const committed = fs.readFileSync(target, 'utf8')
    if (committed !== generated) throw new Error(`generated artifact drift: ${target}`)
  }
  console.log(`Glitch oracle check passed: ${renderCases.length} renders, ${directCases.length} direct matrix cases, ${mutationResults.length} render mutations`)
} else if (mode === '--write') {
  fs.writeFileSync(outputPath, jsonText)
  fs.writeFileSync(reportPath, reportText)
  console.log(`wrote ${outputPath}`)
  console.log(`wrote ${reportPath}`)
}
