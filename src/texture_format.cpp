#include "noisemaker/texture_format.hpp"

#include <cmath>
#include <cstdint>

#include "noisemaker/numeric.hpp"

namespace noisemaker {
namespace {

std::uint8_t unorm8(float value) noexcept {
  if (!std::isfinite(value) || value <= 0.0f) {
    return 0;
  }
  if (value >= 1.0f) {
    return 255;
  }
  return static_cast<std::uint8_t>(std::floor(static_cast<double>(value) * 255.0 + 0.5));
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
        channel = static_cast<float>(unorm8(channel)) / 255.0f;
      }
      return surface;
    case TextureFormat::rgba32f:
      return surface;
  }
  return surface;
}

}  // namespace noisemaker
