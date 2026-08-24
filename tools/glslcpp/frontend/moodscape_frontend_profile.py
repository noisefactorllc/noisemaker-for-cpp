"""Authenticated frontend admission record for ``classicNoisedeck/moodscape``.

The pinned variant is the catalog default (``COLOR_MODE=2``,
``NOISE_TYPE=10``). Moodscape contains a complete Oklab/lattice-hash closure,
but that closure is unreachable from ``main`` in this variant. The profile
records the exact live function graph and the four matrix globals plus
``floatBitsToUint`` site that remain dead.  Native admission uses the exact
source-bound projection below: only those authenticated dead objects are
omitted, while source bytes and the runtime interface remain intact.
"""

from __future__ import annotations

import dataclasses
import hashlib
from collections import Counter
from typing import NamedTuple

from .loop_proof import (
    attach_counted_loop_proofs, clear_counted_loop_proofs,
    summarize_counted_loop_proofs)
from .typed_ir import TypedExpression, TypedProgram

KEY = "classicNoisedeck/moodscape:moodscape"
PROFILE = "moodscape-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
MOODSCAPE_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "moodscape_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 19559
RAW_SHA256 = "a2580a36096208dd7a63965d2b277be9356f29a8d3af634d1736df9142db1a44"
NORMALIZED_BYTES = 10001
NORMALIZED_SHA256 = "fc6cb8b3d72af5960adeed5cf021cd5f026a2782744dba21ff7f69bb77abda06"
FUNCTIONS_SHA256 = "895e2d5aeffc140ee5d6022c43b106a1337f0aced78ad1be40e08f1a86b64756"
WHOLE_PROGRAM_SHA256 = "940632b3735086ed6c3e63151dfcbad4d3dd14a8bfc0a29973d9cbba915f8ba5"
INTERFACE_SHA256 = "f3876f90ac1837966902b9abac594eaeb7d930cc40ae3eb815755db99c8197f9"
DEFINES = (("COLOR_MODE", "int", "2"), ("NOISE_TYPE", "int", "10"))
SOURCE_UNIFORMS = (
    ("time", "float"), ("seed", "int"), ("wrap", "bool"), ("resolution", "vec2"),
    ("tileOffset", "vec2"), ("fullResolution", "vec2"), ("noiseScale", "float"),
    ("refractAmt", "float"), ("speed", "float"), ("hueRotation", "float"),
    ("hueRange", "float"), ("intensity", "float"), ("ridges", "bool"),
)
RUNTIME_UNIFORM_ABI = (
    ("time", "float"), ("seed", "int32"), ("wrap", "bool"), ("resolution", "Vec2"),
    ("tileOffset", "Vec2"), ("fullResolution", "Vec2"), ("noiseScale", "float"),
    ("refractAmt", "float"), ("speed", "float"), ("hueRotation", "float"),
    ("hueRange", "float"), ("intensity", "float"), ("ridges", "bool"),
)
OUTPUT_ABI = ("fragColor", "vec4", "Vec4", "output")
FUNCTION_IDS = (
    (83, "blendBicubic", "float"), (84, "blendLinearOrCosine", "float"),
    (85, "brightnessContrast", "vec3"), (86, "catmullRom3", "float"),
    (87, "catmullRom4", "float"), (88, "constant", "float"),
    (89, "constantOffset", "float"), (90, "hsv2rgb", "vec3"),
    (91, "linearToSrgb", "vec3"), (92, "linear_srgb_from_oklab", "vec3"),
    (93, "main", "void"), (94, "map", "float"), (95, "mod289", "vec2"),
    (96, "mod289", "vec3"), (97, "oklab_from_linear_srgb", "vec3"),
    (98, "pcg", "uvec3"), (99, "periodicFunction", "float"),
    (100, "permute", "vec3"), (101, "positiveModulo", "int"),
    (102, "prng", "vec3"), (103, "quadratic3", "float"),
    (104, "randomFromLatticeWithOffset", "vec3"), (105, "rgb2hsv", "vec3"),
    (106, "simplexValue", "float"), (107, "value", "float"),
)
REACHABLE_FUNCTION_IDS = (85, 90, 93, 94, 95, 96, 99, 100, 106, 107)
DEAD_FUNCTION_IDS = tuple(item[0] for item in FUNCTION_IDS if item[0] not in REACHABLE_FUNCTION_IDS)
MATRIX_GLOBALS = (
    ("fwdA", "mat3", "149:1-151:68", "85a4715acaf78728352d568ef227dceecb7ab4f5b7f0ade1f5771167bdaee42d"),
    ("fwdB", "mat3", "153:1-155:68", "208960cfc4d297c5beff5b6521661cb0a6e1cd357822cea8cf5c36fb5677f1c9"),
    ("invB", "mat3", "157:1-159:66", "7d3e3237c73de1df65fde01f18f6252bfcdd40accd62a41ec9d57fae216a2f9d"),
    ("invA", "mat3", "161:1-163:68", "a8cb27a30a592e9aef5f532cc90d14c6d454e331f56d7f5e4ec10d4d70ed3588"),
)
FLOAT_BITS_SPAN = "282:21-282:46"
FLOAT_BITS_SHA256 = "79f944c016354e20759966fd662d952e80f99dec01f5680a0be7cedec4d12e4e"
EXPECTED_NODE_COUNTS = {"id": 437, "binary": 283, "literal": 253, "swizzle": 93, "declaration": 80, "construct": 50, "assign": 48, "builtin": 37, "call": 33, "unary": 27, "conditional": 6, "index": 5}
EXPECTED_OPERATOR_COUNTS = {"*": 108, "-": 68, "+": 60, "=": 36, "/": 32, "<": 9, "+=": 8, "<=": 7, "==": 6, "&&": 6, "^": 4, ">=": 3, ">": 3, "-=": 2, "++": 1, "^=": 1, ">>": 1, "%": 1, "!=": 1, "*=": 1}

# These locks describe the one admitted native projection.  They are derived
# from the authenticated source closure, not from a generic dead-code pass:
# only the four named matrix globals and the authenticated dead functions may
# disappear.  The reachable functions are re-annotated because the sole
# counted loop belongs to the omitted ``linearToSrgb`` helper.
PROJECTED_FUNCTIONS_SHA256 = "260c309f8b28b138628fbb167603f0740ab8b0c76c88168873fd870017016980"
PROJECTED_WHOLE_PROGRAM_SHA256 = "08181011c8964c7e3213237a89875ae85499bad3310683e22628f8ef29018523"
PROJECTED_INTERFACE_SHA256 = "5d6e657e75ba6dea4922a0c0b25b800b44a49d40d7e38dd12d886b0430381733"
PROJECTED_DECLARATION_NAMES = (
    "time", "seed", "wrap", "resolution", "tileOffset", "fullResolution",
    "noiseScale", "refractAmt", "speed", "hueRotation", "hueRange",
    "intensity", "ridges", "fragColor")


class FrontendProof(NamedTuple):
    program: TypedProgram
    program_key: str
    profile: str
    source_hash: str
    normalized_source_hash: str
    source_uniforms: tuple[tuple[str, str], ...]
    runtime_uniform_abi: tuple[tuple[str, str], ...]
    functions: tuple[object, ...]
    reachable_functions: tuple[object, ...]
    dead_functions: tuple[object, ...]
    matrix_globals: tuple[TypedExpression, ...]
    float_bits_node: TypedExpression
    expression_nodes: tuple[TypedExpression, ...]
    consumed_objects: tuple[object, ...]
    node_counts: tuple[tuple[str, int], ...]
    operator_counts: tuple[tuple[str, int], ...]
    defines: tuple[tuple[str, str, str], ...]
    output_abi: tuple[str, str, str, str]


class ProjectionProof(NamedTuple):
    program: TypedProgram
    program_key: str
    profile: str
    source_hash: str
    normalized_source_hash: str
    functions: tuple[object, ...]
    declarations: tuple[object, ...]
    functions_sha256: str
    whole_program_sha256: str
    interface_sha256: str
    source_uniforms: tuple[tuple[str, str], ...]
    runtime_uniform_abi: tuple[tuple[str, str], ...]
    defines: tuple[tuple[str, str, str], ...]
    output_abi: tuple[str, str, str, str]
    consumed_objects: tuple[object, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source, program.declarations,
                 program.functions, program.resources, program.body_status,
                 program.local_type_names, program.structs, program.uniform_blocks,
                 program.interface_symbols, program.builtin_symbols,
                 program.counted_loop_proof, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names,
                 program.structs, program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk(child)


def _expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values: list[TypedExpression] = []
    def statement(item):
        for expression in item.expressions:
            values.extend(_walk(expression))
        for child in item.children:
            statement(child)
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk(declaration.initializer))
    for function in program.functions:
        for item in function.body:
            statement(item)
    return tuple(values)


def _statements(program: TypedProgram) -> tuple[object, ...]:
    values: list[object] = []

    def statement(item):
        values.append(item)
        for child in item.children:
            statement(child)

    for function in program.functions:
        for item in function.body:
            statement(item)
    return tuple(values)


def _consumed_objects(program: TypedProgram,
                      expressions: tuple[TypedExpression, ...] | None = None) -> tuple[object, ...]:
    values = _expressions(program) if expressions is None else expressions
    statements = _statements(program)
    consumed = tuple(program.declarations) + tuple(program.functions) + statements + values
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("consumed-object ledger is not identity-disjoint")
    return consumed


def _same_identity(actual: tuple[object, ...], expected: tuple[object, ...]) -> bool:
    return (type(actual) is tuple and type(expected) is tuple
            and len(actual) == len(expected) and all(
                left is right for left, right in zip(actual, expected)))


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_moodscape_frontend(program: TypedProgram, source_hash: str | None,
                                    profile: str | None) -> FrontendProof:
    if program.key != KEY or profile != PROFILE:
        raise _fail("exact key/profile required")
    raw, normalized = program.raw_source.encode(), program.source.encode()
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256 or _whole(program) != WHOLE_PROGRAM_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface lock mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value) for item in program.preprocessor_defines)
    if defines != DEFINES:
        raise _fail("compile-time define contract mismatch")
    uniforms = tuple((item.symbol.name, item.type.display()) for item in program.declarations if item.symbol.storage == "uniform")
    if uniforms != SOURCE_UNIFORMS:
        raise _fail("uniform interface census mismatch")
    if (program.resources.uniforms, program.resources.samplers, program.resources.outputs,
            program.resources.uses_texture, program.resources.uses_derivatives) != (tuple(name for name, _ in SOURCE_UNIFORMS), (), (OUTPUT_ABI[0],), False, False):
        raise _fail("resource interface census mismatch")
    if len(program.declarations) != 18 or len(program.functions) != 25:
        raise _fail("declaration/function cardinality mismatch")
    function_identity = tuple((item.id, item.name, item.return_type.display()) for item in program.functions)
    if function_identity != FUNCTION_IDS:
        raise _fail("function identity census mismatch")
    values = _expressions(program)
    node_counts = Counter(item.kind for item in values)
    operator_counts = Counter(item.operator for item in values if item.operator)
    if dict(node_counts) != EXPECTED_NODE_COUNTS or dict(operator_counts) != EXPECTED_OPERATOR_COUNTS:
        raise _fail("expression census mismatch")
    matrix_globals = tuple(item for item in program.declarations if item.type.display() == "mat3")
    if tuple((item.symbol.name, item.type.display(), _span(item), _sha(item)) for item in matrix_globals) != MATRIX_GLOBALS:
        raise _fail("matrix dead-global identity mismatch")
    float_bits = tuple(item for item in values if item.kind == "builtin" and item.callee == "floatBitsToUint")
    if len(float_bits) != 1 or (_span(float_bits[0]), _sha(float_bits[0])) != (FLOAT_BITS_SPAN, FLOAT_BITS_SHA256):
        raise _fail("floatBitsToUint dead-site identity mismatch")
    reachable = tuple(item for item in program.functions if item.id in REACHABLE_FUNCTION_IDS)
    dead = tuple(item for item in program.functions if item.id in DEAD_FUNCTION_IDS)
    if tuple(item.id for item in reachable) != REACHABLE_FUNCTION_IDS or tuple(item.id for item in dead) != DEAD_FUNCTION_IDS:
        raise _fail("function reachability closure mismatch")
    consumed = _consumed_objects(program, values)
    output_abi = OUTPUT_ABI
    return FrontendProof(
        program, KEY, PROFILE, source_hash, hashlib.sha256(normalized).hexdigest(),
        SOURCE_UNIFORMS, RUNTIME_UNIFORM_ABI, tuple(program.functions), reachable,
        dead, matrix_globals, float_bits[0], values, consumed,
        tuple(sorted(node_counts.items())), tuple(sorted(operator_counts.items())),
        DEFINES, output_abi)


def verify_moodscape_frontend(program: TypedProgram, proof: FrontendProof) -> FrontendProof:
    if not isinstance(proof, FrontendProof) or proof.program is not program:
        raise _fail("proof is not bound to selected live program")
    if (proof.program_key != KEY or proof.profile != PROFILE
            or proof.source_hash != RAW_SHA256
            or proof.normalized_source_hash != NORMALIZED_SHA256
            or proof.source_uniforms != SOURCE_UNIFORMS
            or proof.runtime_uniform_abi != RUNTIME_UNIFORM_ABI
            or proof.defines != DEFINES or proof.output_abi != OUTPUT_ABI):
        raise _fail("frontend proof metadata drift")
    expected = authenticate_moodscape_frontend(program, RAW_SHA256, PROFILE)
    if (not _same_identity(proof.functions, expected.functions)
            or not _same_identity(proof.reachable_functions,
                                   expected.reachable_functions)
            or not _same_identity(proof.dead_functions, expected.dead_functions)
            or not _same_identity(proof.matrix_globals, expected.matrix_globals)
            or not _same_identity(proof.expression_nodes,
                                  expected.expression_nodes)
            or not _same_identity(proof.consumed_objects,
                                  expected.consumed_objects)
            or proof.float_bits_node is not expected.float_bits_node
            or proof.node_counts != expected.node_counts
            or proof.operator_counts != expected.operator_counts):
        raise _fail("authenticated closure identity drift")
    return proof


def apply_moodscape_frontend(program: TypedProgram, source_hash: str | None, profile: str | None) -> TypedProgram:
    proof = authenticate_moodscape_frontend(program, source_hash, profile)
    dead_ids = {item.id for item in proof.dead_functions}
    dead_globals = {item.symbol.name for item in proof.matrix_globals}
    if tuple(item.id for item in program.functions if item.id not in dead_ids) != REACHABLE_FUNCTION_IDS:
        raise _fail("authenticated reachable closure cannot be projected")
    if tuple(item.symbol.name for item in program.declarations
             if item.symbol.name not in dead_globals) != PROJECTED_DECLARATION_NAMES:
        raise _fail("authenticated dead-global closure cannot be projected")
    functions = tuple(item for item in program.functions if item.id not in dead_ids)
    functions = attach_counted_loop_proofs(
        clear_counted_loop_proofs(functions), program.key)
    projected = dataclasses.replace(
        program,
        declarations=tuple(item for item in program.declarations
                            if item.symbol.name not in dead_globals),
        functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))
    authenticate_moodscape_projection(projected, source_hash, profile)
    return projected


def authenticate_moodscape_projection(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> ProjectionProof:
    """Authenticate the exact source-bound native projection independently."""
    if program.key != KEY or profile != PROFILE:
        raise _fail("exact key/profile required for projected program")
    raw = program.raw_source.encode()
    normalized = program.source.encode()
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256):
        raise _fail("projected source provenance mismatch")
    if _sha(program.functions) != PROJECTED_FUNCTIONS_SHA256:
        raise _fail("projected function identity or reachability mismatch")
    if _whole(program) != PROJECTED_WHOLE_PROGRAM_SHA256:
        raise _fail("projected whole-program AST lock mismatch")
    if _interface(program) != PROJECTED_INTERFACE_SHA256:
        raise _fail("projected interface lock mismatch")
    if tuple(item.symbol.name for item in program.declarations) != PROJECTED_DECLARATION_NAMES:
        raise _fail("projected declaration closure mismatch")
    if tuple(item.id for item in program.functions) != REACHABLE_FUNCTION_IDS:
        raise _fail("projected reachability closure mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != DEFINES:
        raise _fail("projected compile-time define contract mismatch")
    uniforms = tuple((item.symbol.name, item.type.display())
                     for item in program.declarations
                     if item.symbol.storage == "uniform")
    if uniforms != SOURCE_UNIFORMS:
        raise _fail("projected uniform interface census mismatch")
    if (program.resources.uniforms, program.resources.samplers,
            program.resources.outputs, program.resources.uses_texture,
            program.resources.uses_derivatives) != (
                tuple(name for name, _ in SOURCE_UNIFORMS), (),
                (OUTPUT_ABI[0],), False, False):
        raise _fail("projected resource interface census mismatch")
    if any(item.type.display() == "mat3" for item in program.declarations):
        raise _fail("projected dead matrix global escaped")
    values = _expressions(program)
    if any(item.kind == "builtin" and item.callee == "floatBitsToUint"
           for item in values):
        raise _fail("projected dead floatBitsToUint escaped")
    expected_summary = (0, 0, 0, 0, 0, True)
    summary = program.counted_loop_proof
    if summary is None or (summary.loop_count, summary.unproved_loop_count,
                           summary.max_effective_depth,
                           summary.max_lexical_product, summary.entrypoint_charge,
                           summary.call_graph_acyclic) != expected_summary:
        raise _fail("projected counted-loop proof mismatch")
    consumed = _consumed_objects(program, values)
    return ProjectionProof(
        program, KEY, PROFILE, source_hash,
        hashlib.sha256(normalized).hexdigest(), tuple(program.functions),
        tuple(program.declarations), _sha(program.functions), _whole(program),
        _interface(program), SOURCE_UNIFORMS, RUNTIME_UNIFORM_ABI, DEFINES,
        OUTPUT_ABI, consumed)


def verify_moodscape_projection(
        program: TypedProgram, proof: ProjectionProof) -> ProjectionProof:
    if not isinstance(proof, ProjectionProof) or proof.program is not program:
        raise _fail("projected proof is not bound to selected live program")
    if (proof.program_key != KEY or proof.profile != PROFILE
            or proof.source_hash != RAW_SHA256
            or proof.normalized_source_hash != NORMALIZED_SHA256
            or proof.source_uniforms != SOURCE_UNIFORMS
            or proof.runtime_uniform_abi != RUNTIME_UNIFORM_ABI
            or proof.defines != DEFINES or proof.output_abi != OUTPUT_ABI):
        raise _fail("projected proof metadata drift")
    expected = authenticate_moodscape_projection(
        program, RAW_SHA256, PROFILE)
    if (proof.functions_sha256 != expected.functions_sha256
            or proof.whole_program_sha256 != expected.whole_program_sha256
            or proof.interface_sha256 != expected.interface_sha256
            or not _same_identity(proof.functions, expected.functions)
            or not _same_identity(proof.declarations, expected.declarations)
            or not _same_identity(proof.consumed_objects,
                                  expected.consumed_objects)):
        raise _fail("projected proof identity drift")
    return proof


def replace_expression(program: TypedProgram, target: TypedExpression, replacement: TypedExpression) -> TypedProgram:
    """Return a test-only copy with one expression identity replaced."""
    def replace(value):
        if value is target:
            return replacement
        return dataclasses.replace(value, children=tuple(replace(child) for child in value.children))
    def statement(item):
        return dataclasses.replace(item, expressions=tuple(replace(expr) for expr in item.expressions), children=tuple(statement(child) for child in item.children))
    return dataclasses.replace(program, declarations=tuple(dataclasses.replace(item, initializer=(replace(item.initializer) if item.initializer is not None else None)) for item in program.declarations), functions=tuple(dataclasses.replace(item, body=tuple(statement(statement_item) for statement_item in item.body)) for item in program.functions))


__all__ = ("KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS", "PREPARED_PROFILES", "MOODSCAPE_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES", "DEFINES", "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI", "OUTPUT_ABI", "REACHABLE_FUNCTION_IDS", "DEAD_FUNCTION_IDS", "MATRIX_GLOBALS", "PROJECTED_FUNCTIONS_SHA256", "PROJECTED_WHOLE_PROGRAM_SHA256", "PROJECTED_INTERFACE_SHA256", "FrontendProof", "ProjectionProof", "authenticate_moodscape_frontend", "verify_moodscape_frontend", "authenticate_moodscape_projection", "verify_moodscape_projection", "apply_moodscape_frontend", "replace_expression")
