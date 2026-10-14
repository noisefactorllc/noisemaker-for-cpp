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
const key = 'render/pointsBillboardRender:depthMerge'
const factory = canonicalKernelFactories[key]
assert.equal(kernelFactories.get(key), factory)
const hash = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = data => Buffer.from(data.buffer, data.byteOffset, data.byteLength)
const compare = (a, b) => a[0] - b[0] || a[1] - b[1]
const cases = []
for (const [width, height] of [[1, 1], [5, 1], [3, 3], [4, 3], [7, 5]]) {
  const count = width * height
  for (let runLength = 1; runLength < count * 2; runLength *= 2) {
    const records = Array.from({ length: count }, (_, index) => [((index * 7 + 3) % 11) - 6, index])
    const ordered = []
    for (let start = 0; start < count; start += runLength) {
      ordered.push(...records.slice(start, start + runLength).sort(compare))
    }
    const data = new Float32Array(count * 4)
    const offset = i => ((height - 1 - Math.floor(i / width)) * width + i % width) * 4
    ordered.forEach(([depth, index], i) => data.set([depth, index, 0, 1], offset(i)))
    const source = new Surface(width, height, data)
    const before = Buffer.from(bytes(source.data))
    function render() {
      const destination = new Surface(width, height)
      const kernel = bindCanonicalKernel(factory, { width, height, uniforms: { runLength }, textures: { orderTex: source } })
      runPass({ kernel, destination })
      assert.deepEqual(bytes(source.data), before)
      assert.ok(Array.from(destination.data).every(Number.isFinite))
      return destination
    }
    const first = render(), second = render()
    assert.deepEqual(bytes(first.data), bytes(second.data))
    const expected = []
    for (let start = 0; start < count; start += 2 * runLength) {
      expected.push(...ordered.slice(start, start + 2 * runLength).sort(compare))
    }
    expected.forEach(([depth, index], i) => {
      assert.equal(first.data[offset(i)], depth)
      assert.equal(first.data[offset(i) + 1], index)
    })
    cases.push({ width, height, runLength, input: Array.from(data),
      f32: hash(bytes(first.data)), rgba8: hash(bytes(first.toRgba8())) })
  }
}
process.stdout.write(JSON.stringify({
  key, cpu_revision: '4307ca9f26fc415e4fc5e75227d429d35cc741cd', authority: EXPECTED,
  factory_sha256: hash(factory.toString()), cases,
}, null, 2) + '\n')
