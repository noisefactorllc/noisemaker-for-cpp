// GAP 1 — vec3/vec4 derivative reference probe. READ-ONLY consumer of the
// real noisemaker-for-cpu JS reference runtime; structurally parallel to
// gap1_vec34.cpp (same corner constants, same formulas, same operation
// order, same explicit F32() narrowing after every arithmetic op to mirror
// what the typed C++ emitter does with native `float` operations).
//
// See gap1_vec34.cpp's header comment for why CORNER_BOTTOM_LEFT/
// CORNER_BOTTOM_RIGHT/CORNER_TOP_LEFT were chosen: bottomRight-bottomLeft
// and topLeft-bottomLeft are exact-in-double differences that are NOT
// themselves exactly representable in float32, engineered so scalar
// fwidth(t) (single final rounding, glsl-runtime.js lines 461/518-521) and
// vector fwidth(v3).x (component narrowed immediately, lines 524-530)
// disagree by exactly one ULP at pixel (row=7, col=0).

import { GlslCpuRuntime, bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { writeFileSync } from 'node:fs'

const F32 = Math.fround

const WIDTH = 8
const HEIGHT = 8
const LANES = 24

const CORNER_BOTTOM_LEFT = F32(0.0000071775784817873500288)
const CORNER_BOTTOM_RIGHT = F32(3.7392933194269062369e-8)
const CORNER_TOP_LEFT = F32(0.0025053308345377445221)
const CORNER_TOP_RIGHT = F32(0.5)

const TABLE_X = [0, 0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5].map(F32)
const TABLE_Y = [0, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6].map(F32)

function factory(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const col = Math.floor(context.fragCoord[0] - 0.5)
    const row = Math.floor(context.fragCoord[1] - 0.5)
    const uvx = runtime.varyings.vUv[0]
    const uvy = runtime.varyings.vUv[1]

    let t
    if (col === 0 && row === 0) t = CORNER_BOTTOM_LEFT
    else if (col === 1 && row === 0) t = CORNER_BOTTOM_RIGHT
    else if (col === 0 && row === 1) t = CORNER_TOP_LEFT
    else if (col === 1 && row === 1) t = CORNER_TOP_RIGHT
    else t = F32(TABLE_X[col] + TABLE_Y[row])

    const mul1 = F32(3 * uvx)
    const mul2 = F32(mul1 * uvx)
    const mul3 = F32(2 * uvy)
    const v3y = F32(mul2 - mul3)

    const mul4 = F32(4 * uvy)
    const mul5 = F32(mul4 * uvy)
    const v3z = F32(uvx + mul5)

    const mul6 = F32(uvx * uvy)
    const v4w = F32(mul6 * 2)

    const v3 = new Float32Array([t, v3y, v3z])
    const v4 = new Float32Array([t, v3y, v3z, v4w])

    const gxT = runtime.stdlib.dFdx(t)
    const gyT = runtime.stdlib.dFdy(t)
    const fwT = runtime.stdlib.fwidth(t)

    const gxV3 = runtime.stdlib.dFdx(v3)
    const gyV3 = runtime.stdlib.dFdy(v3)
    const fwV3 = runtime.stdlib.fwidth(v3)

    const gxV4 = runtime.stdlib.dFdx(v4)
    const gyV4 = runtime.stdlib.dFdy(v4)
    const fwV4 = runtime.stdlib.fwidth(v4)

    out[0] = gxT; out[1] = gyT; out[2] = fwT
    out[3] = gxV3[0]; out[4] = gxV3[1]; out[5] = gxV3[2]
    out[6] = gyV3[0]; out[7] = gyV3[1]; out[8] = gyV3[2]
    out[9] = fwV3[0]; out[10] = fwV3[1]; out[11] = fwV3[2]
    out[12] = gxV4[0]; out[13] = gxV4[1]; out[14] = gxV4[2]; out[15] = gxV4[3]
    out[16] = gyV4[0]; out[17] = gyV4[1]; out[18] = gyV4[2]; out[19] = gyV4[3]
    out[20] = fwV4[0]; out[21] = fwV4[1]; out[22] = fwV4[2]; out[23] = fwV4[3]
  }
  return kernel
}
factory.usesDerivatives = true

const runtime = new GlslCpuRuntime()
const kernel = bindGlslKernel(factory, {})
void runtime

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
      time: 0,
      seed: 0,
      frame: 0,
      deltaTime: 0,
    }
    kernel(context, outN)
    const base = (row * WIDTH + col) * LANES
    for (let i = 0; i < LANES; i += 1) results[base + i] = outN[i]
  }
}

writeFileSync(new URL('./gap1_vec34_reference.f32', import.meta.url), Buffer.from(results.buffer))

const names = ['gx_t', 'gy_t', 'fw_t',
  'gx_v3.x', 'gx_v3.y', 'gx_v3.z', 'gy_v3.x', 'gy_v3.y', 'gy_v3.z', 'fw_v3.x', 'fw_v3.y', 'fw_v3.z',
  'gx_v4.x', 'gx_v4.y', 'gx_v4.z', 'gx_v4.w', 'gy_v4.x', 'gy_v4.y', 'gy_v4.z', 'gy_v4.w',
  'fw_v4.x', 'fw_v4.y', 'fw_v4.z', 'fw_v4.w']
let lines = ['row,col,' + names.join(',')]
for (let row = 0; row < HEIGHT; row += 1) {
  for (let col = 0; col < WIDTH; col += 1) {
    const base = (row * WIDTH + col) * LANES
    const vals = []
    for (let i = 0; i < LANES; i += 1) vals.push(results[base + i])
    lines.push(`${row},${col},${vals.join(',')}`)
  }
}
writeFileSync(new URL('./gap1_vec34_reference.csv', import.meta.url), lines.join('\n') + '\n')

const targetBase = (7 * WIDTH + 0) * LANES
console.log('target pixel (row=7,col=0): fw_t=', results[targetBase + 2], ' fw_v3.x=', results[targetBase + 9], ' (expect these to DIFFER by 1 ULP)')
console.log('wrote gap1_vec34_reference.f32 and gap1_vec34_reference.csv')
