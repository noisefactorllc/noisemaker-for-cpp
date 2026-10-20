#pragma once

#include "noisemaker/dsl/error.hpp"

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace noisemaker::dsl {

struct Value;
struct Call;
struct Chain;
using ValuePtr = std::unique_ptr<Value>;

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

// `osc(...)`, the one call the DSL accepts in a value position.
struct CallValue {
  std::unique_ptr<Call> call;
};

// A chain in a value position (a chain argument such as
// `tex: solid(color: #f00)`, the authority's `Expr ::= Chain`).
struct ChainValue {
  std::unique_ptr<Chain> chain;
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
    call,
    chain,
  };

  using Storage = std::variant<double, std::string, bool, ColorValue, SurfaceValue,
                               ArrayValue, IdentifierValue, VectorValue, UnaryValue,
                               BinaryValue, CallValue, ChainValue>;

  Kind kind = Kind::number;
  Storage data = 0.0;
  SourceLocation loc{};

  Value() = default;
  Value(Kind value_kind, Storage value_data, SourceLocation location)
      : kind(value_kind), data(std::move(value_data)), loc(std::move(location)) {}
  Value(const Value& other);
  Value& operator=(const Value& other);
  Value(Value&& other) noexcept = default;
  Value& operator=(Value&& other) noexcept = default;
  ~Value() = default;

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
  static Value call_value(Call call, SourceLocation location);
  static Value chain_value(Chain chain, SourceLocation location);

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
  [[nodiscard]] const Call& call() const { return *std::get<CallValue>(data).call; }
  [[nodiscard]] const Chain& chain() const { return *std::get<ChainValue>(data).chain; }
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
  // `from(namespace, effect(...))` resolves the effect in this one namespace.
  std::optional<std::string> name_space;
};

// `subchain(name: "...", id: "...") { .a() .b() }`: its body calls run in
// place, as the authority compiles the flattened chain.
struct Subchain {
  std::optional<std::string> name;
  std::optional<std::string> id;
  std::vector<Call> body;
  SourceLocation loc{};
};

using ChainElement = std::variant<Call, Subchain>;

struct Chain {
  std::vector<ChainElement> calls;
  SourceLocation loc{};
};

struct Binding {
  std::string name;
  std::variant<Value, Call> value;
  SourceLocation loc{};
  std::size_t plan_index = 0;
};

struct Program {
  std::vector<std::string> search;
  std::vector<Binding> bindings;
  std::vector<Chain> chains;
  std::optional<SurfaceValue> render;
  SourceLocation loc{};
};

}  // namespace noisemaker::dsl
