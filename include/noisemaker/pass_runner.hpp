#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "noisemaker/kernel.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker {

[[nodiscard]] Surface run_pass(const BoundKernel& kernel, std::size_t width,
                               std::size_t height, float time = 0.0f,
                               float seed = 1.0f, std::uint32_t frame = 0,
                               float delta_time = 0.0f);

// The generic multi-render-target pass runner: mirrors the JS authority's
// `runCanonicalMrtPass`/`Async` (src/runtime/renderer.js:450-490) exactly --
// one shared per-pixel loop calls `kernel` ONCE per pixel, producing every
// one of `kernel.output_count()` outputs atomically into one scratch
// buffer, then scatters each output's 4 lanes into its own destination
// Surface. Every returned Surface shares this one `width`/`height`, by
// construction -- exactly like `run_pass`'s single Surface.
//
// This mirrors `runCanonicalMrtPass` itself, which also takes one
// `width`/`height` (derived from `destinations[0]`) and does not re-check
// the other destinations. The dimension-agreement check belongs one layer
// up, where JS puts it: `canonicalMrtDestinations`/`groupMrtDestinations`
// (renderer.js:519-533,806-814) independently resolve each output's own
// texture spec to a size and call `assertMrtDestinationsShareDimensions`
// BEFORE this pixel loop ever runs -- the C++ analog is the executor's own
// destination-resolution step (mirroring `canonicalMrtDestinations`), which
// must perform that same assertion before calling `run_mrt_pass` with the
// now-agreed single size.
//
// The returned surfaces are raw float32, in the same "quantize off-route"
// convention as `run_pass`: storage layout, coordinate convention (bottom-
// left origin, `fragCoord=(x+0.5, height-y-0.5)`), and quantization are
// identical to the single-output path -- callers quantize each returned
// Surface exactly as they would run_pass's result, via the same
// `quantize_texture`.
[[nodiscard]] std::vector<Surface> run_mrt_pass(
    const BoundKernelMrt& kernel, std::size_t width, std::size_t height,
    float time = 0.0f, float seed = 1.0f, std::uint32_t frame = 0,
    float delta_time = 0.0f);

}  // namespace noisemaker
