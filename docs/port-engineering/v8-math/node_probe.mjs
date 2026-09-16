// node_probe.mjs -- evaluates Math.<function> (this IS V8, not an
// approximation of it) over a binary input file produced by gen_inputs.mjs,
// writing results as raw IEEE-754 double bit patterns (little-endian
// uint64). Also prints process.versions.v8 and process.arch so every run
// is self-documenting about which V8/architecture produced the numbers.
//
// Usage: node node_probe.mjs <function> <infile> <outfile>

import { readFileSync, writeFileSync } from 'node:fs'

const FUNCS = {
  sin: (x) => Math.sin(x),
  cos: (x) => Math.cos(x),
  tan: (x) => Math.tan(x),
  asin: (x) => Math.asin(x),
  acos: (x) => Math.acos(x),
  atan: (x) => Math.atan(x),
  exp: (x) => Math.exp(x),
  expm1: (x) => Math.expm1(x),
  log: (x) => Math.log(x),
  log2: (x) => Math.log2(x),
  tanh: (x) => Math.tanh(x),
  pow: (x, y) => Math.pow(x, y),
  atan2: (y, x) => Math.atan2(y, x),
  hypot2: (x, y) => Math.hypot(x, y),
  hypot3: (x, y, z) => Math.hypot(x, y, z),
}

const ARITY = { pow: 2, atan2: 2, hypot2: 2, hypot3: 3 }

function main() {
  const [fn, infile, outfile] = process.argv.slice(2)
  const impl = FUNCS[fn]
  if (!impl || !infile || !outfile) {
    console.error('usage: node node_probe.mjs <function> <infile> <outfile>')
    process.exit(1)
  }
  const arity = ARITY[fn] ?? 1
  const stride = arity * 8
  const input = readFileSync(infile)
  const count = input.length / stride
  if (!Number.isInteger(count)) throw new Error('input file size is not a multiple of the expected stride')

  const inView = new DataView(input.buffer, input.byteOffset, input.byteLength)
  const out = Buffer.alloc(count * 8)
  const outView = new DataView(out.buffer)

  const argBuf = new ArrayBuffer(8)
  const argF64 = new Float64Array(argBuf)
  const argU64 = new BigUint64Array(argBuf)

  for (let i = 0; i < count; i++) {
    const base = i * stride
    let result
    if (arity === 1) {
      argU64[0] = inView.getBigUint64(base, true)
      result = impl(argF64[0])
    } else if (arity === 2) {
      argU64[0] = inView.getBigUint64(base, true)
      const a = argF64[0]
      argU64[0] = inView.getBigUint64(base + 8, true)
      const b = argF64[0]
      result = impl(a, b)
    } else {
      argU64[0] = inView.getBigUint64(base, true)
      const a = argF64[0]
      argU64[0] = inView.getBigUint64(base + 8, true)
      const b = argF64[0]
      argU64[0] = inView.getBigUint64(base + 16, true)
      const c = argF64[0]
      result = impl(a, b, c)
    }
    outView.setFloat64(i * 8, result, true)
  }

  writeFileSync(outfile, out)
  console.error(
    `${fn}: v8=${process.versions.v8} arch=${process.arch} platform=${process.platform} ` +
      `n=${count} -> ${outfile}`,
  )
}

main()
