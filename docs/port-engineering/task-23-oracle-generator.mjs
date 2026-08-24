import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../noisemaker-for-cpu/src/effects/catalog.js'
import { bindCanonicalKernel } from '../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { runPass } from '../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../noisemaker-for-cpu/src/runtime/surface.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'task-23-oracles.json')
const reportPath = path.join(here, 'task-23-oracle-report.md')
const cpuRoot = '../noisemaker-for-cpu'
const cppRoot = '.'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpus = path.join(cppRoot, 'tools/glslcpp/corpus', corpusRevision)
const canonicalPath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js')
const canonicalSha256 = 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56'
const f = Math.fround
const frame = 23
const deltaTime = f(1 / 60)
const runtimeSeed = f(41)

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function sameBytes(a, b) { return a.byteLength === b.byteLength && Buffer.compare(bytes(a), bytes(b)) === 0 }
function countOccurrences(value, needle) { return value.split(needle).length - 1 }
function f32Bits(value) {
  const data = new Float32Array([value])
  return `0x${new DataView(data.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}
function scalarRecord(value, type = 'float') {
  return type === 'int' ? { glsl_type: 'int', value } : { glsl_type: 'float', value, f32_bits_le: f32Bits(value) }
}
function vec2Record(value) { return { glsl_type: 'vec2', values: Array.from(value), f32_bits_le: Array.from(value, f32Bits) } }

const programs = Object.freeze([
  {
    key: 'filter/bloom:ntapGather', source: 'sources/filter/bloom/ntapGather.glsl', rawBytes: 2196,
    rawSha256: 'f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237', normalizedSha256: '1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81',
    factoryName: 'canonicalFactory23', factorySha256: 'a737ac48f663f041f763677680ab5d5282482ab6d10143939de055b980c4207c',
    preFunctionsSha256: 'a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163', postFunctionsSha256: '66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270',
    preWholeSha256: '915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51', postWholeSha256: 'ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c', interfaceSha256: 'b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8',
    defines: {}, global: { symbol: 'MAX_TAPS', symbol_id: 8, value: 64 }, loop: { count: 1, trip_caps: [64], max_depth: 1, max_product: 64, entry_charge: 64 },
    bindingTypes: { radius: 'float', renderScale: 'float', taps: 'int' },
    bindingSignature: ['tileOffset:vec2@1', 'fullResolution:vec2@2', 'inputTex:sampler2D@3/S1', 'radius:float@4', 'renderScale:float@5', 'taps:int@6', 'MAX_TAPS:const int@8'],
    outputSignature: 'fragColor:vec4@7', fetchBounds: { static_texture_sites: 1, dynamic_min: 1, dynamic_max: 64 },
    cases: [
      { name: 'bloom-one-tap-zero-radius', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { radius: f(0), renderScale: f(1), taps: 1 }, coverage: ['one-trip-break', 'zero-radius', 'minimum-taps'] },
      { name: 'bloom-seven-taps-tiled', size: [11, 7], tile: [5, 3], full: [29, 19], uniforms: { radius: f(7.25), renderScale: f(1.5), taps: 7 }, coverage: ['early-break-at-seven', 'tiled-bindings', 'fractional-renderScale'] },
      { name: 'bloom-max-taps', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { radius: f(13.5), renderScale: f(2), taps: 64 }, coverage: ['full-64-trip-loop', 'maximum-bound', 'wide-radius'] },
    ],
    mutations: [
      { name: 'bloom-global-bound-64-to-8', contract: 'changes only MAX_TAPS from 64 to 8', from: 'var MAX_TAPS = 64;', to: 'var MAX_TAPS = 8;', diverge: ['bloom-max-taps'], match: ['bloom-one-tap-zero-radius'] },
      { name: 'bloom-tap-count-forced-one', contract: 'forces the runtime tap clamp result to one', from: 'var tapCount = clamp(taps, 1, MAX_TAPS);', to: 'var tapCount = 1;', diverge: ['bloom-seven-taps-tiled', 'bloom-max-taps'], match: ['bloom-one-tap-zero-radius'] },
    ],
  },
  {
    key: 'filter/directionalBlur:directionalBlur', source: 'sources/filter/directionalBlur/directionalBlur.glsl', rawBytes: 1153,
    rawSha256: '1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c', normalizedSha256: '587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668',
    factoryName: 'canonicalFactory47', factorySha256: 'a3803238488c9bd2fe786b931a0a2ba81a057d02f984017d8e10073c68873344',
    preFunctionsSha256: '8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa', postFunctionsSha256: '6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96',
    preWholeSha256: '30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153', postWholeSha256: '21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b', interfaceSha256: '3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858',
    defines: {}, global: { symbol: 'N', symbol_id: 6, value: 32 }, loop: { count: 1, trip_caps: [32], max_depth: 1, max_product: 32, entry_charge: 32 },
    bindingTypes: { angle: 'float', blurDistance: 'float' },
    bindingSignature: ['inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'angle:float@3', 'blurDistance:float@4', 'N:const int@6'], outputSignature: 'fragColor:vec4@5',
    fetchBounds: { static_texture_sites: 1, dynamic_min: 32, dynamic_max: 32 },
    cases: [
      { name: 'directional-zero-distance', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { angle: f(0), blurDistance: f(0) }, coverage: ['32-trip-zero-distance', 'angle-zero'] },
      { name: 'directional-positive-angle', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { angle: f(37.25), blurDistance: f(9.5) }, coverage: ['positive-angle', 'nonzero-jitter', 'clamped-edge-sampling'] },
      { name: 'directional-negative-angle-wide', size: [9, 13], tile: [0, 0], full: [9, 13], uniforms: { angle: f(-93.5), blurDistance: f(17.25) }, coverage: ['negative-angle', 'portrait', 'wide-blur'] },
    ],
    mutations: [
      { name: 'directional-global-bound-32-to-8', contract: 'changes only N from 32 to 8', from: 'var N = 32;', to: 'var N = 8;', diverge: ['directional-positive-angle', 'directional-negative-angle-wide'], match: [] },
      { name: 'directional-jitter-disabled', contract: 'sets the per-pixel comb jitter to zero', from: 'var jitter = (hash12(new $runtime.PooledFloat32Array([gl_FragCoord[0], gl_FragCoord[1]])) - 0.5) * tapStep;', to: 'var jitter = 0;', diverge: ['directional-positive-angle', 'directional-negative-angle-wide'], match: ['directional-zero-distance'] },
    ],
  },
  {
    key: 'filter/spinBlur:spinBlur', source: 'sources/filter/spinBlur/spinBlur.glsl', rawBytes: 3077,
    rawSha256: 'a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405', normalizedSha256: 'b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee',
    factoryName: 'canonicalFactory145', factorySha256: 'c6b97d30339acd21fc01d2d2cd31073c62d2ba82dbb80e95d9457b0f59737547',
    preFunctionsSha256: 'f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8', postFunctionsSha256: '974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51',
    preWholeSha256: '5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc', postWholeSha256: 'af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff', interfaceSha256: '4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723',
    defines: {}, global: { symbol: 'N', symbol_id: 9, value: 32 }, loop: { count: 1, trip_caps: [32], max_depth: 1, max_product: 32, entry_charge: 32 },
    bindingTypes: { amount: 'float', centerX: 'float', centerY: 'float' },
    bindingSignature: ['inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'fullResolution:vec2@4', 'amount:float@5', 'centerX:float@6', 'centerY:float@7', 'N:const int@9'], outputSignature: 'fragColor:vec4@8',
    fetchBounds: { static_texture_sites: 1, dynamic_min: 32, dynamic_max: 32 },
    cases: [
      { name: 'spin-zero-amount-centered', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { amount: f(0), centerX: f(0.5), centerY: f(0.5) }, coverage: ['32-trip-zero-arc', 'centered'] },
      { name: 'spin-positive-tiled-offcenter', size: [11, 7], tile: [5, 3], full: [29, 19], uniforms: { amount: f(77.5), centerX: f(0.27), centerY: f(0.68) }, coverage: ['positive-arc', 'tiled-global-coordinates', 'offcenter', 'aspect-correction'] },
      { name: 'spin-negative-portrait', size: [9, 13], tile: [2, 4], full: [21, 31], uniforms: { amount: f(-142.25), centerX: f(0.73), centerY: f(0.31) }, coverage: ['negative-arc', 'portrait', 'offcenter', 'clamped-local-sample'] },
    ],
    mutations: [
      { name: 'spin-global-bound-32-to-8', contract: 'changes only N from 32 to 8', from: 'var N = 32;', to: 'var N = 8;', diverge: ['spin-positive-tiled-offcenter', 'spin-negative-portrait'], match: [] },
      { name: 'spin-jitter-disabled', contract: 'sets the mirror-invariant per-pixel angular jitter to zero', from: 'var jitter = (hash12(jitterCoord) - 0.5) * angularStep;', to: 'var jitter = 0;', diverge: ['spin-positive-tiled-offcenter', 'spin-negative-portrait'], match: ['spin-zero-amount-centered'] },
    ],
  },
  {
    key: 'filter/strokes:stkSmear', source: 'sources/filter/strokes/stkSmear.glsl', rawBytes: 14787,
    rawSha256: 'dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db', normalizedSha256: '796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15',
    factoryName: 'canonicalFactory155', factorySha256: '8f82fbdc740e4bf5448e53823c833e22f37db0aacadad01bc4983a4e58e72010',
    preFunctionsSha256: '5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9', postFunctionsSha256: '0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344',
    preWholeSha256: 'b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c', postWholeSha256: '5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf', interfaceSha256: '8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef',
    defines: { MODE: 0 }, global: { symbol: 'MAX_TAPS', symbol_id: 8, value: 24 }, loop: { count: 3, trip_caps: [3, 3, 24], max_depth: 2, max_product: 24, entry_charge: 72 },
    bindingTypes: { strokeLength: 'float', balance: 'float', intensity: 'float' },
    bindingSignature: ['inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'strokeLength:float@4', 'balance:float@5', 'intensity:float@6', 'MAX_TAPS:const int@8'], outputSignature: 'fragColor:vec4@7',
    fetchBounds: { static_texture_sites_in_resolved_MODE_0: 2, dynamic_min_ui_domain: 29, dynamic_min_arbitrary_f32_uniforms: 21, dynamic_max: 119, note: 'main source 1 + two brush fields from 9 to 10 each + two smears from 5 to 49 each for strokeLength 0..100; arbitrary negative lengths can early-break both smears after their initial fetch' },
    cases: [
      { name: 'strokes-short-low-balance', size: [17, 13], tile: [0, 0], full: [17, 13], uniforms: { strokeLength: f(0), balance: f(20), intensity: f(0) }, coverage: ['MODE-0', 'short-smear-break', 'low-balance', 'two-3x3-fields'] },
      { name: 'strokes-long-high-balance-tiled', size: [17, 13], tile: [5, 3], full: [41, 29], uniforms: { strokeLength: f(100), balance: f(80), intensity: f(73) }, coverage: ['MODE-0', '24-trip-cap', 'high-balance', 'tiled-global-fields'] },
      { name: 'strokes-long-low-balance', size: [17, 13], tile: [0, 0], full: [17, 13], uniforms: { strokeLength: f(87.5), balance: f(8), intensity: f(31) }, coverage: ['MODE-0', 'long-smear', 'low-balance', 'field-selection'] },
    ],
    mutations: [
      { name: 'strokes-global-bound-24-to-8', contract: 'changes only MAX_TAPS from 24 to 8', from: 'var MAX_TAPS = 24;', to: 'var MAX_TAPS = 8;', diverge: ['strokes-long-high-balance-tiled', 'strokes-long-low-balance'], match: [] },
      { name: 'strokes-field-selection-forced-135', contract: 'forces the MODE-0 field selector to the 135-degree field', from: 'var side = smoothstep(b - 0.10000000149011612, b + 0.10000000149011612, lum(new $runtime.PooledFloat32Array([src[0], src[1], src[2]])));', to: 'var side = 0;', diverge: ['strokes-short-low-balance', 'strokes-long-low-balance'], match: [] },
    ],
  },
  {
    key: 'filter/vaseline:upsample', source: 'sources/filter/vaseline/upsample.glsl', rawBytes: 2524,
    rawSha256: '39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461', normalizedSha256: '1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93',
    factoryName: 'canonicalFactory170', factorySha256: '322ba53c3b001878f026c615998086ef7732277b5f2d2401064ea2497cb6113a',
    preFunctionsSha256: '9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374', postFunctionsSha256: '2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389',
    preWholeSha256: '5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d', postWholeSha256: '831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6', interfaceSha256: 'fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e',
    defines: {}, global: { symbol: 'TAP_COUNT', symbol_id: 8, value: 32 }, loop: { count: 1, trip_caps: [32], max_depth: 1, max_product: 32, entry_charge: 32 },
    bindingTypes: { renderScale: 'float', alpha: 'float' },
    bindingSignature: ['inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'fullResolution:vec2@4', 'renderScale:float@5', 'alpha:float@6', 'TAP_COUNT:const int@8'], outputSignature: 'fragColor:vec4@7',
    fetchBounds: { static_texture_sites: 2, dynamic_copy_path: 1, dynamic_normal_path: 33 },
    cases: [
      { name: 'vaseline-alpha-zero-copy', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { renderScale: f(1), alpha: f(0) }, coverage: ['alpha-zero-early-return', 'one-fetch', 'exact-input-copy'], exactCopy: true },
      { name: 'vaseline-mid-alpha-tiled', size: [11, 7], tile: [5, 3], full: [29, 19], uniforms: { renderScale: f(1.5), alpha: f(0.625) }, coverage: ['32-trip-loop', 'tiled-coordinate-conversion', 'fractional-renderScale', 'edge-mask'] },
      { name: 'vaseline-alpha-clamped-high', size: [9, 13], tile: [2, 4], full: [21, 31], uniforms: { renderScale: f(2), alpha: f(1.5) }, coverage: ['alpha-clamps-one', 'portrait', 'full-blend'] },
    ],
    mutations: [
      { name: 'vaseline-global-bound-32-to-8', contract: 'changes only TAP_COUNT from 32 to 8', from: 'var TAP_COUNT = 32;', to: 'var TAP_COUNT = 8;', diverge: ['vaseline-mid-alpha-tiled', 'vaseline-alpha-clamped-high'], match: ['vaseline-alpha-zero-copy'] },
      { name: 'vaseline-edge-mask-forced-zero', contract: 'forces the global edge mask to zero while preserving the blur', from: 'var edgeMask = chebyshev_mask(globalUV);', to: 'var edgeMask = 0;', diverge: ['vaseline-mid-alpha-tiled', 'vaseline-alpha-clamped-high'], match: ['vaseline-alpha-zero-copy'] },
    ],
  },
  {
    key: 'filter/wind:wind', source: 'sources/filter/wind/wind.glsl', rawBytes: 3520,
    rawSha256: '68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22', normalizedSha256: '665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4',
    factoryName: 'canonicalFactory177', factorySha256: '163a65997398acd140ec10572d9253914d1659fc240187c1eae5a9de354810dd',
    preFunctionsSha256: '214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d', postFunctionsSha256: '70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4',
    preWholeSha256: 'b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0', postWholeSha256: '6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0', interfaceSha256: '455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85',
    defines: { METHOD: 1 }, global: { symbol: 'MAX_STEPS', symbol_id: 8, value: 128 }, loop: { count: 1, trip_caps: [128], max_depth: 1, max_product: 128, entry_charge: 128 },
    bindingTypes: { direction: 'int', strength: 'float', threshold: 'float' },
    bindingSignature: ['inputTex:sampler2D@1/S1', 'resolution:vec2@2', 'tileOffset:vec2@3', 'direction:int@4', 'strength:float@5', 'threshold:float@6', 'MAX_STEPS:const int@8'], outputSignature: 'fragColor:vec4@7',
    fetchBounds: { static_texture_sites: 2, dynamic_copy_path: 1, dynamic_normal_min: 1, dynamic_normal_max: 129, note: 'positive strength with reach below one enters the normal path but breaks before the first candidate fetch' },
    cases: [
      { name: 'wind-strength-zero-copy', size: [11, 7], tile: [0, 0], full: [11, 7], uniforms: { direction: 0, strength: f(0), threshold: f(50) }, coverage: ['strength-zero-early-return', 'one-fetch', 'exact-input-copy'], exactCopy: true },
      { name: 'wind-tiny-positive-no-march', size: [11, 7], tile: [3, 2], full: [23, 17], uniforms: { direction: 0, strength: f(0.5), threshold: f(50) }, coverage: ['positive-strength-normal-path', 'reach-below-one', 'break-before-first-candidate', 'one-fetch', 'exact-output-copy'], exactCopy: true },
      { name: 'wind-left-medium-tiled', size: [11, 7], tile: [5, 3], full: [29, 19], uniforms: { direction: 0, strength: f(40), threshold: f(5) }, coverage: ['left-march', '51-trip-reach-cap', 'tiled-global-coordinate', 'low-threshold'] },
      { name: 'wind-right-full-strength', size: [13, 9], tile: [0, 0], full: [13, 9], uniforms: { direction: 1, strength: f(100), threshold: f(0) }, coverage: ['right-march', 'full-128-trip-loop', 'maximum-reach', 'zero-threshold'] },
    ],
    mutations: [
      { name: 'wind-global-bound-128-to-16', contract: 'changes only MAX_STEPS from 128 to 16', from: 'var MAX_STEPS = 128;', to: 'var MAX_STEPS = 16;', diverge: ['wind-left-medium-tiled', 'wind-right-full-strength'], match: ['wind-strength-zero-copy', 'wind-tiny-positive-no-march'] },
      { name: 'wind-direction-forced-right', contract: 'forces marchDir to positive one', from: 'var marchDir = (direction == 0) ? -1 : 1;', to: 'var marchDir = 1;', diverge: ['wind-left-medium-tiled'], match: ['wind-strength-zero-copy', 'wind-tiny-positive-no-march', 'wind-right-full-strength'] },
    ],
  },
])

if (sha256(fs.readFileSync(canonicalPath)) !== canonicalSha256) throw new Error('pinned canonical runtime drift')
const factories = new Map()
for (const program of programs) {
  const raw = fs.readFileSync(path.join(corpus, program.source))
  if (raw.byteLength !== program.rawBytes || sha256(raw) !== program.rawSha256) throw new Error(`${program.key}: pinned source drift`)
  const canonical = canonicalKernelFactories[program.key]
  const publicFactory = kernelFactories.get(program.key)
  if (canonical?.name !== program.factoryName || sha256(Buffer.from(canonical.toString())) !== program.factorySha256) throw new Error(`${program.key}: canonical factory drift`)
  if (publicFactory !== canonical || canonicalAdapterFactories[program.key] !== undefined) throw new Error(`${program.key}: public dispatch is not direct canonical identity`)
  factories.set(program.key, { canonical, text: canonical.toString() })
}

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

function render(program, factory, definition) {
  const [width, height] = definition.size
  const input = makeInput(width, height)
  const originalInput = new Float32Array(input.data)
  const kernel = bindCanonicalKernel(factory, {
    width, height, time: f(0.375), frame, deltaTime, seed: runtimeSeed,
    tileOffset: new Float32Array(definition.tile), fullResolution: new Float32Array(definition.full),
    uniforms: { ...program.defines, ...definition.uniforms }, textures: { inputTex: input },
  })
  const output = new Surface(width, height)
  runPass({ kernel, destination: output, time: f(0.375), seed: runtimeSeed })
  if (!sameBytes(input.data, originalInput)) throw new Error(`${definition.name}: input mutated`)
  return { input, output }
}

function probe(surface, x, y) {
  const offset = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(offset, offset + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}

function probes(surface) {
  const points = [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]]
  return points.map(([x, y]) => probe(surface, x, y))
}

function metrics(input, output) {
  let finite = 0, nonfinite = 0, changed = 0, alphaPreserved = 0
  for (let i = 0; i < output.data.length; i += 1) {
    if (Number.isFinite(output.data[i])) finite += 1; else nonfinite += 1
    if (f32Bits(output.data[i]) !== f32Bits(input.data[i])) changed += 1
  }
  for (let i = 3; i < output.data.length; i += 4) if (f32Bits(output.data[i]) === f32Bits(input.data[i])) alphaPreserved += 1
  return { pixels: output.width * output.height, finite_lanes: finite, nonfinite_lanes: nonfinite, changed_f32_lanes_from_same_input_position: changed, alpha_preserved_pixels: alphaPreserved }
}

function recordedUniforms(program, uniforms) {
  return Object.fromEntries(Object.entries(uniforms).map(([name, value]) => [name, scalarRecord(value, program.bindingTypes[name])]))
}

function diff(reference, mutated) {
  const rb = bytes(reference.data), mb = bytes(mutated.data), rr = reference.toRgba8(), mr = mutated.toRgba8()
  let byteDiff = 0, laneDiff = 0, rgbaDiff = 0, maxAbs = 0
  for (let i = 0; i < rb.length; i += 1) if (rb[i] !== mb[i]) byteDiff += 1
  for (let i = 0; i < reference.data.length; i += 1) if (f32Bits(reference.data[i]) !== f32Bits(mutated.data[i])) {
    laneDiff += 1
    if (Number.isFinite(reference.data[i]) && Number.isFinite(mutated.data[i])) maxAbs = Math.max(maxAbs, Math.abs(reference.data[i] - mutated.data[i]))
  }
  for (let i = 0; i < rr.length; i += 1) if (rr[i] !== mr[i]) rgbaDiff += 1
  return { same_f32_bytes: byteDiff === 0, same_rgba8_bytes: rgbaDiff === 0, different_f32_bytes: byteDiff, different_f32_lanes: laneDiff, different_rgba8_bytes: rgbaDiff, max_absolute_f32_difference: maxAbs, mutated_f32_sha256: sha256(mb), mutated_rgba8_sha256: sha256(bytes(mr)) }
}

function mutatedFactory(program, mutation) {
  const text = factories.get(program.key).text
  const count = countOccurrences(text, mutation.from)
  if (count !== 1) throw new Error(`${mutation.name}: replacement count ${count}`)
  return (0, eval)(`(${text.replace(mutation.from, mutation.to)})`)
}

function caseResult(program, definition, surfaces) {
  const factory = factories.get(program.key).canonical
  const first = render(program, factory, definition)
  const second = render(program, factory, definition)
  const rgba = first.output.toRgba8()
  if (!sameBytes(first.input.data, second.input.data) || !sameBytes(first.output.data, second.output.data) || !sameBytes(rgba, second.output.toRgba8())) throw new Error(`${definition.name}: repeat mismatch`)
  const summary = metrics(first.input, first.output)
  if (summary.nonfinite_lanes !== 0) throw new Error(`${definition.name}: nonfinite output`)
  if (definition.exactCopy && !sameBytes(first.input.data, first.output.data)) throw new Error(`${definition.name}: expected exact copy`)
  surfaces.set(definition.name, first.output)
  return {
    name: definition.name, key: program.key, dimensions: { width: definition.size[0], height: definition.size[1] },
    tileOffset: vec2Record(new Float32Array(definition.tile)), fullResolution: vec2Record(new Float32Array(definition.full)),
    uniforms: recordedUniforms(program, definition.uniforms), coverage: definition.coverage,
    input: { f32_sha256: sha256(bytes(first.input.data)), rgba8_sha256: sha256(bytes(first.input.toRgba8())), probes: probes(first.input) },
    output: { f32_sha256: sha256(bytes(first.output.data)), rgba8_sha256: sha256(bytes(rgba)), probes: probes(first.output), metrics: summary },
    repeat_identity: { input_f32_bytes: true, output_f32_bytes: true, output_rgba8_bytes: true }, input_immutable: true,
  }
}

function mutationResult(program, mutation, surfaces) {
  const factory = mutatedFactory(program, mutation)
  const results = program.cases.map(definition => ({ case: definition.name, ...diff(surfaces.get(definition.name), render(program, factory, definition).output) }))
  for (const name of mutation.diverge) if (results.find(item => item.case === name)?.same_f32_bytes !== false) throw new Error(`${mutation.name}: missing divergence ${name}`)
  for (const name of mutation.match) {
    const result = results.find(item => item.case === name)
    if (!result?.same_f32_bytes || !result.same_rgba8_bytes) throw new Error(`${mutation.name}: missing identity ${name}`)
  }
  return { name: mutation.name, key: program.key, contract: mutation.contract, replacement: { from: mutation.from, to: mutation.to, exact_replacement_count: 1 }, required_divergence_cases: mutation.diverge, required_identity_cases: mutation.match, case_results: results }
}

function buildData() {
  const cases = [], mutations = []
  for (const program of programs) {
    const surfaces = new Map()
    cases.push(...program.cases.map(definition => caseResult(program, definition, surfaces)))
    mutations.push(...program.mutations.map(mutation => mutationResult(program, mutation, surfaces)))
  }
  return {
    schema: 'noisemaker-for-cpp.task23-source-global-literal-int.public-canonical-oracles.v1', corpus_revision: corpusRevision,
    provenance: { node: process.version, api: 'public kernelFactories identity with canonicalKernelFactories + bindCanonicalKernel + runPass + Surface', canonical_kernels_path: 'src/effects/generated/canonical-kernels.js', canonical_kernels_sha256: canonicalSha256, reference_only: 'all expected output comes from each pinned public factory after proving it is the identical canonical function object and has no adapter entry' },
    contract: { capability: 'source-global-literal-int-v1', counted_bound_kind: 'source-global-const-literal', numeric_literal_contract: 'glsl-f32', compatibility_transforms: 'none', projected_counts: { typed: 122, public: 124, unported: 88, corpus: 212 }, excluded_adapter_key: 'filter/reindex:nmReindexStats' },
    programs: programs.map(program => ({ key: program.key, source: program.source, raw_source_bytes: program.rawBytes, raw_source_sha256: program.rawSha256, normalized_source_sha256: program.normalizedSha256, defines: program.defines, canonical_factory_name: program.factoryName, canonical_factory_to_string_sha256: program.factorySha256, public_factory_is_canonical_identity: true, adapter_entry_absent: true, pre_function_tuple_sha256: program.preFunctionsSha256, post_function_tuple_sha256: program.postFunctionsSha256, pre_whole_program_sha256: program.preWholeSha256, post_whole_program_sha256: program.postWholeSha256, interface_sha256_pre_and_post: program.interfaceSha256, source_global_literal_int: program.global, counted_loop_proof: program.loop, binding_signature: program.bindingSignature, output_signature: program.outputSignature, resource_fetch_bounds: program.fetchBounds })),
    fixture: { input: 'top-down Float32Array: R=((17*x+31*y+13)%101)/100; G=((7*x+19*y+23)%97)/96; B=((29*x+11*y+5)%89)/88; A=(((5*x+7*y+3)%23)-5)/12', fragment_origin: 'bottom-left, runPass fragCoord=(x+0.5,height-y-0.5)', context: { frame, deltaTime: scalarRecord(deltaTime), runtime_seed: scalarRecord(runtimeSeed) }, verification: 'fresh double render; exact input/output F32 and output RGBA8 repeat; input immutable; every output lane finite; full hashes and probes' },
    cases, mutation_sensitivity: { mutation_count: mutations.length, purpose: 'each key has a literal-bound mutation and an independent semantic/control mutation; required identity cases cover early exits or inactive terms where available', mutations },
  }
}

function buildReport(data) {
  const lines = ['# Task 23 six-key public-canonical oracle report', '', `Corpus revision: \`${data.corpus_revision}\`  `, `Cases: **${data.cases.length}**  `, `Mutations: **${data.mutation_sensitivity.mutation_count}**`, '', 'Every public factory was runtime-proved identical to its pinned canonical factory; no selected key has an adapter entry. All cases repeat byte-identically with immutable input and finite output.', '', '## Programs', '', '| Key | Factory | Global bound | Loop charge | Pre -> post function hash | Interface hash |', '| --- | --- | --- | ---: | --- | --- |']
  for (const p of data.programs) lines.push(`| \`${p.key}\` | \`${p.canonical_factory_name}\` | \`${p.source_global_literal_int.symbol}@${p.source_global_literal_int.symbol_id}=${p.source_global_literal_int.value}\` | ${p.counted_loop_proof.entry_charge} | \`${p.pre_function_tuple_sha256}\` -> \`${p.post_function_tuple_sha256}\` | \`${p.interface_sha256_pre_and_post}\` |`)
  lines.push('', '## Cases', '', '| Key / case | Size | Output F32 SHA-256 | RGBA8 SHA-256 | Changed lanes |', '| --- | --- | --- | --- | ---: |')
  for (const c of data.cases) lines.push(`| \`${c.key}\` / ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | \`${c.output.f32_sha256}\` | \`${c.output.rgba8_sha256}\` | ${c.output.metrics.changed_f32_lanes_from_same_input_position} |`)
  lines.push('', '## Mutation sensitivity', '', '| Key / mutation | Required divergent cases | Maximum changed F32 lanes | Maximum changed RGBA8 bytes |', '| --- | --- | ---: | ---: |')
  for (const m of data.mutation_sensitivity.mutations) lines.push(`| \`${m.key}\` / ${m.name} | ${m.required_divergence_cases.join(', ')} | ${Math.max(...m.case_results.map(x => x.different_f32_lanes))} | ${Math.max(...m.case_results.map(x => x.different_rgba8_bytes))} |`)
  lines.push('', '## Held boundary', '', '`filter/reindex:nmReindexStats` is structurally adjacent but uses the public `reindexStatsFactory` eager-F32 adapter. It is not represented by these direct-canonical outputs and remains excluded.', '')
  return `${lines.join('\n')}\n`
}

const data = buildData()
const json = `${JSON.stringify(data, null, 2)}\n`
const report = buildReport(data)
if (process.argv.length === 2) process.stdout.write(json)
else if (process.argv.length === 3 && process.argv[2] === '--write') {
  fs.writeFileSync(jsonPath, json, 'utf8'); fs.writeFileSync(reportPath, report, 'utf8')
  process.stdout.write(`wrote ${path.basename(jsonPath)} and ${path.basename(reportPath)}\n`)
} else if (process.argv.length === 3 && process.argv[2] === '--check') {
  if (fs.readFileSync(jsonPath, 'utf8') !== json) throw new Error(`${jsonPath} drift`)
  if (fs.readFileSync(reportPath, 'utf8') !== report) throw new Error(`${reportPath} drift`)
  process.stdout.write(`ok ${path.basename(jsonPath)} and ${path.basename(reportPath)}\n`)
} else throw new Error('usage: node task-23-oracle-generator.mjs [--write|--check]')
