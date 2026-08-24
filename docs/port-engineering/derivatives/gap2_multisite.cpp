// GAP 2 — multi-call-site ordinal interleaving.
//
// Kernel A ("interleaved"): six derivative call sites of mixed kinds
// (dFdx/dFdy/fwidth) and mixed widths (scalar/vec2/vec3), executed in a
// fixed order, including a helper function containing one derivative call
// that is invoked TWICE from the kernel body (mirrors
// filter/halftone/halftone.glsl's `halftoneCoverage`/`roundDotCoverage`
// pattern of two unconditional fwidth call sites — except here it's the
// SAME textual call site executed twice, which is actually the sharper
// test of "ordinal is a per-invocation counter, not a per-source-line
// identity": both executions must land at DIFFERENT ordinals (3 and 5
// below) even though they're the same line of source).
//
// Kernel B ("branchy"): exercises glsl-runtime.js's missing-ordinal
// fallback (lines 514-517: `left[i] ?? 0`, `right[i] ?? leftValue`,
// `bottom[i] ?? 0`, `top[i] ?? bottomValue` -- right/top fall back to
// left/bottom, NOT to 0) by branching a derivative call on `uv.x`, which
// DOES vary between quad corners (unlike the real 17 programs' uniform
// `antialias` gate -- see derivatives-architecture.md section 3.2). This
// is a deliberately-constructed stress case, not a claim that any real
// program does this.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -o gap2_multisite gap2_multisite.cpp

#include "derivative_lib.hpp"

#include <cstdio>
#include <fstream>
#include <vector>

namespace gap2 {
using namespace deriv;

struct KernelState {};

// ---------------------------------------------------------------------
// Kernel A: interleaved multi-call-site kernel.
// ---------------------------------------------------------------------
[[nodiscard]] float helper_scalar(const PixelContext& ctx, float x) noexcept {
  const float s = (x * x) + 0.5f;
  return dFdx(ctx, s);  // one derivative call site, invoked from two call sites in pixel_a().
}

void pixel_a(const KernelState&, const PixelContext& context, float* out) noexcept {
  if (context.derivative != nullptr) begin_pixel(*context.derivative);

  const float uvx = context.uv.x;
  const float uvy = context.uv.y;

  const float t1 = (3.0f * uvx) - uvy;
  const float a = dFdx(context, t1);  // ordinal 0: scalar

  Vec3 v3{uvx + uvy, uvx * uvy, uvx - uvy};
  const Vec3 b = fwidth(context, v3);  // ordinal 1: vec3

  Vec2 v2{uvx * 2.0f, uvy * 3.0f};
  const Vec2 c = dFdy(context, v2);  // ordinal 2: vec2

  const float d1 = helper_scalar(context, uvx);  // ordinal 3: scalar, inside helper, 1st call

  const float t2 = (uvx * uvx) + (uvy * uvy);
  const float e = fwidth(context, t2);  // ordinal 4: scalar

  const float d2 = helper_scalar(context, uvy);  // ordinal 5: scalar, inside helper, 2nd call

  out[0] = a;
  out[1] = b.x; out[2] = b.y; out[3] = b.z;
  out[4] = c.x; out[5] = c.y;
  out[6] = d1;
  out[7] = e;
  out[8] = d2;
}

// ---------------------------------------------------------------------
// Kernel B: branchy kernel with a per-pixel-varying (not uniform) gate
// around a derivative call, so different quad corners execute a different
// NUMBER of derivative calls -- the missing-ordinal fallback landmine.
// ---------------------------------------------------------------------
void pixel_b(const KernelState&, const PixelContext& context, float* out) noexcept {
  if (context.derivative != nullptr) begin_pixel(*context.derivative);

  const float uvx = context.uv.x;
  const float uvy = context.uv.y;

  const float t1 = (2.0f * uvx) - uvy;
  const float s1 = dFdx(context, t1);  // ordinal 0: always executed

  const float t2 = uvx + (2.0f * uvy);
  const float s2 = fwidth(context, t2);  // ordinal 1: always executed

  float s3 = 0.0f;
  // Gated on uv.y (not uv.x) because s3 is a dFdy call: dFdy's fallback
  // pair is bottom/top (same column, different row -> same-row corners
  // share uv.x but differ in uv.y), so the gate must vary with uv.y to
  // desynchronize that specific pair. Threshold 0.6 chosen so quadY=2's
  // bottom corner (uv.y=0.5) takes the branch and its top corner
  // (uv.y=0.625) does not, AND the real output pixel at row=3 (whose own
  // uv.y=0.5625) also takes the branch, so the fallback-substituted
  // ordinal-2 value is actually observable in that pixel's output.
  if (uvy < 0.6f) {
    const float t3 = (uvx * uvx) + uvy;
    s3 = dFdy(context, t3);  // ordinal 2: CONDITIONAL -- varies per quad corner
  }

  out[0] = s1;
  out[1] = s2;
  out[2] = s3;
}

}  // namespace gap2

template <typename KernelFn>
void run_grid(const char* csv_path, const char* bin_path, KernelFn kernel_fn, int lanes, const char* const* names) {
  using namespace gap2;
  constexpr int WIDTH = 8;
  constexpr int HEIGHT = 8;

  KernelState state;
  std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash> cache;
  std::vector<float> results(static_cast<std::size_t>(WIDTH) * HEIGHT * static_cast<std::size_t>(lanes));

  std::FILE* csv = std::fopen(csv_path, "w");
  std::fprintf(csv, "row,col");
  for (int i = 0; i < lanes; ++i) std::fprintf(csv, ",%s", names[i]);
  std::fprintf(csv, "\n");

  for (int row = 0; row < HEIGHT; ++row) {
    for (int col = 0; col < WIDTH; ++col) {
      std::vector<float> out(static_cast<std::size_t>(lanes), 0.f);
      run_pixel_with_derivatives<KernelState>(state, kernel_fn, static_cast<float>(col), static_cast<float>(row),
                                                static_cast<float>(WIDTH), static_cast<float>(HEIGHT),
                                                0.f, 0.f, 0u, 0.f, cache, out.data(), out.size());
      const std::size_t base = (static_cast<std::size_t>(row) * WIDTH + col) * static_cast<std::size_t>(lanes);
      std::fprintf(csv, "%d,%d", row, col);
      for (int i = 0; i < lanes; ++i) {
        results[base + static_cast<std::size_t>(i)] = out[static_cast<std::size_t>(i)];
        std::fprintf(csv, ",%.9g", static_cast<double>(out[static_cast<std::size_t>(i)]));
      }
      std::fprintf(csv, "\n");
    }
  }
  std::fclose(csv);
  assert(cache.empty() && "quad cache must be fully evicted after a full raster pass");

  std::ofstream bin(bin_path, std::ios::binary);
  bin.write(reinterpret_cast<const char*>(results.data()), static_cast<std::streamsize>(results.size() * sizeof(float)));
  bin.close();
  std::printf("wrote %s and %s, quad cache entries remaining=%zu\n", bin_path, csv_path, cache.size());
}

int main() {
  using namespace gap2;

  const char* namesA[9] = {"a", "b.x", "b.y", "b.z", "c.x", "c.y", "d1", "e", "d2"};
  run_grid("gap2a_interleaved_output.csv", "gap2a_interleaved_output.f32", &pixel_a, 9, namesA);

  const char* namesB[3] = {"s1", "s2", "s3"};
  run_grid("gap2b_branchy_output.csv", "gap2b_branchy_output.f32", &pixel_b, 3, namesB);

  // Diagnostic: prove the missing-ordinal fallback path was actually
  // exercised for quadX=0, quadY=2 (bottom corner (0,4) takes the uv.y<0.6
  // branch, top corner (0,5) does not), and show what the WRONG
  // ("top falls back to 0" instead of "top falls back to bottomValue")
  // answer would have been, for contrast.
  {
    KernelState state;
    DerivativeState scratch;
    scratch.inverse_width = 1.0f / 8.0f;
    scratch.inverse_height = 1.0f / 8.0f;
    PixelContext dummy_ctx{};
    std::array<DerivativeRecord, kMaxDerivativeSites> bottom_records{}, top_records{};
    std::size_t bottom_count = 0, top_count = 0;
    std::array<float, 8> scratch_out{};
    probe<KernelState>(state, &pixel_b, dummy_ctx, 0.5f, 4.5f, 8.f, 8.f, scratch, bottom_records, bottom_count, scratch_out.data(), scratch_out.size());
    probe<KernelState>(state, &pixel_b, dummy_ctx, 0.5f, 5.5f, 8.f, 8.f, scratch, top_records, top_count, scratch_out.data(), scratch_out.size());
    std::printf("gap2b diagnostic: bottom corner (0,4) record_count=%zu top corner (0,5) record_count=%zu\n", bottom_count, top_count);
    const double bottomValue = bottom_records[2].scalar_value;
    std::printf("gap2b diagnostic: bottom ordinal-2 recorded value=%.9g (top ordinal-2 MISSING -> falls back to this, NOT to 0)\n", bottomValue);
    std::printf("gap2b diagnostic: correct y (top falls back to bottomValue) = %.9g; WRONG (top falls back to 0) would have been %.9g\n",
                bottomValue - bottomValue, 0.0 - bottomValue);
  }

  return 0;
}
