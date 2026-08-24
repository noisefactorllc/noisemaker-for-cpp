"""Exact ownership and ABI proof for the pinned Refract nine-tap arrays."""

from __future__ import annotations

import dataclasses
import hashlib

from .span import SourceSpan, span_at
from .typed_ir import (
    FixedArrayInParameterProof,
    FixedArrayOwnedTableProof,
    FixedArrayParameterProof,
    RefractCompatibilitySiteProof,
    TypedExpression,
    TypedFunction,
    TypedProgram,
    TypedStatement,
)


CAPABILITY = "fixed-array-in-parameter-v1"
REFRACT_KEY = "classicNoisedeck/refract:refract"
SOURCE_PROFILE = "refract-fixed-array-in-parameter-v1"
RAW_SOURCE_SHA256 = "d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2"
NORMALIZED_SOURCE_SHA256 = "bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e"
CANONICAL_FACTORY_SHA256 = "b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6"
INTERFACE_SHA256 = "36d7815ce5aa9efedf3144e199ae7b49dc5819c751475b815708424269033229"
TYPED_IR_SHA256 = "4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188"
WHOLE_PROGRAM_SHA256 = "93329ab73d54ff1eb3b8ec43da8570365d58de8caaa1a36252ef1ad30a709de2"

_BINDINGS = (
    "inputTex:sampler2D", "resolution:vec2", "tileOffset:vec2",
    "fullResolution:vec2", "time:float", "mode:int", "amount:float",
    "direction:float", "blendMode:int", "mixAmt:float", "wrap:int",
)
_CALLER_PROFILES = (
    (39, "derivX", 57, "deriv_x",
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (40, "derivY", 60, "deriv_y",
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
)
_COMPATIBILITY = {
    # mode: source id, equality constant, false builtin, predicate offsets,
    # false-arm offsets
    2: (34, 0.0, "max", (3004, 3023), (3036, 3086)),
    3: (34, 1.0, "min", (3148, 3167), (3180, 3219)),
    7: (34, 1.0, "min", (3542, 3561), (3574, 3622)),
    15: (33, 1.0, "min", (4544, 4563), (4576, 4624)),
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
        program.fixed_nine_table_proof,
        program.fixed_grid_counter_store_proof,
    ))


def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None:
    if program.key != REFRACT_KEY:
        return None
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if (program.preprocessor_defines or raw_hash != RAW_SOURCE_SHA256
            or normalized_hash != NORMALIZED_SOURCE_SHA256
            or source_hash != RAW_SOURCE_SHA256):
        return "source provenance mismatch for fixed-array input parameter"
    return None


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    yield value
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _all_expressions(program: TypedProgram) -> tuple[TypedExpression, ...]:
    values: list[TypedExpression] = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if isinstance(value, TypedExpression):
                    values.append(value)
    return tuple(values)


def _definition(program: TypedProgram, signature_id: int, name: str,
                body_count: int) -> TypedFunction | None:
    matches = [function for function in program.functions
               if function.signature.id == signature_id and function.name == name
               and function.body]
    if len(matches) != 1 or len(matches[0].body) != body_count:
        return None
    return matches[0]


def _declaration(statement: TypedStatement, symbol_id: int, name: str,
                 type_name: str) -> TypedExpression | None:
    if (statement.kind != "decl" or len(statement.expressions) != 1
            or statement.children):
        return None
    value = statement.expressions[0]
    if (value.kind != "declaration" or value.symbol is None
            or value.symbol_id != symbol_id or value.symbol.id != symbol_id
            or value.symbol.name != name or value.type.display() != type_name
            or value.symbol.type != value.type or value.symbol.storage != "local"
            or not value.symbol.writable):
        return None
    return value


def _literal_int(value: TypedExpression, expected: int) -> bool:
    return (value.kind == "literal" and value.type.display() == "int"
            and value.literal_value == expected and value.literal == str(expected))


def _number(value: TypedExpression) -> float | None:
    if (value.kind == "literal" and value.type.display() == "float"
            and isinstance(value.literal_value, float)):
        return value.literal_value
    if (value.kind == "unary" and value.operator == "-"
            and len(value.children) == 1):
        child = value.children[0]
        if (child.kind == "literal" and child.type.display() == "float"
                and isinstance(child.literal_value, float)):
            return -child.literal_value
    return None


def _literal_store(statement: TypedStatement, symbol_id: int,
                   index: int) -> tuple[TypedExpression, TypedExpression] | None:
    if (statement.kind != "expr" or len(statement.expressions) != 1
            or statement.children):
        return None
    assignment = statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2):
        return None
    target, value = assignment.children
    if (target.kind != "index" or len(target.children) != 2
            or target.children[0].kind != "id"
            or target.children[0].symbol_id != symbol_id
            or not _literal_int(target.children[1], index)):
        return None
    return target, value


def _caller_table(function: TypedFunction, symbol_id: int, name: str,
                  expected_values: tuple[float, ...]) -> tuple[
                      FixedArrayOwnedTableProof, TypedExpression] | None:
    declaration = _declaration(function.body[1], symbol_id, name, "float[9]")
    if declaration is None or declaration.children:
        return None
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    values: list[float] = []
    for index, statement in enumerate(function.body[2:11]):
        store = _literal_store(statement, symbol_id, index)
        if store is None:
            return None
        target, rhs = store
        number = _number(rhs)
        if number is None:
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
        values.append(number)
    if tuple(values) != expected_values:
        return None
    call_declaration = _declaration(
        function.body[11], 58 if function.id == 39 else 61,
        "s1" if function.id == 39 else "s2", "vec3")
    if call_declaration is None or len(call_declaration.children) != 1:
        return None
    call = call_declaration.children[0]
    if (call.kind != "call" or call.signature_id != 38
            or call.callee != "convolve" or len(call.children) != 3
            or call.children[1].kind != "id"
            or call.children[1].symbol_id != symbol_id):
        return None
    return (FixedArrayOwnedTableProof(
        role=name, owner_signature_id=function.id, symbol_id=symbol_id,
        symbol_name=name, array_type="float[9]", element_type="float",
        extent=9, native_alias="Kernel9", declaration_statement_index=1,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(range(2, 11)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=tuple(values),
        induction_read_spans=(),
    ), call)


def _offset_component(value: TypedExpression, steps_id: int) -> str | None:
    if (value.kind == "literal" and value.type.display() == "float"
            and value.literal_value == 0.0):
        return "0"
    sign = ""
    inner = value
    if value.kind == "unary" and value.operator == "-" and len(value.children) == 1:
        sign = "-"
        inner = value.children[0]
    if (inner.kind != "swizzle" or inner.member not in ("x", "y")
            or len(inner.children) != 1 or inner.children[0].kind != "id"
            or inner.children[0].symbol_id != steps_id):
        return None
    return sign + inner.member


def _offset_table(function: TypedFunction, induction_id: int) -> FixedArrayOwnedTableProof | None:
    declaration = _declaration(function.body[2], 51, "offset", "vec2[9]")
    if declaration is None or declaration.children:
        return None
    expected = (
        ("-x", "-y"), ("0", "-y"), ("x", "-y"),
        ("-x", "0"), ("0", "0"), ("x", "0"),
        ("-x", "y"), ("0", "y"), ("x", "y"),
    )
    store_spans: list[SourceSpan] = []
    index_spans: list[SourceSpan] = []
    for index, statement in enumerate(function.body[3:12]):
        store = _literal_store(statement, 51, index)
        if store is None:
            return None
        target, rhs = store
        if (rhs.kind != "construct" or rhs.type.display() != "vec2"
                or rhs.constructor_type is None
                or rhs.constructor_type.display() != "vec2"
                or len(rhs.children) != 2
                or tuple(_offset_component(item, 50) for item in rhs.children)
                != expected[index]):
            return None
        store_spans.append(statement.span)
        index_spans.append(target.span)
    reads = tuple(value.span for statement in function.body
                  for value in _walk_statement(statement)
                  if isinstance(value, TypedExpression)
                  and value.kind == "index" and len(value.children) == 2
                  and value.children[0].kind == "id"
                  and value.children[0].symbol_id == 51
                  and value.children[1].kind == "id"
                  and value.children[1].symbol_id == induction_id)
    if len(reads) != 1:
        return None
    return FixedArrayOwnedTableProof(
        role="offset", owner_signature_id=function.id, symbol_id=51,
        symbol_name="offset", array_type="vec2[9]", element_type="vec2",
        extent=9, native_alias="Offsets9", declaration_statement_index=2,
        declaration_span=declaration.span,
        literal_store_statement_indices=tuple(range(3, 12)),
        literal_store_spans=tuple(store_spans),
        literal_index_spans=tuple(index_spans),
        literal_indices=tuple(range(9)), number_values=None,
        induction_read_spans=reads,
    )


def _compatibility_sites(program: TypedProgram,
                         blend: TypedFunction) -> tuple[RefractCompatibilitySiteProof, ...] | None:
    statement = blend.body[3]
    sites: list[RefractCompatibilitySiteProof] = []
    modes: list[int] = []
    while True:
        if (statement.kind != "if" or len(statement.expressions) != 1
                or not statement.children):
            return None
        guard = statement.expressions[0]
        if (guard.kind != "binary" or guard.operator != "=="
                or len(guard.children) != 2):
            return None
        literals = [item for item in guard.children
                    if item.kind == "literal" and isinstance(item.literal_value, int)]
        ids = [item for item in guard.children
               if item.kind == "id" and item.symbol_id == 9]
        if len(literals) != 1 or len(ids) != 1:
            return None
        mode = literals[0].literal_value
        modes.append(mode)
        if mode in _COMPATIBILITY:
            block = statement.children[0]
            if (block.kind != "block" or len(block.children) != 1
                    or block.children[0].kind != "expr"
                    or len(block.children[0].expressions) != 1):
                return None
            assignment = block.children[0].expressions[0]
            if (assignment.kind != "assign" or assignment.operator != "="
                    or len(assignment.children) != 2
                    or assignment.children[0].kind != "id"
                    or assignment.children[0].symbol_id != 47
                    or assignment.children[1].kind != "id"
                    or assignment.children[1].symbol_id != 47):
                return None
            source_id, constant, builtin, condition_offsets, false_offsets = _COMPATIBILITY[mode]
            sites.append(RefractCompatibilitySiteProof(
                blend_mode=mode, guard_span=guard.span,
                assignment_statement_span=block.children[0].span,
                assignment_span=assignment.span, target_symbol_id=47,
                source_symbol_id=source_id, equality_constant=constant,
                false_builtin=builtin,
                original_condition_span=span_at(
                    REFRACT_KEY, program.source, *condition_offsets),
                original_false_span=span_at(
                    REFRACT_KEY, program.source, *false_offsets),
                transformed_rhs_span=assignment.children[1].span,
            ))
        if len(statement.children) == 1:
            break
        if len(statement.children) != 2 or statement.children[1].kind != "if":
            return None
        statement = statement.children[1]
    if tuple(modes) != (0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18):
        return None
    return tuple(sites) if tuple(item.blend_mode for item in sites) == (2, 3, 7, 15) else None


def _mode_one(main: TypedFunction) -> tuple[SourceSpan, tuple[SourceSpan, ...]] | None:
    outer = main.body[8]
    if (outer.kind != "if" or len(outer.children) != 2
            or outer.children[1].kind != "if"):
        return None
    mode_one = outer.children[1]
    guard = mode_one.expressions[0] if len(mode_one.expressions) == 1 else None
    if (guard is None or guard.kind != "binary" or guard.operator != "=="
            or len(guard.children) != 2
            or not any(item.kind == "id" and item.symbol_id == 6 for item in guard.children)
            or not any(_literal_int(item, 1) for item in guard.children)
            or len(mode_one.children) != 1 or mode_one.children[0].kind != "block"
            or len(mode_one.children[0].children) != 2):
        return None
    calls: list[TypedExpression] = []
    for statement, signature_id, name in zip(
            mode_one.children[0].children, (39, 40), ("derivX", "derivY")):
        matches = [value for value in _walk_statement(statement)
                   if isinstance(value, TypedExpression)
                   and value.kind == "call" and value.signature_id == signature_id
                   and value.callee == name]
        if (len(matches) != 1 or len(matches[0].children) != 3
                or matches[0].children[2].kind != "literal"
                or matches[0].children[2].literal_value is not False):
            return None
        calls.append(matches[0])
    return mode_one.span, tuple(item.span for item in calls)


def prove_fixed_array_in_parameter(
        program: TypedProgram) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact transformed, pinned Refract program."""
    if program.key != REFRACT_KEY:
        return None
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines or raw_hash != RAW_SOURCE_SHA256
            or normalized_hash != NORMALIZED_SOURCE_SHA256
            or typed_hash != TYPED_IR_SHA256
            or interface_hash != INTERFACE_SHA256
            or whole_hash != WHOLE_PROGRAM_SHA256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in _BINDINGS)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != _BINDINGS:
        return None

    blend = _definition(program, 35, "blend", 6)
    convolve = _definition(program, 38, "convolve", 17)
    deriv_x = _definition(program, 39, "derivX", 13)
    deriv_y = _definition(program, 40, "derivY", 13)
    main = _definition(program, 42, "main", 14)
    if None in (blend, convolve, deriv_x, deriv_y, main):
        return None
    assert blend is not None and convolve is not None
    assert deriv_x is not None and deriv_y is not None and main is not None

    compatibility = _compatibility_sites(program, blend)
    if compatibility is None:
        return None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != ((18, "uv", "vec2", "in"),
                (19, "kernel", "float[9]", "in"),
                (20, "divide", "bool", "in"))):
        return None
    loop = convolve.body[14]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.trip_count, loop_proof.lexical_depth,
         loop_proof.effective_depth, loop_proof.lexical_product,
         loop_proof.entrypoint_charge)
            != (54, 0, 9, "<", "++", 9, 1, 1, 9, 18)):
        return None
    offset = _offset_table(convolve, 54)
    if offset is None:
        return None

    caller_results = tuple(
        _caller_table(function, symbol_id, name, values)
        for function, (_, _, symbol_id, name, values) in zip(
            (deriv_x, deriv_y), _CALLER_PROFILES))
    if any(item is None for item in caller_results):
        return None
    callers = tuple(item[0] for item in caller_results if item is not None)
    direct_calls = tuple(item[1] for item in caller_results if item is not None)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 19
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 54)
    if len(parameter_reads) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=38, parameter_ordinal=1, symbol_id=19,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )
    mode = _mode_one(main)
    if mode is None:
        return None

    expressions = _all_expressions(program)
    array_ids = {19, 51, 57, 60}
    array_parameters = tuple(
        item for function in program.functions for item in function.parameters
        if item.type.kind == "array")
    array_declarations = tuple(
        item for item in expressions
        if item.kind == "declaration" and item.type.kind == "array")
    array_expressions = tuple(item for item in expressions if item.type.kind == "array")
    array_identifiers = tuple(
        item for item in expressions if item.kind == "id"
        and item.type.kind == "array")
    indexes = tuple(item for item in expressions if item.kind == "index")
    literal_stores = tuple(
        item for item in expressions
        if item.kind == "assign" and item.operator == "=" and item.children
        and item.children[0].kind == "index"
        and len(item.children[0].children) == 2
        and item.children[0].children[0].kind == "id"
        and item.children[0].children[0].symbol_id in array_ids
        and item.children[0].children[1].kind == "literal")
    induction_reads = tuple(
        item for item in indexes if len(item.children) == 2
        and item.children[0].kind == "id"
        and item.children[0].symbol_id in array_ids
        and item.children[1].kind == "id"
        and item.children[1].symbol_id == 54)
    whole_arguments = tuple(item.children[1] for item in direct_calls)
    array_calls = tuple(
        item for item in expressions if item.kind == "call"
        and any(child.type.kind == "array" for child in item.children))
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != (1, 3, 35, 32, 27, 3, 30, 2, 2)
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != array_ids
            or {item.symbol_id for item in array_identifiers} != array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=SOURCE_PROFILE,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=CANONICAL_FACTORY_SHA256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=compatibility,
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=54,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=18,
        main_signature_id=42, mode_one_span=mode[0],
        main_derivative_call_spans=mode[1],
        array_parameter_count=1, array_declaration_count=3,
        array_typed_expression_count=35,
        array_identifier_reference_count=32, literal_store_count=27,
        induction_read_count=3, index_expression_count=30,
        whole_array_argument_count=2, array_call_count=2,
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        caller_tables_never_simultaneously_live=True,
        parameter_read_only_and_synchronous=True,
        mode_zero_array_free=True, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )


def attach_fixed_array_in_parameter_proof(program: TypedProgram) -> TypedProgram:
    base = dataclasses.replace(program, fixed_array_in_parameter_proof=None)
    return dataclasses.replace(
        base, fixed_array_in_parameter_proof=prove_fixed_array_in_parameter(base))
