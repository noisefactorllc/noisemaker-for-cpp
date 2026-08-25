#pragma once

#include "noisemaker/effects/catalog_types.hpp"

#include <string>
#include <optional>
#include <unordered_map>

namespace noisemaker::effects {

struct EffectCatalog {
  EffectCatalog() = default;

  // Copying a generated catalog intentionally drops its private production
  // capability. A copied catalog is caller-owned data and cannot be used to
  // claim authenticated manifest provenance, even when its fields are
  // otherwise unchanged.
  EffectCatalog(const EffectCatalog& other)
      : definitions(other.definitions), canonical_programs(other.canonical_programs),
        reference_passes(other.reference_passes), scatter(other.scatter), provenance(other.provenance) {}

  EffectCatalog& operator=(const EffectCatalog& other) {
    if (this != &other) {
      definitions = other.definitions;
      canonical_programs = other.canonical_programs;
      reference_passes = other.reference_passes;
      scatter = other.scatter;
      provenance = other.provenance;
      index.clear();
      production_capability_ = false;
    }
    return *this;
  }

  EffectCatalog(EffectCatalog&&) noexcept = default;
  EffectCatalog& operator=(EffectCatalog&&) noexcept = default;

  std::vector<EffectDefinition> definitions;
  std::vector<ProgramCompatibility> canonical_programs;
  std::vector<ReferencePassCompatibility> reference_passes;
  std::optional<ScatterCompatibility> scatter;
  CatalogProvenance provenance;

  const EffectDefinition* find(const std::string& id) const;

 private:
  struct ProductionToken {};
  explicit EffectCatalog(ProductionToken) : production_capability_(true) {}
  friend const EffectCatalog& effect_catalog();
  friend class EffectRegistry;

  mutable std::unordered_map<std::string, std::size_t> index;
  bool production_capability_ = false;
};

const EffectCatalog& effect_catalog();

}  // namespace noisemaker::effects
