// Authenticated C++ CPU runner for one corpus record.
//
// It is the byte-for-byte counterpart of tools/benchmark/run_cpu_case.mjs:
// same source bytes, same render options, raw top-down RGBA8 output, never a
// PNG and never a screenshot. Output paths must be absolute and outside the
// repository; the caller owns the scratch directory.
//
// The compile/execute/refuse/write path is shared with the benchmark driver
// through corpus_case.{hpp,cpp}: one compile entry with
// `require_executable = true`, one `GraphExecutor::execute` call site, one
// refusal formatter. This file owns only its CLI and its frozen metadata
// document.
#include "corpus_case.hpp"

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/renderer.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace nb = noisemaker::benchmark;

namespace {

constexpr std::string_view kSchema = "noisemaker-cpp.dsl-cpu-run.v1";

[[noreturn]] void usage(std::string_view message) {
  std::cerr << "run_cpp_case: " << message << "\n"
            << "usage: run_cpp_case --source-file ABS --source-sha256 HEX"
               " --width N --height N --time D --frame N --seed D"
               " --rgba8-output ABS --metadata-output ABS"
               " [--record-id STRING] [--repo-root ABS]"
               " [--plan-relation-output ABS]\n";
  std::exit(nb::kExitUsage);
}

[[nodiscard]] std::string read_file(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) usage("cannot read " + path);
  return std::string(std::istreambuf_iterator<char>(stream),
                     std::istreambuf_iterator<char>());
}

[[nodiscard]] std::string argument(const std::vector<std::string>& args,
                                   std::string_view name, bool required = true) {
  for (std::size_t index = 0; index + 1 < args.size(); ++index) {
    if (args[index] == name) return args[index + 1];
  }
  if (required) usage(std::string(name) + " is required");
  return {};
}

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

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  const auto source_path = argument(args, "--source-file");
  const auto expected_sha256 = argument(args, "--source-sha256");
  const auto raw_output = argument(args, "--rgba8-output");
  const auto metadata_output = argument(args, "--metadata-output");
  // Additive and opt-in. Absent, this driver behaves exactly as it did before
  // the benchmark lane existed, which is how the frozen parity harness calls
  // it.
  const auto record_id = argument(args, "--record-id", false);
  const auto repo_root = argument(args, "--repo-root", false);
  const auto relation_output = argument(args, "--plan-relation-output", false);
  for (const auto* path : {&source_path, &raw_output, &metadata_output}) {
    if (path->empty() || path->front() != '/') usage("absolute paths are required");
  }
  try {
    for (const auto* path : {&raw_output, &metadata_output}) {
      nb::require_external_output_path(*path, repo_root);
    }
    if (!relation_output.empty()) {
      nb::require_external_output_path(relation_output, repo_root);
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_case: " << error.what() << "\n";
    return error.exit_code();
  }

  const std::string source = read_file(source_path);
  const auto actual_sha256 = noisemaker::graph::detail::sha256(source);
  if (actual_sha256 != expected_sha256) {
    std::cerr << "run_cpp_case: case source sha256 mismatch\n";
    return nb::kExitSourceDigestMismatch;
  }

  noisemaker::RenderOptions options;
  options.width = static_cast<std::size_t>(number(argument(args, "--width"), "--width"));
  options.height = static_cast<std::size_t>(number(argument(args, "--height"), "--height"));
  options.time = number(argument(args, "--time"), "--time");
  options.frame = static_cast<std::uint32_t>(number(argument(args, "--frame"), "--frame"));
  options.seed = number(argument(args, "--seed"), "--seed");

  std::vector<std::uint8_t> bytes;
  std::size_t width = 0;
  std::size_t height = 0;
  std::string relation_document;
  try {
    const auto registry = nb::build_registry();
    const auto plan = nb::compile_case(source, registry, source_path, actual_sha256);
    const auto result = nb::execute_case(plan, options);
    bytes = result.surface.to_rgba8();
    width = result.surface.width();
    height = result.surface.height();
    if (!relation_output.empty()) {
      const auto relation = nb::project_relation(
          plan, result, record_id.empty() ? source_path : record_id, actual_sha256,
          options.width, options.height);
      relation_document = nb::serialize_relation(relation, 0) + "\n";
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_case: " << error.what() << "\n";
    return error.exit_code();
  } catch (const noisemaker::graph::GraphError& error) {
    // A structured refusal is a first-class outcome: the caller records the
    // exact reason instead of a wrong image.
    std::cout << nb::refusal_record(kSchema, error) << "\n";
    return nb::kExitRefused;
  } catch (const std::exception& error) {
    std::cout << nb::refusal_record(kSchema, error) << "\n";
    return nb::kExitRefused;
  }

  const std::string digest = nb::sha256_bytes(bytes);
  std::ostringstream metadata;
  metadata << "{\n  \"schema\": \"noisemaker-cpp.dsl-cpu-run.v1\",\n"
           << "  \"status\": \"rendered\",\n"
           << "  \"sourceSha256\": \"" << actual_sha256 << "\",\n"
           << "  \"width\": " << width << ",\n  \"height\": " << height << ",\n"
           << "  \"format\": \"rgba8\",\n  \"orientation\": \"top-down\",\n"
           << "  \"rgba8Sha256\": \"" << digest << "\",\n"
           << "  \"byteLength\": " << bytes.size() << "\n}\n";
  try {
    nb::write_raw_rgba8(raw_output, bytes);
    if (!relation_output.empty()) nb::write_text_file(relation_output, relation_document);
    nb::write_text_file(metadata_output, metadata.str());
  } catch (const nb::CaseContractError& error) {
    std::cerr << "run_cpp_case: " << error.what() << "\n";
    return error.exit_code();
  }
  std::cout << metadata.str();
  return nb::kExitOk;
}
