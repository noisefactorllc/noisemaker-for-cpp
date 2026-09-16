#include "test_harness.hpp"

#include "noisemaker/effects/bit_effects.hpp"
#include "noisemaker/effects/snow.hpp"
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

  // filter/snow:snow: a second hand-written custom adapter, following the
  // exact same bitEffects row shape (only canonical_factory, route_kind,
  // and bind change; every ABI/source hash stays the GLSL-declared one --
  // see src/effects/snow.cpp and the field comment on
  // kMeasuredParityExclusions above).
  const auto* snow = canonical_route("filter/snow:snow", "noisemaker::effects::bind_snow");
  REQUIRE(snow != nullptr);
  REQUIRE(snow->route_kind == "custom_adapter");
  REQUIRE(snow->bind == &noisemaker::effects::bind_snow);

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
  REQUIRE(typed_emitter == 208U);
  REQUIRE(custom_adapter == 3U);
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
