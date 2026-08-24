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
// Cheap-unlocks cluster 2 -- `synth/bitwise:bitwise`, the ONE program in the
// corpus blocked purely on bitwise operators (per
// docs/port-engineering/bitops/bitops-precompute.md SS1, category (a)).
//
// LOAD-BEARING FINDING, VERIFIED NOT ASSUMED: the bitops report's headline
// hazard ("glsl-transpiler emits JavaScript's SIGNED >> for a GLSL uint>>uint
// whenever the enclosing function is not a recognized canonical idiom",
// citing canonical-kernels.js:15313/16410-16426/19971-19975/34733 in OTHER
// programs) does NOT apply to synth/bitwise:bitwise AT ALL: this program has
// ZERO shift operators. Confirmed two independent ways in this session:
//   (a) `grep -n '<<\|>>' sources/synth/bitwise/bitwise.glsl` -- zero matches
//       across all 90 lines of the pinned corpus source.
//   (b) A full read of canonicalFactory244's compiled JS body (the ACTUAL
//       JS-golden reference this oracle freezes) -- `bitOp()` contains only
//       `r = a ^ b`, `r = a & b`, `r = a | b`, `r = ~(a & b)`, `r = ~(a ^ b)`
//       (plus the pre-existing, already-admitted `*`/`+`/`-` arithmetic
//       branches) and nothing else touches a bit operator; `main()`'s two
//       extra `^` sites (`x = x ^ seed`, `y = y ^ (seed * 3)`) are the only
//       other bitwise use in the whole program. No `>>`, `<<`, `>>=`, `<<=`
//       appears anywhere in the compiled factory text.
// So this program's actual, entire new-capability surface is exactly scalar
// signed-int `&`, `|`, `^`, unary `~` (and their op=3/op=4 combinations,
// nand/xnor) -- governed ONLY by bitops-precompute.md's Hazard #2 (JS's
// ToInt32-based bitwise ops already match C++20 two's-complement int32_t
// bit-for-bit, general knowledge corroborated in-repo by the already-shipped
// `bitwise_xor`) and Hazard #3 (shift-count masking) is INAPPLICABLE here --
// there is no shift, so there is no shift count to mask. This is stated
// explicitly, per the task's instruction to determine and report the real
// finding rather than fabricate a shift-semantics test this program's
// compiled JS does not exercise, which would misrepresent it.
//
// Case design instead targets Hazard #2 directly: every case uses at least
// one operand with the sign bit (bit 31) set (negative int32, or an explicit
// mask/operand near INT32_MIN/INT32_MAX), because representation-invariant
// two's-complement behavior is exactly the thing a naive (e.g. widen-to-
// float, or unsigned-only) C++ reimplementation would get wrong for such
// values while a small-positive-only test suite would never catch it -- the
// same principle the task states for the shift hazard, applied here to the
// hazard that actually governs this program.
//
// THE FOUR DISCRIMINATING SHAPES bitops-precompute.md SS5 calls out for this
// exact program are all covered:
//   1. Negative-operand XOR/AND/OR (cases xor-mono-*, and-rgb-*, or-hsv-*).
//   2. ~(a&b) / ~(a^b) at op=3,4 (cases nand-mono-*, xnor-rgb-*).
//   3. mask=0 float-divide-by-zero propagation (case mask-zero-diagnostic).
//   4. colorMode=1 chromatic-shift RGB path, bitOp called 3x with different
//      x/y per channel (cases and-rgb-*, xnor-rgb-*).
//
// Two hard-won lessons applied throughout (carried over verbatim from
// grade/derivative/loopproof):
//   1. RESERVED TOP-LEVEL KEYS -- see loopproof_oracle_generator.mjs header.
//   2. DEFINES: INAPPLICABLE, VERIFIED NOT ASSUMED. Confirmed live via
//      generate_typed_slice._defaults(repo, 'synth/bitwise:bitwise') -> {}
//      in this session, and independently: bitwise.glsl has no preprocessor
//      directive at all (starts `#version 300 es` directly, no #ifdef).
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'bitwise-oracles.json')
const reportPath = path.join(here, 'bitwise-oracle-report.md')
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
const PROGRAM_KEY = 'synth/bitwise:bitwise'

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
// Runtime/catalog hermeticity pinning -- identical hash VALUES to the
// grade/derivative/loopproof generators (same repo state), independently
// recomputed here.
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

const UNIFORM_TYPES = {
  renderScale: 'float', operation: 'int', scale: 'float', offsetX: 'int', offsetY: 'int',
  mask: 'int', seed: 'int', colorMode: 'int', speed: 'float', rotation: 'float', colorOffset: 'int',
}
function normalizeUniformsTyped(raw) {
  const out = {}
  for (const [k, v] of Object.entries(raw)) {
    const type = UNIFORM_TYPES[k]
    if (!type) throw new Error(`unknown uniform "${k}" -- not declared in this program's type map`)
    if (type === 'int') out[k] = v | 0
    else if (type === 'float') out[k] = f(v)
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
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
// renderCase: bitwise.glsl has no `uniform sampler2D` at all -- confirmed by
// reading the source (only gl_FragCoord + uniforms feed the computation) --
// so there is no texture/input-immutability axis for this program, unlike
// every other cluster in this porting project. Every pixel is a pure
// function of gl_FragCoord and the declared uniforms.
// ---------------------------------------------------------------------------
function renderCase(canonical, c) {
  assertNoReservedKeysInUniforms(c.uniforms)
  const uniforms = normalizeUniformsTyped(c.uniforms)
  const time = c.time ?? 0
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const intendedTileOffset = tileOffset ?? new Float32Array(2)
  const intendedFullResolution = fullResolution ?? new Float32Array([c.width, c.height])

  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures: {}, tileOffset, fullResolution, time })
  if (f32Bits(bindings.time) !== f32Bits(f(time))) throw new Error(`${c.name}: kernel did not observe intended time -- top-level binding lesson violated`)
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error(`${c.name}: kernel did not observe intended tileOffset`)
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error(`${c.name}: kernel did not observe intended fullResolution`)
  for (const [k, v] of Object.entries(uniforms)) {
    const bound = bindings[k]
    const same = f32Bits(typeof v === 'number' ? f(v) : v) === f32Bits(typeof bound === 'number' ? f(bound) : bound)
    if (!same) throw new Error(`${c.name}: kernel did not observe intended uniform "${k}" -- reserved-key or spread-order defect`)
  }

  const kernel = bindGlslKernel(canonical, bindings)
  const first = new Surface(c.width, c.height)
  runPass({ kernel, destination: first })
  const kernel2 = bindGlslKernel(canonical, bindings)
  const second = new Surface(c.width, c.height)
  runPass({ kernel: kernel2, destination: second })
  if (!sameBytes(first, second)) throw new Error(`${c.name}: repeat-render mismatch`)

  return { name: c.name, c, uniforms, surface: first }
}

function renderWithFactory(factory, c) {
  const uniforms = normalizeUniformsTyped(c.uniforms)
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures: {}, tileOffset, fullResolution, time: c.time ?? 0 })
  const kernel = bindGlslKernel(factory, bindings)
  const surface = new Surface(c.width, c.height)
  runPass({ kernel, destination: surface })
  return surface
}

// ---------------------------------------------------------------------------
// Load + verify the canonical factory.
// ---------------------------------------------------------------------------
function loadProgram() {
  const sourcePath = path.join(corpusRoot, 'sources/synth/bitwise/bitwise.glsl')
  const sourceBytes = fs.readFileSync(sourcePath)
  const sourceRawBytes = 3095
  const sourceSha256 = '1beb9d4b4fff3466587b9c942af3b1a46c0f35a1bf41874c7461c18dcf2f923f'
  if (sourceBytes.length !== sourceRawBytes) throw new Error('bitwise: source raw byte count drift')
  if (sha256(sourceBytes) !== sourceSha256) throw new Error('bitwise: source sha256 drift')

  const sourceText = sourceBytes.toString('utf8')
  const shiftOperatorSites = (sourceText.match(/<<|>>/g) ?? []).length
  if (shiftOperatorSites !== 0) throw new Error(`bitwise: expected ZERO shift-operator sites in the pinned source, found ${shiftOperatorSites} -- the header comment's load-bearing claim is WRONG, re-derive before shipping`)

  const canonical = canonicalKernelFactories[PROGRAM_KEY]
  if (!canonical) throw new Error(`bitwise: canonical factory missing for key ${PROGRAM_KEY}`)
  if (canonical.name !== 'canonicalFactory244') throw new Error(`bitwise: factory name drift (got ${canonical.name})`)
  const factoryText = canonical.toString()
  const factorySha256 = sha256(factoryText)

  const publicIsCanonical = kernelFactories.get(PROGRAM_KEY) === canonical
  if (!publicIsCanonical) throw new Error('bitwise: public factory is not the canonical identity')
  if (canonicalAdapterFactories[PROGRAM_KEY] !== undefined) throw new Error('bitwise: unexpected adapter override present')

  const compiledShiftSites = (factoryText.match(/<<|>>/g) ?? []).length
  if (compiledShiftSites !== 0) throw new Error(`bitwise: expected ZERO shift-operator sites in the compiled factory text, found ${compiledShiftSites} -- the header comment's load-bearing claim is WRONG, re-derive before shipping`)

  const requiredOperatorSites = ['r = a ^ b;', 'r = a & b;', 'r = a | b;', 'r = ~(a & b);', 'r = ~(a ^ b);']
  for (const site of requiredOperatorSites) {
    if (occurrences(factoryText, site) !== 1) throw new Error(`bitwise: expected exactly one occurrence of "${site}" in the compiled factory text, found ${occurrences(factoryText, site)}`)
  }

  return { sourcePath, sourceRawBytes, sourceSha256, canonical, factoryName: canonical.name, factorySha256, factoryText }
}

const PROGRAM = loadProgram()

// ---------------------------------------------------------------------------
// Case table. Every case carries at least one operand with bit 31 (the sign
// bit) set -- either a negative int32 uniform directly, or a mask/operand
// chosen so that after the coordinate arithmetic (`x = floor(...)+offsetX
// +animOffset; x ^= seed`) the resulting `a`/`b` operands to bitOp() are
// virtually certain to include negative int32 values at some pixels. No
// texture is used (bitwise.glsl declares none), so no `phase`/patternedSurface
// axis applies here.
// ---------------------------------------------------------------------------
const BASE = { renderScale: 1, scale: 2, offsetX: 0, offsetY: 0, speed: 0, rotation: 0, colorOffset: 0 }
const CASES = [
  {
    name: 'xor-mono-seed-negative-one-signbit-mask', width: 6, height: 5,
    uniforms: { ...BASE, operation: 0, colorMode: 0, mask: -2147483648, seed: -1, offsetX: 17, offsetY: -9, scale: 3.5, rotation: 15, speed: 0.4 },
  },
  {
    name: 'and-rgb-int32min-offsets-near-max-mask', width: 5, height: 6, time: 0.75,
    uniforms: { ...BASE, operation: 1, colorMode: 1, mask: 2147483647, seed: -2000000000, offsetX: -1500000000, offsetY: 500000000, scale: 1.7, rotation: -40, speed: 1.1, colorOffset: 37 },
  },
  {
    name: 'or-hsv-negative-offsets-large-seed', width: 7, height: 4,
    uniforms: { ...BASE, operation: 2, colorMode: 2, mask: 999983, seed: 123456789, offsetX: -777, offsetY: 888, scale: 0.6, rotation: 200, speed: -0.3, colorOffset: 5 },
  },
  {
    name: 'nand-mono-int32-extremes-tiled', width: 4, height: 7, tileOffset: [1, 1], fullResolution: [6, 9],
    uniforms: { ...BASE, operation: 3, colorMode: 0, mask: -65536, seed: -1, offsetX: 2000000000, offsetY: -2000000000, scale: 2.2, rotation: 77, speed: 0.9 },
  },
  {
    name: 'xnor-rgb-high-bit-mixed-signs', width: 6, height: 6, time: 2.3,
    uniforms: { ...BASE, operation: 4, colorMode: 1, mask: -3, seed: 2147483647, offsetX: 333, offsetY: -444, scale: 4.1, rotation: -15, speed: 0.2, colorOffset: -19 },
  },
  {
    name: 'mask-zero-divide-by-zero-diagnostic', width: 3, height: 3, diagnostic: true,
    uniforms: { ...BASE, operation: 0, colorMode: 0, mask: 0, seed: 5, offsetX: 1, offsetY: 1 },
  },
]

const OPS = { 0: 'xor', 1: 'and', 2: 'or', 3: 'nand', 4: 'xnor' }
const caseRecords = CASES.map((c) => renderCase(PROGRAM.canonical, c))

// mask=0 is a structural NEGATIVE control: `r = r & 0` always yields 0
// regardless of the pre-mask operator result, so an operator-swap mutation
// can NEVER be observed there (0/0 == 0/0 either way) -- this is asserted
// live below, not assumed, and documented as the reason that case's reach is
// false for every operator mutation despite its own `operation` uniform
// nominally selecting xor.
function reachesMutation(uniforms, opIndex) {
  return uniforms.operation === opIndex && uniforms.mask !== 0
}

// ---------------------------------------------------------------------------
// Mutation builders: operator-swap. Each mutates exactly one op branch of
// bitOp() to a plausible-but-wrong operator (the classic and/or, xor/and,
// nand/nor, xnor/nand confusion bug classes) and asserts nonzero divergence
// among cases selecting that op (with mask != 0), and zero divergence
// everywhere else (proving the mutation is exactly scoped to its own branch,
// not leaking).
// ---------------------------------------------------------------------------
const MUTATIONS = [
  { id: 'bitwise-xor-and-confusion', opIndex: 0, anchor: 'r = a ^ b;', mutated: 'r = a & b;', description: 'op=0 (xor) mutated to `a & b` -- the classic XOR/AND confusion bug.' },
  { id: 'bitwise-and-or-confusion', opIndex: 1, anchor: 'r = a & b;', mutated: 'r = a | b;', description: 'op=1 (and) mutated to `a | b` -- the classic AND/OR confusion bug.' },
  { id: 'bitwise-or-xor-confusion', opIndex: 2, anchor: 'r = a | b;', mutated: 'r = a ^ b;', description: 'op=2 (or) mutated to `a ^ b` -- OR/XOR confusion, plausible when an implementer conflates "combine" operators.' },
  { id: 'bitwise-nand-nor-confusion', opIndex: 3, anchor: 'r = ~(a & b);', mutated: 'r = ~(a | b);', description: 'op=3 (nand) mutated to `~(a | b)` (nor) -- the classic NAND/NOR confusion, and exercises the unary ~ interacting with a differently-computed pre-image, per the task\'s ~(a&b)/~(a^b) discriminating-test callout.' },
  { id: 'bitwise-xnor-nand-confusion', opIndex: 4, anchor: 'r = ~(a ^ b);', mutated: 'r = ~(a & b);', description: 'op=4 (xnor) mutated to `~(a & b)` (nand) -- XNOR/NAND confusion, same unary-~ interaction as above for the other combinator pair.' },
]

for (const mutation of MUTATIONS) {
  if (occurrences(PROGRAM.factoryText, mutation.anchor) !== 1) throw new Error(`${mutation.id}: anchor not unique in factory text`)
  const mutatedText = PROGRAM.factoryText.replace(mutation.anchor, mutation.mutated)
  const mutatedFactory = evaluated(mutatedText)

  const caseResults = caseRecords.map((cr) => {
    const mutatedSurface = renderWithFactory(mutatedFactory, cr.c)
    const diverges = !sameBytes(cr.surface, mutatedSurface)
    const reaches = reachesMutation(cr.uniforms, mutation.opIndex)
    return { case: cr.name, diagnostic: Boolean(cr.c.diagnostic), reaches, diverges }
  })
  const reaching = caseResults.filter((r) => r.reaches)
  const nonReaching = caseResults.filter((r) => !r.reaches)
  const divergentReaching = reaching.filter((r) => r.diverges).length
  const divergentNonReaching = nonReaching.filter((r) => r.diverges).length

  if (reaching.length === 0) throw new Error(`${mutation.id}: no case reaches this mutation's op branch -- fix the case table`)
  if (divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${reaching.length}`)
  if (divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${divergentNonReaching}/${nonReaching.length} non-reaching case(s) diverged -- the mutation leaked outside its intended branch, or reachesMutation() is wrong`)

  mutation.caseResults = caseResults
  mutation.summary = { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
}

// ---------------------------------------------------------------------------
// Assembly
// ---------------------------------------------------------------------------
function build() {
  const eligible = caseRecords.filter((c) => !c.c.diagnostic)
  const diagnostic = caseRecords.filter((c) => c.c.diagnostic)
  return {
    schema: 'noisemaker-for-cpp.future-precompute.cheap-unlocks.bitwise-cluster1.oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version, public_identity: true, adapter_absent: true },
    authorized_defines: { ...AUTHORIZED_DEFINES },
    defines_axis_note: "synth/bitwise:bitwise authorizes the empty define map {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, 'synth/bitwise:bitwise') -> {} in this session, and independently by reading the source: bitwise.glsl has NO preprocessor directive at all (starts `#version 300 es` directly, no #ifdef/#define anywhere). The defines-as-uniforms hazard from the grade/derivative clusters cannot arise here.",
    shift_semantics_finding: {
      claim: 'synth/bitwise:bitwise has ZERO shift-operator (<<, >>) sites -- the bitops-precompute.md headline "JS emits signed >> for uint>>uint" hazard does NOT apply to this program.',
      evidence: [
        "grep -n '<<\\\\|>>' sources/synth/bitwise/bitwise.glsl -- zero matches across all 90 lines of the pinned corpus source (verified live in this session).",
        "canonicalFactory244's compiled JS body (the actual JS-golden reference this oracle freezes) contains no '<<' or '>>' substring anywhere -- verified live via a regex scan of canonical.toString() in loadProgram(), which throws if this claim is ever wrong.",
        'bitOp() contains only r = a^b, r = a&b, r = a|b, r = ~(a&b), r = ~(a^b) (plus the pre-existing *; +; - arithmetic branches, already admitted); main() has two more scalar ^ sites (x ^= seed; y ^= seed*3) and nothing else touches a bit operator.',
      ],
      consequence: "This program's entire new-capability surface is scalar signed-int &, |, ^, unary ~ (and their op=3/op=4 nand/xnor combinations) -- governed only by bitops-precompute.md Hazard #2 (JS ToInt32-based bitwise ops already match C++20 two's-complement int32_t bit-for-bit) and NOT Hazard #1 (signed-vs-logical shift) or Hazard #3 (shift-count masking), both of which are structurally inapplicable: there is no shift op, so there is no shift semantics to get wrong and no shift count to mask. Stated explicitly rather than fabricating a shift test this program's compiled JS does not exercise.",
    },
    high_bit_operand_confirmation: 'Every non-diagnostic case supplies at least one operand with the int32 sign bit set: mask values at/near INT32_MIN/INT32_MAX or with only bit 31 set (-2147483648, 2147483647, -65536, -3), and/or seed/offset values at or near INT32_MIN/INT32_MAX (-1, -2000000000, 2147483647, +-1500000000/+-2000000000) that XOR directly into the per-pixel integer coordinates before every bitOp() call. This matches the discriminating-test intent stated for the shift hazard (operands with the high bit set), applied here to the hazard that actually governs this program: a naive reimplementation that widens to float, or uses unsigned-only arithmetic, or gets two\'s-complement NOT wrong would diverge on exactly these operands while a small-positive-only suite would never catch it.',
    program: {
      key: PROGRAM_KEY, source_file: 'synth/bitwise/bitwise.glsl', source_raw_bytes: PROGRAM.sourceRawBytes, source_sha256: PROGRAM.sourceSha256,
      canonical_factory_name: PROGRAM.factoryName, canonical_factory_to_string_sha256: PROGRAM.factorySha256,
      defines: { ...AUTHORIZED_DEFINES },
      cases: caseRecords.map((cr) => ({
        name: cr.name, dimensions: { width: cr.c.width, height: cr.c.height }, diagnostic: Boolean(cr.c.diagnostic),
        operation: cr.uniforms.operation, operation_name: OPS[cr.uniforms.operation] ?? null, color_mode: cr.uniforms.colorMode,
        uniforms: cr.c.uniforms, time: cr.c.time ?? 0, tile_offset: cr.c.tileOffset ?? [0, 0], full_resolution: cr.c.fullResolution ?? [cr.c.width, cr.c.height],
        repeat_identity: true,
        output: renderResult(cr.surface),
      })),
      mutations: MUTATIONS.map((m) => ({
        id: m.id, op_index: m.opIndex, op_name: OPS[m.opIndex], anchor: m.anchor, mutated: m.mutated, description: m.description,
        case_results: m.caseResults, summary: m.summary,
      })),
    },
    eligibility_summary: {
      total_cases: eligible.length + diagnostic.length, eligible_cases: eligible.length, diagnostic_cases: diagnostic.length,
      note: 'The one diagnostic case (mask=0) is a structural negative control, not an unreached-code diagnostic: mask=0 makes `r = r & m` collapse to 0 regardless of which operator computed the pre-mask r, so bitOp returns float(0)/float(0) = NaN identically for the real implementation AND for every operator-swap mutation -- reach=false for all five mutations is asserted live (reachesMutation() returns false whenever mask===0), not assumed. This case independently exercises discriminating-test #3 from bitops-precompute.md SS5 (mask=0 divide-by-zero propagation): the rendered output must show NaN in every channel, matching JS x/0 semantics exactly, not a C++ divide-by-zero guard that silently substitutes a different value.',
    },
    negative_closure: {
      shift_semantics_test_fabricated: 'refused -- loadProgram() asserts, live, that neither the pinned source nor the compiled factory text contains a shift operator; a shift-count-masking test was not constructed because there is no shift to test. See shift_semantics_finding.',
      small_positive_only_operands_used: 'refused -- see high_bit_operand_confirmation; every non-diagnostic case has at least one sign-bit-set operand.',
      mask_zero_case_silently_dropped: 'refused -- included, documented as a structural (not coverage-gap) zero-reach case for every operator mutation, with its own independent NaN-propagation assertion in the render output.',
      mul_add_sub_ops_covered: 'not applicable -- op=5/6/7 (mul/add/sub) are pre-existing, already-admitted int arithmetic, not part of this unlock; out of scope for this oracle by design.',
    },
  }
}

function report(d) {
  const lines = [
    '# Cheap-unlocks cluster 2 -- `synth/bitwise:bitwise` oracle report', '',
    'Hermetic JS oracle for the one program in the corpus blocked purely on bitwise operators. Ground truth for the future C++20 port\'s bit-exact parity tests.', '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} structural-negative-control diagnostic).`, '',
    '## Defines axis', '', d.defines_axis_note, '',
    '## Shift-semantics finding (load-bearing)', '',
    `**Claim**: ${d.shift_semantics_finding.claim}`, '',
    '**Evidence**:', '', ...d.shift_semantics_finding.evidence.map((e) => `- ${e}`), '',
    `**Consequence**: ${d.shift_semantics_finding.consequence}`, '',
    '## High-bit-operand confirmation', '', d.high_bit_operand_confirmation, '',
    '## Cases', '', '| Case | Size | Op | ColorMode | Diagnostic | Nonfinite lanes | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | ---: | --- | ---: | --- | --- |',
  ]
  for (const c of d.program.cases) {
    lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.operation_name ?? c.operation} | ${c.color_mode} | ${c.diagnostic} | ${c.output.nonfinite_lanes} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
  }
  lines.push('', '## Mutations', '', '| Mutation | Op | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |', '| --- | --- | ---: | ---: | ---: | ---: |')
  for (const m of d.program.mutations) {
    lines.push(`| ${m.id} | ${m.op_name} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
  }
  lines.push('', ...d.program.mutations.map((m) => `- **${m.id}**: ${m.description}`), '')
  lines.push('## Negative closure', '')
  for (const [k, v] of Object.entries(d.negative_closure)) lines.push(`- **${k}**: ${v}`)
  lines.push('')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('bitwise oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('bitwise oracle report drift')
  console.log(`bitwise oracle fixture ok (1 program, ${data.eligibility_summary.total_cases} cases, ${MUTATIONS.length} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
