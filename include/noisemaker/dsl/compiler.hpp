#pragma once

#include "noisemaker/effects/registry.hpp"
#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/dsl/ast.hpp"

#include <string_view>

namespace noisemaker::dsl {

struct CompileOptions { bool require_executable = false; };

[[nodiscard]] graph::ExecutionPlan compile(std::string_view source,
                                           const effects::EffectRegistry& registry,
                                           CompileOptions options = {},
                                           std::string_view source_name = "<dsl>");
[[nodiscard]] graph::ExecutionPlan compile(const Program& program,
                                           const effects::EffectRegistry& registry,
                                           CompileOptions options = {});

[[nodiscard]] inline graph::ExecutionPlan compile_dsl(std::string_view source,
                                                      const effects::EffectRegistry& registry,
                                                      CompileOptions options = {},
                                                      std::string_view source_name = "<dsl>") {
  return compile(source, registry, options, source_name);
}

}  // namespace noisemaker::dsl
