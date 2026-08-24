#pragma once

#include "noisemaker/dsl/error.hpp"

#include <memory>
#include <optional>
#include <string>
#include <variant>
#include <vector>

namespace noisemaker::dsl {

struct Value;
using ValuePtr = std::shared_ptr<Value>;

struct ColorValue {
  std::vector<double> components;
};

struct SurfaceValue {
  std::string name;
  std::size_t index = 0;
  SourceLocation loc{};
};

struct ArrayValue {
  std::vector<Value> values;
};

struct IdentifierValue {
  std::string name;
  std::vector<std::string> path;
};

struct VectorValue {
  std::size_t width = 0;
  std::vector<Value> values;
};

struct UnaryValue {
  char operator_token = 0;
  ValuePtr argument;
};

struct BinaryValue {
  char operator_token = 0;
  ValuePtr left;
  ValuePtr right;
};

struct Value {
  enum class Kind {
    number,
    string,
    boolean,
    color,
    surface,
    array,
    identifier,
    vector,
    unary,
    binary,
  };

  using Storage = std::variant<double, std::string, bool, ColorValue, SurfaceValue,
                               ArrayValue, IdentifierValue, VectorValue, UnaryValue,
                               BinaryValue>;

  Kind kind = Kind::number;
  Storage data = 0.0;
  SourceLocation loc{};

  static Value number(double value, SourceLocation location);
  static Value string(std::string value, SourceLocation location);
  static Value boolean(bool value, SourceLocation location);
  static Value color(std::vector<double> values, SourceLocation location);
  static Value surface(std::string name, std::size_t index, SourceLocation location);
  static Value array(std::vector<Value> values, SourceLocation location);
  static Value identifier(std::string name, std::vector<std::string> path,
                          SourceLocation location);
  static Value vector(std::size_t width, std::vector<Value> values, SourceLocation location);
  static Value unary(char operator_token, Value argument, SourceLocation location);
  static Value binary(char operator_token, Value left, Value right, SourceLocation location);

  [[nodiscard]] double number() const { return std::get<double>(data); }
  [[nodiscard]] const std::string& string_value() const { return std::get<std::string>(data); }
  [[nodiscard]] bool boolean() const { return std::get<bool>(data); }
  [[nodiscard]] const ColorValue& color_value() const { return std::get<ColorValue>(data); }
  [[nodiscard]] const SurfaceValue& surface_value() const { return std::get<SurfaceValue>(data); }
  [[nodiscard]] const ArrayValue& array_value() const { return std::get<ArrayValue>(data); }
  [[nodiscard]] const IdentifierValue& identifier_value() const { return std::get<IdentifierValue>(data); }
  [[nodiscard]] const VectorValue& vector() const { return std::get<VectorValue>(data); }
  [[nodiscard]] const UnaryValue& unary() const { return std::get<UnaryValue>(data); }
  [[nodiscard]] const BinaryValue& binary() const { return std::get<BinaryValue>(data); }
};

struct CallArgument {
  std::optional<std::string> name;
  Value value;
  SourceLocation loc{};
};

struct Call {
  enum class ArgumentMode { none, positional, named };

  std::string name;
  std::vector<CallArgument> arguments;
  ArgumentMode argument_mode = ArgumentMode::none;
  SourceLocation loc{};
};

struct Chain {
  std::vector<Call> calls;
  SourceLocation loc{};
};

struct Binding {
  std::string name;
  std::variant<Value, Call> value;
  SourceLocation loc{};
};

struct Program {
  std::vector<std::string> search;
  std::vector<Binding> bindings;
  std::vector<Chain> chains;
  std::optional<SurfaceValue> render;
  SourceLocation loc{};
};

}  // namespace noisemaker::dsl
