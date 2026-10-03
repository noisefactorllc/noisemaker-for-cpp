// CPU61aa OSD behavior retained only for its immutable historical captures.
#include "osd_kernel.hpp"
#include <cmath>
#include <cstdint>
#include <memory>
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
namespace noisemaker::historical_generated {
// Typed IR program: filter/osd:osd
// Source SHA-256: c45adaf30ecef6fb7f83a4f3995e671df0caaa47bfeceba8bb9bfe2c07427443
namespace typed_93 {
struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double renderScale_value, double alpha_value, double seed_value, double speed_value, double time_value, std::int32_t corner_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), renderScale(renderScale_value), alpha(alpha_value), seed(seed_value), speed(speed_value), time(time_value), corner(corner_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double renderScale;
  double alpha;
  double seed;
  double speed;
  double time;
  std::int32_t corner;
};

[[nodiscard]] glsl::Vec4 sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {
  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);
  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);
}
[[nodiscard]] glsl::Vec4 fetch_texel(const Surface& surface, const glsl::IVec2& coord) noexcept {
  const Rgba sample = texel_fetch_bottom_left(surface, coord[0], coord[1]);
  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);
}
[[nodiscard]] glsl::IVec2 texture_size(const Surface& surface) noexcept {
  return glsl::IVec2(static_cast<std::int32_t>(surface.width()), static_cast<std::int32_t>(surface.height()));
}

[[nodiscard]] std::uint32_t hash2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t a, [[maybe_unused]] std::uint32_t b) noexcept;
[[nodiscard]] std::uint32_t hash3([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t a, [[maybe_unused]] std::uint32_t b, [[maybe_unused]] std::uint32_t c) noexcept;
[[nodiscard]] std::uint32_t pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t v_in) noexcept;
[[nodiscard]] double sample_glyph([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t digit, [[maybe_unused]] double localX, [[maybe_unused]] double localY, [[maybe_unused]] std::int32_t iScale) noexcept;

[[nodiscard]] std::uint32_t hash2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t a, [[maybe_unused]] std::uint32_t b) noexcept {
  return pcg(state, context, (a ^ ((b * std::uint32_t(2654435769)) + std::uint32_t(1663821211))));
}

[[nodiscard]] std::uint32_t hash3([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t a, [[maybe_unused]] std::uint32_t b, [[maybe_unused]] std::uint32_t c) noexcept {
  return pcg(state, context, (hash2(state, context, a, b) ^ ((c * std::uint32_t(2496678331)) + std::uint32_t(1542469173))));
}

[[nodiscard]] std::uint32_t pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t v_in) noexcept {
  [[maybe_unused]] double state_glsl_74 = static_cast<double>(std::uint32_t(v_in) * std::uint32_t(747796405)) + static_cast<double>(std::uint32_t(2891336453));
  [[maybe_unused]] double pcg_shift = glsl::detail::js_shift_right(state_glsl_74, std::uint32_t(28));
  [[maybe_unused]] double pcg_word_shift = glsl::detail::js_shift_right(state_glsl_74, static_cast<double>(pcg_shift) + static_cast<double>(std::uint32_t(4)));
  [[maybe_unused]] std::int32_t pcg_xor = glsl::detail::js_bitwise_xor(pcg_word_shift, state_glsl_74);
  [[maybe_unused]] double word = static_cast<double>(pcg_xor) * static_cast<double>(std::uint32_t(277803737));
  return static_cast<std::uint32_t>(glsl::detail::js_bitwise_xor(glsl::detail::js_shift_right(word, std::uint32_t(22)), word));
}

[[nodiscard]] double sample_glyph([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t digit, [[maybe_unused]] double localX, [[maybe_unused]] double localY, [[maybe_unused]] std::int32_t iScale) noexcept {
  const std::array<std::int32_t, 80> GLYPHS = std::array<std::int32_t, 80>{{std::int32_t(60), std::int32_t(66), std::int32_t(66), std::int32_t(66), std::int32_t(66), std::int32_t(66), std::int32_t(60), std::int32_t(0), std::int32_t(24), std::int32_t(8), std::int32_t(8), std::int32_t(8), std::int32_t(28), std::int32_t(28), std::int32_t(28), std::int32_t(0), std::int32_t(28), std::int32_t(4), std::int32_t(4), std::int32_t(28), std::int32_t(16), std::int32_t(16), std::int32_t(28), std::int32_t(0), std::int32_t(28), std::int32_t(4), std::int32_t(4), std::int32_t(28), std::int32_t(6), std::int32_t(6), std::int32_t(30), std::int32_t(0), std::int32_t(96), std::int32_t(96), std::int32_t(96), std::int32_t(96), std::int32_t(102), std::int32_t(126), std::int32_t(6), std::int32_t(0), std::int32_t(60), std::int32_t(32), std::int32_t(32), std::int32_t(60), std::int32_t(4), std::int32_t(4), std::int32_t(60), std::int32_t(0), std::int32_t(120), std::int32_t(72), std::int32_t(64), std::int32_t(64), std::int32_t(126), std::int32_t(66), std::int32_t(126), std::int32_t(0), std::int32_t(60), std::int32_t(36), std::int32_t(4), std::int32_t(12), std::int32_t(8), std::int32_t(8), std::int32_t(8), std::int32_t(0), std::int32_t(60), std::int32_t(36), std::int32_t(36), std::int32_t(126), std::int32_t(102), std::int32_t(102), std::int32_t(126), std::int32_t(0), std::int32_t(62), std::int32_t(34), std::int32_t(34), std::int32_t(62), std::int32_t(6), std::int32_t(6), std::int32_t(6), std::int32_t(0)}};
  const std::int32_t GLYPH_W = 7;
  const std::int32_t GLYPH_H = 8;
  [[maybe_unused]] double gx = (static_cast<double>(localX) / static_cast<double>(iScale));
  [[maybe_unused]] double gy = (static_cast<double>(localY) / static_cast<double>(iScale));
  if ((((gx < std::int32_t(0)) || (gx >= GLYPH_W)) || (gy < std::int32_t(0))) || (gy >= GLYPH_H)) {
    return static_cast<float>(0.0);
  }
  [[maybe_unused]] std::int32_t row = glsl::detail::js_array_int32_read_for_bitwise(GLYPHS.data(), GLYPHS.size(), static_cast<double>(((digit * std::int32_t(8)) + gy)));
  return float(glsl::detail::js_bitwise_and(glsl::detail::js_shift_right(row, (std::int32_t(6) - gx)), std::int32_t(1)));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  const std::int32_t GLYPH_W = 7;
  const std::int32_t GLYPH_H = 8;
  const std::int32_t BASE_SCALE = 3;
  const std::int32_t BASE_PADDING = 25;
  [[maybe_unused]] std::int32_t iScale = glsl::component_max(glsl::detail::glsl_int_cast((static_cast<double>(float(BASE_SCALE)) * static_cast<double>(state.renderScale))), std::int32_t(1));
  [[maybe_unused]] std::int32_t CELL_W = (GLYPH_W * iScale);
  [[maybe_unused]] std::int32_t CELL_H = (GLYPH_H * iScale);
  [[maybe_unused]] std::int32_t GAP = iScale;
  [[maybe_unused]] std::int32_t PADDING = glsl::detail::glsl_int_cast((static_cast<double>(float(BASE_PADDING)) * static_cast<double>(state.renderScale)));
  [[maybe_unused]] glsl::IVec2 coord = glsl::IVec2(glsl::swizzle<0, 1>(context.frag_coord));
  [[maybe_unused]] glsl::IVec2 texDims = texture_size(*state.inputTex);
  [[maybe_unused]] glsl::Vec2 fullRes = ((glsl::swizzle<0>(state.fullResolution) > static_cast<float>(0.0)) ? glsl::Vec2(state.fullResolution) : glsl::Vec2(glsl::Vec2(texDims)));
  [[maybe_unused]] std::int32_t width = glsl::component_max(glsl::detail::glsl_int_cast(glsl::swizzle<0>(fullRes)), std::int32_t(1));
  [[maybe_unused]] std::int32_t height = glsl::component_max(glsl::detail::glsl_int_cast(glsl::swizzle<1>(fullRes)), std::int32_t(1));
  [[maybe_unused]] glsl::IVec2 globalCoord = (coord + glsl::IVec2(state.tileOffset));
  [[maybe_unused]] glsl::Vec4 texel = fetch_texel(*state.inputTex, coord);
  [[maybe_unused]] double blend_alpha = glsl::clamp(state.alpha, static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] std::int32_t scanlineStep = glsl::component_max((iScale / BASE_SCALE), std::int32_t(1));
  [[maybe_unused]] double scanline = (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.03)) * static_cast<double>(blend_alpha))) * static_cast<double>(float(glsl::detail::js_bitwise_and((glsl::swizzle<1>(globalCoord) / scanlineStep), std::int32_t(1)))))));
  [[maybe_unused]] glsl::Vec3 base_rgb = (glsl::swizzle<0, 1, 2>(texel) * scanline);
  if (blend_alpha <= static_cast<float>(0.0)) {
    output = glsl::Vec4(glsl::Vec4(base_rgb, glsl::swizzle<3>(texel)));
    return;
  }
  [[maybe_unused]] std::uint32_t base_seed = glsl::detail::float_to_uint32(glsl::component_max(state.seed, static_cast<float>(1.0)));
  [[maybe_unused]] std::int32_t glyph_count = (std::int32_t(3) + glsl::detail::glsl_int_cast((glsl::detail::js_to_int32(static_cast<double>(hash2(state, context, base_seed, std::uint32_t(42)))) % glsl::detail::js_to_int32(static_cast<double>(std::uint32_t(4))))));
  [[maybe_unused]] std::int32_t overlay_w = ((glyph_count * CELL_W) + ((glyph_count - std::int32_t(1)) * GAP));
  [[maybe_unused]] std::int32_t overlay_h = CELL_H;
  [[maybe_unused]] std::int32_t origin_x = {};
  [[maybe_unused]] std::int32_t origin_y = {};
  if (state.corner == std::int32_t(0)) {
    origin_x = PADDING;
    origin_y = ((height - overlay_h) - PADDING);
  } else {
    if (state.corner == std::int32_t(1)) {
      origin_x = ((width - overlay_w) - PADDING);
      origin_y = ((height - overlay_h) - PADDING);
    } else {
      if (state.corner == std::int32_t(2)) {
        origin_x = PADDING;
        origin_y = PADDING;
      } else {
        origin_x = ((width - overlay_w) - PADDING);
        origin_y = PADDING;
      }
    }
  }
  if (origin_x < std::int32_t(0)) {
    origin_x = std::int32_t(0);
  }
  if (origin_y < std::int32_t(0)) {
    origin_y = std::int32_t(0);
  }
  [[maybe_unused]] std::int32_t panel_pad = (GAP * std::int32_t(2));
  [[maybe_unused]] std::int32_t panel_x0 = (origin_x - panel_pad);
  [[maybe_unused]] std::int32_t panel_y0 = (origin_y - panel_pad);
  [[maybe_unused]] std::int32_t panel_x1 = ((origin_x + overlay_w) + panel_pad);
  [[maybe_unused]] std::int32_t panel_y1 = ((origin_y + overlay_h) + panel_pad);
  if ((((glsl::swizzle<0>(globalCoord) < panel_x0) || (glsl::swizzle<0>(globalCoord) >= panel_x1)) || (glsl::swizzle<1>(globalCoord) < panel_y0)) || (glsl::swizzle<1>(globalCoord) >= panel_y1)) {
    output = glsl::Vec4(glsl::Vec4(base_rgb, glsl::swizzle<3>(texel)));
    return;
  }
  [[maybe_unused]] std::int32_t lx = (glsl::swizzle<0>(globalCoord) - origin_x);
  [[maybe_unused]] std::int32_t ly = (glsl::swizzle<1>(globalCoord) - origin_y);
  [[maybe_unused]] double mask = static_cast<float>(0.0);
  if ((((lx >= std::int32_t(0)) && (lx < overlay_w)) && (ly >= std::int32_t(0))) && (ly < overlay_h)) {
    [[maybe_unused]] std::int32_t cell_stride = (CELL_W + GAP);
    [[maybe_unused]] double glyph_idx = (static_cast<double>(lx) / static_cast<double>(cell_stride));
    [[maybe_unused]] double within_glyph_x = (lx - (glyph_idx * cell_stride));
    if ((within_glyph_x < CELL_W) && (glyph_idx < glyph_count)) {
      [[maybe_unused]] std::int32_t local_y = ((CELL_H - std::int32_t(1)) - ly);
      [[maybe_unused]] std::int32_t time_cell = glsl::detail::glsl_int_cast(glsl::floor((static_cast<double>(state.time) * static_cast<double>(glsl::component_max(state.speed, static_cast<float>(0.001))))));
      [[maybe_unused]] std::uint32_t digit_hash = hash3(state, context, base_seed, glsl::detail::glsl_uint_cast(glyph_idx), glsl::detail::glsl_uint_cast(time_cell));
      [[maybe_unused]] std::int32_t digit = glsl::detail::glsl_int_cast((glsl::detail::js_to_int32(static_cast<double>(digit_hash)) % glsl::detail::js_to_int32(static_cast<double>(std::uint32_t(10)))));
      mask = sample_glyph(state, context, digit, within_glyph_x, local_y, iScale);
    }
  }
  [[maybe_unused]] glsl::Vec3 panel_bg = (base_rgb * (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(blend_alpha)))));
  if (mask < static_cast<float>(0.5)) {
    output = glsl::Vec4(glsl::Vec4(glsl::clamp(panel_bg, static_cast<float>(0.0), static_cast<float>(1.0)), glsl::swizzle<3>(texel)));
    return;
  }
  [[maybe_unused]] glsl::Vec3 osd_color = glsl::FloatExpr<3>(static_cast<float>(0.7), static_cast<float>(1.0), static_cast<float>(0.75));
  [[maybe_unused]] glsl::Vec3 highlight = glsl::component_max(panel_bg, (osd_color * mask));
  [[maybe_unused]] glsl::Vec3 blended = glsl::mix(panel_bg, highlight, blend_alpha);
  output = glsl::Vec4(glsl::Vec4(glsl::clamp(blended, static_cast<float>(0.0), static_cast<float>(1.0)), glsl::swizzle<3>(texel)));
}
}  // namespace typed_93

BoundKernel bind_filter_osd_osd(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_93::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("renderScale"), bindings.get_number("alpha"), bindings.get_number("seed"), bindings.get_number("speed"), bindings.get_number("time"), bindings.get<std::int32_t>("corner"));
  (void)bindings;
  return BoundKernel(state, &typed_93::pixel);
}

// End frozen OSD block
}
