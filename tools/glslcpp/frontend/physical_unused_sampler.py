"""Prove which samplers of the exact Physical agent its CPU pass leaves unbound."""
from __future__ import annotations

import dataclasses
import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "points/physical:agent"
RAW_SHA256 = "06f3afef8efeaba67f1babf129ee107b06e860ec8458e270ce404fc770b46615"


def omitted_physical_samplers(program: TypedProgram) -> frozenset[str]:
    """Return only the source-locked samplers that the CPU pass does not bind.

    The pinned CPU pass binds inputTex, and the shader reads it in
    spawnColor() to restore an agent's spawn color. Thus no declared sampler
    is omitted. The source lock and the reference audit fail closed if a
    later authority stops reading inputTex again.
    """
    if program.key != KEY:
        return frozenset()
    if hashlib.sha256(program.raw_source.encode()).hexdigest() != RAW_SHA256:
        raise ValueError("Physical unused-sampler source identity changed")
    targets = [d for d in program.declarations if d.symbol.name == "inputTex"]
    if (len(targets) != 1 or targets[0].type.display() != "sampler2D"
            or targets[0].symbol.storage != "uniform" or targets[0].initializer is not None
            or program.resources.uniforms.count("inputTex") != 1
            or program.resources.samplers.count("inputTex") != 1):
        raise ValueError("Physical unused-sampler declaration changed")
    target = targets[0].symbol.id
    references = 0

    def audit(value):
        nonlocal references
        if isinstance(value, TypedExpression):
            if value.symbol_id == target or (value.symbol is not None and value.symbol.id == target):
                references += 1
        if dataclasses.is_dataclass(value):
            for field in dataclasses.fields(value):
                audit(getattr(value, field.name))
        elif isinstance(value, (tuple, list)):
            for child in value:
                audit(child)

    audit(program.functions)
    for declaration in program.declarations:
        audit(declaration.initializer)
    if references == 0:
        raise ValueError("Physical inputTex has no typed reference")
    return frozenset()
