// `render/pointsRender:deposit` scatter-pass oracle. Imports the REAL,
// unmodified `pointsRenderDepositAdapter` directly (which itself calls the
// real, unmodified `computeClipCenter`/`texelFetchAgent`/`scatterPointPixel`
// from the same module -- nothing here reimplements any of that). See
// lenia_oracle_generator.mjs for the shared methodology notes.
//
// Uniform domain coverage: `viewMode` sweeps {0 (flat), 1 (ortho), 2
// (perspective), and an out-of-catalog value to exercise the `viewMode|0`
// truncation's fallthrough-to-flat branch}. `posZ`/`fieldOfView` are
// SOMETIMES OMITTED ENTIRELY from the uniforms object (not merely set to a
// default value) to exercise the real JS `?? default` fallback path, not
// just its resulting numeric value.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { pointsRenderDepositAdapter } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/cpu/points-deposit.js'
import { Surface } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/surface.js'

import { CaseWriter, makeSurfaceData, mulberry32, randomInt, randomUniform } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'points_render-oracles.json')
const reportPath = path.join(here, 'points_render-oracle-report.md')
const fuzzPath = path.join(here, 'points_render-fuzz.bin')

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

function buildUniforms(rng, overrides = {}) {
  const viewModeChoices = [0, 1, 2, 0, 1, 2, 5, -3]
  const uniforms = {
    density: randomUniform(rng, { min: -20, max: 200 }),
    viewMode: viewModeChoices[randomInt(rng, 0, viewModeChoices.length - 1)],
    rotateX: randomUniform(rng, { min: -10, max: 10 }),
    rotateY: randomUniform(rng, { min: -10, max: 10 }),
    rotateZ: randomUniform(rng, { min: -10, max: 10 }),
    posX: randomUniform(rng, { min: -50, max: 50 }),
    posY: randomUniform(rng, { min: -50, max: 50 }),
    viewScale: randomUniform(rng, { min: -5, max: 5 }),
    ...overrides,
  }
  // `posZ`/`fieldOfView` omitted ~40% of the time (tests the real JS `??`
  // fallback, not just a default numeric value).
  if (!('posZOmit' in overrides) && rng() < 0.4) {
    // omitted
  } else {
    uniforms.posZ = overrides.posZ ?? randomUniform(rng, { min: -50, max: 50 })
  }
  if (!('fieldOfViewOmit' in overrides) && rng() < 0.4) {
    // omitted
  } else {
    uniforms.fieldOfView = overrides.fieldOfView ?? randomUniform(rng, { min: -50, max: 250 })
  }
  delete uniforms.posZOmit
  delete uniforms.fieldOfViewOmit
  return uniforms
}

function runCase({ width, height, uniforms, destWidth, destHeight, xyzData, rgbaData, destSeed }) {
  const xyzTex = new Surface(width, height, xyzData.slice())
  const rgbaTex = new Surface(width, height, rgbaData.slice())
  const destination = new Surface(destWidth, destHeight, destSeed.slice())
  const result = pointsRenderDepositAdapter({
    pass: {},
    uniforms,
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
  const uniforms = opts.uniforms ?? buildUniforms(rng)
  const xyzData = opts.xyzData ?? makeSurfaceData(rng, width, height)
  const rgbaData = opts.rgbaData ?? makeSurfaceData(rng, width, height)
  const destSeed = opts.destSeed ?? makeSurfaceData(rng, destWidth, destHeight)
  const first = runCase({ width, height, uniforms, destWidth, destHeight, xyzData, rgbaData, destSeed })
  const again = runCase({ width, height, uniforms, destWidth, destHeight, xyzData, rgbaData, destSeed })
  if (!buffersIdentical(first.outputData, again.outputData) || first.pixels !== again.pixels) {
    throw new Error('points_render oracle case is non-deterministic')
  }
  return { width, height, destWidth, destHeight, uniforms, xyzData, rgbaData, destSeed, ...first }
}

function main() {
  const rng = mulberry32(0x90111a)
  const cases = []

  // Flat view, alive agent, full density.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 4,
      destHeight: 4,
      uniforms: { density: 100, viewMode: 0, rotateX: 0, rotateY: 0, rotateZ: 0, posX: 0, posY: 0, viewScale: 1 },
      xyzData: new Float32Array([0.5, 0.5, 0, 1]),
      rgbaData: new Float32Array([1, 0.5, 0.25, 1]),
      destSeed: new Float32Array(4 * 4 * 4),
    })
  )
  // Dead agent (pos.w<0.5) skip.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 4,
      destHeight: 4,
      uniforms: { density: 100, viewMode: 0, rotateX: 0, rotateY: 0, rotateZ: 0, posX: 0, posY: 0, viewScale: 1 },
      xyzData: new Float32Array([0.5, 0.5, 0, 0.1]),
      rgbaData: new Float32Array([1, 1, 1, 1]),
      destSeed: new Float32Array(4 * 4 * 4),
    })
  )
  // density = 0 -> cullThreshold 0 -> only particleRandom<=0 keeps (v=0 -> fract(0)=0, kept).
  cases.push(buildCase(rng, { width: 4, height: 4, uniforms: buildUniforms(rng, { density: 0 }) }))
  // density negative -> everything culled.
  cases.push(buildCase(rng, { width: 4, height: 4, uniforms: buildUniforms(rng, { density: -50 }) }))
  // Perspective view, camera behind near plane (should return null -> skip).
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 4,
      destHeight: 4,
      uniforms: {
        density: 100,
        viewMode: 2,
        rotateX: 0,
        rotateY: 0,
        rotateZ: 0,
        posX: 0,
        posY: 0,
        posZ: 200,
        viewScale: 1,
        fieldOfView: 60,
      },
      xyzData: new Float32Array([40, 40, 40, 1]),
      rgbaData: new Float32Array([1, 1, 1, 1]),
      destSeed: new Float32Array(4 * 4 * 4),
    })
  )
  // Ortho view, 2D-system auto-detect (z near 0, x/y in [0,1]).
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 5,
      destHeight: 5,
      uniforms: { density: 100, viewMode: 1, rotateX: 0.3, rotateY: 0.2, rotateZ: 0.1, posX: 0, posY: 0, viewScale: 1 },
      xyzData: new Float32Array([0.5, 0.5, 0, 1]),
      rgbaData: new Float32Array([0.1, 0.2, 0.3, 0.4]),
      destSeed: new Float32Array(5 * 5 * 4),
    })
  )
  // Ortho view, 3D-system (not auto-detected as 2D).
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 5,
      destHeight: 5,
      uniforms: { density: 100, viewMode: 1, rotateX: 0.3, rotateY: 0.2, rotateZ: 0.1, posX: 0, posY: 0, viewScale: 1 },
      xyzData: new Float32Array([12, -8, 30, 1]),
      rgbaData: new Float32Array([0.1, 0.2, 0.3, 0.4]),
      destSeed: new Float32Array(5 * 5 * 4),
    })
  )
  // NaN uniform propagation (rotateX NaN).
  cases.push(buildCase(rng, { width: 3, height: 3, uniforms: buildUniforms(rng, { rotateX: Number.NaN, viewMode: 1 }) }))
  // Overlap stress.
  cases.push(buildCase(rng, { width: 6, height: 6, destWidth: 2, destHeight: 2 }))
  // fieldOfView omitted explicitly (viewMode 2, so it's read -> defaults to 0 -> tan(0)=0 -> focalLength=Infinity path).
  cases.push(
    buildCase(rng, {
      width: 2,
      height: 2,
      uniforms: { density: 100, viewMode: 2, rotateX: 0, rotateY: 0, rotateZ: 0, posX: 0, posY: 0, viewScale: 1 },
    })
  )

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
    for (let i = 0; i < 4; i += 1) {
      cases.push(buildCase(rng, { width: w, height: h, destWidth: w, destHeight: h }))
    }
  }
  for (let i = 0; i < 80; i += 1) cases.push(buildCase(rng))

  const jsonCases = cases.map((c, index) => ({
    index,
    width: c.width,
    height: c.height,
    destWidth: c.destWidth,
    destHeight: c.destHeight,
    uniforms: c.uniforms,
    xyzDataHex: toHex(c.xyzData),
    rgbaDataHex: toHex(c.rgbaData),
    destSeedHex: toHex(c.destSeed),
    expectedPixels: c.pixels,
    expectedOutputHex: toHex(c.outputData),
    expectedOutputSha256: sha256(Buffer.from(c.outputData.buffer, c.outputData.byteOffset, c.outputData.byteLength)),
  }))
  fs.writeFileSync(jsonPath, JSON.stringify({ adapter: 'render/pointsRender:deposit', cases: jsonCases }, null, 2))
  fs.writeFileSync(
    reportPath,
    [
      '# render/pointsRender:deposit oracle',
      '',
      `Cases: ${cases.length} (curated, see points_render-oracles.json).`,
      `Fuzz sweep: ${FUZZ_COUNT} cases in points_render-fuzz.bin.`,
      '',
    ].join('\n')
  )

  const writer = new CaseWriter(fuzzPath)
  const fuzzRng = mulberry32(0x90111af2)
  for (let i = 0; i < FUZZ_COUNT; i += 1) {
    const width = randomInt(fuzzRng, 1, 6)
    const height = randomInt(fuzzRng, 1, 6)
    const destWidth = randomInt(fuzzRng, 1, 6)
    const destHeight = randomInt(fuzzRng, 1, 6)
    const uniforms = buildUniforms(fuzzRng)
    const xyzData = makeSurfaceData(fuzzRng, width, height)
    const rgbaData = makeSurfaceData(fuzzRng, width, height)
    const destSeed = makeSurfaceData(fuzzRng, destWidth, destHeight)
    const { pixels, outputData } = runCase({ width, height, uniforms, destWidth, destHeight, xyzData, rgbaData, destSeed })
    const uniformEntries = { ...uniforms }
    writer.writeCase({
      textures: [
        { name: 'xyzTex', surface: { width, height, data: xyzData }, filterLinear: false },
        { name: 'rgbaTex', surface: { width, height, data: rgbaData }, filterLinear: false },
      ],
      uniforms: uniformEntries,
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
