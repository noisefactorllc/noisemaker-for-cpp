#!/usr/bin/env node
// Canonical exact-pixel oracle for synth/mandelbrot:mandelbrot.
// The only executable authority is the public canonical factory from the
// caller-supplied immutable noisemaker-for-cpu snapshot.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const generatorPath = fileURLToPath(import.meta.url)
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'mandelbrot-oracles.json')
const reportPath = path.join(here, 'mandelbrot-oracle-report.md')
const includeGeneratorPath = path.join(cppRoot, 'tools/glslcpp/generate_mandelbrot_native_oracle_include.py')
const programKey = 'synth/mandelbrot:mandelbrot'
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/mandelbrot/mandelbrot.glsl'
const sourceSha256 = '0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615'
const factoryName = 'canonicalFactory252'
const factoryTextSha256 = '27b87c62a87c73d76e5a1d2d6096cecaa6714aeba3f26f72a03698592918ee29'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevision = '117a236679d1db3ab8f0e278230ece277b57564c'
const expectedClosure = Object.freeze([
  ['src/csl/glsl-kernel.js','a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  ['src/csl/glsl-runtime.js','a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  ['src/csl/runtime.js','a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee'],
  ['src/effects/adapters/bit-effects.js','5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7'],
  ['src/effects/adapters/crt.js','c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc'],
  ['src/effects/adapters/f32-color.js','b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046'],
  ['src/effects/adapters/fractal.js','0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29'],
  ['src/effects/adapters/index.js','40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  ['src/effects/adapters/julia.js','0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5'],
  ['src/effects/adapters/median.js','e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583'],
  ['src/effects/adapters/palette.js','8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'],
  ['src/effects/adapters/snow.js','202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366'],
  ['src/effects/catalog.js','d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  ['src/effects/definition.js','fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02'],
  ['src/effects/generated/canonical-adapter-data.js','ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab'],
  ['src/effects/generated/canonical-kernels.js','66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  ['src/effects/generated/kernels.js','b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01'],
  ['src/effects/generated/upstream-snapshot.js','e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
  ['src/effects/registry.js','8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'],
  ['src/runtime/pass-runner.js','fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  ['src/runtime/sampler.js','1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328'],
  ['src/runtime/surface.js','0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
])
const bindingNames = ['resolution','tileOffset','fullResolution','time','poi','outputMode','iterations','centerHiX','centerHiY','centerLoX','centerLoY','zoomSpeed','zoomDepth','invert','stripeFreq','trapShape','lightAngle','rotation']
const bindingAbi = { resolution:'Vec2', tileOffset:'Vec2', fullResolution:'Vec2', time:'number', poi:'int32', outputMode:'int32', iterations:'int32', centerHiX:'number', centerHiY:'number', centerLoX:'number', centerLoY:'number', zoomSpeed:'number', zoomDepth:'number', invert:'number', stripeFreq:'number', trapShape:'int32', lightAngle:'number', rotation:'number' }
const f = Math.fround
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const stable = value => JSON.stringify(value, null, 2) + '\n'
const words = view => Array.from(new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4), n => `0x${n.toString(16).padStart(8,'0')}`)
const packWords = values => { const b = Buffer.alloc(values.length * 4); values.forEach((v,i) => b.writeUInt32LE(Number.parseInt(v,16) >>> 0, i*4)); return b }
const digestWords = values => sha256(packWords(values))
const digestBytes = values => sha256(Buffer.from(values))
const same = (a,b) => a.length === b.length && a.every((v,i) => v === b[i])
const changed = (a,b) => a.reduce((n,v,i) => n + (v !== b[i] ? 1 : 0), 0)
const firstMismatch = (expected, actual) => { const index=expected.findIndex((value,i)=>value!==actual[i]); return index<0 ? null : {index,expected:expected[index],actual:actual[index]} }
function compareExact(expected, actual, label='comparison') {
  if (expected.width !== actual.width || expected.height !== actual.height) throw new Error(`${label}: dimensions mismatch`)
  const count = expected.width * expected.height * 4
  if (!Array.isArray(expected.f32_words_le) || !Array.isArray(actual.f32_words_le) || expected.f32_words_le.length !== count || actual.f32_words_le.length !== count) throw new Error(`${label}: Float32 lane count mismatch`)
  if (!Array.isArray(expected.rgba8_bytes) || !Array.isArray(actual.rgba8_bytes) || expected.rgba8_bytes.length !== count || actual.rgba8_bytes.length !== count) throw new Error(`${label}: RGBA8 byte count mismatch`)
  for (let i=0;i<count;i += 1) if (expected.f32_words_le[i] !== actual.f32_words_le[i]) throw new Error(`${label}: Float32 first mismatch at lane ${i}`)
  for (let i=0;i<count;i += 1) if (expected.rgba8_bytes[i] !== actual.rgba8_bytes[i]) throw new Error(`${label}: RGBA8 first mismatch at byte ${i}`)
  return true
}
const beneath = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`)
function rejectAbsolute(value, label='document') {
  if (typeof value === 'string') { if (/^(?:[A-Za-z]:[\\/]|\\\\|\/)/.test(value) || /(?:^|[\\/])(?:Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute-looking string`); return }
  if (Array.isArray(value)) value.forEach((v,i) => rejectAbsolute(v, `${label}[${i}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([k,v]) => rejectAbsolute(v, `${label}.${k}`))
}
function checked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(`${target}.sha256`, `${sha256(payload)}  ${path.basename(target)}\n`) }
function verify(target) { const payload = fs.readFileSync(target); const side = fs.readFileSync(`${target}.sha256`, 'utf8'); if (side !== `${sha256(payload)}  ${path.basename(target)}\n`) throw new Error(`sidecar drift: ${target}`); return payload }

const argv = process.argv.slice(2)
const mode = argv.filter(x => ['--write','--check','--self-test'].includes(x))
if (mode.length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || ci + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
if (argv.some((x,i) => i !== ci && i !== ci+1 && x !== mode[0])) throw new Error('unexpected argument')
const cpuArg = argv[ci+1]
if (!fs.existsSync(cpuArg) || !fs.statSync(cpuArg).isDirectory()) throw new Error('--cpu-root is not a directory')
const cpuRoot = fs.realpathSync(cpuArg)
const liveArg = process.env.NOISEMAKER_FOR_CPU || path.resolve(cppRoot, '../noisemaker-for-cpu')
const liveRoot = fs.existsSync(liveArg) ? fs.realpathSync(liveArg) : null
if (liveRoot && (beneath(liveRoot,cpuRoot) || beneath(cpuRoot,liveRoot))) throw new Error('--cpu-root must be an immutable snapshot, never the live checkout')
if (beneath(cppRoot,cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')

function closure() {
  const patterns = [/\bfrom\s*['"]([^'"\n]+)['"]/g, /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g, /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm]
  const entries = ['src/effects/catalog.js','src/effects/generated/upstream-snapshot.js','src/csl/glsl-kernel.js','src/csl/glsl-runtime.js','src/runtime/pass-runner.js','src/runtime/surface.js']
  const stack = entries.map(x => path.join(cpuRoot,x)); const seen = new Map()
  while (stack.length) {
    const candidate = fs.realpathSync(stack.pop()); if (seen.has(candidate)) continue
    if (!beneath(cpuRoot,candidate) || (liveRoot && beneath(liveRoot,candidate))) throw new Error('import escaped immutable snapshot')
    const payload = fs.readFileSync(candidate); seen.set(candidate,sha256(payload)); const text = payload.toString('utf8')
    if (/\bimport\s*\(\s*(?!['"])/.test(text)) throw new Error(`nonliteral dynamic import: ${path.relative(cpuRoot,candidate)}`)
    for (const pattern of patterns) { pattern.lastIndex = 0; let m; while ((m = pattern.exec(text))) { const spec = m[1]; if (spec.startsWith('node:')) continue; if (!spec.startsWith('./')&&!spec.startsWith('../')&&!spec.startsWith('/')) throw new Error(`bare module specifier ${spec}`); const resolved = fs.realpathSync(spec.startsWith('/') ? spec : path.resolve(path.dirname(candidate),spec)); stack.push(resolved) } }
  }
  return [...seen].map(([file,hash]) => [path.relative(cpuRoot,file),hash]).sort((a,b) => a[0].localeCompare(b[0]))
}
const actualClosure = closure()
if (JSON.stringify(actualClosure) !== JSON.stringify([...expectedClosure].sort((a,b) => a[0].localeCompare(b[0])))) throw new Error(`CPU import closure mismatch: ${JSON.stringify(actualClosure)}`)
for (const [rel,expected] of expectedClosure) if (sha256(fs.readFileSync(path.join(cpuRoot,rel))) !== expected) throw new Error(`pinned CPU provenance drift: ${rel}`)
const sourcePayload = fs.readFileSync(path.join(cppRoot,sourceRelative)); if (sha256(sourcePayload) !== sourceSha256) throw new Error('mandelbrot corpus source provenance drift')
const load = rel => import(pathToFileURL(fs.realpathSync(path.join(cpuRoot,rel))).href)
const [{ canonicalKernelFactories, kernelFactories }, { UPSTREAM_REVISION }, { bindCanonicalKernel }, { runPass }, { Surface }] = await Promise.all([load('src/effects/catalog.js'),load('src/effects/generated/upstream-snapshot.js'),load('src/csl/glsl-kernel.js'),load('src/runtime/pass-runner.js'),load('src/runtime/surface.js')])
const canonicalFactory = canonicalKernelFactories[programKey]; const publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== factoryName) throw new Error('canonical factory identity drift')
if (publicFactory !== canonicalFactory) throw new Error('public factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call((await load('src/effects/catalog.js')).canonicalAdapterFactories, programKey)) throw new Error('mandelbrot is adapter-routed')
if (UPSTREAM_REVISION !== upstreamRevision) throw new Error('upstream revision drift')
if (sha256(Function.prototype.toString.call(canonicalFactory)) !== factoryTextSha256) throw new Error('canonical factory text drift')

function syntheticInput(width,height,salt) { const s = new Surface(width,height); for (let y=0;y<height;y++) for (let x=0;x<width;x++) { const i=(y*width+x)*4; s.data[i]=f(((x*3+y*5+salt)%17)/16); s.data[i+1]=f(((x*7+y*2+salt)%19)/18); s.data[i+2]=f(((x*11+y*13+salt)%23)/22); s.data[i+3]=f(1) } return s }
const cases = [
  {name:'manual-smooth',width:5,height:4,time:.25,poi:0,outputMode:0,iterations:80,centerHiX:-.75,centerHiY:0,centerLoX:0,centerLoY:0,zoomSpeed:0,zoomDepth:1,invert:0,stripeFreq:0,trapShape:0,lightAngle:30,rotation:0,tileX:0,tileY:0,salt:1},
  {name:'manual-distance-tile',width:4,height:5,time:.75,poi:0,outputMode:1,iterations:120,centerHiX:-.743643887,centerHiY:.131825904,centerLoX:0,centerLoY:0,zoomSpeed:0,zoomDepth:4,invert:0,stripeFreq:0,trapShape:0,lightAngle:60,rotation:12,tileX:.5,tileY:-.25,salt:2},
  {name:'poi-stripe',width:6,height:3,time:1.5,poi:2,outputMode:2,iterations:90,centerHiX:0,centerHiY:0,centerLoX:0,centerLoY:0,zoomSpeed:0,zoomDepth:3,invert:1,stripeFreq:2.75,trapShape:1,lightAngle:120,rotation:0,tileX:0,tileY:0,salt:3},
  {name:'poi-trap',width:5,height:5,time:2,poi:7,outputMode:3,iterations:150,centerHiX:0,centerHiY:0,centerLoX:0,centerLoY:0,zoomSpeed:1.25,zoomDepth:8,invert:0,stripeFreq:0,trapShape:2,lightAngle:210,rotation:0,tileX:-.375,tileY:.625,salt:4},
  {name:'manual-normal',width:4,height:4,time:3.25,poi:0,outputMode:4,iterations:64,centerHiX:-1.4,centerHiY:.01,centerLoX:2e-8,centerLoY:-3e-8,zoomSpeed:0,zoomDepth:2,invert:0,stripeFreq:0,trapShape:0,lightAngle:300,rotation:-18,tileX:0,tileY:0,salt:5},
  {name:'manual-trap-escape',width:4,height:3,time:.5,poi:0,outputMode:3,iterations:64,centerHiX:.3,centerHiY:.4,centerLoX:0,centerLoY:0,zoomSpeed:0,zoomDepth:1,invert:0,stripeFreq:0,trapShape:0,lightAngle:45,rotation:0,tileX:0,tileY:0,salt:7},
  {name:'period-bulb-control',width:3,height:3,time:0,poi:0,outputMode:0,iterations:32,centerHiX:0,centerHiY:0,centerLoX:0,centerLoY:0,zoomSpeed:0,zoomDepth:0,invert:0,stripeFreq:0,trapShape:0,lightAngle:0,rotation:0,tileX:0,tileY:0,salt:6},
]
function render(spec, override={}, factory=canonicalFactory) { const v={...spec,...override}; const input=syntheticInput(v.width,v.height,v.salt); const before=new Uint32Array(input.data.buffer.slice(0)); const uniforms={resolution:new Float32Array([v.width,v.height]),tileOffset:new Float32Array([v.tileX,v.tileY]),fullResolution:new Float32Array([v.width,v.height]),time:f(v.time),poi:v.poi|0,outputMode:v.outputMode|0,iterations:v.iterations|0,centerHiX:f(v.centerHiX),centerHiY:f(v.centerHiY),centerLoX:f(v.centerLoX),centerLoY:f(v.centerLoY),zoomSpeed:f(v.zoomSpeed),zoomDepth:f(v.zoomDepth),invert:f(v.invert),stripeFreq:f(v.stripeFreq),trapShape:v.trapShape|0,lightAngle:f(v.lightAngle),rotation:f(v.rotation)}; const kernel=bindCanonicalKernel(factory,{width:v.width,height:v.height,time:v.time,seed:0,uniforms,textures:{},tileOffset:uniforms.tileOffset,fullResolution:uniforms.fullResolution}); const output=new Surface(v.width,v.height); runPass({kernel,destination:output,time:v.time,seed:0,tileRows:1}); return {inputWords:words(input.data),outputWords:words(output.data),outputBytes:Array.from(output.toRgba8()),inputUnchanged:same(Array.from(before),Array.from(new Uint32Array(input.data.buffer))),outputStorage:output.data} }
const rendered = cases.map(spec => { const r=render(spec); return {...spec,input:{width:spec.width,height:spec.height,f32_words_le:r.inputWords,f32_sha256:digestWords(r.inputWords)},expected:{f32_words_le:r.outputWords,f32_sha256:digestWords(r.outputWords),rgba8_bytes:r.outputBytes,rgba8_sha256:digestBytes(r.outputBytes)},input_immutable_exact_bits:r.inputUnchanged,bindings:{resolution:[spec.width,spec.height],tileOffset:[spec.tileX,spec.tileY],fullResolution:[spec.width,spec.height],time:spec.time,poi:spec.poi,outputMode:spec.outputMode,iterations:spec.iterations,centerHiX:spec.centerHiX,centerHiY:spec.centerHiY,centerLoX:spec.centerLoX,centerLoY:spec.centerLoY,zoomSpeed:spec.zoomSpeed,zoomDepth:spec.zoomDepth,invert:spec.invert,stripeFreq:spec.stripeFreq,trapShape:spec.trapShape,lightAngle:spec.lightAngle,rotation:spec.rotation}} })
const baseline = new Map(rendered.map(x => [x.name,x]));
const canonicalFactoryText = Function.prototype.toString.call(canonicalFactory)
const mutationDefs = [
  {name:'cross-lane-dz-assignment',group:'cross-lane-assignment',mechanism:'replace canonical sequential dz lane writes with an unaliased whole-vector copy',anchor:'(dz[0] = 2 * (zx * dz[0] - zy * dz[1]) + 1, dz[1] = 2 * (zx * dz[1] + zy * dz[0]), dz);',replacement:'(dz = new $runtime.PooledFloat32Array([2 * (zx * dz[0] - zy * dz[1]) + 1, 2 * (zx * dz[1] + zy * dz[0])]), dz);'},
  {name:'df64-new-zr-carrier',group:'df64-carrier',mechanism:'replace the whole-vector new_zr carrier expression',anchor:'var new_zr = df64_add(df64_sub(zr2, zi2), c_re);',replacement:'var new_zr = df64_add(df64_sub(zi2, zr2), c_re);'},
  {name:'df64-whole-vector-carrier',group:'df64-carrier',mechanism:'replace the whole-vector new_zi carrier scale',anchor:'var new_zi = df64_add(df64_mul_f(zri, 2), c_im);',replacement:'var new_zi = df64_add(df64_mul_f(zri, 1), c_im);'},
  {name:'out-smoothIter',group:'out-materialization',mechanism:'mutate scalar smoothIter out assignment',anchor:'smoothIter = i + 1 - nu;',replacement:'smoothIter = i;'},
  {name:'out-rawIter-cardioid',group:'out-materialization',mechanism:'mutate scalar rawIter cardioid out assignment',anchor:'rawIter = (maxIter);',replacement:'rawIter = 0;'},
  {name:'out-z-final',group:'out-materialization',mechanism:'mutate vec2 z_final out assignment',anchor:'(z_final[0] = fx, z_final[1] = fy, z_final);',replacement:'(z_final[0] = 0, z_final[1] = 0, z_final);'},
  {name:'out-dz-final',group:'out-materialization',mechanism:'mutate vec2 dz_final out assignment',anchor:'(dz_final[0] = dz[0], dz_final[1] = dz[1], dz_final);',replacement:'(dz_final[0] = 0, dz_final[1] = 0, dz_final);'},
  {name:'out-stripeAcc',group:'out-materialization',mechanism:'mutate scalar stripeAcc out assignment',anchor:'stripeAcc = stripe;',replacement:'stripeAcc = 0;'},
  {name:'out-trapMin',group:'out-materialization',mechanism:'mutate scalar trapMin out assignment',anchor:'trapMin = trap;',replacement:'trapMin = 0;'},
  {name:'out-getPOI-cX',group:'out-materialization',mechanism:'mutate getPOI cX owner materialization at the main call site',anchor:'[_local_cX_df_1, cY_df] = getPOI.__out__',replacement:'[_local_cX_df_1, cY_df] = [new $runtime.PooledFloat32Array([0, 0]), cY_df]'},
  {name:'out-getPOI-cY',group:'out-materialization',mechanism:'mutate getPOI cY owner materialization at the main call site',anchor:'[_local_cX_df_1, cY_df] = getPOI.__out__',replacement:'[_local_cX_df_1, cY_df] = [_local_cX_df_1, new $runtime.PooledFloat32Array([0, 0])]'},
  {name:'out-transform-re',group:'out-materialization',mechanism:'mutate transformCoords re owner materialization',anchor:'[re_df, im_df] = transformCoords_df64.__out__',replacement:'[re_df, im_df] = [new $runtime.PooledFloat32Array([0, 0]), im_df]',expectedCount:2},
  {name:'out-transform-im',group:'out-materialization',mechanism:'mutate transformCoords im owner materialization',anchor:'[re_df, im_df] = transformCoords_df64.__out__',replacement:'[re_df, im_df] = [re_df, new $runtime.PooledFloat32Array([0, 0])]',expectedCount:2},
  {name:'max-iter-constant',group:'iteration-loop',mechanism:'mutate MAX_ITER constant',anchor:'var MAX_ITER = 500;',replacement:'var MAX_ITER = 1;'},
  {name:'runtime-loop-bound',group:'iteration-loop',mechanism:'mutate runtime maxIter loop break bound',anchor:'n >= maxIter)',replacement:'n >= (maxIter - 1))'},
  {name:'log-magnitude',group:'log-sites',mechanism:'mutate first log magnitude site',anchor:'var log_zn = log(mag2) * 0.5;',replacement:'var log_zn = log(mag2) * 0.25;'},
  {name:'log-normalization',group:'log-sites',mechanism:'mutate second nested log normalization site',anchor:'(log(log_zn / LOG2)) / LOG2;',replacement:'(log(log_zn / LOG2)) / (LOG2 * 2);'},
  {name:'log-distance-magnitude',group:'log-sites',mechanism:'mutate outputDistance log(mag) site',anchor:'var dist = (2 * mag) * log(mag) / dmag;',replacement:'var dist = (2 * mag) * log(mag * 2) / dmag;'},
  {name:'normal-h0',group:'normal-three-sample',mechanism:'mutate normal h0 sample coordinate',anchor:'var h0 = computeValueAt_df64(fragCoord, cX_df, cY_df, z_zoom, rot, maxIter);',replacement:'var h0 = computeValueAt_df64(new $runtime.PooledFloat32Array([fragCoord[0] + 1, fragCoord[1]]), cX_df, cY_df, z_zoom, rot, maxIter);'},
  {name:'normal-hx',group:'normal-three-sample',mechanism:'mutate normal hx sample coordinate',anchor:'var hx = computeValueAt_df64(new $runtime.PooledFloat32Array([fragCoord[0] + 1, fragCoord[1]]), cX_df, cY_df, z_zoom, rot, maxIter);',replacement:'var hx = computeValueAt_df64(new $runtime.PooledFloat32Array([fragCoord[0], fragCoord[1]]), cX_df, cY_df, z_zoom, rot, maxIter);'},
  {name:'normal-hy',group:'normal-three-sample',mechanism:'mutate normal hy sample coordinate',anchor:'var hy = computeValueAt_df64(new $runtime.PooledFloat32Array([fragCoord[0], fragCoord[1] + 1]), cX_df, cY_df, z_zoom, rot, maxIter);',replacement:'var hy = computeValueAt_df64(new $runtime.PooledFloat32Array([fragCoord[0], fragCoord[1]]), cX_df, cY_df, z_zoom, rot, maxIter);'},
]
function mutateFactory(def) { const count=canonicalFactoryText.split(def.anchor).length-1; const expectedCount=def.expectedCount ?? 1; if (count !== expectedCount) throw new Error(`${def.name}: anchor cardinality ${count}, expected ${expectedCount}`); const source=canonicalFactoryText.replaceAll(def.anchor,def.replacement); const factory=Function(`return (${source})`)(); if (typeof factory !== 'function') throw new Error(`${def.name}: mutated factory did not evaluate`); return {source,factory,anchor_occurrence_count:count} }
const ledger = mutationDefs.map(def => { const mutant=mutateFactory(def); const results=cases.map(spec => { const m=render(spec,{},mutant.factory); const c=baseline.get(spec.name); const lanes=changed(c.expected.f32_words_le,m.outputWords); const bytes=changed(c.expected.rgba8_bytes,m.outputBytes); return {case:spec.name,differs:lanes>0||bytes>0,changed_float32_lanes:lanes,changed_rgba8_bytes:bytes,float32_witness:firstMismatch(c.expected.f32_words_le,m.outputWords),rgba8_witness:firstMismatch(c.expected.rgba8_bytes,m.outputBytes)} }); return {...def,independent:true,source_anchor:def.anchor,replacement:def.replacement,anchor_occurrence_count:mutant.anchor_occurrence_count,source_relative_path:sourceRelative,source_sha256:sourceSha256,canonical_factory_text_sha256:factoryTextSha256,mutated_factory_text_sha256:sha256(mutant.source),anchor_sha256:sha256(def.anchor),replacement_sha256:sha256(def.replacement),results,result_sha256:sha256(JSON.stringify(results)),witness_cases:[],control_cases:[]} })
for (const item of ledger) { item.witness_cases=item.results.filter(x=>x.differs).map(x=>x.case); item.control_cases=item.results.filter(x=>!x.differs).map(x=>x.case); if (!item.witness_cases.length) throw new Error(`${item.name} has no witness`) }
const repeatA=render(cases[0]); const repeatB=render(cases[0]);
const independentA=render(cases[1]); const independentB=render(cases[1]);
const controlGroup={repeatability:{case:cases[0].name,identical_float32:same(repeatA.outputWords,repeatB.outputWords),identical_rgba8:same(repeatA.outputBytes,repeatB.outputBytes)},input_immutability:{case:cases[0].name,unchanged:repeatA.inputUnchanged},independent_output_storage:{case:cases[1].name,distinct_data_objects:independentA.outputStorage!==independentB.outputStorage},public_direct_identity:true}
if (!controlGroup.repeatability.identical_float32 || !controlGroup.repeatability.identical_rgba8 || !controlGroup.input_immutability.unchanged || !controlGroup.independent_output_storage.distinct_data_objects) throw new Error('canonical control contract failed')
const comparerFixture={width:1,height:1,f32_words_le:['0x00000000','0x3f800000','0x7fc00001','0x80000000'],rgba8_bytes:[0,1,2,255]}
const rejects=fn=>{try{fn();return false}catch{return true}}
const rejectsWith=(fn,pattern)=>{try{fn();return false}catch(error){return pattern.test(String(error?.message??error))}}
const comparerSelfTests={dimensions_before_access:rejectsWith(()=>compareExact(comparerFixture,{width:2,height:1},'dimensions'),/dimensions mismatch/),first_mismatch_reported:rejectsWith(()=>compareExact(comparerFixture,{...comparerFixture,f32_words_le:['0x00000000','0x3f800000','0x7fc00001','0x00000000']},'signed-zero'),/first mismatch at lane 3/),raw_words_and_rgba8_independent:rejectsWith(()=>compareExact(comparerFixture,{...comparerFixture,rgba8_bytes:[0,1,3,255]},'rgba8-mismatch'),/first mismatch at byte 2/),cases:{good:compareExact(comparerFixture,{...comparerFixture})===true,dimensions:rejects(()=>compareExact(comparerFixture,{...comparerFixture,width:2},'dimensions')),short:rejects(()=>compareExact(comparerFixture,{...comparerFixture,f32_words_le:comparerFixture.f32_words_le.slice(0,3)},'short')),long:rejects(()=>compareExact(comparerFixture,{...comparerFixture,f32_words_le:[...comparerFixture.f32_words_le,'0x00000000']},'long')),rgba8_count:rejects(()=>compareExact(comparerFixture,{...comparerFixture,rgba8_bytes:[0,1,2]},'rgba8-count')),rgba8_mismatch:rejects(()=>compareExact(comparerFixture,{...comparerFixture,rgba8_bytes:[0,1,3,255]},'rgba8-mismatch')),signed_zero:rejects(()=>compareExact(comparerFixture,{...comparerFixture,f32_words_le:['0x00000000','0x3f800000','0x7fc00001','0x00000000']},'signed-zero')),nan_payload:rejects(()=>compareExact(comparerFixture,{...comparerFixture,f32_words_le:['0x00000000','0x3f800000','0x7fc00002','0x80000000']},'nan-payload'))}}
if (!Object.values(comparerSelfTests.cases).every(Boolean)) throw new Error('custom comparer self-test failed')
const document={schema:'noisemaker-for-cpp.mandelbrot.pixel-parity.v1',schema_version:1,program_key:programKey,effect_key:'synth/mandelbrot',runtime_key:programKey,corpus_revision:corpusRevision,upstream_revision:upstreamRevision,factory:{name:factoryName,text_sha256:factoryTextSha256,public_factory_is_canonical_identity:true,adapter_own_key:false},runtime_binding_names:bindingNames,runtime_binding_abi:bindingAbi,canonical_binding_contract:{names:bindingNames,abi:bindingAbi},exactness_contract:{float32:'raw little-endian uint32 words; signed zero and NaN payloads significant',rgba8:'complete independently captured RGBA8 bytes',tolerance:'none',dimensions:'checked before lane access',comparison:'dimensions, counts, every uint32 word, every RGBA8 byte'},comparer_self_tests:comparerSelfTests,provenance:{source:{relative_path:sourceRelative,sha256:sourceSha256},cpu_snapshot:{argument:'<immutable-cpu-snapshot-root>',immutable_snapshot:true,realpath_containment_checked:true,live_checkout_rejected:true,import_closure:actualClosure.map(([relative_path,sha256])=>({relative_path,sha256}))},generator:{relative_path:'docs/port-engineering/mandelbrot-parity/mandelbrot_oracle_generator.mjs',sha256:sha256(fs.readFileSync(generatorPath))},materializer:{relative_path:'tools/glslcpp/generate_mandelbrot_native_oracle_include.py'}},render_cases:rendered,source_mutation_contract:{source_relative_path:sourceRelative,source_sha256:sourceSha256,canonical_factory_text_sha256:factoryTextSha256,execution:'each exact anchor/replacement is applied to canonical factory text and the mutated factory is executed through bindCanonicalKernel/runPass'},mutation_anchor_cardinality:{total:mutationDefs.length,by_group:Object.fromEntries([...new Set(mutationDefs.map(x=>x.group))].map(group=>[group,mutationDefs.filter(x=>x.group===group).length])),anchors:Object.fromEntries(ledger.map(x=>[x.name,x.anchor_occurrence_count]))},mutation_ledger:ledger,control_group:controlGroup,cross_lane_assignment_profile:{status:'authenticated',contract:'whole-vector destination lanes are emitted as source-order sequential writes only for this exact key',source_bound:'mandelbrot source and canonical factory pins',anchor:mutationDefs[0].anchor,replacement:mutationDefs[0].replacement,mutated_factory_text_sha256:ledger[0].mutated_factory_text_sha256},claim_boundaries:{absolute_paths:'stable placeholders only',authority:'unmodified public canonicalFactory252 from immutable snapshot; no local reimplementation or C++ output participates',adapter:'no adapter owns this key',mutations:'source/factory anchor replacements are executed authority mutations, not uniform perturbations'}}
rejectAbsolute(document)
const jsonPayload=Buffer.from(stable(document)); const report=Buffer.from('# Mandelbrot exact-pixel oracle\n\n' +
  'This package authenticates the public `' + programKey + '` canonical factory `' + factoryName + '` from an immutable CPU snapshot. It records raw Float32 words and independently captured RGBA8 bytes with zero tolerance.\n\n' +
  `- Cases: ${rendered.length}; mutation anchors: ${mutationDefs.length}, each with exact source cardinality and an independent witness set.\n` +
  '- Controls: repeat identity, input bit immutability, independent output storage, public/direct factory identity, and adapter-own-key rejection.\n' +
  `- Authority closure: ${actualClosure.length} literal-import files, realpath-confined and hash pinned; nonliteral dynamic imports, live checkout roots, and absolute-looking serialization fail closed.\n` +
  '- Run: `node docs/port-engineering/mandelbrot-parity/mandelbrot_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"`; materialize with `python3 tools/glslcpp/generate_mandelbrot_native_oracle_include.py --check`.\n\n' +
  `JSON SHA-256: ${sha256(jsonPayload)}.\n`)
function selfTest(){ const checks=[['factory identity',publicFactory===canonicalFactory],['closure exact',JSON.stringify(actualClosure)===JSON.stringify([...expectedClosure].sort((a,b)=>a[0].localeCompare(b[0])))],['raw words and bytes complete',rendered.every(x=>x.expected.f32_words_le.length===x.width*x.height*4&&x.expected.rgba8_bytes.length===x.width*x.height*4)],['input immutable',rendered.every(x=>x.input_immutable_exact_bits)],['absolute strings rejected',(()=>{try{rejectAbsolute({x:'/tmp/no'}) ;return false}catch{return true}})()],['mutation anchors exact',ledger.every(x=>x.anchor_occurrence_count===(x.name.startsWith('out-transform-')?2:1)&&x.independent&&x.witness_cases.length)],['custom comparer self-tests',Object.values(comparerSelfTests.cases).every(Boolean)],['signed zero significant',!same(['0x00000000'],['0x80000000'])]]; checks.forEach(([name,ok])=>console.log(`  [${ok?'ok':'FAIL'}] ${name}`)); return checks.every(([,ok])=>ok)?0:1 }
if (mode[0]==='--self-test') process.exit(selfTest())
if (mode[0]==='--write'){ checked(outputPath,jsonPayload); checked(reportPath,report); checked(fileURLToPath(import.meta.url),fs.readFileSync(fileURLToPath(import.meta.url))); console.log(`mandelbrot oracle written (${jsonPayload.length} bytes, ${sha256(jsonPayload)})`) }
else { if (!verify(outputPath).equals(jsonPayload)||!verify(reportPath).equals(report)||!verify(fileURLToPath(import.meta.url)).equals(fs.readFileSync(fileURLToPath(import.meta.url)))) throw new Error('mandelbrot oracle package drift'); console.log('mandelbrot oracle generator: ok') }
