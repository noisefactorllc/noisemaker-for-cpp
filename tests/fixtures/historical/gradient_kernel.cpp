// Frozen Gradient alias behavior for its authenticated historical oracle.
#include "gradient_kernel.hpp"
#include <cmath>
#include <cstdint>
#include <memory>
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
namespace noisemaker::historical_generated {
// Typed IR program: synth/gradient:gradient
// Source SHA-256: 308537be8f376750a2239be89a07e558e54ee1661a0ea360c6a3e48b8c6e7a75
namespace typed_gradient_historical {
struct State final : KernelState {
  State(glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, std::int32_t gradientType_value, double rotation_value, std::int32_t repeat_value, std::int32_t colorCount_value, glsl::DVec3 color1_value, glsl::DVec3 color2_value, glsl::DVec3 color3_value, glsl::DVec3 color4_value, std::int32_t seed_value, double time_value, double speed_value) : resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), gradientType(gradientType_value), rotation(rotation_value), repeat(repeat_value), colorCount(colorCount_value), color1(color1_value), color2(color2_value), color3(color3_value), color4(color4_value), seed(seed_value), time(time_value), speed(speed_value) {}
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  std::int32_t gradientType;
  double rotation;
  std::int32_t repeat;
  std::int32_t colorCount;
  glsl::DVec3 color1;
  glsl::DVec3 color2;
  glsl::DVec3 color3;
  glsl::DVec3 color4;
  std::int32_t seed;
  double time;
  double speed;
};

[[nodiscard]] glsl::Vec4 sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {
  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);
  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);
}
[[nodiscard]] glsl::Vec4 fetch_texel(const Surface& surface, const glsl::IVec2& coord) noexcept {
  const Rgba sample = texel_fetch_bottom_left(surface, coord[0], coord[1]);
  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);
}
[[nodiscard]] glsl::IVec2 texture_size(const Surface& surface) noexcept {
  return glsl::IVec2(static_cast<std::int32_t>(surface.width()), static_cast<std::int32_t>(surface.height()));
}

[[nodiscard]] glsl::Vec3 blendColors([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double t) noexcept;
[[nodiscard]] double fbmNoise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept;
[[nodiscard]] glsl::DVec3 getColor([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t idx) noexcept;
[[nodiscard]] double hash2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept;
[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept;
[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept;
[[nodiscard]] glsl::Vec2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double angle) noexcept;
[[nodiscard]] double valueNoise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept;

[[nodiscard]] glsl::Vec3 blendColors([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double t) noexcept {
  t = glsl::fract(t);
  [[maybe_unused]] double segment = (static_cast<double>(t) * static_cast<double>(float(state.colorCount)));
  [[maybe_unused]] std::int32_t idx = glsl::detail::glsl_int_cast(glsl::floor(segment));
  [[maybe_unused]] double localT = glsl::fract(segment);
  [[maybe_unused]] std::int32_t next = (idx + std::int32_t(1));
  if (next >= state.colorCount) {
    next = std::int32_t(0);
  }
  return glsl::mix(getColor(state, context, idx), getColor(state, context, next), localT);
}

[[nodiscard]] double fbmNoise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept {
  [[maybe_unused]] double sum = static_cast<float>(0.0);
  [[maybe_unused]] double amp = static_cast<float>(0.5);
  [[maybe_unused]] double freq = static_cast<float>(1.0);
  [[maybe_unused]] double maxVal = static_cast<float>(0.0);
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(4)); ++i) {
    sum = (sum + (static_cast<double>(valueNoise(state, context, (p * freq))) * static_cast<double>(amp)));
    maxVal = (maxVal + amp);
    freq = (freq * static_cast<float>(2.0));
    amp = (amp * static_cast<float>(0.5));
  }
  return (static_cast<double>(sum) / static_cast<double>(maxVal));
}

[[nodiscard]] glsl::DVec3 getColor([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t idx) noexcept {
  if (idx == std::int32_t(0)) {
    return state.color1;
  }
  if (idx == std::int32_t(1)) {
    return state.color2;
  }
  if (idx == std::int32_t(2)) {
    return state.color3;
  }
  return state.color4;
}

[[nodiscard]] double hash2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept {
  return glsl::swizzle<0>(prng(state, context, glsl::Vec3(p, float(state.seed))));
}

[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept {
  v = ((v * std::uint32_t(std::int32_t(1664525))) + std::uint32_t(std::int32_t(1013904223)));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  v = glsl::bitwise_xor(v, glsl::shift_right(v, std::uint32_t(std::int32_t(16))));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  return v;
}

[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept {
  glsl::set_swizzle<0>(p, ((glsl::swizzle<0>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<0>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<0>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  glsl::set_swizzle<1>(p, ((glsl::swizzle<1>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<1>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<1>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  glsl::set_swizzle<2>(p, ((glsl::swizzle<2>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<2>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<2>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  return glsl::FloatExpr<3>(glsl::Vec3((glsl::Vec3(pcg(state, context, glsl::UVec3(p))) / float(std::uint32_t(std::int32_t(-1))))));
}

[[nodiscard]] glsl::Vec2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double angle) noexcept {
  [[maybe_unused]] double aspectRatio = (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)));
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) * aspectRatio));
  st = glsl::Vec2((st - glsl::FloatExpr<2>((static_cast<double>(aspectRatio) * static_cast<double>(static_cast<float>(0.5))), static_cast<float>(0.5))));
  [[maybe_unused]] double c = glsl::cos(angle);
  [[maybe_unused]] double s = glsl::sin(angle);
  st = glsl::Vec2((glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c)) * st));
  st = glsl::Vec2((st + glsl::FloatExpr<2>((static_cast<double>(aspectRatio) * static_cast<double>(static_cast<float>(0.5))), static_cast<float>(0.5))));
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) / aspectRatio));
  return st;
}

[[nodiscard]] double valueNoise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 p) noexcept {
  [[maybe_unused]] glsl::Vec2 i = glsl::floor(p);
  [[maybe_unused]] glsl::Vec2 f = glsl::fract(p);
  [[maybe_unused]] glsl::Vec2 u = ((f * f) * (static_cast<float>(3.0) - (static_cast<float>(2.0) * f)));
  [[maybe_unused]] double a = hash2D(state, context, i);
  [[maybe_unused]] double b = hash2D(state, context, (i + glsl::FloatExpr<2>(static_cast<float>(1.0), static_cast<float>(0.0))));
  [[maybe_unused]] double c = hash2D(state, context, (i + glsl::FloatExpr<2>(static_cast<float>(0.0), static_cast<float>(1.0))));
  [[maybe_unused]] double d = hash2D(state, context, (i + glsl::FloatExpr<2>(static_cast<float>(1.0), static_cast<float>(1.0))));
  return glsl::mix(glsl::mix(a, b, glsl::swizzle<0>(u)), glsl::mix(c, d, glsl::swizzle<0>(u)), glsl::swizzle<1>(u));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 st = (globalCoord / state.fullResolution);
  [[maybe_unused]] double aspectRatio = (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)));
  [[maybe_unused]] double angle = (static_cast<double>((static_cast<double>((-state.rotation)) * static_cast<double>(static_cast<float>(3.14159265359)))) / static_cast<double>(static_cast<float>(180.0)));
  [[maybe_unused]] glsl::Vec2 rotatedSt = rotate2D(state, context, st, angle);
  [[maybe_unused]] glsl::Vec2 centered = (st - static_cast<float>(0.5));
  glsl::set_swizzle<0>(centered, (glsl::swizzle<0>(centered) * aspectRatio));
  [[maybe_unused]] glsl::Vec2& rotatedCentered = centered;
  [[maybe_unused]] double c = glsl::cos(angle);
  [[maybe_unused]] double s = glsl::sin(angle);
  glsl::set_swizzle<0>(rotatedCentered, (c * glsl::swizzle<0>(centered) + s * glsl::swizzle<1>(centered)));
  glsl::set_swizzle<1>(rotatedCentered, ((-s) * glsl::swizzle<0>(rotatedCentered) + c * glsl::swizzle<1>(centered)));
  [[maybe_unused]] glsl::Vec3 color = {};
  [[maybe_unused]] double t = {};
  [[maybe_unused]] double timeOffset = (static_cast<double>(state.time) * static_cast<double>(state.speed));
  if (state.gradientType == std::int32_t(0)) {
    [[maybe_unused]] double a = glsl::atan(glsl::swizzle<1>(rotatedCentered), glsl::swizzle<0>(rotatedCentered));
    t = (static_cast<double>((static_cast<double>(a) + static_cast<double>(static_cast<float>(3.14159265359)))) / static_cast<double>(static_cast<float>(6.28318530718)));
    t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
    color = glsl::Vec3(blendColors(state, context, t));
  } else {
    if (state.gradientType == std::int32_t(1)) {
      t = (static_cast<double>(glsl::abs(glsl::swizzle<0>(rotatedCentered))) + static_cast<double>(glsl::abs(glsl::swizzle<1>(rotatedCentered))));
      t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
      color = glsl::Vec3(blendColors(state, context, t));
    } else {
      if (state.gradientType == std::int32_t(2)) {
        [[maybe_unused]] glsl::Vec2 cornerSt = rotate2D(state, context, st, angle);
        [[maybe_unused]] glsl::DVec3 cTL = state.color1;
        [[maybe_unused]] glsl::DVec3 cTR = ((state.colorCount >= std::int32_t(3)) ? glsl::DVec3(state.color2) : glsl::DVec3(state.color1));
        [[maybe_unused]] glsl::DVec3 cBL = ((state.colorCount >= std::int32_t(3)) ? glsl::DVec3(state.color3) : glsl::DVec3(state.color2));
        [[maybe_unused]] glsl::DVec3 cBR = ((state.colorCount >= std::int32_t(4)) ? glsl::DVec3(state.color4) : glsl::DVec3(cBL));
        [[maybe_unused]] glsl::Vec3 top = glsl::mix(cTL, cTR, glsl::swizzle<0>(cornerSt));
        [[maybe_unused]] glsl::Vec3 bottom = glsl::mix(cBL, cBR, glsl::swizzle<0>(cornerSt));
        color = glsl::Vec3(glsl::mix(bottom, top, glsl::swizzle<1>(cornerSt)));
      } else {
        if (state.gradientType == std::int32_t(3)) {
          t = glsl::swizzle<1>(rotatedSt);
          t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
          color = glsl::Vec3(blendColors(state, context, t));
        } else {
          if (state.gradientType == std::int32_t(4)) {
            [[maybe_unused]] glsl::Vec2 noiseSt = (rotatedCentered * static_cast<float>(4.0));
            t = fbmNoise(state, context, noiseSt);
            t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
            color = glsl::Vec3(blendColors(state, context, t));
          } else {
            if (state.gradientType == std::int32_t(5)) {
              [[maybe_unused]] glsl::Vec2 rotatedPoint = (glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c)) * centered);
              [[maybe_unused]] double dist = (static_cast<double>(glsl::length(rotatedPoint)) * static_cast<double>(static_cast<float>(2.0)));
              t = dist;
              t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
              color = glsl::Vec3(blendColors(state, context, t));
            } else {
              if (state.gradientType == std::int32_t(6)) {
                [[maybe_unused]] double a = glsl::atan(glsl::swizzle<1>(rotatedCentered), glsl::swizzle<0>(rotatedCentered));
                [[maybe_unused]] double dist = glsl::length(centered);
                t = glsl::fract((static_cast<double>((static_cast<double>(a) / static_cast<double>(static_cast<float>(6.28318530718)))) + static_cast<double>((static_cast<double>(dist) * static_cast<double>(static_cast<float>(2.0))))));
                t = glsl::fract((static_cast<double>((static_cast<double>(t) * static_cast<double>(float(state.repeat)))) + static_cast<double>(timeOffset)));
                color = glsl::Vec3(blendColors(state, context, t));
              }
            }
          }
        }
      }
    }
  }
  output = glsl::Vec4(glsl::Vec4(color, static_cast<float>(1.0)));
}
}  // namespace typed_gradient_historical

BoundKernel bind_synth_gradient_gradient(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_gradient_historical::State>(bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get<std::int32_t>("gradientType"), bindings.get_number("rotation"), bindings.get<std::int32_t>("repeat"), bindings.get<std::int32_t>("colorCount"), bindings.get<glsl::DVec3>("color1"), bindings.get<glsl::DVec3>("color2"), bindings.get<glsl::DVec3>("color3"), bindings.get<glsl::DVec3>("color4"), bindings.get<std::int32_t>("seed"), bindings.get_number("time"), bindings.get_number("speed"));
  (void)bindings;
  return BoundKernel(state, &typed_gradient_historical::pixel);
}
// End frozen Gradient block
}
