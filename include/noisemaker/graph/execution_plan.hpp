#pragma once

#include "noisemaker/dsl/error.hpp"

#include <cstddef>
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
  std::vector<CompatibilityBinding> outputs;
};

struct ReadStep { SurfaceReference surface; dsl::SourceLocation loc{}; };
struct WriteStep { SurfaceReference surface; dsl::SourceLocation loc{}; };
struct EffectStep {
  EffectIdentity effect;
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
  std::vector<ExecutionChain> chains;
  SurfaceReference render_surface;
  bool require_executable = false;
  bool executable = false;
  std::vector<PassAdmission> availability;
};

}  // namespace noisemaker::graph
