// Test-only kernels from noisemaker-for-cpp a15c4b6816a3cb4a1811a03429e4fbf84530c722.
// Original src/typed_generated/typed_slice.cpp SHA-256:
// 3f7c1644dc966f4f401e523ca0ea830d1ddc2e4372263e8710120930f2176b4c
// Blocks below are byte-exact extractions; only the enclosing namespace differs.
#include "retired_kernels.hpp"

#include <cmath>
#include <cstdint>
#include <memory>

#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"

namespace noisemaker::historical_generated {
// Typed IR program: filter/bc:bc
// Source SHA-256: 1422e35c223dd3b9095dc0eb7b26b1b9f75767748689b15fd3e4006128089701
namespace typed_19 {
struct State final : KernelState {
  State(glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, const Surface* inputTex_value, double brightness_value, double contrast_value) : tileOffset(tileOffset_value), fullResolution(fullResolution_value), inputTex(inputTex_value), brightness(brightness_value), contrast(contrast_value) {}
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  const Surface* inputTex;
  double brightness;
  double contrast;
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

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::IVec2 texSize = texture_size(*state.inputTex);
  [[maybe_unused]] glsl::Vec2 uv = (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texSize));
  [[maybe_unused]] glsl::Vec4 color = sample_texture(*state.inputTex, uv);
  glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * state.brightness));
  [[maybe_unused]] double contrastFactor = (static_cast<double>(state.contrast) * static_cast<double>(static_cast<float>(2.0)));
  glsl::set_swizzle<0, 1, 2>(color, (((glsl::swizzle<0, 1, 2>(color) - static_cast<float>(0.5)) * contrastFactor) + static_cast<float>(0.5)));
  output = glsl::Vec4(color);
}
}  // namespace typed_19

BoundKernel bind_filter_bc_bc(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_19::State>(bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), &bindings.texture("inputTex"), bindings.get_number("brightness"), bindings.get_number("contrast"));
  (void)bindings;
  return BoundKernel(state, &typed_19::pixel);
}

// End frozen block: filter/bc:bc

// Typed IR program: filter/hs:hs
// Source SHA-256: 5449441668f1ed62da954294285b5fbeae48b7c9feeecbfbe3b56bcc9afae4d7
namespace typed_71 {
struct State final : KernelState {
  State(glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, const Surface* inputTex_value, double rotation_value, double hueRange_value, double saturation_value) : tileOffset(tileOffset_value), fullResolution(fullResolution_value), inputTex(inputTex_value), rotation(rotation_value), hueRange(hueRange_value), saturation(saturation_value) {}
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  const Surface* inputTex;
  double rotation;
  double hueRange;
  double saturation;
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

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept;

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] double h = glsl::fract(glsl::swizzle<0>(hsv));
  [[maybe_unused]] double s = glsl::swizzle<1>(hsv);
  [[maybe_unused]] double v = glsl::swizzle<2>(hsv);
  [[maybe_unused]] double c = (static_cast<double>(v) * static_cast<double>(s));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(h) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(v) - static_cast<double>(c));
  [[maybe_unused]] glsl::Vec3 rgb = {};
  if (h < static_cast<float>(0.1666666716337204)) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if (h < static_cast<float>(0.3333333432674408)) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if (h < static_cast<float>(0.5)) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if (h < static_cast<float>(0.6666666865348816)) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if (h < static_cast<float>(0.8333333134651184)) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
          }
        }
      }
    }
  }
  return (rgb + m);
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] double r = glsl::swizzle<0>(rgb);
  [[maybe_unused]] double g = glsl::swizzle<1>(rgb);
  [[maybe_unused]] double b = glsl::swizzle<2>(rgb);
  [[maybe_unused]] double maxC = glsl::component_max(r, glsl::component_max(g, b));
  [[maybe_unused]] double minC = glsl::component_min(r, glsl::component_min(g, b));
  [[maybe_unused]] double delta = (static_cast<double>(maxC) - static_cast<double>(minC));
  [[maybe_unused]] double h = static_cast<float>(0.0);
  if (delta != static_cast<float>(0.0)) {
    if (maxC == r) {
      h = (static_cast<double>(glsl::mod((static_cast<double>((static_cast<double>(g) - static_cast<double>(b))) / static_cast<double>(delta)), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0)));
    } else {
      if (maxC == g) {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(b) - static_cast<double>(r))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(2.0)))) / static_cast<double>(static_cast<float>(6.0)));
      } else {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(r) - static_cast<double>(g))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(4.0)))) / static_cast<double>(static_cast<float>(6.0)));
      }
    }
  }
  [[maybe_unused]] double s = ((maxC == static_cast<float>(0.0)) ? static_cast<float>(0.0) : (static_cast<double>(delta) / static_cast<double>(maxC)));
  return glsl::FloatExpr<3>(h, s, maxC);
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::IVec2 texSize = texture_size(*state.inputTex);
  [[maybe_unused]] glsl::Vec2 uv = (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texSize));
  [[maybe_unused]] glsl::Vec4 color = sample_texture(*state.inputTex, uv);
  [[maybe_unused]] glsl::Vec3 hsv = rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color));
  glsl::set_swizzle<0>(hsv, glsl::fract((static_cast<double>((static_cast<double>(glsl::swizzle<0>(hsv)) * static_cast<double>(map(state, context, state.hueRange, static_cast<float>(0.0), static_cast<float>(200.0), static_cast<float>(0.0), static_cast<float>(2.0))))) + static_cast<double>((static_cast<double>(state.rotation) / static_cast<double>(static_cast<float>(360.0)))))));
  glsl::set_swizzle<1>(hsv, (glsl::swizzle<1>(hsv) * state.saturation));
  glsl::set_swizzle<0, 1, 2>(color, hsv2rgb(state, context, hsv));
  output = glsl::Vec4(color);
}
}  // namespace typed_71

BoundKernel bind_filter_hs_hs(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_71::State>(bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), &bindings.texture("inputTex"), bindings.get_number("rotation"), bindings.get_number("hueRange"), bindings.get_number("saturation"));
  (void)bindings;
  return BoundKernel(state, &typed_71::pixel);
}

// End frozen block: filter/hs:hs

// Typed IR program: filter/corrupt:corrupt
// Source SHA-256: b81642d2e63294f9f51656eb2441cdaf479c495c5e4acb0d3a4907a13b070d02
namespace typed_41 {
struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double time_value, double seed_value, double intensity_value, double sort_value, double shift_value, double bits_value, double channelShift_value, double speed_value, double melt_value, double scatter_value, double bandHeight_value, double renderScale_value) : inputTex(inputTex_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), time(time_value), seed(seed_value), intensity(intensity_value), sort(sort_value), shift(shift_value), bits(bits_value), channelShift(channelShift_value), speed(speed_value), melt(melt_value), scatter(scatter_value), bandHeight(bandHeight_value), renderScale(renderScale_value) {}
  const Surface* inputTex;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  double seed;
  double intensity;
  double sort;
  double shift;
  double bits;
  double channelShift;
  double speed;
  double melt;
  double scatter;
  double bandHeight;
  double renderScale;
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

[[nodiscard]] glsl::Vec3 bitCorrupt([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double bitAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept;
[[nodiscard]] glsl::Vec2 byteShift([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double shiftAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept;
[[nodiscard]] glsl::Vec3 lineHash([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double line, [[maybe_unused]] double rt) noexcept;
[[nodiscard]] glsl::Vec2 meltDisplace([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double meltAmt, [[maybe_unused]] double t, [[maybe_unused]] double resX, [[maybe_unused]] double rs) noexcept;
[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept;
[[nodiscard]] glsl::Vec2 pixelSort([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double sortAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept;
[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept;
[[nodiscard]] double rowTime([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double row, [[maybe_unused]] double t) noexcept;
[[nodiscard]] glsl::Vec2 scatterDisplace([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double scatterAmt, [[maybe_unused]] double t, [[maybe_unused]] double rs, [[maybe_unused]] glsl::Vec2 tileOff) noexcept;

[[nodiscard]] glsl::Vec3 bitCorrupt([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double bitAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept {
  [[maybe_unused]] glsl::Vec3 bh = lineHash(state, context, (static_cast<double>(row) + static_cast<double>(static_cast<float>(400.0))), rt);
  [[maybe_unused]] double levels = glsl::mix(static_cast<float>(256.0), static_cast<float>(2.0), (static_cast<double>(bitAmt) * static_cast<double>(bitAmt)));
  color = glsl::Vec3(glsl::Vec3((glsl::floor(((color * levels) + static_cast<float>(0.5))) / levels)));
  if (bitAmt > static_cast<float>(0.3)) {
    [[maybe_unused]] double xorStrength = (static_cast<double>((static_cast<double>(bitAmt) - static_cast<double>(static_cast<float>(0.3)))) / static_cast<double>(static_cast<float>(0.7)));
    [[maybe_unused]] double px = glsl::floor((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(resX)));
    [[maybe_unused]] glsl::FloatExpr<3> xorHash = prng(state, context, glsl::FloatExpr<3>(px, row, (static_cast<double>((static_cast<double>(state.seed) + static_cast<double>(rt))) + static_cast<double>(static_cast<float>(500.0)))));
    [[maybe_unused]] glsl::Vec3 mask = glsl::step(glsl::FloatExpr<3>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(xorStrength) * static_cast<double>(static_cast<float>(0.5)))))), xorHash);
    color = glsl::Vec3(glsl::mix(color, (static_cast<float>(1.0) - color), mask));
  }
  if (bitAmt > static_cast<float>(0.6)) {
    [[maybe_unused]] double shiftStr = (static_cast<double>((static_cast<double>(bitAmt) - static_cast<double>(static_cast<float>(0.6)))) / static_cast<double>(static_cast<float>(0.4)));
    [[maybe_unused]] double bitShift = (static_cast<double>(glsl::floor((static_cast<double>(glsl::swizzle<0>(bh)) * static_cast<double>(static_cast<float>(4.0))))) + static_cast<double>(static_cast<float>(1.0)));
    [[maybe_unused]] double scale = glsl::pow(static_cast<float>(2.0), bitShift);
    color = glsl::Vec3(glsl::fract((color * glsl::mix(static_cast<float>(1.0), scale, shiftStr))));
  }
  return color;
}

[[nodiscard]] glsl::Vec2 byteShift([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double shiftAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept {
  [[maybe_unused]] glsl::Vec3 rh = lineHash(state, context, row, rt);
  [[maybe_unused]] double chunkWidth = (static_cast<double>(static_cast<float>(8.0)) + static_cast<double>((static_cast<double>(glsl::swizzle<0>(rh)) * static_cast<double>(static_cast<float>(80.0)))));
  [[maybe_unused]] double chunk = glsl::floor((static_cast<double>((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(resX))) / static_cast<double>(chunkWidth)));
  [[maybe_unused]] glsl::FloatExpr<3> ch = prng(state, context, glsl::FloatExpr<3>(chunk, (static_cast<double>(row) + static_cast<double>(static_cast<float>(200.0))), (static_cast<double>(state.seed) + static_cast<double>(rt))));
  [[maybe_unused]] double shiftPx = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(ch)) - static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(static_cast<float>(2.0)))) * static_cast<double>(shiftAmt))) * static_cast<double>(resX))) * static_cast<double>(static_cast<float>(0.15)));
  [[maybe_unused]] double sparsity = glsl::mix(static_cast<float>(0.85), static_cast<float>(0.3), shiftAmt);
  if (glsl::swizzle<1>(ch) > sparsity) {
    glsl::set_swizzle<0>(uv, glsl::fract((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>((static_cast<double>(shiftPx) / static_cast<double>(resX))))));
  }
  return uv;
}

[[nodiscard]] glsl::Vec3 lineHash([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double line, [[maybe_unused]] double rt) noexcept {
  return prng(state, context, glsl::FloatExpr<3>(line, state.seed, rt));
}

[[nodiscard]] glsl::Vec2 meltDisplace([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double meltAmt, [[maybe_unused]] double t, [[maybe_unused]] double resX, [[maybe_unused]] double rs) noexcept {
  [[maybe_unused]] double col = glsl::floor((static_cast<double>((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(resX))) / static_cast<double>(static_cast<float>(3.0))));
  [[maybe_unused]] double colPhase = glsl::swizzle<0>(prng(state, context, glsl::FloatExpr<3>(col, (static_cast<double>(state.seed) + static_cast<double>(static_cast<float>(601.0))), static_cast<float>(0.0))));
  [[maybe_unused]] glsl::FloatExpr<3> dripHash = prng(state, context, glsl::FloatExpr<3>(col, (static_cast<double>(state.seed) + static_cast<double>(static_cast<float>(600.0))), glsl::floor((static_cast<double>((static_cast<double>(t) + static_cast<double>(colPhase))) * static_cast<double>(static_cast<float>(8.0))))));
  [[maybe_unused]] double gravity = (static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::swizzle<1>(uv)))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::swizzle<1>(uv)))));
  [[maybe_unused]] double dripAmt = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(dripHash)) * static_cast<double>(meltAmt))) * static_cast<double>(gravity))) * static_cast<double>(static_cast<float>(0.4)));
  [[maybe_unused]] double dripProb = glsl::mix(static_cast<float>(0.9), static_cast<float>(0.2), meltAmt);
  if (glsl::swizzle<1>(dripHash) > dripProb) {
    [[maybe_unused]] double wobble = (static_cast<double>((static_cast<double>(glsl::sin((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<1>(uv)) * static_cast<double>(static_cast<float>(20.0)))) + static_cast<double>((static_cast<double>(glsl::swizzle<2>(dripHash)) * static_cast<double>(static_cast<float>(6.28318530718)))))) + static_cast<double>(t)))) * static_cast<double>(meltAmt))) * static_cast<double>(static_cast<float>(0.02)));
    glsl::set_swizzle<1>(uv, glsl::clamp((static_cast<double>(glsl::swizzle<1>(uv)) + static_cast<double>(dripAmt)), static_cast<float>(0.0), static_cast<float>(1.0)));
    glsl::set_swizzle<0>(uv, glsl::fract((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>(wobble))));
  }
  return uv;
}

[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept {
  v = ((v * std::uint32_t(1664525)) + std::uint32_t(1013904223));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  v = glsl::bitwise_xor(v, glsl::shift_right(v, std::uint32_t(16)));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  return v;
}

[[nodiscard]] glsl::Vec2 pixelSort([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double row, [[maybe_unused]] double sortAmt, [[maybe_unused]] double rt, [[maybe_unused]] double resX) noexcept {
  [[maybe_unused]] glsl::Vec3 rh = lineHash(state, context, row, rt);
  [[maybe_unused]] double threshold = glsl::mix(static_cast<float>(0.8), static_cast<float>(0.2), sortAmt);
  [[maybe_unused]] double regionSize = (static_cast<double>(static_cast<float>(3.0)) + static_cast<double>((static_cast<double>(glsl::swizzle<1>(rh)) * static_cast<double>(static_cast<float>(20.0)))));
  [[maybe_unused]] double region = glsl::floor((static_cast<double>((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(resX))) / static_cast<double>(regionSize)));
  [[maybe_unused]] glsl::FloatExpr<3> regionHash = prng(state, context, glsl::FloatExpr<3>(region, row, (static_cast<double>(state.seed) + static_cast<double>(rt))));
  [[maybe_unused]] double regionPos = glsl::fract((static_cast<double>((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(resX))) / static_cast<double>(regionSize)));
  [[maybe_unused]] double sortShift = (static_cast<double>((static_cast<double>((static_cast<double>(regionPos) * static_cast<double>(glsl::swizzle<0>(regionHash)))) * static_cast<double>(sortAmt))) * static_cast<double>(static_cast<float>(0.15)));
  if (glsl::swizzle<1>(regionHash) > threshold) {
    glsl::set_swizzle<0>(uv, glsl::fract((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>(sortShift))));
  }
  return uv;
}

[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept {
  glsl::set_swizzle<0>(p, ((glsl::swizzle<0>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<0>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<0>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  glsl::set_swizzle<1>(p, ((glsl::swizzle<1>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<1>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<1>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  glsl::set_swizzle<2>(p, ((glsl::swizzle<2>(p) >= static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<2>(p)) * static_cast<double>(static_cast<float>(2.0))) : (static_cast<double>((static_cast<double>((-glsl::swizzle<2>(p))) * static_cast<double>(static_cast<float>(2.0)))) + static_cast<double>(static_cast<float>(1.0)))));
  return glsl::FloatExpr<3>(glsl::Vec3((glsl::Vec3(pcg(state, context, glsl::UVec3(p))) / float(std::uint32_t(4294967295)))));
}

[[nodiscard]] double rowTime([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double row, [[maybe_unused]] double t) noexcept {
  [[maybe_unused]] double phase = glsl::swizzle<0>(prng(state, context, glsl::FloatExpr<3>(row, (static_cast<double>(state.seed) + static_cast<double>(static_cast<float>(777.0))), static_cast<float>(0.0))));
  return glsl::floor((static_cast<double>((static_cast<double>(t) + static_cast<double>(phase))) * static_cast<double>(static_cast<float>(8.0))));
}

[[nodiscard]] glsl::Vec2 scatterDisplace([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double scatterAmt, [[maybe_unused]] double t, [[maybe_unused]] double rs, [[maybe_unused]] glsl::Vec2 tileOff) noexcept {
  [[maybe_unused]] glsl::Vec2 scaledCoord = glsl::floor(((glsl::swizzle<0, 1>(context.frag_coord) + tileOff) / rs));
  [[maybe_unused]] glsl::FloatExpr<3> phaseHash = prng(state, context, glsl::Vec3(scaledCoord, (static_cast<double>(state.seed) + static_cast<double>(static_cast<float>(700.0)))));
  [[maybe_unused]] double pixTime = glsl::floor((static_cast<double>((static_cast<double>(t) + static_cast<double>(glsl::swizzle<0>(phaseHash)))) * static_cast<double>(static_cast<float>(8.0))));
  [[maybe_unused]] glsl::FloatExpr<3> pixHash = prng(state, context, glsl::Vec3(scaledCoord, (static_cast<double>(pixTime) + static_cast<double>(state.seed))));
  [[maybe_unused]] double threshold = glsl::mix(static_cast<float>(0.98), static_cast<float>(0.1), (static_cast<double>(scatterAmt) * static_cast<double>(scatterAmt)));
  if (glsl::swizzle<0>(pixHash) > threshold) {
    [[maybe_unused]] glsl::FloatExpr<3> dirHash = prng(state, context, glsl::Vec3((scaledCoord + static_cast<float>(1000.0)), (static_cast<double>(pixTime) + static_cast<double>(state.seed))));
    [[maybe_unused]] double dist = (static_cast<double>((static_cast<double>(scatterAmt) * static_cast<double>(static_cast<float>(0.15)))) * static_cast<double>((static_cast<double>(static_cast<float>(0.5)) + static_cast<double>((static_cast<double>(glsl::swizzle<1>(pixHash)) * static_cast<double>(static_cast<float>(0.5)))))));
    glsl::set_swizzle<0>(uv, glsl::fract((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(dirHash)) - static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(dist))))));
    glsl::set_swizzle<1>(uv, glsl::clamp((static_cast<double>(glsl::swizzle<1>(uv)) + static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<1>(dirHash)) - static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(dist)))), static_cast<float>(0.0), static_cast<float>(1.0)));
  }
  return uv;
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 tileDims = glsl::Vec2(texture_size(*state.inputTex));
  [[maybe_unused]] glsl::Vec2 resolution = ((glsl::swizzle<0>(state.fullResolution) > static_cast<float>(0.0)) ? glsl::Vec2(state.fullResolution) : glsl::Vec2(tileDims));
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / resolution);
  [[maybe_unused]] double rs = glsl::component_max(state.renderScale, static_cast<float>(1.0));
  [[maybe_unused]] double resX = (static_cast<double>(glsl::swizzle<0>(resolution)) / static_cast<double>(rs));
  [[maybe_unused]] double spd = glsl::floor(state.speed);
  [[maybe_unused]] double t = (static_cast<double>((static_cast<double>(state.time) * static_cast<double>(static_cast<float>(6.28318530718)))) * static_cast<double>(spd));
  [[maybe_unused]] double rawRow = (static_cast<double>(glsl::swizzle<1>(globalCoord)) / static_cast<double>(rs));
  [[maybe_unused]] double bh = glsl::component_max(static_cast<float>(1.0), glsl::floor((static_cast<double>(state.bandHeight) * static_cast<double>(static_cast<float>(0.32)))));
  [[maybe_unused]] double row = glsl::floor((static_cast<double>(rawRow) / static_cast<double>(bh)));
  [[maybe_unused]] double rt = rowTime(state, context, row, t);
  [[maybe_unused]] glsl::Vec3 rowHash = lineHash(state, context, row, rt);
  [[maybe_unused]] double prob = (static_cast<double>(state.intensity) / static_cast<double>(static_cast<float>(100.0)));
  [[maybe_unused]] bool isCorrupt = (glsl::swizzle<0>(rowHash) < prob);
  [[maybe_unused]] glsl::Vec2& sampleUv = uv;
  [[maybe_unused]] double meltAmt = (static_cast<double>(state.melt) / static_cast<double>(static_cast<float>(100.0)));
  if (meltAmt > static_cast<float>(0.0)) {
    sampleUv = glsl::Vec2(meltDisplace(state, context, sampleUv, meltAmt, t, resX, rs));
  }
  [[maybe_unused]] double scatterAmt = (static_cast<double>(state.scatter) / static_cast<double>(static_cast<float>(100.0)));
  if (scatterAmt > static_cast<float>(0.0)) {
    sampleUv = glsl::Vec2(scatterDisplace(state, context, sampleUv, scatterAmt, t, rs, state.tileOffset));
  }
  if (isCorrupt) {
    [[maybe_unused]] double sortAmt = (static_cast<double>(state.sort) / static_cast<double>(static_cast<float>(100.0)));
    [[maybe_unused]] double shiftAmt = (static_cast<double>(state.shift) / static_cast<double>(static_cast<float>(100.0)));
    if (sortAmt > static_cast<float>(0.0)) {
      sampleUv = glsl::Vec2(pixelSort(state, context, sampleUv, row, sortAmt, rt, resX));
    }
    if (shiftAmt > static_cast<float>(0.0)) {
      sampleUv = glsl::Vec2(byteShift(state, context, sampleUv, row, shiftAmt, rt, resX));
    }
  }
  [[maybe_unused]] glsl::Vec3 color = glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, sampleUv));
  if ((state.channelShift > static_cast<float>(0.0)) && isCorrupt) {
    [[maybe_unused]] double chAmt = (static_cast<double>(state.channelShift) / static_cast<double>(static_cast<float>(100.0)));
    [[maybe_unused]] glsl::Vec3 chHash = lineHash(state, context, (static_cast<double>(row) + static_cast<double>(static_cast<float>(300.0))), rt);
    [[maybe_unused]] double rShift = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(chHash)) - static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(chAmt))) * static_cast<double>(static_cast<float>(0.08)));
    [[maybe_unused]] double bShift = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<1>(chHash)) - static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(chAmt))) * static_cast<double>(static_cast<float>(0.08)));
    [[maybe_unused]] glsl::Vec2 rUv = glsl::FloatExpr<2>(glsl::fract((static_cast<double>(glsl::swizzle<0>(sampleUv)) + static_cast<double>(rShift))), glsl::swizzle<1>(sampleUv));
    [[maybe_unused]] glsl::Vec2 bUv = glsl::FloatExpr<2>(glsl::fract((static_cast<double>(glsl::swizzle<0>(sampleUv)) + static_cast<double>(bShift))), glsl::swizzle<1>(sampleUv));
    glsl::set_swizzle<0>(color, glsl::swizzle<0>(sample_texture(*state.inputTex, rUv)));
    glsl::set_swizzle<2>(color, glsl::swizzle<2>(sample_texture(*state.inputTex, bUv)));
  }
  if ((state.bits > static_cast<float>(0.0)) && isCorrupt) {
    color = glsl::Vec3(bitCorrupt(state, context, color, sampleUv, row, (static_cast<double>(state.bits) / static_cast<double>(static_cast<float>(100.0))), rt, resX));
  }
  output = glsl::Vec4(glsl::Vec4(color, static_cast<float>(1.0)));
}
}  // namespace typed_41

BoundKernel bind_filter_corrupt_corrupt(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_41::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("time"), bindings.get_number("seed"), bindings.get_number("intensity"), bindings.get_number("sort"), bindings.get_number("shift"), bindings.get_number("bits"), bindings.get_number("channelShift"), bindings.get_number("speed"), bindings.get_number("melt"), bindings.get_number("scatter"), bindings.get_number("bandHeight"), bindings.get_number("renderScale"));
  (void)bindings;
  return BoundKernel(state, &typed_41::pixel);
}

// End frozen block: filter/corrupt:corrupt
}  // namespace noisemaker::historical_generated
