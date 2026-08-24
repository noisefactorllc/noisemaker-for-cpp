// verify_edge_amounts.cpp
// Confirms glsl::shift_right_arithmetic's amount-masking matches JS for
// shift-count VALUES outside [0,31] but still representable as
// std::uint32_t (32, 33, 63, 64, 1000000, UINT32_MAX). See
// gen_edge_amounts.mjs for the oracle and rationale.

#include "shift_primitive.hpp"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>

int main() {
  std::ifstream in("edge_amounts_oracle.csv");
  if (!in) {
    std::fprintf(stderr, "FATAL: could not open edge_amounts_oracle.csv (run gen_edge_amounts.mjs first)\n");
    return 2;
  }
  long long compared = 0, exact = 0, divergent = 0;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::size_t p1 = line.find(',');
    std::size_t p2 = line.find(',', p1 + 1);
    const std::int32_t value = static_cast<std::int32_t>(std::strtoll(line.substr(0, p1).c_str(), nullptr, 10));
    const std::uint32_t amount = static_cast<std::uint32_t>(std::strtoull(line.substr(p1 + 1, p2 - p1 - 1).c_str(), nullptr, 10));
    const std::uint32_t expected = static_cast<std::uint32_t>(std::strtoul(line.substr(p2 + 1).c_str(), nullptr, 16));

    const std::uint32_t actual = std::bit_cast<std::uint32_t>(noisemaker::glsl::shift_right_arithmetic(value, amount));
    ++compared;
    if (actual == expected) {
      ++exact;
    } else {
      ++divergent;
      std::printf("DIVERGENT: value=%d amount=%u expected=0x%08x actual=0x%08x\n", value, amount, expected, actual);
    }
  }
  std::printf("edge amounts: N compared=%lld N exact=%lld N divergent=%lld\n", compared, exact, divergent);
  return divergent == 0 ? 0 : 1;
}
