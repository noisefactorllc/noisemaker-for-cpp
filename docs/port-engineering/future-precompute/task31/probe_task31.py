"""Task 31 next-slice precompute probe: curl, caustic, lighting.

READ-ONLY. Never writes into ..
Everything monkeypatched here is restored in `finally`. This reuses the
exact technique already established in
docs/port-engineering/roadmap/probe_globals_second_order.py (source-text
patch + exec + function/method-object monkeypatch, restored) and the
_whole/_interface identity helpers copied verbatim from
tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py so hashes
are directly comparable to that profile and to task30's report.
"""
from __future__ import annotations

import dataclasses
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

KEYS = {
    "curl": "synth/curl:curl",
    "caustic": "classicNoisedeck/caustic:caustic",
    "lighting": "filter/lighting:lighting",
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _whole(program) -> str:
    # Copied verbatim (field order) from extrude_bvec2_relational_reduction_profile._whole
    return _sha((program.key, program.source, program.raw_source, program.declarations,
                 program.functions, program.resources, program.body_status,
                 program.local_type_names, program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.counted_loop_proof, program.preprocessor_defines))


def _interface(program) -> str:
    # Copied verbatim from extrude_bvec2_relational_reduction_profile._interface
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def first(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, typed


def expression_nodes(value, path=()):
    yield path, value
    for index, child in enumerate(value.children):
        yield from expression_nodes(child, (*path, index))


def statement_nodes(value, path):
    for index, expression in enumerate(value.expressions):
        yield from expression_nodes(expression, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from statement_nodes(child, (*path, f"s{index}"))


def function_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))


def identity_row(key: str) -> dict:
    entry, raw, defines, program = load(key)
    typed_keys = sorted(row["program_key"] for row in json.loads(
        (ROOT / "tools/glslcpp/typed_slice.json").read_text())["programs"])
    functions = [{
        "id": f.signature.id, "name": f.name, "return": f.return_type.display(),
        "span": _span(f), "body_statement_count": len(f.body),
        "parameters": [{"name": p.name, "type": p.type.display(),
                         "direction": p.direction} for p in f.parameters],
    } for f in program.functions]
    return {
        "key": key,
        "source": entry["source"],
        "raw_bytes": len(raw.encode()),
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "raw_sha256_matches_manifest": hashlib.sha256(raw.encode()).hexdigest() == entry["raw_sha256"],
        "normalized_bytes": len(program.source.encode()),
        "normalized_sha256": hashlib.sha256(program.source.encode()).hexdigest(),
        "defines": defines,
        "function_count": len(program.functions),
        "functions": functions,
        "whole_program_sha256": _whole(program),
        "interface_sha256": _interface(program),
        "loop_proof": dataclasses.asdict(program.counted_loop_proof) if program.counted_loop_proof else None,
        "loop_proof_tuple": (
            (program.counted_loop_proof.loop_count,
             program.counted_loop_proof.unproved_loop_count,
             program.counted_loop_proof.max_effective_depth,
             program.counted_loop_proof.max_lexical_product,
             program.counted_loop_proof.entrypoint_charge,
             program.counted_loop_proof.call_graph_acyclic)
            if program.counted_loop_proof else None),
        "resources": dataclasses.asdict(program.resources),
        "resources_tuple": (
            program.resources.uniforms, program.resources.samplers,
            program.resources.outputs, program.resources.uses_texture,
            program.resources.uses_derivatives),
        "typed_count_at_probe_time": len(typed_keys),
        "typed_sorted_sha256_at_probe_time": hashlib.sha256(
            ("\n".join(typed_keys) + "\n").encode()).hexdigest(),
    }


def first_gate_row(key: str) -> dict:
    entry, raw, defines, program = load(key)
    try:
        gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
        validator = "pass"
    except Exception as error:  # noqa: BLE001
        validator = first(error)
    try:
        emit.render_typed_cpp(program, program.key, entry["raw_sha256"], "task31_probe", "bind_task31_probe")
        emitter = "pass"
    except Exception as error:  # noqa: BLE001
        emitter = first(error)
    return {"key": key, "validator_unmodified": validator, "emitter_unmodified": emitter}


# --------------------------------------------------------------------------
# Step: admit one builtin name outright (the technique already proven safe by
# future-precompute/analyze_candidates.py -- toggling gen.APPROVED_CAPABILITIES
# / gen._BUILTINS / emit._BUILTIN_NAMES, restored in finally).
# --------------------------------------------------------------------------

def probe_with_builtin_admitted(key: str, builtin_names: tuple[str, ...]) -> dict:
    entry, raw, defines, program = load(key)
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, *builtin_names)
        gen._BUILTINS = frozenset((*old_builtins, *builtin_names))
        emit._BUILTIN_NAMES.update({name: name for name in builtin_names})
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)
        try:
            emit.render_typed_cpp(program, program.key, entry["raw_sha256"], "task31_probe", "bind_task31_probe")
            emitter = "pass"
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
        return {"admitted": list(builtin_names), "validator": validator, "emitter": emitter}
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)


# --------------------------------------------------------------------------
# Step: source-patch validate_capabilities + _Emitter.expression to relax the
# `mod` overload allowlist (curl needs vec3,float and vec4,float in addition
# to the already-approved float,float / vec2,float / vec2,vec2).
# --------------------------------------------------------------------------

_VALIDATE_SRC = inspect.getsource(gen.validate_capabilities)
_MOD_NEEDLE_GEN = (
    '            if value.callee == "mod":\n'
    '                argument_types = tuple(child.type.display() for child in value.children)\n'
    '                if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:\n'
    '                    raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")\n'
)
_MOD_REPLACEMENT_GEN = (
    '            if value.callee == "mod":\n'
    '                argument_types = tuple(child.type.display() for child in value.children)\n'
    '                if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2"),\n'
    '                                          ("vec3", "float"), ("vec4", "float")}:\n'
    '                    raise GeneratorError(f"{location(value)}: unsupported builtin mod overload")\n'
)
assert _VALIDATE_SRC.count(_MOD_NEEDLE_GEN) == 1, "mod needle (gen) not uniquely found"
_PATCHED_VALIDATE_MOD_SRC = _VALIDATE_SRC.replace(_MOD_NEEDLE_GEN, _MOD_REPLACEMENT_GEN, 1)


def _compile_patched_validate_mod():
    namespace = dict(gen.__dict__)
    exec(compile(_PATCHED_VALIDATE_MOD_SRC, "<patched validate_capabilities mod>", "exec"), namespace)
    return namespace["validate_capabilities"]


_EXPRESSION_SRC = inspect.getsource(emit._Emitter.expression)
_MOD_NEEDLE_EMIT = (
    '                if value.callee == "mod":\n'
    '                    argument_types = tuple(child.type.display() for child in value.children)\n'
    '                    if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2")}:\n'
    '                        raise _error(self.program, value, "unsupported builtin mod overload")\n'
)
_MOD_REPLACEMENT_EMIT = (
    '                if value.callee == "mod":\n'
    '                    argument_types = tuple(child.type.display() for child in value.children)\n'
    '                    if argument_types not in {("float", "float"), ("vec2", "float"), ("vec2", "vec2"),\n'
    '                                              ("vec3", "float"), ("vec4", "float")}:\n'
    '                        raise _error(self.program, value, "unsupported builtin mod overload")\n'
)
assert _EXPRESSION_SRC.count(_MOD_NEEDLE_EMIT) == 1, "mod needle (emit) not uniquely found"
_PATCHED_EXPRESSION_MOD_SRC = _EXPRESSION_SRC.replace(_MOD_NEEDLE_EMIT, _MOD_REPLACEMENT_EMIT, 1)
_PATCHED_EXPRESSION_MOD_DEDENT = "\n".join(
    line[4:] if line.startswith("    ") else line
    for line in _PATCHED_EXPRESSION_MOD_SRC.splitlines()) + "\n"


def _compile_patched_expression_mod():
    namespace = dict(emit.__dict__)
    exec(compile(_PATCHED_EXPRESSION_MOD_DEDENT, "<patched expression mod>", "exec"), namespace)
    return namespace["expression"]


def probe_curl_chain() -> dict:
    key = KEYS["curl"]
    entry, raw, defines, program = load(key)
    chain = []
    chain.append({"step": 0, "description": "unmodified",
                   **{k: v for k, v in first_gate_row(key).items() if k != "key"}})

    # step 1: admit tanh
    step1 = probe_with_builtin_admitted(key, ("tanh",))
    chain.append({"step": 1, "description": "admit builtin tanh (capability+builtin sets)", **step1})

    # step 2: admit tanh AND relax mod overload set (vec3,float / vec4,float)
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)
    old_gen_validate = gen.validate_capabilities
    old_emit_expression = emit._Emitter.expression
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, "tanh")
        gen._BUILTINS = frozenset((*old_builtins, "tanh"))
        emit._BUILTIN_NAMES.update({"tanh": "tanh"})
        gen.validate_capabilities = _compile_patched_validate_mod()
        emit._Emitter.expression = _compile_patched_expression_mod()
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)
        try:
            cpp = emit.render_typed_cpp(program, program.key, entry["raw_sha256"], "task31_probe", "bind_task31_probe")
            emitter = "pass"
            cpp_sha = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_bytes = len(cpp.encode())
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
            cpp_sha = None
            cpp_bytes = None
        chain.append({"step": 2, "description": "admit tanh + relax mod overload set to include (vec3,float),(vec4,float)",
                      "validator": validator, "emitter": emitter, "cpp_sha256": cpp_sha, "cpp_bytes": cpp_bytes})
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)
        gen.validate_capabilities = old_gen_validate
        emit._Emitter.expression = old_emit_expression

    return {"key": key, "chain": chain}


# --------------------------------------------------------------------------
# Caustic: floatBitsToUint, then scalar uint ^ uint (as opposed to the
# already-admitted uvec2/3/4 ^ uvec2/3/4 vector case).
# --------------------------------------------------------------------------

_XOR_NEEDLE_GEN = (
    '            elif value.operator == "^":\n'
    '                if any(value is item for item in authorized_perlin_scalar_uint_xors):\n'
    '                    if (left_type, right_type, value.type.display()) != (\n'
    '                            "uint", "uint", "uint"):\n'
    '                        raise GeneratorError(\n'
    '                            f"{location(value)}: malformed authenticated scalar uint XOR")\n'
    '                    visited_perlin_scalar_uint_xors.append(value)\n'
    '                else:\n'
    '                    if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
    '                            or right_type != left_type):\n'
    '                        raise GeneratorError(\n'
    '                            f"{location(value)}: unsupported binary operator ^")\n'
    '                    used.add("uint-vector-bitwise")\n'
)
_XOR_REPLACEMENT_GEN = (
    '            elif value.operator == "^":\n'
    '                if any(value is item for item in authorized_perlin_scalar_uint_xors):\n'
    '                    if (left_type, right_type, value.type.display()) != (\n'
    '                            "uint", "uint", "uint"):\n'
    '                        raise GeneratorError(\n'
    '                            f"{location(value)}: malformed authenticated scalar uint XOR")\n'
    '                    visited_perlin_scalar_uint_xors.append(value)\n'
    '                elif left_type == "uint" and right_type == "uint":\n'
    '                    pass\n'
    '                else:\n'
    '                    if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
    '                            or right_type != left_type):\n'
    '                        raise GeneratorError(\n'
    '                            f"{location(value)}: unsupported binary operator ^")\n'
    '                    used.add("uint-vector-bitwise")\n'
)
assert _VALIDATE_SRC.count(_XOR_NEEDLE_GEN) == 1, "xor needle (gen) not uniquely found"
_PATCHED_VALIDATE_XOR_SRC = _VALIDATE_SRC.replace(_XOR_NEEDLE_GEN, _XOR_REPLACEMENT_GEN, 1)


def _compile_patched_validate_xor():
    namespace = dict(gen.__dict__)
    exec(compile(_PATCHED_VALIDATE_XOR_SRC, "<patched validate_capabilities xor>", "exec"), namespace)
    return namespace["validate_capabilities"]


_XOR_NEEDLE_EMIT = (
    '            if value.operator == "^":\n'
    '                if any(value is item for item in self.authorized_perlin_scalar_uint_xors):\n'
    '                    if (left_type, right_type, value.type.display()) != (\n'
    '                            "uint", "uint", "uint"):\n'
    '                        raise _error(\n'
    '                            self.program, value,\n'
    '                            "malformed authenticated scalar uint XOR")\n'
    '                    self.emitted_perlin_scalar_uint_xors.append(value)\n'
    '                    return (f"({self.expression(value.children[0])} ^ "\n'
    '                            f"{self.expression(value.children[1])})")\n'
    '                if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
    '                        or right_type != left_type):\n'
    '                    raise _error(self.program, value, "unsupported binary operator ^")\n'
)
_XOR_REPLACEMENT_EMIT = (
    '            if value.operator == "^":\n'
    '                if any(value is item for item in self.authorized_perlin_scalar_uint_xors):\n'
    '                    if (left_type, right_type, value.type.display()) != (\n'
    '                            "uint", "uint", "uint"):\n'
    '                        raise _error(\n'
    '                            self.program, value,\n'
    '                            "malformed authenticated scalar uint XOR")\n'
    '                    self.emitted_perlin_scalar_uint_xors.append(value)\n'
    '                    return (f"({self.expression(value.children[0])} ^ "\n'
    '                            f"{self.expression(value.children[1])})")\n'
    '                if left_type == "uint" and right_type == "uint":\n'
    '                    return (f"({self.expression(value.children[0])} ^ "\n'
    '                            f"{self.expression(value.children[1])})")\n'
    '                if (left_type not in {"uvec2", "uvec3", "uvec4"}\n'
    '                        or right_type != left_type):\n'
    '                    raise _error(self.program, value, "unsupported binary operator ^")\n'
)
assert _EXPRESSION_SRC.count(_XOR_NEEDLE_EMIT) == 1, "xor needle (emit) not uniquely found"
_PATCHED_EXPRESSION_XOR_SRC = _EXPRESSION_SRC.replace(_XOR_NEEDLE_EMIT, _XOR_REPLACEMENT_EMIT, 1)
_PATCHED_EXPRESSION_XOR_DEDENT = "\n".join(
    line[4:] if line.startswith("    ") else line
    for line in _PATCHED_EXPRESSION_XOR_SRC.splitlines()) + "\n"


def _compile_patched_expression_xor():
    namespace = dict(emit.__dict__)
    exec(compile(_PATCHED_EXPRESSION_XOR_DEDENT, "<patched expression xor>", "exec"), namespace)
    return namespace["expression"]


def probe_caustic_chain() -> dict:
    key = KEYS["caustic"]
    entry, raw, defines, program = load(key)
    chain = []
    chain.append({"step": 0, "description": "unmodified",
                   **{k: v for k, v in first_gate_row(key).items() if k != "key"}})

    step1 = probe_with_builtin_admitted(key, ("floatBitsToUint",))
    chain.append({"step": 1, "description": "admit builtin floatBitsToUint (capability+builtin sets)", **step1})

    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)
    old_gen_validate = gen.validate_capabilities
    old_emit_expression = emit._Emitter.expression
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, "floatBitsToUint")
        gen._BUILTINS = frozenset((*old_builtins, "floatBitsToUint"))
        emit._BUILTIN_NAMES.update({"floatBitsToUint": "floatBitsToUint"})
        gen.validate_capabilities = _compile_patched_validate_xor()
        emit._Emitter.expression = _compile_patched_expression_xor()
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)
        try:
            cpp = emit.render_typed_cpp(program, program.key, entry["raw_sha256"], "task31_probe", "bind_task31_probe")
            emitter = "pass"
            cpp_sha = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_bytes = len(cpp.encode())
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
            cpp_sha = None
            cpp_bytes = None
        chain.append({"step": 2, "description": "admit floatBitsToUint + admit scalar uint^uint diagnostically",
                      "validator": validator, "emitter": emitter, "cpp_sha256": cpp_sha, "cpp_bytes": cpp_bytes})
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)
        gen.validate_capabilities = old_gen_validate
        emit._Emitter.expression = old_emit_expression

    return {"key": key, "chain": chain}


# --------------------------------------------------------------------------
# Lighting: reflect, then local float[9]/vec2[9] declarations (diagnostic
# only -- the real mechanism is the whole-program fixed_nine_table_proof
# structural proof, not a type-admission toggle).
# --------------------------------------------------------------------------

_REJECT_TYPE_SRC = None  # reject_type is a nested closure inside validate_capabilities; patch whole function.

_ARRAY_NEEDLE_GEN = (
    '    def reject_type(typ, value) -> None:\n'
    '        if typ.kind == "array":\n'
)
_ARRAY_REPLACEMENT_GEN = (
    '    def reject_type(typ, value) -> None:\n'
    '        if typ.kind == "array" and typ.display() in {"float[9]", "vec2[9]"}:\n'
    '            return\n'
    '        if typ.kind == "array":\n'
)
assert _VALIDATE_SRC.count(_ARRAY_NEEDLE_GEN) == 1, "array needle (gen) not uniquely found"
_PATCHED_VALIDATE_ARRAY_SRC = _VALIDATE_SRC.replace(_ARRAY_NEEDLE_GEN, _ARRAY_REPLACEMENT_GEN, 1)


def _compile_patched_validate_array():
    namespace = dict(gen.__dict__)
    exec(compile(_PATCHED_VALIDATE_ARRAY_SRC, "<patched validate_capabilities array>", "exec"), namespace)
    return namespace["validate_capabilities"]


def probe_lighting_chain() -> dict:
    key = KEYS["lighting"]
    entry, raw, defines, program = load(key)
    chain = []
    chain.append({"step": 0, "description": "unmodified",
                   **{k: v for k, v in first_gate_row(key).items() if k != "key"}})

    step1 = probe_with_builtin_admitted(key, ("reflect",))
    chain.append({"step": 1, "description": "admit builtin reflect (capability+builtin sets)", **step1})

    # step2: admit reflect + diagnostically bypass reject_type()'s array check
    # ONLY for validator (the emitter's "unsupported fixed-nine array
    # declaration" gate is not a builtin/type toggle -- it demands an actual
    # fixed_nine_table_proof; there is no equivalently narrow emitter-side
    # toggle without reimplementing that whole proof, so this step reports the
    # validator-only diagnostic and separately re-confirms the emitter's real
    # gate is unchanged and requires the structural proof.)
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names = dict(emit._BUILTIN_NAMES)
    old_gen_validate = gen.validate_capabilities
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, "reflect")
        gen._BUILTINS = frozenset((*old_builtins, "reflect"))
        emit._BUILTIN_NAMES.update({"reflect": "reflect"})
        gen.validate_capabilities = _compile_patched_validate_array()
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            validator = "pass"
        except Exception as error:  # noqa: BLE001
            validator = first(error)
        try:
            emit.render_typed_cpp(program, program.key, entry["raw_sha256"], "task31_probe", "bind_task31_probe")
            emitter = "pass"
        except Exception as error:  # noqa: BLE001
            emitter = first(error)
        chain.append({
            "step": 2,
            "description": ("DIAGNOSTIC ONLY: admit reflect + bypass reject_type's array-kind "
                             "rejection for exactly float[9]/vec2[9] in the VALIDATOR. The emitter "
                             "has no equivalent narrow toggle -- fixed-nine array codegen is gated by "
                             "prove_fixed_nine_local_tables()/SOURCE_LOCKS, a whole-program structural "
                             "proof keyed to filter/sharpen:sharpen and filter/sobel:sobel only, not a "
                             "type-admission flag. This step shows what the validator alone would say "
                             "next; it is not evidence that float[9] could ever be admitted this way "
                             "for real."),
            "validator": validator, "emitter": emitter})
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear()
        emit._BUILTIN_NAMES.update(old_names)
        gen.validate_capabilities = old_gen_validate

    return {"key": key, "chain": chain}


def closure_nodes_for(key: str, filter_fn) -> list[dict]:
    entry, raw, defines, program = load(key)
    nodes = []
    for function in program.functions:
        for path, value in function_nodes(function):
            if filter_fn(value):
                nodes.append({
                    "owner": function.name, "owner_id": function.signature.id,
                    "path": list(path), "span": _span(value), "kind": value.kind,
                    "callee": getattr(value, "callee", None),
                    "operator": getattr(value, "operator", None),
                    "type": value.type.display() if value.type else None,
                    "child_types": [c.type.display() if c.type else None for c in value.children],
                })
    return nodes


def main() -> int:
    out_dir = Path("docs/port-engineering/future-precompute/task31")
    out_dir.mkdir(parents=True, exist_ok=True)

    identity = {name: identity_row(key) for name, key in KEYS.items()}
    first_gates = {name: first_gate_row(key) for name, key in KEYS.items()}

    curl_chain = probe_curl_chain()
    caustic_chain = probe_caustic_chain()
    lighting_chain = probe_lighting_chain()

    closures = {
        "curl": closure_nodes_for(KEYS["curl"], lambda v: (
            (v.kind == "builtin" and v.callee == "tanh")
            or (v.kind == "builtin" and v.callee == "mod"
                and tuple(c.type.display() for c in v.children) in
                {("vec3", "float"), ("vec4", "float")}))),
        "caustic": closure_nodes_for(KEYS["caustic"], lambda v: (
            (v.kind == "builtin" and v.callee == "floatBitsToUint")
            or (v.kind == "binary" and v.operator == "^"
                and v.type and v.type.display() == "uint"))),
        "lighting": closure_nodes_for(KEYS["lighting"], lambda v: (
            (v.kind == "builtin" and v.callee == "reflect")
            or (v.kind == "declaration" and v.type and v.type.kind == "array"))),
    }

    payload = {
        "schema": "noisemaker-for-cpp.future-precompute.task31.v1",
        "corpus_revision": REVISION,
        "note": ("Identity/whole/interface hashes use the exact _whole/_interface field-order "
                 "copied from extrude_bvec2_relational_reduction_profile.py. All monkeypatches "
                 "restored in finally; nothing under noisemaker-for-cpp was modified (verified "
                 "separately via find -newer)."),
        "identity": identity,
        "first_gates_unmodified": first_gates,
        "curl_chain": curl_chain,
        "caustic_chain": caustic_chain,
        "lighting_chain": lighting_chain,
        "closures": closures,
    }
    out = out_dir / "task31-probe-output.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(out)
    print(json.dumps({
        "first_gates": first_gates,
        "curl_chain": [{k: v for k, v in step.items() if k != "cpp_sha256"} for step in curl_chain["chain"]],
        "caustic_chain": [{k: v for k, v in step.items() if k != "cpp_sha256"} for step in caustic_chain["chain"]],
        "lighting_chain": lighting_chain["chain"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
