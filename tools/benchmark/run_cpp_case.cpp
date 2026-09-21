// Authenticated C++ CPU runner for one corpus record.
//
// It is the byte-for-byte counterpart of tools/benchmark/run_cpu_case.mjs:
// same source bytes, same render options, raw top-down RGBA8 output, never a
// PNG and never a screenshot. Output paths must be absolute and outside the
// repository; the caller owns the scratch directory.
//
// The compile/execute/refuse/write path is shared with the benchmark driver
// and the user-facing render CLI through corpus_case.{hpp,cpp}: one compile
// entry with `require_executable = true`, one `GraphExecutor::execute` call
// site, one refusal formatter and one rendered-record serializer. This file
// owns only its CLI.
#include "corpus_case.hpp"

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/renderer.hpp"
#include "noisemaker/surface.hpp"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace nb = noisemaker::benchmark;

namespace {

constexpr std::string_view kSchema = "noisemaker-cpp.dsl-cpu-run.v1";

[[noreturn]] void usage(std::string_view message) {
  std::cerr << "noisemaker-dsl-cpu-case: " << message << "\n"
            << "usage: noisemaker-dsl-cpu-case --source-file ABS --source-sha256 HEX"
               " --width N --height N --time D --frame N --seed D"
               " --rgba8-output ABS --metadata-output ABS"
               " [--record-id STRING] [--repo-root ABS]"
               " [--plan-relation-output ABS] [--float32-output ABS]"
               " [--external-texture NAME=WxH:HEX ...]\n";
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

// Every occurrence of a repeatable flag, in argument order -- unlike
// `argument()` above, which returns only the first. `--external-texture` is
// the one repeatable flag this driver accepts, mirroring how `record_flags`
// (tools/benchmark/corpus_lane.py) emits one `--external-texture` per entry
// in a corpus record's `externalTextures` list.
[[nodiscard]] std::vector<std::string> arguments_all(
    const std::vector<std::string>& args, std::string_view name) {
  std::vector<std::string> values;
  for (std::size_t index = 0; index + 1 < args.size(); ++index) {
    if (args[index] == name) values.push_back(args[index + 1]);
  }
  return values;
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

template <typename Integer>
[[nodiscard]] Integer whole_number(const std::string& text, std::string_view name,
                                   double minimum) {
  const double value = number(text, name);
  // size_t's maximum can round up to 2^N when represented as double. Use
  // that exact exclusive bound and reject invalid values before any cast.
  const double exclusive_upper = std::ldexp(1.0, std::numeric_limits<Integer>::digits);
  if (!std::isfinite(value) || value < minimum || value >= exclusive_upper ||
      value != std::trunc(value)) {
    usage(std::string(name) + (minimum == 0.0 ? " must be a nonnegative integer"
                                               : " must be a positive integer"));
  }
  return static_cast<Integer>(value);
}

[[nodiscard]] std::size_t positive_integer(const std::string& text, std::string_view name) {
  return whole_number<std::size_t>(text, name, 1.0);
}

[[nodiscard]] std::uint8_t hex_nibble(char digit, std::string_view spec) {
  if (digit >= '0' && digit <= '9') return static_cast<std::uint8_t>(digit - '0');
  if (digit >= 'a' && digit <= 'f') return static_cast<std::uint8_t>(digit - 'a' + 10);
  if (digit >= 'A' && digit <= 'F') return static_cast<std::uint8_t>(digit - 'A' + 10);
  usage("--external-texture " + std::string(spec) + " has non-hex byte data");
}

[[nodiscard]] std::vector<std::uint8_t> decode_hex_bytes(std::string_view hex,
                                                          std::string_view spec) {
  if (hex.size() % 2 != 0) {
    usage("--external-texture " + std::string(spec) + " has an odd number of hex digits");
  }
  std::vector<std::uint8_t> bytes;
  bytes.reserve(hex.size() / 2);
  for (std::size_t index = 0; index < hex.size(); index += 2) {
    const auto high = hex_nibble(hex[index], spec);
    const auto low = hex_nibble(hex[index + 1], spec);
    bytes.push_back(static_cast<std::uint8_t>((high << 4) | low));
  }
  return bytes;
}

// Parses one `--external-texture` value: `NAME=WIDTHxHEIGHT:HEXBYTES`, the
// same `{name, width, height, rgba8}` shape a corpus record's
// `externalTextures` entry carries (and the identical construction
// `run_cpu_case.mjs` performs: `api.Surface.fromRgba8(width, height, bytes)`
// off the record's own hex string) -- so `record_flags` can pass the exact
// same bytes to both lanes without either side decoding a PNG. Unlike
// `noisemaker-render`'s `--texture NAME=FILE` (a real file path, the right
// shape for a human at a terminal), this driver's inputs are always
// synthesized in-process by `tools/parity/sweep.py`/`corpus_lane.py`, so hex
// bytes inline in argv avoid a needless PNG round trip through a scratch
// file for every case.
[[nodiscard]] noisemaker::graph::NamedSurface parse_external_texture(
    const std::string& spec) {
  const auto name_end = spec.find('=');
  if (name_end == std::string::npos || name_end == 0) {
    usage("--external-texture must be NAME=WIDTHxHEIGHT:HEX, not \"" + spec + "\"");
  }
  const std::string name = spec.substr(0, name_end);
  const auto dims_and_hex = std::string_view(spec).substr(name_end + 1);
  const auto x_pos = dims_and_hex.find('x');
  const auto colon_pos = dims_and_hex.find(':');
  if (x_pos == std::string_view::npos || colon_pos == std::string_view::npos ||
      colon_pos < x_pos) {
    usage("--external-texture must be NAME=WIDTHxHEIGHT:HEX, not \"" + spec + "\"");
  }
  const std::string width_text(dims_and_hex.substr(0, x_pos));
  const std::string height_text(dims_and_hex.substr(x_pos + 1, colon_pos - x_pos - 1));
  const auto width = positive_integer(width_text, "--external-texture width");
  const auto height = positive_integer(height_text, "--external-texture height");
  if (width > std::numeric_limits<std::size_t>::max() / height ||
      width * height > std::numeric_limits<std::size_t>::max() / 4U ||
      height > noisemaker::kMaxSurfacePixels / width) {
    usage("--external-texture dimensions exceed surface limits");
  }
  const auto hex = dims_and_hex.substr(colon_pos + 1);
  const auto bytes = decode_hex_bytes(hex, spec);
  if (bytes.size() != width * height * 4U) {
    usage("--external-texture " + spec + " byte length does not match width*height*4");
  }
  noisemaker::Surface surface = noisemaker::Surface::from_rgba8(width, height, bytes);
  return noisemaker::graph::NamedSurface{name, std::move(surface)};
}

[[nodiscard]] std::vector<noisemaker::graph::NamedSurface> parse_external_textures(
    const std::vector<std::string>& args) {
  std::vector<noisemaker::graph::NamedSurface> textures;
  for (const auto& spec : arguments_all(args, "--external-texture")) {
    auto texture = parse_external_texture(spec);
    for (auto& existing : textures) {
      if (existing.name == texture.name) {
        usage("--external-texture " + texture.name + " was given more than once");
      }
    }
    textures.push_back(std::move(texture));
  }
  return textures;
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
  // Additive and opt-in, for tools/parity/sweep.py: the pre-quantization
  // float32 surface backing `to_rgba8()`, raw and untouched -- top-down RGBA
  // float32, width*height*4*4 bytes. Absent, behavior is unchanged.
  const auto float32_output = argument(args, "--float32-output", false);
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
    if (!float32_output.empty()) {
      nb::require_external_output_path(float32_output, repo_root);
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "noisemaker-dsl-cpu-case: " << error.what() << "\n";
    return error.exit_code();
  }

  const std::string source = read_file(source_path);
  const auto actual_sha256 = noisemaker::graph::detail::sha256(source);
  if (actual_sha256 != expected_sha256) {
    std::cerr << "noisemaker-dsl-cpu-case: case source sha256 mismatch\n";
    return nb::kExitSourceDigestMismatch;
  }

  noisemaker::RenderOptions options;
  options.width = positive_integer(argument(args, "--width"), "--width");
  options.height = positive_integer(argument(args, "--height"), "--height");
  options.time = number(argument(args, "--time"), "--time");
  options.frame = whole_number<std::uint32_t>(argument(args, "--frame"), "--frame", 0.0);
  options.seed = number(argument(args, "--seed"), "--seed");
  options.external_textures = parse_external_textures(args);

  std::vector<std::uint8_t> bytes;
  std::vector<std::uint8_t> float32_bytes;
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
    if (!float32_output.empty()) {
      const auto surface_data = result.surface.data();
      const auto* begin = reinterpret_cast<const std::uint8_t*>(surface_data.data());
      float32_bytes.assign(begin, begin + surface_data.size() * sizeof(float));
    }
    if (!relation_output.empty()) {
      const auto relation = nb::project_relation(
          plan, result, record_id.empty() ? source_path : record_id, actual_sha256,
          options.width, options.height);
      relation_document = nb::serialize_relation(relation, 0) + "\n";
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "noisemaker-dsl-cpu-case: " << error.what() << "\n";
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

  // The shared serializer, not a second one: `noisemaker-render` emits the
  // identical document from the identical call, so the two cannot drift.
  const std::string metadata = nb::rendered_record(
      kSchema, actual_sha256, width, height, nb::sha256_bytes(bytes), bytes.size());
  try {
    nb::write_raw_rgba8(raw_output, bytes);
    if (!relation_output.empty()) nb::write_text_file(relation_output, relation_document);
    if (!float32_output.empty()) nb::write_raw_rgba8(float32_output, float32_bytes);
    nb::write_text_file(metadata_output, metadata);
  } catch (const nb::CaseContractError& error) {
    std::cerr << "noisemaker-dsl-cpu-case: " << error.what() << "\n";
    return error.exit_code();
  }
  std::cout << metadata;
  return nb::kExitOk;
}
