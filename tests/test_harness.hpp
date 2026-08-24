#pragma once

#include <cmath>
#include <cstdint>
#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace test {

using Function = std::function<void()>;

struct Case {
  const char* name;
  Function function;
};

inline std::vector<Case>& cases() {
  static std::vector<Case> registered;
  return registered;
}

class Registration {
 public:
  Registration(const char* name, Function function) {
    cases().push_back({name, std::move(function)});
  }
};

inline void require(bool condition, const char* expression, const char* file, int line) {
  if (!condition) {
    std::ostringstream message;
    message << file << ':' << line << ": requirement failed: " << expression;
    throw std::runtime_error(message.str());
  }
}

template <typename Exception, typename FunctionType>
void require_throws(FunctionType&& function, const char* expression, const char* file, int line) {
  try {
    function();
  } catch (const Exception&) {
    return;
  } catch (const std::exception& error) {
    std::ostringstream message;
    message << file << ':' << line << ": expected " << expression << ", got " << error.what();
    throw std::runtime_error(message.str());
  }
  std::ostringstream message;
  message << file << ':' << line << ": expected exception " << expression;
  throw std::runtime_error(message.str());
}

inline bool nearly_equal(float actual, float expected, float tolerance = 0.000001f) {
  return std::fabs(actual - expected) <= tolerance;
}

}  // namespace test

#define TEST(name) \
  static void name(); \
  static test::Registration name##_registration(#name, name); \
  static void name()

#define REQUIRE(expression) test::require((expression), #expression, __FILE__, __LINE__)
#define REQUIRE_THROWS_AS(expression, exception_type) \
  test::require_throws<exception_type>([&] { static_cast<void>(expression); }, #exception_type, __FILE__, __LINE__)
