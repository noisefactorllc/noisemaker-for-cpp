import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'

const keys = [
  'mixer/focusBlur:focusBlur',
  'filter/lighting:lighting',
  'classicNoisedeck/caustic:caustic',
  'filter/extrude:extrude',
  'filter/waves:waves',
  'synth/curl:curl',
  'filter/posterize:posterize',
  'filter/watercolor:wcSimplify',
]
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const rows = keys.map(key => {
  const canonical = canonicalKernelFactories[key]
  const publicFactory = kernelFactories.get(key)
  return {
    key,
    canonical_factory_name: canonical?.name ?? null,
    canonical_factory_to_string_sha256: canonical ? sha256(canonical.toString()) : null,
    public_is_exact_canonical_object: publicFactory === canonical,
    adapter_factory_name: canonicalAdapterFactories[key]?.name ?? null,
  }
})
if (rows.some(row => !row.public_is_exact_canonical_object || row.adapter_factory_name !== null)) throw new Error('candidate public identity drift')
const payload = `${JSON.stringify({
  schema: 'noisemaker-for-cpp.future-precompute.public-identities.v1',
  canonical_kernels_sha256: sha256(fs.readFileSync('../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js')),
  catalog_sha256: sha256(fs.readFileSync('../noisemaker-for-cpu/src/effects/catalog.js')),
  adapter_index_sha256: sha256(fs.readFileSync('../noisemaker-for-cpu/src/effects/adapters/index.js')),
  rows,
}, null, 2)}\n`
const output = path.join(path.dirname(fileURLToPath(import.meta.url)), 'public-identities.json')
if (process.argv.includes('--check')) {
  if (!fs.existsSync(output) || fs.readFileSync(output, 'utf8') !== payload) throw new Error('public identity fixture drift')
  console.log(`public identity fixture ok (${rows.length} candidates)`)
} else {
  fs.writeFileSync(output, payload)
  console.log(output)
}
