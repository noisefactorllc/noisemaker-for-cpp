#include "noisemaker/glsl_runtime.hpp"

#include <cmath>
#include <limits>
#include <utility>

namespace noisemaker::glsl {
namespace detail {
std::int32_t float_to_int32(double value) noexcept { if(std::isnan(value))return 0;if(value>=static_cast<double>(std::numeric_limits<std::int32_t>::max()))return std::numeric_limits<std::int32_t>::max();if(value<=static_cast<double>(std::numeric_limits<std::int32_t>::min()))return std::numeric_limits<std::int32_t>::min();return static_cast<std::int32_t>(std::trunc(value)); }
std::uint32_t float_to_uint32(double value) noexcept {
  if (!std::isfinite(value) || value == 0.0) return 0U;
  constexpr double modulus = 4294967296.0;
  double wrapped = std::fmod(std::trunc(value), modulus);
  if (wrapped < 0.0) wrapped += modulus;
  return static_cast<std::uint32_t>(wrapped);
}
std::int32_t js_to_int32(double value) noexcept {
  return std::bit_cast<std::int32_t>(float_to_uint32(value));
}
double js_umul(double left, double right) noexcept {
  return static_cast<double>(float_to_uint32(left) * float_to_uint32(right));
}
std::int32_t js_shift_right(double left, double count) noexcept {
  const std::uint32_t word = float_to_uint32(left);
  const std::uint32_t shift = float_to_uint32(count) & 31U;
  if (shift == 0U) return std::bit_cast<std::int32_t>(word);
  std::uint32_t shifted = word >> shift;
  if ((word & 0x80000000U) != 0U) {
    shifted |= (~std::uint32_t{0}) << (32U - shift);
  }
  return std::bit_cast<std::int32_t>(shifted);
}
double js_logical_shift_right(double left, double count) noexcept {
  const std::uint32_t word = float_to_uint32(left);
  const std::uint32_t shift = float_to_uint32(count) & 31U;
  return static_cast<double>(word >> shift);
}
std::int32_t js_bitwise_and(double left, double right) noexcept {
  return std::bit_cast<std::int32_t>(
      float_to_uint32(left) & float_to_uint32(right));
}
std::int32_t js_bitwise_or(double left, double right) noexcept {
  return std::bit_cast<std::int32_t>(
      float_to_uint32(left) | float_to_uint32(right));
}
std::int32_t js_bitwise_xor(double left, double right) noexcept {
  return std::bit_cast<std::int32_t>(
      float_to_uint32(left) ^ float_to_uint32(right));
}
std::int32_t js_bitwise_not(double value) noexcept {
  return std::bit_cast<std::int32_t>(~float_to_uint32(value));
}
std::int32_t js_array_int32_read_for_bitwise(
    const std::int32_t* values, std::size_t size, double index) noexcept {
  if (values == nullptr || !std::isfinite(index) || index < 0.0
      || std::trunc(index) != index
      || index >= static_cast<double>(size)) {
    return 0;
  }
  return values[static_cast<std::size_t>(index)];
}
}  // namespace detail
float mod(double x,double y) noexcept { return noisemaker::f32(noisemaker::glsl_mod(x,y)); }
float fract(double x) noexcept { return noisemaker::f32(x-std::floor(x)); }
double round(double x) noexcept { return noisemaker::glsl_round(x); }
void Bindings::set_uniform(std::string name,UniformValue value) { if(name.empty())throw KernelBindingError("uniform binding name must not be empty");uniforms_.insert_or_assign(std::move(name),std::move(value)); }
void Bindings::set_texture(std::string name,const noisemaker::Surface& surface) { if(name.empty())throw KernelBindingError("sampler binding name must not be empty");textures_.insert_or_assign(std::move(name),&surface); }
const noisemaker::Surface& Bindings::texture(std::string_view name) const { const auto found=textures_.find(std::string(name));if(found==textures_.end())throw KernelBindingError("sampler binding '"+std::string(name)+"' is missing");return *found->second; }
}  // namespace noisemaker::glsl
