#pragma once

// C++ port of `flow3dDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/flow3d-deposit.js) -- the scatter half of
// `filter3d/flow3d:deposit`. Agents carry voxel-space xyz positions in
// `stateTex1` and RGB in `stateTex2`. The vertex shader flattens z slices
// into a `volumeSize x volumeSize^2` atlas; the fragment shader deposits
// opaque agent color with additive blending.
//
// This is the one adapter of the six that reads `pass.count`
// (`pass?.count ?? capacity`) -- see registry.hpp's `ScatterPass`.
//
// Numeric contract: plain IEEE double throughout (flow3d-deposit.js never
// calls `Math.fround`); `Math.min`/`Math.max` go through
// `glsl::component_min<double>`/`component_max<double>` (NOT `std::min`/
// `std::max`, which do not reproduce JS's NaN-propagation or signed-zero
// tie-break rules for every argument order); `Math.trunc` is `std::trunc`
// (agrees with JS `Math.trunc` on every double: sign/exponent truncation
// with no rounding ambiguity, same class of function as `Math.ceil`/
// `Math.floor`, which noisemaker/glsl_runtime.hpp already documents as
// needing no fdlibm shim). The only narrowing is the destination's own
// float32 store on `+=`.

#include <cstddef>
#include <optional>

#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::flow3d {

struct Uniforms {
  double density = 0.0;
  double volume_size = 0.0;
};

// `state_tex1`/`state_tex2` mirror JS `inputs.stateTex1`/`stateTex2`.
// `pass_count` mirrors JS `pass?.count` (`std::nullopt` when the pass
// record has no `count` field at all).
[[nodiscard]] std::size_t run_deposit(const Surface& state_tex1, const Surface& state_tex2,
                                       const Uniforms& uniforms, std::optional<double> pass_count,
                                       Surface& destination);

// Registers "filter3d/flow3d:deposit". Called from
// register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::flow3d
