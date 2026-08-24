#pragma once

// Flat list of per-effect scatter-adapter registration functions, mirroring
// `noisemaker/generated/catalog.hpp`'s flat `bind_*` declaration style
// (rather than self-registering static-init globals). Add one declaration
// here plus one call in `register_builtin_scatter_adapters()`
// (catalog.cpp) per new scatter adapter -- e.g. when porting DLA's
// `depositGrid`, Lenia's `deposit`, Physarum's `deposit`, pointsRender's
// `deposit`, pointsBillboardRender's `deposit`, or flow3d's `deposit` (the
// six other JS scatter adapters registered in scatter-registry.js).

namespace noisemaker::scatter {

// Call exactly once during process/test startup, before any pass dispatch
// may need a scatter adapter (analogous to how the JS side's
// scatter-registry.js registrations run at module-load time via its own
// imports -- but explicit here rather than implicit, per this file's
// no-static-init-magic convention).
void register_builtin_scatter_adapters();

}  // namespace noisemaker::scatter
