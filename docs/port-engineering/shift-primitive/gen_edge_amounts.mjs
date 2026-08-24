// gen_edge_amounts.mjs
//
// Targeted follow-up to the main sweep: confirms glsl::shift_right_arithmetic's
// `amount & 31U` masking convention holds not just for the canonical 0..31
// range (main sweep) but for out-of-range shift-count VALUES that are
// still representable as std::uint32_t (the primitive's actual parameter
// type) -- 32, 33, 63, 64, 1000000, and UINT32_MAX (4294967295, JS's `-1
// >>> 0` style all-ones pattern, which as a shift count is ToUint32(-1)).
//
// Uses the full curated adversarial value set (the first 206 lines of
// values.txt) x these 6 edge amounts = 1236 rows.

'use strict';
import { readFileSync, writeFileSync } from 'node:fs';

function toHex8(u32) { return (u32 >>> 0).toString(16).padStart(8, '0'); }

const allValues = readFileSync('values.txt', 'utf8').trim().split('\n').map(Number);
const curated = allValues.slice(0, 206); // matches gen_values.mjs curated-set size

const edgeAmounts = [32, 33, 63, 64, 1000000, 4294967295];

const lines = [];
for (const v of curated) {
  for (const s of edgeAmounts) {
    const arith = v >> s;      // JS applies ToUint32(s) & 0x1F internally
    lines.push(`${v},${s >>> 0},${toHex8(arith)}`);
  }
}
writeFileSync('edge_amounts_oracle.csv', lines.join('\n') + '\n');
console.log(`wrote ${lines.length} rows to edge_amounts_oracle.csv`);
