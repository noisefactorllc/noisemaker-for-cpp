#pragma once

// Chain bundle threading -- the C++ port of noisemaker-for-cpu's
// `{image, volume, geometry, volumeSize}` object renderer.js threads as a
// chain's "current" value once any step's own domain leaves plain 2D image
// territory. Every citation below is against src/runtime/renderer.js at the
// pinned authority revision (61aa869).
//
// Pure and side-effect-free, exactly like iteration.hpp: these functions
// take plain values (never a Surface, never the ResourceArena) and either
// return a value or throw std::invalid_argument on the exact violation the
// JS source itself throws on. The executor resolves every Surface-derived
// input (a produced volume's width/height, a bound "volumeSize" parameter)
// before calling in, and performs the actual arena work these decisions
// drive.
//
// Design: docs/port-engineering/chain-bundle-volume-geometry-threading.md.
// Summary of why there is no `is_chain_bundle`/`chain_bundle` pair here,
// unlike the JS original: JS needs them because a chain's "current" value
// is dynamically EITHER a bare Surface OR a `{image,...}` object, and has to
// tell which at runtime. This port's `GraphExecutor::execute()` instead
// threads image/volume/geometry/volumeSize as four separate, always-present
// values (image a `GraphResource*`, exactly as before this module landed;
// volume/geometry/volumeSize new, always null/nullopt for every image-domain
// effect) -- so there is no dynamic case to distinguish; every currently
// admitted effect simply never populates the three new ones.

#include <cstddef>
#include <optional>
#include <string_view>

namespace noisemaker::graph::bundle {

// renderer.js:1047 (and identically at 1181, 1316, 1462 -- the four
// dispatch sites JS has and this port folds to two, non-iterated and the
// iterated-group step, since there is no async variant here): `domain !==
// 'image' && domain !== 'loop-begin' && domain !== 'loop-end'`.
[[nodiscard]] bool is_volume_domain(std::string_view domain) noexcept;

// renderer.js:118-124 -- bundleOutput's four passthrough names. An empty
// name, or a name matching one of the three reserved input tokens, means
// "identity: hand back the input unchanged"; anything else looks the
// resource up under its own name (the executor's own concern, since that
// lookup is a real Surface fetch).
[[nodiscard]] bool is_passthrough_output_name(std::string_view name) noexcept;

// renderer.js:107-116 -- inheritVolumeSize. Called only when the step HAS an
// input volume; the caller is the one who knows whether it does at all.
// `step_declares_volume_size` mirrors `Object.hasOwn(params, 'volumeSize')`;
// `input_volume_width`/`height` are the input volume Surface's own extent.
// Returns the value the step's own "volumeSize" parameter binding should be
// overridden to (never touching a param the step doesn't declare at all,
// and never a domain outside volume-generator/volume-filter/volume-renderer
// -- both mirrored exactly), or nullopt when nothing should change (leave
// the step's own binding alone). Throws std::invalid_argument, naming
// `effect_id`, on the N x N^2 mismatch renderer.js:112-114 itself throws on.
[[nodiscard]] std::optional<double> inherit_volume_size(
    std::string_view effect_id, std::string_view domain,
    bool step_declares_volume_size, std::size_t input_volume_width,
    std::size_t input_volume_height);

// renderer.js:1053-1055 (identically at 1187-1189, 1322-1324, 1468-1470) --
// the volumeSize resolution ternary: a volume-generator resolves from its
// OWN params/produced-volume-width only (never the input bundle's, since a
// generator has no meaningful input volume); every other domain falls back
// through input bundle -> own params -> produced volume width, in that
// order. `produced_volume_width` is the width of whatever this step's own
// pass graph actually produced under its outputTex3d route this invocation
// (nullopt if it produced none).
[[nodiscard]] std::optional<double> resolve_volume_size(
    std::string_view domain, std::optional<double> step_params_volume_size,
    std::optional<double> input_bundle_volume_size,
    std::optional<std::size_t> produced_volume_width);

// renderer.js:1056-1063 (identically at 1190-1197, 1325-1334, 1471-1480) --
// the output-shape re-validation folded into one call: "isVolumeDomain and
// produced nothing under outputTex3d, on a domain that isn't volume-
// renderer" throws "did not produce outputTex3d"; a produced volume on a
// volume-generator/volume-filter domain must be exactly
// `volume_size x volume_size**2`, or throws naming both the expected and
// received shape. A volume-renderer or volume-filter/generator producing no
// volume, or the non-generator/filter domains (volume-renderer, and image/
// loop-begin/loop-end which aren't isVolumeDomain at all), are never
// shape-checked here, matching JS exactly.
void validate_volume_output_shape(
    std::string_view effect_id, std::string_view domain, bool produced_volume,
    std::optional<std::size_t> produced_volume_width,
    std::optional<std::size_t> produced_volume_height,
    std::optional<double> volume_size);

// renderer.js:1067 (identically at 1201, 1341, 1487): "did not produce
// outputTex" -- a non-volume-generator/filter domain that produced no image
// at all. Volume-generator/filter effects are exempt (their real output is
// the volume, not outputTex); every other domain (image, loop-begin/end,
// volume-renderer) must produce one.
[[nodiscard]] bool requires_output_image(std::string_view domain) noexcept;

}  // namespace noisemaker::graph::bundle
