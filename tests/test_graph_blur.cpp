#include "test_harness.hpp"

#include "noisemaker/effects/registry.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/render_result.hpp"
#include "noisemaker/renderer.hpp"

#include "oracles/dsl_blur_rgba8.inc"

#include <array>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace {

constexpr std::string_view kConstantSource =
    "search synth, filter\n"
    "solid(color: #3a7).blur(radiusX: 3, radiusY: 2).write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kNonconstantSource =
    "search filter\n"
    "read(o0).blur(radiusX: 2, radiusY: 5).write(o1)\n"
    "render(o1)\n";

constexpr std::string_view kCrossChainSource =
    "search synth, filter\n"
    "solid(color: #3a7).write(o0)\n"
    "read(o0).blur(radiusX: 3, radiusY: 2).write(o1)\n"
    "render(o1)\n";

noisemaker::RenderOptions options(std::size_t width, std::size_t height) {
  noisemaker::RenderOptions result;
  result.width = width;
  result.height = height;
  result.time = 0.25;
  result.frame = 0;
  result.seed = 17.0;
  return result;
}

noisemaker::Surface patterned_seed(std::size_t width, std::size_t height) {
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t y = 0; y < height; ++y) {
    for (std::size_t x = 0; x < width; ++x) {
      const std::size_t i = (y * width + x) * 4U;
      bytes[i] = static_cast<std::uint8_t>((17U + 37U * x + 53U * y) % 256U);
      bytes[i + 1U] = static_cast<std::uint8_t>((43U + 11U * x + 79U * y) % 256U);
      bytes[i + 2U] = static_cast<std::uint8_t>((71U + 17U * x + 29U * y + 13U * x * y) % 256U);
      bytes[i + 3U] = static_cast<std::uint8_t>(255U - ((19U * x + 7U * y) % 128U));
    }
  }
  return noisemaker::Surface::from_rgba8(width, height, bytes);
}

void reauthenticate(noisemaker::graph::ExecutionPlan& plan) {
  for (auto& snapshot : plan.effects) {
    snapshot.snapshot_sha256 =
        noisemaker::graph::detail::snapshot_sha256(snapshot);
  }
  plan.provenance.plan_payload_sha256 =
      noisemaker::graph::detail::plan_payload_sha256(plan);
}

noisemaker::graph::EffectStep& effect_step(
    noisemaker::graph::ExecutionPlan& plan, std::string_view effect_id);

template <typename Mutate>
void expect_plan_error(Mutate&& mutate,
                       noisemaker::graph::GraphErrorCode expected_code) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "executor-mutation.dsl");
  mutate(plan);
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == expected_code);
    REQUIRE(error.effect_id() == "filter/blur");
    REQUIRE(error.pass_index() == 0U);
    REQUIRE(error.pass_name() == "blurH");
    REQUIRE(error.program_key() == "filter/blur:blurH");
  }
}

noisemaker::graph::EffectStep& effect_step(
    noisemaker::graph::ExecutionPlan& plan, std::string_view effect_id) {
  for (auto& chain : plan.chains) {
    for (auto& variant : chain.steps) {
      auto* step = std::get_if<noisemaker::graph::EffectStep>(&variant);
      if (step != nullptr && step->effect.id == effect_id) return *step;
    }
  }
  throw std::logic_error("test effect step not found");
}

}  // namespace

static_assert(std::is_aggregate_v<noisemaker::RenderOptions>);

TEST(graph_executor_executes_value_owned_plan_after_renderer_destruction) {
  noisemaker::graph::ExecutionPlan plan;
  {
    noisemaker::Renderer renderer;
    plan = renderer.compile(kConstantSource, "constant.dsl");
    REQUIRE(plan.effects.size() == 2U);
    REQUIRE(plan.effects[1].definition.id == "filter/blur");
    REQUIRE(plan.effects[1].definition.textures.size() == 1U);
    REQUIRE(plan.effects[1].definition.textures[0].name == "_blurTemp");
    REQUIRE(plan.effects[1].definition.textures[0].format.has_value());
    REQUIRE(*plan.effects[1].definition.textures[0].format == "rgba8unorm");
  }

  noisemaker::graph::GraphExecutor executor;
  const auto result = executor.execute(plan, options(7U, 5U));
  REQUIRE(result.surface.width() == 7U);
  REQUIRE(result.surface.height() == 5U);
  REQUIRE(result.final_route == "o0");
  REQUIRE(result.pass_count == 3U);
}

TEST(graph_executor_rejects_stale_deep_snapshot_before_allocation) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "constant.dsl");
  plan.effects[1].definition.textures[0].format = std::string("rgba32f");
  noisemaker::graph::GraphExecutor executor;
  try {
    static_cast<void>(executor.execute(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::invalid_snapshot);
    REQUIRE(error.detail() == "plan snapshot or payload hash is invalid");
  }
}

TEST(graph_executor_rejects_admission_cardinality_before_indexing) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "cardinality.dsl");
  plan.effects[1].admissions.pop_back();
  noisemaker::graph::GraphExecutor executor;
  try {
    static_cast<void>(executor.execute(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::invalid_snapshot);
    REQUIRE(error.detail() == "plan snapshot or payload hash is invalid");
  }
}

TEST(graph_executor_rejects_adversarial_pass_metadata_with_stable_context) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "metadata.dsl");

  plan.effects[1].definition.passes[0].draw_buffers =
      noisemaker::effects::Value::number_value(2.0);
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::unsupported_mrt);
    REQUIRE(error.effect_id() == "filter/blur");
    REQUIRE(error.pass_name() == "blurH");
    REQUIRE(error.program_key() == "filter/blur:blurH");
    REQUIRE(std::string(error.what()).find("std::") == std::string::npos);
  }

  plan = renderer.compile(kConstantSource, "metadata-blend.dsl");
  plan.effects[1].definition.passes[0].blend =
      noisemaker::effects::BlendDefinition{};
  plan.effects[1].definition.passes[0].blend->enabled = true;
  plan.effects[1].admissions[0].authority_pass.blend_kind = "boolean";
  plan.effects[1].admissions[0].authority_pass.blend = true;
  effect_step(plan, "filter/blur").passes[0].authority_pass.blend_kind =
      "boolean";
  effect_step(plan, "filter/blur").passes[0].authority_pass.blend = true;
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::unsupported_blend);
    REQUIRE(error.pass_index() == 0U);
  }

  plan = renderer.compile(kConstantSource, "metadata-draw.dsl");
  plan.effects[1].definition.passes[0].draw_mode = "points";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::unsupported_draw_mode);
    REQUIRE(error.pass_index() == 0U);
  }
}

TEST(graph_executor_rejects_wrong_sampler_route_before_binding) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "sampler-route.dsl");
  plan.effects[1].definition.passes[1].inputs[0].second = "not_blur_temp";
  plan.effects[1].admissions[1].authority_pass.inputs[0].second =
      "not_blur_temp";
  effect_step(plan, "filter/blur").passes[1]
      .authority_pass.inputs[0].second = "not_blur_temp";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::missing_binding);
    REQUIRE(error.pass_index() == 1U);
    REQUIRE(error.detail() == "sampler ABI route is invalid");
  }
}

TEST(graph_executor_honors_authenticated_repeat_without_registry_lookup) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "repeat.dsl");
  plan.effects[0].definition.passes[0].repeat =
      noisemaker::effects::Value::number_value(2.5);
  plan.effects[0].admissions[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::number_value(2.5);
  effect_step(plan, "synth/solid").passes[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::number_value(2.5);
  reauthenticate(plan);
  const auto result = renderer.render(plan, options(7U, 5U));
  REQUIRE(result.pass_count() == 5U);
}

TEST(graph_executor_truncates_only_string_uniform_repeat) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "string-repeat.dsl");
  plan.effects[1].definition.passes[0].repeat =
      noisemaker::effects::Value::string_value("radiusX");
  auto& blur = effect_step(plan, "filter/blur");
  plan.effects[1].admissions[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::string_value("radiusX");
  blur.passes[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::string_value("radiusX");
  const auto radius = std::find_if(
      blur.params.begin(), blur.params.end(),
      [](const auto& binding) { return binding.name == "radiusX"; });
  REQUIRE(radius != blur.params.end());
  radius->value = noisemaker::graph::PlanValue::number_value(2.9);
  reauthenticate(plan);
  const auto result = renderer.render(plan, options(7U, 5U));
  REQUIRE(result.pass_count() == 4U);
}

TEST(graph_executor_evaluates_ordered_uniform_conditions) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "conditions.dsl");
  plan.effects[1].definition.passes[0].conditions =
      noisemaker::effects::Value::object_value({
          {"runIf", noisemaker::effects::Value::array_value({
                        noisemaker::effects::Value::object_value({
                            {"uniform", noisemaker::effects::Value::string_value("radiusX")},
                            {"equals", noisemaker::effects::Value::number_value(3.0)},
                        }),
                    })},
      });
  reauthenticate(plan);
  REQUIRE(renderer.render(plan, options(7U, 5U)).pass_count() == 3U);

  plan.effects[1].definition.passes[0].conditions->object[0]
      .second.array[0].object[1].second =
      noisemaker::effects::Value::number_value(99.0);
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::read_before_write);
    REQUIRE(error.pass_name() == "blurV");
    REQUIRE(error.program_key() == "filter/blur:blurV");
  }
}

TEST(graph_executor_rejects_reauthenticated_noncanonical_factory_pairs) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "legacy-solid.dsl");
  plan.effects[0].admissions[0].canonical_factory = "bind_synth_solid";
  effect_step(plan, "synth/solid").passes[0].canonical_factory =
      "bind_synth_solid";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::unavailable_pass);
    REQUIRE(error.effect_id() == "synth/solid");
    REQUIRE(error.program_key() == "synth/solid:solid");
  }

  plan = renderer.compile(kConstantSource, "swapped-blur.dsl");
  plan.effects[1].admissions[0].canonical_factory =
      "bind_filter_blur_blurV";
  effect_step(plan, "filter/blur").passes[0].canonical_factory =
      "bind_filter_blur_blurV";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::unavailable_pass);
    REQUIRE(error.pass_index() == 0U);
    REQUIRE(error.program_key() == "filter/blur:blurH");
  }
}

TEST(graph_executor_reads_a_route_published_by_an_earlier_chain) {
  noisemaker::Renderer renderer;
  const auto result = renderer.render(kCrossChainSource, options(7U, 5U),
                                      "cross-chain.dsl");
  REQUIRE(result.pass_count() == 3U);
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kConstant7x5.size());
  REQUIRE(std::equal(bytes.begin(), bytes.end(),
                     noisemaker_dsl_blur_oracle::kConstant7x5.begin()));
}

TEST(graph_executor_reports_invalid_format_and_dimension_before_allocation) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "format.dsl");
  plan.effects[1].definition.textures[0].format = "rgba999";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::invalid_format);
    REQUIRE(error.effect_id() == "filter/blur");
  }

  plan = renderer.compile(kConstantSource, "dimension.dsl");
  plan.effects[1].definition.textures[0].width.literal =
      std::numeric_limits<double>::infinity();
  plan.effects[1].definition.textures[0].width.kind =
      noisemaker::effects::DimensionKind::literal;
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::invalid_dimension);
    REQUIRE(error.pass_index() == 0U);
  }

  plan = renderer.compile(kConstantSource, "allocation-limit.dsl");
  auto& texture = plan.effects[1].definition.textures[0];
  texture.width.kind = noisemaker::effects::DimensionKind::literal;
  texture.width.literal = 4097.0;
  texture.height.kind = noisemaker::effects::DimensionKind::literal;
  texture.height.literal = 4096.0;
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::allocation_limit);
    REQUIRE(error.pass_index() == 0U);
    REQUIRE(error.detail() == "texture dimensions exceed allocation limit");
  }
}

TEST(renderer_constant_blur_has_exact_dimensions_and_hashable_result) {
  noisemaker::Renderer renderer;
  REQUIRE(noisemaker_dsl_blur_oracle::kConstantSourceSha256 ==
          "c3a9da6bc816effcaf750a386d1024c4d309cc000ef7cf9c9315843a4cb3df2c");
  const auto result = renderer.render(kConstantSource, options(7U, 5U),
                                      "constant.dsl");
  REQUIRE(result.width() == 7U);
  REQUIRE(result.height() == 5U);
  REQUIRE(result.pass_count() == 3U);
  REQUIRE(result.final_route() == "o0");
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kConstant7x5.size());
  REQUIRE(std::equal(bytes.begin(), bytes.end(),
                     noisemaker_dsl_blur_oracle::kConstant7x5.begin()));
}

TEST(renderer_rejects_stateful_mode_before_execution) {
  noisemaker::Renderer renderer;
  auto render_options = options(7U, 5U);
  render_options.one_shot = false;
  REQUIRE_THROWS_AS(renderer.render(kConstantSource, render_options),
                    noisemaker::graph::GraphError);
  try {
    static_cast<void>(renderer.render(kConstantSource, render_options));
  } catch (const noisemaker::graph::GraphError& error) {
    REQUIRE(error.code() == noisemaker::graph::GraphErrorCode::invalid_options);
  }
}

TEST(graph_executor_rejects_reauthenticated_pass_identity_mutations) {
  expect_plan_error(
      [](auto& plan) {
        auto& admission = plan.effects[1].admissions[0];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        admission.identity.index = 9U;
        retained.identity.index = 9U;
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        auto& admission = plan.effects[1].admissions[0];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        admission.identity.name = "forgedBlurH";
        retained.identity.name = "forgedBlurH";
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        auto& admission = plan.effects[1].admissions[0];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        admission.identity.program_key = "filter/blur:forged";
        retained.identity.program_key = "filter/blur:forged";
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
}

TEST(graph_executor_rejects_reauthenticated_output_abi_mutations) {
  // Renaming blurH's producer route consistently through every owned copy is
  // caught by the authenticated ordered-ABI digest at the pass that was
  // forged, before the consuming pass is ever reached.
  expect_plan_error(
      [](auto& plan) {
        auto& snapshot = plan.effects[1];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        snapshot.definition.passes[0].outputs[0].second = "forgedRoute";
        snapshot.admissions[0].authority_pass.outputs[0].second = "forgedRoute";
        snapshot.admissions[0].outputs[0].logical_route = "forgedRoute";
        retained.authority_pass.outputs[0].second = "forgedRoute";
        retained.outputs[0].logical_route = "forgedRoute";
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        auto& snapshot = plan.effects[1];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        snapshot.definition.passes[0].outputs[0].first = "forgedColor";
        snapshot.admissions[0].authority_pass.outputs[0].first = "forgedColor";
        snapshot.admissions[0].outputs[0].physical_name = "forgedColor";
        retained.authority_pass.outputs[0].first = "forgedColor";
        retained.outputs[0].physical_name = "forgedColor";
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        auto& snapshot = plan.effects[1];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        snapshot.admissions[0].outputs[0].cpp_type = "glsl::Vec3";
        retained.outputs[0].cpp_type = "glsl::Vec3";
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        auto& snapshot = plan.effects[1];
        auto& retained = effect_step(plan, "filter/blur").passes[0];
        snapshot.admissions[0].outputs[0].slot = 1U;
        retained.outputs[0].slot = 1U;
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
}

TEST(graph_executor_joins_complete_authority_pass_metadata) {
  const auto mutate_authority = [](auto&& mutate) {
    expect_plan_error(
        [&](auto& plan) {
          auto& snapshot = plan.effects[1].admissions[0].authority_pass;
          auto& retained =
              effect_step(plan, "filter/blur").passes[0].authority_pass;
          mutate(snapshot);
          mutate(retained);
        },
        noisemaker::graph::GraphErrorCode::invalid_snapshot);
  };
  mutate_authority([](auto& authority) { authority.name = "forged"; });
  mutate_authority([](auto& authority) {
    authority.uniforms.push_back(
        {"forged", noisemaker::graph::PlanValue::number_value(1.0)});
  });
  mutate_authority([](auto& authority) {
    authority.blend_kind = "boolean";
    authority.blend = true;
  });
  mutate_authority([](auto& authority) {
    authority.repeat = noisemaker::graph::PlanValue::number_value(2.0);
  });
}

TEST(graph_executor_rejects_reauthenticated_sampler_typed_abi_mutations) {
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].samplers[0].type = "sampler3D";
      },
      noisemaker::graph::GraphErrorCode::binding_type);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].samplers[0].source = "uniform";
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].samplers[0].source_name = "wrongInput";
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].samplers[0].cpp_type = "Surface&";
      },
      noisemaker::graph::GraphErrorCode::binding_type);
}

TEST(graph_executor_uses_one_iteration_for_missing_string_repeat_uniform) {
  noisemaker::Renderer renderer;
  auto plan = renderer.compile(kConstantSource, "missing-repeat.dsl");
  plan.effects[0].definition.passes[0].repeat =
      noisemaker::effects::Value::string_value("missingUniform");
  plan.effects[0].admissions[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::string_value("missingUniform");
  effect_step(plan, "synth/solid").passes[0].authority_pass.repeat =
      noisemaker::graph::PlanValue::string_value("missingUniform");
  reauthenticate(plan);
  const auto result = renderer.render(plan, options(7U, 5U));
  REQUIRE(result.pass_count() == 3U);
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kConstant7x5.size());
  REQUIRE(std::equal(bytes.begin(), bytes.end(),
                     noisemaker_dsl_blur_oracle::kConstant7x5.begin()));
}

TEST(graph_executor_rejects_reauthenticated_uniform_abi_mutations) {
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].uniforms[0].type = "vec4";
      },
      noisemaker::graph::GraphErrorCode::binding_type);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].uniforms[0].source_name = "wrongState";
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].uniforms[0].resource = "wrongRoute";
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].uniforms.push_back(
            {"forged", "float", "effect_parameter", "forged", {}, "float"});
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].admissions[0].uniforms[0].resource = "wrongRoute";
        plan.effects[1].admissions[0].uniforms[1].name =
            plan.effects[1].admissions[0].uniforms[0].name;
      },
      noisemaker::graph::GraphErrorCode::missing_binding);
  // A reordered uniform ABI is not observable by a name-keyed kernel, so the
  // authenticated ordered-ABI digest is what rejects it.
  expect_plan_error(
      [](auto& plan) {
        auto& uniforms = plan.effects[1].admissions[0].uniforms;
        std::swap(uniforms[0], uniforms[1]);
        auto& retained = effect_step(plan, "filter/blur").passes[0].uniforms;
        std::swap(retained[0], retained[1]);
      },
      noisemaker::graph::GraphErrorCode::binding_type);
}

TEST(graph_executor_rejects_reauthenticated_pass_count_and_viewport_mutations) {
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].definition.passes[0].count =
            noisemaker::effects::Value::number_value(2.0);
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
  expect_plan_error(
      [](auto& plan) {
        plan.effects[1].definition.passes[0].viewport =
            noisemaker::effects::Value::string_value("forgedViewport");
      },
      noisemaker::graph::GraphErrorCode::invalid_snapshot);
}

TEST(renderer_nonconstant_blur_owns_seed_surface_copy) {
  noisemaker::Renderer renderer;
  REQUIRE(noisemaker_dsl_blur_oracle::kNonconstantSourceSha256 ==
          "6190f788d4d5f23895ff57f5234ac11fc3790c6b80912d91d08635fb99b42d80");
  noisemaker::RenderOptions render_options;
  render_options.width = 5U;
  render_options.height = 3U;
  render_options.seed = 11.0;
  std::vector<std::uint8_t> seed_bytes(5U * 3U * 4U);
  for (std::size_t y = 0; y < 3U; ++y) {
    for (std::size_t x = 0; x < 5U; ++x) {
      const std::size_t i = (y * 5U + x) * 4U;
      seed_bytes[i] = static_cast<std::uint8_t>((17U + 37U * x + 53U * y) % 256U);
      seed_bytes[i + 1U] = static_cast<std::uint8_t>((43U + 11U * x + 79U * y) % 256U);
      seed_bytes[i + 2U] = static_cast<std::uint8_t>((71U + 17U * x + 29U * y + 13U * x * y) % 256U);
      seed_bytes[i + 3U] = static_cast<std::uint8_t>(255U - ((19U * x + 7U * y) % 128U));
    }
  }
  noisemaker::Surface seed = noisemaker::Surface::from_rgba8(5U, 3U, seed_bytes);
  render_options.seed_surfaces.push_back({"o0", std::move(seed)});
  const auto result = renderer.render(kNonconstantSource, render_options,
                                      "nonconstant.dsl");
  REQUIRE(result.width() == 5U);
  REQUIRE(result.height() == 3U);
  REQUIRE(result.pass_count() == 2U);
  const auto bytes = result.to_rgba8();
  REQUIRE(std::equal(bytes.begin(), bytes.end(),
                     noisemaker_dsl_blur_oracle::kNonconstant5x3.begin()));
}

TEST(renderer_blur_matches_all_source_bound_oracle_extents) {
  noisemaker::Renderer renderer;
  for (const auto& dimensions : std::array<std::pair<std::size_t, std::size_t>, 3>{
           std::pair{11U, 9U}, std::pair{5U, 3U}, std::pair{7U, 4U}}) {
    const bool constant = dimensions.first == 11U;
    noisemaker::RenderOptions render_options;
    render_options.width = dimensions.first;
    render_options.height = dimensions.second;
    render_options.time = constant ? 0.25 : 0.0;
    render_options.seed = constant ? 17.0 : 11.0;
    const auto source = constant ? kConstantSource : kNonconstantSource;
    if (!constant) render_options.seed_surfaces.push_back({"o0", patterned_seed(dimensions.first, dimensions.second)});
    const auto result = renderer.render(source, render_options);
    const auto bytes = result.to_rgba8();
    REQUIRE(result.pass_count() == (constant ? 3U : 2U));
    if (constant) {
      REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kConstant11x9.size());
      REQUIRE(std::equal(bytes.begin(), bytes.end(), noisemaker_dsl_blur_oracle::kConstant11x9.begin()));
    } else if (dimensions.first == 5U) {
      REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kNonconstant5x3.size());
      REQUIRE(std::equal(bytes.begin(), bytes.end(), noisemaker_dsl_blur_oracle::kNonconstant5x3.begin()));
    } else {
      REQUIRE(bytes.size() == noisemaker_dsl_blur_oracle::kNonconstant7x4.size());
      REQUIRE(std::equal(bytes.begin(), bytes.end(), noisemaker_dsl_blur_oracle::kNonconstant7x4.begin()));
    }
  }
}
