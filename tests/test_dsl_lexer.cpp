#include "noisemaker/dsl/lexer.hpp"

#include "test_harness.hpp"

#include <cmath>
#include <charconv>
#include <cstdlib>
#include <limits>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

using noisemaker::dsl::DslError;
using noisemaker::dsl::TokenType;
using noisemaker::dsl::tokenize;

TEST(dsl_lexer_covers_authority_surface) {
  const auto tokens = tokenize("search let render true false o0 o7 foo #123 #123456 #12345678 \"x\\n\" 1.2e-3 + - * / ( ) [ ] , . : = ;", "fixture");
  REQUIRE(tokens.size() == 27);
  REQUIRE(tokens[0].type == TokenType::keyword && tokens[0].lexeme == "search");
  REQUIRE(tokens[2].type == TokenType::keyword && tokens[2].lexeme == "render");
  REQUIRE(tokens[5].type == TokenType::surface && tokens[5].lexeme == "o0");
  REQUIRE(tokens[7].type == TokenType::identifier);
  REQUIRE(tokens[8].type == TokenType::color && tokens[8].lexeme == "#123");
  REQUIRE(tokens[11].type == TokenType::string);
  REQUIRE(std::get<std::string>(tokens[11].value) == "x\n");
  REQUIRE(tokens.back().type == TokenType::eof);
}

TEST(dsl_lexer_accepts_malformed_exponents_as_nan) {
  const auto tokens = tokenize("1e 1e+ 1e- 1e2 -0 1e999 -1e999");
  REQUIRE(tokens.size() == 10);
  REQUIRE(std::isnan(std::get<double>(tokens[0].value)));
  REQUIRE(std::isnan(std::get<double>(tokens[1].value)));
  REQUIRE(std::isnan(std::get<double>(tokens[2].value)));
  REQUIRE(tokens[4].type == TokenType::operator_token && tokens[5].type == TokenType::number);
  REQUIRE(std::isinf(std::get<double>(tokens[6].value)));
  REQUIRE(std::isinf(std::get<double>(tokens[8].value)));
}

TEST(dsl_lexer_tracks_utf16_locations_and_utf8_lexemes) {
  const auto tokens = tokenize("/* 😀 */ o0\n\"😀\"", "astral");
  REQUIRE(tokens[0].type == TokenType::surface);
  REQUIRE(tokens[0].lexeme == "o0");
  REQUIRE(tokens[0].line == 1 && tokens[0].column == 10 && tokens[0].index == 9);
  REQUIRE(tokens[1].line == 2 && tokens[1].column == 1 && tokens[1].index == 12);
  REQUIRE(tokens[1].lexeme == "😀");
  REQUIRE(tokens[2].line == 2 && tokens[2].column == 5 && tokens[2].index == 16);
}

TEST(dsl_lexer_comments_and_errors_are_located_at_their_starts) {
  const auto tokens = tokenize("o0 // 😀\n/* done */ o1");
  REQUIRE(tokens.size() == 3);
  REQUIRE(tokens[1].line == 2 && tokens[1].column == 12);
  REQUIRE_THROWS_AS(tokenize("o0 /* x"), DslError);
  try { static_cast<void>(tokenize("// 😀\n@", "err")); }
  catch (const DslError& error) {
    REQUIRE(error.sourceName == "err");
    REQUIRE(error.line == 2 && error.column == 1 && error.index == 6);
    REQUIRE(error.what() == std::string("err:2:1: Unexpected character \"@\""));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_lexer_rejects_unterminated_strings_and_invalid_colors) {
  REQUIRE_THROWS_AS(tokenize("\"x\n"), DslError);
  REQUIRE_THROWS_AS(tokenize("#12"), DslError);
}

TEST(dsl_lexer_handles_malformed_utf8_without_undefined_behavior) {
  const std::string malformed("\xc3(", 2);
  try { static_cast<void>(tokenize(malformed, "malformed")); }
  catch (const DslError& error) {
    REQUIRE(error.sourceName == "malformed");
    REQUIRE(error.index == 0 && error.byte_index == 0);
    REQUIRE(error.what() == std::string("malformed:1:1: Unexpected character \"Ã\""));
    return;
  }
  REQUIRE(false);
}

TEST(dsl_error_copy_and_move_own_all_diagnostic_fields) {
  DslError copied = [&] {
    DslError original("bad", "owned", 2, 3, 4, 5);
    return original;
  }();
  REQUIRE(copied.sourceName == "owned" && copied.source_name == "owned");
  REQUIRE(copied.line == 2 && copied.column == 3 && copied.index == 4 && copied.byte_index == 5);
  REQUIRE(copied.what() == std::string("owned:2:3: bad"));
  DslError moved = std::move(copied);
  REQUIRE(moved.sourceName == "owned" && moved.source_name == "owned");
  REQUIRE(moved.what() == std::string("owned:2:3: bad"));
  DslError assigned("other", "other", 1, 1);
  assigned = moved;
  REQUIRE(assigned.sourceName == "owned" && assigned.source_name == "owned");
  REQUIRE(assigned.what() == std::string("owned:2:3: bad"));
}

#ifdef NOISEMAKER_DSL_ORACLE_MAIN
namespace {
std::string json_escape(const std::string& value) {
  std::ostringstream out;
  out << '"';
  for (unsigned char ch : value) {
    if (ch == '"') out << "\\\"";
    else if (ch == '\\') out << "\\\\";
    else if (ch == '\n') out << "\\n";
    else if (ch == '\r') out << "\\r";
    else if (ch == '\t') out << "\\t";
    else if (ch < 0x20) { out << "\\u00" << std::hex << static_cast<int>(ch) << std::dec; }
    else out << ch;
  }
  out << '"';
  return out.str();
}
std::string js_number_string(double value) {
  if (std::isnan(value)) return "number:NaN";
  if (std::isinf(value)) return value > 0 ? "number:+Infinity" : "number:-Infinity";
  if (std::signbit(value) && value == 0) return "number:-0";
  std::string text;
  for (int precision = 1; precision <= std::numeric_limits<double>::max_digits10; ++precision) {
    char candidate_buffer[128]{};
    const auto converted = std::to_chars(std::begin(candidate_buffer), std::end(candidate_buffer), value,
                                         std::chars_format::general, precision);
    if (converted.ec != std::errc{}) continue;
    const std::string candidate(candidate_buffer, converted.ptr);
    char* end = nullptr;
    const double round_trip = std::strtod(candidate.c_str(), &end);
    if (end != candidate.c_str() && *end == '\0' && round_trip == value) {
      text = candidate;
      break;
    }
  }
  if (text.empty()) throw std::runtime_error("failed to serialize finite number");
  bool negative = false;
  if (!text.empty() && text.front() == '-') { negative = true; text.erase(text.begin()); }
  int exponent = 0;
  const auto e = text.find_first_of("eE");
  if (e != std::string::npos) {
    exponent = std::stoi(text.substr(e + 1));
    text.erase(e);
  }
  const auto dot = text.find('.');
  const int before_dot = dot == std::string::npos ? static_cast<int>(text.size()) : static_cast<int>(dot);
  if (dot != std::string::npos) text.erase(dot, 1);
  const int decimal_position = before_dot + exponent;
  const int scientific_exponent = decimal_position - 1;
  std::string result;
  if (scientific_exponent >= -6 && scientific_exponent < 21) {
    if (decimal_position <= 0) result = "0." + std::string(static_cast<std::size_t>(-decimal_position), '0') + text;
    else if (decimal_position >= static_cast<int>(text.size())) result = text + std::string(static_cast<std::size_t>(decimal_position - text.size()), '0');
    else result = text.substr(0, static_cast<std::size_t>(decimal_position)) + "." + text.substr(static_cast<std::size_t>(decimal_position));
  } else {
    result.push_back(text.front());
    if (text.size() > 1) result += "." + text.substr(1);
    result += "e";
    if (scientific_exponent >= 0) result += "+";
    result += std::to_string(scientific_exponent);
  }
  return std::string(negative ? "number:-" : "number:") + result;
}
std::string record(const std::string& name, const std::string& source, const std::string& source_name) {
  std::ostringstream out;
  out << "{\"name\":" << json_escape(name);
  try {
    out << ",\"tokens\":[";
    const auto tokens = tokenize(source, source_name);
    for (std::size_t i = 0; i < tokens.size(); ++i) {
      if (i != 0) out << ',';
      const auto& token = tokens[i];
      out << "{\"type\":" << json_escape(noisemaker::dsl::token_type_name(token.type))
          << ",\"lexeme\":" << json_escape(token.lexeme);
      if (std::holds_alternative<double>(token.value)) out << ",\"value\":" << json_escape(js_number_string(std::get<double>(token.value)));
      else if (std::holds_alternative<std::string>(token.value)) out << ",\"value\":" << json_escape(std::get<std::string>(token.value));
      out << ",\"sourceName\":" << json_escape(token.sourceName)
          << ",\"line\":" << token.line << ",\"column\":" << token.column << ",\"index\":" << token.index << '}';
    }
    out << "]}";
  } catch (const DslError& error) {
    out.str("");
    out.clear();
    out << "{\"name\":" << json_escape(name) << ",\"error\":{\"name\":\"DslError\",\"message\":" << json_escape(error.what())
        << ",\"sourceName\":" << json_escape(error.sourceName) << ",\"line\":" << error.line
        << ",\"column\":" << error.column << ",\"index\":" << error.index << "}}";
  }
  return out.str();
}
}  // namespace

int main(int argc, char** argv) {
  std::string source_name = "<dsl>";
  std::string source;
  std::string name = "stdin";
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--source" && i + 1 < argc) source = argv[++i];
    else if (arg == "--source-name" && i + 1 < argc) source_name = argv[++i];
    else if (arg == "--name" && i + 1 < argc) name = argv[++i];
    else { std::cerr << "usage: --source TEXT [--source-name NAME] [--name CASE]\n"; return 2; }
  }
  std::cout << record(name, source, source_name) << '\n';
  return 0;
}
#endif
