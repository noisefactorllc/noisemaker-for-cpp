#include "noisemaker/generated/catalog.hpp"

#include <array>
#include <cstdint>
#include <memory>
#include <stdexcept>

#include "noisemaker/sampler.hpp"

namespace noisemaker::generated {
// Typed IR program: filter/rotate:rot
// Source SHA-256: c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f
namespace typed_task28_projection {
struct State final : KernelState {
  State(const Surface* inputTex_value, double rotation_value, std::int32_t wrap_value, std::int32_t speed_value, double time_value) : inputTex(inputTex_value), rotation(rotation_value), wrap(wrap_value), speed(speed_value), time(time_value) {}
  const Surface* inputTex;
  double rotation;
  std::int32_t wrap;
  std::int32_t speed;
  double time;
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

[[nodiscard]] glsl::Mat2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double angle) noexcept;

[[nodiscard]] glsl::Mat2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double angle) noexcept {
  [[maybe_unused]] double c = glsl::cos(angle);
  [[maybe_unused]] double s = glsl::sin(angle);
  return glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  const double TAU = static_cast<float>(6.283185307179586);
  [[maybe_unused]] glsl::IVec2 texSize = texture_size(*state.inputTex);
  [[maybe_unused]] glsl::Vec2 uv = (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texSize));
  [[maybe_unused]] double angle = state.rotation;
  if (state.speed != std::int32_t(0)) {
    angle = (angle + (static_cast<double>((static_cast<double>(state.time) * static_cast<double>(static_cast<float>(360.0)))) * static_cast<double>(float(state.speed))));
  }
  [[maybe_unused]] double aspect = (static_cast<double>(float(glsl::swizzle<0>(texSize))) / static_cast<double>(float(glsl::swizzle<1>(texSize))));
  [[maybe_unused]] glsl::Vec2 center = glsl::FloatExpr<2>(static_cast<float>(0.5));
  uv = glsl::Vec2((uv - center));
  glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) * aspect));
  uv = glsl::Vec2((rotate2D(state, context, (static_cast<double>((static_cast<double>((-angle)) * static_cast<double>(TAU))) / static_cast<double>(static_cast<float>(360.0)))) * uv));
  glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) / aspect));
  uv = glsl::Vec2((uv + center));
  if (state.wrap == std::int32_t(0)) {
    uv = glsl::Vec2(glsl::abs(glsl::Vec2((glsl::mod((uv + static_cast<float>(1.0)), static_cast<float>(2.0)) - static_cast<float>(1.0)))));
  } else {
    if (state.wrap == std::int32_t(1)) {
      uv = glsl::Vec2(glsl::fract(uv));
    } else {
      uv = glsl::Vec2(glsl::clamp(uv, static_cast<float>(0.0), static_cast<float>(1.0)));
    }
  }
  output = glsl::Vec4(sample_texture(*state.inputTex, uv));
}
}  // namespace typed_task28_projection

BoundKernel bind_filter_rotate_rot(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_task28_projection::State>(&bindings.texture("inputTex"), bindings.get_number("rotation"), bindings.get<std::int32_t>("wrap"), bindings.get<std::int32_t>("speed"), bindings.get_number("time"));
  (void)bindings;
  return BoundKernel(state, &typed_task28_projection::pixel);
}
}  // namespace noisemaker::generated
