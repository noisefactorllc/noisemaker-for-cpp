#pragma once

#include "noisemaker/dsl/ast.hpp"

#include <string_view>

namespace noisemaker::dsl {

[[nodiscard]] Program parse(std::string_view source, std::string_view source_name = "<dsl>");

[[nodiscard]] inline Program parse_dsl(std::string_view source,
                                       std::string_view source_name = "<dsl>") {
  return parse(source, source_name);
}

}  // namespace noisemaker::dsl
