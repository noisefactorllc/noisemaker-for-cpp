#include "noisemaker/effects/scatter/physarum.hpp"

#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::physarum {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& /*pass*/, Surface& destination) {
  // physarum reads no `pass` field.
  const Surface& xyz_tex = bindings.texture("xyzTex");
  const Surface& rgba_tex = bindings.texture("rgbaTex");
  Uniforms uniforms;
  uniforms.deposit = bindings.get_number("deposit");
  return run_deposit(xyz_tex, rgba_tex, uniforms, destination);
}

}  // namespace

std::size_t run_deposit(const Surface& xyz_tex, const Surface& rgba_tex, const Uniforms& uniforms,
                         Surface& destination) {
  namespace pd = points_deposit;
  const auto width = static_cast<std::int64_t>(xyz_tex.width());
  const auto height = static_cast<std::int64_t>(xyz_tex.height());
  const std::int64_t count = width * height;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const auto data = destination.data();
  const double deposit = uniforms.deposit;
  std::size_t pixels = 0;

  for (std::int64_t v = 0; v < count; ++v) {
    const std::int64_t sx = v % width;
    const std::int64_t sy = v / width;
    const Rgba pos = pd::texel_fetch_agent(xyz_tex, sx, sy);
    if (static_cast<double>(pos[3]) < 0.5) continue;  // alive = pos.w

    const double clip_x = static_cast<double>(pos[0]) * 2.0 - 1.0;
    const double clip_y = static_cast<double>(pos[1]) * 2.0 - 1.0;
    const auto offset = pd::scatter_point_pixel(clip_x, clip_y, 1.0, dest_width, dest_height);
    if (!offset.has_value()) continue;

    const Rgba col = pd::texel_fetch_agent(rgba_tex, sx, sy);
    data[*offset] += static_cast<double>(col[0]) * deposit;
    data[*offset + 1] += static_cast<double>(col[1]) * deposit;
    data[*offset + 2] += static_cast<double>(col[2]) * deposit;
    data[*offset + 3] += static_cast<double>(col[3]) * deposit;
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("points/physarum:deposit", &adapter); }

}  // namespace noisemaker::scatter::physarum
