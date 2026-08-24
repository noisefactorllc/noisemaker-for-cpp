#include "noisemaker/pass_runner.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace noisemaker {
namespace {

// `component(value, index)` (glsl-runtime.js:11-13): a scalar broadcasts.
[[nodiscard]] double record_component(const glsl::DerivativeRecord& record,
                                      std::size_t lane) noexcept {
  if (record.lanes == 0U) return record.scalar;
  return lane < record.lanes ? static_cast<double>(record.vector[lane]) : 0.0;
}

[[nodiscard]] glsl::PixelContext make_context(const glsl::Vec2& resolution, float frag_x,
                                              float frag_y, float time, float seed,
                                              std::uint32_t frame, float delta_time) noexcept {
  const glsl::Vec4 frag_coord(frag_x, frag_y, 0.0f, 1.0f);
  return glsl::PixelContext{
      .uv = glsl::Vec2(frag_coord[0] / resolution[0], frag_coord[1] / resolution[1]),
      .frag_coord = frag_coord,
      .resolution = resolution,
      .time = time,
      .seed = seed,
      .frame = frame,
      .delta_time = delta_time,
      .derivative = nullptr,
  };
}

// Difference one ordinal across the four probe corners, reproducing
// glsl-runtime.js:512-533 including its asymmetric missing-ordinal fallbacks:
// `right` falls back to `left` and `top` falls back to `bottom`, NOT to zero.
[[nodiscard]] glsl::DerivativeValue difference_ordinal(
    const std::vector<glsl::DerivativeRecord>& left,
    const std::vector<glsl::DerivativeRecord>& right,
    const std::vector<glsl::DerivativeRecord>& bottom,
    const std::vector<glsl::DerivativeRecord>& top, std::size_t index) noexcept {
  const glsl::DerivativeRecord zero{};
  const glsl::DerivativeRecord& left_value = index < left.size() ? left[index] : zero;
  const glsl::DerivativeRecord& right_value = index < right.size() ? right[index] : left_value;
  const glsl::DerivativeRecord& bottom_value = index < bottom.size() ? bottom[index] : zero;
  const glsl::DerivativeRecord& top_value = index < top.size() ? top[index] : bottom_value;

  glsl::DerivativeValue computed;
  const std::size_t lanes = std::max(std::max(left_value.lanes, right_value.lanes),
                                     std::max(bottom_value.lanes, top_value.lanes));
  if (lanes == 0U) {
    // Scalar: differenced in double, narrowed only when the replay reads it.
    computed.lanes = 0U;
    computed.scalar_x = right_value.scalar - left_value.scalar;
    computed.scalar_y = top_value.scalar - bottom_value.scalar;
    computed.scalar_width = std::fabs(computed.scalar_x) + std::fabs(computed.scalar_y);
    return computed;
  }
  // Vector: every component store narrows, matching the Float32Array buffers.
  computed.lanes = lanes;
  for (std::size_t lane = 0; lane < lanes; ++lane) {
    const float dx = noisemaker::f32(record_component(right_value, lane)
                                     - record_component(left_value, lane));
    const float dy = noisemaker::f32(record_component(top_value, lane)
                                     - record_component(bottom_value, lane));
    computed.vector_x[lane] = dx;
    computed.vector_y[lane] = dy;
    computed.vector_width[lane] = noisemaker::f32(static_cast<double>(std::fabs(dx))
                                                  + static_cast<double>(std::fabs(dy)));
  }
  return computed;
}

}  // namespace

Surface run_pass(const BoundKernel& kernel, std::size_t width, std::size_t height,
                 float time, float seed, std::uint32_t frame, float delta_time) {
  Surface result(width, height);
  auto pixels = result.data();
  const KernelState& state = kernel.state();
  const PixelFn pixel = kernel.pixel();
  const glsl::Vec2 resolution(static_cast<float>(width), static_cast<float>(height));

  const auto store = [&](std::size_t x, std::size_t y, const glsl::Vec4& output) noexcept {
    const std::size_t offset = (y * width + x) * 4U;
    for (std::size_t lane = 0; lane < 4U; ++lane) pixels[offset + lane] = output[lane];
  };

  if (!kernel.uses_derivatives()) {
    for (std::size_t y = 0; y < height; ++y) {
      for (std::size_t x = 0; x < width; ++x) {
        const glsl::PixelContext context =
            make_context(resolution, static_cast<float>(x) + 0.5f,
                         static_cast<float>(height - y) - 0.5f, time, seed, frame, delta_time);
        glsl::Vec4 output;
        pixel(state, context, output);
        store(x, y, output);
      }
    }
    return result;
  }

  // Derivative path, iterated QUAD-MAJOR rather than raster-major.
  //
  // This is a deliberate, documented deviation from the reference. The JS
  // cache-eviction predicate (glsl-runtime.js:541-543) is correct only for JS's
  // raster order, whereas this loop walks fragCoord-space `pixel_y` in the
  // opposite sense (`frag_coord.y = height - row - 0.5`); porting that
  // predicate literally would leak entries or evict too early. Nothing in a
  // kernel carries state across pixels - the reference resets its pools and its
  // derivative ordinal in `beginPixel`, and textures are read-only - so visit
  // order is unobservable in the output. Quad-major then needs no cache at all:
  // each quad's four probes are computed once and consumed immediately by that
  // quad's own members, with the same amortization the reference achieves.
  //
  // All quad geometry is done in fragCoord space, exactly as the reference does
  // it, so the y-flip between raster row and fragCoord never enters the math.
  const std::size_t quads_x = (width + 1U) / 2U;
  const std::size_t quads_y = (height + 1U) / 2U;
  glsl::DerivativeState derivative;
  std::vector<glsl::DerivativeRecord> corner[4];

  for (std::size_t quad_y = 0; quad_y < quads_y; ++quad_y) {
    for (std::size_t quad_x = 0; quad_x < quads_x; ++quad_x) {
      const float x0 = static_cast<float>(quad_x * 2U) + 0.5f;
      const float y0 = static_cast<float>(quad_y * 2U) + 0.5f;

      // Probes sit at the quad members' own fragCoords. The reference does no
      // bounds check here (:502): at the right or bottom edge this legitimately
      // probes one pixel past the canvas, mirroring GPU helper invocations.
      for (std::size_t lane = 0; lane < 4U; ++lane) {
        derivative.mode = glsl::DerivativeMode::Record;
        derivative.index = 0U;
        derivative.records.clear();
        glsl::PixelContext probe = make_context(
            resolution, x0 + static_cast<float>(lane & 1U),
            y0 + static_cast<float>((lane >> 1U) & 1U), time, seed, frame, delta_time);
        probe.derivative = &derivative;
        glsl::Vec4 discarded;
        pixel(state, probe, discarded);
        corner[lane] = derivative.records;  // [bottomLeft, bottomRight, topLeft, topRight]
      }

      for (std::size_t member = 0; member < 4U; ++member) {
        const std::size_t pixel_x = quad_x * 2U + (member & 1U);
        const std::size_t pixel_y = quad_y * 2U + ((member >> 1U) & 1U);
        if (pixel_x >= width || pixel_y >= height) continue;

        const std::size_t x_parity = pixel_x & 1U;
        const std::size_t y_parity = pixel_y & 1U;
        const auto& left = corner[y_parity * 2U];
        const auto& right = corner[y_parity * 2U + 1U];
        const auto& bottom = corner[x_parity];
        const auto& top = corner[x_parity + 2U];

        const std::size_t count = std::max(std::max(left.size(), right.size()),
                                           std::max(bottom.size(), top.size()));
        derivative.values.clear();
        derivative.values.reserve(count);
        for (std::size_t index = 0; index < count; ++index) {
          derivative.values.push_back(difference_ordinal(left, right, bottom, top, index));
        }

        derivative.mode = glsl::DerivativeMode::Replay;
        derivative.index = 0U;
        glsl::PixelContext context =
            make_context(resolution, static_cast<float>(pixel_x) + 0.5f,
                         static_cast<float>(pixel_y) + 0.5f, time, seed, frame, delta_time);
        context.derivative = &derivative;
        glsl::Vec4 output;
        pixel(state, context, output);
        store(pixel_x, height - 1U - pixel_y, output);
      }
    }
  }
  return result;
}

}  // namespace noisemaker
