#include "noisemaker/effects/remap.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <memory>
#include <string>

#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/sampler.hpp"
#include "noisemaker/surface.hpp"

// Hand-written CPU kernel for synth/remap:remap.
//
// Route rationale (see include/noisemaker/effects/remap.hpp for the short
// version): the new upstream remap.glsl introduces `struct ZoneTest { bool
// inside; float d2; }`, the same construct that already made the
// authority's own JS glsl-transpiler give up (see the authority's
// src/effects/adapters/remap.js header comment) and fall back to a
// hand-written adapter. Unlike the corpus's other three corpus-status
// "adapter" programs (synth/julia, classicNoisedeck/fractal,
// filter/palette, filter/historicPalette), whose JS adapters are faithful
// float32 mirrors of their GLSL (explicit Math.fround at every point that
// matters) and so remain typed-generation-compatible, remap.js has zero
// Math.fround calls anywhere in its body: every intermediate (edge tests,
// squared distances, smoothstep, premultiplied compositing) is plain
// double-precision JS-number math, rounded to float32 only once, by the
// Float32Array store the runtime writes `out[]` into.
//
// A typed-generated C++ kernel necessarily rounds to float32 after every
// operation, mirroring GLSL's mandated per-operation float semantics --
// that is what "typed generation" means. Double rounding (compute in wide
// precision, round once) is not in general equal to single rounding after
// every step. An empirical probe (double-throughout vs. float32-per-op,
// same operation order, a diagonal-edged feathered triangle over ~64k
// pixels) found the two disagree in the last mantissa bit for about 11.65%
// of pixels touched by the distance/smoothstep math -- and feathering
// (smoothEdge > 0) is core, documented functionality, not a corner case.
// Typed generation therefore cannot be bit-exact against this authority for
// this program. This kernel instead mirrors remap.js operation-for-
// operation: plain `double` throughout, `noisemaker::f32()` applied only at
// the four `out[]` writes at the very end, exactly where the authority's
// Float32Array store rounds.
//
// Every uniform below is read directly from `Bindings` at bind time (never
// per pixel), matching `src/effects/bit_effects.cpp`'s State pattern. Zone
// geometry, bounds and color are read as `glsl::DVec3`/`glsl::DVec4`
// (double lanes), not `Vec3`/`Vec4` (float lanes): the authority's semantic
// bindings are plain, unrounded JS numbers (`$bindings.zone{N}_bounds`,
// `...v{pair}`, `.bgColor`, ...), authored at arbitrary precision -- a
// float32-lane read would silently round them on the way in and reintroduce
// exactly the divergence the double-precision body is trying to avoid.
namespace noisemaker::effects {
namespace {

using glsl::DVec3;
using glsl::DVec4;
using glsl::Vec2;
using glsl::Vec4;

constexpr int kMaxZones = 8;
constexpr int kMaxPairs = 32;  // MAX_VERTS_PER_ZONE / 2 in the reference GLSL

// One zone's resolved bindings, read once at bind time. Mirrors the
// $bindings.zone{N}_* reads in remap.js's per-pixel kernel and its own
// authority-side "?? default" fallbacks exactly.
struct ZoneState {
  double count = 0.0;
  double active = 0.0;
  double alpha = 1.0;
  DVec4 bounds{0.0, 0.0, 1.0, 1.0};
  std::array<DVec4, kMaxPairs> verts{};  // default (0,0,0,0) per pair
  const Surface* texture = nullptr;
};

struct State final : KernelState {
  Vec2 tile_offset{0.0F, 0.0F};
  Vec2 full_resolution{0.0F, 0.0F};
  Vec2 resolution{0.0F, 0.0F};
  double zone_count = 0.0;
  double smooth_edge = 0.0;
  DVec3 bg_color{0.0, 0.0, 0.0};
  double bg_alpha = 1.0;
  std::array<ZoneState, kMaxZones> zones{};
};

// Mirrors remap.js's local clamp()/smoothstep() exactly: plain double math,
// matching the authority's own local helpers of the same name.
[[nodiscard]] double remap_clamp(double value, double low, double high) noexcept {
  return std::min(std::max(value, low), high);
}
[[nodiscard]] double remap_smoothstep(double edge0, double edge1, double x) noexcept {
  const double t = remap_clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
  return t * t * (3.0 - 2.0 * t);
}

// Mirrors the authority's texture() dispatch (src/csl/glsl-runtime.js
// GlslCpuRuntime#texture): bilinear when the surface asks for it, nearest
// otherwise, both bottom-left-origin. Uses the double-precision sampler
// overloads directly -- sampleUv in the authority is never rounded to
// float32 before the floor/clamp inside the sampler, so neither is this.
[[nodiscard]] Rgba sample_zone_texture(const Surface& surface, double u, double v) noexcept {
  if (surface.filter() == TextureFilter::linear) {
    return sample_bilinear_bottom_left(surface, u, v);
  }
  return sample_nearest_bottom_left(surface, u, v);
}

struct ZoneTest {
  bool inside = false;
  double d2 = 1e30;
};

// Mirrors remap.js's testEdge() exactly, including operator/operand order.
void test_edge(ZoneTest& t, double ax, double ay, double bx, double by,
               double qx, double qy, bool need_dist) noexcept {
  const double ex = bx - ax;
  const double ey = by - ay;
  const double wx = qx - ax;
  const double wy = qy - ay;
  const bool c1 = qy >= ay;
  const bool c2 = qy < by;
  const bool c3 = ex * wy > ey * wx;
  if ((c1 && c2 && c3) || !(c1 || c2 || c3)) t.inside = !t.inside;
  if (need_dist) {
    const double s = remap_clamp((wx * ex + wy * ey) / std::max(ex * ex + ey * ey, 1e-6),
                                 0.0, 1.0);
    const double rx = wx - ex * s;
    const double ry = wy - ey * s;
    const double d2 = rx * rx + ry * ry;
    if (d2 < t.d2) t.d2 = d2;
  }
}

// Mirrors remap.js's walkZone() exactly: one uniform fetch per packed
// vertex pair, closing the polygon from the last vertex.
[[nodiscard]] ZoneTest walk_zone(const ZoneState& zone, int n, double full_res_x,
                                 double full_res_y, double qx, double qy,
                                 bool need_dist) noexcept {
  ZoneTest t;
  const int last = n - 1;
  const DVec4& last_pack = zone.verts[static_cast<std::size_t>(last >> 1)];
  double prev_x = 0.0;
  double prev_y = 0.0;
  if (last % 2 == 0) {
    prev_x = last_pack[0] * full_res_x;
    prev_y = last_pack[1] * full_res_y;
  } else {
    prev_x = last_pack[2] * full_res_x;
    prev_y = last_pack[3] * full_res_y;
  }
  const int pairs = (n + 1) >> 1;
  for (int pair = 0; pair < kMaxPairs; ++pair) {
    if (pair >= pairs) break;
    const DVec4& pack = zone.verts[static_cast<std::size_t>(pair)];
    const double v0x = pack[0] * full_res_x;
    const double v0y = pack[1] * full_res_y;
    test_edge(t, v0x, v0y, prev_x, prev_y, qx, qy, need_dist);
    prev_x = v0x;
    prev_y = v0y;
    if (pair * 2 + 1 < n) {
      const double v1x = pack[2] * full_res_x;
      const double v1y = pack[3] * full_res_y;
      test_edge(t, v1x, v1y, prev_x, prev_y, qx, qy, need_dist);
      prev_x = v1x;
      prev_y = v1y;
    }
  }
  return t;
}

// Mirrors remap.js's remapKernel() exactly, including operation order.
void pixel(const KernelState& base, const glsl::PixelContext& ctx, Vec4& out) noexcept {
  const auto& s = static_cast<const State&>(base);
  const double frag_x = static_cast<double>(ctx.frag_coord[0]);
  const double frag_y = static_cast<double>(ctx.frag_coord[1]);
  const double tile_offset_x = static_cast<double>(s.tile_offset[0]);
  const double tile_offset_y = static_cast<double>(s.tile_offset[1]);
  const double full_res_x = static_cast<double>(s.full_resolution[0]);
  const double full_res_y = static_cast<double>(s.full_resolution[1]);

  // Polygon tests use the GLOBAL pixel position so zones land in the same
  // image position regardless of which tile is rendering; remap JSON is
  // top-left (Y-down), so flip y after the global-coord conversion.
  const double global_x = frag_x + tile_offset_x;
  const double global_y = frag_y + tile_offset_y;
  const double qx = global_x;
  const double qy = full_res_y - global_y;
  const double px = qx / full_res_x;
  const double py = qy / full_res_y;

  // Texture sampling stays TILE-LOCAL: sample at the tile-local pixel
  // position against this pass's own render-target resolution.
  const double resolution_x = static_cast<double>(s.resolution[0]);
  const double resolution_y = static_cast<double>(s.resolution[1]);
  const double sample_u = frag_x / resolution_x;
  const double sample_v = frag_y / resolution_y;

  const int active_count = std::min(static_cast<int>(std::trunc(s.zone_count)), kMaxZones);
  // Feather width in pixels, proportional to the shorter canvas side.
  // smoothEdge is clamped at 0: a negative value would otherwise SHRINK
  // every zone's reject box below.
  const double feather_px =
      std::max(s.smooth_edge, 0.0) * 0.05 * std::min(full_res_x, full_res_y);
  const bool need_dist = feather_px > 0.0;
  const double dilate_x = feather_px / full_res_x;
  const double dilate_y = feather_px / full_res_y;

  double r = 0.0;
  double g = 0.0;
  double b = 0.0;
  double a = 0.0;
  for (int k = 0; k < kMaxZones; ++k) {
    const int z = active_count - 1 - k;  // top-down: highest index first
    if (z < 0) break;
    const ZoneState& zone = s.zones[static_cast<std::size_t>(z)];
    // Clamped: a host-supplied count above the per-zone capacity would
    // otherwise walk past this zone's slots into the next zone's.
    const int n = std::min(static_cast<int>(std::trunc(zone.count)), kMaxPairs * 2);
    if (n < 3 || zone.active < 0.5) continue;  // degenerate, or source not wired

    // Host-supplied bounding box [minX, minY, maxX, maxY], dilated by the
    // feather. The default [0, 0, 1, 1] never rejects a canvas pixel.
    const DVec4& bounds = zone.bounds;
    if (px < bounds[0] - dilate_x || py < bounds[1] - dilate_y ||
        px > bounds[2] + dilate_x || py > bounds[3] + dilate_y) {
      continue;
    }

    const ZoneTest t = walk_zone(zone, n, full_res_x, full_res_y, qx, qy, need_dist);

    double coverage = 1.0;
    if (!t.inside) {
      if (!need_dist) continue;
      coverage = 1.0 - remap_smoothstep(0.0, feather_px, std::sqrt(t.d2));
      if (coverage <= 0.0) continue;
    }

    // Premultiplied "under": this zone is above everything still to come.
    // zone.texture is resolved once at bind time for every one of the 8
    // zone slots (see bind_remap): the GLSL/DSL ABI always wires all 8
    // zone{N}_tex samplers, active or not, exactly as the packed std140
    // block's 8 always-present sampler uniforms require.
    const Rgba src = sample_zone_texture(*zone.texture, sample_u, sample_v);
    const double weight = coverage * zone.alpha;
    const double inv = 1.0 - a;
    r += static_cast<double>(src[0]) * weight * inv;
    g += static_cast<double>(src[1]) * weight * inv;
    b += static_cast<double>(src[2]) * weight * inv;
    a += static_cast<double>(src[3]) * weight * inv;
    if (a >= 0.999) break;
  }

  // Background goes under whatever the zones left uncovered.
  const double inv = 1.0 - a;
  r += s.bg_color[0] * s.bg_alpha * inv;
  g += s.bg_color[1] * s.bg_alpha * inv;
  b += s.bg_color[2] * s.bg_alpha * inv;
  a += s.bg_alpha * inv;

  out[0] = noisemaker::f32(r);
  out[1] = noisemaker::f32(g);
  out[2] = noisemaker::f32(b);
  out[3] = noisemaker::f32(a);
}

}  // namespace

BoundKernel bind_remap(const glsl::Bindings& b) {
  auto state = std::make_shared<State>();
  state->tile_offset = b.get_or<Vec2>("tileOffset", Vec2(0.0F, 0.0F));
  state->full_resolution = b.get<Vec2>("fullResolution");
  state->resolution = b.get<Vec2>("resolution");
  state->zone_count = b.get_or<double>("zoneCount", 0.0);
  state->smooth_edge = b.get_or<double>("smoothEdge", 0.0);
  state->bg_color = b.get_or<DVec3>("bgColor", DVec3(0.0, 0.0, 0.0));
  state->bg_alpha = b.get_or<double>("bgAlpha", 1.0);
  for (int zone = 0; zone < kMaxZones; ++zone) {
    const std::string prefix = "zone" + std::to_string(zone) + "_";
    ZoneState& zs = state->zones[static_cast<std::size_t>(zone)];
    zs.count = b.get_or<double>(prefix + "count", 0.0);
    zs.active = b.get_or<double>(prefix + "active", 0.0);
    zs.alpha = b.get_or<double>(prefix + "alpha", 1.0);
    zs.bounds = b.get_or<DVec4>(prefix + "bounds", DVec4(0.0, 0.0, 1.0, 1.0));
    for (int pair = 0; pair < kMaxPairs; ++pair) {
      zs.verts[static_cast<std::size_t>(pair)] =
          b.get_or<DVec4>(prefix + "v" + std::to_string(pair), DVec4(0.0, 0.0, 0.0, 0.0));
    }
    zs.texture = &b.texture(prefix + "tex");
  }
  return BoundKernel(state, &pixel);
}

}  // namespace noisemaker::effects
