"""Authenticate the current Palette3D constant table and its consumers."""

from dataclasses import dataclass
import hashlib

from .palette_frontend_profile import _authenticate_table, _whole


KEY = "filter3d/palette3d:palette3d"
SOURCE_SHA256 = "6425d323befb35d590b818a2bdb269e7bd6fb11aebf148a0c040b3eff0655015"
NORMALIZED_SHA256 = "996f0bdaf13217441d6b04e1be662e311a326a6ca89bed455d58d9ddcf0dd730"
WHOLE_SHA256 = "4c7593d26de2b45edc1b4c62e2afd75bd86673a84096f49c2336f303051ba83d"


def _expressions(node):
    yield node
    for child in node.children:
        yield from _expressions(child)


def _statements(node):
    for value in node.expressions:
        yield from _expressions(value)
    for child in node.children:
        yield from _statements(child)


@dataclass(frozen=True, slots=True)
class Palette3DProof:
    struct: object
    table: object
    constructors: tuple
    members: tuple
    indexes: tuple
    array_nodes: tuple


def authenticate_palette3d(program, source_hash):
    if program.key != KEY:
        return None
    if (source_hash != SOURCE_SHA256
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != SOURCE_SHA256
            or hashlib.sha256(program.source.encode()).hexdigest() != NORMALIZED_SHA256):
        raise ValueError("Palette3D source identity mismatch")
    if _whole(program) != WHOLE_SHA256:
        raise ValueError("Palette3D typed program identity mismatch")
    # The whole-tree digest binds the palette values, table-index guard,
    # function bodies, interfaces, and absence of writes to the const table.
    # These additional checks return the actual admitted objects to each gate.
    if len(program.structs) != 1:
        raise ValueError("Palette3D struct count mismatch")
    struct = program.structs[0]
    if (struct.name != "PaletteEntry"
            or tuple((field.name, field.type.display()) for field in struct.fields)
            != (("amp", "vec4"), ("freq", "vec4"), ("offset", "vec4"), ("phase", "vec4"))):
        raise ValueError("Palette3D struct fields mismatch")
    table, = (item for item in program.declarations if item.symbol.name == "PALETTES")
    initializer = _authenticate_table(table)
    nodes = tuple(node for declaration in program.declarations
                  if declaration.initializer is not None
                  for node in _expressions(declaration.initializer)) + tuple(
        node for function in program.functions for statement in function.body
        for node in _statements(statement))
    constructors = tuple(node for node in nodes if node.kind == "construct"
                         and node.type.display() in {"PaletteEntry", "PaletteEntry[55]"})
    members = tuple(node for node in nodes if node.kind == "member"
                    and node.children[0].type.display() == "PaletteEntry")
    indexes = tuple(node for node in nodes if node.kind == "index")
    if (len(constructors) != 56 or constructors[0] is not initializer
            or len(members) != 5 or len(indexes) != 1
            or indexes[0].children[0].symbol_id != table.symbol.id):
        raise ValueError("Palette3D table-consumer count mismatch")
    array_nodes = (table,) + tuple(node for node in nodes if node.type.kind == "array")
    return Palette3DProof(struct, table, constructors, members, indexes, array_nodes)
