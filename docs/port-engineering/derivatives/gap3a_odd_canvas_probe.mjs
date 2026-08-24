// GAP 3a — odd-canvas-dimension edge behavior, reference probe. READ-ONLY
// consumer of the real noisemaker-for-cpu JS reference runtime.
// Structurally parallel to gap3a_odd_canvas.cpp: same kernel, WIDTH=7,
// HEIGHT=5 (both odd, so the last quad's x0+1/y0+1 probes genuinely land
// outside [0,WIDTH)x[0,HEIGHT)), same fragCoord.y-flip raster convention.

import { GlslCpuRuntime, bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { writeFileSync } from 'node:fs'

const F32 = Math.fround
const WIDTH = 7
const HEIGHT = 5

function factory(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const uvx = runtime.varyings.vUv[0]
    const uvy = runtime.varyings.vUv[1]
    const uvx2 = F32(uvx * uvx)
    const uvy2 = F32(uvy * uvy)
    const cross = F32(uvx * uvy)
    const term1 = F32(3 * uvx2)
    const term2 = F32(5 * uvy2)
    const term3 = F32(2 * cross)
    const t = F32(F32(term1 + term2) - term3)

    const gx = runtime.stdlib.dFdx(t)
    const gy = runtime.stdlib.dFdy(t)
    const uvVec = new Float32Array([uvx, uvy])
    const fwv = runtime.stdlib.fwidth(uvVec)

    out[0] = gx
    out[1] = gy
    out[2] = fwv[0]
    out[3] = fwv[1]
  }
  return kernel
}
factory.usesDerivatives = true

const runtime = new GlslCpuRuntime()
const kernel = bindGlslKernel(factory, {})
void runtime

const results = new Float32Array(WIDTH * HEIGHT * 4)
const out4 = new Float32Array(4)

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
    kernel(context, out4)
    const base = (row * WIDTH + col) * 4
    results[base + 0] = out4[0]
    results[base + 1] = out4[1]
    results[base + 2] = out4[2]
    results[base + 3] = out4[3]
  }
}

writeFileSync(new URL('./gap3a_odd_canvas_reference.f32', import.meta.url), Buffer.from(results.buffer))
let lines = ['row,col,gx,gy,fwx,fwy']
for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const base = (row * WIDTH + col) * 4
    lines.push(`${row},${col},${results[base + 0]},${results[base + 1]},${results[base + 2]},${results[base + 3]}`)
  }
}
writeFileSync(new URL('./gap3a_odd_canvas_reference.csv', import.meta.url), lines.join('\n') + '\n')
console.log(`wrote gap3a_odd_canvas_reference.f32 and .csv (WIDTH=${WIDTH} HEIGHT=${HEIGHT})`)
