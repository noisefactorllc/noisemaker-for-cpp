// GAP 3c — texture() sampling at a UV derived from a probed, possibly
// off-canvas, quad-corner coordinate. JS side. READ-ONLY consumer of the
// real, unmodified glsl-runtime.js (specifically `runtime.stdlib.texture`,
// i.e. the REAL `#texture` dispatcher used by production kernels, which
// internally flips v for filter==='linear' -- glsl-runtime.js line 198)
// and the real runtime/surface.js Surface class. Structurally parallel to
// gap3c_texture_edge.cpp: identical 7x5 canvas, identical 7x5 texture
// data, identical kernel shape (texture-sample-then-derivative).

import { GlslCpuRuntime, bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'
import { writeFileSync } from 'node:fs'

const WIDTH = 7
const HEIGHT = 5

const data = new Float32Array(WIDTH * HEIGHT * 4)
for (let y = 0; y < HEIGHT; y += 1) {
  for (let x = 0; x < WIDTH; x += 1) {
    const idx = (y * WIDTH + x) * 4
    const linear = y * WIDTH + x
    data[idx + 0] = linear / (WIDTH * HEIGHT)
    data[idx + 1] = x / WIDTH
    data[idx + 2] = y / HEIGHT
    data[idx + 3] = 1
  }
}
const surface = new Surface(WIDTH, HEIGHT, data)
surface.filter = 'linear'  // routes glsl-runtime.js's #texture to sampleBilinear (line 198)

function factory(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const uv = new Float32Array([runtime.varyings.vUv[0], runtime.varyings.vUv[1]])
    const texel = runtime.stdlib.texture(surface, uv)
    const t = texel[0]  // .r

    const gx = runtime.stdlib.dFdx(t)
    const gy = runtime.stdlib.dFdy(t)
    const fw = runtime.stdlib.fwidth(t)

    out[0] = gx
    out[1] = gy
    out[2] = fw
    out[3] = t
  }
  return kernel
}
factory.usesDerivatives = true

const runtime = new GlslCpuRuntime()
const kernel = bindGlslKernel(factory, {})
void runtime

const LANES = 4
const results = new Float32Array(WIDTH * HEIGHT * LANES)
const outN = new Float32Array(LANES)

for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const fragX = col + 0.5
    const fragY = (HEIGHT - row) - 0.5
    const context = {
      fragCoord: new Float32Array([fragX, fragY, 0, 1]),
      uv: new Float32Array([fragX / WIDTH, fragY / HEIGHT]),
      resolution: new Float32Array([WIDTH, HEIGHT]),
      time: 0, seed: 0, frame: 0, deltaTime: 0,
    }
    kernel(context, outN)
    const base = (row * WIDTH + col) * LANES
    for (let i = 0; i < LANES; i += 1) results[base + i] = outN[i]
  }
}

writeFileSync(new URL('./gap3c_texture_edge_reference.f32', import.meta.url), Buffer.from(results.buffer))
let lines = ['row,col,gx,gy,fw,t']
for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const base = (row * WIDTH + col) * LANES
    lines.push(`${row},${col},${results[base + 0]},${results[base + 1]},${results[base + 2]},${results[base + 3]}`)
  }
}
writeFileSync(new URL('./gap3c_texture_edge_reference.csv', import.meta.url), lines.join('\n') + '\n')
console.log(`wrote gap3c_texture_edge_reference.f32 and .csv (WIDTH=${WIDTH} HEIGHT=${HEIGHT})`)
