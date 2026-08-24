// f32-level comparison: reads 8-hex-digit (32-bit) result columns from
// node_out_f32.txt and a candidate probe's output, reports N compared / N
// exact / N divergent / max ULP-at-f32 per function, and lists EVERY
// divergent input (not just the worst) with both f32 results and their
// exact f32 ULP gap, since the coordinator asked for the full list, not a
// sample.
//
// Usage: node compare_f32.mjs <inputs.hex> <node_out_f32.txt> <candidate_out_f32.txt> <label>
import { readFileSync } from 'node:fs';

const [inputsPath, nodePath, candPath, label] = process.argv.slice(2);

const COLUMNS = ['tanh', 'exp', 'expm1', 'sin', 'cos'];

const inputs = readFileSync(inputsPath, 'utf8').trim().split('\n');
const nodeLines = readFileSync(nodePath, 'utf8').trim().split('\n');
const candLines = readFileSync(candPath, 'utf8').trim().split('\n');

if (inputs.length !== nodeLines.length || nodeLines.length !== candLines.length) {
  console.error(`LENGTH MISMATCH: inputs=${inputs.length} node=${nodeLines.length} cand=${candLines.length}`);
  process.exit(1);
}

const buf64 = new ArrayBuffer(8);
const f64 = new Float64Array(buf64);
const u64 = new BigUint64Array(buf64);
function bitsToDouble(hex) {
  u64[0] = BigInt('0x' + hex);
  return f64[0];
}

// ULP distance at f32 via ordered-bit-pattern trick, same idea as compare.mjs
// but on 32-bit patterns.
function toOrdered32(hex) {
  let b = parseInt(hex, 16) >>> 0;
  if (b & 0x80000000) {
    return (~b) >>> 0;
  } else {
    return (b | 0x80000000) >>> 0;
  }
}
function ulpDistance32(aHex, bHex) {
  const oa = toOrdered32(aHex);
  const ob = toOrdered32(bHex);
  return oa > ob ? oa - ob : ob - oa;
}

const stats = {};
const divergentDetails = {};
for (const c of COLUMNS) {
  stats[c] = { n: 0, exact: 0, divergent: 0, maxUlp: 0 };
  divergentDetails[c] = [];
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
      const dist = ulpDistance32(nv, cv);
      if (dist > stats[name].maxUlp) stats[name].maxUlp = dist;
      const x = bitsToDouble(inputs[i]);
      divergentDetails[name].push({ input: inputs[i], x, node: nv, cand: cv, ulp: dist });
    }
  }
}

console.log(`=== ${label || 'f32 comparison'} ===`);
console.log(`N = ${inputs.length}`);
console.log('');
for (const c of COLUMNS) {
  const s = stats[c];
  const pct = ((s.divergent / s.n) * 100).toFixed(6);
  console.log(`${c.padEnd(6)} compared=${s.n}  exact=${s.exact}  divergent=${s.divergent}  (${pct}%)  maxULP@f32=${s.maxUlp}`);
}
console.log('');
console.log('=== full divergent-case listing (all, not just worst) ===');
for (const c of COLUMNS) {
  const list = divergentDetails[c];
  if (list.length === 0) {
    console.log(`${c}: none`);
    continue;
  }
  console.log(`${c}: ${list.length} divergent case(s)`);
  for (const d of list) {
    console.log(`  x=${d.x} (bits ${d.input})  V8_f32=${d.node}  cand_f32=${d.cand}  ulp@f32=${d.ulp}`);
  }
}
