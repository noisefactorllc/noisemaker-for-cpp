#!/usr/bin/env node
// Authenticated Texture pixel oracle. It executes only the canonical factory
// from the caller-supplied immutable CPU snapshot; no C++ implementation is
// imported or consulted.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const out = path.join(here, 'texture-oracles.json')
const report = path.join(here, 'texture-oracle-report.md')
const key = 'filter/texture:texture'
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/texture/texture.glsl'
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const f = value => Math.fround(value)
const words = surface => Array.from(new Uint32Array(surface.data.buffer, surface.data.byteOffset, surface.data.byteLength / 4), x => `0x${(x >>> 0).toString(16).padStart(8, '0')}`)
const rgba = surface => Array.from(surface.toRgba8())
const digestWords = ws => sha(Buffer.from(ws.map(x => Number.parseInt(x, 16)).flatMap(x => [x & 255, (x >>> 8) & 255, (x >>> 16) & 255, x >>> 24])))
const digestBytes = bytes => sha(Buffer.from(bytes))
const beneath = (a, b) => b === a || b.startsWith(`${a}${path.sep}`)
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i])
const countDiff = (a, b) => a.reduce((n, x, i) => n + (x !== b[i] ? 1 : 0), 0)
function closure(root) {
  const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js']
  const stack = entries.map(x => fs.realpathSync(path.join(root, x))); const seen = new Map()
  const imports = /(?:\bfrom\s*|\bimport\s*)['"]([^'"]+)['"]/g
  while (stack.length) {
    const file = stack.pop(); if (seen.has(file)) continue
    const text = fs.readFileSync(file); seen.set(file, sha(text)); imports.lastIndex = 0
    let match; while ((match = imports.exec(text.toString())) !== null) {
      const spec = match[1]; if (spec.startsWith('node:')) continue
      if (!spec.startsWith('./') && !spec.startsWith('../')) throw new Error(`bare import ${spec}`)
      const resolved = fs.realpathSync(path.resolve(path.dirname(file), spec)); if (!beneath(root, resolved)) throw new Error('import escaped snapshot'); stack.push(resolved)
    }
  }
  return [...seen].map(([file, digest]) => ({ relative_path: path.relative(root, file).split(path.sep).join('/'), sha256: digest })).sort((a, b) => a.relative_path.localeCompare(b.relative_path))
}
function surfaceRecord(surface) { const ws = words(surface); const rb = rgba(surface); return { f32_words_le: ws, f32_sha256: digestWords(ws), rgba8_bytes: rb, rgba8_sha256: digestBytes(rb) } }
function input(def, Surface) { const s = new Surface(def.width, def.height); for (let y = 0; y < def.height; y++) for (let x = 0; x < def.width; x++) { const i = (y * def.width + x) * 4; s.data[i] = f(((x * 17 + y * 11 + def.phase) % 29) / 28); s.data[i + 1] = f(((x * 7 + y * 19 + def.phase * 2) % 31) / 30); s.data[i + 2] = f(((x * 13 + y * 5 + def.phase * 3) % 37) / 36); s.data[i + 3] = f(0.2 + ((x + y + def.phase) % 8) / 10) } return s }
function render(factory, def, createBindings, bind, runPass, Surface) {
  const source = input(def, Surface); const before = words(source); const uniforms = { time: f(def.time), alpha: f(def.alpha), scale: f(def.scale), intensity: f(def.intensity), contrast: f(def.contrast), mono: def.mono }
  const bindings = createBindings({ width: def.width, height: def.height, time: def.time, uniforms, textures: { inputTex: source }, tileOffset: new Float32Array(def.tileOffset.map(f)), fullResolution: new Float32Array(def.fullResolution.map(f)) })
  const output = new Surface(def.width, def.height); runPass({ kernel: bind(factory, bindings), destination: output, time: def.time, seed: def.phase, tileRows: 1 })
  if (!same(before, words(source))) throw new Error(`${def.name}: input mutated`)
  return { input: source, output }
}
function compare(a, b) { if (a.output.width !== b.output.width || a.output.height !== b.output.height) throw new Error('dimensions mismatch before lane access'); const aw = words(a.output), bw = words(b.output), ar = rgba(a.output), br = rgba(b.output); return { exact: same(aw, bw) && same(ar, br), mismatched_lanes: countDiff(aw, bw), mismatched_bytes: countDiff(ar, br), first_mismatch: aw.map((x, i) => x !== bw[i] ? { lane: i, reference: x, candidate: bw[i] } : null).find(Boolean) ?? null } }
function comparerSelfTests() { const ok = { width: 1, height: 1, f32_words_le: ['0x3f800000'], rgba8_bytes: [255] }; let touched = false; const badDim = { width: 2, height: 1, get f32_words_le() { touched = true; return [] }, rgba8_bytes: [] }; const check = (a, b) => { if (a.width !== b.width || a.height !== b.height) throw Error('dimensions'); if (a.f32_words_le.length !== b.f32_words_le.length) throw Error('Float32 count'); if (a.f32_words_le.some((x, i) => x !== b.f32_words_le[i])) throw Error('Float32 first mismatch'); if (a.rgba8_bytes.some((x, i) => x !== b.rgba8_bytes[i])) throw Error('RGBA8 first mismatch') }
  const probe = (fn) => { try { fn(); return false } catch { return true } }; return { good_equal: !probe(() => check(ok, { ...ok, f32_words_le: [...ok.f32_words_le], rgba8_bytes: [...ok.rgba8_bytes] })), dimensions_mismatch: probe(() => check(ok, badDim)) && !touched, short_lane_count: probe(() => check(ok, { ...ok, f32_words_le: [] })), rgba8_mismatch: probe(() => check(ok, { ...ok, rgba8_bytes: [0] })), signed_zero: probe(() => check(ok, { ...ok, f32_words_le: ['0x80000000'] })), nan_payload: probe(() => check(ok, { ...ok, f32_words_le: ['0x7fc00001'] })) }
}
function mutate(text, def) { if (text.split(def.anchor).length - 1 !== 1) throw new Error(`${def.name}: anchor cardinality`); const source = text.replace(def.anchor, def.replacement); return { source, factory: eval(`(${source})`) } }
const args = process.argv.slice(2); const mode = args.find(x => ['--write', '--check', '--self-test'].includes(x)); if (!mode || args.filter(x => ['--write', '--check', '--self-test'].includes(x)).length !== 1) throw Error('choose exactly one mode')
const ci = args.indexOf('--cpu-root'); if (ci < 0 || !args[ci + 1]) throw Error('--cpu-root <immutable snapshot> is required'); const cpuArg = path.resolve(args[ci + 1]); const stat = fs.lstatSync(cpuArg); if (!stat.isDirectory() || stat.isSymbolicLink()) throw Error('--cpu-root must be a non-symlink directory'); const cpuRoot = fs.realpathSync(cpuArg); const live = process.env.NOISEMAKER_FOR_CPU ? fs.realpathSync(process.env.NOISEMAKER_FOR_CPU) : null; if ((live && (beneath(live, cpuRoot) || beneath(cpuRoot, live))) || beneath(cppRoot, cpuRoot)) throw Error('authority must be an external immutable snapshot')
const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{ canonicalKernelFactories, kernelFactories }, { createCanonicalBindings }, { bindGlslKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/csl/glsl-runtime.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js')])
if (process.version !== 'v24.7.0') throw Error('Texture authority Node drift')
const canonical = canonicalKernelFactories[key]; const publicFactory = kernelFactories.get(key); if (typeof canonical !== 'function' || typeof publicFactory !== 'function' || publicFactory !== canonical) throw Error('Texture canonical/public factory identity drift')
const factoryText = Function.prototype.toString.call(canonical); const sourcePath = path.join(cppRoot, sourceRelative); const sourceBytes = fs.readFileSync(sourcePath)
const cases = [
  { name: 'paper-alpha-zero', width: 3, height: 3, phase: 1, time: 0, alpha: 0, scale: 1, intensity: 50, contrast: 50, mono: false, tileOffset: [0, 0], fullResolution: [3, 3] },
  { name: 'paper-center', width: 4, height: 3, phase: 2, time: .25, alpha: 1, scale: 1.2, intensity: 65, contrast: 35, mono: false, tileOffset: [1, 2], fullResolution: [16, 12] },
  { name: 'paper-mono', width: 5, height: 4, phase: 3, time: .73, alpha: .625, scale: 2.4, intensity: 90, contrast: 75, mono: true, tileOffset: [3, 1], fullResolution: [20, 16] },
  { name: 'paper-low-contrast', width: 6, height: 5, phase: 4, time: -.2, alpha: .4, scale: .35, intensity: 25, contrast: 10, mono: false, tileOffset: [2, 4], fullResolution: [24, 20] },
  { name: 'paper-high-contrast', width: 7, height: 4, phase: 5, time: 1.1, alpha: 1, scale: 4, intensity: 120, contrast: 100, mono: false, tileOffset: [7, 0], fullResolution: [28, 16] },
  { name: 'paper-wide-tile', width: 8, height: 3, phase: 6, time: .41, alpha: .8, scale: 1.8, intensity: 55, contrast: 55, mono: false, tileOffset: [-2, 5], fullResolution: [32, 12] },
  { name: 'paper-tall-tile', width: 3, height: 8, phase: 7, time: .91, alpha: .2, scale: .8, intensity: 75, contrast: 90, mono: true, tileOffset: [4, -1], fullResolution: [12, 32] },
  { name: 'paper-large', width: 9, height: 7, phase: 8, time: 2.2, alpha: .9, scale: 2.75, intensity: 45, contrast: 62, mono: false, tileOffset: [9, 7], fullResolution: [36, 28] },
]
const comparer = comparerSelfTests(); if (!Object.values(comparer).every(Boolean)) throw Error('strict comparer self-tests failed')
const rendered = cases.map(def => { const direct = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const pub = render(publicFactory, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); const parity = compare(direct, pub); if (!parity.exact) throw Error(`${def.name}: public/direct mismatch`); const repeat = render(canonical, def, createCanonicalBindings, bindGlslKernel, runPass, Surface); return { ...def, input: surfaceRecord(direct.input), expected: surfaceRecord(direct.output), public_expected: surfaceRecord(pub.output), input_immutable_exact_bits: true, public_direct_exact: true, repeat: { exact: compare(direct, repeat).exact, output_object_distinct: direct.output !== repeat.output, output_data_distinct: direct.output.data !== repeat.output.data } } })
const mutationDefs = [
  { name: 'paper-frequency', anchor: 'var freq_scale = 24', replacement: 'var freq_scale = 12', witnesses: ['paper-center', 'paper-wide-tile'] },
  { name: 'paper-gain', anchor: 'var gain = SHADE_GAIN * 0.25', replacement: 'var gain = SHADE_GAIN * 0.5', witnesses: ['paper-mono', 'paper-large'] },
  { name: 'highlight-gain', anchor: 'shade_base * shade_base) * 1.25', replacement: 'shade_base * shade_base) * 0.25', witnesses: ['paper-center', 'paper-high-contrast'] },
  { name: 'alpha-blend', anchor: 'scaled_rgb, a)', replacement: 'scaled_rgb, 0)', witnesses: ['paper-center', 'paper-high-contrast'] },
]
const mutations = mutationDefs.map(def => { const mutant = mutate(factoryText, def); const results = def.witnesses.map(name => { const spec = cases.find(x => x.name === name); const ref = render(canonical, spec, createCanonicalBindings, bindGlslKernel, runPass, Surface); const cand = render(mutant.factory, spec, createCanonicalBindings, bindGlslKernel, runPass, Surface); const rw = words(ref.output), cw = words(cand.output), rr = rgba(ref.output), cr = rgba(cand.output); const result = { case: name, mismatched_lanes: countDiff(rw, cw), mismatched_bytes: countDiff(rr, cr), first_mismatch: rw.map((x, i) => x !== cw[i] ? { lane: i, reference: x, candidate: cw[i] } : null).find(Boolean) }; if (!result.mismatched_lanes || !result.mismatched_bytes) throw Error(`${def.name}/${name}: no witness`); return result }); return { name: def.name, source_anchor: def.anchor, replacement: def.replacement, anchor_sha256: sha(def.anchor), replacement_sha256: sha(def.replacement), mutated_factory_sha256: sha(mutant.source), required_witnesses: def.witnesses, required_witness_results: results, independent: true } })
const frozenClosure = closure(cpuRoot)
const document = { schema: 'noisemaker-for-cpp.texture.pixel-parity.v1', program_key: key, provenance: { authority_node: process.version, upstream_revision: UPSTREAM_REVISION, source: { relative_path: sourceRelative, bytes: sourceBytes.length, sha256: sha(sourceBytes) }, factory: { name: canonical.name, text_bytes: Buffer.byteLength(factoryText), text_sha256: sha(factoryText), public_factory_is_canonical_identity: publicFactory === canonical }, cpu_snapshot: { import_closure: frozenClosure, closure_cardinality: frozenClosure.length, immutable_snapshot: true, live_checkout_rejected: true, realpath_containment_checked: true, symlink_escape_rejected: true } }, runtime_binding_abi: { inputTex: 'sampler2D', time: 'float', alpha: 'float', scale: 'float', intensity: 'float', contrast: 'float', mono: 'bool', tileOffset: 'Vec2', fullResolution: 'Vec2', MODE: 'int32' }, render_cases: rendered, comparer_self_tests: comparer, mutation_ledger: mutations, claim_boundaries: { canonical_factory_only: true, typed_slice_landing: false, shared_emitter_modified: false, mode: 3, pixel_parity_authority: 'canonicalFactory161' } }
const json = Buffer.from(`${JSON.stringify(document, null, 2)}\n`); const md = Buffer.from(`# Texture pixel-parity oracle\n\nFrozen Node ${process.version} authority for filter/texture:texture, compile-time MODE=3 (paper). The package covers alpha early-return, material controls, mono/color, tiled dimensions, exact Float32 words, RGBA8 bytes, public/direct identity, input immutability, repeat storage, and four independent canonical-factory mutation witnesses. It is a prepared native oracle; shared C++ integration is intentionally outside this package.\n`)
function sidecar(file, payload) { fs.writeFileSync(`${file}.sha256`, `${sha(payload)}  ${path.basename(file)}\n`) }
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(out, json); sidecar(out, json); fs.writeFileSync(report, md); sidecar(report, md); console.log(`${rendered.length} cases, ${mutations.length} mutations written`) } else { if (!fs.existsSync(out) || !same([...fs.readFileSync(out)], [...json])) throw Error('texture oracle drift'); if (!fs.existsSync(report) || !same([...fs.readFileSync(report)], [...md])) throw Error('texture report drift'); if (mode === '--self-test') console.log('strict comparer, closure, public/direct parity, and mutation witnesses verified'); else console.log('texture oracle check passed') }
