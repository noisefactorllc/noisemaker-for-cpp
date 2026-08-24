// Shared plumbing for the C++ probes: read inputs.hex, write result hex.
//
// Trap #2 from the prior investigation (recorded in
// task-31-curl-root-cause.md and repeated here so it isn't repeated again):
// a helper that returns `static char buf[N]` makes every printf/format
// argument in the same call share ONE buffer, silently printing the same
// value N times and producing "impossible" divergence numbers (including
// an impossible >100%-looking sqrt mismatch — sqrt is IEEE
// correctly-rounded and must never disagree; any harness that reports a
// sqrt mismatch is broken, not the math). This file avoids that entirely
// by returning std::string by value from to_hex() — no shared buffers.
#ifndef NOISEMAKER_FDLIBM_PROBE_COMMON_HPP_
#define NOISEMAKER_FDLIBM_PROBE_COMMON_HPP_

#include <bit>
#include <cstdint>
#include <cstdio>
#include <string>

inline double bits_to_double(std::uint64_t bits) {
  return std::bit_cast<double>(bits);
}

inline std::uint64_t double_to_bits(double x) {
  return std::bit_cast<std::uint64_t>(x);
}

inline std::string to_hex(double x) {
  char tmp[32];
  std::snprintf(tmp, sizeof(tmp), "%016llx",
                static_cast<unsigned long long>(double_to_bits(x)));
  return std::string(tmp);
}

inline std::uint64_t parse_hex_u64(const std::string& s) {
  return static_cast<std::uint64_t>(std::stoull(s, nullptr, 16));
}

#endif  // NOISEMAKER_FDLIBM_PROBE_COMMON_HPP_
