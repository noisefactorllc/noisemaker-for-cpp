"""Custom-adapter admission for ``filter/median:median``.

The authority never dispatches the typed kernel emitted from median.glsl.
It always runs its own hand-written CPU adapter
(``src/effects/adapters/median.js``), which reads RADIUS as a plain runtime
binding on every pixel (``$bindings.RADIUS | 0``) -- NOT a GLSL preprocessor
define. The typed emitter this profile used to feed (see
``median_frontend_profile.py``, kept unmodified as a correct record of that
proof-carrying admission) can only ever compile one exact RADIUS value per
generated program; ``filter/median:median``'s row baked RADIUS=2 while the
effect's own declared default is 3 (and 1 is also allowed), so any other
requested radius hit ``executor.cpp``'s compile-define-vs-requested-value
refusal before a kernel ever ran. ``filter/median:median`` is now
corpus-status ``adapter`` (see ``tools/glslcpp/check_corpus.py``
``_ADAPTERS``), dispatched instead through a hand-written kernel that
mirrors ``median.js`` operation-for-operation (see ``src/effects/median.cpp``,
``noisemaker::effects::bind_median``, and the oracle proof under
``docs/port-engineering/median-parity/``).

``custom_adapter_binding_abi``/``verify_custom_adapter_binding_abi`` below are
the admission surface: ``tools/glslcpp/generate_typed_slice.py``'s
``_factory_route`` and ``tools/dsl/generate_backend_compatibility.py``'s
``_custom_factory_route`` each add this key to their custom-adapter table and
call ``custom_adapter_binding_abi()`` for its declared ABI -- not regex-
scraped the way bit_effects.cpp's literal ``b.get<T>("name")`` calls are,
even though ``bind_median`` (unlike ``bind_remap``) COULD be scraped that
way (every one of its reads is a literal call, not a runtime-built name):
this is declared explicitly anyway, to register exactly the way
``synth/remap:remap`` does. Both generators call
``verify_custom_adapter_binding_abi`` to fail closed if that declaration
ever drifts from ``include/noisemaker/effects/median.hpp``'s own exported
``kMedianBindingAbi`` contract table.

RADIUS is declared here with cpp_type ``std::int32_t`` (matching
``materialize_plan_value``'s vocabulary in ``src/graph/executor.cpp``, the
same type bit_effects.cpp's MODE/FORMULA/etc. compile defines use) even
though ``bind_median`` itself reads it leniently
(``b.get_or<std::int32_t>("RADIUS", 2)``, falling back to the typed
emitter's old sole baked value for any caller built against the pre-
custom-adapter ABI, which never carried RADIUS as a binding at all).
"""

from __future__ import annotations

import pathlib
import re

KEY = "filter/median:median"
MEDIAN_KEY = KEY

CUSTOM_ADAPTER_SOURCE = "src/effects/median.cpp"
CUSTOM_ADAPTER_HEADER = "include/noisemaker/effects/median.hpp"
CUSTOM_ADAPTER_FACTORY = "noisemaker::effects::bind_median"


def custom_adapter_binding_abi() -> tuple[dict[str, str], ...]:
    """The explicit, hand-declared ABI for ``bind_median``'s binding surface.

    In the exact order ``bind_median()`` (``src/effects/median.cpp``) reads
    them. Cross-checked against ``median.hpp``'s own exported
    ``kMedianBindingAbi`` table by ``verify_custom_adapter_binding_abi``
    below -- the two are meant to be kept in lockstep by hand; a mismatch
    there is the generator's signal that one drifted without the other.
    """
    names: tuple[tuple[str, str], ...] = (
        ("RADIUS", "std::int32_t"),
        ("threshold", "float"),
        ("inputTex", "sampler2D"),
    )
    return tuple({"name": name, "cpp_type": cpp_type, "source": "custom_adapter"}
                for name, cpp_type in names)


def verify_custom_adapter_binding_abi(repository) -> None:
    """Fail closed if ``median.hpp``'s exported ``kMedianBindingAbi`` table
    drifts from ``custom_adapter_binding_abi()``.
    """
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
    "KEY", "MEDIAN_KEY", "CUSTOM_ADAPTER_SOURCE", "CUSTOM_ADAPTER_HEADER",
    "CUSTOM_ADAPTER_FACTORY", "custom_adapter_binding_abi",
    "verify_custom_adapter_binding_abi",
)
