#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/flow3d.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `flow3dDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/flow3d-deposit.js) via
// docs/port-engineering/scatter-adapters/oracle/flow3d_oracle_generator.mjs.
// See that generator's curated set (flow3d-oracles.json) and 12,000-case
// randomized differential sweep (scatter-adapters report) for the full
// verification.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_flow3d_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("filter3d/flow3d:deposit") != nullptr);
}

// oracle case index 0: pass.count absent (falls back to capacity, JS
// `pass?.count ?? capacity`); every agent's atlas coordinate misses the
// destination -- zero deposits, destination byte-unchanged.
TEST(scatter_flow3d_direct_call_matches_js_oracle_no_deposits) {
  const std::vector<std::uint32_t> state1_bits{
      0xbf29fd95, 0xbe739fb0, 0x3eb4597b, 0x3ccb2df0, 0x3facbb58, 0x3e826519, 0x40000000, 0x00000000,
      0xbe85591b, 0xbf1d4c13, 0x3f800233, 0x3fb69303, 0x3e9b5076, 0x3feaf950, 0xc3bc110f, 0x3ff653ef,
  };
  const std::vector<std::uint32_t> state2_bits{
      0x3e83cd2b, 0x49742400, 0x443e69d0, 0x3ff0470d, 0xbf211f4d, 0x3f7740e0, 0xbf5801ca, 0xbf612673,
      0x3ff28ad9, 0x3fda0844, 0x3f471935, 0xbf347cf0, 0x3f3f7512, 0x3efa038c, 0xbf55cc68, 0x3f529238,
  };
  std::vector<std::uint32_t> dest_bits{
      0x43bed8b8, 0x3e92e87e, 0x7f800000, 0x3e477067, 0xbf3bde36, 0xc40778fc, 0x3faa58bb, 0x3f2fb03c,
      0xbf17959e, 0xbf6d285e, 0x3fa0221b, 0xbec9b60d, 0xc41f2572, 0x3f893f33, 0x3f1b7a30, 0xbed41167,
      0xbf59e083, 0x358637bd, 0x80000000, 0x3e26cbf5, 0x3f6a46f4, 0x3fd16c29, 0x7f800000, 0xbf119df0,
      0x3f9560fd, 0xc2e9a0d2, 0x3e5ad0a2, 0xbe8ea1a0, 0xbeb6b93d, 0x3f9e66d8, 0xbf0a8b30, 0x3f2972a3,
      0x3f6d3832, 0x40000000, 0x49742400, 0xbef378f1, 0xbea96bf7, 0x3fcb6eb8, 0xbdee24bd, 0x3fa3abed,
      0xbebdec0b, 0x3f403086, 0x3f2b0b17, 0x3fb940d5, 0x3fe75651, 0x3fe8272f, 0x3f99bdde, 0x3f2044bd,
      0x3f2a8485, 0xc0000000, 0x40000000, 0x3f9d84e1, 0xbf7386ff, 0x3ecfaf8c, 0xbf0b5a70, 0x3f32ba81,
      0x3f0d8bfc, 0x3fcae806, 0xbf09a882, 0x3fc3ba48, 0xc39d5af9, 0x3deb6ca0, 0x3fe8402f, 0xbf34af0b,
  };

  noisemaker::Surface state_tex1(2, 2, bits_to_floats(state1_bits));
  noisemaker::Surface state_tex2(2, 2, bits_to_floats(state2_bits));
  noisemaker::Surface destination(4, 4, bits_to_floats(dest_bits));
  noisemaker::scatter::flow3d::Uniforms uniforms;
  uniforms.density = 10.0;
  uniforms.volume_size = 2.0;

  const std::size_t pixels =
      noisemaker::scatter::flow3d::run_deposit(state_tex1, state_tex2, uniforms, std::nullopt, destination);
  REQUIRE(pixels == 0U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < dest_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == dest_bits[i]);
  }
}

// oracle case index 7: 1x9 agents -> 1x2 destination, FRACTIONAL
// `pass.count` (10.720472631743178) -- exercises the loop bound staying a
// plain double comparison (`agentIndex < count`), not an integer count.
TEST(scatter_flow3d_direct_call_matches_js_oracle_fractional_pass_count) {
  const std::vector<std::uint32_t> state1_bits{
      0x3fab5a1c, 0x3f6b95a1, 0x43a32c59, 0x3fd5727c, 0xbdbfa49e, 0x3c834e67, 0x3fca80e7, 0xbecebdd5,
      0x358637bd, 0xbebea0d4, 0xc9742400, 0x3fe804a7, 0x358637bd, 0x3f886fa4, 0x3f91a878, 0x3f4cc96e,
      0x3f800000, 0xbd50fdcc, 0xbcbc7a59, 0x3f0a8032, 0x3f2043df, 0xbd9f0947, 0x3fe5068e, 0x3f25fd71,
      0x3e32bce0, 0xbeb0cb13, 0x3ff5a26c, 0x3f8380b4, 0xbf72d9ea, 0x3f000000, 0x3eec3fdf, 0xbf39193f,
      0x443e18db, 0xbf55992c, 0xbdde2325, 0x3fc5ecba,
  };
  const std::vector<std::uint32_t> state2_bits{
      0x3e685f06, 0x3e8f9192, 0xc2c865e8, 0x44422130, 0x3f245393, 0xbefece35, 0x3fba2f60, 0x3f72317f,
      0x3fef7dfc, 0x7f800000, 0xc43dc480, 0x3ff7f416, 0x3da94496, 0x3f4f230a, 0x3ff85b1c, 0xbf4565d6,
      0x3f0e1a25, 0x3ffed4f2, 0x3f9d37de, 0xbf7feb1c, 0x3fdc09e2, 0xbddb36de, 0x3fd4c909, 0xbd109560,
      0xbf430825, 0x3fa23a60, 0x3ff44bed, 0x3f2e77b3, 0xbea26405, 0x3f866fcc, 0x3fcc9c84, 0x3fdbf0cb,
      0xbec874a4, 0x4476ee19, 0xc0000000, 0xc3e03316,
  };
  const std::vector<std::uint32_t> dest_bits{0x3f6846e6, 0xbefe6cde, 0x3e0c84d9, 0xbf62a2e6,
                                              0xbf76e3fb, 0x3f4bbf34, 0x3f793169, 0x7fc00000};
  const std::vector<std::uint32_t> expected_bits{0x3f6846e6, 0xbefe6cde, 0x3e0c84d9, 0xbf62a2e6,
                                                  0x3d9a81b6, 0x4030fc08, 0x40cf8232, 0x7fc00000};

  noisemaker::Surface state_tex1(1, 9, bits_to_floats(state1_bits));
  noisemaker::Surface state_tex2(1, 9, bits_to_floats(state2_bits));
  noisemaker::Surface destination(1, 2, bits_to_floats(dest_bits));
  noisemaker::scatter::flow3d::Uniforms uniforms;
  uniforms.density = 18.977855523116887;
  uniforms.volume_size = 6.156960260821506;

  const std::size_t pixels = noisemaker::scatter::flow3d::run_deposit(state_tex1, state_tex2, uniforms,
                                                                       10.720472631743178, destination);
  REQUIRE(pixels == 3U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 9: 6x6 agents -> 2x2 destination, pass.count absent
// (falls back to capacity=36) -- forces real overlapping accumulation
// across all 9 destination-pixel writes, via the registry dispatch path.
TEST(scatter_flow3d_via_registry_matches_js_oracle_6x6_overlap) {
  const std::vector<std::uint32_t> state1_bits{
      0xc0000000, 0x3eb817a9, 0x3f87a286, 0xbf68db19, 0xc9742400, 0x3f486c97, 0x3fc7222d, 0xbebf8504,
      0xbeaa93ad, 0xbf386960, 0x3eb76590, 0xbe1cfe1e, 0x3fbdfb3a, 0x3fa81cbb, 0x3c6d2642, 0x3f1ba346,
      0x40000000, 0x3edb4ff7, 0xc3960713, 0xbe13e10a, 0xbf1130db, 0xbed5b595, 0xc4698623, 0xbf2c8a9d,
      0x3fd229cc, 0x3bf958fa, 0xbceed122, 0x40000000, 0x3e9a4721, 0x3fbf0bd6, 0x3db2747c, 0x3fde6842,
      0x3f87d4c8, 0xbf000000, 0x3df13e78, 0xbe827aa9, 0x3fec8420, 0x3ffc4131, 0x40000000, 0xbdeb8585,
      0x43efa07b, 0x3f4f978a, 0x3ff7d201, 0x3f7914c2, 0x80000000, 0xc4121dde, 0x3ff97382, 0x3ff9dc3f,
      0x3e299403, 0xbe35f351, 0x3ec5eb5a, 0x3ff46e6d, 0xc3010174, 0x3f800000, 0x3f000000, 0x3eeabf90,
      0xbdc67d2c, 0xbdfcddd0, 0x3f7dcea0, 0xbf56afed, 0xc3882750, 0x3d21d55c, 0x3ef7bf5d, 0x3f3b34df,
      0x3f000000, 0x44506553, 0x3f0be4a2, 0x7f800000, 0xbf4f7707, 0xc444b6f1, 0x3fb72034, 0x40000000,
      0x3fbd4085, 0xbecff9fb, 0x3fab09d3, 0x40000000, 0x3f22d882, 0xbf2da985, 0xbf27df80, 0xbf181e3a,
      0x446145c0, 0xbf54e3e3, 0x3f951619, 0x3f387246, 0xbed814c9, 0x3ebace40, 0xbe6bf13e, 0xbf24eef7,
      0x3f96718a, 0x3fae81b9, 0xbf084d73, 0xbec09bcf, 0x3f890bf2, 0xbecbec15, 0x40000000, 0xc3eb3525,
      0x3f7ac05b, 0xbea2d50c, 0x3f5ae498, 0x3fe57231, 0x3fd9d2cc, 0xbf02f0f6, 0xbec4b383, 0x3f3eadff,
      0x3eba4042, 0x3fbde7d6, 0x3fb0ad12, 0x3f05886d, 0xbf457d1b, 0x3e150e20, 0x3fc3f87e, 0x3f9fbfa7,
      0x3ebdfcae, 0x3f552569, 0x3eb7ae93, 0xc385ad79, 0x3fc28d8b, 0x3f705760, 0x3fed5e8a, 0xc0000000,
      0x3e4d5bcc, 0xbd51fbe1, 0x3fec63ba, 0xc0000000, 0x3e7b2d42, 0xbf64fe07, 0xbee8b1d2, 0x3e30c656,
      0x3f736996, 0x3e9874e8, 0x44673458, 0xbf44157d, 0xbf27c084, 0x3f3f05ca, 0x3fc35090, 0x3ffd597e,
      0x3f2011a2, 0xbf3f6809, 0xbf5d3aea, 0x3f7397ac, 0xbf29aea3, 0xbf6348bc, 0x3f2bb639, 0xbf000000,
  };
  const std::vector<std::uint32_t> state2_bits{
      0xbf5c552e, 0x445f7ade, 0x3e58aa5a, 0x3ec5d2c9, 0xbedbd8d7, 0xc4660b8b, 0x3fa95f28, 0xbeb89aed,
      0x3f65385e, 0x00000000, 0xbf6cdb75, 0x3ffddd63, 0x3f1ae93e, 0x3f2780ca, 0xbaf3c734, 0x3e0f52ad,
      0x3f5179c9, 0x3fc1fb77, 0xbf4acad5, 0xbf120d94, 0x3f840ad8, 0x4416c2aa, 0xc373f00d, 0x3ef93286,
      0x3fa7987c, 0x3ffcb782, 0x3d857a88, 0x00000000, 0x3e9775af, 0x3fb9d9c4, 0x3f9378eb, 0x425f0274,
      0xc37b4b33, 0xc3b54786, 0x3f9bbec4, 0x3f7e6b38, 0x3f7927e4, 0x3f7ccee0, 0xbf470f51, 0x3f7b73e8,
      0x3f6a896c, 0xbf34209b, 0xbf3a047d, 0x446508dd, 0x3fb7ae8e, 0x3e4a567c, 0xc9742400, 0x3f45b310,
      0x3f8f7024, 0xbf32e0b7, 0x3f8b8a1d, 0x3e820361, 0xbf7ee383, 0xbeab4b3e, 0xbe0db0b6, 0x80000000,
      0x43c24249, 0x3fc0b314, 0x3f600fc3, 0x3fa89204, 0xbecae91b, 0xbd6eeb0c, 0x3ee46c64, 0xbdbe162b,
      0xbf444dcf, 0x3ff349b6, 0xc3f9cf6a, 0x3f4069f8, 0xbf4aac1a, 0x3f4cfa7b, 0xbf58dea3, 0x3f860272,
      0x3f74ee9f, 0x3e5f72a4, 0xbf1793cd, 0x3f3d6dc8, 0x3f924668, 0xbed4b7c0, 0x3f273f19, 0x40000000,
      0x42a3b1ae, 0x3f223bb2, 0x3f3b6414, 0x3f6485a5, 0x7f800000, 0x3e6c281c, 0x3f88e616, 0xbf0f0cfb,
      0xbe832adb, 0x3d98b343, 0x3fa86704, 0xbe6147f8, 0xbf000000, 0x3d2bc376, 0x7fc00000, 0x3d1a6f7a,
      0xbedf34ed, 0x3f800000, 0x3ed3c915, 0x3fb58a7a, 0x3f982aab, 0x3f1fb770, 0xbf09c0d7, 0xbef2fa7f,
      0xbddc1037, 0x3f8c5387, 0x3fad435a, 0x3ec9be4a, 0x3f25d5e8, 0x3f8aa678, 0x3f996e36, 0xbe01a400,
      0x3fc24813, 0xbd8eee5f, 0xbf2a07d2, 0xbf22ad81, 0x3f9f8f15, 0x40000000, 0xbf4f4ec1, 0x3e0e445b,
      0xbd8bbce3, 0x3f0a2dd2, 0xbebf145d, 0x3f000000, 0x3ee5305d, 0x3fb93911, 0x3f943696, 0xbf113947,
      0x3fe34da1, 0x3fd6bc64, 0x3fdc306c, 0xff800000, 0x3fce61d6, 0x3dbe0be5, 0x3fd38ac9, 0x3fdbb50a,
      0xbf75b2e2, 0xbf1dbed0, 0x3fa75dee, 0xbf2232f9, 0x43984aa5, 0xbe10052e, 0xc46421b5, 0x3feec71f,
  };
  const std::vector<std::uint32_t> dest_bits{
      0x3e3b30e6, 0x441a81b1, 0xbf5b1b5b, 0x3eeba601, 0x3f9e6da7, 0x3f8626fd, 0x3f82fde1, 0xbdbdb50c,
      0xc20219e8, 0x3f84dc40, 0xbbb31bfe, 0x3e48c1b7, 0x3fba0352, 0x3f639743, 0x3fdf07e0, 0xbe83f81b,
  };
  const std::vector<std::uint32_t> expected_bits{
      0x3e3b30e6, 0x441a81b1, 0xbf5b1b5b, 0x3eeba601, 0x3f9e6da7, 0x3f8626fd, 0x3f82fde1, 0xbdbdb50c,
      0xc1dcd855, 0x40fea974, 0x7fc00000, 0x41132307, 0x3fba0352, 0x3f639743, 0x3fdf07e0, 0xbe83f81b,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("filter3d/flow3d:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface state_tex1(6, 6, bits_to_floats(state1_bits));
  noisemaker::Surface state_tex2(6, 6, bits_to_floats(state2_bits));
  noisemaker::Surface destination(2, 2, bits_to_floats(dest_bits));

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("stateTex1", state_tex1);
  bindings.set_texture("stateTex2", state_tex2);
  bindings.set_uniform("density", 200.0);
  bindings.set_uniform("volumeSize", 6.0);

  const noisemaker::scatter::ScatterPass pass;  // pass.count absent
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 9U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
