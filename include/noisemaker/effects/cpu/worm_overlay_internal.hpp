#pragma once

// Test-only exposure of worm_overlay.cpp's internal building blocks, so
// tests can pin function-level ground truth directly (mirroring the
// wormhole port's `wrap_function_rows`/`oklab_lightness_rows` direct-row
// tables) instead of only ever exercising them through the full
// `render_canonical_worm_overlay` entry point. Not part of the public API:
// nothing in `noisemaker::graph`/`noisemaker::Renderer` includes this
// header, and it is not installed.

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace noisemaker::effects::cpu::detail {

// ECMA-262 `ToUint32`: truncate toward zero, then reduce modulo 2^32
// (nonnegative result). This is what JS's `seed >>> 0` performs for any
// finite double `seed`, including negative or fractional values -- NOT the
// same as a plain `static_cast<uint32_t>`, which is undefined/differently
// defined for out-of-range or negative doubles in C++.
[[nodiscard]] std::uint32_t to_uint32(double value) noexcept;

// Line-for-line port of worm-overlay.js's `SeededRng` (a PCG-style xorshift
// generator seeded via `ToUint32`).
class SeededRng {
 public:
  explicit SeededRng(double seed) noexcept;

  [[nodiscard]] std::uint32_t next() noexcept;
  [[nodiscard]] double float_() noexcept;
  [[nodiscard]] double normal(double mean, double deviation) noexcept;

  [[nodiscard]] std::uint32_t state() const noexcept { return state_; }

 private:
  std::uint32_t state_;
};

// Line-for-line port of `valueNoiseField`. Returns the flat `width*height`
// bilinearly-interpolated field (already float32-rounded per element, since
// the authority stores into a `Float32Array`).
[[nodiscard]] std::vector<float> value_noise_field(std::size_t width,
                                                    std::size_t height,
                                                    double frequency,
                                                    SeededRng& rng);

}  // namespace noisemaker::effects::cpu::detail
