"""Second-order probe: if 'unsupported global declaration' were generalized to
admit ANY const scalar/vector/matrix/array global (not just const float
scalar), what's the NEXT blocker for each of the 27 purely-const-typed
members of that family? (The other 3 members -- cellRefract, kaleido,
synth/shape -- have a non-const global and are reported separately; they are
NOT patched to pass, since that is a structurally different, more invasive
capability: mutable module-level state.)

Technique: this admission rule is inline logic inside two functions
(generate_typed_slice.validate_capabilities, and the
emit_typed_cpp._Emitter._validate_source_globals method), not a flag read out
of gen.APPROVED_CAPABILITIES / gen._BUILTINS / emit._BUILTIN_NAMES. Those
lists cannot express "admit const non-float globals". So instead of adding to
a list (as tools/glslcpp future-precompute/analyze_candidates.py does for
builtins), we source-patch a COPY of each function: pull the source via
inspect.getsource, apply narrow, explicit text substitutions that relax only
the float-scalar-only global-admission rule (and extend the const-global
initializer walker to also recurse into constructor expressions, e.g.
vec3(...)/mat3(...)/array literals, which real vector/matrix/array globals
will use), exec the patched source against the module's own globals dict, and
monkeypatch the *function object* (module-level function, or class method)
back onto the module for the duration of the probe only. Everything is
restored in `finally`. No file in the repo is written.

This is a best-effort simulation of "the global-admission rule was
generalized," not a guarantee that a real capability implementation would
look exactly like this patch. Downstream code (matrix/vector arithmetic
checks, array-index bounds proofs, C++ codegen for non-scalar globals) is
UNCHANGED by this patch, so whatever blocker appears next is real evidence of
what remains -- but if the patch itself is too permissive or too strict in a
spot the real implementation would handle differently, the second-order
blocker for that one key could differ. Every result is watched for exceptions
raised BY the patch's own bugs (e.g. AttributeError from a construct-kind
value lacking an expected field) and reported distinctly from ordinary
GeneratorError/TypedEmissionError domain errors.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

# The 27 keys whose ONLY blocking declarations are const-but-non-float
# (established by probe_globals.py's AST classification). Excludes the 3
# non-const-global keys (cellRefract, kaleido, synth/shape).
PURE_CONST_TYPE_KEYS = [
    "classicNoisedeck/bitEffects:bitEffects",
    "classicNoisedeck/cellNoise:cellNoise",
    "classicNoisedeck/colorLab:colorLab",
    "classicNoisedeck/moodscape:moodscape",
    "classicNoisedeck/shapeMixer:shapeMixer",
    "classicNoisedeck/shapes:shapes",
    "filter/adjust:adjust",
    "filter/colorspace:colorspace",
    "filter/edge:edge",
    "filter/emboss:emboss",
    "filter/fxaa:fxaa",
    "filter/glyphMap:glyphMap",
    "filter/grade:creative",
    "filter/grade:hslSecondary",
    "filter/grade:primary",
    "filter/grade:vignette",
    "filter/grade:wheels",
    "filter/grain:grain",
    "filter/historicPalette:historicPalette",
    "filter/normalMap:normalMap",
    "filter/osd:osd",
    "filter/palette:palette",
    "filter/scanlineError:scanlineError",
    "filter/snow:snow",
    "filter/spookyTicker:spookyTicker",
    "filter/texture:texture",
    "filter/wobble:wobble",
]

NON_CONST_GLOBAL_KEYS = [
    "classicNoisedeck/cellRefract:cellRefract",
    "classicNoisedeck/kaleido:kaleido",
    "synth/shape:shape",
]


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, typed


def first(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


# --- Build the patched validate_capabilities (generate_typed_slice.py) -----

_ORIGINAL_VALIDATE_SRC = inspect.getsource(gen.validate_capabilities)

_NEEDLE_1 = (
    '        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
    '\n'
    '        def global_initializer(value) -> None:\n'
    '            if value.type != FLOAT:\n'
    '                raise GeneratorError(f"{location(value)}: unsupported global initializer type {value.type.display()}")\n'
    '            if value.kind == "literal":\n'
)
_REPLACEMENT_1 = (
    '        if storage != "const" or declaration.initializer is None:\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
    '\n'
    '        def global_initializer(value) -> None:\n'
    '            if value.kind == "construct":\n'
    '                for child in value.children:\n'
    '                    global_initializer(child)\n'
    '                return\n'
    '            if value.kind == "literal":\n'
)

_NEEDLE_2 = (
    '        reject_type(declaration.type, declaration)\n'
    '        if declaration.type.kind == "matrix":\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
    '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
)
_REPLACEMENT_2 = (
    '        reject_type(declaration.type, declaration)\n'
    '        if declaration.type.kind == "matrix" and declaration.symbol.storage != "const":\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
    '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
)

assert _ORIGINAL_VALIDATE_SRC.count(_NEEDLE_1) == 1, "needle 1 not uniquely found"
assert _ORIGINAL_VALIDATE_SRC.count(_NEEDLE_2) == 1, "needle 2 not uniquely found"

_PATCHED_VALIDATE_SRC = (
    _ORIGINAL_VALIDATE_SRC
    .replace(_NEEDLE_1, _REPLACEMENT_1, 1)
    .replace(_NEEDLE_2, _REPLACEMENT_2, 1)
)


def _compile_patched_validate():
    namespace = dict(gen.__dict__)
    exec(compile(_PATCHED_VALIDATE_SRC, "<patched validate_capabilities>", "exec"), namespace)
    return namespace["validate_capabilities"]


# --- Build the patched _Emitter._validate_source_globals (emit_typed_cpp.py)

_ORIGINAL_EMIT_SRC = inspect.getsource(emit._Emitter._validate_source_globals)

_ENEEDLE_1 = (
    '            if (declaration.symbol.storage != "const" or declaration.type.display() != "float"\n'
    '                    or declaration.initializer is None):\n'
    '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
    '            dependencies: list[int] = []\n'
    '\n'
    '            def initializer(value: TypedExpression) -> None:\n'
    '                if value.type.display() != "float":\n'
    '                    raise _error(self.program, value, "unsupported source const global initializer type")\n'
    '                if value.kind == "literal":\n'
)
_EREPLACEMENT_1 = (
    '            if (declaration.symbol.storage != "const"\n'
    '                    or declaration.initializer is None):\n'
    '                raise _error(self.program, declaration, "unsupported source global declaration")\n'
    '            dependencies: list[int] = []\n'
    '\n'
    '            def initializer(value: TypedExpression) -> None:\n'
    '                if value.kind == "construct":\n'
    '                    for child in value.children:\n'
    '                        initializer(child)\n'
    '                    return\n'
    '                if value.kind == "literal":\n'
)

assert _ORIGINAL_EMIT_SRC.count(_ENEEDLE_1) == 1, "emitter needle 1 not uniquely found"

_PATCHED_EMIT_SRC = _ORIGINAL_EMIT_SRC.replace(_ENEEDLE_1, _EREPLACEMENT_1, 1)
# dedent the method source (it's indented 4 spaces as a class body member)
_PATCHED_EMIT_SRC_DEDENT = "\n".join(
    line[4:] if line.startswith("    ") else line
    for line in _PATCHED_EMIT_SRC.splitlines()
) + "\n"


def _compile_patched_emit_method():
    namespace = dict(emit.__dict__)
    exec(compile(_PATCHED_EMIT_SRC_DEDENT, "<patched _validate_source_globals>", "exec"), namespace)
    return namespace["_validate_source_globals"]


def probe(key: str) -> dict:
    entry, typed = load(key)
    patched_validate = _compile_patched_validate()
    patched_emit_method = _compile_patched_emit_method()

    old_gen_validate = gen.validate_capabilities
    old_emit_method = emit._Emitter._validate_source_globals
    try:
        gen.validate_capabilities = patched_validate
        emit._Emitter._validate_source_globals = patched_emit_method
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                       source_hash=entry["raw_sha256"])
            validator = "pass"
            validator_exc_type = None
        except Exception as error:  # noqa: BLE001
            validator = first(error)
            validator_exc_type = type(error).__name__
        try:
            emit.render_typed_cpp(typed, key, entry["raw_sha256"],
                                   "second_order_probe", "bind_second_order_probe")
            emitter = "pass"
            emitter_exc_type = None
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
            emitter_exc_type = type(error).__name__
    finally:
        gen.validate_capabilities = old_gen_validate
        emit._Emitter._validate_source_globals = old_emit_method

    return {
        "key": key,
        "validator_with_generalized_const_globals": validator,
        "validator_exc_type": validator_exc_type,
        "emitter_with_generalized_const_globals": emitter,
        "emitter_exc_type": emitter_exc_type,
    }


def main() -> int:
    rows = [probe(key) for key in PURE_CONST_TYPE_KEYS]

    # Confirm the patch is a real relaxation and not a no-op: original
    # (unpatched) validator must fail with the family's own message for every
    # key, else the classification/keys list is wrong.
    sanity = []
    for key in PURE_CONST_TYPE_KEYS:
        entry, typed = load(key)
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                       source_hash=entry["raw_sha256"])
            sanity.append((key, "UNEXPECTED PASS -- key should not be in this family"))
        except Exception as error:  # noqa: BLE001
            sanity.append((key, first(error)))

    tag_counts: dict[str, int] = {}
    for row in rows:
        bucket = row["emitter_with_generalized_const_globals"]
        tag_counts[bucket] = tag_counts.get(bucket, 0) + 1

    out = {
        "family": "unsupported global declaration (const-typed subfamily, 27/30)",
        "note": "non_const_global 3 keys (cellRefract, kaleido, synth/shape) intentionally excluded -- separate capability",
        "sanity_original_validator_still_fails_every_key": sanity,
        "rows": rows,
        "emitter_outcome_distribution_after_hypothetical_admission": tag_counts,
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
