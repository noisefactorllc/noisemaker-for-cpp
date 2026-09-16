// Native comparison of the C++ worm-overlay port
// (src/effects/cpu/worm_overlay.cpp) against
// docs/port-engineering/worm-overlay-parity/worm-overlay-oracles.json --
// a JS-golden oracle generated directly from the real, unmodified authority
// function (see that directory's generator + report for methodology,
// mutation testing, and provenance).
//
// This file intentionally does not depend on the authority or on Node: the
// oracle JSON is a checked-in, sha256-sidecarred artifact, read here with a
// small self-contained parser (scoped to exactly the vocabulary the
// generator emits).

#include "test_harness.hpp"

#include "noisemaker/effects/cpu/worm_overlay.hpp"
#include "noisemaker/effects/cpu/worm_overlay_internal.hpp"
#include "noisemaker/graph/execution_plan.hpp"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace {

// ---------------------------------------------------------------------------
// Minimal JSON reader -- objects, arrays, strings, numbers, true/false/null.
// Numbers use std::strtod (not std::stod): std::stod throws std::out_of_range
// on some standard libraries for values that underflow to a subnormal or
// zero, which is a real trap for a generator that may emit very small
// values; strtod just returns the (possibly zero/subnormal) result.
// ---------------------------------------------------------------------------
class Json {
 public:
  enum class Kind { null_value, boolean, number, string, array, object };

  Kind kind = Kind::null_value;
  bool bool_value = false;
  double number_value = 0.0;
  std::string string_value;
  std::vector<Json> array_value;
  std::vector<std::pair<std::string, Json>> object_value;

  [[nodiscard]] const Json& at(const std::string& key) const {
    for (const auto& [k, v] : object_value) {
      if (k == key) return v;
    }
    throw std::runtime_error("worm-overlay oracle JSON: missing key '" + key + "'");
  }
  [[nodiscard]] bool has(const std::string& key) const {
    for (const auto& [k, v] : object_value) {
      if (k == key) return true;
    }
    return false;
  }
};

class JsonParser {
 public:
  explicit JsonParser(const std::string& text) : text_(text) {}

  Json parse() {
    skip_ws();
    Json value = parse_value();
    skip_ws();
    return value;
  }

 private:
  const std::string& text_;
  std::size_t pos_ = 0;

  [[nodiscard]] char peek() const { return text_[pos_]; }
  void skip_ws() {
    while (pos_ < text_.size() &&
           (text_[pos_] == ' ' || text_[pos_] == '\t' || text_[pos_] == '\n' || text_[pos_] == '\r')) {
      pos_ += 1;
    }
  }

  Json parse_value() {
    skip_ws();
    char c = peek();
    if (c == '{') return parse_object();
    if (c == '[') return parse_array();
    if (c == '"') return parse_string_value();
    if (c == 't' || c == 'f') return parse_bool();
    if (c == 'n') { pos_ += 4; return Json{}; }
    return parse_number();
  }

  Json parse_object() {
    Json result;
    result.kind = Json::Kind::object;
    pos_ += 1;  // '{'
    skip_ws();
    if (peek() == '}') { pos_ += 1; return result; }
    while (true) {
      skip_ws();
      std::string key = parse_raw_string();
      skip_ws();
      pos_ += 1;  // ':'
      Json value = parse_value();
      result.object_value.emplace_back(std::move(key), std::move(value));
      skip_ws();
      char c = text_[pos_];
      pos_ += 1;
      if (c == ',') continue;
      if (c == '}') break;
      throw std::runtime_error("worm-overlay oracle JSON: expected ',' or '}' in object");
    }
    return result;
  }

  Json parse_array() {
    Json result;
    result.kind = Json::Kind::array;
    pos_ += 1;  // '['
    skip_ws();
    if (peek() == ']') { pos_ += 1; return result; }
    while (true) {
      Json value = parse_value();
      result.array_value.push_back(std::move(value));
      skip_ws();
      char c = text_[pos_];
      pos_ += 1;
      if (c == ',') continue;
      if (c == ']') break;
      throw std::runtime_error("worm-overlay oracle JSON: expected ',' or ']' in array");
    }
    return result;
  }

  std::string parse_raw_string() {
    pos_ += 1;  // opening quote
    std::string out;
    while (text_[pos_] != '"') {
      char c = text_[pos_];
      if (c == '\\') {
        pos_ += 1;
        char escaped = text_[pos_];
        switch (escaped) {
          case 'n': out.push_back('\n'); break;
          case 't': out.push_back('\t'); break;
          case '"': out.push_back('"'); break;
          case '\\': out.push_back('\\'); break;
          case '/': out.push_back('/'); break;
          default: out.push_back(escaped); break;
        }
      } else {
        out.push_back(c);
      }
      pos_ += 1;
    }
    pos_ += 1;  // closing quote
    return out;
  }

  Json parse_string_value() {
    Json result;
    result.kind = Json::Kind::string;
    result.string_value = parse_raw_string();
    return result;
  }

  Json parse_bool() {
    Json result;
    result.kind = Json::Kind::boolean;
    if (text_[pos_] == 't') { result.bool_value = true; pos_ += 4; }
    else { result.bool_value = false; pos_ += 5; }
    return result;
  }

  Json parse_number() {
    std::size_t start = pos_;
    if (text_[pos_] == '-') pos_ += 1;
    while (pos_ < text_.size() && (std::isdigit(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '.' ||
                                    text_[pos_] == 'e' || text_[pos_] == 'E' || text_[pos_] == '+' ||
                                    (text_[pos_] == '-' && pos_ != start))) {
      pos_ += 1;
    }
    std::string token = text_.substr(start, pos_ - start);
    Json result;
    result.kind = Json::Kind::number;
    result.number_value = std::strtod(token.c_str(), nullptr);
    return result;
  }
};

std::string read_file(const std::string& path) {
  std::ifstream file(path, std::ios::binary);
  if (!file) throw std::runtime_error("cannot open " + path);
  std::ostringstream buffer;
  buffer << file.rdbuf();
  return buffer.str();
}

std::string repo_root() {
  // tests/ is always a direct child of the repository root in this tree.
  return std::string(__FILE__).substr(0, std::string(__FILE__).rfind("/tests/"));
}

const Json& oracle() {
  static const Json document = [] {
    const std::string path = repo_root() +
        "/docs/port-engineering/worm-overlay-parity/worm-overlay-oracles.json";
    // `text` MUST be a named local, not a temporary passed directly to
    // JsonParser's constructor: JsonParser::text_ is a `const std::string&`
    // member, and a reference bound to a temporary dangles the moment this
    // full expression ends -- exactly the sort of bug this port's own
    // methodology is about catching, not shipping.
    const std::string text = read_file(path);
    JsonParser parser(text);
    return parser.parse();
  }();
  return document;
}

std::string surface_sha256(const noisemaker::Surface& surface) {
  auto data = surface.data();
  return noisemaker::graph::detail::sha256(std::string_view(
      reinterpret_cast<const char*>(data.data()), data.size() * sizeof(float)));
}

std::uint32_t bits_of(float value) {
  std::uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}

}  // namespace

TEST(worm_overlay_render_matches_the_js_oracle_for_every_case) {
  const Json& cases = oracle().at("cases");
  REQUIRE(cases.array_value.size() == 48U);
  for (const Json& kase : cases.array_value) {
    const std::string effect_id = kase.at("effect_id").string_value;
    const auto width = static_cast<std::size_t>(kase.at("width").number_value);
    const auto height = static_cast<std::size_t>(kase.at("height").number_value);
    const Json& seed_json = kase.at("seed");
    const double seed = seed_json.kind == Json::Kind::string
        ? std::nan("") /* "NaN" sentinel */
        : seed_json.number_value;
    const double density = kase.at("density").number_value;
    const std::string expected_sha256 = kase.at("output_sha256").string_value;

    noisemaker::Surface surface =
        noisemaker::effects::cpu::render_canonical_worm_overlay(effect_id, width, height, seed, density);
    const std::string actual_sha256 = surface_sha256(surface);
    if (actual_sha256 != expected_sha256) {
      throw std::runtime_error(kase.at("name").string_value + "/" + effect_id +
                               ": sha256 mismatch (expected " + expected_sha256 + ", got " + actual_sha256 + ")");
    }

    const Json& bits = kase.at("output_bits");
    if (bits.kind == Json::Kind::array) {
      auto data = surface.data();
      REQUIRE(data.size() == bits.array_value.size());
      for (std::size_t i = 0; i < data.size(); ++i) {
        const auto expected_bits = static_cast<std::uint32_t>(bits.array_value[i].number_value);
        REQUIRE(bits_of(data[i]) == expected_bits);
      }
    }
  }
}

TEST(worm_overlay_effect_id_predicate_matches_the_authority_route_set) {
  REQUIRE(noisemaker::effects::cpu::is_worm_overlay_effect("filter/fibers"));
  REQUIRE(noisemaker::effects::cpu::is_worm_overlay_effect("filter/scratches"));
  REQUIRE(noisemaker::effects::cpu::is_worm_overlay_effect("filter/strayHair"));
  REQUIRE(!noisemaker::effects::cpu::is_worm_overlay_effect("filter/wormhole"));
  REQUIRE(!noisemaker::effects::cpu::is_worm_overlay_effect("filter/fibersx"));
  REQUIRE(!noisemaker::effects::cpu::is_worm_overlay_effect(""));
}

TEST(worm_overlay_rejects_an_unsupported_effect_id) {
  REQUIRE_THROWS_AS(
      noisemaker::effects::cpu::render_canonical_worm_overlay("filter/notARealEffect", 4U, 4U, 1.0, 1.0),
      std::invalid_argument);
}

TEST(worm_overlay_rng_matches_the_js_oracle_direct_rows) {
  const Json& rows = oracle().at("rng_rows");
  for (const Json& row : rows.array_value) {
    const Json& seed_json = row.at("seed");
    const double seed = seed_json.kind == Json::Kind::string ? std::nan("") : seed_json.number_value;
    noisemaker::effects::cpu::detail::SeededRng rng(seed);
    const Json& expected_bits = row.at("draw_bits");
    for (const Json& expected : expected_bits.array_value) {
      const double drawn = rng.float_();
      std::uint64_t actual_bits;
      std::memcpy(&actual_bits, &drawn, sizeof(actual_bits));
      const std::uint64_t expected_value = std::strtoull(expected.string_value.c_str(), nullptr, 16);
      if (actual_bits != expected_value) {
        std::ostringstream message;
        message << "seed=" << seed << ": expected 0x" << std::hex << expected_value << ", got 0x" << actual_bits;
        throw std::runtime_error(message.str());
      }
    }
  }
}

TEST(worm_overlay_value_noise_field_matches_the_js_oracle_direct_rows) {
  const Json& rows = oracle().at("noise_field_rows");
  for (const Json& row : rows.array_value) {
    const auto width = static_cast<std::size_t>(row.at("width").number_value);
    const auto height = static_cast<std::size_t>(row.at("height").number_value);
    const double frequency = row.at("frequency").number_value;
    const double seed = row.at("seed").number_value;
    noisemaker::effects::cpu::detail::SeededRng rng(seed);
    std::vector<float> field = noisemaker::effects::cpu::detail::value_noise_field(width, height, frequency, rng);
    const Json& expected_bits = row.at("field_bits");
    REQUIRE(field.size() == expected_bits.array_value.size());
    for (std::size_t i = 0; i < field.size(); ++i) {
      const auto expected = static_cast<std::uint32_t>(expected_bits.array_value[i].number_value);
      REQUIRE(bits_of(field[i]) == expected);
    }
    const std::string expected_sha256 = row.at("field_sha256").string_value;
    const std::string actual_sha256 = noisemaker::graph::detail::sha256(
        std::string_view(reinterpret_cast<const char*>(field.data()), field.size() * sizeof(float)));
    REQUIRE(actual_sha256 == expected_sha256);
  }
}

TEST(worm_overlay_render_is_deterministic_across_repeated_calls) {
  for (const char* effect_id : {"filter/fibers", "filter/scratches", "filter/strayHair"}) {
    auto first = noisemaker::effects::cpu::render_canonical_worm_overlay(effect_id, 12U, 9U, 3.0, 0.4);
    auto second = noisemaker::effects::cpu::render_canonical_worm_overlay(effect_id, 12U, 9U, 3.0, 0.4);
    REQUIRE(surface_sha256(first) == surface_sha256(second));
  }
}
