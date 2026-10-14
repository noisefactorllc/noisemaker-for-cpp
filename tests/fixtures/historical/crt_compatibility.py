"""Pinned public-CPU reduced-turn sine compatibility for CRT."""

from __future__ import annotations

import dataclasses
import hashlib

from .semantic_types import FLOAT
from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


TRANSFORM = "crt-metal-sine-v1"
CRT_KEY = "filter/crt:crt"
RAW_SOURCE_BYTES = 19560
RAW_SOURCE_SHA256 = "62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c"
NORMALIZED_SOURCE_SHA256 = "acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe"
INTERFACE_SHA256 = "9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490"
PRE_FUNCTIONS_SHA256 = "f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72"
PRE_WHOLE_PROGRAM_SHA256 = "f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc"
POST_FUNCTIONS_SHA256 = "1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3"
POST_WHOLE_PROGRAM_SHA256 = "7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2"

# function id, name, brief path, normalized span, pre expression, argument,
# post expression.  The path includes the brief's expression-root sentinel.
_SITES = (
    (98, "compute_lens_offsets", (11, "e0", 0, 0, 0, 0, 1),
     (257, 37, 257, 47),
     "eb792d3743d971b034cad3305939edd164f35d7391b0e956e0ded09f9ab2edca",
     "dfad6ec8408b05020688cf666dd8314a0d5e962d18d258ef05e4c7cbf1d17ab4",
     "fee8d1478892ff364e1f2222fbe484ec9c2821fde88981ac3411c7f460b0c991"),
    (105, "hash3", (2, "e0", 0, 0, 0, 0), (278, 18, 278, 32),
     "ec1ed0047c1fb4fd715375e00874a32e8f9e41ab9f74a3bac5ea23b3f1983150",
     "ba9137a74af006428cd1b19f03d169de8b0889ff1d4aa38dd775e9f85f389ad5",
     "7b805551b3f93876e1bd5ecf76a76efea15276160a8aa7bad7a570ba5da70457"),
    (111, "normalized_sine", (0, "e0", 0, 0, 0, 0), (61, 12, 61, 22),
     "06d6918e656846d23db8b766f298e3158cc09f466cead68bbdb792a95157ffeb",
     "f77149906598a9a158df24b332c186f1cb526dacbfe87bad03262af0a6def1ab",
     "37e92090742c393c51e58b0e243ed94b7c496d81713c72f50a81965ab65d0906"),
    (114, "random_scalar", (0, "e0", 0, 0, 0, 0), (32, 18, 32, 27),
     "42946f9e07f8dbde14695fd889212e33322f6b0b21073f150c104dbdae0207dc",
     "1625e24c6a465e2a1aff50c738539bf101926b078a4a14e617d12daa25efd07b",
     "ebf5806ccb5844082b4824ae98be478a0ccbbedcc446d11e1f782a05a5259fb7"),
    (118, "simplex_random", (2, "e0", 0, 0, 0, 0), (38, 15, 38, 25),
     "528dcb92903e79bdc9b9c3fa9da9d798ff560617e6bfc10d3c0eea8cd3a840fb",
     "385a6b97e9699eb5c2a7b2a2dd223de9794d92452b1ab6061f3bf8e53f8662a0",
     "d86ca37ad7e92a214a0aa669208b860c8c2691623ef830abe7275b6f83a99034"),
    (118, "simplex_random", (3, "e0", 0, 0, 0, 0), (39, 18, 39, 44),
     "ee17c06d50c446e45ea053d72191298f632721fe4daa3a01aad593095bf78367",
     "3c38672a718c912c5748397deb0abcf049c36dd979e9ca9a164f7437d5e2a6d9",
     "13a34f969f04eca11820a7aadee45a56f11e5ae369dfac59e02cb88e78673746"),
)

# function id, name, raw line, normalized span, expression, argument.
_COS_SITES = (
    (118, "simplex_random", 38, (37, 15, 37, 25),
     "d73adbb7e0f3b9c5cb4eb121ac454f08d16cd19bb651b9b3bfb6ddf352fae17a",
     "a07aef30bd37a38aa61216b37a41d239fb2e4c15d11c8e482e4d375443773048"),
    (91, "animated_simplex_value", 199, (198, 20, 198, 30),
     "aa8a39a243601c48cdaa3b328c2aeb5ee045908c55f154e1c7ba69058d29966e",
     "c2f34dcdc8a5568dc56401f25a5efa331f0e8249102791bbc31b6c53c496fa6c"),
    (98, "compute_lens_offsets", 258, (257, 25, 257, 35),
     "9c88ea057347d9c9f968a43c5b9d0a289a689cf6166b8f19a8c7ff1586e64bd9",
     "f5411ea9b54ceb2177a5dad5b00aa01be5ee2b51b3de5fd31b4c200981ea4169"),
    (94, "blend_cosine", 330, (329, 27, 329, 44),
     "f9a0165495911c862940e37195b8d97eba9709c3b6e42ce42b5822e4f152c95d",
     "12f0dd4d11b4959aa15e80b6e3448aad888cc6252076d53195c0def86d51d240"),
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def whole_program_fingerprint(program: TypedProgram) -> str:
    """Hash the frozen semantic tree while excluding optional proof carriers."""
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _fail(message: str) -> ValueError:
    return ValueError(f"{TRANSFORM}: {message}")


def _proofs_empty(program: TypedProgram) -> bool:
    return all(getattr(program, name, None) is None for name in (
        "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
        "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
    ))


def _source_ok(program: TypedProgram) -> bool:
    raw = program.raw_source.encode("utf-8")
    return (
        program.key == CRT_KEY
        and not program.preprocessor_defines
        and len(raw) == RAW_SOURCE_BYTES
        and hashlib.sha256(raw).hexdigest() == RAW_SOURCE_SHA256
        and hashlib.sha256(program.source.encode("utf-8")).hexdigest()
            == NORMALIZED_SOURCE_SHA256
        and interface_fingerprint(program) == INTERFACE_SHA256
    )


def _span(value: TypedExpression) -> tuple[int, int, int, int]:
    return (value.span.start_line, value.span.start_column,
            value.span.end_line, value.span.end_column)


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _builtin_sites(program: TypedProgram, name: str):
    result = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if value.kind == "builtin" and value.callee == name:
                    result.append((function, value))
    return result


def _site_shape(value: TypedExpression, callee: str, signature_id: int) -> bool:
    return (value.kind == "builtin" and value.callee == callee
            and value.signature_id == signature_id and value.type == FLOAT
            and value.category == "rvalue" and len(value.children) == 1)


def _authenticate_cosines(program: TypedProgram) -> None:
    actual = []
    for function, value in _builtin_sites(program, "cos"):
        if not _site_shape(value, "cos", -8):
            raise _fail("cosine shape mismatch")
        actual.append((function.id, function.name, _span(value), _sha(value),
                       _sha(value.children[0])))
    expected = [(item[0], item[1], item[3], item[4], item[5])
                for item in _COS_SITES]
    if sorted(actual) != sorted(expected):
        raise _fail("expected exact four untouched cosine sites")


def _pre_sites(program: TypedProgram) -> dict[tuple[int, tuple[int, int, int, int]], TypedExpression]:
    actual = {}
    for function, value in _builtin_sites(program, "sin"):
        key = (function.id, _span(value))
        if key in actual or not _site_shape(value, "sin", -40):
            raise _fail("pre-transform sine shape mismatch")
        actual[key] = value
    expected = {(item[0], item[3]): item for item in _SITES}
    if set(actual) != set(expected):
        raise _fail("expected exact six pre-transform sine sites")
    for key, value in actual.items():
        site = expected[key]
        if (_sha(value) != site[4] or _sha(value.children[0]) != site[5]):
            raise _fail("pre-transform sine or argument mismatch")
    direct = [value.children[0] for key, value in actual.items()
              if key != (118, (39, 18, 39, 44))]
    if len(direct) != 5 or any(value.kind != "id" for value in direct):
        raise _fail("direct sine argument purity mismatch")
    compound = actual[(118, (39, 18, 39, 44))].children[0]
    if (compound.kind != "binary" or compound.operator != "+"
            or tuple(child.kind for child in compound.children)
            != ("binary", "binary")
            or tuple(child.operator for child in compound.children)
            != ("*", "*")):
        raise _fail("compound sine argument purity mismatch")
    return actual


def _replacement(site: TypedExpression) -> TypedExpression:
    arg = site.children[0]
    span = site.span
    inv_tau = TypedExpression(
        "literal", FLOAT, span, "rvalue",
        literal="0.15915493667125702", literal_value=0.15915493667125702)
    scaled = TypedExpression(
        "binary", FLOAT, span, "rvalue",
        children=(arg, inv_tau), operator="*")
    turns = TypedExpression(
        "construct", FLOAT, span, "rvalue",
        children=(scaled,), constructor_type=FLOAT)
    wrapped = TypedExpression(
        "builtin", FLOAT, span, "rvalue",
        signature_id=-17, children=(turns,), callee="floor")
    phase = TypedExpression(
        "binary", FLOAT, span, "rvalue",
        children=(turns, wrapped), operator="-")
    tau = TypedExpression(
        "literal", FLOAT, span, "rvalue",
        literal="6.2831854820251465", literal_value=6.2831854820251465)
    reduced = TypedExpression(
        "binary", FLOAT, span, "rvalue",
        children=(phase, tau), operator="*")
    result = dataclasses.replace(site, children=(reduced,))
    if (scaled.children[0] is not arg or phase.children[0] is not wrapped.children[0]):
        raise _fail("replacement object identity mismatch")
    return result


def _authenticate_post_sites(program: TypedProgram) -> None:
    actual = {}
    for function, value in _builtin_sites(program, "sin"):
        key = (function.id, _span(value))
        if key in actual or not _site_shape(value, "sin", -40):
            raise _fail("post-transform sine shape mismatch")
        actual[key] = value
    expected = {(item[0], item[3]): item for item in _SITES}
    if set(actual) != set(expected):
        raise _fail("expected exact six post-transform sine sites")
    for key, value in actual.items():
        if _sha(value) != expected[key][6]:
            raise _fail("post-transform sine mismatch")
        reduced = value.children[0]
        if (reduced.kind != "binary" or reduced.type != FLOAT
                or reduced.category != "rvalue" or reduced.operator != "*"
                or len(reduced.children) != 2):
            raise _fail("reduced sine product mismatch")
        phase, tau = reduced.children
        if (tau.kind != "literal" or tau.type != FLOAT
                or tau.category != "rvalue"
                or tau.literal != "6.2831854820251465"
                or tau.literal_value != 6.2831854820251465
                or tau.span != value.span):
            raise _fail("reduced sine TAU mismatch")
        if (phase.kind != "binary" or phase.type != FLOAT
                or phase.category != "rvalue" or phase.operator != "-"
                or len(phase.children) != 2):
            raise _fail("reduced sine phase mismatch")
        turns, wrapped = phase.children
        if (wrapped.kind != "builtin" or wrapped.type != FLOAT
                or wrapped.category != "rvalue" or wrapped.callee != "floor"
                or wrapped.signature_id != -17 or len(wrapped.children) != 1
                or wrapped.children[0] is not turns):
            raise _fail("reduced sine shared turns/floor mismatch")
        if (turns.kind != "construct" or turns.type != FLOAT
                or turns.category != "rvalue" or turns.constructor_type != FLOAT
                or len(turns.children) != 1 or turns.span != value.span):
            raise _fail("reduced sine float constructor mismatch")
        scaled = turns.children[0]
        if (scaled.kind != "binary" or scaled.type != FLOAT
                or scaled.category != "rvalue" or scaled.operator != "*"
                or len(scaled.children) != 2):
            raise _fail("reduced sine INV_TAU product mismatch")
        inv_tau = scaled.children[1]
        if (inv_tau.kind != "literal" or inv_tau.type != FLOAT
                or inv_tau.category != "rvalue"
                or inv_tau.literal != "0.15915493667125702"
                or inv_tau.literal_value != 0.15915493667125702
                or inv_tau.span != value.span):
            raise _fail("reduced sine INV_TAU mismatch")


def apply_crt_metal_sine(program: TypedProgram) -> TypedProgram:
    """Rewrite exactly six authenticated scalar sine sites."""
    if not _proofs_empty(program):
        raise _fail("pre-transform proof carrier is not empty")
    if (not _source_ok(program)
            or _sha(program.functions) != PRE_FUNCTIONS_SHA256
            or whole_program_fingerprint(program) != PRE_WHOLE_PROGRAM_SHA256):
        raise _fail("source, key, interface, or pre-transform tree mismatch")
    sites = _pre_sites(program)
    _authenticate_cosines(program)
    replacements = {key: _replacement(value) for key, value in sites.items()}
    matches = 0

    def expression(function: TypedFunction,
                   value: TypedExpression) -> TypedExpression:
        nonlocal matches
        key = (function.id, _span(value))
        if key in replacements and _sha(value) == _sha(sites[key]):
            matches += 1
            return replacements[key]
        children = tuple(expression(function, child) for child in value.children)
        if all(left is right for left, right in zip(children, value.children)):
            return value
        return dataclasses.replace(value, children=children)

    def statement(function: TypedFunction,
                  value: TypedStatement) -> TypedStatement:
        expressions = tuple(expression(function, item) for item in value.expressions)
        children = tuple(statement(function, item) for item in value.children)
        if (all(left is right for left, right in zip(expressions, value.expressions))
                and all(left is right for left, right in zip(children, value.children))):
            return value
        return dataclasses.replace(value, expressions=expressions, children=children)

    functions = []
    for function in program.functions:
        body = tuple(statement(function, item) for item in function.body)
        if all(left is right for left, right in zip(body, function.body)):
            functions.append(function)
        else:
            functions.append(dataclasses.replace(function, body=body))
    if matches != 6:
        raise _fail(f"expected six exact replacements, got {matches}")
    transformed = dataclasses.replace(program, functions=tuple(functions))
    authenticate_crt_metal_sine(transformed, RAW_SOURCE_SHA256)
    return transformed


def authenticate_crt_metal_sine(
        program: TypedProgram, source_hash: str | None) -> None:
    """Authenticate an already transformed CRT tree without mutating it."""
    if (source_hash != RAW_SOURCE_SHA256 or not _source_ok(program)
            or not _proofs_empty(program)
            or _sha(program.functions) != POST_FUNCTIONS_SHA256
            or whole_program_fingerprint(program) != POST_WHOLE_PROGRAM_SHA256):
        raise _fail("source, interface, proof, or post-transform tree mismatch")
    _authenticate_post_sites(program)
    _authenticate_cosines(program)
