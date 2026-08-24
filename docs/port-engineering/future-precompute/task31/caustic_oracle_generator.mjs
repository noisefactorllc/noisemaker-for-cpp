import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel, createCanonicalBindings } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

// ---------------------------------------------------------------------------
// Task 31 — Caustic floatBitsToUint + scalar uint XOR closure oracle.
//
// Target: classicNoisedeck/caustic:caustic, function randomFromLatticeWithOffset
// (id 94). Four-node closure: one floatBitsToUint(float)->uint call
// (192:21-192:46) and three scalar uint^uint binary nodes (195:10-197:47).
//
// CRITICAL, EMPIRICALLY-VERIFIED CORRECTION TO THE DESIGN BRIEF
// (task-31-brief.md, "Exact four-node closure" / "Oracle requirements"
// sections): the brief claims "Caustic's three scalar XORs are live,
// reachable, rendered code ... randomFromLatticeWithOffset is called from
// constant()/constantOffset(), which the #if NOISE_TYPE == 10 branch of
// noise() calls directly". This is FALSE for the one authorized define
// combination {"NOISE_TYPE": 10}. Direct inspection of the raw corpus
// source (caustic.glsl:373-399) shows `value()` uses real C-preprocessor
// `#if/#elif/#endif` blocks, and the `#elif NOISE_TYPE == 10` branch calls
// ONLY `simplexValue` twice — never `constant`/`constantOffset`. This was
// independently confirmed two ways in this session:
//   1. Static: tools.glslcpp.generate_typed_slice.parse_program/analyze_program
//      run live against the pinned corpus revision with defines {"NOISE_TYPE":10}
//      produces a 22-function program whose call graph from `main` is exactly
//      {brightnessContrast, hsv2rgb, main, map, mod289, noise, periodicFunction,
//      permute, simplexValue, value} — `constant`, `constantOffset`, and
//      `randomFromLatticeWithOffset` are ABSENT from that reachable set.
//   2. Dynamic: rendering the real, hash-pinned canonicalFactory1 (JS
//      reference) at NOISE_TYPE=10 with every one of this file's four
//      structural mutations applied produces BIT-IDENTICAL F32 output to the
//      unmutated baseline in every case (see `full_render_mutations` below).
//      At NOISE_TYPE in {0,1,3,4,5,6} (the "value noise" family, which DOES
//      reach `constant`/`constantOffset`), only the AND mutation diverges —
//      the others (`+`, `|`, and the floatBitsToUint->uint swap) are
//      structurally no-ops there too, because every legitimate call path
//      threads `s` from `float(seed) + <integer offset>` (seed is `uniform
//      int`), so `seedFrac = fract(s)` is always exactly 0.0: floatBitsToUint
//      and uint() agree at 0.0, and 0 is the identity element for `^`/`+`/`|`.
//
// CONSEQUENCE FOR THIS ORACLE: no full-pixel-kernel render, at ANY uniform
// combination (eligible or not), can exercise or discriminate this closure.
// This oracle therefore treats DIRECT INVOCATION of the ported function
// (byte-for-byte extracted from the pinned public factory text, with
// non-integer `s`) as the authoritative closure-parity surface — exactly
// what the brief's OWN Native Test Plan section independently recommends
// ("the smallest wrapping public call, constant()/constantOffset()"). Full
// pixel-kernel renders are still produced (>=4 eligible cases with full F32/
// RGBA8 hashing) for ordinary whole-program parity coverage, but they are
// NOT claimed to discriminate the closure, and that non-discrimination is
// itself asserted (not just narrated) below.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'caustic-oracles.json')
const reportPath = path.join(here, 'caustic-oracle-report.md')
const key = 'classicNoisedeck/caustic:caustic'
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = `tools/glslcpp/corpus/${revision}/sources/classicNoisedeck/caustic/caustic.glsl`
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const AUTHORIZED_DEFINES = Object.freeze({ NOISE_TYPE: 10 })

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return Buffer.compare(bytes(a.data), bytes(b.data)) === 0 }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function u32Hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function defineMapEligible(defines) { return Object.keys(defines).length === 1 && defines.NOISE_TYPE === 10 }

const provenance = {
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
  source_sha256: '161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d',
  canonical_factory_name: 'canonicalFactory1',
  canonical_factory_to_string_sha256: '27beaa017be557b5960bd072d74247896e596fa0b71b5c331c7795f5732a7488',
}

if (sha256(fs.readFileSync(canonicalPath)) !== provenance.canonical_kernels_sha256) throw new Error('canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== provenance.public_catalog_sha256) throw new Error('catalog drift')
if (sha256(fs.readFileSync(adapterPath)) !== provenance.adapter_index_sha256) throw new Error('adapter registry drift')
if (sha256(fs.readFileSync(sourcePath)) !== provenance.source_sha256) throw new Error('source drift')
const canonical = canonicalKernelFactories[key]
if (canonical?.name !== provenance.canonical_factory_name || sha256(canonical.toString()) !== provenance.canonical_factory_to_string_sha256) throw new Error('factory drift')
if (kernelFactories.get(key) !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')

const factoryText = canonical.toString()

// ---------------------------------------------------------------------------
// Byte-for-byte extraction of the closure and its callers from the pinned
// public factory text (occurrence-count-checked, brace-matched — same
// verbatim-substring discipline extrude_oracle_generator.mjs used for its
// topLine/sideLine anchors).
// ---------------------------------------------------------------------------
function extractFn(text, name) {
  const anchor = `function ${name} (`
  const count = text.split(anchor).length - 1
  if (count !== 1) throw new Error(`${name}: expected exactly 1 occurrence of "${anchor}", got ${count}`)
  const start = text.indexOf(anchor)
  let i = text.indexOf('{', start), depth = 0, end = -1
  for (; i < text.length; i += 1) {
    if (text[i] === '{') depth += 1
    else if (text[i] === '}') { depth -= 1; if (depth === 0) { end = i; break } }
  }
  if (end === -1) throw new Error(`${name}: no matching closing brace`)
  let stop = end + 1
  if (text[stop] === ';') stop += 1
  return text.slice(start, stop)
}

const HELPER_NAMES = ['map', 'pcg', 'positiveModulo', 'periodicFunction', 'constant', 'constantOffset', 'randomFromLatticeWithOffset']
const helperText = Object.fromEntries(HELPER_NAMES.map(n => [n, extractFn(factoryText, n)]))
const helperTextSha256 = Object.fromEntries(HELPER_NAMES.map(n => [n, sha256(helperText[n])]))

// Freeze exact extracted-closure identity. floatBitsToUint site + 3 scalar
// XOR sites live entirely inside randomFromLatticeWithOffset's text.
const CLOSURE_SITE_ANCHORS = {
  floatBitsToUint_call: 'floatBitsToUint(seedFrac)',
  xor_site_1: '(cpu_umul(fracBits, 374761393)) ^ 2654435769',
  xor_site_2: '(cpu_umul(fracBits, 668265263)) ^ 2135587861',
  xor_site_3: '(cpu_umul(fracBits, 2246822519)) ^ 2496678324',
}
for (const [name, anchor] of Object.entries(CLOSURE_SITE_ANCHORS)) {
  const count = helperText.randomFromLatticeWithOffset.split(anchor).length - 1
  if (count !== 1) throw new Error(`closure site ${name}: expected exactly 1 occurrence, got ${count}`)
}
// Magic constants, decimal literal in the emitted JS vs. the GLSL hex literal.
if (0x9E3779B9 !== 2654435769 || 0x7F4A7C15 !== 2135587861 || 0x94D049B4 !== 2496678324) {
  throw new Error('magic constant decimal/hex mismatch')
}

// ---------------------------------------------------------------------------
// Build a standalone closure factory: verbatim extracted helper text,
// wired with the same destructuring header the real factory uses for the
// symbols the closure needs, returning {constant, constantOffset,
// randomFromLatticeWithOffset} for direct invocation. An "instrumented"
// variant stashes intermediate xBits/yBits/seedBits/fracBits/jitter/state/
// prngState via textual insertion at unique, occurrence-checked anchors —
// verified byte-for-byte against the verbatim variant's final return value
// before being trusted for anything.
// ---------------------------------------------------------------------------
function buildClosureFactorySrc(randomFromLatticeWithOffsetText) {
  return `(function closureFactory($bindings, $runtime, $probe) {
  const { float, vec2, vec3, ivec2, sin, abs, floor, fract, mod, min, max, clamp, mix, smoothstep, dot, add, subtract, floatBitsToUint } = $runtime.stdlib
  function cpu_float (value) { return $runtime.stdlib.float(value); };
  function cpu_ivec2 (a, b) { return $runtime.stdlib.ivec2(a, b); };
  function cpu_ivec2_vec2 (a, b) { return $runtime.stdlib.ivec2(a, b); };
  function cpu_uvec3 (a, b, c) { return $runtime.stdlib.uvec3(a, b, c); };
  function cpu_umul (left, right) { return $runtime.stdlib.umul(left, right); };
  var time = $bindings["time"];
  var seed = $bindings["seed"];
  var wrap = $bindings["wrap"];
  var speed = $bindings["speed"];
  ${helperText.map}
  ${helperText.pcg}
  ${helperText.positiveModulo}
  ${helperText.periodicFunction}
  ${helperText.constant}
  ${helperText.constantOffset}
  ${randomFromLatticeWithOffsetText}
  return { constant, constantOffset, randomFromLatticeWithOffset };
})`
}

function stashInsert(src, anchor, insertion) {
  const count = src.split(anchor).length - 1
  if (count !== 1) throw new Error(`stash anchor missing/duplicated (expected 1, got ${count}): ${anchor}`)
  return src.replace(anchor, anchor + insertion)
}

let instrumentedRflwoText = helperText.randomFromLatticeWithOffset
instrumentedRflwoText = stashInsert(instrumentedRflwoText,
  'var fracBits = floatBitsToUint(seedFrac);',
  ' $probe.fracBits = fracBits; $probe.xBits = xBits; $probe.yBits = yBits; $probe.seedBits = seedBits; $probe.seedFrac = seedFrac;')
instrumentedRflwoText = stashInsert(instrumentedRflwoText,
  'var jitter = cpu_uvec3((cpu_umul(fracBits, 374761393)) ^ 2654435769, (cpu_umul(fracBits, 668265263)) ^ 2135587861, (cpu_umul(fracBits, 2246822519)) ^ 2496678324);',
  ' $probe.jitter = Array.from(jitter);')
instrumentedRflwoText = stashInsert(instrumentedRflwoText,
  'var state = vec3.xor([], cpu_uvec3(xBits, yBits, seedBits), jitter);',
  ' $probe.state = Array.from(state);')
instrumentedRflwoText = stashInsert(instrumentedRflwoText,
  'var prngState = pcg(state);',
  ' $probe.prngState = Array.from(prngState);')

const verbatimClosureBuild = (0, eval)(buildClosureFactorySrc(helperText.randomFromLatticeWithOffset))
const instrumentedClosureBuild = (0, eval)(buildClosureFactorySrc(instrumentedRflwoText))

// Real $runtime/$bindings, captured from the actual bindGlslKernel machinery
// (not reimplemented) via a throwaway capture factory.
function captureRuntime(uniforms) {
  let capturedRuntime = null, capturedBindings = null
  function captureFactory($bindings, $runtime) { capturedRuntime = $runtime; capturedBindings = $bindings; return function () {} }
  captureFactory.usesDerivatives = false
  const bindings = createCanonicalBindings({ width: 2, height: 2, uniforms, textures: {} })
  bindGlslKernel(captureFactory, bindings)
  return { runtime: capturedRuntime, bindings: capturedBindings }
}

const DEFAULT_UNIFORMS = { NOISE_TYPE: 10, time: 0, seed: 44, wrap: true, noiseScale: 85, speed: 25, hueRotation: 180, hueRange: 25, intensity: 0 }
function fullUniforms(overrides, noiseType = 10) { return { ...DEFAULT_UNIFORMS, ...overrides, NOISE_TYPE: noiseType } }

function closureFor(uniformOverrides, rflwoText, build) {
  const uniforms = fullUniforms(uniformOverrides)
  const { runtime, bindings } = captureRuntime(uniforms)
  const probe = {}
  const closure = build(bindings, runtime, probe)
  return { closure, probe }
}

// Verify instrumentation is semantically inert (produces bit-identical final
// results to the verbatim, un-instrumented extraction) before trusting it.
{
  const verifyInputs = [
    [new Float32Array([0.31, 0.72]), 4, 4, 44.1, [1, -1], { seed: 44, wrap: true }],
    [new Float32Array([-2.4, 9.9]), 12, 3, -0.5, [0, 2], { seed: 0, wrap: false }],
    [new Float32Array([0, 0]), 1, 1, 100.999999, [-3, 5], { seed: 99, wrap: true }],
  ]
  for (const [st, xFreq, yFreq, s, offset, uniformOverrides] of verifyInputs) {
    const { closure: verbatim } = closureFor(uniformOverrides, helperText.randomFromLatticeWithOffset, verbatimClosureBuild)
    const { closure: instrumented } = closureFor(uniformOverrides, instrumentedRflwoText, instrumentedClosureBuild)
    const a = verbatim.randomFromLatticeWithOffset(new Float32Array(st), xFreq, yFreq, s, offset)
    const b = instrumented.randomFromLatticeWithOffset(new Float32Array(st), xFreq, yFreq, s, offset)
    if (!(a[0] === b[0] && a[1] === b[1] && a[2] === b[2])) throw new Error('instrumentation altered semantics')
  }
}

// ---------------------------------------------------------------------------
// Static reachability evidence (recomputed live in this session via
// tools.glslcpp.generate_typed_slice.parse_program/analyze_program against
// the pinned corpus revision with the authorized define map).
// ---------------------------------------------------------------------------
const reachabilityFinding = {
  claim_in_brief: 'randomFromLatticeWithOffset is called from constant()/constantOffset(), which the #if NOISE_TYPE == 10 branch of noise() calls directly',
  verified_status: 'CONTRADICTED',
  static_evidence: {
    tool: 'tools.glslcpp.generate_typed_slice.parse_program + analyze_program, run live against corpus revision a024dc3a960cc44af454abc7aebce50456c194e6 with defines {"NOISE_TYPE": 10}',
    function_count: 22,
    value_function_id: 96,
    value_function_body_statement_count: 2,
    value_function_calls_at_NOISE_TYPE_10: ['simplexValue', 'simplexValue'],
    call_graph_reachable_from_main: ['brightnessContrast', 'hsv2rgb', 'main', 'map', 'mod289', 'noise', 'periodicFunction', 'permute', 'simplexValue', 'value'],
    randomFromLatticeWithOffset_reachable_from_main: false,
    constant_reachable_from_main: false,
    constantOffset_reachable_from_main: false,
    randomFromLatticeWithOffset_function_id: 94,
  },
  dynamic_evidence: {
    method: 'render the real, hash-pinned canonicalFactory1 at every NOISE_TYPE with each of this oracle\'s 4 structural mutations applied, diff full F32 bytes against the unmutated baseline',
    note: 'see full_render_mutations.eligible_case_results (NOISE_TYPE=10: 0/N for all 4 mutations) and full_render_mutations.ineligible_diagnostic_case_results (NOISE_TYPE=0: only the AND mutation diverges) below',
  },
  forced_zero_seedFrac_finding: {
    description: 'Every legitimate call path threads `s` from `float(seed) + <integer literal offset>` (seed is `uniform int`), so seedFrac = fract(s) is always exactly 0.0 wherever the closure IS reachable (NOISE_TYPE in {0,1,3,4,5,6}). floatBitsToUint(0.0) === uint(0.0) === 0, and 0 is the identity element for ^ / + / |, so the floatBitsToUint->uint mutation and the +/| XOR-site mutations are structurally non-discriminating via ANY full-kernel render, reachable or not. Only an AND-style mutation (0 & X = 0 != X = 0 ^ X) discriminates via full render, and only where reachable.',
  },
  conclusion: 'No full-kernel pixel render, at any uniform combination (eligible or not), can exercise or discriminate this closure. This oracle uses direct invocation of the byte-for-byte-extracted public-factory function (with non-integer `s`, which the function\'s own signature permits even though no in-repo caller ever supplies one) as the authoritative closure-parity surface, matching the brief\'s own Native Test Plan recommendation to test via "the smallest wrapping public call, constant()/constantOffset()".',
}

// ---------------------------------------------------------------------------
// Full-kernel render helpers (no input texture: resources say samplers=()).
// ---------------------------------------------------------------------------
function render(factory, { width, height, uniforms, tileOffset, fullResolution }) {
  const kernel = bindCanonicalKernel(factory, {
    width, height, uniforms, textures: {},
    tileOffset: new Float32Array(tileOffset ?? [0, 0]),
    fullResolution: new Float32Array(fullResolution ?? [width, height]),
  })
  const output = new Surface(width, height)
  runPass({ kernel, destination: output })
  return output
}
function probe(surface, x, y) {
  const i = (y * surface.width + x) * 4, values = Array.from(surface.data.slice(i, i + 4))
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
// Eligible full-render cases (defines = {"NOISE_TYPE": 10}, the ONLY
// authorized combination). Varied dimensions/uniforms/time for coverage.
// These do NOT and structurally CANNOT exercise the closure (see finding
// above) — included for ordinary whole-program parity, not closure parity.
// ---------------------------------------------------------------------------
const eligibleRenderDefs = [
  { name: 'simplex-default-seed44', width: 6, height: 5, uniforms: { seed: 44, wrap: true, time: 0 } },
  { name: 'simplex-seed-zero-nowrap', width: 7, height: 4, uniforms: { seed: 0, wrap: false, time: 3.5 } },
  { name: 'simplex-large-seed-tiled', width: 5, height: 7, uniforms: { seed: 99, wrap: true, time: 12 }, tileOffset: [3, 2], fullResolution: [13, 11] },
  { name: 'simplex-negative-intensity-full-hue', width: 8, height: 3, uniforms: { seed: 17, hueRotation: 0, hueRange: 100, intensity: -80, speed: 100, time: 1.25 } },
  { name: 'simplex-min-scale-zero-speed', width: 4, height: 4, uniforms: { seed: 1, noiseScale: 1, speed: 0, time: 0 } },
  { name: 'simplex-max-scale-large-canvas', width: 10, height: 6, uniforms: { seed: 71, noiseScale: 200, speed: 63, hueRange: 5, time: 40 } },
]

// ---------------------------------------------------------------------------
// Ineligible full-render cases: same product parameter surface (`interp`),
// different NOISE_TYPE define -- a genuinely different compiled program the
// C++ port never built. Included to demonstrate the define-eligibility risk
// this task's brief explicitly flags, and (as a bonus diagnostic, not an
// eligibility claim) to show the AND mutation DOES discriminate here.
// ---------------------------------------------------------------------------
const ineligibleRenderDefs = [
  { name: 'value-constant-interp0', width: 6, height: 5, defines: { NOISE_TYPE: 0 }, uniforms: { seed: 44, wrap: true, time: 0 } },
  { name: 'value-linear-interp1', width: 6, height: 5, defines: { NOISE_TYPE: 1 }, uniforms: { seed: 44, wrap: true, time: 0 } },
  { name: 'sine-interp11', width: 6, height: 5, defines: { NOISE_TYPE: 11 }, uniforms: { seed: 44, wrap: true, time: 0 } },
]

// ---------------------------------------------------------------------------
// Direct closure-probe cases: authoritative closure-parity surface. Direct
// invocation of the byte-for-byte extracted, instrumented public-factory
// function, varying st/xFreq/yFreq/s (including fractional values a real
// uniform surface could never produce)/offset/seed/wrap.
// ---------------------------------------------------------------------------
const closureProbeDefs = [
  { name: 'baseline-integer-seed-matches-full-render', st: [0.31, 0.72], xFreq: 4, yFreq: 4, s: 44.0, offset: [0, 0], uniforms: { seed: 44, wrap: true } },
  { name: 'fractional-seed-simple-half', st: [0.31, 0.72], xFreq: 4, yFreq: 4, s: 44.5, offset: [0, 0], uniforms: { seed: 44, wrap: true } },
  { name: 'fractional-seed-float32-rounding-boundary', st: [0.31, 0.72], xFreq: 4, yFreq: 4, s: 44.1, offset: [1, -1], uniforms: { seed: 44, wrap: true } },
  { name: 'negative-fractional-seed', st: [-2.4, 9.9], xFreq: 12, yFreq: 3, s: -0.5, offset: [0, 2], uniforms: { seed: 0, wrap: false } },
  { name: 'near-one-fractional-seed-no-wrap', st: [0, 0], xFreq: 1, yFreq: 1, s: 100.999999, offset: [-3, 5], uniforms: { seed: 99, wrap: true } },
  { name: 'small-fractional-seed-large-offset', st: [5.5, -3.25], xFreq: 85, yFreq: 85, s: 7.000123, offset: [17, -22], uniforms: { seed: 3, wrap: true } },
  { name: 'one-third-fractional-seed', st: [1.1, 1.1], xFreq: 6, yFreq: 6, s: 12 + 1 / 3, offset: [0, 0], uniforms: { seed: 12, wrap: false } },
  { name: 'wrap-toggle-otherwise-identical', st: [5.5, -3.25], xFreq: 85, yFreq: 85, s: 7.000123, offset: [17, -22], uniforms: { seed: 3, wrap: false } },
]

function runClosureProbeCase(def, rflwoText, build) {
  const { closure, probe: probeOut } = closureFor(def.uniforms, rflwoText, build)
  const st = new Float32Array(def.st)
  const original = new Float32Array(st)
  const result = closure.randomFromLatticeWithOffset(st, def.xFreq, def.yFreq, def.s, def.offset)
  const inputImmutable = Buffer.compare(bytes(st), bytes(original)) === 0
  return { result: Array.from(result), probe: probeOut, inputImmutable }
}

function buildClosureProbeRecords() {
  return closureProbeDefs.map(def => {
    const first = runClosureProbeCase(def, instrumentedRflwoText, instrumentedClosureBuild)
    const second = runClosureProbeCase(def, instrumentedRflwoText, instrumentedClosureBuild)
    const repeatIdentity = JSON.stringify(first.result) === JSON.stringify(second.result) && JSON.stringify(first.probe) === JSON.stringify(second.probe)
    if (!repeatIdentity) throw new Error(`${def.name}: repeat mismatch`)
    if (!first.inputImmutable) throw new Error(`${def.name}: st input mutated`)
    const eligible = defineMapEligible(AUTHORIZED_DEFINES)
    return {
      name: def.name, defines: { ...AUTHORIZED_DEFINES }, eligible_for_native_binding: eligible,
      inputs: { st: def.st, xFreq: def.xFreq, yFreq: def.yFreq, s: def.s, s_bits: f32Bits(def.s), offset: def.offset, seed_uniform: def.uniforms.seed, wrap_uniform: def.uniforms.wrap },
      seedFrac: first.probe.seedFrac, seedFrac_bits: f32Bits(first.probe.seedFrac),
      fracBits: first.probe.fracBits, fracBits_hex: u32Hex(first.probe.fracBits),
      xBits: first.probe.xBits, yBits: first.probe.yBits, seedBits: first.probe.seedBits,
      jitter: first.probe.jitter, jitter_hex: first.probe.jitter.map(u32Hex),
      state: first.probe.state, prngState: first.probe.prngState,
      result: first.result, result_bits: first.result.map(f32Bits),
      repeat_identity: true, input_immutable: true,
    }
  })
}

// ---------------------------------------------------------------------------
// Direct rows: pure scalar semantics freeze. floatBitsToUint(seedFrac) and
// the three-way XOR chain, computed with the REAL runtime stdlib primitives
// (floatBitsToUint, umul) -- not reimplemented.
// ---------------------------------------------------------------------------
function scalarClosureRow(seedFracValue) {
  const { runtime } = captureRuntime(DEFAULT_UNIFORMS)
  const { floatBitsToUint } = runtime.stdlib
  const umul = runtime.stdlib.umul
  const fracBits = floatBitsToUint(seedFracValue)
  const jitter = [
    (umul(fracBits, 374761393) ^ 0x9E3779B9) >>> 0,
    (umul(fracBits, 668265263) ^ 0x7F4A7C15) >>> 0,
    (umul(fracBits, 2246822519) ^ 0x94D049B4) >>> 0,
  ]
  return {
    seedFrac_input: seedFracValue, seedFrac_double_repr: String(seedFracValue),
    seedFrac_f32_bits: Number.isNaN(seedFracValue) ? 'nan' : f32Bits(seedFracValue),
    fracBits, fracBits_hex: u32Hex(fracBits),
    jitter, jitter_hex: jitter.map(u32Hex),
  }
}
const DIRECT_SCALAR_SEEDFRAC_VALUES = [
  0.0, -0.0, 0.5, 0.1, 1 / 3, 0.999999, 0.9999999403953552,
  1.401298464324817e-45, 44.1 - 44, NaN, Infinity, -Infinity,
]
function buildDirectScalarRows() {
  const rows = DIRECT_SCALAR_SEEDFRAC_VALUES.map(scalarClosureRow)
  // +0.0 and -0.0 compare equal numerically but must diverge at the bit level.
  if (rows[0].fracBits === rows[1].fracBits) throw new Error('+0.0/-0.0 did not produce distinct floatBitsToUint bit patterns')
  if (rows[0].jitter[0] === rows[1].jitter[0]) throw new Error('+0.0/-0.0 did not propagate to distinct jitter values')
  return rows
}

// ---------------------------------------------------------------------------
// Public-factory mutations. Each is a verbatim textual transform of the
// SAME extracted randomFromLatticeWithOffset text, occurrence-count-checked
// against the pinned public factory. floatBitsToUint->uint is the single
// most dangerous real-world error the brief flags (bit-reinterpretation vs.
// truncating/wrapping numeric conversion). Each XOR site is mutated to a
// DIFFERENT, non-commutative-preserving operator so no two mutations share
// a code path (operand-order swap is deliberately NOT used: XOR is
// commutative, so swapping operands is a non-discriminating no-op here).
// ---------------------------------------------------------------------------
const MUTATIONS = [
  {
    id: 'floatbits-to-numeric-uint-conversion',
    hazard: 'bit-reinterpretation-vs-numeric-conversion',
    anchor: 'var fracBits = floatBitsToUint(seedFrac);',
    replacement: 'var fracBits = $runtime.stdlib.uint(seedFrac);',
  },
  {
    id: 'xor-site-1-to-add',
    hazard: 'xor-vs-add',
    anchor: '(cpu_umul(fracBits, 374761393)) ^ 2654435769',
    replacement: '(cpu_umul(fracBits, 374761393)) + 2654435769',
  },
  {
    id: 'xor-site-2-to-or',
    hazard: 'xor-vs-or',
    anchor: '(cpu_umul(fracBits, 668265263)) ^ 2135587861',
    replacement: '(cpu_umul(fracBits, 668265263)) | 2135587861',
  },
  {
    id: 'xor-site-3-to-and',
    hazard: 'xor-vs-and',
    anchor: '(cpu_umul(fracBits, 2246822519)) ^ 2496678324',
    replacement: '(cpu_umul(fracBits, 2246822519)) & 2496678324',
  },
]

function mutateRflwoText(mutation) {
  const count = helperText.randomFromLatticeWithOffset.split(mutation.anchor).length - 1
  if (count !== 1) throw new Error(`mutation ${mutation.id}: expected exactly 1 anchor occurrence, got ${count}`)
  return helperText.randomFromLatticeWithOffset.replace(mutation.anchor, mutation.replacement)
}
function mutateFullFactoryText(mutation) {
  const count = factoryText.split(mutation.anchor).length - 1
  if (count !== 1) throw new Error(`mutation ${mutation.id}: expected exactly 1 anchor occurrence in full factory text, got ${count}`)
  return factoryText.replace(mutation.anchor, mutation.replacement)
}

function buildDirectClosureMutations() {
  const results = MUTATIONS.map(mutation => {
    const mutatedText = mutateRflwoText(mutation)
    const mutatedBuild = (0, eval)(buildClosureFactorySrc(mutatedText))
    const caseResults = closureProbeDefs.map(def => {
      const baseline = runClosureProbeCase(def, helperText.randomFromLatticeWithOffset, verbatimClosureBuild)
      const mutated = runClosureProbeCase(def, mutatedText, mutatedBuild)
      const diverges = JSON.stringify(baseline.result) !== JSON.stringify(mutated.result)
      return { case: def.name, diverges, baseline_result_bits: baseline.result.map(f32Bits), mutated_result_bits: mutated.result.map(f32Bits) }
    })
    return { id: mutation.id, hazard: mutation.hazard, case_results: caseResults }
  })
  for (const m of results) {
    const divergent = m.case_results.filter(c => c.diverges).length
    if (divergent === 0) throw new Error(`${m.id}: no discriminating direct-closure-probe case — mutation is USELESS`)
  }
  return results
}

function buildFullRenderMutations() {
  const results = MUTATIONS.map(mutation => {
    const mutatedFactory = (0, eval)(`(${mutateFullFactoryText(mutation)})`)
    const eligibleResults = eligibleRenderDefs.map(def => {
      const uniforms = fullUniforms(def.uniforms, 10)
      const baseline = render(canonical, { ...def, uniforms })
      const mutated = render(mutatedFactory, { ...def, uniforms })
      return { case: def.name, diverges: !sameBytes(baseline, mutated) }
    })
    const ineligibleResults = ineligibleRenderDefs.map(def => {
      const uniforms = fullUniforms(def.uniforms, def.defines.NOISE_TYPE)
      const baseline = render(canonical, { ...def, uniforms })
      const mutated = render(mutatedFactory, { ...def, uniforms })
      return { case: def.name, defines: def.defines, diverges: !sameBytes(baseline, mutated) }
    })
    return { id: mutation.id, hazard: mutation.hazard, eligible_case_results: eligibleResults, ineligible_diagnostic_case_results: ineligibleResults }
  })
  // Machine-checked assertion of the dead-code finding: EVERY mutation must
  // produce EXACTLY zero divergence across EVERY eligible (NOISE_TYPE=10)
  // full-render case. If this ever fails, the reachability finding above is
  // wrong and must be re-investigated before shipping.
  for (const m of results) {
    const divergentEligible = m.eligible_case_results.filter(c => c.diverges).length
    if (divergentEligible !== 0) throw new Error(`${m.id}: expected 0 eligible-case divergence (dead code at NOISE_TYPE=10), got ${divergentEligible} -- reachability finding is WRONG, investigate before shipping`)
  }
  // The AND mutation is the one structural mutation expected to discriminate
  // at reachable-but-ineligible NOISE_TYPE values; assert that too, so a
  // silent regression in either direction fails loud.
  const andMutation = results.find(m => m.id === 'xor-site-3-to-and')
  const andDivergentIneligible = andMutation.ineligible_diagnostic_case_results.filter(c => c.diverges).length
  if (andDivergentIneligible === 0) throw new Error('AND mutation failed to discriminate any ineligible (reachable) diagnostic case -- reachability instrumentation is broken')
  return results
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function buildEligibleRenderRecords() {
  return eligibleRenderDefs.map(def => {
    const uniforms = fullUniforms(def.uniforms, 10)
    const first = render(canonical, { ...def, uniforms })
    const second = render(canonical, { ...def, uniforms })
    if (!sameBytes(first, second)) throw new Error(`${def.name}: repeat mismatch`)
    return {
      name: def.name, dimensions: { width: def.width, height: def.height }, defines: { ...AUTHORIZED_DEFINES },
      eligible_for_native_binding: true, uniforms: def.uniforms,
      tile_offset: def.tileOffset ?? [0, 0], full_resolution: def.fullResolution ?? [def.width, def.height],
      output: renderResult(first), repeat_identity: true,
      closure_reachable: false, closure_reachable_note: 'randomFromLatticeWithOffset is unreachable from main() at NOISE_TYPE=10 -- see program.reachability_finding',
    }
  })
}
function buildIneligibleRenderRecords() {
  return ineligibleRenderDefs.map(def => {
    const uniforms = fullUniforms(def.uniforms, def.defines.NOISE_TYPE)
    const first = render(canonical, { ...def, uniforms })
    const second = render(canonical, { ...def, uniforms })
    if (!sameBytes(first, second)) throw new Error(`${def.name}: repeat mismatch`)
    const closureReachable = [0, 1, 3, 4, 5, 6].includes(def.defines.NOISE_TYPE)
    return {
      name: def.name, dimensions: { width: def.width, height: def.height }, defines: def.defines,
      eligible_for_native_binding: false,
      ineligibility_reason: `defines ${JSON.stringify(def.defines)} != authorized ${JSON.stringify(AUTHORIZED_DEFINES)} -- this is a different, never-ported preprocessor branch of the same shared classicNoisedeck/caustic source; its C++-side comparison target does not exist`,
      uniforms: def.uniforms,
      output: renderResult(first), repeat_identity: true,
      closure_reachable: closureReachable,
    }
  })
}

function build() {
  const eligibleRenderCases = buildEligibleRenderRecords()
  const ineligibleRenderCases = buildIneligibleRenderRecords()
  const closureProbeCases = buildClosureProbeRecords()
  const directScalarRows = buildDirectScalarRows()
  const directClosureMutations = buildDirectClosureMutations()
  const fullRenderMutations = buildFullRenderMutations()

  const totalCases = eligibleRenderCases.length + ineligibleRenderCases.length + closureProbeCases.length
  const eligibleCount = eligibleRenderCases.length + closureProbeCases.filter(c => c.eligible_for_native_binding).length
  const ineligibleCount = ineligibleRenderCases.length

  return {
    schema: 'noisemaker-for-cpp.future-precompute.task31.caustic-floatbits-scalar-xor-oracles.v1',
    corpus_revision: revision,
    provenance: { ...provenance, node: process.version, public_identity: true, adapter_absent: true },
    program: {
      key, defines: { ...AUTHORIZED_DEFINES }, profile_candidate: 'caustic-floatbits-scalar-xor-v1',
      closure: {
        owning_function: 'randomFromLatticeWithOffset', owning_function_id: 94,
        floatBitsToUint_sites: 1, scalar_uint_xor_sites: 3,
        helper_text_sha256: helperTextSha256,
        site_anchor_occurrence_checked: true,
      },
      reachability_finding: reachabilityFinding,
    },
    fixture: {
      full_render: 'no input texture (resources: samplers=()); uniforms + defines only',
      fragment_origin: 'bottom-left runPass coordinates',
      direct_closure_probe: 'byte-for-byte extraction of constant/constantOffset/randomFromLatticeWithOffset from the pinned public factory text, invoked directly with synthetic (including non-integer) arguments',
    },
    eligible_render_cases: eligibleRenderCases,
    ineligible_render_cases: ineligibleRenderCases,
    direct_closure_probe_cases: closureProbeCases,
    direct_scalar_rows: directScalarRows,
    direct_closure_mutations: directClosureMutations,
    full_render_mutations: fullRenderMutations,
    eligibility_summary: {
      total_cases: totalCases, eligible_cases: eligibleCount, ineligible_cases: ineligibleCount,
      eligible_render_cases: eligibleRenderCases.length, ineligible_render_cases: ineligibleRenderCases.length,
      eligible_direct_closure_probe_cases: closureProbeCases.filter(c => c.eligible_for_native_binding).length,
    },
    negative_closure: {
      any_other_define_map: 'reject', generic_floatBitsToUint_capability: 'forbidden',
      uintBitsToFloat: 'absent, forbidden', float_to_uint32_reused_for_floatBitsToUint: 'forbidden',
      any_uint_xor_site_outside_the_three_authenticated_nodes: 'reject',
      perlin_scalar_uint_xor_profile_reuse: 'forbidden',
    },
    risks_and_rejected_designs: [
      {
        id: 'nan-bit-pattern-cross-engine-parity',
        severity: 'flag-for-operator-signoff',
        description: 'GLSL NaN bit-pattern behavior is implementation-defined. This oracle pins the exact bit pattern V8/Node produces for a plain `NaN` double routed through floatBitsToUint (Float32Array/Uint32Array alias): direct_scalar_rows entry with seedFrac_double_repr="NaN" freezes fracBits_hex=0x7fc00000 (a canonical quiet NaN, sign=0, all-mantissa-MSB-set). A C++ static_cast<double,NaN> -> float -> std::bit_cast<uint32_t> is NOT guaranteed to reproduce this exact payload/quiet-bit pattern on every platform/compiler. This is not exercised by any legitimate uniform-driven call path in this program (seedFrac is always fract() of a finite value in every real caller), so it is LOW practical risk for Caustic specifically, but is frozen here and flagged per the brief\'s explicit request rather than silently assumed to match.',
      },
      {
        id: 'xor-operand-order-swap-rejected',
        severity: 'rejected-non-discriminating',
        description: 'The brief suggests "swapping operand order where that changes results" as an XOR-site mutation. Rejected: binary ^ is commutative, so swapping (cpu_umul(fracBits, K) ^ MAGIC) to (MAGIC ^ cpu_umul(fracBits, K)) produces bit-identical results for every input -- a mutation that diverges in 0 cases by construction, exactly the Task 30 "useless mutation" trap. Replaced with genuinely non-commutative-preserving operator swaps (+, |, &) that do discriminate, verified per-case above.',
      },
      {
        id: 'plus-or-mutations-non-discriminating-at-any-full-render-uniform',
        severity: 'documented-not-a-flaw',
        description: 'The xor-site-1-to-add and xor-site-2-to-or mutations never discriminate via ANY full-kernel render (eligible or not), because 0 is the identity element for + and | and seedFrac is always exactly 0.0 on every legitimate call path (uniform int seed). This is not a defect in the mutation choice -- it is a genuine property of this program\'s uniform surface, independently confirmed by the AND mutation (0 & X = 0 != X = 0 ^ X) discriminating at the same reachable-but-ineligible NOISE_TYPE values where + and | do not. All four mutations DO discriminate via the direct-closure-probe surface, which is not restricted to integer s.',
      },
    ],
  }
}

function report(d) {
  const lines = [
    '# Task31 Caustic floatBitsToUint + scalar uint XOR closure oracle report', '',
    `Eligible full-render cases: **${d.eligible_render_cases.length}**; ineligible full-render cases: **${d.ineligible_render_cases.length}**; direct closure-probe cases: **${d.direct_closure_probe_cases.length}** (all eligible); direct scalar rows: **${d.direct_scalar_rows.length}**.`,
    '', '## Critical correction to the design brief', '',
    `The brief's Oracle Requirements section claims the XOR closure is "live, reachable, rendered code" at NOISE_TYPE=10, unlike Perlin's dead-code XORs. This is **contradicted** by direct, reproducible evidence: static call-graph analysis via \`tools.glslcpp.generate_typed_slice\` shows \`randomFromLatticeWithOffset\` is unreachable from \`main()\` at the one authorized define map \`{"NOISE_TYPE": 10}\` (only \`simplexValue\` is called), and dynamic mutation testing against the real, hash-pinned JS reference confirms zero output divergence for all 4 structural mutations across every eligible full-render case. See \`program.reachability_finding\` in the JSON for full evidence. This oracle uses direct invocation of the byte-for-byte-extracted public factory function as the authoritative closure-parity surface instead.`,
    '', '## Eligible full-render cases (NOISE_TYPE=10 only)', '',
    '| Case | Size | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- |',
  ]
  for (const c of d.eligible_render_cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`)
  lines.push('', '## Ineligible full-render cases (define-eligibility risk demonstration)', '', '| Case | Defines | closure_reachable | F32 SHA-256 |', '| --- | --- | --- | --- |')
  for (const c of d.ineligible_render_cases) lines.push(`| ${c.name} | ${JSON.stringify(c.defines)} | ${c.closure_reachable} | \`${c.output.f32_sha256}\` |`)
  lines.push('', '## Direct closure-probe cases (authoritative closure parity surface)', '', '| Case | s | seedFrac | fracBits | result bits |', '| --- | --- | --- | --- | --- |')
  for (const c of d.direct_closure_probe_cases) lines.push(`| ${c.name} | ${c.inputs.s} | ${c.seedFrac} | ${c.fracBits_hex} | ${c.result_bits.join(', ')} |`)
  lines.push('', '## Direct closure mutations (discriminate via non-integer s)', '', '| Mutation | Discriminating cases |', '| --- | ---: |')
  for (const m of d.direct_closure_mutations) lines.push(`| ${m.id} | ${m.case_results.filter(c => c.diverges).length}/${m.case_results.length} |`)
  lines.push('', '## Full-render mutations (structurally non-discriminating at NOISE_TYPE=10, confirming dead code)', '', '| Mutation | Eligible (NOISE_TYPE=10) divergent | Ineligible diagnostic divergent |', '| --- | ---: | ---: |')
  for (const m of d.full_render_mutations) lines.push(`| ${m.id} | ${m.eligible_case_results.filter(c => c.diverges).length}/${m.eligible_case_results.length} | ${m.ineligible_diagnostic_case_results.filter(c => c.diverges).length}/${m.ineligible_diagnostic_case_results.length} |`)
  lines.push('', 'All 0/N eligible-case rows above are EXPECTED and machine-asserted (see `buildFullRenderMutations` in the generator) -- they demonstrate dead code, not a failed mutation design. All direct-closure-mutation rows are >0/N by construction (asserted at build time); a 0/N row there would abort generation.', '')
  lines.push('## Risks and rejected designs', '')
  for (const r of d.risks_and_rejected_designs) lines.push(`- **${r.id}** (${r.severity}): ${r.description}`, '')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('caustic oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('caustic oracle report drift')
  console.log(`caustic oracle fixture ok (${data.eligible_render_cases.length} eligible + ${data.ineligible_render_cases.length} ineligible render cases, ${data.direct_closure_probe_cases.length} direct closure-probe cases, ${data.direct_scalar_rows.length} direct scalar rows)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
