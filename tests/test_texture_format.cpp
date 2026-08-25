#include "test_harness.hpp"

#include <array>
#include <vector>

#include "noisemaker/texture_format.hpp"
#include "noisemaker/numeric.hpp"

TEST(texture_format_rgba16f_truncates_each_channel) {
  noisemaker::Surface surface(1, 1, std::vector<float>{0.1f, 0.3333f, 1.5f, -0.25f});

  noisemaker::quantize_texture(surface, noisemaker::TextureFormat::rgba16f);

  const std::array<float, 4> expected{0.0999755859375f, 0.333251953125f, 1.5f, -0.25f};
  const auto data = surface.data();
  for (std::size_t channel = 0; channel < expected.size(); ++channel) {
    REQUIRE(data[channel] == expected[channel]);
  }
}

TEST(texture_format_rgba8_unorm_clamps_and_rounds_to_normalized_bytes) {
  noisemaker::Surface surface(1, 1, std::vector<float>{0.1f, 0.5f, 2.0f, -1.0f});

  noisemaker::quantize_texture(surface, noisemaker::TextureFormat::rgba8_unorm);

  const std::vector<std::uint8_t> expected{26U, 128U, 255U, 0U};
  const auto data = surface.data();
  REQUIRE(noisemaker::float_bits_to_uint(data[0]) == 0x3dd0d0d1U);
  REQUIRE(noisemaker::float_bits_to_uint(data[1]) == 0x3f008081U);
  REQUIRE(noisemaker::float_bits_to_uint(data[2]) == 0x3f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[3]) == 0x00000000U);
  REQUIRE(surface.to_rgba8() == expected);
}

TEST(texture_format_rgba8_unorm_preserves_nan_and_clamps_infinities) {
  noisemaker::Surface surface(1, 1, std::vector<float>{
      noisemaker::uint_bits_to_float(0x7fc00001U),
      noisemaker::uint_bits_to_float(0x7f800000U),
      noisemaker::uint_bits_to_float(0xff800000U),
      0.25f,
  });

  noisemaker::quantize_texture(surface, noisemaker::TextureFormat::rgba8_unorm);

  const auto data = surface.data();
  REQUIRE((data[0] != data[0]));
  REQUIRE(noisemaker::float_bits_to_uint(data[1]) == 0x3f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[2]) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[3]) == 0x3e808081U);
}

TEST(texture_format_rgba32f_preserves_every_channel_bit_pattern) {
  noisemaker::Surface surface(1, 1, std::vector<float>{
      noisemaker::uint_bits_to_float(0x80000000U),
      noisemaker::uint_bits_to_float(0x7fc12345U),
      noisemaker::uint_bits_to_float(0xff800000U),
      noisemaker::uint_bits_to_float(0x3f800000U),
  });

  noisemaker::quantize_texture(surface, noisemaker::TextureFormat::rgba32f);

  const auto data = surface.data();
  REQUIRE(noisemaker::float_bits_to_uint(data[0]) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[1]) == 0x7fc12345U);
  REQUIRE(noisemaker::float_bits_to_uint(data[2]) == 0xff800000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[3]) == 0x3f800000U);
}

TEST(texture_format_invalid_enum_is_a_bit_preserving_no_op) {
  noisemaker::Surface surface(1, 1, std::vector<float>{
      noisemaker::uint_bits_to_float(0x80000000U),
      noisemaker::uint_bits_to_float(0x7fc12345U),
      noisemaker::uint_bits_to_float(0xff800000U),
      noisemaker::uint_bits_to_float(0x3f800000U),
  });

  const auto& result = noisemaker::quantize_texture(
      surface, static_cast<noisemaker::TextureFormat>(999));

  REQUIRE(&result == &surface);
  const auto data = surface.data();
  REQUIRE(noisemaker::float_bits_to_uint(data[0]) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[1]) == 0x7fc12345U);
  REQUIRE(noisemaker::float_bits_to_uint(data[2]) == 0xff800000U);
  REQUIRE(noisemaker::float_bits_to_uint(data[3]) == 0x3f800000U);
}
