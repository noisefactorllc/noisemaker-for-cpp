"""Declaration/signature frontier for the pinned GLSL ES corpus.

This module intentionally stops before expression and body analysis.  It is a
strict two-pass collector so later body checking has one immutable, stable
namespace to consume rather than re-discovering declarations per pass.
"""

from __future__ import annotations

from collections import defaultdict
import dataclasses

from .diagnostics import SemanticDiagnostic, SemanticError
from .semantic_types import INT, Type, array, named_type, struct
from .span import SourceSpan, span_at
from .typed_ir import (FunctionSignature, ResourceRequirements, StructDeclaration,
                       StructField, Symbol, TypedDeclaration, TypedFunction,
                       TypedProgram, UniformBlock)
from .body_semantic import BodyAnalyzer
from .constant_expr import evaluate_int_constant
from .loop_proof import (attach_counted_loop_proofs,
                         authenticate_source_global_literal_int,
                         summarize_counted_loop_proofs,
                         validate_source_global_literal_int_program)
from .local_counter_proof import attach_discarded_local_counter_proofs
from .fixed_nine_table_proof import prove_fixed_nine_local_tables
from .fixed_grid_counter_store_proof import prove_fixed_grid_counter_store


def _span(parsed: dict, path: tuple[object, ...], fallback: SourceSpan) -> SourceSpan:
    for candidate_path, candidate in parsed.get("spans", ()):
        if candidate_path == path:
            return candidate
    return fallback


def _diagnostic(code: str, span: SourceSpan, message: str) -> SemanticError:
    return SemanticError((SemanticDiagnostic(code, span, message),))


def _literal_int(expression: object, constants: dict[str, int]) -> int | None:
    return evaluate_int_constant(expression, constants.get)


def _type(name: str, structs: dict[str, Type], extent: object, constants: dict[str, int], span: SourceSpan) -> Type:
    result = named_type(name, structs)
    if result is None:
        raise _diagnostic("E_UNKNOWN_TYPE", span, f"unknown type {name}")
    if extent is not None:
        size = _literal_int(extent, constants)
        if size is None or size <= 0:
            raise _diagnostic("E_ARRAY_SIZE", span, "array dimension must be a positive constant int")
        result = array(result, size)
    return result


def _signature(name: str, return_type: Type, parameters: tuple[Symbol, ...]) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    return (name, return_type.display(), tuple((parameter.direction, parameter.type.display()) for parameter in parameters))


def analyze_program(parsed: dict, program_key: str | None = None, *,
                    source_global_literal_int_profile: str | None = None) -> TypedProgram:
    """Collect and validate the declaration layer, never mutating ``parsed``.

    ``TypedProgram.body_status`` is deliberately ``"not analyzed"``: this
    function makes no expression, lvalue, overload-call, or control-flow claim.
    """
    key = program_key or parsed.get("program_key") or "<program>"
    source = parsed.get("source") or parsed.get("normalized_source") or ""
    ast = parsed.get("ast", parsed)
    whole = span_at(key, source)
    diagnostics: list[SemanticDiagnostic] = []
    next_id = 1
    struct_types: dict[str, Type] = {}
    struct_fields: dict[str, set[str]] = {}
    struct_records: list[StructDeclaration] = []
    uniform_blocks: list[UniformBlock] = []

    # First pass reserves every named struct, allowing fields to reference
    # earlier types without a source-order heuristic.
    for index, node in enumerate(ast["decls"]):
        if node["k"] != "struct":
            continue
        location = _span(parsed, ("decls", index), whole)
        name = node["name"]
        if name in struct_types:
            diagnostics.append(SemanticDiagnostic("E_DUPLICATE_TYPE", location, f"duplicate struct type {name}"))
            continue
        struct_types[name] = struct(next_id, name); next_id += 1
        struct_fields[name] = set()
    if diagnostics:
        raise SemanticError(diagnostics)

    constants: dict[str, int] = {}
    declarations: list[TypedDeclaration] = []
    globals_by_name: dict[str, Symbol] = {}
    uniform_names: list[str] = []
    sampler_names: list[str] = []
    output_names: list[str] = []
    function_records: list[tuple[dict, int, tuple[Symbol, ...], Type, SourceSpan]] = []
    local_type_names: list[str] = []

    def add_global(name: str, typ: Type, storage: str, location: SourceSpan, writable: bool) -> None:
        nonlocal next_id
        if name in globals_by_name:
            diagnostics.append(SemanticDiagnostic("E_DUPLICATE_SYMBOL", location, f"duplicate global symbol {name}"))
            return
        item = Symbol(next_id, name, typ, storage, location, writable); next_id += 1
        globals_by_name[name] = item
        declarations.append(TypedDeclaration(item, typ, location))
        if storage == "uniform":
            uniform_names.append(name)
            if typ.kind == "sampler": sampler_names.append(name)
        if storage == "output": output_names.append(name)

    # Pass two collects global/interface declarations and creates all function
    # parameter records before checking prototypes against definitions.
    for index, node in enumerate(ast["decls"]):
        location = _span(parsed, ("decls", index), whole)
        kind = node["k"]
        if kind == "struct":
            fields = struct_fields[node["name"]]
            typed_fields: list[StructField] = []
            for field_index, field in enumerate(node["fields"]):
                field_type, field_name, extent = field["type"], field["name"], field["array"]
                field_location = _span(parsed, ("decls", index, "fields", field_index), location)
                try:
                    resolved_field_type = _type(field_type, struct_types, extent, constants, field_location)
                except SemanticError as error:
                    diagnostics.extend(error.diagnostics)
                    continue
                duplicate = field_name in fields
                if duplicate:
                    diagnostics.append(SemanticDiagnostic("E_DUPLICATE_FIELD", field_location, f"duplicate field {field_name}"))
                fields.add(field_name)
                if duplicate:
                    continue
                typed_fields.append(StructField(next_id, field_name, resolved_field_type, field_location)); next_id += 1
            struct_records.append(StructDeclaration(struct_types[node["name"]].symbol_id or 0, node["name"], struct_types[node["name"]], tuple(typed_fields), location))
            if node.get("inst"):
                add_global(node["inst"], struct_types[node["name"]], "global", location, True)
        elif kind == "ubo":
            typed_fields: list[StructField] = []
            for member_index, member in enumerate(node["members"]):
                member_location = _span(parsed, ("decls", index, "members", member_index), location)
                try:
                    member_type = _type(member["type"], struct_types, member["array"], constants, member_location)
                    if node.get("inst") is None:
                        add_global(member["name"], member_type, "uniform", member_location, False)
                    typed_fields.append(StructField(next_id, member["name"], member_type, member_location)); next_id += 1
                except SemanticError as error:
                    diagnostics.extend(error.diagnostics)
            block_type = struct(next_id, node["name"]); next_id += 1
            uniform_blocks.append(UniformBlock(block_type.symbol_id or 0, node["name"], node.get("inst"), tuple(typed_fields), location))
            if node.get("inst") is not None:
                add_global(node["inst"], block_type, "uniform_block", location, False)
        elif kind == "decl":
            quals = set(node["quals"])
            for declarator in node["declarators"]:
                try:
                    typ = _type(node["type"], struct_types, declarator["array"], constants, location)
                except SemanticError as error:
                    diagnostics.extend(error.diagnostics); continue
                name = declarator["name"]
                storage = "uniform" if "uniform" in quals else "output" if name in parsed.get("outputs", ()) or "out" in quals else "const" if "const" in quals else "global"
                add_global(name, typ, storage, location, storage not in {"const", "uniform"})
                if "const" in quals and typ == INT and declarator["init"] and (value := _literal_int(declarator["init"], constants)) is not None:
                    constants[name] = value
        elif kind in {"func", "proto"}:
            try:
                return_type = _type(node["ret"], struct_types, None, constants, location)
            except SemanticError as error:
                diagnostics.extend(error.diagnostics); continue
            parameters: list[Symbol] = []
            parameter_names: set[str] = set()
            for parameter_index, parameter in enumerate(node["params"]):
                type_name, name, qualifiers = parameter["type"], parameter["name"], parameter["quals"]
                parameter_location = _span(parsed, ("decls", index, "params", parameter_index), location)
                try:
                    parameter_type = _type(type_name, struct_types, parameter["array"], constants, parameter_location)
                except SemanticError as error:
                    diagnostics.extend(error.diagnostics); continue
                direction = next((qualifier for qualifier in qualifiers if qualifier in {"in", "out", "inout"}), "in")
                parameter_name = name or f"__param_{parameter_index}"
                if parameter_name in parameter_names:
                    diagnostics.append(SemanticDiagnostic("E_DUPLICATE_SYMBOL", parameter_location, f"duplicate parameter {parameter_name}"))
                parameter_names.add(parameter_name)
                # ``in`` governs the call ABI, not mutability of the callee's
                # local parameter variable.  A function may freely update its
                # own by-value input parameter.
                writable = True
                parameters.append(Symbol(next_id, parameter_name, parameter_type, "parameter", parameter_location, writable, direction)); next_id += 1
            function_records.append((node, index, tuple(parameters), return_type, location))

    # Syntax already gave us every nested declaration.  Decode its structural
    # type here, but deliberately do not infer initializer/body expressions.
    def validate_local_declarations(value: object) -> None:
        if isinstance(value, dict):
            if value.get("k") == "decl" and not value.get("top"):
                for declarator in value["declarators"]:
                    try:
                        # Body analysis owns lexical local array extents: a
                        # declaration can depend on a preceding block const.
                        local_type_names.append(_type(value["type"], struct_types, None, constants, whole).display())
                    except SemanticError as error:
                        diagnostics.extend(error.diagnostics)
            for child in value.values():
                validate_local_declarations(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                validate_local_declarations(child)
    validate_local_declarations(ast)

    signatures: dict[tuple[str, str, tuple[tuple[str, str], ...]], tuple[dict, Type, SourceSpan]] = {}
    function_groups: dict[tuple[str, str, tuple[tuple[str, str], ...]], list[tuple[dict, int, tuple[Symbol, ...], Type, SourceSpan]]] = defaultdict(list)
    main_definitions = 0
    for node, index, parameters, return_type, location in function_records:
        signature = _signature(node["name"], return_type, parameters)
        # Same parameter types/directions may not acquire a different return
        # type through a prototype or definition.
        compatible = [record for candidate, record in signatures.items()
                      if candidate[0] == node["name"] and candidate[2] == signature[2]]
        if compatible and any(record[1] != return_type for record in compatible):
            diagnostics.append(SemanticDiagnostic("E_INCOMPATIBLE_SIGNATURE", location, f"incompatible declaration of {node['name']}"))
            continue
        previous = signatures.get(signature)
        if previous and node["k"] == "func" and previous[0]["k"] == "func":
            diagnostics.append(SemanticDiagnostic("E_DUPLICATE_DEFINITION", location, f"duplicate definition of {node['name']}"))
            continue
        if previous is None or node["k"] == "func":
            signatures[signature] = (node, return_type, location)
        function_groups[signature].append((node, index, parameters, return_type, location))
        if node["name"] == "main" and node["k"] == "func":
            main_definitions += 1
            if return_type.display() != "void" or parameters:
                diagnostics.append(SemanticDiagnostic("E_MAIN_SIGNATURE", location, "main must be exactly void main()"))
    if main_definitions != 1:
        diagnostics.append(SemanticDiagnostic("E_MAIN_SIGNATURE", whole, "program must define exactly one void main()"))
    if diagnostics:
        raise SemanticError(diagnostics)
    functions: list[TypedFunction] = []
    signatures_by_name: dict[str, list[FunctionSignature]] = defaultdict(list)
    body_records: list[tuple[dict, FunctionSignature, tuple[Symbol, ...], tuple[object, ...]]] = []
    for signature_key, records in sorted(function_groups.items()):
        definition = next((location for node, _, _, _, location in records if node["k"] == "func"), None)
        prototype_spans = tuple(location for node, _, _, _, location in records if node["k"] == "proto")
        node, index, parameters, return_type, location = records[-1]
        signature = FunctionSignature(next_id, node["name"], return_type, parameters, prototype_spans, definition); next_id += 1
        signatures_by_name[node["name"]].append(signature)
        for occurrence_node, occurrence_index, occurrence_parameters, _, occurrence in records:
            functions.append(TypedFunction(signature, occurrence))
            body_records.append((occurrence_node, signature, occurrence_parameters, ("decls", occurrence_index)))
    # Declaration records remain exactly as Task 7A exposed them; the injected
    # fragment coordinate is a body-only builtin rather than a source interface.
    body_globals = dict(globals_by_name)
    whole_symbol = Symbol(next_id, "gl_FragCoord", named_type("vec4", struct_types) or INT,
                          "builtin", whole, False)
    next_id += 1
    body_globals["gl_FragCoord"] = whole_symbol
    interface_symbols: list[Symbol] = []
    for varying_name, varying_type_name in sorted(parsed.get("varying_types", {}).items()):
        varying_type = named_type(varying_type_name, struct_types)
        if varying_type is None:
            diagnostics.append(SemanticDiagnostic("E_UNKNOWN_TYPE", whole, f"unknown varying type {varying_type_name}"))
            continue
        varying_symbol = Symbol(next_id, varying_name, varying_type, "varying", whole, False)
        body_globals[varying_name] = varying_symbol
        interface_symbols.append(varying_symbol)
        next_id += 1
    body_structs: dict[str, tuple[Type, dict[str, Type]]] = {
        item.name: (item.type, {field.name: field.type for field in item.fields})
        for item in struct_records
    }
    for block in uniform_blocks:
        block_symbol = next((item.symbol for item in declarations if item.symbol.name == block.instance_name), None)
        if block_symbol is not None:
            body_structs[block.block_name] = (block_symbol.type, {field.name: field.type for field in block.fields})
    analyzer = BodyAnalyzer(parsed, key, globals_=body_globals,
                            signatures={name: tuple(items) for name, items in signatures_by_name.items()},
                            structs=body_structs,
                            resources=ResourceRequirements(tuple(uniform_names), tuple(sampler_names), tuple(output_names)),
                            next_id=next_id, constants=constants)
    initializer_by_symbol = analyzer.global_initializers(ast)
    typed_functions = analyzer.functions(body_records)
    if analyzer.diagnostics:
        raise SemanticError(analyzer.diagnostics)
    preprocessor_defines = tuple(parsed.get("preprocessor_defines", ()))
    typed_declarations = tuple(TypedDeclaration(
        item.symbol, item.type, item.span, initializer_by_symbol.get(item.symbol.id))
        for item in declarations)
    typed_functions = attach_counted_loop_proofs(typed_functions, key)
    try:
        source_global_bounds = authenticate_source_global_literal_int(
            key=key, raw_source=parsed.get("raw_source", source), source=source,
            preprocessor_defines=preprocessor_defines,
            declarations=typed_declarations, functions=typed_functions,
            profile=source_global_literal_int_profile)
    except ValueError as error:
        raise _diagnostic("E_SOURCE_GLOBAL_LITERAL_INT", whole, str(error)) from error
    typed_functions = attach_counted_loop_proofs(
        typed_functions, key, source_global_bounds=source_global_bounds)
    typed_functions = attach_discarded_local_counter_proofs(typed_functions, key)
    program = TypedProgram(
        key, source, typed_declarations, typed_functions,
        ResourceRequirements(tuple(uniform_names), tuple(sampler_names), tuple(output_names),
                             analyzer.uses_texture, analyzer.uses_derivatives),
        "analyzed",
        tuple(local_type_names),
        tuple(struct_records),
        tuple(uniform_blocks),
        tuple(interface_symbols),
        (whole_symbol,),
        summarize_counted_loop_proofs(typed_functions),
        parsed.get("raw_source", source),
        preprocessor_defines,
        None,
        None,
    )
    if source_global_literal_int_profile is not None:
        try:
            validate_source_global_literal_int_program(
                program, source_global_literal_int_profile)
        except ValueError as error:
            raise _diagnostic("E_SOURCE_GLOBAL_LITERAL_INT", whole, str(error)) from error
    program = dataclasses.replace(
        program, fixed_nine_table_proof=prove_fixed_nine_local_tables(program))
    return dataclasses.replace(
        program,
        fixed_grid_counter_store_proof=prove_fixed_grid_counter_store(program))
