"""Exact Landscape 3D volume-atlas loop and perspective-tangent proof."""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .loop_proof import clear_counted_loop_proofs
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "render/renderLandscape3d:landscape"
RAW_SHA256 = "179f6394c13db68de0b2c0f07551c7a661380b7335421c36c4a3389792ac5f43"
RAW_BYTES = 14915
NORMALIZED_SHA256 = "970f67e868874f0d4d6e48a6fc4f0af2e968c61304223cd96804c146223cd01d"
NORMALIZED_BYTES = 13112
FUNCTIONS_SHA256 = "835fbd6c1a06f71265511937733d693e2e4bc0bab9bb873893ae8dbd48a0e2ab"
WHOLE_SHA256 = "7915d55c283ff64f6530e0073a4efb28737bb8ad2b16c9f95537435a53d7ed89"
INTERFACE_SHA256 = "c5480b4a64521870509f69752f34b78bcb102ef2c8a6c7f272f9daa0fc87362c"
TAN_SHA256 = "2f8abe2850875b9165098fe176c164919954aed3de7cdb7e1a8c281e1eedd404"
VOLUME_SIZE_MAX = 256


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _expressions(statement: TypedStatement):
    for expression in statement.expressions:
        yield from _expression_tree(expression)
    for child in statement.children:
        yield from _expressions(child)


def _expression_tree(expression: TypedExpression):
    yield expression
    for child in expression.children:
        yield from _expression_tree(child)


def authenticate(program: TypedProgram, source_hash: str | None):
    """Return the exact bound contract shared by the loop proof and binder."""
    from .runtime_loop_bound_profile import (
        RuntimeLoopBoundContract, RuntimeScalarBoundSeed,
    )

    functions = clear_counted_loop_proofs(program.functions)
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(program.raw_source.encode("utf-8")) != RAW_BYTES
            or hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest() != RAW_SHA256
            or len(program.source.encode("utf-8")) != NORMALIZED_BYTES
            or hashlib.sha256(program.source.encode("utf-8")).hexdigest() != NORMALIZED_SHA256
            or defines != (("FILTERING", "str", "int"), ("VIEW_MODE", "str", "int"))
            or program.body_status != "analyzed"
            or len(functions) != 15
            or _sha(functions) != FUNCTIONS_SHA256
            or _sha(whole) != WHOLE_SHA256
            or _sha(interface) != INTERFACE_SHA256):
        raise ValueError(f"{KEY}: source, variant, or typed-tree profile mismatch")
    symbols = {item.symbol.name: item.symbol for item in program.declarations}
    volume_size = symbols.get("volumeSize")
    volume_cache = symbols.get("volumeCache")
    analytical_geo = symbols.get("analyticalGeo")
    if (volume_size is None or volume_size.id != 10
            or volume_size.type.display() != "int"
            or volume_size.storage != "uniform"
            or volume_cache is None or volume_cache.id != 5
            or volume_cache.type.display() != "sampler2D"
            or analytical_geo is None or analytical_geo.id != 6
            or analytical_geo.type.display() != "sampler2D"):
        raise ValueError(f"{KEY}: volume atlas interface mismatch")
    tangent = tuple(node for function in functions for statement in function.body
                    for node in _expressions(statement)
                    if node.kind == "builtin" and node.callee == "tan")
    if (len(tangent) != 1 or tangent[0].type.display() != "float"
            or tangent[0].span.start_line != 189
            or tangent[0].span.start_column != 31
            or _sha(tangent[0]) != TAN_SHA256):
        raise ValueError(f"{KEY}: perspective tangent site mismatch")
    seed = RuntimeScalarBoundSeed(
        volume_size.id, VOLUME_SIZE_MAX,
        "runtime-volume-atlas-surface-cap", volume_size)
    return RuntimeLoopBoundContract(
        KEY, seed, "volume-atlas-size", "volumeSize", 1,
        VOLUME_SIZE_MAX, 64,
        f"{KEY} volume atlas shape or size mismatch",
        input_surface_name="volumeCache")


def tangent_node(program: TypedProgram, source_hash: str | None) -> TypedExpression:
    authenticate(program, source_hash)
    return next(node for function in program.functions for statement in function.body
                for node in _expressions(statement)
                if node.kind == "builtin" and node.callee == "tan")


class RelationalRecord(NamedTuple):
    reductions: tuple[TypedExpression, ...]
    relationals: tuple[TypedExpression, ...]
    declarations: tuple[TypedExpression, ...]
    swizzles: tuple[TypedExpression, ...]


def relational_nodes(program: TypedProgram, source_hash: str | None) -> RelationalRecord:
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    callees = {"any", "all", "lessThan", "greaterThan", "equal",
               "notEqual", "lessThanEqual", "greaterThanEqual"}
    entries = tuple((function.name, node.callee, _span(node), _sha(node),
                     node.type.display(),
                     tuple(child.type.display() for child in node.children),
                     parent.kind if parent is not None else None, node)
                    for function, _statement, node, parent in _program_nodes(program)
                    if node.kind == "builtin" and node.callee in callees)
    if (len(entries) != 12
            or _sha(tuple(entry[:-1] for entry in entries))
            != "a6f60b063739098f9f2171d7b102f46a5769ed654927443189cc42dd2dcd7b57"
            or sum(entry[1] == "any" for entry in entries) != 5
            or sum(entry[1] == "lessThanEqual" for entry in entries) != 2):
        raise ValueError(f"{KEY}: relational/reduction census mismatch")
    reductions = tuple(entry[-1] for entry in entries if entry[1] == "any")
    relationals = tuple(entry[-1] for entry in entries if entry[1] != "any")
    if any(reduction.children[0] not in relationals for reduction in reductions):
        raise ValueError(f"{KEY}: relational reduction child mismatch")
    declarations = tuple(node for _function, _statement, node, _parent
                         in _program_nodes(program)
                         if node.kind == "declaration"
                         and node.type.display() == "bvec3")
    if (len(declarations) != 2
            or _sha(tuple((_span(item), _sha(item)) for item in declarations))
            != "8f7b238cb275ed2d3c93adf0627b8c1f5e96a468666aac771086715740797535"):
        raise ValueError(f"{KEY}: relational local census mismatch")
    swizzles = tuple(node for _function, _statement, node, _parent
                     in _program_nodes(program)
                     if node.kind == "swizzle" and node.children
                     and node.children[0].type.display() == "bvec3")
    if (len(swizzles) != 10
            or _sha(tuple((_span(item), _sha(item), item.member)
                          for item in swizzles))
            != "7f14c80334c137f314bbc536f8fa78d20e8008a1481d265c255e20a158bdfee2"):
        raise ValueError(f"{KEY}: relational swizzle census mismatch")
    return RelationalRecord(reductions, relationals, declarations, swizzles)


def axis_indexes(program: TypedProgram, source_hash: str | None) -> tuple[TypedExpression, ...]:
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    entries = tuple((function.name, _span(node), _sha(node),
                     node.type.display(), node.children[0].type.display(),
                     node.children[1].type.display(), node.children[1].kind,
                     parent.kind if parent is not None else None,
                     node.children[0].kind, node)
                    for function, _statement, node, parent in _program_nodes(program)
                    if node.kind == "index")
    if (len(entries) != 19
            or _sha(tuple(entry[:-1] for entry in entries))
            != "caf73c99a49023e5b64b1812a68f4c1e4a3ae146a968a30685fbbb5eee42d414"
            or any(entry[0] != "renderPerspective"
                   or entry[4] not in {"vec3", "ivec3"}
                   or entry[6] != "id"
                   or entry[-1].children[1].symbol_id not in {125, 133}
                   for entry in entries)):
        raise ValueError(f"{KEY}: bounded axis-index census mismatch")
    return tuple(entry[-1] for entry in entries)


class SamplerRecord(NamedTuple):
    parameters: tuple
    uses: tuple[TypedExpression, ...]


def borrowed_samplers(program: TypedProgram, source_hash: str | None) -> SamplerRecord:
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    parameters = tuple((function, parameter)
                       for function in program.functions
                       for parameter in function.parameters
                       if parameter.type.kind == "sampler")
    uses = tuple(node for _function, _statement, node, _parent
                 in _program_nodes(program)
                 if node.kind == "id" and node.type.kind == "sampler"
                 and node.symbol_id in {34, 43, 46})
    if (len(parameters) != 3
            or _sha(tuple((function.name, parameter.id, parameter.name,
                           _span(parameter), _sha(parameter))
                          for function, parameter in parameters))
            != "d1f71a9eef432474e7d843476603889a34b185c2be4c3ad2688e519fd1e84583"
            or len(uses) != 10
            or _sha(tuple((next(function.name for function, _statement, candidate, _parent
                                in _program_nodes(program) if candidate is node),
                           node.symbol_id, _span(node), _sha(node))
                          for node in uses))
            != "e22bb58985c77429915105be55bd99d23e9c23eb9a950761e3f9ae55bea01f97"):
        raise ValueError(f"{KEY}: borrowed sampler census mismatch")
    return SamplerRecord(parameters, uses)


class ExposureParameter(NamedTuple):
    parameter: tuple
    parameter_object: object
    uses: tuple[TypedExpression, ...]
    constructs: tuple[TypedExpression, ...]
    assigns: tuple[TypedExpression, ...]


def exposed_face_parameter(program: TypedProgram, source_hash: str | None) -> ExposureParameter:
    """Bind the one bvec3 parameter of exposedFace, its id uses and the
    exact bvec3(false) constructor sites the hoisted crossed locals need."""
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    rows: list[tuple] = []
    objects: list[object] = []
    for function in program.functions:
        for ordinal, parameter in enumerate(function.parameters):
            if parameter.type.display() == "bvec3":
                rows.append((function.name, ordinal, parameter.id, parameter.name,
                             _span(parameter), parameter.type.display(),
                             parameter.direction))
                objects.append(parameter)
    if (len(rows) != 1
            or rows[0] != ("exposedFace", 1, 61, "crossed", "162:30-162:43", "bvec3", "in")
            or _sha(tuple(rows))
            != "ccb50ff5790e4993397215ddf8d259ac97934660f586c866a067c93acd46a6f9"):
        raise ValueError(f"{KEY}: exposed-face parameter mismatch")
    uses = tuple(node for _function, _statement, node, _parent
                 in _program_nodes(program)
                 if node.kind == "id" and getattr(node, "symbol_id", None) == 61)
    if (len(uses) != 6
            or _sha(tuple((next(function.name for function, _statement, candidate, _parent
                                in _program_nodes(program) if candidate is node),
                           _span(node), _sha(node), node.symbol_id)
                          for node in uses))
            != "65528ee47ca5e74e1b2f95eddd3b3710ecbd31601833f9f2ac9bd49b61fbd9fc"):
        raise ValueError(f"{KEY}: exposed-face parameter use mismatch")
    constructs = tuple(node for _function, _statement, node, _parent
                       in _program_nodes(program)
                       if node.kind == "construct" and node.constructor_type is not None
                       and node.constructor_type.display() == "bvec3")
    if (len(constructs) != 2
            or _sha(tuple((next(function.name for function, _statement, candidate, _parent
                                in _program_nodes(program) if candidate is node),
                           _span(node), _sha(node))
                          for node in constructs))
            != "ece84957aee16a63878125322668ee38991f4253bfbaa765e3dc5a727c2d6ec1"):
        raise ValueError(f"{KEY}: exposed-face constructor census mismatch")
    assigns = tuple(node for _function, _statement, node, _parent
                    in _program_nodes(program)
                    if node.kind == "assign" and node.type.display() == "bvec3")
    if (len(assigns) != 2
            or _sha(tuple((next(function.name for function, _statement, candidate, _parent
                                in _program_nodes(program) if candidate is node),
                           _span(node), _sha(node))
                          for node in assigns))
            != "1cb82c282dcb0be520356b0deb7638187d96d3093baf00c042f30875de7d0432"):
        raise ValueError(f"{KEY}: exposed-face assign census mismatch")
    return ExposureParameter(rows[0], objects[0], uses, constructs, assigns)


def perspective_call(program: TypedProgram, source_hash: str | None) -> TypedExpression:
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    calls = tuple((function.name, _span(node), _sha(node), node.callee,
                   node.signature_id, node)
                  for function, _statement, node, _parent in _program_nodes(program)
                  if node.kind == "call" and node.type.display() == "void")
    if (len(calls) != 1
            or _sha(tuple(item[:-1] for item in calls))
            != "999345123b8b67188430ac3bd13aadb2bd9f4e6d546dccc7c212e3a555df146e"):
        raise ValueError(f"{KEY}: perspective call census mismatch")
    return calls[0][-1]


def validate_metadata(effect: dict) -> None:
    params = effect.get("params", {})
    if (params.get("volumeSize") != {"default": 64, "type": "int", "uniform": "volumeSize"}
            or params.get("viewMode", {}).get("choices")
            != {"ortho": 1, "perspective": 2}
            or params.get("filtering", {}).get("choices")
            != {"isosurface": 0, "voxel": 1}):
        raise ValueError(f"{KEY}: volume, view, or filtering metadata mismatch")


__all__ = ["KEY", "authenticate", "tangent_node",
           "relational_nodes", "axis_indexes", "borrowed_samplers",
           "perspective_call", "validate_metadata"]
