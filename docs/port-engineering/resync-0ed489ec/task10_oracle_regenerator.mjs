// Re-derivation script for the task-10 control-flow slice oracle tables
// (tests/test_typed_slice.cpp: typed_control_flow_slice_external_oracles_are_repeatable
// and typed_control_flow_slice_external_branch_oracles_cover_every_arm), part of the
// 0ed489ec46842bffba33ee2ec65a218b6dda51f5 resync (CPU authority 61aa869). Mirrors
// populate_task10_bindings()/render_task10() exactly, including the mixer/alphaMask:alphaMask
// `baseTex` sampler that the new upstream contract added (see docs/port-engineering/task-10-report.md).
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task10_oracle_regenerator.mjs

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

// glowing_edge_source(): low-contrast 6x4 surface, tests/test_typed_slice.cpp.
function glowingEdgeSource() {
  const width = 6
  const height = 4
  const bytes = new Uint8Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      bytes[i] = 45 + 7 * x + 11 * y
      bytes[i + 1] = 73 + 5 * x + 9 * y
      bytes[i + 2] = 22 + 3 * x + 13 * y
      bytes[i + 3] = 255 - 4 * x - 7 * y
    }
  }
  return Surface.fromRgba8(width, height, bytes)
}

// translucent_base_source(): resync addition, tests/test_typed_slice.cpp.
function translucentBaseSource() {
  const width = 4
  const height = 3
  const bytes = new Uint8Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      bytes[i] = 60 + 13 * x + 9 * y
      bytes[i + 1] = 90 + 17 * x + 5 * y
      bytes[i + 2] = 150 + 3 * x + 7 * y
      bytes[i + 3] = 96
    }
  }
  return Surface.fromRgba8(width, height, bytes)
}

const regularInput = source(5, 3, 1)
const edgeInput = glowingEdgeSource()
const blur = source(3, 5, 11)
const tex = source(7, 2, 23)
const base = source(4, 3, 59)

function f32Deep(value) {
  if (Array.isArray(value)) return value.map(f32Deep)
  if (typeof value === 'number') return Math.fround(value)
  return value
}

function bindingsFor(key, polygonSmoothing) {
  const uniforms = {
    tileOffset: [3.0, -2.0],
    fullResolution: [17.0, 13.0],
  }
  const textures = { inputTex: key === 'filter/glowingEdge:glowingEdge' ? edgeInput : regularInput }
  if (key === 'filter/channel:channel') {
    uniforms.channel = 2; uniforms.scale = 2.37; uniforms.offset = 0.19
  } else if (key === 'filter/chromaticAberration:chromaticAberration') {
    uniforms.aberrationAmt = 73.5; uniforms.passthru = 42.25
  } else if (key === 'filter/glowingEdge:glowingEdge') {
    uniforms.alpha = 0.73; uniforms.sobelMetric = 3.0; uniforms.width = 0.4
  } else if (key === 'filter/highPass:hpCombine') {
    textures.blurTex = blur; uniforms.mono = false
  } else if (key === 'filter/pixels:pixels') {
    uniforms.size = 3.7
  } else if (key === 'filter/plasticWrap:pwSpec') {
    textures.blurTex = blur; uniforms.highlight = 77.3; uniforms.smoothness = 31.7
    uniforms.lightDirection = [0.31, 0.79, 0.43]
  } else if (key === 'filter/seamless:seamless') {
    uniforms.blend = 0.31; uniforms.repeat = 2.3; uniforms.curve = 1
  } else if (key === 'filter/sine:sine') {
    uniforms.amount = 8.7; uniforms.colorMode = 1.0
  } else if (key === 'filter/vignette:vignette') {
    uniforms.vignetteBrightness = 0.21; uniforms.alpha = 0.81
  } else if (key === 'mixer/alphaMask:alphaMask') {
    textures.tex = tex; textures.baseTex = base
    uniforms.mixAmt = 47.0; uniforms.maskMode = false
  } else if (key === 'mixer/applyMode:applyMode') {
    textures.tex = tex; uniforms.mode = 1; uniforms.mixAmt = 47.0
  } else if (key === 'mixer/thresholdMix:thresholdMix') {
    textures.tex = tex; uniforms.mode = 1; uniforms.quantize = 3
    uniforms.mapSource = 1; uniforms.threshold = 0.41; uniforms.range = 0.19
    uniforms.thresholdR = 0.22; uniforms.rangeR = 0.0; uniforms.thresholdG = 0.48
    uniforms.rangeG = 0.17; uniforms.thresholdB = 0.69; uniforms.rangeB = 0.0
  } else if (key === 'synth/polygon:shape') {
    uniforms.tileOffset = [3.0, 3.0]
    uniforms.fullResolution = [13.0, 11.0]
    uniforms.aspect = 7.0 / 5.0
    uniforms.sides = 3
    uniforms.radius = 0.4; uniforms.smoothing = polygonSmoothing; uniforms.rotation = 23.0
    uniforms.fgColor = [0.14, 0.73, 0.31]; uniforms.fgAlpha = 0.83
    uniforms.bgColor = [0.91, 0.22, 0.58]; uniforms.bgAlpha = 0.47
  }
  return { uniforms, textures }
}

function applyVariant(uniforms, textures, variant) {
  if (variant === 'channel0') uniforms.channel = 0
  else if (variant === 'channel1') uniforms.channel = 1
  else if (variant === 'channel3') uniforms.channel = 3
  else if (variant === 'fullResolutionZero') uniforms.fullResolution = [0.0, 0.0]
  else if (variant === 'metric0') uniforms.sobelMetric = 0.0
  else if (variant === 'metric1') uniforms.sobelMetric = 1.0
  else if (variant === 'metric2') uniforms.sobelMetric = 2.0
  else if (variant === 'mono') uniforms.mono = true
  else if (variant === 'earlyReturn') uniforms.size = 0.75
  else if (variant === 'zeroLightFallback') uniforms.lightDirection = [0.0, 0.0, 0.0]
  else if (variant === 'oppositeLightHalfFallback') uniforms.lightDirection = [0.0, 0.0, -1.0]
  else if (variant === 'linear') uniforms.curve = 0
  else if (variant === 'sharp') uniforms.curve = 2
  else if (variant === 'zeroBlend') uniforms.blend = 0.0
  else if (variant === 'luminance') uniforms.colorMode = 0.0
  else if (variant === 'maskReturn') uniforms.maskMode = true
  else if (variant === 'maskTranslucentBase') { uniforms.maskMode = true; textures.baseTex = translucentBaseSource() }
  else if (variant === 'alphaNegative') uniforms.mixAmt = -37.0
  else if (variant === 'brightnessNegative') { uniforms.mode = 0; uniforms.mixAmt = -47.0 }
  else if (variant === 'saturation') uniforms.mode = 2
  else if (variant === 'luminanceHard' || variant === 'luminanceSoft') {
    uniforms.mode = 0; uniforms.quantize = 0; uniforms.mapSource = 0
    uniforms.range = variant === 'luminanceHard' ? 0.0 : 0.19
    uniforms.rangeG = 0.0
  } else if (variant === 'sides5ZeroAlpha') {
    uniforms.sides = 5; uniforms.fgAlpha = 0.0; uniforms.bgAlpha = 0.0
  }
}

function render(key, polygonSmoothing = 0.12, variant = null) {
  const { uniforms, textures } = bindingsFor(key, polygonSmoothing)
  if (variant) applyVariant(uniforms, textures, variant)
  const roundedUniforms = {}
  for (const [name, value] of Object.entries(uniforms)) roundedUniforms[name] = f32Deep(value)
  const factory = canonicalKernelFactories[key]
  if (!factory) throw new Error(`no canonical kernel factory for ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width: 7,
    height: 5,
    time: 0.125,
    seed: 7,
    tileOffset: new Float32Array(roundedUniforms.tileOffset ?? [3, -2]),
    fullResolution: new Float32Array(roundedUniforms.fullResolution ?? [17, 13]),
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

function report(name, surface) {
  const floats = sha256Hex(littleEndianFloatBytes(surface))
  const rgba = sha256Hex(surface.toRgba8())
  const probePixels = [0, 17, 34]
  const probes = probePixels.flatMap((p) => Array.from(surface.data.slice(p * 4, p * 4 + 4)).map(bitsHex)).join(' ')
  console.log(`${name}\tfloats=${floats}\trgba=${rgba}\tprobes=${probes}`)
}

const MAIN_KEYS = [
  'filter/channel:channel',
  'filter/chromaticAberration:chromaticAberration',
  'filter/glowingEdge:glowingEdge',
  'filter/highPass:hpCombine',
  'filter/pixels:pixels',
  'filter/plasticWrap:pwSpec',
  'filter/seamless:seamless',
  'filter/sine:sine',
  'filter/vignette:vignette',
  'mixer/alphaMask:alphaMask',
  'mixer/applyMode:applyMode',
  'mixer/thresholdMix:thresholdMix',
  'synth/polygon:shape',
]
for (const key of MAIN_KEYS) report(key, render(key))
report('synth/polygon:shape[zero]', render('synth/polygon:shape', 0.0))

const BRANCH_FIXTURES = [
  ['filter/channel:channel', 'channel0'],
  ['filter/channel:channel', 'channel1'],
  ['filter/channel:channel', 'channel3'],
  ['filter/chromaticAberration:chromaticAberration', 'fullResolutionZero'],
  ['filter/glowingEdge:glowingEdge', 'metric0'],
  ['filter/glowingEdge:glowingEdge', 'metric1'],
  ['filter/glowingEdge:glowingEdge', 'metric2'],
  ['filter/highPass:hpCombine', 'mono'],
  ['filter/pixels:pixels', 'earlyReturn'],
  ['filter/plasticWrap:pwSpec', 'zeroLightFallback'],
  ['filter/plasticWrap:pwSpec', 'oppositeLightHalfFallback'],
  ['filter/seamless:seamless', 'linear'],
  ['filter/seamless:seamless', 'sharp'],
  ['filter/seamless:seamless', 'zeroBlend'],
  ['filter/sine:sine', 'luminance'],
  ['filter/vignette:vignette', 'fullResolutionZero'],
  ['mixer/alphaMask:alphaMask', 'maskReturn'],
  ['mixer/alphaMask:alphaMask', 'maskTranslucentBase'],
  ['mixer/alphaMask:alphaMask', 'alphaNegative'],
  ['mixer/applyMode:applyMode', 'brightnessNegative'],
  ['mixer/applyMode:applyMode', 'saturation'],
  ['mixer/thresholdMix:thresholdMix', 'luminanceHard'],
  ['mixer/thresholdMix:thresholdMix', 'luminanceSoft'],
  ['synth/polygon:shape', 'sides5ZeroAlpha'],
]
for (const [key, variant] of BRANCH_FIXTURES) report(`${key}/${variant}`, render(key, 0.12, variant))
