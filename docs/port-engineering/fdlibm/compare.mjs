// Compares node_out.txt against either baseline_out.txt (std::* vs V8) or
// fdlibm_out.txt (fdlibm port vs V8), column by column, and reports exact
// counts: N compared, N exact, N divergent, plus max ULP and the worst
// offending inputs — per function.
//
// Usage: node compare.mjs <inputs.hex> <node_out.txt> <candidate_out.txt> <label>

import { readFileSync } from 'node:fs';

const [inputsPath, nodePath, candPath, label] = process.argv.slice(2);
if (!inputsPath || !nodePath || !candPath) {
  console.error('usage: node compare.mjs <inputs.hex> <node_out.txt> <candidate_out.txt> <label>');
  process.exit(1);
}

const COLUMNS = ['tanh', 'exp', 'expm1', 'sin', 'cos', 'log', 'atan', 'sqrt', 'pow'];

const inputs = readFileSync(inputsPath, 'utf8').trim().split('\n');
const nodeLines = readFileSync(nodePath, 'utf8').trim().split('\n');
const candLines = readFileSync(candPath, 'utf8').trim().split('\n');

if (inputs.length !== nodeLines.length || nodeLines.length !== candLines.length) {
  console.error(`LENGTH MISMATCH: inputs=${inputs.length} node=${nodeLines.length} cand=${candLines.length}`);
  process.exit(1);
}

const buf = new ArrayBuffer(8);
const f64 = new Float64Array(buf);
const u64 = new BigUint64Array(buf);
function bitsToDouble(hex) {
  u64[0] = BigInt('0x' + hex);
  return f64[0];
}

// ULP distance between two doubles, via their bit patterns, treating the
// bit pattern as a monotonic ordering (standard trick: map to a signed
// integer space where bit-pattern order == value order for all finite
// values including across the zero boundary).
function toOrdered(bitsHex) {
  let b = BigInt('0x' + bitsHex);
  if (b & 0x8000000000000000n) {
    return (~b) & 0xffffffffffffffffn; // negative: flip all bits
  } else {
    return b | 0x8000000000000000n; // positive: flip sign bit
  }
}
function ulpDistance(aHex, bHex) {
  const oa = toOrdered(aHex);
  const ob = toOrdered(bHex);
  const d = oa > ob ? oa - ob : ob - oa;
  return d;
}

const stats = {};
for (const c of COLUMNS) {
  stats[c] = { n: 0, exact: 0, divergent: 0, maxUlp: 0n, worst: null };
}

for (let i = 0; i < inputs.length; i++) {
  const nodeCols = nodeLines[i].split(' ');
  const candCols = candLines[i].split(' ');
  for (let c = 0; c < COLUMNS.length; c++) {
    const name = COLUMNS[c];
    const nv = nodeCols[c];
    const cv = candCols[c];
    stats[name].n++;
    if (nv === cv) {
      stats[name].exact++;
    } else {
      stats[name].divergent++;
      const dist = ulpDistance(nv, cv);
      if (dist > stats[name].maxUlp) {
        stats[name].maxUlp = dist;
        stats[name].worst = { input: inputs[i], node: nv, cand: cv, ulp: dist.toString() };
      }
    }
  }
}

console.log(`=== ${label || 'comparison'} ===`);
console.log(`N = ${inputs.length}`);
console.log('');
for (const c of COLUMNS) {
  const s = stats[c];
  const pct = ((s.divergent / s.n) * 100).toFixed(4);
  console.log(`${c.padEnd(6)} compared=${s.n}  exact=${s.exact}  divergent=${s.divergent}  (${pct}%)  maxULP=${s.maxUlp}`);
  if (s.worst) {
    const x = bitsToDouble(s.worst.input);
    console.log(`       worst: x=${x} (bits ${s.worst.input})  node=${s.worst.node}  cand=${s.worst.cand}  ulp=${s.worst.ulp}`);
  }
}
