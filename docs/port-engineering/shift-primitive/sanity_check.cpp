#include "shift_primitive.hpp"
#include <cstdio>
int main() {
  using namespace noisemaker::glsl;
  static_assert(shift_right_arithmetic(std::int32_t(-1), 16u) == -1);
  static_assert(shift_right_arithmetic(std::int32_t(-2147483648), 1u) == -1073741824);
  static_assert(shift_right_arithmetic(std::uint32_t(0x80000000u), 4u) == 0xF8000000u);
  static_assert(shift_left(std::int32_t(1), 31u) == -2147483648);
  std::printf("sanity ok\n");
  return 0;
}
