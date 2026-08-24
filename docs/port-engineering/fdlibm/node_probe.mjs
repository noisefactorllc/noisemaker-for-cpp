// Reads inputs.hex (one 16-hex-digit IEEE-754 double bit pattern per line,
// written by gen_inputs.mjs) and evaluates V8's own Math.* on each input,
// emitting one line per input of 9 space-separated 16-hex-digit result bit
// patterns: tanh exp expm1 sin cos log atan sqrt pow
//
// This Node process IS V8 — Math.tanh here is exactly the same
// src/base/ieee754.cc code path noisemaker-for-cpu's JS renderer calls, so
// this is a direct oracle, not an approximation of one.
//
// Usage: node node_probe.mjs < inputs.hex > node_out.txt

import { createInterface } from 'node:readline';

const buf = new ArrayBuffer(8);
const f64 = new Float64Array(buf);
const u64 = new BigUint64Array(buf);

function fromHex(h) {
  u64[0] = BigInt('0x' + h);
  return f64[0];
}
function toHex(x) {
  f64[0] = x;
  return u64[0].toString(16).padStart(16, '0');
}

const POW_EXPS = [0.5, 2.0, 3.0, 1.0 / 3.0, -1.5, 10.0];

const rl = createInterface({ input: process.stdin, terminal: false });
let i = 0;
const out = [];
rl.on('line', (line) => {
  const h = line.trim();
  if (h.length === 0) return;
  const x = fromHex(h);
  const ax = Math.abs(x);
  const tanh = Math.tanh(x);
  const exp = Math.exp(x);
  const expm1 = Math.expm1(x);
  const sin = Math.sin(x);
  const cos = Math.cos(x);
  const log = Math.log(ax);
  const atan = Math.atan(x);
  const sqrt = Math.sqrt(ax);
  const pow = Math.pow(ax, POW_EXPS[i % POW_EXPS.length]);
  out.push(
    [tanh, exp, expm1, sin, cos, log, atan, sqrt, pow].map(toHex).join(' ')
  );
  i++;
});
rl.on('close', () => {
  process.stdout.write(out.join('\n') + '\n');
});
