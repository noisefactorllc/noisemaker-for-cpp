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
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace nb = noisemaker::benchmark;

namespace {

// The same schema the harness driver emits, and the same serializer:
// `nb::rendered_record` lives in the shared translation unit, so a consumer of
// `--metadata` parses one document shape regardless of which binary produced
// it -- by construction, not by a test that keeps two copies honest.
// `tests/test_render_cli.py` still asserts the two documents are
// byte-identical, now as a behavioral check on one code path.
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
      --                stop reading options; every later argument is a path

Numbers are decimal. Every option may be given at most once; a repeated option
is a usage error rather than a silent last-one-wins guess.

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

// The help says "a number", and it means a decimal one. `std::stod` also
// accepts `0x10`, `inf` and `nan`, so `--width 0x10` used to render a 16-pixel
// image -- a value the user never typed. The grammar is checked before the
// conversion rather than inferred from what happened to parse.
[[nodiscard]] bool is_decimal_number(std::string_view text) {
  std::size_t index = 0;
  if (index < text.size() && (text[index] == '+' || text[index] == '-')) ++index;
  const std::size_t integer_start = index;
  while (index < text.size() && text[index] >= '0' && text[index] <= '9') ++index;
  std::size_t digits = index - integer_start;
  if (index < text.size() && text[index] == '.') {
    ++index;
    const std::size_t fraction_start = index;
    while (index < text.size() && text[index] >= '0' && text[index] <= '9') ++index;
    digits += index - fraction_start;
  }
  if (digits == 0) return false;
  if (index < text.size() && (text[index] == 'e' || text[index] == 'E')) {
    ++index;
    if (index < text.size() && (text[index] == '+' || text[index] == '-')) ++index;
    const std::size_t exponent_start = index;
    while (index < text.size() && text[index] >= '0' && text[index] <= '9') ++index;
    if (index == exponent_start) return false;
  }
  return index == text.size();
}

[[nodiscard]] double parse_number(const std::string& text, std::string_view flag) {
  if (!is_decimal_number(text)) {
    fail_usage(std::string(flag) + " needs a number, not \"" + text + "\"");
  }
  try {
    std::size_t consumed = 0;
    const double value = std::stod(text, &consumed);
    if (consumed != text.size()) {
      fail_usage(std::string(flag) + " needs a number, not \"" + text + "\"");
    }
    return value;
  } catch (const std::exception&) {
    // Out of `double` range, e.g. `1e400`. Reported as the usage error it is.
    fail_usage(std::string(flag) + " needs a number, not \"" + text + "\"");
  }
}

// The range check precedes every double->integer conversion. A cast of an
// out-of-range double is undefined behavior, so the old
// `value != static_cast<double>(static_cast<std::size_t>(value))` spelling
// depended on UB to reject its own bad input.
template <typename Integer>
[[nodiscard]] bool fits_whole(double value, double lowest) {
  constexpr double kExclusiveUpperBound =
      static_cast<double>(std::numeric_limits<Integer>::max()) + 1.0;
  return value >= lowest && value < kExclusiveUpperBound &&
         value == std::trunc(value);
}

[[nodiscard]] std::size_t parse_extent(const std::string& text, std::string_view flag) {
  const double value = parse_number(text, flag);
  if (!fits_whole<std::size_t>(value, 1.0)) {
    fail_usage(std::string(flag) + " needs a whole number of pixels of at least 1, not \"" +
               text + "\"");
  }
  return static_cast<std::size_t>(value);
}

[[nodiscard]] std::uint32_t parse_frame(const std::string& text, std::string_view flag) {
  const double value = parse_number(text, flag);
  if (!fits_whole<std::uint32_t>(value, 0.0)) {
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

// Fail-closed, phrased for a person. The executor's own reason string is
// reproduced verbatim on the `reason:` line -- a refusal that paraphrases the
// executor is a refusal you cannot act on.
void report_refusal(const noisemaker::graph::GraphError& error,
                    const std::string& source_path) {
  std::cerr << "noisemaker-render: " << source_path
            << " cannot be rendered, so nothing was written.\n"
            << "  reason: " << error.detail() << "\n"
            // The library's own table (declared in graph/executor.hpp), so the
            // `code:` line here can never disagree with the `graph:<name>:`
            // prefix `GraphError::what()` carries.
            << "  code:   " << noisemaker::graph::code_name(error.code()) << " ("
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

[[nodiscard]] Options parse_options(const std::vector<std::string>& args) {
  Options options;
  std::optional<std::string> source;
  // Contradictory repeats are a guess, not forgiveness: `--width 64 --width
  // 128` silently rendered 128 wide. `noisemaker-dsl-cpu-case` already treats
  // a duplicate flag as a usage violation
  // (tests/test_benchmark_cpu_corpus.py), and the user tool now agrees.
  std::vector<std::string> seen;
  const auto claim = [&seen](const std::string& name) {
    if (std::find(seen.begin(), seen.end(), name) != seen.end()) {
      fail_usage(name + " was given more than once");
    }
    seen.push_back(name);
  };
  bool flags_ended = false;
  for (std::size_t index = 0; index < args.size(); ++index) {
    std::string flag = args[index];
    std::optional<std::string> inline_value;
    if (!flags_ended && flag.rfind("--", 0) == 0) {
      const auto equals = flag.find('=');
      if (equals != std::string::npos) {
        inline_value = flag.substr(equals + 1);
        flag = flag.substr(0, equals);
      }
    }
    // An explicitly empty value is a mistake, never the default: `--output=`
    // used to be indistinguishable from an unset `--output` and quietly wrote
    // the default filename while reporting success.
    // `name` is the spelling the user typed, so the diagnostic quotes it back;
    // `canonical` is what the duplicate check keys on, so `-o` and `--output`
    // are one option.
    const auto value = [&](const std::string& name, const char* canonical) -> std::string {
      claim(canonical);
      std::string text;
      if (inline_value) {
        text = *inline_value;
      } else {
        if (index + 1 >= args.size()) fail_usage(name + " needs a value");
        text = args[++index];
      }
      if (text.empty()) fail_usage(name + " needs a non-empty value");
      return text;
    };
    const auto reject_inline_value = [&](const std::string& name) {
      if (inline_value) fail_usage(name + " takes no value");
    };
    if (flags_ended) {
      // Everything after `--` is a path, even one that starts with a dash.
    } else if (flag == "--") {
      reject_inline_value(flag);
      flags_ended = true;
      continue;
    } else if (flag == "-h" || flag == "--help") {
      // Parsed in position, so `-o -h` still means "write to a file named -h"
      // rather than silently printing help and writing nothing.
      reject_inline_value(flag);
      std::cout << kHelp;
      std::exit(nb::kExitOk);
    } else if (flag == "--list-effects") {
      reject_inline_value(flag);
      if (args.size() != 1) {
        fail_usage("--list-effects takes no other arguments");
      }
      print_effect_keys();
      std::exit(nb::kExitOk);
    } else if (flag == "-o" || flag == "--output") {
      options.png_output = value(flag, "--output");
      continue;
    } else if (flag == "--width") {
      options.render.width = parse_extent(value(flag, "--width"), "--width");
      continue;
    } else if (flag == "--height") {
      options.render.height = parse_extent(value(flag, "--height"), "--height");
      continue;
    } else if (flag == "--time") {
      options.render.time = parse_number(value(flag, "--time"), "--time");
      continue;
    } else if (flag == "--frame") {
      options.render.frame = parse_frame(value(flag, "--frame"), "--frame");
      continue;
    } else if (flag == "--seed") {
      options.render.seed = parse_number(value(flag, "--seed"), "--seed");
      continue;
    } else if (flag == "--raw-rgba8") {
      options.raw_output = value(flag, "--raw-rgba8");
      continue;
    } else if (flag == "--metadata") {
      options.metadata_output = value(flag, "--metadata");
      continue;
    } else if (flag.rfind("-", 0) == 0) {
      fail_usage("unknown option \"" + flag + "\"");
    }
    if (source) {
      fail_usage("only one program can be rendered at a time; got \"" + *source +
                 "\" and \"" + flag + "\"");
    }
    source = flag;
  }
  if (!source) {
    fail_usage("name a DSL program to render, for example: noisemaker-render program.dsl");
  }
  options.source_path = *source;
  if (options.png_output.empty()) {
    options.png_output = default_png_output(options.source_path);
  }
  // Refuse a size the encoder cannot write BEFORE rendering it. `encode_png`
  // throws above this limit, and reaching that throw means the whole surface
  // has already been computed and the failure then reads as a program refusal
  // (exit 4) when nothing about the program was refused.
  if (options.render.height != 0 &&
      options.render.width > noisemaker::max_png_pixels / options.render.height) {
    fail_usage("--width x --height is " + std::to_string(options.render.width) + "x" +
               std::to_string(options.render.height) + ", which is more than the " +
               std::to_string(noisemaker::max_png_pixels) +
               " pixels a PNG can hold; choose a smaller --width or --height");
  }
  return options;
}

}  // namespace

int main(int argc, char** argv) {
  const std::vector<std::string> args(argv + 1, argv + argc);
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

  // The shared serializer, not a second one; see `nb::rendered_record`.
  const std::string metadata = nb::rendered_record(
      kMetadataSchema, source_sha256, width, height, nb::sha256_bytes(bytes), bytes.size());
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
