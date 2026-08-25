#include "test_harness.hpp"

#include <cmath>
#include <limits>
#include <optional>
#include <type_traits>
#include <utility>
#include <vector>

#include "noisemaker/graph/resource.hpp"

namespace noisemaker::graph {

// Test-only access mirrors the executor's private construction seam without
// adding mutable resource access to the installed API.
class ResourceArenaTestAccess {
 public:
  static GraphResource& allocate(ResourceArena& arena, std::string name,
                                 std::size_t width, std::size_t height,
                                 noisemaker::TextureFormat format,
                                 ResourceLifetime lifetime) {
    return arena.allocate(std::move(name), width, height, format, lifetime);
  }

  static GraphResource& copy(ResourceArena& arena, std::string name,
                             const noisemaker::Surface& source,
                             noisemaker::TextureFormat format,
                             ResourceLifetime lifetime) {
    return arena.copy(std::move(name), source, format, lifetime);
  }

  static void retain(ResourceArena& arena, GraphResource& resource) {
    arena.retain(resource);
  }

  static void release(ResourceArena& arena, GraphResource& resource) {
    arena.release(resource);
  }

  static void retire(ResourceArena& arena, GraphResource& resource) {
    arena.retire(resource);
  }

  static void alias(ResourceArena& arena, std::string name,
                    GraphResource& resource) {
    arena.alias(std::move(name), resource);
  }

  static void remove_alias(ResourceArena& arena, std::string_view name) {
    arena.remove_alias(name);
  }
};

}  // namespace noisemaker::graph

static_assert(std::is_move_constructible_v<noisemaker::graph::GraphResource>);
static_assert(!std::is_copy_constructible_v<noisemaker::graph::GraphResource>);
static_assert(std::is_move_constructible_v<noisemaker::graph::ResourceArena>);
static_assert(!std::is_copy_constructible_v<noisemaker::graph::ResourceArena>);
static_assert(std::is_aggregate_v<noisemaker::graph::NamedSurface>);
static_assert(std::is_copy_constructible_v<noisemaker::graph::NamedSurface>);

TEST(graph_resource_format_aliases_and_authority_default) {
  using noisemaker::TextureFormat;
  using noisemaker::graph::resolve_texture_format;
  REQUIRE(resolve_texture_format(std::nullopt) == TextureFormat::rgba16f);
  REQUIRE(resolve_texture_format(std::string_view("rgba8")) ==
          TextureFormat::rgba8_unorm);
  REQUIRE(resolve_texture_format(std::string_view("rgba8unorm")) ==
          TextureFormat::rgba8_unorm);
  REQUIRE(resolve_texture_format(std::string_view("rgba16float")) ==
          TextureFormat::rgba16f);
  REQUIRE(resolve_texture_format(std::string_view("rgba32float")) ==
          TextureFormat::rgba32f);
  REQUIRE_THROWS_AS(resolve_texture_format(std::string_view()), std::invalid_argument);
  REQUIRE_THROWS_AS(resolve_texture_format(std::string_view("rgbaf")), std::invalid_argument);
}

TEST(graph_resource_checked_dimension_rejects_unsafe_values_before_cast) {
  REQUIRE(noisemaker::graph::checked_dimension(1.0) == 1U);
  REQUIRE(noisemaker::graph::checked_dimension(4096.0) == 4096U);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(0.0), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(-1.0), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(1.5), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(std::numeric_limits<double>::infinity()), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(std::numeric_limits<double>::quiet_NaN()), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::checked_dimension(9'007'199'254'740'992.0), std::invalid_argument);
}

TEST(graph_resource_arena_keeps_pointees_stable_across_growth) {
  noisemaker::graph::ResourceArena arena;
  auto& first = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "seed", 2U, 1U, noisemaker::TextureFormat::rgba32f,
      noisemaker::graph::ResourceLifetime::seed);
  const auto* first_address = &first;
  for (std::size_t index = 0; index < 128U; ++index) {
    noisemaker::graph::ResourceArenaTestAccess::allocate(
        arena, "scratch" + std::to_string(index), 1U, 1U,
        noisemaker::TextureFormat::rgba16f,
        noisemaker::graph::ResourceLifetime::transient);
  }
  REQUIRE(&arena.require("seed") == first_address);
  REQUIRE(arena.require("seed").width() == 2U);
  REQUIRE(arena.size() == 129U);
}

TEST(graph_resource_copies_caller_surface_data_and_filter) {
  noisemaker::Surface caller(2U, 1U,
                             std::vector<float>{0.1F, 0.2F, 0.3F, 0.4F,
                                                0.5F, 0.6F, 0.7F, 0.8F});
  caller.set_filter(noisemaker::TextureFilter::linear);
  const auto expected = std::vector<float>(caller.data().begin(), caller.data().end());
  noisemaker::graph::ResourceArena arena;
  auto& resource = noisemaker::graph::ResourceArenaTestAccess::copy(
      arena, "external", caller, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::external);
  caller.data()[0] = 1.0F;
  REQUIRE(resource.surface().filter() == noisemaker::TextureFilter::linear);
  REQUIRE(resource.surface().data()[0] == expected[0]);
  REQUIRE(resource.surface().data()[7] == expected[7]);
}

TEST(graph_resource_duplicate_route_replaces_lookup_deterministically) {
  noisemaker::graph::ResourceArena arena;
  noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  auto& replacement = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 3U, 2U, noisemaker::TextureFormat::rgba32f,
      noisemaker::graph::ResourceLifetime::published);
  REQUIRE(&arena.require("route") == &replacement);
  REQUIRE(arena.require("route").width() == 3U);
  REQUIRE(arena.size() == 1U);
}

TEST(graph_resource_retirement_waits_for_live_binding_then_releases) {
  noisemaker::graph::ResourceArena arena;
  auto& old = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  const auto* old_address = &old;
  noisemaker::graph::ResourceArenaTestAccess::retain(arena, old);
  auto& replacement = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 3U, 2U, noisemaker::TextureFormat::rgba32f,
      noisemaker::graph::ResourceLifetime::published);
  REQUIRE(arena.size() == 2U);
  REQUIRE(&old == old_address);
  REQUIRE(old.width() == 1U);
  REQUIRE(&arena.require("route") == &replacement);

  noisemaker::graph::ResourceArenaTestAccess::release(arena, old);
  REQUIRE(arena.size() == 1U);
  REQUIRE(&arena.require("route") == &replacement);
}

TEST(graph_resource_aliases_survive_route_replacement_until_all_refs_release) {
  noisemaker::graph::ResourceArena arena;
  auto& old = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  noisemaker::graph::ResourceArenaTestAccess::alias(arena, "alias", old);
  noisemaker::graph::ResourceArenaTestAccess::alias(arena, "alias", old);
  noisemaker::graph::ResourceArenaTestAccess::retain(arena, old);

  auto& replacement = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 3U, 2U, noisemaker::TextureFormat::rgba32f,
      noisemaker::graph::ResourceLifetime::published);
  REQUIRE(arena.size() == 2U);
  REQUIRE(&arena.require("route") == &replacement);
  REQUIRE(&arena.require("alias") == &old);
  REQUIRE(arena.require("alias").width() == 1U);

  noisemaker::graph::ResourceArenaTestAccess::remove_alias(arena, "alias");
  REQUIRE(arena.size() == 2U);
  noisemaker::graph::ResourceArenaTestAccess::release(arena, old);
  REQUIRE(arena.size() == 1U);
  REQUIRE(&arena.require("route") == &replacement);

  noisemaker::graph::ResourceArenaTestAccess::remove_alias(arena, "route");
  REQUIRE(arena.size() == 0U);
  REQUIRE_THROWS_AS(arena.require("route"), std::out_of_range);
}

TEST(graph_resource_surviving_alias_remains_bindable_after_route_replacement) {
  noisemaker::graph::ResourceArena arena;
  auto& old = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  noisemaker::graph::ResourceArenaTestAccess::alias(arena, "alias", old);
  auto& replacement = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 2U, 2U, noisemaker::TextureFormat::rgba32f,
      noisemaker::graph::ResourceLifetime::published);

  REQUIRE(&arena.require("alias") == &old);
  noisemaker::graph::ResourceArenaTestAccess::retain(arena, old);
  REQUIRE(arena.size() == 2U);
  noisemaker::graph::ResourceArenaTestAccess::remove_alias(arena, "alias");
  REQUIRE(arena.size() == 2U);
  noisemaker::graph::ResourceArenaTestAccess::release(arena, old);
  REQUIRE(arena.size() == 1U);
  REQUIRE(&arena.require("route") == &replacement);
}

TEST(graph_resource_aliases_survive_arena_move) {
  noisemaker::graph::ResourceArena source;
  auto& old = noisemaker::graph::ResourceArenaTestAccess::allocate(
      source, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  noisemaker::graph::ResourceArenaTestAccess::alias(source, "alias", old);
  noisemaker::graph::ResourceArena moved(std::move(source));
  REQUIRE(moved.require("alias").width() == 1U);
  REQUIRE(moved.require("route").width() == 1U);
  REQUIRE_THROWS_AS(source.require("alias"), std::out_of_range);
}

TEST(graph_resource_aliases_survive_arena_move_assignment) {
  noisemaker::graph::ResourceArena source;
  auto& old = noisemaker::graph::ResourceArenaTestAccess::allocate(
      source, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  noisemaker::graph::ResourceArenaTestAccess::alias(source, "alias", old);
  noisemaker::graph::ResourceArena target;
  noisemaker::graph::ResourceArenaTestAccess::allocate(
      target, "discarded", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  target = std::move(source);
  REQUIRE(target.require("alias").width() == 1U);
  REQUIRE(target.require("route").width() == 1U);
  REQUIRE_THROWS_AS(source.require("alias"), std::out_of_range);
}

TEST(graph_resource_alias_rejection_and_release_underflow_are_safe) {
  noisemaker::graph::ResourceArena arena;
  auto& resource = noisemaker::graph::ResourceArenaTestAccess::allocate(
      arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  noisemaker::graph::ResourceArenaTestAccess::release(arena, resource);
  REQUIRE(arena.size() == 1U);
  REQUIRE_THROWS_AS(noisemaker::graph::ResourceArenaTestAccess::alias(
                        arena, "", resource),
                    std::invalid_argument);

  noisemaker::graph::ResourceArena foreign_arena;
  auto& foreign = noisemaker::graph::ResourceArenaTestAccess::allocate(
      foreign_arena, "foreign", 1U, 1U, noisemaker::TextureFormat::rgba16f,
      noisemaker::graph::ResourceLifetime::transient);
  REQUIRE_THROWS_AS(noisemaker::graph::ResourceArenaTestAccess::alias(
                        arena, "foreign-alias", foreign),
                    std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::graph::ResourceArenaTestAccess::retain(
                        arena, foreign),
                    std::invalid_argument);
  noisemaker::graph::ResourceArenaTestAccess::release(arena, foreign);
  noisemaker::graph::ResourceArenaTestAccess::retire(arena, foreign);
  REQUIRE(&arena.require("route") == &resource);
}

TEST(graph_resource_repeated_replacement_is_bounded_after_retirement) {
  noisemaker::graph::ResourceArena arena;
  for (std::size_t index = 0; index < 256U; ++index) {
    noisemaker::graph::ResourceArenaTestAccess::allocate(
        arena, "route", 1U, 1U, noisemaker::TextureFormat::rgba16f,
        noisemaker::graph::ResourceLifetime::transient);
    REQUIRE(arena.size() == 1U);
  }
}

TEST(graph_resource_missing_route_is_deterministic) {
  noisemaker::graph::ResourceArena arena;
  REQUIRE_THROWS_AS(arena.require("missing"), std::out_of_range);
}

TEST(graph_resource_rejected_allocation_does_not_publish_partial_resource) {
  noisemaker::graph::ResourceArena arena;
  REQUIRE_THROWS_AS(noisemaker::graph::ResourceArenaTestAccess::allocate(
                        arena, "too-large", 4097U, 4096U,
                        noisemaker::TextureFormat::rgba16f,
                        noisemaker::graph::ResourceLifetime::transient),
                    std::overflow_error);
  REQUIRE(arena.size() == 0U);
  REQUIRE_THROWS_AS(noisemaker::graph::ResourceArenaTestAccess::allocate(
                        arena, "", 1U, 1U,
                        noisemaker::TextureFormat::rgba16f,
                        noisemaker::graph::ResourceLifetime::transient),
                    std::invalid_argument);
  REQUIRE(arena.size() == 0U);
}
