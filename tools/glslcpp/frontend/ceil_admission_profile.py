"""Closed identity profile for the fused ``int(ceil(x))`` site.

```glsl
int sampleLimit = int(ceil(fr));      // filter/oilPaint:oilFlatten
int r           = int(ceil(radius));  // filter/smooth:smoothBlend
```

Structurally parallel to ``as_u32_round_profile.py``: a dict of per-program
frozen fingerprints (raw/normalized source, function inventory hash,
whole-program and interface hashes, and the exact span/node/argument hashes of
every owned ``ceil`` node), following ``loop_proof.py``'s
``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` precedent, since the shape recurs across
programs rather than being a one-off.

Adds **no new capability token**. ``ceil`` never joins ``_BUILTINS`` or
``APPROVED_CAPABILITIES``; it is admitted purely by node identity through the
same special-cased builtin-name check that already carries ``round`` / ``tanh``
/ ``floatBitsToUint`` / ``all`` / ``lessThanEqual``. The frozen 44-entry
vocabulary is untouched.

Reference semantics: the transpiled JS materializes GLSL ``ceil`` as the shared
runtime's ``ceil: unary(Math.ceil)``, narrowed to f32 immediately on return
(``#unary``: ``F32(operation(value))``). ``Math.ceil`` and ``std::ceil`` agree
on every finite double — unlike ``round``, whose reference form is
``Math.round`` (round-half-toward-+infinity) and matches neither the GLSL spec
nor ``std::round``. So no bespoke narrowing shim is needed here; that asymmetry
is exactly why this is a separate profile from the round admission rather than
a shared one.

The whole-program census below is an EXACT set match: a ``ceil`` node anywhere
outside the frozen set is a hard failure, not an unnoticed extra.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement

PROFILE = "ceil-admission-v1"

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)
# effects alone of the three carriers also carries the mutable-global array
# closure whose row the generator auto-attaches
# `fixed_array_in_parameter_proof` (`effects-convolve-v1`) to before
# validation -- so the strict "every optional proof absent" set would reject
# the authentic row (`ceil-admission-v1: unrelated proof carrier is not
# absent`, the review's third-module finding). The carve is PER KEY (the
# scalar-XOR module's kaleido precedent): the other two carriers keep the
# full absent set. Exactness of the attached proof is not this module's
# concern; the fixed-array arms at both authorities own that equality lock
# (the Amendment 13.2 family split).
_FIXED_ARRAY_PROOF_COMPANION_KEYS = frozenset(
    {"classicNoisedeck/effects:effects"})


def _absent_proof_fields(key: str) -> tuple[str, ...]:
    """The optional-proof fields that must be None for ``key``."""
    if key in _FIXED_ARRAY_PROOF_COMPANION_KEYS:
        return tuple(field for field in _OPTIONAL_PROOF_FIELDS
                     if field != "fixed_array_in_parameter_proof")
    return _OPTIONAL_PROOF_FIELDS


_PROFILES: dict[str, dict] = {
    "synth/roll:roll": {
        "raw_bytes": 2305,
        "raw_sha256": "92b426fa60df51c3db057b8f93ce3c6525cf087fd2398c6e038046f9ede1d8c9",
        "normalized_bytes": 1989,
        "normalized_sha256": "0510d1d997a1c0c79eeece4a59c9fe184be7f6bf9f1e49b400771c2986b7174a",
        "functions_sha256": "e6deb1e52c6bdf2a93af4bf67aeaeb9b5760ef0e0f9b45bc779fb18f8cf923f0",
        "whole_program_sha256": "937886a84885a0faf8fdda051771317b7df7575f831368dee800de54137b815c",
        "interface_sha256": "57bda2f873825d9287c4d4831d7d6a5ebf3457c090f66741ca22a13a02fbdd97",
        "ceil_sites": (
            ("main", "47:29-47:47",
             "8e3da9af88b192ceb663108fe6945675fdd344e753e4653e3e3bc87fc7af4091",
             "5c069493a46a824a6f1298050ba443461226b5a8b85f83eb4f20b4f8ee6d94d0"),
        ),
    },
    "filter/oilPaint:oilFlatten": {
        "raw_bytes": 7321,
        "raw_sha256": "f2f512b35b846d8a15362739a843c162199b7c53d95251918576726b1b094690",
        "normalized_bytes": 3931,
        "normalized_sha256": "2c3df202449636be575a4e5dad4ffe2ea45cd06179cb7dcce88062afc9af1cec",
        "functions_sha256": "843b8fa8d65f4f3508bd0a559b70b264638ac9ca9da157dc4f4900a70acd102e",
        "whole_program_sha256": "8b189cb2e633fbfdcc2a6ab427f8a6210d16ef49edc691cf982a80eb4eb978dd",
        "interface_sha256": "a292ee0fb7b8c029197e606a74be59737c46196dfcbfd0cda2038e2bf6146be6",
        "ceil_sites": (
            ("main", "25:27-25:35",
             "8f2f404e8d2bad6e59019d757fd9a575350b9e1d3fec311f37a3ae5e3de896fd",
             "a611d9adb9074ed9a3cc6177f1651f0f6f3f0fd11169b1f6d3964630af71d24d"),
        ),
    },
    "filter/smooth:smoothBlend": {
        "raw_bytes": 6858,
        "raw_sha256": "c317194f9bbdba9d95c5dcae47e2354221cf0cdb05ffcf14e335a94a4ef3729c",
        "normalized_bytes": 6072,
        "normalized_sha256": "985d7e1324748f706e52b828c144adc2cefa8c70d00ef3a548a939b194d042d8",
        "functions_sha256": "ca788b21fdca0483acc5a5191e662b2d6a97ea15ba5d2c038f8899927b9a874d",
        "whole_program_sha256": "cbbe53eeb5d3bbfd9515875a65d2095849cd142ee8564a07b54ad8138fb1c3e9",
        "interface_sha256": "e6f32fe87fa270c2ae21782c62938d35bffc5b1ca40f461745e207f77c3496ab",
        "ceil_sites": (
            ("edgeBlur", "168:17-168:29",
             "666aa114d810fd36a7c260cba9df877fe24843c79d89638701412b197478aeb8",
             "01c48430fb96aa51d2b13835d149b17da6fa62caad02c043c17163c32514f5bc"),
        ),
    },
    # effects-design §5 mechanism E: the two ceil sites are REACHABLE main
    # code (`uv.x -= ceil(...)`, `uv.y += ceil(...)` -- statements 10/11),
    # this program's one new reachable grammar element (the module census is
    # otherwise unreachable-only for the first two carriers).
    "classicNoisedeck/effects:effects": {
        "raw_bytes": 21087,
        "raw_sha256": "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c",
        "normalized_bytes": 15773,
        "normalized_sha256": "cce2f30177586f4cdabab1e1741a99d1470f49db79c60dc20df9ddbcac9bdfda",
        "functions_sha256": "d06fd4218bd7513a5aecd343bc3bb9d83dfb6b8fba011626fd5bb80707d67579",
        "whole_program_sha256": "db85c4d2cafed8c07bc03d3e203ec83d099575ade15b5b452a9eeb58bb4940d1",
        "interface_sha256": "feeb85a578bad5296e9c345401f7f1a6055da9aa6f5f476c346137f53cdeef52",
        "ceil_sites": (
            ("main", "574:13-574:99",
             "5405bd10d70c8361e0f51e63972b4c3b091348ef95a80adb3c8bc18d3cc3d4df",
             "2a885db687152218ee67b5753cbc8d3fa91534135dc2ece5d1909922b3577622"),
            ("main", "575:13-575:109",
             "0f65b650b6a68a26163014021dc3febbe512a8db24774ea6223570ebfd5a4137",
             "5105faf67c1fdaabce2af946c6577d9c3ee7fe88462c5607dcb02f182779ca8a"),
        ),
    },
    # points/lenia:convolve -- one ceil site in main, the operand of the
    # `int(ceil(searchRadius))` window-radius cast (44:23). Composes with the
    # program's runtime-loop-bound record exactly like synth/curl composes
    # with its vector-math closure: an independent companion authenticated by
    # its own exact block. Figures measured on the post-runtime-apply tree
    # (proofs attached), the tree both the generator and the emitter see.
    "points/lenia:convolve": {
        "raw_bytes": 2019,
        "raw_sha256": "911443464a21bac3436a3d8a9505859b1f6eda97aa0e24ce633aa312970dbc44",
        "normalized_bytes": 1412,
        "normalized_sha256": "066659ba74c22a997773d408977f4e3871f25b9f1f5b59770561bc60a30157b2",
        "functions_sha256": "7ce243bd6ad3b0d3861addc987f515cf196b4b9d21299814f6cadece0d09e09f",
        "whole_program_sha256": "31976ede7a915da80db83452260a36268e95efa577223d30637b008d36f5446e",
        "interface_sha256": "abc96797b7cc6aac133bd6a6f26ef2139f030d430e3d853021dd49cbdc2e9428",
        "ceil_sites": (
            ("main", "44:23-44:41",
             "24d5cf57fed715ab8f2f84048bbc9c578c21968dc7755f7e5c835c2c5fcba64d",
             "f1d724f5dbc549e1a1bb41e3d326549b2fe20f6d4f8d522f89836361c8e884e9"),
        ),
    },
}

CEIL_ADMISSION_KEYS = frozenset(_PROFILES)

__all__ = ("PROFILE", "CEIL_ADMISSION_KEYS", "authenticate_ceil_admission")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface_fingerprint(program: TypedProgram) -> str:
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


def authenticate_ceil_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the exact authenticated ``ceil`` nodes for ``program.key``.

    Returns an empty tuple when ``program.key`` is not a carrier, so callers can
    treat the result as a membership set unconditionally.
    """
    expected = _PROFILES.get(program.key)
    if expected is None:
        if profile is not None:
            raise _fail("program key is not an admitted ceil carrier")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["normalized_sha256"]
            or program.body_status != "analyzed"):
        raise _fail("source, key, or body profile mismatch")
    if (_sha(program.functions) != expected["functions_sha256"]
            or _whole_program_fingerprint(program) != expected["whole_program_sha256"]
            or _interface_fingerprint(program) != expected["interface_sha256"]):
        raise _fail("function, whole-program, or interface profile mismatch")
    if any(getattr(program, field, None) is not None
           for field in _absent_proof_fields(program.key)):
        raise _fail("unrelated proof carrier is not absent")

    # Census the WHOLE program: the set of ceil nodes must match the frozen set
    # exactly. An extra site anywhere is a hard failure.
    found: list[tuple[str, TypedExpression]] = []
    for function in sorted(program.functions, key=lambda item: item.id):
        for statement in function.body:
            for value in _walk_statement(statement):
                if (isinstance(value, TypedExpression) and value.kind == "builtin"
                        and value.callee == "ceil"):
                    found.append((function.name, value))
    if len(found) != len(expected["ceil_sites"]):
        raise _fail("expected exactly the owned ceil site(s)")

    authorized: list[TypedExpression] = []
    for (owner, value), (name, span, node_sha, arg_sha) in zip(
            sorted(found, key=lambda item: _span(item[1])),
            sorted(expected["ceil_sites"], key=lambda item: item[1])):
        if (owner != name or value.category != "rvalue"
                or len(value.children) != 1
                or value.type.display() != "float"
                or value.children[0].type.display() != "float"
                or _span(value) != span or _sha(value) != node_sha
                or _sha(value.children[0]) != arg_sha):
            raise _fail("ceil site or argument profile mismatch")
        authorized.append(value)
    return tuple(authorized)
