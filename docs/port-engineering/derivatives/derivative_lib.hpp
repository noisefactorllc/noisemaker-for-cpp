// SHARED CORE for the gap-closure derivative prototypes (gap1/gap2/gap3).
//
// This header generalizes prototype.cpp's mechanism (DerivativeState carried
// through PixelContext, quad-aware probe/replay driver) to:
//   - vec3 and vec4 derivative overloads (Gap 1), in addition to the
//     existing scalar and vec2 overloads;
//   - an arbitrary number of derivative call sites per kernel invocation,
//     including sites inside helper functions and sites that execute a
//     different number of times per quad corner (Gap 2);
//   - arbitrary (non-8x8, including odd) canvas dimensions so the quad
//     driver's off-canvas probe behavior can be exercised at a real image
//     edge (Gap 3).
//
// Faithfulness to glsl-runtime.js's `#derivative`/`wrapDerivatives`
// (lines 448-546, read from
// ../noisemaker-for-cpu/src/csl/glsl-runtime.js,
// read-only) is the entire point of this file, in particular the
// **narrowing asymmetry** between the scalar and vector code paths:
//
//   - Scalar: the record stores the raw call-site input as a plain JS
//     Number (i.e. IEEE double). `derivativeValues[index] = {x, y, width}`
//     (glsl-runtime.js lines 518-521) is computed from those *unrounded*
//     doubles: `x = rightValue - leftValue`, `y = topValue - bottomValue`,
//     `width = Math.abs(x) + Math.abs(y)` -- no narrowing at all. Only the
//     one field actually *selected* by `kind` gets narrowed, once, via
//     `F32(selected)` at line 461, at the point `#derivative` returns.
//   - Vector: the record stores `Array.from(Float32Array)` (values already
//     float32-exact). But `derivativeValues[index]`'s `x`/`y`/`width` are
//     themselves `Float32Array`s (lines 524-526), so EVERY component store
//     (`x[componentIndex] = ...`, `y[componentIndex] = ...`,
//     `footprint[componentIndex] = ...`, lines 528-530) narrows to float32
//     immediately. `footprint[c]` is computed from the *already-narrowed*
//     `x[c]`/`y[c]` (a second rounding on top of the first), whereas the
//     scalar `width` is a *single* rounding of the raw double sum. These
//     can disagree by 1 ULP for inputs engineered so the exact
//     dFdx/dFdy difference needs more than float32's 24-bit mantissa to
//     represent -- see gap1_vec34.cpp for a concrete constructed case.
//
// This file lives ONLY under docs/port-engineering/derivatives/. It
// does not touch . or
// ../noisemaker-for-cpu.
//
// Build: any translation unit including this header must be compiled with
//   -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off
// (see gap*.cpp for exact invocations). -ffp-contract=off is required: with
// FMA fusion enabled, clang can fuse the multiply-adds inside the
// double-vs-float sensitivity case (and elsewhere) and silently produce a
// different bit pattern than the JS reference, which never fuses anything
// (JS has no FMA).

#pragma once

#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <unordered_map>

namespace deriv {

// ---------------------------------------------------------------------
// Minimal vector stand-ins (deliberately not the real noisemaker::glsl::Vec*
// types -- this is a standalone verification harness, not production code).
// ---------------------------------------------------------------------
struct Vec2 { float x{}, y{}; };
struct Vec3 { float x{}, y{}, z{}; };
struct Vec4 {
  float x{}, y{}, z{}, w{};
  [[nodiscard]] float& operator[](std::size_t i) noexcept {
    switch (i) { case 0: return x; case 1: return y; case 2: return z; default: return w; }
  }
  [[nodiscard]] float operator[](std::size_t i) const noexcept {
    switch (i) { case 0: return x; case 1: return y; case 2: return z; default: return w; }
  }
};

constexpr std::size_t kMaxDerivativeSites = 16;

enum class DerivativeMode : std::uint8_t { Approximate, Record, Replay };
enum class Kind : std::uint8_t { X, Y, Width };

// One recorded call-site input.
//   lanes == 0  -> scalar; `scalar_value` (double) is authoritative, mirrors
//                  glsl-runtime.js storing the raw JS Number.
//   lanes in {2,3,4} -> vector; `lane[0..lanes)` (float) is authoritative,
//                  mirrors `Array.from(Float32Array)` (already float32-exact).
struct DerivativeRecord {
  double scalar_value = 0.0;
  float lane[4]{};
  std::uint8_t lanes = 0;
  bool present = false;
};

// One replay-ready finite-difference sample.
//   lanes == 0  -> scalar_x/scalar_y/scalar_width are the authoritative
//                  *unrounded* doubles (narrowed only at selection time).
//   lanes > 0   -> x[]/y[]/width[] are the authoritative, ALREADY-narrowed
//                  (float) per-component values.
struct DerivativeSample {
  double scalar_x = 0.0, scalar_y = 0.0, scalar_width = 0.0;
  float x[4]{}, y[4]{}, width[4]{};
  std::uint8_t lanes = 0;
};

// Carried via PixelContext::derivative (non-owning, default nullptr) -- see
// derivatives-architecture.md section 2.2, Option B.
struct DerivativeState {
  DerivativeMode mode = DerivativeMode::Approximate;
  float inverse_width = 0.f;
  float inverse_height = 0.f;
  std::size_t ordinal = 0;
  std::array<DerivativeRecord, kMaxDerivativeSites> records{};
  std::size_t record_count = 0;
  std::array<DerivativeSample, kMaxDerivativeSites> replay{};
  std::size_t replay_count = 0;
};

inline void begin_pixel(DerivativeState& state) noexcept { state.ordinal = 0; }

struct PixelContext {
  Vec2 uv{};
  Vec4 frag_coord{};
  Vec2 resolution{};
  float time{};
  float seed{};
  std::uint32_t frame{};
  float delta_time{};
  DerivativeState* derivative = nullptr;
};

// ---------------------------------------------------------------------
// dFdx / dFdy / fwidth dispatch -- C++ analogue of `#derivative(value, kind)`
// (glsl-runtime.js lines 448-474).
// ---------------------------------------------------------------------
[[nodiscard]] inline float derivative_scalar(const PixelContext& ctx, float value, Kind kind) noexcept {
  DerivativeState* state = ctx.derivative;
  assert(state != nullptr && "derivative call outside a derivative-aware pass");
  const std::size_t index = state->ordinal++;
  if (state->mode == DerivativeMode::Record) {
    if (index < state->records.size()) {
      DerivativeRecord rec{};
      rec.scalar_value = static_cast<double>(value);
      rec.lanes = 0;
      rec.present = true;
      state->records[index] = rec;
      state->record_count = index + 1;
    }
    return 0.0f;
  }
  if (state->mode == DerivativeMode::Replay && index < state->replay_count) {
    const DerivativeSample& sample = state->replay[index];
    switch (kind) {
      case Kind::X: return static_cast<float>(sample.scalar_x);
      case Kind::Y: return static_cast<float>(sample.scalar_y);
      case Kind::Width: return static_cast<float>(sample.scalar_width);
    }
  }
  switch (kind) {
    case Kind::X: return state->inverse_width;
    case Kind::Y: return state->inverse_height;
    case Kind::Width: return state->inverse_width + state->inverse_height;
  }
  return 0.0f;
}

// Generic vector path, N in {2,3,4}. `value`/`out` point at N-element float
// arrays. Mirrors glsl-runtime.js's vector branches at lines 452-455 (record)
// and 462-464 (replay) and 468-473 (fallback).
inline void derivative_vector(const PixelContext& ctx, const float* value, std::uint8_t n, Kind kind, float* out) noexcept {
  DerivativeState* state = ctx.derivative;
  assert(state != nullptr && "derivative call outside a derivative-aware pass");
  const std::size_t index = state->ordinal++;
  if (state->mode == DerivativeMode::Record) {
    if (index < state->records.size()) {
      DerivativeRecord rec{};
      rec.lanes = n;
      rec.present = true;
      for (std::uint8_t i = 0; i < n; ++i) rec.lane[i] = value[i];
      state->records[index] = rec;
      state->record_count = index + 1;
    }
    for (std::uint8_t i = 0; i < n; ++i) out[i] = 0.f;
    return;
  }
  if (state->mode == DerivativeMode::Replay && index < state->replay_count) {
    const DerivativeSample& sample = state->replay[index];
    switch (kind) {
      case Kind::X: for (std::uint8_t i = 0; i < n; ++i) out[i] = sample.x[i]; return;
      case Kind::Y: for (std::uint8_t i = 0; i < n; ++i) out[i] = sample.y[i]; return;
      case Kind::Width: for (std::uint8_t i = 0; i < n; ++i) out[i] = sample.width[i]; return;
    }
  }
  for (std::uint8_t i = 0; i < n; ++i) out[i] = 0.f;
  if (kind != Kind::Y && n > 0) out[0] = state->inverse_width;
  if (kind != Kind::X && n > 1) out[1] = state->inverse_height;
  else if (kind == Kind::Y && n > 0) out[0] = state->inverse_height;
}

[[nodiscard]] inline float dFdx(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::X); }
[[nodiscard]] inline float dFdy(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::Y); }
[[nodiscard]] inline float fwidth(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::Width); }

[[nodiscard]] inline Vec2 dFdx(const PixelContext& ctx, Vec2 v) noexcept { float in[2]{v.x, v.y}, out[2]{}; derivative_vector(ctx, in, 2, Kind::X, out); return {out[0], out[1]}; }
[[nodiscard]] inline Vec2 dFdy(const PixelContext& ctx, Vec2 v) noexcept { float in[2]{v.x, v.y}, out[2]{}; derivative_vector(ctx, in, 2, Kind::Y, out); return {out[0], out[1]}; }
[[nodiscard]] inline Vec2 fwidth(const PixelContext& ctx, Vec2 v) noexcept { float in[2]{v.x, v.y}, out[2]{}; derivative_vector(ctx, in, 2, Kind::Width, out); return {out[0], out[1]}; }

[[nodiscard]] inline Vec3 dFdx(const PixelContext& ctx, Vec3 v) noexcept { float in[3]{v.x, v.y, v.z}, out[3]{}; derivative_vector(ctx, in, 3, Kind::X, out); return {out[0], out[1], out[2]}; }
[[nodiscard]] inline Vec3 dFdy(const PixelContext& ctx, Vec3 v) noexcept { float in[3]{v.x, v.y, v.z}, out[3]{}; derivative_vector(ctx, in, 3, Kind::Y, out); return {out[0], out[1], out[2]}; }
[[nodiscard]] inline Vec3 fwidth(const PixelContext& ctx, Vec3 v) noexcept { float in[3]{v.x, v.y, v.z}, out[3]{}; derivative_vector(ctx, in, 3, Kind::Width, out); return {out[0], out[1], out[2]}; }

[[nodiscard]] inline Vec4 dFdx(const PixelContext& ctx, Vec4 v) noexcept { float in[4]{v.x, v.y, v.z, v.w}, out[4]{}; derivative_vector(ctx, in, 4, Kind::X, out); return {out[0], out[1], out[2], out[3]}; }
[[nodiscard]] inline Vec4 dFdy(const PixelContext& ctx, Vec4 v) noexcept { float in[4]{v.x, v.y, v.z, v.w}, out[4]{}; derivative_vector(ctx, in, 4, Kind::Y, out); return {out[0], out[1], out[2], out[3]}; }
[[nodiscard]] inline Vec4 fwidth(const PixelContext& ctx, Vec4 v) noexcept { float in[4]{v.x, v.y, v.z, v.w}, out[4]{}; derivative_vector(ctx, in, 4, Kind::Width, out); return {out[0], out[1], out[2], out[3]}; }

// ---------------------------------------------------------------------
// Quad math -- C++ analogue of glsl-runtime.js's wrapDerivatives' per-index
// derivativeValues computation (lines 512-533), including the narrowing
// asymmetry described at the top of this file.
// ---------------------------------------------------------------------
[[nodiscard]] inline DerivativeSample compute_sample(const DerivativeRecord& l, const DerivativeRecord& r,
                                                       const DerivativeRecord& b, const DerivativeRecord& t) noexcept {
  DerivativeSample sample{};
  const std::uint8_t lanes = std::max({l.lanes, r.lanes, b.lanes, t.lanes});
  sample.lanes = lanes;
  if (lanes == 0) {
    // Scalar path: full double precision, no narrowing until #derivative
    // selects and returns one of x/y/width (mirrors lines 518-521 exactly).
    sample.scalar_x = r.scalar_value - l.scalar_value;
    sample.scalar_y = t.scalar_value - b.scalar_value;
    sample.scalar_width = std::fabs(sample.scalar_x) + std::fabs(sample.scalar_y);
    return sample;
  }
  // Vector path: component() broadcast for any scalar-shaped fallback
  // records mixed in (glsl-runtime.js's `component(value, index)`, line 11:
  // isVector(value) ? value[index] : value) -- narrow every component
  // immediately (mirrors Float32Array element stores at lines 528-530).
  auto component = [](const DerivativeRecord& rec, std::uint8_t i) -> double {
    return rec.lanes > 0 ? static_cast<double>(rec.lane[i]) : rec.scalar_value;
  };
  for (std::uint8_t i = 0; i < lanes; ++i) {
    const double lv = component(l, i);
    const double rv = component(r, i);
    const double bv = component(b, i);
    const double tv = component(t, i);
    sample.x[i] = static_cast<float>(rv - lv);
    sample.y[i] = static_cast<float>(tv - bv);
    sample.width[i] = static_cast<float>(std::fabs(static_cast<double>(sample.x[i])) + std::fabs(static_cast<double>(sample.y[i])));
  }
  return sample;
}

// ---------------------------------------------------------------------
// Generic quad-aware pass driver -- C++ analogue of wrapDerivatives()
// (lines 476-546). Parameterized on an actual PixelFn pointer (unlike
// prototype.cpp's v1, which hardcoded a single global `pixel` -- this
// version is reused across gap1/gap2/gap3's different kernels) and on
// runtime width/height (not compile-time), so Gap 3's odd/non-square
// canvases can reuse the same driver.
//
// NOTE: unlike the real production `noisemaker::PixelFn`
// (`void(*)(const KernelState&, const PixelContext&, Vec4&) noexcept`,
// which always writes exactly 4 RGBA floats), this harness's PixelFn
// writes into a caller-sized `float*` scratch buffer, because the gap1/
// gap2 verification kernels report many more than 4 derivative-result
// lanes per pixel for comparison purposes. This is a verification-harness
// liberty, not a claim about the production interface (see
// derivatives-architecture.md section 2.2 for the actual production
// PixelContext/PixelFn contract this prototype is modeling).
// ---------------------------------------------------------------------
template <typename KernelState>
using PixelFn = void (*)(const KernelState&, const PixelContext&, float* out) noexcept;

struct QuadKey {
  std::int64_t qx, qy;
  bool operator==(const QuadKey& other) const noexcept { return qx == other.qx && qy == other.qy; }
};
struct QuadKeyHash {
  std::size_t operator()(const QuadKey& k) const noexcept {
    return std::hash<std::int64_t>{}(k.qx) ^ (std::hash<std::int64_t>{}(k.qy) << 1);
  }
};

struct QuadCacheEntry {
  std::array<std::array<DerivativeRecord, kMaxDerivativeSites>, 4> corner_records{};
  std::array<std::size_t, 4> corner_counts{};
  std::size_t remaining = 0;
};

template <typename KernelState>
void probe(const KernelState& state, PixelFn<KernelState> kernel_fn, const PixelContext& real_context,
           float fx, float fy, float width, float height, DerivativeState& scratch,
           std::array<DerivativeRecord, kMaxDerivativeSites>& out_records, std::size_t& out_count,
           float* scratch_out, std::size_t scratch_out_len) {
  PixelContext probe_context = real_context;
  probe_context.frag_coord = Vec4{fx, fy, 0.f, 1.f};
  probe_context.uv = Vec2{fx / width, fy / height};
  scratch.mode = DerivativeMode::Record;
  scratch.record_count = 0;
  probe_context.derivative = &scratch;
  for (std::size_t i = 0; i < scratch_out_len; ++i) scratch_out[i] = 0.f;
  kernel_fn(state, probe_context, scratch_out);
  out_records = scratch.records;
  out_count = scratch.record_count;
}

// `out` must have room for `out_len` floats. `scratch_out_len` must be >=
// the widest `out` any of the four probe invocations will write (probe
// outputs are discarded, matching JS's `temporary` in wrapDerivatives).
template <typename KernelState>
void run_pixel_with_derivatives(const KernelState& state, PixelFn<KernelState> kernel_fn,
                                 float col, float row, float width, float height,
                                 float time, float seed, std::uint32_t frame, float delta_time,
                                 std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash>& cache,
                                 float* out, std::size_t out_len) {
  const float fragX = col + 0.5f;
  const float fragY = (height - row) - 0.5f;
  const Vec2 resolution{width, height};

  PixelContext real_context{
      .uv = Vec2{fragX / width, fragY / height},
      .frag_coord = Vec4{fragX, fragY, 0.f, 1.f},
      .resolution = resolution,
      .time = time,
      .seed = seed,
      .frame = frame,
      .delta_time = delta_time,
      .derivative = nullptr,
  };

  const std::int64_t pixelX = static_cast<std::int64_t>(std::floor(fragX - 0.5f));
  const std::int64_t pixelY = static_cast<std::int64_t>(std::floor(fragY - 0.5f));
  const std::int64_t quadX = pixelX >> 1;
  const std::int64_t quadY = pixelY >> 1;
  const QuadKey key{quadX, quadY};

  auto found = cache.find(key);
  if (found == cache.end()) {
    QuadCacheEntry entry;
    const float x0 = static_cast<float>(quadX * 2) + 0.5f;
    const float y0 = static_cast<float>(quadY * 2) + 0.5f;
    DerivativeState scratch;
    scratch.inverse_width = 1.0f / width;
    scratch.inverse_height = 1.0f / height;
    std::array<float, 64> scratch_out{};
    probe(state, kernel_fn, real_context, x0, y0, width, height, scratch, entry.corner_records[0], entry.corner_counts[0], scratch_out.data(), scratch_out.size());
    probe(state, kernel_fn, real_context, x0 + 1.f, y0, width, height, scratch, entry.corner_records[1], entry.corner_counts[1], scratch_out.data(), scratch_out.size());
    probe(state, kernel_fn, real_context, x0, y0 + 1.f, width, height, scratch, entry.corner_records[2], entry.corner_counts[2], scratch_out.data(), scratch_out.size());
    probe(state, kernel_fn, real_context, x0 + 1.f, y0 + 1.f, width, height, scratch, entry.corner_records[3], entry.corner_counts[3], scratch_out.data(), scratch_out.size());

    entry.remaining = 0;
    for (std::int64_t dy = 0; dy < 2; ++dy) {
      for (std::int64_t dx = 0; dx < 2; ++dx) {
        const std::int64_t px = quadX * 2 + dx;
        const std::int64_t py = quadY * 2 + dy;
        if (px >= 0 && px < static_cast<std::int64_t>(width) && py >= 0 && py < static_cast<std::int64_t>(height)) {
          entry.remaining += 1;
        }
      }
    }
    found = cache.emplace(key, entry).first;
  }

  QuadCacheEntry& entry = found->second;
  const std::int64_t xParity = pixelX & 1;
  const std::int64_t yParity = pixelY & 1;
  const auto& left = entry.corner_records[static_cast<std::size_t>(yParity * 2)];
  const std::size_t left_n = entry.corner_counts[static_cast<std::size_t>(yParity * 2)];
  const auto& right = entry.corner_records[static_cast<std::size_t>(yParity * 2 + 1)];
  const std::size_t right_n = entry.corner_counts[static_cast<std::size_t>(yParity * 2 + 1)];
  const auto& bottom = entry.corner_records[static_cast<std::size_t>(xParity)];
  const std::size_t bottom_n = entry.corner_counts[static_cast<std::size_t>(xParity)];
  const auto& top = entry.corner_records[static_cast<std::size_t>(xParity + 2)];
  const std::size_t top_n = entry.corner_counts[static_cast<std::size_t>(xParity + 2)];

  const std::size_t count = std::max({left_n, right_n, bottom_n, top_n});

  DerivativeState replay_state;
  replay_state.mode = DerivativeMode::Replay;
  replay_state.inverse_width = 1.0f / width;
  replay_state.inverse_height = 1.0f / height;
  replay_state.replay_count = count;
  for (std::size_t i = 0; i < count; ++i) {
    // Fallback chaining matches glsl-runtime.js lines 514-517 exactly:
    // missing right falls back to left; missing top falls back to bottom
    // (NOT to 0).
    const DerivativeRecord& l = (i < left_n) ? left[i] : DerivativeRecord{};
    const DerivativeRecord& r = (i < right_n) ? right[i] : l;
    const DerivativeRecord& b = (i < bottom_n) ? bottom[i] : DerivativeRecord{};
    const DerivativeRecord& tp = (i < top_n) ? top[i] : b;
    replay_state.replay[i] = compute_sample(l, r, b, tp);
  }

  real_context.derivative = &replay_state;
  for (std::size_t i = 0; i < out_len; ++i) out[i] = 0.f;
  kernel_fn(state, real_context, out);

  entry.remaining -= 1;
  if (entry.remaining == 0) cache.erase(found);
}

}  // namespace deriv
