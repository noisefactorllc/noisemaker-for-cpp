#pragma once

// C++ port of `pointsRenderDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:308-343) -- the scatter half of
// `render/pointsRender:deposit`. Golden-ratio density cull (evaluated
// BEFORE reading agent state, same order as upstream), then alive check,
// then the shared flat/ortho/perspective clip-center transform
// (`points_deposit::compute_clip_center`). Agent color is deposited
// unscaled (pointsRender has no `deposit` uniform).
//
// Numeric contract: plain IEEE double throughout (points-deposit.js never
// calls `Math.fround`); the only narrowing is the destination's own
// float32 store on `+=`.

#include <cstddef>

#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::points_render {

struct Uniforms {
  double density = 0.0;
  double view_mode = 0.0;
  double rotate_x = 0.0;
  double rotate_y = 0.0;
  double rotate_z = 0.0;
  double pos_x = 0.0;
  double pos_y = 0.0;
  double pos_z = 0.0;  // JS `uniforms.posZ ?? 0`
  double view_scale = 0.0;
  double field_of_view = 0.0;  // only read when the resolved viewMode == 2.
};

// `xyz_tex`/`rgba_tex` mirror JS `inputs.xyzTex`/`rgbaTex`.
[[nodiscard]] std::size_t run_deposit(const Surface& xyz_tex, const Surface& rgba_tex, const Uniforms& uniforms,
                                       Surface& destination);

// Registers "render/pointsRender:deposit". Called from
// register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::points_render
