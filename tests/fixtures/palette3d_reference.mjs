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
const key = 'filter3d/palette3d:palette3d'
const factory = canonicalKernelFactories[key]
assert.equal(kernelFactories.get(key), factory)
const width = 3, height = 9
const hash = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = data => Buffer.from(data.buffer, data.byteOffset, data.byteLength)
function input() {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i++) data[i] = ((i * 17 + 3) % 101) / 100
  return new Surface(width, height, data)
}
function render(index) {
  const source = input(), before = Buffer.from(bytes(source.data))
  const uniforms = { paletteIndex: index, rotation: index % 3 - 1, offset: 13.5, repeat: 1.7, alpha: 0.65 }
  const kernel = bindCanonicalKernel(factory, { width, height, time: 0.375, uniforms, textures: { inputTex3d: source } })
  const output = new Surface(width, height)
  runPass({ kernel, destination: output })
  assert.deepEqual(bytes(source.data), before)
  // The authority's OkLab path can produce NaN from pow(negative, 1/2.4).
  // Preserve its bytes and record each non-finite lane in the capture.
  if (index < 1 || index > 55) assert.deepEqual(bytes(output.data), before)
  return output
}
const cases = []
for (let index = -1; index <= 56; index++) {
  const first = render(index), second = render(index)
  assert.deepEqual(bytes(first.data), bytes(second.data))
  assert.deepEqual(first.toRgba8(), second.toRgba8())
  const nonfinite = Array.from(first.data).flatMap((value, lane) => Number.isFinite(value) ? [] : [lane])
  cases.push({ index, rotation: index % 3 - 1, nonfinite, f32: hash(bytes(first.data)), rgba8: hash(bytes(first.toRgba8())) })
}
process.stdout.write(JSON.stringify({
  key, cpu_revision: '4307ca9f26fc415e4fc5e75227d429d35cc741cd', authority: EXPECTED,
  factory_sha256: hash(factory.toString()), width, height,
  input_f32: hash(bytes(input().data)), cases,
}, null, 2) + '\n')
