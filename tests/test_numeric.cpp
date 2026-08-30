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

// The JS CPU authority's floatToHalf (glsl-runtime.js:61-81) rounds half-UP
// unconditionally and canonicalizes every NaN to 0x7e00; it is NOT IEEE
// ties-to-even. Expected values below come from that authority under node.
TEST(numeric_converts_float_to_half_with_the_js_authority_rule) {
  REQUIRE(noisemaker::float_to_half_js(0.0f) == 0x0000U);
  REQUIRE(noisemaker::float_to_half_js(-0.0f) == 0x8000U);
  REQUIRE(noisemaker::float_bits_to_uint(noisemaker::half_to_float(0x8000U)) == 0x80000000U);
  REQUIRE(noisemaker::float_to_half_js(1.0f) == 0x3c00U);
  REQUIRE(noisemaker::float_to_half_js(65504.0f) == 0x7bffU);
  REQUIRE(noisemaker::float_to_half_js(std::numeric_limits<float>::infinity()) == 0x7c00U);
  REQUIRE(noisemaker::float_to_half_js(-std::numeric_limits<float>::infinity()) == 0xfc00U);
  REQUIRE(std::isnan(noisemaker::half_to_float(noisemaker::float_to_half_js(std::numeric_limits<float>::quiet_NaN()))));
  REQUIRE(noisemaker::half_to_float(0x0001U) == 0x1p-24f);
  // Exact halfway case: ties-to-even would give 0x3c00, the authority gives 0x3c01.
  REQUIRE(noisemaker::float_to_half_js(1.00048828125f) == 0x3c01U);
  REQUIRE(noisemaker::float_to_half_js(-1.00048828125f) == 0xbc01U);
  // Every NaN canonicalizes, sign and payload discarded.
  REQUIRE(noisemaker::float_to_half_js(std::numeric_limits<float>::quiet_NaN()) == 0x7e00U);
  REQUIRE(noisemaker::float_to_half_js(noisemaker::uint_bits_to_float(0xffc12345U)) == 0x7e00U);
  REQUIRE(noisemaker::float_to_half_js(1.00146484375f) == 0x3c02U);
}

// Expansion direction. The JS CPU authority's halfToFloat (glsl-runtime.js:52-59)
// collapses EVERY NaN half code to Number.NaN -- sign and payload discarded --
// which the caller's Float32Array store narrows to 0x7fc00000. Comparisons are on
// bit patterns, never on float equality, because NaN != NaN. Every expected value
// below came from running that authority function under node.
TEST(numeric_expands_half_to_float_with_the_js_authority_rule) {
  const auto expand = [](std::uint16_t code) {
    return noisemaker::float_bits_to_uint(noisemaker::half_to_float(code));
  };

  // Signed zero, subnormals, the subnormal/normal boundary.
  REQUIRE(expand(0x0000U) == 0x00000000U);
  REQUIRE(expand(0x8000U) == 0x80000000U);
  REQUIRE(expand(0x0001U) == 0x33800000U);
  REQUIRE(expand(0x8001U) == 0xb3800000U);
  REQUIRE(expand(0x03ffU) == 0x387fc000U);
  REQUIRE(expand(0x83ffU) == 0xb87fc000U);
  REQUIRE(expand(0x0400U) == 0x38800000U);

  // Normals, including the largest representable half.
  REQUIRE(expand(0x3c00U) == 0x3f800000U);
  REQUIRE(expand(0xbc00U) == 0xbf800000U);
  REQUIRE(expand(0x3c01U) == 0x3f802000U);
  REQUIRE(expand(0x7bffU) == 0x477fe000U);
  REQUIRE(expand(0xfbffU) == 0xc77fe000U);

  // Infinities keep their sign.
  REQUIRE(expand(0x7c00U) == 0x7f800000U);
  REQUIRE(expand(0xfc00U) == 0xff800000U);

  // Every NaN code -- either sign, any payload -- becomes canonical 0x7fc00000.
  REQUIRE(expand(0x7c01U) == 0x7fc00000U);
  REQUIRE(expand(0xfc01U) == 0x7fc00000U);
  REQUIRE(expand(0x7e00U) == 0x7fc00000U);
  REQUIRE(expand(0xfe00U) == 0x7fc00000U);
  REQUIRE(expand(0xffffU) == 0x7fc00000U);
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
