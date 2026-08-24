#include <bit>
#include <cmath>
#include <cstdint>
#include <cstdio>

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
inline double insert_words(std::uint32_t hi, std::uint32_t lo) {
  std::uint64_t bits = 0;
  bits |= static_cast<std::uint64_t>(hi) << 32;
  bits |= static_cast<std::uint64_t>(lo);
  return std::bit_cast<double>(bits);
}

static void P(const char* name, double v) {
  std::printf("%-8s = %+.20g  bits=%016llx\n", name, v, (unsigned long long)std::bit_cast<std::uint64_t>(v));
}

double fd_expm1_dbg(double x) {
  static const double one = 1.0, tiny = 1.0e-300,
                       o_threshold = 7.09782712893383973096e+02,
                       ln2_hi = 6.93147180369123816490e-01,
                       ln2_lo = 1.90821492927058770002e-10,
                       invln2 = 1.44269504088896338700e+00,
                       Q1 = -3.33333333333331316428e-02,
                       Q2 = 1.58730158725481460165e-03,
                       Q3 = -7.93650757867487942473e-05,
                       Q4 = 4.00821782732936239552e-06,
                       Q5 = -2.01099218183624371326e-07;
  static const volatile double huge = 1.0e+300;
  (void)o_threshold; (void)tiny; (void)huge;

  double y, hi, lo, c, t, e, hxs, hfx, r1, twopk;
  std::int32_t k, xsb;
  std::uint32_t hx;

  hx = hi_word(x);
  xsb = static_cast<std::int32_t>(hx & 0x80000000u);
  hx &= 0x7fffffffu;
  c = 0.0;
  std::printf("hx=%08x xsb=%d\n", hx, xsb);

  if (hx > 0x3fd62e42u) {
    std::printf("TOOK REDUCTION BRANCH\n");
    if (hx < 0x3ff0a2b2u) {
      if (xsb == 0) { hi = x - ln2_hi; lo = ln2_lo; k = 1; }
      else { hi = x + ln2_hi; lo = -ln2_lo; k = -1; }
    } else {
      k = static_cast<std::int32_t>(invln2 * x + ((xsb == 0) ? 0.5 : -0.5));
      t = k;
      hi = x - t * ln2_hi;
      lo = t * ln2_lo;
    }
    x = hi - lo;
    c = (hi - x) - lo;
    P("hi", hi); P("lo", lo); P("x_reduced", x); P("c", c);
  } else if (hx < 0x3c900000u) {
    std::printf("TOOK TINY BRANCH\n");
    t = huge + x;
    return x - (t - (huge + x));
  } else {
    std::printf("TOOK k=0 BRANCH (no reduction)\n");
    k = 0;
  }

  hfx = 0.5 * x;
  hxs = x * hfx;
  r1 = one + hxs * (Q1 + hxs * (Q2 + hxs * (Q3 + hxs * (Q4 + hxs * Q5))));
  t = 3.0 - r1 * hfx;
  e = hxs * ((r1 - t) / (6.0 - x * t));
  P("hfx", hfx); P("hxs", hxs); P("r1", r1); P("t", t); P("e", e);
  if (k == 0) {
    double res = x - (x * e - hxs);
    P("result(k=0)", res);
    return res;
  } else {
    twopk = insert_words(0x3ff00000u + (static_cast<std::uint32_t>(k) << 20), 0);
    e = (x * (e - c) - c);
    e -= hxs;
    P("e2", e); P("twopk", twopk);
    if (k == -1) { double res = 0.5 * (x - e) - 0.5; P("result(k=-1)", res); return res; }
    if (k == 1) {
      if (x < -0.25) { double res = -2.0 * (e - (x + 0.5)); P("result(k=1,a)", res); return res; }
      else { double res = one + 2.0 * (x - e); P("result(k=1,b)", res); return res; }
    }
    if (k <= -2 || k > 56) {
      y = one - (e - x);
      if (k == 1024) y = y * 2.0 * 0x1p1023;
      else y = y * twopk;
      double res = y - one;
      P("result(far)", res);
      return res;
    }
    t = one;
    if (k < 20) {
      set_high_word(t, 0x3ff00000u - (0x200000u >> k));
      y = t - (e - x);
      y = y * twopk;
    } else {
      set_high_word(t, static_cast<std::uint32_t>((0x3ff - k) << 20));
      y = x - (e + t);
      y += one;
      y = y * twopk;
    }
    P("result(mid)", y);
    return y;
  }
}

int main(int argc, char** argv) {
  double x;
  std::uint64_t bits = std::strtoull(argv[1], nullptr, 16);
  x = std::bit_cast<double>(bits);
  P("x", x);
  double r = fd_expm1_dbg(x);
  P("FINAL", r);
  return 0;
}
