#pragma once

#include <array>
#include <cstddef>
#include <optional>

namespace noisemaker {
class Surface;
namespace glsl { class Bindings; }
namespace graph { struct MeshData; }
namespace effects {
struct PassDefinition;
// Full-pass CPU mesh adapter. Scalar bindings retain JS Number precision;
// colors/light use DVec3 and optional fullResolution uses DVec2. Mesh texels
// are RGBA32F in upload order. Missing texel lanes are read as NaN.
[[nodiscard]] std::size_t render_triangles(const graph::MeshData& mesh,
                                          const glsl::Bindings& bindings,
                                          Surface& destination);
// input_extent is the extent of the bound meshPositions sampler, falling
// back to inputTex when absent. With neither sampler an extent count draws
// one triangle, subject to the number of complete position texels.
[[nodiscard]] std::size_t render_triangles(
    const graph::MeshData& mesh, const glsl::Bindings& bindings,
    Surface& destination, const PassDefinition& pass,
    std::optional<std::array<std::size_t, 2>> input_extent);
}  // namespace effects
}  // namespace noisemaker
