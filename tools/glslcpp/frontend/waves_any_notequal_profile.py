"""Exact ``any(notEqual(vec2, vec2))`` closure profile for Waves.

This module does not add a general boolean-vector, relational, or reduction
capability. It authenticates the one corpus program whose two
``any(notEqual(vec2, vec2))`` trees may be lowered, and returns the
candidate-owned IR objects consumed independently by the validator and the
emitter -- the same node-identity pattern already used for Extrude's
``all(lessThanEqual(vec2, vec2))`` closure
(``extrude_bvec2_relational_reduction_profile.py``), generalized from
``lessThanEqual``/``all`` to ``notEqual``/``any``.

The ``bvec2`` intermediate produced by each ``notEqual`` is consumed
immediately by its exact parent ``any``. It is never declared, stored,
returned, subscripted, aggregated, or otherwise escaped, and this module
proves that rather than assuming it.

Deliberately independent of, and not mutually exclusive with,
``derivative-admission-v1`` -- Waves also carries one ``dFdx``/``dFdy`` pair
under ``if (antialias)``, admitted separately by that profile. Grade's
LUMA-weights/index-expression pair is the precedent for two profiles
legitimately coexisting on one program key.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "waves-any-notequal-admission-v1"
WAVES_KEY = "filter/waves:waves"

_RAW_BYTES = 2622
_RAW_SHA256 = "f4cddf1b3a6c9c68aa677b6743af313e1cdb2bf0a857ce9a1c13edc80f54e3aa"
_NORMALIZED_BYTES = 2167
_NORMALIZED_SHA256 = "f823bcdbac0ff15096e92fcded5c07611077fb7eece203d48f9f08256e968621"
_FUNCTIONS_SHA256 = "0c9efa54e5863e2022d6e4bc8832bfc3f5a9e11c2ffa3114c623a7faf23ec15f"
_WHOLE_SHA256 = "5e6ed7428f47fdc2037d08c76d7b32a24009a76ce9644bc9386922bd9ab5279e"
_INTERFACE_SHA256 = "7e683c0e5c6ae52a90cd2481a28f96e2a163a315bc58bba7b3b7ae564605e753"

_MAIN_ID = 16
_DEFINES: tuple[tuple[str, str, str], ...] = ()
_LOOP_PROOF = (0, 0, 0, 0, 0, True)

# Exactly the four authenticated nodes, in source order. Each row is
# (callee, path, span, result type, node sha, parent kind, child type tuple,
#  child sha tuple). Nothing outside this tuple may be lowered.
_NODES = (
    ("any", (5, "e0"), "41:9-41:45", "bool",
     "e525f2a44a0b06bc9c4e16da34b63fab5146cd990ad1f953140121ac3bde80bb",
     "None", ("bvec2",),
     ("42ac4cc656c61e41227b707f0653cac5210ae3adffded24d86bbd05d8f4e1ddf",)),
    ("notEqual", (5, "e0", 0), "41:13-41:44", "bvec2",
     "42ac4cc656c61e41227b707f0653cac5210ae3adffded24d86bbd05d8f4e1ddf",
     "builtin", ("vec2", "vec2"),
     ("15bb5cbe8980995c2b73f429886a2ab4d36e67542a723ae6d1a4d826fd9e23af",
      "28b4ec8e7fc373e5081ba0bbc617dd670a124d7caf6211400f865557450736e5")),
    ("any", (10, "e0", 0, 0), "67:21-67:57", "bool",
     "b1b5be15833bf3aa6f8b8996fd6d528155c909b9f52d6cccfd940ecbde0e3b3c",
     "conditional", ("bvec2",),
     ("8feddb4eeaf574449997cb5bd541563411d0b225cedba461565cce7102de526a",)),
    ("notEqual", (10, "e0", 0, 0, 0), "67:25-67:56", "bvec2",
     "8feddb4eeaf574449997cb5bd541563411d0b225cedba461565cce7102de526a",
     "builtin", ("vec2", "vec2"),
     ("df07e35df7a044a1b8a508e579a5b27866ce368c0cfa00866d2f1c34f7bb436b",
      "1cb675a20401ad7dc973c684360f64836d86f709757b9402bb71d6a17001964f")),
)

_ANY_SIGNATURE_ID = -4
_NOTEQUAL_SIGNATURE_ID = -32

# The two closures live at two different statements: an `if` condition at
# line 41 and a ternary condition inside a `decl` at line 67.
_ANCESTOR_KINDS = (("if",), ("decl",))
_ANCESTOR_SPANS = (
    ("41:5-44:6",),
    ("67:5-67:108",),
)

_PROFILE_SHA256 = "52b1bf619769ad8798f00a22c7bb6b57d6af68a61a3bf87b7b402fc8bd017f70"
_FROZEN_PROFILE_TUPLE_REPR = """('waves-any-notequal-admission-v1', 'filter/waves:waves', 'f4cddf1b3a6c9c68aa677b6743af313e1cdb2bf0a857ce9a1c13edc80f54e3aa', (), 'glsl-f32', '0c9efa54e5863e2022d6e4bc8832bfc3f5a9e11c2ffa3114c623a7faf23ec15f', '5e6ed7428f47fdc2037d08c76d7b32a24009a76ce9644bc9386922bd9ab5279e', '7e683c0e5c6ae52a90cd2481a28f96e2a163a315bc58bba7b3b7ae564605e753', 16, (0, 0, 0, 0, 0, True), (('any', (5, 'e0'), '41:9-41:45', 'bool', 'e525f2a44a0b06bc9c4e16da34b63fab5146cd990ad1f953140121ac3bde80bb', 'None', ('bvec2',), ('42ac4cc656c61e41227b707f0653cac5210ae3adffded24d86bbd05d8f4e1ddf',)), ('notEqual', (5, 'e0', 0), '41:13-41:44', 'bvec2', '42ac4cc656c61e41227b707f0653cac5210ae3adffded24d86bbd05d8f4e1ddf', 'builtin', ('vec2', 'vec2'), ('15bb5cbe8980995c2b73f429886a2ab4d36e67542a723ae6d1a4d826fd9e23af', '28b4ec8e7fc373e5081ba0bbc617dd670a124d7caf6211400f865557450736e5')), ('any', (10, 'e0', 0, 0), '67:21-67:57', 'bool', 'b1b5be15833bf3aa6f8b8996fd6d528155c909b9f52d6cccfd940ecbde0e3b3c', 'conditional', ('bvec2',), ('8feddb4eeaf574449997cb5bd541563411d0b225cedba461565cce7102de526a',)), ('notEqual', (10, 'e0', 0, 0, 0), '67:25-67:56', 'bvec2', '8feddb4eeaf574449997cb5bd541563411d0b225cedba461565cce7102de526a', 'builtin', ('vec2', 'vec2'), ('df07e35df7a044a1b8a508e579a5b27866ce368c0cfa00866d2f1c34f7bb436b', '1cb675a20401ad7dc973c684360f64836d86f709757b9402bb71d6a17001964f'))), (('41:5-44:6',), ('67:5-67:108',)))"""

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class WavesAnyNotEqualProof:
    main: TypedFunction
    reductions: tuple[TypedExpression, TypedExpression]
    relationals: tuple[TypedExpression, TypedExpression]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.main, *self.reductions, *self.relationals]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "WAVES_KEY", "WavesAnyNotEqualProof",
           "authenticate_waves_any_notequal_admission",
           "apply_waves_any_notequal_admission",
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


def authenticate_waves_any_notequal_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> WavesAnyNotEqualProof:
    """Authenticate Waves and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != WAVES_KEY or source_hash != _RAW_SHA256:
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
                 "time", "strength", "scale", "speed", "wrap", "rotation",
                 "antialias"),
                ("inputTex",), ("fragColor",), True, True)):
        raise _fail("resource or binding signature mismatch")
    if not program.resources.uses_derivatives:
        raise _fail("derivative resource flag must be set")

    if len(program.functions) != 2:
        raise _fail("function cardinality mismatch")
    main = next((item for item in program.functions if item.id == _MAIN_ID), None)
    if (main is None
            or (main.name, main.return_type.display(), len(main.parameters),
                len(main.body), _span(main))
            != ("main", "void", 0, 12, "29:1-81:2")):
        raise _fail("main identity mismatch")

    # Census the WHOLE program: an extra any/notEqual site anywhere else, or
    # any bvec-typed value that is not one of the two notEqual results, is a
    # hard failure, not an unnoticed extra.
    located: list[tuple[str, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    bvec_nodes: list[TypedExpression] = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                display = None if item.type is None else item.type.display()
                if display is not None and display.startswith("bvec"):
                    bvec_nodes.append(item)
                if item.kind == "builtin" and item.callee in ("any", "notEqual"):
                    if function.id != _MAIN_ID:
                        raise _fail("closure site outside main")
                    located.append((item.callee, path, item, parent, chain))

    if len(located) != len(_NODES):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (callee, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "None" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("closure node identity mismatch")

    for callee, path, item, parent, chain in located:
        expected_signature = (_ANY_SIGNATURE_ID if callee == "any"
                              else _NOTEQUAL_SIGNATURE_ID)
        if item.signature_id != expected_signature:
            raise _fail("closure node signature mismatch")

    relationals = tuple(item for callee, _, item, _, _ in located
                        if callee == "notEqual")
    reductions = tuple(item for callee, _, item, _, _ in located
                       if callee == "any")
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
    if parents[1] is not reductions[0] or parents[3] is not reductions[1]:
        raise _fail("relational parent is not its paired reduction")

    chains = tuple(chain for _, _, _, _, chain in located)
    chain_kinds = tuple(tuple(item.kind for item in chain) for chain in chains)
    if chain_kinds != (_ANCESTOR_KINDS[0], _ANCESTOR_KINDS[0],
                       _ANCESTOR_KINDS[1], _ANCESTOR_KINDS[1]):
        raise _fail("closure ancestry kind mismatch")
    chain_spans = tuple(tuple(_span(item) for item in chain) for chain in chains)
    if (chain_spans[0] != _ANCESTOR_SPANS[0] or chain_spans[1] != _ANCESTOR_SPANS[0]
            or chain_spans[2] != _ANCESTOR_SPANS[1]
            or chain_spans[3] != _ANCESTOR_SPANS[1]):
        raise _fail("closure ancestry span mismatch")

    result = WavesAnyNotEqualProof(main, reductions, relationals,
                                   (chains[0], chains[2]))
    # main, two reductions, two relationals, and the two unique decl/if
    # statements (one per closure -- no shared enclosing statement here,
    # unlike Extrude's shared `for`/`block`).
    if len(result.consumed_objects) != 7:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_waves_any_notequal_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_waves_any_notequal_admission(program, source_hash, profile)
    return program


def is_authenticated_relational_node(
        proof: WavesAnyNotEqualProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated ``notEqual`` objects."""
    return any(node is item for item in proof.relationals)


def is_authenticated_reduction_node(
        proof: WavesAnyNotEqualProof, node: TypedExpression) -> bool:
    """True only for the exact authenticated ``any`` objects."""
    return any(node is item for item in proof.reductions)
