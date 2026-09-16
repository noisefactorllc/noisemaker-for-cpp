#include "noisemaker/effects/median.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

// Hand-written CPU kernel for filter/median:median.
//
// Why hand-written, not typed-generated: the authority never runs the typed
// kernel emitted from median.glsl. It always dispatches its own hand-written
// CPU adapter (src/effects/adapters/median.js, 134 lines, registered in
// src/effects/adapters/index.js) instead. That adapter reads RADIUS as a
// plain runtime binding (`$bindings.RADIUS | 0`) on every pixel -- it is
// NOT a GLSL preprocessor define there, unlike the *typed* median.glsl this
// port replaces, which bakes RADIUS in as a compile-time #define. cpp's
// generated typed_filter_median_median kernel was therefore only ever
// compiled for one RADIUS value (2, the row's "default-only" bake); any
// other requested radius (the effect's own default is 3, and 1 is also
// allowed) hit executor.cpp's compile-define-vs-requested-value refusal
// before ever reaching a kernel. Mirroring median.js by hand instead makes
// RADIUS an ordinary runtime `Bindings` read (see bind_median below), so one
// bound kernel correctly serves every allowed radius.
//
// This kernel mirrors median.js operation-for-operation, including its exact
// JS numeric semantics:
//   * Luminance is `Math.fround`-chained at every step (three nested
//     `Math.fround` calls, not a single rounding at the end) -- reproduced
//     here with `noisemaker::f32()` at each of those same points.
//   * The per-sample "record" used for ranking packs the luminance's raw
//     float32 BIT PATTERN (via `floatBits`/`float_bits_to_uint`) as an
//     unsigned integer key, and the red/green channels as packed IEEE half
//     BIT PATTERNS (via median.js's own local `floatToHalf`, which is NOT
//     IEEE round-to-nearest-even -- it is bit-for-bit the same rule as
//     `noisemaker::float_to_half_js`, glsl-runtime.js:61-81, unconditional
//     round-half-up). Comparisons on these records are plain unsigned
//     integer comparisons, never a floating-point comparison -- this
//     matters for negative or NaN luminance/channel values, whose IEEE bit
//     patterns do not order the same way their float values would.
//   * The median is found by median.js's own hand-rolled selection
//     algorithm: repeated Hoare partitioning with a FIXED pivot re-read from
//     the (always in-range) median index on every outer iteration, not a
//     randomized quickselect. Reproduced verbatim, including operand order
//     in every comparison, so any two engines select the exact same record
//     among true ties (records whose full three-key tuple is identical).
//     The fixed-pivot invariant (left <= medianIndex <= right, maintained by
//     the same narrowing median.js does) guarantees scanLeft/scanRight never
//     leave [left, right], so this port uses plain `std::size_t` indices
//     with no negative-index special case -- unlike a JS `TypedArray`, an
//     out-of-range `std::size_t` read would be undefined behavior, and never
//     actually occurs here.
//   * The selected record's half-packed channels are expanded back with
//     median.js's own local `halfToFloat` (`noisemaker::half_to_float`),
//     which is a lossless (exact, zero-rounding-error) half-to-float32
//     widening -- so unlike remap.js/snow.js there is no meaningful
//     double-vs-float32 seam to get wrong here.
//   * `maximumDifference` mirrors `Math.max(Math.abs(...), Math.abs(...),
//     Math.abs(...))` in plain `double` -- but `Math.max` propagates NaN
//     (returns NaN if ANY argument is NaN) while `std::max`'s
//     `operator<`-based tie-break does NOT reliably do that for NaN
//     operands. `js_max3` below reproduces the JS propagation explicitly;
//     getting this wrong can flip the threshold-gated `replace` decision for
//     any input that carries a NaN channel.
//   * Alpha is never touched by the ranking or the threshold gate: `out[3]`
//     is always the ORIGINAL center pixel's alpha, exactly matching
//     `surface.data[centerOffset + 3]` in median.js.
namespace noisemaker::effects {
namespace {

using glsl::Vec4;

// RADIUS's declared range is [1, 3] (filter/median's `radius` parameter);
// window side is `2 * RADIUS + 1`, so the largest window is 7x7 = 49 --
// exactly median.js's three fixed-size `Uint32Array(49)` record arrays.
constexpr int kMaxRadius = 3;
constexpr std::size_t kMaxWindow =
    static_cast<std::size_t>(2 * kMaxRadius + 1) * static_cast<std::size_t>(2 * kMaxRadius + 1);

// `Math.max(a, b, c)` propagates NaN: the result is NaN if any argument is
// NaN. `std::max` does not reliably do this (it is `operator<`-based, and
// every relational comparison against NaN is false), so this is spelled out
// rather than reused.
[[nodiscard]] double js_max3(double a, double b, double c) noexcept {
  if (std::isnan(a) || std::isnan(b) || std::isnan(c)) {
    return std::numeric_limits<double>::quiet_NaN();
  }
  return std::max(std::max(a, b), c);
}

struct State final : KernelState {
  const Surface* input_tex = nullptr;
  std::int32_t radius = 2;
  double threshold = 0.0;
};

void pixel(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const State&>(base);
  // `context.fragCoord[0] | 0` / `[1] | 0` in median.js: ToInt32 truncates
  // toward zero. fragCoord is always a small non-negative pixel-center
  // float here, so a plain truncating cast agrees with ToInt32 bit for bit
  // (same reasoning as snow.cpp's texelOffset).
  const int center_x = static_cast<int>(ctx.frag_coord[0]);
  const int center_y = static_cast<int>(ctx.frag_coord[1]);
  // RADIUS is a real runtime binding here (see the file header), clamped to
  // the fixed window capacity as cheap defense-in-depth; every corpus-legal
  // request (1, 2, or 3) is already within it.
  const int radius = std::clamp(static_cast<int>(s.radius), 0, kMaxRadius);

  // `surface.data[centerOffset..centerOffset+3]` in median.js: the center
  // sample is read directly, not through the ranking window loop below --
  // it survives even when the window itself is degenerate (radius clamped
  // to 0 would still read exactly the center pixel).
  const Rgba center = texel_fetch_bottom_left(*s.input_tex, center_x, center_y);
  const double original_red = static_cast<double>(center[0]);
  const double original_green = static_cast<double>(center[1]);
  const double original_blue = static_cast<double>(center[2]);
  const float original_alpha = center[3];

  std::array<std::uint32_t, kMaxWindow> brightness{};
  std::array<std::uint32_t, kMaxWindow> red_green{};
  std::array<std::uint32_t, kMaxWindow> blue{};

  std::size_t index = 0;
  for (int y = -radius; y <= radius; ++y) {
    for (int x = -radius; x <= radius; ++x) {
      const Rgba sample = texel_fetch_bottom_left(*s.input_tex, center_x + x, center_y + y);
      const float red = sample[0];
      const float green = sample[1];
      const float sample_blue = sample[2];
      // luminance = fround(fround(fround(red*0.2126) + fround(green*0.7152)) + fround(blue*0.0722))
      // -- three nested fround calls, exactly as median.js chains them, not
      // a single rounding of the whole dot product.
      const float l_red = noisemaker::f32(static_cast<double>(red) * 0.2126);
      const float l_green = noisemaker::f32(static_cast<double>(green) * 0.7152);
      const float l_red_green = noisemaker::f32(static_cast<double>(l_red) + static_cast<double>(l_green));
      const float l_blue = noisemaker::f32(static_cast<double>(sample_blue) * 0.0722);
      const float luminance =
          noisemaker::f32(static_cast<double>(l_red_green) + static_cast<double>(l_blue));

      const std::uint16_t packed_red = noisemaker::float_to_half_js(red);
      const std::uint16_t packed_green = noisemaker::float_to_half_js(green);
      brightness[index] = noisemaker::float_bits_to_uint(luminance);
      red_green[index] = (static_cast<std::uint32_t>(packed_red) << 16U) |
                         static_cast<std::uint32_t>(packed_green);
      blue[index] = static_cast<std::uint32_t>(noisemaker::float_to_half_js(sample_blue));
      ++index;
    }
  }

  const std::size_t count = index;
  const std::size_t median_index = (count - 1U) >> 1U;
  std::size_t left = 0U;
  std::size_t right = count - 1U;

  // Mirrors median.js's hand-rolled selection loop exactly: a fixed pivot
  // re-read from `median_index` on every outer iteration (never a randomized
  // or first/last-element pivot), then one Hoare partition pass narrowing
  // [left, right] toward it. See the file header for why scanLeft/scanRight
  // provably never leave [left, right].
  while (left < right) {
    const std::uint32_t pivot_brightness = brightness[median_index];
    const std::uint32_t pivot_red_green = red_green[median_index];
    const std::uint32_t pivot_blue = blue[median_index];
    std::size_t scan_left = left;
    std::size_t scan_right = right;
    const auto less_pivot = [&](std::size_t record) noexcept {
      if (brightness[record] != pivot_brightness) return brightness[record] < pivot_brightness;
      if (red_green[record] != pivot_red_green) return red_green[record] < pivot_red_green;
      return blue[record] < pivot_blue;
    };
    const auto pivot_less = [&](std::size_t record) noexcept {
      if (pivot_brightness != brightness[record]) return pivot_brightness < brightness[record];
      if (pivot_red_green != red_green[record]) return pivot_red_green < red_green[record];
      return pivot_blue < blue[record];
    };
    while (scan_left <= scan_right) {
      while (less_pivot(scan_left)) ++scan_left;
      while (pivot_less(scan_right)) --scan_right;
      if (scan_left <= scan_right) {
        std::swap(brightness[scan_left], brightness[scan_right]);
        std::swap(red_green[scan_left], red_green[scan_right]);
        std::swap(blue[scan_left], blue[scan_right]);
        ++scan_left;
        --scan_right;
      }
    }
    if (scan_right < median_index) left = scan_left;
    if (median_index < scan_left) right = scan_right;
  }

  const std::uint32_t packed = red_green[median_index];
  // Lossless (exact) half-to-float32 widening -- see the file header.
  const float median_red = noisemaker::half_to_float(static_cast<std::uint16_t>(packed >> 16U));
  const float median_green = noisemaker::half_to_float(static_cast<std::uint16_t>(packed & 0xffffU));
  const float median_blue = noisemaker::half_to_float(static_cast<std::uint16_t>(blue[median_index]));

  const double maximum_difference = js_max3(
      std::fabs(original_red - static_cast<double>(median_red)),
      std::fabs(original_green - static_cast<double>(median_green)),
      std::fabs(original_blue - static_cast<double>(median_blue)));
  const double threshold = s.threshold;
  const bool replace = threshold <= 0.0 || maximum_difference >= threshold / 100.0;

  out[0] = replace ? median_red : static_cast<float>(original_red);
  out[1] = replace ? median_green : static_cast<float>(original_green);
  out[2] = replace ? median_blue : static_cast<float>(original_blue);
  out[3] = original_alpha;
}

}  // namespace

BoundKernel bind_median(const glsl::Bindings& b) {
  auto state = std::make_shared<State>();
  state->input_tex = &b.texture("inputTex");
  // Falls back to 2 -- the typed emitter's old sole baked value -- when
  // RADIUS is absent from `bindings` entirely (every caller driving this
  // kernel through the graph executor's custom-adapter route always
  // supplies it; direct/legacy callers built against the old typed-emitter
  // ABI, which never carried RADIUS as a binding at all, still get the
  // exact behavior they always got).
  state->radius = b.get_or<std::int32_t>("RADIUS", 2);
  // `get_number` (not the strict `get<float>`) so this accepts threshold
  // materialized either as the ABI's declared float (the real
  // custom-adapter dispatch path, via resolve_uniform's float rounding) or
  // as a plain double (every existing direct caller built against the old
  // typed-emitter ABI, including tests/test_generated_kernels.cpp's
  // median_native::bindings helper) -- both already carry the exact same
  // numeric value either way.
  state->threshold = b.get_number("threshold");
  return BoundKernel(state, &pixel);
}

}  // namespace noisemaker::effects
