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
        "raw_bytes": 9726,
        "raw_sha256": "4c664f7443b1085a37896730b5077ed6399ce345a7b5a25101a7a91e00b18363",
        "norm_bytes": 8417,
        "norm_sha256": "0a527a329e196188e6d52ad0e112242446826927e6cf31e1c0abb2bead19fd73",
        "functions_sha256": "67075b3c5276a803fbfe201aafaefdc48a2a276dce18baa539759e03537366b0",
        "whole_sha256": "603b09344b7356dc77c4f4cf426e43eb8cfea815a7f81dd8d291b37371956ac3",
        "interface_sha256": "dc2b8f83d606730c7cc366cc2320707f073f2f4e9e3eaa48bea747f83a6465b3",
        "modulo_count": 1,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9544,
        "raw_sha256": "78513907f1480250cef2e603e91a012aa4972c2e9e4bd66fc5aefa089a9a4775",
        "norm_bytes": 7560,
        "norm_sha256": "7b68cb1352d33295ea3d044de858c4a3c96a76b82c34450d700ba0ccd2758ba8",
        "functions_sha256": "08322fc7d7cfd4ab169f3280bf6bb73c64630f63c6285e3700d8e12daffc1715",
        "whole_sha256": "ade942f1bc599e45bc607ab2a92116368324c28e4d4818c7c73b9cad826d86ba",
        "interface_sha256": "d0d7e70f8758f7b7a924fefb72d36022ea212bc47446eb29b29c02e69e4c470a",
        "modulo_count": 1,
    },
    SPRITE_MEAN_TILES_KEY: {
        "raw_bytes": 1125,
        "raw_sha256": "e81c8f169c10a4168acd07489bafa55ecd349540c35bb1607df1fbba65261cc7",
        "norm_bytes": 955,
        "norm_sha256": "779515fb743ead143217259983866c970cdfcc192f9154c310e2bb0f7afe82db",
        "functions_sha256": "28c2d81cfea081a80f12c6b19d0a770deee75da6b2305d0c9e84ecc74f5575f1",
        "whole_sha256": "11e679e8da769fcdc277f78dc2777b9778ce4746bda7ffd40638bde656192e4c",
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
    if (len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]
            or program.body_status != "analyzed"
            or _sha(program.functions) != expected["functions_sha256"]
            or _whole(program) != expected["whole_sha256"]
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
