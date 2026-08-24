#include "test_harness.hpp"

#include <array>
#include <cmath>
#include <functional>
#include <memory>
#include <string>
#include <type_traits>

#include "noisemaker/glsl_runtime.hpp"

namespace {
template <class Left, class Right>
concept HasGlslMod = requires(const Left& left, const Right& right) {
  noisemaker::glsl::mod(left, right);
};

template <class Incident, class Normal>
concept HasGlslReflect = requires(const Incident& incident, const Normal& normal) {
  noisemaker::glsl::reflect(incident, normal);
};

template <class Incident, class Normal, class Eta>
concept HasGlslRefract = requires(const Incident& incident, const Normal& normal,
                                  const Eta& eta) {
  noisemaker::glsl::refract(incident, normal, eta);
};

template <class Left, class Right>
concept HasGlslPow = requires(const Left& left, const Right& right) {
  noisemaker::glsl::pow(left, right);
};

template <class Value>
concept HasGlslTanh = requires(const Value& value) {
  noisemaker::glsl::tanh(value);
};

static_assert(HasGlslMod<noisemaker::glsl::Vec2, noisemaker::glsl::Vec2>);
static_assert(HasGlslMod<noisemaker::glsl::Vec2, double>);
static_assert(HasGlslMod<noisemaker::glsl::FloatExpr<2>, noisemaker::glsl::Vec2>);
static_assert(HasGlslMod<noisemaker::glsl::FloatExpr<2>, double>);
static_assert(!HasGlslMod<noisemaker::glsl::Vec2, noisemaker::glsl::FloatExpr<2>>);
static_assert(!HasGlslMod<noisemaker::glsl::FloatExpr<2>, noisemaker::glsl::FloatExpr<2>>);
static_assert(!HasGlslMod<double, noisemaker::glsl::Vec2>);
static_assert(!HasGlslMod<noisemaker::glsl::Vec3, noisemaker::glsl::Vec3>);
// Task 31 (Curl) widened `mod` to vec3/vec4-BY-SCALAR only — the exact shapes
// the authorized closure invokes. Vector-by-vector at those widths stays
// banned, so this remains a real width policy rather than a blanket opening.
static_assert(HasGlslMod<noisemaker::glsl::Vec3, double>);
static_assert(HasGlslMod<noisemaker::glsl::Vec4, double>);
static_assert(HasGlslMod<noisemaker::glsl::FloatExpr<3>, double>);
static_assert(HasGlslMod<noisemaker::glsl::FloatExpr<4>, double>);
static_assert(!HasGlslMod<noisemaker::glsl::Vec4, noisemaker::glsl::Vec4>);
static_assert(!HasGlslMod<noisemaker::glsl::Vec3, noisemaker::glsl::FloatExpr<3>>);
static_assert(!HasGlslReflect<double, double>);
static_assert(!HasGlslRefract<double, double, double>);
// tanh is authorized at vec3 only, for the single Curl call site.
static_assert(HasGlslTanh<noisemaker::glsl::Vec3>);
static_assert(HasGlslTanh<noisemaker::glsl::FloatExpr<3>>);
static_assert(!HasGlslTanh<noisemaker::glsl::Vec2>);
static_assert(!HasGlslTanh<noisemaker::glsl::Vec4>);
static_assert(std::is_same_v<decltype(noisemaker::glsl::mod(1.0, 1.0)), float>);
static_assert(HasGlslPow<noisemaker::glsl::Vec3, noisemaker::glsl::FloatExpr<3>>);

template <std::size_t N>
void require_vector_bits(const noisemaker::glsl::Vec<N, float>& actual,
                         const std::array<std::uint32_t, N>& expected) {
  for (std::size_t lane = 0; lane < N; ++lane) {
    REQUIRE(noisemaker::float_bits_to_uint(actual[lane]) == expected[lane]);
  }
}

void require_binding_message(const std::function<void()>& action, const std::string& expected) {
  try { action(); } catch (const noisemaker::glsl::KernelBindingError& error) {
    REQUIRE(std::string(error.what()).find(expected) != std::string::npos);
    return;
  }
  REQUIRE(false);
}
}  // namespace

TEST(glsl_runtime_mod_fract_and_round_match_glsl_contract) {
  using namespace noisemaker::glsl;
  REQUIRE(mod(-1.0, 3.0) == 2.0);
  REQUIRE(fract(-1.25) == 0.75);
  REQUIRE(noisemaker::glsl::round(1.5) == 2.0);
  REQUIRE(noisemaker::glsl::round(-1.5) == -1.0);
  REQUIRE(noisemaker::glsl::round(-0.5) == 0.0);
}

TEST(glsl_runtime_mod_covers_scalar_vector_expression_and_javascript_boundaries) {
  using namespace noisemaker::glsl;
  REQUIRE(mod(-5.5, 2.25) == 1.25);
  REQUIRE(mod(5.5, -2.25) == -1.25);
  REQUIRE(mod(Vec2(-5.5f, 5.5f), Vec2(2.25f, -2.25f)) == Vec2(1.25f, -1.25f));
  REQUIRE(mod(Vec2(-5.5f, 5.5f), 2.25) == Vec2(1.25f, 1.0f));
  REQUIRE(abs(mod(Vec2(-2.25f, 2.25f) + 1.0, 2.0) - 1.0) == Vec2(0.25f));

  // A vector builtin consumes the pending FloatExpr at a Float32 boundary.
  REQUIRE(mod(Vec2(16777216.0f, 1.0f) + 1.0, 3.0) == Vec2(1.0f, 2.0f));
  const Vec2 narrowed = mod(Vec2(0.3f, -0.3f), 0.2f);
  REQUIRE(noisemaker::float_bits_to_uint(narrowed[0]) == 0x3dccccceU);
  REQUIRE(noisemaker::float_bits_to_uint(narrowed[1]) == 0x3dccccccU);

  REQUIRE(noisemaker::float_bits_to_uint(static_cast<float>(mod(-0.0, 3.0))) == 0U);
  REQUIRE(std::isnan(mod(1.0, 0.0)));
  REQUIRE(std::isnan(mod(1.0, std::numeric_limits<double>::infinity())));
  REQUIRE(std::isnan(mod(std::numeric_limits<double>::infinity(), 2.0)));
  REQUIRE(std::isnan(mod(std::numeric_limits<double>::quiet_NaN(), 2.0)));
}

TEST(glsl_runtime_geometric_helpers_handle_nonzero_zero_and_total_internal_reflection) {
  using namespace noisemaker::glsl;
  REQUIRE(dot(Vec2(3.0f, 4.0f), Vec2(1.0f, 2.0f)) == 11.0f);
  REQUIRE(dot(Vec2(1.0f, 2.0f) + 0.5, Vec2(2.0f, 2.0f)) == 8.0f);
  REQUIRE(length(Vec2(3.0f, 4.0f)) == 5.0f);
  REQUIRE(normalize(Vec2()) == Vec2());
  REQUIRE(normalize(Vec2(3.0f, 4.0f)) == Vec2(0.6f, 0.8f));
  const Vec2 sentinel(-5968.8544921875f, 15943.099609375f);
  REQUIRE(noisemaker::float_bits_to_uint(normalize(sentinel)[0]) == 3199435837U);
  REQUIRE(noisemaker::float_bits_to_uint(normalize(sentinel + 0.0)[0]) == 3199435837U);
  REQUIRE(cross(Vec3(1.0f, 0.0f, 0.0f), Vec3(0.0f, 1.0f, 0.0f)) == Vec3(0.0f, 0.0f, 1.0f));
  REQUIRE(reflect(Vec2(1.0f, -1.0f), Vec2(0.0f, 1.0f)) == Vec2(1.0f, 1.0f));
  REQUIRE(reflect(Vec2(1.0f, -1.0f) + 0.0, Vec2(0.0f, 1.0f)) == Vec2(1.0f, 1.0f));
  REQUIRE(refract(Vec2(1.0f, 0.0f), Vec2(0.0f, 1.0f), 2.0) == Vec2());
}

TEST(glsl_runtime_reflect_and_refract_stage_shared_vector_float32_writes) {
  using namespace noisemaker::glsl;
  const Vec3 incident(
      noisemaker::uint_bits_to_float(0x408c4d65U),
      noisemaker::uint_bits_to_float(0xc0407fe6U),
      noisemaker::uint_bits_to_float(0xc0ecaf78U));
  const Vec3 normal(
      noisemaker::uint_bits_to_float(0xc07d065bU),
      noisemaker::uint_bits_to_float(0x4082a176U),
      noisemaker::uint_bits_to_float(0xc002ca11U));
  const auto incident_expression = incident + 0.0;
  const auto normal_expression = normal + 0.0;
  const std::array reflect_bits{0xc2dc7dddU, 0x42e6b53bU, 0xc2854c5fU};
  require_vector_bits(reflect(incident, normal), reflect_bits);
  require_vector_bits(reflect(incident_expression, normal), reflect_bits);
  require_vector_bits(reflect(incident, normal_expression), reflect_bits);
  require_vector_bits(reflect(incident_expression, normal_expression), reflect_bits);
  const double rejected_reflect_scale =
      2.0 * static_cast<double>(dot(normal, incident));
  Vec3 rejected_one_narrow_reflect;
  for (std::size_t lane = 0; lane < 3; ++lane) {
    rejected_one_narrow_reflect[lane] = noisemaker::f32(
        static_cast<double>(incident[lane]) -
        rejected_reflect_scale * static_cast<double>(normal[lane]));
  }
  require_vector_bits(rejected_one_narrow_reflect,
                      std::array{0xc2dc7ddcU, 0x42e6b53bU, 0xc2854c5fU});
  REQUIRE(noisemaker::float_bits_to_uint(rejected_one_narrow_reflect[0]) !=
          reflect_bits[0]);

  const Vec3 refract_incident(
      noisemaker::uint_bits_to_float(0xbfdc1c58U),
      noisemaker::uint_bits_to_float(0xbe8bbd72U),
      noisemaker::uint_bits_to_float(0x3fbd4587U));
  const Vec3 refract_normal(
      noisemaker::uint_bits_to_float(0xbf89dd86U),
      noisemaker::uint_bits_to_float(0x3acd6835U),
      noisemaker::uint_bits_to_float(0xbf12d8d2U));
  const auto refract_incident_expression = refract_incident + 0.0;
  const auto refract_normal_expression = refract_normal + 0.0;
  constexpr double eta = 0.6234136876035227;
  const std::array refract_bits{0x3f2e2accU, 0xbe30d7b3U, 0x3fed73e8U};
  require_vector_bits(refract(refract_incident, refract_normal, eta), refract_bits);
  require_vector_bits(refract(refract_incident_expression, refract_normal, eta), refract_bits);
  require_vector_bits(refract(refract_incident, refract_normal_expression, eta), refract_bits);
  require_vector_bits(refract(refract_incident_expression, refract_normal_expression, eta),
                      refract_bits);
  const double rejected_refract_cosine =
      static_cast<double>(dot(refract_normal, refract_incident));
  const double rejected_refract_discriminant =
      1.0 - eta * eta *
                (1.0 - rejected_refract_cosine * rejected_refract_cosine);
  const double rejected_refract_scale =
      eta * rejected_refract_cosine + std::sqrt(rejected_refract_discriminant);
  Vec3 rejected_one_narrow_refract;
  for (std::size_t lane = 0; lane < 3; ++lane) {
    rejected_one_narrow_refract[lane] = noisemaker::f32(
        eta * static_cast<double>(refract_incident[lane]) -
        rejected_refract_scale * static_cast<double>(refract_normal[lane]));
  }
  require_vector_bits(rejected_one_narrow_refract,
                      std::array{0x3f2e2acbU, 0xbe30d7b2U, 0x3fed73e8U});
  REQUIRE(noisemaker::float_bits_to_uint(rejected_one_narrow_refract[0]) !=
          refract_bits[0]);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_one_narrow_refract[1]) !=
          refract_bits[1]);

  require_vector_bits(refract(Vec2(1.0f, 0.0f), Vec2(0.0f, 1.0f), 2.0),
                      std::array{0x00000000U, 0x00000000U});
  require_vector_bits(refract(Vec2(1.0f, 0.0f), Vec2(0.0f, 1.0f), 1.0),
                      std::array{0x3f800000U, 0x00000000U});
  require_vector_bits(refract(Vec2(0.0f, -1.0f), Vec2(0.0f, 1.0f), 0.5),
                      std::array{0x00000000U, 0xbf800000U});
  require_vector_bits(refract(Vec2(-0.0f, 0.0f), Vec2(0.0f, 1.0f), 1.0),
                      std::array{0x80000000U, 0x00000000U});
  const Vec2 nan_refracted = refract(
      Vec2(1.0f, 0.0f), Vec2(0.0f, 1.0f),
      std::numeric_limits<double>::quiet_NaN());
  REQUIRE(std::isnan(nan_refracted[0]));
  REQUIRE(std::isnan(nan_refracted[1]));
}

TEST(glsl_runtime_shape_mixer_scalar_geometry_and_vec3_mod_match_javascript_staging) {
  using namespace noisemaker::glsl;
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_reflect_scalar(-0.0, 1.0)) ==
          0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_reflect_scalar(-0.0, -1.0)) ==
          0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_reflect_scalar(1.25, -0.5)) ==
          0x3fa00000U);
  const float rejected_mathematical_scalar_reflect = noisemaker::f32(
      1.25 - 2.0 * (-0.5 * 1.25) * -0.5);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_mathematical_scalar_reflect) ==
          0x3f200000U);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_mathematical_scalar_reflect) !=
          noisemaker::float_bits_to_uint(
              shape_mixer_reflect_scalar(1.25, -0.5)));

  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_refract_scalar(-0.0, 1.0, 0.0)) ==
          0xbf800000U);
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_refract_scalar(-0.0, -1.0, 1.0)) ==
          0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_refract_scalar(1.25, -0.5, 0.25)) ==
          0x3f4bef7bU);
  REQUIRE(noisemaker::float_bits_to_uint(shape_mixer_refract_scalar(
              noisemaker::uint_bits_to_float(0xc09a3ceaU),
              noisemaker::uint_bits_to_float(0xc09b847cU), 0.125)) ==
          0x4087049dU);
  const double staged_refract_incident = static_cast<double>(
      noisemaker::uint_bits_to_float(0xc09a3ceaU));
  const double staged_refract_normal = static_cast<double>(
      noisemaker::uint_bits_to_float(0xc09b847cU));
  constexpr double staged_refract_eta = 0.125;
  const double staged_refract_discriminant =
      1.0 - staged_refract_eta * staged_refract_eta;
  const float rejected_one_narrow_scalar_refract = noisemaker::f32(
      staged_refract_incident * staged_refract_eta -
      staged_refract_normal * std::sqrt(staged_refract_discriminant));
  REQUIRE(noisemaker::float_bits_to_uint(rejected_one_narrow_scalar_refract) ==
          0x4087049cU);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_one_narrow_scalar_refract) !=
          noisemaker::float_bits_to_uint(shape_mixer_refract_scalar(
              staged_refract_incident, staged_refract_normal,
              staged_refract_eta)));
  REQUIRE(std::isnan(shape_mixer_refract_scalar(
      1.0, 1.0, std::numeric_limits<double>::quiet_NaN())));

  const Vec3 modded = shape_mixer_mod_vec3(
      Vec3(-5.5f, 5.5f, -0.0f), Vec3(2.25f, -2.25f, 3.0f));
  require_vector_bits(modded, std::array{0x3fa00000U, 0xbfa00000U, 0x00000000U});
  const Vec3 rejected_fmod(
      noisemaker::f32(std::fmod(-5.5, 2.25)),
      noisemaker::f32(std::fmod(5.5, -2.25)),
      noisemaker::f32(std::fmod(-0.0, 3.0)));
  require_vector_bits(rejected_fmod,
                      std::array{0xbf800000U, 0x3f800000U, 0x80000000U});
  REQUIRE(rejected_fmod != modded);
  const Vec3 fractional = shape_mixer_mod_vec3(
      Vec3(0.3f, 0.0f, 0.0f), Vec3(0.2f, 1.0f, 1.0f));
  REQUIRE(noisemaker::float_bits_to_uint(fractional[0]) == 0x3dccccceU);
  constexpr double divisor_factor = 1.234567;
  const float divisor_base = noisemaker::uint_bits_to_float(0x3c90fdbcU);
  const auto divisor_expression = Vec3(divisor_base, 1.0f, 1.0f) * divisor_factor;
  const Vec3 materialized_divisor = shape_mixer_mod_vec3(
      Vec3(noisemaker::uint_bits_to_float(0xc211f4caU), 0.0f, 0.0f),
      divisor_expression);
  REQUIRE(noisemaker::float_bits_to_uint(materialized_divisor[0]) == 0x3add3f80U);
  const float rejected_unmaterialized_divisor = mod(
      static_cast<double>(noisemaker::uint_bits_to_float(0xc211f4caU)),
      static_cast<double>(divisor_base) * divisor_factor);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_unmaterialized_divisor) ==
          0x3add70e9U);
  REQUIRE(noisemaker::float_bits_to_uint(rejected_unmaterialized_divisor) !=
          noisemaker::float_bits_to_uint(materialized_divisor[0]));
}

TEST(glsl_runtime_component_helpers_work_for_scalars_and_vectors) {
  using namespace noisemaker::glsl;
  REQUIRE(component_min(2.0f, 3.0f) == 2.0f);
  REQUIRE(component_max(2.0f, 3.0f) == 3.0f);
  REQUIRE(clamp(-1.0f, 0.0f, 1.0f) == 0.0f);
  REQUIRE(mix(2.0f, 6.0f, 0.25f) == 3.0f);
  REQUIRE(step(0.5f, 0.5f) == 1.0f);
  REQUIRE(smoothstep(0.0f, 1.0f, 0.5f) == 0.5f);
  REQUIRE(component_min(Vec3(2.0f, 5.0f, -1.0f), 1.0f) == Vec3(1.0f, 1.0f, -1.0f));
  REQUIRE(clamp(Vec2(-1.0f, 2.0f), 0.0f, 1.0f) == Vec2(0.0f, 1.0f));
  REQUIRE(mix(Vec2(0.0f, 4.0f), Vec2(2.0f, 8.0f), 0.25f) == Vec2(0.5f, 5.0f));
  REQUIRE(step(0.0f, Vec2(-1.0f, 0.0f)) == Vec2(0.0f, 1.0f));
  REQUIRE(smoothstep(0.0f, 1.0f, Vec2(0.25f, 0.75f)) == Vec2(0.15625f, 0.84375f));
  REQUIRE(clamp(Vec2(-1.0f, 2.0f), 0.0, 1.0) == Vec2(0.0f, 1.0f));
  REQUIRE(mix(Vec2(0.0f, 4.0f), Vec2(2.0f, 8.0f), 0.5) == Vec2(1.0f, 6.0f));
  REQUIRE(step(0.0, Vec2(-1.0f, 0.0f)) == Vec2(0.0f, 1.0f));
  REQUIRE(smoothstep(0.0, 1.0, Vec2(0.25f, 0.75f)) == Vec2(0.15625f, 0.84375f));
  const auto expression = Vec2(-0.25f, 1.25f) + 0.0;
  REQUIRE(component_min(expression, Vec2(0.0f, 1.0f)) == Vec2(-0.25f, 1.0f));
  REQUIRE(component_max(Vec2(-1.0f, 0.5f), expression) == Vec2(-0.25f, 1.25f));
  REQUIRE(clamp(expression, 0.0f, 1.0f) == Vec2(0.0f, 1.0f));
  REQUIRE(mix(expression, Vec2(0.0f, 0.0f), 0.5f) == Vec2(-0.125f, 0.625f));
  REQUIRE(step(0.0f, expression) == Vec2(0.0f, 1.0f));
  REQUIRE(smoothstep(0.0f, 1.0f, expression) == Vec2(0.0f, 1.0f));
  REQUIRE(mix(expression, expression + 1.0, 0.5) == Vec2(0.25f, 1.75f));
}

TEST(glsl_runtime_scalar_smoothstep_narrows_once_after_double_intermediates) {
  const float value = noisemaker::glsl::smoothstep(0.27f, 0.63f, 0.418f);
  REQUIRE(noisemaker::float_bits_to_uint(value) == 0x3ebc73daU);
}

TEST(glsl_component_min_max_match_js_nan_and_signed_zero_rules) {
  using namespace noisemaker::glsl;
  const float nan = std::numeric_limits<float>::quiet_NaN();
  REQUIRE(std::isnan(component_min(nan, 1.0f)));
  REQUIRE(std::isnan(component_max(1.0f, nan)));
  REQUIRE(noisemaker::float_bits_to_uint(component_min(0.0f, -0.0f)) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(component_min(-0.0f, 0.0f)) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(component_max(0.0f, -0.0f)) == 0U);
  REQUIRE(noisemaker::float_bits_to_uint(component_max(-0.0f, 0.0f)) == 0U);
  const Vec2 vector_min = component_min(Vec2(nan, 0.0f), Vec2(1.0f, -0.0f));
  REQUIRE(std::isnan(vector_min[0]));
  REQUIRE(noisemaker::float_bits_to_uint(vector_min[1]) == 0x80000000U);
}

TEST(glsl_runtime_straight_line_math_helpers_cover_scalar_vector_and_boundaries) {
  using namespace noisemaker::glsl;
  const float nan = std::numeric_limits<float>::quiet_NaN();
  REQUIRE(abs(Vec2(-2.0f, 3.0f)) == Vec2(2.0f, 3.0f));
  REQUIRE(floor(Vec2(-1.25f, 2.75f)) == Vec2(-2.0f, 2.0f));
  REQUIRE(fract(Vec2(-1.25f, 2.75f)) == Vec2(0.75f, 0.75f));
  REQUIRE(sign(Vec3(-2.0f, -0.0f, 3.0f)) == Vec3(-1.0f, 0.0f, 1.0f));
  REQUIRE(distance(Vec2(0.0f, 0.0f), Vec2(3.0f, 4.0f)) == 5.0f);
  REQUIRE(normalize(Vec2()) == Vec2());
  REQUIRE(atan(0.0f, -1.0f) > 3.1415925f);
  REQUIRE(noisemaker::float_bits_to_uint(radians(180.0f)) == noisemaker::float_bits_to_uint(3.1415927410125732f));
  REQUIRE(std::isnan(component_min(nan, 1.0f)));
  REQUIRE(noisemaker::float_bits_to_uint(component_min(0.0f, -0.0f)) == 0x80000000U);
  REQUIRE(noisemaker::float_bits_to_uint(component_max(0.0f, -0.0f)) == 0U);
  const Vec2 trig = cos(Vec2(0.0f, 0.0f)) + sin(Vec2(0.0f, 0.0f));
  REQUIRE(trig == Vec2(1.0f));
  REQUIRE(sqrt(Vec2(4.0f, 9.0f)) == Vec2(2.0f, 3.0f));
  REQUIRE(pow(Vec2(2.0f, 3.0f), 2.0f) == Vec2(4.0f, 9.0f));
  REQUIRE(pow(Vec3(4.0f, 9.0f, 16.0f), Vec3(0.5f) + 0.0) ==
          Vec3(2.0f, 3.0f, 4.0f));
}

TEST(glsl_bindings_enforce_exact_uniform_types_and_missing_fallbacks) {
  using namespace noisemaker::glsl;
  Bindings bindings;
  bindings.set_uniform("time", 1.25f);
  REQUIRE(bindings.get_or<float>("time", 0.0f) == 1.25f);
  REQUIRE(bindings.get_or<Vec2>("uv", Vec2(2.0f)) == Vec2(2.0f));
  require_binding_message([&] { static_cast<void>(bindings.get_or<std::int32_t>("time", 0)); }, "uniform binding 'time'");
  require_binding_message([&] { bindings.set_uniform("", 1.0f); }, "uniform");
}

TEST(glsl_bindings_preserve_number_uniforms_and_widen_legacy_float_bindings) {
  using namespace noisemaker::glsl;
  Bindings bindings;
  bindings.set_uniform("exact", 0.15);
  bindings.set_uniform("legacy", 0.15f);
  REQUIRE(bindings.get_number("exact") == 0.15);
  REQUIRE(bindings.get_number("legacy") == static_cast<double>(0.15f));
  require_binding_message([&] { static_cast<void>(bindings.get_number("missing")); },
                          "uniform binding 'missing'");
  bindings.set_uniform("wrong", std::int32_t{1});
  require_binding_message([&] { static_cast<void>(bindings.get_number("wrong")); },
                          "uniform binding 'wrong'");
}

TEST(glsl_bindings_store_nonowning_texture_references_and_report_missing_samplers) {
  using namespace noisemaker::glsl;
  noisemaker::Surface surface(1, 1);
  Bindings bindings;
  bindings.set_texture("input", surface);
  REQUIRE(std::addressof(bindings.texture("input")) == std::addressof(surface));
  require_binding_message([&] { static_cast<void>(bindings.texture("missing")); }, "sampler binding 'missing'");
  require_binding_message([&] { bindings.set_texture("", surface); }, "sampler");
}

TEST(glsl_pixel_context_defaults_to_zero) {
  const noisemaker::glsl::PixelContext context;
  REQUIRE(context.uv == noisemaker::glsl::Vec2());
  REQUIRE(context.frag_coord == noisemaker::glsl::Vec4());
  REQUIRE(context.resolution == noisemaker::glsl::Vec2());
  REQUIRE(context.time == 0.0f);
  REQUIRE(context.seed == 0.0f);
  REQUIRE(context.frame == 0U);
  REQUIRE(context.delta_time == 0.0f);
}

// Task 31 (Curl): tanh on vec3 and GLSL mod at vec3/vec4-by-scalar widths.
// GLSL mod is x - y*floor(x/y) (sign of y), NOT C fmod (sign of x); the
// negative-operand rows below are where a naive fmod port breaks.
TEST(glsl_tanh_vec3_and_wide_mod_match_glsl_semantics) {
  using namespace noisemaker::glsl;
  const Vec3 t = tanh(Vec3(0.0f, 1.0f, -1.0f));
  REQUIRE(t[0] == 0.0f);
  REQUIRE(t[1] == noisemaker::f32(std::tanh(1.0)));
  REQUIRE(t[2] == noisemaker::f32(std::tanh(-1.0)));

  // Positive dividends: GLSL mod and fmod agree.
  REQUIRE((mod(Vec3(7.0f, 289.0f, 290.0f), 289.0) == Vec3(7.0f, 0.0f, 1.0f)));

  // Negative dividends: GLSL mod takes the sign of the divisor, fmod does not.
  // fmod(-1, 289) == -1; GLSL mod(-1, 289) == 288.
  REQUIRE((mod(Vec3(-1.0f, -289.0f, -290.0f), 289.0) == Vec3(288.0f, 0.0f, 288.0f)));
  REQUIRE((mod(Vec4(-1.0f, -2.0f, 3.0f, -289.0f), 289.0) ==
           Vec4(288.0f, 287.0f, 3.0f, 0.0f)));
}
