"""The custom_adapter admission surface for the authority's f32-color adapters.

The authority renders ``filter/pixelSort:luminance``,
``filter/reindex:nmReindexStats`` and ``filter/reindex:nmReindexApply`` with
its hand-written CPU adapters (``src/effects/adapters/f32-color.js``): its
``kernelFactories`` map spreads ``canonicalAdapterFactories`` over the
transpiled factories, so the transpiled kernels of these three programs never
run. ``src/effects/f32_color.cpp`` ports the adapters. As for
``filter/snow:snow`` and ``filter/crt:crt``, the typed bodies of the GLSL
programs are still generated (they anchor the declared interface and the
``emitted_factory`` provenance) and only the canonical factory changes.

Each ``bind_*`` reads exactly the bindings its JS factory reads, in the same
order. ``verify_custom_adapter_binding_abi`` fails closed if a declaration
drifts from the matching table in ``include/noisemaker/effects/f32_color.hpp``.
"""

from __future__ import annotations

import re

PIXEL_SORT_LUMINANCE_KEY = "filter/pixelSort:luminance"
REINDEX_STATS_KEY = "filter/reindex:nmReindexStats"
REINDEX_APPLY_KEY = "filter/reindex:nmReindexApply"
KEYS = (PIXEL_SORT_LUMINANCE_KEY, REINDEX_STATS_KEY, REINDEX_APPLY_KEY)

CUSTOM_ADAPTER_SOURCE = "src/effects/f32_color.cpp"
CUSTOM_ADAPTER_HEADER = "include/noisemaker/effects/f32_color.hpp"

# key -> (C++ factory, C++ binding name, header ABI table, ordered bindings)
_ADAPTERS = {
    PIXEL_SORT_LUMINANCE_KEY: (
        "noisemaker::effects::bind_pixel_sort_luminance", "bind_pixel_sort_luminance",
        "kPixelSortLuminanceBindingAbi", (("inputTex", "sampler2D"),)),
    REINDEX_STATS_KEY: (
        "noisemaker::effects::bind_reindex_stats", "bind_reindex_stats",
        "kReindexStatsBindingAbi", (("inputTex", "sampler2D"),)),
    REINDEX_APPLY_KEY: (
        "noisemaker::effects::bind_reindex_apply", "bind_reindex_apply",
        "kReindexApplyBindingAbi",
        (("inputTex", "sampler2D"), ("statsTex", "sampler2D"), ("uDisplacement", "double"))),
}

CUSTOM_ADAPTER_FACTORIES = {key: value[0] for key, value in _ADAPTERS.items()}


def bind_function(key: str) -> str:
    """The unqualified C++ binding function of ``key``."""
    return _ADAPTERS[key][1]


def custom_adapter_binding_abi(key: str) -> tuple[dict[str, str], ...]:
    """The hand-declared ABI of ``key``'s factory, in the order it reads the bindings."""
    return tuple({"name": name, "cpp_type": cpp_type, "source": "custom_adapter"}
                 for name, cpp_type in _ADAPTERS[key][3])


def verify_custom_adapter_binding_abi(repository, key: str) -> None:
    """Fail closed if ``f32_color.hpp``'s exported table for ``key`` drifts."""
    import pathlib
    header = (pathlib.Path(repository) / CUSTOM_ADAPTER_HEADER).read_text(encoding="utf-8")
    table = _ADAPTERS[key][2]
    match = re.search(rf"\b{table}\{{\{{(.*?)\}}\}};", header, re.DOTALL)
    if match is None:
        raise ValueError(f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table {table} not found")
    exported = re.findall(r'\{"([^"]+)",\s*"([^"]+)"\}', match.group(1))
    expected = [(item["name"], item["cpp_type"]) for item in custom_adapter_binding_abi(key)]
    if exported != expected:
        raise ValueError(
            f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table {table} drifted "
            "from custom_adapter_binding_abi()'s declaration")


__all__ = (
    "PIXEL_SORT_LUMINANCE_KEY", "REINDEX_STATS_KEY", "REINDEX_APPLY_KEY", "KEYS",
    "CUSTOM_ADAPTER_SOURCE", "CUSTOM_ADAPTER_HEADER", "CUSTOM_ADAPTER_FACTORIES",
    "bind_function", "custom_adapter_binding_abi", "verify_custom_adapter_binding_abi",
)
