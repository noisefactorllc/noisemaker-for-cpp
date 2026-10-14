"""Exact current CPU Shape Number-division carrier for positiveModulo."""
from __future__ import annotations

import hashlib
from .mutable_global_frame_profile import (
    SHAPE_KEY, SHAPE_PROFILE, _sha, _whole,
    authenticate_mutable_global_frame,
)

SOURCE_SHA = 'd917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f'
WHOLE_SHA = 'ce26121154ee73ca20ea4ab0c0465e7e3ca0a98d3dc358ac49bcff88f3b8bf86'
FUNCTION_SHA = '024841ccb52181d6eaf95b14189f51a008cc2587e76ce5da94b2b925fb5570d8'
DEFINES = (('LOOP_A_OFFSET', 'str', 'int'), ('LOOP_B_OFFSET', 'str', 'int'))


def authenticate_shape_positive_modulo(program, source_hash):
    if program.key != SHAPE_KEY:
        return None
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != DEFINES:
        return None
    if (source_hash != SOURCE_SHA
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != SOURCE_SHA
            or _whole(program) != WHOLE_SHA):
        raise ValueError('Shape Number positiveModulo source or typed tree mismatch')
    authenticate_mutable_global_frame(program, source_hash, SHAPE_PROFILE)
    matches = tuple(function for function in program.functions
                    if function.name == 'positiveModulo')
    if (len(matches) != 1 or matches[0].id != 115
            or matches[0].return_type.display() != 'int'
            or tuple((p.id, p.name, p.type.display(), p.direction)
                     for p in matches[0].parameters)
            != ((23, 'a', 'int', 'in'), (24, 'b', 'int', 'in'))
            or len(matches[0].body) != 3
            or tuple(item.kind for item in matches[0].body)
            != ('decl', 'if', 'return')
            or _sha(matches[0]) != FUNCTION_SHA):
        raise ValueError('Shape Number positiveModulo function identity mismatch')
    return matches[0]
