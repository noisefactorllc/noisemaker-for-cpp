#pragma once

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
// Hand-written CPU kernel for synth/remap:remap, mirroring the authority's
// hand-written JS adapter (src/effects/adapters/remap.js) operation-for-
// operation. See src/effects/remap.cpp for why: the authority's own GLSL
// transpiler cannot lower remap's `struct ZoneTest`, and (unlike the other
// corpus-status "adapter" programs) the JS adapter itself is not a faithful
// float32 mirror of the GLSL -- it computes in plain JS doubles and rounds
// to float32 only once, at the final output store -- so a typed-generated
// C++ kernel (which rounds after every operation, matching GLSL semantics)
// cannot be bit-exact against it either. This kernel instead reads the same
// semantic uniforms the adapter reads and matches its double-precision
// arithmetic exactly.
[[nodiscard]] BoundKernel bind_remap(const glsl::Bindings& bindings);
}  // namespace noisemaker::effects
