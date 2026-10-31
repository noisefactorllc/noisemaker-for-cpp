import fs from 'node:fs'
import { importCpu } from '../tools/dsl/corpus_authority.mjs'

const directory = process.env.NOISEMAKER_TEST_PHYSARUM_CAPTURE
if (!directory) throw new Error('Physarum capture directory is required')
const { api } = await importCpu(process.env.NOISEMAKER_CPU_ROOT)
const original = api.CpuRenderer.prototype.storeGroupOutput
if (typeof original !== 'function') throw new Error('Group output capture seam is unavailable')
let ordinal = 0
api.CpuRenderer.prototype.storeGroupOutput = function (name, surface, state, ...rest) {
  const base = `${directory}/${ordinal++}`
  fs.appendFileSync(`${directory}/index.tsv`,
    [state.definition.id, name, surface.width, surface.height].join('\t') + '\n')
  fs.writeFileSync(`${base}.f32`,
    Buffer.from(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength))
  fs.writeFileSync(`${base}.rgba8`, surface.toRgba8())
  return original.call(this, name, surface, state, ...rest)
}
