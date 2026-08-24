#pragma once

#include "noisemaker/dsl/error.hpp"

#include <optional>
#include <string>
#include <variant>
#include <vector>

namespace noisemaker::dsl {

enum class TokenType {
  number,
  string,
  color,
  identifier,
  surface,
  keyword,
  punctuation,
  operator_token,
  eof,
};

[[nodiscard]] const char* token_type_name(TokenType type) noexcept;

using TokenValue = std::variant<std::monostate, double, std::string>;

struct Token {
  TokenType type = TokenType::eof;
  std::string lexeme;
  TokenValue value{};
  SourceLocation location{};

  // Convenience mirrors of location fields. They are populated together with
  // location and avoid making callers unpack a nested object in simple code.
  std::string sourceName;
  std::size_t line = 1;
  std::size_t column = 1;
  std::size_t index = 0;
  std::size_t byte_index = 0;

  [[nodiscard]] bool has_value() const noexcept {
    return !std::holds_alternative<std::monostate>(value);
  }
  [[nodiscard]] const std::string& source_name() const noexcept { return sourceName; }
};

[[nodiscard]] std::vector<Token> tokenize(std::string_view source,
                                           std::string_view source_name = "<dsl>");
[[nodiscard]] inline std::vector<Token> tokenize_dsl(
    std::string_view source, std::string_view source_name = "<dsl>") {
  return tokenize(source, source_name);
}

}  // namespace noisemaker::dsl
