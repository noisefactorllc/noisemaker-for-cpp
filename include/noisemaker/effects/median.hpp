#pragma once

#include <array>
#include <cstddef>
#include <string_view>
#include <utility>

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {

// Hand-written CPU kernel for filter/median:median, mirroring the authority's
// hand-written JS adapter (src/effects/adapters/median.js) operation-for-
// operation. See src/effects/median.cpp for why this is hand-written rather
// than typed-generated, and for the RADIUS-as-runtime-binding design that
// lets one bound kernel serve every allowed radius (1, 2, 3) instead of the
// typed emitter's single compiled-in RADIUS=2.
[[nodiscard]] BoundKernel bind_median(const glsl::Bindings& bindings);

// Declared contract for bind_median's binding surface: every (name, cpp_type)
// pair it reads from `Bindings`, in the exact order bind_median() reads them.
// Unlike bind_remap (whose zone names are built at runtime), every one of
// these is a literal `b.get<T>("name")` / `b.texture("name")` call in
// median.cpp, so tools/dsl/generate_backend_compatibility.py's generic
// custom-adapter binding-ABI extractor (the one bit_effects.cpp uses) could
// in principle scrape it directly. This table is declared explicitly anyway,
// matching synth/remap:remap's registration shape exactly (declared ABI +
// drift guard) per this lane's routing-change instructions -- see
// tools/glslcpp/frontend/median_profile.py's module docstring. cpp_type
// strings match materialize_plan_value()'s vocabulary in
// src/graph/executor.cpp (std::int32_t, float) except "sampler2D", which
// marks a `Bindings::texture()` read rather than a `Bindings::get`/`get_or`
// uniform read.
inline constexpr std::size_t kMedianBindingAbiSize = 3U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kMedianBindingAbiSize>
    kMedianBindingAbi{{
        {"RADIUS", "std::int32_t"},
        {"threshold", "float"},
        {"inputTex", "sampler2D"},
    }};

}  // namespace noisemaker::effects
