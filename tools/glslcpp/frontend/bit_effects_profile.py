"""Prepared, source-locked frontend admission for ``classicNoisedeck/bitEffects``.

The existing scalar-uint XOR carrier authenticates the three jitter XORs in
the lattice hash.  This independent profile closes the remaining feature
frontier without widening the global frontend vocabulary: thirteen scalar
``int`` bitwise nodes (including the compile-time mask shift), two
``floatBitsToUint`` ingresses, and the two ``uvec3`` shift/XOR nodes are
authenticated by identity and complete-program cardinality.

The native runtime already exposes every required operation.  The scalar
shift-left is a positive global constant initializer and needs no runtime
ABI; all other operations map to existing ``glsl_types.hpp`` helpers.

The frozen JavaScript authority also preserves one upstream transpiler bug:
the three-source-argument ``maskValue(st, 1.0, -100.0)`` call in ``bitMask``
dispatches to the four-argument JavaScript function, leaving its last
parameter ``undefined``.  The exact call node is authenticated here so the
C++ emitter can reproduce that NaN-bearing misdispatch without changing any
other overload.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEY = "classicNoisedeck/bitEffects:bitEffects"
PROFILE = "bit-effects-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}

RUNTIME_ABI = {
    "scalar_int_bitwise": (
        "glsl::detail::js_bitwise_and",
        "glsl::detail::js_bitwise_or",
        "glsl::detail::js_bitwise_xor",
    ),
    "float_bits_to_uint": "noisemaker::float_bits_to_uint",
    "uvec3_shift_right": "glsl::shift_right",
    "uvec3_bitwise_xor": "glsl::bitwise_xor",
    "compile_time_shift_left": "C++ constant expression",
    "canonical_overload_misdispatch":
        "four-argument maskValue helper with quiet-NaN final argument",
    "canonical_xi_to_int32":
        "whole NaN-bearing xi sum through JavaScript ToInt32",
}

_RAW_BYTES = 12745
_RAW_SHA256 = "03194d61241ec307787d78c9b6d797b520c35c972c938aa701181b8340fa2e40"
_NORMALIZED_BYTES = 8169
_NORMALIZED_SHA256 = "70c88967c308368f81a8739296786c3e501005e536e987446bdc9c1dc93b7bb0"
_FUNCTIONS_SHA256 = "c2ffa4525ea4f39ba9e2395e2e755f580d450b645dee628408ddb089281377f5"
_WHOLE_SHA256 = "5156fbfe252da7e0be21a216e420ca385aac31ab6d4e658a842a5baf4030a234"
_INTERFACE_SHA256 = "22a5c8be48bbe78e87c503b1bbce3bdfeead3e452259dd46057ceccd1f2dc664"
_DEFINES = (
    ("COLOR_SCHEME", "int", "20"), ("FORMULA", "int", "0"),
    ("INTERP", "int", "0"), ("MASK_COLOR_SCHEME", "int", "1"),
    ("MASK_FORMULA", "int", "10"), ("MODE", "int", "1"),
)
_RESOURCES = (
    ("time", "seed", "resolution", "tileOffset", "fullResolution", "n",
     "scale", "rotation", "speed", "tiles", "complexity", "hueRange",
     "hueRotation", "baseHueRange"),
    (), ("fragColor",), False, False,
)
_LOOP = (0, 0, 0, 0, 0, True)
_GLOBAL_CONSTS = (
    (39, "BIT_COUNT", "129:1-129:25",
     "0317fc84e41d85b8f5a2bf11a384443b8a498eeee94c81cde1777cea8f8fdb1c"),
    (40, "mask", "130:1-130:39",
     "b8be4f44ccdaefa7d5493de15703f9cbd420cf98cd0c3c7dc43369dd76f75c93"),
)

# (operator, span, node hash, owner function id or None, owner name or None)
_SCALAR_INT_SITES = (
    ("<<", "130:19-130:33", "4086ce6fdd92b782efea092f78e50f34c86bf5429730348bdc6e0208707a4018", None, None),
    ("&", "141:13-141:35", "cb74535ba72ffa532e07dfd702a22c04e88f2e23459648f64e171219f3a74962", 88, "and"),
    ("&", "141:13-141:21", "1a8e846554896e27f8a382259344834468d373a180f06a4379d6ddbaf6fde9f8", 88, "and"),
    ("&", "141:26-141:34", "2450bd7f24a1451ef19d7931e8031830d5497aa5a0bf9aa013510406068c105f", 88, "and"),
    ("&", "133:13-133:26", "5057c3ceb7246dba03bb2452b588e0e512ce2b26365b19a461f75b49c4ce72ab", 103, "modi"),
    ("&", "145:13-145:35", "566a8ca7c43054e418cf5cb857793bda744d6757eed750d6f92a0f9b21509791", 104, "not2"),
    ("^", "145:13-145:27", "6686d67037408cd542a96cfa3b2ad3e34b50fca31b4480774c909ce21a4b4f65", 104, "not2"),
    ("|", "137:13-137:35", "1e2a563fe6602ed47ccbd1d3ad97381bfb4aeae0810e4e86836d37d940828fab", 107, "or"),
    ("&", "137:13-137:21", "795e2ec65e1bf710955293fd86286da038c4bc99c83bf308bf2e1dcd3f570d3f", 107, "or"),
    ("&", "137:26-137:34", "1c81c0d44845265bfd6aecfb973598388dc9f3aab426d3ab16009a773721758d", 107, "or"),
    ("^", "149:13-149:35", "7580640407292e1b2b11810fde68a44461c412c641f96289052c31ee1521b8cc", 116, "xor"),
    ("&", "149:13-149:21", "f84a01f407585c91493f5fa20216a75fefeb063e3211207a676e33907eb06ea7", 116, "xor"),
    ("&", "149:26-149:34", "d5c92c752df98bf27cc8a664fbb8d3ffc9a3952f76cab1fb00493a347c03921c", 116, "xor"),
)
_FLOAT_BITS_SITES = (
    ("95:21-95:39", "3a461e992dfa3ac5d49f072cb61b2715e3c3f491fdbfce07f6ec99204dc283a1"),
    ("96:21-96:46", "346eecbabb08b5d6f4167231825e239e5bb2c3dbfdc9bbc18f305ab4154200dc"),
)
_VECTOR_UINT_SITES = (
    (">>", "50:7-50:20", "9ffc47bcf117cb601fe604a80f84a15ac521038b54ee7c608334750c58c54482"),
    ("^", "104:19-104:57", "f4ed0fcb5070c26598f76efcae82569ad9381acc457875346a677b9cd439bd74"),
)
_SCALAR_UINT_XOR_SITES = (
    ("99:10-99:46", "0beb3cdd2d124ab9ffe121b511113e638d3067682c3009c818362a61e9ddead9"),
    ("100:10-100:46", "052b8139537615dd7d5407e5f79835b6817d8347b5b6fd3cf86bf5aac214fe8f"),
    ("101:10-101:47", "89c933e13eea0b6619023a7554bffb353eb1bd8c22890671cb91390823a66d8b"),
)
_CANONICAL_OVERLOAD_MISDISPATCH_SITE = (
    92, "bitMask", "340:32-340:58",
    "3a74a6ccca85eb676129416f2486e88c290295c11bfd96a2081ecff417deed1d",
    101, ("vec2", "float", "float"),
)
_CANONICAL_XI_TO_INT32_SITE = (
    111, "randomFromLatticeWithOffset", "90:14-90:54",
    "b62acf308ea960923485e4c3617c90895b60a411d7aa2475b693299033f442c5",
    "+", "int", ("binary", "construct"),
)


@dataclass(frozen=True, slots=True)
class BitEffectsFrontendProof:
    program_key: str
    scalar_int_bitwise_nodes: tuple[TypedExpression, ...]
    float_bits_to_uint_nodes: tuple[TypedExpression, ...]
    vector_uint_bitwise_nodes: tuple[TypedExpression, ...]
    scalar_uint_xor_nodes: tuple[TypedExpression, ...]
    canonical_overload_misdispatch_call: TypedExpression
    canonical_xi_to_int32_node: TypedExpression
    global_const_declarations: tuple[object, ...]
    resources: tuple
    defines: tuple
    declaration_count: int
    function_count: int

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        return (*self.scalar_int_bitwise_nodes,
                *self.float_bits_to_uint_nodes,
                *self.vector_uint_bitwise_nodes,
                *self.scalar_uint_xor_nodes)

    @property
    def scalar_int_bitwise_operators(self) -> tuple[str, ...]:
        return tuple(item.operator for item in self.scalar_int_bitwise_nodes)

    @property
    def float_bits_to_uint_spans(self) -> tuple[str, ...]:
        return tuple(_span(item) for item in self.float_bits_to_uint_nodes)

    @property
    def vector_uint_bitwise_spans(self) -> tuple[str, ...]:
        return tuple(_span(item) for item in self.vector_uint_bitwise_nodes)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


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


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _all_nodes(program: TypedProgram):
    for declaration in program.declarations:
        if declaration.initializer is not None:
            yield from _walk_expression(declaration.initializer)
    for function in program.functions:
        for statement in function.body:
            yield from _walk_statement(statement)


def _replace_expression(program: TypedProgram, target: TypedExpression,
                        replacement: TypedExpression) -> TypedProgram:
    def expression(value):
        if value is target:
            return replacement
        children = tuple(expression(child) for child in value.children)
        value = dataclasses.replace(value, children=children)
        return value

    def statement(value):
        return dataclasses.replace(
            value,
            expressions=tuple(expression(item) for item in value.expressions),
            children=tuple(statement(item) for item in value.children))

    return dataclasses.replace(
        program,
        declarations=tuple(dataclasses.replace(
            item, initializer=None if item.initializer is None else
            expression(item.initializer)) for item in program.declarations),
        functions=tuple(dataclasses.replace(
            item, body=tuple(statement(row) for row in item.body))
            for item in program.functions))


def _check_ledger(values: tuple[object, ...], expected: int) -> None:
    identities = [id(item) for item in values]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _fail("consumed-object identity/cardinality ledger mismatch")


def authenticate_bit_effects_frontend(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> BitEffectsFrontendProof:
    if profile != PROFILE or program.key != KEY:
        raise _fail("exact profile and program key required")
    raw = program.raw_source.encode()
    normalized = program.source.encode()
    if (source_hash != _RAW_SHA256 or len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or tuple((item.name, item.kind, item.canonical_value)
                     for item in program.preprocessor_defines) != _DEFINES
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256
            or program.counted_loop_proof is None
            or (program.counted_loop_proof.loop_count,
                program.counted_loop_proof.unproved_loop_count,
                program.counted_loop_proof.max_effective_depth,
                program.counted_loop_proof.max_lexical_product,
                program.counted_loop_proof.entrypoint_charge,
                program.counted_loop_proof.call_graph_acyclic) != _LOOP):
        raise _fail("source, interface, define, or loop lock mismatch")
    resources = (program.resources.uniforms, program.resources.samplers,
                 program.resources.outputs, program.resources.uses_texture,
                 program.resources.uses_derivatives)
    if resources != _RESOURCES or len(program.declarations) != 17 \
            or len(program.functions) != 30:
        raise _fail("interface cardinality or resource lock mismatch")
    global_consts = tuple(
        declaration for declaration in program.declarations
        if declaration.symbol.id in {row[0] for row in _GLOBAL_CONSTS})
    if tuple((item.symbol.id, item.symbol.name, _span(item), _sha(item))
             for item in global_consts) != _GLOBAL_CONSTS:
        raise _fail("global constant declaration identity/cardinality mismatch")

    located = []
    for declaration in program.declarations:
        if declaration.initializer is not None:
            located.extend((None, item) for item in
                           _walk_expression(declaration.initializer).
                           __iter__())
    for function in program.functions:
        for node in (item for statement in function.body
                     for item in _walk_statement(statement)):
            located.append((function, node))
    scalar = [(function, node) for function, node in located
              if node.kind == "binary" and node.type.display() == "int"
              and node.operator in {"&", "|", "^", "<<", ">>"}]
    scalar_rows = tuple((node.operator, _span(node), _sha(node),
                         None if function is None else function.id,
                         None if function is None else function.name)
                        for function, node in scalar)
    if scalar_rows != _SCALAR_INT_SITES:
        raise _fail("scalar int bitwise site identity/cardinality mismatch")

    float_bits = [node for _, node in located
                  if node.kind == "builtin" and node.callee == "floatBitsToUint"]
    if tuple((_span(node), _sha(node)) for node in float_bits) != _FLOAT_BITS_SITES:
        raise _fail("floatBitsToUint site identity/cardinality mismatch")

    vector = [node for _, node in located
              if node.kind == "binary" and node.type.display() == "uvec3"
              and node.operator in {"^", ">>"}]
    if tuple((node.operator, _span(node), _sha(node)) for node in vector) \
            != _VECTOR_UINT_SITES:
        raise _fail("uvec3 bitwise site identity/cardinality mismatch")

    scalar_uint = [node for _, node in located
                   if node.kind == "binary" and node.type.display() == "uint"
                   and node.operator == "^"]
    if tuple((_span(node), _sha(node)) for node in scalar_uint) \
            != _SCALAR_UINT_XOR_SITES:
        raise _fail("scalar uint XOR site identity/cardinality mismatch")

    misdispatch = [(function, node) for function, node in located
                   if function is not None and function.id == 92
                   and node.kind == "call" and node.callee == "maskValue"
                   and _span(node) == "340:32-340:58"]
    if len(misdispatch) != 1:
        raise _fail("canonical overload misdispatch cardinality mismatch")
    owner, misdispatch_call = misdispatch[0]
    misdispatch_row = (
        owner.id, owner.name, _span(misdispatch_call), _sha(misdispatch_call),
        misdispatch_call.signature_id,
        tuple(child.type.display() for child in misdispatch_call.children),
    )
    if misdispatch_row != _CANONICAL_OVERLOAD_MISDISPATCH_SITE:
        raise _fail("canonical overload misdispatch identity mismatch")

    xi_nodes = [(function, node) for function, node in located
                if function is not None and function.id == 111
                and node.kind == "binary" and _span(node) == "90:14-90:54"]
    if len(xi_nodes) != 1:
        raise _fail("canonical xi ToInt32 cardinality mismatch")
    xi_owner, xi_node = xi_nodes[0]
    xi_row = (
        xi_owner.id, xi_owner.name, _span(xi_node), _sha(xi_node),
        xi_node.operator, xi_node.type.display(),
        tuple(child.kind for child in xi_node.children),
    )
    if xi_row != _CANONICAL_XI_TO_INT32_SITE:
        raise _fail("canonical xi ToInt32 identity mismatch")
    if (len(xi_node.children) != 2
            or xi_node.children[0].operator != "+"
            or tuple(child.type.display()
                     for child in xi_node.children[0].children)
            != ("int", "int")
            or xi_node.children[1].type.display() != "int"
            or len(xi_node.children[1].children) != 1
            or xi_node.children[1].children[0].kind != "builtin"
            or xi_node.children[1].children[0].callee != "floor"
            or xi_node.children[1].children[0].type.display() != "float"):
        raise _fail("canonical xi ToInt32 shape mismatch")

    proof = BitEffectsFrontendProof(
        KEY, tuple(node for _, node in scalar), tuple(float_bits),
        tuple(vector), tuple(scalar_uint), misdispatch_call, xi_node,
        global_consts,
        resources, _DEFINES, len(program.declarations), len(program.functions))
    _check_ledger(proof.consumed_objects, 20)
    return proof


def apply_bit_effects_frontend(program: TypedProgram, source_hash: str | None,
                               profile: str | None) -> TypedProgram:
    authenticate_bit_effects_frontend(program, source_hash, profile)
    return program


__all__ = (
    "KEY", "PROFILE", "KEYS", "PROFILES", "PREPARED_KEYS",
    "PREPARED_PROFILES", "RUNTIME_ABI", "BitEffectsFrontendProof",
    "authenticate_bit_effects_frontend", "apply_bit_effects_frontend",
)
