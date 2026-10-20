#include "test_harness.hpp"

#include <array>
#include <bit>
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

TEST(cpu_adapter_sync_snow_fetches_use_javascript_int32_coercion) {
  struct FetchCase { std::array<std::uint32_t,2> coordinates; std::array<std::uint32_t,4> output; };
  constexpr std::array<FetchCase,5> fetch_cases = {{
  FetchCase{{0x7fc00000u,0x7fc00000u},{0x3ea5294au,0x3ec1bad0u,0x3df9c190u,0x3e124925u}},
  FetchCase{{0x7f800000u,0xff800000u},{0x3ea5294au,0x3ec1bad0u,0x3df9c190u,0x3e124925u}},
  FetchCase{{0x4f800000u,0x4f800000u},{0x3ea5294au,0x3ec1bad0u,0x3df9c190u,0x3e124925u}},
  FetchCase{{0xbff33333u,0x3ff33333u},{0x3e25294au,0x3e41bad0u,0x3f0f9c19u,0x3f124925u}},
  FetchCase{{0x7149f2cau,0xf149f2cau},{0x3ea5294au,0x3ec1bad0u,0x3df9c190u,0x3e124925u}},
  }};
  std::vector<float> data;
  for (std::size_t i = 0; i < 12U; ++i) {
    const auto x = i % 4U;
    const auto y = i / 4U;
    data.insert(data.end(), {
        static_cast<float>(static_cast<double>((3U*x+5U*y)%31U)/31.0),
        static_cast<float>(static_cast<double>((11U*x+7U*y)%37U)/37.0),
        static_cast<float>(static_cast<double>((17U*x+23U*y)%41U)/41.0),
        static_cast<float>(static_cast<double>(i%7U)/7.0)});
  }
  const Surface input(4U, 3U, data);
  Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("alpha", 0.0);
  bindings.set_uniform("time", 0.25);
  bindings.set_uniform("pause", 0.0);
  bindings.set_uniform("density", 75.0);
  const auto kernel = noisemaker::effects::bind_snow(bindings);
  for (const auto& fixture : fetch_cases) {
    noisemaker::glsl::PixelContext context;
    context.frag_coord = noisemaker::glsl::Vec4(
        std::bit_cast<float>(fixture.coordinates[0]),
        std::bit_cast<float>(fixture.coordinates[1]), 0.0F, 1.0F);
    noisemaker::glsl::Vec4 out;
    kernel.run_pixel(context, out);
    for (std::size_t lane = 0; lane < 4U; ++lane) {
      REQUIRE(std::bit_cast<std::uint32_t>(out[lane]) == fixture.output[lane]);
    }
  }
}
