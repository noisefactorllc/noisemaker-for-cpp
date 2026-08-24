import fs from 'node:fs'
import { createDefaultRegistry, effectCatalog, kernels, kernelFactories } from 'file://../noisemaker-for-cpu/src/effects/catalog.js'
import { CpuRenderer } from 'file://../noisemaker-for-cpu/src/runtime/renderer.js'
import { bindCanonicalKernel } from 'file://../noisemaker-for-cpu/src/csl/glsl-kernel.js'

const modulePath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const whole = fs.readFileSync(modulePath, 'utf8')
const start = whole.indexOf('function canonicalFactory245(')
const end = whole.indexOf('\nfunction canonicalFactory246(', start)
let body = whole.slice(start, end)
body = body.replace(
  'dist += r1[2] * (variation * 0.009999999776482582);',
  "dist += r1[2] * (variation * 0.009999999776482582); if(gl_FragCoord[0]===0.5&&gl_FragCoord[1]===0.5) console.log('cell',x,y,'point',...point,'r1',...r1,'r2',...r2,'dist',dist,'d',d);",
)
const patched = `${whole.slice(0, start)}${body}${whole.slice(end)}`
const generated = await import(`data:text/javascript;base64,${Buffer.from(patched).toString('base64')}`)

const renderer = new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories })
const definition = effectCatalog.find((effect) => effect.id === 'synth/cell')
const pass = definition.passes.find((candidate) => candidate.program === 'cell')
const params = definition.normalizeArguments([])
const base = renderer.buildBindings(definition, params, [], null, new Map(), {
  width: 9, height: 7, time: 0.375, frame: 7, seed: 19, externalTextures: {},
})
const uniforms = renderer.passUniforms(pass, params, base.uniforms)
const kernel = bindCanonicalKernel(generated.canonicalKernelFactories['synth/cell:cell'], {
  width: 9, height: 7, time: 0.375, frame: 7, deltaTime: 1 / 60, seed: 19,
  uniforms, textures: {}, tileOffset: [2, 1], fullResolution: [13, 11],
})
const out = new Float32Array(4)
kernel({ fragCoord: new Float32Array([0.5, 0.5]), uv: new Float32Array([0.5 / 9, 0.5 / 7]), resolution: new Float32Array([9, 7]) }, out)
console.log('out', Array.from(out), Array.from(new Uint32Array(out.buffer)).map((x) => x.toString(16)))
