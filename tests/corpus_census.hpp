#pragma once

// Catalog cardinalities and ordinals derived from the generated compatibility
// catalog instead of pinned literals ("213 entries", "julia is ordinal 195").
// The compatibility catalog is generated from the pinned corpus, whose
// vendored/pending split is closed over the JS authority's program set by
// tools/glslcpp/corpus_ratchet.py; the typed catalog these tests inspect is
// produced by a different generator (generate_typed_slice.py), so comparing
// the two is a real cross-check, not a restatement.

#include <algorithm>
#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

#include "noisemaker/effects/catalog.hpp"

namespace corpus_census {

// Multi-output programs are published only through the MRT route table.
[[nodiscard]] inline std::size_t output_count(const noisemaker::effects::ProgramCompatibility& row) {
  for (const auto& [name, value] : row.raw) {
    if (name == "outputs") return value.array.size();
  }
  return 0U;
}

// Every canonical single-output program key, sorted.
[[nodiscard]] inline std::vector<std::string> single_output_program_keys() {
  std::vector<std::string> keys;
  for (const auto& row : noisemaker::effects::effect_catalog().canonical_programs) {
    if (output_count(row) == 1U) keys.push_back(row.program_key);
  }
  std::sort(keys.begin(), keys.end());
  return keys;
}

// Every canonical multi-output program key, sorted.
[[nodiscard]] inline std::vector<std::string> mrt_program_keys() {
  std::vector<std::string> keys;
  for (const auto& row : noisemaker::effects::effect_catalog().canonical_programs) {
    if (output_count(row) > 1U) keys.push_back(row.program_key);
  }
  std::sort(keys.begin(), keys.end());
  return keys;
}

// The typed KernelFactory catalog's exact sorted key sequence: every
// single-output program plus the second physical row of the two programs
// also dispatched through a hand-written legacy factory.
[[nodiscard]] inline std::vector<std::string> expected_catalog_keys() {
  auto keys = single_output_program_keys();
  keys.emplace_back("filter/invert:inv");
  keys.emplace_back("synth/solid:solid");
  std::sort(keys.begin(), keys.end());
  return keys;
}

// A key's first ordinal in the typed KernelFactory catalog.
[[nodiscard]] inline std::size_t catalog_ordinal(std::string_view key) {
  const auto keys = expected_catalog_keys();
  return static_cast<std::size_t>(std::find(keys.begin(), keys.end(), key) - keys.begin());
}

}  // namespace corpus_census
