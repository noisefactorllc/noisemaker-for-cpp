#pragma once

#include <cstddef>
#include <memory>
#include <optional>
#include <string>

#include "noisemaker/glsl_runtime.hpp"

namespace noisemaker {

struct KernelState {
  virtual ~KernelState() = default;
};

using PixelFn = void (*)(const KernelState&, const glsl::PixelContext&,
                         glsl::Vec4&) noexcept;

struct ExactOutputExtent {
  std::size_t width;
  std::size_t height;
  std::string error_message;
};

struct PassContract {
  std::optional<ExactOutputExtent> exact_output_extent;
};

// Stateful handle for one bound canonical factory. Pixel output state persists
// across run_pixel/run_pass calls and is shared by copies. The same handle, or
// copies of it, must not be rendered concurrently; bind independently for each
// concurrent worker.
class BoundKernel {
 public:
  // `uses_derivatives` defaults false so every existing construction site is
  // unchanged; only a kernel calling dFdx/dFdy/fwidth passes true, which routes
  // run_pass through its 2x2-quad record/replay driver.
  BoundKernel(std::shared_ptr<const KernelState> state, PixelFn pixel,
              bool uses_derivatives = false, PassContract pass_contract = {});

  void run_pixel(const glsl::PixelContext& context,
                 glsl::Vec4& output) const noexcept;
  [[nodiscard]] bool uses_derivatives() const noexcept;
  [[nodiscard]] const PassContract& pass_contract() const noexcept;
  void validate_pass(std::size_t width, std::size_t height) const;

 private:
  std::shared_ptr<const KernelState> state_;
  PixelFn pixel_;
  bool uses_derivatives_;
  PassContract pass_contract_;
  // Canonical GLSL factories allocate `fragColor` once at bind time. A pixel
  // invocation that returns before assigning it therefore exposes the last
  // value written by this bound kernel, including writes made by derivative
  // probes and earlier run_pass calls. Copies of BoundKernel represent the
  // same bound factory closure, so they share this slot just as they share the
  // immutable generated state.
  std::shared_ptr<glsl::Vec4> frag_color_;
};

}  // namespace noisemaker
