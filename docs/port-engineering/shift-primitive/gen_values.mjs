// gen_values.mjs
//
// Produces the single, shared list of int32 test operands used by BOTH the
// JS oracle generator (gen_oracle.mjs) and the C++ verifier
// (verify_sweep.cpp), so there is exactly one source of truth for "which
// values were tested" -- no risk of the two languages silently testing
// different inputs.
//
// Composition:
//  - A curated, deliberately adversarial set: every power of two (both
//    signs), every power-of-two-minus-one (both signs), INT32_MIN/MAX,
//    UINT32_MAX (as its int32 bit-pattern, -1), values near those
//    boundaries (+-1, +-2), and a handful of named hash constants that show
//    up in the real programs (0x9E3779B9, golden-ratio constants, etc).
//  - 100,000 pseudorandom int32 values drawn from a fixed-seed PRNG
//    (mulberry32, seeded 0xC0FFEE), so the run is exactly reproducible.
//    (A second, larger 2,000,000-value breadth tier, verified via checksum
//    rather than full per-shift materialization, is added separately by
//    gen_breadth_values.mjs / verify_breadth.cpp.)
//
// Output: values.txt, one signed-decimal int32 value per line.

'use strict';
import { writeFileSync } from 'node:fs';

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0);
  };
}

const curated = new Set();
curated.add(0); curated.add(1); curated.add(-1);
curated.add(2147483647);   // INT32_MAX
curated.add(-2147483648);  // INT32_MIN
curated.add(-2);
curated.add(2147483646);
curated.add(-2147483647);

for (let k = 0; k <= 31; k++) {
  const pow2 = Math.pow(2, k);
  // as int32 bit pattern: values >= 2^31 wrap negative
  const asInt32 = pow2 <= 2147483647 ? pow2 : (pow2 - 4294967296);
  curated.add(asInt32);
  curated.add(-asInt32);
  curated.add(asInt32 + 1);
  curated.add(asInt32 - 1);
  curated.add(-asInt32 + 1);
  curated.add(-asInt32 - 1);

  const pow2m1 = pow2 - 1; // power-of-two-minus-one
  const asInt32b = pow2m1 <= 2147483647 ? pow2m1 : (pow2m1 - 4294967296);
  curated.add(asInt32b);
  curated.add(-asInt32b);
}

// -1 IS UINT32_MAX's int32 bit pattern already covered above.

// Named hash/mix constants seen in the real frontier programs (median,
// spookyTicker, osd, texture) -- included so the curated set overlaps with
// real-program constants, not just synthetic boundaries.
const namedConstants = [
  0x9E3779B9, 0x85EBCA6B, 0xC2B2AE35, 0x27D4EB2F, 0x165667B1,
  0x2246C5C5, 0x0C6EF372, 0x1927B93A,
  2146121005, 2221713035, // literal multiply constants from spookyTicker hash_mix
];
for (const c of namedConstants) {
  // reinterpret as int32 bit pattern (JS `|0` truncates to int32 range)
  curated.add(c | 0);
  curated.add((-c) | 0);
}

const N_RANDOM = 100_000;
const rng = mulberry32(0xC0FFEE);
const randomValues = new Array(N_RANDOM);
for (let i = 0; i < N_RANDOM; i++) {
  const u32 = rng();
  // reinterpret the raw uint32 bits as a signed int32 (two's complement)
  randomValues[i] = u32 >= 2147483648 ? (u32 - 4294967296) : u32;
}

const all = [...curated, ...randomValues];

writeFileSync('values.txt', all.join('\n') + '\n');
console.log(`wrote ${all.length} values (${curated.size} curated + ${randomValues.length} pseudorandom) to values.txt`);
