// STANDALONE PROTOTYPE — screen-space derivative (dFdx/dFdy/fwidth) support
// for the noisemaker-for-cpp typed-kernel runtime.
//
// This file lives ONLY under docs/port-engineering/derivatives/. It
// does not touch . or
// ../noisemaker-for-cpu. It demonstrates the proposed
// mechanism end to end:
//
//   1. A DerivativeState carried through PixelContext (NOT a signature
//      change to the existing PixelFn typedef, NOT a thread_local).
//   2. dFdx/dFdy/fwidth free functions that dispatch on DerivativeState::mode
//      exactly like glsl-runtime.js's `#derivative` (record / replay /
//      approximate fallback).
//   3. A quad-aware pass driver equivalent to glsl-runtime.js's
//      `wrapDerivatives`: 2x2 quad corner probing with a reference-counted
//      cache, coarse dFdx/dFdy sharing within row-pairs/column-pairs.
//
// Build: clang++ -std=c++20 -ffp-contract=off -O2 -o prototype prototype.cpp
//
// The kernel under test matches reference_probe.mjs exactly:
//   float t = 3*uv.x*uv.x + 5*uv.y*uv.y - 2*uv.x*uv.y;
//   float gx = dFdx(t);
//   float gy = dFdy(t);
//   vec2  fwv = fwidth(uv);
//   out = vec4(gx, gy, fwv.x, fwv.y);

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <unordered_map>
#include <vector>
#include <cmath>
#include <cassert>

namespace proto {

// ---------------------------------------------------------------------
// Minimal stand-ins for noisemaker::glsl::Vec2 / Vec4 / PixelContext.
// ---------------------------------------------------------------------
struct Vec2 { float x{}, y{}; };
struct Vec4 { float v[4]{}; float& operator[](std::size_t i) noexcept { return v[i]; } float operator[](std::size_t i) const noexcept { return v[i]; } };

constexpr std::size_t kMaxDerivativeSites = 8;

enum class DerivativeMode : std::uint8_t { Approximate, Record, Replay };

// One recorded call-site input, up to 4 lanes (vec4 is the widest GLSL
// vector type that can flow through dFdx/dFdy/fwidth in this codebase).
struct DerivativeRecord {
  float lane[4]{};
  std::uint8_t lanes = 0; // 0 == "not a vector" (scalar), else lane count
};

// One replay-ready finite-difference sample: x = dFdx, y = dFdy,
// width = fwidth, mirroring glsl-runtime.js lines 511-533 exactly
// (including that `width` is computed once and shared by all three kinds).
struct DerivativeSample {
  float x[4]{};
  float y[4]{};
  float width[4]{};
  std::uint8_t lanes = 0;
};

// Carried via PixelContext::derivative (non-owning pointer, default
// nullptr). This is the ONLY change to PixelContext: one new pointer field
// with a default member initializer, so every existing designated-initializer
// construction of PixelContext in pass_runner.cpp (and all 131 generated
// non-derivative kernels, which never reference context.derivative) is
// byte-for-byte unaffected. No PixelFn signature change.
struct DerivativeState {
  DerivativeMode mode = DerivativeMode::Approximate;
  float inverse_width = 0.f;
  float inverse_height = 0.f;

  // ordinal cursor, reset to 0 at the start of every kernel invocation
  // (equivalent of glsl-runtime.js's beginPixel() zeroing derivativeIndex).
  std::size_t ordinal = 0;

  // record pass
  std::array<DerivativeRecord, kMaxDerivativeSites> records{};
  std::size_t record_count = 0;

  // replay pass (populated by the quad driver before the real call)
  std::array<DerivativeSample, kMaxDerivativeSites> replay{};
  std::size_t replay_count = 0;
};

struct PixelContext {
  Vec2 uv{};
  Vec4 frag_coord{};
  Vec2 resolution{};
  float time{};
  float seed{};
  std::uint32_t frame{};
  float delta_time{};
  DerivativeState* derivative = nullptr; // <-- the only addition
};

inline void begin_pixel(DerivativeState& state) noexcept { state.ordinal = 0; }

// ---------------------------------------------------------------------
// dFdx / dFdy / fwidth dispatch — the C++ analogue of glsl-runtime.js's
// `#derivative(value, kind)` (lines 448-474).
// ---------------------------------------------------------------------
enum class Kind : std::uint8_t { X, Y, Width };

[[nodiscard]] inline float derivative_scalar(const PixelContext& ctx, float value, Kind kind) noexcept {
  DerivativeState* state = ctx.derivative;
  assert(state != nullptr && "derivative call outside a derivative-aware pass");
  const std::size_t index = state->ordinal++;
  if (state->mode == DerivativeMode::Record) {
    if (index < state->records.size()) {
      state->records[index] = DerivativeRecord{{value, 0, 0, 0}, 0};
      state->record_count = index + 1;
    }
    return 0.0f; // dummy, matches JS line 452-455's zero-filled `out`
  }
  if (state->mode == DerivativeMode::Replay && index < state->replay_count) {
    const DerivativeSample& sample = state->replay[index];
    switch (kind) {
      case Kind::X: return sample.x[0];
      case Kind::Y: return sample.y[0];
      case Kind::Width: return sample.width[0];
    }
  }
  // approximate fallback — glsl-runtime.js lines 467-473, scalar branch.
  switch (kind) {
    case Kind::X: return state->inverse_width;
    case Kind::Y: return state->inverse_height;
    case Kind::Width: return state->inverse_width + state->inverse_height;
  }
  return 0.0f;
}

[[nodiscard]] inline Vec2 derivative_vec2(const PixelContext& ctx, Vec2 value, Kind kind) noexcept {
  DerivativeState* state = ctx.derivative;
  assert(state != nullptr && "derivative call outside a derivative-aware pass");
  const std::size_t index = state->ordinal++;
  if (state->mode == DerivativeMode::Record) {
    if (index < state->records.size()) {
      state->records[index] = DerivativeRecord{{value.x, value.y, 0, 0}, 2};
      state->record_count = index + 1;
    }
    return Vec2{0.f, 0.f};
  }
  if (state->mode == DerivativeMode::Replay && index < state->replay_count) {
    const DerivativeSample& sample = state->replay[index];
    switch (kind) {
      case Kind::X: return Vec2{sample.x[0], sample.x[1]};
      case Kind::Y: return Vec2{sample.y[0], sample.y[1]};
      case Kind::Width: return Vec2{sample.width[0], sample.width[1]};
    }
  }
  // approximate fallback, vector branch — glsl-runtime.js lines 467-473.
  Vec2 out{0.f, 0.f};
  if (kind != Kind::Y) out.x = state->inverse_width;
  if (kind != Kind::X) out.y = state->inverse_height;
  else if (kind == Kind::Y) out.x = state->inverse_height; // mirrors the odd JS out[0]=inverseHeight branch for 1-lane vectors; unreachable for our 2-lane case but included for fidelity
  return out;
}

[[nodiscard]] inline float dFdx(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::X); }
[[nodiscard]] inline float dFdy(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::Y); }
[[nodiscard]] inline float fwidth(const PixelContext& ctx, float v) noexcept { return derivative_scalar(ctx, v, Kind::Width); }
[[nodiscard]] inline Vec2 dFdx(const PixelContext& ctx, Vec2 v) noexcept { return derivative_vec2(ctx, v, Kind::X); }
[[nodiscard]] inline Vec2 dFdy(const PixelContext& ctx, Vec2 v) noexcept { return derivative_vec2(ctx, v, Kind::Y); }
[[nodiscard]] inline Vec2 fwidth(const PixelContext& ctx, Vec2 v) noexcept { return derivative_vec2(ctx, v, Kind::Width); }

// ---------------------------------------------------------------------
// The kernel under test (hand-written "typed_N::pixel()" stand-in).
// Signature matches noisemaker::PixelFn exactly:
//   void(*)(const KernelState&, const PixelContext&, Vec4&) noexcept
// ---------------------------------------------------------------------
struct KernelState {};

void pixel(const KernelState&, const PixelContext& context, Vec4& out) noexcept {
  if (context.derivative != nullptr) begin_pixel(*context.derivative);

  const float uvx = context.uv.x;
  const float uvy = context.uv.y;
  const float uvx2 = uvx * uvx;
  const float uvy2 = uvy * uvy;
  const float cross = uvx * uvy;
  const float term1 = 3.0f * uvx2;
  const float term2 = 5.0f * uvy2;
  const float term3 = 2.0f * cross;
  const float t = (term1 + term2) - term3;

  const float gx = dFdx(context, t);
  const float gy = dFdy(context, t);
  const Vec2 fwv = fwidth(context, Vec2{uvx, uvy});

  out[0] = gx;
  out[1] = gy;
  out[2] = fwv.x;
  out[3] = fwv.y;
}

// ---------------------------------------------------------------------
// Quad-aware pass driver — the C++ analogue of glsl-runtime.js's
// wrapDerivatives() (lines 476-546), adapted to pass_runner.cpp's
// raster convention: frag_coord.y = height - row - 0.5 (row 0 = top of
// image = LARGEST frag_coord.y).
// ---------------------------------------------------------------------
using PixelFn = void (*)(const KernelState&, const PixelContext&, Vec4&) noexcept;

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
  std::size_t remaining = 0; // reference count: number of in-bounds member pixels not yet consumed
};

// Runs one probe: evaluates the kernel body once in Record mode at fragment
// coordinate (fx, fy), sharing every other context field with the real
// pixel's context (mirrors `{ ...context, fragCoord, uv }` at
// glsl-runtime.js lines 482-486). NOTE: fx/fy may fall outside the image
// bounds (off-canvas neighbor of an edge pixel) — this is intentional and
// matches the JS reference, which does not bounds-check probe coordinates.
void probe(const KernelState& state, const PixelContext& real_context, float fx, float fy,
           float width, float height, DerivativeState& scratch,
           std::array<DerivativeRecord, kMaxDerivativeSites>& out_records, std::size_t& out_count) {
  PixelContext probe_context = real_context;
  probe_context.frag_coord = Vec4{fx, fy, 0.f, 1.f};
  probe_context.uv = Vec2{fx / width, fy / height};
  scratch.mode = DerivativeMode::Record;
  scratch.record_count = 0;
  probe_context.derivative = &scratch;
  Vec4 dummy;
  pixel(state, probe_context, dummy);
  out_records = scratch.records;
  out_count = scratch.record_count;
}

Vec4 run_pixel_with_derivatives(const KernelState& state, PixelFn /*unused, pixel() called directly*/,
                                 float col, float row, float width, float height,
                                 float time, float seed, std::uint32_t frame, float delta_time,
                                 std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash>& cache) {
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
    // corner order matches glsl-runtime.js lines 502: [ (x0,y0), (x0+1,y0), (x0,y0+1), (x0+1,y0+1) ]
    probe(state, real_context, x0, y0, width, height, scratch, entry.corner_records[0], entry.corner_counts[0]);
    probe(state, real_context, x0 + 1.f, y0, width, height, scratch, entry.corner_records[1], entry.corner_counts[1]);
    probe(state, real_context, x0, y0 + 1.f, width, height, scratch, entry.corner_records[2], entry.corner_counts[2]);
    probe(state, real_context, x0 + 1.f, y0 + 1.f, width, height, scratch, entry.corner_records[3], entry.corner_counts[3]);

    // remaining = number of this quad's member pixels that are in-bounds.
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
  // left/right share the pixel's own row (dFdx); bottom/top share the
  // pixel's own column (dFdy) — glsl-runtime.js lines 505-510.
  const auto& left = entry.corner_records[yParity * 2];
  const std::size_t left_n = entry.corner_counts[yParity * 2];
  const auto& right = entry.corner_records[yParity * 2 + 1];
  const std::size_t right_n = entry.corner_counts[yParity * 2 + 1];
  const auto& bottom = entry.corner_records[xParity];
  const std::size_t bottom_n = entry.corner_counts[xParity];
  const auto& top = entry.corner_records[xParity + 2];
  const std::size_t top_n = entry.corner_counts[xParity + 2];

  const std::size_t count = std::max({left_n, right_n, bottom_n, top_n});

  DerivativeState replay_state;
  replay_state.mode = DerivativeMode::Replay;
  replay_state.inverse_width = 1.0f / width;
  replay_state.inverse_height = 1.0f / height;
  replay_state.replay_count = count;
  for (std::size_t i = 0; i < count; ++i) {
    // fallback chaining matches glsl-runtime.js lines 514-517 exactly:
    // missing right falls back to left; missing top falls back to bottom.
    const DerivativeRecord& l = (i < left_n) ? left[i] : DerivativeRecord{};
    const DerivativeRecord& r = (i < right_n) ? right[i] : l;
    const DerivativeRecord& b = (i < bottom_n) ? bottom[i] : DerivativeRecord{};
    const DerivativeRecord& tp = (i < top_n) ? top[i] : b;
    const std::uint8_t lanes = std::max({l.lanes, r.lanes, b.lanes, tp.lanes});
    DerivativeSample sample{};
    sample.lanes = lanes;
    const std::size_t width_lanes = lanes == 0 ? 1 : lanes;
    for (std::size_t lane = 0; lane < width_lanes; ++lane) {
      const float lv = l.lane[lane];
      const float rv = r.lane[lane];
      const float bv = b.lane[lane];
      const float tv = tp.lane[lane];
      sample.x[lane] = rv - lv;
      sample.y[lane] = tv - bv;
      sample.width[lane] = std::fabs(sample.x[lane]) + std::fabs(sample.y[lane]);
    }
    replay_state.replay[i] = sample;
  }

  real_context.derivative = &replay_state;
  Vec4 output;
  pixel(state, real_context, output);

  entry.remaining -= 1;
  if (entry.remaining == 0) cache.erase(found);

  return output;
}

} // namespace proto

int main() {
  using namespace proto;
  constexpr int WIDTH = 8;
  constexpr int HEIGHT = 8;

  KernelState state;
  std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash> cache;

  std::vector<float> results(static_cast<std::size_t>(WIDTH) * HEIGHT * 4);
  std::FILE* csv = std::fopen("prototype_output.csv", "w");
  std::fprintf(csv, "row,col,gx(dFdx t),gy(dFdy t),fwidth(uv).x,fwidth(uv).y\n");

  for (int row = 0; row < HEIGHT; ++row) {
    for (int col = 0; col < WIDTH; ++col) {
      const Vec4 out = run_pixel_with_derivatives(state, &pixel, static_cast<float>(col), static_cast<float>(row),
                                                    static_cast<float>(WIDTH), static_cast<float>(HEIGHT),
                                                    0.f, 0.f, 0u, 0.f, cache);
      const std::size_t base = (static_cast<std::size_t>(row) * WIDTH + col) * 4;
      results[base + 0] = out[0];
      results[base + 1] = out[1];
      results[base + 2] = out[2];
      results[base + 3] = out[3];
      std::fprintf(csv, "%d,%d,%.9g,%.9g,%.9g,%.9g\n", row, col, out[0], out[1], out[2], out[3]);
    }
  }
  std::fclose(csv);

  assert(cache.empty() && "quad cache must be fully evicted after a full raster pass");

  std::ofstream bin("prototype_output.f32", std::ios::binary);
  bin.write(reinterpret_cast<const char*>(results.data()), static_cast<std::streamsize>(results.size() * sizeof(float)));
  bin.close();

  std::printf("wrote prototype_output.f32 and prototype_output.csv, quad cache entries remaining=%zu\n", cache.size());
  return 0;
}
