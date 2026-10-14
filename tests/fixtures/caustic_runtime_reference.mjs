import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
const [repo, authority, ledger, outputPath] = process.argv.slice(2)
if (![repo, authority, ledger, outputPath].every(value => value && path.isAbsolute(value))) throw Error('usage: node script.mjs ABS_REPO ABS_CPU_ROOT ABS_LEDGER ABS_OUTPUT')
const { authenticateCpuRoot, EXPECTED } = await import(pathToFileURL(path.join(repo, 'tools/dsl/corpus_authority.mjs')).href)

const root = authenticateCpuRoot(authority, ledger)
const load = relative => import(pathToFileURL(path.join(root, relative)).href)
const { canonicalKernelFactories, canonicalAdapterFactories, kernelFactories } = await load('src/effects/catalog.js')
const { effectRecords } = await load('src/effects/generated/upstream-snapshot.js')
const { bindCanonicalKernel } = await load('src/csl/glsl-kernel.js')
const { runPass } = await load('src/runtime/pass-runner.js')
const { Surface } = await load('src/runtime/surface.js')
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const bytes = array => Buffer.from(array.buffer, array.byteOffset, array.byteLength)
const key = 'classicNoisedeck/caustic:caustic'
const factory = canonicalKernelFactories[key]
if (typeof factory !== 'function' || kernelFactories.get(key) !== factory || canonicalAdapterFactories[key] !== undefined) throw Error('canonical factory identity mismatch')
const effect = effectRecords.find(item => item.id === 'classicNoisedeck/caustic')
const declaredChoices = effect?.params?.interp?.choices
const expectedChoices = {constant:0,linear:1,hermite:2,catmullRom3x3:3,catmullRom4x4:4,bSpline3x3:5,bSpline4x4:6,simplex:10,sine:11}
if (JSON.stringify(declaredChoices) !== JSON.stringify(expectedChoices) || effect.params.interp.define !== 'NOISE_TYPE') throw Error('declared choices drift')
const sourcePath = path.join(repo, 'tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources/classicNoisedeck/caustic/caustic.glsl')
const sourceSha256 = hash(fs.readFileSync(sourcePath))
if (sourceSha256 !== '161cb6114f312a223d88a5c60a3ecb694a4c8766fca91b3fc47ae92078f2a00d') throw Error('current corpus source drift')
const width = 8, height = 8
const configs = [
  {name:'default-wrap',wrap:true,noiseScale:85,speed:25,seed:44,hueRotation:180,hueRange:25,intensity:0,time:Math.fround(.375),tileOffset:[0,0],fullResolution:[8,8]},
  {name:'offset-no-wrap',wrap:false,noiseScale:37,speed:63,seed:17,hueRotation:37,hueRange:74,intensity:22,time:Math.fround(.625),tileOffset:[3,-2],fullResolution:[13,11]},
]
const cases = []
for (const [modeName, noiseType] of Object.entries(declaredChoices)) {
  for (const config of configs) {
    const uniforms = {NOISE_TYPE:noiseType,wrap:config.wrap,noiseScale:config.noiseScale,speed:config.speed,seed:config.seed,hueRotation:config.hueRotation,hueRange:config.hueRange,intensity:config.intensity}
    const tileOffset = new Float32Array(config.tileOffset)
    const fullResolution = new Float32Array(config.fullResolution)
    const inputBefore = JSON.stringify({uniforms,tileOffset:Array.from(tileOffset),fullResolution:Array.from(fullResolution),config})
    function render() {
      const kernel = bindCanonicalKernel(factory,{width,height,time:config.time,frame:23,deltaTime:Math.fround(1/60),seed:config.seed,uniforms,tileOffset,fullResolution,textures:{}})
      const destination = new Surface(width,height)
      runPass({kernel,destination,time:config.time,seed:config.seed})
      return destination
    }
    const first = render(), second = render()
    const f32 = hash(bytes(first.data)), rgba8 = hash(first.toRgba8())
    if (f32 !== hash(bytes(second.data)) || rgba8 !== hash(second.toRgba8())) throw Error(`nonrepeatable ${modeName} ${config.name}`)
    const inputAfter = JSON.stringify({uniforms,tileOffset:Array.from(tileOffset),fullResolution:Array.from(fullResolution),config})
    if (inputBefore !== inputAfter) throw Error(`mutated inputs ${modeName} ${config.name}`)
    cases.push({mode_name:modeName,noise_type:noiseType,configuration:config.name,uniforms:{...uniforms},time:config.time,tile_offset:[...tileOffset],full_resolution:[...fullResolution],f32_sha256:f32,rgba8_sha256:rgba8,first_pixel:Array.from(first.data.slice(0,4)),nonfinite_channels:Array.from(first.data).filter(value=>!Number.isFinite(value)).length,input_sha256:hash(Buffer.from(inputBefore))})
  }
}
const output = {authority_root:root,authority_revision:EXPECTED.upstreamRevision,ledger_sha256:hash(fs.readFileSync(ledger)),source_sha256:sourceSha256,factory_name:factory.name,factory_sha256:hash(Buffer.from(Function.prototype.toString.call(factory))),width,height,declared_choices:declaredChoices,cases}
fs.writeFileSync(outputPath,JSON.stringify(output,null,2)+'\n')
console.log(`PASS authenticated CPU ${Object.keys(declaredChoices).length} modes ${cases.length} cases repeated twice; inputs unchanged`)
