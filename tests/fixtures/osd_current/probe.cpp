#include "noisemaker/kernel.hpp"
#include "noisemaker/sampler.hpp"
#include <bit>
#include <cstdint>
#include <iostream>
#include <string>
namespace noisemaker {
#include "osd_emitted.inc"
}
int main(int argc, char** argv) {
  if (argc != 8) return 2;
  using namespace noisemaker;
  const auto width = static_cast<std::size_t>(std::stoull(argv[1]));
  const auto height = static_cast<std::size_t>(std::stoull(argv[2]));
  Surface input(width, height), destination(width, height);
  for (Surface* surface : {&input}) for (float& value : surface->data()) {
    std::uint32_t word = 0;
    for (unsigned byte = 0; byte < 4; ++byte) {
      const auto next = std::cin.get();
      if (next == std::char_traits<char>::eof()) return 3;
      word |= static_cast<std::uint32_t>(static_cast<unsigned char>(next)) << (byte * 8);
    }
    value = std::bit_cast<float>(word);
  }
  glsl::Bindings bindings;
  bindings.set_uniform("fullResolution", glsl::Vec2(static_cast<double>(width), static_cast<double>(height)));
  bindings.set_uniform("tileOffset", glsl::Vec2(0.0));
  bindings.set_uniform("time", static_cast<double>(f32(std::stod(argv[3]))));
  bindings.set_uniform("renderScale", 1.0);
  bindings.set_uniform("resolution", glsl::Vec2(static_cast<double>(width), static_cast<double>(height)));
  const char* names[] = {"alpha", "seed", "speed"};
  for (std::size_t i = 0; i < 3; ++i) bindings.set_uniform(names[i], std::stod(argv[4 + i]));
  bindings.set_uniform("corner", static_cast<std::int32_t>(std::stoi(argv[7])));
  bindings.set_texture("inputTex", input);
  const auto kernel = bind_osd_numerical_probe(bindings);
  for (std::size_t y = 0; y < height; ++y) for (std::size_t x = 0; x < width; ++x) {
    glsl::PixelContext context;
    context.frag_coord = glsl::Vec4(static_cast<double>(x) + .5, static_cast<double>(height - y) - .5, 0.0, 1.0);
    context.resolution = glsl::Vec2(static_cast<double>(width), static_cast<double>(height));
    glsl::Vec4 out;
    kernel.run_pixel(context, out);
    for (std::size_t c = 0; c < 4; ++c) destination.data()[(y * width + x) * 4 + c] = out[c];
  }
  for (float value : destination.data()) {
    const auto word = std::bit_cast<std::uint32_t>(value);
    for (unsigned shift = 0; shift < 32; shift += 8) std::cout.put(static_cast<char>((word >> shift) & 255U));
  }
  for (auto byte : destination.to_rgba8()) std::cout.put(static_cast<char>(byte));
}
