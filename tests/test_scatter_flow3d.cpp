#include "test_harness.hpp"

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/flow3d.hpp"
#include "noisemaker/effects/scatter/registry.hpp"

TEST(scatter_flow3d_registers_under_the_canonical_key) {
  noisemaker::scatter::register_builtin_scatter_adapters();
  REQUIRE(noisemaker::scatter::resolve_scatter_adapter("filter3d/flow3d:deposit") != nullptr);
}
