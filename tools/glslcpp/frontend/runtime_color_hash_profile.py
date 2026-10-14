"""Source-bound dynamic color and lattice-hash sites for two exact programs."""

from __future__ import annotations

from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram
from . import noise_frontend_profile as noise
from . import moodscape_dynamic_profile as moodscape


class Sites(NamedTuple):
    lane_indexes: tuple[TypedExpression, ...]
    float_bits: tuple[TypedExpression, ...]
    scalar_xors: tuple[TypedExpression, ...]


NOISE_INDEX_SPANS = (
    "668:13-668:22", "669:13-669:20", "669:23-669:32",
    "671:13-671:20", "671:35-671:44", "680:13-680:20",
    "681:13-681:22", "681:25-681:32", "683:13-683:22",
    "683:30-683:37",
)
NOISE_BITS_SPANS = ("126:21-126:43",)
NOISE_XOR_SPANS = (
    "129:10-129:46", "130:10-130:46", "131:10-131:47",
)


def authenticate(program: TypedProgram, source_hash: str | None,
                 profile: str | None) -> Sites:
    """Return only the candidate-owned sites in an authenticated projection."""
    if program.key == noise.KEY and profile == noise.PROFILE:
        noise.authenticate_noise_projection(program, source_hash, profile)
        values = noise._expressions(program)
        indexes = tuple(x for x in values if x.kind == "index")
        bits = tuple(x for x in values if x.kind == "builtin"
                     and x.callee == "floatBitsToUint")
        xors = tuple(x for x in values if x.kind == "binary"
                     and x.operator == "^" and x.type.display() == "uint")
        if (tuple(noise._span(x) for x in indexes) != NOISE_INDEX_SPANS
                or tuple(noise._span(x) for x in bits) != NOISE_BITS_SPANS
                or tuple(noise._span(x) for x in xors) != NOISE_XOR_SPANS):
            raise ValueError("Classic Noise dynamic exceptional-site census mismatch")
        sites = Sites(indexes, bits, xors)
    elif program.key == moodscape.KEY and profile == moodscape.PROFILE:
        sites = Sites(*moodscape.authenticate_projection(
            program, source_hash, profile))
    else:
        raise ValueError("dynamic color/hash key or profile mismatch")
    for x in sites.lane_indexes:
        if (x.type.display() != "float" or len(x.children) != 2
                or x.children[0].type.display() != "vec3"
                or x.children[1].type.display() != "int"):
            raise ValueError("dynamic color lane-index type mismatch")
    for x in sites.float_bits:
        if (x.type.display() != "uint" or len(x.children) != 1
                or x.children[0].type.display() != "float"):
            raise ValueError("dynamic lattice bit-ingress type mismatch")
    for x in sites.scalar_xors:
        if (x.type.display() != "uint" or len(x.children) != 2
                or any(c.type.display() != "uint" for c in x.children)):
            raise ValueError("dynamic lattice XOR type mismatch")
    nodes = (*sites.lane_indexes, *sites.float_bits, *sites.scalar_xors)
    if len({id(x) for x in nodes}) != len(nodes):
        raise ValueError("dynamic color/hash site identity collision")
    return sites
