// `points/lenia:deposit` scatter-pass oracle. Imports the REAL, unmodified
// `leniaDepositAdapter` from the pinned authority snapshot and calls it
// directly -- never reimplemented. Produces:
//   lenia-oracles.json        a curated, human-reviewable case set (hand
//                             cases + a size sweep), with full float32
//                             destination-buffer bytes embedded as hex.
//   lenia-fuzz.bin            a large randomized differential-sweep case
//                             file for tools/parity/scatter_fuzz_verify
//                             (see docs/port-engineering/scatter-adapters/
//                             oracle/common.mjs's CaseWriter for the binary
//                             record layout).
//
// Run: node lenia_oracle_generator.mjs [--fuzz-count=N]
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { leniaDepositAdapter } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/cpu/points-deposit.js'
import { Surface } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/surface.js'

import { CaseWriter, finalizeCaseCount, makeSurfaceData, mulberry32, randomInt, randomUniform } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'lenia-oracles.json')
const reportPath = path.join(here, 'lenia-oracle-report.md')
const fuzzPath = path.join(here, 'lenia-fuzz.bin')

const fuzzCountArg = process.argv.find((a) => a.startsWith('--fuzz-count='))
const FUZZ_COUNT = fuzzCountArg ? Number.parseInt(fuzzCountArg.split('=')[1], 10) : 12000

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex')
}

function toHex(float32Array) {
  return Buffer.from(float32Array.buffer, float32Array.byteOffset, float32Array.byteLength).toString('hex')
}

// Runs the real adapter once, returns { pixels, outputData }. `destSeed`
// is cloned before the call so the caller's copy is never mutated by the
// adapter (byte-unmutated-input discipline, mirroring the wormhole oracle).
function runCase({ width, height, depositAmount, destWidth, destHeight, xyzData, destSeed }) {
  const xyzTex = new Surface(width, height, xyzData.slice())
  const destination = new Surface(destWidth, destHeight, destSeed.slice())
  const result = leniaDepositAdapter({
    pass: {},
    uniforms: { depositAmount },
    bindings: {},
    inputs: { xyzTex },
    destination,
    params: {},
  })
  return { pixels: result.pixels, outputData: destination.data }
}

function buildCase(rng, opts = {}) {
  const width = opts.width ?? randomInt(rng, 1, 6)
  const height = opts.height ?? randomInt(rng, 1, 6)
  const destWidth = opts.destWidth ?? randomInt(rng, 1, 6)
  const destHeight = opts.destHeight ?? randomInt(rng, 1, 6)
  const depositAmount = opts.depositAmount ?? randomUniform(rng, { min: -5, max: 5 })
  const xyzData = opts.xyzData ?? makeSurfaceData(rng, width, height)
  const destSeed = opts.destSeed ?? makeSurfaceData(rng, destWidth, destHeight)
  const { pixels, outputData } = runCase({ width, height, depositAmount, destWidth, destHeight, xyzData, destSeed })
  // Determinism check: rerun from the same byte-cloned inputs, require an
  // identical result.
  const again = runCase({ width, height, depositAmount, destWidth, destHeight, xyzData, destSeed })
  if (!buffersIdentical(outputData, again.outputData) || pixels !== again.pixels) {
    throw new Error('lenia oracle case is non-deterministic')
  }
  return { width, height, destWidth, destHeight, depositAmount, xyzData, destSeed, pixels, outputData }
}

function buffersIdentical(a, b) {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i += 1) {
    const av = a[i]
    const bv = b[i]
    if (av !== bv && !(Number.isNaN(av) && Number.isNaN(bv))) return false
  }
  return true
}

function main() {
  const rng = mulberry32(0x1e401a)
  const cases = []

  // Hand-designed discrimination cases.
  // 1x1, all-alive, positive depositAmount, matching dest.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      depositAmount: 1.25,
      xyzData: new Float32Array([0.5, 0.5, 0.0, 1.0]),
      destSeed: new Float32Array([0, 0, 0, 0]),
    })
  )
  // Dead agent (w < 0.5) must skip entirely -- destination unchanged.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      depositAmount: 9.0,
      xyzData: new Float32Array([0.5, 0.5, 0.0, 0.0]),
      destSeed: new Float32Array([1, 2, 3, 4]),
    })
  )
  // w exactly 0.5 boundary -- alive (>= 0.5 keeps).
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      depositAmount: 2.0,
      xyzData: new Float32Array([0.5, 0.5, 0.0, 0.5]),
      destSeed: new Float32Array([0, 0, 0, 0]),
    })
  )
  // Off-canvas landing (xyz maps outside [0, destWidth)).
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 4,
      destHeight: 4,
      depositAmount: 3.0,
      xyzData: new Float32Array([5.0, 5.0, 0.0, 1.0]),
      destSeed: new Float32Array(4 * 4 * 4),
    })
  )
  // NaN depositAmount propagation.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      depositAmount: Number.NaN,
      xyzData: new Float32Array([0.5, 0.5, 0.0, 1.0]),
      destSeed: new Float32Array([0, 0, 0, 0]),
    })
  )
  // Non-square agent texture (dla-style dimension generality is NOT
  // assumed here, but must still not crash: width != height).
  cases.push(buildCase(rng, { width: 1, height: 7 }))
  cases.push(buildCase(rng, { width: 7, height: 1 }))
  cases.push(buildCase(rng, { width: 5, height: 3, destWidth: 5, destHeight: 3 }))
  cases.push(buildCase(rng, { width: 9, height: 13, destWidth: 9, destHeight: 13 }))
  // destination smaller/larger than agent texture (independent dims).
  cases.push(buildCase(rng, { width: 8, height: 8, destWidth: 3, destHeight: 3 }))
  cases.push(buildCase(rng, { width: 3, height: 3, destWidth: 8, destHeight: 8 }))
  // Overlapping deposits: many agents, small destination -- forces
  // multiple agents to land on the same pixel (accumulation order matters).
  cases.push(buildCase(rng, { width: 6, height: 6, destWidth: 2, destHeight: 2 }))

  // Systematic size sweep x a few depositAmount values.
  const sizes = [
    [1, 1],
    [1, 7],
    [7, 1],
    [2, 2],
    [4, 4],
    [5, 3],
    [9, 13],
    [16, 16],
  ]
  const amounts = [0, 1, -1, 0.001, 1000]
  for (const [w, h] of sizes) {
    for (const amount of amounts) {
      cases.push(buildCase(rng, { width: w, height: h, destWidth: w, destHeight: h, depositAmount: amount }))
    }
  }

  // Broad random cases rounding out the curated set.
  for (let i = 0; i < 60; i += 1) cases.push(buildCase(rng))

  const jsonCases = cases.map((c, index) => ({
    index,
    width: c.width,
    height: c.height,
    destWidth: c.destWidth,
    destHeight: c.destHeight,
    depositAmount: c.depositAmount,
    xyzDataHex: toHex(c.xyzData),
    destSeedHex: toHex(c.destSeed),
    expectedPixels: c.pixels,
    expectedOutputHex: toHex(c.outputData),
    expectedOutputSha256: sha256(Buffer.from(c.outputData.buffer, c.outputData.byteOffset, c.outputData.byteLength)),
  }))

  fs.writeFileSync(jsonPath, JSON.stringify({ adapter: 'points/lenia:deposit', cases: jsonCases }, null, 2))

  const report = [
    '# points/lenia:deposit oracle',
    '',
    `Cases: ${cases.length} (curated, see lenia-oracles.json).`,
    `Fuzz sweep: ${FUZZ_COUNT} cases in lenia-fuzz.bin (see scatter_fuzz_verify's report for divergence results).`,
    '',
    'Every curated case was rendered twice from byte-identical inputs and required to be byte-identical (determinism check passed for all cases).',
    '',
  ].join('\n')
  fs.writeFileSync(reportPath, report)

  // Large randomized differential sweep.
  const writer = new CaseWriter(fuzzPath)
  const fuzzRng = mulberry32(0x7e11a)
  for (let i = 0; i < FUZZ_COUNT; i += 1) {
    const width = randomInt(fuzzRng, 1, 6)
    const height = randomInt(fuzzRng, 1, 6)
    const destWidth = randomInt(fuzzRng, 1, 6)
    const destHeight = randomInt(fuzzRng, 1, 6)
    const depositAmount = randomUniform(fuzzRng, { min: -10, max: 10 })
    const xyzData = makeSurfaceData(fuzzRng, width, height)
    const destSeed = makeSurfaceData(fuzzRng, destWidth, destHeight)
    const { pixels, outputData } = runCase({ width, height, depositAmount, destWidth, destHeight, xyzData, destSeed })
    writer.writeCase({
      textures: [{ name: 'xyzTex', surface: { width, height, data: xyzData }, filterLinear: false }],
      uniforms: { depositAmount },
      blend: null,
      count: null,
      destWidth,
      destHeight,
      destSeedData: destSeed,
      expectedData: outputData,
      expectedPixels: pixels,
    })
  }
  writer.close()

  console.log(`wrote ${cases.length} curated cases to ${jsonPath}`)
  console.log(`wrote ${FUZZ_COUNT} fuzz cases to ${fuzzPath}`)
}

main()
