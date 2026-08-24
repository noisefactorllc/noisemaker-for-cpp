// hash_mix_port_logical_control.cpp
//
// NEGATIVE CONTROL for the hash_mix cross-check: same port, but every
// `>>` uses LOGICAL (zero-fill) shift instead of glsl::shift_right_arithmetic
// -- i.e. the mistake this whole task exists to prevent (using the
// existing, already-shipped glsl::shift_right's semantics on a bespoke
// hash helper that actually needs the arithmetic primitive).
//
// If this control does NOT diverge from the JS oracle, that would mean
// the hash_mix cross-check is not actually discriminating between
// logical and arithmetic shift (e.g. because the sampled `v` population
// never hits bit 31), which would make the "positive" result in
// hash_mix_port.cpp meaningless. Expected: substantial divergence here,
// proving the positive result is a real, discriminating pass.

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>

namespace {

[[nodiscard]] constexpr std::uint32_t shift_right_logical_masked(std::uint32_t value, std::uint32_t amount) noexcept {
  return value >> (amount & 31U);  // zero-fill; well-defined for uint32_t regardless of sign bit
}

[[nodiscard]] constexpr std::uint32_t cpu_umul(std::uint32_t left, std::uint32_t right) noexcept {
  return static_cast<std::uint32_t>(left * right);
}

// Identical structure to hash_mix_port.cpp's hash_mix, EXCEPT every shift
// is the (wrong, for this function) logical primitive.
[[nodiscard]] constexpr std::uint32_t hash_mix_WRONG_logical(std::uint32_t v) noexcept {
  v = v ^ shift_right_logical_masked(v, 16u);
  v = cpu_umul(v, 2146121005u);
  v = v ^ shift_right_logical_masked(v, 15u);
  v = cpu_umul(v, 2221713035u);
  v = v ^ shift_right_logical_masked(v, 16u);
  return v;
}

}  // namespace

int main() {
  std::ifstream in("hash_mix_oracle.csv");
  if (!in) {
    std::fprintf(stderr, "FATAL: could not open hash_mix_oracle.csv\n");
    return 2;
  }
  long long compared = 0, exact = 0, divergent = 0;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::size_t p1 = line.find(',');
    const std::int32_t v = static_cast<std::int32_t>(std::strtoll(line.substr(0, p1).c_str(), nullptr, 10));
    const std::uint32_t expected = static_cast<std::uint32_t>(std::strtoul(line.substr(p1 + 1).c_str(), nullptr, 16));
    const std::uint32_t actual = hash_mix_WRONG_logical(std::bit_cast<std::uint32_t>(v));
    ++compared;
    if (actual == expected) ++exact; else ++divergent;
  }
  std::printf("NEGATIVE CONTROL (logical shift, expected to diverge): N compared=%lld N exact=%lld N divergent=%lld (%.2f%% divergent)\n",
              compared, exact, divergent, compared ? 100.0 * static_cast<double>(divergent) / static_cast<double>(compared) : 0.0);
  return 0;
}
