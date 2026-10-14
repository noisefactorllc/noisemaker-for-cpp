"""Authenticate bounded local vec4 arrays in two current shader programs."""

from dataclasses import dataclass
import hashlib

from .palette_frontend_profile import _whole


PROFILES = {
    "filter/temporalAberration:temporalAberration": (
        "d5d298c95e663f89972292ac78767f35c8eba4c3ed08eb24381ac95b97bbc190",
        "203b6acfcdd9ba9ab1fcd1d17042ef0d1bf874e5ac87dd05016ba8695750ac2e",
        "cee174910200513cdab587377525339f2c542308e3bd51059bee7faf6954a5bb",
        ((19, "slots", "vec4[9]"),), 16, 15, 0),
    "synth/navierStokes:nsSmooth": (
        "964147d68d182e7afe016e5fee82ad010e047946121fa407873386cc1c4b4453",
        "5955c9f6a85a884ec2c74c9d071231693eead059e3eb6e9afa8ffdb71ea774f3",
        "4d07db6e828dfe552d0a84a03313b41ccd428a0cff43808b7618c0acb28e2a62",
        ((58, "p", "vec4[9]"), (64, "p", "vec4[16]"),
         (71, "p", "vec4[9]"), (77, "p", "vec4[16]")), 58, 54, 8),
}


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
class LocalVec4ArrayProof:
    declarations: tuple
    array_nodes: tuple
    indexes: tuple
    posts: tuple
    conditional_stores: tuple


def authenticate_local_vec4_arrays(program, source_hash):
    profile = PROFILES.get(program.key)
    if profile is None:
        return None
    raw, normalized, whole, declarations, array_count, index_count, post_count = profile
    if (source_hash != raw
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != raw
            or hashlib.sha256(program.source.encode()).hexdigest() != normalized
            or _whole(program) != whole):
        raise ValueError("local vec4 array source or typed program mismatch")
    # The whole-tree fingerprint binds every store, read and index bound.
    # Temporal slots are all initialized before reads, whose indices clamp
    # to 0..8. Each smoothing loop initializes a full 3x3 or 4x4 array before
    # its literal reads. No array escapes its declaring function or branch.
    nodes = tuple(node for function in program.functions for statement in function.body
                  for node in _statements(statement))
    arrays = tuple(node for node in nodes if node.type.kind == "array")
    decls = tuple(node for node in arrays if node.kind == "declaration")
    indexes = tuple(node for node in nodes if node.kind == "index")
    posts = tuple(node for node in nodes if node.kind == "post")
    conditional_stores = tuple(node for node in nodes if node.kind == "assign"
                               and node.children[0].kind == "index"
                               and node.children[1].kind == "conditional")
    if (tuple((node.symbol_id, node.symbol.name, node.type.display()) for node in decls) != declarations
            or len(arrays) != array_count or len(indexes) != index_count
            or len(posts) != post_count or any(node.children for node in decls)):
        raise ValueError("local vec4 array object census mismatch")
    ids = {node.symbol_id for node in decls}
    if any(node.children[0].symbol_id not in ids or node.children[1].type.display() != "int"
           for node in indexes):
        raise ValueError("local vec4 array index target mismatch")
    if posts and (program.counted_loop_proof.loop_count != 8
                  or program.counted_loop_proof.unproved_loop_count != 0
                  or program.counted_loop_proof.max_lexical_product != 16):
        raise ValueError("local vec4 array counted-loop proof mismatch")
    if len(conditional_stores) != (8 if program.key.startswith("filter/") else 0):
        raise ValueError("local vec4 array conditional-store census mismatch")
    return LocalVec4ArrayProof(decls, arrays, indexes, posts, conditional_stores)
