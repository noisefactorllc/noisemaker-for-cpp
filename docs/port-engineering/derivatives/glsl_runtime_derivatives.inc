// ===========================================================================
// PROPOSED ADDITION to include/noisemaker/glsl_runtime.hpp
// Insert immediately before `struct PixelContext`, then extend PixelContext
// with the `derivative` pointer (see the bottom of this file).
//
// Requires <vector> and <cstddef> in the header's include list.
// ===========================================================================

// ---------------------------------------------------------------------------
// Screen-space derivatives (dFdx / dFdy / fwidth)
//
// Mirrors `GlslRuntime.#derivative` and `GlslRuntime.wrapDerivatives`,
// noisemaker-for-cpu/src/csl/glsl-runtime.js:448-546.
//
// The reference keys every derivative call by a per-invocation ordinal
// (`derivativeIndex`, reset by `beginPixel`), runs the whole kernel body once
// per 2x2-quad corner in 'record' mode to capture each call's *input*, then
// replays the kernel once more to produce the real output from the differenced
// inputs.
//
// NARROWING IS DELIBERATELY ASYMMETRIC and this is load-bearing:
//   * scalars - `derivativeRecords[i] = value` stores a raw JS Number (:451),
//               so the difference is taken in double (:519-521) and narrowed
//               exactly once on the way out (`F32(selected)`, :461).
//   * vectors - the record is `Array.from(Float32Array)` and the x/y/footprint
//               buffers are themselves `Float32Array` (:524-531), so EVERY
//               component store narrows; the replay copy (`out.set`, :463)
//               narrows nothing further.
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

// Scalar form. Returns float: the reference narrows through `F32` on every
// return path that a wrapped kernel can reach.
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
  if (state != nullptr && state->mode == DerivativeMode::Replay
      && index < state->values.size() && state->values[index].lanes == 0U) {
    const DerivativeValue& computed = state->values[index];
    const double selected = kind == DerivativeKind::X      ? computed.scalar_x
                          : kind == DerivativeKind::Y      ? computed.scalar_y
                                                           : computed.scalar_width;
    return noisemaker::f32(selected);
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
  if (state != nullptr && state->mode == DerivativeMode::Record) {
    if (state->records.size() <= index) state->records.resize(index + 1U);
    DerivativeRecord& record = state->records[index];
    record.lanes = N;
    for (std::size_t lane = 0; lane < N; ++lane) record.vector[lane] = value[lane];
    for (std::size_t lane = 0; lane < N; ++lane) result[lane] = 0.0f;
    return result;  // zero-filled dummy (:453-455)
  }
  if (state != nullptr && state->mode == DerivativeMode::Replay
      && index < state->values.size() && state->values[index].lanes == N) {
    const DerivativeValue& computed = state->values[index];
    const float* selected = kind == DerivativeKind::X      ? computed.vector_x
                          : kind == DerivativeKind::Y      ? computed.vector_y
                                                           : computed.vector_width;
    for (std::size_t lane = 0; lane < N; ++lane) result[lane] = selected[lane];
    return result;
  }
  // 'approximate' fallback (:468-473). The reference's if/else-if chain is
  // reproduced exactly, including that the `else` binds to the second `if`:
  //   kind == X     -> [invW, 0, ...]
  //   kind == Y     -> [0, invH, ...]  (N >= 2 always here)
  //   kind == Width -> [invW, invH, ...]
  for (std::size_t lane = 0; lane < N; ++lane) result[lane] = 0.0f;
  const float inverse_w = noisemaker::f32(detail::inverse_width(context));
  const float inverse_h = noisemaker::f32(detail::inverse_height(context));
  if (kind != DerivativeKind::Y) result[0] = inverse_w;
  if (kind != DerivativeKind::X) result[1] = inverse_h;
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
[[nodiscard]] inline Vec<N, float> dFdx(const PixelContext& context, const Vec<N, float>& value) noexcept {
  return derivative_vector(context, value, DerivativeKind::X);
}
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> dFdy(const PixelContext& context, const Vec<N, float>& value) noexcept {
  return derivative_vector(context, value, DerivativeKind::Y);
}
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> fwidth(const PixelContext& context, const Vec<N, float>& value) noexcept {
  return derivative_vector(context, value, DerivativeKind::Width);
}

// A FloatExpr argument materializes first, mirroring the reference: a vector
// expression in JS is produced through `alloc()` into a Float32Array, so it is
// already narrowed by the time the derivative sees it. Scalars are NOT
// materialized - they reach `derivative_scalar` as an un-narrowed double,
// which is exactly the asymmetry documented above.
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> dFdx(const PixelContext& context, const FloatExpr<N>& value) noexcept {
  return derivative_vector(context, Vec<N, float>(value), DerivativeKind::X);
}
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> dFdy(const PixelContext& context, const FloatExpr<N>& value) noexcept {
  return derivative_vector(context, Vec<N, float>(value), DerivativeKind::Y);
}
template <std::size_t N>
[[nodiscard]] inline Vec<N, float> fwidth(const PixelContext& context, const FloatExpr<N>& value) noexcept {
  return derivative_vector(context, Vec<N, float>(value), DerivativeKind::Width);
}

// ---------------------------------------------------------------------------
// PixelContext gains one field. Defaulted to nullptr, so all 131 currently
// typed programs are bit-for-bit unaffected and pay nothing.
//
// struct PixelContext {
//   Vec2 uv{}; Vec4 frag_coord{}; Vec2 resolution{};
//   float time{}; float seed{}; std::uint32_t frame{}; float delta_time{};
//   DerivativeState* derivative = nullptr;   // <-- added
// };
//
// NOTE: `derivative_scalar`/`derivative_vector` reference PixelContext, so
// either forward-declare PixelContext above this block or move this block
// after the struct definition. Moving it after is simpler and is what the
// applied patch should do.
// ---------------------------------------------------------------------------
