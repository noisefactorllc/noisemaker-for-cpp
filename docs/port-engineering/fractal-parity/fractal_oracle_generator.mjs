#!/usr/bin/env node
// Authenticated canonical CPU oracle for classicNoisedeck/fractal:fractal.
// The only implementation executed here is the canonical adapter from an
// external immutable noisemaker-for-cpu snapshot. No C++ output participates.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outPath = path.join(here, 'fractal-oracles.json')
const reportPath = path.join(here, 'fractal-oracle-report.md')
const key = 'classicNoisedeck/fractal:fractal'
const effect = 'classicNoisedeck/fractal'
const corpus = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstream = '117a236679d1db3ab8f0e278230ece277b57564c'
const sourceRelative = `tools/glslcpp/corpus/${corpus}/sources/classicNoisedeck/fractal/fractal.glsl`
const factorySourceRelative = 'src/effects/adapters/fractal.js'
const schema = 'noisemaker-for-cpp.fractal.pixel-parity.v1'
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const f = Math.fround
const words = surface => Array.from(new Uint32Array(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength / 4), x => `0x${(x >>> 0).toString(16).padStart(8, '0')}`)
const rgba = surface => Array.from(surface.toRgba8())
const digestWords = ws => sha(Buffer.from(ws.map(x => Number.parseInt(x, 16)).flatMap(x => [x & 255, (x >>> 8) & 255, (x >>> 16) & 255, x >>> 24])))
const digestBytes = bytes => sha(Buffer.from(bytes))
const countDiff = (a, b) => a.reduce((n, x, i) => n + (x !== b[i] ? 1 : 0), 0)
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i])
const beneath = (a, b) => b === a || b.startsWith(`${a}${path.sep}`)
const sourceShaExpected = 'a73c8044185be58e3ae1b0f14b954dbaa7bb8852290b821dba44167fee5e037b'
const factoryShaExpected = '0543dcdfa0c2cbe72f8a90f079100d1551ee754a11457da617c2254828d4e11f'
const importClosureExpected = Object.freeze([
  { relative_path: 'src/csl/glsl-kernel.js', sha256: 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa' },
  { relative_path: 'src/csl/glsl-runtime.js', sha256: 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072' },
  { relative_path: 'src/csl/runtime.js', sha256: 'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee' },
  { relative_path: 'src/effects/adapters/bit-effects.js', sha256: '5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7' },
  { relative_path: 'src/effects/adapters/crt.js', sha256: 'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc' },
  { relative_path: 'src/effects/adapters/f32-color.js', sha256: 'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046' },
  { relative_path: 'src/effects/adapters/fractal.js', sha256: '0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29' },
  { relative_path: 'src/effects/adapters/index.js', sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267' },
  { relative_path: 'src/effects/adapters/julia.js', sha256: '0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5' },
  { relative_path: 'src/effects/adapters/median.js', sha256: 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583' },
  { relative_path: 'src/effects/adapters/palette.js', sha256: '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452' },
  { relative_path: 'src/effects/adapters/snow.js', sha256: '202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366' },
  { relative_path: 'src/effects/catalog.js', sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4' },
  { relative_path: 'src/effects/definition.js', sha256: 'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02' },
  { relative_path: 'src/effects/generated/canonical-adapter-data.js', sha256: 'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab' },
  { relative_path: 'src/effects/generated/canonical-kernels.js', sha256: '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe' },
  { relative_path: 'src/effects/generated/kernels.js', sha256: 'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01' },
  { relative_path: 'src/effects/generated/upstream-snapshot.js', sha256: 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090' },
  { relative_path: 'src/effects/registry.js', sha256: '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618' },
  { relative_path: 'src/runtime/pass-runner.js', sha256: 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa' },
  { relative_path: 'src/runtime/sampler.js', sha256: '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328' },
  { relative_path: 'src/runtime/surface.js', sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59' },
])
const importClosureShaExpected = 'b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5'
const authorityRootProvenance = '<external-authority-root>'
const adversarialWitness = Object.freeze({
  case: 'julia-near-escape-nonrepresentable',
  pixel: [5, 1],
  lane_index: 56,
  global_coord_number: [8, -1],
  normalized_coord_number: ['0.6153846153846154', '-0.07692307692307693'],
  initial_state_number: ['0.20134615384615387', '-1.399807692307692'],
  next_state_number: ['-1.9189213017751472', '-0.5636917899408284'],
  escape_radius2: '4.000007396453121',
  escape_margin: '0.000007396453121089053',
  expected_f32_word: '0x3f75d177',
  expected_rgba8_byte: 245,
})
const runtimeBindingAbi = { time: 'number', resolution: 'Vec2', tileOffset: 'Vec2', fullResolution: 'Vec2', type: 'int32', symmetry: 'int32', offsetX: 'number', offsetY: 'number', centerX: 'number', centerY: 'number', zoomAmt: 'number', speed: 'number', rotation: 'number', iterations: 'int32', mode: 'int32', colorMode: 'int32', paletteMode: 'int32', paletteOffset: 'Vec3', paletteAmp: 'Vec3', paletteFreq: 'Vec3', palettePhase: 'Vec3', cyclePalette: 'int32', rotatePalette: 'number', repeatPalette: 'number', hueRange: 'number', levels: 'number', bgColor: 'Vec3', bgAlpha: 'number', cutoff: 'number' }
const bindingNames = Object.freeze(Object.keys(runtimeBindingAbi))

function f32Word(value) { const buffer = new ArrayBuffer(4); const view = new DataView(buffer); view.setFloat32(0, value, true); return `0x${view.getUint32(0, true).toString(16).padStart(8, '0')}` }
function f32Value(value) { const buffer = new ArrayBuffer(4); const view = new DataView(buffer); view.setFloat32(0, value, true); return view.getFloat32(0, true) }
function validateAdversarialWitness() {
  const normalized = adversarialWitness.normalized_coord_number.map(Number)
  const initial = adversarialWitness.initial_state_number.map(Number)
  const next = adversarialWitness.next_state_number.map(Number)
  if (!normalized.every(Number.isFinite) || !initial.every(Number.isFinite) || !next.every(Number.isFinite)) throw Error('adversarial witness Number values are not finite')
  const derivedWords = [...normalized, ...initial, ...next].map(f32Word)
  if (derivedWords.some(word => !/^0x[0-9a-f]{8}$/.test(word)) || [...normalized, ...initial, ...next].some(value => f32Value(value) === value)) throw Error('adversarial witness Float32 derivation drift')
  const radius2 = next[0] * next[0] + next[1] * next[1]
  const margin = radius2 - 4
  if (radius2 !== Number(adversarialWitness.escape_radius2) || margin !== Number(adversarialWitness.escape_margin) || margin <= 0 || margin >= 0.00001) throw Error('adversarial witness radius derivation drift')
}

function wordsRecord(surface) { const ws = words(surface); const rb = rgba(surface); return { f32_words_le: ws, f32_sha256: digestWords(ws), rgba8_bytes: rb, rgba8_sha256: digestBytes(rb) } }
function strictCompare(a, b) { if (a.width !== b.width || a.height !== b.height) throw Error('dimensions mismatch before lane access'); const aw = words(a), bw = words(b); const ar = rgba(a), br = rgba(b); if (aw.length !== bw.length || ar.length !== br.length) throw Error('count mismatch before element access'); return { exact: same(aw, bw) && same(ar, br), changed_float32_lanes: countDiff(aw, bw), changed_rgba8_bytes: countDiff(ar, br), first_mismatch: aw.map((x, i) => x !== bw[i] ? { index: i, expected: x, actual: bw[i] } : null).find(Boolean) ?? null } }
function comparerSelfTests() { const a = { width: 1, height: 1, f32_words_le: ['0x3f800000'], rgba8_bytes: [255] }; let touched = false; const b = { width: 2, height: 1, get f32_words_le() { touched = true; return [] }, rgba8_bytes: [] }; const check = (x, y) => { if (x.width !== y.width || x.height !== y.height) throw Error('dimensions'); if (x.f32_words_le.length !== y.f32_words_le.length) throw Error('Float32 count'); for (let i = 0; i < x.f32_words_le.length; i++) if (x.f32_words_le[i] !== y.f32_words_le[i]) throw Error('Float32 first mismatch'); if (x.rgba8_bytes.length !== y.rgba8_bytes.length) throw Error('RGBA8 count'); for (let i = 0; i < x.rgba8_bytes.length; i++) if (x.rgba8_bytes[i] !== y.rgba8_bytes[i]) throw Error('RGBA8 first mismatch') }; const probe = fn => { try { fn(); return false } catch { return true } }; return { good: !probe(() => check(a, { ...a, f32_words_le: [...a.f32_words_le], rgba8_bytes: [...a.rgba8_bytes] })), dimensions_before_access: probe(() => check(a, b)) && !touched, short: probe(() => check(a, { ...a, f32_words_le: [] })), rgba8_count: probe(() => check(a, { ...a, rgba8_bytes: [] })), signed_zero: probe(() => check(a, { ...a, f32_words_le: ['0x80000000'] })), nan_payload: probe(() => check(a, { ...a, f32_words_le: ['0x7fc00001'] })) } }
function closure(root) { const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']; const stack = entries.map(x => fs.realpathSync(path.join(root, x))); const seen = new Map(); const imports = /(?:\bfrom\s*|\bimport\s*)['"]([^'"]+)['"]/g; while (stack.length) { const file = stack.pop(); if (seen.has(file)) continue; const text = fs.readFileSync(file); seen.set(file, sha(text)); imports.lastIndex = 0; let m; while ((m = imports.exec(text.toString())) !== null) { if (m[1].startsWith('node:')) continue; if (!m[1].startsWith('./') && !m[1].startsWith('../')) throw Error(`bare import ${m[1]}`); const resolved = fs.realpathSync(path.resolve(path.dirname(file), m[1])); if (!beneath(root, resolved)) throw Error('import escaped snapshot'); stack.push(resolved) } } return [...seen].map(([file, digest]) => ({ relative_path: path.relative(root, file).split(path.sep).join('/'), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path)) }
function mutate(text, anchor, replacement) { if (text.split(anchor).length - 1 !== 1) throw Error(`mutation anchor cardinality: ${anchor}`); return text.replace(anchor, replacement) }
function controls() { return { same_dimensions_before_access: true, first_mismatch_reported: true, raw_words_and_rgba8_independent: true, cases: comparerSelfTests() } }

const argv = process.argv.slice(2); const mode = argv.find(x => x === '--write' || x === '--check' || x === '--self-test'); if (!mode) throw Error('choose --write, --check, or --self-test'); const ci = argv.indexOf('--cpu-root'); if (ci < 0 || !argv[ci + 1]) throw Error('--cpu-root <immutable snapshot> is required'); const cpuArg = path.resolve(argv[ci + 1]); const stat = fs.lstatSync(cpuArg); if (!stat.isDirectory() || stat.isSymbolicLink()) throw Error('--cpu-root must be a non-symlink directory'); const cpuRoot = fs.realpathSync(cpuArg); const live = process.env.NOISEMAKER_FOR_CPU && fs.existsSync(process.env.NOISEMAKER_FOR_CPU) ? fs.realpathSync(process.env.NOISEMAKER_FOR_CPU) : null; if ((live && (beneath(live, cpuRoot) || beneath(cpuRoot, live))) || beneath(cppRoot, cpuRoot)) throw Error('authority must be an external immutable snapshot')
const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{ canonicalAdapterFactories, kernelFactories }, { createCanonicalBindings }, { bindGlslKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/csl/glsl-runtime.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js')])
if (UPSTREAM_REVISION !== upstream) throw Error(`upstream revision mismatch: expected ${upstream}, got ${UPSTREAM_REVISION}`)
const actualClosure = closure(cpuRoot); if (sha(JSON.stringify(actualClosure)) !== importClosureShaExpected || JSON.stringify(actualClosure) !== JSON.stringify(importClosureExpected)) throw Error('authority import closure mismatch')
validateAdversarialWitness()
if (process.version !== 'v24.7.0') throw Error('Fractal authority Node drift')
const canonical = canonicalAdapterFactories[key]; const publicFactory = kernelFactories.get(key); if (typeof canonical !== 'function' || publicFactory !== canonical) throw Error('canonical/public adapter identity drift')
const factoryText = Function.prototype.toString.call(canonical); if (sha(factoryText) !== factoryShaExpected) throw Error('factory text provenance drift')
const factorySourceText = fs.readFileSync(path.join(cpuRoot, factorySourceRelative), 'utf8')
const sourcePath = path.join(cppRoot, sourceRelative); const sourceBytes = fs.readFileSync(sourcePath); if (sha(sourceBytes) !== sourceShaExpected) throw Error('corpus source provenance drift')
const defaults = { time: 0, resolution: [8, 6], tileOffset: [0, 0], fullResolution: [8, 6], type: 0, symmetry: 0, offsetX: 0, offsetY: 0, centerX: 0, centerY: 0, zoomAmt: 20, speed: 25, rotation: 0, iterations: 24, mode: 0, colorMode: 0, paletteMode: 0, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0, 0.33, 0.67], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1, hueRange: 100, levels: 0, bgColor: [0.02, 0.03, 0.04], bgAlpha: 73, cutoff: 3 }
function render(factory, def) { const width = def.width; const height = def.height; const uniforms = {}; for (const name of bindingNames) { if (name === 'resolution' || name === 'tileOffset' || name === 'fullResolution') continue; const value = def.uniforms[name]; uniforms[name] = Array.isArray(value) ? new Float32Array(value.map(f)) : (typeof value === 'number' && !Number.isInteger(value) ? f(value) : value) } const bindings = createCanonicalBindings({ width, height, time: def.time, tileOffset: new Float32Array(def.tileOffset.map(f)), fullResolution: new Float32Array(def.fullResolution.map(f)), uniforms }); const output = new Surface(width, height); runPass({ kernel: bindGlslKernel(factory, bindings), destination: output, time: def.time, seed: def.seed ?? 1, tileRows: 1 }); return output }
const cases = [
  { name: 'julia-grayscale', width: 8, height: 6, seed: 11, time: 0.17, tileOffset: [0, 0], fullResolution: [8, 6], uniforms: { ...defaults, type: 0, colorMode: 0, iterations: 24, zoomAmt: 8 } },
  { name: 'newton-hsv-tile', width: 7, height: 5, seed: 12, time: 0.43, tileOffset: [3, 2], fullResolution: [14, 10], uniforms: { ...defaults, type: 1, colorMode: 6, hueRange: 83, rotation: 37, iterations: 19, zoomAmt: 31 } },
  { name: 'mandelbrot-palette', width: 9, height: 7, seed: 13, time: -0.29, tileOffset: [-2, 4], fullResolution: [18, 14], uniforms: { ...defaults, type: 2, colorMode: 4, paletteMode: 0, repeatPalette: 1.8, rotatePalette: 17, iterations: 31, zoomAmt: 47 } },
  { name: 'julia-hsv', width: 6, height: 8, seed: 14, time: 0.91, tileOffset: [1, -3], fullResolution: [12, 16], uniforms: { ...defaults, type: 0, colorMode: 6, hueRange: 137, cyclePalette: 1, levels: 3, iterations: 27, cutoff: 1 } },
  { name: 'newton-oklab-palette', width: 8, height: 5, seed: 15, time: 1.2, tileOffset: [0, 0], fullResolution: [8, 5], uniforms: { ...defaults, type: 1, colorMode: 4, paletteMode: 2, paletteOffset: [0.62, 0.43, 0.38], paletteAmp: [0.31, 0.46, 0.29], paletteFreq: [1.1, 1.7, 0.8], palettePhase: [0.1, 0.2, 0.3], iterations: 22, mode: 1 } },
  { name: 'background-escape', width: 5, height: 4, seed: 16, time: 0.05, tileOffset: [0, 0], fullResolution: [5, 4], uniforms: { ...defaults, type: 2, colorMode: 4, bgColor: [0.77, 0.21, 0.09], bgAlpha: 41, zoomAmt: 0, iterations: 4 } },
  { name: 'julia-distance-mode1', width: 7, height: 5, seed: 17, time: -0.37, tileOffset: [2, -1], fullResolution: [13, 11], uniforms: { ...defaults, type: 0, mode: 1, colorMode: 0, iterations: 23, zoomAmt: 19, speed: 61, rotation: 17, centerX: 12.345, centerY: -23.456, cutoff: 0 } },
  { name: 'mandelbrot-distance-mode1', width: 8, height: 6, seed: 18, time: 0.62, tileOffset: [-3, 2], fullResolution: [17, 13], uniforms: { ...defaults, type: 2, mode: 1, colorMode: 0, iterations: 29, zoomAmt: 63, speed: 41, rotation: -29, centerX: -17.25, centerY: 8.75, cutoff: 0 } },
  { name: 'julia-near-escape-nonrepresentable', width: 9, height: 5, seed: 19, time: 0.125, tileOffset: [3, -2], fullResolution: [17, 13], uniforms: { ...defaults, type: 0, mode: 1, colorMode: 0, iterations: 3, zoomAmt: 49, speed: 0, rotation: 0, centerX: -25, centerY: 67, cutoff: 0 } },
].map(def => ({ ...def, uniforms: { ...def.uniforms, resolution: def.uniforms.resolution ?? [def.width, def.height], tileOffset: def.tileOffset, fullResolution: def.fullResolution } }))
const rendered = cases.map(def => { const direct = render(canonical, def); const pub = render(publicFactory, def); const parity = strictCompare(direct, pub); if (!parity.exact) throw Error(`${def.name}: public/direct mismatch`); const repeat = render(canonical, def); const wordsRecordDirect = wordsRecord(direct); return { ...def, expected: wordsRecordDirect, public_expected: wordsRecord(pub), public_direct_exact: true, repeat_exact: strictCompare(direct, repeat).exact, output_storage_distinct: direct !== repeat, output_data_distinct: direct.data !== repeat.data, bindings: def.uniforms } })
const adversarialRendered = rendered.find(caseDef => caseDef.name === adversarialWitness.case); if (!adversarialRendered || adversarialRendered.width !== 9 || adversarialRendered.height !== 5 || adversarialRendered.uniforms.type !== 0 || adversarialRendered.uniforms.mode !== 1 || adversarialRendered.tileOffset[0] !== 3 || adversarialRendered.tileOffset[1] !== -2 || adversarialRendered.fullResolution[0] !== 17 || adversarialRendered.fullResolution[1] !== 13) throw Error('adversarial witness controls drift'); if (adversarialRendered.expected.f32_words_le[adversarialWitness.lane_index] !== adversarialWitness.expected_f32_word || adversarialRendered.expected.rgba8_bytes[adversarialWitness.lane_index] !== adversarialWitness.expected_rgba8_byte) throw Error('adversarial witness output drift')
const mutations = [
  { name: 'julia-arm-to-newton', anchor: 'if ($bindings.type === 0) distance = julia', replacement: 'if ($bindings.type === 0) distance = newton', witnesses: ['julia-grayscale', 'julia-hsv'] },
  { name: 'newton-arm-to-mandelbrot', anchor: 'else if ($bindings.type === 1) distance = newton', replacement: 'else if ($bindings.type === 1) distance = mandelbrot', witnesses: ['newton-hsv-tile', 'newton-oklab-palette'] },
  { name: 'palette-repeat-half', anchor: 'distance * $bindings.repeatPalette', replacement: 'distance * ($bindings.repeatPalette * 0.5)', witnesses: ['mandelbrot-palette', 'newton-oklab-palette'] },
  { name: 'background-alpha-scale', anchor: '$bindings.bgAlpha * 0.01', replacement: '$bindings.bgAlpha * 0.02', witnesses: ['background-escape'] },
  { name: 'hsv-hue-range-half', anchor: '$bindings.hueRange * 0.01', replacement: '$bindings.hueRange * 0.005', witnesses: ['newton-hsv-tile', 'julia-hsv'] },
].map(async def => { const text = mutate(factorySourceText, def.anchor, def.replacement); const module = await import(`data:text/javascript;base64,${Buffer.from(text).toString('base64')}`); const mutant = module.fractalFactory; const results = def.witnesses.map(name => { const spec = cases.find(x => x.name === name); const ref = render(canonical, spec); const cand = render(mutant, spec); const result = strictCompare(ref, cand); if (!result.changed_float32_lanes || !result.changed_rgba8_bytes) throw Error(`${def.name}/${name}: no pixel witness`); return { case: name, ...result } }); return { name: def.name, anchor: def.anchor, replacement: def.replacement, anchor_sha256: sha(def.anchor), replacement_sha256: sha(def.replacement), mutated_factory_sha256: sha(text), independent: true, witness_cases: def.witnesses, results } })
const resolvedMutations = await Promise.all(mutations)
const comparer = controls(); if (!Object.values(comparer.cases).every(Boolean)) throw Error('comparer self-tests failed')
const sourceUniformAbi = Object.fromEntries(bindingNames.map(name => {
  const kind = runtimeBindingAbi[name]
  return [name, ({ number: 'float', int32: 'int', Vec2: 'vec2', Vec3: 'vec3' }[kind] ?? kind)]
}))
const document = { schema, schema_version: 1, program_key: key, effect_key: effect, corpus_revision: corpus, upstream_revision: UPSTREAM_REVISION, factory: { name: canonical.name, text_sha256: factoryShaExpected, public_factory_is_canonical_identity: publicFactory === canonical, adapter_own_key: true }, runtime_binding_names: bindingNames, runtime_binding_abi: runtimeBindingAbi, source_uniform_abi: sourceUniformAbi, provenance: { source: { relative_path: sourceRelative, bytes: sourceBytes.length, sha256: sha(sourceBytes) }, factory_source: { relative_path: factorySourceRelative, sha256: sha(factorySourceText) }, cpu_snapshot: { root_realpath: authorityRootProvenance, import_closure_sha256: importClosureShaExpected, immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, import_closure: actualClosure } }, comparer_self_tests: comparer, render_cases: rendered, adversarial_witness: adversarialWitness, mutation_anchor_cardinality: { total: resolvedMutations.length, anchors: Object.fromEntries(resolvedMutations.map(x => [x.name, 1])) }, mutation_ledger: resolvedMutations, claim_boundaries: { canonical_factory_only: true, typed_slice_landing: false, shared_emitter_modified: false, frontend_blocker: 'counted-loop-proof', first_blocker_span: 'julia:261:5-269:6' } }
const json = Buffer.from(`${JSON.stringify(document, null, 2)}\n`); const md = Buffer.from(`# Fractal pixel-parity oracle\n\nFrozen Node ${process.version} canonical-adapter oracle for **${key}**. It covers Julia, Newton, Mandelbrot, both Julia/Mandelbrot distance (mode=1) paths, adversarial near-escape and nonrepresentable tiled coordinates, grayscale, HSV, RGB palette, Oklab palette, cycling/levels, escaped-background alpha, exact Float32 words, RGBA8 bytes, public/direct identity, repeat storage, and five independent canonical-factory mutation witnesses. The typed landing remains intentionally outside this package; the prepared frontend profile records the first counted-loop blocker at julia 261:5-269:6.\n`)
function sidecar(file, payload) { fs.writeFileSync(`${file}.sha256`, `${sha(payload)}  ${path.basename(file)}\n`) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(outPath, json); sidecar(outPath, json); fs.writeFileSync(reportPath, md); sidecar(reportPath, md); console.log(`${rendered.length} cases, ${mutations.length} mutations written`) } else { if (!fs.existsSync(outPath) || !same([...fs.readFileSync(outPath)], [...json])) throw Error('fractal oracle drift'); if (!fs.existsSync(reportPath) || !same([...fs.readFileSync(reportPath)], [...md])) throw Error('fractal report drift'); console.log(mode === '--self-test' ? 'strict comparer, provenance, public/direct parity, and mutation witnesses verified' : 'fractal oracle check passed') }
