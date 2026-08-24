"""Authenticated frontend/projection lane for Classic Noise.

This is deliberately a key-specific admission record.  The five preprocessor
defines are compile-time authority only; the native interface remains the 24
source uniforms.  Dead helpers and matrix globals are removed only after the
source-bound closure is authenticated, then canonical literal-loop proofs and
the ``octaves`` runtime proof are rebuilt on the projected tree.
"""

from __future__ import annotations

import dataclasses
import hashlib
from collections import Counter
from typing import NamedTuple

from .loop_proof import (
    attach_counted_loop_proofs, clear_counted_loop_proofs,
    summarize_counted_loop_proofs)
from .runtime_loop_bound_profile import (
    RuntimeLoopBoundContract, RuntimeScalarBoundSeed,
    )
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "classicNoisedeck/noise:noise"
PROFILE = "classic-noise-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
NOISE_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "noise_frontend_profile"})}
RAW_BYTES = 31255
RAW_SHA256 = "4cd68543729f94788ef6fa2a484dd47d76154814b027128bef5eb9c8d7461663"
NORMALIZED_BYTES = 14064
NORMALIZED_SHA256 = "9f97d19e355f32e3821057ba8859770a87cbec56c57946d14378764deb8da0f0"

FIXED_DEFINES = (
    ("COLOR_MODE", "int", "6"),
    ("LOOP_OFFSET", "int", "300"),
    ("METRIC", "int", "0"),
    ("NOISE_TYPE", "int", "10"),
    ("REFRACT_MODE", "int", "2"),
)
DEFINES = FIXED_DEFINES
SOURCE_UNIFORMS = (
    ("time", "float"), ("seed", "int"), ("resolution", "vec2"),
    ("tileOffset", "vec2"), ("fullResolution", "vec2"),
    ("xScale", "float"), ("yScale", "float"), ("octaves", "int"),
    ("ridges", "bool"), ("refractAmt", "float"), ("kaleido", "float"),
    ("loopScale", "float"), ("speed", "float"), ("paletteMode", "int"),
    ("paletteOffset", "vec3"), ("paletteAmp", "vec3"),
    ("paletteFreq", "vec3"), ("palettePhase", "vec3"),
    ("cyclePalette", "int"), ("rotatePalette", "float"),
    ("repeatPalette", "float"), ("hueRange", "float"),
    ("hueRotation", "float"), ("wrap", "bool"),
)
RUNTIME_UNIFORM_ABI = tuple(
    (name, {"float": "float", "int": "int32", "bool": "bool",
            "vec2": "Vec2", "vec3": "Vec3"}[kind])
    for name, kind in SOURCE_UNIFORMS)
OUTPUT_ABI = ("fragColor", "vec4", "Vec4", "output")

# Source order, not lexical name order.  This is also the exact emitted state
# constructor order and is intentionally independent of the five fixed defines.
REACHABLE_FUNCTION_IDS = (
    144, 145, 146, 147, 151, 152, 153, 154, 155, 156, 159, 160,
    167, 169, 171)
ALL_FUNCTION_IDS = tuple(range(132, 172))
DEAD_FUNCTION_IDS = tuple(item for item in ALL_FUNCTION_IDS
                          if item not in REACHABLE_FUNCTION_IDS)
PROJECTED_DECLARATION_NAMES = tuple(name for name, _ in SOURCE_UNIFORMS) + ("fragColor",)
RUNTIME_SEED_PROVENANCE = "runtime-metadata-uniform-direct-parameter"
OCTAVES_PARAMETER_ID = 129
OCTAVES_UNIFORM_ID = 8
OCTAVES_CALL_SPAN = "604:17-604:70"
OCTAVES_CALL_SHA256 = "f9fe584857c36403bd636de831765b93b5559017183c4010dabc6c9adf1ea119"
OCTAVES_LOOP_SPAN = "533:5-558:6"
OCTAVES_LOOP_SHA256 = "4430989cf0b3baeba7fd80c3c91bb4668a046978f707a3432815b4475f5cf8f5"

# These are filled with the source-bound fingerprints once the first profile
# implementation is admitted.  Structural identity checks remain active even
# when a development checkout has not yet frozen the derived values.
PRE_FUNCTIONS_SHA256 = "c030e6d65da27c8aa1797ba1f53ca16d084e918e86247e1de47f67128de2d781"
PRE_WHOLE_PROGRAM_SHA256 = "92d54f1e6b8d3abb45b59b7da31b901f2ee5e89b4030f4f22a476fceaedeee29"
INTERFACE_SHA256 = "82b04cb03ee9125c8fc9bfdcae13de8345bd65608bff0bc16a61ae488efcfb58"
PROJECTED_FUNCTIONS_SHA256 = "1d89f895127b4fc13d12ce5f9b804203431eabff396f5aa3be972b0d95184187"
PROJECTED_WHOLE_PROGRAM_SHA256 = "96ea4907d79529d9672c143bb36498364c487936dad8b0c99fc4adbfc4116893"
PROJECTED_INTERFACE_SHA256 = "43f05e6de87b33471bc2057d14d4a65326e2dab0797027c17caaf3010ef1d788"


class FrontendProof(NamedTuple):
    program: TypedProgram
    reachable_functions: tuple[object, ...]
    dead_functions: tuple[object, ...]
    matrix_globals: tuple[object, ...]
    defines: tuple[tuple[str, str, str], ...]
    source_uniforms: tuple[tuple[str, str], ...]
    consumed_objects: tuple[object, ...]


class ProjectionProof(NamedTuple):
    program: TypedProgram
    functions: tuple[object, ...]
    declarations: tuple[object, ...]
    counted_loop_summary: object


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _walk(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk(child)


def _walk_statement(value: TypedStatement):
    yield value
    for expression in value.expressions:
        yield from _walk(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values: list[TypedExpression] = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(item for item in _walk_statement(statement)
                          if isinstance(item, TypedExpression))
    return tuple(values)


def _consumed_objects(program: TypedProgram) -> tuple[object, ...]:
    values = _expressions(program)
    statements = tuple(item for function in program.functions
                       for statement in function.body
                       for item in _walk_statement(statement)
                       if isinstance(item, TypedStatement))
    consumed = tuple(program.declarations) + tuple(program.functions) + statements + values
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("consumed-object ledger is not identity-disjoint")
    return consumed


def _whole(program: TypedProgram, *, cleared: bool = False) -> str:
    functions = (clear_counted_loop_proofs(program.functions)
                 if cleared else program.functions)
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _check_source(program: TypedProgram, source_hash: str | None) -> None:
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.body_status != "analyzed"):
        raise _fail("source or analysis provenance mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != FIXED_DEFINES:
        raise _fail("fixed compile-time define contract mismatch")


def _check_fingerprint(actual: str, expected: str | None, label: str) -> None:
    if expected is not None and actual != expected:
        raise _fail(f"{label} fingerprint mismatch")


def _uniforms(program: TypedProgram) -> tuple[tuple[str, str], ...]:
    return tuple((item.symbol.name, item.type.display())
                 for item in program.declarations
                 if item.symbol.storage == "uniform")


def authenticate_noise_frontend(program: TypedProgram, source_hash: str | None,
                                profile: str | None) -> FrontendProof:
    if profile != PROFILE:
        raise _fail("exact profile required")
    _check_source(program, source_hash)
    if _uniforms(program) != SOURCE_UNIFORMS:
        raise _fail("24-uniform interface census mismatch")
    if (program.resources.uniforms != tuple(name for name, _ in SOURCE_UNIFORMS)
            or program.resources.samplers != ()
            or program.resources.outputs != (OUTPUT_ABI[0],)
            or program.resources.uses_texture
            or program.resources.uses_derivatives):
        raise _fail("resource interface census mismatch")
    if tuple(item.signature.id for item in program.functions) != ALL_FUNCTION_IDS:
        raise _fail("function identity/order census mismatch")
    functions = clear_counted_loop_proofs(program.functions)
    _check_fingerprint(_sha(functions), PRE_FUNCTIONS_SHA256, "pre-function")
    _check_fingerprint(_whole(program, cleared=True), PRE_WHOLE_PROGRAM_SHA256,
                       "pre-whole-program")
    _check_fingerprint(_interface(program), INTERFACE_SHA256, "interface")
    reachable = tuple(item for item in program.functions
                      if item.signature.id in REACHABLE_FUNCTION_IDS)
    dead = tuple(item for item in program.functions
                 if item.signature.id in DEAD_FUNCTION_IDS)
    if tuple(item.signature.id for item in reachable) != REACHABLE_FUNCTION_IDS:
        raise _fail("reachable closure mismatch")
    if tuple(item.signature.id for item in dead) != DEAD_FUNCTION_IDS:
        raise _fail("dead closure mismatch")
    matrix_globals = tuple(item for item in program.declarations
                           if item.type.display() in {"mat3", "mat4"})
    if not matrix_globals:
        raise _fail("dead matrix-global closure missing")
    return FrontendProof(
        program, reachable, dead, matrix_globals, FIXED_DEFINES,
        SOURCE_UNIFORMS, _consumed_objects(program))


def authenticate_noise_runtime(program: TypedProgram, source_hash: str | None,
                               profile: str | None) -> RuntimeLoopBoundContract:
    if profile != PROFILE:
        raise _fail("exact profile required")
    _check_source(program, source_hash)
    function_ids = tuple(item.signature.id for item in program.functions)
    if function_ids == ALL_FUNCTION_IDS:
        _check_fingerprint(_sha(clear_counted_loop_proofs(program.functions)),
                           PRE_FUNCTIONS_SHA256, "pre-function")
        _check_fingerprint(_whole(program, cleared=True),
                           PRE_WHOLE_PROGRAM_SHA256, "pre-whole-program")
    elif function_ids == REACHABLE_FUNCTION_IDS:
        _check_fingerprint(_sha(program.functions), PROJECTED_FUNCTIONS_SHA256,
                           "projected-function")
        _check_fingerprint(_whole(program), PROJECTED_WHOLE_PROGRAM_SHA256,
                           "projected-whole-program")
    else:
        raise _fail("complete function tree identity mismatch")
    helper = next((item for item in program.functions
                   if item.signature.id == 155), None)
    main = next((item for item in program.functions if item.name == "main"), None)
    if helper is None or main is None or len(helper.parameters) != 5:
        raise _fail("octaves helper identity mismatch")
    parameter = helper.parameters[2]
    if ((parameter.id, parameter.name, parameter.type.display(), parameter.storage,
         parameter.writable, parameter.direction)
            != (OCTAVES_PARAMETER_ID, "octaves", "int", "parameter", True, "in")):
        raise _fail("octaves parameter identity mismatch")
    calls = []
    for statement in main.body:
        for value in _walk_statement(statement):
            if (isinstance(value, TypedExpression) and value.kind == "call"
                    and value.signature_id == helper.signature.id):
                calls.append(value)
    if len(calls) != 1:
        raise _fail("octaves call-site census mismatch")
    call = calls[0]
    if (_span(call) != OCTAVES_CALL_SPAN
            or _sha(call) != OCTAVES_CALL_SHA256
            or len(call.children) != 5 or call.children[2].kind != "id"
            or call.children[2].symbol_id != OCTAVES_UNIFORM_ID
            or call.children[2].symbol.name != "octaves"):
        raise _fail("octaves direct-uniform call-site mismatch")
    loops = [(function, value) for function in program.functions
             for statement in function.body
             for value in _walk_statement(statement)
             if isinstance(value, TypedStatement) and value.kind == "for"]
    named = [(function, loop) for function, loop in loops
             if function.signature.id == helper.signature.id
             and loop.span.start_line == 533]
    if len(named) != 1:
        raise _fail("octaves runtime loop identity mismatch")
    loop = named[0][1]
    if _span(loop) != OCTAVES_LOOP_SPAN:
        raise _fail("octaves runtime loop span mismatch")
    if len(program.functions) == len(ALL_FUNCTION_IDS):
        if loop.loop_proof is not None:
            raise _fail("preprojection octaves loop must be unproved")
        companions = [item for _, item in loops if item is not loop]
        if len(companions) != 2 or any(
                item.loop_proof is None
                or (item.loop_proof.start_value, item.loop_proof.bound_value,
                    item.loop_proof.comparison, item.loop_proof.update,
                    item.loop_proof.trip_count)
                != (0, 3, "<", "++", 3)
                for item in companions):
            raise _fail("literal companion loop proofs mismatch")
        if _sha(loop) != OCTAVES_LOOP_SHA256:
            raise _fail("octaves runtime loop source identity mismatch")
    elif loop.loop_proof is not None:
        proof = loop.loop_proof
        if ((proof.start_value, proof.bound_value, proof.comparison,
             proof.update, proof.trip_count, proof.bound_kind)
                    != (1, 8, "<=", "++", 8, RUNTIME_SEED_PROVENANCE)):
            raise _fail("octaves runtime loop proof mismatch")
    elif _sha(loop) != OCTAVES_LOOP_SHA256:
        raise _fail("octaves runtime loop source identity mismatch")
    seed = RuntimeScalarBoundSeed(
        parameter.id, 8, RUNTIME_SEED_PROVENANCE, parameter)
    contract = RuntimeLoopBoundContract(
        KEY, seed, "integer-range", "octaves", 1, 8, 2,
        f"{KEY} octaves must be in [1,8]")
    if (contract.seed is None or contract.seed.symbol is not parameter
            or contract.seed.maximum != 8
            or contract.key != KEY or contract.uniform_name != "octaves"
            or contract.minimum != 1 or contract.default != 2
            or contract.uniform_maximum != 8 or contract.maximum != 8
            or contract.kind != "integer-range"
            or contract.seed.provenance != RUNTIME_SEED_PROVENANCE):
        raise _fail("malformed authenticated octaves contract")
    return contract


def apply_noise_frontend(program: TypedProgram, source_hash: str | None,
                         profile: str | None) -> TypedProgram:
    proof = authenticate_noise_frontend(program, source_hash, profile)
    contract = authenticate_noise_runtime(program, source_hash, profile)
    functions = tuple(item for item in program.functions
                      if item.signature.id in REACHABLE_FUNCTION_IDS)
    functions = attach_counted_loop_proofs(
        clear_counted_loop_proofs(functions), KEY,
        runtime_scalar_bounds=(contract.seed,))
    declarations = tuple(item for item in program.declarations
                         if item.symbol.storage in {"uniform", "output"})
    projected = dataclasses.replace(
        program, declarations=declarations, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))
    authenticate_noise_projection(projected, source_hash, profile)
    return projected


def authenticate_noise_projection(program: TypedProgram, source_hash: str | None,
                                  profile: str | None) -> ProjectionProof:
    if profile != PROFILE:
        raise _fail("exact profile required for projected program")
    _check_source(program, source_hash)
    if tuple(item.signature.id for item in program.functions) != REACHABLE_FUNCTION_IDS:
        raise _fail("projected reachable closure mismatch")
    if tuple(item.symbol.name for item in program.declarations) != PROJECTED_DECLARATION_NAMES:
        raise _fail("projected declaration closure mismatch")
    if _uniforms(program) != SOURCE_UNIFORMS:
        raise _fail("projected 24-uniform interface mismatch")
    if any(item.type.display() in {"mat3", "mat4"} for item in program.declarations):
        raise _fail("projected matrix carrier escaped")
    values = _expressions(program)
    if any(item.kind == "builtin" and item.callee == "floatBitsToUint"
           for item in values):
        raise _fail("projected scalar-XOR carrier escaped")
    if any(item.kind == "index" for item in values):
        raise _fail("projected index carrier escaped")
    if any(item.operator in {"^", "^="} for item in values):
        raise _fail("projected mutable/XOR carrier escaped")
    if not any(item.name == "rotate2D" for item in program.functions):
        raise _fail("reachable rotate2D mat2 carrier was removed")
    summary = program.counted_loop_proof
    if summary is None or (summary.loop_count, summary.unproved_loop_count,
                           summary.max_effective_depth,
                           summary.max_lexical_product,
                           summary.entrypoint_charge,
                           summary.call_graph_acyclic) != (1, 0, 1, 8, 8, True):
        raise _fail("projected runtime loop summary mismatch")
    loop = next((value for function in program.functions
                 for statement in function.body
                 for value in _walk_statement(statement)
                 if isinstance(value, TypedStatement) and value.kind == "for"), None)
    if loop is None or loop.loop_proof is None or loop.loop_proof.bound_value != 8:
        raise _fail("projected octaves proof missing")
    functions_sha = _sha(program.functions)
    whole_sha = _whole(program)
    interface_sha = _interface(program)
    _check_fingerprint(functions_sha, PROJECTED_FUNCTIONS_SHA256,
                       "projected-function")
    _check_fingerprint(whole_sha, PROJECTED_WHOLE_PROGRAM_SHA256,
                       "projected-whole-program")
    _check_fingerprint(interface_sha, PROJECTED_INTERFACE_SHA256,
                       "projected-interface")
    return ProjectionProof(program, tuple(program.functions),
                           tuple(program.declarations), summary)


def verify_noise_projection(program: TypedProgram, proof: ProjectionProof) -> ProjectionProof:
    if not isinstance(proof, ProjectionProof) or proof.program is not program:
        raise _fail("projected proof is not bound to selected live program")
    expected = authenticate_noise_projection(program, RAW_SHA256, PROFILE)
    if (len(proof.functions) != len(expected.functions)
            or len(proof.declarations) != len(expected.declarations)
            or any(left is not right for left, right in zip(
                proof.functions, expected.functions))
            or any(left is not right for left, right in zip(
                proof.declarations, expected.declarations))
            or proof.counted_loop_summary != expected.counted_loop_summary):
        raise _fail("projected proof identity drift")
    return proof


def verify_noise_frontend(program: TypedProgram, proof: FrontendProof) -> FrontendProof:
    if not isinstance(proof, FrontendProof) or proof.program is not program:
        raise _fail("frontend proof is not bound to selected live program")
    expected = authenticate_noise_frontend(program, RAW_SHA256, PROFILE)
    def same_identity(left, right) -> bool:
        return (len(left) == len(right)
                and all(item is expected_item
                        for item, expected_item in zip(left, right)))

    if (not same_identity(proof.reachable_functions,
                          expected.reachable_functions)
            or not same_identity(proof.dead_functions, expected.dead_functions)
            or not same_identity(proof.matrix_globals, expected.matrix_globals)
            or not same_identity(proof.consumed_objects, expected.consumed_objects)
            or proof.defines != expected.defines
            or proof.source_uniforms != expected.source_uniforms):
        raise _fail("frontend proof identity drift")
    return proof


__all__ = (
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
    "PREPARED_PROFILES", "NOISE_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS",
    "RAW_BYTES", "RAW_SHA256", "NORMALIZED_BYTES",
    "NORMALIZED_SHA256", "FIXED_DEFINES", "SOURCE_UNIFORMS",
    "DEFINES", "RUNTIME_UNIFORM_ABI", "OUTPUT_ABI", "REACHABLE_FUNCTION_IDS",
    "DEAD_FUNCTION_IDS", "PROJECTED_DECLARATION_NAMES", "FrontendProof",
    "ProjectionProof", "authenticate_noise_frontend", "authenticate_noise_runtime",
    "authenticate_noise_projection", "verify_noise_projection",
    "verify_noise_frontend", "apply_noise_frontend",
)
