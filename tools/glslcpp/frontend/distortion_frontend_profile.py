"""Prepared, source-bound frontend admission for ``mixer/distortion``.

This is deliberately an admission record, not a typed-slice registration.  The
shader is a useful next frontier but still needs three independent lowering
contracts: sampler parameters, a general derivative ABI, and mutable local
fixed-size arrays.  The profile freezes the exact program and records those
frontier nodes so a later landing cannot silently broaden a shared rule.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram


KEY = "mixer/distortion:distortion"
PROFILE = "distortion-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
DISTORTION_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "distortion_frontend_profile"}),
}
REQUIRED_COMPANION_PROFILES = {KEY: ()}

RAW_BYTES = 8117
RAW_SHA256 = "569fbab57b57baad275a60facfd70b913afe76d69a724b682e821883d40dcae8"
NORMALIZED_BYTES = 6997
NORMALIZED_SHA256 = "5b484e6009b3dd64a8f6c19551dd83f09cab2cf707432ba53cc2ec7ed4bd14db"
FUNCTIONS_SHA256 = "00643dc5cfdd4bea437404400899f77164d4a2583e0e2b1d5653b224c262ff40"
WHOLE_SHA256 = "54a54c4fe1753ffb337e13edfadd3d1152f0c5e10b4f39ffb22f6de8929762e9"
INTERFACE_SHA256 = "f8589bff0d077c5e6e402266b92b9380dfd4e78ea3a4f38dd9fd69a37df63114"

SOURCE_UNIFORMS = (
    ("inputTex", "sampler2D"), ("tex", "sampler2D"),
    ("resolution", "vec2"), ("tileOffset", "vec2"),
    ("fullResolution", "vec2"), ("mode", "int"),
    ("mapSource", "int"), ("intensity", "float"), ("wrap", "int"),
    ("smoothing", "float"), ("aberration", "float"), ("antialias", "bool"),
)
RUNTIME_UNIFORM_ABI = (
    ("resolution", "Vec2"), ("tileOffset", "Vec2"),
    ("fullResolution", "Vec2"), ("mode", "int32"), ("mapSource", "int32"),
    ("intensity", "float"), ("wrap", "int32"), ("smoothing", "float"),
    ("aberration", "float"), ("antialias", "bool"),
)
SAMPLER_RUNTIME_ABI = ("inputTex", "sampler2D", "const Surface&", "tex", "sampler2D", "const Surface&")
SAMPLER_PARAMETER_FUNCTIONS = (
    ("applyDisplacement", ("mapTex", "targetTex"), "91:1-113:2"),
    ("applyReflection", ("mapTex", "targetTex"), "136:1-197:2"),
    ("applyRefraction", ("mapTex", "targetTex"), "116:1-133:2"),
    ("calculateNormal", ("mapTex",), "26:1-72:2"),
)
DERIVATIVE_SPANS = (
    ("dFdx", "102:19-102:36"), ("dFdy", "103:19-103:36"),
    ("dFdx", "159:19-159:32"), ("dFdy", "160:19-160:32"),
    ("dFdx", "122:19-122:36"), ("dFdy", "123:19-123:36"),
)
LOCAL_ARRAY_DECLARATIONS = (
    ("sobel_x", "float[9]", "31:11-31:21"),
    ("sobel_y", "float[9]", "37:11-37:21"),
    ("offsets", "vec2[9]", "42:10-42:20"),
)
SAMPLER_CALLS = (
    ("applyReflection", "calculateNormal", "137:19-137:57"),
    ("applyRefraction", "calculateNormal", "117:19-117:57"),
    ("main", "applyDisplacement", "216:21-216:57"),
    ("main", "applyDisplacement", "218:21-218:57"),
    ("main", "applyRefraction", "223:21-223:66"),
    ("main", "applyRefraction", "225:21-225:66"),
    ("main", "applyReflection", "230:21-230:76"),
    ("main", "applyReflection", "232:21-232:76"),
)
REFLECT_FUNCTION_ID = 32
REFLECT_SIGNATURE_ID = -36
REFLECT_SPAN = "143:26-143:51"
LOOP_PROOF = (1, 0, 1, 9, 9, True)
EXPECTED_EXPR_KINDS = {
    "id": 306, "literal": 121, "binary": 108, "assign": 68,
    "declaration": 54, "builtin": 49, "swizzle": 41, "index": 30,
    "unary": 26, "construct": 16, "call": 15, "post": 1,
    "conditional": 1,
}
EXPECTED_OPERATORS = {
    "*": 45, "+": 45, "=": 40, "-": 30, "+=": 26, "==": 9,
    "/": 3, "*=": 2, "<": 1, "++": 1, ">": 1,
}


class FrontendProof(NamedTuple):
    program_key: str
    sampler_parameter_nodes: tuple[object, ...]
    derivative_nodes: tuple[TypedExpression, ...]
    indexed_nodes: tuple[TypedExpression, ...]
    local_array_declarations: tuple[TypedExpression, ...]
    sampler_calls: tuple[TypedExpression, ...]
    sampler_actual_nodes: tuple[TypedExpression, ...]
    array_stores: tuple[TypedExpression, ...]
    array_reads: tuple[TypedExpression, ...]
    array_loops: tuple[object, ...]
    reflect_node: TypedExpression
    reflect_function_id_value: int
    consumed_objects: tuple[object, ...]

    @property
    def reflect_function_id(self) -> int:
        return self.reflect_function_id_value

    @property
    def reflect_span(self) -> str:
        return _span(self.reflect_node)

    @property
    def reflect_signature_id(self) -> int | None:
        return self.reflect_node.signature_id


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    s = value.span
    return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"


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


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _expressions(program: TypedProgram):
    values = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            values.extend(_walk_expression(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            values.extend(_walk_statement(statement))
    return tuple(values)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_distortion_frontend(program: TypedProgram, source_hash: str | None,
                                     profile: str | None) -> FrontendProof:
    if program.key != KEY:
        raise _fail("selected key is not mixer/distortion:distortion")
    if profile != PROFILE:
        raise _fail("exact prepared profile required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(program.functions) != FUNCTIONS_SHA256
            or _whole(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _fail("source, function, whole-program, or interface lock mismatch")
    if program.body_status != "analyzed" or program.preprocessor_defines != ():
        raise _fail("analyzed body or preprocessor census mismatch")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform-block drift")
    proof = program.counted_loop_proof
    if proof is None or (proof.loop_count, proof.unproved_loop_count,
                         proof.max_effective_depth, proof.max_lexical_product,
                         proof.entrypoint_charge, proof.call_graph_acyclic) != LOOP_PROOF:
        raise _fail("counted-loop census mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives)
            != (tuple(x[0] for x in SOURCE_UNIFORMS), ("inputTex", "tex"),
                ("fragColor",), True, True)):
        raise _fail("resource or binding signature mismatch")
    if len(program.declarations) != 13 or len(program.functions) != 7:
        raise _fail("declaration/function cardinality mismatch")
    expressions = _expressions(program)
    if Counter(item.kind for item in expressions) != Counter(EXPECTED_EXPR_KINDS):
        raise _fail("expression-kind cardinality mismatch")
    if Counter(item.operator for item in expressions if item.operator is not None) != Counter(EXPECTED_OPERATORS):
        raise _fail("operator cardinality mismatch")
    sampler_parameter_nodes = []
    for function in program.functions:
        samplers = tuple(parameter for parameter in function.parameters
                         if parameter.type.display() == "sampler2D")
        if samplers:
            expected = next((item for item in SAMPLER_PARAMETER_FUNCTIONS
                             if item[0] == function.name), None)
            if expected is None or tuple(x.name for x in samplers) != expected[1] or _span(function) != expected[2]:
                raise _fail("sampler-parameter identity census mismatch")
            sampler_parameter_nodes.extend(samplers)
    if tuple((function.name, tuple(x.name for x in function.parameters if x.type.display() == "sampler2D"), _span(function))
             for function in program.functions if any(x.type.display() == "sampler2D" for x in function.parameters)) != SAMPLER_PARAMETER_FUNCTIONS:
        raise _fail("sampler-parameter function census mismatch")
    derivative_nodes = tuple(item for item in expressions
                             if item.kind == "builtin" and item.callee in {"dFdx", "dFdy"})
    if tuple((item.callee, _span(item)) for item in derivative_nodes) != DERIVATIVE_SPANS:
        raise _fail("derivative node identity census mismatch")
    indexed_nodes = tuple(item for item in expressions if item.kind == "index")
    if len(indexed_nodes) != 30:
        raise _fail("fixed-array index census mismatch")
    local_array_declarations = tuple(item for item in expressions if item.kind == "declaration"
                                     and "[" in item.type.display())
    if tuple((item.symbol.name, item.type.display(), _span(item)) for item in local_array_declarations) != LOCAL_ARRAY_DECLARATIONS:
        raise _fail("local-array declaration identity census mismatch")
    sampler_call_records = []
    sampler_calls = []
    for function in program.functions:
        for statement in function.body:
            for item in _walk_statement(statement):
                if (item.kind == "call"
                        and any(child.type.display() == "sampler2D"
                                for child in item.children)):
                    sampler_calls.append(item)
                    sampler_call_records.append((function.name, item.callee, _span(item)))
    sampler_calls = tuple(sampler_calls)
    if tuple(sampler_call_records) != SAMPLER_CALLS:
        raise _fail("sampler-call identity census mismatch")
    sampler_actual_nodes = tuple(child for call in sampler_calls
                                 for child in call.children
                                 if child.type.display() == "sampler2D")
    if len(sampler_actual_nodes) != 14:
        raise _fail("sampler actual census mismatch")
    array_stores = tuple(item for item in indexed_nodes
                         if item.children[1].kind == "literal")
    array_reads = tuple(item for item in indexed_nodes
                        if item.children[1].kind == "id")
    if len(array_stores) != 27 or len(array_reads) != 3:
        raise _fail("fixed-array store/read census mismatch")
    array_loops = tuple(statement for function in program.functions
                        for statement in function.body
                        if statement.kind == "for"
                        and any(any(node is indexed for indexed in indexed_nodes)
                                for node in _walk_statement(statement)))
    if len(array_loops) != 1 or array_loops[0].loop_proof is None:
        raise _fail("fixed-array loop identity census mismatch")
    reflect_records = tuple((function.id, item) for function in program.functions
                            for statement in function.body
                            for item in _walk_statement(statement)
                            if item.kind == "builtin" and item.callee == "reflect")
    if (len(reflect_records) != 1
            or reflect_records[0][0] != REFLECT_FUNCTION_ID
            or reflect_records[0][1].signature_id != REFLECT_SIGNATURE_ID
            or _span(reflect_records[0][1]) != REFLECT_SPAN
            or reflect_records[0][1].type.display() != "vec3"
            or tuple(child.type.display() for child in reflect_records[0][1].children)
            != ("vec3", "vec3")):
        raise _fail("reflect node identity census mismatch")
    reflect_function_id, reflect_node = reflect_records[0]
    consumed = (*sampler_parameter_nodes, *sampler_calls,
                *sampler_actual_nodes, *derivative_nodes, *indexed_nodes,
                *local_array_declarations, *array_loops, reflect_node)
    if len({id(item) for item in consumed}) != len(consumed):
        raise _fail("object identity ledger is not disjoint")
    return FrontendProof(KEY, tuple(sampler_parameter_nodes), derivative_nodes,
                         indexed_nodes, local_array_declarations,
                         sampler_calls, sampler_actual_nodes, array_stores,
                         array_reads, array_loops, reflect_node, reflect_function_id, consumed)


def apply_distortion_frontend(program: TypedProgram, source_hash: str | None,
                              profile: str | None) -> TypedProgram:
    authenticate_distortion_frontend(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS", "PREPARED_PROFILES",
    "DISTORTION_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
    "SOURCE_UNIFORMS", "RUNTIME_UNIFORM_ABI", "SAMPLER_RUNTIME_ABI",
    "SAMPLER_PARAMETER_FUNCTIONS", "DERIVATIVE_SPANS", "LOCAL_ARRAY_DECLARATIONS",
    "SAMPLER_CALLS", "REFLECT_FUNCTION_ID", "REFLECT_SIGNATURE_ID", "REFLECT_SPAN", "LOOP_PROOF",
    "FrontendProof", "authenticate_distortion_frontend",
    "apply_distortion_frontend",
)
