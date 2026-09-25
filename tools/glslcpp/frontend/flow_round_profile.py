"""Closed identity profile for Flow Agent's one round site.

Carrier for points/flow:agent (Flow agent particle simulation kernel).
Admits the single standalone round(float) -> float site at lines 145-147:
    if (quantize > 0.5) {
        finalAngle = round(finalAngle);
    }
Lowered to noisemaker::f32(glsl::round(x)) via Math.round semantics.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "flow-round-admission-v1"
FLOW_AGENT_KEY = "points/flow:agent"

RAW_SOURCE_BYTES = 5848
RAW_SOURCE_SHA256 = "0584139db3b2e14af99788458a48094a0d650a03ae540a0468309bf2f097bb6b"
NORMALIZED_SOURCE_BYTES = 4806
NORMALIZED_SOURCE_SHA256 = "f65a6c7d49e84efc852b351c06b0807f1226aba3c79b6d3e1e3f6ca4f08eb1d4"

FUNCTIONS_SHA256 = "aff889250f44b8b6aa16ecf03c92cf20cfdc45ebd0cc6cf437672b2fca7d55fe"
WHOLE_PROGRAM_SHA256 = "4630e9ddb459f7224ec1636c7cae3cecdc84159bd5e436a40fb2fbdb7c0a3af9"
INTERFACE_SHA256 = "1748203f7868b9ee23ea5891b547e21dcc083b83bf45913e332bbae14affac3b"

IF_STATEMENT_SHA256 = "3131959ec09cb0369d2a39ee2d8316b6244fe9abe65e7f5bb247cafe75298dd4"
EXPR_STATEMENT_SHA256 = "cb1443c929bb0ba3bbcaf7984a5b75d683bd08ad87fd738d2d3c5db987926474"
ASSIGN_EXPRESSION_SHA256 = "046d3ab69eeeb30d2c07467f6fa5e4ec18c55cf3fd3e5637b3c1555dc2720075"
ROUND_SHA256 = "97ad728ea666ea42eb08d668b972fe1938a9a1ec9d3e94d2331cbd453e3578c7"
ARGUMENT_SHA256 = "cb72ad451d1969330c95164685c4a4c1112911c5673bec87d2bded32827dde32"

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

_FUNCTION_INVENTORY = (
    (30, "computeRotationBias", "float", 6, 1, "66:1-94:2"),
    (31, "cube_root", "float", 1, 3, "45:1-49:2"),
    (32, "hash", "float", 1, 1, "36:1-38:2"),
    (33, "hash_uint", "uint", 1, 3, "30:1-34:2"),
    (34, "main", "void", 0, 36, "96:1-167:2"),
    (35, "normalized_sine", "float", 1, 1, "61:1-63:2"),
    (36, "oklab_l", "float", 1, 7, "51:1-59:2"),
    (37, "srgb_to_linear", "float", 1, 2, "40:1-43:2"),
)

_MAIN_ID = 34
_MAIN_SPAN = "96:1-167:2"
_IF_STATEMENT_INDEX = 25
_IF_STATEMENT_SPAN = "145:5-147:6"
_ASSIGN_SPAN = "146:9-146:39"
_NODE_SPAN = "146:22-146:39"
_NODE_SIGNATURE_ID = -38
_DECL_SYMBOL_ID = 66
_DECL_SYMBOL_NAME = "finalAngle"

_BINDINGS = (
    (1, "resolution", "vec2", "uniform", False),
    (2, "time", "float", "uniform", False),
    (3, "stride", "float", "uniform", False),
    (4, "strideDeviation", "float", "uniform", False),
    (5, "kink", "float", "uniform", False),
    (6, "quantize", "float", "uniform", False),
    (7, "inputWeight", "float", "uniform", False),
    (8, "behavior", "float", "uniform", False),
    (9, "inputTex", "sampler2D", "uniform", False),
    (10, "xyzTex", "sampler2D", "uniform", False),
    (11, "velTex", "sampler2D", "uniform", False),
    (12, "rgbaTex", "sampler2D", "uniform", False),
    (13, "outXYZ", "vec4", "output", True),
    (14, "outVel", "vec4", "output", True),
    (15, "outRGBA", "vec4", "output", True),
    (16, "TAU", "float", "const", False),
    (17, "RIGHT_ANGLE", "float", "const", False),
)

_RESOURCES = (
    ("resolution", "time", "stride", "strideDeviation", "kink", "quantize",
     "inputWeight", "behavior", "inputTex", "xyzTex", "velTex", "rgbaTex"),
    ("inputTex", "xyzTex", "velTex", "rgbaTex"),
    ("outXYZ", "outVel", "outRGBA"),
    True,
    False,
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _walk_statement(statement: TypedStatement):
    yield statement
    for expression in statement.expressions:
        yield from _walk_expression(expression)
    for child in statement.children:
        yield from _walk_statement(child)


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_flow_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedExpression:
    """Return the exact authenticated ``round`` node after full authentication."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != FLOW_AGENT_KEY or source_hash != RAW_SOURCE_SHA256
            or len(raw) != RAW_SOURCE_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SOURCE_SHA256
            or len(normalized) != NORMALIZED_SOURCE_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SOURCE_SHA256
            or program.preprocessor_defines or program.body_status != "analyzed"):
        raise _fail("source, key, define, or body profile mismatch")
    if (_sha(program.functions) != FUNCTIONS_SHA256
            or _whole_program_fingerprint(program) != WHOLE_PROGRAM_SHA256
            or _interface_fingerprint(program) != INTERFACE_SHA256):
        raise _fail("function, whole-program, or interface profile mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    functions_sorted = tuple(sorted(program.functions, key=lambda item: item.id))
    if tuple((item.id, item.name, item.return_type.display(), len(item.parameters),
              len(item.body), _span(item)) for item in functions_sorted) != _FUNCTION_INVENTORY:
        raise _fail("function inventory mismatch")
    main = next((item for item in functions_sorted if item.id == _MAIN_ID), None)
    if main is None or main.name != "main" or _span(main) != _MAIN_SPAN:
        raise _fail("main identity mismatch")

    if_statement = main.body[_IF_STATEMENT_INDEX]
    if (if_statement.kind != "if" or len(if_statement.children) != 1
            or _span(if_statement) != _IF_STATEMENT_SPAN
            or _sha(if_statement) != IF_STATEMENT_SHA256):
        raise _fail("if statement profile mismatch")
    block = if_statement.children[0]
    if block.kind != "block" or len(block.children) != 1:
        raise _fail("if body block profile mismatch")
    expr_statement = block.children[0]
    if (expr_statement.kind != "expr" or len(expr_statement.expressions) != 1
            or _sha(expr_statement) != EXPR_STATEMENT_SHA256):
        raise _fail("expression statement profile mismatch")

    assignment = expr_statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2
            or _span(assignment) != _ASSIGN_SPAN
            or _sha(assignment) != ASSIGN_EXPRESSION_SHA256):
        raise _fail("assignment profile mismatch")

    lhs = assignment.children[0]
    if (lhs.kind != "id" or lhs.symbol_id != _DECL_SYMBOL_ID
            or lhs.symbol is None or lhs.symbol.name != _DECL_SYMBOL_NAME
            or lhs.type.display() != "float"):
        raise _fail("assignment lhs profile mismatch")

    round_value = assignment.children[1]
    if (round_value.kind != "builtin" or round_value.callee != "round"
            or round_value.signature_id != _NODE_SIGNATURE_ID
            or round_value.type.display() != "float"
            or round_value.category != "rvalue"
            or len(round_value.children) != 1
            or round_value.children[0].type.display() != "float"
            or _span(round_value) != _NODE_SPAN
            or _sha(round_value) != ROUND_SHA256
            or _sha(round_value.children[0]) != ARGUMENT_SHA256):
        raise _fail("round site or argument profile mismatch")

    # Census the WHOLE program: an extra round site anywhere else is a hard failure
    all_rounds: list[TypedExpression] = []
    for function in functions_sorted:
        for item in function.body:
            for value in _walk_statement(item):
                if (isinstance(value, TypedExpression) and value.kind == "builtin"
                        and value.callee == "round"):
                    all_rounds.append(value)
    if len(all_rounds) != 1 or all_rounds[0] is not round_value:
        raise _fail("expected exactly one owned round site")

    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    if bindings != _BINDINGS:
        raise _fail("binding profile mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES):
        raise _fail("resource profile mismatch")

    return round_value


def apply_flow_round_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate and return the same immutable program object."""
    authenticate_flow_round_admission(program, source_hash, profile)
    return program
