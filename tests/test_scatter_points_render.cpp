#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/points_render.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `pointsRenderDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:308-343) via
// docs/port-engineering/scatter-adapters/oracle/
// points_render_oracle_generator.mjs. See that generator's curated set
// (points_render-oracles.json) and 12,000-case randomized differential
// sweep (scatter-adapters report) for the full verification.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_points_render_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("render/pointsRender:deposit") != nullptr);
}

// oracle case index 0: flat view, alive agent centered -> lands in the
// destination's row-2/col-0 pixel (bottom-up -> top-down row flip).
TEST(scatter_points_render_direct_call_matches_js_oracle_flat_view) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x3f800000};
  const std::vector<std::uint32_t> rgba_bits{0x3f800000, 0x3f000000, 0x3e800000, 0x3f800000};
  std::vector<std::uint32_t> dest_bits(64, 0x00000000);
  std::vector<std::uint32_t> expected_bits(64, 0x00000000);
  expected_bits[24] = 0x3f800000;
  expected_bits[25] = 0x3f000000;
  expected_bits[26] = 0x3e800000;
  expected_bits[27] = 0x3f800000;

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(4, 4, bits_to_floats(dest_bits));
  noisemaker::scatter::points_render::Uniforms uniforms;
  uniforms.density = 100;
  uniforms.view_mode = 0;
  uniforms.view_scale = 1;

  const std::size_t pixels =
      noisemaker::scatter::points_render::run_deposit(xyz_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 1U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 1: pos.w = 0.1 < 0.5 -- dead, skip entirely.
TEST(scatter_points_render_direct_call_skips_dead_agent) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x3dcccccd};
  const std::vector<std::uint32_t> rgba_bits{0x3f800000, 0x3f800000, 0x3f800000, 0x3f800000};
  std::vector<std::uint32_t> dest_bits(64, 0x00000000);

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(4, 4, bits_to_floats(dest_bits));
  noisemaker::scatter::points_render::Uniforms uniforms;
  uniforms.density = 100;
  uniforms.view_mode = 0;
  uniforms.view_scale = 1;

  const std::size_t pixels =
      noisemaker::scatter::points_render::run_deposit(xyz_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 0U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < dest_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == dest_bits[i]);
  }
}

// oracle case index 8: 6x6 agents -> 2x2 destination, flat view but with
// non-default density/viewScale (density affects the golden-ratio cull,
// NOT the flat-view clip transform) -- forces real overlapping
// accumulation, via the registry dispatch path.
TEST(scatter_points_render_via_registry_matches_js_oracle_6x6_overlap) {
  const std::vector<std::uint32_t> xyz_bits{
      0xbf0cd8d1, 0x3f2b5c7d, 0x3f853b28, 0x358637bd, 0x3fc3ebcb, 0xbf52f129, 0xbf563eba, 0x3f689a58,
      0xbe36239b, 0x3d23c671, 0x443631c9, 0x3fdb56d6, 0x3fb9ebf0, 0xbf800000, 0x3f87ffaf, 0x3fe6f993,
      0x3fcdf794, 0x3d2cf182, 0x3f1be332, 0x3fc7e73d, 0x49742400, 0x3e64ea7f, 0xbf5be403, 0x3ff0e6ca,
      0xbf520cf9, 0xbd7821a6, 0x3f8cd747, 0xc3518046, 0xbf784e2a, 0xbf6167be, 0x3f0dae11, 0x3f77d28b,
      0x3f5bbb1e, 0x3fd17130, 0xbf000000, 0xc3c090cc, 0x3fab702a, 0x3dac8600, 0x43cfda54, 0xbf208de5,
      0xbf000000, 0x3f839f53, 0x49742400, 0x3da5fffc, 0x3eac3af3, 0x3feea081, 0x3dafd4ea, 0xbf08d600,
      0x3d839dad, 0x3e8b0c23, 0x3e6299fc, 0xbe440d16, 0x3f88b272, 0xff800000, 0x3fc72eed, 0xbef7879d,
      0x3fd82f1a, 0xbf29ae83, 0x3f82b98f, 0x3fc0edef, 0x3faec694, 0x3fedab55, 0x3fe535dd, 0x00000000,
      0xbdd562d5, 0x3fa5c37b, 0x3e2089dc, 0x3e158235, 0xbdc2bac5, 0x3ff86d61, 0x3f9a90c5, 0xbf6300fc,
      0x3eab290f, 0xbedf9313, 0x3f6db5c7, 0x3ebf5d95, 0x3d20adcf, 0x3f4b00e3, 0x4368619f, 0x3ffa471e,
      0x3f80235b, 0xbf269668, 0x00000000, 0x3e0bd880, 0x3e2e0715, 0x00000000, 0x80000000, 0xbecdccef,
      0xc3e48eba, 0xbf75577d, 0x3f88d7af, 0x3f914500, 0xbe8a8446, 0x4441c3bd, 0x3f89bd47, 0x3f000000,
      0xbf1871e2, 0xbf23f907, 0xbd852457, 0xbe396ac3, 0xbf62b655, 0x3f4f4c28, 0x3f8c76ab, 0xc468471c,
      0x3eb1f545, 0x3f6dfa2a, 0xbf3ee5bb, 0x3f8edd82, 0x3f1d0d7f, 0x3fc50b98, 0xbf800000, 0xbeaad169,
      0xbf5e8398, 0xc3ed4a58, 0x442285c9, 0x3eaaea73, 0x3f6f6ed7, 0x3bdf7233, 0x3f000000, 0x00000000,
      0x7f800000, 0xbeecd324, 0xbf1a73c8, 0xbe0c92b7, 0x3e71bdcd, 0xbf0f6b4e, 0xbe91f922, 0xbddc3c76,
      0x3f233276, 0x3e892929, 0xff800000, 0x3fd72aed, 0x3f5e79ef, 0x3e860937, 0x3eceac97, 0x80000000,
      0xc46747c5, 0x3f8a5e8b, 0x358637bd, 0xc1efd01a, 0x3fd01754, 0x3e586420, 0x3ea73e11, 0xbef29fc5,
  };
  const std::vector<std::uint32_t> rgba_bits{
      0xbf3ba3ff, 0xbeac8ae0, 0x3f0cb856, 0x3f3facf0, 0xff800000, 0x3fdeb084, 0x3e840e0f, 0x3f608888,
      0xbebed902, 0x3ed68d54, 0xbf6ae29b, 0x3fcb0f73, 0x3f815e32, 0x3fda17ff, 0x3e93e348, 0xc42449a1,
      0x3e1aa2cb, 0x4430c571, 0x3eaf7b1c, 0x3ffc7f05, 0xbf0d7f0b, 0x3fd5ef96, 0xbf018053, 0xbf1aab2d,
      0x3fb5816e, 0x44786f3d, 0xff800000, 0x3fdd1a3b, 0x3f211418, 0x3fc52248, 0xc41bcc10, 0xbf13d491,
      0x3f96b053, 0xbf5048be, 0xbe3c38c7, 0x3ff5af63, 0xbf800000, 0xbf4d74df, 0xbd862430, 0x40000000,
      0x3f2919eb, 0x3ea914c2, 0x3ff93682, 0x3f000000, 0xc3cc93d8, 0xbe0d7e28, 0xbf26ab10, 0x3f84e142,
      0x3fed087b, 0xbc6a90c4, 0x3fa513a1, 0xbf000000, 0x3f01b2e4, 0x358637bd, 0x3fa06fd2, 0x3f9057cb,
      0xbda2cf52, 0xbe6598ae, 0x3fb24c34, 0xbf11c356, 0xbf116eda, 0xc338ac22, 0x7f800000, 0xbf3695c7,
      0xbf800000, 0xbec239f5, 0x446b7ada, 0x3e015439, 0xbe7aa361, 0x3fd87785, 0x3f811119, 0xbea5c5e1,
      0x3f96b8d2, 0xbd5d7069, 0xbf32f178, 0x358637bd, 0x3f965344, 0x3e611445, 0xbf603ea7, 0x00000000,
      0xbf062f0f, 0x3ff27e8d, 0x3f8431fa, 0x3fcb427a, 0x3fb563e6, 0x3ffa2c65, 0x3f17b28d, 0xbbf6e891,
      0x3f0d8478, 0x3feb93e4, 0xbf7850fb, 0x3fce8b3e, 0x3e5c0faf, 0xbd83156b, 0x3f1d9ba3, 0xbf302cfd,
      0xbf566792, 0x3ebe677f, 0x3f4c978b, 0x3f2163ed, 0x3ce18d8c, 0x3ec41170, 0x3f8fb83e, 0xc9742400,
      0x3ea80268, 0xbecb8b08, 0x3e362066, 0xbe949d50, 0x3f2a303e, 0x3fe508b6, 0x3fa841ef, 0xbf000000,
      0x444b6c93, 0x3f7a76a2, 0xc3f8771a, 0x3f3e0923, 0x44714b76, 0x3f55b838, 0x3d649778, 0x3f660aa2,
      0x3b8100f1, 0x3ff203f9, 0xbea9f2ea, 0x80000000, 0x3f7889ca, 0x3f800000, 0xbec6e8dc, 0x4419995d,
      0xbf174a77, 0x3fb0d461, 0x3fb51b20, 0x3f5f7eaf, 0xbead9fba, 0x3f8cb1d4, 0xbebc4312, 0x3cf863b3,
      0xc2d624dd, 0xbd18bbd3, 0x3d15cad3, 0x00000000, 0xbec725fa, 0xbf800000, 0x7f800000, 0xbf800000,
  };
  const std::vector<std::uint32_t> dest_bits{
      0x3f227802, 0xc373934f, 0x3fe1ab01, 0x3fb83e82, 0x3fe15103, 0x3fec40cf, 0x3fa173e1, 0x3f6aacd3,
      0xc0000000, 0xbeff8c56, 0x429b0313, 0x3fc58fd8, 0xbe9c6bd7, 0x3f3ae69f, 0xbf800000, 0xbeface32,
  };
  const std::vector<std::uint32_t> expected_bits{
      0x3fe78f45, 0xc3735b0a, 0x3f63175b, 0x3fb83e82, 0x3fe15103, 0x3fec40cf, 0x3fa173e1, 0x3f6aacd3,
      0xc0000000, 0xbeff8c56, 0x429b0313, 0x3fc58fd8, 0xbf658062, 0x400723d8, 0x3ed46c80, 0x3ec42f2c,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("render/pointsRender:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface xyz_tex(6, 6, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(6, 6, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(2, 2, bits_to_floats(dest_bits));

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("xyzTex", xyz_tex);
  bindings.set_texture("rgbaTex", rgba_tex);
  bindings.set_uniform("density", 94.05653338879347);
  bindings.set_uniform("viewMode", 0.0);
  bindings.set_uniform("rotateX", -0.6213113386183977);
  bindings.set_uniform("rotateY", -8.79800230730325);
  bindings.set_uniform("rotateZ", 4.843989317305386);
  bindings.set_uniform("posX", 25.746853766031563);
  bindings.set_uniform("posY", 40.36204724106938);
  bindings.set_uniform("viewScale", -4.993762378580868);
  bindings.set_uniform("fieldOfView", -36.26306701917201);

  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 2U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
