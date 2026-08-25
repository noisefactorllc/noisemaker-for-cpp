#include "test_harness.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

#include "noisemaker/surface.hpp"
#include "noisemaker/numeric.hpp"

TEST(surface_rejects_zero_and_overflowing_dimensions) {
  REQUIRE_THROWS_AS(noisemaker::Surface(0, 1), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::Surface(1, 0), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::Surface(std::numeric_limits<std::size_t>::max(), 2), std::overflow_error);
}

TEST(surface_accepts_exact_authority_pixel_cap) {
  noisemaker::Surface surface(4096U, 4096U);
  REQUIRE(surface.width() == 4096U);
  REQUIRE(surface.height() == 4096U);
  REQUIRE(surface.data().size() == 4096U * 4096U * 4U);
}

TEST(surface_rejects_one_pixel_over_authority_cap_before_allocation) {
  REQUIRE_THROWS_AS(noisemaker::Surface(4097U, 4096U), std::overflow_error);
}

TEST(surface_rejects_mismatched_constructor_data) {
  REQUIRE_THROWS_AS((noisemaker::Surface(1, 1, std::vector<float>{0.0f, 0.0f, 0.0f})), std::invalid_argument);
}

TEST(surface_rejects_mismatched_rgba8_data) {
  const std::vector<std::uint8_t> bytes{0, 0, 0, 0, 0};
  REQUIRE_THROWS_AS(noisemaker::Surface::from_rgba8(1, 1, bytes), std::invalid_argument);
}

TEST(surface_converts_rgba8_to_float32) {
  const std::vector<std::uint8_t> bytes{255, 0, 0, 255, 0, 128, 255, 64};
  const auto surface = noisemaker::Surface::from_rgba8(2, 1, bytes);
  const auto data = surface.data();

  REQUIRE(data.size() == 8U);
  REQUIRE(data[0] == 1.0f);
  REQUIRE(data[1] == 0.0f);
  REQUIRE(data[2] == 0.0f);
  REQUIRE(data[3] == 1.0f);
  REQUIRE(data[4] == 0.0f);
  REQUIRE(data[5] == static_cast<float>(128.0 / 255.0));
  REQUIRE(data[6] == 1.0f);
  REQUIRE(data[7] == static_cast<float>(64.0 / 255.0));
}

TEST(surface_from_rgba8_matches_js_double_division_before_float32_storage) {
  const noisemaker::Surface surface = noisemaker::Surface::from_rgba8(
      1U, 1U, std::array<std::uint8_t, 4>{7U, 120U, 0U, 255U});
  const auto pixels = surface.data();
  REQUIRE(noisemaker::float_bits_to_uint(pixels[0]) == 0x3ce0e0e1U);
  REQUIRE(noisemaker::float_bits_to_uint(pixels[1]) == 0x3ef0f0f1U);
}

TEST(surface_clear_and_clone_use_independent_storage) {
  noisemaker::Surface original(2, 1);
  REQUIRE(original.filter() == noisemaker::TextureFilter::nearest);
  original.set_filter(noisemaker::TextureFilter::linear);
  original.clear({0.25f, 0.5f, 0.75f, 1.0f});
  auto copy = original.clone();
  REQUIRE(copy.filter() == noisemaker::TextureFilter::nearest);
  copy.data()[0] = 0.0f;

  const auto original_data = original.data();
  const auto copy_data = copy.data();
  const std::array<float, 4> expected_color{0.25f, 0.5f, 0.75f, 1.0f};
  for (std::size_t index = 0; index < original_data.size(); ++index) {
    REQUIRE(original_data[index] == expected_color[index % 4U]);
  }
  REQUIRE(copy_data[0] == 0.0f);
  REQUIRE(original_data[0] == 0.25f);
}

TEST(surface_filter_state_has_value_copy_semantics_but_js_clone_resets) {
  noisemaker::Surface original(1U, 1U);
  original.set_filter(noisemaker::TextureFilter::linear);
  const noisemaker::Surface constructed(original);
  REQUIRE(constructed.filter() == noisemaker::TextureFilter::linear);
  noisemaker::Surface assigned(1U, 1U);
  assigned = original;
  REQUIRE(assigned.filter() == noisemaker::TextureFilter::linear);
  REQUIRE(original.clone().filter() == noisemaker::TextureFilter::nearest);
}

TEST(surface_filter_state_defaults_and_clear_preservation_are_explicit) {
  const noisemaker::Surface rgba = noisemaker::Surface::from_rgba8(
      1U, 1U, std::array<std::uint8_t, 4>{1U, 2U, 3U, 4U});
  REQUIRE(rgba.filter() == noisemaker::TextureFilter::nearest);
  noisemaker::Surface surface(1U, 1U);
  surface.set_filter(noisemaker::TextureFilter::linear);
  surface.clear({1.0f, 0.0f, 0.0f, 1.0f});
  REQUIRE(surface.filter() == noisemaker::TextureFilter::linear);
}

TEST(surface_converts_float32_to_rgba8_per_js_contract) {
  noisemaker::Surface surface(2, 1, {
    std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity(),
    -std::numeric_limits<float>::infinity(), -0.1f,
    0.0f, 0.5f, 1.0f, 1.1f,
  });
  const auto bytes = surface.to_rgba8();
  const std::vector<std::uint8_t> expected{0, 0, 0, 0, 0, 128, 255, 255};
  REQUIRE(bytes == expected);
}
