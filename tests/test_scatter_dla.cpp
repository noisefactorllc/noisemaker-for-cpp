#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/dla.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `dlaDepositGridAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:176-216) via
// docs/port-engineering/scatter-adapters/oracle/dla_oracle_generator.mjs.
// See that generator's 108-case curated set (dla-oracles.json) and
// 12,000-case randomized differential sweep (scatter-adapters report) for
// the full verification; these three exist for durable in-repo coverage.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_dla_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("points/dla:depositGrid") != nullptr);
}

// oracle case index 0: vel.y = 0.1 < 0.5 -- NOT "just stuck", skip entirely.
TEST(scatter_dla_direct_call_skips_agent_not_just_stuck) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> vel_bits{0x00000000, 0x3dcccccd, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> rgba_bits{0x3f800000, 0x3f800000, 0x3f800000, 0x3f800000};
  const std::vector<std::uint32_t> dest_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> expected_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface vel_tex(1, 1, bits_to_floats(vel_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::dla::Uniforms uniforms;
  uniforms.deposit = 10.0;

  const std::size_t pixels = noisemaker::scatter::dla::run_deposit(xyz_tex, vel_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 0U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 1: vel.y = 0.5 boundary -- kept (skip is `< 0.5`, so
// exactly 0.5 deposits). Alpha is `energy` alone (deposit*0.1), NOT
// `rgba.a * energy`.
TEST(scatter_dla_direct_call_matches_js_oracle_1x1_just_stuck) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> vel_bits{0x00000000, 0x3f000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> rgba_bits{0x3e4ccccd, 0x3ecccccd, 0x3f19999a, 0x3f4ccccd};
  const std::vector<std::uint32_t> dest_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> expected_bits{0x3da3d70a, 0x3e23d70a, 0x3e75c290, 0x3ecccccd};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface vel_tex(1, 1, bits_to_floats(vel_bits));
  noisemaker::Surface rgba_tex(1, 1, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::dla::Uniforms uniforms;
  uniforms.deposit = 4.0;

  const std::size_t pixels = noisemaker::scatter::dla::run_deposit(xyz_tex, vel_tex, rgba_tex, uniforms, destination);
  REQUIRE(pixels == 1U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 17: 1x7 agents -> 1x7 destination, deposit=1000 --
// exercised via the registry dispatch path.
TEST(scatter_dla_via_registry_matches_js_oracle_1x7) {
  const std::vector<std::uint32_t> xyz_bits{
      0x3f991bd8, 0xbf2e91ba, 0xc2d8f4d5, 0xbdc645e6, 0xff800000, 0x49742400, 0x3f5ee919, 0x3dccebfd,
      0x3fbca4b9, 0xc373cc60, 0x80000000, 0x3ff279d9, 0x3e6fcc3b, 0x00000000, 0xbf4746d7, 0x3ffca513,
      0x3f2ac762, 0x3e974ddb, 0x3f9c62cc, 0xc3c9fe2c, 0xbf655bff, 0x3ed55f8d, 0x3fa6849d, 0x3fff8afe,
      0x3ff6a4a9, 0xbf4399dd, 0x3f3c84fe, 0x444b6cc2,
  };
  const std::vector<std::uint32_t> vel_bits{
      0xbf7b1d20, 0xbe1388b4, 0x3f800000, 0x3f567fc4, 0x3fafc94d, 0xbc8d6af9, 0xc9742400, 0x3f0973f2,
      0x3e035a4a, 0x3f923f9e, 0x3e1e5037, 0xbf6d380d, 0xbe263a55, 0x3fcf374c, 0xc9742400, 0x3f6b708d,
      0x3f6ba5f9, 0x3f0e3d16, 0x3f6547a2, 0xbe905ce0, 0x3f633db1, 0x49742400, 0x3f3b1454, 0xbf0648ce,
      0x4263202c, 0x3ffb65ae, 0x3e91605f, 0x3f8de2d2,
  };
  const std::vector<std::uint32_t> rgba_bits{
      0x3e790103, 0xbe17aa04, 0xc308f7fc, 0xc44146af, 0xbf622f07, 0xbf564fd4, 0xbf2bcac8, 0x7fc00000,
      0x3f4f0f18, 0x445f59da, 0xbf7e8abb, 0xbeb3c769, 0x3fd25eb6, 0xbe9a99dd, 0xbf000000, 0x358637bd,
      0xbd96362c, 0x3fef92fb, 0x3fd66f37, 0x3fe7a769, 0xbf775937, 0x3f12b499, 0xbe7171b9, 0x3ff7caa7,
      0x3f8b86c6, 0x3ee593fb, 0x3fc79c30, 0x3fb70630,
  };
  const std::vector<std::uint32_t> dest_bits{
      0xbede78fa, 0xbe41795c, 0x3ff18e10, 0xc9742400, 0xbf46bf30, 0x3ff9a9f8, 0x3e08c28e, 0x358637bd,
      0xbf47db54, 0xbed788a7, 0xc460be52, 0x3f7937c6, 0xbe8a5fb7, 0x3ee251ea, 0xc4743b30, 0x3f86e464,
      0x3fe3ef6a, 0xc45e692b, 0x3ebcdb2f, 0x00000000, 0xff800000, 0x3ef2aaa8, 0x3ea3e476, 0x3de572d5,
      0xc9742400, 0x39fe05a8, 0x3f8a8fe6, 0x3ff9de4f,
  };
  const std::vector<std::uint32_t> expected_bits{
      0xbede78fa, 0xbe41795c, 0x3ff18e10, 0xc9742400, 0xbf46bf30, 0x3ff9a9f8, 0x3e08c28e, 0x358637bd,
      0xbf47db54, 0xbed788a7, 0xc460be52, 0x3f7937c6, 0xbe8a5fb7, 0x3ee251ea, 0xc4743b30, 0x3f86e464,
      0xc0b1b8ca, 0xc42f9e76, 0x4327e551, 0x42c80000, 0xff800000, 0x3ef2aaa8, 0x3ea3e476, 0x3de572d5,
      0xc97419ba, 0xc1f18f6b, 0xc243ab81, 0x42cbe779,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("points/dla:depositGrid");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface xyz_tex(1, 7, bits_to_floats(xyz_bits));
  noisemaker::Surface vel_tex(1, 7, bits_to_floats(vel_bits));
  noisemaker::Surface rgba_tex(1, 7, bits_to_floats(rgba_bits));
  noisemaker::Surface destination(1, 7, bits_to_floats(dest_bits));

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("xyzTex", xyz_tex);
  bindings.set_texture("velTex", vel_tex);
  bindings.set_texture("rgbaTex", rgba_tex);
  bindings.set_uniform("deposit", 1000.0);

  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 2U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
