#pragma once

#include <cstddef>
#include <cstdint>

#include "noisemaker/kernel.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker {

[[nodiscard]] Surface run_pass(const BoundKernel& kernel, std::size_t width,
                               std::size_t height, float time = 0.0f,
                               float seed = 1.0f, std::uint32_t frame = 0,
                               float delta_time = 0.0f);

}  // namespace noisemaker
