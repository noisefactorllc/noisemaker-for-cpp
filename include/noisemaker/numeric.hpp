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
[[nodiscard]] std::uint16_t float_to_half_rte(float value) noexcept;
[[nodiscard]] float half_to_float(std::uint16_t bits) noexcept;
[[nodiscard]] float float16_truncate(float value) noexcept;

}  // namespace noisemaker
