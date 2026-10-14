"""Authenticate the ten integer post-increments in the current CA shader."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "synth3d/cellularAutomata3d:simulate"
RAW_SHA256 = "e29a5b033304463b8610c86823f46c16751270a3cbaa37f1204df968c6c5394a"
RAW_BYTES = 8843
NORMALIZED_SHA256 = "c4f0d809ea5e0e86ce47653cccac606490dd363733fb7c187e6b3698b2346f7b"
NORMALIZED_BYTES = 6584
FUNCTIONS_SHA256 = "1b621c0f0d629f778954826f22601e2391d72f41a1aea83cac78a846e1a67674"
WHOLE_SHA256 = "e99f386c062d5e5dd5e93efc8248913c77707e9da4bd7395f54981839b28e1ff"
INTERFACE_SHA256 = "7a402a8665f25b7ac55f9663eedc8a452784c477215093af13340b26f957a3e2"
SITES = (
    (29, 51, 32, 40, "a692417ec5248dbc6a337f20fbb0b056e55fa06c7c88cf9f33ffd033fd536b80"),
    (29, 52, 36, 41, "3084a089221add4a2d7b74dc5aadea0ef8e0c808abd5cf2befefbe254f9ca9a1"),
    (29, 53, 40, 42, "d9fba6d7e01cc52d201e0e9acc32130210ff4eb7ca099dce4cfb03c462b4b9fc"),
    (29, 56, 39, 39, "50fbf7ea87e0169e54348265fac406155c6bb1db0002e163f8891e82603ec14a"),
    (30, 73, 21, 44, "fb3efe669537974e9d67f472aae4ac410896e32c175e48de548881b9e862393b"),
    (30, 74, 21, 44, "2f9e60c3394c6acaf5e528d6725839b4fc91f9131917183854bcbeabe956561d"),
    (30, 75, 21, 44, "c36ad07a16b71d5dd06462f70191d3adfcd0d2a2988971caf9b42e89bf11865b"),
    (30, 76, 21, 44, "db8c3ae5f03a14e7da9d03259f2c13683de35b951cdf65882f4ec6420c315a1e"),
    (30, 77, 21, 44, "03a485e267d339ce3cd5daa751815af0fd840e613149d44e266e52ce2b8f8afb"),
    (30, 78, 21, 44, "b7fe025495f45366f1ca0f4896485ee86b836875576b5022d7fb32cb5e63acdf"),
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


def authenticate_ca_posts(
        program: TypedProgram, source_hash: str | None) -> tuple[TypedExpression, ...]:
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (program.key != KEY or source_hash != RAW_SHA256
            or len(raw) != RAW_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or program.preprocessor_defines != () or program.body_status != "analyzed"):
        raise ValueError("cellular-automata-post: exact source and compile configuration required")
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
        raise ValueError("cellular-automata-post: function, whole-program, or interface drift")
    if (len(program.functions) != 9
            or program.counted_loop_proof.loop_count != 3
            or program.counted_loop_proof.unproved_loop_count != 0
            or program.counted_loop_proof.max_lexical_product != 27):
        raise ValueError("cellular-automata-post: counted-loop census drift")
    found = tuple((function.id, node) for function in program.functions
                  for statement in function.body for node in _statements(statement)
                  if node.kind == "post")
    if len(found) != len(SITES):
        raise ValueError("cellular-automata-post: post-expression census drift")
    for (owner_id, node), (expected_owner, line, column, symbol_id, digest) in zip(found, SITES):
        if (owner_id != expected_owner or node.span.start_line != line
                or node.span.start_column != column or node.operator != "++"
                or node.type.display() != "int" or len(node.children) != 1
                or node.children[0].kind != "id"
                or node.children[0].symbol_id != symbol_id
                or node.children[0].type.display() != "int"
                or _sha(node) != digest):
            raise ValueError("cellular-automata-post: exact post site drift")
    moore = next(function for function in program.functions if function.id == 29)
    loops = []

    def walk(statement: TypedStatement):
        if statement.kind == "for":
            loops.append(statement)
        for child in statement.children:
            walk(child)

    for statement in moore.body:
        walk(statement)
    if (len(loops) != 3
            or any(loop.loop_proof is None
                   or loop.loop_proof.induction_symbol_id != symbol_id
                   or loop.loop_proof.trip_count != 3
                   or loop.expressions[-1] is not node
                   for loop, symbol_id, (_, node) in zip(
                       loops, (40, 41, 42), found[:3]))):
        raise ValueError("cellular-automata-post: bounded loop updates drift")
    return tuple(node for _, node in found)
