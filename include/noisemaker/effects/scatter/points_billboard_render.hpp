#pragma once

// C++ port of `pointsBillboardRenderDepositAdapter` (noisemaker-for-cpu:
// src/effects/cpu/billboard-deposit.js) -- the scatter half of BOTH of
// `render/pointsBillboardRender`'s deposit pass records (`deposit`, blend
// `true` additive; `deposit_alpha`, blend `['ONE','ONE_MINUS_SRC_ALPHA']`
// premultiplied-over). Both share `program: "deposit"` and this ONE
// registration; the blend op is read off `pass.blend` per invocation (see
// `is_premultiplied_blend`), never assumed from which pass ran.
//
// Geometry: each particle is a rotated+scaled quad, rasterized by
// inverting the local affine offset map per candidate destination pixel
// (see billboard-deposit.js's file header for why this is exactly
// equivalent to the GPU's two-triangle rasterization for this shape, up to
// a measure-zero boundary-rule difference documented there).
//
// Numeric contract: plain IEEE double throughout EXCEPT `hash()`, which
// narrows through `Math.fround` exactly once (`Math.fround(n + seed)`,
// billboard-deposit.js:82) before hashing its bits -- billboard-deposit.js
// has exactly one `Math.fround` call, grep-verified. `Math.min`/`Math.max`
// go through `points_deposit::js_min`/`js_max` (payload-preserving NaN,
// JS's signed-zero tie-break -- see points_deposit_support.hpp), NOT
// `std::min`/`std::max` or `glsl::component_min`/`component_max`.
// `Math.sign` is ported locally as `js_sign` with the SAME payload-
// preserving NaN rule (verified against a live V8 build: `Math.sign` of a
// custom-payload NaN returns that exact NaN unchanged, not a
// re-materialized canonical one). `Math.cos`/`Math.sin`/`Math.exp` go
// through `noisemaker::fdlibm` (V8-exact); `Math.sqrt`/`Math.abs`/
// `Math.floor`/`Math.ceil` use `std::sqrt`/`std::fabs`/`std::floor`/
// `std::ceil` per this port's established convention (IEEE-correctly-
// rounded / exact-agreement functions need no fdlibm shim). Sprite
// sampling reuses the existing `noisemaker::sample_nearest_bottom_left`/
// `sample_bilinear_bottom_left` DOUBLE overloads directly (never the
// FLOAT overload, which would narrow `u`/`v` to float32 before sampling --
// billboard-deposit.js's own `u`/`v` pipeline is pure double, so narrowing
// them early would diverge).

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::points_billboard_render {

// deposit.vert's literal (slightly truncated) rotation-range constant --
// NOT `2 * Math.PI`; ported as the exact literal upstream authored.
inline constexpr double kTauApprox = 6.283185;

// `hash(n, seed)` (billboard-deposit.js:81-83). Exported for direct unit
// testing, matching the JS reference's own export for the same reason.
[[nodiscard]] double hash(double n, double seed) noexcept;

// `billboardShapeAlpha(shapeMode, u, v)` (billboard-deposit.js:142-147).
[[nodiscard]] double billboard_shape_alpha(std::int32_t shape_mode, double u, double v) noexcept;

// `evaluateBillboardFragment(shapeMode, spriteTex, u, v, agentColor,
// opacity, out)` (billboard-deposit.js:170-185). `agent_color`/`out` are
// plain double RGBA (JS uses PLAIN, non-typed arrays for these
// intermediates -- `pixelColor`/`src`/`sharpScratch`/`blurredScratch` are
// all `[0, 0, 0, 0]` literals, never a Float32Array -- so nothing narrows
// here except a genuine Surface sprite-texel read, which is already
// float32 at rest).
using Rgba64 = std::array<double, 4>;
void evaluate_billboard_fragment(std::int32_t shape_mode, const Surface& sprite_tex, double u, double v,
                                  const Rgba64& agent_color, double opacity, Rgba64& out) noexcept;

// `isPremultipliedBlend(pass)` (billboard-deposit.js:191-195), operating on
// `ScatterPass::blend_factors` rather than a raw JS `pass` object -- see
// registry.hpp.
[[nodiscard]] bool is_premultiplied_blend(const ScatterPass& pass) noexcept;

// The `uniforms` fields this adapter reads beyond what
// `points_deposit::ClipCenterUniforms` already carries (density/viewMode/
// rotate*/pos*/viewScale/fieldOfView -- passed to `computeClipCenter`
// internally by `run_deposit`).
struct Uniforms {
  double density = 0.0;
  double view_mode = 0.0;
  double rotate_x = 0.0;
  double rotate_y = 0.0;
  double rotate_z = 0.0;
  double pos_x = 0.0;
  double pos_y = 0.0;
  double pos_z = 0.0;      // JS `uniforms.posZ ?? 0`
  double view_scale = 0.0;
  double field_of_view = 0.0;
  double shape_mode = 0.0;       // JS `uniforms.shapeMode | 0`
  double blend_mode = 0.0;       // JS `uniforms.blendMode | 0`
  double blur_layer = 0.0;       // JS `(uniforms.blurLayer ?? 0) | 0`
  double deposit_opacity = 0.0;  // JS `uniforms.depositOpacity / 100.0`
  double seed = 0.0;
  double size_variation = 0.0;      // JS `uniforms.sizeVariation / 100.0`
  double rotation_var = 0.0;        // JS `uniforms.rotationVar / 100.0`
  double point_size = 0.0;
  double size_distance = 0.0;       // JS `uniforms.sizeDistance ?? 0`
  double brightness_distance = 0.0; // JS `uniforms.brightnessDistance ?? 0`
  double aperture = 0.0;            // JS `uniforms.aperture ?? 0`
  double focal_distance = 80.0;     // JS `uniforms.focalDistance ?? 80`
};

// `xyz_tex`/`rgba_tex`/`order_tex`/`sprite_tex`/`sprite_mean_tex` mirror JS
// `inputs.xyzTex`/`rgbaTex`/`orderTex`/`spriteTex`/`spriteMeanTex`.
[[nodiscard]] std::size_t run_deposit(const Surface& xyz_tex, const Surface& rgba_tex, const Surface& order_tex,
                                       const Surface& sprite_tex, const Surface& sprite_mean_tex,
                                       const Uniforms& uniforms, const ScatterPass& pass, Surface& destination);

// Registers "render/pointsBillboardRender:deposit". Called from
// register_builtin_scatter_adapters().
void register_adapter();

}  // namespace noisemaker::scatter::points_billboard_render
