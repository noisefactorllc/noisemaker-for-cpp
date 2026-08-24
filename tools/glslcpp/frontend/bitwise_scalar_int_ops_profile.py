"""Exact JavaScript-Number profile for ``synth/bitwise:bitwise``.

The canonical CPU factory performs ordinary arithmetic in binary64 and
applies JavaScript ToInt32 only at explicit ``int(...)`` constructors and
bitwise operators.  Keeping the source parser's GLSL ``int`` inference would
therefore introduce signed-overflow undefined behavior before those
boundaries.  This schema-versioned v2 transform retypes the complete frozen
Number region (five shared symbols, ten arithmetic nodes, and eleven
assignments) to the existing ``FLOAT`` IR type, whose scalar C++ storage is
``double``.  The four explicit constructors and ten bitwise results remain
``INT`` and are emitted through exact JavaScript conversion/bitwise helpers.

Authentication is identity-scoped and fail-closed on both sides of the
transition.  Frozen source, interface, pre-tree, post-tree, per-site, symbol
identity, type-shape, and ordered-census checks prevent this exception from
becoming a general capability or silently expanding to another program.
Three exact source ``float(...)`` calls are Number-preserving identities in
the canonical factory; two other calls remain true Math.fround boundaries.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass

from .semantic_types import FLOAT
from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEYS = ("synth/bitwise:bitwise",)
PROFILE = "bitwise-scalar-int-ops-v2"
PROFILES = {
    "synth/bitwise:bitwise": PROFILE,
}
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

__all__ = (
    "KEYS", "PROFILE", "PROFILES", "BitwiseNumberSemanticsProof",
    "authenticate_bitwise_scalar_int_ops",
    "authenticate_bitwise_scalar_int_ops_transition",
    "authenticate_bitwise_int_to_float_narrowing_skip",
    "apply_bitwise_scalar_int_ops",
)


@dataclass(frozen=True, slots=True)
class BitwiseNumberSemanticsProof:
    bitwise_nodes: tuple[TypedExpression, ...]
    arithmetic_nodes: tuple[TypedExpression, ...]
    int_constructors: tuple[TypedExpression, ...]
    number_symbols: tuple[object, ...]
    number_expressions: tuple[TypedExpression, ...]
    number_assignments: tuple[TypedExpression, ...]
    narrowing_skip_nodes: tuple[TypedExpression, ...]
    float_identity_nodes: tuple[TypedExpression, ...]
    float_boundary_nodes: tuple[TypedExpression, ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values = (
            *self.bitwise_nodes,
            *self.arithmetic_nodes,
            *self.int_constructors,
            *self.number_symbols[:2],
            *self.number_expressions,
            *self.number_assignments,
            *self.float_identity_nodes,
        )
        if len({id(value) for value in values}) != len(values):
            raise _fail("post-transform proof objects are not disjoint")
        return values


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


_LOCKS = {
    "synth/bitwise:bitwise": {
        "profile": PROFILE,
        "raw_bytes": 3095,
        "raw_sha256": "1beb9d4b4fff3466587b9c942af3b1a46c0f35a1bf41874c7461c18dcf2f923f",
        "normalized_bytes": 2334,
        "normalized_sha256": "52122dc5f24fd4172733949aecf1db8b52e697d08fd14581c283d096ec371cc3",
        "whole_sha256": "878c81ea2fc8e43fb81af8fa21464c0431121d1d3aab1f7630c90496874ec2fc",
        "interface_sha256": "b13187b02a83186b25ce374c7f521ab6535dbfc659f5abad36f2c84331414ac9",
        "functions_sha256": "861f0039b6b52d158ec33603d008cdf731fec3462a43e69e56010e558cb7dedd",
        # (function_id, function_name, span, sha256, kind, operator)
        "sites": (
            (23, "bitOp", "34:27-34:32", "604f27c57ec1fc6a0449a533fc52f2211040f0ca935ebca39b8ced773924627e", "binary", "^"),
            (23, "bitOp", "35:27-35:32", "17f3c0867ee95f47b61c55816f49e1f815b632cff9b3273a96d3396958a893d4", "binary", "&"),
            (23, "bitOp", "36:27-36:32", "1854a02b3cf7402e1f346a9a08b99788255d839c9b88671752ed1c769501d0ab", "binary", "|"),
            (23, "bitOp", "37:27-37:35", "c193b941765339b27e4afe283117c5a9a6b944471c1f5b9acf700c564920079c", "unary", "~"),
            (23, "bitOp", "37:29-37:34", "0ee647d28fdc43c77c7302517bd74a03796fbda71e7f555636195a3a14d31550", "binary", "&"),
            (23, "bitOp", "38:27-38:35", "74e028f7f43d6e67ba6fe62043d3f28c8f02db08494dd2139815507b8478cd3f", "unary", "~"),
            (23, "bitOp", "38:29-38:34", "429d19847e7c30864e4fd035b4412be793b47ffe370b76f198def9a31d0b19a6", "binary", "^"),
            (23, "bitOp", "42:9-42:14", "0ae94297673a7007cf98b081af224358ae5665bc938b69f7920ebbe58a874247", "binary", "&"),
            (25, "main", "68:9-68:17", "726f08d8f1f43479a26285876f671a74b098c6101cbee1a6e218ccfc3a43e6d8", "binary", "^"),
            (25, "main", "69:9-69:23", "200a660d17d7ebfc934463a896dd6cbf694d3610ecb7ed03dd0bce087587dc2a", "binary", "^"),
        ),
    },
}


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_statement(statement: TypedStatement, results: list) -> None:
    for expression in statement.expressions:
        _walk_expression(expression, results)
    for child in statement.children:
        _walk_statement(child, results)


def _walk_expression(value: TypedExpression, results: list) -> None:
    results.append(value)
    for child in value.children:
        _walk_expression(child, results)


def _authenticate_pre_bitwise_nodes(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return only the exact frozen bitwise-operator node
    identities for `program.key`'s scalar-int bitwise closure.

    Every `binary` node with operator in {&, |, ^} and every `unary` node
    with operator `~`, anywhere in the whole program, is censused -- not
    merely the frozen sites looked up -- and the count must match the frozen
    site count exactly. This is the whole-program completeness proof: no
    stray, un-authenticated bitwise node (in particular, no `>>` or `<<`
    shift, which this profile deliberately never admits) can exist anywhere
    in the program.
    """
    lock = _LOCKS.get(program.key)
    if lock is None:
        raise _fail("selected key is not in the bitwise scalar-int-ops cluster")
    if profile != lock["profile"]:
        raise _fail("exact profile carrier required")
    if source_hash != lock["raw_sha256"]:
        raise _fail("exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != lock["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != lock["raw_sha256"]
            or len(normalized) != lock["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != lock["normalized_sha256"]
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != lock["functions_sha256"]
            or _whole_fingerprint(program) != lock["whole_sha256"]
            or _interface_fingerprint(program) != lock["interface_sha256"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth, proof.max_lexical_product,
                          proof.entrypoint_charge, proof.call_graph_acyclic)
            != (0, 0, 0, 0, 0, True)):
        raise _fail("loop proof mismatch")

    census: list[tuple[TypedExpression, int, str]] = []
    for function in program.functions:
        results: list[TypedExpression] = []
        for statement in function.body:
            _walk_statement(statement, results)
        for node in results:
            if node.kind == "binary" and node.operator in ("&", "|", "^"):
                census.append((node, function.signature.id, function.name))
            elif node.kind == "unary" and node.operator == "~":
                census.append((node, function.signature.id, function.name))

    expected_sites = lock["sites"]
    if len(census) != len(expected_sites):
        raise _fail("bitwise-node census cardinality mismatch")

    resolved: list[TypedExpression] = []
    for (node, function_id, function_name), expected in zip(census, expected_sites):
        (expected_function_id, expected_function_name, expected_span, expected_sha,
         expected_kind, expected_operator) = expected
        if (function_id != expected_function_id
                or function_name != expected_function_name
                or _span(node) != expected_span
                or _sha(node) != expected_sha
                or node.kind != expected_kind
                or node.operator != expected_operator
                or node.type.display() != "int"):
            raise _fail("bitwise site node profile mismatch")
        if expected_kind == "binary":
            if (len(node.children) != 2
                    or any(child.type.display() != "int" for child in node.children)):
                raise _fail("bitwise binary operand type mismatch")
        else:
            if (len(node.children) != 1
                    or node.children[0].type.display() != "int"):
                raise _fail("bitwise unary operand type mismatch")
        resolved.append(node)

    return tuple(resolved)


# ---------------------------------------------------------------------------
# The two legacy `bitOp` Number-preserving `float(...)` identities.  This
# table remains separate for compatibility with the original focused proof;
# the v2 profile below also authenticates the third identity, `float(mask)`,
# and the two genuine float32 boundaries.
#
# The GLSL source explicitly narrows both operands to float32 before
# dividing. The compiled JS factory does not: it materializes
# the source's `float(r)`/`float(m)` constructor calls as bare identity
# no-ops -- `return (r) / (m);`, with r/m staying full-precision JS Numbers
# through the division, narrowed to float32 only once, at the
# `fragColor[i] = ...` Float32Array store. Verified directly by reading the
# compiled factory text (`src/effects/generated/canonical-kernels.js`, the
# `bitOp` closure), not inferred.
#
# This is invisible for every already-shipped `float(int)` site in the
# corpus, because their `int` operands never leave the exactly-representable-
# in-float32 range (|n| < 2**24). `bitOp`'s `r`/`m` are the AND/XOR/OR/NAND/
# XNOR of two int32 hash-shifted coordinates and can be arbitrarily large in
# magnitude, so the extra narrowing step is observable: for
# `and-rgb-int32min-offsets-near-max-mask`'s pixel (0,0), r=101720324 (well
# past 2**24) and the C++ port's premature `float(r)` rounds it to a
# different float32 than `static_cast<double>(r)` would, producing a 1-ULP-
# wrong final result at `float(r)/float(m)` bit-exactness (verified: the
# no-premature-narrow value 0.0473672170412574 -> 0x3d420421 matches the real
# runtime; the premature-narrow value does not).
#
# Authenticated by node identity, never by widening the general
# `float(intExpr)` constructor-emission rule.  This is scoped to these two
# exact nodes in this one program only.

_NARROWING_SKIP_LOCKS = {
    "synth/bitwise:bitwise": {
        "sites": (
            # (function_id, function_name, span, sha256, base_symbol_id, base_name)
            (23, "bitOp", "43:12-43:20", "449302d399a91597d99f9733805aa8f8db46139ba1f464f6a88cc9d6da55c7b2", 27, "r"),
            (23, "bitOp", "43:23-43:31", "6cd887c054649bb68230ffd2b4e113c96c33ecc8b648cebf3c43c3f0efdf514a", 22, "m"),
        ),
    },
}


def _authenticate_pre_narrowing_skip(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return the exact `float(intExpr)` construct nodes
    inside `bitOp`'s return statement that the real JS runtime materializes
    without an intermediate float32 narrowing step.

    Reuses the SAME whole-program identity gate as
    `authenticate_bitwise_scalar_int_ops` (raw/normalized/whole/interface/
    functions hashes, loop proof, absence of unrelated proof carriers) --
    this function is only ever called for the same program under the same
    profile string, so there is no independent narrower fingerprint to
    maintain.
    """
    lock = _NARROWING_SKIP_LOCKS.get(program.key)
    if lock is None:
        raise _fail("selected key is not in the bitwise narrowing-skip cluster")
    base_lock = _LOCKS.get(program.key)
    if base_lock is None or profile != base_lock["profile"]:
        raise _fail("exact profile carrier required")
    if source_hash != base_lock["raw_sha256"]:
        raise _fail("exact caller source digest required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != base_lock["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != base_lock["raw_sha256"]
            or len(normalized) != base_lock["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != base_lock["normalized_sha256"]
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != base_lock["functions_sha256"]
            or _whole_fingerprint(program) != base_lock["whole_sha256"]
            or _interface_fingerprint(program) != base_lock["interface_sha256"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    bitop = next((f for f in program.functions if f.name == "bitOp"), None)
    if bitop is None or not bitop.body:
        raise _fail("bitOp function missing")
    returned = bitop.body[-1]
    if returned.kind != "return" or len(returned.expressions) != 1:
        raise _fail("bitOp return-statement shape mismatch")
    division = returned.expressions[0]
    if (division.kind != "binary" or division.operator != "/"
            or division.type.display() != "float" or len(division.children) != 2):
        raise _fail("bitOp division-expression shape mismatch")

    resolved: list[TypedExpression] = []
    for node, expected in zip(division.children, lock["sites"]):
        (expected_function_id, expected_function_name, expected_span, expected_sha,
         expected_base_symbol_id, expected_base_name) = expected
        if (bitop.signature.id != expected_function_id
                or bitop.name != expected_function_name
                or _span(node) != expected_span
                or _sha(node) != expected_sha
                or node.kind != "construct"
                or node.constructor_type is None
                or node.constructor_type.display() != "float"
                or len(node.children) != 1
                or node.children[0].kind != "id"
                or node.children[0].type.display() != "int"
                or node.children[0].symbol_id != expected_base_symbol_id
                or node.children[0].symbol is None
                or node.children[0].symbol.name != expected_base_name):
            raise _fail("int-to-float narrowing-skip site mismatch")
        resolved.append(node)

    return tuple(resolved)


# Ordered, machine-readable v2 census.  Each row is
# (function id, function name, normalized span, operator-or-kind, pre-node SHA).
_ARITHMETIC_SITES = (
    (23, "bitOp", "39:27-39:32", "*", "1d7463079b039d6495b04d80c3da5b9398e32e3b0cdc3db1b32e62852774cd23"),
    (23, "bitOp", "40:27-40:32", "+", "d938ed89ef5adf45f47cffdc7ff5cf93108a627810430ef97528a8158171ea31"),
    (23, "bitOp", "41:27-41:32", "-", "e7cd292d264cdd447144e6a8e043d7510f78e15e28bc0c0d8decb68f83d484ed"),
    (25, "main", "64:13-64:68", "+", "5668733b44f347add0e1bc983f99ea1a9d642dbc91539a15f17a7156f38b642a"),
    (25, "main", "64:13-64:55", "+", "7bedd989e744abceeed4b0151fe564bb9c1fc8eb6a8b0400634fbc8dd1091894"),
    (25, "main", "65:13-65:55", "+", "030d2735c1462f80047d48485a8efea31e97d54f0657ed436e36d15b853a7e63"),
    (25, "main", "69:14-69:22", "*", "6e60f205e08f9280f544bcd335b0a78006caab85b2f548dc7051458de31b56b2"),
    (25, "main", "79:25-79:40", "+", "1f19b467d9c098db68be83134a58fbeb1f0580b677f97a72ae84f65acc6e3e1b"),
    (25, "main", "80:28-80:43", "+", "ba4b16285f55e79ed7d659e4fb39402f2264f36f7219309f1f0aa961747604af"),
    (25, "main", "86:46-86:54", "+", "778a56c4a4748315b9ccf39b8a6f2af6a93cc3a9379609907a93e6611cfc8f52"),
)
_INT_CONSTRUCTOR_SITES = (
    (25, "main", "61:22-61:67", "construct", "d6492ca28dd60c64a9e7e2c94ab31852bb95eb24b8f3ca0e03dd607214b54ab9"),
    (25, "main", "61:45-61:56", "construct", "ffa54b7e11fcb632c2057e1e9b3dcd9b675af2b3e64657cab11164177d3aaa00"),
    (25, "main", "64:13-64:45", "construct", "d9287a97f87a62c689be1616a555e12beffb7765c61b8e89565a358ae06ce53b"),
    (25, "main", "65:13-65:45", "construct", "c6a6ca92cc5e500dd222099d47bf16cea40500a6838a041f66c6d95e9fe6d3ba"),
)
_NUMBER_SYMBOL_SITES = (
    (23, "bitOp", 19, "a", "parameter", "32:13-32:18"),
    (23, "bitOp", 20, "b", "parameter", "32:20-32:25"),
    (23, "bitOp", 27, "r", "local", "33:9-33:14"),
    (25, "main", 38, "x", "local", "64:9-64:68"),
    (25, "main", 39, "y", "local", "65:9-65:55"),
)
_ASSIGNMENT_SITES = (
    (23, "bitOp", "34:23-34:32", 27, "07ded36eff0d14477fa6261a7e0b93a63afdd01dd05d2643ce04907f008c9670"),
    (23, "bitOp", "35:23-35:32", 27, "2bd545a1362313f44a4f5037a6606cf9f3e1ba8a56d60013f29afe2ca53131f2"),
    (23, "bitOp", "36:23-36:32", 27, "7355342e348d1db0fe0299774edd3a466a6f3a8539c426793842a451ea917bfd"),
    (23, "bitOp", "37:23-37:35", 27, "c4e5beb7066e665d8cf69b89435c9d3f94f74e3ed2abfddd0d47dc0d40238b04"),
    (23, "bitOp", "38:23-38:35", 27, "e099f296c3ffe5d44de2066c2a05cc3b5531e7ae8d524fcb12387556fedeaba3"),
    (23, "bitOp", "39:23-39:32", 27, "6c1356c7748baa3321d1157b56649e8590855606bc34eb08021584dc3b46c53a"),
    (23, "bitOp", "40:23-40:32", 27, "f6ffc707fe7aa1cd799382183c30c0f006bd63f5408076d6675462c0f5731777"),
    (23, "bitOp", "41:23-41:32", 27, "7abf8b9b7b0d29226f14fbb13cc62c2951de37be09b4af187ef651d187881bc9"),
    (23, "bitOp", "42:5-42:14", 27, "89585c9cc9966c782978dc94d0fa577b243f077707985efb27a3f146152f6306"),
    (25, "main", "68:5-68:17", 38, "a3a29ecd75a63e182aabd903c7877fcf6a186b73fb6a8833c7ec9882bae06a00"),
    (25, "main", "69:5-69:23", 39, "08c6061050439c8d102a0a2643183509255db83d9926f7612ca5fb7656380173"),
)
_FLOAT_IDENTITY_SITES = (
    (23, "bitOp", "43:12-43:20", "449302d399a91597d99f9733805aa8f8db46139ba1f464f6a88cc9d6da55c7b2"),
    (23, "bitOp", "43:23-43:31", "6cd887c054649bb68230ffd2b4e113c96c33ecc8b648cebf3c43c3f0efdf514a"),
    (25, "main", "86:26-86:37", "6e409166f36576347f6d9ca4e6baf5813fa60484e5f95f9cc9486a5679bfa254"),
)
_FLOAT_BOUNDARY_SITES = (
    (25, "main", "61:39-61:57", "001672b7b06e059ec2283e3aa55ad8922df2cfb8b534a999ed03bc64bdffa295"),
    (25, "main", "86:40-86:55", "a378b187c8d28549aa4b0d43e1550791d2d8b7c01641cc77c532660eb0c8cc15"),
)
_POST_BITWISE_OPERAND_TYPES = (
    ("float", "float"), ("float", "float"), ("float", "float"),
    ("int",), ("float", "float"), ("int",), ("float", "float"),
    ("float", "int"), ("float", "int"), ("float", "float"),
)
_POST_ARITHMETIC_OPERAND_TYPES = (
    ("float", "float"), ("float", "float"), ("float", "float"),
    ("float", "int"), ("int", "int"), ("int", "int"),
    ("int", "int"), ("float", "int"), ("float", "int"),
    ("int", "int"),
)
_POST_INT_CONSTRUCTOR_OPERAND_TYPES = (
    ("float",), ("float",), ("float",), ("float",),
)
_POST_FLOAT_IDENTITY_OPERAND_TYPES = (
    ("float",), ("int",), ("int",),
)
_POST_FLOAT_BOUNDARY_OPERAND_TYPES = (
    ("int",), ("float",),
)

# Filled from the deterministic transform below, then frozen.  Empty values
# are deliberately rejected by the public authenticator.
_POST_FUNCTIONS_SHA256 = "1a5b63feca3a2b9fcb027193176aba9d1b23b19c8ceaa2418a23af4b79388e0f"
_POST_WHOLE_SHA256 = "bd05a3b62d306265125cfcfbd45020d79053cf6d4a65b5a218f7e360bdfacddc"
_POST_CENSUS_SHA256 = "185941eeae468eb6a01c5b65beab7c95a306846f06ba36655bed5c57096bd41a"


def _all_expressions(program: TypedProgram) -> list[tuple[object, TypedExpression]]:
    result: list[tuple[object, TypedExpression]] = []
    for function in program.functions:
        def expression(value: TypedExpression) -> None:
            result.append((function, value))
            for child in value.children:
                expression(child)
        def statement(value: TypedStatement) -> None:
            for item in value.expressions:
                expression(item)
            for child in value.children:
                statement(child)
        for item in function.body:
            statement(item)
    return result


def _match_sites(program: TypedProgram, sites: tuple, predicate) -> tuple[TypedExpression, ...]:
    remaining = list(sites)
    resolved: list[TypedExpression] = []
    for function, node in _all_expressions(program):
        if not predicate(node):
            continue
        if not remaining:
            raise _fail("profiled node census cardinality mismatch")
        expected = remaining.pop(0)
        if (function.id, function.name, _span(node)) != expected[:3]:
            raise _fail("profiled node owner/span mismatch")
        resolved.append(node)
    if remaining:
        raise _fail("profiled node census cardinality mismatch")
    return tuple(resolved)


def _pre_profile(program: TypedProgram, source_hash: str | None,
                 profile: str | None) -> BitwiseNumberSemanticsProof:
    bitwise = _authenticate_pre_bitwise_nodes(program, source_hash, profile)
    narrowing = _authenticate_pre_narrowing_skip(program, source_hash, profile)
    expressions = _all_expressions(program)
    arithmetic = _match_sites(
        program, _ARITHMETIC_SITES,
        lambda value: value.kind == "binary" and value.operator in {"+", "-", "*"}
        and value.type.display() == "int")
    constructors = _match_sites(
        program, _INT_CONSTRUCTOR_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "int")
    for node, expected in zip(arithmetic, _ARITHMETIC_SITES):
        if node.operator != expected[3] or _sha(node) != expected[4]:
            raise _fail("arithmetic node profile mismatch")
    for node, expected in zip(constructors, _INT_CONSTRUCTOR_SITES):
        if _sha(node) != expected[4] or node.type.display() != "int":
            raise _fail("integer constructor profile mismatch")

    symbol_by_id: dict[int, object] = {}
    for function in program.functions:
        for parameter in function.parameters:
            if parameter.id in {19, 20}:
                symbol_by_id[parameter.id] = parameter
    for _, node in expressions:
        if node.kind == "declaration" and node.symbol_id in {27, 38, 39}:
            symbol_by_id[node.symbol_id] = node.symbol
    if tuple(symbol_by_id) != (19, 20, 27, 38, 39):
        raise _fail("Number symbol census mismatch")
    number_symbols = tuple(symbol_by_id[symbol_id]
                           for symbol_id in (19, 20, 27, 38, 39))
    for symbol, expected in zip(number_symbols, _NUMBER_SYMBOL_SITES):
        function_id, function_name, symbol_id, name, storage, span = expected
        owner = next(function for function in program.functions
                     if (symbol in function.parameters or any(
                         node.kind == "declaration" and node.symbol is symbol
                         for candidate_function, node in expressions
                         if candidate_function is function)))
        if (owner.id, owner.name, symbol.id, symbol.name, symbol.storage,
                _span(symbol), symbol.type.display(), symbol.writable,
                symbol.direction) != (
                    function_id, function_name, symbol_id, name, storage,
                    span, "int", True, "in"):
            raise _fail("Number symbol identity mismatch")
    number_expressions = tuple(
        node for _, node in expressions
        if node.kind in {"id", "declaration"}
        and node.symbol_id in symbol_by_id)
    if len(number_expressions) != 44:
        raise _fail("Number expression census mismatch")
    for node in number_expressions:
        if (node.type.display() != "int" or node.symbol is not symbol_by_id[node.symbol_id]):
            raise _fail("Number expression symbol/type mismatch")
    assignments = tuple(
        node for _, node in expressions
        if node.kind == "assign" and len(node.children) == 2
        and node.children[0].kind == "id"
        and node.children[0].symbol_id in symbol_by_id)
    if len(assignments) != len(_ASSIGNMENT_SITES):
        raise _fail("Number assignment census mismatch")
    for (function, node), expected in zip(
            ((function, node) for function, node in expressions
             if any(node is assignment for assignment in assignments)),
            _ASSIGNMENT_SITES):
        if ((function.id, function.name, _span(node), node.children[0].symbol_id,
             _sha(node)) != expected or node.type.display() != "int"):
            raise _fail("Number assignment profile mismatch")
    float_identity = _match_sites(
        program, _FLOAT_IDENTITY_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "float"
        and _span(value) in {site[2] for site in _FLOAT_IDENTITY_SITES})
    float_boundaries = _match_sites(
        program, _FLOAT_BOUNDARY_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "float"
        and _span(value) in {site[2] for site in _FLOAT_BOUNDARY_SITES})
    for node, expected in zip(float_identity, _FLOAT_IDENTITY_SITES):
        if _sha(node) != expected[3]:
            raise _fail("Number-preserving float constructor mismatch")
    for node, expected in zip(float_boundaries, _FLOAT_BOUNDARY_SITES):
        if _sha(node) != expected[3]:
            raise _fail("float32 boundary constructor mismatch")
    return BitwiseNumberSemanticsProof(
        bitwise, arithmetic, constructors, number_symbols,
        number_expressions, assignments, narrowing, float_identity,
        float_boundaries)


def _transform_program(program: TypedProgram,
                       proof: BitwiseNumberSemanticsProof) -> TypedProgram:
    replacements = {
        symbol.id: dataclasses.replace(symbol, type=FLOAT)
        for symbol in proof.number_symbols
    }

    def expression(value: TypedExpression) -> TypedExpression:
        children = tuple(expression(child) for child in value.children)
        result = dataclasses.replace(value, children=children)
        if value.kind in {"id", "declaration"} and value.symbol_id in replacements:
            result = dataclasses.replace(
                result, type=FLOAT, symbol=replacements[value.symbol_id])
        if (any(value is node for node in proof.arithmetic_nodes)
                or any(value is node for node in proof.number_assignments)):
            result = dataclasses.replace(result, type=FLOAT)
        return result

    def statement(value: TypedStatement) -> TypedStatement:
        return dataclasses.replace(
            value,
            expressions=tuple(expression(item) for item in value.expressions),
            children=tuple(statement(item) for item in value.children),
        )

    functions = []
    for function in program.functions:
        signature = dataclasses.replace(
            function.signature,
            parameters=tuple(replacements.get(parameter.id, parameter)
                             for parameter in function.parameters),
        )
        functions.append(dataclasses.replace(
            function, signature=signature,
            body=tuple(statement(item) for item in function.body)))
    return dataclasses.replace(program, functions=tuple(functions))


def _post_profile(program: TypedProgram, source_hash: str | None,
                  profile: str | None) -> BitwiseNumberSemanticsProof:
    lock = _LOCKS["synth/bitwise:bitwise"]
    if (program.key != "synth/bitwise:bitwise" or profile != PROFILE
            or source_hash != lock["raw_sha256"]
            or hashlib.sha256(program.raw_source.encode()).hexdigest()
                != lock["raw_sha256"]
            or hashlib.sha256(program.source.encode()).hexdigest()
                != lock["normalized_sha256"]
            or _interface_fingerprint(program) != lock["interface_sha256"]
            or program.body_status != "analyzed" or program.preprocessor_defines != ()):
        raise _fail("source, key, carrier, interface, or define mismatch")
    if (not _POST_FUNCTIONS_SHA256 or not _POST_WHOLE_SHA256
            or _sha(program.functions) != _POST_FUNCTIONS_SHA256
            or _whole_fingerprint(program) != _POST_WHOLE_SHA256):
        raise _fail("post-transform function or whole-program mismatch")

    expressions = _all_expressions(program)
    bitwise = _match_sites(
        program, lock["sites"],
        lambda value: ((value.kind == "binary" and value.operator in {"&", "|", "^"})
                       or (value.kind == "unary" and value.operator == "~")))
    arithmetic = _match_sites(
        program, _ARITHMETIC_SITES,
        lambda value: value.kind == "binary" and value.operator in {"+", "-", "*"}
        and value.type.display() == "float"
        and _span(value) in {site[2] for site in _ARITHMETIC_SITES})
    constructors = _match_sites(
        program, _INT_CONSTRUCTOR_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "int")
    symbol_by_id: dict[int, object] = {}
    for function in program.functions:
        for parameter in function.parameters:
            if parameter.id in {19, 20}:
                symbol_by_id[parameter.id] = parameter
    for _, node in expressions:
        if node.kind == "declaration" and node.symbol_id in {27, 38, 39}:
            symbol_by_id[node.symbol_id] = node.symbol
    number_symbols = tuple(symbol_by_id[symbol_id]
                           for symbol_id in (19, 20, 27, 38, 39))
    number_expressions = tuple(
        node for _, node in expressions
        if node.kind in {"id", "declaration"} and node.symbol_id in symbol_by_id)
    assignments = tuple(
        node for _, node in expressions
        if node.kind == "assign" and len(node.children) == 2
        and node.children[0].kind == "id"
        and node.children[0].symbol_id in symbol_by_id)
    narrowing = tuple(node for _, node in expressions
                      if node.kind == "construct" and _span(node) in {
                          _NARROWING_SKIP_LOCKS[program.key]["sites"][0][2],
                          _NARROWING_SKIP_LOCKS[program.key]["sites"][1][2]})
    float_identity = _match_sites(
        program, _FLOAT_IDENTITY_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "float"
        and _span(value) in {site[2] for site in _FLOAT_IDENTITY_SITES})
    float_boundaries = _match_sites(
        program, _FLOAT_BOUNDARY_SITES,
        lambda value: value.kind == "construct" and value.constructor_type is not None
        and value.constructor_type.display() == "float"
        and _span(value) in {site[2] for site in _FLOAT_BOUNDARY_SITES})
    proof = BitwiseNumberSemanticsProof(
        bitwise, arithmetic, constructors, number_symbols,
        number_expressions, assignments, narrowing, float_identity,
        float_boundaries)
    if (len(bitwise), len(arithmetic), len(constructors), len(number_symbols),
            len(number_expressions), len(assignments), len(narrowing),
            len(float_identity), len(float_boundaries)) != (10, 10, 4, 5, 44, 11, 2, 3, 2):
        raise _fail("post-transform census mismatch")
    if any(symbol.type.display() != "float" for symbol in number_symbols):
        raise _fail("post-transform Number symbol type mismatch")
    if any(node.type.display() != "float" for node in (
            *arithmetic, *number_expressions, *assignments)):
        raise _fail("post-transform Number expression type mismatch")
    if any(node.type.display() != "int" for node in (*bitwise, *constructors)):
        raise _fail("post-transform ToInt32 boundary type mismatch")
    for node, expected, site in zip(
            bitwise, _POST_BITWISE_OPERAND_TYPES, lock["sites"]):
        if (node.kind != site[4] or node.operator != site[5]
                or tuple(child.type.display() for child in node.children)
                != expected):
            raise _fail("post-transform bitwise operand pattern mismatch")
    for node, expected, site in zip(
            arithmetic, _POST_ARITHMETIC_OPERAND_TYPES, _ARITHMETIC_SITES):
        if (node.operator != site[3]
                or tuple(child.type.display() for child in node.children)
                != expected):
            raise _fail("post-transform arithmetic operand pattern mismatch")
    for node, expected in zip(
            constructors, _POST_INT_CONSTRUCTOR_OPERAND_TYPES):
        if (node.constructor_type is None
                or node.constructor_type.display() != "int"
                or tuple(child.type.display() for child in node.children)
                != expected):
            raise _fail("post-transform integer constructor pattern mismatch")
    for node, expected in zip(
            float_identity, _POST_FLOAT_IDENTITY_OPERAND_TYPES):
        if (node.type.display() != "float" or node.constructor_type is None
                or node.constructor_type.display() != "float"
                or tuple(child.type.display() for child in node.children)
                != expected):
            raise _fail("post-transform Number identity pattern mismatch")
    for node, expected in zip(
            float_boundaries, _POST_FLOAT_BOUNDARY_OPERAND_TYPES):
        if (node.type.display() != "float" or node.constructor_type is None
                or node.constructor_type.display() != "float"
                or tuple(child.type.display() for child in node.children)
                != expected):
            raise _fail("post-transform float32 boundary pattern mismatch")
    for symbol, expected in zip(number_symbols, _NUMBER_SYMBOL_SITES):
        if ((symbol.id, symbol.name, symbol.storage, _span(symbol),
             symbol.writable, symbol.direction) !=
                (expected[2], expected[3], expected[4], expected[5], True, "in")):
            raise _fail("post-transform Number symbol metadata mismatch")
    for node in number_expressions:
        if node.symbol is not symbol_by_id[node.symbol_id]:
            raise _fail("post-transform Number symbol identity mismatch")
    census = tuple((function.id, function.name, _span(node), node.kind,
                    node.operator, node.type.display(), _sha(node))
                   for function, node in expressions
                   if any(node is value for value in proof.consumed_objects
                          if isinstance(value, TypedExpression)))
    if not _POST_CENSUS_SHA256 or _sha(census) != _POST_CENSUS_SHA256:
        raise _fail("post-transform ordered census mismatch")
    return proof


def apply_bitwise_scalar_int_ops(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Apply the exact v2 JavaScript-Number semantic transform."""
    pre = _pre_profile(program, source_hash, profile)
    transformed = _transform_program(program, pre)
    _post_profile(transformed, source_hash, profile)
    return transformed


def authenticate_bitwise_scalar_int_ops(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> BitwiseNumberSemanticsProof:
    """Independently authenticate the complete transformed tree."""
    return _post_profile(program, source_hash, profile)


def authenticate_bitwise_scalar_int_ops_transition(
        before: TypedProgram, after: TypedProgram, source_hash: str | None,
        profile: str | None) -> BitwiseNumberSemanticsProof:
    """Authenticate both sides of the exact v2 pre/post transition."""
    pre = _pre_profile(before, source_hash, profile)
    expected = _transform_program(before, pre)
    if after is before or after != expected:
        raise _fail("typed-IR transition mismatch")
    return _post_profile(after, source_hash, profile)


def authenticate_bitwise_int_to_float_narrowing_skip(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Compatibility accessor for the two legacy bitOp identity sites."""
    return _post_profile(program, source_hash, profile).narrowing_skip_nodes
