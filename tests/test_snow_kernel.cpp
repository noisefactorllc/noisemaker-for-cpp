#include "test_harness.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

#include "noisemaker/effects/snow.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/surface.hpp"

#include "oracles/snow_expected.inc"

namespace {

using noisemaker::Surface;
using noisemaker::glsl::Bindings;

// Same deterministic byte pattern the JS generator uses
// (docs/port-engineering/snow-parity/snow_oracle_generator.mjs's
// makeInputTexture, itself borrowed from patterned_seed in
// tests/test_graph_features.cpp), pushed through the same
// Surface::from_rgba8 the native kernel and the oracle both agree on.
Surface patterned_input(std::size_t width, std::size_t height) {
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    bytes[index] = static_cast<std::uint8_t>((index * 37U + 11U) % 256U);
  }
  return Surface::from_rgba8(width, height, bytes);
}

}  // namespace

TEST(snow_kernel_matches_the_frozen_authority_oracle_byte_for_byte) {
  for (const auto& oracle_case : noisemaker_snow_oracle::kCases) {
    const Surface input = patterned_input(oracle_case.width, oracle_case.height);
    Bindings bindings;
    bindings.set_texture("inputTex", input);
    bindings.set_uniform("alpha", oracle_case.alpha);
    bindings.set_uniform("time", oracle_case.time);
    bindings.set_uniform("pause", oracle_case.pause);
    bindings.set_uniform("density", oracle_case.density);

    const auto kernel = noisemaker::effects::bind_snow(bindings);
    const Surface rendered =
        noisemaker::run_pass(kernel, oracle_case.width, oracle_case.height,
                             0.0F, 0.0F, 0U, 0.0F);

    const auto rgba8 = rendered.to_rgba8();
    REQUIRE(rgba8.size() == oracle_case.output_rgba8.size());
    for (std::size_t index = 0; index < rgba8.size(); ++index) {
      REQUIRE(rgba8[index] == oracle_case.output_rgba8[index]);
    }

    const auto data = rendered.data();
    REQUIRE(data.size() == oracle_case.output_float32_words.size());
    for (std::size_t index = 0; index < data.size(); ++index) {
      std::uint32_t bits = 0;
      static_assert(sizeof(bits) == sizeof(float));
      __builtin_memcpy(&bits, &data[index], sizeof(bits));
      REQUIRE(bits == oracle_case.output_float32_words[index]);
    }
  }
}

TEST(snow_kernel_alpha_zero_is_an_exact_passthrough) {
  // snow.js's own fast path: `if (alpha === 0) { out.set(source...); return }`.
  // Every byte of the rendered surface must equal the untouched input.
  const Surface input = patterned_input(5U, 3U);
  Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("alpha", 0.0);
  bindings.set_uniform("time", 12.5);
  bindings.set_uniform("pause", 0.0);
  bindings.set_uniform("density", 50.0);

  const auto kernel = noisemaker::effects::bind_snow(bindings);
  const Surface rendered = noisemaker::run_pass(kernel, 5U, 3U, 0.0F, 0.0F, 0U, 0.0F);
  REQUIRE(rendered.to_rgba8() == input.to_rgba8());
}

TEST(snow_kernel_never_binds_resolution_or_tile_offset) {
  // snow.js never reads $bindings.resolution / tileOffset / fullResolution
  // (unlike the GLSL it replaces) -- bind_snow must not require them either.
  const Surface input = patterned_input(3U, 3U);
  Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("alpha", 0.5);
  bindings.set_uniform("time", 0.25);
  bindings.set_uniform("pause", 0.0);
  bindings.set_uniform("density", 50.0);

  const auto kernel = noisemaker::effects::bind_snow(bindings);
  const Surface rendered = noisemaker::run_pass(kernel, 3U, 3U, 0.0F, 0.0F, 0U, 0.0F);
  REQUIRE(rendered.data().size() == 3U * 3U * 4U);
}
