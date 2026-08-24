#include "noisemaker/dsl/error.hpp"

#include <utility>

namespace noisemaker::dsl {

DslError::DslError(std::string message, SourceLocation location)
    : std::runtime_error(location.source_name + ":" + std::to_string(location.line) + ":" +
                         std::to_string(location.column) + ": " + message),
      sourceName(location.source_name),
      source_name(sourceName),
      line(location.line),
      column(location.column),
      index(location.index),
      byte_index(location.byte_index),
      location_(std::move(location)),
      detail_(std::move(message)) {}

DslError::DslError(std::string message, std::string_view source_name,
                   std::size_t line, std::size_t column, std::size_t index,
                   std::size_t byte_index)
    : DslError(std::move(message),
               SourceLocation{std::string(source_name), line, column, index, byte_index}) {}

}  // namespace noisemaker::dsl
