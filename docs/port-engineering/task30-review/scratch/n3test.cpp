#include "noisemaker/glsl_types.hpp"
int main() {
  noisemaker::glsl::Vec<3, float> a{}, b{};
  auto r = noisemaker::glsl::lessThanEqual<3>(a, b);
  bool x = noisemaker::glsl::all<3>(r);
  return x ? 0 : 1;
}
