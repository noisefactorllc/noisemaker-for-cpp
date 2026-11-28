#include "test_harness.hpp"

#include "noisemaker/graph/executor.hpp"
#include "noisemaker/graph/iteration.hpp"
#include "noisemaker/renderer.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
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

TEST(iterated_group_with_zero_iterations_clears_without_input_and_runs_no_passes) {
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

TEST(iterated_group_with_zero_iterations_clones_incoming_image_and_runs_no_passes) {
  Renderer renderer;
  auto plan = renderer.compile(kLoopRegionSource, "iterated-loop-zero.dsl");
  snapshot_for(plan, "filter/invert").definition.loop_role = "begin";
  snapshot_for(plan, "filter/highPass").definition.loop_role = "end";
  set_iteration_count(effect_step(plan, "filter/invert"), 0.0);
  reauthenticate(plan);

  const auto inputs = options(7U, 5U, 0.6, 2.0);
  const auto incoming = renderer.render(kPerlinSource, inputs);
  const auto result = renderer.render(plan, inputs);
  // Only perlin runs. The loop returns a byte-exact clone of that incoming
  // image; neither invert nor any of highPass's three passes runs.
  REQUIRE(incoming.pass_count() == 1U);
  REQUIRE(result.pass_count() == incoming.pass_count());
  REQUIRE(result.width() == incoming.width());
  REQUIRE(result.height() == incoming.height());
  const auto original = incoming.surface().data();
  const auto cloned = result.surface().data();
  REQUIRE(original.size() == cloned.size());
  REQUIRE(detail::sha256(std::string_view(
              reinterpret_cast<const char*>(original.data()), original.size_bytes())) ==
          detail::sha256(std::string_view(
              reinterpret_cast<const char*>(cloned.data()), cloned.size_bytes())));
  REQUIRE(result.to_rgba8() == incoming.to_rgba8());
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

// filter/motionBlur is the first REAL iterated effect whose kernels are all
// vendored (corpus expansion): pass `main` reads the declared scratch texture
// `_selfTex` BEFORE pass `feedback` (a `copy`) writes it, and that trailing
// feedback pass -- not `main` -- is the step's last pass. Both halves of the
// JS authority's group-step contract are therefore load-bearing here:
//   * ensureGroupScratchResources zero-fills every declared texture before the
//     first iteration, so the plan dry run must not refuse `_selfTex` as
//     read-before-write;
//   * runGroupStepIterationSync returns `state.resources.get('outputTex') ??
//     lastOutput`, so the published image is `main`'s rgba16f `outputTex`,
//     not the rgba8unorm `_selfTex` copy the last pass wrote.
// The digest is the JS authority's own float32 surface for this exact case
// (tools/parity/sweep.py case `filter__motionBlur__default`: 17x11, time 0.25,
// every parameter at its declared default, iterationCount 60), which the
// executor matched byte-for-byte only once both halves were ported.
TEST(iterated_motion_blur_reads_its_scratch_self_texture_and_publishes_output_tex) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search filter, synth\nsolid(color: #3a7).motionBlur().write(o0)\nrender(o0)\n",
      "motion-blur.dsl");
  auto inputs = options(17U, 11U, 0.25, 2360121984.0);
  const auto result = renderer.render(plan, inputs);
  // solid() once, then motionBlur's two passes for each of 60 iterations.
  REQUIRE(result.pass_count() == 1U + 2U * 60U);
  const auto lanes = result.surface().data();
  const std::string bytes(reinterpret_cast<const char*>(lanes.data()), lanes.size() * sizeof(float));
  REQUIRE(detail::sha256(bytes) ==
          "9b5ad5becb52b6027f117de2980cbc7eb8dc58c7868c2c4e457f86f6a0ff266b");
  // The rgba16f outputTex quantization of 0x33/255, not the rgba8unorm value.
  REQUIRE(lanes[0] == 0.199951171875F);
}

TEST(iterated_reaction_diffusion_does_not_multiply_pass_repeats_by_group_iterations) {
  // noisemaker-for-cpu 390071fa078f: eight simulation passes plus one output
  // pass, independently rendered at 17x11, time 0.25, seed 2334197866.
  Renderer renderer;
  for (const int count : {0, 1, 3, 60}) {
    const std::string source =
        "search synth\n"
        "reactionDiffusion(tex: none, zoom: 8, smoothing: 1, speed: 100, "
        "resetState: false, seed: 1, sourceF: 0, feed: 70, sourceK: 0, kill: 67, "
        "sourceR1: 0, rate1: 92, sourceR2: 0, rate2: 22, iterations: 8, "
        "weight: 0, inputIntensity: 0, iterationCount: " + std::to_string(count) +
        ").write(o0)\nrender(o0)\n";
    const auto result = renderer.render(
        source, options(17U, 11U, 0.25, 2334197866.0), "reaction-diffusion-repeat.dsl");
    REQUIRE(result.pass_count() == (count == 0 ? 0U : 9U));
    const auto rgba = result.to_rgba8();
    const std::string bytes(reinterpret_cast<const char*>(rgba.data()), rgba.size());
    REQUIRE(detail::sha256(bytes) ==
            (count == 0 ? "13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf"
                        : "e3d8af7a10e82d756fa8ec9570b39f663ae8a5baba7b32f00f379cd73797905d"));
  }
}

namespace {
void require_render_followon_cpu(std::string_view source, std::size_t passes,
                                std::string_view f32_hash, std::string_view rgba8_hash) {
  noisemaker::Renderer renderer;
  const auto result = renderer.render(source, options(9U, 7U, 0.375, 13.0));
  REQUIRE(result.width() == 9U);
  REQUIRE(result.height() == 7U);
  REQUIRE(result.pass_count() == passes);
  std::string raw;
  raw.reserve(result.surface().data().size() * 4U);
  for (const float value : result.surface().data()) {
    const auto word = std::bit_cast<std::uint32_t>(value);
    for (unsigned shift = 0U; shift < 32U; shift += 8U)
      raw.push_back(static_cast<char>((word >> shift) & 0xffU));
  }
  REQUIRE(noisemaker::graph::detail::sha256(raw) == f32_hash);
  const auto rgba8 = result.to_rgba8();
  REQUIRE(noisemaker::graph::detail::sha256(std::string_view(
      reinterpret_cast<const char*>(rgba8.data()), rgba8.size())) == rgba8_hash);
}
}  // namespace

TEST(graph_render_followon_volume_mrt_canvas_matches_cpu) {
  require_render_followon_cpu(
      "search synth3d, render\nnoise3d(volumeSize: 4, seed: 7).render3d().write(o0)\nrender(o0)\n",
      2U,
      "9d995d4bf7ce7c069b977793a46e4b19ad2e3243069c2032edd9edf68c637f55",
      "6748ee26e285f1af4d742013571a61c3c3afde96570f959791452de26e43c7a2");
}

TEST(graph_render_followon_particle_mrt_canvas_matches_cpu) {
  require_render_followon_cpu(
      "search synth, render\ngradient().pointsEmit(stateSize: x64, layout: grid, seed: 7, iterationCount: 1).pointsRender().write(o0)\nrender(o0)\n",
      7U,
      "a9b8015387d6f984bc6d0077f6235e27e7f56df30a954d51a633c7c76b2da099",
      "37d22ab2dd8d9d23ebd2f8f4aca6868e79a6a8d355c8a1330e19849a32cc4adb");
}

TEST(graph_render_followon_animated_particle_input_matches_cpu) {
  require_render_followon_cpu(
      "search synth, render\nperlin(speed: 3, seed: 7).pointsEmit(stateSize: x64, layout: grid, seed: 7, attrition: 1, iterationCount: 3).pointsRender().write(o0)\nrender(o0)\n",
      21U,
      "abefbab45323e8db85ebcd0bed1f1362318a0485009f55cca8b9e27677bdceb2",
      "dc6a17c9570845b5667fe6faa1361f05e471f5ab033213aec9b26acc0aab8849");
}

TEST(graph_render_followon_static_particle_input_matches_cpu) {
  require_render_followon_cpu(
      "search synth, render\nperlin(speed: 0, seed: 7).pointsEmit(stateSize: x64, layout: grid, seed: 7, attrition: 1, iterationCount: 3).pointsRender().write(o0)\nrender(o0)\n",
      19U,
      "abefbab45323e8db85ebcd0bed1f1362318a0485009f55cca8b9e27677bdceb2",
      "dc6a17c9570845b5667fe6faa1361f05e471f5ab033213aec9b26acc0aab8849");
}

TEST(graph_render_followon_zero_particle_iterations_matches_cpu) {
  require_render_followon_cpu(
      "search synth, render\nperlin(speed: 3, seed: 7).pointsEmit(stateSize: x64, layout: grid, seed: 7, iterationCount: 0).pointsRender().write(o0)\nrender(o0)\n",
      1U,
      "99517881ec21d2342638cf4cc94fb2bfe69f33dd6f72a66a41050206b12b2582",
      "424ce4d74dcf9790cb346dab06a9eb8befe40070299b6d3a1abb37d2eaab05ef");
}

TEST(graph_render_followon_animated_group_owner_state_matches_cpu) {
  require_render_followon_cpu(
      "search synth, points, render\nperlin(speed: 3, seed: 7).pointsEmit(stateSize: x64, layout: grid, seed: 7, iterationCount: 1).life(stateSize: 128, iterationCount: 1).pointsRender(density: 1, intensity: 10, inputIntensity: 10).write(o0)\nrender(o0)\n",
      10U,
      "65f663d25a3964304de36ba8b1b7e28ed6c4b3a95f73edc3f47bd846e9e8e839",
      "fd82355d68966e5b433f33c03374485a921bcece6e233cae2820280204b76e26");
}

TEST(graph_render_followon_named_mrt_resolution_keeps_canvas_and_pixel_extents_distinct) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth, synth3d, render\n"
      "gradient().pointsEmit(stateSize: x64, iterationCount: 1).write(o0)\n"
      "noise3d(volumeSize: 4).render3d().write(o1)\nrender(o0)\n");
  const auto inputs = options(9U, 7U, 0.375, 13.0);
  for (const auto& item : std::vector<std::pair<std::string_view, std::pair<std::size_t, std::size_t>>>{
           {"render/pointsEmit", {64U, 64U}}, {"render/render3d", {4U, 16U}}}) {
    const auto& snapshot = snapshot_for(plan, item.first);
    const auto& step = effect_step(plan, item.first);
    const auto& pass = snapshot.definition.passes.front();
    const auto& admission = snapshot.admissions.front();
    REQUIRE(admission.outputs.size() > 1U);
    const BindingMaterializationContext context{
        &inputs, &snapshot.definition, item.second.first, item.second.second};
    const auto bindings = materialize_uniform_bindings(step, admission, pass, context);
    const auto resolution = bindings.get_or<noisemaker::glsl::Vec2>(
        "resolution", noisemaker::glsl::Vec2(-1.0f));
    REQUIRE(noisemaker::float_bits_to_uint(resolution[0]) == 0x41100000U);
    REQUIRE(noisemaker::float_bits_to_uint(resolution[1]) == 0x40e00000U);
    REQUIRE(context.destination_width == item.second.first);
    REQUIRE(context.destination_height == item.second.second);
  }
  const auto& snapshot = snapshot_for(plan, "synth/gradient");
  const auto& step = effect_step(plan, "synth/gradient");
  const BindingMaterializationContext single_context{&inputs, &snapshot.definition, 5U, 3U};
  const auto single = materialize_uniform_bindings(
      step, snapshot.admissions.front(), snapshot.definition.passes.front(), single_context);
  REQUIRE(snapshot.admissions.front().outputs.size() == 1U);
  const auto resolution = single.get_or<noisemaker::glsl::Vec2>(
      "resolution", noisemaker::glsl::Vec2(-1.0f));
  REQUIRE(resolution[0] == 5.0f);
  REQUIRE(resolution[1] == 3.0f);
}

namespace {
void skip_graph_passes(ExecutionPlan& plan, std::string_view effect_id) {
  auto& snapshot = snapshot_for(plan, effect_id);
  auto& step = effect_step(plan, effect_id);
  for (std::size_t i = 0; i < snapshot.definition.passes.size(); ++i) {
    snapshot.definition.passes[i].repeat = effects::Value::number_value(0.0);
    snapshot.admissions[i].authority_pass.repeat = PlanValue::number_value(0.0);
    step.passes[i].authority_pass.repeat = PlanValue::number_value(0.0);
  }
}
}

TEST(graph_publishes_agent_channels_across_ordinary_and_iterated_steps) {
  Renderer renderer;
  const auto options_1px = options(1, 1, 0, 0);
  for (const bool grouped : {false, true}) {
    for (const auto channel : {"inputXyz", "inputVel", "inputRgba"}) {
      auto plan = renderer.compile("search synth, filter\nsolid(color:#f00).invert().blur().write(o0)\n");
      auto& generator = snapshot_for(plan,"synth/solid").definition;
      generator.output_xyz = "outputTex";
      generator.output_rgba = "outputTex";
      auto& invert = snapshot_for(plan,"filter/invert").definition;
      invert.output_velocity = "outputTex";
      auto& reader = snapshot_for(plan,"filter/blur").definition;
      reader.output_tex = channel;
      if (grouped) {
        invert.iterated = true;
        reader.iterated = true;
        set_iteration_count(effect_step(plan,"filter/invert"), 1.0);
        set_iteration_count(effect_step(plan,"filter/blur"), 1.0);
      }
      skip_graph_passes(plan,"filter/blur");
      reauthenticate(plan);
      const auto pixels = renderer.render(plan,options_1px).to_rgba8();
      const std::vector<std::uint8_t> expected = std::string_view(channel) == "inputVel"
          ? std::vector<std::uint8_t>{0,255,255,255} : std::vector<std::uint8_t>{255,0,0,255};
      REQUIRE(pixels == expected);
    }
  }
}

TEST(graph_sizes_shared_and_private_textures_from_current_step_inputs) {
  Renderer renderer;
  for (const bool shared : {false, true}) {
    for (const auto& [route, expected] : std::array<std::pair<std::string, std::size_t>, 5>{
             {{"tex", 6}, {"external", 3}, {"inputTex", 6}, {"outputTex", 2}, {"unknown", 2}}}) {
      auto plan = renderer.compile(
          "search synth, mixer, filter\nsolid().write(o1); solid().blendMode(tex:o1).invert().write(o0)");
      auto& owner = snapshot_for(plan, "mixer/blendMode").definition;
      auto& reader = snapshot_for(plan, "filter/invert").definition;
      effects::TextureDefinition texture;
      texture.name = shared ? "global_shared" : "scratch";
      texture.width.kind = effects::DimensionKind::literal;
      texture.width.literal = 2;
      auto inputs = options(6, 4, 0, 0);
      texture.width.input_override = route == "external" ? "tex" : route;
      if (route == "external") {
        owner.external_texture = "tex";
        inputs.external_textures.push_back({"tex", Surface(3, 1)});
      }
      texture.height.kind = effects::DimensionKind::literal;
      texture.height.literal = 1;
      owner.textures.push_back(texture);
      if (shared) {
        owner.passes.front().storage_textures = {{"store", texture.name}};
        reader.output_tex = texture.name;
      } else {
        owner.output_xyz = texture.name;
        reader.output_tex = "inputXyz";
      }
      skip_graph_passes(plan, "filter/invert");
      reauthenticate(plan);
      const auto result = renderer.render(plan, inputs);
      REQUIRE(result.width() == expected);
      REQUIRE(result.height() == 1U);
    }
  }
}

TEST(graph_installs_shared_storage_in_first_authored_order) {
  Renderer renderer;
  for (const bool grouped : {false,true}) {
    auto plan = renderer.compile("search synth, filter\nsolid().invert().write(o0)\n");
    auto& source = snapshot_for(plan,"synth/solid").definition;
    auto& reader = snapshot_for(plan,"filter/invert").definition;
    effects::TextureDefinition first;
    first.name = "global_z";
    first.width.kind = effects::DimensionKind::literal;
    first.width.literal = 3;
    first.height = first.width;
    first.height.literal = 2;
    auto second = first;
    second.name = "global_a";
    second.width.literal = 1;
    second.width.input_override = first.name;
    source.textures.push_back(first);
    source.textures.push_back(second);
    source.passes.front().storage_textures = {{"z", first.name}, {"a",second.name}};
    reader.output_xyz = first.name;
    reader.output_tex = second.name;
    reader.iterated = grouped;
    set_iteration_count(effect_step(plan,"filter/invert"), 1.0);
    skip_graph_passes(plan,"filter/invert");
    reauthenticate(plan);
    const auto result = renderer.render(plan,options(6,4,0,0));
    REQUIRE(result.width() == 3U);
    REQUIRE(result.height() == 2U);
    for (const auto lane : result.to_rgba8()) REQUIRE(lane == 0U);
  }
}

TEST(graph_fragment_blend_uses_a_step_local_destination) {
  Renderer renderer;
  const auto inputs = options(1,1,0,0);
  for (const bool grouped : {false,true}) {
    auto plan = renderer.compile("search synth, filter\nsolid(color:#f00).invert().write(o0)\n");
    auto& snapshot = snapshot_for(plan,"filter/invert");
    auto& step = effect_step(plan,"filter/invert");
    snapshot.definition.iterated = grouped;
    set_iteration_count(step,1.0);
    auto& blend = snapshot.definition.passes.front().blend.emplace();
    blend.kind = effects::BlendKind::boolean;
    blend.enabled = true;
    auto& authority = snapshot.admissions.front().authority_pass;
    authority.blend_kind = "boolean";
    authority.blend = true;
    step.passes.front().authority_pass = authority;
    reauthenticate(plan);
    const std::vector<std::uint8_t> cyan{0,255,255,255};
    REQUIRE(renderer.render(plan,inputs).to_rgba8() == cyan);
  }
}

TEST(graph_dispatches_declared_fragment_attachments_in_shader_order) {
  Renderer renderer;
  const auto inputs = options(5,3,0,0);
  auto plan = renderer.compile("search synth3d, render\nshape3d(volumeSize:4).render3d().write(o0)\n");
  const auto expected = renderer.render(plan,inputs).to_rgba8();
  auto& snapshot = snapshot_for(plan,"synth3d/shape3d");
  auto& step = effect_step(plan,"synth3d/shape3d");
  bool checked_mrt = false;
  for (std::size_t i=0; i<snapshot.definition.passes.size(); ++i) {
    auto& outputs = snapshot.definition.passes[i].outputs;
    if (snapshot.admissions[i].outputs.size() > 1U) {
      std::reverse(outputs.begin(),outputs.end());
      checked_mrt = true;
    }
    outputs.emplace_back("unwrittenAttachment","unused");
    snapshot.admissions[i].authority_pass.outputs = outputs;
    step.passes[i].authority_pass.outputs = outputs;
  }
  REQUIRE(checked_mrt);
  reauthenticate(plan);
  REQUIRE(renderer.render(plan,inputs).to_rgba8() == expected);
}

TEST(graph_heightmap_terrain_keeps_top_down_frame_proportions_and_colors) {
  // Pinned CPU heightmap-frame-shapes.test.js. Each digest covers the projected
  // UV colors and their orientation as well as the transparent margins.
  struct Case {
    std::size_t width, height;
    int camera_z;
    std::array<std::size_t,4> bounds;
    std::string_view rgba;
  };
  const Case cases[] = {
    {128,128,-40,{20,107,20,107},"9ee2baa98364b62c424366280d4ec679c45fe336d2435909f354d45b79a69ad4"},
    {256,128,-40,{84,171,42,85},"8af4d304770d49e3f104b2aee213b28edc0b6dcff6edd8c050020e155de2a5b5"},
    {128,256,-120,{42,85,84,171},"81ab4ce8a8529ad1fec64e65989856c504791ae75f500fe0f3c29098c80ddb56"},
  };
  Renderer renderer;
  for (const auto& c : cases) {
    const auto source = "search synth, synth3d, render\n"
        "heightmap3d(heightTex: solid(color: #ffffff), tex: testPattern(pattern: uvMap), "
        "volumeSize: x16, heightScale: 1).renderLandscape3d(viewMode: perspective, rotateX: 1.5708, posZ: " +
        std::to_string(c.camera_z) +
        ", bgAlpha: 0, ambient: 1, diffuseIntensity: 0, specularIntensity: 0).write(o0)\nrender(o0)";
    const auto bytes = renderer.render(renderer.compile(source),options(c.width,c.height,0,1)).to_rgba8();
    std::array<std::size_t,4> bounds{c.width,0,c.height,0};
    for (std::size_t y=0; y<c.height; ++y) {
      for (std::size_t x=0; x<c.width; ++x) {
        if (!bytes[(y*c.width+x)*4+3]) continue;
        bounds[0] = std::min(bounds[0],x);
        bounds[1] = std::max(bounds[1],x);
        bounds[2] = std::min(bounds[2],y);
        bounds[3] = std::max(bounds[3],y);
      }
    }
    REQUIRE(bounds == c.bounds);
    REQUIRE(detail::sha256({reinterpret_cast<const char*>(bytes.data()),bytes.size()}) == c.rgba);
  }
}

TEST(graph_publishes_seeded_parameter_textures) {
  Renderer renderer;
  for (bool iterated : {false, true}) {
    for (const std::string route : {"tex", "current", "empty", "external", "geometry", "volume", "inputGeo", "inputTex3d"}) {
      auto plan = renderer.compile("search synth, mixer, filter\n"
          "solid(color:#f00).write(o1); solid(color:#0f0).blendMode(tex:o1).invert().write(o0)");
      auto& provider = snapshot_for(plan, "mixer/blendMode").definition;
      auto& provider_step = effect_step(plan, "mixer/blendMode");
      provider.iterated = iterated;
      set_iteration_count(provider_step, 1);
      provider.output_xyz = route;
      auto inputs = options(6,4,0,0);
      if (route == "external") {
        provider.external_texture = route;
        Surface source(3,1);
        source.clear({0,0,1,1});
        inputs.external_textures.push_back({route,std::move(source)});
      } else if (route == "inputGeo" || route == "inputTex3d") {
        auto& generator = snapshot_for(plan,"synth/solid").definition;
        generator.output_xyz = "outputTex";
        generator.output_geo = "outputTex";
        generator.output_tex3d = "outputTex";
      } else if (route == "geometry" || route == "volume") {
        effects::TextureDefinition seed;
        seed.name = "scratch";
        seed.width.kind = effects::DimensionKind::literal;
        seed.width.literal = 2;
        seed.height.kind = effects::DimensionKind::literal;
        seed.height.literal = 1;
        provider.textures.push_back(seed);
        if (route == "geometry") provider.output_geo = seed.name;
        else provider.output_tex3d = seed.name;
        effects::ParameterDefinition param;
        param.name = route;
        param.type = route;
        provider.parameters.push_back(param);
      } else if (route == "empty" || route == "current") {
        effects::ParameterDefinition param;
        param.name = "unusedSurface";
        param.type = "surface";
        param.texture = route;
        provider.parameters.push_back(param);
        SurfaceReference input;
        input.kind = SurfaceReference::Kind::input;
        provider_step.params.push_back({param.name,route == "empty" ? PlanValue::null() : PlanValue::surface_value(input)});
      }
      snapshot_for(plan,"filter/invert").definition.output_tex = "inputXyz";
      skip_graph_passes(plan,"filter/invert");
      reauthenticate(plan);
      const auto result = renderer.render(plan, inputs);
      if (route == "geometry" || route == "volume" || route == "empty") {
        REQUIRE(result.width() == (route == "empty" ? 1U : 2U));
        REQUIRE(result.height() == 1U);
        for (const auto byte : result.to_rgba8()) REQUIRE(byte == 0);
      } else if (route == "external") {
        REQUIRE(result.width() == 3U);
        REQUIRE(result.height() == 1U);
        REQUIRE(result.to_rgba8()[2] == 255);
      } else {
        REQUIRE(result.width() == 6U);
        REQUIRE(result.height() == 4U);
        const auto bytes = result.to_rgba8();
        REQUIRE(bytes[0] == (route == "tex" ? 255 : 0));
        REQUIRE(bytes[1] == (route == "tex" ? 0 : 255));
      }
    }
  }
}

TEST(graph_keeps_prior_scratch_private_when_seeding_group_external_textures) {
  Renderer renderer;
  auto plan = renderer.compile("search synth, filter\nsolid().invert().blur().write(o0)");
  auto& source = snapshot_for(plan, "synth/solid").definition;
  effects::TextureDefinition scratch;
  scratch.name = "previousScratch";
  scratch.width.kind = effects::DimensionKind::literal;
  scratch.width.literal = 2;
  scratch.height = scratch.width;
  source.textures.push_back(scratch);
  auto& provider = snapshot_for(plan, "filter/invert").definition;
  provider.iterated = true;
  provider.external_texture = "declaredExternal";
  provider.output_xyz = scratch.name;
  set_iteration_count(effect_step(plan,"filter/invert"),1);
  snapshot_for(plan,"filter/blur").definition.output_tex = "inputXyz";
  skip_graph_passes(plan,"filter/blur");
  reauthenticate(plan);
  auto inputs = options(6,4,0,0);
  inputs.external_textures.push_back({"declaredExternal",Surface(3,1)});
  inputs.external_textures.push_back({scratch.name,Surface(4,1)});
  try {
    (void)renderer.render(plan,inputs);
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::missing_resource);
    REQUIRE(error.detail() == "write has no current image");
  }
}

TEST(graph_scatter_copies_compatible_backdrop_into_a_fresh_destination) {
  Renderer renderer;
  auto plan = renderer.compile("search synth, filter\nsolid(color:#000).wormhole().write(o0)");
  auto& snapshot = snapshot_for(plan, "filter/wormhole");
  auto& step = effect_step(plan, "filter/wormhole");
  effects::ParameterDefinition parameter;
  parameter.name = "wormhole_accum";
  parameter.type = "surface";
  snapshot.definition.parameters.push_back(parameter);
  snapshot.definition.output_tex = parameter.name;
  step.params.push_back({parameter.name, PlanValue::surface_value(SurfaceReference::named("o1",1))});
  // The black source deposits zero. Only bytes copied into the deposit pass
  // can be visible when neither the initial clear nor the final blend runs.
  for (const auto index : {0U, 2U}) {
    snapshot.definition.passes[index].repeat = effects::Value::number_value(0);
    snapshot.admissions[index].authority_pass.repeat = PlanValue::number_value(0);
    step.passes[index].authority_pass.repeat = PlanValue::number_value(0);
  }
  reauthenticate(plan);
  for (const auto& size : {std::array{2U,1U}, std::array{3U,8U}, std::array{6U,4U}}) {
    auto inputs = options(6,4,0,0);
    Surface prior(size[0],size[1]);
    prior.set_filter(TextureFilter::linear);
    for (std::size_t i=0; i<prior.data().size(); ++i) prior.data()[i] = static_cast<float>(i % 12) / 16;
    inputs.seed_surfaces.push_back({"o1",std::move(prior)});
    const auto result = renderer.render(plan, inputs);
    REQUIRE(result.width() == 6U);
    REQUIRE(result.height() == 4U);
    REQUIRE(result.surface().filter() == TextureFilter::nearest);
    const auto data = result.surface().data();
    for (std::size_t i=0; i<data.size(); ++i)
      REQUIRE(data[i] == (size[0] * size[1] == 24 ? static_cast<float>(i % 12) / 16 : 0.0F));
  }
}

TEST(graph_sizes_typed_fallback_from_effective_seed) {
  Renderer renderer;
  for (const bool iterated : {false, true}) {
    for (const auto& [argument, width] : {std::pair{"", 7U}, std::pair{"seed:0", 1U}, std::pair{"seed:3", 3U}}) {
      const std::string source = "search synth, filter\nperlin(" + std::string(argument) + ").invert().write(o0)";
      auto plan = renderer.compile(source);
      auto& provider = snapshot_for(plan, "synth/perlin").definition;
      provider.iterated = iterated;
      set_iteration_count(effect_step(plan, provider.id), 1.0);
      effects::TextureDefinition texture;
      texture.name = "geometryStorage";
      texture.width.kind = effects::DimensionKind::parameter;
      texture.width.parameter = "seed";
      texture.height.kind = effects::DimensionKind::literal;
      texture.height.literal = 1;
      provider.textures.push_back(texture);
      provider.output_geo = texture.name;
      effects::ParameterDefinition geometry;
      geometry.name = "geometry";
      geometry.type = "geometry";
      provider.parameters.push_back(geometry);
      provider.output_xyz = geometry.name;
      snapshot_for(plan, "filter/invert").definition.output_tex = "inputXyz";
      skip_graph_passes(plan, "filter/invert");
      reauthenticate(plan);
      const auto image = renderer.render(plan, options(6, 4, 0, 7));
      REQUIRE(image.width() == width);
      REQUIRE(image.height() == 1U);
    }
  }
}

TEST(graph_shared_storage_uses_the_owners_effective_render_seed) {
  Renderer renderer;
  for (const bool owner_is_later : {false, true}) {
    for (const bool iterated : {false, true}) {
      for (const auto& [binding,width] : {std::pair{"",7U}, std::pair{"seed:0",1U}, std::pair{"seed:3",3U}}) {
        // Clouds' own public minimum seed is one. Perlin accepts explicit zero.
        if (owner_is_later && width == 1) continue;
        const std::string source = "search synth, filter\nperlin(" +
            std::string(owner_is_later ? "" : binding) + ").clouds(" +
            (owner_is_later ? binding : "") + ").write(o0)";
        auto plan = renderer.compile(source);
        auto& writer = snapshot_for(plan, "synth/perlin").definition;
        auto& reader = snapshot_for(plan, "filter/clouds").definition;
        effects::TextureDefinition storage;
        storage.name = "global_shared";
        storage.width.kind = effects::DimensionKind::parameter;
        storage.width.parameter = "seed";
        storage.height.kind = effects::DimensionKind::literal;
        storage.height.literal = 1;
        (owner_is_later ? reader : writer).textures.push_back(storage);
        writer.passes.front().storage_textures = {{"store",storage.name}};
        reader.output_tex = storage.name;
        writer.iterated = iterated;
        reader.iterated = iterated;
        set_iteration_count(effect_step(plan,writer.id),1);
        set_iteration_count(effect_step(plan,reader.id),1);
        skip_graph_passes(plan,reader.id);
        reauthenticate(plan);
        const auto result = renderer.render(plan,options(6,4,0,7));
        REQUIRE(result.width() == width);
        REQUIRE(result.height() == 1U);
      }
    }
  }
}
