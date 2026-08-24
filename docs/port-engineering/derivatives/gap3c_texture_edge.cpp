// GAP 3c — texture() sampling at a UV derived from a probed, possibly
// off-canvas, quad-corner coordinate. This mirrors the real production
// pattern in filter/bulge, filter/pinch, filter/spiral, filter/tunnel,
// filter/warp (all `texture()`-sample using coordinates that flow through
// dFdx/dFdy-adjacent computation -- see derivatives-architecture.md
// section 6's open risk item).
//
// Kernel: `float t = texture(surface, ctx.uv).r; gx=dFdx(t); gy=dFdy(t);
// fw=fwidth(t);` on the SAME odd 7x5 canvas as gap3a, so the quad driver's
// last-row/last-column probes genuinely read `ctx.uv` values outside
// [0,1] (e.g. u = 7/7 = 1.0 exactly for the extra off-canvas probe column,
// v likewise) -- feeding an out-of-range UV directly into the REAL,
// UNMODIFIED C++ sampler (include/noisemaker/sampler.hpp,
// src/sampler.cpp, compiled here read-only) BEFORE the recorded value
// even reaches the derivative machinery.
//
// texture() dispatch below uses `sample_bilinear_bottom_left(surface,u,v)`
// called UNFLIPPED -- the convention verified bit-exact against JS's real
// `#texture` (which internally flips v) in gap3b_sampler_compare.*.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -Iinclude
//        -o gap3c_texture_edge gap3c_texture_edge.cpp
//        src/sampler.cpp
//        src/surface.cpp
//        src/numeric.cpp

#include "derivative_lib.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

#include <cstdio>
#include <fstream>
#include <vector>

namespace gap3c {
using namespace deriv;

struct KernelState {
  const noisemaker::Surface* surface;
};

void pixel(const KernelState& state, const PixelContext& context, float* out) noexcept {
  if (context.derivative != nullptr) begin_pixel(*context.derivative);

  const noisemaker::Rgba texel = noisemaker::sample_bilinear_bottom_left(
      *state.surface, static_cast<double>(context.uv.x), static_cast<double>(context.uv.y));
  const float t = texel[0];  // .r

  const float gx = dFdx(context, t);
  const float gy = dFdy(context, t);
  const float fw = fwidth(context, t);

  out[0] = gx;
  out[1] = gy;
  out[2] = fw;
  out[3] = t;
}

}  // namespace gap3c

int main() {
  using namespace gap3c;
  constexpr int WIDTH = 7;   // odd, matches gap3a's off-canvas-probe canvas
  constexpr int HEIGHT = 5;  // odd
  constexpr int LANES = 4;

  // Distinctive 7x5 texture (matches canvas dims 1:1 so out-of-range UV
  // from an off-canvas probe is unambiguous, not accidentally in-range).
  std::vector<float> data(static_cast<std::size_t>(WIDTH) * HEIGHT * 4);
  for (int y = 0; y < HEIGHT; ++y) {
    for (int x = 0; x < WIDTH; ++x) {
      const std::size_t idx = (static_cast<std::size_t>(y) * WIDTH + static_cast<std::size_t>(x)) * 4;
      const float linear = static_cast<float>(y * WIDTH + x);
      data[idx + 0] = linear / static_cast<float>(WIDTH * HEIGHT);
      data[idx + 1] = static_cast<float>(x) / static_cast<float>(WIDTH);
      data[idx + 2] = static_cast<float>(y) / static_cast<float>(HEIGHT);
      data[idx + 3] = 1.0f;
    }
  }
  noisemaker::Surface surface(WIDTH, HEIGHT, data);
  KernelState state{&surface};

  std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash> cache;
  std::vector<float> results(static_cast<std::size_t>(WIDTH) * HEIGHT * LANES);

  std::FILE* csv = std::fopen("gap3c_texture_edge_output.csv", "w");
  std::fprintf(csv, "row,col,gx,gy,fw,t\n");

  for (int row = 0; row < HEIGHT; ++row) {
    for (int col = 0; col < WIDTH; ++col) {
      float out[LANES]{};
      run_pixel_with_derivatives<KernelState>(state, &pixel, static_cast<float>(col), static_cast<float>(row),
                                                static_cast<float>(WIDTH), static_cast<float>(HEIGHT),
                                                0.f, 0.f, 0u, 0.f, cache, out, LANES);
      const std::size_t base = (static_cast<std::size_t>(row) * WIDTH + col) * LANES;
      std::fprintf(csv, "%d,%d,%.17g,%.17g,%.17g,%.17g\n", row, col,
                   static_cast<double>(out[0]), static_cast<double>(out[1]),
                   static_cast<double>(out[2]), static_cast<double>(out[3]));
      for (int i = 0; i < LANES; ++i) results[base + static_cast<std::size_t>(i)] = out[i];
    }
  }
  std::fclose(csv);
  assert(cache.empty() && "quad cache must be fully evicted after a full raster pass");

  std::ofstream bin("gap3c_texture_edge_output.f32", std::ios::binary);
  bin.write(reinterpret_cast<const char*>(results.data()), static_cast<std::streamsize>(results.size() * sizeof(float)));
  bin.close();

  std::printf("wrote gap3c_texture_edge_output.f32 and .csv (WIDTH=%d HEIGHT=%d), quad cache entries remaining=%zu\n", WIDTH, HEIGHT, cache.size());
  return 0;
}
