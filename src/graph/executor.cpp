#include "noisemaker/graph/executor.hpp"

#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/texture_format.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdlib>
#include <initializer_list>
#include <locale.h>
#if defined(__APPLE__)
#include <xlocale.h>  // Darwin declares strtod_l here, not in <locale.h>.
#endif
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_set>

namespace noisemaker::graph {

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

[[nodiscard]] const PlanValue* parameter(const EffectStep& step,
                                         std::string_view name) {
  for (const auto& item : step.params) {
    if (item.name == name) return &item.value;
  }
  return nullptr;
}

// The executor resolves every declared sampler route against the arena while
// it still owns the resources, then hands the binder a plain value table.
// The arena itself is never reachable from a binding callback.
struct ResolvedSamplerRoutes {
  std::vector<std::pair<std::string_view, const noisemaker::Surface*>> entries;
};

const noisemaker::Surface* lookup_resolved_sampler_route(
    void* context, std::string_view route) {
  const auto* resolved = static_cast<const ResolvedSamplerRoutes*>(context);
  if (resolved == nullptr) return nullptr;
  for (const auto& entry : resolved->entries) {
    if (entry.first == route) return entry.second;
  }
  return nullptr;
}

// The binding-ABI digest grammar. Four independent implementations produce
// these bytes: the typed-slice generator bakes them into the route table from
// the authenticated compatibility document, the registry serializes the same
// document into the plan, this one serializes the value-owned admission, and
// the JS oracle mirrors it for the cross-language plan stream. Dispatch
// requires the admission-derived sections to equal the generated anchors, so a
// reordered or retyped ordered ABI, a forged output ABI or extent, or a forged
// compile define cannot hide behind the identity strings. Field values are
// identifiers, hashes, or format names and never contain the separators.
struct BindingAbiSections {
  std::string samplers;
  std::string uniforms;
  std::string outputs;
  std::string extent;
  std::string defines;
};

[[nodiscard]] BindingAbiSections binding_abi_sections(const PassAdmission& admission) {
  const auto bindings = [](std::string_view name,
                           const std::vector<CompatibilityBinding>& items) {
    std::string bytes(name);
    bytes.push_back('\x1e');
    for (const auto& item : items) {
      for (const auto* field : {&item.name, &item.type, &item.source,
                                &item.source_name, &item.resource, &item.cpp_type}) {
        bytes.append(*field);
        bytes.push_back('\x1f');
      }
    }
    bytes.push_back('\x1e');
    return bytes;
  };
  BindingAbiSections sections;
  sections.samplers = bindings("samplers", admission.samplers);
  sections.uniforms = bindings("uniforms", admission.uniforms);
  sections.outputs = "outputs\x1e";
  for (const auto& output : admission.outputs) {
    sections.outputs += std::to_string(output.slot) + '\x1f';
    sections.outputs += output.physical_name + '\x1f';
    sections.outputs += output.logical_route + '\x1f';
    sections.outputs += output.cpp_type + '\x1f';
  }
  sections.outputs.push_back('\x1e');
  sections.extent = "extent\x1e" + admission.output_extent.width + '\x1f' +
                    admission.output_extent.height + '\x1f' +
                    admission.output_extent.format + '\x1f' + '\x1e';
  sections.defines = "defines\x1e";
  for (const auto& define : admission.compile_defines) {
    sections.defines += define.name + '\x1f' + define.cpp_type + '\x1f' +
                        define.source + '\x1f';
  }
  sections.defines.push_back('\x1e');
  return sections;
}


// Canonical text for a define value in a diagnostic: integral values print
// without a fractional part so the message reads like the authority's own.
[[nodiscard]] std::string number_text(double value) {
  if (std::isfinite(value) && std::trunc(value) == value &&
      std::fabs(value) < 9007199254740992.0) {
    return std::to_string(static_cast<long long>(value));
  }
  std::ostringstream text;
  text.precision(17);
  text << value;
  return text.str();
}

// Look one baked define up in the generated `NAME=VALUE;NAME=VALUE` list.
[[nodiscard]] std::optional<double> baked_define_value(std::string_view defines,
                                                       std::string_view name) {
  std::size_t position = 0;
  while (position < defines.size()) {
    const auto end = defines.find(';', position);
    const auto entry = defines.substr(position, end == std::string_view::npos
                                                    ? std::string_view::npos
                                                    : end - position);
    const auto split = entry.find('=');
    if (split != std::string_view::npos && entry.substr(0, split) == name) {
      double value = 0.0;
      if (!parse_c_number(entry.substr(split + 1), value)) return std::nullopt;
      return value;
    }
    if (end == std::string_view::npos) break;
    position = end + 1;
  }
  return std::nullopt;
}

[[nodiscard]] bool is_sha256(std::string_view value) noexcept {
  if (value.size() != 64U) return false;
  return value.find_first_not_of("0123456789abcdef") == std::string_view::npos;
}

// The CPU authority publishes a non-surface parameter under
// `define ?? uniform ?? name` and a surface parameter under
// `texture ?? name`; see createCanonicalBindings/buildBindings.
[[nodiscard]] std::string_view bound_uniform_name(
    const effects::ParameterDefinition& declared) noexcept {
  if (declared.define.has_value()) return *declared.define;
  if (declared.uniform.has_value()) return *declared.uniform;
  return declared.name;
}

[[nodiscard]] std::string_view bound_texture_name(
    const effects::ParameterDefinition& declared) noexcept {
  return declared.texture.has_value() ? std::string_view(*declared.texture)
                                      : std::string_view(declared.name);
}

// The authority's initializeCanonicalResources(): every declared texture that
// no pass of the effect produces is created up front. The default branch
// clears it at the declared extent and format; `overlayTex` on three effects
// instead reads a dedicated CPU worm-overlay adapter that this port does not
// implement, so that route fails closed instead of guessing a zero fill.
[[nodiscard]] bool is_worm_overlay_resource(std::string_view effect_id,
                                            std::string_view texture) noexcept {
  return texture == "overlayTex" &&
         (effect_id == "filter/fibers" || effect_id == "filter/scratches" ||
          effect_id == "filter/strayHair");
}

[[nodiscard]] std::unordered_set<std::string> unproduced_declared_textures(
    const effects::EffectDefinition& definition) {
  std::unordered_set<std::string> produced;
  for (const auto& pass : definition.passes) {
    for (const auto& output : pass.outputs) produced.insert(output.second);
  }
  std::unordered_set<std::string> result;
  for (const auto& texture : definition.textures) {
    if (produced.find(texture.name) == produced.end()) result.insert(texture.name);
  }
  return result;
}

[[nodiscard]] const effects::ParameterDefinition* surface_parameter_for_route(
    const effects::EffectDefinition& definition, std::string_view route) {
  for (const auto& declared : definition.parameters) {
    if (declared.type == "surface" && bound_texture_name(declared) == route) {
      return &declared;
    }
  }
  return nullptr;
}

// The authority's buildBindings() uniform map: a surface parameter publishes
// only its `colorModeUniform` flag (0 when unbound, 1 otherwise) and every
// other parameter publishes its value under `define ?? uniform ?? name`.
[[nodiscard]] const PlanValue* bound_uniform_value(
    const effects::EffectDefinition& definition, const EffectStep& step,
    std::string_view uniform_name, PlanValue& owned) {
  for (const auto& declared : definition.parameters) {
    if (declared.type == "surface") {
      if (!declared.color_mode_uniform.has_value() ||
          *declared.color_mode_uniform != uniform_name) {
        continue;
      }
      const auto* bound = parameter(step, declared.name);
      owned = PlanValue::number_value(
          bound != nullptr && bound->kind == PlanValue::Kind::surface ? 1.0 : 0.0);
      return &owned;
    }
    if (bound_uniform_name(declared) == uniform_name) {
      return parameter(step, declared.name);
    }
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
      // textureDimension(): an absent spec resolves to the render extent.
      // An unrecognized spec still fails closed below.
      if (expression.raw.kind == effects::ValueKind::null_value) {
        value = static_cast<double>(render_extent);
        break;
      }
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

// The single authenticated fragment output symbol.  Every one of the 211
// canonical compatibility rows declares exactly one `fragColor` /
// `glsl::Vec4` output; the authority pass may name its own key ("color" on
// 19 rows), so the two names are checked against their own authorities.
constexpr std::string_view kFragmentOutputSymbol = "fragColor";

void validate_pass_output_abi(const EffectStep& step,
                              const effects::PassDefinition& pass,
                              const PassAdmission& admission,
                              std::size_t pass_index) {
  const std::string_view program_key = admission.identity.program_key;
  if (pass.outputs.size() != 1U || admission.outputs.size() != 1U) {
    throw GraphError(GraphErrorCode::unsupported_mrt,
                     "exactly one fragment output is supported",
                     step.effect.id, pass_index, pass.name,
                     std::string(program_key));
  }
  const auto& declared = pass.outputs.front();
  const auto& output = admission.outputs.front();
  if (output.slot != 0U || output.physical_name != kFragmentOutputSymbol ||
      output.logical_route != declared.second || declared.second.empty() ||
      declared.first.empty() || output.cpp_type != "glsl::Vec4") {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass output ABI differs from owned definition",
                     step.effect.id, pass_index, pass.name,
                     std::string(program_key));
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
      !authority_repeat_matches(pass, admission.authority_pass)) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass routing differs from admitted ABI",
                     definition.id, pass_index, pass.name,
                     expected_program_key);
  }
  validate_pass_output_abi(step, pass, admission, pass_index);
}

[[nodiscard]] GraphError binding_error(const EffectStep& step,
                                       const PassAdmission& admission,
                                       GraphErrorCode code,
                                       std::string detail) {
  return GraphError(code, std::move(detail), step.effect.id,
                    admission.identity.index, admission.identity.name,
                    admission.identity.program_key);
}

// The authority's buildBindings() overrides a classicNoisedeck effect's
// palette uniforms from its own built-in palette table whenever the effect's
// `palette` parameter selects an entry:
//
//   renderer.js: const entry = Number.isInteger(paletteIndex) && paletteIndex > 0
//                  ? paletteData[paletteIndex - 1] : null
//                if (entry) { uniforms.paletteAmp = entry.slice(0, 3); ... }
//
// This port has not yet ported `paletteData` (55 x 16 authority values), so it
// would bind the plan's own palette uniforms instead. That is invisible at
// settings whose kernel ignores them and wrong everywhere else, so the route
// is refused rather than rendered from the wrong values.
void authenticate_palette_override(const EffectStep& step,
                                   const PassAdmission& admission,
                                   const effects::EffectDefinition& definition) {
  if (definition.name_space != "classicNoisedeck") return;
  for (const auto& declared : definition.parameters) {
    if (declared.type != "palette") continue;
    const auto* selected = parameter(step, declared.name);
    if (selected == nullptr) {
      // As above: unreachable from a compiled plan, refused anyway so the
      // guard cannot be sidestepped by omission.
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "parameter " + declared.name +
                              " selects the palette but the step carries no value for it");
    }
    const double index = plan_number(selected);
    if (!std::isfinite(index) || std::trunc(index) != index || index <= 0.0) return;
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "parameter " + declared.name + " selects palette entry " +
                            number_text(index) +
                            " and the authority overrides the palette uniforms from its"
                            " built-in table, which this port has not ported");
  }
}

// Program keys whose emitted typed kernel is measured not byte-equivalent to
// the pinned authority's own execution of the same program. The authority runs
// eleven keys through hand-written CPU adapters
// (oracle/.../src/effects/adapters/index.js); the compatibility document
// classifies ten of them as `typed_emitter`, and eight of those ten do agree
// with their adapter byte-for-byte. These do not, so they are refused with the
// measured reason rather than dispatched to wrong bytes. Closing them needs a
// compatibility reclassification plus a C++ adapter port.
struct MeasuredParityExclusion {
  std::string_view program_key;
  std::string_view reason;
};

constexpr std::array<MeasuredParityExclusion, 2> kMeasuredParityExclusions = {{
    {"filter/snow:snow",
     "the authority executes a hand-written CPU adapter for this program and the"
     " emitted typed kernel is measured divergent (499 of 748 RGBA8 bytes at 17x11)"},
    {"synth/testPattern:testPattern",
     "the emitted typed kernel is measured divergent from the authority at grid"
     " boundaries (2 pixels, 6 of 748 RGBA8 bytes at 17x11)"},
}};

void authenticate_measured_parity(const EffectStep& step,
                                  const PassAdmission& admission) {
  for (const auto& exclusion : kMeasuredParityExclusions) {
    if (admission.identity.program_key == exclusion.program_key) {
      throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                          std::string(exclusion.reason));
    }
  }
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
        // Declared textures with no producer are initialized by the executor
        // before the first pass runs, so they are available routes from the
        // start of the step.
        const auto declared_textures = unproduced_declared_textures(snapshot.definition);
        for (const auto& declared : declared_textures) {
          if (!is_worm_overlay_resource(snapshot.definition.id, declared)) continue;
          throw GraphError(GraphErrorCode::unavailable_pass,
                           "declared texture requires the canonical CPU worm-overlay adapter",
                           effect.effect.id, 0, {}, declared);
        }
        for (std::size_t pass_index = 0; pass_index < snapshot.definition.passes.size(); ++pass_index) {
          const auto& pass = snapshot.definition.passes[pass_index];
          const auto& admission = snapshot.admissions[pass_index];
          validate_pass_identity_and_output(effect, snapshot.definition, pass,
                                            admission, pass_index);
          validate_ordinary_pass_metadata(effect, admission, pass, pass_index);
          // The per-binding checks run first so a malformed ABI reports its
          // own precise failure; the route digest below then catches whatever
          // only an ordering or identity comparison can see.
          const BindingMaterializationContext preflight_context{
              &inputs, &snapshot.definition, inputs.width, inputs.height};
          preflight_pass_abi(effect, admission, pass, preflight_context);
          const auto* route = authenticate_factory_route(effect, admission);
          authenticate_compile_define_parameters(effect, admission,
                                                 snapshot.definition, *route);
          authenticate_palette_override(effect, admission, snapshot.definition);
          authenticate_measured_parity(effect, admission);
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
            const auto require_named = [&](const std::string& route) {
              if (produced.find(route) == produced.end() &&
                  available_routes.find(route) == available_routes.end()) {
                throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              }
            };
            const auto require_current = [&] {
              if (!have_current) throw GraphError(GraphErrorCode::read_before_write, "input is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
            };
            // A surface parameter owns its declared texture route: an unbound
            // one resolves to the authority's empty surface, so it never needs
            // a producer.
            if (const auto* declared = surface_parameter_for_route(snapshot.definition, input.second);
                declared != nullptr) {
              const auto* bound = parameter(effect, declared->name);
              if (bound == nullptr) {
                throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              }
              if (bound->kind == PlanValue::Kind::null_value) continue;
              if (bound->kind != PlanValue::Kind::surface) {
                throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              }
              if (bound->surface.kind == SurfaceReference::Kind::input) require_current();
              else if (bound->surface.kind == SurfaceReference::Kind::named) require_named(bound->surface.name);
              else throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              continue;
            }
            if (input.second == "inputTex") require_current();
            else if (declared_textures.find(input.second) == declared_textures.end()) {
              require_named(input.second);
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
        std::unordered_set<std::string> outputs;
        for (const auto& output : pass.outputs) {
          if (!outputs.insert(output.second).second) {
            throw GraphError(GraphErrorCode::duplicate_output, "duplicate pass output route",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
        }
        authenticate_compile_define_parameters(
            *effect, admission, snapshot.definition,
            *authenticate_factory_route(*effect, admission));
      }
    }
  }
}


[[nodiscard]] bool is_reserved_name(std::string_view name) noexcept {
  return name == "resolution" || name == "fullResolution" ||
         name == "renderScale" || name == "tileOffset" || name == "time" ||
         name == "frame" || name == "seed" || name == "deltaTime";
}

[[nodiscard]] bool is_finite_plan_number(const PlanValue& value) noexcept {
  return value.kind == PlanValue::Kind::number && std::isfinite(value.number);
}

[[nodiscard]] bool is_integral_plan_number(const PlanValue& value) noexcept {
  return is_finite_plan_number(value) && std::trunc(value.number) == value.number;
}

[[nodiscard]] std::size_t vector_width(std::string_view cpp_type) noexcept {
  if (cpp_type == "glsl::Vec2" || cpp_type == "glsl::IVec2") return 2U;
  if (cpp_type == "glsl::Vec3" || cpp_type == "glsl::IVec3") return 3U;
  if (cpp_type == "glsl::Vec4" || cpp_type == "glsl::IVec4") return 4U;
  return 0U;
}

void validate_uniform_abi_shape(const EffectStep& step,
                                const PassAdmission& admission,
                                const CompatibilityBinding& abi) {
  static constexpr std::array<std::pair<std::string_view, std::string_view>, 8>
      kTypes = {{{"float", "float"},
                 {"double", "double"},
                 {"int", "std::int32_t"},
                 {"uint", "std::uint32_t"},
                 {"bool", "bool"},
                 {"vec2", "glsl::Vec2"},
                 {"vec3", "glsl::Vec3"},
                 {"vec4", "glsl::Vec4"}}};
  bool known = false;
  for (const auto& [type, cpp_type] : kTypes) {
    if (abi.type == type && abi.cpp_type == cpp_type) {
      known = true;
      break;
    }
  }
  known = known || (abi.type == "ivec2" && abi.cpp_type == "glsl::IVec2") ||
          (abi.type == "vec4[267]" && abi.cpp_type == "vec4[267]");
  if (!known || abi.name.empty() || abi.source_name.empty()) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "uniform ABI type or name is unsupported");
  }
  // The authenticated compatibility schema gives a uniform exactly
  // {name, type, cpp_type, source, source_name}; a resource route belongs to
  // a sampler and never to a uniform.
  if (!abi.resource.empty()) {
    throw binding_error(step, admission, GraphErrorCode::missing_binding,
                        "uniform ABI must not declare a resource route");
  }
  if (abi.source == "reserved_runtime_state") {
    if (!is_reserved_name(abi.source_name) || abi.name != abi.source_name) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "unknown reserved runtime binding");
    }
  } else if (abi.source != "effect_parameter" &&
             abi.source != "pass_literal" && abi.source != "pass_derived") {
    throw binding_error(step, admission, GraphErrorCode::missing_binding,
                        "uniform source is not materializable");
  }
}

[[nodiscard]] PlanValue catalog_to_plan(const effects::Value& value) {
  switch (value.kind) {
    case effects::ValueKind::null_value: return PlanValue::null();
    case effects::ValueKind::boolean: return PlanValue::boolean_value(value.boolean);
    case effects::ValueKind::number: return PlanValue::number_value(value.number);
    case effects::ValueKind::string: return PlanValue::string_value(value.string);
    case effects::ValueKind::array: {
      std::vector<PlanValue> values;
      values.reserve(value.array.size());
      for (const auto& item : value.array) values.push_back(catalog_to_plan(item));
      return PlanValue::array_value(std::move(values));
    }
    case effects::ValueKind::object:
      return PlanValue::null();
  }
  return PlanValue::null();
}

[[nodiscard]] glsl::UniformValue materialize_plan_value(
    const PlanValue& supplied, std::string_view cpp_type,
    const EffectStep& step, const PassAdmission& admission,
    std::string_view binding_name) {
  const auto fail = [&](std::string detail) -> glsl::UniformValue {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        std::string(binding_name) + ": " + std::move(detail));
  };
  // A boolean parameter bound to a numeric GLSL uniform carries the
  // authority's Number(boolean) value. Forty-nine boolean parameters keep a
  // bool ABI; six are declared numeric by their pinned program.
  const bool coerce_boolean =
      supplied.kind == PlanValue::Kind::boolean && cpp_type != "bool";
  const PlanValue coerced =
      coerce_boolean ? PlanValue::number_value(supplied.boolean ? 1.0 : 0.0)
                     : PlanValue::null();
  const PlanValue& value = coerce_boolean ? coerced : supplied;
  if (cpp_type == "float") {
    if (!is_finite_plan_number(value)) return fail("expected finite float");
    return noisemaker::f32(value.number);
  }
  if (cpp_type == "double") {
    if (!is_finite_plan_number(value)) return fail("expected finite double");
    return value.number;
  }
  if (cpp_type == "std::int32_t") {
    if (!is_integral_plan_number(value) ||
        value.number < static_cast<double>(std::numeric_limits<std::int32_t>::min()) ||
        value.number > static_cast<double>(std::numeric_limits<std::int32_t>::max())) {
      return fail("expected int32");
    }
    return static_cast<std::int32_t>(value.number);
  }
  if (cpp_type == "std::uint32_t") {
    if (!is_integral_plan_number(value) || value.number < 0.0 ||
        value.number > static_cast<double>(std::numeric_limits<std::uint32_t>::max())) {
      return fail("expected uint32");
    }
    return static_cast<std::uint32_t>(value.number);
  }
  if (cpp_type == "bool") {
    if (value.kind != PlanValue::Kind::boolean) return fail("expected bool");
    return value.boolean;
  }
  const std::size_t width = vector_width(cpp_type);
  if (width != 0U) {
    if (value.kind != PlanValue::Kind::array || value.array.size() != width) {
      return fail("vector has the wrong width");
    }
    std::array<float, 4> f{};
    std::array<std::int32_t, 4> i{};
    for (std::size_t index = 0; index < width; ++index) {
      if (cpp_type.starts_with("glsl::I")) {
        if (!is_integral_plan_number(value.array[index]) ||
            value.array[index].number < static_cast<double>(std::numeric_limits<std::int32_t>::min()) ||
            value.array[index].number > static_cast<double>(std::numeric_limits<std::int32_t>::max())) {
          return fail("integral vector has an invalid lane");
        }
        i[index] = static_cast<std::int32_t>(value.array[index].number);
      } else {
        if (!is_finite_plan_number(value.array[index])) return fail("vector has an invalid lane");
        f[index] = noisemaker::f32(value.array[index].number);
      }
    }
    if (cpp_type == "glsl::Vec2") return glsl::Vec2(f[0], f[1]);
    if (cpp_type == "glsl::Vec3") return glsl::Vec3(f[0], f[1], f[2]);
    if (cpp_type == "glsl::Vec4") return glsl::Vec4(f[0], f[1], f[2], f[3]);
    if (cpp_type == "glsl::IVec2") return glsl::IVec2(i[0], i[1]);
  }
  if (cpp_type == "vec4[267]") {
    if (value.kind != PlanValue::Kind::array || value.array.size() != 267U) {
      return fail("remap block has the wrong cardinality");
    }
    glsl::RemapUniformData result;
    for (std::size_t index = 0; index < 267U; ++index) {
      const auto& row = value.array[index];
      if (row.kind != PlanValue::Kind::array || row.array.size() != 4U) {
        return fail("remap block row has the wrong width");
      }
      for (std::size_t lane = 0; lane < 4U; ++lane) {
        if (!is_finite_plan_number(row.array[lane])) return fail("remap block has an invalid lane");
        result.data[index][lane] = noisemaker::f32(row.array[lane].number);
      }
    }
    return result;
  }
  return fail("unsupported uniform C++ type");
}

[[nodiscard]] glsl::UniformValue reserved_uniform(
    const CompatibilityBinding& abi, const BindingMaterializationContext& context,
    const EffectStep& step, const PassAdmission& admission) {
  if (context.inputs == nullptr) {
    throw binding_error(step, admission, GraphErrorCode::missing_binding,
                        "runtime inputs are missing");
  }
  const auto& inputs = *context.inputs;
  if (abi.source_name == "tileOffset") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(0.0), PlanValue::number_value(0.0)}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "fullResolution") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(static_cast<double>(inputs.width)), PlanValue::number_value(static_cast<double>(inputs.height))}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "resolution") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(static_cast<double>(context.destination_width)), PlanValue::number_value(static_cast<double>(context.destination_height))}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "renderScale") return materialize_plan_value(PlanValue::number_value(1.0), abi.cpp_type, step, admission, abi.name);
  if (abi.source_name == "time") return materialize_plan_value(PlanValue::number_value(inputs.time), abi.cpp_type, step, admission, abi.name);
  if (abi.source_name == "frame") return materialize_plan_value(PlanValue::number_value(static_cast<double>(inputs.frame)), abi.cpp_type, step, admission, abi.name);
  if (abi.source_name == "seed") return materialize_plan_value(PlanValue::number_value(inputs.seed), abi.cpp_type, step, admission, abi.name);
  if (abi.source_name == "deltaTime") return materialize_plan_value(PlanValue::number_value(inputs.delta_time), abi.cpp_type, step, admission, abi.name);
  throw binding_error(step, admission, GraphErrorCode::missing_binding,
                      "unknown reserved runtime binding");
}

[[nodiscard]] const PlanValue* pass_literal_value(
    const effects::PassDefinition& pass, std::string_view name,
    PlanValue& owned) {
  for (const auto& uniform : pass.uniforms) {
    if (uniform.first == name) {
      owned = catalog_to_plan(uniform.second);
      return &owned;
    }
  }
  return nullptr;
}

[[nodiscard]] glsl::UniformValue resolve_uniform(
    const CompatibilityBinding& abi, const EffectStep& step,
    const PassAdmission& admission, const effects::PassDefinition& pass,
    const BindingMaterializationContext& context) {
  validate_uniform_abi_shape(step, admission, abi);
  if (abi.source == "reserved_runtime_state") return reserved_uniform(abi, context, step, admission);
  if (abi.source == "pass_derived") {
    // The runtime always owns an authenticated resolver; the callback seam
    // exists so a caller can substitute an equivalently authenticated one.
    const auto resolver = context.resolve_derived != nullptr
                              ? context.resolve_derived
                              : &resolve_authenticated_pass_derived;
    glsl::UniformValue resolved;
    if (!resolver(context.derived_context, abi.source_name, abi.name, step,
                  admission, pass, context, resolved)) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "pass-derived source is unknown or unavailable");
    }
    const bool correct =
        (abi.cpp_type == "float" && std::holds_alternative<float>(resolved)) ||
        (abi.cpp_type == "double" && std::holds_alternative<double>(resolved)) ||
        (abi.cpp_type == "std::int32_t" && std::holds_alternative<std::int32_t>(resolved)) ||
        (abi.cpp_type == "std::uint32_t" && std::holds_alternative<std::uint32_t>(resolved)) ||
        (abi.cpp_type == "bool" && std::holds_alternative<bool>(resolved)) ||
        (abi.cpp_type == "glsl::Vec2" && std::holds_alternative<glsl::Vec2>(resolved)) ||
        (abi.cpp_type == "glsl::Vec3" && std::holds_alternative<glsl::Vec3>(resolved)) ||
        (abi.cpp_type == "glsl::Vec4" && std::holds_alternative<glsl::Vec4>(resolved)) ||
        (abi.cpp_type == "glsl::IVec2" && std::holds_alternative<glsl::IVec2>(resolved)) ||
        (abi.cpp_type == "vec4[267]" && std::holds_alternative<glsl::RemapUniformData>(resolved));
    if (!correct) throw binding_error(step, admission, GraphErrorCode::binding_type, "pass-derived value has the wrong C++ type");
    return resolved;
  }
  PlanValue owned;
  const PlanValue* value = nullptr;
  if (abi.source == "effect_parameter") {
    value = parameter(step, abi.source_name);
    // A surface parameter contributes no uniform of its own; it publishes the
    // authority's colorModeUniform flag, which is 0 when the surface is
    // unbound and 1 otherwise.
    if (context.definition != nullptr) {
      for (const auto& declared : context.definition->parameters) {
        if (declared.name != abi.source_name || declared.type != "surface") continue;
        if (!declared.color_mode_uniform.has_value() ||
            *declared.color_mode_uniform != abi.name) {
          throw binding_error(step, admission, GraphErrorCode::missing_binding,
                              "surface parameter has no color-mode uniform");
        }
        owned = PlanValue::number_value(
            value != nullptr && value->kind == PlanValue::Kind::surface ? 1.0 : 0.0);
        return materialize_plan_value(owned, abi.cpp_type, step, admission, abi.name);
      }
    }
    // The authority's effectParams(): when the step owns a `seed` parameter
    // and the DSL did not name it explicitly, the render seed replaces the
    // parameter's own value. An absent parameter is a missing binding, not a
    // silent fallback.
    if (abi.source_name == "seed" && value != nullptr &&
        std::find(step.explicit_params.begin(), step.explicit_params.end(), "seed") == step.explicit_params.end()) {
      return reserved_uniform({abi.name, abi.type, "reserved_runtime_state", "seed", {}, abi.cpp_type}, context, step, admission);
    }
  } else {
    value = pass_literal_value(pass, abi.source_name, owned);
  }
  if (value == nullptr) throw binding_error(step, admission, GraphErrorCode::missing_binding, "uniform value is missing");
  return materialize_plan_value(*value, abi.cpp_type, step, admission, abi.name);
}

void validate_pass_controls(const EffectStep& step, const PassAdmission& admission,
                            const effects::PassDefinition& pass) {
  if (admission.status != AvailabilityStatus::compatible) {
    throw binding_error(step, admission,
                        admission.status == AvailabilityStatus::scatter ? GraphErrorCode::unsupported_scatter : GraphErrorCode::unavailable_pass,
                        "pass is not compatible");
  }
  if (admission.dimensionality != "image") throw binding_error(step, admission, GraphErrorCode::unsupported_draw_mode, "only image dimensionality is supported");
  if (admission.draw_mode != "fragment" || (pass.draw_mode.has_value() && *pass.draw_mode != "fragment")) throw binding_error(step, admission, GraphErrorCode::unsupported_draw_mode, "only fragment draw mode is supported");
  if (pass.draw_buffers.has_value() && (pass.draw_buffers->kind != effects::ValueKind::number || !std::isfinite(pass.draw_buffers->number) || pass.draw_buffers->number != 1.0)) throw binding_error(step, admission, GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported");
  if (pass.repeat.has_value() && pass.repeat->kind != effects::ValueKind::number && pass.repeat->kind != effects::ValueKind::string) throw binding_error(step, admission, GraphErrorCode::invalid_options, "repeat must be numeric or a uniform name");
  if (pass.repeat.has_value() && pass.repeat->kind == effects::ValueKind::number && (!std::isfinite(pass.repeat->number) || pass.repeat->number < 0.0)) throw binding_error(step, admission, GraphErrorCode::invalid_options, "repeat must be finite and non-negative");
  if (pass.conditions.has_value() && pass.conditions->kind != effects::ValueKind::object) throw binding_error(step, admission, GraphErrorCode::invalid_options, "conditions must be an object");
}

}  // namespace

const FactoryRouteDescriptor* find_factory_route(
    std::span<const FactoryRouteDescriptor> routes,
    std::string_view program_key,
    std::string_view canonical_factory) noexcept {
  for (const auto& route : routes) {
    if (route.program_key == program_key &&
        route.canonical_factory == canonical_factory) {
      return &route;
    }
  }
  return nullptr;
}

std::span<const FactoryRouteDescriptor> canonical_factory_routes() {
  // One checked projection of the generated canonical view.  The generated
  // table is the source of dispatch truth; this validates its shape once and
  // republishes it in the executor's own descriptor type.  A malformed row is
  // a build-time defect, so it fails closed for every subsequent execution.
  static const std::vector<FactoryRouteDescriptor> routes = [] {
    std::vector<FactoryRouteDescriptor> result;
    const auto generated_routes = generated::canonical_routes();
    result.reserve(generated_routes.size());
    std::unordered_set<std::string> pairs;
    for (const auto& route : generated_routes) {
      const bool known_kind = route.route_kind == "typed_emitter" ||
                              route.route_kind == "custom_adapter";
      if (route.key.empty() || route.canonical_factory.empty() ||
          route.emitted_factory.empty() || !known_kind ||
          !is_sha256(route.source_sha256) ||
          !is_sha256(route.typed_abi_sha256) || route.bind == nullptr ||
          !pairs.insert(std::string(route.key) + "\x1f" +
                        std::string(route.canonical_factory)).second) {
        throw GraphError(GraphErrorCode::invalid_snapshot,
                         "generated canonical route table is malformed", {}, 0,
                         {}, std::string(route.key));
      }
      result.push_back({route.key, route.canonical_factory,
                        route.emitted_factory, route.route_kind,
                        route.source_sha256, route.typed_abi_sha256,
                        route.define_contract, route.defines,
                        route.sampler_abi_sha256, route.uniform_abi_sha256,
                        route.output_abi_sha256, route.output_extent_sha256,
                        route.compile_define_abi_sha256, route.bind});
    }
    return result;
  }();
  return routes;
}

const FactoryRouteDescriptor* authenticate_factory_route(
    const EffectStep& step, const PassAdmission& admission,
    std::span<const FactoryRouteDescriptor> routes) {
  const auto table = routes.empty() ? canonical_factory_routes() : routes;
  const auto* route = find_factory_route(table, admission.identity.program_key,
                                         admission.canonical_factory);
  if (route == nullptr || route->bind == nullptr) {
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "canonical factory route is not admitted");
  }
  // A key/factory pair alone is not provenance.  Every remaining descriptor
  // field must equal the value-owned admission before the payload is used.
  if (route->emitted_factory != admission.emitted_factory ||
      route->route_kind != admission.route_kind ||
      route->source_sha256 != admission.source_sha256 ||
      route->typed_abi_sha256 != admission.typed_abi_sha256) {
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "generated route metadata differs from the admission");
  }
  // The identity strings do not themselves cover the ordered ABI. Each section
  // of the admission's own ordered lists is re-digested and compared to the
  // generated anchor, which the typed-slice generator baked from the
  // authenticated compatibility document -- an authority outside the plan.
  // Every section reports its own code and detail.
  const auto sections = binding_abi_sections(admission);
  const std::array<std::tuple<const std::string*, std::string_view, GraphErrorCode,
                              std::string_view>, 5>
      anchored = {{
          {&sections.samplers, route->sampler_abi_sha256, GraphErrorCode::missing_binding,
           "ordered sampler ABI differs from the generated route anchor"},
          {&sections.uniforms, route->uniform_abi_sha256, GraphErrorCode::binding_type,
           "ordered uniform ABI differs from the generated route anchor"},
          {&sections.outputs, route->output_abi_sha256, GraphErrorCode::invalid_snapshot,
           "output ABI differs from the generated route anchor"},
          {&sections.extent, route->output_extent_sha256, GraphErrorCode::invalid_format,
           "output extent differs from the generated route anchor"},
          {&sections.defines, route->compile_define_abi_sha256,
           GraphErrorCode::unavailable_pass,
           "compile define ABI differs from the generated route anchor"},
      }};
  for (const auto& [bytes, expected, code, detail] : anchored) {
    if (detail::sha256(*bytes) != expected) {
      throw binding_error(step, admission, code, std::string(detail));
    }
  }
  // The plan also carries the registry's own digest of the same document. It
  // is a projection cross-check, not an authority: a disagreement means the
  // registry projection and the value-owned admission have diverged.
  if (detail::sha256(sections.samplers + sections.uniforms + sections.outputs +
                     sections.extent + sections.defines) !=
      admission.binding_abi_sha256) {
    throw binding_error(step, admission, GraphErrorCode::invalid_snapshot,
                        "admission binding ABI digest differs from its own ordered ABI");
  }
  // Compile defines belong to a custom adapter alone and never merge into the
  // uniform ABI.
  if (admission.route_kind != "custom_adapter" && !admission.compile_defines.empty()) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "compile defines are only valid for a custom adapter route");
  }
  for (const auto& define : admission.compile_defines) {
    if (define.name.empty() || define.cpp_type.empty() ||
        define.source != "custom_adapter") {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "compile define ABI is invalid");
    }
    for (const auto& uniform : admission.uniforms) {
      if (uniform.name == define.name) {
        throw binding_error(step, admission, GraphErrorCode::binding_type,
                            "compile define collides with a uniform ABI name");
      }
    }
  }
  return route;
}

void authenticate_compile_define_parameters(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition,
    const FactoryRouteDescriptor& route) {
  // A custom adapter binds its defines as real uniforms, and a `runtime-int`
  // program carries them as pass_derived typed_compile_define uniforms. Only a
  // `default-only` typed emitter has them compiled in, and that program was
  // built around one exact value per define.
  if (route.route_kind == "custom_adapter" || route.define_contract != "default-only") {
    return;
  }
  for (const auto& declared : definition.parameters) {
    if (declared.type == "surface" || !declared.define.has_value()) continue;
    const std::string_view define_name = *declared.define;
    // A define that the ABI carries as a uniform is materialized normally.
    bool carried = false;
    for (const auto& uniform : admission.uniforms) {
      if (uniform.name == define_name) { carried = true; break; }
    }
    if (carried) continue;
    const auto* requested = parameter(step, declared.name);
    if (requested == nullptr) {
      // A compiled plan always materializes the declared default, so this is
      // unreachable from the DSL. A hand-built plan must not be able to skip
      // the check by omitting the parameter.
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "parameter " + declared.name +
                              " backs compile define " + std::string(define_name) +
                              " but the step carries no value for it");
    }
    const double value = plan_number(requested);
    const auto baked = baked_define_value(route.defines, define_name);
    if (!baked.has_value()) {
      throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                          "parameter " + declared.name + " maps to compile define " +
                              std::string(define_name) +
                              " which the generated route does not bake");
    }
    if (!(std::isfinite(value)) || value != *baked) {
      throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                          "parameter " + declared.name + " requests compile define " +
                              std::string(define_name) + "=" + number_text(value) +
                              " but the generated route bakes " +
                              std::string(define_name) + "=" + number_text(*baked));
    }
  }
}

noisemaker::BoundKernel bind_factory_route(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition, const glsl::Bindings& bindings,
    std::span<const FactoryRouteDescriptor> routes) {
  const auto* route = authenticate_factory_route(step, admission, routes);
  authenticate_compile_define_parameters(step, admission, definition, *route);
  authenticate_palette_override(step, admission, definition);
  authenticate_measured_parity(step, admission);
  return route->bind(bindings);
}

namespace {

[[nodiscard]] const CompatibilityBinding* uniform_abi(
    const PassAdmission& admission, std::string_view name) {
  for (const auto& uniform : admission.uniforms) {
    if (uniform.name == name) return &uniform;
  }
  return nullptr;
}

[[nodiscard]] float derived_number(const PlanValue* value, double fallback,
                                   const EffectStep& step,
                                   const PassAdmission& admission,
                                   std::string_view label) {
  if (value == nullptr) return noisemaker::f32(fallback);
  if (!is_finite_plan_number(*value)) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        std::string(label) + " is not a finite number");
  }
  return noisemaker::f32(value->number);
}

[[nodiscard]] glsl::Vec4 derived_vector(const PlanValue* value,
                                        const EffectStep& step,
                                        const PassAdmission& admission,
                                        std::string_view label) {
  if (value == nullptr) return glsl::Vec4(0.0F, 0.0F, 0.0F, 0.0F);
  if (value->kind != PlanValue::Kind::array || value->array.size() != 4U) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        std::string(label) + " is not a four-lane vector");
  }
  std::array<float, 4> lanes{};
  for (std::size_t lane = 0; lane < 4U; ++lane) {
    lanes[lane] = derived_number(&value->array[lane], 0.0, step, admission, label);
  }
  return glsl::Vec4(lanes[0], lanes[1], lanes[2], lanes[3]);
}

// The CPU authority's remapUniformData(): a fixed 267-row std140 block built
// from the effect's own bound uniforms, with the render extent in the last
// row. Absent optional uniforms use the authority's exact fallbacks.
[[nodiscard]] glsl::RemapUniformData remap_uniform_block(
    const effects::EffectDefinition& definition, const EffectStep& step,
    const PassAdmission& admission, std::size_t render_width,
    std::size_t render_height) {
  // Every lane is read through the authority's uniform map, so a bound zone
  // surface publishes its color-mode flag into `zone{N}_active` exactly as
  // buildBindings() does before remapUniformData() reads it.
  const auto number_lane = [&](const std::string& name, double fallback) {
    PlanValue owned;
    return derived_number(bound_uniform_value(definition, step, name, owned),
                          fallback, step, admission, name);
  };
  const auto vector_lane = [&](const std::string& name) {
    PlanValue owned;
    return derived_vector(bound_uniform_value(definition, step, name, owned),
                          step, admission, name);
  };
  glsl::RemapUniformData block;
  glsl::Vec4 background_lanes(0.0F, 0.0F, 0.0F, 0.0F);
  {
    PlanValue owned;
    const auto* background = bound_uniform_value(definition, step, "bgColor", owned);
    if (background != nullptr) {
      if (background->kind != PlanValue::Kind::array ||
          background->array.size() != 3U) {
        throw binding_error(step, admission, GraphErrorCode::binding_type,
                            "bgColor is not a three-lane color");
      }
      for (std::size_t lane = 0; lane < 3U; ++lane) {
        background_lanes[lane] =
            derived_number(&background->array[lane], 0.0, step, admission, "bgColor");
      }
    }
  }
  background_lanes[3] = number_lane("bgAlpha", 1.0);
  block.data[0] = background_lanes;
  block.data[1] = glsl::Vec4(number_lane("zoneCount", 0.0),
                             number_lane("smoothEdge", 0.04), 0.0F,
                             number_lane("time", 0.0));
  for (std::size_t zone = 0; zone < 8U; ++zone) {
    const std::string prefix = "zone" + std::to_string(zone) + "_";
    block.data[2U + zone] = glsl::Vec4(number_lane(prefix + "count", 0.0),
                                       number_lane(prefix + "active", 0.0), 0.0F,
                                       number_lane(prefix + "alpha", 1.0));
    for (std::size_t pair = 0; pair < 32U; ++pair) {
      block.data[10U + zone * 32U + pair] =
          vector_lane(prefix + "v" + std::to_string(pair));
    }
  }
  block.data[266] = glsl::Vec4(static_cast<float>(render_width),
                               static_cast<float>(render_height), 0.0F, 0.0F);
  return block;
}

}  // namespace

bool resolve_authenticated_pass_derived(
    void* context, std::string_view source_name, std::string_view binding_name,
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass,
    const BindingMaterializationContext& binding_context,
    glsl::UniformValue& value) {
  (void)context;
  (void)pass;
  // Every branch below is one authenticated `source_name` from the
  // compatibility document's pass_derived census. An unlisted source falls
  // through and is rejected before the factory is ever selected.
  if (source_name == "fullResolution_aspect_ratio") {
    if (binding_context.destination_width == 0U ||
        binding_context.destination_height == 0U) {
      return false;
    }
    // createCanonicalBindings(): `aspect: f32(width / height)` over the pass
    // destination extent. All twenty live pass-derived rows declare `screen`
    // extents, so this is also the full-resolution ratio the source name
    // describes.
    value = noisemaker::f32(
        static_cast<double>(binding_context.destination_width) /
        static_cast<double>(binding_context.destination_height));
    return true;
  }
  // Canonical binding-layer defaults: `speed`, `centerLoX`, and `centerLoY`
  // are zero, and the unbound `size`/`motion` vectors are zero-initialized
  // exactly as WebGL leaves them.
  if (source_name == "canonical_speed_default" ||
      source_name == "canonical_center_low_x_default" ||
      source_name == "canonical_center_low_y_default") {
    value = noisemaker::f32(0.0);
    return true;
  }
  if (source_name == "canonical_size_default" ||
      source_name == "canonical_motion_default") {
    value = glsl::Vec4(0.0F, 0.0F, 0.0F, 0.0F);
    return true;
  }
  // `splatSource` is declared by the pinned program and read by neither the
  // authority kernel nor the typed kernel; it keeps the zero-initialized
  // canonical default.
  if (source_name == "canonical_splat_source_default") {
    value = static_cast<std::int32_t>(0);
    return true;
  }
  if (binding_context.definition == nullptr) return false;
  if (source_name == "typed_compile_define") {
    const auto* abi = uniform_abi(admission, binding_name);
    PlanValue owned;
    const auto* bound =
        bound_uniform_value(*binding_context.definition, step, binding_name, owned);
    if (abi == nullptr || bound == nullptr) return false;
    value = materialize_plan_value(*bound, abi->cpp_type, step, admission,
                                   binding_name);
    return true;
  }
  if (source_name == "remap_uniform_data") {
    if (binding_context.inputs == nullptr) return false;
    value = remap_uniform_block(*binding_context.definition, step, admission,
                                binding_context.inputs->width,
                                binding_context.inputs->height);
    return true;
  }
  return false;
}

// A custom adapter's binding contract includes compile defines that the
// GLSL-derived uniform ABI does not carry. They resolve only through the
// owning parameter's `define` name, and an absent one fails closed.
void materialize_compile_defines(glsl::Bindings& bindings, const EffectStep& step,
                                 const PassAdmission& admission,
                                 const BindingMaterializationContext& context) {
  if (admission.compile_defines.empty()) return;
  if (admission.route_kind != "custom_adapter" || context.definition == nullptr) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "compile defines are only valid for a custom adapter route");
  }
  for (const auto& define : admission.compile_defines) {
    PlanValue owned;
    const auto* value =
        bound_uniform_value(*context.definition, step, define.name, owned);
    if (value == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "compile define has no owning parameter");
    }
    try {
      bindings.set_uniform(define.name,
                           materialize_plan_value(*value, define.cpp_type, step,
                                                  admission, define.name));
    } catch (const GraphError&) {
      throw;
    } catch (const glsl::KernelBindingError& error) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          error.what());
    }
  }
}

void preflight_pass_abi(const EffectStep& step, const PassAdmission& admission,
                        const effects::PassDefinition& pass,
                        const BindingMaterializationContext& context) {
  validate_pass_controls(step, admission, pass);
  if (context.destination_width == 0U || context.destination_height == 0U) {
    throw binding_error(step, admission, GraphErrorCode::invalid_dimension,
                        "output dimensions must be positive");
  }
  // Every ordered sampler is checked against its declared route, with the
  // authority pass as the route authority. Cardinality is whatever the
  // admission census declares (zero through nine), never one.
  if (pass.inputs.size() != admission.samplers.size()) {
    throw binding_error(step, admission, GraphErrorCode::missing_binding,
                        "sampler ABI route is invalid");
  }
  std::unordered_set<std::string> sampler_names;
  for (std::size_t index = 0; index < pass.inputs.size(); ++index) {
    const auto& input = pass.inputs[index];
    const auto& sampler = admission.samplers[index];
    if (sampler.type != "sampler2D" || sampler.cpp_type != "const Surface&") {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "sampler ABI type is invalid");
    }
    if (sampler.name.empty() || !sampler_names.insert(sampler.name).second ||
        sampler.name != input.first || sampler.resource != input.second ||
        sampler.resource.empty() || sampler.source != "resource" ||
        !sampler.source_name.empty()) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "sampler ABI route is invalid");
    }
    if (context.lookup_surface != nullptr &&
        context.lookup_surface(context.lookup_context, sampler.resource) == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_resource,
                          "declared sampler resource is unavailable");
    }
  }
  validate_pass_output_abi(step, pass, admission, admission.identity.index);
  std::unordered_set<std::string> uniform_names;
  for (const auto& uniform : admission.uniforms) {
    if (!uniform_names.insert(uniform.name).second) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "duplicate uniform ABI binding name");
    }
    (void)resolve_uniform(uniform, step, admission, pass, context);
  }
  glsl::Bindings defines;
  materialize_compile_defines(defines, step, admission, context);
}

glsl::Bindings materialize_uniform_bindings(
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass,
    const BindingMaterializationContext& context) {
  glsl::Bindings bindings;
  for (const auto& uniform : admission.uniforms) {
    try {
      bindings.set_uniform(uniform.name,
                           resolve_uniform(uniform, step, admission, pass, context));
    } catch (const GraphError&) {
      throw;
    } catch (const glsl::KernelBindingError& error) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          error.what());
    }
  }
  materialize_compile_defines(bindings, step, admission, context);
  return bindings;
}

void materialize_sampler_bindings(
    glsl::Bindings& bindings, const PassAdmission& admission,
    const BindingMaterializationContext& context, const EffectStep& step,
    const effects::PassDefinition& pass) {
  (void)pass;
  if (context.lookup_surface == nullptr) {
    if (!admission.samplers.empty()) {
      throw binding_error(step, admission, GraphErrorCode::missing_resource,
                          "sampler lookup is missing");
    }
    return;
  }
  for (const auto& sampler : admission.samplers) {
    const auto* surface = context.lookup_surface(context.lookup_context,
                                                  sampler.resource);
    if (surface == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_resource,
                          "declared sampler resource is unavailable");
    }
    try {
      bindings.set_texture(sampler.name, *surface);
    } catch (const glsl::KernelBindingError& error) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          error.what());
    }
  }
}

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
                                       const ExecutionInputs& inputs) const {
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
        // The authority binds `inputTex` once per effect, before any pass of
        // that effect publishes an output; a later pass never re-reads its own
        // effect's result through the implicit input route.
        GraphResource* const effect_input = current;
        // Holding that binding as a raw pointer is only sound while the arena
        // keeps the pointee. It does not by default: when a non-final pass
        // publishes over the one arena name the input holds, `insert` finds no
        // remaining alias and retires the pointee, and the first
        // `release_borrowed` after that erases it -- so a later pass resolving
        // `inputTex` read freed memory. `filter/temporalAberration` has exactly
        // that shape (pass `main` writes `outputTex`, pass `shift1` reads
        // `inputTex`), and a single pass with `repeat > 1` over the same routes
        // has it too. The pin makes the effect's own binding a reference the
        // arena honours for the whole effect: the input stays alive *and*
        // unretired, so a later pass can still `retain` it, and the input's
        // pre-effect bytes are what that pass sees -- which is the authority's
        // semantics. A borrow alone would keep the memory but leave the
        // resource retired, turning the later `retain` into a throw.
        const ResourceArena::ScopedPin effect_input_pin(arena, effect_input);
        // initializeCanonicalResources(): create and clear every declared
        // texture that no pass of this effect produces, at its own declared
        // extent and format, before the first pass runs.
        const auto declared_textures = unproduced_declared_textures(snapshot.definition);
        for (const auto& texture : snapshot.definition.textures) {
          if (declared_textures.find(texture.name) == declared_textures.end()) continue;
          // initializeCanonicalResources() skips a texture whose name is
          // already a live resource -- the map is pre-seeded with the input
          // image and every bound surface-parameter texture -- so a declared
          // name that collides with one of those must not be cleared over.
          if (surface_parameter_for_route(snapshot.definition, texture.name) != nullptr ||
              texture.name == "inputTex") {
            continue;
          }
          if (is_worm_overlay_resource(snapshot.definition.id, texture.name)) {
            throw GraphError(GraphErrorCode::unavailable_pass,
                             "declared texture requires the canonical CPU worm-overlay adapter",
                             step.effect.id, 0, {}, texture.name);
          }
          try {
            const auto width = resolve_dimension(texture.width, step, arena, inputs.width, true);
            const auto height = resolve_dimension(texture.height, step, arena, inputs.height, false);
            arena.allocate(texture.name, width, height,
                           resolve_texture_format(texture.format),
                           ResourceLifetime::declared);
          } catch (const GraphError&) {
            throw;
          } catch (const std::exception& error) {
            throw GraphError(GraphErrorCode::invalid_dimension, error.what(),
                             step.effect.id, 0, {}, texture.name);
          }
        }
        // Resolve one declared sampler route. A surface parameter publishes
        // its own texture route, exactly as the authority's buildBindings()
        // does; the implicit input image is the route named `inputTex`. An
        // unbound surface parameter binds the authority's 1x1 empty surface,
        // which the executor owns for the whole step rather than publishing
        // into the arena namespace.
        const noisemaker::Surface empty_surface(1U, 1U);
        struct ResolvedRoute {
          GraphResource* resource = nullptr;
          const noisemaker::Surface* surface = nullptr;
        };
        const auto resolve_route =
            [&](std::string_view route) -> ResolvedRoute {
          const auto owned = [](GraphResource* resource) {
            return resource == nullptr ? ResolvedRoute{}
                                       : ResolvedRoute{resource, &resource->surface()};
          };
          if (const auto* declared = surface_parameter_for_route(snapshot.definition, route);
              declared != nullptr) {
            const auto* value = parameter(step, declared->name);
            if (value == nullptr) return {};
            if (value->kind == PlanValue::Kind::null_value) return {nullptr, &empty_surface};
            if (value->kind != PlanValue::Kind::surface) return {};
            if (value->surface.kind == SurfaceReference::Kind::input) return owned(effect_input);
            if (value->surface.kind == SurfaceReference::Kind::named) {
              return owned(arena.find(value->surface.name));
            }
            return {};
          }
          if (route == "inputTex") return owned(effect_input);
          return owned(arena.find(route));
        };
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
          // Every ordered sampler route is resolved and retained before a
          // destination is allocated, and stays retained for the bound
          // kernel's lifetime.
          ResolvedSamplerRoutes resolved;
          std::vector<GraphResource*> borrowed;
          const auto release_borrowed = [&] {
            for (auto* resource : borrowed) arena.release(*resource);
            borrowed.clear();
          };
          for (const auto& sampler : admission.samplers) {
            const auto route = resolve_route(sampler.resource);
            if (route.surface == nullptr) {
              release_borrowed();
              throw GraphError(GraphErrorCode::read_before_write,
                               "input resource is not produced", step.effect.id,
                               pass_index, pass.name,
                               admission.identity.program_key);
            }
            if (route.resource != nullptr &&
                std::find(borrowed.begin(), borrowed.end(), route.resource) == borrowed.end()) {
              arena.retain(*route.resource);
              borrowed.push_back(route.resource);
            }
            resolved.entries.push_back({sampler.resource, route.surface});
          }
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
            // The destination quantization must be the authenticated output
            // extent's format; a forged texture format would otherwise change
            // the quantization of every published byte.
            if (format != resolve_texture_format(admission.output_extent.format)) {
              throw GraphError(GraphErrorCode::invalid_format,
                               "destination format differs from the authenticated output extent",
                               step.effect.id, pass_index, pass.name,
                               admission.identity.program_key);
            }
            const BindingMaterializationContext binding_context{
                &inputs, &snapshot.definition, width, height,
                &lookup_resolved_sampler_route, &resolved};
            preflight_pass_abi(step, admission, pass, binding_context);
            auto bindings = materialize_uniform_bindings(step, admission, pass,
                                                         binding_context);
            materialize_sampler_bindings(bindings, admission, binding_context,
                                         step, pass);
            auto kernel = bind_factory_route(step, admission, snapshot.definition,
                                             bindings);
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
            release_borrowed();
            if (error.effect_id().empty()) {
              throw GraphError(error.code(), std::string(error.detail()),
                               step.effect.id, pass_index, pass.name,
                               admission.identity.program_key);
            }
            throw;
          } catch (const glsl::KernelBindingError& error) {
            (void)error;
            release_borrowed();
            throw GraphError(GraphErrorCode::binding_type, "factory binding failed", step.effect.id, pass_index, pass.name, admission.identity.program_key);
          } catch (const std::exception& error) {
            (void)error;
            release_borrowed();
            throw GraphError(GraphErrorCode::execution_failure, "pass execution failed", step.effect.id, pass_index, pass.name, admission.identity.program_key);
          }
          release_borrowed();
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
