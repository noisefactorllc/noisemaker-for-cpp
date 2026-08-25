#include "noisemaker/texture_format.hpp"

#include <cmath>
#include <cstdint>

#include "noisemaker/numeric.hpp"

namespace noisemaker {
namespace {

float unorm8(float value) noexcept {
  // JavaScript's comparison-based quantizer leaves NaN untouched. Keep the
  // NaN out of integer conversion while mapping infinities through the same
  // ordered clamps as finite values.
  if (std::isnan(value)) {
    return value;
  }
  if (value <= 0.0f) {
    return 0.0f;
  }
  if (value >= 1.0f) {
    return 1.0f;
  }
  const auto byte = static_cast<std::uint8_t>(
      std::floor(static_cast<double>(value) * 255.0 + 0.5));
  return static_cast<float>(byte) / 255.0f;
}

}  // namespace

Surface& quantize_texture(Surface& surface, TextureFormat format) noexcept {
  switch (format) {
    case TextureFormat::rgba16f:
      for (float& channel : surface.data()) {
        channel = float16_truncate(channel);
      }
      return surface;
    case TextureFormat::rgba8_unorm:
      for (float& channel : surface.data()) {
        channel = unorm8(channel);
      }
      return surface;
    case TextureFormat::rgba32f:
      return surface;
  }
  return surface;
}

}  // namespace noisemaker
