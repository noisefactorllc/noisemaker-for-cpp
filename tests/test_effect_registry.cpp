#include "noisemaker/effects/registry.hpp"

#include "test_harness.hpp"

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
