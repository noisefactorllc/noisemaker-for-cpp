// Standalone, self-contained C++20 port of `runWormholeDeposit`
// (noisemaker-for-cpu: src/effects/cpu/wormhole.js:34-76).
//
// This file has NO dependency on noisemaker-for-cpp's own headers/build --
// it is written from scratch against the JS oracle in
// docs/port-engineering/wormhole/oracle/wormhole-oracles.json, per the
// task's instruction to keep this port standalone under
// docs/port-engineering/wormhole/ and to only ever COMPILE
// noisemaker-for-cpp/noisemaker-for-cpu sources into binaries here, never
// modify them.
//
// PRECISION CONTRACT (load-bearing -- do not "clean up"):
//   - JS `Math.fround` rounds a double to the nearest float32 and returns it
//     AS A DOUBLE (53-bit container, 24 significant bits of content). Every
//     JS number is a double regardless of its logical float32 precision, so
//     arithmetic between two "already-frounded" JS numbers still happens at
//     FULL DOUBLE PRECISION until the next explicit fround. The `add`/`mul`/
//     `div` helpers in wormhole.js each do exactly one raw double op followed
//     by exactly one fround. This file mirrors that literally: every
//     intermediate value is a C++ `double`; `f32r()` performs the identical
//     "round-trip through float and back to double" that `Math.fround` does,
//     and `add`/`mul`/`divd` call it exactly once, in the same place the JS
//     source does. Do NOT flatten chained add(add(mul(...),mul(...)),mul(...))
//     expressions into one big double expression -- that would skip
//     intermediate roundings the reference performs and applies to later
//     terms (e.g. lr/mr/sr each round their own Math.pow result before the
//     final dot product rounds again).
//   - `-ffp-contract=off` is mandatory at the call site (see CMake/build
//     script) so `l + r` inside `add()` is never fused with an adjacent `*`
//     into an FMA -- that would compute a result at higher-than-float32
//     intermediate precision than V8 ever produces, silently diverging.
//   - `div(1, 3)` (the OKLab cube-root exponent) is itself F32-rounded BEFORE
//     being passed to `pow` -- `divd(1.0, 3.0)`, not `1.0 / 3.0`.
//   - `pixelStride = 1024 * uniforms.stride` is computed in double, NOT
//     F32-rounded at that statement -- only later, at each of its two use
//     sites (`F32(pixelStride)` inside the offsetX/offsetY expressions).
//     Because 1024 is an exact power of two this happens to be provably
//     unobservable (see the oracle's `pixel_stride_rounding_proof`), but the
//     code still stores `pixelStride` as a `double` computed directly from
//     `1024.0 * uniforms.stride` (never pre-narrowed) to avoid depending on
//     that proof remaining true if this function is ever extended.
//   - `Math.floor(add(sourceX, offsetX))` -- the add is F32-rounded, the
//     floor is not (and does not need to be: floor of an exact float32-
//     representable double is exact regardless of the container precision).
//   - Vertex IDs enumerate GL texels bottom-up: `row = height - 1 - y` for
//     BOTH the source read and the destination write.
//   - `weight = mul(lightness, lightness)` (F32-rounded), and every
//     accumulated RGB channel is round-tripped through `float16_truncate`
//     (a real rgba16f store, truncating not rounding) -- alpha is left
//     completely untouched.
//   - `wrap = uniforms.wrap | 0` is JS's ToInt32 bitwise-OR-with-zero
//     coercion, NOT a plain truncating cast for out-of-32-bit-range or
//     non-finite inputs (those don't occur in the pinned oracle, but the
//     port implements the real algorithm rather than assuming).
//   - `wrapRepeat`/`wrapMirror` operate on values that are always exact
//     mathematical integers by construction (outputs of `Math.floor` on
//     finite doubles); this port carries them as `std::int64_t` (not
//     `int32_t` -- the deliberately-extreme `large-stride-precision-stress`
//     oracle case pushes raw offsets past 2^31) and uses C++'s built-in `%`,
//     which truncates toward zero for integer operands exactly like JS `%`
//     does for integer-valued number operands. Verified against the oracle's
//     `wrap_function_rows` table (extracted from the REAL JS functions,
//     including negative inputs), not assumed.
#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

namespace wormhole {

constexpr double kTau = 6.28318530717959;
constexpr double kPi = 3.141592653589793; // identical double to JS Math.PI

// ---------------------------------------------------------------------------
// F32-rounding primitives -- the one and only place a `float` narrowing
// happens. Every other quantity in this file is a `double`.
// ---------------------------------------------------------------------------
[[nodiscard]] inline double f32r(double value) noexcept {
  return static_cast<double>(static_cast<float>(value));
}
[[nodiscard]] inline double add(double left, double right) noexcept { return f32r(left + right); }
[[nodiscard]] inline double mul(double left, double right) noexcept { return f32r(left * right); }
[[nodiscard]] inline double divd(double left, double right) noexcept { return f32r(left / right); }

// ---------------------------------------------------------------------------
// OKLab lightness -- mirrors wormhole.js's `oklabLightness` statement for
// statement, including the per-operation F32 rounding and the F32-rounded
// div(1,3) cube-root exponent.
// ---------------------------------------------------------------------------
[[nodiscard]] inline double oklab_lightness(double red, double green, double blue) noexcept {
  const double r = std::min(std::max(red, 0.0), 1.0);
  const double g = std::min(std::max(green, 0.0), 1.0);
  const double b = std::min(std::max(blue, 0.0), 1.0);
  const double l = add(add(mul(f32r(0.4122214708), r), mul(f32r(0.5363325363), g)), mul(f32r(0.0514459929), b));
  const double m = add(add(mul(f32r(0.2119034982), r), mul(f32r(0.6806995451), g)), mul(f32r(0.1073969566), b));
  const double s = add(add(mul(f32r(0.0883024619), r), mul(f32r(0.2817188376), g)), mul(f32r(0.6299787005), b));
  const double exponent = divd(1.0, 3.0);
  const double lr = f32r(std::pow(std::max(l, 0.0), exponent));
  const double mr = f32r(std::pow(std::max(m, 0.0), exponent));
  const double sr = f32r(std::pow(std::max(s, 0.0), exponent));
  return add(add(mul(f32r(0.2104542553), lr), mul(f32r(0.793617785), mr)), mul(f32r(-0.0040720468), sr));
}

// ---------------------------------------------------------------------------
// Wrap helpers -- exact-integer arithmetic in int64_t. C++'s built-in `%`
// truncates toward zero for both operands (same as JS `%` on integer-valued
// number operands), so `wrapRepeat`'s double-mod correction ports verbatim.
// ---------------------------------------------------------------------------
[[nodiscard]] inline std::int64_t wrap_repeat(std::int64_t value, std::int64_t size) noexcept {
  return ((value % size) + size) % size;
}
[[nodiscard]] inline std::int64_t wrap_mirror(std::int64_t value, std::int64_t size) noexcept {
  const std::int64_t doubled = size * 2;
  const std::int64_t mirrored = wrap_repeat(value, doubled);
  const std::int64_t diff = mirrored - size + 1;
  const std::int64_t abs_diff = diff < 0 ? -diff : diff;
  return size - 1 - abs_diff;
}

// ---------------------------------------------------------------------------
// JS `value | 0` (ToInt32). Implemented properly (not just a truncating
// cast) so out-of-32-bit-range or non-finite `wrap` uniforms behave exactly
// as the ECMAScript spec defines, even though the pinned oracle never
// exercises those edges.
// ---------------------------------------------------------------------------
[[nodiscard]] inline std::int32_t to_int32_bitwise_or_zero(double value) noexcept {
  if (!std::isfinite(value)) return 0;
  const double truncated = std::trunc(value);
  double modded = std::fmod(truncated, 4294967296.0); // 2^32
  if (modded < 0) modded += 4294967296.0;
  const auto u = static_cast<std::uint32_t>(modded);
  std::int32_t signed_value;
  std::memcpy(&signed_value, &u, sizeof(signed_value));
  return signed_value;
}

// ---------------------------------------------------------------------------
// float16Truncate -- a real rgba16f store: truncating (round-toward-zero
// mantissa truncation, not round-to-nearest), matching
// `src/runtime/texture-format.js`'s `float16Truncate`/`decodeFloat16` pair
// bit manipulation for bit manipulation.
// ---------------------------------------------------------------------------
[[nodiscard]] inline std::uint32_t float_to_bits(float value) noexcept {
  std::uint32_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}
[[nodiscard]] inline float bits_to_float(std::uint32_t bits) noexcept {
  float value;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}
[[nodiscard]] inline float decode_float16(std::uint16_t bits) noexcept {
  const double sign = ((bits & 0x8000u) == 0u) ? 1.0 : -1.0;
  const int exponent = (bits >> 10) & 0x1f;
  const int fraction = bits & 0x3ff;
  if (exponent == 0) {
    return static_cast<float>(sign * static_cast<double>(fraction) * std::pow(2.0, -24.0));
  }
  if (exponent == 0x1f) {
    if (fraction == 0) return sign > 0.0 ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity();
    return std::numeric_limits<float>::quiet_NaN();
  }
  return static_cast<float>(sign * (1.0 + static_cast<double>(fraction) / 1024.0) * std::pow(2.0, static_cast<double>(exponent - 15)));
}
[[nodiscard]] inline float float16_truncate(double value) noexcept {
  const std::uint32_t bits = float_to_bits(static_cast<float>(value));
  const std::uint32_t sign = (bits >> 16) & 0x8000u;
  const std::uint32_t source_exponent = (bits >> 23) & 0xffu;
  const std::uint32_t fraction = bits & 0x7fffffu;
  if (source_exponent == 0xffu) {
    if (fraction == 0u) return sign == 0u ? std::numeric_limits<float>::infinity() : -std::numeric_limits<float>::infinity();
    return std::numeric_limits<float>::quiet_NaN();
  }
  const int exponent = static_cast<int>(source_exponent) - 127 + 15;
  std::uint32_t half_bits;
  if (exponent >= 0x1f) {
    half_bits = sign | 0x7bffu;
  } else if (exponent <= 0) {
    half_bits = (exponent < -10) ? sign : (sign | (((fraction | 0x800000u) >> (1 - exponent)) >> 13));
  } else {
    half_bits = sign | (static_cast<std::uint32_t>(exponent) << 10) | (fraction >> 13);
  }
  return decode_float16(static_cast<std::uint16_t>(half_bits));
}

// ---------------------------------------------------------------------------
// Surface -- minimal standalone RGBA-float32 buffer (deliberately NOT
// noisemaker-for-cpp's Surface -- this file has zero dependency on that
// tree's headers, only on the JS oracle's data).
// ---------------------------------------------------------------------------
struct Surface {
  std::size_t width = 0;
  std::size_t height = 0;
  std::vector<float> data; // interleaved RGBA, width*height*4, top-down rows

  Surface() = default;
  Surface(std::size_t w, std::size_t h) : width(w), height(h), data(w * h * 4, 0.0f) {}
};

struct WormholeUniforms {
  double kink = 1.0;
  double stride = 1.0;
  double rotation = 0.0;
  double wrap = 1.0;
};

// ---------------------------------------------------------------------------
// The port itself -- statement-for-statement mirror of
// `runWormholeDeposit` (wormhole.js:34-76). `destination` is accumulated
// into IN PLACE, exactly like the reference (the renderer pre-seeds it with
// the previous accum-texture contents; this function never clears it).
// ---------------------------------------------------------------------------
inline void run_wormhole_deposit(const Surface& input, Surface& destination, const WormholeUniforms& uniforms) {
  if (input.width != destination.width || input.height != destination.height) {
    throw std::invalid_argument("wormhole deposit requires matching source and destination dimensions");
  }
  const auto width = static_cast<std::int64_t>(input.width);
  const auto height = static_cast<std::int64_t>(input.height);
  const float* input_data = input.data.data();
  float* output_data = destination.data.data();

  const double kink = uniforms.kink;
  const double pixel_stride = 1024.0 * uniforms.stride; // double precision -- see header note
  const double rotation = divd(mul(f32r(uniforms.rotation), f32r(kPi)), 180.0);
  const std::int32_t wrap = to_int32_bitwise_or_zero(uniforms.wrap);

  for (std::int64_t source_y = 0; source_y < height; source_y += 1) {
    for (std::int64_t source_x = 0; source_x < width; source_x += 1) {
      const std::int64_t source_row = height - 1 - source_y;
      const auto source_offset = static_cast<std::size_t>((source_row * width + source_x) * 4);

      const double lightness = oklab_lightness(input_data[source_offset], input_data[source_offset + 1], input_data[source_offset + 2]);
      const double angle = add(mul(mul(lightness, f32r(kTau)), f32r(kink)), rotation);
      const double offset_x = mul(add(f32r(std::cos(angle)), 1.0), f32r(pixel_stride));
      const double offset_y = mul(add(f32r(std::sin(angle)), 1.0), f32r(pixel_stride));

      std::int64_t destination_x = static_cast<std::int64_t>(std::floor(add(static_cast<double>(source_x), offset_x)));
      std::int64_t destination_y = static_cast<std::int64_t>(std::floor(add(static_cast<double>(source_y), offset_y)));

      if (wrap == 0) {
        destination_x = wrap_mirror(destination_x, width);
        destination_y = wrap_mirror(destination_y, height);
      } else if (wrap == 2) {
        destination_x = std::min(std::max(destination_x, std::int64_t{0}), width - 1);
        destination_y = std::min(std::max(destination_y, std::int64_t{0}), height - 1);
      } else {
        destination_x = wrap_repeat(destination_x, width);
        destination_y = wrap_repeat(destination_y, height);
      }

      // `wrapMirror` has a real, narrow off-by-one in the reference
      // algorithm itself (confirmed against the live JS by exhaustive sweep,
      // not a porting artifact -- see wormhole-report.md): for any `value`
      // with `value ≡ -1 (mod 2*size)`, `wrapMirror(value, size)` returns
      // exactly `-1` (never `size`, never anything else). wrapRepeat and the
      // clamp branch are provably always in-range. `destination_x`/
      // `destination_y` here are therefore either fully in range, or exactly
      // one step out on the low side (`-1`) -- never further, and X/Y are
      // independent (either axis, or both, can hit it for a given source
      // pixel).
      //
      // JS computes `destinationOffset` from whatever `destinationRow`/
      // `destinationX` result WITHOUT clamping first -- exactly mirrored
      // below -- and only THEN does three independent per-index TypedArray
      // writes. A Float32Array write at a negative or >=length integer index
      // is a documented, verified-empirically no-op (see report); it is
      // NEVER a wraparound and NEVER a crash. Because every offset here is a
      // multiple of 4 and the buffer length is too, `destinationOffset`,
      // `+1`, and `+2` are always simultaneously in range or simultaneously
      // out -- so a single range check on the flat offset exactly reproduces
      // JS's three independent per-index checks. Critically, this is NOT the
      // same thing as separately validating destination_x/destination_y
      // against [0,width)/[0,height): a lone out-of-range X with an
      // in-range row does not always land off the end of the buffer -- it
      // can alias into the last pixel of the row above, which JS WOULD
      // actually write to (wrongly, but really). Clamping X/Y independently
      // before forming the offset would silently drop writes JS performs.
      const std::int64_t destination_row = height - 1 - destination_y;
      const std::int64_t destination_offset_signed = (destination_row * width + destination_x) * 4;
      const std::int64_t total_lanes = width * height * 4;
      if (destination_offset_signed < 0 || destination_offset_signed + 2 >= total_lanes) {
        continue; // matches JS's silent per-index TypedArray no-op
      }
      const auto destination_offset = static_cast<std::size_t>(destination_offset_signed);

      const double weight = mul(lightness, lightness);
      output_data[destination_offset] = float16_truncate(add(output_data[destination_offset], mul(input_data[source_offset], weight)));
      output_data[destination_offset + 1] = float16_truncate(add(output_data[destination_offset + 1], mul(input_data[source_offset + 1], weight)));
      output_data[destination_offset + 2] = float16_truncate(add(output_data[destination_offset + 2], mul(input_data[source_offset + 2], weight)));
      // Alpha (destination_offset + 3) is deliberately left untouched.
    }
  }
}

} // namespace wormhole
