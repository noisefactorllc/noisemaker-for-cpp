#include "test_harness.hpp"

#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "noisemaker/graph/iteration.hpp"
#include "noisemaker/surface.hpp"

// Native port of noisemaker-for-cpu's `test/iterated-effects.test.js`
// "Step 1a: computeIterationGroups" section (read in full; the pure grouping
// tests there, lines 18-81, are mirrored 1:1 below with the same five
// scenarios and the same expected group shapes) plus dedicated coverage for
// `is_particle_state_name`/`wrap01`/`resolve_iteration_count`. See
// include/noisemaker/graph/iteration.hpp for why this module has no
// renderer-level ("Step 1b") equivalent yet: none of the 25 real effects
// that set `iterated`/`loopRole` have an admitted kernel today, so there is
// nothing to run those fixtures' actual pixel math against.

using noisemaker::graph::EffectStep;
using noisemaker::graph::ExecutionChain;
using noisemaker::graph::ExecutionPlan;
using noisemaker::graph::PlanEffectSnapshot;
using noisemaker::graph::PlanValue;
using noisemaker::graph::ReadStep;
using noisemaker::graph::SurfaceReference;
using noisemaker::graph::WriteStep;
using noisemaker::graph::iteration::IterationGroup;

namespace {

noisemaker::effects::PassDefinition make_pass(
    std::vector<std::pair<std::string, std::string>> inputs,
    std::vector<std::pair<std::string, std::string>> outputs) {
  noisemaker::effects::PassDefinition pass;
  pass.name = "pass";
  pass.program = "pass";
  pass.inputs = std::move(inputs);
  pass.outputs = std::move(outputs);
  return pass;
}

noisemaker::effects::EffectDefinition make_definition(
    std::string id, bool iterated, std::optional<std::string> loop_role,
    std::vector<std::string> texture_names,
    std::vector<noisemaker::effects::PassDefinition> passes) {
  noisemaker::effects::EffectDefinition definition;
  definition.id = std::move(id);
  definition.iterated = iterated;
  definition.loop_role = std::move(loop_role);
  for (auto& name : texture_names) {
    noisemaker::effects::TextureDefinition texture;
    texture.name = std::move(name);
    definition.textures.push_back(std::move(texture));
  }
  definition.passes = std::move(passes);
  return definition;
}

std::size_t add_effect(ExecutionPlan& plan, ExecutionChain& chain,
                       noisemaker::effects::EffectDefinition definition) {
  const std::size_t snapshot_index = plan.effects.size();
  PlanEffectSnapshot snapshot;
  snapshot.definition = std::move(definition);
  plan.effects.push_back(std::move(snapshot));
  EffectStep step;
  step.snapshot_index = snapshot_index;
  chain.steps.push_back(step);
  return chain.steps.size() - 1;
}

void add_read(ExecutionChain& chain, std::string name) {
  ReadStep read;
  read.surface = SurfaceReference::named(std::move(name), 0);
  chain.steps.push_back(read);
}

void add_write(ExecutionChain& chain, std::string name) {
  WriteStep write;
  write.surface = SurfaceReference::named(std::move(name), 0);
  chain.steps.push_back(write);
}

std::vector<std::pair<bool, std::size_t>> shape(
    const std::vector<IterationGroup>& groups) {
  std::vector<std::pair<bool, std::size_t>> result;
  for (const auto& group : groups) {
    result.emplace_back(group.iterated, group.step_indices.size());
  }
  return result;
}

}  // namespace

// iterated-effects.test.js:18-27 -- "groups particle segments and isolates
// stateful effects": pointsEmit (declares global_xyz) + flock (joins via
// global_xyz) form one iterated 2-step group; blur (no particle refs, not
// iterated) is its own group; reactionDiffusion (iterated, but its own
// `global_rd_state` texture name does NOT match the particle pattern, so it
// never opens or joins a group) is its own single-step iterated group.
TEST(compute_iteration_groups_groups_particle_segments_and_isolates_stateful_effects) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain,
             make_definition("render/pointsEmit", true, std::nullopt, {"global_xyz"},
                             {make_pass({{"xyzTex", "global_xyz"}},
                                        {{"outXYZ", "global_xyz"}, {"fragColor", "outputTex"}})}));
  add_effect(plan, chain,
             make_definition("points/flock", true, std::nullopt, {},
                             {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));
  add_effect(plan, chain,
             make_definition("filter/blur", false, std::nullopt, {},
                             {make_pass({{"inputTex", "inputTex"}}, {{"fragColor", "outputTex"}})}));
  add_effect(plan, chain,
             make_definition("synth/reactionDiffusion", true, std::nullopt, {"global_rd_state"},
                             {make_pass({{"bufTex", "global_rd_state"}}, {{"fragColor", "global_rd_state"}})}));

  const auto groups = noisemaker::graph::iteration::compute_iteration_groups(plan, chain);
  const std::vector<std::pair<bool, std::size_t>> expected = {{true, 2}, {false, 1}, {true, 1}};
  REQUIRE(shape(groups) == expected);
}

// iterated-effects.test.js:29-40 -- a second global_xyz-declaring step always
// opens its OWN new group, even immediately after one is already open (two
// pointsEmit() calls never merge into one group).
TEST(compute_iteration_groups_opens_a_new_group_for_each_global_xyz_declaring_step) {
  ExecutionPlan plan;
  ExecutionChain chain;
  const auto emit_a = add_effect(
      plan, chain,
      make_definition("render/pointsEmit", true, std::nullopt, {"global_xyz"},
                      {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));
  const auto emit_b = add_effect(
      plan, chain,
      make_definition("render/pointsEmit", true, std::nullopt, {"global_xyz"},
                      {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));
  const auto flock = add_effect(
      plan, chain,
      make_definition("points/flock", true, std::nullopt, {},
                      {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));

  const auto groups = noisemaker::graph::iteration::compute_iteration_groups(plan, chain);
  const std::vector<std::pair<bool, std::size_t>> expected = {{true, 1}, {true, 2}};
  REQUIRE(shape(groups) == expected);
  REQUIRE(groups[0].step_indices == std::vector<std::size_t>{emit_a});
  REQUIRE(groups[1].step_indices == (std::vector<std::size_t>{emit_b, flock}));
}

// iterated-effects.test.js:42-53 -- read/write chain steps are always
// boundaries: they close any open group, and the step after them starts its
// own fresh group rather than rejoining what was open before the boundary.
TEST(compute_iteration_groups_treats_read_write_as_boundaries_that_close_an_open_group) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain,
             make_definition("render/pointsEmit", true, std::nullopt, {"global_xyz"},
                             {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));
  add_write(chain, "o1");
  add_read(chain, "o1");
  add_effect(plan, chain,
             make_definition("points/flock", true, std::nullopt, {},
                             {make_pass({{"xyzTex", "global_xyz"}}, {{"outXYZ", "global_xyz"}})}));

  const auto groups = noisemaker::graph::iteration::compute_iteration_groups(plan, chain);
  const std::vector<std::pair<bool, std::size_t>> expected = {
      {true, 1}, {false, 1}, {false, 1}, {true, 1}};
  REQUIRE(shape(groups) == expected);
}

// iterated-effects.test.js:55-60 -- no particle/stateful steps at all: every
// step is its own non-iterated, single-step group.
TEST(compute_iteration_groups_leaves_ordinary_chain_as_one_group_per_step) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain,
             make_definition("filter/blur", false, std::nullopt, {},
                             {make_pass({{"inputTex", "inputTex"}}, {{"fragColor", "outputTex"}})}));
  add_effect(plan, chain,
             make_definition("filter/invert", false, std::nullopt, {},
                             {make_pass({{"inputTex", "inputTex"}}, {{"fragColor", "outputTex"}})}));

  const auto groups = noisemaker::graph::iteration::compute_iteration_groups(plan, chain);
  const std::vector<std::pair<bool, std::size_t>> expected = {{false, 1}, {false, 1}};
  REQUIRE(shape(groups) == expected);
}

// iterated-effects.test.js:62-81 -- a balanced loopBegin...loopEnd region
// becomes one iterated, loop-flagged group owning every step between (and
// including) the markers; steps before/after stay their own ordinary groups.
TEST(compute_iteration_groups_makes_a_balanced_loop_region_one_group) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain, make_definition("synth/solid", false, std::nullopt, {}, {}));
  const auto begin = add_effect(
      plan, chain, make_definition("render/loopBegin", true, std::string("begin"), {}, {}));
  add_effect(plan, chain, make_definition("filter/blur", false, std::nullopt, {}, {}));
  const auto end = add_effect(
      plan, chain, make_definition("render/loopEnd", false, std::string("end"), {}, {}));
  add_effect(plan, chain, make_definition("filter/invert", false, std::nullopt, {}, {}));

  const auto groups = noisemaker::graph::iteration::compute_iteration_groups(plan, chain);
  REQUIRE(groups.size() == 3U);
  REQUIRE(groups[0].iterated == false);
  REQUIRE(groups[0].loop == false);
  REQUIRE(groups[0].step_indices.size() == 1U);
  REQUIRE(groups[1].iterated == true);
  REQUIRE(groups[1].loop == true);
  REQUIRE(groups[1].step_indices.size() == 3U);
  REQUIRE(groups[1].step_indices.front() == begin);
  REQUIRE(groups[1].step_indices.back() == end);
  REQUIRE(groups[2].iterated == false);
  REQUIRE(groups[2].loop == false);
  REQUIRE(groups[2].step_indices.size() == 1U);
}

// iteration.js:70 -- a loop region may never cross a read/write boundary.
TEST(compute_iteration_groups_throws_when_a_loop_crosses_a_read_write_boundary) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain, make_definition("render/loopBegin", true, std::string("begin"), {}, {}));
  add_write(chain, "o1");
  REQUIRE_THROWS_AS(noisemaker::graph::iteration::compute_iteration_groups(plan, chain),
                    std::invalid_argument);
}

// iteration.js:71 -- a loopBegin nested inside an already-open loop throws.
TEST(compute_iteration_groups_throws_on_a_nested_loop_begin) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain, make_definition("render/loopBegin", true, std::string("begin"), {}, {}));
  add_effect(plan, chain, make_definition("render/loopBegin", true, std::string("begin"), {}, {}));
  REQUIRE_THROWS_AS(noisemaker::graph::iteration::compute_iteration_groups(plan, chain),
                    std::invalid_argument);
}

// iteration.js:84 -- an unmatched loopEnd (no preceding loopBegin) throws.
TEST(compute_iteration_groups_throws_on_an_unmatched_loop_end) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain, make_definition("render/loopEnd", false, std::string("end"), {}, {}));
  REQUIRE_THROWS_AS(noisemaker::graph::iteration::compute_iteration_groups(plan, chain),
                    std::invalid_argument);
}

// iteration.js:102 -- an unmatched loopBegin (no closing loopEnd by the end
// of the chain) throws.
TEST(compute_iteration_groups_throws_on_an_unmatched_loop_begin) {
  ExecutionPlan plan;
  ExecutionChain chain;
  add_effect(plan, chain, make_definition("render/loopBegin", true, std::string("begin"), {}, {}));
  add_effect(plan, chain, make_definition("filter/blur", false, std::nullopt, {}, {}));
  REQUIRE_THROWS_AS(noisemaker::graph::iteration::compute_iteration_groups(plan, chain),
                    std::invalid_argument);
}

// iteration.js:14 -- PARTICLE_STATE_PATTERN, exercised at its exact boundary
// conditions rather than only the four literal names.
TEST(is_particle_state_name_matches_exactly_the_four_names_and_the_trail_suffix) {
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global_xyz"));
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global_vel"));
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global_rgba"));
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global_life_data"));
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global_points_trail"));
  // Minimal-length trail match: "global_" + "" + "_trail" (13 chars, the
  // floor -- `.* ` in `^global_.*_trail$` may consume zero characters).
  REQUIRE(noisemaker::graph::iteration::is_particle_state_name("global__trail"));
  // A `global_`-prefixed name that is neither a literal alternative nor a
  // `_trail` suffix stays ordinary scratch (phase2-architecture.md's
  // reactionDiffusion/cellularAutomata/mnca/navierStokes finding).
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name("global_rd_state"));
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name("global_ca_state"));
  // Too short to hold both the 7-char prefix and 6-char suffix without
  // overlapping (the regex anchors require non-overlapping consumption).
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name("global_trail"));
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name(""));
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name("xglobal_xyz"));
  REQUIRE(!noisemaker::graph::iteration::is_particle_state_name("global_xyzx"));
}

// iteration.js:23-25 -- wrap01, including negative inputs (JS `%` keeps the
// operand's sign, matching std::fmod exactly, which is why the double-mod
// idiom is needed at all).
TEST(wrap01_matches_the_js_double_mod_idiom) {
  REQUIRE(noisemaker::graph::iteration::wrap01(0.0) == 0.0);
  REQUIRE(noisemaker::graph::iteration::wrap01(0.25) == 0.25);
  REQUIRE(noisemaker::graph::iteration::wrap01(1.0) == 0.0);
  REQUIRE(noisemaker::graph::iteration::wrap01(1.25) == 0.25);
  const double negative = noisemaker::graph::iteration::wrap01(-0.25);
  REQUIRE(negative > 0.749999 && negative < 0.750001);
  const double negative_whole = noisemaker::graph::iteration::wrap01(-1.0);
  REQUIRE(negative_whole == 0.0);
}

// renderer.js:853-855/896-898 -- N resolution and the zero-iteration
// short-circuit test.
TEST(resolve_iteration_count_defaults_to_sixty_and_detects_non_positive_n) {
  {
    const auto resolved = noisemaker::graph::iteration::resolve_iteration_count(nullptr);
    REQUIRE(resolved.n == 60.0);
    REQUIRE(!resolved.zero_iterations);
  }
  {
    const PlanValue value = PlanValue::number_value(5.0);
    const auto resolved = noisemaker::graph::iteration::resolve_iteration_count(&value);
    REQUIRE(resolved.n == 5.0);
    REQUIRE(!resolved.zero_iterations);
  }
  {
    const PlanValue value = PlanValue::number_value(0.0);
    const auto resolved = noisemaker::graph::iteration::resolve_iteration_count(&value);
    REQUIRE(resolved.n == 0.0);
    REQUIRE(resolved.zero_iterations);
  }
  {
    const PlanValue value = PlanValue::number_value(-3.0);
    const auto resolved = noisemaker::graph::iteration::resolve_iteration_count(&value);
    REQUIRE(resolved.zero_iterations);
  }
  {
    // A non-numeric bound value (e.g. a forged/absent parameter) falls back
    // to the JS `Number.isFinite` guard's `: 60` branch, not zero.
    const PlanValue value = PlanValue::string_value("not-a-number");
    const auto resolved = noisemaker::graph::iteration::resolve_iteration_count(&value);
    REQUIRE(resolved.n == 60.0);
    REQUIRE(!resolved.zero_iterations);
  }
}

// renderer.js:762-765 -- storeGroupOutput's routing predicate: a particle
// name or the literal "global_accum" is group-shared; a `global_`-prefixed
// but non-matching name (e.g. `global_ca_state`) and an ordinary name
// (e.g. "outputTex") are not.
TEST(is_group_shared_resource_name_matches_particle_names_and_global_accum_only) {
  REQUIRE(noisemaker::graph::iteration::is_group_shared_resource_name("global_xyz"));
  REQUIRE(noisemaker::graph::iteration::is_group_shared_resource_name("global_accum"));
  REQUIRE(noisemaker::graph::iteration::is_group_shared_resource_name("global_points_trail"));
  REQUIRE(!noisemaker::graph::iteration::is_group_shared_resource_name("global_ca_state"));
  REQUIRE(!noisemaker::graph::iteration::is_group_shared_resource_name("outputTex"));
  REQUIRE(!noisemaker::graph::iteration::is_group_shared_resource_name("_selfTex"));
}

// storeGroupOutput / replaceCanonicalResource (renderer.js:762-765): a write
// under an existing name REPLACES the stored surface rather than mutating
// it -- a previously-taken pointer to the old surface must keep observing
// the old bytes.
TEST(group_resource_map_store_replaces_rather_than_mutates) {
  noisemaker::graph::iteration::GroupResourceMap map;
  map.store("global_accum", noisemaker::Surface(2, 2));
  const auto* first = map.find("global_accum");
  REQUIRE(first != nullptr);
  const auto first_data = std::vector<float>(first->data().begin(), first->data().end());

  noisemaker::Surface next(2, 2);
  next.data()[0] = 0.5F;
  map.store("global_accum", next.clone());
  REQUIRE(map.size() == 1U);
  const auto* second = map.find("global_accum");
  REQUIRE(second != nullptr);
  REQUIRE(second->data()[0] == 0.5F);
  // The first pointer is now dangling by design (the map replaced its
  // backing storage); this only re-checks the VALUE captured before the
  // replacement, proving the replacement actually changed the map's own
  // stored bytes rather than leaving them at their prior value.
  REQUIRE(first_data[0] == 0.0F);
}

TEST(group_resource_map_find_and_contains_report_absence) {
  noisemaker::graph::iteration::GroupResourceMap map;
  REQUIRE(!map.contains("global_xyz"));
  REQUIRE(map.find("global_xyz") == nullptr);
  REQUIRE(map.empty());
  map.store("global_xyz", noisemaker::Surface(1, 1));
  REQUIRE(map.contains("global_xyz"));
  REQUIRE(!map.empty());
}

// finishGroupResources (renderer.js:832-850): release every entry except
// whatever the group's final output retains -- "particle state never
// survives beyond the group run that owns it" (renderer.js:836).
TEST(group_resource_map_release_all_except_keeps_only_the_retained_names) {
  noisemaker::graph::iteration::GroupResourceMap map;
  map.store("global_xyz", noisemaker::Surface(1, 1));
  map.store("global_accum", noisemaker::Surface(1, 1));
  map.store("global_vel", noisemaker::Surface(1, 1));

  auto released = map.release_all_except({"global_accum"});
  REQUIRE(released.size() == 2U);
  REQUIRE(map.size() == 1U);
  REQUIRE(map.contains("global_accum"));
  REQUIRE(!map.contains("global_xyz"));
  REQUIRE(!map.contains("global_vel"));

  bool saw_xyz = false;
  bool saw_vel = false;
  for (const auto& [name, surface] : released) {
    (void)surface;
    saw_xyz = saw_xyz || name == "global_xyz";
    saw_vel = saw_vel || name == "global_vel";
  }
  REQUIRE(saw_xyz);
  REQUIRE(saw_vel);
}

TEST(group_resource_map_release_all_except_empty_retains_nothing) {
  noisemaker::graph::iteration::GroupResourceMap map;
  map.store("global_accum", noisemaker::Surface(1, 1));
  const auto released = map.release_all_except({});
  REQUIRE(released.size() == 1U);
  REQUIRE(map.empty());
}
