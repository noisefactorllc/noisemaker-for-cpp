#include <cstdint>
#include <cstdio>
#include <fstream>
#include <vector>

#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/png.hpp"
#include "noisemaker/surface.hpp"

int main() {
  constexpr std::size_t width = 256;
  constexpr std::size_t height = 256;

  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("resolution",
                       noisemaker::glsl::Vec2(static_cast<float>(width),
                                              static_cast<float>(height)));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
  bindings.set_uniform("fullResolution",
                       noisemaker::glsl::Vec2(static_cast<float>(width),
                                              static_cast<float>(height)));
  bindings.set_uniform("aspect", 1.0f);
  bindings.set_uniform("time", 0.0f);
  bindings.set_uniform("scale", 4.0f);
  bindings.set_uniform("seed", std::int32_t{7});
  bindings.set_uniform("octaves", std::int32_t{3});
  bindings.set_uniform("colorMode", std::int32_t{0});
  bindings.set_uniform("ridges", std::int32_t{0});
  bindings.set_uniform("warpIterations", std::int32_t{0});
  bindings.set_uniform("warpScale", 1.0f);
  bindings.set_uniform("warpIntensity", 0.0f);
  bindings.set_uniform("speed", 0.0f);

  const noisemaker::BoundKernel kernel =
      noisemaker::generated::bind_synth_perlin_perlin(bindings);
  const noisemaker::Surface surface =
      noisemaker::run_pass(kernel, width, height);

  const std::vector<std::uint8_t> png = noisemaker::encode_png(surface);
  std::ofstream out("perlin.png", std::ios::binary);
  out.write(reinterpret_cast<const char*>(png.data()),
            static_cast<std::streamsize>(png.size()));

  std::printf("wrote perlin.png (%zux%zu, %zu bytes)\n", surface.width(),
              surface.height(), png.size());
  std::printf("catalog contains %zu kernels\n",
              noisemaker::generated::catalog().size());
  return 0;
}
