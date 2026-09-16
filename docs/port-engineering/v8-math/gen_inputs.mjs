// gen_inputs.mjs -- deterministic adversarial input generator for the
// v8-math differential harness. Writes raw IEEE-754 double bit patterns
// (little-endian uint64, 8 bytes each; 2-arg functions get interleaved
// pairs, 16 bytes each) to a binary file, read verbatim by both the Node
// probe and the C++ probe -- no formula is ever evaluated independently in
// both languages (a documented prior-session trap: `-4.0 + i*0.02`
// differing under FMA contraction between two "equivalent" re-derivations).
//
// Usage: node gen_inputs.mjs <function> <count> <outfile>
//   function: one of sin cos tan asin acos atan exp expm1 log log2 tanh
//             pow atan2 hypot2 hypot3
//   count:    approximate number of test vectors (arity-1 functions get
//             close to exactly `count`; the 2-arg functions get a grid of
//             roughly sqrt(count) x sqrt(count) plus random pairs, also
//             close to `count`)
//
// Deterministic: a fixed xorshift128+ PRNG seeded from a constant, so the
// same invocation always produces byte-identical output.

import { writeFileSync } from 'node:fs'

function makeRng(seedHi, seedLo) {
  let s0 = BigInt.asUintN(64, BigInt(seedHi))
  let s1 = BigInt.asUintN(64, BigInt(seedLo))
  if (s0 === 0n && s1 === 0n) s1 = 1n
  const MASK = (1n << 64n) - 1n
  return function next() {
    let x = s0
    const y = s1
    s0 = y
    x ^= (x << 23n) & MASK
    x ^= x >> 17n
    x ^= y ^ (y >> 26n)
    s1 = x & MASK
    return (s0 + s1) & MASK
  }
}

function bitsToDouble(bits) {
  const buf = new ArrayBuffer(8)
  new DataView(buf).setBigUint64(0, bits, true)
  return new DataView(buf).getFloat64(0, true)
}
function doubleToBits(value) {
  const buf = new ArrayBuffer(8)
  new DataView(buf).setFloat64(0, value, true)
  return new DataView(buf).getBigUint64(0, true)
}

const SPECIAL_VALUES = [
  0.0, -0.0, 1.0, -1.0, 2.0, -2.0, 0.5, -0.5,
  Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY, Number.NaN,
  Number.MIN_VALUE, -Number.MIN_VALUE, Number.MAX_VALUE, -Number.MAX_VALUE,
  Number.EPSILON, -Number.EPSILON,
  1e-320, -1e-320, 1e300, -1e300, 1e-300, -1e-300,
  Math.PI, -Math.PI, Math.PI / 2, -Math.PI / 2, Math.PI / 4, -Math.PI / 4,
  2 * Math.PI, -2 * Math.PI, Math.LN2, Math.LN10, Math.SQRT2, Math.SQRT1_2,
]

// A handful of alternative NaN payloads (signaling-shaped bit patterns);
// JS canonicalizes any NaN it boxes, so these exercise the C++ side's
// classification paths (isnan) without expecting a specific payload back.
const NAN_PAYLOADS = [
  0x7ff8000000000000n, 0x7ff0000000000001n, 0xfff8000000000000n,
  0x7ff4000000000000n, 0xfff0000000000001n,
]

function denseLinspace(lo, hi, n) {
  const out = []
  for (let i = 0; i < n; i++) out.push(lo + (hi - lo) * (i / (n - 1)))
  return out
}

// ULP-stepped cluster of `radius` steps on each side of `center`.
function ulpCluster(center, radius) {
  const out = [center]
  let up = center
  let down = center
  for (let i = 0; i < radius; i++) {
    up = Math.fround === undefined ? up : up // no-op, keep double precision
    up = nextAfter(up, Number.POSITIVE_INFINITY)
    down = nextAfter(down, Number.NEGATIVE_INFINITY)
    out.push(up, down)
  }
  return out
}

function nextAfter(x, direction) {
  if (Number.isNaN(x) || Number.isNaN(direction) || x === direction) return x
  if (x === 0) {
    const tiny = 5e-324
    return direction > 0 ? tiny : -tiny
  }
  let bits = doubleToBits(x)
  const up = (x > 0) === (direction > x)
  if (up) bits += 1n
  else bits -= 1n
  return bitsToDouble(BigInt.asUintN(64, bits))
}

// Branch thresholds pulled directly from fdlibm.cpp's hex constants (the
// exact high-word cutoffs the argument reduction switches on), reconstructed
// as doubles via insert-high-word-with-zero-low-word, matching how the
// algorithm itself would see a value exactly AT the boundary.
function fromHighWord(hi) {
  return bitsToDouble((BigInt.asUintN(32, BigInt(hi)) << 32n) & 0xffffffff00000000n)
}

const THRESHOLDS_HI = [
  0x3e300000, 0x3fd62e42, 0x3ff0a2b2, 0x40862e42, 0x4043687a,
  0x3fe921fb, 0x400921fb, 0x4002d97c, 0x413921fb, 0x40360000,
  0x3fdc0000, 0x3ff30000, 0x40038000, 0x44100000, 0x3fe00000,
  0x3ff00000, 0x3fef3333, 0x3fe59428, 0x00100000, 0x7ff00000,
  0x3c600000, 0x3e400000,
]

function specialAndThresholdSeeds() {
  const seeds = new Set()
  for (const v of SPECIAL_VALUES) seeds.add(doubleToBits(v))
  for (const hi of THRESHOLDS_HI) {
    for (const v of ulpCluster(fromHighWord(hi), 24)) seeds.add(doubleToBits(v))
    for (const v of ulpCluster(-fromHighWord(hi), 24)) seeds.add(doubleToBits(v))
  }
  // Multiples of pi/2 (sin/cos/tan argument-reduction stress) plus a dense
  // neighborhood around each.
  for (let k = -400; k <= 400; k++) {
    const center = k * (Math.PI / 2)
    for (const v of ulpCluster(center, 6)) seeds.add(doubleToBits(v))
  }
  return seeds
}

function buildUnaryInputs(fn, count) {
  const seeds = specialAndThresholdSeeds()
  for (const nan of NAN_PAYLOADS) seeds.add(nan)

  const domainDense = () => {
    switch (fn) {
      case 'asin':
      case 'acos':
        return denseLinspace(-1, 1, 20000)
      case 'log':
      case 'log2':
        return denseLinspace(1e-300, 1e300, 20000).concat(denseLinspace(0, 10, 20000))
      default:
        return denseLinspace(-1000, 1000, 20000).concat(denseLinspace(-1e6, 1e6, 20000))
    }
  }
  for (const v of domainDense()) seeds.add(doubleToBits(v))

  const values = [...seeds]
  const rng = makeRng(0x9e3779b97f4a7c15n, 0xbf58476d1ce4e5b9n)
  while (values.length < count) {
    // Mix of raw random bit patterns (hits subnormals/huge exponents) and
    // value-uniform-in-range draws (denser near "typical" magnitudes).
    if ((rng() & 1n) === 0n) {
      values.push(rng() & 0xffffffffffffffffn)
    } else {
      const exponent = Number(rng() % 1200n) - 600
      const mantissa = Number(rng() % 1000000n) / 1000000
      const sign = (rng() & 1n) === 0n ? 1 : -1
      let v
      switch (fn) {
        case 'asin':
        case 'acos':
          v = sign * mantissa
          break
        case 'log':
        case 'log2':
          v = Math.pow(2, exponent) * (1 + mantissa)
          break
        default:
          v = sign * Math.pow(2, exponent / 20) * (1 + mantissa)
      }
      values.push(doubleToBits(v))
    }
  }
  return values.slice(0, count).map((v) => (typeof v === 'bigint' ? v : doubleToBits(v)))
}

function buildBinaryInputs(fn, count) {
  const seeds = []
  const specials = SPECIAL_VALUES.concat(NAN_PAYLOADS.map(bitsToDouble))
  for (const a of specials) for (const b of specials) seeds.push([a, b])

  const rng = makeRng(0x243f6a8885a308d3n, 0x13198a2e03707344n)
  const pairs = [...seeds]
  while (pairs.length < count) {
    const draw = () => {
      const kind = rng() % 4n
      if (kind === 0n) return bitsToDouble(rng() & 0xffffffffffffffffn)
      const exponent = Number(rng() % 1200n) - 600
      const mantissa = Number(rng() % 1000000n) / 1000000
      const sign = (rng() & 1n) === 0n ? 1 : -1
      return sign * Math.pow(2, exponent / 20) * (1 + mantissa)
    }
    pairs.push([draw(), draw()])
  }
  return pairs.slice(0, count)
}

function main() {
  const [fn, countArg, outfile] = process.argv.slice(2)
  const count = Number(countArg)
  if (!fn || !count || !outfile) {
    console.error('usage: node gen_inputs.mjs <function> <count> <outfile>')
    process.exit(1)
  }

  const BINARY = new Set(['pow', 'atan2', 'hypot2'])
  const TERNARY = new Set(['hypot3'])

  if (BINARY.has(fn)) {
    const pairs = buildBinaryInputs(fn, count)
    const buf = Buffer.alloc(pairs.length * 16)
    for (let i = 0; i < pairs.length; i++) {
      buf.writeBigUInt64LE(doubleToBits(pairs[i][0]), i * 16)
      buf.writeBigUInt64LE(doubleToBits(pairs[i][1]), i * 16 + 8)
    }
    writeFileSync(outfile, buf)
    console.log(`${fn}: wrote ${pairs.length} pairs (${buf.length} bytes) to ${outfile}`)
    return
  }
  if (TERNARY.has(fn)) {
    const rng = makeRng(0x2545f4914f6cdd1dn, 0x8b6a2c2a5f7e1c3dn)
    const specials = SPECIAL_VALUES.concat(NAN_PAYLOADS.map(bitsToDouble))
    const triples = []
    for (const a of specials) triples.push([a, a * 0.5, a * 0.25])
    while (triples.length < count) {
      const draw = () => {
        const exponent = Number(rng() % 1200n) - 600
        const mantissa = Number(rng() % 1000000n) / 1000000
        const sign = (rng() & 1n) === 0n ? 1 : -1
        return sign * Math.pow(2, exponent / 20) * (1 + mantissa)
      }
      triples.push([draw(), draw(), draw()])
    }
    const trimmed = triples.slice(0, count)
    const buf = Buffer.alloc(trimmed.length * 24)
    for (let i = 0; i < trimmed.length; i++) {
      buf.writeBigUInt64LE(doubleToBits(trimmed[i][0]), i * 24)
      buf.writeBigUInt64LE(doubleToBits(trimmed[i][1]), i * 24 + 8)
      buf.writeBigUInt64LE(doubleToBits(trimmed[i][2]), i * 24 + 16)
    }
    writeFileSync(outfile, buf)
    console.log(`${fn}: wrote ${trimmed.length} triples (${buf.length} bytes) to ${outfile}`)
    return
  }

  const bits = buildUnaryInputs(fn, count)
  const buf = Buffer.alloc(bits.length * 8)
  for (let i = 0; i < bits.length; i++) buf.writeBigUInt64LE(BigInt.asUintN(64, bits[i]), i * 8)
  writeFileSync(outfile, buf)
  console.log(`${fn}: wrote ${bits.length} inputs (${buf.length} bytes) to ${outfile}`)
}

main()
