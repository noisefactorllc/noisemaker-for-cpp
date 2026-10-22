"""Proof profile for authenticated vector-scalar integer modulo (%) carriers.

Authenticates exact vector % scalar integer modulo expressions across programs:
- points/flock:agent (ivec2 % int in spatial grid wrapping)
- points/life:agent (ivec2 % int in spatial grid wrapping)
- render/pointsBillboardRender:spriteMeanTiles (ivec2 % int in tile calculation)

All candidate expressions operate component-wise on an integer vector operand and
a matching integral scalar operand, returning an integer vector of the same dimension.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "vec-scalar-modulo-v1"

FLOCK_AGENT_KEY = "points/flock:agent"
LIFE_AGENT_KEY = "points/life:agent"
SPRITE_MEAN_TILES_KEY = "render/pointsBillboardRender:spriteMeanTiles"

VEC_SCALAR_MODULO_KEYS = frozenset({
    FLOCK_AGENT_KEY,
    LIFE_AGENT_KEY,
    SPRITE_MEAN_TILES_KEY,
})

_PROFILES = {
    FLOCK_AGENT_KEY: {
        "raw_bytes": 11303,
        "raw_sha256": "3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        "norm_bytes": 9625,
        "norm_sha256": "64fba0ca7fa41e701271dd0a713a3427a265f7b599bac510d6eceadea14af792",
        "functions_sha256": "03293a8f9c0ef0a0b627253fe6762f0bd3a62d56c48ed9040bb8913608abee2d",
        "whole_sha256": "59099a0064e8e9af2ebf7477febcb2e1e22fa8272d77222018ec52abfcbbff70",
        "interface_sha256": "25653fe91b5d3024f18a0e791a41dadf848caa7d5644b8b859c581923f4455cb",
        "modulo_count": 1,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9685,
        "raw_sha256": "60421e21ac31334ab7fa23c20d8dedd97a8285580ea85a110b5a347a44adca1e",
        "norm_bytes": 7701,
        "norm_sha256": "105f5af7c0f541bb3721eefc8c1cce7767b2b8d4dac054f18ec9caf00dc79726",
        "functions_sha256": "dd18a9aacf3cef52499030a4f31546d7adccf8e9ff3be3aeac43929ff1884eb7",
        "whole_sha256": "843592ce9021b2022c3db62ade6c91e1f54b506c45f4e48e4a0ece53a7b3a168",
        "interface_sha256": "1633b00a44698f13f38a1e4956553c1634c65821bc7feeb8bb4d1271d293a25e",
        "modulo_count": 1,
    },
    SPRITE_MEAN_TILES_KEY: {
        "raw_bytes": 1125,
        "raw_sha256": "e81c8f169c10a4168acd07489bafa55ecd349540c35bb1607df1fbba65261cc7",
        "norm_bytes": 955,
        "norm_sha256": "779515fb743ead143217259983866c970cdfcc192f9154c310e2bb0f7afe82db",
        "functions_sha256": frozenset({
            "28c2d81cfea081a80f12c6b19d0a770deee75da6b2305d0c9e84ecc74f5575f1",
            "618f685938b1af45f5ef2f27e9054a620e654a12828f5f8c1a8d495fbc8c9d78",
        }),
        "whole_sha256": frozenset({
            "11e679e8da769fcdc277f78dc2777b9778ce4746bda7ffd40638bde656192e4c",
            "ff3223c7275d9eee0e1f63f251791ff2dd06980d83342d9a73d0adddaa0fc72a",
        }),
        "interface_sha256": "1fb06df481aa165235398e2e366fa2253f1a3e2d2f03ee0a9f2ad08f4c5ca122",
        "modulo_count": 1,
    },
}


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


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
    for child in getattr(value, "children", ()):
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in getattr(value, "expressions", ()):
        yield from _walk_expression(expression)
    for child in getattr(value, "children", ()):
        yield from _walk_statement(child)


def authenticate_vec_scalar_modulo(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate vector-scalar integer modulo carriers and return exact AST % nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in VEC_SCALAR_MODULO_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {VEC_SCALAR_MODULO_KEYS}")
    expected = _PROFILES[program.key]
    if source_hash != expected["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    expected_fns = expected["functions_sha256"]
    if isinstance(expected_fns, str):
        expected_fns = {expected_fns}
    expected_whole = expected["whole_sha256"]
    if isinstance(expected_whole, str):
        expected_whole = {expected_whole}
    if (len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]
            or program.body_status != "analyzed"
            or _sha(program.functions) not in expected_fns
            or _whole(program) not in expected_whole
            or _interface(program) != expected["interface_sha256"]):
        raise ValueError(f"{PROFILE}: {program.key} source, function, whole-program, or interface mismatch")

    modulos: list[TypedExpression] = []
    for fn in program.functions:
        for stmt in fn.body:
            for expr in _walk_statement(stmt):
                if getattr(expr, "kind", None) == "binary" and getattr(expr, "operator", None) == "%":
                    c0_type = expr.children[0].type.display()
                    c1_type = expr.children[1].type.display()
                    if (
                        (c0_type in {"ivec2", "ivec3", "ivec4"} and c1_type == "int" and expr.type.display() == c0_type)
                        or (c0_type in {"uvec2", "uvec3", "uvec4"} and c1_type == "uint" and expr.type.display() == c0_type)
                    ):
                        modulos.append(expr)

    if len(modulos) != expected["modulo_count"]:
        raise ValueError(
            f"{PROFILE}: {program.key} expected {expected['modulo_count']} vector-scalar modulo sites, found {len(modulos)}")

    return tuple(modulos)


def apply_vec_scalar_modulo(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_vec_scalar_modulo(program, source_hash, profile)
    return program
