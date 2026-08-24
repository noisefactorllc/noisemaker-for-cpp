#include "noisemaker/dsl/parser.hpp"
#include "noisemaker/dsl/lexer.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <memory>
#include <string>
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
        result.bindings.push_back(binding(previous()));
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
  bool check(std::string_view lexeme) const { return peek().lexeme == lexeme; }
  bool match(std::string_view lexeme) {
    if (!check(lexeme)) return false;
    ++current_;
    return true;
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

  Chain chain() {
    Chain result;
    result.calls.push_back(call());
    result.loc = result.calls.front().loc;
    while (match(".")) result.calls.push_back(call());
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
        if (mode.has_value() && *mode != next_mode) {
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
    return result;
  }

  Value value_expression(int min_precedence = 0) {
    Value left = value_unary();
    auto precedence = [](std::string_view op) {
      if (op == "+" || op == "-") return 1;
      if (op == "*" || op == "/") return 2;
      return -1;
    };
    while (precedence(peek().lexeme) >= min_precedence) {
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
      ++current_;
      if (token.lexeme == "read" && match("(")) {
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
        return result;
      }
      if ((token.lexeme == "vec2" || token.lexeme == "vec3" || token.lexeme == "vec4") &&
          match("(")) {
        std::vector<Value> values;
        if (!check(")")) {
          do values.push_back(value_expression());
          while (match(","));
        }
        consume(")");
        return Value::vector(static_cast<std::size_t>(token.lexeme.back() - '0'),
                             std::move(values), location(token));
      }
      std::vector<std::string> path{token.lexeme};
      while (match(".")) path.push_back(identifier("Expected enum member").lexeme);
      std::string qualified = path.front();
      for (std::size_t i = 1; i < path.size(); ++i) qualified += "." + path[i];
      return Value::identifier(std::move(qualified), std::move(path), location(token));
    }
    throw DslError("Expected DSL value", location(token));
  }

  Value surface_value() {
    const Token& token = peek();
    if (token.type != TokenType::surface) {
      throw DslError("Expected surface reference", location(token));
    }
    ++current_;
    const std::size_t index = static_cast<std::size_t>(std::stoul(token.lexeme.substr(1)));
    if (index > 7) throw DslError("Surface reference must be o0 through o7", location(token));
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
  return {Kind::unary, UnaryValue{operator_token, std::make_shared<Value>(std::move(argument))},
          std::move(location)};
}
Value Value::binary(char operator_token, Value left, Value right, SourceLocation location) {
  return {Kind::binary,
          BinaryValue{operator_token, std::make_shared<Value>(std::move(left)),
                      std::make_shared<Value>(std::move(right))},
          std::move(location)};
}

Program parse(std::string_view source, std::string_view source_name) {
  return Parser(tokenize(source, source_name)).program();
}

}  // namespace noisemaker::dsl
