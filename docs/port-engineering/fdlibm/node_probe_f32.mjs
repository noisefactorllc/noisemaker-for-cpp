// Same as node_probe.mjs, but narrows every result to float32 via
// Math.fround() (IEEE-754 correctly-rounded double->float32, same guarantee
// as noisemaker::f32 = static_cast<float>(double)) before emitting hex, and
// emits 8-hex-digit (32-bit) fields instead of 16-hex-digit (64-bit) ones.
// This mirrors what actually reaches a pixel: every runtime wrapper narrows
// its double result to f32 before returning.
//
// Usage: node node_probe_f32.mjs < inputs.hex > node_out_f32.txt
import { createInterface } from 'node:readline';

const buf64 = new ArrayBuffer(8);
const f64 = new Float64Array(buf64);
const u64 = new BigUint64Array(buf64);
function fromHex(h) {
  u64[0] = BigInt('0x' + h);
  return f64[0];
}

const buf32 = new ArrayBuffer(4);
const f32v = new Float32Array(buf32);
const u32v = new Uint32Array(buf32);
function toHex32(x) {
  f32v[0] = Math.fround(x);
  return u32v[0].toString(16).padStart(8, '0');
}

const rl = createInterface({ input: process.stdin, terminal: false });
const out = [];
rl.on('line', (line) => {
  const h = line.trim();
  if (h.length === 0) return;
  const x = fromHex(h);
  const tanh = Math.tanh(x);
  const exp = Math.exp(x);
  const expm1 = Math.expm1(x);
  const sin = Math.sin(x);
  const cos = Math.cos(x);
  out.push([tanh, exp, expm1, sin, cos].map(toHex32).join(' '));
});
rl.on('close', () => {
  process.stdout.write(out.join('\n') + '\n');
});
