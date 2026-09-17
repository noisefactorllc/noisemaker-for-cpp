#include "noisemaker/effects/scatter/points_deposit_support.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>

#include "noisemaker/fdlibm.hpp"

namespace noisemaker::scatter::points_deposit {

double js_min(double a, double b) noexcept {
  if (std::isnan(a)) return a;
  if (std::isnan(b)) return b;
  if (a == 0.0 && b == 0.0) return (std::signbit(a) || std::signbit(b)) ? -0.0 : 0.0;
  return b < a ? b : a;
}

double js_max(double a, double b) noexcept {
  if (std::isnan(a)) return a;
  if (std::isnan(b)) return b;
  if (a == 0.0 && b == 0.0) return (!std::signbit(a) || !std::signbit(b)) ? 0.0 : -0.0;
  return a < b ? b : a;
}

std::int32_t to_int32_or_zero(double value) noexcept {
  if (!std::isfinite(value)) return 0;
  const double truncated = std::trunc(value);
  double modded = std::fmod(truncated, 4294967296.0);  // 2^32
  if (modded < 0) modded += 4294967296.0;
  const auto u = static_cast<std::uint32_t>(modded);
  std::int32_t signed_value;
  std::memcpy(&signed_value, &u, sizeof(signed_value));
  return signed_value;
}

Rgba texel_fetch_agent(const Surface& surface, std::int64_t sx, std::int64_t sy) noexcept {
  const auto width = static_cast<std::int64_t>(surface.width());
  const auto height = static_cast<std::int64_t>(surface.height());
  const std::int64_t x = sx < 0 ? 0 : (sx >= width ? width - 1 : sx);
  const std::int64_t shader_y = sy < 0 ? 0 : (sy >= height ? height - 1 : sy);
  const std::int64_t y = height - 1 - shader_y;
  const auto offset = static_cast<std::size_t>((y * width + x) * 4);
  const auto data = surface.data();
  return {data[offset], data[offset + 1], data[offset + 2], data[offset + 3]};
}

std::optional<std::size_t> scatter_point_pixel(double clip_x, double clip_y, double clip_w, std::int64_t dest_width,
                                                std::int64_t dest_height) noexcept {
  if (!(clip_w > 0.0)) return std::nullopt;
  const double ndc_x = clip_x / clip_w;
  const double ndc_y = clip_y / clip_w;
  const double gl_col = std::floor((ndc_x * 0.5 + 0.5) * static_cast<double>(dest_width));
  const double gl_row = std::floor((ndc_y * 0.5 + 0.5) * static_cast<double>(dest_height));
  if (!std::isfinite(gl_col) || !std::isfinite(gl_row)) return std::nullopt;
  if (gl_col < 0.0 || gl_col >= static_cast<double>(dest_width) || gl_row < 0.0 ||
      gl_row >= static_cast<double>(dest_height)) {
    return std::nullopt;
  }
  const double storage_row = static_cast<double>(dest_height) - 1.0 - gl_row;
  const double offset = (storage_row * static_cast<double>(dest_width) + gl_col) * 4.0;
  return static_cast<std::size_t>(offset);
}

std::optional<ClipCenter> compute_clip_center(double x, double y, double z, const ClipCenterUniforms& uniforms,
                                               std::int64_t dest_width, std::int64_t dest_height) noexcept {
  const std::int32_t view_mode = to_int32_or_zero(uniforms.view_mode);
  if (view_mode == 0) {
    return ClipCenter{x * 2.0 - 1.0, y * 2.0 - 1.0, 80.0, 0.0, 1.0};
  }

  const bool is_2d_system =
      view_mode == 1 && std::fabs(z) < 1.0 && x >= 0.0 && x <= 1.0 && y >= 0.0 && y <= 1.0;
  double px = x;
  double py = y;
  double pz = z;
  if (is_2d_system) {
    px = x - 0.5;
    py = y - 0.5;
    pz = 0.0;
  }

  const double cos_x = fdlibm::cos(uniforms.rotate_x);
  const double sin_x = fdlibm::sin(uniforms.rotate_x);
  const double x1 = px;
  const double y1 = py * cos_x - pz * sin_x;
  const double z1 = py * sin_x + pz * cos_x;

  const double cos_y = fdlibm::cos(uniforms.rotate_y);
  const double sin_y = fdlibm::sin(uniforms.rotate_y);
  const double x2 = x1 * cos_y + z1 * sin_y;
  const double y2 = y1;
  const double z2 = -x1 * sin_y + z1 * cos_y;

  const double cos_z = fdlibm::cos(uniforms.rotate_z);
  const double sin_z = fdlibm::sin(uniforms.rotate_z);
  double fx = x2 * cos_z - y2 * sin_z;
  double fy = x2 * sin_z + y2 * cos_z;
  const double fz = z2 + uniforms.pos_z;

  fx += uniforms.pos_x;
  fy += uniforms.pos_y;

  const double camera_depth = 80.0 - fz;
  const double camera_distance = std::sqrt(fx * fx + fy * fy + camera_depth * camera_depth);
  double projected_scale = 1.0;
  double clip_x;
  double clip_y;
  if (view_mode == 2) {
    if (camera_depth <= 0.1) return std::nullopt;
    const double focal_length = 1.0 / fdlibm::tan(js_min(js_max(uniforms.field_of_view, 10.0), 150.0) * 0.00872664626);
    clip_x = ((fx * focal_length * uniforms.view_scale) / camera_depth) *
             (static_cast<double>(dest_height) / static_cast<double>(dest_width));
    clip_y = (fy * focal_length * uniforms.view_scale) / camera_depth;
    projected_scale = (80.0 * focal_length * uniforms.view_scale) / (1.732050808 * camera_depth);
  } else if (is_2d_system) {
    clip_x = fx * 3.5 * uniforms.view_scale;
    clip_y = fy * 3.5 * uniforms.view_scale;
  } else {
    clip_x = (fx / 40.0) * uniforms.view_scale;
    clip_y = (fy / 40.0) * uniforms.view_scale;
  }
  return ClipCenter{clip_x, clip_y, camera_depth, camera_distance, projected_scale};
}

double get_number_or(const glsl::Bindings& bindings, std::string_view name, double fallback) {
  try {
    return bindings.get_number(name);
  } catch (const glsl::KernelBindingError&) {
    return fallback;
  }
}

}  // namespace noisemaker::scatter::points_deposit
