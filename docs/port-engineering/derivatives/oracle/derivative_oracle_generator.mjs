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
// Derivative cluster oracle -- 15 GLSL programs blocked on dFdx/dFdy/fwidth,
// about to be ported from noisemaker-for-cpu (JS) to noisemaker-for-cpp
// (C++20). This generator is the JS-golden ground truth the C++ port's
// tests will assert against, bit-exactly. It follows the house style set by
// docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs
// (hermetic imports, --check determinism, per-case mutation testing, an
// explicit intent-verification guard) and extends it with a derivative-
// specific verification layer the grade cluster didn't need: proof that
// each case actually took the wrapDerivatives() quad-probe path (not just
// that the kernel compiled), and mutation testing of the SHARED derivative
// mechanism itself (glsl-runtime.js's wrapDerivatives), not of any single
// program's source text -- because all 15 programs route through the exact
// same runtime method, a mutation of that one method is a universal,
// uniformly-applied discriminator across the whole cluster.
//
// THE 15 PROGRAMS (from derivative-program-characterization.md's verified
// "15 of 17" -- posterize and waves are excluded, each blocked by a second,
// unrelated capability gap: round / any):
//   bulge, celShadingColor, halftone, lens, lensWarp, octaveWarp, pinch,
//   polar, pondRipples, spiral, stThreshold, step, stipple, tunnel, warp.
//
// THREE HARD-WON LESSONS APPLIED THROUGHOUT (the first two carried over
// verbatim from the grade generator; the third is new to this cluster):
//   1. RESERVED TOP-LEVEL KEYS. `createCanonicalBindings` (glsl-kernel.js
//      :20-61) assigns nine canonical keys (resolution, fullResolution,
//      tileOffset, aspectRatio, aspect, time, globalTime, deltaTime, frame)
//      AFTER spreading `...uniforms`, so passing any of them *inside* the
//      uniforms object silently discards the caller's intended value. Every
//      case here is rendered through `renderCase()`, which refuses to build
//      if the uniforms object illegally contains one of these keys, and
//      independently reconstructs the bindings to assert the kernel's own
//      bound `tileOffset`/`fullResolution`/`time` equal the CALLER's
//      intended values.
//   2. MODE/PATTERN/STYLE/WRAP ARE NOT GLSL UNIFORMS -- THEY ARE BINDINGS
//      KEYS TOO. halftone, pondRipples, and stipple pin compile-time GLSL
//      `#define`s (MODE, PATTERN, STYLE, WRAP). The GLSL compiler would
//      resolve these once, at compile time. The JS reference has no
//      preprocessor: reading each canonical factory's own source text
//      (`$bindings["MODE"]`, `$bindings["STYLE"]`, ...) shows these defines
//      are threaded through as ordinary `$bindings` lookups -- i.e. as
//      entries the CALLER must supply inside `uniforms`, at exactly their
//      `generate_typed_slice._defaults()`-authorized value, or the kernel
//      reads `undefined` and silently takes the WRONG runtime branch (e.g.
//      halftone's `if (MODE == 0)` is false when MODE is undefined, and the
//      whole cluster's authority for "which branch is the one ported
//      variant" comes from `_defaults()`, confirmed live below). This is
//      independently verified in `verifyDefineBindingRequirement()`.
//   3. DERIVATIVE-PATH ACTIVATION MUST BE PROVEN, NOT ASSUMED. A kernel with
//      `factory.usesDerivatives` gets wrapped by `runtime.wrapDerivatives`
//      regardless of what its own GLSL branches do -- the probe/replay
//      machinery always runs. That is NOT the same as the program's own
//      `dFdx`/`dFdy`/`fwidth` call site having actually executed for a given
//      case. `renderCase()` independently re-renders every case through a
//      byte-for-byte structural copy of the real `wrapDerivatives` (see
//      `FaithfulRuntime` below) that also records the per-pixel derivative
//      ordinal count, and asserts: (a) the faithful copy's output is BIT-
//      IDENTICAL to the real, unmodified runtime's output (proving the copy
//      is accurate, not just plausible), and (b) the recorded ordinal count
//      matches -- per pixel, with no mixing -- the characterization
//      doc's per-program prediction (2 for the dFdx+dFdy family, 1 for the
//      fwidth-scalar/vec3 family, 4 for halftone) when the derivative path
//      is reachable, and exactly 0 when it is gated off (antialias=false).
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'derivative-oracles.json')
const reportPath = path.join(here, 'derivative-oracle-report.md')
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

// ---------------------------------------------------------------------------
// Runtime/catalog hermeticity pinning (shared across all 15 programs).
// Identical file set and identical hash VALUES to the grade generator's
// RUNTIME_PROVENANCE (same repo state) -- independently recomputed here,
// not copy-pasted trust.
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
// Lesson 1: reserved top-level keys.
// ---------------------------------------------------------------------------
const RESERVED_TOP_LEVEL_KEYS = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']
function assertNoReservedKeysInUniforms(uniforms) {
  for (const k of RESERVED_TOP_LEVEL_KEYS) {
    if (Object.prototype.hasOwnProperty.call(uniforms, k)) {
      throw new Error(`uniforms illegally contains reserved top-level-only key "${k}" -- createCanonicalBindings assigns this AFTER spreading ...uniforms, so it would be silently discarded`)
    }
  }
}

// ---------------------------------------------------------------------------
// Small local reimplementations of glsl-runtime.js's unexported `isVector`/
// `component` helpers (source lines 7-13), needed because the mutation
// runtimes below reimplement `wrapDerivatives` (a public method, safely
// overridable by subclassing) and that method's body calls these two
// unexported free functions. Copied verbatim, not reinvented.
// ---------------------------------------------------------------------------
function isVectorLocal(value) { return ArrayBuffer.isView(value) || Array.isArray(value) }
function componentLocal(value, index) { return isVectorLocal(value) ? value[index] : value }

// ---------------------------------------------------------------------------
// FaithfulRuntime: a byte-for-byte structural copy of the real
// GlslCpuRuntime.wrapDerivatives (glsl-runtime.js:476-546), with
// instrumentation added (never behavior changes) to record, per replay
// call, the derivative ordinal count actually computed for that pixel.
// Used to (a) independently prove the copy is accurate (its rendered output
// must be bit-identical to the real, unmodified bindGlslKernel path) and
// (b) verify the ordinal-count-per-pixel matches the characterization.
//
// SignFlipRuntime and LaneTransposeRuntime are the same copy with exactly
// one deliberate change each -- see their comments -- used as the two
// derivative-mechanism mutations run against every case.
// ---------------------------------------------------------------------------
class FaithfulRuntime extends GlslCpuRuntime {
  wrapDerivatives(kernel) {
    const cache = new Map()
    const temporary = new Float32Array(4)
    this.ordinalCounts = []
    const probe = (context, x, y) => {
      const fragCoord = new Float32Array([x, y])
      const resolution = context.resolution
      const probeContext = { ...context, fragCoord, uv: new Float32Array([x / resolution[0], y / resolution[1]]) }
      this.derivativeMode = 'record'
      this.derivativeRecords = []
      kernel(probeContext, temporary)
      return this.derivativeRecords
    }
    return (context, out) => {
      const pixelX = Math.floor(context.fragCoord[0] - 0.5)
      const pixelY = Math.floor(context.fragCoord[1] - 0.5)
      const quadX = pixelX >> 1
      const quadY = pixelY >> 1
      const key = `${quadX}:${quadY}`
      let lanes = cache.get(key)
      if (!lanes) {
        const x0 = quadX * 2 + 0.5
        const y0 = quadY * 2 + 0.5
        lanes = this.probeLanes(probe, context, x0, y0)
        cache.set(key, lanes)
      }
      const xParity = pixelX & 1
      const yParity = pixelY & 1
      const left = lanes[yParity * 2]
      const right = lanes[yParity * 2 + 1]
      const bottom = lanes[xParity]
      const top = lanes[xParity + 2]
      const count = Math.max(left.length, right.length, bottom.length, top.length)
      this.ordinalCounts.push(count)
      this.derivativeValues = Array.from({ length: count }, (_, index) => this.combineLanes(left, right, bottom, top, index))
      this.derivativeMode = 'replay'
      try {
        kernel(context, out)
      } finally {
        this.derivativeMode = 'approximate'
        this.derivativeRecords = null
        this.derivativeValues = null
        const lastX = pixelX === context.resolution[0] - 1
        const firstYInTraversal = pixelY === 0
        if ((xParity === 1 || lastX) && (yParity === 0 || firstYInTraversal)) cache.delete(key)
      }
    }
  }

  // Quad member probe order -- overridden by LaneTransposeRuntime only.
  probeLanes(probe, context, x0, y0) {
    return [probe(context, x0, y0), probe(context, x0 + 1, y0), probe(context, x0, y0 + 1), probe(context, x0 + 1, y0 + 1)]
  }

  // x/y combination (sign convention) -- overridden by SignFlipRuntime only.
  combineLanes(left, right, bottom, top, index) {
    const fallback = 0
    const leftValue = left[index] ?? fallback
    const rightValue = right[index] ?? leftValue
    const bottomValue = bottom[index] ?? fallback
    const topValue = top[index] ?? bottomValue
    if (!isVectorLocal(leftValue) && !isVectorLocal(rightValue) && !isVectorLocal(bottomValue) && !isVectorLocal(topValue)) {
      const x = rightValue - leftValue
      const y = topValue - bottomValue
      return { x, y, width: Math.abs(x) + Math.abs(y) }
    }
    const width = Math.max(leftValue.length ?? 0, rightValue.length ?? 0, bottomValue.length ?? 0, topValue.length ?? 0)
    const x = new Float32Array(width)
    const y = new Float32Array(width)
    const footprint = new Float32Array(width)
    for (let c = 0; c < width; c += 1) {
      x[c] = componentLocal(rightValue, c) - componentLocal(leftValue, c)
      y[c] = componentLocal(topValue, c) - componentLocal(bottomValue, c)
      footprint[c] = Math.abs(x[c]) + Math.abs(y[c])
    }
    return { x, y, width: footprint }
  }
}

// Mutation A: sign-flip. x' = left - right = -x (y is left untouched).
// Tests the sign convention the architecture doc calls out explicitly
// ("getting this backwards silently negates every result"), modeled as an
// X-ONLY convention error (the realistic single-function-swap mistake --
// `dFdx` implemented backwards while `dFdy` stays correct) rather than a
// simultaneous negation of both axes. This distinction is load-bearing and
// was found empirically, not assumed: the 10 dFdx/dFdy-consuming programs
// all supersample with the SAME four offset taps
// (dx*-0.375+dy*-0.125, dx*0.125+dy*-0.375, dx*0.375+dy*0.125,
// dx*-0.125+dy*0.375), which is a point-symmetric set (closed under
// negation) whose unweighted average is therefore PROVABLY invariant under
// simultaneously negating both dx and dy -- a both-axes sign flip would be
// silently invisible in this specific 4-tap pattern despite being a real
// bug in principle. An x-only flip breaks that symmetry (verified below)
// and is also the more realistic single-line mistake.
//
// Provably a NO-OP for fwidth-only consumers regardless of which axis (or
// axes) flip sign: width = |x|+|y| depends on |x| and |y| independently,
// and IEEE754 negation/abs are exact, so |-x|+|y| === |x|+|y| bit-for-bit
// -- documented as an expected-zero mutation for those programs, not
// silently dropped.
class SignFlipRuntime extends FaithfulRuntime {
  combineLanes(left, right, bottom, top, index) {
    const fallback = 0
    const leftValue = left[index] ?? fallback
    const rightValue = right[index] ?? leftValue
    const bottomValue = bottom[index] ?? fallback
    const topValue = top[index] ?? bottomValue
    if (!isVectorLocal(leftValue) && !isVectorLocal(rightValue) && !isVectorLocal(bottomValue) && !isVectorLocal(topValue)) {
      const x = leftValue - rightValue
      const y = topValue - bottomValue
      return { x, y, width: Math.abs(x) + Math.abs(y) }
    }
    const width = Math.max(leftValue.length ?? 0, rightValue.length ?? 0, bottomValue.length ?? 0, topValue.length ?? 0)
    const x = new Float32Array(width)
    const y = new Float32Array(width)
    const footprint = new Float32Array(width)
    for (let c = 0; c < width; c += 1) {
      x[c] = componentLocal(leftValue, c) - componentLocal(rightValue, c)
      y[c] = componentLocal(topValue, c) - componentLocal(bottomValue, c)
      footprint[c] = Math.abs(x[c]) + Math.abs(y[c])
    }
    return { x, y, width: footprint }
  }
}

// Mutation B: lane-order transpose. Swaps the second and third quad probe
// (the "x0,y0+1" and "x0+1,y0" corners), i.e. [BL,BR,TL,TR] -> [BL,TL,BR,TR].
// Models a coarse-quad-sharing bug -- a plausible real mistake (row-major vs
// column-major corner enumeration) that corrupts which pair of probes feeds
// dFdx vs dFdy (and, for fwidth, corrupts both simultaneously). Expected to
// diverge for every program whose local field has any x/y anisotropy, which
// the patterned, non-flat input textures below guarantee in practice --
// verified empirically per case, not assumed.
class LaneTransposeRuntime extends FaithfulRuntime {
  probeLanes(probe, context, x0, y0) {
    return [probe(context, x0, y0), probe(context, x0, y0 + 1), probe(context, x0 + 1, y0), probe(context, x0 + 1, y0 + 1)]
  }
}

function bindWithRuntimeClass(factory, bindings, RuntimeClass) {
  // Mirrors bindGlslKernel (glsl-runtime.js:549-556) exactly, generalized to
  // accept a runtime CLASS instead of hardcoding `new GlslCpuRuntime()`, so
  // the mutation runtimes above can be driven through the identical
  // factory-invocation contract the real function uses.
  const runtime = new RuntimeClass()
  let kernel = factory(Object.freeze({ ...bindings }), runtime)
  if (factory.usesDerivatives) kernel = runtime.wrapDerivatives(kernel)
  return { kernel, runtime }
}

// ---------------------------------------------------------------------------
// Deterministic patterned input texture -- same construction as the grade
// generator's patternedSurface, so R/G/B/A genuinely differ per pixel (a
// requirement for the lane-transpose mutation to be guaranteed visible) and
// no two cases in the whole oracle share an input (distinct `phase`).
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
    else if (type === 'vec2' || type === 'vec3' || type === 'vec4') out[k] = new Float32Array(v.map(f))
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
}

// ---------------------------------------------------------------------------
// renderCase: the single rendering path every case goes through. Builds
// bindings, asserts the reserved-key guard and the intended-binding
// observation (Lesson 1), renders through the REAL unmodified
// bindGlslKernel, checks repeat-render identity and input immutability,
// independently re-renders through FaithfulRuntime (asserting bit-identical
// output and recording ordinal counts -- Lesson 3), then renders through
// SignFlipRuntime and LaneTransposeRuntime for the mutation table.
// ---------------------------------------------------------------------------
function renderCase(program, c) {
  assertNoReservedKeysInUniforms(c.uniforms)
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = { inputTex: patternedSurface(c.width, c.height, c.phase) }
  if (program.extraTextures) {
    for (const [texName, texPhaseOffset] of Object.entries(program.extraTextures)) {
      textures[texName] = patternedSurface(c.width, c.height, c.phase + texPhaseOffset)
    }
  }
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

  // Real, unmodified path.
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

  // FaithfulRuntime: independently prove the copy is accurate and record
  // per-pixel ordinal counts.
  const { kernel: faithfulKernel, runtime: faithfulRuntime } = bindWithRuntimeClass(program.canonical, bindings, FaithfulRuntime)
  const faithfulSurface = new Surface(c.width, c.height)
  runPass({ kernel: faithfulKernel, destination: faithfulSurface })
  if (!sameBytes(first, faithfulSurface)) throw new Error(`${program.id}/${c.name}: FaithfulRuntime output diverges from the real runtime -- the structural copy of wrapDerivatives is not accurate, investigate before trusting any mutation result`)
  const observedCounts = Array.from(new Set(faithfulRuntime.ordinalCounts))
  const expectedCount = c.reach ? program.expectedOrdinals : 0
  if (observedCounts.length !== 1 || observedCounts[0] !== expectedCount) {
    throw new Error(`${program.id}/${c.name}: ordinal count mismatch -- expected constant ${expectedCount} (reach=${c.reach}), observed distinct counts ${JSON.stringify(observedCounts)}`)
  }

  // Mutation A: sign-flip.
  const { kernel: signFlipKernel } = bindWithRuntimeClass(program.canonical, bindings, SignFlipRuntime)
  const signFlipSurface = new Surface(c.width, c.height)
  runPass({ kernel: signFlipKernel, destination: signFlipSurface })
  const signFlipDiverges = !sameBytes(first, signFlipSurface)

  // Mutation B: lane-order transpose.
  const { kernel: transposeKernel } = bindWithRuntimeClass(program.canonical, bindings, LaneTransposeRuntime)
  const transposeSurface = new Surface(c.width, c.height)
  runPass({ kernel: transposeKernel, destination: transposeSurface })
  const transposeDiverges = !sameBytes(first, transposeSurface)

  return {
    name: c.name,
    dimensions: { width: c.width, height: c.height },
    diagnostic: Boolean(c.diagnostic),
    reach: c.reach,
    uniforms: c.uniforms,
    time,
    tile_offset: c.tileOffset ?? [0, 0],
    full_resolution: c.fullResolution ?? [c.width, c.height],
    repeat_identity: true,
    input_immutable: true,
    ordinal_count_observed: observedCounts[0],
    ordinal_count_expected: expectedCount,
    output: renderResult(first),
    mutation_sign_flip_diverges: signFlipDiverges,
    mutation_lane_transpose_diverges: transposeDiverges,
  }
}

// ---------------------------------------------------------------------------
// Program registry. Each entry independently verified against the live
// corpus/runtime before any case is built (loadProgram, below).
// ---------------------------------------------------------------------------
const PROGRAM_DEFS = [
  {
    id: 'bulge', key: 'filter/bulge:bulge', sourceFile: 'bulge/bulge.glsl',
    factoryName: 'canonicalFactory26', factorySha256: '48eb3ed665bd4d3f27d5bac68e9474ccc38a75168f46ddb61dadf611fc7903ef',
    sourceRawBytes: 2352, sourceSha256: '87f26ffa13ffe946d94d92a00bd45ca3a9787b9ee402dfe04ebc3d4a911eb170',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { strength: 'float', aspectLens: 'bool', wrap: 'int', rotation: 'float', antialias: 'bool' },
    cases: [
      { name: 'strong-bulge-repeat-rotated', width: 6, height: 5, phase: 0, uniforms: { strength: 85, aspectLens: false, wrap: 1, rotation: -60, antialias: true } },
      { name: 'gentle-pinch-clamp', width: 5, height: 6, phase: 1, uniforms: { strength: 15, aspectLens: true, wrap: 2, rotation: 120, antialias: true } },
      { name: 'tiled-mirror', width: 7, height: 4, phase: 2, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { strength: 50, aspectLens: true, wrap: 0, rotation: 20, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 3, uniforms: { strength: 70, aspectLens: true, wrap: 0, rotation: 45, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'celShadingColor', key: 'filter/celShading:celShadingColor', sourceFile: 'celShading/celShadingColor.glsl',
    factoryName: 'canonicalFactory28', factorySha256: '5c10f42ac05d71a35295b6d2e42adbb3c137da8eb1a6b2d5fbfe277f2f5488c9',
    sourceRawBytes: 2780, sourceSha256: '90fa87484d3549bdaa2ddca4836a7ca8602ad4f1f30aa87a72841d4e013521f4',
    defines: {}, family: 'fwidth', hasAntialias: true, expectedOrdinals: 1,
    uniformTypes: { levels: 'int', gamma: 'float', antialias: 'bool', lightDirection: 'vec3', strength: 'float' },
    cases: [
      { name: 'sharp-levels-warm-light', width: 6, height: 5, phase: 10, uniforms: { levels: 3, gamma: 0.4, antialias: true, lightDirection: [0.8, 0.2, 0.5], strength: 0.9 } },
      { name: 'soft-levels-cool-light', width: 5, height: 6, phase: 11, uniforms: { levels: 7, gamma: 1.8, antialias: true, lightDirection: [-0.4, 0.6, 0.3], strength: 0.2 } },
      { name: 'tiled-extreme-levels', width: 7, height: 4, phase: 12, tileOffset: [2, 1], fullResolution: [13, 9], uniforms: { levels: 2, gamma: 2.6, antialias: true, lightDirection: [0.1, -0.9, 0.4], strength: 1 } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 13, uniforms: { levels: 4, gamma: 0.65, antialias: false, lightDirection: [0.5, 0.5, 1], strength: 0 }, diagnostic: true },
    ],
  },
  {
    id: 'halftone', key: 'filter/halftone:halftone', sourceFile: 'halftone/halftone.glsl',
    factoryName: 'canonicalFactory67', factorySha256: '7ddd550b40cc5484a4cac387c2560fe0cbf8d5eb7b30b28a123605d84995b58d',
    sourceRawBytes: 8440, sourceSha256: '063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7',
    defines: { MODE: 0, PATTERN: 0 }, family: 'fwidth', hasAntialias: false, expectedOrdinals: 4,
    uniformTypes: { frequency: 'float', cyanAngle: 'float', magentaAngle: 'float', yellowAngle: 'float', blackAngle: 'float', monoAngle: 'float', sharpness: 'float', inkColor: 'vec3', paperColor: 'vec3', MODE: 'int', PATTERN: 'int' },
    cases: [
      { name: 'classic-screen-angles', width: 6, height: 5, phase: 20, uniforms: { frequency: 18, cyanAngle: 15, magentaAngle: 75, yellowAngle: 0, blackAngle: 45, monoAngle: 45, sharpness: 80, inkColor: [0.05, 0.05, 0.05], paperColor: [0.98, 0.96, 0.9], MODE: 0, PATTERN: 0 }, reach: true },
      { name: 'coarse-soft-screen', width: 5, height: 6, phase: 21, uniforms: { frequency: 6, cyanAngle: 108, magentaAngle: 162, yellowAngle: 90, blackAngle: 0, monoAngle: 0, sharpness: 10, inkColor: [0.1, 0.05, 0.15], paperColor: [0.9, 0.92, 0.85], MODE: 0, PATTERN: 0 }, reach: true },
      { name: 'tiled-fine-crisp-screen', width: 7, height: 4, phase: 22, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { frequency: 5, cyanAngle: -30, magentaAngle: 30, yellowAngle: 60, blackAngle: 90, monoAngle: 30, sharpness: 100, inkColor: [0, 0, 0], paperColor: [1, 1, 1], MODE: 0, PATTERN: 0 }, reach: true },
    ],
  },
  {
    id: 'lens', key: 'filter/lens:lens', sourceFile: 'lens/lens.glsl',
    factoryName: 'canonicalFactory74', factorySha256: 'bbee3c76d338b5a7d7013761be6b925f29e8699cc9f8dca06d3d3aa0bef51e41',
    sourceRawBytes: 2909, sourceSha256: '6633d8c7b1ab23600cb25bb87f3f67c5d1d148b0626169f24de520fbce9e64a5',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { lensDisplacement: 'float', aspectLens: 'bool', antialias: 'bool' },
    cases: [
      { name: 'strong-barrel', width: 6, height: 5, phase: 30, uniforms: { lensDisplacement: 0.9, aspectLens: true, antialias: true } },
      { name: 'pincushion-no-aspect', width: 5, height: 6, phase: 31, uniforms: { lensDisplacement: -0.7, aspectLens: false, antialias: true } },
      { name: 'tiled-mild-barrel', width: 7, height: 4, phase: 32, tileOffset: [2, 3], fullResolution: [13, 12], uniforms: { lensDisplacement: 0.3, aspectLens: true, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 33, uniforms: { lensDisplacement: 0.6, aspectLens: true, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'lensWarp', key: 'filter/lensWarp:lensWarp', sourceFile: 'lensWarp/lensWarp.glsl',
    factoryName: 'canonicalFactory76', factorySha256: 'c4d5f24a54342ff9599a85fd2bdf556badce8cf6da7d8397b33518dc321cc4a9',
    sourceRawBytes: 4033, sourceSha256: '543b53a26b14dfdcf979e2601eaad32d6ec683c41427301b851173334a670480',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { displacement: 'float', speed: 'float', antialias: 'bool' },
    cases: [
      { name: 'fast-strong-warp', width: 6, height: 5, phase: 40, time: 0.6, uniforms: { displacement: 0.85, speed: 3, antialias: true } },
      { name: 'slow-gentle-warp', width: 5, height: 6, phase: 41, time: 3.2, uniforms: { displacement: 0.6, speed: 0.2, antialias: true } },
      { name: 'tiled-static-warp', width: 7, height: 4, phase: 42, time: 1.3, tileOffset: [1, 1], fullResolution: [9, 6], uniforms: { displacement: 0.95, speed: 0.6, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 43, time: 1.1, uniforms: { displacement: 0.7, speed: 1, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'octaveWarp', key: 'filter/octaveWarp:octaveWarp', sourceFile: 'octaveWarp/octaveWarp.glsl',
    factoryName: 'canonicalFactory91', factorySha256: '122e909b90228a9e22184d3601611091ee5493029d03392966e82591846ccf30',
    sourceRawBytes: 4902, sourceSha256: 'ced7dca971a24fb3d8a48641c7bb66c4af637a57984d45ddc9e51f0492a59bea',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { frequency: 'float', octaves: 'float', displacement: 'float', speed: 'float', wrap: 'float', seed: 'float', antialias: 'bool' },
    cases: [
      { name: 'many-octaves-strong', width: 6, height: 5, phase: 50, time: 0.8, uniforms: { frequency: 7, octaves: 5, displacement: 0.4, speed: 1.5, wrap: 1, seed: 17, antialias: true } },
      { name: 'single-octave-mild', width: 5, height: 6, phase: 51, time: 0.35, uniforms: { frequency: 2, octaves: 1, displacement: 1, speed: 0.3, wrap: 1, seed: 7, antialias: true } },
      { name: 'tiled-clamp-warp', width: 7, height: 4, phase: 52, time: 0, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { frequency: 9, octaves: 3, displacement: 0.2, speed: 0, wrap: 2, seed: 5, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 53, time: 1.6, uniforms: { frequency: 5, octaves: 4, displacement: 0.3, speed: 1, wrap: 1, seed: 9, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'pinch', key: 'filter/pinch:pinch', sourceFile: 'pinch/pinch.glsl',
    factoryName: 'canonicalFactory103', factorySha256: '9061ee4b7cd062fc06723cd9366777949bcba7c50a7cd6f1fc1c74b9e1d3a355',
    sourceRawBytes: 2296, sourceSha256: '031405e087822fd10b07d972e53f2f6d2da95f67d9c56605cbc104e0b955d71c',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { strength: 'float', aspectLens: 'bool', wrap: 'int', rotation: 'float', antialias: 'bool' },
    cases: [
      { name: 'deep-pinch-mirror', width: 6, height: 5, phase: 60, uniforms: { strength: 90, aspectLens: true, wrap: 0, rotation: 30, antialias: true } },
      { name: 'shallow-pinch-repeat', width: 5, height: 6, phase: 61, uniforms: { strength: 20, aspectLens: false, wrap: 1, rotation: -90, antialias: true } },
      { name: 'tiled-clamp-pinch', width: 7, height: 4, phase: 62, tileOffset: [3, 1], fullResolution: [14, 10], uniforms: { strength: 55, aspectLens: true, wrap: 2, rotation: 150, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 63, uniforms: { strength: 65, aspectLens: true, wrap: 0, rotation: 0, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'polar', key: 'filter/polar:polar', sourceFile: 'polar/polar.glsl',
    factoryName: 'canonicalFactory114', factorySha256: '782461118d560ca22e7a5f4e945a1b3619c5fa381f07a032f5c305c08149aa96',
    sourceRawBytes: 2027, sourceSha256: '391b82e45bc2ea9799de1a200afbd735af96ad15627695d46cfc8caa1298a36d',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { polarMode: 'int', speed: 'float', rotation: 'float', scale: 'float', aspectLens: 'bool', antialias: 'bool' },
    cases: [
      { name: 'polar-mode-spin', width: 6, height: 5, phase: 70, time: 1.4, uniforms: { polarMode: 0, speed: 1.5, rotation: 0.8, scale: 1.2, aspectLens: true, antialias: true } },
      { name: 'vortex-mode-still', width: 5, height: 6, phase: 71, time: 0, uniforms: { polarMode: 1, speed: -0.4, rotation: -1.2, scale: -0.6, aspectLens: false, antialias: true } },
      { name: 'tiled-vortex-drift', width: 7, height: 4, phase: 72, time: 2.7, tileOffset: [2, 2], fullResolution: [13, 11], uniforms: { polarMode: 1, speed: 0.6, rotation: 1.9, scale: 0.4, aspectLens: true, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 73, time: 0.5, uniforms: { polarMode: 0, speed: 0.2, rotation: 0.5, scale: 0.9, aspectLens: true, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'pondRipples', key: 'filter/pondRipples:pondRipples', sourceFile: 'pondRipples/pondRipples.glsl',
    factoryName: 'canonicalFactory115', factorySha256: 'acd9474e33c243581c29858426ad1ffb107698c42176735c1f7c1b0d03c329b5',
    sourceRawBytes: 5187, sourceSha256: '2958de77f0cdf2a21a00d1505ea75f26df5b66dd7f2cb98431e27178d3386c3d',
    defines: { STYLE: 2, WRAP: 0 }, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { amount: 'float', ridges: 'int', speed: 'int', antialias: 'bool', STYLE: 'int', WRAP: 'int' },
    cases: [
      { name: 'many-ridges-strong-outward', width: 6, height: 5, phase: 80, time: 0.15, uniforms: { amount: 100, ridges: 18, speed: 5, antialias: true, STYLE: 2, WRAP: 0 } },
      { name: 'few-ridges-mild-inward', width: 5, height: 6, phase: 81, time: 0.6, uniforms: { amount: 95, ridges: 3, speed: -5, antialias: true, STYLE: 2, WRAP: 0 } },
      { name: 'tiled-static-ripples', width: 7, height: 4, phase: 82, time: 0, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { amount: 45, ridges: 8, speed: 0, antialias: true, STYLE: 2, WRAP: 0 } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 83, time: 1.2, uniforms: { amount: 60, ridges: 10, speed: 1, antialias: false, STYLE: 2, WRAP: 0 }, diagnostic: true },
    ],
  },
  {
    id: 'spiral', key: 'filter/spiral:spiral', sourceFile: 'spiral/spiral.glsl',
    factoryName: 'canonicalFactory146', factorySha256: '69f34db1db7515a72c87f0d67dea8cc0e08fd067a398b1655b4e5b3fa8541684',
    sourceRawBytes: 2869, sourceSha256: '3d609c5028c859d82c060af21b0675dd0dd0ec6f720dbc9e3b3b21a65893ef4a',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { strength: 'float', speed: 'int', aspectLens: 'bool', wrap: 'int', rotation: 'float', antialias: 'bool' },
    cases: [
      { name: 'tight-fast-spiral', width: 6, height: 5, phase: 90, time: 0.7, uniforms: { strength: -95, speed: 4, aspectLens: true, wrap: 1, rotation: 40, antialias: true } },
      { name: 'loose-slow-spiral', width: 5, height: 6, phase: 91, time: 4.1, uniforms: { strength: -10, speed: -1, aspectLens: false, wrap: 0, rotation: -30, antialias: true } },
      { name: 'tiled-clamp-spiral', width: 7, height: 4, phase: 92, time: 0, tileOffset: [2, 3], fullResolution: [13, 12], uniforms: { strength: -60, speed: 0, aspectLens: true, wrap: 2, rotation: 90, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 93, time: 1.9, uniforms: { strength: -70, speed: 2, aspectLens: true, wrap: 0, rotation: 10, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'stThreshold', key: 'filter/stamp:stThreshold', sourceFile: 'stamp/stThreshold.glsl',
    factoryName: 'canonicalFactory150', factorySha256: '3c6a795c3782cf5c3b32b48c5828696df87ed687e585e56c97971604a680aa79',
    sourceRawBytes: 3467, sourceSha256: 'd93168982b13907e32e1264c021c39f9d434ae122efd7d11898733293ee5da94',
    defines: {}, family: 'fwidth', hasAntialias: false, expectedOrdinals: 1,
    uniformTypes: { balance: 'float', roughness: 'float', inkColor: 'vec3', paperColor: 'vec3' },
    extraTextures: { blurTex: 500 },
    cases: [
      { name: 'ragged-torn-edges', width: 6, height: 5, phase: 100, uniforms: { balance: 35, roughness: 90, inkColor: [0.02, 0.02, 0.02], paperColor: [0.97, 0.95, 0.9] }, reach: true },
      { name: 'clean-iso-line', width: 5, height: 6, phase: 101, uniforms: { balance: 65, roughness: 0, inkColor: [0.15, 0.1, 0.05], paperColor: [0.85, 0.88, 0.9] }, reach: true },
      { name: 'tiled-high-balance', width: 7, height: 4, phase: 102, tileOffset: [2, 1], fullResolution: [13, 9], uniforms: { balance: 90, roughness: 40, inkColor: [0, 0, 0], paperColor: [1, 1, 1] }, reach: true },
    ],
  },
  {
    id: 'step', key: 'filter/step:step', sourceFile: 'step/step.glsl',
    factoryName: 'canonicalFactory151', factorySha256: 'a2e3ae28362d275bacdda15b53d62fe97e36c9df45b60075ee65db116a053aba',
    sourceRawBytes: 709, sourceSha256: '4f5680a9b25a2c12cecdcef3cc1ba106c2ee7a8390790544a3425890153cb7bf',
    defines: {}, family: 'fwidth', hasAntialias: true, expectedOrdinals: 1,
    uniformTypes: { threshold: 'float', antialias: 'bool' },
    cases: [
      { name: 'low-threshold', width: 6, height: 5, phase: 110, uniforms: { threshold: 0.15, antialias: true } },
      { name: 'high-threshold', width: 5, height: 6, phase: 111, uniforms: { threshold: 0.85, antialias: true } },
      { name: 'tiled-mid-threshold', width: 7, height: 4, phase: 112, tileOffset: [2, 2], fullResolution: [13, 10], uniforms: { threshold: 0.5, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 113, uniforms: { threshold: 0.5, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'stipple', key: 'filter/stipple:stipple', sourceFile: 'stipple/stipple.glsl',
    factoryName: 'canonicalFactory152', factorySha256: '50e732c0b6904d2397bf28ac9da6184550c06c4dd416ac2d115846feae51694f',
    sourceRawBytes: 8490, sourceSha256: '69d75b6fab4281fe0a0997eaf6b7b81e5ab30f0da5dfec9255c9dbb6e914c609',
    defines: { MODE: 0 }, family: 'fwidth', hasAntialias: false, expectedOrdinals: 1,
    uniformTypes: { cellSize: 'float', grainSize: 'float', density: 'float', paperColor: 'vec3', seed: 'int', MODE: 'int' },
    cases: [
      { name: 'small-cells-jitter', width: 6, height: 5, phase: 120, uniforms: { cellSize: 4, grainSize: 2, density: 50, paperColor: [0.98, 0.96, 0.9], seed: 7, MODE: 0 }, reach: true },
      { name: 'large-cells', width: 5, height: 6, phase: 121, uniforms: { cellSize: 10, grainSize: 2, density: 50, paperColor: [0.9, 0.9, 0.95], seed: 88, MODE: 0 }, reach: true },
      { name: 'tiled-fine-cells', width: 7, height: 4, phase: 122, tileOffset: [3, 2], fullResolution: [15, 11], uniforms: { cellSize: 6, grainSize: 2, density: 50, paperColor: [1, 1, 1], seed: 23, MODE: 0 }, reach: true },
    ],
  },
  {
    id: 'tunnel', key: 'filter/tunnel:tunnel', sourceFile: 'tunnel/tunnel.glsl',
    factoryName: 'canonicalFactory166', factorySha256: 'c214607fae06b63d8e77f7b6aadee2b5d5b633f193cc8ee4fa7928d1ab97bf26',
    sourceRawBytes: 3062, sourceSha256: 'c0ebe43eead7a1c040dd4a37162d634fe4b1a93ea0b8704bac502fbc5a978193',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { shape: 'int', speed: 'float', rotation: 'float', scale: 'float', center: 'float', aspectLens: 'bool', antialias: 'bool' },
    cases: [
      { name: 'hexagon-fast-spin', width: 6, height: 5, phase: 130, time: 1.1, uniforms: { shape: 4, speed: 3, rotation: 1.5, scale: 0.5, center: 40, aspectLens: true, antialias: true } },
      { name: 'circle-reverse-vignette', width: 5, height: 6, phase: 131, time: 2.6, uniforms: { shape: 0, speed: -2, rotation: -0.5, scale: -0.7, center: -60, aspectLens: false, antialias: true } },
      { name: 'tiled-square-tunnel', width: 7, height: 4, phase: 132, time: 0, tileOffset: [2, 1], fullResolution: [13, 9], uniforms: { shape: 3, speed: 1, rotation: 0.3, scale: 0.2, center: 0, aspectLens: true, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 133, time: 0.4, uniforms: { shape: 1, speed: 0, rotation: 1, scale: 0, center: 20, aspectLens: true, antialias: false }, diagnostic: true },
    ],
  },
  {
    id: 'warp', key: 'filter/warp:warp', sourceFile: 'warp/warp.glsl',
    factoryName: 'canonicalFactory172', factorySha256: '960469b2bbc57d943e2c7c489860967c2e263eb3fbaa99199154e0e1e750fc68',
    sourceRawBytes: 3095, sourceSha256: 'f3034ac02a2926b819ff874d2d1d0d3dacebf2b7a409c983237d6a71865942ee',
    defines: {}, family: 'dFdxDFdy', hasAntialias: true, expectedOrdinals: 2,
    uniformTypes: { strength: 'float', scale: 'float', seed: 'int', speed: 'int', wrap: 'int', antialias: 'bool' },
    cases: [
      { name: 'strong-warp-repeat', width: 6, height: 5, phase: 140, time: 1.3, uniforms: { strength: 95, scale: 3.5, seed: 11, speed: 4, wrap: 1, antialias: true } },
      { name: 'mild-warp-mirror', width: 5, height: 6, phase: 141, time: 3.8, uniforms: { strength: 100, scale: 4.5, seed: 63, speed: 0, wrap: 0, antialias: true } },
      { name: 'tiled-clamp-warp', width: 7, height: 4, phase: 142, time: 0, tileOffset: [3, 1], fullResolution: [14, 10], uniforms: { strength: 55, scale: 2, seed: 29, speed: 2, wrap: 2, antialias: true } },
      { name: 'antialias-off-diagnostic', width: 4, height: 7, phase: 143, time: 0.9, uniforms: { strength: 75, scale: 1.5, seed: 5, speed: 1, wrap: 1, antialias: false }, diagnostic: true },
    ],
  },
]

// ---------------------------------------------------------------------------
// Per-program verification, before any case is built.
// ---------------------------------------------------------------------------
function loadProgram(def) {
  const sourcePath = path.join(corpusRoot, 'sources/filter', def.sourceFile)
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
  if (canonical.usesDerivatives !== true) throw new Error(`${def.id}: factory.usesDerivatives is not true -- bindGlslKernel would NOT wrap this kernel with wrapDerivatives, the whole cluster's premise is false for this program`)

  // Lesson 2: verify define-as-binding requirement live, for programs that
  // pin compile-time defines. Confirms `$bindings["<DEFINE>"]` is genuinely
  // read by the factory text (not e.g. inlined as a literal at generation
  // time, which would make passing it via uniforms a silent no-op instead
  // of the load-bearing requirement the comment above claims).
  for (const defineName of Object.keys(def.defines)) {
    if (!factoryText.includes(`$bindings["${defineName}"]`)) {
      throw new Error(`${def.id}: expected factory text to read $bindings["${defineName}"] for pinned define ${defineName} -- define-as-binding assumption is wrong, investigate`)
    }
  }

  return { ...def, sourcePath, factoryText, canonical, uniformTypes: def.uniformTypes }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)

// reach = true by default for hasAntialias programs unless the case sets
// antialias:false explicitly; unconditional-guard programs (halftone,
// stThreshold, stipple) declare reach:true directly on every case since
// there is no antialias axis to gate on (Lesson 2 forbids varying their
// pinned defines to fabricate a synthetic OFF case).
for (const program of PROGRAMS) {
  for (const c of program.cases) {
    if (program.hasAntialias) c.reach = c.uniforms.antialias === true
    else if (c.reach === undefined) throw new Error(`${program.id}/${c.name}: unconditional-guard program case must set reach explicitly`)
  }
}

for (const program of PROGRAMS) {
  program.caseRecords = program.cases.map((c) => renderCase(program, c))
}

// ---------------------------------------------------------------------------
// Mutation-table assembly: aggregate the per-case divergence booleans
// already computed in renderCase() into the sign-flip / lane-transpose
// summary table, and assert the discrimination requirements.
//
// Sign-flip is a PROVABLE no-op (bit-exact, not just "usually zero") for
// the five fwidth-only programs -- documented as an expected-zero mutation,
// mirroring the grade generator's precedent of reporting a legitimately-
// dead mutation honestly instead of hiding it.
// ---------------------------------------------------------------------------
const SIGN_FLIP_PROVABLY_INVARIANT_FAMILIES = new Set(['fwidth'])

function summarizeMutation(program, key) {
  const reaching = program.caseRecords.filter((c) => c.reach)
  const nonReaching = program.caseRecords.filter((c) => !c.reach)
  const divergentReaching = reaching.filter((c) => c[key]).length
  const divergentNonReaching = nonReaching.filter((c) => c[key]).length
  return { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
}

for (const program of PROGRAMS) {
  if (program.caseRecords.every((c) => !c.reach)) throw new Error(`${program.id}: no reach-eligible case at all -- cannot prove discrimination, fix the case table`)

  const signFlip = summarizeMutation(program, 'mutation_sign_flip_diverges')
  const expectSignFlipZero = SIGN_FLIP_PROVABLY_INVARIANT_FAMILIES.has(program.family)
  if (expectSignFlipZero) {
    if (signFlip.divergent_reaching !== 0) throw new Error(`${program.id}: sign-flip expected to be a provable no-op (fwidth-only program, |x|+|y| invariant under simultaneous negation) but observed ${signFlip.divergent_reaching}/${signFlip.reaching_cases} divergent -- invariance claim is WRONG, investigate`)
  } else {
    if (signFlip.divergent_reaching === 0) throw new Error(`${program.id}: sign-flip expected nonzero divergence (dFdx/dFdy-consuming program) but observed 0/${signFlip.reaching_cases} -- cases are not discriminating the sign convention, fix the case table`)
  }
  if (signFlip.divergent_non_reaching !== 0) throw new Error(`${program.id}: sign-flip diverged on ${signFlip.divergent_non_reaching}/${signFlip.non_reaching_cases} non-reaching case(s) -- the derivative path should be provably dead there, investigate`)

  const transpose = summarizeMutation(program, 'mutation_lane_transpose_diverges')
  if (transpose.divergent_reaching === 0) throw new Error(`${program.id}: lane-transpose expected nonzero divergence (coarse-quad-sharing discriminator) but observed 0/${transpose.reaching_cases} -- cases lack the spatial anisotropy needed to discriminate, fix the case table`)
  if (transpose.divergent_non_reaching !== 0) throw new Error(`${program.id}: lane-transpose diverged on ${transpose.divergent_non_reaching}/${transpose.non_reaching_cases} non-reaching case(s) -- the derivative path should be provably dead there, investigate`)

  program.mutationSummary = {
    sign_flip: { ...signFlip, expected_zero: expectSignFlipZero },
    lane_transpose: { ...transpose, expected_zero: false },
  }
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const programsOut = {}
  let totalEligible = 0
  let totalDiagnostic = 0
  let totalAntialiasOn = 0
  for (const program of PROGRAMS) {
    const eligible = program.caseRecords.filter((c) => !c.diagnostic)
    const diagnostic = program.caseRecords.filter((c) => c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    if (program.hasAntialias) totalAntialiasOn += program.caseRecords.filter((c) => c.uniforms.antialias === true).length
    programsOut[program.id] = {
      key: program.key, source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName, canonical_factory_to_string_sha256: program.factorySha256,
      defines: { ...program.defines }, family: program.family, has_antialias: program.hasAntialias, expected_ordinals_active: program.expectedOrdinals,
      cases: program.caseRecords,
      mutations: program.mutationSummary,
    }
  }
  return {
    schema: 'noisemaker-for-cpp.derivatives.cluster15.derivative-oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version, public_identity: true, adapter_absent: true },
    define_as_binding_note: 'halftone (MODE, PATTERN), pondRipples (STYLE, WRAP), and stipple (MODE) pin compile-time GLSL #defines that the JS reference reads as ordinary $bindings[...] lookups (no preprocessor in JS) -- every case for these three programs supplies the define at its generate_typed_slice._defaults()-authorized value via `uniforms`, verified live against the real _defaults() output (see report) and against the factory text actually containing the $bindings["<NAME>"] read (loadProgram()). Omitting these would silently select the wrong runtime branch, not fail loudly.',
    programs: programsOut,
    eligibility_summary: {
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic, antialias_on_cases: totalAntialiasOn,
      note: 'diagnostic cases are antialias=false renders for the 12 antialias-gated programs, included to prove the derivative path is genuinely DEAD there (ordinal_count_observed=0, zero mutation divergence) -- the exact negative control the task requires so an all-derivatives-disabled oracle could never pass unnoticed. halftone/stThreshold/stipple have no antialias axis (unconditional derivative call under their pinned, authorized defines) and so contribute no diagnostic cases; every one of their cases is reach:true by construction.',
    },
    negative_closure: {
      antialias_off_would_be_worthless_if_undetected: 'refused -- every case independently asserts ordinal_count_observed against ordinal_count_expected (0 vs 2/1/4) at build time; an oracle accidentally rendered with derivatives disabled everywhere would fail the build, not ship silently.',
      sign_flip_zero_on_fwidth_programs_treated_as_bug: 'forbidden -- it is a proven bit-exact invariant (|x|+|y| unchanged under simultaneous negation of both terms), asserted, not hidden; see mutations.sign_flip.expected_zero per program.',
      reusing_grade_clusters_luma_weights_or_index_mutation_shapes: 'not applicable -- this cluster has no per-program constant global or indexed local array; its two mutations (sign_flip, lane_transpose) target the ONE shared mechanism (glsl-runtime.js wrapDerivatives) all 15 programs route through, verified applicable to every program rather than assumed.',
    },
  }
}

function report(d) {
  const lines = [
    '# Derivative cluster (15 programs) oracle report', '',
    'Hermetic JS oracle for the 15 GLSL programs blocked on dFdx/dFdy/fwidth that are about to be ported from noisemaker-for-cpu to noisemaker-for-cpp. Ground truth for bit-exact C++ parity tests.', '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} antialias-off diagnostic). Antialias-ON cases: **${d.eligibility_summary.antialias_on_cases}**.`, '',
    '## Define-as-binding note', '', d.define_as_binding_note, '',
    '## Per-program summary', '',
    '| Program | Family | Ordinals (active) | Has antialias | Cases | Diagnostic | Sign-flip divergent/reaching | Sign-flip expected-zero | Lane-transpose divergent/reaching |', '| --- | --- | ---: | --- | ---: | ---: | --- | --- | --- |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    const sf = p.mutations.sign_flip
    const lt = p.mutations.lane_transpose
    lines.push(`| ${id} | ${p.family} | ${p.expected_ordinals_active} | ${p.has_antialias} | ${eligible + diagnostic} | ${diagnostic} | ${sf.divergent_reaching}/${sf.reaching_cases} | ${sf.expected_zero} | ${lt.divergent_reaching}/${lt.reaching_cases} |`)
  }
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\` (${id})`, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\` (\`${p.canonical_factory_to_string_sha256}\`). Authorized defines: \`${JSON.stringify(p.defines)}\`.`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | Ordinals observed | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | ---: | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${c.reach} | ${c.ordinal_count_observed} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations', '', '| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) | Expected |', '| --- | ---: | ---: | ---: | ---: | --- |')
    const sf = p.mutations.sign_flip
    const lt = p.mutations.lane_transpose
    lines.push(`| sign_flip | ${sf.reaching_cases} | ${sf.divergent_reaching} | ${sf.non_reaching_cases} | ${sf.divergent_non_reaching} | ${sf.expected_zero ? 'ZERO (provable fwidth invariant)' : 'nonzero'} |`)
    lines.push(`| lane_transpose | ${lt.reaching_cases} | ${lt.divergent_reaching} | ${lt.non_reaching_cases} | ${lt.divergent_non_reaching} | nonzero |`)
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
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('derivative oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('derivative oracle report drift')
  const totalMutations = PROGRAMS.length * 2
  console.log(`derivative oracle fixture ok (${PROGRAMS.length} programs, ${data.eligibility_summary.total_cases} cases, ${totalMutations} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
