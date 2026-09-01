#include "test_harness.hpp"

#include <array>
#include <bit>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <span>
#include <sstream>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

#include "noisemaker/glsl_types.hpp"
#include "noisemaker/glsl_runtime.hpp"

static_assert(std::is_constructible_v<noisemaker::glsl::Vec3, float, float, float>);
static_assert(std::is_constructible_v<noisemaker::glsl::Vec3, noisemaker::glsl::Vec2, float>);
static_assert(std::is_constructible_v<noisemaker::glsl::Vec4, noisemaker::glsl::Vec2, noisemaker::glsl::Vec2>);
static_assert(!std::is_constructible_v<noisemaker::glsl::Vec3, noisemaker::glsl::Vec2, noisemaker::glsl::Vec2>);

namespace {

template <class Left, class Right>
concept HasGlslEqual = requires(const Left& left, const Right& right) {
  { equal(left, right) } ->
      std::same_as<noisemaker::glsl::Vec<2, bool>>;
};

static_assert(HasGlslEqual<noisemaker::glsl::Vec2,
                           noisemaker::glsl::Vec2>);
static_assert(HasGlslEqual<noisemaker::glsl::Vec2,
                           noisemaker::glsl::FloatExpr<2>>);
static_assert(HasGlslEqual<noisemaker::glsl::FloatExpr<2>,
                           noisemaker::glsl::Vec2>);
static_assert(HasGlslEqual<noisemaker::glsl::FloatExpr<2>,
                           noisemaker::glsl::FloatExpr<2>>);
static_assert(!HasGlslEqual<noisemaker::glsl::Vec3,
                            noisemaker::glsl::Vec3>);
static_assert(!HasGlslEqual<noisemaker::glsl::Vec4,
                            noisemaker::glsl::Vec4>);

struct GlitchMatrixCase {
  const char* name;
  std::array<std::uint32_t, 16> q;
  std::array<std::uint32_t, 16> first;
  std::array<std::uint32_t, 16> final;
  const char* final_sha256;
  std::size_t right_associated_mismatches;
  std::size_t unrounded_intermediate_mismatches;
};

constexpr std::array<std::uint32_t, 16> kGlitchT{
    0x3f800000U, 0x00000000U, 0xc0400000U, 0x40000000U,
    0x00000000U, 0x00000000U, 0x40400000U, 0xc0000000U,
    0x00000000U, 0x3f800000U, 0xc0000000U, 0x3f800000U,
    0x00000000U, 0x00000000U, 0xbf800000U, 0x3f800000U};
constexpr std::array<std::uint32_t, 16> kGlitchS{
    0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U,
    0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U,
    0xc0400000U, 0x40400000U, 0xc0000000U, 0xbf800000U,
    0x40000000U, 0xc0000000U, 0x3f800000U, 0x3f800000U};

constexpr std::array<GlitchMatrixCase, 5> kGlitchMatrixCases{{
  {"identity-q",
   {0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U,
    0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U},
   {0x3f800000U, 0x00000000U, 0xc0400000U, 0x40000000U, 0x00000000U, 0x00000000U, 0x40400000U, 0xc0000000U,
    0x00000000U, 0x3f800000U, 0xc0000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0xbf800000U, 0x3f800000U},
   {0x3f800000U, 0x00000000U, 0xc0400000U, 0x40000000U, 0x00000000U, 0x3f800000U, 0xc0000000U, 0x3f800000U,
    0xc0400000U, 0xc0000000U, 0x41b80000U, 0xc1700000U, 0x40000000U, 0x3f800000U, 0xc1700000U, 0x41200000U},
   "d0a0329be70a2c456732dd1ceb4013d481b04cc3a5ea3a9d67b594de16ab2244", 0U, 0U},
  {"fractional-q",
   {0xbf546cf0U, 0xbd2e4c41U, 0x3f3ea367U, 0xbf1df51bU, 0x3e2e4c41U, 0x3f751b3cU, 0xbecefa8eU, 0x3ec415caU,
    0xbf7a8d9eU, 0xbe4415caU, 0x3f1882b9U, 0xbf4415caU, 0x3cae4c41U, 0x3f4efa8eU, 0xbf0d9df5U, 0x3e6fa8daU},
   {0xbf546cf0U, 0x3f3ea367U, 0x3fbea368U, 0xbfb93106U, 0x3e2e4c41U, 0xbecefa8eU, 0x4032620bU, 0xbfcc415dU,
    0xbf7a8d9eU, 0x3f1882b9U, 0x3ff7d46dU, 0xbfdf51b4U, 0x3cae4c41U, 0xbf0d9df5U, 0x404efa8eU, 0xbff2620bU},
   {0xbf546cf0U, 0x3f3ea367U, 0x3fbea368U, 0xbfb93106U, 0xbf7a8d9eU, 0x3f1882b9U, 0x3ff7d46dU, 0xbfdf51b4U,
    0x409df51bU, 0xc082b931U, 0xc04d9df6U, 0x409df51cU, 0xc03d46cfU, 0x4015c988U, 0x4024c416U, 0xc055c988U},
   "b65c9f13623dcf8acd325f14a056a0cf747a0772d4ebb529984dfeadc75c03a5", 4U, 3U},
  {"wide-dynamic-q",
   {0x35800000U, 0xc8800000U, 0x3eaaaaabU, 0xbe124925U, 0x437f01feU, 0xc280fdfcU, 0x40490fdbU, 0xc02df854U,
    0x3dcccccdU, 0xbe4ccccdU, 0x3e99999aU, 0xbecccccdU, 0x4640e700U, 0xc5a9c100U, 0x3f800001U, 0x80000000U},
   {0x35800000U, 0x3eaaaaabU, 0xc9400008U, 0x49000003U, 0x437f01feU, 0x40490fdbU, 0xc47084e4U, 0x441fdb96U,
    0x3dcccccdU, 0x3e99999aU, 0xbf8ccccdU, 0x3f000000U, 0x4640e700U, 0x3f800001U, 0xc75057a0U, 0x470ae4c0U},
   {0x35800000U, 0x3eaaaaabU, 0xc9400008U, 0x49000003U, 0x3dcccccdU, 0x3e99999aU, 0xbf8ccccdU, 0x3f000000U,
    0xc634f3b5U, 0x40da6495U, 0x4a131454U, 0xc9c41b40U, 0x4638ef56U, 0xc08a20ecU, 0xc9c646adU, 0x49842f36U},
   "daf3699fafcc2b273320b3fb6a463bd224e6e8bf8af792ee293279ba78252bb9", 3U, 1U},
  {"pcg-shaped-q-a",
   {0x3f66ffe7U, 0x3e2e51a5U, 0xbebb6b70U, 0x3e4e285cU, 0x3eca12e7U, 0x3f572040U, 0x3e932bb8U, 0xbdf46360U,
    0xbdd78051U, 0x3eabe6faU, 0xbe3e01aaU, 0x3d94279dU, 0x3e5ef512U, 0xbef6c017U, 0x3dd1b109U, 0xbd6a6183U},
   {0x3f66ffe7U, 0xbebb6b70U, 0xbfd53090U, 0x3fa655adU, 0x3eca12e7U, 0x3e932bb8U, 0x3f61a51aU, 0xbf392429U,
    0xbdd78051U, 0xbe3e01aaU, 0x3fcf933bU, 0xbf7ec285U, 0x3e5ef512U, 0x3dd1b109U, 0xc00fc787U, 0x3fb8e554U},
   {0x3f66ffe7U, 0xbebb6b70U, 0xbfd53090U, 0x3fa655adU, 0xbdd78051U, 0xbe3e01aaU, 0x3fcf933bU, 0xbf7ec285U,
    0xbfc3e045U, 0x400eab5cU, 0x40d49c7cU, 0xc0b0b685U, 0x3f905d11U, 0xbfb1f0b9U, 0xc0b70083U, 0x408fd4e5U},
   "303e734d9d4eea2c089fafe3e9cb805226c952ff357bdf8357384c9838831768", 1U, 1U},
  {"pcg-shaped-q-b",
   {0x34000000U, 0x3f7fffffU, 0xbeffffffU, 0x3f000001U, 0x3f3b3230U, 0x3e03d300U, 0xbe9a41a7U, 0x3e428d05U,
    0x3f2bfcefU, 0x3ed723b8U, 0xbe8e2ecfU, 0x3d7db9f2U, 0x3f0d1510U, 0x3f384b94U, 0xbed28474U, 0x3e0f63d8U},
   {0x34000000U, 0xbeffffffU, 0x405ffffdU, 0xbffffffcU, 0x3f3b3230U, 0xbe9a41a7U, 0xbfb28cf5U, 0x3f8bfea7U,
    0x3f2bfcefU, 0xbe8e2ecfU, 0xbe85dc12U, 0x3e9334bbU, 0x3f0d1510U, 0xbed28474U, 0x3f982785U, 0xbf1bd64cU},
   {0x34000000U, 0xbeffffffU, 0x405ffffdU, 0xbffffffcU, 0x3f2bfcefU, 0xbe8e2ecfU, 0xbe85dc12U, 0x3e9334bbU,
    0x3e990f38U, 0x3fc80746U, 0xc1759c09U, 0x41150996U, 0xbe754974U, 0xbf8b0bfdU, 0x412b794cU, 0xc0d046cfU},
   "98ca17191f978d3fceaa784be9010cfaf5b7a4736766a41b030c4edb5f88c94c", 1U, 0U},
}};

[[nodiscard]] noisemaker::glsl::Mat4 glitch_mat4(
    const std::array<std::uint32_t, 16>& words) {
  using noisemaker::glsl::Vec4;
  const auto value = [&](std::size_t index) {
    return noisemaker::uint_bits_to_float(words[index]);
  };
  return noisemaker::glsl::Mat4(
      Vec4(value(0), value(1), value(2), value(3)),
      Vec4(value(4), value(5), value(6), value(7)),
      Vec4(value(8), value(9), value(10), value(11)),
      Vec4(value(12), value(13), value(14), value(15)));
}

[[nodiscard]] std::array<std::uint32_t, 16> glitch_mat4_words(
    const noisemaker::glsl::Mat4& matrix) {
  std::array<std::uint32_t, 16> words{};
  for (std::size_t column = 0; column < 4U; ++column)
    for (std::size_t row = 0; row < 4U; ++row)
      words[column * 4U + row] =
          noisemaker::float_bits_to_uint(matrix[column][row]);
  return words;
}

[[nodiscard]] std::array<double, 16> glitch_decode_matrix(
    const std::array<std::uint32_t, 16>& words) {
  std::array<double, 16> values{};
  for (std::size_t index = 0; index < words.size(); ++index)
    values[index] = noisemaker::uint_bits_to_float(words[index]);
  return values;
}

[[nodiscard]] std::array<double, 16> glitch_unrounded_product(
    const std::array<double, 16>& left,
    const std::array<double, 16>& right) {
  std::array<double, 16> result{};
  for (std::size_t column = 0; column < 4U; ++column) {
    for (std::size_t row = 0; row < 4U; ++row) {
      double sum = 0.0;
      for (std::size_t inner = 0; inner < 4U; ++inner)
        sum += left[inner * 4U + row] * right[column * 4U + inner];
      result[column * 4U + row] = sum;
    }
  }
  return result;
}

[[nodiscard]] std::array<std::uint32_t, 16> glitch_narrow_matrix(
    const std::array<double, 16>& values) {
  std::array<std::uint32_t, 16> words{};
  for (std::size_t index = 0; index < values.size(); ++index)
    words[index] = noisemaker::float_bits_to_uint(
        noisemaker::f32(values[index]));
  return words;
}

[[nodiscard]] std::array<std::uint32_t, 16> glitch_rounded_product(
    const std::array<std::uint32_t, 16>& left,
    const std::array<std::uint32_t, 16>& right) {
  return glitch_narrow_matrix(glitch_unrounded_product(
      glitch_decode_matrix(left), glitch_decode_matrix(right)));
}

[[nodiscard]] std::size_t glitch_mismatch_count(
    const std::array<std::uint32_t, 16>& expected,
    const std::array<std::uint32_t, 16>& actual) {
  std::size_t count = 0;
  for (std::size_t index = 0; index < expected.size(); ++index)
    if (expected[index] != actual[index]) ++count;
  return count;
}

[[nodiscard]] std::uint32_t glitch_rotr(std::uint32_t value,
                                        std::uint32_t count) {
  return std::rotr(value, static_cast<int>(count));
}

[[nodiscard]] std::array<std::uint8_t, 32> glitch_sha256(
    std::span<const std::uint8_t> input) {
  constexpr std::array<std::uint32_t, 64> constants{
      0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
      0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U, 0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
      0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
      0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
      0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U, 0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
      0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
      0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
      0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U, 0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U};
  std::vector<std::uint8_t> bytes(input.begin(), input.end());
  const std::uint64_t bit_count =
      static_cast<std::uint64_t>(bytes.size()) * 8U;
  bytes.push_back(0x80U);
  while ((bytes.size() % 64U) != 56U) bytes.push_back(0U);
  for (int shift = 56; shift >= 0; shift -= 8)
    bytes.push_back(static_cast<std::uint8_t>(bit_count >> shift));
  std::array<std::uint32_t, 8> hash{
      0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
      0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U};
  for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16U; ++index) {
      words[index] =
          (static_cast<std::uint32_t>(bytes[offset + index * 4U]) << 24U) |
          (static_cast<std::uint32_t>(bytes[offset + index * 4U + 1U]) << 16U) |
          (static_cast<std::uint32_t>(bytes[offset + index * 4U + 2U]) << 8U) |
          bytes[offset + index * 4U + 3U];
    }
    for (std::size_t index = 16U; index < words.size(); ++index) {
      const std::uint32_t s0 = glitch_rotr(words[index - 15U], 7U) ^
                               glitch_rotr(words[index - 15U], 18U) ^
                               (words[index - 15U] >> 3U);
      const std::uint32_t s1 = glitch_rotr(words[index - 2U], 17U) ^
                               glitch_rotr(words[index - 2U], 19U) ^
                               (words[index - 2U] >> 10U);
      words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
    }
    std::uint32_t a = hash[0], b = hash[1], c = hash[2], d = hash[3];
    std::uint32_t e = hash[4], f = hash[5], g = hash[6], h = hash[7];
    for (std::size_t index = 0; index < words.size(); ++index) {
      const std::uint32_t s1 = glitch_rotr(e, 6U) ^ glitch_rotr(e, 11U) ^
                               glitch_rotr(e, 25U);
      const std::uint32_t choice = (e & f) ^ (~e & g);
      const std::uint32_t temporary1 =
          h + s1 + choice + constants[index] + words[index];
      const std::uint32_t s0 = glitch_rotr(a, 2U) ^ glitch_rotr(a, 13U) ^
                               glitch_rotr(a, 22U);
      const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
      const std::uint32_t temporary2 = s0 + majority;
      h = g; g = f; f = e; e = d + temporary1;
      d = c; c = b; b = a; a = temporary1 + temporary2;
    }
    hash[0] += a; hash[1] += b; hash[2] += c; hash[3] += d;
    hash[4] += e; hash[5] += f; hash[6] += g; hash[7] += h;
  }
  std::array<std::uint8_t, 32> output{};
  for (std::size_t index = 0; index < hash.size(); ++index)
    for (std::size_t lane = 0; lane < 4U; ++lane)
      output[index * 4U + lane] = static_cast<std::uint8_t>(
          hash[index] >> (24U - lane * 8U));
  return output;
}

[[nodiscard]] std::string glitch_hex(std::span<const std::uint8_t> bytes) {
  std::ostringstream output;
  for (const std::uint8_t byte : bytes)
    output << std::hex << std::setfill('0') << std::setw(2)
           << static_cast<unsigned>(byte);
  return output.str();
}

[[nodiscard]] std::string glitch_matrix_sha256(
    const std::array<std::uint32_t, 16>& words) {
  std::array<std::uint8_t, 64> bytes{};
  for (std::size_t index = 0; index < words.size(); ++index)
    for (std::size_t lane = 0; lane < 4U; ++lane)
      bytes[index * 4U + lane] = static_cast<std::uint8_t>(
          words[index] >> (lane * 8U));
  return glitch_hex(glitch_sha256(bytes));
}

}  // namespace

TEST(glsl_vec_default_and_splat_construction) {
  const noisemaker::glsl::Vec3 zero;
  REQUIRE(zero[0] == 0.0f);
  REQUIRE(zero[1] == 0.0f);
  REQUIRE(zero[2] == 0.0f);

  const noisemaker::glsl::Vec3 splat(2.5f);
  REQUIRE(splat[0] == 2.5f);
  REQUIRE(splat[1] == 2.5f);
  REQUIRE(splat[2] == 2.5f);
}

TEST(glsl_vec_exact_and_flattening_construction) {
  using namespace noisemaker::glsl;
  const Vec3 exact(1.0f, 2.0f, 3.0f);
  const Vec3 flattened(Vec2(4.0f, 5.0f), 6.0f);
  const Vec4 pairs(Vec2(7.0f, 8.0f), Vec2(9.0f, 10.0f));
  REQUIRE(exact == Vec3(1.0f, 2.0f, 3.0f));
  REQUIRE(flattened == Vec3(4.0f, 5.0f, 6.0f));
  REQUIRE(pairs == Vec4(7.0f, 8.0f, 9.0f, 10.0f));
  REQUIRE_THROWS_AS(exact.at(3), std::out_of_range);
}

TEST(glsl_canonical_js_vector_equality_result_truthiness_is_not_mathematical_equality) {
  using namespace noisemaker::glsl;
  const Vec3 equal_left(1.0f, 1.0f, 1.0f);
  const Vec3 equal_right(1.0f, 1.0f, 1.0f);
  const Vec3 unequal(1.0f, 0.0f, 1.0f);

  REQUIRE(canonical_js_vector_equality_result_is_truthy(equal_left, equal_right));
  REQUIRE(canonical_js_vector_equality_result_is_truthy(equal_left, unequal));
  REQUIRE(equal_left == equal_right);
  REQUIRE(!(equal_left == unequal));
}

TEST(glsl_javascript_unsigned_multiply_and_fractional_array_read_are_exact) {
  using namespace noisemaker::glsl;
  REQUIRE(detail::js_umul(4294967295.0, 2.0) == 4294967294.0);
  REQUIRE(detail::js_umul(-1.0, 2.0) == 4294967294.0);

  const std::array<std::int32_t, 3> values{11, 22, 33};
  REQUIRE(detail::js_array_int32_read_for_bitwise(
              values.data(), values.size(), 1.0) == 22);
  REQUIRE(detail::js_array_int32_read_for_bitwise(
              values.data(), values.size(), 1.5) == 0);
  REQUIRE(detail::js_array_int32_read_for_bitwise(
              values.data(), values.size(), -1.0) == 0);
  REQUIRE(detail::js_array_int32_read_for_bitwise(
              values.data(), values.size(),
              std::numeric_limits<double>::quiet_NaN()) == 0);
}

// The JS CPU authority's packHalf2x16 is
// `uint32(floatToHalf(value[0]) | (floatToHalf(value[1]) << 16))`
// (noisemaker-for-cpu/src/csl/glsl-runtime.js:419), and its floatToHalf
// (:61-81) rounds half-UP unconditionally rather than to nearest-even. Every
// expected value below was produced by running that exact authority function
// under node; do not "fix" them toward IEEE ties-to-even.
TEST(glsl_pack_and_unpack_half2x16_match_the_js_authority_float_to_half) {
  using namespace noisemaker::glsl;
  const auto low_half = [](std::uint32_t float_bits) {
    return pack_half2x16(Vec2(noisemaker::uint_bits_to_float(float_bits), 0.0f)) & 0xffffU;
  };

  const std::uint32_t packed = pack_half2x16(Vec2(1.0f, -2.0f));
  REQUIRE(packed == 0xc0003c00U);
  REQUIRE(unpack_half2x16(packed) == Vec2(1.0f, -2.0f));

  // Exact halfway case. IEEE ties-to-even would give 0x3c00; the authority
  // adds 0x1000 unconditionally and gives 0x3c01.
  REQUIRE(low_half(0x3f801000U) == 0x3c01U);
  REQUIRE(low_half(0xbf801000U) == 0xbc01U);
  REQUIRE(low_half(0x3f803000U) == 0x3c02U);

  // First two divergent inputs of the exhaustive 2^32 differential.
  REQUIRE(low_half(0x33000000U) == 0x0001U);
  REQUIRE(low_half(0x34200000U) == 0x0003U);
  REQUIRE(low_half(0xb3000000U) == 0x8001U);

  // Subnormal band: pre-truncation plus the unconditional bias, including the
  // carry that promotes the largest subnormal to the smallest normal (0x0400).
  REQUIRE(low_half(0x00000001U) == 0x0000U);
  REQUIRE(low_half(0x007fffffU) == 0x0000U);
  REQUIRE(low_half(0x33800000U) == 0x0001U);
  REQUIRE(low_half(0x387fc000U) == 0x03ffU);
  REQUIRE(low_half(0x387ff000U) == 0x0400U);
  REQUIRE(low_half(0x38800000U) == 0x0400U);

  // Overflow: 65504 is the largest representable half; 65520 carries out of
  // the fraction, bumps the exponent to 31, and becomes infinity.
  REQUIRE(low_half(0x477fe000U) == 0x7bffU);
  REQUIRE(low_half(0x477ff000U) == 0x7c00U);
  REQUIRE(low_half(0x7f7fffffU) == 0x7c00U);

  // Signed zero and infinity.
  REQUIRE(low_half(0x00000000U) == 0x0000U);
  REQUIRE(low_half(0x80000000U) == 0x8000U);
  REQUIRE(low_half(0x7f800000U) == 0x7c00U);
  REQUIRE(low_half(0xff800000U) == 0xfc00U);

  // Every NaN, of either sign and any payload, canonicalizes to 0x7e00 —
  // the authority checks Number.isNaN before it ever reads the sign bit.
  REQUIRE(low_half(0x7fc00000U) == 0x7e00U);
  REQUIRE(low_half(0xffc00000U) == 0x7e00U);
  REQUIRE(low_half(0x7f800001U) == 0x7e00U);
  REQUIRE(low_half(0xffc12345U) == 0x7e00U);

  // Both lanes at once, high lane shifted by 16.
  REQUIRE(pack_half2x16(Vec2(noisemaker::uint_bits_to_float(0x33000000U),
                             noisemaker::uint_bits_to_float(0xbf801000U))) == 0xbc010001U);
}

// The authority's unpackHalf2x16 (glsl-runtime.js:420-425) is two halfToFloat
// calls (:52-59) whose results are stored into the Float32Array that alloc()
// returns (:120-124). halfToFloat maps EVERY NaN half code to Number.NaN, so
// sign and payload are discarded and the lane comes back as 0x7fc00000. These
// are bit-pattern comparisons: `Vec2 == Vec2` uses float equality and NaN is
// never equal to itself, so it cannot express this contract. Expected values
// came from running the authority under node.
TEST(glsl_unpack_half2x16_matches_the_js_authority_half_to_float) {
  using namespace noisemaker::glsl;
  using Lanes = std::pair<std::uint32_t, std::uint32_t>;
  const auto lanes = [](std::uint32_t packed) {
    const Vec2 unpacked = unpack_half2x16(packed);
    return Lanes(noisemaker::float_bits_to_uint(unpacked[0]),
                 noisemaker::float_bits_to_uint(unpacked[1]));
  };

  REQUIRE(lanes(0xbc003c00U) == Lanes(0x3f800000U, 0xbf800000U));
  REQUIRE(lanes(0x80000000U) == Lanes(0x00000000U, 0x80000000U));
  REQUIRE(lanes(0xfc007c00U) == Lanes(0x7f800000U, 0xff800000U));
  REQUIRE(lanes(0x03ff7bffU) == Lanes(0x477fe000U, 0x387fc000U));

  // NaN codes canonicalize in both lanes; the negative NaN does NOT come back
  // as 0xffc00000, and the payload does not survive.
  REQUIRE(lanes(0x7e007c01U) == Lanes(0x7fc00000U, 0x7fc00000U));
  REQUIRE(lanes(0xfe00fe00U) == Lanes(0x7fc00000U, 0x7fc00000U));
  REQUIRE(lanes(0xffff3c00U) == Lanes(0x3f800000U, 0x7fc00000U));
}

TEST(glsl_float_expressions_materialize_at_flattening_and_matrix_boundaries) {
  using namespace noisemaker::glsl;
  const auto pair_expression = Vec2(1.25f, 2.5f) + 0.25;
  const Vec3 flattened(pair_expression, 3.0f);
  REQUIRE(flattened == Vec3(1.5f, 2.75f, 3.0f));

  const Mat2 matrix(Vec2(1.0f, 2.0f), Vec2(3.0f, 4.0f));
  const auto expression = Vec2(5.0f, 6.0f) + 0.0;
  REQUIRE((matrix * expression) == Vec2(23.0f, 34.0f));
  REQUIRE((expression * matrix) == Vec2(17.0f, 39.0f));
}

TEST(glsl_vec_cross_base_conversion_is_deterministic) {
  using namespace noisemaker::glsl;
  const Vec3 values(-1.75f, 2.99f, std::numeric_limits<float>::infinity());
  const IVec3 signed_values(values);
  const UVec3 unsigned_values(values);
  const IVec3 nan_values{Vec3(std::numeric_limits<float>::quiet_NaN())};
  REQUIRE(signed_values == IVec3(-1, 2, INT32_MAX));
  REQUIRE(unsigned_values == UVec3(UINT32_MAX, 2U, 0U));
  REQUIRE(nan_values == IVec3(0));
  const Vec3 narrowed(IVec3(16777217, -2, 1));
  REQUIRE(narrowed[0] == 16777216.0f);
  REQUIRE(narrowed[1] == -2.0f);
}

TEST(glsl_float_vector_expressions_defer_rounding_until_storage) {
  using namespace noisemaker::glsl;
  const Vec2 a(30570110.0f);
  const Vec2 b(35727780.0f);
  const double c = 0.9301421642303467;
  const Vec2 stored = a + b + c;
  REQUIRE(noisemaker::float_bits_to_uint(stored[0]) == 1283254281U);
  const Vec2 exceptional = Vec2(std::numeric_limits<float>::infinity()) +
                           Vec2(-std::numeric_limits<float>::infinity());
  REQUIRE(std::isnan(exceptional[0]));
}

TEST(glsl_integral_vectors_convert_to_deferred_float_expressions) {
  using namespace noisemaker::glsl;
  const UVec2 integers(4000000001U, 3000000001U);
  const Vec2 divided = FloatExpr<2>(integers) / 4294967296.0;
  REQUIRE(noisemaker::float_bits_to_uint(divided[0]) ==
          noisemaker::float_bits_to_uint(static_cast<float>(4000000001.0 / 4294967296.0)));
  REQUIRE(noisemaker::float_bits_to_uint(divided[1]) ==
          noisemaker::float_bits_to_uint(static_cast<float>(3000000001.0 / 4294967296.0)));
}

TEST(glsl_float_expression_swizzles_preserve_deferred_lane_precision) {
  const noisemaker::glsl::FloatExpr<3> value(
      0.5 + 0x1p-30, 0.25 + 0x1p-31, 0.75 + 0x1p-30);
  const double lane = noisemaker::glsl::swizzle<0>(value);
  REQUIRE(lane == 0.5 + 0x1p-30);
  const noisemaker::glsl::FloatExpr<2> pair = noisemaker::glsl::swizzle<2, 1>(value);
  REQUIRE(pair[0] == 0.75 + 0x1p-30);
  REQUIRE(pair[1] == 0.25 + 0x1p-31);
}

TEST(glsl_integer_vector_arithmetic_wraps_and_zero_divides) {
  using namespace noisemaker::glsl;
  REQUIRE((IVec2(INT32_MAX, INT32_MIN) + IVec2(1, -1)) == IVec2(INT32_MIN, INT32_MAX));
  REQUIRE((UVec2(UINT32_MAX, 0U) + UVec2(1U, UINT32_MAX)) == UVec2(0U, UINT32_MAX));
  REQUIRE((IVec2(INT32_MIN, 7) / IVec2(-1, 0)) == IVec2(INT32_MIN, 0));
  REQUIRE((UVec2(9U, 8U) / UVec2(0U, 2U)) == UVec2(0U, 4U));
  REQUIRE((IVec2(1, 2) + 3) == IVec2(4, 5));
  REQUIRE((3 + IVec2(1, 2)) == IVec2(4, 5));
  const auto scalar_left = 2.0 + Vec2(1.5f, 2.5f);
  REQUIRE(scalar_left[0] == 3.5);
  REQUIRE(scalar_left[1] == 4.5);
}

TEST(glsl_unsigned_vector_shift_and_xor_match_javascript_uint32_semantics) {
  using namespace noisemaker::glsl;
  const UVec3 values(UINT32_MAX, 0x80000000U, 0x12345678U);
  REQUIRE(shift_right(values, 32U) == values);
  REQUIRE(shift_right(values, 36U) == UVec3(0x0fffffffU, 0x08000000U, 0x01234567U));
  REQUIRE(bitwise_xor(values, UVec3(0xffffffffU, 1U, 0x00ff00ffU)) ==
          UVec3(0U, 0x80000001U, 0x12cb5687U));
  REQUIRE(detail::float_to_uint32(-1.0) == UINT32_MAX);
  REQUIRE(detail::float_to_uint32(4294967297.0) == 1U);
  REQUIRE(detail::float_to_uint32(std::numeric_limits<double>::infinity()) == 0U);
  REQUIRE(detail::float_to_uint32(std::numeric_limits<double>::quiet_NaN()) == 0U);
}

// The GLSL integral constructors the typed emitter routes through
// `glsl_int_cast`/`glsl_uint_cast`. Every expected value below was measured
// against the JS CPU authority: its transpiled kernels spell `int(x)` and
// `uint(x)` as `x|0` (canonical-kernels.js: `var seedInt = floor(s)|0;`,
// `hash_mix((cellX|0) ^ ((rowSeed|0) * 997))`) and its CSL runtime stdlib
// declares `int: (value) => value | 0` and `uint: (value) => value >>> 0`.
// The three classes C++ leaves UNDEFINED -- NaN, the infinities, and finite
// values outside the destination range -- are the point of these pins: UBSan
// caught both a `nan`->int and a `-12.5238`->unsigned conversion in the
// generated slice, and either one is free to change with the compiler.
TEST(glsl_integral_casts_match_the_authority_for_every_input_class) {
  using namespace noisemaker::glsl::detail;
  const double nan_value = std::numeric_limits<double>::quiet_NaN();
  const double inf_value = std::numeric_limits<double>::infinity();

  // NaN and both infinities: `NaN|0`, `Infinity|0`, `(-Infinity)|0` are 0,
  // and so are the `>>>0` forms.
  REQUIRE(glsl_int_cast(nan_value) == 0);
  REQUIRE(glsl_int_cast(inf_value) == 0);
  REQUIRE(glsl_int_cast(-inf_value) == 0);
  REQUIRE(glsl_uint_cast(nan_value) == 0U);
  REQUIRE(glsl_uint_cast(inf_value) == 0U);
  REQUIRE(glsl_uint_cast(-inf_value) == 0U);
  REQUIRE(glsl_int_cast(std::numeric_limits<float>::quiet_NaN()) == 0);
  REQUIRE(glsl_uint_cast(std::numeric_limits<float>::quiet_NaN()) == 0U);

  // In-range finite values truncate toward zero, exactly as C++ would.
  REQUIRE(glsl_int_cast(1.9) == 1);
  REQUIRE(glsl_int_cast(-1.9) == -1);
  REQUIRE(glsl_int_cast(-0.9) == 0);
  REQUIRE(glsl_int_cast(2147483647.5) == 2147483647);
  REQUIRE(glsl_uint_cast(1.9) == 1U);
  REQUIRE(glsl_uint_cast(-0.9) == 0U);

  // Out-of-range finite values wrap modulo 2^32. `-12.5238` is the exact
  // value UBSan reported out of spookyTicker's `uint(cellX)`; the authority
  // yields `(-12.5238)|0 == -12`, while the C++ conversion saturates to 0 on
  // arm64 and wraps on x86-64.
  REQUIRE(glsl_uint_cast(-12.5238) == 4294967284U);
  // The exact shape UBSan reported, and the sign of zero, which the
  // authority erases: ToUint32(-1.9) truncates toward zero then wraps.
  REQUIRE(glsl_uint_cast(-1.9) == 4294967295U);
  REQUIRE(glsl_uint_cast(-0.0) == 0U);
  REQUIRE(glsl_int_cast(-0.0) == 0);
  REQUIRE(glsl_int_cast(-12.5238) == -12);
  REQUIRE(glsl_int_cast(2147483648.0) == INT32_MIN);
  REQUIRE(glsl_uint_cast(2147483648.0) == 2147483648U);
  REQUIRE(glsl_int_cast(-2147483649.0) == 2147483647);
  REQUIRE(glsl_uint_cast(-2147483649.0) == 2147483647U);
  REQUIRE(glsl_int_cast(3000000000.0) == -1294967296);
  REQUIRE(glsl_uint_cast(3000000000.0) == 3000000000U);
  REQUIRE(glsl_int_cast(4294967296.0) == 0);
  REQUIRE(glsl_uint_cast(4294967296.0) == 0U);
  REQUIRE(glsl_int_cast(-6000000000.0) == -1705032704);
  REQUIRE(glsl_uint_cast(-6000000000.0) == 2589934592U);
  REQUIRE(glsl_int_cast(1e300) == 0);
  REQUIRE(glsl_uint_cast(1e300) == 0U);
  REQUIRE(glsl_int_cast(-1e300) == 0);
  REQUIRE(glsl_uint_cast(-1e300) == 0U);

  // An operand that is already integral keeps the conversion it always had:
  // these sites are reinterpretations, not float narrowing, and the emitter
  // routes them through the same helper only so no cast site can be missed.
  REQUIRE(glsl_uint_cast(std::int32_t(-1)) == UINT32_MAX);
  REQUIRE(glsl_int_cast(std::uint32_t(4294967295U)) == -1);
  REQUIRE(glsl_uint_cast(std::int32_t(7)) == 7U);
  REQUIRE(glsl_int_cast(std::int32_t(INT32_MIN)) == INT32_MIN);
  REQUIRE(glsl_int_cast(true) == 1);
  REQUIRE(glsl_uint_cast(false) == 0U);
}

TEST(glsl_javascript_to_int32_and_bitwise_boundaries_are_exact) {
  using namespace noisemaker::glsl::detail;

  REQUIRE(js_to_int32(1.9) == 1);
  REQUIRE(js_to_int32(-1.9) == -1);
  REQUIRE(js_to_int32(-0.9) == 0);
  REQUIRE(js_to_int32(2147483648.0) == INT32_MIN);
  REQUIRE(js_to_int32(4294967295.0) == -1);
  REQUIRE(js_to_int32(4294967296.0) == 0);
  REQUIRE(js_to_int32(4294967297.0) == 1);
  REQUIRE(js_to_int32(-4294967295.0) == 1);
  REQUIRE(js_to_int32(-6000000000.0) == -1705032704);
  REQUIRE(js_to_int32(std::numeric_limits<double>::quiet_NaN()) == 0);
  REQUIRE(js_to_int32(std::numeric_limits<double>::infinity()) == 0);
  REQUIRE(js_to_int32(-std::numeric_limits<double>::infinity()) == 0);
  REQUIRE(js_to_int32(0.0) == 0);
  REQUIRE(js_to_int32(-0.0) == 0);

  REQUIRE(js_bitwise_or(1.9, 0.0) == 1);
  REQUIRE(js_bitwise_xor(2147483648.0, 0.0) == INT32_MIN);
  REQUIRE(js_bitwise_and(4294967295.0, -1.0) == -1);
  REQUIRE(js_bitwise_xor(
      std::numeric_limits<double>::quiet_NaN(),
      std::numeric_limits<double>::infinity()) == 0);
  REQUIRE(js_bitwise_not(std::numeric_limits<double>::infinity()) == -1);

  REQUIRE(js_bitwise_and(
      -2147483647.0 * -2147483647.0, -1.0) == 0);
  REQUIRE(js_bitwise_xor(0.0, -2000000000.0 * 3.0) == -1705032704);
  REQUIRE(js_bitwise_or(2147483647.0 + 1.0, 0.0) == INT32_MIN);
  REQUIRE(js_bitwise_and(-2147483648.0 - 1.0, -1.0) == INT32_MAX);
  REQUIRE(js_bitwise_not(4294967295.0) == 0);
}

TEST(glsl_javascript_signed_right_shift_matches_frozen_glyph_map_words) {
  using namespace noisemaker::glsl::detail;
  struct Fixture {
    double left;
    double count;
    double mask;
    std::int32_t shifted;
    std::int32_t masked;
  };
  constexpr Fixture fixtures[] = {
      {0.0, 0.0, 1.0, 0, 0},
      {1.0, 0.0, 1.0, 1, 1},
      {2147483647.0, 1.0, 1.0, 1073741823, 1},
      {-2147483648.0, 0.0, 1.0, INT32_MIN, 0},
      {-2147483648.0, 1.0, 1.0, -1073741824, 0},
      {-2147483648.0, 31.0, 1.0, -1, 1},
      {-1.0, 1.0, 1.0, -1, 1},
      {-1.0, 31.0, 1.0, -1, 1},
      {-1.0, 32.0, 1.0, -1, 1},
      {-1.0, 33.0, 1.0, -1, 1},
      {-1.0, -1.0, 1.0, -1, 1},
      {-2147483647.0, 4.0, 1.0, -134217728, 0},
      {-268435456.0, 4.0, 255.0, -16777216, 0},
      {305419896.0, 4.0, 255.0, 19088743, 103},
      {305419896.0, 36.0, 255.0, 19088743, 103},
      {-1431655766.0, 63.0, 1431655765.0, -1, 1431655765},
      {-559038737.0, 4294967295.0, -1.0, -1, -1},
  };
  for (const auto& fixture : fixtures) {
    const auto shifted = js_shift_right(fixture.left, fixture.count);
    REQUIRE(shifted == fixture.shifted);
    REQUIRE(js_bitwise_and(shifted, fixture.mask) == fixture.masked);
  }
}

TEST(glsl_javascript_unsigned_right_shift_preserves_pcg_logical_semantics) {
  using namespace noisemaker::glsl::detail;
  REQUIRE(js_logical_shift_right(0xe3ae4544, 28) == 14);
  REQUIRE(js_logical_shift_right(0x80000000, 1) == 0x40000000);
  REQUIRE(js_logical_shift_right(0xffffffff, 32) == 4294967295.0);
}

TEST(glsl_integer_remainder_is_defined_for_zero_and_signed_overflow) {
  using namespace noisemaker::glsl;
  REQUIRE(integer_mod(std::int32_t{7}, std::int32_t{3}) == 1);
  REQUIRE(integer_mod(std::int32_t{-7}, std::int32_t{3}) == -1);
  REQUIRE(integer_mod(INT32_MIN, std::int32_t{-1}) == 0);
  REQUIRE(integer_mod(std::int32_t{7}, std::int32_t{0}) == 0);
  REQUIRE(integer_mod(std::uint32_t{7}, std::uint32_t{0}) == 0U);
}

TEST(glsl_unary_negation_is_deferred_for_float_and_wrapping_for_int) {
  using namespace noisemaker::glsl;
  const auto expression = -Vec2(1.25f, -2.5f);
  const Vec2 stored = -expression;
  REQUIRE(stored == Vec2(1.25f, -2.5f));
  REQUIRE((-IVec2(INT32_MIN, 7)) == IVec2(INT32_MIN, -7));
  REQUIRE((-UVec2(0U, 1U)) == UVec2(0U, UINT32_MAX));
}

TEST(glsl_swizzles_are_typed_and_alias_safe) {
  using namespace noisemaker::glsl;
  Vec3 value(1.0f, 2.0f, 3.0f);
  REQUIRE(swizzle<2>(value) == 3.0f);
  REQUIRE((swizzle<2, 0>(value) == Vec2(3.0f, 1.0f)));
  set_swizzle<0, 1>(value, swizzle<1, 0>(value));
  REQUIRE(value == Vec3(2.0f, 1.0f, 3.0f));
}

TEST(glsl_matrices_are_column_major_and_multiply_with_storage_narrowing) {
  using namespace noisemaker::glsl;
  const Mat2 matrix(Vec2(1.0f, 2.0f), Vec2(3.0f, 4.0f));
  REQUIRE(matrix[0] == Vec2(1.0f, 2.0f));
  REQUIRE(matrix[1] == Vec2(3.0f, 4.0f));
  REQUIRE((matrix * Vec2(5.0f, 6.0f)) == Vec2(23.0f, 34.0f));
  REQUIRE((Vec2(5.0f, 6.0f) * matrix) == Vec2(17.0f, 39.0f));
  const Mat2 other(Vec2(2.0f, 1.0f), Vec2(0.0f, 3.0f));
  const Mat2 product = matrix * other;
  REQUIRE(product[0] == Vec2(5.0f, 8.0f));
  REQUIRE(product[1] == Vec2(9.0f, 12.0f));
  REQUIRE(Mat3(2.0f)[0] == Vec3(2.0f, 0.0f, 0.0f));
}

TEST(glsl_glitch_mat4_chain_matches_all_five_direct_oracles_and_mutants) {
  const auto t = glitch_mat4(kGlitchT);
  const auto s = glitch_mat4(kGlitchS);
  for (const auto& fixture : kGlitchMatrixCases) {
    const auto q = glitch_mat4(fixture.q);
    const auto first = glitch_mat4_words(t * q);
    REQUIRE(first == fixture.first);
    const auto final = glitch_mat4_words((t * q) * s);
    REQUIRE(final == fixture.final);
    REQUIRE(glitch_matrix_sha256(final) == fixture.final_sha256);

    const auto right_inner = glitch_rounded_product(fixture.q, kGlitchS);
    const auto right_associated =
        glitch_rounded_product(kGlitchT, right_inner);
    REQUIRE(glitch_mismatch_count(fixture.final, right_associated) ==
            fixture.right_associated_mismatches);

    const auto unrounded_first = glitch_unrounded_product(
        glitch_decode_matrix(kGlitchT), glitch_decode_matrix(fixture.q));
    const auto unrounded_final = glitch_narrow_matrix(
        glitch_unrounded_product(
            unrounded_first, glitch_decode_matrix(kGlitchS)));
    REQUIRE(glitch_mismatch_count(fixture.final, unrounded_final) ==
            fixture.unrounded_intermediate_mismatches);
  }
}

TEST(glsl_glitch_vec4_mat4_and_outer_dot_preserve_orientation_and_store) {
  using namespace noisemaker::glsl;
  constexpr std::array<std::uint32_t, 16> a_words{
      0xbf546cf0U, 0x3f3ea367U, 0x3fbea368U, 0xbfb93106U,
      0xbf7a8d9eU, 0x3f1882b9U, 0x3ff7d46dU, 0xbfdf51b4U,
      0x409df51bU, 0xc082b931U, 0xc04d9df6U, 0x409df51cU,
      0xc03d46cfU, 0x4015c988U, 0x4024c416U, 0xc055c988U};
  constexpr std::array<std::uint32_t, 4> tv_words{
      0x3f800000U, 0x3ebd70a4U, 0x3e0c2f84U, 0x3d4f7986U};
  constexpr std::array<std::uint32_t, 4> uv_words{
      0x3f800000U, 0x3f1c28f6U, 0x3ebe83e5U, 0x3e686db6U};
  constexpr std::array<std::uint32_t, 4> expected_vector{
      0xbed8e83fU, 0xbf14e45cU, 0x404f085bU, 0xbff44172U};
  constexpr std::array<std::uint32_t, 4> wrong_orientation_vector{
      0xbf2a7c24U, 0x3f063f65U, 0x3ff2baaaU, 0xbfcafae2U};
  const auto vec4_from_words = [](const std::array<std::uint32_t, 4>& words) {
    return Vec4(noisemaker::uint_bits_to_float(words[0]),
                noisemaker::uint_bits_to_float(words[1]),
                noisemaker::uint_bits_to_float(words[2]),
                noisemaker::uint_bits_to_float(words[3]));
  };
  const Mat4 a = glitch_mat4(a_words);
  const Vec4 tv = vec4_from_words(tv_words);
  const Vec4 uv = vec4_from_words(uv_words);

  const Vec4 production_vector = tv * a;
  for (std::size_t lane = 0; lane < 4U; ++lane)
    REQUIRE(noisemaker::float_bits_to_uint(production_vector[lane]) ==
            expected_vector[lane]);
  REQUIRE(noisemaker::float_bits_to_uint(
              dot(production_vector, uv)) == 0xbc00d72dU);

  std::array<double, 4> unrounded_vector{};
  for (std::size_t column = 0; column < 4U; ++column)
    for (std::size_t row = 0; row < 4U; ++row)
      unrounded_vector[column] +=
          static_cast<double>(tv[row]) * a[column][row];
  double missing_store_dot = 0.0;
  for (std::size_t lane = 0; lane < 4U; ++lane)
    missing_store_dot += unrounded_vector[lane] * uv[lane];
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::f32(missing_store_dot)) == 0xbc00d765U);
  REQUIRE(noisemaker::float_bits_to_uint(
              noisemaker::f32(missing_store_dot)) != 0xbc00d72dU);

  const Vec4 wrong_orientation = a * tv;
  for (std::size_t lane = 0; lane < 4U; ++lane)
    REQUIRE(noisemaker::float_bits_to_uint(wrong_orientation[lane]) ==
            wrong_orientation_vector[lane]);
  REQUIRE(noisemaker::float_bits_to_uint(
              dot(wrong_orientation, uv)) == 0xb9ccdd8dU);
  REQUIRE(wrong_orientation != production_vector);
}

TEST(glsl_glitch_ordered_splat_evaluates_rhs_twice_after_lane_zero_store) {
  using namespace noisemaker::glsl;
  const auto scalar = [](const Vec2& freq, std::size_t& calls,
                         std::uint32_t& second_call_lane_zero) {
    ++calls;
    if (calls == 2U) {
      second_call_lane_zero =
          noisemaker::float_bits_to_uint(swizzle<0>(freq));
    }
    return noisemaker::f32(static_cast<double>(swizzle<0>(freq))
                           + 0.5 * static_cast<double>(swizzle<1>(freq)));
  };

  Vec2 canonical(2.0f, 3.0f);
  std::size_t canonical_calls = 0U;
  std::uint32_t observed_lane_zero = 0U;
  set_swizzle<0>(canonical, swizzle<0>(canonical)
      * scalar(canonical, canonical_calls, observed_lane_zero));
  set_swizzle<1>(canonical, swizzle<1>(canonical)
      * scalar(canonical, canonical_calls, observed_lane_zero));
  REQUIRE(canonical_calls == 2U);
  REQUIRE(observed_lane_zero == 0x40e00000U);
  REQUIRE(canonical == Vec2(7.0f, 25.5f));

  Vec2 broadcast(2.0f, 3.0f);
  std::size_t broadcast_calls = 0U;
  std::uint32_t ignored = 0U;
  const float broadcast_scalar = scalar(
      broadcast, broadcast_calls, ignored);
  broadcast = Vec2(broadcast * broadcast_scalar);
  REQUIRE(broadcast_calls == 1U);
  REQUIRE(broadcast == Vec2(7.0f, 10.5f));
  REQUIRE(broadcast != canonical);

  Vec2 cached(2.0f, 3.0f);
  std::size_t cached_calls = 0U;
  const float cached_scalar = scalar(cached, cached_calls, ignored);
  set_swizzle<0>(cached, swizzle<0>(cached) * cached_scalar);
  set_swizzle<1>(cached, swizzle<1>(cached) * cached_scalar);
  REQUIRE(cached_calls == 1U);
  REQUIRE(cached == broadcast);
  REQUIRE(cached != canonical);

  Vec2 reversed(2.0f, 3.0f);
  std::size_t reversed_calls = 0U;
  set_swizzle<1>(reversed, swizzle<1>(reversed)
      * scalar(reversed, reversed_calls, ignored));
  set_swizzle<0>(reversed, swizzle<0>(reversed)
      * scalar(reversed, reversed_calls, ignored));
  REQUIRE(reversed_calls == 2U);
  REQUIRE(reversed == Vec2(14.5f, 10.5f));
  REQUIRE(reversed != canonical);
}

// Task 30: the exact bvec2 relational/reduction pair Extrude needs. Only the
// two-lane width is instantiable; bvec3/bvec4 relational reduction must remain
// a compile error, not merely an untested path.
TEST(glsl_lane_wise_less_than_equal_and_all_reduce_exactly_two_lanes) {
  using namespace noisemaker::glsl;
  REQUIRE((lessThanEqual(Vec2(1.0f, 2.0f), Vec2(1.0f, 3.0f)) == BVec2(true, true)));
  REQUIRE((lessThanEqual(Vec2(1.0f, 4.0f), Vec2(1.0f, 3.0f)) == BVec2(true, false)));
  REQUIRE((lessThanEqual(Vec2(5.0f, 4.0f), Vec2(1.0f, 3.0f)) == BVec2(false, false)));

  REQUIRE(all(BVec2(true, true)));
  REQUIRE(!all(BVec2(true, false)));
  REQUIRE(!all(BVec2(false, true)));
  REQUIRE(!all(BVec2(false, false)));

  // Equality is inclusive: this is <=, not <. The oracle mutation that swaps
  // lessThanEqual for lessThan is discriminated exactly here.
  REQUIRE(all(lessThanEqual(Vec2(2.0f, 2.0f), Vec2(2.0f, 2.0f))));

  // -0.0 <= 0.0 and 0.0 <= -0.0 both hold under IEEE comparison.
  REQUIRE(all(lessThanEqual(Vec2(-0.0f, 0.0f), Vec2(0.0f, -0.0f))));

  // NaN compares false in every lane, so the reduction is false.
  const float nan = std::numeric_limits<float>::quiet_NaN();
  REQUIRE(!all(lessThanEqual(Vec2(nan, 1.0f), Vec2(1.0f, 1.0f))));
}

TEST(glsl_lane_wise_equal_materializes_float_expr_and_supports_only_two_lanes) {
  using namespace noisemaker::glsl;

  REQUIRE((equal(Vec2(1.0f, 2.0f), Vec2(1.0f, 2.0f)) ==
           BVec2(true, true)));
  REQUIRE((equal(Vec2(1.0f, 2.0f), Vec2(1.0f, 3.0f)) ==
           BVec2(true, false)));
  REQUIRE((equal(Vec2(1.0f, 2.0f), Vec2(4.0f, 2.0f)) ==
           BVec2(false, true)));
  REQUIRE((equal(Vec2(1.0f, 2.0f), Vec2(4.0f, 3.0f)) ==
           BVec2(false, false)));

  REQUIRE((equal(Vec2(+0.0f, -0.0f), Vec2(-0.0f, +0.0f)) ==
           BVec2(true, true)));
  const float infinity = std::numeric_limits<float>::infinity();
  REQUIRE((equal(Vec2(infinity, -infinity),
                 Vec2(infinity, -infinity)) == BVec2(true, true)));
  REQUIRE((equal(Vec2(infinity, -infinity),
                 Vec2(-infinity, infinity)) == BVec2(false, false)));

  const float nan = std::numeric_limits<float>::quiet_NaN();
  REQUIRE((equal(Vec2(nan, 1.0f), Vec2(nan, 1.0f)) ==
           BVec2(false, true)));
  const float adjacent = noisemaker::uint_bits_to_float(0x3f800001U);
  REQUIRE((equal(Vec2(1.0f, adjacent), Vec2(adjacent, 1.0f)) ==
           BVec2(false, false)));

  // The canonical typed-array comparison first materializes both deferred
  // Number lanes as Float32. Comparing these FloatExpr values as binary64
  // would incorrectly report both lanes unequal.
  const Vec2 rounded(0.1f, 0.2f);
  const FloatExpr<2> deferred(0.1, 0.2);
  REQUIRE((equal(rounded, deferred) == BVec2(true, true)));
  REQUIRE((equal(deferred, rounded) == BVec2(true, true)));
  REQUIRE((equal(deferred, FloatExpr<2>(0.1, 0.2)) ==
           BVec2(true, true)));
}

// Reserved-identifier guard: a GLSL local or parameter named `state`,
// `context`, or `output` must not shadow the emitter's own kernel bindings.
// Ten unported corpus programs declare a local named `state`; before the guard
// existed the emitted C++ failed to compile with
//   "redefinition of 'state' with a different type: 'glsl::UVec3' vs 'const State &'".
// This test pins the C++-side invariant that the reserved names remain usable
// as distinct entities in one scope.
TEST(glsl_reserved_emitter_identifiers_do_not_collide_with_mangled_locals) {
  using namespace noisemaker::glsl;
  struct FakeState { int seed; };
  const FakeState state{7};
  const UVec3 state_1(1U, 2U, 3U);
  REQUIRE(state.seed == 7);
  REQUIRE(state_1[0] == 1U);
  REQUIRE(state_1[2] == 3U);
}
