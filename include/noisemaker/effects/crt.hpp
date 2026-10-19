#pragma once

#include <array>
#include <cstddef>
#include <string_view>
#include <utility>

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
// Hand-written CPU kernel for filter/crt:crt, mirroring the authority's
// hand-written JS adapter (src/effects/adapters/crt.js) operation for
// operation.
//
// The authority dispatches that adapter for filter/crt:crt instead of the
// transpiled kernel of crt.glsl. The adapter is a direct float32 translation
// of crt.glsl in the order ANGLE's Metal build evaluates it: every operation
// rounds to float32, fused multiply-adds are exact float32 FMAs
// (noisemaker::fma32), division is a times the float32 reciprocal of b, and
// sine is the modelled Apple GPU sine.
[[nodiscard]] BoundKernel bind_crt(const glsl::Bindings& bindings);

// The declared custom_adapter binding ABI, in the exact order bind_crt()
// reads it. tools/glslcpp/frontend/crt_adapter_profile.py's
// verify_custom_adapter_binding_abi() cross-checks this table against its own
// custom_adapter_binding_abi() declaration at generation time and fails
// closed if the two drift.
inline constexpr std::size_t kCrtBindingAbiSize = 9U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kCrtBindingAbiSize>
    kCrtBindingAbi{{
        {"inputTex", "sampler2D"},
        {"resolution", "glsl::Vec2"},
        {"tileOffset", "glsl::Vec2"},
        {"renderScale", "double"},
        {"alpha", "double"},
        {"fullResolution", "glsl::Vec2"},
        {"time", "double"},
        {"speed", "double"},
        {"seed", "std::int32_t"},
    }};
}  // namespace noisemaker::effects
