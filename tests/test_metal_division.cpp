#include "test_harness.hpp"

#include <bit>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/metal_division.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

#include "oracles/metal_division_expected.inc"

namespace {

namespace oracle = noisemaker_metal_division_oracle;
using noisemaker::metal::metal_divide;
using noisemaker::metal::metal_reciprocal;

float float_from(std::uint32_t bits) { return std::bit_cast<float>(bits); }
double double_from(std::uint64_t bits) { return std::bit_cast<double>(bits); }

bool same_double(double actual, std::uint64_t expected) {
  if (expected == oracle::kNan64) return std::isnan(actual);
  return std::bit_cast<std::uint64_t>(actual) == expected;
}

bool same_float(float actual, std::uint32_t expected) {
  if (expected == oracle::kNan32) return std::isnan(actual);
  return std::bit_cast<std::uint32_t>(actual) == expected;
}

std::string concatenated_bits() {
  const auto& data = noisemaker::metal::reciprocal_data();
  std::string text;
  for (std::size_t line = 0; line < data.bits_lines; ++line) text.append(data.bits[line]);
  return text;
}

}  // namespace

TEST(metal_reciprocal_data_is_the_pinned_authority_capture) {
  const auto& data = noisemaker::metal::reciprocal_data();
  // The CPU authority's src/csl/metal-reciprocal-data.js, LF digest, and the
  // SHA-256 of its base64 band bitstream.
  REQUIRE(data.authority_module_sha256 == "08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87");
  REQUIRE(noisemaker::graph::detail::sha256(concatenated_bits()) == data.bits_sha256);
  REQUIRE(data.bits_sha256 == "9892eeea7b886fe3ffc742d61ed0022d71a22be6930d5b7a2e1633f7feb2ff3b");
  REQUIRE(data.band_low == 0.28);
  REQUIRE(data.band_high == 0.71);
  REQUIRE(data.band_bits == 3607761U);
  REQUIRE(data.positive_deviations == 859417U);
  REQUIRE(data.negative_deviations == 8757U);
}

TEST(metal_reciprocal_band_data_rebuilds_the_captured_two_bit_table) {
  // The authority's own check: every deviation one ulp above or below, by the
  // grid position, rebuilds the 2-bit capture table whose SHA-256 it pins.
  const auto& data = noisemaker::metal::reciprocal_data();
  const std::vector<std::uint8_t> deviations = noisemaker::metal::decode_reciprocal_deviations(data);
  std::string table(static_cast<std::size_t>(1U << 23U) >> 2U, '\0');
  std::size_t positive = 0;
  std::size_t negative = 0;
  for (std::uint32_t mantissa = 1; mantissa < (1U << 23U); ++mantissa) {
    if (((deviations[mantissa >> 3U] >> (mantissa & 7U)) & 1U) == 0U) continue;
    const bool up = noisemaker::metal::reciprocal_grid_position(mantissa) < 0.5;
    (up ? positive : negative) += 1;
    const unsigned code = up ? 1U : 2U;
    table[mantissa >> 2U] = static_cast<char>(static_cast<unsigned char>(table[mantissa >> 2U]) | (code << ((mantissa & 3U) * 2U)));
  }
  REQUIRE(positive == 859417U);
  REQUIRE(negative == 8757U);
  REQUIRE(noisemaker::graph::detail::sha256(table) == data.table_sha256);
}

TEST(metal_reciprocal_data_rejects_a_corrupt_bitstream) {
  auto data = noisemaker::metal::reciprocal_data();
  const std::string_view truncated[] = {data.bits[0]};
  data.bits = truncated;
  data.bits_lines = 1;
  REQUIRE_THROWS_AS(noisemaker::metal::decode_reciprocal_deviations(data), std::runtime_error);
}

TEST(metal_reciprocal_of_41_is_one_ulp_above_the_correctly_rounded_value) {
  const auto bits = [](double value) { return std::bit_cast<std::uint32_t>(static_cast<float>(value)); };
  REQUIRE(bits(metal_reciprocal(41.0)) == bits(1.0 / 41.0) + 1U);
  REQUIRE(bits(metal_reciprocal(-41.0)) == bits(-1.0 / 41.0) + 1U);
  REQUIRE(bits(metal_reciprocal(41.0 * 64.0)) == bits(1.0 / (41.0 * 64.0)) + 1U);
  REQUIRE(metal_reciprocal(23.0) == static_cast<double>(static_cast<float>(1.0 / 23.0)));
  REQUIRE(metal_reciprocal(64.0) == 1.0 / 64.0);
}

TEST(metal_reciprocal_matches_the_authority_for_selected_values) {
  for (const auto& item : oracle::kReciprocals) {
    REQUIRE(same_double(metal_reciprocal(double_from(item.value)), item.result));
  }
}

TEST(metal_divide_matches_every_m4_measured_operand_pair) {
  std::size_t correctly_rounded = 0;
  for (const auto& item : oracle::kMeasured) {
    const float a = float_from(item.a);
    const float b = float_from(item.b);
    const double result = metal_divide(a, b);
    // The GPU's float32 result, and the authority's exact unrounded product.
    REQUIRE(same_float(static_cast<float>(result), item.gpu));
    REQUIRE(same_double(result, item.result));
    if (same_float(static_cast<float>(static_cast<double>(a) / static_cast<double>(b)), item.gpu)) correctly_rounded += 1;
  }
  REQUIRE(std::size(oracle::kMeasured) == 277U);
  // 64 of the 256 runtime pairs and most special operands agree with a
  // correctly rounded division; the other 192 runtime pairs do not.
  REQUIRE(correctly_rounded < std::size(oracle::kMeasured) - 191U);
}

TEST(metal_divide_matches_the_authority_for_pseudo_random_operands) {
  for (const auto& item : oracle::kRandom) {
    REQUIRE(same_double(metal_divide(double_from(item.a), double_from(item.b)), item.result));
  }
  // 4096 generated pairs; the 4 with a NaN operand stay out, because a NaN
  // operand has no exact word in the oracle. The measured special pairs cover
  // NaN operands.
  REQUIRE(std::size(oracle::kRandom) == 4092U);
}

TEST(nearest_texel_selection_matches_every_m4_measured_coordinate) {
  for (const auto& item : oracle::kNearest) {
    std::vector<float> data(static_cast<std::size_t>(item.width) * item.height * 4U, 0.0f);
    for (std::uint32_t y = 0; y < item.height; ++y) {
      for (std::uint32_t x = 0; x < item.width; ++x) {
        // Storage is top-down; shader row y is storage row height - 1 - y.
        const std::size_t offset = (static_cast<std::size_t>(item.height - 1U - y) * item.width + x) * 4U;
        data[offset] = static_cast<float>(x);
        data[offset + 1U] = static_cast<float>(y);
      }
    }
    const noisemaker::Surface surface = noisemaker::Surface(item.width, item.height, std::move(data));
    const noisemaker::Rgba texel =
        noisemaker::sample_nearest_texel_bottom_left(surface, float_from(item.u), float_from(item.v));
    REQUIRE(texel[0] == static_cast<float>(item.column));
    REQUIRE(texel[1] == static_cast<float>(item.row));
    REQUIRE(noisemaker::sample_texture_bottom_left(surface, float_from(item.u), float_from(item.v))[0] ==
            static_cast<float>(item.column));
  }
}
