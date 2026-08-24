// verify_sweep.cpp
//
// Step 4: exhaustive-enough verification. Reads sweep_oracle.csv (produced
// by gen_oracle.mjs from the SAME values.txt this program also reads --
// one shared operand list, so JS and C++ are guaranteed to be tested on
// identical inputs) and, for every (value, shift) row, computes:
//   (a) the CANDIDATE primitive: glsl::shift_right_arithmetic (portable
//       bit_cast formula, shift_primitive.hpp) for the arithmetic column;
//   (b) a NAIVE reference: plain `value >> masked` on std::int32_t, to
//       independently confirm (or refute) that Apple clang 16/arm64's
//       right-shift-of-negative-operand behavior agrees with the portable
//       primitive -- this is the "verify, don't assume" check for
//       Hazard #1's C++20 [expr.shift] claim;
//   (c) glsl::shift_left and the plain uint32_t `>>>`-equivalent (logical
//       shift is unambiguous: uint32_t `>>` is defined as zero-fill in
//       C++, matching JS `>>>` -- no separate primitive needed there,
//       spot-checked here anyway as a corroborating column).
//
// For each column, tallies N compared / N exact / N divergent against the
// JS oracle and prints an exact summary, plus (if any divergence is found)
// up to the first 20 divergent rows for debugging.
//
// Build (mandatory flags):
//   clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off \
//     verify_sweep.cpp -o verify_sweep

#include "shift_primitive.hpp"

#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Row {
  std::int32_t value;
  std::uint32_t shift;
  std::uint32_t expected_arith;
  std::uint32_t expected_logical;
  std::uint32_t expected_left;
};

[[nodiscard]] std::uint32_t parse_hex8(const std::string& s) {
  return static_cast<std::uint32_t>(std::strtoul(s.c_str(), nullptr, 16));
}

struct Tally {
  long long compared = 0;
  long long exact = 0;
  long long divergent = 0;
  std::vector<std::string> first_failures;

  void check(const char* label, std::int32_t value, std::uint32_t shift,
             std::uint32_t expected, std::uint32_t actual) {
    ++compared;
    if (expected == actual) {
      ++exact;
    } else {
      ++divergent;
      if (first_failures.size() < 20) {
        std::ostringstream os;
        os << label << ": value=" << value << " shift=" << shift
           << " expected=0x" << std::hex << expected
           << " actual=0x" << actual << std::dec;
        first_failures.push_back(os.str());
      }
    }
  }
};

}  // namespace

int main() {
  std::ifstream in("sweep_oracle.csv");
  if (!in) {
    std::fprintf(stderr, "FATAL: could not open sweep_oracle.csv (run gen_oracle.mjs first)\n");
    return 2;
  }

  Tally candidate_arith;     // glsl::shift_right_arithmetic(int32_t) -- THE primitive
  Tally candidate_arith_u32; // glsl::shift_right_arithmetic(uint32_t) overload
  Tally naive_native_shift;  // plain `value >> masked` on std::int32_t (toolchain check)
  Tally logical_shift;       // plain uint32_t `>>` (corroborates >>> is unambiguous)
  Tally left_shift;          // glsl::shift_left

  std::string line;
  long long lines_read = 0;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    ++lines_read;

    // Parse "value,shift,arith_hex,logical_hex,left_hex"
    std::size_t p1 = line.find(',');
    std::size_t p2 = line.find(',', p1 + 1);
    std::size_t p3 = line.find(',', p2 + 1);
    std::size_t p4 = line.find(',', p3 + 1);

    const std::int32_t value = static_cast<std::int32_t>(std::strtoll(line.substr(0, p1).c_str(), nullptr, 10));
    const std::uint32_t shift = static_cast<std::uint32_t>(std::strtoul(line.substr(p1 + 1, p2 - p1 - 1).c_str(), nullptr, 10));
    const std::uint32_t expected_arith = parse_hex8(line.substr(p2 + 1, p3 - p2 - 1));
    const std::uint32_t expected_logical = parse_hex8(line.substr(p3 + 1, p4 - p3 - 1));
    const std::uint32_t expected_left = parse_hex8(line.substr(p4 + 1));

    // (a) THE primitive under test.
    {
      const std::int32_t got = noisemaker::glsl::shift_right_arithmetic(value, shift);
      candidate_arith.check("shift_right_arithmetic(int32_t)", value, shift,
                             expected_arith, std::bit_cast<std::uint32_t>(got));
    }
    // (a') uint32_t overload, called with the bit-reinterpreted operand --
    // must match the SAME expected_arith column (arithmetic semantics are
    // about the call-site idiom, not the storage type).
    {
      const std::uint32_t got = noisemaker::glsl::shift_right_arithmetic(
          std::bit_cast<std::uint32_t>(value), shift);
      candidate_arith_u32.check("shift_right_arithmetic(uint32_t)", value, shift,
                                 expected_arith, got);
    }
    // (b) naive plain `>>` on (possibly negative) std::int32_t -- toolchain check.
    {
      const std::uint32_t masked = shift & 31U;
      const std::int32_t got = value >> masked;  // NOLINT: intentional, this is the toolchain probe
      naive_native_shift.check("naive value>>masked", value, shift,
                                expected_arith, std::bit_cast<std::uint32_t>(got));
    }
    // (c) logical shift corroboration (uint32_t >> is unambiguous zero-fill).
    {
      const std::uint32_t masked = shift & 31U;
      const std::uint32_t got = std::bit_cast<std::uint32_t>(value) >> masked;
      logical_shift.check("uint32_t logical >>", value, shift, expected_logical, got);
    }
    // (d) shift_left.
    {
      const std::int32_t got = noisemaker::glsl::shift_left(value, shift);
      left_shift.check("shift_left", value, shift, expected_left, std::bit_cast<std::uint32_t>(got));
    }
  }

  std::printf("rows read from sweep_oracle.csv: %lld\n\n", lines_read);

  auto report = [](const char* name, const Tally& t) {
    std::printf("== %s ==\n", name);
    std::printf("  N compared:  %lld\n", t.compared);
    std::printf("  N exact:     %lld\n", t.exact);
    std::printf("  N divergent: %lld\n", t.divergent);
    if (!t.first_failures.empty()) {
      std::printf("  first failures:\n");
      for (const auto& f : t.first_failures) std::printf("    %s\n", f.c_str());
    }
    std::printf("\n");
  };

  report("shift_right_arithmetic(int32_t)  [THE PRIMITIVE]", candidate_arith);
  report("shift_right_arithmetic(uint32_t) [overload]", candidate_arith_u32);
  report("naive `value >> masked` on int32_t [toolchain check]", naive_native_shift);
  report("uint32_t logical >> [corroborates >>> mapping]", logical_shift);
  report("shift_left [bonus primitive]", left_shift);

  const long long total_divergent = candidate_arith.divergent + candidate_arith_u32.divergent +
                                     naive_native_shift.divergent + logical_shift.divergent +
                                     left_shift.divergent;
  return total_divergent == 0 ? 0 : 1;
}
