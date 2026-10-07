#include "noisemaker/effects/registry.hpp"

#include "test_harness.hpp"
#include "noisemaker/renderer.hpp"

#include <array>
#include <cmath>

#include <algorithm>
#include <utility>

using noisemaker::effects::EffectDefinition;
using noisemaker::effects::EffectRegistry;
using noisemaker::effects::ParameterDefinition;
using noisemaker::effects::ParameterArgument;
using noisemaker::effects::Value;
using noisemaker::graph::PlanValue;

namespace {
EffectDefinition source_effect() {
  EffectDefinition effect;
  effect.id = "fixture/source";
  effect.name_space = "fixture";
  effect.function = "source";
  effect.kind = "generator";
  effect.domain = "image";
  ParameterDefinition amount;
  amount.name = "amount";
  amount.type = "float";
  amount.default_value = Value::number_value(2.0);
  amount.min = Value::number_value(0.0);
  amount.max = Value::number_value(4.0);
  effect.parameters.push_back(amount);
  ParameterDefinition color;
  color.name = "color";
  color.type = "color";
  color.default_value = Value::array_value({Value::number_value(0.0), Value::number_value(0.0), Value::number_value(0.0)});
  effect.parameters.push_back(color);
  noisemaker::effects::PassDefinition pass;
  pass.name = "main";
  pass.program = "source";
  effect.passes.push_back(pass);
  return effect;
}
}

TEST(effect_registry_resolves_in_search_order_and_normalizes_defaults) {
  EffectRegistry registry;
  registry.register_effect(source_effect());
  const auto* found = registry.resolve("source", {"missing", "fixture"});
  REQUIRE(found != nullptr);
  const auto normalized = registry.normalize(*found, {{"amount", PlanValue::number_value(3.0)}});
  REQUIRE(normalized.values.size() == 2);
  REQUIRE(normalized.values[0].name == "amount");
  REQUIRE(normalized.values[0].value.number == 3.0);
  REQUIRE(normalized.values[1].name == "color");
}

TEST(effect_registry_applies_aliases_and_rejects_ranges) {
  auto effect = source_effect();
  effect.parameter_aliases.push_back({"strength", "amount"});
  EffectRegistry registry({effect});
  const auto* found = registry.get("fixture", "source");
  REQUIRE(found != nullptr);
  const auto normalized = registry.normalize(*found, {{"strength", PlanValue::number_value(4.0)}});
  REQUIRE(normalized.values[0].name == "amount");
  REQUIRE_THROWS_AS(registry.normalize(*found, {{"amount", PlanValue::number_value(5.0)}}), std::invalid_argument);
}

TEST(effect_registry_rejects_each_omitted_typed_compatibility_fact) {
  const std::vector<std::string> fields = {"capabilities", "uniforms", "samplers", "outputs", "output_abi", "source", "factory", "semantic", "authority_pass", "draw_mode", "dimensionality"};
  for (const auto& omitted : fields) {
    auto catalog = noisemaker::effects::effect_catalog();
    auto& row = catalog.canonical_programs.front();
    row.raw.erase(std::remove_if(row.raw.begin(), row.raw.end(), [&](const auto& item) { return item.first == omitted; }), row.raw.end());
    REQUIRE_THROWS_AS(EffectRegistry(catalog), std::invalid_argument);
  }
}

TEST(effect_registry_rejects_typed_compatibility_value_mutants) {
  const auto mutate = [](auto&& function) {
    auto catalog = noisemaker::effects::effect_catalog();
    function(catalog.canonical_programs.front());
    REQUIRE_THROWS_AS(EffectRegistry(catalog), std::invalid_argument);
  };
  const auto raw_field = [](auto& row, const std::string& name) -> Value* {
    for (auto& item : row.raw) if (item.first == name) return &item.second;
    return nullptr;
  };
  const auto object_field = [](Value& value, const std::string& name) -> Value* {
    for (auto& item : value.object) if (item.first == name) return &item.second;
    return nullptr;
  };
  mutate([&](auto& row) { row.raw.push_back({"capabilities", Value::array_value({})}); });
  mutate([&](auto& row) { raw_field(row, "source")->string = "sources/../forged.glsl"; });
  mutate([&](auto& row) { raw_field(row, "old_raw_sha256")->string = std::string(64, 'A'); });
  mutate([&](auto& row) { raw_field(row, "reasons")->array.push_back(Value::object_value({{"code", Value::string_value("unexpected")}, {"detail", Value::string_value("value")}})); });
  mutate([&](auto& row) { object_field(*raw_field(row, "semantic"), "new_token_sha256")->string = std::string(64, '0'); });
  mutate([&](auto& row) { object_field(*raw_field(row, "output_abi"), "canonical_slots")->array[0].number = 2; });
  mutate([&](auto& row) { object_field(*raw_field(row, "authority_pass"), "blend")->boolean = true; });
  mutate([&](auto& row) { object_field(*object_field(*raw_field(row, "factory"), "route"), "factory")->string = "wrong"; });
  mutate([&](auto& row) { object_field(raw_field(row, "uniforms")->array.front(), "source")->string = "forged_source"; });
}

TEST(effect_registry_admits_only_authenticated_scope_and_spectrum_audio_arrays) {
  EffectRegistry registry(noisemaker::effects::effect_catalog());
  noisemaker::Renderer renderer;
  for (const auto effect : {"scope", "spectrum"}) {
    const auto* definition = registry.get("synth", effect);
    REQUIRE(definition != nullptr);
    const auto admission = registry.admission(*definition, 0U);
    const std::string name = std::string(effect) == "scope" ? "audioWaveform" : "audioSpectrum";
    const auto binding = std::find_if(admission.uniforms.begin(), admission.uniforms.end(),
        [&](const auto& value) { return value.name == name; });
    REQUIRE(binding != admission.uniforms.end());
    REQUIRE(binding->type == "float[128]");
    REQUIRE(binding->cpp_type == "glsl::AudioUniform128");
    REQUIRE(binding->source == "reserved_runtime_state");
    REQUIRE(binding->source_name == name);

    const auto plan = renderer.compile(std::string("search synth\n") + effect + "().write(o0)\nrender(o0)\n");
    const auto& step = std::get<noisemaker::graph::EffectStep>(plan.chains.front().steps.front());
    REQUIRE(noisemaker::graph::authenticate_factory_route(step, admission) != nullptr);
    for (const auto field : {"name", "type", "cpp_type", "source", "source_name", "program"}) {
      auto forged = admission;
      auto& audio = forged.uniforms[static_cast<std::size_t>(binding - admission.uniforms.begin())];
      const std::string mutation = field;
      if (mutation == "name") audio.name = "foreignAudio";
      if (mutation == "type") audio.type = "float[127]";
      if (mutation == "cpp_type") audio.cpp_type = "glsl::Vec4";
      if (mutation == "source") audio.source = "effect_parameter";
      if (mutation == "source_name") audio.source_name = "foreignAudio";
      if (mutation == "program") forged.identity.program_key = "synth/shape:shape";
      REQUIRE_THROWS_AS(noisemaker::graph::authenticate_factory_route(step, forged), noisemaker::graph::GraphError);
    }
  }
}

TEST(effect_registry_joins_repeated_reference_keys_by_structural_identity) {
  EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto* temporal = registry.get("filter", "temporalAberration");
  REQUIRE(temporal != nullptr);
  std::vector<std::size_t> indexes;
  for (std::size_t index = 0; index < temporal->passes.size(); ++index) {
    if (temporal->passes[index].program == "delayShift") indexes.push_back(registry.admission(*temporal, index).identity.index);
  }
  REQUIRE(indexes.size() == 8);
  for (std::size_t index = 0; index < indexes.size(); ++index) REQUIRE(indexes[index] == index + 1);
  const auto* physarum = registry.get("points", "physarum");
  REQUIRE(physarum != nullptr);
  REQUIRE(registry.admission(*physarum, 2).identity.program_key == "points/physarum:passthrough");
  REQUIRE(registry.admission(*physarum, 4).identity.program_key == "points/physarum:passthrough");
  const auto* loop_end = registry.get("render", "loopEnd");
  REQUIRE(loop_end != nullptr);
  REQUIRE(registry.admission(*loop_end, 0).identity.program_key == "render/loopEnd:copy");
  REQUIRE(registry.admission(*loop_end, 1).identity.program_key == "render/loopEnd:copy");
  const auto* billboard = registry.get("render", "pointsBillboardRender");
  REQUIRE(billboard != nullptr);
  REQUIRE(registry.admission(*billboard, 31).identity.program_key == "render/pointsBillboardRender:deposit");
  REQUIRE(registry.admission(*billboard, 34).identity.program_key == "render/pointsBillboardRender:deposit");
  const auto additive = registry.admission(*billboard, 31);
  const auto alpha = registry.admission(*billboard, 34);
  REQUIRE(additive.authority_pass.blend_kind == "boolean");
  REQUIRE(additive.authority_pass.blend);
  REQUIRE(alpha.authority_pass.blend_kind == "factors");
  REQUIRE(alpha.authority_pass.blend_factors[0] == "ONE");
  REQUIRE(alpha.authority_pass.blend_factors[1] == "ONE_MINUS_SRC_ALPHA");
  REQUIRE(additive.authority_pass.inputs == alpha.authority_pass.inputs);
  REQUIRE(additive.authority_pass.outputs == alpha.authority_pass.outputs);
}

TEST(effect_registry_owns_authenticated_production_provenance_and_scatter_contract) {
  const auto& registry = EffectRegistry(noisemaker::effects::effect_catalog());
  const auto& provenance = registry.provenance();
  REQUIRE(registry.manifest_backed());
  REQUIRE(provenance.backend_schema == "noisemaker-cpp.backend-compatibility.v1");
  REQUIRE(provenance.corpus_revision == "e24c844f8dada85551ab084f41db8944fbc176c8");
  REQUIRE(provenance.cpu_package_sha256.size() == 64);
  REQUIRE(provenance.upstream_package_lock_sha256.size() == 64);
  const auto* wormhole = registry.get("filter", "wormhole");
  REQUIRE(wormhole != nullptr);
  const auto scatter = registry.admission(*wormhole, 1);
  REQUIRE(scatter.status == noisemaker::graph::AvailabilityStatus::scatter);
  REQUIRE(scatter.scatter.has_value());
  REQUIRE(scatter.scatter->adapter == "noisemaker::scatter::wormhole::adapter");
  REQUIRE(scatter.scatter->uniforms.size() == 4);
  REQUIRE(scatter.scatter->outputs.size() == 1);
  REQUIRE(scatter.scatter->outputs[0].logical_route == "wormhole_accum");
}

TEST(effect_registry_binds_each_particle_family_scatter_contract_to_its_own_row) {
  const auto& registry = EffectRegistry(noisemaker::effects::effect_catalog());
  struct Expected { const char* name_space; const char* function; const char* program; const char* adapter; const char* route; };
  const std::vector<Expected> expected = {
      {"points", "physarum", "deposit", "noisemaker::scatter::physarum::adapter", "global_physarum_pheromone"},
      {"points", "dla", "depositGrid", "noisemaker::scatter::dla::adapter", "global_dla_grid"},
      {"points", "lenia", "deposit", "noisemaker::scatter::lenia::adapter", "global_lenia_density"},
      {"filter3d", "flow3d", "deposit", "noisemaker::scatter::flow3d::adapter", "global_flow3d_trail"},
  };
  for (const auto& [name_space, function, program, adapter, route] : expected) {
    const auto* effect = registry.get(name_space, function);
    REQUIRE(effect != nullptr);
    bool found = false;
    for (std::size_t index = 0; index < effect->passes.size(); ++index) {
      if (effect->passes[index].program != program) continue;
      found = true;
      const auto admission = registry.admission(*effect, index);
      REQUIRE(admission.identity.program_key == std::string(name_space) + "/" + function + ":" + program);
      REQUIRE(admission.status == noisemaker::graph::AvailabilityStatus::scatter);
      REQUIRE(admission.scatter.has_value());
      REQUIRE(admission.scatter->adapter == adapter);
      REQUIRE(admission.scatter->outputs.size() == 1);
      REQUIRE(admission.scatter->outputs[0].physical_name == "fragColor");
      REQUIRE(admission.scatter->outputs[0].logical_route == route);
      REQUIRE(admission.scatter->outputs[0].cpp_type == "glsl::Vec4");
    }
    REQUIRE(found);
  }
}

TEST(effect_registry_rejects_forged_reference_metadata_and_provenance) {
  auto metadata = noisemaker::effects::effect_catalog();
  metadata.reference_passes[0].authority_pass.name = "forged";
  REQUIRE_THROWS_AS(EffectRegistry(metadata), std::invalid_argument);
  auto provenance = noisemaker::effects::effect_catalog();
  provenance.provenance.corpus_revision = "forged";
  REQUIRE_THROWS_AS(EffectRegistry(provenance), std::invalid_argument);
  auto scatter = noisemaker::effects::effect_catalog();
  scatter.scatter->outputs[0].logical_route = "forged";
  REQUIRE_THROWS_AS(EffectRegistry(scatter), std::invalid_argument);
}

TEST(effect_registry_preserves_complete_alias_census) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  std::size_t aliases = 0;
  for (const auto& effect : catalog.definitions) aliases += effect.parameter_aliases.size();
  REQUIRE(catalog.definitions.size() == 210);
  REQUIRE(aliases == 84);
}

TEST(effect_registry_rejects_duplicate_reference_triple_and_order_mutation) {
  auto duplicate = noisemaker::effects::effect_catalog();
  duplicate.reference_passes.push_back(duplicate.reference_passes.front());
  REQUIRE_THROWS_AS(EffectRegistry(duplicate), std::invalid_argument);
  auto swapped = noisemaker::effects::effect_catalog();
  std::swap(swapped.reference_passes[0], swapped.reference_passes[1]);
  REQUIRE_THROWS_AS(EffectRegistry(swapped), std::invalid_argument);
}

TEST(effect_registry_rejects_copied_production_catalog_without_private_capability) {
  auto copied = noisemaker::effects::effect_catalog();
  REQUIRE_THROWS_AS(EffectRegistry(copied), std::invalid_argument);

  noisemaker::effects::EffectCatalog assigned;
  assigned = noisemaker::effects::effect_catalog();
  REQUIRE_THROWS_AS(EffectRegistry(assigned), std::invalid_argument);
}

TEST(effect_registry_rejects_copied_catalog_parameter_mutation) {
  auto parameter_name = noisemaker::effects::effect_catalog();
  parameter_name.definitions.front().parameters.front().name = "forged_parameter";
  REQUIRE_THROWS_AS(EffectRegistry(parameter_name), std::invalid_argument);

  auto parameter_default = noisemaker::effects::effect_catalog();
  parameter_default.definitions.front().parameters.front().default_value = Value::number_value(999.0);
  REQUIRE_THROWS_AS(EffectRegistry(parameter_default), std::invalid_argument);
}

TEST(effect_registry_rejects_copied_catalog_pass_and_texture_mutation) {
  auto pass = noisemaker::effects::effect_catalog();
  pass.definitions.front().passes.front().raw.push_back({"forged", Value::boolean_value(true)});
  REQUIRE_THROWS_AS(EffectRegistry(pass), std::invalid_argument);

  auto texture = noisemaker::effects::effect_catalog();
  const auto texture_effect = std::find_if(texture.definitions.begin(), texture.definitions.end(),
                                           [](const auto& effect) { return !effect.textures.empty(); });
  REQUIRE(texture_effect != texture.definitions.end());
  texture_effect->textures.front().name = "forged_texture";
  REQUIRE_THROWS_AS(EffectRegistry(texture), std::invalid_argument);
}

TEST(effect_registry_default_catalog_moves_remain_custom) {
  noisemaker::effects::EffectCatalog original;
  original.definitions.push_back(source_effect());
  noisemaker::effects::EffectCatalog moved(std::move(original));
  EffectRegistry move_registry(moved);
  REQUIRE(!move_registry.manifest_backed());

  noisemaker::effects::EffectCatalog assigned;
  assigned = std::move(moved);
  EffectRegistry assignment_registry(assigned);
  REQUIRE(!assignment_registry.manifest_backed());
}

TEST(effect_registry_accepts_every_repaired_dither_palette) {
  EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto* effect = registry.get("filter", "dither");
  REQUIRE(effect != nullptr);
  for (int palette = 0; palette <= 9; ++palette) {
    const auto normalized = registry.normalize(*effect, {{"palette", PlanValue::number_value(palette)}});
    const auto found = std::find_if(normalized.values.begin(), normalized.values.end(),
        [](const auto& value) { return value.name == "palette"; });
    REQUIRE(found != normalized.values.end());
    REQUIRE(found->value.number == palette);
  }
}

TEST(dither_palette_endpoints_match_repaired_cpu_authority_and_repeat) {
  // Captured from immutable CPU 26d6f42be38da7172f602373e844f85a8155356f.
  // White/black nearest palette colors at threshold +/-0.5, 3x2 pixels.
  constexpr std::array<std::array<std::array<unsigned char, 4>, 2>, 9> endpoints{{
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}},
      {{{{156, 189, 15, 255}}, {{15, 56, 15, 255}}}},
      {{{{255, 153, 0, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 241, 232, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}},
      {{{{255, 255, 255, 255}}, {{0, 0, 0, 255}}}}
  }};
  noisemaker::Renderer renderer;
  noisemaker::graph::ExecutionInputs options;
  options.width = 3U;
  options.height = 2U;
  for (int palette = 1; palette <= 9; ++palette) {
    for (const int color : {1, 0, 1, 0}) {
      const std::string source = "search synth, filter\nsolid(color: [" +
          std::to_string(color) + ", " + std::to_string(color) + ", " +
          std::to_string(color) + "]).dither(palette: " + std::to_string(palette) +
          ", threshold: " + (color ? "0.5" : "-0.5") + ").write(o0)\nrender(o0)\n";
      const auto result = renderer.render(source, options, "dither-palette-endpoints.dsl");
      for (const auto value : result.surface().data()) REQUIRE(std::isfinite(value));
      const auto bytes = result.to_rgba8();
      REQUIRE(bytes.size() == 24U);
      const auto& expected = endpoints[static_cast<std::size_t>(palette - 1)][color ? 0U : 1U];
      for (std::size_t lane = 0; lane < bytes.size(); ++lane) REQUIRE(bytes[lane] == expected[lane % 4U]);
    }
  }
}
