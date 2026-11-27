#include "noisemaker/dsl/compiler.hpp"
#include "noisemaker/js_number.hpp"
#include "noisemaker/effects/catalog.hpp"

#include "test_harness.hpp"

#include <variant>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <charconv>
#include <limits>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace {
noisemaker::effects::EffectDefinition effect(std::string name, std::string kind = "generator") {
  noisemaker::effects::EffectDefinition result;
  result.id = "fixture/" + name;
  result.name_space = "fixture";
  result.function = std::move(name);
  result.kind = std::move(kind);
  result.domain = "image";
  noisemaker::effects::PassDefinition pass;
  pass.name = "main";
  pass.program = result.function;
  pass.outputs = {{"color", "outputTex"}};
  result.passes.push_back(std::move(pass));
  return result;
}
}

TEST(dsl_compiler_builds_owned_generator_read_write_plan) {
  noisemaker::effects::EffectRegistry registry({effect("source")});
  const auto plan = noisemaker::dsl::compile("search fixture\nsource().write(o2)\n", registry);
  REQUIRE(plan.search.size() == 1);
  REQUIRE(plan.chains.size() == 1);
  REQUIRE(plan.chains[0].steps.size() == 2);
  REQUIRE(std::holds_alternative<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]));
  REQUIRE(plan.render_surface.name == "o2");
  REQUIRE(plan.executable);
}

TEST(dsl_compiler_rejects_generator_without_final_write) {
  noisemaker::effects::EffectRegistry registry({effect("source")});
  REQUIRE_THROWS_AS(noisemaker::dsl::compile("search fixture\nsource()\n", registry), noisemaker::dsl::DslError);
}

TEST(dsl_compiler_fails_closed_for_missing_compatibility) {
  auto source = effect("source");
  noisemaker::effects::EffectCatalog catalog;
  catalog.definitions.push_back(source);
  noisemaker::effects::ProgramCompatibility row;
  row.program_key = "fixture/source:source";
  row.status = "missing";
  row.reasons.push_back({"missing_backend_program", row.program_key});
  noisemaker::effects::ReferencePassCompatibility reference;
  reference.effect_id = source.id;
  reference.pass_index = 0;
  reference.pass_name = "main";
  reference.program_key = row.program_key;
  reference.status = "missing";
  reference.reasons = row.reasons;
  catalog.reference_passes.push_back(reference);
  noisemaker::effects::EffectRegistry registry(catalog);
  const auto inspected = noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry);
  REQUIRE(!inspected.executable);
  REQUIRE(inspected.availability.size() == 1);
  REQUIRE_THROWS_AS(noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry,
                                               {.require_executable = true}), noisemaker::dsl::DslError);
}

TEST(dsl_compiler_accepts_real_catalog_generator_and_multipass_filter) {
  noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto solid = noisemaker::dsl::compile(
      "search synth, filter\nsolid(color: #3a7).write(o0)\nrender(o0)\n", registry);
  REQUIRE(solid.executable);
  REQUIRE(solid.availability.size() == 1);
  const auto blur = noisemaker::dsl::compile(
      "search synth, filter\nsolid().blur(radiusX: 3, radiusY: 2).write(o0)\nrender(o0)\n", registry);
  REQUIRE(blur.executable);
  REQUIRE(blur.availability.size() == 3);
}

TEST(dsl_compiler_merges_named_partials_in_stable_key_order) {
  auto source = effect("source");
  noisemaker::effects::ParameterDefinition first;
  first.name = "first";
  first.type = "int";
  first.default_value = noisemaker::effects::Value::number_value(1.0);
  source.parameters.push_back(first);
  noisemaker::effects::ParameterDefinition second;
  second.name = "second";
  second.type = "int";
  second.default_value = noisemaker::effects::Value::number_value(2.0);
  source.parameters.push_back(second);
  noisemaker::effects::EffectRegistry registry({source});
  const auto plan = noisemaker::dsl::compile(
      "search fixture\nlet p = source(first: 3, second: 4)\np(second: 7).write(o0)\n", registry);
  const auto& step = std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]);
  REQUIRE(step.params[0].name == "first");
  REQUIRE(step.params[0].value.number == 3.0);
  REQUIRE(step.params[1].value.number == 7.0);
}

TEST(dsl_compiler_omits_unsupported_inputs_without_shifting_positional_arguments) {
  auto source = effect("source");
  for (const auto& name : {"first", "second"}) {
    noisemaker::effects::ParameterDefinition parameter;
    parameter.name = name;
    parameter.type = "float";
    parameter.default_value = noisemaker::effects::Value::number_value(3.0);
    source.parameters.push_back(parameter);
  }
  noisemaker::effects::EffectRegistry registry({source});
  for (const auto& arguments : {"midi(channel: 1), 7", "audio(band: low), 7", "first: midi(1, min: 0.8), second: 7"}) {
    const auto plan = noisemaker::dsl::compile(std::string("search fixture\nsource(") + arguments + ").write(o0)\n", registry);
    const auto& step = std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]);
    REQUIRE(step.params[0].value.number == 3.0);
    REQUIRE(step.params[1].value.number == 7.0);
    REQUIRE(step.explicit_params.size() == 1);
    REQUIRE(step.explicit_params[0] == "second");
  }
}

namespace {
// The real catalog's plan for `source`; the expected values below are the
// pinned authority's (tests/oracles/dsl_compiler_expected.txt).
noisemaker::graph::ExecutionPlan catalog_plan(const std::string& source) {
  static const noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  return noisemaker::dsl::compile(source, registry);
}
const noisemaker::graph::EffectStep& effect_step(const noisemaker::graph::ExecutionChain& chain, std::size_t index) {
  return std::get<noisemaker::graph::EffectStep>(chain.steps.at(index));
}
const noisemaker::graph::PlanValue& param_value(const noisemaker::graph::EffectStep& step, std::string_view name) {
  for (const auto& binding : step.params) if (binding.name == name) return binding.value;
  throw std::out_of_range("no parameter " + std::string(name));
}
}  // namespace

TEST(dsl_compiler_preserves_element_ids_across_saved_effects_inline_chains_and_io) {
  auto plan = catalog_plan(R"(search synth,synth3d,filter,mixer,render
let n=noise(_id:'base_2',seed:1)
n().subchain(id:'block'){.invert(_id:'flip')}.write(o1,_id:'w')
read(tex:o1,_skip:true,_id:'r').blendMode(tex:n(_id:'over')).write(o0)
noise3d().write3d(vol0,geo0,_id:'w3')
read3d(_skip:true,_id:'r3',tex3d:vol0,geo:geo0).render3d().write(o3)
read3d(vol0,geo0,_id:'r4',).render3d().write(o4))");
  using namespace noisemaker::graph;
  REQUIRE(validate_execution_plan(plan));
  REQUIRE(effect_step(plan.chains[0], 0).id == "base_2");
  REQUIRE(effect_step(plan.chains[0], 1).id == "flip");
  REQUIRE(std::get<WriteStep>(plan.chains[0].steps[2]).id == "w");
  const auto& read = std::get<ReadStep>(plan.chains[1].steps[0]);
  REQUIRE(read.id == "r" && read.skip && read.surface.name == "o1");
  const auto& overlay = effect_step(effect_step(plan.chains[1], 1).inline_chains.at(0).chain, 0);
  REQUIRE(overlay.id == "over");
  REQUIRE(overlay.explicit_params == std::vector<std::string>({"seed"}));
  REQUIRE(std::get<Write3DStep>(plan.chains[2].steps[1]).id == "w3");
  const auto& read3d = std::get<Read3DStep>(plan.chains[3].steps[0]);
  REQUIRE(read3d.id == "r3" && read3d.skip && read3d.geometry == "geo0");
  REQUIRE(std::get<Read3DStep>(plan.chains[4].steps[0]).id == "r4");
  std::get<ReadStep>(plan.chains[1].steps[0]).skip = false;
  REQUIRE(!validate_execution_plan(plan));
  std::get<ReadStep>(plan.chains[1].steps[0]).skip = true;
  std::get<WriteStep>(plan.chains[0].steps[2]).id = "modified";
  REQUIRE(!validate_execution_plan(plan));
}

TEST(dsl_compiler_ignores_invalid_id_expressions_and_enforces_io_argument_forms) {
  for (std::string id : {"''", "'9a'", "'a-b'", "'_x'", "5", "alias", "unknown()"}) {
    const auto plan = catalog_plan("search synth; let alias='valid'; let t=noise(_id:'base'); t(_id:" + id +
        ").write(o1,_id:" + id + "); read(o1,_id:" + id + ").write(o0)");
    REQUIRE(!effect_step(plan.chains[0], 0).id);
    REQUIRE(!std::get<noisemaker::graph::WriteStep>(plan.chains[0].steps[1]).id);
    REQUIRE(!std::get<noisemaker::graph::ReadStep>(plan.chains[1].steps[0]).id);
  }
  for (std::string call : {"noise(1,_id:'x').write(o0)", "noise(_id:'x',1).write(o0)",
      "noise().write(o0,)", "noise().write(surface:o0,_id:'x')", "noise().write(o0,_id:'x',)",
      "noise().write(o0,other:1)", "noise(_skip:true).write(o0)", "read(o0,other:1).write(o0)",
      "read(o0,_skip:true).write(o0)", "noise3d().write3d(vol0,geo0,_id:'x',)",
      "read3d(vol0,geo0,other:1).render3d().write(o0)"}) {
    REQUIRE_THROWS_AS(catalog_plan("search synth,synth3d,render; " + call), noisemaker::dsl::DslError);
  }
  auto plan = catalog_plan("search synth,mixer; noise().blendMode(tex:read(_id:'r',tex:o1,_skip:true)).write(o0)");
  REQUIRE(param_value(effect_step(plan.chains[0],1),"tex").surface.name == "o1");
}

TEST(dsl_compiler_binds_stable_lists_discards_unused_expressions_and_captures_hex_colors) {
  for (std::string call : {"solid(color:[1,0.25,0.5,],)", "solid([1,0.25,0.5,/*end*/],)",
                            "solid(color:vec3(1,0.25,0.5,),)"}) {
    const auto plan = catalog_plan("search synth; " + call + ".write(o0)");
    REQUIRE(param_value(effect_step(plan.chains[0],0),"color").array[1].number == 0.25);
  }
  for (std::string call : {"solid([1,,0])", "solid([,1])", "noise(,)", "noise(12,,)", "noise(scaleX:,)",
                          "noise(seed:7,12)", "noise(12,seed:7)", "noise({seed:7})"}) {
    REQUIRE_THROWS_AS(catalog_plan("search synth; " + call + ".write(o0)"), noisemaker::dsl::DslError);
  }
  for (std::string body : {"let t=noise(seed:7); t(3,4,)", "let t=noise(3,4); t(seed:7,)",
                            "let t=noise(seed:7); let u=t; u(3,4)"}) {
    const auto plan = catalog_plan("search synth; " + body + ".write(o0)");
    const auto& step = effect_step(plan.chains[0],0);
    REQUIRE(param_value(step,"type").number == 3.0 && param_value(step,"octaves").number == 4.0);
    REQUIRE(param_value(step,"seed").number == 7.0);
  }
  const auto overridden = catalog_plan("search synth; let t=noise(type:11); t(bogus(),4).write(o0)");
  REQUIRE(param_value(effect_step(overridden.chains[0],0),"type").number == 11.0);
  std::ostringstream warnings;
  auto* old = std::cerr.rdbuf(warnings.rdbuf());
  try {
    const auto extra = catalog_plan("search synth; let t=solid(#f00); t(1,unknown()).write(o0)");
    REQUIRE(effect_step(extra.chains[0],0).inline_chains.empty());
  } catch (...) { std::cerr.rdbuf(old); throw; }
  std::cerr.rdbuf(old);
  REQUIRE(warnings.str() == "Too many positional arguments for solid(): 'solid' takes 2\n");
  const auto nested = catalog_plan("search synth,filter,mixer; let c=#f00; let alias=c; let t=blendMode(tex:solid(color:alias).invert()); let u=t(mix:.5); let c=#0f0; let alias=#00f; noise().u(_id:'m').write(o0)");
  const auto& inner = effect_step(effect_step(nested.chains[0],1).inline_chains.at(0).chain,0);
  REQUIRE(param_value(inner,"color").array[0].number == 1.0 && param_value(inner,"color").array[2].number == 0.0);
}

TEST(dsl_compiler_reports_invalid_inline_chains_at_the_stored_first_call) {
  for (const auto& [prefix, rest] : std::vector<std::pair<std::string,std::string>>{
      {"noise().blendMode(tex: ", "read(o1).invert()).write(o0)"},
      {"noise().blendMode(", "read3d(vol0,geo0).render3d()).write(o0)"},
      {"noise().blendMode(tex: ", "noise().subchain('s'){.invert()}).write(o0)"},
      {"let t=blendMode(tex: ", "read(o1).invert()); noise().t().write(o0)"},
      {"let layer = ", "read(o1).invert(); noise().blendMode(tex:layer).write(o0)"}}) {
    try { static_cast<void>(catalog_plan("search synth,synth3d,filter,mixer,render\n" + prefix + rest)); }
    catch (const noisemaker::dsl::DslError& error) {
      REQUIRE(error.code == "S001");
      REQUIRE(error.line == 2 && error.column == prefix.size() + 1);
      REQUIRE(error.detail() == "Chain for argument 'tex' in blendMode() may contain only effect calls");
      continue;
    }
    REQUIRE(false);
  }
}

TEST(dsl_compiler_splats_hex_color_into_rgb_slots_with_partial_keyword_precedence) {
  auto probe = effect("rgb");
  for (const auto* name : {"r","g","b","a"}) {
    noisemaker::effects::ParameterDefinition p;
    p.name = name; p.type = "float"; p.default_value = noisemaker::effects::Value::number_value(1.0);
    probe.parameters.push_back(std::move(p));
  }
  const noisemaker::effects::EffectRegistry registry({probe});
  for (const auto& [body, expected] : std::vector<std::pair<std::string,std::vector<double>>>{
      {"let c=#804020; let t=rgb(c,.5,.6,.7); let c=#fff; t(g:.25)", {128.0/255.0,.25,32.0/255.0,.7}},
      {"let t=rgb(r:.25); let u=t(#804020,.6); u(_id:'u')", {.25,.6,1.0,1.0}},
      {"let t=rgb(_id:'t'); t(#f00)", {1.0,0.0,0.0,1.0}}}) {
    const auto plan = noisemaker::dsl::compile("search fixture; " + body + ".write(o0)", registry);
    const auto& step = effect_step(plan.chains[0],0);
    for (std::size_t i = 0; i < expected.size(); ++i) REQUIRE(step.params[i].value.number == expected[i]);
  }
  REQUIRE_THROWS_AS(noisemaker::dsl::compile("search fixture; rgb([1,0,0]).write(o0)",registry),noisemaker::dsl::DslError);
}

TEST(dsl_compiler_lets_follow_statement_order_and_reassignment) {
  const auto plan = catalog_plan("search synth\nlet x = 10\nnoise(scaleX: x).write(o0)\nlet x = 90\nnoise(scaleX: x).write(o1)\nrender(o1)\n");
  REQUIRE(param_value(effect_step(plan.chains[0], 0), "scaleX").number == 10.0);
  REQUIRE(param_value(effect_step(plan.chains[1], 0), "scaleX").number == 90.0);
}

TEST(dsl_compiler_lets_reject_pending_reads_in_inline_chains) {
  try {
    static_cast<void>(catalog_plan("search synth, mixer\nnoise().blendMode(tex: noise(scaleX: x)).write(o0)\nlet x = 20\nrender(o0)\n"));
    REQUIRE(false);
  } catch (const noisemaker::dsl::DslError& error) {
    REQUIRE(std::string(error.what()).find("Variable used before assignment: 'x'") != std::string::npos);
    REQUIRE(error.line == 2);
  }
}

TEST(dsl_compiler_lets_resolve_forward_expressions_once_at_first_use) {
  const auto plan = catalog_plan("search synth\nlet a = b + 1\nlet b = 5\nnoise(scaleX: a).write(o0)\nlet b = 90\nnoise(scaleX: a).write(o1)\nrender(o1)\n");
  REQUIRE(param_value(effect_step(plan.chains[0], 0), "scaleX").number == 6.0);
  REQUIRE(param_value(effect_step(plan.chains[1], 0), "scaleX").number == 6.0);
}

TEST(dsl_compiler_lets_reject_unresolved_bare_names_at_declaration) {
  for (const auto& source : {"search synth\nlet a = b\nlet b = 5\nnoise().write(o0)\n", "search synth\nnoise().write(o0)\nlet a = b\n"}) {
    try {
      static_cast<void>(catalog_plan(source));
      REQUIRE(false);
    } catch (const noisemaker::dsl::DslError& error) {
      REQUIRE(std::string(error.what()).find("Variable used before assignment: 'b'") != std::string::npos);
    }
  }
}

TEST(dsl_compiler_lets_resolve_nested_oscillator_forward_references) {
  const auto plan = catalog_plan("search synth\nlet outer = osc(type: oscKind.sine, speed: inner)\nlet inner = osc(type: oscKind.tri, speed: 2)\nnoise(scaleX: outer).write(o0)\n");
  const auto& outer = param_value(effect_step(plan.chains[0], 0), "scaleX");
  REQUIRE(outer.kind == noisemaker::graph::PlanValue::Kind::oscillator);
  REQUIRE(outer.number == 0.0);
  REQUIRE(outer.array.at(2).kind == noisemaker::graph::PlanValue::Kind::oscillator);
  REQUIRE(outer.array.at(2).number == 1.0);
  REQUIRE(outer.array.at(2).array.at(2).number == 2.0);
}

TEST(dsl_compiler_lets_report_cycles_through_arithmetic_and_oscillators) {
  for (const auto& source : {"search synth\nlet a = b + 1\nlet b = a + 1\nnoise(scaleX: a).write(o0)\n", "search synth\nlet a = osc(speed: b)\nlet b = osc(speed: a)\nnoise(scaleX: a).write(o0)\n"}) {
    try {
      static_cast<void>(catalog_plan(source));
      REQUIRE(false);
    } catch (const noisemaker::dsl::DslError& error) {
      REQUIRE(std::string(error.what()).find("Automation cycle detected: a -> b -> a") != std::string::npos);
      REQUIRE(error.line == 3);
    }
  }
}

TEST(dsl_compiler_lets_resolve_partial_arguments_at_each_call) {
  const auto plan = catalog_plan("search synth\nlet p = noise(scaleX: x)\nlet q = p\nlet x = 10\nq().write(o0)\nlet x = 90\np().write(o1)\n");
  REQUIRE(param_value(effect_step(plan.chains[0], 0), "scaleX").number == 10.0);
  REQUIRE(param_value(effect_step(plan.chains[1], 0), "scaleX").number == 90.0);
}

TEST(dsl_compiler_flattens_a_subchain_into_its_chain) {
  const auto plan = catalog_plan("search synth, filter\nnoise(seed: 1).subchain(name: \"look\", id: \"a\") { .invert() .posterize(levels: 4) }.write(o0)\nrender(o0)\n");
  REQUIRE(plan.chains.size() == 1);
  REQUIRE(plan.chains[0].steps.size() == 4);
  REQUIRE(effect_step(plan.chains[0], 0).effect.id == "synth/noise");
  REQUIRE(effect_step(plan.chains[0], 1).effect.id == "filter/invert");
  REQUIRE(effect_step(plan.chains[0], 2).effect.id == "filter/posterize");
  REQUIRE(param_value(effect_step(plan.chains[0], 2), "levels").number == 4.0);
  REQUIRE(std::holds_alternative<noisemaker::graph::WriteStep>(plan.chains[0].steps[3]));
  REQUIRE_THROWS_AS(catalog_plan("search synth, filter\nnoise(seed: 1).subchain() { .noise() }.write(o0)\nrender(o0)\n"),
                    noisemaker::dsl::DslError);
}

TEST(dsl_compiler_compiles_a_chain_argument_to_a_hidden_surface) {
  const auto plan = catalog_plan("search synth, mixer\nnoise(seed: 1).blendMode(tex: solid(color: #ff0000), mode: screen).write(o0)\nrender(o0)\n");
  const auto& blend = effect_step(plan.chains[0], 1);
  REQUIRE(blend.effect.id == "mixer/blendMode");
  const auto& tex = param_value(blend, "tex");
  REQUIRE(tex.kind == noisemaker::graph::PlanValue::Kind::surface);
  REQUIRE(tex.surface.kind == noisemaker::graph::SurfaceReference::Kind::named);
  REQUIRE(tex.surface.name == "inline:0");
  REQUIRE(param_value(blend, "mode").number == 13.0);
  REQUIRE(blend.explicit_params == std::vector<std::string>({"tex", "mode"}));
  REQUIRE(blend.inline_chains.size() == 1);
  REQUIRE(blend.inline_chains[0].surface == "inline:0");
  REQUIRE(blend.inline_chains[0].chain.steps.size() == 1);
  REQUIRE(effect_step(blend.inline_chains[0].chain, 0).effect.id == "synth/solid");
  REQUIRE_THROWS_AS(catalog_plan("search filter, mixer, synth\nnoise(seed: 1).blendMode(tex: invert(), mode: screen).write(o0)\nrender(o0)\n"),
                    noisemaker::dsl::DslError);
}

TEST(dsl_compiler_accepts_math_pi_triple_quoted_strings_aliases_and_from) {
  const auto pi = catalog_plan("search synth\nnoise(seed: 1, scaleX: Math.PI * 4).write(o0)\nrender(o0)\n");
  REQUIRE(param_value(effect_step(pi.chains[0], 0), "scaleX").number == 12.566370614359172);
  const auto text = catalog_plan("search synth, filter\nsolid(color: #000).text(text: \"\"\"hi\"\"\").write(o0)\nrender(o0)\n");
  REQUIRE(param_value(effect_step(text.chains[0], 1), "text").string == "hi");
  const auto alias = catalog_plan("search synth\nlet pattern = noise\npattern(seed: 3).write(o0)\nrender(o0)\n");
  REQUIRE(effect_step(alias.chains[0], 0).effect.id == "synth/noise");
  REQUIRE(param_value(effect_step(alias.chains[0], 0), "seed").number == 3.0);
  REQUIRE_THROWS_AS(catalog_plan("search synth\nlet pattern = wobble\npattern().write(o0)\nrender(o0)\n"),
                    noisemaker::dsl::DslError);
  const auto from = catalog_plan("search synth, filter\nfrom(classicNoisedeck, noise(seed: 3)).write(o0)\nrender(o0)\n");
  REQUIRE(effect_step(from.chains[0], 0).effect.id == "classicNoisedeck/noise");
}

TEST(dsl_compiler_compiles_write3d_and_read3d_volume_steps) {
  const auto plan = catalog_plan("search synth3d, render\nnoise3d(seed: 1, volumeSize: 8).write3d(vol0, geo0)\nread3d(vol0, geo0).render3d().write(o0)\nrender(o0)\n");
  REQUIRE(plan.chains.size() == 2);
  REQUIRE(plan.chains[0].steps.size() == 2);
  const auto& written = std::get<noisemaker::graph::Write3DStep>(plan.chains[0].steps[1]);
  REQUIRE(written.volume == "vol0");
  REQUIRE(written.geometry == "geo0");
  const auto& read = std::get<noisemaker::graph::Read3DStep>(plan.chains[1].steps[0]);
  REQUIRE(read.volume == "vol0");
  REQUIRE(read.geometry == "geo0");
  REQUIRE(effect_step(plan.chains[1], 1).effect.id == "render/render3d");
}

TEST(dsl_compiler_resolves_float_parameter_choice_names) {
  for (const auto& [value, expected] : {std::pair<const char*, double>{"fwd", 1.0}, {"back", -1.0}, {"none", 0.0},
                                        {"choices.back", -1.0}, {"0.5", 0.5}}) {
    const auto plan = catalog_plan(std::string("search filter, synth\nnoise(seed: 1, ridges: true).palette(rotation: ") + value +
                                   ").write(o0)\nrender(o0)\n");
    REQUIRE(param_value(effect_step(plan.chains[0], 1), "rotation").number == expected);
  }
}

TEST(dsl_compiler_preserves_scatter_and_rejects_an_unknown_program) {
  noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto scatter = noisemaker::dsl::compile(
      "search filter\nread(o0).wormhole().write(o1)\nrender(o1)\n", registry);
  REQUIRE(scatter.executable);
  bool saw_scatter = false;
  for (const auto& pass : scatter.availability) saw_scatter |= pass.status == noisemaker::graph::AvailabilityStatus::scatter;
  REQUIRE(saw_scatter);
  REQUIRE_THROWS_AS(noisemaker::dsl::compile(
      "search synth3d, render\nnotInCatalog().write(o1)\nrender(o1)\n", registry),
      noisemaker::dsl::DslError);
}

TEST(dsl_compiler_plan_copy_owns_nested_parameter_arrays) {
  auto source = effect("source");
  noisemaker::effects::ParameterDefinition vector;
  vector.name = "vector";
  vector.type = "vec3";
  vector.default_value = noisemaker::effects::Value::array_value({
      noisemaker::effects::Value::number_value(1.0),
      noisemaker::effects::Value::number_value(2.0),
      noisemaker::effects::Value::number_value(3.0)});
  source.parameters.push_back(vector);
  noisemaker::effects::EffectRegistry registry({source});
  auto original = noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry);
  auto copied = original;
  auto& copied_step = std::get<noisemaker::graph::EffectStep>(copied.chains[0].steps[0]);
  copied_step.params[0].value.array[0].number = 99.0;
  const auto& original_step = std::get<noisemaker::graph::EffectStep>(original.chains[0].steps[0]);
  REQUIRE(original_step.params[0].value.array[0].number == 1.0);
}

TEST(dsl_compiler_owns_complete_effect_snapshot_and_admissions) {
  auto source = effect("source");
  noisemaker::effects::ParameterDefinition parameter;
  parameter.name = "radius";
  parameter.type = "float";
  parameter.default_value = noisemaker::effects::Value::number_value(2.0);
  parameter.raw = {{"custom", noisemaker::effects::Value::string_value("kept")}};
  source.parameters.push_back(parameter);
  noisemaker::effects::TextureDefinition texture;
  texture.name = "_blurTemp";
  texture.width.kind = noisemaker::effects::DimensionKind::input;
  texture.height.kind = noisemaker::effects::DimensionKind::input;
  texture.format = "rgba8unorm";
  texture.raw = {{"format", noisemaker::effects::Value::string_value("rgba8unorm")}};
  source.textures.push_back(texture);
  source.passes[0].inputs = {{"inputTex", "inputTex"}};
  source.passes[0].uniforms = {{"radius", noisemaker::effects::Value::number_value(2.0)}};
  source.passes[0].repeat = noisemaker::effects::Value::number_value(2.0);
  source.passes[0].conditions = noisemaker::effects::Value::boolean_value(true);
  source.passes[0].viewport = noisemaker::effects::Value::string_value("screen");
  source.passes[0].draw_mode = "fragment";
  source.passes[0].draw_buffers = noisemaker::effects::Value::number_value(1.0);
  source.passes[0].raw = {{"draw_mode", noisemaker::effects::Value::string_value("fragment")}};
  noisemaker::effects::EffectRegistry registry({source});

  const std::string dsl = "search fixture\nsource(radius: 3).write(o0)\n";
  const auto plan = noisemaker::dsl::compile(dsl, registry, {}, "snapshot.dsl");
  REQUIRE(plan.effects.size() == 1);
  REQUIRE(plan.provenance.source_name == "snapshot.dsl");
  REQUIRE(plan.provenance.source_sha256 == "fa4944a520a70cdc2a33345c4df28b4bef92f50ad1d53fcd202194d7d5058d99");
  REQUIRE(plan.provenance.plan_payload_sha256.size() == 64);
  const auto& snapshot = plan.effects.front();
  REQUIRE(snapshot.definition.id == source.id);
  REQUIRE(snapshot.definition.parameters.front().raw.front().first == "custom");
  REQUIRE(snapshot.definition.textures.front().format == "rgba8unorm");
  REQUIRE(snapshot.definition.passes.front().repeat.has_value());
  REQUIRE(snapshot.definition.passes.front().conditions.has_value());
  REQUIRE(snapshot.definition.passes.front().viewport.has_value());
  REQUIRE(snapshot.definition.passes.front().draw_buffers.has_value());
  REQUIRE(snapshot.definition.passes.front().raw.front().first == "draw_mode");
  REQUIRE(snapshot.admissions.size() == snapshot.definition.passes.size());
  REQUIRE(snapshot.snapshot_sha256.size() == 64);
  const auto& step = std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]);
  REQUIRE(step.snapshot_index == 0);
  REQUIRE(noisemaker::graph::validate_execution_plan(plan));
}

TEST(dsl_compiler_plan_remains_valid_after_registry_lifetime) {
  noisemaker::graph::ExecutionPlan plan;
  {
    noisemaker::effects::EffectRegistry registry({effect("lifetime")});
    plan = noisemaker::dsl::compile("search fixture\nlifetime().write(o0)\n", registry);
  }
  REQUIRE(plan.effects.size() == 1);
  REQUIRE(noisemaker::graph::validate_execution_plan(plan));
  REQUIRE(plan.effects.front().definition.id == "fixture/lifetime");
}

TEST(dsl_compiler_deduplicates_snapshots_in_first_use_order) {
  auto repeated = effect("repeated", "filter");
  noisemaker::effects::EffectRegistry registry({repeated});
  const auto plan = noisemaker::dsl::compile(
      "search fixture\nrepeated().repeated().write(o0)\n", registry);
  REQUIRE(plan.effects.size() == 1);
  REQUIRE(std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[0]).snapshot_index == 0);
  REQUIRE(std::get<noisemaker::graph::EffectStep>(plan.chains[0].steps[1]).snapshot_index == 0);
}

TEST(dsl_compiler_snapshot_and_payload_hashes_detect_mutation_and_copy_deterministically) {
  noisemaker::effects::EffectRegistry registry({effect("source")});
  const auto original = noisemaker::dsl::compile("search fixture\nsource().write(o0)\n", registry);
  const auto copied = original;
  REQUIRE(copied.provenance.plan_payload_sha256 == original.provenance.plan_payload_sha256);
  REQUIRE(copied.effects[0].snapshot_sha256 == original.effects[0].snapshot_sha256);
  REQUIRE(noisemaker::graph::validate_execution_plan(copied));

  auto mutated = original;
  mutated.effects[0].definition.passes[0].outputs[0].second = "mutated_route";
  REQUIRE(!noisemaker::graph::validate_execution_plan(mutated));
  mutated = original;
  auto& mutated_step = std::get<noisemaker::graph::EffectStep>(mutated.chains[0].steps[0]);
  mutated_step.params.push_back({"late", noisemaker::graph::PlanValue::number_value(1.0)});
  REQUIRE(!noisemaker::graph::validate_execution_plan(mutated));
}

TEST(dsl_compiler_snapshot_authenticates_every_nested_definition_and_admission_field) {
  auto definition = effect("complete");
  definition.directory_name = "complete-dir";
  definition.name = "Complete";
  definition.tags = {"fixture", "complete"};
  definition.description = "complete definition";
  definition.parameter_aliases = {{"old", "new"}};
  definition.external_texture = "externalTex";
  definition.output_tex3d = "volumeOut";
  definition.output_geo = "geoOut";
  definition.output_xyz = "xyzOut";
  definition.output_velocity = "velocityOut";
  definition.output_rgba = "rgbaOut";
  definition.iterated = true;
  definition.loop_role = "loop";
  definition.raw = {{"effect_raw", noisemaker::effects::Value::string_value("kept")}};
  noisemaker::effects::ParameterDefinition parameter;
  parameter.name = "amount";
  parameter.type = "float";
  parameter.default_value = noisemaker::effects::Value::number_value(1.0);
  parameter.define = "AMOUNT";
  parameter.uniform = "amount";
  parameter.zero = noisemaker::effects::Value::number_value(0.0);
  parameter.enum_values = {{"one", noisemaker::effects::Value::number_value(1.0)}};
  parameter.enum_name = "Amount";
  parameter.choices = {{"one", noisemaker::effects::Value::number_value(1.0)}};
  parameter.min = noisemaker::effects::Value::number_value(0.0);
  parameter.max = noisemaker::effects::Value::number_value(2.0);
  parameter.texture = "amountTex";
  parameter.color_mode_uniform = "amountMode";
  parameter.cpu_only = true;
  parameter.raw = {{"parameter_raw", noisemaker::effects::Value::boolean_value(true)}};
  definition.parameters.push_back(parameter);
  noisemaker::effects::TextureDefinition texture;
  texture.name = "amountTex";
  texture.width.kind = noisemaker::effects::DimensionKind::literal;
  texture.width.literal = 17.0;
  texture.width.raw = noisemaker::effects::Value::number_value(17.0);
  texture.height.kind = noisemaker::effects::DimensionKind::parameter;
  texture.height.parameter = "amount";
  texture.height.raw = noisemaker::effects::Value::string_value("amount");
  texture.format = "rgba16float";
  texture.raw = {{"texture_raw", noisemaker::effects::Value::string_value("kept")}};
  definition.textures.push_back(texture);
  auto& pass = definition.passes.front();
  pass.inputs = {{"inputTex", "inputTex"}};
  pass.outputs = {{"color", "outputTex"}};
  pass.uniforms = {{"amount", noisemaker::effects::Value::number_value(1.0)}};
  pass.count = noisemaker::effects::Value::number_value(1.0);
  pass.repeat = noisemaker::effects::Value::number_value(2.0);
  pass.conditions = noisemaker::effects::Value::boolean_value(true);
  pass.viewport = noisemaker::effects::Value::string_value("screen");
  pass.blend = noisemaker::effects::BlendDefinition{noisemaker::effects::BlendKind::factors, true, {"src", "dst"}};
  pass.draw_mode = "points";
  pass.draw_buffers = noisemaker::effects::Value::number_value(1.0);
  pass.raw = {{"pass_raw", noisemaker::effects::Value::string_value("kept")}};
  noisemaker::effects::EffectRegistry registry({definition});
  const auto original = noisemaker::dsl::compile("search fixture\ncomplete().write(o0)\n", registry);
  REQUIRE(noisemaker::graph::validate_execution_plan(original));

  const auto rejects = [&](auto mutate) {
    auto mutated = original;
    mutate(mutated);
    REQUIRE(!noisemaker::graph::validate_execution_plan(mutated));
  };
  rejects([](auto& plan) { plan.effects[0].definition.parameters[0].default_value->number = 9.0; });
  rejects([](auto& plan) { plan.effects[0].definition.parameters[0].raw[0].second.boolean = false; });
  rejects([](auto& plan) { plan.effects[0].definition.textures[0].width.literal = 18.0; });
  rejects([](auto& plan) { plan.effects[0].definition.textures[0].raw[0].second.string = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].inputs[0].second = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].uniforms[0].second.number = 9.0; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].repeat->number = 9.0; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].conditions->boolean = false; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].viewport->string = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].blend->factors[0] = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].draw_mode = "lines"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].draw_buffers->number = 2.0; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].raw[0].second.string = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.external_texture = "changed"; });
  rejects([](auto& plan) { plan.effects[0].definition.output_tex = "replacement"; });
  rejects([](auto& plan) { plan.effects[0].definition.passes[0].storage_textures.emplace_back("frag", "replacement"); });
  rejects([](auto& plan) { plan.effects[0].definition.raw[0].second.string = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].canonical_factory = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].source_sha256 = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].semantic_sha256 = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].emitted_factory = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].route_kind = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].typed_abi_sha256 = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].binding_abi_sha256 = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].output_extent.width = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].output_extent.height = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].output_extent.format = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].compile_defines.push_back({"D", {}, "custom_adapter", {}, {}, "std::int32_t"}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].capabilities.push_back("changed"); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].dimensionality = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].draw_mode = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].samplers.push_back({"s", "t", "source", "source", "resource", "cpp"}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].uniforms.push_back({"u", "t", "source", "source", "resource", "cpp"}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].outputs.push_back({1U, "o", "route", "cpp"}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].authority_pass.name = "changed"; });
  rejects([](auto& plan) { plan.effects[0].admissions[0].authority_pass.inputs.push_back({"changed", "route"}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].authority_pass.uniforms.push_back({"changed", noisemaker::graph::PlanValue::number_value(1.0)}); });
  rejects([](auto& plan) { plan.effects[0].admissions[0].scatter = noisemaker::graph::ScatterContract{}; });
  rejects([](auto& plan) { plan.effects[0].snapshot_sha256[0] = plan.effects[0].snapshot_sha256[0] == '0' ? '1' : '0'; });
  rejects([](auto& plan) { plan.provenance.plan_payload_sha256[0] = plan.provenance.plan_payload_sha256[0] == '0' ? '1' : '0'; });
}

TEST(dsl_compiler_snapshot_authenticates_every_scatter_contract_field) {
  noisemaker::effects::EffectRegistry registry(noisemaker::effects::effect_catalog());
  const auto original = noisemaker::dsl::compile(
      "search filter\nread(o0).wormhole().write(o1)\nrender(o1)\n", registry);
  REQUIRE(original.effects.size() == 1);
  REQUIRE(original.effects.front().admissions.size() == 3);
  REQUIRE(original.effects.front().admissions[1].scatter.has_value());
  REQUIRE(noisemaker::graph::validate_execution_plan(original));

  const auto rejects = [&](auto mutate) {
    auto mutated = original;
    mutate(*mutated.effects.front().admissions[1].scatter);
    REQUIRE(!noisemaker::graph::validate_execution_plan(mutated));
  };
  rejects([](auto& scatter) { scatter.adapter = "changed"; });
  rejects([](auto& scatter) { scatter.registry = "changed"; });
  rejects([](auto& scatter) { scatter.draw_mode = "changed"; });
  rejects([](auto& scatter) { scatter.dimensionality = "changed"; });
  rejects([](auto& scatter) { scatter.count = "changed"; });
  rejects([](auto& scatter) { scatter.input_texture = "changed"; });
  rejects([](auto& scatter) { scatter.destination_mutation = "changed"; });
  rejects([](auto& scatter) { scatter.blend = !scatter.blend; });
  rejects([](auto& scatter) { scatter.uniforms[0].name = "changed"; });
  rejects([](auto& scatter) { scatter.uniforms[0].source = "changed"; });
  rejects([](auto& scatter) { scatter.uniforms[0].cpp_type = "changed"; });
  rejects([](auto& scatter) { scatter.outputs[0].slot = 9; });
  rejects([](auto& scatter) { scatter.outputs[0].physical_name = "changed"; });
  rejects([](auto& scatter) { scatter.outputs[0].logical_route = "changed"; });
  rejects([](auto& scatter) { scatter.outputs[0].cpp_type = "changed"; });
}

#ifdef NOISEMAKER_DSL_COMPILER_ORACLE_MAIN
namespace {
std::string oracle_escape(const std::string& value) {
  std::ostringstream out;
  out << '"';
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char byte : value) {
    if (byte == '"') out << "\\\"";
    else if (byte == '\\') out << "\\\\";
    else if (byte == '\n') out << "\\n";
    else if (byte == '\r') out << "\\r";
    else if (byte == '\t') out << "\\t";
    else if (byte < 0x20) out << "\\u00" << hex[(byte >> 4) & 0xf] << hex[byte & 0xf];
    else out << byte;
  }
  out << '"';
  return out.str();
}

// Was a second, independently written formatter whose iostream-style exponent
// emitted `number:1e-07` and `number:1e+20` where the JavaScript authority says
// `number:1e-7` and `number:100000000000000000000`. One serializer, shared with
// the lexer and parser oracles: see noisemaker/js_number.hpp.
std::string oracle_number(double value) {
  return noisemaker::js_number_stream_text(value);
}

std::string oracle_loc(const noisemaker::dsl::SourceLocation& location) {
  return "{\"sourceName\":" + oracle_escape(location.source_name) + ",\"line\":" +
         std::to_string(location.line) + ",\"column\":" + std::to_string(location.column) +
         ",\"index\":" + std::to_string(location.index) + "}";
}

std::string oracle_value(const noisemaker::graph::PlanValue& value) {
  using Kind = noisemaker::graph::PlanValue::Kind;
  if (value.kind == Kind::null_value) return "{\"kind\":\"null\"}";
  if (value.kind == Kind::boolean) return "{\"kind\":\"boolean\",\"value\":" + std::string(value.boolean ? "true" : "false") + "}";
  if (value.kind == Kind::number) return "{\"kind\":\"number\",\"value\":" + oracle_escape(oracle_number(value.number)) + "}";
  if (value.kind == Kind::string) return "{\"kind\":\"string\",\"value\":" + oracle_escape(value.string) + "}";
  if (value.kind == Kind::array) {
    std::string result = "{\"kind\":\"array\",\"values\":[";
    for (std::size_t index = 0; index < value.array.size(); ++index) { if (index) result += ','; result += oracle_value(value.array[index]); }
    return result + "]}";
  }
  if (value.kind == Kind::oscillator) {
    std::string result = "{\"kind\":\"oscillator\",\"oscType\":" +
                         std::to_string(static_cast<int>(value.number)) + ",\"fields\":[";
    for (std::size_t index = 0; index < value.array.size(); ++index) { if (index) result += ','; result += oracle_value(value.array[index]); }
    return result + "]}";
  }
  if (value.surface.kind == noisemaker::graph::SurfaceReference::Kind::input) return "{\"kind\":\"surface\",\"value\":{\"kind\":\"input\"}}";
  if (value.surface.kind == noisemaker::graph::SurfaceReference::Kind::named) {
    // The authority projection writes Number(name.slice(1)): an oN surface
    // has its index, a hidden `inline:N` surface has none (NaN, JSON null).
    const std::string& name = value.surface.name;
    const bool numbered = name.size() > 1 && name.front() == 'o' &&
        name.find_first_not_of("0123456789", 1) == std::string::npos;
    return "{\"kind\":\"surface\",\"value\":{\"kind\":\"named\",\"name\":" + oracle_escape(name) + ",\"index\":" +
           (numbered ? std::to_string(value.surface.index) : std::string("null")) + "}}";
  }
  return "{\"kind\":\"surface\",\"value\":{\"kind\":\"none\"}}";
}

std::string oracle_effect_value(const noisemaker::effects::Value& value) {
  using Kind = noisemaker::effects::ValueKind;
  if (value.kind == Kind::null_value) return "{\"kind\":\"null\"}";
  if (value.kind == Kind::boolean) return "{\"kind\":\"boolean\",\"value\":" + std::string(value.boolean ? "true" : "false") + "}";
  if (value.kind == Kind::number) return "{\"kind\":\"number\",\"value\":" + oracle_escape(oracle_number(value.number)) + "}";
  if (value.kind == Kind::string) return "{\"kind\":\"string\",\"value\":" + oracle_escape(value.string) + "}";
  if (value.kind == Kind::array) {
    std::string result = "{\"kind\":\"array\",\"values\":[";
    for (std::size_t index = 0; index < value.array.size(); ++index) {
      if (index) result += ',';
      result += oracle_effect_value(value.array[index]);
    }
    return result + "]}";
  }
  std::string result = "{\"kind\":\"object\",\"entries\":[";
  for (std::size_t index = 0; index < value.object.size(); ++index) {
    if (index) result += ',';
    result += "[" + oracle_escape(value.object[index].first) + "," + oracle_effect_value(value.object[index].second) + "]";
  }
  return result + "]}";
}

std::string oracle_optional_effect_value(const std::optional<noisemaker::effects::Value>& value) {
  if (!value.has_value()) return "{\"present\":false}";
  return "{\"present\":true,\"value\":" + oracle_effect_value(*value) + "}";
}

std::string oracle_optional_plan_value(const std::optional<noisemaker::graph::PlanValue>& value) {
  if (!value.has_value()) return "{\"present\":false}";
  return "{\"present\":true,\"value\":" + oracle_value(*value) + "}";
}

std::string oracle_optional_string(const std::optional<std::string>& value) {
  if (!value.has_value()) return "{\"present\":false}";
  return "{\"present\":true,\"value\":" + oracle_escape(*value) + "}";
}

std::string oracle_effect_string_pairs(const std::vector<std::pair<std::string, std::string>>& values) {
  std::string result = "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index) result += ',';
    result += "[" + oracle_escape(values[index].first) + "," + oracle_escape(values[index].second) + "]";
  }
  return result + "]";
}

std::string oracle_effect_value_pairs(const std::vector<std::pair<std::string, noisemaker::effects::Value>>& values) {
  std::string result = "[";
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index) result += ',';
    result += "[" + oracle_escape(values[index].first) + "," + oracle_effect_value(values[index].second) + "]";
  }
  return result + "]";
}

std::string oracle_dimension_kind(noisemaker::effects::DimensionKind kind) {
  using K = noisemaker::effects::DimensionKind;
  if (kind == K::input) return "input";
  if (kind == K::screen) return "screen";
  if (kind == K::literal) return "literal";
  if (kind == K::parameter) return "parameter";
  if (kind == K::parameter_default) return "parameter_default";
  if (kind == K::power) return "power";
  if (kind == K::screen_division) return "screen_division";
  if (kind == K::resolution) return "resolution";
  return "unknown";
}

std::string oracle_dimension(const noisemaker::effects::DimensionExpression& value) {
  return "{\"kind\":" + oracle_escape(oracle_dimension_kind(value.kind)) +
         ",\"parameter\":" + oracle_escape(value.parameter) +
         ",\"inputOverride\":" + oracle_escape(value.input_override) +
         ",\"literal\":" + oracle_escape(oracle_number(value.literal)) +
         ",\"defaultValue\":" + oracle_escape(oracle_number(value.default_value)) +
         ",\"power\":" + std::to_string(value.power) +
         ",\"raw\":" + oracle_effect_value(value.raw) + "}";
}

std::string oracle_blend(const std::optional<noisemaker::effects::BlendDefinition>& value) {
  if (!value.has_value()) return "{\"present\":false}";
  const auto kind = value->kind == noisemaker::effects::BlendKind::factors ? "factors" : "boolean";
  return "{\"present\":true,\"value\":{\"kind\":" + oracle_escape(kind) +
         ",\"enabled\":" + std::string(value->enabled ? "true" : "false") +
         ",\"factors\":[" + oracle_escape(value->factors[0]) + "," + oracle_escape(value->factors[1]) + "]}}";
}

std::string oracle_parameter(const noisemaker::effects::ParameterDefinition& value) {
  return "{\"name\":" + oracle_escape(value.name) + ",\"type\":" + oracle_escape(value.type) +
         ",\"default\":" + oracle_optional_effect_value(value.default_value) +
         ",\"define\":" + oracle_optional_string(value.define) +
         ",\"uniform\":" + oracle_optional_string(value.uniform) +
         ",\"zero\":" + oracle_optional_effect_value(value.zero) +
         ",\"enumValues\":" + oracle_effect_value_pairs(value.enum_values) +
         ",\"enumName\":" + oracle_optional_string(value.enum_name) +
         ",\"choices\":" + oracle_effect_value_pairs(value.choices) +
         ",\"min\":" + oracle_optional_effect_value(value.min) +
         ",\"max\":" + oracle_optional_effect_value(value.max) +
         ",\"texture\":" + oracle_optional_string(value.texture) +
         ",\"colorModeUniform\":" + oracle_optional_string(value.color_mode_uniform) +
         ",\"cpuOnly\":" + std::string(value.cpu_only ? "true" : "false") +
         ",\"raw\":" + oracle_effect_value_pairs(value.raw) + "}";
}

std::string oracle_pass(const noisemaker::effects::PassDefinition& value) {
  return "{\"name\":" + oracle_escape(value.name) + ",\"program\":" + oracle_escape(value.program) +
         ",\"inputs\":" + oracle_effect_string_pairs(value.inputs) +
         ",\"outputs\":" + oracle_effect_string_pairs(value.outputs) +
         ",\"uniforms\":" + oracle_effect_value_pairs(value.uniforms) +
         ",\"count\":" + oracle_optional_effect_value(value.count) +
         ",\"repeat\":" + oracle_optional_effect_value(value.repeat) +
         ",\"conditions\":" + oracle_optional_effect_value(value.conditions) +
         ",\"viewport\":" + oracle_optional_effect_value(value.viewport) +
         ",\"blend\":" + oracle_blend(value.blend) +
         ",\"drawMode\":" + oracle_optional_string(value.draw_mode) +
         ",\"drawBuffers\":" + oracle_optional_effect_value(value.draw_buffers) +
         (value.storage_textures.empty() ? std::string{} : ",\"storageTextures\":" + oracle_effect_string_pairs(value.storage_textures)) +
         ",\"raw\":" + oracle_effect_value_pairs(value.raw) + "}";
}

std::string oracle_texture(const noisemaker::effects::TextureDefinition& value) {
  return "{\"name\":" + oracle_escape(value.name) + ",\"width\":" + oracle_dimension(value.width) +
         ",\"height\":" + oracle_dimension(value.height) + ",\"format\":" + oracle_optional_string(value.format) +
         ",\"raw\":" + oracle_effect_value_pairs(value.raw) + "}";
}

std::string oracle_definition(const noisemaker::effects::EffectDefinition& value) {
  std::string result = "{\"id\":" + oracle_escape(value.id) + ",\"directoryName\":" + oracle_escape(value.directory_name) +
    ",\"name\":" + oracle_escape(value.name) + ",\"namespace\":" + oracle_escape(value.name_space) +
    ",\"func\":" + oracle_escape(value.function) + ",\"kind\":" + oracle_escape(value.kind) +
    ",\"domain\":" + oracle_escape(value.domain) + ",\"tags\":[";
  for (std::size_t index = 0; index < value.tags.size(); ++index) { if (index) result += ','; result += oracle_escape(value.tags[index]); }
  result += "],\"description\":" + oracle_escape(value.description) +
    ",\"parameterAliases\":" + oracle_effect_string_pairs(value.parameter_aliases) + ",\"parameters\":[";
  for (std::size_t index = 0; index < value.parameters.size(); ++index) { if (index) result += ','; result += oracle_parameter(value.parameters[index]); }
  result += "],\"passes\":[";
  for (std::size_t index = 0; index < value.passes.size(); ++index) { if (index) result += ','; result += oracle_pass(value.passes[index]); }
  result += "],\"textures\":[";
  for (std::size_t index = 0; index < value.textures.size(); ++index) { if (index) result += ','; result += oracle_texture(value.textures[index]); }
  result += "],\"externalTexture\":" + oracle_optional_string(value.external_texture) +
    ",\"outputTex3d\":" + oracle_optional_string(value.output_tex3d) +
    ",\"outputGeo\":" + oracle_optional_string(value.output_geo) +
    ",\"outputXyz\":" + oracle_optional_string(value.output_xyz) +
    ",\"outputVelocity\":" + oracle_optional_string(value.output_velocity) +
    ",\"outputRgba\":" + oracle_optional_string(value.output_rgba) +
    (value.output_tex ? ",\"outputTex\":" + oracle_escape(*value.output_tex) : std::string{}) +
    ",\"iterated\":" + std::string(value.iterated ? "true" : "false") +
    ",\"loopRole\":" + oracle_optional_string(value.loop_role) +
    ",\"raw\":" + oracle_effect_value_pairs(value.raw) + "}";
  return result;
}

std::string oracle_status(noisemaker::graph::AvailabilityStatus status) {
  using S = noisemaker::graph::AvailabilityStatus;
  if (status == S::compatible) return "compatible";
  if (status == S::scatter) return "scatter";
  if (status == S::incompatible) return "incompatible";
  return "missing";
}

std::string oracle_admission(const noisemaker::graph::PassAdmission& admission) {
  std::string result = "{\"index\":" + std::to_string(admission.identity.index) + ",\"name\":" + oracle_escape(admission.identity.name) +
                       ",\"programKey\":" + oracle_escape(admission.identity.program_key) + ",\"status\":" + oracle_escape(oracle_status(admission.status)) + ",\"reasons\":[";
  for (std::size_t index = 0; index < admission.reasons.size(); ++index) {
    if (index) result += ',';
    result += "{\"code\":" + oracle_escape(admission.reasons[index].code) + ",\"detail\":" + oracle_escape(admission.reasons[index].detail) + "}";
  }
  result += "],\"canonicalFactory\":" + oracle_escape(admission.canonical_factory) +
    ",\"sourceSha256\":" + oracle_escape(admission.source_sha256) +
    ",\"semanticSha256\":" + oracle_escape(admission.semantic_sha256) +
    ",\"emittedFactory\":" + oracle_escape(admission.emitted_factory) +
    ",\"routeKind\":" + oracle_escape(admission.route_kind) +
    ",\"typedAbiSha256\":" + oracle_escape(admission.typed_abi_sha256) +
    ",\"bindingAbiSha256\":" + oracle_escape(admission.binding_abi_sha256) +
    ",\"outputExtent\":{\"width\":" + oracle_escape(admission.output_extent.width) +
    ",\"height\":" + oracle_escape(admission.output_extent.height) +
    ",\"format\":" + oracle_escape(admission.output_extent.format) + "},\"compileDefines\":[";
  for (std::size_t index = 0; index < admission.compile_defines.size(); ++index) {
    if (index) result += ',';
    const auto& define = admission.compile_defines[index];
    result += "{\"name\":" + oracle_escape(define.name) + ",\"type\":" + oracle_escape(define.type) +
      ",\"source\":" + oracle_escape(define.source) + ",\"sourceName\":" + oracle_escape(define.source_name) +
      ",\"resource\":" + oracle_escape(define.resource) + ",\"cppType\":" + oracle_escape(define.cpp_type) + "}";
  }
  result += "],\"capabilities\":[";
  for (std::size_t index = 0; index < admission.capabilities.size(); ++index) { if (index) result += ','; result += oracle_escape(admission.capabilities[index]); }
  result += "],\"dimensionality\":" + oracle_escape(admission.dimensionality) + ",\"drawMode\":" + oracle_escape(admission.draw_mode) + ",\"samplers\":[";
  const auto oracle_binding = [](const noisemaker::graph::CompatibilityBinding& binding) {
    return "{\"name\":" + oracle_escape(binding.name) + ",\"type\":" + oracle_escape(binding.type) +
      ",\"source\":" + oracle_escape(binding.source) + ",\"sourceName\":" + oracle_escape(binding.source_name) +
      ",\"resource\":" + oracle_escape(binding.resource) + ",\"cppType\":" + oracle_escape(binding.cpp_type) + "}";
  };
  const auto oracle_bindings = [&](const auto& bindings) {
    std::string output;
    for (std::size_t index = 0; index < bindings.size(); ++index) { if (index) output += ','; output += oracle_binding(bindings[index]); }
    return output;
  };
  result += oracle_bindings(admission.samplers) + "],\"uniforms\":[" + oracle_bindings(admission.uniforms) + "],\"outputs\":[";
  for (std::size_t index = 0; index < admission.outputs.size(); ++index) {
    if (index) result += ',';
    const auto& output = admission.outputs[index];
    result += "{\"slot\":" + std::to_string(output.slot) +
      ",\"physicalName\":" + oracle_escape(output.physical_name) +
      ",\"logicalRoute\":" + oracle_escape(output.logical_route) +
      ",\"cppType\":" + oracle_escape(output.cpp_type) + "}";
  }
  result += "],\"authorityPass\":{\"name\":" + oracle_escape(admission.authority_pass.name) + ",\"inputs\":" + oracle_effect_string_pairs(admission.authority_pass.inputs) + ",\"outputs\":" + oracle_effect_string_pairs(admission.authority_pass.outputs) + ",\"uniforms\":[";
  for (std::size_t index = 0; index < admission.authority_pass.uniforms.size(); ++index) {
    if (index) result += ',';
    result += "[" + oracle_escape(admission.authority_pass.uniforms[index].first) + "," + oracle_value(admission.authority_pass.uniforms[index].second) + "]";
  }
  result += "],\"blendKind\":" + oracle_escape(admission.authority_pass.blend_kind) + ",\"blend\":" + (admission.authority_pass.blend ? "true" : "false") + ",\"blendFactors\":[" + oracle_escape(admission.authority_pass.blend_factors[0]) + "," + oracle_escape(admission.authority_pass.blend_factors[1]) + "],\"repeat\":" + oracle_optional_plan_value(admission.authority_pass.repeat) + ",\"defines\":" + oracle_optional_effect_value(admission.authority_pass.defines) + ",\"viewport\":" + oracle_optional_effect_value(admission.authority_pass.viewport) + "}";
  if (admission.scatter.has_value()) {
    const auto& scatter = *admission.scatter;
    result += ",\"scatter\":{\"adapter\":" + oracle_escape(scatter.adapter) + ",\"registry\":" + oracle_escape(scatter.registry) + ",\"drawMode\":" + oracle_escape(scatter.draw_mode) + ",\"dimensionality\":" + oracle_escape(scatter.dimensionality) + ",\"count\":" + oracle_escape(scatter.count) + ",\"inputTexture\":" + oracle_escape(scatter.input_texture) + ",\"destinationMutation\":" + oracle_escape(scatter.destination_mutation) + ",\"blend\":" + (scatter.blend ? "true" : "false") + ",\"uniforms\":[";
    for (std::size_t index = 0; index < scatter.uniforms.size(); ++index) {
      if (index) result += ',';
      const auto& uniform = scatter.uniforms[index];
      result += "{\"name\":" + oracle_escape(uniform.name) + ",\"type\":" + oracle_escape(uniform.type) + ",\"cppType\":" + oracle_escape(uniform.cpp_type) + ",\"source\":" + oracle_escape(uniform.source) + ",\"sourceName\":" + oracle_escape(uniform.source_name) + ",\"resource\":" + oracle_escape(uniform.resource) + "}";
    }
    result += "],\"outputs\":[";
    for (std::size_t index = 0; index < scatter.outputs.size(); ++index) {
      if (index) result += ',';
      const auto& output = scatter.outputs[index];
      result += "{\"slot\":" + std::to_string(output.slot) + ",\"physicalName\":" + oracle_escape(output.physical_name) + ",\"logicalRoute\":" + oracle_escape(output.logical_route) + ",\"cppType\":" + oracle_escape(output.cpp_type) + "}";
    }
    result += "]}";
  }
  else result += ",\"scatter\":null";
  return result + "}";
}

std::string oracle_surface(const noisemaker::graph::SurfaceReference& surface) {
  return surface.kind == noisemaker::graph::SurfaceReference::Kind::named ? oracle_escape(surface.name) : "null";
}

std::string oracle_step(const noisemaker::graph::CompiledStep& step);

std::string oracle_chain(const noisemaker::graph::ExecutionChain& chain) {
  std::string result = "{\"loc\":" + oracle_loc(chain.loc) + ",\"steps\":[";
  for (std::size_t index = 0; index < chain.steps.size(); ++index) { if (index) result += ','; result += oracle_step(chain.steps[index]); }
  return result + "]}";
}

std::string oracle_step(const noisemaker::graph::CompiledStep& step) {
  return std::visit([](const auto& current) -> std::string {
    using T = std::decay_t<decltype(current)>;
    std::string metadata;
    if (current.id) metadata = ",\"_id\":" + oracle_escape(*current.id);
    if constexpr (std::is_same_v<T, noisemaker::graph::ReadStep> || std::is_same_v<T, noisemaker::graph::Read3DStep>) {
      if (current.skip) metadata += ",\"_skip\":true";
    }
    if constexpr (std::is_same_v<T, noisemaker::graph::ReadStep>) {
      return "{\"kind\":\"read\"" + metadata + ",\"surface\":" + oracle_surface(current.surface) + ",\"loc\":" + oracle_loc(current.loc) + "}";
    } else if constexpr (std::is_same_v<T, noisemaker::graph::WriteStep>) {
      return "{\"kind\":\"write\"" + metadata + ",\"surface\":" + oracle_surface(current.surface) + ",\"loc\":" + oracle_loc(current.loc) + "}";
    } else if constexpr (std::is_same_v<T, noisemaker::graph::Write3DStep> || std::is_same_v<T, noisemaker::graph::Read3DStep>) {
      return std::string("{\"kind\":\"") + (std::is_same_v<T, noisemaker::graph::Write3DStep> ? "write3d" : "read3d") +
             "\"" + metadata + ",\"volume\":" + oracle_escape(current.volume) + ",\"geometry\":" + oracle_escape(current.geometry) +
             ",\"loc\":" + oracle_loc(current.loc) + "}";
    } else {
      std::string result = "{\"kind\":\"effect\"" + metadata + ",\"effectId\":" + oracle_escape(current.effect.id) + ",\"domain\":" + oracle_escape(current.effect.domain) +",\"effectKind\":" + oracle_escape(current.effect.kind) + ",\"snapshotIndex\":" + std::to_string(current.snapshot_index) + ",\"params\":[";
      for (std::size_t index = 0; index < current.params.size(); ++index) { if (index) result += ','; result += "{\"name\":" + oracle_escape(current.params[index].name) + ",\"value\":" + oracle_value(current.params[index].value) + "}"; }
      result += "],\"explicitParams\":[";
      for (std::size_t index = 0; index < current.explicit_params.size(); ++index) { if (index) result += ','; result += oracle_escape(current.explicit_params[index]); }
      result += "],\"passes\":[";
      for (std::size_t index = 0; index < current.passes.size(); ++index) { if (index) result += ','; result += oracle_admission(current.passes[index]); }
      result += "]";
      if (!current.inline_chains.empty()) {
        result += ",\"inlineChains\":[";
        for (std::size_t index = 0; index < current.inline_chains.size(); ++index) {
          if (index) result += ',';
          result += "{\"surface\":" + oracle_escape(current.inline_chains[index].surface) + ",\"chain\":" + oracle_chain(current.inline_chains[index].chain) + "}";
        }
        result += "]";
      }
      return result + ",\"loc\":" + oracle_loc(current.loc) + "}";
    }
  }, step);
}

std::string oracle_snapshot(const noisemaker::graph::PlanEffectSnapshot& snapshot) {
  std::string result = "{\"effectId\":" + oracle_escape(snapshot.definition.id) +
                       ",\"definition\":" + oracle_definition(snapshot.definition) + ",\"admissions\":[";
  for (std::size_t index = 0; index < snapshot.admissions.size(); ++index) {
    if (index) result += ',';
    result += oracle_admission(snapshot.admissions[index]);
  }
  return result + "],\"snapshotSha256\":" + oracle_escape(snapshot.snapshot_sha256) + "}";
}

noisemaker::effects::EffectDefinition oracle_effect(std::string name, std::string kind = "generator", std::string domain = "image") {
  noisemaker::effects::EffectDefinition result;
  result.name_space = "fixture"; result.function = std::move(name); result.id = result.name_space + "/" + result.function;
  result.name = result.function;
  result.kind = std::move(kind); result.domain = std::move(domain);
  noisemaker::effects::PassDefinition pass; pass.name = "main"; pass.program = result.function; pass.outputs = {{"color", "outputTex"}}; result.passes.push_back(std::move(pass));
  return result;
}

noisemaker::effects::EffectRegistry oracle_custom_registry() {
  auto all = oracle_effect("all");
  const auto add = [&](std::string name, std::string type, noisemaker::effects::Value value) { noisemaker::effects::ParameterDefinition parameter; parameter.name = std::move(name); parameter.type = std::move(type); parameter.default_value = std::move(value); all.parameters.push_back(std::move(parameter)); };
  add("f", "float", noisemaker::effects::Value::number_value(1)); add("i", "int", noisemaker::effects::Value::number_value(2)); add("flag", "boolean", noisemaker::effects::Value::boolean_value(true));
  add("c", "color", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v2", "vec2", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v3", "vec3", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("v4", "vec4", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0)}));
  add("m", "mat3", noisemaker::effects::Value::array_value({noisemaker::effects::Value::number_value(1), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(1), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(0), noisemaker::effects::Value::number_value(1)}));
  auto choice = [](std::string name, std::string type, double value, std::vector<std::pair<std::string, noisemaker::effects::Value>> choices) { noisemaker::effects::ParameterDefinition parameter; parameter.name = std::move(name); parameter.type = std::move(type); parameter.default_value = noisemaker::effects::Value::number_value(value); parameter.choices = std::move(choices); return parameter; };
  all.parameters.push_back(choice("e", "enum", 1, {{"one", noisemaker::effects::Value::number_value(1)}, {"zero", noisemaker::effects::Value::number_value(0)}, {"marker", noisemaker::effects::Value::null()}}));
  all.parameters.push_back(choice("member", "member", 1, {{"brushed", noisemaker::effects::Value::number_value(1)}, {"other", noisemaker::effects::Value::number_value(2)}}));
  all.parameters.push_back(choice("palette", "palette", 1, {{"brushed", noisemaker::effects::Value::number_value(1)}, {"other", noisemaker::effects::Value::number_value(2)}}));
  noisemaker::effects::ParameterDefinition string; string.name = "str"; string.type = "string"; string.default_value = noisemaker::effects::Value::string_value("plain"); string.choices = {{"plain", noisemaker::effects::Value::string_value("plain")}, {"bold", noisemaker::effects::Value::string_value("bold")}}; all.parameters.push_back(string);
  noisemaker::effects::ParameterDefinition surface; surface.name = "surf"; surface.type = "surface"; surface.default_value = noisemaker::effects::Value::null(); all.parameters.push_back(surface);
  noisemaker::effects::ParameterDefinition volume; volume.name = "vol"; volume.type = "volume"; volume.default_value = noisemaker::effects::Value::string_value("volume"); all.parameters.push_back(volume);
  noisemaker::effects::ParameterDefinition geometry; geometry.name = "geo"; geometry.type = "geometry"; geometry.default_value = noisemaker::effects::Value::string_value("geo"); all.parameters.push_back(geometry);
  auto source = oracle_effect("source"); noisemaker::effects::ParameterDefinition first; first.name = "first"; first.type = "int"; first.default_value = noisemaker::effects::Value::number_value(1); source.parameters.push_back(first); noisemaker::effects::ParameterDefinition second; second.name = "second"; second.type = "int"; second.default_value = noisemaker::effects::Value::number_value(2); source.parameters.push_back(second);
  auto alias = oracle_effect("alias"); alias.parameter_aliases = {{"strength", "amount"}}; noisemaker::effects::ParameterDefinition amount; amount.name = "amount"; amount.type = "float"; amount.default_value = noisemaker::effects::Value::number_value(1); alias.parameters.push_back(amount);
  auto bounded = oracle_effect("bounded"); noisemaker::effects::ParameterDefinition bound; bound.name = "amount"; bound.type = "float"; bound.default_value = noisemaker::effects::Value::number_value(1); bound.min = noisemaker::effects::Value::number_value(0); bound.max = noisemaker::effects::Value::number_value(2); bounded.parameters.push_back(bound);
  auto required = oracle_effect("required"); noisemaker::effects::ParameterDefinition needed; needed.name = "amount"; needed.type = "float"; required.parameters.push_back(needed);
  return noisemaker::effects::EffectRegistry({all, source, alias, bounded, required, oracle_effect("mixer", "mixer", "image"), oracle_effect("volumeGen", "generator", "volume-generator"), oracle_effect("volumeFilter", "filter", "volume-filter"), oracle_effect("volumeRender", "filter", "volume-renderer"), oracle_effect("loopBegin", "filter", "loop-begin"), oracle_effect("loopEnd", "filter", "loop-end")});
}
}

int main(int argc, char** argv) {
  std::string name, source, source_name = "<dsl>", mode = "custom";
  bool require_executable = false, list_mode = false;
  for (int index = 1; index < argc; ++index) {
    const std::string argument = argv[index];
    if (argument == "--name" && index + 1 < argc) name = argv[++index];
    else if (argument == "--source" && index + 1 < argc) source = argv[++index];
    else if (argument == "--source-name" && index + 1 < argc) source_name = argv[++index];
    else if (argument == "--mode" && index + 1 < argc) mode = argv[++index];
    else if (argument == "--require-executable") require_executable = true;
    else if (argument == "--list") list_mode = true;
    else { std::cerr << "usage: --name NAME --source TEXT --source-name NAME [--mode custom|catalog_records]\n"; return 2; }
  }
  if (list_mode) {
    const auto registry = noisemaker::effects::EffectRegistry(noisemaker::effects::effect_catalog());
    const auto definitions = registry.list();
    std::cout << "[";
    for (std::size_t index = 0; index < definitions.size(); ++index) {
      if (index) std::cout << ',';
      std::cout << oracle_escape(definitions[index]->id);
    }
    std::cout << "]\n";
    return 0;
  }
  std::cout << "{\"name\":" << oracle_escape(name);
  try {
    const auto registry = mode == "catalog_records" ? noisemaker::effects::EffectRegistry(noisemaker::effects::effect_catalog()) : oracle_custom_registry();
    const auto plan = noisemaker::dsl::compile(source, registry, {.require_executable = require_executable}, source_name);
    std::string output = ",\"plan\":{\"schema\":\"noisemaker-cpp.execution-plan.v1\",\"search\":[";
    for (std::size_t index = 0; index < plan.search.size(); ++index) { if (index) output += ','; output += oracle_escape(plan.search[index]); }
    output += "],\"effects\":[";
    for (std::size_t index = 0; index < plan.effects.size(); ++index) { if (index) output += ','; output += oracle_snapshot(plan.effects[index]); }
    output += "],\"chains\":[";
    for (std::size_t chain_index = 0; chain_index < plan.chains.size(); ++chain_index) { if (chain_index) output += ','; output += oracle_chain(plan.chains[chain_index]); }
    output += "],\"renderSurface\":" + oracle_surface(plan.render_surface) + ",\"requireExecutable\":" + (require_executable ? "true" : "false") + ",\"executable\":" + (plan.executable ? "true" : "false") + ",\"availability\":[";
    for (std::size_t index = 0; index < plan.availability.size(); ++index) { if (index) output += ','; output += oracle_admission(plan.availability[index]); }
    const auto& p = plan.provenance;
    output += "],\"provenance\":{\"sourceSha256\":" + oracle_escape(p.source_sha256) + ",\"sourceName\":" + oracle_escape(p.source_name) + ",\"planPayloadSha256\":" + oracle_escape(p.plan_payload_sha256) + ",\"kind\":" + oracle_escape(p.kind) + ",\"schema\":" + oracle_escape(p.schema) + ",\"backendSchema\":" + oracle_escape(p.backend_schema) + ",\"corpusRevision\":" + oracle_escape(p.corpus_revision) + ",\"generatedPayloadSha256\":" + oracle_escape(p.generated_payload_sha256) + ",\"normalizedRecordStreamSha256\":" + oracle_escape(p.normalized_record_stream_sha256) + ",\"authorityLock\":" + oracle_escape(p.authority_lock) + ",\"cpuRevision\":" + oracle_escape(p.cpu_revision) + ",\"sourceLockSha256\":" + oracle_escape(p.source_lock_sha256) + ",\"cpuPackageSha256\":" + oracle_escape(p.cpu_package_sha256) + ",\"cpuPackageLockSha256\":" + oracle_escape(p.cpu_package_lock_sha256) + ",\"cpuSourceLockSha256\":" + oracle_escape(p.cpu_source_lock_sha256) + ",\"upstreamRevision\":" + oracle_escape(p.upstream_revision) + ",\"upstreamTree\":" + oracle_escape(p.upstream_tree) + ",\"upstreamPackageSha256\":" + oracle_escape(p.upstream_package_sha256) + ",\"upstreamPackageLockSha256\":" + oracle_escape(p.upstream_package_lock_sha256) + ",\"compatibilitySha256\":" + oracle_escape(p.compatibility_sha256) + ",\"counts\":{\"definitions\":" + std::to_string(p.counts.definitions) + ",\"passes\":" + std::to_string(p.counts.passes) + ",\"referenceProgramKeys\":" + std::to_string(p.counts.reference_program_keys) + ",\"backendPrograms\":" + std::to_string(p.counts.backend_programs) + ",\"compatiblePrograms\":" + std::to_string(p.counts.compatible_programs) + ",\"incompatiblePrograms\":" + std::to_string(p.counts.incompatible_programs) + ",\"missingPasses\":" + std::to_string(p.counts.missing_passes) + ",\"scatterPasses\":" + std::to_string(p.counts.scatter_passes) + ",\"executableDefinitions\":" + std::to_string(p.counts.executable_definitions) + ",\"incompleteDefinitions\":" + std::to_string(p.counts.incomplete_definitions) + "}}}";
    std::cout << output;
  } catch (const noisemaker::dsl::DslError& error) {
    std::cout << ",\"error\":{\"name\":\"DslError\",\"message\":" << oracle_escape(error.what()) << ",\"sourceName\":" << oracle_escape(error.sourceName) << ",\"line\":" << error.line << ",\"column\":" << error.column << ",\"index\":" << error.index;
    if (error.code) std::cout << ",\"code\":" << oracle_escape(*error.code);
    std::cout << '}';
  }
  std::cout << "}\n";
  return 0;
}
#endif
