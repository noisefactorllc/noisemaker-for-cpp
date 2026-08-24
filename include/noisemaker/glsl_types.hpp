#pragma once

#include <array>
#include <bit>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <type_traits>
#include <utility>

#include "noisemaker/numeric.hpp"

namespace noisemaker::glsl {

namespace detail {
[[nodiscard]] std::int32_t float_to_int32(double value) noexcept;
[[nodiscard]] std::uint32_t float_to_uint32(double value) noexcept;
[[nodiscard]] std::int32_t js_to_int32(double value) noexcept;
[[nodiscard]] double js_umul(double left, double right) noexcept;
[[nodiscard]] std::int32_t js_shift_right(double left, double count) noexcept;
[[nodiscard]] double js_logical_shift_right(double left, double count) noexcept;
[[nodiscard]] std::int32_t js_bitwise_and(double left, double right) noexcept;
[[nodiscard]] std::int32_t js_bitwise_or(double left, double right) noexcept;
[[nodiscard]] std::int32_t js_bitwise_xor(double left, double right) noexcept;
[[nodiscard]] std::int32_t js_bitwise_not(double value) noexcept;
[[nodiscard]] std::int32_t js_array_int32_read_for_bitwise(
    const std::int32_t* values, std::size_t size, double index) noexcept;

template <class T>
[[nodiscard]] constexpr T add(T a, T b) noexcept {
  if constexpr (std::same_as<T, std::int32_t>) {
    return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) + std::bit_cast<std::uint32_t>(b));
  } else {
    return static_cast<T>(a + b);
  }
}
template <class T>
[[nodiscard]] constexpr T subtract(T a, T b) noexcept {
  if constexpr (std::same_as<T, std::int32_t>) {
    return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) - std::bit_cast<std::uint32_t>(b));
  } else {
    return static_cast<T>(a - b);
  }
}
template <class T>
[[nodiscard]] constexpr T multiply(T a, T b) noexcept {
  if constexpr (std::same_as<T, std::int32_t>) {
    return std::bit_cast<std::int32_t>(std::bit_cast<std::uint32_t>(a) * std::bit_cast<std::uint32_t>(b));
  } else {
    return static_cast<T>(a * b);
  }
}
template <class T>
[[nodiscard]] constexpr T divide(T a, T b) noexcept {
  if constexpr (std::same_as<T, std::int32_t>) {
    if (b == 0) return 0;
    if (a == INT32_MIN && b == -1) return INT32_MIN;
    return static_cast<std::int32_t>(a / b);
  } else {
    return b == 0U ? 0U : static_cast<T>(a / b);
  }
}
template <class T, class U>
[[nodiscard]] T convert_lane(U value) noexcept {
  if constexpr (std::same_as<T, std::int32_t> && std::floating_point<U>) return float_to_int32(static_cast<double>(value));
  if constexpr (std::same_as<T, std::uint32_t> && std::floating_point<U>) return float_to_uint32(static_cast<double>(value));
  return static_cast<T>(value);
}
}  // namespace detail

[[nodiscard]] constexpr std::int32_t integer_mod(std::int32_t left, std::int32_t right) noexcept {
  if (right == 0 || (left == INT32_MIN && right == -1)) return 0;
  return static_cast<std::int32_t>(left % right);
}
[[nodiscard]] constexpr std::uint32_t integer_mod(std::uint32_t left, std::uint32_t right) noexcept {
  return right == 0U ? 0U : left % right;
}

template <std::size_t N> class FloatExpr;
template <std::size_t N, class T> class Vec;

namespace detail {
template <class T> struct is_vec : std::false_type {};
template <std::size_t N, class T> struct is_vec<Vec<N, T>> : std::true_type { static constexpr std::size_t lanes = N; };
template <class T> inline constexpr bool is_vec_v = is_vec<std::remove_cvref_t<T>>::value;
template <class T> struct is_float_vec : std::false_type {};
template <std::size_t N> struct is_float_vec<Vec<N, float>> : std::true_type {};
template <class T> inline constexpr bool is_float_vec_v = is_float_vec<std::remove_cvref_t<T>>::value;
template <class T> struct is_float_expr : std::false_type {};
template <std::size_t N> struct is_float_expr<FloatExpr<N>> : std::true_type { static constexpr std::size_t lanes = N; };
template <class T> inline constexpr bool is_float_expr_v = is_float_expr<std::remove_cvref_t<T>>::value;
template <class T> concept LanePart = std::is_arithmetic_v<std::remove_cvref_t<T>> || is_vec_v<T> || is_float_expr_v<T>;
template <class T> struct lane_count : std::integral_constant<std::size_t, 1U> {};
template <std::size_t N, class T> struct lane_count<Vec<N, T>> : std::integral_constant<std::size_t, N> {};
template <std::size_t N> struct lane_count<FloatExpr<N>> : std::integral_constant<std::size_t, N> {};
template <class T> inline constexpr std::size_t lane_count_v = lane_count<std::remove_cvref_t<T>>::value;
template <class... Parts> inline constexpr std::size_t total_lanes_v = (lane_count_v<Parts> + ... + 0U);
template <std::size_t... I> consteval bool unique_indices() {
  constexpr std::array<std::size_t, sizeof...(I)> values{I...};
  for (std::size_t a = 0; a < values.size(); ++a) for (std::size_t b = a + 1; b < values.size(); ++b) if (values[a] == values[b]) return false;
  return true;
}
}  // namespace detail

template <std::size_t N, class T>
class Vec {
 public:
  static_assert(N >= 2 && N <= 4);
  constexpr Vec() = default;
  constexpr explicit Vec(T scalar) { lanes_.fill(scalar); }
  template <class... Values>
    requires(sizeof...(Values) == N && (std::convertible_to<Values, T> && ...))
  constexpr Vec(Values... values) : lanes_{static_cast<T>(values)...} {}
  template <class... Parts>
    requires(sizeof...(Parts) > 0 && (detail::LanePart<Parts> && ...) && detail::total_lanes_v<Parts...> == N && !(sizeof...(Parts) == N && (std::convertible_to<Parts, T> && ...)))
  constexpr explicit Vec(const Parts&... parts) {
    std::size_t offset = 0;
    (append(offset, parts), ...);
  }
  template <class U>
    requires(!std::same_as<U, T>)
  explicit Vec(const Vec<N, U>& other) {
    for (std::size_t i = 0; i < N; ++i) lanes_[i] = detail::convert_lane<T>(other[i]);
  }
  Vec(const FloatExpr<N>& expression) requires std::same_as<T, float>;
  Vec& operator=(const FloatExpr<N>& expression) requires std::same_as<T, float>;
  [[nodiscard]] constexpr T& at(std::size_t index) { return lanes_.at(index); }
  [[nodiscard]] constexpr const T& at(std::size_t index) const { return lanes_.at(index); }
  [[nodiscard]] constexpr T& operator[](std::size_t index) noexcept { return lanes_[index]; }
  [[nodiscard]] constexpr const T& operator[](std::size_t index) const noexcept { return lanes_[index]; }
  [[nodiscard]] constexpr bool operator==(const Vec&) const = default;
 private:
  template <class Part> constexpr void append(std::size_t& offset, const Part& part) {
    if constexpr (detail::is_vec_v<Part> || detail::is_float_expr_v<Part>) for (std::size_t i = 0; i < detail::lane_count_v<Part>; ++i) lanes_[offset++] = detail::convert_lane<T>(part[i]);
    else lanes_[offset++] = detail::convert_lane<T>(part);
  }
  std::array<T, N> lanes_{};
};

// Canonical JavaScript lowers vector equality to an allocated typed-array
// result. The object is truthy whether its comparison lanes are true or false;
// this compatibility comparer intentionally is not mathematical equality.
template <std::size_t N, class T>
[[nodiscard]] constexpr bool canonical_js_vector_equality_result_is_truthy(
    const Vec<N, T>&, const Vec<N, T>&) noexcept {
  return true;
}

template <std::size_t N>
class FloatExpr {
 public:
  constexpr FloatExpr() = default;
  constexpr explicit FloatExpr(double scalar) { lanes_.fill(scalar); }
  constexpr FloatExpr(const Vec<N, float>& vector) { for (std::size_t i = 0; i < N; ++i) lanes_[i] = vector[i]; }
  template <class T> requires(std::integral<T> && !std::same_as<T, bool>)
  constexpr explicit FloatExpr(const Vec<N, T>& vector) {
    for (std::size_t i = 0; i < N; ++i) lanes_[i] = static_cast<double>(vector[i]);
  }
  template <class... Values> requires(sizeof...(Values) == N && (std::convertible_to<Values, double> && ...))
  constexpr FloatExpr(Values... values) : lanes_{static_cast<double>(values)...} {}
  [[nodiscard]] constexpr double operator[](std::size_t index) const noexcept { return lanes_[index]; }
 private:
  template <std::size_t M> friend constexpr FloatExpr<M> make_float_expr(std::array<double, M>);
  std::array<double, N> lanes_{};
};
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> make_float_expr(std::array<double, N> lanes) { FloatExpr<N> result; result.lanes_ = lanes; return result; }
template <std::size_t N, class T>
Vec<N, T>::Vec(const FloatExpr<N>& expression) requires std::same_as<T, float> { for (std::size_t i = 0; i < N; ++i) lanes_[i] = noisemaker::f32(expression[i]); }
template <std::size_t N, class T>
Vec<N, T>& Vec<N, T>::operator=(const FloatExpr<N>& expression) requires std::same_as<T, float> { for (std::size_t i = 0; i < N; ++i) lanes_[i] = noisemaker::f32(expression[i]); return *this; }
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> float_expr(const Vec<N, float>& value) { return FloatExpr<N>(value); }
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> float_expr(const FloatExpr<N>& value) { return value; }
template <std::size_t N, class Op> [[nodiscard]] constexpr FloatExpr<N> float_binary(const FloatExpr<N>& a, const FloatExpr<N>& b, Op op) { std::array<double, N> lanes{}; for (std::size_t i = 0; i < N; ++i) lanes[i] = op(a[i], b[i]); return make_float_expr(lanes); }

#define NOISEMAKER_GLSL_FLOAT_BINARY(symbol) \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const FloatExpr<N>& a, const FloatExpr<N>& b) { return float_binary(a, b, [](double x, double y) { return x symbol y; }); } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const Vec<N, float>& a, const Vec<N, float>& b) { return float_expr(a) symbol float_expr(b); } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const Vec<N, float>& a, const FloatExpr<N>& b) { return float_expr(a) symbol b; } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const FloatExpr<N>& a, const Vec<N, float>& b) { return a symbol float_expr(b); } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const FloatExpr<N>& a, double b) { return a symbol FloatExpr<N>(b); } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(double a, const FloatExpr<N>& b) { return FloatExpr<N>(a) symbol b; } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(const Vec<N, float>& a, double b) { return float_expr(a) symbol b; } \
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator symbol(double a, const Vec<N, float>& b) { return a symbol float_expr(b); }
NOISEMAKER_GLSL_FLOAT_BINARY(+)
NOISEMAKER_GLSL_FLOAT_BINARY(-)
NOISEMAKER_GLSL_FLOAT_BINARY(*)
NOISEMAKER_GLSL_FLOAT_BINARY(/)
#undef NOISEMAKER_GLSL_FLOAT_BINARY

template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator-(const Vec<N, float>& value) { return FloatExpr<N>(0.0) - value; }
template <std::size_t N> [[nodiscard]] constexpr FloatExpr<N> operator-(const FloatExpr<N>& value) { return FloatExpr<N>(0.0) - value; }

template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N, T> operator+(const Vec<N, T>& a, const Vec<N, T>& b) { Vec<N, T> r; for (std::size_t i = 0; i < N; ++i) r[i] = detail::add(a[i], b[i]); return r; }
template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N, T> operator-(const Vec<N, T>& a, const Vec<N, T>& b) { Vec<N, T> r; for (std::size_t i = 0; i < N; ++i) r[i] = detail::subtract(a[i], b[i]); return r; }
template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N, T> operator*(const Vec<N, T>& a, const Vec<N, T>& b) { Vec<N, T> r; for (std::size_t i = 0; i < N; ++i) r[i] = detail::multiply(a[i], b[i]); return r; }
template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N, T> operator/(const Vec<N, T>& a, const Vec<N, T>& b) { Vec<N, T> r; for (std::size_t i = 0; i < N; ++i) r[i] = detail::divide(a[i], b[i]); return r; }
#define NOISEMAKER_GLSL_INTEGER_BINARY(symbol) \
template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N,T> operator symbol(const Vec<N,T>& a,T b) { return a symbol Vec<N,T>(b); } \
template <std::size_t N, class T> requires(!std::same_as<T, float>) [[nodiscard]] constexpr Vec<N,T> operator symbol(T a,const Vec<N,T>& b) { return Vec<N,T>(a) symbol b; }
NOISEMAKER_GLSL_INTEGER_BINARY(+)
NOISEMAKER_GLSL_INTEGER_BINARY(-)
NOISEMAKER_GLSL_INTEGER_BINARY(*)
NOISEMAKER_GLSL_INTEGER_BINARY(/)
#undef NOISEMAKER_GLSL_INTEGER_BINARY

template <std::size_t N, class T> requires(!std::same_as<T, float> && !std::same_as<T, bool>) [[nodiscard]] constexpr Vec<N, T> operator-(const Vec<N, T>& value) { Vec<N, T> result; for (std::size_t i = 0; i < N; ++i) result[i] = detail::subtract(static_cast<T>(0), value[i]); return result; }

template <std::size_t N>
[[nodiscard]] constexpr Vec<N, std::uint32_t> shift_right(
    const Vec<N, std::uint32_t>& value, std::uint32_t amount) noexcept {
  Vec<N, std::uint32_t> result;
  const std::uint32_t masked = amount & 31U;
  for (std::size_t index = 0; index < N; ++index) result[index] = value[index] >> masked;
  return result;
}

// Lane-wise shift amount. GLSL allows `uvecN >> uvecN`; JavaScript masks each
// shift count mod 32 independently, so the mask is applied per lane exactly as
// the scalar overload applies it once. Logical (zero-fill) shift, matching the
// recognized pcg-hash idiom the transpiler emits `>>>` for.
template <std::size_t N>
[[nodiscard]] constexpr Vec<N, std::uint32_t> shift_right(
    const Vec<N, std::uint32_t>& value, const Vec<N, std::uint32_t>& amount) noexcept {
  Vec<N, std::uint32_t> result;
  for (std::size_t index = 0; index < N; ++index) result[index] = value[index] >> (amount[index] & 31U);
  return result;
}

template <std::size_t N>
[[nodiscard]] constexpr Vec<N, std::uint32_t> bitwise_xor(
    const Vec<N, std::uint32_t>& left,
    const Vec<N, std::uint32_t>& right) noexcept {
  Vec<N, std::uint32_t> result;
  for (std::size_t index = 0; index < N; ++index) result[index] = left[index] ^ right[index];
  return result;
}

template <std::size_t... I, std::size_t N, class T> [[nodiscard]] constexpr auto swizzle(const Vec<N,T>& value) { static_assert(sizeof...(I) >= 1 && sizeof...(I) <= 4); static_assert(((I < N) && ...)); if constexpr (sizeof...(I) == 1) return value[std::array<std::size_t,1>{I...}[0]]; else return Vec<sizeof...(I),T>(value[I]...); }
template <std::size_t... I, std::size_t N> [[nodiscard]] constexpr auto swizzle(const FloatExpr<N>& value) { static_assert(sizeof...(I) >= 1 && sizeof...(I) <= 4); static_assert(((I < N) && ...)); if constexpr (sizeof...(I) == 1) return value[std::array<std::size_t,1>{I...}[0]]; else return FloatExpr<sizeof...(I)>(value[I]...); }
template <std::size_t... I, std::size_t N, class T, class V> constexpr void set_swizzle(Vec<N,T>& target,const V& value) { static_assert(sizeof...(I)>=1 && sizeof...(I)<=4); static_assert(((I<N)&&...)); static_assert(detail::unique_indices<I...>()); constexpr std::size_t count=sizeof...(I); std::array<T,count> source{}; if constexpr (count==1) source[0]=detail::convert_lane<T>(value); else { const Vec<count,T> temporary(value); for(std::size_t x=0;x<count;++x) source[x]=temporary[x]; } constexpr std::array<std::size_t,count> destinations{I...}; for(std::size_t x=0;x<count;++x) target[destinations[x]]=source[x]; }

template <std::size_t N>
class Mat {
 public:
  constexpr Mat() = default;
  explicit constexpr Mat(float diagonal) { for (std::size_t i = 0; i < N; ++i) columns_[i][i] = diagonal; }
  template <class... Columns> requires(sizeof...(Columns)==N && (std::same_as<std::remove_cvref_t<Columns>,Vec<N,float>> && ...)) constexpr Mat(Columns&&... columns) : columns_{std::forward<Columns>(columns)...} {}
  [[nodiscard]] constexpr Vec<N,float>& operator[](std::size_t column) noexcept { return columns_[column]; }
  [[nodiscard]] constexpr const Vec<N,float>& operator[](std::size_t column) const noexcept { return columns_[column]; }
  [[nodiscard]] constexpr bool operator==(const Mat&) const = default;
 private: std::array<Vec<N,float>,N> columns_{};
};
template <std::size_t N> [[nodiscard]] inline Vec<N,float> operator*(const Mat<N>& matrix,const Vec<N,float>& vector) { Vec<N,float> result; for(std::size_t row=0;row<N;++row){double sum=0;for(std::size_t column=0;column<N;++column)sum+=static_cast<double>(matrix[column][row])*vector[column];result[row]=noisemaker::f32(sum);} return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> operator*(const Vec<N,float>& vector,const Mat<N>& matrix) { Vec<N,float> result; for(std::size_t column=0;column<N;++column){double sum=0;for(std::size_t row=0;row<N;++row)sum+=static_cast<double>(vector[row])*matrix[column][row];result[column]=noisemaker::f32(sum);} return result; }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> operator*(const Mat<N>& matrix,const FloatExpr<N>& vector) { return matrix * Vec<N,float>(vector); }
template <std::size_t N> [[nodiscard]] inline Vec<N,float> operator*(const FloatExpr<N>& vector,const Mat<N>& matrix) { return Vec<N,float>(vector) * matrix; }
template <std::size_t N> [[nodiscard]] inline Mat<N> operator*(const Mat<N>& a,const Mat<N>& b) { Mat<N> result; for(std::size_t column=0;column<N;++column) result[column]=a*b[column]; return result; }

// Lane-wise relational comparison and boolean reduction.
//
// Deliberately constrained to N == 2. Only the exact bvec2 closure
// authenticated by extrude-bvec2-relational-reduction-v1 is authorized to
// lower to these, so wider boolean-vector relational reduction is a compile
// error rather than a silently available generalization. Widening this
// constraint requires its own authenticated capability.
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> lessThanEqual(
    const Vec<N, float>& left, const Vec<N, float>& right) noexcept {
  Vec<N, bool> result;
  for (std::size_t index = 0; index < N; ++index)
    result[index] = left[index] <= right[index];
  return result;
}

// Exact Edge stored-bvec3 call shapes. The FloatExpr RHS retains JavaScript
// Number lanes, so materialize it through Vec3 before comparing to reproduce
// the canonical Float32Array constructor boundary.
[[nodiscard]] inline Vec<3, bool> lessThan(
    const Vec<3, float>& left, const FloatExpr<3>& right) noexcept {
  const Vec<3, float> materialized(right);
  Vec<3, bool> result;
  for (std::size_t index = 0; index < 3; ++index)
    result[index] = left[index] < materialized[index];
  return result;
}

[[nodiscard]] inline Vec<3, bool> greaterThanEqual(
    const Vec<3, float>& left, const FloatExpr<3>& right) noexcept {
  const Vec<3, float> materialized(right);
  Vec<3, bool> result;
  for (std::size_t index = 0; index < 3; ++index)
    result[index] = left[index] >= materialized[index];
  return result;
}

// Block the implicit Vec3/FloatExpr conversions from widening the authenticated
// call surface. Edge authorizes only (Vec3, FloatExpr<3>), in that order.
[[nodiscard]] Vec<3, bool> lessThan(
    const FloatExpr<3>&, const Vec<3, float>&) = delete;
[[nodiscard]] Vec<3, bool> lessThan(
    const Vec<3, float>&, const Vec<3, float>&) = delete;
[[nodiscard]] Vec<3, bool> greaterThanEqual(
    const FloatExpr<3>&, const Vec<3, float>&) = delete;
[[nodiscard]] Vec<3, bool> greaterThanEqual(
    const Vec<3, float>&, const Vec<3, float>&) = delete;

template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr bool all(const Vec<N, bool>& value) noexcept {
  for (std::size_t index = 0; index < N; ++index)
    if (!value[index]) return false;
  return true;
}

// Emboss authorizes exactly two lane-wise equality results, each consumed
// immediately by all(). Keep the runtime surface constrained to N == 2 so
// this program-scoped admission cannot become generic bvec equality. Deferred
// Number lanes materialize through Vec<N, float> before comparison, matching
// the canonical Float32Array boundary.
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> equal(
    const Vec<N, float>& left, const Vec<N, float>& right) noexcept {
  Vec<N, bool> result;
  for (std::size_t index = 0; index < N; ++index)
    result[index] = left[index] == right[index];
  return result;
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> equal(
    const Vec<N, float>& left, const FloatExpr<N>& right) noexcept {
  return equal(left, Vec<N, float>(right));
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> equal(
    const FloatExpr<N>& left, const Vec<N, float>& right) noexcept {
  return equal(Vec<N, float>(left), right);
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> equal(
    const FloatExpr<N>& left, const FloatExpr<N>& right) noexcept {
  return equal(Vec<N, float>(left), Vec<N, float>(right));
}

// Same N==2 authorization discipline as lessThanEqual/all above, for
// notEqual/any -- only the exact bvec2 closure authenticated by
// waves-any-notequal-admission-v1 is authorized to lower to these.
//
// Three overloads accept a `FloatExpr<N>` operand (e.g. a broadcast
// constructor like `vec2(0.0)`, which the emitter lowers to `FloatExpr<N>`,
// not `Vec<N,float>`) by converting through the existing narrowing Vec
// constructor first -- the same "convert-then-delegate" shape as
// `Mat<N>::operator*(FloatExpr<N>)` above. Narrowing a `FloatExpr<N>` to
// `Vec<N,float>` before an equality/inequality compare is exact whenever
// the constant is precisely representable in f32 (0.0 always is), which is
// the only site this authorizes today.
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> notEqual(
    const Vec<N, float>& left, const Vec<N, float>& right) noexcept {
  Vec<N, bool> result;
  for (std::size_t index = 0; index < N; ++index)
    result[index] = left[index] != right[index];
  return result;
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> notEqual(
    const Vec<N, float>& left, const FloatExpr<N>& right) noexcept {
  return notEqual(left, Vec<N, float>(right));
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> notEqual(
    const FloatExpr<N>& left, const Vec<N, float>& right) noexcept {
  return notEqual(Vec<N, float>(left), right);
}
template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr Vec<N, bool> notEqual(
    const FloatExpr<N>& left, const FloatExpr<N>& right) noexcept {
  return notEqual(Vec<N, float>(left), Vec<N, float>(right));
}

template <std::size_t N> requires(N == 2)
[[nodiscard]] constexpr bool any(const Vec<N, bool>& value) noexcept {
  for (std::size_t index = 0; index < N; ++index)
    if (value[index]) return true;
  return false;
}

using Vec2=Vec<2,float>; using Vec3=Vec<3,float>; using Vec4=Vec<4,float>;
using IVec2=Vec<2,std::int32_t>; using IVec3=Vec<3,std::int32_t>; using IVec4=Vec<4,std::int32_t>;
using UVec2=Vec<2,std::uint32_t>; using UVec3=Vec<3,std::uint32_t>; using UVec4=Vec<4,std::uint32_t>;
using BVec2=Vec<2,bool>; using BVec3=Vec<3,bool>; using BVec4=Vec<4,bool>;
using Mat2=Mat<2>; using Mat3=Mat<3>; using Mat4=Mat<4>;
}  // namespace noisemaker::glsl
