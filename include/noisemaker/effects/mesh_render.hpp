#pragma once

#include <cstddef>

namespace noisemaker {
class Surface;
namespace glsl { class Bindings; }
namespace graph { struct MeshData; }
namespace effects {
// Full-pass CPU mesh adapter. Scalar bindings retain JS Number precision;
// colors/light use DVec3 and optional fullResolution uses DVec2. Mesh texels
// are RGBA32F in upload order. Missing texel lanes are read as NaN.
[[nodiscard]] std::size_t render_triangles(const graph::MeshData& mesh,
                                          const glsl::Bindings& bindings,
                                          Surface& destination);
}  // namespace effects
}  // namespace noisemaker
