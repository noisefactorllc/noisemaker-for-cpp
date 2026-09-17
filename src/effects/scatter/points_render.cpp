#include "noisemaker/effects/scatter/points_render.hpp"

#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::points_render {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& /*pass*/, Surface& destination) {
  // pointsRender reads no `pass` field.
  const Surface& xyz_tex = bindings.texture("xyzTex");
  const Surface& rgba_tex = bindings.texture("rgbaTex");
  Uniforms uniforms;
  uniforms.density = bindings.get_number("density");
  uniforms.view_mode = bindings.get_number("viewMode");
  uniforms.rotate_x = bindings.get_number("rotateX");
  uniforms.rotate_y = bindings.get_number("rotateY");
  uniforms.rotate_z = bindings.get_number("rotateZ");
  uniforms.pos_x = bindings.get_number("posX");
  uniforms.pos_y = bindings.get_number("posY");
  uniforms.pos_z = points_deposit::get_number_or(bindings, "posZ", 0.0);
  uniforms.view_scale = bindings.get_number("viewScale");
  uniforms.field_of_view = points_deposit::get_number_or(bindings, "fieldOfView", 0.0);
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
  const double cull_threshold = uniforms.density / 100.0;

  const pd::ClipCenterUniforms clip_uniforms{
      uniforms.view_mode, uniforms.rotate_x, uniforms.rotate_y, uniforms.rotate_z,
      uniforms.pos_x,     uniforms.pos_y,    uniforms.pos_z,    uniforms.view_scale,
      uniforms.field_of_view,
  };

  std::size_t pixels = 0;

  for (std::int64_t v = 0; v < count; ++v) {
    const double particle_random = pd::js_fract(static_cast<double>(v) * pd::kGoldenRatioConjugate);
    if (particle_random > cull_threshold) continue;  // ported literally: cull on `>`, keep on `<=`

    const std::int64_t sx = v % width;
    const std::int64_t sy = v / width;
    const Rgba pos = pd::texel_fetch_agent(xyz_tex, sx, sy);
    if (static_cast<double>(pos[3]) < 0.5) continue;  // alive = pos.w

    const auto clip = pd::compute_clip_center(static_cast<double>(pos[0]), static_cast<double>(pos[1]),
                                               static_cast<double>(pos[2]), clip_uniforms, dest_width, dest_height);
    if (!clip.has_value()) continue;
    const auto offset = pd::scatter_point_pixel(clip->clip_x, clip->clip_y, 1.0, dest_width, dest_height);
    if (!offset.has_value()) continue;

    const Rgba col = pd::texel_fetch_agent(rgba_tex, sx, sy);
    data[*offset] += static_cast<double>(col[0]);
    data[*offset + 1] += static_cast<double>(col[1]);
    data[*offset + 2] += static_cast<double>(col[2]);
    data[*offset + 3] += static_cast<double>(col[3]);
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("render/pointsRender:deposit", &adapter); }

}  // namespace noisemaker::scatter::points_render
