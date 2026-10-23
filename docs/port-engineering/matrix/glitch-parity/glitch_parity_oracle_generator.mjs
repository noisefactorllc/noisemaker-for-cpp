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
const programKey = 'classicNoisedeck/glitch:glitch'
// This package measures the current authenticated CPU and GLSL source.
const corpusRevision = '32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3'
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
  canonical_kernels: ['src/effects/generated/canonical-kernels.js', '2d2ad7a462d2f5e858d1ff339b0be48db097dbf3e7848bde08b90e7e3df1f869'],
  public_catalog: ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  upstream_snapshot: ['src/effects/generated/upstream-snapshot.js', 'de72cda3ef1b8789b91d284682577be67fd638a2747cae60bea7b72f74ca988f'],
  glsl_kernel: ['src/csl/glsl-kernel.js', 'f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff'],
  glsl_runtime: ['src/csl/glsl-runtime.js', '7f05e207246152aafa8b1777c230be86f266b398fcd535dc9c0e5f0b4f81fd30'],
  pass_runner: ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  surface: ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
}

const expectedImportClosure = {
  "src/csl/glsl-kernel.js": "f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff",
  "src/csl/glsl-runtime.js": "7f05e207246152aafa8b1777c230be86f266b398fcd535dc9c0e5f0b4f81fd30",
  "src/csl/metal-division.js": "104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8",
  "src/csl/metal-reciprocal-data.js": "08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87",
  "src/csl/metal-reciprocal-grid.js": "bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39",
  "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
  "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
  "src/effects/adapters/crt.js": "c37f70e15b6481b2f870761bf103529cd45cf6e5e714a0a6fd731dbe90c1c73f",
  "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
  "src/effects/adapters/fractal.js": "73bb60668d98a142edcd535c146527945af445baa694595da2a19fe0a649e804",
  "src/effects/adapters/index.js": "dd2ca7681884fbc3fa2687faeb52aced50076a5f0856736b63831e859073d22e",
  "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
  "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
  "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
  "src/effects/adapters/remap.js": "91fd829ba2ad68fabab4124f5464994fc267daa097af4f3dd5a7e20f075f9e79",
  "src/effects/adapters/snow.js": "9acaa9c8a612e3b58e5935646bc37540146a52cda6c947cc67d5443d468f041c",
  "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
  "src/effects/definition.js": "9ffd11c838b9b791a26f2ae0701c9a3f640acf1b40be486a93664e2f10af9f2e",
  "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
  "src/effects/generated/canonical-kernels.js": "2d2ad7a462d2f5e858d1ff339b0be48db097dbf3e7848bde08b90e7e3df1f869",
  "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
  "src/effects/generated/upstream-snapshot.js": "de72cda3ef1b8789b91d284682577be67fd638a2747cae60bea7b72f74ca988f",
  "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
  "src/runtime/automation.js": "7ec5b11a269eae6899a2e2d78a4687d87e82b0e623a8b150d0fa7d8feb09065f",
  "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
  "src/runtime/sampler.js": "5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5",
  "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
}
const actualImportClosure = importClosure()
if (JSON.stringify(actualImportClosure) !== JSON.stringify(Object.entries(expectedImportClosure).sort((left, right) => left[0].localeCompare(right[0])))) {
  throw new Error("Glitch authenticated CPU import closure drift")
}
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
if (sourceBytes.length !== 8268 || sha256(sourceBytes) !== '4bb633e963eed011c4724d9b18470baed3ac474eadce98e06288ace5c382846a') {
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
if (Buffer.byteLength(canonicalFactory.toString()) !== 13141 || sha256(canonicalFactory.toString()) !== 'bd51f73be90c40dc830dbca92b2e057939fb50bb9c2d1662ab068520d0c3eb6b') {
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

const currentFrontendProof = `
import dataclasses, hashlib, json, pathlib
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.glitch_mat4_chain_profile import PROFILE, authenticate_glitch_mat4_chain
key = 'classicNoisedeck/glitch:glitch'
path = pathlib.Path(${JSON.stringify(sourcePath)})
raw = path.read_text(encoding='utf-8')
digest = hashlib.sha256(raw.encode()).hexdigest()
candidate = analyze_program(parse_program(raw, key, gen._defaults(pathlib.Path.cwd(), key)), key)
proof = authenticate_glitch_mat4_chain(candidate, digest, PROFILE)
def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError('Glitch mutation anchor cardinality changed')
    return source.replace(old, new)
mutations = [
    ('constructor-coefficient-order', replace_once(raw, 'mat4(f11, f21, f11x, f21x,', 'mat4(f21, f11, f11x, f21x,')),
    ('right-associated-chain', replace_once(raw, 'mat4 A = T * Q * S;', 'mat4 A = T * (Q * S);')),
    ('reverse-inner-operands', replace_once(raw, 'mat4 A = T * Q * S;', 'mat4 A = Q * T * S;')),
    ('extra-matrix-declaration', replace_once(raw, 'mat4 A = T * Q * S;', 'mat4 B = T;\\n    mat4 A = B * Q * S;')),
    ('constructor-arity-drift', replace_once(raw, 'mat4 S = mat4(1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1., 1.);', 'mat4 S = mat4(1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1.);')),
    ('vector-matrix-orientation', replace_once(raw, 'return dot(tv * A, uv);', 'return dot(A * tv, uv);')),
    ('bicubic-return-route', replace_once(raw, 'return dot(tv * A, uv);', 'return dot(tv * A, tv);')),
]
negatives = [
    ('wrong-profile', candidate, digest, 'wrong-profile'),
    ('wrong-key', dataclasses.replace(candidate, key='foreign:glitch'), digest, PROFILE),
    ('wrong-caller-hash', candidate, '0' * 64, PROFILE),
]
for name, rejected_candidate, rejected_hash, rejected_profile in negatives:
    try:
        authenticate_glitch_mat4_chain(rejected_candidate, rejected_hash, rejected_profile)
    except ValueError:
        pass
    else:
        raise AssertionError('Glitch profile admitted ' + name)
for name, changed in mutations:
    try:
        changed_candidate = analyze_program(parse_program(changed, key, gen._defaults(pathlib.Path.cwd(), key)), key)
        authenticate_glitch_mat4_chain(changed_candidate, hashlib.sha256(changed.encode()).hexdigest(), PROFILE)
    except ValueError:
        pass
    else:
        raise AssertionError('Glitch frontend admitted ' + name)
assert len(negatives) + len(mutations) == 10
print(json.dumps({'source_sha256': digest, 'profile': PROFILE,
                  'construct_count': len(proof.constructors),
                  'matrix_product_count': len(proof.matrix_products),
                  'vector_product_count': len(proof.vector_products),
                  'negative_count': len(negatives) + len(mutations),
                  'negative_names': [name for name, *_ in negatives] + [name for name, _ in mutations]}))
`
const frontendProcess = spawnSync(process.env.NOISEMAKER_PYTHON ?? 'python3', ['-B', '-c', currentFrontendProof], {
  cwd: cppRoot,
  encoding: 'utf8',
  env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
})
if (frontendProcess.status !== 0) throw new Error(`frontend proof failed: ${frontendProcess.stderr || frontendProcess.stdout}`)
const frontendProof = JSON.parse(frontendProcess.stdout)
if (frontendProof.source_sha256 !== sha256(sourceBytes) || frontendProof.construct_count !== 3 || frontendProof.matrix_product_count !== 2 || frontendProof.vector_product_count !== 1 || frontendProof.negative_count !== 10 || frontendProof.negative_names?.length !== 10) {
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
  compileMutant('missing-intermediate-f32-stores', [[floatHelper, unroundedHelper], [matrixLine, 'var A = cpu_unrounded_matrix_mult(cpu_unrounded_matrix_mult(T, Q), S);']], ['scanlines-mid-seed-thirty-seven', 'snow-upper-midpoint']),
  compileMutant('reverse-inner-operands', [[matrixLine, 'var A = matrixMult(matrixMult(Q, T), S);']], ['scanlines-max-seed-one']),
  compileMutant('swap-basis-matrices', [[matrixLine, 'var A = matrixMult(matrixMult(S, Q), T);']], ['scanlines-max-seed-one']),
  compileMutant('omit-basis-products', [[matrixLine, 'var A = Q;']], ['scanlines-max-seed-one']),
]

function makeInput(definition) {
  return patternedSurface(definition.width, definition.height, definition.phase)
}

function render(factory, definition, rawBinary64Time = false) {
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
  const canonicalBindings = createCanonicalBindings({
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
  const bindings = rawBinary64Time
    ? Object.freeze({ ...canonicalBindings, time: definition.time })
    : canonicalBindings
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
const timeIngressCase = cases[2]
const timeCanonical = render(canonicalFactory, timeIngressCase).output
const timeRawBinary64 = render(canonicalFactory, timeIngressCase, true).output
const timeIngressLane = 4
const timeIngress = {
  case: timeIngressCase.name,
  lane: timeIngressLane,
  canonical_word: u32Hex(new Uint32Array(timeCanonical.data.buffer)[timeIngressLane]),
  raw_binary64_word: u32Hex(new Uint32Array(timeRawBinary64.data.buffer)[timeIngressLane]),
}
if (timeIngress.canonical_word === timeIngress.raw_binary64_word) {
  throw new Error('Glitch time-ingress case does not distinguish binary64 from Float32')
}

const mutationResults = mutants.map((mutant) => {
  const comparisons = cases.map((definition) => {
    const candidate = render(mutant.factory, definition).output
    return { case: definition.name, ...compareSurfaces(rendered.get(definition.name), candidate) }
  })
  for (const witness of mutant.expected_witnesses) {
    const comparison = comparisons.find((item) => item.case === witness)
    if (!comparison || comparison.float32.exact_f32_bits) throw new Error(`${mutant.name}: required Float32 witness ${witness} did not diverge; divergent cases: ${comparisons.filter((item) => !item.float32.exact_f32_bits).map((item) => item.case).join(', ')}`)
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
    consumed_cpu_revision: '4307ca9f26fc415e4fc5e75227d429d35cc741cd',
    authority_ledger: 'authenticated immutable CPU9f3 source closure',
  },
  comparer_self_tests: comparerSelfTests(),
  frontend_proof: frontendProof,
  matrix_semantics: {
    target: 'column-major, left-associated (T*Q)*S; each matrix product element is F32(sum), matching shipped glsl-runtime.js',
    stale_hazard_rejected: 'plain Array / unrounded intermediate matrix products are not the current noisemaker-for-cpu behavior',
    direct_cases: directCases,
  },
  render_cases: renderCases,
  time_ingress: timeIngress,
  render_mutations: mutationResults,
}

function reportFor(value) {
  const caseRows = value.render_cases.map((item) => `| ${item.name} | ${item.width}x${item.height} | ${item.seed} | ${item.scanlinesAmt} | ${item.output_f32_sha256} | ${item.output_rgba8_sha256} |`).join('\n')
  const mutationRows = value.render_mutations.map((item) => `| ${item.name} | ${item.expected_witnesses.join(', ')} | ${item.divergent_f32_cases.join(', ')} | ${item.divergent_rgba8_cases.join(', ') || '(none; Float32 remains authoritative)'} |`).join('\n')
  const directRows = value.matrix_semantics.direct_cases.map((item) => `| ${item.name} | ${item.left_associated_f32_sha256} | ${item.right_associated_comparison.mismatched_lanes} | ${item.unrounded_intermediate_comparison.mismatched_lanes} |`).join('\n')
  return `# Glitch exact-parity oracle\n\nProgram \`${value.program_key}\`; corpus revision \`${value.corpus_revision}\`.\n\n## Result\n\nThe currently shipped JavaScript reference materializes every matrix-product element through \`F32(sum)\` into a pooled \`Float32Array\`. The exact target is column-major, left-associated \`(T*Q)*S\`, with a float32 store after \`T*Q\` and after the final product. The older plain-Array/no-intermediate-narrowing claim is stale and is actively rejected by this package.\n\nThe reachable matrix closure is exactly three \`mat4\` constructors, two nested \`mat4*mat4\` nodes, and one \`vec4*mat4\` node, all in the live \`bicubic\` function. The current typed frontend authenticates the full bicubic chain and its return route against the exact a1a3 GLSL source. Wrong source hashes and profile carriers fail closed.\n\n## Exact contract\n\n- Float output uses raw little-endian float32 lane words; there is no tolerance.\n- RGBA8 output uses exact encoded bytes and never substitutes for Float32 parity.\n- The custom comparer rejects equal-byte-length dimension mismatches, distinguishes +0 from -0, and reports the first top-down pixel/channel and both lane words.\n- Every render is repeated, compared through the public-catalog identity, checked finite, and proves input-surface immutability.\n- Time ingress is checked at one fixed lane: canonical Float32 \`${value.time_ingress.canonical_word}\`, raw binary64 \`${value.time_ingress.raw_binary64_word}\`.\n\n## Direct matrix fixtures\n\n| Case | Left-associated SHA-256 | Right-association mismatched lanes | Unrounded-intermediate mismatched lanes |\n| --- | --- | ---: | ---: |\n${directRows}\n\nThese fixtures call the real shipped \`GlslCpuRuntime.stdlib.matrixMult\` and independently compare it with a literal \`F32(sum)\` implementation. Crafted fractional/dynamic-range matrices discriminate both association and the obsolete unrounded-intermediate model.\n\n## Render fixtures\n\n| Case | Size | Seed | Scanlines | Float32 SHA-256 | RGBA8 SHA-256 |\n| --- | --- | ---: | ---: | --- | --- |\n${caseRows}\n\nThe suite covers matrix-masked control, maximum and minimum nonzero scanline influence, seed/time extremes, both aspect-lens states, both distortion branches, both vignette branches, all three snow regions, and tiled full-resolution coordinates.\n\n## Render mutation discrimination\n\n| Mutation | Required witnesses | All Float32-divergent cases | All RGBA8-divergent cases |\n| --- | --- | --- | --- |\n${mutationRows}\n\nThe matrix-masked control must remain exact for every mutant. The active-scanline witnesses distinguish wrong association, missing intermediate float32 stores, reversed inner operands, swapped basis matrices, and omitted basis products. RGBA8 is recorded but Float32 bits are the binding contract.\n\n## Frontend fail-closed proof\n\n\`tools/glslcpp/frontend/glitch_mat4_chain_profile.py\` authenticates the exact current source/key/profile/hash, matrix nodes, nested left-association, symbol route, call-graph reachability, and bicubic return route. The oracle generator runs ten fail-closed negatives: wrong profile, key and caller hash, plus coefficient, association, operand-order, matrix-use, constructor-arity, vector-orientation and return-route mutations. Independent profile tests also check these paths.\n\n## Provenance observation\n\nThe oracle uses the immutable CPU revision \`${value.provenance.consumed_cpu_revision}\` and authenticates its import closure, pinned runtime and catalog files, canonical factory text, and the exact a1a3 Glitch GLSL source before rendering.\n\n## Regeneration\n\nFrom the repository root:\n\n\`\`\`sh\nNOISEMAKER_PYTHON=<python-3.14> NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node docs/port-engineering/matrix/glitch-parity/glitch_parity_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>\n<python-3.14> -B tools/glslcpp/generate_glitch_native_oracle_include.py --check\`\`\`\n\nThe generator verifies pinned source/runtime/catalog/factory hashes before executing the real unmodified canonical factory. \`--check\` regenerates the JSON and report in memory and requires byte-for-byte identity.\n`
}

const jsonText = `${JSON.stringify(fixture, null, 2)}\n`
const reportText = reportFor(fixture)
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
