"""Exact identity profile for ``synth3d/fractal3d:precompute``'s two ``log`` sites.

``synth3d/fractal3d:precompute`` reached its first authentic non-counted
frontier at ``93:24: unsupported builtin log`` after the parameter-bound
counted-for seed landed (``loop_proof``'s parameter-uniform entry): both
distance estimators finish with ``float dist = 0.5 * log(r) * r / dr;``.
``log`` is analyzer-known (``body_semantic``'s ``unary_float`` overload) and
the authority routes it through ``Math.log``
(``src/csl/glsl-runtime.js``: ``log: unary(Math.log)``), but the shared
validator ``_BUILTINS`` and emitter arms do not carry it generically --
exactly the Mandelbrot log-admission shape
(``log_admission_profile.py``), so this module freezes the two sites the
same way: a frontend record handing both authorities the exact live nodes,
admitted by node identity, never widening the capability vocabulary.

The two sites (scalar ``float -> float``, arity one, argument the local
``r`` read by id, every parent a ``binary`` node, in program order):

* ``juliaBulb 93:24-93:30`` (normalized) -- ``log(r)`` in the Julia
  Mandelbulb distance estimate;
* ``mandelbulb 55:24-55:30`` (normalized) -- ``log(r)`` in the Mandelbulb
  distance estimate.

Lowering contract: ``glsl::log`` (``noisemaker::fdlibm::log``, V8's own
``ieee754::log``), the same lowering Mandelbrot and Newton already use --
``Math.log`` is the authority and ``std::log`` measurably diverges in the
last bit on a large fraction of doubles. Both sites feed ``r = length(z)``
of an iterated fractal point (non-negative; ``0.0`` at a degenerate first
read only when the loop never runs, where the authority returns ``-inf``
and the port lowers the identical expression tree, so the domain shape is
the authority's own, not a new one).

The program is also the ``parameter-uniform-argument-bound`` counted-for
carrier (``loop_proof``'s frozen ``synth3d/fractal3d:precompute`` entry:
four carrier loops bounded by ``int maxIter``, uniform ``iterations``,
authority maximum 20). This module's fingerprints are computed over the
proof-CLEARED tree so they stay stable across proof attachment; the
seed-attached summary is frozen alongside as a closure lock and the
parameter-uniform metadata binding stays ``loop_proof``'s own business
(the corpus ratchet binds it before any profile runs).
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .loop_proof import (
    clear_counted_loop_proofs,
    summarize_counted_loop_proofs,
)
from .typed_ir import TypedExpression, TypedFunction, TypedProgram


KEY = "synth3d/fractal3d:precompute"
PROFILE = "fractal3d-log-admission-v1"
KEYS: tuple[str, ...] = (KEY,)
PROFILES = {KEY: PROFILE}
FRACTAL3D_LOG_KEYS = frozenset(KEYS)

# The complete allowed field set for the slice row -- an ALLOWLIST enforced
# by the validator's `set(item) != expected` comparison.
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    KEY: frozenset({"defines", "fractal3d_log_profile", "program_key"}),
}

RAW_BYTES = 6912
RAW_SHA256 = "8ab3dfe63e16d4406deee719c1f822d405c712bae21bd1348ae5b75b79a14d41"
NORMALIZED_BYTES = 6409
NORMALIZED_SHA256 = "bfc4b9e886fa4dc5d642abfd6457c643a47287f2095ccac0f99759ad5ff1d5a6"
FUNCTIONS_SHA256 = "a6c435a3887543d3aa3dc4e3560369a877f1a7b37083197b8e8324da26991a3a"
WHOLE_SHA256 = "e8266219a128492532d69183fd0b55ed862ea8eb1a625021ef8fa13fe4dc990e"
INTERFACE_SHA256 = "47b3ed25f3ccea8f7e58ad566c7a2df79cdac82674aa728985d1dae7bfacf9cb"

# The seed-attached counted-for summary: four carrier loops (one per
# fractal carrier), all proved, depth 1, product 20, entrypoint charge
# 4*20, acyclic.
COUNTED_LOOP_SUMMARY = (4, 0, 1, 20, 80, True)

FUNCTION_COUNT = 7
FUNCTION_INVENTORY = (
    (37, "boxFold", "vec3", ((24, "z", "vec3"), (25, "foldingLimit", "float"))),
    (38, "computeFractal", "vec3", ((35, "p", "vec3"), (36, "juliaC", "vec3"))),
    (39, "juliaBulb", "vec3",
     ((19, "pos", "vec3"), (20, "c", "vec3"), (21, "n", "float"),
      (22, "maxIter", "int"), (23, "bail", "float"))),
    (40, "juliaCube", "vec3",
     ((30, "pos", "vec3"), (31, "c", "vec3"), (32, "scale", "float"),
      (33, "maxIter", "int"), (34, "bail", "float"))),
    (41, "main", "void", ()),
    (42, "mandelbulb", "vec3",
     ((15, "pos", "vec3"), (16, "n", "float"), (17, "maxIter", "int"),
      (18, "bail", "float"))),
    (43, "mandelcube", "vec3",
     ((26, "pos", "vec3"), (27, "scale", "float"), (28, "maxIter", "int"),
      (29, "bail", "float"))),
)

RESOURCES = (
    ("volumeSize", "noiseType", "power", "iterations", "bailout", "juliaX",
     "juliaY", "juliaZ", "colorMode", "tileOffset", "renderScale"),
    (),
    ("fragColor", "geoOut"),
    False,
    False,
)

# The transcendental family boundary: log is the only non-approved
# transcendental this program uses (log2/exp/exp2/tanh are all zero) and
# pow, already approved, carries exactly the four frozen carrier sites.
_ZERO_FAMILY = ("log2", "exp", "exp2", "tanh")
POW_SITES = (
    ("juliaBulb", "77:14-77:29", 2),
    ("juliaBulb", "79:20-79:29", 2),
    ("mandelbulb", "39:14-39:29", 2),
    ("mandelbulb", "41:20-41:29", 2),
)

LOG_SITE_COUNT = 2
# (owner_id, owner_name, node span, argument span, statement span,
#  parent kind, (call sha, argument sha, statement sha))
LOG_SITES = (
    (39, "juliaBulb", "93:24-93:30", "93:28-93:29", "93:5-93:40", "binary",
     ("f9c8a6dc4d06b349bb42fac714f941707ca408d7fc5531857f496a1f75ec11b7",
      "46b25d6ad0bc19233b8da832b60b2c89c4bb59b92290a46c14a9a6e124fbba6a",
      "996a06f7917bb773840fb7d0f8761019fef580abf69581be73092375cb164711")),
    (42, "mandelbulb", "55:24-55:30", "55:28-55:29", "55:5-55:40", "binary",
     ("455eb003b04ff0663afded2ae92a969eb15df5743ccc0ad3a6371857e949a455",
      "d59559d021ffe4280c6274027fab2d52894084cc3ffa7fc44668806601aca3ce",
      "82fa0140890420d1eb332e3fbf41341243ea718f634f6f2edc7948ae9170cfb9")),
)
# Argument kind and type, result type per site -- the value tier the
# identity hashes alone would absorb.
LOG_SHAPE = (
    (39, "juliaBulb", "id", "float", "float", "binary", "93:24-93:30"),
    (42, "mandelbulb", "id", "float", "float", "binary", "55:24-55:30"),
)

# The two sites' two live nodes each and the two DISTINCT owner functions:
# 6 distinct objects, each consumed exactly once.
_CONSUMED_LEDGER = 6

_TOTAL_NODES = 670
_TOTAL_ASSIGNS = 35


class Fractal3dLogSite(NamedTuple):
    """One admitted ``log`` call, by live node identity."""

    record: tuple
    node: TypedExpression
    argument: TypedExpression
    owner: TypedFunction

    @property
    def owner_id(self) -> int:
        return self.record[0]

    @property
    def owner_name(self) -> str:
        return self.record[1]

    @property
    def span(self) -> str:
        return self.record[2]


class Fractal3dLogProof(NamedTuple):
    """The two exact live log nodes, plus the visitation ledger."""

    sites: tuple[Fractal3dLogSite, ...]
    consumed_objects: tuple[object, ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole_cleared(program: TypedProgram) -> str:
    """The whole-program fingerprint over the proof-cleared tree.

    Mirrors ``log_admission_profile._whole_cleared`` so attaching the
    parameter-bound seed never moves a coarse field.
    """
    cleared = clear_counted_loop_proofs(program.functions)
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        cleared, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        summarize_counted_loop_proofs(cleared), program.preprocessor_defines,
    ))


def _interface(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _profile_fail(profile: str, message: str) -> ValueError:
    return ValueError(f"{profile}: {message}")


def _walk_with_parent(value: TypedExpression, parent):
    yield value, parent
    for child in value.children:
        yield from _walk_with_parent(child, value)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_with_parent(expression, None)
    for child in value.children:
        yield from _walk_statement(child)


def _program_nodes(program: TypedProgram):
    """``(function, node, parent)`` for every expression node, global
    declaration initializers included."""
    for declaration in program.declarations:
        if declaration.initializer is None:
            continue
        for node, parent in _walk_with_parent(declaration.initializer, None):
            yield None, node, parent
    for function in program.functions:
        for statement in function.body:
            for node, parent in _walk_statement(statement):
                yield function, node, parent


def _site_walk(program: TypedProgram):
    """``(function, node, statement, parent)`` for every ``log`` builtin
    node, in deterministic program order."""
    for function in program.functions:
        def walk(value):
            for expression in value.expressions:
                for node, parent in _walk_with_parent(expression, None):
                    if node.kind == "builtin" and node.callee == "log":
                        yield function, node, value, parent
            for child in value.children:
                yield from walk(child)
        for statement in function.body:
            yield from walk(statement)


def _owner_record(function: TypedFunction | None) -> tuple[int, str]:
    if function is None:
        return (-1, "<global-initializer>")
    return (function.id, function.name)


def _node_census(program: TypedProgram) -> tuple[int, int]:
    total = 0
    assigns = 0
    for _, node, _ in _program_nodes(program):
        total += 1
        if node.kind == "assign":
            assigns += 1
    return total, assigns


def _builtin_census(program: TypedProgram, callee: str) -> tuple:
    found = []
    for function, node, _ in _program_nodes(program):
        if node.kind == "builtin" and node.callee == callee:
            owner_id, owner_name = _owner_record(function)
            found.append((owner_name, _span(node), len(node.children)))
    return tuple(found)


def _site_proofs(program: TypedProgram) -> tuple[Fractal3dLogSite, ...]:
    sites: list[Fractal3dLogSite] = []
    for function, node, statement, parent in _site_walk(program):
        argument = node.children[0]
        owner_id, owner_name = _owner_record(function)
        record = (owner_id, owner_name, _span(node), _span(argument),
                  _span(statement),
                  parent.kind if parent is not None else None,
                  (_sha(node), _sha(argument), _sha(statement)))
        sites.append(Fractal3dLogSite(record, node, argument, function))
    return tuple(sites)


def authenticate_fractal3d_log_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> Fractal3dLogProof | None:
    """Authenticate the frozen log identity profile and return the two
    exact live call nodes for ``program.key``.

    Returns ``None`` when ``program.key`` is not a carrier and no profile
    was supplied; supplying a profile for a non-carrier key is a hard
    failure that names the sole admitted sites.
    """
    if program.key != KEY:
        if profile is not None:
            raise _profile_fail(
                PROFILE,
                "program key is not an admitted fractal3d log admission "
                f"carrier; {KEY} 93:24 and 55:24 are the sole admitted "
                "log sites")
        return None
    if profile != PROFILE:
        raise _profile_fail(PROFILE, "exact profile carrier required")
    if source_hash != RAW_SHA256:
        raise _profile_fail(PROFILE, "exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(normalized) != NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != NORMALIZED_SHA256
            or _sha(clear_counted_loop_proofs(program.functions))
            != FUNCTIONS_SHA256
            or _whole_cleared(program) != WHOLE_SHA256
            or _interface(program) != INTERFACE_SHA256):
        raise _profile_fail(
            PROFILE,
            "source, function, whole-program, or interface lock mismatch")
    summary = program.counted_loop_proof
    if summary is None or (
            summary.loop_count, summary.unproved_loop_count,
            summary.max_effective_depth, summary.max_lexical_product,
            summary.entrypoint_charge, summary.call_graph_acyclic) \
            != COUNTED_LOOP_SUMMARY:
        raise _profile_fail(PROFILE, "counted-for closure summary mismatch")
    if len(program.functions) != FUNCTION_COUNT:
        raise _profile_fail(PROFILE, "function cardinality mismatch")
    inventory = tuple(
        (item.id, item.name, item.return_type.display(),
         tuple((parameter.id, parameter.name, parameter.type.display())
               for parameter in item.parameters))
        for item in program.functions)
    if inventory != FUNCTION_INVENTORY:
        raise _profile_fail(PROFILE, "typed function inventory mismatch")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != RESOURCES):
        raise _profile_fail(PROFILE, "resource profile mismatch")
    sites = _site_proofs(program)
    if len(sites) != LOG_SITE_COUNT:
        raise _profile_fail(PROFILE, "log site census mismatch")
    shape = tuple(
        (site.owner_id, site.owner_name, site.argument.kind,
         site.argument.type.display(), site.node.type.display(),
         site.record[5], site.span)
        for site in sites)
    if shape != LOG_SHAPE:
        raise _profile_fail(PROFILE, "log site shape mismatch")
    if tuple(site.record for site in sites) != LOG_SITES:
        raise _profile_fail(PROFILE, "log site identity mismatch")
    zero_family = tuple(
        sum(1 for _, node, _ in _program_nodes(program)
            if node.kind == "builtin" and node.callee == name)
        for name in _ZERO_FAMILY)
    if zero_family != (0, 0, 0, 0) or _builtin_census(program, "pow") \
            != POW_SITES:
        raise _profile_fail(PROFILE, "log-family census mismatch")
    total, assigns = _node_census(program)
    if total != _TOTAL_NODES or assigns != _TOTAL_ASSIGNS:
        raise _profile_fail(PROFILE, "whole-program node census mismatch")
    consumed = [
        *(item for site in sites for item in (site.node, site.argument)),
        *(site.owner for site in sites),
    ]
    identities = [id(item) for item in consumed]
    if len(identities) != _CONSUMED_LEDGER \
            or len(set(identities)) != _CONSUMED_LEDGER:
        raise _profile_fail(PROFILE, "log admission visitation ledger mismatch")
    return Fractal3dLogProof(tuple(sites), tuple(consumed))


def apply_fractal3d_log_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree:
    the admission IS the identity -- the two ``log`` nodes lower to the
    Math.log contract, so there is nothing to rewrite."""
    authenticate_fractal3d_log_admission(program, source_hash, profile)
    return program


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``."""
    fields = ALLOWED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            PROFILE, f"{key} is not an admitted fractal3d log admission carrier")
    return fields


__all__ = (
    "KEY", "PROFILE", "KEYS", "PROFILES", "FRACTAL3D_LOG_KEYS",
    "ALLOWED_ROW_FIELDS", "allowed_row_fields",
    "RAW_BYTES", "RAW_SHA256", "NORMALIZED_BYTES", "NORMALIZED_SHA256",
    "FUNCTIONS_SHA256", "WHOLE_SHA256", "INTERFACE_SHA256",
    "COUNTED_LOOP_SUMMARY", "FUNCTION_COUNT", "FUNCTION_INVENTORY",
    "RESOURCES", "POW_SITES", "LOG_SITE_COUNT", "LOG_SITES", "LOG_SHAPE",
    "Fractal3dLogSite", "Fractal3dLogProof",
    "authenticate_fractal3d_log_admission", "apply_fractal3d_log_admission",
)
