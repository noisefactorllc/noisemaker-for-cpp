#!/usr/bin/env node
// Mechanically derives the classicNoisedeck palette override table (55
// entries) from the frozen JS authority's own `paletteData` array
// (src/effects/generated/canonical-adapter-data.js) and emits a checked-in
// C++ header the executor's palette-override binding reads at runtime.
//
// This script never hand-types a single table value. It imports the
// authority's own module, validates its shape (55 entries x 16 numbers,
// grouped [amp.r,amp.g,amp.b,mode, freq.r,freq.g,freq.b,0, offset.r,offset.g,
// offset.b,0, phase.r,phase.g,phase.b,0] -- matching
// noisemaker-for-cpu/src/runtime/renderer.js buildBindings():
//   uniforms.paletteAmp    = entry.slice(0, 3)
//   uniforms.paletteFreq   = entry.slice(4, 7)
//   uniforms.paletteOffset = entry.slice(8, 11)
//   uniforms.palettePhase  = entry.slice(12, 15)
//   uniforms.paletteMode   = entry[3] === 0 ? 3 : entry[3]
// -- then serializes every value byte-for-byte (via each double's exact
// decimal round-trip form) into the generated header.
//
// Usage:
//   node generate_classic_noisedeck_palette_table.mjs --cpu-root <authority> --write
//   node generate_classic_noisedeck_palette_table.mjs --cpu-root <authority> --check
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.resolve(here, '../../../include/noisemaker/graph/generated/classic_noisedeck_palette_table.hpp')
const sourceRelative = 'src/effects/generated/canonical-adapter-data.js'

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

// A double's default JS stringification is the shortest decimal that
// round-trips to the exact same IEEE-754 double -- i.e. it reproduces the
// authority's literal bit pattern exactly, never merely "close enough".
function literal(value) {
  if (!Number.isFinite(value)) throw new Error(`non-finite palette table value: ${value}`)
  const text = String(value)
  if (Number(text) !== value) throw new Error(`literal round-trip failed for ${value}`)
  return text.includes('.') || text.includes('e') || text.includes('E') ? text : `${text}.0`
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

const sourcePath = path.join(cpuRoot, sourceRelative)
rejectSymlinkLeaf(sourcePath, 'authority source')
const sourceReal = fs.realpathSync(sourcePath)
if (!sourceReal.startsWith(`${cpuRoot}${path.sep}`)) throw new Error('authority source escapes the immutable snapshot')
const sourceBytes = fs.readFileSync(sourceReal)
const sourceSha = sha256(sourceBytes)

const { paletteData } = await import(pathToFileURL(sourceReal).href)
if (!Array.isArray(paletteData) || paletteData.length !== 55) {
  throw new Error(`authority paletteData must carry exactly 55 entries, found ${paletteData?.length}`)
}
const rows = paletteData.map((entry, index) => {
  if (!Array.isArray(entry) || entry.length !== 16) {
    throw new Error(`paletteData[${index}] must carry exactly 16 numbers, found ${entry?.length}`)
  }
  // Padding lanes (7, 11, 15) are always zero in the authority's vec4-grouped
  // layout; a nonzero value would mean this script's grouping assumption --
  // taken directly from renderer.js's buildBindings() slices -- no longer
  // matches the authority, and it must fail loud rather than mis-derive.
  for (const pad of [7, 11, 15]) {
    if (entry[pad] !== 0) throw new Error(`paletteData[${index}][${pad}] padding lane is not zero: ${entry[pad]}`)
  }
  const mode = entry[3]
  if (![0, 1, 2].includes(mode)) throw new Error(`paletteData[${index}] mode lane is not 0/1/2: ${mode}`)
  return {
    amp: entry.slice(0, 3),
    mode,
    freq: entry.slice(4, 7),
    offset: entry.slice(8, 11),
    phase: entry.slice(12, 15),
  }
})

const rowText = rows.map((row) => {
  const amp = `{${row.amp.map(literal).join(', ')}}`
  const freq = `{${row.freq.map(literal).join(', ')}}`
  const offset = `{${row.offset.map(literal).join(', ')}}`
  const phase = `{${row.phase.map(literal).join(', ')}}`
  return `{${amp}, ${row.mode}, ${freq}, ${offset}, ${phase}}`
})

const header = `// Generated by docs/port-engineering/palette-override/generate_classic_noisedeck_palette_table.mjs
// from the frozen JS authority's ${sourceRelative} (paletteData, sha256
// ${sourceSha}). Do not hand-edit -- regenerate from the authority instead.
//
// classicNoisedeck's palette-typed parameters select an entry (1-based) from
// this 55-entry table; entry 0 ("none") selects no override. Each entry's
// four vectors carry the *full double precision* the authority's own
// paletteData literals carry (never pre-rounded to float here) because the
// authority combines them with per-pixel values before ever narrowing to
// float32 -- see src/graph/executor.cpp's
// apply_classic_noisedeck_palette_override() for where that narrowing
// happens, once, at the same point the authority's Vec3 uniform binding
// would.
#pragma once

#include <array>

namespace noisemaker::graph::palette_table {

struct ClassicNoisedeckPaletteEntry {
  double amp[3];
  int mode;
  double freq[3];
  double offset[3];
  double phase[3];
};

inline constexpr std::array<ClassicNoisedeckPaletteEntry, ${rows.length}> kClassicNoisedeckPaletteTable = {{
${rowText.map((row) => `  ${row}`).join(',\n')},
}};

}  // namespace noisemaker::graph::palette_table
`

if (mode === '--write') {
  writeChecked(outputPath, Buffer.from(header))
  writeChecked(fileURLToPath(import.meta.url), fs.readFileSync(fileURLToPath(import.meta.url)))
  console.log(`wrote ${rows.length} palette table entries to ${path.relative(process.cwd(), outputPath)}`)
} else {
  const existing = verifySidecar(outputPath).toString('utf8')
  if (existing !== header) throw new Error('classicNoisedeck palette table drift: regenerate with --write')
  console.log(`${rows.length} palette table entries verified against the authority`)
}
