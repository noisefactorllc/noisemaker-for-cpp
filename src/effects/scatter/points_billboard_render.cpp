#include "noisemaker/effects/scatter/points_billboard_render.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>

#include "noisemaker/effects/scatter/points_deposit_support.hpp"
#include "noisemaker/fdlibm.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"

namespace noisemaker::scatter::points_billboard_render {
namespace {

namespace pd = points_deposit;

// The 4 distinct quad corners in local offset space (billboard-deposit.js:
// 43-48).
constexpr std::array<std::array<double, 2>, 4> kQuadCornerOffsets{{
    {-1.0, -1.0},
    {1.0, -1.0},
    {-1.0, 1.0},
    {1.0, 1.0},
}};

// `clampNum(value, low, high)` (billboard-deposit.js:50-52): plain
// `Math.min(Math.max(value, low), high)`.
[[nodiscard]] double clamp_num(double value, double low, double high) noexcept {
  return pd::js_min(pd::js_max(value, low), high);
}

// `smoothstep(edge0, edge1, x)` (billboard-deposit.js:54-58).
[[nodiscard]] double smoothstep_js(double edge0, double edge1, double x) noexcept {
  const double t = clamp_num((x - edge0) / (edge1 - edge0), 0.0, 1.0);
  return t * t * (3.0 - 2.0 * t);
}

// `Math.sign(value)`, EXACTLY -- payload-preserving NaN (verified
// empirically against a live V8 build with a custom-payload NaN: `Math.
// sign` returns it unchanged, never a re-materialized canonical NaN), and
// JS's signed-zero identity rule (`Math.sign(-0) === -0`,
// `Math.sign(+0) === +0`, satisfied here by returning `value` itself for
// either).
[[nodiscard]] double js_sign(double value) noexcept {
  if (std::isnan(value)) return value;
  if (value > 0.0) return 1.0;
  if (value < 0.0) return -1.0;
  return value;
}

// `hashUint32(seedBits)` (billboard-deposit.js:73-77): a PCG-style integer
// hash. `Math.imul(a, b) >>> 0` on two already-uint32 operands is exactly
// `(uint32_t)(a * b)` (2's-complement wraparound multiplication is
// identical whether the bits are interpreted as signed or unsigned) --
// `noisemaker::umul` already implements exactly that.
[[nodiscard]] std::uint32_t hash_uint32(std::uint32_t seed_bits) noexcept {
  const std::uint32_t state = umul(seed_bits, 747796405U) + 2891336453U;
  const std::uint32_t shift = (state >> 28U) + 4U;
  const std::uint32_t word = umul((state >> shift) ^ state, 277803737U);
  return (word >> 22U) ^ word;
}

// `floatBitsToUint(value)` (billboard-deposit.js:65-68): reinterpret an
// IEEE-754 float32 bit pattern as uint32 -- exactly
// `noisemaker::float_bits_to_uint`.

// `signedDistanceForShape(shapeMode, px, py)` (billboard-deposit.js:87-136).
[[nodiscard]] double signed_distance_for_shape(std::int32_t shape_mode, double px, double py) noexcept {
  if (shape_mode == 1) return std::sqrt(px * px + py * py) - 0.45;  // circle
  if (shape_mode == 2) return std::fabs(std::sqrt(px * px + py * py) - 0.35) - 0.08;  // ring
  if (shape_mode == 3) return pd::js_max(std::fabs(px), std::fabs(py)) - 0.4;  // square
  if (shape_mode == 4) return std::fabs(px) + std::fabs(py) - 0.45;  // diamond

  if (shape_mode == 5) {
    // Equilateral triangle (Inigo Quilez SDF).
    const double r = 0.25;
    const double k = 1.732050808;  // sqrt(3)
    double tx = std::fabs(px) - r;
    double ty = py - 0.04 + r / k;
    if (tx + k * ty > 0.0) {
      const double next_tx = tx - k * ty;
      const double next_ty = -k * tx - ty;
      tx = next_tx / 2.0;
      ty = next_ty / 2.0;
    }
    tx -= clamp_num(tx, -2.0 * r, 0.0);
    return -std::sqrt(tx * tx + ty * ty) * js_sign(ty);
  }

  // shape_mode == 6: 5-point star (Inigo Quilez SDF, straight edges).
  const double r = 0.35;
  const double rf = 0.4;
  const double k1x = 0.809016994375;
  const double k1y = -0.587785252292;
  const double k2x = -k1x;
  const double k2y = k1y;
  double sx = std::fabs(px);
  double sy = py;
  const double dot1 = k1x * sx + k1y * sy;
  const double m1 = pd::js_max(dot1, 0.0);
  sx -= 2.0 * m1 * k1x;
  sy -= 2.0 * m1 * k1y;
  const double dot2 = k2x * sx + k2y * sy;
  const double m2 = pd::js_max(dot2, 0.0);
  sx -= 2.0 * m2 * k2x;
  sy -= 2.0 * m2 * k2y;
  sx = std::fabs(sx);
  sy -= r;
  const double bax = rf * -k1y - 0.0;
  const double bay = rf * k1x - 1.0;
  const double dot_s_ba = sx * bax + sy * bay;
  const double dot_ba_ba = bax * bax + bay * bay;
  const double h = clamp_num(dot_s_ba / dot_ba_ba, 0.0, r);
  const double rem_x = sx - bax * h;
  const double rem_y = sy - bay * h;
  return std::sqrt(rem_x * rem_x + rem_y * rem_y) * js_sign(sy * bax - sx * bay);
}

// `sampleSprite(surface, u, v)` (billboard-deposit.js:161-164): DOUBLE u/v
// throughout, dispatched on the surface's own filter -- mirrors
// `src/effects/remap.cpp`'s `sample_zone_texture` idiom exactly. NEVER the
// `sample_nearest_bottom_left(Surface, float, float)` overload, which
// would narrow u/v to float32 before sampling.
[[nodiscard]] Rgba sample_sprite(const Surface& surface, double u, double v) noexcept {
  if (surface.filter() == TextureFilter::linear) return sample_bilinear_bottom_left(surface, u, v);
  return sample_nearest_bottom_left(surface, u, v);
}

// `blurWeight(u, v, cu, cv, expansion)` (billboard-deposit.js:199-206).
[[nodiscard]] double blur_weight(double u, double v, double cu, double cv, double expansion) noexcept {
  const double px = (u - cu) / expansion;
  const double py = (v - cv) / expansion;
  const double p2 = px * px + py * py;
  const double gaussian = fdlibm::exp(-p2 / 0.0648) * (1.0 - smoothstep_js(0.45, 0.5, std::sqrt(p2)));
  const double normalization = 1.0 / (0.19724318 * expansion * expansion);
  return gaussian * normalization;
}

// `evaluateBlurSample(shapeMode, spriteTex, u, v, agentColor, opacity,
// out)` (billboard-deposit.js:210-219): shadeSprite, but transparent
// outside the sprite's own [0,1] UV range.
void evaluate_blur_sample(std::int32_t shape_mode, const Surface& sprite_tex, double u, double v,
                           const Rgba64& agent_color, double opacity, Rgba64& out) noexcept {
  if (u < 0.0 || u > 1.0 || v < 0.0 || v > 1.0) {
    out = {0.0, 0.0, 0.0, 0.0};
    return;
  }
  evaluate_billboard_fragment(shape_mode, sprite_tex, u, v, agent_color, opacity, out);
}

// `shadeParticle(shapeMode, spriteTex, spriteMeanTex, u, v, agentColor,
// opacity, blurRadius, out)` (billboard-deposit.js:224-272).
void shade_particle(std::int32_t shape_mode, const Surface& sprite_tex, const Surface& sprite_mean_tex, double u,
                     double v, const Rgba64& agent_color, double opacity, double blur_radius, Rgba64& out) noexcept {
  const double expansion = pd::js_max(1.0 + 2.0 * blur_radius, 2.2516403);
  Rgba64 blurred{};
  if (shape_mode == 0) {
    blurred = {0.0, 0.0, 0.0, 0.0};
    for (std::int64_t yy = 0; yy < 5; ++yy) {
      for (std::int64_t xx = 0; xx < 5; ++xx) {
        const Rgba source = pd::texel_fetch_agent(sprite_mean_tex, xx, yy);
        const double weight = blur_weight(u, v, static_cast<double>(xx) / 4.0, static_cast<double>(yy) / 4.0, expansion);
        blurred[0] += static_cast<double>(source[0]) * weight;
        blurred[1] += static_cast<double>(source[1]) * weight;
        blurred[2] += static_cast<double>(source[2]) * weight;
        blurred[3] += static_cast<double>(source[3]) * weight;
      }
    }
    blurred[0] *= agent_color[0] * opacity;
    blurred[1] *= agent_color[1] * opacity;
    blurred[2] *= agent_color[2] * opacity;
    blurred[3] *= agent_color[3] * opacity;
  } else {
    const Rgba mean_sample = pd::texel_fetch_agent(sprite_mean_tex, 0, 0);
    // `shapeMode === 5 ? 0.5 : 0.5` in the JS source -- both branches are
    // literally identical (a dead ternary); ported literally, not
    // simplified, per this codebase's "no creative reinterpretation" rule.
    const double cu = shape_mode == 5 ? 0.5 : 0.5;
    const double cv = shape_mode == 5 ? 0.54 : 0.5;
    const double weight = blur_weight(u, v, cu, cv, expansion);
    blurred[0] = static_cast<double>(mean_sample[0]) * agent_color[0] * opacity * weight;
    blurred[1] = static_cast<double>(mean_sample[1]) * agent_color[1] * opacity * weight;
    blurred[2] = static_cast<double>(mean_sample[2]) * agent_color[2] * opacity * weight;
    blurred[3] = static_cast<double>(mean_sample[3]) * agent_color[3] * opacity * weight;
  }
  if (blur_radius >= 0.5) {
    out = blurred;
    return;
  }
  Rgba64 sharp{};
  evaluate_blur_sample(shape_mode, sprite_tex, u, v, agent_color, opacity, sharp);
  const double t = smoothstep_js(0.0, 0.5, blur_radius);
  out[0] = sharp[0] * (1.0 - t) + blurred[0] * t;
  out[1] = sharp[1] * (1.0 - t) + blurred[1] * t;
  out[2] = sharp[2] * (1.0 - t) + blurred[2] * t;
  out[3] = sharp[3] * (1.0 - t) + blurred[3] * t;
}

std::size_t adapter(const glsl::Bindings& bindings, const ScatterPass& pass, Surface& destination) {
  const Surface& xyz_tex = bindings.texture("xyzTex");
  const Surface& rgba_tex = bindings.texture("rgbaTex");
  const Surface& order_tex = bindings.texture("orderTex");
  const Surface& sprite_tex = bindings.texture("spriteTex");
  const Surface& sprite_mean_tex = bindings.texture("spriteMeanTex");

  Uniforms uniforms;
  uniforms.density = bindings.get_number("density");
  uniforms.view_mode = bindings.get_number("viewMode");
  uniforms.rotate_x = bindings.get_number("rotateX");
  uniforms.rotate_y = bindings.get_number("rotateY");
  uniforms.rotate_z = bindings.get_number("rotateZ");
  uniforms.pos_x = bindings.get_number("posX");
  uniforms.pos_y = bindings.get_number("posY");
  uniforms.pos_z = pd::get_number_or(bindings, "posZ", 0.0);
  uniforms.view_scale = bindings.get_number("viewScale");
  // Same non-`??` fieldOfView read as points_render.cpp -- see that file's
  // comment. An absent binding must mirror JS `undefined` (-> NaN through
  // Math.max), not a `0.0` default.
  uniforms.field_of_view = pd::get_number_or(bindings, "fieldOfView", std::numeric_limits<double>::quiet_NaN());
  uniforms.shape_mode = bindings.get_number("shapeMode");
  uniforms.blend_mode = bindings.get_number("blendMode");
  uniforms.blur_layer = pd::get_number_or(bindings, "blurLayer", 0.0);
  uniforms.deposit_opacity = bindings.get_number("depositOpacity");
  uniforms.seed = bindings.get_number("seed");
  uniforms.size_variation = bindings.get_number("sizeVariation");
  uniforms.rotation_var = bindings.get_number("rotationVar");
  uniforms.point_size = bindings.get_number("pointSize");
  uniforms.size_distance = pd::get_number_or(bindings, "sizeDistance", 0.0);
  uniforms.brightness_distance = pd::get_number_or(bindings, "brightnessDistance", 0.0);
  uniforms.aperture = pd::get_number_or(bindings, "aperture", 0.0);
  uniforms.focal_distance = pd::get_number_or(bindings, "focalDistance", 80.0);

  return run_deposit(xyz_tex, rgba_tex, order_tex, sprite_tex, sprite_mean_tex, uniforms, pass, destination);
}

}  // namespace

double hash(double n, double seed) noexcept {
  const float narrowed = static_cast<float>(n + seed);  // Math.fround(n + seed)
  const std::uint32_t bits = float_bits_to_uint(narrowed);
  return static_cast<double>(hash_uint32(bits)) / 4294967295.0;
}

double billboard_shape_alpha(std::int32_t shape_mode, double u, double v) noexcept {
  const double px = u - 0.5;
  const double py = v - 0.5;
  if (shape_mode >= 1 && shape_mode <= 6) {
    return 1.0 - smoothstep_js(-0.02, 0.02, signed_distance_for_shape(shape_mode, px, py));
  }
  return fdlibm::exp(-(px * px + py * py) * 8.0);
}

void evaluate_billboard_fragment(std::int32_t shape_mode, const Surface& sprite_tex, double u, double v,
                                  const Rgba64& agent_color, double opacity, Rgba64& out) noexcept {
  if (shape_mode == 0) {
    const Rgba sample = sample_sprite(sprite_tex, u, v);
    out[0] = static_cast<double>(sample[0]) * agent_color[0] * opacity;
    out[1] = static_cast<double>(sample[1]) * agent_color[1] * opacity;
    out[2] = static_cast<double>(sample[2]) * agent_color[2] * opacity;
    out[3] = static_cast<double>(sample[3]) * agent_color[3] * opacity;
    return;
  }
  const double alpha = billboard_shape_alpha(shape_mode, u, v);
  out[0] = agent_color[0] * alpha * opacity;
  out[1] = agent_color[1] * alpha * opacity;
  out[2] = agent_color[2] * alpha * opacity;
  out[3] = alpha * agent_color[3] * opacity;
}

bool is_premultiplied_blend(const ScatterPass& pass) noexcept {
  if (!pass.blend_factors.has_value()) return false;
  auto to_upper = [](std::string value) {
    for (char& c : value) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return value;
  };
  return to_upper(pass.blend_factors->first) == "ONE" && to_upper(pass.blend_factors->second) == "ONE_MINUS_SRC_ALPHA";
}

std::size_t run_deposit(const Surface& xyz_tex, const Surface& rgba_tex, const Surface& order_tex,
                         const Surface& sprite_tex, const Surface& sprite_mean_tex, const Uniforms& uniforms,
                         const ScatterPass& pass, Surface& destination) {
  const auto width = static_cast<std::int64_t>(xyz_tex.width());
  const auto height = static_cast<std::int64_t>(xyz_tex.height());
  const std::int64_t count = width * height;
  const auto dest_width = static_cast<std::int64_t>(destination.width());
  const auto dest_height = static_cast<std::int64_t>(destination.height());
  const double dest_width_d = static_cast<double>(dest_width);
  const double dest_height_d = static_cast<double>(dest_height);
  const auto data = destination.data();
  const bool premultiplied = is_premultiplied_blend(pass);

  const double cull_threshold = uniforms.density / 100.0;
  const std::int32_t shape_mode = pd::to_int32_or_zero(uniforms.shape_mode);
  const std::int32_t view_mode = pd::to_int32_or_zero(uniforms.view_mode);
  const std::int32_t blend_mode = pd::to_int32_or_zero(uniforms.blend_mode);
  const std::int32_t blur_layer = pd::to_int32_or_zero(uniforms.blur_layer);
  const double opacity = uniforms.deposit_opacity / 100.0;
  const double seed = uniforms.seed;
  const double size_variation_fraction = uniforms.size_variation / 100.0;
  const double rotation_var_fraction = uniforms.rotation_var / 100.0;
  const double point_size = uniforms.point_size;
  const double size_distance = uniforms.size_distance;
  const double brightness_distance = uniforms.brightness_distance;
  const double aperture = uniforms.aperture;
  const double focal_distance = uniforms.focal_distance;

  const pd::ClipCenterUniforms clip_uniforms{
      uniforms.view_mode, uniforms.rotate_x, uniforms.rotate_y, uniforms.rotate_z,
      uniforms.pos_x,     uniforms.pos_y,    uniforms.pos_z,    uniforms.view_scale,
      uniforms.field_of_view,
  };

  std::size_t pixels = 0;

  // Whole-draw gate for the BLUR_LAYER==1 clone. Ported literally as
  // `aperture <= 0` (NOT `!(aperture > 0)`, which disagrees with JS for a
  // NaN `aperture`: JS's `<= 0` is `false` for NaN, but `!(NaN > 0)` is
  // `true`).
  if (blur_layer == 1 && (view_mode == 0 || aperture <= 0.0 || blend_mode != 0)) return 0;

  for (std::int64_t v = 0; v < count; ++v) {
    std::int64_t particle_id = v;
    if (blend_mode == 1 && view_mode != 0) {
      const std::int64_t order_sx = particle_id % width;
      const std::int64_t order_sy =
          static_cast<std::int64_t>(std::floor(static_cast<double>(particle_id) / static_cast<double>(width)));
      const Rgba order = pd::texel_fetch_agent(order_tex, order_sx, order_sy);
      particle_id = pd::to_int32_or_zero(static_cast<double>(order[1]));
    }

    const double particle_random = pd::js_fract(static_cast<double>(particle_id) * pd::kGoldenRatioConjugate);
    if (particle_random > cull_threshold) continue;

    const std::int64_t sx = particle_id % width;
    const std::int64_t sy =
        static_cast<std::int64_t>(std::floor(static_cast<double>(particle_id) / static_cast<double>(width)));
    const Rgba pos = pd::texel_fetch_agent(xyz_tex, sx, sy);
    if (static_cast<double>(pos[3]) < 0.5) continue;  // alive = pos.w

    const Rgba agent_color_f = pd::texel_fetch_agent(rgba_tex, sx, sy);
    const auto clip = pd::compute_clip_center(static_cast<double>(pos[0]), static_cast<double>(pos[1]),
                                               static_cast<double>(pos[2]), clip_uniforms, dest_width, dest_height);
    if (!clip.has_value()) continue;
    const double clip_center_x = clip->clip_x;
    const double clip_center_y = clip->clip_y;
    const double camera_depth = clip->camera_depth;
    const double camera_distance = clip->camera_distance;
    const double projected_scale = clip->projected_scale;

    const double size_noise = hash(static_cast<double>(particle_id), seed);
    const double size_multiplier = 1.0 - size_variation_fraction * (size_noise - 0.5);
    double size_fade = 1.0;
    double brightness_fade = 1.0;
    double blur_pixels = 0.0;
    if (view_mode != 0) {
      if (size_distance > 0.0) size_fade = 1.0 - smoothstep_js(0.0, size_distance, camera_distance);
      if (brightness_distance > 0.0) brightness_fade = 1.0 - smoothstep_js(0.0, brightness_distance, camera_distance);
      blur_pixels = pd::js_min(
          32.0, (aperture * std::fabs(camera_depth - focal_distance)) / pd::js_max(std::fabs(camera_depth), 0.1));
    }
    const double base_size = point_size * size_multiplier * projected_scale;
    const double blur_radius = blur_pixels / pd::js_max(base_size, 0.001);
    const double support_radius = blur_pixels > 0.0 ? pd::js_max(blur_radius, 0.62582015) : 0.0;
    const double support_pixels = blur_pixels > 0.0 ? pd::js_max(blur_pixels, base_size * 0.62582015) : 0.0;
    const double low_weight = blend_mode == 0
                                   ? smoothstep_js(4.0, 8.0, blur_pixels * size_fade) * smoothstep_js(0.5, 1.0, blur_radius)
                                   : 0.0;
    const double layer_weight = blur_layer == 1 ? low_weight : 1.0 - low_weight;
    const double procedural_padding = shape_mode == 5 ? 0.04 : 0.0;
    const double blur_padding = blur_pixels > 0.0 ? (shape_mode == 0 ? 0.5 : procedural_padding) : 0.0;
    const double final_size = (base_size * (1.0 + 2.0 * blur_padding) + 2.0 * support_pixels) * size_fade;
    if (!(final_size > 0.0) || !(brightness_fade > 0.0) || !(layer_weight > 0.0)) continue;  // draws nothing

    Rgba64 pixel_color{
        static_cast<double>(agent_color_f[0]) * brightness_fade * layer_weight,
        static_cast<double>(agent_color_f[1]) * brightness_fade * layer_weight,
        static_cast<double>(agent_color_f[2]) * brightness_fade * layer_weight,
        static_cast<double>(agent_color_f[3]) * brightness_fade * layer_weight,
    };

    const double rotation_noise = hash(static_cast<double>(particle_id) + 1234.5, seed);
    const double rotation = rotation_var_fraction * rotation_noise * kTauApprox;
    const double cos_r = fdlibm::cos(rotation);
    const double sin_r = fdlibm::sin(rotation);

    const double half_size = final_size * 0.5;
    const double size_clip_x = half_size * (2.0 / dest_width_d);
    const double size_clip_y = half_size * (2.0 / dest_height_d);
    const double uv_scale = 0.5 + blur_padding + support_radius;

    double min_pxf = std::numeric_limits<double>::infinity();
    double max_pxf = -std::numeric_limits<double>::infinity();
    double min_pyf = std::numeric_limits<double>::infinity();
    double max_pyf = -std::numeric_limits<double>::infinity();
    for (const auto& corner : kQuadCornerOffsets) {
      const double ox = corner[0];
      const double oy = corner[1];
      const double rotated_offset_x = ox * cos_r - oy * sin_r;
      const double rotated_offset_y = ox * sin_r + oy * cos_r;
      const double corner_clip_x = clip_center_x + rotated_offset_x * size_clip_x;
      const double corner_clip_y = clip_center_y + rotated_offset_y * size_clip_y;
      const double pxf = (corner_clip_x * 0.5 + 0.5) * dest_width_d;
      const double pyf = (corner_clip_y * 0.5 + 0.5) * dest_height_d;
      if (pxf < min_pxf) min_pxf = pxf;
      if (pxf > max_pxf) max_pxf = pxf;
      if (pyf < min_pyf) min_pyf = pyf;
      if (pyf > max_pyf) max_pyf = pyf;
    }

    const double col_start = pd::js_max(0.0, std::floor(min_pxf));
    const double col_end = pd::js_min(dest_width_d - 1.0, std::ceil(max_pxf));
    const double row_start = pd::js_max(0.0, std::floor(min_pyf));
    const double row_end = pd::js_min(dest_height_d - 1.0, std::ceil(max_pyf));

    for (double gl_row = row_start; gl_row <= row_end; gl_row += 1.0) {
      const double sample_clip_y = ((gl_row + 0.5) / dest_height_d) * 2.0 - 1.0;
      const double dy = sample_clip_y - clip_center_y;
      const double b = dy / size_clip_y;
      const double storage_row = dest_height_d - 1.0 - gl_row;

      for (double col = col_start; col <= col_end; col += 1.0) {
        const double sample_clip_x = ((col + 0.5) / dest_width_d) * 2.0 - 1.0;
        const double dx = sample_clip_x - clip_center_x;
        const double a = dx / size_clip_x;

        const double offset_x = a * cos_r + b * sin_r;
        const double offset_y = -a * sin_r + b * cos_r;
        if (offset_x < -1.0 || offset_x > 1.0 || offset_y < -1.0 || offset_y > 1.0) continue;

        const double u = offset_x * uv_scale + 0.5;
        const double sprite_v = offset_y * uv_scale + 0.5;
        Rgba64 src{};
        // Ported literally as `blurRadius <= 0` (NOT `!(blurRadius > 0)`,
        // which disagrees with JS for a NaN `blurRadius`).
        if (view_mode == 0 || blur_radius <= 0.0) {
          evaluate_billboard_fragment(shape_mode, sprite_tex, u, sprite_v, pixel_color, opacity, src);
        } else {
          shade_particle(shape_mode, sprite_tex, sprite_mean_tex, u, sprite_v, pixel_color, opacity, blur_radius, src);
        }

        const double offset_d = (storage_row * dest_width_d + col) * 4.0;
        const auto offset = static_cast<std::size_t>(offset_d);
        if (premultiplied) {
          const double inverse_src_alpha = 1.0 - src[3];
          data[offset] = src[0] + static_cast<double>(data[offset]) * inverse_src_alpha;
          data[offset + 1] = src[1] + static_cast<double>(data[offset + 1]) * inverse_src_alpha;
          data[offset + 2] = src[2] + static_cast<double>(data[offset + 2]) * inverse_src_alpha;
          data[offset + 3] = src[3] + static_cast<double>(data[offset + 3]) * inverse_src_alpha;
        } else {
          data[offset] += src[0];
          data[offset + 1] += src[1];
          data[offset + 2] += src[2];
          data[offset + 3] += src[3];
        }
        pixels += 1;
      }
    }
  }

  return pixels;
}

void register_adapter() {
  scatter::register_scatter_adapter("render/pointsBillboardRender:deposit", &adapter);
}

}  // namespace noisemaker::scatter::points_billboard_render
