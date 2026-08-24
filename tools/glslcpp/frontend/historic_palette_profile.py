"""Closed, source-bound frontend admission for Historic Palette.

The proof deliberately carries the *live* typed objects consumed by a later
validator/emitter.  Metadata and source hashes alone are insufficient: every
object in the exact consumed ledger is identity checked against the selected
program, and the ledger is required to be disjoint.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .typed_ir import TypedExpression, TypedProgram

PROFILE = "historic-palette-frontend-admission-v1"
KEY = "filter/historicPalette:historicPalette"
KEYS = (KEY,)
SOURCE_PATH = "filter/historicPalette/historicPalette.glsl"
RAW_SHA256 = "cc0feb09e2f90505766a0b8b0d61ca0cf83a1121ec7b104eea5ff806c9ce0c33"
SOURCE_SHA256 = "69d0af70c74a07e9f2d72aeeb7c1495aa353a8a9ebcba0331a655dde7ac9f4b0"
EXPECTED_STRUCT_FIELDS = ("color1", "color2", "color3", "color4", "color5")
EXPECTED_UNIFORMS = ("tileOffset", "fullResolution", "inputTex", "paletteIndex", "smoothness", "rotation", "offset", "repeat", "alpha", "time")
EXPECTED_RESOURCES = (EXPECTED_UNIFORMS, ("inputTex",), ("fragColor",), True, False)
EXPECTED_FUNCTIONS = (
    ("main", 23, 13, "void", (), "51b7830659a5ff118dd34cd4b7add390db1269e76d5a4634c6e9fe7b31f7273a"),
    ("sampleHistoricPalette", 24, 15, "vec3", ("pal", "lum", "smoothAmount"), "d078dc7e11431dbb86117bbda6203777018275a204e5cbb9cc54699143272f86"),
)
DECLARATIONS_SHA256 = "03f8581cd71ba41ca37bb5637ac79bd3366ce4816f908992ced8b326a943266c"
STRUCTS_SHA256 = "5cc52f4897155301a464f2447e8cac3995b7961c5898e8f9c5aa4336d221dd3d"
FUNCTIONS_SHA256 = "0a441ac55a3a8b328a038ca632d0639a55df3db83206d4f8ccdf55244663bfeb"
PALETTE_INITIALIZER_SHA256 = "fd35b53224e42f5a0dff8a7f3abb16db139239ecfe532b4b68e1387aa95e7652"
CONSUMED_NODE_CARDINALITY = 464
# Adapter-only numeric fact.  Historic palette records come from a plain JS
# Number table and materialize only when the mutable Float32Array-equivalent
# color path consumes a lane.
TABLE_NATIVE_TYPE = "glsl::FloatExpr<3>"
LUMINANCE_HELPER_NAME = "historic_palette_number_luminance"
FRACT_HELPER_NAME = "historic_palette_number_fract"
SMOOTHSTEP_HELPER_NAME = "historic_palette_number_smoothstep"
MIX_STORE_HELPER_NAME = "historic_palette_number_mix_store"


@dataclass(frozen=True, slots=True)
class HistoricPaletteProof:
    program: TypedProgram
    struct: Any
    struct_fields: tuple[Any, ...]
    palettes_declaration: Any
    palettes_initializer: TypedExpression
    palette_entries: tuple[TypedExpression, ...]
    vec3_constructors: tuple[TypedExpression, ...]
    palette_literals: tuple[TypedExpression, ...]
    palette_count_declaration: Any
    palette_count_initializer: TypedExpression
    palette_index_reads: tuple[TypedExpression, ...]
    luminance_site: TypedExpression
    t_initializer: TypedExpression
    fract_site: TypedExpression
    sample_function: Any
    sample_member_sites: tuple[TypedExpression, ...]
    table_native_type: str
    functions: tuple[Any, ...]
    consumed_nodes: tuple[Any, ...]

    # Retain the old read-only metadata surface for callers that only record
    # admission facts; the proof itself remains the authoritative payload.
    def __getitem__(self, key: str) -> object:
        values = {
            "profile": PROFILE,
            "program_key": KEY,
            "source_path": SOURCE_PATH,
            "struct_name": self.struct.name,
            "struct_fields": EXPECTED_STRUCT_FIELDS,
            "palette_count": len(self.palette_entries),
            "palette_entry_width": 5,
            "uniforms": EXPECTED_UNIFORMS,
            "functions": tuple(function.name for function in self.functions),
            "resources": self.program.resources,
        }
        try:
            return values[key]
        except KeyError as exc:
            raise KeyError(key) from exc


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: Any):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _adapter_number_sites(program: TypedProgram):
    mains = tuple(item for item in program.functions if item.name == "main")
    samples = tuple(item for item in program.functions
                    if item.name == "sampleHistoricPalette")
    if len(mains) != 1 or len(samples) != 1:
        raise _fail("adapter function cardinality drift")
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
        raise _fail("adapter luminance site drift")
    if (t is None or len(t.children) != 1
            or t.children[0].kind != "binary"
            or t.children[0].operator != "+"
            or t.children[0].type.display() != "float"):
        raise _fail("adapter t initializer drift")
    t_initializer = t.children[0]
    if (len(t_initializer.children) != 2
            or t_initializer.children[0].kind != "binary"
            or t_initializer.children[0].operator != "*"
            or t_initializer.children[0].children[0].kind != "binary"
            or t_initializer.children[0].children[0].operator != "*"
            or t_initializer.children[0].children[0].children[0].symbol.name
            != "lum"
            or t_initializer.children[0].children[0].children[1].kind
            != "binary"
            or t_initializer.children[0].children[0].children[1].operator
            != "-"
            or tuple(child.literal for child in
                     t_initializer.children[0].children[0].children[1].children)
            != ("1.0", "1e-4")
            or t_initializer.children[0].children[1].symbol.name != "repeat"
            or t_initializer.children[1].kind != "binary"
            or t_initializer.children[1].operator != "*"
            or t_initializer.children[1].children[0].symbol.name != "offset"
            or t_initializer.children[1].children[1].kind != "literal"
            or t_initializer.children[1].children[1].literal != "0.01"):
        raise _fail("adapter t arithmetic closure drift")
    main_nodes = tuple(node for statement in mains[0].body
                       for node in _walk_statement(statement))
    fract_sites = tuple(node for node in main_nodes
                        if node.kind == "builtin" and node.callee == "fract")
    if (len(fract_sites) != 1 or fract_sites[0].type.display() != "float"
            or len(fract_sites[0].children) != 1
            or fract_sites[0].children[0].kind != "id"
            or fract_sites[0].children[0].symbol.name != "t"):
        raise _fail("adapter fract site drift")
    sample_nodes = tuple(node for statement in samples[0].body
                         for node in _walk_statement(statement))
    members = tuple(node for node in sample_nodes
                    if node.kind == "member" and node.children
                    and node.children[0].type.display() == "HistoricPalette")
    if (len(members) != 7
            or any(node.member not in {"color1", "color2", "color3",
                                       "color4", "color5"}
                   for node in members)):
        raise _fail("adapter sample member closure drift")
    return (lum.children[0], t_initializer, fract_sites[0],
            samples[0], members)


def _derive_consumed(program: TypedProgram) -> tuple[dict[str, Any], tuple[Any, ...]]:
    if len(program.structs) != 1:
        raise _fail("consumed struct cardinality drift")
    struct = program.structs[0]
    declarations = {item.symbol.name: item for item in program.declarations}
    palettes = declarations.get("PALETTES")
    palette_count = declarations.get("PALETTE_COUNT")
    if palettes is None or palettes.initializer is None:
        raise _fail("live PALETTES declaration/initializer missing")
    if palette_count is None or palette_count.initializer is None:
        raise _fail("live PALETTE_COUNT declaration/initializer missing")
    initializer = palettes.initializer
    entries = tuple(initializer.children)
    vec3 = tuple(child for entry in entries for child in entry.children)
    literals = tuple(child for constructor in vec3 for child in constructor.children)
    reads = tuple(
        expression for function in program.functions for statement in function.body
        for expression in _walk_statement(statement)
        if expression.kind == "index" and len(expression.children) == 2
        and expression.children[0].kind == "id"
        and expression.children[0].symbol is not None
        and expression.children[0].symbol.name == "PALETTES"
    )
    functions = tuple(program.functions)
    luminance, t_initializer, fract, sample, sample_members = (
        _adapter_number_sites(program))
    consumed = (
        (struct,), tuple(struct.fields), (palettes, initializer), entries, vec3,
        literals, (palette_count, palette_count.initializer), reads, functions,
        (luminance, t_initializer, fract), sample_members,
    )
    ledger = tuple(node for group in consumed for node in group)
    ids = tuple(id(node) for node in ledger)
    if len(ledger) != CONSUMED_NODE_CARDINALITY:
        raise _fail(f"consumed-object cardinality drift: {len(ledger)}")
    if len(set(ids)) != len(ids):
        raise _fail("consumed-object ledger is not identity-disjoint")
    return {
        "struct": struct,
        "struct_fields": tuple(struct.fields),
        "palettes_declaration": palettes,
        "palettes_initializer": initializer,
        "palette_entries": entries,
        "vec3_constructors": vec3,
        "palette_literals": literals,
        "palette_count_declaration": palette_count,
        "palette_count_initializer": palette_count.initializer,
        "palette_index_reads": reads,
        "luminance_site": luminance,
        "t_initializer": t_initializer,
        "fract_site": fract,
        "sample_function": sample,
        "sample_member_sites": sample_members,
        "table_native_type": TABLE_NATIVE_TYPE,
        "functions": functions,
    }, ledger


def verify_historic_palette_proof(program: TypedProgram, proof: HistoricPaletteProof) -> HistoricPaletteProof:
    if not isinstance(proof, HistoricPaletteProof) or proof.program is not program:
        raise _fail("proof is not bound to the selected live program")
    expected, ledger = _derive_consumed(program)
    for name, value in expected.items():
        actual = getattr(proof, name)
        if isinstance(value, tuple):
            if len(actual) != len(value) or any(a is not b for a, b in zip(actual, value)):
                raise _fail(f"consumed {name} identity drift")
        elif actual is not value:
            raise _fail(f"consumed {name} identity drift")
    if len(proof.consumed_nodes) != len(ledger) or any(a is not b for a, b in zip(proof.consumed_nodes, ledger)):
        raise _fail("exact consumed-object ledger identity drift")
    if len({id(node) for node in proof.consumed_nodes}) != CONSUMED_NODE_CARDINALITY:
        raise _fail("proof ledger is not disjoint")
    return proof


def authenticate_historic_palette(program: TypedProgram, source_hash: str | None, profile: str | None) -> HistoricPaletteProof:
    if profile != PROFILE or program.key != KEY or source_hash != RAW_SHA256:
        raise _fail("exact key, caller source hash and profile required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if len(raw) != 12528 or hashlib.sha256(raw).hexdigest() != RAW_SHA256:
        raise _fail("raw source drift")
    if len(normalized) != 6963 or hashlib.sha256(normalized).hexdigest() != SOURCE_SHA256:
        raise _fail("normalized source drift")
    if program.preprocessor_defines != () or program.body_status != "analyzed":
        raise _fail("preprocessor/body status drift")
    resources = program.resources
    if (resources.uniforms, resources.samplers, resources.outputs, resources.uses_texture, resources.uses_derivatives) != EXPECTED_RESOURCES:
        raise _fail("exact resource interface drift")
    if len(program.structs) != 1:
        raise _fail("struct cardinality drift")
    struct = program.structs[0]
    fields = tuple(field.name for field in struct.fields)
    if (struct.id, struct.name, fields, tuple(field.type.display() for field in struct.fields), _sha(program.structs)) != (1, "HistoricPalette", EXPECTED_STRUCT_FIELDS, ("vec3",) * 5, STRUCTS_SHA256):
        raise _fail("exact HistoricPalette struct drift")
    if len(program.declarations) != 13 or _sha(program.declarations) != DECLARATIONS_SHA256:
        raise _fail("declaration cardinality/fingerprint drift")
    palette = next((item for item in program.declarations if item.symbol.name == "PALETTES"), None)
    if (palette is None or palette.type.display() != "HistoricPalette[21]" or palette.initializer is None or len(palette.initializer.children) != 21 or _sha(palette.initializer) != PALETTE_INITIALIZER_SHA256):
        raise _fail("exact palette table drift")
    if len(program.functions) != 2 or _sha(program.functions) != FUNCTIONS_SHA256:
        raise _fail("function cardinality/fingerprint drift")
    for function, expected in zip(program.functions, EXPECTED_FUNCTIONS):
        name, ident, body_count, return_type, params, function_sha = expected
        if (function.name, function.id, len(function.body), function.return_type.display(), tuple(parameter.name for parameter in function.parameters), _sha(function)) != expected:
            raise _fail(f"exact {name} function drift")
        if name == "sampleHistoricPalette" and tuple(parameter.type.display() for parameter in function.parameters) != ("HistoricPalette", "float", "float"):
            raise _fail("exact helper parameter ABI drift")
    values, ledger = _derive_consumed(program)
    if len(values["palette_entries"]) != 21 or any(entry.kind != "construct" for entry in values["palette_entries"]):
        raise _fail("palette constructor census drift")
    if len(values["vec3_constructors"]) != 105 or len(values["palette_literals"]) != 315 or len(values["palette_index_reads"]) != 1:
        raise _fail("nested palette/index census drift")
    proof = HistoricPaletteProof(program=program, consumed_nodes=ledger, **values)
    return verify_historic_palette_proof(program, proof)


def apply_historic_palette(program: TypedProgram, source_hash: str | None, profile: str | None):
    authenticate_historic_palette(program, source_hash, profile)
    return program


__all__ = [
    "PROFILE", "KEY", "KEYS", "SOURCE_PATH", "EXPECTED_STRUCT_FIELDS",
    "TABLE_NATIVE_TYPE", "LUMINANCE_HELPER_NAME", "FRACT_HELPER_NAME",
    "SMOOTHSTEP_HELPER_NAME", "MIX_STORE_HELPER_NAME",
    "HistoricPaletteProof", "authenticate_historic_palette",
    "verify_historic_palette_proof", "apply_historic_palette",
]
