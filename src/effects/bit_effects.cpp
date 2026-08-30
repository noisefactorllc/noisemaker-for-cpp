#include "noisemaker/effects/bit_effects.hpp"

#include <cmath>
#include <cstdint>
#include <memory>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"

namespace noisemaker::effects {
namespace {
using glsl::Vec2;
using glsl::Vec3;
using glsl::Vec4;

[[nodiscard]] float f32(double v) noexcept { return noisemaker::f32(v); }
[[nodiscard]] float add(double a, double b) noexcept { return f32(a + b); }
[[nodiscard]] float sub(double a, double b) noexcept { return f32(a - b); }
[[nodiscard]] float mul(double a, double b) noexcept { return f32(a * b); }
[[nodiscard]] float div(double a, double b) noexcept { return f32(a / b); }
[[nodiscard]] float fract(double v) noexcept { return f32(v - std::floor(v)); }
[[nodiscard]] float mod(double a, double b) noexcept { return f32(a - b * std::floor(a / b)); }
[[nodiscard]] std::int32_t js_i32(double v) noexcept { return glsl::detail::js_to_int32(v); }
[[nodiscard]] std::uint32_t word(double v) noexcept { return noisemaker::float_bits_to_uint(f32(v)); }

struct State final : KernelState {
  State(std::int32_t mode_value, std::int32_t formula_value, std::int32_t color_value,
        std::int32_t interp_value, std::int32_t mask_formula_value,
        std::int32_t mask_color_value, double time_value,
        std::int32_t seed_value,
        Vec2 resolution_value, Vec2 tile_value, Vec2 full_value, double n_value,
        double scale_value, double rotation_value, double speed_value,
        double tiles_value, double complexity_value, double hue_range_value,
        double hue_rotation_value, double base_hue_range_value)
      : mode(mode_value), formula(formula_value), color_scheme(color_value),
        interp(interp_value), mask_formula(mask_formula_value),
        mask_color_scheme(mask_color_value), time(time_value), seed(seed_value),
        resolution(resolution_value), tile_offset(tile_value), full_resolution(full_value),
        n(n_value), scale(scale_value), rotation(rotation_value), speed(speed_value),
        tiles(tiles_value), complexity(complexity_value), hue_range(hue_range_value),
        hue_rotation(hue_rotation_value), base_hue_range(base_hue_range_value) {}
  std::int32_t mode, formula, color_scheme, interp, mask_formula, mask_color_scheme;
  double time;
  std::int32_t seed;
  Vec2 resolution, tile_offset, full_resolution;
  double n, scale, rotation, speed, tiles, complexity, hue_range, hue_rotation, base_hue_range;
};

[[nodiscard]] double cmap(double value, double in_min, double in_max,
                          double out_min, double out_max) noexcept {
  return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min);
}
[[nodiscard]] double cperiodic(double value) noexcept {
  return cmap(glsl::sin(value * f32(6.2831854820251465)), -1.0, 1.0, 0.0, 1.0);
}

[[nodiscard]] std::array<std::uint32_t, 3> random_words(float sx, float sy,
    double xf, double yf, double seed, std::int32_t offset, bool mode1) noexcept {
  const float lx = mul(sx, xf), ly = mul(sy, yf);
  const double fx = std::floor(lx), fy = std::floor(ly);
  const float frac_x = sub(lx, fx), seed_frac = fract(seed);
  const std::int32_t xi = js_i32(fx + offset + js_i32(std::floor(seed)) +
                                  std::floor(static_cast<double>(frac_x) + seed_frac));
  const std::int32_t yi = js_i32(fy);
  const std::uint32_t seed_bits = word(seed), frac_bits = word(seed_frac);
  const std::uint32_t jx = umul(frac_bits, 374761393U) ^ (mode1 ? 0x9e3779b9U : 2654435769U);
  const std::uint32_t jy = umul(frac_bits, 668265263U) ^ (mode1 ? 0x7f4a7c15U : 2135587861U);
  const std::uint32_t jz = umul(frac_bits, 2246822519U) ^ (mode1 ? 0x94d049b4U : 2496678324U);
  return noisemaker::pcg3d({static_cast<std::uint32_t>(xi) ^ jx,
                            static_cast<std::uint32_t>(yi) ^ jy, seed_bits ^ jz});
}
[[nodiscard]] float random_value(float sx, float sy, double xf, double yf,
                                  double seed, std::int32_t offset, bool mode1) noexcept {
  const auto words = random_words(sx, sy, xf, yf, seed, offset, mode1);
  return div(static_cast<float>(words[0]), f32(4294967296.0));
}

[[nodiscard]] double cconstant(const State& s, float sx, float sy, double xf,
                               double yf, double seed) noexcept {
  if (s.mode == 0) {
    const float rt = random_value(sx, sy, xf, yf, seed, 40, false);
    const double scaled = cperiodic(rt - s.time) * cmap(std::fabs(s.speed), 0.0, 100.0, 0.0, f32(0.3330000042915344));
    return cperiodic(random_value(sx, sy, xf, yf, seed, 0, false) - scaled);
  }
  const float rt = random_value(sx, sy, xf, yf, seed, 40, true);
  const float speed = div(mul(std::fabs(s.speed), f32(0.333)), 100.0);
  const float scaled = mul(mul(add(glsl::sin(mul(sub(rt, s.time), f32(6.28318530718))), 1.0), 0.5), speed);
  return mul(add(glsl::sin(mul(sub(random_value(sx, sy, xf, yf, seed, 0, true), scaled), f32(6.28318530718))), 1.0), 0.5);
}
[[nodiscard]] double cvalue(const State& s, float sx, float sy, double xf,
                            double yf, double seed) noexcept {
  const double a = cconstant(s, sx, sy, xf, yf, seed);
  if (s.interp == 0 || s.mode != 0) return a;
  const double dx = 1.0 / xf, dy = 1.0 / yf;
  const double b = cconstant(s, sx, add(sy, dy), xf, yf, seed);
  const double c = cconstant(s, add(sx, dx), sy, xf, yf, seed);
  const double d = cconstant(s, add(sx, dx), add(sy, dy), xf, yf, seed);
  const float ux = mul(sx, xf), uy = mul(sy, yf);
  const float ab = glsl::mix(a, c, fract(ux)), cd = glsl::mix(b, d, fract(ux));
  return glsl::mix(ab, cd, fract(uy));
}

[[nodiscard]] float cbit(const State& s, float sx, float sy, double freq,
                         double n) noexcept {
  const double blendy = n + cperiodic(cvalue(s, sx, sy, freq * f32(0.009999999776482582),
                                              freq * f32(0.009999999776482582), n) * f32(0.10000000149011612)) * 100.0;
  const std::int32_t x = js_i32(static_cast<double>(sx) * freq), y = js_i32(static_cast<double>(sy) * freq);
  const std::int32_t mx = glsl::detail::js_bitwise_and(x, 255);
  const std::int32_t my = glsl::detail::js_bitwise_and(y, 255);
  double value = 1.0;
  switch (s.formula) {
    case 0: value = mod(glsl::detail::js_bitwise_xor(mx, my), blendy); break;
    case 1: value = mod(glsl::detail::js_bitwise_or(mx, my), blendy); break;
    case 2: value = mod(static_cast<double>(sx) * freq * (static_cast<double>(sy) * freq), blendy); break;
    case 3: value = f32(glsl::detail::js_bitwise_xor(mx, my) < blendy); break;
    case 4: value = mod(static_cast<double>(sx) * freq * blendy, static_cast<double>(sy) * freq); break;
    case 5: value = mod((static_cast<double>(sx) * freq - .5) * .25, static_cast<double>(sy) * freq - .5); break;
    default: break;
  }
  return value > 1.0 ? 0.0F : 1.0F;
}
[[nodiscard]] Vec2 crot(const State& s, Vec2 st) noexcept {
  st[0] = f32(st[0] / s.scale); st[1] = f32(st[1] / s.scale);
  const double angle = cmap(s.rotation, 0, 360, 0, 1) * f32(6.2831854820251465);
  st[0] = sub(st[0], s.full_resolution[0] * .5); st[1] = sub(st[1], s.full_resolution[1] * .5);
  const float c = glsl::cos(angle), sn = glsl::sin(angle);
  const float x = f32(static_cast<double>(c) * st[0] + static_cast<double>(sn) * st[1]);
  const float y = f32(-static_cast<double>(sn) * st[0] + static_cast<double>(c) * st[1]);
  st[0] = add(x, s.full_resolution[0] * .5); st[1] = add(y, s.full_resolution[1] * .5);
  return st;
}
[[nodiscard]] Vec3 cfield(const State& s, Vec2 st) noexcept {
  st = crot(s, st); const double freq = cmap(s.scale, 1, 100, s.scale, 8); Vec3 c{};
  auto v = [&](double n) { return cbit(s, st[0], st[1], freq, n); };
  switch (s.color_scheme) {
    case 0: c[2] = v(s.n); break; case 1: c[1] = v(s.n); c[2] = v(s.n); break;
    case 2: c[1] = v(s.n); break; case 3: c[0] = v(s.n); c[2] = v(s.n); break;
    case 4: c[0] = v(s.n); break; case 5: c[0] = v(s.n); c[1] = v(s.n); c[2] = v(s.n); break;
    case 6: c[0] = v(s.n); c[1] = v(s.n); break; case 10: c[2] = v(s.n); c[1] = v(s.n + 1); break;
    case 11: c[2] = v(s.n); c[0] = v(s.n + 1); break; case 12: c[2] = v(s.n); c[0] = v(s.n + 1); c[1] = c[0]; break;
    case 13: c[1] = v(s.n); c[0] = v(s.n + 1); c[2] = c[0]; break; case 14: c[1] = v(s.n); c[0] = v(s.n + 1); break;
    case 15: c[0] = v(s.n); c[1] = v(s.n + 1); c[2] = c[1]; break; case 20: c[0] = v(s.n); c[1] = v(s.n + 1); c[2] = v(s.n + 2); break;
    default: break;
  } return c;
}

[[nodiscard]] float mask_value(const State& s, float sx, float sy, double freq,
                               std::int32_t formula, double seed) noexcept {
  if (formula == 10 || formula == 11) {
    const float xm = mod(std::floor(mul(sx, freq)), freq), ym = mod(std::floor(mul(sy, freq)), freq);
    if (xm == 0 || ym == 0 || xm == f32(freq - 1) || ym == f32(freq - 1)) return 0;
    if (xm >= mul(freq, .5)) return static_cast<float>(cconstant(s, add(std::floor(sx), sub(1, fract(sx))), sy, freq, freq, seed));
    return static_cast<float>(cconstant(s, sx, sy, freq, freq, seed));
  }
  if (formula == 20) {
    const double xf = std::floor(mul(freq, .75)); const float xm = mod(std::floor(mul(sx, xf)), xf), ym = mod(std::floor(mul(sy, freq)), freq);
    if (xm == 0 || ym == 0 || xm == f32(xf - 1) || ym == f32(freq - 1)) return 0;
    return static_cast<float>(cconstant(s, sx, sy, xf, freq, seed));
  }
  if (formula == 30) {
    const double xf = std::floor(mul(freq, .5)) + 1, yf = std::floor(freq); const float xm = mod(std::floor(mul(sx, xf)), xf), ym = mod(std::floor(mul(sy, yf)), yf);
    if (xm == 0 || ym == 0 || xm == f32(xf - 1) || ym == f32(yf - 1)) return 0;
    if (ym == 1) return xm == 1 ? 1 : 0;
    return static_cast<float>(cconstant(s, sx, sy, xf, yf, seed));
  }
  return 1;
}
void hsv(float h0, float sat, float val, Vec3& out) noexcept {
  const float h = fract(h0), c = mul(val, sat), x = mul(c, sub(1, std::fabs(static_cast<double>(mod(mul(h, 6), 2)) - 1))), m = sub(val, c);
  float r=0,g=0,b=0; if(h<f32(1./6)){r=c;g=x;} else if(h<f32(2./6)){r=x;g=c;} else if(h<f32(3./6)){g=c;b=x;} else if(h<f32(4./6)){g=x;b=c;} else if(h<f32(5./6)){r=x;b=c;} else if(h<1){r=c;b=x;}
  out[0]=add(r,m); out[1]=add(g,m); out[2]=add(b,m);
}
void mask_pixel(const State& s, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const float gx=add(ctx.frag_coord[0],s.tile_offset[0]), gy=add(ctx.frag_coord[1],s.tile_offset[1]); const float aspect=div(s.full_resolution[0],s.full_resolution[1]), half=mul(.5,aspect);
  const double freq=std::floor(f32(5+f32(7)*div(sub(s.complexity,1),99))); float x=add(div(gx,s.full_resolution[1]),add(s.seed,1000)), y=add(div(gy,s.full_resolution[1]),add(s.seed,1000));
  x=sub(x,half); y=sub(y,.5);
  x=mul(x,s.tiles); y=mul(y,s.tiles);
  x=add(x,half); y=add(y,.5);
  x=sub(x,half);
  if(s.mask_formula==11)y=mul(y,2);
  const float mask=mask_value(s,x,y,freq,s.mask_formula,-100)>0.5?1:0; if(s.mask_color_scheme==0){out=Vec4(mask,mask,mask,1);return;}
  const float base=add(.01,mul(mul(static_cast<float>(cconstant(s,x,y,1,1,-100)),s.base_hue_range),.01)); const float hue=mul(fract(add(add(base,mul(mul(mask_value(s,x,y,freq,s.mask_formula,0),s.hue_range),.01)),sub(1,div(s.hue_rotation,360)))),mask);
  const float sat=s.mask_color_scheme==3?mask:mul(mask_value(s,x,y,freq,s.mask_formula,25),mask), val=(s.mask_color_scheme==2||s.mask_color_scheme==3)?mask:mul(mask_value(s,x,y,freq,s.mask_formula,50),mask); Vec3 rgb{}; hsv(hue,sat,val,rgb); out=Vec4(rgb[0],rgb[1],rgb[2],1);
}
void pixel(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept { const auto& s=static_cast<const State&>(base); if(s.mode!=0){mask_pixel(s,ctx,out);return;} const float gx=add(ctx.frag_coord[0],s.tile_offset[0]), gy=add(ctx.frag_coord[1],s.tile_offset[1]); const Vec3 c=cfield(s,Vec2(gx,gy)); out=Vec4(c[0],c[1],c[2],1); }
}

BoundKernel bind_bit_effects(const glsl::Bindings& b) {
  const auto state=std::make_shared<State>(b.get<std::int32_t>("MODE"),b.get<std::int32_t>("FORMULA"),b.get<std::int32_t>("COLOR_SCHEME"),b.get<std::int32_t>("INTERP"),b.get<std::int32_t>("MASK_FORMULA"),b.get<std::int32_t>("MASK_COLOR_SCHEME"),b.get_number("time"),b.get<std::int32_t>("seed"),b.get<glsl::Vec2>("resolution"),b.get<glsl::Vec2>("tileOffset"),b.get<glsl::Vec2>("fullResolution"),b.get_number("n"),b.get_number("scale"),b.get_number("rotation"),b.get_number("speed"),b.get_number("tiles"),b.get_number("complexity"),b.get_number("hueRange"),b.get_number("hueRotation"),b.get_number("baseHueRange"));
  return BoundKernel(state,&pixel);
}
}  // namespace noisemaker::effects
