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
  REQUIRE(effect->textures.front().format.has_value());
  REQUIRE(effect->textures.front().format.value() == "rgba16float");
}

TEST(effect_catalog_retains_resolution_dimensions_and_absent_formats) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  for (const char* id : {"render/render3d", "render/renderCubemap3d",
                         "render/renderCubemapSurface", "render/renderLit3d"}) {
    const auto* effect = catalog.find(id);
    REQUIRE(effect != nullptr);
    REQUIRE(effect->textures.size() == 1);
    REQUIRE(effect->textures.front().name == "screenGeoBuffer");
    REQUIRE(effect->textures.front().width.kind == noisemaker::effects::DimensionKind::resolution);
    REQUIRE(effect->textures.front().height.kind == noisemaker::effects::DimensionKind::resolution);
  }

  const auto* cellular = catalog.find("synth/cellularAutomata");
  REQUIRE(cellular != nullptr);
  REQUIRE(cellular->textures.size() == 1);
  REQUIRE(!cellular->textures.front().format.has_value());
  bool cellular_raw_format = false;
  for (const auto& field : cellular->textures.front().raw) cellular_raw_format |= field.first == "format";
  REQUIRE(!cellular_raw_format);
  const auto* bloom = catalog.find("filter/bloom");
  REQUIRE(bloom != nullptr);
  REQUIRE(!bloom->textures.empty());
  bool bloom_raw_format = false;
  for (const auto& field : bloom->textures.front().raw) bloom_raw_format |= field.first == "format";
  REQUIRE(bloom_raw_format);
}

TEST(effect_catalog_retains_closed_blend_forms) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  const auto pass_named = [](const auto* effect, const char* name) {
    for (const auto& pass : effect->passes) {
      if (pass.name == name) return &pass;
    }
    return static_cast<const noisemaker::effects::PassDefinition*>(nullptr);
  };
  const auto* dla = catalog.find("points/dla");
  REQUIRE(dla != nullptr);
  const auto* dla_deposit = pass_named(dla, "depositGrid");
  REQUIRE(dla_deposit != nullptr);
  REQUIRE(dla_deposit->blend.has_value());
  REQUIRE(dla_deposit->blend->kind == noisemaker::effects::BlendKind::factors);
  REQUIRE(dla_deposit->blend->factors[0] == "one");
  REQUIRE(dla_deposit->blend->factors[1] == "one");

  const auto* billboard = catalog.find("render/pointsBillboardRender");
  REQUIRE(billboard != nullptr);
  const auto* alpha = pass_named(billboard, "deposit_alpha");
  REQUIRE(alpha != nullptr);
  REQUIRE(alpha->blend.has_value());
  REQUIRE(alpha->blend->kind == noisemaker::effects::BlendKind::factors);
  REQUIRE(alpha->blend->factors[0] == "ONE");
  REQUIRE(alpha->blend->factors[1] == "ONE_MINUS_SRC_ALPHA");

  const auto* boolean = catalog.find("filter/wormhole");
  REQUIRE(boolean != nullptr);
  const auto* deposit = pass_named(boolean, "deposit");
  REQUIRE(deposit != nullptr);
  REQUIRE(deposit->blend.has_value());
  REQUIRE(deposit->blend->kind == noisemaker::effects::BlendKind::boolean);
  REQUIRE(deposit->blend->enabled);
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
  REQUIRE(provenance.generated_payload_sha256 == "a214893a7c696073791fdb5eeae351ab7cd4638cf988cb446b9b70c43306b116");
}
