#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <vector>

#include "noisemaker/surface.hpp"

namespace noisemaker {

inline constexpr std::size_t max_png_pixels = 16'777'216;
inline constexpr std::size_t max_png_encoded_bytes = 256U * 1024U * 1024U;
inline constexpr std::size_t max_png_decoded_bytes = 96U * 1024U * 1024U;

// Malformed PNG *bytes* are the canonical runtime error: the input came from a
// file, a socket or a user, and the program that decoded it is not itself
// wrong. It is therefore not a `std::logic_error` -- a caller who writes the
// natural `catch (const std::runtime_error&)` around `decode_png` must catch
// it instead of terminating on bad input.
//
// The size-limit refusals above the constants in this header keep throwing
// `std::overflow_error`, which is also `std::runtime_error`-derived, so that
// same catch covers every way `decode_png` can fail on its input.
class PngError : public std::runtime_error {
 public:
  using std::runtime_error::runtime_error;
};

[[nodiscard]] std::vector<std::uint8_t> encode_png(const Surface& surface);
[[nodiscard]] Surface decode_png(std::span<const std::uint8_t> png);

}  // namespace noisemaker
