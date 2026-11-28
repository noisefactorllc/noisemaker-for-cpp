#include <bit>
#include <cstdint>
#include <iostream>
#include <iomanip>
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
  effects::PassDefinition pass;
  std::string kind, count_value, uniform;
  std::cin >> kind >> std::quoted(count_value) >> uniform;
  if (kind == "number") pass.count = effects::Value::number_value(std::stod(count_value));
  if (kind == "string") pass.count = effects::Value::string_value(count_value);
  if (uniform != "-") pass.raw.emplace_back("countUniform", effects::Value::string_value(uniform));
  bool has_extent;
  std::cin >> has_extent;
  std::optional<std::array<std::size_t, 2>> extent;
  if (has_extent) {
    std::size_t w, h;
    std::cin >> w >> h;
    extent = std::array{w, h};
  }
  if (!std::cin) return 2;
  std::cout << effects::render_triangles(mesh, bindings, destination, pass, extent) << '\n';
  for (float value : destination.data()) std::cout << std::bit_cast<std::uint32_t>(value) << ' ';
  std::cout << '\n';
  for (auto value : destination.to_rgba8()) std::cout << static_cast<unsigned>(value) << ' ';
  std::cout << '\n';
}
