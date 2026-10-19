#include "noisemaker/metal_division.hpp"

#include <bit>
#include <cmath>
#include <exception>
#include <limits>
#include <stdexcept>
#include <string>

#include "noisemaker/numeric.hpp"

namespace noisemaker::metal {
namespace {

constexpr double kMinNormal = 1.1754943508222875e-38;
constexpr std::uint32_t kMantissas = 1U << 23U;

int base64_value(char character) noexcept {
  if (character >= 'A' && character <= 'Z') return character - 'A';
  if (character >= 'a' && character <= 'z') return character - 'a' + 26;
  if (character >= '0' && character <= '9') return character - '0' + 52;
  if (character == '+') return 62;
  if (character == '/') return 63;
  return -1;
}

// atob() of the whitespace-free concatenation of the bitstream lines.
std::vector<std::uint8_t> decode_base64(const ReciprocalData& data) {
  std::vector<std::uint8_t> bytes;
  std::uint32_t accumulator = 0;
  int bits = 0;
  bool padded = false;
  for (std::size_t line = 0; line < data.bits_lines; ++line) {
    for (const char character : data.bits[line]) {
      if (character == ' ' || character == '\n' || character == '\r' || character == '\t') continue;
      if (character == '=') {
        padded = true;
        continue;
      }
      const int value = base64_value(character);
      if (value < 0 || padded) throw std::runtime_error("Metal reciprocal data is not base64");
      accumulator = (accumulator << 6U) | static_cast<std::uint32_t>(value);
      bits += 6;
      if (bits >= 8) {
        bits -= 8;
        bytes.push_back(static_cast<std::uint8_t>((accumulator >> static_cast<unsigned>(bits)) & 0xffU));
      }
    }
  }
  return bytes;
}

const std::vector<std::uint8_t>& deviation_table() noexcept {
  // Decoded once, on first use, like the authority's lazy `deviations`.
  static const std::vector<std::uint8_t> table = [] {
    try {
      return decode_reciprocal_deviations(reciprocal_data());
    } catch (...) {
      std::terminate();
    }
  }();
  return table;
}

bool deviates(std::uint32_t mantissa) noexcept {
  return ((deviation_table()[mantissa >> 3U] >> (mantissa & 7U)) & 1U) != 0U;
}

// Both operands are float32 values on the GPU, and subnormals flush to zero.
double flush(double value) noexcept {
  const double rounded = static_cast<double>(noisemaker::f32(value));
  if (rounded != 0.0 && std::fabs(rounded) < kMinNormal) return rounded < 0.0 ? -0.0 : 0.0;
  return rounded;
}

}  // namespace

double reciprocal_grid_position(std::uint32_t mantissa) noexcept {
  const double scaled = 140737488355328.0 / (8388608.0 + static_cast<double>(mantissa));
  return scaled - std::floor(scaled);
}

bool in_reciprocal_band(std::uint32_t mantissa, const ReciprocalData& data) noexcept {
  if (mantissa == 0U) return false;
  const double position = reciprocal_grid_position(mantissa);
  return position >= data.band_low && position <= data.band_high;
}

std::vector<std::uint8_t> decode_reciprocal_deviations(const ReciprocalData& data) {
  const std::vector<std::uint8_t> stream = decode_base64(data);
  std::vector<std::uint8_t> set(kMantissas >> 3U, 0U);
  std::size_t bit = 0;
  std::size_t count = 0;
  for (std::uint32_t mantissa = 1; mantissa < kMantissas; ++mantissa) {
    if (!in_reciprocal_band(mantissa, data)) continue;
    const std::size_t byte = bit >> 3U;
    const unsigned value = byte < stream.size() ? stream[byte] : 0U;
    if (((value >> (bit & 7U)) & 1U) != 0U) {
      set[mantissa >> 3U] = static_cast<std::uint8_t>(set[mantissa >> 3U] | (1U << (mantissa & 7U)));
      count += 1;
    }
    bit += 1;
  }
  if (bit != data.band_bits || count != data.positive_deviations + data.negative_deviations) {
    throw std::runtime_error("Metal reciprocal data is corrupt: " + std::to_string(bit) + " band bits and " +
                             std::to_string(count) + " deviations");
  }
  return set;
}

double metal_reciprocal(double value) noexcept {
  const float rounded = noisemaker::f32(value);
  const std::uint32_t word = std::bit_cast<std::uint32_t>(rounded);
  const std::uint32_t exponent = (word >> 23U) & 0xffU;
  if (exponent == 0U) {
    return (word >> 31U) != 0U ? -std::numeric_limits<double>::infinity()
                               : std::numeric_limits<double>::infinity();
  }
  if (exponent == 0xffU) return static_cast<double>(noisemaker::f32(1.0 / value));
  const double magnitude = std::fabs(static_cast<double>(rounded));
  const double exact = 1.0 / magnitude;
  float reciprocal = noisemaker::f32(exact);
  const std::uint32_t mantissa = word & 0x7fffffU;
  if (mantissa != 0U && deviates(mantissa)) {
    // A deviation rounds the other way: up where the correctly rounded value
    // is below the exact reciprocal, down where it is above.
    std::uint32_t bits = std::bit_cast<std::uint32_t>(reciprocal);
    if (static_cast<double>(reciprocal) < exact) {
      bits += 1U;
    } else {
      bits -= 1U;
    }
    reciprocal = std::bit_cast<float>(bits);
  }
  double result = static_cast<double>(reciprocal);
  if (result < kMinNormal) result = 0.0;
  return (word >> 31U) != 0U ? -result : result;
}

double metal_divide(double dividend, double divisor) noexcept {
  const double product = flush(dividend) * metal_reciprocal(divisor);
  if (product != 0.0 && std::fabs(product) < kMinNormal) return product < 0.0 ? -0.0 : 0.0;
  return product;
}

}  // namespace noisemaker::metal
