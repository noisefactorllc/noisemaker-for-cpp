"""Exact spawn-color comparison closure of the particle behaviors' base-color memory.

Seven particle agent programs carry the same ``baseColor(ivec2, vec4, vec2)``
helper. It keeps a behavior's base color while a diffuse map is active and
returns the live color when the agent respawned:

    vec4 spawnDelta = abs(round(rgba * 255.0) - round(clamp(spawnColor(pos), 0.0, 1.0) * 255.0));
    return all(lessThanEqual(spawnDelta, vec4(1.0))) ? rgba : kept;

This module admits only the four builtin nodes of that helper: the two
``round(vec4)`` sites, the ``lessThanEqual(vec4, vec4)`` relational and its
``all(bvec4)`` reduction. The ``bvec4`` value is consumed immediately by
``all`` and is never declared, stored or returned. The CPU authority
evaluates both ``round`` operands as Float32Array lanes and applies
``Math.round`` per lane, then narrows each lane to f32.

Admission is by object identity, keyed by each program's exact source and IR
digests. It is fail-closed: a changed source, an extra or missing site, or a
bvec value outside the relational aborts. No capability vocabulary token is
added.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "particle-base-color-admission-v1"

_ROUND_SIGNATURE_ID = -38
_ALL_SIGNATURE_ID = -3
_LESS_THAN_EQUAL_SIGNATURE_ID = -24

_PINS = {
    "points/dla:agent": {
        "raw_bytes": 7791, "raw_sha256": "cae55bc611428b4e6938a79814898c8bda2a3af19b303502ec5b77f5479b88f9",
        "norm_bytes": 5998, "norm_sha256": "42ab52479b08fb567ce8d91d9946d0f67025a3f74c369149981c7d8c0afc3098",
        "functions_sha256": "309b3bc451c5471c50aa7f78c9fa5bc8b5c6f3f5b838bc2a5a8f0d74e9c49fac",
        "whole_sha256": "8e23638833b84a4abe58d15bc47b78ab54be59258ae1d58ac877344e3fb9d16a",
        "interface_sha256": "0c30d67bdb183aac29b001aa7fb06e58687ea1257fc4160628fcc48643f59d3d",
        "function_span": "54:1-59:2",
        "nodes": (('round', '57:27-57:46'), ('round', '57:49-57:96'), ('all', '58:12-58:53'), ('lessThanEqual', '58:16-58:52')),
        "outside_rounds": 0,
    },
    "points/flock:agent": {
        "raw_bytes": 11303, "raw_sha256": "3be70196fe1ffee473c7352e5a13d600f507a1bb6f6005622d1c1d03f8b6c156",
        "norm_bytes": 9625, "norm_sha256": "64fba0ca7fa41e701271dd0a713a3427a265f7b599bac510d6eceadea14af792",
        "functions_sha256": "03293a8f9c0ef0a0b627253fe6762f0bd3a62d56c48ed9040bb8913608abee2d",
        "whole_sha256": "59099a0064e8e9af2ebf7477febcb2e1e22fa8272d77222018ec52abfcbbff70",
        "interface_sha256": "25653fe91b5d3024f18a0e791a41dadf848caa7d5644b8b859c581923f4455cb",
        "function_span": "53:1-58:2",
        "nodes": (('round', '56:27-56:46'), ('round', '56:49-56:96'), ('all', '57:12-57:53'), ('lessThanEqual', '57:16-57:52')),
        "outside_rounds": 0,
    },
    "points/flow:agent": {
        "raw_bytes": 7515, "raw_sha256": "f8149c037daa3172ccafdb0ffcadbebad3a5fd7d3b9fa1112861518cddfede06",
        "norm_bytes": 6144, "norm_sha256": "d4dc5e40a1e5454c2285b923dd582b34bf1b25413032f51edcfbe433b43ae9d2",
        "functions_sha256": "3415b919eb0ed7725d7f3cd6f66c6d0218d6d995a460da8a212c371a75d96cd7",
        "whole_sha256": "0961e0f4e18f00c6d43153a299c33eacf486d88e4a6f8e60e029dceede0f4a70",
        "interface_sha256": "101c5b05335de2dfa3513c14b9c93c22840f39e48c6b4db83bae72b88153a2b1",
        "function_span": "51:1-56:2",
        "nodes": (('round', '54:27-54:46'), ('round', '54:49-54:96'), ('all', '55:12-55:53'), ('lessThanEqual', '55:16-55:52')),
        "outside_rounds": 1,
    },
    "points/hydraulic:agent": {
        "raw_bytes": 7967, "raw_sha256": "02bff511e46a3e32cfd7d2aa0c8d49d24a9590441c8900379241ba210a06a0fc",
        "norm_bytes": 6240, "norm_sha256": "b03ff45edcbdd617ac3d2c3b60731d42d10de712a0c1300e0753e650671630c2",
        "functions_sha256": "fb16393b74c70d7c255e3e5322fecb4b93bf3484776464db4c98eb95ef4d0623",
        "whole_sha256": "d957cc2617462e61c53df93c7a68f8fed85039cf5f458bd6fbc3100e58b8f5a3",
        "interface_sha256": "f277f8af2f050e111e372896f97bedcdb09bfa0483345fb6b77934bc0708f761",
        "function_span": "49:1-54:2",
        "nodes": (('round', '52:27-52:46'), ('round', '52:49-52:96'), ('all', '53:12-53:53'), ('lessThanEqual', '53:16-53:52')),
        "outside_rounds": 0,
    },
    "points/lenia:agentField": {
        "raw_bytes": 5099, "raw_sha256": "b5f996e1d84485c4726801aed539690cd242529a81d2101f98cb8ef2ccc56d87",
        "norm_bytes": 3568, "norm_sha256": "7e60f274f421f57c00b3a8b0d050b1ed1c3bfcabc802c90b6fb2aea4f65d17b9",
        "functions_sha256": "0bc4e171eac5782ff04e6d060a620a55c433c2c6ce0953572f92b756a9c7bb6b",
        "whole_sha256": "5b918e77ceeabdcaefc0751923274b7a816a92e00b7ae9490b0b40c29b561cde",
        "interface_sha256": "6cfdaedde03c1c15c28c5c46f73665753c69fe452c5ff3317262abae300f5aa6",
        "function_span": "51:1-56:2",
        "nodes": (('round', '54:27-54:46'), ('round', '54:49-54:96'), ('all', '55:12-55:53'), ('lessThanEqual', '55:16-55:52')),
        "outside_rounds": 0,
    },
    "points/physarum:agent": {
        "raw_bytes": 6510, "raw_sha256": "a9b21cee808cf70e7d29d05f27bdf9bd598ef1f5ac8dae492e6541cf21456e2f",
        "norm_bytes": 5059, "norm_sha256": "1d643cf97a028845eb22904b69a761b1002b715df5d92203a68e54137df89290",
        "functions_sha256": "435c2a35ed63fb4f0e4beca71b295e3f00f11c7e62a823927aac4cdeaf602a52",
        "whole_sha256": "4a898e86b6cea2445a247aee4d53b29b7306563996975462dc084945fa0ca878",
        "interface_sha256": "c760682209b67b28f5a5a76e80fd8913dcd7b0a98995ac314c64987bad6276b0",
        "function_span": "48:1-53:2",
        "nodes": (('round', '51:27-51:46'), ('round', '51:49-51:96'), ('all', '52:12-52:53'), ('lessThanEqual', '52:16-52:52')),
        "outside_rounds": 0,
    },
    "points/physical:agent": {
        "raw_bytes": 5690, "raw_sha256": "06f3afef8efeaba67f1babf129ee107b06e860ec8458e270ce404fc770b46615",
        "norm_bytes": 4152, "norm_sha256": "8ec3c18241a32241e625c44e71377de7e212901cafebb01f70c193aec2ea5edb",
        "functions_sha256": "e9799e4cb945b8fd49099121faf71307f0d3ee0f46a36d60241fc8acd959e9e0",
        "whole_sha256": "caad738335a8200c1ef5a9ce7034977e0704ea7dcb88c1da869868f57fea3d98",
        "interface_sha256": "ca1c4bff0124fb5664d0c5d2cece4849dda6458633ef06517a63d19e4c4dfcd6",
        "function_span": "49:1-54:2",
        "nodes": (('round', '52:27-52:46'), ('round', '52:49-52:96'), ('all', '53:12-53:53'), ('lessThanEqual', '53:16-53:52')),
        "outside_rounds": 0,
    },
}

PARTICLE_BASE_COLOR_KEYS = frozenset(_PINS)


@dataclass(frozen=True, slots=True)
class ParticleBaseColorProof:
    function: TypedFunction
    rounds: tuple[TypedExpression, TypedExpression]
    relational: TypedExpression
    reduction: TypedExpression

    @property
    def nodes(self) -> tuple[TypedExpression, ...]:
        return (*self.rounds, self.reduction, self.relational)


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


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _display(value: TypedExpression | None) -> str | None:
    return None if value is None or value.type is None else value.type.display()


def authenticate_particle_base_color(
        program: TypedProgram, source_hash: str | None) -> ParticleBaseColorProof:
    """Authenticate the exact base-color closure and return its four nodes."""
    expected = _PINS.get(program.key)
    if expected is None:
        raise _fail(f"program key {program.key} is not an admitted carrier")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]
            or program.preprocessor_defines
            or program.body_status != "analyzed"
            or _sha(program.functions) != expected["functions_sha256"]
            or _whole(program) != expected["whole_sha256"]
            or _interface(program) != expected["interface_sha256"]):
        raise _fail(f"{program.key} source, function, whole-program, or interface mismatch")

    helpers = [item for item in program.functions if item.name == "baseColor"]
    if len(helpers) != 1:
        raise _fail(f"{program.key} expected one baseColor helper")
    function = helpers[0]
    if (function.return_type.display() != "vec4"
            or tuple(item.type.display() for item in function.parameters)
            != ("ivec2", "vec4", "vec2")
            or len(function.body) != 4
            or _span(function) != expected["function_span"]):
        raise _fail(f"{program.key} baseColor identity mismatch")

    # Census the WHOLE program. all/lessThanEqual and every bvec value occur
    # only inside baseColor; a round outside it belongs to another profile
    # and its count is frozen here.
    located: list[TypedExpression] = []
    outside_rounds = 0
    for candidate in program.functions:
        for statement in candidate.body:
            for item in _walk_statement(statement):
                display = _display(item)
                if (candidate is not function and display is not None
                        and display.startswith("bvec")):
                    raise _fail(f"{program.key} bvec value outside baseColor")
                if item.kind != "builtin" or item.callee not in ("round", "all", "lessThanEqual"):
                    continue
                if candidate is function:
                    located.append(item)
                elif item.callee == "round":
                    outside_rounds += 1
                else:
                    raise _fail(f"{program.key} {item.callee} outside baseColor")
    if outside_rounds != expected["outside_rounds"]:
        raise _fail(f"{program.key} round census mismatch outside baseColor")
    if tuple((item.callee, _span(item)) for item in located) != expected["nodes"]:
        raise _fail(f"{program.key} closure node identity mismatch")

    declaration, conditional_return = function.body[2], function.body[3]
    if (declaration.kind != "decl" or len(declaration.expressions) != 1
            or conditional_return.kind != "return"
            or len(conditional_return.expressions) != 1):
        raise _fail(f"{program.key} baseColor statement shape mismatch")
    initializer = declaration.expressions[0]
    absolute = initializer.children[0] if len(initializer.children) == 1 else None
    difference = (absolute.children[0]
                  if absolute is not None and len(absolute.children) == 1 else None)
    if (initializer.kind != "declaration" or _display(initializer) != "vec4"
            or absolute is None or absolute.kind != "builtin" or absolute.callee != "abs"
            or _display(absolute) != "vec4"
            or difference is None or difference.kind != "binary"
            or difference.operator != "-" or len(difference.children) != 2):
        raise _fail(f"{program.key} spawnDelta shape mismatch")
    rounds = (difference.children[0], difference.children[1])
    if rounds[0] is not located[0] or rounds[1] is not located[1]:
        raise _fail(f"{program.key} round sites are not the spawnDelta operands")
    for item in rounds:
        operand = item.children[0] if len(item.children) == 1 else None
        if (item.signature_id != _ROUND_SIGNATURE_ID or _display(item) != "vec4"
                or operand is None or operand.kind != "binary" or operand.operator != "*"
                or _display(operand) != "vec4" or len(operand.children) != 2
                or operand.children[1].kind != "literal"
                or operand.children[1].literal_value != 255.0):
            raise _fail(f"{program.key} malformed round(vec4 * 255.0) site")

    conditional = conditional_return.expressions[0]
    reduction, relational = located[2], located[3]
    if (conditional.kind != "conditional" or len(conditional.children) != 3
            or conditional.children[0] is not reduction
            or reduction.signature_id != _ALL_SIGNATURE_ID
            or _display(reduction) != "bool"
            or len(reduction.children) != 1 or reduction.children[0] is not relational
            or relational.signature_id != _LESS_THAN_EQUAL_SIGNATURE_ID
            or _display(relational) != "bvec4"
            or tuple(_display(item) for item in relational.children) != ("vec4", "vec4")):
        raise _fail(f"{program.key} malformed all(lessThanEqual(vec4, vec4)) closure")
    spawn_delta = relational.children[0]
    if spawn_delta.kind != "id" or spawn_delta.symbol is None or spawn_delta.symbol.name != "spawnDelta":
        raise _fail(f"{program.key} relational does not read spawnDelta")

    bvec_nodes = [item for statement in function.body for item in _walk_statement(statement)
                  if (_display(item) or "").startswith("bvec")]
    if len(bvec_nodes) != 1 or bvec_nodes[0] is not relational:
        raise _fail(f"{program.key} bvec4 value escapes its immediate reduction")
    return ParticleBaseColorProof(function, rounds, relational, reduction)


def is_authenticated_round(proof: ParticleBaseColorProof | None, node: object) -> bool:
    return proof is not None and any(node is item for item in proof.rounds)


__all__ = ("PROFILE", "PARTICLE_BASE_COLOR_KEYS", "ParticleBaseColorProof",
           "authenticate_particle_base_color", "is_authenticated_round")
