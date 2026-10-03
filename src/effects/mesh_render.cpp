#include "noisemaker/effects/mesh_render.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

#include "noisemaker/fdlibm.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/graph/executor.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/surface.hpp"

// Operation-for-operation port of CPU26d src/effects/cpu/mesh-render.js.
// All arithmetic locals stay double; r() marks exactly Math.fround calls.
namespace noisemaker::effects {
namespace {
using V3 = std::array<double, 3>;
using M3 = std::array<double, 9>;
[[nodiscard]] double r(double value) noexcept { return static_cast<double>(noisemaker::f32(value)); }
[[nodiscard]] V3 vec(double x, double y, double z) noexcept { return {r(x), r(y), r(z)}; }
[[nodiscard]] double max_zero(double x) noexcept { return x == 0 ? 0 : std::max(x, 0.0); }
[[nodiscard]] V3 normalize(const V3& v) noexcept {
  const double len_sq = r(r(r(v[0] * v[0]) + r(v[1] * v[1])) + r(v[2] * v[2]));
  if (len_sq == 0) return {0, 0, 0};
  const double inv_len = r(1 / std::sqrt(len_sq));
  return vec(r(v[0] * inv_len), r(v[1] * inv_len), r(v[2] * inv_len));
}
[[nodiscard]] M3 multiply(const M3& a, const M3& b) noexcept {
  M3 out{};
  for (std::size_t col = 0; col < 3; ++col) {
    for (std::size_t row = 0; row < 3; ++row) {
      out[col * 3 + row] = r(r(a[row] * b[col * 3]) + r(a[3 + row] * b[col * 3 + 1]) + r(a[6 + row] * b[col * 3 + 2]));
    }
  }
  return out;
}
[[nodiscard]] V3 apply_matrix(const M3& m, const V3& v) noexcept {
  return vec(r(r(m[0] * v[0]) + r(m[3] * v[1]) + r(m[6] * v[2])),
             r(r(m[1] * v[0]) + r(m[4] * v[1]) + r(m[7] * v[2])),
             r(r(m[2] * v[0]) + r(m[5] * v[1]) + r(m[8] * v[2])));
}
[[nodiscard]] V3 vector_binding(const glsl::Bindings& b, const char* name) {
  const auto v = b.get<glsl::DVec3>(name);
  return {v[0], v[1], v[2]};
}
struct Uniforms {
  double mesh_scale, mesh_offset_x, mesh_offset_y, mesh_offset_z;
  double rotate_x, rotate_y, rotate_z, pos_x, pos_y, view_scale, aspect;
  double diffuse_intensity, specular_intensity, shininess, rim_power, rim_intensity, wireframe;
  V3 light_direction, mesh_color, ambient_color, diffuse_color, specular_color;
};
struct Vertex { double px, py, z; V3 normal; };
[[nodiscard]] Vertex vertex(const V3& input_position, const V3& input_normal,
                            const Uniforms& u, double width, double height) noexcept {
  V3 position = vec(input_position[0], input_position[1], input_position[2]);
  const V3 normal = vec(input_normal[0], input_normal[1], input_normal[2]);
  position = vec(r(position[0] * u.mesh_scale), r(position[1] * u.mesh_scale), r(position[2] * u.mesh_scale));
  position = vec(r(position[0] + u.mesh_offset_x), r(position[1] + u.mesh_offset_y), r(position[2] + u.mesh_offset_z));
  const double deg2rad = r(3.14159265 / 180.0);
  const double rx = r(u.rotate_x * deg2rad), ry = r(u.rotate_y * deg2rad), rz = r(u.rotate_z * deg2rad);
  const double cx = r(fdlibm::cos(rx)), sx = r(fdlibm::sin(rx));
  const double cy = r(fdlibm::cos(ry)), sy = r(fdlibm::sin(ry));
  const double cz = r(fdlibm::cos(rz)), sz = r(fdlibm::sin(rz));
  const M3 rot_x{1, 0, 0, 0, cx, sx, 0, -sx, cx};
  const M3 rot_y{cy, 0, sy, 0, 1, 0, -sy, 0, cy};
  const M3 rot_z{cz, -sz, 0, sz, cz, 0, 0, 0, 1};
  const M3 rotation = multiply(multiply(rot_z, rot_y), rot_x);
  V3 rotated_pos = apply_matrix(rotation, position);
  const V3 rotated_normal = apply_matrix(rotation, normal);
  rotated_pos[0] = r(rotated_pos[0] + u.pos_x);
  rotated_pos[1] = r(rotated_pos[1] + u.pos_y);
  double clip_x = r(rotated_pos[0] * u.view_scale);
  const double clip_y = r(rotated_pos[1] * u.view_scale);
  clip_x = r(clip_x / u.aspect);
  const double ndc_z = r(r(rotated_pos[2] - -10.0) / r(10.0 - -10.0));
  return {r(r(r(clip_x + 1) * 0.5) * width), r(r(r(clip_y + 1) * 0.5) * height), ndc_z, rotated_normal};
}
[[nodiscard]] bool fragment(const V3& v_normal, const Uniforms& u,
                            const V3& ndx, const V3& ndy, V3& color) noexcept {
  const V3 normal = normalize(v_normal);
  const V3 light_dir = normalize(vec(u.light_direction[0], u.light_direction[1], u.light_direction[2]));
  const V3 view_dir = vec(0, 0, 1);
  const V3 mesh_color = vec(u.mesh_color[0], u.mesh_color[1], u.mesh_color[2]);
  const V3 ambient = vec(r(u.ambient_color[0] * mesh_color[0]), r(u.ambient_color[1] * mesh_color[1]), r(u.ambient_color[2] * mesh_color[2]));
  const double diffuse_factor = max_zero(r(normal[0] * light_dir[0] + normal[1] * light_dir[1] + normal[2] * light_dir[2]));
  V3 diffuse{};
  for (std::size_t i = 0; i < 3; ++i) diffuse[i] = r(r(u.diffuse_color[i] * diffuse_factor) * mesh_color[i] * u.diffuse_intensity);
  const V3 half_dir = normalize(vec(r(light_dir[0] + view_dir[0]), r(light_dir[1] + view_dir[1]), r(light_dir[2] + view_dir[2])));
  const double spec_angle = max_zero(r(half_dir[0] * normal[0] + half_dir[1] * normal[1] + half_dir[2] * normal[2]));
  const double specular_factor = spec_angle == 0 && u.shininess == 0 ? 1 : fdlibm::pow(spec_angle, u.shininess);
  V3 specular{};
  for (std::size_t i = 0; i < 3; ++i) specular[i] = r(r(u.specular_color[i] * r(specular_factor)) * u.specular_intensity);
  const double rim_base = r(1 - max_zero(r(normal[0] * view_dir[0] + normal[1] * view_dir[1] + normal[2] * view_dir[2])));
  const double rim = rim_base == 0 && u.rim_power == 0 ? 1 : fdlibm::pow(rim_base, u.rim_power);
  const V3 rim_light = vec(r(rim * u.rim_intensity), r(rim * u.rim_intensity), r(rim * u.rim_intensity));
  for (std::size_t i = 0; i < 3; ++i) color[i] = r(r(ambient[i] + diffuse[i]) + r(specular[i] + rim_light[i]));
  if (u.wireframe == 1) {
    const double normal_edge = r(r(fdlibm::hypot(r(ndx[0]), r(ndx[1]), r(ndx[2])) + fdlibm::hypot(r(ndy[0]), r(ndy[1]), r(ndy[2]))));
    if (normal_edge < 0.1) return false;
    color = vec(mesh_color[0], mesh_color[1], mesh_color[2]);
  }
  const double gamma = r(1 / 2.2);
  color = vec(r(fdlibm::pow(color[0], gamma)), r(fdlibm::pow(color[1], gamma)), r(fdlibm::pow(color[2], gamma)));
  return true;
}
[[nodiscard]] double lane(const std::vector<float>& data, std::size_t index) noexcept {
  return index < data.size() ? static_cast<double>(data[index]) : std::numeric_limits<double>::quiet_NaN();
}
}  // namespace

std::size_t render_triangles(const graph::MeshData& mesh, const glsl::Bindings& bindings, Surface& destination) {
  const double width = static_cast<double>(destination.width()), height = static_cast<double>(destination.height());
  const auto full_resolution = bindings.get_or<glsl::DVec2>("fullResolution", glsl::DVec2(width, height));
  const Uniforms u{
      bindings.get_number("meshScale"), bindings.get_number("meshOffsetX"), bindings.get_number("meshOffsetY"), bindings.get_number("meshOffsetZ"),
      bindings.get_number("rotateX"), bindings.get_number("rotateY"), bindings.get_number("rotateZ"), bindings.get_number("posX"), bindings.get_number("posY"), bindings.get_number("viewScale"), r(full_resolution[0] / full_resolution[1]),
      bindings.get_number("diffuseIntensity"), bindings.get_number("specularIntensity"), bindings.get_number("shininess"), bindings.get_number("rimPower"), bindings.get_number("rimIntensity"), bindings.get_or<double>("wireframe", 0),
      vector_binding(bindings, "lightDirection"), vector_binding(bindings, "meshColor"), vector_binding(bindings, "ambientColor"), vector_binding(bindings, "diffuseColor"), vector_binding(bindings, "specularColor")};
  if (mesh.tex_width != 0 && mesh.tex_height > std::numeric_limits<std::size_t>::max() / mesh.tex_width / 4) {
    throw std::invalid_argument("mesh texture dimensions overflow");
  }
  std::vector<float> depth(destination.width() * destination.height(), 1.0F);
  std::size_t covered = 0;
  const std::size_t triangle_count = mesh.tex_width * mesh.tex_height / 3;
  for (std::size_t tri = 0; tri < triangle_count; ++tri) {
    std::array<Vertex, 3> verts{};
    bool all_invalid = true;
    for (std::size_t v = 0; v < 3; ++v) {
      const std::size_t pi = (tri * 3 + v) * 4;
      if (lane(mesh.position_data, pi + 3) != 0) all_invalid = false;
      verts[v] = vertex({lane(mesh.position_data, pi), lane(mesh.position_data, pi + 1), lane(mesh.position_data, pi + 2)},
                        {lane(mesh.normal_data, pi), lane(mesh.normal_data, pi + 1), lane(mesh.normal_data, pi + 2)}, u, width, height);
    }
    if (all_invalid) continue;
    const auto& v0 = verts[0]; const auto& v1 = verts[1]; const auto& v2 = verts[2];
    const double area = r(r(r(v1.px - v0.px) * r(v2.py - v0.py)) - r(r(v2.px - v0.px) * r(v1.py - v0.py)));
    if (!(area > 0)) continue;
    const double det = r(r(r(v0.px * r(v1.py - v2.py)) + r(v1.px * r(v2.py - v0.py))) + r(v2.px * r(v0.py - v1.py)));
    V3 ndx{0, 0, 0}, ndy{0, 0, 0};
    if (u.wireframe == 1 && det != 0) {
      for (std::size_t c = 0; c < 3; ++c) {
        ndx[c] = r((r(r(v0.normal[c] * r(v1.py - v2.py)) + r(v1.normal[c] * r(v2.py - v0.py))) + r(v2.normal[c] * r(v0.py - v1.py))) / det);
        ndy[c] = r((r(r(v0.normal[c] * r(v2.px - v1.px)) + r(v1.normal[c] * r(v0.px - v2.px))) + r(v2.normal[c] * r(v1.px - v0.px))) / det);
      }
    }
    const double min_x = std::max(0.0, std::floor(std::min({v0.px, v1.px, v2.px}) - 0.5));
    const double max_x = std::min(width - 1, std::ceil(std::max({v0.px, v1.px, v2.px}) - 0.5));
    const double min_y = std::max(0.0, std::floor(std::min({v0.py, v1.py, v2.py}) - 0.5));
    const double max_y = std::min(height - 1, std::ceil(std::max({v0.py, v1.py, v2.py}) - 0.5));
    for (double py_gl = min_y; py_gl <= max_y; ++py_gl) {
      const double row = height - 1 - py_gl;
      const double cy = r(py_gl + 0.5);
      for (double px_gl = min_x; px_gl <= max_x; ++px_gl) {
        const double cx = r(px_gl + 0.5);
        const double b0 = r(r(r(v1.px - v0.px) * r(cy - v0.py)) - r(r(v1.py - v0.py) * r(cx - v0.px))) / area;
        const double b1 = r(r(r(v2.px - v1.px) * r(cy - v1.py)) - r(r(v2.py - v1.py) * r(cx - v1.px))) / area;
        const double b2 = 1 - r(b0 + b1);
        if (!(b0 >= 0 && b1 >= 0 && b2 >= 0)) continue;
        const double z = r(r(r(b0 * v0.z) + r(b1 * v1.z)) + r(b2 * v2.z));
        const auto depth_index = static_cast<std::size_t>(row) * destination.width() + static_cast<std::size_t>(px_gl);
        if (!(z < depth[depth_index])) continue;
        depth[depth_index] = static_cast<float>(z);
        V3 normal{};
        for (std::size_t c = 0; c < 3; ++c) normal[c] = r(r(r(b0 * v0.normal[c]) + r(b1 * v1.normal[c])) + r(b2 * v2.normal[c]));
        V3 color{};
        if (!fragment(normal, u, ndx, ndy, color)) continue;
        for (std::size_t c = 0; c < 3; ++c) destination.data()[depth_index * 4 + c] = static_cast<float>(color[c]);
        destination.data()[depth_index * 4 + 3] = 1;
        ++covered;
      }
    }
  }
  return covered;
}
}  // namespace noisemaker::effects
