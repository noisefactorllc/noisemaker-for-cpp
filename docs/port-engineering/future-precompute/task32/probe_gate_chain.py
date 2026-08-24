"""Task 32, task 1: walk the COMPLETE gate chain for the four round-family
candidates (filter/fxaa:fxaa, filter/grain:grain, filter/normalMap:normalMap,
filter/snow:snow), starting unpatched, then applying successive narrow
monkeypatches (restored in `finally`) to test whether "generalized const-global
admission + round" is sufficient to clear each program through both the
validator (generate_typed_slice.validate_capabilities) and the emitter
(emit_typed_cpp.render_typed_cpp).

Stage 0: unpatched (baseline first blocker).
Stage 1: Patch A only -- generalized const-global admission. Reuses the exact
    text substitutions from docs/port-engineering/roadmap/
    probe_globals_second_order.py (drop the float-only restriction in
    validate_capabilities and _Emitter._validate_source_globals; teach the
    initializer walker to recurse into `construct` expressions).
Stage 2: Patch A + Patch B -- Patch B additionally bypasses the per-node
    identity gate that currently restricts `round` to the single
    GATHER_SORTED_KEY-authenticated call site (see
    generate_typed_slice.py:2057-2059,2107-2108 and
    emit_typed_cpp.py:1387-1389), and admits "round" into
    gen.APPROVED_CAPABILITIES / gen._BUILTINS / emit._BUILTIN_NAMES the same
    way future-precompute/analyze_candidates.py admits any other builtin by
    name. This is a probe of "what's next if round is generalized", not a
    real capability implementation -- the real fix would still need its own
    authenticated profile per the codebase's demonstrated pattern (every
    existing builtin exception -- tanh, floatBitsToUint, all/lessThanEqual --
    is a single-identity-node profile, not a name-based allowlist entry).

Every monkeypatch is restored in `finally`. Function-identity and dict/tuple
snapshots are hashed before and after each stage to prove restoration.
No file under noisemaker-for-cpp is written (see restoration_proof section).
"""
from __future__ import annotations

import hashlib
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

KEYS = (
    "filter/fxaa:fxaa",
    "filter/grain:grain",
    "filter/normalMap:normalMap",
    "filter/snow:snow",
)


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, typed


def first(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else f"{type(error).__name__}"


# --------------------------------------------------------------------------
# Patch A: generalized const-global admission (identical text to
# roadmap/probe_globals_second_order.py, reproduced here for a
# self-contained probe script).
# --------------------------------------------------------------------------

_ORIGINAL_VALIDATE_SRC = inspect.getsource(gen.validate_capabilities)

_A_NEEDLE_1 = (
    '        if storage != "const" or declaration.type != FLOAT or declaration.initializer is None:\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global declaration")\n'
    '\n'
    '        def global_initializer(value) -> None:\n'
    '            if value.type != FLOAT:\n'
    '                raise GeneratorError(f"{location(value)}: unsupported global initializer type {value.type.display()}")\n'
    '            if value.kind == "literal":\n'
)
_A_REPLACEMENT_1 = (
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

_A_NEEDLE_2 = (
    '        reject_type(declaration.type, declaration)\n'
    '        if declaration.type.kind == "matrix":\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
    '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
)
_A_REPLACEMENT_2 = (
    '        reject_type(declaration.type, declaration)\n'
    '        if declaration.type.kind == "matrix" and declaration.symbol.storage != "const":\n'
    '            raise GeneratorError(f"{location(declaration)}: unsupported global matrix declaration")\n'
    '        if declaration.symbol.storage not in {"uniform", "output", "const"}:\n'
)

assert _ORIGINAL_VALIDATE_SRC.count(_A_NEEDLE_1) == 1, "A needle 1 not uniquely found"
assert _ORIGINAL_VALIDATE_SRC.count(_A_NEEDLE_2) == 1, "A needle 2 not uniquely found"

# --------------------------------------------------------------------------
# Patch B: generalize `round` -- delete the single-identity gate so it falls
# through to the ordinary `elif value.callee not in _BUILTINS: raise` check,
# and stop excluding it from `used` (capability-usage bookkeeping).
# --------------------------------------------------------------------------

_B_NEEDLE_1 = (
    '            if value.callee == "round":\n'
    '                if value is not authorized_round:\n'
    '                    raise GeneratorError(f"{location(value)}: unsupported builtin round")\n'
    '            elif value.callee == "tanh":\n'
)
_B_REPLACEMENT_1 = (
    '            if value.callee == "tanh":\n'
)

_B_NEEDLE_2 = (
    '            if value.callee not in {"round", "all", "lessThanEqual",\n'
    '                                    "floatBitsToUint", "tanh"}:\n'
    '                used.add(value.callee)\n'
)
_B_REPLACEMENT_2 = (
    '            if value.callee not in {"all", "lessThanEqual",\n'
    '                                    "floatBitsToUint", "tanh"}:\n'
    '                used.add(value.callee)\n'
)

assert _ORIGINAL_VALIDATE_SRC.count(_B_NEEDLE_1) == 1, "B needle 1 not uniquely found"
assert _ORIGINAL_VALIDATE_SRC.count(_B_NEEDLE_2) == 1, "B needle 2 not uniquely found"

_PATCHED_VALIDATE_SRC_A = (
    _ORIGINAL_VALIDATE_SRC
    .replace(_A_NEEDLE_1, _A_REPLACEMENT_1, 1)
    .replace(_A_NEEDLE_2, _A_REPLACEMENT_2, 1)
)
_PATCHED_VALIDATE_SRC_AB = (
    _PATCHED_VALIDATE_SRC_A
    .replace(_B_NEEDLE_1, _B_REPLACEMENT_1, 1)
    .replace(_B_NEEDLE_2, _B_REPLACEMENT_2, 1)
)

assert _PATCHED_VALIDATE_SRC_A != _ORIGINAL_VALIDATE_SRC
assert _PATCHED_VALIDATE_SRC_AB != _PATCHED_VALIDATE_SRC_A


def _compile_validate(src: str):
    namespace = dict(gen.__dict__)
    exec(compile(src, "<patched validate_capabilities>", "exec"), namespace)
    return namespace["validate_capabilities"]


# --------------------------------------------------------------------------
# Emitter side: _Emitter._validate_source_globals (Patch A) and
# _Emitter.expression (Patch B).
# --------------------------------------------------------------------------

_ORIGINAL_EMIT_GLOBALS_SRC = inspect.getsource(emit._Emitter._validate_source_globals)

_EA_NEEDLE_1 = (
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
_EA_REPLACEMENT_1 = (
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

assert _ORIGINAL_EMIT_GLOBALS_SRC.count(_EA_NEEDLE_1) == 1, "EA needle 1 not uniquely found"

_PATCHED_EMIT_GLOBALS_SRC = _ORIGINAL_EMIT_GLOBALS_SRC.replace(_EA_NEEDLE_1, _EA_REPLACEMENT_1, 1)
_PATCHED_EMIT_GLOBALS_SRC_DEDENT = "\n".join(
    line[4:] if line.startswith("    ") else line
    for line in _PATCHED_EMIT_GLOBALS_SRC.splitlines()
) + "\n"


def _compile_emit_globals_method():
    namespace = dict(emit.__dict__)
    exec(compile(_PATCHED_EMIT_GLOBALS_SRC_DEDENT, "<patched _validate_source_globals>", "exec"), namespace)
    return namespace["_validate_source_globals"]


_ORIGINAL_EMIT_EXPRESSION_SRC = inspect.getsource(emit._Emitter.expression)

_EB_NEEDLE_1 = (
    '                if value.callee == "round":\n'
    '                    raise _error(self.program, value, "unsupported builtin round")\n'
    '                if value.callee == "tanh":\n'
)
_EB_REPLACEMENT_1 = (
    '                if value.callee == "tanh":\n'
)

assert _ORIGINAL_EMIT_EXPRESSION_SRC.count(_EB_NEEDLE_1) == 1, "EB needle 1 not uniquely found"

_PATCHED_EMIT_EXPRESSION_SRC = _ORIGINAL_EMIT_EXPRESSION_SRC.replace(_EB_NEEDLE_1, _EB_REPLACEMENT_1, 1)
_PATCHED_EMIT_EXPRESSION_SRC_DEDENT = "\n".join(
    line[4:] if line.startswith("    ") else line
    for line in _PATCHED_EMIT_EXPRESSION_SRC.splitlines()
) + "\n"


def _compile_emit_expression_method():
    namespace = dict(emit.__dict__)
    exec(compile(_PATCHED_EMIT_EXPRESSION_SRC_DEDENT, "<patched expression>", "exec"), namespace)
    return namespace["expression"]


assert _PATCHED_EMIT_EXPRESSION_SRC != _ORIGINAL_EMIT_EXPRESSION_SRC


def snapshot_state():
    return {
        "validate_capabilities_id": id(gen.validate_capabilities),
        "validate_capabilities_src_sha256": hashlib.sha256(
            inspect.getsource(gen.validate_capabilities).encode()).hexdigest(),
        "emit_validate_source_globals_id": id(emit._Emitter._validate_source_globals),
        "emit_validate_source_globals_src_sha256": hashlib.sha256(
            inspect.getsource(emit._Emitter._validate_source_globals).encode()).hexdigest(),
        "emit_expression_id": id(emit._Emitter.expression),
        "emit_expression_src_sha256": hashlib.sha256(
            inspect.getsource(emit._Emitter.expression).encode()).hexdigest(),
        "APPROVED_CAPABILITIES": gen.APPROVED_CAPABILITIES,
        "_BUILTINS": sorted(gen._BUILTINS),
        "_BUILTIN_NAMES": dict(emit._BUILTIN_NAMES),
    }


def run_stage(typed, entry, *, patch_a: bool, patch_b: bool):
    """Run validator+emitter at a given patch stage; restore everything in
    finally; return (result_dict, pre_snapshot, post_snapshot)."""
    pre = snapshot_state()

    old_gen_validate = gen.validate_capabilities
    old_emit_globals = emit._Emitter._validate_source_globals
    old_emit_expression = emit._Emitter.expression
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)

    try:
        if patch_a and patch_b:
            # Mutate the admission tables FIRST: _compile_validate /
            # _compile_emit_expression_method snapshot gen.__dict__ /
            # emit.__dict__ at compile time (exec'd function's __globals__ is
            # that frozen snapshot dict, not a live reference to the module),
            # so "round" must already be present before compiling or the
            # patched function will still see the old tables.
            gen.APPROVED_CAPABILITIES = (*old_caps, "round")
            gen._BUILTINS = frozenset((*old_builtins, "round"))
            emit._BUILTIN_NAMES["round"] = "round"
            gen.validate_capabilities = _compile_validate(_PATCHED_VALIDATE_SRC_AB)
            emit._Emitter._validate_source_globals = _compile_emit_globals_method()
            emit._Emitter.expression = _compile_emit_expression_method()
        elif patch_a:
            gen.validate_capabilities = _compile_validate(_PATCHED_VALIDATE_SRC_A)
            emit._Emitter._validate_source_globals = _compile_emit_globals_method()

        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                      source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)

        try:
            cpp = emit.render_typed_cpp(typed, typed.key, entry["raw_sha256"],
                                        "task32_gate_chain", "bind_task32_gate_chain")
            emitter = "pass"
            cpp_sha256 = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_bytes = len(cpp.encode())
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
            cpp_sha256 = None
            cpp_bytes = None
    finally:
        gen.validate_capabilities = old_gen_validate
        emit._Emitter._validate_source_globals = old_emit_globals
        emit._Emitter.expression = old_emit_expression
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)

    post = snapshot_state()
    return ({"validator": validator, "emitter": emitter,
             "cpp_sha256": cpp_sha256, "cpp_bytes": cpp_bytes},
            pre, post)


def restored(pre, post) -> bool:
    return (pre["validate_capabilities_id"] == post["validate_capabilities_id"]
            and pre["validate_capabilities_src_sha256"] == post["validate_capabilities_src_sha256"]
            and pre["emit_validate_source_globals_id"] == post["emit_validate_source_globals_id"]
            and pre["emit_validate_source_globals_src_sha256"] == post["emit_validate_source_globals_src_sha256"]
            and pre["emit_expression_id"] == post["emit_expression_id"]
            and pre["emit_expression_src_sha256"] == post["emit_expression_src_sha256"]
            and pre["APPROVED_CAPABILITIES"] == post["APPROVED_CAPABILITIES"]
            and pre["_BUILTINS"] == post["_BUILTINS"]
            and pre["_BUILTIN_NAMES"] == post["_BUILTIN_NAMES"])


def main() -> int:
    rows = []
    for key in KEYS:
        entry, raw, defines, typed = load(key)

        stage0, pre0, post0 = run_stage(typed, entry, patch_a=False, patch_b=False)
        stage1, pre1, post1 = run_stage(typed, entry, patch_a=True, patch_b=False)
        stage2, pre2, post2 = run_stage(typed, entry, patch_a=True, patch_b=True)

        rows.append({
            "key": key,
            "defines": defines,
            "raw_sha256": entry["raw_sha256"],
            "stage_0_unpatched": stage0,
            "stage_0_restored": restored(pre0, post0),
            "stage_1_const_global_admission_only": stage1,
            "stage_1_restored": restored(pre1, post1),
            "stage_2_const_global_plus_round": stage2,
            "stage_2_restored": restored(pre2, post2),
            "const_global_plus_round_sufficient":
                stage2["validator"] == "pass" and stage2["emitter"] == "pass",
        })

    # Sanity: unpatched validator for all 4 must fail with the family's own
    # first-blocker message, proving the baseline wasn't already passing.
    sanity = []
    for key in KEYS:
        entry, raw, defines, typed = load(key)
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES,
                                      source_hash=entry["raw_sha256"])
            sanity.append((key, "UNEXPECTED PASS"))
        except Exception as error:  # noqa: BLE001
            sanity.append((key, first(error)))

    payload = {
        "schema": "noisemaker-for-cpp.task32.gate-chain.v1",
        "corpus_revision": REVISION,
        "keys": list(KEYS),
        "patch_a_description": "generalized const-global admission (validate_capabilities + _Emitter._validate_source_globals): drop float-only restriction, recurse construct-expr initializers",
        "patch_b_description": "generalized round admission: delete the GATHER_SORTED_KEY-only identity gate in validate_capabilities and _Emitter.expression, add round to APPROVED_CAPABILITIES/_BUILTINS/_BUILTIN_NAMES by name (probe only -- not a real authenticated profile)",
        "sanity_unpatched_baseline": sanity,
        "rows": rows,
    }
    out = Path(__file__).with_name("gate-chain-output.json")
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
