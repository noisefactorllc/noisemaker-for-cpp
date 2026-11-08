"""Authenticate the two vec3 round sites in the current Shapes 3D source."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "classicNoisedeck/shapes3d:shapes3d"
RAW_SHA256 = "e17550180972bf97883c33eb4b280bfb3456d9212162c91e76cc8befbae941dc"
RAW_BYTES = 16075
NORMALIZED_SHA256 = "1879adb1262c150d2080725875a18a3be35129867a6120145932d9e97d64d2b2"
NORMALIZED_BYTES = 10946
FUNCTIONS_SHA256 = "21d2930ab1dd6100f7b062698269f9d0a832b0fa9172021c5d700c9baea354a5"
WHOLE_SHA256 = "41d766a9686c9a8753c038539535fc9c3233a1e546470bb6bf01b207a917667a"
INTERFACE_SHA256 = "ea7464219162eb9cfe0a9abee77025e131ce64d378bf5ef9026a8559b57574f5"
DEFAULT_DEFINES = (("BLEND_MODE", "int", "10"),
                   ("SHAPE_A", "int", "30"),
                   ("SHAPE_B", "int", "10"))
SITES = (
    (326, 35, "537375dc431a625b3604aaca8ef76fd23203acb16b01bfc4f8af997aebf6d99d",
     "cf362e1a0013505baa607dd09f2d1bcaa373801e6092a6c631c557c7c2c6c2e7"),
    (333, 35, "5ad63d228b354b26a1dd4102f3430c93cea7c20fb3a4744059077008811baf07",
     "22bd22082ba88fa3f48fbe405a1bfbd3197aa7578ce487c08c2cddbb49a39230"),
)
LANE_SITES = (
    (190, 13, 60, "a637ece468dc1fb6f0d0247ab97aab23520e6d2b5d2dc20b9feedd324f8b14f4"),
    (191, 13, 149, "d57ae63929e7a0bba1124ca16cb2669549fb86dc237150c7382aeb4e5afebdd9"),
    (191, 23, 60, "c2b543da66d300329db41d5d1b2f58aec823dee8dbefe5e18b71d76dd02d6362"),
    (193, 13, 149, "bf55be7f4fe05c9dc3871561e067e1e6cd3364f4f6856165ed550650f0e3d9b4"),
    (193, 35, 60, "ae62a04bd166cab0706c4165eb1eb25730f97518741953052e92b60950d211fa"),
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
