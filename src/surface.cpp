#include "noisemaker/surface.hpp"

#include "noisemaker/numeric.hpp"

#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace noisemaker {
namespace {

std::size_t channel_count(std::size_t width, std::size_t height) {
  if (width == 0 || height == 0) {
    throw std::invalid_argument("surface dimensions must be positive");
  }
  if (height > kMaxSurfacePixels / width) {
    throw std::overflow_error("surface pixel count exceeds allocation limit");
  }
  if (width > std::numeric_limits<std::size_t>::max() / height) {
    throw std::overflow_error("surface pixel count overflows size_t");
  }
  const std::size_t pixels = width * height;
  if (pixels > std::numeric_limits<std::size_t>::max() / 4U) {
    throw std::overflow_error("surface channel count overflows size_t");
  }
  return pixels * 4U;
}

std::uint8_t byte_from_float(float value) noexcept {
  if (!std::isfinite(value) || value <= 0.0f) {
    return 0;
  }
  if (value >= 1.0f) {
    return 255;
  }
  return static_cast<std::uint8_t>(std::floor(static_cast<double>(value) * 255.0 + 0.5));
}

}  // namespace

Surface::Surface(std::size_t width, std::size_t height)
    : width_(width), height_(height), data_(channel_count(width, height)) {}

Surface::Surface(std::size_t width, std::size_t height, std::vector<float> data)
    : width_(width), height_(height), data_(std::move(data)) {
  if (data_.size() != channel_count(width, height)) {
    throw std::invalid_argument("surface data must contain exactly four channels per pixel");
  }
}

Surface Surface::from_rgba8(std::size_t width, std::size_t height,
                            std::span<const std::uint8_t> bytes) {
  const std::size_t count = channel_count(width, height);
  if (bytes.size() != count) {
    throw std::invalid_argument("RGBA8 data must contain exactly four channels per pixel");
  }
  std::vector<float> data(count);
  for (std::size_t index = 0; index < count; ++index) {
    data[index] = f32(static_cast<double>(bytes[index]) / 255.0);
  }
  return Surface(width, height, std::move(data));
}

std::size_t Surface::width() const noexcept {
  return width_;
}

std::size_t Surface::height() const noexcept {
  return height_;
}

std::span<float> Surface::data() noexcept {
  return data_;
}

std::span<const float> Surface::data() const noexcept {
  return data_;
}

TextureFilter Surface::filter() const noexcept {
  return filter_;
}

void Surface::set_filter(TextureFilter filter) noexcept {
  filter_ = filter;
}

Surface Surface::clone() const {
  // Matches the authoritative JavaScript Surface.clone(): only pixel storage
  // is cloned; optional sampler state falls back to the constructor default.
  return Surface(width_, height_, data_);
}

Surface& Surface::clear(const std::array<float, 4>& color) {
  for (std::size_t index = 0; index < data_.size(); index += 4U) {
    data_[index] = color[0];
    data_[index + 1U] = color[1];
    data_[index + 2U] = color[2];
    data_[index + 3U] = color[3];
  }
  return *this;
}

std::vector<std::uint8_t> Surface::to_rgba8() const {
  std::vector<std::uint8_t> bytes(data_.size());
  for (std::size_t index = 0; index < data_.size(); ++index) {
    bytes[index] = byte_from_float(data_[index]);
  }
  return bytes;
}

}  // namespace noisemaker
