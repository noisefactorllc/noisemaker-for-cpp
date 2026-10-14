"""Exact Landscape 3D volume-atlas loop and perspective-tangent proof."""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .loop_proof import clear_counted_loop_proofs
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "render/renderLandscape3d:landscape"
RAW_SHA256 = "c9e9ab5c4d7226e774f8d1b9f8aff9d54fd4d6cd97e07c2d3c907df1d7b07ff8"
RAW_BYTES = 13406
NORMALIZED_SHA256 = "8939370f28d017fef6b536e16bded65fdf33a7b6cb7b3e7cd10c926e4974fe3d"
NORMALIZED_BYTES = 12161
FUNCTIONS_SHA256 = "6ced52ebadbf88ed0743d105a2a3841546f8bff0851156935c2b3ea7e9543d7e"
WHOLE_SHA256 = "def60d31fffa29e7dc7c94ccbb27272eb1e72cf28b257007de850b783210dc40"
INTERFACE_SHA256 = "c28906a0565c0fa051d0bbf977dfe74b528cf690931f15096974d74570443be9"
TAN_SHA256 = "729511d49d16e1bc2a8e7b2b828807c8fd506faa2b6a9448d54a2de51514d47d"
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
            or len(functions) != 13
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
            or tangent[0].span.start_line != 167
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
    if (len(entries) != 8
            or _sha(tuple(entry[:-1] for entry in entries))
            != "d426b33043f16cb9557e552d0bb601eb3e3e1023d25bb1c638e5c628db6851c5"
            or sum(entry[1] == "any" for entry in entries) != 3
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
            != "240de1d9b12c3d117ec727d1d67d30511b2c9998c31c259fc261586918322a66"):
        raise ValueError(f"{KEY}: relational local census mismatch")
    swizzles = tuple(node for _function, _statement, node, _parent
                     in _program_nodes(program)
                     if node.kind == "swizzle" and node.children
                     and node.children[0].type.display() == "bvec3")
    if (len(swizzles) != 4
            or _sha(tuple((_span(item), _sha(item), item.member)
                          for item in swizzles))
            != "ef425fdffdcb4fdf44aa5f00a9439033a0826bfaa252c5c003eb76b82f89f299"):
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
            != "b4aadb45fb14ba0fe05b982aa7ca14cb60b0208d1d2bdadb4a8dc7448481cf40"
            or any(entry[0] != "renderPerspective"
                   or entry[4] not in {"vec3", "ivec3"}
                   or entry[6] != "id"
                   or entry[-1].children[1].symbol_id not in {118, 126}
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


def perspective_call(program: TypedProgram, source_hash: str | None) -> TypedExpression:
    authenticate(program, source_hash)
    from .struct_frontier_profile import _program_nodes, _span
    calls = tuple((function.name, _span(node), _sha(node), node.callee,
                   node.signature_id, node)
                  for function, _statement, node, _parent in _program_nodes(program)
                  if node.kind == "call" and node.type.display() == "void")
    if (len(calls) != 1
            or _sha(tuple(item[:-1] for item in calls))
            != "866e761deb4df232dbe30e7a8a287f38619adb7e65375558a77e61773b714f63"):
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
