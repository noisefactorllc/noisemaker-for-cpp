"""Authenticate the two vec3 round sites in the current Shapes 3D source."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "classicNoisedeck/shapes3d:shapes3d"
RAW_SHA256 = "818badfbadcf295d1863d208c0d0582a1349ff64f44dbf43f905a92fcfd4c5ad"
RAW_BYTES = 16152
NORMALIZED_SHA256 = "2f2b40281c84c67297a466a42f7780c8b21b2b037a41bcf7d9c9fb6a98b03617"
NORMALIZED_BYTES = 11023
FUNCTIONS_SHA256 = "4d4046d9448e38c67aab440872deb681ccb03fb632f02c1e25fdd303df5285da"
WHOLE_SHA256 = "fdd41134212bfb343a643861cd2fed235e5d83c13da7f81aeb27f0ec2a980316"
INTERFACE_SHA256 = "e347814a67a9611866fcb8c923c5f32e3e96a850ab08116dd23471e3b66fc24a"
DEFAULT_DEFINES = (("BLEND_MODE", "int", "10"),
                   ("SHAPE_A", "int", "30"),
                   ("SHAPE_B", "int", "10"))
SITES = (
    (328, 35, "2b5092b3b341ef84d2055d1417648686a9e2ed57af8372569a68b12ae03f2ab5",
     "ac019935fc80fefa3052e73c0fc59fed4277b0907d2b815e49d09b296637528c"),
    (335, 35, "874c623d0950a94a81757e10dd3bea0fe4f1b09fb5646a3d87d36c5125784d61",
     "22ee7fc5874466920e5dc7d5be91e39fc878d6d40c81b3a5565b899ca50153da"),
)
LANE_SITES = (
    (192, 13, 60, "623a75664539d9695662d4e89de3d577596e1cf792f6209977041cc246de259d"),
    (193, 13, 149, "3190d2f43b81050dddbefebadd330930d77cdf3b2ca9a7f508fc0bd16c515c3d"),
    (193, 23, 60, "c55e0d4208873ce4f44b845429804399686bf732badfe83e5719ce945ba90450"),
    (195, 13, 149, "4965bce732179b27d46bd217c4d3a02595535563211f0c98adaa7cef5df9e9f5"),
    (195, 35, 60, "eb39784d4b80bc1861f4eb63e591f3b6ce8e8dd0894dcdbbc6ca8edc3e2de896"),
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _expressions(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statements(value: TypedStatement):
    for expression in value.expressions:
        yield from _expressions(expression)
    for child in value.children:
        yield from _statements(child)


def authenticate_shapes3d_rounds(
        program: TypedProgram, source_hash: str | None) -> tuple[TypedExpression, TypedExpression]:
    """Return only the two candidate-owned nodes after whole-program authentication."""
    if program.key == KEY:
        from .shapes3d_runtime_profile import DEFINES, authenticate
        shape = tuple((item.name, item.kind, item.canonical_value)
                      for item in program.preprocessor_defines)
        if shape == DEFINES:
            return authenticate(program, source_hash)[2]
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines) != DEFAULT_DEFINES
            or program.body_status != "analyzed"):
        raise ValueError("shapes3d-round: exact source and compile configuration required")
    whole = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (_sha(program.functions) != FUNCTIONS_SHA256 or _sha(whole) != WHOLE_SHA256
            or _sha(interface) != INTERFACE_SHA256):
        raise ValueError("shapes3d-round: function, whole-program, or interface drift")
    if (len(program.functions) != 24 or len(program.structs) != 2
            or len(program.declarations) != 39):
        raise ValueError("shapes3d-round: function, struct, or declaration census drift")
    owner = next((function for function in program.functions
                  if function.id == 102 and function.name == "applyTransform"), None)
    if owner is None:
        raise ValueError("shapes3d-round: exact owning function required")
    all_rounds = tuple(
        value for function in program.functions for statement in function.body
        for value in _statements(statement)
        if value.kind == "builtin" and value.callee == "round")
    owned_rounds = tuple(
        value for statement in owner.body for value in _statements(statement)
        if value.kind == "builtin" and value.callee == "round")
    if len(all_rounds) != 2 or any(a is not b for a, b in zip(all_rounds, owned_rounds)):
        raise ValueError("shapes3d-round: exact two owned sites required")
    for node, (line, column, digest, argument_digest) in zip(owned_rounds, SITES):
        if (node.span.start_line != line or node.span.start_column != column
                or node.signature_id != -38 or node.type.display() != "vec3"
                or node.category != "rvalue" or len(node.children) != 1
                or node.children[0].type.display() != "vec3"
                or _sha(node) != digest or _sha(node.children[0]) != argument_digest):
            raise ValueError("shapes3d-round: round site or argument drift")
    return owned_rounds


def authenticate_shapes3d_linear_indices(
        program: TypedProgram, source_hash: str | None) -> tuple[TypedExpression, ...]:
    """Prove five lane sites and complete writes in the three-iteration loop."""
    if program.key == KEY:
        from .shapes3d_runtime_profile import DEFINES, authenticate
        shape = tuple((item.name, item.kind, item.canonical_value)
                      for item in program.preprocessor_defines)
        if shape == DEFINES:
            return authenticate(program, source_hash)[1]
    authenticate_shapes3d_rounds(program, source_hash)
    owner = next((function for function in program.functions
                  if function.id == 109 and function.name == "linearToSrgb"), None)
    if (owner is None or owner.return_type.display() != "vec3"
            or len(owner.parameters) != 1
            or (owner.parameters[0].id, owner.parameters[0].name,
                owner.parameters[0].type.display(), owner.parameters[0].direction)
            != (60, "linear", "vec3", "in")
            or tuple(item.kind for item in owner.body) != ("decl", "for", "return")):
        raise ValueError("shapes3d-round: linearToSrgb owner drift")
    declaration, loop, returned = owner.body
    proof = loop.loop_proof
    if (proof is None or (proof.induction_symbol_id, proof.start_value,
            proof.bound_value, proof.comparison, proof.update, proof.bound_kind,
            proof.trip_count, proof.lexical_depth, proof.effective_depth,
            proof.lexical_product, proof.entrypoint_charge)
            != (150, 0, 3, "<", "++", "literal", 3, 1, 1, 3, 103)
            or len(declaration.expressions) != 1
            or declaration.expressions[0].symbol_id != 149
            or declaration.expressions[0].children != ()
            or len(loop.children) != 2 or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 1
            or loop.children[1].children[0].kind != "if"
            or len(returned.expressions) != 1
            or returned.expressions[0].symbol_id != 149):
        raise ValueError("shapes3d-round: bounded lane loop drift")
    conditional = loop.children[1].children[0]
    if (len(conditional.children) != 2
            or any(branch.kind != "block" or len(branch.children) != 1
                   or branch.children[0].kind != "expr"
                   or len(branch.children[0].expressions) != 1
                   or branch.children[0].expressions[0].kind != "assign"
                   or branch.children[0].expressions[0].operator != "="
                   for branch in conditional.children)):
        raise ValueError("shapes3d-round: branch-complete lane writes required")
    all_indices = tuple(
        value for function in program.functions for statement in function.body
        for value in _statements(statement) if value.kind == "index")
    owned_indices = tuple(
        value for statement in owner.body for value in _statements(statement)
        if value.kind == "index")
    if (len(all_indices) != len(LANE_SITES)
            or any(left is not right for left, right in zip(all_indices, owned_indices))):
        raise ValueError("shapes3d-round: exact lane-index census required")
    for node, (line, column, base_id, digest) in zip(owned_indices, LANE_SITES):
        if (node.span.start_line != line or node.span.start_column != column
                or node.type.display() != "float" or len(node.children) != 2
                or node.children[0].kind != "id"
                or node.children[0].symbol_id != base_id
                or node.children[0].type.display() != "vec3"
                or node.children[1].kind != "id"
                or node.children[1].symbol_id != 150
                or node.children[1].type.display() != "int"
                or _sha(node) != digest):
            raise ValueError("shapes3d-round: exact lane-index site drift")
    for branch, expected in zip(conditional.children,
                                (owned_indices[1], owned_indices[3])):
        if branch.children[0].expressions[0].children[0] is not expected:
            raise ValueError("shapes3d-round: lane write path drift")
    references = {
        symbol_id: tuple(value for function in program.functions
                         for statement in function.body
                         for value in _statements(statement)
                         if value.symbol_id == symbol_id)
        for symbol_id in (60, 149, 150)
    }
    if (len(references[60]) != 3 or len(references[149]) != 4
            or len(references[150]) != 8
            or {id(value) for value in references[60]}
            != {id(owned_indices[index].children[0]) for index in (0, 2, 4)}
            or {id(value) for value in references[149]}
            != {id(declaration.expressions[0]), id(returned.expressions[0]),
                id(owned_indices[1].children[0]), id(owned_indices[3].children[0])}
            or not {id(value.children[1]) for value in owned_indices}
            <= {id(value) for value in references[150]}):
        raise ValueError("shapes3d-round: lane reference census drift")
    return owned_indices
