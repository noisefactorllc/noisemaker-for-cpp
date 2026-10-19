#include "noisemaker/graph/executor.hpp"

#include "noisemaker/effects/cpu/worm_overlay.hpp"
#include "noisemaker/effects/catalog.hpp"
#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/effects/mesh_render.hpp"
#include "noisemaker/effects/mesh_render_contract.hpp"
#include "noisemaker/fdlibm.hpp"
#include "noisemaker/graph/automation.hpp"
#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/graph/chain_bundle.hpp"
#include "noisemaker/graph/generated/classic_noisedeck_palette_table.hpp"
#include "noisemaker/graph/iteration.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/texture_format.hpp"

#include <functional>
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

// Visits a chain and, depth first, the chains of its steps' chain arguments.
template <typename F>
void for_each_chain(const ExecutionChain& chain, F&& visit) {
  visit(chain);
  for (const auto& variant : chain.steps) {
    if (const auto* effect = std::get_if<EffectStep>(&variant)) {
      for (const auto& argument : effect->inline_chains) for_each_chain(argument.chain, visit);
    }
  }
}

[[nodiscard]] const PlanValue* parameter(const EffectStep& step,
                                         std::string_view name) {
  for (const auto& item : step.params) {
    if (item.name == name) return &item.value;
  }
  return nullptr;
}

[[nodiscard]] bool has_automation(const EffectStep& step) {
  return std::any_of(step.params.begin(), step.params.end(), [](const ParameterBinding& binding) {
    return binding.value.kind == PlanValue::Kind::oscillator;
  });
}

// The authority's resolveEffectAutomation: every `osc(...)` parameter becomes
// a concrete number for this render's normalized time, scaled into its
// parameter's spec; a step without automation is returned unchanged.
[[nodiscard]] EffectStep with_resolved_automation(const EffectStep& step,
                                                  const effects::EffectDefinition& definition,
                                                  double normalized_time) {
  EffectStep resolved = step;
  for (auto& binding : resolved.params) {
    if (binding.value.kind != PlanValue::Kind::oscillator) continue;
    const effects::ParameterDefinition* declared = nullptr;
    for (const auto& candidate : definition.parameters) {
      if (candidate.name == binding.name) declared = &candidate;
    }
    binding.value = PlanValue::number_value(
        resolve_automation(binding.value, normalized_time, automation_spec(declared)));
  }
  return resolved;
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
// instead reads the canonical CPU worm-overlay adapter
// (noisemaker::effects::cpu::render_canonical_worm_overlay), ported from
// src/effects/cpu/worm-overlay.js -- see
// docs/port-engineering/worm-overlay-parity/ for the oracle and mutation
// evidence. The authority only takes this branch when
// `renderOptions.oneShot !== 'initial'`; this port's `one_shot` is a single
// bool with no `'initial'`-shortcut representation and already corresponds
// to the authority's default (non-`'initial'`) mode, so the adapter always
// runs here -- there is no remaining zero-fill case to special-case.
[[nodiscard]] bool is_worm_overlay_resource(std::string_view effect_id,
                                            std::string_view texture) noexcept {
  return texture == "overlayTex" && effects::cpu::is_worm_overlay_effect(effect_id);
}

// Mirrors the JS renderer's own scatter call sites (`renderer.js:963-965` and
// its three siblings): a pass whose admission is `scatter`-status is only
// actually dispatchable when the authenticated catalog also carries a
// `ScatterContract` for it AND a real C++ adapter has been registered under
// its exact program key -- an admitted-but-unported scatter program (any of
// the six not yet in the registry) must keep failing exactly like today.
// `noisemaker::scatter::register_builtin_scatter_adapters()` is idempotent
// by design (see its own doc comment), so calling it from every independent
// check below -- rather than requiring one designated startup call -- keeps
// each call site self-sufficient regardless of process/test init order,
// matching the existing "same four checks at both the dry-run and the real
// authentication, no way to get past them by any current code path" defense
// in depth this file already practices for the other blanket refusals.
[[nodiscard]] bool scatter_adapter_available(const PassAdmission& admission) {
  if (admission.status != AvailabilityStatus::scatter || !admission.scatter.has_value()) {
    return false;
  }
  noisemaker::scatter::register_builtin_scatter_adapters();
  return noisemaker::scatter::resolve_scatter_adapter(admission.identity.program_key) != nullptr;
}

[[nodiscard]] bool mesh_adapter_available(const PassAdmission& admission) {
  return admission.status == AvailabilityStatus::compatible &&
         admission.identity.program_key == effects::mesh_contract::route.program_key &&
         admission.route_kind == "whole_pass";
}

[[nodiscard]] bool direct_mesh_resource(const PassAdmission& admission,
                                        std::string_view resource) {
  return mesh_adapter_available(admission) &&
         (resource == "global_mesh0_positions" || resource == "global_mesh0_normals");
}

// The mesh a program samples. With no meshData the authority binds
// emptyMeshData() (renderer.js bindExternalInputs, mesh-render.js): the
// zero-filled 256x256 position and normal textures upstream samples before an
// OBJ upload. Every vertex has w = 0, so no triangle is drawn.
[[nodiscard]] const MeshData& bound_mesh_data(const ExecutionInputs& inputs) {
  static const MeshData empty{256U, 256U, std::vector<float>(256U * 256U * 4U, 0.0F),
                              std::vector<float>(256U * 256U * 4U, 0.0F)};
  return inputs.mesh_data.has_value() ? *inputs.mesh_data : empty;
}

[[nodiscard]] std::unordered_set<std::string> initialized_declared_textures(
    const effects::EffectDefinition& definition) {
  std::unordered_set<std::string> produced;
  std::unordered_set<std::string> consumed;
  for (const auto& pass : definition.passes) {
    for (const auto& output : pass.outputs) produced.insert(output.second);
    for (const auto& input : pass.inputs) consumed.insert(input.second);
  }
  std::unordered_set<std::string> result;
  for (const auto& texture : definition.textures) {
    if (produced.find(texture.name) == produced.end() ||
        (texture.name.starts_with('_') && consumed.contains(texture.name))) {
      result.insert(texture.name);
    }
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
      if (bound != nullptr && bound->kind != PlanValue::Kind::null_value) {
        value = number(*bound, expression.parameter);
      } else {
        // This catalog kind has no paramDefault. The CPU uses `default ?? 64`
        // even when the effect does not declare the named parameter.
        value = 64.0;
        if (expression.raw.kind == effects::ValueKind::object) {
          for (const auto& field : expression.raw.object) {
            if (field.first == "default" && field.second.kind != effects::ValueKind::null_value) {
              value = catalog_number(field.second);
              break;
            }
          }
        }
      }
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
        value = noisemaker::fdlibm::pow(number(*bound, expression.parameter),
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

[[nodiscard]] const effects::Value* object_field(const effects::Value& value,
                                                 std::string_view name) {
  if (value.kind != effects::ValueKind::object) return nullptr;
  for (const auto& entry : value.object) {
    if (entry.first == name) return &entry.second;
  }
  return nullptr;
}

// canonicalDestination selects the viewport before the texture specification.
// Resolve inputOverride in the pass's resource map, which includes volume routes.
template <typename Lookup>
[[nodiscard]] std::size_t destination_dimension(
    const effects::PassDefinition& pass, const effects::TextureDefinition* texture,
    const EffectStep& step, const ResourceArena& arena, std::size_t extent,
    bool width, Lookup lookup) {
  const effects::Value* spec = nullptr;
  if (pass.viewport.has_value()) {
    if (pass.viewport->kind != effects::ValueKind::object)
      throw std::invalid_argument("viewport is not an object");
    spec = object_field(*pass.viewport, width ? "w" : "h");
    if (spec == nullptr || spec->kind == effects::ValueKind::null_value)
      spec = object_field(*pass.viewport, width ? "width" : "height");
  }
  if (spec == nullptr || spec->kind == effects::ValueKind::null_value) {
    return texture == nullptr ? extent : resolve_dimension(
        width ? texture->width : texture->height, step, arena, extent, width);
  }
  if (spec->kind == effects::ValueKind::number) return rounded_dimension(spec->number);
  if (spec->kind == effects::ValueKind::string) {
    if (spec->string == "input" || spec->string == "screen" ||
        spec->string == "auto" || spec->string == "resolution") return extent;
    return rounded_dimension(static_cast<double>(extent) * parse_percentage(spec->string) / 100.0);
  }
  if (spec->kind != effects::ValueKind::object)
    throw std::invalid_argument("unsupported viewport dimension");
  if (const auto* input = object_field(*spec, "inputOverride"); input != nullptr &&
      input->kind == effects::ValueKind::string && !input->string.empty()) {
    if (const auto* surface = lookup(input->string); surface != nullptr)
      return width ? surface->width() : surface->height();
  }
  const auto numeric = [&](std::string_view name, double fallback) {
    const auto* field = object_field(*spec, name);
    return field == nullptr || field->kind == effects::ValueKind::null_value
               ? fallback : catalog_number(*field);
  };
  if (const auto* param = object_field(*spec, "param"); param != nullptr) {
    if (param->kind != effects::ValueKind::string)
      throw std::invalid_argument("viewport parameter name is invalid");
    const auto* bound = parameter(step, param->string);
    const bool has_bound = bound != nullptr && bound->kind != PlanValue::Kind::null_value;
    double value = has_bound ? number(*bound, param->string)
                            : numeric("paramDefault", numeric("default", 64.0));
    const auto* multiply = object_field(*spec, "multiply");
    const auto* power = object_field(*spec, "power");
    if (multiply != nullptr) value *= catalog_number(*multiply);
    if (power != nullptr) value = noisemaker::fdlibm::pow(value, catalog_number(*power));
    if (!has_bound && (multiply != nullptr || power != nullptr) &&
        object_field(*spec, "default") != nullptr) value = numeric("default", 64.0);
    return rounded_dimension(value);
  }
  if (const auto* divide = object_field(*spec, "screenDivide"); divide != nullptr) {
    if (divide->kind != effects::ValueKind::string)
      throw std::invalid_argument("viewport divisor parameter is invalid");
    const auto* bound = parameter(step, divide->string);
    const double divisor = bound == nullptr || bound->kind == PlanValue::Kind::null_value
        ? numeric("default", 1.0) : number(*bound, divide->string);
    return rounded_dimension(std::ceil(static_cast<double>(extent) / std::max(1.0, divisor)));
  }
  if (object_field(*spec, "scale") != nullptr) {
    double value = std::floor(static_cast<double>(extent) * numeric("scale", 1.0));
    if (const auto* clamp = object_field(*spec, "clamp"); clamp != nullptr) {
      if (const auto* minimum = object_field(*clamp, "min"); minimum != nullptr)
        value = std::max(catalog_number(*minimum), value);
      if (const auto* maximum = object_field(*clamp, "max"); maximum != nullptr)
        value = std::min(catalog_number(*maximum), value);
    }
    return rounded_dimension(value);
  }
  throw std::invalid_argument("unsupported viewport dimension");
}

[[nodiscard]] bool same_catalog_value(const effects::Value& left, const effects::Value& right) {
  if (left.kind != right.kind) return false;
  switch (left.kind) {
    case effects::ValueKind::null_value: return true;
    case effects::ValueKind::boolean: return left.boolean == right.boolean;
    case effects::ValueKind::number:
      return std::bit_cast<std::uint64_t>(left.number) == std::bit_cast<std::uint64_t>(right.number);
    case effects::ValueKind::string: return left.string == right.string;
    case effects::ValueKind::array:
      if (left.array.size() != right.array.size()) return false;
      for (std::size_t i = 0; i < left.array.size(); ++i)
        if (!same_catalog_value(left.array[i], right.array[i])) return false;
      return true;
    case effects::ValueKind::object:
      if (left.object.size() != right.object.size()) return false;
      for (std::size_t i = 0; i < left.object.size(); ++i)
        if (left.object[i].first != right.object[i].first ||
            !same_catalog_value(left.object[i].second, right.object[i].second)) return false;
      return true;
  }
  return false;
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

[[nodiscard]] bool authority_defines_match(
    const effects::PassDefinition& pass,
    const AuthorityPassMetadata& authority) {
  if (pass.defines.has_value() != authority.defines.has_value()) return false;
  return !pass.defines.has_value() ||
         same_catalog_value(*pass.defines, *authority.defines);
}

[[nodiscard]] bool authority_viewport_matches(
    const effects::PassDefinition& pass, const AuthorityPassMetadata& authority) {
  return pass.viewport.has_value() == authority.viewport.has_value() &&
         (!pass.viewport.has_value() || same_catalog_value(*pass.viewport, *authority.viewport));
}

[[nodiscard]] bool viewport_matches_catalog(
    const effects::EffectDefinition& definition, const effects::PassDefinition& pass,
    std::size_t pass_index) {
  for (const auto& canonical : effects::effect_catalog().definitions) {
    if (canonical.id != definition.id) continue;
    if (pass_index >= canonical.passes.size()) return !pass.viewport.has_value();
    const auto& anchor = canonical.passes[pass_index];
    if (anchor.viewport.has_value() != pass.viewport.has_value()) return false;
    return !pass.viewport.has_value() ||
        (anchor.name == pass.name && anchor.program == pass.program &&
         same_catalog_value(*anchor.viewport, *pass.viewport));
  }
  return !pass.viewport.has_value();
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
  if (mesh_adapter_available(admission)) {
    if (!pass.count.has_value() || pass.count->kind != effects::ValueKind::string ||
        pass.count->string != "input" || pass.viewport.has_value() ||
        !pass.draw_mode.has_value() || *pass.draw_mode != "triangles" ||
        admission.draw_mode != "triangles" || !pass.blend.has_value() ||
        pass.blend->kind != effects::BlendKind::boolean || pass.blend->enabled) {
      throw GraphError(GraphErrorCode::invalid_snapshot, "mesh whole-pass controls differ from the admitted contract",
                       step.effect.id, pass_index, pass.name, admission.identity.program_key);
    }
    return;
  }
  // Scatter count is authenticated by its adapter contract. Viewport metadata
  // is authenticated for every pass by validate_pass_identity_and_output.
  if (scatter_adapter_available(admission)) {
    return;
  }
  if (pass.count.has_value()) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                       "ordinary count is unsupported",
                     step.effect.id, pass_index, pass.name,
                     admission.identity.program_key);
  }
}

// The single authenticated fragment output symbol for an ordinary
// (single-output) pass.  Every one of the 211 canonical single-output
// compatibility rows declares exactly one `fragColor` / `glsl::Vec4`
// output; the authority pass may name its own key ("color" on 19 rows), so
// the two names are checked against their own authorities.
//
// An MRT (drawBuffers >= 2) pass has no such legacy alias: JS's own
// `canonicalMrtDestinations` (renderer.js:519-533) looks up
// `pass.outputs[outputVariable]` BY the real GLSL output-variable name
// (`factory.outputNames`), so a pass's own declared key must already be
// that literal symbol -- verified against every pinned upstream MRT source
// (fragColor/geoOut, outXYZ/outVel/outRGBA[/outData], outState1/2/3).
constexpr std::string_view kFragmentOutputSymbol = "fragColor";

void validate_pass_output_abi(const EffectStep& step,
                              const effects::PassDefinition& pass,
                              const PassAdmission& admission,
                              std::size_t pass_index) {
  const std::string_view program_key = admission.identity.program_key;
  if (scatter_adapter_available(admission)) {
    // The scatter contract carries its own single-output record (empty for
    // an ordinary admission, since scatter's admission() early-returns
    // before populating admission.outputs -- see registry.cpp). Authenticate
    // against that instead, plus the two facts specific to a scatter pass
    // that the ordinary branch below has no field for: `drawMode` must be
    // exactly the adapter's own registered draw mode, and `count` (JS's
    // `count:"input"` -- the adapter iterates once per source pixel itself)
    // must be present and hold that literal string. Viewport dimensions use
    // the same authenticated destination path as ordinary fragment passes.
    if (pass.outputs.size() != 1U || admission.scatter->outputs.size() != 1U) {
      throw GraphError(GraphErrorCode::unsupported_mrt,
                       "exactly one fragment output is supported",
                       step.effect.id, pass_index, pass.name,
                       std::string(program_key));
    }
    const auto& declared = pass.outputs.front();
    const auto& output = admission.scatter->outputs.front();
    if (output.slot != 0U || output.physical_name != kFragmentOutputSymbol ||
        output.logical_route != declared.second || declared.second.empty() ||
        declared.first.empty() || output.cpp_type != "glsl::Vec4") {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "pass output ABI differs from owned definition",
                       step.effect.id, pass_index, pass.name,
                       std::string(program_key));
    }
    if (!pass.draw_mode.has_value() || *pass.draw_mode != admission.scatter->draw_mode ||
        (*pass.draw_mode != "points" && *pass.draw_mode != "billboards")) {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "scatter pass draw mode differs from the admitted contract",
                       step.effect.id, pass_index, pass.name,
                       std::string(program_key));
    }
    bool count_matches = pass.count.has_value() &&
        pass.count->kind == effects::ValueKind::string &&
        pass.count->string == admission.scatter->count;
    if (admission.scatter->count == "pass" && program_key == "filter3d/flow3d:deposit") {
      for (const auto& definition : effects::effect_catalog().definitions) {
        if (definition.id != step.effect.id || pass_index >= definition.passes.size()) continue;
        const auto& anchor = definition.passes[pass_index];
        count_matches = anchor.name == pass.name && anchor.program == pass.program &&
            anchor.count.has_value() && pass.count.has_value() &&
            same_catalog_value(*anchor.count, *pass.count);
        break;
      }
    }
    if (!count_matches) {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "scatter pass count differs from the admitted contract",
                       step.effect.id, pass_index, pass.name,
                       std::string(program_key));
    }
    return;
  }
  if (pass.outputs.empty() || pass.outputs.size() != admission.outputs.size()) {
    throw GraphError(GraphErrorCode::unsupported_mrt,
                     "pass output count differs from the admitted output ABI",
                     step.effect.id, pass_index, pass.name,
                     std::string(program_key));
  }
  const bool single = pass.outputs.size() == 1U;
  for (std::size_t slot = 0; slot < pass.outputs.size(); ++slot) {
    const auto& declared = pass.outputs[slot];
    const auto& output = admission.outputs[slot];
    const std::string_view expected_symbol =
        single ? kFragmentOutputSymbol : std::string_view(declared.first);
    if (output.slot != slot || output.physical_name != expected_symbol ||
        output.logical_route != declared.second || declared.second.empty() ||
        declared.first.empty() || output.cpp_type != "glsl::Vec4") {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "pass output ABI differs from owned definition",
                       step.effect.id, pass_index, pass.name,
                       std::string(program_key));
    }
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
      !authority_defines_match(pass, admission.authority_pass) ||
      !authority_viewport_matches(pass, admission.authority_pass) ||
      !authority_blend_matches(pass, admission.authority_pass) ||
      !authority_repeat_matches(pass, admission.authority_pass)) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "pass routing differs from admitted ABI",
                     definition.id, pass_index, pass.name,
                     expected_program_key);
  }
  if (!viewport_matches_catalog(definition, pass, pass_index)) {
    throw GraphError(GraphErrorCode::invalid_snapshot,
                     "viewport differs from the generated catalog anchor",
                     definition.id, pass_index, pass.name, expected_program_key);
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
// `paletteData` (55 x 16 authority values) is ported at
// include/noisemaker/graph/generated/classic_noisedeck_palette_table.hpp,
// mechanically derived from the authority by
// docs/port-engineering/palette-override/generate_classic_noisedeck_palette_table.mjs.
// This function is left owning only the shape check the authority itself
// performs unconditionally (a compiled plan always carries a value for a
// declared palette parameter; a hand-built one must not be able to skip that
// by omission) -- the override itself is applied by
// apply_classic_noisedeck_palette_override() below, once real uniform
// bindings exist to overwrite.
void authenticate_palette_override(const EffectStep& step,
                                   const PassAdmission& admission,
                                   const effects::EffectDefinition& definition) {
  if (definition.name_space != "classicNoisedeck") return;
  for (const auto& declared : definition.parameters) {
    if (declared.type != "palette") continue;
    if (parameter(step, declared.name) == nullptr) {
      // Unreachable from a compiled plan (it always materializes the
      // declared default), refused anyway so the guard cannot be sidestepped
      // by omission.
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "parameter " + declared.name +
                              " selects the palette but the step carries no value for it");
    }
  }
}

// Applies the authority's classicNoisedeck palette override to already
// materialized uniform bindings, mirroring renderer.js's buildBindings()
// exactly: entry.slice(0,3)/(4,7)/(8,11)/(12,15) become
// paletteAmp/paletteFreq/paletteOffset/palettePhase, and paletteMode is
// entry[3] with the authority's 0->3 (rgb) remap. An index that is not a
// positive integer, or is out of the table's range, selects no entry --
// exactly like `paletteData[paletteIndex - 1]` being `undefined` in JS -- so
// the plan's own (already-bound) palette uniforms are left untouched.
//
// The double-precision palette-uniform carrier list (see this file's
// kTypes comment in validate_uniform_abi_shape and
// tools/glslcpp/emit_typed_cpp.py's classic palette and generic vector
// uniform carriers):
// These kernels read paletteAmp/paletteFreq/paletteOffset/palettePhase as
// glsl::DVec3. Noise's runtime COLOR_MODE=4 reaches pal(), so its palette
// override must preserve the same raw double values as the CPU renderer.
bool classic_noisedeck_palette_uses_double_carrier(
    const effects::EffectDefinition& definition) {
  static constexpr std::array<std::string_view, 7> kIds = {{
      "classicNoisedeck/cellNoise",
      "classicNoisedeck/colorLab",
      "classicNoisedeck/fractal",
      "classicNoisedeck/noise",
      "classicNoisedeck/shapeMixer",
      "classicNoisedeck/shapes",
      "classicNoisedeck/shapes3d",
  }};
  return std::find(kIds.begin(), kIds.end(), definition.id) != kIds.end();
}

// The table stores full authority double precision. Double carriers narrow
// only at the same arithmetic operations as the CPU implementation.
void apply_classic_noisedeck_palette_override(
    glsl::Bindings& bindings, const EffectStep& step,
    const effects::EffectDefinition& definition) {
  if (definition.name_space != "classicNoisedeck") return;
  const bool double_carrier = classic_noisedeck_palette_uses_double_carrier(definition);
  for (const auto& declared : definition.parameters) {
    if (declared.type != "palette") continue;
    const double index = plan_number(parameter(step, declared.name));
    if (!std::isfinite(index) || std::trunc(index) != index || index <= 0.0) return;
    const auto& table = palette_table::kClassicNoisedeckPaletteTable;
    const auto row = static_cast<std::size_t>(index) - 1U;
    if (row >= table.size()) return;
    const auto& entry = table[row];
    if (double_carrier) {
      bindings.set_uniform("paletteAmp", glsl::DVec3(entry.amp[0], entry.amp[1], entry.amp[2]));
      bindings.set_uniform("paletteFreq", glsl::DVec3(entry.freq[0], entry.freq[1], entry.freq[2]));
      bindings.set_uniform("paletteOffset", glsl::DVec3(entry.offset[0], entry.offset[1], entry.offset[2]));
      bindings.set_uniform("palettePhase", glsl::DVec3(entry.phase[0], entry.phase[1], entry.phase[2]));
    } else {
      bindings.set_uniform("paletteAmp",
                           glsl::Vec3(noisemaker::f32(entry.amp[0]),
                                      noisemaker::f32(entry.amp[1]),
                                      noisemaker::f32(entry.amp[2])));
      bindings.set_uniform("paletteFreq",
                           glsl::Vec3(noisemaker::f32(entry.freq[0]),
                                      noisemaker::f32(entry.freq[1]),
                                      noisemaker::f32(entry.freq[2])));
      bindings.set_uniform("paletteOffset",
                           glsl::Vec3(noisemaker::f32(entry.offset[0]),
                                      noisemaker::f32(entry.offset[1]),
                                      noisemaker::f32(entry.offset[2])));
      bindings.set_uniform("palettePhase",
                           glsl::Vec3(noisemaker::f32(entry.phase[0]),
                                      noisemaker::f32(entry.phase[1]),
                                      noisemaker::f32(entry.phase[2])));
    }
    bindings.set_uniform("paletteMode",
                         static_cast<std::int32_t>(entry.mode == 0 ? 3 : entry.mode));
    return;
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
//
// `synth/testPattern:testPattern` was the twelfth entry here (a grid-boundary
// digit-extraction divergence, not an adapter mismatch) until it was proven
// byte-exact and removed -- see the digit-extraction field comment on
// `emitted_testpattern_digit_extraction_declarations` in emit_typed_cpp.py
// and tests/test_testpattern_emitter_regression.py.
//
// `filter/snow:snow` was the last real entry -- the authority's own
// hand-written CPU adapter (src/effects/adapters/snow.js), unmatched by the
// typed kernel emitted from the *GLSL* it replaces -- until it too was
// proven byte-exact against that adapter and wired to a hand-written C++
// port (src/effects/snow.cpp) instead; see
// docs/port-engineering/snow-parity/ and tests/test_snow_kernel.cpp.
//
// The one remaining entry is not a real program: no corpus source can ever
// produce this `program_key`. It is a permanent, reserved test sentinel so
// `graph_executor_fails_closed_on_a_measured_parity_exclusion` (in
// tests/test_graph_features.cpp) can keep proving this refusal path
// without depending on some other real program still happening to be
// excluded here -- exactly the situation that emptied this array once
// snow and testPattern were both closed. Never remove it; only ever
// remove a *real* exclusion above it.
struct MeasuredParityExclusion {
  std::string_view program_key;
  std::string_view reason;
};

constexpr std::array<MeasuredParityExclusion, 1> kMeasuredParityExclusions = {{
    {"__measured_parity_test_sentinel__/neverReal:neverReal",
     "test-only sentinel: proves the executor fails closed on a measured"
     " parity exclusion without depending on a real divergent program"},
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
  }
  // Reject the CPU's unsupported whole-pass iteration before an unrelated
  // pass (such as loopEnd's unavailable copy) or input route obscures it.
  // Snapshot integrity and cardinality are established above; authenticate
  // the exact mesh route before applying this specific refusal.
  for (const auto& top_chain : plan.chains) for_each_chain(top_chain, [&](const ExecutionChain& chain) {
    for (const auto& group : iteration::compute_iteration_groups(plan, chain)) {
      if (!group.iterated) continue;
      for (const auto index : group.step_indices) {
        const auto* step = std::get_if<EffectStep>(&chain.steps.at(index));
        if (step == nullptr) continue;
        const auto& snapshot = plan.effects.at(step->snapshot_index);
        for (const auto& admission : snapshot.admissions) {
          if (!mesh_adapter_available(admission)) continue;
          (void)authenticate_factory_route(*step, admission);
          throw binding_error(*step, admission, GraphErrorCode::unsupported_draw_mode,
                              "CPU authority does not support mesh whole-pass rendering inside iterated groups");
        }
      }
    }
  });
  for (const auto& snapshot : plan.effects) {
    for (std::size_t pass_index = 0; pass_index < snapshot.admissions.size();
         ++pass_index) {
      const auto& admission = snapshot.admissions[pass_index];
      if (admission.status == AvailabilityStatus::scatter) {
        if (!scatter_adapter_available(admission)) {
          throw GraphError(GraphErrorCode::unsupported_scatter,
                           "no scatter adapter is registered for this program",
                           snapshot.definition.id, pass_index,
                           admission.identity.name,
                           admission.identity.program_key);
        }
      } else if (admission.status != AvailabilityStatus::compatible) {
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
  const bool needs_midi = std::any_of(plan.effects.begin(), plan.effects.end(),
      [](const auto& snapshot) { return snapshot.definition.id == "synth/roll"; });
  if (needs_midi && !names.insert("midiNoteGrid").second) {
    throw GraphError(GraphErrorCode::duplicate_output, "duplicate MIDI note grid route");
  }
  const bool needs_mesh = std::any_of(plan.effects.begin(), plan.effects.end(),
      [](const auto& snapshot) {
        return snapshot.definition.id == "render/meshLoader" ||
               snapshot.definition.id == "render/meshRender";
      });
  if (needs_mesh) {
    const auto& mesh = bound_mesh_data(inputs);
    if (mesh.tex_width == 0U || mesh.tex_height == 0U ||
        mesh.tex_height > noisemaker::kMaxSurfacePixels / mesh.tex_width) {
      throw GraphError(GraphErrorCode::invalid_dimension, "mesh texture dimensions are invalid");
    }
    for (const auto name : {"global_mesh0_positions", "global_mesh0_normals"}) {
      if (!names.insert(name).second) {
        throw GraphError(GraphErrorCode::duplicate_output, "duplicate mesh data route");
      }
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
  if (needs_midi) available_routes.insert("midiNoteGrid");
  if (needs_mesh) {
    available_routes.insert("global_mesh0_positions");
    available_routes.insert("global_mesh0_normals");
  }
  // renderer.js runChainSync: a step's chain arguments run before its group
  // and publish their images under the hidden surfaces the step binds.
  std::function<bool(const ExecutionChain&)> preflight_chain;
  preflight_chain = [&](const ExecutionChain& chain) -> bool {
    bool have_current = false;
    bool have_volume = false;
    bool have_geometry = false;
    std::unordered_set<std::string> produced;
    // The dry run mirrors execution's own partition: a step inside an
    // iterated group (renderer.js runIteratedGroup) resolves its routes
    // against its step-local resources and the group-shared map, exactly as
    // lookup_group_step_route does, not against the chain-wide producers.
    std::vector<const iteration::IterationGroup*> group_of(chain.steps.size(), nullptr);
    const auto groups = iteration::compute_iteration_groups(plan, chain);
    for (const auto& group : groups) {
      for (const std::size_t index : group.step_indices) {
        if (index < group_of.size()) group_of[index] = &group;
      }
    }
    for (std::size_t step_index = 0; step_index < chain.steps.size(); ++step_index) {
      const auto& variant = chain.steps[step_index];
      if (const auto* read = std::get_if<ReadStep>(&variant)) {
        if (read->surface.kind != SurfaceReference::Kind::named ||
            available_routes.find(read->surface.name) == available_routes.end()) {
          throw GraphError(GraphErrorCode::missing_resource, "named read surface is missing", {}, 0, {}, read->surface.name);
        }
        have_current = true;
        have_volume = false;
        have_geometry = false;
      } else if (const auto* write = std::get_if<WriteStep>(&variant)) {
        if (!have_current || write->surface.kind != SurfaceReference::Kind::named) {
          throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
        }
        available_routes.insert(write->surface.name);
      } else if (const auto* write3d = std::get_if<Write3DStep>(&variant)) {
        // write3d stores the bundle's volume and geometry (`none` stores
        // nothing) and passes the chain through.
        if (write3d->volume != "none" && have_volume) available_routes.insert(write3d->volume);
        if (write3d->geometry != "none" && have_geometry) available_routes.insert(write3d->geometry);
      } else if (const auto* read3d = std::get_if<Read3DStep>(&variant)) {
        if (available_routes.find(read3d->volume) == available_routes.end()) {
          throw GraphError(GraphErrorCode::missing_resource, "Surface " + read3d->volume + " has not been written", {}, 0, {}, read3d->volume);
        }
        have_current = false;
        have_volume = true;
        have_geometry = available_routes.find(read3d->geometry) != available_routes.end();
      } else {
        const auto& raw_effect = std::get<EffectStep>(variant);
        if (raw_effect.snapshot_index >= plan.effects.size()) {
          throw GraphError(GraphErrorCode::invalid_snapshot, "effect snapshot index is out of range");
        }
        for (const auto& argument : raw_effect.inline_chains) {
          if (!preflight_chain(argument.chain)) {
            throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
          }
          available_routes.insert(argument.surface);
        }
        const auto& snapshot = plan.effects[raw_effect.snapshot_index];
        // Preflight the parameters this render binds: automation resolved.
        const EffectStep effect = with_resolved_automation(raw_effect, snapshot.definition, inputs.time);
        const auto* group = group_of[step_index];
        const bool iterated = group != nullptr && group->iterated;
        bool zero_iterations = false;
        if (iterated) {
          const auto* owner = std::get_if<EffectStep>(
              &chain.steps[group->step_indices.front()]);
          if (owner == nullptr) {
            throw GraphError(GraphErrorCode::invalid_snapshot,
                             "iterated group owner is not an effect step");
          }
          zero_iterations = iteration::resolve_iteration_count(
              parameter(*owner, "iterationCount")).zero_iterations;
        }
        // Group execution seeds every declared typed parameter before it
        // tests pass enablement or repeat count. Check all of those seeds,
        // including parameters that no pass reads, before any allocation.
        if (iterated && !zero_iterations) {
          for (const auto& declared : snapshot.definition.parameters) {
            if (declared.type != "volume" && declared.type != "geometry") continue;
            const bool incoming = declared.type == "volume" ? have_volume : have_geometry;
            const auto& output_name = declared.type == "volume"
                ? snapshot.definition.output_tex3d : snapshot.definition.output_geo;
            if (!incoming && (!output_name.has_value() ||
                texture_for(snapshot.definition, *output_name) == nullptr)) {
              throw GraphError(GraphErrorCode::read_before_write,
                               "typed input has no seeded resource", effect.effect.id);
            }
          }
        }
        // Declared textures with no producer, and consumed underscore-prefixed
        // feedback textures even when also produced (including `_rollFb`),
        // are initialized before execution. This includes `overlayTex` on the
        // three worm-overlay effects. They are available routes from the
        // start of the step -- see the
        // `declared_textures` exemption in the pass.inputs loop below. In an
        // iterated group EVERY declared texture is zero-filled scratch before
        // the first iteration (ensure_group_scratch_resources /
        // renderer.js ensureGroupScratchResources), produced or not.
        auto declared_textures = initialized_declared_textures(snapshot.definition);
        if (iterated) {
          for (const auto& texture : snapshot.definition.textures) declared_textures.insert(texture.name);
        }
        // A group step publishes into its own step-local map.
        std::unordered_set<std::string> step_produced;
        for (std::size_t pass_index = 0; pass_index < snapshot.definition.passes.size(); ++pass_index) {
          const auto& pass = snapshot.definition.passes[pass_index];
          const auto& admission = snapshot.admissions[pass_index];
          if (iterated && mesh_adapter_available(admission)) {
            throw GraphError(GraphErrorCode::unsupported_draw_mode,
                             "CPU authority does not support mesh whole-pass rendering inside iterated groups",
                             effect.effect.id, pass_index, pass.name, admission.identity.program_key);
          }
          validate_pass_identity_and_output(effect, snapshot.definition, pass,
                                            admission, pass_index);
          validate_ordinary_pass_metadata(effect, admission, pass, pass_index);
          // The per-binding checks run first so a malformed ABI reports its
          // own precise failure; the route digest below then catches whatever
          // only an ordering or identity comparison can see.
          const BindingMaterializationContext preflight_context{
              &inputs, &snapshot.definition, inputs.width, inputs.height};
          preflight_pass_abi(effect, admission, pass, preflight_context);
          // A scatter pass has no canonical/emitted factory to authenticate
          // (admission.canonical_factory etc. are empty for it -- see
          // registry.cpp's `admission()` early return); its dispatch route
          // is authenticated by `preflight_scatter_pass_abi` above and, at
          // real execution, by resolving its adapter directly.
          if (!scatter_adapter_available(admission)) {
            if (admission.outputs.size() > 1U) {
              // An MRT pass authenticates against the MRT route table; inside
              // an iterated group it runs through run_group_step_iteration's
              // ported MRT branch (renderer.js's MRT branch inside
              // runGroupStepIteration), so no refusal here.
              (void)authenticate_factory_route_mrt(effect, admission);
            } else {
              const auto* route = authenticate_factory_route(effect, admission);
              authenticate_compile_define_parameters(effect, admission,
                                                     snapshot.definition, *route);
            }
          }
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
          if (!enabled || repeats == 0U || zero_iterations) continue;
          for (const auto& input : pass.inputs) {
            const auto require_named = [&](const std::string& route) {
              if (iterated) {
                // lookup_group_step_route: selfTex/feedback always resolve;
                // particle-state names are created lazily in the group map;
                // global_accum is seeded for a loop region; everything else
                // is step-local (declared scratch or this step's own output).
                if (route == "selfTex" || route == "feedback" ||
                    (route == "midiNoteGrid" && needs_midi) ||
                    iteration::is_particle_state_name(route) ||
                    (route == "global_accum" && group->loop) ||
                    step_produced.find(route) != step_produced.end()) {
                  return;
                }
                throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              }
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
              else if (bound->surface.kind == SurfaceReference::Kind::named) {
                // A named surface parameter is copied from the chain-wide
                // arena by seed_group_step_bindings, then published under
                // its step-local texture route. It is not group scratch.
                if (iterated) {
                  if (available_routes.find(bound->surface.name) == available_routes.end()) {
                    throw GraphError(GraphErrorCode::read_before_write,
                                     "input resource is not produced", effect.effect.id,
                                     pass_index, pass.name, admission.identity.program_key);
                  }
                } else {
                  require_named(bound->surface.name);
                }
              }
              else throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced", effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              continue;
            }
            // Current typed volume/geometry parameters are iterated. The
            // authority seeds their pass routes from the incoming bundle or
            // a cleared surface sized by outputTex3d/outputGeo; the parameter
            // value itself is not a named arena dependency.
            const auto typed_parameter = std::find_if(
                snapshot.definition.parameters.begin(),
                snapshot.definition.parameters.end(),
                [&](const effects::ParameterDefinition& declared) {
                  return (declared.type == "volume" || declared.type == "geometry") &&
                         declared.name == input.second;
                });
            if (typed_parameter != snapshot.definition.parameters.end()) {
              if (!iterated) {
                throw GraphError(GraphErrorCode::read_before_write,
                                 "typed input has no seeded resource", effect.effect.id,
                                 pass_index, pass.name, admission.identity.program_key);
              }
              continue;
            }
            if (input.second == "inputTex") require_current();
            else if (input.second == "inputTex3d" || input.second == "inputGeo") {
              const bool available = input.second == "inputTex3d" ? have_volume : have_geometry;
              if (!available) {
                throw GraphError(GraphErrorCode::read_before_write,
                                 "input bundle resource is not produced", effect.effect.id,
                                 pass_index, pass.name, admission.identity.program_key);
              }
            } else if (declared_textures.find(input.second) == declared_textures.end()) {
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
          if (pass.viewport.has_value()) {
            try {
              const auto lookup = [&](std::string_view name) -> const noisemaker::Surface* {
                for (const auto& input : inputs.seed_surfaces)
                  if (input.name == name) return &input.surface;
                for (const auto& input : inputs.external_textures)
                  if (input.name == name) return &input.surface;
                return nullptr;
              };
              for (const auto& output : pass.outputs) {
                const auto* texture = texture_for(snapshot.definition, output.second);
                const auto width = destination_dimension(pass, texture, effect, ResourceArena{},
                                                          inputs.width, true, lookup);
                const auto height = destination_dimension(pass, texture, effect, ResourceArena{},
                                                           inputs.height, false, lookup);
                if (height > noisemaker::kMaxSurfacePixels / width)
                  throw GraphError(GraphErrorCode::allocation_limit,
                                   "viewport dimensions exceed allocation limit",
                                   effect.effect.id, pass_index, pass.name, admission.identity.program_key);
              }
            } catch (const GraphError&) {
              throw;
            } catch (const std::invalid_argument& error) {
              throw GraphError(GraphErrorCode::invalid_dimension, error.what(),
                               effect.effect.id, pass_index, pass.name, admission.identity.program_key);
            }
          }
          for (const auto& output : pass.outputs) {
            produced.insert(output.second);
            step_produced.insert(output.second);
            if (output.second == "outputTex") have_current = true;
          }
        }
        if (zero_iterations) {
          // No pass reads or publishes a resource in a zero-iteration group.
          // Its owner clones the input bundle, or creates a cleared output
          // when the group starts without input (renderer.js:721-756).
          if (step_index == group->step_indices.front() &&
              !have_current && !have_volume && !have_geometry) {
            if (snapshot.definition.domain == "volume-generator") {
              have_volume = true;
              have_geometry = snapshot.definition.output_geo.has_value() &&
                  !bundle::is_passthrough_output_name(*snapshot.definition.output_geo);
            } else {
              have_current = true;
            }
          }
          continue;
        }
        {
          // Execution binds the incoming bundle once per effect and publishes
          // its declared volume and geometry routes after all passes finish.
          const auto bundle_available = [&](const std::optional<std::string>& name,
                                            bool input_available) {
            if (!name.has_value() || bundle::is_passthrough_output_name(*name))
              return input_available;
            return produced.contains(*name) || available_routes.contains(*name) ||
                   declared_textures.contains(*name);
          };
          have_volume = bundle_available(snapshot.definition.output_tex3d, have_volume);
          have_geometry = bundle_available(snapshot.definition.output_geo, have_geometry);
        }
      }
    }
    return have_current;
  };
  for (const auto& chain : plan.chains) static_cast<void>(preflight_chain(chain));

  for (const auto& top_chain : plan.chains) for_each_chain(top_chain, [&](const ExecutionChain& chain) {
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
        const bool dispatchable_scatter = admission.status == AvailabilityStatus::scatter &&
                                          scatter_adapter_available(admission);
        if (admission.status != AvailabilityStatus::compatible && !dispatchable_scatter) {
          if (admission.status == AvailabilityStatus::scatter) {
            throw GraphError(GraphErrorCode::unsupported_scatter, "no scatter adapter is registered for this program",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
          throw GraphError(GraphErrorCode::unavailable_pass, "pass is not executable",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        // A dispatchable scatter pass's own blend/draw-mode semantics are
        // the adapter's `destination_mutation`/`draw_mode` contract, not
        // this ordinary fragment-gather refusal pair -- both are
        // authenticated instead by `validate_pass_output_abi`'s scatter
        // branch, called below via `validate_pass_identity_and_output`.
        if (!dispatchable_scatter) {
          if (admission.authority_pass.blend || (pass.blend.has_value() && pass.blend->enabled)) {
            throw GraphError(GraphErrorCode::unsupported_blend, "blend is not enabled in Task 6",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
          if (!mesh_adapter_available(admission) && (admission.draw_mode != "fragment" ||
              (pass.draw_mode.has_value() && *pass.draw_mode != "fragment"))) {
            throw GraphError(GraphErrorCode::unsupported_draw_mode, "draw mode is not fragment",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
        }
        // `drawBuffers` (JS: `renderer.js:126`, "MRT (drawBuffers >= 2)") is
        // the authority's own declared render-target count for this pass;
        // an ordinary single-output pass never declares it at all (implicit
        // 1). The only real invariant is that it agrees with how many
        // outputs the pass itself declares -- a MISMATCH is what
        // `unsupported_mrt` means now, not "more than one output": N>1 with
        // a correctly-matching count runs through run_mrt_pass below.
        if (pass.draw_buffers.has_value() &&
            (pass.draw_buffers->kind != effects::ValueKind::number ||
             !std::isfinite(pass.draw_buffers->number))) {
          throw GraphError(GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported",
                           effect->effect.id, index, admission.identity.name, admission.identity.program_key);
        }
        {
          const double declared_draw_buffers =
              pass.draw_buffers.has_value() ? pass.draw_buffers->number : 1.0;
          if (declared_draw_buffers != static_cast<double>(pass.outputs.size())) {
            throw GraphError(GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported",
                             effect->effect.id, index, admission.identity.name, admission.identity.program_key);
          }
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
        // A scatter pass has no canonical/emitted factory to authenticate
        // (see the identical guard in the pre-allocation loop above).
        // A multi-output (drawBuffers >= 2) admission authenticates against
        // the generated MRT route table (same contract the non-iterated
        // dispatch and run_group_step_iteration's ported MRT branch use);
        // authenticate_factory_route_mrt refuses any non-empty compile-define
        // ABI on those routes, so no compile-define parameter walk is needed.
        if (!dispatchable_scatter) {
          if (admission.outputs.size() > 1U) {
            (void)authenticate_factory_route_mrt(*effect, admission);
          } else {
            authenticate_compile_define_parameters(
                *effect, admission, snapshot.definition,
                *authenticate_factory_route(*effect, admission));
          }
        }
      }
    }
  });
}


[[nodiscard]] bool is_reserved_name(std::string_view name) noexcept {
  return name == "resolution" || name == "fullResolution" ||
         name == "invFullResolution" || name == "aspectInv" ||
         name == "renderScale" || name == "tileOffset" || name == "time" ||
         name == "frame" || name == "seed" || name == "deltaTime" ||
         name == "audioWaveform" || name == "audioSpectrum" || name == "midiClockCount";
}

[[nodiscard]] bool is_finite_plan_number(const PlanValue& value) noexcept {
  return value.kind == PlanValue::Kind::number && std::isfinite(value.number);
}

[[nodiscard]] bool is_integral_plan_number(const PlanValue& value) noexcept {
  return is_finite_plan_number(value) && std::trunc(value.number) == value.number;
}

[[nodiscard]] std::size_t vector_width(std::string_view cpp_type) noexcept {
  if (cpp_type == "glsl::Vec2" || cpp_type == "glsl::IVec2" || cpp_type == "glsl::DVec2") return 2U;
  if (cpp_type == "glsl::Vec3" || cpp_type == "glsl::IVec3" || cpp_type == "glsl::DVec3") return 3U;
  if (cpp_type == "glsl::Vec4" || cpp_type == "glsl::IVec4" || cpp_type == "glsl::DVec4") return 4U;
  return 0U;
}

void validate_uniform_abi_shape(const EffectStep& step,
                                const PassAdmission& admission,
                                const CompatibilityBinding& abi) {
  const bool audio_binding = abi.name == "audioWaveform" || abi.name == "audioSpectrum" ||
                             abi.type == "float[128]" || abi.cpp_type == "glsl::AudioUniform128";
  if (audio_binding) {
    const bool correct_program =
        (admission.identity.program_key == "synth/scope:scope" && abi.name == "audioWaveform") ||
        (admission.identity.program_key == "synth/spectrum:spectrum" && abi.name == "audioSpectrum");
    if (!correct_program || abi.type != "float[128]" || abi.cpp_type != "glsl::AudioUniform128" ||
        abi.source != "reserved_runtime_state" || abi.source_name != abi.name || !abi.resource.empty()) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "audio uniform ABI is not authenticated");
    }
    return;
  }
  // "vec3"->"glsl::DVec3" is the classicNoisedeck palette-uniform
  // double-precision carrier (see apply_classic_noisedeck_palette_override
  // and tools/glslcpp/emit_typed_cpp.py's
  // _CLASSIC_NOISEDECK_DOUBLE_PALETTE_CARRIERS): the authenticated ABI for
  // paletteAmp/paletteFreq/paletteOffset/palettePhase on exactly five
  // programs declares this cpp_type instead of the ordinary "glsl::Vec3",
  // and only because their generated kernel actually reads a
  // `glsl::DVec3`-typed uniform there. "vec2"->"glsl::DVec2" is the same
  // carrier shape for exactly one uniform on one program --
  // `synth/media:mediaInput`'s `imageSize` (tools/glslcpp/emit_typed_cpp.py's
  // `_DOUBLE_PRECISION_VEC2_UNIFORM_CARRIERS`): the authority's
  // createCanonicalBindings() spreads `...uniforms` for an ordinary
  // effect-parameter vec2 with no Math.fround anywhere on the path, so a
  // `glsl::Vec2` (float lanes) ABI narrows it to float32 at bind time, one
  // rounding earlier than the authority ever does -- measurably not
  // byte-exact (rare, boundary-triggered) against it.
  static constexpr std::array<std::pair<std::string_view, std::string_view>, 14>
      kTypes = {{{"float", "float"},
                 // A GLSL-declared scalar `float` uniform whose value the JS
                 // CPU authority never rounds to float32 (an ordinary DSL
                 // effect parameter, not one of the few reserved names
                 // createCanonicalBindings() explicitly f32()'s -- time,
                 // seed, deltaTime, aspect, renderScale, the pass-derived
                 // speed/centerLo defaults) binds as C++ `double`, matching
                 // the typed kernel's own `bindings.get_number(...)` read.
                 // The GLSL-facing `type` stays "float" -- only the storage
                 // representation widens. See
                 // generate_backend_compatibility.py's
                 // _FROUNDED_SCALAR_UNIFORMS.
                 {"float", "double"},
                 {"double", "double"},
                 {"int", "std::int32_t"},
                 {"uint", "std::uint32_t"},
                 {"bool", "bool"},
                 {"vec2", "glsl::Vec2"},
                 {"vec2", "glsl::DVec2"},
                 {"vec3", "glsl::Vec3"},
                 {"vec3", "glsl::DVec3"},
                 {"vec4", "glsl::Vec4"},
                 {"dvec3", "glsl::DVec3"},
                 {"dvec4", "glsl::DVec4"},
                 {"mat3", "glsl::Mat3"}}};
  bool known = false;
  for (const auto& [type, cpp_type] : kTypes) {
    if (abi.type == type && abi.cpp_type == cpp_type) {
      known = true;
      break;
    }
  }
  known = known || (abi.type == "ivec2" && abi.cpp_type == "glsl::IVec2") ||
          (abi.type == "vec4[275]" && abi.cpp_type == "vec4[275]");
  const bool noise3d_number_seed =
      admission.identity.program_key == "synth3d/noise3d:precompute" &&
      admission.source_sha256 ==
          "60ce97d188bf78bc84176c063943f29c25371e4325f13cedbb4eec889c905727" &&
      abi.name == "seed" && abi.type == "int" &&
      abi.cpp_type == "double" && abi.source == "effect_parameter" &&
      abi.source_name == "seed";
  const bool cell3d_number_seed =
      admission.identity.program_key == "synth3d/cell3d:precompute" &&
      admission.source_sha256 ==
          "83ef13ab1e5997c76e64280d11e0bdb0eaedd6f41a504d2b1e79761cd1dd1755" &&
      abi.name == "seed" && abi.type == "int" &&
      abi.cpp_type == "double" && abi.source == "effect_parameter" &&
      abi.source_name == "seed";
  const bool cubemap_double_basis =
      ((admission.identity.program_key == "render/renderCubemap3d:renderCubemap3d" &&
        admission.source_sha256 ==
            "bcebff481c2d945e140870b50ce3e32e12bc3f198f75a53dc6d2450d5777db26") ||
       (admission.identity.program_key == "render/renderCubemapSurface:renderCubemapSurface" &&
        admission.source_sha256 ==
            "ce467e742120b8a2ec9c34898a2fd1e2f56a85cbe5d27774bcbb1b7f204511fc")) &&
      abi.name == "cubeBasis" && abi.type == "mat3" &&
      abi.cpp_type == "glsl::DMat3" && abi.source == "effect_parameter" &&
      abi.source_name == "cubeBasis";
  known = known || noise3d_number_seed || cell3d_number_seed || cubemap_double_basis;
  if ((admission.identity.program_key == "render/renderCubemap3d:renderCubemap3d" ||
       admission.identity.program_key == "render/renderCubemapSurface:renderCubemapSurface") &&
      abi.name == "cubeBasis" && !cubemap_double_basis) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "cubemap basis ABI is not authenticated");
  }
  if (admission.identity.program_key == "synth3d/noise3d:precompute" &&
      abi.name == "seed" && !noise3d_number_seed) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "Noise3D seed ABI is not authenticated");
  }
  if (admission.identity.program_key == "synth3d/cell3d:precompute" &&
      abi.name == "seed" && !cell3d_number_seed) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        "Cell3D seed ABI is not authenticated");
  }
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

// The authority binds a parameter's resolved number into its uniform as is
// (renderer.js buildBindings: `uniforms[param.uniform] = value`), so a float
// parameter on a GLSL `int` uniform reaches the kernel raw, fractional or not.
// These five `rotation` parameters are the only float parameters on an int
// uniform. Each kernel reads `rotation` only as `rotation == -1` and
// `rotation == 1` (canonical-kernels.js for tetraColorArray, tetraCosine and
// palette3d; adapters/palette.js `=== -1` and `=== 1` for palette and
// historicPalette). A value that is not an int32 integer equals neither, so it
// takes the no-rotation branch, as 0 does, and binds as 0.
// tests/test_float_int_uniform_parity.py checks these facts against the
// vendored GLSL and the effect catalog, and renders the cases on both lanes.
constexpr std::array<std::pair<std::string_view, std::string_view>, 5> kRawComparedIntUniforms{{
    {"filter/historicPalette:historicPalette", "rotation"},
    {"filter/palette:palette", "rotation"},
    {"filter/tetraColorArray:tetraColorArray", "rotation"},
    {"filter/tetraCosine:tetraCosine", "rotation"},
    {"filter3d/palette3d:palette3d", "rotation"},
}};

[[nodiscard]] bool raw_compared_int_uniform(std::string_view program_key, std::string_view binding_name) noexcept {
  return std::any_of(kRawComparedIntUniforms.begin(), kRawComparedIntUniforms.end(), [&](const auto& entry) {
    return entry.first == program_key && entry.second == binding_name;
  });
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
      if (is_finite_plan_number(value) &&
          raw_compared_int_uniform(admission.identity.program_key, binding_name)) {
        return static_cast<std::int32_t>(0);
      }
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
    if (value.kind != PlanValue::Kind::array) return fail("vector has the wrong width");
    const std::size_t supplied_width = value.array.size();
    if (supplied_width != width) {
      // The authority's "color" DSL parameter type accepts either 3 or 4
      // numeric components -- RGB or RGBA, e.g. `#rrggbb`/`#rrggbbaa`, or a
      // 3- or 4-element literal array -- even though every uniform a
      // "color" parameter binds to in this catalog is declared vec3 (or,
      // for synth/remap's zone colors, dvec3): the authority's
      // src/effects/definition.js `normalizeValue`'s "color" case accepts
      // `value.length === 3 || value.length === 4`, and the result is fed
      // straight through to `uniforms[name] = value` in
      // src/runtime/renderer.js with no truncation. Every canonical kernel
      // that reads such a uniform destructures it by fixed index (e.g.
      // `var r = rgb[0], g = rgb[1], b = rgb[2]`, canonical-kernels.js's
      // filter/tint `rgb_to_hsv`), so a 4th (alpha) component is simply
      // never read -- confirmed by a static scan of every "color"-typed
      // uniform's kernel body for length-sensitive vector ops
      // (distance/length/dot/mix/clamp/...) and by empirically re-rendering
      // all 64 "color" parameters in the catalog with a 3- vs. 4-component
      // value (byte-identical in every case but one, handled below). A
      // supplied width of `width + 1` is that legitimate "RGBA given for a
      // vec3/dvec3 color uniform" case; anything else is a real mismatch
      // and stays refused.
      if (supplied_width != width + 1U) return fail("vector has the wrong width");
      // classicNoisedeck/composite's `inputColor` is the one exception.
      // canonical-kernels.js's composite kernel (`canonicalFactory6`)
      // passes `$bindings["inputColor"]` directly -- never re-sliced to 3
      // components -- into `distance(inputColor, color1)` /
      // `distance(inputColor, color2)`, while `color1`/`color2` ARE always
      // re-sliced to exactly 3 components in `main()`
      // (`new PooledFloat32Array([color1[0], color1[1], color1[2]])`).
      // glsl-runtime.js's `#binary` (backing `subtract`, which `distance`
      // composes from `length`/`dot`) takes its output length from the
      // LEFT operand whenever it is a vector -- here always `inputColor` --
      // and reads `component(right, index)` for every lane up to that
      // length, which is `undefined` (=> NaN) past the always-3-wide right
      // operand's end whenever inputColor carries a 4th component. `dot()`
      // sums across all lanes, so that single NaN lane poisons the whole
      // `distance()` result; NaN compares false against every threshold, so
      // blendMode 0/1/2 (the only modes that reference inputColor) always
      // take their "no match" branch. Measured directly: rendering
      // composite with a 3- vs. 4-component inputColor of the same RGB
      // produces different bytes. Reproduce the poisoning instead of
      // silently dropping the alpha.
      if (step.effect.id == "classicNoisedeck/composite" && binding_name == "inputColor") {
        // `inputColor` is now an ordinary double-vector-uniform carrier
        // (see generate_backend_compatibility.py's
        // `is_double_vector_uniform`), so the poisoned sentinel this
        // returns must match whichever variant alternative the kernel's
        // ABI actually declares, or a later `bindings.get<T>("inputColor")`
        // would throw on a variant-type mismatch instead of reading NaN.
        if (cpp_type == "glsl::DVec3") {
          const double nan = std::numeric_limits<double>::quiet_NaN();
          return glsl::DVec3(nan, nan, nan);
        }
        const float nan = std::numeric_limits<float>::quiet_NaN();
        return glsl::Vec3(nan, nan, nan);
      }
    }
    // DVec3/DVec4 (remap's zone geometry/color/bounds ABI) keep the plan
    // value's full double precision -- unlike Vec2/Vec3/Vec4, which round to
    // float32 below matching GLSL's mandated per-lane float semantics. The
    // authority's semantic $bindings are plain, unrounded JS doubles; a
    // float32 lane here would silently reintroduce exactly the divergence
    // that ruled out typed generation for this program (see remap.cpp).
    if (cpp_type == "glsl::DVec2" || cpp_type == "glsl::DVec3" || cpp_type == "glsl::DVec4") {
      std::array<double, 4> d{};
      for (std::size_t index = 0; index < width; ++index) {
        if (!is_finite_plan_number(value.array[index])) return fail("vector has an invalid lane");
        d[index] = value.array[index].number;
      }
      if (cpp_type == "glsl::DVec2") return glsl::DVec2(d[0], d[1]);
      if (cpp_type == "glsl::DVec3") return glsl::DVec3(d[0], d[1], d[2]);
      return glsl::DVec4(d[0], d[1], d[2], d[3]);
    }
    std::array<float, 4> f{};
    std::array<std::int32_t, 4> i{};
    std::array<double, 4> d{};
    const bool is_double = cpp_type == "glsl::DVec3";
    for (std::size_t index = 0; index < width; ++index) {
      if (cpp_type.starts_with("glsl::I")) {
        if (!is_integral_plan_number(value.array[index]) ||
            value.array[index].number < static_cast<double>(std::numeric_limits<std::int32_t>::min()) ||
            value.array[index].number > static_cast<double>(std::numeric_limits<std::int32_t>::max())) {
          return fail("integral vector has an invalid lane");
        }
        i[index] = static_cast<std::int32_t>(value.array[index].number);
      } else if (is_double) {
        // The classicNoisedeck palette-uniform double-precision carrier
        // (see validate_uniform_abi_shape's kTypes comment): the authority
        // binds these as raw, un-rounded JS doubles, narrowing only where
        // its own per-op arithmetic narrows -- never here, at bind.
        if (!is_finite_plan_number(value.array[index])) return fail("vector has an invalid lane");
        d[index] = value.array[index].number;
      } else {
        if (!is_finite_plan_number(value.array[index])) return fail("vector has an invalid lane");
        f[index] = noisemaker::f32(value.array[index].number);
      }
    }
    if (cpp_type == "glsl::Vec2") return glsl::Vec2(f[0], f[1]);
    if (cpp_type == "glsl::Vec3") return glsl::Vec3(f[0], f[1], f[2]);
    if (cpp_type == "glsl::DVec3") return glsl::DVec3(d[0], d[1], d[2]);
    if (cpp_type == "glsl::Vec4") return glsl::Vec4(f[0], f[1], f[2], f[3]);
    if (cpp_type == "glsl::IVec2") return glsl::IVec2(i[0], i[1]);
  }
  if (cpp_type == "glsl::Mat3") {
    if (value.kind != PlanValue::Kind::array || value.array.size() != 9U) {
      return fail("mat3 has the wrong cardinality");
    }
    glsl::Mat3 result;
    for (std::size_t col = 0; col < 3U; ++col) {
      for (std::size_t row = 0; row < 3U; ++row) {
        const auto& item = value.array[col * 3U + row];
        if (!is_finite_plan_number(item)) return fail("mat3 has an invalid element");
        result[col][row] = noisemaker::f32(item.number);
      }
    }
    return result;
  }
  if (cpp_type == "glsl::DMat3") {
    if (value.kind != PlanValue::Kind::array || value.array.size() != 9U) {
      return fail("mat3 has the wrong cardinality");
    }
    glsl::DMat3 result;
    for (std::size_t col = 0; col < 3U; ++col) {
      for (std::size_t row = 0; row < 3U; ++row) {
        const auto& item = value.array[col * 3U + row];
        if (!is_finite_plan_number(item)) return fail("mat3 has an invalid element");
        result[col][row] = item.number;
      }
    }
    return result;
  }
  if (cpp_type == "vec4[275]") {
    if (value.kind != PlanValue::Kind::array || value.array.size() != 275U) {
      return fail("remap block has the wrong cardinality");
    }
    glsl::RemapUniformData result;
    for (std::size_t index = 0; index < 275U; ++index) {
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
  if (abi.source_name == "midiClockCount") {
    return materialize_plan_value(PlanValue::number_value(inputs.midi_state ? inputs.midi_state->clock_count : 0.0),
                                  abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "audioWaveform") {
    return inputs.audio_state ? inputs.audio_state->waveform : glsl::AudioUniform128{};
  }
  if (abi.source_name == "audioSpectrum") {
    return inputs.audio_state ? inputs.audio_state->spectrum : glsl::AudioUniform128{};
  }
  if (abi.source_name == "tileOffset") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(0.0), PlanValue::number_value(0.0)}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "fullResolution") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(static_cast<double>(inputs.width)), PlanValue::number_value(static_cast<double>(inputs.height))}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "invFullResolution") {
    if (inputs.width == 0U || inputs.height == 0U) {
      throw binding_error(step, admission, GraphErrorCode::invalid_dimension,
                          "full resolution must be positive");
    }
    const double full_width = static_cast<double>(noisemaker::f32(inputs.width));
    const double full_height = static_cast<double>(noisemaker::f32(inputs.height));
    return materialize_plan_value(PlanValue::array_value({
        PlanValue::number_value(static_cast<double>(noisemaker::f32(1.0 / full_width))),
        PlanValue::number_value(static_cast<double>(noisemaker::f32(1.0 / full_height)))}),
        abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "aspectInv") {
    if (inputs.width == 0U || inputs.height == 0U) {
      throw binding_error(step, admission, GraphErrorCode::invalid_dimension,
                          "full resolution must be positive");
    }
    const double aspect = static_cast<double>(noisemaker::f32(inputs.width)) /
                          static_cast<double>(noisemaker::f32(inputs.height));
    return materialize_plan_value(PlanValue::number_value(
        static_cast<double>(noisemaker::f32(1.0 / aspect))),
        abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "resolution") {
    return materialize_plan_value(PlanValue::array_value({PlanValue::number_value(static_cast<double>(context.destination_width)), PlanValue::number_value(static_cast<double>(context.destination_height))}), abi.cpp_type, step, admission, abi.name);
  }
  if (abi.source_name == "renderScale") return materialize_plan_value(PlanValue::number_value(1.0), abi.cpp_type, step, admission, abi.name);
  // `time`/`deltaTime` are createCanonicalBindings' `f32(time)` /
  // `f32(deltaTime)` (glsl-kernel.js:56-58): every DSL-generated kernel
  // observes these already float32-narrowed, at bind time, not at first use.
  // The non-reserved `PixelContext::time/seed` fields a non-derivative
  // `run_pass` call fills in get this same narrowing for free (both call
  // sites pass `noisemaker::f32(inputs.time/seed)` straight through); a
  // hand-written adapter that instead reads these as ordinary named uniforms
  // via `Bindings` (`bind_snow`, `bind_bit_effects`) was going through this
  // function unnarrowed, one rounding step later than the authority.
  if (abi.source_name == "time") return materialize_plan_value(PlanValue::number_value(static_cast<double>(noisemaker::f32(inputs.time))), abi.cpp_type, step, admission, abi.name);
  if (abi.source_name == "frame") return materialize_plan_value(PlanValue::number_value(static_cast<double>(inputs.frame)), abi.cpp_type, step, admission, abi.name);
  // `seed` is double-edged: createCanonicalBindings' base entry is
  // `f32(seed)`, but when the effect declares its own `seed` parameter the
  // runtime's effectParams() substitution (renderer.js:433-437) puts the RAW
  // `renderOptions.seed` into `params`, and the same function's
  // `...uniforms` spread then overrides that base entry with it
  // un-narrowed. So a `float`-typed seed uniform still observes
  // `f32(inputs.seed)` (materialize_plan_value's float path narrows), but an
  // `int`/`uint`-typed seed uniform must truncate the raw value: narrowing
  // through float32 first would deliver e.g. 1365378816 where the authority
  // delivers 1365378863, and every hash seeded from that uniform diverges
  // (the pointsEmit -> dla chain defect).
  //
  // Integer-typed seed uniforms also use the authority's ToInt32/ToUint32
  // wrap (every kernel consumes the seed through `seed|0` / `>>>0`): a
  // render seed past 2^31 renders in the authority (e.g. 2453927936 becomes
  // -1841039360) where a plain int32 range check would refuse a case the
  // authority renders.
  if (abi.source_name == "seed") {
    const auto* seed_param = parameter(step, "seed");
    const bool substituted = seed_param != nullptr &&
        std::find(step.explicit_params.begin(), step.explicit_params.end(), "seed") ==
            step.explicit_params.end();
    double value = substituted ? inputs.seed : static_cast<double>(noisemaker::f32(inputs.seed));
    if (abi.cpp_type == "std::int32_t" || abi.cpp_type == "std::uint32_t") {
      const double truncated = std::trunc(value);
      double wrapped = std::fmod(truncated, 4294967296.0);
      if (wrapped < 0.0) wrapped += 4294967296.0;
      if (abi.cpp_type == "std::int32_t" && wrapped >= 2147483648.0) wrapped -= 4294967296.0;
      value = wrapped;
    }
    return materialize_plan_value(PlanValue::number_value(value), abi.cpp_type, step, admission,
                                  abi.name);
  }
  if (abi.source_name == "deltaTime") return materialize_plan_value(PlanValue::number_value(static_cast<double>(noisemaker::f32(inputs.delta_time))), abi.cpp_type, step, admission, abi.name);
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
        (abi.cpp_type == "vec4[275]" && std::holds_alternative<glsl::RemapUniformData>(resolved));
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
    // silent fallback. The substitution predicate lives in reserved_uniform,
    // where the raw-vs-f32 value rule is applied.
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
    // A dispatchable scatter pass never carries `admission.dimensionality`/
    // `admission.draw_mode` (empty for a scatter admission -- see
    // registry.cpp's `admission()` early return), so it skips only those
    // two admission-field checks below rather than the ordinary
    // pass-shaped ones (draw_buffers/repeat/conditions), which still apply
    // uniformly. The equivalent authentication for the fields it skips
    // lives in `validate_pass_output_abi`'s scatter branch and
    // `preflight_scatter_pass_abi`. This still re-derives dispatchability
    // itself rather than trusting a caller already checked it, matching
    // this file's existing "no way to get past them by any current code
    // path" defense in depth for the other blanket refusals.
    if (!(admission.status == AvailabilityStatus::scatter && scatter_adapter_available(admission))) {
      throw binding_error(step, admission,
                          admission.status == AvailabilityStatus::scatter ? GraphErrorCode::unsupported_scatter : GraphErrorCode::unavailable_pass,
                          "pass is not compatible");
    }
  } else {
    const std::array<std::string_view, 6> allowed_domains = {
        "image", "volume-generator", "volume-filter", "volume-renderer", "loop-begin", "loop-end"};
    if (std::find(allowed_domains.begin(), allowed_domains.end(), admission.dimensionality) == allowed_domains.end()) {
      throw binding_error(step, admission, GraphErrorCode::unsupported_draw_mode, "unsupported dimensionality");
    }
    if (mesh_adapter_available(admission)) {
      validate_ordinary_pass_metadata(step, admission, pass, admission.identity.index);
    } else if (admission.draw_mode != "fragment" || (pass.draw_mode.has_value() && *pass.draw_mode != "fragment")) throw binding_error(step, admission, GraphErrorCode::unsupported_draw_mode, "only fragment draw mode is supported");
  }
  // See the sibling check in the plan dry-run loop above: `unsupported_mrt`
  // now means "declared drawBuffers disagrees with the pass's own output
  // count", not "more than one output".
  if (pass.draw_buffers.has_value() && (pass.draw_buffers->kind != effects::ValueKind::number || !std::isfinite(pass.draw_buffers->number))) throw binding_error(step, admission, GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported");
  if ((pass.draw_buffers.has_value() ? pass.draw_buffers->number : 1.0) != static_cast<double>(pass.outputs.size())) throw binding_error(step, admission, GraphErrorCode::unsupported_mrt, "multiple draw buffers are unsupported");
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
    // A program bound by several authority passes legitimately appears once
    // per binding: same (key, factory) pair, one ordered output ABI per
    // binding. Only a byte-identical duplicate of the whole descriptor --
    // anchors, identity and bind factory included -- is a generation defect.
    struct FullPayload {
      std::string_view emitted_factory;
      std::string_view route_kind;
      std::string_view source_sha256;
      std::string_view typed_abi_sha256;
      std::string_view define_contract;
      std::string_view defines;
      std::string_view sampler_abi_sha256;
      std::string_view uniform_abi_sha256;
      std::string_view output_abi_sha256;
      std::string_view output_extent_sha256;
      std::string_view compile_define_abi_sha256;
      BoundKernel (*bind)(const glsl::Bindings&);
      bool operator==(const FullPayload&) const = default;
    };
    std::unordered_map<std::string, std::vector<FullPayload>> pairs;
    for (const auto& route : generated_routes) {
      const bool known_kind = route.route_kind == "typed_emitter" ||
                              route.route_kind == "custom_adapter";
      if (route.key.empty() || route.canonical_factory.empty() ||
          route.emitted_factory.empty() || !known_kind ||
          !is_sha256(route.source_sha256) ||
          !is_sha256(route.typed_abi_sha256) || route.bind == nullptr) {
        throw GraphError(GraphErrorCode::invalid_snapshot,
                         "generated canonical route table is malformed", {}, 0,
                         {}, std::string(route.key));
      }
      const FullPayload payload{route.emitted_factory, route.route_kind,
                                route.source_sha256, route.typed_abi_sha256,
                                route.define_contract, route.defines,
                                route.sampler_abi_sha256,
                                route.uniform_abi_sha256,
                                route.output_abi_sha256,
                                route.output_extent_sha256,
                                route.compile_define_abi_sha256, route.bind};
      auto& seen = pairs[std::string(route.key) + "\x1f" +
                         std::string(route.canonical_factory)];
      if (std::find(seen.begin(), seen.end(), payload) != seen.end()) {
        throw GraphError(GraphErrorCode::invalid_snapshot,
                         "generated canonical route table is malformed", {}, 0,
                         {}, std::string(route.key));
      }
      seen.push_back(payload);
      result.push_back({route.key, route.canonical_factory,
                        route.emitted_factory, route.route_kind,
                        route.source_sha256, route.typed_abi_sha256,
                        route.define_contract, route.defines,
                        route.sampler_abi_sha256, route.uniform_abi_sha256,
                        route.output_abi_sha256, route.output_extent_sha256,
                        route.compile_define_abi_sha256, route.bind});
    }
    result.push_back(effects::mesh_contract::route);
    return result;
  }();
  return routes;
}

const FactoryRouteDescriptor* authenticate_factory_route(
    const EffectStep& step, const PassAdmission& admission,
    std::span<const FactoryRouteDescriptor> routes) {
  const auto table = routes.empty() ? canonical_factory_routes() : routes;
  // A program bound by several authority passes has one route row per
  // binding: same (key, factory) pair, one ordered output ABI per binding.
  // The dispatching admission authenticates against the row whose baked
  // anchors match its own sections; a key/factory pair alone is not
  // provenance, and a plan whose sections match no generated row refuses.
  std::vector<const FactoryRouteDescriptor*> candidates;
  for (const auto& route : table) {
    if (route.program_key == admission.identity.program_key &&
        route.canonical_factory == admission.canonical_factory) {
      candidates.push_back(&route);
    }
  }
  if (candidates.empty()) {
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "canonical factory route is not admitted");
  }
  const auto sections = binding_abi_sections(admission);
  std::optional<GraphError> first_error;
  std::optional<const FactoryRouteDescriptor*> matched_route;
  for (const FactoryRouteDescriptor* route : candidates) {
    if (route->bind == nullptr &&
        !(route->route_kind == "whole_pass" && route->program_key == effects::mesh_contract::route.program_key)) {
      if (!first_error) first_error = binding_error(step, admission, GraphErrorCode::unavailable_pass,
                                                    "canonical factory route is not admitted");
      continue;
    }
    // Every remaining descriptor field must equal the value-owned admission
    // before the payload is used.
    if (route->emitted_factory != admission.emitted_factory ||
        route->route_kind != admission.route_kind ||
        route->source_sha256 != admission.source_sha256 ||
        route->typed_abi_sha256 != admission.typed_abi_sha256) {
      if (!first_error) first_error = binding_error(step, admission, GraphErrorCode::unavailable_pass,
                                                    "generated route metadata differs from the admission");
      continue;
    }
    // The identity strings do not themselves cover the ordered ABI. Each
    // section of the admission's own ordered lists is re-digested and compared
    // to the generated anchor, which the typed-slice generator baked from the
    // authenticated compatibility document -- an authority outside the plan.
    // Every section reports its own code and detail.
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
    bool matched = true;
    for (const auto& [bytes, expected, code, detail] : anchored) {
      if (detail::sha256(*bytes) != expected) {
        if (!first_error) first_error = binding_error(step, admission, code, std::string(detail));
        matched = false;
        break;
      }
    }
    if (matched) {
      matched_route = route;
      break;
    }
  }
  if (!matched_route) throw *first_error;
  const auto* route = *matched_route;
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
  if (route->bind == nullptr) {
    throw binding_error(step, admission, GraphErrorCode::unsupported_draw_mode,
                        "whole-pass adapter cannot be bound as a fragment kernel");
  }
  authenticate_compile_define_parameters(step, admission, definition, *route);
  authenticate_palette_override(step, admission, definition);
  authenticate_measured_parity(step, admission);
  return route->bind(bindings);
}

const FactoryRouteDescriptorMrt* find_factory_route_mrt(
    std::span<const FactoryRouteDescriptorMrt> routes,
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

std::span<const FactoryRouteDescriptorMrt> canonical_factory_routes_mrt() {
  // One checked projection of the generated MRT route table, exactly like
  // canonical_factory_routes() projects the single-output one: the typed-slice
  // generator publishes every multi-output corpus program here (and only
  // here), and a malformed row fails closed for every later execution.
  static const std::vector<FactoryRouteDescriptorMrt> routes = [] {
    std::vector<FactoryRouteDescriptorMrt> result;
    const auto generated_routes = generated::canonical_routes_mrt();
    result.reserve(generated_routes.size());
    std::unordered_set<std::string> pairs;
    for (const auto& route : generated_routes) {
      if (route.key.empty() || route.canonical_factory.empty() ||
          route.emitted_factory.empty() || route.route_kind != "typed_emitter" ||
          !is_sha256(route.source_sha256) ||
          !is_sha256(route.typed_abi_sha256) || route.bind == nullptr ||
          !pairs.insert(std::string(route.key) + "\x1f" +
                        std::string(route.canonical_factory)).second) {
        throw GraphError(GraphErrorCode::invalid_snapshot,
                         "generated canonical MRT route table is malformed", {}, 0,
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

const FactoryRouteDescriptorMrt* authenticate_factory_route_mrt(
    const EffectStep& step, const PassAdmission& admission,
    std::span<const FactoryRouteDescriptorMrt> routes) {
  const auto table = routes.empty() ? canonical_factory_routes_mrt() : routes;
  const auto* route = find_factory_route_mrt(table, admission.identity.program_key,
                                             admission.canonical_factory);
  if (route == nullptr || route->bind == nullptr) {
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "canonical MRT factory route is not admitted");
  }
  if (route->emitted_factory != admission.emitted_factory ||
      route->route_kind != admission.route_kind ||
      route->source_sha256 != admission.source_sha256 ||
      route->typed_abi_sha256 != admission.typed_abi_sha256) {
    throw binding_error(step, admission, GraphErrorCode::unavailable_pass,
                        "generated MRT route metadata differs from the admission");
  }
  // Mirrors authenticate_factory_route's ordered-ABI cross-check exactly;
  // binding_abi_sections() is already output-count-generic (it walks the
  // whole admission.outputs vector), so no MRT-specific section grammar was
  // needed here.
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
  if (detail::sha256(sections.samplers + sections.uniforms + sections.outputs +
                     sections.extent + sections.defines) !=
      admission.binding_abi_sha256) {
    throw binding_error(step, admission, GraphErrorCode::invalid_snapshot,
                        "admission binding ABI digest differs from its own ordered ABI");
  }
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

// The MRT sibling of bind_factory_route. No compile-define-backed parameter
// authentication yet (authenticate_compile_define_parameters is typed to
// FactoryRouteDescriptor): unreachable today since no MRT effect declares
// any parameters, and authenticate_factory_route_mrt above already refuses
// a route whose compile-define ABI is malformed or non-empty on a
// non-custom-adapter kind.
noisemaker::BoundKernelMrt bind_factory_route_mrt(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition, const glsl::Bindings& bindings,
    std::span<const FactoryRouteDescriptorMrt> routes) {
  const auto* route = authenticate_factory_route_mrt(step, admission, routes);
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

// The CPU authority's remapUniformData(): a fixed 275-row std140 block built
// from the effect's own bound uniforms, with the render extent in row 266 and
// the eight per-zone bounds rows (added upstream) in rows 267..274. Absent
// optional uniforms use the authority's exact fallbacks. This packed block
// feeds only the retired 267/275-row GLSL typed-generation path; the live
// authority kernel for synth/remap:remap is the hand-written adapter
// (remap.js / bind_remap()), which reads the same effect uniforms directly
// and never touches this array. Kept in parity anyway: nothing here may
// silently drift from remapUniformData() just because it is unused.
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
  const auto bounds_lane = [&](const std::string& name) {
    PlanValue owned;
    const auto* bound = bound_uniform_value(definition, step, name, owned);
    if (bound == nullptr) return glsl::Vec4(0.0F, 0.0F, 1.0F, 1.0F);
    return derived_vector(bound, step, admission, name);
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
    block.data[267U + zone] = bounds_lane(prefix + "bounds");
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
  // `resetState` and `useCustom` are declared by pinned programs (points/dla
  // and synth/cellularAutomata) but unexposed by effect parameters; they default to false.
  if (source_name == "canonical_reset_state_default" ||
      source_name == "canonical_use_custom_default") {
    value = false;
    return true;
  }
  if (source_name == "typed_compile_define") {
    if (binding_context.definition == nullptr) return false;
    const auto* abi = uniform_abi(admission, binding_name);
    PlanValue owned;
    const auto* bound =
        bound_uniform_value(*binding_context.definition, step, binding_name, owned);
    if (abi == nullptr || bound == nullptr) return false;
    value = materialize_plan_value(*bound, abi->cpp_type, step, admission,
                                   binding_name);
    return true;
  }
  if (source_name == "typed_pass_define") {
    if (admission.identity.program_key != "render/pointsBillboardRender:depthKeys" ||
        binding_name != "VIEW_MODE" || !pass.defines.has_value() ||
        pass.defines->kind != effects::ValueKind::object ||
        pass.defines->object.size() != 1U ||
        pass.defines->object[0].first != "VIEW_MODE" ||
        pass.defines->object[0].second.kind != effects::ValueKind::number)
      return false;
    const double mode = pass.defines->object[0].second.number;
    if ((pass.name == "depthKeys_1" && mode == 1.0) ||
        (pass.name == "depthKeys_2" && mode == 2.0)) {
      value = static_cast<std::int32_t>(mode);
      return true;
    }
    return false;
  }
  if (source_name == "remap_uniform_data") {
    if (binding_context.inputs == nullptr || binding_context.definition == nullptr) return false;
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

// The scatter analog of the ordinary ABI preflight below: a scatter pass's
// authenticated ABI lives entirely in `admission.scatter` (empty for an
// ordinary admission and vice versa -- see registry.cpp's `admission()`),
// so it is checked against that contract instead of `admission.samplers`/
// `admission.uniforms` (both structurally empty for a scatter admission).
// Every fact this proves is resolvability/shape, exactly like the ordinary
// branch: the real values are read again, identically, when the dispatch
// branch in `execute()` actually builds the adapter's `Bindings`.
std::optional<double> scatter_pass_define_uniform(
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass, std::string_view uniform_name) {
  const auto& key = admission.identity.program_key;
  const bool points = key == "render/pointsRender:deposit";
  const bool billboards = key == "render/pointsBillboardRender:deposit";
  if (!points && !billboards) return std::nullopt;
  double view_mode = -1.0;
  double blend_mode = 0.0;
  double blur_layer = 0.0;
  if (pass.name == "deposit_0") view_mode = 0.0;
  else if (pass.name == "deposit_1") view_mode = 1.0;
  else if (pass.name == "deposit_2") view_mode = 2.0;
  else if (billboards && pass.name == "depositDefocus_1") { view_mode = 1.0; blur_layer = 1.0; }
  else if (billboards && pass.name == "depositDefocus_2") { view_mode = 2.0; blur_layer = 1.0; }
  else if (billboards && pass.name == "deposit_alpha_0") { view_mode = 0.0; blend_mode = 1.0; }
  else if (billboards && pass.name == "deposit_alpha_1") { view_mode = 1.0; blend_mode = 1.0; }
  else if (billboards && pass.name == "deposit_alpha_2") { view_mode = 2.0; blend_mode = 1.0; }
  if (!pass.defines.has_value() || pass.defines->kind != effects::ValueKind::object ||
      pass.defines->object.size() != (points ? 1U : 3U) || view_mode < 0.0) {
    throw binding_error(step, admission, GraphErrorCode::invalid_snapshot,
                        "scatter pass defines differ from registered pass");
  }
  bool found_view = false;
  bool found_blend = false;
  bool found_blur = false;
  for (const auto& [name, value] : pass.defines->object) {
    if (name == "VIEW_MODE") { if (found_view) throw binding_error(step, admission, GraphErrorCode::invalid_snapshot, "duplicate scatter define"); found_view = true; }
    if (name == "BLEND_MODE") { if (found_blend) throw binding_error(step, admission, GraphErrorCode::invalid_snapshot, "duplicate scatter define"); found_blend = true; }
    if (name == "BLUR_LAYER") { if (found_blur) throw binding_error(step, admission, GraphErrorCode::invalid_snapshot, "duplicate scatter define"); found_blur = true; }
    const double expected = name == "VIEW_MODE" ? view_mode :
                            (billboards && name == "BLEND_MODE" ? blend_mode :
                             (billboards && name == "BLUR_LAYER" ? blur_layer : -1.0));
    if (expected < 0.0 || value.kind != effects::ValueKind::number || value.number != expected) {
      throw binding_error(step, admission, GraphErrorCode::invalid_snapshot,
                          "scatter pass defines differ from registered pass");
    }
  }
  if (!found_view || (billboards && (!found_blend || !found_blur))) {
    throw binding_error(step, admission, GraphErrorCode::invalid_snapshot,
                        "scatter pass defines are incomplete");
  }
  if (uniform_name == "viewMode") return view_mode;
  if (billboards && uniform_name == "blendMode") return blend_mode;
  if (billboards && uniform_name == "blurLayer") return blur_layer;
  return std::nullopt;
}

void preflight_scatter_pass_abi(const EffectStep& step, const PassAdmission& admission,
                                const effects::PassDefinition& pass,
                                const BindingMaterializationContext& context) {
  validate_pass_controls(step, admission, pass);
  if (context.destination_width == 0U || context.destination_height == 0U) {
    throw binding_error(step, admission, GraphErrorCode::invalid_dimension,
                        "output dimensions must be positive");
  }
  const auto& scatter = *admission.scatter;
  if (admission.identity.program_key == "render/pointsRender:deposit" ||
      admission.identity.program_key == "render/pointsBillboardRender:deposit") {
    (void)scatter_pass_define_uniform(step, admission, pass, "viewMode");
  }
  // JS's canonicalTextures (renderer.js) resolves EVERY declared pass input
  // under its own uniform name and hands the whole map to the adapter; the
  // adapter reads the subset its shader documents. The contract's
  // `input_texture` names the adapter's primary input and must appear among
  // the declared inputs with a non-empty route; additional declared inputs
  // (dla's velTex/rgbaTex) resolve like any other pass input at dispatch and
  // fail closed there. The earlier "exactly one declared input" rule was
  // written against the single-input wormhole/physarum contracts and
  // refused the authority's own multi-input deposit passes.
  bool contract_input_declared = false;
  for (const auto& input : pass.inputs) {
    if (input.first == scatter.input_texture && !input.second.empty()) {
      contract_input_declared = true;
    }
  }
  if (!contract_input_declared) {
    throw binding_error(step, admission, GraphErrorCode::missing_binding,
                        "scatter input route is invalid");
  }
  // Unlike the ordinary branch, this does not additionally probe
  // `context.lookup_surface`: that table is populated from
  // `admission.samplers` (structurally empty for a scatter admission -- see
  // registry.cpp's `admission()` early return), so it is never populated
  // with the scatter route at all and would spuriously fail here even on a
  // fully resolvable plan. The route's actual availability is authenticated
  // twice already: generically for every pass's `pass.inputs`, scatter
  // included, by `validate_plan_before_allocation`'s own read-before-write
  // loop; and again, for real, by the dispatch branch in `execute()` itself
  // (`resolve_route` there throws `read_before_write` on the same miss).
  validate_pass_output_abi(step, pass, admission, admission.identity.index);
  std::unordered_set<std::string> uniform_names;
  for (const auto& uniform : scatter.uniforms) {
    if (!uniform_names.insert(uniform.name).second) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "duplicate uniform ABI binding name");
    }
    // registry.cpp's own construction-time authentication already requires
    // every scatter uniform to be exactly this shape (`scatter_contract()`,
    // "Malformed scatter compatibility contract"); re-checked here too, so
    // this function fails closed on its own rather than trusting that an
    // upstream check already ran. `source_name` is legitimately empty for
    // every currently-generated scatter uniform (the raw
    // `CompatibilityBindingEvidence` never populates it -- see
    // `effect_catalog.cpp`'s `ScatterCompatibility` literal): the binding
    // NAME doubles as the effect-parameter name to resolve, since a scatter
    // uniform is always an identity `{uniform: "x"}` mapping in the JS
    // source. A future adapter with a real, distinct `source_name` still
    // works: that value wins whenever it is non-empty.
    if (uniform.cpp_type != "double" || uniform.source != "effect_parameter" ||
        uniform.name.empty()) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "scatter uniform ABI is invalid");
    }
    if (scatter_pass_define_uniform(step, admission, pass, uniform.name).has_value()) continue;
    if (context.definition == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "scatter uniform value is missing");
    }
    const std::string_view lookup_name =
        uniform.source_name.empty() ? std::string_view(uniform.name) : std::string_view(uniform.source_name);
    PlanValue owned;
    if (bound_uniform_value(*context.definition, step, lookup_name, owned) == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "scatter uniform value is missing");
    }
  }
}

void materialize_optional_color_alpha(glsl::Bindings& bindings,
                                      const EffectStep& step,
                                      const PassAdmission& admission,
                                      std::string_view name);

void preflight_pass_abi(const EffectStep& step, const PassAdmission& admission,
                        const effects::PassDefinition& pass,
                        const BindingMaterializationContext& context) {
  if (scatter_adapter_available(admission)) {
    preflight_scatter_pass_abi(step, admission, pass, context);
    return;
  }
  validate_pass_controls(step, admission, pass);
  if (context.destination_width == 0U || context.destination_height == 0U) {
    throw binding_error(step, admission, GraphErrorCode::invalid_dimension,
                        "output dimensions must be positive");
  }
  // The authority pass can bind inputs its shader does not declare (the
  // cellularAutomata and MNCA render passes each bind four, but sample two).
  // Match exact name/route pairs, independently of the input map's order:
  // Hydraulic's shader declares inputTex first while its pass binds it last.
  // The full pass and shader-ordered ABI are independently authenticated
  // against their generated anchors before execution.
  std::unordered_set<std::string> sampler_names;
  for (const auto& sampler : admission.samplers) {
    if (sampler.type != "sampler2D" || sampler.cpp_type != "const Surface&") {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "sampler ABI type is invalid");
    }
    const auto input = std::find_if(pass.inputs.begin(), pass.inputs.end(),
                                    [&](const auto& candidate) {
                                      return candidate.first == sampler.name;
                                    });
    if (sampler.name.empty() || !sampler_names.insert(sampler.name).second ||
        input == pass.inputs.end() || sampler.resource != input->second ||
        sampler.resource.empty() || sampler.source != "resource" ||
        !sampler.source_name.empty()) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "sampler ABI route is invalid");
    }
    if (direct_mesh_resource(admission, sampler.resource)) {
      if (context.inputs == nullptr) {
        throw binding_error(step, admission, GraphErrorCode::missing_resource,
                            "declared mesh data resource is unavailable");
      }
    } else if (context.lookup_surface != nullptr &&
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
  if (admission.identity.program_key == "filter/halftone:halftone") {
    glsl::Bindings color_alpha;
    materialize_optional_color_alpha(color_alpha, step, admission, "inkColor");
    materialize_optional_color_alpha(color_alpha, step, admission, "paperColor");
  }
  glsl::Bindings defines;
  materialize_compile_defines(defines, step, admission, context);
}

void materialize_optional_color_alpha(glsl::Bindings& bindings,
                                      const EffectStep& step,
                                      const PassAdmission& admission,
                                      std::string_view name) {
  const PlanValue* value = parameter(step, name);
  if (value == nullptr || value->kind != PlanValue::Kind::array ||
      (value->array.size() != 3U && value->array.size() != 4U) ||
      (value->array.size() == 4U && value->array[3].kind != PlanValue::Kind::number)) {
    throw binding_error(step, admission, GraphErrorCode::binding_type,
                        std::string(name) + ": color must have three or four numeric lanes");
  }
  const std::string suffix(name);
  bindings.set_uniform("__cpuColorHasAlpha_" + suffix, value->array.size() == 4U);
  bindings.set_uniform("__cpuColorAlpha_" + suffix,
                       value->array.size() == 4U ? value->array[3].number : 0.0);
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
  if (admission.identity.program_key == "filter/halftone:halftone") {
    materialize_optional_color_alpha(bindings, step, admission, "inkColor");
    materialize_optional_color_alpha(bindings, step, admission, "paperColor");
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
    // The whole-pass CPU adapter reads these exact authenticated inputs from
    // MeshData. Their route/type ABI and presence were checked in preflight.
    if (direct_mesh_resource(admission, sampler.resource)) continue;
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

// Builds the `glsl::Bindings` a scatter adapter reads, mirroring JS's
// scatter call sites (renderer.js:1331/1356): `canonicalTextures` resolves
// EVERY declared pass input under its own declared uniform name (the adapter
// reads the subset its shader documents -- xyzTex, velTex, rgbaTex,
// stateTex1, inputTex, ...) and `buildScatterBindings` (renderer.js:819-830)
// adds the scalar context; each uniform here is sourced from an ordinary
// effect parameter (registry.cpp's construction-time authentication
// guarantees every scatter uniform is `cpp_type=="double"`/
// `source=="effect_parameter"`). This is a smaller analog of
// `materialize_uniform_bindings`/`materialize_sampler_bindings` above, not a
// reuse of them, because a scatter admission's own
// `admission.samplers`/`admission.uniforms` are structurally empty (see
// registry.cpp's `admission()` early return) -- everything a scatter pass
// needs instead lives in `admission.scatter` plus the pass's declared
// inputs. Callers pass every declared input already resolved; a null surface
// here would mean a caller skipped its own read-before-write refusal.
glsl::Bindings materialize_scatter_bindings(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition,
    const effects::PassDefinition& pass,
    const std::vector<std::pair<std::string, const noisemaker::Surface*>>& inputs) {
  glsl::Bindings bindings;
  const auto& scatter = *admission.scatter;
  try {
    for (const auto& input : inputs) bindings.set_texture(input.first, *input.second);
  } catch (const glsl::KernelBindingError& error) {
    throw binding_error(step, admission, GraphErrorCode::binding_type, error.what());
  }
  for (const auto& uniform : scatter.uniforms) {
    const auto derived = scatter_pass_define_uniform(step, admission, pass, uniform.name);
    if (derived.has_value()) {
      bindings.set_uniform(uniform.name, *derived);
      continue;
    }
    // `source_name` is legitimately empty for every currently-generated
    // scatter uniform -- see the matching comment in
    // `preflight_scatter_pass_abi`. The binding name doubles as the
    // effect-parameter name to resolve in that case.
    const std::string_view lookup_name =
        uniform.source_name.empty() ? std::string_view(uniform.name) : std::string_view(uniform.source_name);
    PlanValue owned;
    const auto* value = bound_uniform_value(definition, step, lookup_name, owned);
    if (value == nullptr) {
      throw binding_error(step, admission, GraphErrorCode::missing_binding,
                          "scatter uniform value is missing");
    }
    const double number_value = plan_number(value);
    if (!std::isfinite(number_value)) {
      throw binding_error(step, admission, GraphErrorCode::binding_type,
                          "scatter uniform value is not finite");
    }
    try {
      bindings.set_uniform(uniform.name, number_value);
    } catch (const glsl::KernelBindingError& error) {
      throw binding_error(step, admission, GraphErrorCode::binding_type, error.what());
    }
  }
  return bindings;
}

// Builds the minimal `ScatterPass` slice a scatter adapter reads, generically,
// from the compiled `effects::PassDefinition` -- no per-effect special case
// (see registry.hpp's `ScatterPass` for exactly which two JS `pass` fields
// any shipped adapter reads, and why nothing else is carried).
noisemaker::scatter::ScatterPass scatter_pass_from_definition(
    const effects::PassDefinition& pass, noisemaker::TextureFormat destination_format) {
  noisemaker::scatter::ScatterPass result;
  result.destination_format = destination_format;
  // `pass.blend`, ONLY the two-element-factors shape (JS's
  // `Array.isArray(pass.blend)` true branch) -- a boolean-kind blend (or no
  // blend at all, wormhole's own shape) leaves `blend_factors` unset,
  // matching `isPremultipliedBlend`'s `!Array.isArray(pass.blend)` early
  // `false`.
  if (pass.blend.has_value() && pass.blend->kind == effects::BlendKind::factors) {
    result.blend_factors = std::make_pair(pass.blend->factors[0], pass.blend->factors[1]);
  }
  // `pass.count`, only when it is an actual JS number (JS `pass?.count`,
  // read by flow3d's adapter). The string sentinel `"input"` some scatter
  // passes declare (wormhole's own `deposit`) is a different, DSL-level
  // concept -- "run once per source pixel", authenticated separately via
  // `admission.scatter->count` -- not the numeric agent-count field a
  // shipped adapter reads off `pass`, so it maps to `nullopt` here exactly
  // like an absent `count`.
  if (pass.count.has_value() && pass.count->kind == effects::ValueKind::number &&
      std::isfinite(pass.count->number)) {
    result.count = pass.count->number;
  }
  return result;
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

// ---------------------------------------------------------------------------
// Iteration-group execution.
//
// See docs/port-engineering/iteration-group-resource-lifetime.md for the full
// design; every citation below is against that document's own citations of
// the JS authority (noisemaker-for-cpu 61aa869, src/runtime/renderer.js and
// src/runtime/iteration.js). Summary: an iterated group's step-scoped and
// group-shared resources are deliberately kept OUT of ResourceArena --
// mirroring the JS authority's own `state.resources`/`groupResources`, which
// are never merged into its `surfaces` map either -- so nothing here can be
// bound by name from outside the one group run that owns it. Only the
// group's final surface (an independent clone) ever crosses into the arena,
// exactly like a non-iterated step's own final pass output already does.
namespace {

// ResourceArena::find/insert are private (friend GraphExecutor only, per
// resource.hpp) -- a lambda defined inside GraphExecutor::execute() inherits
// that access, but a free function does not. Every group-execution helper
// below is therefore a free function that only ever reads the arena through
// its public `require()` (wrapped here to return nullptr instead of
// throwing, exactly like `find` would); the two places that must publish a
// finished surface into the arena (zero_iteration_group_output's result and
// run_iterated_group's final output) return the surface/format/route to
// GraphExecutor::execute() instead, which performs the actual `arena.insert`
// itself, the same way it already publishes every non-iterated pass output.
[[nodiscard]] const GraphResource* find_named_resource(const ResourceArena& arena,
                                                        std::string_view name) noexcept {
  try {
    return &arena.require(name);
  } catch (const std::out_of_range&) {
    return nullptr;
  }
}

// noisemaker::Surface has no default constructor, so
// `std::unordered_map<std::string, Surface>::operator[]` cannot be used
// (it default-constructs on a miss before ever reaching the assignment).
// Mirrors iteration::GroupResourceMap::store's own find-then-emplace-or-
// move-assign shape.
void store_step_resource(std::unordered_map<std::string, noisemaker::Surface>& resources,
                         std::string name, noisemaker::Surface surface) {
  const auto iterator = resources.find(name);
  if (iterator != resources.end()) {
    iterator->second = std::move(surface);
    return;
  }
  resources.emplace(std::move(name), std::move(surface));
}

// renderer.js:34-45 -- groupOwnerStateSize. `undefined` (here: nullopt) for a
// single-step group or an owner with no bound `stateSize`.
[[nodiscard]] std::optional<double> group_owner_state_size(
    const EffectStep& owner_step, std::size_t group_step_count) {
  if (group_step_count <= 1U) return std::nullopt;
  const auto* value = parameter(owner_step, "stateSize");
  if (value == nullptr || value->kind != PlanValue::Kind::number) return std::nullopt;
  return value->number;
}

// renderer.js:660-663 -- initializeGroupStepState's `sourceStep`: a joining
// step's own `stateSize` binding is unconditionally replaced with the
// owner's resolved value whenever the step declares one at all.
[[nodiscard]] EffectStep apply_owner_state_size_override(const EffectStep& step,
                                                          double owner_state_size) {
  EffectStep result = step;
  for (auto& binding : result.params) {
    if (binding.name == "stateSize") {
      binding.value = PlanValue::number_value(owner_state_size);
      return result;
    }
  }
  result.params.push_back({"stateSize", PlanValue::number_value(owner_state_size)});
  return result;
}

// renderer.js:23-32 -- PARTICLE_STATE_FALLBACK_FORMATS / particleStateFallbackFormat.
[[nodiscard]] std::string_view particle_state_fallback_format(std::string_view name) {
  if (name == "global_xyz" || name == "global_vel") return "rgba32f";
  if (name == "global_rgba") return "rgba8";
  return "rgba16f";
}

// renderer.js:665-666 -- usesSelfTex: any pass input value is the reserved
// `selfTex`/`feedback` token.
[[nodiscard]] bool step_uses_self_tex(const effects::EffectDefinition& definition) noexcept {
  for (const auto& pass : definition.passes) {
    for (const auto& input : pass.inputs) {
      if (input.second == "selfTex" || input.second == "feedback") return true;
    }
  }
  return false;
}

// Per-step, per-group-run state: the C++ analog of JS's `state` object built
// once by `initializeGroupStepState` (renderer.js:660-677) and threaded
// unchanged through all `N` iterations.
struct GroupStepState {
  const PlanEffectSnapshot* snapshot = nullptr;
  // Possibly a stateSize-overridden clone (apply_owner_state_size_override)
  // with automation resolved; every downstream lookup (dimensions, uniforms,
  // pass enable/repeat) reads this, never the original chain step.
  EffectStep effective_step{};
  // The same clone before automation resolves (renderer.js `rawStep`): each
  // iteration re-resolves `osc(...)` parameters from it at its own time.
  EffectStep raw_step{};
  // state.resources: declared scratch, refreshed inputTex/surface-parameter
  // routes. Persists across all N iterations; never touches ResourceArena.
  std::unordered_map<std::string, noisemaker::Surface> resources;
  bool uses_self_tex = false;
  std::optional<noisemaker::Surface> self_tex;
};

// renderer.js:679-704 -- groupTextureSpec, folded with the dimension/format
// resolution its two callers (resolveGroupParticleTexture,
// groupOutputDestination) both immediately perform on its result: the first
// step (group order) that declares `name` in its own textures, or the
// synthetic `{param:'stateSize', default:256}` fallback resolved against the
// REFERENCING step.
struct GroupTextureResolution {
  std::size_t width = 0;
  std::size_t height = 0;
  noisemaker::TextureFormat format = noisemaker::TextureFormat::rgba16f;
};

[[nodiscard]] GroupTextureResolution resolve_group_particle_texture_spec(
    std::string_view name, const std::vector<GroupStepState>& step_states,
    const EffectStep& referencing_step, const ResourceArena& arena,
    const ExecutionInputs& inputs) {
  for (const auto& candidate : step_states) {
    const auto* texture = texture_for(candidate.snapshot->definition, name);
    if (texture == nullptr) continue;
    GroupTextureResolution resolution;
    resolution.width = resolve_dimension(texture->width, candidate.effective_step, arena,
                                         inputs.width, true);
    resolution.height = resolve_dimension(texture->height, candidate.effective_step, arena,
                                          inputs.height, false);
    resolution.format = resolve_texture_format(texture->format);
    return resolution;
  }
  effects::DimensionExpression fallback;
  fallback.kind = effects::DimensionKind::parameter_default;
  fallback.parameter = "stateSize";
  fallback.default_value = 256.0;
  GroupTextureResolution resolution;
  resolution.width = resolve_dimension(fallback, referencing_step, arena, inputs.width, true);
  resolution.height = resolve_dimension(fallback, referencing_step, arena, inputs.height, false);
  resolution.format = resolve_texture_format(particle_state_fallback_format(name));
  return resolution;
}

// renderer.js:711-720 -- resolveGroupParticleTexture: lazily creates
// (zero-cleared, once) a group-scoped particle-state texture. Never called
// for the literal `global_accum`, which is only ever seeded up front for a
// loop region (renderer.js:858-865) or absent -- see
// lookup_group_step_route below.
[[nodiscard]] const noisemaker::Surface* resolve_or_create_group_particle_texture(
    std::string_view name, const std::vector<GroupStepState>& step_states,
    const EffectStep& referencing_step, iteration::GroupResourceMap& group_resources,
    const ResourceArena& arena, const ExecutionInputs& inputs) {
  if (const auto* existing = group_resources.find(name)) return existing;
  const auto resolution =
      resolve_group_particle_texture_spec(name, step_states, referencing_step, arena, inputs);
  noisemaker::Surface surface(resolution.width, resolution.height);
  surface.clear();
  group_resources.store(std::string(name), std::move(surface));
  return group_resources.find(name);
}

// The route-lookup context and callback plugged into
// BindingMaterializationContext for a group step's pass materialization --
// the iterated-group analog of `lookup_resolved_sampler_route`.
struct GroupStepRouteContext {
  GroupStepState* state = nullptr;
  iteration::GroupResourceMap* group_resources = nullptr;
  const noisemaker::Surface* empty_surface = nullptr;
  const ResourceArena* arena = nullptr;
};

// renderer.js:726-743 -- groupInputTextures' per-route resolution (the lazy
// particle-texture *creation* it also performs happens separately, before
// this is consulted -- see ensure_group_particle_inputs below, since a plain
// lookup callback cannot create a resource).
[[nodiscard]] const noisemaker::Surface* lookup_group_step_route(void* context,
                                                                  std::string_view route) {
  auto* ctx = static_cast<GroupStepRouteContext*>(context);
  if (ctx == nullptr) return nullptr;
  if (route == "midiNoteGrid") {
    const auto* resource = ctx->arena == nullptr ? nullptr : find_named_resource(*ctx->arena, route);
    return resource == nullptr ? nullptr : &resource->surface();
  }
  if (route == "selfTex" || route == "feedback") {
    return ctx->state->self_tex.has_value() ? &*ctx->state->self_tex : ctx->empty_surface;
  }
  if (route == "global_accum") {
    if (const auto* surface = ctx->group_resources->find(route)) return surface;
    // Falls through: JS only special-cases global_accum when the group map
    // already has it (renderer.js:733-736); otherwise it is ordinary
    // step-local state, exactly like any other declared texture.
  } else if (iteration::is_particle_state_name(route)) {
    return ctx->group_resources->find(route);
  }
  const auto iterator = ctx->state->resources.find(std::string(route));
  return iterator == ctx->state->resources.end() ? nullptr : &iterator->second;
}

// Lazily creates every particle-state texture this pass's own inputs
// reference before binding materialization runs (resolveGroupParticleTexture
// is called inline by groupInputTextures in JS; a plain SurfaceLookup
// callback has no create side, so this runs once up front instead).
void ensure_group_particle_inputs(const effects::PassDefinition& pass,
                                  const std::vector<GroupStepState>& step_states,
                                  const EffectStep& referencing_step,
                                  iteration::GroupResourceMap& group_resources,
                                  const ResourceArena& arena, const ExecutionInputs& inputs) {
  for (const auto& input : pass.inputs) {
    if (iteration::is_particle_state_name(input.second)) {
      (void)resolve_or_create_group_particle_texture(input.second, step_states, referencing_step,
                                                      group_resources, arena, inputs);
    }
  }
}

// renderer.js:947-950 -- the top-of-iteration `bindings.textures` merge into
// `state.resources`: `inputTex` (this iteration's threading input) and every
// surface-parameter route are refreshed every iteration, exactly like
// buildBindings feeds them fresh every non-iterated call.
void seed_group_step_bindings(GroupStepState& state,
                              const noisemaker::Surface* iteration_input,
                              const noisemaker::Surface* iteration_volume,
                              const noisemaker::Surface* iteration_geometry,
                              const ResourceArena& arena,
                              const ExecutionInputs& inputs) {
  if (iteration_input != nullptr) {
    store_step_resource(state.resources, "inputTex", iteration_input->clone());
  } else {
    state.resources.erase("inputTex");
  }
  if (iteration_volume != nullptr)
    store_step_resource(state.resources, "inputTex3d", iteration_volume->clone());
  else
    state.resources.erase("inputTex3d");
  if (iteration_geometry != nullptr)
    store_step_resource(state.resources, "inputGeo", iteration_geometry->clone());
  else
    state.resources.erase("inputGeo");
  const auto& definition = state.snapshot->definition;
  for (const auto& declared : definition.parameters) {
    if (declared.type == "volume" || declared.type == "geometry") {
      const noisemaker::Surface* incoming = declared.type == "volume"
          ? iteration_volume : iteration_geometry;
      if (incoming != nullptr) {
        store_step_resource(state.resources, declared.name, incoming->clone());
        continue;
      }
      if (state.resources.find(declared.name) != state.resources.end()) continue;
      const auto& output_name = declared.type == "volume"
          ? definition.output_tex3d : definition.output_geo;
      const auto* texture = output_name.has_value()
          ? texture_for(definition, *output_name) : nullptr;
      if (texture == nullptr) {
        throw GraphError(GraphErrorCode::missing_resource,
                         "typed parameter requires a declared output texture",
                         state.effective_step.effect.id);
      }
      noisemaker::Surface seed(
          resolve_dimension(texture->width, state.effective_step, arena,
                            inputs.width, true),
          resolve_dimension(texture->height, state.effective_step, arena,
                            inputs.height, false));
      seed.clear();
      store_step_resource(state.resources, declared.name, std::move(seed));
      continue;
    }
    if (declared.type != "surface") continue;
    const std::string route(bound_texture_name(declared));
    const auto* value = parameter(state.effective_step, declared.name);
    if (value == nullptr) continue;
    if (value->kind == PlanValue::Kind::null_value) {
      store_step_resource(state.resources, route, noisemaker::Surface(1U, 1U));
      continue;
    }
    if (value->kind != PlanValue::Kind::surface) continue;
    if (value->surface.kind == SurfaceReference::Kind::input) {
      if (iteration_input == nullptr) {
        throw GraphError(GraphErrorCode::missing_resource,
                         "surface parameter requires an input surface",
                         state.effective_step.effect.id);
      }
      store_step_resource(state.resources, route, iteration_input->clone());
    } else if (value->surface.kind == SurfaceReference::Kind::named) {
      const auto* resource = find_named_resource(arena, value->surface.name);
      if (resource == nullptr) {
        throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced",
                         state.effective_step.effect.id);
      }
      store_step_resource(state.resources, route, resource->surface().clone());
    }
  }
}

// renderer.js:767-774 -- ensureGroupScratchResources: zero-fills, once, every
// declared texture the step's own map does not already hold and that is not
// a particle-state name (those are the group map's concern). Idempotent
// after the first iteration, since `resources.contains(name)` is then always
// true -- matching the JS comment on the identical idiom.
void ensure_group_scratch_resources(GroupStepState& state, const ResourceArena& arena,
                                    const ExecutionInputs& inputs) {
  const auto& definition = state.snapshot->definition;
  for (const auto& texture : definition.textures) {
    if (iteration::is_particle_state_name(texture.name)) continue;
    if (state.resources.find(texture.name) != state.resources.end()) continue;
    const auto width = resolve_dimension(texture.width, state.effective_step, arena,
                                         inputs.width, true);
    const auto height = resolve_dimension(texture.height, state.effective_step, arena,
                                          inputs.height, false);
    const auto format = resolve_texture_format(texture.format);
    (void)format;
    noisemaker::Surface surface(width, height);
    surface.clear();
    state.resources.emplace(texture.name, std::move(surface));
  }
}

// renderer.js:745-760 -- groupOutputDestination: a particle-state output
// route is sized via the declaring step's own spec (resolve_group_particle_
// texture_spec); everything else -- including the literal `global_accum`,
// which is an ordinary declared texture on whichever effect owns it -- via
// the CURRENT step's own declared texture (or the render extent/rgba16f
// default when undeclared, matching the non-iterated path's own fallback).
[[nodiscard]] noisemaker::Surface allocate_group_output_destination(
    std::string_view name, const effects::PassDefinition& pass, const GroupStepState& state,
    const std::vector<GroupStepState>& step_states, const ResourceArena& arena,
    const ExecutionInputs& inputs, noisemaker::TextureFormat& format_out) {
  if (iteration::is_particle_state_name(name)) {
    const auto resolution =
        resolve_group_particle_texture_spec(name, step_states, state.effective_step, arena, inputs);
    format_out = resolution.format;
    return noisemaker::Surface(resolution.width, resolution.height);
  }
  const auto* texture = texture_for(state.snapshot->definition, name);
  const auto lookup = [&](std::string_view route) -> const noisemaker::Surface* {
    const auto found = state.resources.find(std::string(route));
    return found == state.resources.end() ? nullptr : &found->second;
  };
  const auto width = destination_dimension(pass, texture, state.effective_step, arena,
                                            inputs.width, true, lookup);
  const auto height = destination_dimension(pass, texture, state.effective_step, arena,
                                             inputs.height, false, lookup);
  format_out = noisemaker::TextureFormat::rgba16f;
  if (texture != nullptr) {
    format_out = resolve_texture_format(texture->format);
  }
  return noisemaker::Surface(width, height);
}

// renderer.js:762-765 -- storeGroupOutput's single routing predicate, already
// ported as iteration::is_group_shared_resource_name.
void store_group_output(std::string_view name, noisemaker::Surface surface, GroupStepState& state,
                        iteration::GroupResourceMap& group_resources) {
  if (iteration::is_group_shared_resource_name(name)) {
    group_resources.store(std::string(name), std::move(surface));
  } else {
    store_step_resource(state.resources, std::string(name), std::move(surface));
  }
}

struct GroupStepIterationResult {
  noisemaker::Surface surface{1U, 1U};
  noisemaker::TextureFormat format = noisemaker::TextureFormat::rgba16f;
  std::string output_route;
};

struct GroupIterationBundle {
  std::optional<noisemaker::Surface> image;
  std::optional<noisemaker::Surface> volume;
  std::optional<noisemaker::Surface> geometry;
  noisemaker::TextureFormat image_format = noisemaker::TextureFormat::rgba16f;
  noisemaker::TextureFormat volume_format = noisemaker::TextureFormat::rgba16f;
  noisemaker::TextureFormat geometry_format = noisemaker::TextureFormat::rgba16f;
  std::string image_route;
  std::string volume_route;
  std::string geometry_route;
  std::optional<double> volume_size;
};

// renderer.js:943-1074 -- runGroupStepIterationSync, plus groupMrtDestinations
// (806-814) for the MRT shape. Structurally mirrors the non-iterated
// EffectStep loop in GraphExecutor::execute() (the same three pass shapes it
// supports: MRT, scatter, and ordinary single fragment output); the
// divergences are exactly the persistent-resources, group-routing, and
// selfTex bookkeeping this whole block exists for. Reuses every existing
// authenticated materialization helper unchanged.
[[nodiscard]] GroupStepIterationResult run_group_step_iteration(
    GroupStepState& state, const noisemaker::Surface* iteration_input,
    const noisemaker::Surface* iteration_volume,
    const noisemaker::Surface* iteration_geometry,
    const std::vector<GroupStepState>& step_states, iteration::GroupResourceMap& group_resources,
    ResourceArena& arena, const ExecutionInputs& iteration_inputs, std::size_t& pass_count,
    const noisemaker::Surface& empty_surface) {
  seed_group_step_bindings(state, iteration_input, iteration_volume,
                           iteration_geometry, arena, iteration_inputs);
  ensure_group_scratch_resources(state, arena, iteration_inputs);

  const auto& definition = state.snapshot->definition;
  const auto& admissions = state.snapshot->admissions;
  GroupStepIterationResult result;
  bool produced = false;

  for (std::size_t pass_index = 0; pass_index < definition.passes.size(); ++pass_index) {
    const auto& pass = definition.passes[pass_index];
    const auto& admission = admissions[pass_index];
    if (mesh_adapter_available(admission)) {
      throw binding_error(state.effective_step, admission, GraphErrorCode::unsupported_draw_mode,
                          "CPU authority does not support mesh whole-pass rendering inside iterated groups");
    }
    bool enabled = false;
    std::size_t repeats = 0U;
    try {
      enabled = pass_enabled(pass, state.effective_step);
      repeats = pass_repeat(pass, state.effective_step);
    } catch (const std::exception& error) {
      throw GraphError(GraphErrorCode::invalid_options, error.what(),
                       state.effective_step.effect.id, pass_index, pass.name,
                       admission.identity.program_key);
    }
    if (!enabled || repeats == 0U) continue;
    const bool dispatch_scatter = scatter_adapter_available(admission);
    const std::string output_route = pass.outputs.front().second;

    const bool dispatch_mrt = admission.outputs.size() > 1U;

    for (std::size_t repeat = 0; repeat < repeats; ++repeat) {
      ensure_group_particle_inputs(pass, step_states, state.effective_step, group_resources,
                                   arena, iteration_inputs);

      if (dispatch_mrt) {
        // groupMrtDestinations (renderer.js:806-814): resolve every declared
        // output's own destination independently (allocate_group_output_
        // destination is the same per-route sizing the single-output branch
        // below uses), assert they share dimensions BEFORE binding a kernel
        // or running anything (assertMrtDestinationsShareDimensions,
        // renderer.js:51-58 -- the non-iterated MRT branch above ports the
        // same assertion), then run the whole pass through one shared
        // pixel loop (run_mrt_pass, mirroring runCanonicalMrtPass).
        struct MrtDestination { std::string route; noisemaker::TextureFormat format; };
        std::vector<MrtDestination> destinations;
        destinations.reserve(pass.outputs.size());
        std::size_t mrt_width = iteration_inputs.width;
        std::size_t mrt_height = iteration_inputs.height;
        for (std::size_t slot = 0; slot < pass.outputs.size(); ++slot) {
          noisemaker::TextureFormat format = noisemaker::TextureFormat::rgba16f;
          noisemaker::Surface probe = allocate_group_output_destination(
              pass.outputs[slot].second, pass, state, step_states, arena, iteration_inputs, format);
          if (slot == 0U) {
            mrt_width = probe.width();
            mrt_height = probe.height();
          } else if (probe.width() != mrt_width || probe.height() != mrt_height) {
            throw GraphError(GraphErrorCode::unsupported_mrt,
                             "MRT destinations must share dimensions",
                             state.effective_step.effect.id, pass_index, pass.name,
                             admission.identity.program_key);
          }
          destinations.push_back({pass.outputs[slot].second, format});
        }
        GroupStepRouteContext route_context{&state, &group_resources, &empty_surface, &arena};
        // CPU 7f47340 (renderer.js MRT branches): upstream binds the canvas
        // size as `resolution` to every pass; the pixel loop still covers the
        // state-sized MRT destinations.
        const BindingMaterializationContext binding_context{
            &iteration_inputs, &definition, iteration_inputs.width, iteration_inputs.height,
            &lookup_group_step_route, &route_context};
        try {
          preflight_pass_abi(state.effective_step, admission, pass, binding_context);
          auto bindings = materialize_uniform_bindings(state.effective_step, admission, pass,
                                                        binding_context);
          materialize_sampler_bindings(bindings, admission, binding_context, state.effective_step,
                                       pass);
          apply_classic_noisedeck_palette_override(bindings, state.effective_step, definition);
          auto kernel = bind_factory_route_mrt(state.effective_step, admission, definition, bindings);
          auto rendered = noisemaker::run_mrt_pass(kernel, mrt_width, mrt_height,
                                                    noisemaker::f32(iteration_inputs.time),
                                                    noisemaker::f32(iteration_inputs.seed),
                                                    iteration_inputs.frame,
                                                    noisemaker::f32(iteration_inputs.delta_time));
          // renderer.js:1286 -- lastOutput = surfaceList[surfaceList.length
          // - 1]: the group step's own returned/threaded surface is
          // whichever slot ran last, by list position, matching the
          // non-iterated MRT branch's identical "last slot wins" for
          // effect_output -- never specifically the route named "outputTex"
          // (that is a SEPARATE, additional latch this port's non-iterated
          // path also keeps, `wrote_output_tex`, with no group-step analog
          // needed since a group step's return value is always threaded
          // forward regardless of route name, unlike the chain-level
          // `current`).
          for (std::size_t slot = 0; slot < destinations.size(); ++slot) {
            noisemaker::quantize_texture(rendered[slot], destinations[slot].format);
            noisemaker::Surface published_slot = rendered[slot].clone();
            store_group_output(destinations[slot].route, std::move(rendered[slot]), state,
                               group_resources);
            result.surface = std::move(published_slot);
            result.format = destinations[slot].format;
            result.output_route = destinations[slot].route;
          }
        } catch (const GraphError& error) {
          if (error.effect_id().empty()) {
            throw GraphError(error.code(), std::string(error.detail()), state.effective_step.effect.id,
                             pass_index, pass.name, admission.identity.program_key);
          }
          throw;
        } catch (const glsl::KernelBindingError&) {
          throw GraphError(GraphErrorCode::binding_type, "factory binding failed",
                           state.effective_step.effect.id, pass_index, pass.name,
                           admission.identity.program_key);
        } catch (const std::exception&) {
          throw GraphError(GraphErrorCode::execution_failure, "pass execution failed",
                           state.effective_step.effect.id, pass_index, pass.name,
                           admission.identity.program_key);
        }
        ++pass_count;
        produced = true;
        continue;
      }

      noisemaker::TextureFormat format = noisemaker::TextureFormat::rgba16f;
      noisemaker::Surface destination = allocate_group_output_destination(
          output_route, pass, state, step_states, arena, iteration_inputs, format);
      const std::size_t width = destination.width();
      const std::size_t height = destination.height();

      GroupStepRouteContext route_context{&state, &group_resources, &empty_surface, &arena};
      const BindingMaterializationContext binding_context{
          &iteration_inputs, &definition, width, height,
          &lookup_group_step_route, &route_context};

      try {
        preflight_pass_abi(state.effective_step, admission, pass, binding_context);
        if (dispatch_scatter) {
          // Same declared-name -> route mapping as the non-iterated branch:
          // every declared pass input resolves under its own name from the
          // group's step-local/group-shared resources (particle-state names
          // were lazily created by ensure_group_particle_inputs above).
          std::vector<std::pair<std::string, const noisemaker::Surface*>> scatter_inputs;
          scatter_inputs.reserve(pass.inputs.size());
          for (const auto& input : pass.inputs) {
            const auto* input_surface = lookup_group_step_route(&route_context, input.second);
            if (input_surface == nullptr) {
              throw GraphError(GraphErrorCode::read_before_write, "input resource is not produced",
                               state.effective_step.effect.id, pass_index, pass.name,
                               admission.identity.program_key);
            }
            scatter_inputs.push_back({input.first, input_surface});
          }
          auto bindings =
              materialize_scatter_bindings(state.effective_step, admission, definition, pass, scatter_inputs);
          const noisemaker::scatter::ScatterAdapter adapter =
              noisemaker::scatter::resolve_scatter_adapter(admission.identity.program_key);
          if (adapter == nullptr) {
            throw GraphError(GraphErrorCode::unsupported_scatter,
                             "no scatter adapter is registered for this program",
                             state.effective_step.effect.id, pass_index, pass.name,
                             admission.identity.program_key);
          }
          const auto* previous = lookup_group_step_route(&route_context, output_route);
          if (previous != nullptr && previous->data().size() == destination.data().size()) {
            const auto source = previous->data();
            const auto target = destination.data();
            std::copy(source.begin(), source.end(), target.begin());
          } else {
            destination.clear();
          }
          const noisemaker::scatter::ScatterPass scatter_pass = scatter_pass_from_definition(pass, format);
          adapter(bindings, scatter_pass, destination);
          noisemaker::quantize_texture(destination, format);
        } else {
          auto bindings = materialize_uniform_bindings(state.effective_step, admission, pass,
                                                        binding_context);
          materialize_sampler_bindings(bindings, admission, binding_context, state.effective_step,
                                       pass);
          apply_classic_noisedeck_palette_override(bindings, state.effective_step, definition);
          auto kernel = bind_factory_route(state.effective_step, admission, definition, bindings);
          destination = noisemaker::run_pass(kernel, width, height,
                                             noisemaker::f32(iteration_inputs.time),
                                             noisemaker::f32(iteration_inputs.seed),
                                             iteration_inputs.frame,
                                             noisemaker::f32(iteration_inputs.delta_time));
          noisemaker::quantize_texture(destination, format);
        }
      } catch (const GraphError& error) {
        if (error.effect_id().empty()) {
          throw GraphError(error.code(), std::string(error.detail()), state.effective_step.effect.id,
                           pass_index, pass.name, admission.identity.program_key);
        }
        throw;
      } catch (const glsl::KernelBindingError&) {
        throw GraphError(GraphErrorCode::binding_type, "factory binding failed",
                         state.effective_step.effect.id, pass_index, pass.name,
                         admission.identity.program_key);
      } catch (const std::exception&) {
        throw GraphError(GraphErrorCode::execution_failure, "pass execution failed",
                         state.effective_step.effect.id, pass_index, pass.name,
                         admission.identity.program_key);
      }

      ++pass_count;
      noisemaker::Surface published = destination.clone();
      store_group_output(output_route, std::move(destination), state, group_resources);
      result.surface = std::move(published);
      result.format = format;
      result.output_route = output_route;
      produced = true;
    }
  }

  // renderer.js runGroupStepIterationSync: the step's image is its own
  // `outputTex` step resource whenever the step map holds one
  // (`state.resources.get('outputTex') ?? lastOutput`), and only otherwise
  // the last pass output -- a trailing feedback pass that writes a scratch
  // texture (filter/motionBlur's `copy` into `_selfTex`) is not the result.
  // Every `outputTex` store in the step map is allocated by
  // allocate_group_output_destination / ensure_group_scratch_resources with
  // the same format rule, so the format follows from the definition.
  if (const auto found = state.resources.find("outputTex"); found != state.resources.end()) {
    const auto* texture = texture_for(definition, "outputTex");
    result.surface = found->second.clone();
    result.format = texture != nullptr ? resolve_texture_format(texture->format)
                                       : noisemaker::TextureFormat::rgba16f;
    result.output_route = "outputTex";
    produced = true;
  }
  if (!produced) {
    throw GraphError(GraphErrorCode::execution_failure, "iterated step produced no output",
                     state.effective_step.effect.id);
  }
  if (state.self_tex.has_value()) {
    // renderer.js:1068-1072 / assertSelfTexMatchesOutput: a raw byte copy,
    // never a reference swap, so a later pass within the SAME iteration that
    // also reads selfTex can never observe a pool-recycled buffer -- and
    // there is nothing to recycle here anyway, since self_tex is never
    // stored under a name either map's publish path could replace.
    if (state.self_tex->data().size() != result.surface.data().size()) {
      throw GraphError(GraphErrorCode::invalid_dimension,
                       "selfTex must match the step's own output",
                       state.effective_step.effect.id);
    }
    const auto source = result.surface.data();
    const auto target = state.self_tex->data();
    std::copy(source.begin(), source.end(), target.begin());
  }
  return result;
}

// The finished group output GraphExecutor::execute() still needs to publish
// into the arena itself (see find_named_resource's comment above for why
// this layer cannot call `arena.insert` directly).
struct GroupPublishResult {
  noisemaker::Surface surface{1U, 1U};
  bool has_image = false;
  noisemaker::TextureFormat format = noisemaker::TextureFormat::rgba16f;
  std::string route;
  std::optional<noisemaker::Surface> volume;
  std::optional<noisemaker::Surface> geometry;
  noisemaker::TextureFormat volume_format = noisemaker::TextureFormat::rgba16f;
  noisemaker::TextureFormat geometry_format = noisemaker::TextureFormat::rgba16f;
  std::string volume_route;
  std::string geometry_route;
  std::optional<double> volume_size;
};

// renderer.js:721-756 -- zeroIterationGroupOutput. An incoming bundle passes
// through. A volume generator that opens a chain creates clear volume and
// geometry atlases without running a shader pass.
[[nodiscard]] GroupPublishResult zero_iteration_group_output(GraphResource* group_input,
                                                              GraphResource* group_input_volume,
                                                              GraphResource* group_input_geometry,
                                                              const EffectStep& owner_step,
                                                              const effects::EffectDefinition& definition,
                                                              const ResourceArena& arena,
                                                              const ExecutionInputs& inputs) {
  GroupPublishResult result;
  if (group_input != nullptr || group_input_volume != nullptr || group_input_geometry != nullptr) {
    if (group_input != nullptr) {
      result.surface = group_input->surface().clone();
      result.has_image = true;
      result.format = group_input->format();
    }
    if (group_input_volume != nullptr) {
      result.volume = group_input_volume->surface().clone();
      result.volume_format = group_input_volume->format();
      result.volume_route = "inputTex3d";
    }
    if (group_input_geometry != nullptr) {
      result.geometry = group_input_geometry->surface().clone();
      result.geometry_format = group_input_geometry->format();
      result.geometry_route = "inputGeo";
    }
  } else if (definition.domain == "volume-generator") {
    const auto clear_destination = [&](std::string_view route) {
      const auto* texture = texture_for(definition, route);
      const auto width = texture == nullptr ? inputs.width :
          resolve_dimension(texture->width, owner_step, arena, inputs.width, true);
      const auto height = texture == nullptr ? inputs.height :
          resolve_dimension(texture->height, owner_step, arena, inputs.height, false);
      noisemaker::Surface surface(width, height);
      surface.clear();
      return surface;
    };
    if (!definition.output_tex3d.has_value()) {
      throw GraphError(GraphErrorCode::invalid_snapshot,
                       "volume generator has no outputTex3d", definition.id);
    }
    result.volume_route = *definition.output_tex3d;
    result.volume = clear_destination(result.volume_route);
    if (const auto* texture = texture_for(definition, result.volume_route))
      result.volume_format = resolve_texture_format(texture->format);
    if (definition.output_geo.has_value() && *definition.output_geo != "inputGeo") {
      result.geometry_route = *definition.output_geo;
      result.geometry = clear_destination(result.geometry_route);
      if (const auto* texture = texture_for(definition, result.geometry_route))
        result.geometry_format = resolve_texture_format(texture->format);
    }
  } else {
    result.surface = noisemaker::Surface(inputs.width, inputs.height);
    result.surface.clear();
    result.has_image = true;
  }
  result.route = group_input != nullptr ? "inputTex" : "outputTex";
  return result;
}

// renderer.js:852-893 (sync) / 895-936 (async, identical here since this
// executor has no async path) -- runIteratedGroupSync. Owns the whole
// N-iteration run: resolves N, seeds global_accum for a loop region, builds
// every step's persistent state once, runs the pass graph N times, and
// hands its final surface back for GraphExecutor::execute() to publish.
[[nodiscard]] GroupPublishResult run_iterated_group(const ExecutionPlan& plan,
                                                    const ExecutionChain& chain,
                                                    const iteration::IterationGroup& group,
                                                    GraphResource* group_input,
                                                    GraphResource* group_input_volume,
                                                    GraphResource* group_input_geometry,
                                                    ResourceArena& arena,
                                                    const ExecutionInputs& inputs,
                                                    std::size_t& pass_count) {
  const auto& owner_variant = chain.steps[group.step_indices.front()];
  const auto* owner_step = std::get_if<EffectStep>(&owner_variant);
  if (owner_step == nullptr) {
    throw GraphError(GraphErrorCode::execution_failure,
                     "iterated group's owning step is not an effect step");
  }
  const EffectStep* iteration_owner = owner_step;
  for (const auto index : group.step_indices) {
    const auto* candidate = std::get_if<EffectStep>(&chain.steps[index]);
    if (candidate != nullptr && plan.effects[candidate->snapshot_index].definition.iterated) {
      iteration_owner = candidate;
      break;
    }
  }
  const auto* requested = parameter(*iteration_owner, "iterationCount");
  const auto& owner_passes = plan.effects[iteration_owner->snapshot_index].definition.passes;
  const bool has_pass_repeat = std::any_of(owner_passes.begin(), owner_passes.end(),
      [](const auto& pass) {
        if (!pass.repeat.has_value()) return false;
        return (pass.repeat->kind == effects::ValueKind::number && pass.repeat->number != 0.0) ||
               (pass.repeat->kind == effects::ValueKind::string && !pass.repeat->string.empty());
      });
  // CPU authority ea4abf3: pass repeats already specify the per-frame
  // iteration count. Keep zero-iteration bypass and avoid multiplying it
  // by the group count a second time.
  PlanValue group_count;
  if (has_pass_repeat) {
    if (requested == nullptr || requested->kind == PlanValue::Kind::null_value) {
      group_count = PlanValue::number_value(1.0);
    } else if (requested->kind == PlanValue::Kind::number) {
      group_count = PlanValue::number_value(std::min(requested->number, 1.0));
    } else {
      group_count = *requested;
    }
    requested = &group_count;
  }
  const auto resolved = iteration::resolve_iteration_count(requested);
  if (resolved.zero_iterations) {
    return zero_iteration_group_output(
        group_input, group_input_volume, group_input_geometry, *owner_step,
        plan.effects[owner_step->snapshot_index].definition, arena, inputs);
  }
  // A multi-output (drawBuffers >= 2) pass has an authenticated generated MRT
  // route and runs through run_group_step_iteration's ported MRT branch
  // (renderer.js's MRT branch inside runGroupStepIteration: per-output
  // destinations via groupMrtDestinations, one shared pixel loop via
  // runCanonicalMrtPass, per-slot quantize/store, last slot wins for
  // lastOutput), so no refusal here.

  iteration::GroupResourceMap group_resources;
  if (group.loop) {
    if (group_input == nullptr) {
      throw GraphError(GraphErrorCode::missing_resource,
                       "loop region has no input image to seed global_accum",
                       owner_step->effect.id);
    }
    noisemaker::Surface accum = group_input->surface().clone();
    accum.clear();
    group_resources.store("global_accum", std::move(accum));
  }

  // renderer.js groupOwnerStateSize: a particle group's owner is its
  // pointsEmit step (the step declaring global_xyz), which an animated input
  // generator may precede (CPU 7f47340); otherwise the first step.
  const EffectStep* state_owner = owner_step;
  for (const auto index : group.step_indices) {
    const auto* candidate = std::get_if<EffectStep>(&chain.steps[index]);
    if (candidate == nullptr) continue;
    const auto& textures = plan.effects[candidate->snapshot_index].definition.textures;
    if (std::any_of(textures.begin(), textures.end(),
                    [](const auto& texture) { return texture.name == "global_xyz"; })) {
      state_owner = candidate;
      break;
    }
  }
  const auto owner_state_size = group_owner_state_size(*state_owner, group.step_indices.size());

  std::vector<GroupStepState> step_states;
  step_states.reserve(group.step_indices.size());
  for (std::size_t position = 0; position < group.step_indices.size(); ++position) {
    const auto& variant = chain.steps[group.step_indices[position]];
    const auto* step = std::get_if<EffectStep>(&variant);
    if (step == nullptr) {
      throw GraphError(GraphErrorCode::execution_failure,
                       "iterated group contains a non-effect step");
    }
    const auto& snapshot = plan.effects[step->snapshot_index];
    GroupStepState state;
    state.snapshot = &snapshot;
    state.raw_step = (step != state_owner && owner_state_size.has_value() &&
                      parameter(*step, "stateSize") != nullptr)
                         ? apply_owner_state_size_override(*step, *owner_state_size)
                         : *step;
    if (group_input_volume != nullptr && parameter(state.raw_step, "volumeSize") != nullptr) {
      try {
        const auto size = bundle::inherit_volume_size(
            step->effect.id, snapshot.definition.domain, true,
            group_input_volume->surface().width(), group_input_volume->surface().height());
        if (size.has_value()) {
          bool replaced = false;
          for (auto& binding : state.raw_step.params) {
            if (binding.name != "volumeSize") continue;
            binding.value = PlanValue::number_value(*size);
            replaced = true;
            break;
          }
          if (!replaced) state.raw_step.params.push_back({"volumeSize", PlanValue::number_value(*size)});
        }
      } catch (const std::invalid_argument& error) {
        throw GraphError(GraphErrorCode::invalid_dimension, error.what(), step->effect.id);
      }
    }
    state.effective_step = with_resolved_automation(state.raw_step, snapshot.definition, inputs.time);
    state.uses_self_tex = step_uses_self_tex(snapshot.definition);
    if (state.uses_self_tex) {
      const auto* out_texture = texture_for(snapshot.definition, "outputTex");
      std::size_t width = inputs.width;
      std::size_t height = inputs.height;
      if (out_texture != nullptr) {
        width = resolve_dimension(out_texture->width, state.effective_step, arena, inputs.width, true);
        height = resolve_dimension(out_texture->height, state.effective_step, arena, inputs.height,
                                   false);
      }
      noisemaker::Surface self_tex(width, height);
      self_tex.clear();
      state.self_tex = std::move(self_tex);
    }
    step_states.push_back(std::move(state));
  }

  const noisemaker::Surface empty_surface(1U, 1U);
  const double n = resolved.n;
  GroupIterationBundle last_bundle;

  for (std::size_t i = 0; static_cast<double>(i) < n; ++i) {
    ExecutionInputs iteration_inputs = inputs;
    iteration_inputs.frame = static_cast<std::uint32_t>(i);
    iteration_inputs.delta_time = iteration::kIterationDeltaTime;
    iteration_inputs.time = iteration::wrap01(
        inputs.time - (n - 1.0 - static_cast<double>(i)) * iteration::kIterationDeltaTime);

    GroupIterationBundle carried;
    if (group_input != nullptr) {
      carried.image = group_input->surface().clone();
      carried.image_format = group_input->format();
      carried.image_route = "inputTex";
    }
    if (group_input_volume != nullptr) {
      carried.volume = group_input_volume->surface().clone();
      carried.volume_format = group_input_volume->format();
      carried.volume_route = "inputTex3d";
      carried.volume_size = static_cast<double>(carried.volume->width());
    }
    if (group_input_geometry != nullptr) {
      carried.geometry = group_input_geometry->surface().clone();
      carried.geometry_format = group_input_geometry->format();
      carried.geometry_route = "inputGeo";
    }

    for (auto& state : step_states) {
      // renderer.js refreshIterationParams: automation re-resolves against this
      // iteration's own normalized time; other steps keep their init params.
      if (has_automation(state.raw_step)) {
        state.effective_step = with_resolved_automation(state.raw_step, state.snapshot->definition,
                                                        iteration_inputs.time);
      }
      const noisemaker::Surface* step_input = carried.image ? &*carried.image : nullptr;
      const noisemaker::Surface* step_volume = carried.volume ? &*carried.volume : nullptr;
      const noisemaker::Surface* step_geometry = carried.geometry ? &*carried.geometry : nullptr;
      auto step_result = run_group_step_iteration(state, step_input, step_volume, step_geometry,
                                                   step_states, group_resources,
                                                   arena, iteration_inputs, pass_count,
                                                   empty_surface);
      const auto& definition = state.snapshot->definition;
      GroupIterationBundle next;
      const auto select_output = [&](const std::optional<std::string>& name,
                                     std::optional<noisemaker::Surface>& incoming,
                                     noisemaker::TextureFormat incoming_format,
                                     const std::string& incoming_route,
                                     std::optional<noisemaker::Surface>& output,
                                     noisemaker::TextureFormat& output_format,
                                     std::string& output_route) {
        if (!name.has_value() || bundle::is_passthrough_output_name(*name)) {
          output = std::move(incoming);
          output_format = incoming_format;
          output_route = incoming_route;
          return;
        }
        const noisemaker::Surface* selected = group_resources.find(*name);
        if (selected == nullptr) {
          const auto found = state.resources.find(*name);
          if (found != state.resources.end()) selected = &found->second;
        }
        if (selected == nullptr) return;
        output = selected->clone();
        if (const auto* texture = texture_for(definition, *name))
          output_format = resolve_texture_format(texture->format);
        output_route = *name;
      };
      if (const auto found = state.resources.find("outputTex");
                 found != state.resources.end()) {
        next.image = std::move(step_result.surface);
        next.image_route = "outputTex";
        if (const auto* texture = texture_for(definition, "outputTex"))
          next.image_format = resolve_texture_format(texture->format);
      } else if (bundle::is_volume_domain(definition.domain)) {
        next.image = std::move(carried.image);
        next.image_format = carried.image_format;
        next.image_route = carried.image_route;
      } else {
        next.image = std::move(step_result.surface);
        next.image_format = step_result.format;
        next.image_route = std::move(step_result.output_route);
      }
      select_output(definition.output_tex3d, carried.volume, carried.volume_format,
                    carried.volume_route, next.volume, next.volume_format, next.volume_route);
      select_output(definition.output_geo, carried.geometry, carried.geometry_format,
                    carried.geometry_route, next.geometry, next.geometry_format, next.geometry_route);
      std::optional<double> step_volume_size;
      if (const auto* bound = parameter(state.effective_step, "volumeSize");
          bound != nullptr && bound->kind == PlanValue::Kind::number)
        step_volume_size = bound->number;
      next.volume_size = bundle::resolve_volume_size(
          definition.domain, step_volume_size, carried.volume_size,
          next.volume ? std::optional<std::size_t>(next.volume->width()) : std::nullopt);
      try {
        bundle::validate_volume_output_shape(
            definition.id, definition.domain, next.volume.has_value(),
            next.volume ? std::optional<std::size_t>(next.volume->width()) : std::nullopt,
            next.volume ? std::optional<std::size_t>(next.volume->height()) : std::nullopt,
            next.volume_size);
      } catch (const std::invalid_argument& error) {
        throw GraphError(GraphErrorCode::invalid_dimension, error.what(),
                         state.effective_step.effect.id);
      }
      if (!next.image.has_value() && bundle::requires_output_image(definition.domain))
        throw GraphError(GraphErrorCode::invalid_dimension,
                         "iterated step did not produce outputTex",
                         state.effective_step.effect.id);
      carried = std::move(next);
    }
    last_bundle = std::move(carried);
  }

  if (!last_bundle.image && !last_bundle.volume && !last_bundle.geometry) {
    throw GraphError(GraphErrorCode::execution_failure, "iterated group produced no output",
                     owner_step->effect.id);
  }
  GroupPublishResult result;
  if (last_bundle.image.has_value()) {
    result.surface = std::move(*last_bundle.image);
    result.has_image = true;
    result.format = last_bundle.image_format;
    result.route = std::move(last_bundle.image_route);
  }
  result.volume = std::move(last_bundle.volume);
  result.geometry = std::move(last_bundle.geometry);
  result.volume_format = last_bundle.volume_format;
  result.geometry_format = last_bundle.geometry_format;
  result.volume_route = std::move(last_bundle.volume_route);
  result.geometry_route = std::move(last_bundle.geometry_route);
  result.volume_size = last_bundle.volume_size;
  return result;
}

}  // namespace

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
      // The authority always wraps an externally supplied texture with
      // `filter: 'linear'` before binding it (src/runtime/renderer.js,
      // `canonicalTextures()`: `if (definition.externalTexture) { ... filter:
      // 'linear' }`), regardless of what the caller passed in. Any pass that
      // samples it through the generic `texture()`/`textureSize()` builtins
      // (`sample_texture` in the typed emitter) therefore interpolates --
      // e.g. filter/text's `textTex` -- even though a caller-supplied Surface
      // otherwise defaults to nearest. synth/media's `imageTex` is unaffected
      // in practice: its kernel samples it only through `texelFetch`, which
      // never consults the filter. Force the filter here, once, so every
      // effect that binds an external texture gets the authority's sampling
      // mode regardless of how the caller built the source Surface.
      noisemaker::Surface filtered = input.surface.clone();
      filtered.set_filter(noisemaker::TextureFilter::linear);
      arena.copy(input.name, filtered, TextureFormat::rgba32f,
                 ResourceLifetime::external);
    } catch (const std::overflow_error&) {
      throw GraphError(GraphErrorCode::allocation_limit,
                       "external texture copy exceeds allocation limit");
    } catch (const std::exception&) {
      throw GraphError(GraphErrorCode::execution_failure,
                       "external texture copy failed");
    }
  }

  if (std::any_of(plan.effects.begin(), plan.effects.end(),
      [](const auto& snapshot) { return snapshot.definition.id == "synth/roll"; })) {
    noisemaker::Surface grid(128U, 16U);
    grid.set_filter(noisemaker::TextureFilter::nearest);
    if (inputs.midi_state) {
      constexpr std::size_t row_lanes = 128U * 4U;
      for (std::size_t row = 0; row < 16U; ++row) {
        std::copy_n(inputs.midi_state->note_grid.data() + (15U - row) * row_lanes,
                    row_lanes, grid.data().data() + row * row_lanes);
      }
    }
    arena.copy("midiNoteGrid", grid, TextureFormat::rgba32f, ResourceLifetime::external);
  }

  // Only meshLoader samples uploaded mesh textures. meshRender's whole-pass
  // adapter consumes the same validated external data directly.
  if (std::any_of(plan.effects.begin(), plan.effects.end(),
          [](const auto& snapshot) { return snapshot.definition.id == "render/meshLoader"; })) {
    const auto& mesh = bound_mesh_data(inputs);
    const auto bind_mesh_texture = [&](const char* name, const std::vector<float>& packed) {
      noisemaker::Surface surface(mesh.tex_width, mesh.tex_height);
      surface.set_filter(noisemaker::TextureFilter::nearest);
      const auto row_lanes = mesh.tex_width * 4U;
      for (std::size_t row = 0; row < mesh.tex_height; ++row) {
        const auto source = (mesh.tex_height - 1U - row) * row_lanes;
        if (source < packed.size()) {
          std::copy_n(packed.data() + source, std::min(row_lanes, packed.size() - source),
                      surface.data().data() + row * row_lanes);
        }
      }
      arena.copy(name, surface, TextureFormat::rgba32f, ResourceLifetime::external);
    };
    bind_mesh_texture("global_mesh0_positions", mesh.position_data);
    bind_mesh_texture("global_mesh0_normals", mesh.normal_data);
  }

  std::size_t pass_count = 0;
  std::size_t chain_argument_holds = 0;
  // renderer.js runChainSync: runs one chain and returns its final image. A
  // step's chain arguments run first, before the step's iteration group, and
  // each publishes its image under the hidden surface the step binds.
  std::function<GraphResource*(const ExecutionChain&)> run_chain;
  run_chain = [&](const ExecutionChain& chain) -> GraphResource* {
    // The authority starts each chain with an empty bundle. Named image
    // surfaces remain in the arena, but unnamed bundle state is chain-local.
    GraphResource* current = nullptr;
    GraphResource* current_volume = nullptr;
    GraphResource* current_geometry = nullptr;
    std::optional<double> current_volume_size;
    // The CPU authority partitions the chain into iteration groups. Each
    // iterated group shares its scratch resources across the requested ticks.
    for (const auto& group : iteration::compute_iteration_groups(plan, chain)) {
      bool has_chain_arguments = false;
      for (const auto index : group.step_indices) {
        if (const auto* effect = std::get_if<EffectStep>(&chain.steps[index])) {
          has_chain_arguments = has_chain_arguments || !effect->inline_chains.empty();
        }
      }
      if (has_chain_arguments) {
        // A chain argument publishes over the same routes as this chain, so
        // this chain's bundle is held under private aliases while they run.
        const auto hold = [&](GraphResource*& resource) {
          if (resource == nullptr) return;
          const std::string name = "\x01chain-argument-hold:" + std::to_string(chain_argument_holds++);
          arena.alias(name, *resource);
          resource = arena.find(name);
        };
        hold(current);
        hold(current_volume);
        hold(current_geometry);
        for (const auto index : group.step_indices) {
          const auto* effect = std::get_if<EffectStep>(&chain.steps[index]);
          if (effect == nullptr) continue;
          for (const auto& argument : effect->inline_chains) {
            GraphResource* const image = run_chain(argument.chain);
            if (image == nullptr) throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
            arena.alias(argument.surface, *image);
          }
        }
      }
      if (group.iterated) {
        const auto* owner = std::get_if<EffectStep>(&chain.steps[group.step_indices.front()]);
        const auto& owner_definition = plan.effects[owner->snapshot_index].definition;
        auto group_result = run_iterated_group(plan, chain, group, current, current_volume,
                                               current_geometry, arena, inputs, pass_count);
        if (group_result.has_image && group_result.route != "inputTex") {
          current = &arena.insert(group_result.route, std::move(group_result.surface),
                                  group_result.format, ResourceLifetime::transient);
        } else if (!group_result.has_image) {
          current = nullptr;
        }
        const auto publish_bundle_resource = [&](std::optional<noisemaker::Surface>& surface,
                                                 const std::string& route,
                                                 TextureFormat format) -> GraphResource* {
          if (!surface.has_value()) return nullptr;
          if (bundle::is_passthrough_output_name(route))
            return route == "inputGeo" ? current_geometry : current_volume;
          return &arena.insert(route, std::move(*surface), format, ResourceLifetime::transient);
        };
        GraphResource* const volume = publish_bundle_resource(
            group_result.volume, group_result.volume_route, group_result.volume_format);
        GraphResource* const geometry = publish_bundle_resource(
            group_result.geometry, group_result.geometry_route, group_result.geometry_format);
        const auto size = group_result.volume_size.has_value()
            ? group_result.volume_size
            : bundle::resolve_volume_size(
                  owner_definition.domain, std::nullopt, current_volume_size,
                  volume == nullptr ? std::nullopt
                                    : std::optional<std::size_t>(volume->surface().width()));
        try {
          bundle::validate_volume_output_shape(
              owner_definition.id, owner_definition.domain, volume != nullptr,
              volume == nullptr ? std::nullopt
                                : std::optional<std::size_t>(volume->surface().width()),
              volume == nullptr ? std::nullopt
                                : std::optional<std::size_t>(volume->surface().height()), size);
        } catch (const std::invalid_argument& error) {
          throw GraphError(GraphErrorCode::invalid_dimension, error.what(), owner_definition.id);
        }
        current_volume = volume;
        current_geometry = geometry;
        current_volume_size = volume == nullptr ? std::nullopt : size;
        continue;
      }
      const auto& variant = chain.steps[group.step_indices.front()];
      if (const auto* read = std::get_if<ReadStep>(&variant)) {
        if (read->surface.kind != SurfaceReference::Kind::named || arena.find(read->surface.name) == nullptr) {
          throw GraphError(GraphErrorCode::missing_resource, "named read surface is missing", {}, 0, {}, read->surface.name);
        }
        current = arena.find(read->surface.name);
        current_volume = nullptr;
        current_geometry = nullptr;
        current_volume_size.reset();
      } else if (const auto* write = std::get_if<WriteStep>(&variant)) {
        if (current == nullptr || write->surface.kind != SurfaceReference::Kind::named) {
          throw GraphError(GraphErrorCode::missing_resource, "write has no current image");
        }
        arena.alias(write->surface.name, *current);
      } else if (const auto* write3d = std::get_if<Write3DStep>(&variant)) {
        // write3d stores the current bundle's volume and geometry under its
        // two names (`none` stores nothing) and passes the chain through.
        if (write3d->volume != "none" && current_volume != nullptr) arena.alias(write3d->volume, *current_volume);
        if (write3d->geometry != "none" && current_geometry != nullptr) arena.alias(write3d->geometry, *current_geometry);
      } else if (const auto* read3d = std::get_if<Read3DStep>(&variant)) {
        // read3d starts a chain bundle from a stored volume and geometry.
        GraphResource* const volume = arena.find(read3d->volume);
        if (volume == nullptr) {
          throw GraphError(GraphErrorCode::missing_resource, "Surface " + read3d->volume + " has not been written", {}, 0, {}, read3d->volume);
        }
        current = nullptr;
        current_volume = volume;
        current_geometry = arena.find(read3d->geometry);
        current_volume_size = static_cast<double>(volume->surface().width());
      } else {
        // renderer.js:1214 -- inheritVolumeSize runs before effectParams, so
        // a modified "volumeSize" binding is visible everywhere downstream
        // (dimension resolution, uniform resolution, ...). `effective_step`
        // is a value copy, mutated once here if the override applies, then
        // `step` is bound to it for the rest of this block -- every
        // existing line below that reads `step` needs no change at all.
        EffectStep effective_step = std::get<EffectStep>(variant);
        const auto& snapshot = plan.effects[effective_step.snapshot_index];
        GraphResource* const input_volume = current_volume;
        GraphResource* const input_geometry = current_geometry;
        const std::optional<double> input_volume_size = current_volume_size;
        if (input_volume != nullptr) {
          const auto& volume_surface = input_volume->surface();
          const bool declares_volume_size = parameter(effective_step, "volumeSize") != nullptr;
          try {
            const auto override_size = bundle::inherit_volume_size(
                effective_step.effect.id, snapshot.definition.domain, declares_volume_size,
                volume_surface.width(), volume_surface.height());
            if (override_size.has_value()) {
              bool replaced = false;
              for (auto& binding : effective_step.params) {
                if (binding.name == "volumeSize") {
                  binding.value = PlanValue::number_value(*override_size);
                  replaced = true;
                  break;
                }
              }
              if (!replaced) {
                effective_step.params.push_back({"volumeSize", PlanValue::number_value(*override_size)});
              }
            }
          } catch (const std::invalid_argument& error) {
            throw GraphError(GraphErrorCode::invalid_dimension, error.what(), effective_step.effect.id);
          }
        }
        // renderer.js effectParams -> resolveEffectAutomation, after
        // inheritVolumeSize: `osc(...)` parameters read this render's time.
        effective_step = with_resolved_automation(effective_step, snapshot.definition, inputs.time);
        const auto& step = effective_step;
        GraphResource* effect_output = current;
        bool effect_wrote_output_tex = false;
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
        // unproduced texture and consumed underscore-prefixed feedback texture,
        // at its declared extent and format, before the first pass runs.
        const auto declared_textures = initialized_declared_textures(snapshot.definition);
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
            // renderCanonicalWormOverlay(definition.id, renderOptions.width,
            // renderOptions.height, params) -- the authority uses the raw
            // render extent directly, never `canonicalDestination`'s
            // pass/texture-formula resolution (which this effect's declared
            // `overlayTex` happens to resolve to the same value for anyway,
            // since it is declared at `width: "screen", height: "screen"`).
            // `density` is this effect instance's own bound parameter
            // (params.density); a missing binding passes through as the
            // JS-falsy sentinel 0.0, matching `params.density` on an unbound
            // (`undefined`) parameter.
            //
            // `seed` is NOT simply the effect's own parameter: the
            // authority's `effectParams()` (renderer.js:313-315) substitutes
            // the render-level seed whenever the step declares a `seed`
            // parameter that the DSL call did not name explicitly --
            // `!Object.hasOwn(step.params,'seed') || step.explicitParams.
            // includes('seed')` keeps the step's own value; otherwise
            // `{...step.params, seed: renderOptions.seed}`. This is the same
            // substitution `bound_uniform_value()` above applies to ordinary
            // pass uniforms sourced from `effect_parameter:seed`, applied
            // here too since this resource is materialized outside that
            // uniform-binding path.
            const auto* seed_param = parameter(step, "seed");
            const auto* density_param = parameter(step, "density");
            const bool seed_explicit =
                std::find(step.explicit_params.begin(), step.explicit_params.end(), "seed") !=
                step.explicit_params.end();
            double seed_value = 0.0;
            if (seed_param != nullptr && seed_param->kind == PlanValue::Kind::number) {
              seed_value = seed_explicit ? seed_param->number : inputs.seed;
            }
            const double density_value =
                (density_param != nullptr && density_param->kind == PlanValue::Kind::number)
                    ? density_param->number
                    : 0.0;
            noisemaker::Surface overlay = effects::cpu::render_canonical_worm_overlay(
                snapshot.definition.id, inputs.width, inputs.height, seed_value, density_value);
            arena.insert(texture.name, std::move(overlay),
                         resolve_texture_format(texture.format),
                         ResourceLifetime::declared);
            continue;
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
          // renderer.js:1217-1219 -- inputTex3d/inputGeo, seeded into the
          // resource map alongside inputTex. Never true for an image-domain
          // effect, since input_volume/input_geometry stay null the whole
          // life of an all-image chain.
          if (route == "inputTex3d") return owned(input_volume);
          if (route == "inputGeo") return owned(input_geometry);
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
            if (direct_mesh_resource(admission, sampler.resource)) continue;
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
          bool wrote_output_tex = false;
          try {
            if (admission.outputs.size() > 1U) {
              // MRT (drawBuffers >= 2): resolve every declared output's own
              // destination texture spec independently and require they
              // share dimensions BEFORE binding a kernel or allocating any
              // Surface -- the direct analog of the JS authority's
              // canonicalMrtDestinations/assertMrtDestinationsShareDimensions
              // (renderer.js:519-533), which run before its shared pixel
              // loop, not inside it (run_mrt_pass mirrors that split too;
              // see pass_runner.hpp).
              struct MrtDestination { std::string route; TextureFormat format; };
              std::vector<MrtDestination> destinations;
              destinations.reserve(pass.outputs.size());
              std::size_t mrt_width = inputs.width;
              std::size_t mrt_height = inputs.height;
              for (std::size_t slot = 0; slot < pass.outputs.size(); ++slot) {
                const std::string& route = pass.outputs[slot].second;
                const auto* texture = texture_for(snapshot.definition, route);
                const auto lookup = [&](std::string_view name) { return resolve_route(name).surface; };
                const auto width = destination_dimension(pass, texture, step, arena, inputs.width, true, lookup);
                const auto height = destination_dimension(pass, texture, step, arena, inputs.height, false, lookup);
                TextureFormat format = TextureFormat::rgba16f;
                if (texture != nullptr) {
                  try {
                    format = resolve_texture_format(texture->format);
                  } catch (const std::invalid_argument& error) {
                    throw GraphError(GraphErrorCode::invalid_format, error.what(),
                                     step.effect.id, pass_index, pass.name,
                                     admission.identity.program_key);
                  }
                }
                if (format != resolve_texture_format(admission.output_extent.format)) {
                  throw GraphError(GraphErrorCode::invalid_format,
                                   "destination format differs from the authenticated output extent",
                                   step.effect.id, pass_index, pass.name,
                                   admission.identity.program_key);
                }
                if (slot == 0U) {
                  mrt_width = width;
                  mrt_height = height;
                } else if (width != mrt_width || height != mrt_height) {
                  throw GraphError(GraphErrorCode::unsupported_mrt,
                                   "MRT destinations must share dimensions",
                                   step.effect.id, pass_index, pass.name,
                                   admission.identity.program_key);
                }
                destinations.push_back({route, format});
              }
              // CPU 7f47340: the canvas size binds as `resolution`; the pixel
              // loop still covers the MRT destinations.
              const BindingMaterializationContext binding_context{
                  &inputs, &snapshot.definition, inputs.width, inputs.height,
                  &lookup_resolved_sampler_route, &resolved};
              preflight_pass_abi(step, admission, pass, binding_context);
              auto bindings = materialize_uniform_bindings(step, admission, pass,
                                                           binding_context);
              materialize_sampler_bindings(bindings, admission, binding_context,
                                           step, pass);
              apply_classic_noisedeck_palette_override(bindings, step,
                                                       snapshot.definition);
              auto kernel = bind_factory_route_mrt(step, admission, snapshot.definition,
                                                   bindings);
              // Render and quantize off-route, exactly like the
              // single-output path: a failed factory or kernel must never
              // publish a partially initialized destination.
              auto rendered = noisemaker::run_mrt_pass(
                  kernel, mrt_width, mrt_height, noisemaker::f32(inputs.time),
                  noisemaker::f32(inputs.seed), inputs.frame,
                  noisemaker::f32(inputs.delta_time));
              for (std::size_t slot = 0; slot < destinations.size(); ++slot) {
                noisemaker::quantize_texture(rendered[slot], destinations[slot].format);
                auto& destination = arena.insert(destinations[slot].route,
                                                 std::move(rendered[slot]),
                                                 destinations[slot].format,
                                                 ResourceLifetime::transient);
                effect_output = &destination;
                if (destinations[slot].route == "outputTex") wrote_output_tex = true;
              }
              ++pass_count;
            } else {
            const auto* texture = texture_for(snapshot.definition, output_route);
            const auto lookup = [&](std::string_view name) { return resolve_route(name).surface; };
            const auto width = destination_dimension(pass, texture, step, arena, inputs.width, true, lookup);
            const auto height = destination_dimension(pass, texture, step, arena, inputs.height, false, lookup);
            TextureFormat format = TextureFormat::rgba16f;
            if (texture != nullptr) {
              try {
                format = resolve_texture_format(texture->format);
              } catch (const std::invalid_argument& error) {
                throw GraphError(GraphErrorCode::invalid_format, error.what(),
                                 step.effect.id, pass_index, pass.name,
                                 admission.identity.program_key);
              }
            }
            const bool dispatch_scatter = scatter_adapter_available(admission);
            // The destination quantization must be the authenticated output
            // extent's format; a forged texture format would otherwise change
            // the quantization of every published byte. A scatter admission
            // carries no `output_extent` at all (see registry.cpp's
            // `admission()` early return) -- its destination format is
            // simply whatever the effect's own declared texture says, the
            // same source `format` above was already resolved from.
            if (!dispatch_scatter &&
                format != resolve_texture_format(admission.output_extent.format)) {
              throw GraphError(GraphErrorCode::invalid_format,
                               "destination format differs from the authenticated output extent",
                               step.effect.id, pass_index, pass.name,
                               admission.identity.program_key);
            }
            const BindingMaterializationContext binding_context{
                &inputs, &snapshot.definition, width, height,
                &lookup_resolved_sampler_route, &resolved};
            preflight_pass_abi(step, admission, pass, binding_context);
            if (dispatch_scatter) {
              // Mirrors the JS scatter call sites (renderer.js:963-965 and
              // its three siblings): resolve the adapter's one input route
              // exactly like an ordinary sampler (retained for the
              // dispatch's lifetime), build its small scalar `Bindings`
              // (buildScatterBindings), pre-seed the destination with the
              // previous contents of the named output texture -- or a
              // cleared surface if this is its first write, matching
              // `destination_mutation == "in_place_accumulate"` -- run the
              // adapter IN PLACE, then quantize/store exactly like any
              // other pass.
              // JS canonicalTextures (renderer.js:1331): every declared pass
              // input resolves under its own declared uniform name -- the
              // contract's `input_texture` is a variable NAME (xyzTex);
              // resolving it as a route instead of the declared input's
              // route (global_xyz) was the particle-family dispatch bug.
              std::vector<std::pair<std::string, const noisemaker::Surface*>> scatter_inputs;
              scatter_inputs.reserve(pass.inputs.size());
              for (const auto& input : pass.inputs) {
                const auto input_route = resolve_route(input.second);
                if (input_route.surface == nullptr) {
                  release_borrowed();
                  throw GraphError(GraphErrorCode::read_before_write,
                                   "input resource is not produced", step.effect.id,
                                   pass_index, pass.name,
                                   admission.identity.program_key);
                }
                if (input_route.resource != nullptr &&
                    std::find(borrowed.begin(), borrowed.end(), input_route.resource) == borrowed.end()) {
                  arena.retain(*input_route.resource);
                  borrowed.push_back(input_route.resource);
                }
                scatter_inputs.push_back({input.first, input_route.surface});
              }
              auto bindings = materialize_scatter_bindings(
                  step, admission, snapshot.definition, pass, scatter_inputs);
              const noisemaker::scatter::ScatterAdapter adapter =
                  noisemaker::scatter::resolve_scatter_adapter(admission.identity.program_key);
              if (adapter == nullptr) {
                // Unreachable: `dispatch_scatter` already proved this
                // resolves. Guarded anyway so a future change to either
                // side of that proof fails loud here rather than
                // dereferencing a null function pointer.
                throw GraphError(GraphErrorCode::unsupported_scatter,
                                 "no scatter adapter is registered for this program",
                                 step.effect.id, pass_index, pass.name,
                                 admission.identity.program_key);
              }
              const auto* const existing = arena.find(output_route);
              noisemaker::Surface destination =
                  existing != nullptr ? existing->surface().clone()
                                      : noisemaker::Surface(width, height);
              const noisemaker::scatter::ScatterPass scatter_pass = scatter_pass_from_definition(pass, format);
              adapter(bindings, scatter_pass, destination);
              noisemaker::quantize_texture(destination, format);
              auto& stored = arena.insert(output_route, std::move(destination),
                                          format, ResourceLifetime::transient);
              effect_output = &stored;
              wrote_output_tex = output_route == "outputTex";
              ++pass_count;
            } else {
            auto bindings = materialize_uniform_bindings(step, admission, pass,
                                                         binding_context);
            materialize_sampler_bindings(bindings, admission, binding_context,
                                         step, pass);
            apply_classic_noisedeck_palette_override(bindings, step,
                                                     snapshot.definition);
            // Render and quantize off-route.  A failed factory or kernel must
            // never publish a partially initialized destination into the
            // arena, so route replacement is one atomic insert after all work
            // has completed successfully.
            auto rendered = [&]() -> noisemaker::Surface {
            if (mesh_adapter_available(admission)) {
              (void)authenticate_factory_route(step, admission);
              noisemaker::Surface destination(width, height);
              const auto* previous = arena.find(output_route);
              if (previous != nullptr && previous->surface().data().size() == destination.data().size()) {
                std::copy(previous->surface().data().begin(), previous->surface().data().end(), destination.data().begin());
              } else {
                destination.clear();
              }
              (void)effects::render_triangles(bound_mesh_data(inputs), bindings, destination);
              return destination;
            }
            auto kernel = bind_factory_route(step, admission, snapshot.definition, bindings);
            return noisemaker::run_pass(kernel, width, height,
                                                 noisemaker::f32(inputs.time),
                                                 noisemaker::f32(inputs.seed), inputs.frame,
                                                 noisemaker::f32(inputs.delta_time));
            }();
            noisemaker::quantize_texture(rendered, format);
            auto& destination = arena.insert(output_route, std::move(rendered),
                                              format, ResourceLifetime::transient);
            effect_output = &destination;
            wrote_output_tex = output_route == "outputTex";
            ++pass_count;
            }
            }
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
          if (wrote_output_tex) effect_wrote_output_tex = true;
          }
        }
        // renderer.js:1317-1341 (identically at 1053-1067/1187-1201/1471-
        // 1489, folded here into the one structural site this port's
        // non-iterated path has): image is unchanged (`effect_output`,
        // exactly as before this task -- this port's own "last pass wins"
        // simplification of `bundleOutput(outputTex, ...)` is untouched);
        // volume/geometry resolve via bundle_output's passthrough-name
        // check, falling through to a real arena lookup only for a
        // genuinely declared, non-passthrough route name -- never true for
        // an image-domain effect, since it declares neither.
        const auto resolve_bundle_output =
            [&](const std::optional<std::string>& name, GraphResource* input) -> GraphResource* {
          if (!name.has_value() || bundle::is_passthrough_output_name(*name)) return input;
          return arena.find(*name);
        };
        GraphResource* const volume =
            resolve_bundle_output(snapshot.definition.output_tex3d, input_volume);
        GraphResource* const geometry =
            resolve_bundle_output(snapshot.definition.output_geo, input_geometry);
        const std::optional<std::size_t> produced_volume_width =
            volume != nullptr ? std::optional<std::size_t>(volume->surface().width()) : std::nullopt;
        const std::optional<std::size_t> produced_volume_height =
            volume != nullptr ? std::optional<std::size_t>(volume->surface().height()) : std::nullopt;
        std::optional<double> step_params_volume_size;
        if (const auto* bound = parameter(step, "volumeSize");
            bound != nullptr && bound->kind == PlanValue::Kind::number) {
          step_params_volume_size = bound->number;
        }
        const auto volume_size = bundle::resolve_volume_size(
            snapshot.definition.domain, step_params_volume_size, input_volume_size,
            produced_volume_width);
        try {
          bundle::validate_volume_output_shape(step.effect.id, snapshot.definition.domain,
                                               volume != nullptr, produced_volume_width,
                                               produced_volume_height, volume_size);
          if ((effect_wrote_output_tex ? arena.find("outputTex") :
               bundle::is_volume_domain(snapshot.definition.domain) ? effect_input : effect_output)
                  == nullptr && bundle::requires_output_image(snapshot.definition.domain)) {
            throw std::invalid_argument(std::string(step.effect.id) + " did not produce outputTex");
          }
        } catch (const std::invalid_argument& error) {
          throw GraphError(GraphErrorCode::invalid_dimension, error.what(), step.effect.id);
        }
        // JS selects the named outputTex resource before the last MRT slot.
        // A volume producer with no image output retains the input image.
        current = effect_wrote_output_tex ? arena.find("outputTex") :
            bundle::is_volume_domain(snapshot.definition.domain) ? effect_input : effect_output;
        current_volume = volume;
        current_geometry = geometry;
        current_volume_size = volume_size;
      }
    }
    return current;
  };
  for (const auto& chain : plan.chains) static_cast<void>(run_chain(chain));
  if (arena.find(plan.render_surface.name) == nullptr) {
    throw GraphError(GraphErrorCode::missing_resource, "render surface was not published", {}, 0, {}, plan.render_surface.name);
  }
  const auto& final = arena.require(plan.render_surface.name);
  return {final.surface().clone(), std::string(plan.render_surface.name), pass_count};
}

}  // namespace noisemaker::graph
