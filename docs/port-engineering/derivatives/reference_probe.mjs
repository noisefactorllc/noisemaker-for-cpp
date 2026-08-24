// Prototype verification harness — READ-ONLY consumer of the real
// noisemaker-for-cpu JS reference runtime. Does not modify anything under
// ../noisemaker-for-cpu.
//
// Builds a hand-written kernel that exercises dFdx (scalar), dFdy (scalar),
// and fwidth (vector, on uv) through the REAL GlslCpuRuntime derivative
// machinery (bindGlslKernel -> wrapDerivatives -> #derivative), runs it over
// an 8x8 grid using the exact fragCoord convention the C++ pass_runner.cpp
// uses (fragCoord.y = height - row - 0.5, i.e. row 0 is the top of the
// image and has the LARGEST fragCoord.y), and dumps raw float32 output.
//
// Kernel under test, in GLSL-ish pseudocode:
//   float t = 3.0*uv.x*uv.x + 5.0*uv.y*uv.y - 2.0*uv.x*uv.y;
//   float gx = dFdx(t);
//   float gy = dFdy(t);
//   vec2  fwv = fwidth(uv);
//   out = vec4(gx, gy, fwv.x, fwv.y);

import { GlslCpuRuntime, bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { writeFileSync } from 'node:fs'

const F32 = Math.fround

const WIDTH = 8
const HEIGHT = 8

function factory(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const uvx = runtime.varyings.vUv[0]
    const uvy = runtime.varyings.vUv[1]
    // t = 3*uvx^2 + 5*uvy^2 - 2*uvx*uvy, narrowed to f32 at every step to
    // mirror what the typed C++ emitter does (every intermediate is a
    // noisemaker::f32-narrowed float, no double-precision accumulation).
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
void runtime // constructed only to keep parity with how bindGlslKernel is normally invoked

const results = new Float32Array(WIDTH * HEIGHT * 4)
const out4 = new Float32Array(4)

for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const fragX = col + 0.5
    const fragY = (HEIGHT - row) - 0.5 // matches pass_runner.cpp's y-flip convention
    const context = {
      fragCoord: new Float32Array([fragX, fragY, 0, 1]),
      uv: new Float32Array([fragX / WIDTH, fragY / HEIGHT]),
      resolution: new Float32Array([WIDTH, HEIGHT]),
      time: 0,
      seed: 0,
      frame: 0,
      deltaTime: 0,
    }
    kernel(context, out4)
    const base = (row * WIDTH + col) * 4
    results[base + 0] = out4[0]
    results[base + 1] = out4[1]
    results[base + 2] = out4[2]
    results[base + 3] = out4[3]
  }
}

writeFileSync(new URL('./reference_output.f32', import.meta.url), Buffer.from(results.buffer))

// Also dump a human-readable table for the report.
let lines = ['row,col,gx(dFdx t),gy(dFdy t),fwidth(uv).x,fwidth(uv).y']
for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const base = (row * WIDTH + col) * 4
    lines.push(`${row},${col},${results[base + 0]},${results[base + 1]},${results[base + 2]},${results[base + 3]}`)
  }
}
writeFileSync(new URL('./reference_output.csv', import.meta.url), lines.join('\n') + '\n')

console.log('wrote reference_output.f32 and reference_output.csv')
console.log('expected constants: fwidth(uv).x =', F32(1 / WIDTH), ' fwidth(uv).y =', F32(1 / HEIGHT))
