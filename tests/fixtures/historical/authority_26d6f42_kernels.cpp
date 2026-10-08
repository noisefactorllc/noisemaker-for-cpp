// Test-only kernels from noisemaker-for-cpp 03770a6eb5f6dc4089916b42555146235a7f0428
// (CPU authority 26d6f42, corpus e24c844f), retained only for the immutable
// historical captures recorded against them. Original
// src/typed_generated/typed_slice.cpp SHA-256:
// 39fb5c1c09d8e62eb0a61b9fa181150cb905decd950c02199b1f5b5c736be631
// Blocks below are byte-exact extractions; only the enclosing namespace differs
// and the retired comparer is spelled historical_truthy_vector_equality.
#include "authority_26d6f42_kernels.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <memory>

#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"

// The blocks keep their original typed_<n> namespaces, which other historical
// fixtures also use, so they sit in their own enclosing namespace.
namespace noisemaker::historical_generated::authority_26d6f42 {
namespace {
// The authority before 8ae8e2a compiled vector `==` to a typed array of lane
// comparisons, an object JavaScript treats as truthy whatever its lanes hold.
template <std::size_t N, class T>
[[nodiscard]] constexpr bool historical_truthy_vector_equality(
    const glsl::Vec<N, T>&, const glsl::Vec<N, T>&) noexcept {
  return true;
}
}  // namespace

// Typed IR program: classicNoisedeck/coalesce:coalesce
// Source SHA-256: a0f96df68ce058e5e2154c78880b5a611eaf5ab9adcd64242368978c813b6b58
namespace typed_4 {
struct State final : KernelState {
  State(const Surface* inputTex_value, const Surface* tex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double time_value, std::int32_t blendMode_value, double mixAmt_value, double refractAAmt_value, double refractBAmt_value, double refractADir_value, double refractBDir_value) : inputTex(inputTex_value), tex(tex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), time(time_value), blendMode(blendMode_value), mixAmt(mixAmt_value), refractAAmt(refractAAmt_value), refractBAmt(refractBAmt_value), refractADir(refractADir_value), refractBDir(refractBDir_value) {}
  const Surface* inputTex;
  const Surface* tex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  std::int32_t blendMode;
  double mixAmt;
  double refractAAmt;
  double refractBAmt;
  double refractADir;
  double refractBDir;
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

[[nodiscard]] glsl::Vec3 blend([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color1, [[maybe_unused]] glsl::Vec4 color2, [[maybe_unused]] std::int32_t mode, [[maybe_unused]] double factor) noexcept;
[[nodiscard]] double blendOverlay([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double a, [[maybe_unused]] double b) noexcept;
[[nodiscard]] double blendSoftLight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base, [[maybe_unused]] double blend) noexcept;
[[nodiscard]] glsl::Vec4 cloak([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept;

[[nodiscard]] glsl::Vec3 blend([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color1, [[maybe_unused]] glsl::Vec4 color2, [[maybe_unused]] std::int32_t mode, [[maybe_unused]] double factor) noexcept {
  [[maybe_unused]] glsl::Vec4 color = {};
  [[maybe_unused]] glsl::Vec4 middle = {};
  [[maybe_unused]] double amt = map(state, context, state.mixAmt, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec4 a = glsl::FloatExpr<4>(static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec4 b = glsl::FloatExpr<4>(static_cast<float>(1.0));
  if (mode >= std::int32_t(1000)) {
    glsl::set_swizzle<0, 1, 2>(a, rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color1)));
    glsl::set_swizzle<0, 1, 2>(b, rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color2)));
  }
  if (mode == std::int32_t(0)) {
    middle = glsl::Vec4(glsl::component_min((color1 + color2), static_cast<float>(1.0)));
  } else {
    if (mode == std::int32_t(1)) {
      if (state.mixAmt < static_cast<float>(0.0)) {
        return glsl::swizzle<0, 1, 2>(glsl::mix(color1, ((color2 * glsl::FloatExpr<4>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::swizzle<3>(color1))))) + (color1 * glsl::FloatExpr<4>(glsl::swizzle<3>(color1)))), map(state, context, state.mixAmt, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0))));
      } else {
        return glsl::swizzle<0, 1, 2>(glsl::mix(((color1 * glsl::FloatExpr<4>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::swizzle<3>(color2))))) + (color2 * glsl::FloatExpr<4>(glsl::swizzle<3>(color2)))), color2, map(state, context, state.mixAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0))));
      }
    } else {
      if (mode == std::int32_t(2)) {
        middle = glsl::Vec4(middle);
      } else {
        if (mode == std::int32_t(3)) {
          middle = glsl::Vec4(middle);
        } else {
          if (mode == std::int32_t(4)) {
            middle = glsl::Vec4(glsl::component_min(color1, color2));
          } else {
            if (mode == std::int32_t(5)) {
              middle = glsl::Vec4(glsl::abs((color1 - color2)));
            } else {
              if (mode == std::int32_t(6)) {
                middle = glsl::Vec4(((color1 + color2) - ((static_cast<float>(2.0) * color1) * color2)));
              } else {
                if (mode == std::int32_t(7)) {
                  middle = glsl::Vec4(middle);
                } else {
                  if (mode == std::int32_t(8)) {
                    middle = glsl::Vec4(glsl::FloatExpr<4>(blendOverlay(state, context, glsl::swizzle<0>(color2), glsl::swizzle<0>(color1)), blendOverlay(state, context, glsl::swizzle<1>(color2), glsl::swizzle<1>(color1)), blendOverlay(state, context, glsl::swizzle<2>(color2), glsl::swizzle<2>(color1)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                  } else {
                    if (mode == std::int32_t(9)) {
                      middle = glsl::Vec4(glsl::component_max(color1, color2));
                    } else {
                      if (mode == std::int32_t(10)) {
                        middle = glsl::Vec4(glsl::mix(color1, color2, static_cast<float>(0.5)));
                      } else {
                        if (mode == std::int32_t(11)) {
                          middle = glsl::Vec4((color1 * color2));
                        } else {
                          if (mode == std::int32_t(12)) {
                            middle = glsl::Vec4(glsl::Vec4((glsl::FloatExpr<4>(static_cast<float>(1.0)) - glsl::abs(((glsl::FloatExpr<4>(static_cast<float>(1.0)) - color1) - color2)))));
                          } else {
                            if (mode == std::int32_t(13)) {
                              middle = glsl::Vec4(glsl::FloatExpr<4>(blendOverlay(state, context, glsl::swizzle<0>(color1), glsl::swizzle<0>(color2)), blendOverlay(state, context, glsl::swizzle<1>(color1), glsl::swizzle<1>(color2)), blendOverlay(state, context, glsl::swizzle<2>(color1), glsl::swizzle<2>(color2)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                            } else {
                              if (mode == std::int32_t(14)) {
                                middle = glsl::Vec4(glsl::Vec4((glsl::Vec4((glsl::component_min(color1, color2) - glsl::component_max(color1, color2))) + glsl::FloatExpr<4>(static_cast<float>(1.0)))));
                              } else {
                                if (mode == std::int32_t(15)) {
                                  middle = glsl::Vec4(middle);
                                } else {
                                  if (mode == std::int32_t(16)) {
                                    middle = glsl::Vec4((static_cast<float>(1.0) - ((static_cast<float>(1.0) - color1) * (static_cast<float>(1.0) - color2))));
                                  } else {
                                    if (mode == std::int32_t(17)) {
                                      middle = glsl::Vec4(glsl::FloatExpr<4>(blendSoftLight(state, context, glsl::swizzle<0>(color1), glsl::swizzle<0>(color2)), blendSoftLight(state, context, glsl::swizzle<1>(color1), glsl::swizzle<1>(color2)), blendSoftLight(state, context, glsl::swizzle<2>(color1), glsl::swizzle<2>(color2)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                                    } else {
                                      if (mode == std::int32_t(18)) {
                                        middle = glsl::Vec4(glsl::component_max(((color1 + color2) - static_cast<float>(1.0)), static_cast<float>(0.0)));
                                      } else {
                                        if (mode == std::int32_t(1000)) {
                                          glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(b), glsl::swizzle<1>(a), glsl::swizzle<2>(a))));
                                        } else {
                                          if (mode == std::int32_t(1001)) {
                                            glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(a), glsl::swizzle<1>(b), glsl::swizzle<2>(b))));
                                          } else {
                                            if (mode == std::int32_t(1002)) {
                                              glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(a), glsl::swizzle<1>(b), glsl::swizzle<2>(a))));
                                            } else {
                                              if (mode == std::int32_t(1003)) {
                                                glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(b), glsl::swizzle<1>(a), glsl::swizzle<2>(b))));
                                              } else {
                                                if (mode == std::int32_t(1004)) {
                                                  glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(a), glsl::swizzle<1>(a), glsl::swizzle<2>(b))));
                                                } else {
                                                  if (mode == std::int32_t(1005)) {
                                                    glsl::set_swizzle<0, 1, 2>(middle, hsv2rgb(state, context, glsl::FloatExpr<3>(glsl::swizzle<0>(b), glsl::swizzle<1>(b), glsl::swizzle<2>(a))));
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  if (mode >= std::int32_t(1000)) {
    glsl::set_swizzle<3>(middle, glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5)));
  }
  if (factor == static_cast<float>(0.5)) {
    color = glsl::Vec4(middle);
  } else {
    if (factor < static_cast<float>(0.5)) {
      factor = map(state, context, amt, static_cast<float>(0.0), static_cast<float>(0.5), static_cast<float>(0.0), static_cast<float>(1.0));
      color = glsl::Vec4(glsl::mix(color1, middle, factor));
    } else {
      if (factor > static_cast<float>(0.5)) {
        factor = map(state, context, amt, static_cast<float>(0.5), static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(1.0));
        color = glsl::Vec4(glsl::mix(middle, color2, factor));
      }
    }
  }
  return glsl::swizzle<0, 1, 2>(color);
}

[[nodiscard]] double blendOverlay([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double a, [[maybe_unused]] double b) noexcept {
  return ((a < static_cast<float>(0.5)) ? (static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(a))) * static_cast<double>(b)) : (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(a))))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(b)))))));
}

[[nodiscard]] double blendSoftLight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base, [[maybe_unused]] double blend) noexcept {
  return ((blend < static_cast<float>(0.5)) ? (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(base))) * static_cast<double>(blend))) + static_cast<double>((static_cast<double>((static_cast<double>(base) * static_cast<double>(base))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(blend)))))))) : (static_cast<double>((static_cast<double>(glsl::sqrt(base)) * static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(blend))) - static_cast<double>(static_cast<float>(1.0)))))) + static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(base))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(blend)))))));
}

[[nodiscard]] glsl::Vec4 cloak([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept {
  [[maybe_unused]] double m = map(state, context, state.mixAmt, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] double ra = map(state, context, state.refractAAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(0.125));
  [[maybe_unused]] double rb = map(state, context, state.refractBAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(0.125));
  [[maybe_unused]] glsl::Vec4 leftColor = sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex))));
  [[maybe_unused]] glsl::Vec4 rightColor = sample_texture(*state.tex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.tex))));
  [[maybe_unused]] glsl::Vec2 leftUV = glsl::Vec2(st);
  [[maybe_unused]] double rightLen = glsl::length(glsl::swizzle<0, 1, 2>(rightColor));
  glsl::set_swizzle<0>(leftUV, (glsl::swizzle<0>(leftUV) + (static_cast<double>(glsl::cos((static_cast<double>(rightLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(ra))));
  glsl::set_swizzle<1>(leftUV, (glsl::swizzle<1>(leftUV) + (static_cast<double>(glsl::sin((static_cast<double>(rightLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(ra))));
  [[maybe_unused]] glsl::Vec2 leftLocalUV = (((leftUV * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)));
  [[maybe_unused]] glsl::Vec4 leftRefracted = sample_texture(*state.inputTex, glsl::fract(leftLocalUV));
  [[maybe_unused]] glsl::Vec2 rightUV = glsl::Vec2(leftUV);
  [[maybe_unused]] double leftLen = glsl::length(glsl::swizzle<0, 1, 2>(leftColor));
  glsl::set_swizzle<0>(rightUV, (glsl::swizzle<0>(rightUV) + (static_cast<double>(glsl::cos((static_cast<double>(leftLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(rb))));
  glsl::set_swizzle<1>(rightUV, (glsl::swizzle<1>(rightUV) + (static_cast<double>(glsl::sin((static_cast<double>(leftLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(rb))));
  [[maybe_unused]] glsl::Vec2 rightLocalUV = (((rightUV * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.tex)));
  [[maybe_unused]] glsl::Vec4 rightRefracted = sample_texture(*state.tex, glsl::fract(rightLocalUV));
  [[maybe_unused]] glsl::Vec4 leftReflected = glsl::component_min(((rightRefracted * rightColor) / (static_cast<float>(1.0) - (leftRefracted * leftColor))), glsl::FloatExpr<4>(static_cast<float>(1.0)));
  [[maybe_unused]] glsl::Vec4 rightReflected = glsl::component_min(((leftRefracted * leftColor) / (static_cast<float>(1.0) - (rightRefracted * rightColor))), glsl::FloatExpr<4>(static_cast<float>(1.0)));
  [[maybe_unused]] glsl::Vec4 left = glsl::FloatExpr<4>(static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec4 right = glsl::FloatExpr<4>(static_cast<float>(1.0));
  if (state.mixAmt < static_cast<float>(0.0)) {
    left = glsl::Vec4(glsl::mix(leftRefracted, leftReflected, map(state, context, state.mixAmt, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0))));
    right = glsl::Vec4(rightReflected);
  } else {
    left = glsl::Vec4(leftReflected);
    right = glsl::Vec4(glsl::mix(rightRefracted, rightRefracted, map(state, context, state.mixAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0))));
  }
  return glsl::mix(left, right, m);
}

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] double h = glsl::fract(glsl::swizzle<0>(hsv));
  [[maybe_unused]] double s = glsl::swizzle<1>(hsv);
  [[maybe_unused]] double v = glsl::swizzle<2>(hsv);
  [[maybe_unused]] double c = (static_cast<double>(v) * static_cast<double>(s));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(h) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(v) - static_cast<double>(c));
  [[maybe_unused]] glsl::Vec3 rgb = {};
  if ((static_cast<float>(0.0) <= h) && (h < static_cast<float>(0.1666666716337204))) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if ((static_cast<float>(0.1666666716337204) <= h) && (h < static_cast<float>(0.3333333432674408))) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if ((static_cast<float>(0.3333333432674408) <= h) && (h < static_cast<float>(0.5))) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if ((static_cast<float>(0.5) <= h) && (h < static_cast<float>(0.6666666865348816))) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if ((static_cast<float>(0.6666666865348816) <= h) && (h < static_cast<float>(0.8333333134651184))) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            if ((static_cast<float>(0.8333333134651184) <= h) && (h < static_cast<float>(1.0))) {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
            } else {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(0.0)));
            }
          }
        }
      }
    }
  }
  return (rgb + glsl::FloatExpr<3>(m, m, m));
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] double r = glsl::swizzle<0>(rgb);
  [[maybe_unused]] double g = glsl::swizzle<1>(rgb);
  [[maybe_unused]] double b = glsl::swizzle<2>(rgb);
  [[maybe_unused]] double max = glsl::component_max(r, glsl::component_max(g, b));
  [[maybe_unused]] double min = glsl::component_min(r, glsl::component_min(g, b));
  [[maybe_unused]] double delta = (static_cast<double>(max) - static_cast<double>(min));
  [[maybe_unused]] double h = static_cast<float>(0.0);
  if (delta != static_cast<float>(0.0)) {
    if (max == r) {
      h = (static_cast<double>(glsl::mod((static_cast<double>((static_cast<double>(g) - static_cast<double>(b))) / static_cast<double>(delta)), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0)));
    } else {
      if (max == g) {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(b) - static_cast<double>(r))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(2.0)))) / static_cast<double>(static_cast<float>(6.0)));
      } else {
        if (max == b) {
          h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(r) - static_cast<double>(g))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(4.0)))) / static_cast<double>(static_cast<float>(6.0)));
        }
      }
    }
  }
  [[maybe_unused]] double s = ((max == static_cast<float>(0.0)) ? static_cast<float>(0.0) : (static_cast<double>(delta) / static_cast<double>(max)));
  [[maybe_unused]] double v = max;
  return glsl::FloatExpr<3>(h, s, v);
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0), static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec2 st = (globalCoord / state.fullResolution);
  if (state.blendMode == std::int32_t(100)) {
    color = glsl::Vec4(cloak(state, context, st));
  } else {
    [[maybe_unused]] double ra = map(state, context, state.refractAAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(0.125));
    [[maybe_unused]] double rb = map(state, context, state.refractBAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(0.125));
    [[maybe_unused]] glsl::Vec4 leftColor = sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex))));
    [[maybe_unused]] glsl::Vec4 rightColor = sample_texture(*state.tex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.tex))));
    [[maybe_unused]] glsl::Vec2 leftUV = glsl::Vec2(st);
    [[maybe_unused]] double rightLen = (static_cast<double>(glsl::length(glsl::swizzle<0, 1, 2>(rightColor))) + static_cast<double>((static_cast<double>(state.refractADir) / static_cast<double>(static_cast<float>(360.0)))));
    glsl::set_swizzle<0>(leftUV, (glsl::swizzle<0>(leftUV) + (static_cast<double>(glsl::cos((static_cast<double>(rightLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(ra))));
    glsl::set_swizzle<1>(leftUV, (glsl::swizzle<1>(leftUV) + (static_cast<double>(glsl::sin((static_cast<double>(rightLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(ra))));
    [[maybe_unused]] glsl::Vec2 leftLocalUV = (((leftUV * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)));
    [[maybe_unused]] glsl::Vec4 color1 = sample_texture(*state.inputTex, glsl::fract(leftLocalUV));
    [[maybe_unused]] glsl::Vec2 rightUV = glsl::Vec2(leftUV);
    [[maybe_unused]] double leftLen = (static_cast<double>(glsl::length(glsl::swizzle<0, 1, 2>(leftColor))) + static_cast<double>((static_cast<double>(state.refractBDir) / static_cast<double>(static_cast<float>(360.0)))));
    glsl::set_swizzle<0>(rightUV, (glsl::swizzle<0>(rightUV) + (static_cast<double>(glsl::cos((static_cast<double>(leftLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(rb))));
    glsl::set_swizzle<1>(rightUV, (glsl::swizzle<1>(rightUV) + (static_cast<double>(glsl::sin((static_cast<double>(leftLen) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(rb))));
    [[maybe_unused]] glsl::Vec2 rightLocalUV = (((rightUV * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.tex)));
    [[maybe_unused]] glsl::Vec4 color2 = sample_texture(*state.tex, glsl::fract(rightLocalUV));
    glsl::set_swizzle<0, 1, 2>(color, blend(state, context, color1, color2, state.blendMode, state.mixAmt));
    glsl::set_swizzle<3>(color, glsl::component_max(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2)));
  }
  output = glsl::Vec4(color);
}
}  // namespace typed_4

BoundKernel bind_classicNoisedeck_coalesce_coalesce(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_4::State>(&bindings.texture("inputTex"), &bindings.texture("tex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("time"), bindings.get<std::int32_t>("blendMode"), bindings.get_number("mixAmt"), bindings.get_number("refractAAmt"), bindings.get_number("refractBAmt"), bindings.get_number("refractADir"), bindings.get_number("refractBDir"));
  (void)bindings;
  return BoundKernel(state, &typed_4::pixel);
}
// Typed IR program: classicNoisedeck/colorLab:colorLab
// Source SHA-256: 4bf9ea925634ee684e01917ea3b690d332b37905d21c8aa7377bf88625570945
namespace typed_5 {
struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double renderScale_value, double time_value, double levels_value, std::int32_t dither_value, double hueRotation_value, double hueRange_value, bool invert_value, double brightness_value, double contrast_value, double saturation_value, std::int32_t colorMode_value, std::int32_t paletteMode_value, glsl::DVec3 paletteOffset_value, glsl::DVec3 paletteAmp_value, glsl::DVec3 paletteFreq_value, glsl::DVec3 palettePhase_value, std::int32_t cyclePalette_value, double rotatePalette_value, double repeatPalette_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), renderScale(renderScale_value), time(time_value), levels(levels_value), dither(dither_value), hueRotation(hueRotation_value), hueRange(hueRange_value), invert(invert_value), brightness(brightness_value), contrast(contrast_value), saturation(saturation_value), colorMode(colorMode_value), paletteMode(paletteMode_value), paletteOffset(paletteOffset_value), paletteAmp(paletteAmp_value), paletteFreq(paletteFreq_value), palettePhase(palettePhase_value), cyclePalette(cyclePalette_value), rotatePalette(rotatePalette_value), repeatPalette(repeatPalette_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double renderScale;
  double time;
  double levels;
  std::int32_t dither;
  double hueRotation;
  double hueRange;
  bool invert;
  double brightness;
  double contrast;
  double saturation;
  std::int32_t colorMode;
  std::int32_t paletteMode;
  glsl::DVec3 paletteOffset;
  glsl::DVec3 paletteAmp;
  glsl::DVec3 paletteFreq;
  glsl::DVec3 palettePhase;
  std::int32_t cyclePalette;
  double rotatePalette;
  double repeatPalette;
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

[[nodiscard]] glsl::Vec3 brightnessContrast([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] glsl::Vec3 desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
[[nodiscard]] glsl::Vec3 linearToSrgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 linear) noexcept;
[[nodiscard]] glsl::Vec3 linear_srgb_from_oklab([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 c) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] double offsets([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 oklab_from_linear_srgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 c) noexcept;
[[nodiscard]] glsl::Vec3 pal([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double t) noexcept;
[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept;
[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double p) noexcept;
[[nodiscard]] glsl::Vec3 posterize([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] double lev) noexcept;
[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept;
[[nodiscard]] double random([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept;
[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] glsl::Vec3 srgbToLinear([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 srgb) noexcept;

[[nodiscard]] glsl::Vec3 brightnessContrast([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double bright = map(state, context, state.brightness, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(-1.0), static_cast<float>(1.0));
  [[maybe_unused]] double cont = map(state, context, state.contrast, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(2.0));
  color = glsl::Vec3(((((color - static_cast<float>(0.5)) * cont) + static_cast<float>(0.5)) + bright));
  return color;
}

[[nodiscard]] glsl::Vec3 desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double avg = (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.2126)) * static_cast<double>(glsl::swizzle<0>(color)))) + static_cast<double>((static_cast<double>(static_cast<float>(0.7152)) * static_cast<double>(glsl::swizzle<1>(color)))))) + static_cast<double>((static_cast<double>(static_cast<float>(0.0722)) * static_cast<double>(glsl::swizzle<2>(color)))));
  return glsl::FloatExpr<3>(avg);
}

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] double h = glsl::fract(glsl::swizzle<0>(hsv));
  [[maybe_unused]] double s = glsl::swizzle<1>(hsv);
  [[maybe_unused]] double v = glsl::swizzle<2>(hsv);
  [[maybe_unused]] double c = (static_cast<double>(v) * static_cast<double>(s));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(h) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(v) - static_cast<double>(c));
  [[maybe_unused]] glsl::Vec3 rgb = {};
  if ((static_cast<float>(0.0) <= h) && (h < static_cast<float>(0.1666666716337204))) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if ((static_cast<float>(0.1666666716337204) <= h) && (h < static_cast<float>(0.3333333432674408))) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if ((static_cast<float>(0.3333333432674408) <= h) && (h < static_cast<float>(0.5))) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if ((static_cast<float>(0.5) <= h) && (h < static_cast<float>(0.6666666865348816))) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if ((static_cast<float>(0.6666666865348816) <= h) && (h < static_cast<float>(0.8333333134651184))) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            if ((static_cast<float>(0.8333333134651184) <= h) && (h < static_cast<float>(1.0))) {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
            } else {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(0.0)));
            }
          }
        }
      }
    }
  }
  return (rgb + glsl::FloatExpr<3>(m, m, m));
}

[[nodiscard]] glsl::Vec3 linearToSrgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 linear) noexcept {
  [[maybe_unused]] glsl::Vec3 srgb = {};
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(3)); ++i) {
    if (linear[static_cast<std::size_t>(i)] <= static_cast<float>(0.0031308)) {
      srgb[static_cast<std::size_t>(i)] = (static_cast<double>(linear[static_cast<std::size_t>(i)]) * static_cast<double>(static_cast<float>(12.92)));
    } else {
      srgb[static_cast<std::size_t>(i)] = (static_cast<double>((static_cast<double>(static_cast<float>(1.055)) * static_cast<double>(glsl::pow(linear[static_cast<std::size_t>(i)], static_cast<float>(0.4166666567325592))))) - static_cast<double>(static_cast<float>(0.055)));
    }
  }
  return srgb;
}

[[nodiscard]] glsl::Vec3 linear_srgb_from_oklab([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 c) noexcept {
  const glsl::Mat3 fwdA = glsl::Mat3(glsl::Vec3(static_cast<float>(1.0), static_cast<float>(1.0), static_cast<float>(1.0)), glsl::Vec3(static_cast<float>(0.3963377774), static_cast<float>(-0.10556134581565857), static_cast<float>(-0.08948417752981186)), glsl::Vec3(static_cast<float>(0.2158037573), static_cast<float>(-0.0638541728258133), static_cast<float>(-1.2914855480194092)));
  const glsl::Mat3 fwdB = glsl::Mat3(glsl::Vec3(static_cast<float>(4.0767245293), static_cast<float>(-1.2681437730789185), static_cast<float>(-0.004111988469958305)), glsl::Vec3(static_cast<float>(-3.3072168827056885), static_cast<float>(2.6093323231), static_cast<float>(-0.7034763097763062)), glsl::Vec3(static_cast<float>(0.2307590544), static_cast<float>(-0.3411344289779663), static_cast<float>(1.7068625689)));
  [[maybe_unused]] glsl::Vec3 lms = (fwdA * c);
  return (fwdB * ((lms * lms) * lms));
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] double offsets([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept {
  return glsl::distance(st, glsl::FloatExpr<2>(static_cast<float>(0.5)));
}

[[nodiscard]] glsl::Vec3 oklab_from_linear_srgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 c) noexcept {
  const glsl::Mat3 invB = glsl::Mat3(glsl::Vec3(static_cast<float>(0.4121656120), static_cast<float>(0.2118591070), static_cast<float>(0.0883097947)), glsl::Vec3(static_cast<float>(0.5362752080), static_cast<float>(0.6807189584), static_cast<float>(0.2818474174)), glsl::Vec3(static_cast<float>(0.0514575653), static_cast<float>(0.1074065790), static_cast<float>(0.6302613616)));
  const glsl::Mat3 invA = glsl::Mat3(glsl::Vec3(static_cast<float>(0.2104542553), static_cast<float>(1.9779984951), static_cast<float>(0.0259040371)), glsl::Vec3(static_cast<float>(0.7936177850), static_cast<float>(-2.4285922050476074), static_cast<float>(0.7827717662)), glsl::Vec3(static_cast<float>(-0.004072046838700771), static_cast<float>(0.4505937099), static_cast<float>(-0.8086757659912109)));
  [[maybe_unused]] glsl::Vec3 lms = (invB * c);
  return (invA * glsl::Vec3((glsl::sign(lms) * glsl::pow(glsl::abs(lms), glsl::FloatExpr<3>(static_cast<float>(0.3333333333333))))));
}

[[nodiscard]] glsl::Vec3 pal([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double t) noexcept {
  t = (static_cast<double>((static_cast<double>(t) * static_cast<double>(state.repeatPalette))) + static_cast<double>((static_cast<double>(state.rotatePalette) * static_cast<double>(static_cast<float>(0.01)))));
  glsl::Vec3 color{};
  for (int lane = 0; lane < 3; ++lane) {
    const float argument = noisemaker::f32(static_cast<double>(noisemaker::f32(6.28318)) * ((state.paletteFreq[lane] * t) + state.palettePhase[lane]));
    const float cosine = glsl::cos(static_cast<double>(argument));
    const float product = noisemaker::f32(state.paletteAmp[lane] * static_cast<double>(cosine));
    color[lane] = noisemaker::f32(state.paletteOffset[lane] + static_cast<double>(product));
  }
  if (state.paletteMode == std::int32_t(1)) {
    color = glsl::Vec3(hsv2rgb(state, context, color));
  } else {
    if (state.paletteMode == std::int32_t(2)) {
      glsl::set_swizzle<1>(color, (static_cast<double>((static_cast<double>(glsl::swizzle<1>(color)) * static_cast<double>(static_cast<float>(-0.5090000033378601)))) + static_cast<double>(static_cast<float>(.276))));
      glsl::set_swizzle<2>(color, (static_cast<double>((static_cast<double>(glsl::swizzle<2>(color)) * static_cast<double>(static_cast<float>(-0.5090000033378601)))) + static_cast<double>(static_cast<float>(.198))));
      color = glsl::Vec3(linear_srgb_from_oklab(state, context, color));
      color = glsl::Vec3(linearToSrgb(state, context, glsl::swizzle<0, 1, 2>(color)));
    }
  }
  return color;
}

[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec3 v) noexcept {
  v = ((v * std::uint32_t(std::int32_t(1664525))) + std::uint32_t(std::int32_t(1013904223)));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  v = glsl::bitwise_xor(v, glsl::shift_right(v, std::uint32_t(std::int32_t(16))));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  return v;
}

[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double p) noexcept {
  [[maybe_unused]] double x = (static_cast<double>(static_cast<float>(6.28318530718)) * static_cast<double>(p));
  [[maybe_unused]] double func = glsl::sin(x);
  return map(state, context, func, static_cast<float>(-1.0), static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] glsl::Vec3 posterize([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] double lev) noexcept {
  if (lev == static_cast<float>(0.0)) {
    return color;
  } else {
    if (lev == static_cast<float>(1.0)) {
      lev = static_cast<float>(2.0);
    }
  }
  [[maybe_unused]] double gamma = static_cast<float>(0.65);
  color = glsl::Vec3(glsl::pow(color, glsl::FloatExpr<3>(gamma)));
  color = glsl::Vec3(glsl::Vec3((glsl::floor((color * lev)) / lev)));
  color = glsl::Vec3(glsl::pow(color, glsl::FloatExpr<3>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(gamma)))));
  return color;
}

[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 p) noexcept {
  return glsl::FloatExpr<3>(glsl::Vec3((glsl::Vec3(pcg(state, context, glsl::UVec3(p))) / float(std::uint32_t(std::int32_t(-1))))));
}

[[nodiscard]] double random([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 st) noexcept {
  return glsl::swizzle<0>(prng(state, context, glsl::Vec3(st, static_cast<float>(1.0))));
}

[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] double r = glsl::swizzle<0>(rgb);
  [[maybe_unused]] double g = glsl::swizzle<1>(rgb);
  [[maybe_unused]] double b = glsl::swizzle<2>(rgb);
  [[maybe_unused]] double max = glsl::component_max(r, glsl::component_max(g, b));
  [[maybe_unused]] double min = glsl::component_min(r, glsl::component_min(g, b));
  [[maybe_unused]] double delta = (static_cast<double>(max) - static_cast<double>(min));
  [[maybe_unused]] double h = static_cast<float>(0.0);
  if (delta != static_cast<float>(0.0)) {
    if (max == r) {
      h = (static_cast<double>(glsl::mod((static_cast<double>((static_cast<double>(g) - static_cast<double>(b))) / static_cast<double>(delta)), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0)));
    } else {
      if (max == g) {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(b) - static_cast<double>(r))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(2.0)))) / static_cast<double>(static_cast<float>(6.0)));
      } else {
        if (max == b) {
          h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(r) - static_cast<double>(g))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(4.0)))) / static_cast<double>(static_cast<float>(6.0)));
        }
      }
    }
  }
  [[maybe_unused]] double s = ((max == static_cast<float>(0.0)) ? static_cast<float>(0.0) : (static_cast<double>(delta) / static_cast<double>(max)));
  [[maybe_unused]] double v = max;
  return glsl::FloatExpr<3>(h, s, v);
}

[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double sat = map(state, context, state.saturation, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(-1.0), static_cast<float>(1.0));
  [[maybe_unused]] double avg = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(color)) + static_cast<double>(glsl::swizzle<1>(color)))) + static_cast<double>(glsl::swizzle<2>(color)))) / static_cast<double>(static_cast<float>(3.0)));
  color = glsl::Vec3((color - ((avg - color) * sat)));
  return color;
}

[[nodiscard]] glsl::Vec3 srgbToLinear([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 srgb) noexcept {
  [[maybe_unused]] glsl::Vec3 linear = {};
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(3)); ++i) {
    if (srgb[static_cast<std::size_t>(i)] <= static_cast<float>(0.04045)) {
      linear[static_cast<std::size_t>(i)] = (static_cast<double>(srgb[static_cast<std::size_t>(i)]) / static_cast<double>(static_cast<float>(12.92)));
    } else {
      linear[static_cast<std::size_t>(i)] = glsl::pow((static_cast<double>((static_cast<double>(srgb[static_cast<std::size_t>(i)]) + static_cast<double>(static_cast<float>(0.055)))) / static_cast<double>(static_cast<float>(1.055))), static_cast<float>(2.4));
    }
  }
  return linear;
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0));
  [[maybe_unused]] double blendy = periodicFunction(state, context, (static_cast<double>(state.time) - static_cast<double>(offsets(state, context, uv))));
  color = glsl::Vec4(sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex)))));
  if (state.levels != static_cast<float>(0.0)) {
    glsl::set_swizzle<0, 1, 2>(color, posterize(state, context, glsl::swizzle<0, 1, 2>(color), state.levels));
  }
  [[maybe_unused]] double bright = rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color))[static_cast<std::size_t>(std::int32_t(2))];
  if (state.dither == std::int32_t(1)) {
    glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * glsl::FloatExpr<3>(glsl::step(static_cast<float>(0.5), bright))));
  } else {
    if (state.dither == std::int32_t(2)) {
      glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * glsl::FloatExpr<3>(glsl::step(random(state, context, globalCoord), bright))));
    } else {
      if (state.dither == std::int32_t(3)) {
        glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * glsl::FloatExpr<3>(glsl::step(periodicFunction(state, context, (static_cast<double>(random(state, context, globalCoord)) + static_cast<double>(state.time))), bright))));
      } else {
        if (state.dither == std::int32_t(4)) {
          [[maybe_unused]] glsl::Vec2 coord = glsl::Vec2((glsl::swizzle<0, 1>(glsl::mod((globalCoord / state.renderScale), static_cast<float>(4.0))) - static_cast<float>(0.5)));
          if (bright < static_cast<float>(0.12)) {
            glsl::set_swizzle<0, 1, 2>(color, glsl::FloatExpr<3>(static_cast<float>(0.0)));
          } else {
            if (bright < static_cast<float>(0.24)) {
              glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * (historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(1.0)))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))))));
            } else {
              if (bright < static_cast<float>(0.36)) {
                glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * ((historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(1.0)))) || historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(3.0))))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))))));
              } else {
                if (bright < static_cast<float>(0.48)) {
                  glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * ((((glsl::swizzle<0>(coord) == static_cast<float>(1.0)) || (glsl::swizzle<0>(coord) == static_cast<float>(3.0))) && ((glsl::swizzle<1>(coord) == static_cast<float>(1.0)) || (glsl::swizzle<1>(coord) == static_cast<float>(3.0)))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))))));
                } else {
                  if (bright < static_cast<float>(0.60)) {
                    glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * ((((glsl::swizzle<0>(coord) == static_cast<float>(1.0)) || (glsl::swizzle<0>(coord) == static_cast<float>(3.0))) && ((glsl::swizzle<1>(coord) == static_cast<float>(1.0)) || (glsl::swizzle<1>(coord) == static_cast<float>(3.0)))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))))));
                  } else {
                    if (bright < static_cast<float>(0.72)) {
                      glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * ((historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(1.0)))) || historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(3.0))))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))))));
                    } else {
                      if (bright < static_cast<float>(0.84)) {
                        glsl::set_swizzle<0, 1, 2>(color, (glsl::swizzle<0, 1, 2>(color) * (historical_truthy_vector_equality(glsl::Vec2(glsl::swizzle<0, 1>(coord)), glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(1.0)))) ? glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0))) : glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0))))));
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  if (state.colorMode == std::int32_t(0)) {
    glsl::set_swizzle<0, 1, 2>(color, glsl::FloatExpr<3>(glsl::swizzle<2>(rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color)))));
  } else {
    if (state.colorMode == std::int32_t(1)) {
      glsl::set_swizzle<0, 1, 2>(color, srgbToLinear(state, context, glsl::swizzle<0, 1, 2>(color)));
    } else {
      if (state.colorMode == std::int32_t(3)) {
        glsl::set_swizzle<1>(color, (static_cast<double>((static_cast<double>(glsl::swizzle<1>(color)) * static_cast<double>(static_cast<float>(-0.5090000033378601)))) + static_cast<double>(static_cast<float>(.276))));
        glsl::set_swizzle<2>(color, (static_cast<double>((static_cast<double>(glsl::swizzle<2>(color)) * static_cast<double>(static_cast<float>(-0.5090000033378601)))) + static_cast<double>(static_cast<float>(.198))));
        glsl::set_swizzle<0, 1, 2>(color, linear_srgb_from_oklab(state, context, glsl::swizzle<0, 1, 2>(color)));
        glsl::set_swizzle<0, 1, 2>(color, linearToSrgb(state, context, glsl::swizzle<0, 1, 2>(color)));
      } else {
        if (state.colorMode == std::int32_t(4)) {
          [[maybe_unused]] double d = glsl::swizzle<2>(rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color)));
          if (state.cyclePalette == (-std::int32_t(1))) {
            d = (d + state.time);
          } else {
            if (state.cyclePalette == std::int32_t(1)) {
              d = (d - state.time);
            }
          }
          glsl::set_swizzle<0, 1, 2>(color, pal(state, context, d));
        }
      }
    }
  }
  [[maybe_unused]] glsl::Vec3 hsv = rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color));
  hsv[static_cast<std::size_t>(std::int32_t(0))] = glsl::mod((static_cast<double>((static_cast<double>(hsv[static_cast<std::size_t>(std::int32_t(0))]) * static_cast<double>(map(state, context, state.hueRange, static_cast<float>(0.0), static_cast<float>(200.0), static_cast<float>(0.0), static_cast<float>(2.0))))) + static_cast<double>((static_cast<double>(state.hueRotation) / static_cast<double>(static_cast<float>(360.0))))), static_cast<float>(1.0));
  glsl::set_swizzle<0, 1, 2>(color, hsv2rgb(state, context, hsv));
  if (state.invert) {
    glsl::set_swizzle<0, 1, 2>(color, (static_cast<float>(1.0) - glsl::swizzle<0, 1, 2>(color)));
  }
  glsl::set_swizzle<0, 1, 2>(color, brightnessContrast(state, context, glsl::swizzle<0, 1, 2>(color)));
  glsl::set_swizzle<0, 1, 2>(color, saturate(state, context, glsl::swizzle<0, 1, 2>(color)));
  output = glsl::Vec4(color);
}
}  // namespace typed_5

BoundKernel bind_classicNoisedeck_colorLab_colorLab(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_5::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("renderScale"), bindings.get_number("time"), bindings.get_number("levels"), bindings.get<std::int32_t>("dither"), bindings.get_number("hueRotation"), bindings.get_number("hueRange"), bindings.get<bool>("invert"), bindings.get_number("brightness"), bindings.get_number("contrast"), bindings.get_number("saturation"), bindings.get<std::int32_t>("colorMode"), bindings.get<std::int32_t>("paletteMode"), bindings.get<glsl::DVec3>("paletteOffset"), bindings.get<glsl::DVec3>("paletteAmp"), bindings.get<glsl::DVec3>("paletteFreq"), bindings.get<glsl::DVec3>("palettePhase"), bindings.get<std::int32_t>("cyclePalette"), bindings.get_number("rotatePalette"), bindings.get_number("repeatPalette"));
  (void)bindings;
  return BoundKernel(state, &typed_5::pixel);
}
// Typed IR program: classicNoisedeck/effects:effects
// Source SHA-256: e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c
namespace typed_7 {
using Kernel9 = std::array<double, 9>;
using Offsets9 = std::array<glsl::Vec2, 9>;
static_assert(sizeof(Kernel9) == 72U);
static_assert(sizeof(Offsets9) == 72U);

struct Frame final {
  Kernel9 emboss{};  // JS: 0 (double, narrowing=none)
  Kernel9 sharpen{};  // JS: 0 (double, narrowing=none)
  Kernel9 blur{};  // JS: 0 (double, narrowing=none)
  Kernel9 edge{};  // JS: 0 (double, narrowing=none)
  Kernel9 edge2{};  // JS: 0 (double, narrowing=none)
  Kernel9 edge3{};  // JS: 0 (double, narrowing=none)
  Kernel9 sharpenBlur{};  // JS: 0 (double, narrowing=none)
};

struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double renderScale_value, double time_value, double effectAmt_value, double scaleAmt_value, double rotation_value, double offsetX_value, double offsetY_value, double intensity_value, double saturation_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), renderScale(renderScale_value), time(time_value), effectAmt(effectAmt_value), scaleAmt(scaleAmt_value), rotation(rotation_value), offsetX(offsetX_value), offsetY(offsetY_value), intensity(intensity_value), saturation(saturation_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double renderScale;
  double time;
  double effectAmt;
  double scaleAmt;
  double rotation;
  double offsetX;
  double offsetY;
  double intensity;
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

[[nodiscard]] double bicubic([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 p) noexcept;
[[nodiscard]] glsl::Vec3 bloom([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 brightnessContrast([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] glsl::Vec3 cga([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec4 color, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 convolutionEffect([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec3 convolve([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] const Kernel9& kernel, [[maybe_unused]] bool divide) noexcept;
[[nodiscard]] glsl::Vec3 derivatives([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept;
[[nodiscard]] glsl::Vec3 desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] double f([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
void loadKernels([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, Frame& frame) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] double offsets([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept;
[[nodiscard]] glsl::Vec3 outline([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::UVec3 v) noexcept;
[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] double p) noexcept;
[[nodiscard]] glsl::Vec3 pixellate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double size) noexcept;
[[nodiscard]] glsl::Vec3 posterize([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] double lev) noexcept;
[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 p) noexcept;
[[nodiscard]] double random([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 p) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 rgb) noexcept;
[[nodiscard]] glsl::Vec2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double rot) noexcept;
[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] glsl::Vec3 shadow([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec3 sobel([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec3 subpixel([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double scale) noexcept;
[[nodiscard]] glsl::Vec3 zoomBlur([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept;

[[nodiscard]] double bicubic([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 p) noexcept {
  [[maybe_unused]] double x = glsl::swizzle<0>(p);
  [[maybe_unused]] double y = glsl::swizzle<1>(p);
  [[maybe_unused]] double x1 = glsl::floor(x);
  [[maybe_unused]] double y1 = glsl::floor(y);
  [[maybe_unused]] double x2 = (static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.)));
  [[maybe_unused]] double y2 = (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)));
  [[maybe_unused]] double f11 = f(state, context, frame, glsl::FloatExpr<2>(x1, y1));
  [[maybe_unused]] double f12 = f(state, context, frame, glsl::FloatExpr<2>(x1, y2));
  [[maybe_unused]] double f21 = f(state, context, frame, glsl::FloatExpr<2>(x2, y1));
  [[maybe_unused]] double f22 = f(state, context, frame, glsl::FloatExpr<2>(x2, y2));
  [[maybe_unused]] double f11x = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), y1))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), y1))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f12x = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), y2))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), y2))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f21x = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), y1))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), y1))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f22x = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), y2))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), y2))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f11y = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x1, (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x1, (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f12y = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x1, (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x1, (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f21y = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x2, (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x2, (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f22y = (static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x2, (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>(x2, (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(2.)));
  [[maybe_unused]] double f11xy = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))))) + static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(4.)));
  [[maybe_unused]] double f12xy = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))))) + static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x1) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(4.)));
  [[maybe_unused]] double f21xy = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) + static_cast<double>(static_cast<float>(1.)))))))) + static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y1) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(4.)));
  [[maybe_unused]] double f22xy = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) + static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) - static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) + static_cast<double>(static_cast<float>(1.)))))))) + static_cast<double>(f(state, context, frame, glsl::FloatExpr<2>((static_cast<double>(x2) - static_cast<double>(static_cast<float>(1.))), (static_cast<double>(y2) - static_cast<double>(static_cast<float>(1.)))))))) / static_cast<double>(static_cast<float>(4.)));
  [[maybe_unused]] glsl::Mat4 Q = glsl::Mat4(glsl::Vec4(f11, f21, f11x, f21x), glsl::Vec4(f12, f22, f12x, f22x), glsl::Vec4(f11y, f21y, f11xy, f21xy), glsl::Vec4(f12y, f22y, f12xy, f22xy));
  [[maybe_unused]] glsl::Mat4 S = glsl::Mat4(glsl::Vec4(static_cast<float>(1.), static_cast<float>(0.), static_cast<float>(0.), static_cast<float>(0.)), glsl::Vec4(static_cast<float>(0.), static_cast<float>(0.), static_cast<float>(1.), static_cast<float>(0.)), glsl::Vec4(static_cast<float>(-3.0), static_cast<float>(3.), static_cast<float>(-2.0), static_cast<float>(-1.0)), glsl::Vec4(static_cast<float>(2.), static_cast<float>(-2.0), static_cast<float>(1.), static_cast<float>(1.)));
  [[maybe_unused]] glsl::Mat4 T = glsl::Mat4(glsl::Vec4(static_cast<float>(1.), static_cast<float>(0.), static_cast<float>(-3.0), static_cast<float>(2.)), glsl::Vec4(static_cast<float>(0.), static_cast<float>(0.), static_cast<float>(3.), static_cast<float>(-2.0)), glsl::Vec4(static_cast<float>(0.), static_cast<float>(1.), static_cast<float>(-2.0), static_cast<float>(1.)), glsl::Vec4(static_cast<float>(0.), static_cast<float>(0.), static_cast<float>(-1.0), static_cast<float>(1.)));
  [[maybe_unused]] glsl::Mat4 A = ((T * Q) * S);
  [[maybe_unused]] double t = glsl::fract(glsl::swizzle<0>(p));
  [[maybe_unused]] double u = glsl::fract(glsl::swizzle<1>(p));
  [[maybe_unused]] glsl::Vec4 tv = glsl::FloatExpr<4>(static_cast<float>(1.), t, (static_cast<double>(t) * static_cast<double>(t)), (static_cast<double>((static_cast<double>(t) * static_cast<double>(t))) * static_cast<double>(t)));
  [[maybe_unused]] glsl::Vec4 uv = glsl::FloatExpr<4>(static_cast<float>(1.), u, (static_cast<double>(u) * static_cast<double>(u)), (static_cast<double>((static_cast<double>(u) * static_cast<double>(u))) * static_cast<double>(u)));
  return glsl::dot((tv * A), uv);
}

[[nodiscard]] glsl::Vec3 bloom([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept {
  [[maybe_unused]] glsl::Vec3 sum = glsl::FloatExpr<3>(static_cast<float>(0.0));
  [[maybe_unused]] glsl::Vec3 color = glsl::FloatExpr<3>(static_cast<float>(0.0));
  [[maybe_unused]] glsl::Vec3 orig = glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, st));
  [[maybe_unused]] double strength = map(state, context, frame, state.effectAmt, static_cast<float>(0.0), static_cast<float>(20.0), static_cast<float>(0.0), static_cast<float>(0.25));
  for ([[maybe_unused]] std::int32_t i = (-std::int32_t(4)); (i < std::int32_t(4)); ++i) {
    for ([[maybe_unused]] std::int32_t j = (-std::int32_t(3)); (j < std::int32_t(3)); ++j) {
      sum = glsl::Vec3((sum + glsl::Vec3((glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, (st + (glsl::Vec2(j, i) * static_cast<float>(0.004))))) * strength))));
    }
  }
  if (glsl::swizzle<0>(orig) < static_cast<float>(0.3)) {
    color = glsl::Vec3((((sum * sum) * static_cast<float>(0.012)) + orig));
  } else {
    if (glsl::swizzle<0>(orig) < static_cast<float>(0.5)) {
      color = glsl::Vec3((((sum * sum) * static_cast<float>(0.009)) + orig));
    } else {
      color = glsl::Vec3((((sum * sum) * static_cast<float>(0.0075)) + orig));
    }
  }
  color = glsl::Vec3(glsl::clamp(color, static_cast<float>(0.0), static_cast<float>(1.0)));
  return color;
}

[[nodiscard]] glsl::Vec3 brightnessContrast([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double bright = map(state, context, frame, state.intensity, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(-0.4000000059604645), static_cast<float>(0.4));
  [[maybe_unused]] double cont = static_cast<float>(1.0);
  if (state.intensity < static_cast<float>(0.0)) {
    cont = map(state, context, frame, state.intensity, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(0.5), static_cast<float>(1.0));
  } else {
    cont = map(state, context, frame, state.intensity, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(1.0), static_cast<float>(1.5));
  }
  color = glsl::Vec3(((((color - static_cast<float>(0.5)) * cont) + static_cast<float>(0.5)) + bright));
  return color;
}

[[nodiscard]] glsl::Vec3 cga([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec4 color, [[maybe_unused]] glsl::Vec2 st) noexcept {
  [[maybe_unused]] double amt = map(state, context, frame, state.effectAmt, static_cast<float>(0.0), static_cast<float>(20.0), static_cast<float>(0.0), static_cast<float>(5.0));
  if (amt < static_cast<float>(0.01)) {
    return glsl::swizzle<0, 1, 2>(color);
  }
  [[maybe_unused]] double pixelDensity = (static_cast<double>(amt) * static_cast<double>(state.renderScale));
  [[maybe_unused]] double size = (static_cast<double>(static_cast<float>(2.)) * static_cast<double>(pixelDensity));
  [[maybe_unused]] double dSize = (static_cast<double>(static_cast<float>(2.)) * static_cast<double>(size));
  [[maybe_unused]] double amount = (static_cast<double>(glsl::swizzle<0>(state.resolution)) / static_cast<double>(size));
  [[maybe_unused]] double d = (static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(amount));
  [[maybe_unused]] double ar = (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)));
  [[maybe_unused]] double sx = (static_cast<double>(glsl::floor((static_cast<double>(glsl::swizzle<0>(st)) / static_cast<double>(d)))) * static_cast<double>(d));
  d = (static_cast<double>(ar) / static_cast<double>(amount));
  [[maybe_unused]] double sy = (static_cast<double>(glsl::floor((static_cast<double>(glsl::swizzle<1>(st)) / static_cast<double>(d)))) * static_cast<double>(d));
  [[maybe_unused]] glsl::Vec4 base = sample_texture(*state.inputTex, glsl::FloatExpr<2>(sx, sy));
  [[maybe_unused]] double lum = (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(.2126)) * static_cast<double>(glsl::swizzle<0>(base)))) + static_cast<double>((static_cast<double>(static_cast<float>(.7152)) * static_cast<double>(glsl::swizzle<1>(base)))))) + static_cast<double>((static_cast<double>(static_cast<float>(.0722)) * static_cast<double>(glsl::swizzle<2>(base)))));
  [[maybe_unused]] double o = glsl::floor((static_cast<double>(static_cast<float>(6.)) * static_cast<double>(lum)));
  [[maybe_unused]] glsl::Vec3 c1 = {};
  [[maybe_unused]] glsl::Vec3 c2 = {};
  [[maybe_unused]] glsl::Vec3 black = glsl::FloatExpr<3>(static_cast<float>(0.));
  [[maybe_unused]] glsl::Vec3 light = (glsl::FloatExpr<3>(static_cast<float>(85.), static_cast<float>(255.), static_cast<float>(255.)) / static_cast<float>(255.));
  [[maybe_unused]] glsl::Vec3 dark = (glsl::FloatExpr<3>(static_cast<float>(254.), static_cast<float>(84.), static_cast<float>(255.)) / static_cast<float>(255.));
  [[maybe_unused]] glsl::Vec3 white = glsl::FloatExpr<3>(static_cast<float>(1.));
  if (o == static_cast<float>(0.)) {
    c1 = glsl::Vec3(black);
    c2 = glsl::Vec3(c1);
  }
  if (o == static_cast<float>(1.)) {
    c1 = glsl::Vec3(black);
    c2 = glsl::Vec3(dark);
  }
  if (o == static_cast<float>(2.)) {
    c1 = glsl::Vec3(dark);
    c2 = glsl::Vec3(c1);
  }
  if (o == static_cast<float>(3.)) {
    c1 = glsl::Vec3(dark);
    c2 = glsl::Vec3(light);
  }
  if (o == static_cast<float>(4.)) {
    c1 = glsl::Vec3(light);
    c2 = glsl::Vec3(c1);
  }
  if (o == static_cast<float>(5.)) {
    c1 = glsl::Vec3(light);
    c2 = glsl::Vec3(white);
  }
  if (o == static_cast<float>(6.)) {
    c1 = glsl::Vec3(white);
    c2 = glsl::Vec3(c1);
  }
  if (glsl::mod(glsl::swizzle<0>(context.frag_coord), dSize) > size) {
    if (glsl::mod(glsl::swizzle<1>(context.frag_coord), dSize) > size) {
      glsl::set_swizzle<0, 1, 2>(base, c1);
    } else {
      glsl::set_swizzle<0, 1, 2>(base, c2);
    }
  } else {
    if (glsl::mod(glsl::swizzle<1>(context.frag_coord), dSize) > size) {
      glsl::set_swizzle<0, 1, 2>(base, c2);
    } else {
      glsl::set_swizzle<0, 1, 2>(base, c1);
    }
  }
  return glsl::swizzle<0, 1, 2>(base);
}

[[nodiscard]] glsl::Vec3 convolutionEffect([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  return color;
}

[[nodiscard]] glsl::Vec3 convolve([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] const Kernel9& kernel, [[maybe_unused]] bool divide) noexcept {
  [[maybe_unused]] glsl::Vec2 steps = (static_cast<float>(1.0) / state.resolution);
  [[maybe_unused]] Offsets9 offset{};
  offset[0] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), (-glsl::swizzle<1>(steps))));
  offset[1] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), (-glsl::swizzle<1>(steps))));
  offset[2] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), (-glsl::swizzle<1>(steps))));
  offset[3] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), static_cast<float>(0.0)));
  offset[4] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), static_cast<float>(0.0)));
  offset[5] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), static_cast<float>(0.0)));
  offset[6] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), glsl::swizzle<1>(steps)));
  offset[7] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), glsl::swizzle<1>(steps)));
  offset[8] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), glsl::swizzle<1>(steps)));
  [[maybe_unused]] double kernelWeight = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec3 conv = glsl::FloatExpr<3>(static_cast<float>(0.0));
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(9)); ++i) {
    [[maybe_unused]] glsl::Vec3 color = glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, ((((uv + (offset[static_cast<std::size_t>(i)] * state.effectAmt)) * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)))));
    conv = glsl::Vec3((conv + (color * kernel[static_cast<std::size_t>(i)])));
    kernelWeight = (kernelWeight + kernel[static_cast<std::size_t>(i)]);
  }
  if (divide) {
    glsl::set_swizzle<0, 1, 2>(conv, (glsl::swizzle<0, 1, 2>(conv) / kernelWeight));
  }
  return glsl::clamp(glsl::swizzle<0, 1, 2>(conv), static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] glsl::Vec3 derivatives([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept {
  [[maybe_unused]] glsl::Vec3 dcolor = desaturate(state, context, frame, color);
  [[maybe_unused]] Kernel9 deriv_x{};
  deriv_x[0] = static_cast<float>(0.0);
  deriv_x[1] = static_cast<float>(0.0);
  deriv_x[2] = static_cast<float>(0.0);
  deriv_x[3] = static_cast<float>(0.0);
  deriv_x[4] = static_cast<float>(1.0);
  deriv_x[5] = static_cast<float>(-1.0);
  deriv_x[6] = static_cast<float>(0.0);
  deriv_x[7] = static_cast<float>(0.0);
  deriv_x[8] = static_cast<float>(0.0);
  [[maybe_unused]] Kernel9 deriv_y{};
  deriv_y[0] = static_cast<float>(0.0);
  deriv_y[1] = static_cast<float>(0.0);
  deriv_y[2] = static_cast<float>(0.0);
  deriv_y[3] = static_cast<float>(0.0);
  deriv_y[4] = static_cast<float>(1.0);
  deriv_y[5] = static_cast<float>(0.0);
  deriv_y[6] = static_cast<float>(0.0);
  deriv_y[7] = static_cast<float>(-1.0);
  deriv_y[8] = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec3 s1 = convolve(state, context, frame, uv, deriv_x, divide);
  [[maybe_unused]] glsl::Vec3 s2 = convolve(state, context, frame, uv, deriv_y, divide);
  [[maybe_unused]] double dist = glsl::distance(s1, s2);
  return (color = glsl::Vec3(color * dist));
}

[[nodiscard]] glsl::Vec3 desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double avg = (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.2126)) * static_cast<double>(glsl::swizzle<0>(color)))) + static_cast<double>((static_cast<double>(static_cast<float>(0.7152)) * static_cast<double>(glsl::swizzle<1>(color)))))) + static_cast<double>((static_cast<double>(static_cast<float>(0.0722)) * static_cast<double>(glsl::swizzle<2>(color)))));
  return glsl::FloatExpr<3>(avg);
}

[[nodiscard]] double f([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept {
  return random(state, context, frame, glsl::floor(st));
}

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] double h = glsl::fract(glsl::swizzle<0>(hsv));
  [[maybe_unused]] double s = glsl::swizzle<1>(hsv);
  [[maybe_unused]] double v = glsl::swizzle<2>(hsv);
  [[maybe_unused]] double c = (static_cast<double>(v) * static_cast<double>(s));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(h) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(v) - static_cast<double>(c));
  [[maybe_unused]] glsl::Vec3 rgb = {};
  if ((static_cast<float>(0.0) <= h) && (h < static_cast<float>(0.1666666716337204))) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if ((static_cast<float>(0.1666666716337204) <= h) && (h < static_cast<float>(0.3333333432674408))) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if ((static_cast<float>(0.3333333432674408) <= h) && (h < static_cast<float>(0.5))) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if ((static_cast<float>(0.5) <= h) && (h < static_cast<float>(0.6666666865348816))) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if ((static_cast<float>(0.6666666865348816) <= h) && (h < static_cast<float>(0.8333333134651184))) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            if ((static_cast<float>(0.8333333134651184) <= h) && (h < static_cast<float>(1.0))) {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
            } else {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(0.0)));
            }
          }
        }
      }
    }
  }
  return (rgb + glsl::FloatExpr<3>(m, m, m));
}

void loadKernels([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, Frame& frame) noexcept {
  frame.emboss[0] = static_cast<float>(-2.0);
  frame.emboss[1] = static_cast<float>(-1.0);
  frame.emboss[2] = static_cast<float>(0.0);
  frame.emboss[3] = static_cast<float>(-1.0);
  frame.emboss[4] = static_cast<float>(1.0);
  frame.emboss[5] = static_cast<float>(1.0);
  frame.emboss[6] = static_cast<float>(0.0);
  frame.emboss[7] = static_cast<float>(1.0);
  frame.emboss[8] = static_cast<float>(2.0);
  frame.sharpen[0] = static_cast<float>(-1.0);
  frame.sharpen[1] = static_cast<float>(0.0);
  frame.sharpen[2] = static_cast<float>(-1.0);
  frame.sharpen[3] = static_cast<float>(0.0);
  frame.sharpen[4] = static_cast<float>(5.0);
  frame.sharpen[5] = static_cast<float>(0.0);
  frame.sharpen[6] = static_cast<float>(-1.0);
  frame.sharpen[7] = static_cast<float>(0.0);
  frame.sharpen[8] = static_cast<float>(-1.0);
  frame.blur[0] = static_cast<float>(1.0);
  frame.blur[1] = static_cast<float>(2.0);
  frame.blur[2] = static_cast<float>(1.0);
  frame.blur[3] = static_cast<float>(2.0);
  frame.blur[4] = static_cast<float>(4.0);
  frame.blur[5] = static_cast<float>(2.0);
  frame.blur[6] = static_cast<float>(1.0);
  frame.blur[7] = static_cast<float>(2.0);
  frame.blur[8] = static_cast<float>(1.0);
  frame.edge[0] = static_cast<float>(-1.0);
  frame.edge[1] = static_cast<float>(-1.0);
  frame.edge[2] = static_cast<float>(-1.0);
  frame.edge[3] = static_cast<float>(-1.0);
  frame.edge[4] = static_cast<float>(8.0);
  frame.edge[5] = static_cast<float>(-1.0);
  frame.edge[6] = static_cast<float>(-1.0);
  frame.edge[7] = static_cast<float>(-1.0);
  frame.edge[8] = static_cast<float>(-1.0);
  frame.edge2[0] = static_cast<float>(-1.0);
  frame.edge2[1] = static_cast<float>(0.0);
  frame.edge2[2] = static_cast<float>(-1.0);
  frame.edge2[3] = static_cast<float>(0.0);
  frame.edge2[4] = static_cast<float>(4.0);
  frame.edge2[5] = static_cast<float>(0.0);
  frame.edge2[6] = static_cast<float>(-1.0);
  frame.edge2[7] = static_cast<float>(0.0);
  frame.edge2[8] = static_cast<float>(-1.0);
  frame.edge3[0] = static_cast<float>(-0.875);
  frame.edge3[1] = static_cast<float>(-0.75);
  frame.edge3[2] = static_cast<float>(-0.875);
  frame.edge3[3] = static_cast<float>(-0.75);
  frame.edge3[4] = static_cast<float>(5.0);
  frame.edge3[5] = static_cast<float>(-0.75);
  frame.edge3[6] = static_cast<float>(-0.875);
  frame.edge3[7] = static_cast<float>(-0.75);
  frame.edge3[8] = static_cast<float>(-0.875);
  frame.sharpenBlur[0] = static_cast<float>(-2.0);
  frame.sharpenBlur[1] = static_cast<float>(2.0);
  frame.sharpenBlur[2] = static_cast<float>(-2.0);
  frame.sharpenBlur[3] = static_cast<float>(2.0);
  frame.sharpenBlur[4] = static_cast<float>(1.0);
  frame.sharpenBlur[5] = static_cast<float>(2.0);
  frame.sharpenBlur[6] = static_cast<float>(-2.0);
  frame.sharpenBlur[7] = static_cast<float>(2.0);
  frame.sharpenBlur[8] = static_cast<float>(-2.0);
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] double offsets([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept {
  return glsl::distance(st, glsl::FloatExpr<2>(static_cast<float>(0.5)));
}

[[nodiscard]] glsl::Vec3 outline([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] glsl::Vec3 dcolor = desaturate(state, context, frame, color);
  [[maybe_unused]] Kernel9 sobel_x{};
  sobel_x[0] = static_cast<float>(1.0);
  sobel_x[1] = static_cast<float>(0.0);
  sobel_x[2] = static_cast<float>(-1.0);
  sobel_x[3] = static_cast<float>(2.0);
  sobel_x[4] = static_cast<float>(0.0);
  sobel_x[5] = static_cast<float>(-2.0);
  sobel_x[6] = static_cast<float>(1.0);
  sobel_x[7] = static_cast<float>(0.0);
  sobel_x[8] = static_cast<float>(-1.0);
  [[maybe_unused]] Kernel9 sobel_y{};
  sobel_y[0] = static_cast<float>(1.0);
  sobel_y[1] = static_cast<float>(2.0);
  sobel_y[2] = static_cast<float>(1.0);
  sobel_y[3] = static_cast<float>(0.0);
  sobel_y[4] = static_cast<float>(0.0);
  sobel_y[5] = static_cast<float>(0.0);
  sobel_y[6] = static_cast<float>(-1.0);
  sobel_y[7] = static_cast<float>(-2.0);
  sobel_y[8] = static_cast<float>(-1.0);
  [[maybe_unused]] glsl::Vec3 s1 = convolve(state, context, frame, uv, sobel_x, false);
  [[maybe_unused]] glsl::Vec3 s2 = convolve(state, context, frame, uv, sobel_y, false);
  [[maybe_unused]] double dist = glsl::distance(s1, s2);
  [[maybe_unused]] glsl::Vec3 outcolor = (color - dist);
  return glsl::component_max(outcolor, static_cast<float>(0.0));
}

[[nodiscard]] glsl::UVec3 pcg([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::UVec3 v) noexcept {
  v = ((v * std::uint32_t(std::int32_t(1664525))) + std::uint32_t(std::int32_t(1013904223)));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  v = glsl::bitwise_xor(v, glsl::shift_right(v, std::uint32_t(std::int32_t(16))));
  glsl::set_swizzle<0>(v, (glsl::swizzle<0>(v) + (glsl::swizzle<1>(v) * glsl::swizzle<2>(v))));
  glsl::set_swizzle<1>(v, (glsl::swizzle<1>(v) + (glsl::swizzle<2>(v) * glsl::swizzle<0>(v))));
  glsl::set_swizzle<2>(v, (glsl::swizzle<2>(v) + (glsl::swizzle<0>(v) * glsl::swizzle<1>(v))));
  return v;
}

[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] double p) noexcept {
  return map(state, context, frame, glsl::sin((static_cast<double>(p) * static_cast<double>(static_cast<float>(6.28318530718)))), static_cast<float>(-1.0), static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] glsl::Vec3 pixellate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double size) noexcept {
  if (size < static_cast<float>(1.0)) {
    return glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex)))));
  }
  size = (size * static_cast<float>(4.0));
  [[maybe_unused]] double dx = (static_cast<double>(size) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(glsl::swizzle<0>(state.resolution)))));
  [[maybe_unused]] double dy = (static_cast<double>(size) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(glsl::swizzle<1>(state.resolution)))));
  uv = glsl::Vec2((uv - static_cast<float>(0.5)));
  [[maybe_unused]] glsl::Vec2 coord = glsl::FloatExpr<2>((static_cast<double>(dx) * static_cast<double>(glsl::floor((static_cast<double>(glsl::swizzle<0>(uv)) / static_cast<double>(dx))))), (static_cast<double>(dy) * static_cast<double>(glsl::floor((static_cast<double>(glsl::swizzle<1>(uv)) / static_cast<double>(dy))))));
  coord = glsl::Vec2((coord + static_cast<float>(0.5)));
  return glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, coord));
}

[[nodiscard]] glsl::Vec3 posterize([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] double lev) noexcept {
  if (lev == static_cast<float>(0.0)) {
    return color;
  } else {
    if (lev == static_cast<float>(1.0)) {
      return glsl::step(static_cast<float>(0.5), color);
    }
  }
  [[maybe_unused]] double gamma = static_cast<float>(0.65);
  color = glsl::Vec3(glsl::pow(color, glsl::FloatExpr<3>(gamma)));
  color = glsl::Vec3(glsl::Vec3((glsl::floor((color * lev)) / lev)));
  color = glsl::Vec3(glsl::pow(color, glsl::FloatExpr<3>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(gamma)))));
  return color;
}

[[nodiscard]] glsl::FloatExpr<3> prng([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 p) noexcept {
  return glsl::FloatExpr<3>(glsl::Vec3((glsl::Vec3(pcg(state, context, frame, glsl::UVec3(p))) / float(std::uint32_t(std::int32_t(-1))))));
}

[[nodiscard]] double random([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 p) noexcept {
  [[maybe_unused]] glsl::Vec3 p2 = glsl::Vec3(p, static_cast<float>(0.0));
  return (static_cast<double>(float(glsl::swizzle<0>(pcg(state, context, frame, glsl::UVec3(p2))))) / static_cast<double>(float(std::uint32_t(std::int32_t(-1)))));
}

[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] double r = glsl::swizzle<0>(rgb);
  [[maybe_unused]] double g = glsl::swizzle<1>(rgb);
  [[maybe_unused]] double b = glsl::swizzle<2>(rgb);
  [[maybe_unused]] double max = glsl::component_max(r, glsl::component_max(g, b));
  [[maybe_unused]] double min = glsl::component_min(r, glsl::component_min(g, b));
  [[maybe_unused]] double delta = (static_cast<double>(max) - static_cast<double>(min));
  [[maybe_unused]] double h = static_cast<float>(0.0);
  if (delta != static_cast<float>(0.0)) {
    if (max == r) {
      h = (static_cast<double>(glsl::mod((static_cast<double>((static_cast<double>(g) - static_cast<double>(b))) / static_cast<double>(delta)), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0)));
    } else {
      if (max == g) {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(b) - static_cast<double>(r))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(2.0)))) / static_cast<double>(static_cast<float>(6.0)));
      } else {
        if (max == b) {
          h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(r) - static_cast<double>(g))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(4.0)))) / static_cast<double>(static_cast<float>(6.0)));
        }
      }
    }
  }
  [[maybe_unused]] double s = ((max == static_cast<float>(0.0)) ? static_cast<float>(0.0) : (static_cast<double>(delta) / static_cast<double>(max)));
  [[maybe_unused]] double v = max;
  return glsl::FloatExpr<3>(h, s, v);
}

[[nodiscard]] glsl::Vec2 rotate2D([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double rot) noexcept {
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) * (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)))));
  rot = map(state, context, frame, rot, static_cast<float>(0.0), static_cast<float>(360.0), static_cast<float>(0.0), static_cast<float>(2.0));
  [[maybe_unused]] double angle = (static_cast<double>(rot) * static_cast<double>(static_cast<float>(3.14159265359)));
  st = glsl::Vec2((st - glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))), static_cast<float>(0.5))));
  st = glsl::Vec2((glsl::Mat2(glsl::Vec2(glsl::cos(angle), (-glsl::sin(angle))), glsl::Vec2(glsl::sin(angle), glsl::cos(angle))) * st));
  st = glsl::Vec2((st + glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))), static_cast<float>(0.5))));
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) / (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)))));
  return st;
}

[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double sat = map(state, context, frame, state.saturation, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(-1.0), static_cast<float>(1.0));
  [[maybe_unused]] double avg = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(color)) + static_cast<double>(glsl::swizzle<1>(color)))) + static_cast<double>(glsl::swizzle<2>(color)))) / static_cast<double>(static_cast<float>(3.0)));
  color = glsl::Vec3((color - ((avg - color) * sat)));
  return color;
}

[[nodiscard]] glsl::Vec3 shadow([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] Kernel9 sobel_x{};
  sobel_x[0] = static_cast<float>(1.0);
  sobel_x[1] = static_cast<float>(0.0);
  sobel_x[2] = static_cast<float>(-1.0);
  sobel_x[3] = static_cast<float>(2.0);
  sobel_x[4] = static_cast<float>(0.0);
  sobel_x[5] = static_cast<float>(-2.0);
  sobel_x[6] = static_cast<float>(1.0);
  sobel_x[7] = static_cast<float>(0.0);
  sobel_x[8] = static_cast<float>(-1.0);
  [[maybe_unused]] Kernel9 sobel_y{};
  sobel_y[0] = static_cast<float>(1.0);
  sobel_y[1] = static_cast<float>(2.0);
  sobel_y[2] = static_cast<float>(1.0);
  sobel_y[3] = static_cast<float>(0.0);
  sobel_y[4] = static_cast<float>(0.0);
  sobel_y[5] = static_cast<float>(0.0);
  sobel_y[6] = static_cast<float>(-1.0);
  sobel_y[7] = static_cast<float>(-2.0);
  sobel_y[8] = static_cast<float>(-1.0);
  color = glsl::Vec3(rgb2hsv(state, context, frame, color));
  [[maybe_unused]] glsl::Vec3 x = convolve(state, context, frame, uv, sobel_x, false);
  [[maybe_unused]] glsl::Vec3 y = convolve(state, context, frame, uv, sobel_y, false);
  [[maybe_unused]] double shade = glsl::distance(x, y);
  [[maybe_unused]] double highlight = (static_cast<double>(shade) * static_cast<double>(shade));
  shade = (static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::swizzle<2>(color)))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(highlight))))))) * static_cast<double>(shade));
  [[maybe_unused]] double alpha = static_cast<float>(0.75);
  color = glsl::Vec3(glsl::FloatExpr<3>(glsl::swizzle<0>(color), glsl::swizzle<1>(color), glsl::mix(glsl::swizzle<2>(color), shade, alpha)));
  return hsv2rgb(state, context, frame, color);
}

[[nodiscard]] glsl::Vec3 sobel([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  [[maybe_unused]] glsl::Vec3 dcolor = desaturate(state, context, frame, color);
  [[maybe_unused]] Kernel9 sobel_x{};
  sobel_x[0] = static_cast<float>(1.0);
  sobel_x[1] = static_cast<float>(0.0);
  sobel_x[2] = static_cast<float>(-1.0);
  sobel_x[3] = static_cast<float>(2.0);
  sobel_x[4] = static_cast<float>(0.0);
  sobel_x[5] = static_cast<float>(-2.0);
  sobel_x[6] = static_cast<float>(1.0);
  sobel_x[7] = static_cast<float>(0.0);
  sobel_x[8] = static_cast<float>(-1.0);
  [[maybe_unused]] Kernel9 sobel_y{};
  sobel_y[0] = static_cast<float>(1.0);
  sobel_y[1] = static_cast<float>(2.0);
  sobel_y[2] = static_cast<float>(1.0);
  sobel_y[3] = static_cast<float>(0.0);
  sobel_y[4] = static_cast<float>(0.0);
  sobel_y[5] = static_cast<float>(0.0);
  sobel_y[6] = static_cast<float>(-1.0);
  sobel_y[7] = static_cast<float>(-2.0);
  sobel_y[8] = static_cast<float>(-1.0);
  [[maybe_unused]] glsl::Vec3 s1 = convolve(state, context, frame, uv, sobel_x, false);
  [[maybe_unused]] glsl::Vec3 s2 = convolve(state, context, frame, uv, sobel_y, false);
  [[maybe_unused]] double dist = glsl::distance(s1, s2);
  return (color = glsl::Vec3(color * dist));
}

[[nodiscard]] glsl::Vec3 subpixel([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st, [[maybe_unused]] double scale) noexcept {
  scale = (static_cast<double>(map(state, context, frame, scale, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(10.0))) * static_cast<double>(state.renderScale));
  [[maybe_unused]] glsl::Vec3 orig = pixellate(state, context, frame, st, (static_cast<double>(static_cast<float>(4.0)) * static_cast<double>(scale)));
  [[maybe_unused]] glsl::Vec3& color = orig;
  st = glsl::Vec2((st * state.resolution));
  st = glsl::Vec2(glsl::floor(st));
  [[maybe_unused]] double m = glsl::mod(glsl::swizzle<0>(st), (static_cast<double>(static_cast<float>(4.0)) * static_cast<double>(scale)));
  if (glsl::mod(glsl::swizzle<1>(st), (static_cast<double>(static_cast<float>(4.0)) * static_cast<double>(scale))) <= (static_cast<double>(static_cast<float>(1.0)) * static_cast<double>(scale))) {
    color = glsl::Vec3((color * glsl::FloatExpr<3>(static_cast<float>(0.0))));
  } else {
    if (m <= (static_cast<double>(static_cast<float>(1.0)) * static_cast<double>(scale))) {
      color = glsl::Vec3((color * glsl::FloatExpr<3>(static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(0.0))));
    } else {
      if (m <= (static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(scale))) {
        color = glsl::Vec3((color * glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(1.0), static_cast<float>(0.0))));
      } else {
        if (m <= (static_cast<double>(static_cast<float>(3.0)) * static_cast<double>(scale))) {
          color = glsl::Vec3((color * glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0))));
        } else {
          color = glsl::Vec3((color * glsl::FloatExpr<3>(static_cast<float>(0.0))));
        }
      }
    }
  }
  [[maybe_unused]] double factor = glsl::clamp((static_cast<double>(scale) * static_cast<double>(static_cast<float>(0.25))), static_cast<float>(0.0), static_cast<float>(1.0));
  return glsl::mix(orig, color, factor);
}

[[nodiscard]] glsl::Vec3 zoomBlur([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] const Frame& frame, [[maybe_unused]] glsl::Vec2 st) noexcept {
  [[maybe_unused]] glsl::Vec3 color = glsl::FloatExpr<3>(static_cast<float>(0.0));
  [[maybe_unused]] double total = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec2 toCenter = glsl::Vec2((st - static_cast<float>(0.5)));
  [[maybe_unused]] double offset = glsl::swizzle<0>(prng(state, context, frame, glsl::FloatExpr<3>(static_cast<float>(12.9898), static_cast<float>(78.233), static_cast<float>(151.7182))));
  for ([[maybe_unused]] double t = static_cast<float>(0.0); (t <= static_cast<float>(40.0)); ++t) {
    [[maybe_unused]] double percent = (static_cast<double>((static_cast<double>(t) + static_cast<double>(offset))) / static_cast<double>(static_cast<float>(40.0)));
    [[maybe_unused]] double weight = (static_cast<double>(static_cast<float>(4.0)) * static_cast<double>((static_cast<double>(percent) - static_cast<double>((static_cast<double>(percent) * static_cast<double>(percent))))));
    [[maybe_unused]] double strength = map(state, context, frame, state.effectAmt, static_cast<float>(0.0), static_cast<float>(20.0), static_cast<float>(0.0), static_cast<float>(1.0));
    [[maybe_unused]] glsl::Vec4 tex = sample_texture(*state.inputTex, (st + ((toCenter * percent) * strength)));
    color = glsl::Vec3((color + (glsl::swizzle<0, 1, 2>(tex) * weight)));
    total = (total + weight);
  }
  color = glsl::Vec3((color / total));
  return color;
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  Frame frame{};
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0));
  [[maybe_unused]] double scale = (static_cast<double>(static_cast<float>(100.0)) / static_cast<double>(state.scaleAmt));
  if (scale == static_cast<float>(0.0)) {
    scale = static_cast<float>(1.0);
  }
  uv = glsl::Vec2(rotate2D(state, context, frame, uv, state.rotation));
  uv = glsl::Vec2((uv - static_cast<float>(0.5)));
  uv = glsl::Vec2((uv * scale));
  uv = glsl::Vec2((uv + static_cast<float>(0.5)));
  [[maybe_unused]] glsl::Vec2 imageSize = state.resolution;
  glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) - glsl::ceil((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(state.resolution)) / static_cast<double>(glsl::swizzle<0>(imageSize)))) * static_cast<double>(scale))) * static_cast<double>(static_cast<float>(0.5)))) - static_cast<double>((static_cast<double>(static_cast<float>(0.5)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(glsl::swizzle<0>(imageSize)))) * static_cast<double>(scale)))))))));
  glsl::set_swizzle<1>(uv, (glsl::swizzle<1>(uv) + glsl::ceil((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<1>(state.resolution)) / static_cast<double>(glsl::swizzle<1>(imageSize)))) * static_cast<double>(scale))) * static_cast<double>(static_cast<float>(0.5)))) + static_cast<double>((static_cast<double>(static_cast<float>(0.5)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(1.0)) / static_cast<double>(glsl::swizzle<1>(imageSize)))) * static_cast<double>(scale))))))) - static_cast<double>(scale)))));
  glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) - (static_cast<double>(map(state, context, frame, state.offsetX, static_cast<float>(-100.0), static_cast<float>(100.0), (static_cast<double>((static_cast<double>((-glsl::swizzle<0>(state.resolution))) / static_cast<double>(glsl::swizzle<0>(imageSize)))) * static_cast<double>(scale)), (static_cast<double>((static_cast<double>(glsl::swizzle<0>(state.resolution)) / static_cast<double>(glsl::swizzle<0>(imageSize)))) * static_cast<double>(scale)))) * static_cast<double>(static_cast<float>(1.5)))));
  glsl::set_swizzle<1>(uv, (glsl::swizzle<1>(uv) - (static_cast<double>(map(state, context, frame, state.offsetY, static_cast<float>(-100.0), static_cast<float>(100.0), (static_cast<double>((static_cast<double>((-glsl::swizzle<1>(state.resolution))) / static_cast<double>(glsl::swizzle<1>(imageSize)))) * static_cast<double>(scale)), (static_cast<double>((static_cast<double>(glsl::swizzle<1>(state.resolution)) / static_cast<double>(glsl::swizzle<1>(imageSize)))) * static_cast<double>(scale)))) * static_cast<double>(static_cast<float>(1.5)))));
  uv = glsl::Vec2(glsl::fract(uv));
  loadKernels(state, context, frame);
  [[maybe_unused]] double blendy = periodicFunction(state, context, frame, (static_cast<double>(state.time) - static_cast<double>(offsets(state, context, frame, uv))));
  [[maybe_unused]] glsl::Vec2& origUV = uv;
  [[maybe_unused]] glsl::Vec4 origcolor = sample_texture(*state.inputTex, (glsl::swizzle<0, 1>(context.frag_coord) / glsl::Vec2(texture_size(*state.inputTex))));
  color = glsl::Vec4(origcolor);
  glsl::set_swizzle<0, 1, 2>(color, brightnessContrast(state, context, frame, glsl::swizzle<0, 1, 2>(color)));
  glsl::set_swizzle<0, 1, 2>(color, saturate(state, context, frame, glsl::swizzle<0, 1, 2>(color)));
  output = glsl::Vec4(color);
}
}  // namespace typed_7

BoundKernel bind_classicNoisedeck_effects_effects(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_7::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("renderScale"), bindings.get_number("time"), bindings.get_number("effectAmt"), bindings.get_number("scaleAmt"), bindings.get_number("rotation"), bindings.get_number("offsetX"), bindings.get_number("offsetY"), bindings.get_number("intensity"), bindings.get_number("saturation"));
  (void)bindings;
  return BoundKernel(state, &typed_7::pixel);
}
// Typed IR program: classicNoisedeck/lensDistortion:lensDistortion
// Source SHA-256: f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444
namespace typed_11 {
struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double time_value, bool aspectLens_value, std::int32_t shape_value, glsl::DVec3 tint_value, double alpha_value, double vignetteAmt_value, double distortion_value, double speed_value, double loopScale_value, double aberration_value, double hueRotation_value, double hueRange_value, std::int32_t mode_value, bool modulate_value, std::int32_t blendMode_value, double saturation_value, double passthru_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), time(time_value), aspectLens(aspectLens_value), shape(shape_value), tint(tint_value), alpha(alpha_value), vignetteAmt(vignetteAmt_value), distortion(distortion_value), speed(speed_value), loopScale(loopScale_value), aberration(aberration_value), hueRotation(hueRotation_value), hueRange(hueRange_value), mode(mode_value), modulate(modulate_value), blendMode(blendMode_value), saturation(saturation_value), passthru(passthru_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  bool aspectLens;
  std::int32_t shape;
  glsl::DVec3 tint;
  double alpha;
  double vignetteAmt;
  double distortion;
  double speed;
  double loopScale;
  double aberration;
  double hueRotation;
  double hueRange;
  std::int32_t mode;
  bool modulate;
  std::int32_t blendMode;
  double saturation;
  double passthru;
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

[[nodiscard]] double _distance([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 diff, [[maybe_unused]] glsl::Vec2 uv) noexcept;
[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
[[nodiscard]] glsl::Vec3 hsv2rgb2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept;
[[nodiscard]] glsl::Vec3 rgb2hsv2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept;
[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;

[[nodiscard]] double _distance([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 diff, [[maybe_unused]] glsl::Vec2 uv) noexcept {
  glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) * (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)))));
  [[maybe_unused]] double dist = static_cast<float>(1.0);
  if (state.shape == std::int32_t(0)) {
    dist = glsl::length(diff);
  } else {
    if (state.shape == std::int32_t(1)) {
      dist = (static_cast<double>(glsl::abs((static_cast<double>(glsl::swizzle<0>(uv)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))))))) + static_cast<double>(glsl::abs((static_cast<double>(glsl::swizzle<1>(uv)) - static_cast<double>(static_cast<float>(0.5))))));
    } else {
      if (state.shape == std::int32_t(2)) {
        dist = glsl::component_max(glsl::component_max((static_cast<double>(glsl::abs(glsl::swizzle<0>(diff))) - static_cast<double>((static_cast<double>(glsl::swizzle<1>(diff)) * static_cast<double>(static_cast<float>(-0.5))))), (static_cast<double>(static_cast<float>(-1.0)) * static_cast<double>(glsl::swizzle<1>(diff)))), glsl::component_max((static_cast<double>(glsl::abs(glsl::swizzle<0>(diff))) - static_cast<double>((static_cast<double>(glsl::swizzle<1>(diff)) * static_cast<double>(static_cast<float>(0.5))))), (static_cast<double>(static_cast<float>(1.0)) * static_cast<double>(glsl::swizzle<1>(diff)))));
      } else {
        if (state.shape == std::int32_t(3)) {
          dist = glsl::component_max((static_cast<double>((static_cast<double>(glsl::abs((static_cast<double>(glsl::swizzle<0>(uv)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))))))) + static_cast<double>(glsl::abs((static_cast<double>(glsl::swizzle<1>(uv)) - static_cast<double>(static_cast<float>(0.5))))))) / static_cast<double>(glsl::sqrt(static_cast<float>(2.0)))), glsl::component_max(glsl::abs((static_cast<double>(glsl::swizzle<0>(uv)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)))))), glsl::abs((static_cast<double>(glsl::swizzle<1>(uv)) - static_cast<double>(static_cast<float>(0.5))))));
        } else {
          if (state.shape == std::int32_t(4)) {
            dist = glsl::component_max(glsl::abs((static_cast<double>(glsl::swizzle<0>(uv)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution)))))), glsl::abs((static_cast<double>(glsl::swizzle<1>(uv)) - static_cast<double>(static_cast<float>(0.5)))));
          } else {
            if (state.shape == std::int32_t(6)) {
              dist = glsl::component_max((static_cast<double>(glsl::abs(glsl::swizzle<0>(diff))) - static_cast<double>((static_cast<double>(glsl::swizzle<1>(diff)) * static_cast<double>(static_cast<float>(-0.5))))), (static_cast<double>(static_cast<float>(-1.0)) * static_cast<double>(glsl::swizzle<1>(diff))));
            } else {
              if (state.shape == std::int32_t(10)) {
                dist = (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::length(glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(glsl::cos((static_cast<double>(glsl::swizzle<0>(diff)) * static_cast<double>(static_cast<float>(6.28318530718))))) + static_cast<double>(static_cast<float>(1.0)))) * static_cast<double>(static_cast<float>(0.5))), (static_cast<double>((static_cast<double>(glsl::cos((static_cast<double>(glsl::swizzle<1>(diff)) * static_cast<double>(static_cast<float>(6.28318530718))))) + static_cast<double>(static_cast<float>(1.0)))) * static_cast<double>(static_cast<float>(0.5)))))));
              }
            }
          }
        }
      }
    }
  }
  [[maybe_unused]] double lf = map(state, context, state.loopScale, static_cast<float>(1.0), static_cast<float>(100.0), static_cast<float>(6.0), static_cast<float>(1.0));
  [[maybe_unused]] double t = static_cast<float>(1.0);
  if (state.speed < static_cast<float>(0.0)) {
    t = (static_cast<double>((static_cast<double>(dist) * static_cast<double>(lf))) + static_cast<double>(state.time));
  } else {
    t = (static_cast<double>((static_cast<double>(dist) * static_cast<double>(lf))) - static_cast<double>(state.time));
  }
  return glsl::mix(dist, (static_cast<double>((static_cast<double>((static_cast<double>(glsl::sin((static_cast<double>(t) * static_cast<double>(static_cast<float>(6.28318530718))))) + static_cast<double>(static_cast<float>(0.5)))) * static_cast<double>(glsl::abs(state.speed)))) * static_cast<double>(static_cast<float>(0.005))), (static_cast<double>(glsl::abs(state.speed)) * static_cast<double>(static_cast<float>(0.01))));
}

[[nodiscard]] glsl::Vec3 hsv2rgb([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] double h = glsl::fract(glsl::swizzle<0>(hsv));
  [[maybe_unused]] double s = glsl::swizzle<1>(hsv);
  [[maybe_unused]] double v = glsl::swizzle<2>(hsv);
  [[maybe_unused]] double c = (static_cast<double>(v) * static_cast<double>(s));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(h) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(v) - static_cast<double>(c));
  [[maybe_unused]] glsl::Vec3 rgb = {};
  if ((static_cast<float>(0.0) <= h) && (h < static_cast<float>(0.1666666716337204))) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if ((static_cast<float>(0.1666666716337204) <= h) && (h < static_cast<float>(0.3333333432674408))) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if ((static_cast<float>(0.3333333432674408) <= h) && (h < static_cast<float>(0.5))) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if ((static_cast<float>(0.5) <= h) && (h < static_cast<float>(0.6666666865348816))) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if ((static_cast<float>(0.6666666865348816) <= h) && (h < static_cast<float>(0.8333333134651184))) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            if ((static_cast<float>(0.8333333134651184) <= h) && (h < static_cast<float>(1.0))) {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
            } else {
              rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(0.0)));
            }
          }
        }
      }
    }
  }
  return (rgb + glsl::FloatExpr<3>(m, m, m));
}

[[nodiscard]] glsl::Vec3 hsv2rgb2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 hsv) noexcept {
  [[maybe_unused]] glsl::Vec3 rgb = glsl::FloatExpr<3>(static_cast<float>(0.0));
  [[maybe_unused]] double c = (static_cast<double>(glsl::swizzle<2>(hsv)) * static_cast<double>(glsl::swizzle<1>(hsv)));
  [[maybe_unused]] double x = (static_cast<double>(c) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(glsl::abs((static_cast<double>(glsl::mod((static_cast<double>(glsl::swizzle<0>(hsv)) * static_cast<double>(static_cast<float>(6.0))), static_cast<float>(2.0))) - static_cast<double>(static_cast<float>(1.0))))))));
  [[maybe_unused]] double m = (static_cast<double>(glsl::swizzle<2>(hsv)) - static_cast<double>(c));
  if (glsl::swizzle<0>(hsv) < static_cast<float>(0.1666666716337204)) {
    rgb = glsl::Vec3(glsl::FloatExpr<3>(c, x, static_cast<float>(0.0)));
  } else {
    if (glsl::swizzle<0>(hsv) < static_cast<float>(0.3333333432674408)) {
      rgb = glsl::Vec3(glsl::FloatExpr<3>(x, c, static_cast<float>(0.0)));
    } else {
      if (glsl::swizzle<0>(hsv) < static_cast<float>(0.5)) {
        rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), c, x));
      } else {
        if (glsl::swizzle<0>(hsv) < static_cast<float>(0.6666666865348816)) {
          rgb = glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(0.0), x, c));
        } else {
          if (glsl::swizzle<0>(hsv) < static_cast<float>(0.8333333134651184)) {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(x, static_cast<float>(0.0), c));
          } else {
            rgb = glsl::Vec3(glsl::FloatExpr<3>(c, static_cast<float>(0.0), x));
          }
        }
      }
    }
  }
  rgb = glsl::Vec3((rgb + m));
  return rgb;
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] glsl::Vec3 rgb2hsv([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] double r = glsl::swizzle<0>(rgb);
  [[maybe_unused]] double g = glsl::swizzle<1>(rgb);
  [[maybe_unused]] double b = glsl::swizzle<2>(rgb);
  [[maybe_unused]] double max = glsl::component_max(r, glsl::component_max(g, b));
  [[maybe_unused]] double min = glsl::component_min(r, glsl::component_min(g, b));
  [[maybe_unused]] double delta = (static_cast<double>(max) - static_cast<double>(min));
  [[maybe_unused]] double h = static_cast<float>(0.0);
  if (delta != static_cast<float>(0.0)) {
    if (max == r) {
      h = (static_cast<double>(glsl::mod((static_cast<double>((static_cast<double>(g) - static_cast<double>(b))) / static_cast<double>(delta)), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0)));
    } else {
      if (max == g) {
        h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(b) - static_cast<double>(r))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(2.0)))) / static_cast<double>(static_cast<float>(6.0)));
      } else {
        if (max == b) {
          h = (static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(r) - static_cast<double>(g))) / static_cast<double>(delta))) + static_cast<double>(static_cast<float>(4.0)))) / static_cast<double>(static_cast<float>(6.0)));
        }
      }
    }
  }
  [[maybe_unused]] double s = ((max == static_cast<float>(0.0)) ? static_cast<float>(0.0) : (static_cast<double>(delta) / static_cast<double>(max)));
  [[maybe_unused]] double v = max;
  return glsl::FloatExpr<3>(h, s, v);
}

[[nodiscard]] glsl::Vec3 rgb2hsv2([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 rgb) noexcept {
  [[maybe_unused]] glsl::Vec3 hsv = glsl::FloatExpr<3>(static_cast<float>(0.0));
  [[maybe_unused]] double maxC = glsl::component_max(glsl::component_max(glsl::swizzle<0>(rgb), glsl::swizzle<1>(rgb)), glsl::swizzle<2>(rgb));
  [[maybe_unused]] double minC = glsl::component_min(glsl::component_min(glsl::swizzle<0>(rgb), glsl::swizzle<1>(rgb)), glsl::swizzle<2>(rgb));
  [[maybe_unused]] double diff = (static_cast<double>(maxC) - static_cast<double>(minC));
  if (glsl::swizzle<0>(rgb) == maxC) {
    glsl::set_swizzle<0>(hsv, (static_cast<double>((static_cast<double>(glsl::swizzle<1>(rgb)) - static_cast<double>(glsl::swizzle<2>(rgb)))) / static_cast<double>(diff)));
  } else {
    if (glsl::swizzle<1>(rgb) == maxC) {
      glsl::set_swizzle<0>(hsv, (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<2>(rgb)) - static_cast<double>(glsl::swizzle<0>(rgb)))) / static_cast<double>(diff))) + static_cast<double>(static_cast<float>(2.0))));
    } else {
      glsl::set_swizzle<0>(hsv, (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(rgb)) - static_cast<double>(glsl::swizzle<1>(rgb)))) / static_cast<double>(diff))) + static_cast<double>(static_cast<float>(4.0))));
    }
  }
  glsl::set_swizzle<0>(hsv, (static_cast<double>(glsl::mod(glsl::swizzle<0>(hsv), static_cast<float>(6.0))) / static_cast<double>(static_cast<float>(6.0))));
  glsl::set_swizzle<1>(hsv, glsl::component_max(static_cast<float>(0.0), (static_cast<double>(diff) / static_cast<double>(maxC))));
  glsl::set_swizzle<2>(hsv, maxC);
  return hsv;
}

[[nodiscard]] glsl::Vec3 saturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  [[maybe_unused]] double sat = map(state, context, state.saturation, static_cast<float>(-100.0), static_cast<float>(100.0), static_cast<float>(-1.0), static_cast<float>(1.0));
  [[maybe_unused]] double avg = (static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(color)) + static_cast<double>(glsl::swizzle<1>(color)))) + static_cast<double>(glsl::swizzle<2>(color)))) / static_cast<double>(static_cast<float>(3.0)));
  color = glsl::Vec3((color - ((avg - color) * sat)));
  return color;
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec2 diff = (static_cast<float>(0.5) - uv);
  if (state.aspectLens) {
    diff = glsl::Vec2((glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(static_cast<float>(0.5)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))), static_cast<float>(0.5)) - glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(uv)) * static_cast<double>(glsl::swizzle<0>(state.fullResolution)))) / static_cast<double>(glsl::swizzle<1>(state.fullResolution))), glsl::swizzle<1>(uv))));
  }
  [[maybe_unused]] double centerDist = _distance(state, context, diff, uv);
  [[maybe_unused]] double distort = static_cast<float>(0.0);
  [[maybe_unused]] double zoom = static_cast<float>(1.0);
  if (state.distortion < static_cast<float>(0.0)) {
    distort = map(state, context, state.distortion, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(-2.0), static_cast<float>(0.0));
    zoom = map(state, context, state.distortion, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(0.04), static_cast<float>(0.0));
  } else {
    distort = map(state, context, state.distortion, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(2.0));
    zoom = map(state, context, state.distortion, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(-1.0));
  }
  [[maybe_unused]] glsl::Vec2 lensedCoords = glsl::fract(((uv - (diff * zoom)) - (((diff * centerDist) * centerDist) * distort)));
  [[maybe_unused]] double aberrationOffset = (static_cast<double>((static_cast<double>((static_cast<double>(map(state, context, state.aberration, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(0.05))) * static_cast<double>(centerDist))) * static_cast<double>(static_cast<float>(3.14159265359)))) * static_cast<double>(static_cast<float>(0.5)));
  [[maybe_unused]] double redOffset = glsl::mix(glsl::clamp((static_cast<double>(glsl::swizzle<0>(lensedCoords)) + static_cast<double>(aberrationOffset)), static_cast<float>(0.0), static_cast<float>(1.0)), glsl::swizzle<0>(lensedCoords), glsl::swizzle<0>(lensedCoords));
  [[maybe_unused]] glsl::Vec4 red = sample_texture(*state.inputTex, glsl::FloatExpr<2>(redOffset, glsl::swizzle<1>(lensedCoords)));
  [[maybe_unused]] glsl::Vec4 green = sample_texture(*state.inputTex, lensedCoords);
  [[maybe_unused]] double blueOffset = glsl::mix(glsl::swizzle<0>(lensedCoords), glsl::clamp((static_cast<double>(glsl::swizzle<0>(lensedCoords)) - static_cast<double>(aberrationOffset)), static_cast<float>(0.0), static_cast<float>(1.0)), glsl::swizzle<0>(lensedCoords));
  [[maybe_unused]] glsl::Vec4 blue = sample_texture(*state.inputTex, glsl::FloatExpr<2>(blueOffset, glsl::swizzle<1>(lensedCoords)));
  [[maybe_unused]] glsl::Vec3 hsv = glsl::FloatExpr<3>(static_cast<float>(1.0));
  [[maybe_unused]] double t = (state.modulate ? state.time : static_cast<float>(0.0));
  if (state.mode == std::int32_t(0)) {
    color = glsl::Vec4((glsl::FloatExpr<4>(glsl::swizzle<0>(red), glsl::swizzle<1>(green), glsl::swizzle<2>(blue), glsl::swizzle<3>(color)) - green));
    glsl::set_swizzle<3>(color, glsl::swizzle<3>(green));
    hsv = glsl::Vec3(rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color)));
    glsl::set_swizzle<0>(hsv, glsl::fract((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(hsv)) + static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(state.hueRotation) / static_cast<double>(static_cast<float>(360.0)))))))) + static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(hsv)) * static_cast<double>(state.hueRange))) * static_cast<double>(static_cast<float>(0.01)))))) + static_cast<double>(t))));
    glsl::set_swizzle<1>(hsv, static_cast<float>(1.0));
  } else {
    color = glsl::Vec4((glsl::FloatExpr<4>(glsl::length((glsl::FloatExpr<4>(glsl::swizzle<0>(red), glsl::swizzle<1>(green), glsl::swizzle<2>(blue), glsl::swizzle<3>(color)) - green))) * green));
    glsl::set_swizzle<3>(color, glsl::swizzle<3>(green));
    hsv = glsl::Vec3(rgb2hsv(state, context, glsl::swizzle<0, 1, 2>(color)));
    glsl::set_swizzle<0>(hsv, glsl::fract((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(hsv)) + static_cast<double>(static_cast<float>(0.125)))) + static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(state.hueRotation) / static_cast<double>(static_cast<float>(360.0)))))))) * static_cast<double>((static_cast<double>(static_cast<float>(2.0)) + static_cast<double>((static_cast<double>(state.hueRange) * static_cast<double>(static_cast<float>(0.05)))))))) + static_cast<double>(t))));
    glsl::set_swizzle<1>(hsv, static_cast<float>(1.0));
  }
  glsl::set_swizzle<0, 1, 2>(green, glsl::Vec3((saturate(state, context, glsl::swizzle<0, 1, 2>(green)) * map(state, context, state.passthru, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(2.0)))));
  if (state.blendMode == std::int32_t(0)) {
    glsl::set_swizzle<0, 1, 2>(color, glsl::component_min(glsl::Vec3((glsl::swizzle<0, 1, 2>(green) + hsv2rgb(state, context, hsv))), static_cast<float>(1.0)));
  } else {
    if (state.blendMode == std::int32_t(1)) {
      glsl::set_swizzle<0, 1, 2>(color, glsl::component_min(glsl::Vec3((glsl::component_max((glsl::swizzle<0, 1, 2>(green) - glsl::FloatExpr<3>(glsl::swizzle<2>(hsv))), static_cast<float>(0.0)) + hsv2rgb(state, context, hsv))), static_cast<float>(1.0)));
    }
  }
  glsl::set_swizzle<0, 1, 2>(color, glsl::mix(glsl::swizzle<0, 1, 2>(color), (historical_truthy_vector_equality(glsl::Vec3(glsl::swizzle<0, 1, 2>(color)), glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0)))) ? glsl::Vec3(glsl::swizzle<0, 1, 2>(color)) : glsl::Vec3(glsl::component_min(((state.tint * state.tint) / (static_cast<float>(1.0) - glsl::swizzle<0, 1, 2>(color))), glsl::FloatExpr<3>(static_cast<float>(1.0))))), (static_cast<double>(state.alpha) * static_cast<double>(static_cast<float>(0.01)))));
  glsl::set_swizzle<3>(color, glsl::component_max(glsl::swizzle<3>(color), (static_cast<double>(state.alpha) * static_cast<double>(static_cast<float>(0.01)))));
  if (state.vignetteAmt < static_cast<float>(0.0)) {
    glsl::set_swizzle<0, 1, 2>(color, glsl::mix(((glsl::swizzle<0, 1, 2>(color) * static_cast<float>(1.0)) - glsl::pow((static_cast<double>(glsl::length((static_cast<float>(0.5) - uv))) * static_cast<double>(static_cast<float>(1.125))), static_cast<float>(2.0))), glsl::swizzle<0, 1, 2>(color), map(state, context, state.vignetteAmt, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(0.0), static_cast<float>(1.0))));
    glsl::set_swizzle<3>(color, glsl::component_max(glsl::swizzle<3>(color), (static_cast<double>(glsl::length((static_cast<float>(0.5) - uv))) * static_cast<double>(map(state, context, state.vignetteAmt, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(1.0), static_cast<float>(0.0))))));
  } else {
    glsl::set_swizzle<0, 1, 2>(color, glsl::mix(glsl::swizzle<0, 1, 2>(color), (static_cast<float>(1.0) - ((static_cast<float>(1.0) - (glsl::swizzle<0, 1, 2>(color) * static_cast<float>(1.0))) - glsl::pow((static_cast<double>(glsl::length((static_cast<float>(0.5) - uv))) * static_cast<double>(static_cast<float>(1.125))), static_cast<float>(2.0)))), map(state, context, state.vignetteAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0))));
    glsl::set_swizzle<3>(color, glsl::component_max(glsl::swizzle<3>(color), (static_cast<double>(glsl::length((static_cast<float>(0.5) - uv))) * static_cast<double>(map(state, context, state.vignetteAmt, static_cast<float>(-100.0), static_cast<float>(0.0), static_cast<float>(1.0), static_cast<float>(0.0))))));
  }
  output = glsl::Vec4(color);
}
}  // namespace typed_11

BoundKernel bind_classicNoisedeck_lensDistortion_lensDistortion(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_11::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("time"), bindings.get<bool>("aspectLens"), bindings.get<std::int32_t>("shape"), bindings.get<glsl::DVec3>("tint"), bindings.get_number("alpha"), bindings.get_number("vignetteAmt"), bindings.get_number("distortion"), bindings.get_number("speed"), bindings.get_number("loopScale"), bindings.get_number("aberration"), bindings.get_number("hueRotation"), bindings.get_number("hueRange"), bindings.get<std::int32_t>("mode"), bindings.get<bool>("modulate"), bindings.get<std::int32_t>("blendMode"), bindings.get_number("saturation"), bindings.get_number("passthru"));
  (void)bindings;
  return BoundKernel(state, &typed_11::pixel);
}
// Typed IR program: classicNoisedeck/refract:refract
// Source SHA-256: d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2
namespace typed_14 {
using Kernel9 = std::array<double, 9>;
using Offsets9 = std::array<glsl::Vec2, 9>;
static_assert(sizeof(Kernel9) == 72U);
static_assert(sizeof(Offsets9) == 72U);

struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double time_value, std::int32_t mode_value, double amount_value, double direction_value, std::int32_t blendMode_value, double mixAmt_value, std::int32_t wrap_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), time(time_value), mode(mode_value), amount(amount_value), direction(direction_value), blendMode(blendMode_value), mixAmt(mixAmt_value), wrap(wrap_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  std::int32_t mode;
  double amount;
  double direction;
  std::int32_t blendMode;
  double mixAmt;
  std::int32_t wrap;
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

[[nodiscard]] glsl::Vec3 blend([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color1, [[maybe_unused]] glsl::Vec4 color2) noexcept;
[[nodiscard]] double blendOverlay([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double a, [[maybe_unused]] double b) noexcept;
[[nodiscard]] double blendSoftLight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base, [[maybe_unused]] double blend) noexcept;
[[nodiscard]] glsl::Vec3 convolve([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] const Kernel9& kernel, [[maybe_unused]] bool divide) noexcept;
[[nodiscard]] glsl::Vec3 derivX([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept;
[[nodiscard]] glsl::Vec3 derivY([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept;
[[nodiscard]] double desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept;
[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept;
[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double p) noexcept;

[[nodiscard]] glsl::Vec3 blend([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 color1, [[maybe_unused]] glsl::Vec4 color2) noexcept {
  [[maybe_unused]] glsl::Vec4 color = {};
  [[maybe_unused]] glsl::Vec4 middle = {};
  [[maybe_unused]] double amt = map(state, context, state.mixAmt, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(1.0));
  if (state.blendMode == std::int32_t(0)) {
    middle = glsl::Vec4(glsl::component_min((color1 + color2), static_cast<float>(1.0)));
  } else {
    if (state.blendMode == std::int32_t(2)) {
      middle = glsl::Vec4(middle);
    } else {
      if (state.blendMode == std::int32_t(3)) {
        middle = glsl::Vec4(middle);
      } else {
        if (state.blendMode == std::int32_t(4)) {
          middle = glsl::Vec4(glsl::component_min(color1, color2));
        } else {
          if (state.blendMode == std::int32_t(5)) {
            middle = glsl::Vec4(glsl::abs((color1 - color2)));
          } else {
            if (state.blendMode == std::int32_t(6)) {
              middle = glsl::Vec4(((color1 + color2) - ((static_cast<float>(2.0) * color1) * color2)));
            } else {
              if (state.blendMode == std::int32_t(7)) {
                middle = glsl::Vec4(middle);
              } else {
                if (state.blendMode == std::int32_t(8)) {
                  middle = glsl::Vec4(glsl::FloatExpr<4>(blendOverlay(state, context, glsl::swizzle<0>(color2), glsl::swizzle<0>(color1)), blendOverlay(state, context, glsl::swizzle<1>(color2), glsl::swizzle<1>(color1)), blendOverlay(state, context, glsl::swizzle<2>(color2), glsl::swizzle<2>(color1)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                } else {
                  if (state.blendMode == std::int32_t(9)) {
                    middle = glsl::Vec4(glsl::component_max(color1, color2));
                  } else {
                    if (state.blendMode == std::int32_t(10)) {
                      middle = glsl::Vec4(glsl::mix(color1, color2, static_cast<float>(0.5)));
                    } else {
                      if (state.blendMode == std::int32_t(11)) {
                        middle = glsl::Vec4((color1 * color2));
                      } else {
                        if (state.blendMode == std::int32_t(12)) {
                          middle = glsl::Vec4(glsl::Vec4((glsl::FloatExpr<4>(static_cast<float>(1.0)) - glsl::abs(((glsl::FloatExpr<4>(static_cast<float>(1.0)) - color1) - color2)))));
                        } else {
                          if (state.blendMode == std::int32_t(13)) {
                            middle = glsl::Vec4(glsl::FloatExpr<4>(blendOverlay(state, context, glsl::swizzle<0>(color1), glsl::swizzle<0>(color2)), blendOverlay(state, context, glsl::swizzle<1>(color1), glsl::swizzle<1>(color2)), blendOverlay(state, context, glsl::swizzle<2>(color1), glsl::swizzle<2>(color2)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                          } else {
                            if (state.blendMode == std::int32_t(14)) {
                              middle = glsl::Vec4(glsl::Vec4((glsl::Vec4((glsl::component_min(color1, color2) - glsl::component_max(color1, color2))) + glsl::FloatExpr<4>(static_cast<float>(1.0)))));
                            } else {
                              if (state.blendMode == std::int32_t(15)) {
                                middle = glsl::Vec4(middle);
                              } else {
                                if (state.blendMode == std::int32_t(16)) {
                                  middle = glsl::Vec4((static_cast<float>(1.0) - ((static_cast<float>(1.0) - color1) * (static_cast<float>(1.0) - color2))));
                                } else {
                                  if (state.blendMode == std::int32_t(17)) {
                                    middle = glsl::Vec4(glsl::FloatExpr<4>(blendSoftLight(state, context, glsl::swizzle<0>(color1), glsl::swizzle<0>(color2)), blendSoftLight(state, context, glsl::swizzle<1>(color1), glsl::swizzle<1>(color2)), blendSoftLight(state, context, glsl::swizzle<2>(color1), glsl::swizzle<2>(color2)), glsl::mix(glsl::swizzle<3>(color1), glsl::swizzle<3>(color2), static_cast<float>(0.5))));
                                  } else {
                                    if (state.blendMode == std::int32_t(18)) {
                                      middle = glsl::Vec4(glsl::component_max(((color1 + color2) - static_cast<float>(1.0)), static_cast<float>(0.0)));
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  if (amt == static_cast<float>(0.5)) {
    color = glsl::Vec4(middle);
  } else {
    if (amt < static_cast<float>(0.5)) {
      amt = map(state, context, amt, static_cast<float>(0.0), static_cast<float>(0.5), static_cast<float>(0.0), static_cast<float>(1.0));
      color = glsl::Vec4(glsl::mix(color1, middle, amt));
    } else {
      if (amt > static_cast<float>(0.5)) {
        amt = map(state, context, amt, static_cast<float>(0.5), static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(1.0));
        color = glsl::Vec4(glsl::mix(middle, color2, amt));
      }
    }
  }
  return glsl::swizzle<0, 1, 2>(color);
}

[[nodiscard]] double blendOverlay([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double a, [[maybe_unused]] double b) noexcept {
  return ((a < static_cast<float>(0.5)) ? (static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(a))) * static_cast<double>(b)) : (static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(a))))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(b)))))));
}

[[nodiscard]] double blendSoftLight([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base, [[maybe_unused]] double blend) noexcept {
  return ((blend < static_cast<float>(0.5)) ? (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(base))) * static_cast<double>(blend))) + static_cast<double>((static_cast<double>((static_cast<double>(base) * static_cast<double>(base))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(blend)))))))) : (static_cast<double>((static_cast<double>(glsl::sqrt(base)) * static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(blend))) - static_cast<double>(static_cast<float>(1.0)))))) + static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(2.0)) * static_cast<double>(base))) * static_cast<double>((static_cast<double>(static_cast<float>(1.0)) - static_cast<double>(blend)))))));
}

[[nodiscard]] glsl::Vec3 convolve([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] const Kernel9& kernel, [[maybe_unused]] bool divide) noexcept {
  [[maybe_unused]] glsl::Vec2 localUV = (((uv * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)));
  [[maybe_unused]] glsl::Vec2 steps = (static_cast<float>(1.0) / glsl::Vec2(texture_size(*state.inputTex)));
  [[maybe_unused]] Offsets9 offset{};
  offset[0] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), (-glsl::swizzle<1>(steps))));
  offset[1] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), (-glsl::swizzle<1>(steps))));
  offset[2] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), (-glsl::swizzle<1>(steps))));
  offset[3] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), static_cast<float>(0.0)));
  offset[4] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), static_cast<float>(0.0)));
  offset[5] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), static_cast<float>(0.0)));
  offset[6] = glsl::Vec2(glsl::FloatExpr<2>((-glsl::swizzle<0>(steps)), glsl::swizzle<1>(steps)));
  offset[7] = glsl::Vec2(glsl::FloatExpr<2>(static_cast<float>(0.0), glsl::swizzle<1>(steps)));
  offset[8] = glsl::Vec2(glsl::FloatExpr<2>(glsl::swizzle<0>(steps), glsl::swizzle<1>(steps)));
  [[maybe_unused]] double kernelWeight = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec3 conv = glsl::FloatExpr<3>(static_cast<float>(0.0));
  for ([[maybe_unused]] std::int32_t i = std::int32_t(0); (i < std::int32_t(9)); ++i) {
    [[maybe_unused]] glsl::Vec3 color = glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, (localUV + (offset[static_cast<std::size_t>(i)] * glsl::floor(map(state, context, state.amount, static_cast<float>(0.0), static_cast<float>(100.0), static_cast<float>(0.0), static_cast<float>(20.0)))))));
    conv = glsl::Vec3((conv + (color * kernel[static_cast<std::size_t>(i)])));
    kernelWeight = (kernelWeight + kernel[static_cast<std::size_t>(i)]);
  }
  if (divide) {
    glsl::set_swizzle<0, 1, 2>(conv, (glsl::swizzle<0, 1, 2>(conv) / kernelWeight));
  }
  return glsl::clamp(glsl::swizzle<0, 1, 2>(conv), static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] glsl::Vec3 derivX([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept {
  [[maybe_unused]] glsl::Vec3 dcolor = glsl::FloatExpr<3>(desaturate(state, context, color));
  [[maybe_unused]] Kernel9 deriv_x{};
  deriv_x[0] = static_cast<float>(0.0);
  deriv_x[1] = static_cast<float>(0.0);
  deriv_x[2] = static_cast<float>(0.0);
  deriv_x[3] = static_cast<float>(0.0);
  deriv_x[4] = static_cast<float>(1.0);
  deriv_x[5] = static_cast<float>(-1.0);
  deriv_x[6] = static_cast<float>(0.0);
  deriv_x[7] = static_cast<float>(0.0);
  deriv_x[8] = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec3 s1 = convolve(state, context, uv, deriv_x, divide);
  return s1;
}

[[nodiscard]] glsl::Vec3 derivY([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] bool divide) noexcept {
  [[maybe_unused]] glsl::Vec3 dcolor = glsl::FloatExpr<3>(desaturate(state, context, color));
  [[maybe_unused]] Kernel9 deriv_y{};
  deriv_y[0] = static_cast<float>(0.0);
  deriv_y[1] = static_cast<float>(0.0);
  deriv_y[2] = static_cast<float>(0.0);
  deriv_y[3] = static_cast<float>(0.0);
  deriv_y[4] = static_cast<float>(1.0);
  deriv_y[5] = static_cast<float>(0.0);
  deriv_y[6] = static_cast<float>(0.0);
  deriv_y[7] = static_cast<float>(-1.0);
  deriv_y[8] = static_cast<float>(0.0);
  [[maybe_unused]] glsl::Vec3 s2 = convolve(state, context, uv, deriv_y, divide);
  return s2;
}

[[nodiscard]] double desaturate([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 color) noexcept {
  return (static_cast<double>((static_cast<double>((static_cast<double>(static_cast<float>(0.2126)) * static_cast<double>(glsl::swizzle<0>(color)))) + static_cast<double>((static_cast<double>(static_cast<float>(0.7152)) * static_cast<double>(glsl::swizzle<1>(color)))))) + static_cast<double>((static_cast<double>(static_cast<float>(0.0722)) * static_cast<double>(glsl::swizzle<2>(color)))));
}

[[nodiscard]] double map([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double inMin, [[maybe_unused]] double inMax, [[maybe_unused]] double outMin, [[maybe_unused]] double outMax) noexcept {
  return (static_cast<double>(outMin) + static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(outMax) - static_cast<double>(outMin))) * static_cast<double>((static_cast<double>(value) - static_cast<double>(inMin))))) / static_cast<double>((static_cast<double>(inMax) - static_cast<double>(inMin))))));
}

[[nodiscard]] double periodicFunction([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double p) noexcept {
  return map(state, context, glsl::sin((static_cast<double>(p) * static_cast<double>(static_cast<float>(6.28318530718)))), static_cast<float>(-1.0), static_cast<float>(1.0), static_cast<float>(0.0), static_cast<float>(1.0));
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::Vec2 globalCoord = (glsl::swizzle<0, 1>(context.frag_coord) + state.tileOffset);
  [[maybe_unused]] glsl::Vec2 uv = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec4 color = glsl::FloatExpr<4>(static_cast<float>(0.0));
  [[maybe_unused]] glsl::Vec2 localUV = (((uv * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)));
  [[maybe_unused]] glsl::Vec4 inputColor = sample_texture(*state.inputTex, localUV);
  [[maybe_unused]] double brightness = (static_cast<double>(desaturate(state, context, glsl::swizzle<0, 1, 2>(inputColor))) + static_cast<double>((static_cast<double>(state.direction) / static_cast<double>(static_cast<float>(360.0)))));
  [[maybe_unused]] double displacement = (static_cast<double>(state.amount) * static_cast<double>(static_cast<float>(0.01)));
  if ((glsl::swizzle<0>(state.fullResolution) > glsl::swizzle<0>(state.resolution)) || (glsl::swizzle<1>(state.fullResolution) > glsl::swizzle<1>(state.resolution))) {
    [[maybe_unused]] double maxDisplacement = (static_cast<double>(static_cast<float>(256.0)) / static_cast<double>(glsl::component_max(glsl::swizzle<0>(state.fullResolution), glsl::swizzle<1>(state.fullResolution))));
    displacement = glsl::component_min(displacement, maxDisplacement);
  }
  if (state.mode == std::int32_t(0)) {
    glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) + (static_cast<double>(glsl::cos((static_cast<double>(brightness) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(displacement))));
    glsl::set_swizzle<1>(uv, (glsl::swizzle<1>(uv) + (static_cast<double>(glsl::sin((static_cast<double>(brightness) * static_cast<double>(static_cast<float>(6.28318530718))))) * static_cast<double>(displacement))));
  } else {
    if (state.mode == std::int32_t(1)) {
      glsl::set_swizzle<1>(uv, (glsl::swizzle<1>(uv) + (static_cast<double>(desaturate(state, context, derivX(state, context, glsl::swizzle<0, 1, 2>(inputColor), uv, false))) * static_cast<double>(displacement))));
      glsl::set_swizzle<0>(uv, (glsl::swizzle<0>(uv) + (static_cast<double>(desaturate(state, context, derivY(state, context, glsl::swizzle<0, 1, 2>(inputColor), uv, false))) * static_cast<double>(displacement))));
    }
  }
  if (state.wrap == std::int32_t(0)) {
    uv = glsl::Vec2(glsl::abs(glsl::Vec2((glsl::mod((uv + static_cast<float>(1.0)), static_cast<float>(2.0)) - static_cast<float>(1.0)))));
  } else {
    if (state.wrap == std::int32_t(1)) {
      uv = glsl::Vec2(glsl::mod(uv, static_cast<float>(1.0)));
    } else {
      if (state.wrap == std::int32_t(2)) {
        uv = glsl::Vec2(glsl::clamp(uv, static_cast<float>(0.0), static_cast<float>(1.0)));
      }
    }
  }
  [[maybe_unused]] glsl::Vec2 warpedLocalUV = (((uv * state.fullResolution) - state.tileOffset) / glsl::Vec2(texture_size(*state.inputTex)));
  color = glsl::Vec4(sample_texture(*state.inputTex, warpedLocalUV));
  glsl::set_swizzle<0, 1, 2>(color, blend(state, context, inputColor, color));
  output = glsl::Vec4(color);
}
}  // namespace typed_14

BoundKernel bind_classicNoisedeck_refract_refract(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_14::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("time"), bindings.get<std::int32_t>("mode"), bindings.get_number("amount"), bindings.get_number("direction"), bindings.get<std::int32_t>("blendMode"), bindings.get_number("mixAmt"), bindings.get<std::int32_t>("wrap"));
  (void)bindings;
  return BoundKernel(state, &typed_14::pixel);
}
// Typed IR program: filter/degauss:degauss
// Source SHA-256: 915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c
namespace typed_42 {
struct State final : KernelState {
  State(const Surface* inputTex_value, glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double time_value, double displacement_value, double speed_value, std::int32_t seed_value, double direction_value) : inputTex(inputTex_value), resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), time(time_value), displacement(displacement_value), speed(speed_value), seed(seed_value), direction(direction_value) {}
  const Surface* inputTex;
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double time;
  double displacement;
  double speed;
  std::int32_t seed;
  double direction;
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

[[nodiscard]] std::uint32_t as_u32([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept;
[[nodiscard]] double clamp01([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept;
[[nodiscard]] double compute_noise_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec2 coord, [[maybe_unused]] double width, [[maybe_unused]] double height, [[maybe_unused]] glsl::Vec2 freq, [[maybe_unused]] double time, [[maybe_unused]] double speed, [[maybe_unused]] std::uint32_t channel) noexcept;
[[nodiscard]] glsl::Vec2 freq_for_shape([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base_freq, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept;
[[nodiscard]] glsl::Vec3 mod289_vec3([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 x) noexcept;
[[nodiscard]] glsl::Vec4 mod289_vec4([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 x) noexcept;
[[nodiscard]] double normalized_sine([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept;
[[nodiscard]] double periodic_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double time, [[maybe_unused]] double value) noexcept;
[[nodiscard]] glsl::Vec4 permute([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 x) noexcept;
[[nodiscard]] glsl::Vec4 sample_bilinear([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 pos, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept;
[[nodiscard]] double simplex_noise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 v) noexcept;
[[nodiscard]] double singularity_mask([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept;
[[nodiscard]] glsl::Vec4 taylor_inv_sqrt([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 r) noexcept;
[[nodiscard]] double warped_channel_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t channel, [[maybe_unused]] glsl::UVec2 coord, [[maybe_unused]] glsl::Vec2 base_pos, [[maybe_unused]] double width, [[maybe_unused]] double height, [[maybe_unused]] glsl::Vec2 freq, [[maybe_unused]] double displacement, [[maybe_unused]] double mask, [[maybe_unused]] double time, [[maybe_unused]] double speed) noexcept;
[[nodiscard]] double wrap_float([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double limit) noexcept;
[[nodiscard]] std::int32_t wrap_index([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t value, [[maybe_unused]] std::int32_t limit) noexcept;

[[nodiscard]] std::uint32_t as_u32([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept {
  return glsl::detail::float_to_uint32(glsl::component_max(value, static_cast<float>(0.0)));
}

[[nodiscard]] double clamp01([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept {
  return glsl::clamp(value, static_cast<float>(0.0), static_cast<float>(1.0));
}

[[nodiscard]] double compute_noise_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::UVec2 coord, [[maybe_unused]] double width, [[maybe_unused]] double height, [[maybe_unused]] glsl::Vec2 freq, [[maybe_unused]] double time, [[maybe_unused]] double speed, [[maybe_unused]] std::uint32_t channel) noexcept {
  const double TAU = static_cast<float>(6.28318530717958647692);
  [[maybe_unused]] double width_safe = glsl::component_max(width, static_cast<float>(1.0));
  [[maybe_unused]] double height_safe = glsl::component_max(height, static_cast<float>(1.0));
  [[maybe_unused]] double freq_x = glsl::component_max(glsl::swizzle<1>(freq), static_cast<float>(1.0));
  [[maybe_unused]] double freq_y = glsl::component_max(glsl::swizzle<0>(freq), static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec2 uv = glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(float(glsl::swizzle<0>(coord))) / static_cast<double>(width_safe))) * static_cast<double>(freq_x)), (static_cast<double>((static_cast<double>(float(glsl::swizzle<1>(coord))) / static_cast<double>(height_safe))) * static_cast<double>(freq_y)));
  [[maybe_unused]] double angle = (static_cast<double>(time) * static_cast<double>(TAU));
  [[maybe_unused]] double z_base = (static_cast<double>(glsl::cos(angle)) * static_cast<double>(speed));
  [[maybe_unused]] double channel_offset = (static_cast<double>(float(channel)) * static_cast<double>(static_cast<float>(37.0)));
  [[maybe_unused]] double seed_offset = (static_cast<double>(float(state.seed)) * static_cast<double>(static_cast<float>(73.0)));
  [[maybe_unused]] glsl::Vec3 base_seed = glsl::FloatExpr<3>((static_cast<double>((static_cast<double>(static_cast<float>(17.0)) + static_cast<double>(channel_offset))) + static_cast<double>(seed_offset)), (static_cast<double>((static_cast<double>(static_cast<float>(29.0)) + static_cast<double>((static_cast<double>(channel_offset) * static_cast<double>(static_cast<float>(1.3)))))) + static_cast<double>((static_cast<double>(seed_offset) * static_cast<double>(static_cast<float>(1.1))))), (static_cast<double>((static_cast<double>(static_cast<float>(47.0)) + static_cast<double>((static_cast<double>(channel_offset) * static_cast<double>(static_cast<float>(1.7)))))) + static_cast<double>((static_cast<double>(seed_offset) * static_cast<double>(static_cast<float>(0.7))))));
  [[maybe_unused]] double base_noise = simplex_noise(state, context, glsl::FloatExpr<3>((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>(glsl::swizzle<0>(base_seed))), (static_cast<double>(glsl::swizzle<1>(uv)) + static_cast<double>(glsl::swizzle<1>(base_seed))), (static_cast<double>(z_base) + static_cast<double>(glsl::swizzle<2>(base_seed)))));
  [[maybe_unused]] double value = glsl::clamp((static_cast<double>((static_cast<double>(base_noise) * static_cast<double>(static_cast<float>(0.5)))) + static_cast<double>(static_cast<float>(0.5))), static_cast<float>(0.0), static_cast<float>(1.0));
  if ((speed != static_cast<float>(0.0)) && (time != static_cast<float>(0.0))) {
    [[maybe_unused]] glsl::Vec3 time_seed = glsl::FloatExpr<3>((static_cast<double>(glsl::swizzle<0>(base_seed)) + static_cast<double>(static_cast<float>(54.0))), (static_cast<double>(glsl::swizzle<1>(base_seed)) + static_cast<double>(static_cast<float>(82.0))), (static_cast<double>(glsl::swizzle<2>(base_seed)) + static_cast<double>(static_cast<float>(124.0))));
    [[maybe_unused]] double time_noise = simplex_noise(state, context, glsl::FloatExpr<3>((static_cast<double>(glsl::swizzle<0>(uv)) + static_cast<double>(glsl::swizzle<0>(time_seed))), (static_cast<double>(glsl::swizzle<1>(uv)) + static_cast<double>(glsl::swizzle<1>(time_seed))), glsl::swizzle<2>(time_seed)));
    [[maybe_unused]] double time_value = glsl::clamp((static_cast<double>((static_cast<double>(time_noise) * static_cast<double>(static_cast<float>(0.5)))) + static_cast<double>(static_cast<float>(0.5))), static_cast<float>(0.0), static_cast<float>(1.0));
    [[maybe_unused]] double scaled_time = (static_cast<double>(periodic_value(state, context, time, time_value)) * static_cast<double>(speed));
    value = clamp01(state, context, periodic_value(state, context, scaled_time, value));
  }
  return clamp01(state, context, value);
}

[[nodiscard]] glsl::Vec2 freq_for_shape([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double base_freq, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept {
  if (base_freq <= static_cast<float>(0.0)) {
    return glsl::FloatExpr<2>(static_cast<float>(1.0), static_cast<float>(1.0));
  }
  if (glsl::abs((static_cast<double>(width) - static_cast<double>(height))) < static_cast<float>(1e-5)) {
    return glsl::FloatExpr<2>(base_freq, base_freq);
  }
  if ((height < width) && (height > static_cast<float>(0.0))) {
    return glsl::FloatExpr<2>(base_freq, (static_cast<double>((static_cast<double>(base_freq) * static_cast<double>(width))) / static_cast<double>(height)));
  }
  if (width > static_cast<float>(0.0)) {
    return glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(base_freq) * static_cast<double>(height))) / static_cast<double>(width)), base_freq);
  }
  return glsl::FloatExpr<2>(base_freq, base_freq);
}

[[nodiscard]] glsl::Vec3 mod289_vec3([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 x) noexcept {
  return glsl::Vec3((x - glsl::Vec3((glsl::floor((x * static_cast<float>(0.0034602077212184668))) * static_cast<float>(289.0)))));
}

[[nodiscard]] glsl::Vec4 mod289_vec4([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 x) noexcept {
  return glsl::Vec4((x - glsl::Vec4((glsl::floor((x * static_cast<float>(0.0034602077212184668))) * static_cast<float>(289.0)))));
}

[[nodiscard]] double normalized_sine([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value) noexcept {
  return (static_cast<double>((static_cast<double>(glsl::sin(value)) * static_cast<double>(static_cast<float>(0.5)))) + static_cast<double>(static_cast<float>(0.5)));
}

[[nodiscard]] double periodic_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double time, [[maybe_unused]] double value) noexcept {
  const double TAU = static_cast<float>(6.28318530717958647692);
  return normalized_sine(state, context, (static_cast<double>((static_cast<double>(time) - static_cast<double>(value))) * static_cast<double>(TAU)));
}

[[nodiscard]] glsl::Vec4 permute([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 x) noexcept {
  return mod289_vec4(state, context, (((x * static_cast<float>(34.0)) + static_cast<float>(1.0)) * x));
}

[[nodiscard]] glsl::Vec4 sample_bilinear([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 pos, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept {
  [[maybe_unused]] double width_f = glsl::component_max(width, static_cast<float>(1.0));
  [[maybe_unused]] double height_f = glsl::component_max(height, static_cast<float>(1.0));
  [[maybe_unused]] double wrapped_x = wrap_float(state, context, glsl::swizzle<0>(pos), width_f);
  [[maybe_unused]] double wrapped_y = wrap_float(state, context, glsl::swizzle<1>(pos), height_f);
  [[maybe_unused]] std::int32_t x0 = glsl::detail::glsl_int_cast(glsl::floor(wrapped_x));
  [[maybe_unused]] std::int32_t y0 = glsl::detail::glsl_int_cast(glsl::floor(wrapped_y));
  [[maybe_unused]] std::int32_t width_i = glsl::detail::glsl_int_cast(glsl::component_max(width, static_cast<float>(1.0)));
  [[maybe_unused]] std::int32_t height_i = glsl::detail::glsl_int_cast(glsl::component_max(height, static_cast<float>(1.0)));
  if (x0 < std::int32_t(0)) {
    x0 = std::int32_t(0);
  } else {
    if (x0 >= width_i) {
      x0 = (width_i - std::int32_t(1));
    }
  }
  if (y0 < std::int32_t(0)) {
    y0 = std::int32_t(0);
  } else {
    if (y0 >= height_i) {
      y0 = (height_i - std::int32_t(1));
    }
  }
  [[maybe_unused]] std::int32_t x1 = wrap_index(state, context, (x0 + std::int32_t(1)), width_i);
  [[maybe_unused]] std::int32_t y1 = wrap_index(state, context, (y0 + std::int32_t(1)), height_i);
  [[maybe_unused]] double fx = glsl::clamp((static_cast<double>(wrapped_x) - static_cast<double>(float(x0))), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] double fy = glsl::clamp((static_cast<double>(wrapped_y) - static_cast<double>(float(y0))), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] glsl::Vec4 tex00 = fetch_texel(*state.inputTex, glsl::IVec2(x0, y0));
  [[maybe_unused]] glsl::Vec4 tex10 = fetch_texel(*state.inputTex, glsl::IVec2(x1, y0));
  [[maybe_unused]] glsl::Vec4 tex01 = fetch_texel(*state.inputTex, glsl::IVec2(x0, y1));
  [[maybe_unused]] glsl::Vec4 tex11 = fetch_texel(*state.inputTex, glsl::IVec2(x1, y1));
  [[maybe_unused]] glsl::Vec4 mix_x0 = glsl::mix(tex00, tex10, glsl::FloatExpr<4>(fx));
  [[maybe_unused]] glsl::Vec4 mix_x1 = glsl::mix(tex01, tex11, glsl::FloatExpr<4>(fx));
  return glsl::mix(mix_x0, mix_x1, glsl::FloatExpr<4>(fy));
}

[[nodiscard]] double simplex_noise([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec3 v) noexcept {
  [[maybe_unused]] glsl::Vec2 C = glsl::FloatExpr<2>(static_cast<float>(0.1666666716337204), static_cast<float>(0.3333333432674408));
  [[maybe_unused]] glsl::Vec4 D = glsl::FloatExpr<4>(static_cast<float>(0.0), static_cast<float>(0.5), static_cast<float>(1.0), static_cast<float>(2.0));
  [[maybe_unused]] glsl::Vec3 i0 = glsl::floor((v + glsl::dot(v, glsl::FloatExpr<3>(glsl::swizzle<1>(C)))));
  [[maybe_unused]] glsl::Vec3 x0 = ((v - i0) + glsl::dot(i0, glsl::FloatExpr<3>(glsl::swizzle<0>(C))));
  [[maybe_unused]] glsl::Vec3 step1 = glsl::step(glsl::FloatExpr<3>(glsl::swizzle<1>(x0), glsl::swizzle<2>(x0), glsl::swizzle<0>(x0)), x0);
  [[maybe_unused]] glsl::Vec3 l = (glsl::FloatExpr<3>(static_cast<float>(1.0)) - step1);
  [[maybe_unused]] glsl::Vec3 i1 = glsl::component_min(step1, glsl::FloatExpr<3>(glsl::swizzle<2>(l), glsl::swizzle<0>(l), glsl::swizzle<1>(l)));
  [[maybe_unused]] glsl::Vec3 i2 = glsl::component_max(step1, glsl::FloatExpr<3>(glsl::swizzle<2>(l), glsl::swizzle<0>(l), glsl::swizzle<1>(l)));
  [[maybe_unused]] glsl::Vec3 x1 = ((x0 - i1) + glsl::FloatExpr<3>(glsl::swizzle<0>(C)));
  [[maybe_unused]] glsl::Vec3 x2 = ((x0 - i2) + glsl::FloatExpr<3>(glsl::swizzle<1>(C)));
  [[maybe_unused]] glsl::Vec3 x3 = (x0 - glsl::FloatExpr<3>(glsl::swizzle<1>(D)));
  [[maybe_unused]] glsl::Vec3 i = mod289_vec3(state, context, i0);
  [[maybe_unused]] glsl::Vec4 p = permute(state, context, glsl::Vec4((glsl::Vec4((permute(state, context, glsl::Vec4((glsl::Vec4((permute(state, context, (glsl::swizzle<2>(i) + glsl::FloatExpr<4>(static_cast<float>(0.0), glsl::swizzle<2>(i1), glsl::swizzle<2>(i2), static_cast<float>(1.0)))) + glsl::swizzle<1>(i))) + glsl::FloatExpr<4>(static_cast<float>(0.0), glsl::swizzle<1>(i1), glsl::swizzle<1>(i2), static_cast<float>(1.0))))) + glsl::swizzle<0>(i))) + glsl::FloatExpr<4>(static_cast<float>(0.0), glsl::swizzle<0>(i1), glsl::swizzle<0>(i2), static_cast<float>(1.0)))));
  [[maybe_unused]] double n_ = static_cast<float>(0.14285714285714285);
  [[maybe_unused]] glsl::Vec3 ns = ((n_ * glsl::FloatExpr<3>(glsl::swizzle<3>(D), glsl::swizzle<1>(D), glsl::swizzle<2>(D))) - glsl::FloatExpr<3>(glsl::swizzle<0>(D), glsl::swizzle<2>(D), glsl::swizzle<0>(D)));
  [[maybe_unused]] glsl::Vec4 j = glsl::Vec4((p - glsl::Vec4((static_cast<float>(49.0) * glsl::floor(((p * glsl::swizzle<2>(ns)) * glsl::swizzle<2>(ns)))))));
  [[maybe_unused]] glsl::Vec4 x_ = glsl::floor((j * glsl::swizzle<2>(ns)));
  [[maybe_unused]] glsl::Vec4 y_ = glsl::floor((j - (static_cast<float>(7.0) * x_)));
  [[maybe_unused]] glsl::Vec4 x = ((x_ * glsl::swizzle<0>(ns)) + glsl::swizzle<1>(ns));
  [[maybe_unused]] glsl::Vec4 y = ((y_ * glsl::swizzle<0>(ns)) + glsl::swizzle<1>(ns));
  [[maybe_unused]] glsl::Vec4 h = glsl::Vec4((glsl::Vec4((static_cast<float>(1.0) - glsl::abs(x))) - glsl::abs(y)));
  [[maybe_unused]] glsl::Vec4 b0 = glsl::FloatExpr<4>(glsl::swizzle<0>(x), glsl::swizzle<1>(x), glsl::swizzle<0>(y), glsl::swizzle<1>(y));
  [[maybe_unused]] glsl::Vec4 b1 = glsl::FloatExpr<4>(glsl::swizzle<2>(x), glsl::swizzle<3>(x), glsl::swizzle<2>(y), glsl::swizzle<3>(y));
  [[maybe_unused]] glsl::Vec4 s0 = glsl::Vec4((glsl::Vec4((glsl::floor(b0) * static_cast<float>(2.0))) + static_cast<float>(1.0)));
  [[maybe_unused]] glsl::Vec4 s1 = glsl::Vec4((glsl::Vec4((glsl::floor(b1) * static_cast<float>(2.0))) + static_cast<float>(1.0)));
  [[maybe_unused]] glsl::Vec4 sh = (-glsl::step(h, glsl::FloatExpr<4>(static_cast<float>(0.0))));
  [[maybe_unused]] glsl::Vec4 a0 = (glsl::FloatExpr<4>(glsl::swizzle<0>(b0), glsl::swizzle<2>(b0), glsl::swizzle<1>(b0), glsl::swizzle<3>(b0)) + (glsl::FloatExpr<4>(glsl::swizzle<0>(s0), glsl::swizzle<2>(s0), glsl::swizzle<1>(s0), glsl::swizzle<3>(s0)) * glsl::FloatExpr<4>(glsl::swizzle<0>(sh), glsl::swizzle<0>(sh), glsl::swizzle<1>(sh), glsl::swizzle<1>(sh))));
  [[maybe_unused]] glsl::Vec4 a1 = (glsl::FloatExpr<4>(glsl::swizzle<0>(b1), glsl::swizzle<2>(b1), glsl::swizzle<1>(b1), glsl::swizzle<3>(b1)) + (glsl::FloatExpr<4>(glsl::swizzle<0>(s1), glsl::swizzle<2>(s1), glsl::swizzle<1>(s1), glsl::swizzle<3>(s1)) * glsl::FloatExpr<4>(glsl::swizzle<2>(sh), glsl::swizzle<2>(sh), glsl::swizzle<3>(sh), glsl::swizzle<3>(sh))));
  [[maybe_unused]] glsl::Vec3 g0 = glsl::FloatExpr<3>(glsl::swizzle<0>(a0), glsl::swizzle<1>(a0), glsl::swizzle<0>(h));
  [[maybe_unused]] glsl::Vec3 g1 = glsl::FloatExpr<3>(glsl::swizzle<2>(a0), glsl::swizzle<3>(a0), glsl::swizzle<1>(h));
  [[maybe_unused]] glsl::Vec3 g2 = glsl::FloatExpr<3>(glsl::swizzle<0>(a1), glsl::swizzle<1>(a1), glsl::swizzle<2>(h));
  [[maybe_unused]] glsl::Vec3 g3 = glsl::FloatExpr<3>(glsl::swizzle<2>(a1), glsl::swizzle<3>(a1), glsl::swizzle<3>(h));
  [[maybe_unused]] glsl::Vec4 norm = taylor_inv_sqrt(state, context, glsl::FloatExpr<4>(glsl::dot(g0, g0), glsl::dot(g1, g1), glsl::dot(g2, g2), glsl::dot(g3, g3)));
  [[maybe_unused]] glsl::Vec3 g0n = (g0 * glsl::swizzle<0>(norm));
  [[maybe_unused]] glsl::Vec3 g1n = (g1 * glsl::swizzle<1>(norm));
  [[maybe_unused]] glsl::Vec3 g2n = (g2 * glsl::swizzle<2>(norm));
  [[maybe_unused]] glsl::Vec3 g3n = (g3 * glsl::swizzle<3>(norm));
  [[maybe_unused]] double m0 = glsl::component_max((static_cast<double>(static_cast<float>(0.6)) - static_cast<double>(glsl::dot(x0, x0))), static_cast<float>(0.0));
  [[maybe_unused]] double m1 = glsl::component_max((static_cast<double>(static_cast<float>(0.6)) - static_cast<double>(glsl::dot(x1, x1))), static_cast<float>(0.0));
  [[maybe_unused]] double m2 = glsl::component_max((static_cast<double>(static_cast<float>(0.6)) - static_cast<double>(glsl::dot(x2, x2))), static_cast<float>(0.0));
  [[maybe_unused]] double m3 = glsl::component_max((static_cast<double>(static_cast<float>(0.6)) - static_cast<double>(glsl::dot(x3, x3))), static_cast<float>(0.0));
  [[maybe_unused]] double m0sq = (static_cast<double>(m0) * static_cast<double>(m0));
  [[maybe_unused]] double m1sq = (static_cast<double>(m1) * static_cast<double>(m1));
  [[maybe_unused]] double m2sq = (static_cast<double>(m2) * static_cast<double>(m2));
  [[maybe_unused]] double m3sq = (static_cast<double>(m3) * static_cast<double>(m3));
  return (static_cast<double>(static_cast<float>(42.0)) * static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>((static_cast<double>(m0sq) * static_cast<double>(m0sq))) * static_cast<double>(glsl::dot(g0n, x0)))) + static_cast<double>((static_cast<double>((static_cast<double>(m1sq) * static_cast<double>(m1sq))) * static_cast<double>(glsl::dot(g1n, x1)))))) + static_cast<double>((static_cast<double>((static_cast<double>(m2sq) * static_cast<double>(m2sq))) * static_cast<double>(glsl::dot(g2n, x2)))))) + static_cast<double>((static_cast<double>((static_cast<double>(m3sq) * static_cast<double>(m3sq))) * static_cast<double>(glsl::dot(g3n, x3)))))));
}

[[nodiscard]] double singularity_mask([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec2 uv, [[maybe_unused]] double width, [[maybe_unused]] double height) noexcept {
  if ((width <= static_cast<float>(0.0)) || (height <= static_cast<float>(0.0))) {
    return static_cast<float>(0.0);
  }
  [[maybe_unused]] glsl::Vec2 delta = glsl::abs((uv - glsl::FloatExpr<2>(static_cast<float>(0.5), static_cast<float>(0.5))));
  [[maybe_unused]] double aspect = (static_cast<double>(width) / static_cast<double>(height));
  [[maybe_unused]] glsl::Vec2 scaled = glsl::FloatExpr<2>((static_cast<double>(glsl::swizzle<0>(delta)) * static_cast<double>(aspect)), glsl::swizzle<1>(delta));
  [[maybe_unused]] double max_radius = glsl::length(glsl::FloatExpr<2>((static_cast<double>(aspect) * static_cast<double>(static_cast<float>(0.5))), static_cast<float>(0.5)));
  if (max_radius <= static_cast<float>(0.0)) {
    return static_cast<float>(0.0);
  }
  [[maybe_unused]] double normalized = glsl::clamp((static_cast<double>(glsl::length(scaled)) / static_cast<double>(max_radius)), static_cast<float>(0.0), static_cast<float>(1.0));
  [[maybe_unused]] double masked = glsl::sqrt(normalized);
  return glsl::pow(masked, static_cast<float>(5.0));
}

[[nodiscard]] glsl::Vec4 taylor_inv_sqrt([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 r) noexcept {
  return (static_cast<float>(1.79284291400159) - (static_cast<float>(0.85373472095314) * r));
}

[[nodiscard]] double warped_channel_value([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::uint32_t channel, [[maybe_unused]] glsl::UVec2 coord, [[maybe_unused]] glsl::Vec2 base_pos, [[maybe_unused]] double width, [[maybe_unused]] double height, [[maybe_unused]] glsl::Vec2 freq, [[maybe_unused]] double displacement, [[maybe_unused]] double mask, [[maybe_unused]] double time, [[maybe_unused]] double speed) noexcept {
  const double TAU = static_cast<float>(6.28318530717958647692);
  [[maybe_unused]] double noise_value = compute_noise_value(state, context, coord, width, height, freq, time, speed, channel);
  [[maybe_unused]] double centered = (static_cast<double>((static_cast<double>((static_cast<double>(noise_value) * static_cast<double>(static_cast<float>(2.0)))) - static_cast<double>(static_cast<float>(1.0)))) * static_cast<double>(mask));
  [[maybe_unused]] double angle = (static_cast<double>(centered) * static_cast<double>(TAU));
  [[maybe_unused]] glsl::Vec2 offset = ((glsl::FloatExpr<2>(glsl::cos(angle), glsl::sin(angle)) * displacement) * glsl::FloatExpr<2>(glsl::swizzle<0>(state.resolution), glsl::swizzle<1>(state.resolution)));
  [[maybe_unused]] double dirRad = (static_cast<double>((static_cast<double>(state.direction) * static_cast<double>(TAU))) / static_cast<double>(static_cast<float>(360.0)));
  [[maybe_unused]] double dc = glsl::cos(dirRad);
  [[maybe_unused]] double ds = glsl::sin(dirRad);
  offset = glsl::Vec2(glsl::FloatExpr<2>((static_cast<double>((static_cast<double>(glsl::swizzle<0>(offset)) * static_cast<double>(dc))) - static_cast<double>((static_cast<double>(glsl::swizzle<1>(offset)) * static_cast<double>(ds)))), (static_cast<double>((static_cast<double>(glsl::swizzle<0>(offset)) * static_cast<double>(ds))) + static_cast<double>((static_cast<double>(glsl::swizzle<1>(offset)) * static_cast<double>(dc))))));
  [[maybe_unused]] glsl::Vec2 sample_pos = (base_pos + offset);
  [[maybe_unused]] glsl::Vec4 sampled = sample_bilinear(state, context, sample_pos, glsl::swizzle<0>(state.resolution), glsl::swizzle<1>(state.resolution));
  if (channel == std::uint32_t(0)) {
    return glsl::swizzle<0>(sampled);
  }
  if (channel == std::uint32_t(1)) {
    return glsl::swizzle<1>(sampled);
  }
  if (channel == std::uint32_t(2)) {
    return glsl::swizzle<2>(sampled);
  }
  return glsl::swizzle<3>(sampled);
}

[[nodiscard]] double wrap_float([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] double value, [[maybe_unused]] double limit) noexcept {
  if (limit <= static_cast<float>(0.0)) {
    return static_cast<float>(0.0);
  }
  [[maybe_unused]] double result = (static_cast<double>(value) - static_cast<double>((static_cast<double>(glsl::floor((static_cast<double>(value) / static_cast<double>(limit)))) * static_cast<double>(limit))));
  if (result < static_cast<float>(0.0)) {
    result = (static_cast<double>(result) + static_cast<double>(limit));
  }
  return result;
}

[[nodiscard]] std::int32_t wrap_index([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] std::int32_t value, [[maybe_unused]] std::int32_t limit) noexcept {
  if (limit <= std::int32_t(0)) {
    return std::int32_t(0);
  }
  [[maybe_unused]] std::int32_t wrapped = glsl::integer_mod(value, limit);
  if (wrapped < std::int32_t(0)) {
    wrapped = (wrapped + limit);
  }
  return wrapped;
}

void pixel(const KernelState& kernel_base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {
  const auto& state = static_cast<const State&>(kernel_base);
  (void)state;
  (void)context;
  [[maybe_unused]] glsl::UVec3 global_id = glsl::UVec3(glsl::detail::float_to_uint32(glsl::swizzle<0>(context.frag_coord)), glsl::detail::float_to_uint32(glsl::swizzle<1>(context.frag_coord)), std::uint32_t(0));
  [[maybe_unused]] std::uint32_t width = as_u32(state, context, glsl::swizzle<0>(state.resolution));
  [[maybe_unused]] std::uint32_t height = as_u32(state, context, glsl::swizzle<1>(state.resolution));
  if ((glsl::swizzle<0>(global_id) >= width) || (glsl::swizzle<1>(global_id) >= height)) {
    return;
  }
  [[maybe_unused]] glsl::Vec2 coords = glsl::Vec2(glsl::detail::glsl_int_cast(glsl::swizzle<0>(global_id)), glsl::detail::glsl_int_cast(glsl::swizzle<1>(global_id)));
  [[maybe_unused]] glsl::Vec4 original = fetch_texel(*state.inputTex, glsl::IVec2(coords));
  if (state.displacement == static_cast<float>(0.0)) {
    output = glsl::Vec4(original);
    return;
  }
  [[maybe_unused]] glsl::Vec2 fullRes = ((glsl::swizzle<0>(state.fullResolution) > static_cast<float>(0.0)) ? glsl::Vec2(state.fullResolution) : glsl::Vec2(state.resolution));
  [[maybe_unused]] double width_f = glsl::swizzle<0>(fullRes);
  [[maybe_unused]] double height_f = glsl::swizzle<1>(fullRes);
  [[maybe_unused]] glsl::Vec2 uv = ((glsl::FloatExpr<2>((static_cast<double>(float(glsl::swizzle<0>(global_id))) + static_cast<double>(glsl::swizzle<0>(state.tileOffset))), (static_cast<double>(float(glsl::swizzle<1>(global_id))) + static_cast<double>(glsl::swizzle<1>(state.tileOffset)))) + glsl::FloatExpr<2>(static_cast<float>(0.5), static_cast<float>(0.5))) / glsl::FloatExpr<2>(glsl::component_max(width_f, static_cast<float>(1.0)), glsl::component_max(height_f, static_cast<float>(1.0))));
  [[maybe_unused]] double mask = singularity_mask(state, context, uv, width_f, height_f);
  if (mask <= static_cast<float>(0.0)) {
    output = glsl::Vec4(original);
    return;
  }
  [[maybe_unused]] double renderScale = ((glsl::swizzle<0>(state.fullResolution) > static_cast<float>(0.0)) ? (static_cast<double>(glsl::swizzle<0>(state.fullResolution)) / static_cast<double>(glsl::component_max(glsl::swizzle<0>(state.resolution), static_cast<float>(1.0)))) : static_cast<float>(1.0));
  [[maybe_unused]] bool isTiling = (renderScale > static_cast<float>(1.01));
  [[maybe_unused]] double maxOffsetPixels = (isTiling ? static_cast<float>(256.0) : glsl::component_max(glsl::swizzle<0>(state.resolution), glsl::swizzle<1>(state.resolution)));
  [[maybe_unused]] double maxAllowedDisplacement = (static_cast<double>(maxOffsetPixels) / static_cast<double>(glsl::component_max(glsl::swizzle<0>(state.resolution), static_cast<float>(1.0))));
  [[maybe_unused]] double clampedDisplacement = glsl::component_min(state.displacement, maxAllowedDisplacement);
  [[maybe_unused]] glsl::Vec2 freq = freq_for_shape(state, context, static_cast<float>(2.0), width_f, height_f);
  [[maybe_unused]] glsl::Vec2 base_pos = glsl::FloatExpr<2>(float(glsl::swizzle<0>(global_id)), float(glsl::swizzle<1>(global_id)));
  [[maybe_unused]] glsl::Vec2 globalCoordVec = (glsl::FloatExpr<2>(float(glsl::swizzle<0>(global_id)), float(glsl::swizzle<1>(global_id))) + state.tileOffset);
  [[maybe_unused]] glsl::UVec2 coord = glsl::UVec2(globalCoordVec);
  [[maybe_unused]] double red = warped_channel_value(state, context, std::uint32_t(0), coord, base_pos, width_f, height_f, freq, clampedDisplacement, mask, state.time, state.speed);
  [[maybe_unused]] double green = warped_channel_value(state, context, std::uint32_t(1), coord, base_pos, width_f, height_f, freq, clampedDisplacement, mask, state.time, state.speed);
  [[maybe_unused]] double blue = warped_channel_value(state, context, std::uint32_t(2), coord, base_pos, width_f, height_f, freq, clampedDisplacement, mask, state.time, state.speed);
  [[maybe_unused]] double alpha = clamp01(state, context, glsl::swizzle<3>(original));
  output = glsl::Vec4(glsl::FloatExpr<4>(red, green, blue, alpha));
}
}  // namespace typed_42

BoundKernel bind_filter_degauss_degauss(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_42::State>(&bindings.texture("inputTex"), bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("time"), bindings.get_number("displacement"), bindings.get_number("speed"), bindings.get<std::int32_t>("seed"), bindings.get_number("direction"));
  (void)bindings;
  return BoundKernel(state, &typed_42::pixel);
}
// Typed IR program: filter/scale:scale
// Source SHA-256: a45f000ee12c498d7a11a04ecc56e911c9fc804ad9cde60cc7cea47533a19ce3
namespace typed_125 {
struct State final : KernelState {
  State(glsl::Vec2 resolution_value, glsl::Vec2 tileOffset_value, glsl::Vec2 fullResolution_value, double aspect_value, double scaleX_value, double scaleY_value, double centerX_value, double centerY_value, std::int32_t wrap_value, const Surface* inputTex_value) : resolution(resolution_value), tileOffset(tileOffset_value), fullResolution(fullResolution_value), aspect(aspect_value), scaleX(scaleX_value), scaleY(scaleY_value), centerX(centerX_value), centerY(centerY_value), wrap(wrap_value), inputTex(inputTex_value) {}
  glsl::Vec2 resolution;
  glsl::Vec2 tileOffset;
  glsl::Vec2 fullResolution;
  double aspect;
  double scaleX;
  double scaleY;
  double centerX;
  double centerY;
  std::int32_t wrap;
  const Surface* inputTex;
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
  [[maybe_unused]] glsl::Vec2 st = (globalCoord / state.fullResolution);
  [[maybe_unused]] glsl::Vec2 c = glsl::FloatExpr<2>((-state.centerX), state.centerY);
  st = glsl::Vec2((st - c));
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) * state.aspect));
  st = glsl::Vec2((st / glsl::FloatExpr<2>(state.scaleX, state.scaleY)));
  glsl::set_swizzle<0>(st, (glsl::swizzle<0>(st) / state.aspect));
  st = glsl::Vec2((st + c));
  [[maybe_unused]] glsl::Vec2 localUV = (((st * state.fullResolution) - state.tileOffset) / state.resolution);
  if (state.wrap == std::int32_t(0)) {
    localUV = glsl::Vec2(glsl::abs(glsl::Vec2((glsl::mod((localUV + static_cast<float>(1.0)), static_cast<float>(2.0)) - static_cast<float>(1.0)))));
  } else {
    if (state.wrap == std::int32_t(1)) {
      localUV = glsl::Vec2(glsl::fract(localUV));
    } else {
      localUV = glsl::Vec2(glsl::clamp(localUV, static_cast<float>(0.0), static_cast<float>(1.0)));
    }
  }
  output = glsl::Vec4(glsl::Vec4(glsl::swizzle<0, 1, 2>(sample_texture(*state.inputTex, localUV)), static_cast<float>(1.0)));
}
}  // namespace typed_125

BoundKernel bind_filter_scale_scale(const glsl::Bindings& bindings) {
  const auto state = std::make_shared<typed_125::State>(bindings.get<glsl::Vec2>("resolution"), bindings.get<glsl::Vec2>("tileOffset"), bindings.get<glsl::Vec2>("fullResolution"), bindings.get_number("aspect"), bindings.get_number("scaleX"), bindings.get_number("scaleY"), bindings.get_number("centerX"), bindings.get_number("centerY"), bindings.get<std::int32_t>("wrap"), &bindings.texture("inputTex"));
  (void)bindings;
  return BoundKernel(state, &typed_125::pixel);
}
}  // namespace noisemaker::historical_generated::authority_26d6f42
