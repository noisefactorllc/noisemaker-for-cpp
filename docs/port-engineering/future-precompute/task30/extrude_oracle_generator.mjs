import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outPath = path.join(here, 'extrude-oracles.json')
const reportPath = path.join(here, 'extrude-oracle-report.md')
const key = 'filter/extrude:extrude'
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourcePath = `tools/glslcpp/corpus/${revision}/sources/filter/extrude/extrude.glsl`
const canonicalPath = '../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js'
const catalogPath = '../noisemaker-for-cpu/src/effects/catalog.js'
const adapterPath = '../noisemaker-for-cpu/src/effects/adapters/index.js'
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function f32Bits(value) { const a = new Float32Array([value]); return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function sameBytes(a, b) { return Buffer.compare(bytes(a.data), bytes(b.data)) === 0 }
function occurrences(text, needle) { return text.split(needle).length - 1 }
function evaluated(text) { return (0, eval)(`(${text})`) }

const provenance = {
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
  source_sha256: '3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29',
  canonical_factory_name: 'canonicalFactory51',
  canonical_factory_to_string_sha256: '7d5cdd050eaa13282060557e7d6a097ef8300c1b71f31c13d782680eb58d91ef',
}

if (sha256(fs.readFileSync(canonicalPath)) !== provenance.canonical_kernels_sha256) throw new Error('canonical runtime drift')
if (sha256(fs.readFileSync(catalogPath)) !== provenance.public_catalog_sha256) throw new Error('catalog drift')
if (sha256(fs.readFileSync(adapterPath)) !== provenance.adapter_index_sha256) throw new Error('adapter registry drift')
if (sha256(fs.readFileSync(sourcePath)) !== provenance.source_sha256) throw new Error('source drift')
const canonical = canonicalKernelFactories[key]
if (canonical?.name !== provenance.canonical_factory_name || sha256(canonical.toString()) !== provenance.canonical_factory_to_string_sha256) throw new Error('factory drift')
if (kernelFactories.get(key) !== canonical || canonicalAdapterFactories[key] !== undefined) throw new Error('public factory is not direct canonical identity')

const factoryText = canonical.toString()
const topLine = 'var topHit = all(lessThanEqual(abs(new $runtime.PooledFloat32Array([P[0] - faceCenter[0], P[1] - faceCenter[1]])), faceHalf));'
const sideLine = 'var sideHit = (!topHit) && (all(lessThanEqual(abs(new $runtime.PooledFloat32Array([P[0] - cellC[0], P[1] - cellC[1]])), halfCell)));'
if (occurrences(factoryText, topLine) !== 1 || occurrences(factoryText, sideLine) !== 1) throw new Error('exact relational factory shape drift')
const mutations = [
  { id: 'top-lane-any', hazard: 'all-reduction', factory: evaluated(factoryText.replace('const { float,', 'const { any, float,').replace(topLine, topLine.replace('all(', 'any('))) },
  { id: 'side-lane-any', hazard: 'all-reduction', factory: evaluated(factoryText.replace('const { float,', 'const { any, float,').replace(sideLine, sideLine.replace('all(', 'any('))) },
  { id: 'top-strict-less', hazard: 'inclusive-relational', factory: evaluated(factoryText.replace('const { float,', 'const { lessThan, float,').replace(topLine, topLine.replace('lessThanEqual', 'lessThan'))) },
  { id: 'side-strict-less', hazard: 'inclusive-relational', factory: evaluated(factoryText.replace('const { float,', 'const { lessThan, float,').replace(sideLine, sideLine.replace('lessThanEqual', 'lessThan'))) },
]

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    data[i] = f((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
    data[i + 1] = f((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
    data[i + 2] = f((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
    data[i + 3] = f((((7 * x + 11 * y + phase) % 29) + 5) / 37)
  }
  return new Surface(width, height, data)
}

const cases = [
  { name: 'blocks-default-luminance-solid', width: 13, height: 9, phase: 1, defines: { EXTRUDE_TYPE: 0, DEPTH_SOURCE: 0 }, uniforms: { size: f(4), depth: f(30), solidFront: true } },
  { name: 'blocks-depth-zero-window', width: 11, height: 7, phase: 2, defines: { EXTRUDE_TYPE: 0, DEPTH_SOURCE: 0 }, uniforms: { size: f(5), depth: f(0), solidFront: false } },
  { name: 'blocks-max-depth-luminance-window', width: 15, height: 10, phase: 3, defines: { EXTRUDE_TYPE: 0, DEPTH_SOURCE: 0 }, uniforms: { size: f(4), depth: f(100), solidFront: false } },
  { name: 'blocks-random-solid-tiled', width: 9, height: 6, phase: 4, defines: { EXTRUDE_TYPE: 0, DEPTH_SOURCE: 1 }, uniforms: { size: f(4), depth: f(82), solidFront: true }, tileOffset: [3, 5], fullResolution: [17, 15] },
  { name: 'pyramids-luminance-solid', width: 12, height: 8, phase: 5, defines: { EXTRUDE_TYPE: 1, DEPTH_SOURCE: 0 }, uniforms: { size: f(4), depth: f(65), solidFront: true } },
  { name: 'pyramids-random-window-tiled', width: 10, height: 7, phase: 6, defines: { EXTRUDE_TYPE: 1, DEPTH_SOURCE: 1 }, uniforms: { size: f(5), depth: f(91), solidFront: false }, tileOffset: [4, 2], fullResolution: [19, 13] },
]

function render(factory, definition) {
  const input = patternedSurface(definition.width, definition.height, definition.phase)
  const original = new Float32Array(input.data)
  const tileOffset = new Float32Array(definition.tileOffset ?? [0, 0])
  const fullResolution = new Float32Array(definition.fullResolution ?? [definition.width, definition.height])
  const kernel = bindCanonicalKernel(factory, { width: definition.width, height: definition.height,
    uniforms: { ...definition.uniforms, ...definition.defines }, textures: { inputTex: input }, tileOffset, fullResolution })
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel, destination: output })
  if (Buffer.compare(bytes(input.data), bytes(original)) !== 0) throw new Error(`${definition.name}: input mutated`)
  return { input, output }
}
function probe(surface, x, y) {
  const i = (y * surface.width + x) * 4, values = Array.from(surface.data.slice(i, i + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}
function probes(surface) { return [[0,0],[surface.width-1,0],[0,surface.height-1],[surface.width-1,surface.height-1],[Math.floor(surface.width/2),Math.floor(surface.height/2)]].map(([x,y]) => probe(surface,x,y)) }
function result(surface) {
  const rgba = surface.toRgba8(); let nonfinite = 0
  for (const lane of surface.data) if (!Number.isFinite(lane)) nonfinite += 1
  return { f32_sha256: sha256(bytes(surface.data)), rgba8_sha256: sha256(bytes(rgba)), finite_lanes: surface.data.length - nonfinite, nonfinite_lanes: nonfinite, probes: probes(surface) }
}
function diff(reference, candidate) {
  const rgbaA=reference.toRgba8(), rgbaB=candidate.toRgba8(); let f32=0, rgba=0
  for(let i=0;i<reference.data.length;i++) if(f32Bits(reference.data[i])!==f32Bits(candidate.data[i])) f32++
  for(let i=0;i<rgbaA.length;i++) if(rgbaA[i]!==rgbaB[i]) rgba++
  return { same_f32_bytes: sameBytes(reference,candidate), same_rgba8_bytes: Buffer.compare(bytes(rgbaA),bytes(rgbaB))===0, different_f32_lanes:f32, different_rgba8_bytes:rgba, candidate_f32_sha256:sha256(bytes(candidate.data)), candidate_rgba8_sha256:sha256(bytes(rgbaB)) }
}

function directRows() {
  const rows = [
    [[0,0],[0,0]], [[1,2],[1,2]], [[1,2],[1,3]], [[1,2],[2,2]],
    [[-0,0],[0,0]], [[-1,5],[-1,4]], [[16777216,16777216],[16777216,16777216]],
  ]
  return rows.map(([left,right]) => {
    const lanes = [left[0] <= right[0], left[1] <= right[1]]
    return { left:left.map(f), right:right.map(f), left_bits:left.map(x=>f32Bits(f(x))), right_bits:right.map(x=>f32Bits(f(x))), less_than_equal_lanes:lanes, all_result:lanes[0]&&lanes[1], any_result:lanes[0]||lanes[1], strict_less_lanes:[left[0]<right[0],left[1]<right[1]] }
  })
}

function build() {
  const refs = new Map()
  const records = cases.map(c => { const a=render(canonical,c), b=render(canonical,c); if(!sameBytes(a.output,b.output)) throw new Error(`${c.name}: repeat mismatch`); refs.set(c.name,a.output); return { name:c.name, dimensions:{width:c.width,height:c.height}, phase:c.phase, defines:c.defines, uniforms:c.uniforms, tile_offset:c.tileOffset??[0,0], full_resolution:c.fullResolution??[c.width,c.height], input:{f32_sha256:sha256(bytes(a.input.data)),probes:probes(a.input)}, output:result(a.output), repeat_identity:true, input_immutable:true } })
  const mutationResults = mutations.map(m => ({ id:m.id,hazard:m.hazard,case_results:cases.map(c=>({case:c.name,...diff(refs.get(c.name),render(m.factory,c).output)})) }))
  for(const m of mutationResults) if(!m.case_results.some(x=>!x.same_f32_bytes)) throw new Error(`${m.id}: no discriminating case`)
  return { schema:'noisemaker-for-cpp.future-precompute.task30.extrude-relational-reduction-oracles.v1',corpus_revision:revision,provenance:{...provenance,node:process.version,public_identity:true,adapter_absent:true},program:{key,defines:{EXTRUDE_TYPE:0,DEPTH_SOURCE:0},profile_candidate:'extrude-bvec2-relational-reduction-v1',source_raw_bytes:16945,source_sha256:provenance.source_sha256,normalized_bytes:5020,normalized_sha256:'823698d954e1f2f890414a22e6792ca0ca87484ee21d9043cd3c1a347fd7a4ac',exact_closure:{lessThanEqual_vec2_sites:2,all_bvec2_sites:2,result:'two bvec2 temporaries consumed immediately by all'}},fixture:{input:'deterministic top-down F32 RGBA phase pattern',fragment_origin:'bottom-left runPass coordinates'},cases:records,public_factory_mutations:mutationResults,direct_relational_cases:directRows(),negative_closure:{any_other_key_or_define_map:'reject',any_or_lessThan_or_other_width:'reject',stored_or_escaped_bvec2:'reject',generic_relational_or_reduction_capability:'forbidden'}}
}
function report(d) { const lines=['# Task30 Extrude relational/reduction oracle report','',`Cases: **${d.cases.length}**; public mutations: **${d.public_factory_mutations.length}**; direct rows: **${d.direct_relational_cases.length}**.`,'','| Case | Size | Defines | F32 SHA-256 | RGBA8 SHA-256 |','| --- | --- | --- | --- | --- |']; for(const c of d.cases) lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.defines.EXTRUDE_TYPE}/${c.defines.DEPTH_SOURCE} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` |`); lines.push('','| Mutation | Divergent cases |','| --- | ---: |'); for(const m of d.public_factory_mutations) lines.push(`| ${m.id} | ${m.case_results.filter(x=>!x.same_f32_bytes).length}/${m.case_results.length} |`); lines.push('','All factory mutations are output-discriminating. Native tests must also execute and transcribe all direct relational rows lane-by-lane; equality-boundary rows distinguish `<=` from `<`, and mixed-lane rows distinguish `all` from `any`.',''); return lines.join('\n') }
const data=build(), json=`${JSON.stringify(data,null,2)}\n`, md=`${report(data)}\n`
if(process.argv.includes('--check')) { if(fs.readFileSync(outPath,'utf8')!==json||fs.readFileSync(reportPath,'utf8')!==md) throw new Error('oracle drift'); console.log(`extrude oracle fixture ok (${cases.length} cases)`) } else { fs.writeFileSync(outPath,json); fs.writeFileSync(reportPath,md); console.log(outPath) }
