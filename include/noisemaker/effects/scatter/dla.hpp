#pragma once

// C++ port of `dlaDepositGridAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:176-216) -- the scatter half of
// `points/dla:depositGrid`. Only agents that "just stuck" this step
// (`vel.y == 1`) deposit; a stuck agent's own color, scaled by
// `uniforms.deposit * 0.1` ("energy"; deposit range [0.5, 20] maps to
// energy [0.05, 2.0] per depositGrid.frag's own comment), is added into the
// destination additively -- INCLUDING alpha, which is `energy` alone, not
// `rgba.a * energy` (see the JS source's own comment on this).
//
// Numeric contract: plain IEEE double throughout (points-deposit.js never
// calls `Math.fround`); the only narrowing is the destination's own
// Float32Array store on `+=`, which C++ `float += double` reproduces
// exactly (usual arithmetic conversions: widen to double, add, narrow back
// to float32 on assignment -- the same round-to-nearest-even the JS
// TypedArray store performs).

#include <cstddef>

#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::dla {

struct Uniforms {
  double deposit = 0.0;
};

// `xyz_tex`/`vel_tex`/`rgba_tex` mirror JS `inputs.xyzTex`/`velTex`/
// `rgbaTex`. Agent count is `xyz_tex.width() * xyz_tex.height()` (the
// agent-state texture's own size, matching depositGrid.vert's own
// `totalAgents = dims.x * dims.y` -- the one adapter of these six that is
// dimension-general rather than assuming a square state texture). Returns
// the number of agents that actually deposited (JS `{ pixels }`).
[[nodiscard]] std::size_t run_deposit(const Surface& xyz_tex, const Surface& vel_tex, const Surface& rgba_tex,
                                       const Uniforms& uniforms, Surface& destination);

// Registers "points/dla:depositGrid" (see noisemaker/effects/scatter/
// registry.hpp). Called from register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::dla
