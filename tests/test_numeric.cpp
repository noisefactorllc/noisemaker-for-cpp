#include "test_harness.hpp"

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <limits>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/numeric.hpp"

static_assert(noexcept(noisemaker::fdlibm::expm1(0.0)));
static_assert(noexcept(noisemaker::fdlibm::exp(0.0)));
static_assert(noexcept(noisemaker::fdlibm::tanh(0.0)));
static_assert(noexcept(noisemaker::fdlibm::sin(0.0)));
static_assert(noexcept(noisemaker::fdlibm::cos(0.0)));

TEST(numeric_f32_narrows_double_to_ieee_float32) {
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::f32(0.1)) == 0x3dcccccdU);
}

TEST(numeric_matches_glsl_mod_round_and_unsigned_multiplication) {
  REQUIRE(noisemaker::glsl_mod(-1.0, 3.0) == 2.0);
  REQUIRE(noisemaker::glsl_round(0.5) == 1.0);
  REQUIRE(noisemaker::glsl_round(-0.5) == 0.0);
  REQUIRE(noisemaker::glsl_round(-1.5) == -1.0);
  REQUIRE(noisemaker::umul(0xffffffffU, 374761393U) == 3920205903U);
}

TEST(numeric_round_matches_javascript_math_round_at_exact_boundaries) {
  const auto bits = [](double value) { return std::bit_cast<std::uint64_t>(value); };
  constexpr std::uint64_t positive_zero_bits = 0x0000000000000000ULL;
  constexpr std::uint64_t negative_zero_bits = 0x8000000000000000ULL;

  REQUIRE(bits(noisemaker::glsl_round(-0.0)) == negative_zero_bits);
  REQUIRE(bits(noisemaker::glsl_round(-0.5)) == negative_zero_bits);
  REQUIRE(bits(noisemaker::glsl_round(std::nextafter(-0.5, 0.0))) == negative_zero_bits);
  REQUIRE(bits(noisemaker::glsl_round(-0.25)) == negative_zero_bits);
  REQUIRE(bits(noisemaker::glsl_round(-std::numeric_limits<double>::denorm_min())) == negative_zero_bits);
  REQUIRE(noisemaker::glsl_round(std::nextafter(-0.5, -1.0)) == -1.0);

  REQUIRE(bits(noisemaker::glsl_round(0.0)) == positive_zero_bits);
  REQUIRE(bits(noisemaker::glsl_round(std::nextafter(0.5, 0.0))) == positive_zero_bits);
  REQUIRE(noisemaker::glsl_round(0.5) == 1.0);
  REQUIRE(noisemaker::glsl_round(std::nextafter(0.5, 1.0)) == 1.0);

  REQUIRE(noisemaker::glsl_round(-2.5) == -2.0);
  REQUIRE(noisemaker::glsl_round(-1.5) == -1.0);
  REQUIRE(noisemaker::glsl_round(1.5) == 2.0);
  REQUIRE(noisemaker::glsl_round(2.5) == 3.0);
  REQUIRE(noisemaker::glsl_round(16777215.5) == 16777216.0);

  REQUIRE(std::isnan(noisemaker::glsl_round(std::numeric_limits<double>::quiet_NaN())));
  REQUIRE(noisemaker::glsl_round(std::numeric_limits<double>::infinity()) ==
          std::numeric_limits<double>::infinity());
  REQUIRE(noisemaker::glsl_round(-std::numeric_limits<double>::infinity()) ==
          -std::numeric_limits<double>::infinity());
  REQUIRE(noisemaker::glsl_round(0x1p52) == 0x1p52);
  REQUIRE(noisemaker::glsl_round(-0x1p52) == -0x1p52);
  REQUIRE(noisemaker::glsl_round(std::numeric_limits<double>::max()) ==
          std::numeric_limits<double>::max());
}

TEST(numeric_matches_hash_and_pcg_vectors) {
  REQUIRE(noisemaker::hash_uint32(0x1234abcdU) == 737574769U);
  REQUIRE((noisemaker::pcg3d({1U, 2U, 3U}) == std::array<std::uint32_t, 3>{4204755366U, 1223881804U, 1500469937U}));
}

TEST(numeric_preserves_float_bit_patterns) {
  REQUIRE(noisemaker::float_bits_to_uint(0.0f) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(-0.0f) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(1.0f) == 0x3f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(std::numeric_limits<float>::infinity()) == 0x7f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::uint_bits_to_float(0x00000000U)) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::uint_bits_to_float(0x80000000U)) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::uint_bits_to_float(0x3f800000U)) == 0x3f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::uint_bits_to_float(0x7f800000U)) == 0x7f800000U);
  const float nan = noisemaker::uint_bits_to_float(0x7fc00001U);
  REQUIRE(std::isnan(nan));
  REQUIRE((noisemaker::float_bits_to_uint(nan) & 0x7f800000U) == 0x7f800000U);
  REQUIRE((noisemaker::float_bits_to_uint(nan) & 0x007fffffU) != 0U);
}

// Shapes183 (classicNoisedeck/shapes:shapes) reaches floatBitsToUint through
// randomFromLatticeWithOffset, and the three downstream scalar uint XOR sites
// consume its result. At the shipped defines LOOP_A_OFFSET=40 /
// LOOP_B_OFFSET=30 that branch is call-graph reachable but dynamically dead,
// so no full-surface render executes it -- the parity fixtures in
// tests/test_generated_kernels.cpp must never be cited as proof it ran. This
// direct bit-pattern test and the frontend profile mutations carry that proof
// instead.
TEST(numeric_round_trips_the_shapes183_controlled_nan_payload_and_scalar_xor) {
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0x7fc12345U)) == 0x7fc12345U);

  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0x00000000U)) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0x80000000U)) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0x3f000000U)) == 0x3f000000U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0xbf000000U)) == 0xbf000000U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0x7f800000U)) == 0x7f800000U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::uint_bits_to_float(0xff800000U)) == 0xff800000U);
  REQUIRE(noisemaker::float_bits_to_uint(0.0f) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(-0.0f) == 0x80000000U);
  REQUIRE(std::isnan(noisemaker::uint_bits_to_float(0x7fc12345U)));
  REQUIRE(std::isinf(noisemaker::uint_bits_to_float(0x7f800000U)));

  // The high-bit-preserving scalar uint XOR the ingress feeds.
  const std::uint32_t ingress =
      noisemaker::float_bits_to_uint(noisemaker::uint_bits_to_float(0x7fc12345U));
  REQUIRE((ingress ^ 0x00000000U) == 0x7fc12345U);
  REQUIRE((ingress ^ 0xffffffffU) == 0x803edcbaU);
  REQUIRE((ingress ^ 0x80000000U) == 0xffc12345U);
  REQUIRE((0x80000000U ^ 0x80000000U) == 0x00000000U);
  REQUIRE((0xffffffffU ^ 0x7fffffffU) == 0x80000000U);
}

TEST(numeric_converts_ieee_half_with_round_to_nearest_even) {
  REQUIRE(noisemaker::float_to_half_rte(0.0f) == 0x0000U);
  REQUIRE(noisemaker::float_to_half_rte(-0.0f) == 0x8000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::half_to_float(0x8000U)) == 0x80000000U);
  REQUIRE(noisemaker::float_to_half_rte(1.0f) == 0x3c00U);
  REQUIRE(noisemaker::float_to_half_rte(65504.0f) == 0x7bffU);
  REQUIRE(noisemaker::float_to_half_rte(std::numeric_limits<float>::infinity()) == 0x7c00U);
  REQUIRE(noisemaker::float_to_half_rte(-std::numeric_limits<float>::infinity()) == 0xfc00U);
  REQUIRE(std::isnan(noisemaker::half_to_float(noisemaker::float_to_half_rte(std::numeric_limits<float>::quiet_NaN()))));
  REQUIRE(noisemaker::half_to_float(0x0001U) == 0x1p-24f);
  REQUIRE(noisemaker::float_to_half_rte(1.00048828125f) == 0x3c00U);
  REQUIRE(noisemaker::float_to_half_rte(1.00146484375f) == 0x3c02U);
}

TEST(numeric_truncates_float16_and_handles_special_values) {
  const float source = 1.0009f;
  const auto truncated = noisemaker::float16_truncate(source);
  REQUIRE(truncated == 1.0f);
  REQUIRE(truncated != 1.0009765625f);
  REQUIRE(noisemaker::float16_truncate(70000.0f) == 65504.0f);
  REQUIRE(noisemaker::float16_truncate(-70000.0f) == -65504.0f);
  REQUIRE(std::isinf(noisemaker::float16_truncate(std::numeric_limits<float>::infinity())));
  REQUIRE(std::isinf(noisemaker::float16_truncate(-std::numeric_limits<float>::infinity())));
  REQUIRE(std::isnan(noisemaker::float16_truncate(std::numeric_limits<float>::quiet_NaN())));
}
