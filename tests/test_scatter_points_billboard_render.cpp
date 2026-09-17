#include "test_harness.hpp"

#include <cstdint>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/points_billboard_render.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

namespace {

// Regression vectors below were captured directly from the real,
// unmodified `pointsBillboardRenderDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/billboard-deposit.js) via a small standalone driver
// (see docs/port-engineering/scatter-adapters/scatter-adapters-report.md)
// built on top of docs/port-engineering/scatter-adapters/oracle/
// points_billboard_render_oracle_generator.mjs's own methodology. See that
// generator's 167-case curated set (points_billboard_render-oracles.json)
// and 15,000-case randomized differential sweep for the full verification.
std::vector<float> bits_to_floats(const std::vector<std::uint32_t>& bits) {
  std::vector<float> out;
  out.reserve(bits.size());
  for (const auto b : bits) out.push_back(noisemaker::uint_bits_to_float(b));
  return out;
}

// Shared fixture: one 1x1 alive agent, one 2x2 sprite texture (4 distinct
// grayscale corners), a constant-0.5 5x5 spriteMeanTex, flat view,
// shapeMode 0 (textured sprite) unless overridden. All four regression
// tests below share this agent/sprite geometry so the reader can compare
// "same everything except X" across additive vs premultiplied vs dead vs
// procedural-shape.
struct Fixture {
  noisemaker::Surface xyz_tex;
  noisemaker::Surface rgba_tex;
  noisemaker::Surface order_tex;
  noisemaker::Surface sprite_tex;
  noisemaker::Surface sprite_mean_tex;

  explicit Fixture(std::uint32_t xyz_w_bits)
      : xyz_tex(1, 1, bits_to_floats({0x3f000000, 0x3f000000, 0x00000000, xyz_w_bits})),
        rgba_tex(1, 1, bits_to_floats({0x3f800000, 0x3f19999a, 0x3e99999a, 0x3f4ccccd})),
        order_tex(1, 1, std::vector<float>{0.0F, 0.0F, 0.0F, 0.0F}),
        sprite_tex(2, 2, bits_to_floats({0x3f800000, 0x3f800000, 0x3f800000, 0x3f800000, 0x3f000000,
                                          0x3f000000, 0x3f000000, 0x3f800000, 0x3e800000, 0x3e800000,
                                          0x3e800000, 0x3f800000, 0x3f400000, 0x3f400000, 0x3f400000,
                                          0x3f800000})),
        sprite_mean_tex(5, 5, std::vector<float>(5 * 5 * 4, 0.5F)) {}
};

noisemaker::scatter::points_billboard_render::Uniforms base_uniforms() {
  noisemaker::scatter::points_billboard_render::Uniforms u;
  u.density = 100;
  u.view_mode = 0;
  u.view_scale = 1;
  u.shape_mode = 0;
  u.blend_mode = 0;
  u.deposit_opacity = 100;
  u.seed = 1;
  u.size_variation = 0;
  u.rotation_var = 0;
  u.point_size = 3;
  return u;
}

std::vector<std::uint32_t> shared_dest_seed_bits() {
  return {0xbe4ccccd, 0xbdcccccd, 0x00000000, 0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd,
          0xbdcccccd, 0x00000000, 0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd, 0xbdcccccd};
}

}  // namespace

TEST(scatter_points_billboard_render_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("render/pointsBillboardRender:deposit") != nullptr);
}

// Additive blend (pass.blend absent -> isPremultipliedBlend false), alive
// agent, shapeMode 0 (textured sprite), flat view.
TEST(scatter_points_billboard_render_direct_call_matches_js_oracle_additive_sprite) {
  Fixture fixture(0x3f800000);  // xyz.w = 1 -> alive
  noisemaker::Surface destination(2, 2, bits_to_floats(shared_dest_seed_bits()));
  const std::vector<std::uint32_t> expected_bits{0x3f4ccccd, 0x3f000000, 0x3e99999a, 0x3f666667, 0x3f333333,
                                                  0x3f19999a, 0x3f0ccccd, 0x3f19999a, 0x3e19999a, 0x3e19999a,
                                                  0x3e333334, 0x3f800000, 0x3f866666, 0x3f59999a, 0x3cccccd0,
                                                  0x3f333333};

  auto uniforms = base_uniforms();
  const noisemaker::scatter::ScatterPass pass;  // no pass.blend -> additive
  const std::size_t pixels = noisemaker::scatter::points_billboard_render::run_deposit(
      fixture.xyz_tex, fixture.rgba_tex, fixture.order_tex, fixture.sprite_tex, fixture.sprite_mean_tex, uniforms,
      pass, destination);
  REQUIRE(pixels == 4U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// SAME agent/sprite/destination pre-seed as the additive case above, but
// `pass.blend = ["ONE", "ONE_MINUS_SRC_ALPHA"]` (deposit_alpha's
// premultiplied-over blend) -- a genuinely different accumulation formula,
// via the registry dispatch path.
TEST(scatter_points_billboard_render_via_registry_matches_js_oracle_premultiplied_sprite) {
  Fixture fixture(0x3f800000);  // xyz.w = 1 -> alive
  noisemaker::Surface destination(2, 2, bits_to_floats(shared_dest_seed_bits()));
  const std::vector<std::uint32_t> expected_bits{0x3f75c28f, 0x3f147ae2, 0x3e99999a, 0x3f51eb85, 0x3f0a3d71,
                                                  0x3eb851ec, 0x3e6b851f, 0x3f428f5c, 0x3e6b851f, 0x3e19999a,
                                                  0x3dc28f5c, 0x3f570a3e, 0x3f4f5c29, 0x3f07ae15, 0x3e3d70a5,
                                                  0x3f47ae15};

  noisemaker::scatter::register_builtin_scatter_adapters();
  const auto adapter = noisemaker::scatter::resolve_scatter_adapter("render/pointsBillboardRender:deposit");
  REQUIRE(adapter != nullptr);

  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("xyzTex", fixture.xyz_tex);
  bindings.set_texture("rgbaTex", fixture.rgba_tex);
  bindings.set_texture("orderTex", fixture.order_tex);
  bindings.set_texture("spriteTex", fixture.sprite_tex);
  bindings.set_texture("spriteMeanTex", fixture.sprite_mean_tex);
  const auto uniforms = base_uniforms();
  bindings.set_uniform("density", uniforms.density);
  bindings.set_uniform("viewMode", uniforms.view_mode);
  bindings.set_uniform("rotateX", uniforms.rotate_x);
  bindings.set_uniform("rotateY", uniforms.rotate_y);
  bindings.set_uniform("rotateZ", uniforms.rotate_z);
  bindings.set_uniform("posX", uniforms.pos_x);
  bindings.set_uniform("posY", uniforms.pos_y);
  bindings.set_uniform("viewScale", uniforms.view_scale);
  bindings.set_uniform("shapeMode", uniforms.shape_mode);
  bindings.set_uniform("blendMode", uniforms.blend_mode);
  bindings.set_uniform("depositOpacity", uniforms.deposit_opacity);
  bindings.set_uniform("seed", uniforms.seed);
  bindings.set_uniform("sizeVariation", uniforms.size_variation);
  bindings.set_uniform("rotationVar", uniforms.rotation_var);
  bindings.set_uniform("pointSize", uniforms.point_size);

  noisemaker::scatter::ScatterPass pass;
  pass.blend_factors = std::make_pair(std::string("ONE"), std::string("ONE_MINUS_SRC_ALPHA"));
  const std::size_t pixels = adapter(bindings, pass, destination);
  REQUIRE(pixels == 4U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}

// Dead agent (xyz.w = 0.1 < 0.5) -- draws nothing regardless of blend
// mode; destination stays byte-identical to its pre-seed.
TEST(scatter_points_billboard_render_direct_call_skips_dead_agent) {
  Fixture fixture(0x3dcccccd);  // xyz.w = 0.1 -> dead
  const auto dest_bits = shared_dest_seed_bits();
  noisemaker::Surface destination(2, 2, bits_to_floats(dest_bits));

  auto uniforms = base_uniforms();
  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = noisemaker::scatter::points_billboard_render::run_deposit(
      fixture.xyz_tex, fixture.rgba_tex, fixture.order_tex, fixture.sprite_tex, fixture.sprite_mean_tex, uniforms,
      pass, destination);
  REQUIRE(pixels == 0U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < dest_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == dest_bits[i]);
  }
}

// Procedural shapeMode 3 (square SDF, no sprite sampling at all) into a
// 3x3 destination -- exercises signedDistanceForShape's square branch and
// billboardShapeAlpha's smoothstep coverage rule end to end.
TEST(scatter_points_billboard_render_direct_call_matches_js_oracle_procedural_square) {
  Fixture fixture(0x3f800000);  // xyz.w = 1 -> alive
  const std::vector<std::uint32_t> dest_bits{
      0xbe4ccccd, 0xbdcccccd, 0x00000000, 0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd,
      0xbdcccccd, 0x00000000, 0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd, 0xbdcccccd,
      0x00000000, 0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd, 0xbdcccccd, 0x00000000,
      0x3dcccccd, 0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd, 0xbdcccccd, 0x00000000, 0x3dcccccd,
      0x3e4ccccd, 0x3e99999a, 0x3ecccccd, 0xbe4ccccd,
  };
  const std::vector<std::uint32_t> expected_bits{
      0x3f4ccccd, 0x3f000000, 0x3e99999a, 0x3f666667, 0x3f99999a, 0x3f666667, 0x3f333334, 0x3f19999a,
      0x3f666666, 0x3f19999a, 0x3ecccccd, 0x3f800000, 0x3fa66666, 0x3f800000, 0x3dccccce, 0x3f333333,
      0x3f800000, 0x3f333334, 0x3f000000, 0x3f8ccccd, 0x3fb33333, 0x3eccccce, 0x3e4cccce, 0x3f4ccccd,
      0x3f8ccccd, 0x3f4ccccd, 0x3f19999a, 0x3f99999a, 0x3f4ccccd, 0x3f000000, 0x3e99999a, 0x3f666667,
      0x3f99999a, 0x3f666667, 0x3f333334, 0x3f19999a,
  };
  noisemaker::Surface destination(3, 3, bits_to_floats(dest_bits));

  auto uniforms = base_uniforms();
  uniforms.shape_mode = 3;
  uniforms.point_size = 4;
  const noisemaker::scatter::ScatterPass pass;
  const std::size_t pixels = noisemaker::scatter::points_billboard_render::run_deposit(
      fixture.xyz_tex, fixture.rgba_tex, fixture.order_tex, fixture.sprite_tex, fixture.sprite_mean_tex, uniforms,
      pass, destination);
  REQUIRE(pixels == 9U);
  const auto got = destination.data();
  for (std::size_t i = 0; i < expected_bits.size(); ++i) {
    REQUIRE(noisemaker::float_bits_to_uint(got[i]) == expected_bits[i]);
  }
}
