// Re-derivation script for `typed_math_slice_sixteen_external_oracles_are_repeatable`
// (tests/test_typed_slice.cpp), part of the 0ed489ec46842bffba33ee2ec65a218b6dda51f5
// resync (CPU authority 61aa869). Reproduces the exact fixture contract recorded in
// docs/port-engineering/task-9-report.md ("Oracle provenance and inputs"):
//
//   - Surface.fromRgba8 inputs, bytes = [(31x+17y+13t)%256, (11x+47y+29t)%256,
//     (67x+19y+7t)%256, (255-23x-37y-5t)&255]: input 5x3 t=1, blur 3x5 t=11,
//     color 7x2 t=23, edge 4x6 t=37, simplified 6x4 t=41, text 2x7 t=53.
//   - Output 7x5, tileOffset (3,-2), fullResolution (17,13), time .125, seed 7.
//   - Per-key uniforms/textures as in tests/test_typed_slice.cpp
//     populate_task9_bindings().
//
// Prints, per key: SHA-256 of little-endian float32 bytes, SHA-256 of RGBA8
// bytes, and the first 12 raw float32 bit-pattern probes -- the exact triple
// frozen in the native test's `fixtures` table.
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task9_oracle_regenerator.mjs

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

function resolveCpuRoot() {
  const candidates = [process.env.NOISEMAKER_CPU_ROOT, process.env.NOISEMAKER_FOR_CPU]
  for (const candidate of candidates) {
    if (!candidate) continue
    const root = path.resolve(candidate)
    if (fs.existsSync(path.join(root, 'src/effects/catalog.js'))) return root
  }
  throw new Error('JS authority not found: set NOISEMAKER_CPU_ROOT (or NOISEMAKER_FOR_CPU) to a noisemaker-for-cpu checkout')
}
const cpuRoot = resolveCpuRoot()
const authority = (relative) => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const { canonicalKernelFactories } = await authority('src/effects/catalog.js')
const { bindCanonicalKernel } = await authority('src/csl/glsl-kernel.js')
const { runPass } = await authority('src/runtime/pass-runner.js')
const { Surface } = await authority('src/runtime/surface.js')

function source(width, height, tag) {
  const bytes = new Uint8Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      bytes[i] = (31 * x + 17 * y + 13 * tag) % 256
      bytes[i + 1] = (11 * x + 47 * y + 29 * tag) % 256
      bytes[i + 2] = (67 * x + 19 * y + 7 * tag) % 256
      bytes[i + 3] = (255 - 23 * x - 37 * y - 5 * tag) & 255
    }
  }
  return Surface.fromRgba8(width, height, bytes)
}

const input = source(5, 3, 1)
const blur = source(3, 5, 11)
const color = source(7, 2, 23)
const edge = source(4, 6, 37)
const simplified = source(6, 4, 41)
const text = source(2, 7, 53)

function bindingsFor(key) {
  const uniforms = {}
  const textures = { inputTex: input }
  if (key === 'filter/celShading:celShadingBlend') {
    textures.colorTex = color
    textures.edgeTex = edge
    uniforms.edgeColor = [0.17, 0.63, 0.91]
    uniforms.mixAmount = 0.71
  } else if (key === 'filter/chroma:chroma') {
    uniforms.targetHue = 0.37
    uniforms.range = 0.19
    uniforms.feather = 0.07
  } else if (key === 'filter/chrome:chMap') {
    textures.blurTex = blur
    uniforms.detail = 63.0
    uniforms.distortion = 27.0
  } else if (key === 'filter/colorReplace:colorReplace') {
    uniforms.targetColor = [0.23, 0.51, 0.77]
    uniforms.replaceColor = [0.88, 0.16, 0.42]
    uniforms.sensitivity = 0.43
    uniforms.smoothing = 0.18
    uniforms.colorMix = 0.67
    uniforms.replaceAlpha = 0.82
    uniforms.keepAlpha = 0.31
  } else if (key === 'filter/deriv:deriv') {
    uniforms.amount = 1.7
    uniforms.renderScale = 0.75
  } else if (key === 'filter/lensFlare:lensFlare') {
    uniforms.brightness = 137.0
    uniforms.centerX = 0.29
    uniforms.centerY = 0.61
    uniforms.tint = [0.83, 0.94, 0.71]
    // Compile-time-variant define, default-only per task-9-report.md.
    uniforms.LENS_TYPE = 0
  } else if (key === 'filter/mosaicTiles:mosaicTiles') {
    uniforms.tileSize = 4.7
    uniforms.groutWidth = 22.0
    uniforms.relief = 58.0
    uniforms.maxOffset = 31.0
    uniforms.gapFill = 2
    uniforms.backgroundColor = [0.12, 0.34, 0.56]
    uniforms.seed = 7
    // Compile-time-variant define, default-only per task-9-report.md.
    uniforms.MODE = 0
  } else if (key === 'filter/photocopy:pcCombine') {
    textures.blurTex = blur
    uniforms.darkness = 68.0
    uniforms.inkColor = [0.08, 0.17, 0.29]
    uniforms.paperColor = [0.93, 0.84, 0.61]
  } else if (key === 'filter/relief:rlShade') {
    textures.blurTex = blur
    // Compile-time-variant define, default-only per task-9-report.md.
    uniforms.MODE = 0
    uniforms.detail = 57.0
    uniforms.lightAngle = 123.0
    uniforms.balance = 44.0
    uniforms.graininess = 36.0
    uniforms.inkColor = [0.09, 0.18, 0.27]
    uniforms.paperColor = [0.92, 0.79, 0.63]
  } else if (key === 'filter/ridge:ridge') {
    uniforms.level = 0.42
  } else if (key === 'filter/scatter:scatterJitter') {
    uniforms.radius = 2.7
    uniforms.seed = 11
  } else if (key === 'filter/simpleAberration:chromaticAberration') {
    uniforms.displacement = 0.037
  } else if (key === 'filter/text:text') {
    textures.textTex = text
    uniforms.matteColor = [0.14, 0.35, 0.73]
    uniforms.matteOpacity = 0.38
  } else if (key === 'filter/unsharpMask:usmCombine') {
    textures.blurTex = blur
    uniforms.amount = 173.0
    uniforms.threshold = 14.0
  } else if (key === 'filter/watercolor:wcComposite') {
    textures.simplifiedTex = simplified
    uniforms.shadowIntensity = 61.0
    uniforms.paperTexture = 43.0
  } else if (key === 'filter/watercolor:wcSeed') {
    // no extra binding
  }
  return { uniforms, textures }
}

// Declared float uniforms are explicitly f32 at binding (task-9-report.md
// contract): a JS float64 literal like 0.71 is not bit-identical to the
// float32 value the C++ side binds as `0.71f`, and that sub-ULP difference
// propagates through the kernel. Round every leaf number (scalars and vector
// components alike -- fround on an already-exact integer is a no-op).
function f32Deep(value) {
  if (Array.isArray(value)) return value.map(f32Deep)
  if (typeof value === 'number') return Math.fround(value)
  return value
}

function render(key) {
  const { uniforms, textures } = bindingsFor(key)
  const roundedUniforms = {}
  for (const [name, value] of Object.entries(uniforms)) roundedUniforms[name] = f32Deep(value)
  const factory = canonicalKernelFactories[key]
  if (!factory) throw new Error(`no canonical kernel factory for ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width: 7,
    height: 5,
    time: 0.125,
    seed: 7,
    tileOffset: new Float32Array([3, -2]),
    fullResolution: new Float32Array([17, 13]),
    uniforms: roundedUniforms,
    textures,
  })
  const destination = new Surface(7, 5)
  runPass({ kernel, destination })
  return destination
}

function littleEndianFloatBytes(surface) {
  const bytes = new Uint8Array(surface.data.length * 4)
  const view = new DataView(bytes.buffer)
  for (let i = 0; i < surface.data.length; i += 1) view.setFloat32(i * 4, surface.data[i], true)
  return bytes
}

function sha256Hex(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

function bitsHex(f32) {
  const view = new DataView(new ArrayBuffer(4))
  view.setFloat32(0, f32, true)
  return view.getUint32(0, true).toString(16).padStart(8, '0')
}

const KEYS = [
  'filter/celShading:celShadingBlend',
  'filter/chroma:chroma',
  'filter/chrome:chMap',
  'filter/colorReplace:colorReplace',
  'filter/deriv:deriv',
  'filter/lensFlare:lensFlare',
  'filter/mosaicTiles:mosaicTiles',
  'filter/photocopy:pcCombine',
  'filter/relief:rlShade',
  'filter/ridge:ridge',
  'filter/scatter:scatterJitter',
  'filter/simpleAberration:chromaticAberration',
  'filter/text:text',
  'filter/unsharpMask:usmCombine',
  'filter/watercolor:wcComposite',
  'filter/watercolor:wcSeed',
]

for (const key of KEYS) {
  const surface = render(key)
  const floats = sha256Hex(littleEndianFloatBytes(surface))
  const rgba = sha256Hex(surface.toRgba8())
  const probes = Array.from(surface.data.slice(0, 12)).map(bitsHex).join(' ')
  console.log(`${key}\tfloats=${floats}\trgba=${rgba}\tfirst=0x${bitsHex(surface.data[0])}\tprobes=${probes}`)
}
