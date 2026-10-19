// Authority reference for seven tests/test_typed_slice.cpp runtime tests whose captures had no
// checked-in script: typed_hydraulic_preserves_authority_signed_number_hash, the three
// typed_noise3d_* MRT tests, typed_flythrough3d_preserves_authority_mrt_outputs,
// typed_landscape_matches_authority_volume_mrt and typed_halftone_runtime_modes_preserve_cpu_color_arity.
// Each block mirrors its native test's bindings; MRT passes run through the authority's own
// CpuRenderer.runCanonicalMrtPass pixel loop. Native halftone color-alpha carriers are the
// authority's four-component color parameters.
//
// Usage: node tests/fixtures/typed_slice_runtime_reference.mjs --cpu-root ROOT --ledger FILE
import assert from 'node:assert/strict'
import crypto from 'node:crypto'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { authenticateCpuRoot } from '../../tools/dsl/corpus_authority.mjs'
const rootArg = process.argv.indexOf('--cpu-root')
const ledgerArg = process.argv.indexOf('--ledger')
assert.ok(rootArg > 0 && ledgerArg > 0, 'pass --cpu-root ROOT --ledger FILE')
const root = authenticateCpuRoot(process.argv[rootArg + 1], process.argv[ledgerArg + 1])
const load = (relative) => import(pathToFileURL(path.join(root, relative)).href)
const { canonicalKernelFactories } = await load('src/effects/catalog.js')
const { bindCanonicalKernel } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
const { CpuRenderer } = await load('src/runtime/renderer.js')
const f = Math.fround
const sha = (b) => crypto.createHash('sha256').update(b).digest('hex')
const bytes = (a) => Buffer.from(a.buffer, a.byteOffset, a.byteLength)
const hashes = (s) => [sha(bytes(s.data)), sha(Buffer.from(s.toRgba8()))]
function constant(width, height, rgba) {
  const s = new Surface(width, height)
  for (let i = 0; i < width * height; i += 1) s.data.set(rgba.map(f), i * 4)
  return s
}
function mrt(key, width, height, outputs, options, time = 0, seed = 1) {
  const kernel = bindCanonicalKernel(canonicalKernelFactories[key], { width, height, ...options })
  const destinations = Array.from({ length: outputs }, () => new Surface(width, height))
  CpuRenderer.prototype.runCanonicalMrtPass.call(null, { kernel, destinations, time, seed })
  return destinations
}
const result = {}

// typed_hydraulic_preserves_authority_signed_number_hash
{
  const textures = {
    inputTex: constant(17, 11, [0.2, 0.3, 0.4, 1]), xyzTex: constant(17, 11, [0.25, 0.75, 0, 1]),
    velTex: constant(17, 11, [0.05, 0.025, 0, 0]), rgbaTex: constant(17, 11, [0.2, 0.4, 0.6, 1]),
  }
  const uniforms = { resolution: new Float32Array([17, 11]), time: 0.25, stride: 10, quantize: 0, inverse: 0, inputWeight: 100 }
  result.hydraulic = mrt('points/hydraulic:agent', 17, 11, 3, { time: 0.25, uniforms, textures }, f(0.25)).map(hashes)
}

function noise3d(volume, seed, scale, time, octaves = 1, colorMode = 0, ridges = false) {
  const width = volume, height = volume * volume
  const uniforms = {
    tileOffset: new Float32Array([0, 0]), fullResolution: new Float32Array([width, height]),
    time, scale, seed, volumeSize: volume, speed: 1, OCTAVES: octaves, COLOR_MODE: colorMode, RIDGES: ridges,
  }
  return mrt('synth3d/noise3d:precompute', width, height, 2,
    { time, tileOffset: uniforms.tileOffset, fullResolution: uniforms.fullResolution, uniforms }, f(time)).map(hashes)
}
// typed_noise3d_preserves_authority_hash4_number_rounding
result.noise3d_hash4 = [[2, 0, 1.3, 0.25], [2, 42, 1.3, 0.25], [3, 42, 2.7, 0.375]].flatMap(([v, s, sc, t]) => noise3d(v, s, sc, t))
// typed_noise3d_large_seed_number_and_int32_wrap_match_cpu
result.noise3d_large_seed = [
  [3, 0.0, 2.7, 0.375], [3, 31576719.0, 2.7, 0.375], [3, 1512140165.0, 2.7, 0.375], [3, 2687862216.0, 2.7, 0.375],
  [3, 4294967295.0, 2.7, 0.375], [3, 2147483647.0, 2.7, 0.375], [3, 2147483648.0, 2.7, 0.375], [16, 1512140165.0, 3, 0.25],
].map(([v, s, sc, t]) => noise3d(v, s, sc, t))
// typed_noise3d_runtime_defines_match_authority_mrt
result.noise3d_defines = []
for (const octaves of [1, 3, 6]) for (const colorMode of [0, 1]) for (const ridges of [false, true]) {
  const out = noise3d(3, 42.0, 2.7, 0.375, octaves, colorMode, ridges)
  result.noise3d_defines.push({ octaves, colorMode, ridges, color: out[0][0], geo: out[1][0] })
}

// typed_flythrough3d_preserves_authority_mrt_outputs
result.flythrough = [[0, 3], [1, 11]].flatMap(([noiseType, seed]) => {
  const uniforms = {
    tileOffset: new Float32Array([0, 0]), fullResolution: new Float32Array([16, 256]), time: 0.375,
    volumeSize: 16, noiseType, power: 8, iterations: 12, bailout: 4, speed: 0.2, voiSize: 0.5, seed,
  }
  return mrt('synth3d/flythrough3d:precompute', 16, 256, 2,
    { time: 0.375, tileOffset: uniforms.tileOffset, fullResolution: uniforms.fullResolution, uniforms }, f(0.375)).map(hashes)
})

// typed_landscape_matches_authority_volume_mrt
{
  const side = 4
  const volumeCache = new Surface(side, side * side), analyticalGeo = new Surface(side, side * side)
  for (let z = 0; z < side; z += 1) for (let y = 0; y < side; y += 1) for (let x = 0; x < side; x += 1) {
    const o = ((z * side + y) * side + x) * 4
    for (const s of [volumeCache, analyticalGeo]) { s.data[o] = f((x + 1) / 5); s.data[o + 1] = f((y + 1) / 5); s.data[o + 2] = f((z + 1) / 5) }
    volumeCache.data[o + 3] = 1
    analyticalGeo.data[o + 3] = (x + y + z) >= 4 ? f(0.8) : f(0.1)
  }
  result.landscape = []
  for (const [viewMode, filtering] of [[1, 0], [1, 1], [2, 0], [2, 1]]) {
    const uniforms = {
      FILTERING: filtering, VIEW_MODE: viewMode, resolution: new Float32Array([7, 5]),
      fullResolution: new Float32Array([7, 5]), tileOffset: new Float32Array([0, 0]), volumeSize: side,
      threshold: 0.4, zoom: 1, panX: 0.05, panY: -0.03, lightDirection: [f(-0.4), f(0.85), f(0.6)],
      ambient: 0.35, diffuseIntensity: 0.85, specularIntensity: 0.12, bgColor: [f(0.025), f(0.045), f(0.075)],
      bgAlpha: 1, rotateX: 0.3, rotateY: 0.2, rotateZ: 0.1, viewScale: 0.8, posX: 0, posY: 0, posZ: 0, fieldOfView: 60,
    }
    const out = mrt('render/renderLandscape3d:landscape', 7, 5, 2,
      { tileOffset: uniforms.tileOffset, fullResolution: uniforms.fullResolution, uniforms,
        textures: { volumeCache, analyticalGeo } })
    result.landscape.push({ viewMode, filtering, frag: out.map(hashes)[0][0], geo: out.map(hashes)[1][0] })
  }
}

// typed_halftone_runtime_modes_preserve_cpu_color_arity
{
  const input = new Surface(8, 8)
  for (let i = 0; i < 64; i += 1) {
    input.data[4 * i] = (i % 7 + 1) / 9; input.data[4 * i + 1] = (i % 11 + 1) / 13
    input.data[4 * i + 2] = (i % 13 + 1) / 15; input.data[4 * i + 3] = (i % 5 + 1) / 7
  }
  result.halftone = []
  for (const [inkAlpha, paperAlpha] of [[false, false], [false, true], [true, false], [true, true]]) {
    const row = { inkAlpha, paperAlpha, f32: [], rgba: [] }
    for (const [mode, pattern] of [[0, 0], [1, 0], [1, 1], [1, 2]]) {
      const uniforms = {
        MODE: mode, PATTERN: pattern, resolution: new Float32Array([8, 8]), tileOffset: new Float32Array([0, 0]),
        fullResolution: new Float32Array([8, 8]), frequency: 6, cyanAngle: 108, magentaAngle: 162, yellowAngle: 90,
        blackAngle: 45, monoAngle: 45, sharpness: 80,
        inkColor: inkAlpha ? [0.1, 0.2, 0.3, 0.25] : [0.1, 0.2, 0.3],
        paperColor: paperAlpha ? [0.8, 0.7, 0.6, 0.75] : [0.8, 0.7, 0.6],
      }
      const kernel = bindCanonicalKernel(canonicalKernelFactories['filter/halftone:halftone'],
        { width: 8, height: 8, tileOffset: uniforms.tileOffset, fullResolution: uniforms.fullResolution, uniforms, textures: { inputTex: input } })
      const destination = new Surface(8, 8)
      runPass({ kernel, destination })
      const [a, b] = hashes(destination)
      row.f32.push(a); row.rgba.push(b)
    }
    result.halftone.push(row)
  }
}
process.stdout.write(JSON.stringify(result, null, 1) + '\n')
