"""Proof profile for authenticated hash scalar uint XOR carriers.

Authenticates exact scalar uint XOR (^) expressions across hash functions:
- synth3d/noise3d:precompute (hash4)
- filter3d/flow3d:agent (hash_uint)
- points/buddhabrot:agent (hash_uint and agentSeed)
- points/flow:agent (hash_uint)
- points/hydraulic:agent (hash2)
- points/life:matrix (hash_uint)
- points/physical:agent (hash_uint)
- render/pointsEmit:init (hash_uint)
- points/flock:agent (hash_uint)
- points/life:agent (hash_uint)
- points/physarum:agent (hash_uint)

All candidate XOR expressions operate strictly on uint operands and evaluate to uint.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "hash-scalar-uint-xor-v1"

NOISE3D_PRECOMPUTE_KEY = "synth3d/noise3d:precompute"
FLOW3D_AGENT_KEY = "filter3d/flow3d:agent"
BUDDHABROT_AGENT_KEY = "points/buddhabrot:agent"
FLOW_AGENT_KEY = "points/flow:agent"
HYDRAULIC_AGENT_KEY = "points/hydraulic:agent"
LIFE_MATRIX_KEY = "points/life:matrix"
PHYSICAL_AGENT_KEY = "points/physical:agent"
POINTS_EMIT_INIT_KEY = "render/pointsEmit:init"
FLOCK_AGENT_KEY = "points/flock:agent"
LIFE_AGENT_KEY = "points/life:agent"
PHYSARUM_AGENT_KEY = "points/physarum:agent"

HASH_SCALAR_UINT_XOR_KEYS = frozenset({
    NOISE3D_PRECOMPUTE_KEY,
    FLOW3D_AGENT_KEY,
    BUDDHABROT_AGENT_KEY,
    FLOW_AGENT_KEY,
    HYDRAULIC_AGENT_KEY,
    LIFE_MATRIX_KEY,
    PHYSICAL_AGENT_KEY,
    POINTS_EMIT_INIT_KEY,
    FLOCK_AGENT_KEY,
    LIFE_AGENT_KEY,
    PHYSARUM_AGENT_KEY,
})

_PROFILES = {
    NOISE3D_PRECOMPUTE_KEY: {
        "raw_bytes": 7667,
        "raw_sha256": "60ce97d188bf78bc84176c063943f29c25371e4325f13cedbb4eec889c905727",
        "norm_bytes": 5425,
        "norm_sha256": "e4656d5bd9a25340cc793a645d97aed84aac929ad2516421d170f4606c854877",
        "functions_sha256": "613bac6ff3765dfe7887069527715c49b9342d475e0ad485e5b4ee13645223b9",
        "whole_sha256": "ef0ba2aed2e4696f2eaea3fc66b5bdc7eafc243aa8237d7d1c263c079ffa19d4",
        "interface_sha256": "c3c85858579f6b047df4e589bd041a6f266453e6a36ae4ecc0a56c0f88a6a4df",
        "xor_count": 3,
    },
    FLOW3D_AGENT_KEY: {
        "raw_bytes": 9859,
        "raw_sha256": "f4e3622f4def27221de0bd0b93ed1152f56f835957361e0fcffea8b84d3ce356",
        "norm_bytes": 6473,
        "norm_sha256": "1a2f15aaf6c7ed17adf0443e4f16db6ce6400f26977976ea00619bbaf5f4e518",
        "functions_sha256": "78124e7ff158ce6dc534ba69f3cfc9db226feb6ad73ef219c678f9b20cbe0a03",
        "whole_sha256": "9d0390f626c510cacb283121165dd1e10f16a9ee8f66f2d677b50cc0b11fe896",
        "interface_sha256": "23b1456fd0e9a911d2b29760a60e3d0db516a262d4192d572798355e00379863",
        "xor_count": 2,
    },
    BUDDHABROT_AGENT_KEY: {
        "raw_bytes": 4826,
        "raw_sha256": "0e2e9336878287c4c856c6f6a4e7d2a19219d29025f33d0ead8c5f17fc19cc5c",
        "norm_bytes": 4191,
        "norm_sha256": "b88fc526f2c2b3fc2fa1b12fe72760c71282a9ed4488a86e32591fb6cb170e0e",
        "functions_sha256": "47adf379f833f40836b4751f14ad2ca4cc74d64ef16c2db533b971e1f04693b1",
        "whole_sha256": "d9469f0ee2bebfffea6a5a822a9030db7bb39771e3d2127a735a47b926366ca1",
        "interface_sha256": "63439600efc8fdf0040c30da38a2628a36070afb21f9e01e9f44d92e33064935",
        "xor_count": 4,
    },
    FLOW_AGENT_KEY: {
        "raw_bytes": 5848,
        "raw_sha256": "0584139db3b2e14af99788458a48094a0d650a03ae540a0468309bf2f097bb6b",
        "norm_bytes": 4806,
        "norm_sha256": "f65a6c7d49e84efc852b351c06b0807f1226aba3c79b6d3e1e3f6ca4f08eb1d4",
        "functions_sha256": "aff889250f44b8b6aa16ecf03c92cf20cfdc45ebd0cc6cf437672b2fca7d55fe",
        "whole_sha256": "4630e9ddb459f7224ec1636c7cae3cecdc84159bd5e436a40fb2fbdb7c0a3af9",
        "interface_sha256": "1748203f7868b9ee23ea5891b547e21dcc083b83bf45913e332bbae14affac3b",
        "xor_count": 2,
    },
    HYDRAULIC_AGENT_KEY: {
        "raw_bytes": 6329,
        "raw_sha256": "988fe48308354bc7cd8eaa1cb768bccf9ac37b3ce8ebb4256f567eb8419f1001",
        "norm_bytes": 4931,
        "norm_sha256": "f8f8519ff841b4198584d6e39425aacf0f301b7f67f526a82240d6c028d613db",
        "functions_sha256": "b3ce3f2bd7f45bc79685225c9029d319b1ba0090ddbca93ea4d4815f6d448469",
        "whole_sha256": "776f26956d04921a900a70d045a3d9e5162bd9bb9721d0b062d57e312ff04f8c",
        "interface_sha256": "a847dd35f3c877057dff346926415ba40c968b8153c14ed2f0240bca038a0592",
        "xor_count": 4,
    },
    LIFE_MATRIX_KEY: {
        "raw_bytes": 1889,
        "raw_sha256": "405376b51b550714253aff0f818a4fd56d50618bc792558826195b901c5fa073",
        "norm_bytes": 1211,
        "norm_sha256": "eb4d1ee02108dbed36c35559d54f74bcb200c1942ed2db69664140430c1528cb",
        "functions_sha256": "d98cfde1fb2bc5dc304c76847289b28318ae8bed66eafa1f383a31f154c0d7b0",
        "whole_sha256": "13981d01c16fd6eebd62a653657507a7361ca765660faa500bf8aefa93f6d425",
        "interface_sha256": "0b8ad1945ff8b3cb8cdd6a91cceac2c907f5a9f880aeda687684712fd9be70ec",
        "xor_count": 2,
    },
    PHYSICAL_AGENT_KEY: {
        "raw_bytes": 4136,
        "raw_sha256": "a144cacbadeca15a78a83dac987bfd25164bd7904a2e9f0ea22e8b1bf22e3614",
        "norm_bytes": 2927,
        "norm_sha256": "c3a280a29bf0271343121e06bf8c9345a893015a3978a633e9bce7b1ba5a97ed",
        "functions_sha256": "08e2987ae3378a1287bf997f97a9655576d678913f60eb940a59c437dea876f5",
        "whole_sha256": "f32c9a84d8c27cf859573a7829a8396b2fadfd9f88a3ed57d3001fe725186935",
        "interface_sha256": "d0add6d9633da432948fe2a6e3c7ec3285dabab5c5e79935510f810493971567",
        "xor_count": 2,
    },
    POINTS_EMIT_INIT_KEY: {
        "raw_bytes": 5236,
        "raw_sha256": "cd266c795b298b372f077e6aeb6f862c75a0970999fba2f87c4462b322592402",
        "norm_bytes": 3527,
        "norm_sha256": "0d6c62fe326d9ec1e8f7ebbfe90ae7338c8bbe7f75b07d13a3007a81002f80dc",
        "functions_sha256": "35e45f77abdb760c64d089a39992f89f269feea0f0987899636d44bc2b0a9ded",
        "whole_sha256": "42b04762d700eb0b0c8c30627e317f0d2795886a7a80a32113f464608aa5e041",
        "interface_sha256": "4c788a40ea67029aafa7a4f2ecddfe820308b1da11f23f8278bf506e97806da4",
        "xor_count": 2,
    },
    FLOCK_AGENT_KEY: {
        "raw_bytes": 9726,
        "raw_sha256": "4c664f7443b1085a37896730b5077ed6399ce345a7b5a25101a7a91e00b18363",
        "norm_bytes": 8417,
        "norm_sha256": "0a527a329e196188e6d52ad0e112242446826927e6cf31e1c0abb2bead19fd73",
        "functions_sha256": "67075b3c5276a803fbfe201aafaefdc48a2a276dce18baa539759e03537366b0",
        "whole_sha256": "603b09344b7356dc77c4f4cf426e43eb8cfea815a7f81dd8d291b37371956ac3",
        "interface_sha256": "dc2b8f83d606730c7cc366cc2320707f073f2f4e9e3eaa48bea747f83a6465b3",
        "xor_count": 2,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9544,
        "raw_sha256": "78513907f1480250cef2e603e91a012aa4972c2e9e4bd66fc5aefa089a9a4775",
        "norm_bytes": 7560,
        "norm_sha256": "7b68cb1352d33295ea3d044de858c4a3c96a76b82c34450d700ba0ccd2758ba8",
        "functions_sha256": "08322fc7d7cfd4ab169f3280bf6bb73c64630f63c6285e3700d8e12daffc1715",
        "whole_sha256": "ade942f1bc599e45bc607ab2a92116368324c28e4d4818c7c73b9cad826d86ba",
        "interface_sha256": "d0d7e70f8758f7b7a924fefb72d36022ea212bc47446eb29b29c02e69e4c470a",
        "xor_count": 2,
    },
    PHYSARUM_AGENT_KEY: {
        "raw_bytes": 4817,
        "raw_sha256": "d39a5afa26f97da83f61099e712b40d7a901978ce5b2a0070c2d87eef0c03c44",
        "norm_bytes": 3677,
        "norm_sha256": "e4ee3bac5c2066c3c554459b71e0593c6df980b93c60929e85c7962674b601aa",
        "functions_sha256": "f50cfcd2a5bbd96fe3afb495aeff4ce0e31870035da51d5a4bd62f0b77f30e34",
        "whole_sha256": "32d8e51315238189755e5e60df01f40c96f4057a44b95e9c60b93d70db2a1d2c",
        "interface_sha256": "9c75d74e7798cf5017f69ff010e2ab213425c51c5282514e6e1275cfa1eb94ba",
        "xor_count": 2,
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


def authenticate_hash_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate hash scalar uint XOR carriers and return exact AST XOR nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in HASH_SCALAR_UINT_XOR_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {HASH_SCALAR_UINT_XOR_KEYS}")
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

    xors: list[TypedExpression] = []
    for fn in program.functions:
        for stmt in fn.body:
            for expr in _walk_statement(stmt):
                if getattr(expr, "kind", None) == "binary" and getattr(expr, "operator", None) == "^":
                    if (expr.type.display() == "uint"
                            and len(expr.children) == 2
                            and expr.children[0].type.display() == "uint"
                            and expr.children[1].type.display() == "uint"):
                        xors.append(expr)

    if len(xors) != expected["xor_count"]:
        raise ValueError(
            f"{PROFILE}: {program.key} expected {expected['xor_count']} scalar uint XOR sites, found {len(xors)}")

    return tuple(xors)


def apply_hash_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_hash_scalar_uint_xor(program, source_hash, profile)
    return program

