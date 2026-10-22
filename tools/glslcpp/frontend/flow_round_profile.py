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

from .particle_base_color_profile import authenticate_particle_base_color
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "flow-round-admission-v1"
FLOW_AGENT_KEY = "points/flow:agent"

RAW_SOURCE_BYTES = 7515
RAW_SOURCE_SHA256 = "f8149c037daa3172ccafdb0ffcadbebad3a5fd7d3b9fa1112861518cddfede06"
NORMALIZED_SOURCE_BYTES = 6144
NORMALIZED_SOURCE_SHA256 = "d4dc5e40a1e5454c2285b923dd582b34bf1b25413032f51edcfbe433b43ae9d2"

FUNCTIONS_SHA256 = "3415b919eb0ed7725d7f3cd6f66c6d0218d6d995a460da8a212c371a75d96cd7"
WHOLE_PROGRAM_SHA256 = "0961e0f4e18f00c6d43153a299c33eacf486d88e4a6f8e60e029dceede0f4a70"
INTERFACE_SHA256 = "101c5b05335de2dfa3513c14b9c93c22840f39e48c6b4db83bae72b88153a2b1"

IF_STATEMENT_SHA256 = "5b9b42b924ec8d52f85f799ddaf39b1a25707419a21eabd51e6115b4ab3a4d5e"
EXPR_STATEMENT_SHA256 = "8873180620008c35009e2d18eeb4fade74aaf08f77b5ea7aee4654bdd87c533f"
ASSIGN_EXPRESSION_SHA256 = "4e17313680a63c3f6bf16f3f10bf86618ae06a53dbe40951a1e2fd7fe14f871f"
ROUND_SHA256 = "2dcdb183931f5431f21ac775fcc1a9a9807dc7f80d96e5db682457c3981d9915"
ARGUMENT_SHA256 = "d176567b36be05e89922766f574b366e51196e282db4221276d1ec12759ecd4d"

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

_FUNCTION_INVENTORY = (
    (42, "baseColor", "vec4", 3, 4, "51:1-56:2"),
    (43, "computeRotationBias", "float", 6, 1, "101:1-129:2"),
    (44, "cube_root", "float", 1, 3, "80:1-84:2"),
    (45, "hash", "float", 1, 1, "71:1-73:2"),
    (46, "hash_uint", "uint", 1, 3, "65:1-69:2"),
    (47, "keptBaseColor", "vec4", 1, 1, "58:1-60:2"),
    (48, "main", "void", 0, 38, "131:1-205:2"),
    (49, "normalized_sine", "float", 1, 1, "96:1-98:2"),
    (50, "oklab_l", "float", 1, 7, "86:1-94:2"),
    (51, "selectedDiffuse", "vec4", 1, 3, "32:1-36:2"),
    (52, "spawnColor", "vec4", 1, 3, "42:1-46:2"),
    (53, "srgb_to_linear", "float", 1, 2, "75:1-78:2"),
)

_MAIN_ID = 48
_MAIN_SPAN = "131:1-205:2"
_IF_STATEMENT_INDEX = 26
_IF_STATEMENT_SPAN = "182:5-184:6"
_ASSIGN_SPAN = "183:9-183:39"
_NODE_SPAN = "183:22-183:39"
_NODE_SIGNATURE_ID = -38
_DECL_SYMBOL_ID = 85
_DECL_SYMBOL_NAME = "finalAngle"

_BINDINGS = (
    (1, "resolution", "vec2", "uniform", False),
    (2, "time", "float", "uniform", False),
    (3, "stride", "float", "uniform", False),
    (4, "strideDeviation", "float", "uniform", False),
    (5, "kink", "float", "uniform", False),
    (6, "quantize", "float", "uniform", False),
    (7, "inputWeight", "float", "uniform", False),
    (8, "fieldActive", "float", "uniform", False),
    (9, "behavior", "float", "uniform", False),
    (10, "heightTex", "sampler2D", "uniform", False),
    (11, "inputTex", "sampler2D", "uniform", False),
    (12, "xyzTex", "sampler2D", "uniform", False),
    (13, "velTex", "sampler2D", "uniform", False),
    (14, "rgbaTex", "sampler2D", "uniform", False),
    (15, "outXYZ", "vec4", "output", True),
    (16, "outVel", "vec4", "output", True),
    (17, "outRGBA", "vec4", "output", True),
    (18, "diffuseTex", "sampler2D", "uniform", False),
    (19, "diffuseActive", "float", "uniform", False),
    (21, "baseColorTex", "sampler2D", "uniform", False),
    (22, "outBaseColor", "vec4", "output", True),
    (28, "TAU", "float", "const", False),
    (29, "RIGHT_ANGLE", "float", "const", False),
)

_RESOURCES = (
    ("resolution", "time", "stride", "strideDeviation", "kink", "quantize", "inputWeight", "fieldActive", "behavior", "heightTex", "inputTex", "xyzTex", "velTex", "rgbaTex", "diffuseTex", "diffuseActive", "baseColorTex"),
    ("heightTex", "inputTex", "xyzTex", "velTex", "rgbaTex", "diffuseTex", "baseColorTex"),
    ("outXYZ", "outVel", "outRGBA", "outBaseColor"),
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

    # Census the WHOLE program: an extra round site anywhere else is a hard
    # failure. The two round(vec4) sites of the base-color closure belong to
    # particle-base-color-admission-v1 and are authenticated there.
    try:
        base_color_rounds = authenticate_particle_base_color(program, source_hash).rounds
    except ValueError as error:
        raise _fail(f"base-color closure: {error}") from error
    all_rounds: list[TypedExpression] = []
    for function in functions_sorted:
        for item in function.body:
            for value in _walk_statement(item):
                if (isinstance(value, TypedExpression) and value.kind == "builtin"
                        and value.callee == "round"
                        and not any(value is base for base in base_color_rounds)):
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
