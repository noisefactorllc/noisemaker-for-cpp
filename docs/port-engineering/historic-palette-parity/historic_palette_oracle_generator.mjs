#!/usr/bin/env node
// Authenticated exact-pixel oracle for filter/historicPalette:historicPalette.
// Only the canonical adapter factory from the caller-supplied immutable CPU
// snapshot executes; no C++ output or local implementation participates.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const generatorPath = fileURLToPath(import.meta.url)
const cppRoot = fs.realpathSync(path.resolve(here, '../../..'))
const outputPath = path.join(here, 'historic-palette-oracles.json')
const reportPath = path.join(here, 'historic-palette-oracle-report.md')
const programKey = 'filter/historicPalette:historicPalette'
const sourceRelative = 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/historicPalette/historicPalette.glsl'
const sourceSha256 = 'cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33'
const corpusRevision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const upstreamRevision = '117a236679d1db3ab8f0e278230ece277b57564c'
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
]
const bindingNames = ['tileOffset', 'fullResolution', 'inputTex', 'paletteIndex', 'smoothness', 'rotation', 'offset', 'repeat', 'alpha', 'time']
const bindingAbi = { tileOffset: 'Vec2', fullResolution: 'Vec2', inputTex: 'Surface', paletteIndex: 'number', smoothness: 'number', rotation: 'number', offset: 'number', repeat: 'number', alpha: 'number', time: 'number' }
const f = Math.fround
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex')
const stable = value => JSON.stringify(value, null, 2) + '\n'
const words = view => Array.from(new Uint32Array(view.buffer, view.byteOffset, view.byteLength / 4), n => `0x${n.toString(16).padStart(8, '0')}`)
const f32Word = value => words(new Float32Array([value]))[0]
const int32Word = value => Number(value) | 0
const packWords = values => { const b = Buffer.alloc(values.length * 4); values.forEach((v, i) => b.writeUInt32LE(Number.parseInt(v, 16) >>> 0, i * 4)); return b }
const digestWords = values => sha256(packWords(values))
const digestBytes = values => sha256(Buffer.from(values))
const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i])
const changed = (a, b) => a.reduce((n, v, i) => n + (v !== b[i] ? 1 : 0), 0)
const beneath = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`)
function rejectAbsolute(value, label = 'document') {
  if (typeof value === 'string') {
    if (value.startsWith('/') || /(?:^|[\\/])(Users|private|tmp|home)[\\/]/.test(value)) throw new Error(`${label}: absolute-looking string`)
  } else if (Array.isArray(value)) value.forEach((item, i) => rejectAbsolute(item, `${label}[${i}]`))
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, item]) => rejectAbsolute(item, `${label}.${key}`))
}
function checked(target, payload) { fs.writeFileSync(target, payload); fs.writeFileSync(`${target}.sha256`, `${sha256(payload)}  ${path.basename(target)}\n`) }
function verify(target) { const payload = fs.readFileSync(target); if (fs.readFileSync(`${target}.sha256`, 'utf8') !== `${sha256(payload)}  ${path.basename(target)}\n`) throw new Error(`sidecar drift: ${target}`); return payload }
function compareExact(expected, actual, label = 'comparison') {
  if (expected.width !== actual.width || expected.height !== actual.height) throw new Error(`${label}: dimensions mismatch before lane access`)
  if (expected.f32_words_le.length !== actual.f32_words_le.length) throw new Error(`${label}: Float32 count mismatch`)
  for (let i = 0; i < expected.f32_words_le.length; i += 1) if (expected.f32_words_le[i] !== actual.f32_words_le[i]) throw new Error(`${label}: Float32 first mismatch at lane ${i}`)
  if (expected.rgba8_bytes.length !== actual.rgba8_bytes.length) throw new Error(`${label}: RGBA8 count mismatch`)
  for (let i = 0; i < expected.rgba8_bytes.length; i += 1) if (expected.rgba8_bytes[i] !== actual.rgba8_bytes[i]) throw new Error(`${label}: RGBA8 first mismatch at byte ${i}`)
}

const argv = process.argv.slice(2)
const modes = argv.filter(x => ['--write', '--check', '--self-test'].includes(x))
if (modes.length !== 1) throw new Error('choose exactly one of --write, --check, or --self-test')
const ci = argv.indexOf('--cpu-root')
if (ci < 0 || ci + 1 >= argv.length) throw new Error('--cpu-root <immutable snapshot> is required')
const cpuArg = argv[ci + 1]
const cpuArgResolved = path.resolve(cpuArg)
const cpuArgStat = fs.existsSync(cpuArgResolved) ? fs.lstatSync(cpuArgResolved) : null
if (!cpuArgStat || cpuArgStat.isSymbolicLink() || !cpuArgStat.isDirectory()) throw new Error('--cpu-root must be a non-symlink directory')
const cpuRoot = fs.realpathSync(cpuArgResolved)
const liveArg = process.env.NOISEMAKER_FOR_CPU || path.resolve(cppRoot, '../noisemaker-for-cpu')
const liveRoot = fs.existsSync(liveArg) ? fs.realpathSync(liveArg) : null
if (liveRoot && (beneath(liveRoot, cpuRoot) || beneath(cpuRoot, liveRoot))) throw new Error('--cpu-root must be an immutable snapshot, never the live checkout')
if (beneath(cppRoot, cpuRoot)) throw new Error('--cpu-root must not live inside the C++ repository')

function rejectNonliteralDynamicImports(source, label) {
  const dynamic = /\bimport\s*\(([\s\S]*?)\)/g
  let match
  while ((match = dynamic.exec(source))) {
    if (!/^\s*(['"])(?:\\.|(?!\1)[^\\\r\n])*\1\s*$/.test(match[1])) {
      throw new Error(`nonliteral dynamic import in ${label}`)
    }
  }
}
function resolveImportedFile(importer, specifier, root = cpuRoot) {
  if (specifier.startsWith('node:')) return null
  if (!specifier.startsWith('./') && !specifier.startsWith('../')) {
    throw new Error(`bare module specifier ${specifier} in ${importer}`)
  }
  const lexical = path.resolve(path.dirname(importer), specifier)
  let resolved
  try {
    resolved = fs.realpathSync(lexical)
  } catch (error) {
    throw new Error(`cannot resolve imported dependency ${specifier} from ${importer}: ${error.message}`)
  }
  if (!beneath(root, resolved)) throw new Error(`import escaped immutable snapshot: ${specifier} from ${importer}`)
  return resolved
}
function resolveAuthorityFile(relative, root = cpuRoot) {
  const lexical = path.resolve(root, relative)
  const resolved = fs.realpathSync(lexical)
  if (!beneath(root, resolved)) throw new Error(`import escaped immutable snapshot: ${relative}`)
  return resolved
}
function closure(root = cpuRoot) {
  const patterns = [
    /\bfrom\s*['"]([^'"\n]+)['"]/g,
    /\bimport\s*\(\s*['"]([^'"\n]+)['"]\s*\)/g,
    /^[ \t]*import\s+['"]([^'"\n]+)['"]/gm,
  ]
  const stack = [
    'src/effects/catalog.js',
    'src/effects/generated/upstream-snapshot.js',
    'src/csl/glsl-kernel.js',
    'src/csl/glsl-runtime.js',
    'src/runtime/pass-runner.js',
    'src/runtime/surface.js',
  ].map(relative => path.resolve(root, relative))
  const seen = new Map()
  while (stack.length) {
    const importer = fs.realpathSync(stack.pop())
    if (!beneath(root, importer)) throw new Error('import escaped immutable snapshot')
    if (seen.has(importer)) continue
    const payload = fs.readFileSync(importer)
    const source = payload.toString('utf8')
    rejectNonliteralDynamicImports(source, importer)
    seen.set(importer, sha256(payload))
    for (const pattern of patterns) {
      pattern.lastIndex = 0
      let match
      while ((match = pattern.exec(source))) {
        const dependency = resolveImportedFile(importer, match[1], root)
        if (dependency) stack.push(dependency)
      }
    }
  }
  return [...seen].map(([absolute, hash]) => [path.relative(root, absolute).split(path.sep).join('/'), hash]).sort((a, b) => a[0].localeCompare(b[0]))
}
const actualClosure = closure()
const expectedClosureSorted = [...expectedClosure].sort((a, b) => a[0].localeCompare(b[0]))
if (JSON.stringify(actualClosure) !== JSON.stringify(expectedClosureSorted)) throw new Error('CPU import closure exact path/hash mismatch')
for (const [relative, expectedHash] of expectedClosure) {
  const resolved = resolveAuthorityFile(relative)
  if (sha256(fs.readFileSync(resolved)) !== expectedHash) throw new Error(`pinned CPU provenance drift: ${relative}`)
}
const sourcePayload = fs.readFileSync(path.join(cppRoot, sourceRelative)); if (sha256(sourcePayload) !== sourceSha256) throw new Error('historic palette corpus source provenance drift')
const load = relative => import(pathToFileURL(resolveAuthorityFile(relative)).href)
const [{ canonicalAdapterFactories, kernelFactories }, { UPSTREAM_REVISION }, { bindCanonicalKernel }, { runPass }, { Surface }, { historicPaletteData }] = await Promise.all([load('src/effects/catalog.js'), load('src/effects/generated/upstream-snapshot.js'), load('src/csl/glsl-kernel.js'), load('src/runtime/pass-runner.js'), load('src/runtime/surface.js'), load('src/effects/generated/canonical-adapter-data.js')])
const canonicalFactory = canonicalAdapterFactories[programKey]; const publicFactory = kernelFactories.get(programKey)
if (typeof canonicalFactory !== 'function' || canonicalFactory.name !== 'historicPaletteFactory') throw new Error('canonical adapter factory identity drift')
if (publicFactory !== canonicalFactory) throw new Error('public factory is not canonical adapter identity')
if (UPSTREAM_REVISION !== upstreamRevision) throw new Error('upstream revision drift')
const canonicalFactoryText = Function.prototype.toString.call(canonicalFactory); const factoryTextSha256 = sha256(canonicalFactoryText)
const clamp = (value, low = 0, high = 1) => Math.min(Math.max(value, low), high)
const mix = (a, b, amount) => a * (1 - amount) + b * amount
const fract = value => value - Math.floor(value)
const smoothstep = (edge0, edge1, value) => { if (edge0 === edge1) return value < edge0 ? 0 : 1; const amount = clamp((value - edge0) / (edge1 - edge0)); return amount * amount * (3 - 2 * amount) }
function sampleHistoric(entry, lum, smoothness, out) { const blendWidth = smoothness * 0.1; const blends = [smoothstep(0.2 - blendWidth, 0.2 + blendWidth, lum), smoothstep(0.4 - blendWidth, 0.4 + blendWidth, lum), smoothstep(0.6 - blendWidth, 0.6 + blendWidth, lum), smoothstep(0.8 - blendWidth, 0.8 + blendWidth, lum)]; out[0] = entry[0]; out[1] = entry[1]; out[2] = entry[2]; for (let colorIndex = 1; colorIndex < 5; colorIndex += 1) { const amount = blends[colorIndex - 1]; const base = colorIndex * 3; out[0] = mix(out[0], entry[base], amount); out[1] = mix(out[1], entry[base + 1], amount); out[2] = mix(out[2], entry[base + 2], amount) } if (blendWidth > 0) { const distance = lum > 0.5 ? lum - 1 : lum; const wrapFactor = smoothstep(-blendWidth, blendWidth, distance); const wrapMask = 1 - smoothstep(0, blendWidth, Math.abs(distance)); for (let channel = 0; channel < 3; channel += 1) { const wrapColor = mix(entry[12 + channel], entry[channel], wrapFactor); out[channel] = mix(out[channel], wrapColor, wrapMask) } } }

function syntheticInput(width, height, salt) { const input = new Surface(width, height); for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) { const i = (y * width + x) * 4; input.data[i] = f(((x * 3 + y * 5 + salt) % 17) / 16); input.data[i + 1] = f(((x * 7 + y * 2 + salt) % 19) / 18); input.data[i + 2] = f(((x * 11 + y * 13 + salt) % 23) / 22); input.data[i + 3] = f(1) } return input }
const cases = Array.from({ length: 21 }, (_, paletteIndex) => ({ name: `palette-${paletteIndex}`, width: 5 + (paletteIndex % 3), height: 4 + (paletteIndex % 2), time: f((paletteIndex % 5) * 0.37), paletteIndex, smoothness: paletteIndex % 4 === 0 ? 0 : f(0.25 + (paletteIndex % 3) * 0.25), rotation: [-1, 0, 1][paletteIndex % 3], offset: f((paletteIndex * 13) % 101), repeat: 1 + (paletteIndex % 4), alpha: f(paletteIndex % 3 === 0 ? 1 : paletteIndex % 3 === 1 ? 0 : 0.625), tileX: f((paletteIndex % 3) - 1), tileY: f((paletteIndex % 2) * 0.5), salt: paletteIndex + 3 }))
function render(spec, factory = canonicalFactory) {
  const input = syntheticInput(spec.width, spec.height, spec.salt); const before = new Uint32Array(input.data.buffer.slice(0));
  const uniforms = { tileOffset: new Float32Array([spec.tileX, spec.tileY]), fullResolution: new Float32Array([spec.width, spec.height]), paletteIndex: f(spec.paletteIndex), smoothness: f(spec.smoothness), rotation: f(spec.rotation), offset: f(spec.offset), repeat: f(spec.repeat), alpha: f(spec.alpha), time: f(spec.time) }
  const kernel = bindCanonicalKernel(factory, { width: spec.width, height: spec.height, time: spec.time, seed: 0, uniforms, textures: { inputTex: input }, tileOffset: uniforms.tileOffset, fullResolution: uniforms.fullResolution })
  const output = new Surface(spec.width, spec.height); runPass({ kernel, destination: output, time: spec.time, seed: 0, tileRows: 1 })
  return { inputWords: words(input.data), outputWords: words(output.data), outputBytes: Array.from(output.toRgba8()), inputUnchanged: same(Array.from(before), Array.from(new Uint32Array(input.data.buffer))), outputStorageDistinct: output.data !== input.data, outputObject: output, outputData: output.data }
}
function bindingRecord(spec, inputWords) {
  return {
    ...spec,
    inputTex: '<synthetic-input-surface>',
    tileOffset: [spec.tileX, spec.tileY],
    fullResolution: [spec.width, spec.height],
    binding_words: {
      tileOffset: { values: [spec.tileX, spec.tileY], f32_words_le: [f32Word(spec.tileX), f32Word(spec.tileY)] },
      fullResolution: { values: [spec.width, spec.height], f32_words_le: [f32Word(spec.width), f32Word(spec.height)] },
      inputTex: { width: spec.width, height: spec.height, f32_words_le: inputWords, f32_sha256: digestWords(inputWords) },
      paletteIndex: { value: spec.paletteIndex, int32: int32Word(spec.paletteIndex), f32_words_le: [f32Word(spec.paletteIndex)] },
      smoothness: { value: spec.smoothness, f32_words_le: [f32Word(spec.smoothness)] },
      rotation: { value: spec.rotation, int32: int32Word(spec.rotation), f32_words_le: [f32Word(spec.rotation)] },
      offset: { value: spec.offset, f32_words_le: [f32Word(spec.offset)] },
      repeat: { value: spec.repeat, f32_words_le: [f32Word(spec.repeat)] },
      alpha: { value: spec.alpha, f32_words_le: [f32Word(spec.alpha)] },
      time: { value: spec.time, f32_words_le: [f32Word(spec.time)] },
    },
  }
}
const rendered = cases.map(spec => { const first = render(spec); const second = render(spec); const repeatOutputObjectDistinct = first.outputObject !== second.outputObject; const repeatOutputDataDistinct = first.outputData !== second.outputData; if (!same(first.outputWords, second.outputWords) || !same(first.outputBytes, second.outputBytes)) throw new Error(`repeatability failed: ${spec.name}`); if (!first.inputUnchanged || !first.outputStorageDistinct || !repeatOutputObjectDistinct || !repeatOutputDataDistinct) throw new Error(`storage/input/repeat identity failed: ${spec.name}`); const inputHash = digestWords(first.inputWords); const binding = bindingRecord(spec, first.inputWords); return { ...spec, input: { width: spec.width, height: spec.height, f32_words_le: first.inputWords, f32_sha256: inputHash }, input_f32_words_le: first.inputWords, input_f32_sha256: inputHash, expected: { f32_words_le: first.outputWords, f32_sha256: digestWords(first.outputWords), rgba8_bytes: first.outputBytes, rgba8_sha256: digestBytes(first.outputBytes) }, input_immutable_exact_bits: true, input_lifetime: 'caller-owned-independent-surface', input_surface_not_released: true, bindings: binding, binding_words: binding.binding_words, repeat_identity: true, repeat_output_object_distinct: repeatOutputObjectDistinct, repeat_output_data_distinct: repeatOutputDataDistinct, public_direct_identity: true, independent_output_storage: true } })
const baseline = new Map(rendered.map(x => [x.name, x]))
const mutationDefs = [
  { name: 'index-lower-clamp', group: 'index-clamp', mechanism: 'change lower clamp from zero to one', anchor: 'Math.min(Math.max($bindings.paletteIndex | 0, 0), historicPaletteData.length - 1)', replacement: 'Math.min(Math.max($bindings.paletteIndex | 0, 1), historicPaletteData.length - 1)' },
  { name: 'smoothness-branch', group: 'smoothness', mechanism: 'force the helper smoothness input to zero', anchor: 'sampleHistoric(historicPaletteData[index], fract(t), $bindings.smoothness, color)', replacement: 'sampleHistoric(historicPaletteData[index], fract(t), 0, color)' },
  { name: 'palette-sample', group: 'palette-sample', mechanism: 'replace canonical palette sampling with zero color', anchor: 'sampleHistoric(historicPaletteData[index], fract(t), $bindings.smoothness, color)', replacement: 'color.fill(0)' },
  { name: 'rotation-backward', group: 'rotation', mechanism: 'reverse backward time direction', anchor: 'if ($bindings.rotation === -1) t += $bindings.time', replacement: 'if ($bindings.rotation === -1) t -= $bindings.time' },
  { name: 'fract-scale', group: 'fract-boundary', mechanism: 'remove bright-end 1e-4 scale', anchor: 'lum * (1 - 1e-4)', replacement: 'lum * 1' },
  { name: 'alpha-mix', group: 'alpha', mechanism: 'force alpha zero on red channel', anchor: 'mix(input[0], color[0], alpha)', replacement: 'mix(input[0], color[0], 0)' },
]
function mutateFactory(def) { const count = canonicalFactoryText.split(def.anchor).length - 1; if (count !== 1) throw new Error(`${def.name}: anchor cardinality ${count}, expected 1`); const source = canonicalFactoryText.replace(def.anchor, def.replacement); const factory = eval(`(${source})`); if (typeof factory !== 'function') throw new Error(`${def.name}: mutant did not evaluate`); return { source, factory, anchor_occurrence_count: count } }
function mismatch(reference, candidate) { const mismatched_lanes = changed(reference.expected.f32_words_le, candidate.outputWords); const mismatched_bytes = changed(reference.expected.rgba8_bytes, candidate.outputBytes); let first_mismatch = null; for (let i = 0; i < reference.expected.f32_words_le.length; i += 1) if (reference.expected.f32_words_le[i] !== candidate.outputWords[i]) { first_mismatch = { lane: i, reference: reference.expected.f32_words_le[i], candidate: candidate.outputWords[i] }; break } return { mismatched_lanes, mismatched_bytes, first_mismatch } }
const ledger = mutationDefs.map(def => { const mutant = mutateFactory(def); const results = cases.map(spec => ({ case: spec.name, ...mismatch(baseline.get(spec.name), render(spec, mutant.factory)) })); const witnesses = results.filter(x => x.mismatched_lanes > 0).map(x => x.case); if (!witnesses.length) throw new Error(`${def.name}: no behavioral witness`); return { name: def.name, group: def.group, mechanism: def.mechanism, independent: true, structural_only: false, source_relative_path: sourceRelative, source_sha256: sourceSha256, canonical_factory_text_sha256: factoryTextSha256, source_anchor: def.anchor, replacement: def.replacement, source_anchor_sha256: sha256(def.anchor), replacement_sha256: sha256(def.replacement), mutated_factory_text_sha256: sha256(mutant.source), anchor_occurrence_count: mutant.anchor_occurrence_count, required_witnesses: witnesses, required_witness_results: results.filter(x => x.mismatched_lanes > 0) } })
const comparerFixture = { width: 1, height: 1, f32_words_le: ['0x00000000', '0x80000000', '0x7fc00001', '0x3f800000'], rgba8_bytes: [0, 0, 127, 255] }
let dimensionsAccessed = false; const dimensionsActual = { width: 2, height: 1 }; Object.defineProperty(dimensionsActual, 'f32_words_le', { get() { dimensionsAccessed = true; return [] } }); const probe = fn => { try { fn(); return { rejected: false, message: '' } } catch (error) { return { rejected: true, message: String(error?.message || error) } } }
const comparerProbes = { good: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: [...comparerFixture.f32_words_le], rgba8_bytes: [...comparerFixture.rgba8_bytes] })), dimensions: probe(() => compareExact(comparerFixture, dimensionsActual, 'dimensions')), short: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: comparerFixture.f32_words_le.slice(0, 3) }, 'short')), long: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: [...comparerFixture.f32_words_le, '0x00000000'] }, 'long')), rgba8_count: probe(() => compareExact(comparerFixture, { ...comparerFixture, rgba8_bytes: [0, 1, 2] }, 'rgba8-count')), rgba8_mismatch: probe(() => compareExact(comparerFixture, { ...comparerFixture, rgba8_bytes: [0, 1, 126, 255] }, 'rgba8-mismatch')), f32_first: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x00000001', ...comparerFixture.f32_words_le.slice(1)] }, 'f32-first')), signed_zero: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x80000000', ...comparerFixture.f32_words_le.slice(1)] }, 'signed-zero')), nan_payload: probe(() => compareExact(comparerFixture, { ...comparerFixture, f32_words_le: ['0x00000000', '0x80000000', '0x7fc00002', '0x3f800000'] }, 'nan-payload')) }
const comparerSelfTests = { dimensions_before_access: comparerProbes.dimensions.rejected && !dimensionsAccessed, first_mismatch_reported: comparerProbes.f32_first.message.includes('first mismatch') && comparerProbes.rgba8_mismatch.message.includes('first mismatch'), raw_words_and_rgba8_independent: comparerProbes.rgba8_mismatch.rejected && comparerProbes.rgba8_mismatch.message.includes('RGBA8') && comparerProbes.f32_first.rejected && comparerProbes.f32_first.message.includes('Float32'), cases: { good: !comparerProbes.good.rejected, dimensions: comparerProbes.dimensions.rejected, short: comparerProbes.short.rejected, long: comparerProbes.long.rejected, rgba8_count: comparerProbes.rgba8_count.rejected, rgba8_mismatch: comparerProbes.rgba8_mismatch.rejected, signed_zero: comparerProbes.signed_zero.rejected, nan_payload: comparerProbes.nan_payload.rejected } }
if (!Object.values(comparerSelfTests.cases).every(Boolean)) throw new Error('comparer self-test failed')
const document = { schema: 'noisemaker-for-cpp.historic-palette.pixel-parity.v1', schema_version: 1, program_key: programKey, effect_key: 'filter/historicPalette', runtime_key: programKey, corpus_revision: corpusRevision, upstream_revision: upstreamRevision, factory: { name: 'historicPaletteFactory', text_sha256: factoryTextSha256, public_factory_is_canonical_identity: true, adapter_own_key: true }, runtime_binding_names: bindingNames, runtime_binding_abi: bindingAbi, canonical_binding_contract: { names: bindingNames, abi: bindingAbi }, exactness_contract: { float32: 'raw little-endian uint32 words; signed zero and NaN payloads significant', rgba8: 'complete independently captured RGBA8 bytes', tolerance: 'none', dimensions: 'checked before lane access', comparison: 'dimensions, counts, every uint32 word, every RGBA8 byte' }, comparer_self_tests: comparerSelfTests, provenance: { source: { relative_path: sourceRelative, sha256: sourceSha256 }, cpu_snapshot: { argument: '<immutable-cpu-snapshot-root>', immutable_snapshot: true, realpath_containment_checked: true, live_checkout_rejected: true, import_closure: actualClosure.map(([relative_path, sha256]) => ({ relative_path, sha256 })), closure_cardinality: actualClosure.length }, generator: { relative_path: 'docs/port-engineering/historic-palette-parity/historic_palette_oracle_generator.mjs', sha256: sha256(fs.readFileSync(generatorPath)) }, materializer: { relative_path: 'tools/glslcpp/generate_historic_palette_native_oracle_include.py' } }, render_cases: rendered, source_mutation_contract: { source_relative_path: sourceRelative, source_sha256: sourceSha256, canonical_factory_text_sha256: factoryTextSha256, execution: 'each exact canonical adapter factory anchor/replacement is evaluated and executed through bindCanonicalKernel/runPass' }, mutation_anchor_cardinality: { total: ledger.length, by_group: Object.fromEntries([...new Set(ledger.map(x => x.group))].map(group => [group, ledger.filter(x => x.group === group).length])), anchors: Object.fromEntries(ledger.map(x => [x.name, x.anchor_occurrence_count])) }, mutation_ledger: ledger, control_group: { repeatability: { identical_float32: true, identical_rgba8: true, distinct_output_objects: true, distinct_output_data: true }, input_immutability: { unchanged: true }, independent_output_storage: { distinct_data_objects: true }, public_direct_identity: true }, claim_boundaries: { absolute_paths: 'stable placeholders only', authority: 'unmodified public historicPaletteFactory from immutable CPU snapshot; no local reimplementation or C++ output participates', adapter: 'canonical adapter owns this key', mutations: 'exact source/factory anchor replacements are executed authority mutations' } }
rejectAbsolute(document)
const jsonPayload = Buffer.from(stable(document)); const report = Buffer.from(`# Historic Palette exact-pixel oracle\n\n- Program: ${programKey}\n- Authority: unmodified public canonical historicPaletteFactory from an immutable CPU snapshot.\n- Cases: ${rendered.length}; exact mutation ledger entries: ${ledger.length}.\n- The closure is transitively discovered, hash-pinned and realpath-confined.\n- Every palette index plus smoothness, wrap, rotation, fract, alpha, storage and comparer controls is covered.\n\n## Reproduction\n\nnode docs/port-engineering/historic-palette-parity/historic_palette_oracle_generator.mjs --check --cpu-root \"$NOISEMAKER_CPU_ROOT\"\npython3 -B tools/glslcpp/generate_historic_palette_native_oracle_include.py --check\n\nAbsolute checkout paths are intentionally omitted from this report and JSON.\n`)
function symlinkConfinementSelfTest() {
  const temporary = fs.mkdtempSync(path.join('/tmp', 'historic-palette-self-test-'))
  const authority = path.join(temporary, 'authority')
  const outside = path.join(temporary, 'outside')
  try {
    fs.mkdirSync(path.join(authority, 'src', 'effects'), { recursive: true })
    fs.mkdirSync(path.join(authority, 'src', 'effects', 'generated'), { recursive: true })
    fs.mkdirSync(path.join(authority, 'src', 'csl'), { recursive: true })
    fs.mkdirSync(path.join(authority, 'src', 'runtime'), { recursive: true })
    fs.mkdirSync(outside, { recursive: true })
    fs.writeFileSync(path.join(authority, 'src/effects/catalog.js'), "import './dependency.js'\n")
    for (const entry of [
      'src/effects/generated/upstream-snapshot.js',
      'src/csl/glsl-kernel.js',
      'src/csl/glsl-runtime.js',
      'src/runtime/pass-runner.js',
      'src/runtime/surface.js',
    ]) fs.writeFileSync(path.join(authority, entry), '')
    fs.writeFileSync(path.join(outside, 'dependency.js'), 'export const escaped = true\n')
    fs.symlinkSync(path.join(outside, 'dependency.js'), path.join(authority, 'src/effects/dependency.js'))
    try {
      closure(fs.realpathSync(authority))
      return false
    } catch (error) {
      return String(error?.message || error).includes('escaped immutable snapshot')
    }
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true })
  }
}
function selfTest() { const checks = [['factory identity', publicFactory === canonicalFactory], ['closure nonempty', actualClosure.length > 0], ['all palette indexes', rendered.length === 21 && rendered.every(x => x.expected.f32_words_le.length === x.width * x.height * 4 && x.expected.rgba8_bytes.length === x.width * x.height * 4)], ['input immutable', rendered.every(x => x.input_immutable_exact_bits)], ['mutation witnesses', ledger.every(x => x.independent && x.required_witnesses.length > 0)], ['comparer self-tests', Object.values(comparerSelfTests.cases).every(Boolean)], ['symlink confinement', symlinkConfinementSelfTest()]]; checks.forEach(([name, ok]) => console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}`)); return checks.every(([, ok]) => ok) ? 0 : 1 }
if (modes[0] === '--self-test') process.exit(selfTest())
if (modes[0] === '--write') { checked(outputPath, jsonPayload); checked(reportPath, report); checked(generatorPath, fs.readFileSync(generatorPath)); console.log(`historic palette oracle written (${jsonPayload.length} bytes, ${sha256(jsonPayload)})`) }
else { if (!verify(outputPath).equals(jsonPayload) || !verify(reportPath).equals(report) || !verify(generatorPath).equals(fs.readFileSync(generatorPath))) throw new Error('historic palette oracle package drift'); console.log('historic palette oracle: ok') }
