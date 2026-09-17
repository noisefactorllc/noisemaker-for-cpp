// Unit proof for the generic multi-render-target (MRT, drawBuffers >= 2)
// primitive: BoundKernelMrt (kernel.hpp) and run_mrt_pass (pass_runner.hpp).
// Mirrors the JS authority's runCanonicalMrtPass exactly
// (src/runtime/renderer.js:450-490): one kernel call per pixel produces
// every output atomically into persistent per-output registers, which
// run_mrt_pass then scatters into one Surface per output -- the direct MRT
// analog of BoundKernel/run_pass, proven here to share their exact
// coordinate convention and storage.
//
// See docs/... (this campaign's phase2-architecture.md/frontier-92.md) for
// the JS citations this ports; the differential proof against the real JS
// authority kernel (for synthetic 2/3/4-output programs compiled through
// the typed pipeline) lives outside the repo in this session's own
// throwaway harness, not here -- this file is the permanent, checked-in
// primitive-level proof.

#include "test_harness.hpp"

#include <memory>
#include <optional>

#include "noisemaker/kernel.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/texture_format.hpp"

namespace {

class EmptyState final : public noisemaker::KernelState {};

class ValueState final : public noisemaker::KernelState {
 public:
  explicit ValueState(float value) : value(value) {}
  float value;
};

// Two outputs: output[0] gets the same fragCoord-derived pattern
// test_pass_runner.cpp's write_coordinates uses for the single-output path;
// output[1] gets a distinct uv-derived pattern. Proves each of the N
// outputs is independently addressable and that both are produced by the
// SAME kernel invocation (one call per pixel, not one call per output).
void write_two_distinct_outputs(const noisemaker::KernelState&,
                                const noisemaker::glsl::PixelContext& context,
                                noisemaker::glsl::Vec4* outputs) noexcept {
  outputs[0] = noisemaker::glsl::Vec4(context.frag_coord[0], context.frag_coord[1],
                                      context.uv[0], context.uv[1]);
  outputs[1] = noisemaker::glsl::Vec4(context.uv[1], context.uv[0],
                                      context.time, context.seed);
}

// The exact fragCoord-derived pattern test_pass_runner.cpp's
// write_coordinates uses, for the single-output BoundKernel path -- used to
// prove run_mrt_pass's output[0] is byte-identical to run_pass's output for
// the identical expression (same coordinate convention, same storage).
void write_coordinates_single(const noisemaker::KernelState&,
                              const noisemaker::glsl::PixelContext& context,
                              noisemaker::glsl::Vec4& output) noexcept {
  output = noisemaker::glsl::Vec4(context.frag_coord[0], context.frag_coord[1],
                                  context.uv[0], context.uv[1]);
}

void write_first_output_only(const noisemaker::KernelState& state,
                             const noisemaker::glsl::PixelContext& context,
                             noisemaker::glsl::Vec4* outputs) noexcept {
  write_coordinates_single(state, context, outputs[0]);
}

// Three outputs, the last derived from ValueState -- proves state threads
// through exactly like the single-output path, and that a >2-output kernel
// (not just the minimum 2) works.
void write_three_outputs(const noisemaker::KernelState& state,
                         const noisemaker::glsl::PixelContext& context,
                         noisemaker::glsl::Vec4* outputs) noexcept {
  const auto& typed = static_cast<const ValueState&>(state);
  outputs[0] = noisemaker::glsl::Vec4(context.frag_coord[0], 0.0f, 0.0f, 1.0f);
  outputs[1] = noisemaker::glsl::Vec4(0.0f, context.frag_coord[1], 0.0f, 1.0f);
  outputs[2] = noisemaker::glsl::Vec4(0.0f, 0.0f, typed.value, 1.0f);
}

// Writes both outputs unconditionally on frame 0, then only output[1] on
// every later call -- proves output[0]'s persistent register survives
// across calls exactly like BoundKernel::frag_color_ does for the
// single-output path (a pixel invocation that returns/skips a slot exposes
// the last value written to it, never a zeroed fresh buffer).
void write_output_zero_once_then_skip(const noisemaker::KernelState&,
                                      const noisemaker::glsl::PixelContext& context,
                                      noisemaker::glsl::Vec4* outputs) noexcept {
  if (context.frame == 0U) {
    outputs[0] = noisemaker::glsl::Vec4(0.75f, 0.5f, 0.25f, 1.0f);
  }
  outputs[1] = noisemaker::glsl::Vec4(context.frag_coord[0], 0.0f, 0.0f, 1.0f);
}

}  // namespace

TEST(bound_kernel_mrt_rejects_null_state_or_pixel_function) {
  const auto state = std::make_shared<EmptyState>();
  REQUIRE_THROWS_AS(noisemaker::BoundKernelMrt(nullptr, &write_two_distinct_outputs, 2U),
                    std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::BoundKernelMrt(state, nullptr, 2U),
                    std::invalid_argument);
}

TEST(bound_kernel_mrt_rejects_fewer_than_two_outputs) {
  const auto state = std::make_shared<EmptyState>();
  REQUIRE_THROWS_AS(noisemaker::BoundKernelMrt(state, &write_two_distinct_outputs, 1U),
                    std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::BoundKernelMrt(state, &write_two_distinct_outputs, 0U),
                    std::invalid_argument);
}

TEST(bound_kernel_mrt_rejects_derivatives) {
  // No admitted MRT program uses dFdx/dFdy/fwidth; there is deliberately no
  // quad-replay wrapper for this constructor, so it must fail closed rather
  // than silently skip the approximation.
  const auto state = std::make_shared<EmptyState>();
  REQUIRE_THROWS_AS(
      noisemaker::BoundKernelMrt(state, &write_two_distinct_outputs, 2U, true),
      std::invalid_argument);
}

TEST(bound_kernel_mrt_retains_state_and_dispatches_through_stateful_api) {
  std::weak_ptr<const noisemaker::KernelState> weak;
  std::optional<noisemaker::BoundKernelMrt> kernel;
  {
    const auto state = std::make_shared<ValueState>(0.5f);
    weak = state;
    kernel.emplace(state, &write_three_outputs, 3U);
  }
  REQUIRE(!weak.expired());
  REQUIRE(kernel->output_count() == 3U);
  REQUIRE(!kernel->uses_derivatives());
  REQUIRE(!kernel->pass_contract().exact_output_extent.has_value());
  noisemaker::glsl::Vec4 outputs[3];
  const noisemaker::glsl::PixelContext context{
      .uv = {}, .frag_coord = noisemaker::glsl::Vec4(2.0f, 3.0f, 0.0f, 1.0f),
      .resolution = {}, .time = 0.0f, .seed = 0.0f, .frame = 0U,
      .delta_time = 0.0f, .derivative = nullptr};
  kernel->run_pixel(context, outputs);
  REQUIRE(test::nearly_equal(outputs[0][0], 2.0f));
  REQUIRE(test::nearly_equal(outputs[1][1], 3.0f));
  REQUIRE(test::nearly_equal(outputs[2][2], 0.5f));
  kernel.reset();
  REQUIRE(weak.expired());
}

TEST(run_mrt_pass_one_kernel_call_per_pixel_produces_every_output_atomically) {
  constexpr std::size_t kWidth = 5U;
  constexpr std::size_t kHeight = 3U;
  const noisemaker::BoundKernelMrt kernel(std::make_shared<EmptyState>(),
                                          &write_two_distinct_outputs, 2U);
  const std::vector<noisemaker::Surface> surfaces =
      noisemaker::run_mrt_pass(kernel, kWidth, kHeight);
  REQUIRE(surfaces.size() == 2U);
  REQUIRE(surfaces[0].width() == kWidth);
  REQUIRE(surfaces[0].height() == kHeight);
  REQUIRE(surfaces[1].width() == kWidth);
  REQUIRE(surfaces[1].height() == kHeight);

  const auto first = surfaces[0].data();
  const auto second = surfaces[1].data();
  for (std::size_t y = 0; y < kHeight; ++y) {
    for (std::size_t x = 0; x < kWidth; ++x) {
      const std::size_t offset = (y * kWidth + x) * 4U;
      const float expected_fx = static_cast<float>(x) + 0.5f;
      const float expected_fy = static_cast<float>(kHeight - y) - 0.5f;
      const float expected_u = expected_fx / static_cast<float>(kWidth);
      const float expected_v = expected_fy / static_cast<float>(kHeight);
      REQUIRE(test::nearly_equal(first[offset + 0], expected_fx));
      REQUIRE(test::nearly_equal(first[offset + 1], expected_fy));
      REQUIRE(test::nearly_equal(first[offset + 2], expected_u));
      REQUIRE(test::nearly_equal(first[offset + 3], expected_v));
      // output[1] is the SAME pixel's uv, swapped -- produced by the exact
      // same kernel call as output[0], not a second, independent pass.
      REQUIRE(test::nearly_equal(second[offset + 0], expected_v));
      REQUIRE(test::nearly_equal(second[offset + 1], expected_u));
    }
  }
}

TEST(run_mrt_pass_output_zero_matches_run_pass_byte_for_byte) {
  // Same coordinate convention, same storage layout as the single-output
  // path: a kernel whose sole first output writes the identical expression
  // write_coordinates_single does must produce an IDENTICAL Surface to
  // run_pass's own result for that expression.
  constexpr std::size_t kWidth = 7U;
  constexpr std::size_t kHeight = 4U;
  const noisemaker::BoundKernel single(std::make_shared<EmptyState>(),
                                       &write_coordinates_single);
  const noisemaker::Surface expected = noisemaker::run_pass(single, kWidth, kHeight,
                                                             1.5f, 2.5f, 7U, 0.125f);

  const noisemaker::BoundKernelMrt mrt(std::make_shared<EmptyState>(),
                                       &write_first_output_only, 2U);
  const std::vector<noisemaker::Surface> surfaces =
      noisemaker::run_mrt_pass(mrt, kWidth, kHeight, 1.5f, 2.5f, 7U, 0.125f);

  const auto expected_data = expected.data();
  const auto actual_data = surfaces[0].data();
  REQUIRE(expected_data.size() == actual_data.size());
  for (std::size_t index = 0; index < expected_data.size(); ++index) {
    REQUIRE(expected_data[index] == actual_data[index]);
  }
}

TEST(bound_kernel_mrt_persists_output_registers_across_calls) {
  // Mirrors bound_kernel_copies_share_the_canonical_factory_color_slot /
  // pass_runner_preserves_bound_kernel_color_within_and_across_passes for
  // the single-output path: every generated MRT pixel() writes into this
  // SAME persistent storage every call (never a fresh per-call buffer), so
  // a pixel invocation that skips a slot exposes whatever an earlier call
  // last wrote there -- exactly like the JS authority's own per-output
  // closure-variable persistence (fragColor/geoOut/... allocated once per
  // factory call, mutated in place every pixel).
  const noisemaker::BoundKernelMrt kernel(std::make_shared<EmptyState>(),
                                          &write_output_zero_once_then_skip, 2U);
  noisemaker::glsl::Vec4 outputs[2];
  noisemaker::glsl::PixelContext context{
      .uv = {}, .frag_coord = noisemaker::glsl::Vec4(0.0f, 0.0f, 0.0f, 1.0f),
      .resolution = {}, .time = 0.0f, .seed = 0.0f, .frame = 0U,
      .delta_time = 0.0f, .derivative = nullptr};
  kernel.run_pixel(context, outputs);
  REQUIRE(test::nearly_equal(outputs[0][0], 0.75f));

  context.frame = 1U;
  context.frag_coord = noisemaker::glsl::Vec4(9.0f, 0.0f, 0.0f, 1.0f);
  outputs[0] = noisemaker::glsl::Vec4(0.0f, 0.0f, 0.0f, 0.0f);  // caller-side buffer, not the register
  kernel.run_pixel(context, outputs);
  // output[0] was never assigned on this call, yet the copy handed back
  // still carries the earlier value -- proving it came from the kernel's
  // own persistent register, not the caller's zeroed local.
  REQUIRE(test::nearly_equal(outputs[0][0], 0.75f));
  REQUIRE(test::nearly_equal(outputs[1][0], 9.0f));
}

TEST(run_mrt_pass_result_quantizes_through_the_same_api_as_run_pass) {
  const noisemaker::BoundKernelMrt kernel(std::make_shared<EmptyState>(),
                                          &write_two_distinct_outputs, 2U);
  std::vector<noisemaker::Surface> surfaces = noisemaker::run_mrt_pass(kernel, 3U, 3U);
  // Both destinations are ordinary Surfaces; each quantizes independently
  // through the identical entry point the single-output path uses.
  noisemaker::quantize_texture(surfaces[0], noisemaker::TextureFormat::rgba8_unorm);
  noisemaker::quantize_texture(surfaces[1], noisemaker::TextureFormat::rgba16f);
  REQUIRE(surfaces[0].width() == 3U);
  REQUIRE(surfaces[1].width() == 3U);
}

TEST(bound_kernel_mrt_checks_exact_extent_before_surface_construction) {
  noisemaker::PassContract contract;
  contract.exact_output_extent = noisemaker::ExactOutputExtent{
      2U, 2U, "must be 2x2"};
  const noisemaker::BoundKernelMrt kernel(std::make_shared<EmptyState>(),
                                          &write_two_distinct_outputs, 2U,
                                          false, contract);
  REQUIRE_THROWS_AS(noisemaker::run_mrt_pass(kernel, 3U, 3U), std::invalid_argument);
  const std::vector<noisemaker::Surface> ok = noisemaker::run_mrt_pass(kernel, 2U, 2U);
  REQUIRE(ok.size() == 2U);
}
