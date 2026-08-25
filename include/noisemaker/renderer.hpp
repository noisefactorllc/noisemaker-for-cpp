#pragma once

#include "noisemaker/effects/registry.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/render_result.hpp"

#include <string_view>

namespace noisemaker {

using RenderOptions = graph::ExecutionInputs;

class Renderer final {
 public:
  Renderer();
  explicit Renderer(effects::EffectRegistry registry);
  Renderer(const Renderer&) = delete;
  Renderer& operator=(const Renderer&) = delete;
  Renderer(Renderer&&) noexcept;
  Renderer& operator=(Renderer&&) noexcept;
  ~Renderer();

  [[nodiscard]] graph::ExecutionPlan compile(
      std::string_view source, std::string_view source_name = "<dsl>") const;
  [[nodiscard]] RenderResult render(
      std::string_view source, const RenderOptions& options = {},
      std::string_view source_name = "<dsl>") const;
  [[nodiscard]] RenderResult render(
      const graph::ExecutionPlan& plan, const RenderOptions& options = {}) const;

 private:
  effects::EffectRegistry registry_;
};

}  // namespace noisemaker
