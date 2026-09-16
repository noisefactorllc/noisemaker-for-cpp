// cpp_probe.cpp -- evaluates noisemaker::fdlibm::<function> over the SAME
// binary input file gen_inputs.mjs wrote for node_probe.mjs, writing
// results in the identical raw-bit-pattern format so compare.mjs can diff
// them byte-for-byte. Deliberately reads and writes raw bits (never
// re-derives a formula independently of the shared input file) for the
// same reason node_probe.mjs does: a documented prior-session harness bug
// came from two "equivalent" re-derivations of the same input drifting
// under FMA contraction.
//
// Usage: cpp_probe <function> <infile> <outfile>
//
// Build (matching arch, matching contraction as the real project TU):
//   clang++ -std=c++20 -O2 -ffp-contract=fast -Iinclude \
//     docs/port-engineering/v8-math/cpp_probe.cpp src/fdlibm.cpp -o cpp_probe
//   clang++ -arch x86_64 -std=c++20 -O2 -ffp-contract=fast -Iinclude \
//     docs/port-engineering/v8-math/cpp_probe.cpp src/fdlibm.cpp \
//     -o cpp_probe_x86_64

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

#include "noisemaker/fdlibm.hpp"

namespace {

double bits_to_double(std::uint64_t bits) {
  double value;
  static_assert(sizeof(value) == sizeof(bits));
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

std::uint64_t double_to_bits(double value) {
  std::uint64_t bits;
  std::memcpy(&bits, &value, sizeof(bits));
  return bits;
}

std::vector<std::uint8_t> read_all(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) {
    std::fprintf(stderr, "cpp_probe: cannot open %s\n", path.c_str());
    std::exit(1);
  }
  in.seekg(0, std::ios::end);
  const auto size = static_cast<std::size_t>(in.tellg());
  in.seekg(0, std::ios::beg);
  std::vector<std::uint8_t> data(size);
  in.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(size));
  return data;
}

std::uint64_t read_u64le(const std::uint8_t* p) {
  std::uint64_t v = 0;
  for (int i = 7; i >= 0; --i) v = (v << 8) | p[i];
  return v;
}

void write_u64le(std::vector<std::uint8_t>& out, std::uint64_t v) {
  for (int i = 0; i < 8; ++i) {
    out.push_back(static_cast<std::uint8_t>(v & 0xff));
    v >>= 8;
  }
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::fprintf(stderr, "usage: cpp_probe <function> <infile> <outfile>\n");
    return 1;
  }
  const std::string fn = argv[1];
  const std::string infile = argv[2];
  const std::string outfile = argv[3];

  static const std::unordered_map<std::string, int> arity = {
      {"sin", 1},   {"cos", 1},   {"tan", 1},    {"asin", 1},  {"acos", 1},
      {"atan", 1},  {"exp", 1},   {"expm1", 1},  {"log", 1},   {"log2", 1},
      {"tanh", 1},  {"pow", 2},   {"atan2", 2},  {"hypot2", 2}, {"hypot3", 3},
  };
  const auto arity_it = arity.find(fn);
  if (arity_it == arity.end()) {
    std::fprintf(stderr, "cpp_probe: unknown function %s\n", fn.c_str());
    return 1;
  }
  const int n_args = arity_it->second;

  using Fn1 = double (*)(double);
  using Fn2 = double (*)(double, double);
  using Fn3 = double (*)(double, double, double);

  const std::unordered_map<std::string, Fn1> unary = {
      {"sin", noisemaker::fdlibm::sin},   {"cos", noisemaker::fdlibm::cos},
      {"tan", noisemaker::fdlibm::tan},   {"asin", noisemaker::fdlibm::asin},
      {"acos", noisemaker::fdlibm::acos}, {"atan", noisemaker::fdlibm::atan},
      {"exp", noisemaker::fdlibm::exp},   {"expm1", noisemaker::fdlibm::expm1},
      {"log", noisemaker::fdlibm::log},   {"log2", noisemaker::fdlibm::log2},
      {"tanh", noisemaker::fdlibm::tanh},
  };
  const std::unordered_map<std::string, Fn2> binary = {
      {"pow", noisemaker::fdlibm::pow},
      {"atan2", [](double y, double x) { return noisemaker::fdlibm::atan2(y, x); }},
      {"hypot2", [](double x, double y) { return noisemaker::fdlibm::hypot(x, y); }},
  };

  const std::vector<std::uint8_t> input = read_all(infile);
  const std::size_t stride = static_cast<std::size_t>(n_args) * 8;
  if (input.size() % stride != 0) {
    std::fprintf(stderr, "cpp_probe: input size %zu is not a multiple of stride %zu\n",
                 input.size(), stride);
    return 1;
  }
  const std::size_t count = input.size() / stride;

  std::vector<std::uint8_t> out;
  out.reserve(count * 8);

  for (std::size_t i = 0; i < count; ++i) {
    const std::uint8_t* p = input.data() + i * stride;
    double result;
    if (n_args == 1) {
      const double a = bits_to_double(read_u64le(p));
      result = unary.at(fn)(a);
    } else if (n_args == 2) {
      const double a = bits_to_double(read_u64le(p));
      const double b = bits_to_double(read_u64le(p + 8));
      result = binary.at(fn)(a, b);
    } else {
      const double a = bits_to_double(read_u64le(p));
      const double b = bits_to_double(read_u64le(p + 8));
      const double c = bits_to_double(read_u64le(p + 16));
      result = noisemaker::fdlibm::hypot(a, b, c);
    }
    write_u64le(out, double_to_bits(result));
  }

  std::ofstream o(outfile, std::ios::binary);
  o.write(reinterpret_cast<const char*>(out.data()), static_cast<std::streamsize>(out.size()));
  std::fprintf(stderr, "%s: n=%zu -> %s\n", fn.c_str(), count, outfile.c_str());
  return 0;
}
