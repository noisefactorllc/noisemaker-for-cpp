"""Exact dynamic Moodscape frontend projection for the current CPU contract."""

from __future__ import annotations

import dataclasses
import hashlib
from typing import NamedTuple

from tools.glslcpp.frontend.loop_proof import (
    attach_counted_loop_proofs, clear_counted_loop_proofs,
    summarize_counted_loop_proofs,
)
from tools.glslcpp.frontend import moodscape_frontend_profile as default
from tools.glslcpp.frontend.typed_ir import TypedExpression, TypedProgram

KEY = default.KEY
PROFILE = "moodscape-runtime-frontend-v1"
DEFINES = (("COLOR_MODE", "str", "int"), ("NOISE_TYPE", "str", "int"))
NORMALIZED_BYTES = 17863
NORMALIZED_SHA256 = "20a6f4a0accd2f1b02c310ee2d3614f2bba0da58eb4f9a64fdc64ed408d823b9"
FULL_FUNCTIONS_SHA256 = "9c00b6fa9906183d686c508f6535fa76c8a5eff96b07f93f08c1e7c7aded8d97"
FULL_WHOLE_SHA256 = "37ef19ad81826860de6a29feff3b89fff6d0fe46eb7c284712df9ba9a73c3b4c"
FULL_INTERFACE_SHA256 = "6ea4427f1d26166be5ace4037357c1d34da55155b6303e7454409cb3962bd56a"
PROJECTED_FUNCTIONS_SHA256 = "405ed5a85af2a335590416e88c606a06fe27dfa0d707712bf138001e326972c9"
PROJECTED_WHOLE_SHA256 = "b954a5c853150dc073d98859de2546e777f49e8dea7ae0e6485b91bcff7c7825"
PROJECTED_INTERFACE_SHA256 = "11399e43904e3b17c3ebc0289b21bc26e5f734500dfac3f70d43ae87b3fd5759"
REACHABLE_IDS = (106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
                 118, 119, 120, 121, 122, 124, 125, 126, 127, 128, 129, 130,
                 131, 132, 133, 134, 135)
DEAD_IDS = (123,)
MATRIX_LEDGER = (
    ("fwdA", "151:1-153:68", "3c9305e49aceec28322eea18868be7d419ff76199273ae2fae77e269a5eac785"),
    ("fwdB", "155:1-157:68", "8124b5c9b6c11157a9cb481c001f856e543c2ddb508300c784588631c167dbec"),
    ("invB", "159:1-161:66", "3375687c2a685efb11fd17738ab509c1376ea225f5fc0fb14a4c9eb5be0c388c"),
    ("invA", "163:1-165:68", "6e0af1cc398c98d60efeb657e87fd6875e3c5db7ea114d91fd21a0bc23306aac"),
)
LANE_INDEX_LEDGER = (
    ("139:13-139:22", "6bd60913c296bb7349e05474ff5c4327ea2f6398a9e093676465c0bf4a8e7cf7"),
    ("140:13-140:20", "0c5d77219ae68af0fa55c8617baf2ccc33ec4ade15f7e856bc6a6687f1238ba6"),
    ("140:23-140:32", "9b7195c3e4d9a08903e0901bba85c732c6e2001f216606d1a70df3b6b52fabe0"),
    ("142:13-142:20", "375508b57c3bb3ff3316ef77213cf06fd6cc28f0e9ba88e47d961e85df09bf54"),
    ("142:35-142:44", "cdddd2146ca633302a509e0f487dcff66997a188d49622f1c08c177493371abd"),
)
FLOAT_BITS_LEDGER = (("299:21-299:46", "00790aa8164a81c5ba9e4103a3410004e57549f69b0d35983f12f6ef36b225df"),)
SCALAR_XOR_LEDGER = (
    ("302:10-302:46", "7875a1a5c5ace478a1f88619c98c490f2975019773a9bb07b5f1de01b67031c9"),
    ("303:10-303:46", "ab9e09bb2deb556f5521900640a88d8d23bd0a5dabc024e4786205c15516d5ba"),
    ("304:10-304:47", "776ee7737ae52317db173d74786d2b99dd87e4b9ad8897df21ea41c949dd779c"),
)
LOOP = (1, 0, 1, 3, 3, True)
HUE_PAIR_LEDGER = (
    ("572:5-572:43", "21b5b20e4ad0bfbe7b109fe7727a4449024ff0429a1c454591a256dab00b568f",
     "573:5-573:29", "04946dfbf8590c86feb997b986370a9b0221c6c8028d45ee204b627e753578c9"),
    ("591:5-591:43", "2b59834131837ec2542f2b419e0e7b37fa3767d06e7dd75894a6fab72cde45b2",
     "592:5-592:29", "49dfc8a26400b85991de3cdf23cf570f33608582bb4782f6090aa5c20429eb31"),
)


class HuePair(NamedTuple):
    addition: TypedExpression
    fract: TypedExpression


class Sites(NamedTuple):
    lane_indexes: tuple[TypedExpression, ...]
    float_bits: tuple[TypedExpression, ...]
    scalar_xors: tuple[TypedExpression, ...]


def _fail(reason: str) -> ValueError:
    return ValueError(f"{PROFILE}: {reason}")


def _provenance(program: TypedProgram, source_hash: str | None, profile: str | None) -> None:
    if program.key != KEY or profile != PROFILE or source_hash != default.RAW_SHA256:
        raise _fail("key, source hash, or profile mismatch")
    if (len(program.raw_source.encode()) != default.RAW_BYTES
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != default.RAW_SHA256
            or len(program.source.encode()) != NORMALIZED_BYTES
            or hashlib.sha256(program.source.encode()).hexdigest() != NORMALIZED_SHA256
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines) != DEFINES):
        raise _fail("source or define contract mismatch")


def _matrix_ledger(program: TypedProgram) -> tuple[tuple[str, str, str], ...]:
    return tuple((item.symbol.name, default._span(item), default._sha(item))
                 for item in program.declarations if item.type.display() == "mat3")


def _hue_pairs(program: TypedProgram) -> tuple[HuePair, ...]:
    main = next((function for function in program.functions
                 if function.name == "main"), None)
    if main is None:
        raise _fail("main function missing")
    pairs: list[HuePair] = []

    def color_red(node: TypedExpression) -> bool:
        return (node.kind == "swizzle" and node.member == "r"
                and node.type.display() == "float" and len(node.children) == 1
                and node.children[0].kind == "id"
                and node.children[0].symbol_id == 220
                and node.children[0].symbol.name == "color"
                and node.children[0].type.display() == "vec4")

    def visit(items) -> None:
        for first, second in zip(items, items[1:]):
            if (len(first.expressions) != 1 or len(second.expressions) != 1):
                continue
            addition, fract = first.expressions[0], second.expressions[0]
            if (addition.kind != "assign" or addition.operator != "+="
                    or fract.kind != "assign" or fract.operator != "="
                    or len(addition.children) != 2 or len(fract.children) != 2
                    or not color_red(addition.children[0])
                    or not color_red(fract.children[0])):
                continue
            call = fract.children[1]
            if (call.kind != "builtin" or call.callee != "fract"
                    or call.signature_id != -18 or len(call.children) != 1
                    or not color_red(call.children[0])):
                continue
            pairs.append(HuePair(addition, fract))
        for item in items:
            visit(item.children)

    visit(main.body)
    if tuple((default._span(pair.addition), default._sha(pair.addition),
              default._span(pair.fract), default._sha(pair.fract))
             for pair in pairs) != HUE_PAIR_LEDGER:
        raise _fail("hue-addition/fract adjacency or identity mismatch")
    for pair in pairs:
        increment = pair.addition.children[1]
        if (increment.kind != "binary" or increment.operator != "-"
                or len(increment.children) != 2
                or increment.children[0].kind != "literal"
                or increment.children[0].literal_value != 1.0):
            raise _fail("hue increment form mismatch")
        quotient = increment.children[1]
        if (quotient.kind != "binary" or quotient.operator != "/"
                or len(quotient.children) != 2
                or quotient.children[0].kind != "id"
                or quotient.children[0].symbol_id != 12
                or quotient.children[0].symbol.name != "hueRotation"
                or quotient.children[1].kind != "literal"
                or quotient.children[1].literal_value != 360.0):
            raise _fail("hue rotation source mismatch")
    return tuple(pairs)


def _sites(program: TypedProgram) -> Sites:
    indexes: list[TypedExpression] = []
    float_bits: list[TypedExpression] = []
    scalar_xors: list[TypedExpression] = []
    for function in program.functions:
        for item in function.body:
            def scan(statement):
                for expression in statement.expressions:
                    for node in default._walk(expression):
                        if node.kind == "index":
                            if function.name != "linearToSrgb":
                                raise _fail("index escaped linearToSrgb")
                            indexes.append(node)
                        elif node.kind == "builtin" and node.callee == "floatBitsToUint":
                            if function.name != "randomFromLatticeWithOffset":
                                raise _fail("float-bit ingress escaped lattice hash")
                            float_bits.append(node)
                        elif (node.kind == "binary" and node.operator == "^"
                              and node.type.display() == "uint"):
                            if function.name != "randomFromLatticeWithOffset":
                                raise _fail("scalar XOR escaped lattice hash")
                            scalar_xors.append(node)
                for child in statement.children:
                    scan(child)
            scan(item)
    for values, ledger in ((indexes, LANE_INDEX_LEDGER),
                           (float_bits, FLOAT_BITS_LEDGER),
                           (scalar_xors, SCALAR_XOR_LEDGER)):
        if tuple((default._span(item), default._sha(item)) for item in values) != ledger:
            raise _fail("exceptional site identity mismatch")
    for node in indexes:
        if (node.type.display() != "float" or len(node.children) != 2
                or node.children[0].type.display() != "vec3"
                or node.children[1].type.display() != "int"):
            raise _fail("lane index type mismatch")
    for node in float_bits:
        if (node.type.display() != "uint" or len(node.children) != 1
                or node.children[0].type.display() != "float"):
            raise _fail("float-bit ingress type mismatch")
    for node in scalar_xors:
        if (node.type.display() != "uint" or len(node.children) != 2
                or any(child.type.display() != "uint" for child in node.children)):
            raise _fail("scalar XOR type mismatch")
    _hue_pairs(program)
    return Sites(tuple(indexes), tuple(float_bits), tuple(scalar_xors))


def authenticate_projection(program: TypedProgram, source_hash: str | None,
                            profile: str | None) -> Sites:
    _provenance(program, source_hash, profile)
    if (len(program.functions) != 29
            or tuple(item.id for item in program.functions) != REACHABLE_IDS
            or default._sha(program.functions) != PROJECTED_FUNCTIONS_SHA256
            or default._whole(program) != PROJECTED_WHOLE_SHA256
            or default._interface(program) != PROJECTED_INTERFACE_SHA256
            or tuple((item.symbol.name, default._span(item), default._sha(item))
                     for item in program.declarations if item.type.display() == "mat3") != MATRIX_LEDGER[:2]):
        raise _fail("projected tree or matrix closure mismatch")
    loop = program.counted_loop_proof
    if loop is None or (loop.loop_count, loop.unproved_loop_count,
                        loop.max_effective_depth, loop.max_lexical_product,
                        loop.entrypoint_charge, loop.call_graph_acyclic) != LOOP:
        raise _fail("bounded loop proof mismatch")
    return _sites(program)


def apply(program: TypedProgram, source_hash: str | None,
          profile: str | None) -> tuple[TypedProgram, Sites]:
    _provenance(program, source_hash, profile)
    if (len(program.functions) != 30
            or default._sha(program.functions) != FULL_FUNCTIONS_SHA256
            or default._whole(program) != FULL_WHOLE_SHA256
            or default._interface(program) != FULL_INTERFACE_SHA256
            or tuple(item.id for item in program.functions) != tuple(sorted((*REACHABLE_IDS, *DEAD_IDS)))
            or _matrix_ledger(program) != MATRIX_LEDGER):
        raise _fail("full dynamic tree mismatch")
    _sites(program)
    functions = attach_counted_loop_proofs(
        clear_counted_loop_proofs(tuple(item for item in program.functions
                                         if item.id in REACHABLE_IDS)), program.key)
    projected = dataclasses.replace(
        program,
        functions=functions,
        declarations=tuple(item for item in program.declarations
                           if item.symbol.name not in ("invA", "invB")),
        counted_loop_proof=summarize_counted_loop_proofs(functions),
    )
    return projected, authenticate_projection(projected, source_hash, profile)


def authenticate_hue_pairs(program: TypedProgram, source_hash: str | None,
                           profile: str | None) -> tuple[HuePair, ...]:
    authenticate_projection(program, source_hash, profile)
    return _hue_pairs(program)
