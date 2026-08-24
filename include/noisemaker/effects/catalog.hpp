#pragma once

#include "noisemaker/effects/catalog_types.hpp"

#include <string>
#include <unordered_map>

namespace noisemaker::effects {

struct EffectCatalog {
  std::vector<EffectDefinition> definitions;
  std::vector<ProgramCompatibility> compatibility;
  CatalogProvenance provenance;

  const EffectDefinition* find(const std::string& id) const;

 private:
  mutable std::unordered_map<std::string, std::size_t> index;
};

const EffectCatalog& effect_catalog();

}  // namespace noisemaker::effects
