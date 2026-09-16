#pragma once

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
// Hand-written CPU kernel for filter/snow:snow, mirroring the authority's
// hand-written JS adapter (src/effects/adapters/snow.js) operation-for-
// operation.
//
// filter/snow is corpus-status "adapter": the authority never runs a
// typed-generated kernel for this program at all, so there is no GLSL
// spec to match against -- snow.js itself, byte for byte, is the ground
// truth. Measured against the typed-generated kernel this port replaces
// (compiled from the *GLSL* source, which is a DIFFERENT, only loosely
// related computation the authority never executes), 499 of 748 RGBA8
// bytes diverged at 17x11. This kernel instead reads exactly the five
// bindings snow.js reads (`inputTex`, `alpha`, `time`, `pause`, `density`
// -- notably NOT `resolution`, `tileOffset`, or `fullResolution`: snow.js
// never binds them) and matches its float32-per-operation arithmetic,
// including its two hash-noise samples, its clamped/Y-flipped texel
// fetch, and its early alpha==0 passthrough, exactly.
[[nodiscard]] BoundKernel bind_snow(const glsl::Bindings& bindings);
}  // namespace noisemaker::effects
