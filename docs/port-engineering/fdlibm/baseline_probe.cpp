// Baseline probe: reads inputs.hex, evaluates std::* (the platform libm —
// what the C++ runtime calls today via glsl_runtime.hpp), writes 9
// space-separated hex result columns per line in the same order as
// node_probe.mjs: tanh exp expm1 sin cos log atan sqrt pow
//
// Build (mandatory flags):
//   clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off \
//       -O2 -o baseline_probe baseline_probe.cpp
#include <cmath>
#include <iostream>
#include <string>

#include "probe_common.hpp"

namespace {
constexpr double kPowExps[] = {0.5, 2.0, 3.0, 1.0 / 3.0, -1.5, 10.0};
constexpr int kPowExpsCount = 6;
}  // namespace

int main() {
  std::string line;
  long long i = 0;
  std::string out;
  out.reserve(1 << 20);
  while (std::getline(std::cin, line)) {
    if (line.empty()) continue;
    const double x = bits_to_double(parse_hex_u64(line));
    const double ax = std::fabs(x);
    const double tanh_v = std::tanh(x);
    const double exp_v = std::exp(x);
    const double expm1_v = std::expm1(x);
    const double sin_v = std::sin(x);
    const double cos_v = std::cos(x);
    const double log_v = std::log(ax);
    const double atan_v = std::atan(x);
    const double sqrt_v = std::sqrt(ax);
    const double pow_v = std::pow(ax, kPowExps[i % kPowExpsCount]);

    out += to_hex(tanh_v);
    out += ' ';
    out += to_hex(exp_v);
    out += ' ';
    out += to_hex(expm1_v);
    out += ' ';
    out += to_hex(sin_v);
    out += ' ';
    out += to_hex(cos_v);
    out += ' ';
    out += to_hex(log_v);
    out += ' ';
    out += to_hex(atan_v);
    out += ' ';
    out += to_hex(sqrt_v);
    out += ' ';
    out += to_hex(pow_v);
    out += '\n';
    ++i;
  }
  std::cout << out;
  return 0;
}
