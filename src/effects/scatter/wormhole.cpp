#include "noisemaker/effects/scatter/wormhole.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>

#include "noisemaker/effects/scatter/registry.hpp"

namespace noisemaker::scatter::wormhole {
namespace {

constexpr double kTau = 6.28318530717959;
constexpr double kPi = 3.141592653589793;  // identical double to JS Math.PI

[[nodiscard]] double f32r(double value) noexcept { return static_cast<double>(static_cast<float>(value)); }
[[nodiscard]] double add(double left, double right) noexcept { return f32r(left + right); }
[[nodiscard]] double mul(double left, double right) noexcept { return f32r(left * right); }
[[nodiscard]] double divd(double left, double right) noexcept { return f32r(left / right); }

[[nodiscard]] double oklab_lightness(double red, double green, double blue) noexcept {
  const double r = std::min(std::max(red, 0.0), 1.0);
  const double g = std::min(std::max(green, 0.0), 1.0);
  const double b = std::min(std::max(blue, 0.0), 1.0);
  const double l = add(add(mul(f32r(0.4122214708), r), mul(f32r(0.5363325363), g)), mul(f32r(0.0514459929), b));
  const double m = add(add(mul(f32r(0.2119034982), r), mul(f32r(0.6806995451), g)), mul(f32r(0.1073969566), b));
  const double s = add(add(mul(f32r(0.0883024619), r), mul(f32r(0.2817188376), g)), mul(f32r(0.6299787005), b));
  const double exponent = divd(1.0, 3.0);
  const double lr = f32r(std::pow(std::max(l, 0.0), exponent));
  const double mr = f32r(std::pow(std::max(m, 0.0), exponent));
  const double sr = f32r(std::pow(std::max(s, 0.0), exponent));
  return add(add(mul(f32r(0.2104542553), lr), mul(f32r(0.793617785), mr)), mul(f32r(-0.0040720468), sr));
}

[[nodiscard]] std::int64_t wrap_repeat(std::int64_t value, std::int64_t size) noexcept {
  return ((value % size) + size) % size;
}
[[nodiscard]] std::int64_t wrap_mirror(std::int64_t value, std::int64_t size) noexcept {
  const std::int64_t doubled = size * 2;
  const std::int64_t mirrored = wrap_repeat(value, doubled);
  const std::int64_t diff = mirrored - size + 1;
  const std::int64_t abs_diff = diff < 0 ? -diff : diff;
  return size - 1 - abs_diff;
}

[[nodiscard]] std::int32_t to_int32_bitwise_or_zero(double value) noexcept {
  if (!std::isfinite(value)) return 0;
  const double truncated = std::trunc(value);
  double modded = std::fmod(truncated, 4294967296.0);  // 2^32
  if (modded < 0) modded += 4294967296.0;
  const auto u = static_cast<std::uint32_t>(modded);
  std::int32_t signed_value;
  std::memcpy(&signed_value, &u, sizeof(signed_value));
  return signed_value;
}

[[nodiscard]] std::uint32_t float_to_bits(float value) noexcept {
  std::uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}
[[nodiscard]] float decode_float16(std::uint16_t bits) noexcept {
  const double sign = ((bits & 0x8000u) == 0u) ? 1.0 : -1.0;
  const int exponent = (bits >> 10) & 0x1f;
  const int fraction = bits & 0x3ff;
  if (exponent == 0) return static_cast<float>(sign * static_cast<double>(fraction) * std::pow(2.0, -24.0));
  if (exponent == 0x1f) {
    if (fraction == 0) return sign > 0.0 ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity();
    return std::numeric_limits<float>::quiet_NaN();
  }
  return static_cast<float>(sign * (1.0 + static_cast<double>(fraction) / 1024.0) * std::pow(2.0, static_cast<double>(exponent - 15)));
}
// A real rgba16f store: truncating (round-toward-zero mantissa truncation,
// not round-to-nearest), matching texture-format.js's
// `float16Truncate`/`decodeFloat16` pair bit manipulation for bit
// manipulation.
[[nodiscard]] float float16_truncate(double value) noexcept {
  const std::uint32_t bits = float_to_bits(static_cast<float>(value));
  const std::uint32_t sign = (bits >> 16) & 0x8000u;
  const std::uint32_t source_exponent = (bits >> 23) & 0xffu;
  const std::uint32_t fraction = bits & 0x7fffffu;
  if (source_exponent == 0xffu) {
    if (fraction == 0u) return sign == 0u ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity();
    return std::numeric_limits<float>::quiet_NaN();
  }
  const int exponent = static_cast<int>(source_exponent) - 127 + 15;
  std::uint32_t half_bits;
  if (exponent >= 0x1f) {
    half_bits = sign | 0x7bffu;
  } else if (exponent <= 0) {
    half_bits = (exponent < -10) ? sign : (sign | (((fraction | 0x800000u) >> (1 - exponent)) >> 13));
  } else {
    half_bits = sign | (static_cast<std::uint32_t>(exponent) << 10) | (fraction >> 13);
  }
  return decode_float16(static_cast<std::uint16_t>(half_bits));
}

std::size_t adapter(const glsl::Bindings& bindings, Surface& destination) {
  const Surface& input = bindings.texture("inputTex");
  Uniforms uniforms;
  uniforms.kink = bindings.get_number("kink");
  uniforms.stride = bindings.get_number("stride");
  uniforms.rotation = bindings.get_number("rotation");
  uniforms.wrap = bindings.get_number("wrap");
  run_deposit(input, destination, uniforms);
  return input.width() * input.height();
}

}  // namespace

void run_deposit(const Surface& input, Surface& destination, const Uniforms& uniforms) {
  if (input.width() != destination.width() || input.height() != destination.height()) {
    throw std::invalid_argument("wormhole deposit requires matching source and destination dimensions");
  }
  const auto width = static_cast<std::int64_t>(input.width());
  const auto height = static_cast<std::int64_t>(input.height());
  const auto input_data = input.data();
  const auto output_data = destination.data();

  const double kink = uniforms.kink;
  const double pixel_stride = 1024.0 * uniforms.stride;  // double precision -- see header note
  const double rotation = divd(mul(f32r(uniforms.rotation), f32r(kPi)), 180.0);
  const std::int32_t wrap = to_int32_bitwise_or_zero(uniforms.wrap);

  for (std::int64_t source_y = 0; source_y < height; source_y += 1) {
    for (std::int64_t source_x = 0; source_x < width; source_x += 1) {
      const std::int64_t source_row = height - 1 - source_y;
      const auto source_offset = static_cast<std::size_t>((source_row * width + source_x) * 4);

      const double lightness = oklab_lightness(input_data[source_offset], input_data[source_offset + 1], input_data[source_offset + 2]);
      const double angle = add(mul(mul(lightness, f32r(kTau)), f32r(kink)), rotation);
      const double offset_x = mul(add(f32r(std::cos(angle)), 1.0), f32r(pixel_stride));
      const double offset_y = mul(add(f32r(std::sin(angle)), 1.0), f32r(pixel_stride));

      std::int64_t destination_x = static_cast<std::int64_t>(std::floor(add(static_cast<double>(source_x), offset_x)));
      std::int64_t destination_y = static_cast<std::int64_t>(std::floor(add(static_cast<double>(source_y), offset_y)));

      if (wrap == 0) {
        destination_x = wrap_mirror(destination_x, width);
        destination_y = wrap_mirror(destination_y, height);
      } else if (wrap == 2) {
        destination_x = std::min(std::max(destination_x, std::int64_t{0}), width - 1);
        destination_y = std::min(std::max(destination_y, std::int64_t{0}), height - 1);
      } else {
        destination_x = wrap_repeat(destination_x, width);
        destination_y = wrap_repeat(destination_y, height);
      }

      // See header/wormhole-report.md: wrapMirror can legitimately return -1
      // (value ≡ -1 mod 2*size); JS silently no-ops the resulting
      // out-of-range TypedArray write. Bounds-check the FLAT offset (not X/Y
      // independently -- an out-of-range X with an in-range row can alias
      // into the previous row's last pixel, which JS really does write to).
      const std::int64_t destination_row = height - 1 - destination_y;
      const std::int64_t destination_offset_signed = (destination_row * width + destination_x) * 4;
      const std::int64_t total_lanes = width * height * 4;
      if (destination_offset_signed < 0 || destination_offset_signed + 2 >= total_lanes) {
        continue;
      }
      const auto destination_offset = static_cast<std::size_t>(destination_offset_signed);

      const double weight = mul(lightness, lightness);
      output_data[destination_offset] = float16_truncate(add(output_data[destination_offset], mul(input_data[source_offset], weight)));
      output_data[destination_offset + 1] = float16_truncate(add(output_data[destination_offset + 1], mul(input_data[source_offset + 1], weight)));
      output_data[destination_offset + 2] = float16_truncate(add(output_data[destination_offset + 2], mul(input_data[source_offset + 2], weight)));
      // Alpha (destination_offset + 3) is deliberately left untouched.
    }
  }
}

void register_adapter() { scatter::register_scatter_adapter("filter/wormhole:deposit", &adapter); }

}  // namespace noisemaker::scatter::wormhole
