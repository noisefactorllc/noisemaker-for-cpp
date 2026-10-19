// Re-derivation script for `typed_task12_all_one_hundred_twenty_external_oracles_are_exact_and_repeatable`
// (tests/test_typed_slice.cpp). Mirrors populate_task12_bindings()/render_task12() exactly.
// The filter/hs:hs, classicNoisedeck/coalesce:coalesce and filter/scale:scale rows render
// through historical kernels in the native test and keep their historical captures; this
// script skips them (filter/hs is no longer in the authority catalog).
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task12_oracle_regenerator.mjs

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

function constantSurface(width, height, rgba) {
  const bytes = new Uint8Array(width * height * 4)
  for (let i = 0; i < width * height; i += 1) bytes.set(rgba, i * 4)
  return Surface.fromRgba8(width, height, bytes)
}

const tag1 = source(5, 3, 1)
const tag23 = source(7, 2, 23)
const tag37 = source(4, 6, 37)
const constantA = constantSurface(5, 3, [51, 153, 26, 102])
const constantB = constantSurface(7, 2, [230, 77, 179, 204])
const hueNegative = constantSurface(3, 2, [230, 10, 180, 177])

// task12_number(): leading decimal digits after `prefix`, else `fallback`.
function number(value, prefix, fallback = 0) {
  if (!value.startsWith(prefix)) return fallback
  let result = 0
  let found = false
  for (const character of value.slice(prefix.length)) {
    if (character < '0' || character > '9') break
    found = true
    result = result * 10 + (character.charCodeAt(0) - 48)
  }
  return found ? result : fallback
}

// Native float/vec2/int uniforms enter as f32 (fround is a no-op on integers);
// DVec3 uniforms keep their JS doubles.
const f = Math.fround
const dvec3 = (x, y, z) => ({ dvec3: [x, y, z] })

function bindingsFor(key, variant) {
  const fullResolutionFallback = variant === 'fullResolutionFallback'
  const uniforms = {
    resolution: [9.0, 7.0],
    tileOffset: [-5.0, 3.0],
    fullResolution: fullResolutionFallback ? [0.0, 0.0] : [17.0, 13.0],
    time: 0.375,
  }
  const textures = {}
  if (key === 'classicNoisedeck/coalesce:coalesce') {
    textures.inputTex = tag1; textures.tex = tag23
    let mode = number(variant, 'blend')
    if (variant.startsWith('hsv')) mode = number(variant, 'hsv')
    else if (variant === 'cloak100') mode = 100
    else if (variant === 'factorHalf' || variant === 'factorLow') mode = 10
    else if (variant === 'alphaNegative') mode = 1
    uniforms.blendMode = mode
    uniforms.mixAmt = variant === 'factorHalf' ? 0.5 : variant === 'factorLow' ? 0.25 : variant === 'alphaNegative' ? -37.0 : 50.0
    uniforms.refractAAmt = 43.0; uniforms.refractBAmt = 61.0
    uniforms.refractADir = -137.0; uniforms.refractBDir = 211.0
  } else if (key === 'classicNoisedeck/composite:composite') {
    textures.inputTex = constantA; textures.tex = constantB
    uniforms.blendMode = number(variant, 'mode'); uniforms.range = 1.0; uniforms.mixAmt = 63.0
    if (variant.endsWith('Far')) uniforms.inputColor = dvec3(0.0, 0.0, 0.0)
    else if (variant === 'mode2Near') uniforms.inputColor = dvec3(230.0 / 255.0, 77.0 / 255.0, 179.0 / 255.0)
    else uniforms.inputColor = dvec3(0.2, 0.6, 26.0 / 255.0)
  } else if (key === 'filter/hs:hs') {
    textures.inputTex = hueNegative
    uniforms.rotation = number(variant, 'sector')
    uniforms.hueRange = 100.0; uniforms.saturation = 73.0
  } else if (key === 'filter/repeat:repeat') {
    textures.inputTex = tag37; uniforms.aspect = 9.0 / 7.0
    uniforms.x = -2.7; uniforms.y = 3.4; uniforms.offsetX = -0.83; uniforms.offsetY = 0.67
    uniforms.wrap = number(variant, 'wrap')
  } else if (key === 'filter/scale:scale') {
    textures.inputTex = tag37; uniforms.aspect = 9.0 / 7.0
    uniforms.scaleX = -1.7; uniforms.scaleY = 2.3; uniforms.centerX = 0.73; uniforms.centerY = -0.61
    uniforms.wrap = number(variant, 'wrap')
  } else if (key === 'filter/scroll:scroll') {
    textures.inputTex = tag37; uniforms.aspect = 9.0 / 7.0
    uniforms.x = -0.81; uniforms.y = 0.66; uniforms.speedX = 1.7; uniforms.speedY = -2.2
    uniforms.wrap = number(variant, 'wrap')
  } else if (key === 'filter/translate:translate') {
    textures.inputTex = tag37; uniforms.x = -0.91; uniforms.y = 0.78
    uniforms.wrap = number(variant, 'wrap')
  } else if (key === 'mixer/patternMix:patternMix') {
    textures.inputTex = tag1; textures.tex = tag23
    uniforms.patternType = variant === 'fallback' ? 99 : variant === 'fullResolutionFallback' ? 4 : number(variant, 'pattern')
    uniforms.scale = 5.7; uniforms.thickness = 0.58
    uniforms.smoothness = 0.047; uniforms.rotation = 31.0
    uniforms.invert = variant === 'invert' ? 1 : 0
  } else if (key === 'mixer/shapeMask:shapeMask') {
    textures.inputTex = tag1; textures.tex = tag23
    uniforms.shape = variant === 'fallback' ? 99
      : (variant === 'invert' || variant === 'animated' || variant === 'fullResolutionFallback') ? 5
        : number(variant, 'shape')
    uniforms.radius = 0.57; uniforms.edgeSmooth = 0.083
    uniforms.rotation = 27.0; uniforms.posX = -0.23; uniforms.posY = 0.19
    uniforms.invert = variant === 'invert' ? 1 : 0
    uniforms.speed = variant === 'animated' ? 2 : 0
  } else if (key === 'mixer/split:split') {
    textures.inputTex = tag1; textures.tex = tag23
    uniforms.position = -0.17; uniforms.rotation = 38.0; uniforms.softness = 0.12
    uniforms.invert = variant === 'invertOdd' ? 1 : 0
    uniforms.speed = variant === 'animatedEven' ? 0.5 : (variant === 'animatedOdd' || variant === 'invertOdd') ? 2.0 : 0.0
  } else if (key === 'mixer/uvRemap:uvRemap') {
    textures.inputTex = tag1; textures.tex = tag23
    const fallback = variant === 'fallbacks'
    uniforms.mapSource = fallback ? 9 : number(variant, 'map')
    uniforms.channel = fallback ? 9 : number(variant.slice(variant.indexOf('channel')), 'channel')
    uniforms.scale = 260.0
    uniforms.offset = -1.23
    uniforms.wrap = fallback ? 9 : number(variant.slice(variant.indexOf('wrap')), 'wrap')
  } else if (key === 'synth/modPattern:modPattern') {
    let shape1 = 0; let shape2 = 1; let shape3 = 2; let blend = 0; let anim = 0
    if (variant === 'blend1Anim1') { shape1 = 1; shape2 = 2; shape3 = 0; blend = 1; anim = 1 }
    else if (variant === 'blend2Anim2') { shape1 = 2; shape2 = 0; shape3 = 1; blend = 2; anim = 2 }
    else if (variant === 'blend3') { shape1 = -1; blend = 3 }
    uniforms.shape1 = shape1; uniforms.scale1 = 5.3; uniforms.repeat1 = 3.7
    uniforms.shape2 = shape2; uniforms.scale2 = 4.6; uniforms.repeat2 = 5.1
    uniforms.shape3 = shape3; uniforms.scale3 = 3.2; uniforms.repeat3 = 6.3
    uniforms.blend = blend; uniforms.smoothing = 12.0; uniforms.speed = 3.7; uniforms.animMode = anim
  } else if (key === 'synth/pattern:pattern') {
    const pattern = variant === 'fallback' ? 99 : number(variant, 'pattern')
    uniforms.aspect = 17.0 / 13.0; uniforms.patternType = pattern; uniforms.scale = 5.4
    uniforms.thickness = 0.57; uniforms.smoothness = 0.046; uniforms.rotation = 29.0
    uniforms.skew = -0.31; uniforms.animation = pattern === 0 ? 2 : pattern === 2 ? 1 : 0
    uniforms.speed = 3.6; uniforms.fgColor = dvec3(0.91, 0.17, 0.63)
    uniforms.bgColor = dvec3(0.08, 0.72, 0.34)
  } else {
    throw new Error(`unknown Task 12 key ${key}`)
  }
  return { uniforms, textures }
}

function render(key, variant) {
  const { uniforms, textures } = bindingsFor(key, variant)
  const rounded = {}
  for (const [name, value] of Object.entries(uniforms)) {
    if (value && value.dvec3) rounded[name] = value.dvec3
    else if (Array.isArray(value)) rounded[name] = value.map(f)
    else rounded[name] = f(value)
  }
  const factory = canonicalKernelFactories[key]
  if (!factory) throw new Error(`no canonical kernel factory for ${key}`)
  const kernel = bindCanonicalKernel(factory, {
    width: 9,
    height: 7,
    time: 0.375,
    seed: 7,
    tileOffset: new Float32Array(rounded.tileOffset),
    fullResolution: new Float32Array(rounded.fullResolution),
    uniforms: rounded,
    textures,
  })
  const destination = new Surface(9, 7)
  runPass({ kernel, destination })
  return destination
}

function littleEndianFloatBytes(surface) {
  const bytes = new Uint8Array(surface.data.length * 4)
  const view = new DataView(bytes.buffer)
  for (let i = 0; i < surface.data.length; i += 1) view.setFloat32(i * 4, surface.data[i], true)
  return bytes
}

const sha256Hex = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex')

function bitsHex(value) {
  const view = new DataView(new ArrayBuffer(4))
  view.setFloat32(0, value, true)
  return view.getUint32(0, true).toString(16).padStart(8, '0')
}

const FIXTURES = [
  ...Array.from({ length: 19 }, (_, i) => ['classicNoisedeck/coalesce:coalesce', `blend${i}`]),
  ...Array.from({ length: 6 }, (_, i) => ['classicNoisedeck/coalesce:coalesce', `hsv${1000 + i}`]),
  ...['cloak100', 'factorHalf', 'factorLow', 'alphaNegative'].map((v) => ['classicNoisedeck/coalesce:coalesce', v]),
  ...Array.from({ length: 16 }, (_, i) => ['classicNoisedeck/composite:composite', `mode${i}`]),
  ...['mode0Far', 'mode1Far', 'mode2Near', 'mode2Far'].map((v) => ['classicNoisedeck/composite:composite', v]),
  ...[0, 60, 120, 180, 240, 300].map((v) => ['filter/hs:hs', `sector${v}`]),
  ...['filter/repeat:repeat', 'filter/scale:scale', 'filter/scroll:scroll', 'filter/translate:translate']
    .flatMap((key) => [0, 1, 2].map((wrap) => [key, `wrap${wrap}`])),
  ...Array.from({ length: 9 }, (_, i) => ['mixer/patternMix:patternMix', `pattern${i}`]),
  ...['invert', 'fallback', 'fullResolutionFallback'].map((v) => ['mixer/patternMix:patternMix', v]),
  ...Array.from({ length: 8 }, (_, i) => ['mixer/shapeMask:shapeMask', `shape${i}`]),
  ...['invert', 'animated', 'fallback', 'fullResolutionFallback'].map((v) => ['mixer/shapeMask:shapeMask', v]),
  ...['static', 'animatedEven', 'animatedOdd', 'invertOdd', 'fullResolutionFallback'].map((v) => ['mixer/split:split', v]),
  ...['map0_channel0_wrap0', 'map0_channel1_wrap1', 'map0_channel2_wrap2',
    'map1_channel0_wrap0', 'map1_channel1_wrap1', 'map1_channel2_wrap2', 'fallbacks'].map((v) => ['mixer/uvRemap:uvRemap', v]),
  ...['blend0Anim0', 'blend1Anim1', 'blend2Anim2', 'blend3'].map((v) => ['synth/modPattern:modPattern', v]),
  ...Array.from({ length: 12 }, (_, i) => ['synth/pattern:pattern', `pattern${i}`]),
  ['synth/pattern:pattern', 'fallback'],
]

const HISTORICAL = new Set(['filter/hs:hs', 'classicNoisedeck/coalesce:coalesce', 'filter/scale:scale'])

console.error(`total fixtures: ${FIXTURES.length}; historical rows skipped: ${FIXTURES.filter(([key]) => HISTORICAL.has(key)).length}`)
for (const [key, variant] of FIXTURES) {
  if (HISTORICAL.has(key)) continue
  const surface = render(key, variant)
  const floats = sha256Hex(littleEndianFloatBytes(surface))
  const rgba = sha256Hex(surface.toRgba8())
  const probes = [0, 31, 62].flatMap((p) => Array.from(surface.data.slice(p * 4, p * 4 + 4)).map(bitsHex)).join(' ')
  console.log(`${key}/${variant}\tfloats=${floats}\trgba=${rgba}\tprobes=${probes}`)
}
