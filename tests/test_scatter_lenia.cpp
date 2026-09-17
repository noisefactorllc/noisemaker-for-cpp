#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/lenia.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `leniaDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/points-deposit.js:226-256) via
// docs/port-engineering/scatter-adapters/oracle/lenia_oracle_generator.mjs,
// independent of and smaller than that generator's full curated set (112
// cases, lenia-oracles.json) and 12,000-case randomized differential sweep
// (see the scatter-adapters report for the sweep's zero-divergence
// result). These exist so this port carries its own durable, in-repo
// regression coverage without depending on an out-of-tree fixture.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_lenia_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("points/lenia:deposit") != nullptr);
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("points/no-such-effect:deposit") == nullptr);
}

// oracle case index 0: 1x1, alive (xyz.w=1), depositAmount=1.25.
TEST(scatter_lenia_direct_call_matches_js_oracle_1x1_alive) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x3f800000};
  const std::vector<std::uint32_t> dest_bits{0x00000000, 0x00000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> expected_bits{0x3fa00000, 0x00000000, 0x00000000, 0x3f800000};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::lenia::Uniforms uniforms;
  uniforms.deposit_amount = 1.25;

  const std::size_t pixels = noisemaker::scatter::lenia::run_deposit(xyz_tex, uniforms, destination);
  REQUIRE(pixels == 1U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 1: 1x1, DEAD (xyz.w=0 < 0.5) -- must skip entirely;
// destination stays byte-identical to its pre-seed, and pixels == 0.
TEST(scatter_lenia_direct_call_skips_dead_agent) {
  const std::vector<std::uint32_t> xyz_bits{0x3f000000, 0x3f000000, 0x00000000, 0x00000000};
  const std::vector<std::uint32_t> dest_bits{0x3f800000, 0x40000000, 0x40400000, 0x40800000};
  const std::vector<std::uint32_t> expected_bits{0x3f800000, 0x40000000, 0x40400000, 0x40800000};

  noisemaker::Surface xyz_tex(1, 1, bits_to_floats(xyz_bits));
  noisemaker::Surface destination(1, 1, bits_to_floats(dest_bits));
  noisemaker::scatter::lenia::Uniforms uniforms;
  uniforms.deposit_amount = 9.0;

  const std::size_t pixels = noisemaker::scatter::lenia::run_deposit(xyz_tex, uniforms, destination);
  REQUIRE(pixels == 0U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// oracle case index 17: 1x7 agents -> 1x7 destination, depositAmount=0 --
// exercises the "always deposits the fixed (amount, 0, 0, 1) constant"
// rule even when amount itself is 0 (alpha still gets +1), via the
// registry dispatch path rather than a direct run_deposit call.
TEST(scatter_lenia_via_registry_matches_js_oracle_1x7_two_alive) {
  const std::vector<std::uint32_t> xyz_bits{
      0x3fab3c10, 0xff800000, 0xbf4d7d65, 0xc0000000, 0x3fd9760f, 0x3fd04f7c, 0xc3642439, 0x3ec2cf3e,
      0x49742400, 0x40000000, 0x3ea733af, 0xbf3d74de, 0x3fce0b68, 0xbf79cba1, 0xbf35e2b5, 0x3fbc0c1c,
      0xbe056ec4, 0xbdc359b9, 0xbe56e297, 0xc44abaae, 0x3cfe8220, 0x80000000, 0x3f82d2db, 0x3f906c1a,
      0x3f000000, 0x3e956e88, 0x3ff772d8, 0x3f60cc39,
  };
  const std::vector<std::uint32_t> dest_bits{
      0x3fe03269, 0xbf504e6e, 0xbef9356d, 0xbe614333, 0xbf06f2b5, 0x3ef6085b, 0xbeaf0d8b, 0xbe043c4d,
      0x3fc8354f, 0x3f2017e3, 0x3fa4d64c, 0x3e1126f3, 0x3f782a30, 0xbe2bc37d, 0xbf800000, 0xbf1b314d,
      0xbf38e900, 0x43b0f67f, 0x3f86bdd6, 0xc3f8c863, 0x00000000, 0x3fb156f9, 0x3ff8013e, 0xbe348b79,
      0xbf671dca, 0xbf800000, 0x3f701bf2, 0x3fc67456,
  };
  const std::vector<std::uint32_t> expected_bits{
      0x3fe03269, 0xbf504e6e, 0xbef9356d, 0xbe614333, 0xbf06f2b5, 0x3ef6085b, 0xbeaf0d8b, 0xbe043c4d,
      0x3fc8354f, 0x3f2017e3, 0x3fa4d64c, 0x3e1126f3, 0x3f782a30, 0xbe2bc37d, 0xbf800000, 0xbf1b314d,
      0xbf38e900, 0x43b0f67f, 0x3f86bdd6, 0xc3f84863, 0x00000000, 0x3fb156f9, 0x3ff8013e, 0xbe348b79,
      0xbf671dca, 0xbf800000, 0x3f701bf2, 0x40233a2b,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("points/lenia:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface xyz_tex(1, 7, bits_to_floats(xyz_bits));
  noisemaker::Surface destination(1, 7, bits_to_floats(dest_bits));

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("xyzTex", xyz_tex);
  bindings.set_uniform("depositAmount", 0.0);

  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 2U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
