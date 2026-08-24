#!/usr/bin/env node
// Frozen, standalone filter/spookyTicker pixel oracle.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppLexical = path.resolve(here, '../../..')
const outputPath = path.join(here, 'spooky-ticker-oracles.json')
const reportPath = path.join(here, 'spooky-ticker-oracle-report.md')
const programKey = 'filter/spookyTicker:spookyTicker'
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/spookyTicker/spookyTicker.glsl'
const sourceBytesExpected = 4276
const sourceShaExpected = 'd50ca880cd6c6c03dd01a7ae683316d42ed93baddaadce9f3b918be1c816d50f'
const factoryName = 'canonicalFactory147'
const factoryBytesExpected = 4103
const factoryShaExpected = '9eb9fa9412b700f73e687209bb60803d121ab5e4e036a80d5552797011a0384b'
const authorityNode = 'v24.7.0'
const upstreamRevisionExpected = '117a236679d1db3ab8f0e278230ece277b57564c'

const modes = new Set(['--write', '--check', '--self-test'])
function parseArgs() {
  let mode = null
  let cpuArg = null
  const argv = process.argv.slice(2)
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (modes.has(token)) {
      if (mode !== null) throw new Error('duplicate mode')
      mode = token
      continue
    }
    if (token === '--cpu-root') {
      if (cpuArg !== null || index + 1 >= argv.length || argv[index + 1].startsWith('-')) {
        throw new Error('exactly one --cpu-root ROOT is required')
      }
      cpuArg = argv[++index]
      continue
    }
    throw new Error(`unknown option: ${token}`)
  }
  if (mode === null) throw new Error('choose --write, --check, or --self-test')
  if (cpuArg === null) throw new Error('--cpu-root required')
  const liveArg = process.env.NOISEMAKER_FOR_CPU
  if (!liveArg) throw new Error('NOISEMAKER_FOR_CPU required')
  return { mode, cpuArg, liveArg }
}

function lexicalDirectory(raw, label) {
  if (typeof raw !== 'string' || raw.length === 0) throw new Error(`${label} required`)
  const lexical = path.resolve(raw)
  let stat
  try { stat = fs.lstatSync(lexical) } catch { throw new Error(`${label} missing`) }
  if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`${label} must be a non-symlink directory`)
  return lexical
}

function beneath(root, candidate) {
  return candidate === root || candidate.startsWith(`${root}${path.sep}`)
}

const { mode, cpuArg, liveArg } = parseArgs()
const cppLexicalChecked = lexicalDirectory(cppLexical, 'C++ checkout')
const authorityLexical = lexicalDirectory(cpuArg, 'authority root')
const liveLexical = lexicalDirectory(liveArg, 'live root')
const cppRoot = fs.realpathSync(cppLexicalChecked)
const cpuRoot = fs.realpathSync(authorityLexical)
const liveRoot = fs.realpathSync(liveLexical)
if (cpuRoot === liveRoot || beneath(cpuRoot, liveRoot) || beneath(liveRoot, cpuRoot)) {
  throw new Error('authority and live roots must be distinct and non-overlapping')
}
if (beneath(cppRoot, cpuRoot) || beneath(cpuRoot, cppRoot)
    || beneath(cppRoot, liveRoot) || beneath(liveRoot, cppRoot)) {
  throw new Error('authority/live roots must be external to the C++ checkout')
}
const sourcePath = path.join(cppRoot, sourceRelative)

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
const entryFiles = ['src/effects/catalog.js','src/effects/generated/upstream-snapshot.js','src/csl/glsl-kernel.js','src/csl/glsl-runtime.js','src/runtime/pass-runner.js','src/runtime/surface.js']
const imports = [(/\bfrom\s*['"]([^'"\n]+)['"]/g), (/^[ \t]*import\s+['"]([^'"\n]+)['"]/gm)]
const dynamic = /\bimport\s*\(([^)]*)\)/g
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const bytes = view => Buffer.from(view.buffer, view.byteOffset, view.byteLength)
const words = view => new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4)
const wordHex = value => `0x${(value >>> 0).toString(16).padStart(8,'0')}`
const sidecarText = (target,payload) => `${sha256(payload)}  ${path.basename(target)}\n`
const verifySidecar = target => { const payload=fs.readFileSync(target); if(fs.readFileSync(`${target}.sha256`,'utf8')!==sidecarText(target,payload)) throw new Error(`sidecar drift: ${target}`); return payload }
function discoverClosure(root) {
  const confined=fs.realpathSync(root), stack=entryFiles.map(x=>path.join(confined,x)), seen=new Map()
  const realConfined=(candidate,label)=>{let stat;try{stat=fs.lstatSync(candidate)}catch{throw new Error(`missing import dependency ${label}`)} if(stat.isSymbolicLink()) throw new Error(`import symlink rejected: ${label}`); let resolved;try{resolved=fs.realpathSync(candidate)}catch{throw new Error(`missing import dependency ${label}`)} if(!beneath(confined,resolved)) throw new Error('import symlink escapes immutable snapshot'); return resolved}
  const enqueue=(spec,file)=>{ if(spec.startsWith('node:')) return; if(!spec.startsWith('./')&&!spec.startsWith('../')) throw new Error(`bare module specifier ${spec}`); const target=path.resolve(path.dirname(file),spec); if(!beneath(confined,target)) throw new Error('import escapes immutable snapshot'); stack.push(realConfined(target,spec)) }
  while(stack.length){ const file=realConfined(stack.pop(),stack.at(-1)||'entry'); if(seen.has(file)) continue; const text=fs.readFileSync(file,'utf8'); seen.set(file,sha256(Buffer.from(text))); dynamic.lastIndex=0; let m; while((m=dynamic.exec(text))){const literal=m[1].trim();if(!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) throw new Error(`nonliteral dynamic import in ${file}`);enqueue(literal.slice(1,-1),file)} for(const re of imports){re.lastIndex=0;while((m=re.exec(text))) enqueue(m[1],file)} }
  return [...seen].map(([file,digest])=>({relative_path:path.relative(root,file),sha256:digest})).sort((a,b)=>a.relative_path.localeCompare(b.relative_path))
}
function verifyClosure(root, expected=expectedClosure){ const actual=discoverClosure(root); const wanted=expected.map(([relative_path,digest])=>({relative_path,sha256:digest})).sort((a,b)=>a.relative_path.localeCompare(b.relative_path)); if(JSON.stringify(actual)!==JSON.stringify(wanted)) throw new Error(`CPU import closure mismatch: expected ${wanted.length}, found ${actual.length}`); return actual }
const noAbsolute = value => { if(typeof value==='string' && (value.startsWith('/')||/(?:^|[\\/])(Users|private|tmp|home)[\\/]/.test(value))) throw new Error('oracle absolute path serialized'); if(Array.isArray(value)) value.forEach(noAbsolute); else if(value&&typeof value==='object') Object.values(value).forEach(noAbsolute) }
verifyClosure(cpuRoot)
const load=relative=>import(pathToFileURL(path.join(cpuRoot,relative)).href)
const {canonicalAdapterFactories,canonicalKernelFactories,kernelFactories}=await load('src/effects/catalog.js'); const {UPSTREAM_REVISION}=await load('src/effects/generated/upstream-snapshot.js'); const {createCanonicalBindings}=await load('src/csl/glsl-kernel.js'); const {bindGlslKernel}=await load('src/csl/glsl-runtime.js'); const {runPass}=await load('src/runtime/pass-runner.js'); const {Surface}=await load('src/runtime/surface.js')
if(process.version!==authorityNode||UPSTREAM_REVISION!==upstreamRevisionExpected) throw new Error('authority drift')
const canonicalFactory=canonicalKernelFactories[programKey], publicFactory=kernelFactories.get(programKey), canonicalText=Function.prototype.toString.call(canonicalFactory)
if(typeof canonicalFactory!=='function'||canonicalFactory.name!==factoryName||Buffer.byteLength(canonicalText)!==factoryBytesExpected||sha256(canonicalText)!==factoryShaExpected) throw new Error('canonical factory drift')
if(publicFactory!==canonicalFactory||Object.hasOwn(canonicalAdapterFactories,programKey)) throw new Error('public/direct identity or adapter override drift')
const sourceBytes=fs.readFileSync(sourcePath); if(sourceBytes.length!==sourceBytesExpected||sha256(sourceBytes)!==sourceShaExpected) throw new Error('source provenance drift')
const f32=Math.fround, cases=[
  {name:'pass-through-top',width:12,height:8,renderScale:1,rows:1,alpha:1,seed:1,speed:0,time:0,tileRows:2,tileOffset:[0,0],fullResolution:[12,8],phase:1},
  {name:'alpha-zero-bottom',width:40,height:32,renderScale:1,rows:1,alpha:0,seed:7,speed:1,time:.25,tileRows:7,tileOffset:[0,0],fullResolution:[40,32],phase:2},
  {name:'glyph-hash-scroll',width:48,height:36,renderScale:1,rows:1,alpha:.75,seed:17,speed:2,time:.5,tileRows:32,tileOffset:[3,2],fullResolution:[64,48],phase:3},
  {name:'rows-two-shadow',width:56,height:64,renderScale:1,rows:2,alpha:1,seed:23,speed:3,time:.75,tileRows:5,tileOffset:[-2,4],fullResolution:[64,80],phase:4},
  {name:'scaled-render',width:80,height:72,renderScale:2,rows:2,alpha:.4,seed:99,speed:5,time:.33,tileRows:11,tileOffset:[5,-1],fullResolution:[160,144],phase:5},
  {name:'negative-cell-scroll',width:32,height:40,renderScale:1,rows:1,alpha:.9,seed:-11,speed:-2,time:.61,tileRows:1,tileOffset:[-7,0],fullResolution:[32,40],phase:6},
  {name:'zero-speed-time',width:36,height:48,renderScale:3,rows:1,alpha:.2,seed:0,speed:0,time:9.5,tileRows:13,tileOffset:[1,1],fullResolution:[108,144],phase:7},
]
function inputSurface(d){const data=new Float32Array(d.width*d.height*4);for(let i=0;i<data.length;i+=4){const p=i/4,x=p%d.width,y=Math.floor(p/d.width);data[i]=f32(((x*17+y*11+d.phase)%23)/22);data[i+1]=f32(((x*7+y*19+d.phase*2)%29)/28);data[i+2]=f32(((x*13+y*5+d.phase*3)%31)/30);data[i+3]=f32(.4+((x+y+d.phase)%5)/10)}return new Surface(d.width,d.height,data)}
function render(factory,d){const inputTex=inputSurface(d),before=new Uint32Array(words(inputTex.data)),output=new Surface(d.width,d.height);const bindings=createCanonicalBindings({width:d.width,height:d.height,time:f32(d.time),seed:d.seed,uniforms:{renderScale:f32(d.renderScale),time:f32(d.time),speed:f32(d.speed),alpha:f32(d.alpha),rows:d.rows,seed:d.seed},textures:{inputTex},tileOffset:new Float32Array(d.tileOffset.map(f32)),fullResolution:new Float32Array(d.fullResolution.map(f32))});const kernel=bindGlslKernel(factory,bindings);runPass({kernel,destination:output,time:d.time,seed:d.seed,tileRows:d.tileRows});const after=words(inputTex.data);if(before.some((x,i)=>x!==after[i]))throw new Error(`${d.name}: input mutated`);return {output,input:inputTex,inputImmutable:true,inputLifetimeStable:true}}
function compare(a,b){const dims=a.width===b.width&&a.height===b.height;if(!dims)return {exact:false,dimensions_match:false,lane_count_match:false,mismatched_lanes:0,mismatched_bytes:0,exact_f32_bits:false,exact_rgba8_bytes:false,first_mismatch:null,first_rgba8_mismatch:null};const la=words(a.data),lb=words(b.data);let ml=Math.abs(la.length-lb.length),fm=null;for(let i=0;i<Math.min(la.length,lb.length);i++)if(la[i]!==lb[i]){ml++;if(!fm)fm={lane_index:i,bits_reference:wordHex(la[i]),bits_candidate:wordHex(lb[i])}}const ba=new Uint8Array(a.toRgba8()),bb=new Uint8Array(b.toRgba8());let mb=Math.abs(ba.length-bb.length),fb=null;for(let i=0;i<Math.min(ba.length,bb.length);i++)if(ba[i]!==bb[i]){mb++;if(!fb)fb={byte_index:i,byte_reference:ba[i],byte_candidate:bb[i]}}return {exact:ml===0&&mb===0,dimensions_match:true,lane_count_match:la.length===lb.length,mismatched_lanes:ml,mismatched_bytes:mb,exact_f32_bits:ml===0,exact_rgba8_bytes:mb===0,first_mismatch:fm,first_rgba8_mismatch:fb}}
const hostileDimensionGuard=()=>{const hostile={width:1,height:1,get data(){throw new Error('lane access before dimension check')},toRgba8(){throw new Error('rgba access before dimension check')}};const other={width:2,height:1,get data(){throw new Error('other lane access before dimension check')},toRgba8(){throw new Error('other rgba access before dimension check')}};return !compare(hostile,other).exact}
const selfTests={good_equal:compare({width:1,height:1,data:new Float32Array([1,0,0,1]),toRgba8:()=>[255,0,0,255]},{width:1,height:1,data:new Float32Array([1,0,0,1]),toRgba8:()=>[255,0,0,255]}).exact,dimensions_mismatch:!compare({width:1,height:1,data:new Float32Array(4),toRgba8:()=>[0,0,0,0]},{width:2,height:1,data:new Float32Array(8),toRgba8:()=>[0,0,0,0,0,0,0,0]}).exact,short_lane_count:!compare({width:1,height:1,data:new Float32Array(4),toRgba8:()=>[0,0,0,0]},{width:1,height:1,data:new Float32Array(3),toRgba8:()=>[0,0,0,0]}).exact,long_lane_count:!compare({width:1,height:1,data:new Float32Array(3),toRgba8:()=>[0,0,0,0]},{width:1,height:1,data:new Float32Array(4),toRgba8:()=>[0,0,0,0]}).exact,rgba8_mismatch:!compare({width:1,height:1,data:new Float32Array(4),toRgba8:()=>[0,0,0,0]},{width:1,height:1,data:new Float32Array(4),toRgba8:()=>[1,0,0,0]}).exact,signed_zero_rejected:!compare({width:1,height:1,data:new Float32Array(new Uint32Array([0,0,0,0]).buffer),toRgba8:()=>[0,0,0,0]},{width:1,height:1,data:new Float32Array(new Uint32Array([0x80000000,0,0,0]).buffer),toRgba8:()=>[0,0,0,0]}).exact,nan_payload_rejected:!compare({width:1,height:1,data:new Float32Array(new Uint32Array([0x7fc00001,0,0,0]).buffer),toRgba8:()=>[0,0,0,0]},{width:1,height:1,data:new Float32Array(new Uint32Array([0x7fc00002,0,0,0]).buffer),toRgba8:()=>[0,0,0,0]}).exact,hostile_dimension_guard:hostileDimensionGuard()}; if(!Object.values(selfTests).every(Boolean))throw new Error('comparer self-tests failed')
const refs=new Map(), renderCases=cases.map(d=>{const first=render(canonicalFactory,d), second=render(publicFactory,d), repeat=compare(first.output,second.output);if(!repeat.exact)throw new Error(`${d.name}: public/direct mismatch`);const inputWords=Array.from(words(first.input.data),wordHex), inputBytes=Array.from(new Uint8Array(first.input.toRgba8()));refs.set(d.name,first.output);return {name:d.name,width:d.width,height:d.height,tile_rows:d.tileRows,controls:{renderScale:d.renderScale,rows:d.rows,alpha:d.alpha,seed:d.seed,speed:d.speed,time:d.time,tileOffset:d.tileOffset,fullResolution:d.fullResolution},input:{phase:d.phase,f32_words_le:inputWords,f32_sha256:sha256(bytes(first.input.data)),rgba8_bytes:inputBytes,rgba8_sha256:sha256(Buffer.from(inputBytes))},output_f32_words_le:Array.from(words(first.output.data),wordHex),output_f32_sha256:sha256(bytes(first.output.data)),output_rgba8_bytes:Array.from(new Uint8Array(first.output.toRgba8())),output_rgba8_sha256:sha256(bytes(first.output.toRgba8())),input_immutable_exact_bits:first.inputImmutable,input_lifetime_stable:first.inputLifetimeStable,public_direct_repeat_exact:repeat.exact,distinct_storage:first.output!==second.output&&first.input!==second.input}})
const mutations=[
  {name:'alpha-axis',anchor:'mask * alpha, mask * alpha',replacement:'mask * 1, mask * 1',witnesses:['glyph-hash-scroll']},
  {name:'time-speed-axis',anchor:'var t = time * speed;',replacement:'var t = time + speed;',witnesses:['glyph-hash-scroll']},
  {name:'seed-hash-axis',anchor:'var baseSeed = hash_mix((seed|0) * 7919);',replacement:'var baseSeed = hash_mix((seed|0) * 7918);',witnesses:['glyph-hash-scroll','rows-two-shadow']},
  {name:'render-scale-geometry',anchor:'var iScale = max((BASE_SCALE) * renderScale|0, 1);',replacement:'var iScale = max((BASE_SCALE) * 1|0, 1);',witnesses:['scaled-render']},
  {name:'row-count-geometry',anchor:'var totalH = rows * (CELL_H + ROW_GAP);',replacement:'var totalH = CELL_H + ROW_GAP;',witnesses:['scaled-render']},
  {name:'glyph-bit-index',anchor:'var row = GLYPHS[digit * 8 + gy];',replacement:'var row = GLYPHS[gy];',witnesses:['rows-two-shadow']},
  {name:'hash-xor-carrier',anchor:'v = v ^ (v >> 16);',replacement:'v = v | (v >> 16);',witnesses:['glyph-hash-scroll','rows-two-shadow']},
  {name:'scan-coordinate',anchor:'var px = floor(v_texCoord[0] * dims[0])|0;',replacement:'var px = floor(v_texCoord[1] * dims[0])|0;',witnesses:['glyph-hash-scroll']},
  {name:'negative-cell-floor',anchor:'var cellX = sx >= 0 ? sx / CELL_W : (sx - CELL_W + 1) / CELL_W;',replacement:'var cellX = sx / CELL_W;',witnesses:['negative-cell-scroll']},
  {name:'varying-uv-alias',anchor:'v_texCoord.set($runtime.varyings["v_texCoord"])',replacement:'v_texCoord.set(new Float32Array([0, 0]))',witnesses:['glyph-hash-scroll']},
]
function compileFactory(text){return Function(`return (${text})`)()}
const ledger=mutations.map(m=>{if(!canonicalText.includes(m.anchor))throw new Error(`mutation anchor absent: ${m.name}`);const text=canonicalText.replace(m.anchor,m.replacement),factory=compileFactory(text),results=m.witnesses.map(name=>{const mutated=render(factory,cases.find(x=>x.name===name)).output,result=compare(refs.get(name),mutated);if(result.mismatched_lanes===0||result.mismatched_bytes===0)throw new Error(`${m.name}: inert witness ${name}`);return {case:name,mismatched_lanes:result.mismatched_lanes,mismatched_bytes:result.mismatched_bytes,first_mismatch:result.first_mismatch,first_rgba8_mismatch:result.first_rgba8_mismatch}});return {name:m.name,anchor_text:m.anchor,replacement_text:m.replacement,anchor_sha256:sha256(Buffer.from(m.anchor)),replacement_sha256:sha256(Buffer.from(m.replacement)),mutated_factory_sha256:sha256(Buffer.from(text)),required_witnesses:m.witnesses,required_witness_results:results}})
const document={schema:'noisemaker-for-cpp.spooky-ticker.pixel-parity.v1',program_key:programKey,provenance:{authority_node:process.version,upstream_revision:UPSTREAM_REVISION,source_relative:sourceRelative,source_bytes:sourceBytesExpected,source_sha256:sourceShaExpected,factory_name:factoryName,factory_bytes:factoryBytesExpected,factory_sha256:factoryShaExpected,live_checkout_required:true,authority_live_distinct:true,authority_live_non_symlink_directories:true,import_closure:verifyClosure(cpuRoot)},factory:{name:factoryName,text_sha256:factoryShaExpected,public_direct_identity:publicFactory===canonicalFactory,adapter_override:false},source_uniform_abi:{inputTex:'sampler2D',renderScale:'float',time:'float',speed:'float',alpha:'float',rows:'int',seed:'int'},runtime_binding_abi:{inputTex:'sampler2D',renderScale:'number',time:'number',speed:'number',alpha:'number',rows:'int32',seed:'int32'},input_fixture:{schema:'noisemaker-for-cpp.spooky-ticker.input-texture.v1',coordinate_order:'x-fastest row-major',component_order:['r','g','b','a'],formulas:['f32(((x*17+y*11+phase)%23)/22)','f32(((x*7+y*19+phase*2)%29)/28)','f32(((x*13+y*5+phase*3)%31)/30)','f32(.4+((x+y+phase)%5)/10)']},render_cases:renderCases,comparer_self_tests:selfTests,behavioral_mutation_ledger:ledger,mutation_contract:{behavioral_names:mutations.map(x=>x.name),witnesses:Object.fromEntries(mutations.map(x=>[x.name,x.witnesses]))}}
noAbsolute(document);const serialized=`${JSON.stringify(document,null,2)}\n`;const report=`# SpookyTicker pixel oracle\n\nThis package freezes the canonical \`filter/spookyTicker:spookyTicker\` factory. It covers uv/varying aliasing, ticker rows and negative-cell scrolling, glyph indexing and signed/unsigned hashes, renderScale, full-res storage dimensions, time, speed, seed, alpha, repeated tile scans, exact Float32 words, and RGBA8 bytes.\n\n- Schema: \`${document.schema}\`\n- Cases: ${renderCases.length}; behavioral mutations: ${ledger.length}.\n- Every case checks immutable sampler input, retained lifetime, canonical/public identity, and distinct output/input storage.\n- Run with: \`NOISEMAKER_FOR_CPU=<live-noisemaker-for-cpu-checkout> node spooky_ticker_oracle_generator.mjs --check --cpu-root <immutable-cpu-snapshot-root>\`\n`
function writeChecked(target,payload){fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,payload);fs.writeFileSync(`${target}.sha256`,sidecarText(target,payload))}
if(mode==='--self-test'){const symlinkClone=fs.mkdtempSync(path.join(os.tmpdir(),'spooky-ticker-symlink-'));fs.cpSync(cpuRoot,symlinkClone,{recursive:true});const escaped=path.join(symlinkClone,'src/csl/runtime.js');fs.rmSync(escaped);fs.symlinkSync(os.tmpdir(),escaped);let symlinkRejected=false;try{verifyClosure(symlinkClone)}catch{symlinkRejected=true}fs.rmSync(symlinkClone,{recursive:true,force:true});if(!symlinkRejected)throw new Error('import symlink escape accepted');console.log('symlink import-closure escape rejected')}
if(mode==='--write'){writeChecked(outputPath,Buffer.from(serialized));writeChecked(reportPath,Buffer.from(report));writeChecked(fileURLToPath(import.meta.url),fs.readFileSync(fileURLToPath(import.meta.url)));console.log(`${renderCases.length} cases, ${ledger.length} behavioral mutations written`)}else{if(verifySidecar(outputPath).toString()!==serialized||verifySidecar(reportPath).toString()!==report)throw new Error('SpookyTicker oracle drift');console.log(`${renderCases.length} cases, ${ledger.length} behavioral mutations, ${Object.keys(selfTests).length} strict comparer self-tests`)}
if(mode==='--self-test'){const clone=fs.mkdtempSync(path.join(os.tmpdir(),'spooky-ticker-oracle-'));fs.cpSync(cpuRoot,clone,{recursive:true});fs.appendFileSync(path.join(clone,'src/csl/runtime.js'),'\n// deliberate mutation\n');let rejected=false;try{verifyClosure(clone)}catch{rejected=true}if(!rejected)throw new Error('modified import dependency accepted');let missing=false;try{verifyClosure(cpuRoot,expectedClosure.slice(0,-1))}catch{missing=true}if(!missing)throw new Error('missing import-closure entry accepted');fs.rmSync(clone,{recursive:true,force:true});console.log('modified import dependency rejected');console.log('missing import-closure entry rejected');console.log('public/direct/repeat identity verified');for(const x of ledger)console.log(`factory mutation witness: ${x.name}`)}
