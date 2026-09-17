"""The custom_adapter admission surface for ``filter/snow:snow``.

``filter/snow`` is corpus-status ``adapter`` (see
``tools/glslcpp/check_corpus.py``'s ``_ADAPTERS``): the authority always
dispatches its hand-written CPU adapter (``src/effects/adapters/snow.js``),
never the typed kernel emitted from the *GLSL* it replaces. Unlike
``synth/remap:remap``, ``snow.glsl`` is perfectly typeable -- it is simply the
wrong ground truth: measured against the real adapter, the emitted typed
kernel diverged at 499 of 748 RGBA8 bytes (17x11). So, unlike
``remap_profile.py``, there is no retired frontend-authentication proof here
and no early return anywhere in ``generate_typed_slice.py`` or
``emit_typed_cpp.py`` -- the typed body for ``filter/snow:snow`` is still
generated exactly as before (it anchors the GLSL-declared uniform/sampler/
output shape and gives ``kCanonicalRoutes`` its ``emitted_factory``
provenance) and simply is not the function ``kCatalog`` dispatches: only the
canonical factory changes, exactly like ``classicNoisedeck/bitEffects``.

``bind_snow`` (``src/effects/snow.cpp``) reads exactly five bindings --
``inputTex``, ``alpha``, ``time``, ``pause``, ``density`` -- notably NOT
``resolution``, ``tileOffset``, or ``fullResolution``: every filter's GLSL
scaffold declares those three regardless of whether the shader body uses
them, but ``snow.js`` (the real ground truth) never binds them, so neither
does this port. ``custom_adapter_binding_abi``/``verify_custom_adapter_binding_abi``
below are the declared ABI and its drift guard, in exactly the shape
``tools/glslcpp/generate_typed_slice.py``'s ``_factory_route`` and
``tools/dsl/generate_backend_compatibility.py``'s ``_custom_factory_route``
already generalized for ``synth/remap:remap``: a small table maps a program
key to a factory-route builder, and each builder calls this module's
``verify_custom_adapter_binding_abi`` to fail closed if the declaration ever
drifts from ``include/noisemaker/effects/snow.hpp``'s own exported
``kBindingAbi`` contract table.
"""

from __future__ import annotations

import re

KEY = "filter/snow:snow"
SNOW_KEY = KEY

CUSTOM_ADAPTER_SOURCE = "src/effects/snow.cpp"
CUSTOM_ADAPTER_HEADER = "include/noisemaker/effects/snow.hpp"
CUSTOM_ADAPTER_FACTORY = "noisemaker::effects::bind_snow"


def custom_adapter_binding_abi() -> tuple[dict[str, str], ...]:
    """The explicit, hand-declared ABI for ``bind_snow``'s binding surface.

    In the exact order ``bind_snow()`` (``src/effects/snow.cpp``) reads them,
    which is also the exact order ``snowKernel`` (``snow.js``) reads
    ``$bindings``.
    """
    names = (
        ("inputTex", "sampler2D"),
        ("alpha", "double"),
        ("time", "double"),
        ("pause", "double"),
        ("density", "double"),
    )
    return tuple({"name": name, "cpp_type": cpp_type, "source": "custom_adapter"}
                 for name, cpp_type in names)


def verify_custom_adapter_binding_abi(repository) -> None:
    """Fail closed if ``snow.hpp``'s exported ``kBindingAbi`` table drifts
    from ``custom_adapter_binding_abi()``.
    """
    import pathlib
    header_path = pathlib.Path(repository) / CUSTOM_ADAPTER_HEADER
    header = header_path.read_text(encoding="utf-8")
    pairs = re.findall(r'\{"([^"]+)",\s*"([^"]+)"\}', header)
    if not pairs:
        raise ValueError(f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table not found")
    exported = {(name, cpp_type) for name, cpp_type in pairs}
    expected = {(item["name"], item["cpp_type"]) for item in custom_adapter_binding_abi()}
    if exported != expected:
        raise ValueError(
            f"{CUSTOM_ADAPTER_HEADER}: exported binding ABI table drifted "
            "from custom_adapter_binding_abi()'s declaration")


__all__ = (
    "KEY", "SNOW_KEY", "CUSTOM_ADAPTER_SOURCE", "CUSTOM_ADAPTER_HEADER",
    "CUSTOM_ADAPTER_FACTORY", "custom_adapter_binding_abi",
    "verify_custom_adapter_binding_abi",
)
