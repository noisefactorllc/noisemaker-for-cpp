#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/physarum.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `physarumDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:264-296) via
// docs/port-engineering/scatter-adapters/oracle/
// physarum_oracle_generator.mjs. See that generator's curated set
// (physarum-oracles.json) and 12,000-case randomized differential sweep
// (scatter-adapters report) for the full verification.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_physarum_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("points/physarum:deposit") != nullptr);
}

// oracle case index 0: pos.w = 0.2 < 0.5 -- dead, skip entirely.
TEST(scatter_physarum_direct_call_skips_dead_agent) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x3e4ccccd};
  const std::vector<std::uint32_t> rgba_bits{0x3f800000, 0x3f800000, 0x3f800000, 0x3f800000};
  const std::vector<std::uint32_t> dest_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> expected_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::physarum::Uniforms uniforms;
  uniforms.deposit = 3.0;

  const std::size_t pixels = noisemaker::scatter::physarum::run_deposit(xyz_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 0U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 1: pos.w = 0.5 boundary -- alive; ALL FOUR channels
// (including alpha) scale by the `deposit` uniform.
TEST(scatter_physarum_direct_call_matches_js_oracle_1x1_alive) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x3f000000};
  const std::vector<std::uint32_t> rgba_bits{0x3e800000, 0x3f000000, 0x3f400000, 0x3f800000};
  const std::vector<std::uint32_t> dest_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> expected_bits{0x3f400000, 0x3fc00000, 0x40100000, 0x40400000};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::physarum::Uniforms uniforms;
  uniforms.deposit = 3.0;

  const std::size_t pixels = noisemaker::scatter::physarum::run_deposit(xyz_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 1U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 4: 6x6 agents -> 2x2 destination (36 agents onto 4
// pixels forces real overlapping accumulation), via the registry dispatch
// path.
TEST(scatter_physarum_via_registry_matches_js_oracle_6x6_overlap) {
  const std::vector<std::uint32_t> xyz_bits{
      0x3f93bd24, 0xbf11130e, 0x3d442dd2, 0xbd8a96f7, 0xbf07e02f, 0x3fa38e51, 0x3fce68ea, 0x3ede8d89,
      0x444809de, 0x3fa75827, 0x40000000, 0x3fd482ef, 0x3f97791e, 0xc37cdbc2, 0xbf800000, 0xc440ed8b,
      0xbf7143d0, 0x3fdbcf19, 0x3fe00445, 0x3f31c277, 0x3fa4d066, 0xbf01eda7, 0x3f06ee59, 0x3ee9fa56,
      0xbf2af993, 0x3fcf5ba6, 0x3f712af5, 0xbeca8acb, 0xbf6f2be7, 0x40000000, 0xbd06923b, 0x3fad6437,
      0xbec0e688, 0x3f690505, 0x3e74bc74, 0x3f87966b, 0xbe1e1645, 0xbdcebc18, 0x3e86754a, 0x430656a0,
      0x3f84dad2, 0xc2d539c1, 0xbd96a753, 0x3f800000, 0x3fee06f6, 0xbf5dd24d, 0x3fa30025, 0x3ecab112,
      0xbf080bfa, 0x3fd17ccd, 0x3dbb375a, 0x3ff5ac6e, 0x3e4829e3, 0x3ddee301, 0x3eefb788, 0x3ffd69cf,
      0x3f7feead, 0x3f15108c, 0xbe95b149, 0x3e7ca4a2, 0x4436a23c, 0x3f3a9336, 0x3f034432, 0x3d62840a,
      0x3e99c859, 0xbf000000, 0x3e872187, 0x443ec1d5, 0xc4555099, 0x3fc31a04, 0x3ee7ab20, 0x3f8f3141,
      0x3fc0b059, 0xbf5d1278, 0xbf2a69db, 0xbf7bc538, 0xbf16a2f8, 0x3f3616a2, 0x3eec0dd3, 0x3f275f68,
      0xbf1f738a, 0x3f4f03d0, 0x3fc6544e, 0xc46f6500, 0x3ee6938c, 0xbecd7def, 0x3f5701c4, 0xbe3a3307,
      0x3fe05ec7, 0xbe90a180, 0x441d18ca, 0x3f2e30f1, 0x3f798044, 0xbe3b8f71, 0x441a2714, 0x3e2305b7,
      0x3dbe7465, 0xbf800000, 0x3ed51d30, 0xbf48f274, 0x3f1f030b, 0x3f373bdc, 0x3f9542b0, 0x3fd4e570,
      0x3f5051ad, 0x3f4d0042, 0x3e279a74, 0x7fc00000, 0x442c047d, 0x3f000000, 0x3fd65319, 0xbed0d0dd,
      0x00000000, 0x43a6a2dd, 0x3f9f1985, 0x40000000, 0x3fa0fd2c, 0x3f549b1e, 0x3f29ddad, 0x3f70e203,
      0x3fcf0232, 0x3ff4f7d9, 0xbf15e6c5, 0xbca77caa, 0x7fc00000, 0xbed5aa97, 0x3fee87c9, 0x4475657b,
      0xbf4918ae, 0x3fc172ce, 0xbe3dd009, 0x3e5202f6, 0xbeee237d, 0xbd9498c7, 0x3f2cb5c8, 0x3f897a08,
      0x3fc968a7, 0xc9742400, 0x3f18a4c0, 0x3d6d98c6, 0x3feed5ca, 0x3fa5ecd2, 0x3f295956, 0x3ffc4e55,
  };
  const std::vector<std::uint32_t> rgba_bits{
      0x3fc376c8, 0x3e7164eb, 0x43a8d51c, 0xbf0d6554, 0x3fa231d2, 0x3fa75686, 0xbf535e44, 0xbc75f3a6,
      0x3eb23617, 0xc370c0c2, 0x7f800000, 0x3e5b70b6, 0xc263d079, 0x3ff03560, 0xc424242b, 0xbe520c00,
      0xbf1852b6, 0x3f1f3acc, 0x3fe62639, 0x3fd89bab, 0xbf32c972, 0x3fd899f9, 0xbf201bd7, 0x3f000000,
      0xbf75d59b, 0xbea00e34, 0x40000000, 0xbf61f685, 0x3fb825dd, 0x3e4618fe, 0xbf063ec1, 0xbef6770e,
      0x3f32e385, 0x3f49316a, 0x3fe8392f, 0x3fa264c8, 0xbecc2068, 0x3fdbf0c9, 0xc9742400, 0x3dac1cb5,
      0x3e3ce9e0, 0xbf0ca41c, 0x3ff12fc0, 0xbf2811eb, 0xbf3302b0, 0x3ebacc16, 0x3ffed753, 0x49742400,
      0x358637bd, 0xc45189a1, 0xbed1fea2, 0x3fc51ef7, 0x3f198447, 0xbed6a1bf, 0x3f4ecf71, 0x3d62cb7e,
      0x4406ffc5, 0xbe4af643, 0x3dbd114e, 0x3f800000, 0x3d624ade, 0x40000000, 0xbf51d762, 0xbf7820c0,
      0x358637bd, 0x3f8c5cf1, 0xbf29b5c7, 0x3f356970, 0x3f8a03ea, 0x3fdac4a7, 0xbe1d1350, 0xbf7c7b38,
      0xc43d3d73, 0x3ee29f34, 0xbf800000, 0x3fe17c0e, 0xbf156383, 0xbc8be2f9, 0x3f3c3516, 0xbf3f766d,
      0xbf12dfeb, 0x3f4549d6, 0x00000000, 0x3fe2b236, 0x3eec841c, 0xc9742400, 0x3f98f9b3, 0x3f38bf18,
      0xbf7d7024, 0x3dbb5b06, 0x3f57a747, 0x3ee5f8f5, 0x3e8d13c5, 0x3ed178f8, 0xbf25076f, 0x3f000000,
      0x3ffd0fab, 0x43ad67e9, 0x3cfcdfb9, 0x3e216a91, 0x3f8be4ac, 0xbf3326a1, 0xbd9f0749, 0x3fb0b4ee,
      0x3fb4b461, 0x3ff7a4c4, 0xbeda2a54, 0xbe33f238, 0xbe52f07b, 0x3f880bae, 0xbddc0e51, 0x3eaea9f2,
      0x3edb0e41, 0x7f800000, 0xff800000, 0xbf4583bd, 0xbf5fc614, 0x3fe01263, 0xbc4fb69c, 0xbedd4820,
      0xbe39474d, 0x3fdc3970, 0xc4574236, 0x3e46d900, 0x3ff131d2, 0x7fc00000, 0xbf000000, 0xbda6bb99,
      0x43c13eae, 0x3fe77eaa, 0x3fade7a7, 0x3e44aebe, 0x3fa4a78b, 0x3ed0abf2, 0x3fcd16e9, 0x49742400,
      0x3f2d7663, 0xc0000000, 0x3e0a4344, 0xbf5485b5, 0x3e619ffb, 0xbf0cc8cb, 0x3ed60067, 0xbf569838,
  };
  const std::vector<std::uint32_t> dest_bits{
      0x3f6c3e3c, 0xbf6c9c2e, 0xc3ece042, 0x3fcdb3ff, 0x3fd395d8, 0x3ea24836, 0x3e391a71, 0xbefbfd6f,
      0xc9742400, 0x40000000, 0x3ef51d13, 0x3fce490a, 0x42094e65, 0xbf800000, 0x445bbb5f, 0xbe91ae24,
  };
  const std::vector<std::uint32_t> expected_bits{
      0x3f6c3e3c, 0xbf6c9c2e, 0xc3ece042, 0x3fcdb3ff, 0x4107dabf, 0x406c0d87, 0xbf98e5da, 0x403301d0,
      0xc97423e6, 0x3f5b057c, 0x402bca4b, 0x3fe1a258, 0x42094e65, 0xbf800000, 0x445bbb5f, 0xbe91ae24,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("points/physarum:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface xyz_tex(6, 6, bits_to_floats(xyz_bits));
  noisemaker::Surface rgba_tex(6, 6, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(2, 2, bits_to_floats(dest_bits));

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("xyzTex", xyz_tex);
  bindings.set_texture("rgbaTex", rgba_tex);
  bindings.set_uniform("deposit", 2.730057283770293);

  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 3U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
