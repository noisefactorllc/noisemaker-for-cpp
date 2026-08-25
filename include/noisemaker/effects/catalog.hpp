#pragma once

#include "noisemaker/effects/catalog_types.hpp"

#include <string>
#include <optional>
#include <unordered_map>

namespace noisemaker::effects {

struct EffectCatalog {
  std::vector<EffectDefinition> definitions;
  std::vector<ProgramCompatibility> canonical_programs;
  std::vector<ReferencePassCompatibility> reference_passes;
  std::optional<ScatterCompatibility> scatter;
  CatalogProvenance provenance;

  const EffectDefinition* find(const std::string& id) const;

 private:
  mutable std::unordered_map<std::string, std::size_t> index;
};

const EffectCatalog& effect_catalog();

}  // namespace noisemaker::effects
