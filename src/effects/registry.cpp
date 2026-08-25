#include "noisemaker/effects/registry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <charconv>
#include <utility>

namespace noisemaker::effects {
namespace {

using graph::PlanValue;

const Value* field(const std::vector<std::pair<std::string, Value>>& fields,
                  std::string_view name) {
  for (const auto& item : fields) if (item.first == name) return &item.second;
  return nullptr;
}

std::string string_field(const std::vector<std::pair<std::string, Value>>& fields,
                         std::string_view name) {
  const auto* value = field(fields, name);
  return value != nullptr && value->kind == ValueKind::string ? value->string : std::string{};
}

graph::CompatibilityBinding binding_value(const Value& value) {
  graph::CompatibilityBinding result;
  if (value.kind != ValueKind::object) return result;
  result.name = string_field(value.object, "name");
  result.type = string_field(value.object, "type");
  result.source = string_field(value.object, "source");
  result.source_name = string_field(value.object, "source_name");
  result.resource = string_field(value.object, "resource");
  result.cpp_type = string_field(value.object, "cpp_type");
  return result;
}

void binding_array(const Value* value, std::vector<graph::CompatibilityBinding>& output) {
  if (value == nullptr || value->kind != ValueKind::array) return;
  for (const auto& item : value->array) output.push_back(binding_value(item));
}

PlanValue copy_value(const Value& value) {
  switch (value.kind) {
    case ValueKind::null_value: return PlanValue::null();
    case ValueKind::boolean: return PlanValue::boolean_value(value.boolean);
    case ValueKind::number: return PlanValue::number_value(value.number);
    case ValueKind::string: return PlanValue::string_value(value.string);
    case ValueKind::array: {
      std::vector<PlanValue> values;
      values.reserve(value.array.size());
      for (const auto& item : value.array) values.push_back(copy_value(item));
      return PlanValue::array_value(std::move(values));
    }
    case ValueKind::object: {
      const auto* kind = field(value.object, "kind");
      if (kind != nullptr && kind->kind == ValueKind::string && kind->string == "input") {
        return PlanValue::surface_value(graph::SurfaceReference::input());
      }
      if (kind != nullptr && kind->kind == ValueKind::string && kind->string == "surface") {
        const auto* name = field(value.object, "name");
        const auto* index = field(value.object, "index");
        if (name != nullptr && name->kind == ValueKind::string && index != nullptr &&
            index->kind == ValueKind::number && std::isfinite(index->number) &&
            index->number >= 0.0) {
          return PlanValue::surface_value(graph::SurfaceReference::named(
              name->string, static_cast<std::size_t>(index->number)));
        }
      }
      throw std::invalid_argument("Unsupported object parameter value");
    }
  }
  throw std::invalid_argument("Unsupported parameter value");
}

const std::vector<std::pair<std::string, Value>>& choices_for(const ParameterDefinition& parameter) {
  return parameter.choices.empty() ? parameter.enum_values : parameter.choices;
}

const Value* choice(const ParameterDefinition& parameter, std::string_view key) {
  const auto& choices = choices_for(parameter);
  for (const auto& item : choices) if (item.first == key) return &item.second;
  return nullptr;
}

std::string final_member(std::string value) {
  const auto dot = value.find_last_of('.');
  if (dot != std::string::npos) value.erase(0, dot + 1);
  return value;
}

std::string choice_names(const ParameterDefinition& parameter, bool omit_null) {
  std::string result;
  bool first = true;
  for (const auto& item : choices_for(parameter)) {
    if (omit_null && item.second.kind == ValueKind::null_value) continue;
    if (!first) result += ", ";
    first = false;
    result += item.first;
  }
  return result;
}

std::string number_text(double value) {
  if (std::isnan(value)) return "NaN";
  if (std::isinf(value)) return value < 0.0 ? "-Infinity" : "Infinity";
  if (value == 0.0 && std::signbit(value)) return "-0";
  char buffer[64]{};
  const auto converted = std::to_chars(std::begin(buffer), std::end(buffer), value,
                                       std::chars_format::general,
                                       std::numeric_limits<double>::max_digits10);
  if (converted.ec == std::errc{}) return std::string(buffer, converted.ptr);
  return std::to_string(value);
}

PlanValue enum_value(const ParameterDefinition& parameter, PlanValue value,
                    const std::string& name) {
  if (value.kind != PlanValue::Kind::string) return value;
  const std::string key = final_member(value.string);
  const Value* found = choice(parameter, key);
  if (found == nullptr || found->kind == ValueKind::null_value) {
    throw std::invalid_argument("Parameter \"" + name + "\" must be one of " +
                                choice_names(parameter, true));
  }
  return copy_value(*found);
}

PlanValue color_value(PlanValue value, const std::string& name) {
  if (value.kind != PlanValue::Kind::string) return value;
  const std::string& text = value.string;
  if ((text.size() != 7 && text.size() != 9) || text.front() != '#') {
    throw std::invalid_argument("Parameter \"" + name + "\" must be an RGB or RGBA color");
  }
  auto hex = [](char c) -> int {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
  };
  std::vector<PlanValue> components;
  for (std::size_t i = 1; i < text.size(); i += 2) {
    const int hi = hex(text[i]);
    const int lo = hex(text[i + 1]);
    if (hi < 0 || lo < 0) {
      throw std::invalid_argument("Parameter \"" + name + "\" must be an RGB or RGBA color");
    }
    components.push_back(PlanValue::number_value(static_cast<double>(hi * 16 + lo) / 255.0));
  }
  return PlanValue::array_value(std::move(components));
}

[[noreturn]] void type_error(const std::string& name, std::string_view text) {
  throw std::invalid_argument("Parameter \"" + name + "\" " + std::string(text));
}

PlanValue normalize_value(const ParameterDefinition& parameter, PlanValue value,
                          const std::string& name) {
  const auto is_number = value.kind == PlanValue::Kind::number;
  if (parameter.type == "float") {
    if (!is_number || !std::isfinite(value.number)) type_error(name, "must be a finite number");
  } else if (parameter.type == "int") {
    if (!choices_for(parameter).empty()) value = enum_value(parameter, std::move(value), name);
    if (value.kind != PlanValue::Kind::number || !std::isfinite(value.number) ||
        std::trunc(value.number) != value.number) type_error(name, "must be an integer");
  } else if (parameter.type == "bool" || parameter.type == "boolean") {
    if (value.kind != PlanValue::Kind::boolean) type_error(name, "must be boolean");
  } else if (parameter.type == "color") {
    value = color_value(std::move(value), name);
    if (value.kind != PlanValue::Kind::array || (value.array.size() != 3 && value.array.size() != 4)) {
      type_error(name, "must be an RGB or RGBA color");
    }
    for (const auto& item : value.array) if (item.kind != PlanValue::Kind::number) type_error(name, "must be an RGB or RGBA color");
  } else if (parameter.type == "vec2" || parameter.type == "vec3" || parameter.type == "vec4") {
    const std::size_t width = static_cast<std::size_t>(parameter.type.back() - '0');
    if (value.kind != PlanValue::Kind::array || value.array.size() != width) type_error(name, "must be a " + parameter.type);
    for (const auto& item : value.array) if (item.kind != PlanValue::Kind::number) type_error(name, "must be a " + parameter.type);
  } else if (parameter.type == "mat3") {
    if (value.kind != PlanValue::Kind::array || value.array.size() != 9) type_error(name, "must be a mat3");
    for (const auto& item : value.array) if (item.kind != PlanValue::Kind::number || !std::isfinite(item.number)) type_error(name, "must be a mat3");
  } else if (parameter.type == "enum") {
    value = enum_value(parameter, std::move(value), name);
    if (value.kind != PlanValue::Kind::number) type_error(name, "must be an enum value");
  } else if (parameter.type == "member" || parameter.type == "palette") {
    value = enum_value(parameter, std::move(value), name);
    if (value.kind != PlanValue::Kind::number || !std::isfinite(value.number) || std::trunc(value.number) != value.number) type_error(name, "must be an enum value");
  } else if (parameter.type == "string") {
    if (value.kind != PlanValue::Kind::string) type_error(name, "must be a string");
    if (!choices_for(parameter).empty()) {
      const std::string key = final_member(value.string);
      if (const Value* found = choice(parameter, key); found != nullptr) value = copy_value(*found);
      else {
        bool direct = false;
        for (const auto& item : choices_for(parameter)) {
          const PlanValue candidate = copy_value(item.second);
          if (candidate.kind == PlanValue::Kind::string && candidate.string == value.string) { direct = true; break; }
        }
        if (!direct) throw std::invalid_argument("Parameter \"" + name + "\" must be one of " + choice_names(parameter, false));
      }
    }
  } else if (parameter.type == "surface") {
    if (value.kind == PlanValue::Kind::null_value || (value.kind == PlanValue::Kind::string && value.string == "none")) value = PlanValue::null();
    else if (value.kind == PlanValue::Kind::string && value.string == "inputTex") value = PlanValue::surface_value(graph::SurfaceReference::input());
    else if (value.kind != PlanValue::Kind::surface) type_error(name, "must be a surface reference");
  } else if (parameter.type == "volume" || parameter.type == "geometry") {
    if (value.kind != PlanValue::Kind::string || value.string.empty()) type_error(name, "must be a " + parameter.type + " reference");
  } else {
    throw std::invalid_argument("Unsupported parameter type \"" + parameter.type + "\"");
  }
  if (value.kind == PlanValue::Kind::number) {
    if (parameter.min.has_value() && parameter.min->kind == ValueKind::number && value.number < parameter.min->number) {
      throw std::invalid_argument("Parameter \"" + name + "\" must be at least " + number_text(parameter.min->number));
    }
    if (parameter.max.has_value() && parameter.max->kind == ValueKind::number && value.number > parameter.max->number) {
      throw std::invalid_argument("Parameter \"" + name + "\" must be at most " + number_text(parameter.max->number));
    }
  }
  return value;
}

}  // namespace

EffectRegistry::EffectRegistry(const EffectCatalog& catalog)
    : compatibility_(catalog.compatibility) {
  manifest_backed_ = true;
  definitions_.reserve(catalog.definitions.size());
  for (const auto& definition : catalog.definitions) register_effect(definition);
  std::vector<std::string> keys;
  for (const auto& row : compatibility_) {
    if (std::find(keys.begin(), keys.end(), row.program_key) != keys.end()) {
      throw std::invalid_argument("Duplicate compatibility program key \"" + row.program_key + "\"");
    }
    keys.push_back(row.program_key);
    if (row.status != "compatible" && row.status != "incompatible" && row.status != "missing" && row.status != "registered") {
      throw std::invalid_argument("Invalid compatibility status \"" + row.status + "\"");
    }
    if (row.status == "compatible" && row.raw.empty()) {
      throw std::invalid_argument("Compatible compatibility row has no validated raw view: " + row.program_key);
    }
    if (row.status == "registered" && row.program_key != "filter/wormhole:deposit") {
      throw std::invalid_argument("Unknown scatter compatibility row: " + row.program_key);
    }
    if (row.status == "compatible") {
      const auto* raw_key = field(row.raw, "program_key");
      const auto* raw_status = field(row.raw, "status");
      const auto* raw_dimensions = field(row.raw, "dimensionality");
      const auto* raw_draw = field(row.raw, "draw_mode");
      const auto* raw_output = field(row.raw, "output_abi");
      if (raw_key == nullptr || raw_key->kind != ValueKind::string || raw_key->string != row.program_key ||
          raw_status == nullptr || raw_status->kind != ValueKind::string || raw_status->string != "compatible" ||
          raw_dimensions == nullptr || raw_dimensions->kind != ValueKind::string ||
          raw_draw == nullptr || raw_draw->kind != ValueKind::string ||
          raw_output == nullptr || raw_output->kind != ValueKind::object) {
        throw std::invalid_argument("Malformed compatible compatibility row: " + row.program_key);
      }
      if (!row.canonical_factory.has_value() || !row.source_sha256.has_value() ||
          !row.semantic_sha256.has_value()) {
        throw std::invalid_argument("Compatible compatibility row lacks authenticated identity: " + row.program_key);
      }
    }
  }
}

EffectRegistry::EffectRegistry(std::vector<EffectDefinition> definitions) {
  for (auto& definition : definitions) register_effect(std::move(definition));
}

EffectRegistry& EffectRegistry::register_effect(EffectDefinition definition) {
  if (definition.name_space.empty() || definition.function.empty()) throw std::invalid_argument("Effect definition requires namespace and func");
  if (definition.id.empty()) definition.id = definition.name_space + "/" + definition.function;
  if (definition.domain.empty()) definition.domain = "image";
  if (definition.id != definition.name_space + "/" + definition.function) throw std::invalid_argument("Effect definition id does not match namespace and func");
  if (definition.kind != "generator" && definition.kind != "filter" && definition.kind != "mixer") throw std::invalid_argument("Invalid effect kind \"" + definition.kind + "\"");
  if (definition.passes.empty()) throw std::invalid_argument("Effect definition requires at least one pass");
  const std::vector<std::string> domains = {"image", "volume-generator", "volume-filter", "volume-renderer", "loop-begin", "loop-end"};
  if (std::find(domains.begin(), domains.end(), definition.domain) == domains.end()) throw std::invalid_argument("Invalid effect domain \"" + definition.domain + "\"");
  if (get(definition.name_space, definition.function) != nullptr) throw std::invalid_argument("Effect \"" + definition.id + "\" is already registered");
  definitions_.push_back(std::move(definition));
  return *this;
}

const EffectDefinition* EffectRegistry::get(std::string_view name_space, std::string_view function) const noexcept {
  const std::string id = std::string(name_space) + "/" + std::string(function);
  for (const auto& definition : definitions_) if (definition.id == id) return &definition;
  return nullptr;
}

const EffectDefinition* EffectRegistry::resolve(std::string_view function, const std::vector<std::string>& search) const noexcept {
  for (const auto& name_space : search) if (const auto* result = get(name_space, function); result != nullptr) return result;
  return nullptr;
}

std::vector<const EffectDefinition*> EffectRegistry::list() const {
  std::vector<const EffectDefinition*> result;
  for (const auto& definition : definitions_) result.push_back(&definition);
  std::sort(result.begin(), result.end(), [](const auto* left, const auto* right) { return left->id < right->id; });
  return result;
}

NormalizedArguments EffectRegistry::normalize(const EffectDefinition& definition,
                                              const std::vector<ParameterArgument>& arguments) const {
  std::vector<ParameterDefinition> params = definition.parameters;
  std::vector<std::pair<std::string, PlanValue>> values;
  std::vector<bool> present(params.size(), false);
  values.reserve(params.size());
  for (const auto& parameter : params) {
    if (parameter.default_value.has_value()) values.emplace_back(parameter.name, normalize_value(parameter, copy_value(*parameter.default_value), parameter.name));
    else values.emplace_back(parameter.name, PlanValue::null());
  }
  const bool named = !arguments.empty() && arguments.front().name.has_value();
  for (std::size_t index = 0; index < arguments.size(); ++index) {
    const std::optional<std::string> supplied = named ? arguments[index].name : (index < params.size() ? std::optional<std::string>(params[index].name) : std::nullopt);
    const std::string supplied_name = supplied.value_or("argument " + std::to_string(index + 1));
    std::string canonical = supplied_name;
    for (const auto& alias : definition.parameter_aliases) if (alias.first == supplied_name) { canonical = alias.second; break; }
    std::size_t parameter_index = params.size();
    for (std::size_t candidate = 0; candidate < params.size(); ++candidate) if (params[candidate].name == canonical) { parameter_index = candidate; break; }
    if (parameter_index == params.size()) {
      std::string accepted;
      for (const auto& parameter : params) { if (!accepted.empty()) accepted += ", "; accepted += parameter.name; }
      for (const auto& alias : definition.parameter_aliases) { if (!accepted.empty()) accepted += ", "; accepted += alias.first; }
      throw std::invalid_argument("Unknown parameter \"" + supplied_name + "\" for " + definition.id + "; accepted: " + accepted);
    }
    values[parameter_index].second = normalize_value(params[parameter_index], arguments[index].value, canonical);
    present[parameter_index] = true;
  }
  for (std::size_t index = 0; index < params.size(); ++index) {
    if (!present[index] && !params[index].default_value.has_value()) throw std::invalid_argument("Missing required parameter \"" + params[index].name + "\" for " + definition.id);
  }
  NormalizedArguments result;
  for (std::size_t index = 0; index < params.size(); ++index) if (present[index] || params[index].default_value.has_value()) result.values.push_back({params[index].name, std::move(values[index].second)});
  return result;
}

graph::PassAdmission EffectRegistry::admission(const EffectDefinition& definition, std::size_t pass_index) const {
  if (pass_index >= definition.passes.size()) throw std::invalid_argument("Pass index out of range");
  const auto& pass = definition.passes[pass_index];
  graph::PassAdmission result;
  result.identity = {pass_index, pass.name, definition.id + ":" + pass.program};
  const ProgramCompatibility* row = nullptr;
  for (const auto& candidate : compatibility_) if (candidate.program_key == result.identity.program_key) { row = &candidate; break; }
  if (row == nullptr) {
    if (manifest_backed_) {
      result.status = graph::AvailabilityStatus::missing;
      result.reasons.push_back({"missing_compatibility_row", result.identity.program_key});
    } else {
      result.status = graph::AvailabilityStatus::compatible;
    }
    return result;
  }
  if (row->status == "registered") {
    result.status = graph::AvailabilityStatus::scatter;
    result.reasons.push_back({"explicit_scatter_adapter", result.identity.program_key});
  }
  else if (row->status == "compatible") result.status = graph::AvailabilityStatus::compatible;
  else if (row->status == "incompatible") result.status = graph::AvailabilityStatus::incompatible;
  else result.status = graph::AvailabilityStatus::missing;
  result.canonical_factory = row->canonical_factory.value_or("");
  result.source_sha256 = row->source_sha256.value_or("");
  result.semantic_sha256 = row->semantic_sha256.value_or("");
  result.dimensionality = string_field(row->raw, "dimensionality");
  result.draw_mode = string_field(row->raw, "draw_mode");
  for (const auto& reason : row->reasons) result.reasons.push_back({reason.first, reason.second});
  if (const auto* capability = field(row->raw, "capabilities"); capability != nullptr && capability->kind == ValueKind::array) {
    for (const auto& item : capability->array) if (item.kind == ValueKind::string) result.capabilities.push_back(item.string);
  }
  binding_array(field(row->raw, "samplers"), result.samplers);
  binding_array(field(row->raw, "uniforms"), result.uniforms);
  binding_array(field(row->raw, "outputs"), result.outputs);
  return result;
}

}  // namespace noisemaker::effects
