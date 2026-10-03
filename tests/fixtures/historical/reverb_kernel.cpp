// Test-only kernels from noisemaker-for-cpp a15c4b6816a3cb4a1811a03429e4fbf84530c722.
// Original src/typed_generated/typed_slice.cpp SHA-256:
// 3f7c1644dc966f4f401e523ca0ea830d1ddc2e4372263e8710120930f2176b4c
// Blocks below are byte-exact extractions; only the enclosing namespace differs.
#include "reverb_kernel.hpp"

#include <cmath>
#include <cstdint>
#include <memory>

#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"

namespace noisemaker::historical_generated {
// Typed IR program: filter/reverb:reverb
// Source SHA-256: 4dde4b901aded65365d0d46145a7d50dcd2b8d279e32c3d1e7bf02cfc7f78bcb
namespace typed_125 {
struct State final : KernelState {
  State(glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, const Surface* inputTex_value, std::int32_t iterations_value, bool ridges_value, double alpha_value, double wrap_value) : tileOffset(tileOffset_value), fullResolution(fullResolution_value), inputTex(inputTex_value), iterations(iterations_value), ridges(ridges_value), alpha(alpha_value), wrap(wrap_value) {}
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  const Surface* inputTex;
  std::int32_t iterations;
  bool ridges;
  double alpha;
  double wrap;
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

[[nodiscard]] glsl::Vec2 applyWrap([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec4 ridge_transform([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color) noexcept;

[[nodiscard]] glsl::Vec2 applyWrap([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] std::int32_t mode = glsl::detail::glsl_int_cast(state.wrap);
  if (mode == std::int32_t(0)) {
    return glsl::abs(glsl::Vec2((glsl::mod((uv + static_cast<float>(1.0)), static_cast<float>(2.0)) - static_cast<float>(1.0))));
  } else {
    if (mode == std::int32_t(1)) {
      return glsl::fract(uv);
    }
  }
  return glsl::clamp(uv, static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] glsl::Vec4 ridge_transform([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color) noexcept {
  return glsl::Vec4((glsl::FloatExpr<4>(static_cast<float>(1.0)) - glsl::abs(((color * static_cast<float>(2.0)) - glsl::FloatExpr<4>(static_cast<float>(1.0))))));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::IVec2 dims = texture_size(*state.inputTex);
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 globalUV = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec2 localUV = (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(dims));
  [[maybe_unused]] glsl::Vec4 original = sample_texture(*state.inputTex, localUV);
  [[maybe_unused]] glsl::Vec4& current = original;
  if (state.ridges) {
    current = glsl::Vec4(ridge_transform(state, context, current));
  }
  [[maybe_unused]] glsl::Vec4& accum = current;
  [[maybe_unused]] double totalWeight = static_cast<float>(1.0);
  [[maybe_unused]] double weight = static_cast<float>(0.5);
  [[maybe_unused]] double scale = static_cast<float>(2.0);
  [[maybe_unused]] std::int32_t iters = glsl::clamp(state.iterations, std::int32_t(1), std::int32_t(8));
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < iters); ++i) {
    [[maybe_unused]] glsl::Vec2 warpedGlobalUV = (globalUV * scale);
    [[maybe_unused]] glsl::Vec2 wrappedGlobalUV = applyWrap(state, context, warpedGlobalUV);
    [[maybe_unused]] glsl::Vec2 sampledLocalUV = glsl::fract((((wrappedGlobalUV * state.fullResolution) - state.tileOffset) / glsl::Vec2(dims)));
    [[maybe_unused]] glsl::Vec4 scaled = sample_texture(*state.inputTex, sampledLocalUV);
    if (state.ridges) {
      scaled = glsl::Vec4(ridge_transform(state, context, scaled));
    }
    accum = glsl::Vec4((accum + (scaled * weight)));
    totalWeight = (totalWeight + weight);
    scale = (scale * static_cast<float>(2.0));
    weight = (weight * static_cast<float>(0.5));
  }
  [[maybe_unused]] glsl::Vec4 result = (accum / totalWeight);
  output = glsl::Vec4(glsl::Vec4(glsl::mix(glsl::swizzle<0, 1, 2>(original), glsl::swizzle<0, 1, 2>(result), state.alpha), static_cast<float>(1.0)));
}
}  // namespace typed_125

BoundKernel bind_filter_reverb_reverb(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_125::State>(bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), &bindings.texture("inputTex"), bindings.get<std::int32_t>("iterations"), bindings.get<bool>("ridges"), bindings.get_number("alpha"), bindings.get_number("wrap"));
  (void)bindings;
  return BoundKernel(state, &typed_125::pixel);
}

// End frozen block: filter/reverb:reverb
}  // namespace noisemaker::historical_generated
