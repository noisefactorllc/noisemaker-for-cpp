#include "noisemaker/graph/executor.hpp"

#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/texture_format.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstdlib>
#include <initializer_list>
#include <locale.h>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>

namespace noisemaker::graph {
namespace {

[[nodiscard]] bool parse_c_number(std::string_view text, double& value) {
  const std::string owned(text);
  char* end = nullptr;
#if defined(_WIN32)
  _locale_t c_locale = _create_locale(LC_NUMERIC, "C");
  if (c_locale == nullptr) {
    throw std::runtime_error("failed to create C numeric locale");
  }
  value = _strtod_l(owned.c_str(), &end, c_locale);
  _free_locale(c_locale);
#else
  locale_t c_locale = newlocale(LC_NUMERIC_MASK, "C", static_cast<locale_t>(0));
  if (c_locale == nullptr) {
    throw std::runtime_error("failed to create C numeric locale");
  }
  value = strtod_l(owned.c_str(), &end, c_locale);
  freelocale(c_locale);
#endif
  return end == owned.c_str() + owned.size();
}

const char* code_name(GraphErrorCode code) noexcept {
  switch (code) {
    case GraphErrorCode::invalid_options: return "invalid_options";
    case GraphErrorCode::invalid_dimension: return "invalid_dimension";
    case GraphErrorCode::allocation_limit: return "allocation_limit";
    case GraphErrorCode::invalid_format: return "invalid_format";
    case GraphErrorCode::missing_resource: return "missing_resource";
    case GraphErrorCode::read_before_write: return "read_before_write";
    case GraphErrorCode::duplicate_output: return "duplicate_output";
    case GraphErrorCode::unavailable_pass: return "unavailable_pass";
    case GraphErrorCode::invalid_snapshot: return "invalid_snapshot";
    case GraphErrorCode::missing_binding: return "missing_binding";
    case GraphErrorCode::binding_type: return "binding_type";
    case GraphErrorCode::unsupported_blend: return "unsupported_blend";
    case GraphErrorCode::unsupported_mrt: return "unsupported_mrt";
    case GraphErrorCode::unsupported_draw_mode: return "unsupported_draw_mode";
    case GraphErrorCode::unsupported_scatter: return "unsupported_scatter";
    case GraphErrorCode::execution_failure: return "execution_failure";
  }
  return "execution_failure";
}

[[nodiscard]] const PlanValue* parameter(const EffectStep& step,
                                         std::string_view name) {
  for (const auto& item : step.params) {
    if (item.name == name) return &item.value;
  }
  return nullptr;
}

[[nodiscard]] double number(const PlanValue& value, std::string_view label) {
  if (value.kind != PlanValue::Kind::number || !std::isfinite(value.number)) {
    throw std::invalid_argument("numeric binding " + std::string(label) + " is invalid");
  }
  return value.number;
}

[[nodiscard]] double plan_number(const PlanValue* value) {
  if (value == nullptr) return std::numeric_limits<double>::quiet_NaN();
  if (value->kind == PlanValue::Kind::number) return value->number;
  if (value->kind == PlanValue::Kind::boolean) return value->boolean ? 1.0 : 0.0;
  if (value->kind == PlanValue::Kind::string) {
    if (value->string.empty()) return 0.0;
    double parsed = 0.0;
    if (parse_c_number(value->string, parsed)) return parsed;
  }
  return std::numeric_limits<double>::quiet_NaN();
}

[[nodiscard]] double catalog_number(const effects::Value& value,
                                    const EffectStep* step = nullptr) {
  if (value.kind == effects::ValueKind::number) return value.number;
  if (value.kind == effects::ValueKind::boolean) return value.boolean ? 1.0 : 0.0;
  if (value.kind == effects::ValueKind::string) {
    if (step != nullptr) {
      if (const auto* bound = parameter(*step, value.string); bound != nullptr) {
        return plan_number(bound);
      }
    }
    if (value.string.empty()) return 0.0;
    double parsed = 0.0;
    if (parse_c_number(value.string, parsed)) return parsed;
  }
  return std::numeric_limits<double>::quiet_NaN();
}

[[nodiscard]] std::optional<double> optional_uniform_number(
    const effects::PassDefinition& pass, const EffectStep& step,
    std::string_view uniform_name) {
  for (const auto& uniform : pass.uniforms) {
    if (uniform.first == uniform_name) {
      return catalog_number(uniform.second, &step);
    }
  }
  const auto* bound = parameter(step, uniform_name);
  if (bound == nullptr) return std::nullopt;
  return plan_number(bound);
}

[[nodiscard]] double uniform_number(const effects::PassDefinition& pass,
                                    const EffectStep& step,
                                    std::string_view uniform_name) {
  return optional_uniform_number(pass, step, uniform_name)
      .value_or(std::numeric_limits<double>::quiet_NaN());
}

[[nodiscard]] bool pass_enabled(const effects::PassDefinition& pass,
                                const EffectStep& step) {
  if (!pass.conditions.has_value()) return true;
  if (pass.conditions->kind != effects::ValueKind::object) {
    throw std::invalid_argument("pass conditions must be an object");
  }
  for (const auto& group : pass.conditions->object) {
    if (group.first != "runIf" && group.first != "skipIf") {
      throw std::invalid_argument("unknown pass condition");
    }
    if (group.second.kind != effects::ValueKind::array) {
      throw std::invalid_argument("pass condition group must be an array");
    }
    for (const auto& rule : group.second.array) {
      if (rule.kind != effects::ValueKind::object) {
        throw std::invalid_argument("pass condition rule must be an object");
      }
      const effects::Value* uniform = nullptr;
      const effects::Value* equals = nullptr;
      for (const auto& field : rule.object) {
        if (field.first == "uniform") uniform = &field.second;
        else if (field.first == "equals") equals = &field.second;
        else throw std::invalid_argument("unknown pass condition field");
      }
      if (uniform == nullptr || uniform->kind != effects::ValueKind::string ||
          equals == nullptr) {
        throw std::invalid_argument("pass condition rule is incomplete");
      }
      const bool equal = uniform_number(pass, step, uniform->string) ==
                         catalog_number(*equals);
      if (group.first == "runIf" && !equal) return false;
      if (group.first == "skipIf" && equal) return false;
    }
  }
  return true;
}

[[nodiscard]] std::size_t pass_repeat(const effects::PassDefinition& pass,
                                      const EffectStep& step) {
  if (!pass.repeat.has_value()) return 1U;
  double value = 0.0;
  const bool uniform_repeat = pass.repeat->kind == effects::ValueKind::string;
  if (pass.repeat->kind == effects::ValueKind::number) value = pass.repeat->number;
  else if (pass.repeat->kind == effects::ValueKind::string) {
    value = optional_uniform_number(pass, step, pass.repeat->string)
                .value_or(1.0);
    if (!std::isfinite(value)) {
      throw std::invalid_argument("repeat uniform is not finite");
    }
    value = std::trunc(value);
  } else {
    throw std::invalid_argument("repeat must be numeric or a uniform name");
  }
  if (!std::isfinite(value)) {
    throw std::invalid_argument("repeat is not finite");
  }
  if (value <= 0.0) return 0U;
  const double count = uniform_repeat ? value : std::ceil(value);
  constexpr double kMaxSafeInteger = 9007199254740991.0;
  if (count > kMaxSafeInteger ||
      count > static_cast<double>(std::numeric_limits<std::size_t>::max())) {
    throw std::overflow_error("repeat exceeds representable range");
  }
  return static_cast<std::size_t>(count);
}

[[nodiscard]] double parse_percentage(std::string_view raw) {
  // This is the authority's exact percentage grammar:
  // ^(\d+(?:\.\d+)?)%$
  if (raw.size() < 2U || raw.back() != '%') {
    throw std::invalid_argument("unsupported percentage dimension");
  }
  const auto number_text = raw.substr(0, raw.size() - 1U);
  if (number_text.empty() || number_text.front() == '.' ||
      number_text.back() == '.' ||
      number_text.find_first_not_of("0123456789.") != std::string_view::npos ||
      number_text.find('.') != number_text.rfind('.')) {
    throw std::invalid_argument("unsupported percentage dimension");
  }
  double percent = 0.0;
  if (!parse_c_number(number_text, percent) || !std::isfinite(percent)) {
    throw std::invalid_argument("unsupported percentage dimension");
  }
  return percent;
}

[[nodiscard]] std::size_t rounded_dimension(double value) {
  if (!std::isfinite(value)) throw std::invalid_argument("dimension is not finite");
  constexpr double kMaxSafeInteger = 9007199254740991.0; // Number.MAX_SAFE_INTEGER
  if (value > kMaxSafeInteger) {
    throw std::invalid_argument("dimension exceeds safe integer range");
  }
  return checked_dimension(std::max(1.0, std::floor(value + 0.5)));
}

[[nodiscard]] const effects::TextureDefinition* texture_for(
    const effects::EffectDefinition& definition, std::string_view name) {
  for (const auto& texture : definition.textures) {
    if (texture.name == name) return &texture;
  }
  return nullptr;
}

[[nodiscard]] std::size_t resolve_dimension(
    const effects::DimensionExpression& expression, const EffectStep& step,
    const ResourceArena& arena, std::size_t render_extent,
    bool width) {
  if (!expression.input_override.empty()) {
    try {
      const auto& resource = arena.require(expression.input_override);
      return width ? resource.width() : resource.height();
    } catch (const std::invalid_argument&) {
      // The JavaScript authority falls through to the parameter/default arm
      // when an inputOverride route is absent.
    }
  }
  double value = static_cast<double>(render_extent);
  switch (expression.kind) {
    case effects::DimensionKind::input:
    case effects::DimensionKind::screen:
    case effects::DimensionKind::resolution:
      value = static_cast<double>(render_extent);
      break;
    case effects::DimensionKind::literal:
      value = expression.literal;
      break;
    case effects::DimensionKind::parameter: {
      const auto* bound = parameter(step, expression.parameter);
      if (bound == nullptr) throw std::invalid_argument("dimension parameter is missing");
      value = number(*bound, expression.parameter);
      break;
    }
    case effects::DimensionKind::parameter_default:
      value = expression.default_value;
      if (const auto* bound = parameter(step, expression.parameter); bound != nullptr) {
        value = number(*bound, expression.parameter);
      }
      break;
    case effects::DimensionKind::power: {
      // The catalog's `default` is already the powered fallback (for
      // example volumeSize default 1024 for a 32^2 atlas). Apply the power
      // only to a normalized parameter override.
      if (const auto* bound = parameter(step, expression.parameter); bound != nullptr) {
        value = std::pow(number(*bound, expression.parameter),
                         static_cast<double>(expression.power));
      } else {
        value = expression.default_value;
      }
      break;
    }
    case effects::DimensionKind::screen_division: {
      if (expression.raw.kind == effects::ValueKind::string &&
          !expression.raw.string.empty() && expression.raw.string.back() == '%') {
        value = static_cast<double>(render_extent) *
                parse_percentage(expression.raw.string) / 100.0;
      } else {
        value = expression.default_value;
        if (const auto* bound = parameter(step, expression.parameter); bound != nullptr) {
          value = number(*bound, expression.parameter);
        }
        if (value <= 0.0 || !std::isfinite(value)) {
          throw std::invalid_argument("screen division is invalid");
        }
        value = std::ceil(static_cast<double>(render_extent) /
                          std::max(1.0, value));
      }
      break;
    }
    case effects::DimensionKind::unknown: {
      if (expression.raw.kind == effects::ValueKind::string) {
        const auto& raw = expression.raw.string;
        if (raw == "input" || raw == "screen" || raw == "resolution" || raw == "100%") {
          value = static_cast<double>(render_extent);
          break;
        }
        if (!raw.empty() && raw.back() == '%') {
          value = static_cast<double>(render_extent) * parse_percentage(raw) / 100.0;
          break;
        }
      }
      throw std::invalid_argument("unsupported dimension expression");
    }
  }
  (void)width;
  return rounded_dimension(value);
}

enum class SamplerAbiStatus { valid, missing_binding, binding_type };
enum class UniformAbiStatus { valid, missing_binding, binding_type };

[[nodiscard]] SamplerAbiStatus task6_sampler_abi_status(
    const effects::PassDefinition& pass, const PassAdmission& admission) {
  if (pass.inputs.size() != admission.samplers.size() ||
      pass.inputs.size() > 1U) {
    return SamplerAbiStatus::missing_binding;
  }
  for (std::size_t index = 0; index < pass.inputs.size(); ++index) {
    const auto& input = pass.inputs[index];
    const auto& sampler = admission.samplers[index];
    if (sampler.type != "sampler2D" ||
        sampler.cpp_type != "const Surface&") {
      return SamplerAbiStatus::binding_type;
    }
    if (sampler.name != input.first || sampler.source != "resource" ||
        !sampler.source_name.empty() || sampler.resource != input.second) {
      return SamplerAbiStatus::missing_binding;
    }
  }
  return SamplerAbiStatus::valid;
}

[[nodiscard]] bool catalog_value_matches_plan(const effects::Value& catalog,
                                              const PlanValue& plan) {
  switch (catalog.kind) {
    case effects::ValueKind::null_value:
      return plan.kind == PlanValue::Kind::null_value;
    case effects::ValueKind::boolean:
      return plan.kind == PlanValue::Kind::boolean &&
             plan.boolean == catalog.boolean;
    case effects::ValueKind::number:
      return plan.kind == PlanValue::Kind::number &&
             std::bit_cast<std::uint64_t>(plan.number) ==
                 std::bit_cast<std::uint64_t>(catalog.number);
    case effects::ValueKind::string:
      return plan.kind == PlanValue::Kind::string &&
             plan.string == catalog.string;
    case effects::ValueKind::array:
      if (plan.kind != PlanValue::Kind::array ||
          plan.array.size() != catalog.array.size()) {
        return false;
      }
      for (std::size_t index = 0; index < catalog.array.size(); ++index) {
        if (!catalog_value_matches_plan(catalog.array[index],
                                        plan.array[index])) {
          return false;
        }
      }
      return true;
    case effects::ValueKind::object: {
      const effects::Value* kind = nullptr;
      const effects::Value* name = nullptr;
      const effects::Value* index = nullptr;
      for (const auto& field : catalog.object) {
        if (field.first == "kind") kind = &field.second;
        else if (field.first == "name") name = &field.second;
        else if (field.first == "index") index = &field.second;
      }
      if (kind != nullptr && kind->kind == effects::ValueKind::string &&
          kind->string == "input") {
        return plan.kind == PlanValue::Kind::surface &&
               plan.surface.kind == SurfaceReference::Kind::input;
      }
      if (kind != nullptr && kind->kind == effects::ValueKind::string &&
          kind->string == "surface" && name != nullptr && index != nullptr &&
          name->kind == effects::ValueKind::string &&
          index->kind == effects::ValueKind::number &&
          std::isfinite(index->number) && index->number >= 0.0 &&
          std::trunc(index->number) == index->number) {
        return plan.kind == PlanValue::Kind::surface &&
               plan.surface.kind == SurfaceReference::Kind::named &&
               plan.surface.name == name->string &&
               plan.surface.index == static_cast<std::size_t>(index->number);
      }
      return plan.kind == PlanValue::Kind::null_value;
    }
  }
  return false;
}

[[nodiscard]] bool authority_uniforms_match(
    const effects::PassDefinition& pass,
    const AuthorityPassMetadata& authority) {
  if (pass.uniforms.size() != authority.uniforms.size()) return false;
  for (std::size_t index = 0; index < pass.uniforms.size(); ++index) {
    if (pass.uniforms[index].first != authority.uniforms[index].first ||
        !catalog_value_matches_plan(pass.uniforms[index].second,
                                    authority.uniforms[index].second)) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool authority_blend_matches(
    const effects::PassDefinition& pass,
    const AuthorityPassMetadata& authority) {
  if (!pass.blend.has_value()) {
    return authority.blend_kind == "none" && !authority.blend &&
           authority.blend_factors[0].empty() &&
           authority.blend_factors[1].empty();
  }
  if (pass.blend->kind == effects::BlendKind::boolean) {
    return authority.blend_kind == "boolean" &&
           authority.blend == pass.blend->enabled &&
           authority.blend_factors[0].empty() &&
           authority.blend_factors[1].empty();
  }
  return authority.blend_kind == "factors" && authority.blend &&
         authority.blend_factors == pass.blend->factors;
}

[[nodiscard]] bool authority_repeat_matches(
    const effects::PassDefinition& pass,
    const AuthorityPassMetadata& authority) {
  if (pass.repeat.has_value() != authority.repeat.has_value()) return false;
  return !pass.repeat.has_value() ||
         catalog_value_matches_plan(*pass.repeat, *authority.repeat);
}

void validate_sampler_abi(const effects::PassDefinition& pass,
                          const PassAdmission& admission,
                          std::string_view effect_id,
                          std::size_t pass_index) {
  const auto status = task6_sampler_abi_status(pass, admission);
  if (status == SamplerAbiStatus::valid) return;
  throw GraphError(
      status == SamplerAbiStatus::binding_type
          ? GraphErrorCode::binding_type
          : GraphErrorCode::missing_binding,
      status == SamplerAbiStatus::binding_type
          ? "sampler ABI type is invalid"
          : "sampler ABI route is invalid",
      std::string(effect_id), pass_index, pass.name,
      std::string(effect_id) + ":" + pass.program);
}

[[nodiscard]] UniformAbiStatus uniform_abi_status(
    const PassAdmission& admission,
    std::initializer_list<CompatibilityBinding> expected) {
  if (admission.uniforms.size() != expected.size()) {
    return UniformAbiStatus::missing_binding;
  }
  std::size_t index = 0;
  for (const auto& binding : expected) {
    const auto& actual = admission.uniforms[index++];
    if (actual.type != binding.type || actual.cpp_type != binding.cpp_type) {
      return UniformAbiStatus::binding_type;
    }
    if (actual.name != binding.name || actual.source != binding.source ||
        actual.source_name != binding.source_name ||
        actual.resource != binding.resource) {
      return UniformAbiStatus::missing_binding;
    }
  }
  return UniformAbiStatus::valid;
}

void validate_uniform_abi(
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass,
    std::initializer_list<CompatibilityBinding> expected) {
  const auto status = uniform_abi_status(admission, expected);
  if (status == UniformAbiStatus::valid) return;
  throw GraphError(
      status == UniformAbiStatus::binding_type
          ? GraphErrorCode::binding_type
          : GraphErrorCode::missing_binding,
      status == UniformAbiStatus::binding_type
          ? "uniform ABI type is invalid"
          : "uniform ABI structure is invalid",
      step.effect.id, admission.identity.index, pass.name,
      admission.identity.program_key);
}

void validate_ordinary_pass_metadata(const EffectStep& step,
                                     const PassAdmission& admission,
                                     const effects::PassDefinition& pass,
                                     std::size_t pass_index) {
  if (pass.count.has_value() || pass.viewport.has_value()) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "ordinary count or viewport is unsupported",
                     step.effect.id, pass_index, pass.name,
                     admission.identity.program_key);
  }
}

void validate_pass_identity_and_output(
    const EffectStep& step, const effects::EffectDefinition& definition,
    const effects::PassDefinition& pass, const PassAdmission& admission,
    std::size_t pass_index) {
  const std::string expected_program_key =
      definition.id + ":" + pass.program;
  if (step.effect.id != definition.id ||
      admission.identity.index != pass_index ||
      admission.identity.name != pass.name ||
      admission.identity.program_key != expected_program_key) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass identity differs from owned definition",
                     definition.id, pass_index, pass.name,
                     expected_program_key);
  }
  if (admission.authority_pass.name != pass.name ||
      admission.authority_pass.inputs != pass.inputs ||
      admission.authority_pass.outputs != pass.outputs ||
      !authority_uniforms_match(pass, admission.authority_pass) ||
      !authority_blend_matches(pass, admission.authority_pass) ||
      !authority_repeat_matches(pass, admission.authority_pass) ||
      pass.outputs.size() != 1U || admission.outputs.size() != 1U) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass routing differs from admitted ABI",
                     definition.id, pass_index, pass.name,
                     expected_program_key);
  }
  const auto& pass_output = pass.outputs.front();
  const auto& abi_output = admission.outputs.front();
  const bool solid = definition.id == "synth/solid" && pass.program == "solid";
  const bool blur_h = definition.id == "filter/blur" && pass.program == "blurH";
  const bool blur_v = definition.id == "filter/blur" && pass.program == "blurV";
  const std::string_view expected_pass_physical = solid ? "color" : "fragColor";
  const std::string_view expected_logical_route = blur_h ? "_blurTemp" : "outputTex";
  if ((!solid && !blur_h && !blur_v) ||
      pass_output.first != expected_pass_physical ||
      pass_output.second != expected_logical_route ||
      abi_output.slot != 0U || abi_output.physical_name != "fragColor" ||
      abi_output.logical_route != expected_logical_route ||
      abi_output.cpp_type != "glsl::Vec4") {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass output ABI differs from owned definition",
                     definition.id, pass_index, pass.name,
                     expected_program_key);
  }
}

void validate_factory_abi(const EffectStep& step, const PassAdmission& admission,
                          const effects::PassDefinition& pass) {
  if (step.effect.id == "synth/solid" && pass.program == "solid") {
    if (admission.identity.program_key != "synth/solid:solid" ||
        admission.canonical_factory != "bind_synth_solid_solid") {
      throw GraphError(GraphErrorCode::unavailable_pass, "canonical factory mismatch",
                       step.effect.id, admission.identity.index,
                       admission.identity.name, admission.identity.program_key);
    }
    validate_uniform_abi(
        step, admission, pass,
        {{"color", "vec3", "effect_parameter", "color", {}, "glsl::Vec3"},
         {"alpha", "float", "effect_parameter", "alpha", {}, "float"}});
    return;
  }
  if (step.effect.id == "filter/blur" && pass.program == "blurH") {
    if (admission.identity.program_key != "filter/blur:blurH" ||
        admission.canonical_factory != "bind_filter_blur_blurH") {
      throw GraphError(GraphErrorCode::unavailable_pass, "canonical factory mismatch",
                       step.effect.id, admission.identity.index,
                       admission.identity.name, admission.identity.program_key);
    }
    validate_uniform_abi(
        step, admission, pass,
        {{"tileOffset", "vec2", "reserved_runtime_state", "tileOffset", {}, "glsl::Vec2"},
         {"fullResolution", "vec2", "reserved_runtime_state", "fullResolution", {}, "glsl::Vec2"},
         {"radiusX", "float", "effect_parameter", "radiusX", {}, "float"},
         {"renderScale", "float", "reserved_runtime_state", "renderScale", {}, "float"}});
    return;
  }
  if (step.effect.id == "filter/blur" && pass.program == "blurV") {
    if (admission.identity.program_key != "filter/blur:blurV" ||
        admission.canonical_factory != "bind_filter_blur_blurV") {
      throw GraphError(GraphErrorCode::unavailable_pass, "canonical factory mismatch",
                       step.effect.id, admission.identity.index,
                       admission.identity.name, admission.identity.program_key);
    }
    validate_uniform_abi(
        step, admission, pass,
        {{"tileOffset", "vec2", "reserved_runtime_state", "tileOffset", {}, "glsl::Vec2"},
         {"fullResolution", "vec2", "reserved_runtime_state", "fullResolution", {}, "glsl::Vec2"},
         {"radiusY", "float", "effect_parameter", "radiusY", {}, "float"},
         {"renderScale", "float", "reserved_runtime_state", "renderScale", {}, "float"}});
    return;
  }
  throw GraphError(GraphErrorCode::unavailable_pass, "factory is not admitted for Task 6",
                   step.effect.id, admission.identity.index, admission.identity.name,
                   admission.identity.program_key);
}

void validate_plan_before_allocation(const ExecutionPlan& plan,
                                     const ExecutionInputs& inputs) {
  if (!validate_execution_plan(plan)) {
    throw GraphError(GraphErrorCode::invalid_snapshot, "plan snapshot or payload hash is invalid");
  }
  // Keep every variable-cardinality relationship checked before any indexed
  // access below.  This is deliberately redundant with the authenticated
  // snapshot validator: it makes this boundary fail closed even if a future
  // plan schema grows a new validation path.
  for (const auto& snapshot : plan.effects) {
    if (snapshot.definition.passes.size() != snapshot.admissions.size()) {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "effect admission cardinality mismatch",
                       snapshot.definition.id);
    }
    for (std::size_t pass_index = 0; pass_index < snapshot.admissions.size();
         ++pass_index) {
      const auto& admission = snapshot.admissions[pass_index];
      if (admission.status == AvailabilityStatus::scatter) {
        throw GraphError(GraphErrorCode::unsupported_scatter,
                         "scatter is not enabled in Task 6",
                         snapshot.definition.id, pass_index,
                         admission.identity.name,
                         admission.identity.program_key);
      }
      if (admission.status != AvailabilityStatus::compatible) {
        throw GraphError(GraphErrorCode::unavailable_pass,
                         "pass is not executable", snapshot.definition.id,
                         pass_index, admission.identity.name,
                         admission.identity.program_key);
      }
    }
  }
  if (plan.render_surface.kind != SurfaceReference::Kind::named ||
      plan.render_surface.name.empty()) {
    throw GraphError(GraphErrorCode::invalid_snapshot, "render surface is not a named route");
  }
  if (inputs.width == 0U || inputs.height == 0U) {
    throw GraphError(GraphErrorCode::invalid_dimension, "render dimensions must be positive");
  }
  if (inputs.height > noisemaker::kMaxSurfacePixels / inputs.width) {
    throw GraphError(GraphErrorCode::allocation_limit, "render dimensions exceed allocation limit");
  }
  if (!std::isfinite(inputs.time) || !std::isfinite(inputs.seed) ||
      !std::isfinite(inputs.delta_time)) {
    throw GraphError(GraphErrorCode::invalid_options, "runtime values must be finite");
  }
  if (!inputs.one_shot) {
    throw GraphError(GraphErrorCode::invalid_options, "one_shot=false is unsupported");
  }
  std::unordered_set<std::string> names;
  for (const auto& input : inputs.seed_surfaces) {
    if (input.name.empty() || !names.insert(input.name).second) {
      throw GraphError(GraphErrorCode::duplicate_output, "duplicate seed surface route");
    }
    if (input.surface.width() == 0U || input.surface.height() == 0U) {
      throw GraphError(GraphErrorCode::invalid_dimension, "seed surface dimensions are invalid");
    }
  }
  for (const auto& input : inputs.external_textures) {
    if (input.name.empty() || !names.insert(input.name).second) {
      throw GraphError(GraphErrorCode::duplicate_output, "duplicate external texture route");
    }
  }

  // Authenticate every allocation-relevant declaration and producer route
  // while the executor still owns no caller-derived resources.
  for (const auto& snapshot : plan.effects) {
    for (const auto& texture : snapshot.definition.textures) {
      try {
        (void)resolve_texture_format(texture.format);
      } catch (const std::invalid_argument& error) {
        throw GraphError(GraphErrorCode::invalid_format, error.what(), snapshot.definition.id);
      }
    }
  }
  if (!plan.executable) {
    throw GraphError(GraphErrorCode::unavailable_pass,
                     "plan contains an unavailable pass");
  }
  std::unordered_set<std::string> available_routes;
  for (const auto& input : inputs.seed_surfaces) available_routes.insert(input.name);
  for (const auto& input : inputs.external_textures) available_routes.insert(input.name);
  for (const auto& chain : plan.chains) {
    bool have_current = false;
    std::unordered_set<std::string> produced;
    for (const auto& variant : chain.steps) {
      if (const auto* read = std::get_if<ReadStep>(&variant)) {
        if (read->surface.kind != SurfaceReference::Kind::named ||
            available_routes.find(read->surface.name) == available_routes.end()) {
          throw GraphError(GraphErrorCode::missing_resource, "named read surface is missing", {}, 0, {}, read->surface.name);
        }
        have_current = true;
      } else if (const auto* write = std::get_if<WriteStep>(&variant)) {
        if (!have_current || write->surface.kind != SurfaceReference::Kind::named) {
          throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
        }
        available_routes.insert(write->surface.name);
      } else {
        const auto& effect = std::get<EffectStep>(variant);
        if (effect.snapshot_index >= plan.effects.size()) {
          throw GraphError(GraphErrorCode::invalid_snapshot, "effect snapshot index is out of range");
        }
        const auto& snapshot = plan.effects[effect.snapshot_index];
        for (std::size_t pass_index = 0; pass_index < snapshot.definition.passes.size(); ++pass_index) {
          const auto& pass = snapshot.definition.passes[pass_index];
          const auto& admission = snapshot.admissions[pass_index];
          validate_pass_identity_and_output(effect, snapshot.definition, pass,
                                            admission, pass_index);
          validate_ordinary_pass_metadata(effect, admission, pass, pass_index);
          validate_sampler_abi(pass, admission, effect.effect.id, pass_index);
          validate_factory_abi(effect, admission, pass);
          bool enabled = true;
          std::size_t repeats = 1U;
          try {
            enabled = pass_enabled(pass, effect);
            repeats = pass_repeat(pass, effect);
          } catch (const std::exception& error) {
            throw GraphError(GraphErrorCode::invalid_options, error.what(),
                             effect.effect.id, pass_index, pass.name,
                             admission.identity.program_key);
          }
          if (!enabled || repeats == 0U) continue;
          for (const auto& input : pass.inputs) {
            if (input.second == "inputTex") {
              if (!have_current) throw GraphError(GraphErrorCode::read_before_write, "input is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
            } else if (produced.find(input.second) == produced.end() &&
                       available_routes.find(input.second) == available_routes.end()) {
              throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
            }
          }
          for (const auto& texture : snapshot.definition.textures) {
            try {
              const auto resolve_static = [&](const effects::DimensionExpression& expression,
                                              bool width) -> std::size_t {
                if (expression.input_override.empty()) {
                  return resolve_dimension(expression, effect, ResourceArena{},
                                          width ? inputs.width : inputs.height, width);
                }
                for (const auto& input : inputs.seed_surfaces) {
                  if (input.name == expression.input_override) return width ? input.surface.width() : input.surface.height();
                }
                for (const auto& input : inputs.external_textures) {
                  if (input.name == expression.input_override) return width ? input.surface.width() : input.surface.height();
                }
                if (produced.find(expression.input_override) != produced.end() ||
                    available_routes.find(expression.input_override) !=
                        available_routes.end()) {
                  // The prior pass is authenticated as a producer. Its exact
                  // extent is resolved at execution after that resource exists.
                  return width ? inputs.width : inputs.height;
                }
                return resolve_dimension(expression, effect, ResourceArena{},
                                         width ? inputs.width : inputs.height,
                                         width);
              };
              const auto width = resolve_static(texture.width, true);
              const auto height = resolve_static(texture.height, false);
              if (height > noisemaker::kMaxSurfacePixels / width) {
                throw GraphError(
                    GraphErrorCode::allocation_limit,
                    "texture dimensions exceed allocation limit",
                    effect.effect.id, pass_index, pass.name,
                    admission.identity.program_key);
              }
            } catch (const GraphError&) {
              throw;
            } catch (const std::invalid_argument& error) {
              throw GraphError(GraphErrorCode::invalid_dimension, error.what(), effect.effect.id, pass_index, pass.name, admission.identity.program_key);
            }
          }
          for (const auto& output : pass.outputs) {
            produced.insert(output.second);
            if (output.second == "outputTex") have_current = true;
          }
        }
      }
    }
  }

  for (const auto& chain : plan.chains) {
    for (const auto& variant : chain.steps) {
      const auto* effect = std::get_if<EffectStep>(&variant);
      if (effect == nullptr) continue;
      if (effect->snapshot_index >= plan.effects.size()) {
        throw GraphError(GraphErrorCode::invalid_snapshot, "effect snapshot index is out of range");
      }
      const auto& snapshot = plan.effects[effect->snapshot_index];
      if (snapshot.definition.passes.size() != snapshot.admissions.size() ||
          snapshot.definition.passes.size() != effect->passes.size()) {
        throw GraphError(GraphErrorCode::invalid_snapshot, "effect admission cardinality mismatch",
                         effect->effect.id);
      }
      for (std::size_t index = 0; index < snapshot.definition.passes.size(); ++index) {
        const auto& pass = snapshot.definition.passes[index];
        const auto& admission = snapshot.admissions[index];
        const auto& retained = effect->passes[index];
        if (detail::admission_sha256(retained) !=
            detail::admission_sha256(admission)) {
          throw GraphError(GraphErrorCode::invalid_snapshot,
                           "effect step admission differs from owned snapshot",
                           effect->effect.id, index, admission.identity.name,
                           admission.identity.program_key);
        }
        if (admission.status != AvailabilityStatus::compatible) {
          if (admission.status == AvailabilityStatus::scatter) {
            throw GraphError(GraphErrorCode::unsupported_scatter, "scatter is not enabled in Task 6",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
          throw GraphError(GraphErrorCode::unavailable_pass, "pass is not executable",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        if (admission.authority_pass.blend || (pass.blend.has_value() && pass.blend->enabled)) {
          throw GraphError(GraphErrorCode::unsupported_blend, "blend is not enabled in Task 6",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        if (admission.draw_mode != "fragment" ||
            (pass.draw_mode.has_value() && *pass.draw_mode != "fragment")) {
          throw GraphError(GraphErrorCode::unsupported_draw_mode, "draw mode is not fragment",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        if (pass.draw_buffers.has_value() &&
            (pass.draw_buffers->kind != effects::ValueKind::number ||
             !std::isfinite(pass.draw_buffers->number) ||
             pass.draw_buffers->number != 1.0)) {
          throw GraphError(GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        validate_pass_identity_and_output(*effect, snapshot.definition, pass,
                                          admission, index);
        validate_ordinary_pass_metadata(*effect, admission, pass, index);
        validate_sampler_abi(pass, admission, effect->effect.id, index);
        std::unordered_set<std::string> outputs;
        for (const auto& output : pass.outputs) {
          if (!outputs.insert(output.second).second) {
            throw GraphError(GraphErrorCode::duplicate_output, "duplicate pass output route",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
        }
        validate_factory_abi(*effect, admission, pass);
      }
    }
  }
}

void set_uniform(glsl::Bindings& bindings, const CompatibilityBinding& abi,
                 const EffectStep& step, const ExecutionInputs& inputs,
                 std::size_t destination_width, std::size_t destination_height) {
  if (abi.source == "reserved_runtime_state") {
    if (abi.name == "tileOffset") bindings.set_uniform(abi.name, glsl::Vec2(0.0F, 0.0F));
    else if (abi.name == "fullResolution") bindings.set_uniform(abi.name, glsl::Vec2(static_cast<float>(inputs.width), static_cast<float>(inputs.height)));
    else if (abi.name == "resolution") bindings.set_uniform(abi.name, glsl::Vec2(static_cast<float>(destination_width), static_cast<float>(destination_height)));
    else if (abi.name == "renderScale") bindings.set_uniform(abi.name, 1.0F);
    else if (abi.name == "time") bindings.set_uniform(abi.name, noisemaker::f32(inputs.time));
    else if (abi.name == "seed") bindings.set_uniform(abi.name, noisemaker::f32(inputs.seed));
    else if (abi.name == "deltaTime") bindings.set_uniform(abi.name, noisemaker::f32(inputs.delta_time));
    else if (abi.name == "frame") bindings.set_uniform(abi.name, inputs.frame);
    else throw GraphError(GraphErrorCode::missing_binding, "unknown reserved runtime binding");
    return;
  }
  if (abi.source != "effect_parameter") {
    throw GraphError(GraphErrorCode::missing_binding, "unsupported binding source");
  }
  const PlanValue* value = parameter(step, abi.source_name.empty() ? abi.name : abi.source_name);
  if (value == nullptr) throw GraphError(GraphErrorCode::missing_binding, "effect parameter is missing");
  if (abi.name == "seed" &&
      std::find(step.explicit_params.begin(), step.explicit_params.end(), "seed") == step.explicit_params.end()) {
    bindings.set_uniform(abi.name, noisemaker::f32(inputs.seed));
    return;
  }
  try {
    if (abi.cpp_type == "float") bindings.set_uniform(abi.name, noisemaker::f32(number(*value, abi.name)));
    else if (abi.cpp_type == "double") bindings.set_uniform(abi.name, number(*value, abi.name));
    else if (abi.cpp_type == "glsl::Vec2" || abi.cpp_type == "glsl::Vec3" || abi.cpp_type == "glsl::Vec4") {
      if (value->kind != PlanValue::Kind::array) throw std::invalid_argument("vector binding is not an array");
      const std::size_t width = abi.cpp_type == "glsl::Vec2" ? 2U : (abi.cpp_type == "glsl::Vec3" ? 3U : 4U);
      if (value->array.size() != width) throw std::invalid_argument("vector binding has wrong width");
      if (width == 2U) bindings.set_uniform(abi.name, glsl::Vec2(noisemaker::f32(number(value->array[0], abi.name)), noisemaker::f32(number(value->array[1], abi.name))));
      else if (width == 3U) bindings.set_uniform(abi.name, glsl::Vec3(noisemaker::f32(number(value->array[0], abi.name)), noisemaker::f32(number(value->array[1], abi.name)), noisemaker::f32(number(value->array[2], abi.name))));
      else bindings.set_uniform(abi.name, glsl::Vec4(noisemaker::f32(number(value->array[0], abi.name)), noisemaker::f32(number(value->array[1], abi.name)), noisemaker::f32(number(value->array[2], abi.name)), noisemaker::f32(number(value->array[3], abi.name))));
    } else {
      throw GraphError(GraphErrorCode::binding_type, "unsupported uniform ABI type");
    }
  } catch (const GraphError&) { throw; }
  catch (const std::exception& error) { throw GraphError(GraphErrorCode::binding_type, error.what()); }
}

[[nodiscard]] noisemaker::BoundKernel bind_canonical(
    const PassAdmission& admission, const glsl::Bindings& bindings) {
  if (admission.canonical_factory == "bind_synth_solid_solid") return generated::bind_synth_solid_solid(bindings);
  if (admission.canonical_factory == "bind_filter_blur_blurH") return generated::bind_filter_blur_blurH(bindings);
  if (admission.canonical_factory == "bind_filter_blur_blurV") return generated::bind_filter_blur_blurV(bindings);
  throw std::invalid_argument("factory is not admitted");
}

}  // namespace

GraphError::GraphError(GraphErrorCode code, std::string detail,
                       std::string effect_id, std::size_t pass_index,
                       std::string pass_name, std::string program_key)
    : std::runtime_error(make_what(code, detail, effect_id, pass_index,
                                   pass_name, program_key)),
      code_(code), detail_(std::move(detail)), effect_id_(std::move(effect_id)),
      pass_index_(pass_index), pass_name_(std::move(pass_name)),
      program_key_(std::move(program_key)) {}

std::string GraphError::make_what(GraphErrorCode code, std::string_view detail,
                                  std::string_view effect_id,
                                  std::size_t pass_index,
                                  std::string_view pass_name,
                                  std::string_view program_key) {
  std::string result = "graph:" + std::string(code_name(code)) + ": ";
  if (!effect_id.empty()) {
    result += "effect=" + std::string(effect_id) + " pass=" + std::to_string(pass_index);
    if (!pass_name.empty()) result += " name=" + std::string(pass_name);
    if (!program_key.empty()) result += " program=" + std::string(program_key);
    result += ": ";
  }
  result += detail;
  return result;
}

ExecutionResult GraphExecutor::execute(const ExecutionPlan& plan,
                                       ExecutionInputs inputs) const {
  validate_plan_before_allocation(plan, inputs);
  ResourceArena arena;
  for (const auto& input : inputs.seed_surfaces) {
    try {
      arena.copy(input.name, input.surface, TextureFormat::rgba32f,
                 ResourceLifetime::seed);
    } catch (const std::overflow_error&) {
      throw GraphError(GraphErrorCode::allocation_limit,
                       "seed surface copy exceeds allocation limit");
    } catch (const std::exception&) {
      throw GraphError(GraphErrorCode::execution_failure,
                       "seed surface copy failed");
    }
  }
  for (const auto& input : inputs.external_textures) {
    try {
      arena.copy(input.name, input.surface, TextureFormat::rgba32f,
                 ResourceLifetime::external);
    } catch (const std::overflow_error&) {
      throw GraphError(GraphErrorCode::allocation_limit,
                       "external texture copy exceeds allocation limit");
    } catch (const std::exception&) {
      throw GraphError(GraphErrorCode::execution_failure,
                       "external texture copy failed");
    }
  }

  GraphResource* current = nullptr;
  std::size_t pass_count = 0;
  for (const auto& chain : plan.chains) {
    for (const auto& variant : chain.steps) {
      if (const auto* read = std::get_if<ReadStep>(&variant)) {
        if (read->surface.kind != SurfaceReference::Kind::named || arena.find(read->surface.name) == nullptr) {
          throw GraphError(GraphErrorCode::missing_resource, "named read surface is missing", {}, 0, {}, read->surface.name);
        }
        current = arena.find(read->surface.name);
      } else if (const auto* write = std::get_if<WriteStep>(&variant)) {
        if (current == nullptr || write->surface.kind != SurfaceReference::Kind::named) {
          throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
        }
        arena.alias(write->surface.name, *current);
      } else {
        const auto& step = std::get<EffectStep>(variant);
        const auto& snapshot = plan.effects[step.snapshot_index];
        GraphResource* effect_output = current;
        for (std::size_t pass_index = 0; pass_index < snapshot.definition.passes.size(); ++pass_index) {
          const auto& pass = snapshot.definition.passes[pass_index];
          const auto& admission = snapshot.admissions[pass_index];
          bool enabled = false;
          std::size_t repeats = 0U;
          try {
            enabled = pass_enabled(pass, step);
            repeats = pass_repeat(pass, step);
          } catch (const std::exception& error) {
            throw GraphError(GraphErrorCode::invalid_options, error.what(),
                             step.effect.id, pass_index, pass.name,
                             admission.identity.program_key);
          }
          if (!enabled || repeats == 0U) continue;
          for (std::size_t repeat = 0; repeat < repeats; ++repeat) {
          GraphResource* input_resource = nullptr;
          for (const auto& input : pass.inputs) {
            const std::string route = input.second == "inputTex" ? (current == nullptr ? std::string() : std::string(current->name())) : input.second;
            if (route.empty()) throw GraphError(GraphErrorCode::read_before_write, "input is not produced", step.effect.id, pass_index, pass.name, admission.identity.program_key);
            input_resource = arena.find(route);
            if (input_resource == nullptr) {
              throw GraphError(GraphErrorCode::read_before_write,
                               "input resource is not produced", step.effect.id,
                               pass_index, pass.name,
                               admission.identity.program_key);
            }
          }
          if (input_resource != nullptr) arena.retain(*input_resource);
          const std::string output_route = pass.outputs.front().second;
          const auto* texture = texture_for(snapshot.definition, output_route);
          std::size_t width = inputs.width;
          std::size_t height = inputs.height;
          TextureFormat format = TextureFormat::rgba16f;
          try {
            if (texture != nullptr) {
              width = resolve_dimension(texture->width, step, arena, inputs.width, true);
              height = resolve_dimension(texture->height, step, arena, inputs.height, false);
              try {
                format = resolve_texture_format(texture->format);
              } catch (const std::invalid_argument& error) {
                throw GraphError(GraphErrorCode::invalid_format, error.what(),
                                 step.effect.id, pass_index, pass.name,
                                 admission.identity.program_key);
              }
            }
            glsl::Bindings bindings;
            for (const auto& sampler : admission.samplers) {
              if (sampler.name == "inputTex" && input_resource != nullptr) bindings.set_texture(sampler.name, input_resource->surface());
              else throw GraphError(GraphErrorCode::missing_binding, "sampler resource is missing", step.effect.id, pass_index, pass.name, admission.identity.program_key);
            }
            for (const auto& uniform : admission.uniforms) set_uniform(bindings, uniform, step, inputs, width, height);
            auto kernel = bind_canonical(admission, bindings);
            // Render and quantize off-route.  A failed factory or kernel must
            // never publish a partially initialized destination into the
            // arena, so route replacement is one atomic insert after all work
            // has completed successfully.
            auto rendered = noisemaker::run_pass(kernel, width, height,
                                                 noisemaker::f32(inputs.time),
                                                 noisemaker::f32(inputs.seed), inputs.frame,
                                                 noisemaker::f32(inputs.delta_time));
            noisemaker::quantize_texture(rendered, format);
            auto& destination = arena.insert(output_route, std::move(rendered),
                                              format, ResourceLifetime::transient);
            effect_output = &destination;
            ++pass_count;
          } catch (const GraphError& error) {
            if (input_resource != nullptr) arena.release(*input_resource);
            if (error.effect_id().empty()) {
              throw GraphError(error.code(), std::string(error.detail()),
                               step.effect.id, pass_index, pass.name,
                               admission.identity.program_key);
            }
            throw;
          } catch (const glsl::KernelBindingError& error) {
            (void)error;
            if (input_resource != nullptr) arena.release(*input_resource);
            throw GraphError(GraphErrorCode::binding_type, "factory binding failed", step.effect.id, pass_index, pass.name, admission.identity.program_key);
          } catch (const std::exception& error) {
            (void)error;
            if (input_resource != nullptr) arena.release(*input_resource);
            throw GraphError(GraphErrorCode::execution_failure, "pass execution failed", step.effect.id, pass_index, pass.name, admission.identity.program_key);
          }
          if (input_resource != nullptr) arena.release(*input_resource);
          if (output_route == "outputTex") current = effect_output;
          }
        }
        current = effect_output;
      }
    }
  }
  if (current == nullptr || arena.find(plan.render_surface.name) == nullptr) {
    throw GraphError(GraphErrorCode::missing_resource, "render surface was not published", {}, 0, {}, plan.render_surface.name);
  }
  const auto& final = arena.require(plan.render_surface.name);
  return {final.surface().clone(), std::string(plan.render_surface.name), pass_count};
}

}  // namespace noisemaker::graph
