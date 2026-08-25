#include "noisemaker/effects/registry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <charconv>
#include <tuple>
#include <set>
#include <array>
#include <utility>

namespace noisemaker::effects {
namespace {

using graph::PlanValue;

const Value* field(const std::vector<std::pair<std::string, Value>>& fields,
                  std::string_view name) {
  for (const auto& item : fields) if (item.first == name) return &item.second;
  return nullptr;
}

const Value& required_field(const std::vector<std::pair<std::string, Value>>& fields,
                            std::string_view name, ValueKind kind, const std::string& context) {
  const auto* value = field(fields, name);
  if (value == nullptr || value->kind != kind) {
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": field " + std::string(name));
  }
  return *value;
}

void exact_object(const std::vector<std::pair<std::string, Value>>& fields,
                  std::initializer_list<std::string_view> allowed,
                  const std::string& context) {
  std::set<std::string_view> names(allowed.begin(), allowed.end());
  std::set<std::string> seen;
  for (const auto& pair : fields) {
    if (!names.count(pair.first) || !seen.insert(pair.first).second)
      throw std::invalid_argument("Malformed compatible compatibility row " + context + ": exact object keys");
  }
  if (seen.size() != names.size())
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": missing object key");
}

void nonempty_string(const Value& value, const std::string& context) {
  if (value.kind != ValueKind::string || value.string.empty())
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": non-empty string expected");
}

bool hex_sha256(std::string_view value) {
  if (value.size() != 64) return false;
  for (const char character : value) {
    if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f'))) return false;
  }
  return true;
}

void sha256_field(const Value& value, const std::string& context) {
  if (value.kind != ValueKind::string || !hex_sha256(value.string))
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": lowercase sha256 expected");
}

void safe_path_field(const Value& value, bool source_root, const std::string& context) {
  nonempty_string(value, context);
  const std::string& path = value.string;
  if (path.front() == '/' || path.find('\\') != std::string::npos ||
      (source_root && path.rfind("sources/", 0) != 0) || (!source_root && path.rfind("src/", 0) != 0))
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": unsafe path");
  std::size_t start = 0;
  while (start <= path.size()) {
    const auto end = path.find('/', start);
    const auto component = path.substr(start, end == std::string::npos ? std::string::npos : end - start);
    if (component.empty() || component == "." || component == "..")
      throw std::invalid_argument("Malformed compatible compatibility row " + context + ": unsafe path component");
    if (end == std::string::npos) break;
    start = end + 1;
  }
}

bool same_value(const Value& left, const Value& right) {
  if (left.kind != right.kind) return false;
  if (left.kind == ValueKind::null_value) return true;
  if (left.kind == ValueKind::boolean) return left.boolean == right.boolean;
  if (left.kind == ValueKind::number) return left.number == right.number;
  if (left.kind == ValueKind::string) return left.string == right.string;
  if (left.kind == ValueKind::array) {
    if (left.array.size() != right.array.size()) return false;
    for (std::size_t index = 0; index < left.array.size(); ++index) if (!same_value(left.array[index], right.array[index])) return false;
    return true;
  }
  if (left.object.size() != right.object.size()) return false;
  for (std::size_t index = 0; index < left.object.size(); ++index) {
    if (left.object[index].first != right.object[index].first || !same_value(left.object[index].second, right.object[index].second)) return false;
  }
  return true;
}

bool same_authority_value(const Value& left, const Value& right) {
  if (left.kind != right.kind) return false;
  if (left.kind != ValueKind::object) return same_value(left, right);
  if (left.object.size() != right.object.size()) return false;
  for (const auto& item : left.object) {
    const auto* counterpart = field(right.object, item.first);
    if (counterpart == nullptr || !same_authority_value(item.second, *counterpart)) return false;
  }
  return true;
}

void required_binding_array(const Value& value, const std::string& context, bool output) {
  if (value.kind != ValueKind::array) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": binding array expected");
  for (const auto& item : value.array) {
    if (item.kind != ValueKind::object) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": binding object expected");
    if (output) exact_object(item.object, {"slot", "physical_name", "logical_route", "cpp_type"}, context);
    else if (context.find(".samplers") != std::string::npos) exact_object(item.object, {"name", "type", "cpp_type", "source", "resource"}, context);
    else exact_object(item.object, {"name", "type", "cpp_type", "source", "source_name"}, context);
    nonempty_string(required_field(item.object, "cpp_type", ValueKind::string, context), context + ".cpp_type");
    if (output) {
      const auto& slot = required_field(item.object, "slot", ValueKind::number, context);
      if (!std::isfinite(slot.number) || slot.number < 0 || std::trunc(slot.number) != slot.number)
        throw std::invalid_argument("Malformed compatible compatibility row " + context + ": output slot");
      nonempty_string(required_field(item.object, "physical_name", ValueKind::string, context), context + ".physical_name");
      nonempty_string(required_field(item.object, "logical_route", ValueKind::string, context), context + ".logical_route");
    } else if (context.find(".samplers") != std::string::npos) {
      nonempty_string(required_field(item.object, "name", ValueKind::string, context), context + ".name");
      if (required_field(item.object, "type", ValueKind::string, context).string != "sampler2D" ||
          required_field(item.object, "cpp_type", ValueKind::string, context).string != "const Surface&" ||
          required_field(item.object, "source", ValueKind::string, context).string != "resource")
        throw std::invalid_argument("Malformed compatible compatibility row " + context + ": sampler ABI");
      nonempty_string(required_field(item.object, "resource", ValueKind::string, context), context + ".resource");
    } else {
      nonempty_string(required_field(item.object, "name", ValueKind::string, context), context + ".name");
      const auto& type = required_field(item.object, "type", ValueKind::string, context);
      const std::array<std::string_view, 8> allowed_types = {"float", "int", "bool", "vec2", "vec3", "vec4", "ivec2", "vec4[267]"};
      if (std::find(allowed_types.begin(), allowed_types.end(), type.string) == allowed_types.end())
        throw std::invalid_argument("Malformed compatible compatibility row " + context + ": uniform type");
      const auto& source = required_field(item.object, "source", ValueKind::string, context);
      const std::array<std::string_view, 6> allowed_sources = {"effect_parameter", "pass_literal", "pass_derived", "reserved_runtime_state", "resource", "external_texture"};
      if (std::find(allowed_sources.begin(), allowed_sources.end(), source.string) == allowed_sources.end())
        throw std::invalid_argument("Malformed compatible compatibility row " + context + ": uniform source");
      nonempty_string(required_field(item.object, "source_name", ValueKind::string, context), context + ".source_name");
    }
  }
}

void validate_compatible_raw(const ProgramCompatibility& row) {
  const auto& raw = row.raw;
  const std::string context = row.program_key;
  exact_object(raw, {"row_kind", "effect_id", "program", "program_key", "status", "reasons", "source", "old_raw_sha256", "new_raw_sha256", "typed_abi_sha256", "old_raw_bytes", "new_raw_bytes", "source_classification", "compatibility_transform", "derivative_use", "draw_mode", "dimensionality", "capabilities", "uniforms", "samplers", "outputs", "output_abi", "semantic", "factory", "authority_pass"}, context);
  for (const auto name : {"effect_id", "program", "program_key"}) nonempty_string(required_field(raw, name, ValueKind::string, context), context + "." + std::string(name));
  if (field(raw, "program_key")->string != field(raw, "effect_id")->string + ":" + field(raw, "program")->string)
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": program identity");
  if (field(raw, "row_kind")->string != "canonical" || field(raw, "status")->string != "compatible") throw std::invalid_argument("Malformed compatible compatibility row " + context + ": status identity");
  const auto& reasons = required_field(raw, "reasons", ValueKind::array, context);
  if (!reasons.array.empty()) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": compatible reasons must be empty");
  safe_path_field(required_field(raw, "source", ValueKind::string, context), true, context + ".source");
  for (const auto name : {"typed_abi_sha256", "old_raw_sha256", "new_raw_sha256"}) sha256_field(required_field(raw, name, ValueKind::string, context), context + "." + std::string(name));
  for (const auto name : {"old_raw_bytes", "new_raw_bytes"}) {
    const auto& bytes = required_field(raw, name, ValueKind::number, context);
    if (!std::isfinite(bytes.number) || bytes.number < 0 || std::trunc(bytes.number) != bytes.number) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": raw byte count");
  }
  const auto& classification = required_field(raw, "source_classification", ValueKind::string, context);
  if (classification.string != "raw_exact" && classification.string != "semantic_exact") throw std::invalid_argument("Malformed compatible compatibility row " + context + ": source classification");
  nonempty_string(required_field(raw, "compatibility_transform", ValueKind::string, context), context + ".compatibility_transform");
  if (required_field(raw, "dimensionality", ValueKind::string, context).string != "image" || required_field(raw, "draw_mode", ValueKind::string, context).string != "fragment") throw std::invalid_argument("Malformed compatible compatibility row " + context + ": execution ABI");
  required_field(raw, "derivative_use", ValueKind::boolean, context);
  {
    const auto& capabilities = field(raw, "capabilities")->array;
    std::set<std::string> unique;
    if (capabilities.size() != 44) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": capability census");
    for (const auto& capability : capabilities) if (capability.kind != ValueKind::string || capability.string.empty() || !unique.insert(capability.string).second) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": duplicate capability");
  }
  required_binding_array(required_field(raw, "samplers", ValueKind::array, context), context + ".samplers", false);
  required_binding_array(required_field(raw, "uniforms", ValueKind::array, context), context + ".uniforms", false);
  required_binding_array(required_field(raw, "outputs", ValueKind::array, context), context + ".outputs", true);
  const auto& semantic = required_field(raw, "semantic", ValueKind::object, context).object;
  exact_object(semantic, {"old_token_sha256", "new_token_sha256", "old_typed_ir_sha256", "new_typed_ir_sha256"}, context + ".semantic");
  for (const auto name : {"old_token_sha256", "old_typed_ir_sha256", "new_token_sha256", "new_typed_ir_sha256"}) required_field(semantic, name, ValueKind::string, context + ".semantic");
  for (const auto name : {"old_token_sha256", "old_typed_ir_sha256", "new_token_sha256", "new_typed_ir_sha256"}) sha256_field(required_field(semantic, name, ValueKind::string, context + ".semantic"), context + ".semantic." + std::string(name));
  if (field(semantic, "old_token_sha256")->string != field(semantic, "new_token_sha256")->string || field(semantic, "old_typed_ir_sha256")->string != field(semantic, "new_typed_ir_sha256")->string) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": semantic hash mismatch");
  const auto& output = required_field(raw, "output_abi", ValueKind::object, context).object;
  exact_object(output, {"cardinality", "canonical_slots", "extent", "logical_routes", "physical_names", "single_output_canonical"}, context + ".output_abi");
  required_field(output, "canonical_slots", ValueKind::array, context + ".output_abi");
  required_field(output, "cardinality", ValueKind::number, context + ".output_abi");
  required_field(output, "logical_routes", ValueKind::array, context + ".output_abi");
  required_field(output, "physical_names", ValueKind::array, context + ".output_abi");
  required_field(output, "single_output_canonical", ValueKind::boolean, context + ".output_abi");
  const auto& extent = required_field(output, "extent", ValueKind::object, context + ".output_abi").object;
  required_field(extent, "format", ValueKind::string, context + ".output_abi.extent");
  for (const auto name : {"height", "width"}) {
    const auto* dimension = field(extent, name);
    if (dimension == nullptr || (dimension->kind != ValueKind::string &&
        (dimension->kind != ValueKind::number || dimension->number <= 0.0 || std::trunc(dimension->number) != dimension->number)))
      throw std::invalid_argument("Malformed compatible compatibility row " + context + ": output extent");
  }
  const auto& outputs = field(raw, "outputs")->array;
  const auto& slots = field(output, "canonical_slots")->array;
  const auto& logical = field(output, "logical_routes")->array;
  const auto& physical = field(output, "physical_names")->array;
  const auto cardinality_value = field(output, "cardinality");
  if (cardinality_value->number <= 0 || std::trunc(cardinality_value->number) != cardinality_value->number ||
      static_cast<std::size_t>(cardinality_value->number) != outputs.size() || slots.size() != outputs.size() ||
      logical.size() != outputs.size() || physical.size() != outputs.size()) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": output ABI cardinality");
  for (std::size_t i = 0; i < outputs.size(); ++i) {
    if (outputs[i].kind != ValueKind::object || field(outputs[i].object, "slot") == nullptr ||
        field(outputs[i].object, "logical_route") == nullptr || field(outputs[i].object, "physical_name") == nullptr ||
        field(outputs[i].object, "slot")->number != static_cast<double>(i) ||
        field(outputs[i].object, "logical_route")->kind != ValueKind::string || field(outputs[i].object, "physical_name")->kind != ValueKind::string ||
        logical[i].kind != ValueKind::string || physical[i].kind != ValueKind::string ||
        field(outputs[i].object, "logical_route")->string != logical[i].string ||
        field(outputs[i].object, "physical_name")->string != physical[i].string ||
        slots[i].kind != ValueKind::number || slots[i].number != static_cast<double>(i) ||
        logical[i].string.empty() || physical[i].string.empty()) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": output ABI projection");
  }
  const auto& authority_pass = required_field(raw, "authority_pass", ValueKind::object, context).object;
  exact_object(authority_pass, {"name", "inputs", "outputs", "uniforms", "blend", "repeat"}, context + ".authority_pass");
  required_field(authority_pass, "name", ValueKind::string, context + ".authority_pass");
  required_field(authority_pass, "inputs", ValueKind::object, context + ".authority_pass");
  required_field(authority_pass, "outputs", ValueKind::object, context + ".authority_pass");
  required_field(authority_pass, "uniforms", ValueKind::object, context + ".authority_pass");
  required_field(authority_pass, "blend", ValueKind::boolean, context + ".authority_pass");
  const auto* repeat_value = field(authority_pass, "repeat");
  if (repeat_value == nullptr || (repeat_value->kind != ValueKind::null_value && repeat_value->kind != ValueKind::number)) {
    throw std::invalid_argument("Malformed compatible compatibility row " + context + ": authority pass repeat");
  }
  const auto& factory = required_field(raw, "factory", ValueKind::object, context).object;
  exact_object(factory, {"canonical", "emitted_factory", "legacy_public", "route", "typed_manifest_output", "typed_manifest_output_sha256"}, context + ".factory");
  for (const auto name : {"canonical", "emitted_factory", "legacy_public", "typed_manifest_output"}) nonempty_string(required_field(factory, name, ValueKind::string, context + ".factory"), context + ".factory." + std::string(name));
  sha256_field(required_field(factory, "typed_manifest_output_sha256", ValueKind::string, context + ".factory"), context + ".factory.typed_manifest_output_sha256");
  const auto& route = required_field(factory, "route", ValueKind::object, context + ".factory").object;
  const auto& route_kind = required_field(route, "kind", ValueKind::string, context + ".factory.route");
  if (route_kind.string == "typed_emitter") {
    exact_object(route, {"factory", "kind", "source", "source_sha256"}, context + ".factory.route");
    if (required_field(route, "factory", ValueKind::string, context + ".factory.route").string != field(factory, "canonical")->string) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": factory route identity");
  } else if (route_kind.string == "custom_adapter") {
    exact_object(route, {"binding_abi", "emitted_factory", "factory", "kind", "output_abi", "source", "source_sha256"}, context + ".factory.route");
    if (required_field(route, "factory", ValueKind::string, context + ".factory.route").string != field(factory, "canonical")->string || required_field(route, "emitted_factory", ValueKind::string, context + ".factory.route").string != field(factory, "emitted_factory")->string) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": custom route identity");
    const auto& abi = required_field(route, "binding_abi", ValueKind::object, context + ".factory.route").object;
    exact_object(abi, {"samplers", "uniforms"}, context + ".factory.route.binding_abi");
    for (const auto name : {"samplers", "uniforms"}) {
      const auto& entries = required_field(abi, name, ValueKind::array, context + ".factory.route.binding_abi");
      for (const auto& entry : entries.array) {
        if (entry.kind != ValueKind::object) throw std::invalid_argument("Malformed compatible compatibility row " + context + ": custom binding ABI");
        exact_object(entry.object, {"cpp_type", "name", "source"}, context + ".factory.route.binding_abi");
        nonempty_string(required_field(entry.object, "cpp_type", ValueKind::string, context), context + ".custom.cpp_type");
        nonempty_string(required_field(entry.object, "name", ValueKind::string, context), context + ".custom.name");
        nonempty_string(required_field(entry.object, "source", ValueKind::string, context), context + ".custom.source");
      }
    }
    const auto& route_output = required_field(route, "output_abi", ValueKind::object, context + ".factory.route").object;
    exact_object(route_output, {"cardinality", "cpp_type"}, context + ".factory.route.output_abi");
    if (required_field(route_output, "cardinality", ValueKind::number, context).number != 1 || required_field(route_output, "cpp_type", ValueKind::string, context).string != "glsl::Vec4") throw std::invalid_argument("Malformed compatible compatibility row " + context + ": custom output ABI");
  } else throw std::invalid_argument("Malformed compatible compatibility row " + context + ": factory route kind");
  safe_path_field(required_field(route, "source", ValueKind::string, context + ".factory.route"), false, context + ".factory.route.source");
  sha256_field(required_field(route, "source_sha256", ValueKind::string, context + ".factory.route"), context + ".factory.route.source_sha256");
}

void validate_authority_pass(const ProgramCompatibility& row, const PassDefinition& pass) {
  const auto* raw = field(row.raw, "authority_pass");
  if (raw == nullptr || raw->kind != ValueKind::object) throw std::invalid_argument("Canonical authority pass is missing: " + row.program_key);
  std::vector<std::pair<std::string, Value>> inputs;
  for (const auto& item : pass.inputs) inputs.emplace_back(item.first, Value::string_value(item.second));
  std::vector<std::pair<std::string, Value>> outputs;
  for (const auto& item : pass.outputs) outputs.emplace_back(item.first, Value::string_value(item.second));
  std::vector<std::pair<std::string, Value>> uniforms;
  for (const auto& item : pass.uniforms) uniforms.emplace_back(item.first, item.second);
  const Value expected = Value::object_value({
      {"name", Value::string_value(pass.name)},
      {"inputs", Value::object_value(std::move(inputs))},
      {"outputs", Value::object_value(std::move(outputs))},
      {"uniforms", Value::object_value(std::move(uniforms))},
      {"blend", Value::boolean_value(pass.blend.has_value() && pass.blend->enabled)},
      {"repeat", pass.repeat.value_or(Value::null())}});
  if (raw->object.size() != expected.object.size()) throw std::invalid_argument("Canonical authority pass does not match catalog: " + row.program_key);
  for (const auto& item : expected.object) {
    const auto* actual = field(raw->object, item.first);
    if (actual == nullptr || !same_authority_value(*actual, item.second)) throw std::invalid_argument("Canonical authority pass does not match catalog: " + row.program_key);
  }
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
    : canonical_programs_(catalog.canonical_programs), reference_passes_(catalog.reference_passes),
      scatter_(catalog.scatter), provenance_(catalog.provenance) {
  manifest_backed_ = true;
  definitions_.reserve(catalog.definitions.size());
  for (const auto& definition : catalog.definitions) register_effect(definition);
  const bool strict_manifest = !catalog.provenance.schema.empty();
  if (strict_manifest && (canonical_programs_.size() != 211 || reference_passes_.size() != 305 || !scatter_.has_value()))
    throw std::invalid_argument("Compatibility census cardinality drift");
  if (strict_manifest && (provenance_.counts.definitions != 205 || provenance_.counts.passes != 305 || provenance_.counts.reference_program_keys != 295 ||
      provenance_.counts.backend_programs != 212 || provenance_.counts.compatible_programs != 210 || provenance_.counts.incompatible_programs != 1 ||
      provenance_.counts.missing_passes != 93 || provenance_.counts.scatter_passes != 1 || provenance_.counts.executable_definitions != 166 ||
      provenance_.counts.incomplete_definitions != 39 || !hex_sha256(provenance_.compatibility_sha256)))
    throw std::invalid_argument("Compatibility provenance census drift");
  std::set<std::string> canonical_keys;
  canonical_views_.reserve(canonical_programs_.size());
  for (const auto& row : canonical_programs_) {
    if (!canonical_keys.insert(row.program_key).second || row.effect_id.empty() || row.program.empty() ||
        row.program_key != row.effect_id + ":" + row.program)
      throw std::invalid_argument("Malformed or duplicate canonical compatibility identity: " + row.program_key);
    if (row.status != "compatible" && row.status != "incompatible") throw std::invalid_argument("Invalid canonical compatibility status");
    if (row.status == "compatible" && !row.reasons.empty()) throw std::invalid_argument("Compatible canonical row has reasons: " + row.program_key);
    if (row.status == "incompatible" && row.reasons.empty()) throw std::invalid_argument("Incompatible canonical row has no reasons: " + row.program_key);
    const auto slash = row.effect_id.find('/');
    const auto* definition = slash == std::string::npos ? nullptr : get(row.effect_id.substr(0, slash), row.effect_id.substr(slash + 1));
    if (definition == nullptr) throw std::invalid_argument("Canonical compatibility effect is not registered: " + row.effect_id);
    std::size_t pass_index = definition->passes.size();
    for (std::size_t i = 0; i < definition->passes.size(); ++i) if (definition->passes[i].program == row.program) { pass_index = i; break; }
    if (pass_index == definition->passes.size()) throw std::invalid_argument("Canonical compatibility pass is not registered: " + row.program_key);
    if (row.status == "compatible") {
      validate_compatible_raw(row);
      const auto* raw_effect = field(row.raw, "effect_id");
      const auto* raw_program = field(row.raw, "program");
      const auto* raw_key = field(row.raw, "program_key");
      const auto* raw_status = field(row.raw, "status");
      if (raw_effect == nullptr || raw_effect->kind != ValueKind::string || raw_effect->string != row.effect_id ||
          raw_program == nullptr || raw_program->kind != ValueKind::string || raw_program->string != row.program ||
          raw_key == nullptr || raw_key->kind != ValueKind::string || raw_key->string != row.program_key ||
          raw_status == nullptr || raw_status->kind != ValueKind::string || raw_status->string != "compatible")
        throw std::invalid_argument("Canonical compatibility identity cross-check failed: " + row.program_key);
      validate_authority_pass(row, definition->passes[pass_index]);
    }
    graph::PassAdmission view;
    view.status = row.status == "compatible" ? graph::AvailabilityStatus::compatible : graph::AvailabilityStatus::incompatible;
    view.identity = {pass_index, definition->passes[pass_index].name, row.program_key};
    view.canonical_factory = row.canonical_factory.value_or("");
    view.source_sha256 = row.source_sha256.value_or("");
    view.semantic_sha256 = row.semantic_sha256.value_or("");
    view.dimensionality = string_field(row.raw, "dimensionality");
    view.draw_mode = string_field(row.raw, "draw_mode");
    for (const auto& reason : row.reasons) view.reasons.push_back({reason.first, reason.second});
    binding_array(field(row.raw, "samplers"), view.samplers);
    binding_array(field(row.raw, "uniforms"), view.uniforms);
    binding_array(field(row.raw, "outputs"), view.outputs);
    if (const auto* capabilities = field(row.raw, "capabilities"); capabilities != nullptr)
      for (const auto& item : capabilities->array) view.capabilities.push_back(item.string);
    canonical_views_.push_back(std::move(view));
  }
  std::set<std::tuple<std::string, std::size_t, std::string>> reference_keys;
  std::size_t expected_reference = 0;
  for (const auto& row : reference_passes_) {
    const auto identity = std::make_tuple(row.effect_id, row.pass_index, row.program_key);
    if (!reference_keys.insert(identity).second || row.status == "registered") throw std::invalid_argument("Malformed or duplicate reference pass compatibility");
    const auto slash = row.effect_id.find('/');
    const auto* definition = slash == std::string::npos ? nullptr : get(row.effect_id.substr(0, slash), row.effect_id.substr(slash + 1));
    if (definition == nullptr || row.pass_index >= definition->passes.size() || definition->passes[row.pass_index].name != row.pass_name ||
        definition->id + ":" + definition->passes[row.pass_index].program != row.program_key)
      throw std::invalid_argument("Reference pass identity does not join catalog: " + row.effect_id);
    if (strict_manifest) {
      std::size_t ordinal = 0;
      for (const auto& candidate : definitions_) {
        for (std::size_t index = 0; index < candidate.passes.size(); ++index) {
          if (ordinal == expected_reference && (candidate.id != row.effect_id || index != row.pass_index))
            throw std::invalid_argument("Reference pass authority ordering drift");
          ++ordinal;
        }
      }
      ++expected_reference;
    }
    const auto canonical = std::find_if(canonical_programs_.begin(), canonical_programs_.end(), [&](const auto& item) { return item.program_key == row.program_key; });
    auto expected_reasons = [](std::initializer_list<std::pair<std::string_view, std::string_view>> values) {
      std::vector<std::pair<std::string, std::string>> result;
      for (const auto& value : values) result.emplace_back(value.first, value.second);
      return result;
    };
    if (row.status == "compatible" || row.status == "incompatible") {
      if (canonical == canonical_programs_.end() || canonical->status != row.status) throw std::invalid_argument("Reference/canonical compatibility status mismatch: " + row.program_key);
      if (row.status == "compatible" && !row.reasons.empty()) throw std::invalid_argument("Compatible reference has reasons: " + row.program_key);
      if (row.status == "incompatible" && row.reasons != canonical->reasons) throw std::invalid_argument("Incompatible reference reason mismatch: " + row.program_key);
    } else if (row.status == "missing") {
      if (canonical != canonical_programs_.end() || (scatter_ && scatter_->program_key == row.program_key)) throw std::invalid_argument("Missing reference has a backend row: " + row.program_key);
      if (row.reasons != expected_reasons({{"missing_backend_program", row.program_key}})) throw std::invalid_argument("Missing reference reason mismatch: " + row.program_key);
    } else if (row.status == "scatter") {
      if (canonical != canonical_programs_.end() || !scatter_ || scatter_->program_key != row.program_key) throw std::invalid_argument("Invalid scatter reference row");
      if (row.reasons != expected_reasons({{"explicit_scatter_adapter", row.program_key}})) throw std::invalid_argument("Scatter reference reason mismatch: " + row.program_key);
    } else throw std::invalid_argument("Invalid reference compatibility status");
  }
  if (strict_manifest && expected_reference != 305) throw std::invalid_argument("Compatibility reference authority cardinality drift");
  if (scatter_ && (scatter_->program_key != "filter/wormhole:deposit" || scatter_->adapter != "noisemaker::scatter::wormhole::adapter" || scatter_->registry != "noisemaker::scatter::resolve_scatter_adapter" ||
      scatter_->draw_mode != "points" || scatter_->dimensionality != "image" || scatter_->count != "input" ||
      scatter_->input_texture != "inputTex" || scatter_->destination_mutation != "in_place_accumulate" ||
      !scatter_->blend || scatter_->uniforms.size() != 4 || scatter_->outputs.size() != 1 || scatter_->outputs[0].slot != 0 ||
      scatter_->outputs[0].physical_name != "fragColor" || scatter_->outputs[0].logical_route != "wormhole_accum" || scatter_->outputs[0].cpp_type != "glsl::Vec4" ||
      scatter_->uniforms[0].name != "kink" || scatter_->uniforms[1].name != "stride" || scatter_->uniforms[2].name != "rotation" || scatter_->uniforms[3].name != "wrap" ||
      std::any_of(scatter_->uniforms.begin(), scatter_->uniforms.end(), [](const auto& uniform) { return uniform.cpp_type != "double" || uniform.source != "effect_parameter" || uniform.name.empty(); }) ||
      scatter_->reasons != std::vector<std::pair<std::string, std::string>>{{"explicit_scatter_adapter", "filter/wormhole:deposit"}}))
    throw std::invalid_argument("Malformed scatter compatibility contract");
}

EffectRegistry::EffectRegistry(std::vector<EffectDefinition> definitions) {
  provenance_.schema = "noisemaker-cpp.execution-plan.custom";
  provenance_.cpu_behavioral_lock = "custom";
  provenance_.normalized_record_stream_sha256 = "custom";
  provenance_.compatibility_sha256 = "custom";
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
  auto folded = [](std::string value) {
    for (char& character : value) if (character >= 'A' && character <= 'Z') character = static_cast<char>(character - 'A' + 'a');
    return value;
  };
  std::sort(result.begin(), result.end(), [&](const auto* left, const auto* right) {
    const std::string left_folded = folded(left->id);
    const std::string right_folded = folded(right->id);
    if (left_folded != right_folded) return left_folded < right_folded;
    return left->id < right->id;
  });
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
  if (!manifest_backed_) {
    result.status = graph::AvailabilityStatus::compatible;
    return result;
  }
  const ReferencePassCompatibility* reference = nullptr;
  for (const auto& candidate : reference_passes_) if (candidate.effect_id == definition.id && candidate.pass_index == pass_index && candidate.program_key == result.identity.program_key) { reference = &candidate; break; }
  if (reference == nullptr) throw std::invalid_argument("Reference pass compatibility missing after validated construction");
  for (const auto& reason : reference->reasons) result.reasons.push_back({reason.first, reason.second});
  if (reference->status == "scatter") {
    result.status = graph::AvailabilityStatus::scatter;
    result.reasons = {{"explicit_scatter_adapter", result.identity.program_key}};
    return result;
  }
  result.status = reference->status == "compatible" ? graph::AvailabilityStatus::compatible :
                  (reference->status == "incompatible" ? graph::AvailabilityStatus::incompatible : graph::AvailabilityStatus::missing);
  const auto canonical = std::find_if(canonical_programs_.begin(), canonical_programs_.end(), [&](const auto& item) { return item.program_key == reference->program_key; });
  if (canonical != canonical_programs_.end()) {
    const std::size_t index = static_cast<std::size_t>(canonical - canonical_programs_.begin());
    const auto& view = canonical_views_[index];
    result.canonical_factory = view.canonical_factory;
    result.source_sha256 = view.source_sha256;
    result.semantic_sha256 = view.semantic_sha256;
    result.dimensionality = view.dimensionality;
    result.draw_mode = view.draw_mode;
    result.capabilities = view.capabilities;
    result.samplers = view.samplers;
    result.uniforms = view.uniforms;
    result.outputs = view.outputs;
  }
  return result;
}

}  // namespace noisemaker::effects
