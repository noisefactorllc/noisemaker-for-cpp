// Re-derivation script for `typed_task14_all_thirty_external_oracles_are_exact_repeatable_and_top_down`
// (tests/test_typed_slice.cpp). Mirrors task14_cases()/populate_task14_bindings()/render_task14()
// exactly; CASES carries each native row's binding inputs in the same order.
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task14_oracle_regenerator.mjs

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

const surfaces = { 1: source(5, 3, 1), 23: source(4, 6, 23), 37: source(7, 2, 37), 53: source(3, 5, 53) }
function surface(tag) {
  if (!surfaces[tag]) throw new Error(`unknown Task 14 formula surface tag ${tag}`)
  return surfaces[tag]
}

// key, variant, values (f32), integers, flag, tileOffset, fullResolution, time, inputTag, originalTag
const CASES = [
  ['filter/pixelSort:prepare', 'mirror_light', [-135.0, 0.0, 0.0, 0.0, 0.0], [0, 0, 0], false, [-7.0, 5.0], [17.0, 13.0], 0.375, 1, 0],
  ['filter/pixelSort:prepare', 'repeat_dark', [90.0, 1.0, 0.0, 0.0, 0.0], [0, 0, 0], true, [11.0, -4.0], [29.0, 17.0], 0.375, 23, 0],
  ['filter/pixelSort:prepare', 'clamp_light', [180.0, 2.0, 0.0, 0.0, 0.0], [0, 0, 0], false, [-13.0, 9.0], [23.0, 19.0], 0.375, 37, 0],
  ['filter/pixelSort:prepare', 'fallback_dark', [37.0, 9.0, 0.0, 0.0, 0.0], [0, 0, 0], true, [5.0, -11.0], [31.0, 13.0], 0.375, 53, 0],
  ['filter/pixelSort:finalize', 'mirror_alpha0_light', [-135.0, 0.0, 0.0, 0.0, 0.0], [0, 0, 0], false, [-7.0, 5.0], [17.0, 13.0], 0.375, 1, 23],
  ['filter/pixelSort:finalize', 'repeat_alpha073_dark', [90.0, 1.0, 0.73000001907348633, 0.0, 0.0], [0, 0, 0], true, [11.0, -4.0], [29.0, 17.0], 0.375, 23, 37],
  ['filter/pixelSort:finalize', 'clamp_alpha1_light', [180.0, 2.0, 1.0, 0.0, 0.0], [0, 0, 0], false, [-13.0, 9.0], [23.0, 19.0], 0.375, 37, 53],
  ['filter/pixelSort:finalize', 'fallback_alpha027_dark', [37.0, 9.0, 0.27000001072883606, 0.0, 0.0], [0, 0, 0], true, [5.0, -11.0], [31.0, 13.0], 0.375, 53, 1],
  ['filter/skew:skew', 'clamp_negative_tile', [-0.37000000476837158, -137.0, 0.0, 0.73000001907348633, 0.0], [0, 0, 0], false, [-7.0, 5.0], [17.0, 13.0], 0.375, 1, 0],
  ['filter/skew:skew', 'mirror_clamped_skew', [100.0, 0.0, 1.0, 1.9099999666213989, 0.0], [0, 0, 0], false, [11.0, -4.0], [29.0, 17.0], 0.375, 23, 0],
  ['filter/skew:skew', 'repeat_positive', [0.70999997854232788, 123.0, 2.0, 1.0, 0.0], [0, 0, 0], false, [-13.0, 9.0], [23.0, 19.0], 0.375, 37, 0],
  ['filter/skew:skew', 'fallback_repeat', [-100.0, 179.0, -4.0, 0.5, 0.0], [0, 0, 0], false, [5.0, -11.0], [31.0, 13.0], 0.375, 53, 0],
  ['filter/tetraCosine:tetraCosine', 'rgb_static_alpha0', [0.0, 0.0, 0.0, 0.0, 0.0], [0, 0, 0], false, [-7.0, 5.0], [17.0, 13.0], 0.375, 1, 0],
  ['filter/tetraCosine:tetraCosine', 'hsv_backward', [0.40999999642372131, 0.0, 0.0, 0.0, 0.0], [1, -1, 0], false, [11.0, -4.0], [29.0, 17.0], 0.875, 23, 0],
  ['filter/tetraCosine:tetraCosine', 'oklab_forward_alpha1', [1.0, 0.0, 0.0, 0.0, 0.0], [2, 1, 0], false, [-13.0, 9.0], [23.0, 19.0], 0.625, 37, 0],
  ['filter/tetraCosine:tetraCosine', 'oklch_static', [0.77999997138977051, 0.0, 0.0, 0.0, 0.0], [3, 0, 0], false, [5.0, -11.0], [31.0, 13.0], 1.125, 53, 0],
  ['filter/tetraCosine:tetraCosine', 'fallback_rgb', [0.23000000417232513, 0.0, 0.0, 0.0, 0.0], [9, 9, 0], false, [-17.0, -3.0], [37.0, 21.0], 1.75, 1, 0],
  ['filter/tile:tile', 'mirrorXY_aspect', [0.37000000476837158, -0.61000001430511475, 0.43999999761581421, 17.0, 2.2999999523162842], [0, 0, 0], true, [-7.0, 5.0], [17.0, 13.0], 0.375, 1, 0],
  ['filter/tile:tile', 'rotate2_noaspect', [1.7100000381469727, 0.82999998331069946, -0.28999999165534973, 113.0, 4.6999998092651367], [1, 0, 0], false, [11.0, -4.0], [29.0, 17.0], 0.375, 23, 0],
  ['filter/tile:tile', 'rotate4_aspect', [0.92000001668930054, -0.14000000059604645, 0.67000001668930054, 251.0, 6.0999999046325684], [2, 0, 0], true, [-13.0, 9.0], [23.0, 19.0], 0.375, 37, 0],
  ['filter/tile:tile', 'hex_rotate6_noaspect', [2.2699999809265137, 0.37999999523162842, -0.73000001907348633, 329.0, 3.4000000953674316], [3, 0, 0], false, [5.0, -11.0], [31.0, 13.0], 0.375, 53, 0],
  ['filter/tile:tile', 'fallback_rotate4', [0.57999998331069946, 0.9100000262260437, 0.11999999731779099, 71.0, 8.6000003814697266], [9, 0, 0], true, [-17.0, -3.0], [37.0, 21.0], 0.375, 1, 0],
  ['synth/osc2d:osc2d', 'sine', [0.0, -137.0, 0.0, 0.0, 0.0], [0, 3, 7], false, [-7.0, 5.0], [17.0, 13.0], 0.0, 0, 0],
  ['synth/osc2d:osc2d', 'linear', [2.5, -45.0, 0.0, 0.0, 0.0], [1, 5, 19], false, [11.0, -4.0], [29.0, 17.0], 0.375, 0, 0],
  ['synth/osc2d:osc2d', 'saw', [4.25, 0.0, 0.0, 0.0, 0.0], [2, 7, 37], false, [-13.0, 9.0], [23.0, 19.0], 0.875, 0, 0],
  ['synth/osc2d:osc2d', 'saw_inverse', [1.5, 67.0, 0.0, 0.0, 0.0], [3, 11, 61], false, [5.0, -11.0], [31.0, 13.0], 1.125, 0, 0],
  ['synth/osc2d:osc2d', 'square', [3.75, 179.0, 0.0, 0.0, 0.0], [4, 13, 83], false, [-17.0, -3.0], [37.0, 21.0], 1.75, 0, 0],
  ['synth/osc2d:osc2d', 'noise1d_resolution_fallback', [5.5, -91.0, 0.0, 0.0, 0.0], [5, 17, 101], false, [-19.0, 7.0], [0.0, 0.0], 0.625, 0, 0],
  ['synth/osc2d:osc2d', 'noise2d', [7.25, 31.0, 0.0, 0.0, 0.0], [6, 23, 251], false, [9.0, -15.0], [41.0, 27.0], 0.9375, 0, 0],
  ['synth/osc2d:osc2d', 'fallback_noise2d', [9.75, 143.0, 0.0, 0.0, 0.0], [9, 29, 503], false, [-23.0, -9.0], [43.0, 31.0], 1.375, 0, 0],
]

// Native float uniforms enter as f32 (fround is a no-op on integers and booleans stay booleans).
const f = Math.fround

function bindingsFor([key, , values, integers, flag, tileOffset, fullResolution, time, inputTag, originalTag]) {
  const uniforms = {}
  const textures = {}
  if (key === 'filter/pixelSort:prepare') {
    textures.inputTex = surface(inputTag)
    uniforms.resolution = [9.0, 7.0]
    uniforms.angled = values[0]; uniforms.time = time
    uniforms.darkest = flag; uniforms.wrap = values[1]
  } else if (key === 'filter/pixelSort:finalize') {
    textures.inputTex = surface(inputTag); textures.originalTex = surface(originalTag)
    uniforms.resolution = [9.0, 7.0]
    uniforms.angled = values[0]; uniforms.darkest = flag
    uniforms.wrap = values[1]; uniforms.alpha = values[2]
  } else if (key === 'filter/skew:skew') {
    textures.inputTex = surface(inputTag)
    uniforms.skewAmt = values[0]; uniforms.rotation = values[1]
    uniforms.wrap = values[2]; uniforms.tileOffset = tileOffset
    uniforms.fullResolution = fullResolution; uniforms.renderScale = values[3]
  } else if (key === 'filter/tetraCosine:tetraCosine') {
    textures.inputTex = surface(inputTag); uniforms.tileOffset = tileOffset
    uniforms.fullResolution = fullResolution; uniforms.colorMode = integers[0]
    uniforms.offsetR = 0.10999999940395355; uniforms.offsetG = 0.43000000715255737
    uniforms.offsetB = 0.79000002145767212; uniforms.ampR = 0.87000000476837158
    uniforms.ampG = 0.61000001430511475; uniforms.ampB = 0.28999999165534973
    uniforms.freqR = 1.0; uniforms.freqG = 3.0; uniforms.freqB = 4.0
    uniforms.phaseR = 0.070000000298023224; uniforms.phaseG = 0.33000001311302185
    uniforms.phaseB = 0.81000000238418579; uniforms.repeat = 2.7000000476837158
    uniforms.offset = 0.18999999761581421; uniforms.alpha = values[0]
    uniforms.rotation = integers[1]; uniforms.time = time
  } else if (key === 'filter/tile:tile') {
    textures.inputTex = surface(inputTag); uniforms.tileOffset = tileOffset
    uniforms.fullResolution = fullResolution; uniforms.symmetry = integers[0]
    uniforms.scale = values[0]; uniforms.offsetX = values[1]
    uniforms.offsetY = values[2]; uniforms.angle = values[3]
    uniforms.repeat = values[4]; uniforms.aspectLens = flag
  } else if (key === 'synth/osc2d:osc2d') {
    uniforms.resolution = [9.0, 7.0]
    uniforms.tileOffset = tileOffset; uniforms.fullResolution = fullResolution
    uniforms.aspect = fullResolution[0] / fullResolution[1]; uniforms.time = time
    uniforms.oscType = integers[0]; uniforms.frequency = integers[1]
    uniforms.speed = values[0]; uniforms.rotation = values[1]
    uniforms.seed = integers[2]
  } else {
    throw new Error(`unknown Task 14 key ${key}`)
  }
  return { uniforms, textures }
}

function render(fixture) {
  const [key, , , integers, , , , time] = fixture
  const { uniforms, textures } = bindingsFor(fixture)
  const rounded = {}
  for (const [name, value] of Object.entries(uniforms)) {
    if (Array.isArray(value)) rounded[name] = value.map(f)
    else rounded[name] = typeof value === 'boolean' ? value : f(value)
  }
  const factory = canonicalKernelFactories[key]
  if (!factory) throw new Error(`no canonical kernel factory for ${key}`)
  const options = { width: 9, height: 7, time: f(time), seed: f(integers[2]), uniforms: rounded, textures }
  if (rounded.tileOffset) options.tileOffset = new Float32Array(rounded.tileOffset)
  if (rounded.fullResolution) options.fullResolution = new Float32Array(rounded.fullResolution)
  const kernel = bindCanonicalKernel(factory, options)
  const destination = new Surface(9, 7)
  runPass({ kernel, destination })
  return destination
}

function littleEndianFloatBytes(value) {
  const bytes = new Uint8Array(value.data.length * 4)
  const view = new DataView(bytes.buffer)
  for (let i = 0; i < value.data.length; i += 1) view.setFloat32(i * 4, value.data[i], true)
  return bytes
}

const sha256Hex = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex')

function bitsHex(value) {
  const view = new DataView(new ArrayBuffer(4))
  view.setFloat32(0, value, true)
  return view.getUint32(0, true).toString(16).padStart(8, '0')
}

console.error(`total fixtures: ${CASES.length}`)
for (const fixture of CASES) {
  const output = render(fixture)
  const floats = sha256Hex(littleEndianFloatBytes(output))
  const rgba = sha256Hex(output.toRgba8())
  const probes = [0, 31, 62].flatMap((p) => Array.from(output.data.slice(p * 4, p * 4 + 4)).map(bitsHex)).join(' ')
  console.log(`${fixture[0]}/${fixture[1]}\tfloats=${floats}\trgba=${rgba}\tprobes=${probes}`)
}
