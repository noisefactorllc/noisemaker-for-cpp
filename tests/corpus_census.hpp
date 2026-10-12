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

// One canonical token per JSON value. The binding-projection distinctness key
// below mirrors tests/corpus_census.py's `json.dumps(..., sort_keys=True)`
// hashing of the same sections; the token does not sort keys because the
// generated catalog preserves the compatibility document's field order, which
// one generation pins.
[[nodiscard]] inline std::string projection_token(
    const noisemaker::effects::Value& value) {
  using noisemaker::effects::Value;
  using noisemaker::effects::ValueKind;
  switch (value.kind) {
    case ValueKind::null_value: return "null";
    case ValueKind::boolean: return value.boolean ? "1" : "0";
    case ValueKind::number: return std::to_string(value.number);
    case ValueKind::string: return "\"" + value.string + "\"";
    case ValueKind::array: {
      std::string token = "[";
      for (const auto& entry : value.array) token += projection_token(entry) + ",";
      return token + "]";
    }
    case ValueKind::object: {
      std::string token = "{";
      for (const auto& entry : value.object)
        token += "\"" + entry.first + "\":" + projection_token(entry.second) + ",";
      return token + "}";
    }
  }
  return "null";
}

// The value of one object member, or null when absent.
[[nodiscard]] inline noisemaker::effects::Value projection_member(
    const std::vector<std::pair<std::string, noisemaker::effects::Value>>& entries,
    std::string_view key) {
  for (const auto& entry : entries)
    if (entry.first == key) return entry.second;
  return noisemaker::effects::Value::null();
}

[[nodiscard]] inline noisemaker::effects::Value projection_member(
    const noisemaker::effects::Value& value, std::string_view key) {
  using noisemaker::effects::Value;
  using noisemaker::effects::ValueKind;
  if (value.kind != ValueKind::object) return Value::null();
  for (const auto& entry : value.object)
    if (entry.first == key) return entry.second;
  return Value::null();
}

// Multi-output programs are published only through the MRT route table.
[[nodiscard]] inline std::size_t output_count(const noisemaker::effects::ProgramCompatibility& row) {
  for (const auto& [name, value] : row.raw) {
    if (name == "outputs") return value.array.size();
  }
  return 0U;
}

// Every fragment factory with one output, excluding the mesh whole-pass route.
[[nodiscard]] inline std::vector<std::string> single_output_program_keys() {
  std::vector<std::string> keys;
  for (const auto& row : noisemaker::effects::effect_catalog().canonical_programs) {
    if (output_count(row) == 1U && row.program_key != "render/meshRender:render")
      keys.push_back(row.program_key);
  }
  std::sort(keys.begin(), keys.end());
  return keys;
}

// Expected single-output canonical route rows: one row per program, plus one
// extra row per additional DISTINCT binding projection of a multi-bound
// program. The generated route table shares one row among bindings whose
// whole descriptor is byte-identical -- the executor refuses a byte-identical
// duplicate of a descriptor as a generation defect -- so extras count
// distinct projections, not bindings. The projection distinctness reads the
// row's preserved compatibility JSON (raw) and hashes the same three sections
// the python census hashes: the binding's samplers (falling back to the row's
// when the binding carries none), its ordered outputs, and its output extent.
[[nodiscard]] inline std::size_t expected_single_output_route_rows() {
  using noisemaker::effects::ValueKind;
  std::size_t rows = 0;
  for (const auto& row : noisemaker::effects::effect_catalog().canonical_programs) {
    if (output_count(row) == 1U && row.program_key != "render/meshRender:render") {
      const auto raw_row = projection_member(row.raw, "binding_outputs");
      const auto row_samplers = projection_member(row.raw, "samplers");
      if (raw_row.kind != ValueKind::array || raw_row.array.empty()) {
        rows += 1U;
        continue;
      }
      std::vector<std::string> distinct;
      for (const auto& binding : raw_row.array) {
        auto samplers = projection_member(binding, "samplers");
        if (samplers.kind == ValueKind::null_value) samplers = row_samplers;
        const std::string projection = projection_token(samplers) + "\x1f" +
            projection_token(projection_member(binding, "outputs")) + "\x1f" +
            projection_token(projection_member(binding, "extent"));
        if (std::find(distinct.begin(), distinct.end(), projection)
            == distinct.end())
          distinct.push_back(projection);
      }
      rows += distinct.size();
    }
  }
  return rows;
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
