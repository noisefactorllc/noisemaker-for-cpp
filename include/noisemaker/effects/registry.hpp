#pragma once

#include "noisemaker/effects/catalog.hpp"
#include "noisemaker/graph/execution_plan.hpp"

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace noisemaker::effects {

struct ParameterArgument {
  std::optional<std::string> name;
  graph::PlanValue value;
};

struct NormalizedArguments {
  std::vector<graph::ParameterBinding> values;
};

class EffectRegistry {
 public:
  EffectRegistry() = default;
  explicit EffectRegistry(const EffectCatalog& catalog);
  explicit EffectRegistry(std::vector<EffectDefinition> definitions);

  EffectRegistry& register_effect(EffectDefinition definition);
  EffectRegistry& register_definition(const EffectDefinition& definition) { return register_effect(definition); }

  [[nodiscard]] const EffectDefinition* get(std::string_view name_space, std::string_view function) const noexcept;
  [[nodiscard]] const EffectDefinition* resolve(std::string_view function,
                                                 const std::vector<std::string>& search) const noexcept;
  [[nodiscard]] std::vector<const EffectDefinition*> list() const;
  [[nodiscard]] NormalizedArguments normalize(const EffectDefinition& definition,
                                               const std::vector<ParameterArgument>& arguments) const;
  [[nodiscard]] NormalizedArguments normalize_arguments(const EffectDefinition& definition,
                                                         const std::vector<ParameterArgument>& arguments) const {
    return normalize(definition, arguments);
  }
  [[nodiscard]] graph::PassAdmission admission(const EffectDefinition& definition,
                                                std::size_t pass_index) const;
  [[nodiscard]] const std::vector<ProgramCompatibility>& compatibility() const noexcept { return canonical_programs_; }
  [[nodiscard]] const std::vector<ReferencePassCompatibility>& reference_passes() const noexcept { return reference_passes_; }
  [[nodiscard]] const CatalogProvenance& provenance() const noexcept { return provenance_; }
  [[nodiscard]] bool manifest_backed() const noexcept { return manifest_backed_; }

 private:
  std::vector<EffectDefinition> definitions_;
  std::vector<ProgramCompatibility> canonical_programs_;
  std::vector<ReferencePassCompatibility> reference_passes_;
  std::optional<ScatterCompatibility> scatter_;
  std::vector<graph::PassAdmission> canonical_views_;
  CatalogProvenance provenance_;
  bool manifest_backed_ = false;
};

}  // namespace noisemaker::effects
