"""Pinned canonical-JavaScript compatibility repair for Refract blend arms."""

from __future__ import annotations

import dataclasses
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


TRANSFORM = "refract-truthy-vector-conditional-noop-v1"
REFRACT_KEY = "classicNoisedeck/refract:refract"
RAW_SOURCE_SHA256 = "d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2"
NORMALIZED_SOURCE_SHA256 = "bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e"
PRE_FUNCTIONS_SHA256 = "ccde114d367313d1feb218c7f956df4059534b5c139c757a30ae156292e9cc09"
PRE_WHOLE_PROGRAM_SHA256 = "0b2ebb355e506de21ffd829a72302494bd8c77d7bd35fb7f7a5e4b3407ce7003"
INTERFACE_SHA256 = "36d7815ce5aa9efedf3144e199ae7b49dc5819c751475b815708424269033229"
POST_FUNCTIONS_SHA256 = "4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188"
POST_WHOLE_PROGRAM_SHA256 = "93329ab73d54ff1eb3b8ec43da8570365d58de8caaa1a36252ef1ad30a709de2"

_MODE_SEQUENCE = (0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
_SITES = {
    2: (120, 34, 0.0, "max",
        "76dd1c7bd072f1c123bc7b11c381ecfbd42c658b74cedeca8ce0531bd1e65c6d"),
    3: (123, 34, 1.0, "min",
        "1a58e644c3fdfd7dffcbafceb6818a85c647db3a8ab944184c473db7ed17b5b9"),
    7: (135, 34, 1.0, "min",
        "fc1f8b322b55bfa6bc2ba556b2974c6ab2d52b7df303ecdaea8d705d1283586c"),
    15: (159, 33, 1.0, "min",
         "49509667ab252de2479f53b0d843c81a9eb04a83fc3e4c38a130c4a4319e394b"),
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _interface_fingerprint(program: TypedProgram) -> str:
    profile = (
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    )
    return _sha(profile)


def whole_program_fingerprint(program: TypedProgram) -> str:
    """Hash every semantic input through the accepted Task 18 proof layer."""
    profile = (
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
        program.fixed_nine_table_proof,
        program.fixed_grid_counter_store_proof,
    )
    return _sha(profile)


def _fail(message: str) -> ValueError:
    return ValueError(f"{TRANSFORM}: {message}")


def _guard_mode(statement: TypedStatement, blend_mode_id: int) -> int | None:
    if statement.kind != "if" or len(statement.expressions) != 1:
        return None
    guard = statement.expressions[0]
    if (guard.kind != "binary" or guard.operator != "=="
            or len(guard.children) != 2):
        return None
    for identifier, literal in ((guard.children[0], guard.children[1]),
                                (guard.children[1], guard.children[0])):
        if (identifier.kind == "id" and identifier.symbol_id == blend_mode_id
                and literal.kind == "literal"
                and literal.type.display() == "int"
                and isinstance(literal.literal_value, int)):
            return literal.literal_value
    return None


def _rewrite_site(statement: TypedStatement, mode: int,
                  middle_id: int) -> TypedStatement:
    expected_line, source_id, constant, false_builtin, expected_hash = _SITES[mode]
    if (statement.kind != "block" or len(statement.children) != 1
            or statement.children[0].kind != "expr"
            or len(statement.children[0].expressions) != 1):
        raise _fail(f"mode {mode} arm shape mismatch")
    expression = statement.children[0].expressions[0]
    if (_sha(expression) != expected_hash or expression.kind != "assign"
            or expression.operator != "=" or len(expression.children) != 2
            or expression.span.start_line != expected_line):
        raise _fail(f"mode {mode} assignment mismatch")
    target, conditional = expression.children
    if (target.kind != "id" or target.symbol_id != middle_id
            or conditional.kind != "conditional"
            or len(conditional.children) != 3):
        raise _fail(f"mode {mode} target/conditional mismatch")
    predicate, true_value, false_value = conditional.children
    if (predicate.kind != "binary" or predicate.operator != "=="
            or len(predicate.children) != 2
            or true_value.kind != "id" or true_value.symbol_id != source_id
            or false_value.kind != "builtin"
            or false_value.callee != false_builtin):
        raise _fail(f"mode {mode} predicate/arm mismatch")
    equality = False
    for identifier, constructor in ((predicate.children[0], predicate.children[1]),
                                    (predicate.children[1], predicate.children[0])):
        equality = equality or (
            identifier.kind == "id" and identifier.symbol_id == source_id
            and constructor.kind == "construct"
            and constructor.constructor_type is not None
            and constructor.constructor_type.display() == "vec4"
            and len(constructor.children) == 1
            and constructor.children[0].kind == "literal"
            and constructor.children[0].literal_value == constant)
    if not equality:
        raise _fail(f"mode {mode} equality mismatch")
    replacement = dataclasses.replace(
        expression, children=(target, target))
    return dataclasses.replace(
        statement,
        children=(dataclasses.replace(
            statement.children[0], expressions=(replacement,)),))


def _rewrite_chain(root: TypedStatement, blend_mode_id: int,
                   middle_id: int) -> TypedStatement:
    modes: list[int] = []

    def rewrite(statement: TypedStatement) -> TypedStatement:
        mode = _guard_mode(statement, blend_mode_id)
        if mode is None or not statement.children:
            raise _fail("blendMode control ancestry mismatch")
        modes.append(mode)
        then = statement.children[0]
        if mode in _SITES:
            then = _rewrite_site(then, mode, middle_id)
        if len(statement.children) == 1:
            children = (then,)
        elif (len(statement.children) == 2
              and statement.children[1].kind == "if"):
            children = (then, rewrite(statement.children[1]))
        else:
            raise _fail("blendMode else-if chain mismatch")
        return dataclasses.replace(statement, children=children)

    result = rewrite(root)
    if tuple(modes) != _MODE_SEQUENCE:
        raise _fail(f"expected exact blendMode sequence {_MODE_SEQUENCE}, got {tuple(modes)}")
    return result


def apply_refract_truthy_vector_noops(program: TypedProgram) -> TypedProgram:
    """Rewrite exactly four truthy typed-array conditions to source-locked no-ops."""
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if (program.key != REFRACT_KEY or program.preprocessor_defines
            or raw_hash != RAW_SOURCE_SHA256
            or normalized_hash != NORMALIZED_SOURCE_SHA256
            or _sha(program.functions) != PRE_FUNCTIONS_SHA256
            or whole_program_fingerprint(program) != PRE_WHOLE_PROGRAM_SHA256
            or _interface_fingerprint(program) != INTERFACE_SHA256):
        raise _fail("source, key, interface, or pre-transform tree mismatch")
    blends = [function for function in program.functions
              if function.name == "blend" and function.body]
    if len(blends) != 1:
        raise _fail("expected one blend definition")
    blend = blends[0]
    if (blend.return_type.display() != "vec3"
            or tuple((parameter.name, parameter.type.display())
                     for parameter in blend.parameters)
            != (("color1", "vec4"), ("color2", "vec4"))
            or len(blend.body) != 6):
        raise _fail("blend signature/body mismatch")
    middle = blend.body[1]
    if (middle.kind != "decl" or len(middle.expressions) != 1
            or middle.expressions[0].kind != "declaration"
            or middle.expressions[0].symbol is None
            or middle.expressions[0].symbol.name != "middle"
            or middle.expressions[0].type.display() != "vec4"
            or middle.expressions[0].children):
        raise _fail("middle declaration mismatch")
    blend_mode = next((item.symbol for item in program.declarations
                       if item.symbol.name == "blendMode"), None)
    if blend_mode is None or blend_mode.type.display() != "int":
        raise _fail("blendMode uniform mismatch")
    rewritten_body = list(blend.body)
    rewritten_body[3] = _rewrite_chain(
        rewritten_body[3], blend_mode.id,
        middle.expressions[0].symbol_id or 0)
    rewritten_blend = dataclasses.replace(blend, body=tuple(rewritten_body))
    functions = tuple(rewritten_blend if function.signature.id == blend.signature.id
                      else function for function in program.functions)
    transformed = dataclasses.replace(program, functions=functions)
    if (_sha(transformed.functions) != POST_FUNCTIONS_SHA256
            or whole_program_fingerprint(transformed) != POST_WHOLE_PROGRAM_SHA256
            or _interface_fingerprint(transformed) != INTERFACE_SHA256):
        raise _fail("post-transform tree mismatch")
    return transformed
