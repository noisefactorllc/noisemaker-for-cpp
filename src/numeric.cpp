#include "noisemaker/numeric.hpp"

#include <bit>
#include <cmath>
#include <limits>

namespace noisemaker {

float f32(double value) noexcept {
  return static_cast<float>(value);
}

double glsl_mod(double x, double y) noexcept {
  return x - y * std::floor(x / y);
}

double glsl_round(double value) noexcept {
  const double lower = std::floor(value);
  double result = value - lower >= 0.5 ? lower + 1.0 : lower;
  if (result == 0.0 && std::signbit(value)) {
    result = -0.0;
  }
  return result;
}

std::uint32_t umul(std::uint32_t a, std::uint32_t b) noexcept {
  return a * b;
}

std::uint32_t hash_uint32(std::uint32_t value) noexcept {
  value ^= value >> 16U;
  value = umul(value, 0x7feb352dU);
  value ^= value >> 15U;
  value = umul(value, 0x846ca68bU);
  value ^= value >> 16U;
  return value;
}

std::array<std::uint32_t, 3> pcg3d(std::array<std::uint32_t, 3> value) noexcept {
  for (std::uint32_t& component : value) {
    component = umul(component, 1664525U) + 1013904223U;
  }
  value[0] += umul(value[1], value[2]);
  value[1] += umul(value[2], value[0]);
  value[2] += umul(value[0], value[1]);
  for (std::uint32_t& component : value) {
    component ^= component >> 16U;
  }
  value[0] += umul(value[1], value[2]);
  value[1] += umul(value[2], value[0]);
  value[2] += umul(value[0], value[1]);
  return value;
}

std::uint32_t float_bits_to_uint(float value) noexcept {
  return std::bit_cast<std::uint32_t>(value);
}

float uint_bits_to_float(std::uint32_t value) noexcept {
  return std::bit_cast<float>(value);
}

// Semantics-exact transcription of the JS CPU authority's `floatToHalf`
// (noisemaker-for-cpu/src/csl/glsl-runtime.js:61-81), which is what
// `packHalf2x16` calls there. This is NOT IEEE round-to-nearest-even: the
// authority adds 0x1000 unconditionally (round-half-UP, away from zero), it
// pre-truncates subnormals by shifting the restored significand before the
// same unconditional bias, and it returns the canonical positive quiet NaN
// 0x7e00 for every NaN regardless of sign. Bit-exact parity with the
// authority is the contract, so the authority's rule is the correct rule
// here; do not "correct" it toward IEEE ties-to-even. The name says `_js`
// precisely because it is not RTE.
std::uint16_t float_to_half_js(float value) noexcept {
  // if (Number.isNaN(value)) return 0x7e00
  if (std::isnan(value)) {
    return static_cast<std::uint16_t>(0x7e00U);
  }
  // if (value === Number.POSITIVE_INFINITY) return 0x7c00
  if (value == std::numeric_limits<float>::infinity()) {
    return static_cast<std::uint16_t>(0x7c00U);
  }
  // if (value === Number.NEGATIVE_INFINITY) return 0xfc00
  if (value == -std::numeric_limits<float>::infinity()) {
    return static_cast<std::uint16_t>(0xfc00U);
  }

  // const bits = new Uint32Array(new Float32Array([value]).buffer)[0]
  const std::uint32_t bits = float_bits_to_uint(value);
  // const sign = (bits >>> 16) & 0x8000
  const std::uint32_t sign = (bits >> 16U) & 0x8000U;
  // let exponent = ((bits >>> 23) & 0xff) - 127 + 15
  std::int32_t exponent = static_cast<std::int32_t>((bits >> 23U) & 0xffU) - 127 + 15;
  // let fraction = bits & 0x7fffff
  std::uint32_t fraction = bits & 0x7fffffU;

  if (exponent <= 0) {
    // if (exponent < -10) return sign
    if (exponent < -10) {
      return static_cast<std::uint16_t>(sign);
    }
    // fraction = (fraction | 0x800000) >>> (1 - exponent)
    fraction = (fraction | 0x800000U) >> static_cast<unsigned>(1 - exponent);
    // return sign | ((fraction + 0x1000) >>> 13)
    return static_cast<std::uint16_t>(sign | ((fraction + 0x1000U) >> 13U));
  }
  // if (exponent >= 31) return sign | 0x7c00
  if (exponent >= 31) {
    return static_cast<std::uint16_t>(sign | 0x7c00U);
  }
  // fraction += 0x1000
  fraction += 0x1000U;
  // if (fraction & 0x800000) { fraction = 0; exponent += 1; ... }
  if ((fraction & 0x800000U) != 0U) {
    fraction = 0U;
    exponent += 1;
    if (exponent >= 31) {
      return static_cast<std::uint16_t>(sign | 0x7c00U);
    }
  }
  // return sign | (exponent << 10) | (fraction >>> 13)
  return static_cast<std::uint16_t>(sign | (static_cast<std::uint32_t>(exponent) << 10U) |
                                    (fraction >> 13U));
}

// Semantics-exact transcription of the JS CPU authority's `halfToFloat`
// (noisemaker-for-cpu/src/csl/glsl-runtime.js:52-59), which is what
// `unpackHalf2x16` calls there (:420-425). The authority computes in double
// and the caller stores the result into the Float32Array that `alloc()` hands
// back (:120-124), so the observable value is the float32 narrowing of that
// double -- which is what `f32()` does here.
//
// The one behaviour that is easy to get wrong: EVERY half NaN code collapses
// to `Number.NaN`. Sign and payload are discarded, because the authority never
// looks at them on that branch. Preserving them (as an IEEE-minded
// implementation would) diverges on 2045 of the 65536 codes.
float half_to_float(std::uint16_t value) noexcept {
  // const sign = (value & 0x8000) ? -1 : 1
  const double sign = (value & 0x8000U) != 0U ? -1.0 : 1.0;
  // const exponent = (value >>> 10) & 0x1f
  const std::uint32_t exponent = (static_cast<std::uint32_t>(value) >> 10U) & 0x1fU;
  // const fraction = value & 0x3ff
  const std::uint32_t fraction = static_cast<std::uint32_t>(value) & 0x3ffU;

  // if (exponent === 0) return sign * Math.pow(2, -14) * (fraction / 1024)
  if (exponent == 0U) {
    return f32(sign * 0x1p-14 * (static_cast<double>(fraction) / 1024.0));
  }
  // if (exponent === 0x1f) return fraction ? Number.NaN : sign * Number.POSITIVE_INFINITY
  if (exponent == 0x1fU) {
    if (fraction != 0U) {
      // `Number.NaN` narrowed to float32 is 0x7fc00000: positive, quiet, no
      // payload. Spelled as a bit pattern rather than a NaN literal so no
      // compiler's choice of quiet-NaN encoding can drift it.
      return uint_bits_to_float(0x7fc00000U);
    }
    return f32(sign * std::numeric_limits<double>::infinity());
  }
  // return sign * Math.pow(2, exponent - 15) * (1 + fraction / 1024)
  return f32(sign * std::ldexp(1.0, static_cast<int>(exponent) - 15) *
             (1.0 + static_cast<double>(fraction) / 1024.0));
}

float float16_truncate(float value) noexcept {
  const std::uint32_t bits = float_bits_to_uint(value);
  const std::uint16_t sign = static_cast<std::uint16_t>((bits >> 16U) & 0x8000U);
  const std::uint32_t source_exponent = (bits >> 23U) & 0xffU;
  const std::uint32_t fraction = bits & 0x7fffffU;
  if (source_exponent == 0xffU) {
    if (fraction == 0U) {
      return sign == 0U ? std::numeric_limits<float>::infinity()
                        : -std::numeric_limits<float>::infinity();
    }
    return std::numeric_limits<float>::quiet_NaN();
  }

  const int exponent = static_cast<int>(source_exponent) - 127 + 15;
  std::uint16_t half_bits = 0;
  if (exponent >= 31) {
    half_bits = static_cast<std::uint16_t>(sign | 0x7bffU);
  } else if (exponent <= 0) {
    if (exponent < -10) {
      half_bits = sign;
    } else {
      const std::uint32_t significand = fraction | 0x800000U;
      half_bits = static_cast<std::uint16_t>(sign | ((significand >> (1 - exponent)) >> 13U));
    }
  } else {
    half_bits = static_cast<std::uint16_t>(sign | (static_cast<std::uint16_t>(exponent) << 10U) |
                                           (fraction >> 13U));
  }
  return half_to_float(half_bits);
}

}  // namespace noisemaker
