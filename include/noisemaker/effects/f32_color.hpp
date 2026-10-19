#pragma once

#include <array>
#include <cstddef>
#include <string_view>
#include <utility>

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
// Hand-written CPU kernels for filter/pixelSort:luminance,
// filter/reindex:nmReindexStats and filter/reindex:nmReindexApply, mirroring
// the authority's hand-written JS adapters (src/effects/adapters/f32-color.js)
// operation for operation.
//
// The authority dispatches these adapters instead of the transpiled kernels
// of luminance.glsl, nmReindexStats.glsl and nmReindexApply.glsl. Every
// arithmetic step rounds to float32 as Math.fround does, and Math.pow is
// V8's (noisemaker::fdlibm::pow).
[[nodiscard]] BoundKernel bind_pixel_sort_luminance(const glsl::Bindings& bindings);
[[nodiscard]] BoundKernel bind_reindex_stats(const glsl::Bindings& bindings);
[[nodiscard]] BoundKernel bind_reindex_apply(const glsl::Bindings& bindings);

// The declared custom_adapter binding ABIs, in the exact order each bind_*()
// reads them. tools/glslcpp/frontend/f32_color_adapter_profile.py's
// verify_custom_adapter_binding_abi() cross-checks each table against its own
// declaration at generation time and fails closed if they drift.
inline constexpr std::size_t kPixelSortLuminanceBindingAbiSize = 1U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kPixelSortLuminanceBindingAbiSize>
    kPixelSortLuminanceBindingAbi{{
        {"inputTex", "sampler2D"},
    }};
inline constexpr std::size_t kReindexStatsBindingAbiSize = 1U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kReindexStatsBindingAbiSize>
    kReindexStatsBindingAbi{{
        {"inputTex", "sampler2D"},
    }};
inline constexpr std::size_t kReindexApplyBindingAbiSize = 6U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kReindexApplyBindingAbiSize>
    kReindexApplyBindingAbi{{
        {"inputTex", "sampler2D"},
        {"statsTex", "sampler2D"},
        {"uDisplacement", "double"},
        {"resolution", "glsl::Vec2"},
        {"tileOffset", "glsl::Vec2"},
        {"fullResolution", "glsl::Vec2"},
    }};
}  // namespace noisemaker::effects
