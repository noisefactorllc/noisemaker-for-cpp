// compare.mjs -- diffs two raw-bit-pattern result files (one from
// node_probe.mjs, one from cpp_probe), ordinal-encoding each IEEE-754 bit
// pattern to compute exact ULP distance, and reports N compared / N exact /
// N divergent / max ULP / up to a handful of the worst divergent inputs
// (cross-referenced against the shared input file so the report is
// reproducible, not just a count).
//
// Usage: node compare.mjs <function> <inputs-file> <v8-result-file>
//                          <cpp-result-file> [n-args]

import { readFileSync } from 'node:fs'

function bitsAt(buf, offset) {
  return buf.readBigUInt64LE(offset)
}

// Maps an IEEE-754 double bit pattern to a monotonic ordinal so that ULP
// distance is just |ordinal(a) - ordinal(b)|, including across the
// positive/negative-zero boundary and the positive/negative-value
// boundary (the standard "totalOrder"-adjacent trick).
function ordinal(bits) {
  const SIGN = 0x8000000000000000n
  if ((bits & SIGN) === 0n) return bits | SIGN
  return SIGN - (bits & ~SIGN) - 1n
}

function ulpDistance(aBits, bBits) {
  const aNaN = isNaNBits(aBits)
  const bNaN = isNaNBits(bBits)
  // This harness compares NaN classification, not its payload or sign bits.
  if (aNaN && bNaN) return 0n
  if (aNaN !== bNaN) return -1n // sentinel: one NaN, one not -- always divergent
  const oa = ordinal(aBits)
  const ob = ordinal(bBits)
  return oa > ob ? oa - ob : ob - oa
}

function isNaNBits(bits) {
  const exponent = (bits >> 52n) & 0x7ffn
  const mantissa = bits & 0xfffffffffffffn
  return exponent === 0x7ffn && mantissa !== 0n
}

function hex(bits) {
  return '0x' + bits.toString(16).padStart(16, '0')
}

function main() {
  const [fn, inputsFile, v8File, cppFile, nArgsArg] = process.argv.slice(2)
  if (!fn || !inputsFile || !v8File || !cppFile) {
    console.error('usage: node compare.mjs <function> <inputs-file> <v8-result-file> <cpp-result-file> [n-args]')
    process.exit(1)
  }
  const nArgs = Number(nArgsArg ?? 1)
  const inputStride = nArgs * 8

  const inputs = readFileSync(inputsFile)
  const v8 = readFileSync(v8File)
  const cpp = readFileSync(cppFile)

  const count = v8.length / 8
  if (cpp.length / 8 !== count) throw new Error('result file lengths differ')
  if (inputs.length / inputStride !== count) throw new Error('input file does not match result count')

  let exact = 0
  let divergent = 0
  let maxUlp = 0n
  const worst = []

  for (let i = 0; i < count; i++) {
    const a = bitsAt(v8, i * 8)
    const b = bitsAt(cpp, i * 8)
    const dist = ulpDistance(a, b)
    if (dist === 0n) {
      exact++
      continue
    }
    divergent++
    const reportedDist = dist < 0n ? 0xffffffffn : dist
    if (reportedDist > maxUlp) maxUlp = reportedDist
    if (worst.length < 20) {
      const args = []
      for (let k = 0; k < nArgs; k++) args.push(hex(bitsAt(inputs, i * inputStride + k * 8)))
      worst.push({ index: i, args, v8: hex(a), cpp: hex(b), ulp: reportedDist.toString() })
    }
  }

  worst.sort((x, y) => Number(BigInt(y.ulp) - BigInt(x.ulp)))

  console.log(JSON.stringify({
    function: fn,
    n_args: nArgs,
    compared: count,
    exact,
    divergent,
    percent_divergent: count === 0 ? 0 : (100 * divergent) / count,
    max_ulp: maxUlp.toString(),
    worst_cases: worst.slice(0, 10),
  }, null, 2))
}

main()
