import assert from 'node:assert/strict'
import crypto from 'node:crypto'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { authenticateCpuRoot, EXPECTED } from '../../tools/dsl/corpus_authority.mjs'

const rootArg = process.argv.indexOf('--cpu-root')
const ledgerArg = process.argv.indexOf('--ledger')
assert.ok(rootArg > 0 && ledgerArg > 0, 'pass --cpu-root ROOT --ledger FILE')
const root = authenticateCpuRoot(process.argv[rootArg + 1], process.argv[ledgerArg + 1])
const load = relative => import(pathToFileURL(path.join(root, relative)).href)
const { canonicalKernelFactories, kernelFactories } = await load('src/effects/catalog.js')
const { bindCanonicalKernel } = await load('src/csl/glsl-kernel.js')
const { Surface } = await load('src/runtime/surface.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const hash = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = data => Buffer.from(data.buffer, data.byteOffset, data.byteLength)
const key = 'filter/hatch:hatch'
const factory = canonicalKernelFactories[key]
assert.equal(kernelFactories.get(key), factory)
const cases = []
for (const [width, height] of [[7, 5], [11, 3]]) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i++) data[i] = ((i * 17 + 3) % 101) / 100
  const input = new Surface(width, height, data)
  const before = Buffer.from(bytes(input.data))
  for (let mode = 0; mode < 6; mode++) {
    for (let colors = 0; colors < 4; colors++) {
      const inkColor = [0.073, 0.191, 0.337]
      const paperColor = [0.923, 0.817, 0.711]
      if (colors & 1) inkColor.push(0.271)
      if (colors & 2) paperColor.push(0.683)
      const uniforms = { MODE: mode, resolution: [width, height], tileOffset: [-3, 2],
        strokeLength: 37.5, direction: mode % 4, balance: 43.25, pressure: 67.75,
        inkColor, paperColor }
      function render() {
        const output = new Surface(width, height)
        const kernel = bindCanonicalKernel(factory, { width, height, tileOffset: uniforms.tileOffset,
          uniforms, textures: { inputTex: input } })
        runPass({ kernel, destination: output })
        assert.deepEqual(bytes(input.data), before)
        return output
      }
      const first = render()
      assert.deepEqual(bytes(first.data), bytes(render().data))
      cases.push({ width, height, mode, colors, uniforms,
        nonfinite: Array.from(first.data).filter(value => !Number.isFinite(value)).length,
        f32: hash(bytes(first.data)), rgba8: hash(bytes(first.toRgba8())) })
    }
  }
}
process.stdout.write(JSON.stringify({ cpu_revision: '4307ca9f26fc415e4fc5e75227d429d35cc741cd',
  authority: EXPECTED, factory_sha256: hash(factory.toString()), cases }, null, 2) + '\n')
