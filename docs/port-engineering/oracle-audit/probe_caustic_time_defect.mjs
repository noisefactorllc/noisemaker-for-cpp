import crypto from 'node:crypto'
import { canonicalKernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
const f = Math.fround

const key = 'classicNoisedeck/caustic:caustic'
const factory = canonicalKernelFactories[key]
if (!factory) throw new Error('factory missing for ' + key)

// Exact eligible-case uniforms overrides copied verbatim from
// docs/port-engineering/future-precompute/task31/caustic_oracle_generator.mjs
// lines 208-209 (DEFAULT_UNIFORMS, fullUniforms) and lines 300-305 (eligibleRenderDefs),
// defines = {NOISE_TYPE:10} (the authorized map). The generator's actual render()
// call uses fullUniforms(def.uniforms, 10) = {...DEFAULT_UNIFORMS, ...def.uniforms,
// NOISE_TYPE: 10} -- reproduced exactly here, not just the case-level override object.
const DEFAULT_UNIFORMS = { NOISE_TYPE: 10, time: 0, seed: 44, wrap: true, noiseScale: 85, speed: 25, hueRotation: 180, hueRange: 25, intensity: 0 }
function fullUniforms(overrides, noiseType = 10) { return { ...DEFAULT_UNIFORMS, ...overrides, NOISE_TYPE: noiseType } }

const rawCases = [
  { name: 'simplex-default-seed44', width: 6, height: 5, uniforms: { seed: 44, wrap: true, time: 0 } },
  { name: 'simplex-seed-zero-nowrap', width: 7, height: 4, uniforms: { seed: 0, wrap: false, time: 3.5 } },
  { name: 'simplex-large-seed-tiled', width: 5, height: 7, uniforms: { seed: 99, wrap: true, time: 12 }, tileOffset: [3, 2], fullResolution: [13, 11] },
  { name: 'simplex-negative-intensity-full-hue', width: 8, height: 3, uniforms: { seed: 17, hueRotation: 0, hueRange: 100, intensity: -80, speed: 100, time: 1.25 } },
  { name: 'simplex-min-scale-zero-speed', width: 4, height: 4, uniforms: { seed: 1, noiseScale: 1, speed: 0, time: 0 } },
  { name: 'simplex-max-scale-large-canvas', width: 10, height: 6, uniforms: { seed: 71, noiseScale: 200, speed: 63, hueRange: 5, time: 40 } },
]
const cases = rawCases.map((c) => ({ ...c, uniforms: fullUniforms(c.uniforms, 10) }))

function renderBroken({ width, height, uniforms, tileOffset, fullResolution }) {
  // Exactly mirrors caustic_oracle_generator.mjs's current render() (line 269-278):
  // uniforms (including `time`) passed straight through, no top-level `time`.
  const kernel = bindCanonicalKernel(factory, {
    width, height, uniforms, textures: {},
    tileOffset: new Float32Array(tileOffset ?? [0, 0]),
    fullResolution: new Float32Array(fullResolution ?? [width, height]),
  })
  const output = new Surface(width, height)
  runPass({ kernel, destination: output })
  return output
}

function renderCorrected({ width, height, uniforms, tileOffset, fullResolution }) {
  const { time: caseTime, ...restUniforms } = uniforms
  const kernel = bindCanonicalKernel(factory, {
    width, height, uniforms: restUniforms, textures: {},
    time: caseTime ?? 0,
    tileOffset: new Float32Array(tileOffset ?? [0, 0]),
    fullResolution: new Float32Array(fullResolution ?? [width, height]),
  })
  const output = new Surface(width, height)
  runPass({ kernel, destination: output })
  return output
}

const frozen = JSON.parse(
  await (await import('node:fs/promises')).readFile(
    'docs/port-engineering/future-precompute/task31/caustic-oracles.json', 'utf8'
  )
)
const frozenByName = Object.fromEntries(frozen.eligible_render_cases.map((c) => [c.name, c.output.f32_sha256]))

console.log('case | intended time | broken sha256(8) | corrected sha256(8) | frozen sha256(8) | frozen==broken | frozen==corrected | broken==corrected (harmless iff true)')
for (const c of cases) {
  const broken = renderBroken(c)
  const corrected = renderCorrected(c)
  const brokenHash = sha256(bytes(broken.data))
  const correctedHash = sha256(bytes(corrected.data))
  const frozenHash = frozenByName[c.name]
  console.log([
    c.name,
    c.uniforms.time,
    brokenHash.slice(0, 10),
    correctedHash.slice(0, 10),
    (frozenHash || 'MISSING').slice(0, 10),
    frozenHash === brokenHash,
    frozenHash === correctedHash,
    brokenHash === correctedHash,
  ].join(' | '))
}
