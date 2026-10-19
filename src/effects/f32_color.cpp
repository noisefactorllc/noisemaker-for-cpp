#include "noisemaker/effects/f32_color.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

// Hand-written CPU kernels for filter/pixelSort:luminance,
// filter/reindex:nmReindexStats and filter/reindex:nmReindexApply.
//
// Ported by hand from the authority's src/effects/adapters/f32-color.js,
// operation for operation. Every helper below has the name and the rounding of
// its JS counterpart: add/sub/mul/div round to float32 (Math.fround),
// Math.min and Math.max keep their JS semantics through js_min and js_max, and
// Math.pow is V8's (noisemaker::fdlibm::pow). Coordinates go through ToInt32
// (`| 0`) where the JS uses it.
namespace noisemaker::effects {
namespace {

using glsl::Vec4;

[[nodiscard]] double F(double value) noexcept { return static_cast<double>(noisemaker::f32(value)); }
[[nodiscard]] double add(double left, double right) noexcept { return F(left + right); }
[[nodiscard]] double sub(double left, double right) noexcept { return F(left - right); }
[[nodiscard]] double mul(double left, double right) noexcept { return F(left * right); }
[[nodiscard]] double div(double left, double right) noexcept { return F(left / right); }
[[nodiscard]] std::int32_t to_int32(double value) noexcept { return glsl::detail::js_to_int32(value); }

[[nodiscard]] double js_max(double a, double b) noexcept {
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == 0.0 && b == 0.0) return std::signbit(a) && std::signbit(b) ? -0.0 : 0.0;
  return a > b ? a : b;
}
[[nodiscard]] double js_min(double a, double b) noexcept {
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == 0.0 && b == 0.0) return std::signbit(a) || std::signbit(b) ? -0.0 : 0.0;
  return a < b ? a : b;
}

// value <= 0 ? 0 : value >= 1 ? 1 : value (NaN passes through).
[[nodiscard]] double clamp01(double value) noexcept {
  if (value <= 0.0) return 0.0;
  if (value >= 1.0) return 1.0;
  return value;
}

[[nodiscard]] double srgb_to_linear(double value) noexcept {
  value = clamp01(value);
  if (value <= F(0.04045)) return div(value, F(12.92));
  return F(noisemaker::fdlibm::pow(div(add(value, F(0.055)), F(1.055)), F(2.4)));
}

[[nodiscard]] double cube_root(double value) noexcept {
  if (value == 0.0) return 0.0;
  return mul(value >= 0.0 ? 1.0 : -1.0, F(noisemaker::fdlibm::pow(std::fabs(value), div(1.0, 3.0))));
}

[[nodiscard]] double oklab_lightness(double red, double green, double blue) noexcept {
  const double r = srgb_to_linear(red);
  const double g = srgb_to_linear(green);
  const double b = srgb_to_linear(blue);
  const double l = add(add(mul(F(0.4121656120), r), mul(F(0.5362752080), g)), mul(F(0.0514575653), b));
  const double m = add(add(mul(F(0.2118591070), r), mul(F(0.6807189584), g)), mul(F(0.1074065790), b));
  const double s = add(add(mul(F(0.0883097947), r), mul(F(0.2818474174), g)), mul(F(0.6302613616), b));
  return clamp01(add(add(mul(F(0.2104542553), cube_root(l)), mul(F(0.7936177850), cube_root(m))),
                     mul(F(-0.0040720468), cube_root(s))));
}

// texelOffset(surface, x, y): x and y clamp to the surface, with y counted
// from the bottom row, exactly as texel_fetch_bottom_left reads it.
[[nodiscard]] Rgba texel(const Surface& surface, std::int32_t shader_x, std::int32_t shader_y) noexcept {
  return texel_fetch_bottom_left(surface, shader_x, shader_y);
}

[[nodiscard]] double lightness_at(const Surface& surface, std::int32_t shader_x, std::int32_t shader_y) noexcept {
  const Rgba value = texel(surface, shader_x, shader_y);
  return oklab_lightness(value[0], value[1], value[2]);
}

[[nodiscard]] Vec4 vec4(double x, double y, double z, double w) noexcept {
  return Vec4(static_cast<float>(x), static_cast<float>(y), static_cast<float>(z), static_cast<float>(w));
}

struct InputState final : KernelState {
  const Surface* input = nullptr;
};

struct ApplyState final : KernelState {
  const Surface* input = nullptr;
  const Surface* stats = nullptr;
  double displacement = 0.0;
};

void pixel_sort_luminance(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const InputState&>(base);
  const std::int32_t x = to_int32(static_cast<double>(ctx.frag_coord[0]));
  const std::int32_t y = to_int32(static_cast<double>(ctx.frag_coord[1]));
  out = vec4(lightness_at(*s.input, x, y),
             F(static_cast<double>(x) / (static_cast<double>(s.input->width()) - 1.0)), 0.0, 1.0);
}

void reindex_stats(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const InputState&>(base);
  const std::int32_t origin_x = to_int32(static_cast<double>(ctx.frag_coord[0]));
  const std::int32_t origin_y = to_int32(static_cast<double>(ctx.frag_coord[1]));
  if (origin_x % 8 != 0 || origin_y % 8 != 0) {
    out = vec4(0.0, 0.0, 0.0, 0.0);
    return;
  }
  const auto width = static_cast<std::int64_t>(s.input->width());
  const auto height = static_cast<std::int64_t>(s.input->height());
  double minimum = F(3.402823466e38);
  double maximum = F(-3.402823466e38);
  for (std::int64_t y = origin_y; y < std::min<std::int64_t>(std::int64_t{origin_y} + 8, height); y += 1) {
    for (std::int64_t x = origin_x; x < std::min<std::int64_t>(std::int64_t{origin_x} + 8, width); x += 1) {
      const double value = lightness_at(*s.input, static_cast<std::int32_t>(x), static_cast<std::int32_t>(y));
      minimum = js_min(minimum, value);
      maximum = js_max(maximum, value);
    }
  }
  out = vec4(minimum, maximum, 0.0, 1.0);
}

void reindex_apply(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const ApplyState&>(base);
  const Surface& input = *s.input;
  const std::int32_t x = to_int32(static_cast<double>(ctx.frag_coord[0]));
  const std::int32_t y = to_int32(static_cast<double>(ctx.frag_coord[1]));
  const double reference = lightness_at(input, x, y);
  const Rgba stats = texel(*s.stats, 0, 0);
  const double minimum = stats[0];
  const double maximum = stats[1];
  const double range = sub(maximum, minimum);
  double normalized = reference;
  if (range > F(0.0001)) normalized = clamp01(div(sub(reference, minimum), range));
  const auto width = static_cast<double>(input.width());
  const auto height = static_cast<double>(input.height());
  const double dimension = std::min(width, height);
  const double offset_value = add(mul(mul(normalized, F(s.displacement)), F(dimension)), normalized);
  const double qx = offset_value / width;
  const double qy = offset_value / height;
  const std::int32_t sample_x = std::min(to_int32(F((qx - std::floor(qx)) * width)),
                                         static_cast<std::int32_t>(input.width()) - 1);
  const std::int32_t sample_y = std::min(to_int32(F((qy - std::floor(qy)) * height)),
                                         static_cast<std::int32_t>(input.height()) - 1);
  const Rgba value = texel(input, sample_x, sample_y);
  out = Vec4(value[0], value[1], value[2], value[3]);
}

}  // namespace

BoundKernel bind_pixel_sort_luminance(const glsl::Bindings& b) {
  auto state = std::make_shared<InputState>();
  state->input = &b.texture("inputTex");
  return BoundKernel(state, &pixel_sort_luminance);
}

BoundKernel bind_reindex_stats(const glsl::Bindings& b) {
  auto state = std::make_shared<InputState>();
  state->input = &b.texture("inputTex");
  return BoundKernel(state, &reindex_stats);
}

BoundKernel bind_reindex_apply(const glsl::Bindings& b) {
  auto state = std::make_shared<ApplyState>();
  state->input = &b.texture("inputTex");
  state->stats = &b.texture("statsTex");
  state->displacement = b.get_number("uDisplacement");
  // nmReindexApply.glsl declares these three; the JS adapter never reads
  // them, but the binding still fails closed when one is missing or mistyped.
  static_cast<void>(b.get<glsl::Vec2>("resolution"));
  static_cast<void>(b.get<glsl::Vec2>("tileOffset"));
  static_cast<void>(b.get<glsl::Vec2>("fullResolution"));
  return BoundKernel(state, &reindex_apply);
}

}  // namespace noisemaker::effects
