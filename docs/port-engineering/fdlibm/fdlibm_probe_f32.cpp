// fdlibm at f32: computes fdlibm::{tanh,exp,expm1,sin,cos} at double
// precision, then narrows to float exactly as the patched
// noisemaker::glsl::{tanh,exp,sin,cos} would:
// `return noisemaker::f32(noisemaker::fdlibm::tanh(value));`
// Emits 8-hex-digit (32-bit) fields, same format as baseline_probe_f32.cpp
// and node_probe_f32.mjs.
//
// Build: clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror
//        -ffp-contract=off -O2 -o fdlibm_probe_f32 fdlibm_probe_f32.cpp fdlibm.cpp
#include <iostream>
#include <string>

#include "fdlibm.hpp"
#include "probe_common.hpp"

static inline std::string to_hex32(float f) {
  std::uint32_t bits;
  static_assert(sizeof(bits) == sizeof(f));
  __builtin_memcpy(&bits, &f, sizeof(bits));
  char tmp[16];
  std::snprintf(tmp, sizeof(tmp), "%08x", static_cast<unsigned>(bits));
  return std::string(tmp);
}

int main() {
  std::string line;
  std::string out;
  out.reserve(1 << 20);
  while (std::getline(std::cin, line)) {
    if (line.empty()) continue;
    const double x = bits_to_double(parse_hex_u64(line));
    const float tanh_v = static_cast<float>(fdlibm::tanh(x));
    const float exp_v = static_cast<float>(fdlibm::exp(x));
    const float expm1_v = static_cast<float>(fdlibm::expm1(x));
    const float sin_v = static_cast<float>(fdlibm::sin(x));
    const float cos_v = static_cast<float>(fdlibm::cos(x));
    out += to_hex32(tanh_v);
    out += ' ';
    out += to_hex32(exp_v);
    out += ' ';
    out += to_hex32(expm1_v);
    out += ' ';
    out += to_hex32(sin_v);
    out += ' ';
    out += to_hex32(cos_v);
    out += '\n';
  }
  std::cout << out;
  return 0;
}
