#include <cstddef>
template <std::size_t N> requires(N==2)
constexpr bool f(int) { return true; }

template <std::size_t N>
constexpr bool check() { return requires(int a) { f<N>(a); }; }

static_assert(!check<3>());
static_assert(check<2>());

int main(){}
