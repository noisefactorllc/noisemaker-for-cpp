// GAP 3a — odd-canvas-dimension edge behavior.
//
// glsl-runtime.js's `probe()` (lines 479-491) evaluates the four quad
// corners at exactly the member pixels' own fragCoords with NO bounds
// check (line 502 area) -- at the right/bottom image edge, x0+1/y0+1 can
// legitimately land one pixel past the canvas. A WIDTH=HEIGHT=8 (even x
// even) canvas never actually stresses this: quadX max = 3 -> x0=6,
// x0+1=7, both in [0,8). A 7x5 canvas (odd x odd) DOES: the last quad's
// x0+1/y0+1 land at column 7 (canvas width is 7, valid columns 0..6) and
// row 5 (canvas height is 5, valid rows 0..4) -- genuinely off-canvas.
//
// This file reuses the same derivative-kernel shape as the original
// prototype.cpp (scalar dFdx/dFdy on a quadratic `t`, vector fwidth on
// uv) purely as a vehicle to exercise the quad driver's off-canvas-probe
// path on an odd canvas and verify C++/JS still agree bit-exactly there.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -o gap3a_odd_canvas gap3a_odd_canvas.cpp

#include "derivative_lib.hpp"

#include <cstdio>
#include <fstream>
#include <vector>

namespace gap3a {
using namespace deriv;

struct KernelState {};

void pixel(const KernelState&, const PixelContext& context, float* out) noexcept {
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
  Vec2 uvVec{uvx, uvy};
  const Vec2 fwv = fwidth(context, uvVec);

  out[0] = gx;
  out[1] = gy;
  out[2] = fwv.x;
  out[3] = fwv.y;
}

}  // namespace gap3a

int main() {
  using namespace gap3a;
  constexpr int WIDTH = 7;   // odd
  constexpr int HEIGHT = 5;  // odd
  constexpr int LANES = 4;

  KernelState state;
  std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash> cache;
  std::vector<float> results(static_cast<std::size_t>(WIDTH) * HEIGHT * LANES);

  std::FILE* csv = std::fopen("gap3a_odd_canvas_output.csv", "w");
  std::fprintf(csv, "row,col,gx,gy,fwx,fwy\n");

  for (int row = 0; row < HEIGHT; ++row) {
    for (int col = 0; col < WIDTH; ++col) {
      float out[LANES]{};
      run_pixel_with_derivatives<KernelState>(state, &pixel, static_cast<float>(col), static_cast<float>(row),
                                                static_cast<float>(WIDTH), static_cast<float>(HEIGHT),
                                                0.f, 0.f, 0u, 0.f, cache, out, LANES);
      const std::size_t base = (static_cast<std::size_t>(row) * WIDTH + col) * LANES;
      std::fprintf(csv, "%d,%d,%.9g,%.9g,%.9g,%.9g\n", row, col,
                   static_cast<double>(out[0]), static_cast<double>(out[1]),
                   static_cast<double>(out[2]), static_cast<double>(out[3]));
      for (int i = 0; i < LANES; ++i) results[base + static_cast<std::size_t>(i)] = out[i];
    }
  }
  std::fclose(csv);
  assert(cache.empty() && "quad cache must be fully evicted after a full raster pass");

  std::ofstream bin("gap3a_odd_canvas_output.f32", std::ios::binary);
  bin.write(reinterpret_cast<const char*>(results.data()), static_cast<std::streamsize>(results.size() * sizeof(float)));
  bin.close();

  std::printf("wrote gap3a_odd_canvas_output.f32 and .csv (WIDTH=%d HEIGHT=%d), quad cache entries remaining=%zu\n", WIDTH, HEIGHT, cache.size());
  return 0;
}
