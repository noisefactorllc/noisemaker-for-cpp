import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { spawnSync } from 'node:child_process'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../../../..')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourceRel = `tools/glslcpp/corpus/${revision}/sources/synth/testPattern/testPattern.glsl`
const sourceSha = 'f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20'
const sourceBytes = 5919
const key = 'synth/testPattern:testPattern'
const out = path.join(here, 'testPattern-oracles.json')
const report = path.join(here, 'testPattern-oracle-report.md')
const materializer = path.join(root, 'tools/glslcpp/generate_testpattern_native_oracle_include.py')
const coherencePath = path.join(here, 'testPattern-oracle-coherence.json')
const generatorPath = path.join(here, 'testPattern_oracle_generator.mjs')
const coherenceSchema = 'noisemaker-for-cpp.testPattern.oracle-coherence.v1'
// Canonical hash of the exact manifest bytes with only the self-referential generator digest redacted.
const coherenceAnchor = 'cf188502dcdab8b4bee35fb18cb77dd2c54837ae22365d95abba58b9c4a51792'
const f = Math.fround
const hash = b => crypto.createHash('sha256').update(b).digest('hex')
const bytes = x => Buffer.from(x.buffer, x.byteOffset, x.byteLength)
const bits = x => { const a = new Float32Array([x]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
const words = x => Array.from(x, bits)
const rejectPath = x => { if (typeof x === 'string' && (/^(?:[A-Za-z]:[\\/]|\\\\|\/)/.test(x) || /(?:^|[\\/])(Users|private|tmp|home)[\\/]/.test(x))) throw Error('serialized path rejected') }

function checkedAsset(file) {
  const payload = fs.readFileSync(file)
  const sidecar = fs.readFileSync(`${file}.sha256`, 'utf8')
  const expected = `${hash(payload)}  ${path.basename(file)}\n`
  if (sidecar !== expected) throw Error(`checksum sidecar drift: ${path.basename(file)}`)
  return payload
}
function anchoredManifestPayload(payload) {
  const text = Buffer.from(payload).toString('utf8')
  const redacted = text.replace(/(\"generator_sha256\"\s*:\s*)\"[0-9a-f]{64}\"/, '$1\"<generator-sha256>\"')
  if (redacted === text) throw Error('coherence generator hash field missing')
  return Buffer.from(redacted)
}
function verifyAnchoredCoherence() {
  const payload = checkedAsset(coherencePath)
  if (hash(anchoredManifestPayload(payload)) !== coherenceAnchor) throw Error('coherence content anchor drift')
  let manifest
  try { manifest = JSON.parse(payload.toString('utf8')) } catch (error) { throw Error(`coherence JSON invalid: ${error.message}`) }
  const keys = Object.keys(manifest).sort()
  if (keys.join(',') !== 'generator_sha256,include_sha256,oracle_sha256,report_sha256,schema' || manifest.schema !== coherenceSchema) throw Error('coherence schema drift')
  for (const name of ['generator','report','oracle','include']) {
    if (typeof manifest[`${name}_sha256`] !== 'string' || !/^[0-9a-f]{64}$/.test(manifest[`${name}_sha256`])) throw Error(`coherence ${name} hash malformed`)
  }
  const generatorDigest = hash(checkedAsset(generatorPath))
  if (generatorDigest !== manifest.generator_sha256) throw Error('coherence hash drift: generator')
  for (const [name, file] of [['report', report], ['oracle', out], ['include', path.join(root, 'tests/oracles/testPattern_expected.inc')]]) {
    const digest = hash(checkedAsset(file))
    if (digest !== manifest[`${name}_sha256`]) throw Error(`coherence hash drift: ${name}`)
  }
  return manifest
}
function verifyCoherence() {
  const result = spawnSync('python3', [materializer, '--check'], {cwd: root, encoding: 'utf8'})
  if (result.error || result.status !== 0) throw Error(`anchored materializer coherence check failed: ${(result.stderr || result.stdout || result.error?.message || '').trim()}`)
  return true
}

const closure = {
 'src/csl/glsl-kernel.js':'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa','src/csl/glsl-runtime.js':'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072','src/csl/runtime.js':'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee','src/effects/adapters/bit-effects.js':'5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7','src/effects/adapters/crt.js':'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc','src/effects/adapters/f32-color.js':'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046','src/effects/adapters/fractal.js':'0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29','src/effects/adapters/index.js':'40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267','src/effects/adapters/julia.js':'0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5','src/effects/adapters/median.js':'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583','src/effects/adapters/palette.js':'8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452','src/effects/adapters/snow.js':'202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366','src/effects/catalog.js':'d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4','src/effects/definition.js':'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02','src/effects/generated/canonical-adapter-data.js':'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab','src/effects/generated/canonical-kernels.js':'66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe','src/effects/generated/kernels.js':'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01','src/effects/generated/upstream-snapshot.js':'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090','src/effects/registry.js':'8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618','src/runtime/pass-runner.js':'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa','src/runtime/sampler.js':'1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328','src/runtime/surface.js':'0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'
}
function authority(argv) {
  const i = argv.indexOf('--cpu-root'), raw = i >= 0 ? argv[i + 1] : process.env.NOISEMAKER_CPU_ROOT
  if (!raw) throw Error('existing immutable CPU snapshot required')
  let st
  try { st = fs.lstatSync(raw) } catch { throw Error('--cpu-root must be a directory') }
  if (st.isSymbolicLink()) throw Error('--cpu-root must not be a symlink')
  if (!st.isDirectory()) throw Error('--cpu-root must be a directory')
  const real = path.resolve(fs.realpathSync.native(raw))
  const cppReal = path.resolve(fs.realpathSync.native(root))
  const beneathCpp = (a,b) => a === b || a.startsWith(`${b}${path.sep}`)
  if (beneathCpp(real, cppReal)) throw Error('--cpu-root must not live inside the C++ repository')
  const liveRaw = process.env.NOISEMAKER_FOR_CPU || (process.env.HOME ? path.join(process.env.HOME, 'platform/noisemaker-for-cpu') : '')
  if (!liveRaw || !fs.existsSync(liveRaw)) throw Error(`live noisemaker-for-cpu checkout does not exist: ${liveRaw || '<unset>'}`)
  let liveStat
  try { liveStat = fs.lstatSync(liveRaw) } catch { throw Error(`live noisemaker-for-cpu checkout does not exist: ${liveRaw}`) }
  if (liveStat.isSymbolicLink()) throw Error('NOISEMAKER_FOR_CPU must not be a symlink')
  if (!liveStat.isDirectory()) throw Error(`live noisemaker-for-cpu checkout does not exist: ${liveRaw}`)
  const liveReal = path.resolve(fs.realpathSync.native(liveRaw))
  const beneath = (a,b) => a === b || a.startsWith(`${b}${path.sep}`)
  if (beneath(liveReal, real) || beneath(real, liveReal)) throw Error('authority snapshot and live checkout must be distinct roots')
  return real
}
function lexImportTokens(text) {
  const tokens = []
  for (let i = 0; i < text.length;) {
    const ch = text[i]
    if (/\s/.test(ch)) { i++; continue }
    if (ch === '/' && text[i + 1] === '/') { i += 2; while (i < text.length && text[i] !== '\n') i++; continue }
    if (ch === '/' && text[i + 1] === '*') { const end = text.indexOf('*/', i + 2); if (end < 0) throw Error('unterminated comment in import graph'); i = end + 2; continue }
    if (ch === '"' || ch === "'" || ch === '`') {
      const quote = ch, start = i++; let value = '', escaped = false, closed = false
      for (; i < text.length; i++) { const c = text[i]; if (escaped) { value += c; escaped = false; continue } if (c === '\\') { escaped = true; value += c; continue } if (c === quote) { closed = true; i++; break } value += c }
      if (!closed) throw Error('unterminated string in import graph')
      tokens.push({kind:'string', value, quote, start}); continue
    }
    if (/[A-Za-z_$]/.test(ch)) { const start = i++; while (i < text.length && /[A-Za-z0-9_$]/.test(text[i])) i++; tokens.push({kind:'id', value:text.slice(start, i), start}); continue }
    tokens.push({kind:'punct', value:ch, start:i}); i++
  }
  return tokens
}
function staticImportSpecifiers(text) {
  const tokens = lexImportTokens(text), specs = []
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i]
    if (token.kind !== 'id' || (token.value !== 'import' && token.value !== 'export')) continue
    if (tokens[i - 1]?.value === '.') continue
    const next = tokens[i + 1]
    if (token.value === 'import' && next?.value === '(') continue
    if (next?.kind === 'string') { specs.push(next.value); continue }
    let boundary = tokens.length
    for (let j = i + 1; j < tokens.length; j++) { if (tokens[j].value === ';' || (j > i + 1 && tokens[j].kind === 'id' && (tokens[j].value === 'import' || tokens[j].value === 'export'))) { boundary = j; break } }
    for (let j = i + 1; j + 1 < boundary; j++) if (tokens[j].kind === 'id' && tokens[j].value === 'from' && tokens[j + 1].kind === 'string') { specs.push(tokens[j + 1].value); break }
  }
  return specs
}
function dynamicImportSpecifiers(text) {
  const tokens = lexImportTokens(text), specs = []
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].kind !== 'id' || tokens[i].value !== 'import' || tokens[i - 1]?.value === '.' || tokens[i + 1]?.value !== '(') continue
    const argument = tokens[i + 2]
    if (argument?.kind !== 'string' || argument.quote === '`' || tokens[i + 3]?.value !== ')') throw Error('nonliteral dynamic import')
    specs.push(argument.value)
  }
  return specs
}
function verify(root) {
  const starts = ['src/effects/catalog.js','src/csl/glsl-kernel.js','src/csl/glsl-runtime.js','src/runtime/pass-runner.js','src/runtime/surface.js']
  const queue = [...starts], seen = new Set()
  while (queue.length) {
    const rel = path.posix.normalize(queue.pop())
    if (seen.has(rel)) continue
    if (rel.startsWith('../') || path.posix.isAbsolute(rel)) throw Error(`import escapes authority: ${rel}`)
    const p = path.join(root, rel), stat = fs.lstatSync(p)
    if (stat.isSymbolicLink()) throw Error(`closure file must not be a symlink: ${rel}`)
    if (!stat.isFile()) throw Error(`missing closure file: ${rel}`)
    const real = path.resolve(fs.realpathSync.native(p)), relative = path.relative(root, real)
    if (relative.startsWith('..') || path.isAbsolute(relative) || relative !== rel) throw Error(`closure realpath escape: ${rel}`)
    seen.add(rel)
    const text = fs.readFileSync(real, 'utf8'), specs = staticImportSpecifiers(text)
    try { specs.push(...dynamicImportSpecifiers(text)) } catch (error) { throw Error(`${error.message} in ${rel}`) }
    for (const specifier of specs) {
      if (specifier.startsWith('node:')) continue
      if (!specifier.startsWith('.')) throw Error(`bare import: ${specifier}`)
      const target = path.posix.normalize(path.posix.join(path.posix.dirname(rel), specifier))
      if (!target.endsWith('.js') || target.startsWith('../')) throw Error(`import escapes authority: ${rel} -> ${specifier}`)
      queue.push(target)
    }
  }
  const expected = Object.keys(closure).sort(), actual = [...seen].sort()
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw Error(`literal import graph drift: expected ${expected.length}, got ${actual.length}`)
  return actual.map((rel) => {
    const p = path.join(root, rel), stat = fs.lstatSync(p)
    if (stat.isSymbolicLink()) throw Error(`closure file must not be a symlink: ${rel}`)
    const got = hash(fs.readFileSync(p)), want = closure[rel]
    if (got !== want) throw Error(`runtime closure hash drift: ${rel}`)
    return {relative_path: rel, sha256: got}
  })
}
function exact(a,b) { if(a.width!==b.width||a.height!==b.height) return {equal:false,reason:'dimensions'}; if(a.f32.length!==b.f32.length) return {equal:false,reason:'float32-count'}; if(a.rgba.length!==b.rgba.length) return {equal:false,reason:'rgba8-count'}; for(let i=0;i<a.f32.length;i++) if(a.f32[i]!==b.f32[i]) return {equal:false,reason:'float32',first:i}; for(let i=0;i<a.rgba.length;i++) if(a.rgba[i]!==b.rgba[i]) return {equal:false,reason:'rgba8',first:i}; return {equal:true} }
function comparer() { const a={width:1,height:1,f32:['0x00000000'],rgba:[0]}; return {good_equal:exact(a,a).equal,dimensions_before_access:exact(a,{...a,width:2}).reason==='dimensions',short_count:exact(a,{...a,f32:[]}).reason==='float32-count',long_count:exact(a,{...a,rgba:[0,0]}).reason==='rgba8-count',signed_zero:exact(a,{...a,f32:['0x80000000']}).reason==='float32',nan_payload:exact(a,{...a,f32:['0x7fc00001']}).reason==='float32',rgba8_independent:exact(a,{...a,rgba:[1]}).reason==='rgba8',first_mismatch_reported:exact(a,{...a,f32:['0x3f800000']}).first===0} }
const cases=[
 {name:'checker-hundreds-digit',width:1,height:1,gridSize:12,pattern:0,tileOffset:[19,27],fullResolution:[1000,1000],phase:1}, {name:'checker-single-digit',width:1,height:1,gridSize:3,pattern:0,tileOffset:[499.5,499.5],fullResolution:[1000,1000],phase:2}, {name:'checker-grid-clamp',width:2,height:2,gridSize:0,pattern:0,tileOffset:[0,0],fullResolution:[2,2],phase:3}, {name:'color-bars',width:8,height:1,gridSize:4,pattern:1,tileOffset:[0,0],fullResolution:[8,1],phase:4}, {name:'gradient-nonsquare',width:4,height:3,gridSize:4,pattern:2,tileOffset:[1,0],fullResolution:[8,3],phase:5}, {name:'uv-map-tile',width:3,height:2,gridSize:3,pattern:3,tileOffset:[2,1],fullResolution:[6,4],phase:6}, {name:'grid-lines',width:5,height:4,gridSize:3,pattern:4,tileOffset:[0,0],fullResolution:[5,4],phase:7}, {name:'color-grid',width:4,height:3,gridSize:4,pattern:5,tileOffset:[0,0],fullResolution:[4,3],phase:8}, {name:'dot-grid',width:5,height:5,gridSize:4,pattern:6,tileOffset:[0,0],fullResolution:[5,5],phase:9}
]
const mutationSpecs=[
 ['digit-extraction-trip-count','for (var i = 0; i < 3; i++)','for (var i = 0; i < 2; i++)','digit extraction trip-count off-by-one',['checker-hundreds-digit']], ['glyph-bit-sample','return ((GLYPH[digit] >> bitIndex) & 1) == 1;','return true;','glyph bit sample forced',['checker-hundreds-digit']], ['checker-grid-clamp','function checkerboard (uv) {\n  \tuv = $runtime.copy(uv);\n  \tvar n = max(gridSize, 1);','function checkerboard (uv) {\n  \tuv = $runtime.copy(uv);\n  \tvar n = max(gridSize, 2);','minimum grid-size clamp',['checker-grid-clamp']], ['pattern-bars-dispatch','if (pattern == 1)','if (pattern == 9)','pattern branch dispatch',['color-bars']], ['bars-upper-clamp','clamp(bar, 0, 7)','clamp(bar, 0, 6)','SMPTE bar upper clamp',['color-bars']], ['gradient-axis','globalCoord[0] / fullResolution[0]','globalCoord[1] / fullResolution[1]','gradient axis',['gradient-nonsquare']], ['uv-axis','[globalCoord[0] / fullResolution[0], globalCoord[1] / fullResolution[1]]','[globalCoord[1] / fullResolution[1], globalCoord[0] / fullResolution[0]]','UV axis swap',['uv-map-tile']], ['color-grid-golden-ratio','0.6180340051651001','0.5','cell hue progression',['color-grid']], ['dot-grid-threshold','smoothstep(0.11999999731779099, 0.15000000596046448, dist)','smoothstep(0.5, 0.6000000238418579, dist)','dot radius threshold',['dot-grid']]
]
const structural=[{name:'dead-cpu-float-helper',anchor:'function cpu_float (value)',replacement:'function cpu_float_unused (value)',mechanism:'structural-only dead helper rename'},{name:'source-comment-only',anchor:'Render a number at a position within a cell',replacement:'Render a number at a position within a cell (authenticated)',mechanism:'structural-only comment mutation'}]
async function render(factory,c,api){ const b=api.create({width:c.width,height:c.height,uniforms:{gridSize:c.gridSize|0,pattern:c.pattern|0},tileOffset:new Float32Array(c.tileOffset),fullResolution:new Float32Array(c.fullResolution),time:0}); const a=new api.Surface(c.width,c.height); api.run({kernel:api.bind(factory,b),destination:a}); const d=new api.Surface(c.width,c.height); api.run({kernel:api.bind(factory,b),destination:d}); const rgba=a.toRgba8(), rgba2=d.toRgba8(); return {...c,controls:{resolution:[c.width,c.height],tileOffset:c.tileOffset,fullResolution:c.fullResolution,gridSize:c.gridSize,pattern:c.pattern},output_f32_words_le:words(a.data),output_f32_sha256:hash(bytes(a.data)),output_rgba8_bytes:Array.from(rgba),output_rgba8_sha256:hash(bytes(rgba)),alpha:{f32_word:bits(a.data[3]),rgba8_byte:rgba[3]},repeat_identical_float32:Buffer.compare(bytes(a.data),bytes(d.data))===0,repeat_identical_rgba8:Buffer.compare(bytes(rgba),bytes(rgba2))===0,repeat_distinct_data_objects:a!==d,repeat_distinct_backing_buffers:a.data.buffer!==d.data.buffer} }

async function buildFixture(cpu){ const importClosure=verify(cpu); const source=fs.readFileSync(path.join(root,sourceRel)); if(source.length!==sourceBytes||hash(source)!==sourceSha)throw Error('source provenance drift'); const [k,g,r,p,s,catalog]=await Promise.all([import(pathToFileURL(path.join(cpu,'src/effects/generated/canonical-kernels.js'))),import(pathToFileURL(path.join(cpu,'src/csl/glsl-kernel.js'))),import(pathToFileURL(path.join(cpu,'src/csl/glsl-runtime.js'))),import(pathToFileURL(path.join(cpu,'src/runtime/pass-runner.js'))),import(pathToFileURL(path.join(cpu,'src/runtime/surface.js'))),import(pathToFileURL(path.join(cpu,'src/effects/catalog.js')))]); const factory=k.canonicalKernelFactories[key], publicFactory=catalog.kernelFactories.get(key), adapterFactory=catalog.canonicalAdapterFactories[key], canonicalOwnKey=Object.prototype.hasOwnProperty.call(k.canonicalKernelFactories,key), adapterOwnKey=Object.prototype.hasOwnProperty.call(catalog.canonicalAdapterFactories,key); if(!factory||factory.name!=='canonicalFactory277'||!canonicalOwnKey||publicFactory!==factory||adapterOwnKey)throw Error('canonical/public/adapter identity drift'); const api={create:g.createCanonicalBindings,bind:r.bindGlslKernel,run:p.runPass,Surface:s.Surface}; const rendered=[]; for(const c of cases)rendered.push(await render(factory,c,api)); const ledger=[]; for(const [name,anchor,replacement,mechanism,witnessCases] of mutationSpecs){ const text=factory.toString(); if(text.split(anchor).length!==2)throw Error(`mutation anchor not unique: ${name}`); const mutatedText=text.replace(anchor,replacement), mf=(0,eval)(`(${mutatedText})`), results=[]; for(const c of cases){const base=rendered.find(x=>x.name===c.name), cand=await render(mf,c,api), q=exact({width:base.width,height:base.height,f32:base.output_f32_words_le,rgba:base.output_rgba8_bytes},{width:cand.width,height:cand.height,f32:cand.output_f32_words_le,rgba:cand.output_rgba8_bytes});results.push({case:c.name,differs:!q.equal,reason:q.reason||'equal',changed_float32_lanes:base.output_f32_words_le.filter((v,i)=>v!==cand.output_f32_words_le[i]).length,changed_rgba8_bytes:base.output_rgba8_bytes.filter((v,i)=>v!==cand.output_rgba8_bytes[i]).length,first_mismatch:q.first??null})} const ws=results.filter(x=>witnessCases.includes(x.case)&&x.changed_float32_lanes&&x.changed_rgba8_bytes);if(ws.length!==witnessCases.length)throw Error(`mutation witness missing: ${name}`);ledger.push({name,group:name.split('-')[0],mechanism,source_relative_path:sourceRel,source_anchor:anchor,replacement,anchor_occurrence_count:1,source_anchor_sha256:hash(Buffer.from(anchor)),replacement_sha256:hash(Buffer.from(replacement)),canonical_factory_sha256:hash(Buffer.from(text)),mutated_factory_sha256:hash(Buffer.from(mutatedText)),results,result_sha256:hash(Buffer.from(JSON.stringify({name,results}))),witness_cases:witnessCases,required_witness_results:ws}) } const doc={schema:'noisemaker-for-cpp.testPattern.pixel-parity.v1',schema_version:1,program_key:key,effect_key:'synth/testPattern',runtime_key:key,corpus_revision:revision,upstream_revision:'117a236679d1db3ab8f0e278230ece277b57564c',factory:{name:factory.name,text_sha256:hash(Buffer.from(factory.toString())),public_direct_identity:publicFactory===factory,canonical_own_key:canonicalOwnKey,adapter_own_key:adapterOwnKey},binding_names:['resolution','tileOffset','fullResolution','gridSize','pattern'],binding_abi:{resolution:'Vec2',tileOffset:'Vec2',fullResolution:'Vec2',gridSize:'int32',pattern:'int32'},source_uniform_abi:{resolution:'vec2',tileOffset:'vec2',fullResolution:'vec2',gridSize:'int',pattern:'int'},input_contract:{kind:'source-only',runtime_input_path:'none',lifetime_claimed:false,immutability_claimed:false,reason:'Test Pattern has no sampler or input texture path'},exactness_contract:{float32:'raw little-endian uint32 words; signed zero and NaN payloads significant',rgba8:'complete independent RGBA8 byte arrays',tolerance:'none',comparison_order:'dimensions, counts, every float32 word, every RGBA8 byte'},comparer_self_tests:comparer(),authority:{oracle:'live canonical factory from immutable CPU snapshot',live_checkout_rejected:true,leaf_symlink_rejected:true,parent_alias_accepted:true,import_closure:importClosure},provenance:{source:{relative_path:sourceRel,bytes:sourceBytes,sha256:sourceSha},factory:{relative_path:'src/effects/generated/canonical-kernels.js',sha256:closure['src/effects/generated/canonical-kernels.js']},cpu_root:'<immutable-cpu-snapshot-root>'},render_cases:rendered,mutation_contract:{behavioral_names:ledger.map(x=>x.name),structural_names:structural.map(x=>x.name),control_group:'all patterns and source-specific branches'},behavioral_mutation_ledger:ledger,structural_mutation_ledger:structural.map(x=>({...x,source_relative_path:sourceRel,source_anchor_sha256:hash(Buffer.from(x.anchor)),replacement_sha256:hash(Buffer.from(x.replacement)),no_pixel_witness_claimed:true})),control_group:{repeatability:{case:'color-bars',identical_float32:rendered.find(x=>x.name==='color-bars').repeat_identical_float32,identical_rgba8:rendered.find(x=>x.name==='color-bars').repeat_identical_rgba8},independent_output_storage:{case:'color-bars',distinct_data_objects:rendered.find(x=>x.name==='color-bars').repeat_distinct_data_objects,distinct_backing_buffers:rendered.find(x=>x.name==='color-bars').repeat_distinct_backing_buffers},public_direct_identity:publicFactory===factory,canonical_own_key:canonicalOwnKey,adapter_own_key:adapterOwnKey},claim_boundaries:{authority:'immutable CPU snapshot only',runtime:'exact Float32 and RGBA8 bytes',input:'source-only kernel; no input lifetime or immutability claim',structural_mutations:'structure authenticated; no pixel witness claimed'}}; const json=JSON.stringify(doc,null,2)+'\n'; const md=`# Test Pattern pixel-parity oracle\n\nProgram: \`${key}\`. Source: \`${sourceRel}\` (${sourceBytes} bytes, \`${sourceSha}\`).\n\nInput contract: **source-only**. Test Pattern has no sampler or input texture path; no input lifetime or immutability claim is made.\n\nCases: **${rendered.length}**. Behavioral mutants: **${ledger.length}**, each has Float32 and RGBA8 witnesses. Structural-only mutants: **${structural.length}**.\n\n| Case | Size | Pattern | Float32 SHA-256 | RGBA8 SHA-256 |\n| --- | ---: | ---: | --- | --- |\n${rendered.map(c=>`| ${c.name} | ${c.width}x${c.height} | ${c.pattern} | ${c.output_f32_sha256} | ${c.output_rgba8_sha256} |`).join('\n')}\n`; return {json, report: md, counts: {cases: rendered.length, mutations: ledger.length, structural: structural.length}} }

async function writeFixture(cpu) {
  const built = await buildFixture(cpu)
  fs.writeFileSync(out, built.json)
  fs.writeFileSync(`${out}.sha256`, `${hash(Buffer.from(built.json))}  ${path.basename(out)}\n`)
  fs.writeFileSync(report, built.report)
  fs.writeFileSync(`${report}.sha256`, `${hash(Buffer.from(built.report))}  ${path.basename(report)}\n`)
  verifyAnchoredCoherence()
  verifyCoherence()
  console.log(`testPattern oracle: ${built.counts.cases} cases, ${built.counts.mutations} behavioral mutations, ${built.counts.structural} structural-only`)
}
async function checkFixture(cpu) {
  verifyAnchoredCoherence()
  const built = await buildFixture(cpu)
  if (Buffer.compare(Buffer.from(built.json), checkedAsset(out)) !== 0) throw Error('oracle rebuild drift')
  if (Buffer.compare(Buffer.from(built.report), checkedAsset(report)) !== 0) throw Error('report rebuild drift')
  verifyAnchoredCoherence()
  verifyCoherence()
  console.log('testPattern oracle fixture ok (authority, closure, source, rebuild, anchored coherence, and sidecars verified)')
}

const argv = process.argv.slice(2)
const modes = argv.filter((token) => ['--write','--check','--self-test'].includes(token))
if (modes.length !== 1) throw Error('choose exactly one of --write, --check, or --self-test')
const mode = modes[0], cpuIndex = argv.indexOf('--cpu-root')
if (cpuIndex < 0) {
  if (argv.length !== 1 || !process.env.NOISEMAKER_CPU_ROOT) throw Error('--cpu-root <immutable snapshot> or NOISEMAKER_CPU_ROOT is required')
} else if (cpuIndex + 1 >= argv.length || argv.length !== 3 || argv.some((token, index) => index !== cpuIndex && index !== cpuIndex + 1 && token !== mode)) {
  throw Error('usage: --write|--check|--self-test --cpu-root ROOT')
}
const cpu = authority(argv)
if (mode === '--check') await checkFixture(cpu)
else await writeFixture(cpu)

