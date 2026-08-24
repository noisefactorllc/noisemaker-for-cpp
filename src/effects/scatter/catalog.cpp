#include "noisemaker/effects/scatter/catalog.hpp"

#include "noisemaker/effects/scatter/wormhole.hpp"

namespace noisemaker::scatter {

// Idempotent by design: `register_scatter_adapter` itself still throws on a
// genuine duplicate KEY (catching real registration bugs), but this
// aggregate entry point is meant to be called defensively from multiple
// independent call sites (test fixtures, future subsystem init paths) --
// exactly once for real, silently a no-op after that.
void register_builtin_scatter_adapters() {
  static bool registered = [] {
    wormhole::register_adapter();
    // Six more calls land here as the remaining scatter adapters are ported:
    // dla::register_adapter(); lenia::register_adapter();
    // physarum::register_adapter(); points_render::register_adapter();
    // points_billboard_render::register_adapter(); flow3d::register_adapter();
    return true;
  }();
  static_cast<void>(registered);
}

}  // namespace noisemaker::scatter
