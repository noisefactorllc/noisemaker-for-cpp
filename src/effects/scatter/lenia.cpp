#include "noisemaker/effects/scatter/lenia.hpp"

#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::lenia {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& /*pass*/, Surface& destination) {
  // lenia reads no `pass` field.
  const Surface& xyz_tex = bindings.texture("xyzTex");
  Uniforms uniforms;
  uniforms.deposit_amount = bindings.get_number("depositAmount");
  return run_deposit(xyz_tex, uniforms, destination);
}

}  // namespace

std::size_t run_deposit(const Surface& xyz_tex, const Uniforms& uniforms, Surface& destination) {
  namespace pd = points_deposit;
  const auto width = static_cast<std::int64_t>(xyz_tex.width());
  const auto height = static_cast<std::int64_t>(xyz_tex.height());
  const std::int64_t count = width * height;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const auto data = destination.data();
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

    data[*offset] += uniforms.deposit_amount;
    data[*offset + 1] += 0.0;
    data[*offset + 2] += 0.0;
    data[*offset + 3] += 1.0;
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("points/lenia:deposit", &adapter); }

}  // namespace noisemaker::scatter::lenia
