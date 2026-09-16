#!/usr/bin/env node
// Exhaustive JS-authority side of the palette override sweep: for each of
// the six palette effects the executor actually admits (classicNoisedeck/
// shapes3d is excluded from this port's corpus at recordKind "excluded" --
// noted, not swept), every palette index 0..55, and two sizes (one square,
// one non-square), render through the pinned JS authority CpuRenderer and
// write { case_id: { rgba8Sha256, source, width, height, time, seed } } to
// a JSON file the C++ side then replays byte-for-byte.
import crypto from 'node:crypto'
import fs from 'node:fs'

import { createDefaultRegistry, kernelFactories, kernels } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/catalog.js'
import { CpuRenderer } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/renderer.js'

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex') }
function renderer() { return new CpuRenderer({ registry: createDefaultRegistry(), kernels, kernelFactories, tileRows: 8 }) }

const SIZES = [
  { width: 24, height: 24, label: 'square' },
  { width: 37, height: 13, label: 'nonsquare' },
]

// Base params exactly matching each effect's DSL corpus default record
// (tests/fixtures/dsl/executable-corpus.json), varying only `palette`.
const EFFECTS = {
  cellNoise: {
    make: (n) => `search synth, classicNoisedeck\nsolid(color: #3a7).cellNoise(shape: 0, scale: 75, cellScale: 87, smooth: 11, variation: 50, speed: 1, paletteMode: 4, seed: 1, colorMode: 0, palette: ${n}, paletteOffset: [0.5, 0.5, 0.5], cyclePalette: 1, paletteAmp: [0.5, 0.5, 0.5], rotatePalette: 0, paletteFreq: [2, 2, 2], repeatPalette: 1, palettePhase: [1, 1, 1], tex: none, texInfluence: 2, texIntensity: 0).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 2170337908,
  },
  colorLab: {
    make: (n) => `search synth, classicNoisedeck\nsolid(color: #3a7).colorLab(colorMode: 2, palette: ${n}, paletteMode: 0, paletteOffset: [0.83, 0.6, 0.63], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0.3, 0.1, 0], cyclePalette: 1, rotatePalette: 0, repeatPalette: 1, hueRotation: 0, hueRange: 100, saturation: 0, invert: false, brightness: 0, contrast: 50, levels: 0, dither: 0).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 168746864,
  },
  fractal: {
    make: (n) => `search classicNoisedeck\nfractal(type: 0, symmetry: 0, zoomAmt: 0, rotation: 0, speed: 30, offsetX: 70, offsetY: 50, centerX: 0, centerY: 0, mode: 0, iterations: 50, colorMode: 4, palette: ${n}, paletteMode: 0, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0, 0, 0], cyclePalette: 1, rotatePalette: 0, repeatPalette: 1, hueRange: 100, levels: 0, bgColor: #000000, bgAlpha: 100, cutoff: 0).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 3956202905,
  },
  noise: {
    make: (n) => `search classicNoisedeck\nnoise(type: 10, octaves: 2, xScale: 75, yScale: 75, ridges: false, wrap: true, seed: 1, refractMode: 2, refractAmt: 0, loopOffset: 300, loopScale: 75, speed: 25, kaleido: 1, metric: 0, paletteMode: 3, hueRotation: 179, hueRange: 25, colorMode: 6, palette: ${n}, cyclePalette: 1, rotatePalette: 0, repeatPalette: 1, paletteOffset: [0.5, 0.5, 0.5], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0.3, 0.2, 0.2]).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 2396922987,
  },
  shapeMixer: {
    make: (n) => `search synth, classicNoisedeck\nsolid(color: #3a7).shapeMixer(tex: none, blendMode: 2, loopOffset: 10, loopScale: 80, wrap: true, seed: 1, animate: 1, palette: ${n}, paletteMode: 0, paletteOffset: [0.83, 0.6, 0.63], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0.3, 0.1, 0], cyclePalette: 1, rotatePalette: 0, repeatPalette: 1, levels: 0).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 3115229185,
  },
  shapes: {
    make: (n) => `search classicNoisedeck\nshapes(loopAOffset: 40, loopBOffset: 30, loopAScale: 1, loopBScale: 1, speedA: 50, speedB: 50, seed: 1, wrap: true, palette: ${n}, paletteMode: 0, paletteOffset: [0.83, 0.6, 0.63], paletteAmp: [0.5, 0.5, 0.5], paletteFreq: [1, 1, 1], palettePhase: [0.3, 0.1, 0], cyclePalette: 1, rotatePalette: 0, repeatPalette: 1).write(o0)\nrender(o0)\n`,
    time: 0.25, seed: 2214277204,
  },
}

const cases = []
for (const [name, spec] of Object.entries(EFFECTS)) {
  for (let entry = 0; entry <= 55; entry++) {
    for (const size of SIZES) {
      const source = spec.make(entry)
      const result = renderer().render(source, { width: size.width, height: size.height, time: spec.time, seed: spec.seed, oneShot: 'ready' })
      const rgba = Buffer.from(result.toRgba8())
      cases.push({
        case_id: `${name}/${entry}/${size.label}`,
        effect: name, entry, size: size.label,
        source, width: size.width, height: size.height, time: spec.time, seed: spec.seed,
        rgba8_sha256: sha256(rgba),
      })
    }
  }
}
fs.writeFileSync('/private/tmp/claude-502/-Users-alex-platform-scaffold/4b35d94f-8f1c-451d-b220-88b458c1bfa7/scratchpad/exhaustive_cases.json', JSON.stringify(cases))
console.log(`wrote ${cases.length} cases`)
