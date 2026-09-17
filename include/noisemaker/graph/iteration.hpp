#pragma once

// Iteration-group computation for the CPU executor's future stateful/particle
// effect support -- the C++ port of noisemaker-for-cpu's
// src/runtime/iteration.js (read in full; every citation below is against
// that file at the pinned authority revision 61aa869, plus the group-driver
// call sites in src/runtime/renderer.js it feeds).
//
// Pure and side-effect-free, exactly like its JS original: this only reads
// plan-authored metadata (EffectDefinition::iterated/loop_role/textures,
// PassDefinition::inputs/outputs) -- never a Surface, never the
// ResourceArena, never a real render. That is deliberate: it makes the
// grouping algorithm independently testable without a single real GLSL
// kernel, which matters today because every one of the 25 effects that
// actually sets `iterated` true (Families B/C/D's iterated generators/
// Family E's particle effects) has NO admitted kernel yet (see
// phase2-architecture.md's family reports) -- there is no way to prove an
// N-iteration render byte-exact against anything until that corpus work
// lands.
//
// NOT YET WIRED into GraphExecutor::execute(). Wiring it requires
// restructuring execute()'s single "one EffectStep, one pass per call, one
// GraphResource* current" per-chain loop into one that runs a whole group's
// steps N times sharing a step-scoped and a group-scoped resource map -- and,
// per the architecture map's own risk callout, a real design pass on
// ResourceArena's lifetime model first (it has no category today for
// "persists across N re-executions of a subgraph, never published to a name
// any other step could bind by mistake"). That step-by-step execution
// plumbing has nothing to verify against without a real kernel; this module
// is the part that does, and is meant to be reused unmodified once it does.

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/surface.hpp"

#include <cstddef>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace noisemaker::graph::iteration {

// iteration.js:14 -- PARTICLE_STATE_PATTERN
// (`/^global_(xyz|vel|rgba|life_data)$|^global_.*_trail$/`). `render/
// pointsEmit` is the only definition that ever declares `global_xyz` itself
// (iteration.js:9-13); every OTHER step whose own pass graph references one
// of these four exact names or a `global_*_trail` name joins whatever
// particle group is currently open (iteration.js:31-37). A `global_`-
// prefixed name that doesn't match this exact pattern (e.g.
// `synth/reactionDiffusion`'s private `global_rd_state`) stays ordinary
// per-step scratch -- confirmed by direct string comparison against the
// four literal alternatives and the `^global_.*_trail$` alternative (a
// 13-character floor: 7-char prefix + 6-char suffix, non-overlapping since
// the pattern is anchored at both ends).
[[nodiscard]] bool is_particle_state_name(std::string_view name) noexcept;

// iteration.js:21 -- ITERATION_DELTA_TIME: upstream's synthetic
// per-simulation-tick step, 1/60s over its canonical 10s wraparound loop.
inline constexpr double kIterationDeltaTime = 1.0 / 600.0;

// iteration.js:23-25 -- wrap01(x) = ((x % 1) + 1) % 1, using JS `%`'s
// fmod-equivalent (ECMA-262: "analogous to... the C library function fmod")
// double-remainder semantics, which is exactly `std::fmod`. Used to compute
// each iteration's `time` (renderer.js:877): `wrap01(renderOptions.time -
// (N-1-i) * ITERATION_DELTA_TIME)`.
[[nodiscard]] double wrap01(double value) noexcept;

// renderer.js:853-855 (identically mirrored, async, at 896-898): `N =
// Number.isFinite(iterationCount) ? iterationCount : 60`; the group is
// zero-iteration when `!(N > 0)` (covers N<=0 and NaN -- though NaN never
// reaches this branch, `Number.isFinite` already routed it to the `: 60`
// default). `iteration_count_value` is the step's own bound `iterationCount`
// parameter (`nullptr` if the effect declares none), mirroring
// `group.steps[0].params.iterationCount`.
struct ResolvedIterationCount {
  double n = 60.0;
  bool zero_iterations = false;
};
[[nodiscard]] ResolvedIterationCount resolve_iteration_count(
    const PlanValue* iteration_count_value) noexcept;

// iteration.js:57-105 -- computeIterationGroups. One entry per group;
// `step_indices` holds indices into `chain.steps` (the same vector this
// operates over), in the original order. `loop` distinguishes a
// `loopBegin`...`loopEnd` region (iteration.js:69-77) from an ordinary or
// particle group -- both are `iterated:true`, but only a loop region
// additionally gets the `global_accum` group-shared surface at execution
// time (renderer.js:858-865).
//
// Three group-forming rules, evaluated in this exact order for every
// non-loop, non-read/write step (iteration.js:84-100):
//   1. `loop_role == "begin"` opens a loop region; `loop_role == "end"`
//      closes it. A `read`/`write` step, or a nested `begin`, inside an open
//      loop throws, as does an unmatched `begin` or `end`.
//   2. A step declaring `global_xyz` in its OWN `definition.textures`
//      always closes whatever is open and opens a brand new particle group
//      that it owns (even immediately after another such step -- two
//      `pointsEmit()` calls in one chain open two independent groups, never
//      one merged group).
//   3. While a particle group is open, a later step joins it iff its own
//      pass inputs/outputs reference a particle-state name; otherwise it
//      closes the group and starts its own single-step (non-iterated unless
//      its own `definition.iterated` is set) group.
// `read`/`write` steps outside an open loop are always boundaries: they
// close any open particle group and become their own single-step,
// non-iterated group (iteration.js:79-83).
//
// Throws `std::invalid_argument` for exactly the three invariants the JS
// source enforces, with the same conditions (iteration.js:70,71,84,102):
// a loop region crossing a read/write boundary, a nested `loopBegin`, or an
// unmatched `loopBegin`/`loopEnd`.
struct IterationGroup {
  std::vector<std::size_t> step_indices;
  bool iterated = false;
  bool loop = false;
};
[[nodiscard]] std::vector<IterationGroup> compute_iteration_groups(
    const ExecutionPlan& plan, const ExecutionChain& chain);

// storeGroupOutput's single routing predicate (renderer.js:762-765):
//   storeGroupOutput(name, surface, state, groupResources, surfaces, owned) {
//     if (isParticleStateName(name) || name === 'global_accum')
//       this.replaceCanonicalResource(name, surface, groupResources, ...)
//     else this.replaceCanonicalResource(name, surface, state.resources, ...)
//   }
// A particle-state name or the literal `global_accum` always shares the
// SAME map across every step in the group's whole N-iteration run;
// everything else is the caller's own per-step concern (`state.resources`
// in JS, a step-scoped map this module does not model), untouched by this
// predicate. `global_accum` is matched by literal name equality, never the
// particle regex -- confirmed independently in
// phase2-architecture.md's §3.2.1 (`filter/convolutionFeedback`'s own
// `global_ca_state`/`global_mnca_state`/`global_rd_state`/`global_ns_*`
// names, despite the `global_` prefix, do NOT match either this or
// `is_particle_state_name`).
[[nodiscard]] bool is_group_shared_resource_name(std::string_view name) noexcept;

// The group-shared resource map itself: one named `Surface` per group run.
// Mirrors JS's `groupResources` (a plain `Map`, `renderer.js:857` /
// `runIteratedGroupSync`) plus two lifetime rules read off its real call
// sites rather than assumed:
//   - `replaceCanonicalResource` (used by `storeGroupOutput` above and by
//     `resolveGroupParticleTexture`/the loop-region `global_accum` seed,
//     renderer.js:860-864) always REPLACES whatever was stored under a
//     name -- never mutates a surface in place -- so a later pass that
//     already retained the old value keeps observing the old bytes, exactly
//     like the step-scoped, non-group `ResourceArena::insert` publish path
//     this module deliberately does not depend on.
//   - `finishGroupResources` (renderer.js:832-850) releases every entry at
//     group end EXCEPT whatever surface(s) the group's final output
//     retains -- "particle state never survives beyond the group run that
//     owns it" (renderer.js:836, a comment on this exact line). This class
//     does not itself own release/pooling (it has no ResourceArena to call
//     into); `release_all_except` returns the set of surfaces a caller
//     should actually release, letting the real caller -- once wired --
//     apply whatever its own arena's release semantics are.
class GroupResourceMap {
 public:
  // Replaces (constructing if absent) the surface stored under `name`.
  void store(std::string name, Surface surface);

  [[nodiscard]] bool contains(std::string_view name) const noexcept;
  [[nodiscard]] const Surface* find(std::string_view name) const noexcept;
  [[nodiscard]] std::size_t size() const noexcept { return resources_.size(); }

  // Removes and returns every entry NOT identified by `retained_names` --
  // the surfaces a caller should release once it has finished publishing
  // the group's real output under whatever name(s) it retains. Mirrors
  // `finishGroupResources`' "release everything not in `retained`" loop;
  // unlike the JS original (which compares Surface *identity*, since a name
  // can be re-pointed to the same surface object retained elsewhere), this
  // compares by NAME, since `GroupResourceMap` never aliases two names to
  // one surface -- the caller passes the retained NAME(s), not object
  // identity, and gets back every other entry's Surface by value to dispose
  // of however its own resource lifetime model requires.
  [[nodiscard]] std::vector<std::pair<std::string, Surface>> release_all_except(
      const std::vector<std::string_view>& retained_names);

  [[nodiscard]] bool empty() const noexcept { return resources_.empty(); }

 private:
  std::unordered_map<std::string, Surface> resources_;
};

}  // namespace noisemaker::graph::iteration
