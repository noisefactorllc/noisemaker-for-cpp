#include "corpus_case.hpp"

#include "noisemaker/dsl/compiler.hpp"
#include "noisemaker/effects/catalog.hpp"
#include "noisemaker/js_number.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <system_error>
#include <variant>

namespace noisemaker::benchmark {
namespace {

// Canonical relation separators. Unit separator between a field name, its
// element count, and each element; record separator after every field.
constexpr char kUnit = '\x1f';
constexpr char kRecord = '\x1e';

void append_field(std::string& out, std::string_view name,
                  const std::vector<std::string>& values) {
  out.append(name);
  out.push_back(kUnit);
  out.append(std::to_string(values.size()));
  for (const auto& value : values) {
    out.push_back(kUnit);
    out.append(value);
  }
  out.push_back(kRecord);
}

[[nodiscard]] std::filesystem::path canonical_parent(const std::string& path) {
  std::filesystem::path candidate(path);
  std::error_code code;
  auto parent = std::filesystem::weakly_canonical(candidate.parent_path(), code);
  if (code) {
    throw CaseContractError(kExitOutputPath,
                            "output directory does not resolve: " + path);
  }
  return parent;
}

[[nodiscard]] bool is_inside(const std::filesystem::path& child,
                             const std::filesystem::path& parent) {
  auto child_it = child.begin();
  auto parent_it = parent.begin();
  for (; parent_it != parent.end(); ++parent_it, ++child_it) {
    if (child_it == child.end() || *child_it != *parent_it) return false;
  }
  return true;
}

}  // namespace

std::string json_string(std::string_view value) {
  std::string out;
  out.reserve(value.size() + 2);
  out.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
      case '"': out.append("\\\""); break;
      case '\\': out.append("\\\\"); break;
      case '\b': out.append("\\b"); break;
      case '\f': out.append("\\f"); break;
      case '\n': out.append("\\n"); break;
      case '\r': out.append("\\r"); break;
      case '\t': out.append("\\t"); break;
      default:
        if (character < 0x20) {
          char buffer[7];
          std::snprintf(buffer, sizeof(buffer), "\\u%04x", character);
          out.append(buffer);
        } else {
          out.push_back(static_cast<char>(character));
        }
    }
  }
  out.push_back('"');
  return out;
}

std::string json_array(const std::vector<std::string>& values) {
  std::string out = "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) out.append(", ");
    out.append(json_string(values[index]));
  }
  out.push_back(']');
  return out;
}

std::string json_number(std::size_t value) { return std::to_string(value); }

std::string json_number(std::uint64_t value) { return std::to_string(value); }

std::string json_double(double value) {
  if (!std::isfinite(value)) {
    throw CaseContractError(kExitUsage, "a non-finite number cannot be serialized");
  }
  // One serializer for the whole port: ECMAScript Number::toString semantics
  // from js_number.hpp, never a local printf format.
  return js_number_to_string(value);
}

effects::EffectRegistry build_registry() {
  return effects::EffectRegistry(effects::effect_catalog());
}

graph::ExecutionPlan compile_case(std::string_view source,
                                  const effects::EffectRegistry& registry,
                                  std::string_view source_name,
                                  std::string_view authenticated_source_sha256) {
  // `require_executable` is written into the canonical plan payload, so this
  // spelling is load-bearing: `Renderer::compile()` passes `CompileOptions{}`
  // and yields a different `plan_payload_sha256` for identical source bytes.
  auto plan = dsl::compile(source, registry, {.require_executable = true}, source_name);
  if (!graph::validate_execution_plan(plan)) {
    throw CaseContractError(kExitPlanAuthentication,
                            "the compiled plan does not authenticate against its own payload");
  }
  if (plan.provenance.source_sha256 != authenticated_source_sha256) {
    throw CaseContractError(kExitPlanAuthentication,
                            "plan provenance source digest is not the authenticated source digest");
  }
  return plan;
}

graph::ExecutionResult execute_case(const graph::ExecutionPlan& plan,
                                    const graph::ExecutionInputs& inputs) {
  return graph::GraphExecutor{}.execute(plan, inputs);
}

PlanIdentity project_identity(const graph::ExecutionPlan& plan) {
  PlanIdentity identity;
  identity.plan_payload_sha256 = graph::detail::plan_payload_sha256(plan);
  identity.provenance_source_sha256 = plan.provenance.source_sha256;
  identity.provenance_source_name = plan.provenance.source_name;
  identity.require_executable = plan.require_executable;
  identity.executable = plan.executable;
  identity.snapshot_count = plan.effects.size();
  identity.validated = graph::validate_execution_plan(plan);
  return identity;
}

CaseProvenance project_provenance(const graph::ExecutionPlan& plan) {
  CaseProvenance provenance;
  provenance.cpu_behavioral_lock = plan.provenance.authority_lock;
  provenance.source_lock_sha256 = plan.provenance.cpu_source_lock_sha256;
  provenance.upstream_revision = plan.provenance.upstream_revision;
  provenance.upstream_tree = plan.provenance.upstream_tree;
  provenance.catalog_payload_sha256 = plan.provenance.generated_payload_sha256;
  return provenance;
}

PlanRelation project_relation(const graph::ExecutionPlan& plan,
                              const graph::ExecutionResult& result,
                              std::string_view record_id,
                              std::string_view source_sha256, std::size_t width,
                              std::size_t height) {
  PlanRelation relation;
  relation.schema = "noisemaker-cpp.plan-relation.v1";
  relation.record_id = std::string(record_id);
  relation.source_sha256 = std::string(source_sha256);
  for (const auto& chain : plan.chains) {
    for (const auto& step : chain.steps) {
      if (const auto* read = std::get_if<graph::ReadStep>(&step)) {
        relation.step_kinds.emplace_back("read");
        relation.reads.push_back(read->surface.name);
      } else if (const auto* effect = std::get_if<graph::EffectStep>(&step)) {
        relation.step_kinds.emplace_back("effect");
        relation.effect_ids.push_back(effect->effect.id);
        for (const auto& admission : effect->passes) {
          relation.pass_keys.push_back(admission.identity.program_key);
          // Emitted verbatim. `rgba16float` is not aliased to `rgba16f`: the
          // lanes already agree on the raw spelling, and an alias table would
          // mask a real future divergence rather than reveal one.
          relation.pass_formats.push_back(admission.output_extent.format);
        }
      } else if (const auto* write = std::get_if<graph::WriteStep>(&step)) {
        relation.step_kinds.emplace_back("write");
        relation.routes.push_back(write->surface.name);
      }
    }
  }
  relation.final_surface = plan.render_surface.name;
  relation.width = width;
  relation.height = height;
  relation.pass_count = result.pass_count;
  relation.relation_sha256 =
      graph::detail::sha256(canonical_relation_bytes(relation));
  return relation;
}

std::string canonical_relation_bytes(const PlanRelation& relation) {
  std::string out;
  append_field(out, "schema", {relation.schema});
  append_field(out, "recordId", {relation.record_id});
  append_field(out, "sourceSha256", {relation.source_sha256});
  append_field(out, "stepKinds", relation.step_kinds);
  append_field(out, "effectIds", relation.effect_ids);
  append_field(out, "passKeys", relation.pass_keys);
  append_field(out, "passFormats", relation.pass_formats);
  append_field(out, "reads", relation.reads);
  append_field(out, "routes", relation.routes);
  append_field(out, "finalSurface", {relation.final_surface});
  append_field(out, "dimensions",
               {std::to_string(relation.width), std::to_string(relation.height)});
  append_field(out, "passCount", {std::to_string(relation.pass_count)});
  return out;
}

std::string serialize_relation(const PlanRelation& relation, int indent) {
  const std::string pad(static_cast<std::size_t>(indent), ' ');
  const std::string inner(static_cast<std::size_t>(indent) + 2, ' ');
  std::string out = "{\n";
  out += inner + "\"schema\": " + json_string(relation.schema) + ",\n";
  out += inner + "\"recordId\": " + json_string(relation.record_id) + ",\n";
  out += inner + "\"sourceSha256\": " + json_string(relation.source_sha256) + ",\n";
  out += inner + "\"stepKinds\": " + json_array(relation.step_kinds) + ",\n";
  out += inner + "\"effectIds\": " + json_array(relation.effect_ids) + ",\n";
  out += inner + "\"passKeys\": " + json_array(relation.pass_keys) + ",\n";
  out += inner + "\"passFormats\": " + json_array(relation.pass_formats) + ",\n";
  out += inner + "\"reads\": " + json_array(relation.reads) + ",\n";
  out += inner + "\"routes\": " + json_array(relation.routes) + ",\n";
  out += inner + "\"finalSurface\": " + json_string(relation.final_surface) + ",\n";
  out += inner + "\"dimensions\": {\"width\": " + json_number(relation.width) +
         ", \"height\": " + json_number(relation.height) + "},\n";
  out += inner + "\"passCount\": " + json_number(relation.pass_count) + ",\n";
  out += inner + "\"relationSha256\": " + json_string(relation.relation_sha256) + "\n";
  out += pad + "}";
  return out;
}

TimingSummary summarize(const std::vector<std::uint64_t>& samples,
                        std::size_t pixels) {
  if (samples.empty()) {
    throw CaseContractError(kExitUsage, "a summary requires at least one sample");
  }
  if (pixels == 0) {
    throw CaseContractError(kExitUsage, "a summary requires a positive pixel count");
  }
  std::vector<std::uint64_t> sorted(samples);
  std::sort(sorted.begin(), sorted.end());
  const std::size_t count = sorted.size();
  TimingSummary summary;
  summary.min_ns = sorted.front();
  summary.max_ns = sorted.back();
  // The JS lane rounds an even-length median half-up; integer (a + b + 1) / 2
  // is the same value for nonnegative samples without a float round trip.
  summary.median_ns = (count % 2 == 0)
                          ? (sorted[count / 2 - 1] + sorted[count / 2] + 1) / 2
                          : sorted[count / 2];
  // The same IEEE-754 expression the JS lane evaluates, so the selected index
  // cannot drift between the two summaries of one sample vector.
  const auto rank = static_cast<std::size_t>(
      std::max(0.0, std::ceil(static_cast<double>(count) * 0.95) - 1.0));
  summary.p95_ns = sorted[std::min(rank, count - 1)];
  summary.pixels = pixels;
  summary.megapixels_per_second =
      summary.median_ns == 0
          ? 0.0
          : static_cast<double>(pixels) * 1000.0 / static_cast<double>(summary.median_ns);
  return summary;
}

void require_external_output_path(const std::string& path, const std::string& repo_root) {
  if (path.empty() || path.front() != '/') {
    throw CaseContractError(kExitOutputPath, "output paths must be absolute: " + path);
  }
  std::error_code code;
  const auto status = std::filesystem::symlink_status(path, code);
  if (!code && status.type() == std::filesystem::file_type::symlink) {
    throw CaseContractError(kExitOutputPath, "output must not be a symlink: " + path);
  }
  if (repo_root.empty()) return;
  auto root = std::filesystem::weakly_canonical(std::filesystem::path(repo_root), code);
  if (code) {
    throw CaseContractError(kExitOutputPath, "repository root does not resolve: " + repo_root);
  }
  const auto resolved = canonical_parent(path) / std::filesystem::path(path).filename();
  if (is_inside(resolved, root)) {
    throw CaseContractError(
        kExitOutputPath, "output must resolve outside the repository: " + path);
  }
}

void write_raw_rgba8(const std::string& path, const std::vector<std::uint8_t>& bytes) {
  std::ofstream raw(path, std::ios::binary | std::ios::trunc);
  if (!raw) throw CaseContractError(kExitOutputPath, "cannot write " + path);
  raw.write(reinterpret_cast<const char*>(bytes.data()),
            static_cast<std::streamsize>(bytes.size()));
  raw.close();
  if (!raw) throw CaseContractError(kExitOutputPath, "cannot write " + path);
}

void write_text_file(const std::string& path, const std::string& text) {
  std::ofstream stream(path, std::ios::trunc);
  if (!stream) throw CaseContractError(kExitOutputPath, "cannot write " + path);
  stream << text;
  stream.close();
  if (!stream) throw CaseContractError(kExitOutputPath, "cannot write " + path);
}

std::string sha256_bytes(const std::vector<std::uint8_t>& bytes) {
  return graph::detail::sha256(
      std::string_view(reinterpret_cast<const char*>(bytes.data()), bytes.size()));
}

std::string refusal_record(std::string_view schema, const graph::GraphError& error) {
  std::string out = "{";
  out += "\"schema\":" + json_string(schema) + ",";
  out += "\"status\":\"refused\",";
  out += "\"code\":\"" + std::to_string(static_cast<unsigned>(error.code())) + "\",";
  out += "\"detail\":\"" + std::string(error.detail()) + "\",";
  out += "\"programKey\":\"" + std::string(error.program_key()) + "\"}";
  return out;
}

std::string refusal_record(std::string_view schema, const std::exception& error) {
  std::string out = "{";
  out += "\"schema\":" + json_string(schema) + ",";
  out += "\"status\":\"refused\",";
  out += "\"code\":\"exception\",\"detail\":\"" + std::string(error.what()) + "\"}";
  return out;
}

}  // namespace noisemaker::benchmark
