#!/usr/bin/env node
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import {pathToFileURL} from 'node:url'

const args={}
for(let i=2;i<process.argv.length;i++){
  const key=process.argv[i]
  if(key==='--write'||key==='--check'){
    if(args.mode)throw Error('one mode is required')
    args.mode=key
  }else if(['--repo','--cpu-root','--ledger','--output-inc'].includes(key)){
    if(args[key]||i+1>=process.argv.length)throw Error(`${key} requires one value`)
    args[key]=process.argv[++i]
  }else throw Error(`unknown argument: ${key}`)
}
if(!args.mode||['--repo','--cpu-root','--ledger','--output-inc'].some(k=>!args[k]))throw Error('mode, repo, cpu-root, ledger, and output-inc are required')
if(process.version!=='v26.0.0')throw Error('Node 26.0.0 is required')
const repo=path.resolve(args['--repo']),cpu=path.resolve(args['--cpu-root']),ledger=path.resolve(args['--ledger']),output=path.resolve(args['--output-inc'])
const sha=x=>crypto.createHash('sha256').update(x).digest('hex')
const bytes=x=>Buffer.from(x.buffer,x.byteOffset,x.byteLength)
const words=x=>Array.from(new Uint32Array(x.buffer,x.byteOffset,x.byteLength/4),v=>`0x${v.toString(16).padStart(8,'0')}`)
const load=rel=>import(pathToFileURL(path.join(cpu,rel)).href)
const {authenticateCpuRoot}=await import(pathToFileURL(path.join(repo,'tools/dsl/corpus_authority.mjs')).href)
authenticateCpuRoot(cpu,ledger)
const [{canonicalKernelFactories,kernelFactories,canonicalAdapterFactories},{effectRecords,UPSTREAM_REVISION},{bindCanonicalKernel},{runPass},{Surface}]=await Promise.all([
  load('src/effects/catalog.js'),load('src/effects/generated/upstream-snapshot.js'),load('src/csl/glsl-kernel.js'),load('src/runtime/pass-runner.js'),load('src/runtime/surface.js')])
const revision='6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
const sourceSha='b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316'
const factorySha='6d6adaeff42719de80378bbaf61d1f3c405dc24e34cae99b9354750582b66cd2'
const key='classicNoisedeck/effects:effects'
const factory=canonicalKernelFactories[key]
if(UPSTREAM_REVISION!==revision||factory?.name!=='canonicalFactory7'||kernelFactories.get(key)!==factory||Object.hasOwn(canonicalAdapterFactories,key)||sha(factory.toString())!==factorySha)throw Error('CPU factory identity drift')
const source=path.join(repo,'tools/glslcpp/corpus',revision,'sources/classicNoisedeck/effects/effects.glsl')
if(sha(fs.readFileSync(source))!==sourceSha)throw Error('GLSL source drift')
const metadata=JSON.parse(fs.readFileSync(path.join(repo,'tools/glslcpp/corpus',revision,'metadata.json'))).effects['classicNoisedeck/effects']
const live=effectRecords.find(x=>x.id==='classicNoisedeck/effects')
const orderedChoices=x=>Object.entries(x).sort(([a],[b])=>a.localeCompare(b))
if(!live||live.func!=='effects'||JSON.stringify(orderedChoices(metadata.params.effect.choices))!==JSON.stringify(orderedChoices(live.params.effect.choices))||JSON.stringify(orderedChoices(metadata.params.flip.choices))!==JSON.stringify(orderedChoices(live.params.flip.choices)))throw Error('metadata enum drift')
const domain=name=>[...new Set(Object.values(metadata.params[name].choices).filter(Number.isInteger))].sort((a,b)=>a-b)
const effects=domain('effect'),flips=domain('flip')
if(effects.join()!=='0,1,2,3,4,5,6,7,8,9,100,110,120,200,210,220,230,300,301'||flips.join()!=='0,1,2,3,11,12,13,14,15,16,17,18')throw Error('declared enum domain drift')
const fixtures=[
  {name:'full-nonsquare',w:7,h:5,iw:7,ih:5,t:2,tile:[0,0],full:[7,5],rotation:37,scaleAmt:75,offsetX:23,offsetY:-17,time:1.25},
  {name:'offset-tile',w:4,h:3,iw:9,ih:8,t:7,tile:[2,3],full:[9,8],rotation:-28,scaleAmt:140,offsetX:-31,offsetY:26,time:2.5},
  {name:'zero-offset-full-mismatch',w:4,h:3,iw:9,ih:8,t:7,tile:[0,0],full:[9,8],rotation:-28,scaleAmt:140,offsetX:-31,offsetY:26,time:2.5},
  {name:'offset-tile-zoom-clamp',w:4,h:3,iw:600,ih:600,t:7,tile:[3000,2200],full:[4096,3072],effectAmt:20,rotation:0,scaleAmt:100,offsetX:0,offsetY:0,time:2.5},
]
function makeInput(f){
  const data=new Float32Array(f.iw*f.ih*4)
  for(let y=0;y<f.ih;y++)for(let x=0;x<f.iw;x++){
    const i=(y*f.iw+x)*4
    data[i]=((3*x+5*y+f.t)%16)/16
    data[i+1]=((x+2*y+f.t)%8)/8
    data[i+2]=((5*x+y+f.t)%32)/32
    data[i+3]=1
  }
  return new Surface(f.iw,f.ih,data)
}
function render(spec,activeFactory=factory){
  const f=fixtures[spec.fixture],tex=makeInput(f),before=bytes(tex.data).toString('hex')
  const tileOffset=new Float32Array(f.tile),fullResolution=new Float32Array(f.full)
  const uniforms={EFFECT:spec.effect,FLIP:spec.flip,renderScale:1,time:Math.fround(f.time),effectAmt:f.effectAmt??1,scaleAmt:Math.fround(f.scaleAmt),rotation:Math.fround(f.rotation),offsetX:Math.fround(f.offsetX),offsetY:Math.fround(f.offsetY),intensity:20,saturation:-15}
  const uniformsBefore=JSON.stringify(uniforms),tileBefore=bytes(tileOffset).toString('hex'),fullBefore=bytes(fullResolution).toString('hex')
  const destination=new Surface(f.w,f.h)
  runPass({kernel:bindCanonicalKernel(activeFactory,{width:f.w,height:f.h,time:f.time,seed:1,tileOffset,fullResolution,textures:{inputTex:tex},uniforms}),destination,time:0,seed:1})
  if(bytes(tex.data).toString('hex')!==before||JSON.stringify(uniforms)!==uniformsBefore||bytes(tileOffset).toString('hex')!==tileBefore||bytes(fullResolution).toString('hex')!==fullBefore)throw Error(`${spec.name}: input mutation`)
  const rgba=destination.toRgba8()
  return {words:words(destination.data),rgba:[...rgba],f32_sha256:sha(bytes(destination.data)),rgba8_sha256:sha(bytes(rgba))}
}
const requests=[]
for(let fixture=0;fixture<2;fixture++){
  for(const effect of effects)requests.push({name:`${fixtures[fixture].name}-effect-${effect}`,effect,flip:0,fixture})
  for(const flip of flips)requests.push({name:`${fixtures[fixture].name}-flip-${flip}`,effect:0,flip,fixture})
}
for(const [effect,flip] of [[230,18],[220,11],[300,15],[301,16],[210,17],[100,13],[8,3],[120,2]])requests.push({name:`cross-${effect}-${flip}`,effect,flip,fixture:requests.length%2})
requests.push({name:'zero-offset-full-mismatch-zoomblur',effect:230,flip:0,fixture:2})
requests.push({name:'offset-tile-zoom-clamp-zoomblur',effect:230,flip:0,fixture:3})
const cases=requests.map(spec=>{
  const first=render(spec),second=render(spec)
  if(JSON.stringify(first)!==JSON.stringify(second))throw Error(`${spec.name}: repeat mismatch`)
  const f=fixtures[spec.fixture]
  if(first.words.length!==f.w*f.h*4||first.rgba.length!==f.w*f.h*4)throw Error(`${spec.name}: output extent mismatch`)
  return {...spec,...first}
})
const clampNeedle='min(max(tapB, new $runtime.PooledFloat32Array([-tapBudget[0], -tapBudget[1]])), tapBudget).reduce((res,el,i)=>(res[i] = el, res), tapB);'
const originalFactoryText=Function.prototype.toString.call(factory)
if(originalFactoryText.split(clampNeedle).length!==2)throw Error('exact zoomBlur clamp site census drift')
const noClampFactory=(0,eval)(`(${originalFactoryText.replace(clampNeedle,'tapB;')})`)
const clampSpec={name:'offset-tile-zoom-clamp-zoomblur',effect:230,flip:0,fixture:3}
const zeroSpec={name:'zero-offset-full-mismatch-zoomblur',effect:230,flip:0,fixture:2}
const originalClamp=render(clampSpec),withoutClamp=render(clampSpec,noClampFactory)
const originalZero=render(zeroSpec),mutantZero=render(zeroSpec,noClampFactory)
const clampChangedWords=originalClamp.words.filter((word,i)=>word!==withoutClamp.words[i]).length
const clampChangedRgba=originalClamp.rgba.filter((byte,i)=>byte!==withoutClamp.rgba[i]).length
if(!clampChangedWords||!clampChangedRgba||JSON.stringify(originalZero)!==JSON.stringify(mutantZero))throw Error('tile clamp source-reversion control did not distinguish the active branch')
if(JSON.stringify(originalClamp)!==JSON.stringify(render(clampSpec))||JSON.stringify(withoutClamp)!==JSON.stringify(render(clampSpec,noClampFactory)))throw Error('tile clamp source-reversion control did not repeat')
if(cases.length!==72)throw Error('case census drift')
const lines=[
  '// Generated by tests/fixtures/effects_runtime_reference.mjs from authenticated CPU4307. Do not edit.',
  '#pragma once',
  'namespace effects_runtime_oracle {',
  'struct Case { std::string_view name; int effect; int flip; std::size_t fixture; std::span<const std::uint32_t> words; std::span<const std::uint8_t> rgba; };',
  `inline constexpr std::string_view kSourceSha256="${sourceSha}";`,
  `inline constexpr std::string_view kFactorySha256="${factorySha}";`,
  `inline constexpr std::string_view kLedgerSha256="${sha(fs.readFileSync(ledger))}";`,
  `inline constexpr std::array<int,${effects.length}> kEffects{${effects.join(',')}};`,
  `inline constexpr std::array<int,${flips.length}> kFlips{${flips.join(',')}};`,
]
for(let i=0;i<cases.length;i++){
  const c=cases[i]
  lines.push(`inline constexpr std::array<std::uint32_t,${c.words.length}> kWords${i}{${c.words.map(x=>`${x}U`).join(',')}};`)
  lines.push(`inline constexpr std::array<std::uint8_t,${c.rgba.length}> kRgba${i}{${c.rgba.map(x=>`${x}U`).join(',')}};`)
}
lines.push(`inline constexpr std::array<Case,${cases.length}> kCases{{`)
for(let i=0;i<cases.length;i++){
  const c=cases[i]
  lines.push(`  Case{"${c.name}",${c.effect},${c.flip},${c.fixture}U,kWords${i},kRgba${i}},`)
}
lines.push('}};','}  // namespace effects_runtime_oracle','')
const generated=lines.join('\n')
if(args.mode==='--write')fs.writeFileSync(output,generated)
else if(fs.readFileSync(output,'utf8')!==generated)throw Error('Effects runtime oracle drift')
console.log(JSON.stringify({mode:args.mode,cases:cases.length,effects:effects.length,flips:flips.length,fixture_geometries:fixtures.map(f=>[f.w,f.h,f.iw,f.ih]),clamp_source_reversion_changed_words:clampChangedWords,clamp_source_reversion_changed_rgba:clampChangedRgba,zero_offset_control_equal:true,output,sha256:sha(generated)}))
