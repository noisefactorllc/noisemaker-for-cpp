#include "noisemaker/effects/cpu/worm_overlay.hpp"
#include "noisemaker/effects/cpu/worm_overlay_internal.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/numeric.hpp"

// Operation-for-operation port of noisemaker-for-cpu's
// src/effects/cpu/worm-overlay.js (181 lines). See worm_overlay.hpp for the
// precision contract. Every function below corresponds 1:1 to a same-named
// (camelCase vs snake_case) function in the JS file; comments cite the JS
// line ranges from the pinned authority revision 61aa869.

namespace noisemaker::effects::cpu {

namespace {

constexpr double kTau = 6.283185307179586;  // Math.PI * 2, identical double to JS

}  // namespace

namespace detail {

// worm-overlay.js:6-7 -- `this.state = ((seed >>> 0) * 747796405 + 2891336453) >>> 0`.
// ECMA-262 ToUint32(seed): truncate toward zero, reduce mod 2^32.
std::uint32_t to_uint32(double value) noexcept {
  if (!std::isfinite(value)) return 0U;
  double truncated = std::trunc(value);
  double reduced = std::fmod(truncated, 4294967296.0);  // 2^32
  if (reduced < 0.0) reduced += 4294967296.0;
  return static_cast<std::uint32_t>(reduced);
}

// JS's bitwise `^`/`&`/`|`/`~`/`<<`/`>>` all produce a SIGNED int32 result
// (ECMA-262 ToInt32 on the numeric operands), unlike `>>>`, which produces
// an unsigned uint32. When that signed result then feeds an ARITHMETIC
// operator (here, `* 277803737`), JS multiplies the actual signed numeric
// value -- e.g. a bit pattern of 0xE8CB0731 is the double -456730575, not
// 3838236721 -- and since the multiplication can exceed 2^53 and round,
// the sign genuinely changes which double the rounding lands on. Verified
// against a live V8: reinterpreting the XOR result as unsigned before this
// multiply produced `word=3759772544` for one `next()` step where the real
// engine produces `3759772560` -- a 16-count divergence traced to exactly
// this. Converts a 32-bit pattern to the double JS would use as the
// left-hand operand of `^`'s result in further arithmetic.
double as_js_int32(std::uint32_t bits) noexcept {
  return bits >= 0x80000000U ? static_cast<double>(bits) - 4294967296.0
                              : static_cast<double>(bits);
}

// IMPORTANT: `state * 747796405` (state up to 2^32-1, multiplier ~7.5e8) and
// `xorResult * 277803737` below can both exceed 2^53 -- JS performs these as
// ordinary double multiplications, NOT exact integer arithmetic, so the
// product is rounded to the nearest representable double *before* the
// `>>> 0` truncation. A `uint32_t * uint32_t` (exact, wrapping mod 2^32) is
// NOT equivalent and was the first bug this port's own oracle caught: for
// seed 1000's second `next()` step the exact product/sum reduces to
// 2212494646 mod 2^32, but JS's double-rounded value reduces to 2212494848
// -- a 202-count divergence, confirmed against a live V8. Every
// multiply-then-truncate step here MUST go through `double`, matching JS's
// actual (imprecise) arithmetic, never native modular integer arithmetic.
SeededRng::SeededRng(double seed) noexcept
    : state_(to_uint32(static_cast<double>(to_uint32(seed)) * 747796405.0 + 2891336453.0)) {}

// worm-overlay.js:10-14
std::uint32_t SeededRng::next() noexcept {
  state_ = to_uint32(static_cast<double>(state_) * 747796405.0 + 2891336453.0);
  const std::uint32_t shift = (state_ >> 28) + 4U;
  const std::uint32_t xored_bits = (state_ >> shift) ^ state_;
  const std::uint32_t word = to_uint32(as_js_int32(xored_bits) * 277803737.0);
  return (word >> 22) ^ word;
}

// worm-overlay.js:16-18
double SeededRng::float_() noexcept {
  return static_cast<double>(next()) / 4294967295.0;
}

// worm-overlay.js:20-24
double SeededRng::normal(double mean, double deviation) noexcept {
  double u1 = std::max(float_(), 1e-10);
  double u2 = float_();
  return mean + deviation * std::sqrt(-2.0 * fdlibm::log(u1)) * fdlibm::cos(kTau * u2);
}

// worm-overlay.js:27-52
std::vector<float> value_noise_field(std::size_t width, std::size_t height,
                                      double frequency, SeededRng& rng) {
  const std::size_t gridWidth = static_cast<std::size_t>(std::ceil(frequency)) + 2U;
  const std::size_t gridHeight = static_cast<std::size_t>(std::ceil(frequency)) + 2U;
  std::vector<float> grid(gridWidth * gridHeight);
  for (auto& cell : grid) cell = noisemaker::f32(rng.float_());

  std::vector<float> field(width * height);
  for (std::size_t y = 0; y < height; ++y) {
    for (std::size_t x = 0; x < width; ++x) {
      const double fieldX = (static_cast<double>(x) / static_cast<double>(width)) * frequency;
      const double fieldY = (static_cast<double>(y) / static_cast<double>(height)) * frequency;
      const double integerX = std::floor(fieldX);
      const double integerY = std::floor(fieldY);
      const double deltaX = fieldX - integerX;
      const double deltaY = fieldY - integerY;
      const double smoothX = deltaX * deltaX * (3.0 - 2.0 * deltaX);
      const double smoothY = deltaY * deltaY * (3.0 - 2.0 * deltaY);
      const auto ix = static_cast<std::size_t>(integerX);
      const auto iy = static_cast<std::size_t>(integerY);
      const double topLeft = grid[iy * gridWidth + ix];
      const double topRight = grid[iy * gridWidth + ix + 1U];
      const double bottomLeft = grid[(iy + 1U) * gridWidth + ix];
      const double bottomRight = grid[(iy + 1U) * gridWidth + ix + 1U];
      const double value = (topLeft * (1.0 - smoothX) + topRight * smoothX) * (1.0 - smoothY) +
                            (bottomLeft * (1.0 - smoothX) + bottomRight * smoothX) * smoothY;
      field[y * width + x] = noisemaker::f32(value);
    }
  }
  return field;
}

}  // namespace detail

namespace {

using detail::SeededRng;

// worm-overlay.js:54-87
void draw_segment(Surface& surface, double x0, double y0, double x1, double y1,
                   double line_width, const std::array<double, 3>& color, double alpha) {
  if (alpha <= 0.0) return;
  const double radius = line_width * 0.5;
  const double surfaceWidthD = static_cast<double>(surface.width());
  const double surfaceHeightD = static_cast<double>(surface.height());
  const auto minX = static_cast<std::int64_t>(
      std::max(0.0, std::floor(std::min(x0, x1) - radius - 1.0)));
  const auto maxX = static_cast<std::int64_t>(
      std::min(surfaceWidthD - 1.0, std::ceil(std::max(x0, x1) + radius + 1.0)));
  const auto minY = static_cast<std::int64_t>(
      std::max(0.0, std::floor(std::min(y0, y1) - radius - 1.0)));
  const auto maxY = static_cast<std::int64_t>(
      std::min(surfaceHeightD - 1.0, std::ceil(std::max(y0, y1) + radius + 1.0)));
  const double dx = x1 - x0;
  const double dy = y1 - y0;
  const double lengthSquared = dx * dx + dy * dy;
  auto data = surface.data();
  const auto width = surface.width();

  for (std::int64_t y = minY; y <= maxY; ++y) {
    for (std::int64_t x = minX; x <= maxX; ++x) {
      const double px = static_cast<double>(x) + 0.5;
      const double py = static_cast<double>(y) + 0.5;
      const double amount = lengthSquared > 0.0
          ? std::min(std::max(((px - x0) * dx + (py - y0) * dy) / lengthSquared, 0.0), 1.0)
          : 0.0;
      const double nearestX = x0 + dx * amount;
      const double nearestY = y0 + dy * amount;
      const double distance = fdlibm::hypot(px - nearestX, py - nearestY);
      const double coverage = std::min(std::max(radius + 0.5 - distance, 0.0), 1.0);
      const double sourceAlpha = alpha * coverage;
      if (sourceAlpha <= 0.0) continue;
      const std::size_t offset = (static_cast<std::size_t>(y) * width + static_cast<std::size_t>(x)) * 4U;
      const double destinationAlpha = static_cast<double>(data[offset + 3U]);
      const double outputAlpha = sourceAlpha + destinationAlpha * (1.0 - sourceAlpha);
      for (int channel = 0; channel < 3; ++channel) {
        const double value = outputAlpha > 0.0
            ? (color[static_cast<std::size_t>(channel)] * sourceAlpha +
               static_cast<double>(data[offset + static_cast<std::size_t>(channel)]) * destinationAlpha *
                   (1.0 - sourceAlpha)) /
                  outputAlpha
            : 0.0;
        data[offset + static_cast<std::size_t>(channel)] = noisemaker::f32(value);
      }
      data[offset + 3U] = noisemaker::f32(outputAlpha);
    }
  }
}

enum class Behavior { chaotic, obedient, unruly };

struct TraceOptions {
  double seed = 1.0;
  double density = 1.0;
  double kink = 1.0;
  double stride = 1.0;
  double stride_deviation = 0.0;
  double duration = 1.0;
  Behavior behavior = Behavior::chaotic;
  double flow_frequency = 1.0;
  double line_width = 1.0;
  double alpha = 1.0;
  // worm-overlay.js's `color(rng, index)` -- `index` is accepted by two of
  // the three call sites' signatures but used by none of them, so it is
  // dropped here (verified by direct reading of all three call sites: fibers
  // and strayHair declare `(rng) =>`, scratches declares `() =>`).
  std::function<std::array<double, 3>(SeededRng&)> color;
};

// worm-overlay.js:89-122
void trace(Surface& surface, const TraceOptions& options) {
  SeededRng rng(options.seed);
  const double width = static_cast<double>(surface.width());
  const double height = static_cast<double>(surface.height());
  const double minDimension = std::min(width, height);
  const double maxDimension = std::max(width, height);
  const double strideScale = maxDimension / 1024.0;
  // worm-overlay.js:94 -- `new SeededRng(options.seed * 31337)` is a
  // throwaway RNG used only to build the flow field; it never advances
  // `rng` (the worm-drawing generator) and is discarded immediately after.
  SeededRng flowRng(options.seed * 31337.0);
  std::vector<float> flow =
      detail::value_noise_field(surface.width(), surface.height(), options.flow_frequency, flowRng);
  const auto count = static_cast<std::size_t>(
      std::max(1.0, std::floor(maxDimension * options.density)));
  const double sharedRotation = rng.float_() * kTau;

  struct Worm {
    double x = 0.0;
    double y = 0.0;
    double stride = 0.0;
    double rotation = 0.0;
    std::array<double, 3> color{};
  };

  std::vector<Worm> worms(count);
  for (std::size_t index = 0; index < count; ++index) {
    Worm& worm = worms[index];
    // worm-overlay.js:98-102 -- field evaluation order is x, y, stride,
    // rotation, color; each RNG-drawing field consumes state in that exact
    // sequence, so the order below is load-bearing.
    worm.x = rng.float_() * width;
    worm.y = rng.float_() * height;
    worm.stride = rng.normal(options.stride, options.stride_deviation) * strideScale;
    worm.rotation = options.behavior == Behavior::obedient ? sharedRotation : rng.float_() * kTau;
    worm.color = options.color(rng);
  }

  const auto iterations = static_cast<std::size_t>(
      std::max(1.0, std::floor(std::sqrt(minDimension) * options.duration)));

  for (auto& worm : worms) {
    double x = worm.x;
    double y = worm.y;
    for (std::size_t iteration = 0; iteration < iterations; ++iteration) {
      const double lifetime = iterations > 1U
          ? static_cast<double>(iteration) / static_cast<double>(iterations - 1U)
          : 1.0;
      const double exposure = 1.0 - std::abs(1.0 - lifetime * 2.0);
      const double flowX = std::floor(std::fmod(std::fmod(x, width) + width, width));
      const double flowY = std::floor(std::fmod(std::fmod(y, height) + height, height));
      double angle = static_cast<double>(
          flow[static_cast<std::size_t>(flowY) * surface.width() + static_cast<std::size_t>(flowX)]) *
          kTau * options.kink;
      angle += options.behavior == Behavior::obedient ? sharedRotation : worm.rotation;
      const double nextX = x + fdlibm::sin(angle) * worm.stride;
      const double nextY = y + fdlibm::cos(angle) * worm.stride;
      draw_segment(surface, x, y, nextX, nextY, options.line_width, worm.color,
                   options.alpha * exposure);
      x = nextX;
      y = nextY;
    }
  }
}

}  // namespace

bool is_worm_overlay_effect(std::string_view effect_id) noexcept {
  return effect_id == "filter/fibers" || effect_id == "filter/scratches" ||
         effect_id == "filter/strayHair";
}

// worm-overlay.js:124-181
Surface render_canonical_worm_overlay(std::string_view effect_id, std::size_t width,
                                       std::size_t height, double seed_param,
                                       double density_param) {
  Surface surface(width, height);
  // worm-overlay.js:126 -- `const seed = params.seed || 1`: any JS-falsy
  // number (+0, -0, NaN) resolves to 1.
  const double seed = (seed_param == 0.0 || std::isnan(seed_param)) ? 1.0 : seed_param;
  const double density = density_param;

  if (effect_id == "filter/fibers") {
    const double baseDensity = 0.5 + density * 2.0;
    for (int layer = 0; layer < 4; ++layer) {
      const double layerSeed = seed * 1000.0 + static_cast<double>(layer) * 137.0;
      TraceOptions options;
      options.seed = layerSeed;
      options.density = baseDensity;
      options.kink = 5.0 + std::fmod(layerSeed, 5.0);
      options.stride = 0.75;
      options.stride_deviation = 0.125;
      options.duration = 1.0;
      options.behavior = Behavior::chaotic;
      options.flow_frequency = 4.0;
      options.line_width = std::max(1.5, static_cast<double>(width) / 384.0);
      options.color = [](SeededRng& rng) -> std::array<double, 3> {
        return {std::floor(rng.float_() * 200.0 + 55.0) / 255.0,
                std::floor(rng.float_() * 200.0 + 55.0) / 255.0,
                std::floor(rng.float_() * 200.0 + 55.0) / 255.0};
      };
      options.alpha = 0.5;
      trace(surface, options);
    }
  } else if (effect_id == "filter/scratches") {
    for (int layer = 0; layer < 4; ++layer) {
      const double layerSeed = seed * 1000.0 + static_cast<double>(layer) * 251.0;
      TraceOptions options;
      options.seed = layerSeed;
      options.density = 0.1 + density * 0.4;
      options.kink = 0.125 + std::fmod(layerSeed, 50.0) / 400.0;
      options.stride = 0.75;
      options.stride_deviation = 0.5;
      options.duration = 2.0 + std::fmod(layerSeed, 3.0);
      options.behavior = std::fmod(layerSeed, 2.0) == 0.0 ? Behavior::obedient : Behavior::unruly;
      options.flow_frequency = 2.0 + std::fmod(layerSeed, 3.0);
      options.line_width = std::max(0.5, static_cast<double>(width) / 1024.0);
      options.color = [](SeededRng&) -> std::array<double, 3> { return {1.0, 1.0, 1.0}; };
      options.alpha = 1.0;
      trace(surface, options);
    }
  } else if (effect_id == "filter/strayHair") {
    const double layerSeed = seed * 1000.0 + 42.0;
    TraceOptions options;
    options.seed = layerSeed;
    options.density = 0.001 + density * 0.004;
    options.kink = 5.0 + std::fmod(layerSeed, 45.0);
    options.stride = 0.5;
    options.stride_deviation = 0.25;
    options.duration = 8.0 + std::fmod(layerSeed, 8.0);
    options.behavior = Behavior::unruly;
    options.flow_frequency = 4.0;
    options.line_width = std::max(1.0, static_cast<double>(width) / 400.0);
    options.color = [](SeededRng& rng) -> std::array<double, 3> {
      return {std::floor(rng.float_() * 30.0) / 255.0, std::floor(rng.float_() * 30.0) / 255.0,
              std::floor(rng.float_() * 30.0) / 255.0};
    };
    options.alpha = 0.666;
    trace(surface, options);
  } else {
    throw std::invalid_argument("Unsupported canonical CPU overlay " + std::string(effect_id));
  }

  // worm-overlay.js:179 -- quantize to 1/255 steps, stored back through the
  // authority's Float32Array (so through `noisemaker::f32` here too).
  auto data = surface.data();
  for (auto& value : data) {
    const double clamped = std::min(std::max(static_cast<double>(value), 0.0), 1.0);
    value = noisemaker::f32(std::floor(clamped * 255.0 + 0.5) / 255.0);
  }
  return surface;
}

}  // namespace noisemaker::effects::cpu
