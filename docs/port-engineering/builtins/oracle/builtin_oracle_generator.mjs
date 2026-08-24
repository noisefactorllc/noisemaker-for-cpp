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
// "Builtin admission" cluster oracle -- 6 GLSL programs blocked (today, or
// after a documented, unlanded const-global-admission widening) on exactly
// one of three GLSL builtins the C++20 generator does not yet admit by
// node-identity: `round`, `any`, `reflect`
// (`docs/port-engineering/REMAINING-WORK-ROADMAP.md`, "Builtin
// admission (round/any/reflect) -- 3 singletons"). This generator is the
// JS-golden ground truth the C++ port's tests will assert against,
// bit-exactly. House style follows
// `docs/port-engineering/future-precompute/task32-grade/grade_oracle_generator.mjs`
// (hermetic imports, --check determinism, per-case mutation testing, an
// explicit intent-verification guard) and
// `docs/port-engineering/derivatives/oracle/derivative_oracle_generator.mjs`
// (mutating the SHARED RUNTIME MECHANISM rather than per-program source
// text, because `round`/`any`/`reflect` are stdlib entries in
// `GlslCpuRuntime`'s `#createStdlib()` -- glsl-runtime.js:216-431 -- shared
// by every program that calls them, not program-local closures).
//
// THE 6 PROGRAMS:
//   filter/posterize:posterize  -- round   (60:34 raw; reachable, unconditional)
//   filter/waves:waves          -- any     (41:9 raw;  reachable, unconditional, called twice)
//   filter/lighting:lighting    -- reflect (93:26 raw; reachable iff reflection>0 || aberration>0)
//   filter/fxaa:fxaa            -- round   (blocked TODAY on a global decl;
//                                            round becomes terminal once that
//                                            lands -- relaxed_global_probe.json)
//   filter/grain:grain          -- round   (same relaxed-global situation)
//   filter/snow:snow            -- round   (same relaxed-global situation --
//                                            but see the dead-code finding below)
//
// THREE HARD-WON LESSONS CARRIED OVER VERBATIM from grade/derivatives:
//   1. RESERVED TOP-LEVEL KEYS. `createCanonicalBindings` (glsl-kernel.js
//      :20-61) assigns nine canonical keys (resolution, fullResolution,
//      tileOffset, aspectRatio, aspect, time, globalTime, deltaTime, frame)
//      AFTER spreading `...uniforms`, so passing any of them *inside* the
//      uniforms object silently discards the caller's intended value. Every
//      case here is rendered through `renderCase()`, which refuses to build
//      if the uniforms object illegally contains one of these keys, and
//      independently reconstructs the bindings to assert the kernel's own
//      bound `tileOffset`/`fullResolution`/`time` -- AND every declared
//      uniform -- equal the CALLER's intended values (glsl-kernel.js's
//      spread-order hazard has already frozen four wrong expectations once).
//   2. DEFINES ARE BOUND AS UNIFORMS, NOT PREPROCESSED. Verified live below
//      via `generate_typed_slice._defaults()`: all six programs compile at
//      exact defines `{}` (no #define/#ifdef besides the universal `#ifdef
//      GL_ES` guard), so there is no "different define map" axis for this
//      cluster -- documented explicitly, not fabricated.
//   3. REACHABILITY MUST BE PROVEN, NOT ASSUMED. Unlike the grade/derivative
//      clusters, three of these six programs (`fxaa`, `grain`, `snow`) reveal
//      a genuinely new hazard on inspection: their `round()` call site(s)
//      structurally can ONLY ever receive an already-integer float32 (image
//      width/height, `Number.isInteger`-guaranteed by createCanonicalBindings)
//      -- so no full-render pixel case can ever exercise a genuine `.5` tie
//      there, REGARDLESS of which rounding convention is correct. Worse,
//      `snow`'s `as_u32()` (the sole function that calls `round()`) is
//      declared but **never called from `main()` at all** -- verified by
//      grep against both the raw GLSL source and the compiled JS factory
//      text, and independently reconfirmed at runtime via an instrumented
//      call-log (zero `round()` invocations recorded for every snow case).
//      This oracle treats these as first-class findings, proven with
//      evidence and machine-asserted zero divergence, not silently dropped.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'builtin-oracles.json')
const reportPath = path.join(here, 'builtin-oracle-report.md')
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
function isVectorLocal(value) { return ArrayBuffer.isView(value) || Array.isArray(value) }

// ---------------------------------------------------------------------------
// Runtime/catalog hermeticity pinning -- identical file set AND identical
// hash VALUES to the grade and derivative generators (same repo state),
// independently recomputed here, not copy-pasted trust.
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
// Mutation runtimes. Each subclasses the REAL, unmodified GlslCpuRuntime and
// replaces exactly ONE stdlib entry post-construction (`this.stdlib` is a
// plain writable instance property; the frozen object it points to is
// simply swapped for a new one -- verified safe, see probe transcript in the
// report). Every mutated closure that needs `subtract`/`multiply`/`dot`/
// `normalize`/`add` reuses the REAL runtime's own per-component F32-rounding
// implementations of those (captured before the swap), so the ONLY thing
// that changes is the one deliberate hazard -- never the surrounding
// arithmetic precision.
//
// `round`/`any`/`reflect` are called SCALAR-only (round), VECTOR-only
// (any, reflect) across all six programs in this cluster -- confirmed by
// reading every call site in every compiled factory text below -- so the
// mutated closures do not need to replicate `GlslCpuRuntime#unary`'s
// vector-broadcast branch.
// ---------------------------------------------------------------------------
function bankersRound(v) {
  const fl = Math.floor(v)
  const d = v - fl
  if (d < 0.5) return fl
  if (d > 0.5) return fl + 1
  return (fl % 2 === 0) ? fl : fl + 1 // exact tie: round to even
}
function awayFromZeroRound(v) { return Math.sign(v) * Math.floor(Math.abs(v) + 0.5) }
function floorPlusHalfRound(v) { return Math.floor(v + 0.5) }

class RoundMinusOneRuntime extends GlslCpuRuntime {
  // General reachability/liveness discriminator: round(x) -> round(x) - 1,
  // for EVERY input (tie or not). Distinguishes "round() genuinely executes
  // and its result is load-bearing" from the tie-break-specific mutations
  // below, which are legitimately no-ops on the always-integer inputs fxaa
  // and grain feed round() -- see the module header.
  constructor() { super(); const real = this.stdlib; this.stdlib = Object.freeze({ ...real, round: (v) => Math.fround(real.round(v) - 1) }) }
}
class RoundBankersRuntime extends GlslCpuRuntime {
  // The GLSL-SPEC-COMPLIANT (round-half-to-even / "banker's rounding")
  // materialization -- deliberately WRONG here, because the JS reference
  // uses `Math.round` (round-half-towards-+Infinity), not the spec's
  // tie-break rule. This is the mutation that catches "I implemented round()
  // per the GLSL spec" as a bug.
  constructor() { super(); const real = this.stdlib; this.stdlib = Object.freeze({ ...real, round: (v) => Math.fround(bankersRound(v)) }) }
}
class RoundAwayFromZeroRuntime extends GlslCpuRuntime {
  // The "naive C++ round()" materialization (round-half-away-from-zero,
  // i.e. what `std::round` actually does) -- deliberately WRONG here for
  // the same reason. Catches "I used std::round() directly" as a bug.
  constructor() { super(); const real = this.stdlib; this.stdlib = Object.freeze({ ...real, round: (v) => Math.fround(awayFromZeroRound(v)) }) }
}
class RoundFloorPlusHalfRuntime extends GlslCpuRuntime {
  // The subtle "obviously correct" C++ idiom `std::floor(x + 0.5f)` --
  // matches Math.round's VALUE everywhere except at exactly x = -0.5, where
  // it silently returns +0 instead of -0 (see report: "-0.5 + 0.5" is
  // computed by IEEE754 addition of two exactly-canceling operands, which
  // rounds to +0, not -0). A direct-row-only discriminator: no full-render
  // call site in this cluster can reach x = -0.5 (see reachability notes).
  constructor() { super(); const real = this.stdlib; this.stdlib = Object.freeze({ ...real, round: (v) => Math.fround(floorPlusHalfRound(v)) }) }
}

class AnyAsAllRuntime extends GlslCpuRuntime {
  // Plausible real bug: any/all confusion (AND-reduction instead of OR).
  constructor() {
    super()
    const real = this.stdlib
    const mutated = (value) => { for (let i = 0; i < value.length; i += 1) if (!value[i]) return false; return true }
    this.stdlib = Object.freeze({ ...real, any: mutated })
  }
}
class AnyReverseOrderRuntime extends GlslCpuRuntime {
  // Same OR-reduction, iterated in reverse -- tests whether short-circuit
  // ORDER (not the boolean value) leaks into observable output. Since every
  // input to `any()` in this cluster is a fully-materialized, side-effect-
  // free Float32Array (produced by `notEqual()` before `any()` is ever
  // called), order cannot matter -- expected zero divergence everywhere,
  // proven below rather than assumed.
  constructor() {
    super()
    const real = this.stdlib
    const mutated = (value) => { for (let i = value.length - 1; i >= 0; i -= 1) if (value[i]) return true; return false }
    this.stdlib = Object.freeze({ ...real, any: mutated })
  }
}

class ReflectSignFlipRuntime extends GlslCpuRuntime {
  // I - 2*dot(N,I)*N -> I + 2*dot(N,I)*N. The sign-convention bug the
  // architecture doc calls out explicitly.
  constructor() {
    super()
    const real = this.stdlib
    const mutated = (incident, normal) => real.add(incident, real.multiply(normal, 2 * real.dot(normal, incident)))
    this.stdlib = Object.freeze({ ...real, reflect: mutated })
  }
}
class ReflectAutoNormalizeRuntime extends GlslCpuRuntime {
  // Defensively normalizes N before applying the formula -- GLSL's spec
  // says the CALLER must pass a normalized N and reflect() must NOT do it
  // itself; a C++ port that "helpfully" normalizes defensively diverges
  // whenever N is not already unit length.
  constructor() {
    super()
    const real = this.stdlib
    const mutated = (incident, normal) => {
      const n = real.normalize(normal)
      return real.subtract(incident, real.multiply(n, 2 * real.dot(n, incident)))
    }
    this.stdlib = Object.freeze({ ...real, reflect: mutated })
  }
}

class InstrumentedRuntime extends GlslCpuRuntime {
  // Pass-through (zero behavior change) wrapper around round/any/reflect
  // that records every call's arguments. Used to (a) independently prove
  // the wrapper is behavior-preserving (its rendered output must be
  // bit-identical to the real, unmodified runtime), and (b) prove
  // reachability -- or non-reachability, for `snow` -- by call count,
  // rather than inferring it from source-reading alone.
  constructor() {
    super()
    const real = this.stdlib
    this.callLog = { round: [], any: [], reflect: [] }
    const record = (name, fn) => (...args) => {
      this.callLog[name].push(args.map((a) => (isVectorLocal(a) ? Array.from(a) : a)))
      return fn(...args)
    }
    this.stdlib = Object.freeze({ ...real, round: record('round', real.round), any: record('any', real.any), reflect: record('reflect', real.reflect) })
  }
}

function bindWithRuntimeClass(factory, bindings, RuntimeClass) {
  // Mirrors bindGlslKernel (glsl-runtime.js:549-556) exactly, generalized to
  // accept a runtime CLASS instead of hardcoding `new GlslCpuRuntime()`.
  const runtime = new RuntimeClass()
  let kernel = factory(Object.freeze({ ...bindings }), runtime)
  if (factory.usesDerivatives) kernel = runtime.wrapDerivatives(kernel)
  return { kernel, runtime }
}

// ---------------------------------------------------------------------------
// Deterministic patterned input texture -- identical construction to the
// grade/derivative generators, so R/G/B/A genuinely differ per pixel and no
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
    else if (type === 'vec2' || type === 'vec3' || type === 'vec4') out[k] = new Float32Array(v.map(f))
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
}

// ---------------------------------------------------------------------------
// renderCase: the single rendering path every case goes through.
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

  // InstrumentedRuntime: independently prove the pass-through wrapper is
  // accurate (bit-identical to the real runtime) and capture the call log
  // that proves (or disproves) reachability of this program's builtin.
  const { kernel: instrKernel, runtime: instrRuntime } = bindWithRuntimeClass(program.canonical, bindings, InstrumentedRuntime)
  const instrSurface = new Surface(c.width, c.height)
  runPass({ kernel: instrKernel, destination: instrSurface })
  if (!sameBytes(first, instrSurface)) throw new Error(`${program.id}/${c.name}: InstrumentedRuntime output diverges from the real runtime -- the pass-through wrapper is not accurate, investigate before trusting any mutation result`)
  const callCount = instrRuntime.callLog[program.builtin].length
  const expectReach = Boolean(c.reach)
  if (expectReach && callCount === 0) throw new Error(`${program.id}/${c.name}: reach=true declared but zero "${program.builtin}" calls recorded -- reach predicate is wrong`)
  if (!expectReach && callCount !== 0) throw new Error(`${program.id}/${c.name}: reach=false declared but ${callCount} "${program.builtin}" call(s) recorded -- reach predicate is wrong`)

  // Mutation table: run every mutation this program's builtin family
  // defines, record divergence.
  const mutationResults = {}
  for (const mutation of program.mutations) {
    const { kernel: mutKernel } = bindWithRuntimeClass(program.canonical, bindings, mutation.RuntimeClass)
    const mutSurface = new Surface(c.width, c.height)
    runPass({ kernel: mutKernel, destination: mutSurface })
    mutationResults[mutation.id] = !sameBytes(first, mutSurface)
  }

  return {
    name: c.name,
    dimensions: { width: c.width, height: c.height },
    diagnostic: Boolean(c.diagnostic),
    reach: expectReach,
    builtin_call_count: callCount,
    builtin_call_args: instrRuntime.callLog[program.builtin],
    uniforms: c.uniforms,
    time,
    tile_offset: c.tileOffset ?? [0, 0],
    full_resolution: c.fullResolution ?? [c.width, c.height],
    repeat_identity: true,
    input_immutable: true,
    output: renderResult(first),
    mutation_diverges: mutationResults,
  }
}

// ---------------------------------------------------------------------------
// Program registry.
// ---------------------------------------------------------------------------
const ROUND_MUTATIONS = [
  { id: 'round-minus-one-liveness', kind: 'round', RuntimeClass: RoundMinusOneRuntime, hazard: 'general-liveness', description: 'round(x) -> round(x) - 1 for every input, tie or not. Proves the call site genuinely executes and its result is load-bearing -- independent of the tie-break question.' },
  { id: 'round-bankers-spec-tiebreak', kind: 'round', RuntimeClass: RoundBankersRuntime, hazard: 'wrong-tiebreak-rule-glsl-spec', description: 'round(x) -> round-half-to-even ("banker\'s rounding", the GLSL SPEC\'s tie-break rule). The JS reference materializes round() as Math.round (round-half-towards-+Infinity), NOT the spec\'s rule -- this mutation catches a spec-faithful-but-wrong C++ implementation.' },
  { id: 'round-away-from-zero-naive-cpp', kind: 'round', RuntimeClass: RoundAwayFromZeroRuntime, hazard: 'wrong-tiebreak-rule-naive-cpp', description: 'round(x) -> round-half-away-from-zero (what std::round actually does). Catches "I called std::round() directly" as a bug.' },
]
const ANY_MUTATIONS = [
  { id: 'any-as-all-confusion', kind: 'any', RuntimeClass: AnyAsAllRuntime, hazard: 'any-all-confusion', description: 'any(v) -> all(v) (AND-reduction instead of OR). Diverges exactly when the input vector is neither all-true nor all-false.' },
  { id: 'any-reverse-iteration-order', kind: 'any', RuntimeClass: AnyReverseOrderRuntime, hazard: 'order-dependence-probe', description: 'Same OR-reduction, iterated last-to-first. Proves the short-circuit ORDER does not leak into observable output (expected zero divergence everywhere, proven not assumed).' },
]
const REFLECT_MUTATIONS = [
  { id: 'reflect-sign-flip', kind: 'reflect', RuntimeClass: ReflectSignFlipRuntime, hazard: 'wrong-sign-convention', description: 'reflect(I,N) = I - 2*dot(N,I)*N -> I + 2*dot(N,I)*N. The sign-convention bug the architecture doc calls out.' },
  { id: 'reflect-defensive-normalize', kind: 'reflect', RuntimeClass: ReflectAutoNormalizeRuntime, hazard: 'defensive-internal-normalize', description: 'reflect(I,N) internally normalizes N before applying the formula. GLSL\'s reflect() must NOT do this (spec requires the CALLER to pass unit N); diverges whenever N is not already unit length.' },
]

const PROGRAM_DEFS = [
  {
    id: 'posterize', key: 'filter/posterize:posterize', sourceFile: 'posterize/posterize.glsl',
    factoryName: 'canonicalFactory116', factorySha256: '317e38c428bda5e89258c3bc64cae3fbfb54ffa43e0b02f98b2329f542c546ed',
    sourceRawBytes: 2630, sourceSha256: '460910a8d1103eca5cc0b4df82f39fd91fbc447b9a815250ae7d34dfab8ee5b2',
    builtin: 'round', mutations: ROUND_MUTATIONS,
    uniformTypes: { levels: 'float', gamma: 'float', antialias: 'bool' },
    reachabilityNote: 'round(levels_raw) at line 65 executes unconditionally, every pixel, before the antialias branch -- always reachable. levels_raw = max(levels, 0.0), so this call site can NEVER receive a negative input: round-half-away-from-zero and Math.round agree on every non-negative real, so the away-from-zero mutation is a PROVABLE (and proven, below) no-op for every posterize case, regardless of whether levels lands on a tie.',
    cases: [
      { name: 'half-tie-2.5-discriminates-bankers', width: 6, height: 5, phase: 800, reach: true, uniforms: { levels: 2.5, gamma: 1.2, antialias: true } },
      { name: 'half-tie-6.5-discriminates-bankers-antialias-off', width: 5, height: 6, phase: 801, reach: true, uniforms: { levels: 6.5, gamma: 0.7, antialias: false } },
      { name: 'ordinary-levels-no-tie-sanity', width: 7, height: 4, phase: 802, tileOffset: [1, 1], fullResolution: [9, 6], reach: true, uniforms: { levels: 4, gamma: 2.2, antialias: true } },
      { name: 'min-levels-tie-absorbed-diagnostic', width: 4, height: 7, phase: 803, reach: true, diagnostic: true, uniforms: { levels: 0.5, gamma: 1.5, antialias: true } },
    ],
  },
  {
    id: 'waves', key: 'filter/waves:waves', sourceFile: 'waves/waves.glsl',
    factoryName: 'canonicalFactory176', factorySha256: '4a289d05076a7588ced250d307eeaf8d8d0b1628bd5fc907ea71481b02ed2ae5',
    sourceRawBytes: 2622, sourceSha256: 'f4cddf1b3a6c9c68aa677b6743af313e1cdb2bf0a857ce9a1c13edc80f54e3aa',
    builtin: 'any', mutations: ANY_MUTATIONS,
    uniformTypes: { strength: 'float', scale: 'float', speed: 'int', wrap: 'int', rotation: 'float', antialias: 'bool' },
    reachabilityNote: 'any(notEqual(tileOffset, vec2(0.0))) is called TWICE per pixel (lines 48 and 74), unconditionally -- always reachable regardless of tileOffset value.',
    cases: [
      { name: 'tile-zero-any-false', width: 6, height: 5, phase: 810, tileOffset: [0, 0], fullResolution: [6, 5], reach: true, uniforms: { strength: 40, scale: 2.5, speed: 1, wrap: 1, rotation: 15, antialias: true } },
      { name: 'tile-x-only-any-true-one-lane', width: 5, height: 6, phase: 811, tileOffset: [2, 0], fullResolution: [9, 8], reach: true, uniforms: { strength: -30, scale: 1.5, speed: 0, wrap: 0, rotation: -40, antialias: true } },
      { name: 'tile-y-only-any-true-other-lane', width: 7, height: 4, phase: 812, tileOffset: [0, 3], fullResolution: [11, 9], reach: true, uniforms: { strength: 55, scale: 3, speed: 2, wrap: 2, rotation: 70, antialias: false } },
      { name: 'tile-both-any-true-full', width: 4, height: 7, phase: 813, tileOffset: [2, 2], fullResolution: [8, 10], reach: true, uniforms: { strength: -70, scale: 0.8, speed: -1, wrap: 1, rotation: 100, antialias: true } },
    ],
  },
  {
    id: 'lighting', key: 'filter/lighting:lighting', sourceFile: 'lighting/lighting.glsl',
    factoryName: 'canonicalFactory78', factorySha256: '9c9b70f5738071d64edb39c331ebf39b0075dd215fdae61db23b381a0898f75f',
    sourceRawBytes: 6049, sourceSha256: 'a0601f7012f385c14c1bdb9f462e5dcb303fe05cfbb4645484d5d1bd629e1a4f',
    builtin: 'reflect', mutations: REFLECT_MUTATIONS,
    uniformTypes: { diffuseColor: 'vec3', specularColor: 'vec3', specularIntensity: 'float', shininess: 'float', ambientColor: 'vec3', lightDirection: 'vec3', normalStrength: 'float', smoothing: 'float', renderScale: 'float', reflection: 'float', refraction: 'float', aberration: 'float' },
    extraTextures: { heightMap: 300 },
    reachabilityNote: 'reflect(incident, normal) is called once inside applyReflection, itself called only when reflection>0.0 || aberration>0.0. `normal` is always normalize()\'d (unit length) before it reaches reflect() in THIS program -- so the "defensive normalize" mutation is expected to be a full-render no-op here (proven, not assumed) even though it is a genuine hazard for the C++ port in general (see the direct rows for a non-unit-N discriminating case). When aberration>0 but reflection==0, applyReflection still executes and reflect() still fires (reachable, proven by call log), but its output is immediately multiplied by reflection==0, so BOTH reflect mutations are legitimately-zero-divergence for that case too -- documented with proof, not dropped.',
    cases: [
      { name: 'reflection-strong-sign-matters', width: 6, height: 5, phase: 820, reach: true, uniforms: { diffuseColor: [0.6, 0.5, 0.4], specularColor: [0.9, 0.9, 0.8], specularIntensity: 0.7, shininess: 24, ambientColor: [0.1, 0.1, 0.12], lightDirection: [0.4, 0.6, 0.5], normalStrength: 2.5, smoothing: 1.2, renderScale: 1, reflection: 60, refraction: 0, aberration: 0 } },
      { name: 'reflection-aberration-refraction-mixed-tiled', width: 5, height: 6, phase: 821, tileOffset: [2, 1], fullResolution: [11, 13], reach: true, uniforms: { diffuseColor: [0.3, 0.4, 0.6], specularColor: [0.8, 0.7, 0.9], specularIntensity: 0.4, shininess: 8, ambientColor: [0.05, 0.06, 0.08], lightDirection: [-0.3, 0.5, 0.7], normalStrength: 1.8, smoothing: 0.8, renderScale: 1, reflection: 35, refraction: 18, aberration: 20 } },
      { name: 'aberration-only-zero-offset-diagnostic', width: 7, height: 4, phase: 822, reach: true, diagnostic: true, uniforms: { diffuseColor: [0.5, 0.5, 0.5], specularColor: [0.6, 0.6, 0.6], specularIntensity: 0.3, shininess: 16, ambientColor: [0.08, 0.08, 0.08], lightDirection: [0.2, 0.2, 0.9], normalStrength: 1, smoothing: 1, renderScale: 1, reflection: 0, refraction: 0, aberration: 25 } },
      { name: 'all-off-diagnostic-no-reflect-call', width: 4, height: 7, phase: 823, reach: false, diagnostic: true, uniforms: { diffuseColor: [0.5, 0.5, 0.5], specularColor: [0.5, 0.5, 0.5], specularIntensity: 0.5, shininess: 12, ambientColor: [0.1, 0.1, 0.1], lightDirection: [0.3, 0.4, 0.8], normalStrength: 1, smoothing: 1, renderScale: 1, reflection: 0, refraction: 0, aberration: 0 } },
    ],
  },
  {
    id: 'fxaa', key: 'filter/fxaa:fxaa', sourceFile: 'fxaa/fxaa.glsl',
    factoryName: 'canonicalFactory56', factorySha256: '8c707f68d552fa852fa899d377616a0c772f0ebefce3026137af301f044bb3c0',
    sourceRawBytes: 4938, sourceSha256: '088449aa1fd5855489d3ce0c6ed2986b9b128fa93ace5817dbeafeff92a7bdf0',
    builtin: 'round', mutations: ROUND_MUTATIONS,
    uniformTypes: { strength: 'float', sharpness: 'float', threshold: 'float' },
    blockedTodayOn: 'unsupported global declaration (LUMA_WEIGHTS vec3 const) -- round becomes terminal only after that lands; see relaxed_global_probe.json',
    reachabilityNote: 'as_u32(resolution.x) / as_u32(resolution.y) execute unconditionally at the top of main() -- reachable, and its result (width_u/height_u) genuinely gates an early-return (verified: shrinking it by 1 causes the last column/row to early-return to transparent black). But resolution.x/y are ALWAYS exact integers (Number.isInteger enforced by createCanonicalBindings), so round(integer) == integer under every rounding convention -- no full-render case can ever exercise a genuine tie here. sanitized_channelCount()\'s round() (a second call site) is DEAD CODE: grepped, it is declared but never invoked from main().',
    cases: [
      { name: 'small-canvas-round-reachable-integer-only', width: 6, height: 5, phase: 830, reach: true, uniforms: { strength: 0.6, sharpness: 4, threshold: 0.05 } },
      { name: 'tiled-canvas-round-reachable-integer-only', width: 5, height: 6, phase: 831, tileOffset: [2, 1], fullResolution: [11, 9], reach: true, uniforms: { strength: 0.9, sharpness: 8, threshold: 0.02 } },
      { name: 'wide-canvas-round-reachable-integer-only', width: 7, height: 4, phase: 832, reach: true, uniforms: { strength: 0.3, sharpness: 2, threshold: 0.1 } },
      { name: 'tall-canvas-round-reachable-integer-only', width: 4, height: 7, phase: 833, reach: true, uniforms: { strength: 1.0, sharpness: 6, threshold: 0.01 } },
    ],
  },
  {
    id: 'grain', key: 'filter/grain:grain', sourceFile: 'grain/grain.glsl',
    factoryName: 'canonicalFactory65', factorySha256: '36a15bacaf42ebe94dc587fdc77cb56a5c714cae51fd40c7f7a6a187794ef44f',
    sourceRawBytes: 8796, sourceSha256: '6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0',
    builtin: 'round', mutations: ROUND_MUTATIONS,
    uniformTypes: { renderScale: 'float', alpha: 'float', pause: 'float' },
    blockedTodayOn: 'unsupported global declaration (const scalar table: PI/TAU/UINT32_TO_FLOAT/INTERPOLATION_*/BASE_SEED) -- round becomes terminal only after that lands',
    reachabilityNote: 'as_u32(res.x) / as_u32(res.y) execute unconditionally at the top of main() -- reachable, same early-return-gate structure and same always-integer-input constraint as fxaa (both proven below).',
    cases: [
      { name: 'basic-grain-round-reachable-integer-only', width: 6, height: 5, phase: 840, time: 0.4, reach: true, uniforms: { renderScale: 1, alpha: 0.6, pause: 0 } },
      { name: 'tiled-grain-round-reachable-integer-only', width: 5, height: 6, phase: 841, time: 1.1, tileOffset: [2, 1], fullResolution: [9, 8], reach: true, uniforms: { renderScale: 1.5, alpha: 0.8, pause: 0 } },
      { name: 'paused-grain-round-reachable-integer-only', width: 7, height: 4, phase: 842, time: 2.0, reach: true, uniforms: { renderScale: 1, alpha: 0.5, pause: 1 } },
      { name: 'scaled-grain-round-reachable-integer-only', width: 4, height: 7, phase: 843, time: 0, reach: true, uniforms: { renderScale: 2, alpha: 0.15, pause: 0 } },
    ],
  },
  {
    id: 'snow', key: 'filter/snow:snow', sourceFile: 'snow/snow.glsl',
    factoryName: 'canonicalFactory142', factorySha256: '769bbb2ed7322417cb3334d9427a1037c8dd40fd55f5e003490cd0129ef109b1',
    sourceRawBytes: 2982, sourceSha256: 'ae057787cc101755743c17b4cdf46b51d70ed8b9896fed9535a058c8b252f48a',
    builtin: 'round', mutations: ROUND_MUTATIONS,
    uniformTypes: { alpha: 'float', pause: 'float', density: 'float' },
    blockedTodayOn: 'unsupported global declaration (const scalar/vec3 table: CHANNEL_COUNT/TAU/TIME_SEED_OFFSETS/STATIC_SEED/LIMITER_SEED) -- round becomes terminal only after that lands',
    reachabilityNote: 'as_u32() -- the only function in this source that calls round() -- is DECLARED but NEVER CALLED anywhere in main() or any function main() transitively calls. Verified by grep against both the raw GLSL source (zero call sites besides the declaration) and the compiled JS factory text (same), and independently reconfirmed here at runtime: the InstrumentedRuntime call log for round() is empty for every snow case. round() is therefore fully dead code in this program -- the C++ port needs a node-identity admission for the call to type-check, but no case can or should assert non-trivial round() BEHAVIOR for snow; every mutation is expected (and proven) zero-divergence for every case.',
    cases: [
      { name: 'basic-snow-round-dead', width: 6, height: 5, phase: 850, time: 0.3, reach: false, uniforms: { alpha: 0.7, pause: 0, density: 40 } },
      { name: 'tiled-snow-round-dead', width: 5, height: 6, phase: 851, time: 1.4, tileOffset: [2, 1], fullResolution: [9, 8], reach: false, uniforms: { alpha: 0.5, pause: 0, density: 70 } },
      { name: 'paused-snow-round-dead', width: 7, height: 4, phase: 852, time: 2.2, reach: false, uniforms: { alpha: 0.9, pause: 1, density: 20 } },
      { name: 'zero-alpha-early-exit-diagnostic', width: 4, height: 7, phase: 853, time: 0, reach: false, diagnostic: true, uniforms: { alpha: 0, pause: 0, density: 50 } },
    ],
  },
]

// ---------------------------------------------------------------------------
// Per-program verification (source bytes, canonical factory identity), then
// case rendering.
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

  // Unlike grade/derivatives, do NOT require kernelFactories.get(key) ===
  // canonical for every program: filter/snow:snow's PUBLIC factory is a
  // hand-written performance adapter (src/effects/adapters/snow.js,
  // registered in canonicalAdapterFactories), not the canonical transpiled
  // factory. This is a genuine, load-bearing finding (see report) -- the
  // C++ port targets the CANONICAL (GLSL-transpiled) factory, exactly as
  // `generate_typed_slice.py` types the raw GLSL source, so
  // canonicalKernelFactories[key] remains correct oracle input for all six
  // programs; we just document the exception instead of asserting it away.
  const publicIsCanonical = kernelFactories.get(def.key) === canonical
  const hasAdapterOverride = canonicalAdapterFactories[def.key] !== undefined
  if (def.id === 'snow') {
    if (publicIsCanonical) throw new Error('snow: expected public factory to NOT be the canonical identity (adapter-override finding is stale -- update the generator)')
    if (!hasAdapterOverride) throw new Error('snow: expected an adapter override to be present (adapter-override finding is stale -- update the generator)')
  } else {
    if (!publicIsCanonical) throw new Error(`${def.id}: public factory is not the canonical identity (unexpected adapter override)`)
    if (hasAdapterOverride) throw new Error(`${def.id}: unexpected adapter override present`)
  }

  return { ...def, sourcePath, factoryText, canonical, publicIsCanonical, hasAdapterOverride }
}

const PROGRAMS = PROGRAM_DEFS.map(loadProgram)
for (const program of PROGRAMS) program.caseRecords = program.cases.map((c) => renderCase(program, c))

// ---------------------------------------------------------------------------
// Mutation-expectation table: per (program, mutation, case), is zero
// divergence EXPECTED (and why)? Anything not listed here is expected to
// diverge for every reach=true case. Every entry is machine-checked against
// the real render below -- a wrong expectation throws, per house style
// ("verify rather than assume").
// ---------------------------------------------------------------------------
const EXPECTED_ZERO = {
  // posterize: bankers only ties (case3 has none: no tie; case4's tie is
  // absorbed by the MIN_LEVELS floor regardless of which round() answer
  // feeds it). away-from-zero: proven no-op on every case (domain is
  // clamped non-negative before round() ever sees it). minus-one: also
  // absorbed by the MIN_LEVELS floor at levels=0.5 (max(1,1) == max(0,1)),
  // the SAME absorption effect, independently reconfirming it.
  'posterize/round-minus-one-liveness': ['min-levels-tie-absorbed-diagnostic'],
  'posterize/round-bankers-spec-tiebreak': ['ordinary-levels-no-tie-sanity', 'min-levels-tie-absorbed-diagnostic'],
  'posterize/round-away-from-zero-naive-cpp': ['half-tie-2.5-discriminates-bankers', 'half-tie-6.5-discriminates-bankers-antialias-off', 'ordinary-levels-no-tie-sanity', 'min-levels-tie-absorbed-diagnostic'],
  // waves: any-as-all only diverges on the mixed (exactly-one-true) cases.
  'waves/any-as-all-confusion': ['tile-zero-any-false', 'tile-both-any-true-full'],
  'waves/any-reverse-iteration-order': ['tile-zero-any-false', 'tile-x-only-any-true-one-lane', 'tile-y-only-any-true-other-lane', 'tile-both-any-true-full'],
  // lighting: defensive-normalize is a full-render no-op everywhere in THIS
  // program (N is always pre-normalized) -- proven below. sign-flip is a
  // no-op only on the "offset collapses to zero" diagnostic case.
  'lighting/reflect-defensive-normalize': ['reflection-strong-sign-matters', 'reflection-aberration-refraction-mixed-tiled', 'aberration-only-zero-offset-diagnostic'],
  'lighting/reflect-sign-flip': ['aberration-only-zero-offset-diagnostic'],
  // fxaa/grain: round() is reachable but its input is always an exact
  // integer, so BOTH tie-break mutations are structural no-ops for every
  // case (only round-minus-one, which perturbs every input regardless of
  // tie, can be discriminating here).
  'fxaa/round-bankers-spec-tiebreak': 'ALL',
  'fxaa/round-away-from-zero-naive-cpp': 'ALL',
  'grain/round-bankers-spec-tiebreak': 'ALL',
  'grain/round-away-from-zero-naive-cpp': 'ALL',
  // snow: round() is entirely dead code -- every mutation is a no-op on
  // every case.
  'snow/round-minus-one-liveness': 'ALL',
  'snow/round-bankers-spec-tiebreak': 'ALL',
  'snow/round-away-from-zero-naive-cpp': 'ALL',
}

for (const program of PROGRAMS) {
  for (const mutation of program.mutations) {
    const key = `${program.id}/${mutation.id}`
    const expectZeroSpec = EXPECTED_ZERO[key]
    const expectZeroSet = expectZeroSpec === 'ALL' ? new Set(program.caseRecords.map((c) => c.name)) : new Set(expectZeroSpec ?? [])
    for (const c of program.caseRecords) {
      const diverges = c.mutation_diverges[mutation.id]
      if (!c.reach) {
        if (diverges) throw new Error(`${key}/${c.name}: non-reaching case diverged -- reach predicate or mutation scope is wrong`)
        continue
      }
      const expectZero = expectZeroSet.has(c.name)
      if (expectZero && diverges) throw new Error(`${key}/${c.name}: expected ZERO divergence (documented) but observed divergence -- the "legitimately zero" claim is WRONG, investigate before shipping`)
      if (!expectZero && !diverges) throw new Error(`${key}/${c.name}: expected NONZERO divergence but observed none -- mutation is not actually discriminating for this case, fix the case or the expectation table`)
    }
  }
}

// ---------------------------------------------------------------------------
// Direct rows: invoke the shared runtime stdlib functions directly (not
// reimplemented) with hand-picked inputs unconstrained by any one program's
// reachable domain -- the only way to exhaustively characterize round() at
// all six required .5 boundaries (both signs) and reflect() with a
// deliberately non-normalized N, per the task's explicit discrimination
// requirements.
// ---------------------------------------------------------------------------
const REAL_RUNTIME = new GlslCpuRuntime()
const MINUS_ONE_RUNTIME = new RoundMinusOneRuntime()
const BANKERS_RUNTIME = new RoundBankersRuntime()
const AWAY_RUNTIME = new RoundAwayFromZeroRuntime()
const FLOOR_HALF_RUNTIME = new RoundFloorPlusHalfRuntime()

function roundDirectRow(v) {
  const real = REAL_RUNTIME.stdlib.round(v)
  const minusOne = MINUS_ONE_RUNTIME.stdlib.round(v)
  const bankers = BANKERS_RUNTIME.stdlib.round(v)
  const away = AWAY_RUNTIME.stdlib.round(v)
  const floorHalf = FLOOR_HALF_RUNTIME.stdlib.round(v)
  return {
    input: v,
    real_result: real, real_result_bits: f32Bits(real),
    minus_one_result: minusOne, minus_one_result_bits: f32Bits(minusOne), diverges_from_minus_one: f32Bits(real) !== f32Bits(minusOne),
    bankers_result: bankers, bankers_result_bits: f32Bits(bankers), diverges_from_bankers: f32Bits(real) !== f32Bits(bankers),
    away_from_zero_result: away, away_from_zero_result_bits: f32Bits(away), diverges_from_away_from_zero: f32Bits(real) !== f32Bits(away),
    floor_plus_half_result: floorHalf, floor_plus_half_result_bits: f32Bits(floorHalf), diverges_from_floor_plus_half: f32Bits(real) !== f32Bits(floorHalf),
  }
}
const ROUND_TIE_INPUTS = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
const ROUND_SANITY_INPUTS = [-3.25, -1, 0, 1, 3.25, 100]
const roundDirectRows = { tie_inputs_both_signs: ROUND_TIE_INPUTS.map(roundDirectRow), non_tie_sanity_inputs: ROUND_SANITY_INPUTS.map(roundDirectRow) }
// Non-vacuity + evidence assertions for the round() ground-truth claim.
for (const row of roundDirectRows.non_tie_sanity_inputs) {
  if (row.diverges_from_bankers || row.diverges_from_away_from_zero || row.diverges_from_floor_plus_half) {
    throw new Error(`round direct row ${row.input}: a non-tie input diverged from a tie-break mutation -- the mutations are not scoped to ties only, investigate`)
  }
}
if (!roundDirectRows.tie_inputs_both_signs.some((r) => r.diverges_from_bankers)) throw new Error('bankers mutation never diverges on any tie input -- not a real discriminator')
if (!roundDirectRows.tie_inputs_both_signs.some((r) => r.diverges_from_away_from_zero)) throw new Error('away-from-zero mutation never diverges on any tie input -- not a real discriminator')
if (!roundDirectRows.tie_inputs_both_signs.every((r) => r.diverges_from_minus_one)) throw new Error('minus-one mutation failed to diverge on every tie input -- not a real discriminator')
const floorHalfRow = roundDirectRows.tie_inputs_both_signs.find((r) => r.input === -0.5)
if (!floorHalfRow.diverges_from_floor_plus_half) throw new Error('-0.5: expected floor(x+0.5) to diverge from Math.round (the -0 sign trap) but it did not -- the claim is wrong')
if (!Object.is(floorHalfRow.real_result, -0)) throw new Error('-0.5: expected the real JS reference (Math.round) to return -0 -- claim is wrong, re-derive')
if (!Object.is(floorHalfRow.floor_plus_half_result, 0) || Object.is(floorHalfRow.floor_plus_half_result, -0)) throw new Error('-0.5: expected floor(x+0.5) to return +0 (not -0) -- claim is wrong, re-derive')
for (const row of roundDirectRows.tie_inputs_both_signs) {
  if (row.input !== -0.5 && row.diverges_from_floor_plus_half) throw new Error(`round direct row ${row.input}: floor(x+0.5) unexpectedly diverges away from the -0.5 boundary -- claim scope is wrong`)
}

const REAL_RT2 = new GlslCpuRuntime()
const ANY_AS_ALL_RT = new AnyAsAllRuntime()
const ANY_REVERSE_RT = new AnyReverseOrderRuntime()
function anyDirectRow(vec) {
  const arr = new Float32Array(vec)
  const real = REAL_RT2.stdlib.any(arr)
  const asAll = ANY_AS_ALL_RT.stdlib.any(new Float32Array(vec))
  const reverse = ANY_REVERSE_RT.stdlib.any(new Float32Array(vec))
  return { input: vec, real_result: real, as_all_result: asAll, diverges_from_as_all: real !== asAll, reverse_order_result: reverse, diverges_from_reverse_order: real !== reverse }
}
const ANY_DIRECT_INPUTS = [[0, 0], [1, 0], [0, 1], [1, 1], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 1, 1]]
const anyDirectRows = ANY_DIRECT_INPUTS.map(anyDirectRow)
if (!anyDirectRows.some((r) => r.diverges_from_as_all)) throw new Error('any-as-all mutation never diverges on any direct row -- not a real discriminator')
if (anyDirectRows.some((r) => r.diverges_from_reverse_order)) throw new Error('reverse-order mutation diverged on a direct row -- the order-invariance claim is wrong')

const REAL_RT3 = new GlslCpuRuntime()
const REFLECT_SIGN_RT = new ReflectSignFlipRuntime()
const REFLECT_NORM_RT = new ReflectAutoNormalizeRuntime()
function reflectDirectRow(name, incident, normal) {
  const I = new Float32Array(incident)
  const N = new Float32Array(normal)
  const real = Array.from(REAL_RT3.stdlib.reflect(new Float32Array(incident), new Float32Array(normal)))
  const signFlip = Array.from(REFLECT_SIGN_RT.stdlib.reflect(new Float32Array(incident), new Float32Array(normal)))
  const autoNorm = Array.from(REFLECT_NORM_RT.stdlib.reflect(new Float32Array(incident), new Float32Array(normal)))
  const nLength = Math.sqrt(normal.reduce((s, v) => s + v * v, 0))
  return {
    name, incident: Array.from(I), normal: Array.from(N), normal_length: nLength, normal_is_unit: Math.abs(nLength - 1) < 1e-6,
    real_result: real, real_result_bits: real.map(f32Bits),
    sign_flip_result: signFlip, sign_flip_result_bits: signFlip.map(f32Bits), diverges_from_sign_flip: real.some((v, i) => f32Bits(v) !== f32Bits(signFlip[i])),
    auto_normalize_result: autoNorm, auto_normalize_result_bits: autoNorm.map(f32Bits), diverges_from_auto_normalize: real.some((v, i) => f32Bits(v) !== f32Bits(autoNorm[i])),
  }
}
const reflectDirectRows = [
  reflectDirectRow('unit-N-positive-dot', [0.5, 0.3, 0.8], [0, 0, 1]),
  reflectDirectRow('unit-N-negative-dot', [-0.4, 0.2, -0.9], [0, 0, 1]),
  reflectDirectRow('unit-N-orthogonal-dot-zero', [1, 0, 0], [0, 0, 1]),
  reflectDirectRow('non-normalized-N-short', [0.6, 0.2, 0.7], [0.1, 0, 0]),
  reflectDirectRow('non-normalized-N-long', [0.3, -0.4, 0.9], [0, 0, 50]),
  reflectDirectRow('non-normalized-N-generic', [0.5, 0.5, -0.3], [2, -1, 4]),
]
{
  const orth = reflectDirectRows.find((r) => r.name === 'unit-N-orthogonal-dot-zero')
  if (orth.diverges_from_sign_flip) throw new Error('orthogonal dot=0 case: sign-flip should be a mathematical no-op (2*0*N=0 regardless of sign) but it diverged')
  const unitCases = reflectDirectRows.filter((r) => r.normal_is_unit)
  if (!unitCases.some((r) => r.diverges_from_sign_flip)) throw new Error('no unit-N direct row discriminates the sign-flip mutation')
  const nonUnitCases = reflectDirectRows.filter((r) => !r.normal_is_unit)
  if (nonUnitCases.length === 0) throw new Error('no non-normalized-N direct row constructed')
  if (!nonUnitCases.every((r) => r.diverges_from_auto_normalize)) throw new Error('a non-normalized-N direct row failed to diverge from the defensive-normalize mutation')
  if (unitCases.some((r) => r.diverges_from_auto_normalize)) throw new Error('a unit-N direct row unexpectedly diverges from the defensive-normalize mutation (should be a no-op when N is already unit length)')
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const programsOut = {}
  let totalCases = 0
  let totalDiagnostic = 0
  for (const program of PROGRAMS) {
    totalCases += program.caseRecords.length
    totalDiagnostic += program.caseRecords.filter((c) => c.diagnostic).length
    programsOut[program.id] = {
      key: program.key, defines: {}, builtin: program.builtin,
      blocked_today_on: program.blockedTodayOn ?? null,
      reachability_note: program.reachabilityNote,
      source_file: program.sourceFile, source_raw_bytes: program.sourceRawBytes, source_sha256: program.sourceSha256,
      canonical_factory_name: program.factoryName, canonical_factory_to_string_sha256: program.factorySha256,
      public_factory_is_canonical: program.publicIsCanonical, has_adapter_override: program.hasAdapterOverride,
      mutations: program.mutations.map((m) => ({ id: m.id, kind: m.kind, hazard: m.hazard, description: m.description })),
      cases: program.caseRecords,
    }
  }
  return {
    schema: 'noisemaker-for-cpp.builtins.builtin-admission-cluster-closure-oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version, public_identity: true },
    authorized_defines: {},
    defines_axis_note: 'All six programs compile at exact defines {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults() for all six keys, and independently by grep: the only preprocessor directive present in any of the six sources is the universal `#ifdef GL_ES` guard. No "different define map" axis exists for this cluster.',
    findings: {
      snow_public_factory_is_not_canonical: 'filter/snow:snow is the one program in this cluster whose PUBLIC kernelFactories entry is NOT canonicalKernelFactories -- src/effects/adapters/snow.js (snowFactory) hand-optimizes the same GLSL program for production rendering. The C++ port targets the CANONICAL (GLSL-transpiled) semantics, exactly as generate_typed_slice.py types the raw source, so this oracle correctly uses canonicalKernelFactories[key] for all six programs including snow -- documented here rather than silently working around it.',
      snow_round_is_dead_code: 'as_u32(), the only function in snow.glsl that calls round(), is declared but never invoked from main() -- confirmed by grep against the raw source, the compiled JS factory text, AND a runtime call-log instrumentation (zero round() calls recorded for every snow case built below). round() still gates the C++ generator\'s frozen-vocabulary walk (the walk visits declared functions, not just reachable ones), so a node-identity admission is still required for snow to type-check, but no case here asserts non-trivial round() BEHAVIOR for snow.',
      fxaa_grain_round_domain_is_integer_only: 'round()\'s reachable call site in both fxaa and grain (as_u32 applied to resolution.x/y or an equivalent) can never receive a fractional input: width/height are always exact integers (Number.isInteger enforced by createCanonicalBindings). Consequently no full-render case in either program can discriminate ANY rounding tie-break rule -- proven below (zero divergence, not assumed) for both the banker\'s-rounding and away-from-zero mutations, across every case. Only a general-liveness mutation (round(x) -> round(x)-1, which perturbs every input regardless of tie) is discriminating for these two programs at full-render.',
      posterize_round_domain_is_nonneg_only: 'posterize\'s round() input is levels_raw = max(levels, 0.0) -- always non-negative. round-half-away-from-zero agrees with Math.round on every non-negative real, so that mutation is a PROVABLE (and proven) no-op on every posterize case; only the banker\'s-rounding mutation (which differs from Math.round at positive ties too, e.g. 0.5 and 2.5) is discriminating at full-render for this program. Both signs of the required .5 boundary are still exhaustively covered via the direct rows below, unconstrained by this program\'s domain.',
      minus_0p5_sign_of_zero_trap: 'Math.round(-0.5) === -0 (verified: Object.is check). The common "obviously correct" C++ idiom `std::floor(x + 0.5f)` matches Math.round\'s VALUE at every other tested boundary but returns +0 (not -0) at exactly x=-0.5, because -0.5f+0.5f is an exact IEEE754 cancellation that rounds to +0. A C++ round() built on floor(x+0.5) will therefore differ from the JS reference in the SIGN BIT of a zero result at this one input -- proven via a direct row, not assumed.',
      lighting_reflect_defensive_normalize_is_full_render_noop: 'The "defensive internal normalize" reflect() mutation is a proven bit-exact no-op for every lighting full-render case: this program always calls normalize() on its normal vector before reflect() ever sees it (calculateNormal -> normalize(vec3(-dx,-dy,1))), so double-normalizing changes nothing. This is a property of THIS PROGRAM, not of reflect() in general -- the hazard is real and independently proven via a direct row using a deliberately non-unit N.',
    },
    programs: programsOut,
    eligibility_summary: { total_cases: totalCases, diagnostic_cases: totalDiagnostic },
    round_direct_rows: roundDirectRows,
    any_direct_rows: anyDirectRows,
    reflect_direct_rows: reflectDirectRows,
    negative_closure: {
      any_other_define_map: 'reject -- not constructible for this cluster, see defines_axis_note',
      generic_round_any_reflect_capability: 'forbidden -- this oracle characterizes exactly the three node-identity call sites documented per program, never a general "admit all round/any/reflect calls" capability',
      snow_round_treated_as_render_validated: 'forbidden -- validated structurally (call-log-proven unreachable) only; zero live consumers, zero divergence is EXPECTED and confirmed, not a coverage gap',
    },
  }
}

function report(d) {
  const lines = [
    '# Builtin admission cluster (`round` / `any` / `reflect`) closure oracle report', '',
    `Six programs blocked (three today, three after a documented but unlanded const-global-admission widening) on exactly one of three GLSL builtins with zero-or-partial node-identity admission in the C++20 generator. Authorized define map for all six: \`{}\`.`, '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.diagnostic_cases} early-exit / dead-code diagnostic).`, '',
    '## Findings', '',
  ]
  for (const [k, v] of Object.entries(d.findings)) lines.push(`- **${k}**: ${v}`)
  lines.push('', '## Per-program summary', '', '| Program | Builtin | Blocked today on | Cases | Diagnostic |', '| --- | --- | --- | ---: | ---: |')
  for (const [id, p] of Object.entries(d.programs)) {
    const diag = p.cases.filter((c) => c.diagnostic).length
    lines.push(`| ${id} | ${p.builtin} | ${p.blocked_today_on ?? '(terminal today)'} | ${p.cases.length} | ${diag} |`)
  }
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\` (${p.builtin})`, '')
    lines.push(`Source: \`${p.source_file}\` (${p.source_raw_bytes} bytes, \`${p.source_sha256}\`). Canonical factory \`${p.canonical_factory_name}\` (\`${p.canonical_factory_to_string_sha256}\`). Public factory is canonical identity: ${p.public_factory_is_canonical}. Adapter override present: ${p.has_adapter_override}.`, '')
    lines.push(`**Reachability**: ${p.reachability_note}`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | Call count | F32 SHA-256 |', '| --- | --- | --- | --- | ---: | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${c.reach} | ${c.builtin_call_count} | \`${c.output.f32_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations', '', '| Mutation | Hazard | Case | Reach | Diverges |', '| --- | --- | --- | --- | --- |')
    for (const m of p.mutations) {
      for (const c of p.cases) {
        lines.push(`| ${m.id} | ${m.hazard} | ${c.name} | ${c.reach} | ${c.mutation_diverges[m.id]} |`)
      }
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}`), '')
  }
  lines.push('## `round()` at the six required .5 boundaries (both signs) -- direct rows', '')
  lines.push('The JS reference materializes GLSL `round()` as `unary(Math.round)` (glsl-runtime.js:350) -- i.e. **round-half-towards-positive-infinity**, NOT the GLSL spec\'s round-half-to-even ("banker\'s rounding"), and NOT `std::round`\'s round-half-away-from-zero. Determined empirically (Math.round semantics probed directly, not assumed from any spec):', '')
  lines.push('| Input | Real (Math.round) | round-half-to-even (spec) | Diverges | round-half-away-from-zero (std::round) | Diverges | floor(x+0.5) | Diverges |', '| ---: | ---: | ---: | --- | ---: | --- | ---: | --- |')
  for (const r of d.round_direct_rows.tie_inputs_both_signs) {
    lines.push(`| ${r.input} | ${Object.is(r.real_result, -0) ? '-0' : r.real_result} | ${r.bankers_result} | ${r.diverges_from_bankers} | ${r.away_from_zero_result} | ${r.diverges_from_away_from_zero} | ${Object.is(r.floor_plus_half_result, -0) ? '-0' : r.floor_plus_half_result} | ${r.diverges_from_floor_plus_half} |`)
  }
  lines.push('', 'Non-tie sanity inputs (must show zero divergence against every tie-break mutation -- proven, not assumed):', '')
  lines.push('| Input | Real | Diverges (any mutation) |', '| ---: | ---: | --- |')
  for (const r of d.round_direct_rows.non_tie_sanity_inputs) {
    lines.push(`| ${r.input} | ${r.real_result} | ${r.diverges_from_bankers || r.diverges_from_away_from_zero || r.diverges_from_floor_plus_half} |`)
  }
  lines.push('', '## `any()` discrimination -- direct rows', '', '| Input | Real (any) | as-all result | Diverges | Reverse-order result | Diverges |', '| --- | --- | --- | --- | --- | --- |')
  for (const r of d.any_direct_rows) {
    lines.push(`| [${r.input.join(',')}] | ${r.real_result} | ${r.as_all_result} | ${r.diverges_from_as_all} | ${r.reverse_order_result} | ${r.diverges_from_reverse_order} |`)
  }
  lines.push('', '## `reflect()` discrimination -- direct rows', '', '| Case | I | N | \\|N\\| | unit N | Real | Diverges (sign-flip) | Diverges (defensive-normalize) |', '| --- | --- | --- | ---: | --- | --- | --- | --- |')
  for (const r of d.reflect_direct_rows) {
    lines.push(`| ${r.name} | [${r.incident.join(',')}] | [${r.normal.join(',')}] | ${r.normal_length.toFixed(4)} | ${r.normal_is_unit} | [${r.real_result.map((v) => v.toFixed(4)).join(',')}] | ${r.diverges_from_sign_flip} | ${r.diverges_from_auto_normalize} |`)
  }
  lines.push('', '## Negative closure', '')
  for (const [k, v] of Object.entries(d.negative_closure)) lines.push(`- **${k}**: ${v}`)
  lines.push('')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('builtin oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('builtin oracle report drift')
  const totalMutations = PROGRAMS.reduce((n, p) => n + p.mutations.length, 0)
  console.log(`builtin oracle fixture ok (${PROGRAMS.length} programs, ${data.eligibility_summary.total_cases} cases, ${totalMutations} mutation kinds, ${data.round_direct_rows.tie_inputs_both_signs.length + data.round_direct_rows.non_tie_sanity_inputs.length} round direct rows, ${data.any_direct_rows.length} any direct rows, ${data.reflect_direct_rows.length} reflect direct rows)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
