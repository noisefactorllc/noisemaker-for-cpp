#pragma once

#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>

namespace noisemaker::dsl {

struct SourceLocation {
  std::string source_name = "<dsl>";
  std::size_t line = 1;
  std::size_t column = 1;
  std::size_t index = 0;
  std::size_t byte_index = 0;
};

class DslError final : public std::runtime_error {
 public:
  DslError(std::string message, SourceLocation location);
  DslError(std::string message, std::string_view source_name,
           std::size_t line, std::size_t column, std::size_t index = 0,
           std::size_t byte_index = 0);

  [[nodiscard]] const std::string& detail() const noexcept { return detail_; }
  [[nodiscard]] const SourceLocation& location() const noexcept { return location_; }

  // These names mirror the JavaScript authority and make diagnostics easy to
  // consume from C++ clients. The snake_case aliases are retained as the
  // idiomatic C++ spelling.
  std::string sourceName;
  std::string source_name;
  std::size_t line;
  std::size_t column;
  std::size_t index;
  std::size_t byte_index;

 private:
  SourceLocation location_;
  std::string detail_;
};

}  // namespace noisemaker::dsl
