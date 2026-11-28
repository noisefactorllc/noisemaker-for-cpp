#include "noisemaker/pass_runner.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <span>
#include <unordered_map>
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

enum class Factor { one, zero, src, inverse_src, src_alpha, inverse_src_alpha,
                    dst_alpha, inverse_dst_alpha, dst, inverse_dst };

Factor blend_factor(std::string name) {
  for (char& c : name) {
    if (c == '_') c = '-';
    else if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
  }
  if (name == "zero") return Factor::zero;
  if (name == "src" || name == "src-color") return Factor::src;
  if (name == "one-minus-src" || name == "one-minus-src-color") return Factor::inverse_src;
  if (name == "src-alpha") return Factor::src_alpha;
  if (name == "one-minus-src-alpha") return Factor::inverse_src_alpha;
  if (name == "dst-alpha") return Factor::dst_alpha;
  if (name == "one-minus-dst-alpha") return Factor::inverse_dst_alpha;
  if (name == "dst" || name == "dst-color") return Factor::dst;
  if (name == "one-minus-dst" || name == "one-minus-dst-color") return Factor::inverse_dst;
  return Factor::one;
}

double weight(Factor factor, double src, double dst, double src_alpha, double dst_alpha) {
  switch (factor) {
    case Factor::zero: return 0;
    case Factor::src: return src;
    case Factor::inverse_src: return 1 - src;
    case Factor::src_alpha: return src_alpha;
    case Factor::inverse_src_alpha: return 1 - src_alpha;
    case Factor::dst_alpha: return dst_alpha;
    case Factor::inverse_dst_alpha: return 1 - dst_alpha;
    case Factor::dst: return dst;
    case Factor::inverse_dst: return 1 - dst;
    default: return 1;
  }
}
}  // namespace

void blend_pass_output(const effects::BlendDefinition& blend, Surface& source,
                       const Surface* previous) {
  if (blend.kind == effects::BlendKind::boolean && !blend.enabled) return;
  const auto source_factor = blend.kind == effects::BlendKind::boolean ? Factor::one : blend_factor(blend.factors[0]);
  const auto destination_factor = blend.kind == effects::BlendKind::boolean ? Factor::one : blend_factor(blend.factors[1]);
  const auto output = source.data();
  const auto backdrop = previous && previous->width() == source.width() && previous->height() == source.height()
      ? previous->data() : std::span<const float>{};
  for (std::size_t p = 0; p < output.size(); p += 4) {
    const double source_alpha = output[p + 3];
    const double destination_alpha = backdrop.empty() ? 0 : backdrop[p + 3];
    for (std::size_t c = 0; c < 4; ++c) {
      const double src = output[p + c];
      const double dst = backdrop.empty() ? 0 : backdrop[p + c];
      output[p + c] = static_cast<float>(
          src * weight(source_factor, src, dst, source_alpha, destination_alpha) +
          dst * weight(destination_factor, src, dst, source_alpha, destination_alpha));
    }
  }
}

Surface run_pass(const BoundKernel& kernel, std::size_t width, std::size_t height,
                 float time, float seed, std::uint32_t frame, float delta_time) {
  kernel.validate_pass(width, height);
  Surface result(width, height);
  auto pixels = result.data();
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
        kernel.run_pixel(context, output);
        store(x, y, output);
      }
    }
    return result;
  }

  // Derivative path follows canonical runPass raster order exactly. The first
  // visited member of a 2x2 quad records its four helper invocations; later
  // members replay the cached differences. Invocation order is observable:
  // canonical generated factories retain one fragColor slot across probes,
  // replays, pixels, passes, and copies of the same bound kernel.
  const std::size_t quads_x = (width + 1U) / 2U;
  struct QuadRecords {
    std::array<std::vector<glsl::DerivativeRecord>, 4> corner;
  };
  std::unordered_map<std::size_t, QuadRecords> cache;
  cache.reserve(quads_x);
  glsl::DerivativeState derivative;

  for (std::size_t y = 0; y < height; ++y) {
    const std::size_t pixel_y = height - 1U - y;
    for (std::size_t pixel_x = 0; pixel_x < width; ++pixel_x) {
      const std::size_t quad_x = pixel_x / 2U;
      const std::size_t quad_y = pixel_y / 2U;
      const std::size_t cache_index = quad_y * quads_x + quad_x;
      const float x0 = static_cast<float>(quad_x * 2U) + 0.5f;
      const float y0 = static_cast<float>(quad_y * 2U) + 0.5f;

      auto [cached, inserted] = cache.try_emplace(cache_index);
      if (inserted) {
        // The reference performs no bounds check for probes: edge quads can
        // invoke one-pixel-outside helpers, in bottom-left fragCoord space.
        for (std::size_t lane = 0; lane < 4U; ++lane) {
          derivative.mode = glsl::DerivativeMode::Record;
          derivative.index = 0U;
          derivative.records.clear();
          glsl::PixelContext probe = make_context(
              resolution, x0 + static_cast<float>(lane & 1U),
              y0 + static_cast<float>((lane >> 1U) & 1U), time, seed, frame,
              delta_time);
          probe.derivative = &derivative;
          glsl::Vec4 discarded;
          kernel.run_pixel(probe, discarded);
          cached->second.corner[lane] = derivative.records;
        }
      }

      const std::size_t x_parity = pixel_x & 1U;
      const std::size_t y_parity = pixel_y & 1U;
      const auto& corner = cached->second.corner;
      const auto& left = corner[y_parity * 2U];
      const auto& right = corner[y_parity * 2U + 1U];
      const auto& bottom = corner[x_parity];
      const auto& top = corner[x_parity + 2U];

      const std::size_t count = std::max(std::max(left.size(), right.size()),
                                         std::max(bottom.size(), top.size()));
      derivative.values.clear();
      derivative.values.reserve(count);
      for (std::size_t index = 0; index < count; ++index) {
        derivative.values.push_back(
            difference_ordinal(left, right, bottom, top, index));
      }

      derivative.mode = glsl::DerivativeMode::Replay;
      derivative.index = 0U;
      glsl::PixelContext context =
          make_context(resolution, static_cast<float>(pixel_x) + 0.5f,
                       static_cast<float>(pixel_y) + 0.5f, time, seed, frame,
                       delta_time);
      context.derivative = &derivative;
      glsl::Vec4 output;
      kernel.run_pixel(context, output);
      store(pixel_x, y, output);

      // glsl-runtime.js evicts after the last raster-visited member of the
      // quad. This predicate is copied in fragCoord-space terms.
      const bool last_x = pixel_x == width - 1U;
      const bool first_y_in_traversal = pixel_y == 0U;
      if ((x_parity == 1U || last_x)
          && (y_parity == 0U || first_y_in_traversal)) {
        cache.erase(cached);
      }
    }
  }
  derivative.mode = glsl::DerivativeMode::Approximate;
  return result;
}

std::vector<Surface> run_mrt_pass(const BoundKernelMrt& kernel, std::size_t width,
                                  std::size_t height, float time, float seed,
                                  std::uint32_t frame, float delta_time) {
  return detail::run_fragment_attachments(kernel, width, height, time, seed, frame, delta_time, kernel.output_count());
}

std::vector<Surface> detail::run_fragment_attachments(
    const BoundKernelMrt& kernel, std::size_t width, std::size_t height, float time, float seed,
    std::uint32_t frame, float delta_time, std::size_t attachment_count) {
  if (attachment_count == 0 || attachment_count > kernel.output_count())
    throw std::invalid_argument("fragment attachment count exceeds the compiled outputs");
  kernel.validate_pass(width, height);
  const std::size_t output_count = kernel.output_count();
  std::vector<Surface> results;
  results.reserve(attachment_count);
  for (std::size_t index = 0; index < attachment_count; ++index) {
    results.emplace_back(width, height);
  }
  std::vector<std::span<float>> pixels;
  pixels.reserve(attachment_count);
  for (auto& surface : results) pixels.push_back(surface.data());
  const glsl::Vec2 resolution(static_cast<float>(width), static_cast<float>(height));

  // No admitted MRT kernel uses derivatives (BoundKernelMrt's constructor
  // refuses uses_derivatives=true outright), so this is the only path --
  // the exact non-derivative half of run_pass's raster order and fragCoord
  // convention, generalized from one Vec4 per pixel to `output_count` of
  // them, scattered exactly like `runCanonicalMrtPass`'s `out` scratch
  // buffer (renderer.js:450-490): one kernel call per pixel produces every
  // output atomically, then each 4-lane chunk is stored into its own
  // destination at the same pixel offset.
  std::vector<glsl::Vec4> outputs(output_count);
  for (std::size_t y = 0; y < height; ++y) {
    for (std::size_t x = 0; x < width; ++x) {
      const glsl::PixelContext context =
          make_context(resolution, static_cast<float>(x) + 0.5f,
                       static_cast<float>(height - y) - 0.5f, time, seed, frame, delta_time);
      kernel.run_pixel(context, outputs.data());
      const std::size_t offset = (y * width + x) * 4U;
      for (std::size_t slot = 0; slot < attachment_count; ++slot) {
        for (std::size_t lane = 0; lane < 4U; ++lane) {
          pixels[slot][offset + lane] = outputs[slot][lane];
        }
      }
    }
  }
  return results;
}

}  // namespace noisemaker
