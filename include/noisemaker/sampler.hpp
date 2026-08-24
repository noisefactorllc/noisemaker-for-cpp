#pragma once

#include <array>

#include "noisemaker/surface.hpp"

namespace noisemaker {

using Rgba = std::array<float, 4>;

[[nodiscard]] Rgba sample_nearest_top_down(const Surface& surface, double u, double v) noexcept;
[[nodiscard]] Rgba sample_nearest_bottom_left(const Surface& surface, double u, double v) noexcept;
// Generated GLSL texture() helpers pass Float32 UV lanes through this overload.
// It is the normalized texture seam and consumes Surface::filter(); the
// original binary64 overload above remains an explicit nearest sampler.
[[nodiscard]] Rgba sample_nearest_bottom_left(const Surface& surface, float u, float v) noexcept;
[[nodiscard]] Rgba sample_bilinear_bottom_left(const Surface& surface, double u, double v) noexcept;
[[nodiscard]] Rgba texel_fetch_bottom_left(const Surface& surface, int x, int y) noexcept;

}  // namespace noisemaker
