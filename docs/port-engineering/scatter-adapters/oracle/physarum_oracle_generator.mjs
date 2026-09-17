// `points/physarum:deposit` scatter-pass oracle. Imports the REAL,
// unmodified `physarumDepositAdapter` directly. See
// lenia_oracle_generator.mjs for the shared methodology notes.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { physarumDepositAdapter } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/cpu/points-deposit.js'
import { Surface } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/surface.js'

import { CaseWriter, makeSurfaceData, mulberry32, randomInt, randomUniform } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'physarum-oracles.json')
const reportPath = path.join(here, 'physarum-oracle-report.md')
const fuzzPath = path.join(here, 'physarum-fuzz.bin')

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

function runCase({ width, height, deposit, destWidth, destHeight, xyzData, rgbaData, destSeed }) {
  const xyzTex = new Surface(width, height, xyzData.slice())
  const rgbaTex = new Surface(width, height, rgbaData.slice())
  const destination = new Surface(destWidth, destHeight, destSeed.slice())
  const result = physarumDepositAdapter({
    pass: {},
    uniforms: { deposit },
    bindings: {},
    inputs: { xyzTex, rgbaTex },
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
  const deposit = opts.deposit ?? randomUniform(rng, { min: -5, max: 5 })
  const xyzData = opts.xyzData ?? makeSurfaceData(rng, width, height)
  const rgbaData = opts.rgbaData ?? makeSurfaceData(rng, width, height)
  const destSeed = opts.destSeed ?? makeSurfaceData(rng, destWidth, destHeight)
  const first = runCase({ width, height, deposit, destWidth, destHeight, xyzData, rgbaData, destSeed })
  const again = runCase({ width, height, deposit, destWidth, destHeight, xyzData, rgbaData, destSeed })
  if (!buffersIdentical(first.outputData, again.outputData) || first.pixels !== again.pixels) {
    throw new Error('physarum oracle case is non-deterministic')
  }
  return { width, height, destWidth, destHeight, deposit, xyzData, rgbaData, destSeed, ...first }
}

function main() {
  const rng = mulberry32(0x9101a)
  const cases = []

  // pos.w < 0.5 skip.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      deposit: 3,
      xyzData: new Float32Array([0.5, 0.5, 0, 0.2]),
      rgbaData: new Float32Array([1, 1, 1, 1]),
      destSeed: new Float32Array([0, 0, 0, 0]),
    })
  )
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 1,
      destHeight: 1,
      deposit: 3,
      xyzData: new Float32Array([0.5, 0.5, 0, 0.5]),
      rgbaData: new Float32Array([0.25, 0.5, 0.75, 1]),
      destSeed: new Float32Array([0, 0, 0, 0]),
    })
  )
  cases.push(buildCase(rng, { width: 1, height: 1, destWidth: 1, destHeight: 1, deposit: Number.NaN }))
  cases.push(buildCase(rng, { width: 1, height: 1, destWidth: 1, destHeight: 1, deposit: Number.POSITIVE_INFINITY }))
  cases.push(buildCase(rng, { width: 6, height: 6, destWidth: 2, destHeight: 2 }))

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
  const deposits = [0, 1, -1, 0.001, 500]
  for (const [w, h] of sizes) {
    for (const deposit of deposits) {
      cases.push(buildCase(rng, { width: w, height: h, destWidth: w, destHeight: h, deposit }))
    }
  }
  for (let i = 0; i < 60; i += 1) cases.push(buildCase(rng))

  const jsonCases = cases.map((c, index) => ({
    index,
    width: c.width,
    height: c.height,
    destWidth: c.destWidth,
    destHeight: c.destHeight,
    deposit: c.deposit,
    xyzDataHex: toHex(c.xyzData),
    rgbaDataHex: toHex(c.rgbaData),
    destSeedHex: toHex(c.destSeed),
    expectedPixels: c.pixels,
    expectedOutputHex: toHex(c.outputData),
    expectedOutputSha256: sha256(Buffer.from(c.outputData.buffer, c.outputData.byteOffset, c.outputData.byteLength)),
  }))
  fs.writeFileSync(jsonPath, JSON.stringify({ adapter: 'points/physarum:deposit', cases: jsonCases }, null, 2))
  fs.writeFileSync(
    reportPath,
    [
      '# points/physarum:deposit oracle',
      '',
      `Cases: ${cases.length} (curated, see physarum-oracles.json).`,
      `Fuzz sweep: ${FUZZ_COUNT} cases in physarum-fuzz.bin.`,
      '',
    ].join('\n')
  )

  const writer = new CaseWriter(fuzzPath)
  const fuzzRng = mulberry32(0x9101af22)
  for (let i = 0; i < FUZZ_COUNT; i += 1) {
    const width = randomInt(fuzzRng, 1, 6)
    const height = randomInt(fuzzRng, 1, 6)
    const destWidth = randomInt(fuzzRng, 1, 6)
    const destHeight = randomInt(fuzzRng, 1, 6)
    const deposit = randomUniform(fuzzRng, { min: -10, max: 10 })
    const xyzData = makeSurfaceData(fuzzRng, width, height)
    const rgbaData = makeSurfaceData(fuzzRng, width, height)
    const destSeed = makeSurfaceData(fuzzRng, destWidth, destHeight)
    const { pixels, outputData } = runCase({ width, height, deposit, destWidth, destHeight, xyzData, rgbaData, destSeed })
    writer.writeCase({
      textures: [
        { name: 'xyzTex', surface: { width, height, data: xyzData }, filterLinear: false },
        { name: 'rgbaTex', surface: { width, height, data: rgbaData }, filterLinear: false },
      ],
      uniforms: { deposit },
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
