#pragma once

// C++ port of `leniaDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:226-256) -- the scatter half of
// `points/lenia:deposit`. Every alive agent (`xyz.w >= 0.5`) deposits the
// SAME constant `(depositAmount, 0, 0, 1)` regardless of its own state --
// lenia's `deposit.vert` has no `rgbaTex` input at all, and `deposit.frag`
// ignores agent state entirely.
//
// Numeric contract: each red/alpha addition stores through float32; an
// rgba16f destination also truncates to half float after each point.

#include <cstddef>

#include "noisemaker/texture_format.hpp"

namespace noisemaker::scatter::lenia {

struct Uniforms {
  double deposit_amount = 0.0;
};

// `xyz_tex` mirrors JS `inputs.xyzTex`. Agent count is
// `xyz_tex.width() * xyz_tex.height()` (matches deposit.vert's own
// `totalAgents = stateSize.x * stateSize.x` only because every lenia
// particle-state texture in the current catalog is square -- see
// points-deposit.js's own header note). Returns the number of agents that
// actually deposited.
[[nodiscard]] std::size_t run_deposit(const Surface& xyz_tex, const Uniforms& uniforms, Surface& destination,
                                      TextureFormat destination_format = TextureFormat::rgba32f);

// Registers "points/lenia:deposit". Called from
// register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::lenia
