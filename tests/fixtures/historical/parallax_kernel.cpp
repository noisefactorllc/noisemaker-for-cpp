// CPU61aa Parallax retained only for its immutable historical captures.
#include "parallax_kernel.hpp"
#include <cmath>
#include <cstdint>
#include <memory>
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
namespace noisemaker::historical_generated {
// Typed IR program: filter/parallax:parallax
// Source SHA-256: 5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642
namespace typed_98 {
struct State final : KernelState {
  State(const Surface* inputTex_value, const Surface* heightMap_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, glsl::DVec3 direction_value, double pivot_value) : inputTex(inputTex_value), heightMap(heightMap_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), direction(direction_value), pivot(pivot_value) {}
  const Surface* inputTex;
  const Surface* heightMap;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  glsl::DVec3 direction;
  double pivot;
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

[[nodiscard]] double getHeight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec4 getInput([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] double getLuminosity([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;

[[nodiscard]] double getHeight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] glsl::Vec2 mapSize = glsl::Vec2(texture_size(*state.heightMap));
  [[maybe_unused]] glsl::Vec2 localUV = (((uv * state.fullResolution) - state.tileOffset) / mapSize);
  return getLuminosity(state, context, glsl::swizzle<0, 1, 2>(sample_texture(*state.heightMap, localUV)));
}

[[nodiscard]] glsl::Vec4 getInput([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] glsl::Vec2 texSize = glsl::Vec2(texture_size(*state.inputTex));
  [[maybe_unused]] glsl::Vec2 localUV = (((uv * state.fullResolution) - state.tileOffset) / texSize);
  return sample_texture(*state.inputTex, localUV);
}

[[nodiscard]] double getLuminosity([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  return glsl::dot(color, glsl::FloatExpr<3>(static_cast<float>(0.299), static_cast<float>(0.587), static_cast<float>(0.114)));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  const std::int32_t MARCH_STEPS = 32;
  const double SHIFT_SCALE = static_cast<float>(0.15);
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec3 v = ((glsl::length(state.direction) > static_cast<float>(0.0)) ? glsl::Vec3(glsl::normalize(state.direction)) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0))));
  [[maybe_unused]] glsl::Vec2 shift = (glsl::swizzle<0, 1>(v) * SHIFT_SCALE);
  [[maybe_unused]] bool isTileRendering = (glsl::length(state.tileOffset) > static_cast<float>(0.0));
  if (isTileRendering) {
    [[maybe_unused]] double maxDispPixels = static_cast<float>(256.0);
    [[maybe_unused]] double dispPixels = glsl::length((shift * state.fullResolution));
    if (dispPixels > maxDispPixels) {
      shift = glsl::Vec2((shift * (static_cast<double>(maxDispPixels) / static_cast<double>(dispPixels))));
    }
  }
  [[maybe_unused]] double t = static_cast<float>(1.0);
  [[maybe_unused]] glsl::Vec2 rayUV = (uv + (shift * (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(state.pivot))));
  [[maybe_unused]] double f = (static_cast<double>(t) - static_cast<double>(getHeight(state, context, rayUV)));
  if (f > static_cast<float>(0.0)) {
    [[maybe_unused]] double stepSize = (static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(float(MARCH_STEPS)));
    for ([[maybe_unused]] std::int32_t i = std::int32_t(1); (i <= MARCH_STEPS); ++i) {
      [[maybe_unused]] double prevF = f;
      [[maybe_unused]] glsl::Vec2& prevUV = rayUV;
      t = (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(float(i)) * static_cast<double>(stepSize))));
      rayUV = glsl::Vec2((uv + (shift * (static_cast<double>(t) - static_cast<double>(state.pivot)))));
      f = (static_cast<double>(t) - static_cast<double>(getHeight(state, context, rayUV)));
      if (f <= static_cast<float>(0.0)) {
        [[maybe_unused]] double w = (static_cast<double>(f) / static_cast<double>((static_cast<double>(f) - static_cast<double>(prevF))));
        rayUV = glsl::Vec2(glsl::mix(rayUV, prevUV, w));
        break;
      }
    }
  }
  output = glsl::Vec4(getInput(state, context, rayUV));
}
}  // namespace typed_98

BoundKernel bind_filter_parallax_parallax(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_98::State>(&bindings.texture("inputTex"), &bindings.texture("heightMap"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get<glsl::DVec3>("direction"), bindings.get_number("pivot"));
  (void)bindings;
  return BoundKernel(state, &typed_98::pixel);
}

// End frozen Parallax block
}
