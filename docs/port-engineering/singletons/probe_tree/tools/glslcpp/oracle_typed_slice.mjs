// Development-only external parity oracle for the Task-8 typed emission slice.
// Development-only: requires a sibling checkout of noisemaker-for-cpu next to
// this repository. Run from the noisemaker-for-cpu checkout:
//   node ../noisemaker-for-cpp/tools/glslcpp/oracle_typed_slice.mjs
import crypto from 'node:crypto'
import { canonicalKernelFactories } from '../../../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
import { bindCanonicalKernel } from '../../../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../noisemaker-for-cpu/src/runtime/surface.js'

const expected = {
  'filter/wormhole:clear': ['5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef', '5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1'],
  'filter/bc:bc': ['17e28b5ca13d1a21234aaaf6d3a2fc2f605f29413ad1baa1db1b6343010878e3', 'a10774e92b60d5558b372d349fcac02f3424fd92cd880f2701d1d00f3154767e'],
  'filter/threshold:thresh': ['61f2a88622e0a75332fb6994f5ae82a21c6889df4296e9c64b58f2de9d41d45e', '63d3dc8653662baff87afd576ae73ecfc61d65c688cebfde7406153e6484ac65'],
  'filter/smoothstep:smoothstep': ['200eb65fed133e0640ed0165c4be24923e6fda1c236c3ea8b5d07f8747566b45', '340558b647177c7f72bbd4b2fcbecef4facfd780a5e6fbfaf7231961895058a7'],
  'mixer/channelCombine:channelCombine': ['8bd32d6a3e760ed40d064c8671aec9e9ce7e491d666083c5cf2785224fb4a290', 'a5ac13cccc6fdb4d53bd7fefc545b7fedcbf5cca1ec93b7ab51fe746438c342f'],
}

const digest = (value) => crypto.createHash('sha256').update(value).digest('hex')
const source = (width, height, tag) => {
  const bytes = new Uint8Array(width * height * 4)
  for (let y = 0; y < height; ++y) for (let x = 0; x < width; ++x) {
    const index = (y * width + x) * 4
    bytes[index] = (31 * x + 17 * y + 13 * tag) % 256
    bytes[index + 1] = (11 * x + 47 * y + 29 * tag) % 256
    bytes[index + 2] = (67 * x + 19 * y + 7 * tag) % 256
    bytes[index + 3] = (255 - 23 * x - 37 * y - 5 * tag) & 255
  }
  return Surface.fromRgba8(width, height, bytes)
}
const f = Math.fround
const a = source(5, 3, 1); const r = source(5, 3, 11); const g = source(3, 5, 23); const b = source(7, 2, 37)
const common = { tileOffset: new Float32Array([f(3), f(-2)]), fullResolution: new Float32Array([f(17), f(13)]) }
const cases = {
  'filter/wormhole:clear': [{}, {}],
  'filter/bc:bc': [{ ...common, brightness: f(1.3), contrast: f(.72) }, { inputTex: a }],
  'filter/threshold:thresh': [{ ...common, level: f(.45), sharpness: f(.18) }, { inputTex: a }],
  'filter/smoothstep:smoothstep': [{ ...common, edge0: f(.2), edge1: f(.75) }, { inputTex: a }],
  'mixer/channelCombine:channelCombine': [{ ...common, resolution: new Float32Array([f(8), f(8)]), rLevel: f(85), gLevel: f(60), bLevel: f(95) }, { rTex: r, gTex: g, bTex: b }],
}

for (const [key, [uniforms, textures]] of Object.entries(cases)) {
  const destination = new Surface(8, 8)
  const kernel = bindCanonicalKernel(canonicalKernelFactories[key], {
    width: 8, height: 8, time: f(.125), seed: f(7), uniforms, textures,
    fullResolution: new Float32Array([8, 8]),
  })
  runPass({ kernel, destination, time: .125, seed: 7 })
  const floats = digest(Buffer.from(destination.data.buffer, destination.data.byteOffset, destination.data.byteLength))
  const rgba = digest(Buffer.from(destination.toRgba8()))
  if (floats !== expected[key][0] || rgba !== expected[key][1]) throw new Error(`${key}: ${floats} ${rgba}`)
  console.log(`${key}: ${floats} ${rgba}`)
}
