// probe_semantics.mjs
//
// Step 1 of the shift-primitive task: establish exact JS bitwise/shift
// semantics EMPIRICALLY (not from memory), across a deliberately
// adversarial input set: negative values, values with the high bit set,
// values >= 2^31, values >= 2^32, non-integer inputs, shift counts of
// 0, 31, 32, 33, and negative shift counts.
//
// This script only reads nothing and writes only into this task's own
// directory (probe_semantics_output.json / .txt). No git, no writes
// outside docs/port-engineering/shift-primitive/.
//
// Run: node probe_semantics.mjs > probe_semantics_output.txt
//      (also writes probe_semantics_output.json)

'use strict';

const results = [];

function record(section, expr, inputs, value) {
  results.push({ section, expr, inputs, value: describe(value) });
}

function describe(v) {
  if (typeof v === 'number') {
    if (Number.isNaN(v)) return { type: 'number', repr: 'NaN' };
    if (!Number.isFinite(v)) return { type: 'number', repr: v > 0 ? 'Infinity' : '-Infinity' };
    return { type: 'number', repr: String(v), hex: Number.isInteger(v) ? toHex32IfInRange(v) : undefined };
  }
  return { type: typeof v, repr: String(v) };
}

function toHex32IfInRange(v) {
  // Only annotate with a hex view when the value plausibly is an int32/uint32
  // bit pattern, purely for human-readability in the report; never used for
  // computation.
  if (v >= -2147483648 && v <= 4294967295) {
    const u = v < 0 ? (v >>> 0) : v;
    return '0x' + (u >>> 0).toString(16).padStart(8, '0');
  }
  return undefined;
}

// ---------------------------------------------------------------------
// Section A: adversarial scalar value set for single-operand ops (>>, >>>,
// <<, ~) exercised at representative shift counts.
// ---------------------------------------------------------------------

const adversarialValues = [
  0, 1, -1,
  2147483647,           // INT32_MAX
  -2147483648,          // INT32_MIN
  2147483648,           // 2^31 (== INT32_MIN's uint32 magnitude, as a positive JS number)
  4294967295,           // UINT32_MAX
  4294967296,           // 2^32 exactly
  4294967297,           // 2^32 + 1
  -4294967296,          // -(2^32)
  8589934591,           // 2^33 - 1
  1073741824,           // 2^30
  -1073741824,          // -(2^30)
  65536, -65536,
  65535, -65535,
  255, -255,
  256, -256,
  16777216, -16777216,  // 2^24
];

const shiftCounts = [0, 1, 15, 16, 31, 32, 33, 63, 64, -1, -31, -32, -33, 1000000];

for (const v of adversarialValues) {
  for (const s of shiftCounts) {
    record('A.shift_right_signed', 'v >> s', { v, s }, v >> s);
    record('A.shift_right_unsigned', 'v >>> s', { v, s }, v >>> s);
    record('A.shift_left', 'v << s', { v, s }, v << s);
  }
  record('A.bitwise_not', '~v', { v }, ~v);
}

// ---------------------------------------------------------------------
// Section B: non-integer / out-of-range operand coercion (ToInt32/ToUint32
// behavior for the shift/bitwise family) -- verified empirically, not
// assumed.
// ---------------------------------------------------------------------

const nonIntegerValues = [
  3.7, -3.7, 3.2, -3.2, 0.5, -0.5, 2.9999999,
  1e10, -1e10, 1e20, -1e20,
  NaN, Infinity, -Infinity,
  4294967296.5, -0, 2147483647.9999, -2147483648.9999,
];

for (const v of nonIntegerValues) {
  record('B.coerce_shift_right_signed', 'v >> 0', { v }, v >> 0);
  record('B.coerce_shift_right_unsigned', 'v >>> 0', { v }, v >>> 0);
  record('B.coerce_bitwise_or', 'v | 0', { v }, v | 0);
  record('B.coerce_bitwise_not', '~v', { v }, ~v);
}

// Non-integer / out-of-range SHIFT COUNTS (the RHS operand of >>, >>>, <<).
const nonIntegerShiftCounts = [2.9, -2.9, 31.9, 32.1, NaN, Infinity, -Infinity, 4294967328 /* = 32 mod 2^32, but as a huge literal */];
for (const s of nonIntegerShiftCounts) {
  record('B.coerce_shift_count_signed', '1 >> s', { v: 1, s }, 1 >> s);
  record('B.coerce_shift_count_signed_neg', '(-1) >> s', { v: -1, s }, (-1) >> s);
  record('B.coerce_shift_count_unsigned', '(0xFFFFFFFF|0) >>> s', { v: -1, s }, (0xFFFFFFFF | 0) >>> s);
}

// ---------------------------------------------------------------------
// Section C: binary bitwise ops (&, |, ^) on an adversarial pair set,
// including both operands negative, both with high bit set, and mixed.
// ---------------------------------------------------------------------

const pairs = [
  [-1, -1], [-1, 1], [1, -1], [0, -1], [-1, 0],
  [2147483647, -2147483648], [-2147483648, -2147483648],
  [2147483648, 2147483648], [4294967295, 4294967295],
  [0x9E3779B9 | 0, -1], [0x85EBCA6B | 0, 0x9E3779B9 | 0],
  [1073741824, -1073741824],
  [4294967296, 4294967296], // both coerce to 0
];

for (const [a, b] of pairs) {
  record('C.and', 'a & b', { a, b }, a & b);
  record('C.or', 'a | b', { a, b }, a | b);
  record('C.xor', 'a ^ b', { a, b }, a ^ b);
}

// ---------------------------------------------------------------------
// Section D: the specific masking claim -- shift counts reduce mod 32,
// verified by direct equality checks across many amounts (not asserted,
// EMPIRICALLY COMPARED and the boolean result recorded).
// ---------------------------------------------------------------------

const maskingProbeValues = [1, -1, 2147483647, -2147483648, 0x12345678 | 0];
for (const v of maskingProbeValues) {
  for (let s = -70; s <= 130; s++) {
    const direct = v >> s;
    const masked = v >> (((s % 32) + 32) % 32); // s mod 32, normalized to [0,32)
    if (direct !== masked) {
      record('D.masking_signed_shift_MISMATCH', 'v >> s vs v >> (s mod 32)', { v, s }, { direct, masked });
    }
  }
  for (let s = -70; s <= 130; s++) {
    const direct = v >>> s;
    const masked = v >>> (((s % 32) + 32) % 32);
    if (direct !== masked) {
      record('D.masking_unsigned_shift_MISMATCH', 'v >>> s vs v >>> (s mod 32)', { v, s }, { direct, masked });
    }
  }
  for (let s = -70; s <= 130; s++) {
    const direct = v << s;
    const masked = v << (((s % 32) + 32) % 32);
    if (direct !== masked) {
      record('D.masking_left_shift_MISMATCH', 'v << s vs v << (s mod 32)', { v, s }, { direct, masked });
    }
  }
}
record('D.masking_summary', 'count of mismatches found (should be 0 if "amount mod 32" holds)', {},
  results.filter(r => r.section.endsWith('_MISMATCH')).length);

// ---------------------------------------------------------------------
// Emit
// ---------------------------------------------------------------------

console.log(JSON.stringify({ node_version: process.version, generated_at: new Date().toISOString(), results }, null, 2));
