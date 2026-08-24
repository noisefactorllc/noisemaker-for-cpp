#!/usr/bin/env node
// Frozen-authority Median oracle. This file deliberately does not import or
// modify the shared C++ typed-slice generator.
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../../..')
const out = path.join(here, 'median-oracles.json')
const report = path.join(here, 'median-oracle-report.md')
const key = 'filter/median:median'
const nodeVersion = 'v24.7.0'
const entryFiles = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
const imports = [ /\bfrom\s*["']([^"'\n]+)["']/g, /^[ \t]*import\s+["']([^"'\n]+)["']/gm ]
const dynamic = /\bimport\s*\(([^)]*)\)/g
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const beneath = (a, b) => b === a || b.startsWith(`${a}${path.sep}`)
const real = (rootPath, candidate, label) => { const resolved = fs.realpathSync(candidate); if (!beneath(rootPath, resolved)) throw new Error(`${label}: import escapes immutable snapshot`); return resolved }
function closure(cpuRoot) {
  const stack = entryFiles.map(item => real(cpuRoot, path.join(cpuRoot, item), 'entry')); const seen = new Map()
  const enqueue = (specifier, file) => { if (specifier.startsWith('node:')) return; if (!specifier.startsWith('./') && !specifier.startsWith('../')) throw new Error(`bare module specifier ${specifier}`); stack.push(real(cpuRoot, path.resolve(path.dirname(file), specifier), path.relative(cpuRoot, file))) }
  while (stack.length) { const file = stack.pop(); if (seen.has(file)) continue; const text = fs.readFileSync(file, 'utf8'); seen.set(file, sha(Buffer.from(text))); dynamic.lastIndex = 0; let m; while ((m = dynamic.exec(text))) { const literal = m[1].trim(); if (!/^(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')$/.test(literal)) throw new Error(`nonliteral dynamic import in ${path.relative(cpuRoot, file)}`); enqueue(literal.slice(1, -1), file) } for (const re of imports) { re.lastIndex = 0; while ((m = re.exec(text))) enqueue(m[1], file) } }
  return [...seen.entries()].map(([file, digest]) => ({ relative_path: path.relative(cpuRoot, file), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
}
function sidecar(file, bytes) { fs.writeFileSync(`${file}.sha256`, `${sha(bytes)}  ${path.basename(file)}\n`) }
function words(surface) { return new Uint32Array(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength / 4) }
function hex(value) { return `0x${(value >>> 0).toString(16).padStart(8, '0')}` }
function compare(reference, candidate) {
  if (reference.width !== candidate.width || reference.height !== candidate.height) return { exact: false, dimensions_match: false, lane_count_match: false, mismatched_lanes: 0, mismatched_bytes: 0, first_mismatch: null, first_rgba8_mismatch: null }
  const left = words(reference), right = words(candidate); let lanes = Math.abs(left.length - right.length); let first = null
  for (let i = 0; i < Math.min(left.length, right.length); i++) if (left[i] !== right[i]) { lanes++; if (!first) first = { lane_index: i, reference: hex(left[i]), candidate: hex(right[i]) } }
  const lb = new Uint8Array(reference.toRgba8()), rb = new Uint8Array(candidate.toRgba8()); let bytes = Math.abs(lb.length - rb.length); let firstByte = null
  for (let i = 0; i < Math.min(lb.length, rb.length); i++) if (lb[i] !== rb[i]) { bytes++; if (!firstByte) firstByte = { byte_index: i, reference: lb[i], candidate: rb[i] } }
  return { exact: lanes === 0 && bytes === 0 && left.length === right.length && lb.length === rb.length, dimensions_match: true, lane_count_match: left.length === right.length, mismatched_lanes: lanes, mismatched_bytes: bytes, first_mismatch: first, first_rgba8_mismatch: firstByte }
}
function fake(w, h, f32, rgba) { return { width: w, height: h, get data() { return new Float32Array(new Uint32Array(f32).buffer) }, toRgba8: () => Uint8Array.from(rgba) } }
function comparerSelfTests() {
  const equal = compare(fake(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]), fake(1, 1, [0x3f800000, 0, 0, 0x3f800000], [255, 0, 0, 255]))
  const dimensions = compare({ width: 1, height: 1, get data() { throw new Error('accessed lanes before dimensions') } }, { width: 2, height: 1, get data() { throw new Error('accessed lanes before dimensions') } })
  const short = compare(fake(1, 1, [0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]))
  const rgba = compare(fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0, 0, 0, 0], [1, 0, 0, 0]))
  const zero = compare(fake(1, 1, [0, 0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0x80000000, 0, 0, 0], [0, 0, 0, 0]))
  const nan = compare(fake(1, 1, [0x7fc00001, 0, 0, 0], [0, 0, 0, 0]), fake(1, 1, [0x7fc00002, 0, 0, 0], [0, 0, 0, 0]))
  return { good_equal: equal.exact, dimensions_mismatch: !dimensions.dimensions_match, short_lane_count: !short.lane_count_match, rgba8_mismatch: rgba.mismatched_bytes > 0, signed_zero: zero.mismatched_lanes > 0, nan_payload: nan.mismatched_lanes > 0 }
}
function input(def) { const data = new Float32Array(def.width * def.height * 4); for (let i = 0; i < data.length; i += 4) { const p = i / 4; const x = p % def.width; const y = Math.floor(p / def.width); data[i] = Math.fround(((x * 17 + y * 11 + def.phase) % 23) / 22); data[i + 1] = Math.fround(((x * 7 + y * 19 + def.phase * 2) % 29) / 28); data[i + 2] = Math.fround(((x * 13 + y * 5 + def.phase * 3) % 31) / 30); data[i + 3] = Math.fround(.15 + ((x + y + def.phase) % 8) / 10) } return data }
function surface(def, Surface) { return new Surface(def.width, def.height, input(def)) }
function render(factory, def, createBindings, bind, runPass, Surface) { const source = surface(def, Surface); const before = new Uint32Array(words(source)); const destination = new Surface(def.width, def.height); const bindings = createBindings({ width: def.width, height: def.height, time: Math.fround(def.time), uniforms: { threshold: Math.fround(def.threshold), RADIUS: def.radius }, textures: { inputTex: source }, tileOffset: new Float32Array(def.tileOffset.map(Math.fround)), fullResolution: new Float32Array(def.fullResolution.map(Math.fround)) }); const kernel = bind(factory, bindings); runPass({ kernel, destination, time: def.time, seed: def.phase }); const after = words(source); if (before.some((value, index) => value !== after[index])) throw new Error(`${def.name}: input mutated`); return { output: destination, input: source } }
function surfaceRecord(value) { const data = new Uint8Array(value.data.buffer, value.data.byteOffset, value.data.byteLength); const rgba = new Uint8Array(value.toRgba8()); return { f32_words_le: Array.from(words(value), hex), f32_sha256: sha(Buffer.from(data)), rgba8_bytes: Array.from(rgba), rgba8_sha256: sha(Buffer.from(rgba)) } }
async function mutatedFactory(canonicalText, mutation) { if (canonicalText.split(mutation.anchor).length - 1 !== 1) throw new Error(`mutation anchor cardinality: ${mutation.name}`); const text = canonicalText.replace(mutation.anchor, mutation.replacement); const encoded = Buffer.from(`export const factory = ${text}\n`).toString('base64'); return (await import(`data:text/javascript;base64,${encoded}#${sha(text)}`)).factory }

const args = process.argv.slice(2); const mode = args.find(token => ['--write', '--check', '--self-test'].includes(token)); if (!mode || args.filter(token => ['--write', '--check', '--self-test'].includes(token)).length !== 1) throw new Error('choose exactly one mode')
const cpuIndex = args.indexOf('--cpu-root'); if (cpuIndex < 0) throw new Error('--cpu-root <immutable snapshot> is required'); const cpuArg = args[cpuIndex + 1]; if (!cpuArg || fs.lstatSync(cpuArg).isSymbolicLink()) throw new Error('--cpu-root must not be a symlink'); const cpuRoot = fs.realpathSync(cpuArg); const live = fs.realpathSync(process.env.NOISEMAKER_FOR_CPU ?? path.join(process.env.HOME ?? '', 'platform/noisemaker-for-cpu')); if (beneath(live, cpuRoot) || beneath(cpuRoot, live) || beneath(fs.realpathSync(root), cpuRoot)) throw new Error('authority must be immutable external snapshot')
const load = relative => import(pathToFileURL(real(cpuRoot, path.join(cpuRoot, relative), 'load')).href)
const [{ canonicalKernelFactories, kernelFactories }, { createCanonicalBindings }, { bindGlslKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/csl/glsl-runtime.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js')])
if (process.version !== nodeVersion) throw new Error('Median authority Node drift')
const canonical = canonicalKernelFactories[key]; const publicFactory = kernelFactories.get(key); if (typeof canonical !== 'function' || typeof publicFactory !== 'function') throw new Error('Median factory missing')
const canonicalText = Function.prototype.toString.call(canonical); const sourcePath = path.join(cpuRoot, 'src/effects/generated/canonical-kernels.js'); const sourceBytes = fs.readFileSync(sourcePath)
const cases = [
  { name: 'radius1-threshold-zero', radius: 1, width: 4, height: 3, threshold: 0, phase: 1, time: 0, tileOffset: [0, 0], fullResolution: [4, 3] },
  { name: 'radius1-threshold-high', radius: 1, width: 5, height: 4, threshold: 95, phase: 2, time: .2, tileOffset: [1, 2], fullResolution: [20, 16] },
  { name: 'radius2-edge', radius: 2, width: 3, height: 3, threshold: 10, phase: 3, time: .1, tileOffset: [2, 1], fullResolution: [12, 12] },
  { name: 'radius2-middle', radius: 2, width: 6, height: 5, threshold: 50, phase: 4, time: .4, tileOffset: [3, 2], fullResolution: [24, 20] },
  { name: 'radius2-preserve', radius: 2, width: 7, height: 4, threshold: 100, phase: 5, time: .2, tileOffset: [4, 3], fullResolution: [32, 24] },
  { name: 'radius3-edge', radius: 3, width: 4, height: 4, threshold: 1, phase: 6, time: .63, tileOffset: [2, 3], fullResolution: [16, 16] },
  { name: 'radius3-middle', radius: 3, width: 8, height: 5, threshold: 25, phase: 7, time: .77, tileOffset: [5, 1], fullResolution: [64, 40] },
  { name: 'radius3-preserve', radius: 3, width: 9, height: 6, threshold: 100, phase: 8, time: 1.1, tileOffset: [9, 6], fullResolution: [72, 48] },
  { name: 'radius3-large', radius: 3, width: 11, height: 7, threshold: 0, phase: 9, time: -.25, tileOffset: [0, 4], fullResolution: [88, 56] },
]
const comparer = comparerSelfTests(); if (!Object.values(comparer).every(Boolean)) throw new Error('strict comparer self-tests failed')
const cpuClosure = closure(cpuRoot); const renderCases = []
for (const def of cases) { const direct = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const pub = render(publicFactory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const parity = compare(direct.output, pub.output); if (!parity.exact) throw new Error(`${def.name}: public/direct mismatch ${JSON.stringify(parity)}`); const repeat = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const source = surfaceRecord(direct.input); renderCases.push({ name: def.name, width: def.width, height: def.height, radius: def.radius, threshold: def.threshold, time: def.time, tileOffset: def.tileOffset, fullResolution: def.fullResolution, input: source, expected: surfaceRecord(direct.output), public_expected: surfaceRecord(pub.output), repeat: { exact: compare(direct.output, repeat.output).exact, output_object_distinct: direct.output !== repeat.output, output_data_distinct: direct.output.data !== repeat.output.data }, input_immutable_exact_bits: true, public_direct_exact: parity.exact }) }
const mutationDefs = [
  { name: 'median-index', anchor: 'var medianIndex = (activeCount - 1) >> 1', replacement: 'var medianIndex = (activeCount + 1) >> 1', witnesses: ['radius1-threshold-zero', 'radius2-middle'] },
  { name: 'center-alpha', anchor: 'centerAlpha = sampleColor[3]', replacement: 'centerAlpha = 0', witnesses: ['radius1-threshold-high', 'radius2-preserve'] },
  { name: 'clamp-upper-edge', anchor: 'dimensions, cpu_ivec2(1)', replacement: 'dimensions, cpu_ivec2(2)', witnesses: ['radius2-edge', 'radius3-edge'] },
  { name: 'center-alpha-offset', anchor: 'centerAlpha = sampleColor[3]', replacement: 'centerAlpha = sampleColor[3] + 0.1', witnesses: ['radius3-middle'] },
]
const mutationLedger = []
for (const mutation of mutationDefs) { const factory = await mutatedFactory(canonicalText, mutation); const results = mutation.witnesses.map(name => { const def = cases.find(item => item.name === name); const reference = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface).output; const candidate = render(factory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface).output; const result = compare(reference, candidate); if (result.exact || result.mismatched_lanes === 0 || result.mismatched_bytes === 0) throw new Error(`${mutation.name}/${name}: non-witness`); return { case: name, mismatched_lanes: result.mismatched_lanes, mismatched_bytes: result.mismatched_bytes, first_mismatch: result.first_mismatch, first_rgba8_mismatch: result.first_rgba8_mismatch } }); mutationLedger.push({ name: mutation.name, source_anchor: mutation.anchor, replacement: mutation.replacement, anchor_sha256: sha(mutation.anchor), replacement_sha256: sha(mutation.replacement), mutated_factory_sha256: sha(Function.prototype.toString.call(factory)), required_witnesses: mutation.witnesses, required_witness_results: results, independent: true }) }
const document = { schema: 'noisemaker-for-cpp.median.pixel-parity.v1', program_key: key, provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source: { relative_path: 'src/effects/generated/canonical-kernels.js', bytes: sourceBytes.length, sha256: sha(sourceBytes) }, factory: { name: canonical.name, text_bytes: Buffer.byteLength(canonicalText), text_sha256: sha(canonicalText), public_factory_name: publicFactory.name, public_factory_is_canonical_identity: publicFactory === canonical }, cpu_snapshot: { import_closure: cpuClosure, closure_cardinality: cpuClosure.length, immutable_snapshot: true, live_checkout_rejected: true, realpath_containment_checked: true, symlink_escape_rejected: true } }, runtime_binding_abi: { inputTex: 'sampler2D', threshold: 'float', RADIUS: 'int32', tileOffset: 'Vec2', fullResolution: 'Vec2' }, render_cases: renderCases, comparer_self_tests: comparer, mutation_ledger: mutationLedger, claim_boundaries: { typed_slice_landing: false, shared_emitter_modified: false, pixel_parity_authority: 'canonicalFactory80 and medianFactory' } }
const json = Buffer.from(`${JSON.stringify(document, null, 2)}\n`); const md = Buffer.from(`# Median pixel-parity oracle\n\nFrozen Node ${process.version} authority for filter/median:median. The package covers radii 1, 2, and 3, exact Float32 words, RGBA8 bytes, public/direct identity, repeat storage, input immutability, and four source mutation witnesses. The typed-slice integration remains prepared-only because the shared emitter currently rejects the counted-for program proof at 47:5.\n`); if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(out, json); sidecar(out, json); fs.writeFileSync(report, md); sidecar(report, md); console.log(`${renderCases.length} cases, ${mutationLedger.length} mutations written`) } else { if (!fs.existsSync(out) || fs.readFileSync(out, 'utf8') !== json.toString()) throw new Error('median oracle drift'); if (!fs.existsSync(report) || fs.readFileSync(report, 'utf8') !== md.toString()) throw new Error('median report drift'); if (mode === '--self-test') console.log('strict comparer self-tests, closure, public/direct parity, and mutation witnesses verified'); else console.log('median oracle check passed') }
