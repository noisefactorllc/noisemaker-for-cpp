// GAP 2 — multi-call-site ordinal interleaving reference probe. READ-ONLY
// consumer of the real noisemaker-for-cpu JS reference runtime.
// Structurally parallel to gap2_multisite.cpp: same two kernels (A =
// interleaved mixed-kind/mixed-width call sites incl. a helper called
// twice; B = branchy, exercising the missing-ordinal fallback), same
// formulas, same F32() narrowing after every arithmetic op.

import { GlslCpuRuntime, bindGlslKernel } from '../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { writeFileSync } from 'node:fs'

const F32 = Math.fround
const WIDTH = 8
const HEIGHT = 8

function runGrid(factory, lanes, names, binName, csvName) {
  const runtime = new GlslCpuRuntime()
  const kernel = bindGlslKernel(factory, {})
  void runtime
  const results = new Float32Array(WIDTH * HEIGHT * lanes)
  const outN = new Float32Array(lanes)
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
      outN.fill(0)
      kernel(context, outN)
      const base = (row * WIDTH + col) * lanes
      for (let i = 0; i < lanes; i += 1) results[base + i] = outN[i]
    }
  }
  writeFileSync(new URL(`./${binName}`, import.meta.url), Buffer.from(results.buffer))
  let lines = ['row,col,' + names.join(',')]
  for (let row = 0; row < HEIGHT; row += 1) {
    for (let col = 0; col < WIDTH; col += 1) {
      const base = (row * WIDTH + col) * lanes
      const vals = []
      for (let i = 0; i < lanes; i += 1) vals.push(results[base + i])
      lines.push(`${row},${col},${vals.join(',')}`)
    }
  }
  writeFileSync(new URL(`./${csvName}`, import.meta.url), lines.join('\n') + '\n')
  console.log(`wrote ${binName} and ${csvName}`)
}

// ---------------------------------------------------------------------
// Kernel A: interleaved multi-call-site kernel.
// ---------------------------------------------------------------------
function helperScalar(runtime, x) {
  const s = F32((x * x) + 0.5)
  return runtime.stdlib.dFdx(s)
}

function factoryA(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const uvx = runtime.varyings.vUv[0]
    const uvy = runtime.varyings.vUv[1]

    const t1 = F32(F32(3 * uvx) - uvy)
    const a = runtime.stdlib.dFdx(t1)  // ordinal 0: scalar

    const v3 = new Float32Array([F32(uvx + uvy), F32(uvx * uvy), F32(uvx - uvy)])
    const b = runtime.stdlib.fwidth(v3)  // ordinal 1: vec3

    const v2 = new Float32Array([F32(uvx * 2), F32(uvy * 3)])
    const c = runtime.stdlib.dFdy(v2)  // ordinal 2: vec2

    const d1 = helperScalar(runtime, uvx)  // ordinal 3: scalar, helper 1st call

    const t2 = F32(F32(uvx * uvx) + F32(uvy * uvy))
    const e = runtime.stdlib.fwidth(t2)  // ordinal 4: scalar

    const d2 = helperScalar(runtime, uvy)  // ordinal 5: scalar, helper 2nd call

    out[0] = a
    out[1] = b[0]; out[2] = b[1]; out[3] = b[2]
    out[4] = c[0]; out[5] = c[1]
    out[6] = d1
    out[7] = e
    out[8] = d2
  }
  return kernel
}
factoryA.usesDerivatives = true

// ---------------------------------------------------------------------
// Kernel B: branchy kernel, missing-ordinal fallback stress case.
// ---------------------------------------------------------------------
function factoryB(bindings, runtime) {
  const kernel = (context, out) => {
    runtime.beginPixel(context)
    const uvx = runtime.varyings.vUv[0]
    const uvy = runtime.varyings.vUv[1]

    const t1 = F32(F32(2 * uvx) - uvy)
    const s1 = runtime.stdlib.dFdx(t1)  // ordinal 0: always

    const t2 = F32(uvx + F32(2 * uvy))
    const s2 = runtime.stdlib.fwidth(t2)  // ordinal 1: always

    let s3 = 0.0
    if (uvy < 0.6) {
      const t3 = F32(F32(uvx * uvx) + uvy)
      s3 = runtime.stdlib.dFdy(t3)  // ordinal 2: conditional on uv.y
    }

    out[0] = s1
    out[1] = s2
    out[2] = s3
  }
  return kernel
}
factoryB.usesDerivatives = true

runGrid(factoryA, 9, ['a', 'b.x', 'b.y', 'b.z', 'c.x', 'c.y', 'd1', 'e', 'd2'],
  'gap2a_interleaved_reference.f32', 'gap2a_interleaved_reference.csv')
runGrid(factoryB, 3, ['s1', 's2', 's3'],
  'gap2b_branchy_reference.f32', 'gap2b_branchy_reference.csv')

// Diagnostic: independently probe the same quad C++'s diagnostic block
// inspects (quadX=0, quadY=2: bottom corner (0,4), top corner (0,5)) to
// confirm the JS reference ALSO has divergent per-corner record counts
// there, using the runtime's own record-mode machinery directly (mirrors
// what wrapDerivatives does internally, without touching glsl-runtime.js).
{
  const runtime2 = new GlslCpuRuntime()
  const kernel2 = factoryB({}, runtime2)
  const probeOnce = (x, y) => {
    const context = {
      fragCoord: new Float32Array([x, y]),
      uv: new Float32Array([x / WIDTH, y / HEIGHT]),
      resolution: new Float32Array([WIDTH, HEIGHT]),
      time: 0, seed: 0, frame: 0, deltaTime: 0,
    }
    runtime2.derivativeMode = 'record'
    runtime2.derivativeRecords = []
    const temp = new Float32Array(4)
    kernel2(context, temp)
    return runtime2.derivativeRecords
  }
  const bottom = probeOnce(0.5, 4.5)
  const top = probeOnce(0.5, 5.5)
  console.log(`gap2b JS diagnostic: bottom corner (0,4) record_count=${bottom.length} top corner (0,5) record_count=${top.length}`)
  console.log(`gap2b JS diagnostic: bottom ordinal-2 recorded value=${bottom[2]}`)
}
