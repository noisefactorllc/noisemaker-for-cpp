#include "noisemaker/dsl/parser.hpp"
#include "noisemaker/js_number.hpp"

#include "test_harness.hpp"

#include <string>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale.h>
#include <sstream>
#include <variant>

using noisemaker::dsl::DslError;
using noisemaker::dsl::Value;
using noisemaker::dsl::parse;

TEST(dsl_parser_preserves_program_order_and_typed_values) {
  const auto program = parse(
      "search synth, filter, render\n"
      "let tuned = noise(scale: 7)\n"
      "tuned(seed: 11).posterize(levels: 5).write(o0)\n"
      "render(o0)",
      "parser.dsl");
  REQUIRE(program.search.size() == 3);
  REQUIRE(program.search[0] == "synth");
  REQUIRE(program.search[2] == "render");
  REQUIRE(program.bindings.size() == 1);
  REQUIRE(program.chains.size() == 1);
  REQUIRE(program.chains[0].calls.size() == 3);
  REQUIRE(program.chains[0].calls[0].name == "tuned");
  REQUIRE(program.render.has_value());
  REQUIRE(program.render->name == "o0");
}

TEST(dsl_parser_builds_precedence_unary_parentheses_and_vector_width) {
  const auto program = parse(
      "search synth\n"
      "solid(vec3(-1 + 2 * (3 - -4), 5, 6)).write(o0)\n"
      "render(o0)");
  const auto& value = program.chains[0].calls[0].arguments[0].value;
  REQUIRE(value.kind == Value::Kind::vector);
  REQUIRE(value.vector().width == 3);
  REQUIRE(value.vector().values.size() == 3);
  REQUIRE(value.vector().values[0].kind == Value::Kind::binary);
}

TEST(dsl_parser_preserves_vector_widths_and_expands_alpha_colors) {
  const auto program = parse(
      "search synth\n"
      "solid(vec2(1, 2)).write(o0)\n"
      "solid(vec4(1, 2, 3, 4)).write(o1)\n"
      "solid(color: #12345678).write(o2)\n"
      "  render(o2)");
  REQUIRE(program.chains[0].calls[0].arguments[0].value.vector().width == 2);
  REQUIRE(program.chains[1].calls[0].arguments[0].value.vector().width == 4);
  const auto& color = program.chains[2].calls[0].arguments[0].value.color_value().components;
  REQUIRE(color.size() == 4);
  REQUIRE(color[3] == 120.0 / 255.0);
  REQUIRE(program.render->loc.column == 3);
}

TEST(dsl_parser_rejects_mixed_arguments_at_second_argument_location) {
  try {
    static_cast<void>(parse("search synth\nnoise(4, seed: 2)", "mixed.dsl"));
  } catch (const DslError& error) {
    REQUIRE(error.what() == std::string(
                "mixed.dsl:2:10: Cannot mix positional and named arguments"));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_parser_accepts_named_read_forms_and_rejects_other_names) {
  const auto program = parse(
      "search synth\nsolid(read(surface: o0)).write(o1)\nrender(o1)");
  REQUIRE(program.chains[0].calls[0].arguments[0].value.kind == Value::Kind::surface);
  const auto tex_program = parse(
      "search synth\nsolid(read(tex: o0)).write(o1)\nrender(o1)");
  REQUIRE(tex_program.chains[0].calls[0].arguments[0].value.kind == Value::Kind::surface);
  try {
    static_cast<void>(parse("search synth\nsolid(read(foo: o0))", "read.dsl"));
  } catch (const DslError& error) {
    REQUIRE(error.what() == std::string(
                "read.dsl:2:12: read() surface argument must be named \"surface\" or \"tex\""));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_parser_rejects_duplicate_render_and_invalid_surface) {
  REQUIRE_THROWS_AS(parse("search synth\nrender(o0); render(o1)", "render.dsl"), DslError);
  try {
    static_cast<void>(parse("search synth\nsolid().write(o9)", "surface.dsl"));
  } catch (const DslError& error) {
    REQUIRE(error.what() == std::string(
                "surface.dsl:2:15: Surface reference must be o0 through o7"));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_parser_uses_authority_expected_token_diagnostics) {
  try {
    static_cast<void>(parse("search synth\nsolid(1", "expected.dsl"));
  } catch (const DslError& error) {
    REQUIRE(error.what() == std::string("expected.dsl:2:8: Expected \")\""));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_parser_rejects_arbitrarily_large_surface_suffix_with_dsl_error) {
  try {
    static_cast<void>(parse(
        "search synth\nsolid().write(o999999999999999999999999999999999999999999999999999999999999)",
        "huge-surface.dsl"));
  } catch (const DslError& error) {
    REQUIRE(error.what() == std::string(
                "huge-surface.dsl:2:15: Surface reference must be o0 through o7"));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_parser_copies_nested_expression_values_independently) {
  const auto program = parse("search synth\nsolid(1 + 2 * 3).write(o0)");
  Value original = program.chains[0].calls[0].arguments[0].value;
  Value copied = original;
  auto& copied_binary = std::get<noisemaker::dsl::BinaryValue>(copied.data);
  copied_binary.left->data = 9.0;
  REQUIRE(std::get<noisemaker::dsl::BinaryValue>(original.data).left != copied_binary.left);
  REQUIRE(std::get<double>(std::get<noisemaker::dsl::BinaryValue>(original.data).left->data) != 9.0);

  Value moved = std::move(copied);
  auto& moved_binary = std::get<noisemaker::dsl::BinaryValue>(moved.data);
  moved_binary.right->data = 11.0;
  REQUIRE(std::get<double>(moved_binary.right->data) == 11.0);
}

#ifdef NOISEMAKER_DSL_PARSER_ORACLE_MAIN
namespace {
std::string json_escape(const std::string& value) {
  std::ostringstream out;
  out << '"';
  constexpr char hex[] = "0123456789abcdef";
  for (unsigned char ch : value) {
    if (ch == '"') out << "\\\"";
    else if (ch == '\\') out << "\\\\";
    else if (ch == '\n') out << "\\n";
    else if (ch == '\r') out << "\\r";
    else if (ch == '\t') out << "\\t";
    else if (ch < 0x20) out << "\\u00" << hex[(ch >> 4) & 0xf] << hex[ch & 0xf];
    else out << static_cast<char>(ch);
  }
  out << '"';
  return out.str();
}

// One serializer, shared with the lexer and compiler oracles: see
// noisemaker/js_number.hpp. Never reimplement it here.
std::string number_string(double value) {
  return noisemaker::js_number_stream_text(value);
}

std::string loc_json(const noisemaker::dsl::SourceLocation& loc) {
  std::ostringstream out;
  out << "{\"sourceName\":" << json_escape(loc.source_name)
      << ",\"line\":" << loc.line << ",\"column\":" << loc.column
      << ",\"index\":" << loc.index << '}';
  return out.str();
}

std::string value_json(const Value& value);

std::string values_json(const std::vector<Value>& values) {
  std::ostringstream out;
  out << '[';
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (i != 0) out << ',';
    out << value_json(values[i]);
  }
  out << ']';
  return out.str();
}

std::string value_json(const Value& value) {
  std::ostringstream out;
  switch (value.kind) {
    case Value::Kind::number:
      out << "{\"kind\":\"number\",\"value\":" << json_escape(number_string(value.number())) << '}';
      break;
    case Value::Kind::string:
      out << "{\"kind\":\"string\",\"value\":" << json_escape(value.string_value()) << '}';
      break;
    case Value::Kind::boolean:
      out << "{\"kind\":\"boolean\",\"value\":" << (value.boolean() ? "true" : "false") << '}';
      break;
    case Value::Kind::color: {
      out << '[';
      const auto& components = value.color_value().components;
      for (std::size_t i = 0; i < components.size(); ++i) {
        if (i != 0) out << ',';
        out << "{\"kind\":\"number\",\"value\":" << json_escape(number_string(components[i])) << '}';
      }
      out << ']';
      break;
    }
    case Value::Kind::surface:
      out << "{\"kind\":\"surface\",\"name\":" << json_escape(value.surface_value().name)
          << ",\"loc\":" << loc_json(value.loc) << '}';
      break;
    case Value::Kind::array: out << values_json(value.array_value().values); break;
    case Value::Kind::identifier:
      out << "{\"kind\":\"identifier\",\"name\":" << json_escape(value.identifier_value().name)
          << ",\"loc\":" << loc_json(value.loc) << '}';
      break;
    case Value::Kind::vector:
      out << "{\"kind\":\"vector\",\"width\":" << value.vector().width
          << ",\"values\":" << values_json(value.vector().values)
          << ",\"loc\":" << loc_json(value.loc) << '}';
      break;
    case Value::Kind::unary:
      out << "{\"kind\":\"unary\",\"operator\":" << json_escape(std::string(1, value.unary().operator_token))
          << ",\"argument\":" << value_json(*value.unary().argument)
          << ",\"loc\":" << loc_json(value.loc) << '}';
      break;
    case Value::Kind::binary:
      out << "{\"kind\":\"binary\",\"operator\":" << json_escape(std::string(1, value.binary().operator_token))
          << ",\"left\":" << value_json(*value.binary().left)
          << ",\"right\":" << value_json(*value.binary().right)
          << ",\"loc\":" << loc_json(value.loc) << '}';
      break;
  }
  return out.str();
}

std::string call_json(const noisemaker::dsl::Call& call) {
  std::ostringstream out;
  const char* mode = call.argument_mode == noisemaker::dsl::Call::ArgumentMode::none ? "none" :
                     call.argument_mode == noisemaker::dsl::Call::ArgumentMode::named ? "named" : "positional";
  out << "{\"kind\":\"Call\",\"name\":" << json_escape(call.name) << ",\"args\":[";
  for (std::size_t i = 0; i < call.arguments.size(); ++i) {
    if (i != 0) out << ',';
    const auto& arg = call.arguments[i];
    out << "{\"name\":" << (arg.name.has_value() ? json_escape(*arg.name) : "null")
        << ",\"value\":" << value_json(arg.value) << ",\"loc\":" << loc_json(arg.loc) << '}';
  }
  out << ']';
  if (call.argument_mode == noisemaker::dsl::Call::ArgumentMode::none) {
    out << ",\"argMode\":null";
  } else {
    out << ",\"argMode\":\"" << mode << '\"';
  }
  out << ",\"loc\":" << loc_json(call.loc) << '}';
  return out.str();
}

std::string program_json(const noisemaker::dsl::Program& program) {
  std::ostringstream out;
  out << "{\"kind\":\"DslProgram\",\"search\":[";
  for (std::size_t i = 0; i < program.search.size(); ++i) {
    if (i != 0) out << ',';
    out << json_escape(program.search[i]);
  }
  out << "],\"bindings\":[";
  for (std::size_t i = 0; i < program.bindings.size(); ++i) {
    if (i != 0) out << ',';
    const auto& binding = program.bindings[i];
    out << "{\"kind\":\"Binding\",\"name\":" << json_escape(binding.name) << ",\"value\":";
    if (std::holds_alternative<Value>(binding.value)) out << value_json(std::get<Value>(binding.value));
    else out << call_json(std::get<noisemaker::dsl::Call>(binding.value));
    out << ",\"loc\":" << loc_json(binding.loc) << '}';
  }
  out << "],\"chains\":[";
  for (std::size_t i = 0; i < program.chains.size(); ++i) {
    if (i != 0) out << ',';
    const auto& chain = program.chains[i];
    out << "{\"kind\":\"Chain\",\"calls\":[";
    for (std::size_t j = 0; j < chain.calls.size(); ++j) {
      if (j != 0) out << ',';
      out << call_json(chain.calls[j]);
    }
    out << "],\"loc\":" << loc_json(chain.loc) << '}';
  }
  out << "],\"render\":";
  if (program.render.has_value()) {
    out << "{\"kind\":\"surface\",\"name\":" << json_escape(program.render->name)
        << ",\"loc\":" << loc_json(program.render->loc) << '}';
  } else out << "null";
  out << ",\"loc\":" << loc_json(program.loc) << '}';
  return out.str();
}
}  // namespace

int main(int argc, char** argv) {
  std::string name = "stdin";
  std::string source_name = "<dsl>";
  std::string source;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--name" && i + 1 < argc) name = argv[++i];
    else if (arg == "--source-name" && i + 1 < argc) source_name = argv[++i];
    else if (arg == "--source" && i + 1 < argc) source = argv[++i];
    else { std::cerr << "usage: --name NAME --source-name NAME --source TEXT\n"; return 2; }
  }
  std::cout << "{\"name\":" << json_escape(name);
  try {
    const auto program = parse(source, source_name);
    std::cout << ",\"ast\":" << program_json(program);
  } catch (const DslError& error) {
    std::cout << ",\"error\":{\"name\":\"DslError\",\"message\":" << json_escape(error.what())
              << ",\"sourceName\":" << json_escape(error.sourceName) << ",\"line\":" << error.line
              << ",\"column\":" << error.column << ",\"index\":" << error.index << '}';
  }
  std::cout << "}\n";
}
#endif
