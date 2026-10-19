// Re-derivation script for `typed_task13_all_twenty_one_external_oracles_are_exact_and_repeatable`
// (tests/test_typed_slice.cpp). Mirrors populate_task13_bindings()/render_task13() exactly:
// tileOffset and fullResolution reach the canonical options only for the programs that bind them.
//
// Usage: NOISEMAKER_CPU_ROOT=<authority dir> node task13_oracle_regenerator.mjs

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
const tag23 = source(4, 6, 23)
const tag37 = source(7, 2, 37)
const luma = Surface.fromRgba8(3, 3, new Uint8Array([
  13, 20, 30, 64, 128, 128, 128, 128, 240, 225, 210, 192,
  30, 40, 50, 70, 110, 120, 130, 140, 220, 230, 240, 200,
  7, 8, 9, 30, 160, 150, 140, 160, 250, 245, 235, 220,
]))
const statsRange = constantSurface(1, 1, [30, 200, 71, 255])
const statsFlat = constantSurface(1, 1, [99, 99, 71, 255])
const overlay = constantSurface(4, 6, [238, 53, 181, 179])

// Native float/vec2/int uniforms enter as f32 (fround is a no-op on integers);
// DVec3 uniforms keep their JS doubles.
const f = Math.fround
const dvec3 = (x, y, z) => ({ dvec3: [x, y, z] })

function bindingsFor(key, variant) {
  const uniforms = {}
  const textures = {}
  const tiled = () => { uniforms.tileOffset = [-7.0, 5.0]; uniforms.fullResolution = [17.0, 13.0] }
  if (key === 'filter/bloom:brightPass') {
    tiled()
    textures.inputTex = luma
    uniforms.threshold = variant === 'below' ? 0.98 : variant === 'above' ? 0.01 : 0.5
    uniforms.softKnee = variant === 'softKnee' ? 0.21 : 0.01
  } else if (key === 'filter/bloom:composite') {
    tiled()
    textures.inputTex = tag1; textures.bloomTex = tag23
    uniforms.intensity = variant === 'zeroIntensity' ? 0.0 : 1.7
    uniforms.tint = variant === 'zeroIntensity' ? dvec3(0.7, 0.2, 0.9) : dvec3(0.31, 0.83, 0.52)
  } else if (key === 'filter/fibers:fibersBlend' || key === 'filter/scratches:scratchesBlend') {
    textures.inputTex = tag1; textures.overlayTex = overlay
    uniforms.alpha = variant === 'alpha0' ? 0.0 : variant === 'alpha1' ? 1.0 : 0.53
  } else if (key === 'filter/normalize:apply') {
    tiled()
    textures.inputTex = tag23
    textures.statsTex = variant === 'flat' ? statsFlat : statsRange
  } else if (key === 'filter/pixelSort:luminance') {
    textures.inputTex = variant === 'heterogeneous' ? luma : tag37
  } else if (key === 'filter/reindex:nmReindexApply') {
    tiled()
    uniforms.resolution = [9.0, 7.0]
    textures.inputTex = tag1
    textures.statsTex = variant === 'rangeFlat' ? statsFlat : statsRange
    uniforms.uDisplacement = variant === 'rangePositive' ? 2.7 : variant === 'rangeFlat' ? -1.9 : 0.0
  } else if (key === 'filter/strayHair:strayHairBlend') {
    textures.inputTex = tag1; textures.overlayTex = overlay
    const alternate = variant === 'integerSystemB'
    uniforms.alpha = variant === 'alphaOne' ? 1.0 : 0.47
    uniforms.tileOffset = alternate ? [19, -11] : [-7, 5]
    uniforms.fullResolution = alternate ? [29, 31] : [17, 13]
    uniforms.renderScale = alternate ? 1.91 : variant === 'alphaOne' ? 1.0 : 0.73
  } else {
    throw new Error(`unknown Task 13 key ${key}`)
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
  const options = { width: 9, height: 7, time: 0.375, seed: 7, uniforms: rounded, textures }
  if (rounded.tileOffset) options.tileOffset = new Float32Array(rounded.tileOffset)
  if (rounded.fullResolution) options.fullResolution = new Float32Array(rounded.fullResolution)
  const kernel = bindCanonicalKernel(factory, options)
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
  ...['softKnee', 'below', 'above'].map((v) => ['filter/bloom:brightPass', v]),
  ...['zeroIntensity', 'tintedHDR'].map((v) => ['filter/bloom:composite', v]),
  ...['alpha0', 'alpha0p53', 'alpha1'].map((v) => ['filter/fibers:fibersBlend', v]),
  ...['range', 'flat'].map((v) => ['filter/normalize:apply', v]),
  ...['heterogeneous', 'nonSquareClamp'].map((v) => ['filter/pixelSort:luminance', v]),
  ...['rangePositive', 'rangeFlat', 'zeroDisplacement'].map((v) => ['filter/reindex:nmReindexApply', v]),
  ...['alpha0', 'alpha0p53', 'alpha1'].map((v) => ['filter/scratches:scratchesBlend', v]),
  ...['integerSystemA', 'integerSystemB', 'alphaOne'].map((v) => ['filter/strayHair:strayHairBlend', v]),
]

console.error(`total fixtures: ${FIXTURES.length}`)
for (const [key, variant] of FIXTURES) {
  const surface = render(key, variant)
  const floats = sha256Hex(littleEndianFloatBytes(surface))
  const rgba = sha256Hex(surface.toRgba8())
  const probes = [0, 31, 62].flatMap((p) => Array.from(surface.data.slice(p * 4, p * 4 + 4)).map(bitsHex)).join(' ')
  console.log(`${key}/${variant}\tfloats=${floats}\trgba=${rgba}\tprobes=${probes}`)
}
