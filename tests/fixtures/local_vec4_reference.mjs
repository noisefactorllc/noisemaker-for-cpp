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

function input(width, height, frame, empty) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i++) {
    data[i] = i % 4 === 3
      ? (empty && (Math.floor(i / 4) + frame) % 3 === 0 ? 0 : 1)
      : ((i * 17 + frame * 11 + 3) % 101) / 100
  }
  return new Surface(width, height, data)
}

function render(key, width, height, uniforms, textures) {
  const factory = canonicalKernelFactories[key]
  assert.equal(kernelFactories.get(key), factory)
  const before = Object.values(textures).map(surface => Buffer.from(bytes(surface.data)))
  const destination = new Surface(width, height)
  const kernel = bindCanonicalKernel(factory, { width, height, uniforms, textures })
  runPass({ kernel, destination })
  Object.values(textures).forEach((surface, i) => assert.deepEqual(bytes(surface.data), before[i]))
  assert.ok(Array.from(destination.data).every(Number.isFinite), `${key}: non-finite output`)
  return destination
}

const cases = []
function capture(key, width, height, uniforms, textures, extra) {
  const first = render(key, width, height, uniforms, textures)
  const second = render(key, width, height, uniforms, textures)
  assert.deepEqual(bytes(first.data), bytes(second.data))
  cases.push({ key, width, height, uniforms, ...extra,
    f32: hash(bytes(first.data)), rgba8: hash(bytes(first.toRgba8())) })
}

const temporal = 'filter/temporalAberration:temporalAberration'
for (const empty of [false, true]) {
  const textures = { inputTex: input(4, 3, 0, false) }
  for (let frame = 1; frame <= 8; frame++) textures[`h${frame}`] = input(4, 3, frame, empty)
  for (const delay of [-2, 0, 0.25, 1, 2, 3, 4, 5, 6, 7, 7.75, 8, 20]) {
    capture(temporal, 4, 3,
      { redDelay: delay, greenDelay: 8 - delay, blueDelay: delay / 2 + 0.375 }, textures, { empty })
  }
}

const smooth = 'synth/navierStokes:nsSmooth'
for (const [width, height] of [[13, 11], [3, 2], [5, 3]]) {
  for (const smoothing of [-1, 0, 1, 2, 3, 4, 5, 6, 7]) {
    capture(smooth, width, height, { smoothing }, { canvasTex: input(5, 3, 2, false) }, {})
  }
}

process.stdout.write(JSON.stringify({
  cpu_revision: '7f473400ac744025d46221bf527b43c1b5c1ef4e', authority: EXPECTED,
  factories: Object.fromEntries([temporal, smooth].map(key => [key, hash(canonicalKernelFactories[key].toString())])),
  cases,
}, null, 2) + '\n')
