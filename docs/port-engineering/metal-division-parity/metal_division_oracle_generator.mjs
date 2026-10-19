#!/usr/bin/env node
// Exact oracle for the authority's Metal division and GPU nearest-texel rules.
//
// The CPU authority evaluates a GLSL float division with a run-time divisor as
// `metalDivide(a, b)` (src/csl/metal-division.js): the float32 dividend times
// the measured Apple M4 reciprocal of the float32 divisor, left unrounded.
// Its transpiled kernels sample a nearest texture with
// `sampleNearestTexelBottomLeft` (src/runtime/sampler.js). This generator runs
// those unmodified authority functions and records their exact outputs:
//
// - every M4-measured operand pair of test/fixtures/authority/
//   metal-division-m4.json, with the GPU's float32 result and the authority's
//   unrounded double result;
// - deterministic pseudo-random operand pairs, including double dividends that
//   are not float32 values and subnormal operands;
// - metalReciprocal of selected values;
// - every M4-measured coordinate of test/fixtures/authority/nearest-texel-m4.json,
//   with the texel the authority selects.
//
// Usage:
//   node metal_division_oracle_generator.mjs --cpu-root <immutable authority> --write
//   node metal_division_oracle_generator.mjs --cpu-root <immutable authority> --check
import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const outputPath = path.join(here, 'metal-division-oracles.json')
const SCHEMA = 'noisemaker-for-cpp.metal-division.v1'
const SOURCES = [
  'src/csl/metal-division.js',
  'src/csl/metal-reciprocal-data.js',
  'src/csl/metal-reciprocal-grid.js',
  'src/runtime/sampler.js',
  'test/fixtures/authority/metal-division-m4.json',
  'test/fixtures/authority/nearest-texel-m4.json',
]
// The authority files this oracle was derived from. A different authority
// must be pinned here deliberately before it can produce a new oracle.
const EXPECTED_SOURCE_SHA256 = {
  'src/csl/metal-division.js': '104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8',
  'src/csl/metal-reciprocal-data.js': '08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87',
  'src/csl/metal-reciprocal-grid.js': 'bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39',
  'src/runtime/sampler.js': '5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5',
  'test/fixtures/authority/metal-division-m4.json': 'dabb115f748af29027e6722e7a536cefb2220dc202caa2124a0f95d44aa7c68a',
  'test/fixtures/authority/nearest-texel-m4.json': '993e75db2b9a9896a4181d05720b5f28b4e820410554788b0fc849c67504a014',
}

const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex')
const argv = process.argv.slice(2)
const modes = argv.filter((value) => value === '--write' || value === '--check')
if (modes.length !== 1) throw new Error('choose exactly one of --write or --check')
const rootIndex = argv.indexOf('--cpu-root')
if (rootIndex < 0 || rootIndex + 1 >= argv.length) throw new Error('--cpu-root <immutable authority> is required')
const requested = path.resolve(argv[rootIndex + 1])
const stat = fs.lstatSync(requested)
if (stat.isSymbolicLink() || !stat.isDirectory()) throw new Error('--cpu-root must be a non-symlink directory')
const cpuRoot = fs.realpathSync(requested)

const sources = SOURCES.map((relative) => {
  const bytes = fs.readFileSync(path.join(cpuRoot, relative))
  const digest = sha256(bytes.toString('utf8').replace(/\r\n/g, '\n'))
  const expected = EXPECTED_SOURCE_SHA256[relative]
  if (digest !== expected) throw new Error(`${relative} sha256 ${digest} is not the pinned ${expected}`)
  return { relativePath: relative, sha256: digest }
})

const load = (relative) => import(pathToFileURL(path.join(cpuRoot, relative)).href)
const { metalDivide, metalReciprocal } = await load('src/csl/metal-division.js')
const { sampleNearestTexelBottomLeft } = await load('src/runtime/sampler.js')
const fixture = (name) => JSON.parse(fs.readFileSync(path.join(cpuRoot, 'test/fixtures/authority', name), 'utf8'))

const f32 = new Float32Array(1)
const u32 = new Uint32Array(f32.buffer)
const f64 = new Float64Array(1)
const u64 = new Uint32Array(f64.buffer)
const fromBits = (bits) => { u32[0] = bits >>> 0; return f32[0] }
const toBits = (value) => { f32[0] = value; return u32[0] }
// A double as 16 hex digits, or "nan" for any NaN (payloads are not part of this contract).
function doubleWord(value) {
  if (Number.isNaN(value)) return 'nan'
  f64[0] = value
  return u64[1].toString(16).padStart(8, '0') + u64[0].toString(16).padStart(8, '0')
}
function fromDoubleWord(word) {
  u64[1] = parseInt(word.slice(0, 8), 16)
  u64[0] = parseInt(word.slice(8), 16)
  return f64[0]
}
const floatWord = (value) => (Number.isNaN(value) ? 'nan' : toBits(value).toString(16).padStart(8, '0'))

// Measured pairs: the authority's float32 result must equal the GPU's.
const { runtime, special } = fixture('metal-division-m4.json')
const measured = [...runtime, ...special].map(([a, b, gpu]) => {
  const result = metalDivide(fromBits(a), fromBits(b))
  const rounded = Math.fround(result)
  const expected = fromBits(gpu)
  if (!(Object.is(rounded, expected) || (Number.isNaN(rounded) && Number.isNaN(expected)))) {
    throw new Error(`authority disagrees with the M4 capture for ${a} / ${b}`)
  }
  return { a: a.toString(16).padStart(8, '0'), b: b.toString(16).padStart(8, '0'), gpu: floatWord(expected), result: doubleWord(result) }
})

// Deterministic pseudo-random operands (xorshift32), spread over every
// exponent, with double dividends that are not float32 values.
let state = 0x9e3779b9
const next = () => { state ^= state << 13; state >>>= 0; state ^= state >>> 17; state ^= state << 5; state >>>= 0; return state }
const randomFloat = () => {
  const word = next()
  const exponent = next() % 8 === 0 ? (next() % 256) : 100 + (next() % 56)
  return fromBits((word & 0x807fffff) | (exponent << 23))
}
const random = []
for (let index = 0; index < 4096; index += 1) {
  let a = randomFloat()
  const b = randomFloat()
  if (index % 3 === 1 && Number.isFinite(a)) a = a * (1 + (next() / 2 ** 32) * 2 ** -30)
  if (index % 7 === 3) a = a * 1e-38
  random.push({ a: doubleWord(a), b: doubleWord(b), result: doubleWord(metalDivide(a, b)) })
}
for (const row of random) {
  if (row.a === 'nan' || row.b === 'nan') continue
  if (doubleWord(metalDivide(fromDoubleWord(row.a), fromDoubleWord(row.b))) !== row.result) throw new Error('random pair is not reproducible')
}

const reciprocalInputs = [41, -41, 41 * 64, 23, 64, 1, -1, 3, 0.1, 1e-3, 1e30, -1e-30, 3.4028234663852886e38,
  1e39, -1e39, 1.1754943508222875e-38, 5e-39, -5e-39, 1e-45, 0, -0, Infinity, -Infinity, 0.5 + 2 ** -40, 41.000001]
const reciprocals = reciprocalInputs.map((value) => ({ value: doubleWord(value), result: doubleWord(metalReciprocal(value)) }))

// Nearest texel selection at every measured coordinate.
const { boundaries, special41x3 } = fixture('nearest-texel-m4.json')
const nearest = boundaries.map(([width, uBits, column]) => {
  const data = new Float32Array(width * 4)
  for (let x = 0; x < width; x += 1) data[x * 4] = x
  const out = sampleNearestTexelBottomLeft({ width, height: 1, data }, fromBits(uBits), 0.5, new Float32Array(4))
  if (out[0] !== column) throw new Error(`authority disagrees with the M4 capture at u=${uBits} width ${width}`)
  return { width, height: 1, u: uBits.toString(16).padStart(8, '0'), v: floatWord(0.5), column, row: 0 }
})
{
  const width = 41
  const height = 3
  const data = new Float32Array(width * height * 4)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = ((height - 1 - y) * width + x) * 4
      data[offset] = x
      data[offset + 1] = y
    }
  }
  for (const [uBits, vBits, column, row] of special41x3) {
    const out = sampleNearestTexelBottomLeft({ width, height, data }, fromBits(uBits), fromBits(vBits), new Float32Array(4))
    if (out[0] !== column || out[1] !== row) throw new Error(`authority disagrees with the M4 capture at ${uBits},${vBits}`)
    nearest.push({ width, height, u: uBits.toString(16).padStart(8, '0'), v: vBits.toString(16).padStart(8, '0'), column, row })
  }
}

const document = {
  schema: SCHEMA,
  sources,
  exact: true,
  toleranceNone: true,
  measured,
  random,
  reciprocals,
  nearest,
}
const payload = Buffer.from(`${JSON.stringify(document, null, 1)}\n`)
const sidecar = `${sha256(payload)}  ${path.basename(outputPath)}\n`
if (modes[0] === '--write') {
  fs.writeFileSync(outputPath, payload)
  fs.writeFileSync(`${outputPath}.sha256`, sidecar)
  console.log(`metal division oracle: wrote ${measured.length} measured, ${random.length} random, ${reciprocals.length} reciprocal, ${nearest.length} nearest cases`)
} else {
  if (!fs.readFileSync(outputPath).equals(payload)) throw new Error('metal-division-oracles.json differs from the authority')
  if (fs.readFileSync(`${outputPath}.sha256`, 'utf8') !== sidecar) throw new Error('metal-division-oracles.json sidecar drift')
  console.log('metal division oracle: ok')
}
