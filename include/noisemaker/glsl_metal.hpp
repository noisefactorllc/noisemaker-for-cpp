#pragma once

// GLSL float division by a run-time divisor, as the CPU authority's kernel
// generator lowers it (scripts/upstream/compile-glsl.js): every lane becomes
// `$runtime.fdiv(a, b)`, the Metal division of noisemaker/metal_division.hpp.
//
// These overloads mirror `operator/` in glsl_types.hpp lane for lane. Only the
// lane operation changes: a scalar result stays an unrounded double, a
// float-lane vector result stays a deferred FloatExpr that rounds when it is
// materialized, and a double-lane vector result keeps unrounded lanes. The
// emitter chooses Metal division only at the call sites that the authority
// routes to `$runtime.fdiv` (tools/glslcpp/frontend/metal_division.py).

#include <array>
#include <cstddef>

#include "noisemaker/glsl_types.hpp"
#include "noisemaker/metal_division.hpp"

namespace noisemaker::glsl {

[[nodiscard]] inline double metal_divide(double a, double b) noexcept {
  return noisemaker::metal::metal_divide(a, b);
}

template <std::size_t N>
[[nodiscard]] FloatExpr<N> metal_divide(const FloatExpr<N>& a, const FloatExpr<N>& b) noexcept {
  std::array<double, N> lanes{};
  for (std::size_t i = 0; i < N; ++i) lanes[i] = noisemaker::metal::metal_divide(a[i], b[i]);
  return make_float_expr(lanes);
}
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, float>& a, const Vec<N, float>& b) noexcept { return metal_divide(float_expr(a), float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, float>& a, const FloatExpr<N>& b) noexcept { return metal_divide(float_expr(a), b); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const FloatExpr<N>& a, const Vec<N, float>& b) noexcept { return metal_divide(a, float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const FloatExpr<N>& a, double b) noexcept { return metal_divide(a, FloatExpr<N>(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(double a, const FloatExpr<N>& b) noexcept { return metal_divide(FloatExpr<N>(a), b); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, float>& a, double b) noexcept { return metal_divide(float_expr(a), FloatExpr<N>(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(double a, const Vec<N, float>& b) noexcept { return metal_divide(FloatExpr<N>(a), float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, double>& a, const Vec<N, float>& b) noexcept { return metal_divide(float_expr(a), float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, float>& a, const Vec<N, double>& b) noexcept { return metal_divide(float_expr(a), float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, double>& a, const FloatExpr<N>& b) noexcept { return metal_divide(float_expr(a), b); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const FloatExpr<N>& a, const Vec<N, double>& b) noexcept { return metal_divide(a, float_expr(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(const Vec<N, double>& a, double b) noexcept { return metal_divide(float_expr(a), FloatExpr<N>(b)); }
template <std::size_t N> [[nodiscard]] FloatExpr<N> metal_divide(double a, const Vec<N, double>& b) noexcept { return metal_divide(FloatExpr<N>(a), float_expr(b)); }
// Two double-lane vectors: the authority's plain-array lanes stay unrounded.
template <std::size_t N>
[[nodiscard]] Vec<N, double> metal_divide(const Vec<N, double>& a, const Vec<N, double>& b) noexcept {
  Vec<N, double> result;
  for (std::size_t i = 0; i < N; ++i) result[i] = noisemaker::metal::metal_divide(a[i], b[i]);
  return result;
}

}  // namespace noisemaker::glsl
