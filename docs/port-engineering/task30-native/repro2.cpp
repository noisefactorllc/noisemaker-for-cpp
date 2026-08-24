#include <cstddef>
#include <type_traits>
template <std::size_t N> requires(N==2)
constexpr bool f(int) { return true; }

template <std::size_t N> constexpr bool invocable = requires(int a) { { f<N>(a) }; };

static_assert(!invocable<3>);
static_assert(invocable<2>);

int main(){}
