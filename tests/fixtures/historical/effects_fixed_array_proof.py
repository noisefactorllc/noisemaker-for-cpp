_EFFECTS_DEFINES = (
    PreprocessorDefine("EFFECT", "int", "0"),
    PreprocessorDefine("FLIP", "int", "0"),
)

_EFFECTS_BINDINGS = (
    "inputTex:sampler2D", "resolution:vec2", "tileOffset:vec2",
    "fullResolution:vec2", "renderScale:float", "time:float",
    "effectAmt:float", "scaleAmt:float", "rotation:float", "offsetX:float",
    "offsetY:float", "intensity:float", "saturation:float",
)

_EFFECTS_ARRAY_IDS = frozenset(
    {15, 16, 17, 18, 19, 20, 21, 42, 151, 157, 158, 179, 180, 202, 203,
     210, 211})

_EFFECTS_CENSUS = (1, 9, 164, 155, 144, 3, 147, 8, 8)

_EFFECTS_REACHABLE = ("brightnessContrast", "loadKernels", "main", "map",
                      "offsets", "periodicFunction", "rotate2D", "saturate")

_EFFECTS_PARAMETERS = (
    (41, "uv", "vec2", "in"),
    (42, "kernel", "float[9]", "in"),
    (43, "divide", "bool", "in"),
)

_EFFECTS_LOOP_PROOF = (
    154, 0, 9, "<", "++", "literal", 9, 1, 1, 9, 0,
)

_EFFECTS_OFFSET_SYMBOL_ID = 151

_EFFECTS_OFFSET_STEPS_ID = 150

_EFFECTS_CALLER_TABLES = (
    (71, "derivatives", 25, 157, "deriv_x", 21,
     (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0)),
    (71, "derivatives", 25, 158, "deriv_y", 22,
     (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0)),
    (90, "sobel", 25, 210, "sobel_x", 21, _SOBEL_X),
    (90, "sobel", 25, 211, "sobel_y", 22, _SOBEL_Y),
    (79, "outline", 26, 179, "sobel_x", 21, _SOBEL_X),
    (79, "outline", 26, 180, "sobel_y", 22, _SOBEL_Y),
    (89, "shadow", 29, 202, "sobel_x", 21, _SOBEL_X),
    (89, "shadow", 29, 203, "sobel_y", 22, _SOBEL_Y),
)

def _prove_effects(program: TypedProgram,
                   profile: _Profile) -> FixedArrayInParameterProof | None:
    """Return a proof only for the exact pinned, EFFECT=0 effects program.

    Structurally the cellRefract/kaleido convolve family under its own
    symbol ids (SEVEN globals 15-21, parameter 42, offset table 151,
    induction 154): the same caller-table payloads, the same EFFECT=0
    collapse witness (`convolutionEffect` reduced to `return color;`, which
    is what makes all seven globals write-only), the same shadow-at-0/10
    quirk.  The measured differences frozen here are the two-define contract
    (EFFECT/FLIP), the eight-function reachable set, and the family's first
    SEVEN-array whole-program census (144 literal stores over 17 array ids
    -- never shared with a sibling key).
    """
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    typed_hash = _sha(program.functions)
    interface_hash = _interface_fingerprint(program)
    whole_hash = _whole_program_fingerprint(program)
    if (program.preprocessor_defines != profile.preprocessor_defines
            or raw_hash != profile.raw_source_sha256
            or normalized_hash != profile.normalized_source_sha256
            or typed_hash != profile.typed_ir_sha256
            or interface_hash != profile.interface_sha256
            or whole_hash != profile.whole_program_sha256
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.body_status != "analyzed"
            or program.structs or program.uniform_blocks
            or program.resources.uniforms != tuple(item.split(":", 1)[0]
                                                   for item in profile.binding_signature)
            or program.resources.samplers != ("inputTex",)
            or program.resources.outputs != ("fragColor",)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    binding_signature = tuple(
        f"{item.symbol.name}:{item.type.display()}"
        for item in program.declarations if item.symbol.storage == "uniform")
    if binding_signature != profile.binding_signature:
        return None

    convolve = _definition(program, 70, "convolve", 16)
    main = _definition(program, 76, "main", 23)
    collapsed = _definition(program, 69, "convolutionEffect", 1)
    if None in (convolve, main, collapsed):
        return None
    assert convolve is not None and main is not None and collapsed is not None
    if (convolve.return_type.display() != "vec3"
            or tuple((item.id, item.name, item.type.display(), item.direction)
                     for item in convolve.parameters)
            != _EFFECTS_PARAMETERS):
        return None
    loop = convolve.body[13]
    if (loop.kind != "for" or loop.loop_proof is None
            or len(loop.expressions) != 2 or len(loop.children) != 2
            or loop.children[1].kind != "block"
            or len(loop.children[1].children) != 3):
        return None
    loop_proof = loop.loop_proof
    if ((loop_proof.induction_symbol_id, loop_proof.start_value,
         loop_proof.bound_value, loop_proof.comparison, loop_proof.update,
         loop_proof.bound_kind, loop_proof.trip_count,
         loop_proof.lexical_depth, loop_proof.effective_depth,
         loop_proof.lexical_product, loop_proof.entrypoint_charge)
            != _EFFECTS_LOOP_PROOF):
        return None
    # Bind the induction/trip contract to the statements the proof summarizes:
    # `int i = 0;`, `i < 9;` and `i++` with the frozen induction symbol.
    initializer, condition, update = (loop.children[0], *loop.expressions)
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.children
            or initializer.expressions[0].kind != "declaration"
            or initializer.expressions[0].symbol_id != 154
            or len(initializer.expressions[0].children) != 1
            or not _literal_int(initializer.expressions[0].children[0], 0)
            or condition.kind != "binary" or condition.operator != "<"
            or len(condition.children) != 2
            or condition.children[0].kind != "id"
            or condition.children[0].symbol_id != 154
            or not _literal_int(condition.children[1], 9)
            or update.kind != "post" or update.operator != "++"
            or len(update.children) != 1
            or update.children[0].kind != "id"
            or update.children[0].symbol_id != 154):
        return None

    offset = _cellrefract_offset_table(
        convolve, owner_signature_id=70, symbol_id=_EFFECTS_OFFSET_SYMBOL_ID,
        steps_id=_EFFECTS_OFFSET_STEPS_ID, induction_id=154)
    if offset is None:
        return None

    caller_results = []
    for (owner_id, owner_name, body_count, symbol_id, name, call_index,
         values) in _EFFECTS_CALLER_TABLES:
        owner = _definition(program, owner_id, owner_name, body_count)
        if owner is None:
            return None
        table = _cellrefract_caller_table(
            program, owner, symbol_id, name, call_index, values,
            convolve_signature_id=70)
        if table is None:
            return None
        caller_results.append(table)
    callers = tuple(item[0] for item in caller_results)
    direct_calls = tuple(item[1] for item in caller_results)

    parameter_reads = tuple(
        value.span for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "index"
        and len(value.children) == 2 and value.children[0].kind == "id"
        and value.children[0].symbol_id == 42
        and value.children[1].kind == "id"
        and value.children[1].symbol_id == 154)
    if len(parameter_reads) != 2:
        return None
    kernel_references = tuple(
        value for statement in convolve.body
        for value in _walk_statement(statement)
        if isinstance(value, TypedExpression) and value.kind == "id"
        and value.symbol_id == 42)
    if len(kernel_references) != 2:
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=70, parameter_ordinal=1, symbol_id=42,
        symbol_name="kernel", array_type="float[9]", element_type="float",
        extent=9, direction="in", native_abi="const Kernel9&",
        induction_read_spans=parameter_reads, reads_per_iteration=2,
        direct_call_spans=tuple(item.span for item in direct_calls),
        direct_argument_spans=tuple(item.children[1].span for item in direct_calls),
    )

    # Unreachability recorded as a frozen fact: the proof vouches grammar,
    # not liveness.  The EFFECT=0 collapse witness is convolutionEffect's
    # single `return color;` statement, and main invokes no array caller.
    witness = collapsed.body[0]
    if (witness.kind != "return" or len(witness.expressions) != 1
            or witness.children
            or witness.expressions[0].kind != "id"
            or witness.expressions[0].symbol_id != 53
            or witness.expressions[0].symbol is None
            or witness.expressions[0].symbol.name != "color"):
        return None
    if _cellrefract_reachable_names(program, main_signature_id=76) \
            != _EFFECTS_REACHABLE:
        return None

    (array_parameters, array_declarations, array_expressions,
     array_identifiers, literal_stores, induction_reads, indexes,
     whole_arguments, array_calls) = _array_census(
        program, profile.array_ids, 154, direct_calls)
    if ((len(array_parameters), len(array_declarations), len(array_expressions),
         len(array_identifiers), len(literal_stores), len(induction_reads),
         len(indexes), len(whole_arguments), len(array_calls))
            != profile.census
            or {item.symbol_id for item in array_expressions
                if item.symbol_id is not None} != profile.array_ids
            or {item.symbol_id for item in array_identifiers} != profile.array_ids):
        return None

    return FixedArrayInParameterProof(
        proof_kind=CAPABILITY, source_profile=profile.source_profile,
        raw_source_sha256=raw_hash, normalized_source_sha256=normalized_hash,
        canonical_factory_sha256=profile.canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=binding_signature,
        compatibility_sites=(),
        kernel_alias="Kernel9", offsets_alias="Offsets9",
        caller_tables=callers, parameter=parameter, offset_table=offset,
        convolve_loop_span=loop.span, induction_symbol_id=154,
        loop_trip_count=9, lexical_product=9, entrypoint_charge=0,
        main_signature_id=76, mode_one_span=witness.span,
        main_derivative_call_spans=(),
        array_parameter_count=len(array_parameters),
        array_declaration_count=len(array_declarations),
        array_typed_expression_count=len(array_expressions),
        array_identifier_reference_count=len(array_identifiers),
        literal_store_count=len(literal_stores),
        induction_read_count=len(induction_reads),
        index_expression_count=len(indexes),
        whole_array_argument_count=len(whole_arguments),
        array_call_count=len(array_calls),
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        # Derived, not transcribed: within every caller the second table is
        # fully initialized before the first table's consuming convolve
        # call, exactly the family shape -- the pairs DO coexist.
        caller_tables_never_simultaneously_live=False,
        parameter_read_only_and_synchronous=True,
        # No mode dispatch exists here; the reachable pixel path writes the
        # seven globals through loadKernels every pixel.
        mode_zero_array_free=False, raw_simultaneous_payload_bytes=144,
        interface_sha256=interface_hash, typed_ir_sha256=typed_hash,
        whole_program_sha256=whole_hash,
    )
