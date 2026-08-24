// GAP 1 — vec3 and vec4 dFdx/dFdy/fwidth overloads.
//
// Exercises the three programs in the real 17-program set that call
// fwidth() on a vec3 (filter/celShading/celShadingColor,
// filter/posterize/posterize, filter/step/step — see
// derivatives-architecture.md section 3.1) plus vec4 for completeness
// (the widest GLSL vector type dFdx/dFdy/fwidth can be applied to).
//
// Also builds a case DELIBERATELY sensitive to the scalar-vs-vector
// narrowing asymmetry documented in derivative_lib.hpp's header comment:
// a scalar `t` and vec3/vec4 component `v3.x`/`v4.x` compute the IDENTICAL
// underlying quantity (same TABLE_X[col] + TABLE_Y[row] formula), but
// because the scalar derivative path keeps dFdx/dFdy in double precision
// until the single final F32() narrowing (glsl-runtime.js lines 518-521,
// 461) while the vector path narrows every component immediately (lines
// 524-530), fwidth(t) and fwidth(v3).x are EXPECTED to disagree by
// exactly 1 ULP at pixel (row=7, col=0) for the TABLE_X/TABLE_Y constants
// chosen below. Getting the C++ narrowing backwards (e.g. rounding the
// scalar path early, matching the vector path) would collapse this
// intentional 1-ULP disagreement and silently pass a smooth-polynomial
// test while failing the real programs.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -o gap1_vec34 gap1_vec34.cpp

#include "derivative_lib.hpp"

#include <cstdio>
#include <fstream>
#include <vector>

namespace gap1 {
using namespace deriv;

struct KernelState {};

// Corner values for the (col in {0,1}, row in {0,1}) target quad were found
// by brute-force search over the *actual* geometric constraint (bottomLeft
// is shared as the base of BOTH the dFdx-direction and dFdy-direction
// subtraction, since dFdx = bottomRight-bottomLeft and dFdy =
// topLeft-bottomLeft for the bottom-left member pixel of a quad) such that
// the EXACT (double-precision) differences xExact = bottomRight-bottomLeft
// and yExact = topLeft-bottomLeft are not themselves exactly representable
// in float32 (i.e. genuinely need >24 bits of mantissa), so that
//   F32(|xExact| + |yExact|)                       (scalar path)
// differs from
//   F32(|F32(xExact)| + |F32(yExact)|)              (vector path)
// by exactly one ULP. Columns/rows >= 2 use arbitrary smooth values; only
// columns {0,1} and rows {0,1} (i.e. the quad at quadX=0, quadY=0) matter
// for the sensitivity case.
constexpr float CORNER_BOTTOM_LEFT = 0.0000071775784817873500288f;
constexpr float CORNER_BOTTOM_RIGHT = 3.7392933194269062369e-8f;
constexpr float CORNER_TOP_LEFT = 0.0025053308345377445221f;
constexpr float CORNER_TOP_RIGHT = 0.5f;  // not part of the sensitivity case; any value

constexpr float TABLE_X[8] = {0.f, 0.f, 0.25f, 0.5f, 0.75f, 1.0f, 1.25f, 1.5f};
constexpr float TABLE_Y[8] = {0.f, 0.f, 0.1f, 0.2f, 0.3f, 0.4f, 0.5f, 0.6f};

void pixel(const KernelState&, const PixelContext& context, float* out) noexcept {
  if (context.derivative != nullptr) begin_pixel(*context.derivative);

  const int col = static_cast<int>(context.frag_coord.x - 0.5f);
  const int row = static_cast<int>(context.frag_coord.y - 0.5f);

  const float uvx = context.uv.x;
  const float uvy = context.uv.y;

  // Scalar quantity: identical formula to v3.x/v4.x below, used to expose
  // the narrowing asymmetry between the scalar and vector derivative paths.
  // The (col,row) in {0,1}x{0,1} quad uses four DIRECTLY-tabulated corner
  // constants (no intervening addition, so no extra rounding contaminates
  // the carefully-chosen bit patterns); every other quad uses an ordinary
  // separable sum (magnitude and rounding behavior irrelevant there).
  float t;
  if (col == 0 && row == 0) {
    t = CORNER_BOTTOM_LEFT;
  } else if (col == 1 && row == 0) {
    t = CORNER_BOTTOM_RIGHT;
  } else if (col == 0 && row == 1) {
    t = CORNER_TOP_LEFT;
  } else if (col == 1 && row == 1) {
    t = CORNER_TOP_RIGHT;
  } else {
    t = TABLE_X[static_cast<std::size_t>(col)] + TABLE_Y[static_cast<std::size_t>(row)];
  }

  Vec3 v3{};
  v3.x = t;                                      // same formula/value as `t`
  v3.y = (3.0f * uvx * uvx) - (2.0f * uvy);      // ordinary smooth, vec3 coverage
  v3.z = uvx + (4.0f * uvy * uvy);               // ordinary smooth, vec3 coverage

  Vec4 v4{};
  v4.x = t;                                      // reuse sensitive scalar
  v4.y = v3.y;
  v4.z = v3.z;
  v4.w = uvx * uvy * 2.0f;                       // ordinary smooth, vec4 coverage

  const float gx_t = dFdx(context, t);
  const float gy_t = dFdy(context, t);
  const float fw_t = fwidth(context, t);

  const Vec3 gx_v3 = dFdx(context, v3);
  const Vec3 gy_v3 = dFdy(context, v3);
  const Vec3 fw_v3 = fwidth(context, v3);

  const Vec4 gx_v4 = dFdx(context, v4);
  const Vec4 gy_v4 = dFdy(context, v4);
  const Vec4 fw_v4 = fwidth(context, v4);

  out[0] = gx_t; out[1] = gy_t; out[2] = fw_t;
  out[3] = gx_v3.x; out[4] = gx_v3.y; out[5] = gx_v3.z;
  out[6] = gy_v3.x; out[7] = gy_v3.y; out[8] = gy_v3.z;
  out[9] = fw_v3.x; out[10] = fw_v3.y; out[11] = fw_v3.z;
  out[12] = gx_v4.x; out[13] = gx_v4.y; out[14] = gx_v4.z; out[15] = gx_v4.w;
  out[16] = gy_v4.x; out[17] = gy_v4.y; out[18] = gy_v4.z; out[19] = gy_v4.w;
  out[20] = fw_v4.x; out[21] = fw_v4.y; out[22] = fw_v4.z; out[23] = fw_v4.w;
}

}  // namespace gap1

int main() {
  using namespace gap1;
  constexpr int WIDTH = 8;
  constexpr int HEIGHT = 8;
  constexpr int LANES = 24;

  KernelState state;
  std::unordered_map<QuadKey, QuadCacheEntry, QuadKeyHash> cache;

  std::vector<float> results(static_cast<std::size_t>(WIDTH) * HEIGHT * LANES);
  std::FILE* csv = std::fopen("gap1_vec34_output.csv", "w");
  std::fprintf(csv, "row,col");
  const char* names[LANES] = {
      "gx_t", "gy_t", "fw_t",
      "gx_v3.x", "gx_v3.y", "gx_v3.z", "gy_v3.x", "gy_v3.y", "gy_v3.z", "fw_v3.x", "fw_v3.y", "fw_v3.z",
      "gx_v4.x", "gx_v4.y", "gx_v4.z", "gx_v4.w", "gy_v4.x", "gy_v4.y", "gy_v4.z", "gy_v4.w",
      "fw_v4.x", "fw_v4.y", "fw_v4.z", "fw_v4.w",
  };
  for (const char* name : names) std::fprintf(csv, ",%s", name);
  std::fprintf(csv, "\n");

  for (int row = 0; row < HEIGHT; ++row) {
    for (int col = 0; col < WIDTH; ++col) {
      float out[LANES];
      run_pixel_with_derivatives<KernelState>(state, &pixel, static_cast<float>(col), static_cast<float>(row),
                                                static_cast<float>(WIDTH), static_cast<float>(HEIGHT),
                                                0.f, 0.f, 0u, 0.f, cache, out, LANES);
      const std::size_t base = (static_cast<std::size_t>(row) * WIDTH + col) * LANES;
      std::fprintf(csv, "%d,%d", row, col);
      for (int i = 0; i < LANES; ++i) {
        results[base + static_cast<std::size_t>(i)] = out[i];
        std::fprintf(csv, ",%.9g", static_cast<double>(out[i]));
      }
      std::fprintf(csv, "\n");
    }
  }
  std::fclose(csv);

  assert(cache.empty() && "quad cache must be fully evicted after a full raster pass");

  std::ofstream bin("gap1_vec34_output.f32", std::ios::binary);
  bin.write(reinterpret_cast<const char*>(results.data()), static_cast<std::streamsize>(results.size() * sizeof(float)));
  bin.close();

  // Directly print the target sensitivity-case pixel (row=7, col=0): fw_t
  // (index 2) is expected to differ from fw_v3.x (index 9) by exactly 1 ULP.
  const std::size_t targetBase = (7u * WIDTH + 0u) * LANES;
  std::printf("target pixel (row=7,col=0): fw_t=%.9g fw_v3.x=%.9g (expect these to DIFFER by 1 ULP)\n",
              static_cast<double>(results[targetBase + 2]), static_cast<double>(results[targetBase + 9]));

  std::printf("wrote gap1_vec34_output.f32 and gap1_vec34_output.csv, quad cache entries remaining=%zu\n", cache.size());
  return 0;
}
