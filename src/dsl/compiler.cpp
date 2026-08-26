#include "noisemaker/dsl/compiler.hpp"

#include "noisemaker/dsl/parser.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>

namespace noisemaker::graph::detail {
namespace {

class CanonicalWriter final {
 public:
  void token(std::string_view value) {
    bytes_ += std::to_string(value.size());
    bytes_ += ':';
    bytes_ += value;
  }
  void number(double value) {
    // Canonical numeric values are IEEE-754 binary64 bits, written in
    // big-endian hexadecimal. This avoids implementation-specific decimal
    // formatting (including exponent spelling) and is directly portable to
    // JavaScript DataView/getUint32 hashing.
    std::uint64_t bits = 0;
    static_assert(sizeof(bits) == sizeof(value));
    std::memcpy(&bits, &value, sizeof(bits));
    char encoded[16]{};
    constexpr char hex[] = "0123456789abcdef";
    for (int index = 15; index >= 0; --index) {
      encoded[index] = hex[bits & 0xfu];
      bits >>= 4u;
    }
    token(std::string("number-bits:") + std::string(encoded, sizeof(encoded)));
  }
  void boolean(bool value) { token(value ? "true" : "false"); }
  void size(std::size_t value) { token(std::to_string(value)); }
  void optional(bool present) { boolean(present); }
  [[nodiscard]] const std::string& bytes() const noexcept { return bytes_; }

 private:
  std::string bytes_;
};

void value(CanonicalWriter& writer, const effects::Value& input);

void plan_value(CanonicalWriter& writer, const PlanValue& input) {
  writer.size(static_cast<std::size_t>(input.kind));
  switch (input.kind) {
    case PlanValue::Kind::null_value: break;
    case PlanValue::Kind::boolean: writer.boolean(input.boolean); break;
    case PlanValue::Kind::number: writer.number(input.number); break;
    case PlanValue::Kind::string: writer.token(input.string); break;
    case PlanValue::Kind::array:
      writer.size(input.array.size());
      for (const auto& item : input.array) plan_value(writer, item);
      break;
    case PlanValue::Kind::surface:
      writer.size(static_cast<std::size_t>(input.surface.kind));
      writer.token(input.surface.name);
      writer.size(input.surface.index);
      break;
  }
}

void location(CanonicalWriter& writer, const dsl::SourceLocation& input) {
  writer.token(input.source_name);
  writer.size(input.line);
  writer.size(input.column);
  writer.size(input.index);
}

template <typename T, typename F>
void vector_values(CanonicalWriter& writer, const std::vector<T>& values, F&& emit) {
  writer.size(values.size());
  for (const auto& item : values) emit(writer, item);
}

void string_pairs(CanonicalWriter& writer, const std::vector<std::pair<std::string, std::string>>& values) {
  vector_values(writer, values, [](CanonicalWriter& out, const auto& item) {
    out.token(item.first); out.token(item.second);
  });
}

void value_pairs(CanonicalWriter& writer, const std::vector<std::pair<std::string, effects::Value>>& values) {
  vector_values(writer, values, [](CanonicalWriter& out, const auto& item) {
    out.token(item.first); value(out, item.second);
  });
}

void optional_value(CanonicalWriter& writer, const std::optional<effects::Value>& input) {
  writer.optional(input.has_value());
  if (input.has_value()) value(writer, *input);
}

void optional_string(CanonicalWriter& writer, const std::optional<std::string>& input) {
  writer.optional(input.has_value());
  if (input.has_value()) writer.token(*input);
}

void dimension(CanonicalWriter& writer, const effects::DimensionExpression& input) {
  writer.size(static_cast<std::size_t>(input.kind));
  writer.token(input.parameter);
  writer.token(input.input_override);
  writer.number(input.literal);
  writer.number(input.default_value);
  writer.number(static_cast<double>(input.power));
  value(writer, input.raw);
}

void parameter(CanonicalWriter& writer, const effects::ParameterDefinition& input) {
  writer.token(input.name); writer.token(input.type); optional_value(writer, input.default_value);
  optional_string(writer, input.define); optional_value(writer, input.zero);
  value_pairs(writer, input.choices); value_pairs(writer, input.enum_values);
  optional_string(writer, input.enum_name); optional_value(writer, input.min); optional_value(writer, input.max);
  optional_string(writer, input.uniform); optional_string(writer, input.texture);
  optional_string(writer, input.color_mode_uniform); writer.boolean(input.cpu_only); value_pairs(writer, input.raw);
}

void blend(CanonicalWriter& writer, const std::optional<effects::BlendDefinition>& input) {
  writer.optional(input.has_value());
  if (input.has_value()) {
    writer.size(static_cast<std::size_t>(input->kind)); writer.boolean(input->enabled);
    writer.token(input->factors[0]); writer.token(input->factors[1]);
  }
}

void pass(CanonicalWriter& writer, const effects::PassDefinition& input) {
  writer.token(input.name); writer.token(input.program); string_pairs(writer, input.inputs);
  string_pairs(writer, input.outputs); value_pairs(writer, input.uniforms); optional_value(writer, input.count);
  optional_value(writer, input.repeat); optional_value(writer, input.conditions); optional_value(writer, input.viewport);
  blend(writer, input.blend); optional_string(writer, input.draw_mode); optional_value(writer, input.draw_buffers);
  value_pairs(writer, input.raw);
}

void texture(CanonicalWriter& writer, const effects::TextureDefinition& input) {
  writer.token(input.name); dimension(writer, input.width); dimension(writer, input.height);
  optional_string(writer, input.format); value_pairs(writer, input.raw);
}

void value(CanonicalWriter& writer, const effects::Value& input) {
  writer.size(static_cast<std::size_t>(input.kind));
  writer.boolean(input.boolean); writer.number(input.number); writer.token(input.string);
  vector_values(writer, input.array, [](CanonicalWriter& out, const auto& item) { value(out, item); });
  value_pairs(writer, input.object);
}

void definition(CanonicalWriter& writer, const effects::EffectDefinition& input) {
  writer.token(input.id); writer.token(input.directory_name); writer.token(input.name); writer.token(input.name_space);
  writer.token(input.function); writer.token(input.kind); writer.token(input.domain); vector_values(writer, input.tags, [](auto& out, const auto& item) { out.token(item); });
  writer.token(input.description); string_pairs(writer, input.parameter_aliases);
  vector_values(writer, input.parameters, [](auto& out, const auto& item) { parameter(out, item); });
  vector_values(writer, input.passes, [](auto& out, const auto& item) { pass(out, item); });
  vector_values(writer, input.textures, [](auto& out, const auto& item) { texture(out, item); });
  optional_string(writer, input.external_texture); optional_string(writer, input.output_tex3d); optional_string(writer, input.output_geo);
  optional_string(writer, input.output_xyz); optional_string(writer, input.output_velocity); optional_string(writer, input.output_rgba);
  writer.boolean(input.iterated); optional_string(writer, input.loop_role); value_pairs(writer, input.raw);
}

void binding(CanonicalWriter& writer, const CompatibilityBinding& input) {
  writer.token(input.name); writer.token(input.type); writer.token(input.source); writer.token(input.source_name);
  writer.token(input.resource); writer.token(input.cpp_type);
}

void output(CanonicalWriter& writer, const CompatibilityOutput& input) {
  writer.size(input.slot); writer.token(input.physical_name);
  writer.token(input.logical_route); writer.token(input.cpp_type);
}

void authority_pass(CanonicalWriter& writer, const AuthorityPassMetadata& input) {
  writer.token(input.name); string_pairs(writer, input.inputs); string_pairs(writer, input.outputs); vector_values(writer, input.uniforms, [](auto& out, const auto& item) { out.token(item.first); plan_value(out, item.second); });
  writer.token(input.blend_kind); writer.boolean(input.blend); writer.token(input.blend_factors[0]); writer.token(input.blend_factors[1]);
  writer.optional(input.repeat.has_value()); if (input.repeat.has_value()) plan_value(writer, *input.repeat);
}

void admission(CanonicalWriter& writer, const PassAdmission& input) {
  writer.size(input.identity.index); writer.token(input.identity.name); writer.token(input.identity.program_key);
  writer.size(static_cast<std::size_t>(input.status)); vector_values(writer, input.reasons, [](auto& out, const auto& item) { out.token(item.code); out.token(item.detail); });
  writer.token(input.canonical_factory); writer.token(input.source_sha256); writer.token(input.semantic_sha256);
  writer.token(input.emitted_factory); writer.token(input.route_kind); writer.token(input.typed_abi_sha256);
  writer.token(input.binding_abi_sha256);
  writer.token(input.output_extent.width); writer.token(input.output_extent.height); writer.token(input.output_extent.format);
  vector_values(writer, input.compile_defines, [](auto& out, const auto& item) { binding(out, item); });
  vector_values(writer, input.capabilities, [](auto& out, const auto& item) { out.token(item); });
  writer.token(input.dimensionality); writer.token(input.draw_mode);
  vector_values(writer, input.samplers, [](auto& out, const auto& item) { binding(out, item); });
  vector_values(writer, input.uniforms, [](auto& out, const auto& item) { binding(out, item); });
  vector_values(writer, input.outputs, [](auto& out, const auto& item) { output(out, item); }); authority_pass(writer, input.authority_pass);
  writer.optional(input.scatter.has_value());
  if (input.scatter.has_value()) {
    const auto& scatter = *input.scatter;
    writer.token(scatter.adapter); writer.token(scatter.registry); writer.token(scatter.draw_mode); writer.token(scatter.dimensionality);
    writer.token(scatter.count); writer.token(scatter.input_texture); writer.token(scatter.destination_mutation); writer.boolean(scatter.blend);
    vector_values(writer, scatter.uniforms, [](auto& out, const auto& item) { binding(out, item); });
    vector_values(writer, scatter.outputs, [](auto& out, const auto& item) { out.size(item.slot); out.token(item.physical_name); out.token(item.logical_route); out.token(item.cpp_type); });
  }
}

void snapshot(CanonicalWriter& writer, const PlanEffectSnapshot& input) {
  definition(writer, input.definition); vector_values(writer, input.admissions, [](auto& out, const auto& item) { admission(out, item); });
}

void surface(CanonicalWriter& writer, const SurfaceReference& input) {
  writer.size(static_cast<std::size_t>(input.kind)); writer.token(input.name); writer.size(input.index); location(writer, input.loc);
}

void step(CanonicalWriter& writer, const CompiledStep& input) {
  std::visit([&](const auto& current) {
    using T = std::decay_t<decltype(current)>;
    if constexpr (std::is_same_v<T, ReadStep>) { writer.token("read"); surface(writer, current.surface); location(writer, current.loc); }
    else if constexpr (std::is_same_v<T, WriteStep>) { writer.token("write"); surface(writer, current.surface); location(writer, current.loc); }
    else {
      writer.token("effect"); writer.token(current.effect.id); writer.token(current.effect.domain); writer.token(current.effect.kind); writer.size(current.snapshot_index);
      vector_values(writer, current.params, [](auto& out, const auto& item) { out.token(item.name); plan_value(out, item.value); });
      vector_values(writer, current.explicit_params, [](auto& out, const auto& item) { out.token(item); });
      vector_values(writer, current.passes, [](auto& out, const auto& item) { admission(out, item); }); location(writer, current.loc);
    }
  }, input);
}


}  // namespace

std::string sha256(std::string_view input) {
  constexpr std::array<std::uint32_t, 64> k = {
      0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
      0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
      0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
      0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
      0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
      0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
      0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
      0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u};
  std::array<std::uint32_t, 8> h = {0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u};
  const std::uint64_t bit_length = static_cast<std::uint64_t>(input.size()) * 8u;
  const std::size_t padded = ((input.size() + 9u + 63u) / 64u) * 64u;
  std::string message(padded, '\0');
  std::memcpy(message.data(), input.data(), input.size()); message[input.size()] = static_cast<char>(0x80);
  for (int byte = 0; byte < 8; ++byte) message[padded - 1 - byte] = static_cast<char>(bit_length >> (byte * 8));
  for (std::size_t offset = 0; offset < padded; offset += 64) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t i = 0; i < 16; ++i) words[i] = (static_cast<std::uint32_t>(static_cast<unsigned char>(message[offset + 4*i])) << 24) | (static_cast<std::uint32_t>(static_cast<unsigned char>(message[offset + 4*i + 1])) << 16) | (static_cast<std::uint32_t>(static_cast<unsigned char>(message[offset + 4*i + 2])) << 8) | static_cast<std::uint32_t>(static_cast<unsigned char>(message[offset + 4*i + 3]));
    for (std::size_t i = 16; i < 64; ++i) { const auto s0 = std::rotr(words[i-15], 7u) ^ std::rotr(words[i-15], 18u) ^ (words[i-15] >> 3); const auto s1 = std::rotr(words[i-2], 17u) ^ std::rotr(words[i-2], 19u) ^ (words[i-2] >> 10); words[i] = words[i-16] + s0 + words[i-7] + s1; }
    auto working = h;
    for (std::size_t i = 0; i < 64; ++i) { const auto s1 = std::rotr(working[4], 6u) ^ std::rotr(working[4], 11u) ^ std::rotr(working[4], 25u); const auto ch = (working[4] & working[5]) ^ (~working[4] & working[6]); const auto temp1 = working[7] + s1 + ch + k[i] + words[i]; const auto s0 = std::rotr(working[0], 2u) ^ std::rotr(working[0], 13u) ^ std::rotr(working[0], 22u); const auto maj = (working[0] & working[1]) ^ (working[0] & working[2]) ^ (working[1] & working[2]); const auto temp2 = s0 + maj; working = {temp1 + temp2, working[0], working[1], working[2], working[3] + temp1, working[4], working[5], working[6]}; }
    for (std::size_t i = 0; i < 8; ++i) h[i] += working[i];
  }
  std::string result; result.reserve(64); constexpr char hex[] = "0123456789abcdef";
  for (const auto word : h) for (int shift = 28; shift >= 0; shift -= 4) result += hex[(word >> shift) & 0xfu];
  return result;
}

std::string admission_sha256(const PassAdmission& input) {
  CanonicalWriter writer; admission(writer, input); return sha256(writer.bytes());
}

std::string snapshot_sha256(const PlanEffectSnapshot& input) {
  CanonicalWriter writer; snapshot(writer, input); return sha256(writer.bytes());
}

std::string plan_payload_sha256(const ExecutionPlan& input) {
  CanonicalWriter writer;
  vector_values(writer, input.search, [](auto& out, const auto& item) { out.token(item); });
  vector_values(writer, input.effects, [](auto& out, const auto& item) { snapshot(out, item); });
  vector_values(writer, input.chains, [](auto& out, const auto& item) { location(out, item.loc); vector_values(out, item.steps, [](auto& inner, const auto& step_value) { step(inner, step_value); }); });
  surface(writer, input.render_surface); writer.boolean(input.require_executable); writer.boolean(input.executable);
  vector_values(writer, input.availability, [](auto& out, const auto& item) { admission(out, item); });
  return sha256(writer.bytes());
}

}  // namespace noisemaker::graph::detail

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
  auto plan = compile(parse(source, source_name), registry, options);
  plan.provenance.source_sha256 = graph::detail::sha256(source);
  plan.provenance.source_name = std::string(source_name);
  plan.provenance.plan_payload_sha256 = graph::detail::plan_payload_sha256(plan);
  return plan;
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
  plan.provenance.source_name = program.loc.source_name;
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
      auto snapshot_it = std::find_if(plan.effects.begin(), plan.effects.end(), [&](const auto& snapshot) {
        return snapshot.definition.id == definition->id;
      });
      if (snapshot_it == plan.effects.end()) {
        graph::PlanEffectSnapshot snapshot;
        snapshot.definition = *definition;
        snapshot.admissions.reserve(definition->passes.size());
        for (std::size_t snapshot_pass = 0; snapshot_pass < definition->passes.size(); ++snapshot_pass)
          snapshot.admissions.push_back(registry.admission(*definition, snapshot_pass));
        snapshot.snapshot_sha256 = graph::detail::snapshot_sha256(snapshot);
        plan.effects.push_back(std::move(snapshot));
        snapshot_it = std::prev(plan.effects.end());
      }
      step.snapshot_index = static_cast<std::size_t>(std::distance(plan.effects.begin(), snapshot_it));
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
  plan.provenance.plan_payload_sha256 = graph::detail::plan_payload_sha256(plan);
  return plan;
}

}  // namespace noisemaker::dsl

namespace noisemaker::graph {

bool validate_execution_plan(const ExecutionPlan& plan) noexcept {
  try {
    for (const auto& snapshot : plan.effects) {
      if (snapshot.definition.passes.size() != snapshot.admissions.size()) return false;
      if (snapshot.snapshot_sha256 != detail::snapshot_sha256(snapshot)) return false;
    }
    for (const auto& chain : plan.chains) {
      for (const auto& compiled : chain.steps) {
        if (const auto* effect = std::get_if<EffectStep>(&compiled)) {
          if (effect->snapshot_index >= plan.effects.size()) return false;
          const auto& snapshot = plan.effects[effect->snapshot_index];
          if (effect->effect.id != snapshot.definition.id || effect->effect.domain != snapshot.definition.domain || effect->effect.kind != snapshot.definition.kind) return false;
        }
      }
    }
    return !plan.provenance.plan_payload_sha256.empty() && plan.provenance.plan_payload_sha256 == detail::plan_payload_sha256(plan);
  } catch (...) {
    return false;
  }
}

}  // namespace noisemaker::graph
