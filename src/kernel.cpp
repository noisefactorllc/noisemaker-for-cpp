#include "noisemaker/kernel.hpp"

#include <stdexcept>
#include <string>
#include <utility>

namespace noisemaker {

BoundKernel::BoundKernel(std::shared_ptr<const KernelState> state, PixelFn pixel,
                         bool uses_derivatives, PassContract pass_contract)
    : state_(std::move(state)), pixel_(pixel), uses_derivatives_(uses_derivatives),
      pass_contract_(pass_contract),
      frag_color_(std::make_shared<glsl::Vec4>()) {
  if (!state_) {
    throw std::invalid_argument("kernel state must not be null");
  }
  if (pixel_ == nullptr) {
    throw std::invalid_argument("kernel pixel function must not be null");
  }
  if (pass_contract_.exact_output_extent.has_value()) {
    const ExactOutputExtent& extent = *pass_contract_.exact_output_extent;
    if (extent.width == 0U || extent.height == 0U || extent.error_message.empty()) {
      throw std::invalid_argument("exact output extent contract is invalid");
    }
  }
}

void BoundKernel::run_pixel(const glsl::PixelContext& context,
                            glsl::Vec4& output) const noexcept {
  pixel_(*state_, context, *frag_color_);
  output = *frag_color_;
}

bool BoundKernel::uses_derivatives() const noexcept { return uses_derivatives_; }

const PassContract& BoundKernel::pass_contract() const noexcept {
  return pass_contract_;
}

void BoundKernel::validate_pass(std::size_t width, std::size_t height) const {
  if (!pass_contract_.exact_output_extent.has_value()) return;
  const ExactOutputExtent& extent = *pass_contract_.exact_output_extent;
  if (width != extent.width || height != extent.height) {
    throw std::invalid_argument(std::string(extent.error_message));
  }
}

}  // namespace noisemaker
