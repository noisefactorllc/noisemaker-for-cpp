#pragma once

#include <array>
#include <cstdint>

namespace noisemaker {

[[nodiscard]] float f32(double value) noexcept;
[[nodiscard]] double glsl_mod(double x, double y) noexcept;
[[nodiscard]] double glsl_round(double value) noexcept;
[[nodiscard]] std::uint32_t umul(std::uint32_t a, std::uint32_t b) noexcept;
[[nodiscard]] std::uint32_t hash_uint32(std::uint32_t value) noexcept;
[[nodiscard]] std::array<std::uint32_t, 3>
pcg3d(std::array<std::uint32_t, 3> value) noexcept;
[[nodiscard]] std::uint32_t float_bits_to_uint(float value) noexcept;
[[nodiscard]] float uint_bits_to_float(std::uint32_t value) noexcept;
// Converts float32 to an IEEE half BIT PATTERN using the JS CPU authority's
// `floatToHalf` rule (glsl-runtime.js:61-81): unconditional +0x1000 round-
// half-up, the authority's subnormal pre-truncation, and canonical 0x7e00 for
// every NaN. This is deliberately NOT IEEE round-to-nearest-even; see
// src/numeric.cpp for the line-by-line transcription.
[[nodiscard]] std::uint16_t float_to_half_js(float value) noexcept;
// Expands an IEEE half BIT PATTERN using the JS CPU authority's `halfToFloat`
// rule (glsl-runtime.js:52-59): every NaN code collapses to the canonical
// 0x7fc00000, sign and payload discarded.
[[nodiscard]] float half_to_float(std::uint16_t value) noexcept;
[[nodiscard]] float float16_truncate(float value) noexcept;

}  // namespace noisemaker
