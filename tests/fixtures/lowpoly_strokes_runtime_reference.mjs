import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { authenticateCpuRoot } from '../../tools/dsl/corpus_authority.mjs'
const [repo,cpuRoot,ledger]=process.argv.slice(2)
if (![repo,cpuRoot,ledger].every(value=>value&&path.isAbsolute(value))) throw Error('pass absolute repository, CPU root, and ledger paths')
const root=authenticateCpuRoot(cpuRoot,ledger)
const load = rel => import(pathToFileURL(path.join(root, rel)).href)
const { canonicalKernelFactories, canonicalAdapterFactories, kernelFactories } = await load('src/effects/catalog.js')
const { bindCanonicalKernel } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
const hash = b => crypto.createHash('sha256').update(b).digest('hex')
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength)
const f = Math.fround
const width = 7, height = 5, time = f(.375), seed = 43
function makeInput() {
  const data = new Float32Array(width * height * 4)
  for (let y=0; y<height; ++y) for (let x=0; x<width; ++x) {
    const i=(y*width+x)*4
    data[i]=f((((37*x+17*y+11)%127)+1)/129)
    data[i+1]=f((((19*x+43*y+7)%113)+2)/117)
    data[i+2]=f((((61*x+29*y+3)%109)+3)/115)
    data[i+3]=f((((7*x+5*y+2)%23)+8)/31)
  }
  return new Surface(width,height,data)
}
const programs = [
  {key:'filter/lowPoly:lowPoly', source:'sources/filter/lowPoly/lowPoly.glsl', expectedSource:'2f6a184ef4d372ebf811eaa59420bbce66fa25702e23a278557521679ce7b2f5', cases:[
    {name:'plain-flat',border:0,light:0,mode:0}, {name:'border-one-edges',border:1,light:0,mode:1},
    {name:'border-max-distance2',border:100,light:0,mode:2}, {name:'light-one-distance3',border:0,light:1,mode:3},
    {name:'light-max-flat',border:0,light:100,mode:0}, {name:'mixed-mid-edges',border:33,light:67,mode:1},
    {name:'mixed-max-distance3',border:100,light:100,mode:3} ]},
  {key:'filter/strokes:stkSmear', source:'sources/filter/strokes/stkSmear.glsl', expectedSource:'dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db', cases:[
    {name:'angled',mode:0}, {name:'sprayed',mode:1}, {name:'dark',mode:2}, {name:'sumiE',mode:3}, {name:'smudge',mode:4} ]}
]
const output=[]
for (const program of programs) {
  const sourceBytes=fs.readFileSync(path.join(path.join(repo,'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'), program.source))
  if (hash(sourceBytes)!==program.expectedSource) throw Error('source drift '+program.key)
  const factory=canonicalKernelFactories[program.key]
  if (typeof factory!=='function' || kernelFactories.get(program.key)!==factory || canonicalAdapterFactories[program.key]!==undefined) throw Error('factory identity '+program.key)
  const rows=[]
  for (const c of program.cases) {
    function render() {
      const input=makeInput(), original=Buffer.from(bytes(input.data))
      const uniforms=program.key.includes('lowPoly') ? {
        LP_BORDER:c.border, LP_LIGHT:c.light, scale:35, seed:17, mode:c.mode,
        edgeStrength:.42, edgeColor:new Float32Array([.13,.67,.29]), speed:2,
        alpha:.83,
      } : {MODE:c.mode, strokeLength:18, balance:44, intensity:66}
      const kernel=bindCanonicalKernel(factory,{width,height,time,frame:37,deltaTime:f(1/60),seed,uniforms,textures:{inputTex:input},tileOffset:new Float32Array([2,1]),fullResolution:new Float32Array([11,9])})
      const image=new Surface(width,height)
      runPass({kernel,destination:image,time,seed})
      if (!bytes(input.data).equals(original)) throw Error('input mutated '+program.key+' '+c.name)
      return {input,image}
    }
    const one=render(), two=render()
    const f32=hash(bytes(one.image.data)), rgba=hash(one.image.toRgba8())
    if (f32!==hash(bytes(two.image.data)) || rgba!==hash(two.image.toRgba8())) throw Error('repeat mismatch '+program.key+' '+c.name)
    rows.push({...c, f32, rgba, input_f32:hash(bytes(one.input.data)), first_pixel:Array.from(one.image.data.slice(0,4)), nonfinite:Array.from(one.image.data).filter(x=>!Number.isFinite(x)).length})
  }
  output.push({key:program.key, source_sha256:program.expectedSource, factory_name:factory.name, factory_sha256:hash(Buffer.from(Function.prototype.toString.call(factory))), cases:rows})
}
process.stdout.write(JSON.stringify({cpu_root:root,canonical_kernels_sha256:hash(fs.readFileSync(path.join(root,'src/effects/generated/canonical-kernels.js'))),width,height,time,seed,programs:output},null,2)+'\n')
