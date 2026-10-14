import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const cppRoot = process.cwd()
const cpuRoot = process.env.NOISEMAKER_CPU_ROOT
if (!cpuRoot) throw new Error('NOISEMAKER_CPU_ROOT is required')
const ledger = process.env.NOISEMAKER_CPU_LEDGER ?? `${cpuRoot}.ledger.sha256`
const outputPath = process.env.NOISEMAKER_ORACLE_OUTPUT
const revision = '6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d'
const key = 'synth/shape:shape'
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength)
const words = value => Array.from(new Uint32Array(value.buffer, value.byteOffset, value.byteLength / 4),
  x => `0x${(x >>> 0).toString(16).padStart(8, '0')}`)
const f = Math.fround

const {authenticateCpuRoot} = await import(pathToFileURL(path.join(cppRoot, 'tools/dsl/corpus_authority.mjs')).href)
authenticateCpuRoot(cpuRoot, ledger)
const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{canonicalKernelFactories, canonicalAdapterFactories, kernelFactories},
  {bindCanonicalKernel}, {runPass}, {Surface}, {UPSTREAM_REVISION}] = await Promise.all([
  load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'),
  load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'),
  load('src/effects/generated/upstream-snapshot.js'),
])
if (process.version !== 'v26.0.0' || UPSTREAM_REVISION !== revision) {
  throw new Error('CPU runtime/source revision mismatch')
}
const factory = canonicalKernelFactories[key]
const sourcePath = path.join(cppRoot, 'tools/glslcpp/corpus', revision, 'sources/synth/shape/shape.glsl')
const sourceSha = 'd917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f'
if (typeof factory !== 'function' || factory.name !== 'canonicalFactory285' ||
    kernelFactories.get(key) !== factory || canonicalAdapterFactories[key] !== undefined ||
    sha(fs.readFileSync(sourcePath)) !== sourceSha) {
  throw new Error('Shape canonical factory/source identity mismatch')
}
const metadata = JSON.parse(fs.readFileSync(path.join(cppRoot, 'tools/glslcpp/corpus', revision, 'metadata.json')))
const effect = metadata.effects['synth/shape']
if (!effect || effect.passes.length !== 1 || effect.passes[0].key !== key) {
  throw new Error('Shape metadata/pass identity mismatch')
}
const domain = {}
for (const parameter of Object.values(effect.params)) {
  if (!parameter.define) continue
  domain[parameter.define] = [...new Set(Object.values(parameter.choices).filter(Number.isInteger))].sort((a,b)=>a-b)
}
if (Object.keys(domain).sort().join() !== 'LOOP_A_OFFSET,LOOP_B_OFFSET' ||
    JSON.stringify(domain.LOOP_A_OFFSET) !== JSON.stringify(domain.LOOP_B_OFFSET) ||
    !domain.LOOP_A_OFFSET.includes(40) || !domain.LOOP_B_OFFSET.includes(30)) {
  throw new Error('Shape declared define domain mismatch')
}
const base = {geometry:'base',width:16,height:9,tileOffset:[2,1],fullResolution:[22,15],
  time:0.375,seed:7,wrap:true,loopAScale:37,loopBScale:61,speedA:50,speedB:-25}
const alternate = {geometry:'alternate',width:11,height:7,tileOffset:[0,0],fullResolution:[11,7],
  time:-1.25,seed:13,wrap:false,loopAScale:20,loopBScale:75,speedA:-60,speedB:80}
const requests = []
requests.push({name:'default',dimension:'default',defines:{LOOP_A_OFFSET:40,LOOP_B_OFFSET:30},controls:base})
for (const value of domain.LOOP_A_OFFSET) requests.push({name:`A-${value}`,dimension:'LOOP_A_OFFSET',
  defines:{LOOP_A_OFFSET:value,LOOP_B_OFFSET:30},controls:base})
for (const value of domain.LOOP_B_OFFSET) requests.push({name:`B-${value}`,dimension:'LOOP_B_OFFSET',
  defines:{LOOP_A_OFFSET:40,LOOP_B_OFFSET:value},controls:base})
for (const [a,b] of [[300,350],[370,400],[200,210],[410,110]]) {
  requests.push({name:`cross-${a}-${b}`,dimension:'cross',
    defines:{LOOP_A_OFFSET:a,LOOP_B_OFFSET:b},controls:alternate})
}
function render(spec) {
  const c = spec.controls
  const tileOffset = new Float32Array(c.tileOffset.map(f))
  const fullResolution = new Float32Array(c.fullResolution.map(f))
  const uniforms = {LOOP_A_OFFSET:spec.defines.LOOP_A_OFFSET,LOOP_B_OFFSET:spec.defines.LOOP_B_OFFSET,
    time:f(c.time),seed:c.seed,wrap:c.wrap,loopAScale:f(c.loopAScale),loopBScale:f(c.loopBScale),
    speedA:f(c.speedA),speedB:f(c.speedB)}
  const inputBefore = JSON.stringify({uniforms,tileOffset:[...tileOffset],fullResolution:[...fullResolution]})
  const destination = new Surface(c.width,c.height)
  const options = {width:c.width,height:c.height,time:f(c.time),seed:c.seed,uniforms,tileOffset,fullResolution}
  runPass({kernel:bindCanonicalKernel(factory,options),destination})
  if (JSON.stringify({uniforms,tileOffset:[...tileOffset],fullResolution:[...fullResolution]}) !== inputBefore) {
    throw new Error(`${spec.name}: input bindings mutated`)
  }
  const rgba = destination.toRgba8()
  if (destination.data.length !== c.width*c.height*4 || rgba.length !== destination.data.length) {
    throw new Error(`${spec.name}: output extent mismatch`)
  }
  return {f32_sha256:sha(bytes(destination.data)),rgba8_sha256:sha(bytes(rgba)),
    f32_words_le:words(destination.data),rgba8_bytes:[...rgba]}
}
const cases = requests.map(spec => {
  const first=render(spec),second=render(spec)
  if (JSON.stringify(first)!==JSON.stringify(second)) throw new Error(`${spec.name}: repeat mismatch`)
  return {...spec,expected:first,repeat_exact:true,inputs_unchanged:true}
})
for (const name of ['LOOP_A_OFFSET','LOOP_B_OFFSET']) {
  const observed=cases.filter(c=>c.dimension===name).map(c=>c.defines[name]).sort((a,b)=>a-b)
  if(JSON.stringify(observed)!==JSON.stringify(domain[name])) throw new Error(`${name}: enum coverage mismatch`)
}
const data={schema:'noisemaker-for-cpp.shape.runtime-cpu-oracle.v1',cpu_revision:'9f3bd6a',
  upstream_revision:UPSTREAM_REVISION,node_version:process.version,
  authority_ledger_sha256:sha(fs.readFileSync(ledger)),program_key:key,
  source_sha256:sourceSha,factory_name:factory.name,factory_text_sha256:sha(factory.toString()),
  define_domains:domain,exactness:'all raw Float32 words and RGBA8 bytes; no tolerance',cases}
if (outputPath) fs.writeFileSync(outputPath,JSON.stringify(data,null,2)+'\n')
else process.stdout.write(JSON.stringify(data,null,2)+'\n')
