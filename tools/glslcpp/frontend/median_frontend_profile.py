"""Fail-closed prepared frontend admission for ``filter/median:median``.

Median is intentionally kept out of the shared typed-slice registry. The
source is analyzable for the three supported compile-time radii, but the
current emitter rejects the counted-for proof before it can emit this effect.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import Counter
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram

KEY = "filter/median:median"
PROFILE = "median-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "median_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}
RADIUS_DEFINES = (1, 2, 3)
DEFAULT_RADIUS = 2
RAW_SOURCE_SHA256 = "95e869c02fe2645f4a1b5af5a7446b3f2bacb888f2c965bc272ba56b10666e5d"
NORMALIZED_SOURCE_SHA256 = {1: "fa655bb858bf0f03f84ce065bf6a02aadef5ff482065a6e2f408f1a7a558a39e", 2: "c79b9626828e47335a08dd0057256420b7400bdde50badd85421eb2ae131fd02", 3: "4d84a477b2a53afad21f407b92539d35725e04a2d6a70d2c3f692ba6b6eb0a35"}
WHOLE_PROGRAM_SHA256 = {1: "afe8be05727ecc65053e86014bd4e8fa4b991282575cdf29ed156006878a4251", 2: "a2dda054aa7485307149069181c02c10970a09fe731d679162e95f91445e7e49", 3: "8ad185e431d817133168c61106d284a35e108a2e9da80d1427138aa09091142a"}
INTERFACE_SHA256 = {1: "3199fd9c28b84cefdd461a715417c0ca13b8fc94b4784f138a1f5d1afd087768", 2: "5ed1d50ecb274a59849e21e4549c2adba585ad5c930772577a9af95190edcfc9", 3: "b86248644c423a68e4c6730d867582076c1c7b92b15d15c75bd97ba8681a3203"}
SOURCE_UNIFORMS = (("inputTex", "sampler2D"), ("threshold", "float"))
RUNTIME_UNIFORM_ABI = (("threshold", "float"), ("RADIUS", "int32"))
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&")
INDEX_RUNTIME_REQUIREMENTS = ("gl_FragCoord", "textureSize", "texelFetch", "bottom-left")
CURRENT_EMITTER_BLOCKER = "47:5: unsupported counted-for program proof"
FUNCTION_NAMES = ("lessRecord", "main", "packRecordBlue", "packRecordMajor", "readRecord", "unpackRecordRgb")
EXPECTED_NODE_COUNTS = {"id": 123, "binary": 32, "declaration": 30, "literal": 30, "swizzle": 20, "index": 18, "builtin": 12, "assign": 11, "construct": 10, "post": 7, "call": 6, "unary": 2, "conditional": 1}
EXPECTED_OPERATOR_COUNTS = {"<": 6, "<=": 5, "++": 5, "-": 5, "!=": 2, "==": 2, "/": 2, "--": 2, "&": 2, "|": 2, "<<": 2, ">>": 2, "&&": 1, "||": 1, ">=": 1, "+": 1}
UNPROVED_WHILE_SPANS = ("63:5-84:6", "68:9-81:10", "69:13-69:117", "70:13-70:120")
UNPROVED_WHILE_SHA256 = ("7ac9d2c157c6b3ae6a565546ec2f36133c2401e1e4460c5b7014477869e16773", "997a88b1d4ddece95a099c616c9f3bf03b2dc311bc2e4a96f0eefa285221ba31", "d621264d7448f7d6c0f4781d801191b6e15352c685ad8af1f01152da828a2fa2", "75cb83f7adba6a597e9d5c0ef15af13b2cc342b9f7bda562022bd8b4d0ade78d")


class FrontendProof(NamedTuple):
    program: TypedProgram
    program_key: str
    profile: str
    radius: int
    source_hash: str
    normalized_source_hash: str
    source_uniforms: tuple[tuple[str, str], ...]
    runtime_uniform_abi: tuple[tuple[str, str], ...]
    functions: tuple[object, ...]
    expression_nodes: tuple[TypedExpression, ...]
    consumed_nodes: tuple[object, ...]
    node_counts: tuple[tuple[str, int], ...]
    operator_counts: tuple[tuple[str, int], ...]
    unproved_while_spans: tuple[str, ...]
    unproved_while_sha256: tuple[str, ...]
    array_declarations: tuple[TypedExpression, ...]
    array_indexes: tuple[TypedExpression, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _walk(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk(child)


def _expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values = []
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


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source, program.declarations, program.functions, program.resources, program.body_status, program.local_type_names, program.structs, program.uniform_blocks, program.interface_symbols, program.builtin_symbols, program.counted_loop_proof, program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources, program.local_type_names, program.structs, program.uniform_blocks, program.interface_symbols, program.builtin_symbols, program.preprocessor_defines))


def _span(value) -> str:
    item = value.span
    return f"{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}"


def _while_nodes(program: TypedProgram):
    values = []
    def statement(item):
        if item.kind == "while":
            values.append(item)
        for child in item.children:
            statement(child)
    for function in program.functions:
        for item in function.body:
            statement(item)
    return tuple(values)


def load_live_program(root, radius: int = 2):
    from tools.glslcpp import check_corpus
    from tools.glslcpp.frontend import parse_program
    from tools.glslcpp.frontend.semantic import analyze_program
    if radius not in RADIUS_DEFINES:
        raise ValueError("median radius must be 1, 2, or 3")
    corpus = check_corpus._corpus_root(root)
    manifest = json.loads((corpus / "manifest.json").read_text())
    entry = next(item for item in manifest["programs"] if item["program_key"] == KEY)
    raw = (corpus / entry["source"]).read_text()
    return entry["raw_sha256"], analyze_program(parse_program(raw, KEY, {"RADIUS": radius}), KEY)


def authenticate_median_frontend(program: TypedProgram, source_hash: str | None, profile: str, radius: int = 2) -> FrontendProof:
    if program.key != KEY or profile != PROFILE or radius not in RADIUS_DEFINES:
        raise ValueError("median frontend profile/key/radius mismatch")
    raw_hash = hashlib.sha256(program.raw_source.encode()).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode()).hexdigest()
    if source_hash != RAW_SOURCE_SHA256 or raw_hash != RAW_SOURCE_SHA256 or normalized_hash != NORMALIZED_SOURCE_SHA256[radius]:
        raise ValueError("median source provenance mismatch")
    if len(program.preprocessor_defines) != 1 or program.preprocessor_defines[0].name != "RADIUS" or program.preprocessor_defines[0].canonical_value != str(radius):
        raise ValueError("median RADIUS define drift")
    if _whole(program) != WHOLE_PROGRAM_SHA256[radius] or _interface(program) != INTERFACE_SHA256[radius]:
        raise ValueError("median AST/interface fingerprint drift")
    uniforms = tuple((d.symbol.name, d.type.display()) for d in program.declarations if d.symbol.storage == "uniform")
    if uniforms != SOURCE_UNIFORMS or len(program.declarations) != 3 or len(program.functions) != 6:
        raise ValueError("median interface cardinality drift")
    if tuple(fn.name for fn in program.functions) != FUNCTION_NAMES:
        raise ValueError("median function identity drift")
    values = _expressions(program)
    consumed = tuple(program.declarations) + tuple(program.functions) + values
    if len({id(value) for value in consumed}) != len(consumed):
        raise ValueError("median consumed-object ledger is not identity-disjoint")
    operators = tuple(node for node in values if node.kind in ("binary", "unary", "post"))
    while_nodes = _while_nodes(program)
    while_spans = tuple(_span(item) for item in while_nodes)
    while_hashes = tuple(_sha(item) for item in while_nodes)
    if radius == DEFAULT_RADIUS and (while_spans != UNPROVED_WHILE_SPANS or while_hashes != UNPROVED_WHILE_SHA256):
        raise ValueError("median unproved-while identity drift")
    array_declarations = tuple(item for item in values if item.kind == "declaration" and item.type.display() in {"uvec2[25]", "uint[25]"})
    array_indexes = tuple(item for item in values if item.kind == "index" and item.children and item.children[0].kind == "id" and item.children[0].symbol_id in {23, 24})
    if radius == DEFAULT_RADIUS and (tuple(item.symbol_id for item in array_declarations) != (23, 24) or len(array_indexes) != 18):
        raise ValueError("median fixed-array identity drift")
    proof = FrontendProof(program, KEY, PROFILE, radius, source_hash, normalized_hash, SOURCE_UNIFORMS, RUNTIME_UNIFORM_ABI, tuple(program.functions), values, consumed, tuple(sorted(Counter(n.kind for n in values).items())), tuple(sorted(Counter(n.operator for n in operators).items())), while_spans, while_hashes, array_declarations, array_indexes)
    if dict(proof.node_counts) != EXPECTED_NODE_COUNTS or dict(proof.operator_counts) != EXPECTED_OPERATOR_COUNTS:
        raise ValueError("median AST census drift")
    return proof


def verify_median_frontend(program: TypedProgram, proof: FrontendProof) -> FrontendProof:
    if not isinstance(proof, FrontendProof) or proof.program is not program:
        raise ValueError("median proof is not bound to selected live program")
    expected = authenticate_median_frontend(program, proof.source_hash, proof.profile, proof.radius)
    if any(a is not b for a, b in zip(proof.consumed_nodes, expected.consumed_nodes)):
        raise ValueError("median consumed-object identity drift")
    if proof.expression_nodes != expected.expression_nodes:
        raise ValueError("median expression closure drift")
    if proof.unproved_while_spans != expected.unproved_while_spans or proof.unproved_while_sha256 != expected.unproved_while_sha256:
        raise ValueError("median unproved-while identity drift")
    if any(a is not b for a, b in zip(proof.array_declarations, expected.array_declarations)) or any(a is not b for a, b in zip(proof.array_indexes, expected.array_indexes)):
        raise ValueError("median fixed-array identity drift")
    return proof


def replace_expression(program: TypedProgram, target: TypedExpression, replacement: TypedExpression) -> TypedProgram:
    def replace(value):
        if value is target:
            return replacement
        return dataclasses.replace(value, children=tuple(replace(child) for child in value.children))
    def statement(item):
        return dataclasses.replace(item, expressions=tuple(replace(x) for x in item.expressions), children=tuple(statement(x) for x in item.children))
    return dataclasses.replace(program, declarations=tuple(dataclasses.replace(x, initializer=(replace(x.initializer) if x.initializer else None)) for x in program.declarations), functions=tuple(dataclasses.replace(x, body=tuple(statement(s) for s in x.body)) for x in program.functions))
