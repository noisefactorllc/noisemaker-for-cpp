#!/usr/bin/env node
// Strict source-bound exact-pixel oracle for synth/remap:remap.
//
// Re-derived at the 0ed489ec... corpus / 61aa869 authority bump. The prior
// oracle (see git history) authenticated `canonicalKernelFactories.canonicalFactory272`,
// a typed-generated kernel reading a packed std140 `data[267]` array, because
// at the OLD upstream revision (117a2366...) the authority's own GLSL
// transpiler handled remap.glsl without trouble. Upstream's 0ed489ec... bump
// grew the uniform layout to 275 slots and introduced
// `struct ZoneTest { bool inside; float d2; }`, which the authority's own
// transpiler cannot lower (see the authority's own comment at the top of
// `src/effects/adapters/remap.js`) -- so the authority itself now dispatches
// `canonicalAdapterFactories.remapFactory`, a hand-written CPU adapter that
// reads semantic uniforms directly ($bindings.zone{N}_*, .bgColor, ...), never
// the packed array. This generator authenticates THAT factory instead. This
// is a legitimate re-derivation, not a relaxation: the authority changed
// underneath the program, so the oracle must follow it to still mean
// "matches the authority."
import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'remap-oracles.json')
const reportPath = path.join(here, 'remap-oracle-report.md')
const materializerPath = path.resolve(cppRoot, 'tools/glslcpp/generate_remap_native_oracle_include.py')
const programKey = 'synth/remap:remap'
const sourceRelative = 'tools/glslcpp/corpus/0ed489ec46842bffba33ee2ec65a218b6dda51f5/sources/synth/remap/remap.glsl'
const sourceSha256 = '500f761ac9b0a58aedc7574f974994abfdaf4d41cb9947a11b4cdd18b0482b9b'
const factorySourceRelative = 'src/effects/adapters/remap.js'
const factoryName = 'remapFactory'
const corpusRevision = '0ed489ec46842bffba33ee2ec65a218b6dda51f5'
const upstreamRevision = '0ed489ec46842bffba33ee2ec65a218b6dda51f5'
// The full literal-import closure reachable from the same six entry points the
// old oracle used, recomputed against the 61aa869 authority snapshot (see
// compute_closure.mjs in the lane scratch dir this was derived in). Sorted by
// path; every file's own sha256 is re-checked below, so a stale entry here
// fails closed rather than silently drifting.
const expectedClosure = [
 ['src/csl/glsl-kernel.js','a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa'],
 ['src/csl/glsl-runtime.js','a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072'],
 ['src/csl/runtime.js','a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee'],
 ['src/effects/adapters/bit-effects.js','5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7'],
 ['src/effects/adapters/crt.js','c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc'],
 ['src/effects/adapters/f32-color.js','b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046'],
 ['src/effects/adapters/fractal.js','0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29'],
 ['src/effects/adapters/index.js','dd2ca7681884fbc3fa2687faeb52aced50076a5f0856736b63831e859073d22e'],
 ['src/effects/adapters/julia.js','0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5'],
 ['src/effects/adapters/median.js','e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583'],
 ['src/effects/adapters/palette.js','8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'],
 ['src/effects/adapters/remap.js','91fd829ba2ad68fabab4124f5464994fc267daa097af4f3dd5a7e20f075f9e79'],
 ['src/effects/adapters/snow.js','202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366'],
 ['src/effects/catalog.js','d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'],
 ['src/effects/definition.js','fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02'],
 ['src/effects/generated/canonical-adapter-data.js','ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab'],
 ['src/effects/generated/canonical-kernels.js','f47dcb900599cf784f7b77d57322452ad6feab7e93f0bbf278d3c81a655bc53c'],
 ['src/effects/generated/kernels.js','b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01'],
 ['src/effects/generated/upstream-snapshot.js','6e7d5516228d7baf6cb6ce87853caf06c61a711e650cf13120bba4db0f9b1ac7'],
 ['src/effects/registry.js','8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'],
 ['src/runtime/pass-runner.js','fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'],
 ['src/runtime/sampler.js','1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328'],
 ['src/runtime/surface.js','0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'],
]
// The adapter's real binding surface: semantic uniforms read directly by
// remapFactory, not the packed std140 `data[275]` array (that array is built
// by remapUniformData() for the retired generated-kernel path only -- see
// src/runtime/renderer.js -- and the adapter never reads it).
const bindingNames = ['tileOffset', 'fullResolution', 'resolution', 'zoneCount', 'smoothEdge',
  'bgColor', 'bgAlpha',
  ...Array.from({ length: 8 }, (_, z) => [`zone${z}_count`, `zone${z}_active`, `zone${z}_alpha`,
    `zone${z}_bounds`, ...Array.from({ length: 32 }, (_, p) => `zone${z}_v${p}`), `zone${z}_tex`]).flat()]
const f = Math.fround, sha256 = v => crypto.createHash('sha256').update(v).digest('hex'),
  finalize = v => { if (v && v.program_key === programKey) { v.schema = 'noisemaker-for-cpp.remap.pixel-parity.v2'; v.schema_version = 2; v.input_fixture.schema = 'noisemaker-for-cpp.remap.input-texture.v2'; v.comparer_self_tests = comparerSelfTests; v.control_group = controlGroup; v.factory.public_factory_is_canonical_identity = controlGroup.public_direct_identity; v.factory.canonical_own_key = controlGroup.canonical_own_key; v.factory.adapter_own_key = controlGroup.adapter_own_key } return v },
  stable = v => JSON.stringify(finalize(v), null, 2) + '\n'
const words = v => Array.from(new Uint32Array(v.buffer, v.byteOffset, v.byteLength / 4), n => `0x${n.toString(16).padStart(8, '0')}`)
const packWords = a => { const b = Buffer.alloc(a.length * 4); a.forEach((v, i) => b.writeUInt32LE(Number.parseInt(v, 16) >>> 0, i * 4)); return b }
const digestWords = a => sha256(packWords(a)), digestBytes = a => sha256(Buffer.from(a))
const changed = (a, b) => a.reduce((n, v, i) => n + (v !== b[i]), 0)
const firstMismatch = (a, b) => { const i = a.findIndex((v, j) => v !== b[j]); return i < 0 ? null : { index: i, expected: a[i], actual: b[i] } }
const beneath = (r, c) => c === r || c.startsWith(`${r}${path.sep}`)
function rejectAbsolute(v, l = 'doc') {
  if (typeof v === 'string') { if (/^(?:[A-Za-z]:[\\/]|\\\\|\/)/.test(v) || /(?:^|[\\/])(?:Users|private|tmp|home)[\\/]/.test(v)) throw Error(`${l}: absolute-looking string`); return }
  if (Array.isArray(v)) v.forEach((x, i) => rejectAbsolute(x, `${l}[${i}]`))
  else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => rejectAbsolute(x, `${l}.${k}`))
}
function checked(t, p) { fs.writeFileSync(t, p); fs.writeFileSync(`${t}.sha256`, `${sha256(p)}  ${path.basename(t)}\n`) }
function verify(t) { const p = fs.readFileSync(t); if (fs.readFileSync(`${t}.sha256`, 'utf8') !== `${sha256(p)}  ${path.basename(t)}\n`) throw Error(`sidecar drift: ${t}`); return p }
function closure(cpu, live) {
  const pats = [/\bfrom\s*['"]([^'"\n]+)['"]/g, /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g, /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm]
  const stack = ['src/effects/catalog.js', 'src/effects/generated/upstream-snapshot.js', 'src/csl/glsl-kernel.js', 'src/csl/glsl-runtime.js', 'src/runtime/pass-runner.js', 'src/runtime/surface.js'].map(x => path.join(cpu, x))
  const seen = new Map()
  while (stack.length) {
    const c = fs.realpathSync(stack.pop())
    if (seen.has(c)) continue
    if (!beneath(cpu, c) || beneath(live, c)) throw Error('import escaped immutable snapshot')
    const p = fs.readFileSync(c); const source = p.toString()
    seen.set(c, sha256(p))
    for (const pat of pats) {
      pat.lastIndex = 0; let m
      while ((m = pat.exec(source))) { const s = m[1]; if (s.startsWith('node:')) continue; if (!s.startsWith('./') && !s.startsWith('../')) throw Error(`bare module specifier ${s}`); stack.push(path.resolve(path.dirname(c), s)) }
    }
  }
  return [...seen].map(([f2, h]) => [path.relative(cpu, f2), h]).sort((a, b) => a[0].localeCompare(b[0]))
}

const argv = process.argv.slice(2), mode = argv.filter(x => ['--write', '--check', '--self-test'].includes(x))
if (mode.length !== 1) throw Error('choose exactly one of --write, --check, or --self-test')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || ci + 1 >= argv.length) throw Error('--cpu-root <immutable snapshot> is required')
if (argv.some((x, i) => i !== ci && i !== ci + 1 && x !== mode[0])) throw Error('unexpected argument')
const arg = path.resolve(argv[ci + 1]), st = fs.lstatSync(arg)
if (st.isSymbolicLink() || !st.isDirectory()) throw Error('--cpu-root must be a non-symlink directory')
const cpu = fs.realpathSync(arg)
if (beneath(cppRoot, cpu)) throw Error('--cpu-root must not live inside the C++ repository')
const liveArg = process.env.NOISEMAKER_FOR_CPU
if (!liveArg) throw Error('NOISEMAKER_FOR_CPU live checkout is required')
if (!fs.existsSync(liveArg) || !fs.statSync(liveArg).isDirectory()) throw Error('an existing live checkout is required for --cpu-root validation')
const liveArgResolved = path.resolve(liveArg), live = fs.realpathSync(liveArgResolved)
if (live !== liveArgResolved || live === cpu || beneath(live, cpu) || beneath(cpu, live)) throw Error('live checkout cannot be authority')

const actualClosure = closure(cpu, live)
const expectedClosureSorted = [...expectedClosure].sort((a, b) => a[0].localeCompare(b[0]))
if (JSON.stringify(actualClosure) !== JSON.stringify(expectedClosureSorted)) throw Error('CPU import closure exact path/hash mismatch')
for (const [r, h] of expectedClosure) if (sha256(fs.readFileSync(path.join(cpu, r))) !== h) throw Error(`pinned CPU provenance drift: ${r}`)
if (sha256(fs.readFileSync(path.join(cppRoot, sourceRelative))) !== sourceSha256) throw Error('Remap GLSL source provenance drift')

const load = r => import(pathToFileURL(fs.realpathSync(path.join(cpu, r))).href)
const [{ canonicalKernelFactories, canonicalAdapterFactories, kernelFactories }, { UPSTREAM_REVISION }, { bindCanonicalKernel }, { runPass }, { Surface }] =
  await Promise.all([load('src/effects/catalog.js'), load('src/effects/generated/upstream-snapshot.js'), load('src/csl/glsl-kernel.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js')])
const canonicalFactory = canonicalAdapterFactories[programKey], publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== factoryName || publicFactory !== canonicalFactory) throw Error('Remap factory identity drift')
if (UPSTREAM_REVISION !== upstreamRevision) throw Error('upstream revision drift')
const factoryFile = path.join(cpu, factorySourceRelative), factorySource = fs.readFileSync(factoryFile, 'utf8')
const factoryText = Function.prototype.toString.call(canonicalFactory)
if (!factorySource.includes(factoryText)) throw Error('factory source binding drift')
const factoryTextSha256 = sha256(factoryText), factorySourceSha256 = sha256(fs.readFileSync(factoryFile))

function tex(w, h, s) { const out = new Surface(w, h); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const i = (y * w + x) * 4; out.data[i] = f(((x * 3 + y * 5 + s) % 17) / 16); out.data[i + 1] = f(((x * 7 + y * 2 + s) % 19) / 18); out.data[i + 2] = f(((x * 11 + y * 13 + s) % 23) / 22); out.data[i + 3] = f(.25 + ((x + y + s) % 7) / 10) } return out }

// Cases 1-10 mirror the prior oracle's scenario coverage (background,
// polygon inside/outside, feather, overlapping premultiplied translucent
// zones, an inactive zone, tiling, zero alpha, the 8-zone cap, dispatch
// across all 8 zones, a degenerate <3-vertex zone). Cases 11-14 are new:
// they exercise the upstream zone-bounds rejection feature the old oracle
// had no uniform for at all, including the feather-driven bounds dilation,
// two zones with independent disjoint bounds windows, and bounds combined
// with a non-default tile offset.
const cases = [
  { name: 'background', width: 5, height: 4, salt: 1, zoneCount: 0, bgColor: [.1, .2, .3], bgAlpha: .75, smoothEdge: .04, zones: [] },
  { name: 'triangle', width: 7, height: 5, salt: 2, zoneCount: 1, bgColor: [0, 0, 0], bgAlpha: 1, smoothEdge: 0, zones: [{ count: 3, alpha: 1, active: 1, verts: [[0, 0], [1, 0], [.5, 1]] }] },
  { name: 'square-soft', width: 6, height: 6, salt: 3, zoneCount: 1, bgColor: [.05, .1, .15], bgAlpha: .5, smoothEdge: .8, zones: [{ count: 4, alpha: .6, active: 1, verts: [[.1, .1], [.9, .1], [.9, .9], [.1, .9]] }] },
  { name: 'overlap', width: 8, height: 5, salt: 4, zoneCount: 2, bgColor: [.2, .1, .05], bgAlpha: .8, smoothEdge: 0, zones: [{ count: 4, alpha: .5, active: 1, verts: [[0, 0], [.8, 0], [.8, 1], [0, 1]] }, { count: 4, alpha: .9, active: 1, verts: [[.2, 0], [1, 0], [1, 1], [.2, 1]] }] },
  { name: 'inactive', width: 5, height: 7, salt: 5, zoneCount: 2, bgColor: [.4, .3, .2], bgAlpha: .9, smoothEdge: .2, zones: [{ count: 4, alpha: 1, active: 0, verts: [[0, 0], [1, 0], [1, 1], [0, 1]] }] },
  { name: 'tiled', width: 6, height: 4, salt: 6, zoneCount: 1, bgColor: [0, 0, 0], bgAlpha: 1, smoothEdge: .1, tileOffset: [3, 2], fullResolution: [12, 8], zones: [{ count: 4, alpha: .75, active: 1, verts: [[.2, .2], [.8, .2], [.8, .8], [.2, .8]] }] },
  { name: 'alpha-zero', width: 4, height: 4, salt: 7, zoneCount: 1, bgColor: [.3, .4, .5], bgAlpha: .7, smoothEdge: 0, zones: [{ count: 4, alpha: 0, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]] }] },
  { name: 'eight-zone-cap', width: 9, height: 3, salt: 8, zoneCount: 9, bgColor: [0, 0, 0], bgAlpha: 1, smoothEdge: 0, zones: Array.from({ length: 8 }, (_, i) => ({ count: 3, alpha: .1 + i * .1, active: 1, verts: [[0, 0], [1, 0], [.5, 1]] })) },
  { name: 'dispatch-all-zones', width: 16, height: 8, salt: 9, zoneCount: 8, bgColor: [0, 0, 0], bgAlpha: 1, smoothEdge: 0, zones: Array.from({ length: 8 }, (_, i) => ({ count: 4, alpha: 1, active: 1, verts: [[i / 8, 0], [(i + 1) / 8, 0], [(i + 1) / 8, 1], [i / 8, 1]] })) },
  { name: 'degenerate-active', width: 5, height: 4, salt: 10, zoneCount: 1, bgColor: [.25, .35, .45], bgAlpha: .6, smoothEdge: 0, zones: [{ count: 2, alpha: 1, active: 1, verts: [[.1, .1], [.9, .9]] }] },
  { name: 'bounds-reject-outside', width: 10, height: 6, salt: 11, zoneCount: 1, bgColor: [.15, .05, .2], bgAlpha: 1, smoothEdge: 0, zones: [{ count: 4, alpha: 1, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]], bounds: [.5, 0, 1, 1] }] },
  { name: 'bounds-reject-with-feather', width: 8, height: 5, salt: 12, zoneCount: 1, bgColor: [.05, .2, .1], bgAlpha: 1, smoothEdge: 4, zones: [{ count: 4, alpha: 1, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]], bounds: [.3, .3, .7, .7] }] },
  { name: 'bounds-two-zones-disjoint-windows', width: 9, height: 7, salt: 13, zoneCount: 2, bgColor: [.1, .1, .1], bgAlpha: 1, smoothEdge: 0, zones: [{ count: 4, alpha: .6, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]], bounds: [0, 0, .5, 1] }, { count: 4, alpha: .8, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]], bounds: [.4, 0, 1, 1] }] },
  { name: 'bounds-tiled-nonsquare', width: 6, height: 4, salt: 14, zoneCount: 1, bgColor: [.2, .2, 0], bgAlpha: 1, smoothEdge: 2, tileOffset: [6, 4], fullResolution: [18, 12], zones: [{ count: 4, alpha: 1, active: 1, verts: [[0, 0], [1, 0], [1, 1], [0, 1]], bounds: [.2, .2, .8, .8] }] },
]

// Builds the exact semantic uniform surface remapFactory reads -- never the
// packed std140 array (that is the retired generated-kernel path's own
// input, built by remapUniformData(), and is not exercised here at all).
function semanticUniforms(s) {
  const uniforms = { zoneCount: s.zoneCount, smoothEdge: s.smoothEdge, bgColor: s.bgColor, bgAlpha: s.bgAlpha }
  for (let z = 0; z < 8; z++) {
    const q = s.zones[z]
    if (!q) continue
    uniforms[`zone${z}_count`] = q.count
    uniforms[`zone${z}_active`] = q.active
    uniforms[`zone${z}_alpha`] = q.alpha
    if (q.bounds) uniforms[`zone${z}_bounds`] = q.bounds
    const pairs = Math.ceil(q.verts.length / 2)
    for (let p = 0; p < pairs; p++) {
      const a = q.verts[p * 2] ?? [0, 0], b = q.verts[p * 2 + 1] ?? [0, 0]
      uniforms[`zone${z}_v${p}`] = [a[0], a[1], b[0], b[1]]
    }
  }
  return uniforms
}

function render(s, factory = canonicalFactory) {
  const input = tex(s.width, s.height, s.salt), before = new Uint32Array(input.data.buffer.slice(0))
  const textures = Object.fromEntries(Array.from({ length: 8 }, (_, z) => [`zone${z}_tex`, z === 1 ? tex(s.width, s.height, s.salt + 100) : input]))
  const kernel = bindCanonicalKernel(factory, {
    width: s.width, height: s.height, uniforms: semanticUniforms(s), textures,
    tileOffset: s.tileOffset ? new Float32Array(s.tileOffset) : undefined,
    fullResolution: s.fullResolution ? new Float32Array(s.fullResolution) : undefined,
  })
  const output = new Surface(s.width, s.height)
  runPass({ kernel, destination: output, time: 0, seed: 0, tileRows: 1 })
  return {
    input, output, inputWords: words(input.data), outputWords: words(output.data), outputBytes: Array.from(output.toRgba8()),
    inputUnchanged: before.every((v, i) => v === new Uint32Array(input.data.buffer)[i]),
    inputStorage: input.data, outputObject: output, outputData: output.data, outputBuffer: output.data.buffer,
  }
}

function compareExact(expectedWords, actualWords, expectedBytes, actualBytes, width, height) {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) return { equal: false, reason: 'dimensions', firstFloat32Mismatch: null, firstRgba8Mismatch: null }
  const n = width * height * 4
  if (expectedWords.length !== n || actualWords.length !== n) return { equal: false, reason: 'float32_count', firstFloat32Mismatch: null, firstRgba8Mismatch: null }
  if (expectedBytes.length !== n || actualBytes.length !== n) return { equal: false, reason: 'rgba8_count', firstFloat32Mismatch: null, firstRgba8Mismatch: null }
  const float32 = firstMismatch(expectedWords, actualWords), rgba8 = firstMismatch(expectedBytes, actualBytes)
  return { equal: float32 === null && rgba8 === null, reason: float32 ? 'float32_mismatch' : rgba8 ? 'rgba8_mismatch' : 'equal', firstFloat32Mismatch: float32, firstRgba8Mismatch: rgba8 }
}

const comparerSelfTests = (() => {
  const z = ['0x00000000', '0x00000000', '0x00000000', '0x00000000'], b = [0, 0, 0, 0]
  const good = compareExact(z, z, b, b, 1, 1), dim = compareExact([], [], [], [], 0, 1)
  const short = compareExact(z.slice(0, 3), z, b, b, 1, 1), long = compareExact([...z, '0x00000000'], z, b, b, 1, 1)
  const rgbaCount = compareExact(z, z, [], [], 1, 1), rgbaMismatch = compareExact(z, z, b, [0, 0, 0, 1], 1, 1)
  const signedZero = compareExact(z, ['0x80000000', ...z.slice(1)], b, b, 1, 1)
  const nanPayload = compareExact(['0x7fc00001', ...z.slice(1)], ['0x7fc00002', ...z.slice(1)], b, b, 1, 1)
  const first = compareExact([...z, ...z], ['0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000000', '0x00000001'], [...b, ...b], [...b, ...b], 2, 1)
  return { good: good.equal, dimensions: dim.reason === 'dimensions', short: short.reason === 'float32_count', long: long.reason === 'float32_count', rgba8_count: rgbaCount.reason === 'rgba8_count', rgba8_mismatch: rgbaMismatch.reason === 'rgba8_mismatch', signed_zero: signedZero.reason === 'float32_mismatch', nan_payload: nanPayload.reason === 'float32_mismatch', first_mismatch: first.firstFloat32Mismatch?.index === 7 }
})()

const rendered = cases.map(s => {
  const r = render(s), repeat = render(s), direct = render(s, publicFactory), ib = Array.from(r.input.toRgba8())
  const repeatComparison = compareExact(r.outputWords, repeat.outputWords, r.outputBytes, repeat.outputBytes, s.width, s.height)
  const directComparison = compareExact(r.outputWords, direct.outputWords, r.outputBytes, direct.outputBytes, s.width, s.height)
  const controls = { zone_count: s.zoneCount, bg_color: s.bgColor, bg_alpha: s.bgAlpha, smooth_edge: s.smoothEdge, tile_offset: s.tileOffset ?? [0, 0], full_resolution: s.fullResolution ?? [s.width, s.height], zones: s.zones }
  if (!repeatComparison.equal || !directComparison.equal || repeat.outputObject === r.outputObject || repeat.outputBuffer === r.outputBuffer || !r.inputUnchanged) throw Error(`Remap case identity/immutability failed: ${s.name}`)
  return {
    name: s.name, width: s.width, height: s.height, salt: s.salt, controls, control_sha256: sha256(stable(controls)),
    input: { width: s.width, height: s.height, salt: s.salt, f32_words_le: r.inputWords, f32_sha256: digestWords(r.inputWords), rgba8_bytes: ib, rgba8_sha256: digestBytes(ib) },
    expected: { f32_words_le: r.outputWords, f32_sha256: digestWords(r.outputWords), rgba8_bytes: r.outputBytes, rgba8_sha256: digestBytes(r.outputBytes) },
    repeat_identity: { exact_float32: repeatComparison.equal, exact_rgba8: repeatComparison.equal, distinct_output_object: repeat.outputObject !== r.outputObject, distinct_backing_buffer: repeat.outputBuffer !== r.outputBuffer },
    public_identity: { exact_float32: directComparison.equal, exact_rgba8: directComparison.equal, factory_identity: publicFactory === canonicalFactory },
    input_immutable_exact_bits: r.inputUnchanged,
  }
})
const baseline = new Map(rendered.map(x => [x.name, x]))

// Seven independent source-anchor mutations of the WHOLE remap.js module
// text (not just remapFactory's own toString(): unlike the old generated
// kernel, the adapter factors testEdge/walkZone out as separate top-level
// functions the factory closes over, so re-evaluating just the factory's
// own text would throw ReferenceError). Each anchor is checked to occur
// exactly once in the unmutated file before it is replaced.
const defs = [
  { name: 'polygon-crossing', group: 'polygon-branch', mechanism: 'disable the even-odd crossing toggle', anchor: 't.inside = !t.inside', replacement: 't.inside = false' },
  { name: 'edge-distance', group: 'edge-smoothing', mechanism: 'disable squared-distance accumulation', anchor: 'if (d2 < t.d2) t.d2 = d2', replacement: 'if (false) t.d2 = d2' },
  { name: 'zone-count-read', group: 'zone-metadata', mechanism: 'force every zone vertex count to zero', anchor: 'const n = Math.min(Math.trunc(count), MAX_PAIRS * 2)', replacement: 'const n = 0' },
  { name: 'zone-active-gate', group: 'zone-metadata', mechanism: 'drop the active-flag gate, keep the vertex-count gate', anchor: 'if (n < 3 || active < 0.5) continue', replacement: 'if (n < 3) continue' },
  { name: 'zone-bounds-reject', group: 'zone-bounds', mechanism: 'disable the per-zone bounds rejection entirely', anchor: 'if (px < bounds[0] - dilateX || py < bounds[1] - dilateY || px > bounds[2] + dilateX || py > bounds[3] + dilateY) continue', replacement: 'if (false) continue' },
  { name: 'feather-coverage', group: 'edge-smoothing', mechanism: 'force full coverage outside the polygon whenever distance math would apply', anchor: 'coverage = 1 - smoothstep(0, featherPx, Math.sqrt(t.d2))', replacement: 'coverage = 1' },
  { name: 'sample-zone-dispatch', group: 'sampler-dispatch', mechanism: 'route every zone sample to the next zone slot', anchor: 'const surface = $bindings[`zone${z}_tex`]', replacement: 'const surface = $bindings[`zone${(z + 1) % MAX_ZONES}_tex`]' },
]
const ledger = []
for (const d of defs) {
  const n = factorySource.split(d.anchor).length - 1
  if (n !== 1) throw Error(`${d.name}: anchor cardinality ${n}`)
  const mutated = factorySource.replace(d.anchor, d.replacement)
  let mf
  try { mf = (await import(`data:text/javascript;base64,${Buffer.from(mutated).toString('base64')}`))[factoryName] } catch { mf = null }
  if (typeof mf !== 'function') throw Error(`${d.name}: mutant failed to evaluate`)
  const results = cases.map(s => {
    const m = render(s, mf), b = baseline.get(s.name)
    const fl = changed(b.expected.f32_words_le, m.outputWords), by = changed(b.expected.rgba8_bytes, m.outputBytes)
    return { case: s.name, changed_float32_lanes: fl, changed_rgba8_bytes: by, float32_witness: firstMismatch(b.expected.f32_words_le, m.outputWords), rgba8_witness: firstMismatch(b.expected.rgba8_bytes, m.outputBytes) }
  })
  const w = results.filter(x => x.changed_float32_lanes > 0 && x.changed_rgba8_bytes > 0)
  if (!w.length) throw Error(`${d.name}: no Float32+RGBA8 witness`)
  ledger.push({
    ...d, independent: true, source_relative_path: factorySourceRelative, source_sha256: factorySourceSha256,
    canonical_factory_text_sha256: factoryTextSha256, mutated_module_text_sha256: sha256(mutated), anchor_occurrence_count: n,
    source_anchor_sha256: sha256(d.anchor), replacement_sha256: sha256(d.replacement),
    results, witness_cases: w.map(x => x.case), control_cases: results.filter(x => !x.changed_float32_lanes).map(x => x.case),
  })
}

const a = render(cases[1]), b = render(cases[1]), c = render(cases[1]), d = render(cases[2])
const controlGroup = {
  repeatability: { case: cases[1].name, identical_float32: JSON.stringify(a.outputWords) === JSON.stringify(b.outputWords), identical_rgba8: JSON.stringify(a.outputBytes) === JSON.stringify(b.outputBytes), distinct_output_objects: a.outputObject !== b.outputObject, distinct_backing_buffers: a.outputBuffer !== b.outputBuffer },
  input_immutability: { case: cases[1].name, unchanged: a.inputUnchanged },
  input_lifetime: { case: cases[1].name, stable_after_independent_render: JSON.stringify(c.inputWords) === JSON.stringify(words(c.inputStorage)) },
  independent_output_storage: { case: cases[1].name, distinct_data_objects: c.outputData !== a.outputData, distinct_backing_buffers: c.outputBuffer !== a.outputBuffer },
  public_direct_identity: publicFactory === canonicalFactory,
  canonical_own_key: Object.prototype.hasOwnProperty.call(canonicalKernelFactories, programKey),
  adapter_own_key: Object.prototype.hasOwnProperty.call(canonicalAdapterFactories, programKey),
}
if (!controlGroup.repeatability.identical_float32 || !controlGroup.repeatability.identical_rgba8 || !controlGroup.repeatability.distinct_output_objects || !controlGroup.repeatability.distinct_backing_buffers
    || !controlGroup.input_immutability.unchanged || !controlGroup.input_lifetime.stable_after_independent_render || !controlGroup.independent_output_storage.distinct_data_objects
    || !controlGroup.independent_output_storage.distinct_backing_buffers || !controlGroup.public_direct_identity
    // Inverted from the pre-bump oracle: the authority's OWN generated kernel
    // for this program still exists (unused) so canonical_own_key stays true,
    // but the whole point of this re-derivation is that the adapter now also
    // owns the key and, via catalog.js's spread order, wins.
    || !controlGroup.canonical_own_key || !controlGroup.adapter_own_key)
  throw Error('Remap runtime controls failed')

const document = {
  schema: 'noisemaker-for-cpp.remap.pixel-parity.v1', schema_version: 1, program_key: programKey, effect_key: 'synth/remap', runtime_key: programKey,
  corpus_revision: corpusRevision, upstream_revision: upstreamRevision,
  factory: { name: factoryName, text_sha256: factoryTextSha256, public_factory_is_canonical_identity: true, adapter_own_key: true },
  runtime_binding_names: bindingNames,
  exactness_contract: { float32: 'raw little-endian uint32 words; signed zero and NaN payloads significant', rgba8: 'complete independently captured RGBA8 bytes', tolerance: 'none', dimensions: 'checked before lane access' },
  comparer_self_tests: { dimensions_before_access: true, first_mismatch_reported: true, raw_words_and_rgba8_independent: true, cases: { good: true, dimensions: true, short: true, long: true, rgba8_count: true, rgba8_mismatch: true, signed_zero: true, nan_payload: true } },
  provenance: {
    source: { relative_path: sourceRelative, sha256: sourceSha256 },
    factory_source: { relative_path: factorySourceRelative, sha256: factorySourceSha256 },
    cpu_snapshot: { argument: '<immutable-cpu-snapshot-root>', immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, import_closure: actualClosure.map(([relative_path, sha]) => ({ relative_path, sha256: sha })) },
    generator: { relative_path: 'docs/port-engineering/remap-parity/remap_oracle_generator.mjs', sha256: '' },
    materializer: { relative_path: 'tools/glslcpp/generate_remap_native_oracle_include.py', sha256: '' },
  },
  input_fixture: { schema: 'noisemaker-for-cpp.remap.input-texture.v1', coordinate_order: 'x-fastest row-major', component_order: ['r', 'g', 'b', 'a'], formula: 'f32(((x*3+y*5+salt)%17)/16), f32(((x*7+y*2+salt)%19)/18), f32(((x*11+y*13+salt)%23)/22), f32(.25+((x+y+salt)%7)/10)' },
  render_cases: rendered,
  source_mutation_contract: { source_relative_path: factorySourceRelative, source_sha256: factorySourceSha256, execution: 'independent exact source anchor replacements of the whole adapter module, re-imported as a fresh module and rendered through bindCanonicalKernel/runPass' },
  mutation_anchor_cardinality: { total: ledger.length, anchors: Object.fromEntries(ledger.map(x => [x.name, x.anchor_occurrence_count])) },
  mutation_ledger: ledger,
  control_group: controlGroup,
  claim_boundaries: { authority: 'remapFactory (canonicalAdapterFactories) from an immutable snapshot; C++ output does not participate', source: 'Remap GLSL and the hand-written JS adapter are hash-pinned', mutations: 'independent whole-module source anchor replacements, never uniform perturbations' },
}
rejectAbsolute(document)
document.provenance.generator.sha256 = sha256(fs.readFileSync(fileURLToPath(import.meta.url)))
document.provenance.materializer.sha256 = fs.existsSync(materializerPath) ? sha256(fs.readFileSync(materializerPath)) : '0'.repeat(64)
const payload = Buffer.from(stable(document))
const report = Buffer.from(`# Remap exact-pixel CPU oracle\n\nAuthenticated \`${programKey}\` against an immutable CPU snapshot and the hand-written \`remapFactory\` adapter (semantic uniforms, not the packed std140 RemapUniforms array -- that array now feeds only the retired generated-kernel path). Exact Float32 words and independently captured RGBA8 bytes are required.\n\n- Cases: ${rendered.length}; source mutants: ${ledger.length}.\n- Authority closure: ${actualClosure.length} literal-import files.\n- JSON SHA-256: ${sha256(payload)}.\n`)

const allTrue = value => typeof value === 'boolean' ? value : (typeof value === 'object' && value !== null ? Object.values(value).every(allTrue) : true)
function selfTest() {
  const checks = [
    ['closure', JSON.stringify(actualClosure) === JSON.stringify(expectedClosureSorted)],
    ['captures', rendered.every(x => x.expected.f32_words_le.length === x.width * x.height * 4 && x.expected.rgba8_bytes.length === x.width * x.height * 4)],
    ['mutants', ledger.every(x => x.anchor_occurrence_count === 1 && x.witness_cases.length && x.results.some(r => r.changed_float32_lanes > 0 && r.changed_rgba8_bytes > 0))],
    ['controls', allTrue(controlGroup)],
    ['comparer', allTrue(comparerSelfTests)],
    ['paths', (() => { try { rejectAbsolute({ x: '/tmp/x' }); return false } catch { return true } })()],
  ]
  checks.forEach(([n, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${n}`))
  return checks.every(([, ok]) => ok) ? 0 : 1
}
function checkMaterializer() {
  const result = spawnSync('python3', ['-B', materializerPath, '--check'], { cwd: cppRoot, encoding: 'utf8' })
  if (result.status !== 0) throw Error(`remap native materializer coherence check failed: ${result.stderr || result.stdout || `exit ${result.status}`}`)
}
if (mode[0] === '--self-test') process.exit(selfTest())
if (mode[0] === '--write') { checked(outputPath, payload); checked(reportPath, report); console.log(`remap oracle written (${payload.length} bytes, ${sha256(payload)})`) }
else { if (!verify(outputPath).equals(payload) || !verify(reportPath).equals(report)) throw Error('remap oracle package drift'); checkMaterializer(); console.log(`remap oracle generator: ok (${rendered.length} cases, ${ledger.length} mutations)`) }
