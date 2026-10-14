import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..')
const argv=process.argv.slice(2)
const args={}
for(let i=0;i<argv.length;i++){
  const key=argv[i]
  if(key==='--write'||key==='--check'){
    if(args.mode)throw Error('one mode is required')
    args.mode=key
  }else if(key==='--cpu-root'||key==='--ledger'){
    if(i+1>=argv.length||args[key])throw Error(`${key} requires one value`)
    args[key]=argv[++i]
  }else throw Error(`unknown argument: ${key}`)
}
if(!args.mode||!args['--cpu-root']||!args['--ledger'])throw Error('--write or --check, --cpu-root, and --ledger are required')
const cpu=path.resolve(args['--cpu-root'])
const ledger=path.resolve(args['--ledger'])
const outputPath=path.join(repo,'tests/oracles/classic_shapes_runtime_expected.inc')
const key = 'classicNoisedeck/shapes:shapes'
const revision = '6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
const sourceSha = '28775b3e960c9051a320d48c7974792fbef33eaab80e5ca9aed5af43e8645d5e'
const sha = x => crypto.createHash('sha256').update(x).digest('hex')
const bytes = x => Buffer.from(x.buffer,x.byteOffset,x.byteLength)
const words = x => Array.from(new Uint32Array(x.buffer,x.byteOffset,x.byteLength/4),v=>`0x${v.toString(16).padStart(8,'0')}`)
const load = rel => import(pathToFileURL(path.join(cpu,rel)).href)
const {authenticateCpuRoot} = await import(pathToFileURL(path.join(repo,'tools/dsl/corpus_authority.mjs')).href)
authenticateCpuRoot(cpu,ledger)
const [{canonicalKernelFactories,kernelFactories,canonicalAdapterFactories}, {bindCanonicalKernel}, {runPass}, {Surface}, {UPSTREAM_REVISION}] = await Promise.all([
  load('src/effects/catalog.js'),load('src/csl/glsl-kernel.js'),load('src/runtime/pass-runner.js'),load('src/runtime/surface.js'),load('src/effects/generated/upstream-snapshot.js')])
if(process.version!=='v26.0.0'||UPSTREAM_REVISION!==revision)throw Error('CPU authority revision mismatch')
const factory=canonicalKernelFactories[key]
if(typeof factory!=='function'||factory.name!=='canonicalFactory16'||kernelFactories.get(key)!==factory||canonicalAdapterFactories[key]!==undefined)throw Error('factory route mismatch')
const corpus=path.join(repo,'tools/glslcpp/corpus',revision)
const source=path.join(corpus,'sources/classicNoisedeck/shapes/shapes.glsl')
if(sha(fs.readFileSync(source))!==sourceSha)throw Error('GLSL source mismatch')
const meta=JSON.parse(fs.readFileSync(path.join(corpus,'metadata.json'))).effects['classicNoisedeck/shapes']
const domain={}
for(const param of Object.values(meta.params))if(param.define)domain[param.define]=[...new Set(Object.values(param.choices).filter(Number.isInteger))].sort((a,b)=>a-b)
if(Object.keys(domain).sort().join()!=='LOOP_A_OFFSET,LOOP_B_OFFSET'||domain.LOOP_A_OFFSET.length!==25||domain.LOOP_B_OFFSET.length!==25)throw Error('define domain mismatch')
const existingOraclePath=path.join(repo,'docs/port-engineering/shapes-parity/shapes183-oracles.json')
const oracleBytes=fs.readFileSync(existingOraclePath)
const sidecar=fs.readFileSync(`${existingOraclePath}.sha256`,'utf8')
if(sidecar!==`${sha(oracleBytes)}  shapes183-oracles.json\n`)throw Error('Shapes183 input fixture sidecar mismatch')
const fixtures=JSON.parse(oracleBytes).render_cases
if(fixtures.length!==6||fixtures[0].name!=='oklab-palette-a'||fixtures[3].name!=='oklab-palette-negative-speed')throw Error('Shapes183 input fixture identity mismatch')
const inputs=[fixtures[0],fixtures[3]]
function input(fixture){
  const result={width:fixture.width,height:fixture.height}
  for(const [name,spec] of Object.entries(fixture.bindings)){
    result[name]=spec.abi==='Vec2'||spec.abi==='Vec3'?new Float32Array(spec.f32_values):spec.abi==='number'?Math.fround(spec.f32_value):spec.value
  }
  return result
}
function render(spec){
  const c=input(spec.fixture)
  const uniforms={LOOP_A_OFFSET:spec.defines.LOOP_A_OFFSET,LOOP_B_OFFSET:spec.defines.LOOP_B_OFFSET}
  for(const name of ['time','seed','wrap','loopAScale','loopBScale','speedA','speedB','paletteMode','paletteOffset','paletteAmp','paletteFreq','palettePhase','cyclePalette','rotatePalette','repeatPalette'])uniforms[name]=c[name]
  const before=JSON.stringify({uniforms,tileOffset:[...c.tileOffset],fullResolution:[...c.fullResolution]})
  const output=new Surface(c.width,c.height)
  runPass({kernel:bindCanonicalKernel(factory,{width:c.width,height:c.height,time:c.time,seed:c.seed,uniforms,tileOffset:c.tileOffset,fullResolution:c.fullResolution}),destination:output,time:0,seed:1})
  if(JSON.stringify({uniforms,tileOffset:[...c.tileOffset],fullResolution:[...c.fullResolution]})!==before)throw Error(`${spec.name}: mutated input`)
  const rgba=output.toRgba8()
  return {f32_sha256:sha(bytes(output.data)),rgba8_sha256:sha(bytes(rgba)),f32_words_le:words(output.data),rgba8_bytes:[...rgba]}
}
const requests=[{name:'default',defines:{LOOP_A_OFFSET:40,LOOP_B_OFFSET:30},fixture:inputs[0]}]
for(const value of domain.LOOP_A_OFFSET)requests.push({name:`A-${value}`,defines:{LOOP_A_OFFSET:value,LOOP_B_OFFSET:30},fixture:inputs[0]})
for(const value of domain.LOOP_B_OFFSET)requests.push({name:`B-${value}`,defines:{LOOP_A_OFFSET:40,LOOP_B_OFFSET:value},fixture:inputs[0]})
for(const [a,b] of [[300,350],[370,400],[200,210],[410,110]])requests.push({name:`cross-${a}-${b}`,defines:{LOOP_A_OFFSET:a,LOOP_B_OFFSET:b},fixture:inputs[1]})
const cases=requests.map(spec=>{
  const expected=render(spec),repeat=render(spec)
  if(JSON.stringify(expected)!==JSON.stringify(repeat))throw Error(`${spec.name}: repeat mismatch`)
  return {name:spec.name,defines:spec.defines,fixture_name:spec.fixture.name,width:spec.fixture.width,height:spec.fixture.height,expected,repeat_exact:true,input_unchanged:true}
})
if(cases.length!==55)throw Error('runtime case census mismatch')
const format=(values,suffix,perLine)=>values.reduce((lines,value,index)=>{
  if(index%perLine===0)lines.push('    ')
  lines[lines.length-1]+=`${value}${suffix}, `
  return lines
},[]).join('\n')
const lines=[
  '// Generated by tests/fixtures/classic_shapes_runtime_reference.mjs. Do not edit.',
  '#pragma once',
  'namespace classic_shapes_runtime_oracle {',
  'struct Case { std::string_view name; std::int32_t loop_a; std::int32_t loop_b; std::size_t fixture_index; std::size_t width; std::size_t height; std::span<const std::uint32_t> words; std::span<const std::uint8_t> rgba8; };',
  `inline constexpr std::string_view kSourceSha256 = "${sourceSha}";`,
  `inline constexpr std::string_view kFactorySha256 = "${sha(factory.toString())}";`,
  `inline constexpr std::string_view kLedgerSha256 = "${sha(fs.readFileSync(ledger))}";`,
  `inline constexpr std::array<std::int32_t,25> kLoopADomain{${domain.LOOP_A_OFFSET.map(x=>`${x}`).join(',')}};`,
  `inline constexpr std::array<std::int32_t,25> kLoopBDomain{${domain.LOOP_B_OFFSET.map(x=>`${x}`).join(',')}};`,
]
for(let index=0;index<cases.length;index++){
  const item=cases[index]
  if(item.expected.f32_words_le.length!==item.width*item.height*4||item.expected.rgba8_bytes.length!==item.expected.f32_words_le.length)throw Error(`${item.name}: lane count mismatch`)
  lines.push(`inline constexpr std::array<std::uint32_t,${item.expected.f32_words_le.length}> kWords${index}{`)
  lines.push(format(item.expected.f32_words_le,'U',8))
  lines.push('};')
  lines.push(`inline constexpr std::array<std::uint8_t,${item.expected.rgba8_bytes.length}> kRgba${index}{`)
  lines.push(format(item.expected.rgba8_bytes,'U',16))
  lines.push('};')
}
lines.push('inline constexpr std::array<Case,55> kCases{{')
for(let index=0;index<cases.length;index++){
  const item=cases[index]
  const fixtureIndex=fixtures.findIndex(x=>x.name===item.fixture_name)
  if(fixtureIndex<0)throw Error(`${item.name}: fixture not found`)
  lines.push(`  Case{"${item.name}",${item.defines.LOOP_A_OFFSET},${item.defines.LOOP_B_OFFSET},${fixtureIndex}U,${item.width}U,${item.height}U,kWords${index},kRgba${index}},`)
}
lines.push('}};','}  // namespace classic_shapes_runtime_oracle','')
const generated=lines.join('\n')
if(args.mode==='--write')fs.writeFileSync(outputPath,generated)
else if(fs.readFileSync(outputPath,'utf8')!==generated)throw Error('Classic Shapes runtime fixture drift')
console.log(JSON.stringify({mode:args.mode,cases:cases.length,domain_values:domain.LOOP_A_OFFSET.length,fixture_sha256:sha(generated),output:outputPath}))
