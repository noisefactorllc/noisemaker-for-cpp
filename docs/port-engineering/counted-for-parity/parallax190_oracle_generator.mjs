#!/usr/bin/env node
// Parallax canonical JavaScript oracle generator (`filter/parallax:parallax`,
// typed row 190 -- the counted-for ladder's first landing).
//
// Authority: the unmodified public canonical factory `canonicalFactory98`
// from an immutable snapshot of `noisemaker-for-cpu`, executed through the
// pinned `bindCanonicalKernel` / `runPass` path. No C++ output participates
// in any expected array. A locally reimplemented formula is not an oracle
// and is never used here.
//
// This package exists because row 190 shipped WITHOUT one, and was wrong.
// `DEFECTS-FOUND.md` item 6: the authority's `var prevUV = rayUV` binds a
// reference to one `PooledFloat32Array`, the march writes `rayUV` in place,
// so the refinement `mix(rayUV, prevUV, w)` is `mix(x, x, w) == x` -- a
// no-op. The emitter value-copied and performed the interpolation. The
// `refinement-copy-restored` mutant below reproduces exactly that emission,
// and its witness set is the regression guard: any future port that copies
// instead of aliasing reproduces the mutant, not the canonical.
//
// The case list is chosen against that defect specifically. `straddle` and
// `straddle-tile` are the discriminators -- their marches enter the
// refinement with a nonzero `w`. `full-basic` is deliberately kept even
// though it does NOT discriminate: the original defect was invisible at one
// plausible binding set, and the case list records that fact rather than
// hiding it.
//
//   node docs/port-engineering/counted-for-parity/parallax190_oracle_generator.mjs \
//     --write --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
//   node docs/port-engineering/counted-for-parity/parallax190_oracle_generator.mjs \
//     --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '..', '..', '..'))

const programKey = 'filter/parallax:parallax'
const factoryName = 'canonicalFactory98'
const nextFactoryName = 'canonicalFactory99'
const sourceRelative =
  'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/parallax/parallax.glsl'
const sourceSha256Expected =
  '5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642'

// The factory's own text, pinned. Any upstream edit to parallax invalidates
// every expected array below and must invalidate this generator first.
const factoryTextSha256 =
  '052b2b2cc1a086a57c458fd8ae49b6065391f19f55feaa0662e14f6614cde905'

// Cross-validation of the Function.prototype.toString pinning method: the
// same snapshot must reproduce cellRefract's frozen factory-text digest
// (cellrefract186 oracle) or the METHOD -- not the snapshot -- is
// untrustworthy and this generator refuses to run.
const crossValidationKey = 'classicNoisedeck/cellRefract:cellRefract'
const crossValidationFactorySha256 =
  '329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3'

const bindingNames = Object.freeze([
  'inputTex', 'heightMap', 'tileOffset', 'fullResolution', 'direction', 'pivot',
])
// Read off the emitted typed_80 binder. `tileOffset` and `fullResolution` are
// OPTIONS-level in createCanonicalBindings -- see the trap note below.
const bindingAbi = Object.freeze({
  inputTex: 'sampler2D', heightMap: 'sampler2D', tileOffset: 'vec2',
  fullResolution: 'vec2', direction: 'vec3', pivot: 'number',
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
function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytesOf(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function words(view) { return new Uint32Array(view.buffer, view.byteOffset, view.length) }
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }

// ---------------------------------------------------------------------------
// Arguments and snapshot confinement
// ---------------------------------------------------------------------------

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
  if (token !== modes[0]) throw new Error(`unexpected argument: ${token}`)
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
const liveCpuReal = validateRoot(liveArgument, 'NOISEMAKER_FOR_CPU')
let liveIdentity
try {
  liveIdentity = JSON.parse(fs.readFileSync(path.join(liveCpuReal, 'package.json'), 'utf8')).name
} catch {
  throw new Error('NOISEMAKER_FOR_CPU is not a noisemaker-cpu checkout')
}
if (liveIdentity !== 'noisemaker-cpu') throw new Error('NOISEMAKER_FOR_CPU is not a noisemaker-cpu checkout')
if (cpuRoot === liveCpuReal || beneath(cpuRoot, liveCpuReal) || beneath(liveCpuReal, cpuRoot)) {
  throw new Error('authority and live checkout must be distinct, non-overlapping roots')
}
if (beneath(cppRoot, cpuRoot) || beneath(cpuRoot, cppRoot)
    || beneath(cppRoot, liveCpuReal) || beneath(liveCpuReal, cppRoot)) {
  throw new Error('authority and live checkout must be external to the C++ repository')
}

// ---------------------------------------------------------------------------
// Provenance
// ---------------------------------------------------------------------------

for (const [name, [relative, expected]] of Object.entries(pinnedCpuFiles)) {
  const actual = sha256(fs.readFileSync(path.join(cpuRoot, relative)))
  if (actual !== expected) throw new Error(`${name} provenance drift: ${actual}`)
}

function confine(candidate, why) {
  let stat
  try { stat = fs.lstatSync(candidate) } catch { throw new Error(`${why} is missing: ${candidate}`) }
  if (stat.isSymbolicLink()) throw new Error(`${why} must not be a symlink: ${candidate}`)
  const real = fs.realpathSync(candidate)
  if (!beneath(cpuRoot, real)) throw new Error(`${why} escaped the snapshot: ${real}`)
  return real
}
const load = (relative) => import(pathToFileURL(confine(path.join(cpuRoot, relative), 'load')).href)
const { canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { bindCanonicalKernel } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')

const canonicalFactory = canonicalKernelFactories[programKey]
if (typeof canonicalFactory !== 'function') throw new Error(`${programKey}: no canonical factory`)
if (canonicalFactory.name !== factoryName) {
  throw new Error(`factory identity drift: ${canonicalFactory.name} != ${factoryName}`)
}
if (!kernelFactories.has(programKey)) {
  throw new Error(`${programKey}: absent from the public catalog -- adapter-only routing would change the authority`)
}

const canonicalText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalText) !== factoryTextSha256) {
  throw new Error(`factory text drift: ${sha256(canonicalText)}`)
}
const crossValidationText =
  Function.prototype.toString.call(canonicalKernelFactories[crossValidationKey])
if (sha256(crossValidationText) !== crossValidationFactorySha256) {
  throw new Error('toString pinning method failed cross-validation against cellRefract')
}
// The factory text must be the same bytes the file carries, so a factory
// rebuilt at import time cannot slip past the pin.
const canonicalKernelsSource = fs.readFileSync(path.join(cpuRoot, pinnedCpuFiles.canonical_kernels[0]), 'utf8')
const sliceStart = canonicalKernelsSource.indexOf(`function ${factoryName}`)
const sliceEnd = canonicalKernelsSource.indexOf(`function ${nextFactoryName}`, sliceStart)
if (sliceStart < 0 || sliceEnd < 0) throw new Error('factory slice not found in the pinned source')
if (!canonicalKernelsSource.slice(sliceStart, sliceEnd).startsWith(canonicalText)) {
  throw new Error('factory text is not a verbatim prefix of its slice in the pinned source')
}

const sourceBytes = fs.readFileSync(path.join(cppRoot, sourceRelative))
if (sha256(sourceBytes) !== sourceSha256Expected) {
  throw new Error(`corpus source drift: ${sha256(sourceBytes)}`)
}

// ---------------------------------------------------------------------------
// The alias fact this package exists to pin, asserted against the authority
// text rather than described in prose.
// ---------------------------------------------------------------------------

const aliasDeclaration = 'var prevUV = rayUV;'
const inPlaceMarchUpdate = '(rayUV[0] = uv[0] + shift[0] * (t - pivot), rayUV[1] = uv[1] + shift[1] * (t - pivot), rayUV);'
const refinementWrite = 'mix(rayUV, prevUV, w).reduce((res,el,i)=>(res[i] = el, res), rayUV);'
for (const [label, text] of [['alias declaration', aliasDeclaration],
                             ['in-place march update', inPlaceMarchUpdate],
                             ['refinement write', refinementWrite]]) {
  const count = canonicalText.split(text).length - 1
  if (count !== 1) throw new Error(`${label}: expected exactly one occurrence, found ${count}`)
}
// `prevUV` is never rebound after its declaration -- if it were, the alias
// would not track `rayUV` and the no-op argument would not hold.
if ((canonicalText.split('prevUV =').length - 1) !== 1) {
  throw new Error('prevUV is assigned more than once; the alias argument no longer holds')
}

// ---------------------------------------------------------------------------
// Exact comparison
// ---------------------------------------------------------------------------

function compareExact(actual, expected, label) {
  const actualWords = words(actual.data)
  const expectedWords = words(expected.data)
  if (actualWords.length !== expectedWords.length) {
    throw new Error(`${label}: lane count ${actualWords.length} != ${expectedWords.length}`)
  }
  const actualBytes = actual.toRgba8()
  const expectedBytes = expected.toRgba8()
  let changedLanes = 0
  let firstMismatch = null
  for (let index = 0; index < actualWords.length; ++index) {
    if (actualWords[index] !== expectedWords[index]) {
      ++changedLanes
      if (firstMismatch === null) {
        firstMismatch = { lane: index, expected: u32Hex(expectedWords[index]), actual: u32Hex(actualWords[index]) }
      }
    }
  }
  let changedBytes = 0
  for (let index = 0; index < actualBytes.length; ++index) {
    if (actualBytes[index] !== expectedBytes[index]) ++changedBytes
  }
  return {
    exact: changedLanes === 0 && changedBytes === 0,
    changed_lane_count: changedLanes,
    changed_rgba8_byte_count: changedBytes,
    first_float32_mismatch: firstMismatch,
  }
}

// The comparer must be shown to FAIL, or a green run proves nothing.
function comparerSelfTests() {
  const left = new Surface(2, 1)
  const right = new Surface(2, 1)
  const rows = []
  rows.push({ name: 'identical-is-exact', pass: compareExact(left, right, 'self').exact === true })
  right.data[0] = 1
  rows.push({ name: 'one-lane-differs-is-caught', pass: compareExact(left, right, 'self').changed_lane_count === 1 })
  right.data[0] = 0
  // A float32 difference too small to survive RGBA8 quantization must still
  // be caught on the word comparison -- the whole point of word parity.
  right.data[1] = 1e-9
  const subByte = compareExact(left, right, 'self')
  rows.push({ name: 'sub-quantization-difference-is-caught', pass: subByte.exact === false && subByte.changed_lane_count === 1 })
  rows.push({ name: 'sub-quantization-difference-moves-no-byte', pass: subByte.changed_rgba8_byte_count === 0 })
  const failed = rows.filter((row) => !row.pass)
  if (failed.length) throw new Error(`comparer self-test failed: ${failed.map((r) => r.name).join(', ')}`)
  return rows
}
const comparerSelfTestRows = comparerSelfTests()

// ---------------------------------------------------------------------------
// Inputs and cases
// ---------------------------------------------------------------------------

function makeSurface(width, height, tag) {
  const bytes = new Uint8Array(width * height * 4)
  for (let y = 0; y < height; ++y) {
    for (let x = 0; x < width; ++x) {
      const index = (y * width + x) * 4
      bytes[index] = (31 * x + 17 * y + 13 * tag) % 256
      bytes[index + 1] = (11 * x + 47 * y + 29 * tag) % 256
      bytes[index + 2] = (67 * x + 19 * y + 7 * tag) % 256
      bytes[index + 3] = 255
    }
  }
  return Surface.fromRgba8(width, height, bytes)
}

// THE TRAP, recorded where it can bite: `createCanonicalBindings` spreads
// `...uniforms` FIRST and then overwrites `resolution`, `fullResolution`,
// `tileOffset`, `aspectRatio`, `aspect`, `time`, `globalTime`, `deltaTime`
// and `frame` from the OPTIONS level. Passing tileOffset/fullResolution
// inside `uniforms` silently loses them and makes the JS render a full route
// against the port's tile route -- a large, entirely fake divergence. They go
// at the options level, and only `direction`/`pivot` are real uniforms here.
const cases = [
  {
    name: 'full-basic', width: 5, height: 4, inputTag: 1, heightTag: 7,
    inputWidth: 5, inputHeight: 4, heightWidth: 5, heightHeight: 4,
    tileOffset: [0, 0], fullResolution: [5, 4],
    direction: [0.6, -0.3, 0.75], pivot: 0.35,
    route: 'full',
    role: 'DOES NOT discriminate the refinement mutant -- kept deliberately, '
      + 'because the shipped defect was invisible at exactly this shape',
  },
  {
    name: 'straddle', width: 4, height: 5, inputTag: 3, heightTag: 5,
    inputWidth: 11, inputHeight: 9, heightWidth: 11, heightHeight: 9,
    tileOffset: [0, 0], fullResolution: [11, 9],
    direction: [-0.8, 0.4, 0.2], pivot: 0.0,
    route: 'full',
    role: 'the primary discriminator: every pixel enters the refinement with a nonzero w',
  },
  {
    name: 'straddle-tile', width: 4, height: 5, inputTag: 3, heightTag: 5,
    inputWidth: 11, inputHeight: 9, heightWidth: 11, heightHeight: 9,
    tileOffset: [3, 2], fullResolution: [11, 9],
    direction: [-0.8, 0.4, 0.2], pivot: 0.0,
    route: 'tile',
    role: 'the same march under a nonzero tileOffset -- pins the tile offset rule and the refinement together',
  },
  {
    name: 'zero-direction', width: 6, height: 3, inputTag: 2, heightTag: 9,
    inputWidth: 6, inputHeight: 3, heightWidth: 6, heightHeight: 3,
    tileOffset: [0, 0], fullResolution: [6, 3],
    direction: [0, 0, 0], pivot: 0.5,
    route: 'full',
    role: 'the length(direction) == 0 fallback arm: v becomes vec3(0,0,1), shift is zero, the march is a fixed point',
  },
  {
    name: 'tile-clamped', width: 4, height: 4, inputTag: 4, heightTag: 6,
    inputWidth: 9, inputHeight: 9, heightWidth: 9, heightHeight: 9,
    tileOffset: [2, 1], fullResolution: [4096, 4096],
    direction: [0.9, 0.9, 0.05], pivot: 0.25,
    route: 'tile',
    role: 'the ONLY case that reaches the dispPixels > maxDispPixels clamp arm',
  },
  {
    name: 'mismatched-maps', width: 6, height: 4, inputTag: 11, heightTag: 13,
    inputWidth: 6, inputHeight: 4, heightWidth: 3, heightHeight: 7,
    tileOffset: [0, 0], fullResolution: [6, 4],
    direction: [0.5, 0.5, 0.5], pivot: 0.6,
    route: 'full',
    role: 'heightMap and inputTex at different sizes -- pins the two independent textureSize divisors apart',
  },
]

function surfacesFor(definition) {
  return {
    inputTex: makeSurface(definition.inputWidth, definition.inputHeight, definition.inputTag),
    heightMap: makeSurface(definition.heightWidth, definition.heightHeight, definition.heightTag),
  }
}

function optionsFor(definition, textures) {
  return {
    width: definition.width,
    height: definition.height,
    time: 0,
    seed: 1,
    tileOffset: new Float32Array([f(definition.tileOffset[0]), f(definition.tileOffset[1])]),
    fullResolution: new Float32Array([f(definition.fullResolution[0]), f(definition.fullResolution[1])]),
    uniforms: {
      direction: new Float32Array(definition.direction.map(f)),
      pivot: f(definition.pivot),
    },
    textures,
  }
}

function render(factory, definition) {
  const textures = surfacesFor(definition)
  const before = {
    inputTex: words(textures.inputTex.data).slice(),
    heightMap: words(textures.heightMap.data).slice(),
  }
  const output = new Surface(definition.width, definition.height)
  runPass({
    kernel: bindCanonicalKernel(factory, optionsFor(definition, textures)),
    destination: output,
    time: 0,
    seed: 1,
  })
  for (const name of ['inputTex', 'heightMap']) {
    const after = words(textures[name].data)
    if (before[name].some((word, index) => word !== after[index])) {
      throw new Error(`${definition.name}: the ${name} surface was mutated by the render`)
    }
  }
  return { output, textures }
}

function surfaceRecord(surface) {
  const rawWords = words(surface.data)
  const rgba8 = surface.toRgba8()
  const finite = surface.data.filter(Number.isFinite).length
  if (finite !== surface.data.length) throw new Error('non-finite output lane')
  const alphaWords = new Set()
  for (let index = 3; index < rawWords.length; index += 4) alphaWords.add(u32Hex(rawWords[index]))
  if (alphaWords.size !== 1 || !alphaWords.has('0x3f800000')) {
    throw new Error(`alpha float words are not uniformly 0x3f800000: ${[...alphaWords].join(',')}`)
  }
  return {
    width: surface.width,
    height: surface.height,
    f32_words_le: Array.from(rawWords, u32Hex),
    f32_sha256: sha256(bytesOf(surface.data)),
    rgba8_bytes: Array.from(rgba8),
    rgba8_sha256: sha256(bytesOf(rgba8)),
    finite_lane_count: finite,
    alpha_f32_word: '0x3f800000',
    alpha_rgba8_byte: 255,
  }
}

function inputRecord(surface) {
  return {
    width: surface.width,
    height: surface.height,
    row_order: 'top-down storage; the GLSL texture origin is bottom-left and texture() flips',
    f32_words_le: Array.from(words(surface.data), u32Hex),
    f32_sha256: sha256(bytesOf(surface.data)),
  }
}

const canonicalExpected = new Map()
const renderCases = cases.map((definition) => {
  const { output, textures } = render(canonicalFactory, definition)
  canonicalExpected.set(definition.name, output)
  return {
    name: definition.name,
    route: definition.route,
    role: definition.role,
    width: definition.width,
    height: definition.height,
    bindings: {
      tileOffset: definition.tileOffset.map((value) => u32Hex(words(new Float32Array([f(value)]))[0])),
      fullResolution: definition.fullResolution.map((value) => u32Hex(words(new Float32Array([f(value)]))[0])),
      direction: definition.direction.map((value) => u32Hex(words(new Float32Array([f(value)]))[0])),
      pivot: u32Hex(words(new Float32Array([f(definition.pivot)]))[0]),
    },
    input: inputRecord(textures.inputTex),
    height_map: inputRecord(textures.heightMap),
    expected: surfaceRecord(output),
  }
})

// ---------------------------------------------------------------------------
// Mutation ledger
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

function measureAcrossCases(factory, label) {
  return cases.map((definition) => {
    const { output } = render(factory, definition)
    const comparison = compareExact(output, canonicalExpected.get(definition.name), `${label}/${definition.name}`)
    return {
      case: definition.name,
      differs: !comparison.exact,
      changed_lane_count: comparison.changed_lane_count,
      changed_rgba8_byte_count: comparison.changed_rgba8_byte_count,
      f32_sha256: sha256(bytesOf(output.data)),
      first_mismatch: comparison.first_float32_mismatch,
    }
  })
}

const mutantSpecs = [
  {
    name: 'refinement-copy-restored',
    target: '`var prevUV = rayUV;` becomes `var prevUV = $runtime.copy(rayUV);`',
    contract: 'THE defect this package exists for (DEFECTS-FOUND item 6). Copying instead of '
      + 'aliasing makes the straddle refinement `mix(rayUV, prevUV, w)` a real interpolation '
      + 'instead of the authority\'s no-op. This mutant IS the emission the port shipped at '
      + 'row 190; a port that reproduces it fails here.',
    anchor: aliasDeclaration,
    replacement: 'var prevUV = $runtime.copy(rayUV);',
    reaching: 'only cases whose march straddles and refines with a nonzero w',
  },
  {
    name: 'refinement-weight-negated',
    target: '`var w = f / (f - prevF);` becomes `var w = -f / (f - prevF);`',
    contract: 'the refinement weight itself. Under the authority\'s aliasing this is '
      + 'MULTIPLIED INTO A ZERO DELTA and cannot move a lane -- it is budgeted as a measured '
      + 'INVARIANT, not as a discriminator, and its all-identical row below is the evidence '
      + 'that the refinement really is inert.',
    anchor: 'var w = f / (f - prevF);',
    replacement: 'var w = -f / (f - prevF);',
    reaching: 'nothing: dead under the alias',
    invariant: true,
  },
  {
    name: 'march-steps-halved',
    target: 'the march bound `MARCH_STEPS` 32 becomes 16 at the loop and the step size',
    contract: 'the counted-for seed contract (frontend/loop_proof.py\'s '
      + '`filter/parallax:parallax` entry, MARCH_STEPS = 32). A port that admitted the wrong '
      + 'literal bound renders this mutant.',
    anchors: [['var stepSize = 1 / (MARCH_STEPS);', 'var stepSize = 1 / (16);'],
              ['i <= MARCH_STEPS;', 'i <= 16;']],
    reaching: 'every case whose march runs past 16 steps',
  },
  {
    name: 'shift-scale-halved',
    target: '`SHIFT_SCALE` 0.15 becomes 0.075 at the single shift site',
    contract: 'the other source-global const literal. Independent of the march bound, so a '
      + 'port that confused the two globals fails exactly one of these two mutants.',
    anchor: 'var shift = new $runtime.PooledFloat32Array([v[0] * SHIFT_SCALE, v[1] * SHIFT_SCALE]);',
    replacement: 'var shift = new $runtime.PooledFloat32Array([v[0] * 0.075, v[1] * 0.075]);',
    reaching: 'every case with a nonzero direction',
  },
  {
    name: 'luminosity-weights-swapped',
    target: 'the getLuminosity dot weights `vec3(0.299, 0.587, 0.114)` become r/b swapped',
    contract: 'the height-map read path -- `getHeight` is the only consumer, so this pins '
      + 'that the port samples the HEIGHT map (not the input) for the march.',
    anchor: 'return dot(color, new $runtime.PooledFloat32Array([0.29899999499320984, 0.5870000123977661, 0.11400000005960464]));',
    replacement: 'return dot(color, new $runtime.PooledFloat32Array([0.11400000005960464, 0.5870000123977661, 0.29899999499320984]));',
    reaching: 'every case whose march samples a non-uniform height map',
  },
  {
    name: 'textureLod-becomes-texelFetch-origin',
    target: 'the getInput sample coordinate loses its tileOffset subtraction',
    contract: 'the tile offset rule inside getInput. The tile cases discriminate; the full '
      + 'cases are algebraic controls (tileOffset is the zero vector there).',
    anchor: 'var localUV = new $runtime.PooledFloat32Array([(uv[0] * fullResolution[0] - tileOffset[0]) / texSize[0], (uv[1] * fullResolution[1] - tileOffset[1]) / texSize[1]]);\n  	return textureLod(inputTex, localUV, 0);',
    replacement: 'var localUV = new $runtime.PooledFloat32Array([(uv[0] * fullResolution[0]) / texSize[0], (uv[1] * fullResolution[1]) / texSize[1]]);\n  	return textureLod(inputTex, localUV, 0);',
    reaching: 'the tile cases only',
  },
]

const mutationLedger = mutantSpecs.map((spec) => {
  const compiled = compileMutant(spec)
  const rows = measureAcrossCases(compiled.factory, spec.name)
  const discriminating = rows.filter((row) => row.differs)
  if (spec.invariant) {
    if (discriminating.length !== 0) {
      throw new Error(`${spec.name}: budgeted INVARIANT but ${discriminating.length} case(s) differ`)
    }
  } else if (discriminating.length === 0) {
    throw new Error(`${spec.name}: no case discriminates this mutant`)
  }
  return {
    name: spec.name,
    target: spec.target,
    contract: spec.contract,
    reaching: spec.reaching,
    budgeted_as: spec.invariant ? 'measured invariant' : 'discriminator',
    anchor_count: compiled.anchors.length,
    anchor_sha256: compiled.anchors.map(([anchor]) => sha256(anchor)),
    replacement_sha256: compiled.anchors.map(([, replacement]) => sha256(replacement)),
    mutated_factory_sha256: sha256(compiled.mutatedText),
    discriminating_cases: discriminating.map((row) => row.case),
    rows,
  }
})

// The regression guard, asserted rather than hoped for: the defect mutant has
// to be discriminated by at least one case, and `full-basic` must NOT be one
// of them -- that asymmetry is the whole lesson of DEFECTS-FOUND item 6.
const defectLedger = mutationLedger.find((entry) => entry.name === 'refinement-copy-restored')
if (defectLedger.discriminating_cases.length === 0) {
  throw new Error('the refinement mutant is not discriminated by any case; this package would not guard the defect')
}
if (defectLedger.discriminating_cases.includes('full-basic')) {
  throw new Error('full-basic now discriminates the refinement mutant; the case-list note is stale and must be re-derived')
}

// ---------------------------------------------------------------------------
// Controls
// ---------------------------------------------------------------------------

const controls = []
{
  // An unbound heightMap is not a legal binding for this program, but an
  // EXTREME external time/seed must be inert: parallax reads neither.
  const externalRows = cases.map((definition) => {
    const textures = surfacesFor(definition)
    const output = new Surface(definition.width, definition.height)
    runPass({
      kernel: bindCanonicalKernel(canonicalFactory, optionsFor(definition, textures)),
      destination: output,
      time: 1234.5,
      seed: 987654,
    })
    return { case: definition.name, ...compareExact(output, canonicalExpected.get(definition.name), 'external') }
  })
  if (externalRows.some((row) => !row.exact)) {
    throw new Error('external time/seed is not inert for parallax')
  }
  controls.push({
    name: 'external-time-and-seed-extreme',
    result: 'identical',
    detail: 'parallax declares neither uniform; runPass time/seed cannot reach it',
    rows: externalRows,
  })
}

// ---------------------------------------------------------------------------
// Emit
// ---------------------------------------------------------------------------

const payload = {
  schema: 'parallax190-oracles-v1',
  program_key: programKey,
  corpus_revision: 'a024dc3a960cc44af454abc7aebce50456c194e6',
  source_sha256: sourceSha256Expected,
  authority: {
    cpu_root_argument: '<immutable-cpu-snapshot-root>',
    live_checkout_argument: '<live-noisemaker-for-cpu-checkout>',
  },
  factory: { name: factoryName, text_sha256: factoryTextSha256 },
  cross_validation: { key: crossValidationKey, factory_text_sha256: crossValidationFactorySha256 },
  authority_files: Object.fromEntries(
    Object.entries(pinnedCpuFiles).map(([name, [relative, digest]]) => [name, { path: relative, sha256: digest }])),
  binding_names: bindingNames,
  binding_abi: bindingAbi,
  alias_contract: {
    declaration: aliasDeclaration,
    in_place_update: inPlaceMarchUpdate,
    refinement_write: refinementWrite,
    consequence: 'prevUV and rayUV are one PooledFloat32Array; the refinement is mix(x, x, w) == x, a no-op',
  },
  comparer_self_tests: comparerSelfTestRows,
  cases: renderCases,
  mutation_ledger: mutationLedger,
  controls,
}

const jsonTarget = path.join(here, 'parallax190-oracles.json')
const reportTarget = path.join(here, 'parallax190-oracle-report.md')
const jsonText = `${JSON.stringify(payload, null, 1)}\n`

const discriminationTable = mutationLedger.map((entry) => {
  const marks = cases.map((definition) => {
    const row = entry.rows.find((item) => item.case === definition.name)
    return row.differs ? `${row.changed_lane_count}` : '.'
  })
  return `| \`${entry.name}\` | ${entry.budgeted_as} | ${marks.join(' | ')} |`
}).join('\n')

const reportText = `# parallax190 oracle report

Generated by \`parallax190_oracle_generator.mjs\` from an immutable snapshot
of \`noisemaker-for-cpu\`. Authority: \`${factoryName}\`, factory text
\`${factoryTextSha256}\`.

The authority argument is serialized only as \`<immutable-cpu-snapshot-root>\`; the
required live identity input is serialized only as
\`<live-noisemaker-for-cpu-checkout>\`. No host checkout path participates in
the generated document.

This package exists because typed row 190 shipped without one and was wrong.
See \`../DEFECTS-FOUND.md\` item 6 and \`parallax190-alias-divergence.md\`.

## The alias contract

\`\`\`
${aliasDeclaration}
${inPlaceMarchUpdate}
${refinementWrite}
\`\`\`

\`prevUV\` and \`rayUV\` are one \`PooledFloat32Array\`. The refinement is
therefore \`mix(x, x, w) == x\` -- a no-op in the authority. The generator
asserts each of those three lines occurs exactly once, and that \`prevUV\` is
never rebound.

## Cases

${renderCases.map((item) => `- **${item.name}** (${item.route}, ${item.width}x${item.height}) --- ${item.role}`).join('\n')}

## Mutation ledger --- changed float32 lanes per case

| mutant | budgeted as | ${cases.map((c) => c.name).join(' | ')} |
| --- | --- | ${cases.map(() => '---:').join(' | ')} |
${discriminationTable}

\`.\` means bit-identical to the canonical render.

**\`refinement-copy-restored\` is the regression guard.** It reproduces the
emission the port shipped at row 190. Note that \`full-basic\` does NOT
discriminate it: the defect was invisible at that shape, which is why the
case is kept rather than dropped. The generator fails if that ever stops
being true.

\`refinement-weight-negated\` is budgeted as a measured **invariant**, not a
discriminator: under the alias the weight multiplies a zero delta. Its
all-identical row is the positive evidence that the refinement is inert.

## Controls

${controls.map((item) => `- **${item.name}**: ${item.result} --- ${item.detail}`).join('\n')}

## Comparer self-tests

${comparerSelfTestRows.map((row) => `- ${row.name}: ${row.pass ? 'pass' : 'FAIL'}`).join('\n')}
`

function verifySidecar(target, payloadText) {
  const expected = sidecarText(target, payloadText)
  const actual = fs.readFileSync(sidecarPath(target), 'utf8')
  if (actual !== expected) throw new Error(`${path.basename(target)}: sidecar drift`)
}

if (write) {
  fs.writeFileSync(jsonTarget, jsonText)
  fs.writeFileSync(sidecarPath(jsonTarget), sidecarText(jsonTarget, jsonText))
  fs.writeFileSync(reportTarget, reportText)
  fs.writeFileSync(sidecarPath(reportTarget), sidecarText(reportTarget, reportText))
  const selfText = fs.readFileSync(fileURLToPath(import.meta.url))
  fs.writeFileSync(sidecarPath(fileURLToPath(import.meta.url)),
                   sidecarText(fileURLToPath(import.meta.url), selfText))
} else {
  const onDisk = fs.readFileSync(jsonTarget, 'utf8')
  if (onDisk !== jsonText) throw new Error('parallax190-oracles.json drift')
  const onDiskReport = fs.readFileSync(reportTarget, 'utf8')
  if (onDiskReport !== reportText) throw new Error('parallax190-oracle-report.md drift')
  verifySidecar(jsonTarget, jsonText)
  verifySidecar(reportTarget, reportText)
  verifySidecar(fileURLToPath(import.meta.url), fs.readFileSync(fileURLToPath(import.meta.url)))
}

const summary = mutationLedger
  .map((entry) => `${entry.name}:${entry.discriminating_cases.length}/${cases.length}`)
  .join(' ')
console.log(`Parallax190 oracle ${write ? 'written' : 'checked'}: ${cases.length} cases, `
  + `${mutationLedger.length} ledger mutants [${summary}], `
  + `${controls.length} control, alias contract asserted at 3 sites`)
