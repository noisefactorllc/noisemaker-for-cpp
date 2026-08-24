// Confirms, against the REAL project headers (compiled read-only, nothing
// modified), that the Curl-specific vec3 tanh overload
// (glsl::tanh(const Vec<3,float>&), which lowers to
// detail::map_float(value, [](double lane){ return <impl>(lane); }))
// produces BIT-IDENTICAL results to the scalar glsl::tanh(double) overload,
// lane by lane, over the full input sweep. This is compiled twice: once
// against the unpatched real headers (std::tanh path) and once against the
// patched copies (fdlibm::tanh path) to directly settle whether the two
// call shapes ever disagree, rather than relying on "the code looks the
// same" reasoning alone.
//
// Reads inputs.hex, writes one line per input: "<scalar_f32_hex>
// <vec3lane0_f32_hex> <match>" where match is 1 if bit-identical.
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <string>

#include "noisemaker/glsl_runtime.hpp"

using namespace noisemaker;

static double bits_to_double(std::uint64_t bits) {
  double d;
  static_assert(sizeof(d) == sizeof(bits));
  __builtin_memcpy(&d, &bits, sizeof(d));
  return d;
}
static std::uint32_t float_bits(float f) {
  std::uint32_t b;
  static_assert(sizeof(b) == sizeof(f));
  __builtin_memcpy(&b, &f, sizeof(b));
  return b;
}

int main() {
  std::string line;
  long long n = 0, mismatches = 0;
  while (std::getline(std::cin, line)) {
    if (line.empty()) continue;
    const std::uint64_t bits = static_cast<std::uint64_t>(std::stoull(line, nullptr, 16));
    const double x = bits_to_double(bits);

    const float scalar_result = glsl::tanh(x);

    glsl::Vec<3, float> v;
    v[0] = noisemaker::f32(x);
    v[1] = noisemaker::f32(x);
    v[2] = noisemaker::f32(x);
    // NOTE: this materializes x to f32 BEFORE tanh (that's the narrow-vs-not
    // distinction task-31-curl-SOLVED.md documents, orthogonal to what we're
    // testing here). What we're testing is: given the SAME f32-narrowed lane
    // value, does the vec3 path's inner lambda compute the identical
    // transcendental as the scalar path? So compare the vec3 result against
    // calling the scalar wrapper on that SAME already-narrowed f32 value
    // widened back to double (v[0] as double), not against x directly.
    const glsl::Vec<3, float> vec_result = glsl::tanh(v);
    const float scalar_on_narrowed = glsl::tanh(static_cast<double>(v[0]));

    const bool match = float_bits(vec_result[0]) == float_bits(scalar_on_narrowed) &&
                        float_bits(vec_result[1]) == float_bits(scalar_on_narrowed) &&
                        float_bits(vec_result[2]) == float_bits(scalar_on_narrowed);
    if (!match) {
      ++mismatches;
      std::printf("MISMATCH x=%.17g narrowed_lane=%.9g scalar_on_narrowed_bits=%08x vec_lane0_bits=%08x\n",
                   x, static_cast<double>(v[0]), float_bits(scalar_on_narrowed), float_bits(vec_result[0]));
    }
    (void)scalar_result;
    ++n;
  }
  std::printf("N=%lld mismatches=%lld\n", n, mismatches);
  return 0;
}
