#pragma once

#include "noisemaker/effects/catalog_types.hpp"
#include "noisemaker/dsl/error.hpp"

#include <cstddef>
#include <array>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace noisemaker::graph {

struct SurfaceReference {
  enum class Kind { none, input, named };
  Kind kind = Kind::none;
  std::string name;
  std::size_t index = 0;
  dsl::SourceLocation loc{};

  static SurfaceReference none(dsl::SourceLocation loc = {}) { return {Kind::none, {}, 0, std::move(loc)}; }
  static SurfaceReference input(dsl::SourceLocation loc = {}) { return {Kind::input, {}, 0, std::move(loc)}; }
  static SurfaceReference named(std::string value, std::size_t surface_index,
                                dsl::SourceLocation loc = {}) {
    return {Kind::named, std::move(value), surface_index, std::move(loc)};
  }
};

struct PlanValue {
  enum class Kind { null_value, boolean, number, string, array, surface };
  Kind kind = Kind::null_value;
  bool boolean = false;
  double number = 0.0;
  std::string string;
  std::vector<PlanValue> array;
  SurfaceReference surface{};

  static PlanValue null() { return {}; }
  static PlanValue boolean_value(bool value) { PlanValue result; result.kind = Kind::boolean; result.boolean = value; return result; }
  static PlanValue number_value(double value) { PlanValue result; result.kind = Kind::number; result.number = value; return result; }
  static PlanValue string_value(std::string value) { PlanValue result; result.kind = Kind::string; result.string = std::move(value); return result; }
  static PlanValue array_value(std::vector<PlanValue> value) { PlanValue result; result.kind = Kind::array; result.array = std::move(value); return result; }
  static PlanValue surface_value(SurfaceReference value) { PlanValue result; result.kind = Kind::surface; result.surface = std::move(value); return result; }
};

struct ParameterBinding { std::string name; PlanValue value; };
struct EffectIdentity { std::string id; std::string domain; std::string kind; };
struct PassIdentity { std::size_t index = 0; std::string name; std::string program_key; };

struct AvailabilityReason { std::string code; std::string detail; };
enum class AvailabilityStatus { compatible, scatter, missing, incompatible };
struct CompatibilityBinding {
  std::string name;
  std::string type;
  std::string source;
  std::string source_name;
  std::string resource;
  std::string cpp_type;
};

struct AuthorityPassMetadata {
  std::string name;
  std::vector<std::pair<std::string, std::string>> inputs;
  std::vector<std::pair<std::string, std::string>> outputs;
  std::vector<std::pair<std::string, PlanValue>> uniforms;
  std::string blend_kind;
  bool blend = false;
  std::array<std::string, 2> blend_factors{};
  std::optional<PlanValue> repeat;
};

struct CompatibilityOutput {
  std::size_t slot = 0;
  std::string physical_name;
  std::string logical_route;
  std::string cpp_type;
};

using ScatterOutput = CompatibilityOutput;

struct ScatterContract {
  std::string adapter;
  std::string registry;
  std::string draw_mode;
  std::string dimensionality;
  std::string count;
  std::string input_texture;
  std::string destination_mutation;
  bool blend = false;
  std::vector<CompatibilityBinding> uniforms;
  std::vector<CompatibilityOutput> outputs;
};

struct PassAdmission {
  PassIdentity identity;
  AvailabilityStatus status = AvailabilityStatus::missing;
  std::vector<AvailabilityReason> reasons;
  std::string canonical_factory;
  std::string source_sha256;
  std::string semantic_sha256;
  std::vector<std::string> capabilities;
  std::string dimensionality;
  std::string draw_mode;
  std::vector<CompatibilityBinding> samplers;
  std::vector<CompatibilityBinding> uniforms;
  std::vector<CompatibilityOutput> outputs;
  AuthorityPassMetadata authority_pass;
  std::optional<ScatterContract> scatter;
};

struct PlanProvenance {
  // Exact source identity and the canonical execution payload identity. These
  // are copied into a plan and never derived from a live registry at execute.
  std::string source_sha256;
  std::string source_name;
  std::string plan_payload_sha256;
  std::string kind;
  std::string schema;
  std::string backend_schema;
  std::string corpus_revision;
  std::string generated_payload_sha256;
  std::string normalized_record_stream_sha256;
  std::string authority_lock;
  std::string cpu_revision;
  std::string source_lock_sha256;
  std::string cpu_package_sha256;
  std::string cpu_package_lock_sha256;
  std::string cpu_source_lock_sha256;
  std::string upstream_revision;
  std::string upstream_package_sha256;
  std::string upstream_package_lock_sha256;
  std::string upstream_tree;
  std::string compatibility_sha256;
  struct Counts {
    std::size_t definitions = 0;
    std::size_t passes = 0;
    std::size_t reference_program_keys = 0;
    std::size_t backend_programs = 0;
    std::size_t compatible_programs = 0;
    std::size_t incompatible_programs = 0;
    std::size_t missing_passes = 0;
    std::size_t scatter_passes = 0;
    std::size_t executable_definitions = 0;
    std::size_t incomplete_definitions = 0;
  } counts;
};

struct PlanEffectSnapshot {
  effects::EffectDefinition definition;
  std::vector<PassAdmission> admissions;
  std::string snapshot_sha256;
};

struct ReadStep { SurfaceReference surface; dsl::SourceLocation loc{}; };
struct WriteStep { SurfaceReference surface; dsl::SourceLocation loc{}; };
struct EffectStep {
  EffectIdentity effect;
  std::size_t snapshot_index = 0;
  std::vector<ParameterBinding> params;
  std::vector<std::string> explicit_params;
  std::vector<PassAdmission> passes;
  dsl::SourceLocation loc{};
};
using CompiledStep = std::variant<ReadStep, EffectStep, WriteStep>;

struct ExecutionChain {
  std::vector<CompiledStep> steps;
  dsl::SourceLocation loc{};
};

struct ExecutionPlan {
  std::vector<std::string> search;
  std::vector<PlanEffectSnapshot> effects;
  std::vector<ExecutionChain> chains;
  SurfaceReference render_surface;
  bool require_executable = false;
  bool executable = false;
  std::vector<PassAdmission> availability;
  PlanProvenance provenance;
};

// Returns true only when every owned snapshot, step reference, and the plan
// payload authenticate against their canonical value-owned bytes.
[[nodiscard]] bool validate_execution_plan(const ExecutionPlan& plan) noexcept;

// Canonical hashes are exposed for source-bound oracle projections and for
// execution-side diagnostics; both operate only on value-owned plan data.
namespace detail {
[[nodiscard]] std::string admission_sha256(const PassAdmission& admission);
[[nodiscard]] std::string snapshot_sha256(const PlanEffectSnapshot& snapshot);
[[nodiscard]] std::string plan_payload_sha256(const ExecutionPlan& plan);
}  // namespace detail

}  // namespace noisemaker::graph
