#include "noisemaker/graph/iteration.hpp"

#include <algorithm>
#include <cmath>
#include <optional>
#include <stdexcept>
#include <utility>
#include <variant>

namespace noisemaker::graph::iteration {
namespace {

[[nodiscard]] const effects::EffectDefinition& definition_of(
    const ExecutionPlan& plan, const EffectStep& step) {
  return plan.effects.at(step.snapshot_index).definition;
}

// iteration.js:27-29 -- declaresXyz: `Object.prototype.hasOwnProperty.call(
// step.definition.textures ?? {}, 'global_xyz')`.
[[nodiscard]] bool declares_xyz(const effects::EffectDefinition& definition) noexcept {
  for (const auto& texture : definition.textures) {
    if (texture.name == "global_xyz") return true;
  }
  return false;
}

// iteration.js:31-37 -- referencesParticleState: any pass input OR output
// value (never the key -- the key is the uniform/output-variable name, the
// value is the resource route) matching PARTICLE_STATE_PATTERN.
[[nodiscard]] bool references_particle_state(
    const effects::EffectDefinition& definition) noexcept {
  for (const auto& pass : definition.passes) {
    for (const auto& input : pass.inputs) {
      if (is_particle_state_name(input.second)) return true;
    }
    for (const auto& output : pass.outputs) {
      if (is_particle_state_name(output.second)) return true;
    }
  }
  return false;
}

[[nodiscard]] bool loop_role_is(const effects::EffectDefinition& definition,
                                std::string_view role) noexcept {
  return definition.loop_role.has_value() && *definition.loop_role == role;
}

}  // namespace

bool is_particle_state_name(std::string_view name) noexcept {
  if (name == "global_xyz" || name == "global_vel" || name == "global_rgba" ||
      name == "global_life_data") {
    return true;
  }
  constexpr std::string_view kPrefix = "global_";
  constexpr std::string_view kSuffix = "_trail";
  if (name.size() < kPrefix.size() + kSuffix.size()) return false;
  return name.substr(0, kPrefix.size()) == kPrefix &&
         name.substr(name.size() - kSuffix.size()) == kSuffix;
}

double wrap01(double value) noexcept {
  const double modded = std::fmod(value, 1.0);
  return std::fmod(modded + 1.0, 1.0);
}

ResolvedIterationCount resolve_iteration_count(
    const PlanValue* iteration_count_value) noexcept {
  ResolvedIterationCount result;
  if (iteration_count_value != nullptr &&
      iteration_count_value->kind == PlanValue::Kind::number &&
      std::isfinite(iteration_count_value->number)) {
    result.n = iteration_count_value->number;
  } else {
    result.n = 60.0;
  }
  result.zero_iterations = !(result.n > 0.0);
  return result;
}

std::vector<IterationGroup> compute_iteration_groups(
    const ExecutionPlan& plan, const ExecutionChain& chain) {
  std::vector<IterationGroup> groups;
  std::optional<IterationGroup> open_group;
  std::optional<IterationGroup> open_loop;

  const auto close_open_group = [&]() {
    if (!open_group.has_value()) return;
    groups.push_back(*open_group);
    open_group.reset();
  };

  for (std::size_t index = 0; index < chain.steps.size(); ++index) {
    const auto& variant = chain.steps[index];
    const bool is_boundary = std::holds_alternative<ReadStep>(variant) ||
                             std::holds_alternative<WriteStep>(variant);

    // iteration.js:69-77 -- inside an open loop region, every step (read,
    // write, or effect) is consumed by the loop until a matching `end`.
    if (open_loop.has_value()) {
      if (is_boundary) {
        throw std::invalid_argument(
            "Loop iteration group cannot cross a read/write boundary");
      }
      const auto& definition = definition_of(plan, std::get<EffectStep>(variant));
      if (loop_role_is(definition, "begin")) {
        throw std::invalid_argument("Nested loop iteration groups are not supported");
      }
      open_loop->step_indices.push_back(index);
      if (loop_role_is(definition, "end")) {
        groups.push_back(*open_loop);
        open_loop.reset();
      }
      continue;
    }

    // iteration.js:79-83 -- read/write steps outside a loop are always
    // boundaries: close any open particle group, pass through as their own
    // single-step, non-iterated group.
    if (is_boundary) {
      close_open_group();
      groups.push_back(IterationGroup{{index}, false, false});
      continue;
    }

    const auto& effect_step = std::get<EffectStep>(variant);
    const auto& definition = definition_of(plan, effect_step);

    // iteration.js:84 -- an unmatched loopEnd throws immediately.
    if (loop_role_is(definition, "end")) {
      throw std::invalid_argument("loopEnd has no matching loopBegin");
    }
    // iteration.js:85-88 -- loopBegin closes whatever's open and starts a
    // new loop region (always iterated:true/loop:true once closed).
    if (loop_role_is(definition, "begin")) {
      close_open_group();
      open_loop = IterationGroup{{index}, true, true};
      continue;
    }
    // iteration.js:90-93 -- a step declaring `global_xyz` always closes
    // whatever's open and opens a brand-new particle group it owns.
    if (declares_xyz(definition)) {
      close_open_group();
      open_group = IterationGroup{{index}, definition.iterated, false};
      continue;
    }
    // iteration.js:95-97 -- while a particle group is open, a step joins it
    // iff it references a particle-state name.
    if (open_group.has_value() && references_particle_state(definition)) {
      open_group->step_indices.push_back(index);
      continue;
    }
    // iteration.js:99-100 -- otherwise: close whatever's open, start this
    // step's own single-step group (iterated iff its own definition is).
    close_open_group();
    groups.push_back(IterationGroup{{index}, definition.iterated, false});
  }

  // iteration.js:102 -- an unmatched loopBegin throws at end-of-chain, not
  // mid-loop (a loop only ever throws on a *later* step, never on running
  // out of steps while still inside one, until this final check).
  if (open_loop.has_value()) {
    throw std::invalid_argument("loopBegin has no matching loopEnd");
  }
  close_open_group();
  return groups;
}

bool is_group_shared_resource_name(std::string_view name) noexcept {
  return is_particle_state_name(name) || name == "global_accum";
}

void GroupResourceMap::store(std::string name, Surface surface) {
  const auto it = resources_.find(name);
  if (it != resources_.end()) {
    it->second = std::move(surface);
    return;
  }
  resources_.emplace(std::move(name), std::move(surface));
}

bool GroupResourceMap::contains(std::string_view name) const noexcept {
  return resources_.find(std::string(name)) != resources_.end();
}

const Surface* GroupResourceMap::find(std::string_view name) const noexcept {
  const auto it = resources_.find(std::string(name));
  return it == resources_.end() ? nullptr : &it->second;
}

std::vector<std::pair<std::string, Surface>> GroupResourceMap::release_all_except(
    const std::vector<std::string_view>& retained_names) {
  std::vector<std::pair<std::string, Surface>> released;
  for (auto it = resources_.begin(); it != resources_.end();) {
    const bool retained =
        std::find(retained_names.begin(), retained_names.end(), it->first) !=
        retained_names.end();
    if (retained) {
      ++it;
      continue;
    }
    released.emplace_back(it->first, std::move(it->second));
    it = resources_.erase(it);
  }
  return released;
}

}  // namespace noisemaker::graph::iteration
