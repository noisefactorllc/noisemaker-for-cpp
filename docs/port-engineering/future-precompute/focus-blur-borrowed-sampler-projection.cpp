#include "noisemaker/generated/catalog.hpp"

#include <array>
#include <cstdint>
#include <memory>
#include <stdexcept>

#include "noisemaker/sampler.hpp"

namespace noisemaker::generated {
// Typed IR program: mixer/focusBlur:focusBlur
// Source SHA-256: dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1
namespace future_probe {
struct State final : KernelState {
  State(const Surface* inputTex_value, const Surface* tex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double focalDistance_value, double aperture_value, double sampleBias_value, std::int32_t depthSource_value) : inputTex(inputTex_value), tex(tex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), focalDistance(focalDistance_value), aperture(aperture_value), sampleBias(sampleBias_value), depthSource(depthSource_value) {}
  const Surface* inputTex;
  const Surface* tex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double focalDistance;
  double aperture;
  double sampleBias;
  std::int32_t depthSource;
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

[[nodiscard]] glsl::Vec4 applyFocusBlur([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Surface& sceneTex, [[maybe_unused]] const Surface& depthTex, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] double computeBlurFactor([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double depth) noexcept;
[[nodiscard]] double getLuminosity([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;

[[nodiscard]] glsl::Vec4 applyFocusBlur([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Surface& sceneTex, [[maybe_unused]] const Surface& depthTex, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] glsl::Vec4 depthSample = sample_texture(depthTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(depthTex))));
  [[maybe_unused]] double depth = getLuminosity(state, context, glsl::swizzle<0, 1, 2>(depthSample));
  [[maybe_unused]] double blurRadius = (static_cast<double>(computeBlurFactor(state, context, depth)) * static_cast<double>(state.sampleBias));
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0));
  [[maybe_unused]] double GOLDEN = static_cast<float>(2.399963);
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(64)); ++i) {
    [[maybe_unused]] double r = glsl::sqrt((static_cast<double>(float(i)) / static_cast<double>(static_cast<float>(64.0))));
    [[maybe_unused]] double theta = (static_cast<double>(float(i)) * static_cast<double>(GOLDEN));
    [[maybe_unused]] glsl::Vec2 offset = (((glsl::FloatExpr<2>(glsl::cos(theta), glsl::sin(theta)) * r) * blurRadius) / state.resolution);
    color = glsl::Vec4((color + sample_texture(sceneTex, ((((uv + offset) * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(sceneTex))))));
  }
  return (color / static_cast<float>(64.0));
}

[[nodiscard]] double computeBlurFactor([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double depth) noexcept {
  [[maybe_unused]] double focalPlane = (static_cast<double>(state.focalDistance) * static_cast<double>(static_cast<float>(0.01)));
  [[maybe_unused]] double blur = (static_cast<double>(glsl::abs((static_cast<double>(depth) - static_cast<double>(focalPlane)))) * static_cast<double>(state.aperture));
  return glsl::clamp(blur, static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] double getLuminosity([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  return glsl::dot(color, glsl::FloatExpr<3>(static_cast<float>(0.2126), static_cast<float>(0.7152), static_cast<float>(0.0722)));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec4 color = {};
  if (state.depthSource == std::int32_t(0)) {
    color = glsl::Vec4(applyFocusBlur(state, context, *state.tex, *state.inputTex, uv));
  } else {
    color = glsl::Vec4(applyFocusBlur(state, context, *state.inputTex, *state.tex, uv));
  }
  glsl::set_swizzle<3>(color, glsl::component_max(glsl::swizzle<3>(sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex))))), glsl::swizzle<3>(sample_texture(*state.tex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.tex)))))));
  output = glsl::Vec4(color);
}
}  // namespace future_probe

BoundKernel bind_future_probe(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<future_probe::State>(&bindings.texture("inputTex"), &bindings.texture("tex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("focalDistance"), bindings.get_number("aperture"), bindings.get_number("sampleBias"), bindings.get<std::int32_t>("depthSource"));
  (void)bindings;
  return BoundKernel(state, &future_probe::pixel);
}

}  // namespace noisemaker::generated
