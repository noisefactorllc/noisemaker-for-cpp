#include "noisemaker/effects/scatter/lenia.hpp"

#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"

namespace noisemaker::scatter::lenia {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& pass, Surface& destination) {
  const Surface& xyz_tex = bindings.texture("xyzTex");
  Uniforms uniforms;
  uniforms.deposit_amount = bindings.get_number("depositAmount");
  return run_deposit(xyz_tex, uniforms, destination, pass.destination_format);
}

}  // namespace

std::size_t run_deposit(const Surface& xyz_tex, const Uniforms& uniforms, Surface& destination,
                        TextureFormat destination_format) {
  namespace pd = points_deposit;
  const auto width = static_cast<std::int64_t>(xyz_tex.width());
  const auto height = static_cast<std::int64_t>(xyz_tex.height());
  const std::int64_t count = width * height;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const auto data = destination.data();
  const bool half_float_blend = destination_format == TextureFormat::rgba16f;
  std::size_t pixels = 0;

  for (std::int64_t v = 0; v < count; ++v) {
    const std::int64_t sx = v % width;
    const std::int64_t sy = v / width;
    const Rgba xyz = pd::texel_fetch_agent(xyz_tex, sx, sy);
    if (static_cast<double>(xyz[3]) < 0.5) continue;  // alive = xyz.w

    const double clip_x = static_cast<double>(xyz[0]) * 2.0 - 1.0;
    const double clip_y = static_cast<double>(xyz[1]) * 2.0 - 1.0;
    const auto offset = pd::scatter_point_pixel(clip_x, clip_y, 1.0, dest_width, dest_height);
    if (!offset.has_value()) continue;

    const double red = static_cast<double>(data[*offset]) + uniforms.deposit_amount;
    data[*offset] = half_float_blend ? float16_truncate(static_cast<float>(red)) : static_cast<float>(red);
    data[*offset + 1] += 0.0;
    data[*offset + 2] += 0.0;
    const double alpha = static_cast<double>(data[*offset + 3]) + 1.0;
    data[*offset + 3] = half_float_blend ? float16_truncate(static_cast<float>(alpha)) : static_cast<float>(alpha);
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("points/lenia:deposit", &adapter); }

}  // namespace noisemaker::scatter::lenia
