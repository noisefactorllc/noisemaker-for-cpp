"""Frozen semantic records.  They contain no execution-time lookup machinery."""

from __future__ import annotations

from dataclasses import dataclass

from .semantic_types import Type
from .span import SourceSpan


@dataclass(frozen=True, slots=True)
class Symbol:
    id: int
    name: str
    type: Type
    storage: str
    span: SourceSpan
    writable: bool
    direction: str = "in"


@dataclass(frozen=True, slots=True)
class TypedExpression:
    kind: str
    type: Type
    span: SourceSpan
    category: str
    symbol_id: int | None = None
    signature_id: int | None = None
    children: tuple["TypedExpression", ...] = ()
    # These source-independent fields are deliberately retained so a later
    # emitter never has to consult the mutable parser AST again.
    literal: str | bool | None = None
    operator: str | None = None
    callee: str | None = None
    member: str | None = None
    constructor_type: Type | None = None
    symbol: Symbol | None = None
    literal_value: int | float | bool | None = None


@dataclass(frozen=True, slots=True)
class CountedLoopProof:
    induction_symbol_id: int
    start_value: int
    bound_value: int
    comparison: str
    update: str
    bound_kind: str
    trip_count: int
    lexical_depth: int
    effective_depth: int
    lexical_product: int
    entrypoint_charge: int


@dataclass(frozen=True, slots=True)
class CountedLoopProgramProof:
    loop_count: int
    unproved_loop_count: int
    max_effective_depth: int
    max_lexical_product: int
    entrypoint_charge: int
    call_graph_acyclic: bool


@dataclass(frozen=True, slots=True)
class DiscardedLocalCounterProof:
    proof_kind: str
    main_signature_id: int
    target_symbol_id: int
    target_type: str
    initializer_symbol_id: int
    initial_value: int
    initializer_span: SourceSpan
    statement_span: SourceSpan
    update_span: SourceSpan
    update_operator: str
    value_discarded: bool
    conditional_span: SourceSpan
    containing_loop_span: SourceSpan
    induction_symbol_id: int
    containing_loop_trip_count: int
    max_updates_per_visit: int
    lower_bound: int
    upper_bound: int
    predicate_profile: str
    sample_x_symbol_id: int
    x_symbol_id: int
    other_luminance_symbol_id: int
    own_luminance_symbol_id: int
    loop_body_statement_count: int
    skip_conditional_index: int
    counter_conditional_index: int


@dataclass(frozen=True, slots=True)
class PreprocessorDefine:
    name: str
    kind: str
    canonical_value: str


@dataclass(frozen=True, slots=True)
class FixedNineArrayProof:
    role: str
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_element_type: str
    declaration_statement_index: int
    declaration_span: SourceSpan
    literal_store_statement_indices: tuple[int, ...]
    literal_store_spans: tuple[SourceSpan, ...]
    literal_store_index_spans: tuple[SourceSpan, ...]
    literal_store_indices: tuple[int, ...]
    read_spans: tuple[SourceSpan, ...]
    reads_per_iteration: int


@dataclass(frozen=True, slots=True)
class FixedNineLocalTableProof:
    proof_kind: str
    source_profile: str
    main_signature_id: int
    main_body_statement_count: int
    define_contract: tuple[PreprocessorDefine, ...]
    arrays: tuple[FixedNineArrayProof, ...]
    initialization_start_statement_index: int
    initialization_end_statement_index: int
    loop_statement_index: int
    loop_span: SourceSpan
    induction_symbol_id: int
    start_value: int
    bound_value: int
    trip_count: int
    lower_bound: int
    upper_bound: int
    loop_body_statement_count: int
    read_profile: str
    array_reference_count: int
    no_read_before_initialization: bool
    no_write_after_initialization: bool
    no_escape: bool
    raw_payload_bytes: int
    typed_ir_sha256: str
    whole_program_sha256: str


@dataclass(frozen=True, slots=True)
class FixedGridLiteralReadProof:
    array_symbol_id: int
    literal_index: int
    index_span: SourceSpan
    expression_role: str
    role_ordinal: int


@dataclass(frozen=True, slots=True)
class FixedGridCounterStoreProof:
    proof_kind: str
    source_profile: str
    main_signature_id: int
    main_body_statement_count: int
    define_contract: tuple[PreprocessorDefine, ...]
    dimension_symbol_id: int
    dimension_symbol_name: str
    texture_size_statement_index: int
    early_return_statement_index: int
    early_return_span: SourceSpan
    zero_predicate_span: SourceSpan
    zero_assignment_span: SourceSpan
    zero_return_span: SourceSpan
    early_return_profile: str
    dominates_array: bool
    dominates_fetch: bool
    dominates_grid: bool
    dominates_store: bool
    dominates_counter_update: bool
    array_symbol_id: int
    array_symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_element_type: str
    array_declaration_statement_index: int
    array_declaration_span: SourceSpan
    counter_symbol_id: int
    counter_symbol_name: str
    counter_type: str
    counter_declaration_statement_index: int
    counter_declaration_span: SourceSpan
    counter_initializer_span: SourceSpan
    counter_initial_value: int
    outer_loop_statement_index: int
    outer_loop_span: SourceSpan
    outer_induction_symbol_id: int
    inner_loop_span: SourceSpan
    inner_induction_symbol_id: int
    loop_update_expression_kind: str
    loop_start: int
    loop_bound: int
    loop_comparison: str
    per_loop_trip_count: int
    lexical_product: int
    entrypoint_charge: int
    outer_body_statement_count: int
    inner_body_statement_count: int
    dynamic_store_statement_span: SourceSpan
    dynamic_store_index_span: SourceSpan
    dynamic_store_rhs_span: SourceSpan
    store_rhs_profile: str
    counter_update_statement_span: SourceSpan
    counter_update_expression_span: SourceSpan
    counter_update_source_kind: str
    counter_update_operator: str
    counter_update_value_discarded: bool
    store_precedes_update: bool
    store_lower_bound: int
    store_upper_bound: int
    store_count: int
    counter_final_value: int
    literal_reads: tuple[FixedGridLiteralReadProof, ...]
    literal_read_profile: str
    literal_read_count: int
    literal_read_unique_indices: tuple[int, ...]
    literal_read_occurrence_counts: tuple[tuple[int, int], ...]
    array_declaration_count: int
    array_reference_count: int
    array_typed_expression_count: int
    index_expression_count: int
    counter_declaration_count: int
    counter_reference_count: int
    no_array_initializer: bool
    no_copy_alias_escape_or_abi_use: bool
    no_alternate_array_write: bool
    no_alternate_counter_use: bool
    no_dynamic_read: bool
    no_index_after_grid: bool
    raw_payload_bytes: int
    typed_ir_sha256: str
    whole_program_sha256: str


@dataclass(frozen=True, slots=True)
class RefractCompatibilitySiteProof:
    blend_mode: int
    guard_span: SourceSpan
    assignment_statement_span: SourceSpan
    assignment_span: SourceSpan
    target_symbol_id: int
    source_symbol_id: int
    equality_constant: float
    false_builtin: str
    original_condition_span: SourceSpan
    original_false_span: SourceSpan
    transformed_rhs_span: SourceSpan


@dataclass(frozen=True, slots=True)
class FixedArrayOwnedTableProof:
    role: str
    owner_signature_id: int
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_alias: str
    declaration_statement_index: int
    declaration_span: SourceSpan
    literal_store_statement_indices: tuple[int, ...]
    literal_store_spans: tuple[SourceSpan, ...]
    literal_index_spans: tuple[SourceSpan, ...]
    literal_indices: tuple[int, ...]
    number_values: tuple[float, ...] | None
    induction_read_spans: tuple[SourceSpan, ...]


@dataclass(frozen=True, slots=True)
class FixedArrayParameterProof:
    owner_signature_id: int
    parameter_ordinal: int
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    direction: str
    native_abi: str
    induction_read_spans: tuple[SourceSpan, ...]
    reads_per_iteration: int
    direct_call_spans: tuple[SourceSpan, ...]
    direct_argument_spans: tuple[SourceSpan, ...]


@dataclass(frozen=True, slots=True)
class FixedArrayInParameterProof:
    proof_kind: str
    source_profile: str
    raw_source_sha256: str
    normalized_source_sha256: str
    canonical_factory_sha256: str
    define_contract: tuple[PreprocessorDefine, ...]
    binding_signature: tuple[str, ...]
    compatibility_sites: tuple[RefractCompatibilitySiteProof, ...]
    kernel_alias: str
    offsets_alias: str
    caller_tables: tuple[FixedArrayOwnedTableProof, ...]
    parameter: FixedArrayParameterProof
    offset_table: FixedArrayOwnedTableProof
    convolve_loop_span: SourceSpan
    induction_symbol_id: int
    loop_trip_count: int
    lexical_product: int
    entrypoint_charge: int
    main_signature_id: int
    mode_one_span: SourceSpan
    main_derivative_call_spans: tuple[SourceSpan, ...]
    array_parameter_count: int
    array_declaration_count: int
    array_typed_expression_count: int
    array_identifier_reference_count: int
    literal_store_count: int
    induction_read_count: int
    index_expression_count: int
    whole_array_argument_count: int
    array_call_count: int
    no_alias_copy_escape_return_or_post_call_use: bool
    complete_initialization_dominates_reads: bool
    caller_tables_never_simultaneously_live: bool
    parameter_read_only_and_synchronous: bool
    mode_zero_array_free: bool
    raw_simultaneous_payload_bytes: int
    interface_sha256: str
    typed_ir_sha256: str
    whole_program_sha256: str


@dataclass(frozen=True, slots=True)
class SacredStarNumberDivisionSiteProof:
    transform: str
    function_signature_id: int
    induction_symbol_id: int
    divisor_symbol_id: int
    local_symbol_id: int
    declaration_span: SourceSpan
    division_span: SourceSpan
    multiplication_span: SourceSpan
    subtraction_span: SourceSpan
    consumption_span: SourceSpan
    pre_function_sha256: str
    post_function_sha256: str
    pre_whole_program_sha256: str
    post_whole_program_sha256: str


@dataclass(frozen=True, slots=True)
class FixedAffineStoreRegionProof:
    role: str
    statement_index: int
    statement_span: SourceSpan
    loop_span: SourceSpan | None
    induction_symbol_id: int | None
    loop_start: int | None
    loop_bound: int | None
    comparison: str | None
    update: str | None
    trip_count: int
    index_span: SourceSpan
    index_profile: str
    lower_index: int
    upper_index: int
    write_count: int
    rhs_span: SourceSpan
    rhs_profile: str


@dataclass(frozen=True, slots=True)
class FixedAffineReadSiteProof:
    role: str
    index_span: SourceSpan
    index_profile: str
    induction_symbol_id: int
    owning_loop_span: SourceSpan
    control_span: SourceSpan | None
    dynamic_read_count: int
    enclosing_expression_profile: str


@dataclass(frozen=True, slots=True)
class FixedAffineCenters13Proof:
    proof_kind: str
    key: str
    source_profile: str
    numeric_profile: str
    raw_source_sha256: str
    normalized_source_sha256: str
    canonical_factory_sha256: str
    canonical_runtime_sha256: str
    interface_sha256: str
    transformed_function_sha256: str
    transformed_whole_program_sha256: str
    define_contract: tuple[PreprocessorDefine, ...]
    binding_signature: tuple[str, ...]
    output_symbol_id: int
    output_symbol_name: str
    logical_route: str
    compatibility_site: SacredStarNumberDivisionSiteProof
    fruit_signature_id: int
    fruit_body_profile: str
    main_signature_id: int
    main_control_profile: str
    symbol_id: int
    symbol_name: str
    array_type: str
    element_type: str
    extent: int
    native_alias: str
    declaration_statement_index: int
    declaration_span: SourceSpan
    store_regions: tuple[FixedAffineStoreRegionProof, ...]
    read_sites: tuple[FixedAffineReadSiteProof, ...]
    call_routing_profile: str
    draw_lines_guard_profile: str
    array_declaration_count: int
    array_typed_expression_count: int
    array_base_identifier_count: int
    index_expression_count: int
    static_store_site_count: int
    dynamic_store_count: int
    static_read_site_count: int
    circle_read_count: int
    line_endpoint_read_count: int
    maximum_dynamic_read_count: int
    initialization_complete: bool
    write_sets_disjoint: bool
    initialization_dominates_reads: bool
    no_post_read_writes: bool
    no_alias_copy_escape: bool
    loop_count: int
    unproved_loop_count: int
    max_effective_depth: int
    max_lexical_product: int
    entrypoint_charge: int
    call_graph_acyclic: bool
    table_payload_bytes: int


@dataclass(frozen=True, slots=True)
class TypedDeclaration:
    symbol: Symbol
    type: Type
    span: SourceSpan
    initializer: TypedExpression | None = None


@dataclass(frozen=True, slots=True)
class StructField:
    id: int
    name: str
    type: Type
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class StructDeclaration:
    id: int
    name: str
    type: Type
    fields: tuple[StructField, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class UniformBlock:
    id: int
    block_name: str
    instance_name: str | None
    fields: tuple[StructField, ...]
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class FunctionSignature:
    id: int
    name: str
    return_type: Type
    parameters: tuple[Symbol, ...]
    declaration_spans: tuple[SourceSpan, ...]
    definition_span: SourceSpan | None


@dataclass(frozen=True, slots=True)
class TypedFunction:
    signature: FunctionSignature
    span: SourceSpan
    body: tuple["TypedStatement", ...] = ()

    @property
    def id(self) -> int:
        return self.signature.id

    @property
    def name(self) -> str:
        return self.signature.name

    @property
    def return_type(self) -> Type:
        return self.signature.return_type

    @property
    def parameters(self) -> tuple[Symbol, ...]:
        return self.signature.parameters


@dataclass(frozen=True, slots=True)
class TypedStatement:
    kind: str
    span: SourceSpan
    expressions: tuple[TypedExpression, ...] = ()
    children: tuple["TypedStatement", ...] = ()
    loop_proof: CountedLoopProof | None = None
    counter_proof: DiscardedLocalCounterProof | None = None


@dataclass(frozen=True, slots=True)
class ResourceRequirements:
    uniforms: tuple[str, ...]
    samplers: tuple[str, ...]
    outputs: tuple[str, ...]
    uses_texture: bool = False
    uses_derivatives: bool = False


@dataclass(frozen=True, slots=True)
class TypedProgram:
    key: str
    source: str
    declarations: tuple[TypedDeclaration, ...]
    functions: tuple[TypedFunction, ...]
    resources: ResourceRequirements
    body_status: str = "not analyzed"
    local_type_names: tuple[str, ...] = ()
    structs: tuple[StructDeclaration, ...] = ()
    uniform_blocks: tuple[UniformBlock, ...] = ()
    # Source-declared varyings and injected fragment builtins are part of the
    # typed interface, not ambient names an emitter has to rediscover.
    interface_symbols: tuple[Symbol, ...] = ()
    builtin_symbols: tuple[Symbol, ...] = ()
    counted_loop_proof: CountedLoopProgramProof | None = None
    raw_source: str = ""
    preprocessor_defines: tuple[PreprocessorDefine, ...] = ()
    fixed_nine_table_proof: FixedNineLocalTableProof | None = None
    fixed_grid_counter_store_proof: FixedGridCounterStoreProof | None = None
    fixed_array_in_parameter_proof: FixedArrayInParameterProof | None = None
    fixed_affine_centers13_proof: FixedAffineCenters13Proof | None = None
