"""Authenticate the current Effects zoomBlur local products array."""

from dataclasses import dataclass
import hashlib

from tools.glslcpp.frontend.palette_frontend_profile import _whole
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine


KEY = "classicNoisedeck/effects:effects"
RAW_SHA256 = "1a5d9684bef39715572e85aa24419cd002e592b6192cd2dbc3b0f7d53d836a90"
NORMALIZED_SHA256 = "8e2724f35c3dba9c2531ebcdc114de42332fe7d74388a3a70e12aed8347fcbd1"
WHOLE_SHA256 = "6bb2f3c967c83ffb39823c0fc3c228f5380bbbb5284d1eed4ff70b368f9d78a1"
DEFINES = (PreprocessorDefine("EFFECT", "str", "int"),
           PreprocessorDefine("FLIP", "str", "int"))
WRITE_LOOP = (242, 0, 40, "<=", "++", "literal", 41, 1, 1, 41, 82)
READ_LOOP = (251, 0, 41, "<", "++", "literal", 41, 1, 1, 41, 82)


def _nodes(statement):
    for expression in statement.expressions:
        yield from _expression_nodes(expression)
    for child in statement.children:
        yield from _nodes(child)


def _expression_nodes(value):
    yield value
    for child in value.children:
        yield from _expression_nodes(child)


def _loop_record(proof):
    if proof is None:
        return None
    return (proof.induction_symbol_id, proof.start_value, proof.bound_value,
            proof.comparison, proof.update, proof.bound_kind,
            proof.trip_count, proof.lexical_depth, proof.effective_depth,
            proof.lexical_product, proof.entrypoint_charge)


@dataclass(frozen=True, slots=True)
class ZoomBlurLocalArrayProof:
    declaration: object
    write_loop: object
    read_loop: object
    store: object
    store_index: object
    read_index: object
    array_nodes: tuple[object, ...]
    indexes: tuple[object, ...]


def authenticate_zoomblur_local_array(program, source_hash):
    if program.key != KEY or program.preprocessor_defines != DEFINES:
        return None
    current = source_hash == 'b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316'
    expected_raw = 'b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316' if current else RAW_SHA256
    expected_normalized = '681ded19ebe739c5ec7b017f0125f59fbb7b0e63378b86555c1bb0db5cf868e8' if current else NORMALIZED_SHA256
    expected_whole = '8837586c616d95ddad64be70054b15be46395f87603ffbb18f012161d7f8302d' if current else WHOLE_SHA256
    if (source_hash != expected_raw
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != expected_raw
            or hashlib.sha256(program.source.encode()).hexdigest() != expected_normalized
            or _whole(program) != expected_whole):
        raise ValueError("Effects zoomBlur source or typed tree mismatch")
    functions = tuple(function for function in program.functions if function.name == "zoomBlur")
    if len(functions) != 1 or functions[0].signature.id != 96 or len(functions[0].body) != 12:
        raise ValueError("Effects zoomBlur function identity mismatch")
    zoom = functions[0]
    declaration = zoom.body[4].expressions[0]
    write_loop = zoom.body[5]
    read_loop = zoom.body[6]
    if (declaration.kind != "declaration" or declaration.type.display() != "vec3[41]"
            or declaration.symbol_id != 241 or declaration.symbol.name != "products"
            or declaration.children or declaration.span.start_line != (622 if current else 604)
            or write_loop.kind != "for" or read_loop.kind != "for"
            or _loop_record(write_loop.loop_proof) != WRITE_LOOP
            or _loop_record(read_loop.loop_proof) != ((252, 0, 41, "<", "++", "literal", 41, 1, 1, 41, 82) if current else READ_LOOP)):
        raise ValueError("Effects zoomBlur array extent or loop bound mismatch")
    first_nodes = tuple(_nodes(write_loop))
    second_nodes = tuple(_nodes(read_loop))
    stores = tuple(node for node in first_nodes if node.kind == "assign"
                   and node.children and node.children[0].kind == "index"
                   and node.children[0].children[0].symbol_id == 241)
    reads = tuple(node for node in second_nodes if node.kind == "index"
                  and node.children[0].symbol_id == 241)
    if len(stores) != 1 or len(reads) != 1:
        raise ValueError("Effects zoomBlur local array access census mismatch")
    store = stores[0]
    store_index = store.children[0]
    read_index = reads[0]
    subscript = store_index.children[1]
    if (store.operator != "=" or store.span.start_line != (641 if current else 614)
            or subscript.kind != "construct" or subscript.type.display() != "int"
            or len(subscript.children) != 1 or subscript.children[0].symbol_id != 242
            or read_index.span.start_line != (645 if current else 618)
            or read_index.children[1].kind != "id"
            or read_index.children[1].symbol_id != (252 if current else 251)):
        raise ValueError("Effects zoomBlur local array store or read mismatch")
    all_nodes = tuple(node for statement in zoom.body for node in _nodes(statement))
    array_nodes = tuple(node for node in all_nodes if node.type.kind == "array")
    indexes = tuple(node for node in all_nodes if node.kind == "index"
                    and node.children[0].symbol_id == 241)
    if (len(array_nodes) != 3 or len(indexes) != 2
            or indexes != (store_index, read_index)
            or tuple(node.symbol_id for node in array_nodes) != (241, 241, 241)):
        raise ValueError("Effects zoomBlur local array object census mismatch")
    return ZoomBlurLocalArrayProof(declaration, write_loop, read_loop, store,
                                   store_index, read_index, array_nodes, indexes)
