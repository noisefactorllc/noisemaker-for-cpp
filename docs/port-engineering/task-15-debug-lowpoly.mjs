import fs from 'node:fs'
import { createDefaultRegistry, effectCatalog, kernels, kernelFactories } from 'file://../noisemaker-for-cpu/src/effects/catalog.js'
import { CpuRenderer } from 'file://../noisemaker-for-cpu/src/runtime/renderer.js'
import { bindCanonicalKernel } from 'file://../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { Surface } from 'file://../noisemaker-for-cpu/src/runtime/surface.js'

const modulePath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const whole = fs.readFileSync(modulePath, 'utf8')
const start = whole.indexOf('function canonicalFactory79(')
const end = whole.indexOf('\nfunction canonicalFactory80(', start)
let body = whole.slice(start, end)
body = body.replace(
  'return new $runtime.PooledFloat32Array([v[0] / 4294967296, v[1] / 4294967296]);',
  "var hv = new $runtime.PooledFloat32Array([v[0] / 4294967296, v[1] / 4294967296]); if(gl_FragCoord[0]===2.5&&gl_FragCoord[1]===0.5) console.log('hash2',Array.from(p),s,Array.from(v),Array.from(hv)); return hv;",
)
body = body.replace(
  'var d = distance(auv, point);',
  "var d = distance(auv, point); if(gl_FragCoord[0]===2.5&&gl_FragCoord[1]===0.5) console.log('site',dy,dx,Array.from(neighborF),Array.from(offset),Array.from(point),d);",
)
body = body.replace(
  'var edgeFactor = mix(edgeStrength, 0, edgeDist);',
  "var edgeFactor = mix(edgeStrength, 0, edgeDist); if(gl_FragCoord[0]===2.5&&gl_FragCoord[1]===0.5) console.log('final',minDist,secondDist,edgeDist,edgeFactor,Array.from(cellColor),Array.from(original||[]));",
)
const patched = `${whole.slice(0, start)}${body}${whole.slice(end)}`
const generated = await import(`data:text/javascript;base64,${Buffer.from(patched).toString('base64')}`)

const renderer = new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories })
const definition = effectCatalog.find((effect) => effect.id === 'filter/lowPoly')
const pass = definition.passes.find((candidate) => candidate.program === 'lowPoly')
const params = definition.normalizeArguments([])
const base = renderer.buildBindings(definition, params, [], null, new Map(), {
  width: 9, height: 7, time: 0.375, frame: 7, seed: 19, externalTextures: {},
})
const uniforms = renderer.passUniforms(pass, params, base.uniforms)
const inputTex = new Surface(11, 9)
for (let y = 0; y < 9; y += 1) for (let x = 0; x < 11; x += 1) {
  const lane = (y * 11 + x) * 4
  inputTex.data[lane] = ((x * 17 + y * 31 + 13) % 101) / 100
  inputTex.data[lane + 1] = ((x * 7 + y * 19 + 23) % 97) / 96
  inputTex.data[lane + 2] = ((x * 29 + y * 11 + 5) % 89) / 88
  inputTex.data[lane + 3] = 0.35 + ((x * 3 + y * 5 + 1) % 13) / 20
}
const kernel = bindCanonicalKernel(generated.canonicalKernelFactories['filter/lowPoly:lowPoly'], {
  width: 9, height: 7, time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19,
  uniforms, textures: { inputTex }, tileOffset: [2, 1], fullResolution: [13, 11],
})
const out = new Float32Array(4)
kernel({ fragCoord: new Float32Array([2.5, 0.5]), uv: new Float32Array([2.5 / 9, 0.5 / 7]), resolution: new Float32Array([9, 7]) }, out)
console.log('out', Array.from(out), Array.from(new Uint32Array(out.buffer)).map((x) => x.toString(16)))
