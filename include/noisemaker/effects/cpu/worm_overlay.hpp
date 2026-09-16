#pragma once

// C++ port of the authority's canonical CPU worm-overlay adapter
// (noisemaker-for-cpu: src/effects/cpu/worm-overlay.js, 181 lines), wired
// from `src/runtime/renderer.js`'s `initializeCanonicalResources()` for the
// three effects whose `overlayTex` has no pass producer: `filter/fibers`,
// `filter/scratches`, `filter/strayHair`. See
// docs/port-engineering/worm-overlay-parity/ for the oracle, mutation
// testing, and full methodology writeup.
//
// PRECISION CONTRACT:
//   - Every intermediate value is a `double`, matching JS's default number
//     type. The only narrowing points are the ones the authority itself
//     narrows: every store into the overlay `Surface`'s backing storage
//     (`std::vector<float>`, matching a JS `Float32Array`) rounds through
//     `noisemaker::f32()` (== `Math.fround`), exactly where the authority's
//     `Float32Array` assignment operator would.
//   - `Math.log` and `Math.hypot` are NOT platform libm: V8's `Math.log`
//     diverges from `std::log` at ~1-7% of double inputs (measured; see
//     `include/noisemaker/fdlibm.hpp`), and `Math.hypot` has no fdlibm
//     ancestor at all (V8's own scaled Kahan-sum algorithm) and diverges
//     from platform `std::hypot` at ~18% of inputs (measured; see
//     docs/port-engineering/worm-overlay-parity/hypot-differential-report.md).
//     Both route through `noisemaker::fdlibm::{log,hypot}`. `Math.sin`,
//     `Math.cos` route through the pre-existing `noisemaker::fdlibm::{sin,cos}`.
//     `Math.sqrt`, `Math.floor`, `Math.ceil`, `Math.abs`, `Math.min`,
//     `Math.max` are plain IEEE-754 double operations with no cross-runtime
//     divergence risk and use `std::` directly.
//   - JS `%` (remainder, sign follows the dividend) is `std::fmod`, never
//     `noisemaker::glsl_mod` (GLSL `mod()` is floored division -- a
//     different, wrong-sign-for-negative-input operation).
//   - `Math.round` on this function's always-non-negative domain ([0,1]
//     clamped, times 255) is `std::floor(x + 0.5)`, matching this
//     codebase's own established idiom for the same JS semantic
//     (src/surface.cpp's `byte_from_float`, src/texture_format.cpp).
//   - The RNG's `seed >>> 0` (ECMA-262 ToUint32) is ported exactly
//     (truncate-toward-zero, then reduce modulo 2^32, not `glsl`/C++'s
//     implicit unsigned-conversion semantics, which differ for negative or
//     huge fractional doubles).
//
// SCOPE NOTE: the authority's `renderer.js` only calls this function when
// `renderOptions.oneShot !== 'initial'` (the `'initial'` mode instead
// zero-fills `overlayTex`, skipping this adapter entirely). This port's
// executor integration (src/graph/executor.cpp) has no representation of
// that `'initial'` shortcut at all -- `graph::ExecutionInputs::one_shot` is
// a single bool that already corresponds to the authority's *default*
// (`'ready'`) mode, not to the `'initial'` bypass -- so this adapter always
// computes the real overlay, exactly matching what the authority does for
// every render this port can currently drive. See the executor wiring
// comment at `is_worm_overlay_resource` for detail.

#include <cstddef>
#include <string_view>

#include "noisemaker/surface.hpp"

namespace noisemaker::effects::cpu {

// True for exactly the three effect ids the authority routes through this
// adapter (`filter/fibers`, `filter/scratches`, `filter/strayHair`).
// Mirrors `is_worm_overlay_resource`'s effect-id half in
// src/graph/executor.cpp -- kept here too so callers outside the executor
// (tests, tools) don't need to duplicate the id list.
[[nodiscard]] bool is_worm_overlay_effect(std::string_view effect_id) noexcept;

// Computes the deterministic worm-overlay texture for `effect_id` at
// `width`x`height`, given the effect's own bound `seed` and `density`
// parameters (NOT the render-level seed). Mirrors
// `renderCanonicalWormOverlay(effectId, width, height, params)` exactly:
//   - `seed_param` follows JS `params.seed || 1` (any falsy value --
//     +0, -0, or NaN -- resolves to 1; any other finite value, including
//     negative or fractional, passes through unchanged).
//   - `density_param` passes through unchanged (no fallback, matching the
//     authority: an effect definition that fails to bind `density` is
//     itself an executor bug, not something this function papers over).
// Throws `std::invalid_argument` for any other `effect_id`, matching the
// authority's `throw new Error(...)`.
[[nodiscard]] Surface render_canonical_worm_overlay(std::string_view effect_id,
                                                     std::size_t width,
                                                     std::size_t height,
                                                     double seed_param,
                                                     double density_param);

}  // namespace noisemaker::effects::cpu
