#include "test_harness.hpp"

#include <memory>
#include <optional>

#include "noisemaker/kernel.hpp"

namespace {

template <typename T>
concept HasRawPixelAccessor = requires(const T& value) { value.pixel(); };

template <typename T>
concept HasRawStateAccessor = requires(const T& value) { value.state(); };

class TestState final : public noisemaker::KernelState {
 public:
  explicit TestState(float value) : value(value) {}
  float value;
};

void copy_value(const noisemaker::KernelState& state,
                const noisemaker::glsl::PixelContext&,
                noisemaker::glsl::Vec4& output) noexcept {
  const auto& typed = static_cast<const TestState&>(state);
  output = noisemaker::glsl::Vec4(typed.value, 0.0f, 0.0f, 1.0f);
}

}  // namespace

TEST(bound_kernel_rejects_null_state_or_pixel_function) {
  const auto state = std::make_shared<TestState>(0.25f);
  REQUIRE_THROWS_AS(noisemaker::BoundKernel(nullptr, &copy_value), std::invalid_argument);
  REQUIRE_THROWS_AS(noisemaker::BoundKernel(state, nullptr), std::invalid_argument);
}

TEST(bound_kernel_retains_state_and_dispatches_through_stateful_api) {
  std::weak_ptr<const noisemaker::KernelState> weak;
  std::optional<noisemaker::BoundKernel> kernel;
  {
    const auto state = std::make_shared<TestState>(0.25f);
    weak = state;
    kernel.emplace(state, &copy_value);
  }
  REQUIRE(!weak.expired());
  REQUIRE(!kernel->pass_contract().exact_output_extent.has_value());
  noisemaker::glsl::Vec4 output;
  kernel->run_pixel({}, output);
  REQUIRE(test::nearly_equal(output[0], 0.25f));
  REQUIRE(test::nearly_equal(output[3], 1.0f));
  kernel.reset();
  REQUIRE(weak.expired());
}

TEST(bound_kernel_does_not_expose_raw_state_or_pixel_callback) {
  static_assert(!HasRawPixelAccessor<noisemaker::BoundKernel>);
  static_assert(!HasRawStateAccessor<noisemaker::BoundKernel>);
  REQUIRE(!HasRawPixelAccessor<noisemaker::BoundKernel>);
  REQUIRE(!HasRawStateAccessor<noisemaker::BoundKernel>);
}

TEST(bound_kernel_exact_output_extent_is_closed_and_copyable) {
  const auto state = std::make_shared<TestState>(0.25f);
  const noisemaker::PassContract contract{
      noisemaker::ExactOutputExtent{1U, 1U, "expected one pixel"}};
  const noisemaker::BoundKernel kernel(state, &copy_value, false, contract);
  REQUIRE(kernel.pass_contract().exact_output_extent.has_value());
  kernel.validate_pass(1U, 1U);
  REQUIRE_THROWS_AS(kernel.validate_pass(2U, 1U), std::invalid_argument);
  const noisemaker::BoundKernel copied = kernel;
  copied.validate_pass(1U, 1U);
  REQUIRE_THROWS_AS(copied.validate_pass(1U, 2U), std::invalid_argument);
}

TEST(bound_kernel_rejects_malformed_exact_output_extent) {
  const auto state = std::make_shared<TestState>(0.25f);
  REQUIRE_THROWS_AS(
      noisemaker::BoundKernel(
          state, &copy_value, false,
          noisemaker::PassContract{
              noisemaker::ExactOutputExtent{0U, 1U, "invalid"}}),
      std::invalid_argument);
  REQUIRE_THROWS_AS(
      noisemaker::BoundKernel(
          state, &copy_value, false,
          noisemaker::PassContract{
              noisemaker::ExactOutputExtent{1U, 1U, ""}}),
      std::invalid_argument);
}
