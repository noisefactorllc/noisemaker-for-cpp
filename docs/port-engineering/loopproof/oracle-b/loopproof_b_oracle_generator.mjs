import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { canonicalAdapterFactories, canonicalKernelFactories, kernelFactories } from '../../../../../noisemaker-for-cpu/src/effects/catalog.js'
import { createCanonicalBindings } from '../../../../../noisemaker-for-cpu/src/csl/glsl-kernel.js'
import { bindGlslKernel } from '../../../../../noisemaker-for-cpu/src/csl/glsl-runtime.js'
import { runPass } from '../../../../../noisemaker-for-cpu/src/runtime/pass-runner.js'
import { Surface } from '../../../../../noisemaker-for-cpu/src/runtime/surface.js'

// ---------------------------------------------------------------------------
// Loop-proof cluster oracle-b -- the EXPENSIVE half of the eight-program
// loop-proof-blocked cluster named in the task brief:
//
//   classicNoisedeck/effects:effects    classicNoisedeck/fractal:fractal
//   classicNoisedeck/noise:noise        synth/noise:noise
//   synth/mandelbrot:mandelbrot         synth/testPattern:testPattern
//   filter/reindex:nmReindexReduce      filter/median:median
//
// Mirrors docs/port-engineering/loopproof/oracle-a/loopproof_a_oracle_generator.mjs
// (same hermeticity pinning, same renderCase()/mutateFactoryText() discipline,
// same reach/divergence machine-assertion), extended for THREE traps oracle-a
// did not have to deal with:
//
//   (1) TWO of the eight (`filter/median:median`, `classicNoisedeck/fractal:fractal`)
//       are NOT reachable through a canonical GLSL-transpiled kernel at all --
//       verified live below, not assumed. `fractal` has ZERO canonical entry
//       (manifest status "adapter", `compile-glsl.js`'s explicit skip list,
//       `generatedBytes: 0` in glsl-coverage.js -- a PERMANENT architectural
//       routing, not a loop-proof side effect: the adapter's julia/newton/
//       mandelbrot sub-fractal engine is a hand JS port of an OLDER algorithm,
//       unrelated to the corpus fractal.glsl source this generator does NOT
//       use). `median` DOES have a canonical factory (canonicalFactory80) but
//       it is shadowed by `canonicalAdapterFactories['filter/median:median']`
//       in the live public routing -- and empirically, canonicalFactory80
//       CRASHES on a 5x5 render that the adapter handles fine (see the
//       "median canonical factory defect" section below). Both are oracled
//       against their real, working ADAPTER instead, via a module-text-copy
//       + `data:` URL dynamic import (adapters nest their helpers at MODULE
//       scope, not inside the factory closure, so the canonical-kernel
//       `eval(factory.toString())` trick does not reach them).
//   (2) `filter/median:median`'s quickselect has a genuine INFINITE-LOOP trap
//       in its inner Hoare-partition boundary (`scanLeft <= scanRight` -> `<`
//       loses the convergence invariant and the outer loop never terminates --
//       verified live, hung >120s, killed under watchdog). That mutation site
//       is AVOIDED entirely; both median mutations instead wrap the OUTER
//       `while (left < right)` convergence loop in a hard iteration cap that
//       provably terminates by construction.
//   (3) `classicNoisedeck/effects:effects` is UNCOVERABLE for a THIRD reason
//       distinct from oracle-a's dither crash and from (1) above: its EFFECT
//       define genuinely IS bound as a runtime uniform (`var EFFECT =
//       $bindings["EFFECT"]`, matching the defines-bound-as-uniforms lesson),
//       but the entire effect-dispatch block (containing every loop in the
//       file: convolve's 3x3 kernel loop, bloom's -4..4 nested loop, zoomBlur's
//       0..40 loop) is gated behind `if (EFFECT != 0) { if (effectAmt != 0) {`
//       in `main()`, and the authorized define is EFFECT=0. Verified live: a
//       loop mutation on `convolve()` shows ZERO divergence at EFFECT=0 across
//       four different effectAmt values, and NONZERO divergence at the SAME
//       mutation under an unauthorized EFFECT=1 -- proving the loop is real
//       and the mutation is real, but genuinely dead at the one define value
//       this task's reachability rule authorizes.
//
// THE TOP-LEVEL-BINDING LESSON, applied throughout (glsl-kernel.js:20-61):
// nine canonical keys are assigned AFTER the `...uniforms` spread, so passing
// any of them *inside* uniforms silently discards the caller's intended
// value. Every canonical-factory case renders through `renderCase()`, which
// refuses to build if `uniforms` illegally contains one of these keys and
// independently reconstructs bindings to assert the kernel's own bound values
// equal the caller's intent. The two adapter-routed programs (median,
// fractal) go through the same reserved-key guard in `renderAdapterCase()`.
// ---------------------------------------------------------------------------

const here = path.dirname(fileURLToPath(import.meta.url))
// noisemaker-for-cpp repo root is 4 levels up from this file
// (oracle-b -> loopproof -> port-engineering -> docs -> repo root); resolved
// via `here` (import.meta.url-derived) so this generator behaves identically
// regardless of the invoking shell's CWD -- every filesystem path below is
// built from `repoRoot`/`cpuRepoRoot`, never a bare CWD-relative string.
const repoRoot = path.resolve(here, '../../../..')
const cpuRepoRoot = path.resolve(repoRoot, '..', 'noisemaker-for-cpu')
const outPath = path.join(here, 'loopproof-b-oracles.json')
const reportPath = path.join(here, 'loopproof-b-oracle-report.md')
const revision = 'a024dc3a960cc44af454abc7aebce50456c194e6'
const corpusRoot = path.join(repoRoot, `tools/glslcpp/corpus/${revision}`)
const glslKernelPath = path.join(cpuRepoRoot, 'src/csl/glsl-kernel.js')
const glslRuntimePath = path.join(cpuRepoRoot, 'src/csl/glsl-runtime.js')
const passRunnerPath = path.join(cpuRepoRoot, 'src/runtime/pass-runner.js')
const surfacePath = path.join(cpuRepoRoot, 'src/runtime/surface.js')
const catalogPath = path.join(cpuRepoRoot, 'src/effects/catalog.js')
const canonicalPath = path.join(cpuRepoRoot, 'src/effects/generated/canonical-kernels.js')
const adapterPath = path.join(cpuRepoRoot, 'src/effects/adapters/index.js')
const fractalAdapterSourcePath = path.join(cpuRepoRoot, 'src/effects/adapters/fractal.js')
const medianAdapterSourcePath = path.join(cpuRepoRoot, 'src/effects/adapters/median.js')
const f = Math.fround

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function bytes(value) { return Buffer.from(value.buffer, value.byteOffset, value.byteLength) }
function f32Bits(value) {
  if (Number.isNaN(value)) return 'nan'
  const a = new Float32Array([value])
  return `0x${new DataView(a.buffer).getUint32(0, true).toString(16).padStart(8, '0')}`
}
function sameBytes(a, b) { return Buffer.compare(bytes(a.data), bytes(b.data)) === 0 }
function evaluated(text) { return (0, eval)(`(${text})`) }
function occurrences(text, needle) { return text.split(needle).length - 1 }
async function loadModuleExport(sourceText, exportName) {
  const mod = await import(`data:text/javascript;base64,${Buffer.from(sourceText).toString('base64')}`)
  return mod[exportName]
}

function checkpoint(id, payload) {
  const p = path.join(here, `partial-${id}.json`)
  const json = `${JSON.stringify(payload, null, 2)}\n`
  fs.writeFileSync(p, json)
  fs.writeFileSync(`${p}.sha256`, `${sha256(json)}  ${path.basename(p)}\n`)
  console.log(`[checkpoint] ${id}: wrote ${path.basename(p)}`)
}

// ---------------------------------------------------------------------------
// Runtime/catalog hermeticity pinning -- independently recomputed against the
// live tree, matching oracle-a's/grade's pinned values exactly (same repo
// state at generation time), plus the two adapter SOURCE FILES this generator
// additionally depends on (fractal.js, median.js), which oracle-a never
// touched.
// ---------------------------------------------------------------------------
const RUNTIME_PROVENANCE = {
  glsl_kernel_sha256: 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa',
  glsl_runtime_sha256: 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072',
  pass_runner_sha256: 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa',
  surface_sha256: '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59',
  public_catalog_sha256: 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4',
  canonical_kernels_sha256: 'e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56',
  adapter_index_sha256: '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267',
  fractal_adapter_source_sha256: '67266ec1ade502d9ddf7032cff0f905162faf898c1dbfcafc4ba191e2ca8e4ac',
  median_adapter_source_sha256: 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583',
}
for (const [file, hash] of [
  [glslKernelPath, RUNTIME_PROVENANCE.glsl_kernel_sha256],
  [glslRuntimePath, RUNTIME_PROVENANCE.glsl_runtime_sha256],
  [passRunnerPath, RUNTIME_PROVENANCE.pass_runner_sha256],
  [surfacePath, RUNTIME_PROVENANCE.surface_sha256],
  [catalogPath, RUNTIME_PROVENANCE.public_catalog_sha256],
  [canonicalPath, RUNTIME_PROVENANCE.canonical_kernels_sha256],
  [adapterPath, RUNTIME_PROVENANCE.adapter_index_sha256],
  [fractalAdapterSourcePath, RUNTIME_PROVENANCE.fractal_adapter_source_sha256],
  [medianAdapterSourcePath, RUNTIME_PROVENANCE.median_adapter_source_sha256],
]) {
  if (sha256(fs.readFileSync(file)) !== hash) throw new Error(`runtime drift: ${file}`)
}

// ---------------------------------------------------------------------------
// Lesson 1: reserved top-level keys + full intended-binding verification.
// ---------------------------------------------------------------------------
const RESERVED_TOP_LEVEL_KEYS = ['time', 'globalTime', 'deltaTime', 'frame', 'tileOffset', 'fullResolution', 'resolution', 'aspect', 'aspectRatio']
function assertNoReservedKeysInUniforms(uniforms) {
  for (const k of RESERVED_TOP_LEVEL_KEYS) {
    if (Object.prototype.hasOwnProperty.call(uniforms, k)) {
      throw new Error(`uniforms illegally contains reserved top-level-only key "${k}" -- createCanonicalBindings assigns this AFTER spreading ...uniforms, so it would be silently discarded`)
    }
  }
}

function normalizeUniformsTyped(typeMap, raw) {
  const out = {}
  for (const [k, v] of Object.entries(raw)) {
    const type = typeMap[k]
    if (!type) throw new Error(`unknown uniform "${k}" -- not declared in this program's type map (check for typos or a missing entry)`)
    if (type === 'bool') out[k] = Boolean(v)
    else if (type === 'int') out[k] = v | 0
    else if (type === 'float') out[k] = f(v)
    else if (type === 'vec2' || type === 'vec3' || type === 'vec4') out[k] = new Float32Array(v.map(f))
    else throw new Error(`unhandled uniform type "${type}" for "${k}"`)
  }
  return out
}

function patternedSurface(width, height, phase) {
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4
      data[i] = f((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
      data[i + 1] = f((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
      data[i + 2] = f((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
      data[i + 3] = f((((7 * x + 11 * y + phase) % 29) + (phase ? 2 : 13)) / 43)
    }
  }
  return new Surface(width, height, data)
}

function probe(surface, x, y) {
  const i = (y * surface.width + x) * 4
  const values = Array.from(surface.data.slice(i, i + 4))
  return { at_top_down_xy: [x, y], values, f32_bits_le: values.map(f32Bits) }
}
function probes(surface) {
  return [[0, 0], [surface.width - 1, 0], [0, surface.height - 1], [surface.width - 1, surface.height - 1], [Math.floor(surface.width / 2), Math.floor(surface.height / 2)]].map(([x, y]) => probe(surface, x, y))
}
function renderResult(surface) {
  const rgba = surface.toRgba8()
  let nonfinite = 0
  for (const lane of surface.data) if (!Number.isFinite(lane)) nonfinite += 1
  return { f32_sha256: sha256(bytes(surface.data)), rgba8_sha256: sha256(bytes(rgba)), finite_lanes: surface.data.length - nonfinite, nonfinite_lanes: nonfinite, probes: probes(surface) }
}

// ---------------------------------------------------------------------------
// renderCase: canonical-kernel rendering path (nmReindexReduce, mandelbrot,
// median-CRASH-EVIDENCE-ONLY, classicNoisedeck/noise, synth/noise,
// testPattern, effects-EVIDENCE-ONLY) -- identical discipline to oracle-a.
// ---------------------------------------------------------------------------
function renderCase(program, c) {
  assertNoReservedKeysInUniforms(c.uniforms)
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures ? program.buildTextures(c) : {}
  const inputBytesBefore = {}
  for (const [name, tex] of Object.entries(textures)) inputBytesBefore[name] = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')

  const time = c.time ?? 0
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const intendedTileOffset = tileOffset ?? new Float32Array(2)
  const intendedFullResolution = fullResolution ?? new Float32Array([c.width, c.height])

  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time })
  if (f32Bits(bindings.time) !== f32Bits(f(time))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended time -- top-level binding lesson violated`)
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended tileOffset`)
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended fullResolution`)
  for (const [k, v] of Object.entries(uniforms)) {
    const bound = bindings[k]
    const same = ArrayBuffer.isView(v)
      ? Array.from(v).every((x, i) => f32Bits(x) === f32Bits(bound[i]))
      : (typeof v === 'boolean' ? bound === v : f32Bits(typeof v === 'number' ? f(v) : v) === f32Bits(typeof bound === 'number' ? f(bound) : bound))
    if (!same) throw new Error(`${program.id}/${c.name}: kernel did not observe intended uniform "${k}" -- reserved-key or spread-order defect`)
  }
  for (const [k, v] of Object.entries(program.defines ?? {})) {
    const bound = bindings[k]
    if (f32Bits(typeof v === 'number' ? f(v) : v) !== f32Bits(typeof bound === 'number' ? f(bound) : bound)) {
      throw new Error(`${program.id}/${c.name}: kernel did not observe authorized define "${k}"=${v} -- defines-bound-as-uniforms lesson violated`)
    }
  }

  const kernel = bindGlslKernel(program.canonical, bindings)
  const first = new Surface(c.width, c.height)
  runPass({ kernel, destination: first })
  for (const [name, tex] of Object.entries(textures)) {
    const after = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')
    if (inputBytesBefore[name] !== after) throw new Error(`${program.id}/${c.name}: input texture "${name}" was mutated by render`)
  }
  const kernel2 = bindGlslKernel(program.canonical, bindings)
  const second = new Surface(c.width, c.height)
  runPass({ kernel: kernel2, destination: second })
  if (!sameBytes(first, second)) throw new Error(`${program.id}/${c.name}: repeat-render mismatch`)

  return { name: c.name, surface: first, c }
}

function renderWithFactory(program, c, factory) {
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures ? program.buildTextures(c) : {}
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time: c.time ?? 0 })
  const kernel = bindGlslKernel(factory, bindings)
  const surface = new Surface(c.width, c.height)
  runPass({ kernel, destination: surface })
  return surface
}

function mutateFactoryText(factoryText, mutation) {
  if (occurrences(factoryText, mutation.anchor) !== 1) throw new Error(`mutation anchor not unique/found: ${mutation.id}`)
  return factoryText.replace(mutation.anchor, mutation.mutated)
}

// ---------------------------------------------------------------------------
// Adapter-path rendering: median.js / fractal.js nest their per-lane helper
// functions (packRecordMajor/lessRecord/swap for median; julia/newton/
// mandelbrot/hsvToRgb/palette for fractal) at MODULE scope, not inside the
// exported factory closure -- so the canonical-kernel `eval(factory.
// toString())` trick used above cannot see them (toString() only captures
// the factory function's own body, which just calls the module-level names
// by reference). Instead: read the module's raw SOURCE TEXT, apply the same
// textual anchor/replace mutation discipline to that text, and load the
// (real or mutated) module via a `data:` URL dynamic import -- verified
// working before use (a throwaway `export function foo(x){return x+1}`
// round-tripped through this exact mechanism). No filesystem write, no /tmp,
// no modification to the source tree; the mutated text lives only in memory
// for the duration of one `import()` call.
// ---------------------------------------------------------------------------
async function renderAdapterCase(program, c) {
  assertNoReservedKeysInUniforms(c.uniforms)
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures ? program.buildTextures(c) : {}
  const inputBytesBefore = {}
  for (const [name, tex] of Object.entries(textures)) inputBytesBefore[name] = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')

  const time = c.time ?? 0
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const intendedTileOffset = tileOffset ?? new Float32Array(2)
  const intendedFullResolution = fullResolution ?? new Float32Array([c.width, c.height])

  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time })
  if (f32Bits(bindings.time) !== f32Bits(f(time))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended time -- top-level binding lesson violated`)
  if (f32Bits(bindings.tileOffset[0]) !== f32Bits(f(intendedTileOffset[0])) || f32Bits(bindings.tileOffset[1]) !== f32Bits(f(intendedTileOffset[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended tileOffset`)
  if (f32Bits(bindings.fullResolution[0]) !== f32Bits(f(intendedFullResolution[0])) || f32Bits(bindings.fullResolution[1]) !== f32Bits(f(intendedFullResolution[1]))) throw new Error(`${program.id}/${c.name}: kernel did not observe intended fullResolution`)
  for (const [k, v] of Object.entries(uniforms)) {
    const bound = bindings[k]
    const same = ArrayBuffer.isView(v)
      ? Array.from(v).every((x, i) => f32Bits(x) === f32Bits(bound[i]))
      : (typeof v === 'boolean' ? bound === v : f32Bits(typeof v === 'number' ? f(v) : v) === f32Bits(typeof bound === 'number' ? f(bound) : bound))
    if (!same) throw new Error(`${program.id}/${c.name}: kernel did not observe intended uniform "${k}"`)
  }

  const factory = await loadModuleExport(program.moduleSourceText, program.exportName)
  const kernel = bindGlslKernel(factory, bindings)
  const first = new Surface(c.width, c.height)
  runPass({ kernel, destination: first })
  for (const [name, tex] of Object.entries(textures)) {
    const after = Buffer.from(tex.data.buffer, tex.data.byteOffset, tex.data.byteLength).toString('hex')
    if (inputBytesBefore[name] !== after) throw new Error(`${program.id}/${c.name}: input texture "${name}" was mutated by render`)
  }
  const factory2 = await loadModuleExport(program.moduleSourceText, program.exportName)
  const kernel2 = bindGlslKernel(factory2, bindings)
  const second = new Surface(c.width, c.height)
  runPass({ kernel: kernel2, destination: second })
  if (!sameBytes(first, second)) throw new Error(`${program.id}/${c.name}: repeat-render mismatch`)

  return { name: c.name, surface: first, c }
}

async function renderAdapterWithMutatedSource(program, c, mutatedSourceText) {
  const uniforms = normalizeUniformsTyped(program.uniformTypes, c.uniforms)
  const textures = program.buildTextures ? program.buildTextures(c) : {}
  const tileOffset = c.tileOffset ? new Float32Array(c.tileOffset) : undefined
  const fullResolution = c.fullResolution ? new Float32Array(c.fullResolution) : undefined
  const bindings = createCanonicalBindings({ width: c.width, height: c.height, uniforms, textures, tileOffset, fullResolution, time: c.time ?? 0 })
  const factory = await loadModuleExport(mutatedSourceText, program.exportName)
  const kernel = bindGlslKernel(factory, bindings)
  const surface = new Surface(c.width, c.height)
  runPass({ kernel, destination: surface })
  return surface
}

// =============================================================================
// PROGRAM 1: filter/reindex:nmReindexReduce
// =============================================================================
// Loop-proof site: `for (var ty = 0; ty < MAX_TILE_DIM; ++ty) { ... for (var
// tx = 0; tx < MAX_TILE_DIM; ++tx) { ... } }`, MAX_TILE_DIM = 512 (the "512x512
// nested product, ~64x over cap" the task brief calls out) -- but the ACTUAL
// per-render trip count is bounded by `break` on `tx>=tileCount.x` /
// `ty>=tileCount.y`, where tileCount = ceil(statsTexSize/TILE_SIZE=8). The
// render's own OUTPUT canvas is a single pixel by construction ("Single pixel
// output; ensure only the first fragment runs the reduction" -- verified live
// in the compiled JS: `if (gl_FragCoord!=(0,0)) { fragColor=0; return; }`), so
// cost is O(tileCount.x*tileCount.y) texel fetches at a 1x1 destination
// canvas regardless of how large statsTex nominally is -- cheap even at the
// largest statsTex used here (33x33, tileCount 5x5, 25 fetches).
//
// Mutation target: the SHARED `var MAX_TILE_DIM = 512;` global -- ONE symbol
// caps BOTH nested loops (unlike a per-axis bound), so per-case statsTex
// dimensions are chosen to isolate which axis a given case's divergence
// comes from. `texelFetch` flips Y (`glsl-runtime.js:206`, `y = height-1-
// shaderY`, verified live with a marker sweep below, matching the lesson
// already documented in oracle-a's statsFinal design note) -- `placeTile()`
// accounts for this so a case's intended shader-space tile (tx,ty) lands at
// the correct TOP-DOWN data row.
const nmReindexReduce = (() => {
  const key = 'filter/reindex:nmReindexReduce'
  const sourceFile = 'nmReindexReduce.glsl'
  const sourceRawBytes = 1331
  const sourceSha256 = '5e9701125522aaa1f838858a7892ac1312f1161608a5f94b494ae64c7db8b7ff'
  const factoryName = 'canonicalFactory119'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/filter/reindex', sourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== sourceRawBytes) throw new Error('nmReindexReduce: source raw byte count drift')
    if (sha256(sourceBytes) !== sourceSha256) throw new Error('nmReindexReduce: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('nmReindexReduce: canonical factory missing')
    if (canonical.name !== factoryName) throw new Error(`nmReindexReduce: factory name drift (got ${canonical.name})`)
    if (kernelFactories.get(key) !== canonical) throw new Error('nmReindexReduce: public factory is not the canonical identity')
    if (canonicalAdapterFactories[key] !== undefined) throw new Error('nmReindexReduce: unexpected adapter override present')
    return { sourcePath, canonical, factoryText: canonical.toString() }
  }

  function placeTile(data, w, h, tx, ty, minV, maxV) {
    // texelFetch(statsTex, (tx*8, ty*8)) reads TOP-DOWN data row (h-1-ty*8),
    // column tx*8 -- verified live via a marker sweep (dataRow=height-1-
    // shaderY matched exactly for shaderY in {0,8,16} against a 24-row probe
    // texture; the naive un-flipped placement was tried FIRST and produced
    // WRONG divergence attribution (case2/case3/case4 all read background
    // 0.5 instead of the placed marker) until this flip was applied -- the
    // exact "verify empirically, don't assume" trap the task warns about,
    // now paid down once here rather than per-case.
    const row = h - 1 - ty * 8
    const col = tx * 8
    const idx = (row * w + col) * 4
    data[idx] = f(minV)
    data[idx + 1] = f(maxV)
  }
  function statsSurface(width, height, tiles) {
    const data = new Float32Array(width * height * 4)
    for (let i = 0; i < width * height; i += 1) { data[i * 4] = f(0.5); data[i * 4 + 1] = f(0.5); data[i * 4 + 3] = 1 }
    for (const [tx, ty, minV, maxV] of tiles) placeTile(data, width, height, tx, ty, minV, maxV)
    return new Surface(width, height, data)
  }
  function tileCountOf(statsWidth, statsHeight) {
    return { x: Math.ceil(statsWidth / 8), y: Math.ceil(statsHeight / 8) }
  }

  const cases = [
    {
      name: 'min-in-last-row-y-axis', width: 1, height: 1,
      statsWidth: 16, statsHeight: 33, tiles: [[0, 4, 0.01, 0.5], [0, 0, 0.5, 0.9]],
      uniforms: {},
    },
    {
      name: 'max-in-last-col-x-axis', width: 1, height: 1,
      statsWidth: 33, statsHeight: 16, tiles: [[4, 0, 0.5, 0.95], [0, 0, 0.05, 0.5]],
      uniforms: {},
    },
    {
      name: 'small-3x3-grid-multi-tile-drop', width: 1, height: 1,
      statsWidth: 20, statsHeight: 20, tiles: [[2, 1, 0.02, 0.5], [1, 2, 0.5, 0.92]],
      uniforms: {},
    },
    {
      name: 'single-tile-diagnostic', width: 1, height: 1,
      statsWidth: 8, statsHeight: 8, tiles: [[0, 0, 0.1, 0.9]],
      uniforms: {}, diagnostic: true,
    },
  ]

  const mutations = [
    {
      id: 'nmReindexReduce-tile-cap-off-by-one', kind: 'trip_count_off_by_one', reachKey: 'offByOne',
      anchor: 'var MAX_TILE_DIM = 512;', mutated: 'var MAX_TILE_DIM = 4;',
      description: 'Shrink the shared tile-scan cap from 512 to 4: drops tile row/col index 4 from BOTH nested loops (they share one symbol). Reach-eligible exactly when a case\'s tileCount.x or tileCount.y exceeds 4.',
    },
    {
      id: 'nmReindexReduce-tile-cap-swap', kind: 'trip_count_swap', reachKey: 'swap',
      anchor: 'var MAX_TILE_DIM = 512;', mutated: 'var MAX_TILE_DIM = 1;',
      description: 'Shrink the shared tile-scan cap to 1: a materially wrong trip count, visiting only tile (0,0) regardless of true tileCount. Reach-eligible whenever a case\'s tileCount.x or tileCount.y exceeds 1.',
    },
  ]

  function buildTextures(c) { return { statsTex: statsSurface(c.statsWidth, c.statsHeight, c.tiles) } }

  // reach: derived directly from tileCount vs. each mutation's cap --
  // verified live below (not merely computed) via the same
  // renderWithFactory() machine-assertion every other program's mutations
  // go through.
  const reachByCase = {}
  for (const c of cases) {
    const tc = tileCountOf(c.statsWidth, c.statsHeight)
    reachByCase[c.name] = { offByOne: tc.x > 4 || tc.y > 4, swap: tc.x > 1 || tc.y > 1 }
  }

  return { id: 'nmReindexReduce', key, uniformTypes: {}, defines: {}, loadProgram, statsSurface, tileCountOf, buildTextures, cases, mutations, reachByCase }
})()

// =============================================================================
// PROGRAM 2: synth/mandelbrot:mandelbrot
// =============================================================================
// Loop-proof site: `for (var n = 0; n < MAX_ITER; n++) { if (n>=maxIter)
// break; ... }`, MAX_ITER = 500 (the task brief's "up to 500 iterations per
// pixel"). `maxIter = min(iterations, MAX_ITER)` is a SEPARATE runtime clamp
// computed from the `iterations` uniform -- the mutation anchors ONLY the
// for-loop's own static bound text, leaving that clamp computation untouched,
// so with `iterations=500` the real render's behavior is governed entirely by
// the static 500 cap (maxIter=500=MAX_ITER exactly).
//
// Discrimination trap (named explicitly in the task brief): most Mandelbrot
// samples escape in a handful of iterations, insensitive to any believable
// cap. Calibrated empirically (a throwaway double-precision escape-time probe
// used ONLY to pick literal center coordinates, independent of the oracle's
// actual proof, which always renders through the real df64 factory): a 1x1
// canvas at effective zoom 1 (zoomDepth=0) makes pixel (0,0) sample the
// `center` uniform EXACTLY (uv=(0,0) when fullResolution=(1,1)), giving exact
// control over which c-value is tested. c=(-1.256,0) is a real point on the
// Mandelbrot set's real-axis segment [-2,0.25] (verified NOT cardioid/
// period-2-bulb, so it is not shortcut by the early-out) -- it runs the FULL
// 500-iteration loop without escaping, making it maximally sensitive to any
// cap below 500. Verified live: diverges under a cap of 499 AND a cap of 80.
const mandelbrotProgram = (() => {
  const key = 'synth/mandelbrot:mandelbrot'
  const sourceFile = 'mandelbrot.glsl'
  const sourceRawBytes = 14855
  const sourceSha256 = '0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615'
  const factoryName = 'canonicalFactory252'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/synth/mandelbrot', sourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== sourceRawBytes) throw new Error('mandelbrot: source raw byte count drift')
    if (sha256(sourceBytes) !== sourceSha256) throw new Error('mandelbrot: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('mandelbrot: canonical factory missing')
    if (canonical.name !== factoryName) throw new Error(`mandelbrot: factory name drift (got ${canonical.name})`)
    if (kernelFactories.get(key) !== canonical) throw new Error('mandelbrot: public factory is not the canonical identity')
    if (canonicalAdapterFactories[key] !== undefined) throw new Error('mandelbrot: unexpected adapter override present')
    return { sourcePath, canonical, factoryText: canonical.toString() }
  }

  const uniformTypes = {
    poi: 'int', outputMode: 'int', iterations: 'int',
    centerHiX: 'float', centerHiY: 'float', centerLoX: 'float', centerLoY: 'float',
    zoomSpeed: 'float', zoomDepth: 'float', invert: 'float', stripeFreq: 'float',
    trapShape: 'int', lightAngle: 'float', rotation: 'float',
  }
  function baseUniforms(cx, cy) {
    return { poi: 0, outputMode: 0, iterations: 500, centerHiX: cx, centerHiY: cy, centerLoX: 0, centerLoY: 0, zoomSpeed: 0, zoomDepth: 0, invert: 0, stripeFreq: 0, trapShape: 0, lightAngle: 0, rotation: 0 }
  }

  // Empirically calibrated (see module header): all five points verified
  // live via a probe render at iterations=500 BEFORE being locked in here,
  // not assumed from the cardioid/bulb formulas alone.
  const cases = [
    { name: 'never-escapes-real-axis-boundary', width: 1, height: 1, uniforms: baseUniforms(-1.256, 0.0) },
    { name: 'moderate-escape-273-seahorse-tip', width: 1, height: 1, uniforms: baseUniforms(-0.74543, 0.11301) },
    { name: 'slow-escape-112-seahorse-alt', width: 1, height: 1, uniforms: baseUniforms(-0.7269, 0.1889) },
    { name: 'cardioid-early-out-diagnostic', width: 1, height: 1, uniforms: baseUniforms(0.0, 0.0), diagnostic: true },
    { name: 'fast-escape-far-outside-diagnostic', width: 1, height: 1, uniforms: baseUniforms(2.5, 2.5), diagnostic: true },
  ]

  // reach: computed from the SAME live probe used to calibrate the cases
  // (not re-derived here) -- documented per case:
  //   never-escapes (true rawIter=500): reach for BOTH caps (499 and 80).
  //   moderate-273 / slow-112 (true escape 273 / 112): reach for the cap=80
  //     mutation only -- 273 and 112 both exceed 80, but neither exceeds 499,
  //     so the off-by-one (cap 499) mutation is expected-zero for these two
  //     -- exactly the smoothBlend-style "engineered for a DIFFERENT
  //     mutation" case oracle-a's design notes call for, verified live below.
  //   cardioid / fast-escape: structurally non-reaching (cardioid hits the
  //     early-out before the loop; fast-escape breaks in 1-2 iterations, far
  //     under either cap) -- verified live, zero divergence under both caps.
  const reachByCase = {
    'never-escapes-real-axis-boundary': { offByOne: true, swap: true },
    'moderate-escape-273-seahorse-tip': { offByOne: false, swap: true },
    'slow-escape-112-seahorse-alt': { offByOne: false, swap: true },
    'cardioid-early-out-diagnostic': { offByOne: false, swap: false },
    'fast-escape-far-outside-diagnostic': { offByOne: false, swap: false },
  }

  const mutations = [
    {
      id: 'mandelbrot-max-iter-off-by-one', kind: 'trip_count_off_by_one', reachKey: 'offByOne',
      anchor: 'for (var n = 0; n < MAX_ITER; n++) {', mutated: 'for (var n = 0; n < 499; n++) {',
      description: 'Drop the static cap from 500 to 499 -- the smallest possible wrong trip count. Only the never-escapes case (true rawIter=500) reaches a cap this close to the real bound.',
    },
    {
      id: 'mandelbrot-max-iter-swap', kind: 'trip_count_swap', reachKey: 'swap',
      anchor: 'for (var n = 0; n < MAX_ITER; n++) {', mutated: 'for (var n = 0; n < 80; n++) {',
      description: 'Shrink the static cap to 80 -- a materially wrong trip count. Reach-eligible for all three non-diagnostic cases (true iteration counts 500/273/112, all exceeding 80).',
    },
  ]

  return { id: 'mandelbrot', key, uniformTypes, defines: {}, loadProgram, cases, mutations, reachByCase }
})()

// =============================================================================
// PROGRAM 3: filter/median:median (ADAPTER-ROUTED -- see module header (1)+(2))
// =============================================================================
// The canonical GLSL-transpiled kernel (canonicalFactory80) exists and its
// factory text carries the exact same quickselect shape as median.glsl --
// but it CRASHES on rendering a plain 5x5 patterned image (verified live,
// `TypeError: Cannot read properties of undefined (reading 'length')` inside
// $runtime.copy, called from the transpiled `lessRecord`), while the SAME
// input renders fine at 4x4, 6x6, and through `medianFactory` (the adapter)
// at every size tried. This is a genuine, previously-undocumented defect in
// noisemaker-for-cpu's transpiled median kernel, independent of and
// orthogonal to the loop-proof gate -- captured live below as hard evidence,
// analogous to oracle-a's dither `errRow[i]` crash. Because the canonical
// path cannot serve as ground truth, this generator builds its oracle
// against `medianFactory` (`src/effects/adapters/median.js`) -- a faithful,
// WORKING hand port of the identical Hoare-partition quickselect algorithm
// (same `while(left<right){ while(scanLeft<=scanRight){ inner whiles } }`
// shape, same half-float pack/unpack scheme), exactly the "adapter as
// JS-golden ground truth" precedent set by the wormhole:deposit oracle in
// REMAINING-WORK-ROADMAP.md.
const medianProgram = (() => {
  const key = 'filter/median:median'
  const canonicalFactoryName = 'canonicalFactory80'
  const canonicalSourceFile = 'median.glsl'
  const canonicalSourceRawBytes = 3846
  const canonicalSourceSha256 = '95e869c02fe2645f4a1b5af5a7446b3f2bacb888f2c965bc272ba56b10666e5d'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/filter/median', canonicalSourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== canonicalSourceRawBytes) throw new Error('median: source raw byte count drift')
    if (sha256(sourceBytes) !== canonicalSourceSha256) throw new Error('median: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('median: canonical factory unexpectedly missing (expected present-but-broken)')
    if (canonical.name !== canonicalFactoryName) throw new Error(`median: canonical factory name drift (got ${canonical.name})`)
    const adapter = canonicalAdapterFactories[key]
    if (adapter === undefined) throw new Error('median: expected adapter override to be present (routing changed)')
    if (kernelFactories.get(key) !== adapter) throw new Error('median: public factory is not the adapter (routing changed)')
    if (adapter.name !== 'medianFactory') throw new Error(`median: adapter factory name drift (got ${adapter.name})`)
    const moduleSourceText = fs.readFileSync(path.resolve(here, medianAdapterSourcePath), 'utf8')
    return { sourcePath, canonical, moduleSourceText }
  }

  // ---- Live evidence: the canonical factory's crash, captured mechanically
  // (not merely asserted) -- and proof the crash is data-dependent (4x4 and
  // 6x6 render fine, 5x5 does not), ruling out a trivial setup mistake.
  function captureCanonicalDefectEvidence(canonical) {
    function patterned(w, h, phase) {
      const data = new Float32Array(w * h * 4)
      for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
        const i = (y * w + x) * 4
        data[i] = f((((31 * x + 17 * y + 7 + 19 * phase) % 97) + 1) / 101)
        data[i + 1] = f((((13 * x + 37 * y + 11 + 23 * phase) % 89) + 2) / 97)
        data[i + 2] = f((((43 * x + 5 * y + 3 + 29 * phase) % 83) + 3) / 91)
        data[i + 3] = 1
      }
      return new Surface(w, h, data)
    }
    function attempt(w, h) {
      try {
        const inputTex = patterned(w, h, 0)
        const bindings = createCanonicalBindings({ width: w, height: h, uniforms: { RADIUS: 3, threshold: 0 }, textures: { inputTex }, time: 0 })
        const kernel = bindGlslKernel(canonical, bindings)
        const surface = new Surface(w, h)
        runPass({ kernel, destination: surface })
        return { width: w, height: h, threw: false, message: null }
      } catch (error) {
        return { width: w, height: h, threw: true, message: error.message }
      }
    }
    const sizes = [[4, 4], [5, 5], [6, 6]]
    const attempts = sizes.map(([w, h]) => attempt(w, h))
    const fiveByFive = attempts.find((a) => a.width === 5 && a.height === 5)
    if (!fiveByFive.threw) throw new Error('median: expected canonicalFactory80 to CRASH at 5x5 (documented defect) -- it did not, the defect claim would be WRONG, investigate')
    if (attempts.some((a) => (a.width !== 5) && a.threw)) throw new Error('median: expected 4x4/6x6 to render fine (defect isolated to 5x5-class inputs) -- one of them also crashed, investigate')
    return { attempts, isolated_repro_note: 'canonicalFactory80 crashes on this exact 5x5 patterned input; 4x4 and 6x6 render fine with the identical algorithm shape and identical uniform contract -- data-dependent, not a hermeticity mistake in this generator.' }
  }

  // ---- The AVOIDED mutation: documented with hard evidence, not silently
  // skipped. `while (scanLeft <= scanRight)` -> `while (scanLeft < scanRight)`
  // drops the Hoare partition's tie-breaking crossing step, which can leave
  // `scanLeft === scanRight === medianIndex` after the middle loop exits --
  // neither `scanRight < medianIndex` nor `medianIndex < scanLeft` then
  // holds, so `left`/`right` are UNCHANGED and the outer `while (left <
  // right)` loop never makes progress again. Verified live: hung past a
  // 120-second wall-clock watchdog on the 8x8 patterned case below (a plain
  // synchronous infinite loop blocks Node's event loop, so even an in-
  // process `setTimeout` guard cannot fire) -- killed, not merely
  // hypothesized.
  const AVOIDED_INNER_MUTATION_NOTE = {
    anchor: 'while (scanLeft <= scanRight) {',
    attempted_mutation: 'while (scanLeft < scanRight) {',
    outcome: 'INFINITE LOOP -- verified live, killed after exceeding a 120s wall-clock watchdog on an 8x8 patterned render; a synchronous JS while-loop blocks the event loop so no in-process timer can preempt it',
    root_cause: 'dropping the `<=` boundary loses the guarantee that scanLeft/scanRight cross by the end of the middle loop; when they instead land exactly on medianIndex, neither outer-loop narrowing branch fires and left/right are unchanged forever',
    disposition: 'AVOIDED as a mutation site entirely. Both mutations below instead cap the OUTER `while (left < right)` convergence loop with an explicit counter, which provably terminates by construction regardless of data, sidestepping this hazard rather than working around it case-by-case.',
  }

  const uniformTypes = { RADIUS: 'int', threshold: 'float' }
  const defines = { RADIUS: 3 }

  function patternedSurfaceLocal(w, h, phase) { return patternedSurface(w, h, phase) }
  function uniformSurface(w, h, r, g, b) {
    const data = new Float32Array(w * h * 4)
    for (let i = 0; i < w * h; i += 1) { data[i * 4] = f(r); data[i * 4 + 1] = f(g); data[i * 4 + 2] = f(b); data[i * 4 + 3] = 1 }
    return new Surface(w, h, data)
  }

  const cases = [
    { name: 'high-variance-8x8', width: 8, height: 8, phase: 900, uniforms: { RADIUS: 3, threshold: 0 } },
    { name: 'high-variance-6x5', width: 6, height: 5, phase: 901, uniforms: { RADIUS: 3, threshold: 0 } },
    { name: 'high-variance-7x7', width: 7, height: 7, phase: 902, uniforms: { RADIUS: 3, threshold: 0 } },
    { name: 'uniform-color-diagnostic', width: 6, height: 6, phase: null, uniforms: { RADIUS: 3, threshold: 0 }, diagnostic: true },
  ]
  function buildTextures(c) {
    return { inputTex: c.phase === null ? uniformSurface(c.width, c.height, 0.3, 0.5, 0.7) : patternedSurfaceLocal(c.width, c.height, c.phase) }
  }

  // reach: verified live via a graduated-cap sweep (1,2,3,4,5,6,8,10,15) on
  // each high-variance case, showing the REAL (uncapped) result is only
  // reproduced at cap>=15 -- i.e. the true outer-loop convergence depth
  // exceeds 10 for all three high-variance cases, comfortably above BOTH
  // mutation caps (1 and 5). The uniform-color diagnostic converges within
  // cap=1 (verified live: cap 1, 2, and 5 all already match the real,
  // uncapped result) -- proving the "already-converged sort is trip-count-
  // insensitive" trap the task brief names, and giving a genuine reach=false
  // negative control.
  const reachByCase = {
    'high-variance-8x8': { cap1: true, cap5: true },
    'high-variance-6x5': { cap1: true, cap5: true },
    'high-variance-7x7': { cap1: true, cap5: true },
    'uniform-color-diagnostic': { cap1: false, cap5: false },
  }

  const mutations = [
    {
      id: 'median-outer-convergence-cap-1', kind: 'trip_count_swap', reachKey: 'cap1',
      anchor: 'while (left < right) {', mutated: 'for (let __cap = 0; (left < right) && (__cap < 1); __cap++) {',
      description: 'Cap the outer quickselect convergence loop at 1 pass -- severe, provably-terminating (bounded by a counter, not data) trip-count reduction. Reach-eligible on all three high-variance cases (true convergence depth >10); the uniform-color diagnostic already converges within 1 pass and is expected-zero.',
    },
    {
      id: 'median-outer-convergence-cap-5', kind: 'trip_count_off_by_one', reachKey: 'cap5',
      anchor: 'while (left < right) {', mutated: 'for (let __cap = 0; (left < right) && (__cap < 5); __cap++) {',
      description: 'Cap the outer quickselect convergence loop at 5 passes -- milder than cap-1 but still well under the true convergence depth (>10) for all three high-variance cases; the uniform-color diagnostic is unaffected (converges in 1 pass).',
    },
  ]

  return { id: 'median', key, uniformTypes, defines, loadProgram, captureCanonicalDefectEvidence, AVOIDED_INNER_MUTATION_NOTE, buildTextures, cases, mutations, reachByCase, exportName: 'medianFactory' }
})()

// =============================================================================
// PROGRAM 4: classicNoisedeck/noise:noise
// =============================================================================
// Loop-proof site: `multires()`'s `for (var i = 1; i <= octaves; i++) {`, a
// PARAMETER-bound loop (octaves is a plain uniform, min 1 / max 8 per the
// upstream param schema -- NOT one of the five #define-bound values
// {COLOR_MODE, LOOP_OFFSET, METRIC, REFRACT_MODE, NOISE_TYPE}, whose
// authorized defaults are used unmodified). Called UNCONDITIONALLY from
// main() regardless of NOISE_TYPE (verified live from the factory text) --
// always reachable at the authorized defines.
//
// The named trap ("octave loop may saturate as amplitudes shrink
// geometrically"): each octave i contributes weight 1/2^i to a weighted
// average (`color += layer/multiplier; ... color /= multiplicand`), so late
// octaves contribute vanishingly little. Verified empirically (not assumed)
// at octaves=3, 4, and 6 that dropping the LAST octave still produces a
// bit-exact divergence at every one of those three octave counts -- i.e. the
// geometric decay has not yet saturated away at float32 precision for any
// octave count in this program's authorized range (max 8).
const classicNoiseProgram = (() => {
  const key = 'classicNoisedeck/noise:noise'
  const sourceFile = 'noise.glsl'
  const sourceRawBytes = 31255
  const sourceSha256 = '4cd68543729f94788ef6fa2a484dd47d76154814b027128bef5eb9c8d7461663'
  const factoryName = 'canonicalFactory12'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/classicNoisedeck/noise', sourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== sourceRawBytes) throw new Error('classicNoisedeck/noise: source raw byte count drift')
    if (sha256(sourceBytes) !== sourceSha256) throw new Error('classicNoisedeck/noise: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('classicNoisedeck/noise: canonical factory missing')
    if (canonical.name !== factoryName) throw new Error(`classicNoisedeck/noise: factory name drift (got ${canonical.name})`)
    if (kernelFactories.get(key) !== canonical) throw new Error('classicNoisedeck/noise: public factory is not the canonical identity')
    if (canonicalAdapterFactories[key] !== undefined) throw new Error('classicNoisedeck/noise: unexpected adapter override present')
    const factoryText = canonical.toString()
    for (const k of ['NOISE_TYPE', 'REFRACT_MODE', 'LOOP_OFFSET', 'METRIC', 'COLOR_MODE']) {
      if (!new RegExp(`\\$bindings\\[${JSON.stringify(k)}\\]`).test(factoryText)) {
        throw new Error(`classicNoisedeck/noise: authorized define "${k}" is not actually read by the factory as a binding`)
      }
    }
    return { sourcePath, canonical, factoryText }
  }

  const defines = { COLOR_MODE: 6, LOOP_OFFSET: 300, METRIC: 0, REFRACT_MODE: 2, NOISE_TYPE: 10 }
  const uniformTypes = {
    COLOR_MODE: 'int', LOOP_OFFSET: 'int', METRIC: 'int', REFRACT_MODE: 'int', NOISE_TYPE: 'int',
    seed: 'int', xScale: 'float', yScale: 'float', octaves: 'int', ridges: 'bool', refractAmt: 'float',
    kaleido: 'int', loopScale: 'float', speed: 'float', paletteMode: 'int',
    paletteOffset: 'vec3', paletteAmp: 'vec3', paletteFreq: 'vec3', palettePhase: 'vec3',
    cyclePalette: 'int', rotatePalette: 'float', repeatPalette: 'int', hueRange: 'float', hueRotation: 'float', wrap: 'bool',
  }
  function baseUniforms(octaves) {
    return {
      ...defines,
      seed: 1, xScale: 75, yScale: 75, octaves, ridges: false, refractAmt: 0, kaleido: 1,
      loopScale: 75, speed: 10, paletteMode: 0, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.5, 0.5, 0.5],
      paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0], cyclePalette: 0, rotatePalette: 0, repeatPalette: 1,
      hueRange: 25, hueRotation: 179, wrap: true,
    }
  }
  const cases = [
    { name: 'three-octaves', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(3) },
    { name: 'four-octaves', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(4) },
    { name: 'six-octaves-saturation-check', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(6) },
  ]
  const mutations = [
    {
      id: 'classicNoisedeckNoise-octave-off-by-one', kind: 'trip_count_off_by_one',
      anchor: 'for (var i = 1; i <= octaves; i++) {', mutated: 'for (var i = 1; i < octaves; i++) {',
      description: 'Drop the last octave (i<octaves instead of i<=octaves): smallest possible wrong trip count. Verified live to diverge at octaves=3, 4, and 6 -- the geometric weight decay (1/2^i) has not saturated the mutated last octave into float32 invisibility at any of these counts.',
    },
    {
      id: 'classicNoisedeckNoise-octave-swap', kind: 'trip_count_swap',
      anchor: 'for (var i = 1; i <= octaves; i++) {', mutated: 'for (var i = 1; i <= octaves - 2; i++) {',
      description: 'Drop the last two octaves: a materially wrong trip count, verified live to diverge at octaves=3, 4, and 6.',
    },
  ]
  return { id: 'classicNoisedeckNoise', key, uniformTypes, defines, loadProgram, cases, mutations, reach: () => ({ default: true }) }
})()

// =============================================================================
// PROGRAM 5: synth/noise:noise
// =============================================================================
// Same octave-loop shape as classicNoisedeck/noise, simpler program (fewer
// defines: only NOISE_TYPE/LOOP_OFFSET; `colorMode` is a plain UNIFORM here,
// not a define, so colorMode=0 (mono passthrough, `return vec3(color[2])`)
// is used freely to keep the case simple -- verified live to still exercise
// and discriminate the octave loop.
const synthNoiseProgram = (() => {
  const key = 'synth/noise:noise'
  const sourceFile = 'noise.glsl'
  const sourceRawBytes = 18131
  const sourceSha256 = '410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274'
  const factoryName = 'canonicalFactory265'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/synth/noise', sourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== sourceRawBytes) throw new Error('synth/noise: source raw byte count drift')
    if (sha256(sourceBytes) !== sourceSha256) throw new Error('synth/noise: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('synth/noise: canonical factory missing')
    if (canonical.name !== factoryName) throw new Error(`synth/noise: factory name drift (got ${canonical.name})`)
    if (kernelFactories.get(key) !== canonical) throw new Error('synth/noise: public factory is not the canonical identity')
    if (canonicalAdapterFactories[key] !== undefined) throw new Error('synth/noise: unexpected adapter override present')
    const factoryText = canonical.toString()
    for (const k of ['NOISE_TYPE', 'LOOP_OFFSET']) {
      if (!new RegExp(`\\$bindings\\[${JSON.stringify(k)}\\]`).test(factoryText)) {
        throw new Error(`synth/noise: authorized define "${k}" is not actually read by the factory as a binding`)
      }
    }
    return { sourcePath, canonical, factoryText }
  }

  const defines = { LOOP_OFFSET: 300, NOISE_TYPE: 10 }
  const uniformTypes = { LOOP_OFFSET: 'int', NOISE_TYPE: 'int', scaleX: 'float', scaleY: 'float', octaves: 'int', ridges: 'bool', loopScale: 'float', speed: 'float', colorMode: 'int', wrap: 'bool' }
  function baseUniforms(octaves) { return { ...defines, scaleX: 75, scaleY: 75, octaves, ridges: false, loopScale: 75, speed: 10, colorMode: 0, wrap: true } }
  const cases = [
    { name: 'three-octaves', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(3) },
    { name: 'four-octaves', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(4) },
    { name: 'six-octaves-saturation-check', width: 6, height: 5, tileOffset: [3, 5], fullResolution: [16, 13], uniforms: baseUniforms(6) },
  ]
  const mutations = [
    {
      id: 'synthNoise-octave-off-by-one', kind: 'trip_count_off_by_one',
      anchor: 'for (var i = 1; i <= oct; i++) {', mutated: 'for (var i = 1; i < oct; i++) {',
      description: 'Drop the last octave. Verified live to diverge at octaves=3, 4, and 6.',
    },
    {
      id: 'synthNoise-octave-swap', kind: 'trip_count_swap',
      anchor: 'for (var i = 1; i <= oct; i++) {', mutated: 'for (var i = 1; i <= oct - 2; i++) {',
      description: 'Drop the last two octaves. Verified live to diverge at octaves=3, 4, and 6.',
    },
  ]
  return { id: 'synthNoise', key, uniformTypes, defines, loadProgram, cases, mutations, reach: () => ({ default: true }) }
})()

// =============================================================================
// PROGRAM 6: synth/testPattern:testPattern
// =============================================================================
// Loop-proof site: `renderNumber()`'s fixed `for (var i = 0; i < 3; i++) {
// digits[i] = temp % 10; temp /= 10; }` digit-extraction loop -- a
// literal-3 cap (not parameter-bound), pre-zeroed `digits=[0,0,0]` array.
// `checkerboard()` (pattern=0, the authorized default per _defaults(); no
// GLSL defines exist for this program at all) always calls `renderNumber()`
// unconditionally.
//
// A 1x1 canvas + `tileOffset` gives EXACT control over which UV (and hence
// which grid cell / glyph sub-pixel) the single rendered pixel samples,
// following the same technique used for mandelbrot's boundary points above.
// Empirically located (brute-force UV scan, not hand-derived): cellUV
// (0.225, 0.330) inside gridSize=12's cell (0,0) -- cellNum=132, a 3-digit
// number -- lands inside the HUNDREDS digit's glyph rectangle at a bit
// position where GLYPH[0] and GLYPH[1] differ, so dropping the i=2
// extraction (leaving digits[2]=0 instead of the true hundreds digit 1)
// flips that pixel from background to glyph-black.
const testPatternProgram = (() => {
  const key = 'synth/testPattern:testPattern'
  const sourceFile = 'testPattern.glsl'
  const sourceRawBytes = 5919
  const sourceSha256 = 'f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20'
  const factoryName = 'canonicalFactory277'

  function loadProgram() {
    const sourcePath = path.join(corpusRoot, 'sources/synth/testPattern', sourceFile)
    const sourceBytes = fs.readFileSync(sourcePath)
    if (sourceBytes.length !== sourceRawBytes) throw new Error('testPattern: source raw byte count drift')
    if (sha256(sourceBytes) !== sourceSha256) throw new Error('testPattern: source sha256 drift')
    const canonical = canonicalKernelFactories[key]
    if (!canonical) throw new Error('testPattern: canonical factory missing')
    if (canonical.name !== factoryName) throw new Error(`testPattern: factory name drift (got ${canonical.name})`)
    if (kernelFactories.get(key) !== canonical) throw new Error('testPattern: public factory is not the canonical identity')
    if (canonicalAdapterFactories[key] !== undefined) throw new Error('testPattern: unexpected adapter override present')
    return { sourcePath, canonical, factoryText: canonical.toString() }
  }

  const uniformTypes = { gridSize: 'int', pattern: 'int' }
  const cases = [
    {
      // gridSize=12, cellNum=132 (3-digit, cell (0,0)). uv=(0.01875,0.0275)
      // via fullResolution=(1000,1000); tileOffset chosen so the 1x1
      // canvas's single pixel (fragCoord=(0.5,0.5)) samples exactly that uv.
      name: 'hundreds-digit-glyph-hit', width: 1, height: 1,
      tileOffset: [18.25, 27], fullResolution: [1000, 1000],
      uniforms: { gridSize: 12, pattern: 0 },
    },
    {
      // gridSize=3, cellNum=4 (1-digit, cell (1,1)). Only digits[0] is ever
      // read (numDigits=1), so dropping the i=1/i=2 extraction changes
      // nothing observable -- diagnostic.
      name: 'single-digit-diagnostic', width: 1, height: 1,
      tileOffset: [499.5, 499.5], fullResolution: [1000, 1000],
      uniforms: { gridSize: 3, pattern: 0 }, diagnostic: true,
    },
  ]
  const mutations = [
    {
      id: 'testPattern-digit-extraction-off-by-one', kind: 'trip_count_off_by_one',
      anchor: 'for (var i = 0; i < 3; i++) {', mutated: 'for (var i = 0; i < 2; i++) {',
      description: 'Drop the hundreds-digit extraction (i<2 instead of i<3): digits[2] stays at its zero-initialized value. Verified live to flip the hundreds-digit-glyph-hit pixel from background to glyph-black.',
    },
    {
      id: 'testPattern-digit-extraction-swap', kind: 'trip_count_swap',
      anchor: 'for (var i = 0; i < 3; i++) {', mutated: 'for (var i = 0; i < 1; i++) {',
      description: 'Drop both the tens- and hundreds-digit extraction (i<1): a materially wrong trip count. Verified live to diverge identically to the off-by-one mutation at this probe point (both leave digits[2]=0).',
    },
  ]
  return { id: 'testPattern', key, uniformTypes, defines: {}, loadProgram, cases, mutations, reach: (c) => ({ default: !c.diagnostic }) }
})()

// =============================================================================
// PROGRAM 7: classicNoisedeck/fractal:fractal (ADAPTER-ROUTED, NO CANONICAL --
// see module header (1))
// =============================================================================
// `canonicalKernelFactories['classicNoisedeck/fractal:fractal']` is
// undefined -- verified live, and independently confirmed as a PERMANENT
// architectural decision, not a build gap: `compile-glsl.js`'s explicit
// adapter skip-list, `glsl-coverage.js`'s `"status": "adapter",
// "generatedBytes": 0` entry, and `canonicalAdapterFactories` all agree. The
// corpus `fractal.glsl` this generator does NOT use describes a totally
// different (df64, octave-based) algorithm than what actually ships --
// `fractalFactory` (`src/effects/adapters/fractal.js`) is a from-scratch
// hand JS port with its own julia()/newton()/mandelbrot() sub-fractal
// engines, each with a genuine parameter-bound counted loop with early
// break. This oracle covers julia() only (type=0, the authorized default
// per upstream-snapshot.js) -- newton()/mandelbrot() share the identical
// loop shape but are out of scope for this pass; documented, not silently
// dropped.
//
// colorMode=0 (mono passthrough, a plain uniform not a define) keeps the
// case free of the palette/hsv machinery entirely: output is exactly
// Math.fround(iteration/count) replicated across RGB, directly exposing the
// loop's own trip count in the rendered pixel.
const fractalProgram = (() => {
  const key = 'classicNoisedeck/fractal:fractal'

  function loadProgram() {
    const canonical = canonicalKernelFactories[key]
    if (canonical !== undefined) throw new Error('fractal: expected NO canonical factory (permanent adapter-only routing) -- one now exists, re-investigate this program from scratch')
    const adapter = canonicalAdapterFactories[key]
    if (adapter === undefined) throw new Error('fractal: expected adapter to be present')
    if (kernelFactories.get(key) !== adapter) throw new Error('fractal: public factory is not the adapter')
    if (adapter.name !== 'fractalFactory') throw new Error(`fractal: adapter factory name drift (got ${adapter.name})`)
    const moduleSourceText = fs.readFileSync(path.resolve(here, fractalAdapterSourcePath), 'utf8')
    return { canonical: null, moduleSourceText }
  }

  const uniformTypes = {
    type: 'int', symmetry: 'int', zoomAmt: 'float', rotation: 'float', speed: 'float',
    offsetX: 'float', offsetY: 'float', centerX: 'float', centerY: 'float', mode: 'int',
    iterations: 'int', colorMode: 'int', cyclePalette: 'int', rotatePalette: 'float', repeatPalette: 'int',
    hueRange: 'float', levels: 'int', bgColor: 'vec3', bgAlpha: 'float', cutoff: 'float',
    paletteMode: 'int', paletteOffset: 'vec3', paletteAmp: 'vec3', paletteFreq: 'vec3', palettePhase: 'vec3',
  }
  function baseUniforms(offsetX, offsetY) {
    return {
      type: 0, symmetry: 0, zoomAmt: 0, rotation: 0, speed: 0, offsetX, offsetY, centerX: 0, centerY: 0,
      mode: 0, iterations: 50, colorMode: 0, cyclePalette: 0, rotatePalette: 0, repeatPalette: 1,
      hueRange: 100, levels: 0, bgColor: [0, 0, 0], bgAlpha: 100, cutoff: 0,
      paletteMode: 0, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0],
    }
  }
  // c=(-0.35,0.27015) via offsetX=-70,offsetY=27.015 (map(-100,100,-0.5,0.5)
  // / map(-100,100,-1,1) inverted). z0 controlled via tileOffset = z0/2
  // (zoomAmt=0 -> zoom=2; rotation=0 makes rotate() an identity; centerX/Y=0).
  const cases = [
    { name: 'julia-never-escapes-z0a', width: 1, height: 1, tileOffset: [0.05, 0.05], fullResolution: [1, 1], uniforms: baseUniforms(-70, 27.015) },
    { name: 'julia-never-escapes-z0b', width: 1, height: 1, tileOffset: [-0.1, 0.05], fullResolution: [1, 1], uniforms: baseUniforms(-70, 27.015) },
    { name: 'julia-fast-escape-diagnostic', width: 1, height: 1, tileOffset: [1, 1], fullResolution: [1, 1], uniforms: baseUniforms(-70, 27.015), diagnostic: true },
  ]
  const mutations = [
    {
      id: 'fractal-julia-count-off-by-one', kind: 'trip_count_off_by_one',
      anchor: 'for (let index = 0; index < count; index += 1) {', mutated: 'for (let index = 0; index < count - 1; index += 1) {',
      description: 'Drop the last julia() iteration (count-1 instead of count, count=iterations*2=100). Reach-eligible on both never-escapes cases (true escape >> 100, verified via a double-precision calibration probe restricted to this generator\'s case-design step -- the actual proof renders through the real fractalFactory).',
    },
    {
      id: 'fractal-julia-count-swap', kind: 'trip_count_swap',
      anchor: 'for (let index = 0; index < count; index += 1) {', mutated: 'for (let index = 0; index < count - 40; index += 1) {',
      description: 'Drop the last 40 julia() iterations (count-40=60): a materially wrong trip count. Same reach-eligibility as the off-by-one mutation.',
    },
  ]
  return { id: 'fractal', key, uniformTypes, defines: {}, loadProgram, cases, mutations, reach: (c) => ({ default: !c.diagnostic }), exportName: 'fractalFactory' }
})()

// =============================================================================
// PROGRAM 8: classicNoisedeck/effects:effects -- UNCOVERABLE (see module
// header (3))
// =============================================================================
const EFFECTS_BLOCKED = {
  id: 'effects', key: 'classicNoisedeck/effects:effects',
  sourceFile: 'effects.glsl', sourceRawBytes: 21087,
  sourceSha256: 'e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c',
  factoryName: 'canonicalFactory7',
  reason: 'UNRENDERABLE-AS-DISCRIMINATING, not merely non-discriminating -- verified live, not assumed. `EFFECT` genuinely IS bound as a runtime uniform (`var EFFECT = $bindings["EFFECT"];`, matching the defines-bound-as-uniforms lesson -- it is NOT preprocessor-eliminated, unlike a first, wrong hypothesis this generator formed and then disproved by grepping the compiled JS text for `function convolve`/`function bloom`/`function zoomBlur`, all of which ARE present). Every loop in this program (convolve()\'s 3x3 kernel-tap loop, bloom()\'s -4..4 nested loop, zoomBlur()\'s 0..40 loop) lives exclusively inside functions reachable ONLY through `main()`\'s `if (EFFECT != 0) { if (effectAmt != 0) { ... } }` gate -- and `generate_typed_slice._defaults()` authorizes EFFECT=0 for this program (confirmed live, not assumed). At EFFECT=0 that whole block is skipped at RUNTIME on every invocation, so none of its loops ever execute. Verified live, not merely inferred from reading the source: a textual off-by-one mutation on convolve()\'s tap loop (`for (var i = 0; i < 9; i++)` -> `for (var i = 0; i < 0; i++)`) produces ZERO divergence across four different `effectAmt` values (0, 5, 10, 20) at the authorized EFFECT=0 -- and the IDENTICAL mutation produces NONZERO divergence at an UNAUTHORIZED EFFECT=1, proving the loop and the mutation are both real and working, just genuinely unreachable at the one define value this task\'s reachability rule (only build cases reachable from main() at the authorized defines) permits. No case can be built for this program without violating that rule.',
}
function verifyEffectsBlocked() {
  const sourcePath = path.join(corpusRoot, 'sources/classicNoisedeck/effects', EFFECTS_BLOCKED.sourceFile)
  const sourceBytes = fs.readFileSync(sourcePath)
  if (sourceBytes.length !== EFFECTS_BLOCKED.sourceRawBytes) throw new Error('effects: source raw byte count drift')
  if (sha256(sourceBytes) !== EFFECTS_BLOCKED.sourceSha256) throw new Error('effects: source sha256 drift')
  const canonical = canonicalKernelFactories[EFFECTS_BLOCKED.key]
  if (!canonical) throw new Error('effects: canonical factory missing')
  if (canonical.name !== EFFECTS_BLOCKED.factoryName) throw new Error(`effects: factory name drift (got ${canonical.name})`)
  if (kernelFactories.get(EFFECTS_BLOCKED.key) !== canonical) throw new Error('effects: public factory is not the canonical identity')
  if (canonicalAdapterFactories[EFFECTS_BLOCKED.key] !== undefined) throw new Error('effects: unexpected adapter override present')
  const factoryText = canonical.toString()
  if (!/var EFFECT = \$bindings\["EFFECT"\];/.test(factoryText)) throw new Error('effects: EFFECT is not bound as a runtime uniform as documented -- re-investigate')
  const anchor = 'for (var i = 0; i < 9; i++) {'
  if (occurrences(factoryText, anchor) !== 1) throw new Error('effects: convolve tap-loop anchor not unique/found')
  const mutated = evaluated(factoryText.replace(anchor, 'for (var i = 0; i < 0; i++) {'))

  function render(factory, EFFECT, effectAmt) {
    const w = 6, h = 5
    const inputTex = patternedSurface(w, h, 950)
    const uniforms = { EFFECT, FLIP: 0, renderScale: 1, effectAmt, scaleAmt: 100, rotation: 0, offsetX: 0, offsetY: 0, intensity: 1, saturation: 1 }
    const bindings = createCanonicalBindings({ width: w, height: h, uniforms, textures: { inputTex }, time: 0 })
    const kernel = bindGlslKernel(factory, bindings)
    const surface = new Surface(w, h)
    runPass({ kernel, destination: surface })
    return surface
  }

  const atAuthorizedDefault = [0, 5, 10, 20].map((effectAmt) => {
    const r = render(canonical, 0, effectAmt)
    const m = render(mutated, 0, effectAmt)
    return { effectAmt, EFFECT: 0, diverges: !sameBytes(r, m) }
  })
  if (atAuthorizedDefault.some((r) => r.diverges)) throw new Error('effects: expected ZERO divergence at authorized EFFECT=0 -- the dead-code claim would be WRONG, investigate')

  const rUnauth = render(canonical, 1, 10)
  const mUnauth = render(mutated, 1, 10)
  const atUnauthorized = { effectAmt: 10, EFFECT: 1, diverges: !sameBytes(rUnauth, mUnauth) }
  if (!atUnauthorized.diverges) throw new Error('effects: expected NONZERO divergence at unauthorized EFFECT=1 (proving the loop/mutation are real) -- got zero, investigate')

  return {
    factory_name: canonical.name, public_is_canonical: true, adapter_override_present: false,
    effect_bound_as_runtime_uniform: true,
    authorized_defines: { EFFECT: 0, FLIP: 0 },
    mutation_anchor: anchor, mutation_description: 'convolve() 3x3 tap loop: i<9 -> i<0 (never executes)',
    at_authorized_default: atAuthorizedDefault,
    at_unauthorized_control: atUnauthorized,
  }
}

// =============================================================================
// EXECUTION
// =============================================================================
const ONLY = process.argv.find((a) => a.startsWith('--only='))?.slice('--only='.length)?.split(',')
const DO_CHECK = process.argv.includes('--check')
const DO_ASSEMBLE = process.argv.includes('--assemble') || (!ONLY && !DO_CHECK)

function shouldRun(id) { return !ONLY || ONLY.includes(id) }

// ---- Canonical-factory programs (synchronous rendering) -------------------
const CANONICAL_PROGRAMS = [nmReindexReduce, mandelbrotProgram, classicNoiseProgram, synthNoiseProgram, testPatternProgram]

function runCanonicalProgram(programDef) {
  const program = { ...programDef, ...programDef.loadProgram() }
  program.caseRecords = program.cases.map((c) => {
    const rendered = renderCase(program, c)
    const reach = program.reachByCase ? program.reachByCase[c.name] : program.reach(c)
    return { ...rendered, reach }
  })
  const anyReach = program.caseRecords.some((cr) => Object.values(cr.reach).some(Boolean))
  if (!anyReach) throw new Error(`${program.id}: no reach-eligible case at all`)

  for (const mutation of program.mutations) {
    const reachKey = mutation.reachKey ?? 'default'
    const mutatedText = mutateFactoryText(program.factoryText, mutation)
    const mutatedFactory = evaluated(mutatedText)
    const caseResults = program.caseRecords.map((cr) => {
      const mutatedSurface = renderWithFactory(program, cr.c, mutatedFactory)
      const diverges = !sameBytes(cr.surface, mutatedSurface)
      const reaches = Boolean(cr.reach[reachKey])
      return { case: cr.name, diagnostic: Boolean(cr.c.diagnostic), reaches, diverges }
    })
    const reaching = caseResults.filter((r) => r.reaches)
    const nonReaching = caseResults.filter((r) => !r.reaches)
    const divergentReaching = reaching.filter((r) => r.diverges).length
    const divergentNonReaching = nonReaching.filter((r) => r.diverges).length
    if (reaching.length === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site`)
    if (divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${reaching.length}`)
    if (divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${divergentNonReaching}/${nonReaching.length} non-reaching case(s) diverged -- reach() or mutation scope is wrong`)
    mutation.caseResults = caseResults
    mutation.summary = { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
  }

  console.log(`[checkpoint] ${program.id}: ${program.caseRecords.length} cases, ${program.mutations.length} mutations verified`)
  const payload = {
    id: program.id, key: program.key, defines: program.defines ?? {},
    cases: program.caseRecords.map((cr) => ({
      name: cr.name, dimensions: { width: cr.c.width, height: cr.c.height }, diagnostic: Boolean(cr.c.diagnostic), reach: cr.reach,
      uniforms: cr.c.uniforms, tile_offset: cr.c.tileOffset ?? [0, 0], full_resolution: cr.c.fullResolution ?? [cr.c.width, cr.c.height],
      eligible_for_native_binding: true, repeat_identity: true, input_immutable: true,
      output: renderResult(cr.surface),
    })),
    mutations: program.mutations.map((m) => ({
      id: m.id, kind: m.kind, reach_key: m.reachKey ?? 'default', anchor: m.anchor, mutated: m.mutated, description: m.description,
      case_results: m.caseResults, summary: m.summary,
    })),
  }
  checkpoint(program.id, payload)
  return payload
}

// ---- Adapter-based programs (async rendering) ------------------------------
async function runAdapterProgram(programDef) {
  const loaded = programDef.loadProgram()
  const program = { ...programDef, ...loaded }

  program.caseRecords = []
  for (const c of program.cases) {
    const rendered = await renderAdapterCase(program, c)
    const reach = program.reachByCase ? program.reachByCase[c.name] : program.reach(c)
    program.caseRecords.push({ ...rendered, reach })
  }
  const anyReach = program.caseRecords.some((cr) => Object.values(cr.reach).some(Boolean))
  if (!anyReach) throw new Error(`${program.id}: no reach-eligible case at all`)

  for (const mutation of program.mutations) {
    const reachKey = mutation.reachKey ?? 'default'
    if (occurrences(program.moduleSourceText, mutation.anchor) !== 1) throw new Error(`${mutation.id}: anchor not unique/found in module source`)
    const mutatedSourceText = program.moduleSourceText.replace(mutation.anchor, mutation.mutated)
    const caseResults = []
    for (const cr of program.caseRecords) {
      const mutatedSurface = await renderAdapterWithMutatedSource(program, cr.c, mutatedSourceText)
      const diverges = !sameBytes(cr.surface, mutatedSurface)
      const reaches = Boolean(cr.reach[reachKey])
      caseResults.push({ case: cr.name, diagnostic: Boolean(cr.c.diagnostic), reaches, diverges })
    }
    const reaching = caseResults.filter((r) => r.reaches)
    const nonReaching = caseResults.filter((r) => !r.reaches)
    const divergentReaching = reaching.filter((r) => r.diverges).length
    const divergentNonReaching = nonReaching.filter((r) => r.diverges).length
    if (reaching.length === 0) throw new Error(`${mutation.id}: no case reaches this mutation's site`)
    if (divergentReaching === 0) throw new Error(`${mutation.id}: expected nonzero divergence among reach-eligible cases, got 0/${reaching.length}`)
    if (divergentNonReaching !== 0) throw new Error(`${mutation.id}: ${divergentNonReaching}/${nonReaching.length} non-reaching case(s) diverged`)
    mutation.caseResults = caseResults
    mutation.summary = { reaching_cases: reaching.length, divergent_reaching: divergentReaching, non_reaching_cases: nonReaching.length, divergent_non_reaching: divergentNonReaching }
  }

  console.log(`[checkpoint] ${program.id}: ${program.caseRecords.length} cases, ${program.mutations.length} mutations verified`)
  const extra = {}
  if (program.id === 'median') {
    extra.canonical_factory_defect = program.captureCanonicalDefectEvidence(program.canonical)
    extra.avoided_mutation = program.AVOIDED_INNER_MUTATION_NOTE
  }
  const payload = {
    id: program.id, key: program.key, defines: program.defines ?? {},
    ground_truth: `adapter (${program.exportName}) -- see module header / report for why`,
    cases: program.caseRecords.map((cr) => ({
      name: cr.name, dimensions: { width: cr.c.width, height: cr.c.height }, diagnostic: Boolean(cr.c.diagnostic), reach: cr.reach,
      uniforms: cr.c.uniforms, tile_offset: cr.c.tileOffset ?? [0, 0], full_resolution: cr.c.fullResolution ?? [cr.c.width, cr.c.height],
      eligible_for_native_binding: true, repeat_identity: true, input_immutable: true,
      output: renderResult(cr.surface),
    })),
    mutations: program.mutations.map((m) => ({
      id: m.id, kind: m.kind, reach_key: m.reachKey ?? 'default', anchor: m.anchor, mutated: m.mutated, description: m.description,
      case_results: m.caseResults, summary: m.summary,
    })),
    ...extra,
  }
  checkpoint(program.id, payload)
  return payload
}

function runEffectsBlocked() {
  const evidence = verifyEffectsBlocked()
  console.log('[checkpoint] effects: documented as UNCOVERABLE, blocker evidence captured live')
  const payload = { id: 'effects', key: EFFECTS_BLOCKED.key, status: 'UNCOVERABLE', reason: EFFECTS_BLOCKED.reason, evidence }
  checkpoint('effects', payload)
  return payload
}

// ---------------------------------------------------------------------------
// Assembly + report (only when running the full batch, not a single --only)
// ---------------------------------------------------------------------------
function loadAllCheckpoints() {
  const ids = ['nmReindexReduce', 'mandelbrot', 'median', 'classicNoisedeckNoise', 'synthNoise', 'testPattern', 'fractal', 'effects']
  const out = {}
  for (const id of ids) {
    const p = path.join(here, `partial-${id}.json`)
    if (!fs.existsSync(p)) throw new Error(`missing checkpoint for ${id} -- run with --only=${id} first`)
    out[id] = JSON.parse(fs.readFileSync(p, 'utf8'))
  }
  return out
}

function buildFinal(parts) {
  const coveredIds = ['nmReindexReduce', 'mandelbrot', 'median', 'classicNoisedeckNoise', 'synthNoise', 'testPattern', 'fractal']
  const programsOut = {}
  let totalEligible = 0
  let totalDiagnostic = 0
  for (const id of coveredIds) {
    const p = parts[id]
    const eligible = p.cases.filter((c) => !c.diagnostic)
    const diagnostic = p.cases.filter((c) => c.diagnostic)
    totalEligible += eligible.length
    totalDiagnostic += diagnostic.length
    programsOut[id] = p
  }
  return {
    schema: 'noisemaker-for-cpp.loopproof.oracle-b.eight-program-loop-trip-count-oracles.v1',
    corpus_revision: revision,
    provenance: { ...RUNTIME_PROVENANCE, node: process.version },
    programs: programsOut,
    effects: parts.effects,
    eligibility_summary: {
      programs_covered: coveredIds.length,
      programs_blocked: 1,
      total_cases: totalEligible + totalDiagnostic, eligible_cases: totalEligible, diagnostic_cases: totalDiagnostic,
      total_mutations: coveredIds.reduce((n, id) => n + parts[id].mutations.length, 0),
    },
  }
}

function report(d) {
  const lines = [
    '# Loop-proof cluster oracle-b report', '',
    'Hermetic JS oracle for the expensive half of the eight-program loop-proof-blocked cluster. Ground truth for the future C++20 port\'s bit-exact parity tests, once each program\'s loop-proof gate clears.', '',
    `Programs covered with a full discriminating oracle: **${d.eligibility_summary.programs_covered}**. Programs that could not be covered: **${d.eligibility_summary.programs_blocked}** (\`classicNoisedeck/effects:effects\` -- see below).`, '',
    `Total cases across the seven covered programs: **${d.eligibility_summary.total_cases}** (${d.eligibility_summary.eligible_cases} closure-exercising + ${d.eligibility_summary.diagnostic_cases} diagnostic). Total mutations: **${d.eligibility_summary.total_mutations}**.`, '',
    '## Ground truth per program', '',
    '| Program | Ground truth | Notes |', '| --- | --- | --- |',
    '| nmReindexReduce | canonical factory | clean, no adapter override |',
    '| mandelbrot | canonical factory | clean, no adapter override |',
    '| median | **adapter** (`medianFactory`) | canonical factory (`canonicalFactory80`) CRASHES on a 5x5 render -- see below |',
    '| classicNoisedeck/noise | canonical factory | clean, no adapter override |',
    '| synth/noise | canonical factory | clean, no adapter override |',
    '| testPattern | canonical factory | clean, no adapter override |',
    '| fractal | **adapter** (`fractalFactory`) | NO canonical factory exists at all -- permanent architectural routing, `generatedBytes: 0` |',
    '| effects | n/a -- UNCOVERABLE | dead code at the authorized define, see below |',
    '',
    '## Per-program summary', '',
    '| Program | Cases | Diagnostic | Mutations | All mutations diverge on >=1 reach-eligible case |', '| --- | ---: | ---: | ---: | --- |',
  ]
  for (const [id, p] of Object.entries(d.programs)) {
    const eligible = p.cases.filter((c) => !c.diagnostic).length
    const diagnostic = p.cases.filter((c) => c.diagnostic).length
    const allDiverge = p.mutations.every((m) => m.summary.divergent_reaching > 0)
    lines.push(`| ${id} | ${eligible} | ${diagnostic} | ${p.mutations.length} | ${allDiverge} |`)
  }
  lines.push('| effects | -- | -- | -- | **UNCOVERABLE -- see below** |')
  lines.push('')
  for (const [id, p] of Object.entries(d.programs)) {
    lines.push(`## \`${p.key}\` (${id})`, '')
    lines.push(`Defines: \`${JSON.stringify(p.defines)}\`. Ground truth: ${p.ground_truth ?? 'canonical factory (clean, verified)'}`, '')
    lines.push('### Cases', '', '| Case | Size | Diagnostic | Reach | F32 SHA-256 | RGBA8 SHA-256 |', '| --- | --- | --- | --- | --- | --- |')
    for (const c of p.cases) {
      lines.push(`| ${c.name} | ${c.dimensions.width}x${c.dimensions.height} | ${c.diagnostic} | ${JSON.stringify(c.reach)} | \`${c.output.f32_sha256.slice(0, 16)}...\` | \`${c.output.rgba8_sha256.slice(0, 16)}...\` |`)
    }
    lines.push('', '### Mutations -- empirical divergence figures', '', '| Mutation | Kind | Reaching cases | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |', '| --- | --- | ---: | ---: | ---: | ---: |')
    for (const m of p.mutations) {
      lines.push(`| ${m.id} | ${m.kind} | ${m.summary.reaching_cases} | ${m.summary.divergent_reaching} | ${m.summary.non_reaching_cases} | ${m.summary.divergent_non_reaching} |`)
    }
    lines.push('', ...p.mutations.map((m) => `- **${m.id}**: ${m.description}`), '')
    if (p.canonical_factory_defect) {
      lines.push('### Canonical-factory defect (median)', '', 'The GLSL-transpiled `canonicalFactory80` crashes on certain input sizes; the adapter (used as this oracle\'s ground truth) does not.', '', '| Size | Threw | Message |', '| --- | --- | --- |')
      for (const a of p.canonical_factory_defect.attempts) lines.push(`| ${a.width}x${a.height} | ${a.threw} | ${a.message ?? '--'} |`)
      lines.push('', p.canonical_factory_defect.isolated_repro_note, '')
    }
    if (p.avoided_mutation) {
      lines.push('### Avoided mutation site (median)', '', `Anchor: \`${p.avoided_mutation.anchor}\`. Attempted mutation: \`${p.avoided_mutation.attempted_mutation}\`.`, '', `**Outcome:** ${p.avoided_mutation.outcome}`, '', `**Root cause:** ${p.avoided_mutation.root_cause}`, '', `**Disposition:** ${p.avoided_mutation.disposition}`, '')
    }
  }
  lines.push('## `classicNoisedeck/effects:effects` -- UNCOVERABLE', '')
  lines.push(d.effects.reason, '')
  lines.push('### Live evidence captured by this generator', '')
  const ev = d.effects.evidence
  lines.push(`- \`EFFECT\` confirmed bound as a runtime uniform: **${ev.effect_bound_as_runtime_uniform}** (\`var EFFECT = $bindings["EFFECT"];\`)`)
  lines.push(`- Authorized defines: \`${JSON.stringify(ev.authorized_defines)}\``)
  lines.push(`- Mutation: \`${ev.mutation_description}\` (anchor \`${ev.mutation_anchor}\`)`)
  lines.push(`- At the authorized default (EFFECT=0), across effectAmt in {0,5,10,20}: **0/4 diverged**`, '')
  lines.push('  | effectAmt | EFFECT | Diverges |', '  | ---: | ---: | --- |')
  for (const r of ev.at_authorized_default) lines.push(`  | ${r.effectAmt} | ${r.EFFECT} | ${r.diverges} |`)
  lines.push('', `- At an UNAUTHORIZED control value (EFFECT=1, effectAmt=10): **diverges=${ev.at_unauthorized_control.diverges}** -- proves the loop and mutation are real, just unreachable at the authorized default.`, '')
  return lines.join('\n')
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
async function main() {
  if (DO_CHECK) {
    const parts = loadAllCheckpoints()
    const data = buildFinal(parts)
    const json = `${JSON.stringify(data, null, 2)}\n`
    const md = `${report(data)}\n`
    if (!fs.existsSync(outPath) || fs.readFileSync(outPath, 'utf8') !== json) throw new Error('loopproof-b oracle JSON drift')
    if (!fs.existsSync(reportPath) || fs.readFileSync(reportPath, 'utf8') !== md) throw new Error('loopproof-b oracle report drift')
    console.log(`loopproof-b oracle fixture ok (${data.eligibility_summary.programs_covered} programs covered + 1 documented blocker, ${data.eligibility_summary.total_cases} cases, ${data.eligibility_summary.total_mutations} mutations)`)
    return
  }

  if (shouldRun('nmReindexReduce')) runCanonicalProgram(nmReindexReduce)
  if (shouldRun('mandelbrot')) runCanonicalProgram(mandelbrotProgram)
  if (shouldRun('classicNoisedeckNoise')) runCanonicalProgram(classicNoiseProgram)
  if (shouldRun('synthNoise')) runCanonicalProgram(synthNoiseProgram)
  if (shouldRun('testPattern')) runCanonicalProgram(testPatternProgram)
  if (shouldRun('median')) await runAdapterProgram(medianProgram)
  if (shouldRun('fractal')) await runAdapterProgram(fractalProgram)
  if (shouldRun('effects')) runEffectsBlocked()

  if (DO_ASSEMBLE) {
    const parts = loadAllCheckpoints()
    const data = buildFinal(parts)
    const json = `${JSON.stringify(data, null, 2)}\n`
    const md = `${report(data)}\n`
    fs.writeFileSync(outPath, json)
    fs.writeFileSync(`${outPath}.sha256`, `${sha256(json)}  ${path.basename(outPath)}\n`)
    fs.writeFileSync(reportPath, md)
    fs.writeFileSync(`${reportPath}.sha256`, `${sha256(md)}  ${path.basename(reportPath)}\n`)
    console.log(outPath)
    console.log(reportPath)
  }
}

await main()
