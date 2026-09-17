#pragma once

// C++ port of `physarumDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:264-296) -- the scatter half of
// `points/physarum:deposit`. Every alive agent (`pos.w >= 0.5`) deposits
// its own color, scaled by the `deposit` uniform, into ALL FOUR channels
// (including alpha, unlike dla's fixed-alpha rule).
//
// Numeric contract: same as dla.hpp/lenia.hpp -- plain IEEE double
// throughout, the only narrowing is the destination's own float32 store on
// `+=`.

#include <cstddef>

#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::physarum {

struct Uniforms {
  double deposit = 0.0;
};

// `xyz_tex`/`rgba_tex` mirror JS `inputs.xyzTex`/`rgbaTex`. Agent count is
// `xyz_tex.width() * xyz_tex.height()`.
[[nodiscard]] std::size_t run_deposit(const Surface& xyz_tex, const Surface& rgba_tex, const Uniforms& uniforms,
                                       Surface& destination);

// Registers "points/physarum:deposit". Called from
// register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::physarum
