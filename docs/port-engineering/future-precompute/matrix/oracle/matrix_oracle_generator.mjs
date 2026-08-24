import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { createCanonicalBindings } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel, GlslCpuRuntime } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

// ---------------------------------------------------------------------------
// Matrix-dispatch cluster oracle -- Slice B (matrix*vector), 5 programs:
//   filter/adjust:adjust            filter/colorspace:colorspace
//   classicNoisedeck/cellNoise:cellNoise
//   classicNoisedeck/colorLab:colorLab
//   classicNoisedeck/shapes:shapes
//
// This is the JS-golden ground truth the future C++20 port's matrix-vector
// dispatch (mat3*vec3, N=3) will be asserted against, bit-exactly. `glitch`
// (Slice C, mat4 chained matrix*matrix) is deliberately EXCLUDED -- it needs
// a different lowering and is out of scope, per
// `docs/port-engineering/future-precompute/matrix/matrix-precompute-report.md`.
//
// Follows the house style of
// `docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs`
// (hermetic imports, --check determinism, per-case mutation testing with a
// reserved-key intent-verification guard) and
// `docs/port-engineering/derivatives/oracle/derivative_oracle_generator.mjs`
// (per-uniform binding-observation assertion, defines-bound-as-uniforms
// verification). Both were read, not assumed, before writing this file.
//
// ALL FIVE PROGRAMS SHARE ONE LIVE MATRIX HELPER, `linear_srgb_from_oklab`:
//   vec3 linear_srgb_from_oklab(vec3 c) {
//     vec3 lms = fwdA * c;              // mat3 * vec3, SIMPLE operand
//     return fwdB * (lms * lms * lms);  // mat3 * vec3, COMPOUND operand
//   }
// Three of the five (cellNoise, colorLab, shapes) ALSO declare the inverse,
// `oklab_from_linear_srgb` (invA/invB), but never CALL it from `main()` at
// any reachable branch -- confirmed by direct source read (below) and
// independently corroborated by the precompute report's call-graph probe.
//
// THE LOAD-BEARING HAZARD (independently re-derived from the live
// `canonicalKernelFactories` text, not trusted from the precompute report
// alone -- see loadProgram()'s structural asserts):
//   Finding A (SAFE, live): `fwdA * c` transpiles to an inlined per-row
//   sum-of-products expression, and `fwdB * (lms*lms*lms)` transpiles to a
//   `.map()` call whose SECOND argument (the cube) is wrapped in
//   `new $runtime.PooledFloat32Array([...])` -- narrowed to f32 BEFORE the
//   row-dot-product runs. Both shapes compute the full row-sum in double and
//   narrow exactly ONCE, matching C++'s `operator*(Mat<N>, Vec<N,float>)`
//   (`glsl_types.hpp:231`, `result[row] = f32(sum)`) exactly. This is
//   PROVEN, not assumed, by mutation testing below (`*-cube-unnarrowed`):
//   removing that narrowing step measurably diverges the final f32 bit
//   pattern for ordinary (non-degenerate) inputs.
//   Finding B (present, but DEAD, and additionally PROVABLY UNOBSERVABLE by
//   an "unnarrow the compound operand" test): the inverse's compound operand
//   is `sign(lms) * pow(abs(lms), vec3(1/3))`, transpiled as
//   `vec3.multiply([], sign(lms), pow(...))` -- the `[]` is a genuine plain
//   JS Array, never narrowed, matching the report's documented divergent
//   shape. BUT `sign(x) in {-1, 0, 1}` and both operands are already
//   individually f32-narrowed (`sign`/`pow` are `#unary`/`#binary` stdlib
//   calls, which narrow every element), so their product is an EXACT
//   multiply by a unit magnitude at ANY precision -- narrowing timing cannot
//   change the bit pattern. Verified two ways below: a closed-form proof
//   (this comment) and an empirical, machine-asserted zero-divergence sweep
//   (`buildDeadInverseNarrowingProof`). This narrows, but does not
//   contradict, the precompute report's Finding B/C -- the general
//   "un-narrowed compound operand" divergence class is real (proven live for
//   `linear_srgb_from_oklab`'s cube), it simply happens not to manifest for
//   THIS SPECIFIC dead function's sign-multiply shape.
//
// PER-PROGRAM NARROWING VERDICT (stated once here, repeated in the report):
//   adjust, colorspace       -- narrowing-SAFE, no dead inverse exists at all.
//   cellNoise, colorLab, shapes -- LIVE half narrowing-SAFE (Finding A);
//     DEAD half carries Finding B's divergent code shape but is provably
//     unobservable for this specific pattern (see above); cannot be
//     render-validated regardless (unreachable from main()).
//
// THREE HARD-WON LESSONS APPLIED THROUGHOUT:
//   1. RESERVED TOP-LEVEL KEYS. `createCanonicalBindings` (glsl-kernel.js
//      :20-61) assigns nine canonical keys (resolution, fullResolution,
//      tileOffset, aspectRatio, aspect, time, globalTime, deltaTime, frame)
//      AFTER spreading `...uniforms`, so passing any of them *inside* the
//      uniforms object silently discards the caller's intended value. Every
//      case here renders through `renderCase()`, which refuses to build if
//      the uniforms object illegally contains one of these keys, then
//      independently reconstructs the bindings and asserts the kernel's own
//      bound value for EVERY declared uniform (not just the three
//      historically-bitten ones) equals the CALLER's intended value --
//      generalizing the grade generator's lesson-1 guard with the
//      derivative generator's per-uniform assertion loop.
//   2. DEFINES ARE BOUND AS UNIFORMS, NOT PREPROCESSED. `shapes.glsl` pins
//      two compile-time-looking `#ifndef LOOP_A_OFFSET / #define
//      LOOP_A_OFFSET 40` macros. The JS reference has no preprocessor:
//      reading the canonical factory's own text shows `LOOP_A_OFFSET` and
//      `LOOP_B_OFFSET` are read via `$bindings["LOOP_A_OFFSET"]` /
//      `$bindings["LOOP_B_OFFSET"]` at RUNTIME. `generate_typed_slice.
//      _defaults()` was independently run against the live repo (not
//      assumed) and returns `{LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30}` for
//      `classicNoisedeck/shapes:shapes` and `{}` for the other four keys --
//      every `shapes` case below passes these two names inside `uniforms`
//      at exactly that authorized value, and `loadProgram()` independently
//      asserts the factory text actually reads each `$bindings[...]` name.
//   3. REACHABILITY MUST BE PROVEN PER CALL SITE, NOT PER PROGRAM. Each
//      program's `reach()` predicate is derived from a direct read of its
//      `main()`/`pal()` branch structure (documented per-program below), not
//      copied from the precompute report's summary table. `runMutation()`
//      machine-asserts every reach-eligible case actually diverges under
//      each mutation and every non-reaching case shows ZERO divergence --
//      if the reach() predicate or a mutation's scope were wrong, the build
//      throws rather than silently freezing a wrong expectation (per this
//      project's "time-in-uniforms" postmortem, `REMAINING-WORK-ROADMAP.md`
//      standing hazard #6).
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'matrix-oracles.json')
const reportPath = path.join(here, 'matrix-oracle-report.md')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpusRoot = `tools/glslcpp/corpus/${revision}`
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const glslKernelPath = '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
const glslRuntimePath = '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
const passRunnerPath = '../noisemaker-for-cpu/src/runtime/pass-runner.js'
const surfacePath = '../noisemaker-for-cpu/src/runtime/surface.js'
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
// hash VALUES to the grade and derivative generators (same repo state),
// independently recomputed here, not copy-pasted trust.
// ---------------------------------------------------------------------------
const RUNTIME_PROVENANCE = {
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
  glsl_kernel_sha256: 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa',
  glsl_runtime_sha256: 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072',
  pass_runner_sha256: 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa',
  surface_sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
}
for (const [file, hash] of [
  [canonicalPath, RUNTIME_PROVENANCE.canonical_kernels_sha256],
  [catalogPath, RUNTIME_PROVENANCE.public_catalog_sha256],
  [adapterPath, RUNTIME_PROVENANCE.adapter_index_sha256],
  [glslKernelPath, RUNTIME_PROVENANCE.glsl_kernel_sha256],
  [glslRuntimePath, RUNTIME_PROVENANCE.glsl_runtime_sha256],
  [passRunnerPath, RUNTIME_PROVENANCE.pass_runner_sha256],
  [surfacePath, RUNTIME_PROVENANCE.surface_sha256],
]) {
  if (sha256(fs.readFileSync(file)) !== hash) throw new Error(`runtime drift: ${file}`)
}

// ---------------------------------------------------------------------------
// Lesson 1: reserved top-level keys + full per-uniform intent verification.
// ---------------------------------------------------------------------------
const RESERVED_TOP_LEVEL_KEYS = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']
function assertNoReservedKeysInUniforms(uniforms) {
  for (const k of RESERVED_TOP_LEVEL_KEYS) {
    if (Object.prototype.hasOwnProperty.call(uniforms, k)) {
      throw new Error(`uniforms illegally contains reserved top-level-only key "${k}" -- createCanonicalBindings assigns this AFTER spreading ...uniforms, so it would be silently discarded`)
    }
  }
}

function renderCase(factory, opts) {
  assertNoReservedKeysInUniforms(opts.uniforms)
  const intendedTime = opts.time ?? 0
  const intendedTileOffset = opts.tileOffset ?? new Float32Array(2)
  const intendedFullResolution = opts.fullResolution ?? new Float32Array([opts.width, opts.height])
  const bindings = createCanonicalBindings(opts)
  if (f32Bits(bindings.time) !== f32Bits(f(intendedTime))) throw new Error('kernel did not observe intended time -- top-level binding lesson violated')
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error('kernel did not observe intended tileOffset -- top-level binding lesson violated')
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error('kernel did not observe intended fullResolution -- top-level binding lesson violated')
  for (const [k, v] of Object.entries(opts.uniforms)) {
    const bound = bindings[k]
    if (bound === undefined) throw new Error(`kernel bindings missing declared uniform "${k}" entirely -- intent-verification lesson violated`)
    const same = ArrayBuffer.isView(v)
      ? Array.from(v).every((x, i) => f32Bits(x) === f32Bits(bound[i]))
      : (typeof v === 'boolean' ? bound === v : f32Bits(typeof v === 'number' ? f(v) : v) === f32Bits(typeof bound === 'number' ? f(bound) : bound))
    if (!same) throw new Error(`kernel did not observe intended uniform "${k}" -- reserved-key, spread-order, or define-as-uniform defect`)
  }
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(opts.width, opts.height)
  runPass({ kernel, destination: output })
  return output
}

// ---------------------------------------------------------------------------
// Deterministic patterned input texture -- same construction as the grade
// and derivative generators, so R/G/B/A genuinely differ per pixel and no
// two cases in the whole oracle share an input (distinct `phase`).
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

function normalizeUniformsTyped(typeMap, raw) {
  const out = {}
  for (const [k, v] of Object.entries(raw)) {
    const type = typeMap[k]
    if (!type) throw new Error(`unknown uniform "${k}" -- not declared in this program's type map (check for typos or a missing entry)`)
    if (type === 'bool') out[k] = Boolean(v)
    else if (type === 'int') out[k] = v | 0
    else if (type === 'float') out[k] = f(v)
    else if (type === 'vec3') out[k] = new Float32Array(v.map(f))
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
}

// ---------------------------------------------------------------------------
// Block extraction (marker-based, occurrence-checked), matching the grade
// generator's discipline.
// ---------------------------------------------------------------------------
function extractBlock(factoryText, startMarker, endMarker) {
  const start = factoryText.indexOf(startMarker)
  if (start === -1) throw new Error(`start marker missing: ${startMarker}`)
  if (factoryText.indexOf(startMarker, start + 1) !== -1) throw new Error(`start marker not unique: ${startMarker}`)
  const endIdx = factoryText.indexOf(endMarker, start)
  if (endIdx === -1) throw new Error(`end marker missing after start marker: ${startMarker} .. ${endMarker}`)
  const block = factoryText.slice(start, endIdx + endMarker.length)
  if (occurrences(factoryText, block) !== 1) throw new Error(`extracted block not unique in factory text: ${startMarker}`)
  return block
}
function mutateFactoryText(factoryText, mutation) {
  if (occurrences(factoryText, mutation.anchor) !== 1) throw new Error(`mutation anchor not unique at apply-time: ${mutation.id}`)
  return factoryText.replace(mutation.anchor, mutation.mutated)
}

// ---------------------------------------------------------------------------
// Mutation A: "wrong matrix constant" -- swap fwdB's column 0 and column 1
// (a plausible transposition/copy-paste bug). fwdB is genuinely asymmetric
// (no row/column is a scalar multiple of another), so this changes the
// entire live-half output for any non-degenerate input -- the exact class
// of bug `matrix_type_admission`'s emitter lowering must not ship.
// ---------------------------------------------------------------------------
const FWDB_ANCHOR = 'var fwdB = new Float32Array([4.076724529266357, -1.2681437730789185, -0.004111988469958305, -3.3072168827056885, 2.609332323074341, -0.7034763097763062, 0.23075905442237854, -0.3411344289779663, 1.7068625688552856]);'
const FWDB_COLUMN_SWAPPED = 'var fwdB = new Float32Array([-1.2681437730789185, 2.609332323074341, -0.3411344289779663, 4.076724529266357, -3.3072168827056885, 0.23075905442237854, -0.004111988469958305, -0.7034763097763062, 1.7068625688552856]);'
function buildConstantSwapMutation() {
  return { anchor: FWDB_ANCHOR, mutated: FWDB_COLUMN_SWAPPED, siteCount: 1 }
}

// ---------------------------------------------------------------------------
// Mutation B: "compound-operand narrowing removed" -- simulate what would
// ship if the emitter's `matN*vecN` lowering fed the un-narrowed
// `lms*lms*lms` double-precision intermediate straight into the row
// dot-product instead of narrowing it to f32 first (Finding B's divergence
// class, applied to the LIVE cube pattern instead of the dead sign*pow
// pattern where it happens to be unobservable -- see module header).
// Scoped to the `linear_srgb_from_oklab` block only (via start/end markers)
// so it cannot accidentally touch the dead `oklab_from_linear_srgb`, which
// has its own, textually distinct compound-operand shape.
// ---------------------------------------------------------------------------
const LIVE_FN_START = 'function linear_srgb_from_oklab (c) {'
const LIVE_FN_END = '}, fwdB);\n  };'
const LIVE_CUBE_NARROWED_ANCHOR = '(new $runtime.PooledFloat32Array([(lms[0] * lms[0]) * lms[0], (lms[1] * lms[1]) * lms[1], (lms[2] * lms[2]) * lms[2]]))'
const LIVE_CUBE_UNNARROWED = '([(lms[0] * lms[0]) * lms[0], (lms[1] * lms[1]) * lms[1], (lms[2] * lms[2]) * lms[2]])'
function buildCompoundNarrowingMutation(factoryText) {
  const block = extractBlock(factoryText, LIVE_FN_START, LIVE_FN_END)
  if (occurrences(block, LIVE_CUBE_NARROWED_ANCHOR) !== 1) throw new Error('cube-narrowing anchor not found exactly once inside linear_srgb_from_oklab block')
  return { anchor: LIVE_CUBE_NARROWED_ANCHOR, mutated: LIVE_CUBE_UNNARROWED, siteCount: 1 }
}

// ---------------------------------------------------------------------------
// Dead-inverse structural anchors (cellNoise, colorLab, shapes only).
// ---------------------------------------------------------------------------
const DEAD_FN_START = 'function oklab_from_linear_srgb (c) {'
const DEAD_SIGN_POW_UNNARROWED_ANCHOR = 'vec3.multiply([], sign(lms), pow(abs(lms), new $runtime.PooledFloat32Array([0.3333333432674408, 0.3333333432674408, 0.3333333432674408])))'
const DEAD_SIGN_POW_NARROWED = 'vec3.multiply(new $runtime.PooledFloat32Array(3), sign(lms), pow(abs(lms), new $runtime.PooledFloat32Array([0.3333333432674408, 0.3333333432674408, 0.3333333432674408])))'

// ---------------------------------------------------------------------------
// Direct-closure extraction (grade generator's technique, extended here to
// program-local matrix helpers): replace the factory's `return function
// canonicalKernel(...)` tail with a plain object exposing the named
// internal closures, so direct rows invoke the REAL closures directly.
// ---------------------------------------------------------------------------
const KERNEL_TAIL_MARKER = '  return function canonicalKernel(context, out) {'
function buildExtractorFactory(factoryText, helperNames) {
  const idx = factoryText.lastIndexOf(KERNEL_TAIL_MARKER)
  if (idx === -1) throw new Error('extractor tail marker not found')
  if (occurrences(factoryText, KERNEL_TAIL_MARKER) !== 1) throw new Error('extractor tail marker not unique')
  const head = factoryText.slice(0, idx)
  const extractorText = `${head}  return { ${helperNames.join(', ')} };\n}`
  return evaluated(extractorText)
}
function makeDirectBindings() { return Object.freeze({ ...createCanonicalBindings({ width: 1, height: 1, uniforms: {}, textures: {} }) }) }
function makeDirectRuntime() { return new GlslCpuRuntime() }

// ---------------------------------------------------------------------------
// Program registry. Each entry is independently verified against the live
// corpus/runtime before any case is built (loadProgram, below). Reach
// predicates and defines were derived from a direct read of each program's
// source (module header + inline citations), not copied from the
// precompute report.
// ---------------------------------------------------------------------------
const PROGRAM_DEFS = [
  {
    // adjust.glsl: mode 2 (OKLab) and mode 3 (OKLCH, which also constructs
    // an oklab vec3 from L/C/H before calling the same helper) both reach
    // `linear_srgb_from_oklab`. No inverse function is declared in this
    // program at all (verified: 0 occurrences of "oklab_from_linear_srgb").
    id: 'adjust', key: 'filter/adjust:adjust', sourceFile: 'filter/adjust/adjust.glsl',
    factoryName: 'canonicalFactory19', factorySha256: '30a22b13bc733bcbf15545734336006d3ed09101cf82bc6d7c589c843c09e3b0',
    sourceSha256: 'dc1d8456ff2bb6d00ecc62af33ef3a730a990b18b7037d29a29a6e3a3b963ce8', sourceRawBytes: 3786,
    defines: {}, hasDeadInverse: false, textureNames: ['inputTex'],
    uniformTypes: { mode: 'int', rotation: 'float', hueRange: 'float', saturation: 'float', brightness: 'float', contrast: 'float' },
    reach: (u) => ({ matrix: u.mode === 2 || u.mode === 3 }),
    cases: [
      { name: 'oklab-mode-varied', width: 6, height: 5, phase: 700, uniforms: { mode: 2, rotation: 37, hueRange: 120, saturation: 1.3, brightness: 1.05, contrast: 0.6 } },
      { name: 'oklch-mode-tiled', width: 5, height: 6, phase: 701, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { mode: 3, rotation: -95, hueRange: 64, saturation: 0.4, brightness: 0.9, contrast: 1.4 } },
      { name: 'oklab-mode-extreme', width: 7, height: 4, phase: 702, uniforms: { mode: 2, rotation: 0, hueRange: 200, saturation: 2, brightness: 1, contrast: 1 } },
      { name: 'oklch-mode-negative-tiled', width: 4, height: 7, phase: 703, tileOffset: [1, 3], fullResolution: [10, 12], uniforms: { mode: 3, rotation: 180, hueRange: 0, saturation: 0, brightness: 1, contrast: 1 } },
      { name: 'hsv-mode-diagnostic', width: 3, height: 3, phase: 704, uniforms: { mode: 1, rotation: 45, hueRange: 100, saturation: 1, brightness: 1, contrast: 0.5 }, diagnostic: true },
      { name: 'off-mode-diagnostic', width: 3, height: 3, phase: 705, uniforms: { mode: 0, rotation: 0, hueRange: 100, saturation: 1, brightness: 1, contrast: 0.5 }, diagnostic: true },
    ],
  },
  {
    // colorspace.glsl: mode 1 (OKLab) and mode 2 (OKLCH, else-branch) both
    // reach `linear_srgb_from_oklab`. No inverse declared (0 occurrences).
    id: 'colorspace', key: 'filter/colorspace:colorspace', sourceFile: 'filter/colorspace/colorspace.glsl',
    factoryName: 'canonicalFactory38', factorySha256: '5c4ede05fe48ee05b9c0e1198450ea28f6018f6038848dfe295a06381f8df883',
    sourceSha256: '602f1a2ce0abd59e8e17753c8ec9b49d01fbe0f169d60ad290d294904e02f705', sourceRawBytes: 2711,
    defines: {}, hasDeadInverse: false, textureNames: ['inputTex'],
    uniformTypes: { mode: 'int' },
    reach: (u) => ({ matrix: u.mode === 1 || u.mode === 2 }),
    cases: [
      { name: 'oklab-mode', width: 6, height: 5, phase: 710, uniforms: { mode: 1 } },
      { name: 'oklch-mode-tiled', width: 5, height: 6, phase: 711, tileOffset: [2, 2], fullResolution: [9, 13], uniforms: { mode: 2 } },
      { name: 'oklab-mode-tiled', width: 7, height: 4, phase: 712, tileOffset: [3, 1], fullResolution: [14, 10], uniforms: { mode: 1 } },
      { name: 'oklch-mode-extreme-canvas', width: 4, height: 7, phase: 713, uniforms: { mode: 2 } },
      { name: 'hsv-mode-diagnostic', width: 3, height: 3, phase: 714, uniforms: { mode: 0 }, diagnostic: true },
    ],
  },
  {
    // cellNoise.glsl: `pal(d)` is only called when colorMode==2 (main.glsl
    // line ~350), and INSIDE `pal()` the matrix path only fires at
    // paletteMode==2 -- so reach requires BOTH. `oklab_from_linear_srgb` is
    // declared (invA/invB) but never called anywhere in this file.
    id: 'cellNoise', key: 'classicNoisedeck/cellNoise:cellNoise', sourceFile: 'classicNoisedeck/cellNoise/cellNoise.glsl',
    factoryName: 'canonicalFactory2', factorySha256: 'c22f3abe9db76b0b926895c55fdf202847f65a78ca9940dc4ac7122f9e9f53b6',
    sourceSha256: '9fd76306b377ef501a5dd340263179f04e3e890cc05d5e82f524f7bdf793d3b8', sourceRawBytes: 9643,
    defines: {}, hasDeadInverse: true, textureNames: ['tex'],
    uniformTypes: {
      seed: 'int', renderScale: 'float', shape: 'int', scale: 'float', cellScale: 'float', cellSmooth: 'float',
      variation: 'float', speed: 'float', paletteMode: 'int', paletteOffset: 'vec3', paletteAmp: 'vec3',
      paletteFreq: 'vec3', palettePhase: 'vec3', colorMode: 'int', cyclePalette: 'int', rotatePalette: 'float',
      repeatPalette: 'float', texInfluence: 'int', texIntensity: 'float',
    },
    reach: (u) => ({ matrix: u.colorMode === 2 && u.paletteMode === 2 }),
    cases: [
      { name: 'oklab-palette-worley', width: 6, height: 5, phase: 720, time: 0.3, uniforms: { seed: 11, renderScale: 1, shape: 0, scale: 40, cellScale: 50, cellSmooth: 20, variation: 15, speed: 2, paletteMode: 2, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], colorMode: 2, cyclePalette: 0, rotatePalette: 10, repeatPalette: 1, texInfluence: 0, texIntensity: 0 } },
      { name: 'oklab-palette-tiled', width: 5, height: 6, phase: 721, time: 1.7, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { seed: 47, renderScale: 1, shape: 1, scale: 60, cellScale: 30, cellSmooth: 40, variation: 60, speed: -1, paletteMode: 2, paletteOffset: [0.3, 0.6, 0.5], paletteAmp: [0.5, 0.3, 0.4], paletteFreq: [2, 1.5, 1], palettePhase: [0.1, 0.4, 0.9], colorMode: 2, cyclePalette: 1, rotatePalette: -30, repeatPalette: 2, texInfluence: 0, texIntensity: 0 } },
      { name: 'oklab-palette-hexagon-tex-influence', width: 7, height: 4, phase: 722, time: 0, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { seed: 5, renderScale: 1, shape: 2, scale: 20, cellScale: 75, cellSmooth: 5, variation: 90, speed: 0, paletteMode: 2, paletteOffset: [0.6, 0.4, 0.5], paletteAmp: [0.35, 0.45, 0.3], paletteFreq: [0.8, 1.2, 1.6], palettePhase: [0.25, 0.6, 0.15], colorMode: 2, cyclePalette: -1, rotatePalette: 50, repeatPalette: 0.5, texInfluence: 1, texIntensity: 60 } },
      { name: 'oklab-palette-extreme', width: 4, height: 7, phase: 723, time: 5, uniforms: { seed: 99, renderScale: 1, shape: 4, scale: 1, cellScale: 1, cellSmooth: 100, variation: 0, speed: 10, paletteMode: 2, paletteOffset: [0, 1, 0.5], paletteAmp: [1, 1, 1], paletteFreq: [5, 5, 5], palettePhase: [0.5, 0.5, 0.5], colorMode: 2, cyclePalette: 0, rotatePalette: 0, repeatPalette: 3, texInfluence: 0, texIntensity: 0 } },
      { name: 'diagnostic-colorMode-grayscale', width: 3, height: 3, phase: 724, time: 0, uniforms: { seed: 1, renderScale: 1, shape: 0, scale: 40, cellScale: 50, cellSmooth: 20, variation: 15, speed: 0, paletteMode: 2, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], colorMode: 0, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, texInfluence: 0, texIntensity: 0 }, diagnostic: true },
      { name: 'diagnostic-paletteMode-hsv', width: 3, height: 3, phase: 725, time: 0, uniforms: { seed: 1, renderScale: 1, shape: 0, scale: 40, cellScale: 50, cellSmooth: 20, variation: 15, speed: 0, paletteMode: 1, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], colorMode: 2, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, texInfluence: 0, texIntensity: 0 }, diagnostic: true },
    ],
  },
  {
    // colorLab.glsl: TWO reach paths -- colorMode==3 calls
    // `linear_srgb_from_oklab` directly; colorMode==4 calls `pal(d)`, which
    // reaches it only when paletteMode==2. `oklab_from_linear_srgb` is
    // declared but never called anywhere in this file.
    id: 'colorLab', key: 'classicNoisedeck/colorLab:colorLab', sourceFile: 'classicNoisedeck/colorLab/colorLab.glsl',
    factoryName: 'canonicalFactory5', factorySha256: '14a7f15dcc865abb6780304e3e4f8d427a47255f638da38a78c075680ec932dd',
    sourceSha256: '8a2615887cde9ad2f6adead3a6f69a9f21ac015f762e6add80f23aa293bd530a', sourceRawBytes: 9273,
    defines: {}, hasDeadInverse: true, textureNames: ['inputTex'],
    uniformTypes: {
      renderScale: 'float', levels: 'float', dither: 'int', hueRotation: 'float', hueRange: 'float', invert: 'bool',
      brightness: 'float', contrast: 'float', saturation: 'float', colorMode: 'int', paletteMode: 'int',
      paletteOffset: 'vec3', paletteAmp: 'vec3', paletteFreq: 'vec3', palettePhase: 'vec3', cyclePalette: 'int',
      rotatePalette: 'float', repeatPalette: 'float',
    },
    reach: (u) => ({ matrix: u.colorMode === 3 || (u.colorMode === 4 && u.paletteMode === 2) }),
    cases: [
      { name: 'oklab-direct', width: 6, height: 5, phase: 730, time: 0.2, uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: 15, hueRange: 80, invert: false, brightness: 5, contrast: 40, saturation: 10, colorMode: 3, paletteMode: 0, paletteOffset: [0, 0, 0], paletteAmp: [0, 0, 0], paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1 } },
      { name: 'oklab-direct-tiled-inverted', width: 5, height: 6, phase: 731, time: 1.1, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: -40, hueRange: 150, invert: true, brightness: -20, contrast: 70, saturation: -30, colorMode: 3, paletteMode: 0, paletteOffset: [0, 0, 0], paletteAmp: [0, 0, 0], paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1 } },
      { name: 'palette-oklab-tiled', width: 7, height: 4, phase: 732, time: 0, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: 0, hueRange: 0, invert: false, brightness: 0, contrast: 50, saturation: 0, colorMode: 4, paletteMode: 2, paletteOffset: [0.5, 0.4, 0.6], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1.5, 1.2, 0.8], palettePhase: [0.2, 0.5, 0.8], cyclePalette: 1, rotatePalette: 25, repeatPalette: 2 } },
      { name: 'palette-oklab-cycle-negative', width: 4, height: 7, phase: 733, time: 3.4, uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: 60, hueRange: 200, invert: false, brightness: 10, contrast: 20, saturation: 15, colorMode: 4, paletteMode: 2, paletteOffset: [0.3, 0.7, 0.5], paletteAmp: [0.6, 0.2, 0.5], paletteFreq: [0.5, 2.5, 1], palettePhase: [0.9, 0.1, 0.4], cyclePalette: -1, rotatePalette: -60, repeatPalette: 0.5 } },
      { name: 'diagnostic-colorMode-grayscale', width: 3, height: 3, phase: 734, time: 0, uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: 0, hueRange: 0, invert: false, brightness: 0, contrast: 50, saturation: 0, colorMode: 0, paletteMode: 0, paletteOffset: [0, 0, 0], paletteAmp: [0, 0, 0], paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1 }, diagnostic: true },
      { name: 'diagnostic-palette-hsv', width: 3, height: 3, phase: 735, time: 0, uniforms: { renderScale: 1, levels: 0, dither: 0, hueRotation: 0, hueRange: 0, invert: false, brightness: 0, contrast: 50, saturation: 0, colorMode: 4, paletteMode: 1, paletteOffset: [0.5, 0.4, 0.6], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1.5, 1.2, 0.8], palettePhase: [0.2, 0.5, 0.8], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1 }, diagnostic: true },
    ],
  },
  {
    // shapes.glsl: `pal(d)` is called UNCONDITIONALLY from main() (no
    // colorMode gate exists in this program at all), so reach reduces to
    // paletteMode==2 alone. LOOP_A_OFFSET/LOOP_B_OFFSET are read via
    // $bindings at runtime (Lesson 2) -- generate_typed_slice._defaults()
    // was run live against the repo and returns {LOOP_A_OFFSET: 40,
    // LOOP_B_OFFSET: 30}, matching this file's own #ifndef defaults, so
    // every case below pins both at exactly that authorized value.
    // `oklab_from_linear_srgb` is declared but never called anywhere.
    id: 'shapes', key: 'classicNoisedeck/shapes:shapes', sourceFile: 'classicNoisedeck/shapes/shapes.glsl',
    factoryName: 'canonicalFactory16', factorySha256: 'a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3',
    sourceSha256: '60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0', sourceRawBytes: 21289,
    defines: { LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 }, hasDeadInverse: true, textureNames: [],
    uniformTypes: {
      seed: 'int', wrap: 'bool', loopAScale: 'float', loopBScale: 'float', speedA: 'float', speedB: 'float',
      paletteMode: 'int', paletteOffset: 'vec3', paletteAmp: 'vec3', paletteFreq: 'vec3', palettePhase: 'vec3',
      cyclePalette: 'int', rotatePalette: 'float', repeatPalette: 'float', LOOP_A_OFFSET: 'int', LOOP_B_OFFSET: 'int',
    },
    reach: (u) => ({ matrix: u.paletteMode === 2 }),
    cases: [
      { name: 'oklab-palette-a', width: 6, height: 5, phase: 740, time: 0.5, uniforms: { seed: 3, wrap: false, loopAScale: 50, loopBScale: 50, speedA: 20, speedB: -10, paletteMode: 2, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 } },
      { name: 'oklab-palette-tiled', width: 5, height: 6, phase: 741, time: 2.1, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { seed: 77, wrap: true, loopAScale: 10, loopBScale: 90, speedA: -40, speedB: 60, paletteMode: 2, paletteOffset: [0.3, 0.6, 0.4], paletteAmp: [0.5, 0.2, 0.45], paletteFreq: [2, 0.5, 1.5], palettePhase: [0.2, 0.7, 0.5], cyclePalette: 1, rotatePalette: 15, repeatPalette: 2, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 } },
      { name: 'oklab-palette-extreme', width: 7, height: 4, phase: 742, time: 0, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { seed: 150, wrap: false, loopAScale: 100, loopBScale: 1, speedA: 0, speedB: 100, paletteMode: 2, paletteOffset: [0, 1, 0.5], paletteAmp: [1, 1, 1], paletteFreq: [5, 3, 4], palettePhase: [0.5, 0.5, 0.5], cyclePalette: -1, rotatePalette: 80, repeatPalette: 0.5, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 } },
      { name: 'oklab-palette-negative-speed', width: 4, height: 7, phase: 743, time: 4.4, uniforms: { seed: 9, wrap: true, loopAScale: 1, loopBScale: 100, speedA: 100, speedB: -100, paletteMode: 2, paletteOffset: [0.6, 0.4, 0.5], paletteAmp: [0.35, 0.4, 0.3], paletteFreq: [0.8, 1.6, 1.2], palettePhase: [0.6, 0.15, 0.85], cyclePalette: 0, rotatePalette: -45, repeatPalette: 3, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 } },
      { name: 'diagnostic-palette-hsv', width: 3, height: 3, phase: 744, time: 0, uniforms: { seed: 1, wrap: false, loopAScale: 50, loopBScale: 50, speedA: 0, speedB: 0, paletteMode: 1, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 }, diagnostic: true },
      { name: 'diagnostic-palette-rgb', width: 3, height: 3, phase: 745, time: 0, uniforms: { seed: 1, wrap: false, loopAScale: 50, loopBScale: 50, speedA: 0, speedB: 0, paletteMode: 0, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.4, 0.4, 0.4], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, LOOP_A_OFFSET: 40, LOOP_B_OFFSET: 30 }, diagnostic: true },
    ],
  },
]

// ---------------------------------------------------------------------------
// Per-program verification, before any case is built.
// ---------------------------------------------------------------------------
function loadProgram(def) {
  const sourcePath = path.join(corpusRoot, 'sources', def.sourceFile)
  const sourceBytes = fs.readFileSync(sourcePath)
  if (sourceBytes.length !== def.sourceRawBytes) throw new Error(`${def.id}: source raw byte count drift`)
  if (sha256(sourceBytes) !== def.sourceSha256) throw new Error(`${def.id}: source sha256 drift`)

  const canonical = canonicalKernelFactories[def.key]
  if (!canonical) throw new Error(`${def.id}: canonical factory missing for key ${def.key}`)
  if (canonical.name !== def.factoryName) throw new Error(`${def.id}: factory name drift (got ${canonical.name})`)
  const factoryText = canonical.toString()
  if (sha256(factoryText) !== def.factorySha256) throw new Error(`${def.id}: factory toString() sha256 drift`)
  if (kernelFactories.get(def.key) !== canonical) throw new Error(`${def.id}: public factory is not the canonical identity`)
  if (canonicalAdapterFactories[def.key] !== undefined) throw new Error(`${def.id}: unexpected adapter override present`)
  if (Boolean(canonical.usesDerivatives)) throw new Error(`${def.id}: unexpectedly uses derivatives -- out of scope for this oracle`)

  // Structural narrowing-shape verification (Findings A/B, independently
  // re-derived here rather than trusted from the precompute report).
  if (occurrences(factoryText, LIVE_FN_START) !== 1) throw new Error(`${def.id}: linear_srgb_from_oklab not found or not unique`)
  if (!factoryText.includes(LIVE_CUBE_NARROWED_ANCHOR)) throw new Error(`${def.id}: expected narrow-safe cube shape (Finding A) not found -- narrowing analysis may be stale`)
  const hasDeadInverse = occurrences(factoryText, DEAD_FN_START) === 1
  if (def.hasDeadInverse !== hasDeadInverse) throw new Error(`${def.id}: dead-inverse presence drift (expected ${def.hasDeadInverse}, found ${hasDeadInverse})`)
  if (hasDeadInverse && !factoryText.includes(DEAD_SIGN_POW_UNNARROWED_ANCHOR)) throw new Error(`${def.id}: expected divergent-shape (Finding B) not found in oklab_from_linear_srgb`)

  // Defines-as-uniforms binding requirement (Lesson 2).
  for (const defineName of Object.keys(def.defines)) {
    if (!factoryText.includes(`$bindings["${defineName}"]`)) throw new Error(`${def.id}: factory does not read $bindings["${defineName}"] -- define-as-uniform binding requirement violated`)
  }

  return { ...def, sourcePath, factoryText, canonical }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)

// ---------------------------------------------------------------------------
// Case rendering.
// ---------------------------------------------------------------------------
function buildCaseRecords(program) {
  return program.cases.map((c) => {
    const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
    const textures = {}
    program.textureNames.forEach((texName, index) => {
      textures[texName] = patternedSurface(c.width, c.height, c.phase + (index + 1) * 10000)
    })
    const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
    const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
    const opts = { width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time: c.time ?? 0 }

    const inputBytesBefore = {}
    for (const [name, tex] of Object.entries(textures)) inputBytesBefore[name] = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')
    const first = renderCase(program.canonical, opts)
    for (const [name, tex] of Object.entries(textures)) {
      const after = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')
      if (inputBytesBefore[name] !== after) throw new Error(`${program.id}/${c.name}: input texture "${name}" was mutated by render`)
    }
    const second = renderCase(program.canonical, opts)
    if (!sameBytes(first, second)) throw new Error(`${program.id}/${c.name}: repeat-render mismatch`)

    const reach = program.reach(c.uniforms)
    return {
      def: c, name: c.name, dimensions: { width: c.width, height: c.height },
      defines: { ...program.defines }, eligible_for_native_binding: true,
      diagnostic: Boolean(c.diagnostic), reach,
      uniforms: c.uniforms, time: c.time ?? 0,
      tile_offset: c.tileOffset ?? [0, 0], full_resolution: c.fullResolution ?? [c.width, c.height],
      repeat_identity: true, input_immutable: true,
      output: renderResult(first),
      opts, surface: first,
    }
  })
}

for (const program of PROGRAMS) program.caseRecords = buildCaseRecords(program)

// ---------------------------------------------------------------------------
// Mutation definitions + execution (per-case harness identical in spirit to
// the grade generator's: every reach-eligible case must diverge, every
// non-reaching case must NOT).
// ---------------------------------------------------------------------------
function buildMutationsForProgram(program) {
  const mutations = []
  {
    const m = buildConstantSwapMutation()
    mutations.push({
      id: `${program.id}-fwdB-column-swap`, kind: 'constant', reachKey: 'matrix',
      hazard: 'wrong-matrix-constant',
      description: 'Swap fwdB column 0 and column 1 -- a plausible transposition/copy-paste bug in the emitted mat3 constructor. fwdB is asymmetric (no row/column is a scalar multiple of another), so this changes the live-half output structurally.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }
  {
    const m = buildCompoundNarrowingMutation(program.factoryText)
    mutations.push({
      id: `${program.id}-cube-unnarrowed`, kind: 'narrowing', reachKey: 'matrix',
      hazard: 'compound-operand-narrowing-removed',
      description: 'Remove the f32-narrowing wrap around the lms*lms*lms cube before it feeds fwdB\'s row dot-product -- simulates an emitter that lowers matN*vecN for a COMPOUND operand by accumulating in double without narrowing first (Finding B\'s divergence class, verified live on this SAFE-by-construction site). Proves the narrow-once contract (glsl_types.hpp:231/233) is load-bearing, not incidental.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }
  return mutations
}

function runMutation(program, mutation) {
  const mutatedText = mutateFactoryText(program.factoryText, mutation)
  const mutatedFactory = evaluated(mutatedText)
  const caseResults = program.caseRecords.map((c) => {
    const mutatedSurface = renderCase(mutatedFactory, c.opts)
    const diverges = !sameBytes(c.surface, mutatedSurface)
    const reaches = Boolean(c.reach[mutation.reachKey])
    return { case: c.name, diagnostic: c.diagnostic, reaches, diverges }
  })
  const reachingCases = caseResults.filter((r) => r.reaches)
  const nonReachingCases = caseResults.filter((r) => !r.reaches)
  const divergentReaching = reachingCases.filter((r) => r.diverges).length
  const divergentNonReaching = nonReachingCases.filter((r) => r.diverges).length
  return { caseResults, reachingCount: reachingCases.length, divergentReaching, nonReachingCount: nonReachingCases.length, divergentNonReaching }
}

for (const program of PROGRAMS) {
  program.mutations = buildMutationsForProgram(program)
  for (const mutation of program.mutations) {
    const result = runMutation(program, mutation)
    mutation.result = result
    if (result.reachingCount === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site at all -- cannot prove discrimination, fix the case table`)
    if (result.divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${result.reachingCount} -- investigate before shipping`)
    if (result.divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${result.divergentNonReaching}/${result.nonReachingCount} non-reaching case(s) diverged -- the reach() predicate or the mutation's scope is wrong, investigate before shipping`)
  }
}

// ---------------------------------------------------------------------------
// Direct rows: freeze the exact narrowing behavior of `linear_srgb_from_oklab`
// (all 5 programs) using the REAL extracted closure -- not reimplemented --
// against BOTH mutations, plus a dedicated proof for the DEAD
// `oklab_from_linear_srgb` (cellNoise/colorLab/shapes only) that the
// sign*pow compound operand is UNOBSERVABLE under the same narrowing-removal
// technique (machine-asserted zero divergence across every row, with the
// closed-form reason recorded alongside).
//
// Six fixed input rows are used throughout, chosen deliberately (not
// "small round numbers"): a zero-vector control (mathematically exact
// no-op for a linear map, regardless of matrix constants or narrowing
// timing -- included precisely to demonstrate why trivial inputs prove
// nothing), plus five inputs -- including two found by random search
// specifically to need >24 bits of mantissa to round correctly -- that DO
// discriminate.
// ---------------------------------------------------------------------------
const DIRECT_ROW_INPUTS = [
  { label: 'zero-vector-control', input: [0, 0, 0] },
  { label: 'round-halves', input: [0.5, 0.5, 0.5] },
  { label: 'round-simple', input: [0.2, 0.5, 0.9] },
  { label: 'unit-corners', input: [1, 1, 1] },
  { label: 'mantissa-sensitive-1', input: [0.3026677668094635, -0.4383176267147064, 0.9536864757537842] },
  { label: 'mantissa-sensitive-2', input: [-0.031175531446933746, 0.25623390078544617, -0.7011103630065918] },
]

function liveDirectRows(program) {
  const helperNames = ['linear_srgb_from_oklab']
  const real = buildExtractorFactory(program.factoryText, helperNames)(makeDirectBindings(), makeDirectRuntime())
  const constantSwapMutation = program.mutations.find((m) => m.id === `${program.id}-fwdB-column-swap`)
  const narrowingMutation = program.mutations.find((m) => m.id === `${program.id}-cube-unnarrowed`)
  const constantSwapExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, constantSwapMutation), helperNames)(makeDirectBindings(), makeDirectRuntime())
  const narrowingExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, narrowingMutation), helperNames)(makeDirectBindings(), makeDirectRuntime())

  const rows = DIRECT_ROW_INPUTS.map(({ label, input }) => {
    const c = new Float32Array(input.map(f))
    const realResult = Array.from(real.linear_srgb_from_oklab(new Float32Array(c)))
    const swapResult = Array.from(constantSwapExtractor.linear_srgb_from_oklab(new Float32Array(c)))
    const narrowResult = Array.from(narrowingExtractor.linear_srgb_from_oklab(new Float32Array(c)))
    const divergesFromSwap = realResult.some((x, i) => f32Bits(x) !== f32Bits(swapResult[i]))
    const divergesFromUnnarrowed = realResult.some((x, i) => f32Bits(x) !== f32Bits(narrowResult[i]))
    return {
      label, input: Array.from(c), input_bits: Array.from(c).map(f32Bits),
      real_result: realResult, real_result_bits: realResult.map(f32Bits),
      fwdB_column_swap_result: swapResult, fwdB_column_swap_result_bits: swapResult.map(f32Bits), diverges_from_fwdB_column_swap: divergesFromSwap,
      cube_unnarrowed_result: narrowResult, cube_unnarrowed_result_bits: narrowResult.map(f32Bits), diverges_from_cube_unnarrowed: divergesFromUnnarrowed,
    }
  })

  const zeroRow = rows.find((r) => r.label === 'zero-vector-control')
  if (zeroRow.diverges_from_fwdB_column_swap || zeroRow.diverges_from_cube_unnarrowed) {
    throw new Error(`${program.id}: zero-vector control row unexpectedly diverged -- the "zero vector is an exact no-op for a linear map" proof is WRONG, investigate`)
  }
  const nonZeroRows = rows.filter((r) => r.label !== 'zero-vector-control')
  if (!nonZeroRows.some((r) => r.diverges_from_fwdB_column_swap)) throw new Error(`${program.id}: no non-zero direct row diverges under fwdB-column-swap -- direct rows do not exercise the hazard`)
  if (!nonZeroRows.some((r) => r.diverges_from_cube_unnarrowed)) throw new Error(`${program.id}: no non-zero direct row diverges under cube-unnarrowed -- direct rows do not exercise the hazard`)

  return rows
}

// Structural-only: prove the dead inverse's sign*pow compound operand is
// unobservable under the same "remove narrowing" mutation technique, with
// the closed-form reason (sign(x) in {-1,0,1}, both operands already
// individually f32-narrowed by #unary/#binary stdlib calls, so their
// product is an exact multiply by a unit magnitude at any precision).
function buildDeadInverseNarrowingProof(program) {
  const helperNames = ['oklab_from_linear_srgb']
  const real = buildExtractorFactory(program.factoryText, helperNames)(makeDirectBindings(), makeDirectRuntime())
  if (occurrences(program.factoryText, DEAD_SIGN_POW_UNNARROWED_ANCHOR) !== 1) throw new Error(`${program.id}: dead sign*pow anchor not found exactly once`)
  const fixedText = program.factoryText.split(DEAD_SIGN_POW_UNNARROWED_ANCHOR).join(DEAD_SIGN_POW_NARROWED)
  const fixed = buildExtractorFactory(fixedText, helperNames)(makeDirectBindings(), makeDirectRuntime())

  const rows = DIRECT_ROW_INPUTS.map(({ label, input }) => {
    const c = new Float32Array(input.map(f))
    const realResult = Array.from(real.oklab_from_linear_srgb(new Float32Array(c)))
    const narrowedResult = Array.from(fixed.oklab_from_linear_srgb(new Float32Array(c)))
    const diverges = realResult.some((x, i) => f32Bits(x) !== f32Bits(narrowedResult[i]))
    return {
      label, input: Array.from(c), input_bits: Array.from(c).map(f32Bits),
      real_asshipped_result: realResult, real_asshipped_result_bits: realResult.map(f32Bits),
      hypothetically_narrowed_result: narrowedResult, hypothetically_narrowed_result_bits: narrowedResult.map(f32Bits),
      diverges: diverges,
    }
  })
  if (rows.some((r) => r.diverges)) {
    throw new Error(`${program.id}: dead-inverse narrowing proof FAILED -- expected zero divergence (sign*pow is exact regardless of narrowing timing), but at least one row diverged; the closed-form proof is wrong or the anchor targets the wrong site`)
  }
  return {
    proof: 'sign(x) in {-1, 0, 1} for all real x (IEEE754 sign, ignoring NaN), and both `sign(lms)` and `pow(abs(lms), vec3(1/3))` are already individually f32-narrowed before the multiply (sign/pow are #unary/#binary stdlib calls in glsl-runtime.js, which narrow every element to f32 on write). Multiplying an f32 value by exactly -1, 0, or 1 is EXACT at any precision -- it can only flip a sign bit or zero the result, never round. Therefore narrowing the PRODUCT before vs. after feeding it into the invA row dot-product cannot change the bit pattern, and this is a mathematically provable, not merely empirically observed, zero-divergence result.',
    rows,
  }
}

for (const program of PROGRAMS) {
  program.directRowsLive = liveDirectRows(program)
  program.directRowsDeadInverse = program.hasDeadInverse ? buildDeadInverseNarrowingProof(program) : null
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const programsOut = {}
  let totalEligible = 0
  let totalDiagnostic = 0
  for (const program of PROGRAMS) {
    const eligible = program.caseRecords.filter((c) => !c.diagnostic)
    const diagnostic = program.caseRecords.filter((c) => c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    programsOut[program.id] = {
      key: program.key, defines: { ...program.defines },
      source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName, canonical_factory_to_string_sha256: program.factorySha256,
      has_dead_inverse: program.hasDeadInverse,
      closures_exercised_by_cases: ['linear_srgb_from_oklab'],
      closures_structural_only: program.hasDeadInverse ? ['oklab_from_linear_srgb'] : [],
      narrowing_verdict: program.hasDeadInverse
        ? 'live half (linear_srgb_from_oklab) narrowing-SAFE, verified by mutation (see cube-unnarrowed); dead half (oklab_from_linear_srgb) carries Finding B\'s divergent code shape but is unreachable from main() and, independently, provably unobservable for its specific sign*pow operand -- see direct_rows_dead_inverse.proof'
        : 'narrowing-SAFE, verified by mutation (see cube-unnarrowed); no inverse function exists in this program',
      cases: program.caseRecords.map((c) => ({
        name: c.name, dimensions: c.dimensions, defines: c.defines, eligible_for_native_binding: c.eligible_for_native_binding,
        diagnostic: c.diagnostic, reach: c.reach, uniforms: c.uniforms, time: c.time, tile_offset: c.tile_offset, full_resolution: c.full_resolution,
        repeat_identity: c.repeat_identity, input_immutable: c.input_immutable, output: c.output,
      })),
      mutations: program.mutations.map((m) => ({
        id: m.id, kind: m.kind, reach_key: m.reachKey, hazard: m.hazard, description: m.description, site_count: m.siteCount,
        case_results: m.result.caseResults,
        summary: { reaching_cases: m.result.reachingCount, divergent_reaching: m.result.divergentReaching, non_reaching_cases: m.result.nonReachingCount, divergent_non_reaching: m.result.divergentNonReaching },
      })),
      direct_rows_live: program.directRowsLive,
      direct_rows_dead_inverse: program.directRowsDeadInverse,
    }
  }

  return {
    schema: 'noisemaker-for-cpp.future-precompute.matrix.slice-b-matrix-vector-closure-oracles.v1',
    corpus_revision: revision,
    scope_note: 'Slice B only: mat3*vec3 (N=3) matrix-vector dispatch across 5 programs (adjust, colorspace, cellNoise, colorLab, shapes). glitch (Slice C, mat4 chained matrix*matrix) is deliberately excluded -- different lowering, different oracle.',
    provenance: { ...RUNTIME_PROVENANCE, node: process.version, public_identity: true, adapter_absent: true },
    narrowing_analysis: {
      finding_a_live_safe: 'linear_srgb_from_oklab (all 5 programs): fwdA*c (simple operand) is an inlined per-row sum-of-products expression; fwdB*(lms*lms*lms) (compound operand) narrows the cube to f32 (wrapped in new $runtime.PooledFloat32Array([...])) BEFORE the row dot-product. Both compute the full row-sum in double and narrow exactly once, matching C++ operator*(Mat<N>,Vec<N,float>) (glsl_types.hpp:231) and operator*(Mat<N>,FloatExpr<N>) (glsl_types.hpp:233) exactly. Proven by mutation (see each program\'s "*-cube-unnarrowed" entry): removing the narrowing step measurably diverges the final f32 output for ordinary inputs.',
      finding_b_dead_and_unobservable: 'oklab_from_linear_srgb (cellNoise, colorLab, shapes only): invB*c is narrow-safe by the same shape as fwdA*c; the inverse\'s compound operand invA*(sign(lms)*pow(abs(lms),vec3(1/3))) transpiles with the divergent shape vec3.multiply([], sign(lms), pow(...)) (plain Array, never narrowed) -- matching the precompute report\'s Finding B exactly. This function is NEVER called from main() in any of the 3 programs that declare it (confirmed by direct source read), so it cannot be render-validated regardless. Additionally and independently, its specific compound-operand shape is PROVABLY UNOBSERVABLE under a narrowing-removal mutation: sign(x) in {-1,0,1}, both operands already individually f32-narrowed, so their product is an exact multiply by unit magnitude at any precision -- see each affected program\'s direct_rows_dead_inverse.proof for the closed-form argument and the machine-asserted zero-divergence sweep.',
      slice_c_out_of_scope: 'The report\'s Finding C (matrix*matrix chained products via matrixMult\'s un-narrowed Array accumulator, live in glitch\'s T*Q*S bicubic chain) is a DIFFERENT divergence, in a DIFFERENT program, requiring a DIFFERENT lowering (chained-product, not vector-multiply) -- explicitly out of scope for this Slice B oracle per the task brief.',
    },
    programs: programsOut,
    eligibility_summary: {
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic,
      note: 'diagnostic cases render through branches that do NOT reach the matrix code (off/hsv modes, colorMode=0/1, paletteMode=0/1) specifically to prove the reach() classification and mutation scoping are sound -- zero divergence is expected and machine-asserted for every mutation on every diagnostic case.',
    },
    negative_closure: {
      slice_c_glitch: 'excluded -- mat4 chained matrix*matrix, different lowering, see narrowing_analysis.slice_c_out_of_scope',
      moodscape_noise_effects: 'excluded -- entire matrix closure dead at authorized defines in all three (per the precompute report\'s reachability probe; not independently re-verified here since this oracle only targets the 5 live-or-half-live Slice B programs)',
      dead_inverse_treated_as_render_validated: 'forbidden -- oklab_from_linear_srgb is validated structurally only (direct closure invocation + narrowing proof), never through a full-render case, because it has zero live callers in all 3 programs that declare it',
      generic_mat3_vec3_capability: 'forbidden -- this oracle is scoped to the 5 named program_keys and their exact fwdA/fwdB/invA/invB constant identities, not "any mat3*vec3 site"',
    },
  }
}

function report(d) {
  const lines = [
    '# Matrix-dispatch cluster (Slice B: matrix*vector) closure oracle report', '',
    `Corpus revision \`${d.corpus_revision}\`. 5 programs. ${d.scope_note}`, '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} non-reaching diagnostic).`, '',
    '## Narrowing analysis', '',
    `**Finding A (live, safe)**: ${d.narrowing_analysis.finding_a_live_safe}`, '',
    `**Finding B (dead, and separately unobservable)**: ${d.narrowing_analysis.finding_b_dead_and_unobservable}`, '',
    `**Slice C (out of scope)**: ${d.narrowing_analysis.slice_c_out_of_scope}`, '',
    '## Per-program summary', '',
    '| Program | Key | Has dead inverse | Eligible cases | Diagnostic cases | Mutations | Narrowing verdict |', '| --- | --- | --- | ---: | ---: | ---: | --- |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    lines.push(`| ${id} | \`${p.key}\` | ${p.has_dead_inverse} | ${eligible} | ${diagnostic} | ${p.mutations.length} | ${p.narrowing_verdict.split('.')[0]}. |`)
  }
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\``, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\` (\`${p.canonical_factory_to_string_sha256}\`). Defines: \`${JSON.stringify(p.defines)}\`.`, '')
    lines.push(`Closures exercised by full-render cases: ${p.closures_exercised_by_cases.map((c) => `\`${c}\``).join(', ')}.`)
    lines.push(p.closures_structural_only.length ? `Closures authenticated structurally ONLY (dead, never render-validated): ${p.closures_structural_only.map((c) => `\`${c}\``).join(', ')}.` : 'No dead closures in this program.', '')
    lines.push(`Narrowing verdict: ${p.narrowing_verdict}`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${JSON.stringify(c.reach)} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations', '', '| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |', '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |')
    for (const m of p.mutations) {
      lines.push(`| ${m.id} | ${m.kind} | ${m.reach_key} | ${m.site_count} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}`), '')
    lines.push(`### Direct rows: \`linear_srgb_from_oklab\` (live)`, '', `${p.direct_rows_live.length} rows, real closure invoked directly. Zero-vector control row shows zero divergence under both mutations (proven exact no-op); at least one non-zero row diverges under each (machine-asserted).`, '')
    if (p.direct_rows_dead_inverse) {
      lines.push(`### Direct rows: \`oklab_from_linear_srgb\` (dead, structural only)`, '', `${p.direct_rows_dead_inverse.rows.length} rows, real closure invoked directly. ALL rows show zero divergence under the narrowing-removal mutation, machine-asserted -- proof: ${p.direct_rows_dead_inverse.proof}`, '')
    }
    lines.push('')
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
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('matrix oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('matrix oracle report drift')
  const totalMutations = PROGRAMS.reduce((n, p) => n + p.mutations.length, 0)
  console.log(`matrix oracle fixture ok (${PROGRAMS.length} programs, ${data.eligibility_summary.total_cases} cases, ${totalMutations} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
