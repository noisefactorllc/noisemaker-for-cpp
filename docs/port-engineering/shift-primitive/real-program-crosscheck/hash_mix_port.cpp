// hash_mix_port.cpp
//
// Step 5: real-program cross-check, C++ side.
//
// Ports `hash_mix` (canonical-kernels.js:19970-19976, filter/spookyTicker,
// snapshotted verbatim in snapshot_canonicalFactory147.js.excerpt) to
// C++20, using glsl::shift_right_arithmetic (../shift_primitive.hpp, the
// primitive this task designs) for every `>>`, and plain uint32_t
// multiplication for `cpu_umul` (Math.imul(a,b)>>>0 -- verified to match
// plain uint32_t wraparound multiplication separately below and in
// umul_oracle.csv; that fact is NOT part of the shift primitive, it is a
// pre-existing, already-shipped correctness property of this codebase's
// `detail::multiply`/umul handling per bitops-precompute.md's own
// "What I could not verify" note -- re-confirmed here only because the
// cross-check needs it to be faithful).
//
// Compares hash_mix(v) for every v in the shared values.txt population
// (100,206 values spanning the full int32 range) against hash_mix_oracle.csv
// and umul_oracle.csv, reporting exact N compared/exact/divergent.

#include "../shift_primitive.hpp"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>

namespace {

// Plain uint32_t multiplication: well-defined modular wraparound in C++,
// matching Math.imul(a,b)>>>0's 32-bit truncated-product semantics.
[[nodiscard]] constexpr std::uint32_t cpu_umul(std::uint32_t left, std::uint32_t right) noexcept {
  return static_cast<std::uint32_t>(left * right);
}

// Verbatim structural port of canonical-kernels.js:19970-19976:
//   function hash_mix (v) {
//     v = v ^ (v >> 16);
//     v = cpu_umul(v, 2146121005);
//     v = v ^ (v >> 15);
//     v = cpu_umul(v, 2221713035);
//     v = v ^ (v >> 16);
//     return v;
//   }
// Every `>>` becomes glsl::shift_right_arithmetic (NOT glsl::shift_right,
// which would be the wrong -- logical -- primitive for this bespoke,
// non-canonical-idiom hash helper per Hazard #1).
[[nodiscard]] constexpr std::uint32_t hash_mix(std::uint32_t v) noexcept {
  v = v ^ noisemaker::glsl::shift_right_arithmetic(v, 16u);
  v = cpu_umul(v, 2146121005u);
  v = v ^ noisemaker::glsl::shift_right_arithmetic(v, 15u);
  v = cpu_umul(v, 2221713035u);
  v = v ^ noisemaker::glsl::shift_right_arithmetic(v, 16u);
  return v;
}

}  // namespace

int main() {
  // --- hash_mix cross-check ---
  {
    std::ifstream in("hash_mix_oracle.csv");
    if (!in) {
      std::fprintf(stderr, "FATAL: could not open hash_mix_oracle.csv (run hash_mix_reference.mjs first)\n");
      return 2;
    }
    long long compared = 0, exact = 0, divergent = 0;
    std::string line;
    while (std::getline(in, line)) {
      if (line.empty()) continue;
      std::size_t p1 = line.find(',');
      const std::int32_t v = static_cast<std::int32_t>(std::strtoll(line.substr(0, p1).c_str(), nullptr, 10));
      const std::uint32_t expected = static_cast<std::uint32_t>(std::strtoul(line.substr(p1 + 1).c_str(), nullptr, 16));
      const std::uint32_t actual = hash_mix(std::bit_cast<std::uint32_t>(v));
      ++compared;
      if (actual == expected) {
        ++exact;
      } else {
        ++divergent;
        if (divergent <= 20) {
          std::printf("DIVERGENT hash_mix: v=%d expected=0x%08x actual=0x%08x\n", v, expected, actual);
        }
      }
    }
    std::printf("hash_mix cross-check: N compared=%lld N exact=%lld N divergent=%lld\n", compared, exact, divergent);
    if (divergent != 0) return 1;
  }

  // --- cpu_umul spot-check (supporting fact, not the primitive itself) ---
  {
    std::ifstream in("umul_oracle.csv");
    if (!in) {
      std::fprintf(stderr, "FATAL: could not open umul_oracle.csv\n");
      return 2;
    }
    long long compared = 0, exact = 0, divergent = 0;
    std::string line;
    while (std::getline(in, line)) {
      if (line.empty()) continue;
      std::size_t p1 = line.find(',');
      std::size_t p2 = line.find(',', p1 + 1);
      const std::int32_t a = static_cast<std::int32_t>(std::strtoll(line.substr(0, p1).c_str(), nullptr, 10));
      const std::int32_t b = static_cast<std::int32_t>(std::strtoll(line.substr(p1 + 1, p2 - p1 - 1).c_str(), nullptr, 10));
      const std::uint32_t expected = static_cast<std::uint32_t>(std::strtoul(line.substr(p2 + 1).c_str(), nullptr, 16));
      const std::uint32_t actual = cpu_umul(std::bit_cast<std::uint32_t>(a), std::bit_cast<std::uint32_t>(b));
      ++compared;
      if (actual == expected) {
        ++exact;
      } else {
        ++divergent;
        if (divergent <= 20) {
          std::printf("DIVERGENT umul: a=%d b=%d expected=0x%08x actual=0x%08x\n", a, b, expected, actual);
        }
      }
    }
    std::printf("cpu_umul spot-check: N compared=%lld N exact=%lld N divergent=%lld\n", compared, exact, divergent);
    if (divergent != 0) return 1;
  }

  return 0;
}
