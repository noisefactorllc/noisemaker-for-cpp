#pragma once

#include <cassert>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <variant>
#include <vector>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/glsl_types.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker::glsl {
[[nodiscard]] float mod(double x, double y) noexcept;
[[nodiscard]] float fract(double x) noexcept;
[[nodiscard]] double round(double x) noexcept;
[[nodiscard]] inline std::uint32_t pack_half2x16(
    const Vec2& value) noexcept {
  const std::uint32_t low = noisemaker::float_to_half_rte(value[0]);
  const std::uint32_t high = noisemaker::float_to_half_rte(value[1]);
  return low | (high << 16U);
}
[[nodiscard]] inline Vec2 unpack_half2x16(std::uint32_t value) noexcept {
  return Vec2(
      noisemaker::half_to_float(static_cast<std::uint16_t>(value)),
      noisemaker::half_to_float(static_cast<std::uint16_t>(value >> 16U)));
}

namespace detail {
template <std::size_t N, class Function>
[[nodiscard]] inline Vec<N, float> map_float(const Vec<N, float>& value, Function function) {
  Vec<N, float> result;
  for (std::size_t lane = 0; lane < N; ++lane) result[lane] = noisemaker::f32(function(static_cast<double>(value[lane])));
  return result;
}
template <std::size_t N, class Function>
[[nodiscard]] inline Vec<N, float> map_float2(const Vec<N, float>& a, const Vec<N, float>& b, Function function) {
  Vec<N, float> result;
  for (std::size_t lane = 0; lane < N; ++lane)
    result[lane] = noisemaker::f32(function(static_cast<double>(a[lane]), static_cast<double>(b[lane])));
  return result;
}
}  // namespace detail

[[nodiscard]] inline float abs(double value) { return noisemaker::f32(std::fabs(value)); }
[[nodiscard]] inline float atan(double value) { return noisemaker::f32(std::atan(value)); }
[[nodiscard]] inline float atan(double y, double x) { return noisemaker::f32(std::atan2(y, x)); }
// cos/exp/sin/tanh route through noisemaker::fdlibm — a bit-exact port of the
// fdlibm routines V8 itself uses for Math.cos/exp/sin/tanh (V8's
// src/base/ieee754.cc), rather than the platform std:: implementation.
// std:: is "accurate" but not required to be correctly-rounded and measurably
// disagrees with V8 in the last bit on a large fraction of doubles (measured:
// tanh 4.27%, exp 5.81%, sin 2.71%, cos 2.64% divergent over a 403k-point
// adversarial sweep — see noisemaker-for-cpp-sdd/fdlibm/fdlibm-report.md).
// The fdlibm port reduces that to 0.008%-0.39% (worst case 3 ULP) under this
// project's mandatory -ffp-contract=off; see the report for the diagnosed
// root cause of that residual (traced to V8's own binary containing
// FMA-contracted arithmetic on FMA-capable hardware, not a port defect) and
// why hand-placed std::fma() was deliberately not used to chase it further.
// Math.ceil and std::ceil agree on every finite double, so this needs no
// fdlibm shim -- unlike cos/exp/sin/tanh above.
[[nodiscard]] inline float ceil(double value) { return noisemaker::f32(std::ceil(value)); }
[[nodiscard]] inline float cos(double value) { return noisemaker::f32(noisemaker::fdlibm::cos(value)); }
[[nodiscard]] inline float exp(double value) { return noisemaker::f32(noisemaker::fdlibm::exp(value)); }
[[nodiscard]] inline float floor(double value) { return noisemaker::f32(std::floor(value)); }
[[nodiscard]] inline float pow(double base, double exponent) { return noisemaker::f32(std::pow(base, exponent)); }
[[nodiscard]] inline float radians(double degrees) { return noisemaker::f32(degrees * 0.017453292519943295); }
[[nodiscard]] inline float sign(double value) {
  return value > 0.0 ? 1.0f : (value < 0.0 ? -1.0f : 0.0f);
}
[[nodiscard]] inline float sin(double value) { return noisemaker::f32(noisemaker::fdlibm::sin(value)); }
[[nodiscard]] inline float sqrt(double value) { return noisemaker::f32(std::sqrt(value)); }
// GLSL's inversesqrt follows the CPU oracle's unary adapter: evaluate the
// reciprocal in JavaScript Number precision, then materialize the float.
[[nodiscard]] inline float inversesqrt(double value) {
  return noisemaker::f32(1.0 / std::sqrt(value));
}
[[nodiscard]] inline float tanh(double value) { return noisemaker::f32(noisemaker::fdlibm::tanh(value)); }

#define NOISEMAKER_GLSL_UNARY_VECTOR(name) \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const Vec<N,float>& value) { return detail::map_float(value, [](double lane) { return glsl::name(lane); }); } \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const FloatExpr<N>& value) { return glsl::name(Vec<N,float>(value)); }
NOISEMAKER_GLSL_UNARY_VECTOR(abs)
NOISEMAKER_GLSL_UNARY_VECTOR(atan)
NOISEMAKER_GLSL_UNARY_VECTOR(cos)
NOISEMAKER_GLSL_UNARY_VECTOR(exp)
NOISEMAKER_GLSL_UNARY_VECTOR(floor)
NOISEMAKER_GLSL_UNARY_VECTOR(radians)
NOISEMAKER_GLSL_UNARY_VECTOR(sign)
NOISEMAKER_GLSL_UNARY_VECTOR(sin)
NOISEMAKER_GLSL_UNARY_VECTOR(sqrt)
#undef NOISEMAKER_GLSL_UNARY_VECTOR

template <std::size_t N> [[nodiscard]] inline Vec<N,float> fract(const Vec<N,float>& value) { return detail::map_float(value, [](double lane) { const float consumed=noisemaker::f32(lane); return static_cast<double>(consumed)-std::floor(static_cast<double>(consumed)); }); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> fract(const FloatExpr<N>& value) { return fract(Vec<N,float>(value)); }
template <std::size_t N> requires(N == 2) [[nodiscard]] inline Vec<N,float> mod(const Vec<N,float>& a,const Vec<N,float>& b) { return detail::map_float2(a,b,[](double x,double y){return glsl::mod(x,y);}); }
template <std::size_t N> requires(N == 2) [[nodiscard]] inline Vec<N,float> mod(const Vec<N,float>& a,double b) { return detail::map_float(a,[b](double x){return glsl::mod(x,b);}); }
template <std::size_t N> requires(N == 2) [[nodiscard]] inline Vec<N,float> mod(const FloatExpr<N>& a,const Vec<N,float>& b) { return mod(Vec<N,float>(a),b); }
template <std::size_t N> requires(N == 2) Vec<N,float> mod(const Vec<N,float>&,const FloatExpr<N>&) = delete;
template <std::size_t N> requires(N == 2) Vec<N,float> mod(const FloatExpr<N>&,const FloatExpr<N>&) = delete;
template <std::size_t N> requires(N == 2) [[nodiscard]] inline Vec<N,float> mod(const FloatExpr<N>& a,double b) { return mod(Vec<N,float>(a),b); }
// Task 31 (Curl): the exact wider `mod` shapes the authorized closure invokes.
// Deliberately constrained to N == 3 || N == 4 rather than left open, matching
// the N == 2 narrowing above: only widths an authenticated profile admits are
// instantiable. These delegate to glsl::mod, i.e. x - y*floor(x/y), so GLSL
// sign-of-divisor semantics hold — do NOT substitute std::fmod.
template <std::size_t N> requires(N == 3 || N == 4) [[nodiscard]] inline Vec<N,float> mod(const Vec<N,float>& a,double b) { return detail::map_float(a,[b](double x){return glsl::mod(x,b);}); }
template <std::size_t N> requires(N == 3 || N == 4) [[nodiscard]] inline Vec<N,float> mod(const FloatExpr<N>& a,double b) { return mod(Vec<N,float>(a),b); }

// Task 31 (Curl): tanh on vec3 only, for the one authenticated call site.
//
// Two spellings, deliberately. `tanh` follows the house convention and narrows
// a FloatExpr argument to f32 first, matching what the JavaScript reference
// does when its generator materialises a Float32Array before the call.
// `tanh_lanewise` does NOT narrow the argument: it evaluates each lane's
// double operand directly and narrows only the result, matching what the JS
// reference does when its transpiler scalarises the assignment instead. The
// emitter picks the spelling per authenticated call site — see
// task-31-curl-SOLVED.md. Do not "simplify" these into one function; the
// difference is observable in the last bits of the rendered image.
template <std::size_t N> requires(N == 3) [[nodiscard]] inline Vec<N,float> tanh(const Vec<N,float>& value) { return detail::map_float(value,[](double lane){return noisemaker::fdlibm::tanh(lane);}); }
template <std::size_t N> requires(N == 3) [[nodiscard]] inline Vec<N,float> tanh(const FloatExpr<N>& value) { return tanh(Vec<N,float>(value)); }
template <std::size_t N> requires(N == 3) [[nodiscard]] inline Vec<N,float> tanh_lanewise(const FloatExpr<N>& value) { Vec<N,float> result; for (std::size_t i = 0; i < N; ++i) result[i] = glsl::tanh(value[i]); return result; }
template <std::size_t N> requires(N == 3) [[nodiscard]] inline Vec<N,float> tanh_lanewise(const Vec<N,float>& value) { return tanh(value); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const Vec<N,float>& a,const Vec<N,float>& b) { return detail::map_float2(a,b,[](double x,double y){return glsl::pow(x,y);}); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const Vec<N,float>& a,double b) { return pow(a,Vec<N,float>(noisemaker::f32(b))); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const Vec<N,float>& a,const FloatExpr<N>& b) { return pow(a,Vec<N,float>(b)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const FloatExpr<N>& a,double b) { return pow(Vec<N,float>(a),b); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const FloatExpr<N>& a,const Vec<N,float>& b) { return pow(Vec<N,float>(a),b); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> pow(const FloatExpr<N>& a,const FloatExpr<N>& b) { return pow(Vec<N,float>(a),Vec<N,float>(b)); }

template <std::size_t N> [[nodiscard]] inline float dot(const Vec<N,float>& a,const Vec<N,float>& b) { double sum=0.0; for(std::size_t i=0;i<N;++i) sum+=static_cast<double>(a[i])*b[i]; return noisemaker::f32(sum); }
template <std::size_t N> [[nodiscard]] inline float dot(const FloatExpr<N>& a,const Vec<N,float>& b) { return dot(Vec<N,float>(a),b); }
template <std::size_t N> [[nodiscard]] inline float dot(const Vec<N,float>& a,const FloatExpr<N>& b) { return dot(a,Vec<N,float>(b)); }
template <std::size_t N> [[nodiscard]] inline float dot(const FloatExpr<N>& a,const FloatExpr<N>& b) { return dot(Vec<N,float>(a),Vec<N,float>(b)); }
template <std::size_t N> [[nodiscard]] inline float length(const Vec<N,float>& value) { return noisemaker::f32(std::sqrt(static_cast<double>(dot(value,value)))); }
template <std::size_t N> [[nodiscard]] inline float length(const FloatExpr<N>& value) { return length(Vec<N,float>(value)); }
template <std::size_t N> [[nodiscard]] inline float distance(const Vec<N,float>& a,const Vec<N,float>& b) { return length(a-b); }
template <std::size_t N> [[nodiscard]] inline float distance(const FloatExpr<N>& a,const Vec<N,float>& b) { return distance(Vec<N,float>(a),b); }
template <std::size_t N> [[nodiscard]] inline float distance(const Vec<N,float>& a,const FloatExpr<N>& b) { return distance(a,Vec<N,float>(b)); }
template <std::size_t N> [[nodiscard]] inline float distance(const FloatExpr<N>& a,const FloatExpr<N>& b) { return distance(Vec<N,float>(a),Vec<N,float>(b)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> normalize(const Vec<N,float>& value) { const float vector_length=length(value);if(vector_length==0.0f)return {};Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(static_cast<double>(value[i])/static_cast<double>(vector_length));return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> normalize(const FloatExpr<N>& value) { return normalize(Vec<N,float>(value)); }
[[nodiscard]] inline Vec3 cross(const Vec3& a,const Vec3& b) { return Vec3(noisemaker::f32(static_cast<double>(a[1])*b[2]-static_cast<double>(a[2])*b[1]), noisemaker::f32(static_cast<double>(a[2])*b[0]-static_cast<double>(a[0])*b[2]), noisemaker::f32(static_cast<double>(a[0])*b[1]-static_cast<double>(a[1])*b[0])); }
[[nodiscard]] inline Vec3 cross(const FloatExpr<3>& a,const Vec3& b) { return cross(Vec3(a),b); }
[[nodiscard]] inline Vec3 cross(const Vec3& a,const FloatExpr<3>& b) { return cross(a,Vec3(b)); }
[[nodiscard]] inline Vec3 cross(const FloatExpr<3>& a,const FloatExpr<3>& b) { return cross(Vec3(a),Vec3(b)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> reflect(const Vec<N,float>& incident,const Vec<N,float>& normal) { const double scale=2.0*static_cast<double>(dot(normal,incident));Vec<N,float> result;for(std::size_t i=0;i<N;++i){const float normal_product=noisemaker::f32(static_cast<double>(normal[i])*scale);result[i]=noisemaker::f32(static_cast<double>(incident[i])-static_cast<double>(normal_product));}return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> reflect(const FloatExpr<N>& incident,const Vec<N,float>& normal) { return reflect(Vec<N,float>(incident),normal); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> reflect(const Vec<N,float>& incident,const FloatExpr<N>& normal) { return reflect(incident,Vec<N,float>(normal)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> reflect(const FloatExpr<N>& incident,const FloatExpr<N>& normal) { return reflect(Vec<N,float>(incident),Vec<N,float>(normal)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> refract(const Vec<N,float>& incident,const Vec<N,float>& normal,double eta) { const double cosine=static_cast<double>(dot(normal,incident));const double discriminant=1.0-eta*eta*(1.0-cosine*cosine);if(discriminant<0.0)return {};const double scale=eta*cosine+std::sqrt(discriminant);Vec<N,float> result;for(std::size_t i=0;i<N;++i){const float left=noisemaker::f32(eta*static_cast<double>(incident[i]));const float right=noisemaker::f32(scale*static_cast<double>(normal[i]));result[i]=noisemaker::f32(static_cast<double>(left)-static_cast<double>(right));}return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> refract(const FloatExpr<N>& incident,const Vec<N,float>& normal,double eta) { return refract(Vec<N,float>(incident),normal,eta); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> refract(const Vec<N,float>& incident,const FloatExpr<N>& normal,double eta) { return refract(incident,Vec<N,float>(normal),eta); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> refract(const FloatExpr<N>& incident,const FloatExpr<N>& normal,double eta) { return refract(Vec<N,float>(incident),Vec<N,float>(normal),eta); }

// Shape Mixer reaches these scalar/vector shapes through JavaScript's
// polymorphic helpers. Keep them named and local to that admitted closure:
// widening the generic GLSL overload set would silently authorize unrelated
// programs with observably different scalar semantics.
[[nodiscard]] inline float shape_mixer_reflect_scalar(double incident,double normal) noexcept { const float product=noisemaker::f32(normal*(+0.0));return noisemaker::f32(incident-static_cast<double>(product)); }
[[nodiscard]] inline float shape_mixer_refract_scalar(double incident,double normal,double eta) noexcept { const double discriminant=1.0-eta*eta;const float left=noisemaker::f32(incident*eta);const float right=noisemaker::f32(normal*std::sqrt(discriminant));return noisemaker::f32(static_cast<double>(left)-static_cast<double>(right)); }
[[nodiscard]] inline Vec3 shape_mixer_mod_vec3(const Vec3& x,const Vec3& y) noexcept { return Vec3(glsl::mod(x[0],y[0]),glsl::mod(x[1],y[1]),glsl::mod(x[2],y[2])); }

template <class T> [[nodiscard]] inline T component_min(T a,T b) { if constexpr(std::floating_point<T>){if(std::isnan(a)||std::isnan(b))return std::numeric_limits<T>::quiet_NaN();if(a==b&&a==static_cast<T>(0))return std::signbit(a)||std::signbit(b)?static_cast<T>(-0.0):static_cast<T>(0.0);}return b<a?b:a; }
template <class T> [[nodiscard]] inline T component_max(T a,T b) { if constexpr(std::floating_point<T>){if(std::isnan(a)||std::isnan(b))return std::numeric_limits<T>::quiet_NaN();if(a==b&&a==static_cast<T>(0))return !std::signbit(a)||!std::signbit(b)?static_cast<T>(0.0):static_cast<T>(-0.0);}return a<b?b:a; }
[[nodiscard]] inline float component_min(double a,double b) { return noisemaker::f32(component_min<double>(a,b)); }
[[nodiscard]] inline float component_min(float a,double b) { return component_min(static_cast<double>(a),b); }
[[nodiscard]] inline float component_min(double a,float b) { return component_min(a,static_cast<double>(b)); }
[[nodiscard]] inline float component_max(double a,double b) { return noisemaker::f32(component_max<double>(a,b)); }
[[nodiscard]] inline float component_max(float a,double b) { return component_max(static_cast<double>(a),b); }
[[nodiscard]] inline float component_max(double a,float b) { return component_max(a,static_cast<double>(b)); }
template <class T> requires(!std::floating_point<T>&&!detail::is_vec_v<T>&&!detail::is_float_expr_v<T>) [[nodiscard]] inline T clamp(T x,T low,T high) { return component_min(component_max(x,low),high); }
template <class T> requires(!std::floating_point<T>&&!detail::is_vec_v<T>&&!detail::is_float_expr_v<T>) [[nodiscard]] inline T mix(T x,T y,T amount) { return static_cast<T>(x*(static_cast<T>(1)-amount)+y*amount); }
template <class T> requires(!std::floating_point<T>&&!detail::is_vec_v<T>&&!detail::is_float_expr_v<T>) [[nodiscard]] inline T step(T edge,T x) { return x<edge?static_cast<T>(0):static_cast<T>(1); }
[[nodiscard]] inline float mix(double x,double y,double amount) { return noisemaker::f32(x*(1.0-amount)+y*amount); }
[[nodiscard]] inline float clamp(double x,double low,double high) { return noisemaker::f32(component_min<double>(component_max<double>(x,low),high)); }
[[nodiscard]] inline float step(double edge,double x) { return x<edge?0.0f:1.0f; }
[[nodiscard]] inline float smoothstep(double edge0,double edge1,double x) { const double t=component_min<double>(component_max<double>((x-edge0)/(edge1-edge0),0.0),1.0);return noisemaker::f32(t*t*(3.0-2.0*t)); }
template <class A,class B,class C> requires(std::is_arithmetic_v<A>&&std::is_arithmetic_v<B>&&std::is_arithmetic_v<C>&&!(std::same_as<A,B>&&std::same_as<B,C>)) [[nodiscard]] inline float mix(A x,B y,C amount) { return mix(static_cast<double>(x),static_cast<double>(y),static_cast<double>(amount)); }
template <class A,class B,class C> requires(std::is_arithmetic_v<A>&&std::is_arithmetic_v<B>&&std::is_arithmetic_v<C>&&!(std::same_as<A,B>&&std::same_as<B,C>)) [[nodiscard]] inline float clamp(A x,B low,C high) { return noisemaker::f32(component_min(static_cast<double>(component_max(static_cast<double>(x),static_cast<double>(low))),static_cast<double>(high))); }
template <class A,class B> requires(std::is_arithmetic_v<A>&&std::is_arithmetic_v<B>&&!std::same_as<A,B>) [[nodiscard]] inline float step(A edge,B x) { return static_cast<double>(x)<static_cast<double>(edge)?0.0f:1.0f; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_min(const Vec<N,T>& a,const Vec<N,T>& b) { Vec<N,T> result;for(std::size_t i=0;i<N;++i)result[i]=component_min(a[i],b[i]);return result; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_min(const Vec<N,T>& a,T b) { return component_min(a,Vec<N,T>(b)); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_min(T a,const Vec<N,T>& b) { return component_min(Vec<N,T>(a),b); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_max(const Vec<N,T>& a,const Vec<N,T>& b) { Vec<N,T> result;for(std::size_t i=0;i<N;++i)result[i]=component_max(a[i],b[i]);return result; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_max(const Vec<N,T>& a,T b) { return component_max(a,Vec<N,T>(b)); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> component_max(T a,const Vec<N,T>& b) { return component_max(Vec<N,T>(a),b); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> clamp(const Vec<N,T>& x,const Vec<N,T>& low,const Vec<N,T>& high) { return component_min(component_max(x,low),high); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> clamp(const Vec<N,T>& x,T low,T high) { return clamp(x,Vec<N,T>(low),Vec<N,T>(high)); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> mix(const Vec<N,T>& a,const Vec<N,T>& b,const Vec<N,T>& amount) { Vec<N,T> result;for(std::size_t i=0;i<N;++i)result[i]=mix(a[i],b[i],amount[i]);return result; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> mix(const Vec<N,T>& a,const Vec<N,T>& b,T amount) { return mix(a,b,Vec<N,T>(amount)); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> step(const Vec<N,T>& edge,const Vec<N,T>& x) { Vec<N,T> result;for(std::size_t i=0;i<N;++i)result[i]=step(edge[i],x[i]);return result; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> step(T edge,const Vec<N,T>& x) { return step(Vec<N,T>(edge),x); }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> smoothstep(const Vec<N,T>& edge0,const Vec<N,T>& edge1,const Vec<N,T>& x) { Vec<N,T> result;for(std::size_t i=0;i<N;++i)result[i]=smoothstep(edge0[i],edge1[i],x[i]);return result; }
template <std::size_t N,class T> [[nodiscard]] inline Vec<N,T> smoothstep(T edge0,T edge1,const Vec<N,T>& x) { return smoothstep(Vec<N,T>(edge0),Vec<N,T>(edge1),x); }

template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_min(const Vec<N,float>& a,double b) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(component_min(static_cast<double>(a[i]),b));return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_min(double a,const Vec<N,float>& b) { return component_min(b,a); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_max(const Vec<N,float>& a,double b) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(component_max(static_cast<double>(a[i]),b));return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_max(double a,const Vec<N,float>& b) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(component_max(a,static_cast<double>(b[i])));return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> clamp(const Vec<N,float>& x,double low,double high) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(clamp(static_cast<double>(x[i]),low,high));return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const Vec<N,float>& a,const Vec<N,float>& b,double amount) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(static_cast<double>(a[i])*(1.0-amount)+static_cast<double>(b[i])*amount);return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const Vec<N,float>& a,const Vec<N,float>& b,float amount) { return mix(a,b,static_cast<double>(amount)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> step(double edge,const Vec<N,float>& x) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=static_cast<double>(x[i])<edge?0.0f:1.0f;return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> smoothstep(double edge0,double edge1,const Vec<N,float>& x) { Vec<N,float> result;for(std::size_t i=0;i<N;++i)result[i]=noisemaker::f32(smoothstep(edge0,edge1,static_cast<double>(x[i])));return result; }

template <std::size_t N> [[nodiscard]] inline Vec<N,float> materialize(const Vec<N,float>& value) { return value; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> materialize(const FloatExpr<N>& value) { return Vec<N,float>(value); }
#define NOISEMAKER_GLSL_EXPR_BINARY_HELPER(name) \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const FloatExpr<N>& a,const Vec<N,float>& b) { return name(materialize(a),b); } \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const Vec<N,float>& a,const FloatExpr<N>& b) { return name(a,materialize(b)); } \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const FloatExpr<N>& a,const FloatExpr<N>& b) { return name(materialize(a),materialize(b)); } \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(const FloatExpr<N>& a,float b) { return name(materialize(a),b); } \
template <std::size_t N> [[nodiscard]] inline Vec<N,float> name(float a,const FloatExpr<N>& b) { return name(a,materialize(b)); }
NOISEMAKER_GLSL_EXPR_BINARY_HELPER(component_min)
NOISEMAKER_GLSL_EXPR_BINARY_HELPER(component_max)
#undef NOISEMAKER_GLSL_EXPR_BINARY_HELPER
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_min(const FloatExpr<N>& a,double b) { return component_min(materialize(a),b); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_min(double a,const FloatExpr<N>& b) { return component_min(a,materialize(b)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_max(const FloatExpr<N>& a,double b) { return component_max(materialize(a),b); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> component_max(double a,const FloatExpr<N>& b) { return component_max(a,materialize(b)); }

template <class A, class B, class C> requires((detail::is_float_vec_v<A>||detail::is_float_expr_v<A>)&&(detail::is_float_vec_v<B>||detail::is_float_expr_v<B>)&&(detail::is_float_vec_v<C>||detail::is_float_expr_v<C>)&&(detail::lane_count_v<A> == detail::lane_count_v<B>)&&(detail::lane_count_v<A> == detail::lane_count_v<C>)&&(detail::is_float_expr_v<A>||detail::is_float_expr_v<B>||detail::is_float_expr_v<C>)) [[nodiscard]] inline auto clamp(const A& x,const B& low,const C& high) -> Vec<detail::lane_count_v<A>,float> { return clamp(materialize(x),materialize(low),materialize(high)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> clamp(const FloatExpr<N>& x,float low,float high) { return clamp(materialize(x),low,high); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> clamp(const FloatExpr<N>& x,double low,double high) { return clamp(materialize(x),low,high); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> clamp(const Vec<N,float>& x,const FloatExpr<N>& low,float high) { return clamp(x,materialize(low),Vec<N,float>(high)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> clamp(const Vec<N,float>& x,float low,const FloatExpr<N>& high) { return clamp(x,Vec<N,float>(low),materialize(high)); }

template <class A, class B, class C> requires((detail::is_float_vec_v<A>||detail::is_float_expr_v<A>)&&(detail::is_float_vec_v<B>||detail::is_float_expr_v<B>)&&(detail::is_float_vec_v<C>||detail::is_float_expr_v<C>)&&(detail::lane_count_v<A> == detail::lane_count_v<B>)&&(detail::lane_count_v<A> == detail::lane_count_v<C>)&&(detail::is_float_expr_v<A>||detail::is_float_expr_v<B>||detail::is_float_expr_v<C>)) [[nodiscard]] inline auto mix(const A& a,const B& b,const C& amount) -> Vec<detail::lane_count_v<A>,float> { return mix(materialize(a),materialize(b),materialize(amount)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const FloatExpr<N>& a,const Vec<N,float>& b,float amount) { return mix(materialize(a),b,amount); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const Vec<N,float>& a,const FloatExpr<N>& b,float amount) { return mix(a,materialize(b),amount); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const Vec<N,float>& a,const Vec<N,float>& b,const FloatExpr<N>& amount) { return mix(a,b,materialize(amount)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const FloatExpr<N>& a,const Vec<N,float>& b,double amount) { return mix(materialize(a),b,amount); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const Vec<N,float>& a,const FloatExpr<N>& b,double amount) { return mix(a,materialize(b),amount); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> mix(const FloatExpr<N>& a,const FloatExpr<N>& b,double amount) { return mix(materialize(a),materialize(b),amount); }

template <class A, class B> requires((detail::is_float_vec_v<A>||detail::is_float_expr_v<A>)&&(detail::is_float_vec_v<B>||detail::is_float_expr_v<B>)&&(detail::lane_count_v<A> == detail::lane_count_v<B>)&&(detail::is_float_expr_v<A>||detail::is_float_expr_v<B>)) [[nodiscard]] inline auto step(const A& edge,const B& x) -> Vec<detail::lane_count_v<A>,float> { return step(materialize(edge),materialize(x)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> step(float edge,const FloatExpr<N>& x) { return step(edge,materialize(x)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> step(double edge,const FloatExpr<N>& x) { return step(edge,materialize(x)); }

template <class A, class B, class C> requires((detail::is_float_vec_v<A>||detail::is_float_expr_v<A>)&&(detail::is_float_vec_v<B>||detail::is_float_expr_v<B>)&&(detail::is_float_vec_v<C>||detail::is_float_expr_v<C>)&&(detail::lane_count_v<A> == detail::lane_count_v<B>)&&(detail::lane_count_v<A> == detail::lane_count_v<C>)&&(detail::is_float_expr_v<A>||detail::is_float_expr_v<B>||detail::is_float_expr_v<C>)) [[nodiscard]] inline auto smoothstep(const A& edge0,const B& edge1,const C& x) -> Vec<detail::lane_count_v<A>,float> { return smoothstep(materialize(edge0),materialize(edge1),materialize(x)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> smoothstep(float edge0,float edge1,const FloatExpr<N>& x) { return smoothstep(edge0,edge1,materialize(x)); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> smoothstep(double edge0,double edge1,const FloatExpr<N>& x) { return smoothstep(edge0,edge1,materialize(x)); }

// Remap's std140 block is a fixed ABI, not a generic dynamically-sized array.
// Keeping the storage owned makes a binding copy-safe: the caller may release
// or mutate its source object immediately after set_uniform().
struct RemapUniformData {
  std::array<Vec4, 267> data{};
};
using UniformValue=std::variant<float,double,std::int32_t,std::uint32_t,bool,Vec2,Vec3,Vec4,IVec2,IVec3,IVec4,UVec2,UVec3,UVec4,BVec2,BVec3,BVec4,Mat2,Mat3,Mat4,RemapUniformData>;
class KernelBindingError : public std::runtime_error { public: using std::runtime_error::runtime_error; };
class Bindings {
 public:
  void set_uniform(std::string name,UniformValue value);
  // The caller retains ownership: surface must outlive this Bindings and captured kernels.
  void set_texture(std::string name,const noisemaker::Surface& surface);
  template <class T> [[nodiscard]] T get(std::string_view name) const { const auto found=uniforms_.find(std::string(name));if(found==uniforms_.end())throw KernelBindingError("uniform binding '"+std::string(name)+"' is missing");if(const auto* value=std::get_if<T>(&found->second);value!=nullptr)return *value;throw KernelBindingError("uniform binding '"+std::string(name)+"' has the wrong type"); }
  template <class T> [[nodiscard]] T get_or(std::string_view name,const T& fallback) const { const auto found=uniforms_.find(std::string(name));if(found==uniforms_.end())return fallback;if(const auto* value=std::get_if<T>(&found->second);value!=nullptr)return *value;throw KernelBindingError("uniform binding '"+std::string(name)+"' has the wrong type"); }
  [[nodiscard]] double get_number(std::string_view name) const { const auto found=uniforms_.find(std::string(name));if(found==uniforms_.end())throw KernelBindingError("uniform binding '"+std::string(name)+"' is missing");if(const auto* value=std::get_if<double>(&found->second);value!=nullptr)return *value;if(const auto* value=std::get_if<float>(&found->second);value!=nullptr)return static_cast<double>(*value);throw KernelBindingError("uniform binding '"+std::string(name)+"' has the wrong type"); }
  [[nodiscard]] const noisemaker::Surface& texture(std::string_view name) const;
 private:
  std::unordered_map<std::string,UniformValue> uniforms_;
  std::unordered_map<std::string,const noisemaker::Surface*> textures_;
};
// ---------------------------------------------------------------------------
// Screen-space derivatives (dFdx / dFdy / fwidth)
//
// Mirrors `GlslRuntime.#derivative` and `GlslRuntime.wrapDerivatives`,
// noisemaker-for-cpu/src/csl/glsl-runtime.js:448-546. The reference keys every
// derivative call by a per-invocation ordinal (`derivativeIndex`, reset by
// `beginPixel`), runs the whole kernel body once per 2x2-quad corner in
// 'record' mode to capture each call's *input*, then replays the kernel once
// more to produce the real output from the differenced inputs.
//
// Narrowing is deliberately asymmetric and this is load-bearing:
//   * scalars - the record stores a raw JS Number (:451), so the difference is
//               taken in double (:519-521) and narrowed exactly once on the way
//               out (`F32(selected)`, :461).
//   * vectors - the record is `Array.from(Float32Array)` and the x/y/footprint
//               buffers are themselves `Float32Array` (:524-531), so every
//               component store narrows; the replay copy narrows nothing more.
// Reversing these passes a smooth-polynomial test and fails on real programs.
// ---------------------------------------------------------------------------
enum class DerivativeMode { Approximate, Record, Replay };
enum class DerivativeKind { X, Y, Width };

// One recorded derivative-call input. `lanes == 0` denotes the scalar case.
struct DerivativeRecord {
  std::size_t lanes = 0;
  double scalar = 0.0;
  float vector[4] = {0.0f, 0.0f, 0.0f, 0.0f};
};

// The differenced result for one ordinal, shaped like the record it came from.
struct DerivativeValue {
  std::size_t lanes = 0;
  double scalar_x = 0.0;
  double scalar_y = 0.0;
  double scalar_width = 0.0;
  float vector_x[4] = {0.0f, 0.0f, 0.0f, 0.0f};
  float vector_y[4] = {0.0f, 0.0f, 0.0f, 0.0f};
  float vector_width[4] = {0.0f, 0.0f, 0.0f, 0.0f};
};

struct DerivativeState {
  DerivativeMode mode = DerivativeMode::Approximate;
  std::size_t index = 0;
  std::vector<DerivativeRecord> records;
  std::vector<DerivativeValue> values;
};

// `derivative` stays null for every program that does not use a derivative
// builtin, so all previously typed programs are bit-for-bit unaffected.
struct PixelContext { Vec2 uv{}; Vec4 frag_coord{}; Vec2 resolution{}; float time{}; float seed{}; std::uint32_t frame{}; float delta_time{}; DerivativeState* derivative = nullptr; };

namespace detail {
// `1 / resolution`, matching `beginPixel`'s inverseWidth/inverseHeight
// (glsl-runtime.js:145-146). Division is in double, exactly as JS does it.
[[nodiscard]] inline double inverse_width(const PixelContext& context) noexcept {
  return 1.0 / static_cast<double>(context.resolution[0]);
}
[[nodiscard]] inline double inverse_height(const PixelContext& context) noexcept {
  return 1.0 / static_cast<double>(context.resolution[1]);
}
[[nodiscard]] inline std::size_t derivative_take_ordinal(DerivativeState* state) noexcept {
  return state == nullptr ? 0U : state->index++;
}
}  // namespace detail

// Scalar form. Every reachable return path narrows through `f32`, matching the
// reference's `F32(...)`.
[[nodiscard]] inline float derivative_scalar(const PixelContext& context, double value,
                                             DerivativeKind kind) noexcept {
  DerivativeState* state = context.derivative;
  const std::size_t index = detail::derivative_take_ordinal(state);
  if (state != nullptr && state->mode == DerivativeMode::Record) {
    if (state->records.size() <= index) state->records.resize(index + 1U);
    DerivativeRecord& record = state->records[index];
    record.lanes = 0U;
    record.scalar = value;
    return 0.0f;  // JS returns the Number 0 (:452), not a narrowed input.
  }
  if (state != nullptr && state->mode == DerivativeMode::Replay && index < state->values.size()) {
    const DerivativeValue& computed = state->values[index];
    // Shape stability across the quad is proved at admission time, so a width
    // mismatch here means the admitted closure was wrong, not the input.
    assert(computed.lanes == 0U && "derivative ordinal changed shape between record and replay");
    if (computed.lanes == 0U) {
      const double selected = kind == DerivativeKind::X ? computed.scalar_x
                            : kind == DerivativeKind::Y ? computed.scalar_y
                                                        : computed.scalar_width;
      return noisemaker::f32(selected);
    }
  }
  // 'approximate' fallback (:467) - a coarse constant, reached only by a kernel
  // invoked outside the quad driver.
  const double inverse = kind == DerivativeKind::X ? detail::inverse_width(context)
                       : kind == DerivativeKind::Y ? detail::inverse_height(context)
                       : detail::inverse_width(context) + detail::inverse_height(context);
  return noisemaker::f32(inverse);
}

// Vector form. Every component store narrows, matching the Float32Array
// buffers in the reference.
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> derivative_vector(const PixelContext& context,
                                                     const Vec<N, float>& value,
                                                     DerivativeKind kind) noexcept {
  static_assert(N >= 2U && N <= 4U, "derivatives are defined for vec2/vec3/vec4");
  DerivativeState* state = context.derivative;
  const std::size_t index = detail::derivative_take_ordinal(state);
  Vec<N, float> result;
  for (std::size_t lane = 0; lane < N; ++lane) result[lane] = 0.0f;
  if (state != nullptr && state->mode == DerivativeMode::Record) {
    if (state->records.size() <= index) state->records.resize(index + 1U);
    DerivativeRecord& record = state->records[index];
    record.lanes = N;
    for (std::size_t lane = 0; lane < N; ++lane) record.vector[lane] = value[lane];
    return result;  // zero-filled dummy (:453-455)
  }
  if (state != nullptr && state->mode == DerivativeMode::Replay && index < state->values.size()) {
    const DerivativeValue& computed = state->values[index];
    assert(computed.lanes == N && "derivative ordinal changed shape between record and replay");
    if (computed.lanes == N) {
      const float* selected = kind == DerivativeKind::X ? computed.vector_x
                            : kind == DerivativeKind::Y ? computed.vector_y
                                                        : computed.vector_width;
      for (std::size_t lane = 0; lane < N; ++lane) result[lane] = selected[lane];
      return result;
    }
  }
  // 'approximate' fallback (:468-473). The reference's `else if` at :472 is
  // dead whenever the width is at least 2, which the static_assert guarantees.
  if (kind != DerivativeKind::Y) result[0] = noisemaker::f32(detail::inverse_width(context));
  if (kind != DerivativeKind::X) result[1] = noisemaker::f32(detail::inverse_height(context));
  return result;
}

// Public spellings. The emitter lowers `dFdx(e)` to `glsl::dFdx(context, e)`.
[[nodiscard]] inline float dFdx(const PixelContext& context, double value) noexcept {
  return derivative_scalar(context, value, DerivativeKind::X);
}
[[nodiscard]] inline float dFdy(const PixelContext& context, double value) noexcept {
  return derivative_scalar(context, value, DerivativeKind::Y);
}
[[nodiscard]] inline float fwidth(const PixelContext& context, double value) noexcept {
  return derivative_scalar(context, value, DerivativeKind::Width);
}
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> dFdx(const PixelContext& context, const Vec<N,float>& value) noexcept { return derivative_vector(context, value, DerivativeKind::X); }
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> dFdy(const PixelContext& context, const Vec<N,float>& value) noexcept { return derivative_vector(context, value, DerivativeKind::Y); }
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> fwidth(const PixelContext& context, const Vec<N,float>& value) noexcept { return derivative_vector(context, value, DerivativeKind::Width); }

// A FloatExpr argument materializes first: a vector expression in JS is
// produced through `alloc()` into a Float32Array, so it is already narrowed by
// the time the derivative sees it. Scalars are deliberately NOT materialized -
// they arrive as an un-narrowed double, which is exactly the asymmetry above.
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> dFdx(const PixelContext& context, const FloatExpr<N>& value) noexcept { return derivative_vector(context, Vec<N,float>(value), DerivativeKind::X); }
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> dFdy(const PixelContext& context, const FloatExpr<N>& value) noexcept { return derivative_vector(context, Vec<N,float>(value), DerivativeKind::Y); }
template <std::size_t N>
[[nodiscard]] inline Vec<N,float> fwidth(const PixelContext& context, const FloatExpr<N>& value) noexcept { return derivative_vector(context, Vec<N,float>(value), DerivativeKind::Width); }
}  // namespace noisemaker::glsl
