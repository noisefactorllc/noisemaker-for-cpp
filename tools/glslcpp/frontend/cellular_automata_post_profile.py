"""Authenticate the ten integer post-increments in the current CA shader."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "synth3d/cellularAutomata3d:simulate"
RAW_SHA256 = "0e2cf2bb49dffd6d5e1360772e750fde7328c0e29e2122bcb829ab00e006b881"
RAW_BYTES = 9257
NORMALIZED_SHA256 = "a10f48efe5b29791d5c049fc62a1955051a5b5a9e3f846f9dc87483f4ed32a74"
NORMALIZED_BYTES = 6734
FUNCTIONS_SHA256 = "2fe56a236dd6b86853c33bf68e521a4ea78fddb65e1c2d5e3c6e07e10753eae1"
WHOLE_SHA256 = "073ef5eb17770206d4adbcda1c069ecb063dd4ca4f38516f1d8a3f1977b12ec1"
INTERFACE_SHA256 = "fce73c45922415e4228f120d79289557e7a15f0f3a7cb148a698bb9b5cf07185"
SITES = (
    (32, 61, 32, 44, "2155e1376804853a87a00f54d7b729991cab76de69a690c8890292aafcb6c15b"),
    (32, 62, 36, 45, "e6c4f551df56d53406c1f8e39a25f2fe350dd099d2d86f66b7cc185a769622e9"),
    (32, 63, 40, 46, "d56cfffdc0cf3aafa67c847fb8fc66feed85f2089f38ac88aafe8a2e26ce24d3"),
    (32, 66, 39, 43, "9f104e945e705b601ace6c698a5dfa4514048f8dccbd4fe5e17ce38882fd4f87"),
    (33, 83, 21, 48, "09671fc606acf43ba582f6e50c2876b55bfc388f8068ec298882235fea0ba98b"),
    (33, 84, 21, 48, "dabcda0fcb40f5ea0c481068b7a481da8f3dad02784d59d870364c6fd26825c4"),
    (33, 85, 21, 48, "935549aee0b6bdd84a27394aa804f814e4e33704a2fabba6eca7d19d2236803c"),
    (33, 86, 21, 48, "20126fcd40f5eb786fdd8ba04e1a6fc0422c001e6246f1e94d44167434719fa3"),
    (33, 87, 21, 48, "e5b83701c27d260fe6665b284f092cd2530fb936618972371fc14d4129d5f354"),
    (33, 88, 21, 48, "755fac6fe42e352c6186c361df858f113e86e6f8b072bfc03566b441ac142492"),
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
    if (len(program.functions) != 10
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
    moore = next(function for function in program.functions if function.id == 32)
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
                       loops, (44, 45, 46), found[:3]))):
        raise ValueError("cellular-automata-post: bounded loop updates drift")
    return tuple(node for _, node in found)
