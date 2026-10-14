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
  const auto data = destination.data();
  std::size_t pixels = 0;

  for (std::int64_t agent_index = 0; static_cast<double>(agent_index) < count; ++agent_index) {
    const std::int64_t state_x = agent_index % state_width;
    const std::int64_t state_y = agent_index / state_width;
    const Rgba state1 = pd::texel_fetch_agent(state_tex1, state_x, state_y);
    const Rgba state2 = pd::texel_fetch_agent(state_tex2, state_x, state_y);

    const double atlas_x = static_cast<double>(state1[0]);
    const double atlas_y = static_cast<float>(
        static_cast<double>(state1[1]) + std::floor(static_cast<double>(state1[2])) * volume_size);
    if (atlas_x <= 1.0 / 512.0 || atlas_y <= 1.0 / 512.0) continue;
    const double gl_col = std::ceil(std::floor(atlas_x * 256.0 + 0.5) / 256.0) - 1.0;
    const double gl_row = std::ceil(std::floor(atlas_y * 256.0 + 0.5) / 256.0) - 1.0;
    if (!std::isfinite(gl_col) || !std::isfinite(gl_row)) continue;
    if (gl_col < 0.0 || gl_col >= volume_size || gl_row < 0.0 || gl_row >= atlas_height) continue;
    const double offset = ((atlas_height - 1.0 - gl_row) * volume_size + gl_col) * 4.0;

    // The authority addresses the volume atlas, even for a mismatched destination.
    // A Float32Array ignores a non-integer or out-of-range index; preserve that
    // behavior without converting an invalid index to size_t.
    for (std::size_t lane = 0; lane < 4; ++lane) {
      const double index = offset + static_cast<double>(lane);
      if (index >= 0.0 && index < static_cast<double>(data.size()) && std::trunc(index) == index) {
        data[static_cast<std::size_t>(index)] += lane == 3 ? 1.0 : static_cast<double>(state2[lane]);
      }
    }
    pixels += 1;
  }

  return pixels;
}

void register_adapter() { scatter::register_scatter_adapter("filter3d/flow3d:deposit", &adapter); }

}  // namespace noisemaker::scatter::flow3d
