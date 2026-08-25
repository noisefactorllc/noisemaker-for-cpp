#include "noisemaker/dsl/compiler.hpp"
#include "noisemaker/effects/catalog.hpp"

#include "test_harness.hpp"

#include <variant>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <charconv>
#include <limits>

namespace {
noisemaker::effects::EffectDefinition effect(std::string name, std::string kind = "generator") {
  noisemaker::effects::EffectDefinition result;
  result.id = "fixture/" + name;
  result.name_space = "fixture";
  result.function = std::move(name);
  result.kind = std::move(kind);
  result.domain = "image";
  noisemaker::effects::PassDefinition pass;
  pass.name = "main";
  pass.program = result.function;
  result.passes.push_back(std::move(pass));
  return result;
}
}

TEST(dsl_compiler_builds_owned_generator_read_write_plan) {
  noisemaker::effects::EffectRegistry registry({effect("source")});
  const auto plan = noisemaker::dsl::compile("search fixture\nsource().write(o2)\n", registry);
  REQUIRE(plan.search.size() == 1);
  REQUIRE(plan.chains.size() == 1);
  REQUIRE(plan.chains[0].steps.size() == 2);
  REQUIRE(std::holds_alternative<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]));
  REQUIRE(plan.render_surface.name == "o2");
  REQUIRE(plan.executable);
}

TEST(dsl_compiler_rejects_generator_without_final_write) {
  noisemaker::effects::EffectRegistry registry({effect("source")});
  REQUIRE_THROWS_AS(noisemaker::dsl::compile("search fixture\nsource()\n", registry), noisemaker::dsl::DslError);
}

TEST(dsl_compiler_fails_closed_for_missing_compatibility) {
  auto source = effect("source");
  noisemaker::effects::EffectCatalog catalog;
  catalog.definitions.push_back(source);
  noisemaker::effects::ProgramCompatibility row;
  row.program_key = "fixture/source:source";
  row.status = "missing";
  row.reasons.push_back({"missing_backend_program", row.program_key});
  noisemaker::effects::ReferencePassCompatibility reference;
  reference.effect_id = source.id;
  reference.pass_index = 0;
  reference.pass_name = "main";
  reference.program_key = row.program_key;
  reference.status = "missing";
  reference.reasons = row.reasons;
  catalog.reference_passes.push_back(reference);
  noisemaker::effects::EffectRegistry registry(catalog);
  const auto inspected = noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry);
  REQUIRE(!inspected.executable);
  REQUIRE(inspected.availability.size() == 1);
  REQUIRE_THROWS_AS(noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry,
                                               {.require_executable = true}), noisemaker::dsl::DslError);
}

TEST(dsl_compiler_accepts_real_catalog_generator_and_multipass_filter) {
  noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto solid = noisemaker::dsl::compile(
      "search synth, filter\nsolid(color: #3a7).write(o0)\nrender(o0)\n", registry);
  REQUIRE(solid.executable);
  REQUIRE(solid.availability.size() == 1);
  const auto blur = noisemaker::dsl::compile(
      "search synth, filter\nsolid().blur(radiusX: 3, radiusY: 2).write(o0)\nrender(o0)\n", registry);
  REQUIRE(blur.executable);
  REQUIRE(blur.availability.size() == 3);
}

TEST(dsl_compiler_merges_named_partials_in_stable_key_order) {
  auto source = effect("source");
  noisemaker::effects::ParameterDefinition first;
  first.name = "first";
  first.type = "int";
  first.default_value = noisemaker::effects::Value::number_value(1.0);
  source.parameters.push_back(first);
  noisemaker::effects::ParameterDefinition second;
  second.name = "second";
  second.type = "int";
  second.default_value = noisemaker::effects::Value::number_value(2.0);
  source.parameters.push_back(second);
  noisemaker::effects::EffectRegistry registry({source});
  const auto plan = noisemaker::dsl::compile(
      "search fixture\nlet p = source(first: 3, second: 4)\np(second: 7).write(o0)\n", registry);
  const auto& step = std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]);
  REQUIRE(step.params[0].name == "first");
  REQUIRE(step.params[0].value.number == 3.0);
  REQUIRE(step.params[1].value.number == 7.0);
}

TEST(dsl_compiler_preserves_scatter_and_rejects_source_incompatible_text) {
  noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto scatter = noisemaker::dsl::compile(
      "search filter\nread(o0).wormhole().write(o1)\nrender(o1)\n", registry);
  REQUIRE(scatter.executable);
  bool saw_scatter = false;
  for (const auto& pass : scatter.availability) saw_scatter |= pass.status == noisemaker::graph::AvailabilityStatus::scatter;
  REQUIRE(saw_scatter);
  const auto text = noisemaker::dsl::compile(
      "search filter\nread(o0).text().write(o1)\nrender(o1)\n", registry);
  REQUIRE(!text.executable);
  REQUIRE_THROWS_AS(noisemaker::dsl::compile(
      "search filter\nread(o0).text().write(o1)\nrender(o1)\n", registry,
      {.require_executable = true}), noisemaker::dsl::DslError);
}

TEST(dsl_compiler_plan_copy_owns_nested_parameter_arrays) {
  auto source = effect("source");
  noisemaker::effects::ParameterDefinition vector;
  vector.name = "vector";
  vector.type = "vec3";
  vector.default_value = noisemaker::effects::Value::array_value({
      noisemaker::effects::Value::number_value(1.0),
      noisemaker::effects::Value::number_value(2.0),
      noisemaker::effects::Value::number_value(3.0)});
  source.parameters.push_back(vector);
  noisemaker::effects::EffectRegistry registry({source});
  auto original = noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry);
  auto copied = original;
  auto& copied_step = std::get<noisemaker::graph::EffectStep>(copied.chains[0].steps[0]);
  copied_step.params[0].value.array[0].number = 99.0;
  const auto& original_step = std::get<noisemaker::graph::EffectStep>(original.chains[0].steps[0]);
  REQUIRE(original_step.params[0].value.array[0].number == 1.0);
}

#ifdef NOISEMAKER_DSL_COMPILER_ORACLE_MAIN
namespace {
std::string oracle_escape(const std::string& value) {
  std::ostringstream out;
  out << '"';
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char byte : value) {
    if (byte == '"') out << "\\\"";
    else if (byte == '\\') out << "\\\\";
    else if (byte == '\n') out << "\\n";
    else if (byte == '\r') out << "\\r";
    else if (byte == '\t') out << "\\t";
    else if (byte < 0x20) out << "\\u00" << hex[(byte >> 4) & 0xf] << hex[byte & 0xf];
    else out << byte;
  }
  out << '"';
  return out.str();
}

std::string oracle_number(double value) {
  if (std::isnan(value)) return "number:NaN";
  if (std::isinf(value)) return value < 0 ? "number:-Infinity" : "number:+Infinity";
  if (value == 0.0 && std::signbit(value)) return "number:-0";
  char buffer[64]{};
  const auto result = std::to_chars(std::begin(buffer), std::end(buffer), value,
                                    std::chars_format::general);
  return std::string("number:") + (result.ec == std::errc{} ? std::string(buffer, result.ptr) : std::to_string(value));
}

std::string oracle_loc(const noisemaker::dsl::SourceLocation& location) {
  return "{\"sourceName\":" + oracle_escape(location.source_name) + ",\"line\":" +
         std::to_string(location.line) + ",\"column\":" + std::to_string(location.column) +
         ",\"index\":" + std::to_string(location.index) + "}";
}

std::string oracle_value(const noisemaker::graph::PlanValue& value) {
  using Kind = noisemaker::graph::PlanValue::Kind;
  if (value.kind == Kind::null_value) return "{\"kind\":\"null\"}";
  if (value.kind == Kind::boolean) return "{\"kind\":\"boolean\",\"value\":" + std::string(value.boolean ? "true" : "false") + "}";
  if (value.kind == Kind::number) return "{\"kind\":\"number\",\"value\":" + oracle_escape(oracle_number(value.number)) + "}";
  if (value.kind == Kind::string) return "{\"kind\":\"string\",\"value\":" + oracle_escape(value.string) + "}";
  if (value.kind == Kind::array) {
    std::string result = "{\"kind\":\"array\",\"values\":[";
    for (std::size_t index = 0; index < value.array.size(); ++index) { if (index) result += ','; result += oracle_value(value.array[index]); }
    return result + "]}";
  }
  if (value.surface.kind == noisemaker::graph::SurfaceReference::Kind::input) return "{\"kind\":\"surface\",\"value\":{\"kind\":\"input\"}}";
  if (value.surface.kind == noisemaker::graph::SurfaceReference::Kind::named) {
    return "{\"kind\":\"surface\",\"value\":{\"kind\":\"named\",\"name\":" + oracle_escape(value.surface.name) + ",\"index\":" + std::to_string(value.surface.index) + "}}";
  }
  return "{\"kind\":\"surface\",\"value\":{\"kind\":\"none\"}}";
}

std::string oracle_status(noisemaker::graph::AvailabilityStatus status) {
  using S = noisemaker::graph::AvailabilityStatus;
  if (status == S::compatible) return "compatible";
  if (status == S::scatter) return "scatter";
  if (status == S::incompatible) return "incompatible";
  return "missing";
}

std::string oracle_admission(const noisemaker::graph::PassAdmission& admission) {
  std::string result = "{\"index\":" + std::to_string(admission.identity.index) + ",\"name\":" + oracle_escape(admission.identity.name) +
                       ",\"programKey\":" + oracle_escape(admission.identity.program_key) + ",\"status\":" + oracle_escape(oracle_status(admission.status)) + ",\"reasons\":[";
  for (std::size_t index = 0; index < admission.reasons.size(); ++index) {
    if (index) result += ',';
    result += "{\"code\":" + oracle_escape(admission.reasons[index].code) + ",\"detail\":" + oracle_escape(admission.reasons[index].detail) + "}";
  }
  return result + "]}";
}

std::string oracle_surface(const noisemaker::graph::SurfaceReference& surface) {
  return surface.kind == noisemaker::graph::SurfaceReference::Kind::named ? oracle_escape(surface.name) : "null";
}

std::string oracle_step(const noisemaker::graph::CompiledStep& step) {
  return std::visit([](const auto& current) -> std::string {
    using T = std::decay_t<decltype(current)>;
    if constexpr (std::is_same_v<T, noisemaker::graph::ReadStep>) {
      return "{\"kind\":\"read\",\"surface\":" + oracle_surface(current.surface) + ",\"loc\":" + oracle_loc(current.loc) + "}";
    } else if constexpr (std::is_same_v<T, noisemaker::graph::WriteStep>) {
      return "{\"kind\":\"write\",\"surface\":" + oracle_surface(current.surface) + ",\"loc\":" + oracle_loc(current.loc) + "}";
    } else {
      std::string result = "{\"kind\":\"effect\",\"effectId\":" + oracle_escape(current.effect.id) + ",\"domain\":" + oracle_escape(current.effect.domain) +",\"effectKind\":" + oracle_escape(current.effect.kind) + ",\"params\":[";
      for (std::size_t index = 0; index < current.params.size(); ++index) { if (index) result += ','; result += "{\"name\":" + oracle_escape(current.params[index].name) + ",\"value\":" + oracle_value(current.params[index].value) + "}"; }
      result += "],\"explicitParams\":[";
      for (std::size_t index = 0; index < current.explicit_params.size(); ++index) { if (index) result += ','; result += oracle_escape(current.explicit_params[index]); }
      result += "],\"passes\":[";
      for (std::size_t index = 0; index < current.passes.size(); ++index) { if (index) result += ','; result += oracle_admission(current.passes[index]); }
      return result + "],\"loc\":" + oracle_loc(current.loc) + "}";
    }
  }, step);
}

noisemaker::effects::EffectDefinition oracle_effect(std::string name, std::string kind = "generator", std::string domain = "image") {
  noisemaker::effects::EffectDefinition result;
  result.name_space = "fixture"; result.function = std::move(name); result.id = result.name_space + "/" + result.function;
  result.kind = std::move(kind); result.domain = std::move(domain);
  noisemaker::effects::PassDefinition pass; pass.name = "main"; pass.program = result.function; result.passes.push_back(std::move(pass));
  return result;
}

noisemaker::effects::EffectRegistry oracle_custom_registry() {
  auto all = oracle_effect("all");
  const auto add = [&](std::string name, std::string type, noisemaker::effects::Value value) { noisemaker::effects::ParameterDefinition parameter; parameter.name = std::move(name); parameter.type = std::move(type); parameter.default_value = std::move(value); all.parameters.push_back(std::move(parameter)); };
  add("f", "float", noisemaker::effects::Value::number_value(1)); add("i", "int", noisemaker::effects::Value::number_value(2)); add("flag", "boolean", noisemaker::effects::Value::boolean_value(true));
  add("c", "color", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v2", "vec2", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v3", "vec3", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v4", "vec4", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("m", "mat3", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(1), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(1), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(1)}));
  auto choice = [](std::string name, std::string type, double value, std::vector<std::pair<std::string, noisemaker::effects::Value>> choices) { noisemaker::effects::ParameterDefinition parameter; parameter.name = std::move(name); parameter.type = std::move(type); parameter.default_value = noisemaker::effects::Value::number_value(value); parameter.choices = std::move(choices); return parameter; };
  all.parameters.push_back(choice("e", "enum", 1, {{"one", noisemaker::effects::Value::number_value(1)}, {"zero", noisemaker::effects::Value::number_value(0)}, {"marker", noisemaker::effects::Value::null()}}));
  all.parameters.push_back(choice("member", "member", 1, {{"brushed", noisemaker::effects::Value::number_value(1)}, {"other", noisemaker::effects::Value::number_value(2)}}));
  all.parameters.push_back(choice("palette", "palette", 1, {{"brushed", noisemaker::effects::Value::number_value(1)}, {"other", noisemaker::effects::Value::number_value(2)}}));
  noisemaker::effects::ParameterDefinition string; string.name = "str"; string.type = "string"; string.default_value = noisemaker::effects::Value::string_value("plain"); string.choices = {{"plain", noisemaker::effects::Value::string_value("plain")}, {"bold", noisemaker::effects::Value::string_value("bold")}}; all.parameters.push_back(string);
  noisemaker::effects::ParameterDefinition surface; surface.name = "surf"; surface.type = "surface"; surface.default_value = noisemaker::effects::Value::null(); all.parameters.push_back(surface);
  noisemaker::effects::ParameterDefinition volume; volume.name = "vol"; volume.type = "volume"; volume.default_value = noisemaker::effects::Value::string_value("volume"); all.parameters.push_back(volume);
  noisemaker::effects::ParameterDefinition geometry; geometry.name = "geo"; geometry.type = "geometry"; geometry.default_value = noisemaker::effects::Value::string_value("geo"); all.parameters.push_back(geometry);
  auto source = oracle_effect("source"); noisemaker::effects::ParameterDefinition first; first.name = "first"; first.type = "int"; first.default_value = noisemaker::effects::Value::number_value(1); source.parameters.push_back(first); noisemaker::effects::ParameterDefinition second; second.name = "second"; second.type = "int"; second.default_value = noisemaker::effects::Value::number_value(2); source.parameters.push_back(second);
  auto alias = oracle_effect("alias"); alias.parameter_aliases = {{"strength", "amount"}}; noisemaker::effects::ParameterDefinition amount; amount.name = "amount"; amount.type = "float"; amount.default_value = noisemaker::effects::Value::number_value(1); alias.parameters.push_back(amount);
  auto bounded = oracle_effect("bounded"); noisemaker::effects::ParameterDefinition bound; bound.name = "amount"; bound.type = "float"; bound.default_value = noisemaker::effects::Value::number_value(1); bound.min = noisemaker::effects::Value::number_value(0); bound.max = noisemaker::effects::Value::number_value(2); bounded.parameters.push_back(bound);
  auto required = oracle_effect("required"); noisemaker::effects::ParameterDefinition needed; needed.name = "amount"; needed.type = "float"; required.parameters.push_back(needed);
  return noisemaker::effects::EffectRegistry({all, source, alias, bounded, required, oracle_effect("mixer", "mixer", "image"), oracle_effect("volumeGen", "generator", "volume-generator"), oracle_effect("volumeFilter", "filter", "volume-filter"), oracle_effect("volumeRender", "filter", "volume-renderer"), oracle_effect("loopBegin", "filter", "loop-begin"), oracle_effect("loopEnd", "filter", "loop-end")});
}
}

int main(int argc, char** argv) {
  std::string name, source, source_name = "<dsl>", mode = "custom";
  bool require_executable = false, list_mode = false;
  for (int index = 1; index < argc; ++index) {
    const std::string argument = argv[index];
    if (argument == "--name" && index + 1 < argc) name = argv[++index];
    else if (argument == "--source" && index + 1 < argc) source = argv[++index];
    else if (argument == "--source-name" && index + 1 < argc) source_name = argv[++index];
    else if (argument == "--mode" && index + 1 < argc) mode = argv[++index];
    else if (argument == "--require-executable") require_executable = true;
    else if (argument == "--list") list_mode = true;
    else { std::cerr << "usage: --name NAME --source TEXT --source-name NAME [--mode custom|catalog_records]\n"; return 2; }
  }
  if (list_mode) {
    const auto registry = noisemaker::effects::EffectRegistry(noisemaker::effects::effect_catalog());
    const auto definitions = registry.list();
    std::cout << "[";
    for (std::size_t index = 0; index < definitions.size(); ++index) {
      if (index) std::cout << ',';
      std::cout << oracle_escape(definitions[index]->id);
    }
    std::cout << "]\n";
    return 0;
  }
  std::cout << "{\"name\":" << oracle_escape(name);
  try {
    const auto registry = mode == "catalog_records" ? noisemaker::effects::EffectRegistry(noisemaker::effects::effect_catalog()) : oracle_custom_registry();
    const auto plan = noisemaker::dsl::compile(source, registry, {.require_executable = require_executable}, source_name);
    std::string output = ",\"plan\":{\"schema\":\"noisemaker-cpp.execution-plan.v1\",\"search\":[";
    for (std::size_t index = 0; index < plan.search.size(); ++index) { if (index) output += ','; output += oracle_escape(plan.search[index]); }
    output += "],\"chains\":[";
    for (std::size_t chain_index = 0; chain_index < plan.chains.size(); ++chain_index) { if (chain_index) output += ','; const auto& chain = plan.chains[chain_index]; output += "{\"loc\":" + oracle_loc(chain.loc) + ",\"steps\":["; for (std::size_t step_index = 0; step_index < chain.steps.size(); ++step_index) { if (step_index) output += ','; output += oracle_step(chain.steps[step_index]); } output += "]}"; }
    output += "],\"renderSurface\":" + oracle_surface(plan.render_surface) + ",\"requireExecutable\":" + (require_executable ? "true" : "false") + ",\"executable\":" + (plan.executable ? "true" : "false") + ",\"availability\":[";
    for (std::size_t index = 0; index < plan.availability.size(); ++index) { if (index) output += ','; output += oracle_admission(plan.availability[index]); }
    const auto& p = plan.provenance;
    output += "],\"provenance\":{\"kind\":" + oracle_escape(p.kind) + ",\"schema\":" + oracle_escape(p.schema) + ",\"generatedPayloadSha256\":" + oracle_escape(p.generated_payload_sha256) + ",\"normalizedRecordStreamSha256\":" + oracle_escape(p.normalized_record_stream_sha256) + ",\"authorityLock\":" + oracle_escape(p.authority_lock) + ",\"cpuRevision\":" + oracle_escape(p.cpu_revision) + ",\"sourceLockSha256\":" + oracle_escape(p.source_lock_sha256) + ",\"upstreamRevision\":" + oracle_escape(p.upstream_revision) + ",\"upstreamTree\":" + oracle_escape(p.upstream_tree) + ",\"compatibilitySha256\":" + oracle_escape(p.compatibility_sha256) + ",\"counts\":{\"definitions\":" + std::to_string(p.counts.definitions) + ",\"passes\":" + std::to_string(p.counts.passes) + ",\"referenceProgramKeys\":" + std::to_string(p.counts.reference_program_keys) + ",\"backendPrograms\":" + std::to_string(p.counts.backend_programs) + ",\"compatiblePrograms\":" + std::to_string(p.counts.compatible_programs) + ",\"incompatiblePrograms\":" + std::to_string(p.counts.incompatible_programs) + ",\"missingPasses\":" + std::to_string(p.counts.missing_passes) + ",\"scatterPasses\":" + std::to_string(p.counts.scatter_passes) + ",\"executableDefinitions\":" + std::to_string(p.counts.executable_definitions) + ",\"incompleteDefinitions\":" + std::to_string(p.counts.incomplete_definitions) + "}}}";
    std::cout << output;
  } catch (const noisemaker::dsl::DslError& error) {
    std::cout << ",\"error\":{\"name\":\"DslError\",\"message\":" << oracle_escape(error.what()) << ",\"sourceName\":" << oracle_escape(error.sourceName) << ",\"line\":" << error.line << ",\"column\":" << error.column << ",\"index\":" << error.index << '}';
  }
  std::cout << "}\n";
  return 0;
}
#endif
