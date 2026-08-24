#include "test_harness.hpp"

#include <memory>

#include "noisemaker/kernel.hpp"
#include "noisemaker/pass_runner.hpp"

namespace {

class EmptyState final : public noisemaker::KernelState {};

void write_coordinates(const noisemaker::KernelState&,
                       const noisemaker::glsl::PixelContext& context,
                       noisemaker::glsl::Vec4& output) noexcept {
  output = noisemaker::glsl::Vec4(context.frag_coord[0], context.frag_coord[1],
                                  context.uv[0], context.uv[1]);
}

void write_timing(const noisemaker::KernelState&,
                  const noisemaker::glsl::PixelContext& context,
                  noisemaker::glsl::Vec4& output) noexcept {
  output = noisemaker::glsl::Vec4(context.time, context.seed,
                                  static_cast<float>(context.frame), context.delta_time);
}

void write_only_left_pixel(const noisemaker::KernelState&,
                           const noisemaker::glsl::PixelContext& context,
                           noisemaker::glsl::Vec4& output) noexcept {
  if (context.resolution[0] <= 1.0f || context.frag_coord[0] >= 1.0f) return;
  output = noisemaker::glsl::Vec4(0.25f, 0.5f, 0.75f, 1.0f);
}

void write_only_last_derivative_probe(
    const noisemaker::KernelState&,
    const noisemaker::glsl::PixelContext& context,
    noisemaker::glsl::Vec4& output) noexcept {
  (void)noisemaker::glsl::dFdx(context, context.uv[0]);
  if (context.derivative == nullptr
      || context.derivative->mode != noisemaker::glsl::DerivativeMode::Record
      || context.frag_coord[0] != 1.5f || context.frag_coord[1] != 1.5f) {
    return;
  }
  output = noisemaker::glsl::Vec4(0.125f, 0.25f, 0.5f, 1.0f);
}

void write_derivative_probe_coordinates_only(
    const noisemaker::KernelState&,
    const noisemaker::glsl::PixelContext& context,
    noisemaker::glsl::Vec4& output) noexcept {
  (void)noisemaker::glsl::dFdx(context, context.uv[0]);
  if (context.derivative == nullptr
      || context.derivative->mode != noisemaker::glsl::DerivativeMode::Record) {
    return;
  }
  output = noisemaker::glsl::Vec4(context.frag_coord[0],
                                  context.frag_coord[1], 0.0f, 1.0f);
}

// A linear field in uv. Its screen-space derivatives have an exact closed
// form: uv.x advances by 1/width per pixel of fragCoord.x, so for
// `t = 3*uv.x + 5*uv.y` we expect dFdx(t) == 3/width and dFdy(t) == 5/height,
// with fwidth == |dFdx| + |dFdy|. Signs are asymmetric (3 vs -5) so a flipped
// difference, a swapped axis, or a transposed quad corner all change the
// answer rather than cancelling out.
void write_linear_derivatives(const noisemaker::KernelState&,
                              const noisemaker::glsl::PixelContext& context,
                              noisemaker::glsl::Vec4& output) noexcept {
  const double t = 3.0 * static_cast<double>(context.uv[0])
                 - 5.0 * static_cast<double>(context.uv[1]);
  output = noisemaker::glsl::Vec4(noisemaker::glsl::dFdx(context, t),
                                  noisemaker::glsl::dFdy(context, t),
                                  noisemaker::glsl::fwidth(context, t), 0.0f);
}

}  // namespace

TEST(pass_runner_quad_driver_reproduces_closed_form_linear_derivatives) {
  // Odd dimensions on both axes, so the last quad in each direction is half
  // outside the canvas and the driver genuinely probes past the edge.
  constexpr std::size_t kWidth = 7U;
  constexpr std::size_t kHeight = 5U;
  const noisemaker::BoundKernel kernel(std::make_shared<EmptyState>(),
                                       &write_linear_derivatives, true);
  const noisemaker::Surface image = noisemaker::run_pass(kernel, kWidth, kHeight);
  const auto data = image.data();

  const float expected_dx = 3.0f / static_cast<float>(kWidth);
  const float expected_dy = -5.0f / static_cast<float>(kHeight);
  const float expected_width = expected_dx - expected_dy;  // |dx| + |dy|

  for (std::size_t y = 0; y < kHeight; ++y) {
    for (std::size_t x = 0; x < kWidth; ++x) {
      const std::size_t offset = (y * kWidth + x) * 4U;
      REQUIRE(test::nearly_equal(data[offset + 0U], expected_dx));
      REQUIRE(test::nearly_equal(data[offset + 1U], expected_dy));
      REQUIRE(test::nearly_equal(data[offset + 2U], expected_width));
    }
  }
}

TEST(pass_runner_without_derivatives_leaves_the_context_pointer_null) {
  // The fast path must not hand kernels a derivative state; a program that
  // never calls a derivative builtin has to be bit-for-bit unaffected.
  const noisemaker::BoundKernel kernel(std::make_shared<EmptyState>(), &write_coordinates);
  REQUIRE(!kernel.uses_derivatives());
  const noisemaker::Surface image = noisemaker::run_pass(kernel, 2U, 2U);
  const auto data = image.data();
  REQUIRE(test::nearly_equal(data[0], 0.5f));
  REQUIRE(test::nearly_equal(data[1], 1.5f));
}

TEST(pass_runner_uses_bottom_left_glsl_coordinates_and_top_down_surface_storage) {
  const noisemaker::BoundKernel kernel(std::make_shared<EmptyState>(), &write_coordinates);
  const noisemaker::Surface image = noisemaker::run_pass(kernel, 2U, 2U);
  const auto data = image.data();

  REQUIRE(test::nearly_equal(data[0], 0.5f));
  REQUIRE(test::nearly_equal(data[1], 1.5f));
  REQUIRE(test::nearly_equal(data[2], 0.25f));
  REQUIRE(test::nearly_equal(data[3], 0.75f));
  REQUIRE(test::nearly_equal(data[4], 1.5f));
  REQUIRE(test::nearly_equal(data[5], 1.5f));
  REQUIRE(test::nearly_equal(data[8], 0.5f));
  REQUIRE(test::nearly_equal(data[9], 0.5f));
  REQUIRE(test::nearly_equal(data[12], 1.5f));
  REQUIRE(test::nearly_equal(data[13], 0.5f));
}

TEST(pass_runner_propagates_time_seed_frame_and_delta_time) {
  const noisemaker::BoundKernel kernel(std::make_shared<EmptyState>(), &write_timing);
  const noisemaker::Surface image = noisemaker::run_pass(kernel, 1U, 1U, 2.5f, 3.0f, 7U, 0.125f);
  const auto data = image.data();
  REQUIRE(test::nearly_equal(data[0], 2.5f));
  REQUIRE(test::nearly_equal(data[1], 3.0f));
  REQUIRE(test::nearly_equal(data[2], 7.0f));
  REQUIRE(test::nearly_equal(data[3], 0.125f));
}

TEST(pass_runner_preserves_bound_kernel_color_within_and_across_passes) {
  const noisemaker::BoundKernel kernel(
      std::make_shared<EmptyState>(), &write_only_left_pixel);
  const noisemaker::Surface first = noisemaker::run_pass(kernel, 3U, 1U);
  for (std::size_t pixel = 0; pixel < 3U; ++pixel) {
    const std::size_t offset = pixel * 4U;
    REQUIRE(first.data()[offset] == 0.25f);
    REQUIRE(first.data()[offset + 1U] == 0.5f);
    REQUIRE(first.data()[offset + 2U] == 0.75f);
    REQUIRE(first.data()[offset + 3U] == 1.0f);
  }

  // A new pass on the same bound kernel begins with an early return. The
  // canonical factory's persistent fragColor must still contain the prior
  // pass's last value.
  const noisemaker::Surface second = noisemaker::run_pass(kernel, 1U, 1U);
  REQUIRE(second.data()[0] == 0.25f);
  REQUIRE(second.data()[1] == 0.5f);
  REQUIRE(second.data()[2] == 0.75f);
  REQUIRE(second.data()[3] == 1.0f);

  // A freshly bound kernel starts from Float32Array zero initialization.
  const noisemaker::BoundKernel fresh(
      std::make_shared<EmptyState>(), &write_only_left_pixel);
  noisemaker::glsl::PixelContext skipped;
  skipped.frag_coord = noisemaker::glsl::Vec4(1.5f, 0.5f, 0.0f, 1.0f);
  noisemaker::glsl::Vec4 output(9.0f);
  fresh.run_pixel(skipped, output);
  REQUIRE(output == noisemaker::glsl::Vec4(0.0f));
}

TEST(bound_kernel_copies_share_the_canonical_factory_color_slot) {
  const noisemaker::BoundKernel original(
      std::make_shared<EmptyState>(), &write_only_left_pixel);
  const noisemaker::BoundKernel copy = original;

  // The copy executes the write. The original then begins with a skipped
  // invocation and must observe the same factory-closure fragColor slot.
  (void)noisemaker::run_pass(copy, 2U, 1U);
  const noisemaker::Surface inherited = noisemaker::run_pass(original, 1U, 1U);
  REQUIRE(inherited.data()[0] == 0.25f);
  REQUIRE(inherited.data()[1] == 0.5f);
  REQUIRE(inherited.data()[2] == 0.75f);
  REQUIRE(inherited.data()[3] == 1.0f);
}

TEST(pass_runner_derivative_probes_share_bound_kernel_color_with_replay) {
  const noisemaker::BoundKernel kernel(
      std::make_shared<EmptyState>(), &write_only_last_derivative_probe, true);
  const noisemaker::Surface image = noisemaker::run_pass(kernel, 1U, 1U);
  REQUIRE(image.data()[0] == 0.125f);
  REQUIRE(image.data()[1] == 0.25f);
  REQUIRE(image.data()[2] == 0.5f);
  REQUIRE(image.data()[3] == 1.0f);
}

TEST(pass_runner_derivative_invocation_order_matches_canonical_raster_schedule) {
  const noisemaker::BoundKernel kernel(
      std::make_shared<EmptyState>(), &write_derivative_probe_coordinates_only,
      true);
  const noisemaker::Surface image = noisemaker::run_pass(kernel, 4U, 2U);

  // Canonical runPass visits the top row first. Its first pixel in each quad
  // runs that quad's four probes; later replays carry the most recently probed
  // top-right coordinate. By the time traversal returns to the lower-left
  // quad, the upper-right quad's probe value is still the bound fragColor.
  constexpr float expected_x[] = {1.5f, 1.5f, 3.5f, 3.5f,
                                  3.5f, 3.5f, 3.5f, 3.5f};
  for (std::size_t pixel = 0; pixel < 8U; ++pixel) {
    REQUIRE(image.data()[pixel * 4U] == expected_x[pixel]);
    REQUIRE(image.data()[pixel * 4U + 1U] == 1.5f);
    REQUIRE(image.data()[pixel * 4U + 2U] == 0.0f);
    REQUIRE(image.data()[pixel * 4U + 3U] == 1.0f);
  }
}

TEST(pass_runner_checks_exact_extent_before_surface_construction) {
  const noisemaker::BoundKernel kernel(
      std::make_shared<EmptyState>(), &write_coordinates, false,
      noisemaker::PassContract{noisemaker::ExactOutputExtent{
          1U, 1U, "stats output dimensions must be 1x1"}});
  bool exact_message = false;
  try {
    (void)noisemaker::run_pass(kernel, 0U, 1U);
  } catch (const std::invalid_argument& error) {
    exact_message = true;
    REQUIRE(std::string_view(error.what()) ==
            "stats output dimensions must be 1x1");
  }
  REQUIRE(exact_message);
}
