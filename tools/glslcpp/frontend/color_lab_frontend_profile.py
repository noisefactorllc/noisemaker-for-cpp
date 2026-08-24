"""Fail-closed prepared frontend profile for classicNoisedeck/colorLab.

The profile carries the live typed objects and the narrow native ABI/index
requirements consumed by the shared generator and emitter.  Admission remains
bound to the exact pinned ColorLab source and to the identity-disjoint typed
object closure authenticated below.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple

from .typed_ir import TypedExpression, TypedProgram


KEY = "classicNoisedeck/colorLab:colorLab"
PROFILE = "color-lab-frontend-admission-v1"
KEYS = (KEY,)
PROFILES = {KEY: PROFILE}
PREPARED_KEYS: tuple[str, ...] = ()
PREPARED_PROFILES: dict[str, str] = {}
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "color_lab_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_SOURCE_SHA256 = "8a2615887cde9ad2f6adead3a6f69a9f21ac015f762e6add80f23aa293bd530a"
NORMALIZED_SOURCE_SHA256 = "601f1cbbf9a2091e88ec2c6434242cc8226e61a54e10526e465b8b0c0e696e36"
FUNCTIONS_SHA256 = "a25b2238f53b238d649094eb875af667adf2f23540616e303e5c5201388bf19b"
WHOLE_PROGRAM_SHA256 = "9afd0459dcbcb60675cbed02daecca190994a5a2679b482a2fb885d3f97b269f"
INTERFACE_SHA256 = "d9b8011a259bda1a0591512337886c38ec2e359f3bb53644e170b485b975f062"

SOURCE_UNIFORMS = (
    ("inputTex", "sampler2D"), ("resolution", "vec2"),
    ("tileOffset", "vec2"), ("fullResolution", "vec2"),
    ("renderScale", "float"), ("time", "float"), ("levels", "float"),
    ("dither", "int"), ("hueRotation", "float"), ("hueRange", "float"),
    ("invert", "bool"), ("brightness", "float"), ("contrast", "float"),
    ("saturation", "float"), ("colorMode", "int"), ("paletteMode", "int"),
    ("paletteOffset", "vec3"), ("paletteAmp", "vec3"),
    ("paletteFreq", "vec3"), ("palettePhase", "vec3"),
    ("cyclePalette", "int"), ("rotatePalette", "float"),
    ("repeatPalette", "float"),
)
RUNTIME_UNIFORM_ABI = (
    ("resolution", "Vec2"), ("tileOffset", "Vec2"),
    ("fullResolution", "Vec2"), ("renderScale", "float"),
    ("time", "float"), ("levels", "float"), ("dither", "int32"),
    ("hueRotation", "float"), ("hueRange", "float"), ("invert", "bool"),
    ("brightness", "float"), ("contrast", "float"), ("saturation", "float"),
    ("colorMode", "int32"), ("paletteMode", "int32"),
    ("paletteOffset", "Vec3"), ("paletteAmp", "Vec3"),
    ("paletteFreq", "Vec3"), ("palettePhase", "Vec3"),
    ("cyclePalette", "int32"), ("rotatePalette", "float"),
    ("repeatPalette", "float"),
)
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&")
INDEX_RUNTIME_REQUIREMENTS = ("gl_FragCoord", "tileOffset", "fullResolution", "textureSize")
RUNTIME_ABI = {"sampler": SAMPLER_RUNTIME_ABI, "uniforms": RUNTIME_UNIFORM_ABI,
               "indexing": INDEX_RUNTIME_REQUIREMENTS}
FUNCTION_NAMES = (
    "brightnessContrast", "desaturate", "hsv2rgb", "linearToSrgb",
    "linear_srgb_from_oklab", "main", "map", "offsets",
    "oklab_from_linear_srgb", "pal", "pcg", "periodicFunction", "posterize",
    "prng", "random", "rgb2hsv", "saturate", "srgbToLinear",
)
EXPECTED_OPERATOR_COUNTS = {"-": 38, "*": 37, "==": 32, "/": 29, "+": 22,
                            "<": 15, "&&": 8, "<=": 8, "||": 6,
                            "++": 2, "!=": 2, ">>": 1}
EXPECTED_NODE_COUNTS = {"id": 314, "literal": 203, "binary": 176,
                        "swizzle": 90, "assign": 61, "construct": 51,
                        "declaration": 43, "call": 27, "builtin": 26,
                        "unary": 24, "index": 13, "conditional": 7}


class FrontendProof(NamedTuple):
    program: TypedProgram
    program_key: str
    profile: str
    source_hash: str
    normalized_source_hash: str
    source_uniforms: tuple[tuple[str, str], ...]
    runtime_uniform_abi: tuple[tuple[str, str], ...]
    functions: tuple[Any, ...]
    operator_nodes: tuple[TypedExpression, ...]
    index_nodes: tuple[TypedExpression, ...]
    vector_equality_nodes: tuple[TypedExpression, ...]
    consumed_nodes: tuple[object, ...]
    node_counts: tuple[tuple[str, int], ...]
    operator_counts: tuple[tuple[str, int], ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


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


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(statement):
    for expression in statement.expressions:
        yield from _walk_expression(expression)
    for child in statement.children:
        yield from _walk_statement(child)


def _all_expression_nodes(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _consumed(program: TypedProgram):
    expressions = _all_expression_nodes(program)
    # Declaration and function objects are deliberately carried alongside the
    # recursive expression closure.  Identity disjointness prevents a later
    # emitter from replacing a live node with a structurally similar foreign one.
    values = tuple(program.declarations) + tuple(program.functions) + expressions
    if len({id(value) for value in values}) != len(values):
        raise ValueError("ColorLab consumed-object ledger is not identity-disjoint")
    return expressions, values


def load_live_program(root: Path):
    from tools.glslcpp import check_corpus, generate_typed_slice
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    corpus = check_corpus._corpus_root(root)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"] if item["program_key"] == KEY)
    raw = (corpus / entry["source"]).read_text()
    program = analyze_program(parse_program(raw, KEY, generate_typed_slice._defaults(root, KEY)), KEY)
    return entry["raw_sha256"], program


def _proof(program: TypedProgram, source_hash: str) -> FrontendProof:
    expressions, consumed = _consumed(program)
    operators = tuple(node for node in expressions if node.kind in ("binary", "unary"))
    indexes = tuple(node for node in expressions if node.kind == "index")
    vector_equalities = tuple(
        node for node in expressions
        if (node.kind == "binary" and node.operator == "=="
            and len(node.children) == 2
            and tuple(child.type.display() for child in node.children)
            == ("vec2", "vec2"))
    )
    return FrontendProof(program, KEY, PROFILE, source_hash,
                         hashlib.sha256(program.source.encode()).hexdigest(),
                         SOURCE_UNIFORMS, RUNTIME_UNIFORM_ABI,
                         tuple(program.functions), operators, indexes,
                         vector_equalities, consumed,
                         tuple(sorted(Counter(node.kind for node in expressions).items())),
                         tuple(sorted(Counter(node.operator for node in operators).items())))


def authenticate_color_lab_frontend(program: TypedProgram, source_hash: str | None,
                                    profile: str) -> FrontendProof:
    if profile != PROFILE or program.key != KEY:
        raise ValueError("ColorLab frontend profile/key mismatch")
    raw_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode()).hexdigest()
    if source_hash != RAW_SOURCE_SHA256 or raw_hash != RAW_SOURCE_SHA256 or normalized_hash != NORMALIZED_SOURCE_SHA256:
        raise ValueError("ColorLab source provenance mismatch")
    if program.preprocessor_defines or _sha(program.functions) != FUNCTIONS_SHA256:
        raise ValueError("ColorLab function/source fingerprint drift")
    if _whole(program) != WHOLE_PROGRAM_SHA256 or _interface(program) != INTERFACE_SHA256:
        raise ValueError("ColorLab AST/interface fingerprint drift")
    uniforms = tuple((item.symbol.name, item.type.display()) for item in program.declarations
                     if item.symbol.storage == "uniform")
    if uniforms != SOURCE_UNIFORMS:
        raise ValueError("ColorLab uniform interface drift")
    if len(program.declarations) != 28 or len(program.functions) != 18:
        raise ValueError("ColorLab declaration/function cardinality drift")
    if tuple(function.name for function in program.functions) != FUNCTION_NAMES:
        raise ValueError("ColorLab function identity drift")
    proof = _proof(program, source_hash)
    if dict(proof.node_counts) != EXPECTED_NODE_COUNTS:
        raise ValueError("ColorLab node census drift")
    if dict(proof.operator_counts) != EXPECTED_OPERATOR_COUNTS:
        raise ValueError("ColorLab operator census drift")
    if len(proof.index_nodes) != 13:
        raise ValueError("ColorLab index census drift")
    if len(proof.vector_equality_nodes) != 6:
        raise ValueError("ColorLab vector-equality census drift")
    return proof


def verify_color_lab_frontend(program: TypedProgram, proof: FrontendProof) -> FrontendProof:
    if not isinstance(proof, FrontendProof) or proof.program is not program:
        raise ValueError("ColorLab proof is not bound to selected live program")
    expected = authenticate_color_lab_frontend(program, proof.source_hash, proof.profile)
    if any(left is not right for left, right in zip(proof.functions, expected.functions)):
        raise ValueError("ColorLab function identity drift")
    if len(proof.consumed_nodes) != len(expected.consumed_nodes) or any(
            left is not right for left, right in zip(proof.consumed_nodes, expected.consumed_nodes)):
        raise ValueError("ColorLab consumed-object identity drift")
    if proof.operator_nodes != expected.operator_nodes:
        raise ValueError("ColorLab operator closure drift")
    if (len(proof.index_nodes) != len(expected.index_nodes)
            or any(left is not right for left, right in zip(
                proof.index_nodes, expected.index_nodes))):
        raise ValueError("ColorLab index closure identity drift")
    if (len(proof.vector_equality_nodes) != len(expected.vector_equality_nodes)
            or any(left is not right for left, right in zip(
                proof.vector_equality_nodes,
                expected.vector_equality_nodes))):
        raise ValueError("ColorLab vector-equality closure identity drift")
    return proof


def apply_color_lab_frontend(program: TypedProgram, source_hash: str | None,
                             profile: str) -> TypedProgram:
    authenticate_color_lab_frontend(program, source_hash, profile)
    return program


def allowed_row_fields(key: str):
    return ALLOWED_ROW_FIELDS.get(key, frozenset())


def replace_expression(program: TypedProgram, target: TypedExpression,
                       replacement: TypedExpression) -> TypedProgram:
    """Return a test-only copy with one expression identity replaced."""
    def replace(value):
        if value is target:
            return replacement
        return dataclasses.replace(value, children=tuple(replace(child) for child in value.children))
    def replace_statement(statement):
        return dataclasses.replace(statement,
            expressions=tuple(replace(expr) for expr in statement.expressions),
            children=tuple(replace_statement(child) for child in statement.children))
    declarations = tuple(dataclasses.replace(item, initializer=(replace(item.initializer)
                         if item.initializer is not None else None)) for item in program.declarations)
    functions = tuple(dataclasses.replace(fn, body=tuple(
        dataclasses.replace(stmt,
            expressions=tuple(replace(expr) for expr in stmt.expressions),
            children=tuple(replace_statement(child) for child in stmt.children))
        for stmt in fn.body)) for fn in program.functions)
    return dataclasses.replace(program, declarations=declarations, functions=functions)


__all__ = [
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
    "PREPARED_PROFILES", "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
    "FrontendProof", "authenticate_color_lab_frontend",
    "verify_color_lab_frontend", "apply_color_lab_frontend",
    "allowed_row_fields",
]
