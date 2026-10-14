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
const { bindGlslKernel } = await load('src/csl/glsl-runtime.js')
const { CpuRenderer } = await load('src/runtime/renderer.js')
const { Surface } = await load('src/runtime/surface.js')
const hash = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = data => Buffer.from(data.buffer, data.byteOffset, data.byteLength)
const key = 'filter3d/flow3d:agent'
const factory = canonicalKernelFactories[key]
assert.equal(kernelFactories.get(key), factory)
const cases = []
for (const scenario of [0, 1, 2]) {
  const textures = { stateTex1: new Surface(2, 2), stateTex2: new Surface(2, 2),
    stateTex3: new Surface(2, 2), mixerTex: new Surface(4, 16) }
  for (let i = 0; i < 4; i++) {
    textures.stateTex1.data.set([i * 0.5 + 0.25, 1.5, 2.25, i * 0.2 + 0.1], i * 4)
    textures.stateTex2.data.set([0.2, 0.4, 0.6, i], i * 4)
    textures.stateTex3.data.set([scenario === 2 ? 3 : 0.2, scenario === 0 ? 0 : 1, -0.15, 0], i * 4)
  }
  for (let i = 0; i < textures.mixerTex.data.length; i++) textures.mixerTex.data[i] = ((i * 17 + 3) % 101) / 100
  const before = Object.values(textures).map(surface => Buffer.from(bytes(surface.data)))
  for (const behavior of [0, 1, 2, 3, 4, 5, 10, 11]) {
    const uniforms = { BEHAVIOR: behavior, volumeSize: 4, stride: 1.25,
      strideDeviation: 0.2, kink: 1.1, time: 0.375, lifetime: 1.25, density: 100 }
    function render() {
      const destinations = [new Surface(2, 2), new Surface(2, 2), new Surface(2, 2)]
      const kernel = bindGlslKernel(factory, { ...uniforms, ...textures })
      CpuRenderer.prototype.runCanonicalMrtPass({ kernel, destinations, time: uniforms.time })
      Object.values(textures).forEach((surface, index) => assert.deepEqual(bytes(surface.data), before[index]))
      return destinations
    }
    const first = render(), second = render()
    first.forEach((surface, index) => {
      assert.deepEqual(bytes(surface.data), bytes(second[index].data))
      assert.ok(Array.from(surface.data).every(Number.isFinite))
    })
    cases.push({ scenario, behavior, uniforms, outputs: first.map(surface => ({
      f32: hash(bytes(surface.data)), rgba8: hash(bytes(surface.toRgba8())) })) })
  }
}
process.stdout.write(JSON.stringify({ cpu_revision: '4307ca9f26fc415e4fc5e75227d429d35cc741cd',
  authority: EXPECTED, factory_sha256: hash(factory.toString()), cases }, null, 2) + '\n')
