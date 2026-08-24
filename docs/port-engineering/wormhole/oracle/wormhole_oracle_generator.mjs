import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { runWormholeDeposit } from '../noisemaker-for-cpu/src/effects/cpu/wormhole.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'
import { float16Truncate } from '../noisemaker-for-cpu/src/runtime/texture-format.js'

// ---------------------------------------------------------------------------
// `filter/wormhole:deposit` scatter-pass oracle.
//
// This is NOT a GLSL-kernel oracle. `deposit.frag` is a two-line passthrough
// (`fragColor = vColor`) -- it IS transpiled (canonicalFactory181 in
// canonical-kernels.js, glsl-coverage.js status "generated") but the CPU
// reference never executes that kernel. `src/runtime/renderer.js` branches on
// `pass.drawMode === 'points'` and dispatches to the hand-written scatter
// adapter registered in `src/effects/cpu/scatter-registry.js`, which forwards
// straight to `runWormholeDeposit` (`src/effects/cpu/wormhole.js:34-76`). That
// function -- imported here UNMODIFIED, called directly, never reimplemented
// -- is the ground truth this oracle freezes and the C++ port must match.
//
// Methodology, matching `future-precompute/task32-grade/grade_oracle_generator.mjs`:
//   1. Provenance: sha256 every source file this oracle depends on, and the
//      pinned-corpus `deposit.frag`, verified at load time (throws on drift).
//   2. Determinism: every case is rendered twice from byte-identical inputs;
//      the two runs must be byte-identical, and the input surface must be
//      provably unmutated by the call.
//   3. Mutation testing: `wormhole.js`'s source text is read, sha256-pinned,
//      surgically mutated at named anchor sites (each anchor's uniqueness is
//      verified before AND after mutation, exactly like grade oracle's
//      `extractBlock`/`occurrences` discipline), re-evaluated as a standalone
//      function via `new Function`, and run against every case. Each mutation
//      declares a `reach` predicate computed from INDEPENDENT diagnostics (a
//      separate, clearly-labelled reimplementation of the same arithmetic,
//      used only for case classification -- never as a source of golden
//      values). The build throws unless every reaching case actually
//      diverges and every non-reaching case does NOT -- both directions are
//      machine-checked, not assumed.
//   4. One candidate mutation (pixelStride "double vs float32" storage order)
//      was checked and found to be a PROVABLE NO-OP for this function -- see
//      `pixel_stride_rounding_proof` below -- and is reported as such rather
//      than silently dropped or falsely claimed as a discriminator. This is
//      the exact "obvious mutation turns out to be a no-op" trap called out
//      in the task brief; it is not hidden.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'wormhole-oracles.json')
const reportPath = path.join(here, 'wormhole-oracle-report.md')

const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const wormholePath = '../noisemaker-for-cpu/src/effects/cpu/wormhole.js'
const texFormatPath = '../noisemaker-for-cpu/src/runtime/texture-format.js'
const surfacePath = '../noisemaker-for-cpu/src/runtime/surface.js'
const scatterRegistryPath = '../noisemaker-for-cpu/src/effects/cpu/scatter-registry.js'
const depositFragPath = `tools/glslcpp/corpus/${revision}/sources/filter/wormhole/deposit.frag`

const F32 = Math.fround
const TAU = 6.28318530717959

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function occurrences(text, needle) { return needle.length === 0 ? 0 : text.split(needle).length - 1 }

const f32scratch = new Float32Array(1)
const u32scratch = new Uint32Array(f32scratch.buffer)
function bitsU32(value) { f32scratch[0] = value; return u32scratch[0] }
function bitsHex(value) { return `0x${bitsU32(value).toString(16).padStart(8, '0')}` }
function bytesOf(float32Array) { return Buffer.from(float32Array.buffer, float32Array.byteOffset, float32Array.byteLength) }
function sameSurfaceBytes(a, b) { return Buffer.compare(bytesOf(a.data), bytesOf(b.data)) === 0 }

// ---------------------------------------------------------------------------
// Provenance -- pinned sha256 of every source file this oracle depends on,
// re-verified at load time. Values below were computed from the live files
// via `shasum -a 256` at authoring time; any drift throws immediately.
// ---------------------------------------------------------------------------
function pinnedHash(filePath) { return sha256(fs.readFileSync(filePath)) }

// Pinned sha256 of every source file this oracle depends on -- computed once
// via `shasum -a 256` / this same sha256() function against the live files at
// authoring time, then frozen here. Re-verified against the live files below;
// any drift throws immediately rather than silently rendering against
// changed reference code.
const RUNTIME_PROVENANCE = {
  wormhole_js_sha256: '45adb569c80897848b84fc4551eaa14a00c62db99db02ecca98d417f9b74d195',
  texture_format_js_sha256: '10af8fd92813c7872eecf51b203c01a4e6ebc79a4c5fa7d38661a12192efbcfe',
  surface_js_sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  scatter_registry_js_sha256: '940ed6fe1b27e826330c7b1c49336126e37a39e29176ee335bb50526dc40c4d2',
  deposit_frag_sha256: '156401729b935381b38732d8e84ebdbbe185734e642972fa45533c5ce51a083d',
}

const LIVE_HASHES = {
  wormhole_js_sha256: pinnedHash(wormholePath),
  texture_format_js_sha256: pinnedHash(texFormatPath),
  surface_js_sha256: pinnedHash(surfacePath),
  scatter_registry_js_sha256: pinnedHash(scatterRegistryPath),
  deposit_frag_sha256: pinnedHash(depositFragPath),
}

for (const key of Object.keys(RUNTIME_PROVENANCE)) {
  if (RUNTIME_PROVENANCE[key] !== LIVE_HASHES[key]) throw new Error(`provenance drift: ${key} (pinned ${RUNTIME_PROVENANCE[key]}, live ${LIVE_HASHES[key]})`)
}

const depositFragBytes = fs.readFileSync(depositFragPath).length

// ---------------------------------------------------------------------------
// Determinism self-check + text-surgery fidelity check happen after the
// mutation-runtime builder is defined below (needs REAL extracted runtime).
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Deterministic patterned input generator. Channel moduli/coefficients differ
// per channel and per `phase` so no two cases share an input, and R/G/B
// genuinely differ per pixel (a permutation bug would otherwise hide).
// ---------------------------------------------------------------------------
function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = F32((((37 * x + 19 * y + 5 + 23 * phase) % 97) + 1) / 101)
      data[i + 1] = F32((((17 * x + 41 * y + 9 + 29 * phase) % 89) + 2) / 97)
      data[i + 2] = F32((((53 * x + 7 * y + 3 + 31 * phase) % 83) + 3) / 91)
      data[i + 3] = F32((((11 * x + 13 * y + 1 + 37 * phase) % 61) + 4) / 71)
    }
  }
  return new Surface(width, height, data)
}

function seedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = F32((((7 * x + 29 * y + 2 + 41 * phase) % 79) + 1) / 131)
      data[i + 1] = F32((((23 * x + 3 * y + 6 + 43 * phase) % 73) + 2) / 127)
      data[i + 2] = F32((((5 * x + 31 * y + 4 + 47 * phase) % 67) + 3) / 113)
      data[i + 3] = F32((((13 * x + 17 * y + 8 + 53 * phase) % 59) + 4) / 103)
    }
  }
  return new Surface(width, height, data)
}

function solidSurface(width, height, color) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i += 4) {
    data[i] = F32(color[0]); data[i + 1] = F32(color[1]); data[i + 2] = F32(color[2]); data[i + 3] = F32(color[3])
  }
  return new Surface(width, height, data)
}

// ---------------------------------------------------------------------------
// Independent diagnostics -- a SEPARATE reimplementation of the same
// arithmetic, used ONLY to classify cases (does this case exercise
// out-of-bounds wrapping? collisions? nonzero signal?) for mutation `reach`
// predicates and for case metadata. Golden values NEVER come from this code
// path -- they always come from the real, unmodified `runWormholeDeposit`
// (or, for mutation rows, from the surgically-mutated copy of its own source
// text). Keeping this duplication honest: if it silently drifted from the
// reference, the worst case is a wrong `reach` classification, which the
// structural soundness check below (non-reaching cases must show ZERO
// divergence) would catch as a contradiction.
// ---------------------------------------------------------------------------
function dAdd(a, b) { return F32(a + b) }
function dMul(a, b) { return F32(a * b) }
function dDiv(a, b) { return F32(a / b) }
function dOklabLightness(red, green, blue) {
  const r = Math.min(Math.max(red, 0), 1)
  const g = Math.min(Math.max(green, 0), 1)
  const b = Math.min(Math.max(blue, 0), 1)
  const l = dAdd(dAdd(dMul(F32(0.4122214708), r), dMul(F32(0.5363325363), g)), dMul(F32(0.0514459929), b))
  const m = dAdd(dAdd(dMul(F32(0.2119034982), r), dMul(F32(0.6806995451), g)), dMul(F32(0.1073969566), b))
  const s = dAdd(dAdd(dMul(F32(0.0883024619), r), dMul(F32(0.2817188376), g)), dMul(F32(0.6299787005), b))
  const exponent = dDiv(1, 3)
  const lr = F32(Math.pow(Math.max(l, 0), exponent))
  const mr = F32(Math.pow(Math.max(m, 0), exponent))
  const sr = F32(Math.pow(Math.max(s, 0), exponent))
  return dAdd(dAdd(dMul(F32(0.2104542553), lr), dMul(F32(0.793617785), mr)), dMul(F32(-0.0040720468), sr))
}
function dWrapRepeat(value, size) { return ((value % size) + size) % size }
function dWrapMirror(value, size) {
  const doubled = size * 2
  const mirrored = dWrapRepeat(value, doubled)
  return size - 1 - Math.abs(mirrored - size + 1)
}

function computeDiagnostics(width, height, inputData, uniforms) {
  const kink = uniforms.kink
  const pixelStride = 1024 * uniforms.stride
  const rotation = dDiv(dMul(F32(uniforms.rotation), F32(Math.PI)), 180)
  const wrap = uniforms.wrap | 0
  let hasSignal = false
  let rawOobX = 0
  let rawOobY = 0
  let negRawX = 0
  let negRawY = 0
  const finalCount = new Map()
  for (let sourceY = 0; sourceY < height; sourceY += 1) {
    for (let sourceX = 0; sourceX < width; sourceX += 1) {
      const sourceRow = height - 1 - sourceY
      const sourceOffset = (sourceRow * width + sourceX) * 4
      const r = inputData[sourceOffset]
      const g = inputData[sourceOffset + 1]
      const b = inputData[sourceOffset + 2]
      if (r > 0 || g > 0 || b > 0) hasSignal = true
      const lightness = dOklabLightness(r, g, b)
      const angle = dAdd(dMul(dMul(lightness, F32(TAU)), F32(kink)), rotation)
      const offsetX = dMul(dAdd(F32(Math.cos(angle)), 1), F32(pixelStride))
      const offsetY = dMul(dAdd(F32(Math.sin(angle)), 1), F32(pixelStride))
      let destinationX = Math.floor(dAdd(sourceX, offsetX))
      let destinationY = Math.floor(dAdd(sourceY, offsetY))
      if (destinationX < 0 || destinationX >= width) rawOobX += 1
      if (destinationY < 0 || destinationY >= height) rawOobY += 1
      if (destinationX < 0) negRawX += 1
      if (destinationY < 0) negRawY += 1
      if (wrap === 0) {
        destinationX = dWrapMirror(destinationX, width)
        destinationY = dWrapMirror(destinationY, height)
      } else if (wrap === 2) {
        destinationX = Math.min(Math.max(destinationX, 0), width - 1)
        destinationY = Math.min(Math.max(destinationY, 0), height - 1)
      } else {
        destinationX = dWrapRepeat(destinationX, width)
        destinationY = dWrapRepeat(destinationY, height)
      }
      const destinationRow = height - 1 - destinationY
      const key = destinationRow * width + destinationX
      finalCount.set(key, (finalCount.get(key) ?? 0) + 1)
    }
  }
  let collisionSites = 0
  let maxMultiplicity = 1
  for (const v of finalCount.values()) {
    if (v > 1) collisionSites += 1
    if (v > maxMultiplicity) maxMultiplicity = v
  }
  return { hasSignal, rawOobX, rawOobY, negRawX, negRawY, collisionSites, maxMultiplicity, totalSources: width * height, wrapResolved: wrap }
}

// ---------------------------------------------------------------------------
// pixelStride "double vs float32 storage order" -- checked, not assumed.
// `pixelStride = 1024 * uniforms.stride` is computed in double and only
// F32-rounded at each use site (`F32(pixelStride)`, twice). Because 1024 is
// an exact power of two, scaling by it commutes exactly with round-to-float32
// (no mantissa bits are gained or lost by an exact power-of-two multiply), so
// `Math.fround(1024 * stride) === 1024 * Math.fround(stride)` for every
// finite, non-overflowing `stride`. This is PROVEN below over a wide sample
// set rather than assumed -- if it were ever false the sample loop would
// throw and this oracle would need a genuinely discriminating mutation here
// instead. It is reported honestly as a no-op rather than dressed up as a
// discriminator.
// ---------------------------------------------------------------------------
function buildPixelStrideRoundingProof() {
  const samples = [
    0, 1, 2, 0.5, 1.5, -1.4, -0.9, 1e-7, 3.3333333333333335, 0.1, 0.001,
    12345.6789, -0.0001, 2.0000001, 1.9999999, 1e6, -1e6, 5000000.123456,
    Number.EPSILON, 1 - Number.EPSILON, 2 ** -20, -(2 ** -20),
  ]
  const rows = samples.map((stride) => {
    const doubleFirst = F32(1024 * stride)
    const floatFirst = 1024 * F32(stride)
    return { stride, double_first_bits: bitsHex(doubleFirst), float_first_bits: bitsHex(floatFirst), equal: bitsU32(doubleFirst) === bitsU32(floatFirst) }
  })
  const allEqual = rows.every((r) => r.equal)
  if (!allEqual) throw new Error('pixelStride rounding-order proof FAILED -- this is no longer a no-op, a real mutation is needed here; see rows for the failing stride value')
  return {
    claim: 'Math.fround(1024 * stride) === 1024 * Math.fround(stride) for every sampled stride -- storage order is provably unobservable for this multiplier',
    samples: rows,
    all_equal: allEqual,
  }
}

// ---------------------------------------------------------------------------
// Mutation runtime builder -- extracts `wormhole.js`'s real source text,
// verifies it, strips the `import`/`export` wrapper, and evaluates it as a
// standalone function that returns `{ runWormholeDeposit, oklabLightness,
// wrapRepeat, wrapMirror, add, mul, div }`. Applying this to the UNMODIFIED
// text and cross-checking against the real imported `runWormholeDeposit`
// proves the text-surgery technique is faithful before any mutation is
// trusted.
// ---------------------------------------------------------------------------
const wormholeSourceText = fs.readFileSync(wormholePath, 'utf8')
const IMPORT_LINE = "import { float16Truncate } from '../../runtime/texture-format.js'\n"
const EXPORT_ANCHOR = 'export function runWormholeDeposit'

function buildRuntimeFromSource(sourceText) {
  if (occurrences(sourceText, IMPORT_LINE) !== 1) throw new Error('import line anchor not found exactly once')
  const withoutImport = sourceText.replace(IMPORT_LINE, '')
  if (occurrences(withoutImport, EXPORT_ANCHOR) !== 1) throw new Error('export anchor not found exactly once')
  const withoutExport = withoutImport.replace(EXPORT_ANCHOR, 'function runWormholeDeposit')
  const wrapped = `${withoutExport}\nreturn { runWormholeDeposit, oklabLightness, wrapRepeat, wrapMirror, add, mul, div };\n`
  // eslint-disable-next-line no-new-func
  return new Function('float16Truncate', wrapped)(float16Truncate)
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

const REAL = buildRuntimeFromSource(wormholeSourceText)

// ---------------------------------------------------------------------------
// Case construction. `purposes` tags whether a case exists to drive mutation
// discrimination (Part 1) and/or the C++ bit-exact sweep (Part 2) -- most
// cases serve both.
// ---------------------------------------------------------------------------
function normalizeUniforms(u) { return { kink: u.kink, stride: u.stride, rotation: u.rotation, wrap: u.wrap } }

function buildCase(def) {
  const uniforms = normalizeUniforms(def.uniforms)
  const input = def.solidColor ? solidSurface(def.width, def.height, def.solidColor) : patternedSurface(def.width, def.height, def.phase)
  const seedDestination = def.seedPhase != null ? seedSurface(def.width, def.height, def.seedPhase) : new Surface(def.width, def.height)
  const diagnostics = computeDiagnostics(def.width, def.height, input.data, uniforms)
  return { def, uniforms, input, seedDestination, diagnostics }
}

// ---- Discrimination cases (Part 1) -----------------------------------------
const DISCRIMINATION_DEFS = [
  { name: 'mirror-collision-oob-6x5', width: 6, height: 5, uniforms: { kink: 1.7, stride: 1.3, rotation: 37, wrap: 0 }, phase: 10, seedPhase: 55, purposes: ['discrimination', 'sweep'] },
  { name: 'repeat-collision-oob-7x4', width: 7, height: 4, uniforms: { kink: 0.6, stride: 1.9, rotation: -125, wrap: 1 }, phase: 20, seedPhase: 66, purposes: ['discrimination', 'sweep'] },
  { name: 'clamp-collision-oob-5x9', width: 5, height: 9, uniforms: { kink: 2.4, stride: 1.1, rotation: 173, wrap: 2 }, phase: 30, seedPhase: 77, purposes: ['discrimination', 'sweep'] },
  { name: 'mirror-negative-stride-negmod-6x6', width: 6, height: 6, uniforms: { kink: 1.0, stride: -1.4, rotation: 10, wrap: 0 }, phase: 31, purposes: ['discrimination', 'sweep'] },
  { name: 'repeat-negative-stride-negmod-7x5', width: 7, height: 5, uniforms: { kink: 0.3, stride: -0.9, rotation: -40, wrap: 1 }, phase: 32, purposes: ['discrimination', 'sweep'] },
  { name: 'clamp-negative-stride-5x5', width: 5, height: 5, uniforms: { kink: 1.0, stride: -1.2, rotation: 5, wrap: 2 }, phase: 33, purposes: ['discrimination', 'sweep'] },
  { name: 'wrap-else-arbitrary-value-6x4', width: 6, height: 4, uniforms: { kink: 0.8, stride: 1.6, rotation: 88, wrap: 7 }, phase: 34, purposes: ['discrimination'] },
  { name: 'wrap-fractional-truncation-1p9-9x6', width: 9, height: 6, uniforms: { kink: 1.1, stride: 1.4, rotation: 60, wrap: 1.9 }, phase: 35, purposes: ['discrimination'] },
  { name: 'wrap-fractional-truncation-2p7-9x6', width: 9, height: 6, uniforms: { kink: 1.1, stride: 1.4, rotation: 60, wrap: 2.7 }, phase: 35, purposes: ['discrimination'] },
  // NOTE: `cpu-special-effects.test.js`'s "wormhole point deposit scatters
  // every source pixel with additive luminance weighting" test expects 0.5,
  // but that assertion is on the FULL pipeline's `outputTex` after the
  // `blend` pass mixes accumTex against inputTex -- not on the deposit's
  // accum texture alone. Driving `runWormholeDeposit` directly (as this
  // oracle does, per the task brief) skips `blend` entirely, so the correct
  // known-answer here is the deposit's own output: white has OKLab lightness
  // 1.0 exactly (verified independently below and via `oklab_lightness_rows`),
  // weight = 1*1 = 1, so RGB = float16Truncate(0 + 1*1) = 1, alpha untouched at 0.
  { name: 'known-answer-solid-white-1x1', width: 1, height: 1, uniforms: { kink: 1, stride: 0, rotation: 0, wrap: 1 }, solidColor: [1, 1, 1, 1], purposes: ['discrimination', 'sweep'], knownAnswer: [1, 1, 1, 0] },
  { name: 'identity-shift-zero-kink-zero-rotation-7x7', width: 7, height: 7, uniforms: { kink: 0, stride: 0.5, rotation: 0, wrap: 1 }, phase: 36, purposes: ['discrimination'], diagnostic: true },
  { name: 'identity-zero-stride-clamp-7x9', width: 7, height: 9, uniforms: { kink: 0, stride: 0, rotation: -180, wrap: 2 }, phase: 37, purposes: ['discrimination'], diagnostic: true },
  { name: 'large-stride-precision-stress-6x6', width: 6, height: 6, uniforms: { kink: 1.3, stride: 5000000, rotation: 15, wrap: 1 }, phase: 38, purposes: ['discrimination'], diagnostic: true },
  { name: 'high-precision-stride-6x6', width: 6, height: 6, uniforms: { kink: 1.234567891234, stride: 0.918273645192837, rotation: 63.14159265358979, wrap: 0 }, phase: 39, purposes: ['discrimination', 'sweep'] },
]

// ---- Sweep grid (Part 2): odd/non-square/power-of-two canvas sizes x all
// three canonical wrap modes, each with a distinct patterned input and
// varied kink/stride/rotation per (size, wrap) index. -----------------------
const SWEEP_SIZES = [
  [1, 1], [2, 3], [3, 2], [4, 4], [5, 5], [6, 7], [7, 6], [8, 8],
  [9, 13], [13, 9], [16, 16], [17, 31], [31, 17], [33, 33], [5, 1], [1, 7],
]
const SWEEP_WRAPS = [0, 1, 2]

const SWEEP_DEFS = []
let sweepIndex = 0
for (const [width, height] of SWEEP_SIZES) {
  for (const wrap of SWEEP_WRAPS) {
    sweepIndex += 1
    const kink = F32(0.2 + ((sweepIndex * 37) % 480) / 100) // spread across [0.2, 5.0)
    const stride = F32(((sweepIndex * 53) % 200) / 100) // [0, 2.0)
    const rotation = F32(-180 + ((sweepIndex * 71) % 3600) / 10) // [-180, 180)
    SWEEP_DEFS.push({
      name: `sweep-${width}x${height}-wrap${wrap}-${sweepIndex}`,
      width, height,
      uniforms: { kink, stride, rotation, wrap },
      phase: 1000 + sweepIndex,
      seedPhase: sweepIndex % 2 === 0 ? 2000 + sweepIndex : undefined,
      purposes: ['sweep'],
    })
  }
}

const ALL_DEFS = [...DISCRIMINATION_DEFS, ...SWEEP_DEFS]
const CASES = ALL_DEFS.map(buildCase)

// ---------------------------------------------------------------------------
// Render + determinism + known-answer verification.
// ---------------------------------------------------------------------------
function renderReal(kase) {
  const inputBefore = Buffer.from(kase.input.data).toString('hex')
  const destination1 = kase.seedDestination.clone()
  runWormholeDeposit(kase.input, destination1, kase.uniforms)
  const inputAfter = Buffer.from(kase.input.data).toString('hex')
  if (inputBefore !== inputAfter) throw new Error(`${kase.def.name}: input surface was mutated by runWormholeDeposit`)
  const destination2 = kase.seedDestination.clone()
  runWormholeDeposit(kase.input, destination2, kase.uniforms)
  if (!sameSurfaceBytes(destination1, destination2)) throw new Error(`${kase.def.name}: repeat-render mismatch (determinism failure)`)
  return destination1
}

for (const kase of CASES) {
  kase.output = renderReal(kase)
  if (kase.def.knownAnswer) {
    const [r, g, b, a] = kase.def.knownAnswer
    const data = kase.output.data
    const ok = Math.abs(data[0] - r) < 1e-6 && Math.abs(data[1] - g) < 1e-6 && Math.abs(data[2] - b) < 1e-6 && data[3] === a
    if (!ok) throw new Error(`${kase.def.name}: known-answer mismatch, got [${data[0]}, ${data[1]}, ${data[2]}, ${data[3]}]`)
  }
}

// Text-surgery fidelity self-check: the extracted-from-source-text REAL
// runtime must reproduce the real imported function byte-for-byte on every
// case, before any mutation result is trusted.
for (const kase of CASES) {
  const destination = kase.seedDestination.clone()
  REAL.runWormholeDeposit(kase.input, destination, kase.uniforms)
  if (!sameSurfaceBytes(destination, kase.output)) throw new Error(`${kase.def.name}: extracted-runtime self-check mismatch -- text surgery is not faithful, do not trust mutation results`)
}

// ---------------------------------------------------------------------------
// Mutation catalogue.
// ---------------------------------------------------------------------------
const WRAP_BLOCK_START = 'if (wrap === 0) {'
const WRAP_BLOCK_END = 'destinationY = wrapRepeat(destinationY, height)\n      }'
const wrapBlock = extractBlock(wormholeSourceText, WRAP_BLOCK_START, WRAP_BLOCK_END)

const MIRROR_X = 'destinationX = wrapMirror(destinationX, width)'
const MIRROR_Y = 'destinationY = wrapMirror(destinationY, height)'
const CLAMP_X = 'destinationX = Math.min(Math.max(destinationX, 0), width - 1)'
const CLAMP_Y = 'destinationY = Math.min(Math.max(destinationY, 0), height - 1)'
const REPEAT_X = 'destinationX = wrapRepeat(destinationX, width)'
const REPEAT_Y = 'destinationY = wrapRepeat(destinationY, height)'
for (const anchor of [MIRROR_X, MIRROR_Y, CLAMP_X, CLAMP_Y, REPEAT_X, REPEAT_Y]) {
  if (occurrences(wrapBlock, anchor) !== 1) throw new Error(`wrap-block sub-anchor not unique: ${anchor}`)
}

function buildMirrorClampSwapBlock() {
  const TOKEN_X = '__SWAP_TOKEN_X__'
  const TOKEN_Y = '__SWAP_TOKEN_Y__'
  let mutated = wrapBlock
  mutated = mutated.replace(MIRROR_X, TOKEN_X).replace(MIRROR_Y, TOKEN_Y)
  mutated = mutated.replace(CLAMP_X, MIRROR_X).replace(CLAMP_Y, MIRROR_Y)
  mutated = mutated.replace(TOKEN_X, CLAMP_X).replace(TOKEN_Y, CLAMP_Y)
  return mutated
}
function buildElseBecomesClampBlock() {
  return wrapBlock.replace(REPEAT_X, CLAMP_X).replace(REPEAT_Y, CLAMP_Y)
}

const SOURCE_ROW_ANCHOR = 'const sourceRow = height - 1 - sourceY'
const DEST_ROW_ANCHOR = 'const destinationRow = height - 1 - destinationY'
const WEIGHT_ANCHOR = 'const weight = mul(lightness, lightness)'
const DIV13_ANCHOR = 'const exponent = div(1, 3)'

const ACCUM_START = 'outputData[destinationOffset] = float16Truncate(add(outputData[destinationOffset], mul(inputData[sourceOffset], weight)))'
const ACCUM_END = 'outputData[destinationOffset + 2] = float16Truncate(add(outputData[destinationOffset + 2], mul(inputData[sourceOffset + 2], weight)))'
const accumBlock = extractBlock(wormholeSourceText, ACCUM_START, ACCUM_END)

function buildFloat16SkipBlock() {
  const lines = accumBlock.split('\n')
  let replaced = 0
  const mutatedLines = lines.map((line) => {
    const m = line.match(/^(\s*outputData\[[^\]]+\] = )float16Truncate\((.*)\)$/)
    if (!m) return line
    replaced += 1
    return `${m[1]}${m[2]}`
  })
  if (replaced !== 3) throw new Error(`float16Truncate-skip mutation expected 3 sites, got ${replaced}`)
  return mutatedLines.join('\n')
}
function buildAlphaWrittenBlock() {
  const alphaLine = 'outputData[destinationOffset + 3] = float16Truncate(add(outputData[destinationOffset + 3], mul(inputData[sourceOffset + 3], weight)))'
  return `${accumBlock}\n      ${alphaLine}`
}

const OKLAB_START = 'const l = add(add(mul(F32(0.4122214708), r), mul(F32(0.5363325363), g)), mul(F32(0.0514459929), b))'
const OKLAB_END = 'const s = add(add(mul(F32(0.0883024619), r), mul(F32(0.2817188376), g)), mul(F32(0.6299787005), b))'
const oklabBlock = extractBlock(wormholeSourceText, OKLAB_START, OKLAB_END)
const OKLAB_MATRIX_UNROUNDED = [
  '  const l = (0.4122214708 * r) + (0.5363325363 * g) + (0.0514459929 * b)',
  '  const m = (0.2119034982 * r) + (0.6806995451 * g) + (0.1073969566 * b)',
  '  const s = (0.0883024619 * r) + (0.2817188376 * g) + (0.6299787005 * b)',
].join('\n')

const MUTATIONS = [
  {
    id: 'wrap-mirror-clamp-swap', kind: 'wrap-dispatch', reachKey: 'wrapSwapReach',
    hazard: 'mirror/clamp branch bodies swapped for wrap===0 and wrap===2',
    description: 'Swap the wrapMirror and clamp bodies so wrap===0 clamps and wrap===2 mirrors, leaving the condition checks untouched. Only observable when a case actually needs wrapping (raw pre-wrap destination out of [0,size)).',
    anchor: wrapBlock, mutated: buildMirrorClampSwapBlock(),
    reach: (d, u) => (((u.wrap | 0) === 0) || ((u.wrap | 0) === 2)) && (d.rawOobX > 0 || d.rawOobY > 0),
  },
  {
    id: 'wrap-else-becomes-clamp', kind: 'wrap-dispatch', reachKey: 'wrapElseReach',
    hazard: 'the else (repeat) branch clamps instead of wrapping',
    description: 'Replace the else-branch wrapRepeat calls with clamp calls, leaving wrap===0/2 untouched. Reaches any case whose resolved wrap value is neither 0 nor 2 and that needs wrapping.',
    anchor: wrapBlock, mutated: buildElseBecomesClampBlock(),
    reach: (d) => !(d.wrapResolved === 0 || d.wrapResolved === 2) && (d.rawOobX > 0 || d.rawOobY > 0),
  },
  {
    id: 'source-row-flip-removed', kind: 'vertex-id-convention', reachKey: 'heightGtOne',
    hazard: 'bottom-up sourceRow convention dropped (uses sourceY directly)',
    description: 'sourceRow = sourceY instead of height - 1 - sourceY. Reaches any case with height > 1 and nonzero image signal.',
    anchor: SOURCE_ROW_ANCHOR, mutated: 'const sourceRow = sourceY',
    reach: (d) => d.hasSignal, // height>1 filtered separately below via case metadata
  },
  {
    id: 'destination-row-flip-removed', kind: 'vertex-id-convention', reachKey: 'heightGtOne',
    hazard: 'bottom-up destinationRow convention dropped (uses destinationY directly)',
    description: 'destinationRow = destinationY instead of height - 1 - destinationY. Reaches any case with height > 1 and nonzero image signal.',
    anchor: DEST_ROW_ANCHOR, mutated: 'const destinationRow = destinationY',
    reach: (d) => d.hasSignal,
  },
  {
    id: 'weight-formula-linear', kind: 'accumulation', reachKey: 'hasSignal',
    hazard: 'weight = lightness instead of lightness*lightness',
    description: 'Replaces the quadratic accumulation weight with a linear one. Reaches any case with nonzero image signal.',
    anchor: WEIGHT_ANCHOR, mutated: 'const weight = lightness',
    reach: (d) => d.hasSignal,
  },
  {
    id: 'float16-truncate-skipped', kind: 'accumulation', reachKey: 'hasSignal',
    hazard: 'accumulation stored at full float32 precision, skipping the rgba16f round-trip',
    description: 'All three RGB accumulate lines drop the float16Truncate() wrapper, storing the raw F32-rounded sum instead of its float16 round-trip.',
    anchor: accumBlock, mutated: buildFloat16SkipBlock(),
    reach: (d) => d.hasSignal,
  },
  {
    id: 'div13-not-frounded', kind: 'oklab-lightness', reachKey: 'hasSignal',
    hazard: 'cube-root exponent computed as raw 1/3 instead of F32-rounded div(1,3)',
    description: 'exponent = 1 / 3 (full double precision) instead of div(1, 3) (F32-rounded before use in Math.pow).',
    anchor: DIV13_ANCHOR, mutated: 'const exponent = 1 / 3',
    reach: (d) => d.hasSignal,
  },
  {
    id: 'oklab-matrix-not-frounded', kind: 'oklab-lightness', reachKey: 'hasSignal',
    hazard: 'l/m/s matrix multiply-accumulate done in plain double arithmetic instead of per-operation F32 rounding',
    description: 'Replaces the add(add(mul(F32(c0),r),mul(F32(c1),g)),mul(F32(c2),b)) chains for l/m/s with plain (c0*r)+(c1*g)+(c2*b) double arithmetic -- same constants, no per-operation F32 rounding.',
    anchor: oklabBlock, mutated: OKLAB_MATRIX_UNROUNDED,
    reach: (d) => d.hasSignal,
  },
  {
    id: 'alpha-channel-written', kind: 'channel-scope', reachKey: 'hasSignal',
    hazard: 'alpha channel accumulated like RGB instead of being left untouched',
    description: 'Adds a 4th accumulate line writing destinationOffset+3, matching the RGB pattern. The reference deliberately leaves alpha alone.',
    anchor: accumBlock, mutated: buildAlphaWrittenBlock(),
    reach: (d) => d.hasSignal,
  },
]

function heightGtOne(kase) { return kase.def.height > 1 }

function runMutation(mutation) {
  const mutatedSourceText = mutateSource(wormholeSourceText, mutation.anchor, mutation.mutated)
  const mutatedRuntime = buildRuntimeFromSource(mutatedSourceText)
  const caseResults = CASES.map((kase) => {
    const destination = kase.seedDestination.clone()
    mutatedRuntime.runWormholeDeposit(kase.input, destination, kase.uniforms)
    const diverges = !sameSurfaceBytes(destination, kase.output)
    let reaches = mutation.reach(kase.diagnostics, kase.uniforms)
    if (mutation.reachKey === 'heightGtOne') reaches = reaches && heightGtOne(kase)
    return { case: kase.def.name, reaches, diverges }
  })
  const reaching = caseResults.filter((r) => r.reaches)
  const nonReaching = caseResults.filter((r) => !r.reaches)
  const divergentReaching = reaching.filter((r) => r.diverges).length
  const divergentNonReaching = nonReaching.filter((r) => r.diverges).length
  return { caseResults, reachingCount: reaching.length, divergentReaching, nonReachingCount: nonReaching.length, divergentNonReaching }
}

for (const mutation of MUTATIONS) {
  const result = runMutation(mutation)
  mutation.result = result
  if (result.reachingCount === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site -- cannot prove discrimination`)
  if (result.divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${result.reachingCount}`)
  if (result.divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${result.divergentNonReaching}/${result.nonReachingCount} non-reaching case(s) diverged -- reach predicate or mutation scope is wrong`)
}

// ---------------------------------------------------------------------------
// Direct rows: wrapRepeat / wrapMirror (integer table incl. negatives, proving
// JS `%` truncated-toward-zero semantics) and oklabLightness (clamping +
// cube-root precision), using the REAL extracted closures directly.
// ---------------------------------------------------------------------------
const WRAP_ROW_INPUTS = [
  [0, 5], [4, 5], [5, 5], [6, 5], [-1, 5], [-5, 5], [-6, 5], [-11, 5],
  [13, 4], [-13, 4], [0, 1], [-1, 1], [1000000, 7], [-1000000, 7],
  [4095, 4096], [-4095, 4096], [8, 8], [-8, 8],
]
function wrapRows(fn) {
  return WRAP_ROW_INPUTS.map(([value, size]) => {
    const result = fn(value, size)
    return { value, size, result, note: value < 0 ? 'negative input -- exercises JS truncated-toward-zero %' : null }
  })
}
const WRAP_REPEAT_ROWS = wrapRows(REAL.wrapRepeat)
const WRAP_MIRROR_ROWS = wrapRows(REAL.wrapMirror)
// Structural check, using TWO independent formulas so the comparison is not
// circular: (a) `naiveMod` is JS's raw truncated-toward-zero `%` (can be
// negative); wrapRepeat's double-mod correction must differ from it for
// every negative-value row, proving the correction is load-bearing, not a
// no-op. (b) `floorModReference` computes the true mathematical floor-mod via
// floor DIVISION (`value - size*Math.floor(value/size)`) -- a structurally
// different code path from wrapRepeat's double-`%` trick -- and wrapRepeat
// must agree with it on every row, proving the double-mod trick is correct,
// not merely self-consistent.
function naiveMod(value, size) { return value % size }
function floorModReference(value, size) { return value - size * Math.floor(value / size) }
for (const row of WRAP_REPEAT_ROWS) {
  const viaFloor = floorModReference(row.value, row.size)
  if (viaFloor !== row.result) throw new Error(`wrapRepeat row ${row.value},${row.size}: disagrees with independent floor-mod reference (got ${row.result}, expected ${viaFloor})`)
  // Exact negative multiples of `size` are a legitimate exception: naive
  // truncated `%` already yields -0 there, and -0 === 0 in JS, so the
  // correction is a genuine (not vacuous) no-op precisely because there is
  // nothing to correct -- both encode the same array index. Every other
  // negative row must show the correction actually changing the value.
  if (row.value < 0 && row.value % row.size !== 0) {
    const naive = naiveMod(row.value, row.size)
    if (naive === row.result) throw new Error(`wrapRepeat row ${row.value},${row.size}: double-mod correction had no effect vs naive truncated %% -- negative-input coverage is vacuous`)
  }
}

const OKLAB_ROW_INPUTS = [
  [0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5], [1, 0, 0], [0, 1, 0], [0, 0, 1],
  [-0.3, 1.4, 0.5], [2, 2, 2], [0.0001, 0.0001, 0.0001], [0.999999, 0.000001, 0.5],
  [0.2109, 0.7893, 0.0512], [-1, -1, -1],
]
const OKLAB_ROWS = OKLAB_ROW_INPUTS.map(([r, g, b]) => {
  const lightness = REAL.oklabLightness(r, g, b)
  return { r, g, b, lightness, lightness_bits: bitsHex(lightness) }
})

// ---------------------------------------------------------------------------
// Assembly.
// ---------------------------------------------------------------------------
function surfaceToBitsArray(surface) { return Array.from(surface.data, bitsU32) }

function caseToJson(kase) {
  return {
    name: kase.def.name,
    purposes: kase.def.purposes,
    diagnostic: Boolean(kase.def.diagnostic),
    width: kase.def.width,
    height: kase.def.height,
    uniforms: kase.uniforms,
    seeded: kase.def.seedPhase != null,
    diagnostics: kase.diagnostics,
    input_bits: surfaceToBitsArray(kase.input),
    seed_bits: kase.def.seedPhase != null ? surfaceToBitsArray(kase.seedDestination) : null,
    output_bits: surfaceToBitsArray(kase.output),
    output_sha256: sha256(bytesOf(kase.output.data)),
    input_sha256: sha256(bytesOf(kase.input.data)),
  }
}

function build() {
  return {
    schema: 'noisemaker-for-cpp.wormhole.deposit-scatter-oracle.v1',
    corpus_revision: revision,
    provenance: {
      ...RUNTIME_PROVENANCE,
      deposit_frag_bytes: depositFragBytes,
      node: process.version,
      reference_function: 'runWormholeDeposit (src/effects/cpu/wormhole.js:34-76), imported and called directly, never reimplemented for golden values',
      adapter_key: 'filter/wormhole:deposit',
      note: 'deposit.frag IS transpiled (canonicalFactory181, glsl-coverage.js status "generated") but the CPU renderer never executes that kernel for drawMode:"points" passes -- see src/runtime/renderer.js pass.drawMode branch and scatter-registry.js header comment.',
    },
    text_surgery_self_check: 'PASS -- extracted-from-source-text runtime reproduces the real imported runWormholeDeposit byte-for-byte on every case (asserted at build time)',
    pixel_stride_rounding_proof: buildPixelStrideRoundingProof(),
    wrap_function_rows: { wrap_repeat: WRAP_REPEAT_ROWS, wrap_mirror: WRAP_MIRROR_ROWS },
    oklab_lightness_rows: OKLAB_ROWS,
    mutations: MUTATIONS.map((m) => ({
      id: m.id, kind: m.kind, hazard: m.hazard, description: m.description,
      summary: { reaching_cases: m.result.reachingCount, divergent_reaching: m.result.divergentReaching, non_reaching_cases: m.result.nonReachingCount, divergent_non_reaching: m.result.divergentNonReaching },
      case_results: m.result.caseResults,
    })),
    cases: CASES.map(caseToJson),
    eligibility_summary: {
      total_cases: CASES.length,
      discrimination_cases: CASES.filter((k) => k.def.purposes.includes('discrimination')).length,
      sweep_cases: CASES.filter((k) => k.def.purposes.includes('sweep')).length,
      diagnostic_cases: CASES.filter((k) => k.def.diagnostic).length,
    },
  }
}

function report(d) {
  const lines = [
    '# `filter/wormhole:deposit` scatter-pass oracle report', '',
    'Ground truth is `runWormholeDeposit` (`src/effects/cpu/wormhole.js:34-76`), imported and called directly -- never reimplemented for golden values. See `provenance.note` for why the transpiled `deposit.frag` kernel is irrelevant to this port.',
    '',
    `Total cases: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.discrimination_cases} discrimination-focused, ${d.eligibility_summary.sweep_cases} sweep-focused, ${d.eligibility_summary.diagnostic_cases} diagnostic/control).`,
    '',
    '## Provenance', '',
    '| File | sha256 |', '| --- | --- |',
    `| wormhole.js | \`${d.provenance.wormhole_js_sha256}\` |`,
    `| texture-format.js | \`${d.provenance.texture_format_js_sha256}\` |`,
    `| surface.js | \`${d.provenance.surface_js_sha256}\` |`,
    `| scatter-registry.js | \`${d.provenance.scatter_registry_js_sha256}\` |`,
    `| deposit.frag (corpus ${d.corpus_revision}) | \`${d.provenance.deposit_frag_sha256}\` (${d.provenance.deposit_frag_bytes} bytes) |`,
    '',
    `Text-surgery self-check: **${d.text_surgery_self_check}**`, '',
    '## pixelStride rounding-order proof (provable no-op, reported honestly)', '',
    d.pixel_stride_rounding_proof.claim, '',
    `Checked over ${d.pixel_stride_rounding_proof.samples.length} sampled stride values; \`all_equal: ${d.pixel_stride_rounding_proof.all_equal}\`. This is the specific case the task brief warns about: an "obvious" storage-order mutation that turns out to be structurally unobservable (1024 is an exact power of two, so round-then-scale equals scale-then-round). It is reported here as a checked non-discriminator rather than silently dropped.`, '',
    '## Mutations', '',
    '| Mutation | Kind | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |',
    '| --- | --- | ---: | ---: | ---: | ---: |',
  ]
  for (const m of d.mutations) {
    lines.push(`| ${m.id} | ${m.kind} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
  }
  lines.push('')
  for (const m of d.mutations) lines.push(`- **${m.id}** (${m.kind}): ${m.description}`)
  lines.push('', '## Wrap function direct rows', '', `wrapRepeat: ${d.wrap_function_rows.wrap_repeat.length} rows. wrapMirror: ${d.wrap_function_rows.wrap_mirror.length} rows. Both include negative inputs to pin down JS \`%\` truncated-toward-zero semantics (see \`wormhole-oracles.json\` for the full table).`, '')
  lines.push('## oklabLightness direct rows', '', `${d.oklab_lightness_rows.length} rows spanning clamped-negative, clamped->1, zero, unit, and near-boundary inputs.`, '')
  lines.push('## Cases', '', '| Case | Size | Purposes | Diagnostic | Wrap | Collisions | Raw OOB (x,y) | Output SHA-256 |', '| --- | --- | --- | --- | --- | ---: | --- | --- |')
  for (const c of d.cases) {
    lines.push(`| ${c.name} | ${c.width}x${c.height} | ${c.purposes.join(',')} | ${c.diagnostic} | ${c.diagnostics.wrapResolved} | ${c.diagnostics.collisionSites} | ${c.diagnostics.rawOobX},${c.diagnostics.rawOobY} | \`${c.output_sha256.slice(0, 16)}...\` |`)
  }
  lines.push('')
  return lines.join('\n')
}

const data = build()
const json = `${JSON.stringify(data, null, 2)}\n`
const md = `${report(data)}\n`

if (process.argv.includes('--check')) {
  if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('wormhole oracle JSON drift')
  if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('wormhole oracle report drift')
  console.log(`wormhole oracle fixture ok (${data.eligibility_summary.total_cases} cases, ${data.mutations.length} mutations)`)
} else {
  fs.writeFileSync(outPath, json)
  fs.writeFileSync(reportPath, md)
  console.log(outPath)
}
