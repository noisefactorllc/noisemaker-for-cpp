// fdlibm probe: reads inputs.hex, evaluates fdlibm::{tanh,exp,expm1,sin,cos}
// for the five ported functions and std::{log,atan,sqrt,pow} (unchanged,
// carried along only to keep the column format identical to the other two
// probes) and writes the same 9-column hex format as node_probe.mjs /
// baseline_probe.cpp: tanh exp expm1 sin cos log atan sqrt pow
//
// Build (mandatory flags):
//   clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off \
//       -O2 -o fdlibm_probe fdlibm_probe.cpp fdlibm.cpp
#include <cmath>
#include <iostream>
#include <string>

#include "fdlibm.hpp"
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
    const double tanh_v = fdlibm::tanh(x);
    const double exp_v = fdlibm::exp(x);
    const double expm1_v = fdlibm::expm1(x);
    const double sin_v = fdlibm::sin(x);
    const double cos_v = fdlibm::cos(x);
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
