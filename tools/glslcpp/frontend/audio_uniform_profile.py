"""Exact-source admission of scope/spectrum's two readonly audio samples."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .typed_ir import TypedDeclaration, TypedExpression, TypedProgram


# Shader e24c844f8dada85551ab084f41db8944fbc176c8; CPU 26d6f42b canonical
# factories 284/287. These exceptions do not admit other uniform arrays.
_LOCKS = {
    "synth/scope:scope": (
        "audioWaveform",
        "e5e4d09db8e884a41f1cc2ce908f438dc4cff9f2f22741c30877e3f9aae91b90",
        "6be09581b8fa0b96c838fe929f2b365fa69e161714a40344bc4fd25a9906e710",
        (25, 26)),
    "synth/spectrum:spectrum": (
        "audioSpectrum",
        "552157fb5fad42e56c767a38468e0b04095f5d93e1c6ede55044d5da76cb78fb",
        "d998a448cdc46c4a552d10aa35d4eff17c319ab671c38d3d0cd7f5db532901b1",
        (24, 25)),
}
KEYS = frozenset(_LOCKS)


@dataclass(frozen=True)
class AudioUniformProof:
    program: TypedProgram
    declaration: TypedDeclaration
    reads: tuple[TypedExpression, ...]


def _whole(program: TypedProgram) -> str:
    value = (program.key, program.source, program.raw_source,
             program.declarations, program.functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.counted_loop_proof,
             program.preprocessor_defines)
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _expressions(value):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statements(value):
    for expression in value.expressions:
        yield from _expressions(expression)
    for child in value.children:
        yield from _statements(child)


def authenticate_audio_uniform(program: TypedProgram,
                               source_hash: str | None) -> AudioUniformProof | None:
    lock = _LOCKS.get(program.key)
    if lock is None:
        return None
    name, raw_hash, whole_hash, lines = lock
    if (source_hash != raw_hash
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != raw_hash
            or _whole(program) != whole_hash or program.body_status != "analyzed"):
        raise ValueError("audio-uniform128: source or typed program mismatch")
    if any(getattr(program, field, None) is not None for field in (
            "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
            "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof")):
        raise ValueError("audio-uniform128: unrelated proof carrier")
    expected = (("resolution", "vec2", "uniform", False),
                ("tileOffset", "vec2", "uniform", False),
                ("fullResolution", "vec2", "uniform", False),
                (name, "float[128]", "uniform", False),
                ("lineColor", "vec3", "uniform", False),
                ("lineThickness", "float", "uniform", False),
                ("gain", "float", "uniform", False),
                ("fragColor", "vec4", "output", True))
    actual = tuple((d.symbol.name, d.type.display(), d.symbol.storage,
                    d.symbol.writable) for d in program.declarations)
    if actual != expected:
        raise ValueError("audio-uniform128: declaration ABI mismatch")
    declaration = program.declarations[3]
    nodes = tuple(n for f in program.functions for s in f.body
                  for n in _statements(s))
    reads = tuple(n for n in nodes if n.kind == "index")
    if len(reads) != 2:
        raise ValueError("audio-uniform128: exact two-read census required")
    for read, line, index_name in zip(reads, lines, ("i0", "i1")):
        if (len(read.children) != 2 or read.type.display() != "float"
                or read.span.start_line != line
                or read.span.start_column != 16 or read.span.end_column != 33):
            raise ValueError("audio-uniform128: indexed read identity mismatch")
        base, index = read.children
        if (base.kind != "id" or base.symbol is not declaration.symbol
                or base.symbol_id != declaration.symbol.id
                or index.kind != "id" or index.symbol is None
                or index.symbol.name != index_name or index.type.display() != "int"):
            raise ValueError("audio-uniform128: indexed operand identity mismatch")
    references = tuple(n for n in nodes if n.symbol_id == declaration.symbol.id)
    if len(references) != 2 or any(
            reference is not read.children[0]
            for reference, read in zip(references, reads)):
        raise ValueError("audio-uniform128: unexpected whole-array use")
    return AudioUniformProof(program, declaration, reads)
