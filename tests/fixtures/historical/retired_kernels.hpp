#pragma once

#include "noisemaker/kernel.hpp"

namespace noisemaker::historical_generated {

[[nodiscard]] BoundKernel bind_filter_bc_bc(const glsl::Bindings& bindings);
[[nodiscard]] BoundKernel bind_filter_corrupt_corrupt(const glsl::Bindings& bindings);
[[nodiscard]] BoundKernel bind_filter_hs_hs(const glsl::Bindings& bindings);

}  // namespace noisemaker::historical_generated
