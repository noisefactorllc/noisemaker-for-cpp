#!/usr/bin/env node
// Authenticated exact-pixel oracle for synth/newton:newton.
// Only the public canonical factory from the caller-supplied immutable CPU
// snapshot executes.  C++ output is never an input to this package.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const generatorPath = fileURLToPath(import.meta.url)
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'newton-oracles.json')
const reportPath = path.join(here, 'newton-oracle-report.md')
const programKey = 'synth/newton:newton'
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/newton/newton.glsl'
const sourceSha256 = '603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac'
const factoryName = 'canonicalFactory264'
const factoryTextSha256 = '7e4e95cfd6afa9f89e24920dbb06cd3af6f90f0c83f4329e302f701b78bba7af'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevision = '117a236679d1db3ab8f0e278230ece277b57564c'
const expectedClosure = Object.freeze([
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
])
const bindingNames = ['resolution', 'tileOffset', 'fullResolution', 'time', 'degree', 'relaxation', 'iterations', 'tolerance', 'poi', 'centerHiX', 'centerHiY', 'centerLoX', 'centerLoY', 'zoomSpeed', 'zoomDepth', 'degreeSpeed', 'degreeRange', 'relaxSpeed', 'relaxRange', 'rotation', 'outputMode', 'invert']
const bindingAbi = Object.fromEntries(bindingNames.map(name => [name, name === 'resolution' || name === 'tileOffset' || name === 'fullResolution' ? 'Vec2' : 'number']))
const f = Math.fround
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const stable = value => JSON.stringify(value, null, 2) + '\n'
const words = view => Array.from(new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4), n => `0x${n.toString(16).padStart(8, '0')}`)
const packWords = values => { const b = Buffer.alloc(values.length * 4); values.forEach((v, i) => b.writeUInt32LE(Number.parseInt(v, 16) >>> 0, i * 4)); return b }
const digestWords = values => sha256(packWords(values))
const digestBytes = values => sha256(Buffer.from(values))
const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i])
const changed = (a, b) => a.reduce((n, v, i) => n + (v !== b[i] ? 1 : 0), 0)
const beneath = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`)

function rejectAbsolute(value, label = 'document') {
  if (typeof value === 'string') {
    if (/^(?:[A-Za-z]:[\\/]|\\\\|\/)/.test(value) || /(?:^|[\\/])(?:Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute-looking string`)
  } else if (Array.isArray(value)) value.forEach((v, i) => rejectAbsolute(v, `${label}[${i}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([k, v]) => rejectAbsolute(v, `${label}.${k}`))
}
function checked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(`${target}.sha256`, `${sha256(payload)}  ${path.basename(target)}\n`) }
function verify(target) { const payload = fs.readFileSync(target); if (fs.readFileSync(`${target}.sha256`, 'utf8') !== `${sha256(payload)}  ${path.basename(target)}\n`) throw new Error(`sidecar drift: ${target}`); return payload }
function compareExact(expected, actual, label = 'comparison') {
  if (expected.width !== actual.width || expected.height !== actual.height) throw new Error(`${label}: dimensions mismatch`)
  const count = expected.width * expected.height * 4
  if (!Array.isArray(expected.f32_words_le) || !Array.isArray(actual.f32_words_le) || expected.f32_words_le.length !== count || actual.f32_words_le.length !== count) throw new Error(`${label}: Float32 lane count mismatch`)
  if (!Array.isArray(expected.rgba8_bytes) || !Array.isArray(actual.rgba8_bytes) || expected.rgba8_bytes.length !== count || actual.rgba8_bytes.length !== count) throw new Error(`${label}: RGBA8 byte count mismatch`)
  for (let i = 0; i < count; i += 1) if (expected.f32_words_le[i] !== actual.f32_words_le[i]) throw new Error(`${label}: Float32 first mismatch at lane ${i}`)
  for (let i = 0; i < count; i += 1) if (expected.rgba8_bytes[i] !== actual.rgba8_bytes[i]) throw new Error(`${label}: RGBA8 first mismatch at byte ${i}`)
  return true
}

const argv = process.argv.slice(2)
const modes = argv.filter(x => ['--write', '--check', '--self-test'].includes(x))
if (modes.length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || ci + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
if (argv.some((x, i) => i !== ci && i !== ci + 1 && x !== modes[0])) throw new Error('unexpected argument')
const cpuArg = argv[ci + 1]
if (!fs.existsSync(cpuArg) || !fs.statSync(cpuArg).isDirectory()) throw new Error('--cpu-root is not a directory')
const cpuRoot = fs.realpathSync(cpuArg)
const liveArg = process.env.NOISEMAKER_FOR_CPU || path.resolve(cppRoot, '../noisemaker-for-cpu')
const liveRoot = fs.existsSync(liveArg) ? fs.realpathSync(liveArg) : null
if (liveRoot && (beneath(liveRoot, cpuRoot) || beneath(cpuRoot, liveRoot))) throw new Error('--cpu-root must be an immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')

function closure() {
  const patterns = [/\bfrom\s*['"]([^'"\n]+)['"]/g, /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g, /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm]
  const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
  const stack = entries.map(x => path.join(cpuRoot, x)); const seen = new Map()
  while (stack.length) {
    const candidate = fs.realpathSync(stack.pop()); if (seen.has(candidate)) continue
    if (!beneath(cpuRoot, candidate) || (liveRoot && beneath(liveRoot, candidate))) throw new Error('import escaped immutable snapshot')
    const payload = fs.readFileSync(candidate); const text = payload.toString('utf8'); seen.set(candidate, sha256(payload))
    if (/\bimport\s*\(\s*(?!['"])/.test(text)) throw new Error(`nonliteral dynamic import: ${path.relative(cpuRoot, candidate)}`)
    for (const pattern of patterns) { pattern.lastIndex = 0; let match; while ((match = pattern.exec(text))) { const spec = match[1]; if (spec.startsWith('node:')) continue; if (!spec.startsWith('./') && !spec.startsWith('../') && !spec.startsWith('/')) throw new Error(`bare module specifier ${spec}`); stack.push(fs.realpathSync(spec.startsWith('/') ? spec : path.resolve(path.dirname(candidate), spec))) } }
  }
  return [...seen].map(([file, hash]) => [path.relative(cpuRoot, file), hash]).sort((a, b) => a[0].localeCompare(b[0]))
}
const actualClosure = closure()
if (JSON.stringify(actualClosure) !== JSON.stringify([...expectedClosure].sort((a, b) => a[0].localeCompare(b[0])))) throw new Error(`CPU import closure mismatch: ${JSON.stringify(actualClosure)}`)
for (const [relative, expected] of expectedClosure) if (sha256(fs.readFileSync(path.join(cpuRoot, relative))) !== expected) throw new Error(`pinned CPU provenance drift: ${relative}`)
const sourcePayload = fs.readFileSync(path.join(cppRoot, sourceRelative)); if (sha256(sourcePayload) !== sourceSha256) throw new Error('newton corpus source provenance drift')
const load = relative => import(pathToFileURL(fs.realpathSync(path.join(cpuRoot, relative))).href)
const [{ canonicalKernelFactories, kernelFactories, canonicalAdapterFactories }, { UPSTREAM_REVISION }, { bindCanonicalKernel }, { runPass }, { Surface }] = await Promise.all([load('src/effects/catalog.js'), load('src/effects/generated/upstream-snapshot.js'), load('src/csl/glsl-kernel.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js')])
const canonicalFactory = canonicalKernelFactories[programKey]; const publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== factoryName) throw new Error('canonical factory identity drift')
if (publicFactory !== canonicalFactory) throw new Error('public factory is not canonical identity')
if (Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey)) throw new Error('newton is adapter-routed')
if (UPSTREAM_REVISION !== upstreamRevision) throw new Error('upstream revision drift')
const canonicalFactoryText = Function.prototype.toString.call(canonicalFactory)
if (sha256(canonicalFactoryText) !== factoryTextSha256) throw new Error('canonical factory text drift')

function syntheticInput(width, height, salt) { const input = new Surface(width, height); for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) { const i = (y * width + x) * 4; input.data[i] = f(((x * 3 + y * 5 + salt) % 17) / 16); input.data[i + 1] = f(((x * 7 + y * 2 + salt) % 19) / 18); input.data[i + 2] = f(((x * 11 + y * 13 + salt) % 23) / 22); input.data[i + 3] = f(1) } return input }
const cases = [
  { name: 'manual-baseline', width: 4, height: 4, time: 0.25, poi: 0, outputMode: 0, iterations: 80, degree: 3, relaxation: 1, tolerance: 0.001, centerHiX: 0, centerHiY: 0, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 1, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: 0, invert: 0, tileX: 0, tileY: 0, salt: 1 },
  { name: 'poi-spiral', width: 4, height: 3, time: 0.75, poi: 2, outputMode: 0, iterations: 100, degree: 3, relaxation: 1, tolerance: 0.0001, centerHiX: 0, centerHiY: 0, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 5, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: 11, invert: 0, tileX: 0.25, tileY: -0.25, salt: 2 },
  { name: 'root-mode', width: 3, height: 4, time: 1.25, poi: 4, outputMode: 1, iterations: 120, degree: 5, relaxation: 0.9, tolerance: 0.01, centerHiX: 0, centerHiY: 0, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 3, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: -17, invert: 0, tileX: 0, tileY: 0, salt: 3 },
  { name: 'combined-mode', width: 5, height: 3, time: 2, poi: 3, outputMode: 2, iterations: 150, degree: 5, relaxation: 1.2, tolerance: 0.005, centerHiX: 0.01, centerHiY: -0.02, centerLoX: 1e-7, centerLoY: -2e-7, zoomSpeed: 1.2, zoomDepth: 4, degreeSpeed: 0.5, degreeRange: 1, relaxSpeed: 0.7, relaxRange: 0.3, rotation: 25, invert: 0, tileX: -0.5, tileY: 0.5, salt: 4 },
  { name: 'invert-axis', width: 4, height: 4, time: 0.5, poi: 1, outputMode: 0, iterations: 70, degree: 3, relaxation: 1, tolerance: 0.002, centerHiX: 0, centerHiY: 0, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 2, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: 0, invert: 1, tileX: 0, tileY: 0, salt: 5 },
  { name: 'degree-axis', width: 3, height: 3, time: 1.1, poi: 0, outputMode: 0, iterations: 90, degree: 7, relaxation: 1, tolerance: 0.003, centerHiX: -0.2, centerHiY: 0.15, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 1, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: 8, invert: 0, tileX: 0, tileY: 0, salt: 6 },
  { name: 'relax-axis', width: 3, height: 5, time: 1.7, poi: 0, outputMode: 2, iterations: 110, degree: 4, relaxation: 1.6, tolerance: 0.002, centerHiX: 0.1, centerHiY: -0.1, centerLoX: 0, centerLoY: 0, zoomSpeed: 0.8, zoomDepth: 2, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: 33, invert: 0, tileX: 0, tileY: 0, salt: 7 },
  { name: 'tolerance-axis', width: 5, height: 4, time: 0.9, poi: 5, outputMode: 1, iterations: 100, degree: 6, relaxation: 1, tolerance: 0.05, centerHiX: 0, centerHiY: 0, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 2, degreeSpeed: 0, degreeRange: 0, relaxSpeed: 0, relaxRange: 0, rotation: -9, invert: 0, tileX: 0, tileY: 0, salt: 8 },
]
function render(spec, factory = canonicalFactory) {
  const input = syntheticInput(spec.width, spec.height, spec.salt); const before = new Uint32Array(input.data.buffer.slice(0))
  const bindings = {}
  for (const name of bindingNames) bindings[name] = name === 'resolution' || name === 'tileOffset' || name === 'fullResolution' ? new Float32Array(name === 'tileOffset' ? [spec.tileX, spec.tileY] : [spec.width, spec.height]) : f(spec[name])
  const kernel = bindCanonicalKernel(factory, { width: spec.width, height: spec.height, time: spec.time, seed: 0, uniforms: bindings, textures: {}, tileOffset: bindings.tileOffset, fullResolution: bindings.fullResolution })
  const output = new Surface(spec.width, spec.height); runPass({ kernel, destination: output, time: spec.time, seed: 0, tileRows: 1 })
  return { inputWords: words(input.data), outputWords: words(output.data), outputBytes: Array.from(output.toRgba8()), inputUnchanged: same(Array.from(before), Array.from(new Uint32Array(input.data.buffer))), outputStorageDistinct: output.data !== input.data, outputObject: output, outputData: output.data }
}
function bindingRecord(spec) { return Object.fromEntries(bindingNames.map(name => [name, name === 'resolution' || name === 'fullResolution' ? [spec.width, spec.height] : name === 'tileOffset' ? [spec.tileX, spec.tileY] : spec[name]])) }
const rendered = cases.map(spec => { const first = render(spec); const second = render(spec); const repeatOutputObjectDistinct = first.outputObject !== second.outputObject; const repeatOutputDataDistinct = first.outputData !== second.outputData; if (!same(first.outputWords, second.outputWords) || !same(first.outputBytes, second.outputBytes)) throw new Error(`repeatability failed: ${spec.name}`); if (!first.inputUnchanged || !first.outputStorageDistinct || !repeatOutputObjectDistinct || !repeatOutputDataDistinct) throw new Error(`storage/input/repeat identity contract failed: ${spec.name}`); return { ...spec, input: { width: spec.width, height: spec.height, f32_words_le: first.inputWords, f32_sha256: digestWords(first.inputWords) }, expected: { f32_words_le: first.outputWords, f32_sha256: digestWords(first.outputWords), rgba8_bytes: first.outputBytes, rgba8_sha256: digestBytes(first.outputBytes) }, input_immutable_exact_bits: true, bindings: bindingRecord(spec), repeat_identity: true, repeat_output_object_distinct: repeatOutputObjectDistinct, repeat_output_data_distinct: repeatOutputDataDistinct, public_direct_identity: true, independent_output_storage: true } })
const baseline = new Map(rendered.map(x => [x.name, x]))

const mutationDefs = [
  { name: 'cross-lane-assignment', group: 'cross-lane-assignment', mechanism: 'replace source-order sequential matrix lane writes with swapped lane owners', anchor: '(uv[0] = cpu_matrix_assignment_0[0], uv[1] = cpu_matrix_assignment_0[1], uv);', replacement: '(uv[0] = cpu_matrix_assignment_0[1], uv[1] = cpu_matrix_assignment_0[0], uv);' },
  { name: 'df64-cmul-rr-owner', group: 'out-materialization', mechanism: 'replace df64_cmul real out-owner materialization', anchor: 'df64_sub(df64_mul(ar, br), df64_mul(ai, bi)).reduce((res,el,i)=>(res[i] = el, res), rr);', replacement: 'rr.fill(0);' },
  { name: 'df64-cmul-ri-owner', group: 'out-materialization', mechanism: 'replace df64_cmul imaginary out-owner materialization', anchor: 'df64_add(df64_mul(ar, bi), df64_mul(ai, br)).reduce((res,el,i)=>(res[i] = el, res), ri);', replacement: 'ri.fill(0);' },
  { name: 'transform-re-owner', group: 'out-materialization', mechanism: 'replace transformCoords real out-owner materialization', anchor: 'df64_add(uv_re_df, cX_df).reduce((res,el,i)=>(res[i] = el, res), re_df);', replacement: 're_df.fill(0);' },
  { name: 'transform-im-owner', group: 'out-materialization', mechanism: 'replace transformCoords imaginary out-owner materialization', anchor: 'df64_add(uv_im_df, cY_df).reduce((res,el,i)=>(res[i] = el, res), im_df);', replacement: 'im_df.fill(0);' },
  { name: 'cmul-call-materialization', group: 'out-materialization', mechanism: 'replace df64_cmul power carrier with a zero imaginary owner', anchor: '(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), [tr, ti] = df64_cmul.__out__, df64_cmul.__return__);', replacement: '(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), [tr, ti] = [tr, new $runtime.PooledFloat32Array([0, 0])], df64_cmul.__return__);' },
  { name: 'znr-call-materialization', group: 'out-materialization', mechanism: 'replace df64_cmul result carrier at the z-power owner', anchor: '(df64_cmul(pwr, pwi, zr_df, zi_df, znr, zni), [znr, zni] = df64_cmul.__out__, df64_cmul.__return__);', replacement: '(df64_cmul(pwr, pwi, zr_df, zi_df, znr, zni), [znr, zni] = [znr, new $runtime.PooledFloat32Array([0, 0])], df64_cmul.__return__);' },
  { name: 'transform-call-materialization', group: 'out-materialization', mechanism: 'replace transformCoords out carrier owner', anchor: '(transformCoords_df64(globalCoord, new $runtime.PooledFloat32Array([cHi[0], cLo[0]]), new $runtime.PooledFloat32Array([cHi[1], cLo[1]]), zoom, rotation, re_df, im_df), [re_df, im_df] = transformCoords_df64.__out__, transformCoords_df64.__return__);', replacement: '(transformCoords_df64(globalCoord, new $runtime.PooledFloat32Array([cHi[0], cLo[0]]), new $runtime.PooledFloat32Array([cHi[1], cLo[1]]), zoom, rotation, re_df, im_df), [re_df, im_df] = [transformCoords_df64.__out__[0], new $runtime.PooledFloat32Array([0, 0])], transformCoords_df64.__return__);' },
  { name: 'iteration-outer-bound', group: 'control-axis', mechanism: 'shorten Newton iteration bound', anchor: 'for (var n = 0; n < 500; n++)', replacement: 'for (var n = 0; n < 1; n++)' },
  { name: 'iteration-power-bound', group: 'control-axis', mechanism: 'shorten repeated-power bound', anchor: 'for (var j = 0; j < 7; j++)', replacement: 'for (var j = 0; j < 1; j++)' },
  { name: 'degree-control-axis', group: 'control-axis', mechanism: 'offset effective degree control', anchor: 'var effDegree = degree;', replacement: 'var effDegree = degree + 1;' },
  { name: 'relaxation-control-axis', group: 'control-axis', mechanism: 'offset effective relaxation control', anchor: 'var effRelax = relaxation;', replacement: 'var effRelax = relaxation + 0.25;' },
  { name: 'tolerance-control-axis', group: 'control-axis', mechanism: 'widen convergence tolerance control', anchor: 'if (d < tolerance) {', replacement: 'if (d < (tolerance * 2)) {' },
  { name: 'rotation-control-axis', group: 'control-axis', mechanism: 'reverse rotation control', anchor: 'var angle = (-rot * TAU) / 360;', replacement: 'var angle = (rot * TAU) / 360;' },
  { name: 'invert-control-axis', group: 'control-axis', mechanism: 'remove inversion control', anchor: 'value = 1 - value;', replacement: 'value = value;' },
  { name: 'struct-POIData-declaration', group: 'struct-declaration', mechanism: 'source-bound POIData declaration probe paired with an executed canonical POI representation mutant', anchor: 'return {\n  \tcenter: new $runtime.PooledFloat32Array([0, 0, 0, 0]),\n  \tdeg: 3,\n  \tmaxZoom: 7\n  \t};\n  \t};\n  \tif (idx == 2) {', replacement: 'return {\n  \tcenter: new $runtime.PooledFloat32Array([0, 0, 0, 0]),\n  \tdeg: 4,\n  \tmaxZoom: 7\n  \t};\n  \t};\n  \tif (idx == 2) {', sourceProbeAnchor: 'struct POIData {', sourceProbeReplacement: 'struct POIData { float provenanceWitness;' },
]
function mutateFactory(def) {
  const targetText = canonicalFactoryText
  const targetAnchor = def.anchor
  const targetReplacement = def.replacement
  const count = targetText.split(targetAnchor).length - 1; const expected = def.expectedCount ?? 1
  if (count !== expected) throw new Error(`${def.name}: anchor cardinality ${count}, expected ${expected}`)
  const source = targetText.replaceAll(targetAnchor, targetReplacement)
  const factory = Function(`return (${source})`)()
  if (typeof factory !== 'function') throw new Error(`${def.name}: mutated factory did not evaluate`)
  return { source, factory, anchor_occurrence_count: count }
}
function mismatch(reference, candidate) { const floatCount = changed(reference.expected.f32_words_le, candidate.outputWords); const byteCount = changed(reference.expected.rgba8_bytes, candidate.outputBytes); let first = null; for (let i = 0; i < reference.expected.f32_words_le.length; i += 1) if (reference.expected.f32_words_le[i] !== candidate.outputWords[i]) { first = { lane: i, reference: reference.expected.f32_words_le[i], candidate: candidate.outputWords[i] }; break } return { mismatched_lanes: floatCount, mismatched_bytes: byteCount, first_mismatch: first } }
const ledger = mutationDefs.map(def => { const mutant = mutateFactory(def); const results = cases.map(spec => { const candidate = render(spec, mutant.factory); const row = mismatch(baseline.get(spec.name), candidate); return { case: spec.name, ...row } }); const witnesses = results.filter(x => x.mismatched_lanes > 0).map(x => x.case); const sourceProbe = def.sourceProbeAnchor ? { structural_probe: true, source_probe_anchor: def.sourceProbeAnchor, source_probe_replacement: def.sourceProbeReplacement, source_probe_anchor_sha256: sha256(def.sourceProbeAnchor), source_probe_replacement_sha256: sha256(def.sourceProbeReplacement), factory_anchor: def.anchor, factory_replacement: def.replacement, factory_anchor_sha256: sha256(def.anchor), factory_replacement_sha256: sha256(def.replacement) } : {}; return { name: def.name, group: def.group, mechanism: def.mechanism, independent: true, structural_only: false, source_relative_path: sourceRelative, source_sha256: sourceSha256, canonical_factory_text_sha256: factoryTextSha256, source_anchor: def.sourceProbeAnchor || def.anchor, replacement: def.sourceProbeReplacement || def.replacement, source_anchor_sha256: sha256(def.sourceProbeAnchor || def.anchor), replacement_sha256: sha256(def.sourceProbeReplacement || def.replacement), mutated_factory_text_sha256: sha256(mutant.source), anchor_occurrence_count: mutant.anchor_occurrence_count, required_witnesses: witnesses, required_witness_results: results.filter(x => x.mismatched_lanes > 0), ...sourceProbe } })
for (const row of ledger) if (!row.structural_only && row.required_witnesses.length === 0) throw new Error(`${row.name}: no behavioral witness`)

const comparerFixture = { width: 1, height: 1, f32_words_le: ['0x00000000', '0x80000000', '0x7fc00001', '0x3f800000'], rgba8_bytes: [0, 0, 127, 255] }
const rejects = fn => { try { fn(); return false } catch { return true } }
const comparerProbe = fn => { try { fn(); return { rejected: false, message: '' } } catch (error) { return { rejected: true, message: String(error?.message || error) } } }
let dimensionsAccessed = false
const dimensionsActual = { width: 2, height: 1 }
Object.defineProperty(dimensionsActual, 'f32_words_le', { get() { dimensionsAccessed = true; return [] } })
const comparerProbes = { good: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: [...comparerFixture.f32_words_le], rgba8_bytes: [...comparerFixture.rgba8_bytes] })), dimensions: comparerProbe(() => compareExact(comparerFixture, dimensionsActual, 'dimensions')), short: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: comparerFixture.f32_words_le.slice(0, 3) }, 'short')), long: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: [...comparerFixture.f32_words_le, '0x00000000'] }, 'long')), rgba8_count: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, rgba8_bytes: [0, 1, 2] }, 'rgba8-count')), rgba8_mismatch: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, rgba8_bytes: [0, 1, 3, 255] }, 'rgba8-mismatch')), signed_zero: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x80000000', ...comparerFixture.f32_words_le.slice(1)] }, 'signed-zero')), nan_payload: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x00000000', '0x80000000', '0x7fc00002', '0x3f800000'] }, 'nan-payload')), f32_first: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x00000001', ...comparerFixture.f32_words_le.slice(1)] }, 'f32-first')), rgba_first: comparerProbe(() => compareExact(comparerFixture, { ...comparerFixture, rgba8_bytes: [1, 0, 127, 255] }, 'rgba-first')) }
const comparerSelfTests = { dimensions_before_access: comparerProbes.dimensions.rejected && !dimensionsAccessed, first_mismatch_reported: comparerProbes.f32_first.message.includes('first mismatch') && comparerProbes.rgba_first.message.includes('first mismatch'), raw_words_and_rgba8_independent: comparerProbes.f32_first.rejected && comparerProbes.f32_first.message.includes('Float32') && comparerProbes.rgba_first.rejected && comparerProbes.rgba_first.message.includes('RGBA8'), cases: { good: !comparerProbes.good.rejected, dimensions: comparerProbes.dimensions.rejected, short: comparerProbes.short.rejected, long: comparerProbes.long.rejected, rgba8_count: comparerProbes.rgba8_count.rejected, rgba8_mismatch: comparerProbes.rgba8_mismatch.rejected, signed_zero: comparerProbes.signed_zero.rejected, nan_payload: comparerProbes.nan_payload.rejected } }
if (!Object.values(comparerSelfTests.cases).every(Boolean)) throw new Error('comparer self-test failed')
const sourceMutationContract = { source_relative_path: sourceRelative, source_sha256: sourceSha256, canonical_factory_text_sha256: factoryTextSha256, execution: 'each exact factory anchor/replacement is evaluated and executed through bindCanonicalKernel/runPass; the struct source mutation is structural-only' }
const document = { schema: 'noisemaker-for-cpp.newton.pixel-parity.v1', schema_version: 1, program_key: programKey, effect_key: 'synth/newton', runtime_key: programKey, corpus_revision: corpusRevision, upstream_revision: upstreamRevision, factory: { name: factoryName, text_sha256: factoryTextSha256, public_factory_is_canonical_identity: true, adapter_own_key: false }, runtime_binding_names: bindingNames, runtime_binding_abi: bindingAbi, canonical_binding_contract: { names: bindingNames, abi: bindingAbi }, exactness_contract: { float32: 'raw little-endian uint32 words; signed zero and NaN payloads significant', rgba8: 'complete independently captured RGBA8 bytes', tolerance: 'none', dimensions: 'checked before lane access', comparison: 'dimensions, counts, every uint32 word, every RGBA8 byte' }, comparer_self_tests: comparerSelfTests, provenance: { source: { relative_path: sourceRelative, sha256: sourceSha256 }, cpu_snapshot: { argument: '<immutable-cpu-snapshot-root>', immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, import_closure: actualClosure.map(([relative_path, hash]) => ({ relative_path, sha256: hash })), closure_cardinality: actualClosure.length }, generator: { relative_path: 'docs/port-engineering/newton-parity/newton_oracle_generator.mjs', sha256: sha256(fs.readFileSync(generatorPath)) }, materializer: { relative_path: 'tools/glslcpp/generate_newton_native_oracle_include.py' } }, render_cases: rendered, source_mutation_contract: { ...sourceMutationContract, execution: 'each exact factory anchor/replacement is evaluated and executed through bindCanonicalKernel/runPass; struct-POIData-declaration additionally records a source-bound struct probe paired with its executed POI representation mutant' }, mutation_anchor_cardinality: { total: ledger.length, by_group: Object.fromEntries([...new Set(ledger.map(x => x.group))].map(group => [group, ledger.filter(x => x.group === group).length])), anchors: Object.fromEntries(ledger.map(x => [x.name, x.anchor_occurrence_count])) }, mutation_ledger: ledger, control_group: { repeatability: { case: 'manual-baseline', identical_float32: true, identical_rgba8: true, distinct_output_objects: true, distinct_output_data: true }, input_immutability: { case: 'manual-baseline', unchanged: true }, independent_output_storage: { case: 'manual-baseline', distinct_data_objects: true }, public_direct_identity: true }, cross_lane_assignment_profile: { status: 'authenticated', source_bound: 'newton source and canonical factory pins', anchor: ledger.find(x => x.name === 'cross-lane-assignment').source_anchor, replacement: ledger.find(x => x.name === 'cross-lane-assignment').replacement, mutated_factory_text_sha256: ledger.find(x => x.name === 'cross-lane-assignment').mutated_factory_text_sha256 }, claim_boundaries: { absolute_paths: 'stable placeholders only', authority: 'unmodified public canonicalFactory264 from immutable CPU snapshot; no local reimplementation or C++ output participates', adapter: 'no adapter owns this key', mutations: 'exact source/factory anchor replacements are executed authority mutations, not uniform perturbations' } }
rejectAbsolute(document)
const jsonPayload = Buffer.from(stable(document))
const report = Buffer.from(`# Newton exact-pixel oracle\n\n- Program: ${programKey}\n- Authority: unmodified public canonicalFactory264 from an immutable CPU snapshot.\n- Cases: ${rendered.length}; exact mutation ledger entries: ${ledger.length}.\n- The checked closure has ${actualClosure.length} files and is realpath-confined; literal dynamic imports are traversed and nonliteral imports are rejected.\n- Controls include repeatability, direct public identity, independent output storage, and exact input Float32-bit immutability.\n- Compare with raw Float32 words and independently captured RGBA8 bytes; tolerance is none.\n\n## Reproduction\n\nnode docs/port-engineering/newton-parity/newton_oracle_generator.mjs --check --cpu-root \"$NOISEMAKER_CPU_ROOT\"\npython3 -B tools/glslcpp/generate_newton_native_oracle_include.py --check\n\nAbsolute checkout paths are intentionally omitted from this report and JSON.\n`)
function selfTest() { const checks = [['factory identity', publicFactory === canonicalFactory], ['closure exact', JSON.stringify(actualClosure) === JSON.stringify([...expectedClosure].sort((a, b) => a[0].localeCompare(b[0])))], ['raw words and bytes complete', rendered.every(x => x.expected.f32_words_le.length === x.width * x.height * 4 && x.expected.rgba8_bytes.length === x.width * x.height * 4)], ['input immutable', rendered.every(x => x.input_immutable_exact_bits)], ['absolute strings rejected', rejects(() => rejectAbsolute({ x: '/tmp/no' }))], ['mutation anchors exact', ledger.every(x => x.anchor_occurrence_count > 0 && x.independent && (x.structural_only || x.required_witnesses.length > 0))], ['custom comparer self-tests', Object.values(comparerSelfTests.cases).every(Boolean)]]; checks.forEach(([name, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}`)); return checks.every(([, ok]) => ok) ? 0 : 1 }
if (modes[0] === '--self-test') process.exit(selfTest())
if (modes[0] === '--write') { checked(outputPath, jsonPayload); checked(reportPath, report); checked(generatorPath, fs.readFileSync(generatorPath)); console.log(`newton oracle written (${jsonPayload.length} bytes, ${sha256(jsonPayload)})`) }
else { if (!verify(outputPath).equals(jsonPayload) || !verify(reportPath).equals(report) || !verify(generatorPath).equals(fs.readFileSync(generatorPath))) throw new Error('newton oracle package drift'); console.log('newton oracle: ok') }
