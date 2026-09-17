// `filter3d/flow3d:deposit` scatter-pass oracle. Imports the REAL,
// unmodified `flow3dDepositAdapter` directly. See lenia_oracle_generator.mjs
// for the shared methodology notes.
//
// `pass.count` is SOMETIMES OMITTED entirely (tests the real JS `pass?.
// count ?? capacity` fallback), sometimes a plain integer, sometimes
// fractional/negative/huge/NaN (every uniform/pass-field domain edge the
// task brief calls for).
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { flow3dDepositAdapter } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/cpu/flow3d-deposit.js'
import { Surface } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/surface.js'

import { CaseWriter, makeSurfaceData, mulberry32, randomInt, randomUniform } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'flow3d-oracles.json')
const reportPath = path.join(here, 'flow3d-oracle-report.md')
const fuzzPath = path.join(here, 'flow3d-fuzz.bin')

const fuzzCountArg = process.argv.find((a) => a.startsWith('--fuzz-count='))
const FUZZ_COUNT = fuzzCountArg ? Number.parseInt(fuzzCountArg.split('=')[1], 10) : 12000

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex')
}
function toHex(float32Array) {
  return Buffer.from(float32Array.buffer, float32Array.byteOffset, float32Array.byteLength).toString('hex')
}
function buffersIdentical(a, b) {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i] && !(Number.isNaN(a[i]) && Number.isNaN(b[i]))) return false
  }
  return true
}

function runCase({ width, height, uniforms, passCount, destWidth, destHeight, state1Data, state2Data, destSeed }) {
  const stateTex1 = new Surface(width, height, state1Data.slice())
  const stateTex2 = new Surface(width, height, state2Data.slice())
  const destination = new Surface(destWidth, destHeight, destSeed.slice())
  const pass = passCount === undefined ? {} : { count: passCount }
  const result = flow3dDepositAdapter({
    pass,
    uniforms,
    bindings: {},
    inputs: { stateTex1, stateTex2 },
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
  const uniforms = opts.uniforms ?? {
    density: randomUniform(rng, { min: -5, max: 20 }),
    volumeSize: randomUniform(rng, { min: 1, max: 8 }),
  }
  const passCount = 'passCount' in opts ? opts.passCount : rng() < 0.4 ? undefined : randomUniform(rng, { min: -5, max: width * height + 5 })
  const state1Data = opts.state1Data ?? makeSurfaceData(rng, width, height)
  const state2Data = opts.state2Data ?? makeSurfaceData(rng, width, height)
  const destSeed = opts.destSeed ?? makeSurfaceData(rng, destWidth, destHeight)
  const first = runCase({ width, height, uniforms, passCount, destWidth, destHeight, state1Data, state2Data, destSeed })
  const again = runCase({ width, height, uniforms, passCount, destWidth, destHeight, state1Data, state2Data, destSeed })
  if (!buffersIdentical(first.outputData, again.outputData) || first.pixels !== again.pixels) {
    throw new Error('flow3d oracle case is non-deterministic')
  }
  return { width, height, destWidth, destHeight, uniforms, passCount, state1Data, state2Data, destSeed, ...first }
}

function main() {
  const rng = mulberry32(0xf10d3d)
  const cases = []

  // pass.count entirely absent -> falls back to capacity.
  cases.push(buildCase(rng, { width: 2, height: 2, destWidth: 4, destHeight: 4, passCount: undefined, uniforms: { density: 10, volumeSize: 2 } }))
  // pass.count = 0 -> zero agents processed.
  cases.push(buildCase(rng, { width: 3, height: 3, passCount: 0 }))
  // pass.count negative -> Math.max(0, ...) clamps to 0.
  cases.push(buildCase(rng, { width: 3, height: 3, passCount: -5 }))
  // pass.count NaN -> whole count NaN -> zero iterations.
  cases.push(buildCase(rng, { width: 3, height: 3, passCount: Number.NaN }))
  // pass.count larger than capacity -> clamped to capacity.
  cases.push(buildCase(rng, { width: 2, height: 2, passCount: 1000 }))
  // density negative -> maxAgents negative (trunc could be -0) -> clamps count near 0.
  cases.push(buildCase(rng, { width: 3, height: 3, passCount: undefined, uniforms: { density: -0.001, volumeSize: 4 } }))
  // volumeSize = 0 -> atlasHeight 0 -> division by zero -> Infinity/NaN clip coords -> discard.
  cases.push(buildCase(rng, { width: 2, height: 2, uniforms: { density: 50, volumeSize: 0 } }))
  // Non-square state textures.
  cases.push(buildCase(rng, { width: 1, height: 9 }))
  cases.push(buildCase(rng, { width: 9, height: 1 }))
  // Overlap stress: many agents into a tiny destination.
  cases.push(buildCase(rng, { width: 6, height: 6, destWidth: 2, destHeight: 2, passCount: undefined, uniforms: { density: 200, volumeSize: 6 } }))

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
  for (const [w, h] of sizes) {
    for (let i = 0; i < 4; i += 1) cases.push(buildCase(rng, { width: w, height: h, destWidth: w, destHeight: h }))
  }
  for (let i = 0; i < 70; i += 1) cases.push(buildCase(rng))

  const jsonCases = cases.map((c, index) => ({
    index,
    width: c.width,
    height: c.height,
    destWidth: c.destWidth,
    destHeight: c.destHeight,
    uniforms: c.uniforms,
    passCount: c.passCount === undefined ? null : c.passCount,
    state1DataHex: toHex(c.state1Data),
    state2DataHex: toHex(c.state2Data),
    destSeedHex: toHex(c.destSeed),
    expectedPixels: c.pixels,
    expectedOutputHex: toHex(c.outputData),
    expectedOutputSha256: sha256(Buffer.from(c.outputData.buffer, c.outputData.byteOffset, c.outputData.byteLength)),
  }))
  fs.writeFileSync(jsonPath, JSON.stringify({ adapter: 'filter3d/flow3d:deposit', cases: jsonCases }, null, 2))
  fs.writeFileSync(
    reportPath,
    ['# filter3d/flow3d:deposit oracle', '', `Cases: ${cases.length} (curated, see flow3d-oracles.json).`, `Fuzz sweep: ${FUZZ_COUNT} cases in flow3d-fuzz.bin.`, ''].join('\n')
  )

  const writer = new CaseWriter(fuzzPath)
  const fuzzRng = mulberry32(0xf10d3d22)
  for (let i = 0; i < FUZZ_COUNT; i += 1) {
    const width = randomInt(fuzzRng, 1, 6)
    const height = randomInt(fuzzRng, 1, 6)
    const destWidth = randomInt(fuzzRng, 1, 6)
    const destHeight = randomInt(fuzzRng, 1, 6)
    const uniforms = { density: randomUniform(fuzzRng, { min: -10, max: 30 }), volumeSize: randomUniform(fuzzRng, { min: -2, max: 10 }) }
    const passCount = fuzzRng() < 0.35 ? undefined : randomUniform(fuzzRng, { min: -10, max: width * height + 10 })
    const state1Data = makeSurfaceData(fuzzRng, width, height)
    const state2Data = makeSurfaceData(fuzzRng, width, height)
    const destSeed = makeSurfaceData(fuzzRng, destWidth, destHeight)
    const { pixels, outputData } = runCase({ width, height, uniforms, passCount, destWidth, destHeight, state1Data, state2Data, destSeed })
    writer.writeCase({
      textures: [
        { name: 'stateTex1', surface: { width, height, data: state1Data }, filterLinear: false },
        { name: 'stateTex2', surface: { width, height, data: state2Data }, filterLinear: false },
      ],
      uniforms,
      blend: null,
      count: passCount === undefined ? null : passCount,
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
