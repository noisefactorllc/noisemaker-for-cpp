// Deterministic adversarial input generator. Produces a list of raw IEEE-754
// double bit patterns (as 16-hex-digit lowercase strings, one per line) that
// both the Node probe and the C++ probes read verbatim, so both languages
// compute on bit-identical inputs. No randomness leaks in from either
// runtime's own PRNG; a fixed-seed xorshift is used instead.
//
// Usage: node gen_inputs.mjs > inputs.hex

const buf = new ArrayBuffer(8);
const f64 = new Float64Array(buf);
const u64 = new BigUint64Array(buf);

function bitsOf(x) {
  f64[0] = x;
  return u64[0];
}
function hex(bits) {
  return bits.toString(16).padStart(16, '0');
}
function isFiniteBits(bits) {
  const exp = Number((bits >> 52n) & 0x7ffn);
  return exp !== 0x7ff;
}

const seen = new Set();
const out = [];
function push(x) {
  if (!Number.isFinite(x)) return;
  const bits = bitsOf(x);
  const h = hex(bits);
  if (seen.has(h)) return;
  seen.add(h);
  out.push(h);
}
function pushBits(bits) {
  if (!isFiniteBits(bits)) return;
  const h = hex(bits);
  if (seen.has(h)) return;
  seen.add(h);
  out.push(h);
}

// ---- A. Dense linspace near zero ----
for (let i = -2000; i <= 2000; i++) {
  push(i * 5e-10); // covers [-1e-6, 1e-6]
}

// ---- B. Denormal / subnormal range, log-spaced, both signs ----
{
  const minDenorm = 5e-324; // smallest positive double (rounds to true min)
  const minNormal = 2.2250738585072014e-308;
  const steps = 2000;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const mag = Math.exp(Math.log(minDenorm) + t * (Math.log(minNormal) - Math.log(minDenorm)));
    push(mag);
    push(-mag);
  }
  // exact denormal bit patterns at the extremes
  for (let m = 1n; m <= 64n; m++) {
    pushBits(m); // positive denormals, bits 1..64
    pushBits(m | 0x8000000000000000n); // negative denormals
  }
  pushBits(0x000fffffffffffffn); // largest denormal
  pushBits(0x800fffffffffffffn);
  pushBits(0x0010000000000000n); // smallest normal
  pushBits(0x8010000000000000n);
}

// ---- C. Boundary clusters: fdlibm/V8 branch thresholds ----
const boundaries = [
  Math.pow(2, -54),
  Math.pow(2, -28),
  Math.pow(2, -27),
  0.5 * Math.LN2,
  Math.LN2,
  1.5 * Math.LN2,
  1.0,
  22.0,
  56 * Math.LN2,
  7.09782712893383973096e+02, // o_threshold (exp/expm1 overflow)
  7.45133219101941108420e+02, // |u_threshold| (exp underflow)
  Math.PI / 4,
  3 * Math.PI / 4,
  Math.PI / 2,
  Math.pow(2, 19) * (Math.PI / 2), // rem_pio2 medium/large boundary
  0.3, // __kernel_cos small-x branch (ix < 0x3FD33333)
  0.78125, // __kernel_cos qx branch
  Math.pow(2, -27), // __kernel_sin/__kernel_cos |x|<2**-27 branch
  709.7822265625, // sinh LOG_MAXD
  710.4758600739439, // sinh KSINH_OVERFLOW
];
// multiples of pi/2 out to a large k, since sin/cos rem_pio2 branches on
// exact proximity to (2k+1)*pi/4 windows
for (let k = 1; k <= 300; k++) {
  boundaries.push(k * (Math.PI / 2));
}
// exact hi-word boundaries used literally in the fdlibm source (as bit
// patterns reconstructed from their documented high words)
const hiWordBoundaries = [
  0x3fd62e42n, 0x3ff0a2b2n, 0x40036000n /* ~22 hi word approx */,
  0x40360000n, 0x4043687an, 0x40862e42n, 0xc0874910n,
  0x3e300000n, 0x3c900000n, 0x3e400000n, 0x3fe921fbn, 0x4002d97cn,
  0x413921fbn, 0x3fd33333n, 0x3fe90000n,
];
for (const hw of hiWordBoundaries) {
  pushBits(hw << 32n);
  pushBits((hw << 32n) | 0x8000000000000000n);
}
for (const b0 of boundaries) {
  if (!Number.isFinite(b0)) continue;
  for (const b of [b0, -b0]) {
    const bits = bitsOf(b);
    const sign = bits & 0x8000000000000000n;
    const mag = bits & 0x7fffffffffffffffn;
    for (let d = -64n; d <= 64n; d++) {
      // step the MAGNITUDE by d ULPs, then re-apply the sign, so we never
      // walk a negative boundary's bit pattern across zero into the other
      // sign's bit space.
      const steppedMag = mag + d;
      if (steppedMag < 0n || steppedMag > 0x7ff0000000000000n) continue;
      pushBits(steppedMag | sign);
    }
  }
}

// ---- D. Systematic wide-domain linspace ----
for (let i = -40000; i <= 40000; i++) {
  push(i * 0.0025); // [-100, 100] step 0.0025
}
for (let i = -2000; i <= 2000; i++) {
  push(i * 5); // [-10000, 10000] step 5
}
const extremes = [
  1e15, -1e15, 1e100, -1e100, 1e300, -1e300,
  Number.MAX_VALUE, -Number.MAX_VALUE,
  1e-300, -1e-300, 1e-320, -1e-320,
  123456.789, -987654.321, 1e10, -1e10, 1e6, -1e6,
];
for (const e of extremes) push(e);

// ---- E. Pseudorandom, fixed-seed xorshift128+ ----
// Deterministic PRNG so re-runs are bit-reproducible without relying on
// either language's own RNG (keeps Node/C++ input generation moot — Node
// generates once, C++ never generates, only reads).
function makeXorshift128p(seedHi, seedLo) {
  let s0 = seedHi;
  let s1 = seedLo;
  const MASK = (1n << 64n) - 1n;
  return function next() {
    let x = s0;
    const y = s1;
    s0 = y;
    x ^= (x << 23n) & MASK;
    x ^= x >> 17n;
    x ^= y ^ (y >> 26n);
    s1 = x & MASK;
    return (s0 + s1) & MASK;
  };
}
const rng = makeXorshift128p(0x9e3779b97f4a7c15n, 0xbf58476d1ce4e5b9n);

// E1: fully bit-random (log-uniform magnitude coverage), filtered finite
for (let i = 0; i < 150000; i++) {
  pushBits(rng());
}
// E2: random doubles uniform in value over [-50, 50] (linear coverage of the
// range most transcendentals in the shader corpus actually see)
for (let i = 0; i < 50000; i++) {
  const bits = rng();
  const u = Number(bits % 1000000000n) / 1000000000; // [0,1)
  push((u - 0.5) * 100);
}
// E3: random doubles uniform in value over [-1, 1] (tanh/sin/cos heavy zone)
for (let i = 0; i < 30000; i++) {
  const bits = rng();
  const u = Number(bits % 1000000000n) / 1000000000;
  push((u - 0.5) * 2);
}

// ---- F. Explicit zero / signed-zero ----
push(0.0);
push(-0.0);

process.stderr.write(`generated ${out.length} unique finite inputs\n`);
process.stdout.write(out.join('\n') + '\n');
