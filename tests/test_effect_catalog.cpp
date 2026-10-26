#include "noisemaker/effects/catalog.hpp"
#include "noisemaker/dsl/compiler.hpp"

#include "test_harness.hpp"

#include <algorithm>
#include <array>

TEST(effect_catalog_is_ordered_and_lookup_is_secondary) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  REQUIRE(catalog.definitions.size() == 210);
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
  const auto* alpha = pass_named(billboard, "deposit_alpha_0");
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
  REQUIRE(provenance.generated_payload_sha256 == "5fb54b3d45b3dc4af48e9502fe289247b32d6042b864110f1b9e5f3062785390");
}

// The authority moved particle texture inputs into the behaviors: each
// surface parameter defaults to `none`, reports its binding through its
// colorModeUniform, and routes to a sampler of the same name. The deprecated
// `fieldTex` name resolves to `heightTex` (definition.js paramAliases).
TEST(effect_catalog_particle_surface_parameters_bind_explicit_alias_and_default_routes) {
  struct Fixture { const char* id; const char* parameter; const char* function; const char* mode; const char* alias; };
  const std::array fixtures{
      Fixture{"points/attractor", "diffuseTex", "attractor", "diffuseActive", nullptr},
      Fixture{"points/dla", "heightTex", "dla", "fieldActive", "fieldTex"},
      Fixture{"points/dla", "diffuseTex", "dla", "diffuseActive", nullptr},
      Fixture{"points/flock", "diffuseTex", "flock", "diffuseActive", nullptr},
      Fixture{"points/flow", "heightTex", "flow", "fieldActive", "fieldTex"},
      Fixture{"points/hydraulic", "heightTex", "hydraulic", "fieldActive", nullptr},
      Fixture{"points/life", "diffuseTex", "life", "diffuseActive", nullptr},
      Fixture{"points/physarum", "heightTex", "physarum", "fieldActive", "fieldTex"},
      Fixture{"points/physical", "diffuseTex", "physical", "diffuseActive", nullptr},
  };
  const auto& catalog = noisemaker::effects::effect_catalog();
  const noisemaker::effects::EffectRegistry registry(catalog);
  const auto* emitter = catalog.find("render/pointsEmit");
  REQUIRE(emitter != nullptr);
  REQUIRE(std::none_of(emitter->parameters.begin(), emitter->parameters.end(),
      [](const auto& item) { return item.type == "surface"; }));
  for (const auto& fixture : fixtures) {
    const auto* definition = catalog.find(fixture.id);
    REQUIRE(definition != nullptr);
    const auto parameter = std::find_if(definition->parameters.begin(), definition->parameters.end(),
        [&](const auto& item) { return item.name == fixture.parameter; });
    REQUIRE(parameter != definition->parameters.end());
    REQUIRE(parameter->type == "surface");
    REQUIRE(parameter->default_value.has_value());
    REQUIRE(parameter->default_value->string == "none");
    REQUIRE(parameter->color_mode_uniform.has_value());
    REQUIRE(*parameter->color_mode_uniform == fixture.mode);
    std::vector<std::string> arguments{"", std::string(fixture.parameter) + ": o1"};
    if (fixture.alias != nullptr) arguments.push_back(std::string(fixture.alias) + ": o1");
    for (const auto& argument : arguments) {
      const bool explicit_source = !argument.empty();
      const auto plan = noisemaker::dsl::compile(
          "search synth, points, render\nsolid().write(o1)\nsolid()." +
          std::string(fixture.function) + "(" + argument + ").write(o0)\nrender(o0)\n", registry);
      REQUIRE(plan.executable);
      bool found = false;
      for (const auto& chain : plan.chains) for (const auto& step : chain.steps) {
        const auto* effect = std::get_if<noisemaker::graph::EffectStep>(&step);
        if (effect == nullptr || effect->effect.id != fixture.id) continue;
        const auto binding = std::find_if(effect->params.begin(), effect->params.end(),
            [&](const auto& item) { return item.name == fixture.parameter; });
        REQUIRE(binding != effect->params.end());
        if (explicit_source) {
          REQUIRE(binding->value.kind == noisemaker::graph::PlanValue::Kind::surface);
          REQUIRE(binding->value.surface.kind == noisemaker::graph::SurfaceReference::Kind::named);
          REQUIRE(binding->value.surface.name == "o1");
          REQUIRE((effect->explicit_params == std::vector<std::string>{fixture.parameter}));
        } else {
          REQUIRE(binding->value.kind == noisemaker::graph::PlanValue::Kind::null_value);
          REQUIRE(effect->explicit_params.empty());
        }
        REQUIRE(std::none_of(effect->params.begin(), effect->params.end(),
            [](const auto& item) { return item.name == "fieldTex"; }));
        bool routed = false;
        for (const auto& pass : effect->passes) for (const auto& sampler : pass.samplers) {
          if (sampler.name == fixture.parameter && sampler.resource == fixture.parameter) routed = true;
        }
        REQUIRE(routed);
        found = true;
      }
      REQUIRE(found);
    }
  }
}

TEST(effect_catalog_matches_current_authority_retirements_and_additions) {
  const auto& catalog = noisemaker::effects::effect_catalog();
  for (const char* id : {"filter/bc", "filter/colorspace", "filter/hs"}) {
    REQUIRE(catalog.find(id) == nullptr);
  }
  for (const char* id : {"render/meshLoader", "render/meshRender", "synth/roll", "synth/scope", "synth/spectrum"}) {
    REQUIRE(catalog.find(id) != nullptr);
  }
}
