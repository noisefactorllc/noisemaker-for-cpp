#include "test_harness.hpp"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

#include "noisemaker/effects/median.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/surface.hpp"

#include "oracles/median_all_radii_expected.inc"

namespace {

using noisemaker::Surface;
using noisemaker::glsl::Bindings;

using Rgba = std::array<float, 4>;

// Every pixel generator below is a literal transcription of the matching
// named generator in
// docs/port-engineering/median-parity/median_all_radii_oracle_generator.mjs
// (see each oracle case's `generator` tag) -- same arithmetic, same single
// rounding-to-float32 at the point of storage (`Math.fround` there,
// `static_cast<float>` of a `double` computation here).
Rgba gradient_pixel(std::size_t col, std::size_t row, std::size_t width, std::size_t height) {
  const double r = static_cast<double>(col + 1U) / static_cast<double>(width + 1U);
  const double g = static_cast<double>(row + 1U) / static_cast<double>(height + 1U);
  const double b = static_cast<double>((col * 3U + row * 5U) % 11U) / 10.0;
  return {static_cast<float>(r), static_cast<float>(g), static_cast<float>(b), 1.0F};
}

Rgba checkerboard_pixel(std::size_t col, std::size_t row) {
  const bool on = (col + row) % 2U == 0U;
  return on ? Rgba{0.75F, 0.25F, 0.5F, 1.0F} : Rgba{0.2F, 0.6F, 0.1F, 1.0F};
}

Rgba red_green_tie_pixel(std::size_t col, std::size_t row) {
  const bool on = (col + row) % 2U == 0U;
  return on ? Rgba{0.0F, static_cast<float>(0.6486297249794006), 0.5F, 1.0F}
            : Rgba{static_cast<float>(0.5049999952316284), static_cast<float>(0.49851369857788086),
                   0.5F, 1.0F};
}

Rgba translucent_ramp_pixel(std::size_t col, std::size_t row, std::size_t width) {
  const double r = static_cast<double>(col + 1U) / static_cast<double>(width + 1U);
  const double g = static_cast<double>(row + 2U) / 9.0;
  const double b = 1.0 - r;
  const double a = static_cast<double>(col % 5U) / 4.0;
  return {static_cast<float>(r), static_cast<float>(g), static_cast<float>(b),
         static_cast<float>(a)};
}

Rgba hdr_and_negative_pixel(std::size_t col, std::size_t row) {
  static constexpr std::array<Rgba, 9> kValues{{
      {-0.3F, 1.6F, 0.2F, 1.0F}, {0.1F, 0.2F, 0.3F, 1.0F}, {-0.1F, 1.9F, 0.4F, 1.0F},
      {0.5F, 0.05F, 1.7F, 1.0F}, {0.05F, -0.6F, 0.05F, 1.0F}, {0.9F, 0.3F, -0.2F, 1.0F},
      {-1.5F, 0.4F, 0.4F, 1.0F}, {0.2F, 0.2F, 0.2F, 1.0F}, {1.3F, -0.4F, 0.9F, 1.0F},
  }};
  return kValues[row * 3U + col];
}

Rgba nan_channel_pixel(std::size_t col, std::size_t row) {
  if (row == 1U && col == 1U) {
    return {std::numeric_limits<float>::quiet_NaN(), 0.4F, 0.6F, 1.0F};
  }
  return gradient_pixel(col, row, 3U, 3U);
}

Rgba pixel_for(std::string_view generator, std::size_t col, std::size_t row,
               std::size_t width, std::size_t height) {
  if (generator == "gradient") return gradient_pixel(col, row, width, height);
  if (generator == "checkerboard") return checkerboard_pixel(col, row);
  if (generator == "redGreenTie") return red_green_tie_pixel(col, row);
  if (generator == "translucentRamp") return translucent_ramp_pixel(col, row, width);
  if (generator == "hdrAndNegative") return hdr_and_negative_pixel(col, row);
  if (generator == "nanChannel") return nan_channel_pixel(col, row);
  throw std::invalid_argument("unknown oracle pixel generator");
}

// Row 0 is the TOP of the image, matching
// median_all_radii_oracle_generator.mjs's makeInputTexture and
// noisemaker::texel_fetch_bottom_left's own y-flip convention.
Surface oracle_input(const noisemaker_median_all_radii_oracle::Case& fixture) {
  std::vector<float> data(static_cast<std::size_t>(fixture.width) *
                          static_cast<std::size_t>(fixture.height) * 4U);
  for (std::size_t row = 0; row < fixture.height; ++row) {
    for (std::size_t col = 0; col < fixture.width; ++col) {
      const Rgba value = pixel_for(fixture.generator, col, row, fixture.width, fixture.height);
      const std::size_t base = (row * fixture.width + col) * 4U;
      data[base + 0U] = value[0];
      data[base + 1U] = value[1];
      data[base + 2U] = value[2];
      data[base + 3U] = value[3];
    }
  }
  return Surface(fixture.width, fixture.height, std::move(data));
}

std::uint32_t float_bits(float value) {
  std::uint32_t bits = 0;
  static_assert(sizeof(bits) == sizeof(value));
  __builtin_memcpy(&bits, &value, sizeof(bits));
  return bits;
}

}  // namespace

TEST(median_kernel_matches_the_frozen_authority_oracle_byte_for_byte) {
  REQUIRE(noisemaker_median_all_radii_oracle::kCases.size() == 19U);
  std::array<bool, 3> radius_seen{false, false, false};
  for (const auto& fixture : noisemaker_median_all_radii_oracle::kCases) {
    REQUIRE(fixture.radius >= 1 && fixture.radius <= 3);
    radius_seen[static_cast<std::size_t>(fixture.radius) - 1U] = true;

    const Surface input = oracle_input(fixture);
    Bindings bindings;
    bindings.set_texture("inputTex", input);
    bindings.set_uniform("RADIUS", fixture.radius);
    bindings.set_uniform("threshold", static_cast<float>(fixture.threshold));

    const auto kernel = noisemaker::effects::bind_median(bindings);
    const Surface rendered = noisemaker::run_pass(kernel, fixture.width, fixture.height);

    const auto rgba8 = rendered.to_rgba8();
    REQUIRE(rgba8.size() == fixture.output_rgba8.size());
    for (std::size_t index = 0; index < rgba8.size(); ++index) {
      REQUIRE(rgba8[index] == fixture.output_rgba8[index]);
    }

    const auto data = rendered.data();
    REQUIRE(data.size() == fixture.output_float32_words.size());
    for (std::size_t index = 0; index < data.size(); ++index) {
      REQUIRE(float_bits(data[index]) == fixture.output_float32_words[index]);
    }
  }
  // Every allowed radius (1, 2, 3) is actually exercised by this matrix --
  // the whole point of this oracle relative to the original median-oracles.json
  // package, which the report says leaves radii other than 2 unwired.
  REQUIRE(radius_seen[0]);
  REQUIRE(radius_seen[1]);
  REQUIRE(radius_seen[2]);
}

TEST(median_kernel_alpha_is_always_the_original_center_pixel) {
  // median.js never ranks or replaces alpha: `out[3] = surface.data[centerOffset + 3]`
  // unconditionally, regardless of the replace/threshold decision.
  std::vector<float> data{
      0.1F, 0.2F, 0.3F, 0.4F, 0.5F, 0.6F, 0.7F, 0.8F,
      0.9F, 0.05F, 0.15F, 0.9F, 0.2F, 0.25F, 0.35F, 0.2F,
  };
  Surface input(2U, 2U, data);
  Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("RADIUS", std::int32_t{1});
  bindings.set_uniform("threshold", 0.0F);
  const auto kernel = noisemaker::effects::bind_median(bindings);
  const Surface rendered = noisemaker::run_pass(kernel, 2U, 2U);
  const auto out = rendered.data();
  // Alpha always passes through the CENTER sample unchanged, so the output
  // alpha at storage position (x, y) trivially equals the input alpha at
  // that same (x, y) -- the run_pass / texel_fetch_bottom_left y-flips each
  // apply once in opposite directions and cancel for the center read.
  REQUIRE(out[3] == data[3]);
  REQUIRE(out[7] == data[7]);
  REQUIRE(out[11] == data[11]);
  REQUIRE(out[15] == data[15]);
}

TEST(median_kernel_defaults_radius_to_two_when_unbound) {
  // Every caller reaching bind_median through the graph executor's custom-
  // adapter route always supplies RADIUS (see materialize_compile_defines in
  // src/graph/executor.cpp). A caller built against the OLD typed-emitter
  // ABI -- which never carried RADIUS as a binding at all -- must still get
  // exactly the behavior it always got: RADIUS=2, the sole value that ABI
  // ever baked.
  std::vector<float> data(5U * 5U * 4U, 0.0F);
  for (std::size_t i = 0; i < 25U; ++i) {
    data[i * 4U + 0U] = static_cast<float>(i) / 25.0F;
    data[i * 4U + 1U] = static_cast<float>(24U - i) / 25.0F;
    data[i * 4U + 2U] = static_cast<float>((i * 7U) % 25U) / 25.0F;
    data[i * 4U + 3U] = 1.0F;
  }
  Surface input(5U, 5U, data);

  Bindings with_radius;
  with_radius.set_texture("inputTex", input);
  with_radius.set_uniform("RADIUS", std::int32_t{2});
  with_radius.set_uniform("threshold", 0.0F);
  const Surface expected = noisemaker::run_pass(
      noisemaker::effects::bind_median(with_radius), 5U, 5U);

  Bindings without_radius;
  without_radius.set_texture("inputTex", input);
  without_radius.set_uniform("threshold", 0.0F);
  const Surface actual = noisemaker::run_pass(
      noisemaker::effects::bind_median(without_radius), 5U, 5U);

  REQUIRE(actual.to_rgba8() == expected.to_rgba8());
}
