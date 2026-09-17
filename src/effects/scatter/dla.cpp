#include "noisemaker/effects/scatter/dla.hpp"

#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::dla {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& /*pass*/, Surface& destination) {
  // dla reads no `pass` field.
  const Surface& xyz_tex = bindings.texture("xyzTex");
  const Surface& vel_tex = bindings.texture("velTex");
  const Surface& rgba_tex = bindings.texture("rgbaTex");
  Uniforms uniforms;
  uniforms.deposit = bindings.get_number("deposit");
  return run_deposit(xyz_tex, vel_tex, rgba_tex, uniforms, destination);
}

}  // namespace

std::size_t run_deposit(const Surface& xyz_tex, const Surface& vel_tex, const Surface& rgba_tex,
                         const Uniforms& uniforms, Surface& destination) {
  namespace pd = points_deposit;
  const auto width = static_cast<std::int64_t>(xyz_tex.width());
  const auto height = static_cast<std::int64_t>(xyz_tex.height());
  const std::int64_t count = width * height;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const auto data = destination.data();
  const double energy = uniforms.deposit * 0.1;
  std::size_t pixels = 0;

  for (std::int64_t v = 0; v < count; ++v) {
    const std::int64_t sx = v % width;
    const std::int64_t sy = v / width;
    // Read vel first (cheap early-exit) -- texelFetch has no side effects,
    // so this matches the JS reference's own observable behavior exactly.
    const Rgba vel = pd::texel_fetch_agent(vel_tex, sx, sy);
    const double just_stuck = static_cast<double>(vel[1]);  // vel.y
    if (just_stuck < 0.5) continue;

    const Rgba xyz = pd::texel_fetch_agent(xyz_tex, sx, sy);
    const double clip_x = static_cast<double>(xyz[0]) * 2.0 - 1.0;
    const double clip_y = static_cast<double>(xyz[1]) * 2.0 - 1.0;
    const auto offset = pd::scatter_point_pixel(clip_x, clip_y, 1.0, dest_width, dest_height);
    if (!offset.has_value()) continue;

    const Rgba rgba = pd::texel_fetch_agent(rgba_tex, sx, sy);
    // fragColor = vec4(v_color * energy, energy) -- alpha is `energy`
    // alone, NOT rgba.a * energy.
    data[*offset] += static_cast<double>(rgba[0]) * energy;
    data[*offset + 1] += static_cast<double>(rgba[1]) * energy;
    data[*offset + 2] += static_cast<double>(rgba[2]) * energy;
    data[*offset + 3] += energy;
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("points/dla:depositGrid", &adapter); }

}  // namespace noisemaker::scatter::dla
