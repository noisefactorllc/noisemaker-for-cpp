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

std::uint16_t float_to_half_rte(float value) noexcept {
  const std::uint32_t bits = float_bits_to_uint(value);
  const std::uint16_t sign = static_cast<std::uint16_t>((bits >> 16U) & 0x8000U);
  const std::uint32_t source_exponent = (bits >> 23U) & 0xffU;
  const std::uint32_t fraction = bits & 0x7fffffU;

  if (source_exponent == 0xffU) {
    return fraction == 0U ? static_cast<std::uint16_t>(sign | 0x7c00U)
                          : static_cast<std::uint16_t>(sign | 0x7e00U);
  }

  int exponent = static_cast<int>(source_exponent) - 127 + 15;
  if (exponent >= 31) {
    return static_cast<std::uint16_t>(sign | 0x7c00U);
  }
  if (exponent <= 0) {
    if (exponent < -10) {
      return sign;
    }
    const std::uint32_t significand = fraction | 0x800000U;
    const unsigned shift = static_cast<unsigned>(14 - exponent);
    std::uint32_t result = significand >> shift;
    const std::uint32_t remainder = significand & ((1U << shift) - 1U);
    const std::uint32_t halfway = 1U << (shift - 1U);
    if (remainder > halfway || (remainder == halfway && (result & 1U) != 0U)) {
      ++result;
    }
    return static_cast<std::uint16_t>(sign | result);
  }

  std::uint32_t result = fraction >> 13U;
  const std::uint32_t remainder = fraction & 0x1fffU;
  if (remainder > 0x1000U || (remainder == 0x1000U && (result & 1U) != 0U)) {
    ++result;
    if (result == 0x400U) {
      result = 0U;
      ++exponent;
      if (exponent >= 31) {
        return static_cast<std::uint16_t>(sign | 0x7c00U);
      }
    }
  }
  return static_cast<std::uint16_t>(sign | (static_cast<std::uint16_t>(exponent) << 10U) | result);
}

float half_to_float(std::uint16_t bits) noexcept {
  const std::uint32_t sign = (static_cast<std::uint32_t>(bits) & 0x8000U) << 16U;
  const std::uint32_t exponent = (static_cast<std::uint32_t>(bits) >> 10U) & 0x1fU;
  const std::uint32_t fraction = static_cast<std::uint32_t>(bits) & 0x03ffU;
  if (exponent == 0U) {
    if (fraction == 0U) {
      return uint_bits_to_float(sign);
    }
    const float magnitude = std::ldexp(static_cast<float>(fraction), -24);
    return sign == 0U ? magnitude : -magnitude;
  }
  if (exponent == 0x1fU) {
    if (fraction == 0U) {
      return uint_bits_to_float(sign | 0x7f800000U);
    }
    return uint_bits_to_float(sign | 0x7fc00000U | (fraction << 13U));
  }
  const float magnitude = std::ldexp(1.0f + static_cast<float>(fraction) / 1024.0f,
                                     static_cast<int>(exponent) - 15);
  return sign == 0U ? magnitude : -magnitude;
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
