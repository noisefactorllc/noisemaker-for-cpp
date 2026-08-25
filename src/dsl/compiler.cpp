#include "noisemaker/dsl/compiler.hpp"

#include "noisemaker/dsl/parser.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>

namespace noisemaker::dsl {
namespace {

using graph::ExecutionChain;
using graph::ExecutionPlan;
using graph::PlanValue;
using graph::SurfaceReference;

struct ResolvedArgument { std::optional<std::string> name; PlanValue value; SourceLocation loc{}; };
struct ResolvedCall {
  std::string name;
  std::vector<ResolvedArgument> args;
  dsl::Call::ArgumentMode mode = dsl::Call::ArgumentMode::none;
  SourceLocation loc{};
};
struct Partial { ResolvedCall call; };
using InternalBinding = std::variant<PlanValue, Partial>;

[[noreturn]] void value_error(std::string message, const SourceLocation& loc) {
  throw DslError(std::move(message), loc);
}

PlanValue evaluate(const Value& value, const std::map<std::string, InternalBinding>& bindings) {
  switch (value.kind) {
    case Value::Kind::number: return PlanValue::number_value(value.number());
    case Value::Kind::string: return PlanValue::string_value(value.string_value());
    case Value::Kind::boolean: return PlanValue::boolean_value(value.boolean());
    case Value::Kind::color: {
      std::vector<PlanValue> components;
      for (const double component : value.color_value().components) components.push_back(PlanValue::number_value(component));
      return PlanValue::array_value(std::move(components));
    }
    case Value::Kind::surface: {
      const auto& surface = value.surface_value();
      return PlanValue::surface_value(SurfaceReference::named(surface.name, surface.index, surface.loc));
    }
    case Value::Kind::array: {
      std::vector<PlanValue> values;
      values.reserve(value.array_value().values.size());
      for (const auto& item : value.array_value().values) values.push_back(evaluate(item, bindings));
      return PlanValue::array_value(std::move(values));
    }
    case Value::Kind::identifier: {
      const auto& identifier = value.identifier_value();
      const auto found = bindings.find(identifier.name);
      if (found == bindings.end()) return PlanValue::string_value(identifier.name);
      if (std::holds_alternative<Partial>(found->second)) value_error("Effect partial \"" + identifier.name + "\" cannot be used as a value", value.loc);
      return std::get<PlanValue>(found->second);
    }
    case Value::Kind::vector: {
      std::vector<PlanValue> values;
      for (const auto& item : value.vector().values) values.push_back(evaluate(item, bindings));
      bool numeric = values.size() == value.vector().width;
      for (const auto& item : values) numeric = numeric && item.kind == PlanValue::Kind::number;
      if (!numeric) value_error("vec" + std::to_string(value.vector().width) + " requires " + std::to_string(value.vector().width) + " numeric values", value.loc);
      return PlanValue::array_value(std::move(values));
    }
    case Value::Kind::unary: {
      const PlanValue operand = evaluate(*value.unary().argument, bindings);
      if (operand.kind != PlanValue::Kind::number) value_error("Unary arithmetic requires a number", value.loc);
      return PlanValue::number_value(value.unary().operator_token == '-' ? -operand.number : operand.number);
    }
    case Value::Kind::binary: {
      const PlanValue left = evaluate(*value.binary().left, bindings);
      const PlanValue right = evaluate(*value.binary().right, bindings);
      if (left.kind != PlanValue::Kind::number || right.kind != PlanValue::Kind::number) value_error("Arithmetic requires numeric values", value.loc);
      switch (value.binary().operator_token) {
        case '+': return PlanValue::number_value(left.number + right.number);
        case '-': return PlanValue::number_value(left.number - right.number);
        case '*': return PlanValue::number_value(left.number * right.number);
        default: return PlanValue::number_value(left.number / right.number);
      }
    }
  }
  value_error("Unsupported DSL value", value.loc);
}

ResolvedCall resolve_call(const Call& call, const std::map<std::string, InternalBinding>& bindings) {
  ResolvedCall result;
  result.name = call.name;
  result.mode = call.argument_mode;
  result.loc = call.loc;
  for (const auto& argument : call.arguments) result.args.push_back({argument.name, evaluate(argument.value, bindings), argument.loc});
  return result;
}

ResolvedCall merge_partial(const Partial& stored, const ResolvedCall& call) {
  if (stored.call.mode == Call::ArgumentMode::none) {
    ResolvedCall result = call;
    result.name = stored.call.name;
    return result;
  }
  if (call.mode == Call::ArgumentMode::none) {
    ResolvedCall result = stored.call;
    result.loc = call.loc;
    return result;
  }
  if (stored.call.mode != call.mode) throw DslError("Partial and call arguments must use the same named or positional form", call.loc);
  if (stored.call.mode == Call::ArgumentMode::positional) {
    ResolvedCall result = call;
    result.name = stored.call.name;
    result.args = stored.call.args;
    result.args.insert(result.args.end(), call.args.begin(), call.args.end());
    return result;
  }
  ResolvedCall result = call;
  result.name = stored.call.name;
  result.mode = Call::ArgumentMode::named;
  // Match the authority Map.set merge: overwrite in place and retain the
  // first insertion position, while new keys append once.
  result.args.clear();
  for (const auto& stored_argument : stored.call.args) {
    auto existing = std::find_if(result.args.begin(), result.args.end(), [&](const auto& argument) {
      return argument.name == stored_argument.name;
    });
    if (existing == result.args.end()) result.args.push_back(stored_argument);
    else *existing = stored_argument;
  }
  for (const auto& incoming : call.args) {
    auto existing = std::find_if(result.args.begin(), result.args.end(), [&](const auto& argument) { return argument.name == incoming.name; });
    if (existing == result.args.end()) result.args.push_back(incoming);
    else *existing = incoming;
  }
  return result;
}

bool has_input_texture(const effects::EffectDefinition& definition) {
  for (const auto& pass : definition.passes) for (const auto& input : pass.inputs) if (input.second == "inputTex") return true;
  return false;
}

SurfaceReference surface_from_value(const PlanValue& value) {
  if (value.kind != PlanValue::Kind::surface || value.surface.kind != SurfaceReference::Kind::named) return {};
  return value.surface;
}

std::string availability_text(const graph::PassAdmission& admission) {
  std::string text = "Effect pass \"" + admission.identity.program_key + "\" unavailable";
  for (const auto& reason : admission.reasons) text += ": " + reason.code + " (" + reason.detail + ")";
  return text;
}

}  // namespace

ExecutionPlan compile(std::string_view source, const effects::EffectRegistry& registry,
                      CompileOptions options, std::string_view source_name) {
  return compile(parse(source, source_name), registry, options);
}

ExecutionPlan compile(const Program& program, const effects::EffectRegistry& registry,
                      CompileOptions options) {
  if (program.search.empty()) throw DslError("Missing required search directive", program.loc);
  std::map<std::string, InternalBinding> bindings;
  for (const auto& binding : program.bindings) {
    if (bindings.find(binding.name) != bindings.end()) throw DslError("Duplicate binding \"" + binding.name + "\"", binding.loc);
    if (std::holds_alternative<Call>(binding.value)) {
      const auto& call = std::get<Call>(binding.value);
      bindings.emplace(binding.name, Partial{resolve_call(call, bindings)});
    } else {
      bindings.emplace(binding.name, evaluate(std::get<Value>(binding.value), bindings));
    }
  }

  ExecutionPlan plan;
  plan.search = program.search;
  plan.require_executable = options.require_executable;
  const auto& provenance = registry.provenance();
  plan.provenance.kind = registry.manifest_backed() ? "manifest" : "custom";
  plan.provenance.schema = provenance.schema;
  plan.provenance.backend_schema = provenance.backend_schema;
  plan.provenance.corpus_revision = provenance.corpus_revision;
  plan.provenance.generated_payload_sha256 = provenance.generated_payload_sha256;
  plan.provenance.normalized_record_stream_sha256 = provenance.normalized_record_stream_sha256;
  plan.provenance.authority_lock = provenance.cpu_behavioral_lock;
  plan.provenance.cpu_revision = provenance.cpu_revision;
  plan.provenance.source_lock_sha256 = provenance.source_lock_sha256;
  plan.provenance.cpu_package_sha256 = provenance.cpu_package_sha256;
  plan.provenance.cpu_package_lock_sha256 = provenance.cpu_package_lock_sha256;
  plan.provenance.cpu_source_lock_sha256 = provenance.cpu_source_lock_sha256;
  plan.provenance.upstream_revision = provenance.upstream_revision;
  plan.provenance.upstream_package_sha256 = provenance.upstream_package_sha256;
  plan.provenance.upstream_package_lock_sha256 = provenance.upstream_package_lock_sha256;
  plan.provenance.upstream_tree = provenance.upstream_tree;
  plan.provenance.compatibility_sha256 = provenance.compatibility_sha256;
  plan.provenance.counts = {provenance.counts.definitions, provenance.counts.passes, provenance.counts.reference_program_keys,
                            provenance.counts.backend_programs, provenance.counts.compatible_programs, provenance.counts.incompatible_programs,
                            provenance.counts.missing_passes, provenance.counts.scatter_passes, provenance.counts.executable_definitions,
                            provenance.counts.incomplete_definitions};
  SurfaceReference last_written;
  SourceLocation first_unavailable{};
  bool have_unavailable = false;

  for (const auto& source_chain : program.chains) {
    ExecutionChain chain;
    chain.loc = source_chain.loc;
    bool has_image = false;
    bool has_volume = false;
    bool starts_with_generator = false;
    std::optional<SourceLocation> open_loop;
    for (std::size_t index = 0; index < source_chain.calls.size(); ++index) {
      const auto& source_call = source_chain.calls[index];
      const auto found_binding = bindings.find(source_call.name);
      if (found_binding != bindings.end()) {
        if (!std::holds_alternative<Partial>(found_binding->second)) throw DslError("Binding \"" + source_call.name + "\" is not callable", source_call.loc);
        const auto stored_mode = std::get<Partial>(found_binding->second).call.mode;
        if (stored_mode != Call::ArgumentMode::none && source_call.argument_mode != Call::ArgumentMode::none && stored_mode != source_call.argument_mode)
          throw DslError("Partial and call arguments must use the same named or positional form", source_call.loc);
      }
      ResolvedCall call = resolve_call(source_call, bindings);
      if (found_binding != bindings.end()) call = merge_partial(std::get<Partial>(found_binding->second), call);

      if (call.name == "read") {
        if (index != 0 || call.args.size() != 1 || call.args.front().value.kind != PlanValue::Kind::surface) throw DslError("read(surface) must begin a chain", call.loc);
        chain.steps.push_back(graph::ReadStep{surface_from_value(call.args.front().value), call.loc});
        has_image = true;
        continue;
      }
      if (call.name == "write") {
        if (open_loop.has_value()) throw DslError("loopBegin must be closed by loopEnd before write", call.loc);
        if (!has_image || call.args.size() != 1 || call.args.front().value.kind != PlanValue::Kind::surface) throw DslError("write(surface) requires a current image", call.loc);
        const SurfaceReference surface = surface_from_value(call.args.front().value);
        chain.steps.push_back(graph::WriteStep{surface, call.loc});
        last_written = surface;
        continue;
      }

      const auto* definition = registry.resolve(call.name, program.search);
      if (definition == nullptr) throw DslError("Unknown effect \"" + call.name + "\" in search namespaces " + [&] { std::string value; for (std::size_t i = 0; i < program.search.size(); ++i) { if (i) value += ", "; value += program.search[i]; } return value; }(), call.loc);

      if (definition->domain == "volume-generator") {
        if (index != 0 && !(definition->iterated && has_volume)) throw DslError("Generator " + definition->id + " must begin a chain", call.loc);
        if (index == 0) starts_with_generator = true;
        has_volume = true;
      } else if (definition->domain == "volume-filter") {
        if (!has_volume) throw DslError("volume filter " + definition->id + " requires a volume input", call.loc);
      } else if (definition->domain == "volume-renderer") {
        if (!has_volume) throw DslError("volume renderer " + definition->id + " requires a volume input", call.loc);
        has_image = true;
      } else if (definition->domain == "loop-begin") {
        if (!has_image) throw DslError(definition->id + " requires a current image", call.loc);
        if (open_loop.has_value()) throw DslError("nested loopBegin regions are not supported", call.loc);
        open_loop = call.loc;
      } else if (definition->domain == "loop-end") {
        if (!open_loop.has_value()) throw DslError("loopEnd has no matching loopBegin", call.loc);
        if (!has_image) throw DslError(definition->id + " requires a current image", call.loc);
        open_loop.reset();
      } else if (definition->kind == "generator") {
        if (index != 0) throw DslError("Generator " + definition->id + " must begin a chain", call.loc);
        starts_with_generator = true;
        has_image = true;
      } else if (!has_image) {
        if (has_input_texture(*definition)) throw DslError(definition->kind + " " + definition->id + " requires an input; begin with a generator or read(oN)", call.loc);
        has_image = true;
      }

      std::vector<effects::ParameterArgument> args;
      for (const auto& argument : call.args) args.push_back({argument.name, argument.value});
      effects::NormalizedArguments normalized;
      try { normalized = registry.normalize(*definition, args); }
      catch (const std::exception& error) { throw DslError(error.what(), call.loc); }
      graph::EffectStep step;
      step.effect = {definition->id, definition->domain, definition->kind};
      for (auto& binding : normalized.values) step.params.push_back(std::move(binding));
      for (std::size_t argument_index = 0; argument_index < call.args.size(); ++argument_index) {
        const auto& argument = call.args[argument_index];
        const std::string supplied = argument.name.value_or(argument_index < definition->parameters.size() ? definition->parameters[argument_index].name : "argument " + std::to_string(argument_index + 1));
        std::string canonical = supplied;
        for (const auto& alias : definition->parameter_aliases) if (alias.first == supplied) { canonical = alias.second; break; }
        step.explicit_params.push_back(std::move(canonical));
      }
      step.loc = call.loc;
      for (std::size_t pass_index = 0; pass_index < definition->passes.size(); ++pass_index) {
        auto admission = registry.admission(*definition, pass_index);
        if (admission.status != graph::AvailabilityStatus::compatible && admission.status != graph::AvailabilityStatus::scatter && !have_unavailable) {
          have_unavailable = true;
          first_unavailable = call.loc;
        }
        plan.availability.push_back(admission);
        step.passes.push_back(std::move(admission));
      }
      chain.steps.push_back(std::move(step));
    }
    if (open_loop.has_value()) throw DslError("loopBegin must be closed by loopEnd before the chain ends", *open_loop);
    if (starts_with_generator && (chain.steps.empty() || !std::holds_alternative<graph::WriteStep>(chain.steps.back()))) throw DslError("Generator chain must end with write(oN)", chain.loc);
    plan.chains.push_back(std::move(chain));
  }
  plan.render_surface = program.render.has_value()
                           ? SurfaceReference::named(program.render->name, program.render->index, program.render->loc)
                           : last_written;
  if (plan.render_surface.kind == SurfaceReference::Kind::none) throw DslError("No render surface specified and no write() found - add render(oN) or write(oN)", program.loc);
  plan.executable = !have_unavailable;
  if (options.require_executable && !plan.executable) {
    for (const auto& admission : plan.availability) {
      if (admission.status != graph::AvailabilityStatus::compatible && admission.status != graph::AvailabilityStatus::scatter) throw DslError(availability_text(admission), first_unavailable);
    }
  }
  return plan;
}

}  // namespace noisemaker::dsl
