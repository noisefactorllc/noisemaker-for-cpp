#include "test_harness.hpp"
#include "corpus_census.hpp"

#include "noisemaker/effects/bit_effects.hpp"
#include "noisemaker/effects/median.hpp"
#include "noisemaker/effects/snow.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/renderer.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <new>
#include <limits>
#include <optional>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

// Global allocation accounting. The executor must complete its plan, input,
// route, ABI, and resource preflight before it copies a caller surface or
// allocates a destination, and a copy of a caller surface is large enough to
// be visible here. Counting is armed only around the calls under test.
//
// Under AddressSanitizer the replacement is compiled out: displacing ASan's
// own operator new would drop its redzones and new/delete-mismatch detection
// for every allocation in the binary. The quantitative leg of the test is
// skipped there; its compile-time and caller-surface legs still run.
#if defined(__SANITIZE_ADDRESS__)
#define NOISEMAKER_TEST_COUNTS_ALLOCATIONS 0
#elif defined(__has_feature)
#if __has_feature(address_sanitizer)
#define NOISEMAKER_TEST_COUNTS_ALLOCATIONS 0
#else
#define NOISEMAKER_TEST_COUNTS_ALLOCATIONS 1
#endif
#else
#define NOISEMAKER_TEST_COUNTS_ALLOCATIONS 1
#endif

namespace {
bool g_counting_allocations = false;
std::size_t g_allocated_bytes = 0;
}  // namespace

#if NOISEMAKER_TEST_COUNTS_ALLOCATIONS
namespace {
void* counted_allocate(std::size_t size) {
  if (g_counting_allocations) g_allocated_bytes += size;
  void* pointer = std::malloc(size == 0U ? 1U : size);
  if (pointer == nullptr) throw std::bad_alloc();
  return pointer;
}

void* counted_allocate(std::size_t size, std::align_val_t alignment) {
  if (g_counting_allocations) g_allocated_bytes += size;
  // std::aligned_alloc requires a size that is a multiple of the alignment.
  const std::size_t boundary = static_cast<std::size_t>(alignment);
  const std::size_t requested = size == 0U ? boundary : size;
  const std::size_t bytes = ((requested + boundary - 1U) / boundary) * boundary;
  void* pointer = std::aligned_alloc(boundary, bytes);
  if (pointer == nullptr) throw std::bad_alloc();
  return pointer;
}
}  // namespace

void* operator new(std::size_t size) { return counted_allocate(size); }
void* operator new[](std::size_t size) { return counted_allocate(size); }
void* operator new(std::size_t size, std::align_val_t alignment) {
  return counted_allocate(size, alignment);
}
void* operator new[](std::size_t size, std::align_val_t alignment) {
  return counted_allocate(size, alignment);
}

void operator delete(void* pointer) noexcept { std::free(pointer); }
void operator delete[](void* pointer) noexcept { std::free(pointer); }
void operator delete(void* pointer, std::size_t) noexcept { std::free(pointer); }
void operator delete[](void* pointer, std::size_t) noexcept { std::free(pointer); }
void operator delete(void* pointer, std::align_val_t) noexcept { std::free(pointer); }
void operator delete[](void* pointer, std::align_val_t) noexcept { std::free(pointer); }
void operator delete(void* pointer, std::size_t, std::align_val_t) noexcept { std::free(pointer); }
void operator delete[](void* pointer, std::size_t, std::align_val_t) noexcept { std::free(pointer); }
#endif

namespace {

using namespace noisemaker::graph;
using namespace noisemaker;

constexpr std::string_view kSolidSource =
    "search synth\n"
    "solid(color: #3a7).write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kInvertSource =
    "search synth, filter\n"
    "solid(color: #3a7).invert().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kHighPassSource =
    "search synth, filter\n"
    "solid(color: #3a7).highPass().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kPerlinSource =
    "search synth\n"
    "perlin().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kNoiseSource =
    "search synth\n"
    "noise().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kRemapSource =
    "search synth\n"
    "remap().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kBitEffectsSource =
    "search classicNoisedeck\n"
    "bitEffects().write(o0)\n"
    "render(o0)\n";

constexpr std::string_view kSeededBlurSource =
    "search filter\n"
    "read(o0).blur(radiusX: 2, radiusY: 5).write(o1)\n"
    "render(o1)\n";

RenderOptions options(std::size_t width, std::size_t height) {
  RenderOptions result;
  result.width = width;
  result.height = height;
  result.time = 0.25;
  result.frame = 0;
  result.seed = 17.0;
  return result;
}

EffectStep& effect_step(ExecutionPlan& plan, std::string_view effect_id) {
  for (auto& chain : plan.chains) {
    for (auto& variant : chain.steps) {
      auto* step = std::get_if<EffectStep>(&variant);
      if (step != nullptr && step->effect.id == effect_id) return *step;
    }
  }
  throw std::logic_error("test effect step not found");
}

PlanEffectSnapshot& snapshot_for(ExecutionPlan& plan, std::string_view effect_id) {
  for (auto& snapshot : plan.effects) {
    if (snapshot.definition.id == effect_id) return snapshot;
  }
  throw std::logic_error("test effect snapshot not found");
}

void reauthenticate(ExecutionPlan& plan) {
  for (auto& snapshot : plan.effects) {
    snapshot.snapshot_sha256 = detail::snapshot_sha256(snapshot);
  }
  plan.provenance.plan_payload_sha256 = detail::plan_payload_sha256(plan);
}

const FactoryRouteDescriptor* canonical_route(std::string_view program_key,
                                              std::string_view canonical_factory) {
  return find_factory_route(canonical_factory_routes(), program_key,
                            canonical_factory);
}

// Renders are compared to the pinned CPU authority by exact RGBA8 digest:
// dimensions and length first, then every byte through the hash.
std::string rgba8_sha256(const RenderResult& result) {
  const auto bytes = result.to_rgba8();
  REQUIRE(bytes.size() == result.width() * result.height() * 4U);
  return detail::sha256(std::string_view(
      reinterpret_cast<const char*>(bytes.data()), bytes.size()));
}

Surface patterned_seed(std::size_t width, std::size_t height) {
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t index = 0; index < bytes.size(); ++index) {
    bytes[index] = static_cast<std::uint8_t>((index * 37U + 11U) % 256U);
  }
  return Surface::from_rgba8(width, height, bytes);
}

// Binds one compiled pass through the public materialization seam so a
// derived value can be asserted exactly rather than inferred from pixels.
glsl::Bindings bind_compiled_pass(ExecutionPlan& plan, std::string_view effect_id,
                                  std::size_t pass_index,
                                  const ExecutionInputs& inputs,
                                  std::size_t destination_width,
                                  std::size_t destination_height) {
  auto& snapshot = snapshot_for(plan, effect_id);
  const auto& step = effect_step(plan, effect_id);
  const auto& pass = snapshot.definition.passes[pass_index];
  const auto& admission = snapshot.admissions[pass_index];
  const BindingMaterializationContext context{
      &inputs, &snapshot.definition, destination_width, destination_height};
  preflight_pass_abi(step, admission, pass, context);
  return materialize_uniform_bindings(step, admission, pass, context);
}

}  // namespace

// The advertised preflight boundary must be observable in the type system:
// a by-value parameter would copy every caller surface before validation.
static_assert(
    std::is_same_v<decltype(&GraphExecutor::execute),
                   ExecutionResult (GraphExecutor::*)(const ExecutionPlan&,
                                                      const ExecutionInputs&) const>);

TEST(graph_audio_uniforms_default_to_zero_and_snapshot_independent_arrays) {
  Renderer renderer;
  for (const auto effect : {"scope", "spectrum"}) {
    const std::string effect_id = std::string("synth/") + effect;
    const std::string uniform = std::string(effect) == "scope" ? "audioWaveform" : "audioSpectrum";
    auto plan = renderer.compile(std::string("search synth\n") + effect +
                                 "().write(o0)\nrender(o0)\n", "audio-input.dsl");
    ExecutionInputs inputs;
    inputs.width = 7U;
    inputs.height = 5U;
    const auto defaults = bind_compiled_pass(plan, effect_id, 0U, inputs, 7U, 5U)
                              .get<glsl::AudioUniform128>(uniform);
    for (float value : defaults.data) REQUIRE(value == 0.0F);
    inputs.audio_state.emplace();
    inputs.audio_state->waveform.data.fill(0.1234567F);
    inputs.audio_state->spectrum.data.fill(0.7654321F);
    const auto bound = bind_compiled_pass(plan, effect_id, 0U, inputs, 7U, 5U);
    const float expected = std::string(effect) == "scope" ? 0.1234567F : 0.7654321F;
    inputs.audio_state->waveform.data.fill(0.9F);
    inputs.audio_state->spectrum.data.fill(0.9F);
    for (float value : bound.get<glsl::AudioUniform128>(uniform).data) REQUIRE(value == expected);
    const auto rebound = bind_compiled_pass(plan, effect_id, 0U, inputs, 7U, 5U);
    for (float value : rebound.get<glsl::AudioUniform128>(uniform).data) REQUIRE(value == 0.9F);
  }
}

TEST(graph_roll_binds_zero_grid_then_uploaded_channel_one_at_the_bottom) {
  Renderer renderer;
  const auto source = "search synth\nroll().write(o0)\nrender(o0)\n";
  auto opts = options(17U, 256U);
  const auto empty = renderer.render(source, opts);
  opts.midi_state.emplace();
  opts.midi_state->note_grid[60U * 4U] = 1.0F;
  opts.midi_state->note_grid[60U * 4U + 1U] = 1.0F;
  opts.midi_state->clock_count = 241.5;
  const auto original = opts.midi_state->note_grid;
  const auto active = renderer.render(source, opts);
  REQUIRE(active.pass_count() == 2U);
  REQUIRE(opts.midi_state->note_grid == original);
  const auto bottom = (247U * 17U) * 4U + 1U;
  const auto top = (7U * 17U) * 4U + 1U;
  REQUIRE(empty.surface().data()[bottom] == 0.0F);
  REQUIRE(active.surface().data()[bottom] == 1.0F);
  REQUIRE(active.surface().data()[top] == empty.surface().data()[top]);
  auto plan = renderer.compile(source);
  REQUIRE(bind_compiled_pass(plan, "synth/roll", 0U, opts, 17U, 256U)
              .get_number("midiClockCount") == 241.5);
  opts.external_textures.push_back({"midiNoteGrid", Surface(128U, 16U)});
  REQUIRE_THROWS_AS(renderer.render(source, opts), GraphError);
}

TEST(graph_mesh_loader_binds_packed_data_with_upload_row_orientation) {
  Renderer renderer;
  auto opts = options(3U, 2U);
  opts.mesh_data = MeshData{2U, 2U,
      {-0.5F, 0.25F, 0.75F, 1.0F, 1.5F, -0.75F, 0.125F, 1.0F,
       0.125F, 0.5F, -1.0F, 1.0F, -0.25F, 1.5F, 0.5F, 1.0F},
      {1.0F, 0.0F, -1.0F, 0.0F, 0.5F, -0.5F, 0.25F, 0.0F,
       -0.25F, 0.75F, 0.5F, 0.0F, 0.125F, -0.75F, 1.0F, 0.0F}};
  const auto original = opts.mesh_data->position_data;
  const auto result = renderer.render("search render\nmeshLoader().write(o0)\nrender(o0)\n", opts);
  REQUIRE(result.pass_count() == 1U);
  const std::vector<float> expected{
      0.5625F, 0.75F, 0.0F, 1.0F, 0.5625F, 0.125F, 1.0F, 1.0F, 0.5625F, 0.125F, 1.0F, 1.0F,
      0.25F, 0.625F, 0.875F, 1.0F, 0.75F, 0.25F, 0.625F, 1.0F, 0.75F, 0.25F, 0.625F, 1.0F};
  const auto actual = result.surface().data();
  REQUIRE(std::vector<float>(actual.begin(), actual.end()) == expected);
  REQUIRE(opts.mesh_data->position_data == original);
}

TEST(graph_mesh_loader_samples_the_empty_mesh_without_data_and_preserves_default_dimensions) {
  Renderer renderer;
  const auto source = "search render\nmeshLoader().write(o0)\nrender(o0)\n";
  auto opts = options(1U, 1U);
  // CPU 3cc7a036: with no meshData the authority samples emptyMeshData(), the
  // zero-filled 256x256 mesh textures.
  const auto empty = renderer.render(source, opts);
  REQUIRE(empty.pass_count() == 1U);
  const auto lanes = empty.surface().data();
  REQUIRE(std::vector<float>(lanes.begin(), lanes.end()) == std::vector<float>({0.5F, 0.5F, 0.5F, 1.0F}));
  opts.mesh_data.emplace();
  REQUIRE(opts.mesh_data->tex_width == 256U);
  REQUIRE(opts.mesh_data->tex_height == 256U);
  opts.mesh_data->position_data.resize(256U * 256U * 4U);
  opts.mesh_data->normal_data.resize(256U * 256U * 4U);
  REQUIRE(renderer.render(source, opts).pass_count() == 1U);
  opts.mesh_data->tex_width = 0U;
  REQUIRE_THROWS_AS(renderer.render(source, opts), GraphError);
  opts.mesh_data->tex_width = 256U;
  opts.external_textures.push_back({"global_mesh0_positions", Surface(1U, 1U)});
  REQUIRE_THROWS_AS(renderer.render(source, opts), GraphError);
}

TEST(graph_mesh_loader_pads_short_arrays_and_ignores_extra_upload_words) {
  Renderer renderer;
  const auto source = "search render\nmeshLoader().write(o0)\nrender(o0)\n";
  auto opts = options(2U, 2U);
  opts.mesh_data = MeshData{1U, 2U, {}, {}};
  auto empty = renderer.render(source, opts);
  for (std::size_t pixel = 0; pixel < 4U; ++pixel) {
    const auto lanes = empty.surface().data();
    REQUIRE(lanes[pixel * 4U] == 0.5F);
    REQUIRE(lanes[pixel * 4U + 1U] == 0.5F);
    REQUIRE(lanes[pixel * 4U + 2U] == 0.5F);
    REQUIRE(lanes[pixel * 4U + 3U] == 1.0F);
  }
  opts.mesh_data->position_data = {-0.5F, 0.25F, 0.75F, 1.0F, 0.125F};
  opts.mesh_data->normal_data = {0.5F};
  const auto partial = renderer.render(source, opts);
  const std::vector<float> expected{
      0.5625F, 0.5F, 0.5F, 1.0F, 0.5F, 0.5F, 0.5F, 1.0F,
      0.25F, 0.625F, 0.875F, 1.0F, 0.75F, 0.5F, 0.5F, 1.0F};
  const auto actual = partial.surface().data();
  REQUIRE(std::vector<float>(actual.begin(), actual.end()) == expected);
  opts.mesh_data->position_data.resize(8U, 0.0F);
  opts.mesh_data->normal_data.resize(8U, 0.0F);
  opts.mesh_data->position_data.insert(opts.mesh_data->position_data.end(), {32.0F, -32.0F, 64.0F});
  opts.mesh_data->normal_data.insert(opts.mesh_data->normal_data.end(), {-8.0F, 8.0F});
  const auto extra = renderer.render(source, opts);
  const auto extra_lanes = extra.surface().data();
  REQUIRE(std::vector<float>(extra_lanes.begin(), extra_lanes.end()) == expected);
}

TEST(graph_mesh_loader_preserves_float32_until_output_quantization) {
  Renderer renderer;
  auto opts = options(2U, 1U);
  opts.mesh_data = MeshData{1U, 1U, {-0.9999F, 0.0F, 0.0F, 1.0F}, {}};
  const auto result = renderer.render("search render\nmeshLoader().write(o0)\nrender(o0)\n", opts);
  // CPU 26d6f42: quantizing this input to half first instead produces 0.000244140625.
  REQUIRE(result.surface().data()[0] == 0.000050008296966552734F);
}

TEST(graph_generated_canonical_route_table_is_connected_and_duplicate_safe) {
  const auto routes = canonical_factory_routes();
  REQUIRE(routes.size() == corpus_census::expected_single_output_route_rows() + 1U);
  // Every multi-output corpus program is published through the MRT table
  // instead, and never through the single-output one.
  const auto mrt_routes = canonical_factory_routes_mrt();
  const auto mrt_keys = corpus_census::mrt_program_keys();
  REQUIRE(mrt_routes.size() == mrt_keys.size());
  for (std::size_t index = 0; index < mrt_keys.size(); ++index) {
    REQUIRE(mrt_routes[index].program_key == mrt_keys[index]);
    REQUIRE(mrt_routes[index].bind != nullptr);
    for (const auto& route : routes) REQUIRE(route.program_key != mrt_keys[index]);
  }

  // The two duplicate legacy keys must resolve to the authenticated canonical
  // factory only; the legacy physical row is absent from the canonical view.
  const auto* invert = canonical_route("filter/invert:inv", "bind_filter_invert_inv");
  REQUIRE(invert != nullptr);
  REQUIRE(invert->emitted_factory == "bind_filter_invert_inv");
  REQUIRE(invert->route_kind == "typed_emitter");
  REQUIRE(canonical_route("filter/invert:inv", "bind_filter_invert") == nullptr);
  const auto* solid = canonical_route("synth/solid:solid", "bind_synth_solid_solid");
  REQUIRE(solid != nullptr);
  REQUIRE(solid->emitted_factory == "bind_synth_solid_solid");
  REQUIRE(canonical_route("synth/solid:solid", "bind_synth_solid") == nullptr);

  const auto* bit_effects = canonical_route("classicNoisedeck/bitEffects:bitEffects",
                                            "noisemaker::effects::bind_bit_effects");
  REQUIRE(bit_effects != nullptr);
  REQUIRE(bit_effects->route_kind == "custom_adapter");
  REQUIRE(bit_effects->bind == &noisemaker::effects::bind_bit_effects);

  // filter/snow:snow: a second hand-written custom adapter, following the
  // exact same bitEffects row shape (only canonical_factory, route_kind,
  // and bind change; every ABI/source hash stays the GLSL-declared one --
  // see src/effects/snow.cpp and the field comment on
  // kMeasuredParityExclusions above).
  const auto* snow = canonical_route("filter/snow:snow", "noisemaker::effects::bind_snow");
  REQUIRE(snow != nullptr);
  REQUIRE(snow->route_kind == "custom_adapter");
  REQUIRE(snow->bind == &noisemaker::effects::bind_snow);
  const auto* median = canonical_route("filter/median:median", "noisemaker::effects::bind_median");
  REQUIRE(median != nullptr);
  REQUIRE(median->route_kind == "custom_adapter");
  REQUIRE(median->bind == &noisemaker::effects::bind_median);

  // The source-incompatible row stays present for inspection; execution
  // rejects it on admission status, not by absence from the table.
  REQUIRE(canonical_route("filter/text:text", "bind_filter_text_text") != nullptr);

  std::size_t typed_emitter = 0;
  std::size_t custom_adapter = 0;
  std::size_t whole_pass = 0;
  for (const auto& route : routes) {
    if (route.route_kind == "whole_pass") {
      REQUIRE(route.program_key == "render/meshRender:render");
      REQUIRE(route.canonical_factory == "noisemaker::effects::render_triangles");
      REQUIRE(route.bind == nullptr);
      ++whole_pass;
    } else {
      REQUIRE(route.bind != nullptr);
    }
    REQUIRE(route.source_sha256.size() == 64U);
    REQUIRE(route.typed_abi_sha256.size() == 64U);
    if (route.route_kind == "typed_emitter") ++typed_emitter;
    if (route.route_kind == "custom_adapter") ++custom_adapter;
  }
  // Eight hand-written custom adapters (bitEffects, crt, median, the
  // pixelSort luminance pass, the reindex stats and apply passes, remap,
  // snow); every other single-output corpus program is a typed-emitter route.
  REQUIRE(custom_adapter == 8U);
  REQUIRE(whole_pass == 1U);
  REQUIRE(typed_emitter == corpus_census::expected_single_output_route_rows() - custom_adapter);
}

TEST(graph_executor_dispatches_the_duplicate_canonical_invert_route) {
  Renderer renderer;
  auto plan = renderer.compile(kInvertSource, "invert.dsl");
  const auto& admission = snapshot_for(plan, "filter/invert").admissions[0];
  REQUIRE(admission.identity.program_key == "filter/invert:inv");
  REQUIRE(admission.canonical_factory == "bind_filter_invert_inv");
  REQUIRE(admission.emitted_factory == "bind_filter_invert_inv");
  REQUIRE(admission.route_kind == "typed_emitter");

  // Actual dispatch: the inverted result must be the exact per-channel
  // complement of the same solid render, which only the real invert kernel
  // produces.
  const auto plain = renderer.render(kSolidSource, options(7U, 5U), "solid.dsl").to_rgba8();
  const auto inverted = renderer.render(plan, options(7U, 5U)).to_rgba8();
  REQUIRE(inverted.size() == plain.size());
  for (std::size_t index = 0; index < inverted.size(); ++index) {
    const bool alpha = (index % 4U) == 3U;
    REQUIRE(inverted[index] ==
            (alpha ? plain[index] : static_cast<std::uint8_t>(255U - plain[index])));
  }
}

TEST(graph_composite_color_distance_matches_authority_at_range_boundary) {
  Renderer renderer;
  constexpr std::string_view source =
      "search synth, classicNoisedeck\n"
      "solid(color: #00f).write(o1)\n"
      "solid(color: #f00).composite(tex: o1, "
      "inputColor: [0.7311236763534933, 0.12281395953931051, 0.8734191544441814], "
      "range: 92.20839543873512, blendMode: 1, mix: 50).write(o0)\n"
      "render(o0)\n";
  const auto result = renderer.render(source, options(3U, 2U));
  // Exact RGBA8 and Float32 from pinned JS authority 61aa869 through
  // run_cpu_case.mjs. A distance evaluated wholly in double returns blue;
  // the authority's intermediate Float32 writes select the purple blend.
  REQUIRE(rgba8_sha256(result) ==
          "c2b238e970fc079b0eb344ced8cb87d1d109a5c1dbb5b8f8c0f0904cfe44edd0");
  constexpr std::array expected{0.5f, 0.0f, 0.5f, 1.0f};
  const auto pixels = result.surface().data();
  for (std::size_t index = 0; index < pixels.size(); ++index) {
    REQUIRE(float_bits_to_uint(pixels[index]) ==
            float_bits_to_uint(expected[index % expected.size()]));
  }
}

TEST(graph_executor_rejects_the_legacy_duplicate_factory_for_a_canonical_key) {
  Renderer renderer;
  auto plan = renderer.compile(kInvertSource, "legacy-invert.dsl");
  snapshot_for(plan, "filter/invert").admissions[0].canonical_factory = "bind_filter_invert";
  effect_step(plan, "filter/invert").passes[0].canonical_factory = "bind_filter_invert";
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
    REQUIRE(error.program_key() == "filter/invert:inv");
    REQUIRE(error.detail() == "canonical factory route is not admitted");
  }
}

TEST(graph_executor_rejects_generated_route_metadata_that_differs_from_the_admission) {
  const auto expect_rejected = [](auto&& mutate) {
    Renderer renderer;
    auto plan = renderer.compile(kInvertSource, "forged-route-metadata.dsl");
    mutate(snapshot_for(plan, "filter/invert").admissions[0]);
    mutate(effect_step(plan, "filter/invert").passes[0]);
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(7U, 5U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
      REQUIRE(error.detail() == "generated route metadata differs from the admission");
    }
  };
  expect_rejected([](PassAdmission& admission) { admission.emitted_factory = "bind_filter_invert"; });
  expect_rejected([](PassAdmission& admission) { admission.route_kind = "custom_adapter"; });
  expect_rejected([](PassAdmission& admission) {
    admission.source_sha256 = std::string(64U, 'a');
  });
  expect_rejected([](PassAdmission& admission) {
    admission.typed_abi_sha256 = std::string(64U, 'b');
  });
}

TEST(graph_executor_materializes_every_ordered_sampler_route) {
  Renderer renderer;
  auto plan = renderer.compile(kHighPassSource, "high-pass.dsl");
  auto& snapshot = snapshot_for(plan, "filter/highPass");
  REQUIRE(snapshot.admissions.size() == 3U);
  const auto& combine = snapshot.admissions[2];
  REQUIRE(combine.identity.program_key == "filter/highPass:hpCombine");
  REQUIRE(combine.samplers.size() == 2U);
  REQUIRE(combine.samplers[0].resource != combine.samplers[1].resource);
  // The second sampler is a named intermediate produced by an earlier pass of
  // the same effect, not the implicit input image.
  REQUIRE(combine.samplers[1].resource != "inputTex");

  const auto result = renderer.render(plan, options(9U, 6U));
  REQUIRE(result.width() == 9U);
  REQUIRE(result.height() == 6U);
  REQUIRE(result.pass_count() == 4U);
}

TEST(graph_executor_renders_cellular_automata_with_unused_authority_inputs) {
  // Independent RGBA8 hashes from pinned JS authority 9f3bd6ad. The
  // authenticated CpuRenderer rendered these exact programs and options.
  // The render pass declares four input routes but its shader samples two.
  Renderer renderer;
  for (const auto& [iterations, expected] :
       std::vector<std::pair<int, std::string_view>>{
           {3, "01e38f2e1fa62415128c6d2508b4fb02095c22dd772eb21d218668dfa91a830d"},
           {7, "986a0fed202c801b92b7f2a5ce3c1d01b8df71ed05e265363779629233ceb473"}}) {
    const auto source = "search synth\ncellularAutomata(zoom: 1, iterationCount: " +
                        std::to_string(iterations) + ").write(o0)\nrender(o0)\n";
    const auto result = renderer.render(source, options(9U, 6U));
    REQUIRE(result.pass_count() == static_cast<std::size_t>(iterations) * 2U);
    REQUIRE(rgba8_sha256(result) == expected);
  }
}

TEST(graph_executor_renders_mnca_with_unused_authority_inputs) {
  // Same authority capture as the cellularAutomata case above; the two
  // iteration counts have different images, so this also catches a skipped
  // update pass or a renderer that returns only its first iteration.
  Renderer renderer;
  for (const auto& [iterations, expected] :
       std::vector<std::pair<int, std::string_view>>{
           {3, "ee6326a670cd14c024a3d97d33a6c0787544595fee454a9eb8614c8704b49332"},
           {7, "6a9ef5194229a0aa8a9a828a188d8c4f43efc1b7cee08d7d87fad344efd06e49"}}) {
    const auto source = "search synth\nmnca(zoom: 1, iterationCount: " +
                        std::to_string(iterations) + ").write(o0)\nrender(o0)\n";
    const auto result = renderer.render(source, options(9U, 6U));
    REQUIRE(result.pass_count() == static_cast<std::size_t>(iterations) * 2U);
    REQUIRE(rgba8_sha256(result) == expected);
  }
}

TEST(graph_sampler_preflight_accepts_authority_input_map_order) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth, points\nsolid().hydraulic().write(o0)\nrender(o0)\n");
  const auto& snapshot = snapshot_for(plan, "points/hydraulic");
  const auto& step = effect_step(plan, "points/hydraulic");
  const auto inputs = options(9U, 6U);
  const BindingMaterializationContext context{
      &inputs, &snapshot.definition, inputs.width, inputs.height};
  // The shader starts with inputTex; the authority input map ends with it.
  // Both orders are independently authenticated and do not need to coincide.
  REQUIRE(snapshot.admissions[0].samplers.front().name == "inputTex");
  REQUIRE(snapshot.definition.passes[0].inputs.back().first == "inputTex");
  preflight_pass_abi(step, snapshot.admissions[0], snapshot.definition.passes[0], context);
}

TEST(graph_sampler_preflight_rejects_forged_routes_despite_unused_authority_inputs) {
  Renderer renderer;
  auto plan = renderer.compile("search synth\nmnca().write(o0)\nrender(o0)\n");
  const auto& snapshot = snapshot_for(plan, "synth/mnca");
  const auto& step = effect_step(plan, "synth/mnca");
  const auto& pass = snapshot.definition.passes[1];
  const auto inputs = options(9U, 6U);
  const BindingMaterializationContext context{
      &inputs, &snapshot.definition, inputs.width, inputs.height};
  const auto expect_rejected = [&](auto&& mutate) {
    auto admission = snapshot.admissions[1];
    mutate(admission);
    try {
      preflight_pass_abi(step, admission, pass, context);
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::missing_binding);
      REQUIRE(error.detail() == "sampler ABI route is invalid");
    }
  };
  expect_rejected([](PassAdmission& admission) {
    admission.samplers[0].resource = "tex";
  });
  expect_rejected([](PassAdmission& admission) {
    admission.samplers[0].name = "undeclaredTex";
  });
  expect_rejected([](PassAdmission& admission) {
    admission.samplers[1].name = admission.samplers[0].name;
  });
  expect_rejected([](PassAdmission& admission) {
    admission.samplers[0].source_name = "forged";
  });
}

TEST(graph_iterated_surface_parameters_resolve_prior_named_outputs) {
  Renderer renderer;
  for (const std::string_view effect : {"cellularAutomata", "mnca"}) {
    const auto source = "search synth\nnoise().write(o1)\n" + std::string(effect) +
                        "(tex: o1, zoom: 1, weight: 100, iterationCount: 3)"
                        ".write(o0)\nrender(o0)\n";
    const auto result = renderer.render(source, options(9U, 6U));
    REQUIRE(result.pass_count() == 7U);
    // Pinned JS authority 9f3bd6ad, captured with its CpuRenderer. Weight
    // 100 makes the named source change the image; an empty fallback fails.
    REQUIRE(rgba8_sha256(result) ==
            "151bdd9587ee3224e7b2027b9ea26a7b127583004ec898b900dde9ccdbb5757f");
  }
}

TEST(graph_iterated_surface_parameters_reject_unwritten_named_outputs) {
  Renderer renderer;
  for (const std::string_view effect : {"cellularAutomata", "mnca"}) {
    auto plan = renderer.compile("search synth\n" + std::string(effect) +
        "(tex: o1, iterationCount: 3).write(o0)\nrender(o0)\n");
    try {
      static_cast<void>(renderer.render(plan, options(9U, 6U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::read_before_write);
      REQUIRE(error.effect_id() == "synth/" + std::string(effect));
    }
  }
}

TEST(graph_executor_fails_closed_on_an_unproduced_secondary_sampler_route) {
  // Unforged: filter/lighting's second sampler is a surface parameter bound
  // to a route the same step only writes afterwards, so the declared route
  // has no producer at read time. The authority rejects it the same way.
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth, filter\n"
      "solid(color: #3a7).lighting(heightMap: o0).write(o0)\n"
      "render(o0)\n",
      "lighting-self-reference.dsl");
  const auto& admission = snapshot_for(plan, "filter/lighting").admissions[0];
  REQUIRE(admission.samplers.size() == 2U);
  REQUIRE(admission.samplers[1].resource == "heightMap");
  try {
    static_cast<void>(renderer.render(plan, options(9U, 6U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::read_before_write);
    REQUIRE(error.program_key() == "filter/lighting:lighting");
  }
}

TEST(graph_executor_binds_every_declared_sampler_of_a_wide_route) {
  // remap declares eight sampler routes, all fed by unbound surface
  // parameters. The authority binds its 1x1 empty surface for each.
  //
  // KNOWN FAILING as of the 0ed489ec.../61aa869 authority bump, for a reason
  // upstream of this lane: synth/remap:remap is classified "incompatible" in
  // src/effects/generated/backend_compatibility.json (its pinned source
  // changed and the retired typed-generated kernel no longer matches it), so
  // the DSL/graph pipeline now refuses to compile or dispatch ANY remap pass
  // at all -- "pass is not executable"/"pass is not compatible" -- for every
  // remap DSL program regardless of what this test asserts. Reaching
  // "compatible" needs a custom_adapter route added to
  // tools/glslcpp/generate_typed_slice.py's _factory_route and
  // tools/dsl/generate_backend_compatibility.py's _custom_factory_route
  // (both outside this lane's permitted edits). The standalone kernel this
  // lane delivers (noisemaker::effects::bind_remap, oracle-verified in
  // tests/test_generated_kernels.cpp) does not depend on that route and is
  // unaffected.
  Renderer renderer;
  auto plan = renderer.compile(kRemapSource, "remap.dsl");
  const auto& admission = snapshot_for(plan, "synth/remap").admissions[0];
  REQUIRE(admission.samplers.size() == 8U);
  const auto result = renderer.render(plan, options(5U, 3U));
  REQUIRE(result.width() == 5U);
  REQUIRE(result.height() == 3U);
  REQUIRE(result.pass_count() == 1U);
}

TEST(graph_executor_resolves_the_aspect_ratio_pass_derived_binding) {
  Renderer renderer;
  auto plan = renderer.compile(kPerlinSource, "perlin.dsl");
  const auto& admission = snapshot_for(plan, "synth/perlin").admissions[0];
  const auto aspect = std::find_if(
      admission.uniforms.begin(), admission.uniforms.end(),
      [](const auto& uniform) { return uniform.name == "aspect"; });
  REQUIRE(aspect != admission.uniforms.end());
  REQUIRE(aspect->source == "pass_derived");
  REQUIRE(aspect->source_name == "fullResolution_aspect_ratio");

  const auto inputs = options(11U, 7U);
  const auto bindings = bind_compiled_pass(plan, "synth/perlin", 0U, inputs, 11U, 7U);
  REQUIRE(bindings.get<float>("aspect") == noisemaker::f32(11.0 / 7.0));

  const auto result = renderer.render(plan, inputs);
  REQUIRE(result.width() == 11U);
  REQUIRE(result.height() == 7U);
  REQUIRE(result.pass_count() == 1U);
}

TEST(graph_executor_resolves_typed_compile_define_bindings_from_owned_parameters) {
  Renderer renderer;
  auto plan = renderer.compile(kNoiseSource, "noise.dsl");
  const auto& admission = snapshot_for(plan, "synth/noise").admissions[0];
  const auto define = std::find_if(
      admission.uniforms.begin(), admission.uniforms.end(),
      [](const auto& uniform) { return uniform.name == "NOISE_TYPE"; });
  REQUIRE(define != admission.uniforms.end());
  REQUIRE(define->source_name == "typed_compile_define");

  const auto inputs = options(6U, 6U);
  const auto bindings = bind_compiled_pass(plan, "synth/noise", 0U, inputs, 6U, 6U);
  REQUIRE(bindings.get<std::int32_t>("NOISE_TYPE") == 10);
  REQUIRE(bindings.get<std::int32_t>("LOOP_OFFSET") == 300);

  auto explicit_plan = renderer.compile(
      "search synth\nnoise(type: 2, loopOffset: 20).write(o0)\nrender(o0)\n",
      "noise-explicit.dsl");
  const auto explicit_bindings =
      bind_compiled_pass(explicit_plan, "synth/noise", 0U, inputs, 6U, 6U);
  REQUIRE(explicit_bindings.get<std::int32_t>("NOISE_TYPE") == 2);
  REQUIRE(explicit_bindings.get<std::int32_t>("LOOP_OFFSET") == 20);
  REQUIRE(renderer.render(explicit_plan, inputs).pass_count() == 1U);
}

TEST(graph_executor_owns_the_remap_semantic_bindings_and_canonical_defaults) {
  // synth/remap:remap is a custom_adapter route (see src/effects/remap.cpp):
  // its dispatch-time ABI is bind_remap's own semantic uniform surface
  // (zoneCount, smoothEdge, bgColor, bgAlpha, zone{N}_*), never the retired
  // packed std140 `data[275]` array -- that array is no longer part of this
  // program's admission at all (nothing declares a "data" uniform for it
  // any more), so it is unreachable through bind_compiled_pass.
  Renderer renderer;
  auto plan = renderer.compile(kRemapSource, "remap-uniforms.dsl");
  const auto inputs = options(13U, 4U);
  const auto bindings = bind_compiled_pass(plan, "synth/remap", 0U, inputs, 13U, 4U);
  REQUIRE(bindings.get_or<double>("zoneCount", -1.0) == 0.0);
  REQUIRE(bindings.get_or<double>("smoothEdge", -1.0) == 0.04);
  REQUIRE(bindings.get_or<double>("bgAlpha", -1.0) == 1.0);
  const auto bg_color = bindings.get_or<glsl::DVec3>("bgColor", glsl::DVec3(-1.0, -1.0, -1.0));
  REQUIRE(bg_color[0] == 0.0);
  REQUIRE(bg_color[1] == 0.0);
  REQUIRE(bg_color[2] == 0.0);
  REQUIRE(bindings.get<glsl::Vec2>("fullResolution") == glsl::Vec2(13.0F, 4.0F));
  REQUIRE(bindings.get<glsl::Vec2>("resolution") == glsl::Vec2(13.0F, 4.0F));
  // No zone{N}_tex is bound (kRemapSource wires none), so every zone's
  // colorModeUniform-derived `active` flag reads the authority's unbound
  // default: 0.
  for (std::size_t zone = 0U; zone < 8U; ++zone) {
    const auto name = "zone" + std::to_string(zone) + "_active";
    REQUIRE(bindings.get_or<double>(name, -1.0) == 0.0);
  }
  // No zone{N}_bounds is bound either; every zone defaults to the
  // authority's [0, 0, 1, 1] (a box that never rejects a canvas pixel).
  for (std::size_t zone = 0U; zone < 8U; ++zone) {
    const auto name = "zone" + std::to_string(zone) + "_bounds";
    const auto bounds = bindings.get_or<glsl::DVec4>(name, glsl::DVec4(-1.0, -1.0, -1.0, -1.0));
    REQUIRE(bounds[0] == 0.0);
    REQUIRE(bounds[1] == 0.0);
    REQUIRE(bounds[2] == 1.0);
    REQUIRE(bounds[3] == 1.0);
  }
}

TEST(graph_executor_rejects_an_unknown_pass_derived_source_before_dispatch) {
  Renderer renderer;
  auto plan = renderer.compile(kPerlinSource, "forged-derived.dsl");
  auto& snapshot = snapshot_for(plan, "synth/perlin");
  auto& retained = effect_step(plan, "synth/perlin").passes[0];
  const auto forge = [](PassAdmission& admission) {
    for (auto& uniform : admission.uniforms) {
      if (uniform.source == "pass_derived") uniform.source_name = "forged_source";
    }
  };
  forge(snapshot.admissions[0]);
  forge(retained);
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(11U, 7U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::missing_binding);
    REQUIRE(error.detail() == "pass-derived source is unknown or unavailable");
    REQUIRE(error.program_key() == "synth/perlin:perlin");
  }
}

TEST(graph_executor_dispatches_the_authenticated_custom_adapter) {
  Renderer renderer;
  auto plan = renderer.compile(kBitEffectsSource, "bit-effects.dsl");
  const auto& step = effect_step(plan, "classicNoisedeck/bitEffects");
  const auto& admission = snapshot_for(plan, "classicNoisedeck/bitEffects").admissions[0];
  REQUIRE(admission.route_kind == "custom_adapter");
  REQUIRE(admission.canonical_factory == "noisemaker::effects::bind_bit_effects");
  // The selected payload is the custom adapter itself, not the emitted typed
  // symbol retained for provenance.
  const auto* route = authenticate_factory_route(step, admission);
  REQUIRE(route->bind == &noisemaker::effects::bind_bit_effects);
  REQUIRE(route->emitted_factory == "bind_classicNoisedeck_bitEffects_bitEffects");

  // The adapter's six compile defines are plan-owned, never merged into the
  // GLSL uniform ABI, and resolved from their owning parameters.
  REQUIRE(admission.compile_defines.size() == 6U);
  for (const auto& define : admission.compile_defines) {
    REQUIRE(define.source == "custom_adapter");
    REQUIRE(define.cpp_type == "std::int32_t");
    for (const auto& uniform : admission.uniforms) REQUIRE(uniform.name != define.name);
  }

  // Exact dispatch: byte-for-byte equal to the pinned CPU authority.
  auto inputs = options(8U, 5U);
  inputs.seed = 1.0;
  const auto result = renderer.render(plan, inputs);
  REQUIRE(result.width() == 8U);
  REQUIRE(result.height() == 5U);
  REQUIRE(rgba8_sha256(result) ==
          "4c3dd05256d9e721249550e9bd242f8c2212153453e3b47c547b2f39f97808fd");
}

TEST(graph_executor_rejects_a_forged_or_absent_compile_define) {
  const auto expect_rejected = [](auto&& mutate, GraphErrorCode expected) {
    Renderer renderer;
    auto plan = renderer.compile(kBitEffectsSource, "forged-define.dsl");
    mutate(snapshot_for(plan, "classicNoisedeck/bitEffects").admissions[0]);
    mutate(effect_step(plan, "classicNoisedeck/bitEffects").passes[0]);
    reauthenticate(plan);
    auto inputs = options(8U, 5U);
    inputs.seed = 1.0;
    try {
      static_cast<void>(renderer.render(plan, inputs));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == expected);
    }
  };
  // A define with no owning parameter cannot be materialized.
  expect_rejected([](PassAdmission& admission) { admission.compile_defines[0].name = "NO_SUCH_DEFINE"; },
                  GraphErrorCode::missing_binding);
  // A define may never claim a name the uniform ABI already owns; that name
  // has no `define` parameter behind it either.
  expect_rejected([](PassAdmission& admission) { admission.compile_defines[0].name = admission.uniforms[0].name; },
                  GraphErrorCode::missing_binding);
  // Dropping a required define changes the authenticated identity.
  expect_rejected([](PassAdmission& admission) { admission.compile_defines.pop_back(); },
                  GraphErrorCode::unavailable_pass);
}

TEST(graph_executor_rejects_an_incompatible_route_before_binding) {
  // Forge incompatibility on a compatible program so the test never depends on
  // some real program happening to be broken.
  Renderer renderer;
  auto plan = renderer.compile(kPerlinSource, "forged-incompatible.dsl");
  auto& snapshot = snapshot_for(plan, "synth/perlin");
  REQUIRE(snapshot.admissions[0].status == AvailabilityStatus::compatible);
  snapshot.admissions[0].status = AvailabilityStatus::incompatible;
  effect_step(plan, "synth/perlin").passes[0].status = AvailabilityStatus::incompatible;
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
    REQUIRE(error.program_key() == "synth/perlin:perlin");
  }
}

TEST(graph_executor_preflights_before_copying_caller_owned_surfaces) {
  Renderer renderer;
  ExecutionInputs inputs = options(5U, 3U);
  inputs.seed_surfaces.push_back({"o0", patterned_seed(512U, 512U)});
  // One arena copy of this seed is 512 * 512 * 4 floats.
  constexpr std::size_t kSeedCopyBytes = 512U * 512U * 4U * sizeof(float);

  auto rejected = renderer.compile(kSeededBlurSource, "preflight-order.dsl");
  snapshot_for(rejected, "filter/blur").admissions[0].canonical_factory = "bind_synth_solid";
  effect_step(rejected, "filter/blur").passes[0].canonical_factory = "bind_synth_solid";
  reauthenticate(rejected);

  GraphExecutor executor;
  g_allocated_bytes = 0;
  g_counting_allocations = true;
  bool threw = false;
  try {
    static_cast<void>(executor.execute(rejected, inputs));
  } catch (const GraphError& error) {
    threw = error.code() == GraphErrorCode::unavailable_pass;
  }
  g_counting_allocations = false;
  const std::size_t rejected_bytes = g_allocated_bytes;
  REQUIRE(threw);
#if NOISEMAKER_TEST_COUNTS_ALLOCATIONS
  REQUIRE(rejected_bytes < kSeedCopyBytes);
#endif
  // The caller keeps its own surface: nothing was moved out of the inputs.
  REQUIRE(inputs.seed_surfaces.size() == 1U);
  REQUIRE(inputs.seed_surfaces[0].surface.width() == 512U);

  // Control: the same inputs through an accepted plan must allocate at least
  // one seed copy, proving the accounting above observes the copy it denies.
  const auto accepted = renderer.compile(kSeededBlurSource, "preflight-control.dsl");
  g_allocated_bytes = 0;
  g_counting_allocations = true;
  const auto result = executor.execute(accepted, inputs);
  g_counting_allocations = false;
  REQUIRE(result.surface.width() == 5U);
#if NOISEMAKER_TEST_COUNTS_ALLOCATIONS
  REQUIRE(g_allocated_bytes >= kSeedCopyBytes);
  REQUIRE(rejected_bytes < g_allocated_bytes);
#else
  static_cast<void>(rejected_bytes);
  static_cast<void>(kSeedCopyBytes);
#endif
}

TEST(graph_generic_uniform_materializer_supports_all_value_owned_abi_shapes) {
  std::vector<PlanValue> remap;
  remap.reserve(275U);
  for (std::size_t index = 0; index < 275U; ++index) {
    remap.push_back(PlanValue::array_value({
        PlanValue::number_value(static_cast<double>(index)),
        PlanValue::number_value(1.0), PlanValue::number_value(2.0),
        PlanValue::number_value(3.0)}));
  }
  effects::EffectDefinition definition;
  effects::PassDefinition pass;
  pass.name = "render";
  pass.program = "render";
  pass.outputs = {{"fragColor", "outputTex"}};
  definition.passes.push_back(pass);

  PassAdmission admission;
  admission.status = AvailabilityStatus::compatible;
  admission.identity = {0U, "render", "synth/test:render"};
  admission.dimensionality = "image";
  admission.draw_mode = "fragment";
  admission.outputs.push_back({0U, "fragColor", "outputTex", "glsl::Vec4"});
  admission.authority_pass.name = "render";
  admission.authority_pass.outputs = {{"fragColor", "outputTex"}};
  admission.uniforms = {
      {"flag", "bool", "effect_parameter", "flag", {}, "bool"},
      {"count", "int", "effect_parameter", "count", {}, "std::int32_t"},
      {"offset", "ivec2", "effect_parameter", "offset", {}, "glsl::IVec2"},
      {"direction", "vec4", "effect_parameter", "direction", {}, "glsl::Vec4"},
      {"data", "vec4[275]", "effect_parameter", "data", {}, "vec4[275]"},
  };

  EffectStep step;
  step.effect = {"synth/test", "image", "generator"};
  step.params = {
      {"flag", PlanValue::boolean_value(true)},
      {"count", PlanValue::number_value(-3.0)},
      {"offset", PlanValue::array_value({PlanValue::number_value(7.0), PlanValue::number_value(-2.0)})},
      {"direction", PlanValue::array_value({PlanValue::number_value(0.1), PlanValue::number_value(0.2), PlanValue::number_value(0.3), PlanValue::number_value(0.4)})},
      {"data", PlanValue::array_value(std::move(remap))},
  };

  const auto inputs = options(7U, 5U);
  const BindingMaterializationContext context{&inputs, &definition, 7U, 5U};
  preflight_pass_abi(step, admission, pass, context);
  const auto bindings = materialize_uniform_bindings(step, admission, pass, context);
  REQUIRE(bindings.get<bool>("flag"));
  REQUIRE(bindings.get<std::int32_t>("count") == -3);
  REQUIRE(bindings.get<glsl::IVec2>("offset")[0] == 7);
  REQUIRE(bindings.get<glsl::Vec4>("direction")[3] == noisemaker::f32(0.4));
  REQUIRE(bindings.get<glsl::RemapUniformData>("data").data[274][0] == noisemaker::f32(274.0));

  // A uniform must never carry a sampler's resource route, and a duplicate
  // ABI name is rejected before any value is bound.
  auto forged = admission;
  forged.uniforms[0].resource = "inputTex";
  try {
    preflight_pass_abi(step, forged, pass, context);
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::missing_binding);
    REQUIRE(error.detail() == "uniform ABI must not declare a resource route");
  }
  forged = admission;
  forged.uniforms[1].name = forged.uniforms[0].name;
  try {
    preflight_pass_abi(step, forged, pass, context);
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::missing_binding);
    REQUIRE(error.detail() == "duplicate uniform ABI binding name");
  }
}

TEST(graph_executor_binds_the_render_seed_over_a_defaulted_effect_seed) {
  // The authority's effectParams(): a step that owns a `seed` parameter it did
  // not name explicitly takes the render seed. Two render seeds must therefore
  // produce different bytes, and each must equal the authority exactly.
  Renderer renderer;
  const auto zero = renderer.render(kPerlinSource, options(8U, 8U), "perlin.dsl");
  auto seeded_options = options(8U, 8U);
  seeded_options.seed = 17.0;
  const auto seventeen = renderer.render(kPerlinSource, seeded_options, "perlin.dsl");
  auto zero_options = options(8U, 8U);
  zero_options.seed = 0.0;
  const auto explicit_zero = renderer.render(kPerlinSource, zero_options, "perlin.dsl");

  REQUIRE(rgba8_sha256(seventeen) !=
          rgba8_sha256(explicit_zero));
  REQUIRE(rgba8_sha256(explicit_zero) ==
          "b14b742e1cbfa926a13ef7190f4cd3760e47711b0e36f9c2ae907a08106672d3");
  REQUIRE(rgba8_sha256(seventeen) ==
          "63e9783ccd4685694267d430306c5ed00cc9c61b2906037c91d5246a682e6f57");
  static_cast<void>(zero);

  // An explicitly named seed keeps its own value at every render seed.
  const auto explicit_source =
      "search synth\nperlin(seed: 5).write(o0)\nrender(o0)\n";
  const auto pinned = renderer.render(explicit_source, options(8U, 8U), "perlin-explicit.dsl");
  const auto pinned_other = renderer.render(explicit_source, seeded_options, "perlin-explicit.dsl");
  REQUIRE(rgba8_sha256(pinned) == rgba8_sha256(pinned_other));
}

TEST(graph_executor_publishes_a_bound_zone_surface_into_the_remap_block) {
  // A bound zone surface publishes its color-mode flag through the generic
  // bound_uniform_value() mechanism, so `zone0_active` reads 1 (bound) while
  // `zone1_active` -- never bound, since zoneCount: 1 -- reads the authority's
  // unbound default of 0. This is the native end-to-end proof: the rendered
  // bytes are compared against a hash captured directly from the JS
  // authority (node tools/benchmark/run_cpu_case.mjs against
  // .nm-cpp-work/authority/61aa869) for this exact source/options, not
  // assumed equal to any prior kernel's output.
  Renderer renderer;
  const auto source =
      "search synth\n"
      "solid(color: #f00).write(o1)\n"
      "remap(zoneCount: 1, zone0_tex: o1).write(o0)\n"
      "render(o0)\n";
  auto plan = renderer.compile(source, "remap-zone.dsl");
  auto inputs = options(6U, 4U);
  inputs.seed = 3.0;
  const auto bindings = bind_compiled_pass(plan, "synth/remap", 0U, inputs, 6U, 4U);
  REQUIRE(bindings.get_or<double>("zone0_active", -1.0) == 1.0);
  REQUIRE(bindings.get_or<double>("zone1_active", -1.0) == 0.0);
  REQUIRE(rgba8_sha256(renderer.render(plan, inputs)) ==
          "8a9c935c59f4b61cd6baaf7cb0413e1e0671418073528aefde032fd5078bba45");
}

TEST(graph_executor_rejects_every_forged_component_of_the_ordered_binding_abi) {
  const auto expect_rejected = [](auto&& mutate, GraphErrorCode expected,
                                  std::string_view detail) {
    Renderer renderer;
    auto plan = renderer.compile(kHighPassSource, "forged-binding-abi.dsl");
    mutate(snapshot_for(plan, "filter/highPass").admissions[2]);
    mutate(effect_step(plan, "filter/highPass").passes[2]);
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(9U, 6U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == expected);
      REQUIRE(error.detail() == detail);
    }
  };
  // Each of the five ordered-ABI components is anchored to the generated route
  // table and reports its own code and detail.
  expect_rejected([](PassAdmission& admission) {
        std::swap(admission.samplers[0], admission.samplers[1]);
      }, GraphErrorCode::missing_binding,
      "ordered sampler ABI differs from the generated route anchor");
  expect_rejected([](PassAdmission& admission) {
        std::swap(admission.uniforms[0], admission.uniforms[1]);
      }, GraphErrorCode::binding_type,
      "ordered uniform ABI differs from the generated route anchor");
  expect_rejected([](PassAdmission& admission) {
        admission.outputs[0].physical_name = "forgedColor";
      }, GraphErrorCode::invalid_snapshot,
      "pass output ABI differs from owned definition");
  expect_rejected([](PassAdmission& admission) {
        admission.output_extent.format = "rgba8unorm";
      }, GraphErrorCode::invalid_format,
      "output extent differs from the generated route anchor");
  expect_rejected([](PassAdmission& admission) {
        admission.compile_defines.push_back(
            {"FORGED", {}, "custom_adapter", {}, {}, "std::int32_t"});
      }, GraphErrorCode::binding_type,
      "compile defines are only valid for a custom adapter route");

  // The sampler anchor also fires on its own when the owned pass definition is
  // forged in step with the admission, so the route check is not the only
  // thing standing behind sampler order.
  {
    Renderer renderer;
    auto plan = renderer.compile(kHighPassSource, "forged-sampler-anchor.dsl");
    const auto forge = [](PassAdmission& admission) {
      std::swap(admission.samplers[0], admission.samplers[1]);
    };
    auto& snapshot = snapshot_for(plan, "filter/highPass");
    forge(snapshot.admissions[2]);
    forge(effect_step(plan, "filter/highPass").passes[2]);
    std::swap(snapshot.definition.passes[2].inputs[0],
              snapshot.definition.passes[2].inputs[1]);
    std::swap(snapshot.admissions[2].authority_pass.inputs[0],
              snapshot.admissions[2].authority_pass.inputs[1]);
    std::swap(effect_step(plan, "filter/highPass").passes[2].authority_pass.inputs[0],
              effect_step(plan, "filter/highPass").passes[2].authority_pass.inputs[1]);
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(9U, 6U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::missing_binding);
      REQUIRE(error.detail() ==
              "ordered sampler ABI differs from the generated route anchor");
    }
  }

  // The plan's own registry-derived digest is a projection cross-check with a
  // distinct detail of its own.
  {
    Renderer renderer;
    auto plan = renderer.compile(kHighPassSource, "forged-projection-digest.dsl");
    snapshot_for(plan, "filter/highPass").admissions[2].binding_abi_sha256 =
        std::string(64U, 'c');
    effect_step(plan, "filter/highPass").passes[2].binding_abi_sha256 =
        std::string(64U, 'c');
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(9U, 6U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::invalid_snapshot);
      REQUIRE(error.detail() ==
              "admission binding ABI digest differs from its own ordered ABI");
    }
  }
}

TEST(graph_executor_requires_the_authenticated_output_extent_format) {
  // A forged destination format changes the quantization of every published
  // byte. Forging the owned texture leaves the authenticated digest intact,
  // so the extent cross-check is what rejects it.
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth, filter\n"
      "solid(color: #3a7).blur(radiusX: 3, radiusY: 2).write(o0)\n"
      "render(o0)\n",
      "forged-extent-format.dsl");
  auto& snapshot = snapshot_for(plan, "filter/blur");
  REQUIRE(snapshot.admissions[0].output_extent.format == "rgba8unorm");
  for (auto& texture : snapshot.definition.textures) {
    if (texture.name == "_blurTemp") texture.format = std::string("rgba16f");
  }
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::invalid_format);
    REQUIRE(error.detail() ==
            "destination format differs from the authenticated output extent");
  }
}

TEST(graph_executor_resolves_an_absent_texture_dimension_as_the_render_extent) {
  // filter/reindex declares `statsTiles` with a format and no dimensions.
  // textureDimension() resolves an absent spec to the render extent, and the
  // rendered bytes equal the authority exactly.
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth, filter\n"
      "solid(color: #3a7).reindex().write(o0)\n"
      "render(o0)\n",
      "reindex.dsl");
  const auto& definition = snapshot_for(plan, "filter/reindex").definition;
  const auto stats = std::find_if(
      definition.textures.begin(), definition.textures.end(),
      [](const auto& texture) { return texture.name == "statsTiles"; });
  REQUIRE(stats != definition.textures.end());
  REQUIRE(stats->width.kind == effects::DimensionKind::unknown);
  REQUIRE(stats->width.raw.kind == effects::ValueKind::null_value);

  auto inputs = options(8U, 8U);
  inputs.seed = 1.0;
  REQUIRE(rgba8_sha256(renderer.render(plan, inputs)) ==
          "a00aa40f8749301bc115f5b3ab96bb1ea7110bdb4a0f2947d82af672d29d1a43");
}

TEST(graph_executor_uses_the_declared_dimension_default_without_a_parameter) {
  // CPU 9f3bd6ad: pointsBillboardRender has no stateSize parameter. Its
  // depthOrderA/B textures still resolve `{param: stateSize, default: 256}`.
  Renderer renderer;
  const auto source =
      "search points, render, synth\n"
      "solid().pointsEmit(stateSize: x64).pointsBillboardRender("
      "shapeMode: 1, tex: none, blendMode: 0, depositOpacity: 20, "
      "pointSize: 8, sizeVariation: 0, rotationVar: 0, seed: 42, "
      "density: 50, intensity: 75, inputIntensity: 10.15, viewMode: 0, "
      "rotateX: 0.3, rotateY: 0, rotateZ: 0, viewScale: 0.8, "
      "posX: 0, posY: 0, posZ: 0, fieldOfView: 60, sizeDistance: 0, "
      "brightnessDistance: 0, aperture: 0, focalDistance: 80, "
      "iterationCount: 60).write(o0)\n"
      "render(o0)\n";
  auto inputs = options(17U, 11U);
  inputs.seed = 3696838460.0;
  const auto result = renderer.render(source, inputs);
  REQUIRE(rgba8_sha256(result) ==
          "557f6ae7d848327edca5df66c4642f7a4d3a13535c790ac46f1e315e0e71b76f");
  const auto data = result.surface().data();
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                          data.size_bytes())) ==
          "dd82a5e4c154c59e95519a4941f44f324c75c42e3db643665e26ad7ecf06493e");
}

TEST(graph_dimension_catalog_keeps_param_default_distinct_from_default) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search points, render, synth\n"
      "solid().pointsEmit(stateSize: x64).buddhabrot(iterationCount: 0).write(o0)\n"
      "render(o0)\n");
  const auto& definition = snapshot_for(plan, "points/buddhabrot").definition;
  const auto texture = std::find_if(
      definition.textures.begin(), definition.textures.end(),
      [](const auto& item) { return item.name == "global_zState"; });
  REQUIRE(texture != definition.textures.end());
  REQUIRE(texture->width.kind == effects::DimensionKind::parameter_default);
  REQUIRE(texture->height.kind == effects::DimensionKind::parameter_default);
  REQUIRE(texture->width.default_value == 512.0);
  REQUIRE(texture->height.default_value == 512.0);
  REQUIRE(std::any_of(texture->width.raw.object.begin(),
                      texture->width.raw.object.end(),
                      [](const auto& field) {
                        return field.first == "paramDefault" &&
                               field.second.kind == effects::ValueKind::number &&
                               field.second.number == 512.0;
                      }));
}

TEST(graph_executor_renders_authenticated_volume_viewports) {
  // CPU 9f3bd6ad: the precompute MRT has a 4x16 viewport, while the image is
  // 7x5. Palette inherits the input volume size before its pass runs, then
  // render3d projects the 4x16 atlas into the final image.
  struct Case { const char* source; const char* rgba; const char* floats; };
  const Case cases[] = {
      {"search synth3d, render\nshape3d(volumeSize: 4).render3d().write(o0)\nrender(o0)\n",
       "27a0f6ab7ea6dfff9099d2ce508baae7c5d55c265457d6a122fdb78020ef3675",
       "c869cd037f7c578caa15939c5631aff1bcf6587002533558d5365bd0d8c04ccd"},
      {"search synth3d, filter3d, render\nshape3d(volumeSize: 4).palette3d(volumeSize: 8).render3d().write(o0)\nrender(o0)\n",
       "6c6f1c863baaa7d73fae9604b1f6306dfa4f08393348b5e47f8f49746b7be89d",
       "3b0d2babb4623c4edad5284c124cc4eb408423a7495d6275a5f88de6ec29996f"},
      {"search synth3d, filter3d, render\nshape3d(volumeSize: 4).flow3d(iterationCount: 1, density: 1).render3d().write(o0)\nrender(o0)\n",
       "c749db6f8e235e0d5945474a7a4ab70e395c9072aeedc9f8fa4fbac2b3b699b7",
       "ae14df9704171b72f7fa0977ad75ba72c736bd1670a2b8a5af2cc440f5d9a483"},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    const auto result = renderer.render(item.source, options(7U, 5U));
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                            data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_repeats_animated_noise_for_each_flow_tick) {
  // Fresh CPU 5fd2194 capture; its smoke test pins the same RGBA8 bytes.
  Renderer renderer;
  const auto source =
      "search synth3d, filter3d, render\n"
      "noise3d(seed: 0, volumeSize: x32).flow3d(iterationCount: 2).render3d().write(o0)\n"
      "render(o0)\n";
  auto inputs = options(8U, 8U);
  inputs.seed = 1.0;
  inputs.time = 0.15333333333333332;
  const auto result = renderer.render(source, inputs);
  REQUIRE(rgba8_sha256(result) ==
          "0165ffddf3120854c80c0e36e8446253a00733b776ff45a5ecd004bd408e5fb1");
  const auto data = result.surface().data();
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                          data.size_bytes())) ==
          "765d50a6bdb2a159bd302efd0affbe8f6680cf33e72d7435b096519837b0525d");
}

TEST(graph_executor_preserves_double_cubemap_basis_uniforms) {
  // CPU 7f47340 retains the nine parameter values until the completed ray is
  // stored as float32. Rounding the matrix first changes one rgba16f step.
  constexpr const char* source =
      "search synth3d, filter3d, render\n"
      "noise3d(volumeSize: 64).renderCubemapSurface(volumeSize: 32, "
      "density: 20, absorption: 4, emission: 4, "
      "cubeBasis: [-1.5097436419112655, 0.8338904725453848, "
      "0.8030976313762073, 0.5783815168611464, 1.2226387625875654, "
      "0.8235589957020275, 0.4221211688745119, 0.8229414908629156, "
      "3.9163901307685807], bgColor: #b9fb5e9f, bgAlpha: 1).write(o0)\n"
      "render(o0)\n";
  auto render_options = options(128U, 40U);
  render_options.time = 0.0;
  render_options.seed = 3897427244.0;
  Renderer renderer;
  const auto result = renderer.render(source, render_options);
  const auto data = result.surface().data();
  REQUIRE(data[(22U * 128U + 106U) * 4U + 0U] == 1.8583984375F);
  REQUIRE(detail::sha256(std::string_view(
              reinterpret_cast<const char*>(data.data()), data.size_bytes())) ==
          "913a4ea2e52a6b65d14e34e086cfbb0147403e784f901329be0adba74b54ff94");
  REQUIRE(rgba8_sha256(result) ==
          "1f55ffcddc1fce4d4ab43d09da1f8e58730a19bf3aadd78331c3eaaa8b9b4410");
}

TEST(graph_executor_preserves_hatch_stroke_scale_float32_boundary) {
  // CPU4307 stores the reciprocal stroke scale in a Float32Array before
  // multiplication. These two captures differ only in float32, not RGBA8.
  struct Case {
    unsigned width;
    unsigned height;
    double seed;
    const char* rgba;
    const char* floats;
  };
  const Case cases[] = {
      {64U, 64U, 722341297.0,
       "8a0aad0d586a53893bfc9e8fe003ebf1992205ac9c976a155502a95137978128",
       "713b504f89da8082a0cd0dff314d4297997a6f9ae590e3f0a48b33fc5f683260"},
      {97U, 61U, 654448771.0,
       "dcb3330d427bb10aef511c6f8fd7b22a72248e850689935012d3d2a3100b733c",
       "c33ab452cd658be2ea8b20ce3bdd6a0d5327389eed75370bcc58bc11d43a7896"},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    auto render_options = options(item.width, item.height);
    render_options.time = 0.999;
    render_options.seed = item.seed;
    const auto result = renderer.render(
        "search filter, synth\n"
        "noise(seed: 7).hatch(mode: 4, strokeLength: 50, direction: 0, "
        "balance: 50, pressure: 50, inkColor: #1a1a1a, paperColor: #f5f0e0)"
        ".write(o0)\nrender(o0)\n", render_options);
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(
                reinterpret_cast<const char*>(data.data()), data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_preserves_gradient_rotation_value_copy) {
  // CPU4307 copies centered before the two rotation stores. These captures
  // cover a float32-only mismatch, a spiral mismatch, and a downstream chain.
  struct Case {
    const char* source;
    unsigned width;
    unsigned height;
    double time;
    double seed;
    const char* rgba;
    const char* floats;
  };
  const Case cases[] = {
      {"search synth\n"
       "gradient(type: 4, rotation: -180, repeat: 1, speed: -5, seed: 0, "
       "color1: #7102eb54, color2: #634ae781, color3: #44e0f68d, "
       "color4: #823b8ffe, colorCount: 2).write(o0)\nrender(o0)\n",
       128U, 37U, 0.25, 1577027250.0,
       "365c0f10a46ab79cb969c461dc27f6a5e0b81b7a4824326a5c47a795681d44e9",
       "90fbf0009700b37a97c10c9171e0ec98cf74c813873ad370a2df550d1f1ba636"},
      {"search synth\n"
       "gradient(type: 6, rotation: -93.20992920816589, repeat: 1, speed: -5, "
       "seed: 74, color1: #c82b5ff6, color2: #c8c3dcf7, color3: #4f42c03b, "
       "color4: #011860e2, colorCount: 4).write(o0)\nrender(o0)\n",
       17U, 11U, 0.0, 4277095002.0,
       "20dc4b476cd5b34891f7a1fb28a3a966a7bb96d44ad55b1487d3d8721e7eaeae",
       "071d1306b97eb8d7599689e862ff7b7a13f1fd35b7c67fbfbcac5e784c5382f3"},
      {"search synth, filter\n"
       "gradient(type: 0, rotation: -180, repeat: 1, speed: -5, seed: 0, "
       "color1: #c6420c80, color2: #599d3b80, color3: #259af780, "
       "color4: #a6fc2b80, colorCount: 2).lightLeak(alpha: 1, color: #ffcc4c, "
       "speed: 0.5, seed: 1).scratches(density: 0.3, alpha: 0.75, seed: 1)"
       ".write(o0)\nrender(o0)\n",
       97U, 61U, 0.999, 2082350962.0,
       "ff8d6917d28a95463a58b91ba4d9c8c758a6c1fee6aa6266ec7d6bb62cfa513c",
       "040320f4f162c52bb84cbaf48e7f035d18299f583c53c52613fc61c5a7c6e751"},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    auto render_options = options(item.width, item.height);
    render_options.time = item.time;
    render_options.seed = item.seed;
    const auto result = renderer.render(item.source, render_options);
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(
                reinterpret_cast<const char*>(data.data()), data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_preserves_iterated_image_volume_and_geometry_bundle) {
  // CPU4307 carries each bundle component through every step in a loop.
  // The second palette pass reads the volume after an image renderer.
  struct Case {
    const char* middle;
    const char* rgba;
    const char* floats;
    std::array<std::size_t, 2> pass_counts;
  };
  const Case cases[] = {
      {"palette3d(volumeSize: 4).render3d().palette3d(volumeSize: 4).render3d()",
       "036080b5744697b71018f1b98f11c47bf83f1cb6fd255f1a36d0962a778d9a72",
       "639f94a948d2c2638445cc30fba54006025a874fd471c0d9457904690b562ce0",
       {9U, 16U}},
      {"palette3d(volumeSize: 4).render3d().renderLit3d()",
       "b9bbf0365eba2e2d2d0db4e51a8a341968dd32a7297a6fe44665ad6e2b43e5f5",
       "9c85fe78121718c668cf78bcf3e83d694be6817a4a77fa09e08c259deba3adb4",
       {8U, 14U}},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    for (const unsigned count : {1U, 2U}) {
      const std::string source =
          "search synth3d, filter3d, render\n"
          "shape3d(volumeSize: 4).render3d().loopBegin(iterationCount: " +
          std::to_string(count) + ")." + item.middle +
          ".loopEnd().write(o0)\nrender(o0)\n";
      auto render_options = options(8U, 8U);
      render_options.time = 0.2;
      render_options.seed = 1.0;
      const auto result = renderer.render(source, render_options);
      REQUIRE(result.pass_count() == item.pass_counts[count - 1U]);
      REQUIRE(rgba8_sha256(result) == item.rgba);
      const auto data = result.surface().data();
      REQUIRE(detail::sha256(std::string_view(
                  reinterpret_cast<const char*>(data.data()), data.size_bytes())) ==
              item.floats);
    }
  }
}

TEST(graph_executor_zero_iteration_volume_group_preserves_input_bundle) {
  Renderer renderer;
  const auto base = renderer.render(
      "search synth3d, render\nshape3d(volumeSize: 4).render3d().write(o0)\nrender(o0)\n",
      options(7U, 5U));
  const auto skipped = renderer.render(
      "search synth3d, filter3d, render\n"
      "shape3d(volumeSize: 4).flow3d(iterationCount: 0).render3d().write(o0)\n"
      "render(o0)\n", options(7U, 5U));
  REQUIRE(rgba8_sha256(skipped) == rgba8_sha256(base));
  const auto left = base.surface().data();
  const auto right = skipped.surface().data();
  REQUIRE(left.size() == right.size());
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(left.data()),
                                          left.size_bytes())) ==
          detail::sha256(std::string_view(reinterpret_cast<const char*>(right.data()),
                                          right.size_bytes())));
}

TEST(graph_executor_zero_iteration_volume_generator_creates_cleared_bundle) {
  // CPU 9f3bd6ad zeroIterationGroupOutput creates a clear volume and geometry
  // atlas when a volume generator opens the chain and its count is zero.
  Renderer renderer;
  const auto result = renderer.render(
      "search synth3d, render\n"
      "reactionDiffusion3d(volumeSize: 4, iterationCount: 0).render3d().write(o0)\n"
      "render(o0)\n", options(7U, 5U));
  REQUIRE(rgba8_sha256(result) ==
          "fb9ae3e76f54906621ab2db14e1c374a9657257ffcf0eadfd274b00133dfc7f5");
  const auto data = result.surface().data();
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                          data.size_bytes())) ==
          "d594ae252c2273b1eccbcb14f5c0e50770cfdf9795220b54637ee0251ecbc046");
}

TEST(graph_executor_seeds_typed_volume_and_geometry_parameters) {
  // CPU9f3 renderer.js seedTypedChainResources binds an incoming bundle or
  // clears outputTex3d/outputGeo-sized surfaces.  `vol0` and `geo0` are
  // parameter metadata, not named arena dependencies.
  struct Case { const char* effect; bool incoming; const char* rgba; const char* floats; };
  const std::array<Case, 4> cases{{
      {"cellularAutomata3d", false,
       "23f4d15b5cb703a983c2e98031a395cc5704fb39197e815ef61352605ccc0409",
       "83e559adef6088bcbea5e5ca3eb8f9abf034fb8d5d3521502fb30e925237524d"},
      {"reactionDiffusion3d", false,
       "0e0a054c6eb854f9dada108c81bf59bfc294be51bc7fb2a6bca851de40cf9151",
       "11d2ffc713fc9923fb1ea43160e1c15e63a0945e667374248f1559ac7e200e08"},
      {"cellularAutomata3d", true,
       "8338daf7f3a8b05f11fbdbd33cbf61a5c1e84f636e85bf5902687a18a56d170a",
       "3e8aff2f05fd066ef5309f40028dab4be871c9fbd6a032bb8beb434af111c2cc"},
      {"reactionDiffusion3d", true,
       "8338daf7f3a8b05f11fbdbd33cbf61a5c1e84f636e85bf5902687a18a56d170a",
       "76ca10250b1e05ac90ad5fa3134c4b30317e907dd3566d8a57bc455a1cb30121"},
  }};
  Renderer renderer;
  for (const auto& item : cases) {
    const std::string source = "search synth3d, render\n" +
        std::string(item.incoming ? "shape3d(volumeSize: 4)." : "") + item.effect +
        "(volumeSize: 4, source: vol0, geoSource: geo0, iterationCount: 1)"
        ".render3d().write(o0)\nrender(o0)\n";
    const auto result = renderer.render(source, options(5U, 3U));
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                            data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_rejects_unseedable_typed_route_and_unknown_route) {
  Renderer renderer;
  constexpr std::string_view source =
      "search synth3d, render\n"
      "cellularAutomata3d(volumeSize: 4, source: vol0, geoSource: geo0, "
      "iterationCount: 1).render3d().write(o0)\nrender(o0)\n";
  enum class Mutation { missing_volume, missing_geometry, unknown_route };
  for (const Mutation mutation : {Mutation::missing_volume,
                                  Mutation::missing_geometry,
                                  Mutation::unknown_route}) {
    auto plan = renderer.compile(source);
    auto& snapshot = snapshot_for(plan, "synth3d/cellularAutomata3d");
    if (mutation != Mutation::unknown_route) {
      // No incoming bundle and no declared output texture can seed `source`
      // or `geoSource`. The latter is not read by this effect's pass.
      const auto& output_name = mutation == Mutation::missing_volume
          ? snapshot.definition.output_tex3d : snapshot.definition.output_geo;
      snapshot.definition.textures.erase(
          std::remove_if(snapshot.definition.textures.begin(),
                         snapshot.definition.textures.end(),
                         [&](const auto& texture) {
                           return output_name.has_value() &&
                                  texture.name == *output_name;
                         }), snapshot.definition.textures.end());
    } else {
      // An undeclared route must not inherit the typed-parameter exemption.
      snapshot.definition.passes.front().inputs.back().second = "unknownTypedRoute";
    }
    reauthenticate(plan);
    ExecutionInputs inputs = options(5U, 3U);
    inputs.seed_surfaces.push_back({"o0", patterned_seed(512U, 512U)});
#if NOISEMAKER_TEST_COUNTS_ALLOCATIONS
    constexpr std::size_t kSeedCopyBytes = 512U * 512U * 4U * sizeof(float);
#endif
    GraphExecutor executor;
    g_allocated_bytes = 0;
    g_counting_allocations = true;
    bool refused = false;
    try {
      static_cast<void>(executor.execute(plan, inputs));
    } catch (const GraphError& error) {
      // Both removed textures reach the all-parameter seed preflight.
      // The forged pass route must fail the admitted pass identity first.
      refused = mutation != Mutation::unknown_route
          ? error.code() == GraphErrorCode::read_before_write &&
            error.detail() == "typed input has no seeded resource"
          : error.code() == GraphErrorCode::invalid_snapshot &&
            error.detail() == "pass routing differs from admitted ABI";
    }
    g_counting_allocations = false;
    REQUIRE(refused);
#if NOISEMAKER_TEST_COUNTS_ALLOCATIONS
    REQUIRE(g_allocated_bytes < kSeedCopyBytes);
#endif
  }
}

TEST(graph_executor_navier_stokes_default_matches_cpu9f3_hash_order) {
  // CPU 7f47340 canonicalFactory271 reads both hash22 lanes from the input
  // vector before it stores either lane. This full effect witnesses the
  // seeded state.
  Renderer renderer;
  const auto result = renderer.render(
      "search synth\n"
      "navierStokes(tex: none, zoom: 1, iterations: 30, smoothing: 1, "
      "speed: 100, dyeDecay: 98, velocityDecay: 99, inputForce: 0.5, "
      "inputDye: 0.9, inputIntensity: 10, resetState: false, seed: 1, "
      "iterationCount: 60).write(o0)\nrender(o0)\n",
      options(17U, 11U));
  REQUIRE(rgba8_sha256(result) ==
          "3a30c53de177c1087d58f6559fab4296b0d618e7888b2809953c8596d25e2746");
  const auto data = result.surface().data();
  REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                          data.size_bytes())) ==
          "4c4c49dfaae4a0fe155df1852ab1504eacd486e132c1fef3a2582c4d2d53966c");
}

TEST(graph_executor_rejects_volume_from_an_earlier_chain) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth3d, render\n"
      "shape3d(volumeSize: 4).render3d().write(o0)\n"
      "shape3d(volumeSize: 4).render3d().write(o1)\n"
      "render(o1)\n");
  REQUIRE(plan.chains.size() == 2U);
  REQUIRE(plan.chains[1].steps.size() == 3U);
  const auto* producer = std::get_if<EffectStep>(&plan.chains[1].steps.front());
  REQUIRE(producer != nullptr);
  REQUIRE(producer->effect.id == "synth3d/shape3d");
  plan.chains[1].steps.erase(plan.chains[1].steps.begin());
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::read_before_write);
    REQUIRE(error.detail() == "input bundle resource is not produced");
  }
}

TEST(graph_executor_rejects_removed_or_forged_admitted_viewport) {
  for (const bool omit : {false, true}) {
    Renderer renderer;
    auto plan = renderer.compile(
        "search synth3d, render\nshape3d(volumeSize: 4).render3d().write(o0)\nrender(o0)\n");
    auto& snapshot = snapshot_for(plan, "synth3d/shape3d");
    REQUIRE(snapshot.admissions.front().authority_pass.viewport.has_value());
    const auto mutate = [&](auto& admission) {
      if (omit) admission.authority_pass.viewport.reset();
      else admission.authority_pass.viewport = effects::Value::object_value({
          {"width", effects::Value::number_value(7.0)},
          {"height", effects::Value::number_value(5.0)}});
    };
    mutate(snapshot.admissions.front());
    mutate(effect_step(plan, "synth3d/shape3d").passes.front());
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(7U, 5U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::invalid_snapshot);
      REQUIRE(error.detail() == "pass routing differs from admitted ABI");
    }
  }
}

TEST(graph_executor_rejects_paired_viewport_forgery_before_allocation) {
  for (const bool iterated : {false, true}) {
    Renderer renderer;
    auto plan = renderer.compile(kSolidSource, "forged-paired-viewport.dsl");
    auto& snapshot = snapshot_for(plan, "synth/solid");
    snapshot.definition.iterated = iterated;
    const auto viewport = effects::Value::object_value({
        {"width", effects::Value::number_value(3.0)},
        {"height", effects::Value::number_value(2.0)}});
    snapshot.definition.passes.front().viewport = viewport;
    snapshot.admissions.front().authority_pass.viewport = viewport;
    effect_step(plan, "synth/solid").passes.front().authority_pass.viewport = viewport;
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(7U, 5U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::invalid_snapshot);
      REQUIRE(error.detail() == "viewport differs from the generated catalog anchor");
    }
  }
  // Removing an authentic viewport from both copies must also fail closed.
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth3d, render\nshape3d(volumeSize: 4).render3d().write(o0)\nrender(o0)\n");
  auto& snapshot = snapshot_for(plan, "synth3d/shape3d");
  snapshot.definition.passes.front().viewport.reset();
  snapshot.admissions.front().authority_pass.viewport.reset();
  effect_step(plan, "synth3d/shape3d").passes.front().authority_pass.viewport.reset();
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::invalid_snapshot);
    REQUIRE(error.detail() == "viewport differs from the generated catalog anchor");
  }
}

TEST(graph_executor_rejects_forged_flow3d_draw_count) {
  Renderer renderer;
  auto plan = renderer.compile(
      "search synth3d, filter3d, render\nshape3d(volumeSize: 4).flow3d(iterationCount: 1, density: 1).render3d().write(o0)\nrender(o0)\n");
  auto& snapshot = snapshot_for(plan, "filter3d/flow3d");
  const auto pass = std::find_if(snapshot.definition.passes.begin(), snapshot.definition.passes.end(),
                                [](const auto& item) { return item.name == "deposit"; });
  REQUIRE(pass != snapshot.definition.passes.end());
  REQUIRE(pass->count.has_value());
  REQUIRE(pass->count->kind == effects::ValueKind::number);
  pass->count = effects::Value::number_value(1.0);
  reauthenticate(plan);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::invalid_snapshot);
    REQUIRE(error.detail() == "scatter pass count differs from the admitted contract");
  }
}

TEST(graph_executor_renders_the_canonical_worm_overlay_effects_byte_exact) {
  // `overlayTex` on these three effects is fed by a dedicated CPU adapter
  // (noisemaker::effects::cpu::render_canonical_worm_overlay, ported from
  // src/effects/cpu/worm-overlay.js -- see
  // docs/port-engineering/worm-overlay-parity/ for the oracle and mutation
  // evidence). None of these DSL calls names `seed` explicitly, so the
  // authority's `effectParams()` substitutes the render-level seed
  // (`options(8,8)`'s seed of 17.0) for the effect's own declared default --
  // these pinned hashes were captured from the live JS authority under that
  // exact substitution, not the effect's own seed:1 default.
  struct Case { const char* effect; const char* sha256; };
  const Case cases[] = {
      {"scratches", "9050e3f7cec6503fc0f4ec24f906764b625b5262eeb5f3685ae3026cbff4010d"},
      {"strayHair", "945bd0bc9cfb10d7105e111817c2f2a254536b0eaa19037630a6124bb975c03c"},
      {"fibers", "a00aa40f8749301bc115f5b3ab96bb1ea7110bdb4a0f2947d82af672d29d1a43"},
  };
  for (const auto& kase : cases) {
    Renderer renderer;
    const std::string source = std::string("search synth, filter\n") +
                               "solid(color: #3a7)." + kase.effect + "().write(o0)\n" +
                               "render(o0)\n";
    const auto result = renderer.render(source, options(8U, 8U), "worm.dsl");
    REQUIRE(rgba8_sha256(result) == kase.sha256);
  }
}

TEST(graph_executor_worm_overlay_explicit_seed_bypasses_the_render_seed_substitution) {
  // With `seed` named explicitly in the DSL call, `effectParams()` must NOT
  // substitute the render-level seed -- the effect's own explicit value
  // (7) is what reaches `renderCanonicalWormOverlay`, so this render must
  // differ from an otherwise-identical unbound-seed render (whose effective
  // seed is 17, the render-level default from `options()`).
  Renderer renderer;
  const std::string explicitSource =
      "search synth, filter\nsolid(color: #3a7).scratches(seed: 7).write(o0)\nrender(o0)\n";
  const std::string defaultSource =
      "search synth, filter\nsolid(color: #3a7).scratches().write(o0)\nrender(o0)\n";
  const auto explicitResult = renderer.render(explicitSource, options(8U, 8U), "worm-explicit.dsl");
  const auto defaultResult = renderer.render(defaultSource, options(8U, 8U), "worm-default.dsl");
  REQUIRE(rgba8_sha256(explicitResult) != rgba8_sha256(defaultResult));
}


TEST(graph_executor_runtime_perlin_and_emboss_defines_match_cpu) {
  // Captured by tests/fixtures/runtime_define_graph_reference.mjs against CPU 7f47340.
  struct Case { const char* source; const char* floats; const char* rgba; };
  const std::array<Case, 4> cases{{
      {"search synth\nperlin(dimensions: 2).write(o0)\nrender(o0)\n", "f96c3fdde5e7da28fe616c0f668e03caeac7ca4b07a10c8c6e218353e897efd7", "63e9783ccd4685694267d430306c5ed00cc9c61b2906037c91d5246a682e6f57"},
      {"search synth\nperlin(dimensions: 3).write(o0)\nrender(o0)\n", "4c9df6444aa8766ea2eb4b848cd25dba549297646c3b99745399748fa6e23cbb", "2e2b34d4314dbd85d72d57727b2ee7c1e663db8570d814b037d32b9dac9f7018"},
      {"search synth, filter\nsolid(color: #3a7).emboss(style: 0).write(o0)\nrender(o0)\n", "bbab47259fa6a1340de8b4d202619b0552481b96b09418e3afd33e0c62c4161e", "a00aa40f8749301bc115f5b3ab96bb1ea7110bdb4a0f2947d82af672d29d1a43"},
      {"search synth, filter\nsolid(color: #3a7).emboss(style: 1).write(o0)\nrender(o0)\n", "843226302196ad6439a199a7fc8f1f258f4f082db30c43ba593483eecdd3be72", "eec68212ac4794baa76cf2d4520d0401aeb7156ee1ee28dabbc0bf0fdec54cb7"},
  }};
  Renderer renderer;
  for (const auto& item : cases) {
    const auto result = renderer.render(item.source, options(8U, 8U), "define.dsl");
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                            data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_honors_runtime_and_adapter_compile_defines_exactly) {
  // Two contracts are unaffected by the authentication above and must stay
  // byte-exact against the authority at a non-default define: `runtime-int`
  // carries its defines as pass_derived uniforms, and a custom adapter binds
  // them as real uniforms.
  Renderer renderer;
  auto inputs = options(8U, 8U);
  REQUIRE(rgba8_sha256(renderer.render(
              "search synth\nnoise(type: 1).write(o0)\nrender(o0)\n", inputs, "noise.dsl")) ==
          "6cf4f87470b72b70cc1dcb32b85875c734bb7f2dcb1c891251a566e112ea6878");
  REQUIRE(rgba8_sha256(renderer.render(
              "search classicNoisedeck\nbitEffects(mode: 2).write(o0)\nrender(o0)\n",
              inputs, "bit.dsl")) ==
          "d7e1f80a6402b56b58d45158bc9286e9b67535cb9b89264edf253b8593ba72d3");
}

TEST(graph_executor_applies_the_ported_classic_noisedeck_palette_override) {
  // buildBindings() overrides a classicNoisedeck effect's palette uniforms
  // from the authority's built-in table whenever the palette parameter
  // selects an entry. That table is now ported
  // (include/noisemaker/graph/generated/classic_noisedeck_palette_table.hpp),
  // so a valid selection dispatches and renders from the table -- it is no
  // longer refused.
  Renderer renderer;
  // Palette entry 0 selects no table entry (unchanged): the plan's own
  // palette uniforms are used, matching `paletteData[paletteIndex - 1]`
  // never being consulted when `paletteIndex <= 0`.
  REQUIRE(renderer.render(
              "search classicNoisedeck\nshapes(palette: 0).write(o0)\nrender(o0)\n",
              options(8U, 8U), "palette.dsl").width() == 8U);
  // Palette entry 46 selects a real table row and must render -- the value
  // is pinned against the JS authority via the corpus/oracle lanes
  // (docs/port-engineering/palette-override/), not re-derived here; this is
  // a regression pin against silent drift.
  REQUIRE(rgba8_sha256(renderer.render(
              "search classicNoisedeck\nshapes(palette: 46).write(o0)\nrender(o0)\n",
              options(8U, 8U), "palette.dsl")) ==
          "c623ebc0ff70a67ac65a43d0fd69bb63ef8a9759f3bdd01d59462d02081318b0");
  // An index a compiled plan could never carry (out of the table's 1..55
  // range, e.g. from a hand-built plan) selects no entry either, exactly
  // like the authority's own out-of-bounds `paletteData[...]` access being
  // `undefined`: the effect still dispatches, from the plan's own uniforms.
  REQUIRE(renderer.render(
              "search classicNoisedeck\nshapes(palette: 0).write(o0)\nrender(o0)\n",
              options(8U, 8U), "palette.dsl").width() == 8U);
}

TEST(graph_executor_classic_shapes3d_palette_override_preserves_binding_carriers) {
  // CPU 9f3bd6ad, 8x8, time 0.25, seed 17. Palette zero retains the
  // caller's vectors; palette 40 replaces them with the canonical table.
  struct Case { const char* source; const char* rgba; const char* floats; };
  const Case cases[] = {
      {"search classicNoisedeck, synth\nsolid(color: #3a7).shapes3d(palette: 0).write(o0)\nrender(o0)\n",
       "83d905af352efe5c4002df073f8261af7e69a5db534e9344c3c08370c36e9663",
       "c295dfd4ef6c8ce513dc68cbd448b1495d0e93f83d4fd47f9fa570054f5e5f73"},
      {"search classicNoisedeck, synth\nsolid(color: #3a7).shapes3d(palette: 40).write(o0)\nrender(o0)\n",
       "2f3a19dc693eba6c025b5aaeda4fbd4b320b4fa6ef27f9f67a5ccd6a7259837d",
       "e3004ea82718aabd624c2b2b52eea832d71dae15ba5bd293f708d8fa26cb470e"},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    auto plan = renderer.compile(item.source, "shapes3d-palette.dsl");
    const auto& admission = snapshot_for(plan, "classicNoisedeck/shapes3d").admissions[0];
    for (const char* name : {"paletteOffset", "paletteAmp", "paletteFreq", "palettePhase"}) {
      const auto uniform = std::find_if(admission.uniforms.begin(), admission.uniforms.end(),
          [name](const auto& binding) { return binding.name == name; });
      REQUIRE(uniform != admission.uniforms.end());
      REQUIRE(uniform->cpp_type == "glsl::DVec3");
    }
    const auto result = renderer.render(plan, options(8U, 8U));
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                           data.size_bytes())) == item.floats);
  }
}

TEST(graph_executor_classic_noise_palette_runtime_preserves_raw_uniforms) {
  // CPU 9f3bd6ad renders the same DSL twice with palette entry 2 and the
  // default 8x8, time 0.25, seed 17 inputs. COLOR_MODE=4 reaches pal();
  // COLOR_MODE=6 keeps the historical HSV path.
  struct Case { const char* source; const char* rgba; const char* floats; };
  const Case cases[] = {
      {"search classicNoisedeck\nnoise(colorMode: palette, palette: 2).write(o0)\nrender(o0)\n",
       "01edf5301fb956cf3da32fe8570b17479da92d5412dd4f12dea8c383782dd123",
       "984801325e1ca56ea03be67baa86b1b78de3b4aae6b6d2bd9541542d4405d0ad"},
      {"search classicNoisedeck\nnoise(colorMode: hsv, palette: 2).write(o0)\nrender(o0)\n",
       "f5b1fd5a140541a8a9291f652e781b7b1e2ff240c42a765754fc2e5d7c1b0e34",
       "9a152ef97fbd7436a9a60017c23c04e42b938f177eb3c339d4b7ae88ce7b5b48"},
  };
  Renderer renderer;
  for (const auto& item : cases) {
    auto plan = renderer.compile(item.source, "classic-noise-palette.dsl");
    const auto& admission = snapshot_for(plan, "classicNoisedeck/noise").admissions[0];
    for (const char* name : {"paletteOffset", "paletteAmp", "paletteFreq", "palettePhase"}) {
      const auto uniform = std::find_if(
          admission.uniforms.begin(), admission.uniforms.end(),
          [name](const auto& binding) { return binding.name == name; });
      REQUIRE(uniform != admission.uniforms.end());
      REQUIRE(uniform->cpp_type == "glsl::DVec3");
    }
    const auto result = renderer.render(plan, options(8U, 8U));
    REQUIRE(rgba8_sha256(result) == item.rgba);
    const auto data = result.surface().data();
    REQUIRE(detail::sha256(std::string_view(reinterpret_cast<const char*>(data.data()),
                                            data.size_bytes())) == item.floats);
  }
  auto forged = renderer.compile(cases[0].source, "forged-classic-noise-palette.dsl");
  const auto narrow_palette = [](PassAdmission& admission) {
    const auto uniform = std::find_if(
        admission.uniforms.begin(), admission.uniforms.end(),
        [](const auto& binding) { return binding.name == "paletteAmp"; });
    REQUIRE(uniform != admission.uniforms.end());
    uniform->cpp_type = "glsl::Vec3";
  };
  narrow_palette(snapshot_for(forged, "classicNoisedeck/noise").admissions[0]);
  narrow_palette(effect_step(forged, "classicNoisedeck/noise").passes[0]);
  reauthenticate(forged);
  try {
    static_cast<void>(renderer.render(forged, options(8U, 8U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::binding_type);
    REQUIRE(error.detail() == "ordered uniform ABI differs from the generated route anchor");
  }
}

TEST(graph_executor_rejects_forged_synth3d_number_seed_abi) {
  Renderer renderer;
  const std::array<std::pair<const char*, const char*>, 2> cases{{
      {"synth3d/noise3d",
       "search synth3d, filter3d, render\n"
       "noise3d(volumeSize: 32).render3d().write(o0)\nrender(o0)\n"},
      {"synth3d/cell3d",
       "search synth3d, filter3d, render\n"
       "cell3d(volumeSize: 64, metric: 0, scale: 10, variation: 100, seed: 1, colorMode: 1).render3d().write(o0)\nrender(o0)\n"},
  }};
  for (const auto& [effect, source] : cases) {
    auto plan = renderer.compile(source, "forged-synth3d-seed.dsl");
    const auto forge = [](PassAdmission& admission) {
      const auto seed = std::find_if(
          admission.uniforms.begin(), admission.uniforms.end(),
          [](const auto& binding) { return binding.name == "seed"; });
      REQUIRE(seed != admission.uniforms.end());
      REQUIRE(seed->type == "int");
      REQUIRE(seed->cpp_type == "double");
      REQUIRE(seed->source == "effect_parameter");
      seed->cpp_type = "std::int32_t";
    };
    forge(snapshot_for(plan, effect).admissions[0]);
    forge(effect_step(plan, effect).passes[0]);
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(8U, 8U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::binding_type);
      REQUIRE(error.detail() == (std::string_view(effect) == "synth3d/noise3d"
              ? "Noise3D seed ABI is not authenticated"
              : "Cell3D seed ABI is not authenticated"));
    }
  }
}

TEST(graph_executor_fails_closed_on_a_measured_parity_exclusion) {
  // Both real entries `kMeasuredParityExclusions` once named --
  // `filter/snow:snow` (a hand-written-adapter mismatch) and
  // `synth/testPattern:testPattern` (a grid-boundary digit-extraction
  // divergence; see tests/test_testpattern_emitter_regression.py and the
  // field comment on `emitted_testpattern_digit_extraction_declarations`
  // in emit_typed_cpp.py) -- are now proven byte-exact and gone, so this
  // test cannot depend on either any more.
  //
  // Forging a *different* compiled program's `identity.program_key` to
  // masquerade as an excluded key, the way
  // graph_executor_rejects_the_incompatible_text_route_before_binding
  // forges `status`, does not work if it goes through `renderer.render()`:
  // that path re-derives `identity.program_key` from the compiled
  // effect/pass definition and cross-checks it
  // (`validate_pass_identity_and_output`) before any binding is attempted,
  // so forging only the admission's copy trips THAT check instead ("pass
  // identity differs from owned definition").
  //
  // `bind_factory_route` (declared in executor.hpp for exactly this kind of
  // seam) sits BELOW that whole-plan check, so this drives it directly: a
  // real, unmodified, successfully-compiled perlin admission/bindings pair
  // (proving every other authenticate_* step it must first pass is
  // satisfied unchanged), a hand-copied route descriptor that matches it
  // field for field, and only the one pair of `program_key`s -- the
  // admission's and the local route's -- moved together to the frozen test
  // sentinel `kMeasuredParityExclusions` reserves for exactly this.
  Renderer renderer;
  auto plan = renderer.compile(kPerlinSource, "measured-parity-sentinel.dsl");
  const auto inputs = options(7U, 5U);
  const auto bindings = bind_compiled_pass(plan, "synth/perlin", 0U, inputs, 7U, 5U);

  const std::string sentinel_key =
      "__measured_parity_test_sentinel__/neverReal:neverReal";
  const auto* real_route =
      canonical_route("synth/perlin:perlin", "bind_synth_perlin_perlin");
  REQUIRE(real_route != nullptr);
  FactoryRouteDescriptor sentinel_route = *real_route;
  sentinel_route.program_key = sentinel_key;
  const std::array<FactoryRouteDescriptor, 1> routes{{sentinel_route}};

  auto& snapshot = snapshot_for(plan, "synth/perlin");
  auto admission = snapshot.admissions[0];
  admission.identity.program_key = sentinel_key;
  const auto& step = effect_step(plan, "synth/perlin");

  try {
    static_cast<void>(bind_factory_route(step, admission, snapshot.definition,
                                         bindings, routes));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
    REQUIRE(error.detail().find("measured parity exclusion") != std::string_view::npos);
  }
}

TEST(graph_executor_refuses_a_step_that_omits_a_guarded_parameter) {
  // A compiled plan always materializes the declared default, so neither guard
  // can be reached this way from the DSL. A hand-built or edited plan can omit
  // the entry, and an omission must not be a way past the guard.
  const auto erase_parameter = [](EffectStep& step, std::string_view name) {
    for (auto item = step.params.begin(); item != step.params.end(); ++item) {
      if (item->name == name) { step.params.erase(item); return true; }
    }
    return false;
  };

  {
    Renderer renderer;
    auto plan = renderer.compile(
        "search synth, filter\nsolid(color: #3a7).median().write(o0)\nrender(o0)\n",
        "absent-define.dsl");
    REQUIRE(erase_parameter(effect_step(plan, "filter/median"), "radius"));
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(8U, 8U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      // filter/median:median is now a custom_adapter route (see
      // src/effects/median.cpp / noisemaker::effects::bind_median): RADIUS
      // is a real compile-define binding materialized straight from the
      // step's own "radius" parameter, not a default-only typed-emitter
      // bake, so an omitted parameter fails closed one step earlier now --
      // in materialize_compile_defines, not authenticate_compile_define_parameters
      // (which returns immediately for any custom_adapter route). Same
      // guard, same error code, different message.
      REQUIRE(error.code() == GraphErrorCode::missing_binding);
      REQUIRE(error.detail() == "compile define has no owning parameter");
    }
  }
  {
    Renderer renderer;
    auto plan = renderer.compile(
        "search classicNoisedeck\nshapes(palette: 0).write(o0)\nrender(o0)\n",
        "absent-palette.dsl");
    REQUIRE(erase_parameter(effect_step(plan, "classicNoisedeck/shapes"), "palette"));
    reauthenticate(plan);
    try {
      static_cast<void>(renderer.render(plan, options(8U, 8U)));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::missing_binding);
      REQUIRE(error.detail() ==
              "parameter palette selects the palette but the step carries no value "
              "for it");
    }
  }
}

TEST(graph_halftone_color_alpha_carrier_preserves_presence_and_value) {
  const auto color = [](double r, double g, double b, std::optional<double> alpha) {
    std::vector<PlanValue> lanes = {PlanValue::number_value(r),
                                    PlanValue::number_value(g),
                                    PlanValue::number_value(b)};
    if (alpha.has_value()) lanes.push_back(PlanValue::number_value(*alpha));
    return PlanValue::array_value(std::move(lanes));
  };
  PassAdmission admission;
  admission.identity.program_key = "filter/halftone:halftone";
  admission.uniforms = {
      {"inkColor", "vec3", "effect_parameter", "inkColor", {}, "glsl::DVec3"},
      {"paperColor", "vec3", "effect_parameter", "paperColor", {}, "glsl::DVec3"},
  };
  EffectStep step;
  step.effect = {"filter/halftone", "image", "filter"};
  effects::PassDefinition pass;
  const auto inputs = options(8U, 8U);
  const BindingMaterializationContext context{&inputs, nullptr, 8U, 8U};
  for (const auto& [ink_alpha, paper_alpha] :
       std::array<std::pair<std::optional<double>, std::optional<double>>, 4>{
           std::pair{std::optional<double>{}, std::optional<double>{}},
           std::pair{std::optional<double>{}, std::optional<double>{0.75}},
           std::pair{std::optional<double>{0.25}, std::optional<double>{}},
           std::pair{std::optional<double>{std::numeric_limits<double>::quiet_NaN()},
                     std::optional<double>{0.75}},
       }) {
    step.params = {{"inkColor", color(0.1, 0.2, 0.3, ink_alpha)},
                   {"paperColor", color(0.8, 0.7, 0.6, paper_alpha)}};
    const auto bindings = materialize_uniform_bindings(step, admission, pass, context);
    REQUIRE(bindings.get<bool>("__cpuColorHasAlpha_inkColor") == ink_alpha.has_value());
    REQUIRE(bindings.get<bool>("__cpuColorHasAlpha_paperColor") == paper_alpha.has_value());
    if (ink_alpha.has_value()) {
      REQUIRE((std::isnan(*ink_alpha) &&
               std::isnan(bindings.get<double>("__cpuColorAlpha_inkColor"))) ||
              bindings.get<double>("__cpuColorAlpha_inkColor") == *ink_alpha);
    }
    if (paper_alpha.has_value()) {
      REQUIRE(bindings.get<double>("__cpuColorAlpha_paperColor") == *paper_alpha);
    }
  }
}
