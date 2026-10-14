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
RAW_BYTES = 32527
RAW_SHA256 = "d86306e285a2f80dae86fe79cde92ceb89ec898ef78e6a15d140bfdf0e030bb2"
NORMALIZED_BYTES = 14516
NORMALIZED_SHA256 = "9c8b14bfae4e4107cbf00e0c98cf026232a4dcf9c528ef9b9cd095de43397a31"

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
OCTAVES_CALL_SPAN = "617:17-617:70"
OCTAVES_CALL_SHA256 = "1916c874d801d26c584797a32f26a264d5a0ced24ee3c63c52ba6db96078172d"
OCTAVES_LOOP_SPAN = "535:5-562:6"
OCTAVES_LOOP_SHA256 = "d716cbe498e0a65e8fb4cfde8111b3de9b3b9408772573ca18989ea3a7634961"

# These are filled with the source-bound fingerprints once the first profile
# implementation is admitted.  Structural identity checks remain active even
# when a development checkout has not yet frozen the derived values.
PRE_FUNCTIONS_SHA256 = "5d8602eaa58f09ab0e3d40f06a5c40f2d6cb13a23b23f9d0112e7007a46d612d"
PRE_WHOLE_PROGRAM_SHA256 = "ae20df5a34f7a3ef85ea5d06a45aed865375c92286f0d6f76b8ef7a3f734199e"
INTERFACE_SHA256 = "0a8a35c7ff49b0c41ef22473bf300e4c9339e3d467f1aa54eab432787e314cab"
PROJECTED_FUNCTIONS_SHA256 = "0f1488a9c9c9f04d3a31edc99551f8ab6d1224edd19377ccceb5507cef41b27c"
PROJECTED_WHOLE_PROGRAM_SHA256 = "a748d51726f7bb0b745a38556b1c26afc51a3ece2253a852e32e4bb81fdb30b0"
PROJECTED_INTERFACE_SHA256 = "61a01b4c45504af1921978ba524f2f1c7d23a53d7ae89df0ee9447738b1244d1"


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
    if _dynamic_selected(program):
        return _authenticate_dynamic_frontend(program, source_hash)
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
    if _dynamic_selected(program):
        return _authenticate_dynamic_runtime(program, source_hash)
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
             and loop.span.start_line == int(OCTAVES_LOOP_SPAN.split(":", 1)[0])]
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
    if _dynamic_selected(program):
        return _apply_dynamic_frontend(program, source_hash, profile)
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
    if _dynamic_selected(program):
        return _authenticate_dynamic_projection(program, source_hash)
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


# Five runtime integer defines produce a separate, source-authenticated tree.
# The fixed-define projection above keeps its original fingerprints and gates.
_DYNAMIC_DEFINES = (('COLOR_MODE', 'str', 'int'),
 ('LOOP_OFFSET', 'str', 'int'),
 ('METRIC', 'str', 'int'),
 ('NOISE_TYPE', 'str', 'int'),
 ('REFRACT_MODE', 'str', 'int'))
_DYNAMIC_IDENTITY = (25933,
 '57766e86231d83aaa0f3d8bc249488717f5abf5f1eeacfde2f7716670cefa1da',
 (('COLOR_MODE', 'str', 'int'),
  ('LOOP_OFFSET', 'str', 'int'),
  ('METRIC', 'str', 'int'),
  ('NOISE_TYPE', 'str', 'int'),
  ('REFRACT_MODE', 'str', 'int')),
 (158,
  159,
  160,
  161,
  162,
  163,
  164,
  165,
  166,
  167,
  168,
  169,
  170,
  171,
  172,
  173,
  174,
  175,
  176,
  177,
  178,
  179,
  180,
  181,
  182,
  183,
  184,
  185,
  186,
  187,
  188,
  189,
  190,
  191,
  192,
  193,
  194,
  195,
  196,
  197,
  198,
  199,
  200,
  201,
  202,
  203),
 '4f2a51b01c6695801ac91f69b6e75e6ba2b29348c970c183032dd18ccacb6607',
 'f47b3437dc94d87054b5a603d77df556dc322b48d4fcb5aa93b91358da45c682',
 '18dad3df629463d414a68cbb5fbfdc78a2030dfe656e573a77e8d4743861b4f8',
 ((1,
   'COLOR_MODE',
   'int',
   'uniform',
   '1:1-1:24',
   '9ef007217df951ecc2f7b10fca555c469c7478e19608bc809d666e89b674d6ac'),
  (2,
   'LOOP_OFFSET',
   'int',
   'uniform',
   '2:1-2:25',
   'a34f76af39ef49b034a71a049a0b7210b90f7c387c459bccf2fdc43bb896e078'),
  (3,
   'METRIC',
   'int',
   'uniform',
   '3:1-3:20',
   'f4812ef73bc63e5c63b8f87c1b66d66a9c3113834b03d38ae56bb4cdb3ddd227'),
  (4,
   'NOISE_TYPE',
   'int',
   'uniform',
   '4:1-4:24',
   'a7cfaff4a29eaa3482508a8db0235d67f1facb64955a0e66c4f8d2aa69c3ce66'),
  (5,
   'REFRACT_MODE',
   'int',
   'uniform',
   '5:1-5:26',
   '3c3459b88559d7a6d62e1ce81596ac9fbcd07c0293fecfa144b60c52481a5e9b'),
  (6,
   'time',
   'float',
   'uniform',
   '23:1-23:20',
   '2effab0ccf61c1f960e79733d2565f6a093a575396712f87aeed72f437dac6ee'),
  (7,
   'seed',
   'int',
   'uniform',
   '24:1-24:18',
   '383f0cb7d61cbc39c631e34433ced0e09db5ea4ea004e1e0ef521e4385492512'),
  (8,
   'resolution',
   'vec2',
   'uniform',
   '25:1-25:25',
   '54972ee559dc37f7904a06a9534ad3252a845223888528c3195a452ef75288c0'),
  (9,
   'tileOffset',
   'vec2',
   'uniform',
   '26:1-26:25',
   '5708237ed48701a0049cd5d46f69fd219960f0304a8c4a1d0508066cb454277c'),
  (10,
   'fullResolution',
   'vec2',
   'uniform',
   '27:1-27:29',
   'ba991a174712aeb47bdb2db0cf80c241d2e7672cab4414a780ddfc9b78edd78f'),
  (11,
   'xScale',
   'float',
   'uniform',
   '28:1-28:22',
   'b457dca4ba06f9642679c6b5d518eae79bd846961fb6911baf2d4e72436551b7'),
  (12,
   'yScale',
   'float',
   'uniform',
   '29:1-29:22',
   '56c7a06f45533efd0add0c60b202ca63ed4e64a8a7cce90627c8cba0b7280e4e'),
  (13,
   'octaves',
   'int',
   'uniform',
   '30:1-30:21',
   '5cde20693be730cfffe83ee2fab058d1f6301167f00929b433aef9811f4f9f06'),
  (14,
   'ridges',
   'bool',
   'uniform',
   '31:1-31:21',
   'd819c02820e69c839b0d12442d195e730e6b24d13d5b273337e48202b47b396b'),
  (15,
   'refractAmt',
   'float',
   'uniform',
   '32:1-32:26',
   'e1679acf262cd0e1e48924b9a28c5cf3f2d20e40cacfd0853d2d6b94fd6a5ac9'),
  (16,
   'kaleido',
   'float',
   'uniform',
   '33:1-33:23',
   'f023c972d0800e1ceabf16429170a80c3b805bb5adddeb314516f93f479c26e4'),
  (17,
   'loopScale',
   'float',
   'uniform',
   '34:1-34:25',
   'cb8bdb9aa856f0d136e35b9c1639cfd42ce3bc482fe92cae8fb2f89edd152742'),
  (18,
   'speed',
   'float',
   'uniform',
   '35:1-35:21',
   '64dfbf5781f732ec387430876e0d5032052c7ada8c9738e41ec7a5637c3486a2'),
  (19,
   'paletteMode',
   'int',
   'uniform',
   '36:1-36:25',
   '9da1a73f49861d0ec021de66998132284f97ab305076777c2763145386c000bc'),
  (20,
   'paletteOffset',
   'vec3',
   'uniform',
   '37:1-37:28',
   '790fe13596ec3db419584fb1bcd2ad81d36140566ae13a3ea0448f0fd0d8fd97'),
  (21,
   'paletteAmp',
   'vec3',
   'uniform',
   '38:1-38:25',
   '38da792772d32bd80e904a15a3c720d9ab51af1917ed73602c0b7f06bb4f5158'),
  (22,
   'paletteFreq',
   'vec3',
   'uniform',
   '39:1-39:26',
   '502a7109005186fffd06c48ec397b69c2d8bc12484c85982ebe6ec107084cf2c'),
  (23,
   'palettePhase',
   'vec3',
   'uniform',
   '40:1-40:27',
   'e6562a78cb2e432236accf0fc7529d200a26a020c6b9534034be9856ca0bf940'),
  (24,
   'cyclePalette',
   'int',
   'uniform',
   '41:1-41:26',
   '9d02c595028fba9dce56528ef9f06105a9fc9413f6ef5c6966fd9c21e5ac09be'),
  (25,
   'rotatePalette',
   'float',
   'uniform',
   '42:1-42:29',
   '1f1c5fc675aef39f92224c3dab10e4ebbd95f2f9958f5bcff01b3c8987055497'),
  (26,
   'repeatPalette',
   'float',
   'uniform',
   '43:1-43:29',
   '0605bc1ad4cfc81683c5c1ed9ffd59b084b52b36184898558ab03683bb87918b'),
  (27,
   'hueRange',
   'float',
   'uniform',
   '44:1-44:24',
   '017f0c010b3f8632b42b4b99c1b37d76e8e4510fdb40363c96d69472f042f5f8'),
  (28,
   'hueRotation',
   'float',
   'uniform',
   '45:1-45:27',
   'eb17d3b43f0beaf2604b204b2b8c1501ef144f47231cbbe3d298bc21850c7868'),
  (29,
   'wrap',
   'bool',
   'uniform',
   '46:1-46:19',
   '50e516beedf89d447fa9e90e553016eb564be35e45992be9c1dce384cd8161ef'),
  (30,
   'fragColor',
   'vec4',
   'output',
   '47:1-47:16',
   '29906fe5332cc00eaa15d7c5fff81de273f1e8818a76fb47496930a43c1d4765'),
  (141,
   'fwdA',
   'mat3',
   'const',
   '692:1-694:68',
   '0797d7e9fe948b47081231125e454e6a709c9cdc82ed70714230ba29ff695ef8'),
  (142,
   'fwdB',
   'mat3',
   'const',
   '696:1-698:68',
   'c67f36bb8ba75aa95312ad826392d114a7630e65276a1fce3ddd65f44977704c'),
  (143,
   'invB',
   'mat3',
   'const',
   '700:1-702:66',
   '25698bf9cdd90044f8653da2f511d0641ad104c20cf6f8ac33a89f76ca1d68e0'),
  (144,
   'invA',
   'mat3',
   'const',
   '704:1-706:68',
   '82e5abb35de82ec517810c97f832a383a1c7c0557e02b0ec76538d5ca219e083')),
 (('COLOR_MODE',
   'LOOP_OFFSET',
   'METRIC',
   'NOISE_TYPE',
   'REFRACT_MODE',
   'time',
   'seed',
   'resolution',
   'tileOffset',
   'fullResolution',
   'xScale',
   'yScale',
   'octaves',
   'ridges',
   'refractAmt',
   'kaleido',
   'loopScale',
   'speed',
   'paletteMode',
   'paletteOffset',
   'paletteAmp',
   'paletteFreq',
   'palettePhase',
   'cyclePalette',
   'rotatePalette',
   'repeatPalette',
   'hueRange',
   'hueRotation',
   'wrap'),
  (),
  ('fragColor',),
  False,
  False),
 ((158, 'bicubicValue', (159, 168, 170)),
  (159, 'blendBicubic', ()),
  (160, 'blendLinearOrCosine', ()),
  (161, 'catmullRom3', ()),
  (162, 'catmullRom3x3ValueNoise', (161, 168, 169)),
  (163, 'catmullRom4', ()),
  (164, 'catmullRom4x4ValueNoise', (163, 168, 170)),
  (165, 'circles', ()),
  (166, 'concentric', ()),
  (167, 'constant', (168,)),
  (168, 'constantFromLattice', (169,)),
  (169, 'constantFromLatticeWithOffset', (189, 190, 192)),
  (170, 'constantOffset', (169,)),
  (171, 'cubic', ()),
  (172, 'cubic3x3ValueNoise', (168, 169, 194)),
  (173, 'diamonds', ()),
  (174, 'generate_octave', (203,)),
  (175, 'getMetric', ()),
  (176, 'hsv2rgb', ()),
  (177, 'kaleidoscope', (175, 198)),
  (178, 'latticeValue', (168,)),
  (179, 'linearToSrgb', ()),
  (180, 'linear_srgb_from_oklab', ()),
  (181, 'main', (177, 182, 185, 186, 190)),
  (182, 'map', ()),
  (183, 'mod289', ()),
  (184, 'mod289', ()),
  (185, 'multires', (174, 176, 179, 180, 182, 188, 196, 202, 203)),
  (186, 'offset', (165, 173, 197, 199, 203)),
  (187, 'oklab_from_linear_srgb', ()),
  (188, 'pal', (176, 179, 180)),
  (189, 'pcg', ()),
  (190, 'periodicFunction', (182,)),
  (191, 'permute', (184,)),
  (192, 'positiveModulo', ()),
  (193, 'prng', (189,)),
  (194, 'quadratic3', ()),
  (195, 'random', (193,)),
  (196, 'rgb2hsv', ()),
  (197, 'rings', ()),
  (198, 'rotate2D', ()),
  (199, 'shape', ()),
  (200, 'simplexValue', (182, 183, 190, 191)),
  (201, 'sineNoise', (193,)),
  (202, 'srgbToLinear', ()),
  (203, 'value', (158, 160, 162, 164, 168, 170, 172, 200, 201))),
 (158,
  159,
  160,
  161,
  162,
  163,
  164,
  165,
  168,
  169,
  170,
  172,
  173,
  174,
  175,
  176,
  177,
  179,
  180,
  181,
  182,
  183,
  184,
  185,
  186,
  188,
  189,
  190,
  191,
  192,
  193,
  194,
  196,
  197,
  198,
  199,
  200,
  201,
  202,
  203),
 (('fwdA',
   ((180,
     'linear_srgb_from_oklab',
     '715:16-715:20',
     'e93c16b0ae44a5cf5d388240a23392d438b7f0880f7e43676e0623bb58182c3d'),)),
  ('fwdB',
   ((180,
     'linear_srgb_from_oklab',
     '717:12-717:16',
     'ff0739b42ccc58b361247e21e370fd17a0add5485efdff1339d0917ab555c127'),)),
  ('invB',
   ((187,
     'oklab_from_linear_srgb',
     '709:16-709:20',
     '1c35a6e96fb13e15cf58862c2aef06b12cc61af74447dc2555f85d04745d0930'),)),
  ('invA',
   ((187,
     'oklab_from_linear_srgb',
     '711:12-711:16',
     'ff9aed7a709f2748d46a88300ac7898c6b0d9b6ca55776ff3c72d3fbba365f31'),))))
_DYNAMIC_PROJECTION = (('COLOR_MODE',
  'LOOP_OFFSET',
  'METRIC',
  'NOISE_TYPE',
  'REFRACT_MODE',
  'time',
  'seed',
  'resolution',
  'tileOffset',
  'fullResolution',
  'xScale',
  'yScale',
  'octaves',
  'ridges',
  'refractAmt',
  'kaleido',
  'loopScale',
  'speed',
  'paletteMode',
  'paletteOffset',
  'paletteAmp',
  'paletteFreq',
  'palettePhase',
  'cyclePalette',
  'rotatePalette',
  'repeatPalette',
  'hueRange',
  'hueRotation',
  'wrap',
  'fragColor',
  'fwdA',
  'fwdB'),
 (158,
  159,
  160,
  161,
  162,
  163,
  164,
  165,
  168,
  169,
  170,
  172,
  173,
  174,
  175,
  176,
  177,
  179,
  180,
  181,
  182,
  183,
  184,
  185,
  186,
  188,
  189,
  190,
  191,
  192,
  193,
  194,
  196,
  197,
  198,
  199,
  200,
  201,
  202,
  203),
 'f815f59f32cdf19e3fec5eed12f2d39b28f99c83d94322436f2c5f6815b774a2',
 'b514f8a4cc31f1241fc70855b7a5ff64f33540b9902233db2dfbd9b0d3a9b835',
 '9e2b791e215b5e729b9ac43c82dcfd6d8e87a15b37bc21b997bf54858c57ff78',
 (3, 0, 1, 8, 11, True))
_DYNAMIC_OCTAVES = (185,
 155,
 13,
 181,
 '937:17-937:70',
 'd89dd6a6b2e941a8451c4b58872cadde8875eba2c29a8981f6dbc95012d3be14',
 '777:5-808:6',
 '0317155518fcbb780e43f5c0f6024dcf3f41ff004451cdd7ae61d9ecee2db54c',
 (('linearToSrgb', '667:5-673:6', '9c6f8ab837fa4fbe01f6de9a08965ee92eb9924c272497c62de78273bcb3dcb9'),
  ('srgbToLinear', '679:5-685:6', '53587573f190ffa7f118aad5fdeb62b1f2a1a10ca7842e70a064ac2f5187c84b')))
_DYNAMIC_REACHABLE_IDS = (158,
 159,
 160,
 161,
 162,
 163,
 164,
 165,
 168,
 169,
 170,
 172,
 173,
 174,
 175,
 176,
 177,
 179,
 180,
 181,
 182,
 183,
 184,
 185,
 186,
 188,
 189,
 190,
 191,
 192,
 193,
 194,
 196,
 197,
 198,
 199,
 200,
 201,
 202,
 203)
_DYNAMIC_DEAD_IDS = (166, 167, 171, 178, 187, 195)
_DYNAMIC_RECORD_SHA256 = '8dc28d99131ed43623fc713acd74896b354e28096fe68035fc2a750a6d8e13f5'


def _dynamic_selected(program: TypedProgram) -> bool:
    return tuple((d.name,d.kind,d.canonical_value) for d in program.preprocessor_defines) == _DYNAMIC_DEFINES


def _check_dynamic_record(program: TypedProgram, source_hash: str | None) -> None:
    if (_sha((_DYNAMIC_IDENTITY,_DYNAMIC_PROJECTION,_DYNAMIC_OCTAVES,
              _DYNAMIC_REACHABLE_IDS,_DYNAMIC_DEAD_IDS)) != _DYNAMIC_RECORD_SHA256
            or program.key != KEY or source_hash != RAW_SHA256
            or len(program.raw_source.encode('utf-8')) != RAW_BYTES
            or hashlib.sha256(program.raw_source.encode('utf-8')).hexdigest() != RAW_SHA256
            or len(program.source.encode('utf-8')) != _DYNAMIC_IDENTITY[0]
            or hashlib.sha256(program.source.encode('utf-8')).hexdigest() != _DYNAMIC_IDENTITY[1]
            or program.body_status != 'analyzed' or program.structs or program.uniform_blocks):
        raise _fail('runtime source, record, or structure mismatch')


def _dynamic_graph(program: TypedProgram):
    known={f.signature.id for f in program.functions}
    main=next((f.signature.id for f in program.functions if f.name=='main'),None)
    if main is None:
        raise _fail('runtime main function absent')
    graph=tuple((f.signature.id,f.name,tuple(sorted({x.signature_id for st in f.body
                    for x in _walk_statement(st) if isinstance(x,TypedExpression)
                    and x.kind=='call' and x.signature_id in known}))) for f in program.functions)
    seen=set();stack=[main]
    lookup={i:c for i,name,c in graph}
    while stack:
        i=stack.pop()
        if i in seen:continue
        seen.add(i);stack.extend(lookup[i])
    return graph,tuple(sorted(seen))


def _dynamic_matrix_refs(program: TypedProgram):
    return tuple((d.symbol.name,tuple((f.signature.id,f.name,_span(x),_sha(x))
                  for f in program.functions for st in f.body for x in _walk_statement(st)
                  if isinstance(x,TypedExpression) and x.kind=='id' and x.symbol_id==d.symbol.id))
                 for d in program.declarations if d.symbol.name in {'fwdA','fwdB','invA','invB'})


def _authenticate_dynamic_frontend(program: TypedProgram, source_hash: str | None) -> FrontendProof:
    _check_dynamic_record(program, source_hash)
    if not _dynamic_selected(program):raise _fail('five runtime-int define carrier required')
    graph,seen=_dynamic_graph(program)
    loop_free=clear_counted_loop_proofs(program.functions)
    identity=(len(program.source.encode('utf-8')),
              hashlib.sha256(program.source.encode('utf-8')).hexdigest(),
              tuple((d.name,d.kind,d.canonical_value) for d in program.preprocessor_defines),
              tuple(f.signature.id for f in program.functions),_sha(loop_free),
              _whole(program,cleared=True),_interface(program),
              tuple((d.symbol.id,d.symbol.name,d.type.display(),d.symbol.storage,_span(d),_sha(d))
                    for d in program.declarations),
              (program.resources.uniforms,program.resources.samplers,program.resources.outputs,
               program.resources.uses_texture,program.resources.uses_derivatives),graph,seen,
              _dynamic_matrix_refs(program))
    if (identity != _DYNAMIC_IDENTITY or seen!=_DYNAMIC_REACHABLE_IDS
            or tuple(i for i in _DYNAMIC_IDENTITY[3] if i not in seen)!=_DYNAMIC_DEAD_IDS):
        raise _fail('runtime full tree, interface, call graph, or matrix refs mismatch')
    matrices=tuple(d for d in program.declarations if d.type.display()=='mat3')
    if (tuple(d.symbol.name for d in matrices)!=('fwdA','fwdB','invB','invA')
            or not all(refs and all(item[0] in seen for item in refs)
                       for name,refs in _dynamic_matrix_refs(program)[:2])
            or any(any(item[0] in seen for item in refs)
                   for name,refs in _dynamic_matrix_refs(program)[2:])):
        raise _fail('runtime matrix reachability mismatch')
    return FrontendProof(program,tuple(f for f in program.functions if f.signature.id in seen),
                         tuple(f for f in program.functions if f.signature.id in _DYNAMIC_DEAD_IDS),
                         matrices,_DYNAMIC_DEFINES,
                         _uniforms(program),_consumed_objects(program))


def _authenticate_dynamic_runtime(program: TypedProgram, source_hash: str | None) -> RuntimeLoopBoundContract:
    _check_dynamic_record(program,source_hash)
    projected=tuple(d.symbol.name for d in program.declarations)==_DYNAMIC_PROJECTION[0]
    if projected:
        _authenticate_dynamic_projection(program,source_hash)
    else:
        _authenticate_dynamic_frontend(program,source_hash)
    helper=next((f for f in program.functions if f.signature.id==_DYNAMIC_OCTAVES[0]),None)
    main=next((f for f in program.functions if f.signature.id==_DYNAMIC_OCTAVES[3]),None)
    if helper is None or main is None or len(helper.parameters)!=5:
        raise _fail('runtime octaves owner mismatch')
    parameter=helper.parameters[2]
    if (parameter.id,parameter.name,parameter.type.display(),parameter.storage,
        parameter.writable,parameter.direction)!=(_DYNAMIC_OCTAVES[1],'octaves','int','parameter',True,'in'):
        raise _fail('runtime octaves parameter mismatch')
    calls=tuple(x for st in main.body for x in _walk_statement(st)
                if isinstance(x,TypedExpression) and x.kind=='call'
                and x.signature_id==helper.signature.id)
    loops=tuple((f,x) for f in program.functions for st in f.body for x in _walk_statement(st)
                if isinstance(x,TypedStatement) and x.kind=='for')
    named=tuple(x for f,x in loops if f is helper)
    if (len(calls)!=1 or len(named)!=1
            or (_span(calls[0]),_sha(calls[0]),_span(named[0]))
            !=(_DYNAMIC_OCTAVES[4],_DYNAMIC_OCTAVES[5],_DYNAMIC_OCTAVES[6])
            or calls[0].children[2].kind!='id'
            or calls[0].children[2].symbol_id!=_DYNAMIC_OCTAVES[2]
            or (tuple((f.name,_span(x)) for f,x in loops if x is not named[0])
                !=tuple((name,span) for name,span,digest in _DYNAMIC_OCTAVES[8])
                if projected else tuple((f.name,_span(x),_sha(x)) for f,x in loops
                                        if x is not named[0])!=_DYNAMIC_OCTAVES[8])):
        raise _fail('runtime octaves call or loop census mismatch')
    loop=named[0]
    if projected:
        if (loop.loop_proof is None or loop.loop_proof.bound_value!=8
                or loop.loop_proof.bound_kind!=RUNTIME_SEED_PROVENANCE):
            raise _fail('runtime projected octaves proof mismatch')
    elif loop.loop_proof is not None or _sha(loop)!=_DYNAMIC_OCTAVES[7]:
        raise _fail('runtime preprojection octaves source mismatch')
    seed=RuntimeScalarBoundSeed(parameter.id,8,RUNTIME_SEED_PROVENANCE,parameter)
    return RuntimeLoopBoundContract(KEY,seed,'integer-range','octaves',1,8,2,
                                    f'{KEY} octaves must be in [1,8]')


def _apply_dynamic_frontend(program: TypedProgram,source_hash: str | None,
                            profile: str | None) -> TypedProgram:
    if profile != PROFILE:raise _fail('exact profile required')
    _authenticate_dynamic_frontend(program,source_hash)
    contract=_authenticate_dynamic_runtime(program,source_hash)
    functions=attach_counted_loop_proofs(clear_counted_loop_proofs(tuple(
        f for f in program.functions if f.signature.id in _DYNAMIC_REACHABLE_IDS)),KEY,
        runtime_scalar_bounds=(contract.seed,))
    declarations=tuple(d for d in program.declarations if d.symbol.name in _DYNAMIC_PROJECTION[0])
    projected=dataclasses.replace(program,declarations=declarations,functions=functions,
                                  counted_loop_proof=summarize_counted_loop_proofs(functions))
    _authenticate_dynamic_projection(projected,source_hash)
    return projected


def _authenticate_dynamic_projection(program: TypedProgram,source_hash: str | None) -> ProjectionProof:
    _check_dynamic_record(program,source_hash)
    summary=program.counted_loop_proof
    if summary is None:raise _fail('runtime projected loop summary absent')
    actual=(tuple(d.symbol.name for d in program.declarations),
            tuple(f.signature.id for f in program.functions),_sha(program.functions),
            _whole(program),_interface(program),
            (summary.loop_count,summary.unproved_loop_count,summary.max_effective_depth,
             summary.max_lexical_product,summary.entrypoint_charge,summary.call_graph_acyclic))
    if actual!=_DYNAMIC_PROJECTION:
        raise _fail('runtime projection identity mismatch')
    _authenticate_dynamic_runtime_core = tuple(f.signature.id for f in program.functions)
    if _authenticate_dynamic_runtime_core != _DYNAMIC_REACHABLE_IDS:
        raise _fail('runtime reachable function census mismatch')
    if any(d.symbol.name in {'invA','invB'} for d in program.declarations):
        raise _fail('runtime dead matrix escaped')
    return ProjectionProof(program,tuple(program.functions),tuple(program.declarations),summary)
