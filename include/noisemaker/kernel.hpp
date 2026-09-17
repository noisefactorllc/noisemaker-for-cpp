#pragma once

#include <cstddef>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "noisemaker/glsl_runtime.hpp"

namespace noisemaker {

struct KernelState {
  virtual ~KernelState() = default;
};

using PixelFn = void (*)(const KernelState&, const glsl::PixelContext&,
                         glsl::Vec4&) noexcept;

// A multi-render-target pixel function: writes every one of a program's N
// declared outputs, in declaration (== `layout(location=N)`) order, into
// `outputs[0..N)` for the ONE pixel named by `context`. Mirrors the JS
// authority's per-program `canonicalKernel(context, out)` closures generated
// around `runCanonicalMrtPass`'s shared `out` scratch buffer
// (src/runtime/renderer.js:450-490): one kernel call produces every output
// for a pixel atomically, never one call per output.
using PixelFnMrt = void (*)(const KernelState&, const glsl::PixelContext&,
                            glsl::Vec4*) noexcept;

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

// Stateful handle for one bound multi-render-target ("MRT", drawBuffers >= 2)
// canonical factory. Mirrors BoundKernel exactly, generalized from one
// persistent `fragColor` register to `output_count()` persistent registers
// (one per declared output, in declaration order) -- the direct analog of
// the JS authority's per-output `Float32Array(4)` closure variables
// (`fragColor`, `geoOut`, `outXYZ`, ... allocated once per factory call in
// e.g. canonical-kernels.js, never per pixel). Pixel output state persists
// across run_pixel calls and is shared by copies, exactly like BoundKernel;
// the same concurrency caveat applies.
class BoundKernelMrt {
 public:
  // No derivative-quad-replay wrapper exists for this constructor yet: no
  // admitted MRT program uses dFdx/dFdy/fwidth (verified against every
  // pinned upstream MRT source), so `uses_derivatives` is refused rather
  // than silently ignored.
  BoundKernelMrt(std::shared_ptr<const KernelState> state, PixelFnMrt pixel,
                 std::size_t output_count, bool uses_derivatives = false,
                 PassContract pass_contract = {});

  // `outputs` must point at exactly `output_count()` writable Vec4 slots,
  // one per declared output in declaration order -- the same order
  // `run_mrt_pass`'s destination list and the admission's `outputs` ABI use.
  void run_pixel(const glsl::PixelContext& context,
                 glsl::Vec4* outputs) const noexcept;
  [[nodiscard]] std::size_t output_count() const noexcept;
  [[nodiscard]] bool uses_derivatives() const noexcept;
  [[nodiscard]] const PassContract& pass_contract() const noexcept;
  void validate_pass(std::size_t width, std::size_t height) const;

 private:
  std::shared_ptr<const KernelState> state_;
  PixelFnMrt pixel_;
  std::size_t output_count_;
  bool uses_derivatives_;
  PassContract pass_contract_;
  // One persistent register per declared output, exactly mirroring
  // BoundKernel::frag_color_ generalized to N slots: every generated MRT
  // pixel() function receives a pointer into this same persistent storage
  // (never a fresh per-call buffer), so a pixel invocation that returns
  // before writing every slot exposes whatever earlier call last wrote it --
  // matching the JS authority's own per-output closure-variable persistence.
  std::shared_ptr<std::vector<glsl::Vec4>> outputs_;
};

}  // namespace noisemaker
