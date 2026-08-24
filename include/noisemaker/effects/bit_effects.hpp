#pragma once

#include "noisemaker/kernel.hpp"

namespace noisemaker::effects {
[[nodiscard]] BoundKernel bind_bit_effects(const glsl::Bindings& bindings);
}
