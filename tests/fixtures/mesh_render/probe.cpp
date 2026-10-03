#include <bit>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#include "noisemaker/effects/mesh_render.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/surface.hpp"

int main() {
  using namespace noisemaker;
  std::size_t width, height, count;
  graph::MeshData mesh;
  std::cin >> width >> height >> mesh.tex_width >> mesh.tex_height;
  Surface destination(width, height);
  std::array<float, 4> clear{};
  for (auto& value : clear) std::cin >> value;
  destination.clear(clear);
  std::cin >> count; mesh.position_data.resize(count);
  for (auto& value : mesh.position_data) std::cin >> value;
  std::cin >> count; mesh.normal_data.resize(count);
  for (auto& value : mesh.normal_data) std::cin >> value;
  glsl::Bindings bindings;
  std::cin >> count;
  for (std::size_t i = 0; i < count; ++i) {
    std::string name; double value;
    std::cin >> name >> value;
    bindings.set_uniform(name, value);
  }
  std::cin >> count;
  for (std::size_t i = 0; i < count; ++i) {
    std::string name; double x, y, z;
    std::cin >> name >> x >> y >> z;
    bindings.set_uniform(name, glsl::DVec3(x, y, z));
  }
  bool has_full_resolution;
  std::cin >> has_full_resolution;
  if (has_full_resolution) {
    double x, y; std::cin >> x >> y;
    bindings.set_uniform("fullResolution", glsl::DVec2(x, y));
  }
  if (!std::cin) return 2;
  std::cout << effects::render_triangles(mesh, bindings, destination) << '\n';
  for (float value : destination.data()) std::cout << std::bit_cast<std::uint32_t>(value) << ' ';
  std::cout << '\n';
  for (auto value : destination.to_rgba8()) std::cout << static_cast<unsigned>(value) << ' ';
  std::cout << '\n';
}
