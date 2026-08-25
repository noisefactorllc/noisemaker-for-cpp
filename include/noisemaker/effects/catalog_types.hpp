#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace noisemaker::effects {

enum class ValueKind { null_value, boolean, number, string, array, object };

struct Value {
  ValueKind kind = ValueKind::null_value;
  bool boolean = false;
  double number = 0.0;
  std::string string;
  std::vector<Value> array;
  std::vector<std::pair<std::string, Value>> object;

  static Value null() { return {}; }
  static Value boolean_value(bool value) { Value result; result.kind = ValueKind::boolean; result.boolean = value; return result; }
  static Value number_value(double value) { Value result; result.kind = ValueKind::number; result.number = value; return result; }
  static Value string_value(std::string value) { Value result; result.kind = ValueKind::string; result.string = std::move(value); return result; }
  static Value array_value(std::vector<Value> value) { Value result; result.kind = ValueKind::array; result.array = std::move(value); return result; }
  static Value object_value(std::vector<std::pair<std::string, Value>> value) { Value result; result.kind = ValueKind::object; result.object = std::move(value); return result; }
};

enum class DimensionKind { input, screen, literal, parameter, parameter_default, power, screen_division, resolution, unknown };

struct DimensionExpression {
  DimensionKind kind = DimensionKind::unknown;
  std::string parameter;
  std::string input_override;
  double literal = 0.0;
  double default_value = 0.0;
  int power = 1;
  Value raw = Value::null();
};

struct ParameterDefinition {
  std::string name;
  std::string type;
  std::optional<Value> default_value;
  std::optional<std::string> define;
  std::optional<std::string> uniform;
  std::optional<Value> zero;
  std::vector<std::pair<std::string, Value>> enum_values;
  std::optional<std::string> enum_name;
  std::vector<std::pair<std::string, Value>> choices;
  std::optional<Value> min;
  std::optional<Value> max;
  std::optional<std::string> texture;
  std::optional<std::string> color_mode_uniform;
  bool cpu_only = false;
  std::vector<std::pair<std::string, Value>> raw;
};

struct TextureDefinition {
  std::string name;
  DimensionExpression width;
  DimensionExpression height;
  std::optional<std::string> format;
  std::vector<std::pair<std::string, Value>> raw;
};

enum class BlendKind { boolean, factors };

struct BlendDefinition {
  BlendKind kind = BlendKind::boolean;
  bool enabled = false;
  std::array<std::string, 2> factors{};
};

struct PassDefinition {
  std::string name;
  std::string program;
  std::vector<std::pair<std::string, std::string>> inputs;
  std::vector<std::pair<std::string, std::string>> outputs;
  std::vector<std::pair<std::string, Value>> uniforms;
  std::optional<Value> count;
  std::optional<Value> repeat;
  std::optional<Value> conditions;
  std::optional<Value> viewport;
  std::optional<BlendDefinition> blend;
  std::optional<std::string> draw_mode;
  std::optional<Value> draw_buffers;
  std::vector<std::pair<std::string, Value>> raw;
};

struct EffectDefinition {
  std::string id;
  std::string directory_name;
  std::string name;
  std::string name_space;
  std::string function;
  std::string kind;
  std::string domain;
  std::vector<std::string> tags;
  std::string description;
  std::vector<std::pair<std::string, std::string>> parameter_aliases;
  std::vector<ParameterDefinition> parameters;
  std::vector<PassDefinition> passes;
  std::vector<TextureDefinition> textures;
  std::optional<std::string> external_texture;
  std::optional<std::string> output_tex3d;
  std::optional<std::string> output_geo;
  std::optional<std::string> output_xyz;
  std::optional<std::string> output_velocity;
  std::optional<std::string> output_rgba;
  bool iterated = false;
  std::optional<std::string> loop_role;
  std::vector<std::pair<std::string, Value>> raw;
};

struct ProgramCompatibility {
  std::string effect_id;
  std::string program;
  std::string program_key;
  std::string status;
  std::vector<std::pair<std::string, std::string>> reasons;
  std::optional<std::string> canonical_factory;
  std::optional<std::string> source_sha256;
  std::optional<std::string> semantic_sha256;
  std::vector<std::pair<std::string, Value>> raw;
};

struct ReferencePassCompatibility {
  std::string effect_id;
  std::size_t pass_index = 0;
  std::string pass_name;
  std::string program_key;
  std::string status;
  std::vector<std::pair<std::string, std::string>> reasons;
};

struct CompatibilityBindingEvidence {
  std::string name;
  std::string type;
  std::string cpp_type;
  std::string source;
  std::string source_name;
  std::string resource;
};

struct CompatibilityOutputEvidence {
  std::size_t slot = 0;
  std::string physical_name;
  std::string logical_route;
  std::string cpp_type;
};

struct ScatterCompatibility {
  std::string program_key;
  std::string adapter;
  std::string registry;
  std::string draw_mode;
  std::string dimensionality;
  std::string count;
  std::string input_texture;
  std::string destination_mutation;
  bool blend = false;
  std::vector<CompatibilityBindingEvidence> uniforms;
  std::vector<CompatibilityOutputEvidence> outputs;
  std::vector<std::pair<std::string, std::string>> reasons;
};

struct CatalogCounts {
  std::size_t definitions = 0;
  std::size_t passes = 0;
  std::size_t reference_program_keys = 0;
  std::size_t backend_programs = 0;
  std::size_t compatible_programs = 0;
  std::size_t incompatible_programs = 0;
  std::size_t missing_passes = 0;
  std::size_t scatter_passes = 0;
  std::size_t executable_definitions = 0;
  std::size_t incomplete_definitions = 0;
};

struct CatalogProvenance {
  std::string schema;
  std::string cpu_behavioral_lock;
  std::string cpu_revision;
  std::string source_lock_sha256;
  std::string upstream_revision;
  // SHA-256 of generated C++ bytes with this field's string value replaced by
  // an empty placeholder. This is intentionally non-self-referential.
  std::string generated_payload_sha256;
  std::string normalized_record_stream_sha256;
  std::string compatibility_sha256;
  std::string upstream_tree;
  std::string first_effect_id;
  std::string last_effect_id;
  CatalogCounts counts;
};

}  // namespace noisemaker::effects
