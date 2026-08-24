#include "noisemaker/sampler.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

namespace noisemaker {
namespace {

std::size_t normalized_index(double coordinate, std::size_t extent) noexcept {
  const double texel = std::floor(coordinate * static_cast<double>(extent));
  if (!(texel >= 0.0)) {
    return 0;
  }
  if (texel >= static_cast<double>(extent)) {
    return extent - 1U;
  }
  return static_cast<std::size_t>(texel);
}

std::size_t clamped_index(double coordinate, std::size_t extent) noexcept {
  if (!(coordinate >= 0.0)) {
    return 0;
  }
  if (coordinate >= static_cast<double>(extent)) {
    return extent - 1U;
  }
  return static_cast<std::size_t>(coordinate);
}

std::size_t clamped_index(int coordinate, std::size_t extent) noexcept {
  if (coordinate <= 0) {
    return 0;
  }
  const std::size_t index = static_cast<std::size_t>(coordinate);
  return index >= extent ? extent - 1U : index;
}

Rgba storage_texel(const Surface& surface, std::size_t x, std::size_t storage_y) noexcept {
  const auto data = surface.data();
  const std::size_t index = (storage_y * surface.width() + x) * 4U;
  return {data[index], data[index + 1U], data[index + 2U], data[index + 3U]};
}

}  // namespace

Rgba sample_nearest_top_down(const Surface& surface, double u, double v) noexcept {
  if (std::isnan(u) || std::isnan(v)) {
    const float nan = std::numeric_limits<float>::quiet_NaN();
    return {nan, nan, nan, nan};
  }
  return storage_texel(surface, normalized_index(u, surface.width()),
                       normalized_index(v, surface.height()));
}

Rgba sample_nearest_bottom_left(const Surface& surface, double u, double v) noexcept {
  if (std::isnan(u) || std::isnan(v)) {
    const float nan = std::numeric_limits<float>::quiet_NaN();
    return {nan, nan, nan, nan};
  }
  const std::size_t shader_y = normalized_index(v, surface.height());
  return storage_texel(surface, normalized_index(u, surface.width()),
                       surface.height() - 1U - shader_y);
}

Rgba sample_nearest_bottom_left(const Surface& surface, float u, float v) noexcept {
  if (surface.filter() == TextureFilter::linear) {
    return sample_bilinear_bottom_left(surface, static_cast<double>(u),
                                       static_cast<double>(v));
  }
  return sample_nearest_bottom_left(surface, static_cast<double>(u),
                                    static_cast<double>(v));
}

Rgba sample_bilinear_bottom_left(const Surface& surface, double u, double v) noexcept {
  const double top_down_v = 1.0 - v;
  const double sample_x = std::clamp(u * static_cast<double>(surface.width()) - 0.5, 0.0,
                                     static_cast<double>(surface.width() - 1U));
  const double sample_y =
      std::clamp(top_down_v * static_cast<double>(surface.height()) - 0.5, 0.0,
                 static_cast<double>(surface.height() - 1U));
  const double base_x = std::floor(sample_x);
  const double base_y = std::floor(sample_y);
  const double x_weight = sample_x - base_x;
  const double y_weight = sample_y - base_y;
  const std::size_t x0 = clamped_index(base_x, surface.width());
  const std::size_t x1 = clamped_index(base_x + 1.0, surface.width());
  const std::size_t y0 = clamped_index(base_y, surface.height());
  const std::size_t y1 = clamped_index(base_y + 1.0, surface.height());
  const Rgba p00 = storage_texel(surface, x0, y0);
  const Rgba p10 = storage_texel(surface, x1, y0);
  const Rgba p01 = storage_texel(surface, x0, y1);
  const Rgba p11 = storage_texel(surface, x1, y1);

  Rgba result{};
  for (std::size_t channel = 0; channel < result.size(); ++channel) {
    const double top = static_cast<double>(p00[channel]) +
                       (static_cast<double>(p10[channel]) -
                        static_cast<double>(p00[channel])) *
                           x_weight;
    const double bottom = static_cast<double>(p01[channel]) +
                          (static_cast<double>(p11[channel]) -
                           static_cast<double>(p01[channel])) *
                              x_weight;
    result[channel] =
        static_cast<float>(top + (bottom - top) * y_weight);
  }
  return result;
}

Rgba texel_fetch_bottom_left(const Surface& surface, int x, int y) noexcept {
  const std::size_t shader_y = clamped_index(y, surface.height());
  return storage_texel(surface, clamped_index(x, surface.width()),
                       surface.height() - 1U - shader_y);
}

}  // namespace noisemaker
