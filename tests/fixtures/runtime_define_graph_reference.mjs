import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const [repository, authorityRoot, ledger] = process.argv.slice(2)
if (![repository, authorityRoot, ledger].every(value => value && path.isAbsolute(value))) {
  throw new Error('pass absolute repository, CPU authority, and ledger paths')
}
const { authenticateCpuRoot, EXPECTED } = await import(
  pathToFileURL(path.join(repository, 'tools/dsl/corpus_authority.mjs')).href)
const root = authenticateCpuRoot(authorityRoot, ledger)
const load = relative => import(pathToFileURL(path.join(root, relative)).href)
const [{ CpuRenderer }, { createDefaultRegistry, kernels, kernelFactories }, { UPSTREAM_REVISION }] = await Promise.all([
  load('src/runtime/renderer.js'), load('src/effects/catalog.js'),
  load('src/effects/generated/upstream-snapshot.js'),
])
if (process.version !== 'v26.0.0' || UPSTREAM_REVISION !== EXPECTED.upstreamRevision) {
  throw new Error('CPU runtime or source revision mismatch')
}
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const renderer = new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories })
const options = Object.freeze({ width: 8, height: 8, time: 0.25, frame: 0, seed: 17 })
const cases = [
  { name: 'perlin-2', source: 'search synth\nperlin(dimensions: 2).write(o0)\nrender(o0)\n' },
  { name: 'perlin-3', source: 'search synth\nperlin(dimensions: 3).write(o0)\nrender(o0)\n' },
  { name: 'emboss-0', source: 'search synth, filter\nsolid(color: #3a7).emboss(style: 0).write(o0)\nrender(o0)\n' },
  { name: 'emboss-1', source: 'search synth, filter\nsolid(color: #3a7).emboss(style: 1).write(o0)\nrender(o0)\n' },
]
const record = result => {
  const data = result.surface.data
  return {
    float32_sha256: hash(Buffer.from(data.buffer, data.byteOffset, data.byteLength)),
    rgba8_sha256: hash(Buffer.from(result.toRgba8())),
  }
}
const results = cases.map(item => {
  const first = renderer.render(item.source, options)
  const second = renderer.render(item.source, options)
  const expected = record(first)
  if (JSON.stringify(expected) !== JSON.stringify(record(second))) {
    throw new Error(`${item.name} is not repeatable`)
  }
  return { ...item, ...expected }
})
process.stdout.write(JSON.stringify({
  authority_revision: EXPECTED.upstreamRevision,
  authority_ledger_sha256: hash(fs.readFileSync(ledger)),
  options, results,
}, null, 2) + '\n')
