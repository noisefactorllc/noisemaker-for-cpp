// `render/pointsBillboardRender:deposit` scatter-pass oracle. Imports the
// REAL, unmodified `pointsBillboardRenderDepositAdapter` (and, through it,
// the real `computeClipCenter`/`texelFetchAgent`/`scatterPointPixel`/
// `fract`/`GOLDEN_RATIO_CONJUGATE` from points-deposit.js) directly. See
// lenia_oracle_generator.mjs for the shared methodology notes.
//
// This is the widest-domain adapter of the six: covers every `shapeMode`
// (0 sprite-texture, 1-6 procedural SDFs, 7 + out-of-domain soft
// fallback), every `viewMode` (0 flat, 1 ortho, 2 perspective, plus an
// out-of-catalog value), `blendMode` 0/1, `blurLayer` 0/1/omitted, BOTH
// `pass.blend` shapes (`deposit`'s additive vs `deposit_alpha`'s
// premultiplied array, plus lowercase/garbage variants of the array
// strings), and `spriteTex.filter` both 'linear' and the nearest default.
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { pointsBillboardRenderDepositAdapter } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/effects/cpu/billboard-deposit.js'
import { Surface } from '/Users/alex/platform/.nm-cpp-work/authority/61aa869/src/runtime/surface.js'

import { CaseWriter, makeSurfaceData, mulberry32, randomInt, randomUniform } from './common.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const jsonPath = path.join(here, 'points_billboard_render-oracles.json')
const reportPath = path.join(here, 'points_billboard_render-oracle-report.md')
const fuzzPath = path.join(here, 'points_billboard_render-fuzz.bin')

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

const BLEND_CHOICES = [
  null, // absent -> additive
  ['ONE', 'ONE_MINUS_SRC_ALPHA'], // canonical premultiplied
  ['one', 'one_minus_src_alpha'], // lowercase -- isPremultipliedBlend upper-cases
  ['ONE', 'ONE'], // array, but not the premultiplied pair -> additive
  ['garbage', 'nonsense'], // array of unrelated strings -> additive
]

function buildUniforms(rng, overrides = {}) {
  const viewModeChoices = [0, 1, 2, 0, 1, 2, 5, -3]
  const shapeModeChoices = [0, 1, 2, 3, 4, 5, 6, 7, 0, 9, -1]
  const blendModeChoices = [0, 1, 0, 1, 3]
  const uniforms = {
    density: randomUniform(rng, { min: -20, max: 200 }),
    viewMode: viewModeChoices[randomInt(rng, 0, viewModeChoices.length - 1)],
    rotateX: randomUniform(rng, { min: -6, max: 6 }),
    rotateY: randomUniform(rng, { min: -6, max: 6 }),
    rotateZ: randomUniform(rng, { min: -6, max: 6 }),
    posX: randomUniform(rng, { min: -30, max: 30 }),
    posY: randomUniform(rng, { min: -30, max: 30 }),
    viewScale: randomUniform(rng, { min: -3, max: 3 }),
    shapeMode: shapeModeChoices[randomInt(rng, 0, shapeModeChoices.length - 1)],
    blendMode: blendModeChoices[randomInt(rng, 0, blendModeChoices.length - 1)],
    depositOpacity: randomUniform(rng, { min: -50, max: 200 }),
    seed: randomUniform(rng, { min: -1000, max: 1000 }),
    sizeVariation: randomUniform(rng, { min: -50, max: 200 }),
    rotationVar: randomUniform(rng, { min: -50, max: 200 }),
    pointSize: randomUniform(rng, { min: -5, max: 40 }),
    ...overrides,
  }
  const maybeOmit = (name, gen) => {
    if (rng() < 0.35) return
    uniforms[name] = gen()
  }
  if (!('posZ' in overrides)) maybeOmit('posZ', () => randomUniform(rng, { min: -30, max: 30 }))
  if (!('fieldOfView' in overrides)) maybeOmit('fieldOfView', () => randomUniform(rng, { min: -50, max: 250 }))
  if (!('blurLayer' in overrides)) maybeOmit('blurLayer', () => [0, 1, 2][randomInt(rng, 0, 2)])
  if (!('sizeDistance' in overrides)) maybeOmit('sizeDistance', () => randomUniform(rng, { min: -10, max: 40 }))
  if (!('brightnessDistance' in overrides)) maybeOmit('brightnessDistance', () => randomUniform(rng, { min: -10, max: 40 }))
  if (!('aperture' in overrides)) maybeOmit('aperture', () => randomUniform(rng, { min: -5, max: 20 }))
  if (!('focalDistance' in overrides)) maybeOmit('focalDistance', () => randomUniform(rng, { min: -10, max: 160 }))
  return uniforms
}

function runCase({ width, height, uniforms, blend, destWidth, destHeight, xyzData, rgbaData, orderData, spriteWidth, spriteHeight, spriteData, spriteFilterLinear, meanWidth, meanHeight, meanData, destSeed }) {
  const xyzTex = new Surface(width, height, xyzData.slice())
  const rgbaTex = new Surface(width, height, rgbaData.slice())
  const orderTex = new Surface(width, height, orderData.slice())
  const spriteTex = new Surface(spriteWidth, spriteHeight, spriteData.slice())
  if (spriteFilterLinear) spriteTex.filter = 'linear'
  const spriteMeanTex = new Surface(meanWidth, meanHeight, meanData.slice())
  const destination = new Surface(destWidth, destHeight, destSeed.slice())
  const pass = blend ? { blend } : {}
  const result = pointsBillboardRenderDepositAdapter({
    pass,
    uniforms,
    bindings: {},
    inputs: { xyzTex, rgbaTex, orderTex, spriteTex, spriteMeanTex },
    destination,
    params: {},
  })
  return { pixels: result.pixels, outputData: destination.data }
}

function buildCase(rng, opts = {}) {
  const width = opts.width ?? randomInt(rng, 1, 5)
  const height = opts.height ?? randomInt(rng, 1, 5)
  const destWidth = opts.destWidth ?? randomInt(rng, 1, 6)
  const destHeight = opts.destHeight ?? randomInt(rng, 1, 6)
  const uniforms = opts.uniforms ?? buildUniforms(rng)
  const blend = 'blend' in opts ? opts.blend : BLEND_CHOICES[randomInt(rng, 0, BLEND_CHOICES.length - 1)]
  const xyzData = opts.xyzData ?? makeSurfaceData(rng, width, height)
  const rgbaData = opts.rgbaData ?? makeSurfaceData(rng, width, height)
  const orderData = opts.orderData ?? makeSurfaceData(rng, width, height)
  const spriteWidth = opts.spriteWidth ?? randomInt(rng, 1, 4)
  const spriteHeight = opts.spriteHeight ?? randomInt(rng, 1, 4)
  const spriteData = opts.spriteData ?? makeSurfaceData(rng, spriteWidth, spriteHeight)
  const spriteFilterLinear = opts.spriteFilterLinear ?? rng() < 0.5
  // spriteMeanTex sometimes exactly 5x5 (the "real" contract), sometimes
  // smaller/larger to exercise texelFetchAgent's clamp.
  const meanIsFive = rng() < 0.6
  const meanWidth = opts.meanWidth ?? (meanIsFive ? 5 : randomInt(rng, 1, 6))
  const meanHeight = opts.meanHeight ?? (meanIsFive ? 5 : randomInt(rng, 1, 6))
  const meanData = opts.meanData ?? makeSurfaceData(rng, meanWidth, meanHeight)
  const destSeed = opts.destSeed ?? makeSurfaceData(rng, destWidth, destHeight)

  const args = { width, height, uniforms, blend, destWidth, destHeight, xyzData, rgbaData, orderData, spriteWidth, spriteHeight, spriteData, spriteFilterLinear, meanWidth, meanHeight, meanData, destSeed }
  const first = runCase(args)
  const again = runCase(args)
  if (!buffersIdentical(first.outputData, again.outputData) || first.pixels !== again.pixels) {
    throw new Error('points_billboard_render oracle case is non-deterministic')
  }
  return { ...args, ...first }
}

function main() {
  const rng = mulberry32(0xb111b0a)
  const cases = []

  // Flat view, shapeMode 0 (sprite), additive blend, alive agent centered.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 6,
      destHeight: 6,
      blend: null,
      uniforms: buildUniforms(rng, { viewMode: 0, shapeMode: 0, density: 100, blendMode: 0, pointSize: 4 }),
      xyzData: new Float32Array([0.5, 0.5, 0, 1]),
      rgbaData: new Float32Array([1, 0.5, 0.25, 1]),
    })
  )
  // Same, but premultiplied deposit_alpha blend.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 6,
      destHeight: 6,
      blend: ['ONE', 'ONE_MINUS_SRC_ALPHA'],
      uniforms: buildUniforms(rng, { viewMode: 0, shapeMode: 0, density: 100, blendMode: 0, pointSize: 4 }),
      xyzData: new Float32Array([0.5, 0.5, 0, 1]),
      rgbaData: new Float32Array([1, 0.5, 0.25, 0.6]),
    })
  )
  // Dead agent (pos.w<0.5) -- draws nothing.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 6,
      destHeight: 6,
      uniforms: buildUniforms(rng, { viewMode: 0, shapeMode: 0, density: 100 }),
      xyzData: new Float32Array([0.5, 0.5, 0, 0.1]),
    })
  )
  // Every procedural shapeMode 1..7 at flat view.
  for (let shapeMode = 1; shapeMode <= 7; shapeMode += 1) {
    cases.push(
      buildCase(rng, {
        width: 1,
        height: 1,
        destWidth: 8,
        destHeight: 8,
        uniforms: buildUniforms(rng, { viewMode: 0, shapeMode, density: 100, pointSize: 6 }),
        xyzData: new Float32Array([0.5, 0.5, 0, 1]),
      })
    )
  }
  // Perspective view with blur (aperture>0), shapeMode 0, requires the
  // shadeParticle blur path.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 10,
      destHeight: 10,
      uniforms: buildUniforms(rng, {
        viewMode: 2,
        shapeMode: 0,
        density: 100,
        blendMode: 0,
        pointSize: 4,
        aperture: 5,
        focalDistance: 20,
        posZ: 0,
        fieldOfView: 60,
      }),
      xyzData: new Float32Array([0, 0, 30, 1]),
      meanWidth: 5,
      meanHeight: 5,
    })
  )
  // blendMode 1 with a depth-sort orderTex re-indexing particleId.
  cases.push(
    buildCase(rng, {
      width: 2,
      height: 2,
      destWidth: 8,
      destHeight: 8,
      uniforms: buildUniforms(rng, { viewMode: 1, blendMode: 1, density: 100, shapeMode: 0 }),
      orderData: new Float32Array([0, 3, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]),
    })
  )
  // blurLayer === 1 whole-draw gate (viewMode 0 -> return { pixels: 0 } immediately).
  cases.push(
    buildCase(rng, {
      width: 2,
      height: 2,
      uniforms: buildUniforms(rng, { viewMode: 0, blurLayer: 1, aperture: 5, blendMode: 0 }),
    })
  )
  // NaN rotation propagation.
  cases.push(buildCase(rng, { width: 2, height: 2, uniforms: buildUniforms(rng, { rotationVar: Number.NaN }) }))
  // spriteTex filter linear, shapeMode 0.
  cases.push(
    buildCase(rng, {
      width: 1,
      height: 1,
      destWidth: 6,
      destHeight: 6,
      spriteFilterLinear: true,
      uniforms: buildUniforms(rng, { viewMode: 0, shapeMode: 0, density: 100, pointSize: 5 }),
      xyzData: new Float32Array([0.5, 0.5, 0, 1]),
    })
  )
  // Overlap stress: many agents into a tiny destination.
  cases.push(buildCase(rng, { width: 5, height: 5, destWidth: 2, destHeight: 2 }))
  // fieldOfView entirely omitted under viewMode 2 (NaN-through-Math.max path).
  cases.push(
    buildCase(rng, {
      width: 2,
      height: 2,
      uniforms: buildUniforms(rng, { viewMode: 2, fieldOfView: undefined }),
    })
  )

  const sizes = [
    [1, 1],
    [1, 5],
    [5, 1],
    [2, 2],
    [4, 4],
    [5, 3],
  ]
  for (const [w, h] of sizes) {
    for (let i = 0; i < 5; i += 1) cases.push(buildCase(rng, { width: w, height: h, destWidth: w + 2, destHeight: h + 2 }))
  }
  for (let i = 0; i < 120; i += 1) cases.push(buildCase(rng))

  const jsonCases = cases.map((c, index) => ({
    index,
    width: c.width,
    height: c.height,
    destWidth: c.destWidth,
    destHeight: c.destHeight,
    uniforms: c.uniforms,
    blend: c.blend,
    spriteWidth: c.spriteWidth,
    spriteHeight: c.spriteHeight,
    spriteFilterLinear: c.spriteFilterLinear,
    meanWidth: c.meanWidth,
    meanHeight: c.meanHeight,
    xyzDataHex: toHex(c.xyzData),
    rgbaDataHex: toHex(c.rgbaData),
    orderDataHex: toHex(c.orderData),
    spriteDataHex: toHex(c.spriteData),
    meanDataHex: toHex(c.meanData),
    destSeedHex: toHex(c.destSeed),
    expectedPixels: c.pixels,
    expectedOutputHex: toHex(c.outputData),
    expectedOutputSha256: sha256(Buffer.from(c.outputData.buffer, c.outputData.byteOffset, c.outputData.byteLength)),
  }))
  fs.writeFileSync(jsonPath, JSON.stringify({ adapter: 'render/pointsBillboardRender:deposit', cases: jsonCases }, null, 2))
  fs.writeFileSync(
    reportPath,
    [
      '# render/pointsBillboardRender:deposit oracle',
      '',
      `Cases: ${cases.length} (curated, see points_billboard_render-oracles.json).`,
      `Fuzz sweep: ${FUZZ_COUNT} cases in points_billboard_render-fuzz.bin.`,
      '',
    ].join('\n')
  )

  const writer = new CaseWriter(fuzzPath)
  const fuzzRng = mulberry32(0xb111b0a22)
  for (let i = 0; i < FUZZ_COUNT; i += 1) {
    const width = randomInt(fuzzRng, 1, 5)
    const height = randomInt(fuzzRng, 1, 5)
    const destWidth = randomInt(fuzzRng, 1, 6)
    const destHeight = randomInt(fuzzRng, 1, 6)
    const uniforms = buildUniforms(fuzzRng)
    const blend = BLEND_CHOICES[randomInt(fuzzRng, 0, BLEND_CHOICES.length - 1)]
    const xyzData = makeSurfaceData(fuzzRng, width, height)
    const rgbaData = makeSurfaceData(fuzzRng, width, height)
    const orderData = makeSurfaceData(fuzzRng, width, height)
    const spriteWidth = randomInt(fuzzRng, 1, 4)
    const spriteHeight = randomInt(fuzzRng, 1, 4)
    const spriteData = makeSurfaceData(fuzzRng, spriteWidth, spriteHeight)
    const spriteFilterLinear = fuzzRng() < 0.5
    const meanIsFive = fuzzRng() < 0.6
    const meanWidth = meanIsFive ? 5 : randomInt(fuzzRng, 1, 6)
    const meanHeight = meanIsFive ? 5 : randomInt(fuzzRng, 1, 6)
    const meanData = makeSurfaceData(fuzzRng, meanWidth, meanHeight)
    const destSeed = makeSurfaceData(fuzzRng, destWidth, destHeight)

    const args = { width, height, uniforms, blend, destWidth, destHeight, xyzData, rgbaData, orderData, spriteWidth, spriteHeight, spriteData, spriteFilterLinear, meanWidth, meanHeight, meanData, destSeed }
    const { pixels, outputData } = runCase(args)

    writer.writeCase({
      textures: [
        { name: 'xyzTex', surface: { width, height, data: xyzData }, filterLinear: false },
        { name: 'rgbaTex', surface: { width, height, data: rgbaData }, filterLinear: false },
        { name: 'orderTex', surface: { width, height, data: orderData }, filterLinear: false },
        { name: 'spriteTex', surface: { width: spriteWidth, height: spriteHeight, data: spriteData }, filterLinear: spriteFilterLinear },
        { name: 'spriteMeanTex', surface: { width: meanWidth, height: meanHeight, data: meanData }, filterLinear: false },
      ],
      uniforms,
      blend,
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
