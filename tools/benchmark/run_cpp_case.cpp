// Authenticated C++ CPU runner for one corpus record.
//
// It is the byte-for-byte counterpart of tools/benchmark/run_cpu_case.mjs:
// same source bytes, same render options, raw top-down RGBA8 output, never a
// PNG and never a screenshot. Output paths must be absolute and outside the
// repository; the caller owns the scratch directory.
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

namespace {

[[noreturn]] void usage(std::string_view message) {
  std::cerr << "run_cpp_case: " << message << "\n"
            << "usage: run_cpp_case --source-file ABS --source-sha256 HEX"
               " --width N --height N --time D --frame N --seed D"
               " --rgba8-output ABS --metadata-output ABS\n";
  std::exit(2);
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
  for (const auto* path : {&source_path, &raw_output, &metadata_output}) {
    if (path->empty() || path->front() != '/') usage("absolute paths are required");
  }

  const std::string source = read_file(source_path);
  const auto actual_sha256 = noisemaker::graph::detail::sha256(source);
  if (actual_sha256 != expected_sha256) {
    std::cerr << "run_cpp_case: case source sha256 mismatch\n";
    return 3;
  }

  noisemaker::RenderOptions options;
  options.width = static_cast<std::size_t>(number(argument(args, "--width"), "--width"));
  options.height = static_cast<std::size_t>(number(argument(args, "--height"), "--height"));
  options.time = number(argument(args, "--time"), "--time");
  options.frame = static_cast<std::uint32_t>(number(argument(args, "--frame"), "--frame"));
  options.seed = number(argument(args, "--seed"), "--seed");

  noisemaker::Renderer renderer;
  std::vector<std::uint8_t> bytes;
  std::size_t width = 0;
  std::size_t height = 0;
  try {
    const auto result = renderer.render(source, options, source_path);
    bytes = result.to_rgba8();
    width = result.width();
    height = result.height();
  } catch (const noisemaker::graph::GraphError& error) {
    // A structured refusal is a first-class outcome: the caller records the
    // exact reason instead of a wrong image.
    std::cout << "{\"schema\":\"noisemaker-cpp.dsl-cpu-run.v1\",\"status\":\"refused\","
              << "\"code\":\"" << static_cast<unsigned>(error.code()) << "\","
              << "\"detail\":\"" << error.detail() << "\","
              << "\"programKey\":\"" << error.program_key() << "\"}\n";
    return 4;
  } catch (const std::exception& error) {
    std::cout << "{\"schema\":\"noisemaker-cpp.dsl-cpu-run.v1\",\"status\":\"refused\","
              << "\"code\":\"exception\",\"detail\":\"" << error.what() << "\"}\n";
    return 4;
  }

  std::ofstream raw(raw_output, std::ios::binary | std::ios::trunc);
  if (!raw) usage("cannot write " + raw_output);
  raw.write(reinterpret_cast<const char*>(bytes.data()),
            static_cast<std::streamsize>(bytes.size()));
  raw.close();

  const std::string digest = noisemaker::graph::detail::sha256(
      std::string_view(reinterpret_cast<const char*>(bytes.data()), bytes.size()));
  std::ostringstream metadata;
  metadata << "{\n  \"schema\": \"noisemaker-cpp.dsl-cpu-run.v1\",\n"
           << "  \"status\": \"rendered\",\n"
           << "  \"sourceSha256\": \"" << actual_sha256 << "\",\n"
           << "  \"width\": " << width << ",\n  \"height\": " << height << ",\n"
           << "  \"format\": \"rgba8\",\n  \"orientation\": \"top-down\",\n"
           << "  \"rgba8Sha256\": \"" << digest << "\",\n"
           << "  \"byteLength\": " << bytes.size() << "\n}\n";
  std::ofstream meta(metadata_output, std::ios::trunc);
  if (!meta) usage("cannot write " + metadata_output);
  meta << metadata.str();
  meta.close();
  std::cout << metadata.str();
  return 0;
}
