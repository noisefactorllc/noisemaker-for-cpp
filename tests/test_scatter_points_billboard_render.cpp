#include "test_harness.hpp"

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/points_billboard_render.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

TEST(scatter_points_billboard_render_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("render/pointsBillboardRender:deposit") != nullptr);
}
