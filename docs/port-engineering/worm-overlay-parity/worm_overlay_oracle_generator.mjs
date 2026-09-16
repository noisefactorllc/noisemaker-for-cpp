#!/usr/bin/env node
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// ---------------------------------------------------------------------------
// `filter/{fibers,scratches,strayHair}` canonical CPU worm-overlay oracle.
//
// Ground truth is `renderCanonicalWormOverlay` (noisemaker-for-cpu:
// src/effects/cpu/worm-overlay.js), imported UNMODIFIED and called directly
// -- never reimplemented for golden values. Methodology mirrors
// docs/port-engineering/wormhole/oracle/wormhole_oracle_generator.mjs
// (provenance pinning, determinism self-check, text-surgery mutation
// testing with independently-computed reach predicates) adapted to this
// function's shape: a self-seeding hand-written CPU adapter (no scatter
// pass, no input surface -- it allocates and fills its own Surface).
//
// Usage:
//   node worm_overlay_oracle_generator.mjs --cpu-root <path> [--check]
// `--cpu-root` (or $NOISEMAKER_CPU_ROOT) must name a checkout of the pinned
// authority revision 61aa869.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'worm-overlay-oracles.json')
const reportPath = path.join(here, 'worm-overlay-oracle-report.md')

function arg(name) {
  const index = process.argv.indexOf(name)
  return index === -1 ? null : process.argv[index + 1]
}

const cpuRoot = arg('--cpu-root') ?? process.env.NOISEMAKER_CPU_ROOT
if (!cpuRoot) {
  console.error('usage: worm_overlay_oracle_generator.mjs --cpu-root <path> [--check]  (or set $NOISEMAKER_CPU_ROOT)')
  process.exit(2)
}

const wormOverlayPath = path.join(cpuRoot, 'src/effects/cpu/worm-overlay.js')
const surfacePath = path.join(cpuRoot, 'src/runtime/surface.js')

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function occurrences(text, needle) { return needle.length === 0 ? 0 : text.split(needle).length - 1 }
function pinnedHash(filePath) { return sha256(fs.readFileSync(filePath)) }

// Pinned sha256 of every source file this oracle depends on, computed via
// this same sha256() function against the live files at authoring time,
// then frozen here. Re-verified against the live files at load; any drift
// throws immediately.
const PROVENANCE = {
  worm_overlay_js_sha256: '4b180a359e477061ef18532707e9516a662c6463e179246dd5f4e118563f208d',
  surface_js_sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
}
const LIVE = {
  worm_overlay_js_sha256: pinnedHash(wormOverlayPath),
  surface_js_sha256: pinnedHash(surfacePath),
}
for (const key of Object.keys(PROVENANCE)) {
  if (PROVENANCE[key] !== LIVE[key]) throw new Error(`provenance drift: ${key} (pinned ${PROVENANCE[key]}, live ${LIVE[key]})`)
}

const { renderCanonicalWormOverlay } = await import(`file://${wormOverlayPath}`)

const f32scratch = new Float32Array(1)
const u32scratch = new Uint32Array(f32scratch.buffer)
function bitsU32(value) { f32scratch[0] = value; return u32scratch[0] }
function bitsHex(value) { return `0x${bitsU32(value).toString(16).padStart(8, '0')}` }

// `SeededRng.float()`/`.normal()` return full JS doubles, NOT float32 --
// unlike the Surface/valueNoiseField data (both genuinely Float32Array).
// Using the float32 `bitsHex` above on a double would silently narrow it
// first and only ever check the top 32 bits' worth of precision. This
// captures the real 64-bit IEEE-754 pattern.
const f64scratch = new Float64Array(1)
const u64scratch = new BigUint64Array(f64scratch.buffer)
function bitsHexF64(value) { f64scratch[0] = value; return `0x${u64scratch[0].toString(16).padStart(16, '0')}` }
function bytesOf(float32Array) { return Buffer.from(float32Array.buffer, float32Array.byteOffset, float32Array.byteLength) }
function sameSurfaceBytes(a, b) { return Buffer.compare(bytesOf(a.data), bytesOf(b.data)) === 0 }

// ---------------------------------------------------------------------------
// Case matrix. Chosen to cover: all 3 effect ids; several seeds (integer,
// zero/falsy, negative, fractional, huge -- ToUint32 stress); several sizes
// including 1x1 (forces `iterations===1`, skipping the `iterations>1`
// lifetime ternary), non-square, and a size matching the DSL corpus lane's
// own 17x11 fixture; several densities including 0 (density floor via
// `Math.max(1, ...)`) and large. `seed=0`/`seed=NaN` specifically exercise
// the `params.seed || 1` fallback branch (JS-falsy, not just "zero").
// ---------------------------------------------------------------------------
const EFFECT_IDS = ['filter/fibers', 'filter/scratches', 'filter/strayHair']

const CASE_DEFS = [
  // Defaults at the corpus lane's own fixture size.
  { name: 'default-17x11', width: 17, height: 11, seed: 1, density: 1 },
  // 1x1 forces iterations<=1 (the `iterations>1 ? ... : 1` false branch) and
  // count===1 via the density floor.
  { name: 'tiny-1x1', width: 1, height: 1, seed: 1, density: 1 },
  { name: 'tiny-2x2', width: 2, height: 2, seed: 3, density: 0.01 },
  // Non-square, both orientations.
  { name: 'wide-33x9', width: 33, height: 9, seed: 7, density: 0.5 },
  { name: 'tall-9x33', width: 9, height: 33, seed: 7, density: 0.5 },
  // A size large enough to exercise many worms/iterations.
  { name: 'moderate-64x48', width: 64, height: 48, seed: 42, density: 1 },
  // seed=0 and NaN both must fall back to 1 (`params.seed || 1`).
  { name: 'falsy-seed-zero', width: 16, height: 16, seed: 0, density: 1 },
  { name: 'falsy-seed-nan', width: 16, height: 16, seed: Number.NaN, density: 1 },
  // Negative and fractional seeds exercise ToUint32's truncate-then-mod path
  // and the `layerSeed % N` fmod-not-integer-mod arithmetic.
  { name: 'negative-seed', width: 20, height: 12, seed: -5, density: 0.3 },
  { name: 'fractional-seed', width: 20, height: 12, seed: 1.6180339887, density: 0.3 },
  { name: 'tiny-fractional-seed', width: 20, height: 12, seed: 0.0001, density: 0.3 },
  // A huge seed stresses ToUint32's modulo-2^32 reduction and the RNG's own
  // double-precision-sensitive multiply/add (see worm_overlay.cpp's
  // `as_js_int32`/rounding comments for what this guards against).
  { name: 'huge-seed', width: 20, height: 12, seed: 123456789012, density: 0.3 },
  // density=0 floors count at 1 via `Math.max(1, Math.floor(...))`.
  { name: 'zero-density', width: 24, height: 16, seed: 5, density: 0 },
  // Large density stresses many worms / heavy overdraw.
  { name: 'large-density', width: 24, height: 16, seed: 5, density: 5 },
  // A second, independent seed/size combination per effect for general
  // sweep coverage beyond the hand-picked control-flow cases above.
  { name: 'sweep-a', width: 11, height: 23, seed: 13, density: 0.7 },
  { name: 'sweep-b', width: 40, height: 40, seed: 99, density: 0.2 },
]

const CASES = []
for (const effectId of EFFECT_IDS) {
  for (const def of CASE_DEFS) CASES.push({ effectId, ...def })
}

// ---------------------------------------------------------------------------
// Render + determinism check.
// ---------------------------------------------------------------------------
function renderCase(kase) {
  const params = { seed: kase.seed, density: kase.density }
  const first = renderCanonicalWormOverlay(kase.effectId, kase.width, kase.height, params)
  const second = renderCanonicalWormOverlay(kase.effectId, kase.width, kase.height, params)
  if (!sameSurfaceBytes(first, second)) {
    throw new Error(`${kase.effectId}/${kase.name}: repeat-render mismatch (determinism failure)`)
  }
  return first
}

for (const kase of CASES) {
  kase.output = renderCase(kase)
}

// ---------------------------------------------------------------------------
// Mutation runtime builder -- extracts worm-overlay.js's real source text,
// verifies it, strips the `import`/`export` wrapper, and evaluates it as a
// standalone function returning `{ renderCanonicalWormOverlay, SeededRng,
// valueNoiseField }`. Applying this to the UNMODIFIED text and cross-
// checking against the real imported function proves the text-surgery
// technique is faithful before any mutation result is trusted.
// ---------------------------------------------------------------------------
const wormOverlaySourceText = fs.readFileSync(wormOverlayPath, 'utf8')
const IMPORT_LINE = "import { Surface } from '../../runtime/surface.js'\n"
const EXPORT_ANCHOR = 'export function renderCanonicalWormOverlay'

function buildRuntimeFromSource(sourceText) {
  if (occurrences(sourceText, IMPORT_LINE) !== 1) throw new Error('import line anchor not found exactly once')
  const withoutImport = sourceText.replace(IMPORT_LINE, '')
  if (occurrences(withoutImport, EXPORT_ANCHOR) !== 1) throw new Error('export anchor not found exactly once')
  const withoutExport = withoutImport.replace(EXPORT_ANCHOR, 'function renderCanonicalWormOverlay')
  const wrapped = `${withoutExport}\nreturn { renderCanonicalWormOverlay, SeededRng, valueNoiseField };\n`
  // eslint-disable-next-line no-new-func
  return new Function('Surface', wrapped)(Surface)
}

function extractBlock(sourceText, startMarker, endMarker) {
  const start = sourceText.indexOf(startMarker)
  if (start === -1) throw new Error(`start marker missing: ${startMarker}`)
  if (sourceText.indexOf(startMarker, start + 1) !== -1) throw new Error(`start marker not unique: ${startMarker}`)
  const endIdx = sourceText.indexOf(endMarker, start)
  if (endIdx === -1) throw new Error(`end marker missing after start marker: ${startMarker} .. ${endMarker}`)
  const block = sourceText.slice(start, endIdx + endMarker.length)
  if (occurrences(sourceText, block) !== 1) throw new Error(`extracted block not unique in source text: ${startMarker}`)
  return block
}

function mutateSource(sourceText, anchor, replacement) {
  if (occurrences(sourceText, anchor) !== 1) throw new Error(`mutation anchor not unique at apply-time: ${anchor.slice(0, 80)}`)
  const mutated = sourceText.replace(anchor, replacement)
  if (mutated === sourceText) throw new Error('mutation produced no textual change')
  return mutated
}

// `Surface` is imported inside the extracted module text via the injected
// function parameter above -- need the real class here too, for the
// self-check and for the direct-row tests below.
const { Surface } = await import(`file://${surfacePath}`)

const REAL = buildRuntimeFromSource(wormOverlaySourceText)

// Text-surgery fidelity self-check: the extracted-from-source-text REAL
// runtime must reproduce the real imported function byte-for-byte on every
// case, before any mutation result is trusted.
for (const kase of CASES) {
  const params = { seed: kase.seed, density: kase.density }
  const reproduced = REAL.renderCanonicalWormOverlay(kase.effectId, kase.width, kase.height, params)
  if (!sameSurfaceBytes(reproduced, kase.output)) {
    throw new Error(`${kase.effectId}/${kase.name}: extracted-runtime self-check mismatch -- text surgery is not faithful, do not trust mutation results`)
  }
}

// ---------------------------------------------------------------------------
// Mutation catalogue. Each declares a `reach` predicate over the case
// definitions (not the diagnostics module -- these are simple enough to
// state directly and are reviewed by hand below).
// ---------------------------------------------------------------------------
const RNG_NEXT_START = '  next() {'
const RNG_NEXT_END = '    return ((word >>> 22) ^ word) >>> 0\n  }'
const rngNextBlock = extractBlock(wormOverlaySourceText, RNG_NEXT_START, RNG_NEXT_END)

const NORMAL_LINE = '    return mean + deviation * Math.sqrt(-2 * Math.log(u1)) * Math.cos(TAU * u2)'
const SMOOTHSTEP_X = '      const smoothX = deltaX * deltaX * (3 - 2 * deltaX)'
const DRAW_BLEND_LINE = '          ? (color[channel] * sourceAlpha + data[offset + channel] * destinationAlpha * (1 - sourceAlpha)) / outputAlpha'
const OBEDIENT_ROTATION_LINE = "    rotation: options.behavior === 'obedient' ? sharedRotation : rng.float() * TAU,"
const FINAL_ROUND_LINE = '  for (let index = 0; index < surface.data.length; index += 1) surface.data[index] = Math.round(Math.min(Math.max(surface.data[index], 0), 1) * 255) / 255'
const KINK_ANGLE_LINE = '      let angle = flow[flowY * surface.width + flowX] * TAU * options.kink'
const SCRATCHES_BEHAVIOR_LINE = "        behavior: layerSeed % 2 === 0 ? 'obedient' : 'unruly',"

const MUTATIONS = [
  {
    id: 'rng-multiplier-tampered',
    hazard: 'the LCG step multiplier is changed, desynchronizing every subsequent draw',
    anchor: rngNextBlock,
    mutated: rngNextBlock.replace('747796405', '747796407'),
    reach: () => true,
  },
  {
    id: 'normal-sqrt-log-sign-flip',
    hazard: 'Box-Muller normal() drops the negation on the log term',
    anchor: NORMAL_LINE,
    mutated: '    return mean + deviation * Math.sqrt(2 * Math.log(u1)) * Math.cos(TAU * u2)',
    // Only observable where stride actually varies the drawn path AND the
    // sqrt argument's sign flip changes real() vs NaN -- reaches every case
    // since Math.log(u1) is always negative (u1 in (0,1)) so the ORIGINAL
    // sqrt argument is always positive and the mutated one always negative
    // (NaN), producing NaN strides everywhere worms are drawn.
    reach: () => true,
  },
  {
    id: 'smoothstep-linear',
    hazard: 'valueNoiseField uses a linear (not smoothstep) interpolation weight',
    anchor: SMOOTHSTEP_X,
    mutated: '      const smoothX = deltaX',
    reach: () => true,
  },
  {
    id: 'draw-blend-ignores-destination',
    hazard: 'alpha compositing drops the destination-blend term (paints flat color)',
    anchor: DRAW_BLEND_LINE,
    mutated: '          ? (color[channel] * sourceAlpha) / outputAlpha',
    reach: () => true,
  },
  {
    id: 'obedient-unruly-swapped',
    hazard: "the 'obedient' shared-rotation branch's condition is inverted",
    anchor: OBEDIENT_ROTATION_LINE,
    mutated: "    rotation: options.behavior !== 'obedient' ? sharedRotation : rng.float() * TAU,",
    // Inverting the CONDITION (not just swapping the two branches) reaches
    // every effect, not only scratches (the only one with a real 'obedient'
    // layer): fibers/strayHair never satisfy the original condition, so
    // they always took the `: rng.float() * TAU` branch (drawing an RNG
    // value); the inverted condition is then always TRUE for them, so they
    // always take `sharedRotation` instead -- both the value AND whether an
    // RNG draw happens change, for every case. A per-case divergence
    // guarantee is not required here, only nonzero divergence among
    // reaching cases and zero among non-reaching -- vacuous since
    // `reach: () => true` excludes nothing.
    reach: () => true,
  },
  {
    id: 'final-quantization-removed',
    hazard: 'the 1/255-step quantization pass is skipped, leaving raw float32 accumulation',
    anchor: FINAL_ROUND_LINE,
    mutated: '  // quantization intentionally removed by mutation',
    reach: () => true,
  },
  {
    id: 'kink-angle-doubled',
    hazard: 'the flow-field kink contribution to the turn angle is doubled',
    anchor: KINK_ANGLE_LINE,
    mutated: '      let angle = flow[flowY * surface.width + flowX] * TAU * options.kink * 2',
    reach: () => true,
  },
  {
    id: 'scratches-obedient-unruly-labels-swapped',
    hazard: "scratches' per-layer 'obedient'/'unruly' dispatch is swapped (layerSeed%2===0 now means unruly)",
    anchor: SCRATCHES_BEHAVIOR_LINE,
    mutated: "        behavior: layerSeed % 2 === 0 ? 'unruly' : 'obedient',",
    // Effect-scoped: only `filter/scratches` reads this line at all
    // (fibers/strayHair never execute this branch). Swapping the ternary's
    // two RESULTS (not its condition) flips every layer's label regardless
    // of which way the condition resolves -- `cond ? A : B` vs `cond ? B :
    // A` disagree on both the true and the false path -- so this reaches
    // (and, checked below, diverges) every scratches case including the
    // two whose `layerSeed % 2 === 0` never holds for any layer. Confirmed
    // empirically: an earlier, narrower `hasObedientLayer`-gated predicate
    // under-reported reach by exactly those 2 cases.
    reach: (kase) => kase.effectId === 'filter/scratches',
  },
]

function runMutation(mutation) {
  const mutatedSourceText = mutateSource(wormOverlaySourceText, mutation.anchor, mutation.mutated)
  const mutatedRuntime = buildRuntimeFromSource(mutatedSourceText)
  const caseResults = CASES.map((kase) => {
    const params = { seed: kase.seed, density: kase.density }
    const mutatedOutput = mutatedRuntime.renderCanonicalWormOverlay(kase.effectId, kase.width, kase.height, params)
    const diverges = !sameSurfaceBytes(mutatedOutput, kase.output)
    const reaches = mutation.reach(kase)
    return { case: `${kase.effectId}/${kase.name}`, reaches, diverges }
  })
  const reaching = caseResults.filter((r) => r.reaches)
  const nonReaching = caseResults.filter((r) => !r.reaches)
  return {
    caseResults,
    reachingCount: reaching.length,
    divergentReaching: reaching.filter((r) => r.diverges).length,
    nonReachingCount: nonReaching.length,
    divergentNonReaching: nonReaching.filter((r) => r.diverges).length,
  }
}

for (const mutation of MUTATIONS) {
  const result = runMutation(mutation)
  mutation.result = result
  if (result.reachingCount === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site -- cannot prove discrimination`)
  if (result.divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${result.reachingCount}`)
  if (result.divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${result.divergentNonReaching}/${result.nonReachingCount} non-reaching case(s) diverged -- reach predicate or mutation scope is wrong`)
}

// ---------------------------------------------------------------------------
// Direct rows: SeededRng.float() sequences for several seeds (using the REAL
// extracted class), and valueNoiseField grid/field samples -- function-level
// ground truth, independent of the full renderCanonicalWormOverlay pipeline.
// ---------------------------------------------------------------------------
const RNG_SEED_ROWS = [1, 0, -5, 1000, 1.6180339887, 123456789012, 4294967295, 4294967296, -1]
const RNG_ROWS = RNG_SEED_ROWS.map((seed) => {
  const rng = new REAL.SeededRng(seed)
  const draws = []
  for (let i = 0; i < 8; i += 1) draws.push(rng.float())
  return { seed, draws, draw_bits: draws.map(bitsHexF64) }
})

const NOISE_FIELD_ROWS = [
  { width: 5, height: 5, frequency: 4, seed: 7 },
  { width: 8, height: 3, frequency: 2.5, seed: 42 },
].map((def) => {
  const rng = new REAL.SeededRng(def.seed)
  const field = REAL.valueNoiseField(def.width, def.height, def.frequency, rng)
  return { ...def, field_bits: Array.from(field, bitsU32), field_sha256: sha256(bytesOf(field)) }
})

// ---------------------------------------------------------------------------
// Assembly.
// ---------------------------------------------------------------------------
function caseToJson(kase) {
  return {
    name: kase.name,
    effect_id: kase.effectId,
    width: kase.width,
    height: kase.height,
    seed: Number.isNaN(kase.seed) ? 'NaN' : kase.seed,
    density: kase.density,
    output_sha256: sha256(bytesOf(kase.output.data)),
    // Full bit array only for the small corpus-matching case, so the native
    // test can do a byte-for-byte comparison without depending solely on a
    // hash for at least one representative, human-inspectable case.
    output_bits: kase.name === 'default-17x11' ? Array.from(kase.output.data, bitsU32) : null,
  }
}

function build() {
  return {
    schema: 'noisemaker-for-cpp.worm-overlay.canonical-cpu-adapter-oracle.v1',
    provenance: {
      ...PROVENANCE,
      node: process.version,
      reference_function: 'renderCanonicalWormOverlay (src/effects/cpu/worm-overlay.js), imported and called directly, never reimplemented for golden values',
      effect_ids: EFFECT_IDS,
    },
    text_surgery_self_check: 'PASS -- extracted-from-source-text runtime reproduces the real imported renderCanonicalWormOverlay byte-for-byte on every case (asserted at build time)',
    rng_rows: RNG_ROWS,
    noise_field_rows: NOISE_FIELD_ROWS,
    mutations: MUTATIONS.map((m) => ({
      id: m.id, hazard: m.hazard,
      summary: { reaching_cases: m.result.reachingCount, divergent_reaching: m.result.divergentReaching, non_reaching_cases: m.result.nonReachingCount, divergent_non_reaching: m.result.divergentNonReaching },
      case_results: m.result.caseResults,
    })),
    cases: CASES.map(caseToJson),
  }
}

function report(d) {
  const lines = [
    '# canonical CPU worm-overlay oracle report', '',
    'Ground truth is `renderCanonicalWormOverlay` (`src/effects/cpu/worm-overlay.js`), imported and called directly -- never reimplemented for golden values.',
    '',
    `Total cases: **${d.cases.length}** (${CASE_DEFS.length} case definitions x ${EFFECT_IDS.length} effect ids).`,
    '',
    '## Provenance', '',
    '| File | sha256 |', '| --- | --- |',
    `| worm-overlay.js | \`${d.provenance.worm_overlay_js_sha256}\` |`,
    `| surface.js | \`${d.provenance.surface_js_sha256}\` |`,
    '',
    `Text-surgery self-check: **${d.text_surgery_self_check}**`, '',
    '## Mutations', '',
    '| Mutation | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |',
    '| --- | ---: | ---: | ---: | ---: |',
  ]
  for (const m of d.mutations) {
    lines.push(`| ${m.id} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
  }
  lines.push('')
  for (const m of d.mutations) lines.push(`- **${m.id}**: ${m.hazard}`)
  lines.push('', '## RNG direct rows', '', `${d.rng_rows.length} seeds x 8 draws each, using the REAL extracted \`SeededRng\` class (see \`worm-overlay-oracles.json\` for the full table).`, '')
  lines.push('## Noise-field direct rows', '', `${d.noise_field_rows.length} (width,height,frequency,seed) combinations.`, '')
  lines.push('## Cases', '', '| Case | Effect | Size | Seed | Density | Output SHA-256 |', '| --- | --- | --- | ---: | ---: | --- |')
  for (const c of d.cases) {
    lines.push(`| ${c.name} | ${c.effect_id} | ${c.width}x${c.height} | ${c.seed} | ${c.density} | \`${c.output_sha256.slice(0, 16)}...\` |`)
  }
  lines.push('')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('worm-overlay oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('worm-overlay oracle report drift')
  console.log(`worm-overlay oracle fixture ok (${data.cases.length} cases, ${data.mutations.length} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
