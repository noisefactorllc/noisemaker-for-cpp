#pragma once

#include "noisemaker/dsl/token.hpp"

namespace noisemaker::dsl {

using Lexer = std::vector<Token>;

[[nodiscard]] bool is_blank(std::string_view text) noexcept;

}  // namespace noisemaker::dsl
