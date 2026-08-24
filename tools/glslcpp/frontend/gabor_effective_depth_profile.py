"""Exact source-authenticated effective-depth policy for Gabor.

This is deliberately not a general counted-loop widening.  The semantic
frontend already proves every Gabor loop.  This profile authenticates the
complete candidate and returns candidate-owned proof/function/statement
objects so the validator and emitter may independently permit effective depth
four for this program only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

from .typed_ir import (
    CountedLoopProgramProof,
    TypedFunction,
    TypedProgram,
    TypedStatement,
)


PROFILE = "gabor-effective-depth-4-v1"
GABOR_KEY = "synth/gabor:gabor"

_RAW_BYTES = 3870
_RAW_SHA256 = "91665da2d584d6d88b38e8ba314dfc0b546dd49d29aa161f5d66aecf6bf67bf5"
_NORMALIZED_BYTES = 3325
_NORMALIZED_SHA256 = "c6ba77aa9356f28d74488499da414638422f3b0fbd4d1a3e9efce986acbabf53"
_FUNCTIONS_SHA256 = "aceaa52e3b81ed3c6321d0fd554289d537740af19aec64c831c371a804ed9d16"
_WHOLE_PROGRAM_SHA256 = "23a70538ffb5a8be5f192bbe12051608552fa56e92150c678b4eaea50beac3e3"
_INTERFACE_SHA256 = "a907bff6e0b13d1077e6517555f53613c5c05e4115fe39d96d0a759750558f38"
_METADATA_SHA256 = "ac6932d14a15cb06b388f7fa08919042b29c8bd1b9200eaa418fa922c6787b8a"

_PROGRAM_PROOF = (4, 0, 4, 72, 425, True)
_RESOURCES = (
    ("resolution", "tileOffset", "fullResolution", "time", "seed", "scale",
     "orientation", "bandwidth", "isotropy", "density", "octaves", "speed"),
    (), ("fragColor",), False, False,
)
_DECLARATIONS = (
    (1, "resolution", "vec2", "uniform", False, "in", "4:1-4:25"),
    (2, "tileOffset", "vec2", "uniform", False, "in", "5:1-5:25"),
    (3, "fullResolution", "vec2", "uniform", False, "in", "6:1-6:29"),
    (4, "time", "float", "uniform", False, "in", "7:1-7:20"),
    (5, "seed", "float", "uniform", False, "in", "8:1-8:20"),
    (6, "scale", "float", "uniform", False, "in", "9:1-9:21"),
    (7, "orientation", "float", "uniform", False, "in", "10:1-10:27"),
    (8, "bandwidth", "float", "uniform", False, "in", "11:1-11:25"),
    (9, "isotropy", "float", "uniform", False, "in", "12:1-12:24"),
    (10, "density", "float", "uniform", False, "in", "13:1-13:23"),
    (11, "octaves", "float", "uniform", False, "in", "14:1-14:23"),
    (12, "speed", "float", "uniform", False, "in", "15:1-15:21"),
    (13, "fragColor", "vec4", "output", True, "in", "16:1-16:16"),
)
_FUNCTIONS = (
    (29, "gaborNoise", "float", 8, 5, "44:1-81:2",
     "b3ccf364a6c6d502663d73136ceda1a9deb23b35ceaaf19cd6a4f1522b54ccdc"),
    (30, "main", "void", 0, 19, "83:1-118:2",
     "3a445664e348e818d9b717f2379665f2ad231c6c56000fdbdfa57ab40f38a238"),
    (31, "map", "float", 5, 1, "39:1-41:2",
     "ab32650efe76f0c6aaa910bcc9c5890ae4c1df2314a4fe46c0e593a483e369c5"),
    (32, "pcg", "uvec3", 1, 9, "20:1-30:2",
     "c0b8b6e04415f3fccdf1a228dfdad0e7558f6ce6a9ffd2bb4a4e3f1af6f82781"),
    (33, "prng", "vec3", 1, 4, "32:1-37:2",
     "8cff065622e1cfb96c51df737a96a75ed5d720fd9a2fd8a60b7e0b2821d577a2"),
)
_LOOPS = (
    (29, "gaborNoise", "for", "49:5-79:6",
     "5723ebb0f0af04516281d8da3bc0c73f09f486c728f8459f0d8fe6d5e1ae94c7",
     3, 1, 2, 72, 425),
    (29, "gaborNoise", "for", "50:9-78:10",
     "63384855eb3ca1af2a86806b52829c70be3a22b01c2c17e0324d1d048005907c",
     3, 2, 3, 72, 425),
    (29, "gaborNoise", "for", "54:13-77:14",
     "daf0f0add9d0be6310ec527bc5126f4d5bc6acf6e324ef643ef0ebf1a0b919d5",
     8, 3, 4, 72, 425),
    (30, "main", "for", "104:5-113:6",
     "1018cb4de2542972568ccadcf48a738338be2da24a0cecafce828358cef15da1",
     5, 1, 1, 5, 425),
)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class GaborEffectiveDepthContract:
    key: str
    maximum_effective_depth: int
    program_proof: CountedLoopProgramProof
    owners: tuple[TypedFunction, ...]
    loops: tuple[TypedStatement, ...]
    _candidate: TypedProgram = field(repr=False, compare=False)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _walk(statements: tuple[TypedStatement, ...]):
    for statement in statements:
        yield statement
        yield from _walk(statement.children)


def _proof_tuple(proof: CountedLoopProgramProof) -> tuple[object, ...]:
    return (proof.loop_count, proof.unproved_loop_count,
            proof.max_effective_depth, proof.max_lexical_product,
            proof.entrypoint_charge, proof.call_graph_acyclic)


def _whole(program: TypedProgram) -> tuple[object, ...]:
    return (program.key, program.source, program.raw_source,
            program.declarations, program.functions, program.resources,
            program.body_status, program.local_type_names, program.structs,
            program.uniform_blocks, program.interface_symbols,
            program.builtin_symbols, program.counted_loop_proof,
            program.preprocessor_defines)


def _interface(program: TypedProgram) -> tuple[object, ...]:
    return (program.declarations, program.resources,
            program.local_type_names, program.structs,
            program.uniform_blocks, program.interface_symbols,
            program.builtin_symbols, program.preprocessor_defines)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _candidate_loop_rows(program: TypedProgram):
    owners: list[TypedFunction] = []
    loops: list[TypedStatement] = []
    rows = []
    for function in program.functions:
        for statement in _walk(function.body):
            if statement.kind not in {"for", "while", "dowhile"}:
                continue
            proof = statement.loop_proof
            if proof is None:
                raise _fail("unproved loop in authenticated candidate")
            owners.append(function)
            loops.append(statement)
            rows.append((
                function.id, function.name, statement.kind, _span(statement),
                _sha(statement), proof.trip_count, proof.lexical_depth,
                proof.effective_depth, proof.lexical_product,
                proof.entrypoint_charge,
            ))
    return tuple(owners), tuple(loops), tuple(rows)


def validate_gabor_effective_depth_contract(
        contract: GaborEffectiveDepthContract) -> GaborEffectiveDepthContract:
    """Revalidate candidate ownership before either authority consumes it."""
    candidate = contract._candidate
    if (contract.key != GABOR_KEY or candidate.key != GABOR_KEY
            or contract.maximum_effective_depth != 4
            or candidate.counted_loop_proof is not contract.program_proof
            or _proof_tuple(contract.program_proof) != _PROGRAM_PROOF):
        raise _fail("malformed authenticated effective-depth contract")
    owners, loops, rows = _candidate_loop_rows(candidate)
    if (rows != _LOOPS or len(contract.owners) != len(owners)
            or len(contract.loops) != len(loops)
            or any(actual is not expected
                   for actual, expected in zip(contract.owners, owners))
            or any(actual is not expected
                   for actual, expected in zip(contract.loops, loops))):
        raise _fail("malformed authenticated effective-depth contract")
    return contract


def authenticate_gabor_effective_depth(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> GaborEffectiveDepthContract:
    """Authenticate the exact canonical Gabor candidate."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != GABOR_KEY:
        raise _fail("profile on foreign key")
    if source_hash != _RAW_SHA256:
        raise _fail("exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _sha(_whole(program)) != _WHOLE_PROGRAM_SHA256
            or _sha(_interface(program)) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field_name, None) is not None
           for field_name in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES):
        raise _fail("resource or binding signature mismatch")
    declarations = tuple(
        (item.symbol.id, item.symbol.name, item.symbol.type.display(),
         item.symbol.storage, item.symbol.writable, item.symbol.direction,
         _span(item.symbol))
        for item in program.declarations)
    if declarations != _DECLARATIONS:
        raise _fail("declaration inventory mismatch")
    functions = tuple(
        (item.id, item.name, item.return_type.display(), len(item.parameters),
         len(item.body), _span(item), _sha(item))
        for item in program.functions)
    if functions != _FUNCTIONS:
        raise _fail("function inventory mismatch")
    proof = program.counted_loop_proof
    if proof is None or _proof_tuple(proof) != _PROGRAM_PROOF:
        raise _fail("loop or call graph profile mismatch")
    owners, loops, rows = _candidate_loop_rows(program)
    if rows != _LOOPS:
        raise _fail("loop statement, owner, or proof mismatch")

    return validate_gabor_effective_depth_contract(
        GaborEffectiveDepthContract(
            GABOR_KEY, 4, proof, owners, loops, program))


def validate_gabor_metadata(effect: object) -> None:
    """Authenticate the complete eight-parameter, one-pass metadata record."""
    try:
        encoded = json.dumps(effect, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        raise _fail("metadata contract mismatch") from None
    if hashlib.sha256(encoded.encode("utf-8")).hexdigest() != _METADATA_SHA256:
        raise _fail("metadata contract mismatch")


__all__ = (
    "PROFILE", "GABOR_KEY", "GaborEffectiveDepthContract",
    "authenticate_gabor_effective_depth",
    "validate_gabor_effective_depth_contract", "validate_gabor_metadata",
)
