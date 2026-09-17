#include "test_harness.hpp"

#include "noisemaker/graph/executor.hpp"
#include "noisemaker/graph/iteration.hpp"
#include "noisemaker/renderer.hpp"

#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// Exercises the wiring landed in GraphExecutor::execute() for
// iteration::compute_iteration_groups / run_iterated_group -- see
// docs/port-engineering/iteration-group-resource-lifetime.md for the design.
//
// Every scenario here starts from a REAL, DSL-compiled, admitted plan (never
// a hand-forged admission) and mutates only the plan-level metadata
// (EffectDefinition::iterated/loop_role, and an injected `iterationCount`
// step parameter) that iteration::compute_iteration_groups itself reads --
// exactly the same "mutate a compiled plan, then reauthenticate" technique
// test_graph_features.cpp already uses for its own admission-tampering
// tests. This proves the iterated-group EXECUTION path -- the N-iteration
// loop, per-iteration frame/time/deltaTime, and multi-step loop-region
// grouping -- dispatches through the real synth/perlin, filter/invert, and
// filter/highPass kernels unmodified.
//
// What this file deliberately does NOT attempt: exercising particle-state
// (`global_xyz`/...) or `global_accum` ROUTING, step-scoped persistent
// SCRATCH state across iterations, or `selfTex`/`feedback`. All four require
// a pass whose OWN admitted route name literally matches one of those
// reserved tokens or a particle-state pattern -- and every currently
// admitted program's sampler/output ABI is SHA-256-pinned
// (binding_abi_sha256, re-derived from admission.samplers/uniforms/outputs
// against the generated canonical route table) against its real GLSL
// route names, so renaming a real kernel's own route to "global_xyz" or
// "selfTex" for a test would simply fail authentication, not exercise the
// code differently. Those four mechanics have no real kernel to drive them
// through yet, precisely the gap Family B/C/D/E is meant to close; this is
// the same honest limitation iteration.hpp's own doc comment and
// test_graph_iteration.cpp's header already state for the pure-grouping
// tests.
namespace {

using namespace noisemaker::graph;
using namespace noisemaker;

constexpr std::string_view kPerlinSource =
    "search synth\n"
    "perlin().write(o0)\n"
    "render(o0)\n";

// perlin() is a generator (the DSL compiler requires a generator to begin
// its chain -- it cannot be piped into), so it runs as an ordinary,
// non-iterated step BEFORE the loop region; invert()/highPass() form the
// loop itself, fed perlin()'s real (non-null) output as `group_input` --
// renderer.js:858-865 requires one to seed `global_accum` from, exactly like
// this port's own run_iterated_group.
constexpr std::string_view kLoopRegionSource =
    "search synth, filter\n"
    "perlin().invert().highPass().write(o0)\n"
    "render(o0)\n";

ExecutionInputs options(std::size_t width, std::size_t height, double time, double seed) {
  ExecutionInputs result;
  result.width = width;
  result.height = height;
  result.time = time;
  result.frame = 0;
  result.seed = seed;
  result.delta_time = 0.0;
  return result;
}

PlanEffectSnapshot& snapshot_for(ExecutionPlan& plan, std::string_view effect_id) {
  for (auto& snapshot : plan.effects) {
    if (snapshot.definition.id == effect_id) return snapshot;
  }
  throw std::logic_error("test effect snapshot not found");
}

EffectStep& effect_step(ExecutionPlan& plan, std::string_view effect_id) {
  for (auto& chain : plan.chains) {
    for (auto& variant : chain.steps) {
      auto* step = std::get_if<EffectStep>(&variant);
      if (step != nullptr && step->effect.id == effect_id) return *step;
    }
  }
  throw std::logic_error("test effect step not found");
}

// Every mutation in this file only ever touches EffectDefinition fields
// (iterated/loop_role) that live on PlanEffectSnapshot::definition, never a
// PassAdmission field -- so the EffectStep's own retained admission copies
// (compared against the snapshot's by validate_plan_before_allocation) never
// drift, and only snapshot_sha256/plan_payload_sha256 need recomputing.
void reauthenticate(ExecutionPlan& plan) {
  for (auto& snapshot : plan.effects) {
    snapshot.snapshot_sha256 = detail::snapshot_sha256(snapshot);
  }
  plan.provenance.plan_payload_sha256 = detail::plan_payload_sha256(plan);
}

// Injects `iterationCount` as a bound step parameter -- mirroring how a real
// iterated effect's own catalog default would arrive on `step.params`, since
// GraphExecutor reads it with the same plain `parameter(step,
// "iterationCount")` lookup regardless of where the binding came from.
void set_iteration_count(EffectStep& step, double value) {
  for (auto& binding : step.params) {
    if (binding.name == "iterationCount") {
      binding.value = PlanValue::number_value(value);
      return;
    }
  }
  step.params.push_back({"iterationCount", PlanValue::number_value(value)});
}

// The exact per-iteration ExecutionInputs run_iterated_group computes for
// iteration `i` of `n` (iteration.hpp's own ported wrap01/kIterationDeltaTime
// -- this calls the SAME primitives the implementation does, not a
// reimplementation of the arithmetic, so this test asserts the wiring uses
// them, not that the formula itself is right; the formula's own unit tests
// already live in test_graph_iteration.cpp).
ExecutionInputs iteration_inputs_at(const ExecutionInputs& base, double n, std::size_t i) {
  ExecutionInputs result = base;
  result.frame = static_cast<std::uint32_t>(i);
  result.delta_time = iteration::kIterationDeltaTime;
  result.time = iteration::wrap01(base.time - (n - 1.0 - static_cast<double>(i)) * iteration::kIterationDeltaTime);
  return result;
}

}  // namespace

TEST(iterated_group_of_a_single_real_pass_runs_n_times_and_matches_the_last_iteration) {
  Renderer renderer;

  for (const double iteration_count : {1.0, 3.0, 7.0}) {
    auto plan = renderer.compile(kPerlinSource, "iterated-perlin.dsl");
    snapshot_for(plan, "synth/perlin").definition.iterated = true;
    set_iteration_count(effect_step(plan, "synth/perlin"), iteration_count);
    reauthenticate(plan);

    const auto base_inputs = options(9U, 6U, 0.37, 5.0);
    const auto result = renderer.render(plan, base_inputs);
    REQUIRE(result.pass_count() == static_cast<std::size_t>(iteration_count));
    REQUIRE(result.width() == 9U);
    REQUIRE(result.height() == 6U);

    // perlin()'s own GLSL reads both `time` and `seed` (sources/synth/perlin/
    // perlin.glsl: `uniform float time; uniform int seed;` -- the gradient
    // angle animates with time). Iteration i = n-1 (the group's LAST
    // iteration -- the only one whose result survives, since a single-step
    // group with no persistent scratch re-feeds the group's own original
    // input every iteration, exactly like renderer.js's `stepInput =
    // groupInput` reset at the top of every outer loop turn) always computes
    // `time = wrap01(base.time - 0*dt) = wrap01(base.time)` regardless of N
    // -- so the direct comparison target uses frame = N-1 (the one field
    // that DOES vary with N) at that same wrapped time.
    const auto n = static_cast<std::size_t>(iteration_count);
    const auto expected_inputs = iteration_inputs_at(base_inputs, iteration_count, n - 1U);
    auto direct_plan = renderer.compile(kPerlinSource, "direct-perlin.dsl");
    const auto direct = renderer.render(direct_plan, expected_inputs);
    REQUIRE(direct.pass_count() == 1U);
    REQUIRE(result.to_rgba8() == direct.to_rgba8());
  }
}

TEST(iterated_group_output_tracks_the_base_time_it_was_given) {
  // Same mechanism as above, at a fixed N, with two different base `time`
  // values -- confirms the iterated path threads the CALLER's `inputs.time`
  // through (via wrap01(base.time - 0*dt) at the last iteration), not a
  // stale or hardcoded value.
  Renderer renderer;
  constexpr double kIterationCount = 4.0;

  auto make_result = [&](double time) {
    auto plan = renderer.compile(kPerlinSource, "iterated-perlin-time.dsl");
    snapshot_for(plan, "synth/perlin").definition.iterated = true;
    set_iteration_count(effect_step(plan, "synth/perlin"), kIterationCount);
    reauthenticate(plan);
    return renderer.render(plan, options(8U, 5U, time, 11.0));
  };

  const auto low = make_result(0.05);
  const auto high = make_result(0.85);
  REQUIRE(low.to_rgba8() != high.to_rgba8());

  auto direct_plan = renderer.compile(kPerlinSource, "direct-perlin-time.dsl");
  const auto expected_high =
      iteration_inputs_at(options(8U, 5U, 0.85, 11.0), kIterationCount, 3U);
  const auto direct_high = renderer.render(direct_plan, expected_high);
  REQUIRE(high.to_rgba8() == direct_high.to_rgba8());
}

TEST(iterated_group_with_zero_iterations_clones_the_input_and_runs_no_passes) {
  Renderer renderer;
  auto plan = renderer.compile(kPerlinSource, "iterated-perlin-zero.dsl");
  snapshot_for(plan, "synth/perlin").definition.iterated = true;
  set_iteration_count(effect_step(plan, "synth/perlin"), 0.0);
  reauthenticate(plan);

  const auto inputs = options(6U, 4U, 0.5, 3.0);
  const auto result = renderer.render(plan, inputs);
  REQUIRE(result.pass_count() == 0U);
  REQUIRE(result.width() == 6U);
  REQUIRE(result.height() == 4U);
  // synth/perlin is a generator (declares no `inputTex` sampler route), so
  // the group opens the chain with no input surface to clone -- the zero-
  // iteration path falls back to a cleared render-extent surface
  // (renderer.js's own `zeroIterationGroupOutput` volume/image branch,
  // restricted here to the plain-Surface case). Every pixel must be exactly
  // the authority's `clear()` value: transparent black.
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == 6U * 4U * 4U);
  for (const auto byte : bytes) REQUIRE(byte == 0U);
}

TEST(iterated_loop_region_sweeps_two_real_steps_into_one_group) {
  // perlin() runs first (a generator must begin its chain -- the DSL
  // compiler rejects piping into one), giving the loop region a real,
  // non-null `group_input`; invert()/highPass() are marked as the loop
  // region itself (renderer.js/iteration.js's loopBegin/loopEnd -- iteration
  // group membership is driven purely by EffectDefinition::loop_role/
  // iterated metadata, never by a pass's own input/output route names, so
  // marking these two real, unmodified-ABI steps this way is a faithful
  // simulation of a real loop-region chain). Neither references
  // `global_accum` in its own pass inputs/outputs, so this does not exercise
  // global_accum ROUTING (see the file-level comment on that gap) -- it
  // exercises everything else a loop region needs: compute_iteration_groups
  // recognizing a multi-step region, run_iterated_group seeding (and safely
  // discarding, unused) global_accum, and both real kernels dispatching
  // correctly N times each with the same per-iteration inputs.
  Renderer renderer;
  constexpr double kIterationCount = 3.0;

  auto plan = renderer.compile(kLoopRegionSource, "iterated-loop.dsl");
  snapshot_for(plan, "filter/invert").definition.loop_role = "begin";
  snapshot_for(plan, "filter/highPass").definition.loop_role = "end";
  set_iteration_count(effect_step(plan, "filter/invert"), kIterationCount);
  reauthenticate(plan);

  const auto base_inputs = options(7U, 5U, 0.6, 2.0);
  const auto result = renderer.render(plan, base_inputs);
  // perlin() (outside the loop region) contributes one pass; the loop
  // region contributes invert()'s 1 pass + highPass()'s 3 passes
  // (blurH/blurV/combine) per iteration.
  REQUIRE(result.pass_count() == 1U + 4U * static_cast<std::size_t>(kIterationCount));

  // Same "last iteration wins" reasoning as the single-step tests, applied
  // to the whole loop region: with no cross-iteration state, N repeats of
  // the identical 2-kernel pipeline collapse to running it once at the last
  // iteration's inputs. perlin() sits OUTSIDE the loop and never sees its
  // per-iteration override -- but at the boundary iteration i = N-1 the
  // loop's own `time`/`seed` are unchanged from `base_inputs` (only `frame`
  // and `delta_time` differ, and neither perlin(), invert(), nor highPass()
  // reads either), so re-running the WHOLE source non-iteratively at
  // `expected_inputs` reproduces perlin()'s real output too, without a
  // separate seeded comparison plan.
  const auto expected_inputs = iteration_inputs_at(base_inputs, kIterationCount, 2U);
  auto direct_plan = renderer.compile(kLoopRegionSource, "direct-loop.dsl");
  const auto direct = renderer.render(direct_plan, expected_inputs);
  REQUIRE(direct.pass_count() == 5U);
  REQUIRE(result.to_rgba8() == direct.to_rgba8());
}

TEST(iterated_loop_region_is_recognized_by_compute_iteration_groups_directly) {
  // A grouping-only companion to the end-to-end test above -- confirms the
  // exact group shape iteration::compute_iteration_groups produces for this
  // plan, the same way test_graph_iteration.cpp's pure tests already check
  // hand-built plans, just against a real DSL-compiled one here.
  Renderer renderer;
  auto plan = renderer.compile(kLoopRegionSource, "iterated-loop-groups.dsl");
  snapshot_for(plan, "filter/invert").definition.loop_role = "begin";
  snapshot_for(plan, "filter/highPass").definition.loop_role = "end";
  reauthenticate(plan);

  REQUIRE(plan.chains.size() == 1U);
  const auto groups = iteration::compute_iteration_groups(plan, plan.chains.front());
  // perlin() (ordinary, non-iterated) | [invert, highPass] (the loop
  // region) | write(o0) (its own boundary group).
  REQUIRE(groups.size() == 3U);
  REQUIRE(!groups[0].iterated);
  REQUIRE(groups[0].step_indices.size() == 1U);
  REQUIRE(groups[1].iterated);
  REQUIRE(groups[1].loop);
  REQUIRE(groups[1].step_indices.size() == 2U);
  REQUIRE(!groups[2].iterated);
  REQUIRE(groups[2].step_indices.size() == 1U);
}
