"""Authenticate the CPU9f3 Navier-Stokes hash22 lane-order exception."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "synth/navierStokes:nsSplat"
RAW_BYTES = 3251
RAW_SHA256 = "c3e88bac9c8afa8ed31baec34756db36ad30dd0e73588b35ffc320cba36d3f37"
NORMALIZED_BYTES = 2261
NORMALIZED_SHA256 = "fb963f9eeb25519f147f8e233ed86d393384dadd34acbebcedd460ac0c98098c"
ASSIGNMENT_SHA256 = "d5f27c59022325e594418dc051b6e391fbc77d2c2bc7a86f2079f6e347ce98c7"
CONSTRUCTOR_SHA256 = "50cdd63c9ba38d174b4251a253bfd79e273ddbff5714680a47caf47232267259"
FUNCTIONS_SHA256 = "30566cf880730ba3141768f9aaf88abc150049030fd03db3d9b906c6f38aee56"
DECLARATIONS_SHA256 = "dd486e4625ad7d2826ef6be30dff5de283645c080b1ecea4cf10e6897465dd0c"
RESOURCES_SHA256 = "c581cd6181ba8fee6a5f93fa19f614b0327ee00614cf34d69be818a43a167e2d"
INTERFACE_SHA256 = "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d"
BUILTINS_SHA256 = "8c1812233a23f8cbe095588f75f5687aba5da3f256cca09dd5ffb76bfb5a0c59"
LOCAL_TYPES_SHA256 = "6f12c0d41f9e157bb032ac482dd4bef7cb3d5ccd083426c15cfdb5cd848d5cf2"
DOT_SHA256 = (
    "32da72031c1973a8100043424aa883a90e7dba3f06248368d3b9475883467fa6",
    "3bca36a097741a85c19a35641b588b6a22d09996f11449388ab6313d75106058",
)


@dataclass(frozen=True, slots=True)
class NavierHash22Proof:
    assignment: TypedExpression
    target: TypedExpression
    first: TypedExpression
    second: TypedExpression


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def authenticate_navier_hash22(program: TypedProgram, source_hash: str) -> NavierHash22Proof | None:
    if program.key != KEY:
        return None
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != RAW_SHA256 or len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256):
        raise ValueError("Navier hash22 exact source identity mismatch")
    if program.preprocessor_defines:
        raise ValueError("Navier hash22 defines must be empty")
    if (program.body_status != "analyzed" or _sha(program.functions) != FUNCTIONS_SHA256
            or _sha(program.declarations) != DECLARATIONS_SHA256
            or _sha(program.resources) != RESOURCES_SHA256
            or _sha(program.interface_symbols) != INTERFACE_SHA256
            or _sha(program.builtin_symbols) != BUILTINS_SHA256
            or _sha(program.local_type_names) != LOCAL_TYPES_SHA256
            or program.structs or program.uniform_blocks):
        raise ValueError("Navier hash22 complete typed program identity mismatch")
    functions = [f for f in program.functions if f.id == 14 and f.name == "hash22"]
    if len(functions) != 1:
        raise ValueError("Navier hash22 function identity mismatch")
    matches = []
    for statement in functions[0].body:
        if statement.kind != "expr":
            continue
        for expression in statement.expressions:
            if expression.kind == "assign":
                matches.append(expression)
    if len(matches) != 1:
        raise ValueError("Navier hash22 assignment count mismatch")
    assignment = matches[0]
    if (assignment.operator != "=" or assignment.type.display() != "vec2"
            or assignment.span.start_line != 25 or assignment.span.start_column != 5
            or assignment.span.end_line != 25 or assignment.span.end_column != 69
            or _sha(assignment) != ASSIGNMENT_SHA256
            or len(assignment.children) != 2):
        raise ValueError("Navier hash22 assignment identity mismatch")
    target, constructor = assignment.children
    if (target.kind != "id" or target.symbol_id != 11
            or target.symbol is None or target.symbol.name != "p"
            or target.type.display() != "vec2"
            or constructor.kind != "construct" or constructor.type.display() != "vec2"
            or len(constructor.children) != 2 or _sha(constructor) != CONSTRUCTOR_SHA256):
        raise ValueError("Navier hash22 target/constructor mismatch")
    first, second = constructor.children
    for index, dot in enumerate((first, second)):
        if (dot.kind != "builtin" or dot.callee != "dot"
                or dot.type.display() != "float" or len(dot.children) != 2
                or dot.children[0].kind != "id" or dot.children[0].symbol_id != 11
                or _sha(dot) != DOT_SHA256[index]):
            raise ValueError("Navier hash22 dot source mismatch")
    return NavierHash22Proof(assignment, target, first, second)
