"""Closed frontend admission proof for ``filter/palette:palette``.

Palette is deliberately authenticated as one exact program.  In particular,
the const ``PaletteEntry[55]`` table is admitted by declaration identity and
by recursively checking every one of its 55 four-``vec4`` records; a generic
``struct[]`` capability would be too wide for the native emitter.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .typed_ir import TypedExpression, TypedProgram


KEY = "filter/palette:palette"
PROFILE = "palette-frontend-admission-v1"
KEYS = (KEY,)
PROFILES = {KEY: PROFILE}
PREPARED_KEYS: tuple[str, ...] = ()
PALETTE_FRONTEND_KEYS = frozenset(PROFILES)
ALLOWED_ROW_FIELDS = {
    KEY: frozenset({"defines", "program_key", "palette_frontend_profile"}),
}
REQUIRED_COMPANION_PROFILES: dict[str, tuple[tuple[str, str], ...]] = {}

RAW_SOURCE_SHA256 = "03ab3914862807288f7d5f6d2cbe8907cfa66fd1bb80b02df509880292967c09"
NORMALIZED_SOURCE_SHA256 = "5e233dee16d462d5a93b30f95f2fc480ba5165bdab8a01bd6dc87c4285fa8b9f"
FUNCTIONS_SHA256 = "a551a1a323d72ddf60a2e00f89501f2a5b99b6416f85853b491b6a10004daa1e"
WHOLE_PROGRAM_SHA256 = "0c44dcab5981ec093aee667a4d8aacf26e037dfce7d2af53e6180f9e1891777b"

UNIFORM_NAMES = (
    "tileOffset", "fullResolution", "inputTex", "paletteIndex", "rotation",
    "offset", "repeat", "alpha", "time",
)
UNIFORM_TYPES = (
    "vec2", "vec2", "sampler2D", "int", "int", "float", "float", "float", "float",
)
STRUCT_NAME = "PaletteEntry"
STRUCT_FIELDS = ("amp", "freq", "offset", "phase")
STRUCT_FIELD_TYPES = ("vec4", "vec4", "vec4", "vec4")
PALETTE_COUNT = 55
CONST_ARRAY_CONSTRUCT_COUNT = 276
PALETTE_ENTRY_CONSTRUCT_COUNT = 55
VEC4_CONSTRUCT_COUNT = 220
PALETTE_LITERAL_COUNT = 880
CONSUMED_NODE_CARDINALITY = 1180
PALETTE_INDEX_COUNT = 1
FUNCTION_NAMES = ("cosinePalette", "hsv2rgb", "linear2srgb", "main", "oklab2linear", "oklab2rgb")
# Adapter-only numeric facts.  These are consumed only when this exact
# source-bound profile is authenticated; they are not a global GLSL numeric
# contract.
TABLE_NATIVE_TYPE = "glsl::FloatExpr<4>"
COSINE_NATIVE_TYPE = "glsl::FloatExpr<3>"
TAU_NAME = "TAU"
COSINE_HELPER_NAME = "palette_cosine_number_cos"
CLAMP_HELPER_NAME = "palette_cosine_number_clamp"
LUMINANCE_HELPER_NAME = "palette_number_luminance"
LINEAR_TO_SRGB_HELPER_NAME = "palette_number_linear_to_srgb"


@dataclass(frozen=True, slots=True)
class PaletteFrontendProof:
    """Identity-bound typed objects admitted to the narrow Palette emitter."""

    program: TypedProgram
    struct: Any
    struct_fields: tuple[Any, ...]
    palette_count_declaration: Any
    palette_count_initializer: TypedExpression
    palettes_declaration: Any
    palettes_initializer: TypedExpression
    palette_entries: tuple[TypedExpression, ...]
    palette_entry_constructors: tuple[TypedExpression, ...]
    vec4_constructors: tuple[TypedExpression, ...]
    palette_literals: tuple[TypedExpression, ...]
    palette_index_reads: tuple[TypedExpression, ...]
    exceptional_nodes: tuple[TypedExpression, ...]
    tau_declaration: Any
    tau_initializer: TypedExpression
    cosine_function: Any
    cosine_site: TypedExpression
    cosine_clamp_site: TypedExpression
    cosine_vector_sites: tuple[TypedExpression, ...]
    luminance_site: TypedExpression
    t_initializer: TypedExpression
    hsv_function: Any
    oklab_function: Any
    table_native_type: str
    functions: tuple[Any, ...]
    consumed_nodes: tuple[Any, ...]
    program_key: str
    profile: str
    source_hash: str
    normalized_source_hash: str
    uniform_names: tuple[str, ...]
    uniform_types: tuple[str, ...]
    struct_name: str
    struct_field_count: int
    field_names: tuple[str, ...]
    field_types: tuple[str, ...]
    palette_count: int
    const_array_construct_count: int
    palette_index_count: int

    def __getitem__(self, key: str) -> object:
        values = {
            "profile": self.profile,
            "program_key": self.program_key,
            "uniforms": self.uniform_names,
            "struct_name": self.struct_name,
            "struct_fields": self.field_names,
            "palette_count": self.palette_count,
            "functions": tuple(function.name for function in self.functions),
        }
        if key not in values:
            raise KeyError(key)
        return values[key]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _walk(value):
    yield value
    for child in value.children:
        yield from _walk(child)


def _whole(program) -> str:
    payload = (
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    )
    return _sha(payload)


def _uniforms(program):
    rows = tuple(item for item in program.declarations if item.symbol.storage == "uniform")
    return tuple(item.symbol.name for item in rows), tuple(item.type.display() for item in rows)


def _palette_decl(program):
    rows = [item for item in program.declarations if item.symbol.name == "PALETTES"]
    if len(rows) != 1:
        raise ValueError("Palette const struct array declaration cardinality mismatch")
    return rows[0]


def _authenticate_table(declaration):
    symbol = declaration.symbol
    if symbol.storage != "const" or symbol.writable:
        raise ValueError("Palette const struct array storage drift")
    if declaration.type.display() != "PaletteEntry[55]":
        raise ValueError("Palette const struct array type drift")
    initializer = declaration.initializer
    if initializer is None or initializer.kind != "construct" \
            or initializer.type.display() != "PaletteEntry[55]" \
            or initializer.constructor_type.display() != "PaletteEntry[55]" \
            or len(initializer.children) != PALETTE_COUNT:
        raise ValueError("Palette const struct array initializer closure drift")
    for entry in initializer.children:
        if entry.kind != "construct" or entry.type.display() != "PaletteEntry" \
                or entry.constructor_type.display() != "PaletteEntry" \
                or len(entry.children) != 4:
            raise ValueError("PaletteEntry constructor closure drift")
        for field in entry.children:
            if field.kind != "construct" or field.type.display() != "vec4" \
                    or field.constructor_type.display() != "vec4" \
                    or len(field.children) != 4 \
                    or any(item.kind != "literal" for item in field.children):
                raise ValueError("PaletteEntry vec4 literal closure drift")
    return initializer


def _palette_index_count(program, symbol_id: int) -> int:
    nodes = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            nodes.extend(_walk(declaration.initializer))
    for function in program.functions:
        for statement in function.body:
            for expression in statement.expressions:
                nodes.extend(_walk(expression))
            for child in statement.children:
                nodes.extend(_walk_statement(child))
    indices = [node for node in nodes if node.kind == "index"
               and node.children and node.children[0].kind == "id"
               and node.children[0].symbol_id == symbol_id]
    if len(indices) != PALETTE_INDEX_COUNT:
        raise ValueError("Palette table index cardinality drift")
    node = indices[0]
    if len(node.children) != 2 or node.children[1].kind != "binary" \
            or node.children[1].operator != "-":
        raise ValueError("Palette table index expression drift")
    return len(indices)


def _walk_statement(statement):
    yield from ()
    for expression in statement.expressions:
        yield from _walk(expression)
    for child in statement.children:
        yield from _walk_statement(child)


def _cosine_sites(program):
    """Resolve the exact retained-Number sites in ``cosinePalette``.

    The source function is intentionally small and hash-pinned, but these
    identity checks keep an emitter from treating an arbitrary vec3/cos/clamp
    expression as a precision exception.
    """
    functions = tuple(item for item in program.functions
                      if item.name == "cosinePalette")
    if len(functions) != 1:
        raise ValueError("Palette cosine function cardinality drift")
    function = functions[0]
    nodes = tuple(node for statement in function.body
                  for node in _walk_statement(statement))
    clamps = tuple(node for node in nodes
                   if node.kind == "builtin" and node.callee == "clamp")
    cosines = tuple(node for node in nodes
                    if node.kind == "builtin" and node.callee == "cos")
    if len(clamps) != 1 or len(cosines) != 1:
        raise ValueError("Palette cosine builtin cardinality drift")
    clamp = clamps[0]
    if (clamp.type.display() != "vec3" or len(clamp.children) != 3
            or clamp.children[0].kind != "binary"
            or clamp.children[0].operator != "+"):
        raise ValueError("Palette cosine clamp expression drift")
    plus = clamp.children[0]
    product = plus.children[1]
    if (product.kind != "binary" or product.operator != "*"
            or product.type.display() != "vec3"
            or len(product.children) != 2
            or product.children[1] is not cosines[0]):
        raise ValueError("Palette cosine vector expression drift")
    vector_sites = (plus, product)
    if any(node.type.display() != "vec3" for node in vector_sites):
        raise ValueError("Palette cosine vector site type drift")
    return function, cosines[0], clamp, vector_sites


def _adapter_number_sites(program):
    mains = tuple(item for item in program.functions if item.name == "main")
    if len(mains) != 1:
        raise ValueError("Palette main function cardinality drift")
    declarations = tuple(
        expression for statement in mains[0].body
        for expression in statement.expressions
        if expression.kind == "declaration")
    by_name = {item.symbol.name: item for item in declarations}
    lum = by_name.get("lum")
    t = by_name.get("t")
    if (lum is None or len(lum.children) != 1
            or lum.children[0].kind != "builtin"
            or lum.children[0].callee != "dot"
            or tuple(child.type.display() for child in lum.children[0].children)
            != ("vec3", "vec3")
            or lum.children[0].children[0].kind != "swizzle"
            or lum.children[0].children[0].member != "rgb"
            or lum.children[0].children[1].kind != "construct"
            or tuple(child.literal for child in
                     lum.children[0].children[1].children)
            != ("0.299", "0.587", "0.114")):
        raise ValueError("Palette adapter luminance site drift")
    if (t is None or len(t.children) != 1
            or t.children[0].kind != "binary"
            or t.children[0].operator != "+"
            or t.children[0].type.display() != "float"):
        raise ValueError("Palette adapter t initializer drift")
    initializer = t.children[0]
    if (len(initializer.children) != 2
            or any(child.kind != "binary" or child.operator != "*"
                   for child in initializer.children)
            or tuple(child.symbol.name for child in initializer.children[0].children)
            != ("lum", "repeat")
            or initializer.children[1].children[0].symbol.name != "offset"
            or initializer.children[1].children[1].kind != "literal"
            or initializer.children[1].children[1].literal != "0.01"):
        raise ValueError("Palette adapter t arithmetic closure drift")
    hsv = tuple(item for item in program.functions if item.name == "hsv2rgb")
    oklab = tuple(item for item in program.functions if item.name == "oklab2rgb")
    if (len(hsv) != 1 or len(oklab) != 1
            or hsv[0].return_type.display() != "vec3"
            or oklab[0].return_type.display() != "vec3"
            or tuple(parameter.type.display() for parameter in hsv[0].parameters)
            != ("vec3",)
            or tuple(parameter.type.display() for parameter in oklab[0].parameters)
            != ("vec3",)):
        raise ValueError("Palette adapter color conversion closure drift")
    return lum.children[0], initializer, hsv[0], oklab[0]


def _derive_consumed(program: TypedProgram):
    if len(program.structs) != 1 or program.structs[0].name != STRUCT_NAME:
        raise ValueError("Palette live struct declaration drift")
    struct = program.structs[0]
    declarations = {item.symbol.name: item for item in program.declarations}
    palette_count = declarations.get("PALETTE_COUNT")
    palettes = declarations.get("PALETTES")
    if palette_count is None or palette_count.initializer is None:
        raise ValueError("Palette live count declaration/initializer missing")
    if palettes is None or palettes.initializer is None:
        raise ValueError("Palette live table declaration/initializer missing")
    tau = declarations.get(TAU_NAME)
    if (tau is None or tau.initializer is None
            or tau.type.display() != "float"
            or tau.initializer.kind != "literal"
            or tau.initializer.type.display() != "float"):
        raise ValueError("Palette TAU declaration/initializer missing")
    cosine_function, cosine_site, cosine_clamp_site, cosine_vector_sites = (
        _cosine_sites(program))
    luminance_site, t_initializer, hsv_function, oklab_function = (
        _adapter_number_sites(program))
    initializer = palettes.initializer
    entries = tuple(initializer.children)
    entry_constructors = tuple(entry for entry in entries if entry.kind == "construct")
    vec4 = tuple(field for entry in entries for field in entry.children
                 if field.kind == "construct")
    literals = tuple(literal for field in vec4 for literal in field.children
                     if literal.kind == "literal")
    reads = tuple(
        expression for function in program.functions for statement in function.body
        for expression in _walk_statement(statement)
        if expression.kind == "index" and len(expression.children) == 2
        and expression.children[0].kind == "id"
        and expression.children[0].symbol is not None
        and expression.children[0].symbol.name == "PALETTES"
    )
    if len(reads) != PALETTE_INDEX_COUNT:
        raise ValueError("Palette table index cardinality drift")
    if len(reads[0].children) != 2 or reads[0].children[1].kind != "binary" \
            or reads[0].children[1].operator != "-":
        raise ValueError("Palette table index expression drift")
    # The binary subtract child is the exceptional source form behind the
    # one-based table lookup.  It is separately carried and ledgered so an
    # emitter cannot silently replace it with a generic index expression.
    exceptional = tuple(read.children[1] for read in reads)
    groups = (
        (struct,), tuple(struct.fields),
        (palette_count, palette_count.initializer),
        (palettes,), (initializer,), entries, vec4,
        literals, reads, exceptional,
        (tau, tau.initializer), cosine_vector_sites,
        (cosine_site, cosine_clamp_site), tuple(program.functions),
        (luminance_site, t_initializer),
    )
    ledger = tuple(node for group in groups for node in group)
    if len(ledger) != CONSUMED_NODE_CARDINALITY:
        raise ValueError(f"Palette consumed-object cardinality drift: {len(ledger)}")
    if len({id(node) for node in ledger}) != len(ledger):
        raise ValueError("Palette consumed-object ledger is not identity-disjoint")
    values = {
        "struct": struct,
        "struct_fields": tuple(struct.fields),
        "palette_count_declaration": palette_count,
        "palette_count_initializer": palette_count.initializer,
        "palettes_declaration": palettes,
        "palettes_initializer": initializer,
        "palette_entries": entries,
        "palette_entry_constructors": entry_constructors,
        "vec4_constructors": vec4,
        "palette_literals": literals,
        "palette_index_reads": reads,
        "exceptional_nodes": exceptional,
        "tau_declaration": tau,
        "tau_initializer": tau.initializer,
        "cosine_function": cosine_function,
        "cosine_site": cosine_site,
        "cosine_clamp_site": cosine_clamp_site,
        "cosine_vector_sites": cosine_vector_sites,
        "luminance_site": luminance_site,
        "t_initializer": t_initializer,
        "hsv_function": hsv_function,
        "oklab_function": oklab_function,
        "table_native_type": TABLE_NATIVE_TYPE,
        "functions": tuple(program.functions),
    }
    return values, ledger


def verify_palette_frontend_proof(program: TypedProgram, proof: PaletteFrontendProof) -> PaletteFrontendProof:
    if not isinstance(proof, PaletteFrontendProof) or proof.program is not program:
        raise ValueError("Palette proof is not bound to the selected live program")
    expected, ledger = _derive_consumed(program)
    for name, value in expected.items():
        actual = getattr(proof, name)
        if isinstance(value, tuple):
            if len(actual) != len(value) or any(a is not b for a, b in zip(actual, value)):
                raise ValueError(f"Palette consumed {name} identity drift")
        elif actual is not value:
            raise ValueError(f"Palette consumed {name} identity drift")
    if len(proof.consumed_nodes) != len(ledger) \
            or any(a is not b for a, b in zip(proof.consumed_nodes, ledger)):
        raise ValueError("Palette exact consumed-object ledger identity drift")
    if len({id(node) for node in proof.consumed_nodes}) != CONSUMED_NODE_CARDINALITY:
        raise ValueError("Palette proof ledger is not disjoint")
    return proof


def authenticate_palette_frontend(program, source_hash: str | None, profile: str) -> PaletteFrontendProof:
    if profile != PROFILE:
        raise ValueError("Palette frontend profile mismatch")
    if program.key != KEY:
        raise ValueError("Palette frontend program key mismatch")
    raw_hash = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    normalized_hash = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    if raw_hash != RAW_SOURCE_SHA256 or normalized_hash != NORMALIZED_SOURCE_SHA256 \
            or source_hash != RAW_SOURCE_SHA256:
        raise ValueError("Palette source provenance mismatch")
    if program.preprocessor_defines:
        raise ValueError("Palette preprocessor defines drift")
    if _sha(program.functions) != FUNCTIONS_SHA256 or _whole(program) != WHOLE_PROGRAM_SHA256:
        raise ValueError("Palette AST fingerprint drift")
    uniform_names, uniform_types = _uniforms(program)
    if uniform_names != UNIFORM_NAMES or uniform_types != UNIFORM_TYPES:
        raise ValueError("Palette uniform interface drift")
    if len(program.declarations) != 16 or len(program.functions) != 6:
        raise ValueError("Palette declaration/function cardinality drift")
    if tuple(function.name for function in program.functions) != FUNCTION_NAMES:
        raise ValueError("Palette function identity drift")
    if len(program.structs) != 1 or program.structs[0].name != STRUCT_NAME:
        raise ValueError("Palette struct declaration identity drift")
    struct = program.structs[0]
    field_names = tuple(field.name for field in struct.fields)
    field_types = tuple(field.type.display() for field in struct.fields)
    if field_names != STRUCT_FIELDS or field_types != STRUCT_FIELD_TYPES:
        raise ValueError("Palette struct declaration fields drift")
    palette_decl = _palette_decl(program)
    initializer = _authenticate_table(palette_decl)
    construct_count = sum(1 for declaration in program.declarations
                          if declaration.initializer is not None
                          for node in _walk(declaration.initializer)
                          if node.kind == "construct")
    if construct_count != CONST_ARRAY_CONSTRUCT_COUNT:
        raise ValueError("Palette const array construct cardinality drift")
    index_count = _palette_index_count(program, palette_decl.symbol.id)
    values, ledger = _derive_consumed(program)
    if len(values["palette_entries"]) != PALETTE_COUNT \
            or len(values["palette_entry_constructors"]) != PALETTE_ENTRY_CONSTRUCT_COUNT \
            or len(values["vec4_constructors"]) != VEC4_CONSTRUCT_COUNT \
            or len(values["palette_literals"]) != PALETTE_LITERAL_COUNT:
        raise ValueError("Palette nested constructor/literal census drift")
    proof = PaletteFrontendProof(
        program=program, consumed_nodes=ledger, **values,
        program_key=KEY, profile=PROFILE, source_hash=raw_hash,
        normalized_source_hash=normalized_hash, uniform_names=uniform_names,
        uniform_types=uniform_types, struct_name=STRUCT_NAME,
        struct_field_count=len(struct.fields), field_names=field_names,
        field_types=field_types, palette_count=PALETTE_COUNT,
        const_array_construct_count=construct_count,
        palette_index_count=index_count,
    )
    return verify_palette_frontend_proof(program, proof)


def apply_palette_frontend(program, source_hash: str | None, profile: str):
    authenticate_palette_frontend(program, source_hash, profile)
    return program


def allowed_row_fields(key: str):
    return ALLOWED_ROW_FIELDS.get(key, frozenset())


__all__ = [
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
    "PALETTE_FRONTEND_KEYS", "ALLOWED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
    "TABLE_NATIVE_TYPE", "COSINE_NATIVE_TYPE", "TAU_NAME",
    "COSINE_HELPER_NAME", "CLAMP_HELPER_NAME", "LUMINANCE_HELPER_NAME",
    "LINEAR_TO_SRGB_HELPER_NAME",
    "PaletteFrontendProof", "authenticate_palette_frontend", "verify_palette_frontend_proof",
    "apply_palette_frontend",
    "allowed_row_fields",
]
