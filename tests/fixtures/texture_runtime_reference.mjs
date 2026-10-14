import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import {pathToFileURL} from 'node:url'

const [repo, root, ledger, output] = process.argv.slice(2)
if (![repo, root, ledger, output].every(value => value && path.isAbsolute(value))) throw Error('usage: node script.mjs ABS_REPO ABS_CPU_ROOT ABS_LEDGER ABS_OUTPUT')
const sha=x=>crypto.createHash('sha256').update(x).digest('hex')
if (process.version!=='v26.0.0') throw Error('Node version drift')
if (!fs.lstatSync(root).isDirectory()||fs.lstatSync(root).isSymbolicLink()) throw Error('authority root is not a regular directory')
const lines=fs.readFileSync(ledger,'utf8').trim().split('\n')
for(const line of lines){const match=/^([0-9a-f]{64})  (\/.*)$/.exec(line);if(!match)throw Error('ledger format');const file=match[2];if(!file.startsWith(`${root}/`))throw Error('ledger root mismatch');const stat=fs.lstatSync(file);if(!stat.isFile()||stat.isSymbolicLink()||sha(fs.readFileSync(file))!==match[1])throw Error(`authority ledger mismatch: ${path.relative(root,file)}`)}
const load=relative=>import(pathToFileURL(path.join(root,relative)).href)
const [{canonicalKernelFactories,kernelFactories},{createCanonicalBindings},{bindGlslKernel},{runPass},{Surface},{UPSTREAM_REVISION}]=await Promise.all([load('src/effects/catalog.js'),load('src/csl/glsl-kernel.js'),load('src/csl/glsl-runtime.js'),load('src/runtime/pass-runner.js'),load('src/runtime/surface.js'),load('src/effects/generated/upstream-snapshot.js')])
const key='filter/texture:texture',factory=canonicalKernelFactories[key]
if(typeof factory!=='function'||kernelFactories.get(key)!==factory)throw Error('canonical/public factory identity mismatch')
const factoryText=Function.prototype.toString.call(factory)
const f=Math.fround
const specs=[
 {name:'paper-center',width:4,height:3,phase:2,time:.25,alpha:1,scale:1.2,intensity:65,contrast:35,mono:false,tileOffset:[1,2],fullResolution:[16,12]},
 {name:'paper-wide-tile',width:8,height:3,phase:6,time:.41,alpha:.8,scale:1.8,intensity:55,contrast:55,mono:false,tileOffset:[-2,5],fullResolution:[32,12]},
]
function input(def){const s=new Surface(def.width,def.height);for(let y=0;y<def.height;y++)for(let x=0;x<def.width;x++){const i=(y*def.width+x)*4;s.data[i]=f(((x*17+y*11+def.phase)%29)/28);s.data[i+1]=f(((x*7+y*19+def.phase*2)%31)/30);s.data[i+2]=f(((x*13+y*5+def.phase*3)%37)/36);s.data[i+3]=f(.2+((x+y+def.phase)%8)/10)}return s}
function words(s){return Array.from(new Uint32Array(s.data.buffer,s.data.byteOffset,s.data.byteLength/4),x=>`0x${(x>>>0).toString(16).padStart(8,'0')}`)}
function byteDigest(ws){return sha(Buffer.from(ws.map(x=>Number.parseInt(x,16)).flatMap(x=>[x&255,(x>>>8)&255,(x>>>16)&255,x>>>24])))}
function record(s){const w=words(s),b=Array.from(s.toRgba8());return {f32_words_le:w,f32_sha256:byteDigest(w),rgba8_bytes:b,rgba8_sha256:sha(Buffer.from(b))}}
function render(def,mode){const src=input(def),before=record(src);const uniforms={MODE:mode,time:f(def.time),alpha:f(def.alpha),scale:f(def.scale),intensity:f(def.intensity),contrast:f(def.contrast),mono:def.mono};const bindings=createCanonicalBindings({width:def.width,height:def.height,time:def.time,uniforms,textures:{inputTex:src},tileOffset:new Float32Array(def.tileOffset.map(f)),fullResolution:new Float32Array(def.fullResolution.map(f))});if(bindings.MODE!==mode)throw Error('MODE binding mismatch');const dst=new Surface(def.width,def.height);runPass({kernel:bindGlslKernel(factory,bindings),destination:dst,time:def.time,seed:def.phase,tileRows:1});const after=record(src);if(after.f32_sha256!==before.f32_sha256||after.rgba8_sha256!==before.rgba8_sha256)throw Error(`input mutated: ${def.name} MODE ${mode}`);return {input:before,output:record(dst),object:dst}}
const cases=[]
for(const spec of specs){let stableInput=null;for(let mode=0;mode<=14;mode++){const a=render(spec,mode),b=render(spec,mode);if(stableInput===null)stableInput=a.input.f32_sha256;if(a.input.f32_sha256!==stableInput||b.input.f32_sha256!==stableInput)throw Error('inputs differ across modes');if(a.output.f32_sha256!==b.output.f32_sha256||a.output.rgba8_sha256!==b.output.rgba8_sha256||a.object===b.object||a.object.data===b.object.data)throw Error(`repeat mismatch: ${spec.name} MODE ${mode}`);cases.push({name:spec.name,mode,input:a.input,expected:a.output,repeat_exact:true,repeat_storage_distinct:true,input_unchanged:true})}}
const doc={schema:'noisemaker-for-cpp.texture.runtime-mode-cpu-reference.v1',authority:{root,ledger_sha256:sha(fs.readFileSync(ledger)),ledger_entries:lines.length,node:process.version,upstream_revision:UPSTREAM_REVISION,program_key:key,factory_name:factory.name,factory_text_sha256:sha(factoryText),public_factory_is_canonical:true,source_sha256:sha(fs.readFileSync(path.join(repo, 'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources/filter/texture/texture.glsl')))},specs,cases}
fs.writeFileSync(output,`${JSON.stringify(doc,null,2)}\n`)
console.log(JSON.stringify({path:output,sha256:sha(fs.readFileSync(output)),cases:cases.length,modes:[0,14],specs:specs.map(x=>x.name),ledger_entries:lines.length,factory_text_sha256:doc.authority.factory_text_sha256}))
