#pragma once

// Float division as the Apple GPU authority evaluates it.
//
// This is a port of the CPU authority's src/csl/metal-division.js. ANGLE's
// Metal backend compiles WebGL2 shaders with fast math, so a GLSL `a / b`
// with a run-time divisor becomes `a * rcp(b)`: the product of the float32
// dividend and the hardware reciprocal of the float32 divisor. The Apple M4
// reciprocal is not correctly rounded. For some mantissas it is one ulp away
// from the correctly rounded value; the deviation depends only on the
// mantissa. The deviating mantissas come from the authority's measured
// capture, which src/metal_reciprocal_data.cpp embeds byte for
// byte. Subnormal inputs and results flush to zero, as on the GPU.

#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace noisemaker::metal {

// The authority's METAL_RECIPROCAL record (src/csl/metal-reciprocal-data.js).
// `bits` holds the base64 band bitstream exactly as the authority writes it,
// one string per source line.
struct ReciprocalData {
  double band_low;
  double band_high;
  std::size_t band_bits;
  std::size_t positive_deviations;
  std::size_t negative_deviations;
  std::string_view table_sha256;
  std::string_view bits_sha256;
  std::string_view authority_module_sha256;
  const std::string_view* bits;
  std::size_t bits_lines;
};

[[nodiscard]] const ReciprocalData& reciprocal_data() noexcept;

// Where the exact reciprocal of 1 + mantissa / 2^23 falls on the float32 grid,
// as a fraction of one ulp (metal-reciprocal-grid.js).
[[nodiscard]] double reciprocal_grid_position(std::uint32_t mantissa) noexcept;
[[nodiscard]] bool in_reciprocal_band(std::uint32_t mantissa, const ReciprocalData& data) noexcept;

// Expands the band bitstream into one bit per mantissa (2^23 bits, low bit
// first), as decodeReciprocalDeviations does. Throws std::runtime_error when
// the bitstream or its counts are corrupt.
[[nodiscard]] std::vector<std::uint8_t> decode_reciprocal_deviations(const ReciprocalData& data);

// The hardware reciprocal of a float32 value (metalReciprocal). The argument
// is rounded to float32 first; the result is a float32 value.
[[nodiscard]] double metal_reciprocal(double value) noexcept;

// `a / b` for a run-time divisor (metalDivide). Both operands round to
// float32 and flush subnormals to zero. The product is exact in double and is
// returned unrounded, so a following add rounds once, like the fused
// multiply-add the GPU emits for `a / b + c`.
[[nodiscard]] double metal_divide(double dividend, double divisor) noexcept;

}  // namespace noisemaker::metal
