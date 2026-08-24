"""Proof construction for one source-locked discarded local counter statement."""

from __future__ import annotations

from dataclasses import replace

from .typed_ir import (DiscardedLocalCounterProof, TypedExpression,
                       TypedFunction, TypedStatement)


COMPUTE_RANK_KEY = "filter/pixelSort:computeRank"
COMPUTE_RANK_RAW_SHA256 = "6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4"
COMPUTE_RANK_NORMALIZED_SHA256 = "49d716ae2a00b7f24971c08433cde6f484efe4bb70a4e6d7b69050a49f19cf48"
CAPABILITY = "discarded-local-counter-statement-v1"


def _integer_literal(value: TypedExpression) -> int | None:
    if (value.kind == "literal" and value.type.display() == "int"
            and isinstance(value.literal_value, int)):
        return value.literal_value
    return None


def _expressions(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statement_expressions(value: TypedStatement):
    for expression in value.expressions:
        yield from _expressions(expression)
    for child in value.children:
        yield from _statement_expressions(child)


def _clear(value: TypedStatement) -> TypedStatement:
    return replace(value, counter_proof=None,
                   children=tuple(_clear(child) for child in value.children))


def _target_id(value: TypedExpression, symbol_id: int) -> bool:
    return (value.kind == "id" and value.symbol_id == symbol_id
            and value.symbol is not None and value.symbol.id == symbol_id)


def _declaration(statement: TypedStatement, name: str, type_name: str,
                 storage: str) -> TypedExpression | None:
    if statement.kind != "decl" or len(statement.expressions) != 1:
        return None
    value = statement.expressions[0]
    if (value.kind != "declaration" or value.type.display() != type_name
            or value.symbol_id is None or value.symbol is None
            or value.symbol.id != value.symbol_id or value.symbol.name != name
            or value.symbol.storage != storage or value.symbol.type != value.type):
        return None
    return value


def _bound_id(value: TypedExpression, declaration: TypedExpression) -> bool:
    return (declaration.symbol_id is not None and value.kind == "id"
            and value.symbol_id == declaration.symbol_id
            and value.symbol == declaration.symbol and value.type == declaration.type)


def _binary_ids(value: TypedExpression, operator: str,
                left: TypedExpression, right: TypedExpression) -> bool:
    return (value.kind == "binary" and value.type.display() == "bool"
            and value.operator == operator and len(value.children) == 2
            and _bound_id(value.children[0], left)
            and _bound_id(value.children[1], right))


def _attach_main(function: TypedFunction) -> TypedFunction:
    # This capability is deliberately a source-specific proof, not a generic
    # postfix-increment admission. Bind the canonical direct main/loop layout
    # and every stable symbol/operator in the counter's control predicate.
    if len(function.body) != 11:
        return function
    x = _declaration(function.body[2], "x", "int", "local")
    y = _declaration(function.body[3], "y", "int", "local")
    width = _declaration(function.body[4], "width", "int", "local")
    own_luminance = _declaration(function.body[5], "myLum", "float", "local")
    sample_count = _declaration(function.body[6], "NUM_SAMPLES", "int", "const")
    declaration = _declaration(function.body[7], "brighterCount", "int", "local")
    if any(item is None for item in (
            x, y, width, own_luminance, sample_count, declaration)):
        return function
    assert x is not None and y is not None and width is not None
    assert own_luminance is not None and sample_count is not None and declaration is not None
    initializer_statement = function.body[7]
    if (not declaration.symbol.writable or len(declaration.children) != 1
            or _integer_literal(declaration.children[0]) != 0
            or len(sample_count.children) != 1
            or _integer_literal(sample_count.children[0]) != 32):
        return function
    target_id = declaration.symbol_id
    if target_id is None:
        return function

    loop = function.body[8]
    if (loop.kind != "for" or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 4):
        return function
    induction = _declaration(loop.children[0], "s", "int", "local")
    if induction is None or len(induction.children) != 1 or _integer_literal(induction.children[0]) != 0:
        return function
    condition, loop_update = loop.expressions
    if (not _binary_ids(condition, "<", induction, sample_count)
            or loop_update.kind not in {"post", "unary"}
            or loop_update.operator != "++" or len(loop_update.children) != 1
            or not _bound_id(loop_update.children[0], induction)):
        return function

    loop_body = loop.children[1]
    sample_x = _declaration(loop_body.children[0], "sampleX", "int", "local")
    skip = loop_body.children[1]
    other_luminance = _declaration(loop_body.children[2], "otherLum", "float", "local")
    conditional = loop_body.children[3]
    if sample_x is None or other_luminance is None:
        return function
    if (skip.kind != "if" or len(skip.expressions) != 1 or len(skip.children) != 1
            or skip.children[0].kind != "continue"
            or not _binary_ids(skip.expressions[0], "==", sample_x, x)):
        return function
    if (conditional.kind != "if" or len(conditional.expressions) != 1
            or len(conditional.children) != 1
            or conditional.children[0].kind != "block"
            or len(conditional.children[0].children) != 1):
        return function
    update_statement = conditional.children[0].children[0]
    if update_statement.kind != "expr" or len(update_statement.expressions) != 1:
        return function
    update = update_statement.expressions[0]
    if (update.kind != "post" or update.operator != "++" or len(update.children) != 1
            or not _target_id(update.children[0], target_id)):
        return function

    predicate = conditional.expressions[0]
    if (predicate.kind != "binary" or predicate.type.display() != "bool"
            or predicate.operator != "||" or len(predicate.children) != 2):
        return function
    brighter, tie_break = predicate.children
    if not _binary_ids(brighter, ">", other_luminance, own_luminance):
        return function
    if (tie_break.kind != "binary" or tie_break.type.display() != "bool"
            or tie_break.operator != "&&" or len(tie_break.children) != 2):
        return function
    equal_luminance, stable_order = tie_break.children
    if (not _binary_ids(equal_luminance, "==", other_luminance, own_luminance)
            or not _binary_ids(stable_order, "<", sample_x, x)):
        return function

    proof = loop.loop_proof
    if (proof is None or proof.start_value != 0 or proof.bound_value != 32
            or proof.comparison != "<" or proof.update != "++"
            or proof.bound_kind != "local-const-literal" or proof.trip_count != 32
            or proof.lexical_depth != 1 or proof.effective_depth != 1
            or proof.lexical_product != 32 or proof.entrypoint_charge != 32
            or proof.induction_symbol_id != induction.symbol_id
            or proof.induction_symbol_id == target_id):
        return function

    all_expressions = tuple(item for statement in function.body
                            for item in _statement_expressions(statement))
    writes = []
    target_references = []
    float_reads = []
    for expression in all_expressions:
        if _target_id(expression, target_id):
            target_references.append(expression)
        if (expression.kind in {"post", "unary"} and expression.operator in {"++", "--"}
                and expression.children and _target_id(expression.children[0], target_id)):
            writes.append(expression)
        if (expression.kind == "assign" and expression.children
                and _target_id(expression.children[0], target_id)):
            writes.append(expression)
        if (expression.kind == "construct" and expression.type.display() == "float"
                and len(expression.children) == 1
                and _target_id(expression.children[0], target_id)):
            float_reads.append(expression)
    if writes != [update] or len(target_references) != 2 or len(float_reads) != 1:
        return function

    counter_proof = DiscardedLocalCounterProof(
        proof_kind=CAPABILITY,
        main_signature_id=function.signature.id,
        target_symbol_id=target_id,
        target_type="int",
        initializer_symbol_id=target_id,
        initial_value=0,
        initializer_span=initializer_statement.span,
        statement_span=update_statement.span,
        update_span=update.span,
        update_operator="++",
        value_discarded=True,
        conditional_span=conditional.span,
        containing_loop_span=loop.span,
        induction_symbol_id=proof.induction_symbol_id,
        containing_loop_trip_count=proof.trip_count,
        max_updates_per_visit=1,
        lower_bound=0,
        upper_bound=32,
        predicate_profile="otherLum>myLum||(otherLum==myLum&&sampleX<x)",
        sample_x_symbol_id=sample_x.symbol_id or 0,
        x_symbol_id=x.symbol_id or 0,
        other_luminance_symbol_id=other_luminance.symbol_id or 0,
        own_luminance_symbol_id=own_luminance.symbol_id or 0,
        loop_body_statement_count=4,
        skip_conditional_index=1,
        counter_conditional_index=3,
    )

    def annotate(statement: TypedStatement) -> TypedStatement:
        attached = counter_proof if statement is update_statement else None
        return replace(statement, counter_proof=attached,
                       children=tuple(annotate(child) for child in statement.children))

    return replace(function, body=tuple(annotate(statement) for statement in function.body))


def attach_discarded_local_counter_proofs(
        functions: tuple[TypedFunction, ...], key: str) -> tuple[TypedFunction, ...]:
    """Recompute the exact statement proof using typed IR and stable symbols only."""
    clean = tuple(replace(function, body=tuple(_clear(statement)
                                               for statement in function.body))
                  for function in functions)
    if key != COMPUTE_RANK_KEY:
        return clean
    mains = [function for function in clean if function.name == "main" and function.body]
    if len(mains) != 1:
        return clean
    main_id = mains[0].signature.id
    return tuple(_attach_main(function) if function.signature.id == main_id else function
                 for function in clean)
