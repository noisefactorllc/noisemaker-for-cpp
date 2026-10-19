#include "noisemaker/effects/crt.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

// Hand-written CPU kernel for filter/crt:crt.
//
// Ported by hand from the authority's src/effects/adapters/crt.js, operation
// for operation. Every helper below has the name and the rounding of its JS
// counterpart. Math.max and Math.min keep their JS semantics (NaN propagates,
// +0 is above -0) through js_max and js_min. Math.sin goes through fdlibm, the
// port of V8's own sine.
namespace noisemaker::effects {
namespace {

using glsl::Vec4;

[[nodiscard]] double F(double value) noexcept { return static_cast<double>(noisemaker::f32(value)); }
[[nodiscard]] double fma32(double a, double b, double c) noexcept { return noisemaker::fma32(a, b, c); }

[[nodiscard]] double js_max(double a, double b) noexcept {
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == 0.0 && b == 0.0) return std::signbit(a) && std::signbit(b) ? -0.0 : 0.0;
  return a > b ? a : b;
}
[[nodiscard]] double js_min(double a, double b) noexcept {
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == 0.0 && b == 0.0) return std::signbit(a) || std::signbit(b) ? -0.0 : 0.0;
  return a < b ? a : b;
}

[[nodiscard]] double add(double a, double b) noexcept { return F(a + b); }
[[nodiscard]] double sub(double a, double b) noexcept { return F(a - b); }
[[nodiscard]] double mul(double a, double b) noexcept { return F(a * b); }
// Metal lowers a / b to a times the float32 reciprocal of b.
[[nodiscard]] double div(double a, double b) noexcept { return F(a * F(1.0 / b)); }
[[nodiscard]] double fract(double value) noexcept { return F(value - std::floor(value)); }
[[nodiscard]] double clamp(double value, double low, double high) noexcept { return js_min(js_max(value, low), high); }
[[nodiscard]] double clamp01(double value) noexcept { return clamp(value, 0.0, 1.0); }
[[nodiscard]] double sqrt(double value) noexcept { return F(std::sqrt(value)); }
// mix(a, b, t) lowers to fma(t, b - a, a).
[[nodiscard]] double mix(double a, double b, double t) noexcept { return fma32(t, sub(b, a), a); }
// length(): one rounded square, then the second square fused into it.
[[nodiscard]] double length2(double x, double y) noexcept { return sqrt(fma32(y, y, mul(x, x))); }
[[nodiscard]] double dot3(double ax, double ay, double az, double bx, double by, double bz) noexcept {
  return fma32(az, bz, fma32(ay, by, mul(ax, bx)));
}

const double kPiDouble = 3.141592653589793;
const double kInvTau = F(1.0 / (2.0 * kPiDouble));
const double kInvThree = F(0.3333333333333333);
const double kHash = F(43758.5453123);
const double kHash3 = F(43758.5453);

// Apple GPU sine (crt.js quadrantSine): r is 4 * fract(x / tau) in float32;
// the fold to y in [0, 1] and the residual model of P are the authority's.
[[nodiscard]] double quadrant_sine(double r) noexcept {
  const double n = std::floor(r);
  const double f = r - n;
  const std::int32_t quadrant = glsl::detail::js_to_int32(n);
  const double y = (quadrant & 1) != 0 ? 1.0 - f : f;
  if (y == 0.0) return n >= 2.0 ? -0.0 : 0.0;
  const double z = 2.0 * y * y - 1.0;
  const double quotient = noisemaker::fdlibm::sin(y * kPiDouble / 2.0) / y;
  const double p = F(quotient - 1.1920928955078125e-07 * (0.783734 + 0.010102 * z + 0.052674 * (2.0 * z * z - 1.0)));
  const double value = F(y * p);
  return n >= 2.0 ? -value : value;
}
[[nodiscard]] double quadrant_of_turns(double turns) noexcept { return F(4.0 * (turns - std::floor(turns))); }
[[nodiscard]] double sine(double x) noexcept { return quadrant_sine(quadrant_of_turns(F(x * kInvTau))); }
[[nodiscard]] double sin_turns(double turns) noexcept { return quadrant_sine(quadrant_of_turns(turns)); }
[[nodiscard]] double cos_turns(double turns) noexcept { return quadrant_sine(quadrant_of_turns(add(turns, 0.25))); }
[[nodiscard]] double cos_half_turns(double half_turns) noexcept {
  return quadrant_sine(quadrant_of_turns(fma32(half_turns, 0.5, 0.25)));
}

[[nodiscard]] double periodic_value(double time, double value) noexcept {
  return fma32(sin_turns(sub(time, value)), 0.5, 0.5);
}
const double kC289 = F(1.0 / 289.0);
[[nodiscard]] double mod289(double x) noexcept { return sub(x, mul(std::floor(mul(x, kC289)), 289.0)); }
[[nodiscard]] double permute(double x) noexcept { return mod289(mul(fma32(x, 34.0, 1.0), x)); }
const double kTaylorA = F(1.79284291400159);
const double kTaylorB = F(0.85373472095314);
const double kCx = F(1.0 / 6.0);
const double kCy = F(1.0 / 3.0);
const double kN = F(0.14285714285714285);
const double kNsX = mul(kN, 2.0);
const double kNsY = sub(mul(kN, 0.5), 1.0);
const double kNsZ = kN;
const double kM0 = F(0.6);

[[nodiscard]] double simplex_noise(double vx, double vy, double vz) noexcept {
  const double dv = dot3(vx, vy, vz, kCy, kCy, kCy);
  const double i0x = std::floor(add(vx, dv));
  const double i0y = std::floor(add(vy, dv));
  const double i0z = std::floor(add(vz, dv));
  const double di = dot3(i0x, i0y, i0z, kCx, kCx, kCx);
  const double x0x = add(sub(vx, i0x), di);
  const double x0y = add(sub(vy, i0y), di);
  const double x0z = add(sub(vz, i0z), di);
  const double s1x = x0x < x0y ? 0.0 : 1.0;
  const double s1y = x0y < x0z ? 0.0 : 1.0;
  const double s1z = x0z < x0x ? 0.0 : 1.0;
  const double lx = 1.0 - s1z;
  const double ly = 1.0 - s1x;
  const double lz = 1.0 - s1y;
  const double i1x = js_min(s1x, lx), i1y = js_min(s1y, ly), i1z = js_min(s1z, lz);
  const double i2x = js_max(s1x, lx), i2y = js_max(s1y, ly), i2z = js_max(s1z, lz);
  std::array<double, 12> corners{};
  corners[0] = x0x; corners[1] = x0y; corners[2] = x0z;
  corners[3] = add(sub(x0x, i1x), kCx); corners[4] = add(sub(x0y, i1y), kCx); corners[5] = add(sub(x0z, i1z), kCx);
  corners[6] = add(sub(x0x, i2x), kCy); corners[7] = add(sub(x0y, i2y), kCy); corners[8] = add(sub(x0z, i2z), kCy);
  corners[9] = sub(x0x, 0.5); corners[10] = sub(x0y, 0.5); corners[11] = sub(x0z, 0.5);
  const double ix = mod289(i0x);
  const double iy = mod289(i0y);
  const double iz = mod289(i0z);
  const std::array<double, 4> offsets_x{0.0, i1x, i2x, 1.0};
  const std::array<double, 4> offsets_y{0.0, i1y, i2y, 1.0};
  const std::array<double, 4> offsets_z{0.0, i1z, i2z, 1.0};
  std::array<double, 4> p{};
  for (std::size_t k = 0; k < 4; ++k) {
    const double pz = permute(add(iz, offsets_z[k]));
    const double py = permute(add(add(pz, iy), offsets_y[k]));
    p[k] = permute(add(add(py, ix), offsets_x[k]));
  }
  std::array<double, 4> x{};
  std::array<double, 4> y{};
  std::array<double, 4> h{};
  for (std::size_t k = 0; k < 4; ++k) {
    const double j = sub(p[k], mul(49.0, std::floor(mul(mul(p[k], kNsZ), kNsZ))));
    const double xi = std::floor(mul(j, kNsZ));
    const double yi = std::floor(sub(j, mul(7.0, xi)));
    x[k] = fma32(xi, kNsX, kNsY);
    y[k] = fma32(yi, kNsX, kNsY);
    h[k] = sub(sub(1.0, std::fabs(x[k])), std::fabs(y[k]));
  }
  const std::array<double, 4> b0{x[0], x[1], y[0], y[1]};
  const std::array<double, 4> b1{x[2], x[3], y[2], y[3]};
  std::array<double, 4> s0{};
  std::array<double, 4> s1{};
  std::array<double, 4> sh{};
  for (std::size_t k = 0; k < 4; ++k) {
    s0[k] = add(mul(std::floor(b0[k]), 2.0), 1.0);
    s1[k] = add(mul(std::floor(b1[k]), 2.0), 1.0);
    sh[k] = h[k] > 0.0 ? 0.0 : -1.0;
  }
  std::array<double, 12> gradient{};
  gradient[0] = fma32(s0[0], sh[0], b0[0]); gradient[1] = fma32(s0[2], sh[0], b0[2]); gradient[2] = h[0];
  gradient[3] = fma32(s0[1], sh[1], b0[1]); gradient[4] = fma32(s0[3], sh[1], b0[3]); gradient[5] = h[1];
  gradient[6] = fma32(s1[0], sh[2], b1[0]); gradient[7] = fma32(s1[2], sh[2], b1[2]); gradient[8] = h[2];
  gradient[9] = fma32(s1[1], sh[3], b1[1]); gradient[10] = fma32(s1[3], sh[3], b1[3]); gradient[11] = h[3];
  double sum = 0.0;
  for (std::size_t k = 0; k < 4; ++k) {
    const std::size_t g = k * 3U;
    const double gx = gradient[g], gy = gradient[g + 1U], gz = gradient[g + 2U];
    const double norm = fma32(-kTaylorB, dot3(gx, gy, gz, gx, gy, gz), kTaylorA);
    const double cx = corners[g], cy = corners[g + 1U], cz = corners[g + 2U];
    const double m = js_max(sub(kM0, dot3(cx, cy, cz, cx, cy, cz)), 0.0);
    const double msq = mul(m, m);
    const double term = dot3(mul(gx, norm), mul(gy, norm), mul(gz, norm), cx, cy, cz);
    sum = k == 0 ? mul(mul(msq, msq), term) : fma32(mul(msq, msq), term, sum);
  }
  return mul(42.0, sum);
}

[[nodiscard]] double wrap_float(double value, double limit) noexcept {
  if (limit <= 0.0) return 0.0;
  double result = fma32(-std::floor(div(value, limit)), limit, value);
  if (result < 0.0) result = add(result, limit);
  return result;
}

[[nodiscard]] std::array<double, 2> freq_for_shape(double base_freq, double width, double height) noexcept {
  const double freq = js_max(base_freq, 1.0);
  const double width_safe = js_max(width, 1.0);
  const double height_safe = js_max(height, 1.0);
  if (std::fabs(sub(width_safe, height_safe)) < F(1e-5)) return {freq, freq};
  if (height_safe < width_safe) return {freq, js_max(std::floor(div(mul(freq, width_safe), height_safe)), 1.0)};
  return {js_max(std::floor(div(mul(freq, height_safe), width_safe)), 1.0), freq};
}

[[nodiscard]] double value_noise_hash(double cx, double cy, double cz, double seed) noexcept {
  const double dot_value = fma32(seed, F(0.001), dot3(cx, cy, cz, F(12.9898), F(78.233), F(37.719)));
  return fract(mul(sine(dot_value), kHash3));
}
[[nodiscard]] double fade(double value) noexcept { return mul(mul(value, value), fma32(-2.0, value, 3.0)); }
[[nodiscard]] double lerp(double a, double b, double t) noexcept { return fma32(sub(b, a), t, a); }

[[nodiscard]] double value_noise_3d(double x, double y, double z, double seed) noexcept {
  const double cx = std::floor(x), cy = std::floor(y), cz = std::floor(z);
  const double tx = fade(sub(x, cx)), ty = fade(sub(y, cy)), tz = fade(sub(z, cz));
  const auto h = [&](double dx, double dy, double dz) { return value_noise_hash(cx + dx, cy + dy, cz + dz, seed); };
  const double x00 = lerp(h(0, 0, 0), h(1, 0, 0), tx);
  const double x10 = lerp(h(0, 1, 0), h(1, 1, 0), tx);
  const double x01 = lerp(h(0, 0, 1), h(1, 0, 1), tx);
  const double x11 = lerp(h(0, 1, 1), h(1, 1, 1), tx);
  return lerp(lerp(x00, x10, ty), lerp(x01, x11, ty), tz);
}

[[nodiscard]] double wrap_unit(double value) noexcept {
  double wrapped = sub(value, std::floor(value));
  if (wrapped < 0.0) wrapped = add(wrapped, 1.0);
  return wrapped;
}

// rgbToHsv and hsvToRgb write Float32Array lanes; every stored value is
// already a float32 value.
void rgb_to_hsv(double r, double g, double b, std::array<double, 3>& out) noexcept {
  const double c_max = js_max(js_max(r, g), b);
  const double c_min = js_min(js_min(r, g), b);
  const double delta = sub(c_max, c_min);
  double hue = 0.0;
  if (delta > 0.0) {
    if (c_max == r) {
      double segment = div(sub(g, b), delta);
      if (segment < 0.0) segment = add(segment, 6.0);
      hue = segment;
    } else if (c_max == g) {
      hue = add(div(sub(b, r), delta), 2.0);
    } else {
      hue = add(div(sub(r, g), delta), 4.0);
    }
    hue = wrap_unit(div(hue, 6.0));
  }
  out[0] = F(hue);
  out[1] = F(c_max != 0.0 ? div(delta, c_max) : 0.0);
  out[2] = F(c_max);
}
void hsv_to_rgb(double h, double s, double v, std::array<double, 3>& out) noexcept {
  const double dh = mul(h, 6.0);
  const double one_minus_s = sub(1.0, s);
  out[0] = F(clamp01(mul(fma32(s, clamp01(sub(std::fabs(sub(dh, 3.0)), 1.0)), one_minus_s), v)));
  out[1] = F(clamp01(mul(fma32(s, clamp01(add(-std::fabs(sub(dh, 2.0)), 2.0)), one_minus_s), v)));
  out[2] = F(clamp01(mul(fma32(s, clamp01(add(-std::fabs(sub(dh, 4.0)), 2.0)), one_minus_s), v)));
}
void adjust_hue(double r, double g, double b, double amount, std::array<double, 3>& out) noexcept {
  std::array<double, 3> hsv{};
  rgb_to_hsv(r, g, b, hsv);
  hsv_to_rgb(wrap_unit(add(hsv[0], amount)), clamp01(hsv[1]), clamp01(hsv[2]), out);
}
void adjust_saturation(double r, double g, double b, double amount, std::array<double, 3>& out) noexcept {
  std::array<double, 3> hsv{};
  rgb_to_hsv(r, g, b, hsv);
  hsv_to_rgb(hsv[0], clamp01(mul(hsv[1], amount)), clamp01(hsv[2]), out);
}
[[nodiscard]] double apply_vignette(double value, double brightness, double mask, double alpha) noexcept {
  return mix(value, mix(value, brightness, mask), clamp01(alpha));
}

struct State final : KernelState {
  const Surface* input = nullptr;
  double tile_offset_x = 0.0;
  double tile_offset_y = 0.0;
  double render_scale = 0.0;
  double alpha = 0.0;
  double rs = 0.0;
  double width = 0.0;
  double height = 0.0;
  double time = 0.0;
  double speed = 0.0;
  double seed = 0.0;
  double freq_x = 0.0;
  double freq_y = 0.0;
  double width_safe = 0.0;
  double height_safe = 0.0;
  double z_base = 0.0;
  double base_seed_x = 0.0;
  double base_seed_y = 0.0;
  double base_seed_z = 0.0;
  double time_seed_x = 0.0;
  double time_seed_y = 0.0;
  double time_seed_z = 0.0;
  bool animated = false;
  double aspect = 0.0;
  double max_radius = 0.0;
  double scan_base0 = 0.0;
  double scan_base1 = 0.0;
  double displacement_pixels = 0.0;
  double hue_shift = 0.0;
  double vignette_alpha = 0.0;
};

constexpr double kDisplacement = 0.0625;
constexpr double kPixelsPerBar = 2.5;

[[nodiscard]] double animated_simplex_value(const State& s, double u, double v) noexcept {
  const double base_noise = simplex_noise(add(u, s.base_seed_x), add(v, s.base_seed_y), add(s.z_base, s.base_seed_z));
  double value = clamp01(fma32(base_noise, 0.5, 0.5));
  if (s.animated) {
    const double time_noise = simplex_noise(add(u, s.time_seed_x), add(v, s.time_seed_y), s.time_seed_z);
    const double time_value = clamp01(fma32(time_noise, 0.5, 0.5));
    value = clamp01(periodic_value(mul(periodic_value(s.time, time_value), s.speed), value));
  }
  return clamp01(value);
}

void lens_offsets(const State& s, double sample_x, double sample_y, std::array<double, 2>& out) noexcept {
  const double wrapped_x = wrap_float(sample_x, s.width_safe);
  const double wrapped_y = wrap_float(sample_y, s.height_safe);
  const double noise = animated_simplex_value(s, mul(div(wrapped_x, s.width_safe), s.freq_x),
                                              mul(div(wrapped_y, s.height_safe), s.freq_y));
  const double dx = std::fabs(sub(div(add(wrapped_x, 0.5), s.width_safe), 0.5));
  const double dy = std::fabs(sub(div(add(wrapped_y, 0.5), s.height_safe), 0.5));
  double mask = 0.0;
  if (s.max_radius > 0.0) {
    const double normalized = clamp01(div(length2(mul(dx, s.aspect), dy), s.max_radius));
    const double masked = sqrt(normalized);
    const double squared = mul(masked, masked);
    mask = mul(mul(squared, squared), masked);
  }
  const double distortion = mul(fma32(noise, 2.0, -1.0), mask);
  out[0] = F(mul(mul(cos_turns(distortion), kDisplacement), s.width_safe));
  out[1] = F(mul(mul(sin_turns(distortion), kDisplacement), s.height_safe));
}

[[nodiscard]] double scan_row(const State& s, double row) noexcept {
  return std::fmod(std::trunc(std::floor(div(row, kPixelsPerBar))), 2.0) == 0.0 ? s.scan_base0 : s.scan_base1;
}

[[nodiscard]] double sample_scanline(const State& s, double sample_x, double sample_y) noexcept {
  double wrapped_x = fma32(-std::floor(div(sample_x, s.width)), s.width, sample_x);
  double wrapped_y = fma32(-std::floor(div(sample_y, s.height)), s.height, sample_y);
  if (wrapped_x < 0.0) wrapped_x = add(wrapped_x, s.width);
  if (wrapped_y < 0.0) wrapped_y = add(wrapped_y, s.height);
  wrapped_x = clamp(wrapped_x, 0.0, sub(s.width, 1.0));
  wrapped_y = clamp(wrapped_y, 0.0, sub(s.height, 1.0));
  const double y0 = std::floor(wrapped_y);
  const double y1 = js_min(add(y0, 1.0), sub(s.height, 1.0));
  const double x_fract = clamp01(sub(wrapped_x, std::floor(wrapped_x)));
  const double y_fract = clamp01(sub(wrapped_y, y0));
  const double top = scan_row(s, y0);
  const double bottom = scan_row(s, y1);
  return mix(mix(top, top, x_fract), mix(bottom, bottom, x_fract), y_fract);
}

// The four seed hashes reduce fma(seed, 73/tau, (17 + c)/tau).
[[nodiscard]] double sin_turns_from_seed(double seed, double offset) noexcept {
  return quadrant_sine(quadrant_of_turns(fma32(seed, F(73.0 * kInvTau), F(F(17.0 + F(offset)) * kInvTau))));
}
[[nodiscard]] double seed_hash(double seed, double offset) noexcept {
  return fract(mul(sin_turns_from_seed(seed, offset), kHash));
}

// blend_cosine: the b*w product fuses into the final add.
[[nodiscard]] double blend_cosine(double a, double b, double value) noexcept {
  const double c = cos_half_turns(clamp01(value));
  const double weight = mul(sub(1.0, c), 0.5);
  return fma32(b, weight, mul(a, fma32(0.5, c, 0.5)));
}
[[nodiscard]] double blend_scan(double value, double scan) noexcept {
  return mix(value, mul(add(value, scan), scan), 0.5);
}

[[nodiscard]] Rgba fetch(const State& s, double x, double y) noexcept {
  // The JS adapter stores the coordinate in an Int32Array (ToInt32).
  return texel_fetch_bottom_left(*s.input, glsl::detail::js_to_int32(x), glsl::detail::js_to_int32(y));
}

void pixel(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const State&>(base);
  const double gx = static_cast<double>(glsl::detail::js_to_int32(static_cast<double>(ctx.frag_coord[0])));
  const double gy = static_cast<double>(glsl::detail::js_to_int32(static_cast<double>(ctx.frag_coord[1])));
  const Rgba base_sample = fetch(s, gx, gy);
  const double base_r = base_sample[0], base_g = base_sample[1], base_b = base_sample[2];
  if (s.alpha == 0.0) {
    out = Vec4(base_sample[0], base_sample[1], base_sample[2], base_sample[3]);
    return;
  }
  const double x = div(add(gx, s.tile_offset_x), s.rs);
  const double y = div(add(gy, s.tile_offset_y), s.rs);
  std::array<double, 2> offsets{};
  lens_offsets(s, x, y, offsets);
  const double scan_value = sample_scanline(s, add(x, offsets[0]), add(y, offsets[1]));
  const double green_r = clamp01(blend_scan(base_r, scan_value));
  const double green_g = clamp01(blend_scan(base_g, scan_value));
  const double green_b = clamp01(blend_scan(base_b, scan_value));

  const double dx = div(sub(x, mul(s.width, 0.5)), s.width);
  const double dy = div(sub(y, mul(s.height, 0.5)), s.height);
  const double singularity = length2(dx, dy);
  const double aber_mask = mul(mul(singularity, singularity), singularity);
  const double gradient_x = clamp01(div(x, sub(s.width, 1.0)));

  const double red_x = mix(js_min(add(x, s.displacement_pixels), sub(s.width, 1.0)), x, gradient_x);
  const double red_sample_x = blend_cosine(x, red_x, aber_mask);
  const Rgba red_fetch = fetch(s, std::trunc(sub(mul(red_sample_x, s.render_scale), s.tile_offset_x)), gy);
  lens_offsets(s, red_sample_x, y, offsets);
  const double red_scan = sample_scanline(s, add(red_sample_x, offsets[0]), add(y, offsets[1]));

  const double blue_x = mix(x, js_max(sub(x, s.displacement_pixels), 0.0), gradient_x);
  const double blue_sample_x = blend_cosine(x, blue_x, aber_mask);
  const Rgba blue_fetch = fetch(s, std::trunc(sub(mul(blue_sample_x, s.render_scale), s.tile_offset_x)), gy);
  lens_offsets(s, blue_sample_x, y, offsets);
  const double blue_scan = sample_scanline(s, add(blue_sample_x, offsets[0]), add(y, offsets[1]));

  std::array<double, 3> red{};
  std::array<double, 3> green{};
  std::array<double, 3> blue{};
  std::array<double, 3> color{};
  adjust_hue(blend_scan(red_fetch[0], red_scan), blend_scan(red_fetch[1], red_scan),
             blend_scan(red_fetch[2], red_scan), s.hue_shift, red);
  adjust_hue(green_r, green_g, green_b, s.hue_shift, green);
  adjust_hue(blend_scan(blue_fetch[0], blue_scan), blend_scan(blue_fetch[1], blue_scan),
             blend_scan(blue_fetch[2], blue_scan), s.hue_shift, blue);
  adjust_hue(red[0], green[1], blue[2], -s.hue_shift, color);
  adjust_saturation(color[0], color[1], color[2], 1.125, color);
  for (auto& channel : color) channel = F(apply_vignette(channel, 0.0, singularity, s.vignette_alpha));
  const double local_mean = mul(add(add(color[0], color[1]), color[2]), kInvThree);
  const std::array<double, 3> base_rgb{base_r, base_g, base_b};
  std::array<float, 3> result{};
  for (std::size_t channel = 0; channel < 3; ++channel) {
    const double normalized = clamp01(fma32(sub(color[channel], local_mean), 1.25, local_mean));
    const double quantized = div(std::floor(fma32(clamp01(normalized), 255.0, 0.5)), 255.0);
    result[channel] = noisemaker::f32(mix(base_rgb[channel], quantized, s.alpha));
  }
  out = Vec4(result[0], result[1], result[2], base_sample[3]);
}

}  // namespace

BoundKernel bind_crt(const glsl::Bindings& b) {
  auto state = std::make_shared<State>();
  State& s = *state;
  s.input = &b.texture("inputTex");
  const glsl::Vec2 resolution = b.get<glsl::Vec2>("resolution");
  const glsl::Vec2 tile_offset = b.get<glsl::Vec2>("tileOffset");
  s.tile_offset_x = tile_offset[0];
  s.tile_offset_y = tile_offset[1];
  s.render_scale = b.get_number("renderScale");
  s.alpha = clamp01(b.get_number("alpha"));
  s.rs = js_max(s.render_scale, 1.0);
  const glsl::Vec2 full_resolution_binding = b.get<glsl::Vec2>("fullResolution");
  const glsl::Vec2 full_resolution = full_resolution_binding[0] > 0.0F ? full_resolution_binding : resolution;
  s.width = js_max(div(full_resolution[0], s.rs), 1.0);
  s.height = js_max(div(full_resolution[1], s.rs), 1.0);
  s.time = b.get_number("time");
  s.speed = b.get_number("speed");
  s.seed = static_cast<double>(b.get<std::int32_t>("seed"));
  const std::array<double, 2> freq = freq_for_shape(2.0, s.width, s.height);
  s.freq_x = js_max(freq[1], 1.0);
  s.freq_y = js_max(freq[0], 1.0);
  s.width_safe = js_max(s.width, 1.0);
  s.height_safe = js_max(s.height, 1.0);

  // animated_simplex_value's per-render terms.
  s.z_base = mul(cos_turns(s.time), s.speed);
  const double seed_term = mul(s.seed, 73.0);
  s.base_seed_x = add(17.0, seed_term);
  s.base_seed_y = fma32(seed_term, F(1.1), 29.0);
  s.base_seed_z = fma32(seed_term, F(0.7), 47.0);
  s.time_seed_x = add(s.base_seed_x, 54.0);
  s.time_seed_y = add(s.base_seed_y, 82.0);
  s.time_seed_z = add(s.base_seed_z, 124.0);
  s.animated = s.speed != 0.0 && s.time != 0.0;
  s.aspect = div(s.width_safe, s.height_safe);
  s.max_radius = length2(mul(s.aspect, 0.5), 0.5);

  // get_scanline_base_values.
  const double time_scaled = mul(mul(s.time, s.speed), F(0.1));
  const double noise_seed = fma32(s.seed, 31.0, F(19.37));
  s.scan_base0 = value_noise_3d(0.0, 0.0, time_scaled, noise_seed);
  s.scan_base1 = value_noise_3d(1.0, 0.0, time_scaled, noise_seed);

  const double displacement_base = fma32(seed_hash(s.seed, 0.37), F(0.00625), F(0.0125));
  const double simplex_value = seed_hash(s.seed, 0.73);
  s.displacement_pixels = mul(mul(displacement_base, s.width), simplex_value);
  s.hue_shift = fma32(seed_hash(s.seed, 1.91), 0.25, -0.125);
  s.vignette_alpha = mul(seed_hash(s.seed, 3.17), F(0.175));
  return BoundKernel(state, &pixel);
}

}  // namespace noisemaker::effects
