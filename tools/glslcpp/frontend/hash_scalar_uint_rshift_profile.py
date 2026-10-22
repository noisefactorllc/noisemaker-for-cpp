"""Proof profile for authenticated hash scalar uint right shift (>>) carriers.

Authenticates exact scalar uint right shift (>>) expressions across hash functions:
- filter3d/flow3d:agent (hash_uint)
- points/buddhabrot:agent (hash_uint)
- points/flow:agent (hash_uint)
- points/physarum:agent (hash_uint)
- points/dla:agent (hash_uint)
- points/attractor:agent (hash_uint)
- points/hydraulic:agent (hash2)
- points/life:matrix (hash_uint)
- points/physical:agent (hash_uint)
- render/pointsEmit:init (hash_uint)
- points/dla:agent (hash_uint)

All candidate right shift expressions operate strictly on uint operands and evaluate to uint.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "hash-scalar-uint-rshift-v1"

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
DLA_AGENT_KEY = "points/dla:agent"
ATTRACTOR_AGENT_KEY = "points/attractor:agent"
HASH_SCALAR_UINT_RSHIFT_KEYS = frozenset({
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
    DLA_AGENT_KEY,
    ATTRACTOR_AGENT_KEY,
})

_PROFILES = {
    FLOW3D_AGENT_KEY: {
        "raw_bytes": 9859,
        "raw_sha256": "f4e3622f4def27221de0bd0b93ed1152f56f835957361e0fcffea8b84d3ce356",
        "norm_bytes": 6473,
        "norm_sha256": "1a2f15aaf6c7ed17adf0443e4f16db6ce6400f26977976ea00619bbaf5f4e518",
        "functions_sha256": "78124e7ff158ce6dc534ba69f3cfc9db226feb6ad73ef219c678f9b20cbe0a03",
        "whole_sha256": "9d0390f626c510cacb283121165dd1e10f16a9ee8f66f2d677b50cc0b11fe896",
        "interface_sha256": "23b1456fd0e9a911d2b29760a60e3d0db516a262d4192d572798355e00379863",
        "rshift_count": 3,
    },
    BUDDHABROT_AGENT_KEY: {
        "raw_bytes": 6121,
        "raw_sha256": "efecb24d045790bee064e160a1b09a7f411589e76fee87591261bba0cc44870f",
        "norm_bytes": 5302,
        "norm_sha256": "f702257b10bb7daedbaa4877c9c42ba465f6526ff5b289f3de8b75ba5a315ec2",
        "functions_sha256": "58e61d7ba35af9a09b9ff6e5a5dd05f4e502fd63685e222ecaaed591d50ba576",
        "whole_sha256": "f061acf37cd43905cbff8c1b61b4e5ca7aea507207d5545d82cc7e47b2d943ca",
        "interface_sha256": "28cd880fc851acae557c6e94b3d1daaf9ba71525be7d8335db2b282759e249d8",
        "rshift_count": 3,
    },
    FLOW_AGENT_KEY: {
        "raw_bytes": 7515,
        "raw_sha256": "f8149c037daa3172ccafdb0ffcadbebad3a5fd7d3b9fa1112861518cddfede06",
        "norm_bytes": 6144,
        "norm_sha256": "d4dc5e40a1e5454c2285b923dd582b34bf1b25413032f51edcfbe433b43ae9d2",
        "functions_sha256": "3415b919eb0ed7725d7f3cd6f66c6d0218d6d995a460da8a212c371a75d96cd7",
        "whole_sha256": "0961e0f4e18f00c6d43153a299c33eacf486d88e4a6f8e60e029dceede0f4a70",
        "interface_sha256": "101c5b05335de2dfa3513c14b9c93c22840f39e48c6b4db83bae72b88153a2b1",
        "rshift_count": 3,
    },
    HYDRAULIC_AGENT_KEY: {
        "raw_bytes": 7967,
        "raw_sha256": "02bff511e46a3e32cfd7d2aa0c8d49d24a9590441c8900379241ba210a06a0fc",
        "norm_bytes": 6240,
        "norm_sha256": "b03ff45edcbdd617ac3d2c3b60731d42d10de712a0c1300e0753e650671630c2",
        "functions_sha256": "fb16393b74c70d7c255e3e5322fecb4b93bf3484776464db4c98eb95ef4d0623",
        "whole_sha256": "d957cc2617462e61c53df93c7a68f8fed85039cf5f458bd6fbc3100e58b8f5a3",
        "interface_sha256": "f277f8af2f050e111e372896f97bedcdb09bfa0483345fb6b77934bc0708f761",
        "rshift_count": 6,
    },
    LIFE_MATRIX_KEY: {
        "raw_bytes": 1889,
        "raw_sha256": "405376b51b550714253aff0f818a4fd56d50618bc792558826195b901c5fa073",
        "norm_bytes": 1211,
        "norm_sha256": "eb4d1ee02108dbed36c35559d54f74bcb200c1942ed2db69664140430c1528cb",
        "functions_sha256": "d98cfde1fb2bc5dc304c76847289b28318ae8bed66eafa1f383a31f154c0d7b0",
        "whole_sha256": "13981d01c16fd6eebd62a653657507a7361ca765660faa500bf8aefa93f6d425",
        "interface_sha256": "0b8ad1945ff8b3cb8cdd6a91cceac2c907f5a9f880aeda687684712fd9be70ec",
        "rshift_count": 3,
    },
    PHYSICAL_AGENT_KEY: {
        "raw_bytes": 5690,
        "raw_sha256": "06f3afef8efeaba67f1babf129ee107b06e860ec8458e270ce404fc770b46615",
        "norm_bytes": 4152,
        "norm_sha256": "8ec3c18241a32241e625c44e71377de7e212901cafebb01f70c193aec2ea5edb",
        "functions_sha256": "e9799e4cb945b8fd49099121faf71307f0d3ee0f46a36d60241fc8acd959e9e0",
        "whole_sha256": "caad738335a8200c1ef5a9ce7034977e0704ea7dcb88c1da869868f57fea3d98",
        "interface_sha256": "ca1c4bff0124fb5664d0c5d2cece4849dda6458633ef06517a63d19e4c4dfcd6",
        "rshift_count": 3,
    },
    POINTS_EMIT_INIT_KEY: {
        "raw_bytes": 5236,
        "raw_sha256": "cd266c795b298b372f077e6aeb6f862c75a0970999fba2f87c4462b322592402",
        "norm_bytes": 3527,
        "norm_sha256": "0d6c62fe326d9ec1e8f7ebbfe90ae7338c8bbe7f75b07d13a3007a81002f80dc",
        "functions_sha256": "35e45f77abdb760c64d089a39992f89f269feea0f0987899636d44bc2b0a9ded",
        "whole_sha256": "42b04762d700eb0b0c8c30627e317f0d2795886a7a80a32113f464608aa5e041",
        "interface_sha256": "4c788a40ea67029aafa7a4f2ecddfe820308b1da11f23f8278bf506e97806da4",
        "rshift_count": 3,
    },
    FLOCK_AGENT_KEY: {
        "raw_bytes": 11303,
        "raw_sha256": "3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        "norm_bytes": 9625,
        "norm_sha256": "64fba0ca7fa41e701271dd0a713a3427a265f7b599bac510d6eceadea14af792",
        "functions_sha256": "03293a8f9c0ef0a0b627253fe6762f0bd3a62d56c48ed9040bb8913608abee2d",
        "whole_sha256": "59099a0064e8e9af2ebf7477febcb2e1e22fa8272d77222018ec52abfcbbff70",
        "interface_sha256": "25653fe91b5d3024f18a0e791a41dadf848caa7d5644b8b859c581923f4455cb",
        "rshift_count": 3,
    },
    LIFE_AGENT_KEY: {
        "raw_bytes": 9685,
        "raw_sha256": "60421e21ac31334ab7fa23c20d8dedd97a8285580ea85a110b5a347a44adca1e",
        "norm_bytes": 7701,
        "norm_sha256": "105f5af7c0f541bb3721eefc8c1cce7767b2b8d4dac054f18ec9caf00dc79726",
        "functions_sha256": "dd18a9aacf3cef52499030a4f31546d7adccf8e9ff3be3aeac43929ff1884eb7",
        "whole_sha256": "843592ce9021b2022c3db62ade6c91e1f54b506c45f4e48e4a0ece53a7b3a168",
        "interface_sha256": "1633b00a44698f13f38a1e4956553c1634c65821bc7feeb8bb4d1271d293a25e",
        "rshift_count": 3,
    },
    PHYSARUM_AGENT_KEY: {
        "raw_bytes": 6510,
        "raw_sha256": "a9b21cee808cf70e7d29d05f27bdf9bd598ef1f5ac8dae492e6541cf21456e2f",
        "norm_bytes": 5059,
        "norm_sha256": "1d643cf97a028845eb22904b69a761b1002b715df5d92203a68e54137df89290",
        "functions_sha256": "435c2a35ed63fb4f0e4beca71b295e3f00f11c7e62a823927aac4cdeaf602a52",
        "whole_sha256": "4a898e86b6cea2445a247aee4d53b29b7306563996975462dc084945fa0ca878",
        "interface_sha256": "c760682209b67b28f5a5a76e80fd8913dcd7b0a98995ac314c64987bad6276b0",
        "rshift_count": 3,
    },
    DLA_AGENT_KEY: {
        "raw_bytes": 7791,
        "raw_sha256": "cae55bc611428b4e6938a79814898c8bda2a3af19b303502ec5b77f5479b88f9",
        "norm_bytes": 5998,
        "norm_sha256": "42ab52479b08fb567ce8d91d9946d0f67025a3f74c369149981c7d8c0afc3098",
        "functions_sha256": "309b3bc451c5471c50aa7f78c9fa5bc8b5c6f3f5b838bc2a5a8f0d74e9c49fac",
        "whole_sha256": "8e23638833b84a4abe58d15bc47b78ab54be59258ae1d58ac877344e3fb9d16a",
        "interface_sha256": "0c30d67bdb183aac29b001aa7fb06e58687ea1257fc4160628fcc48643f59d3d",
        "rshift_count": 3,
    },
    ATTRACTOR_AGENT_KEY: {
        "raw_bytes": 6045,
        "raw_sha256": "cfe98602348063ab7cb3aa0c642f70de000c2352a40368e8fc9eddcf47447e82",
        "norm_bytes": 4962,
        "norm_sha256": "40a92be211e8fdf13632733980068dc859f0537d5a6ea41e6f23a880a6da2b82",
        "functions_sha256": "0fa03645f358ef1548d70d161d1de8a3537c9515b3ccc6192a03315c6687792b",
        "whole_sha256": "fdf7bfecf50c8e0bd9203bea3ade19426ff315b3d4468711a9891a90eb1f3477",
        "interface_sha256": "67f852eea1830480136dcda6881990f5a10a467ba3a9d94f765515a2d9b0118d",
        "rshift_count": 3,
    },
}


_FLOW3D_DYNAMIC_PROFILE = {
    **_PROFILES[FLOW3D_AGENT_KEY],
    "norm_bytes": 7343,
    "norm_sha256": "ae17b10b719181a4d613ebcb0b94b433f6fb9bbf834d3e48af88f58e93f327ac",
    "functions_sha256": "c86c927f2fb8bf59b6c792a46c515059f8c0b59e4b8bb8bfc673c2e775e02b40",
    "whole_sha256": "4c4b20021fac2c8676319378ec9bbcda8b134e909341fb674b3de21a254162cf",
    "interface_sha256": "fd22dc46e80d2bc1fc46fd94322484a52668d588ff0271a6f531c8e2e3632142",
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


def authenticate_hash_scalar_uint_rshift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate hash scalar uint right shift carriers and return exact AST >> nodes."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in HASH_SCALAR_UINT_RSHIFT_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {HASH_SCALAR_UINT_RSHIFT_KEYS}")
    expected = (_FLOW3D_DYNAMIC_PROFILE
                if program.key == FLOW3D_AGENT_KEY
                and tuple((item.name, item.kind, item.canonical_value)
                          for item in program.preprocessor_defines)
                == (("BEHAVIOR", "str", "int"),)
                else _PROFILES[program.key])
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

    rshifts: list[TypedExpression] = []
    for fn in program.functions:
        for stmt in fn.body:
            for expr in _walk_statement(stmt):
                if getattr(expr, "kind", None) == "binary" and getattr(expr, "operator", None) == ">>":
                    if (expr.type.display() == "uint"
                            and len(expr.children) == 2
                            and expr.children[0].type.display() == "uint"
                            and expr.children[1].type.display() == "uint"):
                        rshifts.append(expr)

    if len(rshifts) != expected["rshift_count"]:
        raise ValueError(
            f"{PROFILE}: {program.key} expected {expected['rshift_count']} scalar uint right shift sites, found {len(rshifts)}")

    return tuple(rshifts)


def apply_hash_scalar_uint_rshift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Validate profile and return program untouched (identity carrier)."""
    authenticate_hash_scalar_uint_rshift(program, source_hash, profile)
    return program
