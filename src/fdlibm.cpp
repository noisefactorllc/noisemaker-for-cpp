// fdlibm.cpp — implementation. See fdlibm.hpp for why this exists.
//
// This is a line-for-line transcription of V8's src/base/ieee754.cc
// (checked against a fresh fetch of the EXACT V8 tag this environment's
// Node reports -- 14.6.202.33-node.19 -- see
// docs/port-engineering/v8-math/v8_ieee754_reference.cc, and the pow/hypot
// provenance notes in fdlibm.hpp), which is itself adapted from Sun
// Microsystems' fdlibm:
//
// ====================================================
// Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
//
// Developed at SunSoft, a Sun Microsystems, Inc. business.
// Permission to use, copy, modify, and distribute this
// software is freely granted, provided that this notice
// is preserved.
// ====================================================
//
// V8's adaptation additionally copyright 2016 the V8 project authors,
// under a BSD-style license (V8 is BSD-licensed; the fdlibm portions carry
// the original Sun notice above per V8's own file header).
//
// Ported: expm1, exp, tanh, sin, cos, tan, asin, acos, atan, atan2, log,
// log2, pow (V8's live math::pow wrapper, not the retired fdlibm pow), and
// hypot (V8's own Torque algorithm, not an fdlibm one) -- plus the internal
// argument-reduction machinery sin/cos/tan require (__ieee754_rem_pio2,
// __kernel_rem_pio2, __kernel_sin, __kernel_cos, __kernel_tan) and log2's
// k_log1p kernel. See fdlibm.hpp for the per-function provenance (which of
// these come from base::ieee754::*, which from v8::internal::math::*, and
// which from a Torque builtin).
//
// Word-access macros are translated to functions using std::bit_cast
// (C++20), which is well-defined (no strict-aliasing UB) and produces
// identical code to the original's memcpy-based type punning. Everything
// else — branch structure, operator order, constant tables — is preserved
// exactly, because THAT is what determines the exact output bits.
//
// Compile this translation unit with -ffp-contract=fast (scoped in
// CMakeLists.txt to just this one file). See fdlibm.hpp for why.

#include "noisemaker/fdlibm.hpp"

#include <bit>
#include <cmath>
#include <cstdint>
#include <limits>

namespace noisemaker::fdlibm {
namespace {

// ---- word access helpers (replace V8's EXTRACT_WORDS / GET_*_WORD /
//      SET_*_WORD / INSERT_WORDS macros) ----

inline std::uint32_t hi_word(double x) {
  return static_cast<std::uint32_t>(std::bit_cast<std::uint64_t>(x) >> 32);
}

inline std::uint32_t lo_word(double x) {
  return static_cast<std::uint32_t>(std::bit_cast<std::uint64_t>(x) &
                                     0xffffffffu);
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

inline double insert_words(std::uint32_t hi, std::uint32_t lo) {
  std::uint64_t bits = 0;
  bits |= static_cast<std::uint64_t>(hi) << 32;
  bits |= static_cast<std::uint64_t>(lo);
  return std::bit_cast<double>(bits);
}

// ============================================================
// expm1(x): e^x - 1, accurate near x == 0.
// ============================================================
double fd_expm1(double x) {
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

  double y, hi, lo, c, t, e, hxs, hfx, r1, twopk;
  std::int32_t k, xsb;
  std::uint32_t hx;

  hx = hi_word(x);
  xsb = static_cast<std::int32_t>(hx & 0x80000000u); /* sign bit of x */
  hx &= 0x7fffffffu;                                 /* high word of |x| */
  c = 0.0;

  /* filter out huge and non-finite argument */
  if (hx >= 0x4043687Au) {   /* if |x|>=56*ln2 */
    if (hx >= 0x40862E42u) { /* if |x|>=709.78... */
      if (hx >= 0x7ff00000u) {
        std::uint32_t low = lo_word(x);
        if (((hx & 0xfffffu) | low) != 0)
          return x + x; /* NaN */
        else
          return (xsb == 0) ? x : -1.0; /* exp(+-inf)={inf,-1} */
      }
      if (x > o_threshold) return huge * huge; /* overflow */
    }
    if (xsb != 0) {          /* x < -56*ln2, return -1.0 with inexact */
      if (x + tiny < 0.0)    /* raise inexact */
        return tiny - one;   /* return -1 */
    }
  }

  /* argument reduction */
  if (hx > 0x3fd62e42u) {   /* if  |x| > 0.5 ln2 */
    if (hx < 0x3ff0a2b2u) { /* and |x| < 1.5 ln2 */
      if (xsb == 0) {
        hi = x - ln2_hi;
        lo = ln2_lo;
        k = 1;
      } else {
        hi = x + ln2_hi;
        lo = -ln2_lo;
        k = -1;
      }
    } else {
      k = static_cast<std::int32_t>(invln2 * x +
                                     ((xsb == 0) ? 0.5 : -0.5));
      t = k;
      hi = x - t * ln2_hi; /* t*ln2_hi is exact here */
      lo = t * ln2_lo;
    }
    x = hi - lo;
    c = (hi - x) - lo;
  } else if (hx < 0x3c900000u) { /* when |x|<2**-54, return x */
    t = huge + x;                /* return x with inexact flags when x!=0 */
    return x - (t - (huge + x));
  } else {
    k = 0;
  }

  /* x is now in primary range */
  hfx = 0.5 * x;
  hxs = x * hfx;
  r1 = one + hxs * (Q1 + hxs * (Q2 + hxs * (Q3 + hxs * (Q4 + hxs * Q5))));
  t = 3.0 - r1 * hfx;
  e = hxs * ((r1 - t) / (6.0 - x * t));
  if (k == 0) {
    return x - (x * e - hxs); /* c is 0 */
  } else {
    twopk = insert_words(
        0x3ff00000u + (static_cast<std::uint32_t>(k) << 20), 0); /* 2^k */
    e = (x * (e - c) - c);
    e -= hxs;
    if (k == -1) return 0.5 * (x - e) - 0.5;
    if (k == 1) {
      if (x < -0.25)
        return -2.0 * (e - (x + 0.5));
      else
        return one + 2.0 * (x - e);
    }
    if (k <= -2 || k > 56) { /* suffice to return exp(x)-1 */
      y = one - (e - x);
      if (k == 1024)
        y = y * 2.0 * 0x1p1023;
      else
        y = y * twopk;
      return y - one;
    }
    t = one;
    if (k < 20) {
      set_high_word(t, 0x3ff00000u - (0x200000u >> k)); /* t=1-2^-k */
      y = t - (e - x);
      y = y * twopk;
    } else {
      set_high_word(t, static_cast<std::uint32_t>((0x3ff - k) << 20)); /* 2^-k */
      y = x - (e + t);
      y += one;
      y = y * twopk;
    }
  }
  return y;
}

// ============================================================
// exp(x): e^x.
// ============================================================
double fd_exp(double x) {
  static const double one = 1.0, halF[2] = {0.5, -0.5},
                       o_threshold = 7.09782712893383973096e+02,
                       u_threshold = -7.45133219101941108420e+02,
                       ln2HI[2] = {6.93147180369123816490e-01,
                                   -6.93147180369123816490e-01},
                       ln2LO[2] = {1.90821492927058770002e-10,
                                   -1.90821492927058770002e-10},
                       invln2 = 1.44269504088896338700e+00,
                       P1 = 1.66666666666666019037e-01,
                       P2 = -2.77777777770155933842e-03,
                       P3 = 6.61375632143793436117e-05,
                       P4 = -1.65339022054652515390e-06,
                       P5 = 4.13813679705723846039e-08,
                       E = 2.718281828459045;

  static const volatile double huge = 1.0e+300,
                                twom1000 = 9.33263618503218878990e-302,
                                two1023 = 8.988465674311579539e307;

  double y, hi = 0.0, lo = 0.0, c, t, twopk;
  std::int32_t k = 0, xsb;
  std::uint32_t hx;

  hx = hi_word(x);
  xsb = static_cast<std::int32_t>((hx >> 31) & 1u); /* sign bit of x */
  hx &= 0x7fffffffu;                                /* high word of |x| */

  /* filter out non-finite argument */
  if (hx >= 0x40862E42u) { /* if |x|>=709.78... */
    if (hx >= 0x7ff00000u) {
      std::uint32_t lx = lo_word(x);
      if (((hx & 0xfffffu) | lx) != 0)
        return x + x; /* NaN */
      else
        return (xsb == 0) ? x : 0.0; /* exp(+-inf)={inf,0} */
    }
    if (x > o_threshold) return huge * huge;         /* overflow */
    if (x < u_threshold) return twom1000 * twom1000; /* underflow */
  }

  /* argument reduction */
  if (hx > 0x3fd62e42u) {   /* if  |x| > 0.5 ln2 */
    if (hx < 0x3ff0a2b2u) { /* and |x| < 1.5 ln2 */
      if (x == 1.0) return E;
      hi = x - ln2HI[xsb];
      lo = ln2LO[xsb];
      k = 1 - xsb - xsb;
    } else {
      k = static_cast<std::int32_t>(invln2 * x + halF[xsb]);
      t = k;
      hi = x - t * ln2HI[0]; /* t*ln2HI is exact here */
      lo = t * ln2LO[0];
    }
    x = hi - lo;
  } else if (hx < 0x3e300000u) {         /* when |x|<2**-28 */
    if (huge + x > one) return one + x; /* trigger inexact */
  } else {
    k = 0;
  }

  /* x is now in primary range */
  t = x * x;
  if (k >= -1021) {
    twopk = insert_words(
        0x3ff00000u + (static_cast<std::uint32_t>(k) << 20), 0);
  } else {
    twopk = insert_words(
        0x3ff00000u + (static_cast<std::uint32_t>(k + 1000) << 20), 0);
  }
  c = x - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))));
  if (k == 0) {
    return one - ((x * c) / (c - 2.0) - x);
  } else {
    y = one - ((lo - (x * c) / (2.0 - c)) - hi);
  }
  if (k >= -1021) {
    if (k == 1024) return y * 2.0 * two1023;
    return y * twopk;
  } else {
    return y * twopk * twom1000;
  }
}

// ============================================================
// __ieee754_rem_pio2 / __kernel_rem_pio2 / __kernel_sin / __kernel_cos —
// argument reduction and [-pi/4, pi/4] kernels shared by sin() and cos().
// ============================================================

int kernel_rem_pio2(double* x, double* y, int e0, int nx, int prec,
                     const std::int32_t* ipio2) {
  static const int init_jk[] = {2, 3, 4, 6};

  static const double PIo2[] = {
      1.57079625129699707031e+00, 7.54978941586159635335e-08,
      5.39030252995776476554e-15, 3.28200341580791294123e-22,
      1.27065575308067607349e-29, 1.22933308981111328932e-36,
      2.73370053816464559624e-44, 2.16741683877804819444e-51,
  };

  static const double zero = 0.0, one = 1.0,
                       two24 = 1.67772160000000000000e+07,
                       twon24 = 5.96046447753906250000e-08;

  std::int32_t jz, jx, jv, jp, jk, carry, n, iq[20], i, j, k, m, q0, ih;
  double z, fw, f[20], fq[20] = {}, q[20];

  jk = init_jk[prec];
  jp = jk;

  jx = nx - 1;
  jv = (e0 - 3) / 24;
  if (jv < 0) jv = 0;
  q0 = e0 - 24 * (jv + 1);

  j = jv - jx;
  m = jx + jk;
  for (i = 0; i <= m; i++, j++) {
    f[i] = (j < 0) ? zero : static_cast<double>(ipio2[j]);
  }

  for (i = 0; i <= jk; i++) {
    for (j = 0, fw = 0.0; j <= jx; j++) fw += x[j] * f[jx + i - j];
    q[i] = fw;
  }

  jz = jk;
recompute:
  for (i = 0, j = jz, z = q[jz]; j > 0; i++, j--) {
    fw = static_cast<double>(static_cast<std::int32_t>(twon24 * z));
    iq[i] = static_cast<std::int32_t>(z - two24 * fw);
    z = q[j - 1] + fw;
  }

  z = std::scalbn(z, q0);
  z -= 8.0 * std::floor(z * 0.125);
  n = static_cast<std::int32_t>(z);
  z -= static_cast<double>(n);
  ih = 0;
  if (q0 > 0) {
    i = (iq[jz - 1] >> (24 - q0));
    n += i;
    iq[jz - 1] -= i << (24 - q0);
    ih = iq[jz - 1] >> (23 - q0);
  } else if (q0 == 0) {
    ih = iq[jz - 1] >> 23;
  } else if (z >= 0.5) {
    ih = 2;
  }

  if (ih > 0) {
    n += 1;
    carry = 0;
    for (i = 0; i < jz; i++) {
      j = iq[i];
      if (carry == 0) {
        if (j != 0) {
          carry = 1;
          iq[i] = 0x1000000 - j;
        }
      } else {
        iq[i] = 0xffffff - j;
      }
    }
    if (q0 > 0) {
      switch (q0) {
        case 1:
          iq[jz - 1] &= 0x7fffff;
          break;
        case 2:
          iq[jz - 1] &= 0x3fffff;
          break;
        default:
          break;
      }
    }
    if (ih == 2) {
      z = one - z;
      if (carry != 0) z -= std::scalbn(one, q0);
    }
  }

  if (z == zero) {
    j = 0;
    for (i = jz - 1; i >= jk; i--) j |= iq[i];
    if (j == 0) {
      for (k = 1; jk >= k && iq[jk - k] == 0; k++) {
      }

      for (i = jz + 1; i <= jz + k; i++) {
        f[jx + i] = static_cast<double>(ipio2[jv + i]);
        for (j = 0, fw = 0.0; j <= jx; j++) fw += x[j] * f[jx + i - j];
        q[i] = fw;
      }
      jz += k;
      goto recompute;
    }
  }

  if (z == 0.0) {
    jz -= 1;
    q0 -= 24;
    while (iq[jz] == 0) {
      jz--;
      q0 -= 24;
    }
  } else {
    z = std::scalbn(z, -q0);
    if (z >= two24) {
      fw = static_cast<double>(static_cast<std::int32_t>(twon24 * z));
      iq[jz] = static_cast<std::int32_t>(z - two24 * fw);
      jz += 1;
      q0 += 24;
      iq[jz] = static_cast<std::int32_t>(fw);
    } else {
      iq[jz] = static_cast<std::int32_t>(z);
    }
  }

  fw = std::scalbn(one, q0);
  for (i = jz; i >= 0; i--) {
    q[i] = fw * static_cast<double>(iq[i]);
    fw *= twon24;
  }

  for (i = jz; i >= 0; i--) {
    for (fw = 0.0, k = 0; k <= jp && k <= jz - i; k++) fw += PIo2[k] * q[i + k];
    fq[jz - i] = fw;
  }

  switch (prec) {
    case 0:
      fw = 0.0;
      for (i = jz; i >= 0; i--) fw += fq[i];
      y[0] = (ih == 0) ? fw : -fw;
      break;
    case 1:
    case 2:
      fw = 0.0;
      for (i = jz; i >= 0; i--) fw += fq[i];
      y[0] = (ih == 0) ? fw : -fw;
      fw = fq[0] - fw;
      for (i = 1; i <= jz; i++) fw += fq[i];
      y[1] = (ih == 0) ? fw : -fw;
      break;
    case 3:
    default:
      for (i = jz; i > 0; i--) {
        fw = fq[i - 1] + fq[i];
        fq[i] += fq[i - 1] - fw;
        fq[i - 1] = fw;
      }
      for (i = jz; i > 1; i--) {
        fw = fq[i - 1] + fq[i];
        fq[i] += fq[i - 1] - fw;
        fq[i - 1] = fw;
      }
      for (fw = 0.0, i = jz; i >= 2; i--) fw += fq[i];
      if (ih == 0) {
        y[0] = fq[0];
        y[1] = fq[1];
        y[2] = fw;
      } else {
        y[0] = -fq[0];
        y[1] = -fq[1];
        y[2] = -fw;
      }
  }
  return n & 7;
}

std::int32_t ieee754_rem_pio2(double x, double* y) {
  static const std::int32_t two_over_pi[] = {
      0xA2F983, 0x6E4E44, 0x1529FC, 0x2757D1, 0xF534DD, 0xC0DB62, 0x95993C,
      0x439041, 0xFE5163, 0xABDEBB, 0xC561B7, 0x246E3A, 0x424DD2, 0xE00649,
      0x2EEA09, 0xD1921C, 0xFE1DEB, 0x1CB129, 0xA73EE8, 0x8235F5, 0x2EBB44,
      0x84E99C, 0x7026B4, 0x5F7E41, 0x3991D6, 0x398353, 0x39F49C, 0x845F8B,
      0xBDF928, 0x3B1FF8, 0x97FFDE, 0x05980F, 0xEF2F11, 0x8B5A0A, 0x6D1F6D,
      0x367ECF, 0x27CB09, 0xB74F46, 0x3F669E, 0x5FEA2D, 0x7527BA, 0xC7EBE5,
      0xF17B3D, 0x0739F7, 0x8A5292, 0xEA6BFB, 0x5FB11F, 0x8D5D08, 0x560330,
      0x46FC7B, 0x6BABF0, 0xCFBC20, 0x9AF436, 0x1DA9E3, 0x91615E, 0xE61B08,
      0x659985, 0x5F14A0, 0x68408D, 0xFFD880, 0x4D7327, 0x310606, 0x1556CA,
      0x73A8C9, 0x60E27B, 0xC08C6B,
  };

  static const std::int32_t npio2_hw[] = {
      0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C,
      0x4025FDBB, 0x402921FB, 0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C,
      0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB, 0x403AB41B, 0x403C463A,
      0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
      0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB,
      0x404858EB, 0x404921FB,
  };

  static const double zero = 0.0, half = 0.5, two24 = 1.67772160000000000000e+07,
                       invpio2 = 6.36619772367581382433e-01,
                       pio2_1 = 1.57079632673412561417e+00,
                       pio2_1t = 6.07710050650619224932e-11,
                       pio2_2 = 6.07710050630396597660e-11,
                       pio2_2t = 2.02226624879595063154e-21,
                       pio2_3 = 2.02226624871116645580e-21,
                       pio2_3t = 8.47842766036889956997e-32;

  double z, w, t, r, fn;
  double tx[3];
  std::int32_t e0, i, j, nx, n, ix, hx;
  std::uint32_t low;

  z = 0;
  hx = static_cast<std::int32_t>(hi_word(x));
  ix = hx & 0x7fffffff;
  if (ix <= 0x3fe921fb) { /* |x| ~<= pi/4 , no need for reduction */
    y[0] = x;
    y[1] = 0;
    return 0;
  }
  if (ix < 0x4002d97c) { /* |x| < 3pi/4, special case with n=+-1 */
    if (hx > 0) {
      z = x - pio2_1;
      if (ix != 0x3ff921fb) {
        y[0] = z - pio2_1t;
        y[1] = (z - y[0]) - pio2_1t;
      } else {
        z -= pio2_2;
        y[0] = z - pio2_2t;
        y[1] = (z - y[0]) - pio2_2t;
      }
      return 1;
    } else {
      z = x + pio2_1;
      if (ix != 0x3ff921fb) {
        y[0] = z + pio2_1t;
        y[1] = (z - y[0]) + pio2_1t;
      } else {
        z += pio2_2;
        y[0] = z + pio2_2t;
        y[1] = (z - y[0]) + pio2_2t;
      }
      return -1;
    }
  }
  if (ix <= 0x413921fb) { /* |x| ~<= 2^19*(pi/2), medium size */
    t = std::fabs(x);
    n = static_cast<std::int32_t>(t * invpio2 + half);
    fn = static_cast<double>(n);
    r = t - fn * pio2_1;
    w = fn * pio2_1t;
    if (n < 32 && ix != npio2_hw[n - 1]) {
      y[0] = r - w;
    } else {
      std::uint32_t high;
      j = ix >> 20;
      y[0] = r - w;
      high = hi_word(y[0]);
      i = j - static_cast<std::int32_t>((high >> 20) & 0x7ffu);
      if (i > 16) {
        t = r;
        w = fn * pio2_2;
        r = t - w;
        w = fn * pio2_2t - ((t - r) - w);
        y[0] = r - w;
        high = hi_word(y[0]);
        i = j - static_cast<std::int32_t>((high >> 20) & 0x7ffu);
        if (i > 49) {
          t = r;
          w = fn * pio2_3;
          r = t - w;
          w = fn * pio2_3t - ((t - r) - w);
          y[0] = r - w;
        }
      }
    }
    y[1] = (r - y[0]) - w;
    if (hx < 0) {
      y[0] = -y[0];
      y[1] = -y[1];
      return -n;
    } else {
      return n;
    }
  }
  /* all other (large) arguments */
  if (ix >= 0x7ff00000) {
    y[0] = y[1] = x - x;
    return 0;
  }
  low = lo_word(x);
  set_low_word(z, low);
  e0 = (ix >> 20) - 1046;
  set_high_word(z, static_cast<std::uint32_t>(
                        ix - static_cast<std::int32_t>(
                                  static_cast<std::uint32_t>(e0) << 20)));
  for (i = 0; i < 2; i++) {
    tx[i] = static_cast<double>(static_cast<std::int32_t>(z));
    z = (z - tx[i]) * two24;
  }
  tx[2] = z;
  nx = 3;
  while (tx[nx - 1] == zero) nx--;
  n = kernel_rem_pio2(tx, y, e0, nx, 2, two_over_pi);
  if (hx < 0) {
    y[0] = -y[0];
    y[1] = -y[1];
    return -n;
  }
  return n;
}

double kernel_cos(double x, double y) {
  static const double one = 1.00000000000000000000e+00,
                       C1 = 4.16666666666666019037e-02,
                       C2 = -1.38888888888741095749e-03,
                       C3 = 2.48015872894767294178e-05,
                       C4 = -2.75573143513906633035e-07,
                       C5 = 2.08757232129817482790e-09,
                       C6 = -1.13596475577881948265e-11;

  double a, iz, z, r, qx = 0.0;
  std::int32_t ix;
  ix = static_cast<std::int32_t>(hi_word(x));
  ix &= 0x7fffffff;
  if (ix < 0x3e400000) {
    if (static_cast<int>(x) == 0) return one;
  }
  z = x * x;
  r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))));
  if (ix < 0x3fd33333) {
    return one - (0.5 * z - (z * r - x * y));
  } else {
    if (ix > 0x3fe90000) {
      qx = 0.28125;
    } else {
      qx = insert_words(static_cast<std::uint32_t>(ix - 0x00200000), 0);
    }
    iz = 0.5 * z - qx;
    a = one - qx;
    return a - (iz - (z * r - x * y));
  }
}

double kernel_sin(double x, double y, int iy) {
  static const double half = 5.00000000000000000000e-01,
                       S1 = -1.66666666666666324348e-01,
                       S2 = 8.33333333332248946124e-03,
                       S3 = -1.98412698298579493134e-04,
                       S4 = 2.75573137070700676789e-06,
                       S5 = -2.50507602534068634195e-08,
                       S6 = 1.58969099521155010221e-10;

  double z, r, v;
  std::int32_t ix;
  ix = static_cast<std::int32_t>(hi_word(x));
  ix &= 0x7fffffff;
  if (ix < 0x3e400000) {
    if (static_cast<int>(x) == 0) return x;
  }
  z = x * x;
  v = z * x;
  r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)));
  if (iy == 0) {
    return x + v * (S1 + z * r);
  } else {
    return x - ((z * (half * y - v * r) - y) - v * S1);
  }
}

// The shared r/v/s polynomial combination __kernel_tan needs, factored into
// its own never-inlined function. This is NOT an algorithmic change --
// compare byte-for-byte with the two lines this replaces inside
// __kernel_tan below, textually identical, zero explicit std::fma. It
// exists because of a measured, reproducible compiler fact, not a
// portability shortcut: with these two lines inlined directly into
// kernel_tan (as fdlibm.cpp originally had them), the exact same source
// compiles to DIFFERENT machine code depending on surrounding code shape
// -- clang's -ffp-contract=fast auto-fusion heuristic for these
// multiply-adds is sensitive to register pressure/scheduling context from
// the rest of kernel_tan's body, and that context-dependence is exactly
// why this port measured a residual 304/2,000,000 (0.015%) divergence
// from V8's Math.tan even though every other fdlibm-derived function in
// this file reaches 0/2,000,000 under the same -ffp-contract=fast.
// Isolating the expression in its own `noinline` function removes that
// context-dependence: compiled on its own, with no other live variables
// competing for registers, clang's heuristic makes one fixed choice
// regardless of the caller, and that choice reproduces V8's arm64 AND
// x86-64 binaries exactly (verified: 0/2,000,000 on both architectures,
// at both -O2 and -O3, see docs/port-engineering/v8-math/v8-math-report.md
// section on tan). tests/test_fdlibm_contract_pin.cpp pins several of the
// specific inputs that were divergent before this change, specifically so
// a future refactor that re-inlines this (or a compiler upgrade that
// changes the isolated function's own codegen) fails loudly instead of
// silently reintroducing the residual.
__attribute__((noinline)) double kernel_tan_combine(double y, double z,
                                                      double s, double r,
                                                      double v, double T0) {
  double result = y + z * (s * (r + v) + y);
  result += T0 * s;
  return result;
}

// ============================================================
// __kernel_tan(x, y, iy): tangent on [-pi/4, pi/4] (plus the low-order
// correction y and the "which half" flag iy), exactly as
// v8_ieee754_reference.cc's __kernel_tan.
// ============================================================
double kernel_tan(double x, double y, int iy) {
  static const double T[] = {
      3.33333333333334091986e-01,  1.33333333333201242699e-01,
      5.39682539762260521377e-02,  2.18694882948595424599e-02,
      8.86323982359930005737e-03,  3.59207910759131235356e-03,
      1.45620945432529025516e-03,  5.88041240820264096874e-04,
      2.46463134818469906812e-04,  7.81794442939557092300e-05,
      7.14072491382608190305e-05,  -1.85586374855275456654e-05,
      2.59073051863633712884e-05,  1.00000000000000000000e+00,
      7.85398163397448278999e-01,  3.06161699786838301793e-17,
  };
  static const double& one = T[13];
  static const double& pio4 = T[14];
  static const double& pio4lo = T[15];

  double z, r, v, w, s;
  std::int32_t ix, hx;

  hx = static_cast<std::int32_t>(hi_word(x));
  ix = hx & 0x7fffffff;
  if (ix < 0x3e300000) {
    if (static_cast<int>(x) == 0) {
      std::uint32_t low = lo_word(x);
      if (((static_cast<std::uint32_t>(ix) | low) | static_cast<std::uint32_t>(iy + 1)) == 0) {
        return one / std::fabs(x);
      } else {
        if (iy == 1) {
          return x;
        } else {
          double a, t;
          z = w = x + y;
          set_low_word(z, 0);
          v = y - (z - x);
          t = a = -one / w;
          set_low_word(t, 0);
          s = one + t * z;
          return t + a * (s + t * v);
        }
      }
    }
  }
  if (ix >= 0x3fe59428) {
    if (hx < 0) {
      x = -x;
      y = -y;
    }
    z = pio4 - x;
    w = pio4lo - y;
    x = z + w;
    y = 0.0;
  }
  z = x * x;
  w = z * z;
  r = T[1] + w * (T[3] + w * (T[5] + w * (T[7] + w * (T[9] + w * T[11]))));
  v = z * (T[2] + w * (T[4] + w * (T[6] + w * (T[8] + w * (T[10] + w * T[12])))));
  s = z * x;
  r = kernel_tan_combine(y, z, s, r, v, T[0]);
  w = x + r;
  if (ix >= 0x3fe59428) {
    v = iy;
    return (1 - ((hx >> 30) & 2)) * (v - 2.0 * (x - (w * w / (w + v) - r)));
  }
  if (iy == 1) {
    return w;
  } else {
    double a, t;
    z = w;
    set_low_word(z, 0);
    v = r - (z - x);
    t = a = -1.0 / w;
    set_low_word(t, 0);
    s = 1.0 + t * z;
    return t + a * (s + t * v);
  }
}

// ============================================================
// asin(x) / acos(x): shared R(z) rational-polynomial kernel, exactly as
// v8_ieee754_reference.cc.
// ============================================================
double fd_asin(double x) {
  static const double one = 1.00000000000000000000e+00,
                       huge = 1.000e+300,
                       pio2_hi = 1.57079632679489655800e+00,
                       pio2_lo = 6.12323399573676603587e-17,
                       pio4_hi = 7.85398163397448278999e-01,
                       pS0 = 1.66666666666666657415e-01,
                       pS1 = -3.25565818622400915405e-01,
                       pS2 = 2.01212532134862925881e-01,
                       pS3 = -4.00555345006794114027e-02,
                       pS4 = 7.91534994289814532176e-04,
                       pS5 = 3.47933107596021167570e-05,
                       qS1 = -2.40339491173441421878e+00,
                       qS2 = 2.02094576023350569471e+00,
                       qS3 = -6.88283971605453293030e-01,
                       qS4 = 7.70381505559019352791e-02;

  double t, w, p, q, c, r, s;
  std::int32_t hx, ix;

  t = 0;
  hx = static_cast<std::int32_t>(hi_word(x));
  ix = hx & 0x7fffffff;
  if (ix >= 0x3ff00000) {
    std::uint32_t lx = lo_word(x);
    if (((static_cast<std::uint32_t>(ix) - 0x3ff00000u) | lx) == 0) {
      return x * pio2_hi + x * pio2_lo;
    }
    return std::numeric_limits<double>::signaling_NaN();
  } else if (ix < 0x3fe00000) {
    if (ix < 0x3e400000) {
      if (huge + x > one) return x;
    } else {
      t = x * x;
    }
    p = t * (pS0 + t * (pS1 + t * (pS2 + t * (pS3 + t * (pS4 + t * pS5)))));
    q = one + t * (qS1 + t * (qS2 + t * (qS3 + t * qS4)));
    w = p / q;
    return x + x * w;
  }
  w = one - std::fabs(x);
  t = w * 0.5;
  p = t * (pS0 + t * (pS1 + t * (pS2 + t * (pS3 + t * (pS4 + t * pS5)))));
  q = one + t * (qS1 + t * (qS2 + t * (qS3 + t * qS4)));
  s = std::sqrt(t);
  if (ix >= 0x3fef3333) {
    w = p / q;
    t = pio2_hi - (2.0 * (s + s * w) - pio2_lo);
  } else {
    w = s;
    set_low_word(w, 0);
    c = (t - w * w) / (s + w);
    r = p / q;
    p = 2.0 * s * r - (pio2_lo - 2.0 * c);
    q = pio4_hi - 2.0 * w;
    t = pio4_hi - (p - q);
  }
  if (hx > 0)
    return t;
  else
    return -t;
}

double fd_acos(double x) {
  static const double one = 1.00000000000000000000e+00,
                       pi = 3.14159265358979311600e+00,
                       pio2_hi = 1.57079632679489655800e+00,
                       pio2_lo = 6.12323399573676603587e-17,
                       pS0 = 1.66666666666666657415e-01,
                       pS1 = -3.25565818622400915405e-01,
                       pS2 = 2.01212532134862925881e-01,
                       pS3 = -4.00555345006794114027e-02,
                       pS4 = 7.91534994289814532176e-04,
                       pS5 = 3.47933107596021167570e-05,
                       qS1 = -2.40339491173441421878e+00,
                       qS2 = 2.02094576023350569471e+00,
                       qS3 = -6.88283971605453293030e-01,
                       qS4 = 7.70381505559019352791e-02;

  double z, p, q, r, w, s, c, df;
  std::int32_t hx, ix;
  hx = static_cast<std::int32_t>(hi_word(x));
  ix = hx & 0x7fffffff;
  if (ix >= 0x3ff00000) {
    std::uint32_t lx = lo_word(x);
    if (((static_cast<std::uint32_t>(ix) - 0x3ff00000u) | lx) == 0) {
      if (hx > 0)
        return 0.0;
      else
        return pi + 2.0 * pio2_lo;
    }
    return std::numeric_limits<double>::signaling_NaN();
  }
  if (ix < 0x3fe00000) {
    if (ix <= 0x3c600000) return pio2_hi + pio2_lo;
    z = x * x;
    p = z * (pS0 + z * (pS1 + z * (pS2 + z * (pS3 + z * (pS4 + z * pS5)))));
    q = one + z * (qS1 + z * (qS2 + z * (qS3 + z * qS4)));
    r = p / q;
    return pio2_hi - (x - (pio2_lo - x * r));
  } else if (hx < 0) {
    z = (one + x) * 0.5;
    p = z * (pS0 + z * (pS1 + z * (pS2 + z * (pS3 + z * (pS4 + z * pS5)))));
    q = one + z * (qS1 + z * (qS2 + z * (qS3 + z * qS4)));
    s = std::sqrt(z);
    r = p / q;
    w = r * s - pio2_lo;
    return pi - 2.0 * (s + w);
  } else {
    z = (one - x) * 0.5;
    s = std::sqrt(z);
    df = s;
    set_low_word(df, 0);
    c = (z - df * df) / (s + df);
    p = z * (pS0 + z * (pS1 + z * (pS2 + z * (pS3 + z * (pS4 + z * pS5)))));
    q = one + z * (qS1 + z * (qS2 + z * (qS3 + z * qS4)));
    r = p / q;
    w = r * s + c;
    return 2.0 * (df + w);
  }
}

// ============================================================
// atan(x)
// ============================================================
double fd_atan(double x) {
  static const double atanhi[] = {
      4.63647609000806093515e-01,
      7.85398163397448278999e-01,
      9.82793723247329054082e-01,
      1.57079632679489655800e+00,
  };
  static const double atanlo[] = {
      2.26987774529616870924e-17,
      3.06161699786838301793e-17,
      1.39033110312309984516e-17,
      6.12323399573676603587e-17,
  };
  static const double aT[] = {
      3.33333333333329318027e-01,  -1.99999999998764832476e-01,
      1.42857142725034663711e-01,  -1.11111104054623557880e-01,
      9.09088713343650656196e-02,  -7.69187620504482999495e-02,
      6.66107313738753120669e-02,  -5.83357013379057348645e-02,
      4.97687799461593236017e-02,  -3.65315727442169155270e-02,
      1.62858201153657823623e-02,
  };
  static const double one = 1.0, huge = 1.0e300;

  double w, s1, s2, z;
  std::int32_t ix, hx, id;

  hx = static_cast<std::int32_t>(hi_word(x));
  ix = hx & 0x7fffffff;
  if (ix >= 0x44100000) {
    std::uint32_t low = lo_word(x);
    if (ix > 0x7ff00000 || (ix == 0x7ff00000 && (low != 0))) return x + x;
    if (hx > 0)
      return atanhi[3] + atanlo[3];
    else
      return -atanhi[3] - atanlo[3];
  }
  if (ix < 0x3fdc0000) {
    if (ix < 0x3e400000) {
      if (huge + x > one) return x;
    }
    id = -1;
  } else {
    x = std::fabs(x);
    if (ix < 0x3ff30000) {
      if (ix < 0x3fe60000) {
        id = 0;
        x = (2.0 * x - one) / (2.0 + x);
      } else {
        id = 1;
        x = (x - one) / (x + one);
      }
    } else {
      if (ix < 0x40038000) {
        id = 2;
        x = (x - 1.5) / (one + 1.5 * x);
      } else {
        id = 3;
        x = -1.0 / x;
      }
    }
  }
  z = x * x;
  w = z * z;
  s1 = z * (aT[0] +
            w * (aT[2] + w * (aT[4] + w * (aT[6] + w * (aT[8] + w * aT[10])))));
  s2 = w * (aT[1] + w * (aT[3] + w * (aT[5] + w * (aT[7] + w * aT[9]))));
  if (id < 0) {
    return x - x * (s1 + s2);
  } else {
    z = atanhi[id] - ((x * (s1 + s2) - atanlo[id]) - x);
    return (hx < 0) ? -z : z;
  }
}

// ============================================================
// atan2(y, x)
//
// Classification pre-checks below (isnan/isinf/==0.0/==1.0/signbit) are a
// behavior-preserving restatement of V8's raw-bit-pattern tests (which use
// NegateWithWraparound/SubWithWraparound purely to dodge C89-era
// signed-overflow UB around the sign/NaN/zero classification, not to
// affect any rounded result) -- verified equivalent by hand, one branch at
// a time, against v8_ieee754_reference.cc. The numeric formula itself (the
// k=(iy-ix)>>20 magnitude threshold, the atan(fabs(y/x)) call, and the
// pi/pi_lo combination in the final switch) is untouched and still keyed
// off the exact exponent words via hi_word(), because THAT is what
// determines the output bits.
// ============================================================
double fd_atan2(double y, double x) {
  static const double zero = 0.0,
                       pi_o_4 = 7.8539816339744827900e-01,
                       pi_o_2 = 1.5707963267948965580e+00,
                       pi = 3.1415926535897931160e+00;
  static const volatile double pi_lo = 1.2246467991473531772e-16;
  static const volatile double tiny = 1.0e-300;

  if (std::isnan(x) || std::isnan(y)) return x + y;

  if (x == 1.0) return fd_atan(y);

  const std::int32_t hx = static_cast<std::int32_t>(hi_word(x));
  const std::int32_t ix = static_cast<std::int32_t>(hi_word(x) & 0x7fffffffu);
  const std::int32_t iy = static_cast<std::int32_t>(hi_word(y) & 0x7fffffffu);
  int m = (std::signbit(y) ? 1 : 0) | (std::signbit(x) ? 2 : 0);

  if (y == 0.0) {
    switch (m) {
      case 0:
      case 1:
        return y;
      case 2:
        return pi + tiny;
      default:
        return -pi - tiny;
    }
  }
  if (x == 0.0) return std::signbit(y) ? -pi_o_2 - tiny : pi_o_2 + tiny;

  if (std::isinf(x)) {
    if (std::isinf(y)) {
      switch (m) {
        case 0:
          return pi_o_4 + tiny;
        case 1:
          return -pi_o_4 - tiny;
        case 2:
          return 3.0 * pi_o_4 + tiny;
        default:
          return -3.0 * pi_o_4 - tiny;
      }
    } else {
      switch (m) {
        case 0:
          return zero;
        case 1:
          return -zero;
        case 2:
          return pi + tiny;
        default:
          return -pi - tiny;
      }
    }
  }
  if (std::isinf(y)) return std::signbit(y) ? -pi_o_2 - tiny : pi_o_2 + tiny;

  double z;
  const std::int32_t k = (iy - ix) >> 20;
  if (k > 60) {
    z = pi_o_2 + 0.5 * pi_lo;
    // |y/x| > 2**60: x's sign is numerically irrelevant at this ratio, so
    // fdlibm forces the case-2/3 pi-combination branches off entirely
    // here (this line was dropped in an earlier draft of this port and
    // is exactly what the differential harness caught: dropping it made
    // ~10% of adversarial atan2 pairs 1 ULP off, not a rounding-mode
    // artifact at all).
    m &= 1;
  } else if (hx < 0 && k < -60) {
    z = 0.0;
  } else {
    z = fd_atan(std::fabs(y / x));
  }
  switch (m) {
    case 0:
      return z;
    case 1:
      return -z;
    case 2:
      return pi - (z - pi_lo);
    default:
      return (z - pi_lo) - pi;
  }
}

// log2() is NOT defined in this TU -- see src/fdlibm_log2.cpp. Its
// combined-precision Dekker-style summation (val_hi/val_lo/w below) is
// actively BROKEN by FMA contraction (verified: 0/50000 divergent from V8
// under -ffp-contract=off, but 108/50000 under -ffp-contract=fast, the
// opposite direction from every other function in this file), so it
// cannot share this TU's -ffp-contract=fast override. See that file's
// header comment and docs/port-engineering/v8-math/v8-math-report.md.

// The two combining expressions fd_log's k!=0 branches need, each factored
// into its own never-inlined function -- same rationale and technique as
// kernel_tan_combine below: the identical source, inlined directly inside
// fd_log (as this file originally had it), measurably diverges from V8 on
// arm64 under this file's -ffp-contract=fast (2/50,000 residual at that
// scale; see docs/port-engineering/v8-math/v8-math-report.md).
//
// An earlier version of this fix used an explicit std::fma() at each site
// instead of a noinline extraction, and that reached 0/2,000,000 on arm64
// -- but REGRESSED x86-64 to 180/2,000,000 divergent, because std::fma()
// unconditionally fuses on every architecture, while V8's own x86-64
// binary does not fuse this expression at all (the x86-64 baseline this
// project targets has no hardware fused-multiply-add for
// -ffp-contract=fast to select, so V8's own ieee754.cc build stays
// unfused there). Isolating the plain, unfused expression in its own
// noinline function instead lets ordinary -ffp-contract=fast auto-fusion
// decide per architecture -- fusing on arm64 (matching V8's arm64
// binary), staying unfused on x86-64 baseline (matching V8's x86-64
// binary) -- with no explicit std::fma anywhere. Verified 0/2,000,000 on
// both arm64 and x86-64.
__attribute__((noinline)) double log_combine_a(double s, double hfsq,
                                                 double r, double dk,
                                                 double ln2_lo) {
  return s * (hfsq + r) + dk * ln2_lo;
}
__attribute__((noinline)) double log_combine_b(double s, double f, double r,
                                                 double dk, double ln2_lo) {
  return s * (f - r) - dk * ln2_lo;
}

// ============================================================
// log(x): natural logarithm.
//
// Method: argument reduction to x = 2^k*(1+f), sqrt(2)/2 < 1+f < sqrt(2);
// degree-14 Remez polynomial approximation of log(1+f). See
// v8_ieee754_reference.cc's method comment (reproduced verbatim above the
// V8 `log` definition) for the full derivation; this is a line-for-line
// transcription, constants and branch structure unchanged.
// ============================================================
double fd_log(double x) {
  static const double ln2_hi = 6.93147180369123816490e-01,
                       ln2_lo = 1.90821492927058770002e-10,
                       two54 = 1.80143985094819840000e+16,
                       Lg1 = 6.666666666666735130e-01,
                       Lg2 = 3.999999999940941908e-01,
                       Lg3 = 2.857142874366239149e-01,
                       Lg4 = 2.222219843214978396e-01,
                       Lg5 = 1.818357216161805012e-01,
                       Lg6 = 1.531383769920937332e-01,
                       Lg7 = 1.479819860511658591e-01;

  static const double zero = 0.0;

  double hfsq, f, s, z, r, w, t1, t2, dk;
  std::int32_t k, hx, i, j;
  std::uint32_t lx;

  hx = static_cast<std::int32_t>(hi_word(x));
  lx = lo_word(x);

  k = 0;
  if (hx < 0x00100000) { /* x < 2**-1022  */
    if (((static_cast<std::uint32_t>(hx) & 0x7fffffffu) | lx) == 0) {
      return -std::numeric_limits<double>::infinity(); /* log(+-0)=-inf */
    }
    if (hx < 0) {
      return std::numeric_limits<double>::signaling_NaN(); /* log(-#) = NaN */
    }
    k -= 54;
    x *= two54; /* subnormal number, scale up x */
    hx = static_cast<std::int32_t>(hi_word(x));
  }
  if (hx >= 0x7ff00000) return x + x;
  k += (hx >> 20) - 1023;
  hx &= 0x000fffff;
  i = (hx + 0x95f64) & 0x100000;
  set_high_word(x, static_cast<std::uint32_t>(hx | (i ^ 0x3ff00000))); /* normalize x or x/2 */
  k += (i >> 20);
  f = x - 1.0;
  if ((0x000fffff & (2 + hx)) < 3) { /* -2**-20 <= f < 2**-20 */
    if (f == zero) {
      if (k == 0) {
        return zero;
      } else {
        dk = static_cast<double>(k);
        return dk * ln2_hi + dk * ln2_lo;
      }
    }
    r = f * f * (0.5 - 0.33333333333333333 * f);
    if (k == 0) {
      return f - r;
    } else {
      dk = static_cast<double>(k);
      return dk * ln2_hi - ((r - dk * ln2_lo) - f);
    }
  }
  s = f / (2.0 + f);
  dk = static_cast<double>(k);
  z = s * s;
  i = hx - 0x6147a;
  w = z * z;
  j = 0x6b851 - hx;
  t1 = w * (Lg2 + w * (Lg4 + w * Lg6));
  t2 = z * (Lg1 + w * (Lg3 + w * (Lg5 + w * Lg7)));
  i |= j;
  r = t2 + t1;
  if (i > 0) {
    hfsq = 0.5 * f * f;
    if (k == 0)
      return f - (hfsq - s * (hfsq + r));
    else
      return dk * ln2_hi - ((hfsq - log_combine_a(s, hfsq, r, dk, ln2_lo)) - f);
  } else {
    if (k == 0)
      return f - s * (f - r);
    else
      return dk * ln2_hi - (log_combine_b(s, f, r, dk, ln2_lo) - f);
  }
}

}  // namespace

// ============================================================
// tanh(x)
// ============================================================
double tanh(double x) noexcept {
  static const volatile double tiny = 1.0e-300;
  static const double one = 1.0, two = 2.0, huge = 1.0e300;
  double t, z;
  std::int32_t jx, ix;

  jx = static_cast<std::int32_t>(hi_word(x));
  ix = jx & 0x7fffffff;

  if (ix >= 0x7ff00000) {
    if (jx >= 0)
      return one / x + one;
    else
      return one / x - one;
  }

  if (ix < 0x40360000) {
    if (ix < 0x3e300000) {
      if (huge + x > one) return x;
    }
    if (ix >= 0x3ff00000) {
      t = fd_expm1(two * std::fabs(x));
      z = one - two / (t + two);
    } else {
      t = fd_expm1(-two * std::fabs(x));
      z = -t / (t + two);
    }
  } else {
    z = one - tiny;
  }
  return (jx >= 0) ? z : -z;
}

double expm1(double x) noexcept { return fd_expm1(x); }

double exp(double x) noexcept { return fd_exp(x); }

double sin(double x) noexcept {
  double y[2], z = 0.0;
  std::int32_t n, ix;

  ix = static_cast<std::int32_t>(hi_word(x));
  ix &= 0x7fffffff;
  if (ix <= 0x3fe921fb) {
    return kernel_sin(x, z, 0);
  } else if (ix >= 0x7ff00000) {
    return x - x;
  } else {
    n = ieee754_rem_pio2(x, y);
    switch (n & 3) {
      case 0:
        return kernel_sin(y[0], y[1], 1);
      case 1:
        return kernel_cos(y[0], y[1]);
      case 2:
        return -kernel_sin(y[0], y[1], 1);
      default:
        return -kernel_cos(y[0], y[1]);
    }
  }
}

double cos(double x) noexcept {
  double y[2], z = 0.0;
  std::int32_t n, ix;

  ix = static_cast<std::int32_t>(hi_word(x));
  ix &= 0x7fffffff;
  if (ix <= 0x3fe921fb) {
    return kernel_cos(x, z);
  } else if (ix >= 0x7ff00000) {
    return x - x;
  } else {
    n = ieee754_rem_pio2(x, y);
    switch (n & 3) {
      case 0:
        return kernel_cos(y[0], y[1]);
      case 1:
        return -kernel_sin(y[0], y[1], 1);
      case 2:
        return -kernel_cos(y[0], y[1]);
      default:
        return kernel_sin(y[0], y[1], 1);
    }
  }
}

double log(double x) noexcept { return fd_log(x); }
// log2() lives in src/fdlibm_log2.cpp, compiled without this TU's
// -ffp-contract=fast override -- see the comment above where k_log1p/
// fd_log2 used to live in this file, and fdlibm_log2.cpp's header.
double tan(double x) noexcept {
  double y[2], z = 0.0;
  std::int32_t n, ix;

  ix = static_cast<std::int32_t>(hi_word(x));
  ix &= 0x7fffffff;
  if (ix <= 0x3fe921fb) {
    return kernel_tan(x, z, 1);
  } else if (ix >= 0x7ff00000) {
    return x - x;
  } else {
    n = ieee754_rem_pio2(x, y);
    return kernel_tan(y[0], y[1], 1 - ((n & 1) << 1));
  }
}
double asin(double x) noexcept { return fd_asin(x); }
double acos(double x) noexcept { return fd_acos(x); }
double atan(double x) noexcept { return fd_atan(x); }
double atan2(double y, double x) noexcept { return fd_atan2(y, x); }

// ============================================================
// pow(x, y): V8's LIVE Math.pow (v8::internal::math::pow,
// src/numbers/ieee754.cc, active whenever `use_std_math_pow` is true --
// the default on every platform except AIX; confirmed active on this
// build both by reading the flag default and empirically, see fdlibm.hpp).
// NOT V8's retired base::ieee754::legacy::pow.
//
// The final `else` branch is a literal std::pow(x, y) call, on purpose:
// V8's own math::pow falls back to std::pow too, and since that resolves
// to the OS's shared libm symbol on both sides (this binary and the V8
// process it must match both dynamically link the same `pow` from the
// same OS on the same machine), no algorithm needs porting for that
// branch -- calling std::pow here IS calling exactly what V8 calls.
// ============================================================
double pow(double x, double y) noexcept {
  if (std::isnan(y)) {
    return std::numeric_limits<double>::quiet_NaN();
  }
  if (std::isinf(y) && (x == 1.0 || x == -1.0)) {
    return std::numeric_limits<double>::quiet_NaN();
  }
  // std::pow distinguishes signaling/quiet NaN; JS doesn't, and any NaN
  // canonicalizes to the same bit pattern once it crosses back into a JS
  // Number, so no explicit canonicalization of x is needed here.
  if (y == 2.0) {
    return x * x;
  } else if (y == 0.5) {
    if (std::isinf(x)) return std::numeric_limits<double>::infinity();
    return std::sqrt(x + 0.0);
  }
  return std::pow(x, y);
}

// hypot() (2/3/N-arg) lives in src/fdlibm_off.cpp -- Math.hypot is a
// Torque builtin lowered directly by V8's own JIT backend, unrelated to
// this TU's -ffp-contract=fast override, and measured to need the plain
// (unfused) formula. See fdlibm_off.cpp's header comment.

}  // namespace fdlibm
