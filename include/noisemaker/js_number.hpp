#pragma once

// Exact ECMAScript `Number::toString` (radix 10) formatting.
//
// The JavaScript authority renders every numeric literal, parameter value and
// bound message with `String(value)`. C++ has no equivalent: `std::to_chars`
// picks the same shortest round-tripping digits but formats the exponent with
// iostream/printf conventions (`1e-07`, `1e+20`) where ECMAScript never zero
// pads an exponent and only switches to exponential notation outside the
// decimal exponent window [-6, 21). Every C++ site that serializes a double
// into a cross-language stream MUST go through this one routine; a second,
// independently written formatter is how `1e-07` reached a checked stream.

#include <charconv>
#include <cmath>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>

#include <cstdlib>
#include <locale.h>
#if defined(__APPLE__)
#include <xlocale.h>  // Darwin declares strtod_l here, not in <locale.h>.
#endif

namespace noisemaker {

// Parses `text` with the C numeric locale regardless of the global locale.
// Only ever fed `std::to_chars` output, so a partial parse is a logic error.
[[nodiscard]] inline double js_number_parse_exact(const std::string& text) {
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
  if (end != text.c_str() + text.size()) throw std::runtime_error("invalid number: " + text);
  return value;
}

// `String(value)` for any double. Note the ECMAScript spelling of the
// non-finite and signed-zero cases: `String(-0)` is "0", not "-0", and
// `String(Infinity)` is "Infinity", not "+Infinity". Stream conventions that
// disagree belong in the stream writer, not here.
[[nodiscard]] inline std::string js_number_to_string(double value) {
  if (std::isnan(value)) return "NaN";
  if (std::isinf(value)) return value < 0.0 ? "-Infinity" : "Infinity";
  if (value == 0.0) return "0";

  // Shortest digit string that round-trips, exactly as ECMAScript requires the
  // smallest k with s * 10^(n-k) == m.
  std::string text;
  for (int precision = 1; precision <= std::numeric_limits<double>::max_digits10; ++precision) {
    char buffer[128]{};
    const auto converted = std::to_chars(std::begin(buffer), std::end(buffer), value,
                                         std::chars_format::general, precision);
    if (converted.ec != std::errc{}) continue;
    const std::string candidate(buffer, converted.ptr);
    if (js_number_parse_exact(candidate) == value) { text = candidate; break; }
  }
  if (text.empty()) throw std::runtime_error("failed to serialize finite number");

  bool negative = false;
  if (text.front() == '-') { negative = true; text.erase(text.begin()); }
  int exponent = 0;
  const auto marker = text.find_first_of("eE");
  if (marker != std::string::npos) { exponent = std::stoi(text.substr(marker + 1)); text.erase(marker); }
  const auto dot = text.find('.');
  const int before_dot = dot == std::string::npos ? static_cast<int>(text.size()) : static_cast<int>(dot);
  if (dot != std::string::npos) text.erase(dot, 1);
  // Strip the leading zeros a fixed-notation candidate such as "0.001" carries;
  // ECMAScript's digit string `s` never has one.
  int leading_zeros = 0;
  while (leading_zeros + 1 < static_cast<int>(text.size()) && text[static_cast<std::size_t>(leading_zeros)] == '0') ++leading_zeros;
  text.erase(0, static_cast<std::size_t>(leading_zeros));
  // Trailing zeros are likewise not part of `s` once the value is exact.
  while (text.size() > 1 && text.back() == '0') text.pop_back();

  const int decimal_position = before_dot + exponent - leading_zeros;
  const int scientific_exponent = decimal_position - 1;
  std::string result;
  if (scientific_exponent >= -6 && scientific_exponent < 21) {
    if (decimal_position <= 0) {
      result = "0." + std::string(static_cast<std::size_t>(-decimal_position), '0') + text;
    } else if (decimal_position >= static_cast<int>(text.size())) {
      result = text + std::string(static_cast<std::size_t>(decimal_position) - text.size(), '0');
    } else {
      result = text.substr(0, static_cast<std::size_t>(decimal_position)) + "." +
               text.substr(static_cast<std::size_t>(decimal_position));
    }
  } else {
    result.push_back(text.front());
    if (text.size() > 1) result += "." + text.substr(1);
    result += "e";
    if (scientific_exponent >= 0) result += "+";
    result += std::to_string(scientific_exponent);
  }
  return negative ? "-" + result : result;
}

// The cross-language oracle streams tag every numeric payload and spell the
// non-finite and negative-zero cases differently from `String(value)`; those
// three spellings are the stream's own convention, everything else is exact
// ECMAScript. One writer, shared by the lexer, parser and compiler oracles.
[[nodiscard]] inline std::string js_number_stream_text(double value) {
  if (std::isnan(value)) return "number:NaN";
  if (std::isinf(value)) return value < 0.0 ? "number:-Infinity" : "number:+Infinity";
  if (value == 0.0 && std::signbit(value)) return "number:-0";
  return "number:" + js_number_to_string(value);
}

}  // namespace noisemaker
