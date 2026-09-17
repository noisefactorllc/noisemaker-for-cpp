#include "test_harness.hpp"

#include <optional>
#include <stdexcept>
#include <string>

#include "noisemaker/graph/chain_bundle.hpp"

// Native tests for the pure chain-bundle helpers
// (docs/port-engineering/chain-bundle-volume-geometry-threading.md), ported
// against renderer.js at the pinned authority revision (61aa869). Mirrors
// test_graph_iteration.cpp's own approach: these are the parts of Family D
// that are independently testable without a real volume-domain kernel --
// none exist yet (every synth3d/*, filter3d/flow3d effect still refuses
// with missing_backend_program), so GraphExecutor::execute()'s own use of
// these helpers is proven safe for every CURRENTLY admitted (image-domain)
// effect by the required before/after sweep instead, not by a dedicated
// native test here.

using noisemaker::graph::bundle::inherit_volume_size;
using noisemaker::graph::bundle::is_passthrough_output_name;
using noisemaker::graph::bundle::is_volume_domain;
using noisemaker::graph::bundle::requires_output_image;
using noisemaker::graph::bundle::resolve_volume_size;
using noisemaker::graph::bundle::validate_volume_output_shape;

TEST(is_volume_domain_excludes_only_image_and_the_two_loop_roles) {
  REQUIRE(!is_volume_domain("image"));
  REQUIRE(!is_volume_domain("loop-begin"));
  REQUIRE(!is_volume_domain("loop-end"));
  REQUIRE(is_volume_domain("volume-generator"));
  REQUIRE(is_volume_domain("volume-filter"));
  REQUIRE(is_volume_domain("volume-renderer"));
  REQUIRE(is_volume_domain("anything-else"));
}

TEST(is_passthrough_output_name_matches_exactly_the_four_js_cases) {
  REQUIRE(is_passthrough_output_name(""));
  REQUIRE(is_passthrough_output_name("inputTex"));
  REQUIRE(is_passthrough_output_name("inputTex3d"));
  REQUIRE(is_passthrough_output_name("inputGeo"));
  REQUIRE(!is_passthrough_output_name("outputTex3d"));
  REQUIRE(!is_passthrough_output_name("myVolume"));
}

TEST(inherit_volume_size_does_nothing_when_the_step_has_no_volume_size_param) {
  const auto result = inherit_volume_size("synth3d/fractal3d", "volume-generator", false, 64U, 4096U);
  REQUIRE(!result.has_value());
}

TEST(inherit_volume_size_does_nothing_outside_the_three_volume_domains) {
  // Even with a declared volumeSize param and a well-formed input volume,
  // an image/loop-role/other domain never inherits (renderer.js:110).
  REQUIRE(!inherit_volume_size("x", "image", true, 64U, 4096U).has_value());
  REQUIRE(!inherit_volume_size("x", "loop-begin", true, 64U, 4096U).has_value());
  REQUIRE(!inherit_volume_size("x", "loop-end", true, 64U, 4096U).has_value());
}

TEST(inherit_volume_size_overrides_to_the_input_volumes_own_width_for_each_volume_domain) {
  for (const char* domain : {"volume-generator", "volume-filter", "volume-renderer"}) {
    const auto result = inherit_volume_size("synth3d/fractal3d", domain, true, 32U, 1024U);
    REQUIRE(result.has_value());
    REQUIRE(*result == 32.0);
  }
}

TEST(inherit_volume_size_throws_on_a_malformed_n_by_n_squared_atlas) {
  bool threw = false;
  try {
    (void)inherit_volume_size("synth3d/fractal3d", "volume-filter", true, 32U, 999U);
  } catch (const std::invalid_argument& error) {
    threw = true;
    const std::string message = error.what();
    REQUIRE(message.find("synth3d/fractal3d") != std::string::npos);
    REQUIRE(message.find("32x1024") != std::string::npos);
    REQUIRE(message.find("32x999") != std::string::npos);
  }
  REQUIRE(threw);
}

TEST(resolve_volume_size_for_a_generator_ignores_the_input_bundle_entirely) {
  // renderer.js:1053-1055 -- a volume-generator resolves from its own
  // params/produced-volume-width only; the input bundle's own volumeSize
  // (which a generator has no meaningful use for) never wins, even when
  // present.
  REQUIRE(resolve_volume_size("volume-generator", 40.0, 999.0, 80U) == 40.0);
  REQUIRE(resolve_volume_size("volume-generator", std::nullopt, 999.0, 80U) == 80.0);
  REQUIRE(!resolve_volume_size("volume-generator", std::nullopt, 999.0, std::nullopt).has_value());
}

TEST(resolve_volume_size_for_every_other_domain_prefers_the_input_bundle_first) {
  // renderer.js:1187-1189/1322-1324/1468-1470 -- inputBundle.volumeSize ??
  // params.volumeSize ?? volume?.width ?? null, in that order.
  REQUIRE(resolve_volume_size("volume-filter", 40.0, 99.0, 80U) == 99.0);
  REQUIRE(resolve_volume_size("volume-filter", 40.0, std::nullopt, 80U) == 40.0);
  REQUIRE(resolve_volume_size("volume-filter", std::nullopt, std::nullopt, 80U) == 80.0);
  REQUIRE(!resolve_volume_size("volume-filter", std::nullopt, std::nullopt, std::nullopt).has_value());
  REQUIRE(resolve_volume_size("image", std::nullopt, std::nullopt, std::nullopt) == std::nullopt);
}

TEST(validate_volume_output_shape_requires_a_volume_on_every_volume_domain_but_renderer) {
  bool threw = false;
  try {
    validate_volume_output_shape("synth3d/fractal3d", "volume-generator", false, std::nullopt,
                                 std::nullopt, std::nullopt);
  } catch (const std::invalid_argument& error) {
    threw = true;
    REQUIRE(std::string(error.what()) == "synth3d/fractal3d did not produce outputTex3d");
  }
  REQUIRE(threw);

  // volume-renderer is explicitly exempt (renderer.js:1056/1325 -- "domain
  // !== 'volume-renderer'"); image/loop-begin/loop-end aren't isVolumeDomain
  // at all, so they are exempt too, regardless of whether a volume exists.
  validate_volume_output_shape("x", "volume-renderer", false, std::nullopt, std::nullopt, std::nullopt);
  validate_volume_output_shape("x", "image", false, std::nullopt, std::nullopt, std::nullopt);
}

TEST(validate_volume_output_shape_checks_the_n_by_n_squared_atlas_on_generator_and_filter_only) {
  // A well-formed 16x256 atlas passes for both checked domains.
  validate_volume_output_shape("x", "volume-generator", true, 16U, 256U, 16.0);
  validate_volume_output_shape("x", "volume-filter", true, 16U, 256U, 16.0);
  // volume-renderer never shape-checks its produced volume (renderer.js:1057
  // only lists generator/filter).
  validate_volume_output_shape("x", "volume-renderer", true, 16U, 999U, 16.0);

  bool threw = false;
  try {
    validate_volume_output_shape("synth3d/noise3d", "volume-generator", true, 16U, 999U, 16.0);
  } catch (const std::invalid_argument& error) {
    threw = true;
    REQUIRE(std::string(error.what()) ==
            "synth3d/noise3d volume atlas expected 16x256, received 16x999");
  }
  REQUIRE(threw);
}

TEST(requires_output_image_exempts_only_generator_and_filter) {
  REQUIRE(!requires_output_image("volume-generator"));
  REQUIRE(!requires_output_image("volume-filter"));
  REQUIRE(requires_output_image("volume-renderer"));
  REQUIRE(requires_output_image("image"));
  REQUIRE(requires_output_image("loop-begin"));
  REQUIRE(requires_output_image("loop-end"));
}
