#include "noisemaker/dsl/lexer.hpp"

#include <charconv>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <locale.h>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

namespace noisemaker::dsl {
namespace {

struct Decoded {
  std::uint32_t codepoint = 0xfffd;
  std::size_t width = 1;
  bool valid = false;
};

Decoded decode(std::string_view source, std::size_t at) noexcept {
  if (at >= source.size()) return {};
  const auto byte = [&source](std::size_t i) { return static_cast<unsigned char>(source[i]); };
  const unsigned char first = byte(at);
  if (first < 0x80) return {first, 1, true};
  std::size_t width = 0;
  std::uint32_t value = 0;
  std::uint32_t minimum = 0;
  if ((first & 0xe0U) == 0xc0U) { width = 2; value = first & 0x1fU; minimum = 0x80; }
  else if ((first & 0xf0U) == 0xe0U) { width = 3; value = first & 0x0fU; minimum = 0x800; }
  else if ((first & 0xf8U) == 0xf0U) { width = 4; value = first & 0x07U; minimum = 0x10000; }
  else return {first, 1, false};
  if (at + width > source.size()) return {first, 1, false};
  for (std::size_t i = 1; i < width; ++i) {
    const unsigned char continuation = byte(at + i);
    if ((continuation & 0xc0U) != 0x80U) return {first, 1, false};
    value = (value << 6U) | (continuation & 0x3fU);
  }
  if (value < minimum || value > 0x10ffffU || (value >= 0xd800U && value <= 0xdfffU)) {
    return {first, 1, false};
  }
  return {value, width, true};
}

bool ascii_digit(std::uint32_t cp) noexcept { return cp >= '0' && cp <= '9'; }
bool ascii_hex(std::uint32_t cp) noexcept {
  return (cp >= '0' && cp <= '9') || (cp >= 'a' && cp <= 'f') || (cp >= 'A' && cp <= 'F');
}
bool ascii_identifier_start(std::uint32_t cp) noexcept {
  return (cp >= 'a' && cp <= 'z') || (cp >= 'A' && cp <= 'Z') || cp == '_';
}
bool ascii_identifier_part(std::uint32_t cp) noexcept { return ascii_identifier_start(cp) || ascii_digit(cp); }
bool is_keyword(std::string_view word) noexcept {
  return word == "search" || word == "let" || word == "render" || word == "true" || word == "false";
}
bool is_punctuation(char ch) noexcept {
  return ch == '(' || ch == ')' || ch == '[' || ch == ']' || ch == ',' || ch == '.' ||
         ch == ':' || ch == '=' || ch == ';';
}
bool is_operator(char ch) noexcept { return ch == '+' || ch == '-' || ch == '*' || ch == '/'; }
bool js_whitespace(std::uint32_t cp) noexcept {
  return cp == 0x0009 || cp == 0x000a || cp == 0x000b || cp == 0x000c || cp == 0x000d ||
         cp == 0x0020 || cp == 0x00a0 || cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200a) ||
         cp == 0x2028 || cp == 0x2029 || cp == 0x202f || cp == 0x205f || cp == 0x3000 || cp == 0xfeff;
}

double parse_c_number(std::string_view lexeme) {
  std::string text(lexeme);
  char* end = nullptr;
#if defined(_WIN32)
  _locale_t c_locale = _create_locale(LC_NUMERIC, "C");
  if (c_locale == nullptr) throw std::runtime_error("failed to create C numeric locale");
  const double value = _strtod_l(text.c_str(), &end, c_locale);
  _free_locale(c_locale);
#else
  locale_t c_locale = newlocale(LC_NUMERIC_MASK, "C", static_cast<locale_t>(0));
  if (c_locale == nullptr) throw std::runtime_error("failed to create C numeric locale");
  const double value = strtod_l(text.c_str(), &end, c_locale);
  freelocale(c_locale);
#endif
  if (end != text.c_str() + text.size()) throw std::runtime_error("incomplete DSL number conversion");
  return value;
}

std::string json_character(std::uint32_t cp) {
  std::uint32_t unit = cp;
  if (cp > 0xffffU) unit = 0xd800U + ((cp - 0x10000U) >> 10U);
  std::string result;
  result.push_back('"');
  if (unit == '"') result += "\\\"";
  else if (unit == '\\') result += "\\\\";
  else if (unit == '\b') result += "\\b";
  else if (unit == '\f') result += "\\f";
  else if (unit == '\n') result += "\\n";
  else if (unit == '\r') result += "\\r";
  else if (unit == '\t') result += "\\t";
  else if (unit < 0x20U) {
    constexpr char hex[] = "0123456789abcdef";
    result += "\\u00";
    result.push_back(hex[(unit >> 4U) & 0xfU]);
    result.push_back(hex[unit & 0xfU]);
  } else if (cp > 0xffffU) {
    constexpr char hex[] = "0123456789abcdef";
    result += "\\u";
    for (int shift = 12; shift >= 0; shift -= 4) result.push_back(hex[(unit >> shift) & 0xfU]);
  } else if (cp <= 0x7fU) result.append(1, static_cast<char>(unit));
  else if (cp <= 0x7ffU) {
    result.push_back(static_cast<char>(0xc0U | (cp >> 6U)));
    result.push_back(static_cast<char>(0x80U | (cp & 0x3fU)));
  } else {
    result.push_back(static_cast<char>(0xe0U | (cp >> 12U)));
    result.push_back(static_cast<char>(0x80U | ((cp >> 6U) & 0x3fU)));
    result.push_back(static_cast<char>(0x80U | (cp & 0x3fU)));
  }
  result.push_back('"');
  return result;
}

class Scanner {
 public:
  Scanner(std::string_view source, std::string_view source_name)
      : source_(source), source_name_(source_name) {}

  std::vector<Token> run() {
    while (!at_end()) {
      const auto current = peek();
      if (js_whitespace(current.codepoint)) { advance(); continue; }
      if (current.codepoint == '/' && peek(1).codepoint == '/') { skip_line_comment(); continue; }
      if (current.codepoint == '/' && peek(1).codepoint == '*') { skip_block_comment(); continue; }
      scan_token();
    }
    Token eof;
    eof.type = TokenType::eof;
    eof.sourceName = source_name_;
    eof.location = location();
    sync(eof);
    tokens_.push_back(std::move(eof));
    return tokens_;
  }

 private:
  Decoded peek(std::size_t offset = 0) const noexcept {
    std::size_t position = byte_pos_;
    for (std::size_t i = 0; i < offset && position < source_.size(); ++i) position += decode(source_, position).width;
    return decode(source_, position);
  }
  bool at_end() const noexcept { return byte_pos_ >= source_.size(); }
  Decoded advance() noexcept {
    const auto value = decode(source_, byte_pos_);
    byte_pos_ += value.width;
    const std::size_t units = value.codepoint > 0xffffU ? 2 : 1;
    index_ += units;
    if (value.codepoint == '\n') { ++line_; column_ = 1; }
    else column_ += units;
    return value;
  }
  SourceLocation location() const { return {source_name_, line_, column_, index_, byte_pos_}; }
  void sync(Token& token) const {
    token.sourceName = source_name_;
    token.line = token.location.line;
    token.column = token.location.column;
    token.index = token.location.index;
    token.byte_index = token.location.byte_index;
  }
  std::string slice(std::size_t from) const { return std::string(source_.substr(from, byte_pos_ - from)); }
  void skip_line_comment() { advance(); advance(); while (!at_end() && peek().codepoint != '\n') advance(); }
  void skip_block_comment() {
    const auto start = location();
    advance(); advance();
    while (!at_end() && !(peek().codepoint == '*' && peek(1).codepoint == '/')) advance();
    if (at_end()) throw DslError("Unterminated block comment", start);
    advance(); advance();
  }
  void push(TokenType type, std::size_t from, SourceLocation start, TokenValue value = {}) {
    Token token;
    token.type = type;
    token.lexeme = slice(from);
    token.value = std::move(value);
    token.location = std::move(start);
    sync(token);
    tokens_.push_back(std::move(token));
  }
  void scan_token() {
    const auto start = location();
    const std::size_t from = byte_pos_;
    const auto first = peek().codepoint;
    if (first == '#') {
      advance();
      while (ascii_hex(peek().codepoint)) advance();
      const auto lexeme = slice(from);
      if (lexeme.size() != 4 && lexeme.size() != 7 && lexeme.size() != 9) {
        throw DslError("Colors must use #RGB, #RRGGBB, or #RRGGBBAA", start);
      }
      push(TokenType::color, from, start);
      return;
    }
    if (first == '"') {
      advance();
      std::string value;
      while (!at_end() && peek().codepoint != '"') {
        if (peek().codepoint == '\n') throw DslError("Unterminated string", start);
        if (peek().codepoint == '\\') {
          advance();
          if (at_end()) { value += "undefined"; break; }
          const auto escaped = advance().codepoint;
          if (escaped == 'n') value.push_back('\n');
          else if (escaped == 't') value.push_back('\t');
          else value += encode(escaped);
        } else value += encode(advance().codepoint);
      }
      if (at_end()) throw DslError("Unterminated string", start);
      advance();
      push(TokenType::string, from, start, value);
      // The authority's string token uses the decoded value as its lexeme;
      // unlike every other token it does not retain the surrounding quotes.
      tokens_.back().lexeme = std::get<std::string>(tokens_.back().value);
      return;
    }
    if (ascii_digit(first) || (first == '.' && ascii_digit(peek(1).codepoint))) {
      while (ascii_digit(peek().codepoint)) advance();
      if (peek().codepoint == '.') { advance(); while (ascii_digit(peek().codepoint)) advance(); }
      if (peek().codepoint == 'e' || peek().codepoint == 'E') {
        advance();
        if (peek().codepoint == '+' || peek().codepoint == '-') advance();
        while (ascii_digit(peek().codepoint)) advance();
      }
      const auto lexeme = slice(from);
      const auto exponent = lexeme.find_first_of("eE");
      std::size_t digit = std::string::npos;
      if (exponent != std::string::npos) {
        digit = exponent + 1;
        if (digit < lexeme.size() && (lexeme[digit] == '+' || lexeme[digit] == '-')) ++digit;
      }
      const double value = exponent != std::string::npos && digit == lexeme.size()
                               ? std::numeric_limits<double>::quiet_NaN()
                               : parse_c_number(lexeme);
      push(TokenType::number, from, start, value);
      return;
    }
    if (ascii_identifier_start(first)) {
      advance(); while (ascii_identifier_part(peek().codepoint)) advance();
      const auto lexeme = slice(from);
      TokenType type = TokenType::identifier;
      if (lexeme.size() > 1 && lexeme[0] == 'o') {
        bool surface = true; for (std::size_t i = 1; i < lexeme.size(); ++i) surface = surface && ascii_digit(static_cast<unsigned char>(lexeme[i]));
        if (surface) type = TokenType::surface;
      }
      if (type == TokenType::identifier && is_keyword(lexeme)) type = TokenType::keyword;
      push(type, from, start);
      return;
    }
    if (first < 0x80U && is_punctuation(static_cast<char>(first))) { advance(); push(TokenType::punctuation, from, start); return; }
    if (first < 0x80U && is_operator(static_cast<char>(first))) { advance(); push(TokenType::operator_token, from, start); return; }
    throw DslError("Unexpected character " + json_character(first), start);
  }
  static std::string encode(std::uint32_t cp) {
    std::string out;
    if (cp <= 0x7fU) out.push_back(static_cast<char>(cp));
    else if (cp <= 0x7ffU) { out.push_back(static_cast<char>(0xc0U | (cp >> 6U))); out.push_back(static_cast<char>(0x80U | (cp & 0x3fU))); }
    else if (cp <= 0xffffU) { out.push_back(static_cast<char>(0xe0U | (cp >> 12U))); out.push_back(static_cast<char>(0x80U | ((cp >> 6U) & 0x3fU))); out.push_back(static_cast<char>(0x80U | (cp & 0x3fU))); }
    else { out.push_back(static_cast<char>(0xf0U | (cp >> 18U))); out.push_back(static_cast<char>(0x80U | ((cp >> 12U) & 0x3fU))); out.push_back(static_cast<char>(0x80U | ((cp >> 6U) & 0x3fU))); out.push_back(static_cast<char>(0x80U | (cp & 0x3fU))); }
    return out;
  }

  std::string_view source_;
  std::string source_name_;
  std::size_t byte_pos_ = 0;
  std::size_t index_ = 0;
  std::size_t line_ = 1;
  std::size_t column_ = 1;
  std::vector<Token> tokens_;
};

}  // namespace

const char* token_type_name(TokenType type) noexcept {
  switch (type) {
    case TokenType::number: return "number";
    case TokenType::string: return "string";
    case TokenType::color: return "color";
    case TokenType::identifier: return "identifier";
    case TokenType::surface: return "surface";
    case TokenType::keyword: return "keyword";
    case TokenType::punctuation: return "punctuation";
    case TokenType::operator_token: return "operator";
    case TokenType::eof: return "eof";
  }
  return "unknown";
}

std::vector<Token> tokenize(std::string_view source, std::string_view source_name) {
  return Scanner(source, source_name).run();
}

}  // namespace noisemaker::dsl
