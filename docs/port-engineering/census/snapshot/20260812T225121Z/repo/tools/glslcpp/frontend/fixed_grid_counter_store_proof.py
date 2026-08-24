"""Exact proof for the two pinned counter-filled 3x3 scalar tables."""

from __future__ import annotations

from collections import Counter
import hashlib

from .typed_ir import (FixedGridCounterStoreProof,
                       FixedGridLiteralReadProof, TypedExpression,
                       TypedProgram, TypedStatement)


CAPABILITY = "fixed-grid-counter-store-v1"
CEL_KEY = "filter/celShading:celShadingEdges"
OUTLINE_KEY = "filter/outline:outlineSobel"
SOURCE_LOCKS = {
    CEL_KEY: (
        "9c2848c92bd0f3e2de76fd065ac8fc55086cb7d209ce09ac4ba6488acda4630e",
        "c8e56f507bfa71ac7d43dbe7cc8060695a2e0fc1eb2f1b2bc19e2ed17d55411e",
    ),
    OUTLINE_KEY: (
        "cfe848d1605f1ad693fd3ce9e518a4adf4e0f34e3fff6c6ae1ebcaec49949f5d",
        "fa3eb35ad201e4cbf44a0f3e43060652f2cf099a6b2de1c7c4f906c0d30cca5d",
    ),
}
_PROFILES = {
    CEL_KEY: {
        "profile": "cel-shading-edges-3x3-v1",
        "body_count": 13, "array_index": 5, "counter_index": 6,
        "loop_index": 7, "inner_count": 5, "store_index": 3,
        "rhs": "cel-wrapped-fetch-luminosity-v1", "dimension": "texSize",
    },
    OUTLINE_KEY: {
        "profile": "outline-sobel-3x3-v1",
        "body_count": 14, "array_index": 6, "counter_index": 7,
        "loop_index": 8, "inner_count": 4, "store_index": 2,
        "rhs": "outline-wrapped-fetch-red-v1", "dimension": "dimensions",
    },
}
_TYPED_IR_LOCKS = {
    CEL_KEY: "3581b9006260f19fd8519172628a5de1b3b81edd123279ad81f30906dc9d8e50",
    OUTLINE_KEY: "af33cbbba839cfb7ea71ce64a57805d31aba97edbe487095df7b89e44dbdb1ac",
}
_WHOLE_PROGRAM_LOCKS = {
    CEL_KEY: "ba5adfa3c30ba1290dbd5382c1158d3f695245428403054b42fe5012b51dfcc4",
    OUTLINE_KEY: "66c92544399ae3ca62dcd2ad35454e0ab86005474e5032a999d48ea3ca7c8c3c",
}
_GX_READS = (0, 2, 3, 5, 6, 8)
_GY_READS = (0, 1, 2, 6, 7, 8)


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


def _whole_program_fingerprint(program: TypedProgram) -> str:
    profile = (
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
        program.fixed_nine_table_proof,
    )
    return hashlib.sha256(repr(profile).encode("utf-8")).hexdigest()


def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None:
    locks = SOURCE_LOCKS.get(program.key)
    if locks is None:
        return None
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if (program.preprocessor_defines or raw_hash != locks[0]
            or normalized_hash != locks[1] or source_hash != locks[0]):
        return "source provenance mismatch for fixed-grid counter store"
    return None


def _single_declaration(statement: TypedStatement, name: str,
                        type_name: str) -> TypedExpression | None:
    if statement.kind != "decl" or len(statement.expressions) != 1:
        return None
    value = statement.expressions[0]
    if (value.kind != "declaration" or value.symbol is None
            or value.symbol_id is None or value.symbol.id != value.symbol_id
            or value.symbol.name != name or value.type.display() != type_name
            or value.symbol.type != value.type or value.symbol.storage != "local"
            or not value.symbol.writable):
        return None
    return value


def _literal(value: TypedExpression, expected: int) -> bool:
    return (value.kind == "literal" and value.type.display() == "int"
            and value.literal == str(expected)
            and value.literal_value == expected)


def _negative_one(value: TypedExpression) -> bool:
    return (value.kind == "unary" and value.operator == "-"
            and len(value.children) == 1 and _literal(value.children[0], 1))


def _exact_loop(loop: TypedStatement, name: str,
                expected_depth: int) -> tuple[TypedExpression, TypedStatement] | None:
    if (loop.kind != "for" or len(loop.expressions) != 2
            or len(loop.children) != 2 or loop.children[1].kind != "block"
            or loop.loop_proof is None):
        return None
    declaration = _single_declaration(loop.children[0], name, "int")
    if declaration is None or len(declaration.children) != 1 or not _negative_one(declaration.children[0]):
        return None
    condition, update = loop.expressions
    if (condition.kind != "binary" or condition.operator != "<="
            or len(condition.children) != 2
            or condition.children[0].kind != "id"
            or condition.children[0].symbol_id != declaration.symbol_id
            or not _literal(condition.children[1], 1)
            or update.kind != "unary" or update.operator != "++"
            or len(update.children) != 1 or update.children[0].kind != "id"
            or update.children[0].symbol_id != declaration.symbol_id):
        return None
    proof = loop.loop_proof
    if (proof.induction_symbol_id != declaration.symbol_id
            or proof.start_value != -1 or proof.bound_value != 1
            or proof.comparison != "<=" or proof.update != "++"
            or proof.bound_kind != "literal" or proof.trip_count != 3
            or proof.lexical_depth != expected_depth
            or proof.effective_depth != expected_depth
            or proof.lexical_product != 9 or proof.entrypoint_charge != 12):
        return None
    return declaration, loop.children[1]


def _early_return(statement: TypedStatement, dimension_id: int,
                  output_id: int) -> tuple[TypedExpression, TypedStatement, TypedStatement] | None:
    if (statement.kind != "if" or len(statement.expressions) != 1
            or len(statement.children) != 1 or statement.children[0].kind != "block"
            or len(statement.children[0].children) != 2):
        return None
    predicate = statement.expressions[0]
    if predicate.kind != "binary" or predicate.operator != "||" or len(predicate.children) != 2:
        return None
    for comparison, member in zip(predicate.children, ("x", "y")):
        if (comparison.kind != "binary" or comparison.operator != "=="
                or len(comparison.children) != 2
                or comparison.children[0].kind != "swizzle"
                or comparison.children[0].member != member
                or len(comparison.children[0].children) != 1
                or comparison.children[0].children[0].kind != "id"
                or comparison.children[0].children[0].symbol_id != dimension_id
                or not _literal(comparison.children[1], 0)):
            return None
    assignment_statement, return_statement = statement.children[0].children
    if (assignment_statement.kind != "expr" or len(assignment_statement.expressions) != 1
            or return_statement.kind != "return" or return_statement.expressions
            or return_statement.children):
        return None
    assignment = assignment_statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2
            or assignment.children[0].kind != "id"
            or assignment.children[0].symbol_id != output_id
            or assignment.children[1].kind != "construct"
            or assignment.children[1].type.display() != "vec4"
            or len(assignment.children[1].children) != 1
            or assignment.children[1].children[0].kind != "literal"
            or assignment.children[1].children[0].literal != "0.0"
            or assignment.children[1].children[0].literal_value != 0.0):
        return None
    return predicate, assignment_statement, return_statement


def _literal_reads(statement: TypedStatement, array_id: int,
                   role: str, expected: tuple[int, ...]) -> tuple[FixedGridLiteralReadProof, ...] | None:
    if statement.kind != "decl" or len(statement.expressions) != 1:
        return None
    declaration = statement.expressions[0]
    if declaration.kind != "declaration" or len(declaration.children) != 1:
        return None
    reads = []
    for value in _walk_expression(declaration.children[0]):
        if value.kind != "index":
            continue
        if (len(value.children) != 2 or value.children[0].kind != "id"
                or value.children[0].symbol_id != array_id
                or not isinstance(value.children[1].literal_value, int)
                or not _literal(value.children[1], value.children[1].literal_value)):
            return None
        reads.append(FixedGridLiteralReadProof(
            array_id, value.children[1].literal_value, value.span, role, len(reads)))
    if tuple(item.literal_index for item in reads) != expected:
        return None
    return tuple(reads)


def prove_fixed_grid_counter_store(
        program: TypedProgram) -> FixedGridCounterStoreProof | None:
    """Return a proof only for an exact pinned Task 18 whole program."""
    config = _PROFILES.get(program.key)
    if config is None or program.preprocessor_defines:
        return None
    typed_ir_hash = hashlib.sha256(repr(program.functions).encode("utf-8")).hexdigest()
    whole_hash = _whole_program_fingerprint(program)
    if (typed_ir_hash != _TYPED_IR_LOCKS[program.key]
            or whole_hash != _WHOLE_PROGRAM_LOCKS[program.key]):
        return None
    if (program.structs or program.uniform_blocks or program.interface_symbols
            or not program.resources.uses_texture or program.resources.uses_derivatives
            or program.counted_loop_proof is None
            or program.counted_loop_proof.loop_count != 2
            or program.counted_loop_proof.unproved_loop_count != 0
            or program.counted_loop_proof.max_effective_depth != 2
            or program.counted_loop_proof.max_lexical_product != 9
            or program.counted_loop_proof.entrypoint_charge != 12
            or not program.counted_loop_proof.call_graph_acyclic):
        return None
    mains = [item for item in program.functions if item.name == "main" and item.body]
    if len(mains) != 1 or len(mains[0].body) != config["body_count"]:
        return None
    main = mains[0]
    dimension = _single_declaration(main.body[1], config["dimension"], "ivec2")
    output = next((item.symbol for item in program.declarations
                   if item.symbol.name == "fragColor"), None)
    if (dimension is None or len(dimension.children) != 1
            or dimension.children[0].kind != "builtin"
            or dimension.children[0].callee != "textureSize"
            or output is None):
        return None
    early = _early_return(main.body[2], dimension.symbol_id, output.id)
    if early is None:
        return None
    predicate, zero_assignment, zero_return = early

    array = _single_declaration(main.body[config["array_index"]], "samples", "float[9]")
    counter = _single_declaration(main.body[config["counter_index"]], "idx", "int")
    if (array is None or array.children or counter is None
            or len(counter.children) != 1 or not _literal(counter.children[0], 0)
            or config["counter_index"] != config["array_index"] + 1
            or config["loop_index"] != config["counter_index"] + 1):
        return None

    outer_loop = main.body[config["loop_index"]]
    outer = _exact_loop(outer_loop, "ky", 1)
    if outer is None or len(outer[1].children) != 1:
        return None
    inner_loop = outer[1].children[0]
    inner = _exact_loop(inner_loop, "kx", 2)
    if inner is None or len(inner[1].children) != config["inner_count"]:
        return None
    inner_body = inner[1]
    store_statement = inner_body.children[config["store_index"]]
    update_statement = inner_body.children[config["store_index"] + 1]
    if (config["store_index"] + 2 != len(inner_body.children)
            or store_statement.kind != "expr" or len(store_statement.expressions) != 1
            or update_statement.kind != "expr" or len(update_statement.expressions) != 1):
        return None
    assignment = store_statement.expressions[0]
    update = update_statement.expressions[0]
    if (assignment.kind != "assign" or assignment.operator != "="
            or len(assignment.children) != 2
            or assignment.children[0].kind != "index"
            or len(assignment.children[0].children) != 2
            or assignment.children[0].children[0].kind != "id"
            or assignment.children[0].children[0].symbol_id != array.symbol_id
            or assignment.children[0].children[1].kind != "id"
            or assignment.children[0].children[1].symbol_id != counter.symbol_id
            or update.kind != "post" or update.operator != "++"
            or len(update.children) != 1 or update.children[0].kind != "id"
            or update.children[0].symbol_id != counter.symbol_id
            or store_statement.span.end > update_statement.span.start):
        return None
    rhs = assignment.children[1]
    rhs_nodes = tuple(_walk_expression(rhs))
    if any(node.symbol_id in {array.symbol_id, counter.symbol_id} for node in rhs_nodes):
        return None
    if program.key == CEL_KEY:
        if (rhs.kind != "call" or rhs.callee != "getLuminosity"
                or len(rhs.children) != 1 or rhs.children[0].kind != "swizzle"
                or rhs.children[0].member != "rgb"):
            return None
    else:
        if (rhs.kind != "swizzle" or rhs.member != "r" or len(rhs.children) != 1
                or rhs.children[0].kind != "builtin"
                or rhs.children[0].callee != "texelFetch"):
            return None

    gx_reads = _literal_reads(main.body[config["loop_index"] + 1],
                              array.symbol_id, "sobel-gx", _GX_READS)
    gy_reads = _literal_reads(main.body[config["loop_index"] + 2],
                              array.symbol_id, "sobel-gy", _GY_READS)
    if gx_reads is None or gy_reads is None:
        return None
    literal_reads = gx_reads + gy_reads

    all_nodes = tuple(node for function in program.functions for statement in function.body
                      for node in _walk_statement(statement))
    expressions = tuple(node for node in all_nodes if isinstance(node, TypedExpression))
    array_references = tuple(node for node in expressions
                             if node.kind == "id" and node.symbol_id == array.symbol_id)
    counter_references = tuple(node for node in expressions
                               if node.kind == "id" and node.symbol_id == counter.symbol_id)
    array_declarations = tuple(node for node in expressions
                               if node.kind == "declaration" and node.symbol_id == array.symbol_id)
    counter_declarations = tuple(node for node in expressions
                                 if node.kind == "declaration" and node.symbol_id == counter.symbol_id)
    array_typed = tuple(node for node in expressions if node.type.kind == "array")
    indices = tuple(node for node in expressions if node.kind == "index")
    if (len(array_declarations) != 1 or len(array_references) != 13
            or len(array_typed) != 14 or len(indices) != 13
            or len(counter_declarations) != 1 or len(counter_references) != 2):
        return None
    expected_index_spans = {assignment.children[0].span,
                            *(item.index_span for item in literal_reads)}
    if {item.span for item in indices} != expected_index_spans:
        return None
    expected_array_spans = {item.children[0].span for item in indices}
    if {item.span for item in array_references} != expected_array_spans:
        return None
    if {item.span for item in counter_references} != {
            assignment.children[0].children[1].span, update.children[0].span}:
        return None
    fetches = tuple(node for node in expressions
                    if node.kind == "builtin" and node.callee == "texelFetch")
    if len(fetches) != 1 or zero_return.span.end > min(item.span.start for item in fetches):
        return None
    occurrence_counts = tuple(sorted(Counter(
        item.literal_index for item in literal_reads).items()))
    return FixedGridCounterStoreProof(
        CAPABILITY, config["profile"], main.signature.id, len(main.body),
        program.preprocessor_defines, dimension.symbol_id, dimension.symbol.name,
        1, 2, main.body[2].span, predicate.span, zero_assignment.span,
        zero_return.span, "dimension-x-or-y-zero-output-zero-return-v1",
        zero_return.span.end < array.span.start,
        zero_return.span.end < fetches[0].span.start,
        zero_return.span.end < outer_loop.span.start,
        zero_return.span.end < store_statement.span.start,
        zero_return.span.end < update_statement.span.start,
        array.symbol_id, array.symbol.name, array.type.display(), "float", 9,
        "double", config["array_index"], array.span,
        counter.symbol_id, counter.symbol.name, counter.type.display(),
        config["counter_index"], counter.span, counter.children[0].span, 0,
        config["loop_index"], outer_loop.span,
        outer_loop.loop_proof.induction_symbol_id, inner_loop.span,
        inner_loop.loop_proof.induction_symbol_id, "unary", -1, 1, "<=", 3,
        9, 12, len(outer[1].children), len(inner_body.children),
        store_statement.span, assignment.children[0].span, rhs.span, config["rhs"],
        update_statement.span, update.span, "post", "++", True,
        store_statement.span.end <= update_statement.span.start,
        0, 8, 9, 9, literal_reads,
        "exact-authored-sobel-gx-gy-literal-reads-v1", len(literal_reads),
        tuple(sorted(set(item.literal_index for item in literal_reads))),
        occurrence_counts, len(array_declarations), len(array_references),
        len(array_typed), len(indices), len(counter_declarations),
        len(counter_references), True, True, True, True, True, True, 72,
        typed_ir_hash, whole_hash)
