#pragma once

#include <array>
#include <cstddef>
#include <string_view>
#include <utility>

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
// Hand-written CPU kernel for synth/remap:remap, mirroring the authority's
// hand-written JS adapter (src/effects/adapters/remap.js) operation-for-
// operation. See src/effects/remap.cpp for why this is hand-written rather
// than typed-generated.
[[nodiscard]] BoundKernel bind_remap(const glsl::Bindings& bindings);

// Declared contract for bind_remap's binding surface: every (name, cpp_type)
// pair it reads from `Bindings`, in the exact order bind_remap() reads them.
// bind_remap() builds these names at runtime (`"zone" + std::to_string(zone)
// + "_count"`, ...), so this table cannot be produced by scraping literal
// `b.get<T>("name")` text out of the source the way the generic
// custom-adapter binding-ABI extractor does for e.g. bit_effects.cpp.
// tools/dsl/generate_backend_compatibility.py's remap route instead declares
// its ABI explicitly and cross-checks its declared name/type set against
// this table (parsed as static text) -- the two are meant to be kept in
// lockstep by hand; a mismatch is the generator's signal that one drifted
// without the other. cpp_type strings match materialize_plan_value()'s
// vocabulary in src/graph/executor.cpp (double, glsl::Vec2, glsl::DVec3,
// glsl::DVec4) except "sampler2D", which marks a `Bindings::texture()` read
// rather than a `Bindings::get`/`get_or` uniform read.
inline constexpr std::size_t kRemapBindingAbiSize = 303U;
inline constexpr std::array<std::pair<std::string_view, std::string_view>, kRemapBindingAbiSize>
    kRemapBindingAbi{{
        {"tileOffset", "glsl::Vec2"}, {"fullResolution", "glsl::Vec2"}, {"resolution", "glsl::Vec2"}, {"zoneCount", "double"},
        {"smoothEdge", "double"}, {"bgColor", "glsl::DVec3"}, {"bgAlpha", "double"}, {"zone0_count", "double"},
        {"zone0_active", "double"}, {"zone0_alpha", "double"}, {"zone0_bounds", "glsl::DVec4"}, {"zone0_v0", "glsl::DVec4"},
        {"zone0_v1", "glsl::DVec4"}, {"zone0_v2", "glsl::DVec4"}, {"zone0_v3", "glsl::DVec4"}, {"zone0_v4", "glsl::DVec4"},
        {"zone0_v5", "glsl::DVec4"}, {"zone0_v6", "glsl::DVec4"}, {"zone0_v7", "glsl::DVec4"}, {"zone0_v8", "glsl::DVec4"},
        {"zone0_v9", "glsl::DVec4"}, {"zone0_v10", "glsl::DVec4"}, {"zone0_v11", "glsl::DVec4"}, {"zone0_v12", "glsl::DVec4"},
        {"zone0_v13", "glsl::DVec4"}, {"zone0_v14", "glsl::DVec4"}, {"zone0_v15", "glsl::DVec4"}, {"zone0_v16", "glsl::DVec4"},
        {"zone0_v17", "glsl::DVec4"}, {"zone0_v18", "glsl::DVec4"}, {"zone0_v19", "glsl::DVec4"}, {"zone0_v20", "glsl::DVec4"},
        {"zone0_v21", "glsl::DVec4"}, {"zone0_v22", "glsl::DVec4"}, {"zone0_v23", "glsl::DVec4"}, {"zone0_v24", "glsl::DVec4"},
        {"zone0_v25", "glsl::DVec4"}, {"zone0_v26", "glsl::DVec4"}, {"zone0_v27", "glsl::DVec4"}, {"zone0_v28", "glsl::DVec4"},
        {"zone0_v29", "glsl::DVec4"}, {"zone0_v30", "glsl::DVec4"}, {"zone0_v31", "glsl::DVec4"}, {"zone0_tex", "sampler2D"},
        {"zone1_count", "double"}, {"zone1_active", "double"}, {"zone1_alpha", "double"}, {"zone1_bounds", "glsl::DVec4"},
        {"zone1_v0", "glsl::DVec4"}, {"zone1_v1", "glsl::DVec4"}, {"zone1_v2", "glsl::DVec4"}, {"zone1_v3", "glsl::DVec4"},
        {"zone1_v4", "glsl::DVec4"}, {"zone1_v5", "glsl::DVec4"}, {"zone1_v6", "glsl::DVec4"}, {"zone1_v7", "glsl::DVec4"},
        {"zone1_v8", "glsl::DVec4"}, {"zone1_v9", "glsl::DVec4"}, {"zone1_v10", "glsl::DVec4"}, {"zone1_v11", "glsl::DVec4"},
        {"zone1_v12", "glsl::DVec4"}, {"zone1_v13", "glsl::DVec4"}, {"zone1_v14", "glsl::DVec4"}, {"zone1_v15", "glsl::DVec4"},
        {"zone1_v16", "glsl::DVec4"}, {"zone1_v17", "glsl::DVec4"}, {"zone1_v18", "glsl::DVec4"}, {"zone1_v19", "glsl::DVec4"},
        {"zone1_v20", "glsl::DVec4"}, {"zone1_v21", "glsl::DVec4"}, {"zone1_v22", "glsl::DVec4"}, {"zone1_v23", "glsl::DVec4"},
        {"zone1_v24", "glsl::DVec4"}, {"zone1_v25", "glsl::DVec4"}, {"zone1_v26", "glsl::DVec4"}, {"zone1_v27", "glsl::DVec4"},
        {"zone1_v28", "glsl::DVec4"}, {"zone1_v29", "glsl::DVec4"}, {"zone1_v30", "glsl::DVec4"}, {"zone1_v31", "glsl::DVec4"},
        {"zone1_tex", "sampler2D"}, {"zone2_count", "double"}, {"zone2_active", "double"}, {"zone2_alpha", "double"},
        {"zone2_bounds", "glsl::DVec4"}, {"zone2_v0", "glsl::DVec4"}, {"zone2_v1", "glsl::DVec4"}, {"zone2_v2", "glsl::DVec4"},
        {"zone2_v3", "glsl::DVec4"}, {"zone2_v4", "glsl::DVec4"}, {"zone2_v5", "glsl::DVec4"}, {"zone2_v6", "glsl::DVec4"},
        {"zone2_v7", "glsl::DVec4"}, {"zone2_v8", "glsl::DVec4"}, {"zone2_v9", "glsl::DVec4"}, {"zone2_v10", "glsl::DVec4"},
        {"zone2_v11", "glsl::DVec4"}, {"zone2_v12", "glsl::DVec4"}, {"zone2_v13", "glsl::DVec4"}, {"zone2_v14", "glsl::DVec4"},
        {"zone2_v15", "glsl::DVec4"}, {"zone2_v16", "glsl::DVec4"}, {"zone2_v17", "glsl::DVec4"}, {"zone2_v18", "glsl::DVec4"},
        {"zone2_v19", "glsl::DVec4"}, {"zone2_v20", "glsl::DVec4"}, {"zone2_v21", "glsl::DVec4"}, {"zone2_v22", "glsl::DVec4"},
        {"zone2_v23", "glsl::DVec4"}, {"zone2_v24", "glsl::DVec4"}, {"zone2_v25", "glsl::DVec4"}, {"zone2_v26", "glsl::DVec4"},
        {"zone2_v27", "glsl::DVec4"}, {"zone2_v28", "glsl::DVec4"}, {"zone2_v29", "glsl::DVec4"}, {"zone2_v30", "glsl::DVec4"},
        {"zone2_v31", "glsl::DVec4"}, {"zone2_tex", "sampler2D"}, {"zone3_count", "double"}, {"zone3_active", "double"},
        {"zone3_alpha", "double"}, {"zone3_bounds", "glsl::DVec4"}, {"zone3_v0", "glsl::DVec4"}, {"zone3_v1", "glsl::DVec4"},
        {"zone3_v2", "glsl::DVec4"}, {"zone3_v3", "glsl::DVec4"}, {"zone3_v4", "glsl::DVec4"}, {"zone3_v5", "glsl::DVec4"},
        {"zone3_v6", "glsl::DVec4"}, {"zone3_v7", "glsl::DVec4"}, {"zone3_v8", "glsl::DVec4"}, {"zone3_v9", "glsl::DVec4"},
        {"zone3_v10", "glsl::DVec4"}, {"zone3_v11", "glsl::DVec4"}, {"zone3_v12", "glsl::DVec4"}, {"zone3_v13", "glsl::DVec4"},
        {"zone3_v14", "glsl::DVec4"}, {"zone3_v15", "glsl::DVec4"}, {"zone3_v16", "glsl::DVec4"}, {"zone3_v17", "glsl::DVec4"},
        {"zone3_v18", "glsl::DVec4"}, {"zone3_v19", "glsl::DVec4"}, {"zone3_v20", "glsl::DVec4"}, {"zone3_v21", "glsl::DVec4"},
        {"zone3_v22", "glsl::DVec4"}, {"zone3_v23", "glsl::DVec4"}, {"zone3_v24", "glsl::DVec4"}, {"zone3_v25", "glsl::DVec4"},
        {"zone3_v26", "glsl::DVec4"}, {"zone3_v27", "glsl::DVec4"}, {"zone3_v28", "glsl::DVec4"}, {"zone3_v29", "glsl::DVec4"},
        {"zone3_v30", "glsl::DVec4"}, {"zone3_v31", "glsl::DVec4"}, {"zone3_tex", "sampler2D"}, {"zone4_count", "double"},
        {"zone4_active", "double"}, {"zone4_alpha", "double"}, {"zone4_bounds", "glsl::DVec4"}, {"zone4_v0", "glsl::DVec4"},
        {"zone4_v1", "glsl::DVec4"}, {"zone4_v2", "glsl::DVec4"}, {"zone4_v3", "glsl::DVec4"}, {"zone4_v4", "glsl::DVec4"},
        {"zone4_v5", "glsl::DVec4"}, {"zone4_v6", "glsl::DVec4"}, {"zone4_v7", "glsl::DVec4"}, {"zone4_v8", "glsl::DVec4"},
        {"zone4_v9", "glsl::DVec4"}, {"zone4_v10", "glsl::DVec4"}, {"zone4_v11", "glsl::DVec4"}, {"zone4_v12", "glsl::DVec4"},
        {"zone4_v13", "glsl::DVec4"}, {"zone4_v14", "glsl::DVec4"}, {"zone4_v15", "glsl::DVec4"}, {"zone4_v16", "glsl::DVec4"},
        {"zone4_v17", "glsl::DVec4"}, {"zone4_v18", "glsl::DVec4"}, {"zone4_v19", "glsl::DVec4"}, {"zone4_v20", "glsl::DVec4"},
        {"zone4_v21", "glsl::DVec4"}, {"zone4_v22", "glsl::DVec4"}, {"zone4_v23", "glsl::DVec4"}, {"zone4_v24", "glsl::DVec4"},
        {"zone4_v25", "glsl::DVec4"}, {"zone4_v26", "glsl::DVec4"}, {"zone4_v27", "glsl::DVec4"}, {"zone4_v28", "glsl::DVec4"},
        {"zone4_v29", "glsl::DVec4"}, {"zone4_v30", "glsl::DVec4"}, {"zone4_v31", "glsl::DVec4"}, {"zone4_tex", "sampler2D"},
        {"zone5_count", "double"}, {"zone5_active", "double"}, {"zone5_alpha", "double"}, {"zone5_bounds", "glsl::DVec4"},
        {"zone5_v0", "glsl::DVec4"}, {"zone5_v1", "glsl::DVec4"}, {"zone5_v2", "glsl::DVec4"}, {"zone5_v3", "glsl::DVec4"},
        {"zone5_v4", "glsl::DVec4"}, {"zone5_v5", "glsl::DVec4"}, {"zone5_v6", "glsl::DVec4"}, {"zone5_v7", "glsl::DVec4"},
        {"zone5_v8", "glsl::DVec4"}, {"zone5_v9", "glsl::DVec4"}, {"zone5_v10", "glsl::DVec4"}, {"zone5_v11", "glsl::DVec4"},
        {"zone5_v12", "glsl::DVec4"}, {"zone5_v13", "glsl::DVec4"}, {"zone5_v14", "glsl::DVec4"}, {"zone5_v15", "glsl::DVec4"},
        {"zone5_v16", "glsl::DVec4"}, {"zone5_v17", "glsl::DVec4"}, {"zone5_v18", "glsl::DVec4"}, {"zone5_v19", "glsl::DVec4"},
        {"zone5_v20", "glsl::DVec4"}, {"zone5_v21", "glsl::DVec4"}, {"zone5_v22", "glsl::DVec4"}, {"zone5_v23", "glsl::DVec4"},
        {"zone5_v24", "glsl::DVec4"}, {"zone5_v25", "glsl::DVec4"}, {"zone5_v26", "glsl::DVec4"}, {"zone5_v27", "glsl::DVec4"},
        {"zone5_v28", "glsl::DVec4"}, {"zone5_v29", "glsl::DVec4"}, {"zone5_v30", "glsl::DVec4"}, {"zone5_v31", "glsl::DVec4"},
        {"zone5_tex", "sampler2D"}, {"zone6_count", "double"}, {"zone6_active", "double"}, {"zone6_alpha", "double"},
        {"zone6_bounds", "glsl::DVec4"}, {"zone6_v0", "glsl::DVec4"}, {"zone6_v1", "glsl::DVec4"}, {"zone6_v2", "glsl::DVec4"},
        {"zone6_v3", "glsl::DVec4"}, {"zone6_v4", "glsl::DVec4"}, {"zone6_v5", "glsl::DVec4"}, {"zone6_v6", "glsl::DVec4"},
        {"zone6_v7", "glsl::DVec4"}, {"zone6_v8", "glsl::DVec4"}, {"zone6_v9", "glsl::DVec4"}, {"zone6_v10", "glsl::DVec4"},
        {"zone6_v11", "glsl::DVec4"}, {"zone6_v12", "glsl::DVec4"}, {"zone6_v13", "glsl::DVec4"}, {"zone6_v14", "glsl::DVec4"},
        {"zone6_v15", "glsl::DVec4"}, {"zone6_v16", "glsl::DVec4"}, {"zone6_v17", "glsl::DVec4"}, {"zone6_v18", "glsl::DVec4"},
        {"zone6_v19", "glsl::DVec4"}, {"zone6_v20", "glsl::DVec4"}, {"zone6_v21", "glsl::DVec4"}, {"zone6_v22", "glsl::DVec4"},
        {"zone6_v23", "glsl::DVec4"}, {"zone6_v24", "glsl::DVec4"}, {"zone6_v25", "glsl::DVec4"}, {"zone6_v26", "glsl::DVec4"},
        {"zone6_v27", "glsl::DVec4"}, {"zone6_v28", "glsl::DVec4"}, {"zone6_v29", "glsl::DVec4"}, {"zone6_v30", "glsl::DVec4"},
        {"zone6_v31", "glsl::DVec4"}, {"zone6_tex", "sampler2D"}, {"zone7_count", "double"}, {"zone7_active", "double"},
        {"zone7_alpha", "double"}, {"zone7_bounds", "glsl::DVec4"}, {"zone7_v0", "glsl::DVec4"}, {"zone7_v1", "glsl::DVec4"},
        {"zone7_v2", "glsl::DVec4"}, {"zone7_v3", "glsl::DVec4"}, {"zone7_v4", "glsl::DVec4"}, {"zone7_v5", "glsl::DVec4"},
        {"zone7_v6", "glsl::DVec4"}, {"zone7_v7", "glsl::DVec4"}, {"zone7_v8", "glsl::DVec4"}, {"zone7_v9", "glsl::DVec4"},
        {"zone7_v10", "glsl::DVec4"}, {"zone7_v11", "glsl::DVec4"}, {"zone7_v12", "glsl::DVec4"}, {"zone7_v13", "glsl::DVec4"},
        {"zone7_v14", "glsl::DVec4"}, {"zone7_v15", "glsl::DVec4"}, {"zone7_v16", "glsl::DVec4"}, {"zone7_v17", "glsl::DVec4"},
        {"zone7_v18", "glsl::DVec4"}, {"zone7_v19", "glsl::DVec4"}, {"zone7_v20", "glsl::DVec4"}, {"zone7_v21", "glsl::DVec4"},
        {"zone7_v22", "glsl::DVec4"}, {"zone7_v23", "glsl::DVec4"}, {"zone7_v24", "glsl::DVec4"}, {"zone7_v25", "glsl::DVec4"},
        {"zone7_v26", "glsl::DVec4"}, {"zone7_v27", "glsl::DVec4"}, {"zone7_v28", "glsl::DVec4"}, {"zone7_v29", "glsl::DVec4"},
        {"zone7_v30", "glsl::DVec4"}, {"zone7_v31", "glsl::DVec4"}, {"zone7_tex", "sampler2D"},
    }};
}  // namespace noisemaker::effects
