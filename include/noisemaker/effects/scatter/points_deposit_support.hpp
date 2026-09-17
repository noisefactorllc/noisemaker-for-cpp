#pragma once

// Shared helpers ported from noisemaker-for-cpu's `src/effects/cpu/
// points-deposit.js` (module-level exports `GOLDEN_RATIO_CONJUGATE`,
// `fract`, `texelFetchAgent`, `scatterPointPixel`, `computeClipCenter`).
// Six JS scatter adapters import these from that one file rather than each
// re-typing them -- `points/dla:depositGrid`, `points/lenia:deposit`,
// `points/physarum:deposit`, and `render/pointsRender:deposit` (all defined
// alongside these helpers in points-deposit.js itself), plus
// `render/pointsBillboardRender:deposit` (billboard-deposit.js explicitly
// imports `computeClipCenter`, `fract`, `texelFetchAgent`,
// `GOLDEN_RATIO_CONJUGATE` from points-deposit.js) and
// `filter3d/flow3d:deposit` (flow3d-deposit.js imports `scatterPointPixel`,
// `texelFetchAgent`). This C++ header mirrors that sharing 1:1 -- ONE
// implementation each, reused by every C++ adapter file, so no two ports of
// the same JS function can silently drift apart from each other.
//
// Every function here operates in plain IEEE double precision, exactly like
// its JS source: none of `fract`/`texelFetchAgent`/`scatterPointPixel`/
// `computeClipCenter` ever calls `Math.fround` (grep-verified against
// points-deposit.js) -- so nothing here narrows to float32 either, except
// where reading directly from a `Surface`'s already-float32 storage
// (`texel_fetch_agent`, which is exactly `data[offset]` in JS: a read, not a
// round-tripping store).
//
// Transcendentals (`Math.cos`/`Math.sin`/`Math.tan` in `computeClipCenter`)
// go through `noisemaker::fdlibm` (V8-exact), never `std::` -- see
// noisemaker/fdlibm.hpp.

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::points_deposit {

// `GOLDEN_RATIO_CONJUGATE` (points-deposit.js:33) -- the golden-ratio
// low-discrepancy constant both density-cull adapters (`render/
// pointsRender:deposit`, `render/pointsBillboardRender:deposit`) multiply
// the raw particle index by before taking `fract`.
inline constexpr double kGoldenRatioConjugate = 0.618033988749895;

// `fract(value)` (points-deposit.js:35-37): `value - Math.floor(value)`,
// plain double, no narrowing.
[[nodiscard]] inline double js_fract(double value) noexcept {
  return value - std::floor(value);
}

// `Math.min(a, b)` / `Math.max(a, b)`, EXACTLY -- not `std::min`/`std::max`
// (whose NaN/sign-of-zero tie-break is unspecified and, empirically,
// disagrees with V8 for at least one argument order) and not
// `glsl::component_min<double>`/`component_max<double>` (which forces a
// CANONICAL NaN on either operand being NaN, whereas real V8 -- verified
// empirically against this Node build with a custom NaN payload injected
// via a DataView -- returns the FIRST NaN argument (scanning left to
// right) with its exact bit pattern preserved, never a re-materialized
// canonical NaN). These two mirror that measured behavior exactly: if `a`
// is NaN, return `a` unchanged; else if `b` is NaN, return `b` unchanged;
// else apply the ordinary value rule, with JS's signed-zero tie-break
// (`Math.min(-0, +0) === -0`; `Math.max(-0, +0) === +0`) when both operands
// compare equal to zero. Composing two calls left-associatively
// (`js_min(js_min(a, b), c)`) reproduces JS's variadic `Math.min(a, b, c)`
// exactly, including which of several simultaneous NaN arguments' payload
// survives -- verified against the same live V8 build for every argument
// order tested (see the points-deposit oracle report).
[[nodiscard]] double js_min(double a, double b) noexcept;
[[nodiscard]] double js_max(double a, double b) noexcept;

// `uniforms.viewMode | 0` and friends: JS's `ToInt32` bitwise-OR-with-zero
// truncation (ECMA-262 7.1.6) -- NaN/Infinity become 0, everything else
// truncates toward zero and wraps modulo 2^32 into a signed 32-bit int.
// Shared by `computeClipCenter`'s `viewMode` and (in the billboard adapter)
// `shapeMode`/`viewMode`/`blendMode`/`blurLayer`/the depth-sorted
// `particleId`. Deliberately re-derived here rather than reused from
// wormhole.cpp's private copy of the same rule: that copy is intentionally
// self-contained (see wormhole.hpp's port note), and this is a pure,
// stateless, three-line function -- duplicating it is lower-risk than
// coupling two otherwise-independent translation units.
[[nodiscard]] std::int32_t to_int32_or_zero(double value) noexcept;

// `texelFetchAgent(surface, sx, sy)` (points-deposit.js:44-53): clamp to
// bounds, then flip the GL (bottom-up) row into storage's top-down row. Real
// callers in every ported adapter only ever pass in-bounds coordinates
// (`v % w`, `floor(v / w)` for `v < w*h`, or an already-clamped-by-caller
// depth-sort index); the clamp is kept anyway for parity with the JS
// reference's own defensive clamp (and with `GlslCpuRuntime#texelFetch`,
// which it mirrors).
[[nodiscard]] Rgba texel_fetch_agent(const Surface& surface, std::int64_t sx, std::int64_t sy) noexcept;

// `scatterPointPixel(clipX, clipY, clipW, destWidth, destHeight)`
// (points-deposit.js:74-84): GPU 1-px-point rasterization equivalence.
// Returns the destination FLOAT-SPAN offset (already `* 4`, i.e. a direct
// index into `Surface::data()`) for the touched pixel, or `std::nullopt`
// when discarded (mirrors JS's `null`) -- non-finite NDC (a non-finite clip
// position) discards explicitly, before the ordinary bounds check, exactly
// like the JS reference's explicit `Number.isFinite` guard.
[[nodiscard]] std::optional<std::size_t> scatter_point_pixel(double clip_x, double clip_y, double clip_w,
                                                              std::int64_t dest_width,
                                                              std::int64_t dest_height) noexcept;

// The `uniforms` fields `computeClipCenter` reads, pre-resolved by the
// caller (adapters differ in which of these a pass actually binds; e.g.
// `posZ` is JS `uniforms.posZ ?? 0` -- the CALLER applies that fallback via
// `get_number_or` below before populating this struct, not this function).
struct ClipCenterUniforms {
  double view_mode = 0.0;
  double rotate_x = 0.0;
  double rotate_y = 0.0;
  double rotate_z = 0.0;
  double pos_x = 0.0;
  double pos_y = 0.0;
  double pos_z = 0.0;
  double view_scale = 0.0;
  // Only read when the resolved viewMode == 2 (perspective). Unlike
  // `pos_z`, JS reads `uniforms.fieldOfView` with NO `?? default` -- the
  // CALLER must pass NaN (not 0) here when the pass leaves it unbound, to
  // mirror `Math.max(undefined, 10)` coercing to NaN. Do not default this
  // field to 0.0 anywhere upstream (a real, caught divergence -- see
  // points_render.cpp's and points_billboard_render.cpp's own comments).
  double field_of_view = 0.0;
};

struct ClipCenter {
  double clip_x = 0.0;
  double clip_y = 0.0;
  double camera_depth = 0.0;
  double camera_distance = 0.0;
  double projected_scale = 0.0;
};

// `computeClipCenter(x, y, z, uniforms, destWidth, destHeight)`
// (points-deposit.js:108-170): shared clip-space CENTER computation, byte-
// identical between `render/pointsRender/glsl/deposit.vert` and `render/
// pointsBillboardRender/glsl/deposit.vert`. Returns `std::nullopt` exactly
// when the JS reference returns `null` (perspective view, at-or-behind the
// near plane).
[[nodiscard]] std::optional<ClipCenter> compute_clip_center(double x, double y, double z,
                                                             const ClipCenterUniforms& uniforms,
                                                             std::int64_t dest_width,
                                                             std::int64_t dest_height) noexcept;

// JS `uniforms.<name> ?? <fallback>`: several ported adapters bind a
// uniform only optionally (the pass may simply not declare it), and the JS
// side substitutes `fallback` only for `undefined`/`null` -- never for a
// present `0` or `NaN`. `glsl::Bindings::get_number` throws
// `KernelBindingError` for a name with no entry at all; this catches
// exactly that (an absent binding, matching JS `undefined`) and returns
// `fallback`, otherwise returns the real bound value unchanged.
[[nodiscard]] double get_number_or(const glsl::Bindings& bindings, std::string_view name, double fallback);

}  // namespace noisemaker::scatter::points_deposit
