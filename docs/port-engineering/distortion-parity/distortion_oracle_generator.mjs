#!/usr/bin/env node
// Authenticated canonical CPU oracle for mixer/distortion:distortion.
// This package is prepared-only: no C++ output participates in the oracle.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const key = 'mixer/distortion:distortion'
const effect = 'mixer/distortion'
const corpus = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const sourceRelative = `tools/glslcpp/corpus/${corpus}/sources/mixer/distortion/distortion.glsl`
const outPath = path.join(here, 'distortion-oracles.json')
const reportPath = path.join(here, 'distortion-oracle-report.md')
const sha = value => crypto.createHash('sha256').update(value).digest('hex')
const f = Math.fround
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength)
const words = value => Array.from(new Uint32Array(value.buffer, value.byteOffset, value.byteLength / 4), x => `0x${(x >>> 0).toString(16).padStart(8, '0')}`)
const rgba = surface => Array.from(surface.toRgba8())
const equal = (a, b) => a.length === b.length && a.every((x, i) => x === b[i])
const countDiff = (a, b) => a.reduce((n, x, i) => n + (x !== b[i] ? 1 : 0), 0)
const beneath = (a, b) => a === b || b.startsWith(`${a}${path.sep}`)
function rejectSymlinkLeaf(candidate, label) {
  const leaf = path.resolve(candidate)
  try {
    if (fs.lstatSync(leaf).isSymbolicLink()) throw Error(`${label} must not be a symlink: ${candidate}`)
  } catch (error) {
    if (error?.code === 'ENOENT') return
    throw error
  }
}
const factoryShaExpected = '4f962484b211546300a659acde664df1d9430ceff7108d0877c13cf47d5a3fa5'
const sourceShaExpected = '569fbab57b57baad275a60facfd70b913afe76d69a724b682e821883d40dcae8'
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

const argv = process.argv.slice(2)
const mode = argv.find(x => x === '--write' || x === '--check' || x === '--self-test')
if (!mode) throw Error('choose --write, --check, or --self-test')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || !argv[ci + 1]) throw Error('--cpu-root <immutable snapshot> is required')
const cpuArg = path.resolve(argv[ci + 1])
rejectSymlinkLeaf(cpuArg, '--cpu-root')
const stat = fs.lstatSync(cpuArg)
if (!stat.isDirectory() || stat.isSymbolicLink()) throw Error('--cpu-root must be a non-symlink directory')
const cpuRoot = fs.realpathSync(cpuArg)
const liveArg = process.env.NOISEMAKER_FOR_CPU
if (liveArg) rejectSymlinkLeaf(liveArg, 'NOISEMAKER_FOR_CPU')
if (!liveArg || !fs.existsSync(liveArg) || !fs.statSync(liveArg).isDirectory()) {
  throw Error(`live noisemaker-for-cpu checkout does not exist: ${liveArg ?? '<unset>'}`)
}
const livePackage = path.join(liveArg, 'package.json')
let liveIdentity
try { liveIdentity = JSON.parse(fs.readFileSync(livePackage, 'utf8')).name } catch { throw Error('NOISEMAKER_FOR_CPU is not a noisemaker-for-cpu checkout') }
if (liveIdentity !== 'noisemaker-cpu') throw Error('NOISEMAKER_FOR_CPU is not a noisemaker-for-cpu checkout')
const live = fs.realpathSync(liveArg)
if (beneath(live, cpuRoot) || beneath(cpuRoot, live)) throw Error('authority must be an external immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot)) throw Error('authority must be an external immutable snapshot')

function importClosure() {
  const patterns = [
    /\bfrom\s*['"]([^'"\n]+)['"]/g,
    /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
    /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
  ]
  const entries = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js',
    'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js',
    'src/runtime/surface.js']
  const stack = entries.map(relative => path.join(cpuRoot, relative))
  const seen = new Map()
  while (stack.length) {
    const candidate = stack.pop()
    let resolved
    try { resolved = fs.realpathSync(candidate) } catch { throw Error(`missing import closure file: ${candidate}`) }
    if (!beneath(cpuRoot, resolved) || (live && beneath(live, resolved))) {
      throw Error('import escaped immutable snapshot')
    }
    if (seen.has(resolved)) continue
    const payload = fs.readFileSync(resolved)
    const text = payload.toString('utf8')
    seen.set(resolved, sha(payload))
    if (/\bimport\s*\(\s*(?!['"])/.test(text)) {
      throw Error(`nonliteral dynamic import: ${path.relative(cpuRoot, resolved)}`)
    }
    for (const pattern of patterns) {
      pattern.lastIndex = 0
      let match
      while ((match = pattern.exec(text))) {
        const specifier = match[1]
        if (specifier.startsWith('node:')) continue
        if (!specifier.startsWith('./') && !specifier.startsWith('../') && !specifier.startsWith('/')) {
          throw Error(`bare module specifier ${specifier}`)
        }
        const next = specifier.startsWith('/') ? specifier : path.resolve(path.dirname(resolved), specifier)
        let nextResolved
        try { nextResolved = fs.realpathSync(next) } catch { throw Error(`import escaped or missing: ${specifier}`) }
        if (!beneath(cpuRoot, nextResolved) || (live && beneath(live, nextResolved))) {
          throw Error(`import escaped immutable snapshot: ${specifier}`)
        }
        stack.push(nextResolved)
      }
    }
  }
  return [...seen].map(([file, hash]) => [path.relative(cpuRoot, file), hash])
    .sort((a, b) => a[0].localeCompare(b[0]))
}

const actualClosure = importClosure()
const expectedClosureSorted = [...expectedClosure].sort((a, b) => a[0].localeCompare(b[0]))
if (JSON.stringify(actualClosure) !== JSON.stringify(expectedClosureSorted)) {
  throw Error(`CPU import closure mismatch: ${JSON.stringify(actualClosure)}`)
}
for (const [relative, expected] of expectedClosureSorted) {
  if (sha(fs.readFileSync(path.join(cpuRoot, relative))) !== expected) {
    throw Error(`pinned CPU provenance drift: ${relative}`)
  }
}

const load = relative => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const [{ canonicalKernelFactories, kernelFactories }, { bindCanonicalKernel }, { runPass }, { Surface }, { UPSTREAM_REVISION }] = await Promise.all([
  load('src/effects/catalog.js'), load('src/csl/glsl-kernel.js'), load('src/runtime/pass-runner.js'),
  load('src/runtime/surface.js'), load('src/effects/generated/upstream-snapshot.js'),
])
if (process.version !== 'v24.7.0') throw Error('Distortion authority Node drift')
const canonical = canonicalKernelFactories[key]
const publicFactory = kernelFactories.get(key)
if (typeof canonical !== 'function' || publicFactory !== canonical) throw Error('canonical/public factory identity drift')
if (sha(canonical.toString()) !== factoryShaExpected) throw Error('canonical factory text drift')
const sourceBytes = fs.readFileSync(path.join(cppRoot, sourceRelative))
if (sha(sourceBytes) !== sourceShaExpected) throw Error('corpus source drift')

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const i = (y * width + x) * 4
    data[i] = f((((17 * x + 29 * y + 3 + phase * 7) % 67) + 1) / 71)
    data[i + 1] = f((((31 * x + 11 * y + 5 + phase * 13) % 73) + 2) / 79)
    data[i + 2] = f((((7 * x + 43 * y + 9 + phase * 17) % 83) + 3) / 89)
    data[i + 3] = f((((13 * x + 19 * y + phase) % 37) + 4) / 43)
  }
  return new Surface(width, height, data)
}

const cases = [
  { name: 'displacement-mirror-map-a', width: 8, height: 6, phaseA: 1, phaseB: 2, mode: 0, mapSource: 0, wrap: 0, intensity: 65, smoothing: 1, aberration: 0, antialias: false, tileOffset: [0, 0], fullResolution: [8, 6] },
  { name: 'displacement-repeat-map-b-aa', width: 7, height: 5, phaseA: 3, phaseB: 4, mode: 0, mapSource: 1, wrap: 1, intensity: 90, smoothing: 4, aberration: 0, antialias: true, tileOffset: [2, 1], fullResolution: [13, 9] },
  { name: 'refraction-clamp-map-a', width: 9, height: 6, phaseA: 5, phaseB: 6, mode: 1, mapSource: 0, wrap: 2, intensity: 75, smoothing: 12, aberration: 0, antialias: false, tileOffset: [0, 0], fullResolution: [9, 6] },
  { name: 'refraction-mirror-map-b-aa', width: 6, height: 8, phaseA: 7, phaseB: 8, mode: 1, mapSource: 1, wrap: 0, intensity: 35, smoothing: 3, aberration: 0, antialias: true, tileOffset: [-1, 3], fullResolution: [12, 15] },
  { name: 'reflection-repeat-chromatic', width: 8, height: 7, phaseA: 9, phaseB: 10, mode: 2, mapSource: 0, wrap: 1, intensity: 100, smoothing: 9, aberration: 22, antialias: false, tileOffset: [1, -2], fullResolution: [14, 11] },
  { name: 'reflection-clamp-chromatic-aa', width: 7, height: 6, phaseA: 11, phaseB: 12, mode: 2, mapSource: 1, wrap: 2, intensity: 48, smoothing: 20, aberration: 7, antialias: true, tileOffset: [0, 0], fullResolution: [7, 6] },
]

function render(factory, definition) {
  const inputTex = patternedSurface(definition.width, definition.height, definition.phaseA)
  const tex = patternedSurface(definition.width, definition.height, definition.phaseB)
  const uniforms = {
    resolution: new Float32Array([definition.width, definition.height]),
    tileOffset: new Float32Array(definition.tileOffset.map(f)),
    fullResolution: new Float32Array(definition.fullResolution.map(f)),
    mode: definition.mode, mapSource: definition.mapSource,
    intensity: f(definition.intensity), wrap: definition.wrap,
    smoothing: f(definition.smoothing), aberration: f(definition.aberration),
    antialias: definition.antialias,
  }
  const inputBefore = snapshotSurface(inputTex)
  const texBefore = snapshotSurface(tex)
  const output = new Surface(definition.width, definition.height)
  runPass({ kernel: bindCanonicalKernel(factory, { width: definition.width, height: definition.height,
    uniforms, textures: { inputTex, tex }, tileOffset: uniforms.tileOffset,
    fullResolution: uniforms.fullResolution }), destination: output })
  assertSurfaceUnchanged(inputBefore, inputTex, `${definition.name}/inputTex`)
  assertSurfaceUnchanged(texBefore, tex, `${definition.name}/tex`)
  return { output, inputTex, tex, input_immutable: true }
}

function record(surface) {
  const ws = words(surface.data); const rb = rgba(surface)
  return { f32_words_le: ws, f32_sha256: sha(bytes(surface.data)), rgba8_bytes: rb, rgba8_sha256: sha(Buffer.from(rb)) }
}

function strictCompare(a, b) {
  if (a.width !== b.width || a.height !== b.height) throw Error('dimensions mismatch before lane access')
  const aw = a.data instanceof Float32Array ? words(a.data) : (a.f32_words_le ?? a.words)
  const bw = b.data instanceof Float32Array ? words(b.data) : (b.f32_words_le ?? b.words)
  const ar = a.data instanceof Float32Array ? rgba(a) : (a.rgba8_bytes ?? a.rgba)
  const br = b.data instanceof Float32Array ? rgba(b) : (b.rgba8_bytes ?? b.rgba)
  const expectedCount = a.width * a.height * 4
  if (!Array.isArray(aw) || !Array.isArray(bw) || aw.length !== expectedCount || bw.length !== expectedCount) {
    throw Error('Float32 count mismatch before element access')
  }
  if (!Array.isArray(ar) || !Array.isArray(br) || ar.length !== expectedCount || br.length !== expectedCount) {
    throw Error('RGBA8 count mismatch before element access')
  }
  const changedFloat32 = countDiff(aw, bw)
  const changedRgba8 = countDiff(ar, br)
  return { exact: changedFloat32 === 0 && changedRgba8 === 0,
    changed_float32_lanes: changedFloat32, changed_rgba8_bytes: changedRgba8 }
}

function snapshotSurface(surface) {
  return { words: words(surface.data), bytes: Array.from(bytes(surface.data)) }
}

function assertSurfaceUnchanged(before, surface, label) {
  const after = snapshotSurface(surface)
  if (!equal(before.words, after.words) || !equal(before.bytes, after.bytes))
    throw Error(`${label}: input surface mutated during runPass`)
}

function mutate(text, anchor, replacement) {
  if (text.split(anchor).length - 1 !== 1) throw Error(`mutation anchor cardinality: ${anchor}`)
  return text.replace(anchor, replacement)
}

function comparerSelfTests() {
  const good = { width: 1, height: 1, f32_words_le: ['0x3f800000', '0x00000000', '0x00000000', '0x3f800000'], rgba8_bytes: [255, 0, 0, 255] }
  let touched = false
  const dimensions = { width: 2, height: 1, get f32_words_le() { touched = true; return [] }, rgba8_bytes: [] }
  const rejected = (fn, phrase) => { try { fn(); return false } catch (error) { return !phrase || String(error.message).includes(phrase) } }
  const clone = (value, changes = {}) => ({ ...value, f32_words_le: [...value.f32_words_le], rgba8_bytes: [...value.rgba8_bytes], ...changes })
  const plusZero = clone(good, { f32_words_le: ['0x00000000', ...good.f32_words_le.slice(1)] })
  const minusZero = clone(good, { f32_words_le: ['0x80000000', ...good.f32_words_le.slice(1)] })
  const nanA = clone(good, { f32_words_le: ['0x7fc00001', ...good.f32_words_le.slice(1)] })
  const nanB = clone(good, { f32_words_le: ['0x7fc00002', ...good.f32_words_le.slice(1)] })
  const input = { data: new Float32Array([f(1), f(2)]) }
  const inputBefore = snapshotSurface(input)
  input.data[0] = f(3)
  const inputMutationRejected = rejected(() => assertSurfaceUnchanged(inputBefore, input, 'self-test'))
  const rgbaMismatch = clone(good, { rgba8_bytes: [255, 0, 0, 254] })
  return {
    good: strictCompare(good, clone(good)).exact,
    dimensions_before_access: rejected(() => strictCompare(good, dimensions), 'dimensions') && !touched,
    f32_count: rejected(() => strictCompare(good, clone(good, { f32_words_le: [] })), 'Float32 count'),
    rgba8_count: rejected(() => strictCompare(good, clone(good, { rgba8_bytes: [] })), 'RGBA8 count'),
    signed_zero: strictCompare(plusZero, minusZero).exact === false,
    nan_payload: strictCompare(nanA, nanB).exact === false,
    rgba_mismatch: strictCompare(good, rgbaMismatch).exact === false,
    input_mutation_rejected: inputMutationRejected,
  }
}

const rendered = cases.map(definition => {
  const first = render(canonical, definition); const second = render(canonical, definition)
  if (sha(bytes(first.output.data)) !== sha(bytes(second.output.data))) throw Error(`${definition.name}: repeat mismatch`)
  return { ...definition, expected: record(first.output), repeat_exact: true,
    input_immutable: first.input_immutable }
})
const factoryText = canonical.toString()
const mutationDefs = [
  { name: 'mode-displacement-to-reflection', anchor: 'if (mode == 0)', replacement: 'if (mode == 2)', witnesses: ['displacement-mirror-map-a', 'displacement-repeat-map-b-aa'] },
  { name: 'wrap-repeat-to-clamp', anchor: 'wrap == 1', replacement: 'wrap == 2', witnesses: ['displacement-repeat-map-b-aa', 'reflection-repeat-chromatic'] },
  { name: 'displacement-strength-half', anchor: 'offset[0] = (cos(len * 6.2831854820251465)) * (intensity * 0.0010000000474974513);', replacement: 'offset[0] = (cos(len * 6.2831854820251465)) * (intensity * 0.0005000000237487257);', witnesses: ['displacement-mirror-map-a', 'displacement-repeat-map-b-aa'] },
]
const mutationLedger = await Promise.all(mutationDefs.map(async definition => {
  const text = mutate(factoryText, definition.anchor, definition.replacement)
  const module = await import(`data:text/javascript;base64,${Buffer.from(`${text}\nexport { canonicalFactory194 as distortionFactory }`).toString('base64')}`)
  const mutant = module.distortionFactory
  const results = definition.witnesses.map(name => { const spec = cases.find(x => x.name === name); const ref = render(canonical, spec).output; const cand = render(mutant, spec).output; const result = strictCompare({ width: ref.width, height: ref.height, ...record(ref) }, { width: cand.width, height: cand.height, ...record(cand) }); if (!result.changed_float32_lanes || !result.changed_rgba8_bytes) throw Error(`${definition.name}/${name}: no pixel witness`); return { case: name, ...result } })
  return { ...definition, anchor_sha256: sha(definition.anchor), replacement_sha256: sha(definition.replacement), mutated_factory_sha256: sha(text), independent: true, results }
}))
const comparer = comparerSelfTests()
if (!Object.values(comparer).every(Boolean)) throw Error('comparer self-tests failed')
const document = { schema: 'noisemaker-for-cpp.distortion.pixel-parity.v1', schema_version: 1, program_key: key, effect_key: effect, corpus_revision: corpus, upstream_revision: UPSTREAM_REVISION, factory: { name: canonical.name, text_sha256: factoryShaExpected, public_factory_is_canonical_identity: true, adapter_own_key: false }, runtime_binding_names: ['inputTex', 'tex', 'resolution', 'tileOffset', 'fullResolution', 'mode', 'mapSource', 'intensity', 'wrap', 'smoothing', 'aberration', 'antialias'], runtime_binding_abi: { inputTex: 'Surface', tex: 'Surface', resolution: 'Vec2', tileOffset: 'Vec2', fullResolution: 'Vec2', mode: 'int32', mapSource: 'int32', intensity: 'number', wrap: 'int32', smoothing: 'number', aberration: 'number', antialias: 'bool' }, source_uniform_abi: { inputTex: 'sampler2D', tex: 'sampler2D', resolution: 'vec2', tileOffset: 'vec2', fullResolution: 'vec2', mode: 'int', mapSource: 'int', intensity: 'float', wrap: 'int', smoothing: 'float', aberration: 'float', antialias: 'bool' }, provenance: { source: { relative_path: sourceRelative, bytes: sourceBytes.length, sha256: sha(sourceBytes) }, cpu_snapshot: { immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, import_closure: actualClosure.map(([relative_path, sha256]) => ({ relative_path, sha256 })), closure_cardinality: actualClosure.length } }, comparer_self_tests: comparer, render_cases: rendered, mutation_anchor_cardinality: { total: mutationLedger.length, anchors: Object.fromEntries(mutationLedger.map(x => [x.name, 1])) }, mutation_ledger: mutationLedger, claim_boundaries: { canonical_factory_only: true, typed_slice_landing: false, shared_emitter_modified: false, first_blocker: 'sampler-parameter:calculateNormal:26:1-72:2', additional_blockers: ['derivative-abi:6 call sites', 'mutable-local-arrays:3 declarations / 30 indexed expressions'] } }
const payload = Buffer.from(`${JSON.stringify(document, null, 2)}\n`)
const report = Buffer.from(`# Distortion pixel-parity oracle\n\nAuthenticated canonical CPU oracle for **${key}**. It covers displacement, refraction, reflection, map-source routing, mirror/repeat/clamp wrapping, chromatic aberration, antialias sampling, tiled coordinates, exact Float32 words, RGBA8 bytes, repeatability, and three independent factory mutation witnesses.\n\nThe authority is an unmodified public canonical factory from an immutable CPU snapshot. Its recursively traversed, realpath-confined literal-import closure contains ${actualClosure.length} hash-pinned files; bare specifiers, missing/escaping imports, and nonliteral dynamic imports fail before any oracle import executes.\n\nEach canonical run snapshots both \`inputTex\` and \`tex\` before \`runPass\`, then compares exact Float32 words and backing bytes on those same surfaces immediately after the run. The assertion throws on any mutation; each case's \`input_immutable: true\` flag is emitted only after both checks succeed. The authenticated binding order is \`inputTex:Surface/sampler2D\`, \`tex:Surface/sampler2D\`, followed by the ten scalar/vector controls.\n\nThe typed landing remains intentionally outside this package. The prepared frontend profile records sampler parameters, six derivative calls, and three mutable local fixed-size arrays as separate blockers.\n\n## Reproduction\n\nnode docs/port-engineering/distortion-parity/distortion_oracle_generator.mjs --check --cpu-root \\"$NOISEMAKER_CPU_ROOT\\"\npython3 -B tools/glslcpp/generate_distortion_native_oracle_include.py --check\n`)
function selfTest() {
  const checks = [
    ['closure cardinality', actualClosure.length === expectedClosure.length],
    ['closure exact', JSON.stringify(actualClosure) === JSON.stringify(expectedClosureSorted)],
    ['comparer cases', Object.values(comparer).every(Boolean)],
    ['mutation witnesses', mutationLedger.every(item => item.independent && item.results.every(result => result.changed_float32_lanes > 0 && result.changed_rgba8_bytes > 0))],
  ]
  checks.forEach(([name, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}`))
  if (!checks.every(([, ok]) => ok)) throw Error('Distortion oracle self-test failed')
}
if (mode === '--write') { fs.mkdirSync(here, { recursive: true }); fs.writeFileSync(outPath, payload); fs.writeFileSync(`${outPath}.sha256`, `${sha(payload)}  distortion-oracles.json\n`); fs.writeFileSync(reportPath, report); fs.writeFileSync(`${reportPath}.sha256`, `${sha(report)}  distortion-oracle-report.md\n`); console.log(`distortion oracle written (${rendered.length} cases, ${mutationLedger.length} mutations)`) } else { if (!fs.existsSync(outPath) || !equal([...fs.readFileSync(outPath)], [...payload])) throw Error('distortion oracle drift'); if (!fs.existsSync(reportPath) || !equal([...fs.readFileSync(reportPath)], [...report])) throw Error('distortion report drift'); if (mode === '--self-test') { selfTest(); console.log('strict comparer, provenance, and mutation witnesses verified') } else console.log('distortion oracle check passed') }
