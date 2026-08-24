#pragma once

// Registry of hand-written C++ "scatter" adapters for vertex-stage
// (`drawMode: "points"` / `"billboards"`) passes -- the C++ analog of
// noisemaker-for-cpu's `src/effects/cpu/scatter-registry.js`.
//
// WHY THIS EXISTS: `run_pass` (noisemaker/pass_runner.hpp) is a per-pixel
// GATHER -- it calls a `BoundKernel`'s pixel function once per DESTINATION
// pixel and fills every output pixel exactly once. A handful of upstream
// programs (wormhole's `deposit`, and per the JS scatter-registry.js header
// comment: DLA's `depositGrid`, Lenia's `deposit`, Physarum's `deposit`,
// pointsRender's `deposit`, pointsBillboardRender's `deposit`, and flow3d's
// `deposit` -- seven programs total, six beyond wormhole) are SCATTER passes
// instead: they rasterize a variable number of points/quads per SOURCE
// pixel, landing on a variable number of destination pixels (zero, one, or
// several source pixels can address the same destination pixel, and
// -- see wormhole's own report -- a source can even address no destination
// pixel at all, matching a real JS TypedArray out-of-range write no-op).
// That shape does not fit `run_pass`'s "exactly once per destination pixel"
// contract, so it needs its own dispatch -- exactly the reason JS carved
// `scatter-registry.js` out of the ordinary GLSL-kernel path.
//
// DESIGN, mirroring the JS contract 1:1 so the six remaining adapters need
// no new machinery when they're ported:
//   - Adapter signature: `(const glsl::Bindings&, Surface& destination) ->
//     std::size_t`. `bindings` is the SAME `glsl::Bindings` an ordinary
//     `bind_*` kernel factory already receives (see
//     `noisemaker/generated/catalog.hpp`) -- ONE uniform/texture-resolution
//     code path for both pass shapes, not a second parallel one. `bindings`
//     supplies both the scatter's uniforms (`get_number`/`get<T>`) and its
//     input texture(s) (`texture(name)`).
//   - `destination` is the output Surface, pre-seeded by the (future)
//     multi-pass driver with the previous contents of the named output
//     texture (or cleared, if none) -- the adapter accumulates into it IN
//     PLACE, exactly like the JS contract; the driver quantizes/stores the
//     result afterward like any other pass.
//   - Return value mirrors JS's `{ pixels }` -- the count of source pixels
//     processed, for parity with existing pass-stats plumbing and tests.
//   - Adapters are keyed by the SAME `"${effectId}:${program}"` string the
//     manifest/pass data already carries (identical to how JS keys
//     `scatter-registry.js`), so whatever future structure drives pass
//     dispatch (reading the ported manifest's `drawMode` field) needs no
//     per-effect special-casing -- one string lookup, same shape as a
//     BoundKernel lookup.
//   - Registration is EXPLICIT (`register_scatter_adapter`, called from each
//     effect's own `register_*` function, aggregated in
//     `noisemaker/effects/scatter/catalog.hpp`'s
//     `register_builtin_scatter_adapters()`) -- never a global/static
//     constructor. This matches the existing codebase's preference (flat
//     `bind_*` declarations in `generated/catalog.hpp`, no self-registering
//     statics anywhere in `src/generated` or `src/typed_generated`) and
//     avoids static-initialization-order hazards across translation units.
//
// FUTURE DISPATCH SITE (not yet built -- see wormhole-report.md's
// integration section): whatever eventually plays `renderer.js`'s role of
// iterating an effect's `pass` list and calling `run_pass` per pass should
// gain exactly one new branch, mirroring `renderer.js`'s own
// `pass.drawMode === 'points' || pass.drawMode === 'billboards'` check:
//
//   if (pass.draw_mode == DrawMode::Points || pass.draw_mode == DrawMode::Billboards) {
//     const ScatterAdapter adapter = resolve_scatter_adapter(scatter_key);
//     if (adapter == nullptr) throw std::runtime_error("missing scatter adapter: " + scatter_key);
//     adapter(bindings, destination);
//   } else {
//     destination = run_pass(bound_kernel, width, height, ...);
//   }
//
// That branch is the ENTIRE integration surface -- everything else (Surface
// lifetime, uniform binding, quantization, output storage) is already
// shared with the gather path.

#include <cstddef>
#include <string_view>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker::scatter {

using ScatterAdapter = std::size_t (*)(const glsl::Bindings& bindings, Surface& destination);

// Registers `adapter` under `key` (e.g. "filter/wormhole:deposit"). Throws
// `std::invalid_argument` if `key` is empty or already registered -- a
// silently-overwritten adapter is exactly the kind of bug this registry
// exists to make impossible to introduce by accident.
void register_scatter_adapter(std::string_view key, ScatterAdapter adapter);

// Returns nullptr if `key` has no registered adapter (mirrors JS
// `resolveScatterAdapter`'s `undefined` return -- callers decide whether a
// missing adapter is a hard error, exactly like the JS renderer does at its
// call sites).
[[nodiscard]] ScatterAdapter resolve_scatter_adapter(std::string_view key) noexcept;

}  // namespace noisemaker::scatter
