import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import {pathToFileURL,fileURLToPath} from 'node:url'
const args={}
for(let index=2;index<process.argv.length;++index){
 const flag=process.argv[index]
 if(flag==='--write'||flag==='--check'){
  if(args[flag])throw new Error(`duplicate ${flag}`)
  args[flag]=true
 }else if(['--cpu-root','--cpp-root','--ledger','--output','--json-output'].includes(flag)){
  if(args[flag]||index+1>=process.argv.length)throw new Error(`missing or duplicate ${flag}`)
  args[flag]=process.argv[++index]
 }else throw new Error(`unknown argument ${flag}`)
}
if(Boolean(args['--write'])===Boolean(args['--check']))throw new Error('choose exactly one of --write or --check')
if(!args['--cpu-root']||!args['--ledger'])throw new Error('--cpu-root and --ledger are required')
const cppRoot=path.resolve(args['--cpp-root']??path.join(path.dirname(fileURLToPath(import.meta.url)),'../..'))
const cpuRoot=path.resolve(args['--cpu-root'])
const ledger=path.resolve(args['--ledger'])
const includePath=path.resolve(args['--output']??path.join(cppRoot,'tests/oracles/array_runtime_expected.inc'))
const jsonPath=args['--json-output']?path.resolve(args['--json-output']):null
const authority=await import(pathToFileURL(path.join(cppRoot,'tools/dsl/corpus_authority.mjs')).href)
authority.authenticateCpuRoot(cpuRoot,ledger)
const load=async relative=>import(pathToFileURL(path.join(cpuRoot,relative)).href)
const {effectRecords,UPSTREAM_REVISION}=await load('src/effects/generated/upstream-snapshot.js')
const {canonicalKernelFactories,kernelFactories,canonicalAdapterFactories}=await load('src/effects/catalog.js')
const {bindCanonicalKernel}=await load('src/csl/glsl-kernel.js')
const {runPass}=await load('src/runtime/pass-runner.js')
const {Surface}=await load('src/runtime/surface.js')
if(process.version!=='v26.0.0'||UPSTREAM_REVISION!=='6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d')throw new Error('CPU runtime/source revision mismatch')
const sha=b=>crypto.createHash('sha256').update(b).digest('hex')
const bytesOf=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength)
const f=Math.fround
function inputSurface(width,height,salt){
 const surface=new Surface(width,height)
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const i=(y*width+x)*4
  surface.data[i]=f(((x*3+y*5+salt)%16)/16)
  surface.data[i+1]=f(((x*7+y*2+salt*3)%16)/16)
  surface.data[i+2]=f(((x*11+y*13+salt*2)%16)/16)
  surface.data[i+3]=1
 }
 return surface
}
function render(effect,factory,axes,geometry,controls){
 const {width,height,salt}=geometry
 const input=inputSurface(width,height,salt)
 const before=Buffer.from(bytesOf(input.data))
 const uniforms={inputTex:input}
 for(const p of Object.values(effect.params)){
  if(p.uniform)uniforms[p.uniform]=p.default
  if(p.define)uniforms[p.define]=axes[p.define]??p.default
 }
 Object.assign(uniforms,controls)
 const options={width,height,time:controls.time??0.375,seed:controls.seed??7,
  uniforms,textures:{inputTex:input},tileOffset:new Float32Array([0,0]),fullResolution:new Float32Array([width,height])}
 const kernel=bindCanonicalKernel(factory,options)
 const output=new Surface(width,height)
 runPass({kernel,destination:output,time:options.time,seed:options.seed,tileRows:2})
 if(!before.equals(bytesOf(input.data)))throw new Error('input mutated')
 return {input_f32_sha256:sha(before),output_f32_sha256:sha(bytesOf(output.data)),
  output_rgba8_sha256:sha(Buffer.from(output.toRgba8())),
  input_f32_words_le:Array.from(new Uint32Array(input.data.buffer,input.data.byteOffset,input.data.length),n=>'0x'+n.toString(16).padStart(8,'0')),
  output_f32_words_le:Array.from(new Uint32Array(output.data.buffer,output.data.byteOffset,output.data.length),n=>'0x'+n.toString(16).padStart(8,'0')),
  output_rgba8_bytes:Array.from(output.toRgba8())}
}
const expectedFactories={
 'classicNoisedeck/cellRefract:cellRefract':['canonicalFactory3','3f181e358e4dbae130d79b5f0a8deabf1ae75464039ee58e87cf6be8cff7995b'],
 'classicNoisedeck/kaleido:kaleido':['canonicalFactory9','b3d50a77be2917e92330b69680bd5fa62b84e8347aee503ae38d19f10460efa2'],
}
const geometries=[{width:7,height:5,salt:3},{width:9,height:4,salt:7}]
const out={schema:'noisemaker-for-cpp.dynamic-kernel9-cpu9f3.v1',authority_revision:UPSTREAM_REVISION,cases:[]}
for(const effectId of ['classicNoisedeck/cellRefract','classicNoisedeck/kaleido']){
 const effect=effectRecords.find(x=>x.id===effectId)
 const key=`${effectId}:${effect.func}`
 const factory=canonicalKernelFactories[key]
 if(typeof factory!=='function'||kernelFactories.get(key)!==factory||Object.hasOwn(canonicalAdapterFactories,key))throw new Error('public canonical factory mismatch '+key)
 const factorySha=sha(Function.prototype.toString.call(factory))
 if(factory.name!==expectedFactories[key][0]||factorySha!==expectedFactories[key][1])throw new Error('canonical factory identity drift '+key)
 const defaults=Object.fromEntries(Object.values(effect.params).filter(p=>p.define).map(p=>[p.define,p.default]))
 const axes=[]
 for(const [name,p] of Object.entries(effect.params))if(p.define){
  for(const value of [...new Set(Object.values(p.choices??{}).filter(Number.isInteger))].sort((a,b)=>a-b))
   axes.push({axis:p.define,value,defines:{...defaults,[p.define]:value}})
 }
 axes.push({axis:'cross',value:1,defines:Object.fromEntries(Object.entries(defaults).map(([k,v])=>[k,k==='KERNEL'?1:k==='SHAPE'?6:k==='EFFECT'?4:k==='LOOP_OFFSET'?410:k==='DIRECTION'?0:k==='METRIC'?5:v]))})
 axes.push({axis:'cross',value:2,defines:Object.fromEntries(Object.entries(defaults).map(([k,v])=>[k,k==='KERNEL'?120:k==='SHAPE'?0:k==='LOOP_OFFSET'?300:k==='DIRECTION'?1:k==='METRIC'?2:v]))})
 for(const geometry of geometries)for(const axis of axes){
  const controls=effectId.endsWith('/cellRefract')
   ? {time:0.3,seed:7,scale:50,cellScale:75,cellSmooth:40,variation:30,speed:2,refractAmt:55,direction:90,wrap:1,effectWidth:4}
   : {time:0.375,seed:7,speed:2,loopScale:3,kaleido:3,effectWidth:4,wrap:true}
  const first=render(effect,factory,axis.defines,geometry,controls)
  const second=render(effect,factory,axis.defines,geometry,controls)
  if(first.output_f32_sha256!==second.output_f32_sha256||first.output_rgba8_sha256!==second.output_rgba8_sha256)throw new Error('nonrepeatable '+key+' '+JSON.stringify(axis))
  out.cases.push({key,factory_name:factory.name,factory_text_sha256:factorySha,
   axis:axis.axis,value:axis.value,defines:axis.defines,geometry,controls,...first})
 }
}
if(out.cases.length!==138)throw new Error('array runtime case census mismatch')
const includeLines=[
 '// Generated by tests/fixtures/array_runtime_reference.mjs from authenticated CPU source.',
 'namespace dynamic_kernel9_oracle {',
 'struct Case {',
 '  std::string_view key;',
 '  std::string_view axis;',
 '  std::int32_t axis_value;',
 '  std::size_t width, height, salt;',
 '  std::array<std::int32_t, 4> defines;',
 '  std::string_view input_f32_sha256, output_f32_sha256, output_rgba8_sha256;',
 '};',
 `inline constexpr std::array<Case, ${out.cases.length}> kCases{{`,
]
for(const c of out.cases){
 const d=c.defines
 const values=c.key.includes('/cellRefract:')?[d.KERNEL,d.SHAPE,0,0]:[d.DIRECTION,d.KERNEL,d.LOOP_OFFSET,d.METRIC]
 includeLines.push(`  {${JSON.stringify(c.key)}, ${JSON.stringify(c.axis)}, ${c.value}, ${c.geometry.width}U, ${c.geometry.height}U, ${c.geometry.salt}U, {${values.join(', ')}}, ${JSON.stringify(c.input_f32_sha256)}, ${JSON.stringify(c.output_f32_sha256)}, ${JSON.stringify(c.output_rgba8_sha256)}},`)
}
includeLines.push('}};','}  // namespace dynamic_kernel9_oracle')
const includeBytes=Buffer.from(includeLines.join('\n')+'\n')
const jsonBytes=Buffer.from(JSON.stringify(out,null,2)+'\n')
if(args['--write']){
 fs.mkdirSync(path.dirname(includePath),{recursive:true})
 fs.writeFileSync(includePath,includeBytes)
 if(jsonPath)fs.writeFileSync(jsonPath,jsonBytes)
}else{
 if(!fs.readFileSync(includePath).equals(includeBytes))throw new Error('array runtime include drift')
 if(jsonPath&&!fs.readFileSync(jsonPath).equals(jsonBytes))throw new Error('array runtime JSON drift')
}
console.log(`PASS ${out.cases.length} include=${sha(includeBytes)} json=${sha(jsonBytes)}`)
