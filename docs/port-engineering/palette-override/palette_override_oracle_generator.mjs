#!/usr/bin/env node
// Frozen-authority pixel oracle for the classicNoisedeck palette override.
//
// Renders each of the six affected effects (cellNoise, colorLab, fractal,
// noise, shapeMixer, shapes) through the full JS authority Renderer -- the
// same buildBindings() path the C++ executor's
// apply_classic_noisedeck_palette_override() mirrors -- at several palette
// entries (0, 1, the effect's own default, a couple in between, and 55) and,
// for effects whose colorMode can bypass the palette entirely, at a
// colorMode that actually exercises pal(). A couple of cases also perturb
// other, non-palette parameters. Every render is 17x11 (matching the DSL
// corpus lane's own default-record size) and captured as both an RGBA8
// digest and a raw little-endian Float32 digest.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'palette-override-oracles.json')

function sha256(value) { return crypto.createHash('sha256').update(value).digest('hex') }
function sidecarPath(target) { return `${target}.sha256` }
function sidecarText(target, payload) { return `${sha256(payload)}  ${path.basename(target)}\n` }
function writeChecked(target, payload) {
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, payload)
  fs.writeFileSync(sidecarPath(target), sidecarText(target, payload))
}
function verifySidecar(target) {
  if (!fs.existsSync(target) || !fs.existsSync(sidecarPath(target))) throw new Error(`missing sidecar: ${target}`)
  const payload = fs.readFileSync(target)
  if (fs.readFileSync(sidecarPath(target), 'utf8') !== sidecarText(target, payload)) throw new Error(`sidecar drift: ${target}`)
  return payload
}
function rejectSymlinkLeaf(candidate, label) {
  try { if (fs.lstatSync(path.resolve(candidate)).isSymbolicLink()) throw new Error(`${label} must not be a symlink`) }
  catch (error) { if (error?.code !== 'ENOENT') throw error }
}

const args = process.argv.slice(2)
const mode = args.find((token) => ['--write', '--check'].includes(token))
if (!mode || args.filter((token) => ['--write', '--check'].includes(token)).length !== 1) {
  throw new Error('choose exactly one of --write or --check')
}
const cpuIndex = args.indexOf('--cpu-root')
if (cpuIndex < 0) throw new Error('--cpu-root <immutable authority snapshot> is required')
const cpuArg = args[cpuIndex + 1]
rejectSymlinkLeaf(cpuArg, '--cpu-root')
if (!fs.statSync(cpuArg).isDirectory()) throw new Error('--cpu-root is not a directory')
const cpuRoot = fs.realpathSync(cpuArg)

const load = (relative) => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const { createDefaultRegistry, kernelFactories, kernels } = await load('src/effects/catalog.js')
const { CpuRenderer } = await load('src/runtime/renderer.js')

function renderer() {
  return new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories, tileRows: 8 })
}
function rawBytes(view) { return Buffer.from(view.buffer, view.byteOffset, view.byteLength) }

// width/height match the DSL corpus lane's own default-record size, so this
// oracle exercises the same render shape the corpus lane verifies.
const WIDTH = 17
const HEIGHT = 11

function renderCase(source, options) {
  const result = renderer().render(source, { width: WIDTH, height: HEIGHT, oneShot: 'ready', ...options })
  const rgba = Buffer.from(result.toRgba8())
  return {
    rgba8_sha256: sha256(rgba),
    f32_sha256: sha256(rawBytes(result.surface.data)),
    first_rgba8_bytes: Array.from(rgba.subarray(0, 16)),
  }
}

// Each effect's own params, exactly matching its DSL corpus default record
// (tests/fixtures/dsl/executable-corpus.json) except where a case
// deliberately varies palette / colorMode / another named parameter. `base`
// never repeats a key with an override: every value this generator varies
// across cases is deliberately left OUT of `base` and always supplied by the
// call site instead, so a DSL source can never carry the same parameter
// twice (the compiler's own last-write-wins would otherwise mask a bug here
// silently).
function dslCall(prelude, call, params) {
  const text = Object.entries(params).map(([key, value]) => `${key}: ${value}`).join(', ')
  return `${prelude}\n${call}(${text}).write(o0)\nrender(o0)\n`
}

const effects = {
  cellNoise: {
    call: (params) => dslCall('search synth, classicNoisedeck', 'solid(color: #3a7).cellNoise', params),
    base: { shape: 0, scale: 75, cellScale: 87, smooth: 11, paletteMode: 4, seed: 1, tex: 'none', texInfluence: 2, texIntensity: 0, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { variation: 50, speed: 1 },
    variableNonDefault: { variation: 80, speed: 3 },
    defaultEntry: 32,
    paletteColorMode: 2,  // "palette" choice; the corpus default (0 = mono) never reads pal().
    defaultColorMode: 0,
    options: { time: 0.25, seed: 2170337908 },
  },
  colorLab: {
    call: (params) => dslCall('search synth, classicNoisedeck', 'solid(color: #3a7).colorLab', params),
    base: { paletteMode: 0, saturation: 0, invert: false, levels: 0, dither: 0, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { hueRotation: 0, brightness: 0, contrast: 50, hueRange: 100 },
    variableNonDefault: { hueRotation: 40, brightness: 15, contrast: 70, hueRange: 100 },
    defaultEntry: 46,
    paletteColorMode: 4,
    defaultColorMode: 2,
    options: { time: 0.25, seed: 168746864 },
  },
  fractal: {
    call: (params) => dslCall('search classicNoisedeck', 'fractal', params),
    base: { type: 0, symmetry: 0, zoomAmt: 0, speed: 30, centerX: 0, centerY: 0, mode: 0, iterations: 50, paletteMode: 0, hueRange: 100, levels: 0, bgColor: '#000000', bgAlpha: 100, cutoff: 0, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { rotation: 0, offsetX: 70, offsetY: 50 },
    variableNonDefault: { rotation: 45, offsetX: 20, offsetY: 85 },
    defaultEntry: 12,
    paletteColorMode: 4,  // the corpus default already is "palette".
    defaultColorMode: 4,
    options: { time: 0.25, seed: 3956202905 },
  },
  noise: {
    call: (params) => dslCall('search classicNoisedeck', 'noise', params),
    base: { type: 10, octaves: 2, xScale: 75, yScale: 75, ridges: false, wrap: true, seed: 1, refractMode: 2, refractAmt: 0, loopOffset: 300, loopScale: 75, speed: 25, metric: 0, paletteMode: 3, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { hueRotation: 179, hueRange: 25, kaleido: 1 },
    variableNonDefault: { hueRotation: 60, hueRange: 90, kaleido: 3 },
    defaultEntry: 2,
    // colorMode, loopOffset, metric, type and refractMode are compile
    // defines baked into this port's "default-only" generated route for
    // classicNoisedeck/noise (tools/glslcpp/typed_slice.json) -- a real,
    // pre-existing port limitation unrelated to the palette override (the
    // same class of limitation as filter/median's baked RADIUS, already
    // excluded in tests/oracles/dsl_corpus_parity_exclusions.json). This
    // port cannot request colorMode: 4 ("palette") for noise, so its default
    // colorMode (6, "hsv") -- which never reads pal() either -- is kept
    // everywhere; only hueRotation/hueRange/kaleido (real uniforms) vary.
    paletteColorMode: null,
    defaultColorMode: 6,
    options: { time: 0.25, seed: 2396922987 },
  },
  shapeMixer: {
    call: (params) => dslCall('search synth, classicNoisedeck', 'solid(color: #3a7).shapeMixer', params),
    base: { tex: 'none', blendMode: 2, wrap: true, seed: 1, animate: 1, paletteMode: 0, levels: 0, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { loopOffset: 10, loopScale: 80 },
    // loopOffset is a compile define baked into this port's generated route
    // (LOOP_OFFSET in tools/glslcpp/typed_slice.json) and cannot vary; only
    // loopScale (a real uniform) does.
    variableNonDefault: { loopOffset: 10, loopScale: 40 },
    defaultEntry: 41,
    paletteColorMode: null,  // no colorMode gate: always palette-driven.
    defaultColorMode: null,
    options: { time: 0.25, seed: 3115229185 },
  },
  shapes: {
    call: (params) => dslCall('search classicNoisedeck', 'shapes', params),
    base: { loopBOffset: 30, loopBScale: 1, speedB: 50, seed: 1, wrap: true, paletteMode: 0, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1 },
    variable: { loopAOffset: 40, loopAScale: 1, speedA: 50 },
    // loopAOffset (and loopBOffset, held fixed in `base`) are compile
    // defines baked into this port's generated route (LOOP_A_OFFSET /
    // LOOP_B_OFFSET) and cannot vary; only loopAScale/speedA (real uniforms)
    // do.
    variableNonDefault: { loopAOffset: 40, loopAScale: 2, speedA: 80 },
    defaultEntry: 46,
    paletteColorMode: null,
    defaultColorMode: null,
    options: { time: 0.25, seed: 2214277204 },
  },
}

for (const [name, spec] of Object.entries(effects)) {
  const overlap = Object.keys(spec.base).filter((key) => key in spec.variable)
  if (overlap.length > 0) throw new Error(`${name}: base/variable key overlap: ${overlap.join(', ')}`)
}

function buildSource(spec, { colorMode, palette, variable }) {
  const params = { ...spec.base, ...variable }
  if (colorMode !== null && colorMode !== undefined) params.colorMode = colorMode
  params.palette = palette
  return spec.call(params)
}

const document = { schema: 'noisemaker-for-cpu.classic-noisedeck-palette-override.pixel-parity.v1', width: WIDTH, height: HEIGHT, cases: [] }

for (const [name, spec] of Object.entries(effects)) {
  const sweepEntries = [...new Set([0, 1, spec.defaultEntry, 28, 55])].sort((a, b) => a - b)
  for (const entry of sweepEntries) {
    const source = buildSource(spec, { colorMode: spec.defaultColorMode, palette: entry, variable: spec.variable })
    document.cases.push({ name: `${name}/entry-${entry}`, effect: name, source, options: spec.options, ...renderCase(source, spec.options) })
  }
  if (spec.paletteColorMode !== null && spec.paletteColorMode !== spec.defaultColorMode) {
    // A colorMode that actually reads pal(), proving the override changes
    // rendered bytes rather than only binding harmlessly-unread uniforms.
    for (const entry of [spec.defaultEntry, 55]) {
      const source = buildSource(spec, { colorMode: spec.paletteColorMode, palette: entry, variable: spec.variable })
      document.cases.push({ name: `${name}/palette-colorMode-entry-${entry}`, effect: name, source, options: spec.options, ...renderCase(source, spec.options) })
    }
  }
  // Non-default *non-palette* parameters, at a non-default entry, still with
  // the identity t-scaling (rotatePalette: 0, repeatPalette: 1) every corpus
  // default already uses, and (where the effect has a colorMode gate) the
  // colorMode that actually reads pal().
  const nonDefaultColorMode = spec.paletteColorMode ?? spec.defaultColorMode
  const nonDefaultEntry = name === 'fractal' || name === 'shapes' || name === 'noise' ? 28 : 55
  const source = buildSource(spec, { colorMode: nonDefaultColorMode, palette: nonDefaultEntry, variable: spec.variableNonDefault })
  document.cases.push({ name: `${name}/non-default-other-params`, effect: name, source, options: spec.options, ...renderCase(source, spec.options) })
}

const serialized = `${JSON.stringify(document, null, 2)}\n`

// A matching native test: the same DSL programs, rendered through the
// public noisemaker::Renderer, required byte-exact against the RGBA8 digest
// this oracle captured from the authority. One TEST() per case so a failure
// names the exact case, matching the rest of this test binary's style.
const cppTestPath = path.resolve(here, '../../../tests/test_palette_override_oracle.cpp')
function cppStringLiteral(text) {
  return `"${text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`
}
function sanitizeTestName(name) {
  return name.replace(/[^A-Za-z0-9]+/g, '_')
}
const cppCases = document.cases.map((entry) => `
TEST(palette_override_oracle_${sanitizeTestName(entry.name)}) {
  // ${entry.name}: mechanically captured from the JS authority by
  // palette_override_oracle_generator.mjs -- see palette-override-oracles.json.
  Renderer renderer;
  RenderOptions options;
  options.width = ${document.width}U;
  options.height = ${document.height}U;
  options.time = ${entry.options.time};
  options.frame = 0;
  options.seed = ${entry.options.seed};
  const auto result = renderer.render(${cppStringLiteral(entry.source)}, options, "${entry.name}.dsl");
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == result.width() * result.height() * 4U);
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(bytes.data()), bytes.size())) ==
          "${entry.rgba8_sha256}");
}
`).join('')
const cppTest = `// Generated by docs/port-engineering/palette-override/palette_override_oracle_generator.mjs.
// Do not hand-edit -- regenerate from the authority instead. See
// docs/port-engineering/palette-override/palette-override-oracles.json for
// the full oracle (RGBA8 + Float32 digests, per-case DSL sources and
// options) this file's expectations are drawn from.
#include "test_harness.hpp"

#include "noisemaker/renderer.hpp"

using namespace noisemaker;
using namespace noisemaker::graph;

namespace {
${cppCases}}  // namespace
`

if (mode === '--write') {
  writeChecked(outputPath, Buffer.from(serialized))
  writeChecked(cppTestPath, Buffer.from(cppTest))
  writeChecked(fileURLToPath(import.meta.url), fs.readFileSync(fileURLToPath(import.meta.url)))
  console.log(`wrote ${document.cases.length} palette override oracle cases and their native test`)
} else {
  if (verifySidecar(outputPath).toString('utf8') !== serialized) throw new Error('palette override oracle drift: regenerate with --write')
  if (verifySidecar(cppTestPath).toString('utf8') !== cppTest) throw new Error('palette override native test drift: regenerate with --write')
  console.log(`${document.cases.length} palette override oracle cases verified against the authority`)
}
