#!/usr/bin/env python3
"""Frozen typed-frontend proof for ``classicNoisedeck/glitch:glitch``.

This is oracle evidence, not admission code. It authenticates the exact live
mat4 closure: three constructors, nested left-associated ``(T*Q)*S``, the
downstream ``tv*A`` vector product, and the bicubic return route.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402
from tools.glslcpp.frontend.typed_ir import (  # noqa: E402
    TypedExpression,
    TypedProgram,
    TypedStatement,
)


REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
KEY = "classicNoisedeck/glitch:glitch"
PROFILE = "glitch-mat4-chain-v1"
SOURCE = (ROOT / "tools/glslcpp/corpus" / REVISION
          / "sources/classicNoisedeck/glitch/glitch.glsl")
RAW_SHA256 = "13d6350eb21cfb5a7c9f0d0a8fffe8e7495068ca2e082d1520ef14ca5b34c134"
NORMALIZED_SHA256 = "ca3932d19ca01fcc11d1336f4026b5f21622a27eb1e2e7b3d75858b56473a224"
RAW_IR_SHA256 = "326e44df7aaf2767dbc5848c0dde543f1b45863ecabb8b925e580704327e91ee"
FUNCTIONS_SHA256 = "0ce0022ffb116a4ea03a82e32c372b52b41f67e42b11d4aca2b067da2fa22e61"
DECLARATIONS_SHA256 = "3501eee0dc5daa002d085d9a272fb8f39dd387d311f77f09f87f47601d2c50d4"
WHOLE_SHA256 = "c5cb35d06830b48a1f0cba9b5f493c1aac9ec6fb3eeba2ca15ec6ca6449e1178"
INTERFACE_SHA256 = "5c67224f53f6b88d52e64fd8e888478c6e43ccceeb2ddd8f68d06e8418dc0b92"
EXPECTED_FUNCTIONS = (
    "bicubic", "f", "glitch", "main", "map", "offsets", "pcg",
    "periodicFunction", "prng", "scanlines", "snow",
)
EXPECTED_CONSTRUCT_SPANS = (
    "76:14-76:114", "77:14-77:86", "78:14-78:86",
)
EXPECTED_MATRIX_PRODUCT_SPANS = ("79:14-79:23", "79:14-79:19")
EXPECTED_VECTOR_PRODUCT_SPANS = ("84:16-84:22",)
CAPTURED_PRE_ADMISSION_FRONTIER = {
    "typed_slice_programs": 175,
    "current": {
        "validator": (
            "classicNoisedeck/glitch:glitch:76:10: unsupported typed type mat4"),
        "emitter": (
            "classicNoisedeck/glitch:glitch:1:1: unsupported typed type mat4"),
    },
    "after_type_table_only_bypass": {
        "validator": (
            "classicNoisedeck/glitch:glitch:76:14: unsupported matrix constructor"),
        "emitter": (
            "classicNoisedeck/glitch:glitch:79:14: unsupported matrix binary expression"),
    },
}


def sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def whole(program: TypedProgram) -> str:
    return sha((program.key, program.source, program.raw_source,
                program.declarations, program.functions, program.resources,
                program.body_status, program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.counted_loop_proof,
                program.preprocessor_defines))


def interface(program: TypedProgram) -> str:
    return sha((program.declarations, program.resources,
                program.local_type_names, program.structs,
                program.uniform_blocks, program.interface_symbols,
                program.builtin_symbols, program.preprocessor_defines))


def walk_expression(value: TypedExpression,
                    parent: TypedExpression | None = None,
                    path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from walk_expression(child, value, (*path, index))


def walk_statement(value: TypedStatement,
                   path: tuple[object, ...] = (),
                   ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        yield from ((item, parent, expression_path, chain)
                    for item, parent, expression_path in walk_expression(
                        expression, None, (*path, f"e{index}")))
    for index, child in enumerate(value.children):
        yield from walk_statement(child, (*path, f"s{index}"), chain)


def parse(raw: str, key: str = KEY) -> TypedProgram:
    return analyze_program(
        parse_program(raw, key, gen._defaults(ROOT, key)), key)


def all_nodes(program: TypedProgram):
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in walk_statement(statement,
                                                            (index,)):
                yield function, item, parent, path, chain


def matrix_constructs(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "construct"
            and item[1].type.display() == "mat4"]


def matrix_products(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "binary" and item[1].operator == "*"
            and item[1].type.display() == "mat4"
            and [child.type.display() for child in item[1].children]
            == ["mat4", "mat4"]]


def vector_products(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "binary" and item[1].operator == "*"
            and item[1].type.display() == "vec4"
            and [child.type.display() for child in item[1].children]
            == ["vec4", "mat4"]]


def matrix_declarations(program: TypedProgram):
    return [item for item in all_nodes(program)
            if item[1].kind == "declaration"
            and item[1].type.display() == "mat4"]


def call_graph(program: TypedProgram) -> dict[str, tuple[str, ...]]:
    names = {function.id: function.name for function in program.functions}
    graph: dict[str, set[str]] = {function.name: set()
                                  for function in program.functions}
    for function, item, _, _, _ in all_nodes(program):
        if item.kind == "call" and item.signature_id in names:
            graph[function.name].add(names[item.signature_id])
    return {name: tuple(sorted(children)) for name, children in graph.items()}


def reachable(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    pending = ["main"]
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        pending.extend(graph.get(name, ()))
    return tuple(sorted(visited))


def symbol_name(value: TypedExpression) -> str | None:
    return getattr(value.symbol, "name", None)


def identity_accepts(program: TypedProgram, *, key: str, raw_hash: str,
                     profile: str) -> bool:
    if (key != KEY or raw_hash != RAW_SHA256 or profile != PROFILE
            or program.key != KEY):
        return False
    if (sha(program.source) != NORMALIZED_SHA256
            or sha(program.raw_source) != RAW_IR_SHA256
            or sha(program.functions) != FUNCTIONS_SHA256
            or sha(program.declarations) != DECLARATIONS_SHA256
            or whole(program) != WHOLE_SHA256
            or interface(program) != INTERFACE_SHA256):
        return False
    if tuple(function.name for function in program.functions) != EXPECTED_FUNCTIONS:
        return False
    graph = call_graph(program)
    if reachable(graph) != tuple(sorted(EXPECTED_FUNCTIONS)):
        return False

    constructs = matrix_constructs(program)
    products = matrix_products(program)
    vector = vector_products(program)
    declarations = matrix_declarations(program)
    if (tuple(span(item[1]) for item in constructs)
            != EXPECTED_CONSTRUCT_SPANS
            or tuple(span(item[1]) for item in products)
            != EXPECTED_MATRIX_PRODUCT_SPANS
            or tuple(span(item[1]) for item in vector)
            != EXPECTED_VECTOR_PRODUCT_SPANS):
        return False
    if len(declarations) != 4 or any(len(item[1].children) != 16
                                    for item in constructs):
        return False
    if any(item[0].name != "bicubic" for item in
           (*constructs, *products, *vector, *declarations)):
        return False

    outer = products[0][1]
    inner = products[1][1]
    if (outer.children[0] is not inner
            or [symbol_name(child) for child in inner.children] != ["T", "Q"]
            or symbol_name(outer.children[1]) != "S"):
        return False
    product = vector[0][1]
    if [symbol_name(child) for child in product.children] != ["tv", "A"]:
        return False

    # Exact route: vec4 product is the first child of the sole dot builtin at
    # the bicubic return and uv is the second child.
    dot_parents = [item for item in all_nodes(program)
                   if item[1].kind == "builtin" and item[1].callee == "dot"
                   and len(item[1].children) == 2
                   and item[1].children[0] is product]
    if len(dot_parents) != 1 or symbol_name(dot_parents[0][1].children[1]) != "uv":
        return False
    if not any(statement.kind == "return"
               for statement in dot_parents[0][4]):
        return False
    return True


def first_error(action) -> str:
    try:
        action()
    except Exception as error:  # noqa: BLE001 - freezes authority text
        return str(error).strip().splitlines()[0]
    return "pass"


def validate_and_emit(program: TypedProgram) -> dict[str, str]:
    return {
        "validator": first_error(lambda: gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=RAW_SHA256)),
        "emitter": first_error(lambda: emit.render_typed_cpp(
            program, KEY, RAW_SHA256, "glitch_probe", "bind_glitch_probe")),
    }


def type_only_bypass(program: TypedProgram) -> dict[str, str]:
    old_approved = gen.APPROVED_TYPES
    old_types = emit._TYPES
    try:
        gen.APPROVED_TYPES = (*old_approved, "mat4")
        emit._TYPES = {**old_types, "mat4": "glsl::Mat4"}
        return validate_and_emit(program)
    finally:
        gen.APPROVED_TYPES = old_approved
        emit._TYPES = old_types


def live_frontier(program: TypedProgram) -> dict[str, Any]:
    return {
        "typed_slice_programs_at_probe_time": len(
            gen.load_slice(ROOT)["programs"]),
        "current": validate_and_emit(program),
        "after_type_table_only_bypass": type_only_bypass(program),
        "interpretation": (
            "mat4 type admission exposes the distinct constructor and "
            "matrix-binary dispatch gates; the exact node census defines "
            "the required identity-scoped closure"),
    }


def mutation_result(name: str, raw: str) -> dict[str, Any]:
    try:
        program = parse(raw)
    except Exception as error:  # noqa: BLE001 - rejection is expected evidence
        return {"name": name, "accepted": False,
                "parse_rejected": str(error).strip().splitlines()[0]}
    return {
        "name": name,
        "accepted": identity_accepts(program, key=KEY,
                                     raw_hash=hashlib.sha256(
                                         raw.encode()).hexdigest(),
                                     profile=PROFILE),
        "whole_sha256": whole(program),
    }


def replace_once(raw: str, old: str, new: str) -> str:
    if raw.count(old) != 1:
        raise AssertionError(f"mutation anchor count for {old!r}: {raw.count(old)}")
    return raw.replace(old, new)


def describe_node(item) -> dict[str, Any]:
    function, node, parent, path, chain = item
    return {
        "owner": function.name,
        "owner_signature_id": function.id,
        "span": span(node),
        "kind": node.kind,
        "operator": node.operator,
        "type": node.type.display(),
        "child_kinds": [child.kind for child in node.children],
        "child_types": [child.type.display() for child in node.children],
        "child_symbols": [symbol_name(child) for child in node.children],
        "node_sha256": sha(node),
        "parent_kind": parent.kind if parent is not None else None,
        "parent_span": span(parent) if parent is not None else None,
        "path": list(path),
        "statement_chain": [{"kind": statement.kind, "span": span(statement)}
                            for statement in chain],
    }


def build() -> dict[str, Any]:
    raw = SOURCE.read_text()
    if hashlib.sha256(raw.encode()).hexdigest() != RAW_SHA256:
        raise AssertionError("pinned Glitch source drift")
    program = parse(raw)
    if not identity_accepts(program, key=KEY, raw_hash=RAW_SHA256,
                            profile=PROFILE):
        raise AssertionError("baseline Glitch identity rejected")

    negative_programs = [
        ("constructor-coefficient-order", replace_once(
            raw, "mat4(f11, f21, f11x, f21x,",
            "mat4(f21, f11, f11x, f21x,")),
        ("right-associated-chain", replace_once(
            raw, "mat4 A = T * Q * S;", "mat4 A = T * (Q * S);")),
        ("reverse-inner-operands", replace_once(
            raw, "mat4 A = T * Q * S;", "mat4 A = Q * T * S;")),
        ("extra-matrix-declaration", replace_once(
            raw, "mat4 A = T * Q * S;",
            "mat4 B = T;\n    mat4 A = B * Q * S;")),
        ("constructor-arity-drift", replace_once(
            raw, "mat4 S = mat4(1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1., 1.);",
            "mat4 S = mat4(1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1.);")),
        ("vector-matrix-orientation", replace_once(
            raw, "return dot(tv * A, uv);", "return dot(A * tv, uv);")),
        ("bicubic-return-route", replace_once(
            raw, "return dot(tv * A, uv);", "return dot(tv * A, tv);")),
    ]
    mutations = [mutation_result(name, source)
                 for name, source in negative_programs]
    contract_negatives = [
        {"name": "wrong-profile", "accepted": identity_accepts(
            program, key=KEY, raw_hash=RAW_SHA256, profile="wrong")},
        {"name": "wrong-key", "accepted": identity_accepts(
            program, key="foreign:glitch", raw_hash=RAW_SHA256,
            profile=PROFILE)},
        {"name": "wrong-caller-hash", "accepted": identity_accepts(
            program, key=KEY, raw_hash="0" * 64, profile=PROFILE)},
        *mutations,
    ]
    if any(item["accepted"] for item in contract_negatives):
        raise AssertionError("Glitch identity gate accepted a negative")

    graph = call_graph(program)
    constructs = matrix_constructs(program)
    products = matrix_products(program)
    vector = vector_products(program)
    declarations = matrix_declarations(program)
    return {
        "schema": 1,
        "program_key": KEY,
        "profile": PROFILE,
        "corpus_revision": REVISION,
        "source": {
            "relative_path": str(SOURCE.relative_to(ROOT)),
            "bytes": len(raw.encode()),
            "sha256": RAW_SHA256,
            "normalized_ir_sha256": NORMALIZED_SHA256,
            "raw_ir_sha256": RAW_IR_SHA256,
            "functions_sha256": FUNCTIONS_SHA256,
            "declarations_sha256": DECLARATIONS_SHA256,
            "whole_ir_sha256": WHOLE_SHA256,
            "interface_sha256": INTERFACE_SHA256,
        },
        "reachability": {
            "call_graph": graph,
            "reachable_from_main": list(reachable(graph)),
            "reachable_function_count": len(reachable(graph)),
            "total_function_count": len(program.functions),
            "all_functions_reachable": len(reachable(graph))
            == len(program.functions),
        },
        "matrix_nodes": {
            "declarations": [describe_node(item) for item in declarations],
            "constructs": [describe_node(item) for item in constructs],
            "matrix_matrix_products": [describe_node(item)
                                       for item in products],
            "vector_matrix_products": [describe_node(item)
                                       for item in vector],
            "nested_chain": {
                "source_shape": "(T * Q) * S",
                "outer_span": span(products[0][1]),
                "inner_span": span(products[1][1]),
                "inner_symbols": [symbol_name(child)
                                  for child in products[1][1].children],
                "outer_right_symbol": symbol_name(products[0][1].children[1]),
                "outer_left_is_inner_identity": products[0][1].children[0]
                is products[1][1],
            },
        },
        "frontier": {
            "snapshot_kind": "captured-pre-admission-live175",
            "durability": (
                "frozen evidence; --live-frontier observes later admission "
                "without changing this oracle"),
            **CAPTURED_PRE_ADMISSION_FRONTIER,
            "interpretation": (
                "mat4 type admission exposes the distinct constructor and "
                "matrix-binary dispatch gates; the exact node census above "
                "defines the required identity-scoped closure"),
        },
        "identity_gate": {
            "baseline_accepted": True,
            "negative_count": len(contract_negatives),
            "negatives": contract_negatives,
            "general_mat4_admitted": False,
            "required_profile": PROFILE,
        },
        "lowering_contract": {
            "layout": "column-major",
            "association": "left-associated (T*Q)*S",
            "matrix_product_materialization": (
                "each output element F32(sum), including the T*Q intermediate"),
            "vector_product_materialization": (
                "each tv*A component F32(dot sum) before outer dot"),
            "scope": (
                "only these authenticated mat4 nodes; no general matrix "
                "constructor, matrix*matrix, or vec*matrix capability"),
        },
    }


def main() -> int:
    data = build()
    if "--live-frontier" in sys.argv:
        print(json.dumps(live_frontier(parse(SOURCE.read_text())),
                         indent=2, sort_keys=True))
    elif "--check" in sys.argv:
        print("Glitch frontend proof ok (3 constructors, 2 mat4 products, "
              "1 vec4 product, 10 fail-closed negatives)")
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
