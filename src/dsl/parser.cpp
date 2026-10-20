#include "noisemaker/dsl/parser.hpp"
#include "noisemaker/dsl/lexer.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>

namespace noisemaker::dsl {
namespace {

SourceLocation location(const Token& token) {
  return token.location;
}

Value make_unary(char op, Value argument, SourceLocation loc) {
  return Value::unary(op, std::move(argument), std::move(loc));
}

class Parser {
 public:
  explicit Parser(std::vector<Token> tokens) : tokens_(std::move(tokens)) {}

  Program program() {
    Program result;
    result.loc = location(peek());
    if (match("search")) {
      do result.search.push_back(search_namespace().lexeme);
      while (match(","));
      static_cast<void>(match(";"));
    }
    while (!at_end()) {
      if (match(";")) continue;
      if (match("let")) {
        auto declared = binding(previous());
        declared.plan_index = result.chains.size();
        result.bindings.push_back(std::move(declared));
      } else if (match("render")) {
        if (result.render.has_value()) {
          throw DslError("Program may only declare one render surface", location(previous()));
        }
        const Token start = previous();
        consume("(");
        const Value rendered = surface_value();
        result.render = rendered.surface_value();
        result.render->loc = location(start);
        consume(")");
        static_cast<void>(match(";"));
      } else {
        result.chains.push_back(chain());
        static_cast<void>(match(";"));
      }
    }
    return result;
  }

 private:
  const Token& peek(std::size_t offset = 0) const {
    const std::size_t index = std::min(current_ + offset, tokens_.size() - 1);
    return tokens_[index];
  }
  const Token& previous() const { return tokens_[current_ - 1]; }
  bool at_end() const { return peek().type == TokenType::eof; }
  // A string token's lexeme is its content, so a string never matches
  // punctuation, an operator or a keyword: `text(")")` holds the string ")".
  bool check(std::string_view lexeme) const {
    return peek().type != TokenType::string && peek().lexeme == lexeme;
  }
  bool match(std::string_view lexeme) {
    if (!check(lexeme)) return false;
    ++current_;
    return true;
  }
  bool is_punctuation(std::string_view lexeme) const {
    return peek().type == TokenType::punctuation && peek().lexeme == lexeme;
  }
  bool at_subchain() const {
    return peek().type == TokenType::keyword && peek().lexeme == "subchain";
  }
  const Token& consume(std::string_view lexeme,
                      std::string message = {}) {
    if (!check(lexeme)) {
      if (message.empty()) message = "Expected \"" + std::string(lexeme) + "\"";
      throw DslError(std::move(message), location(peek()));
    }
    return tokens_[current_++];
  }
  const Token& identifier(std::string message = "Expected identifier") {
    const Token& token = peek();
    if (token.type != TokenType::identifier) throw DslError(std::move(message), location(token));
    ++current_;
    return token;
  }
  const Token& search_namespace(std::string message = "Expected namespace after search") {
    const Token& token = peek();
    if (token.type == TokenType::identifier ||
        (token.type == TokenType::keyword && token.lexeme == "render")) {
      ++current_;
      return token;
    }
    throw DslError(std::move(message), location(token));
  }

  Binding binding(const Token& start) {
    const Token& name = identifier("Expected binding name after let");
    consume("=");
    Binding result;
    result.name = name.lexeme;
    result.loc = location(start);
    if (peek().type == TokenType::identifier && peek(1).lexeme == "(") {
      result.value = call();
    } else {
      result.value = value_expression();
    }
    static_cast<void>(match(";"));
    return result;
  }

  static bool is_write_call(const Call& value) {
    return value.name == "write" || value.name == "write3d";
  }

  Chain chain() {
    Chain result;
    Call first = call();
    result.loc = first.loc;
    result.calls.emplace_back(std::move(first));
    while (match(".")) {
      if (at_subchain()) result.calls.emplace_back(subchain());
      else if (peek().lexeme == "write3d" && peek().type == TokenType::identifier) result.calls.emplace_back(write3d());
      else result.calls.emplace_back(call());
    }
    return result;
  }

  // The authority's port of upstream parseWriteCall for write3d: two
  // positional references, a volume and a geometry (`write3d(vol0, geo0)`),
  // each an identifier or a surface.
  Call write3d() {
    const Token& name = identifier();
    const SourceLocation name_loc = location(name);
    consume("(");
    const auto reference = [this]() -> Value {
      const Token& token = peek();
      if (token.type == TokenType::surface) return surface_value();
      if (token.type != TokenType::identifier) throw DslError("Expected surface reference", location(token));
      ++current_;
      return Value::identifier(token.lexeme, {token.lexeme}, location(token));
    };
    Value volume = reference();
    consume(",");
    Value geometry = reference();
    consume(")");
    Call result;
    result.name = "write3d";
    result.argument_mode = Call::ArgumentMode::positional;
    result.loc = name_loc;
    for (Value* value : {&volume, &geometry}) {
      CallArgument argument;
      argument.loc = value->loc;
      argument.value = std::move(*value);
      result.arguments.push_back(std::move(argument));
    }
    return result;
  }

  // A chain in a value position (upstream parseChain in its 'expression'
  // context). It may hold subchain blocks, and it cannot hold write() or
  // write3d().
  Value expression_chain(Call first) {
    Chain result;
    result.loc = first.loc;
    result.calls.emplace_back(std::move(first));
    while (is_punctuation(".")) {
      ++current_;
      if (at_subchain()) {
        result.calls.emplace_back(subchain());
        continue;
      }
      Call next = call();
      if (is_write_call(next)) throw DslError("Expected effect or IO function name", next.loc);
      result.calls.emplace_back(std::move(next));
    }
    const SourceLocation loc = result.loc;
    return Value::chain_value(std::move(result), loc);
  }

  // The authority's port of upstream parseSubchainCall. A single leading
  // string is shorthand for `name`; unknown keys are discarded and the last
  // duplicate wins.
  Subchain subchain() {
    const Token start = tokens_[current_++];
    consume("(");
    Subchain result;
    result.loc = location(start);
    if (peek().type == TokenType::string) {
      result.name = std::get<std::string>(tokens_[current_++].value);
    } else {
      while (peek().type == TokenType::identifier && peek(1).lexeme == ":") {
        const std::string key = identifier().lexeme;
        consume(":");
        // A value that is not a string ends the arguments, so the closing ')'
        // check below reports it.
        if (peek().type != TokenType::string) break;
        std::string value = std::get<std::string>(tokens_[current_++].value);
        if (key == "name") result.name = std::move(value);
        else if (key == "id") result.id = std::move(value);
        static_cast<void>(match(","));
      }
    }
    if (result.name.has_value() && result.name->empty()) result.name.reset();
    if (result.id.has_value() && result.id->empty()) result.id.reset();
    consume(")");
    consume("{");
    // The body holds at least one element, so an empty block fails on its
    // missing '.'.
    do {
      consume(".");
      Call next = call();
      if (is_write_call(next)) throw DslError("Expected effect or IO function name", next.loc);
      result.body.push_back(std::move(next));
    } while (!check("}"));
    consume("}");
    return result;
  }

  Call call() {
    const Token& name = identifier("Expected effect or IO function name");
    Call result;
    result.name = name.lexeme;
    result.loc = location(name);
    consume("(");
    std::optional<Call::ArgumentMode> mode;
    if (!check(")")) {
      do {
        const bool named = peek().type == TokenType::identifier && peek(1).lexeme == ":";
        const auto next_mode = named ? Call::ArgumentMode::named : Call::ArgumentMode::positional;
        if (mode.has_value() && *mode != next_mode && name.lexeme != "midi" && name.lexeme != "audio") {
          throw DslError("Cannot mix positional and named arguments", location(peek()));
        }
        mode = next_mode;
        CallArgument argument;
        if (named) {
          argument.name = identifier().lexeme;
          consume(":");
        }
        argument.loc = location(peek());
        argument.value = value_expression();
        result.arguments.push_back(std::move(argument));
      } while (match(","));
    }
    consume(")");
    result.argument_mode = mode.value_or(Call::ArgumentMode::none);
    return result.name == "from" ? from_call(std::move(result)) : result;
  }

  // The authority's port of upstream transformFromInvocation:
  // `from(namespace, effect(...))` is the effect call, resolved in that one
  // namespace. Any other from(...) stays a call named `from`.
  static Call from_call(Call value) {
    if (value.argument_mode != Call::ArgumentMode::positional || value.arguments.size() != 2) return value;
    const Value& name_space = value.arguments[0].value;
    const Value& target = value.arguments[1].value;
    if (name_space.kind != Value::Kind::identifier || target.kind != Value::Kind::chain) return value;
    const Chain& chain = target.chain();
    if (chain.calls.size() != 1 || !std::holds_alternative<Call>(chain.calls.front())) return value;
    const Call& inner = std::get<Call>(chain.calls.front());
    if (inner.name == "read" || inner.name == "read3d" || is_write_call(inner)) return value;
    Call result = inner;
    result.name_space = name_space.identifier_value().name;
    return result;
  }

  Value value_expression(int min_precedence = 0) {
    Value left = value_unary();
    auto precedence = [](std::string_view op) {
      if (op == "+" || op == "-") return 1;
      if (op == "*" || op == "/") return 2;
      return -1;
    };
    while (peek().type == TokenType::operator_token && precedence(peek().lexeme) >= min_precedence) {
      const Token operator_token = tokens_[current_++];
      Value right = value_expression(precedence(operator_token.lexeme) + 1);
      left = Value::binary(operator_token.lexeme.front(), std::move(left), std::move(right),
                           location(operator_token));
    }
    return left;
  }

  Value value_unary() {
    if (match("-") || match("+")) {
      const Token operator_token = previous();
      return make_unary(operator_token.lexeme.front(), value_unary(), location(operator_token));
    }
    return value_primary();
  }

  Value value_primary() {
    const Token& token = peek();
    if (token.type == TokenType::number) {
      ++current_;
      return Value::number(std::get<double>(token.value), location(token));
    }
    if (token.type == TokenType::string) {
      ++current_;
      return Value::string(std::get<std::string>(token.value), location(token));
    }
    if (token.lexeme == "true" || token.lexeme == "false") {
      ++current_;
      return Value::boolean(token.lexeme == "true", location(token));
    }
    if (token.type == TokenType::color) {
      ++current_;
      return Value::color(parse_color(token.lexeme), location(token));
    }
    if (token.type == TokenType::surface) return surface_value();
    if (match("[")) {
      std::vector<Value> values;
      if (!check("]")) {
        do values.push_back(value_expression());
        while (match(","));
      }
      consume("]");
      return Value::array(std::move(values), location(token));
    }
    if (match("(")) {
      Value value = value_expression();
      consume(")");
      return value;
    }
    if (token.type == TokenType::identifier) {
      // MIDI/audio calls are parsed only for unsupported-input warnings.
      if ((token.lexeme == "osc" || token.lexeme == "midi" || token.lexeme == "audio") && peek(1).lexeme == "(") {
        const SourceLocation loc = location(token);
        return Value::call_value(call(), loc);
      }
      const Token name_token = token;
      ++current_;
      const std::string& name = name_token.lexeme;
      // `Math.PI` is the one numeric constant of upstream's grammar.
      if (name == "Math" && is_punctuation(".") && peek(1).type == TokenType::identifier &&
          peek(1).lexeme == "PI") {
        current_ += 2;
        return Value::number(3.141592653589793, location(name_token));
      }
      // A one-argument `read3d(vol0)` names a volume or geometry for a
      // parameter. With two arguments it starts a chain.
      if (name == "read3d" && is_punctuation("(")) {
        --current_;
        Call read3d = call();
        if (read3d.arguments.size() == 1 && read3d.arguments.front().value.kind == Value::Kind::identifier) {
          return read3d.arguments.front().value;
        }
        return expression_chain(std::move(read3d));
      }
      if (name == "read" && match("(")) {
        if (peek().type == TokenType::identifier && peek(1).lexeme == ":") {
          const Token& argument_name = identifier();
          if (argument_name.lexeme != "surface" && argument_name.lexeme != "tex") {
            throw DslError("read() surface argument must be named \"surface\" or \"tex\"",
                           location(previous()));
          }
          consume(":");
        }
        Value result = surface_value();
        consume(")");
        // `read(oN).effect()` in a value position is a chain argument that
        // starts from the surface. A bare `read(oN)` stays a surface reference.
        if (is_punctuation(".")) {
          Call read;
          read.name = "read";
          read.argument_mode = Call::ArgumentMode::positional;
          read.loc = location(name_token);
          CallArgument argument;
          argument.loc = result.loc;
          argument.value = std::move(result);
          read.arguments.push_back(std::move(argument));
          return expression_chain(std::move(read));
        }
        return result;
      }
      if ((name == "vec2" || name == "vec3" || name == "vec4") && match("(")) {
        std::vector<Value> values;
        if (!check(")")) {
          do values.push_back(value_expression());
          while (match(","));
        }
        consume(")");
        return Value::vector(static_cast<std::size_t>(name.back() - '0'),
                             std::move(values), location(name_token));
      }
      // Any other call in a value position starts a chain argument
      // (upstream `Expr ::= Chain`), for example `tex: solid(color: #f00)`.
      if (is_punctuation("(")) {
        --current_;
        return expression_chain(call());
      }
      std::vector<std::string> path{name};
      while (match(".")) path.push_back(identifier("Expected enum member").lexeme);
      std::string qualified = path.front();
      for (std::size_t i = 1; i < path.size(); ++i) qualified += "." + path[i];
      return Value::identifier(std::move(qualified), std::move(path), location(name_token));
    }
    throw DslError("Expected DSL value", location(token));
  }

  Value surface_value() {
    const Token& token = peek();
    if (token.type != TokenType::surface) {
      throw DslError("Expected surface reference", location(token));
    }
    ++current_;
    std::size_t index = 0;
    for (const char digit : std::string_view(token.lexeme).substr(1)) {
      const std::size_t numeric_digit = static_cast<std::size_t>(digit - '0');
      if (numeric_digit > 7 || index > (7 - numeric_digit) / 10) {
        throw DslError("Surface reference must be o0 through o7", location(token));
      }
      index = index * 10 + numeric_digit;
    }
    return Value::surface(token.lexeme, index, location(token));
  }

  static std::vector<double> parse_color(const std::string& lexeme) {
    std::string hex = lexeme.substr(1);
    if (hex.size() == 3) {
      std::string expanded;
      expanded.reserve(6);
      for (char value : hex) { expanded.push_back(value); expanded.push_back(value); }
      hex = std::move(expanded);
    }
    std::vector<double> values;
    for (std::size_t offset = 0; offset < 6; offset += 2) {
      values.push_back(static_cast<double>(std::stoul(hex.substr(offset, 2), nullptr, 16)) / 255.0);
    }
    if (hex.size() == 8) {
      values.push_back(static_cast<double>(std::stoul(hex.substr(6, 2), nullptr, 16)) / 255.0);
    }
    return values;
  }

  std::vector<Token> tokens_;
  std::size_t current_ = 0;
};

}  // namespace

Value Value::number(double value, SourceLocation location) {
  return {Kind::number, value, std::move(location)};
}
Value Value::string(std::string value, SourceLocation location) {
  return {Kind::string, std::move(value), std::move(location)};
}
Value Value::boolean(bool value, SourceLocation location) {
  return {Kind::boolean, value, std::move(location)};
}
Value Value::color(std::vector<double> values, SourceLocation location) {
  return {Kind::color, ColorValue{std::move(values)}, std::move(location)};
}
Value Value::surface(std::string name, std::size_t index, SourceLocation location) {
  return {Kind::surface, SurfaceValue{std::move(name), index, location}, std::move(location)};
}
Value Value::array(std::vector<Value> values, SourceLocation location) {
  return {Kind::array, ArrayValue{std::move(values)}, std::move(location)};
}
Value Value::identifier(std::string name, std::vector<std::string> path,
                        SourceLocation location) {
  return {Kind::identifier, IdentifierValue{std::move(name), std::move(path)}, std::move(location)};
}
Value Value::vector(std::size_t width, std::vector<Value> values, SourceLocation location) {
  return {Kind::vector, VectorValue{width, std::move(values)}, std::move(location)};
}
Value Value::unary(char operator_token, Value argument, SourceLocation location) {
  return {Kind::unary, UnaryValue{operator_token, std::make_unique<Value>(std::move(argument))},
          std::move(location)};
}
Value Value::binary(char operator_token, Value left, Value right, SourceLocation location) {
  return {Kind::binary,
          BinaryValue{operator_token, std::make_unique<Value>(std::move(left)),
                      std::make_unique<Value>(std::move(right))},
          std::move(location)};
}

Value Value::call_value(Call call, SourceLocation location) {
  return {Kind::call, CallValue{std::make_unique<Call>(std::move(call))}, std::move(location)};
}

Value Value::chain_value(Chain chain, SourceLocation location) {
  return {Kind::chain, ChainValue{std::make_unique<Chain>(std::move(chain))}, std::move(location)};
}

namespace {
Value::Storage clone_storage(const Value::Storage& storage) {
  return std::visit(
      [](const auto& value) -> Value::Storage {
        using T = std::decay_t<decltype(value)>;
        if constexpr (std::is_same_v<T, UnaryValue>) {
          return UnaryValue{value.operator_token, std::make_unique<Value>(*value.argument)};
        } else if constexpr (std::is_same_v<T, BinaryValue>) {
          return BinaryValue{value.operator_token, std::make_unique<Value>(*value.left),
                             std::make_unique<Value>(*value.right)};
        } else if constexpr (std::is_same_v<T, CallValue>) {
          return CallValue{std::make_unique<Call>(*value.call)};
        } else if constexpr (std::is_same_v<T, ChainValue>) {
          return ChainValue{std::make_unique<Chain>(*value.chain)};
        } else {
          return value;
        }
      },
      storage);
}
}  // namespace

Value::Value(const Value& other)
    : kind(other.kind), data(clone_storage(other.data)), loc(other.loc) {}

Value& Value::operator=(const Value& other) {
  if (this == &other) return *this;
  Value copy(other);
  kind = copy.kind;
  data = std::move(copy.data);
  loc = std::move(copy.loc);
  return *this;
}

Program parse(std::string_view source, std::string_view source_name) {
  return Parser(tokenize(source, source_name)).program();
}

}  // namespace noisemaker::dsl
