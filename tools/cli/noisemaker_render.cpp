// noisemaker-render — render a Noisemaker DSL program to a PNG.
//
// This is the user-facing entry point. It is deliberately forgiving about the
// things a person gets wrong (relative paths, omitted options, an omitted
// output name) and deliberately unforgiving about the thing that matters: it
// renders through the *same* library route the corpus harness drives, so a
// picture produced here is the picture the parity lane validates.
//
// One code path. Compile, execute and RGBA8 extraction all go through
// `tools/benchmark/corpus_case.{hpp,cpp}` — the same `compile_case`
// (`require_executable = true`), the same single `GraphExecutor::execute` call
// site, the same byte writer and the same SHA-256 helper that
// `noisemaker-dsl-cpu-case` and `noisemaker-dsl-cpu-benchmark` use. Nothing
// about rendering is reimplemented here; this file owns only its CLI, its help
// text and its human-readable refusal formatting.
//
// Input authentication is a harness concern, not a user concern: there is no
// `--source-sha256` flag. The harness driver keeps it because a corpus record
// must prove it ran the bytes it claims to have run. A person rendering their
// own file already knows which file they wrote.
#include "corpus_case.hpp"

#include "noisemaker/effects/catalog.hpp"
#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/png.hpp"
#include "noisemaker/renderer.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace nb = noisemaker::benchmark;

namespace {

// The same schema and the same field set the harness driver emits, so a
// consumer of `--metadata` parses one document shape regardless of which
// binary produced it. `tests/test_render_cli.py` renders one program through
// both binaries and asserts the two documents are byte-identical, so the
// schema cannot drift apart unnoticed.
constexpr std::string_view kMetadataSchema = "noisemaker-cpp.dsl-cpu-run.v1";

constexpr std::string_view kHelp =
    R"(noisemaker-render — render a Noisemaker DSL program to a PNG.

usage:
  noisemaker-render PROGRAM.dsl [options]
  noisemaker-render --list-effects
  noisemaker-render --help

Renders PROGRAM.dsl and writes a PNG. With no options at all it renders
512x512 at time 0, frame 0, seed 1, and writes the program's own name with a
.png extension into the current directory. Paths may be relative.

options:
  -o, --output PATH     PNG to write (default: the program's basename + .png)
      --width N         pixels across (default: 512)
      --height N        pixels down (default: 512)
      --time D          animation time in seconds (default: 0)
      --frame N         frame counter (default: 0)
      --seed D          seed (default: 1)
      --raw-rgba8 PATH  also write the raw top-down RGBA8 bytes
      --metadata PATH   also write a JSON document describing the render
      --list-effects    print every effect key in the catalog, sorted, and exit
  -h, --help            print this text and exit

examples:
  noisemaker-render program.dsl
  noisemaker-render program.dsl -o out.png
  noisemaker-render program.dsl --width 512 --height 512 --seed 7 --time 0.5
  noisemaker-render program.dsl --raw-rgba8 frame.rgba8 --metadata frame.json

No environment variables are needed to render. Rendering reads nothing but the
program file you name.

exit codes:
  0  rendered
  2  the command line could not be understood
  4  the program was refused (it will not render); the reason is on stderr
  5  the compiled plan failed to authenticate against its own payload
  6  an output could not be written
)";

struct Options {
  std::string source_path;
  std::string png_output;
  std::string raw_output;
  std::string metadata_output;
  noisemaker::RenderOptions render;
};

[[noreturn]] void fail_usage(const std::string& message) {
  std::cerr << "noisemaker-render: " << message << "\n"
            << "Try 'noisemaker-render --help'.\n";
  std::exit(nb::kExitUsage);
}

[[nodiscard]] double parse_number(const std::string& text, std::string_view flag) {
  try {
    std::size_t consumed = 0;
    const double value = std::stod(text, &consumed);
    if (consumed != text.size()) {
      fail_usage(std::string(flag) + " needs a number, not \"" + text + "\"");
    }
    return value;
  } catch (const std::exception&) {
    fail_usage(std::string(flag) + " needs a number, not \"" + text + "\"");
  }
}

[[nodiscard]] std::size_t parse_extent(const std::string& text, std::string_view flag) {
  const double value = parse_number(text, flag);
  if (!(value >= 1.0) || value != static_cast<double>(static_cast<std::size_t>(value))) {
    fail_usage(std::string(flag) + " needs a whole number of pixels of at least 1, not \"" +
               text + "\"");
  }
  return static_cast<std::size_t>(value);
}

[[nodiscard]] std::uint32_t parse_frame(const std::string& text, std::string_view flag) {
  const double value = parse_number(text, flag);
  if (!(value >= 0.0) || value != static_cast<double>(static_cast<std::uint32_t>(value))) {
    fail_usage(std::string(flag) + " needs a whole frame number of at least 0, not \"" +
               text + "\"");
  }
  return static_cast<std::uint32_t>(value);
}

[[nodiscard]] std::string read_source(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    fail_usage("cannot read the program file \"" + path + "\"");
  }
  return std::string(std::istreambuf_iterator<char>(stream),
                     std::istreambuf_iterator<char>());
}

// `program.dsl` -> `program.png`, `a/b/program.dsl` -> `program.png`. The
// default output lands in the working directory rather than beside the source,
// so rendering a file out of a checkout never writes into that checkout.
[[nodiscard]] std::string default_png_output(const std::string& source_path) {
  auto stem = std::filesystem::path(source_path).stem().string();
  if (stem.empty()) stem = "render";
  return stem + ".png";
}

void print_effect_keys() {
  const auto& catalog = noisemaker::effects::effect_catalog();
  std::vector<std::string> keys;
  keys.reserve(catalog.definitions.size());
  for (const auto& definition : catalog.definitions) keys.push_back(definition.id);
  std::sort(keys.begin(), keys.end());
  std::string out;
  for (const auto& key : keys) {
    out.append(key);
    out.push_back('\n');
  }
  std::cout << out;
}

[[nodiscard]] std::string_view code_name(noisemaker::graph::GraphErrorCode code) {
  using Code = noisemaker::graph::GraphErrorCode;
  switch (code) {
    case Code::invalid_options: return "invalid_options";
    case Code::invalid_dimension: return "invalid_dimension";
    case Code::allocation_limit: return "allocation_limit";
    case Code::invalid_format: return "invalid_format";
    case Code::missing_resource: return "missing_resource";
    case Code::read_before_write: return "read_before_write";
    case Code::duplicate_output: return "duplicate_output";
    case Code::unavailable_pass: return "unavailable_pass";
    case Code::invalid_snapshot: return "invalid_snapshot";
    case Code::missing_binding: return "missing_binding";
    case Code::binding_type: return "binding_type";
    case Code::unsupported_blend: return "unsupported_blend";
    case Code::unsupported_mrt: return "unsupported_mrt";
    case Code::unsupported_draw_mode: return "unsupported_draw_mode";
    case Code::unsupported_scatter: return "unsupported_scatter";
    case Code::execution_failure: return "execution_failure";
  }
  return "unknown";
}

// Fail-closed, phrased for a person. The executor's own reason string is
// reproduced verbatim on the `reason:` line -- a refusal that paraphrases the
// executor is a refusal you cannot act on.
void report_refusal(const noisemaker::graph::GraphError& error,
                    const std::string& source_path) {
  std::cerr << "noisemaker-render: " << source_path
            << " cannot be rendered, so nothing was written.\n"
            << "  reason: " << error.detail() << "\n"
            << "  code:   " << code_name(error.code()) << " ("
            << static_cast<unsigned>(error.code()) << ")\n";
  if (!error.effect_id().empty()) {
    std::cerr << "  effect: " << error.effect_id();
    if (!error.pass_name().empty()) {
      std::cerr << ", pass " << error.pass_index() << " \"" << error.pass_name() << "\"";
    }
    if (!error.program_key().empty()) {
      std::cerr << " (" << error.program_key() << ")";
    }
    std::cerr << "\n";
  }
}

[[nodiscard]] std::string metadata_document(const std::string& source_sha256,
                                            std::size_t width, std::size_t height,
                                            const std::string& rgba8_sha256,
                                            std::size_t byte_length) {
  std::string out = "{\n";
  out += "  \"schema\": " + nb::json_string(kMetadataSchema) + ",\n";
  out += "  \"status\": \"rendered\",\n";
  out += "  \"sourceSha256\": " + nb::json_string(source_sha256) + ",\n";
  out += "  \"width\": " + nb::json_number(width) + ",\n";
  out += "  \"height\": " + nb::json_number(height) + ",\n";
  out += "  \"format\": \"rgba8\",\n";
  out += "  \"orientation\": \"top-down\",\n";
  out += "  \"rgba8Sha256\": " + nb::json_string(rgba8_sha256) + ",\n";
  out += "  \"byteLength\": " + nb::json_number(byte_length) + "\n}\n";
  return out;
}

[[nodiscard]] Options parse_options(const std::vector<std::string>& args) {
  Options options;
  std::optional<std::string> source;
  for (std::size_t index = 0; index < args.size(); ++index) {
    std::string flag = args[index];
    std::optional<std::string> inline_value;
    if (flag.rfind("--", 0) == 0) {
      const auto equals = flag.find('=');
      if (equals != std::string::npos) {
        inline_value = flag.substr(equals + 1);
        flag = flag.substr(0, equals);
      }
    }
    const auto value = [&](std::string_view name) -> std::string {
      if (inline_value) return *inline_value;
      if (index + 1 >= args.size()) fail_usage(std::string(name) + " needs a value");
      return args[++index];
    };
    if (flag == "-o" || flag == "--output") {
      options.png_output = value(flag);
    } else if (flag == "--width") {
      options.render.width = parse_extent(value(flag), "--width");
    } else if (flag == "--height") {
      options.render.height = parse_extent(value(flag), "--height");
    } else if (flag == "--time") {
      options.render.time = parse_number(value(flag), "--time");
    } else if (flag == "--frame") {
      options.render.frame = parse_frame(value(flag), "--frame");
    } else if (flag == "--seed") {
      options.render.seed = parse_number(value(flag), "--seed");
    } else if (flag == "--raw-rgba8") {
      options.raw_output = value(flag);
    } else if (flag == "--metadata") {
      options.metadata_output = value(flag);
    } else if (flag == "-" || flag.rfind("-", 0) == 0) {
      fail_usage("unknown option \"" + flag + "\"");
    } else {
      if (source) {
        fail_usage("only one program can be rendered at a time; got \"" + *source +
                   "\" and \"" + flag + "\"");
      }
      source = flag;
    }
  }
  if (!source) {
    fail_usage("name a DSL program to render, for example: noisemaker-render program.dsl");
  }
  options.source_path = *source;
  if (options.png_output.empty()) {
    options.png_output = default_png_output(options.source_path);
  }
  return options;
}

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
  for (const auto& argument : args) {
    if (argument == "-h" || argument == "--help") {
      std::cout << kHelp;
      return nb::kExitOk;
    }
    if (argument == "--list-effects") {
      if (args.size() != 1) {
        fail_usage("--list-effects takes no other arguments");
      }
      print_effect_keys();
      return nb::kExitOk;
    }
  }

  const Options options = parse_options(args);
  const std::string source = read_source(options.source_path);
  const auto source_sha256 = noisemaker::graph::detail::sha256(source);

  std::vector<std::uint8_t> bytes;
  std::vector<std::uint8_t> png;
  std::size_t width = 0;
  std::size_t height = 0;
  try {
    // The shared path, verbatim: one registry, one compile entry with
    // `require_executable = true`, one executor call site.
    const auto registry = nb::build_registry();
    const auto plan =
        nb::compile_case(source, registry, options.source_path, source_sha256);
    const auto result = nb::execute_case(plan, options.render);
    bytes = result.surface.to_rgba8();
    width = result.surface.width();
    height = result.surface.height();
    png = noisemaker::encode_png(result.surface);
  } catch (const nb::CaseContractError& error) {
    std::cerr << "noisemaker-render: " << error.what() << "\n";
    return error.exit_code();
  } catch (const noisemaker::graph::GraphError& error) {
    report_refusal(error, options.source_path);
    return nb::kExitRefused;
  } catch (const std::exception& error) {
    std::cerr << "noisemaker-render: " << options.source_path
              << " cannot be rendered, so nothing was written.\n"
              << "  reason: " << error.what() << "\n";
    return nb::kExitRefused;
  }

  const std::string metadata = metadata_document(
      source_sha256, width, height, nb::sha256_bytes(bytes), bytes.size());
  try {
    // `write_raw_rgba8` is the shared byte writer; `write_text_file` the shared
    // text writer. Neither the PNG nor the raw frame gets a second serializer.
    nb::write_raw_rgba8(options.png_output, png);
    if (!options.raw_output.empty()) nb::write_raw_rgba8(options.raw_output, bytes);
    if (!options.metadata_output.empty()) {
      nb::write_text_file(options.metadata_output, metadata);
    }
  } catch (const nb::CaseContractError& error) {
    std::cerr << "noisemaker-render: " << error.what() << "\n";
    return error.exit_code();
  }

  std::cout << "wrote " << options.png_output << " (" << width << "x" << height << ")\n";
  return nb::kExitOk;
}
