// fdlibm_off.cpp -- noisemaker::fdlibm functions that must NOT be compiled
// with fdlibm.cpp's -ffp-contract=fast override, split into their own
// translation unit (deliberately named for what it needs, not for which
// functions happen to live here today).
//
// log2(): a line-for-line transcription of V8's src/base/ieee754.cc log2()
// (and its k_log1p() kernel), exactly like fdlibm.cpp's other functions --
// see fdlibm.hpp and fdlibm.cpp for the general provenance/FMA background.
// Its combining arithmetic at the end (`hi = f - hfsq; ... val_lo = (lo +
// hi) * ivln2lo + lo * ivln2hi; w = y + val_hi; val_lo += (y - w) +
// val_hi; ...`) is a Dekker/two-sum-style compensated summation. Those
// algorithms work by exploiting exact IEEE-754 rounding at every single
// step (the whole point of `SET_LOW_WORD(hi, 0)` above is to force an
// exactly-representable split); fusing any of those steps into an FMA
// changes the rounding they depend on and breaks the compensation, rather
// than just nudging the result by a coincidental ULP. Measured
// (docs/port-engineering/v8-math/v8-math-report.md): 0/50,000 divergent
// from V8's Math.log2 under -ffp-contract=off, REGRESSING to ~108-208
// divergent under -ffp-contract=fast -- the opposite direction from every
// fdlibm.cpp function, where fast is required to reach 0.
//
// hypot(): NOT compiled by V8's C++ toolchain at all -- Math.hypot is a
// Torque builtin (src/builtins/math.tq), lowered directly to TurboFan/CSA
// machine code by V8's OWN JIT backend, which has no relationship to
// clang's -ffp-contract flag. Measured directly: the plain, unfused
// `na*na + nb*nb` (no fma) matches V8's Math.hypot(x,y) bit-for-bit; an
// explicit `std::fma(na, na, nb*nb)` does NOT (see the report). Under this
// file's ordinary -ffp-contract=off, the plain expression as written stays
// unfused and matches; under fdlibm.cpp's -ffp-contract=fast override the
// auto-fuser was contracting it and introduced a measured 56-99/50,000
// divergence (fixed by this file's move, not by any added std::fma).
//
// Do not merge either of these back into fdlibm.cpp, and do not add an
// -ffp-contract=fast override for this file.

#include "noisemaker/fdlibm.hpp"

#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace noisemaker::fdlibm {
namespace {

inline std::uint32_t hi_word(double x) {
  return static_cast<std::uint32_t>(std::bit_cast<std::uint64_t>(x) >> 32);
}

inline std::uint32_t lo_word(double x) {
  return static_cast<std::uint32_t>(std::bit_cast<std::uint64_t>(x) & 0xffffffffu);
}

inline void set_high_word(double& d, std::uint32_t v) {
  std::uint64_t bits = std::bit_cast<std::uint64_t>(d);
  bits &= 0x0000'0000'ffff'ffffull;
  bits |= static_cast<std::uint64_t>(v) << 32;
  d = std::bit_cast<double>(bits);
}

inline void set_low_word(double& d, std::uint32_t v) {
  std::uint64_t bits = std::bit_cast<std::uint64_t>(d);
  bits &= 0xffff'ffff'0000'0000ull;
  bits |= static_cast<std::uint64_t>(v);
  d = std::bit_cast<double>(bits);
}

// k_log1p(f): log(1+f) - f for 1+f in ~[sqrt(2)/2, sqrt(2)]. Shared kernel
// used by log2() below, exactly as v8_ieee754_reference.cc's k_log1p.
// (log()'s own fd_log in fdlibm.cpp inlines the equivalent steps directly,
// exactly as V8's log() does -- log() and log2() are separate top-level
// functions in the reference and are kept separate here too.)
double k_log1p(double f) {
  static const double Lg1 = 6.666666666666735130e-01,
                       Lg2 = 3.999999999940941908e-01,
                       Lg3 = 2.857142874366239149e-01,
                       Lg4 = 2.222219843214978396e-01,
                       Lg5 = 1.818357216161805012e-01,
                       Lg6 = 1.531383769920937332e-01,
                       Lg7 = 1.479819860511658591e-01;

  double hfsq, s, z, w, r, t1, t2;
  s = f / (2.0 + f);
  z = s * s;
  w = z * z;
  t1 = w * (Lg2 + w * (Lg4 + w * Lg6));
  t2 = z * (Lg1 + w * (Lg3 + w * (Lg5 + w * Lg7)));
  r = t2 + t1;
  hfsq = 0.5 * f * f;
  return s * (hfsq + r);
}

// log2(x): base-2 logarithm, exactly as v8_ieee754_reference.cc's log2 --
// NOT log(x)*invln2, which would round differently.
double fd_log2(double x) {
  static const double two54 = 1.80143985094819840000e+16,
                       ivln2hi = 1.44269504072144627571e+00,
                       ivln2lo = 1.67517131648865118353e-10;

  double f, hfsq, hi, lo, r, val_hi, val_lo, w, y;
  std::int32_t i, k, hx;
  std::uint32_t lx;

  hx = static_cast<std::int32_t>(hi_word(x));
  lx = lo_word(x);

  k = 0;
  if (hx < 0x00100000) {
    if (((static_cast<std::uint32_t>(hx) & 0x7fffffffu) | lx) == 0) {
      return -std::numeric_limits<double>::infinity();
    }
    if (hx < 0) {
      return std::numeric_limits<double>::signaling_NaN();
    }
    k -= 54;
    x *= two54;
    hx = static_cast<std::int32_t>(hi_word(x));
  }
  if (hx >= 0x7ff00000) return x + x;
  if (hx == 0x3ff00000 && lx == 0) return 0.0;
  k += (hx >> 20) - 1023;
  hx &= 0x000fffff;
  i = (hx + 0x95f64) & 0x100000;
  set_high_word(x, static_cast<std::uint32_t>(hx | (i ^ 0x3ff00000)));
  k += (i >> 20);
  y = static_cast<double>(k);
  f = x - 1.0;
  hfsq = 0.5 * f * f;
  r = k_log1p(f);

  hi = f - hfsq;
  set_low_word(hi, 0);
  lo = (f - hi) - hfsq + r;
  val_hi = hi * ivln2hi;
  val_lo = (lo + hi) * ivln2lo + lo * ivln2hi;

  w = y + val_hi;
  val_lo += (y - w) + val_hi;
  val_hi = w;

  return val_lo + val_hi;
}

}  // namespace

double log2(double x) noexcept { return fd_log2(x); }

// ============================================================
// hypot: V8's Math.hypot (src/builtins/math.tq, FastMathHypot/MathHypot)
// has a DIFFERENT fast-path formula per argument count -- 2 args: no Kahan
// compensation at all; 3 args: a compensation term folded in between only
// the first two squared terms; >3 args (the "Slow" label): a full running
// Kahan-compensated sum. These are transcribed as three separate overloads
// below rather than one generic loop, because unifying them would use the
// wrong (N-arg) formula for the N=2 and N=3 cases and produce a different
// last bit than V8 whenever the compensation terms are non-zero. See this
// file's header comment for why hypot needs THIS file's ordinary
// -ffp-contract=off rather than fdlibm.cpp's override.
// ============================================================
double hypot(double x, double y) noexcept {
  double ax = std::fabs(x);
  double ay = std::fabs(y);
  // V8 checks has_infinity before has_nan: Infinity beats NaN (matches the
  // ECMA-262 Math.hypot spec, step 4.a/4.b ordering).
  if (std::isinf(ax) || std::isinf(ay)) return std::numeric_limits<double>::infinity();
  if (std::isnan(ax) || std::isnan(ay)) return std::numeric_limits<double>::quiet_NaN();
  double max = ax > ay ? ax : ay;
  if (max == 0.0) return 0.0;
  // FastMathHypot's 2-arg path, math.tq: NO Kahan compensation.
  const double na = ax / max;
  const double nb = ay / max;
  return std::sqrt(na * na + nb * nb) * max;
}

double hypot(double x, double y, double z) noexcept {
  double ax = std::fabs(x);
  double ay = std::fabs(y);
  double az = std::fabs(z);
  if (std::isinf(ax) || std::isinf(ay) || std::isinf(az)) {
    return std::numeric_limits<double>::infinity();
  }
  if (std::isnan(ax) || std::isnan(ay) || std::isnan(az)) {
    return std::numeric_limits<double>::quiet_NaN();
  }
  double max = ax > ay ? ax : ay;
  max = az > max ? az : max;
  if (max == 0.0) return 0.0;
  // FastMathHypot's 3-arg path, math.tq: the compensation is computed from
  // powerA/powerB only, then subtracted from powerC -- NOT a running
  // Kahan sum over all three terms. Preserve that exact shape.
  const double power_a = (ax / max) * (ax / max);
  const double power_b = (ay / max) * (ay / max);
  const double compensation = (power_a + power_b) - power_a - power_b;
  const double power_c = (az / max) * (az / max) - compensation;
  return std::sqrt(power_a + power_b + power_c) * max;
}

// General N-argument path, matching math.tq's "Slow" label (the runtime's
// own fallback for Math.hypot(...) called with more than 3 arguments, or
// with a non-fast-path argument shape). Not currently reached by any call
// site in this project (every kernel calls the 2- or 3-argument form), but
// ported for completeness of "one math layer" per the parity contract.
double hypot_n(const double* values, int count) noexcept {
  if (count == 0) return 0.0;
  bool one_arg_is_nan = false;
  double max = 0.0;
  std::vector<double> abs_values(static_cast<std::size_t>(count));
  for (int i = 0; i < count; ++i) {
    const double value = values[i];
    if (std::isnan(value)) {
      one_arg_is_nan = true;
      abs_values[static_cast<std::size_t>(i)] = 0.0;
      continue;
    }
    const double abs_value = std::fabs(value);
    abs_values[static_cast<std::size_t>(i)] = abs_value;
    if (abs_value > max) max = abs_value;
  }
  if (std::isinf(max)) return std::numeric_limits<double>::infinity();
  if (one_arg_is_nan) return std::numeric_limits<double>::quiet_NaN();
  if (max == 0.0) return 0.0;

  // math.tq's exact Slow-path Kahan loop: summand is offset by the RUNNING
  // compensation before being added (not a fabs-magnitude branch -- V8
  // does not use the classic Neumaier variant here).
  double sum = 0.0;
  double compensation = 0.0;
  for (int i = 0; i < count; ++i) {
    const double n = abs_values[static_cast<std::size_t>(i)] / max;
    const double summand = n * n - compensation;
    const double preliminary = sum + summand;
    compensation = (preliminary - sum) - summand;
    sum = preliminary;
  }
  return std::sqrt(sum) * max;
}

}  // namespace noisemaker::fdlibm
