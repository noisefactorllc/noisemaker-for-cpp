import assert from 'node:assert/strict'
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import {pathToFileURL} from 'node:url'
import {authenticateCpuRoot} from '../../tools/dsl/corpus_authority.mjs'
const [repo,cpuRoot,ledger]=process.argv.slice(2)
if (![repo,cpuRoot,ledger].every(value=>value&&path.isAbsolute(value))) throw Error('pass absolute repository, CPU root, and ledger paths')
const root=authenticateCpuRoot(cpuRoot,ledger)
const load=p=>import(pathToFileURL(path.join(root,p)).href)
const {canonicalKernelFactories,kernelFactories}=await load('src/effects/catalog.js')
const {bindCanonicalKernel}=await load('src/csl/glsl-kernel.js')
const {runPass}=await load('src/runtime/pass-runner.js')
const {Surface}=await load('src/runtime/surface.js')
const key='classicNoisedeck/shapes3d:shapes3d',factory=canonicalKernelFactories[key]
assert.equal(kernelFactories.get(key),factory)
const corpus=path.join(repo,'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d')
const source=fs.readFileSync(path.join(corpus,'sources/classicNoisedeck/shapes3d/shapes3d.glsl'))
const hash=a=>crypto.createHash('sha256').update(a).digest('hex')
assert.equal(hash(source),'818badfbadcf295d1863d208c0d0582a1349ff64f44dbf43f905a92fcfd4c5ad')
const meta=JSON.parse(fs.readFileSync(path.join(corpus,'metadata.json'))).effects['classicNoisedeck/shapes3d']
const width=5,height=4,time=Math.fround(.375),seed=17
const initial=new Float32Array(width*height*4)
for(let i=0;i<width*height;i++) {initial[i*4]=Math.fround(((i*11+3)%23)/23);initial[i*4+1]=Math.fround(((i*7+5)%29)/29);initial[i*4+2]=Math.fround(((i*13+1)%31)/31);initial[i*4+3]=Math.fround(.4+(i%4)*.15)}
const input=new Surface(width,height,initial)
const inputHash=hash(Buffer.from(input.data.buffer))
const d={BLEND_MODE:meta.params.blendMode.default,SHAPE_A:meta.params.shapeA.default,SHAPE_B:meta.params.shapeB.default}
const b=[...new Set(Object.values(meta.params.blendMode.choices))]
const a=[...new Set(Object.values(meta.params.shapeA.choices))]
const c=[...new Set(Object.values(meta.params.shapeB.choices))]
const cases=[{name:'default',...d},{name:'parameter',...d,variant:true},...b.map(v=>({name:'blend-'+v,...d,BLEND_MODE:v})),...a.map(v=>({name:'a-'+v,...d,SHAPE_A:v})),...c.map(v=>({name:'b-'+v,...d,SHAPE_B:v}))]
const rows=[]
for(const item of cases) {
 const uniforms={BLEND_MODE:item.BLEND_MODE,SHAPE_A:item.SHAPE_A,SHAPE_B:item.SHAPE_B,shapeAScale:item.variant?45:64,shapeBScale:item.variant?36:27,shapeAThickness:item.variant?9:5,shapeBThickness:item.variant?7:5,smoothness:item.variant?12:1,spin:item.variant?35:0,flip:item.variant?-25:0,spinSpeed:2,flipSpeed:2,repetition:item.variant,animation:1,flythroughSpeed:0,spacing:10,cameraDist:8,bgColor:new Float32Array([.1,.3,.6]),bgAlpha:15,colorMode:item.variant?1:10,paletteMode:0,paletteOffset:new Float32Array([.83,.6,.63]),paletteAmp:new Float32Array([.5,.5,.5]),paletteFreq:new Float32Array([1,1,1]),palettePhase:new Float32Array([.3,.1,0]),cyclePalette:1,rotatePalette:0,repeatPalette:1,weight:item.variant?35:0}
 function render(){const kernel=bindCanonicalKernel(factory,{width,height,time,seed,uniforms,textures:{inputTex:input}});const dst=new Surface(width,height);runPass({kernel,destination:dst,time,seed});return dst}
 const x=render(),y=render();assert.equal(hash(Buffer.from(x.data.buffer)),hash(Buffer.from(y.data.buffer)),item.name);assert.equal(hash(Buffer.from(input.data.buffer)),inputHash,item.name)
 rows.push({...item,f32:hash(Buffer.from(x.data.buffer)),rgba8:hash(x.toRgba8()),words:Array.from(new Uint32Array(x.data.buffer)),rgbaBytes:Array.from(x.toRgba8())})
}
process.stdout.write(JSON.stringify({cpu:'4307ca9f26fc415e4fc5e75227d429d35cc741cd',width,height,time,seed,inputHash,coverage:{BLEND_MODE:b,SHAPE_A:a,SHAPE_B:c},rows})+'\n')
