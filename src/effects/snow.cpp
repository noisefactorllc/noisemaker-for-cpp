#include "noisemaker/effects/snow.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <memory>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

// Hand-written CPU kernel for filter/snow:snow.
//
// Ported by hand from the authority's src/effects/adapters/snow.js,
// operation-for-operation, exactly like src/effects/remap.cpp mirrors
// remap.js and src/effects/bit_effects.cpp mirrors the bitEffects adapter.
// snow.js computes in plain JS-double locals but wraps EVERY arithmetic
// operator (`add`/`sub`/`mul`/`div`/`fract`) in `Math.fround`
// individually -- unlike remap.js, which rounds once at the final store
// -- so this port applies `noisemaker::f32()` at exactly the same points,
// not just at the four `out[]` writes. Two asymmetries in snow.js are
// intentional and are NOT normalized here:
//   * `cosine()` calls `Math.cos` directly; `sine()` first reduces its
//     argument to a `[0, 1)` "turns" fraction before calling `Math.sin`.
//     `cosine()`'s one call site (`snowNoise`) never needs the reduction
//     (its argument is already small), so the authority never added it.
//   * `snowHash`'s two cross terms round differently: the first
//     (`sx * add(sy, ...)`) is a bare, unrounded `double` multiply; the
//     second (`mul(sy, add(sz, ...))`) rounds to float32 before the add.
namespace noisemaker::effects {
namespace {

using glsl::Vec4;

[[nodiscard]] double f32(double value) noexcept {
  return static_cast<double>(noisemaker::f32(value));
}
[[nodiscard]] double add(double left, double right) noexcept { return f32(left + right); }
[[nodiscard]] double sub(double left, double right) noexcept { return f32(left - right); }
[[nodiscard]] double mul(double left, double right) noexcept { return f32(left * right); }
[[nodiscard]] double div(double left, double right) noexcept { return f32(left / right); }
[[nodiscard]] double fract(double value) noexcept { return f32(value - std::floor(value)); }
// `value <= 0 ? 0 : value >= 1 ? 1 : value` -- deliberately NOT rounded:
// every caller already passes an f32-valued double, and 0/1 are exact.
[[nodiscard]] double clamp01(double value) noexcept {
  if (value <= 0.0) return 0.0;
  if (value >= 1.0) return 1.0;
  return value;
}

constexpr double kTau = 6.283185307179586;      // rounded to float32 below
constexpr double kInvTau = 1.0 / 6.283185307179586;  // rounded to float32 below

// `sine()` first reduces its argument to a small "turns" fraction before
// calling `Math.sin` (snow.js's own range-reduction trick); `cosine()`
// does not -- see the file header. `phase` is deliberately left
// unrounded between the fract-like step and the final `sin()` call,
// exactly matching `const phase = turns - Math.floor(turns)` in JS.
[[nodiscard]] double sine(double value) noexcept {
  const double turns = f32(value * f32(kInvTau));
  const double phase = turns - std::floor(turns);
  return f32(std::sin(phase * f32(kTau)));
}
[[nodiscard]] double cosine(double value) noexcept { return f32(std::cos(value)); }

[[nodiscard]] double periodic_value(double time, double value) noexcept {
  return mul(add(sine(mul(sub(time, value), f32(kTau))), 1.0), 0.5);
}

// Mirrors snowHash(vec3) exactly, including which of its two cross terms
// round to float32 before the add and which stay a bare double product
// (see the file header).
[[nodiscard]] double snow_hash(double x, double y, double z) noexcept {
  // Every literal below is rounded to float32 individually BEFORE it
  // reaches `add`/`mul` (`mul(x, F32(0.1031))`, `add(sy, F32(33.33))`, ...
  // in snow.js) -- passing the raw double literal instead would multiply
  // or add against a different (unrounded) operand and can shift the
  // final float32 rounding by a bit.
  const double k0_1031 = f32(0.1031);
  const double k33_33 = f32(33.33);
  const double sx = fract(mul(x, k0_1031));
  const double sy = fract(mul(y, k0_1031));
  const double sz = fract(mul(z, k0_1031));
  const double inner = f32((sx * add(sy, k33_33)) + mul(sy, add(sz, k33_33)));
  const double dot_val = f32(inner + (sz * add(sx, k33_33)));
  const double shifted_xy = f32((sx + sy) + f32(2.0 * dot_val));
  return clamp01(fract(f32(shifted_xy * add(sz, dot_val))));
}

// Mirrors snowNoise(vec2, float, float, vec3) exactly.
[[nodiscard]] double snow_noise(double x, double y, double time, double speed,
                                const std::array<double, 3>& seed) noexcept {
  const double angle = mul(time, f32(kTau));
  const double cosine_value = cosine(angle);
  const double z_base = std::fabs(cosine_value) < f32(0.0000001) ? 0.0 : mul(cosine_value, speed);
  const double base_value =
      snow_hash(add(x, seed[0]), add(y, seed[1]), add(z_base, seed[2]));
  if (speed == 0.0 || time == 0.0) return base_value;

  const double time_seed_x = add(seed[0], 97.0);
  const double time_seed_y = add(seed[1], 57.0);
  const double time_seed_z = add(seed[2], 131.0);
  const double time_value =
      snow_hash(add(x, time_seed_x), add(y, time_seed_y), add(1.0, time_seed_z));
  const double scaled_time = mul(periodic_value(time, time_value), speed);
  return clamp01(periodic_value(scaled_time, base_value));
}

constexpr std::array<double, 3> kStaticSeed{37.0, 17.0, 53.0};
constexpr std::array<double, 3> kLimiterSeed{113.0, 71.0, 193.0};

struct State final : KernelState {
  const Surface* input_tex = nullptr;
  double alpha = 0.0;
  double time = 0.0;
  double pause = 0.0;
  double density = 0.0;
};

// Mirrors snowFactory's returned kernel exactly, including the early
// alpha==0 passthrough (computed BEFORE time/pause/density are even
// consulted in snow.js -- moot here since bind_snow reads every uniform
// up front, matching bit_effects.cpp's and remap.cpp's own State pattern,
// but the passthrough's early return is still observable: it never
// evaluates the noise at all).
void pixel(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const State&>(base);
  const double x = static_cast<double>(ctx.frag_coord[0]);
  const double y = static_cast<double>(ctx.frag_coord[1]);
  // `shaderX | 0` / `shaderY | 0` in snow.js's texelOffset: ToInt32
  // truncates toward zero. fragCoord is always a small non-negative
  // pixel-center float here, so a plain truncating cast agrees with
  // ToInt32 bit for bit.
  const Rgba texel = texel_fetch_bottom_left(*s.input_tex, static_cast<int>(x),
                                             static_cast<int>(y));

  const double alpha = clamp01(s.alpha);
  if (alpha == 0.0) {
    out = Vec4(texel[0], texel[1], texel[2], texel[3]);
    return;
  }

  const double time = s.pause > 0.5 ? 0.0 : s.time;
  const double speed = f32(100.0);
  const double static_value = snow_noise(x, y, time, speed, kStaticSeed);
  const double limiter_value = snow_noise(x, y, time, speed, kLimiterSeed);
  const double density = std::max(mul(s.density, f32(0.01)), f32(0.0001));
  const double exponent = div(sub(1.0, density), density);
  const double limiter_mask =
      mul(f32(std::pow(std::min(limiter_value, f32(0.99)), exponent)), alpha);
  const double inverse_mask = sub(1.0, limiter_mask);

  out[0] = noisemaker::f32(static_cast<double>(texel[0]) * inverse_mask +
                           static_value * limiter_mask);
  out[1] = noisemaker::f32(static_cast<double>(texel[1]) * inverse_mask +
                           static_value * limiter_mask);
  out[2] = noisemaker::f32(static_cast<double>(texel[2]) * inverse_mask +
                           static_value * limiter_mask);
  out[3] = texel[3];
}

}  // namespace

BoundKernel bind_snow(const glsl::Bindings& b) {
  auto state = std::make_shared<State>();
  state->input_tex = &b.texture("inputTex");
  state->alpha = b.get_number("alpha");
  state->time = b.get_number("time");
  state->pause = b.get_number("pause");
  state->density = b.get_number("density");
  return BoundKernel(state, &pixel);
}

}  // namespace noisemaker::effects
