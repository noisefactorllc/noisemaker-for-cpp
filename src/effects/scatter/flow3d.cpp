#include "noisemaker/effects/scatter/flow3d.hpp"

#include <cmath>
#include <cstdint>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::flow3d {
namespace {

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& pass, Surface& destination) {
  const Surface& state_tex1 = bindings.texture("stateTex1");
  const Surface& state_tex2 = bindings.texture("stateTex2");
  Uniforms uniforms;
  uniforms.density = bindings.get_number("density");
  uniforms.volume_size = bindings.get_number("volumeSize");
  return run_deposit(state_tex1, state_tex2, uniforms, pass.count, destination);
}

}  // namespace

std::size_t run_deposit(const Surface& state_tex1, const Surface& state_tex2, const Uniforms& uniforms,
                         std::optional<double> pass_count, Surface& destination) {
  namespace pd = points_deposit;
  const auto state_width = static_cast<std::int64_t>(state_tex1.width());
  const auto state_height = static_cast<std::int64_t>(state_tex1.height());
  const double capacity = static_cast<double>(state_width) * static_cast<double>(state_height);
  const double max_agents =
      std::trunc(std::max(static_cast<double>(state_width), static_cast<double>(state_height)) * uniforms.density * 0.2);
  const double draw_count = pass_count.has_value() ? *pass_count : capacity;
  const double count = pd::js_max(0.0, pd::js_min(pd::js_min(draw_count, capacity), max_agents));
  const double volume_size = uniforms.volume_size;
  const double atlas_height = volume_size * volume_size;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const auto data = destination.data();
  std::size_t pixels = 0;

  for (std::int64_t agent_index = 0; static_cast<double>(agent_index) < count; ++agent_index) {
    const std::int64_t state_x = agent_index % state_width;
    const std::int64_t state_y = agent_index / state_width;
    const Rgba state1 = pd::texel_fetch_agent(state_tex1, state_x, state_y);
    const Rgba state2 = pd::texel_fetch_agent(state_tex2, state_x, state_y);

    const double atlas_x = static_cast<double>(state1[0]);
    const double atlas_y = static_cast<double>(state1[1]) + std::floor(static_cast<double>(state1[2])) * volume_size;
    const double clip_x = (atlas_x / volume_size) * 2.0 - 1.0;
    const double clip_y = (atlas_y / atlas_height) * 2.0 - 1.0;
    const auto offset = pd::scatter_point_pixel(clip_x, clip_y, 1.0, dest_width, dest_height);
    if (!offset.has_value()) continue;

    data[*offset] += static_cast<double>(state2[0]);
    data[*offset + 1] += static_cast<double>(state2[1]);
    data[*offset + 2] += static_cast<double>(state2[2]);
    data[*offset + 3] += 1.0;
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("filter3d/flow3d:deposit", &adapter); }

}  // namespace noisemaker::scatter::flow3d
