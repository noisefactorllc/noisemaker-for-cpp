import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'task-22-oracles.json')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision)
const canonicalKernelsPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const adapterPath = path.join(cpuRoot, 'src/effects/adapters/crt.js')
const key = 'filter/crt:crt'
const source = 'sources/filter/crt/crt.glsl'
const expectedRawBytes = 19560
const expectedRawSha256 = '62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c'
const expectedNormalizedSha256 = 'acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe'
const expectedCanonicalKernelsSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const expectedAdapterFileSha256 = 'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc'
const expectedFactorySha256 = '6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303'
const expectedAdapterFactorySha256 = '240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7'
const expectedFunctionTupleFingerprint = 'f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72'
const expectedWholeProgramFingerprint = 'f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc'
const f = Math.fround
const frame = 17
const deltaTime = f(1 / 60)
const runtimeSeed = f(29)
const TAU = f(6.283185307179586)
const INV_TAU = f(1 / 6.283185307179586)
const sourceFunctions = Object.freeze([
  'adjust_hue', 'adjust_saturation', 'animated_simplex_value', 'apply_vignette', 'as_u32',
  'blend_cosine', 'blend_linear', 'clamp01', 'clamp_index', 'compute_lens_offsets',
  'compute_singularity', 'fade', 'fade_vec3', 'freq_for_shape', 'get_scanline_base_values',
  'get_scanline_value_interpolated', 'hash3', 'hsv_to_rgb', 'lerp', 'main', 'mod289_vec3',
  'mod289_vec4', 'normalized_sine', 'periodic_value', 'permute', 'random_scalar',
  'rgb_to_hsv', 'sample_scanline_bilinear', 'simplex_noise', 'simplex_random',
  'singularity_mask', 'taylor_inv_sqrt', 'value_noise_3d', 'wrap_float', 'wrap_unit',
])

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function countOccurrences(value, needle) { return value.split(needle).length - 1 }
function f32Bits(value) { const v = new Float32Array([value]); return `0x${new DataView(v.buffer).getUint32(0, true).toString(16).padStart(8, '0')}` }
function scalarRecord(value, type = 'float') { return type === 'int' ? { glsl_type: 'int', value } : { glsl_type: 'float', value, f32_bits_le: f32Bits(value) } }
function vec2Record(value) { return { glsl_type: 'vec2', values: Array.from(value), f32_bits_le: Array.from(value, f32Bits) } }

const rawSource = fs.readFileSync(path.join(corpus, source))
if (rawSource.byteLength !== expectedRawBytes || sha256(rawSource) !== expectedRawSha256) throw new Error('pinned CRT source drift')
if (sha256(fs.readFileSync(canonicalKernelsPath)) !== expectedCanonicalKernelsSha256) throw new Error('pinned canonical runtime drift')
if (sha256(fs.readFileSync(adapterPath)) !== expectedAdapterFileSha256) throw new Error('pinned CRT adapter drift')
const canonicalFactory = canonicalKernelFactories[key]
const adapterFactory = canonicalAdapterFactories[key]
if (canonicalFactory?.name !== 'canonicalFactory44' || adapterFactory?.name !== 'crtFactory') throw new Error('pinned CRT factory identity drift')
if (kernelFactories.get(key) !== adapterFactory) throw new Error('public CRT dispatch no longer selects adapter')
const canonicalFactoryText = canonicalFactory.toString()
if (sha256(Buffer.from(canonicalFactoryText)) !== expectedFactorySha256) throw new Error('pinned canonical CRT factory drift')
if (sha256(Buffer.from(adapterFactory.toString())) !== expectedAdapterFactorySha256) throw new Error('pinned CRT adapter factory drift')
for (const name of sourceFunctions) if (countOccurrences(canonicalFactoryText, `function ${name} (`) !== 1) throw new Error(`function shape drift: ${name}`)

function metalSine(value) {
  const turns = f(value * INV_TAU)
  const phase = turns - Math.floor(turns)
  return f(Math.sin(phase * TAU))
}
function withMetalSine(factory) {
  return function task22MetalSineFactory($bindings, $runtime) {
    const runtime = Object.create($runtime)
    const sin = value => {
      if (!ArrayBuffer.isView(value) && !Array.isArray(value)) return metalSine(value)
      const out = $runtime.alloc(value.length)
      for (let index = 0; index < value.length; index += 1) out[index] = metalSine(value[index])
      return out
    }
    runtime.stdlib = Object.freeze({ ...$runtime.stdlib, sin })
    return factory($bindings, runtime)
  }
}

const defaults = Object.freeze({ alpha: f(0.5), speed: f(1), seed: 1, renderScale: f(1) })
const caseDefinitions = Object.freeze([
  { name: 'alpha-zero-exact-copy-tiled', size: [13, 9], tileOffset: [7, 11], fullResolution: [41, 29], time: f(0.375), uniforms: { ...defaults, alpha: f(0), speed: f(2), seed: 37, renderScale: f(2) }, exactCopy: true, coverage: ['uniform-alpha-zero-early-return', 'exact-F32-copy', 'shadowed-local-alpha-not-reached', 'tiled-bindings-not-reached'] },
  { name: 'alpha-negative-clamps-zero-copy', size: [9, 7], tileOffset: [3, 5], fullResolution: [23, 19], time: f(0.625), uniforms: { ...defaults, alpha: f(-0.25), seed: 19 }, exactCopy: true, coverage: ['uniform-alpha-clamp-lower-bound', 'exact-F32-copy'] },
  { name: 'default-landscape-untiled', size: [13, 9], tileOffset: [0, 0], fullResolution: [13, 9], time: f(0.375), uniforms: { ...defaults }, coverage: ['metadata-defaults', 'landscape-frequency', 'normal-three-fetch-path', 'metal-sine-adapter'] },
  { name: 'alpha-above-one-clamps-and-preserves-input-alpha', size: [13, 9], tileOffset: [0, 0], fullResolution: [13, 9], time: f(0.4375), uniforms: { ...defaults, alpha: f(1.75), seed: 11 }, coverage: ['uniform-alpha-clamp-upper-bound', 'shadowed-local-alpha', 'output-input-alpha-preservation'] },
  { name: 'landscape-tiled-render-scale-two', size: [13, 9], tileOffset: [7, 11], fullResolution: [47, 23], time: f(0.4375), uniforms: { alpha: f(0.75), speed: f(1.75), seed: 37, renderScale: f(2) }, coverage: ['tiled-coordinate-chain', 'renderScale-two', 'extreme-landscape-frequency', 'red-blue-local-x', 'nondefault-seed-time-speed'] },
  { name: 'portrait-tiled-fractional-render-scale', size: [9, 13], tileOffset: [5, 3], fullResolution: [23, 37], time: f(0.6125), uniforms: { alpha: f(0.625), speed: f(2), seed: 100, renderScale: f(1.5) }, coverage: ['portrait-frequency', 'fractional-renderScale', 'tiled-coordinate-chain', 'red-blue-order'] },
  { name: 'speed-zero-nonzero-time', size: [13, 9], tileOffset: [4, 6], fullResolution: [31, 25], time: f(0.875), uniforms: { alpha: f(0.875), speed: f(0), seed: 19, renderScale: f(1) }, coverage: ['shadowed-speed-zero', 'animated-simplex-short-circuit', 'scanline-time-times-speed-zero'] },
  { name: 'time-zero-positive-speed', size: [13, 9], tileOffset: [3, 2], fullResolution: [29, 21], time: f(0), uniforms: { alpha: f(0.875), speed: f(1.5), seed: 53, renderScale: f(1) }, coverage: ['shadowed-time-zero', 'animated-simplex-short-circuit', 'nonzero-speed'] },
  { name: 'full-resolution-zero-fallback', size: [13, 9], tileOffset: [2, 1], fullResolution: [0, 0], time: f(0.3125), uniforms: { alpha: f(0.75), speed: f(1.25), seed: 11, renderScale: f(1) }, coverage: ['fullResolution-x-nonpositive-fallback', 'resolution-substitution'] },
  { name: 'square-large-time-max-metadata', size: [11, 11], tileOffset: [3, 2], fullResolution: [31, 31], time: f(12345.625), uniforms: { alpha: f(1), speed: f(5), seed: 100, renderScale: f(1.5) }, coverage: ['square-frequency-equality', 'large-angle-metal-sine-range-reduction', 'metadata-maxima'] },
  { name: 'render-scale-below-one-clamps', size: [13, 9], tileOffset: [0, 0], fullResolution: [13, 9], time: f(0.46875), uniforms: { alpha: f(0.5), speed: f(1.25), seed: 29, renderScale: f(0.5) }, coverage: ['rs-clamped-to-one', 'raw-renderScale-retained-at-aberration-remap'] },
])

function makeInput(width, height) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const lane = (y * width + x) * 4
    data[lane] = ((17 * x + 31 * y + 13) % 101) / 100
    data[lane + 1] = ((7 * x + 19 * y + 23) % 97) / 96
    data[lane + 2] = ((29 * x + 11 * y + 5) % 89) / 88
    data[lane + 3] = (((5 * x + 7 * y + 3) % 23) - 5) / 12
  }
  return new Surface(width, height, data)
}
function points(width, height) { return [[0,0],[width-1,0],[0,height-1],[width-1,height-1],[Math.floor(width/2),Math.floor(height/2)],[1,1],[width-2,height-2]].filter((p,i,a)=>a.findIndex(q=>q[0]===p[0]&&q[1]===p[1])===i) }
function probe(surface, x, y) { const i=(y*surface.width+x)*4; const values=Array.from(surface.data.slice(i,i+4)); return { at_top_down_xy:[x,y], values, f32_bits_le:values.map(f32Bits) } }
function render(factory, definition) {
  const [width,height]=definition.size; const input=makeInput(width,height)
  const kernel=bindCanonicalKernel(factory,{ width,height,time:definition.time,frame,deltaTime,seed:runtimeSeed,tileOffset:new Float32Array(definition.tileOffset),fullResolution:new Float32Array(definition.fullResolution),uniforms:definition.uniforms,textures:{inputTex:input} })
  const output=new Surface(width,height); runPass({kernel,destination:output,time:definition.time,seed:runtimeSeed}); return {input,output}
}
function metrics(input, output) {
  let finite=0, nonfinite=0, changed=0, changedRgb=0, exactPixels=0, alphaPreserved=0, alphaOutside=0
  for(let p=0;p<output.width*output.height;p+=1){const i=p*4;let exact=true,rgb=false;for(let l=0;l<4;l+=1){const a=output.data[i+l],b=input.data[i+l];Number.isFinite(a)?finite++:nonfinite++;if(f32Bits(a)!==f32Bits(b)){changed++;exact=false;if(l<3)rgb=true}}if(exact)exactPixels++;if(rgb)changedRgb++;if(f32Bits(output.data[i+3])===f32Bits(input.data[i+3]))alphaPreserved++;if(output.data[i+3]<0||output.data[i+3]>1)alphaOutside++}
  return {pixels:output.width*output.height,finite_lanes:finite,nonfinite_lanes:nonfinite,changed_f32_lanes:changed,changed_rgb_pixels:changedRgb,exact_input_pixels:exactPixels,alpha_preserved_pixels:alphaPreserved,alpha_out_of_unit_interval_pixels:alphaOutside}
}
function uniformsRecord(u){return {alpha:scalarRecord(u.alpha),speed:scalarRecord(u.speed),seed:scalarRecord(u.seed,'int'),renderScale:scalarRecord(u.renderScale)}}
const publicSurfaces=new Map()
function caseResult(definition){
  const first=render(adapterFactory,definition),second=render(adapterFactory,definition),a8=first.output.toRgba8(),b8=second.output.toRgba8()
  if(!sameBytes(first.output.data,second.output.data)||!sameBytes(a8,b8))throw new Error(`${definition.name}: public repeat drift`)
  const reconstructed=render(withMetalSine(canonicalFactory),definition).output
  if(!sameBytes(first.output.data,reconstructed.data)||!sameBytes(a8,reconstructed.toRgba8()))throw new Error(`${definition.name}: local adapter reconstruction drift`)
  if(definition.exactCopy&&!sameBytes(first.input.data,first.output.data))throw new Error(`${definition.name}: expected exact copy`)
  const m=metrics(first.input,first.output);if(m.nonfinite_lanes)throw new Error(`${definition.name}: nonfinite output`);if(!definition.exactCopy&&m.changed_rgb_pixels===0)throw new Error(`${definition.name}: uninformative`)
  if(m.alpha_preserved_pixels!==m.pixels)throw new Error(`${definition.name}: input alpha not preserved`)
  publicSurfaces.set(definition.name,first.output);const ps=points(...definition.size)
  return {name:definition.name,key,dimensions:{width:definition.size[0],height:definition.size[1]},tileOffset:vec2Record(new Float32Array(definition.tileOffset)),fullResolution:vec2Record(new Float32Array(definition.fullResolution)),time:scalarRecord(definition.time),uniforms:uniformsRecord(definition.uniforms),coverage:definition.coverage,input:{f32_sha256:sha256(bytes(first.input.data)),rgba8_sha256:sha256(bytes(first.input.toRgba8())),probes:ps.map(([x,y])=>probe(first.input,x,y))},output:{f32_sha256:sha256(bytes(first.output.data)),rgba8_sha256:sha256(bytes(a8)),probes:ps.map(([x,y])=>probe(first.output,x,y)),metrics:m},repeat_identity:{output_f32_bytes:true,output_rgba8_bytes:true},local_adapter_reconstruction_identity:{output_f32_bytes:true,output_rgba8_bytes:true}}
}
function replacedFactory(name,replacements){let text=canonicalFactoryText;const applied=[];for(const r of replacements){const actual=countOccurrences(text,r.from);if(actual!==r.count)throw new Error(`${name}: replacement count ${actual} != ${r.count}`);text=text.split(r.from).join(r.to);applied.push({...r,exact_replacement_count:r.count})}return {factory:(0,eval)(`(${text})`),applied}}
function diff(reference,mutated){let lanes=0,fb=0,rb=0,max=0;const a=bytes(reference.data),b=bytes(mutated.data),ar=reference.toRgba8(),br=mutated.toRgba8();for(let i=0;i<a.length;i++)fb+=a[i]!==b[i];for(let i=0;i<reference.data.length;i++)if(f32Bits(reference.data[i])!==f32Bits(mutated.data[i])){lanes++;if(Number.isFinite(reference.data[i])&&Number.isFinite(mutated.data[i]))max=Math.max(max,Math.abs(reference.data[i]-mutated.data[i]))}for(let i=0;i<ar.length;i++)rb+=ar[i]!==br[i];return {same_f32_bytes:fb===0,same_rgba8_bytes:rb===0,different_f32_bytes:fb,different_f32_lanes:lanes,different_rgba8_bytes:rb,max_absolute_f32_difference:max,mutated_f32_sha256:sha256(b),mutated_rgba8_sha256:sha256(bytes(br))}}

const exactCopyCases=['alpha-zero-exact-copy-tiled','alpha-negative-clamps-zero-copy']
const mutationDefinitions=Object.freeze([
  {name:'public-metal-sine-disabled',contract:'uses raw canonical Math.sin instead of required public CRT reduced-turn sine adapter',directRaw:true,mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two','square-large-time-max-metadata'],mustMatch:exactCopyCases},
  {name:'uniform-time-local-alias-offset',contract:'perturbs only the shadow-safe local time copy',r:[{from:'var _local_time_1 = time;',to:'var _local_time_1 = time + 0.125;',count:1}],mustDiverge:['default-landscape-untiled','time-zero-positive-speed'],mustMatch:exactCopyCases.concat(['speed-zero-nonzero-time'])},
  {name:'uniform-speed-local-alias-offset',contract:'perturbs only the shadow-safe local speed copy',r:[{from:'var _local_speed_1 = speed;',to:'var _local_speed_1 = speed + 0.25;',count:1}],mustDiverge:['default-landscape-untiled','time-zero-positive-speed'],mustMatch:exactCopyCases},
  {name:'output-alpha-uses-uniform-not-shadowed-input',contract:'writes uniform alpha instead of base_sample alpha, exposing local alpha shadow identity',r:[{from:'fragColor[3] = base_sample[3]',to:'fragColor[3] = alpha',count:1}],mustDiverge:['default-landscape-untiled','alpha-above-one-clamps-and-preserves-input-alpha'],mustMatch:[]},
  {name:'uniform-alpha-clamp-disabled',contract:'uses raw uniform alpha for the early return and final mix',r:[{from:'var alphaVal = clamp(alpha, 0, 1);',to:'var alphaVal = alpha;',count:1}],mustDiverge:['alpha-negative-clamps-zero-copy','alpha-above-one-clamps-and-preserves-input-alpha'],mustMatch:['alpha-zero-exact-copy-tiled']},
  {name:'render-scale-clamp-disabled',contract:'uses raw renderScale for scaled dimensions instead of max(renderScale,1)',r:[{from:'var rs = max(renderScale, 1);',to:'var rs = renderScale;',count:1}],mustDiverge:['render-scale-below-one-clamps'],mustMatch:caseDefinitions.filter(c=>c.uniforms.renderScale>=1).map(c=>c.name)},
  {name:'full-resolution-fallback-disabled',contract:'selects zero fullResolution instead of resolution at x equals zero',r:[{from:'var fullRes = fullResolution[0] > 0 ? fullResolution : resolution;',to:'var fullRes = fullResolution[0] >= 0 ? fullResolution : resolution;',count:1}],mustDiverge:['full-resolution-zero-fallback'],mustMatch:caseDefinitions.filter(c=>c.fullResolution[0]>0).map(c=>c.name)},
  {name:'shape-frequency-axes-unswapped',contract:'uses same-axis frequency instead of canonical cross-axis mapping',r:[{from:'var freq_x = max(freq[1], 1);\n  \tvar freq_y = max(freq[0], 1);',to:'var freq_x = max(freq[0], 1);\n  \tvar freq_y = max(freq[1], 1);',count:1}],mustDiverge:['landscape-tiled-render-scale-two','portrait-tiled-fractional-render-scale'],mustMatch:exactCopyCases.concat(['square-large-time-max-metadata'])},
  {name:'scanline-parity-forced-first-value',contract:'removes odd/even scanline selection',r:[{from:'return (scanline_index == 0 ? base_values[0] : base_values[1]);',to:'return base_values[0];',count:1}],mustDiverge:['default-landscape-untiled','portrait-tiled-fractional-render-scale'],mustMatch:exactCopyCases},
  {name:'red-tile-local-subtraction-disabled',contract:'uses red global x directly as local texture x',r:[{from:'var red_sample_local_x = red_sample_global_x - tileOffset[0];',to:'var red_sample_local_x = red_sample_global_x;',count:1}],mustDiverge:['landscape-tiled-render-scale-two','portrait-tiled-fractional-render-scale'],mustMatch:exactCopyCases.concat(['default-landscape-untiled'])},
  {name:'blue-tile-local-subtraction-disabled',contract:'uses blue global x directly as local texture x',r:[{from:'var blue_sample_local_x = blue_sample_global_x - tileOffset[0];',to:'var blue_sample_local_x = blue_sample_global_x;',count:1}],mustDiverge:['landscape-tiled-render-scale-two','portrait-tiled-fractional-render-scale'],mustMatch:exactCopyCases.concat(['default-landscape-untiled'])},
  {name:'red-channel-assembly-uses-blue',contract:'assembles output red from blue_blended rather than red_blended',r:[{from:'adjust_hue(red_blended, hue_shift)[0]',to:'adjust_hue(blue_blended, hue_shift)[0]',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
  {name:'restore-hue-disabled',contract:'removes the post-assembly negative hue restoration',r:[{from:'adjust_hue(color, -hue_shift).reduce((res,el,i)=>(res[i] = el, res), color);',to:'color = color;',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
  {name:'saturation-boost-disabled',contract:'removes the 1.125 saturation adjustment',r:[{from:'adjust_saturation(color, 1.125).reduce((res,el,i)=>(res[i] = el, res), color);',to:'color = color;',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
  {name:'vignette-alpha-forced-zero',contract:'retains vignette calls but forces their blend strength to zero',r:[{from:'var vignette_alpha = (random_scalar(seed_base + 3.1700000762939453)) * 0.17499999701976776;',to:'var vignette_alpha = 0;',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
  {name:'contrast-gain-1-25-to-1',contract:'removes final local-mean contrast gain',r:[{from:'(color[0] - local_mean) * 1.25 + local_mean',to:'(color[0] - local_mean) * 1 + local_mean',count:1},{from:'(color[1] - local_mean) * 1.25 + local_mean',to:'(color[1] - local_mean) * 1 + local_mean',count:1},{from:'(color[2] - local_mean) * 1.25 + local_mean',to:'(color[2] - local_mean) * 1 + local_mean',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
  {name:'local-mean-eager-f32-materialization',contract:'inserts an incorrect eager F32 boundary before multiplying by INV_THREE',r:[{from:'var local_mean = (color[0] + color[1] + color[2]) * INV_THREE;',to:'var local_mean = Math.fround(color[0] + color[1] + color[2]) * INV_THREE;',count:1}],mustDiverge:['default-landscape-untiled'],mustMatch:exactCopyCases},
  {name:'seed-base-disabled',contract:'removes integer seed from chromatic and vignette random controls',r:[{from:'var seed_base = 17 + (seed) * 73;',to:'var seed_base = 17;',count:1}],mustDiverge:['default-landscape-untiled','landscape-tiled-render-scale-two'],mustMatch:exactCopyCases},
])
function mutationResult(d){let factory,applied=[];if(d.directRaw)factory=canonicalFactory;else{const x=replacedFactory(d.name,d.r);factory=withMetalSine(x.factory);applied=x.applied}const results=caseDefinitions.map(c=>({case:c.name,...diff(publicSurfaces.get(c.name),render(factory,c).output)}));for(const n of d.mustDiverge??[]){const x=results.find(v=>v.case===n);if(!x||x.same_f32_bytes)throw new Error(`${d.name}: missing divergence ${n}`)}for(const n of d.mustMatch??[]){const x=results.find(v=>v.case===n);if(!x||!x.same_f32_bytes||!x.same_rgba8_bytes)throw new Error(`${d.name}: missing identity ${n}`)}return {name:d.name,contract:d.contract,replacements:applied,required_divergence_cases:d.mustDiverge??[],required_identity_cases:d.mustMatch??[],case_results:results}}

function build(){const cases=caseDefinitions.map(caseResult);const mutations=mutationDefinitions.map(mutationResult);return `${JSON.stringify({schema:'noisemaker-for-cpp.task22-crt.public-adapter-oracles.v1',corpus_revision:corpusRevision,provenance:{node:process.version,api:'public kernelFactories CRT adapter + bindCanonicalKernel + runPass + Surface',canonical_kernels_path:'src/effects/generated/canonical-kernels.js',canonical_kernels_sha256:expectedCanonicalKernelsSha256,adapter_path:'src/effects/adapters/crt.js',adapter_file_sha256:expectedAdapterFileSha256,canonical_factory_name:canonicalFactory.name,canonical_factory_to_string_sha256:expectedFactorySha256,adapter_factory_name:adapterFactory.name,adapter_factory_to_string_sha256:expectedAdapterFactorySha256,public_dispatch_is_adapter:true,reference_only:'expected outputs come from the pinned public CPU CRT adapter; raw canonical and counted factory mutations are diagnostics only'},program:{key,source,raw_source_bytes:expectedRawBytes,raw_source_sha256:expectedRawSha256,normalized_source_sha256:expectedNormalizedSha256,defines:{},numeric_literal_contract:'glsl-f32',required_runtime_compatibility:'crt-metal-sine-v1',typed_shape:{source_functions:sourceFunctions,function_count:35,loops:0,call_graph:'acyclic'},function_tuple_fingerprint:expectedFunctionTupleFingerprint,whole_program_fingerprint:expectedWholeProgramFingerprint,uniform_binding_signature:['PI:const float@1','TAU:const float@2','INV_THREE:const float@3','inputTex:sampler2D@4/S1','resolution:vec2@5','tileOffset:vec2@6','fullResolution:vec2@7','time:float@8','speed:float@9','seed:int@10','alpha:float@11','renderScale:float@12'],output_signature:'fragColor:vec4@88',pass_route:{inputs:{inputTex:'inputTex'},outputs:{fragColor:'outputTex'},uniforms:{alpha:'alpha',speed:'speed',seed:'seed'}},metadata_defaults:uniformsRecord(defaults),normal_path_dynamic_fetches_per_pixel:{base:1,red:1,blue:1,total:3,lod:0},shadow_contract:{uniform_time:'time@8',local_time:'time@193',uniform_speed:'speed@9',local_speed:'speed@194',uniform_alpha:'alpha@11',local_alpha:'alpha@205'}},fixture:{input:{construction:'asymmetric top-down Float32Array formula shared with Task21; alpha deliberately outside [0,1]'},fragment_origin:'bottom-left',float_bytes:'host little-endian Float32Array bytes',context:{frame,deltaTime:scalarRecord(deltaTime),runtime_seed:scalarRecord(runtimeSeed)},verification:'fresh double render, exact F32/RGBA8 repeat, finite lanes, input alpha preservation'},cases,mutation_sensitivity:{purpose:'locks public adapter, shadowed symbols, alpha return/mix, render/tile/full coordinates, scanline parity, channel order, hue/saturation/vignette/contrast, seed, and F32 association',mutations}},null,2)}\n`}
const expected=build()
if(process.argv.length===2)process.stdout.write(expected)
else if(process.argv.length===3&&process.argv[2]==='--write'){fs.writeFileSync(outputPath,expected,'utf8');process.stdout.write(`wrote ${path.basename(outputPath)}\n`)}
else if(process.argv.length===3&&process.argv[2]==='--check'){if(fs.readFileSync(outputPath,'utf8')!==expected)throw new Error('frozen oracle drift');process.stdout.write(`ok ${path.basename(outputPath)}\n`)}
else throw new Error('usage: node task-22-oracle-generator.mjs [--write|--check]')
