#include "noisemaker/graph/executor.hpp"
#include "noisemaker/render_result.hpp"
#include "noisemaker/renderer.hpp"

#include <type_traits>

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
  return source_result.width() == 1U && source_result.height() == 1U &&
                 source_result.pass_count() == 1U &&
                 source_result.final_route() == "o0" &&
                 source_result.to_rgba8().size() == 4U
             ? 0
             : 1;
}
