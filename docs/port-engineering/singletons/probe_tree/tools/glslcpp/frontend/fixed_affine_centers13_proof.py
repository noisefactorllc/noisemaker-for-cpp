"""Exact ownership and affine-index proof for Sacred Geometry's centers table."""

from __future__ import annotations

import dataclasses
import hashlib

from .sacred_geometry_compatibility import (
    INTERFACE_SHA256, NORMALIZED_SOURCE_SHA256, POST_FUNCTION_SHA256,
    POST_WHOLE_PROGRAM_SHA256, PRE_FUNCTION_SHA256,
    PRE_WHOLE_PROGRAM_SHA256, RAW_SOURCE_SHA256, SACRED_KEY, TRANSFORM,
    authenticate_sacred_star_number_division, interface_fingerprint,
    whole_program_fingerprint,
)
from .typed_ir import (
    FixedAffineCenters13Proof, FixedAffineReadSiteProof,
    FixedAffineStoreRegionProof, SacredStarNumberDivisionSiteProof,
    TypedExpression, TypedFunction, TypedProgram, TypedStatement,
)


CAPABILITY = "fixed-affine-centers13-v1"
SOURCE_PROFILE = "sacred-geometry-fixed-affine-centers13-v1"
NUMERIC_PROFILE = "glsl-f32"
CANONICAL_FACTORY_SHA256 = "b4ed8af983d8bda5d48e05d418458c2fc82170f745b021199df7f7095fadb2f2"
CANONICAL_RUNTIME_SHA256 = "e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56"
FRUIT_FUNCTION_SHA256 = "1b41f8dfec8061e8f8f9f81979a8d00fe6f4f1fe350a5a59e3c1d1c53c642535"
FRUIT_BODY_SHA256 = "bdfde2d99556092203fe744475995ea61f6a7a9876eca92c6fefd1a86f56c38b"
MAIN_FUNCTION_SHA256 = "9f8307702faa0f459256108a315cbeaa3ccb2e59d9181f7d6bd622b461009227"
MAIN_BODY_SHA256 = "461de24b340c31ad0b577a18acd6b9e7ec96e483fc814accd14bd4c66c7afbda"

_BINDINGS = (
    "resolution:vec2@1", "tileOffset:vec2@2", "fullResolution:vec2@3",
    "aspect:float@4", "scale:float@5", "rotation:float@6",
    "thickness:float@7", "smoothness:float@8", "geometry:int@9",
    "rings:int@10", "starPoints:int@11", "animation:int@12",
    "speed:float@13", "pulseDepth:float@14", "time:float@15",
    "fgColor:vec3@16", "bgColor:vec3@17", "fragColor:vec4@18",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None:
    if program.key != SACRED_KEY:
        return None
    if (source_hash != RAW_SOURCE_SHA256 or program.preprocessor_defines
            or hashlib.sha256(program.raw_source.encode()).hexdigest()
            != RAW_SOURCE_SHA256
            or hashlib.sha256(program.source.encode()).hexdigest()
            != NORMALIZED_SOURCE_SHA256):
        return "source provenance mismatch for fixed affine centers13"
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


def _expressions(function: TypedFunction) -> tuple[TypedExpression, ...]:
    return tuple(value for statement in function.body
                 for value in _walk_statement(statement)
                 if isinstance(value, TypedExpression))


def _span(value, line: int, column: int, end: int | None = None):
    matches = [item for item in value
               if item.span.start_line == line and item.span.start_column == column
               and (end is None or item.span.end_column == end)]
    if len(matches) != 1:
        raise ValueError(f"{CAPABILITY}: expected one site at {line}:{column}")
    return matches[0]


def _index_site(expressions: tuple[TypedExpression, ...], line: int,
                column: int) -> TypedExpression:
    value = _span(expressions, line, column)
    if (value.kind != "index" or len(value.children) != 2
            or value.children[0].kind != "id"
            or value.children[0].symbol_id != 73):
        raise ValueError(f"{CAPABILITY}: centers index mismatch at {line}:{column}")
    return value


def _int_literal(value: TypedExpression) -> int | None:
    if (value.kind == "literal" and value.type.display() == "int"
            and isinstance(value.literal_value, int)
            and value.literal == str(value.literal_value)):
        return value.literal_value
    return None


def _affine_index(index: TypedExpression,
                  loop: TypedStatement | None) -> tuple[str, int, int, int]:
    value = index.children[1]
    if loop is None:
        literal = _int_literal(value)
        if literal is None:
            raise ValueError(f"{CAPABILITY}: center index is not an integer literal")
        return f"literal:{literal}", literal, literal, 1
    proof = loop.loop_proof
    if (proof is None or proof.start_value != 0 or proof.comparison != "<"
            or proof.update != "++" or proof.trip_count != proof.bound_value):
        raise ValueError(f"{CAPABILITY}: initializer loop is not exact counted form")
    if (value.kind != "binary" or value.operator != "+"
            or len(value.children) != 2):
        raise ValueError(f"{CAPABILITY}: initializer index is not literal+k")
    offset = _int_literal(value.children[0])
    induction = value.children[1]
    if (offset is None or induction.kind != "id"
            or induction.symbol_id != proof.induction_symbol_id):
        raise ValueError(f"{CAPABILITY}: initializer affine identity mismatch")
    lower = offset + proof.start_value
    upper = lower + proof.trip_count - 1
    return (f"{offset}+k@{proof.induction_symbol_id}", lower, upper,
            proof.trip_count)


def _store_region(role: str, statement_index: int, statement: TypedStatement,
                  loop: TypedStatement | None,
                  assignment: TypedExpression) -> FixedAffineStoreRegionProof:
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2):
        raise ValueError(f"{CAPABILITY}: {role} store assignment mismatch")
    index, rhs = assignment.children
    if (index.kind != "index" or len(index.children) != 2
            or index.children[0].kind != "id"
            or index.children[0].symbol_id != 73):
        raise ValueError(f"{CAPABILITY}: {role} store target mismatch")
    profile, lower, upper, count = _affine_index(index, loop)
    proof = loop.loop_proof if loop is not None else None
    return FixedAffineStoreRegionProof(
        role=role, statement_index=statement_index, statement_span=statement.span,
        loop_span=None if loop is None else loop.span,
        induction_symbol_id=None if proof is None else proof.induction_symbol_id,
        loop_start=None if proof is None else proof.start_value,
        loop_bound=None if proof is None else proof.bound_value,
        comparison=None if proof is None else proof.comparison,
        update=None if proof is None else proof.update,
        trip_count=1 if proof is None else proof.trip_count,
        index_span=index.span, index_profile=profile, lower_index=lower,
        upper_index=upper, write_count=count, rhs_span=rhs.span,
        rhs_profile=_sha(rhs),
    )


def _read_site(role: str, index: TypedExpression, loop: TypedStatement,
               control: TypedStatement | None,
               enclosing: TypedExpression) -> FixedAffineReadSiteProof:
    proof = loop.loop_proof
    subscript = index.children[1]
    if (proof is None or subscript.kind != "id"
            or subscript.symbol_id != proof.induction_symbol_id
            or proof.start_value != 0 or proof.bound_value != 13
            or proof.comparison != "<" or proof.update != "++"
            or proof.trip_count != 13):
        raise ValueError(f"{CAPABILITY}: {role} read loop/index mismatch")
    dynamic_count = proof.trip_count
    if control is not None:
        guard = control.expressions[0] if len(control.expressions) == 1 else None
        if (guard is None or guard.kind != "binary" or guard.operator != "<="
                or len(guard.children) != 2
                or tuple((item.kind, item.symbol_id) for item in guard.children)
                != (("id", 89), ("id", 88))
                or len(control.children) != 1
                or control.children[0].kind != "continue"):
            raise ValueError(f"{CAPABILITY}: line pair guard mismatch")
        dynamic_count = proof.trip_count * (proof.trip_count - 1) // 2
    return FixedAffineReadSiteProof(
        role=role, index_span=index.span,
        index_profile=f"{subscript.symbol.name}@{subscript.symbol_id}",
        induction_symbol_id=proof.induction_symbol_id,
        owning_loop_span=loop.span,
        control_span=None if control is None else control.span,
        dynamic_read_count=dynamic_count,
        enclosing_expression_profile=_sha(enclosing),
    )


def prove_fixed_affine_centers13(
        program: TypedProgram) -> FixedAffineCenters13Proof | None:
    if program.key != SACRED_KEY:
        return None
    authenticate_sacred_star_number_division(program, RAW_SOURCE_SHA256)
    if (interface_fingerprint(program) != INTERFACE_SHA256
            or _sha(program.functions) != POST_FUNCTION_SHA256
            or whole_program_fingerprint(program) != POST_WHOLE_PROGRAM_SHA256):
        raise ValueError(f"{CAPABILITY}: transformed tree mismatch")
    if (program.preprocessor_defines or program.structs or program.uniform_blocks
            or program.interface_symbols
            or tuple((item.id, item.name, item.type.display(), item.storage)
                     for item in program.builtin_symbols)
            != ((50, "gl_FragCoord", "vec4", "builtin"),)
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in _BINDINGS[:-1])
            or program.resources.samplers or program.resources.uses_texture
            or program.resources.uses_derivatives
            or program.resources.outputs != ("fragColor",)):
        raise ValueError(f"{CAPABILITY}: interface/resource mismatch")
    bindings = tuple(f"{item.symbol.name}:{item.type.display()}@{item.symbol.id}"
                     for item in program.declarations)
    if bindings != _BINDINGS:
        raise ValueError(f"{CAPABILITY}: binding signature mismatch")
    definitions = [item for item in program.functions if item.body]
    fruit_matches = [item for item in definitions
                     if item.id == 40 and item.name == "fruitMask"]
    main_matches = [item for item in definitions
                    if item.id == 42 and item.name == "main"]
    star_matches = [item for item in definitions
                    if item.id == 46 and item.name == "starPolygonMask"]
    if (len(fruit_matches) != 1 or len(main_matches) != 1
            or len(star_matches) != 1 or len(definitions) != 12):
        raise ValueError(f"{CAPABILITY}: function identity/count mismatch")
    fruit, main, star = fruit_matches[0], main_matches[0], star_matches[0]
    if (_sha(fruit) != FRUIT_FUNCTION_SHA256 or _sha(fruit.body) != FRUIT_BODY_SHA256
            or _sha(main) != MAIN_FUNCTION_SHA256 or _sha(main.body) != MAIN_BODY_SHA256
            or len(fruit.body) != 12
            or tuple((p.id, p.name, p.type.display()) for p in fruit.parameters)
            != ((31, "p", "vec2"), (32, "drawLines", "bool"))):
        raise ValueError(f"{CAPABILITY}: fruit/main profile mismatch")

    values = _expressions(fruit)
    declaration = _span(values, 96, 10, 21)
    if (declaration.kind != "declaration" or declaration.symbol_id != 73
            or declaration.symbol is None or declaration.symbol.name != "centers"
            or declaration.type.display() != "vec2[13]" or declaration.children
            or declaration.symbol.storage != "local"
            or not declaration.symbol.writable):
        raise ValueError(f"{CAPABILITY}: centers declaration mismatch")
    indices = tuple(item for item in values if item.kind == "index"
                    and item.children and item.children[0].kind == "id"
                    and item.children[0].symbol_id == 73)
    expected_sites = ((97, 5), (100, 9), (104, 9), (114, 39),
                      (120, 30), (140, 46), (140, 58))
    if tuple((item.span.start_line, item.span.start_column) for item in indices) != expected_sites:
        raise ValueError(f"{CAPABILITY}: exact centers index census mismatch")
    typed_arrays = tuple(item for item in values
                         if item.type.display() == "vec2[13]")
    base_ids = tuple(item for item in values
                     if item.kind == "id" and item.symbol_id == 73)
    if len(typed_arrays) != 8 or len(base_ids) != 7 or len(indices) != 7:
        raise ValueError(f"{CAPABILITY}: recursive array census mismatch")

    center_assignment = fruit.body[3].expressions[0]
    inner_loop, outer_loop = fruit.body[4], fruit.body[5]
    inner_statement = inner_loop.children[1].children[1]
    outer_statement = outer_loop.children[1].children[1]
    assignments = (center_assignment, inner_statement.expressions[0],
                   outer_statement.expressions[0])
    if any(item.kind != "assign" or item.operator != "="
           or len(item.children) != 2 for item in assignments):
        raise ValueError(f"{CAPABILITY}: initializer assignment mismatch")
    store_regions = (
        _store_region("center", 3, fruit.body[3], None, assignments[0]),
        _store_region("inner", 4, inner_statement, inner_loop, assignments[1]),
        _store_region("outer", 5, outer_statement, outer_loop, assignments[2]),
    )
    store_summary = tuple(
        (item.role, item.statement_index, item.induction_symbol_id,
         item.loop_start, item.loop_bound, item.comparison, item.update,
         item.trip_count, item.index_profile, item.lower_index,
         item.upper_index, item.write_count, item.index_span.start_line,
         item.index_span.start_column, item.rhs_profile)
        for item in store_regions)
    if store_summary != (
        ("center", 3, None, None, None, None, None, 1, "literal:0",
         0, 0, 1, 97, 5,
         "b4192d798e6aa86813402556ac424648d3cec31bdbb9ccae290bb3333ae71460"),
        ("inner", 4, 74, 0, 6, "<", "++", 6, "1+k@74",
         1, 6, 6, 100, 9,
         "afcc88b6f4d46a9c142ac22bb405b1e889b746a55efeba0571eed154f2b08868"),
        ("outer", 5, 76, 0, 6, "<", "++", 6, "7+k@76",
         7, 12, 6, 104, 9,
         "82967ef419b7cdcb50c973bc75bd0de6a7d37cbd31eab59889ecd35579771b21"),
    ):
        raise ValueError(f"{CAPABILITY}: initializer fact reconstruction mismatch")
    circle_loop = fruit.body[9]
    line_guard = fruit.body[10]
    outer_line_loop = line_guard.children[0].children[2]
    inner_line_loop = outer_line_loop.children[1].children[0]
    pair_guard = inner_line_loop.children[1].children[0]
    circle_origin_enclosing = _span(values, 114, 15, 50)
    circle_distance_enclosing = _span(values, 120, 15, 51)
    line_enclosing = _span(values, 140, 23, 69)
    read_sites = (
        _read_site("circle-origin", indices[3], circle_loop, None,
                   circle_origin_enclosing),
        _read_site("circle-distance", indices[4], circle_loop, None,
                   circle_distance_enclosing),
        _read_site("line-left", indices[5], outer_line_loop, pair_guard,
                   line_enclosing),
        _read_site("line-right", indices[6], inner_line_loop, pair_guard,
                   line_enclosing),
    )
    read_summary = tuple(
        (item.role, item.index_span.start_line, item.index_span.start_column,
         item.index_profile, item.induction_symbol_id,
         item.owning_loop_span.start_line,
         None if item.control_span is None else item.control_span.start_line,
         item.dynamic_read_count, item.enclosing_expression_profile)
        for item in read_sites)
    if read_summary != (
        ("circle-origin", 114, 39, "i@81", 81, 113, None, 13,
         "fe857f63689a36f1a7ac45c612f74f991455dc0e80e232470c66b9705b36572a"),
        ("circle-distance", 120, 30, "i@81", 81, 113, None, 13,
         "1defe8dd202804628f5018dff5d82d8f510af36e67ba193ee9ff6c998e7a68a5"),
        ("line-left", 140, 46, "i@88", 88, 137, 139, 78,
         "23c2caeec7badf25809db005d5d3b7ca665fd8ba0b8bfd50f81955eff1f61ae5"),
        ("line-right", 140, 58, "j@89", 89, 138, 139, 78,
         "23c2caeec7badf25809db005d5d3b7ca665fd8ba0b8bfd50f81955eff1f61ae5"),
    ):
        raise ValueError(f"{CAPABILITY}: read/control fact reconstruction mismatch")
    written_sets = tuple(set(range(region.lower_index, region.upper_index + 1))
                         for region in store_regions)
    initialization_complete = set().union(*written_sets) == set(range(13))
    write_sets_disjoint = sum(len(item) for item in written_sets) == len(
        set().union(*written_sets))
    store_lines = tuple(region.index_span.start_line for region in store_regions)
    read_lines = tuple(site.index_span.start_line for site in read_sites)
    initialization_dominates_reads = max(store_lines) < min(read_lines)
    no_post_read_writes = all(item.span.start_line < min(read_lines)
                              for item in indices[:3])
    no_alias_copy_escape = (
        len(typed_arrays) == 8 and len(base_ids) == 7
        and all(item is declaration or item.kind == "id" for item in typed_arrays)
        and all(any(item is index.children[0] for index in indices)
                for item in base_ids)
        and not any(item.kind in {"call", "construct", "assign", "return"}
                    and item.type.display() == "vec2[13]" for item in values)
    )
    if not (initialization_complete and write_sets_disjoint
            and initialization_dominates_reads and no_post_read_writes
            and no_alias_copy_escape
            and sum(region.write_count for region in store_regions) == 13
            and sum(site.dynamic_read_count for site in read_sites[:2]) == 26
            and sum(site.dynamic_read_count for site in read_sites[2:]) == 156):
        raise ValueError(f"{CAPABILITY}: ownership/work reconstruction mismatch")
    loop = program.counted_loop_proof
    if (loop is None or (loop.loop_count, loop.unproved_loop_count,
                         loop.max_effective_depth, loop.max_lexical_product,
                         loop.entrypoint_charge, loop.call_graph_acyclic)
            != (9, 0, 2, 169, 207, True)):
        raise ValueError(f"{CAPABILITY}: counted-loop profile mismatch")
    star_values = _expressions(star)
    site = SacredStarNumberDivisionSiteProof(
        transform=TRANSFORM, function_signature_id=46,
        induction_symbol_id=106, divisor_symbol_id=37, local_symbol_id=107,
        declaration_span=_span(star_values, 260, 13, 44).span,
        division_span=_span(star_values, 260, 29, 39).span,
        multiplication_span=_span(star_values, 260, 29, 44).span,
        subtraction_span=_span(star_values, 260, 18, 44).span,
        consumption_span=_span(star_values, 262, 30, 31).span,
        pre_function_sha256=PRE_FUNCTION_SHA256,
        post_function_sha256=POST_FUNCTION_SHA256,
        pre_whole_program_sha256=PRE_WHOLE_PROGRAM_SHA256,
        post_whole_program_sha256=POST_WHOLE_PROGRAM_SHA256,
    )
    call_routing_profile = _sha(main)
    draw_lines_guard_profile = _sha(line_guard)
    if (call_routing_profile != MAIN_FUNCTION_SHA256
            or draw_lines_guard_profile
            != "0eef7a910e92d8f9d010d54c68bb11cbd24492b24b14bdccb5f5a866ba84650d"):
        raise ValueError(f"{CAPABILITY}: call routing/guard mismatch")
    return FixedAffineCenters13Proof(
        proof_kind=CAPABILITY, key=SACRED_KEY, source_profile=SOURCE_PROFILE,
        numeric_profile=NUMERIC_PROFILE, raw_source_sha256=RAW_SOURCE_SHA256,
        normalized_source_sha256=NORMALIZED_SOURCE_SHA256,
        canonical_factory_sha256=CANONICAL_FACTORY_SHA256,
        canonical_runtime_sha256=CANONICAL_RUNTIME_SHA256,
        interface_sha256=INTERFACE_SHA256,
        transformed_function_sha256=POST_FUNCTION_SHA256,
        transformed_whole_program_sha256=POST_WHOLE_PROGRAM_SHA256,
        define_contract=(), binding_signature=_BINDINGS, output_symbol_id=18,
        output_symbol_name="fragColor", logical_route="color->outputTex",
        compatibility_site=site, fruit_signature_id=40,
        fruit_body_profile=FRUIT_BODY_SHA256, main_signature_id=42,
        main_control_profile=MAIN_BODY_SHA256, symbol_id=73,
        symbol_name="centers", array_type="vec2[13]", element_type="vec2",
        extent=13, native_alias="Centers13", declaration_statement_index=2,
        declaration_span=declaration.span, store_regions=store_regions,
        read_sites=read_sites, call_routing_profile=call_routing_profile,
        draw_lines_guard_profile=draw_lines_guard_profile, array_declaration_count=1,
        array_typed_expression_count=8, array_base_identifier_count=7,
        index_expression_count=7, static_store_site_count=3,
        dynamic_store_count=13, static_read_site_count=4,
        circle_read_count=26, line_endpoint_read_count=156,
        maximum_dynamic_read_count=sum(site.dynamic_read_count
                                       for site in read_sites),
        initialization_complete=initialization_complete,
        write_sets_disjoint=write_sets_disjoint,
        initialization_dominates_reads=initialization_dominates_reads,
        no_post_read_writes=no_post_read_writes,
        no_alias_copy_escape=no_alias_copy_escape,
        loop_count=9, unproved_loop_count=0, max_effective_depth=2,
        max_lexical_product=169, entrypoint_charge=207,
        call_graph_acyclic=True, table_payload_bytes=104,
    )


def attach_fixed_affine_centers13_proof(program: TypedProgram) -> TypedProgram:
    base = dataclasses.replace(program, fixed_affine_centers13_proof=None)
    return dataclasses.replace(
        base, fixed_affine_centers13_proof=prove_fixed_affine_centers13(base))
