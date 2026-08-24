#pragma once

#include "noisemaker/surface.hpp"

namespace noisemaker {

enum class TextureFormat { rgba16f, rgba8_unorm, rgba32f };

Surface& quantize_texture(Surface& surface, TextureFormat format) noexcept;

}  // namespace noisemaker
