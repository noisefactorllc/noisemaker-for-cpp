"""Prove the exact Physical agent's declared inputTex is never read."""
from __future__ import annotations

import dataclasses
import hashlib

from .typed_ir import TypedExpression, TypedProgram

KEY = "points/physical:agent"
RAW_SHA256 = "a144cacbadeca15a78a83dac987bfd25164bd7904a2e9f0ea22e8b1bf22e3614"


def omitted_physical_samplers(program: TypedProgram) -> frozenset[str]:
    """Return only the source-locked sampler that has no typed references.

    The CPU pass does not bind inputTex. Its shader declares the name for
    chainability, but only the separate passthrough program samples it.
    Preserve the full IR for existing source and arithmetic proof checks.
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

    def audit(value):
        if isinstance(value, TypedExpression):
            if value.symbol_id == target or (value.symbol is not None and value.symbol.id == target):
                raise ValueError("Physical inputTex has a typed reference")
        if dataclasses.is_dataclass(value):
            for field in dataclasses.fields(value):
                audit(getattr(value, field.name))
        elif isinstance(value, (tuple, list)):
            for child in value:
                audit(child)

    audit(program.functions)
    for declaration in program.declarations:
        audit(declaration.initializer)
    return frozenset({"inputTex"})
