#!/usr/bin/env node
// Frozen-authority dither oracle. This package is prepared-only: it does not
// import, modify, or regenerate the shared C++ typed slice.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../../..')
const out = path.join(here, 'dither-oracles.json')
const report = path.join(here, 'dither-oracle-report.md')
const key = 'filter/dither:dither'
const baselineNames = ['bayer2-input', 'bayer8-tiled', 'dot-input', 'line-input', 'crosshatch-input', 'noise-input', 'fallback-type', 'error-diffusion-input', 'error-diffusion-input-tiled']
const adversarialNames = ['error-diffusion-negative-tile', 'levels-2-boundary', 'levels-16-boundary']
const caseNames = [...baselineNames, ...adversarialNames]
const mutationNames = ['fallback-default', 'quantize-levels', 'error-diffusion-route']
const corpusSourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl'
const corpusSourcePath = path.join(root, corpusSourceRelative)
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const corpusSourceBytes = fs.readFileSync(corpusSourcePath)
const corpusSourceSha256 = sha(corpusSourceBytes)
const expectedUpstreamRevision = '117a236679d1db3ab8f0e278230ece277b57564c'
const expectedCanonicalSource = { relative_path: 'src/effects/generated/canonical-kernels.js', bytes: 1713290, sha256: '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe' }
const expectedFactory = { name: 'canonicalFactory48', text_bytes: 22898, text_sha256: '28a1c56b63d345eaa3c3e803b19397a546730020d456ed2c29eb39aec3a5c820', public_factory_name: 'canonicalFactory48', public_factory_is_canonical_identity: true }
const expectedClosure = [
  ['src/csl/glsl-kernel.js', 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
  ['src/csl/glsl-runtime.js', 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
  ['src/csl/runtime.js', 'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee'],
  ['src/effects/adapters/bit-effects.js', '5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7'],
  ['src/effects/adapters/crt.js', 'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc'],
  ['src/effects/adapters/f32-color.js', 'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046'],
  ['src/effects/adapters/fractal.js', '0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29'],
  ['src/effects/adapters/index.js', '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267'],
  ['src/effects/adapters/julia.js', '0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5'],
  ['src/effects/adapters/median.js', 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583'],
  ['src/effects/adapters/palette.js', '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'],
  ['src/effects/adapters/snow.js', '202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366'],
  ['src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
  ['src/effects/definition.js', 'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02'],
  ['src/effects/generated/canonical-adapter-data.js', 'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab'],
  ['src/effects/generated/canonical-kernels.js', '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe'],
  ['src/effects/generated/kernels.js', 'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01'],
  ['src/effects/generated/upstream-snapshot.js', 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090'],
  ['src/effects/registry.js', '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'],
  ['src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
  ['src/runtime/sampler.js', '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328'],
  ['src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
].map(([relative_path, sha256]) => ({ relative_path, sha256 }))
const expectedClosureSha256 = 'b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5'
const expectedMutationIdentities = {
  'fallback-default': { anchor_sha256: '8e35a9b15829e194b90777d8f38e5709ec2e1f8cfa875d4294496fade9f67683', replacement_sha256: '8fb42fd196d8a5e5bff6ba3a7a1dd24a87fe4dfb2b0f07a75146dc5bdcd1251b', mutated_factory_sha256: '85c2335ba2395a5d80f05fff460de3ddf5779b39524a927ee506618c36e0f611' },
  'quantize-levels': { anchor_sha256: '4af10b05bcf97c256bedc908d8fc491d9a7d53b3bd16508493a436d742f602ac', replacement_sha256: 'aa8311a86e4e743a9c84375b905a6c66581039145887910832a63625c2ef4b34', mutated_factory_sha256: 'c48b59a286a1178abe723287b9ea9869600425609971827b37bb4b2d5b6ea007' },
  'error-diffusion-route': { anchor_sha256: '4d67d8c234a20ad7a01c31093fd192a8a78821d5414d115bbc1dfbb209586e3f', replacement_sha256: 'a379b9b2de4ff3d9bbc89b6f64472ac79af6d39b89ae7604f2cf529752d32788', mutated_factory_sha256: '3937d5b5265b810304261dae07e087890cec8fcf755da6a17d82146aa0432be3' },
}
const hex = value => `0x${(value >>> 0).toString(16).padStart(8, '0')}`
const words = surface => new Uint32Array(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength / 4)
const beneath = (a, b) => b === a || b.startsWith(`${a}${path.sep}`)
function compare(a, b) {
  if (a.width !== b.width || a.height !== b.height) return { exact: false, dimensions_match: false, lane_count_match: false, mismatched_lanes: 0, mismatched_bytes: 0, first_mismatch: null, first_rgba8_mismatch: null }
  const aw = words(a), bw = words(b); let lanes = Math.abs(aw.length - bw.length); let first = null
  for (let i = 0; i < Math.min(aw.length, bw.length); i++) if (aw[i] !== bw[i]) { lanes++; if (!first) first = { lane_index: i, reference: hex(aw[i]), candidate: hex(bw[i]) } }
  const ar = new Uint8Array(a.toRgba8()), br = new Uint8Array(b.toRgba8()); let bytes = Math.abs(ar.length - br.length); let firstByte = null
  for (let i = 0; i < Math.min(ar.length, br.length); i++) if (ar[i] !== br[i]) { bytes++; if (!firstByte) firstByte = { byte_index: i, reference: ar[i], candidate: br[i] } }
  return { exact: lanes === 0 && bytes === 0 && aw.length === bw.length && ar.length === br.length, dimensions_match: true, lane_count_match: aw.length === bw.length, mismatched_lanes: lanes, mismatched_bytes: bytes, first_mismatch: first, first_rgba8_mismatch: firstByte }
}
function fake(w, h, f32, rgba) { return { width: w, height: h, get data() { return new Float32Array(new Uint32Array(f32).buffer) }, toRgba8: () => Uint8Array.from(rgba) } }
function comparerSelfTests() {
  const equal = compare(fake(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]), fake(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]))
  const dimensions = compare({ width: 1, height: 1, get data() { throw new Error('accessed before dimensions') } }, { width: 2, height: 1, get data() { throw new Error('accessed before dimensions') } })
  const short = compare(fake(1, 1, [0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]))
  const rgba = compare(fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0, 0, 0, 0], [1, 0, 0, 0]))
  const signedZero = compare(fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0x80000000, 0, 0, 0], [0, 0, 0, 0]))
  return { good_equal: equal.exact, dimensions_mismatch: !dimensions.dimensions_match, short_lane_count: !short.lane_count_match, rgba8_mismatch: rgba.mismatched_bytes > 0, signed_zero: signedZero.mismatched_lanes > 0 }
}
function input(def) {
  const data = new Float32Array(def.width * def.height * 4)
  for (let i = 0; i < data.length; i += 4) { const p = i / 4; const x = p % def.width; const y = Math.floor(p / def.width); data[i] = Math.fround(((x * 17 + y * 11 + def.phase) % 23) / 22); data[i + 1] = Math.fround(((x * 7 + y * 19 + def.phase * 2) % 29) / 28); data[i + 2] = Math.fround(((x * 13 + y * 5 + def.phase * 3) % 31) / 30); data[i + 3] = Math.fround(.15 + ((x + y + def.phase) % 8) / 10) }
  return data
}
function surface(def, Surface) { return new Surface(def.width, def.height, input(def)) }
function render(factory, def, createBindings, bind, runPass, Surface) {
  const source = surface(def, Surface); const before = new Uint32Array(words(source)); const destination = new Surface(def.width, def.height)
  const bindings = createBindings({ width: def.width, height: def.height, time: Math.fround(def.time), uniforms: { ditherType: def.ditherType, threshold: Math.fround(def.threshold), matrixScale: Math.fround(def.matrixScale), renderScale: Math.fround(def.renderScale), palette: def.palette, levels: def.levels, time: Math.fround(def.time), mixAmount: Math.fround(def.mixAmount) }, textures: { inputTex: source }, tileOffset: new Float32Array(def.tileOffset.map(Math.fround)), fullResolution: new Float32Array(def.fullResolution.map(Math.fround)) })
  const kernel = bind(factory, bindings); runPass({ kernel, destination, time: def.time, seed: def.phase }); const after = words(source)
  if (before.some((value, index) => value !== after[index])) throw new Error(`${def.name}: input mutated`)
  return { output: destination, input: source }
}
function surfaceRecord(value) { const bytes = new Uint8Array(value.data.buffer, value.data.byteOffset, value.data.byteLength); if (Array.from(value.data).some(lane => !Number.isFinite(lane))) throw new Error('non-finite Float32 lane'); const rgba = new Uint8Array(value.toRgba8()); return { f32_words_le: Array.from(words(value), hex), f32_sha256: sha(Buffer.from(bytes)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha(Buffer.from(rgba)) } }
async function mutatedFactory(text, mutation) { if (text.split(mutation.anchor).length - 1 !== 1) throw new Error(`mutation anchor cardinality: ${mutation.name}`); const encoded = Buffer.from(`export const factory = ${text.replace(mutation.anchor, mutation.replacement)}\n`).toString('base64'); return (await import(`data:text/javascript;base64,${encoded}#${sha(text + mutation.name)}`)).factory }
function closure(cpuRoot) { const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']; const imports = /\bfrom\s*["']([^"'\n]+)["']/g; const stack = entries.map(e => path.join(cpuRoot, e)); const seen = new Map(); while (stack.length) { const file = fs.realpathSync(stack.pop()); if (!beneath(cpuRoot, file)) throw new Error('closure escapes authority'); if (seen.has(file)) continue; const text = fs.readFileSync(file, 'utf8'); seen.set(file, sha(Buffer.from(text))); imports.lastIndex = 0; let m; while ((m = imports.exec(text))) if (m[1].startsWith('./') || m[1].startsWith('../')) { const next = fs.realpathSync(path.resolve(path.dirname(file), m[1])); if (!beneath(cpuRoot, next)) throw new Error('closure escapes authority'); stack.push(next) } } return [...seen.entries()].map(([file, digest]) => ({ relative_path: path.relative(cpuRoot, file), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path)) }
function truncDiv(value, divisor) { return value < 0 ? Math.ceil(value / divisor) : Math.floor(value / divisor) }
function signedTrace(def) {
  const cellSize = Math.fround(Math.fround(def.matrixScale) * Math.fround(def.renderScale))
  const points = [0, 1, def.width - 1].map(x => {
    const global = [Math.fround(x + 0.5 + def.tileOffset[0]), Math.fround(0.5 + def.tileOffset[1])]
    const cell = [Math.floor(global[0] / cellSize), Math.floor(global[1] / cellSize)]
    return { fragment: [x, 0], global, cell, block_origin: [truncDiv(cell[0], 4) * 4, truncDiv(cell[1], 4) * 4] }
  })
  const target = points[0]
  const loopOffset = [-4, -4]
  const loopCell = [target.block_origin[0] + loopOffset[0], target.block_origin[1] + loopOffset[1]]
  const loopGlobal = [Math.fround((loopCell[0] + 0.5) * cellSize), Math.fround((loopCell[1] + 0.5) * cellSize)]
  const rawLocal = [Math.floor(loopGlobal[0]) - def.tileOffset[0], Math.floor(loopGlobal[1]) - def.tileOffset[1]]
  const clamped = [Math.max(0, Math.min(def.width - 1, rawLocal[0])), Math.max(0, Math.min(def.height - 1, rawLocal[1]))]
  const lx = target.cell[0] - target.block_origin[0]
  const ly = target.cell[1] - target.block_origin[1]
  const lastRow = loopOffset[1] === ly
  const visited = loopOffset[1] >= -11 && loopOffset[1] <= ly && loopOffset[1] >= -4 && loopOffset[0] >= -4 && !(lastRow && loopOffset[0] >= lx)
  if (!visited || !rawLocal.some((value, index) => value !== clamped[index])) throw new Error('signed trace clamp witness is not a visited raster point')
  return {
    method: 'source-derived-error-diffusion-trace-v1',
    source: { relative_path: corpusSourceRelative, raw_sha256: corpusSourceSha256, block_span: '508-566', fetch_span: '500-506' },
    signed_division: 'truncate_toward_zero', fs_block: 4, cell_size: cellSize,
    negative_global_coordinate: points.some(point => point.global.some(value => value < 0)),
    negative_block_origin: points.some(point => point.block_origin.some(value => value < 0)),
    points,
    clamp_witness: { fragment: target.fragment, block_origin: target.block_origin, loop_offset: loopOffset, cell: loopCell, global: loopGlobal, raw_local: rawLocal, clamped_local: clamped, visited, clamped: rawLocal[0] !== clamped[0] || rawLocal[1] !== clamped[1] },
  }
}
const comparerPolicy = { f32_words_exact: true, rgba8_bytes_exact: true, dimensions_before_data: true, signed_zero_exact: true, input_bits_exact: true, public_direct_exact: true, repeat_identity_exact: true }

const args = process.argv.slice(2); const mode = args.find(token => ['--write', '--check', '--self-test'].includes(token)); if (!mode || args.filter(token => ['--write', '--check', '--self-test'].includes(token)).length !== 1) throw new Error('choose exactly one mode')
const cpuIndex = args.indexOf('--cpu-root'); if (cpuIndex < 0) throw new Error('--cpu-root <immutable snapshot> is required'); const cpuArg = args[cpuIndex + 1]; if (!cpuArg) throw new Error('--cpu-root <immutable snapshot> is required'); const cpuStat = fs.lstatSync(cpuArg); if (cpuStat.isSymbolicLink()) throw new Error('--cpu-root must not be a symlink'); const cpuRoot = fs.realpathSync(cpuArg); if (beneath(root, cpuRoot)) throw new Error('--cpu-root must be an external immutable authority, not the work checkout'); const liveArg = process.env.NOISEMAKER_FOR_CPU; if (liveArg) { const liveStat = fs.lstatSync(liveArg); if (liveStat.isSymbolicLink()) throw new Error('NOISEMAKER_FOR_CPU must not be a symlink'); const liveRoot = fs.realpathSync(liveArg); if (liveRoot === cpuRoot || beneath(liveRoot, cpuRoot) || beneath(cpuRoot, liveRoot)) throw new Error('live checkout cannot be authority') }
const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{ canonicalKernelFactories, kernelFactories }, { createCanonicalBindings }, { bindGlslKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/csl/glsl-runtime.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js')])
const canonical = canonicalKernelFactories[key]; const publicFactory = kernelFactories.get(key); if (typeof canonical !== 'function' || typeof publicFactory !== 'function') throw new Error('dither factory missing')
const canonicalText = Function.prototype.toString.call(canonical); const sourcePath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js'); const sourceBytes = fs.readFileSync(sourcePath)
if (UPSTREAM_REVISION !== expectedUpstreamRevision || sourcePath !== path.join(cpuRoot, expectedCanonicalSource.relative_path) || sourceBytes.length !== expectedCanonicalSource.bytes || sha(sourceBytes) !== expectedCanonicalSource.sha256 || canonical.name !== expectedFactory.name || Buffer.byteLength(canonicalText) !== expectedFactory.text_bytes || sha(canonicalText) !== expectedFactory.text_sha256 || publicFactory.name !== expectedFactory.public_factory_name || publicFactory !== canonical) throw new Error('pinned CPU authority identity mismatch')
const closureEntries = closure(cpuRoot); if (JSON.stringify(closureEntries) !== JSON.stringify(expectedClosure) || sha(Buffer.from(JSON.stringify(closureEntries))) !== expectedClosureSha256) throw new Error('pinned CPU authority closure mismatch')
const cases = [
  { name: 'bayer2-input', width: 4, height: 3, ditherType: 0, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 4, mixAmount: 1, phase: 1, time: 0, tileOffset: [0, 0], fullResolution: [4, 3] },
  { name: 'bayer8-tiled', width: 7, height: 5, ditherType: 2, threshold: .13, matrixScale: 2, renderScale: 1, palette: 0, levels: 5, mixAmount: .85, phase: 2, time: .2, tileOffset: [3, 2], fullResolution: [24, 20] },
  { name: 'dot-input', width: 6, height: 4, ditherType: 3, threshold: -.2, matrixScale: 2, renderScale: 1.25, palette: 0, levels: 4, mixAmount: 1, phase: 3, time: .4, tileOffset: [2, 1], fullResolution: [18, 14] },
  { name: 'line-input', width: 5, height: 6, ditherType: 4, threshold: .2, matrixScale: 3, renderScale: .75, palette: 0, levels: 4, mixAmount: .6, phase: 4, time: .75, tileOffset: [4, 3], fullResolution: [20, 24] },
  { name: 'crosshatch-input', width: 6, height: 5, ditherType: 5, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 4, mixAmount: 1, phase: 5, time: .1, tileOffset: [1, 4], fullResolution: [12, 10] },
  { name: 'noise-input', width: 7, height: 4, ditherType: 6, threshold: -.1, matrixScale: 2, renderScale: 1, palette: 0, levels: 4, mixAmount: .9, phase: 6, time: 1.1, tileOffset: [5, 2], fullResolution: [28, 16] },
  { name: 'fallback-type', width: 3, height: 3, ditherType: 99, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 4, mixAmount: 1, phase: 9, time: 0, tileOffset: [0, 0], fullResolution: [3, 3] },
  { name: 'error-diffusion-input', width: 5, height: 5, ditherType: 7, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 4, mixAmount: 1, phase: 7, time: .33, tileOffset: [0, 0], fullResolution: [5, 5] },
  { name: 'error-diffusion-input-tiled', width: 6, height: 4, ditherType: 7, threshold: .1, matrixScale: 2, renderScale: 1, palette: 0, levels: 4, mixAmount: .8, phase: 8, time: -.2, tileOffset: [2, 1], fullResolution: [18, 12] },
  { name: 'error-diffusion-negative-tile', width: 6, height: 4, ditherType: 7, threshold: .1, matrixScale: 2, renderScale: 1, palette: 0, levels: 4, mixAmount: .8, phase: 10, time: -.2, tileOffset: [-9, 2], fullResolution: [18, 12] },
  { name: 'levels-2-boundary', width: 4, height: 3, ditherType: 0, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 2, mixAmount: 1, phase: 10, time: 0, tileOffset: [0, 0], fullResolution: [4, 3] },
  { name: 'levels-16-boundary', width: 4, height: 3, ditherType: 0, threshold: 0, matrixScale: 1, renderScale: 1, palette: 0, levels: 16, mixAmount: 1, phase: 11, time: 0, tileOffset: [0, 0], fullResolution: [4, 3] },
]
if (cases.length !== 12 || cases.some((item, index) => item.name !== caseNames[index]) || cases.some(item => item.palette !== 0)) throw new Error('exact twelve-case palette=0 matrix mismatch')
cases.find(item => item.name === 'error-diffusion-negative-tile').signed_trace = signedTrace(cases.find(item => item.name === 'error-diffusion-negative-tile'))
const comparer = comparerSelfTests(); if (!Object.values(comparer).every(Boolean)) throw new Error('strict comparer self-tests failed')
const renderCases = []; for (const def of cases) { const direct = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const pub = render(publicFactory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const parity = compare(direct.output, pub.output); if (!parity.exact) throw new Error(`${def.name}: public/direct mismatch ${JSON.stringify(parity)}`); const repeat = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); renderCases.push({ ...def, input: surfaceRecord(direct.input), expected: surfaceRecord(direct.output), public_expected: surfaceRecord(pub.output), repeat: { exact: compare(direct.output, repeat.output).exact, output_object_distinct: direct.output !== repeat.output, output_data_distinct: direct.output.data !== repeat.output.data }, input_immutable_exact_bits: true, public_direct_exact: parity.exact }) }
const mutations = [
  { name: 'fallback-default', anchor: 'return 0.5;\n  };\n  function quantizeWithDither', replacement: 'return 0.25;\n  };\n  function quantizeWithDither', witnesses: ['fallback-type'] },
  { name: 'quantize-levels', anchor: 'return floor(new $runtime.PooledFloat32Array([dithered[0] * levels, dithered[1] * levels, dithered[2] * levels])).map(function (_) {return _ / (levels - 1);});', replacement: 'return floor(new $runtime.PooledFloat32Array([dithered[0] * levels, dithered[1] * levels, dithered[2] * levels])).map(function (_) {return _ / levels;});', witnesses: ['bayer2-input'] },
  { name: 'error-diffusion-route', anchor: 'if (ditherType == DITHER_ERROR_DIFFUSION)', replacement: 'if (ditherType == DITHER_BAYER_2X2)', witnesses: ['error-diffusion-input', 'error-diffusion-input-tiled'] },
]
const mutationLedger = []; for (const mutation of mutations) { const factory = await mutatedFactory(canonicalText, mutation); const mutatedFactorySha256 = sha(Function.prototype.toString.call(factory)); const anchorSha256 = sha(mutation.anchor); const replacementSha256 = sha(mutation.replacement); const expectedIdentity = expectedMutationIdentities[mutation.name]; if (!expectedIdentity || anchorSha256 !== expectedIdentity.anchor_sha256 || replacementSha256 !== expectedIdentity.replacement_sha256 || mutatedFactorySha256 !== expectedIdentity.mutated_factory_sha256) throw new Error(`pinned mutation identity mismatch: ${mutation.name}`); const results = mutation.witnesses.map(name => { const def = cases.find(item => item.name === name); const reference = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface).output; const candidate = render(factory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface).output; const result = compare(reference, candidate); if (result.exact || result.mismatched_lanes === 0 || result.mismatched_bytes === 0) throw new Error(`${mutation.name}/${name}: non-witness`); return { case: name, mismatched_lanes: result.mismatched_lanes, mismatched_bytes: result.mismatched_bytes, first_mismatch: result.first_mismatch, first_rgba8_mismatch: result.first_rgba8_mismatch } }); mutationLedger.push({ name: mutation.name, source_anchor: mutation.anchor, replacement: mutation.replacement, anchor_sha256: anchorSha256, replacement_sha256: replacementSha256, mutated_factory_sha256: mutatedFactorySha256, required_witnesses: mutation.witnesses, required_witness_results: results, independent: true }) }
if (mutationLedger.length !== 3 || mutationLedger.some((item, index) => item.name !== mutationNames[index])) throw new Error('exact mutation matrix mismatch')
function rgbLaneIndices(record, word) { return record.f32_words_le.flatMap((value, index) => index % 4 !== 3 && value === word ? [index] : []) }
for (const entry of renderCases.filter(item => item.name === 'levels-2-boundary' || item.name === 'levels-16-boundary')) {
  const zero = rgbLaneIndices(entry.expected, '0x00000000')
  const one = rgbLaneIndices(entry.expected, '0x3f800000')
  if ((entry.name === 'levels-2-boundary' && (JSON.stringify(zero) !== JSON.stringify([0, 1, 4, 6, 13, 14, 17, 18, 21, 22, 28, 30, 32, 34, 36, 37, 41]) || JSON.stringify(one) !== JSON.stringify([2, 5, 8, 10, 12, 20, 24, 25, 38, 40, 44, 45, 46]))) || (entry.name === 'levels-16-boundary' && (JSON.stringify(zero) !== JSON.stringify([2, 5, 33]) || JSON.stringify(one) !== JSON.stringify([8, 25])))) throw new Error(`level endpoint evidence mismatch: ${entry.name}`)
  entry.level_evidence = { levels: entry.levels, rgb_endpoint_lanes: { zero, one }, highest_level_word: '0x3f800000', highest_level_rgb_lanes: one }
}
function blockerResult(factory, def) { try { render(factory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); return { throws: false, message: null } } catch (error) { return { throws: true, message: String(error?.message || error) } } }
const blockerBase = { route: 'palette != PALETTE_INPUT', error: 'ditherWithPalette(...).reduce is not a function', source_anchor: 'ditherWithPalette(...).reduce((res,el,i)=>(res[i] = el, res), result)', reproducible: true }
const blockerDef = { ...cases[0], name: 'palette-blocker', palette: 2 }
const negativeAuthority = { ...blockerBase, case_name: blockerDef.name, palette: blockerDef.palette, direct: blockerResult(canonical, blockerDef), public: blockerResult(publicFactory, blockerDef) }
if (!negativeAuthority.direct.throws || !negativeAuthority.public.throws || negativeAuthority.direct.message !== blockerBase.error || negativeAuthority.public.message !== blockerBase.error) throw new Error('non-input palette blocker contract drift')
const closureSha256 = expectedClosureSha256
const document = { schema: 'noisemaker-for-cpp.dither.pixel-parity.v1', program_key: key, provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source: { relative_path: 'src/effects/generated/canonical-kernels.js', bytes: sourceBytes.length, sha256: sha(sourceBytes) }, factory: { name: canonical.name, text_bytes: Buffer.byteLength(canonicalText), text_sha256: sha(canonicalText), public_factory_name: publicFactory.name, public_factory_is_canonical_identity: publicFactory === canonical }, corpus_source: { relative_path: corpusSourceRelative, raw_bytes: corpusSourceBytes.length, raw_sha256: corpusSourceSha256 }, cpu_snapshot: { import_closure: closureEntries, closure_sha256: closureSha256, immutable_snapshot: true, live_checkout_rejected: true, realpath_containment_checked: true, symlink_escape_rejected: true } }, runtime_binding_abi: { inputTex: 'sampler2D', tileOffset: 'Vec2', fullResolution: 'Vec2', ditherType: 'int32', threshold: 'float', matrixScale: 'float', renderScale: 'float', palette: 'int32', levels: 'int32', time: 'float', mixAmount: 'float' }, render_cases: renderCases, comparer_policy: comparerPolicy, comparer_self_tests: comparer, mutation_ledger: mutationLedger, claim_boundaries: { typed_slice_landing: false, shared_emitter_modified: false, pixel_parity_authority: 'canonicalFactory48 and ditherFactory' }, upstream_runtime_blockers: [negativeAuthority], negative_authority: negativeAuthority }
const json = Buffer.from(`${JSON.stringify(document, null, 2)}\n`); const md = Buffer.from(`# Dither pixel-parity oracle\n\nFrozen Node ${process.version} authority for filter/dither:dither. The exact twelve cases are the nine baseline records (${baselineNames.join(', ')}) followed by the three adversarial controls (${adversarialNames.join(', ')}). All positive cases use palette=0 and carry exact Float32 words, RGBA8 bytes, repeat storage, input immutability, public/direct parity, comparer policy/self-tests, and the three mutation witnesses. The negative-tile case carries a source-bound signed global/cell/block-origin/clamp trace derived from the pinned corpus source. The non-input palette authority blocker is independently executed for canonical and public factories and must throw ditherWithPalette(...).reduce is not a function. Typed-slice integration remains prepared-only.\n`)
function sidecar(file, bytes) { fs.writeFileSync(`${file}.sha256`, `${sha(bytes)}  ${path.basename(file)}\n`) }
function sidecarText(file, bytes) { return `${sha(bytes)}  ${path.basename(file)}\n` }
function checkSidecar(file, bytes) { const sidecarPath = `${file}.sha256`; if (!fs.existsSync(sidecarPath) || fs.readFileSync(sidecarPath, 'utf8') !== sidecarText(file, bytes)) throw new Error(`${path.basename(file)} sidecar drift`) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(out, json); sidecar(out, json); fs.writeFileSync(report, md); sidecar(report, md); console.log(`${renderCases.length} cases, ${mutationLedger.length} mutations written`) } else { if (!fs.existsSync(out) || fs.readFileSync(out, 'utf8') !== json.toString()) throw new Error('dither oracle drift'); if (!fs.existsSync(report) || fs.readFileSync(report, 'utf8') !== md.toString()) throw new Error('dither report drift'); checkSidecar(out, json); checkSidecar(report, md); if (mode === '--self-test') console.log('strict comparer self-tests, twelve cases, signed trace, portable closure, blocker, public/direct parity, and mutation witnesses verified'); else console.log('dither oracle check passed') }
