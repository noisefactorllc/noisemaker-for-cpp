"""The custom_adapter admission surface for ``filter/crt:crt``.

Since noisemaker-for-cpu 7f47340 the authority dispatches its hand-written
CPU adapter for ``filter/crt:crt`` (``src/effects/adapters/crt.js``), a
direct float32 translation of ``crt.glsl`` in the Metal evaluation order,
instead of the transpiled kernel. ``bind_crt`` (``src/effects/crt.cpp``)
ports that adapter. As for ``filter/snow:snow``, the typed body of
``crt.glsl`` is still generated (it anchors the declared interface and the
``emitted_factory`` provenance) and only the canonical factory changes.

``bind_crt`` reads the nine bindings that ``crtFactory`` reads, in the same
order. ``verify_custom_adapter_binding_abi`` fails closed if this declaration
drifts from ``include/noisemaker/effects/crt.hpp``'s exported
``kCrtBindingAbi`` table.
"""

from __future__ import annotations

import re

KEY = "filter/crt:crt"
CRT_ADAPTER_KEY = KEY

CUSTOM_ADAPTER_SOURCE = "src/effects/crt.cpp"
CUSTOM_ADAPTER_HEADER = "include/noisemaker/effects/crt.hpp"
CUSTOM_ADAPTER_FACTORY = "noisemaker::effects::bind_crt"


def custom_adapter_binding_abi() -> tuple[dict[str, str], ...]:
    """The hand-declared ABI of ``bind_crt``, in the order it reads the bindings."""
    names = (
        ("inputTex", "sampler2D"),
        ("resolution", "glsl::Vec2"),
        ("tileOffset", "glsl::Vec2"),
        ("renderScale", "double"),
        ("alpha", "double"),
        ("fullResolution", "glsl::Vec2"),
        ("time", "double"),
        ("speed", "double"),
        ("seed", "std::int32_t"),
    )
    return tuple({"name": name, "cpp_type": cpp_type, "source": "custom_adapter"}
                 for name, cpp_type in names)


def verify_custom_adapter_binding_abi(repository) -> None:
    """Fail closed if ``crt.hpp``'s exported ``kCrtBindingAbi`` table drifts."""
    import pathlib
    header_path = pathlib.Path(repository) / CUSTOM_ADAPTER_HEADER
    header = header_path.read_text(encoding="utf-8")
    pairs = re.findall(r'\{"([^"]+)",\s*"([^"]+)"\}', header)
    if not pairs:
        raise ValueError(f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table not found")
    exported = [(name, cpp_type) for name, cpp_type in pairs]
    expected = [(item["name"], item["cpp_type"]) for item in custom_adapter_binding_abi()]
    if exported != expected:
        raise ValueError(
            f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table drifted "
            "from custom_adapter_binding_abi()'s declaration")


__all__ = (
    "KEY", "CRT_ADAPTER_KEY", "CUSTOM_ADAPTER_SOURCE", "CUSTOM_ADAPTER_HEADER",
    "CUSTOM_ADAPTER_FACTORY", "custom_adapter_binding_abi",
    "verify_custom_adapter_binding_abi",
)
