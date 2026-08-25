#include "noisemaker/renderer.hpp"

#include "noisemaker/dsl/compiler.hpp"
#include "noisemaker/effects/catalog.hpp"

#include <utility>

namespace noisemaker {

Renderer::Renderer() : registry_(effects::effect_catalog()) {}

Renderer::Renderer(effects::EffectRegistry registry)
    : registry_(std::move(registry)) {}

Renderer::Renderer(Renderer&&) noexcept = default;

Renderer& Renderer::operator=(Renderer&&) noexcept = default;

Renderer::~Renderer() = default;

graph::ExecutionPlan Renderer::compile(std::string_view source,
                                       std::string_view source_name) const {
  return dsl::compile(source, registry_, {}, source_name);
}

RenderResult Renderer::render(std::string_view source,
                              const RenderOptions& options,
                              std::string_view source_name) const {
  auto plan = dsl::compile(source, registry_, {.require_executable = true}, source_name);
  return render(plan, options);
}

RenderResult Renderer::render(const graph::ExecutionPlan& plan,
                              const RenderOptions& options) const {
  graph::GraphExecutor executor;
  auto result = executor.execute(plan, options);
  return RenderResult(std::move(result.surface), std::move(result.final_route),
                      result.pass_count);
}

}  // namespace noisemaker
