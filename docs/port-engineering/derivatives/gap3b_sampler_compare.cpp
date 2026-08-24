// GAP 3b — direct sampler-vs-sampler comparison at out-of-range UV.
//
// This program links the REAL, UNMODIFIED noisemaker-for-cpp sampler
// implementation (include/noisemaker/sampler.hpp, src/sampler.cpp,
// src/surface.cpp -- compiled here read-only, nothing under
// . is edited) and feeds it the
// same synthetic 4x4 texture and the same (u,v) coordinate list --
// spanning in-range, exact-boundary, and clearly out-of-range values -- as
// gap3b_sampler_compare_probe.mjs feeds the REAL, UNMODIFIED
// noisemaker-for-cpu sampler (src/runtime/sampler.js, src/runtime/
// surface.js).
//
// Three comparisons are made (see gap-closure-report.md for the numeric
// results):
//   1. NEAREST: C++ sample_nearest_bottom_left(surface,u,v) vs JS
//      sampleNearestBottomLeft(surface,u,v) -- both are called UNFLIPPED
//      in their respective real production texture() dispatchers
//      (glsl-runtime.js line 199; typed_slice.cpp's `sample_nearest_
//      bottom_left(surface, uv[0], uv[1])` call sites), so this is a
//      like-for-like production-convention comparison.
//   2. BILINEAR, naive same-argument comparison: C++
//      sample_bilinear_bottom_left(surface,u,v) vs raw JS
//      sampleBilinear(surface,u,v) with NO flip. sample_bilinear_bottom_
//      left has ZERO call sites anywhere in noisemaker-for-cpp today
//      (verified: `grep -rn sample_bilinear_bottom_left` under
//      include/ and src/ finds only its own declaration/definition), so
//      there is no established C++ calling convention to defer to; this
//      comparison checks whether the two "bottom_left"/raw functions
//      agree when called with literally the same arguments.
//   3. BILINEAR, production-convention comparison: C++
//      sample_bilinear_bottom_left(surface,u,v) [unflipped -- the natural
//      extension of the ALREADY-established sample_nearest_bottom_left
//      unflipped convention] vs JS's ACTUAL `#texture` dispatch for
//      filter==='linear' (glsl-runtime.js line 198):
//      `sampleBilinear(surface, coord[0], 1 - coord[1])` -- i.e. JS DOES
//      flip v before calling the raw sampler.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -Iinclude
//        -o gap3b_sampler_compare gap3b_sampler_compare.cpp
//        src/sampler.cpp
//        src/surface.cpp

#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

#include <cstdio>
#include <fstream>
#include <vector>

int main() {
  using namespace noisemaker;

  // 4x4 surface, distinctive per-texel RGBA so any wrap/clamp/flip bug is
  // visible rather than masked by a uniform texture.
  constexpr std::size_t W = 4, H = 4;
  std::vector<float> data(W * H * 4);
  for (std::size_t y = 0; y < H; ++y) {
    for (std::size_t x = 0; x < W; ++x) {
      const std::size_t idx = (y * W + x) * 4;
      const float linear = static_cast<float>(y * W + x);
      data[idx + 0] = linear / 16.0f;                              // R: linear index / 16
      data[idx + 1] = static_cast<float>(x) / 4.0f;                // G: storage column / 4
      data[idx + 2] = static_cast<float>(y) / 4.0f;                // B: storage row / 4
      data[idx + 3] = 1.0f;                                        // A: 1
    }
  }
  Surface surface(W, H, data);

  struct Coord { double u, v; const char* label; };
  const std::vector<Coord> coords = {
      {0.125, 0.125, "interior"},
      {0.5, 0.5, "center"},
      {0.9, 0.1, "interior-2"},
      {0.0, 0.0, "boundary-00"},
      {1.0, 1.0, "boundary-11"},
      {0.0, 1.0, "boundary-01"},
      {1.0, 0.0, "boundary-10"},
      {-0.3, 0.2, "neg-u"},
      {1.7, 0.5, "over-u"},
      {-0.01, -0.01, "neg-both-small"},
      {1.5, 1.5, "over-both"},
      {-2.3, 3.7, "far-out"},
      {0.5, -5.0, "far-neg-v"},
      {5.0, 0.5, "far-over-u"},
  };

  std::FILE* csv = std::fopen("gap3b_sampler_compare_output.csv", "w");
  std::fprintf(csv, "label,u,v,nearest_bl_r,nearest_bl_g,nearest_bl_b,nearest_bl_a,"
                     "bilinear_bl_unflipped_r,bilinear_bl_unflipped_g,bilinear_bl_unflipped_b,bilinear_bl_unflipped_a\n");
  std::vector<float> raw;  // [nearest(4), bilinear_unflipped(4)] per coord, for bit-exact comparison
  raw.reserve(coords.size() * 8);
  for (const Coord& c : coords) {
    const Rgba nearest = sample_nearest_bottom_left(surface, c.u, c.v);
    const Rgba bilinear = sample_bilinear_bottom_left(surface, c.u, c.v);  // unflipped, natural convention
    std::fprintf(csv, "%s,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",
                 c.label, c.u, c.v,
                 static_cast<double>(nearest[0]), static_cast<double>(nearest[1]),
                 static_cast<double>(nearest[2]), static_cast<double>(nearest[3]),
                 static_cast<double>(bilinear[0]), static_cast<double>(bilinear[1]),
                 static_cast<double>(bilinear[2]), static_cast<double>(bilinear[3]));
    for (float v : nearest) raw.push_back(v);
    for (float v : bilinear) raw.push_back(v);
  }
  std::fclose(csv);

  std::ofstream bin("gap3b_sampler_compare_output.f32", std::ios::binary);
  bin.write(reinterpret_cast<const char*>(raw.data()), static_cast<std::streamsize>(raw.size() * sizeof(float)));
  bin.close();

  std::printf("wrote gap3b_sampler_compare_output.csv and .f32 (%zu coords)\n", coords.size());
  return 0;
}
