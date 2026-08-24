#include "noisemaker/effects/catalog.hpp"

#include "test_harness.hpp"

TEST(effect_catalog_is_ordered_and_lookup_is_secondary) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  REQUIRE(catalog.definitions.size() == 205);
  REQUIRE(catalog.definitions.front().id == "classicNoisedeck/bitEffects");
  REQUIRE(catalog.definitions.back().id == "synth3d/shape3d");
  REQUIRE(catalog.find("filter/blur") != nullptr);
  REQUIRE(!catalog.definitions.front().raw.empty());
  REQUIRE(catalog.definitions.front().raw.front().first == "id");
  REQUIRE(catalog.definitions.front().raw.front().second.kind == noisemaker::effects::ValueKind::string);
}

TEST(effect_catalog_retains_dynamic_dimensions_and_formats) {
  const auto* effect = noisemaker::effects::effect_catalog().find("filter/bloom");
  REQUIRE(effect != nullptr);
  REQUIRE(!effect->textures.empty());
  REQUIRE(effect->textures.front().width.kind == noisemaker::effects::DimensionKind::input);
  REQUIRE(effect->textures.front().format == "rgba16float");
}

TEST(effect_catalog_retains_blur_order_and_external_texture) {
  const auto* blur = noisemaker::effects::effect_catalog().find("filter/blur");
  REQUIRE(blur != nullptr);
  REQUIRE(blur->passes.size() >= 2);
  REQUIRE(blur->passes[0].name == "blurH");
  REQUIRE(blur->passes[1].name == "blurV");
  const auto* text = noisemaker::effects::effect_catalog().find("filter/text");
  REQUIRE(text != nullptr);
  REQUIRE(text->external_texture.has_value());
  REQUIRE(text->external_texture.value() == "textTex");
  const auto* points = noisemaker::effects::effect_catalog().find("points/attractor");
  REQUIRE(points != nullptr);
  REQUIRE(points->output_xyz.has_value());
  REQUIRE(points->output_velocity.has_value());
  REQUIRE(points->output_rgba.has_value());
}

TEST(effect_catalog_value_preserves_negative_zero) {
  const auto nan = noisemaker::effects::Value::number_value(std::numeric_limits<double>::quiet_NaN());
  const auto positive_inf = noisemaker::effects::Value::number_value(std::numeric_limits<double>::infinity());
  const auto negative_inf = noisemaker::effects::Value::number_value(-std::numeric_limits<double>::infinity());
  const auto negative_zero = noisemaker::effects::Value::number_value(-0.0);
  REQUIRE(nan.kind == noisemaker::effects::ValueKind::number);
  REQUIRE(std::isnan(nan.number));
  REQUIRE(std::isinf(positive_inf.number) && positive_inf.number > 0.0);
  REQUIRE(std::isinf(negative_inf.number) && negative_inf.number < 0.0);
  REQUIRE(std::signbit(negative_zero.number));
}

TEST(effect_catalog_provenance_contains_non_self_referential_payload_hash) {
  const auto& provenance = noisemaker::effects::effect_catalog().provenance;
  REQUIRE(provenance.generated_payload_sha256 == "bcd1fdb126a231632865f1a3f2448c9fcb528a5457d58947f4c474af6622e93d");
}
