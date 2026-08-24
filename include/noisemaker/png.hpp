#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include "noisemaker/surface.hpp"

namespace noisemaker {

inline constexpr std::size_t max_png_pixels = 16'777'216;
inline constexpr std::size_t max_png_encoded_bytes = 256U * 1024U * 1024U;
inline constexpr std::size_t max_png_decoded_bytes = 96U * 1024U * 1024U;

[[nodiscard]] std::vector<std::uint8_t> encode_png(const Surface& surface);
[[nodiscard]] Surface decode_png(std::span<const std::uint8_t> png);

}  // namespace noisemaker
