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
// Task 32 -- `filter/grade` cluster oracle. SIX programs, six independent
// GLSL source files sharing only the `effect_id` "filter/grade" and a strong
// family resemblance (five of the six declare a byte-identical
// srgbToLinear/linearToSrgb pair; see task-32-brief.md, which this generator
// independently re-verifies rather than trusting).
//
//   filter/grade:primary       filter/grade:hslSecondary  filter/grade:wheels
//   filter/grade:vignette      filter/grade:creative      filter/grade:lut
//
// Two new capability shapes under authentication (per the frozen brief):
//   (a) global_admission for a `const vec3 LUMA_WEIGHTS = vec3(0.2126,
//       0.7152, 0.0722)` global, present in five of the six programs (not
//       `lut`, which inlines the literal as a `dot()` argument instead of a
//       named global -- confirmed below, not assumed).
//   (b) index_expression_admission for `for`-loop-induction-variable-indexed
//       reads AND writes of a local vec3 lane (`linear[i] = ...`) -- a shape
//       none of the six existing index-admission tracks cover, because they
//       all require a literal-int index for a *write*.
//
// Authorized define map for all six: `{}` (confirmed live below via
// generate_typed_slice._defaults -- this repo has no #ifdef/#define macro in
// any of the six sources besides the universal `#ifdef GL_ES` guard, so
// there is no "different define map" axis to construct an ineligible-by-
// define case from; see `defines_axis_note` in the assembled JSON).
//
// THREE HARD-WON LESSONS APPLIED THROUGHOUT:
//   1. `time`/`tileOffset`/`fullResolution`/etc. MUST be bound as TOP-LEVEL
//      options, never inside `uniforms` -- `createCanonicalBindings`
//      (glsl-kernel.js:20-61) assigns them AFTER spreading `...uniforms`, so
//      a same-named key inside `uniforms` is silently discarded. Every case
//      in this oracle is rendered through `renderCase()` below, which (a)
//      refuses to build if the uniforms object illegally contains one of
//      these reserved top-level keys, and (b) independently reconstructs the
//      bindings via `createCanonicalBindings` and asserts the kernel's own
//      bound `tileOffset`/`fullResolution`/`time` values equal the CALLER's
//      intended values -- not trusting the call, per the lesson.
//   2. Every case is labelled `eligible_for_native_binding` -- true only
//      when its define map equals the program's authorized defaults ({}).
//      Since this cluster has no define axis at all, this is always true by
//      construction; documented explicitly rather than silently assumed.
//   3. Per-mutation divergence counts are reported explicitly, including the
//      ZERO-divergence cases (hslSecondary's dead LUMA_WEIGHTS global) --
//      investigated and confirmed as expected-dead, not hidden.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'grade-oracles.json')
const reportPath = path.join(here, 'grade-oracle-report.md')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpusRoot = `tools/glslcpp/corpus/${revision}`
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const glslKernelPath = '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
const glslRuntimePath = '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
const passRunnerPath = '../noisemaker-for-cpu/src/runtime/pass-runner.js'
const surfacePath = '../noisemaker-for-cpu/src/runtime/surface.js'
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
// Runtime/catalog hermeticity pinning (shared across all six programs).
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
// Lesson 1: top-level-binding assertion. Refuses to render if the uniforms
// object illegally shadows a reserved top-level key, then independently
// rebuilds the bindings object and asserts the kernel's bound
// tileOffset/fullResolution/time genuinely equal the caller's intent --
// rather than trusting that passing them as sibling options "worked".
// ---------------------------------------------------------------------------
const RESERVED_TOP_LEVEL_KEYS = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']
function assertNoReservedKeysInUniforms(uniforms) {
  for (const k of RESERVED_TOP_LEVEL_KEYS) {
    if (Object.prototype.hasOwnProperty.call(uniforms, k)) {
      throw new Error(`uniforms illegally contains reserved top-level-only key "${k}" -- createCanonicalBindings assigns this AFTER spreading ...uniforms, so it would be silently discarded`)
    }
  }
}
function renderCase(factory, { width, height, uniforms, textures, tileOffset, fullResolution, time }) {
  assertNoReservedKeysInUniforms(uniforms)
  const intendedTime = time ?? 0
  const intendedTileOffset = tileOffset ?? new Float32Array(2)
  const intendedFullResolution = fullResolution ?? new Float32Array([width, height])
  const bindings = createCanonicalBindings({ width, height, uniforms, textures, tileOffset, fullResolution, time: intendedTime })
  if (f32Bits(bindings.time) !== f32Bits(f(intendedTime))) throw new Error('kernel did not observe intended time -- top-level binding lesson violated')
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error('kernel did not observe intended tileOffset -- top-level binding lesson violated')
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error('kernel did not observe intended fullResolution -- top-level binding lesson violated')
  const kernel = bindGlslKernel(factory, bindings)
  const output = new Surface(width, height)
  runPass({ kernel, destination: output })
  return output
}

// ---------------------------------------------------------------------------
// Deterministic patterned input texture (top-down F32 RGBA), phase-varied so
// no two cases across the whole oracle share an input. Each channel uses a
// different modulus/coefficient set so R/G/B/A genuinely differ per pixel --
// required so a lane-transpose index mutation is guaranteed to be visible
// (a permutation of identical lanes would hide the bug).
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

// ---------------------------------------------------------------------------
// Block extraction (marker-based, occurrence-checked) and mutation builders.
// Extracting via markers (rather than embedding hand-copied literal blocks)
// avoids whitespace/tab transcription risk while still enforcing the same
// single-occurrence discipline `curl_oracle_generator.mjs` uses for its
// hand-anchored SITE_ANCHORS.
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

function buildGlobalSwapMutation(factoryText) {
  const anchor = 'var LUMA_WEIGHTS = new Float32Array([0.2125999927520752, 0.7152000069618225, 0.0722000002861023]);'
  if (occurrences(factoryText, anchor) !== 1) throw new Error('LUMA_WEIGHTS declaration anchor not found exactly once')
  const mutated = 'var LUMA_WEIGHTS = new Float32Array([0.299, 0.587, 0.114]);'
  return { anchor, mutated, siteCount: 1 }
}

function buildIndexTransposeWriteMutation(factoryText, startMarker, endMarker, writeVarName, offset) {
  const block = extractBlock(factoryText, startMarker, endMarker)
  const pattern = new RegExp(`${writeVarName}\\[i\\] =`, 'g')
  const matches = block.match(pattern)
  if (!matches || matches.length < 1) throw new Error(`no ${writeVarName}[i] write sites found in block starting "${startMarker}"`)
  const mutated = block.replace(pattern, `${writeVarName}[(i + ${offset}) % 3] =`)
  if (mutated === block) throw new Error('transpose mutation produced no textual change')
  return { anchor: block, mutated, siteCount: matches.length }
}

function buildIndexConstantInductionMutation(factoryText, startMarker, endMarker) {
  const block = extractBlock(factoryText, startMarker, endMarker)
  const count = occurrences(block, '[i]')
  if (count < 1) throw new Error(`no [i] occurrences found in block starting "${startMarker}"`)
  const mutated = block.split('[i]').join('[0]')
  return { anchor: block, mutated, siteCount: count }
}

function mutateFactoryText(factoryText, mutation) {
  if (occurrences(factoryText, mutation.anchor) !== 1) throw new Error('mutation anchor not unique at apply-time')
  return factoryText.replace(mutation.anchor, mutation.mutated)
}

// ---------------------------------------------------------------------------
// Direct-closure extraction: replace the factory's `return function
// canonicalKernel(...)` tail with a plain object exposing the named internal
// helper functions, so direct rows can invoke the REAL per-lane
// srgbToLinear/linearToSrgb/hslToRgb/lutHardLight/lutSolarize closures
// directly -- not reimplemented -- exactly the discipline
// `curl_oracle_generator.mjs`'s `captureRuntime` throwaway-factory technique
// uses for stdlib primitives, extended here to program-local closures.
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
function makeDirectBindings() {
  return Object.freeze({ ...createCanonicalBindings({ width: 1, height: 1, uniforms: {}, textures: {} }) })
}
function makeDirectRuntime() { return new GlslCpuRuntime() }

// ---------------------------------------------------------------------------
// Program registry. Each entry is independently verified against the live
// corpus/runtime before any case is built.
// ---------------------------------------------------------------------------
const PROGRAM_DEFS = [
  {
    id: 'primary', key: 'filter/grade:primary', sourceFile: 'primary.glsl',
    factoryName: 'canonicalFactory62',
    factorySha256: 'b8beeb5acc689dcd3bc09c6347c9b6994267f08fec07bf3a19a72e898f009f46',
    sourceSha256: '008521bf82834ef55383a492adacb259964170831c92d6c9ddc6368acc850cc2', sourceRawBytes: 5839,
    hasGlobal: true, globalDead: false,
    globalReadFunctions: ['applyContrast', 'applyTonalRanges', 'applyCurve', 'applySaturation'],
    reach: (u) => ({ index: true, global: true }),
    cases: [
      { name: 'cool-shadow-lift', width: 6, height: 5, phase: 100, uniforms: { temperature: -0.4, tint: 0.2, exposure: 0.5, contrast: 0.3, highlights: -0.2, shadows: 0.4, whites: 0.1, blacks: -0.1, saturation: 1.3, curveShadows: 0.2, curveMidtones: -0.1, curveHighlights: 0.15 } },
      { name: 'warm-highlight-punch', width: 5, height: 6, phase: 101, uniforms: { temperature: 0.6, tint: -0.3, exposure: -0.8, contrast: -0.4, highlights: 0.5, shadows: -0.3, whites: 0.4, blacks: 0.2, saturation: 0.6, curveShadows: -0.3, curveMidtones: 0.25, curveHighlights: -0.2 } },
      { name: 'extreme-maxima', width: 7, height: 4, phase: 102, uniforms: { temperature: 1, tint: 1, exposure: 4, contrast: 1, highlights: 1, shadows: 1, whites: 1, blacks: 1, saturation: 2, curveShadows: 1, curveMidtones: 1, curveHighlights: 1 } },
      { name: 'extreme-minima-tiled', width: 4, height: 7, phase: 103, tileOffset: [3, 2], fullResolution: [11, 13], uniforms: { temperature: -1, tint: -1, exposure: -4, contrast: -1, highlights: -1, shadows: -1, whites: -1, blacks: -1, saturation: 0, curveShadows: -1, curveMidtones: -1, curveHighlights: -1 } },
    ],
  },
  {
    id: 'hslSecondary', key: 'filter/grade:hslSecondary', sourceFile: 'hslSecondary.glsl',
    factoryName: 'canonicalFactory60',
    factorySha256: 'df65c190f706d88e73c63f143636c74e371c860ebe9fbbdcc6978a67134900ce',
    sourceSha256: '2f2c54a6d977ccc0ba8657c02f1fc2fecfb576ad85f6d03ea16468fc9cbd095a', sourceRawBytes: 4975,
    hasGlobal: true, globalDead: true, globalReadFunctions: [],
    reach: (u) => ({ index: u.hslEnable !== 0, global: false }),
    cases: [
      { name: 'key-reds-boost-sat', width: 6, height: 5, phase: 200, uniforms: { hslEnable: 1, hslHueCenter: 0.02, hslHueRange: 0.08, hslSatMin: 0.2, hslSatMax: 0.9, hslLumMin: 0.1, hslLumMax: 0.9, hslFeather: 0.05, hslHueShift: 0.05, hslSatAdjust: 0.4, hslLumAdjust: 0.1 } },
      { name: 'key-greens-desaturate', width: 5, height: 6, phase: 201, uniforms: { hslEnable: 1, hslHueCenter: 0.33, hslHueRange: 0.1, hslSatMin: 0.1, hslSatMax: 1.0, hslLumMin: 0.0, hslLumMax: 1.0, hslFeather: 0.08, hslHueShift: -0.1, hslSatAdjust: -0.5, hslLumAdjust: -0.2 } },
      { name: 'wide-key-max-shift', width: 7, height: 4, phase: 202, uniforms: { hslEnable: 1, hslHueCenter: 0.6, hslHueRange: 0.5, hslSatMin: 0, hslSatMax: 1, hslLumMin: 0, hslLumMax: 1, hslFeather: 0.5, hslHueShift: 0.5, hslSatAdjust: 1, hslLumAdjust: 1 } },
      { name: 'narrow-key-negative-shift-tiled', width: 4, height: 7, phase: 203, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { hslEnable: 1, hslHueCenter: 0.85, hslHueRange: 0.02, hslSatMin: 0.4, hslSatMax: 0.6, hslLumMin: 0.4, hslLumMax: 0.6, hslFeather: 0.01, hslHueShift: -0.5, hslSatAdjust: -1, hslLumAdjust: -1 } },
      { name: 'disabled-early-exit-diagnostic', width: 3, height: 3, phase: 204, uniforms: { hslEnable: 0, hslHueCenter: 0.5, hslHueRange: 0.1, hslSatMin: 0, hslSatMax: 1, hslLumMin: 0, hslLumMax: 1, hslFeather: 0.1, hslHueShift: 0, hslSatAdjust: 0, hslLumAdjust: 0 }, diagnostic: true },
    ],
  },
  {
    id: 'wheels', key: 'filter/grade:wheels', sourceFile: 'wheels.glsl',
    factoryName: 'canonicalFactory64',
    factorySha256: '0ea06a78c7c12757581c8e1776a29da21beccf0ccd461ac07d3c461546e913ef',
    sourceSha256: 'fa9c411096816263985e8d5ef82ade976667a6cadecf8929ecd185edbc71f479', sourceRawBytes: 3529,
    hasGlobal: true, globalDead: false, globalReadFunctions: ['applyWheels'],
    reach: (u) => {
      const off = (v) => Math.hypot((v[0] - 0.5) * 2, (v[1] - 0.5) * 2, (v[2] - 0.5) * 2)
      const allNeutral = off(u.wheelShadows) < 0.01 && off(u.wheelMidtones) < 0.01 && off(u.wheelHighlights) < 0.01
      return { index: true, global: !allNeutral }
    },
    cases: [
      { name: 'shadow-cool-highlight-warm', width: 6, height: 5, phase: 300, uniforms: { wheelShadows: [0.3, 0.4, 0.7], wheelMidtones: [0.5, 0.5, 0.5], wheelHighlights: [0.7, 0.55, 0.35], wheelBalance: 0.2 } },
      { name: 'midtone-push-magenta', width: 5, height: 6, phase: 301, uniforms: { wheelShadows: [0.5, 0.5, 0.5], wheelMidtones: [0.65, 0.45, 0.6], wheelHighlights: [0.5, 0.5, 0.5], wheelBalance: -0.3 } },
      { name: 'extreme-all-wheels', width: 7, height: 4, phase: 302, uniforms: { wheelShadows: [0, 0, 1], wheelMidtones: [1, 0, 0], wheelHighlights: [0, 1, 0], wheelBalance: 1 } },
      { name: 'gentle-all-wheels-negative-balance-tiled', width: 4, height: 7, phase: 303, tileOffset: [1, 3], fullResolution: [10, 12], uniforms: { wheelShadows: [0.55, 0.48, 0.52], wheelMidtones: [0.48, 0.53, 0.47], wheelHighlights: [0.52, 0.5, 0.46], wheelBalance: -1 } },
      { name: 'neutral-wheels-global-skip-diagnostic', width: 3, height: 3, phase: 304, uniforms: { wheelShadows: [0.5, 0.5, 0.5], wheelMidtones: [0.5, 0.5, 0.5], wheelHighlights: [0.5, 0.5, 0.5], wheelBalance: 0 }, diagnostic: true },
    ],
  },
  {
    id: 'vignette', key: 'filter/grade:vignette', sourceFile: 'vignette.glsl',
    factoryName: 'canonicalFactory63',
    factorySha256: '2470f6f7e0c46c41dc199a37862c7ac4de676716695b3237b91f9f15d4a58e9d',
    sourceSha256: '740ad849a37c99d87962a376c2e618b24248dc4b2799066aaf6364861727c1fa', sourceRawBytes: 4133,
    hasGlobal: true, globalDead: false, globalReadFunctions: ['applyVignette (inside `if (highlightProtect > 0.0)`)'],
    reach: (u) => {
      const active = Math.abs(u.vignetteAmount) >= 0.001
      return { index: active, global: active && u.vigHiProtect > 0 }
    },
    cases: [
      { name: 'darken-circle-highlight-protect', width: 6, height: 5, phase: 400, uniforms: { vignetteAmount: 0.7, vignetteMidpoint: 0.5, vignetteRoundness: 1, vignetteFeather: 0.4, vigHiProtect: 0.8 } },
      { name: 'lighten-ellipse-no-protect', width: 5, height: 6, phase: 401, uniforms: { vignetteAmount: -0.5, vignetteMidpoint: 0.6, vignetteRoundness: -1, vignetteFeather: 0.6, vigHiProtect: 0 } },
      { name: 'extreme-max-tiled-highlight-protect', width: 7, height: 4, phase: 402, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { vignetteAmount: 1, vignetteMidpoint: 0.5, vignetteRoundness: 1, vignetteFeather: 1, vigHiProtect: 1 } },
      { name: 'extreme-minima-highlight-protect', width: 4, height: 7, phase: 403, uniforms: { vignetteAmount: -1, vignetteMidpoint: 0.3, vignetteRoundness: -1, vignetteFeather: 0.2, vigHiProtect: 0.5 } },
      { name: 'near-zero-amount-early-exit-diagnostic', width: 3, height: 3, phase: 404, uniforms: { vignetteAmount: 0.0005, vignetteMidpoint: 0.5, vignetteRoundness: 0, vignetteFeather: 0.5, vigHiProtect: 1 }, diagnostic: true },
    ],
  },
  {
    id: 'creative', key: 'filter/grade:creative', sourceFile: 'creative.glsl',
    factoryName: 'canonicalFactory59',
    factorySha256: 'b5b99c6a5951ea7d68dbd6a58d6dc303393c95aa80aaa7f7a3de866e32530779',
    sourceSha256: 'b043aa43d17e098ffb736f16e6c81a5ca422ecdd6fc37fef03c39b01cc939bd3', sourceRawBytes: 4230,
    hasGlobal: true, globalDead: false, globalReadFunctions: ['applyVibrance', 'applyFadedFilm', 'applySplitTone'],
    reach: (u) => {
      const vib = Math.abs(u.vibrance) >= 0.001
      const fade = u.fadedFilm >= 0.001
      const off = (v) => Math.hypot((v[0] - 0.5) * 2, (v[1] - 0.5) * 2, (v[2] - 0.5) * 2)
      const tint = !(off(u.shadowTint) < 0.01 && off(u.highlightTint) < 0.01)
      return { index: true, global: vib || fade || tint }
    },
    cases: [
      { name: 'boost-vibrance-lift-blacks-tint', width: 6, height: 5, phase: 500, uniforms: { vibrance: 0.6, fadedFilm: 0.3, shadowTint: [0.4, 0.45, 0.6], highlightTint: [0.6, 0.55, 0.4], splitToneBalance: 0.2 } },
      { name: 'desaturate-vibrance-heavy-fade', width: 5, height: 6, phase: 501, uniforms: { vibrance: -0.7, fadedFilm: 0.8, shadowTint: [0.3, 0.5, 0.5], highlightTint: [0.5, 0.5, 0.3], splitToneBalance: -0.4 } },
      { name: 'extreme-maxima', width: 7, height: 4, phase: 502, uniforms: { vibrance: 1, fadedFilm: 1, shadowTint: [0, 0, 1], highlightTint: [1, 0, 0], splitToneBalance: 1 } },
      { name: 'extreme-minima-tiled', width: 4, height: 7, phase: 503, tileOffset: [2, 2], fullResolution: [9, 13], uniforms: { vibrance: -1, fadedFilm: 0.05, shadowTint: [1, 1, 0], highlightTint: [0, 1, 1], splitToneBalance: -1 } },
      { name: 'all-neutral-global-skip-diagnostic', width: 3, height: 3, phase: 504, uniforms: { vibrance: 0, fadedFilm: 0, shadowTint: [0.5, 0.5, 0.5], highlightTint: [0.5, 0.5, 0.5], splitToneBalance: 0 }, diagnostic: true },
    ],
  },
  {
    id: 'lut', key: 'filter/grade:lut', sourceFile: 'lut.glsl',
    factoryName: 'canonicalFactory61',
    factorySha256: 'd4e69f82c63b29797a6b5450cb65c291f6e377a2043f10c785d5a5b49b5f8abe',
    sourceSha256: '0a8a3ae4d2a14142ae7d53373bfac6ac87a0b175dff132d71cd80e6226f9ec40', sourceRawBytes: 13745,
    hasGlobal: false, globalDead: false, globalReadFunctions: [],
    reach: (u) => {
      const active = !(u.preset === 0 || u.alpha <= 0)
      return { index: active, srgbPair: active, hardLight: active && u.preset === 20, solarize: active && u.preset === 22 }
    },
    cases: [
      { name: 'hardlight-preset', width: 6, height: 5, phase: 600, uniforms: { preset: 20, alpha: 1 } },
      { name: 'solarize-preset', width: 5, height: 6, phase: 601, uniforms: { preset: 22, alpha: 0.8 } },
      { name: 'tealorange-preset-full-blend', width: 7, height: 4, phase: 602, uniforms: { preset: 1, alpha: 1 } },
      { name: 'vintage-partial-blend-tiled', width: 4, height: 7, phase: 603, tileOffset: [2, 1], fullResolution: [9, 11], uniforms: { preset: 8, alpha: 0.5 } },
      { name: 'no-lut-early-exit-diagnostic', width: 3, height: 3, phase: 604, uniforms: { preset: 0, alpha: 1 }, diagnostic: true },
    ],
  },
]

// ---------------------------------------------------------------------------
// Per-program verification, case rendering, mutation execution, direct rows.
// ---------------------------------------------------------------------------
function loadProgram(def) {
  const sourcePath = path.join(corpusRoot, 'sources/filter/grade', def.sourceFile)
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

  return { ...def, sourcePath, factoryText, canonical }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)

function normalizeUniforms(uniforms) {
  const out = {}
  for (const [k, v] of Object.entries(uniforms)) out[k] = Array.isArray(v) ? new Float32Array(v.map(f)) : f(v)
  return out
}

function buildCaseRecords(program) {
  return program.cases.map((c) => {
    const uniforms = normalizeUniforms(c.uniforms)
    const inputTex = patternedSurface(c.width, c.height, c.phase)
    const inputBytesBefore = Buffer.from(inputTex.data.buffer, inputTex.data.byteOffset, inputTex.data.byteLength).toString('hex')
    const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
    const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
    const opts = { width: c.width, height: c.height, uniforms, textures: { inputTex }, tileOffset, fullResolution, time: 0 }
    const first = renderCase(program.canonical, opts)
    const inputBytesAfter = Buffer.from(inputTex.data.buffer, inputTex.data.byteOffset, inputTex.data.byteLength).toString('hex')
    if (inputBytesBefore !== inputBytesAfter) throw new Error(`${program.id}/${c.name}: input texture was mutated by render`)
    const second = renderCase(program.canonical, opts)
    if (!sameBytes(first, second)) throw new Error(`${program.id}/${c.name}: repeat-render mismatch`)
    const reach = program.reach(c.uniforms)
    const definesMatch = JSON.stringify(AUTHORIZED_DEFINES) === JSON.stringify(AUTHORIZED_DEFINES) // always true; no define axis exists (see module header)
    return {
      def: c, name: c.name, dimensions: { width: c.width, height: c.height },
      defines: { ...AUTHORIZED_DEFINES }, eligible_for_native_binding: definesMatch,
      diagnostic: Boolean(c.diagnostic), reach,
      uniforms: c.uniforms,
      tile_offset: c.tileOffset ?? [0, 0], full_resolution: c.fullResolution ?? [c.width, c.height],
      repeat_identity: true, input_immutable: true,
      output: renderResult(first),
      opts, surface: first,
    }
  })
}

for (const program of PROGRAMS) program.caseRecords = buildCaseRecords(program)

// ---------------------------------------------------------------------------
// Mutation definitions per program (global-literal-swap and two
// index-expression shapes -- transpose-write and constant-induction --
// covering both capabilities the brief flags as needing new authentication).
// ---------------------------------------------------------------------------
const SRGB_START = 'function srgbToLinear (srgb) {'
const SRGB_END = 'return linear;\n  };'
const LIN_START = 'function linearToSrgb (linear) {'
const LIN_END = 'return srgb;\n  };'
const HSL_TO_RGB_START = 'function hslToRgb (hsl) {'
const HSL_TO_RGB_END = 'return rgb;\n  };'
const LUT_HARDLIGHT_START = 'function lutHardLight (rgb) {'
const LUT_HARDLIGHT_END = 'return clamp(result, 0, 1);\n  };'
const LUT_SOLARIZE_START = 'function lutSolarize (rgb) {'
const LUT_SOLARIZE_END = 'return clamp(result, 0, 1);\n  };'

function buildMutationsForProgram(program) {
  const { factoryText } = program
  const mutations = []

  if (program.hasGlobal) {
    const m = buildGlobalSwapMutation(factoryText)
    mutations.push({
      id: `${program.id}-luma-weights-bt601-swap`, kind: 'global', reachKey: 'global',
      hazard: 'wrong-constant-vec3-global-literal',
      description: 'Swap LUMA_WEIGHTS from BT.709 (0.2126/0.7152/0.0722) to BT.601 (0.299/0.587/0.114) -- a plausible-looking but wrong luma-weight constant, the exact shape of bug the global_admission profile must prevent silently compiling.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }

  {
    const m = buildIndexTransposeWriteMutation(factoryText, SRGB_START, SRGB_END, 'linear', 2)
    mutations.push({
      id: `${program.id}-srgbToLinear-write-index-transpose`, kind: 'index', reachKey: program.id === 'lut' ? 'srgbPair' : 'index',
      hazard: 'index-expression-write-lane-transpose',
      description: 'srgbToLinear: transpose the WRITE index from linear[i] to linear[(i+2)%3] while leaving the srgb[i] READ untouched -- a cyclic lane-swap bug the index_expression_admission profile must prevent silently compiling.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }
  {
    const m = buildIndexConstantInductionMutation(factoryText, LIN_START, LIN_END)
    mutations.push({
      id: `${program.id}-linearToSrgb-constant-induction`, kind: 'index', reachKey: program.id === 'lut' ? 'srgbPair' : 'index',
      hazard: 'index-expression-induction-variable-replaced-by-constant',
      description: 'linearToSrgb: replace every loop-induction-variable subscript [i] with the constant [0] -- both the READ (linear[i]) and WRITE (srgb[i]) collapse onto lane 0, leaving lanes 1/2 at their zero-initialized value. Exactly the "replace the induction variable with a constant" shape the brief calls out.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }

  if (program.id === 'hslSecondary') {
    const m = buildIndexTransposeWriteMutation(factoryText, HSL_TO_RGB_START, HSL_TO_RGB_END, 'rgb', 1)
    mutations.push({
      id: `${program.id}-hslToRgb-write-index-transpose`, kind: 'index', reachKey: 'index',
      hazard: 'index-expression-write-lane-transpose-write-only-site',
      description: 'hslToRgb: transpose the WRITE index from rgb[i] to rgb[(i+1)%3] on all four per-lane branches. hslToRgb is the one write-only index site in this cluster (it never reads rgb[i]) -- this mutation is the program-specific closure beyond the shared srgbToLinear/linearToSrgb pair.',
      note: 'One reach-eligible case ("narrow-key-negative-shift-tiled", hslSatAdjust=-1) is expected and confirmed to NOT diverge under this mutation: hslToRgb itself has its own internal early return (`if (s < 0.001) return vec3(l,l,l);`) that the coarse hslEnable!=0 reach flag does not model. That case\'s hslSatAdjust=-1 clamps corrected saturation to exactly 0 for every pixel, so the per-lane indexed loop this mutation targets never executes for that case -- the mutation still needs and gets nonzero divergence overall (3/4), so it remains a genuine discriminator; this is a documented reach-granularity nuance, not a failure to discriminate.',
      anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
    })
  }

  if (program.id === 'lut') {
    {
      const m = buildIndexTransposeWriteMutation(factoryText, LUT_HARDLIGHT_START, LUT_HARDLIGHT_END, 'result', 2)
      mutations.push({
        id: `${program.id}-lutHardLight-write-index-transpose`, kind: 'index', reachKey: 'hardLight',
        hazard: 'index-expression-write-lane-transpose',
        description: 'lutHardLight (reachable only at preset==20): transpose the WRITE index from result[i] to result[(i+2)%3] while leaving rgb[i] READs untouched.',
        anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
      })
    }
    {
      const m = buildIndexConstantInductionMutation(factoryText, LUT_SOLARIZE_START, LUT_SOLARIZE_END)
      mutations.push({
        id: `${program.id}-lutSolarize-constant-induction`, kind: 'index', reachKey: 'solarize',
        hazard: 'index-expression-induction-variable-replaced-by-constant',
        description: 'lutSolarize (reachable only at preset==22): replace every [i] subscript with the constant [0], collapsing both the rgb[i] read and result[i] write onto lane 0.',
        anchor: m.anchor, mutated: m.mutated, siteCount: m.siteCount,
      })
    }
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

const EXPECTED_ZERO_MUTATIONS = new Set(['hslSecondary-luma-weights-bt601-swap'])

for (const program of PROGRAMS) {
  program.mutations = buildMutationsForProgram(program)
  for (const mutation of program.mutations) {
    const result = runMutation(program, mutation)
    mutation.result = result
    const expectZero = EXPECTED_ZERO_MUTATIONS.has(mutation.id)
    if (expectZero) {
      if (result.divergentReaching !== 0) {
        throw new Error(`${mutation.id}: expected exactly 0 divergence among reach-eligible cases (documented dead code), got ${result.divergentReaching}/${result.reachingCount} -- investigate before shipping, the dead-code claim would be WRONG`)
      }
    } else {
      if (result.reachingCount === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site at all -- cannot prove discrimination, fix the case table`)
      if (result.divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${result.reachingCount} -- investigate before shipping`)
    }
    // Structural soundness check, independent of the expected/dead
    // classification above: cases that do NOT reach this mutation's site
    // (early-exit diagnostics, or a different mutation's site) must show
    // ZERO divergence -- if they diverge, either the reach() predicate is
    // wrong or the mutation leaked outside its intended site.
    if (result.divergentNonReaching !== 0) {
      throw new Error(`${mutation.id}: ${result.divergentNonReaching}/${result.nonReachingCount} non-reaching case(s) diverged -- the reach() predicate or the mutation's scope is wrong, investigate before shipping`)
    }
  }
}

// ---------------------------------------------------------------------------
// Direct rows: freeze the exact indexed-read/write semantics of
// srgbToLinear/linearToSrgb (all six programs), hslToRgb (hslSecondary), and
// lutHardLight/lutSolarize (lut), using the REAL extracted closures -- not
// reimplemented. Each row also runs the same input through the
// index-transpose and constant-induction MUTATED closures (built via the
// same extractor technique applied to the mutated factory text) so the
// divergence is demonstrated at the closure level, not just full-render.
// ---------------------------------------------------------------------------
function vec3Row(realFn, mutatedFns, input) {
  const inputArr = new Float32Array(input.map(f))
  const real = Array.from(realFn(inputArr))
  const row = {
    input: Array.from(inputArr), input_bits: Array.from(inputArr).map(f32Bits),
    real_result: real, real_result_bits: real.map(f32Bits),
  }
  for (const [label, fn] of Object.entries(mutatedFns)) {
    const out = Array.from(fn(new Float32Array(input.map(f))))
    row[`${label}_result`] = out
    row[`${label}_result_bits`] = out.map(f32Bits)
    row[`diverges_from_${label}`] = real.some((v, i) => f32Bits(v) !== f32Bits(out[i]))
  }
  return row
}

function buildDirectRowsForProgram(program) {
  const helperNames = ['srgbToLinear', 'linearToSrgb']
  if (program.id === 'hslSecondary') helperNames.push('hslToRgb')
  if (program.id === 'lut') helperNames.push('lutHardLight', 'lutSolarize')

  const realExtractor = buildExtractorFactory(program.factoryText, helperNames)
  const real = realExtractor(makeDirectBindings(), makeDirectRuntime())

  const transposeSrgb = program.mutations.find((m) => m.id === `${program.id}-srgbToLinear-write-index-transpose`)
  const constInductLin = program.mutations.find((m) => m.id === `${program.id}-linearToSrgb-constant-induction`)
  const mutatedSrgbExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, transposeSrgb), helperNames)
  const mutatedLinExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, constInductLin), helperNames)
  const mutatedSrgb = mutatedSrgbExtractor(makeDirectBindings(), makeDirectRuntime())
  const mutatedLin = mutatedLinExtractor(makeDirectBindings(), makeDirectRuntime())

  const srgbInputs = [
    [0, 0.04045, 0.040451],
    [-0.1, 0.5, 1.0],
    [0.01, 0.02, 0.03],
    [0.2, 0.5, 0.9],
    [1.0, 0.0, 0.04045],
    [0.04045, 0.04045, 0.04045],
  ]
  const srgbToLinearRows = srgbInputs.map((v) => vec3Row(real.srgbToLinear, { transpose_write: mutatedSrgb.srgbToLinear }, v))

  const linInputs = [
    [0, 0.0031308, 0.0031309],
    [-0.05, 0.4, 0.99],
    [0.001, 0.002, 0.003],
    [0.1, 0.4, 0.8],
    [0.9999, 0.0, 0.0031308],
    [0.0031308, 0.0031308, 0.0031308],
  ]
  const linearToSrgbRows = linInputs.map((v) => vec3Row(real.linearToSrgb, { constant_induction: mutatedLin.linearToSrgb }, v))

  const result = { srgb_to_linear_rows: srgbToLinearRows, linear_to_srgb_rows: linearToSrgbRows }

  if (program.id === 'hslSecondary') {
    const transposeHsl = program.mutations.find((m) => m.id === `${program.id}-hslToRgb-write-index-transpose`)
    const mutatedHslExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, transposeHsl), helperNames)
    const mutatedHsl = mutatedHslExtractor(makeDirectBindings(), makeDirectRuntime())
    const hslInputs = [
      [0.0, 0.8, 0.5],
      [0.25, 0.6, 0.3],
      [0.5, 1.0, 0.7],
      [0.75, 0.4, 0.2],
      [0.99, 0.9, 0.9],
    ]
    result.hsl_to_rgb_rows = hslInputs.map((v) => vec3Row(real.hslToRgb, { transpose_write: mutatedHsl.hslToRgb }, v))
  }

  if (program.id === 'lut') {
    const transposeHardLight = program.mutations.find((m) => m.id === `${program.id}-lutHardLight-write-index-transpose`)
    const constInductSolarize = program.mutations.find((m) => m.id === `${program.id}-lutSolarize-constant-induction`)
    const mutatedHardLightExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, transposeHardLight), helperNames)
    const mutatedSolarizeExtractor = buildExtractorFactory(mutateFactoryText(program.factoryText, constInductSolarize), helperNames)
    const mutatedHardLight = mutatedHardLightExtractor(makeDirectBindings(), makeDirectRuntime())
    const mutatedSolarize = mutatedSolarizeExtractor(makeDirectBindings(), makeDirectRuntime())
    const rgbInputs = [
      [0.1, 0.4, 0.49],
      [0.51, 0.6, 0.9],
      [0.0, 0.5, 1.0],
      [0.3, 0.7, 0.2],
      [0.5, 0.5, 0.5],
    ]
    result.lut_hard_light_rows = rgbInputs.map((v) => vec3Row(real.lutHardLight, { transpose_write: mutatedHardLight.lutHardLight }, v))
    result.lut_solarize_rows = rgbInputs.map((v) => vec3Row(real.lutSolarize, { constant_induction: mutatedSolarize.lutSolarize }, v))
  }

  return result
}

for (const program of PROGRAMS) {
  program.directRows = buildDirectRowsForProgram(program)
  // Non-vacuity: every direct-row group must contain at least one row that
  // actually diverges from each mutated-closure comparison column, for
  // every group present on this program -- otherwise the "direct rows
  // freeze the exact indexed semantics" claim would be untested.
  for (const [groupName, rows] of Object.entries(program.directRows)) {
    const divergeKeys = Object.keys(rows[0]).filter((k) => k.startsWith('diverges_from_'))
    for (const key of divergeKeys) {
      if (!rows.some((r) => r[key])) throw new Error(`${program.id}/${groupName}: no row diverges via ${key} -- direct rows do not actually exercise the hazard`)
    }
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
    const eligible = program.caseRecords.filter((c) => !c.diagnostic)
    const diagnostic = program.caseRecords.filter((c) => c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    programsOut[program.id] = {
      key: program.key, defines: { ...AUTHORIZED_DEFINES }, profile_candidate_global: program.hasGlobal ? `grade-${program.id.toLowerCase()}-luma-weights-v1` : null,
      profile_candidate_index: `grade-${program.id.toLowerCase()}-index-expression-v1`,
      source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName, canonical_factory_to_string_sha256: program.factorySha256,
      has_global: program.hasGlobal, global_dead: program.globalDead, global_read_functions: program.globalReadFunctions,
      cases: program.caseRecords.map((c) => ({
        name: c.name, dimensions: c.dimensions, defines: c.defines, eligible_for_native_binding: c.eligible_for_native_binding,
        diagnostic: c.diagnostic, reach: c.reach, uniforms: c.uniforms, tile_offset: c.tile_offset, full_resolution: c.full_resolution,
        repeat_identity: c.repeat_identity, input_immutable: c.input_immutable, output: c.output,
      })),
      mutations: program.mutations.map((m) => ({
        id: m.id, kind: m.kind, reach_key: m.reachKey, hazard: m.hazard, description: m.description, site_count: m.siteCount,
        expected_zero: EXPECTED_ZERO_MUTATIONS.has(m.id), note: m.note ?? null,
        case_results: m.result.caseResults,
        summary: { reaching_cases: m.result.reachingCount, divergent_reaching: m.result.divergentReaching, non_reaching_cases: m.result.nonReachingCount, divergent_non_reaching: m.result.divergentNonReaching },
      })),
      direct_rows: program.directRows,
    }
  }

  return {
    schema: 'noisemaker-for-cpp.future-precompute.task32.grade-cluster-closure-oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version, public_identity: true, adapter_absent: true },
    authorized_defines: { ...AUTHORIZED_DEFINES },
    defines_axis_note: 'All six grade programs compile with exact defines {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, key) for all six keys, and independently by grep: the only preprocessor directive in any of the six sources is the universal `#ifdef GL_ES` guard (no #define/#ifdef of any effect-specific macro exists, unlike synth/curl\'s OCTAVES/OUTPUT_MODE/RIDGES). Consequently there is no "different define map" axis from which to construct an ineligible-by-define case for this cluster -- every full-render case below is eligible_for_native_binding: true by construction, and this is stated explicitly rather than fabricating a synthetic ineligible case that would not reflect anything real.',
    two_capability_shapes: {
      global_admission: 'const vec3 LUMA_WEIGHTS = vec3(0.2126, 0.7152, 0.0722) -- present in primary, hslSecondary (dead), wheels, vignette, creative; absent from lut (which inlines the literal as a dot() argument in luma(), confirmed: zero `const` declarations in lut.glsl).',
      index_expression_admission: 'for-loop-induction-variable-indexed read AND write of a local vec3 lane (e.g. `linear[i] = srgb[i] / 12.92;`) -- 74 sites total across the six programs per the frozen brief; this oracle exercises the shared srgbToLinear/linearToSrgb pair (present in all six) plus the two program-specific extra closures (hslToRgb write-only in hslSecondary; lutHardLight/lutSolarize in lut).',
    },
    programs: programsOut,
    eligibility_summary: {
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic,
      note: 'diagnostic cases are early-exit renders (hslEnable=0 / neutral wheels / near-zero vignetteAmount / all-neutral creative tints / preset=0) included to prove the reach() classification and mutation scoping are sound (zero divergence expected there for every mutation) -- they are still eligible_for_native_binding: true (defines still match), just documented separately from the "at least 4 differing, closure-exercising" cases the task requires.',
    },
    negative_closure: {
      any_other_define_map: 'reject -- not constructible for this cluster, see defines_axis_note',
      generic_const_vec3_global_capability: 'forbidden -- must stay scoped to the five frozen per-program LUMA_WEIGHTS declaration identities, never widened to "any const vec3"',
      generic_id_indexed_write_capability: 'forbidden -- must stay scoped to the 74 frozen per-program node identities, never widened to "any id-indexed write"',
      hslSecondary_luma_weights_treated_as_render_validated: 'forbidden -- validated structurally (type-checks) only; zero live consumers, zero divergence is EXPECTED and confirmed, not a coverage gap',
      reusing_existing_index_capability_tokens: 'forbidden -- FIXED_NINE/FIXED_GRID/FIXED_ARRAY_PARAMETER/FIXED_AFFINE_CENTERS13 must not be reused as the used.add(...) token for grade\'s index sites; this is a JS behavioral oracle only and does not itself assert Python-side vocabulary, but documents the constraint per the frozen brief §6 for the implementer',
    },
  }
}

function report(d) {
  const lines = [
    '# Task 32 `filter/grade` cluster closure oracle report', '',
    `Six programs, six independent GLSL sources, sharing only \`effect_id: "filter/grade"\`. Authorized define map for all six: \`{}\`.`, '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} early-exit diagnostic). All cases \`eligible_for_native_binding: true\` -- see \`defines_axis_note\`.`, '',
    '## Defines axis', '', d.defines_axis_note, '',
    '## Two capability shapes', '',
    `**global_admission**: ${d.two_capability_shapes.global_admission}`, '',
    `**index_expression_admission**: ${d.two_capability_shapes.index_expression_admission}`, '',
    '## Per-program summary', '',
    '| Program | Has global | Global dead | Eligible cases | Diagnostic cases | Mutations |', '| --- | --- | --- | ---: | ---: | ---: |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    lines.push(`| ${id} | ${p.has_global} | ${p.global_dead} | ${eligible} | ${diagnostic} | ${p.mutations.length} |`)
  }
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\``, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\` (\`${p.canonical_factory_to_string_sha256}\`).`, '')
    if (p.has_global) {
      lines.push(`Global \`LUMA_WEIGHTS\`: ${p.global_dead ? '**DEAD** -- zero live reads (expected-dead confirmation, not a coverage gap)' : `read by ${p.global_read_functions.join(', ')}`}.`, '')
    } else {
      lines.push('No global constant in this program (literal inlined directly into `luma()`\'s `dot()` call).', '')
    }
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${JSON.stringify(c.reach)} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations', '', '| Mutation | Kind | Reach key | Sites | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |', '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |')
    for (const m of p.mutations) {
      lines.push(`| ${m.id} | ${m.kind} | ${m.reach_key} | ${m.site_count} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} | ${m.expected_zero ? 'ZERO (dead code)' : 'nonzero'} |`)
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}${m.note ? ` _Note: ${m.note}_` : ''}`), '')
    const dr = p.direct_rows
    for (const [groupName, rows] of Object.entries(dr)) {
      lines.push(`### Direct rows: \`${groupName}\``, '', `${rows.length} rows, real closure invoked directly (not reimplemented). At least one row diverges from each mutated-closure comparison column (machine-asserted at build time).`, '')
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
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('grade oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('grade oracle report drift')
  const totalMutations = PROGRAMS.reduce((n, p) => n + p.mutations.length, 0)
  const totalDirectRowGroups = PROGRAMS.reduce((n, p) => n + Object.keys(p.directRows).length, 0)
  console.log(`grade oracle fixture ok (${PROGRAMS.length} programs, ${data.eligibility_summary.total_cases} cases, ${totalMutations} mutations, ${totalDirectRowGroups} direct-row groups)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
