#include "test_harness.hpp"

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>

#include "noisemaker/sampler.hpp"

namespace {

noisemaker::Surface sampler_fixture() {
  return noisemaker::Surface(2, 2, std::vector<float>{
      0.0f, 0.25f, 0.5f, 1.0f,
      0.25f, 0.5f, 1.0f, 0.0f,
      0.5f, 1.0f, 0.0f, 0.25f,
      1.0f, 0.0f, 0.25f, 0.5f,
  });
}

void require_rgba(const noisemaker::Rgba& actual, const noisemaker::Rgba& expected) {
  for (std::size_t channel = 0; channel < actual.size(); ++channel) {
    REQUIRE(test::nearly_equal(actual[channel], expected[channel]));
  }
}

}  // namespace

TEST(sampler_nearest_top_down_uses_surface_storage_rows) {
  const auto surface = sampler_fixture();
  require_rgba(noisemaker::sample_nearest_top_down(surface, 0.25, 0.25),
               {0.0f, 0.25f, 0.5f, 1.0f});
  require_rgba(noisemaker::sample_nearest_top_down(surface, 0.75, 0.75),
               {1.0f, 0.0f, 0.25f, 0.5f});
}

TEST(sampler_nearest_bottom_left_uses_glsl_row_addressing_and_clamps) {
  const auto surface = sampler_fixture();
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.25, 0.25),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.75, 0.25),
               {1.0f, 0.0f, 0.25f, 0.5f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.25, 0.75),
               {0.0f, 0.25f, 0.5f, 1.0f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.75, 0.75),
               {0.25f, 0.5f, 1.0f, 0.0f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.25, 0.5),
               {0.0f, 0.25f, 0.5f, 1.0f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, -100.0, -100.0),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 100.0, 100.0),
               {0.25f, 0.5f, 1.0f, 0.0f});
}

TEST(sampler_nearest_propagates_nan_coordinates_like_typed_array_indexing) {
  const auto surface = sampler_fixture();
  for (const auto& sample : {
           noisemaker::sample_nearest_top_down(surface, std::numeric_limits<double>::quiet_NaN(), 0.5),
           noisemaker::sample_nearest_bottom_left(surface, 0.5, std::numeric_limits<double>::quiet_NaN())}) {
    for (float channel : sample) REQUIRE(std::isnan(channel));
  }
}

TEST(sampler_bilinear_bottom_left_uses_half_texel_centers_and_edge_clamping) {
  const auto surface = sampler_fixture();
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 0.25, 0.25),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 0.75, 0.25),
               {1.0f, 0.0f, 0.25f, 0.5f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 0.25, 0.75),
               {0.0f, 0.25f, 0.5f, 1.0f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 0.75, 0.75),
               {0.25f, 0.5f, 1.0f, 0.0f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 0.5, 0.5),
               {0.4375f, 0.4375f, 0.4375f, 0.4375f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, -100.0, -100.0),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(surface, 100.0, 100.0),
               {0.25f, 0.5f, 1.0f, 0.0f});
}

TEST(sampler_generated_texture_float_seam_dispatches_without_changing_explicit_nearest_or_texel_fetch) {
  noisemaker::Surface surface = sampler_fixture();
  surface.set_filter(noisemaker::TextureFilter::linear);

  // Generated texture() helpers pass Float32 UV lanes. That overload is the
  // runtime texture seam and consumes Surface::filter().
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.5f, 0.5f),
               {0.4375f, 0.4375f, 0.4375f, 0.4375f});

  // The pre-existing explicit-nearest API remains nearest when callers pass
  // its original binary64 coordinates, and integer texelFetch ignores filter.
  require_rgba(noisemaker::sample_nearest_bottom_left(surface, 0.5, 0.5),
               {0.25f, 0.5f, 1.0f, 0.0f});
  require_rgba(noisemaker::sample_nearest_top_down(surface, 0.5, 0.5),
               {1.0f, 0.0f, 0.25f, 0.5f});
  require_rgba(noisemaker::texel_fetch_bottom_left(surface, 1, 1),
               {0.25f, 0.5f, 1.0f, 0.0f});
}

TEST(sampler_generated_linear_texture_matches_js_signed_zero_bits) {
  noisemaker::Surface surface(1U, 1U, std::vector<float>{
      -0.0f, -0.0f, -0.0f, -0.0f,
  });
  surface.set_filter(noisemaker::TextureFilter::linear);

  // Authoritative JS sampleBilinear evaluates -0 + (-0 - -0) * 0 and
  // Math.fround stores +0 in every lane. Approximate equality cannot
  // distinguish the signed-zero regression this fixture is intended to catch.
  const noisemaker::Rgba sample =
      noisemaker::sample_nearest_bottom_left(surface, 0.5f, 0.5f);
  for (const float lane : sample) {
    REQUIRE(std::bit_cast<std::uint32_t>(lane) == 0x00000000U);
  }
}

TEST(sampler_bilinear_bottom_left_clamps_infinities_and_propagates_nan) {
  const auto surface = sampler_fixture();
  require_rgba(noisemaker::sample_bilinear_bottom_left(
                   surface, -std::numeric_limits<double>::infinity(), 0.5),
               {0.25f, 0.625f, 0.25f, 0.625f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(
                   surface, std::numeric_limits<double>::infinity(), 0.5),
               {0.625f, 0.25f, 0.625f, 0.25f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(
                   surface, 0.5, -std::numeric_limits<double>::infinity()),
               {0.75f, 0.5f, 0.125f, 0.375f});
  require_rgba(noisemaker::sample_bilinear_bottom_left(
                   surface, 0.5, std::numeric_limits<double>::infinity()),
               {0.125f, 0.375f, 0.75f, 0.5f});

  const auto nan_sample = noisemaker::sample_bilinear_bottom_left(
      surface, std::numeric_limits<double>::quiet_NaN(), 0.5);
  for (float channel : nan_sample) {
    REQUIRE(std::isnan(channel));
  }
}

TEST(sampler_texel_fetch_bottom_left_addresses_integer_rows_and_clamps) {
  const auto surface = sampler_fixture();
  require_rgba(noisemaker::texel_fetch_bottom_left(surface, 0, 0),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::texel_fetch_bottom_left(surface, 1, 1),
               {0.25f, 0.5f, 1.0f, 0.0f});
  require_rgba(noisemaker::texel_fetch_bottom_left(surface, -100, -100),
               {0.5f, 1.0f, 0.0f, 0.25f});
  require_rgba(noisemaker::texel_fetch_bottom_left(surface, 100, 100),
               {0.25f, 0.5f, 1.0f, 0.0f});
}

TEST(sampler_texel_fetch_bottom_left_preserves_exact_float_lanes_and_repeats) {
  const noisemaker::Surface surface(1U, 2U, std::vector<float>{
      0.1f, -2.25f, 12345.5f, 0.375f,
      -0.0f, 0.2f, -987.75f, 0.625f,
  });
  const noisemaker::Rgba lower{-0.0f, 0.2f, -987.75f, 0.625f};
  const noisemaker::Rgba upper{0.1f, -2.25f, 12345.5f, 0.375f};
  REQUIRE(noisemaker::texel_fetch_bottom_left(surface, 0, 0) == lower);
  REQUIRE(noisemaker::texel_fetch_bottom_left(surface, 0, 1) == upper);
  REQUIRE(noisemaker::texel_fetch_bottom_left(surface, -7, -9) == lower);
  REQUIRE(noisemaker::texel_fetch_bottom_left(surface, 8, 11) == upper);
  REQUIRE(noisemaker::texel_fetch_bottom_left(surface, 0, 0) ==
          noisemaker::texel_fetch_bottom_left(surface, 0, 0));
}
