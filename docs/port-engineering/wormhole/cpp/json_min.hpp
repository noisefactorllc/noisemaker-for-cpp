// Minimal, self-contained recursive-descent JSON parser -- just enough to
// read `wormhole-oracles.json`. Not a general-purpose JSON library: it
// supports objects, arrays, strings (basic escapes), numbers, true/false/
// null, which is the complete vocabulary the oracle generator emits.
#pragma once

#include <cctype>
#include <cstdint>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace json_min {

class Value;
using Array = std::vector<Value>;
using Object = std::vector<std::pair<std::string, Value>>; // preserves insertion order; lookups are linear (fine at this size)

enum class Type { Null, Boolean, Number, String, Array, Object };

class Value {
 public:
  Value() : type_(Type::Null) {}
  explicit Value(bool b) : type_(Type::Boolean), bool_(b) {}
  explicit Value(double n) : type_(Type::Number), number_(n) {}
  explicit Value(std::string s) : type_(Type::String), string_(std::move(s)) {}
  explicit Value(Array a) : type_(Type::Array), array_(std::make_shared<Array>(std::move(a))) {}
  explicit Value(Object o) : type_(Type::Object), object_(std::make_shared<Object>(std::move(o))) {}

  [[nodiscard]] Type type() const noexcept { return type_; }
  [[nodiscard]] bool is_null() const noexcept { return type_ == Type::Null; }

  [[nodiscard]] double as_number() const {
    if (type_ != Type::Number) throw std::runtime_error("json_min: expected number");
    return number_;
  }
  [[nodiscard]] std::int64_t as_int64() const { return static_cast<std::int64_t>(as_number()); }
  [[nodiscard]] bool as_bool() const {
    if (type_ != Type::Boolean) throw std::runtime_error("json_min: expected boolean");
    return bool_;
  }
  [[nodiscard]] const std::string& as_string() const {
    if (type_ != Type::String) throw std::runtime_error("json_min: expected string");
    return string_;
  }
  [[nodiscard]] const Array& as_array() const {
    if (type_ != Type::Array) throw std::runtime_error("json_min: expected array");
    return *array_;
  }
  [[nodiscard]] const Object& as_object() const {
    if (type_ != Type::Object) throw std::runtime_error("json_min: expected object");
    return *object_;
  }
  [[nodiscard]] const Value& at(const std::string& key) const {
    for (const auto& [k, v] : as_object()) if (k == key) return v;
    throw std::runtime_error("json_min: missing key '" + key + "'");
  }
  [[nodiscard]] bool has(const std::string& key) const {
    for (const auto& [k, v] : as_object()) if (k == key) return true;
    return false;
  }

 private:
  Type type_;
  bool bool_ = false;
  double number_ = 0.0;
  std::string string_;
  std::shared_ptr<Array> array_;
  std::shared_ptr<Object> object_;
};

class Parser {
 public:
  explicit Parser(const std::string& text) : text_(text), pos_(0) {}

  Value parse() {
    skip_ws();
    Value v = parse_value();
    skip_ws();
    if (pos_ != text_.size()) throw std::runtime_error("json_min: trailing content after top-level value");
    return v;
  }

 private:
  const std::string& text_;
  std::size_t pos_;

  [[nodiscard]] char peek() const {
    if (pos_ >= text_.size()) throw std::runtime_error("json_min: unexpected end of input");
    return text_[pos_];
  }
  char advance() { return text_[pos_++]; }
  void expect(char c) {
    if (peek() != c) throw std::runtime_error(std::string("json_min: expected '") + c + "'");
    pos_ += 1;
  }
  void skip_ws() {
    while (pos_ < text_.size() && (text_[pos_] == ' ' || text_[pos_] == '\t' || text_[pos_] == '\n' || text_[pos_] == '\r')) pos_ += 1;
  }

  Value parse_value() {
    skip_ws();
    const char c = peek();
    if (c == '{') return parse_object();
    if (c == '[') return parse_array();
    if (c == '"') return Value(parse_string());
    if (c == 't') { expect_literal("true"); return Value(true); }
    if (c == 'f') { expect_literal("false"); return Value(false); }
    if (c == 'n') { expect_literal("null"); return Value(); }
    return parse_number();
  }

  void expect_literal(const char* literal) {
    for (const char* p = literal; *p != '\0'; ++p) {
      if (pos_ >= text_.size() || text_[pos_] != *p) throw std::runtime_error(std::string("json_min: expected literal '") + literal + "'");
      pos_ += 1;
    }
  }

  Value parse_object() {
    expect('{');
    Object obj;
    skip_ws();
    if (peek() == '}') { pos_ += 1; return Value(std::move(obj)); }
    while (true) {
      skip_ws();
      std::string key = parse_string();
      skip_ws();
      expect(':');
      Value val = parse_value();
      obj.emplace_back(std::move(key), std::move(val));
      skip_ws();
      char c = advance();
      if (c == ',') continue;
      if (c == '}') break;
      throw std::runtime_error("json_min: expected ',' or '}' in object");
    }
    return Value(std::move(obj));
  }

  Value parse_array() {
    expect('[');
    Array arr;
    skip_ws();
    if (peek() == ']') { pos_ += 1; return Value(std::move(arr)); }
    while (true) {
      Value val = parse_value();
      arr.push_back(std::move(val));
      skip_ws();
      char c = advance();
      if (c == ',') continue;
      if (c == ']') break;
      throw std::runtime_error("json_min: expected ',' or ']' in array");
    }
    return Value(std::move(arr));
  }

  std::string parse_string() {
    expect('"');
    std::string out;
    while (true) {
      if (pos_ >= text_.size()) throw std::runtime_error("json_min: unterminated string");
      char c = advance();
      if (c == '"') break;
      if (c == '\\') {
        if (pos_ >= text_.size()) throw std::runtime_error("json_min: unterminated escape");
        char e = advance();
        switch (e) {
          case '"': out.push_back('"'); break;
          case '\\': out.push_back('\\'); break;
          case '/': out.push_back('/'); break;
          case 'n': out.push_back('\n'); break;
          case 't': out.push_back('\t'); break;
          case 'r': out.push_back('\r'); break;
          case 'b': out.push_back('\b'); break;
          case 'f': out.push_back('\f'); break;
          case 'u': {
            // Not needed by this oracle's content (ASCII-only identifiers and
            // hex strings); handled minimally by skipping 4 hex digits and
            // emitting '?' so a real occurrence is visible rather than
            // silently mis-decoded.
            for (int i = 0; i < 4; ++i) { if (pos_ >= text_.size()) throw std::runtime_error("json_min: bad \\u escape"); pos_ += 1; }
            out.push_back('?');
            break;
          }
          default: throw std::runtime_error("json_min: unknown escape");
        }
      } else {
        out.push_back(c);
      }
    }
    return out;
  }

  Value parse_number() {
    const std::size_t start = pos_;
    if (pos_ < text_.size() && text_[pos_] == '-') pos_ += 1;
    while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) pos_ += 1;
    if (pos_ < text_.size() && text_[pos_] == '.') {
      pos_ += 1;
      while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) pos_ += 1;
    }
    if (pos_ < text_.size() && (text_[pos_] == 'e' || text_[pos_] == 'E')) {
      pos_ += 1;
      if (pos_ < text_.size() && (text_[pos_] == '+' || text_[pos_] == '-')) pos_ += 1;
      while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) pos_ += 1;
    }
    if (pos_ == start) throw std::runtime_error("json_min: invalid number");
    const std::string token = text_.substr(start, pos_ - start);
    return Value(std::stod(token));
  }
};

inline Value parse(const std::string& text) { return Parser(text).parse(); }

} // namespace json_min
