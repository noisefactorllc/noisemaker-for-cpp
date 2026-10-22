"""Exact diffuse-color output stores of the particle behaviors' agent programs.

Each authenticated agent program stores its diffuse color with one GLSL
statement of this form:

    outRGBA = diffuseActive > 0.5 ? selectedDiffuse(...) : base;

The CPU authority's transpiled JavaScript lowers that statement as
``diffuseActive > 0.5 ? selectedDiffuse(...) : base.reduce(..., outRGBA)``.
Only the false arm stores into ``outRGBA``. When a diffuse map is bound, the
true arm is evaluated, its value is discarded, and ``outRGBA`` keeps the value
that the same kernel binding stored for an earlier pixel (initially zero).
This module admits exactly those statements, by object identity, keyed by each
program's exact source digest. The emitter lowers each one with the same
false-arm-only store. Every other assignment keeps its GLSL semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "particle-diffuse-output-keep-v1"

# program key: (raw source sha256, assignment spans in program-walk order)
_PINS = {
    "points/attractor:agent": ("cfe98602348063ab7cb3aa0c642f70de000c2352a40368e8fc9eddcf47447e82",
        ("183:9-183:80", "213:5-213:77")),
    "points/buddhabrot:agent": ("efecb24d045790bee064e160a1b09a7f411589e76fee87591261bba0cc44870f",
        ("159:9-159:140", "204:5-204:89")),
    "points/dla:agent": ("cae55bc611428b4e6938a79814898c8bda2a3af19b303502ec5b77f5479b88f9",
        ("206:9-206:74", "212:9-212:74", "218:9-218:74")),
    "points/flock:agent": ("3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        ("342:5-342:70",)),
    "points/flow:agent": ("f8149c037daa3172ccafdb0ffcadbebad3a5fd7d3b9fa1112861518cddfede06",
        ("203:5-203:70",)),
    "points/hydraulic:agent": ("02bff511e46a3e32cfd7d2aa0c8d49d24a9590441c8900379241ba210a06a0fc",
        ("237:5-237:70",)),
    "points/lenia:agentField": ("b5f996e1d84485c4726801aed539690cd242529a81d2101f98cb8ef2ccc56d87",
        ("151:5-151:70",)),
    "points/physarum:agent": ("a9b21cee808cf70e7d29d05f27bdf9bd598ef1f5ac8dae492e6541cf21456e2f",
        ("180:5-180:70",)),
    "points/physical:agent": ("06f3afef8efeaba67f1babf129ee107b06e860ec8458e270ce404fc770b46615",
        ("176:9-176:74",)),
}

PARTICLE_DIFFUSE_OUTPUT_KEYS = frozenset(_PINS)


@dataclass(frozen=True, slots=True)
class ParticleDiffuseOutputProof:
    assignments: tuple[TypedExpression, ...]


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _display(value: TypedExpression | None) -> str | None:
    return None if value is None or value.type is None else value.type.display()


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statements(statements: tuple[TypedStatement, ...]):
    for statement in statements:
        yield statement
        yield from _walk_statements(statement.children)


def authenticate_particle_diffuse_outputs(
        program: TypedProgram, source_hash: str | None) -> ParticleDiffuseOutputProof:
    """Authenticate every diffuse output store and return the exact assignments."""
    pin = _PINS.get(program.key)
    if pin is None:
        raise _fail(f"program key {program.key} is not an admitted carrier")
    expected_hash, expected_spans = pin
    if (source_hash != expected_hash
            or hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest() != expected_hash
            or program.preprocessor_defines or program.body_status != "analyzed"):
        raise _fail(f"{program.key} source identity mismatch")

    # Census the WHOLE program: every assignment whose value is a conditional
    # is one of the frozen stores, and no other expression is an assignment
    # with a conditional value.
    located: list[TypedExpression] = []
    for function in program.functions:
        for statement in _walk_statements(function.body):
            for expression in statement.expressions:
                for item in _walk_expression(expression):
                    if (item.kind == "assign" and len(item.children) == 2
                            and item.children[1].kind == "conditional"):
                        if statement.kind != "expr" or statement.expressions != (item,):
                            raise _fail(f"{program.key} conditional assignment outside an expression statement")
                        located.append(item)
    if tuple(_span(item) for item in located) != expected_spans:
        raise _fail(f"{program.key} diffuse output store identity mismatch")
    for item in located:
        target, conditional = item.children
        if (item.operator != "=" or target.kind != "id" or target.symbol is None
                or target.symbol.name != "outRGBA" or target.symbol.storage != "output"
                or _display(target) != "vec4" or _display(conditional) != "vec4"
                or len(conditional.children) != 3):
            raise _fail(f"{program.key} malformed diffuse output store")
        condition = conditional.children[0]
        if (condition.kind != "binary" or condition.operator != ">"
                or len(condition.children) != 2
                or condition.children[0].kind != "id"
                or condition.children[0].symbol is None
                or condition.children[0].symbol.name != "diffuseActive"
                or condition.children[0].symbol.storage != "uniform"
                or condition.children[1].kind != "literal"
                or condition.children[1].literal_value != 0.5):
            raise _fail(f"{program.key} diffuse output store condition mismatch")
    return ParticleDiffuseOutputProof(tuple(located))


__all__ = ("PROFILE", "PARTICLE_DIFFUSE_OUTPUT_KEYS", "ParticleDiffuseOutputProof",
           "authenticate_particle_diffuse_outputs")
