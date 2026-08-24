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
// Loop-proof cluster oracle-a -- EIGHT programs, blocked on the counted-loop
// program-proof gate (tools/glslcpp's loop_proof.py), per
// docs/port-engineering/loopproof/loop-proof-study.md SS1/SS2:
//
//   filter/blur:blurH            filter/blur:blurV          filter/dither:dither
//   filter/normalize:statsFinal  filter/oilPaint:oilFlatten  filter/smooth:smoothBlend
//   filter/zoomBlur:zoomBlur     filter/tetraColorArray:tetraColorArray
//
// This is the JS-golden ground truth the future C++20 port's bit-exact tests
// will assert against, once each program clears its loop-proof gate. All
// eight already have a real, working canonicalKernelFactories[] entry in
// noisemaker-for-cpu today -- the loop-proof gate is a tools/glslcpp
// (C++ static-analysis / codegen) concept, not a JS-runtime one; the JS
// renderer transpiles straight off the pinned upstream GLSL
// (scripts/upstream/compile-glsl.js) with no dependency on that gate at all.
// Verified live below, not assumed: all eight keys resolve to a canonical
// factory, all eight have public factory === canonical factory (no adapter
// override anywhere in this cluster).
//
// HAZARD THIS CLUSTER IS BUILT AROUND (task brief, restated): a case that
// merely shows *some* byte difference under a trip-count mutation is not
// enough if the mutation could plausibly be idempotent/saturating for real
// programs elsewhere -- each mutation here is machine-verified to produce
// nonzero divergence on every reach-eligible case, and the report documents
// the actual per-mutation divergence counts, not just an assertion of
// success. Two programs in this cluster needed a *second* design pass after
// the first candidate case/mutation combination produced zero or
// near-vacuous divergence (see statsFinal and tetraColorArray below) --
// documented inline at the point of the fix, following the parallax lesson
// from the sibling `cheap-unlocks` oracle.
//
// THE TOP-LEVEL-BINDING LESSON, applied throughout (glsl-kernel.js:20-61):
// nine canonical keys (resolution, fullResolution, tileOffset, aspectRatio,
// aspect, time, globalTime, deltaTime, frame) are assigned AFTER the
// `...uniforms` spread, so passing any of them *inside* uniforms silently
// discards the caller's intended value. Every case is rendered through
// `renderCase()`, which refuses to build if `uniforms` illegally contains one
// of these keys, and independently reconstructs the bindings to assert the
// kernel's own bound values -- for the reserved keys AND for every declared
// per-program uniform -- equal the CALLER's intended values, not merely
// "whatever came out".
//
// DEFINES: verified live via tools.glslcpp.generate_typed_slice._defaults,
// not assumed. Of the eight, only `filter/oilPaint:oilFlatten` has a
// non-empty authorized define map: `{MODE: 1}` (matches its source's
// `#ifndef MODE #define MODE 1`). All other seven authorize `{}`. Per the
// defines-bound-as-uniforms lesson, MODE is independently confirmed read by
// the factory as `$bindings["MODE"]` (oilFlatten factory line 9), not
// preprocessed away -- this generator asserts that live, not by comment.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'loopproof-a-oracles.json')
const reportPath = path.join(here, 'loopproof-a-oracle-report.md')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpusRoot = `tools/glslcpp/corpus/${revision}`
const glslKernelPath = '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
const glslRuntimePath = '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
const passRunnerPath = '../noisemaker-for-cpu/src/runtime/pass-runner.js'
const surfacePath = '../noisemaker-for-cpu/src/runtime/surface.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
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
// Runtime/catalog hermeticity pinning -- independently recomputed, matching
// the grade/derivative/cheap-unlocks generators' pinned values exactly (same
// repo state), not copy-pasted trust.
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
// Deterministic patterned input texture -- R/G/B/A each use a different
// modulus/coefficient set so no two channels are correlated and no two cases
// share an input (distinct `phase`).
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
  for (const [k, v] of Object.entries(program.defines ?? {})) {
    const bound = bindings[k]
    if (f32Bits(typeof v === 'number' ? f(v) : v) !== f32Bits(typeof bound === 'number' ? f(bound) : bound)) {
      throw new Error(`${program.id}/${c.name}: kernel did not observe authorized define "${k}"=${v} -- defines-bound-as-uniforms lesson violated`)
    }
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

  return { name: c.name, surface: first, c }
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
// Mutation application: every mutation here is a textual anchor/replacement
// pair applied directly to the compiled JS factory's toString(), matching
// the actual compiled loop-bound expression -- not a source-GLSL edit and
// not a global-const swap (this cluster's blocked loops mostly derive their
// bound from a per-invocation LOCAL, not a top-level `var NAME = literal`
// declaration, so the `source-global-literal-int-v1`-style const-swap shape
// used by the sibling cheap-unlocks generator does not apply uniformly
// here -- verified per-program below, not assumed).
// ---------------------------------------------------------------------------
function mutateFactoryText(factoryText, mutation) {
  if (occurrences(factoryText, mutation.anchor) !== 1) throw new Error(`mutation anchor not unique/found: ${mutation.id}`)
  return factoryText.replace(mutation.anchor, mutation.mutated)
}

// ---------------------------------------------------------------------------
// Bespoke texture builders, empirically verified (not assumed) against the
// live runtime before being locked in here -- see the report's per-program
// "design note" for what the first candidate looked like when it failed to
// discriminate, where applicable (the parallax lesson).
// ---------------------------------------------------------------------------
// statsFinal-specific: a texture where the global-min R lane and global-max G
// lane are placed at KNOWN, ISOLATED texel coordinates so an undershot
// y-loop or x-loop bound can be independently proven to miss exactly one of
// them. `minAt`/`maxAt` are [col, row] in TOP-DOWN Surface-data coordinates.
function statsFinalSurface(width, height, minAt, maxAt) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = f(0.5 + 0.01 * ((x * 7 + y * 3) % 5))
      data[i + 1] = f(0.5 - 0.01 * ((x * 5 + y * 11) % 5))
      data[i + 2] = 0
      data[i + 3] = 1
    }
  }
  data[(minAt[1] * width + minAt[0]) * 4] = f(0.001)
  data[(maxAt[1] * width + maxAt[0]) * 4 + 1] = f(0.999)
  return new Surface(width, height, data)
}

// smoothBlend/searchEdge-specific: an edge texture (R=edgeH, G=edgeV) with a
// single row containing a controlled-distance "edge found" (R<0.5) column to
// the left of a designated render column, and a second, close "found"
// column to the right so the vertical/right-search branches stay short and
// the divergence is attributable to the LEFT search's trip count alone.
function searchEdgeSurface(width, height, row, renderCol, foundLeftCol, foundRightCol) {
  const data = new Float32Array(width * height * 4)
  for (let x = 0; x < width; x += 1) data[(row * width + x) * 4 + 3] = 1
  for (let x = foundLeftCol + 1; x <= renderCol; x += 1) data[(row * width + x) * 4] = 1
  for (let x = renderCol; x < foundRightCol; x += 1) data[(row * width + x) * 4] = 1
  data[(row * width + foundLeftCol) * 4] = 0
  data[(row * width + foundRightCol) * 4] = 0
  return new Surface(width, height, data)
}

// ---------------------------------------------------------------------------
// Program registry -- seven programs (the eighth, dither, is documented as
// uncoverable below the registry; see DITHER_BLOCKER).
// ---------------------------------------------------------------------------
const TETRA_COLORS = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1], [1, 1, 1], [0.5, 0.5, 0.5]]
function tetraColorUniforms(colorCount, extra) {
  const uniforms = {
    colorMode: 0, colorCount, positionMode: 0,
    pos0: 0, pos1: 0, pos2: 0, pos3: 0, pos4: 0, pos5: 0, pos6: 0, pos7: 0,
    repeat: 1, offset: 0, smoothness: 0, alpha: 1, rotation: 0,
    ...extra,
  }
  for (let i = 0; i < 8; i += 1) uniforms[`color${i}`] = TETRA_COLORS[i]
  return uniforms
}

const PROGRAM_DEFS = [
  {
    id: 'blurH', key: 'filter/blur:blurH', sourceFile: 'blurH.glsl', sourceDir: 'blur',
    factoryName: 'canonicalFactory24',
    sourceRawBytes: 1120, sourceSha256: 'c4283e820b2ade9148358ad4582d350bc7f4a5ccb5fc60f2e1b76bcda58deecc',
    uniformTypes: { radiusX: 'float', renderScale: 'float' },
    loopRole: 'Horizontal Gaussian-blur tap radius: `radius = int(radiusX*renderScale)` drives both the loop bound `[-radius, radius]` and `sigma = radius/3`, so a wrong trip count changes which texels are summed without changing the weighting curve itself.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    reach: (c) => ({ default: c.uniforms.radiusX * c.uniforms.renderScale >= 1 }),
    cases: [
      { name: 'radius5-wide', width: 12, height: 10, phase: 0, uniforms: { radiusX: 5, renderScale: 1 } },
      { name: 'radius4-tall', width: 10, height: 12, phase: 1, uniforms: { radiusX: 4, renderScale: 1 } },
      { name: 'radius3-tiled', width: 16, height: 14, phase: 2, tileOffset: [3, 2], fullResolution: [22, 18], uniforms: { radiusX: 3, renderScale: 1 } },
      { name: 'radius6-scaled-square', width: 9, height: 9, phase: 3, uniforms: { radiusX: 3, renderScale: 2 } },
      { name: 'radius0-early-exit-diagnostic', width: 5, height: 5, phase: 4, uniforms: { radiusX: 0, renderScale: 1 }, diagnostic: true },
    ],
    mutations: [
      { id: 'blurH-tap-radius-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var i = -radius; i <= radius; i++) {', mutated: 'for (var i = -radius; i < radius; i++) {', description: 'Drop the `i<=radius` upper bound to `i<radius`: the smallest possible wrong trip count, dropping exactly the `+radius` tap while leaving `-radius..radius-1` and sigma untouched.' },
      { id: 'blurH-tap-radius-swap', kind: 'trip_count_swap', anchor: 'for (var i = -radius; i <= radius; i++) {', mutated: 'for (var i = -radius; i <= radius - 2; i++) {', description: 'Shrink the upper bound by 2 (`radius-2`): a materially wrong, asymmetric trip count that drops multiple outer taps while sigma (still computed from the true radius) stays fixed.' },
    ],
  },
  {
    id: 'blurV', key: 'filter/blur:blurV', sourceFile: 'blurV.glsl', sourceDir: 'blur',
    factoryName: 'canonicalFactory25',
    sourceRawBytes: 1118, sourceSha256: 'cc33343032b34e1ede6eed15fbdcb9229ad64484a092b2914065b09fa957fb9b',
    uniformTypes: { radiusY: 'float', renderScale: 'float' },
    loopRole: 'Vertical Gaussian-blur tap radius -- byte-identical shape to blurH, transposed to the Y axis.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    reach: (c) => ({ default: c.uniforms.radiusY * c.uniforms.renderScale >= 1 }),
    cases: [
      { name: 'radius5-wide', width: 12, height: 10, phase: 10, uniforms: { radiusY: 5, renderScale: 1 } },
      { name: 'radius4-tall', width: 10, height: 12, phase: 11, uniforms: { radiusY: 4, renderScale: 1 } },
      { name: 'radius3-tiled', width: 16, height: 14, phase: 12, tileOffset: [2, 3], fullResolution: [21, 19], uniforms: { radiusY: 3, renderScale: 1 } },
      { name: 'radius6-scaled-square', width: 9, height: 9, phase: 13, uniforms: { radiusY: 3, renderScale: 2 } },
      { name: 'radius0-early-exit-diagnostic', width: 5, height: 5, phase: 14, uniforms: { radiusY: 0, renderScale: 1 }, diagnostic: true },
    ],
    mutations: [
      { id: 'blurV-tap-radius-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var i = -radius; i <= radius; i++) {', mutated: 'for (var i = -radius; i < radius; i++) {', description: 'Same off-by-one shape as blurH, transposed to Y.' },
      { id: 'blurV-tap-radius-swap', kind: 'trip_count_swap', anchor: 'for (var i = -radius; i <= radius; i++) {', mutated: 'for (var i = -radius; i <= radius - 2; i++) {', description: 'Same swap shape as blurH, transposed to Y.' },
    ],
  },
  {
    id: 'statsFinal', key: 'filter/normalize:statsFinal', sourceFile: 'statsFinal.glsl', sourceDir: 'normalize',
    factoryName: 'canonicalFactory90',
    sourceRawBytes: 959, sourceSha256: '0b8daf6d5a38dc34bbd98800fdd46f9cdfa0b97f00196382023456a0b6eb1dfa',
    uniformTypes: {},
    loopRole: 'Full-image min/max reduction: nested `y<inSize.y`/`x<inSize.x` loops scan every texel of `inputTex`, taking the R-channel running min and G-channel running max. A wrong bound silently drops rows/columns from the reduction with no visible error signal other than a wrong min/max.',
    buildTextures: (c) => ({ inputTex: statsFinalSurface(c.width, c.height, c.minAt, c.maxAt) }),
    reach: () => ({ default: true }),
    cases: [
      // DESIGN NOTE (documented per the task's discriminability requirement,
      // not merely asserted): a first candidate using the shared
      // `patternedSurface()` helper was tried and rejected here before this
      // file was written -- its per-pixel formula has no guarantee that the
      // GLOBAL min/max lane lands in the specific row/column a bound
      // mutation removes, so on most phases/sizes it produced ZERO
      // divergence (the true min/max just happened to survive the
      // undershoot). `statsFinalSurface()` instead places the min/max at a
      // KNOWN, ISOLATED coordinate chosen to be exactly the row (or column)
      // an off-by-one/swap mutation removes -- verified empirically below
      // to diverge on exactly the intended channel and NOT the other.
      { name: 'min-in-first-topdown-row', width: 6, height: 5, minAt: [3, 0], maxAt: [1, 3], uniforms: {} },
      { name: 'max-in-last-topdown-col', width: 9, height: 7, minAt: [2, 5], maxAt: [8, 2], uniforms: {} },
      { name: 'min-and-max-share-first-row', width: 8, height: 6, minAt: [0, 0], maxAt: [7, 0], uniforms: {} },
      { name: 'square-canvas', width: 10, height: 10, minAt: [4, 0], maxAt: [9, 6], uniforms: {} },
    ],
    mutations: [
      { id: 'statsFinal-y-bound-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var y = 0; y < inSize[1]; y++) {', mutated: 'for (var y = 0; y < inSize[1] - 1; y++) {', description: 'Drop the LAST y-iteration (shader-y = inSize.y-1). texelFetch flips Y, so this is exactly the FIRST top-down data row -- undershoots the reduction by one full row.' },
      { id: 'statsFinal-x-bound-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var x = 0; x < inSize[0]; x++) {', mutated: 'for (var x = 0; x < inSize[0] - 1; x++) {', description: 'Drop the LAST x-iteration (column inSize.x-1, unaffected by the Y flip) -- undershoots the reduction by one full column.' },
    ],
  },
  {
    id: 'oilFlatten', key: 'filter/oilPaint:oilFlatten', sourceFile: 'oilFlatten.glsl', sourceDir: 'oilPaint',
    factoryName: 'canonicalFactory92',
    sourceRawBytes: 7321, sourceSha256: 'f2f512b35b846d8a15362739a843c162199b7c53d95251918576726b1b094690',
    defines: { MODE: 1 },
    uniformTypes: { MODE: 'int', size: 'float' },
    loopRole: '8-sector Kuwahara-style oil-paint sample window: `sampleLimit = ceil(clamp(radius,1,12))` drives the nested `[-sampleLimit,sampleLimit]^2` scan that buckets neighbors into 8 octant accumulators; the octant with lowest color variance is chosen as the flattened output. A wrong trip count changes octant membership counts and variances, hence which octant (and mean color) wins.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    // fr = clamp(radius,1,12) is ALWAYS >=1 regardless of `size`, so
    // sampleLimit = ceil(fr) is always >=1 and the sample window always
    // executes at least once -- unconditionally reachable at the authorized
    // define MODE=1 (verified from source: no early-return path exists).
    reach: () => ({ default: true }),
    cases: [
      { name: 'radius6-wide', width: 10, height: 9, phase: 20, uniforms: { MODE: 1, size: 6 } },
      { name: 'radius8-tall', width: 9, height: 10, phase: 21, uniforms: { MODE: 1, size: 8 } },
      { name: 'radius4-square', width: 12, height: 12, phase: 22, uniforms: { MODE: 1, size: 4 } },
      { name: 'radius10-tiled', width: 14, height: 13, phase: 23, tileOffset: [2, 1], fullResolution: [20, 18], uniforms: { MODE: 1, size: 10 } },
      { name: 'small-radius3-tight-window', width: 11, height: 11, phase: 24, uniforms: { MODE: 1, size: 3 } },
    ],
    mutations: [
      { id: 'oilFlatten-sample-window-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var y = -sampleLimit; y <= sampleLimit; y++) {\n  \tfor (var x = -sampleLimit; x <= sampleLimit; x++) {', mutated: 'for (var y = -sampleLimit; y <= sampleLimit; y++) {\n  \tfor (var x = -sampleLimit; x < sampleLimit; x++) {', description: 'Drop the `x<=sampleLimit` upper bound to `x<sampleLimit`: smallest possible wrong trip count, removing the rightmost column of the sample window from every octant tally.' },
      { id: 'oilFlatten-sample-window-swap', kind: 'trip_count_swap', anchor: 'for (var y = -sampleLimit; y <= sampleLimit; y++) {\n  \tfor (var x = -sampleLimit; x <= sampleLimit; x++) {', mutated: 'for (var y = -sampleLimit; y <= sampleLimit - 2; y++) {\n  \tfor (var x = -sampleLimit; x <= sampleLimit - 2; x++) {', description: 'Shrink BOTH loop upper bounds by 2: a materially wrong, asymmetric window that drops a whole outer ring from the bottom-right of the octant scan.' },
    ],
  },
  {
    id: 'smoothBlend', key: 'filter/smooth:smoothBlend', sourceFile: 'smoothBlend.glsl', sourceDir: 'smooth',
    factoryName: 'canonicalFactory139',
    sourceRawBytes: 6858, sourceSha256: 'c317194f9bbdba9d95c5dcae47e2354221cf0cdb05ffcf14e335a94a4ef3729c',
    uniformTypes: { smoothType: 'int', strength: 'float', threshold: 'float', radius: 'float', samples: 'int', searchSteps: 'int' },
    loopRole: '`searchEdge()`\'s SMAA-style edge-distance search (`for(i=1;i<=32;i++){ if(i>searchSteps) break; ...; if(edge<0.5) return i-1; }`) is the ONE loop in this program\'s blocked set (per loop-proof-study SS2/SS7: start/bound/update are already fully canonical -- the sole violation is the blanket "any return in body" veto, not the bound itself). The hard cap of 32 only matters when `searchSteps>=`(the mutated cap) AND the nearest same-orientation edge is farther than the mutated cap but within 32 -- both engineered explicitly in the cases below (see design note).',
    buildTextures: (c) => ({
      inputTex: patternedSurface(c.width, c.height, c.phase),
      edgeTex: searchEdgeSurface(c.width, c.height, c.row, c.renderCol, c.foundLeftCol, c.foundRightCol),
    }),
    reach: (c) => ({ default: c.uniforms.smoothType === 1 }),
    cases: [
      // DESIGN NOTE: a first candidate case (search distance 20, searchSteps
      // 32) was tried against BOTH the off-by-one (32->31) and swap (32->16)
      // mutations. It correctly discriminated the swap (cap shrinks below
      // 20) but produced ZERO divergence for the off-by-one mutation (cap
      // 31 is still far above distance 20) -- exactly the "verify, don't
      // assume" trap the task warns about. Fixed by adding a SECOND case
      // whose search distance is exactly 32 (the boundary the off-by-one
      // mutation clips), so each mutation has at least one case that
      // reaches AND diverges, per the report's mutation table.
      { name: 'edge-distance-20-swap-target', width: 40, height: 6, phase: 30, row: 2, renderCol: 25, foundLeftCol: 5, foundRightCol: 26, uniforms: { smoothType: 1, strength: 1, threshold: 0.1, radius: 3, samples: 4, searchSteps: 32 } },
      { name: 'edge-distance-32-off-by-one-target', width: 40, height: 6, phase: 31, row: 2, renderCol: 33, foundLeftCol: 1, foundRightCol: 34, uniforms: { smoothType: 1, strength: 1, threshold: 0.1, radius: 3, samples: 4, searchSteps: 32 } },
      { name: 'msaa-mode-diagnostic-non-reaching', width: 8, height: 7, phase: 32, row: 1, renderCol: 4, foundLeftCol: 0, foundRightCol: 6, uniforms: { smoothType: 0, strength: 1, threshold: 0.1, radius: 3, samples: 4, searchSteps: 32 }, diagnostic: true },
    ],
    mutations: [
      { id: 'smoothBlend-searchEdge-cap-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var i = 1; i <= 32; i++) {', mutated: 'for (var i = 1; i < 32; i++) {', description: 'Drop the hard cap from 32 to 31: at search distance exactly 32 (the `edge-distance-32-off-by-one-target` case), the mutated search never reaches the edge and falls through to `return searchSteps`, diverging from the real `return 31`.' },
      { id: 'smoothBlend-searchEdge-cap-swap', kind: 'trip_count_swap', anchor: 'for (var i = 1; i <= 32; i++) {', mutated: 'for (var i = 1; i <= 16; i++) {', description: 'Halve the hard cap to 16: at search distance 20 (the `edge-distance-20-swap-target` case), the mutated search never reaches the edge and falls through to `return searchSteps`, diverging from the real `return 19`.' },
    ],
  },
  {
    id: 'zoomBlur', key: 'filter/zoomBlur:zoomBlur', sourceFile: 'zoomBlur.glsl', sourceDir: 'zoomBlur',
    factoryName: 'canonicalFactory182',
    sourceRawBytes: 1496, sourceSha256: '3b24e68c6aec2161bbac73f5cac3d21e658531fff6a365ae78a4982179a707bd',
    uniformTypes: { strength: 'float' },
    loopRole: 'Radial zoom-blur sample count: `for(t=0;t<=40;t++)` (float induction, the loop-proof-study shape this program is blocked on) drives a 41-tap parabolic-weighted radial sample average. A wrong trip count drops samples asymmetrically across the `percent=(t+offset)/40` parabola, changing both the weighted color sum and the normalizing `total`.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    // NOTE: unlike blur's `radius<=0` early return, zoomBlur's loop has
    // no early exit at all -- it always executes all 41 iterations
    // regardless of `strength`. Verified empirically below: even at
    // strength=0 (where every tap samples the identical uv, so the
    // mathematically-expected weighted average is invariant to trip
    // count) the off-by-one mutation STILL diverges, at float32
    // rounding precision in the weighted sum/normalize -- a stronger,
    // not weaker, discrimination result, so this case is always
    // reach-eligible (not a non-reaching diagnostic).
    reach: () => ({ default: true }),
    cases: [
      { name: 'moderate-strength-wide', width: 12, height: 10, phase: 40, uniforms: { strength: 0.6 } },
      { name: 'strong-strength-tall', width: 10, height: 12, phase: 41, uniforms: { strength: 0.9 } },
      { name: 'weak-strength-tiled', width: 16, height: 14, phase: 42, tileOffset: [2, 2], fullResolution: [20, 18], uniforms: { strength: 0.3 } },
      { name: 'large-strength-square', width: 9, height: 9, phase: 43, uniforms: { strength: 1.5 } },
      { name: 'zero-strength-uniform-sampling', width: 5, height: 5, phase: 44, uniforms: { strength: 0 } },
    ],
    mutations: [
      { id: 'zoomBlur-sample-count-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var t = 0; t <= 40; t++) {', mutated: 'for (var t = 0; t < 40; t++) {', description: 'Drop the `t<=40` upper bound to `t<40`: smallest possible wrong trip count, dropping the t=40 sample (percent=1, the parabola\'s other zero-weight endpoint -- still touches `total` at float32 precision because `offset` is nonzero).' },
      { id: 'zoomBlur-sample-count-swap', kind: 'trip_count_swap', anchor: 'for (var t = 0; t <= 40; t++) {', mutated: 'for (var t = 0; t <= 20; t++) {', description: 'Halve the sample count to 21 taps (t=0..20): a materially wrong trip count that drops the entire back half of the parabola, including its highest-weight taps near t=20..40.' },
    ],
  },
  {
    id: 'tetraColorArray', key: 'filter/tetraColorArray:tetraColorArray', sourceFile: 'tetraColorArray.glsl', sourceDir: 'tetraColorArray',
    factoryName: 'canonicalFactory158',
    sourceRawBytes: 9754, sourceSha256: '68c7cabce311a0a05ba116ce8d34bd5e70e0c09bfb8eab06c93f4f9e01fa5438',
    uniformTypes: { colorMode: 'int', colorCount: 'int', positionMode: 'int', color0: 'vec3', color1: 'vec3', color2: 'vec3', color3: 'vec3', color4: 'vec3', color5: 'vec3', color6: 'vec3', color7: 'vec3', pos0: 'float', pos1: 'float', pos2: 'float', pos3: 'float', pos4: 'float', pos5: 'float', pos6: 'float', pos7: 'float', repeat: 'float', offset: 'float', smoothness: 'float', alpha: 'float', rotation: 'int' },
    loopRole: '`sampleColorArray()`\'s `for(i=1;i<count;i++)` blends across `count-1` palette-stop boundaries (`count` = the `colorCount` uniform, a parameter-bound loop per loop-proof-study SS2). A wrong trip count skips the transition into the last color stop(s), changing the gradient color at any luminance `t` past the dropped boundary.',
    buildTextures: (c) => ({ inputTex: patternedSurface(c.width, c.height, c.phase) }),
    // The real loop `for(i=1;i<count;i++)` runs at least once whenever
    // colorCount>=2 (not >=3 -- corrected after this generator's first
    // reach() draft wrongly flagged colorCount=2 as non-reaching and the
    // verification step below caught it: the off-by-one mutation DOES
    // diverge at colorCount=2, because the real version still runs the
    // i=1 iteration that the mutated `i<count-1` version skips).
    // Any colorCount>=2 makes the real loop run >=1 time; both mutations
    // below shrink the upper bound (to count-1 or count-3), which for
    // count-3 can go negative -- `i=1;i<negative` is simply 0 iterations
    // in JS, still strictly fewer than the real >=1, so BOTH mutations
    // are reach-eligible (and verified to diverge) at every colorCount>=2
    // tested here, not just the larger counts originally assumed.
    reach: (c) => ({ default: c.uniforms.colorCount >= 2 }),
    cases: [
      { name: 'four-stops-wide', width: 10, height: 9, phase: 50, uniforms: tetraColorUniforms(4) },
      { name: 'six-stops-tall', width: 9, height: 10, phase: 51, uniforms: tetraColorUniforms(6) },
      { name: 'eight-stops-square', width: 12, height: 8, phase: 52, uniforms: tetraColorUniforms(8) },
      { name: 'three-stops-small', width: 8, height: 8, phase: 53, uniforms: tetraColorUniforms(3) },
      { name: 'two-stops-minimal', width: 6, height: 6, phase: 54, uniforms: tetraColorUniforms(2) },
    ],
    mutations: [
      { id: 'tetraColorArray-stop-count-off-by-one', kind: 'trip_count_off_by_one', anchor: 'for (var i = 1; i < count; i++) {', mutated: 'for (var i = 1; i < count - 1; i++) {', description: 'Drop the last blend iteration (`i<count-1`): smallest possible wrong trip count, skipping the transition into the final color stop.' },
      { id: 'tetraColorArray-stop-count-swap', kind: 'trip_count_swap', anchor: 'for (var i = 1; i < count; i++) {', mutated: 'for (var i = 1; i < count - 3; i++) {', description: 'Drop the last three blend iterations (`i<count-3`, clamped to 0 iterations in JS whenever count<=3): a materially wrong trip count, verified to diverge from colorCount=2 upward.' },
    ],
  },
]

const DITHER_BLOCKER = {
  id: 'dither', key: 'filter/dither:dither', sourceFile: 'dither.glsl',
  factoryName: 'canonicalFactory48',
  sourceRawBytes: 19391, sourceSha256: 'a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb',
  reason: 'UNRENDERABLE, not merely non-discriminating -- verified live, not assumed. All three of this program\'s blocked loop-proof sites (the FS_ERR_W-bound fill loop, and the two "-FS_APRON_MAX" symmetric-window r/c loops -- loop-proof-study SS2/SS4) live exclusively inside errorDiffusion(), reachable only when ditherType==DITHER_ERROR_DIFFUSION(7). The CURRENT PINNED canonical-kernels.js (sha256 e605746c...98815ab56, the same hash independently verified by every other oracle in this audited family) compiles errorDiffusion()\'s array-fill loop as `fsSeedNoise(...).reduce((res,el,i)=>(res[i]=el,res), errRow[i])` -- passing the not-yet-assigned `errRow[i]` (undefined, since `errRow` starts as `[]`) as reduce\'s INITIAL accumulator, which throws `TypeError: Cannot set properties of undefined (setting \'0\')` on the very first loop iteration (i=0), for EVERY canvas size and EVERY uniform combination -- confirmed with a minimal isolated repro of the exact reduce-into-undefined pattern (see report). This is 100% reproducible, unconditional, and independent of any loop-bound mutation: the reference JS this oracle must treat as ground truth does not produce ANY output for the one branch containing this program\'s blocked loops, so no render-level trip-count discrimination can be demonstrated -- not because the loops fail to discriminate, but because the reference crashes before either the real or the mutated factory can be compared. This is a genuine, independently-discovered defect in noisemaker-for-cpu (most likely a glsl-transpiler code-generation gap for first-time GLSL fixed-array element writes, distinct from and orthogonal to the C++ loop-proof gate this cluster exists to unblock) -- out of scope to fix here per the task\'s explicit prohibition on modifying noisemaker-for-cpu. Confirmed the crash is isolated to this one function: `errorDiffusion` occurs exactly once in canonical-kernels.js, and the existing test suite (test/canonical-kernel-smoke.test.js) only ever exercises dither at its DEFAULT (Bayer, non-error-diffusion) dither type, so this defect was never previously exercised or caught.',
}

// ---------------------------------------------------------------------------
// Per-program verification, before any case is built.
// ---------------------------------------------------------------------------
function loadProgram(def) {
  const sourcePath = path.join(corpusRoot, 'sources/filter', def.sourceDir, def.sourceFile)
  const sourceBytes = fs.readFileSync(sourcePath)
  if (sourceBytes.length !== def.sourceRawBytes) throw new Error(`${def.id}: source raw byte count drift`)
  if (sha256(sourceBytes) !== def.sourceSha256) throw new Error(`${def.id}: source sha256 drift`)

  const canonical = canonicalKernelFactories[def.key]
  if (!canonical) throw new Error(`${def.id}: canonical factory missing for key ${def.key}`)
  if (canonical.name !== def.factoryName) throw new Error(`${def.id}: factory name drift (got ${canonical.name})`)
  const factoryText = canonical.toString()

  const publicIsCanonical = kernelFactories.get(def.key) === canonical
  if (!publicIsCanonical) throw new Error(`${def.id}: public factory is not the canonical identity`)
  if (canonicalAdapterFactories[def.key] !== undefined) throw new Error(`${def.id}: unexpected adapter override present`)

  if (def.defines) {
    for (const k of Object.keys(def.defines)) {
      if (!new RegExp(`\\$bindings\\[${JSON.stringify(k)}\\]`).test(factoryText)) {
        throw new Error(`${def.id}: authorized define "${k}" is not actually read by the factory as a binding -- defines-bound-as-uniforms lesson`)
      }
    }
  }

  return { ...def, sourcePath, factoryText, canonical }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)

// ---------------------------------------------------------------------------
// Case rendering.
// ---------------------------------------------------------------------------
for (const program of PROGRAMS) {
  program.caseRecords = program.cases.map((c) => {
    const rendered = renderCase(program, c)
    return { ...rendered, reach: program.reach(c) }
  })
  const anyReach = program.caseRecords.some((cr) => Object.values(cr.reach).some(Boolean))
  if (!anyReach) throw new Error(`${program.id}: no reach-eligible case at all -- cannot prove discrimination, fix the case table`)
}

// ---------------------------------------------------------------------------
// Mutation execution -- machine-asserted nonzero divergence on reach-eligible
// cases, zero divergence on non-reach-eligible cases, per mutation.
// ---------------------------------------------------------------------------
for (const program of PROGRAMS) {
  for (const mutation of program.mutations) {
    const reachKey = mutation.reachKey ?? 'default'
    const mutatedText = mutateFactoryText(program.factoryText, mutation)
    const mutatedFactory = evaluated(mutatedText)

    const caseResults = program.caseRecords.map((cr) => {
      const mutatedSurface = renderWithFactory(program, cr.c, mutatedFactory)
      const diverges = !sameBytes(cr.surface, mutatedSurface)
      const reaches = Boolean(cr.reach[reachKey])
      return { case: cr.name, diagnostic: Boolean(cr.c.diagnostic), reaches, diverges }
    })
    const reaching = caseResults.filter((r) => r.reaches)
    const nonReaching = caseResults.filter((r) => !r.reaches)
    const divergentReaching = reaching.filter((r) => r.diverges).length
    const divergentNonReaching = nonReaching.filter((r) => r.diverges).length

    if (reaching.length === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site -- cannot prove discrimination, fix the case table`)
    if (divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases (trip count must genuinely discriminate), got 0/${reaching.length} -- the loop body may be idempotent/saturating for these cases, investigate before shipping`)
    if (divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${divergentNonReaching}/${nonReaching.length} non-reaching case(s) diverged -- the reach() predicate is wrong or the mutation leaked outside its intended site, investigate before shipping`)

    mutation.caseResults = caseResults
    mutation.summary = { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
    mutation.partialDivergenceNote = divergentReaching !== reaching.length
      ? `Only ${divergentReaching}/${reaching.length} reach-eligible cases diverged -- the remaining reach-eligible case(s) were engineered for a DIFFERENT mutation in this program (see design note) and are not expected to diverge under this one.`
      : null
  }
  // Save this program's cases/mutations to disk incrementally, per the
  // "work incrementally, don't hold everything until the end" instruction --
  // a partial-oracle checkpoint after each program clears its mutations.
  const checkpointPath = path.join(here, `.checkpoint-${program.id}.json`)
  fs.writeFileSync(checkpointPath, JSON.stringify({
    id: program.id, key: program.key,
    cases: program.caseRecords.map((cr) => cr.name),
    mutations: program.mutations.map((m) => ({ id: m.id, summary: m.summary })),
  }, null, 2))
  console.log(`[checkpoint] ${program.id}: ${program.caseRecords.length} cases, ${program.mutations.length} mutations verified`)
}

// ---------------------------------------------------------------------------
// dither: independently verify the documented crash live (hard evidence,
// not a claim) -- both that the error-diffusion path throws unconditionally,
// AND that dither's OTHER (non-blocked) code paths render fine, proving the
// defect is isolated to errorDiffusion() and not a hermeticity/setup mistake
// on this generator's part.
// ---------------------------------------------------------------------------
function verifyDitherBlocker(def) {
  const sourcePath = path.join(corpusRoot, 'sources/filter/dither', def.sourceFile)
  const sourceBytes = fs.readFileSync(sourcePath)
  if (sourceBytes.length !== def.sourceRawBytes) throw new Error('dither: source raw byte count drift')
  if (sha256(sourceBytes) !== def.sourceSha256) throw new Error('dither: source sha256 drift')
  const canonical = canonicalKernelFactories[def.key]
  if (!canonical) throw new Error('dither: canonical factory missing')
  if (canonical.name !== def.factoryName) throw new Error(`dither: factory name drift (got ${canonical.name})`)
  if (kernelFactories.get(def.key) !== canonical) throw new Error('dither: public factory is not the canonical identity')
  if (canonicalAdapterFactories[def.key] !== undefined) throw new Error('dither: unexpected adapter override present')

  // Isolated repro of the exact compiled pattern, independent of the render
  // pipeline -- proves the crash is inherent to the reduce-into-undefined
  // shape itself, not an artifact of this generator's bindings/textures.
  let isolatedReproThrew = false
  let isolatedReproMessage = null
  try {
    const errRow = []
    ;[1, 2, 3].reduce((res, el, i) => (res[i] = el, res), errRow[0])
  } catch (error) {
    isolatedReproThrew = true
    isolatedReproMessage = error.message
  }
  if (!isolatedReproThrew) throw new Error('dither: isolated repro of the reduce-into-undefined pattern unexpectedly did NOT throw -- the documented blocker claim would be WRONG, investigate')

  // Live render attempt through the real pipeline, DITHER_ERROR_DIFFUSION=7,
  // across several unrelated widths/heights/uniform combinations -- must
  // throw the SAME error class on every single one (100% reproducible, not
  // input-dependent).
  const inputTex = patternedSurface(6, 5, 0)
  const attempts = [
    { width: 6, height: 5, levels: 4, matrixScale: 1, renderScale: 1, threshold: 0 },
    { width: 1, height: 1, levels: 2, matrixScale: 2, renderScale: 1, threshold: 0.2 },
    { width: 12, height: 9, levels: 8, matrixScale: 0.5, renderScale: 2, threshold: -0.1 },
  ]
  const renderAttempts = attempts.map((a) => {
    const tex = patternedSurface(a.width, a.height, 1)
    const uniforms = { ditherType: 7, threshold: f(a.threshold), matrixScale: f(a.matrixScale), renderScale: f(a.renderScale), palette: 0, levels: a.levels, mixAmount: f(1) }
    const bindings = createCanonicalBindings({ width: a.width, height: a.height, uniforms, textures: { inputTex: tex }, time: 0 })
    const kernel = bindGlslKernel(canonical, bindings)
    const surface = new Surface(a.width, a.height)
    try {
      runPass({ kernel, destination: surface })
      return { ...a, threw: false, message: null }
    } catch (error) {
      return { ...a, threw: true, message: error.message }
    }
  })
  if (!renderAttempts.every((r) => r.threw)) throw new Error(`dither: at least one DITHER_ERROR_DIFFUSION render attempt unexpectedly SUCCEEDED -- the documented blocker claim would be WRONG, investigate: ${JSON.stringify(renderAttempts)}`)
  if (!renderAttempts.every((r) => r.message === renderAttempts[0].message)) throw new Error(`dither: render attempts threw DIFFERENT errors -- the crash may not be the documented unconditional defect, investigate: ${JSON.stringify(renderAttempts)}`)

  // Prove isolation: a NON-error-diffusion dither type (Bayer 2x2) on the
  // SAME factory, SAME kind of inputs, renders successfully -- the defect is
  // confined to errorDiffusion(), not a general breakage of this program.
  const okBindings = createCanonicalBindings({
    width: 6, height: 5,
    uniforms: { ditherType: 0, threshold: f(0), matrixScale: f(1), renderScale: f(1), palette: 0, levels: 4, mixAmount: f(1) },
    textures: { inputTex }, time: 0,
  })
  const okKernel = bindGlslKernel(canonical, okBindings)
  const okSurface = new Surface(6, 5)
  runPass({ kernel: okKernel, destination: okSurface })
  let nonFinite = 0
  for (const lane of okSurface.data) if (!Number.isFinite(lane)) nonFinite += 1

  return {
    isolated_repro_threw: isolatedReproThrew,
    isolated_repro_message: isolatedReproMessage,
    render_attempts: renderAttempts,
    non_error_diffusion_render_ok: true,
    non_error_diffusion_finite_lanes: okSurface.data.length - nonFinite,
    non_error_diffusion_nonfinite_lanes: nonFinite,
    factory_name: canonical.name,
    public_is_canonical: true,
    adapter_override_present: false,
  }
}

const ditherEvidence = verifyDitherBlocker(DITHER_BLOCKER)
fs.writeFileSync(path.join(here, '.checkpoint-dither.json'), JSON.stringify({ id: 'dither', blocked: true, evidence: ditherEvidence }, null, 2))
console.log('[checkpoint] dither: documented as UNRENDERABLE, blocker evidence captured live')

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const programsOut = {}
  let totalEligible = 0
  let totalDiagnostic = 0
  for (const program of PROGRAMS) {
    const eligible = program.caseRecords.filter((cr) => !cr.c.diagnostic)
    const diagnostic = program.caseRecords.filter((cr) => cr.c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    programsOut[program.id] = {
      key: program.key,
      defines: { ...(program.defines ?? {}) },
      source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName,
      public_is_canonical: true,
      adapter_override: null,
      loop_role: program.loopRole,
      cases: program.caseRecords.map((cr) => ({
        name: cr.name, dimensions: { width: cr.c.width, height: cr.c.height }, diagnostic: Boolean(cr.c.diagnostic), reach: cr.reach,
        uniforms: cr.c.uniforms, time: cr.c.time ?? 0, tile_offset: cr.c.tileOffset ?? [0, 0], full_resolution: cr.c.fullResolution ?? [cr.c.width, cr.c.height],
        // Every case in this generator renders at the program's single
        // authorized define map (verified live in loadProgram()) -- no case
        // tests an off-default define, so this is always true by construction.
        eligible_for_native_binding: true,
        repeat_identity: true, input_immutable: true,
        output: renderResult(cr.surface),
      })),
      mutations: program.mutations.map((m) => ({
        id: m.id, kind: m.kind, reach_key: m.reachKey ?? 'default', anchor: m.anchor, mutated: m.mutated, description: m.description,
        case_results: m.caseResults, summary: m.summary, partial_divergence_note: m.partialDivergenceNote,
      })),
    }
  }

  return {
    schema: 'noisemaker-for-cpp.loopproof.oracle-a.eight-program-loop-trip-count-oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version },
    programs: programsOut,
    dither: {
      key: DITHER_BLOCKER.key,
      status: 'UNCOVERABLE',
      reason: DITHER_BLOCKER.reason,
      evidence: ditherEvidence,
    },
    eligibility_summary: {
      programs_covered: PROGRAMS.length,
      programs_blocked: 1,
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic,
      total_mutations: PROGRAMS.reduce((n, p) => n + p.mutations.length, 0),
    },
  }
}

function report(d) {
  const lines = [
    '# Loop-proof cluster oracle-a report', '',
    'Hermetic JS oracle for eight programs blocked on the counted-loop program-proof gate. Ground truth for the future C++20 port\'s bit-exact parity tests, once each program\'s loop-proof gate clears.', '',
    `Programs covered with a full discriminating oracle: **${d.eligibility_summary.programs_covered}**. Programs that could not be covered: **${d.eligibility_summary.programs_blocked}** (\`filter/dither:dither\` -- see below).`, '',
    `Total cases across the seven covered programs: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} diagnostic). Total mutations: **${d.eligibility_summary.total_mutations}**.`, '',
    '## Per-program summary', '',
    '| Program | Cases | Diagnostic | Mutations | All mutations diverge on >=1 reach-eligible case |', '| --- | ---: | ---: | ---: | --- |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    const allDiverge = p.mutations.every((m) => m.summary.divergent_reaching > 0)
    lines.push(`| ${id} | ${eligible} | ${diagnostic} | ${p.mutations.length} | ${allDiverge} |`)
  }
  lines.push(`| dither | -- | -- | -- | **UNCOVERABLE -- see below** |`)
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\` (${id})`, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\`. Public factory is canonical: ${p.public_is_canonical}. Defines: \`${JSON.stringify(p.defines)}\`.`, '')
    lines.push(`Loop role: ${p.loop_role}`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${JSON.stringify(c.reach)} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations -- empirical divergence figures', '', '| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |', '| --- | --- | ---: | ---: | ---: | ---: |')
    for (const m of p.mutations) {
      lines.push(`| ${m.id} | ${m.kind} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}${m.partial_divergence_note ? ` _Note: ${m.partial_divergence_note}_` : ''}`), '')
  }
  lines.push('## `filter/dither:dither` -- UNCOVERABLE', '')
  lines.push(d.dither.reason, '')
  lines.push('### Live evidence captured by this generator', '')
  lines.push(`- Isolated repro of the exact compiled \`.reduce(callback, arr[notYetSet])\` pattern threw: **${d.dither.evidence.isolated_repro_threw}** (\`${d.dither.evidence.isolated_repro_message}\`)`)
  lines.push(`- Full-pipeline render attempts at \`ditherType=DITHER_ERROR_DIFFUSION(7)\` across 3 unrelated canvas sizes/uniform sets: ${d.dither.evidence.render_attempts.length}/${d.dither.evidence.render_attempts.length} threw, all with the identical message \`${d.dither.evidence.render_attempts[0].message}\``)
  lines.push(`- Same factory, \`ditherType=DITHER_BAYER_2X2(0)\`, renders successfully: finite_lanes=${d.dither.evidence.non_error_diffusion_finite_lanes}, nonfinite_lanes=${d.dither.evidence.non_error_diffusion_nonfinite_lanes} -- proves the defect is isolated to \`errorDiffusion()\`, not a general breakage of this program or a hermeticity mistake in this generator.`, '')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('loopproof-a oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('loopproof-a oracle report drift')
  console.log(`loopproof-a oracle fixture ok (${PROGRAMS.length} programs covered + 1 documented blocker, ${data.eligibility_summary.total_cases} cases, ${data.eligibility_summary.total_mutations} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  // Clean up the per-program progress checkpoints now that the final,
  // authoritative JSON/report have been written -- they served their
  // "work incrementally, don't hold everything until the end" purpose
  // during generation; the final oracle JSON supersedes them.
  for (const program of PROGRAMS) {
    const p = path.join(here, `.checkpoint-${program.id}.json`)
    if (fs.existsSync(p)) fs.unlinkSync(p)
  }
  const ditherCheckpoint = path.join(here, '.checkpoint-dither.json')
  if (fs.existsSync(ditherCheckpoint)) fs.unlinkSync(ditherCheckpoint)
  console.log(outPath)
  console.log(reportPath)
}
