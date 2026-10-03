#include "test_harness.hpp"
#include "noisemaker/renderer.hpp"
#include "noisemaker/effects/mesh_render_contract.hpp"

#include <algorithm>
#include <functional>
#include <limits>
#include <string>

namespace {
using namespace noisemaker;
using namespace noisemaker::graph;

std::string source(std::string_view call) {
  return "search synth, render\nsolid(color: #f00)." + std::string(call) +
         ".write(o0)\nrender(o0)\n";
}

RenderOptions mesh_options() {
  RenderOptions options;
  options.width = 9U;
  options.height = 7U;
  options.mesh_data = MeshData{3U, 1U,
      {-0.8F, -0.7F, 0.0F, 1.0F, 0.7F, -0.6F, 0.4F, 1.0F, -0.1F, 0.9F, -0.2F, 1.0F},
      {0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F}};
  return options;
}

const EffectStep& mesh_step(const ExecutionPlan& plan) {
  for (const auto& chain : plan.chains) {
    for (const auto& variant : chain.steps) {
      const auto* step = std::get_if<EffectStep>(&variant);
      if (step != nullptr && step->effect.id == "render/meshRender") return *step;
    }
  }
  throw std::logic_error("mesh step missing");
}
}  // namespace

TEST(mesh_whole_pass_graph_matches_authenticated_cpu26d_captures) {
  // Captured through tools/dsl/corpus_authority.mjs importCpu at CPU26d,
  // including clear pass, RGBA16F quantization, upload and RGBA8 export.
  const std::pair<std::string_view, std::string_view> cases[] = {
      {"meshRender()", "e2c6d13dbddf4569a89f441e592978f1d3c0b2c6157fd04857271aa6c64f0884"},
      {"meshRender(scale: 0.7, offsetX: 0.2, rotateZ: 35, meshColor: #fc8)",
       "5fd222fe471d25214f5999fe7ae27a5404655662783544d433015500153f50a7"},
      {"meshRender(wireframe: wireframe)", "9d3cf2c490412dfb34f726306f4b86f013135db64a8d9b8ca62398865fdab043"},
  };
  Renderer renderer;
  const auto options = mesh_options();
  for (const auto& [call, hash] : cases) {
    const auto result = renderer.render(source(call), options);
    const auto bytes = result.to_rgba8();
    REQUIRE(result.pass_count() == 3U);
    REQUIRE(bytes.size() == 9U * 7U * 4U);
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(bytes.data()), bytes.size())) == hash);
    REQUIRE(bytes[0] == 25U);
    REQUIRE(bytes[1] == 25U);
    REQUIRE(bytes[2] == 38U);
    REQUIRE(bytes[3] == 255U);
  }
}

TEST(mesh_whole_pass_route_authentication_rejects_forged_metadata_and_abi) {
  Renderer renderer;
  const auto plan = renderer.compile(source("meshRender()"));
  const auto& step = mesh_step(plan);
  const auto& admission = step.passes[1];
  REQUIRE(admission.route_kind == "whole_pass");
  REQUIRE(authenticate_factory_route(step, admission)->bind == nullptr);
  const std::function<void(PassAdmission&)> mutations[] = {
      [](auto& value) { value.route_kind = "typed_emitter"; },
      [](auto& value) { value.source_sha256[0] = value.source_sha256[0] == '0' ? '1' : '0'; },
      [](auto& value) { value.typed_abi_sha256[0] = value.typed_abi_sha256[0] == '0' ? '1' : '0'; },
      [](auto& value) { std::swap(value.uniforms[0], value.uniforms[1]); },
      [](auto& value) { value.uniforms[0].cpp_type = "glsl::Vec3"; },
      [](auto& value) { std::swap(value.samplers[0], value.samplers[1]); },
      [](auto& value) { value.output_extent.format = "rgba32f"; },
  };
  for (const auto& mutate : mutations) {
    auto forged = admission;
    mutate(forged);
    REQUIRE_THROWS_AS(authenticate_factory_route(step, forged), GraphError);
  }
  const auto& definition = plan.effects[step.snapshot_index].definition;
  REQUIRE_THROWS_AS(bind_factory_route(step, admission, definition, glsl::Bindings{}), GraphError);
}

TEST(mesh_whole_pass_controls_and_missing_external_data_fail_closed) {
  Renderer renderer;
  const auto plan = renderer.compile(source("meshRender()"));
  const auto& step = mesh_step(plan);
  const auto& definition = plan.effects[step.snapshot_index].definition;
  const auto options = mesh_options();
  const BindingMaterializationContext context{&options, &definition, 9U, 7U};
  const auto& admission = step.passes[1];
  preflight_pass_abi(step, admission, definition.passes[1], context);
  const std::function<void(effects::PassDefinition&)> mutations[] = {
      [](auto& value) { value.count = effects::Value::string_value("resolution"); },
      [](auto& value) { value.draw_mode = "fragment"; },
      [](auto& value) { value.blend->enabled = true; },
      [](auto& value) { value.viewport = effects::Value::string_value("screen"); },
  };
  for (const auto& mutate : mutations) {
    auto forged = definition.passes[1];
    mutate(forged);
    REQUIRE_THROWS_AS(preflight_pass_abi(step, admission, forged, context), GraphError);
  }
  auto missing = options;
  missing.mesh_data.reset();
  try {
    (void)renderer.render(plan, missing);
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::missing_resource);
  }
}

TEST(mesh_whole_pass_external_mesh_dimensions_and_routes_fail_before_allocation) {
  Renderer renderer;
  const auto plan = renderer.compile(source("meshRender()"));
  const std::pair<std::size_t, std::size_t> dimensions[] = {
      {0U, 1U}, {1U, 0U}, {kMaxSurfacePixels + 1U, 1U},
      {1U, kMaxSurfacePixels + 1U},
      {std::numeric_limits<std::size_t>::max(), 2U},
  };
  for (const auto& [width, height] : dimensions) {
    auto options = mesh_options();
    options.mesh_data->tex_width = width;
    options.mesh_data->tex_height = height;
    try {
      (void)renderer.render(plan, options);
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::invalid_dimension);
      REQUIRE(error.detail() == "mesh texture dimensions are invalid");
    }
  }
  for (const auto name : {"global_mesh0_positions", "global_mesh0_normals"}) {
    for (const bool seed : {false, true}) {
      auto options = mesh_options();
      if (seed) options.seed_surfaces.push_back({name, Surface(1U, 1U)});
      else options.external_textures.push_back({name, Surface(1U, 1U)});
      try {
        (void)renderer.render(plan, options);
        REQUIRE(false);
      } catch (const GraphError& error) {
        REQUIRE(error.code() == GraphErrorCode::duplicate_output);
        REQUIRE(error.detail() == "duplicate mesh data route");
      }
    }
  }
}

TEST(mesh_whole_pass_iterated_groups_remain_unsupported_by_cpu_authority) {
  Renderer renderer;
  const auto plan = renderer.compile(source("loopBegin(iterationCount: 2).meshRender().loopEnd()"));
  try {
    (void)renderer.render(plan, mesh_options());
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unsupported_draw_mode);
    REQUIRE(error.detail() == "CPU authority does not support mesh whole-pass rendering inside iterated groups");
    REQUIRE(error.effect_id() == "render/meshRender");
    REQUIRE(error.program_key() == "render/meshRender:render");
    REQUIRE(error.pass_index() == 1U);
  }
}
