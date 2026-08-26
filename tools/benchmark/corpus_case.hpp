#pragma once
// The one C++ execution path every corpus driver shares.
//
// Both `run_cpp_case.cpp` (the parity driver) and `run_cpp_benchmark.cpp` (the
// timing driver) compile this translation unit, so there is exactly one
// compile entry, one executor call site, one refusal formatter, one relation
// projection, and one raw-RGBA8 writer. Nothing here parses or emits JSON with
// a library: the serializers below are narrow and owned, so the C++ side never
// grows a general JSON dependency.
#include "noisemaker/effects/registry.hpp"
#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/executor.hpp"

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace noisemaker::benchmark {

// Exit codes are part of the driver contract; the harness classifies on them.
inline constexpr int kExitOk = 0;
inline constexpr int kExitUsage = 2;
inline constexpr int kExitSourceDigestMismatch = 3;
inline constexpr int kExitRefused = 4;
inline constexpr int kExitPlanAuthentication = 5;
inline constexpr int kExitOutputPath = 6;

// A contract violation that carries the exit code the driver must return.
// Distinct from `graph::GraphError`: a refusal is the program's answer, while
// this is the driver refusing to proceed.
class CaseContractError final : public std::runtime_error {
 public:
  CaseContractError(int exit_code, const std::string& message)
      : std::runtime_error(message), exit_code_(exit_code) {}
  [[nodiscard]] int exit_code() const noexcept { return exit_code_; }

 private:
  int exit_code_;
};

// The normalized, cross-lane comparable projection of one execution. Every
// field here was measured to agree between the JS CPU authority's compiled
// plan and this executor's `ExecutionPlan` over all 166 admitted records.
struct PlanRelation {
  std::string schema;
  std::string record_id;
  std::string source_sha256;
  std::vector<std::string> step_kinds;
  std::vector<std::string> effect_ids;
  std::vector<std::string> pass_keys;
  std::vector<std::string> pass_formats;
  std::vector<std::string> reads;
  std::vector<std::string> routes;
  std::string final_surface;
  std::size_t width = 0;
  std::size_t height = 0;
  std::size_t pass_count = 0;
  std::string relation_sha256;
};

// C++-lane plan provenance. Recorded, never compared across lanes: it is the
// canonical payload identity of *this* compiler, and `require_executable` is
// inside that payload.
struct PlanIdentity {
  std::string plan_payload_sha256;
  std::string provenance_source_sha256;
  std::string provenance_source_name;
  bool require_executable = false;
  bool executable = false;
  std::size_t snapshot_count = 0;
  bool validated = false;
};

// The catalog provenance a benchmark record carries so a number can always be
// traced back to the authority the bytes were validated against.
struct CaseProvenance {
  std::string cpu_behavioral_lock;
  std::string source_lock_sha256;
  std::string upstream_revision;
  std::string upstream_tree;
  std::string catalog_payload_sha256;
};

struct TimingSummary {
  std::uint64_t min_ns = 0;
  std::uint64_t median_ns = 0;
  std::uint64_t p95_ns = 0;
  std::uint64_t max_ns = 0;
  std::size_t pixels = 0;
  double megapixels_per_second = 0.0;
};

// ---------------------------------------------------------------------------
// Narrow owned serializers.
//
// These deliberately return `std::string` rather than streaming into an
// ostream. A `void quoted(const std::string&)` helper is silently out-competed
// by `std::quoted` through ADL at some call sites and emits syntactically
// valid JSON with empty contents, which is far worse than a compile error.
// ---------------------------------------------------------------------------
[[nodiscard]] std::string json_string(std::string_view value);
[[nodiscard]] std::string json_array(const std::vector<std::string>& values);
[[nodiscard]] std::string json_number(std::size_t value);
[[nodiscard]] std::string json_number(std::uint64_t value);
[[nodiscard]] std::string json_double(double value);

// ---------------------------------------------------------------------------
// The shared execution path.
// ---------------------------------------------------------------------------

// The one registry construction. Costly (tens of milliseconds) relative to a
// render, which is exactly why every driver fences it out of its timing.
[[nodiscard]] effects::EffectRegistry build_registry();

// The one compile entry. `require_executable` is hardcoded true because it is
// written into the canonical plan payload: compiling the identical source
// bytes with the default `CompileOptions{}` produces a *different*
// `plan_payload_sha256`, and that difference is invisible in the rendered
// pixels. Throws `CaseContractError(kExitPlanAuthentication)` when the plan
// fails `validate_execution_plan()` or when its provenance source digest is
// not the authenticated source digest.
[[nodiscard]] graph::ExecutionPlan compile_case(
    std::string_view source, const effects::EffectRegistry& registry,
    std::string_view source_name, std::string_view authenticated_source_sha256);

// The sole dispatch seam. Route authentication, define contracts, and
// preflight-before-copy all stay inside `graph::GraphExecutor::execute`; there
// is no bypass here and no second call site anywhere in tools/benchmark.
[[nodiscard]] graph::ExecutionResult execute_case(const graph::ExecutionPlan& plan,
                                                  const graph::ExecutionInputs& inputs);

[[nodiscard]] PlanIdentity project_identity(const graph::ExecutionPlan& plan);
[[nodiscard]] CaseProvenance project_provenance(const graph::ExecutionPlan& plan);

// Projects the cross-lane relation. `pass_keys` come from
// `PassAdmission::identity::program_key` (`<effectId>:<program>`); the JS lane
// must key on `pass.program` and never on `pass.name` -- e.g.
// `classicNoisedeck/bitEffects` carries `name:"render"` and
// `program:"bitEffects"`, and keying on the name diverges on every record.
[[nodiscard]] PlanRelation project_relation(const graph::ExecutionPlan& plan,
                                            const graph::ExecutionResult& result,
                                            std::string_view record_id,
                                            std::string_view source_sha256,
                                            std::size_t width, std::size_t height);

// The canonical pre-hash byte stream of a relation, excluding
// `relation_sha256` itself. Field order and separators are the cross-lane
// contract; the JS and Python lanes reproduce this byte-for-byte.
[[nodiscard]] std::string canonical_relation_bytes(const PlanRelation& relation);
[[nodiscard]] std::string serialize_relation(const PlanRelation& relation, int indent);

[[nodiscard]] TimingSummary summarize(const std::vector<std::uint64_t>& samples,
                                      std::size_t pixels);

// Every driver output path must be absolute, must not already exist as a
// symlink, and -- when a repository root is supplied -- must resolve outside
// it. Raw frames landing inside the checkout is exactly what the corpus
// procedure forbids, so the guard lives in the shared writer rather than in
// each driver's argv handling.
void require_external_output_path(const std::string& path, const std::string& repo_root);
void write_raw_rgba8(const std::string& path, const std::vector<std::uint8_t>& bytes);
void write_text_file(const std::string& path, const std::string& text);

[[nodiscard]] std::string sha256_bytes(const std::vector<std::uint8_t>& bytes);

// The structured refusal both drivers print on stdout, byte-identical between
// them so the harness needs exactly one parser.
[[nodiscard]] std::string refusal_record(std::string_view schema,
                                         const graph::GraphError& error);
[[nodiscard]] std::string refusal_record(std::string_view schema,
                                         const std::exception& error);

}  // namespace noisemaker::benchmark
