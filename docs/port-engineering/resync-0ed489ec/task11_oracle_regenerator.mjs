// Re-derivation script for `typed_task11_all_ninety_four_external_oracles_are_exact_and_repeatable`
// (tests/test_typed_slice.cpp), part of the 0ed489ec46842bffba33ee2ec65a218b6dda51f5 resync
// (CPU authority 61aa869). Mirrors populate_task11_bindings()/render_task11() exactly.
// Full binding contract is also recorded in docs/port-engineering/task-11-oracles.json.
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task11_oracle_regenerator.mjs

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

function task11Grayscale() {
  const bytes = new Uint8Array(4 * 6 * 4)
  for (let y = 0; y < 6; y += 1) {
    for (let x = 0; x < 4; x += 1) {
      const i = (y * 4 + x) * 4
      const value = 20 + 17 * x + 11 * y
      bytes[i] = value; bytes[i + 1] = value; bytes[i + 2] = value
      bytes[i + 3] = 200 - 9 * x - 7 * y
    }
  }
  return Surface.fromRgba8(4, 6, bytes)
}

function task11Transparent() {
  const bytes = new Uint8Array(17 * 13 * 4)
  for (let i = 0; i < bytes.length; i += 4) {
    bytes[i] = 211; bytes[i + 1] = 37; bytes[i + 2] = 143; bytes[i + 3] = 0
  }
  return Surface.fromRgba8(17, 13, bytes)
}

function task11Edges() {
  const bytes = new Uint8Array(4 * 6 * 4)
  for (let y = 0; y < 6; y += 1) {
    for (let x = 0; x < 4; x += 1) {
      const i = (y * 4 + x) * 4
      bytes[i] = (31 * x + 17 * y + 13 * 37) % 256
      bytes[i + 1] = (11 * x + 47 * y + 29 * 37) % 256
      bytes[i + 2] = (67 * x + 19 * y + 7 * 37) % 256
      bytes[i + 3] = (255 - 23 * x - 37 * y - 5 * 37) & 255
    }
  }
  bytes[(5 * 4 + 3) * 4] = 255
  return Surface.fromRgba8(4, 6, bytes)
}

function task11TintHybrid() {
  const bytes = new Uint8Array([
    0, 0, 0, 255, 64, 64, 64, 244, 230, 30, 80, 233, 30, 220, 80, 222, 40, 70, 230, 211,
    96, 96, 96, 200, 240, 80, 20, 189, 20, 240, 100, 178, 60, 100, 240, 167, 200, 30, 160, 156,
    17, 17, 17, 145, 180, 40, 90, 134, 50, 180, 210, 123, 210, 160, 30, 112, 90, 30, 180, 101,
  ])
  return Surface.fromRgba8(5, 3, bytes)
}

const input = source(5, 3, 1)
const tex = source(7, 2, 23)
const edges = task11Edges()
const grayscale = task11Grayscale()
const tintHybrid = task11TintHybrid()
const media = source(17, 13, 59)
const transparent = task11Transparent()

function suffix(value, prefix) {
  let result = 0
  for (const digit of value.slice(prefix.length)) result = result * 10 + (digit.charCodeAt(0) - 48)
  return result
}

function bindingsFor(key, variant) {
  const uniforms = {
    resolution: [7.0, 5.0],
    tileOffset: [3.0, 2.0],
    fullResolution: [13.0, 11.0],
    time: 0.125,
  }
  const textures = {}
  if (key === 'classicNoisedeck/splat:splat') {
    textures.inputTex = input
    uniforms.seed = 7.0; uniforms.enabled = true
    uniforms.useSpecks = true; uniforms.splatSource = 0; uniforms.scale = 3.7
    uniforms.cutoff = 41.0; uniforms.speed = 2.0
    uniforms.splatColor = [0.81, 0.22, 0.63]
    uniforms.mode = 2; uniforms.speckScale = 2.6; uniforms.speckCutoff = 38.0
    uniforms.speckSpeed = 3.0; uniforms.speckSeed = 5.0
    uniforms.speckColor = [0.17, 0.74, 0.39]
    uniforms.speckMode = 3
    if (variant === 'disabledNoSpecks') { uniforms.enabled = false; uniforms.useSpecks = false }
    if (variant.startsWith('splatMode')) { uniforms.useSpecks = false; uniforms.mode = suffix(variant, 'splatMode') }
    if (variant.startsWith('speckMode')) { uniforms.enabled = false; uniforms.speckMode = suffix(variant, 'speckMode') }
  } else if (key === 'filter/corrupt:corrupt') {
    textures.inputTex = input
    uniforms.seed = 7.0; uniforms.intensity = 0.0; uniforms.sort = 0.0
    uniforms.shift = 0.0; uniforms.bits = 0.0; uniforms.channelShift = 0.0; uniforms.speed = 3.0
    uniforms.melt = 0.0; uniforms.scatter = 0.0; uniforms.bandHeight = 3.0; uniforms.renderScale = 1.0
    if (variant !== 'clean') {
      if (variant === 'mixedLowBits') {
        uniforms.intensity = 50.0; uniforms.bits = 20.0
      } else {
        uniforms.intensity = 100.0; uniforms.sort = 100.0; uniforms.shift = 100.0
        uniforms.bits = variant === 'bitsMid' ? 45.0 : 100.0
        uniforms.channelShift = 100.0
        if (variant === 'full') { uniforms.melt = 100.0; uniforms.scatter = 100.0 }
      }
    }
  } else if (key === 'filter/flipMirror:flipMirror') {
    textures.inputTex = input
    uniforms.flipMode = suffix(variant, 'mode')
  } else if (key === 'filter/outline:outlineBlend') {
    textures.inputTex = input; textures.edgesTexture = edges
    uniforms.invert = variant === 'whiteOutline' ? 1.0 : 0.0
  } else if (key === 'filter/outline:outlineValueMap') {
    textures.inputTex = variant === 'grayscale' ? grayscale : input
  } else if (key === 'filter/spatter:spatter') {
    textures.inputTex = input
    uniforms.color = [0.83, 0.19, 0.47]
    uniforms.density = 1.5; uniforms.alpha = 0.83; uniforms.seed = 11
    if (variant === 'fallbackResolution') uniforms.fullResolution = [0.0, 0.0]
  } else if (key === 'filter/tint:colorize') {
    textures.inputTex = variant === 'mode2' ? tintHybrid : input
    uniforms.color = [0.16, 0.69, 0.83]
    uniforms.alpha = 0.62; uniforms.mode = suffix(variant, 'mode')
  } else if (key === 'mixer/blendMode:blendMode') {
    textures.inputTex = input; textures.tex = tex
    const mode = suffix(variant, 'mode')
    uniforms.mode = mode; uniforms.mixAmt = mode === 14 ? 47.0 : -37.0
  } else if (key === 'mixer/centerMask:centerMask') {
    textures.inputTex = input; textures.tex = tex
    uniforms.shape = 0
    uniforms.power = -80.0; uniforms.hardness = 0.0; uniforms.blendMode = 14
    if (variant === 'shape-1') uniforms.shape = -1
    else if (variant.startsWith('shape')) uniforms.shape = suffix(variant, 'shape')
    else { uniforms.shape = 2; uniforms.blendMode = suffix(variant, 'blend') }
  } else if (key === 'synth/media:mediaInput') {
    textures.imageTex = variant === 'transparent' ? transparent : media
    uniforms.imageSize = [17.0, 13.0]; uniforms.position = 0
    uniforms.rotation = 0.0; uniforms.scaleAmt = 100.0; uniforms.offsetX = 0.0
    uniforms.offsetY = 0.0; uniforms.tiling = 0; uniforms.flip = 0
    uniforms.bgColor = [0.12, 0.34, 0.56]; uniforms.bgAlpha = 0.71
    if (variant.startsWith('position')) uniforms.position = suffix(variant, 'position')
    else if (variant.startsWith('tiling')) {
      uniforms.position = 4; uniforms.scaleAmt = 40.0
      uniforms.tiling = suffix(variant, 'tiling')
    } else if (variant.startsWith('flip')) {
      uniforms.position = 4
      uniforms.flip = suffix(variant, 'flip')
    } else if (variant === 'outOfBounds') {
      uniforms.scaleAmt = 15.0; uniforms.offsetX = 100.0; uniforms.offsetY = 100.0
      uniforms.bgColor = [0.03, 0.57, 0.91]; uniforms.bgAlpha = 0.63
    } else {
      uniforms.position = 4
      if (variant === 'scaleZeroGuard') uniforms.scaleAmt = Infinity
    }
  }
  return { uniforms, textures }
}

function f32Deep(value) {
  if (Array.isArray(value)) return value.map(f32Deep)
  if (typeof value === 'number') return Math.fround(value)
  return value
}

function render(key, variant) {
  const { uniforms, textures } = bindingsFor(key, variant)
  const roundedUniforms = {}
  for (const [name, value] of Object.entries(uniforms)) roundedUniforms[name] = f32Deep(value)
  const factory = canonicalKernelFactories[key]
  if (!factory) throw new Error(`no canonical kernel factory for ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width: 7,
    height: 5,
    time: 0.125,
    seed: 7,
    tileOffset: new Float32Array(roundedUniforms.tileOffset ?? [3, 2]),
    fullResolution: new Float32Array(roundedUniforms.fullResolution ?? [13, 11]),
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

const FIXTURES = [
  ['classicNoisedeck/splat:splat', 'primary'],
  ['classicNoisedeck/splat:splat', 'disabledNoSpecks'],
  ['classicNoisedeck/splat:splat', 'splatMode0'],
  ['classicNoisedeck/splat:splat', 'splatMode1'],
  ['classicNoisedeck/splat:splat', 'splatMode3'],
  ['classicNoisedeck/splat:splat', 'speckMode0'],
  ['classicNoisedeck/splat:splat', 'speckMode1'],
  ['classicNoisedeck/splat:splat', 'speckMode2'],
  ['filter/corrupt:corrupt', 'clean'],
  ['filter/corrupt:corrupt', 'full'],
  ['filter/corrupt:corrupt', 'bitsMid'],
  ['filter/corrupt:corrupt', 'mixedLowBits'],
  ['filter/flipMirror:flipMirror', 'mode0'],
  ['filter/flipMirror:flipMirror', 'mode1'],
  ['filter/flipMirror:flipMirror', 'mode2'],
  ['filter/flipMirror:flipMirror', 'mode3'],
  ['filter/flipMirror:flipMirror', 'mode11'],
  ['filter/flipMirror:flipMirror', 'mode12'],
  ['filter/flipMirror:flipMirror', 'mode13'],
  ['filter/flipMirror:flipMirror', 'mode14'],
  ['filter/flipMirror:flipMirror', 'mode15'],
  ['filter/flipMirror:flipMirror', 'mode16'],
  ['filter/flipMirror:flipMirror', 'mode17'],
  ['filter/flipMirror:flipMirror', 'mode18'],
  ['filter/outline:outlineBlend', 'blackOutline'],
  ['filter/outline:outlineBlend', 'whiteOutline'],
  ['filter/outline:outlineValueMap', 'colorOklab'],
  ['filter/outline:outlineValueMap', 'grayscale'],
  ['filter/spatter:spatter', 'primary'],
  ['filter/spatter:spatter', 'fallbackResolution'],
  ['filter/tint:colorize', 'mode0'],
  ['filter/tint:colorize', 'mode1'],
  ['filter/tint:colorize', 'mode2'],
  ...Array.from({ length: 16 }, (_, i) => ['mixer/blendMode:blendMode', `mode${i}`]),
  ['mixer/centerMask:centerMask', 'shape0'],
  ['mixer/centerMask:centerMask', 'shape1'],
  ['mixer/centerMask:centerMask', 'shape2'],
  ['mixer/centerMask:centerMask', 'shape-1'],
  ...Array.from({ length: 14 }, (_, i) => ['mixer/centerMask:centerMask', `blend${i}`]),
  ['mixer/centerMask:centerMask', 'blend15'],
  ...Array.from({ length: 9 }, (_, i) => ['synth/media:mediaInput', `position${i}`]),
  ['synth/media:mediaInput', 'tiling1'],
  ['synth/media:mediaInput', 'tiling2'],
  ['synth/media:mediaInput', 'tiling3'],
  ['synth/media:mediaInput', 'flip1'],
  ['synth/media:mediaInput', 'flip2'],
  ['synth/media:mediaInput', 'flip3'],
  ['synth/media:mediaInput', 'flip11'],
  ['synth/media:mediaInput', 'flip12'],
  ['synth/media:mediaInput', 'flip13'],
  ['synth/media:mediaInput', 'flip14'],
  ['synth/media:mediaInput', 'flip15'],
  ['synth/media:mediaInput', 'flip16'],
  ['synth/media:mediaInput', 'flip17'],
  ['synth/media:mediaInput', 'flip18'],
  ['synth/media:mediaInput', 'outOfBounds'],
  ['synth/media:mediaInput', 'transparent'],
  ['synth/media:mediaInput', 'scaleZeroGuard'],
]

console.error(`total fixtures: ${FIXTURES.length}`)
for (const [key, variant] of FIXTURES) {
  const surface = render(key, variant)
  const floats = sha256Hex(littleEndianFloatBytes(surface))
  const rgba = sha256Hex(surface.toRgba8())
  const probes = [0, 17, 34].flatMap((p) => Array.from(surface.data.slice(p * 4, p * 4 + 4)).map(bitsHex)).join(' ')
  console.log(`${key}/${variant}\tfloats=${floats}\trgba=${rgba}\tprobes=${probes}`)
}
