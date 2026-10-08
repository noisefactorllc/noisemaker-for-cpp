#pragma once

#include "noisemaker/effects/catalog_types.hpp"
#include "noisemaker/graph/execution_plan.hpp"

#include <optional>

namespace noisemaker::graph {

// The consumer range an automation value scales into, and whether the consumer
// rounds to an integer: upstream's expander.js uniformSpecs entry.
struct AutomationSpec {
  std::optional<double> min;
  std::optional<double> max;
  bool integer = false;
};

// The spec the authority builds for a parameter (renderer.js automationParamSpec):
// a float/int parameter without choices scales 0..1 into its declared min..max
// (0..100 when undeclared); an int parameter with choices is rounded, scaled
// into its declared range only when it declares one. Every other type gets none.
[[nodiscard]] std::optional<AutomationSpec> automation_spec(const effects::ParameterDefinition* parameter);

// Evaluates an oscillator automation value at the normalized 0..1 loop time,
// scaled into `spec` (automation.js evaluateAutomation + resolveAutomationUniform).
[[nodiscard]] double resolve_automation(const PlanValue& value, double normalized_time,
                                        const std::optional<AutomationSpec>& spec);

}  // namespace noisemaker::graph
