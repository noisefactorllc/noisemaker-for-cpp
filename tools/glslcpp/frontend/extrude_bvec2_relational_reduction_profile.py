"""Exact bvec2 relational/reduction closure profile for Extrude.

This module does not add a general boolean-vector, relational, or reduction
capability.  It authenticates the one corpus program whose two
``all(lessThanEqual(vec2, vec2))`` trees may be lowered, and returns the
candidate-owned IR objects consumed independently by the validator and the
emitter.

The ``bvec2`` intermediate produced by each ``lessThanEqual`` is consumed
immediately by its exact parent ``all``.  It is never declared, stored,
returned, subscripted, aggregated, or otherwise escaped, and this module
proves that rather than assuming it.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "extrude-bvec2-relational-reduction-v1"
EXTRUDE_KEY = "filter/extrude:extrude"

_RAW_BYTES = 16945
_RAW_SHA256 = "3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29"
_NORMALIZED_BYTES = 5020
_NORMALIZED_SHA256 = "823698d954e1f2f890414a22e6792ca0ca87484ee21d9043cd3c1a347fd7a4ac"
_FUNCTIONS_SHA256 = "cb662c33d7dda0b59a63de9d9ff5e5672e18e137ad43f18f2aa1855cf29e4bb0"
_WHOLE_SHA256 = "1e02d72c7b5c61d49462310fbbcd9f1816d0440f8716bdaaace7c2396ceb36e3"
_INTERFACE_SHA256 = "0e8079c94619fc0e8ad85b401a1bd51211f504c933fa963dbf9c7cdbfaec9fe7"

_MAIN_ID = 36
_DEFINES = (("DEPTH_SOURCE", "int", "0"), ("EXTRUDE_TYPE", "int", "0"))
_LOOP_PROOF = (3, 0, 3, 9, 90, True)

# Exactly the four authenticated nodes, in source order.  Each row is
# (callee, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple).  Nothing outside this tuple may be lowered.
_NODES = (
    ("all", (12, "s1", "s8", "e0", 0), "159:23-159:72", "bool",
     "38eea107e78da89e0f6dd529d77520ccbea907e980df5e0bbc1f01099e8c4efb",
     "declaration", ("bvec2",),
     ("3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1",)),
    ("lessThanEqual", (12, "s1", "s8", "e0", 0, 0), "159:27-159:71", "bvec2",
     "3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1",
     "builtin", ("vec2", "vec2"),
     ("22eda3c5c2624d95d3086837ce97e60ce6e021d0b7df110b6d8e810e7eb38b2b",
      "cd0911899d67d82d41687bb6f2b835b460e179c131a54bf851617abd89254770")),
    ("all", (12, "s1", "s9", "e0", 0, 1), "160:37-160:81", "bool",
     "51877b40b69819a50d527eef19e642e612a9027fcdb58698e707c0818825b2bf",
     "binary", ("bvec2",),
     ("546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04",)),
    ("lessThanEqual", (12, "s1", "s9", "e0", 0, 1, 0), "160:41-160:80", "bvec2",
     "546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04",
     "builtin", ("vec2", "vec2"),
     ("c44a75f30c85e2d6dab1a20d1c9f3d4b1d75fc34270101ade1683b6ac6ba0586",
      "0ef205a50ebf3481cf1cc74247cf488e83e611176bc04004578945ea14d8d4df")),
)

# Both closures live inside the one counted `for` at 143:5-173:6.
_ANCESTOR_KINDS = ("for", "block", "decl")
_ANCESTOR_SPANS = (
    ("143:5-173:6", "143:33-173:6", "159:9-159:73"),
    ("143:5-173:6", "143:33-173:6", "160:9-160:82"),
)

_PROFILE_SHA256 = "ff17a4b84671a14d1e44e5bd8e97f5857b0889a4d8db2803f56fd0a5e7e500b5"
_FROZEN_PROFILE_TUPLE_REPR = """('extrude-bvec2-relational-reduction-v1', 'filter/extrude:extrude', '3be128643867dc78184bd209306cbe524538fd8d6d53a21817fb87f746100e29', (('DEPTH_SOURCE', 'int', '0'), ('EXTRUDE_TYPE', 'int', '0')), 'glsl-f32', 'cb662c33d7dda0b59a63de9d9ff5e5672e18e137ad43f18f2aa1855cf29e4bb0', '1e02d72c7b5c61d49462310fbbcd9f1816d0440f8716bdaaace7c2396ceb36e3', '0e8079c94619fc0e8ad85b401a1bd51211f504c933fa963dbf9c7cdbfaec9fe7', 36, (3, 0, 3, 9, 90, True), (('all', (12, 's1', 's8', 'e0', 0), '159:23-159:72', 'bool', '38eea107e78da89e0f6dd529d77520ccbea907e980df5e0bbc1f01099e8c4efb', 'declaration', ('bvec2',), ('3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1',)), ('lessThanEqual', (12, 's1', 's8', 'e0', 0, 0), '159:27-159:71', 'bvec2', '3048bc23943a393e84d677ebdf15bfc97a942a43635bb8dd95227a594a1ad9e1', 'builtin', ('vec2', 'vec2'), ('22eda3c5c2624d95d3086837ce97e60ce6e021d0b7df110b6d8e810e7eb38b2b', 'cd0911899d67d82d41687bb6f2b835b460e179c131a54bf851617abd89254770')), ('all', (12, 's1', 's9', 'e0', 0, 1), '160:37-160:81', 'bool', '51877b40b69819a50d527eef19e642e612a9027fcdb58698e707c0818825b2bf', 'binary', ('bvec2',), ('546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04',)), ('lessThanEqual', (12, 's1', 's9', 'e0', 0, 1, 0), '160:41-160:80', 'bvec2', '546f5c52a1a44cc20b6dda2b3fd66a38e8b6bc2f68adc2287fcfc8843d771e04', 'builtin', ('vec2', 'vec2'), ('c44a75f30c85e2d6dab1a20d1c9f3d4b1d75fc34270101ade1683b6ac6ba0586', '0ef205a50ebf3481cf1cc74247cf488e83e611176bc04004578945ea14d8d4df'))), (('143:5-173:6', '143:33-173:6', '159:9-159:73'), ('143:5-173:6', '143:33-173:6', '160:9-160:82')))"""

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class ExtrudeBvec2RelationalReductionProof:
    main: TypedFunction
    reductions: tuple[TypedExpression, TypedExpression]
    relationals: tuple[TypedExpression, TypedExpression]
    reduction_parents: tuple[TypedExpression, TypedExpression]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.main, *self.reductions, *self.relationals,
                                *self.reduction_parents]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "EXTRUDE_KEY", "ExtrudeBvec2RelationalReductionProof",
           "authenticate_extrude_bvec2_relational_reduction",
           "apply_extrude_bvec2_relational_reduction",
           "is_authenticated_relational_node", "is_authenticated_reduction_node")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _profile_tuple() -> tuple[object, ...]:
    # Compact frozen package identity.  The whole-program lock below
    # authenticates every detailed coordinate; this tuple exists to prevent
    # silent retargeting of the profile itself.
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_extrude_bvec2_relational_reduction(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> ExtrudeBvec2RelationalReductionProof:
    """Authenticate Extrude and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != EXTRUDE_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or defines != _DEFINES
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")

    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (("inputTex", "resolution", "tileOffset", "fullResolution",
                 "size", "depth", "solidFront"),
                ("inputTex",), ("fragColor",), True, False)):
        raise _fail("resource or binding signature mismatch")

    if len(program.functions) != 9:
        raise _fail("function cardinality mismatch")
    main = next((item for item in program.functions if item.id == _MAIN_ID), None)
    if (main is None
            or (main.name, main.return_type.display(), len(main.parameters),
                len(main.body), _span(main))
            != ("main", "void", 0, 16, "127:1-199:2")):
        raise _fail("main identity mismatch")

    # Collect every all/lessThanEqual site in the WHOLE program, so an
    # additional site anywhere else is a hard failure rather than an
    # unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    bvec_nodes: list[TypedExpression] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                display = None if item.type is None else item.type.display()
                if display is not None and display.startswith("bvec"):
                    bvec_nodes.append(item)
                if item.kind == "builtin" and item.callee in ("all", "lessThanEqual"):
                    if function.id != _MAIN_ID:
                        raise _fail("closure site outside main")
                    located.append((item.callee, path, item, parent, chain))

    if len(located) != len(_NODES):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (callee, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("closure node identity mismatch")

    # Every bvec-typed value in the program must be one of the two authenticated
    # relational results.  This is what forbids declaration, storage, return,
    # subscripting, aggregation, or any other escape.
    relationals = tuple(item for callee, _, item, _, _ in located
                        if callee == "lessThanEqual")
    reductions = tuple(item for callee, _, item, _, _ in located
                       if callee == "all")
    if len(relationals) != 2 or len(reductions) != 2:
        raise _fail("relational or reduction cardinality mismatch")
    if len(bvec_nodes) != 2 or any(
            not any(node is item for item in relationals) for node in bvec_nodes):
        raise _fail("bvec2 value escapes its immediate reduction")

    # Each reduction consumes exactly one child, and that child is exactly the
    # paired relational object (identity, not equality).
    for reduction, relational in zip(reductions, relationals):
        if (len(reduction.children) != 1
                or reduction.children[0] is not relational):
            raise _fail("reduction does not immediately consume its relational")
        if len(relational.children) != 2:
            raise _fail("relational arity mismatch")

    parents = tuple(parent for _, _, _, parent, _ in located)
    reduction_parents = (parents[0], parents[2])
    if any(parent is None for parent in reduction_parents):
        raise _fail("reduction parent mismatch")
    if parents[1] is not reductions[0] or parents[3] is not reductions[1]:
        raise _fail("relational parent is not its paired reduction")

    chains = tuple(chain for _, _, _, _, chain in located)
    chain_kinds = tuple(tuple(item.kind for item in chain) for chain in chains)
    if chain_kinds != (_ANCESTOR_KINDS,) * 4:
        raise _fail("closure ancestry kind mismatch")
    chain_spans = tuple(tuple(_span(item) for item in chain) for chain in chains)
    if (chain_spans[0] != _ANCESTOR_SPANS[0]
            or chain_spans[1] != _ANCESTOR_SPANS[0]
            or chain_spans[2] != _ANCESTOR_SPANS[1]
            or chain_spans[3] != _ANCESTOR_SPANS[1]):
        raise _fail("closure ancestry span mismatch")

    result = ExtrudeBvec2RelationalReductionProof(
        main, reductions, relationals, reduction_parents,
        (chains[0], chains[2]))
    # main, two reductions, two relationals, two reduction parents, and the
    # four unique statements: the shared enclosing `for` and `block`, plus one
    # `decl` per closure.
    if len(result.consumed_objects) != 11:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_extrude_bvec2_relational_reduction(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_extrude_bvec2_relational_reduction(program, source_hash, profile)
    return program


def is_authenticated_relational_node(
        proof: ExtrudeBvec2RelationalReductionProof,
        node: TypedExpression) -> bool:
    """True only for the exact authenticated ``lessThanEqual`` objects."""
    return any(node is item for item in proof.relationals)


def is_authenticated_reduction_node(
        proof: ExtrudeBvec2RelationalReductionProof,
        node: TypedExpression) -> bool:
    """True only for the exact authenticated ``all`` objects."""
    return any(node is item for item in proof.reductions)
