#include "noisemaker/graph/executor.hpp"
#include "noisemaker/effects/catalog_types.hpp"
#include "noisemaker/render_result.hpp"
#include "noisemaker/renderer.hpp"

#include <string>
#include <type_traits>
#include <utility>
#include <vector>

int main() {
  static_assert(std::is_copy_constructible_v<noisemaker::RenderOptions>);
  static_assert(std::is_move_constructible_v<noisemaker::RenderOptions>);
  static_assert(!std::is_constructible_v<noisemaker::graph::GraphExecutor,
                                         noisemaker::effects::EffectRegistry*>);
  noisemaker::RenderOptions options{1, 1, 0.0, 0, 1.0, 0.0, true, {}, {}};
  noisemaker::Renderer renderer;
  const auto plan = renderer.compile("search synth\nsolid().write(o0)\nrender(o0)\n");
  const auto plan_result = renderer.render(plan, options);
  if (plan_result.width() != 1U || plan_result.height() != 1U ||
      plan_result.pass_count() != 1U || plan_result.final_route() != "o0" ||
      plan_result.to_rgba8().size() != 4U) {
    return 1;
  }
  const auto source_result = renderer.render(
      "search synth\nsolid().write(o0)\nrender(o0)\n", options,
      "consumer.dsl");
  if (source_result.width() != 1U || source_result.height() != 1U ||
      source_result.pass_count() != 1U || source_result.final_route() != "o0" ||
      source_result.to_rgba8().size() != 4U) {
    return 1;
  }

  // Value::object keeps the published pair-vector API surface: construct from
  // a pair vector, assign one, convert back, and index pairs element-wise.
  using noisemaker::effects::Value;
  using noisemaker::effects::ValueKind;
  std::vector<std::pair<std::string, Value>> entries{
      {"alpha", Value::number_value(2.0)},
      {"beta", Value::string_value("x")}};
  const Value from_factory = Value::object_value(entries);
  const std::vector<std::pair<std::string, Value>> round_trip = from_factory.object;
  if (round_trip.size() != entries.size() || round_trip[0].first != "alpha" ||
      round_trip[0].second.kind != ValueKind::number ||
      round_trip[0].second.number != 2.0 ||
      round_trip[1].first != "beta" ||
      round_trip[1].second.kind != ValueKind::string ||
      round_trip[1].second.string != "x") {
    return 1;
  }
  Value assigned = Value::null();
  assigned.object = entries;
  if (assigned.object.size() != 2U || assigned.object[1].second.string != "x") {
    return 1;
  }
  assigned.object.push_back(std::make_pair("gamma", Value::boolean_value(true)));
  if (assigned.object.size() != 3U || assigned.object[2].first != "gamma" ||
      assigned.object[2].second.boolean != true) {
    return 1;
  }
  for (const auto& entry : assigned.object) {
    if (entry.first.empty()) {
      return 1;
    }
  }
  return 0;
}
