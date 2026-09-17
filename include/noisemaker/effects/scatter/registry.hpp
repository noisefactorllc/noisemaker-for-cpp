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
//   - Adapter signature: `(const glsl::Bindings&, const ScatterPass&,
//     Surface& destination) -> std::size_t`. `bindings` is the SAME
//     `glsl::Bindings` an ordinary `bind_*` kernel factory already receives
//     (see `noisemaker/generated/catalog.hpp`) -- ONE uniform/texture-
//     resolution code path for both pass shapes, not a second parallel one.
//     `bindings` supplies both the scatter's uniforms (`get_number`/
//     `get<T>`) and its input texture(s) (`texture(name)`) -- multiple
//     named input textures (JS's `inputs: { uniformName: Surface }`) need no
//     extra machinery either, since `Bindings::set_texture`/`texture(name)`
//     already key by name.
//   - `pass` carries the SAME minimal slice of the JS `pass` record
//     (`registry.hpp`'s `ScatterPass`, see below) that the JS scatter
//     adapters actually read off their own `pass` parameter --
//     `pass.blend` (`render/pointsBillboardRender:deposit`'s
//     `isPremultipliedBlend`) and `pass.count` (`filter3d/flow3d:deposit`).
//     This was added (wormhole shipped without it) once porting the six
//     remaining adapters showed two of them genuinely read `pass` fields
//     `bindings`/`inputs`/`destination` cannot carry; every other JS `pass`
//     field (`name`, `program`, `inputs`, `outputs`, `uniforms`) is either
//     already carried elsewhere in this signature or unread by any shipped
//     adapter (including wormhole, which takes a `ScatterPass` purely for a
//     uniform function-pointer type and never reads it), so `ScatterPass`
//     stays exactly as wide as what is observably read -- not as wide as
//     the JS `pass` object's full shape, and JS's scalar `bindings` context
//     (`time`/`frame`/`seed`/...) and `params` are deliberately NOT added:
//     no shipped adapter, old or new, reads either.
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
// DISPATCH SITE: `GraphExecutor::execute` (src/graph/executor.cpp) gains
// exactly one new branch, mirroring `renderer.js`'s own
// `pass.drawMode === 'points' || pass.drawMode === 'billboards'` check:
//
//   if (pass.draw_mode == DrawMode::Points || pass.draw_mode == DrawMode::Billboards) {
//     const ScatterAdapter adapter = resolve_scatter_adapter(scatter_key);
//     if (adapter == nullptr) throw std::runtime_error("missing scatter adapter: " + scatter_key);
//     adapter(bindings, scatter_pass, destination);
//   } else {
//     destination = run_pass(bound_kernel, width, height, ...);
//   }
//
// The executor builds `scatter_pass` itself, generically, from the compiled
// `effects::PassDefinition` (`pass.blend`/`pass.count`) rather than any
// per-effect special case -- see `scatter_pass_from_definition` in
// executor.cpp.

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker::scatter {

// The minimal slice of a JS scatter `pass` record that any shipped adapter
// actually reads (see the header comment above for the full rationale).
struct ScatterPass {
  // `pass.blend`, ONLY when it is a two-element array (JS's
  // `Array.isArray(pass.blend)` true branch) -- e.g. `{"ONE",
  // "ONE_MINUS_SRC_ALPHA"}`. `std::nullopt` covers every other JS shape
  // (`true`, `false`, `undefined`/absent), matching
  // `isPremultipliedBlend`'s `!Array.isArray(pass.blend)` early `false`.
  // Values are compared case-insensitively at the one read site
  // (`points_billboard_render::is_premultiplied_blend`), matching JS's
  // `String(x).toUpperCase()`.
  std::optional<std::pair<std::string, std::string>> blend_factors;
  // `pass.count`, when the pass record has one (JS `pass?.count`).
  // `std::nullopt` mirrors JS `undefined` (no `count` field at all, or no
  // `pass` object) at the one read site (`flow3dDepositAdapter`'s
  // `pass?.count ?? capacity`) -- a `double` rather than an integer type
  // because JS's `??`/`Math.min` never coerce or truncate `pass.count`
  // before comparing it against the other two (already-integer-valued)
  // operands.
  std::optional<double> count;
};

using ScatterAdapter = std::size_t (*)(const glsl::Bindings& bindings, const ScatterPass& pass, Surface& destination);

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
