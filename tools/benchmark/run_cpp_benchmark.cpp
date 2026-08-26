// Authenticated C++ CPU benchmark driver for one corpus record.
//
// It renders exactly what `run_cpp_case` renders, from the same authenticated
// source bytes and the same options, through the same real
// `graph::GraphExecutor`. What it adds is a timing protocol with a hard fence:
// the registry build, the compile, the correctness execution, the relation
// projection, the RGBA8 extraction, the hashing, and every file write are all
// outside the measured region.
//
// Correctness blocks; performance only reports. A byte or plan divergence
// exits nonzero. No timing number gates anything, here or in the harness.
#include "corpus_case.hpp"

#include "noisemaker/renderer.hpp"

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace nb = noisemaker::benchmark;

namespace {

constexpr std::string_view kSchema = "noisemaker-cpp.cpu-benchmark-result.v1";
constexpr std::string_view kRefusalSchema = "noisemaker-cpp.dsl-cpu-run.v1";
constexpr std::size_t kMinimumWarmups = 5;
constexpr std::size_t kMinimumSamples = 30;

#ifndef NOISEMAKER_BENCHMARK_FLAGS
#error "NOISEMAKER_BENCHMARK_FLAGS must be supplied by the build so the record cannot claim flags the target was not built with"
#endif
#ifndef NOISEMAKER_BENCHMARK_BUILD_TYPE
#error "NOISEMAKER_BENCHMARK_BUILD_TYPE must be supplied by the build"
#endif

constexpr std::string_view kDescription = R"(noisemaker-dsl-cpu-benchmark
  --source-file ABS            DSL source bytes, exactly as the record carries them
  --source-sha256 HEX64        record.sourceSha256; mismatch is fatal before any work
  --record-id STRING           record.id, copied verbatim into the emitted record
  --width N --height N         record.options.width / .height
  --time D --frame N --seed D  record.options.time / .frame / .seed
  --one-shot ready|continuous  record.options.oneShot, asserted, never inferred
  --render-scale D             record.options.renderScale, must be exactly 1
  --timing-mode render_only|compile_and_render
  --warmups N                  >= 5
  --samples N                  >= 30
  --repo-root ABS              the checkout; every path must fall outside it
  --rgba8-output ABS           raw top-down RGBA8, written only on success
  --benchmark-output ABS       the benchmark record
  [--plan-relation-output ABS] relation alone, for cross-lane diffing
  [--describe]                 print this contract and exit 0

exit 0 rendered and measured; 2 usage; 3 source sha256 mismatch;
     4 refused (structured refusal on stdout); 5 plan authentication failure;
     6 output-path contract violation
schema noisemaker-cpp.cpu-benchmark-result.v1
relation noisemaker-cpp.plan-relation.v1
timing render_only times GraphExecutor::execute on one compiled plan;
     compile_and_render times Renderer::render, the only JS-comparable mode
no PNG, no screenshot, no epsilon, no tolerance, no seeded-RNG flag,
no seed-surface flag
)";

[[noreturn]] void usage(std::string_view message) {
  std::cerr << "run_cpp_benchmark: " << message << "\n" << kDescription;
  std::exit(nb::kExitUsage);
}

class Arguments final {
 public:
  Arguments(int argc, char** argv) {
    const std::vector<std::string> tokens(argv + 1, argv + argc);
    std::size_t index = 0;
    while (index < tokens.size()) {
      const std::string& token = tokens[index];
      if (token.rfind("--", 0) != 0) usage("unexpected positional argument " + token);
      if (token == "--describe") {
        if (tokens.size() != 1) usage("--describe accepts no other flag");
        std::cout << kDescription;
        std::exit(nb::kExitOk);
      }
      if (index + 1 >= tokens.size()) usage(token + " requires a value");
      if (!known(token)) usage("unknown flag " + token);
      if (values_.count(token) != 0) usage("duplicate flag " + token);
      values_.emplace(token, tokens[index + 1]);
      index += 2;
    }
  }

  [[nodiscard]] std::string required(std::string_view name) const {
    const auto found = values_.find(std::string(name));
    if (found == values_.end()) usage(std::string(name) + " is required");
    return found->second;
  }

  [[nodiscard]] std::string optional(std::string_view name,
                                     std::string fallback = {}) const {
    const auto found = values_.find(std::string(name));
    return found == values_.end() ? fallback : found->second;
  }

 private:
  [[nodiscard]] static bool known(const std::string& name) {
    // A closed set. An unrecognized flag is a contract violation, never a
    // silently ignored token: a `--seed-surface` or a `--tolerance` that the
    // driver quietly dropped would produce a number for something other than
    // the case the harness asked for.
    static const std::vector<std::string> kKnown = {
        "--source-file",   "--source-sha256", "--record-id",
        "--width",         "--height",        "--time",
        "--frame",         "--seed",          "--one-shot",
        "--render-scale",  "--timing-mode",   "--warmups",
        "--samples",       "--repo-root",     "--rgba8-output",
        "--benchmark-output", "--plan-relation-output"};
    for (const auto& candidate : kKnown) {
      if (candidate == name) return true;
    }
    return false;
  }

  std::map<std::string, std::string> values_;
};

[[nodiscard]] double number(const std::string& text, std::string_view name) {
  try {
    std::size_t consumed = 0;
    const double value = std::stod(text, &consumed);
    if (consumed != text.size()) usage(std::string(name) + " is not a number");
    return value;
  } catch (const std::exception&) {
    usage(std::string(name) + " is not a number");
  }
}

[[nodiscard]] std::size_t count(const std::string& text, std::string_view name,
                                std::size_t floor) {
  const double value = number(text, name);
  if (value < 0.0 || value != static_cast<double>(static_cast<std::size_t>(value))) {
    usage(std::string(name) + " must be a nonnegative integer");
  }
  const auto parsed = static_cast<std::size_t>(value);
  if (parsed < floor) {
    usage(std::string(name) + " must be at least " + std::to_string(floor));
  }
  return parsed;
}

[[nodiscard]] std::string read_file(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) usage("cannot read " + path);
  return std::string(std::istreambuf_iterator<char>(stream),
                     std::istreambuf_iterator<char>());
}

[[nodiscard]] std::string samples_array(const std::vector<std::uint64_t>& samples) {
  std::string out = "[";
  for (std::size_t index = 0; index < samples.size(); ++index) {
    if (index != 0) out.append(", ");
    out.append(std::to_string(samples[index]));
  }
  out.push_back(']');
  return out;
}

[[nodiscard]] std::string platform_block() {
  std::string compiler = "unknown";
  std::string compiler_version = "unknown";
#if defined(__apple_build_version__)
  compiler = "AppleClang";
  compiler_version = __clang_version__;
#elif defined(__clang__)
  compiler = "Clang";
  compiler_version = __clang_version__;
#elif defined(__GNUC__)
  compiler = "GNU";
  compiler_version = __VERSION__;
#endif
  std::string out = "{\n";
  out += "    \"driver\": " + nb::json_string("cpp-cpu") + ",\n";
  out += "    \"os\": " + nb::json_string(
#if defined(__APPLE__)
                              "darwin"
#elif defined(__linux__)
                              "linux"
#else
                              "unknown"
#endif
                              ) + ",\n";
  out += "    \"arch\": " + nb::json_string(
#if defined(__aarch64__) || defined(_M_ARM64)
                                "arm64"
#elif defined(__x86_64__) || defined(_M_X64)
                                "x86_64"
#else
                                "unknown"
#endif
                                ) + ",\n";
  out += "    \"runtime\": " + nb::json_string("native") + ",\n";
  out += "    \"compiler\": " + nb::json_string(compiler) + ",\n";
  out += "    \"compilerVersion\": " + nb::json_string(compiler_version) + ",\n";
  out += "    \"cxxStandard\": " + std::to_string(__cplusplus) + ",\n";
  out += "    \"flags\": " + nb::json_string(NOISEMAKER_BENCHMARK_FLAGS) + ",\n";
  out += "    \"buildType\": " + nb::json_string(NOISEMAKER_BENCHMARK_BUILD_TYPE) + "\n";
  out += "  }";
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  const Arguments args(argc, argv);

  const auto repo_root = args.required("--repo-root");
  if (repo_root.empty() || repo_root.front() != '/') usage("--repo-root must be absolute");
  const auto source_path = args.required("--source-file");
  const auto expected_sha256 = args.required("--source-sha256");
  const auto record_id = args.required("--record-id");
  const auto raw_output = args.required("--rgba8-output");
  const auto benchmark_output = args.required("--benchmark-output");
  const auto relation_output = args.optional("--plan-relation-output");

  const auto timing_mode = args.required("--timing-mode");
  if (timing_mode != "render_only" && timing_mode != "compile_and_render") {
    usage("--timing-mode must be render_only or compile_and_render");
  }
  const bool render_only = timing_mode == "render_only";

  const auto one_shot = args.required("--one-shot");
  if (one_shot != "ready" && one_shot != "continuous") {
    usage("--one-shot must be ready or continuous");
  }
  if (one_shot != "ready") {
    // Every admitted record is `ready` today. Rendering a `continuous` record
    // as if it were `ready` would be wrong bytes wearing a benchmark number,
    // so the driver stops instead.
    usage("--one-shot continuous is not executable by this port");
  }
  const auto render_scale = number(args.required("--render-scale"), "--render-scale");
  if (render_scale != 1.0) usage("--render-scale must be exactly 1");

  const auto warmups = count(args.required("--warmups"), "--warmups", kMinimumWarmups);
  const auto samples = count(args.required("--samples"), "--samples", kMinimumSamples);

  // Path contract first: nothing is read, built, compiled, or executed until
  // every path is proven absolute, non-symlink, and outside the checkout.
  try {
    for (const auto* path : {&source_path, &raw_output, &benchmark_output}) {
      nb::require_external_output_path(*path, repo_root);
    }
    if (!relation_output.empty()) {
      nb::require_external_output_path(relation_output, repo_root);
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_benchmark: " << error.what() << "\n";
    return error.exit_code();
  }

  const std::string source = read_file(source_path);
  const auto actual_sha256 = noisemaker::graph::detail::sha256(source);
  if (actual_sha256 != expected_sha256) {
    std::cerr << "run_cpp_benchmark: case source sha256 mismatch\n";
    return nb::kExitSourceDigestMismatch;
  }

  noisemaker::RenderOptions options;
  options.width = static_cast<std::size_t>(number(args.required("--width"), "--width"));
  options.height = static_cast<std::size_t>(number(args.required("--height"), "--height"));
  options.time = number(args.required("--time"), "--time");
  options.frame = static_cast<std::uint32_t>(number(args.required("--frame"), "--frame"));
  options.seed = number(args.required("--seed"), "--seed");
  options.one_shot = true;
  if (options.width == 0 || options.height == 0) usage("--width and --height must be positive");

  using Clock = std::chrono::steady_clock;

  // [fenced] registry construction. It costs tens of milliseconds, dozens of
  // times a single render at corpus extent, so it can never sit inside a
  // sample.
  const auto setup_started = Clock::now();
  const auto registry = nb::build_registry();
  const auto setup_ns = static_cast<std::uint64_t>(
      std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - setup_started).count());

  std::uint64_t compile_ns = 0;
  std::vector<std::uint64_t> sample_ns;
  sample_ns.reserve(samples);
  std::vector<std::uint8_t> bytes;
  std::size_t width = 0;
  std::size_t height = 0;
  std::string final_route;
  std::size_t pass_count = 0;
  nb::PlanRelation relation;
  nb::PlanIdentity identity;
  nb::CaseProvenance provenance;

  try {
    // [TIMED once] the single compile. In render_only this is the only
    // compile the process performs.
    const auto compile_started = Clock::now();
    auto plan = nb::compile_case(source, registry, record_id, actual_sha256);
    compile_ns = static_cast<std::uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - compile_started).count());

    identity = nb::project_identity(plan);
    provenance = nb::project_provenance(plan);

    // [fenced, MANDATORY] the untimed correctness execution. Refusals are
    // execute-time, never compile-time: all 166 admitted records compile, and
    // the 16 non-rendering ones throw `GraphError` out of
    // `GraphExecutor::execute`. Without this pass, a refusal would land inside
    // the timed region and produce a crash or a meaningless sample.
    const auto reference = nb::execute_case(plan, options);
    bytes = reference.surface.to_rgba8();
    width = reference.surface.width();
    height = reference.surface.height();
    final_route = reference.final_route;
    pass_count = reference.pass_count;
    relation = nb::project_relation(plan, reference, record_id, actual_sha256,
                                    options.width, options.height);

    if (render_only) {
      for (std::size_t index = 0; index < warmups; ++index) {
        const auto discarded = nb::execute_case(plan, options);
        (void)discarded;
      }
      for (std::size_t index = 0; index < samples; ++index) {
        const auto started = Clock::now();
        // Nothing but the authenticated dispatch is inside the clock pair: no
        // to_rgba8, no hashing, no output allocation.
        const auto measured = nb::execute_case(plan, options);
        const auto elapsed = Clock::now() - started;
        sample_ns.push_back(static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count()));
        (void)measured;
      }
    } else {
      // The JS CPU authority has no plan-accepting render entry, so the only
      // honest cross-lane mode recompiles per sample through the public API.
      const noisemaker::Renderer renderer{nb::build_registry()};
      for (std::size_t index = 0; index < warmups; ++index) {
        const auto discarded = renderer.render(source, options, record_id);
        (void)discarded;
      }
      for (std::size_t index = 0; index < samples; ++index) {
        const auto started = Clock::now();
        const auto measured = renderer.render(source, options, record_id);
        const auto elapsed = Clock::now() - started;
        sample_ns.push_back(static_cast<std::uint64_t>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count()));
        (void)measured;
      }
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_benchmark: " << error.what() << "\n";
    return error.exit_code();
  } catch (const noisemaker::graph::GraphError& error) {
    std::cout << nb::refusal_record(kRefusalSchema, error) << "\n";
    return nb::kExitRefused;
  } catch (const std::exception& error) {
    std::cout << nb::refusal_record(kRefusalSchema, error) << "\n";
    return nb::kExitRefused;
  }

  const auto summary = nb::summarize(sample_ns, options.width * options.height);
  const auto digest = nb::sha256_bytes(bytes);
  const std::size_t compile_count = render_only ? 1 : (warmups + samples + 1);

  std::string document = "{\n";
  document += "  \"schema\": " + nb::json_string(kSchema) + ",\n";
  document += "  \"program\": {\n";
  document += "    \"id\": " + nb::json_string(record_id) + ",\n";
  document += "    \"sourceSha256\": " + nb::json_string(actual_sha256) + ",\n";
  document += "    \"width\": " + nb::json_number(options.width) + ",\n";
  document += "    \"height\": " + nb::json_number(options.height) + ",\n";
  document += "    \"options\": {\"width\": " + nb::json_number(options.width) +
              ", \"height\": " + nb::json_number(options.height) +
              ", \"time\": " + nb::json_double(options.time) +
              ", \"frame\": " + nb::json_number(static_cast<std::size_t>(options.frame)) +
              ", \"seed\": " + nb::json_double(options.seed) +
              ", \"oneShot\": " + nb::json_string(one_shot) +
              ", \"renderScale\": " + nb::json_double(render_scale) + "}\n";
  document += "  },\n";
  document += "  \"provenance\": {\n";
  document += "    \"cpuBehavioralLock\": " + nb::json_string(provenance.cpu_behavioral_lock) + ",\n";
  document += "    \"sourceLockSha256\": " + nb::json_string(provenance.source_lock_sha256) + ",\n";
  document += "    \"upstreamRevision\": " + nb::json_string(provenance.upstream_revision) + ",\n";
  document += "    \"upstreamTree\": " + nb::json_string(provenance.upstream_tree) + ",\n";
  document += "    \"catalogPayloadSha256\": " + nb::json_string(provenance.catalog_payload_sha256) + "\n";
  document += "  },\n";
  document += "  \"platform\": " + platform_block() + ",\n";
  document += "  \"mode\": " + nb::json_string(timing_mode) + ",\n";
  document += "  \"warmups\": " + nb::json_number(warmups) + ",\n";
  document += "  \"samples\": " + nb::json_number(samples) + ",\n";
  document += "  \"compileCount\": " + nb::json_number(compile_count) + ",\n";
  document += "  \"compileNs\": " + nb::json_number(compile_ns) + ",\n";
  document += "  \"setupNs\": " + nb::json_number(setup_ns) + ",\n";
  document += "  \"sampleNs\": " + samples_array(sample_ns) + ",\n";
  document += "  \"summary\": {\"minNs\": " + nb::json_number(summary.min_ns) +
              ", \"medianNs\": " + nb::json_number(summary.median_ns) +
              ", \"p95Ns\": " + nb::json_number(summary.p95_ns) +
              ", \"maxNs\": " + nb::json_number(summary.max_ns) +
              ", \"pixels\": " + nb::json_number(summary.pixels) +
              ", \"megapixelsPerSecond\": " + nb::json_double(summary.megapixels_per_second) + "},\n";
  document += "  \"output\": {\"width\": " + nb::json_number(width) +
              ", \"height\": " + nb::json_number(height) +
              ", \"format\": \"rgba8\", \"orientation\": \"top-down\"" +
              ", \"byteLength\": " + nb::json_number(bytes.size()) +
              ", \"rgba8Sha256\": " + nb::json_string(digest) + "},\n";
  document += "  \"planRelation\": " + nb::serialize_relation(relation, 2) + ",\n";
  document += "  \"planIdentity\": {\n";
  document += "    \"planPayloadSha256\": " + nb::json_string(identity.plan_payload_sha256) + ",\n";
  document += "    \"provenanceSourceSha256\": " + nb::json_string(identity.provenance_source_sha256) + ",\n";
  document += "    \"provenanceSourceName\": " + nb::json_string(identity.provenance_source_name) + ",\n";
  document += std::string("    \"requireExecutable\": ") + (identity.require_executable ? "true" : "false") + ",\n";
  document += std::string("    \"executable\": ") + (identity.executable ? "true" : "false") + ",\n";
  document += "    \"snapshotCount\": " + nb::json_number(identity.snapshot_count) + ",\n";
  document += std::string("    \"validated\": ") + (identity.validated ? "true" : "false") + "\n";
  document += "  },\n";
  document += "  \"correctness\": {\"status\": \"rendered\", \"finalRoute\": " +
              nb::json_string(final_route) +
              ", \"passCount\": " + nb::json_number(pass_count) + "}\n";
  document += "}\n";

  try {
    // The raw frame is opened only now, after a successful correctness
    // execution, so a refusal can never leave a partial file behind.
    nb::write_raw_rgba8(raw_output, bytes);
    if (!relation_output.empty()) {
      nb::write_text_file(relation_output, nb::serialize_relation(relation, 0) + "\n");
    }
    nb::write_text_file(benchmark_output, document);
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_benchmark: " << error.what() << "\n";
    return error.exit_code();
  }
  std::cout << document;
  return nb::kExitOk;
}
