"""Generic, hash-locked source hoist for dynamic-define runtime lowering.

When ``preprocess.py`` lowers a ``#if``/``#elif``/``#else`` chain gated on a
*dynamic* (runtime-uniform) define into a real GLSL ``if``/``else if``/
``else``, any local variable the chain DECLARES inside one branch and the
surrounding code REFERENCES after the chain closes breaks: each branch is now
its own ``{ }`` scope, so the declaration does not escape it. This is exactly
the hazard ``noise_runtime_define_profile.py`` hand-fixed for ``synth/noise``'s
``base`` local (see that module's ``transform_source``). This module
generalizes the *same* fix -- hoist one bare declaration above the chain,
turn every one of its N branch-local declaring statements into a plain
assignment -- into a small, table-driven, hash-locked primitive that covers
every other program with the identical hazard shape.

Why this is semantics-preserving: every declaring statement here is a pure
initializer (``TYPE NAME = EXPR;``), never an accumulation (``NAME += ...``),
and the branches of one conditional chain are mutually exclusive. Whether the
authority's compiler statically drops the untaken branches (eliminating every
declaration but one) or this port's runtime `if` skips them dynamically,
exactly one assignment reaches any later read of the name either way -- the
hoist changes nothing about which value ends up there.

Every table entry is locked to the exact pinned raw corpus source (hash and
byte count) and to an exact expected occurrence count for both the
conditional region it targets and the declaring statement inside it; any
drift in the corpus source (a different upstream revision, a hand-edit) fails
closed instead of silently mis-transforming something that moved.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

_DIRECTIVE_OPEN = ("#if", "#ifdef", "#ifndef")


class HoistError(ValueError):
    """A pinned source or occurrence-count assumption no longer holds."""


@dataclass(frozen=True)
class _Hoist:
    decl_type: str
    decl_name: str
    # The conditional chain whose declaring statements get rewritten to plain
    # assignments. `region_if_occurrence` is 0-based: which match of
    # `region_if_text` (by exact stripped line text) starts this program's
    # chain, since the same condition text can legitimately recur elsewhere
    # in the same file for an unrelated chain.
    region_if_text: str
    region_if_occurrence: int
    expected_branch_count: int
    # Where the hoisted bare declaration is inserted: immediately before or
    # after the `insert_anchor_occurrence`-th (0-based) line whose stripped
    # text equals `insert_anchor_text`. Defaults to the region's own `#if`
    # line (i.e. hoist immediately above the chain) when left as None -- most
    # cases want exactly that; a few (a nested chain, or several sibling
    # chains sharing one hoist) anchor on an earlier, unambiguous code line
    # instead so the hoisted declaration lands above every chain that needs
    # it without depending on a directive line that recurs verbatim.
    insert_anchor_text: str | None = None
    insert_anchor_occurrence: int = 0
    insert_after: bool = False


@dataclass(frozen=True)
class _Profile:
    raw_sha256: str
    raw_bytes: int
    hoists: tuple[_Hoist, ...]


# classicNoisedeck/cellRefract:cellRefract -- SHAPE == 1 special-cases the
# diamond metric with its own `dist`; every other shape falls through to
# shapeDistance(). Read outside the chain at `d = smin(d, dist, ...)`.
_CELL_REFRACT = _Profile(
    raw_sha256="aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70",
    raw_bytes=13719,
    hoists=(_Hoist("float", "dist", "#if SHAPE == 1", 0, 2),),
)

# classicNoisedeck/kaleido:kaleido -- DIRECTION selects the rotation sign fed
# into the sides repeat below the chain.
_KALEIDO = _Profile(
    raw_sha256="18a201e5189430578a2cd1d03cea911957a08f3bd7f3e74e78b97eb9f946ed52",
    raw_bytes=27570,
    hoists=(_Hoist("float", "dir", "#if DIRECTION == 1", 0, 3),),
)

# classicNoisedeck/noise:noise -- two independent hazards. `nominalFreq`
# (multires(), NOISE_TYPE-gated) is read as `nominalFreq.x` a few statements
# below its chain; `#if NOISE_TYPE == 11` recurs 4 times in this file (an
# unrelated one in generate_octave-adjacent code, and the two `main()` chains
# that assign already-hoisted `freq`/`lf` and need no hoist of their own), so
# the occurrence index picks out multires()'s chain specifically. `baseLoop`
# is nested inside `#if LOOP_OFFSET == 300` and read at
# `vec2 nominalFreq = vec2(baseLoop)` a few lines below its own chain (a
# second, block-scoped `nominalFreq` local to that `{ }`, distinct from
# multires()'s -- GLSL/the typed IR scope these independently per function
# and per brace block, so the two same-named locals never collide).
_NOISE = _Profile(
    raw_sha256="8629349c5cc4d44d7b4b7c1f0b3f27fe4fe82793461f26544c80a4fb5076d138",
    raw_bytes=31258,
    hoists=(
        _Hoist("vec2", "nominalFreq", "#if NOISE_TYPE == 11", 1, 3),
        _Hoist("float", "baseLoop", "#if NOISE_TYPE == 11", 3, 3),
    ),
)

# filter/halftone:halftone -- `ink` is PATTERN-gated (dot vs. line/other) and
# read two statements later by the shared `tonemap2(1.0 - ink, ...)` call.
_HALFTONE = _Profile(
    raw_sha256="063ddb13f5fffc6f957d4be0a60b0408ff706d6111fd4e3ba52582f7507c7ad7",
    raw_bytes=8440,
    hoists=(_Hoist("float", "ink", "#if PATTERN == 0", 0, 2),),
)

# filter/lowPoly:lowPoly -- three hazards. `nearestCell` is declared in the
# SECOND of four `#if LP_BORDER > 0` chains in this file (the first gates a
# whole function definition at global scope -- glslcpp's dynamic-define
# preprocessor already keeps that one intact via its own `include_all`
# handling, no hoist involved -- the third only ASSIGNS `nearestCell` inside
# the neighbor search loop, no declaration; the fourth is unrelated). It is
# read well below, in the border-drawing block. `modeResult`/`borderMask`
# share one `#if (LP_BORDER > 0) || (LP_LIGHT > 0)` chain (no `#elif`/`#else`
# -- one branch, still hazardous since both names are read after the chain
# closes) and are independent hoists sharing that same region.
_LOW_POLY = _Profile(
    raw_sha256="2f6a184ef4d372ebf811eaa59420bbce66fa25702e23a278557521679ce7b2f5",
    raw_bytes=8719,
    hoists=(
        _Hoist("ivec2", "nearestCell", "#if LP_BORDER > 0", 1, 1),
        _Hoist("vec3", "modeResult", "#if (LP_BORDER > 0) || (LP_LIGHT > 0)", 0, 1),
        _Hoist("float", "borderMask", "#if (LP_BORDER > 0) || (LP_LIGHT > 0)", 0, 1),
    ),
)

# filter/oilPaint:oilFlatten -- MODE selects the Kuwahara radius; read two
# statements later by `fr = clamp(radius, ...)`.
_OIL_FLATTEN = _Profile(
    raw_sha256="f2f512b35b846d8a15362739a843c162199b7c53d95251918576726b1b094690",
    raw_bytes=7321,
    hoists=(_Hoist("float", "radius", "#if MODE == 0", 0, 2),),
)

# filter/texture:texture -- two independent, sibling `#if MODE == 4` chains
# (paper/stucco frequency, then paper/stucco shading gain); each read a few
# statements below its own chain.
_TEXTURE = _Profile(
    raw_sha256="8e95251ef9a7789b1de4e51718ab3bebd9fc6d20db8acd0969191e288ec7454c",
    raw_bytes=14344,
    hoists=(
        _Hoist("float", "freq_scale", "#if MODE == 4", 0, 2),
        _Hoist("float", "gain", "#if MODE == 4", 1, 2),
    ),
)

# filter/wind:wind -- four sibling `#if METHOD == 1` (or `== 1`/`== 2`/else)
# chains inside the same per-step loop. `decayRate`/`taperStart` are both
# read by the `endTaper`/`weight` statements right after the second chain
# closes, so both hoist above the first chain (their shared, unambiguous
# predecessor statement); `densityRate`/`methodGain` are both read by the
# `density`/`blendAmount` statements after the fourth chain, so both hoist
# above the third chain's predecessor statement.
_WIND = _Profile(
    raw_sha256="68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22",
    raw_bytes=3520,
    hoists=(
        _Hoist("float", "decayRate", "#if METHOD == 1", 0, 3,
               insert_anchor_text="float alongRun = distancePx / max(reach, 1.0);",
               insert_after=True),
        _Hoist("float", "taperStart", "#if METHOD == 1", 1, 2,
               insert_anchor_text="float alongRun = distancePx / max(reach, 1.0);",
               insert_after=True),
        _Hoist("float", "densityRate", "#if METHOD == 1", 2, 2,
               insert_anchor_text="vec3 integrated = accumColor / max(accumWeight, 0.00001);",
               insert_after=True),
        _Hoist("float", "methodGain", "#if METHOD == 1", 3, 2,
               insert_anchor_text="vec3 integrated = accumColor / max(accumWeight, 0.00001);",
               insert_after=True),
    ),
)

PROFILES: dict[str, _Profile] = {
    "classicNoisedeck/cellRefract:cellRefract": _CELL_REFRACT,
    "classicNoisedeck/kaleido:kaleido": _KALEIDO,
    "classicNoisedeck/noise:noise": _NOISE,
    "filter/halftone:halftone": _HALFTONE,
    "filter/lowPoly:lowPoly": _LOW_POLY,
    "filter/oilPaint:oilFlatten": _OIL_FLATTEN,
    "filter/texture:texture": _TEXTURE,
    "filter/wind:wind": _WIND,
}


def is_hoisted_program(program_key: str) -> bool:
    return program_key in PROFILES


def _nth_index(lines: list[str], text: str, occurrence: int) -> int:
    found = 0
    for index, line in enumerate(lines):
        if line.strip() == text:
            if found == occurrence:
                return index
            found += 1
    raise HoistError(f"occurrence {occurrence} of {text!r} not found "
                      f"(only {found} match(es))")


def _matching_endif(lines: list[str], if_index: int) -> int:
    depth = 0
    for index in range(if_index, len(lines)):
        head = lines[index].strip()
        if any(head.startswith(directive) for directive in _DIRECTIVE_OPEN):
            depth += 1
        elif head == "#endif":
            depth -= 1
            if depth == 0:
                return index
    raise HoistError(f"no matching #endif for chain opened at line {if_index + 1}")


def transform_source(source: str, program_key: str) -> str:
    """Apply every authenticated hoist for `program_key`, or return `source`
    unchanged if it carries none."""
    profile = PROFILES.get(program_key)
    if profile is None:
        return source
    raw = source.encode("utf-8")
    if len(raw) != profile.raw_bytes or hashlib.sha256(raw).hexdigest() != profile.raw_sha256:
        raise HoistError(f"{program_key}: pinned source hash mismatch for dynamic-define hoist")
    lines = source.split("\n")
    for hoist in profile.hoists:
        region_start = _nth_index(lines, hoist.region_if_text, hoist.region_if_occurrence)
        region_end = _matching_endif(lines, region_start)
        pattern = f"{hoist.decl_type} {hoist.decl_name} ="
        replacement = f"{hoist.decl_name} ="
        count = sum(lines[index].count(pattern) for index in range(region_start, region_end + 1))
        if count != hoist.expected_branch_count:
            raise HoistError(
                f"{program_key}: {hoist.decl_name}: expected {hoist.expected_branch_count} "
                f"declaring occurrence(s) in the {hoist.region_if_text!r} chain, found {count}")
        for index in range(region_start, region_end + 1):
            lines[index] = lines[index].replace(pattern, replacement)
        anchor_text = hoist.insert_anchor_text or hoist.region_if_text
        anchor_occurrence = (0 if hoist.insert_anchor_text is not None
                              else hoist.region_if_occurrence)
        anchor_index = _nth_index(lines, anchor_text, anchor_occurrence)
        insert_index = anchor_index + 1 if hoist.insert_after else anchor_index
        indent = lines[anchor_index][:len(lines[anchor_index]) - len(lines[anchor_index].lstrip())]
        lines.insert(insert_index, f"{indent}{hoist.decl_type} {hoist.decl_name};")
    return "\n".join(lines)


__all__ = ["HoistError", "PROFILES", "is_hoisted_program", "transform_source"]
