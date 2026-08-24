#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/effects/scatter/wormhole.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real, unmodified
// `runWormholeDeposit` (noisemaker-for-cpu: src/effects/cpu/wormhole.js),
// independent of and smaller than the full 62-case/9-mutation oracle at
// docs/port-engineering/wormhole/oracle/wormhole-oracles.json (see
// wormhole-report.md for that full verification). These three exist so this
// port carries its own durable, in-repo regression coverage without
// depending on an out-of-tree fixture.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

}  // namespace

TEST(scatter_wormhole_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("filter/wormhole:deposit") != nullptr);
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("filter/no-such-effect:deposit") == nullptr);
}

TEST(scatter_wormhole_direct_call_matches_js_oracle_mirror_4x3) {
  const std::vector<std::uint32_t> input_bits{
      0x3e7353a5, 0x3f30d322, 0x3f5b6db7, 0x3dc9ea5e, 0x3f1a9d26, 0x3f5db0d3, 0x3f070871, 0x3e81cd85,
      0x3c2237c3, 0x3dfd5c5f, 0x3e4a8ca9, 0x3ed12073, 0x3ec0a238, 0x3e991279, 0x3f47bc7c, 0x3f1039b1,
      0x3ed9faee, 0x3e4893cb, 0x3f6f1ef2, 0x3e9039b1, 0x3f4ac5b4, 0x3ebe0547, 0x3f1ab9ac, 0x3edf8c9f,
      0x3e4ac5b4, 0x3f0be054, 0x3e8ca8cb, 0x3f176fc6, 0x3f1079aa, 0x3f38be05, 0x3f5b6db7, 0x3f3f193d,
      0x3f1d2605, 0x3f1e59bb, 0x3dca8ca9, 0x3eedf8ca, 0x3ca237c3, 0x3f4b376c, 0x3f2e6ae7, 0x3f1ea5dc,
      0x3ec5b3f6, 0x3d53224f, 0x3eb40b41, 0x3f464f53, 0x3f40a238, 0x3e683f57, 0x3f6f1ef2, 0x3d9039b1,
  };
  const std::vector<std::uint32_t> expected_output_bits{
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3e444000, 0x3e1c0000, 0x3ecb8000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3ed7c000, 0x3ed96000, 0x3d8b0000, 0x00000000, 0x3f1dc000, 0x3e8d4000, 0x3f076000, 0x00000000,
      0x3e394000, 0x3f852000, 0x3f8a0000, 0x00000000, 0x3f34e000, 0x3f516000, 0x3f61e000, 0x00000000,
      0x3f5e6000, 0x3f31a000, 0x3f99a000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
  };

  noisemaker::Surface input(4, 3, bits_to_floats(input_bits));
  noisemaker::Surface destination(4, 3);
  noisemaker::scatter::wormhole::Uniforms uniforms;
  uniforms.kink = 1.1;
  uniforms.stride = 0.7;
  uniforms.rotation = 25.0;
  uniforms.wrap = 0.0;  // mirror

  noisemaker::scatter::wormhole::run_deposit(input, destination, uniforms);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_output_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_output_bits[i]);
  }
}

TEST(scatter_wormhole_via_registry_matches_js_oracle_repeat_3x4) {
  const std::vector<std::uint32_t> input_bits{
      0x3eee41e7, 0x3d93cb37, 0x3e924925, 0x3f1ea5dc, 0x3f54e930, 0x3e7d5c5f, 0x3f5e3de4, 0x3f464f53,
      0x3e7353a5, 0x3ed86991, 0x3f09d89e, 0x3d9039b1, 0x3f274981, 0x3efd5c5f, 0x3eb9ab9b, 0x3f4d8569,
      0x3d7353a5, 0x3f2b8be0, 0x3d070871, 0x3dc9ea5e, 0x3ed9faee, 0x3f586991, 0x3f1d89d9, 0x3e81cd85,
      0x3f57720f, 0x3f6ae2f8, 0x3ee10e11, 0x3e01cd85, 0x3e7d7721, 0x3e3376c3, 0x3de10e11, 0x3e9039b1,
      0x3f1d2605, 0x3eb376c3, 0x3f313b14, 0x3edf8c9f, 0x3d8df0cb, 0x3ed86991, 0x3f043844, 0x3e9ea5dc,
      0x3edf0cac, 0x3f191279, 0x3e3f4bf5, 0x3eedf8ca, 0x3f4d4e93, 0x3f45f02a, 0x3f44ec4f, 0x3f1ea5dc,
  };
  const std::vector<std::uint32_t> expected_output_bits{
      0x3e420000, 0x3ed70000, 0x3de9e000, 0x00000000, 0x3fcda000, 0x3f968000, 0x3fa82000, 0x00000000,
      0x3ed90000, 0x3ea46000, 0x3e70e000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3da60000, 0x3d6b2000, 0x3d136000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3eae8000, 0x3f2d4000, 0x3efc4000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3f56e000, 0x3f8ae000, 0x3f982000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x3e8fe000, 0x3ec58000, 0x3df6c000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
  };

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("filter/wormhole:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::Surface input(3, 4, bits_to_floats(input_bits));
  noisemaker::Surface destination(3, 4);

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("kink", 0.4);
  bindings.set_uniform("stride", 1.6);
  bindings.set_uniform("rotation", -95.0);
  bindings.set_uniform("wrap", 1.0);  // repeat

  const std::size_t pixels = adapter(bindings, destination);
  REQUIRE(pixels == 3U * 4U);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_output_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_output_bits[i]);
  }
}

TEST(scatter_wormhole_clamp_wrap_matches_js_oracle_5x2) {
  const std::vector<std::uint32_t> input_bits{
      0x3f316cfd, 0x3ebe0547, 0x3f205a06, 0x3e9039b1, 0x3dcac5b4, 0x3f0be054, 0x3e97e97f, 0x3edf8c9f,
      0x3eee41e7, 0x3f38be05, 0x3f610e11, 0x3f176fc6, 0x3f54e930, 0x3f659bb6, 0x3f0ca8cb, 0x3f3f193d,
      0x3e7353a5, 0x3e1e59bb, 0x3e610e11, 0x3f66c2b4, 0x3f61958b, 0x3f4b376c, 0x3f340b41, 0x3eedf8ca,
      0x3e930289, 0x3d53224f, 0x3ebf4bf5, 0x3f1ea5dc, 0x3f274981, 0x3e683f57, 0x3d340b41, 0x3f464f53,
      0x3d7353a5, 0x3ecddb0d, 0x3f205a06, 0x3d9039b1, 0x3ed9faee, 0x3f13cb37, 0x3e97e97f, 0x3e66c2b4,
  };
  const std::vector<std::uint32_t> expected_output_bits{
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x3f3ea000, 0x3f4da000, 0x3efc0000, 0x00000000,
      0x4016c000, 0x401fc000, 0x4020a000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
      0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
  };

  noisemaker::Surface input(5, 2, bits_to_floats(input_bits));
  noisemaker::Surface destination(5, 2);
  noisemaker::scatter::wormhole::Uniforms uniforms;
  uniforms.kink = 2.2;
  uniforms.stride = 0.3;
  uniforms.rotation = 150.0;
  uniforms.wrap = 2.0;  // clamp

  noisemaker::scatter::wormhole::run_deposit(input, destination, uniforms);

  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_output_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_output_bits[i]);
  }
}

TEST(scatter_wormhole_rejects_mismatched_dimensions) {
  noisemaker::Surface input(2, 2);
  noisemaker::Surface destination(3, 3);
  noisemaker::scatter::wormhole::Uniforms uniforms;
  REQUIRE_THROWS_AS(noisemaker::scatter::wormhole::run_deposit(input, destination, uniforms), std::invalid_argument);
}
