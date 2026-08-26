#include "test_harness.hpp"

#include "noisemaker/effects/bit_effects.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/renderer.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <new>
#include <string>
#include <type_traits>
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

constexpr std::string_view kTextSource =
    "search synth, filter\n"
    "solid(color: #3a7).text().write(o0)\n"
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

TEST(graph_generated_canonical_route_table_is_connected_and_duplicate_safe) {
  const auto routes = canonical_factory_routes();
  REQUIRE(routes.size() == 211U);

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

  // The source-incompatible row stays present for inspection; execution
  // rejects it on admission status, not by absence from the table.
  REQUIRE(canonical_route("filter/text:text", "bind_filter_text_text") != nullptr);

  std::size_t typed_emitter = 0;
  std::size_t custom_adapter = 0;
  for (const auto& route : routes) {
    REQUIRE(route.bind != nullptr);
    REQUIRE(route.source_sha256.size() == 64U);
    REQUIRE(route.typed_abi_sha256.size() == 64U);
    if (route.route_kind == "typed_emitter") ++typed_emitter;
    if (route.route_kind == "custom_adapter") ++custom_adapter;
  }
  REQUIRE(typed_emitter == 210U);
  REQUIRE(custom_adapter == 1U);
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

TEST(graph_executor_owns_the_remap_uniform_block_and_canonical_defaults) {
  Renderer renderer;
  auto plan = renderer.compile(kRemapSource, "remap-uniforms.dsl");
  const auto inputs = options(13U, 4U);
  const auto bindings = bind_compiled_pass(plan, "synth/remap", 0U, inputs, 13U, 4U);
  const auto& block = bindings.get<glsl::RemapUniformData>("data");
  // Row 0 is the background color/alpha, row 1 carries the zone count and the
  // authority's 0.04 smooth-edge fallback, and the final row carries the
  // render extent supplied by the caller.
  REQUIRE(block.data[0][3] == 1.0F);
  REQUIRE(block.data[1][0] == 0.0F);
  REQUIRE(block.data[1][1] == noisemaker::f32(0.04));
  REQUIRE(block.data[2][3] == 1.0F);
  REQUIRE(block.data[265][0] == 0.0F);
  REQUIRE(block.data[266][0] == 13.0F);
  REQUIRE(block.data[266][1] == 4.0F);
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

TEST(graph_executor_rejects_the_incompatible_text_route_before_binding) {
  Renderer renderer;
  auto plan = renderer.compile(kTextSource, "text.dsl");
  const auto& admission = snapshot_for(plan, "filter/text").admissions[0];
  REQUIRE(admission.status == AvailabilityStatus::incompatible);
  REQUIRE(plan.executable == false);
  try {
    static_cast<void>(renderer.render(plan, options(7U, 5U)));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
    REQUIRE(error.program_key() == "filter/text:text");
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
  remap.reserve(267U);
  for (std::size_t index = 0; index < 267U; ++index) {
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
      {"data", "vec4[267]", "effect_parameter", "data", {}, "vec4[267]"},
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
  REQUIRE(bindings.get<glsl::RemapUniformData>("data").data[266][0] == noisemaker::f32(266.0));

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
  // A bound zone surface publishes its color-mode flag, so `zone0_active` is
  // 1 and the rendered bytes equal the authority exactly.
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
  const auto& block = bindings.get<glsl::RemapUniformData>("data");
  REQUIRE(block.data[2][1] == 1.0F);
  REQUIRE(block.data[3][1] == 0.0F);
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
      }, GraphErrorCode::missing_binding, "sampler ABI route is invalid");
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

TEST(graph_executor_fails_closed_on_the_unported_worm_overlay_resource) {
  // The authority initializes a declared texture with no producer, but
  // `overlayTex` on these three effects is fed by a dedicated CPU adapter this
  // port does not implement. Guessing a zero fill would publish wrong bytes,
  // so the route is refused by name before any allocation.
  for (const auto* effect : {"scratches", "strayHair", "fibers"}) {
    Renderer renderer;
    const std::string source = std::string("search synth, filter\n") +
                               "solid(color: #3a7)." + effect + "().write(o0)\n" +
                               "render(o0)\n";
    try {
      static_cast<void>(renderer.render(source, options(8U, 8U), "worm.dsl"));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
      REQUIRE(error.detail() ==
              "declared texture requires the canonical CPU worm-overlay adapter");
      REQUIRE(error.program_key() == "overlayTex");
    }
  }
}


TEST(graph_executor_fails_closed_when_a_parameter_requests_an_unbaked_compile_define) {
  // The authority publishes a define-backed parameter under its define name,
  // which changes the compiled program. A `default-only` typed emitter was
  // compiled around one value, so any other request must fail closed naming
  // the parameter, the requested value, and the baked value -- never render
  // the baked program and drop the request.
  Renderer renderer;
  const auto refuse = [&](std::string_view source, std::string_view detail) {
    try {
      static_cast<void>(renderer.render(source, options(8U, 8U), "define.dsl"));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
      REQUIRE(error.detail() == detail);
    }
  };
  refuse("search synth\nperlin(dimensions: 3).write(o0)\nrender(o0)\n",
         "parameter dimensions requests compile define DIMENSIONS=3 but the "
         "generated route bakes DIMENSIONS=2");
  refuse("search synth, filter\nsolid(color: #3a7).emboss(style: 1).write(o0)\nrender(o0)\n",
         "parameter style requests compile define STYLE=1 but the generated "
         "route bakes STYLE=0");

  // The baked value itself still dispatches, whether it is defaulted or named.
  REQUIRE(renderer.render("search synth\nperlin().write(o0)\nrender(o0)\n",
                          options(8U, 8U), "define.dsl").width() == 8U);
  REQUIRE(renderer.render("search synth\nperlin(dimensions: 2).write(o0)\nrender(o0)\n",
                          options(8U, 8U), "define.dsl").width() == 8U);
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

TEST(graph_executor_fails_closed_on_an_unported_palette_override) {
  // buildBindings() overrides a classicNoisedeck effect's palette uniforms
  // from the authority's built-in table whenever the palette parameter selects
  // an entry. That table is not ported, so the route is refused instead of
  // being rendered from the plan's own palette values.
  Renderer renderer;
  try {
    static_cast<void>(renderer.render(
        "search classicNoisedeck\nshapes(palette: 46).write(o0)\nrender(o0)\n",
        options(8U, 8U), "palette.dsl"));
    REQUIRE(false);
  } catch (const GraphError& error) {
    REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
    REQUIRE(error.detail() ==
            "parameter palette selects palette entry 46 and the authority overrides "
            "the palette uniforms from its built-in table, which this port has not "
            "ported");
  }
  // Palette entry 0 selects no table entry, so the effect still dispatches.
  REQUIRE(renderer.render(
              "search classicNoisedeck\nshapes(palette: 0).write(o0)\nrender(o0)\n",
              options(8U, 8U), "palette.dsl").width() == 8U);
}

TEST(graph_executor_fails_closed_on_a_measured_parity_exclusion) {
  // Two program keys are measured not byte-equivalent to the authority's own
  // execution. They are refused with the measured reason rather than
  // dispatched to wrong bytes.
  Renderer renderer;
  for (const auto* source : {
           "search synth, filter\nsolid(color: #3a7).snow().write(o0)\nrender(o0)\n",
           "search synth\ntestPattern().write(o0)\nrender(o0)\n"}) {
    try {
      static_cast<void>(renderer.render(source, options(8U, 8U), "parity.dsl"));
      REQUIRE(false);
    } catch (const GraphError& error) {
      REQUIRE(error.code() == GraphErrorCode::unavailable_pass);
      REQUIRE(error.detail().find("measured divergent") != std::string_view::npos);
    }
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
      REQUIRE(error.code() == GraphErrorCode::missing_binding);
      REQUIRE(error.detail() ==
              "parameter radius backs compile define RADIUS but the step carries no "
              "value for it");
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
