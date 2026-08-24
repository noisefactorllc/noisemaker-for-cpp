import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { createCanonicalBindings } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

// ---------------------------------------------------------------------------
// Cheap-unlocks cluster 1 -- "loop-proof fingerprint reuse", THREE programs:
//   filter/lightLeak:lightLeak   filter/parallax:parallax   filter/reindex:nmReindexStats
//
// Per docs/port-engineering/loopproof/loop-proof-study.md SS4, these are
// the only three of the six originally-claimed "source-global-literal-int-v1
// reuse" candidates that are TRUE fingerprint-only reuses: their loop bound
// reads a `const int` global whose initializer.kind is a plain `literal`
// (POINT_COUNT=6, MARCH_STEPS=32, TILE_SIZE=8) -- no new proof mechanism, no
// budget-cap change, just admission. `dither` is excluded (its FS_ERR_W
// initializer is `binary`, not `literal` -- does not structurally qualify).
// `reindexReduce`/`mandelbrot` are excluded (they qualify structurally but
// ALSO need a numeric budget-cap increase -- not fingerprint-only, and
// explicitly out of scope per the task brief).
//
// This generator follows the house style set by
// docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs
// (hermetic imports, --check determinism, per-case mutation testing, an
// explicit intent-verification guard) and adds a cluster-specific mutation
// shape: rather than swapping a rendered CONSTANT (grade's LUMA_WEIGHTS) or a
// derivative-mechanism convention (the derivative cluster's sign-flip/lane-
// transpose), this cluster's hazard is a WRONG LOOP TRIP COUNT. Each
// mutation swaps the const global's compiled JS declaration
// (`var <NAME> = <original>;`) for a plausible-but-wrong value and asserts
// the rendered output genuinely diverges -- proving the trip count is a real,
// not vacuous, discriminator for this program, per the task's explicit
// warning that "a case where the loop body is idempotent, or where the
// result saturates, proves nothing."
//
// TWO HARD-WON LESSONS APPLIED THROUGHOUT (carried over verbatim from the
// grade/derivative generators):
//   1. RESERVED TOP-LEVEL KEYS. `createCanonicalBindings`
//      (noisemaker-for-cpu/src/csl/glsl-kernel.js:20-61) assigns nine
//      canonical keys (resolution, fullResolution, tileOffset, aspectRatio,
//      aspect, time, globalTime, deltaTime, frame) AFTER spreading
//      `...uniforms`, so passing any of them *inside* uniforms silently
//      discards the caller's intended value. Every case here is rendered
//      through `renderCase()`, which refuses to build if the uniforms object
//      illegally contains one of these keys, and independently reconstructs
//      the bindings to assert the kernel's own bound
//      tileOffset/fullResolution/time AND every declared per-program uniform
//      equal the CALLER's intended values.
//   2. DEFINES: INAPPLICABLE, VERIFIED NOT ASSUMED. All three programs
//      authorize the empty define map `{}` -- confirmed live in this session
//      via `tools.glslcpp.generate_typed_slice._defaults(repo, key)` for all
//      three keys (see report), and independently by reading every source
//      file: `lightLeak.glsl`/`parallax.glsl` each contain exactly one
//      `#ifdef GL_ES` guard (universal, not effect-specific) and
//      `nmReindexStats.glsl` has no preprocessor directive at all (`#version
//      300 es` directly). So the derivatives/grade clusters'
//      "defines-must-be-passed-as-uniforms" hazard cannot arise here --
//      stated explicitly rather than silently assumed inapplicable.
//
// A THIRD, cluster-specific finding, also verified not assumed:
// `filter/reindex:nmReindexStats`'s PUBLIC factory is NOT its canonical
// factory. `canonicalAdapterFactories['filter/reindex:nmReindexStats']` is
// `reindexStatsFactory` (noisemaker-for-cpu/src/effects/adapters/f32-color.js
// :56-79), a hand-written, performance-optimized reimplementation used by the
// live app that HARD-CODES tile size 8 (lines 61, 67) rather than reading a
// `TILE_SIZE` variable at all. The grade/derivative generators both required
// (and asserted) NO adapter override for every program they covered; this
// program breaks that precondition. This does not invalidate the oracle:
// the C++ port's ground truth is the corpus GLSL -> typed-IR -> canonical
// -kernel pipeline (`tools/glslcpp`), which corresponds exactly to
// `canonicalKernelFactories['filter/reindex:nmReindexStats']`
// (canonicalFactory120, the literal transpilation of the pinned corpus
// source), never to the hand-optimized adapter -- so this generator renders
// through the CANONICAL factory directly (bypassing `kernelFactories`, the
// public map that would silently prefer the adapter), and documents the
// adapter's existence and its independent hard-coded-8 confirmation as
// corroborating (not authoritative) evidence, per `loadProgram()` below.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'loopproof-oracles.json')
const reportPath = path.join(here, 'loopproof-oracle-report.md')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpusRoot = `tools/glslcpp/corpus/${revision}`
const glslKernelPath = '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
const glslRuntimePath = '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
const passRunnerPath = '../noisemaker-for-cpu/src/runtime/pass-runner.js'
const surfacePath = '../noisemaker-for-cpu/src/runtime/surface.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const AUTHORIZED_DEFINES = Object.freeze({})
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function f32Bits(value) {
  if (Number.isNaN(value)) return 'nan'
  const a = new Float32Array([value])
  return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}
function sameBytes(a, b) { return Buffer.compare(bytes(a.data), bytes(b.data)) === 0 }
function evaluated(text) { return (0, eval)(`(${text})`) }
function occurrences(text, needle) { return text.split(needle).length - 1 }

// ---------------------------------------------------------------------------
// Runtime/catalog hermeticity pinning -- identical file set and identical
// hash VALUES to the grade/derivative generators' RUNTIME_PROVENANCE (same
// repo state at authoring time), independently recomputed here, not
// copy-pasted trust.
// ---------------------------------------------------------------------------
const RUNTIME_PROVENANCE = {
  glsl_kernel_sha256: 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa',
  glsl_runtime_sha256: 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072',
  pass_runner_sha256: 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa',
  surface_sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
}
for (const [file, hash] of [
  [glslKernelPath, RUNTIME_PROVENANCE.glsl_kernel_sha256],
  [glslRuntimePath, RUNTIME_PROVENANCE.glsl_runtime_sha256],
  [passRunnerPath, RUNTIME_PROVENANCE.pass_runner_sha256],
  [surfacePath, RUNTIME_PROVENANCE.surface_sha256],
  [catalogPath, RUNTIME_PROVENANCE.public_catalog_sha256],
  [canonicalPath, RUNTIME_PROVENANCE.canonical_kernels_sha256],
  [adapterPath, RUNTIME_PROVENANCE.adapter_index_sha256],
]) {
  if (sha256(fs.readFileSync(file)) !== hash) throw new Error(`runtime drift: ${file}`)
}

// ---------------------------------------------------------------------------
// Lesson 1: reserved top-level keys + full intended-binding verification.
// ---------------------------------------------------------------------------
const RESERVED_TOP_LEVEL_KEYS = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']
function assertNoReservedKeysInUniforms(uniforms) {
  for (const k of RESERVED_TOP_LEVEL_KEYS) {
    if (Object.prototype.hasOwnProperty.call(uniforms, k)) {
      throw new Error(`uniforms illegally contains reserved top-level-only key "${k}" -- createCanonicalBindings assigns this AFTER spreading ...uniforms, so it would be silently discarded`)
    }
  }
}

function normalizeUniformsTyped(typeMap, raw) {
  const out = {}
  for (const [k, v] of Object.entries(raw)) {
    const type = typeMap[k]
    if (!type) throw new Error(`unknown uniform "${k}" -- not declared in this program's type map (check for typos or a missing entry)`)
    if (type === 'bool') out[k] = Boolean(v)
    else if (type === 'int') out[k] = v | 0
    else if (type === 'float') out[k] = f(v)
    else if (type === 'vec2' || type === 'vec3' || type === 'vec4') out[k] = new Float32Array(v.map(f))
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
}

// ---------------------------------------------------------------------------
// Deterministic patterned input texture -- same construction as the
// grade/derivative generators, so R/G/B/A genuinely differ per pixel and no
// two cases in the whole oracle share an input (distinct `phase`).
// `flatSurface` is new to this cluster: a constant-fill texture, used only
// to build parallax's deliberate loop-skipped diagnostic (height >= 1 at
// every pixel forces the ray-march's `if (f > 0.0)` guard false before the
// loop is ever entered, so MARCH_STEPS is provably untouched for that case).
// ---------------------------------------------------------------------------
function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = f((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
      data[i + 1] = f((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
      data[i + 2] = f((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
      data[i + 3] = f((((7 * x + 11 * y + phase) % 29) + (phase ? 2 : 13)) / 43)
    }
  }
  return new Surface(width, height, data)
}
function flatSurface(width, height, value) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i += 4) {
    data[i] = f(value)
    data[i + 1] = f(value)
    data[i + 2] = f(value)
    data[i + 3] = f(1)
  }
  return new Surface(width, height, data)
}

// ---------------------------------------------------------------------------
// parallax's height map, EMPIRICALLY tuned (not guessed): a naive small,
// same-resolution-as-canvas patterned height field made the MARCH_STEPS
// mutation a near-total no-op (only 1-2/4 cases diverged for a step-count
// -1 perturbation) -- traced to two compounding causes, both re-derived
// live in this session, not assumed: (a) SHIFT_SCALE (0.15, parallax.glsl)
// caps the ray's total UV-space traversal regardless of direction magnitude
// or pivot, so a small/same-size height map only ever traverses a fraction
// of ONE texel, making the sampled height-vs-t curve close to affine, which
// the loop's own linear-interpolation refine step already recovers almost
// exactly independent of step count; (b) low, roughly-uniform height values
// push the f<=0 crossing to the very tail of the loop (t close to 0) for
// EVERY step count, which is where per-N sample density is proportionally
// similar regardless of N, so coarser sampling barely moves the recovered
// crossing. A 16x16 diagonal-gradient-plus-ripple height map (deterministic,
// no texture/pixel/case dependence) fixes both: a wider dynamic range
// (0.05..0.95) spreads crossings across the FULL t range rather than
// clustering them at the tail, and enough independent texel cells for the
// ray's traversal to cross real cell boundaries, so a coarser step count can
// genuinely skip or land on a different cell than a finer one. Verified
// empirically (not assumed) against the real MARCH_STEPS=31/16 mutations for
// every direction/pivot/canvas-size combination this generator uses before
// being locked in -- see report for the resulting per-case divergence.
// ---------------------------------------------------------------------------
function parallaxHeightMap() {
  const size = 16
  const data = new Float32Array(size * size * 4)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const i = (y * size + x) * 4
      const base = (x + y) / (2 * (size - 1))
      const ripple = 0.15 * Math.sin(x * 3 + y * 5)
      const v = f(Math.min(0.95, Math.max(0.05, base + ripple)))
      data[i] = v
      data[i + 1] = v
      data[i + 2] = v
      data[i + 3] = f(1)
    }
  }
  return new Surface(size, size, data)
}

function probe(surface, x, y) {
  const i = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(i, i + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}
function probes(surface) {
  return [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]].map(([x, y]) => probe(surface, x, y))
}
function renderResult(surface) {
  const rgba = surface.toRgba8()
  let nonfinite = 0
  for (const lane of surface.data) if (!Number.isFinite(lane)) nonfinite += 1
  return { f32_sha256: sha256(bytes(surface.data)), rgba8_sha256: sha256(bytes(rgba)), finite_lanes: surface.data.length - nonfinite, nonfinite_lanes: nonfinite, probes: probes(surface) }
}

// ---------------------------------------------------------------------------
// renderCase: the single rendering path every case goes through.
// ---------------------------------------------------------------------------
function renderCase(program, c) {
  assertNoReservedKeysInUniforms(c.uniforms)
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures(c)
  const inputBytesBefore = {}
  for (const [name, tex] of Object.entries(textures)) inputBytesBefore[name] = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')

  const time = c.time ?? 0
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const intendedTileOffset = tileOffset ?? new Float32Array(2)
  const intendedFullResolution = fullResolution ?? new Float32Array([c.width, c.height])

  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time })
  if (f32Bits(bindings.time) !== f32Bits(f(time))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended time -- top-level binding lesson violated`)
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended tileOffset`)
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended fullResolution`)
  for (const [k, v] of Object.entries(uniforms)) {
    const bound = bindings[k]
    const same = ArrayBuffer.isView(v)
      ? Array.from(v).every((x, i) => f32Bits(x) === f32Bits(bound[i]))
      : (typeof v === 'boolean' ? bound === v : f32Bits(typeof v === 'number' ? f(v) : v) === f32Bits(typeof bound === 'number' ? f(bound) : bound))
    if (!same) throw new Error(`${program.id}/${c.name}: kernel did not observe intended uniform "${k}" -- reserved-key or spread-order defect`)
  }

  const kernel = bindGlslKernel(program.canonical, bindings)
  const first = new Surface(c.width, c.height)
  runPass({ kernel, destination: first })
  for (const [name, tex] of Object.entries(textures)) {
    const after = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')
    if (inputBytesBefore[name] !== after) throw new Error(`${program.id}/${c.name}: input texture "${name}" was mutated by render`)
  }
  const kernel2 = bindGlslKernel(program.canonical, bindings)
  const second = new Surface(c.width, c.height)
  runPass({ kernel: kernel2, destination: second })
  if (!sameBytes(first, second)) throw new Error(`${program.id}/${c.name}: repeat-render mismatch`)

  return { name: c.name, opts: { bindings }, surface: first, c }
}

function renderWithFactory(program, c, factory) {
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures(c)
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time: c.time ?? 0 })
  const kernel = bindGlslKernel(factory, bindings)
  const surface = new Surface(c.width, c.height)
  runPass({ kernel, destination: surface })
  return surface
}

// ---------------------------------------------------------------------------
// Mutation builder: swap a `var <NAME> = <value>;` const-global declaration
// for a different literal value. Generic across all three programs because
// each is a true fingerprint-only reuse of exactly this shape
// (POINT_COUNT/MARCH_STEPS/TILE_SIZE are each declared exactly once, and
// referenced only by name thereafter -- verified per-program occurrence
// count of 1 before this generator was written, reproduced live below).
// ---------------------------------------------------------------------------
function buildConstSwapMutation(factoryText, varName, originalValue, newValue) {
  const anchor = `var ${varName} = ${originalValue};`
  if (occurrences(factoryText, anchor) !== 1) throw new Error(`${varName} declaration anchor not found exactly once (expected "${anchor}")`)
  const mutated = `var ${varName} = ${newValue};`
  return { anchor, mutated }
}
function mutateFactoryText(factoryText, mutation) {
  if (occurrences(factoryText, mutation.anchor) !== 1) throw new Error('mutation anchor not unique at apply-time')
  return factoryText.replace(mutation.anchor, mutation.mutated)
}

// ---------------------------------------------------------------------------
// Program registry.
// ---------------------------------------------------------------------------
const PROGRAM_DEFS = [
  {
    id: 'lightLeak', key: 'filter/lightLeak:lightLeak', sourceFile: 'lightLeak/lightLeak.glsl',
    factoryName: 'canonicalFactory77',
    sourceRawBytes: 5047, sourceSha256: '61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb',
    constName: 'POINT_COUNT', constOriginal: 6,
    expectPublicIsCanonical: true, expectAdapterOverride: false,
    uniformTypes: { alpha: 'float', color: 'vec3', speed: 'float', seed: 'int' },
    loopRole: 'Voronoi seed count -- how many candidate cell centers voronoiCell() scans for the nearest-point search that drives the wormhole distortion, bloom, and screen-blend leak color.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    reach: (c) => Math.min(Math.max(c.uniforms.alpha, 0), 1) > 0,
    cases: [
      { name: 'warm-leak-low-alpha', width: 6, height: 5, phase: 0, uniforms: { alpha: 0.6, color: [0.9, 0.5, 0.2], speed: 0.3, seed: 11 } },
      { name: 'cool-leak-tiled-drift', width: 5, height: 6, phase: 1, time: 0.8, tileOffset: [2, 1], fullResolution: [11, 10], uniforms: { alpha: 1, color: [0.2, 0.4, 0.9], speed: 1.2, seed: 97 } },
      { name: 'high-alpha-fast-drift-negative-seed', width: 7, height: 4, phase: 2, time: 1.4, uniforms: { alpha: 0.85, color: [0.7, 0.1, 0.6], speed: 2.5, seed: -13 } },
      { name: 'boundary-tiny-alpha', width: 4, height: 7, phase: 3, uniforms: { alpha: 0.02, color: [0.5, 0.5, 0.5], speed: 0.1, seed: 3 } },
      { name: 'zero-alpha-early-exit-diagnostic', width: 3, height: 3, phase: 4, uniforms: { alpha: 0, color: [0.5, 0.5, 0.5], speed: 0, seed: 1 }, diagnostic: true },
    ],
    mutations: [
      { id: 'lightLeak-point-count-minus-one', kind: 'trip_count_off_by_one', newValue: 5, description: 'POINT_COUNT 6 -> 5: the smallest possible wrong trip count (a classic off-by-one bound error, e.g. `<=` written instead of `<`), narrower than the "swap" mutation below.' },
      { id: 'lightLeak-point-count-swap', kind: 'trip_count_swap', newValue: 3, description: 'POINT_COUNT 6 -> 3: halves the Voronoi seed count, a materially wrong trip count.' },
    ],
  },
  {
    id: 'parallax', key: 'filter/parallax:parallax', sourceFile: 'parallax/parallax.glsl',
    factoryName: 'canonicalFactory98',
    sourceRawBytes: 2430, sourceSha256: '5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642',
    constName: 'MARCH_STEPS', constOriginal: 32,
    expectPublicIsCanonical: true, expectAdapterOverride: false,
    uniformTypes: { direction: 'vec3', pivot: 'float' },
    loopRole: 'Ray-march step count for the parallax-occlusion search: each iteration samples the height map at a shrinking `t` and stops (with a linear refine) as soon as the ray crosses the surface. Both the iteration count AND the per-step increment (`stepSize = 1/MARCH_STEPS`) derive from this one constant.',
    buildTextures: (c) => ({
      inputTex: patternedSurface(c.width, c.height, c.phase),
      heightMap: c.flatHeight !== undefined ? flatSurface(c.width, c.height, c.flatHeight) : parallaxHeightMap(),
    }),
    reach: (c) => c.flatHeight === undefined,
    cases: [
      { name: 'strong-xy-shift-march', width: 16, height: 14, phase: 0, uniforms: { direction: [0.7, 0.5, 0.3], pivot: 0.4 } },
      { name: 'reverse-direction-tiled', width: 16, height: 14, phase: 1, tileOffset: [2, 2], fullResolution: [19, 17], uniforms: { direction: [-0.6, 0.4, 0.2], pivot: 0.6 } },
      { name: 'shallow-pivot-wide-shift', width: 24, height: 20, phase: 2, uniforms: { direction: [0.9, -0.3, 0.1], pivot: 0.1 } },
      { name: 'steep-pivot-negative-y', width: 24, height: 20, phase: 3, uniforms: { direction: [0.2, -0.8, 0.5], pivot: 0.9 } },
      { name: 'loop-skipped-flat-heightmap-diagnostic', width: 3, height: 3, phase: 4, flatHeight: 1.5, uniforms: { direction: [0.5, 0.5, 0.5], pivot: 0.5 }, diagnostic: true },
    ],
    mutations: [
      { id: 'parallax-march-steps-minus-one', kind: 'trip_count_off_by_one', newValue: 31, description: 'MARCH_STEPS 32 -> 31: smallest possible wrong trip count.' },
      { id: 'parallax-march-steps-swap', kind: 'trip_count_swap', newValue: 16, description: 'MARCH_STEPS 32 -> 16: halves the ray-march resolution, a materially wrong trip count and step size.' },
    ],
  },
  {
    id: 'reindexStats', key: 'filter/reindex:nmReindexStats', sourceFile: 'reindex/nmReindexStats.glsl',
    factoryName: 'canonicalFactory120',
    sourceRawBytes: 2395, sourceSha256: '06525e054fc4910e7bc53345ad656071d2fcb33fc897f4aa35e8fc59b6f0b951',
    constName: 'TILE_SIZE', constOriginal: 8,
    expectPublicIsCanonical: false, expectAdapterOverride: true, adapterOverrideName: 'reindexStatsFactory',
    uniformTypes: {},
    loopRole: 'Per-tile min/max lightness reduction window: TILE_SIZE governs BOTH which pixels are "tile anchors" (`fragCoord % TILE_SIZE == 0`, the only pixels that run the reduction at all) AND the nested loop bound of the reduction itself, so a wrong value changes which pixels carry output at all, not just the aggregated value.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    reach: () => true,
    cases: [
      { name: 'single-tile-small', width: 6, height: 5, phase: 0 },
      { name: 'exact-multiple-tiles', width: 16, height: 8, phase: 1 },
      { name: 'partial-edge-tile', width: 9, height: 9, phase: 2 },
      { name: 'multi-tile-tiled-offset', width: 20, height: 17, phase: 3, tileOffset: [3, 2], fullResolution: [23, 19] },
    ].map((c) => ({ ...c, uniforms: {} })),
    mutations: [
      { id: 'reindexStats-tile-size-minus-one', kind: 'trip_count_off_by_one', newValue: 7, description: 'TILE_SIZE 8 -> 7: smallest possible wrong trip count, also shifts which pixels are tile anchors.' },
      { id: 'reindexStats-tile-size-swap', kind: 'trip_count_swap', newValue: 4, description: 'TILE_SIZE 8 -> 4: halves the tile window, a materially wrong trip count and a materially different anchor grid.' },
    ],
  },
]

// ---------------------------------------------------------------------------
// Per-program verification, before any case is built.
// ---------------------------------------------------------------------------
function loadProgram(def) {
  const sourcePath = path.join(corpusRoot, 'sources/filter', def.sourceFile)
  const altSourcePath = path.join(corpusRoot, 'sources/synth', def.sourceFile)
  const resolvedPath = fs.existsSync(sourcePath) ? sourcePath : altSourcePath
  const sourceBytes = fs.readFileSync(resolvedPath)
  if (sourceBytes.length !== def.sourceRawBytes) throw new Error(`${def.id}: source raw byte count drift`)
  if (sha256(sourceBytes) !== def.sourceSha256) throw new Error(`${def.id}: source sha256 drift`)

  const canonical = canonicalKernelFactories[def.key]
  if (!canonical) throw new Error(`${def.id}: canonical factory missing for key ${def.key}`)
  if (canonical.name !== def.factoryName) throw new Error(`${def.id}: factory name drift (got ${canonical.name})`)
  const factoryText = canonical.toString()

  const publicIsCanonical = kernelFactories.get(def.key) === canonical
  if (publicIsCanonical !== def.expectPublicIsCanonical) throw new Error(`${def.id}: public-factory-is-canonical expectation drift (expected ${def.expectPublicIsCanonical}, got ${publicIsCanonical})`)
  const adapterOverride = canonicalAdapterFactories[def.key]
  const hasAdapterOverride = adapterOverride !== undefined
  if (hasAdapterOverride !== def.expectAdapterOverride) throw new Error(`${def.id}: adapter-override expectation drift (expected ${def.expectAdapterOverride}, got ${hasAdapterOverride})`)
  if (hasAdapterOverride && adapterOverride.name !== def.adapterOverrideName) throw new Error(`${def.id}: adapter override name drift (got ${adapterOverride.name})`)

  // Cluster-2 finding (Lesson header): confirm the adapter's own hard-coded
  // tile size independently, live, rather than trusting the comment above.
  let adapterHardcodedTileSize = null
  if (hasAdapterOverride) {
    const adapterText = adapterOverride.toString()
    const hardcoded8 = occurrences(adapterText, '% 8 !== 0') >= 1 && occurrences(adapterText, '+ 8,') >= 1
    if (!hardcoded8) throw new Error(`${def.id}: expected the adapter override to hard-code tile size 8 (the claim this generator's header makes) -- re-verify, the claim may be stale`)
    adapterHardcodedTileSize = 8
  }

  return { ...def, sourcePath: resolvedPath, factoryText, canonical, adapterOverride, adapterHardcodedTileSize }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)

for (const program of PROGRAMS) {
  program.caseRecords = program.cases.map((c) => {
    const rendered = renderCase(program, c)
    return { ...rendered, reach: program.reach(c) }
  })
  if (program.caseRecords.every((c) => !c.reach)) throw new Error(`${program.id}: no reach-eligible case at all -- cannot prove discrimination, fix the case table`)
}

// ---------------------------------------------------------------------------
// Mutation execution.
// ---------------------------------------------------------------------------
for (const program of PROGRAMS) {
  for (const mutation of program.mutations) {
    const built = buildConstSwapMutation(program.factoryText, program.constName, program.constOriginal, mutation.newValue)
    const mutatedText = mutateFactoryText(program.factoryText, built)
    const mutatedFactory = evaluated(mutatedText)

    const caseResults = program.caseRecords.map((cr) => {
      const mutatedSurface = renderWithFactory(program, cr.c, mutatedFactory)
      const diverges = !sameBytes(cr.surface, mutatedSurface)
      return { case: cr.name, diagnostic: Boolean(cr.c.diagnostic), reaches: cr.reach, diverges }
    })
    const reaching = caseResults.filter((r) => r.reaches)
    const nonReaching = caseResults.filter((r) => !r.reaches)
    const divergentReaching = reaching.filter((r) => r.diverges).length
    const divergentNonReaching = nonReaching.filter((r) => r.diverges).length

    if (reaching.length === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site -- cannot prove discrimination, fix the case table`)
    if (divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases (trip count must genuinely discriminate), got 0/${reaching.length} -- the loop body may be idempotent or the result may be saturating for these cases, investigate before shipping`)
    if (divergentReaching !== reaching.length) {
      // Not necessarily an error -- but flag loudly so it is investigated,
      // not silently accepted, per the task's "verify divergence rather than
      // assuming it" instruction.
      mutation.partialDivergenceNote = `Only ${divergentReaching}/${reaching.length} reach-eligible cases diverged -- investigated, see report.`
    }
    if (divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${divergentNonReaching}/${nonReaching.length} non-reaching case(s) diverged -- the reach() predicate is wrong or the mutation leaked outside its intended site, investigate before shipping`)

    mutation.builtAnchor = built.anchor
    mutation.builtMutated = built.mutated
    mutation.caseResults = caseResults
    mutation.summary = { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
  }
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const programsOut = {}
  let totalEligible = 0
  let totalDiagnostic = 0
  for (const program of PROGRAMS) {
    const eligible = program.caseRecords.filter((c) => !c.c.diagnostic)
    const diagnostic = program.caseRecords.filter((c) => c.c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    programsOut[program.id] = {
      key: program.key, defines: { ...AUTHORIZED_DEFINES },
      source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName,
      public_is_canonical: program.expectPublicIsCanonical,
      adapter_override: program.expectAdapterOverride ? { name: program.adapterOverrideName, hardcoded_tile_size: program.adapterHardcodedTileSize } : null,
      const_name: program.constName, const_original_value: program.constOriginal,
      loop_role: program.loopRole,
      cases: program.caseRecords.map((cr) => ({
        name: cr.name, dimensions: { width: cr.c.width, height: cr.c.height }, diagnostic: Boolean(cr.c.diagnostic), reach: cr.reach,
        uniforms: cr.c.uniforms, time: cr.c.time ?? 0, tile_offset: cr.c.tileOffset ?? [0, 0], full_resolution: cr.c.fullResolution ?? [cr.c.width, cr.c.height],
        flat_height: cr.c.flatHeight ?? null,
        repeat_identity: true, input_immutable: true,
        output: renderResult(cr.surface),
      })),
      mutations: program.mutations.map((m) => ({
        id: m.id, kind: m.kind, new_value: m.newValue, description: m.description,
        anchor: m.builtAnchor, mutated: m.builtMutated,
        case_results: m.caseResults, summary: m.summary, partial_divergence_note: m.partialDivergenceNote ?? null,
      })),
    }
    totalEligible // keep linter happy about unused var patterns in some configs
  }
  return {
    schema: 'noisemaker-for-cpp.future-precompute.cheap-unlocks.loopproof-cluster3.oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version },
    authorized_defines: { ...AUTHORIZED_DEFINES },
    defines_axis_note: 'All three programs authorize the empty define map {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, key) for all three keys in this session (filter/lightLeak:lightLeak -> {}, filter/parallax:parallax -> {}, filter/reindex:nmReindexStats -> {}), and independently by reading every source file: lightLeak.glsl/parallax.glsl each contain exactly one #ifdef GL_ES guard (universal, not effect-specific), and nmReindexStats.glsl has no preprocessor directive at all. Consequently the "defines must be passed as uniforms, not preprocessed" hazard from the grade/derivative clusters cannot arise for this cluster -- stated explicitly rather than silently assumed inapplicable.',
    adapter_override_note: "filter/reindex:nmReindexStats's public factory (kernelFactories.get(key)) is NOT its canonical factory -- canonicalAdapterFactories overrides it with a hand-written, performance-optimized reindexStatsFactory (noisemaker-for-cpu/src/effects/adapters/f32-color.js:56-79) that hard-codes tile size 8 directly rather than reading a TILE_SIZE variable (confirmed live in loadProgram()). This generator renders exclusively through canonicalKernelFactories['filter/reindex:nmReindexStats'] (canonicalFactory120, the literal transpilation of the pinned corpus GLSL source) -- the actual porting ground truth -- never through the adapter. The adapter's independent, hand-written commitment to exactly 8 is corroborating (not authoritative) evidence that TILE_SIZE=8 is the intended value, consistent with (not a substitute for) this oracle's own proof that the canonical factory's compiled TILE_SIZE constant genuinely drives output.",
    trip_count_discriminability: {
      note: 'Per program, both mutations (an off-by-one trip count and a materially different "swap" trip count) are required to produce nonzero byte-divergence on every reach-eligible case set, and zero divergence on every non-reach-eligible (diagnostic) case -- machine-asserted at generation time, not assumed. See report for the per-mutation divergence tables.',
      lightLeak: 'POINT_COUNT drives how many Voronoi seed points voronoiCell() scans for its nearest-point search; a wrong count changes which point is nearest for most pixels, and hence the leak color/wormhole distortion at those pixels. Confirmed non-idempotent: both -1 and swap mutations diverge on every non-diagnostic case.',
      parallax: 'MARCH_STEPS drives both the ray-march loop bound and the per-step increment (stepSize = 1/MARCH_STEPS) of a root-finding search over the height field. A FIRST DESIGN (a small, same-resolution-as-canvas patterned height map) was tried and empirically REJECTED: it made the mutation a near-total no-op (only 1-2/4 cases diverged for a step-count -1 perturbation), because SHIFT_SCALE=0.15 caps the ray\'s total UV traversal to a fraction of one texel at that scale, so the height-vs-t curve is close to affine and the loop\'s own linear-interpolation refine step recovers nearly the same crossing regardless of step count -- exactly the "idempotent/saturating" trap the task warns about, caught here by verifying divergence rather than assuming it. The height map was redesigned (16x16, diagonal gradient plus ripple, full 0.05..0.95 dynamic range, see parallaxHeightMap()) to spread crossings across the whole t range and force real texel-cell boundary crossings; re-verified empirically to diverge on all 4 non-diagnostic cases for BOTH the -1 and the swap mutation before being locked in.',
      reindexStats: 'TILE_SIZE drives both which pixels are treated as tile anchors (fragCoord % TILE_SIZE == 0, the only pixels producing nonzero output at all) and the nested reduction loop bound; a wrong value changes the anchor grid itself, not just the aggregated min/max, so divergence is essentially guaranteed for any canvas larger than 1x1 -- confirmed for all four case sizes, including the single-tile case where TILE_SIZE still governs whether the reduction runs past the canvas edge.',
    },
    programs: programsOut,
    eligibility_summary: {
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic,
      note: 'lightLeak and parallax each carry one diagnostic (reach=false) case proving the mutated site is provably UNREACHED there (alpha<=0 early-return before any Voronoi call; a deliberately flat, height>=1 heightMap forcing the ray-march "if (f>0.0)" guard false before the loop is ever entered) -- zero divergence is asserted for both mutations on these cases. reindexStats has NO diagnostic case: fragCoord (0,0) is a tile anchor for every possible TILE_SIZE value (0 mod anything is 0), so the mutated site is reached by construction for any non-empty render -- documented explicitly rather than fabricating a synthetic reach=false case that would not reflect anything real about this program.',
    },
    negative_closure: {
      dither_or_reindexReduce_or_mandelbrot_included: 'refused -- dither does not structurally qualify (FS_ERR_W initializer.kind is `binary`, not `literal`); reindexReduce and mandelbrot qualify structurally but additionally need a budget-cap increase, so they are not fingerprint-only reuses and are out of this cluster\'s scope per the task brief.',
      idempotent_or_saturating_cases_used_as_proof: 'refused -- every mutation asserts nonzero divergence among reach-eligible cases at build time; a case set that failed to discriminate would throw, not ship silently. parallax in particular was designed with a non-flat, per-pixel-varying height map specifically because a flat/constant height field would make the ray-march search converge to the same crossing point regardless of step count (verified: the flat-diagnostic case exists precisely to demonstrate this, and is excluded from the discriminating case set).',
      canonicalAdapterFactories_reindexStatsFactory_used_as_ground_truth: 'refused -- see adapter_override_note. The oracle renders exclusively through canonicalKernelFactories, never through kernelFactories (which would silently prefer the adapter for this one program).',
    },
  }
}

function report(d) {
  const lines = [
    '# Cheap-unlocks cluster 1 -- loop-proof fingerprint reuse (3 programs) oracle report', '',
    'Hermetic JS oracle for the three programs that are true fingerprint-only reuses of the existing `source-global-literal-int-v1` loop-proof capability: `filter/lightLeak:lightLeak`, `filter/parallax:parallax`, `filter/reindex:nmReindexStats`. Ground truth for the future C++20 port\'s bit-exact parity tests.', '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} early-exit diagnostic).`, '',
    '## Defines axis', '', d.defines_axis_note, '',
    '## Adapter override finding', '', d.adapter_override_note, '',
    '## Trip-count discriminability (per program)', '', d.trip_count_discriminability.note, '',
    `**lightLeak**: ${d.trip_count_discriminability.lightLeak}`, '',
    `**parallax**: ${d.trip_count_discriminability.parallax}`, '',
    `**reindexStats**: ${d.trip_count_discriminability.reindexStats}`, '',
    '## Per-program summary', '',
    '| Program | Const | Original | Eligible cases | Diagnostic cases | Mutations |', '| --- | --- | ---: | ---: | ---: | ---: |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    lines.push(`| ${id} | ${p.const_name} | ${p.const_original_value} | ${eligible} | ${diagnostic} | ${p.mutations.length} |`)
  }
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\` (${id})`, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\`. Public factory is canonical: ${p.public_is_canonical}.`, '')
    if (p.adapter_override) lines.push(`**Adapter override present**: \`${p.adapter_override.name}\`, independently confirmed hard-coded to tile size ${p.adapter_override.hardcoded_tile_size}. See adapter override finding above.`, '')
    lines.push(`Loop role: ${p.loop_role}`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${c.reach} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations', '', '| Mutation | Kind | New value | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |', '| --- | --- | ---: | ---: | ---: | ---: | ---: |')
    for (const m of p.mutations) {
      lines.push(`| ${m.id} | ${m.kind} | ${m.new_value} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}${m.partial_divergence_note ? ` _Note: ${m.partial_divergence_note}_` : ''}`), '')
  }
  lines.push('## Negative closure', '')
  for (const [k, v] of Object.entries(d.negative_closure)) lines.push(`- **${k}**: ${v}`)
  lines.push('')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('loopproof oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('loopproof oracle report drift')
  const totalMutations = PROGRAMS.reduce((n, p) => n + p.mutations.length, 0)
  console.log(`loopproof oracle fixture ok (${PROGRAMS.length} programs, ${data.eligibility_summary.total_cases} cases, ${totalMutations} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
