#pragma once

// C++ port of `runWormholeDeposit` (noisemaker-for-cpu:
// src/effects/cpu/wormhole.js:34-76) -- the scatter half of
// `filter/wormhole:deposit`. Verified bit-exact against a machine-checked JS
// oracle (62 cases spanning all three wrap modes, odd/non-square/power-of-two
// canvas sizes, collisions, out-of-bounds wraps, and negative-modulo inputs;
// 9 mutation-tested behaviors; see wormhole-report.md for the full
// methodology and results). This header is the reviewed, ready-to-apply
// version of the standalone proof-of-concept at
// docs/port-engineering/wormhole/cpp/wormhole_deposit.hpp, retargeted
// from a throwaway standalone Surface onto the real `noisemaker::Surface`.
//
// PRECISION CONTRACT -- see the standalone header for the full rationale;
// summarized here:
//   - Every intermediate value is a `double`. `f32r()` performs the
//     "round-trip through float and back to double" that JS `Math.fround`
//     does; `add`/`mul`/`divd` each apply it exactly once, exactly where the
//     JS source does. Never flatten a chained add(add(mul(...),mul(...)))
//     expression -- that skips intermediate roundings later terms depend on.
//   - `-ffp-contract=off` (already the project-wide default per
//     CMakeLists.txt) keeps the compiler from fusing any `a*b+c` shape into
//     an FMA; this codebase's per-operation-rounding style also blocks
//     contraction structurally (each rounding is a real, observable
//     `static_cast<float>`), but the flag stays mandatory as defense in
//     depth.
//   - `div(1, 3)` (the OKLab cube-root exponent) is F32-rounded BEFORE
//     `pow`, not `1.0 / 3.0`.
//   - `pixelStride = 1024 * uniforms.stride` is double precision, never
//     pre-narrowed (see wormhole-report.md's `pixel_stride_rounding_proof`
//     for why this happens to be provably unobservable for this specific
//     multiplier -- documented rather than relied upon).
//   - Vertex IDs are bottom-up: `row = height - 1 - y` for BOTH the source
//     read and the destination write.
//   - `weight = mul(lightness, lightness)`; every accumulated RGB channel
//     round-trips through `float16_truncate` (a real rgba16f store,
//     truncating not rounding); alpha is never touched.
//   - `wrapMirror` has a genuine off-by-one for `value ≡ -1 (mod 2*size)`
//     (returns exactly -1, proven by exhaustive sweep in wormhole-report.md)
//     which in JS silently no-ops the destination TypedArray write. This
//     port reproduces that exactly via a flat-offset bounds check -- NOT by
//     clamping X/Y independently, which would silently drop writes JS
//     actually performs (an out-of-range X with an in-range row can alias
//     into the previous row's last pixel, which JS really does write to).
#include <cstddef>

#include "noisemaker/surface.hpp"

namespace noisemaker::scatter::wormhole {

struct Uniforms {
  double kink = 1.0;
  double stride = 1.0;
  double rotation = 0.0;
  double wrap = 1.0;  // 0 = mirror, 2 = clamp, anything else = repeat (matches `uniforms.wrap | 0` dispatch)
};

// Accumulates `input` into `destination` IN PLACE (never clears it -- the
// caller pre-seeds it with the previous accum-texture contents, exactly like
// the JS adapter contract). Throws `std::invalid_argument` if the two
// surfaces' dimensions don't match, matching the JS reference's own guard.
void run_deposit(const Surface& input, Surface& destination, const Uniforms& uniforms);

// Registers the "filter/wormhole:deposit" scatter adapter (see
// noisemaker/effects/scatter/registry.hpp). Called from
// `register_builtin_scatter_adapters()`
// (noisemaker/effects/scatter/catalog.hpp) -- never as a static initializer.
void register_adapter();

}  // namespace noisemaker::scatter::wormhole
