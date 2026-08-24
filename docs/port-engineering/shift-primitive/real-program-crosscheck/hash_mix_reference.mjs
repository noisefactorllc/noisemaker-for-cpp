// hash_mix_reference.mjs
//
// Step 5: real-program cross-check.
//
// This is a byte-for-byte copy of `hash_mix` and its `cpu_umul` dependency
// as they actually appear, TODAY, in shipped generated JS:
//   ../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js
//   lines 19970-19976 (hash_mix), inside canonicalFactory147
//   (filter/spookyTicker), lines 19948-20030+ snapshotted verbatim into
//   ./snapshot_canonicalFactory147.js.excerpt (sha256 sidecar alongside).
//   `cpu_umul` = $runtime.stdlib.umul = (left,right) => Math.imul(left,right) >>> 0
//   (noisemaker-for-cpu/src/csl/glsl-runtime.js:319).
//
// Both source files were only READ, never modified (per task constraints:
// noisemaker-for-cpu is read-only). Full source file sha256 recorded in
// shift-primitive-report.md and canonical_kernels_source.sha256 alongside
// this file, so this snapshot is independently checkable against the live
// tree even though "another agent is actively editing the generator
// Python" and the generated JS could change under us later.
//
// hash_mix's `v` argument is GLSL-`uint`-typed in the original GLSL
// (spookyTicker.glsl) but, per Hazard #1, is lowered through
// glsl-transpiler's GENERIC scalar fallback (not the pcg3d idiom), so its
// `>>` is JS's plain, sign-propagating right shift -- this is exactly the
// function bitops-precompute.md cites (§ Hazard #1, "canonical-
// kernels.js:19971-19975 (filter/spookyTicker, hash_mix ... all plain
// >>") as live evidence for why the arithmetic-shift primitive is needed.

'use strict';
import { readFileSync, writeFileSync } from 'node:fs';

function cpu_umul(left, right) {
  return Math.imul(left, right) >>> 0;
}

// Verbatim copy of canonical-kernels.js:19970-19976.
function hash_mix(v) {
  v = v ^ (v >> 16);
  v = cpu_umul(v, 2146121005);
  v = v ^ (v >> 15);
  v = cpu_umul(v, 2221713035);
  v = v ^ (v >> 16);
  return v;
}

function toHex8(u32) { return (u32 >>> 0).toString(16).padStart(8, '0'); }

// Reuse the SAME shared value population as the primitive sweep, so the
// real-program cross-check exercises the same full-int32-range,
// bit-31-set-heavy distribution, not a fresh/narrower sample.
const values = readFileSync('../values.txt', 'utf8').trim().split('\n').map(Number);

const lines = [];
for (const v of values) {
  const result = hash_mix(v | 0); // `|0` mirrors every real call site, which always
                                   // passes an already-ToInt32'd expression into hash_mix
                                   // (e.g. `(rowSeed|0) ^ 17`, `(seed|0) * 7919`).
  lines.push(`${v},${toHex8(result)}`);
}
writeFileSync('hash_mix_oracle.csv', lines.join('\n') + '\n');
console.log(`wrote ${lines.length} hash_mix(v) rows to hash_mix_oracle.csv`);

// Separately and narrowly: confirm Math.imul(a,b)>>>0 (cpu_umul) is bit-
// identical to plain uint32_t a*b wraparound multiplication, since the
// C++ port below needs that fact and it is NOT part of the shift
// primitive itself -- flagged and verified independently, not assumed.
const mulRows = [];
const mulSampleValues = values.slice(0, 5000); // a representative sub-sample; full N^2 is not needed,
                                                 // this is a corroborating spot-check, not the primitive.
for (let i = 0; i < mulSampleValues.length; i++) {
  const a = mulSampleValues[i];
  const b = mulSampleValues[(i * 7 + 13) % mulSampleValues.length];
  mulRows.push(`${a},${b},${toHex8(cpu_umul(a, b))}`);
}
writeFileSync('umul_oracle.csv', mulRows.join('\n') + '\n');
console.log(`wrote ${mulRows.length} cpu_umul(a,b) rows to umul_oracle.csv`);
