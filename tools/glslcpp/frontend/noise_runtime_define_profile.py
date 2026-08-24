"""Authenticated dynamic-define normalization for ``synth/noise``.

Noise's two selector defines are uniforms in the native runtime.  The GLSL
source declares ``base`` only in the nested ``LOOP_OFFSET == 300`` branches;
the dynamic preprocessor lowers those branches to ordinary statements, so the
declaration must be hoisted before semantic analysis.  This transform is
deliberately source-locked and line-preserving.
"""

from __future__ import annotations

import hashlib


KEY = "synth/noise:noise"
PROFILE = "runtime-defines-noise-v1"
DYNAMIC_DEFINES = {"NOISE_TYPE": "int", "LOOP_OFFSET": "int"}
NOISE_TYPE_CHOICES = frozenset({0, 1, 2, 3, 4, 5, 6, 10, 11})
LOOP_OFFSET_CHOICES = frozenset(
    {10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 200, 210, 300, 400, 410})

RAW_SOURCE_SHA256 = "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274"
RAW_SOURCE_BYTES = 18131
_BASE_ANCHOR = "    vec2 lf = vec2(1.0);"
_BASE_HOIST = "    vec2 lf = vec2(1.0); float base = 0.0;"
_BASE_DECLARATIONS = (
    "    float base = map(75.0, 1.0, 100.0, 40.0, 1.0);",
    "    float base = map(75.0, 1.0, 100.0, 6.0, 0.5);",
    "    float base = map(75.0, 1.0, 100.0, 20.0, 3.0);",
)
TRANSFORMED_SOURCE_SHA256 = "4dc363cb0ab0fdff4e1ca1cf8d96f1f617fb44c78de52cd7b652d031408c512a"
TRANSFORMED_SOURCE_BYTES = 18131
NORMALIZED_SOURCE_SHA256 = "3c1aae1409269390e11e78c8cba7f3be189ea02674c90cc76560b99afdde175b"
NORMALIZED_SOURCE_BYTES = 17302
PRE_RUNTIME_FUNCTIONS_SHA256 = "21eba2d2d45570e78b3343e677045c5657079e3991c95bdc05ad4d1bd76dec69"
PRE_RUNTIME_WHOLE_SHA256 = "cda8a5f8a11fa3977e695f8079afe6386bbc20f583088a336fd6fa735c9a49af"
POST_RUNTIME_FUNCTIONS_SHA256 = "386946aa9af99af94e1df9f2d86bbf743b0fb95b44a6edb48e7ebad152bf3d5f"
POST_RUNTIME_WHOLE_SHA256 = "be33d87310c50bd560bdbc01c13318f66503dfa3e11d42c2b00f74d9595f368d"


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _whole(program: object) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def transform_source(source: str, program_key: str = KEY) -> str:
    """Apply the one authenticated, line-preserving dynamic-define transform."""
    if program_key != KEY:
        raise _fail("program key mismatch")
    raw = source.encode("utf-8")
    if len(raw) != RAW_SOURCE_BYTES or hashlib.sha256(raw).hexdigest() != RAW_SOURCE_SHA256:
        raise _fail("source hash mismatch")
    if source.count(_BASE_ANCHOR) != 1:
        raise _fail("base hoist anchor census mismatch")
    if any(source.count(item) != 1 for item in _BASE_DECLARATIONS):
        raise _fail("base declaration census mismatch")
    transformed = source.replace(_BASE_ANCHOR, _BASE_HOIST, 1)
    for declaration in _BASE_DECLARATIONS:
        transformed = transformed.replace(declaration, declaration.replace("float base = ", "base = "), 1)
    encoded = transformed.encode("utf-8")
    if (len(encoded) != TRANSFORMED_SOURCE_BYTES
            or hashlib.sha256(encoded).hexdigest() != TRANSFORMED_SOURCE_SHA256):
        raise _fail("transformed source fingerprint mismatch")
    if len(source.splitlines()) != len(transformed.splitlines()):
        raise _fail("transform changed source line count")
    return transformed


def is_dynamic_program(program: object) -> bool:
    return (getattr(program, "key", None) == KEY
            and tuple((item.name, item.kind, item.canonical_value)
                      for item in getattr(program, "preprocessor_defines", ()))
            == (("LOOP_OFFSET", "str", "int"), ("NOISE_TYPE", "str", "int")))


def authenticate_source(program: object, source_hash: str | None) -> None:
    """Check the complete dynamic source identity before carrier proofs run."""
    if not is_dynamic_program(program):
        raise _fail("dynamic Noise program identity mismatch")
    raw = program.raw_source.encode("utf-8")
    if (source_hash != RAW_SOURCE_SHA256 or len(raw) != RAW_SOURCE_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SOURCE_SHA256
            or len(program.source.encode("utf-8")) != NORMALIZED_SOURCE_BYTES
            or hashlib.sha256(program.source.encode("utf-8")).hexdigest()
            != NORMALIZED_SOURCE_SHA256
            or len(program.functions) != 35
            or len(program.declarations) != 17):
        raise _fail("dynamic source or interface fingerprint mismatch")


def authenticate_runtime_loop(program: object, source_hash: str | None,
                              profile: str | None):
    from .runtime_loop_bound_profile import (
        RuntimeLoopBoundContract, RuntimeScalarBoundSeed,
        validate_runtime_loop_contract)

    if not is_dynamic_program(program):
        return None
    if profile != "runtime-loop-bound-v1":
        raise _fail("exact runtime-loop-bound profile required")
    authenticate_source(program, source_hash)
    if ((_sha(program.functions), _whole(program)) not in {
            (PRE_RUNTIME_FUNCTIONS_SHA256, PRE_RUNTIME_WHOLE_SHA256),
            (POST_RUNTIME_FUNCTIONS_SHA256, POST_RUNTIME_WHOLE_SHA256)}):
        raise _fail("dynamic typed tree fingerprint mismatch")
    octaves = next((item.symbol for item in program.declarations
                    if item.symbol.name == "octaves"), None)
    helper = next((item for item in program.functions if item.name == "multires"), None)
    if octaves is None or helper is None or len(helper.parameters) != 5:
        raise _fail("octaves runtime-loop identity mismatch")
    parameter = helper.parameters[2]
    if parameter.name != "oct" or parameter.type.display() != "int":
        raise _fail("octaves runtime-loop parameter mismatch")
    seed = RuntimeScalarBoundSeed(parameter.id, 8,
                                  "runtime-metadata-uniform-direct-parameter",
                                  parameter)
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        KEY, seed, "integer-range", "octaves", 1, 8, 2,
        f"{KEY} octaves must be in [1,8]"))


def authenticate_scalar_xor(program: object, source_hash: str | None,
                            profile: str | None):
    from .scalar_uint_xor_profile import _collect

    if not is_dynamic_program(program):
        return None
    if profile != "scalar-uint-xor-v1":
        raise _fail("exact scalar uint XOR profile required")
    authenticate_source(program, source_hash)
    if (_sha(program.functions) != POST_RUNTIME_FUNCTIONS_SHA256
            or _whole(program) != POST_RUNTIME_WHOLE_SHA256):
        raise _fail("post-runtime dynamic typed tree fingerprint mismatch")
    xors, parents, owners, _ = _collect(program)
    if len(xors) != 3 or len({id(item) for item in xors}) != 3:
        raise _fail("scalar uint XOR census mismatch")
    if any(item.type.display() != "uint" or len(item.children) != 2
           or any(child.type.display() != "uint" for child in item.children)
           for item in xors):
        raise _fail("scalar uint XOR type mismatch")
    return tuple(xors)


def authenticate_noise_ingress(program: object, source_hash: str | None,
                               profile: str | None):
    from .scalar_uint_xor_profile import _walk_statement

    xors = authenticate_scalar_xor(program, source_hash, profile)
    if xors is None:
        return None
    located = []
    for function in program.functions:
        for statement in function.body:
            for value, _ in _walk_statement(statement):
                if value.kind == "builtin" and value.callee == "floatBitsToUint":
                    located.append(value)
    if len(located) != 1:
        raise _fail("float-bit ingress census mismatch")
    return tuple(located)


def dynamic_frame_contract(program: object):
    from .mutable_global_frame_profile import FrameContract, FrameField

    if not is_dynamic_program(program):
        raise _fail("dynamic Noise frame identity mismatch")
    field = FrameField(17, "globalCoord", "vec2", "glsl::Vec2", 2,
                       "per-lane-f32", "new Float32Array([0, 0])",
                       "float32-array")
    return FrameContract("Frame", "frame", "pixel", True, "const Frame& frame",
                         "const Frame&", 2, "main", (field,))


def authenticate_frame(program: object, source_hash: str | None,
                       profile: str | None):
    if not is_dynamic_program(program):
        return None
    if profile != "mutable-global-frame-noise-v1":
        raise _fail("exact mutable-global frame profile required")
    authenticate_source(program, source_hash)
    fields = tuple(item for item in program.declarations
                   if item.symbol.name == "globalCoord"
                   and item.symbol.storage == "global"
                   and item.type.display() == "vec2")
    if len(fields) != 1 or not fields[0].symbol.writable:
        raise _fail("globalCoord frame census mismatch")
    return fields


__all__ = [
    "DYNAMIC_DEFINES", "KEY", "LOOP_OFFSET_CHOICES", "NOISE_TYPE_CHOICES",
    "PROFILE", "RAW_SOURCE_BYTES", "RAW_SOURCE_SHA256",
    "TRANSFORMED_SOURCE_BYTES", "TRANSFORMED_SOURCE_SHA256", "transform_source",
]
