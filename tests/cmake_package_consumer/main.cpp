#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/png.hpp"
#include "noisemaker/surface.hpp"

int main() {
  noisemaker::Surface surface(1, 1);
  const auto png = noisemaker::encode_png(surface);
  return noisemaker::generated::catalog().empty() || png.empty() ? 1 : 0;
}
