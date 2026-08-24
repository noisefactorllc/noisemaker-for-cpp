// gen_oracle.mjs
//
// Reads values.txt (the shared operand list) and computes JS's actual
// results for v >> s (arithmetic/signed), v >>> s (logical/unsigned), and
// v << s (left shift), for every value and all 32 canonical shift amounts
// (0..31 -- amounts outside this range were already proven, in
// probe_semantics.mjs Section D, to reduce to this range via `amount mod
// 32` with zero exceptions found across -70..130 on five representative
// values, so testing the canonical 0..31 range for the full value
// population is the non-redundant part of the sweep).
//
// Output: sweep_oracle.csv, one row per (value, shift) pair:
//   value,shift,arith_hex,logical_hex,left_hex
// where the three hex fields are the 8-hex-digit uint32 bit pattern of the
// JS result (so -1 and 4294967295 both print as ffffffff, letting the C++
// side compare bit patterns directly regardless of which C++ type it
// chooses to store the result in).

'use strict';
import { readFileSync, writeFileSync, createWriteStream } from 'node:fs';

function toHex8(u32) {
  return (u32 >>> 0).toString(16).padStart(8, '0');
}

const values = readFileSync('values.txt', 'utf8').trim().split('\n').map(Number);

const out = createWriteStream('sweep_oracle.csv');
let rows = 0;
for (const v of values) {
  for (let s = 0; s <= 31; s++) {
    const arith = v >> s;
    const logical = v >>> s;
    const left = v << s;
    out.write(`${v},${s},${toHex8(arith)},${toHex8(logical)},${toHex8(left)}\n`);
    rows++;
  }
}
out.end(() => {
  console.log(`wrote ${rows} rows (${values.length} values x 32 shift amounts) to sweep_oracle.csv`);
});
