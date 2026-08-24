#include <cstddef>
template <std::size_t N> requires(N==2)
constexpr bool f(int) { return true; }

static_assert(!requires(int a) { f<3>(a); });

int main(){}
