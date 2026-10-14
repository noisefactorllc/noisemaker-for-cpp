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
FLYTHROUGH_KEY = "synth3d/flythrough3d:precompute"
FLYTHROUGH_PROFILE = "fractal3d-log-flythrough3d-v1"
KEYS: tuple[str, ...] = (FLYTHROUGH_KEY, KEY)
PROFILES = {KEY: PROFILE, FLYTHROUGH_KEY: FLYTHROUGH_PROFILE}
FRACTAL3D_LOG_KEYS = frozenset(KEYS)

# The complete allowed field set for the slice row -- an ALLOWLIST enforced
# by the validator's `set(item) != expected` comparison.
ALLOWED_ROW_FIELDS: dict[str, frozenset[str]] = {
    KEY: frozenset({"defines", "fractal3d_log_profile", "program_key"}),
    FLYTHROUGH_KEY: frozenset({"defines", "fractal3d_log_profile",
                              "out_inout_admission_profile", "program_key"}),
}

RAW_BYTES = 6882
RAW_SHA256 = "4bc39fb7920cf0829cc6a6fc4670cdac9f5ea68c5438f569050a4732c1e6de19"
NORMALIZED_BYTES = 6173
NORMALIZED_SHA256 = "3dd80cd8f5a01004ace3df4e3dea95b0861b8e1f191b66958ceabe36f3a8be93"
FUNCTIONS_SHA256 = "12e274f8dbf497961ff11160898d060106eac4e5f478af2aeb8694da9752d2f3"
WHOLE_SHA256 = "010e849e6f0200c60386d2e534fff888d30337d006d87842378212014773b493"
INTERFACE_SHA256 = "cd93a4bff583a921ca02539c2f537dde9b8151efd5f298f0bd3ae9dae831cbb7"

# The seed-attached counted-for summary: four carrier loops (one per
# fractal carrier), all proved, depth 1, product 20, entrypoint charge
# 4*20, acyclic.
COUNTED_LOOP_SUMMARY = (4, 0, 1, 20, 80, True)

FUNCTION_COUNT = 7
FUNCTION_INVENTORY = (
    (35, "boxFold", "vec3", ((22, "z", "vec3"), (23, "foldingLimit", "float"))),
    (36, "computeFractal", "vec3", ((33, "p", "vec3"), (34, "juliaC", "vec3"))),
    (37, "juliaBulb", "vec3",
     ((17, "pos", "vec3"), (18, "c", "vec3"), (19, "n", "float"),
      (20, "maxIter", "int"), (21, "bail", "float"))),
    (38, "juliaCube", "vec3",
     ((28, "pos", "vec3"), (29, "c", "vec3"), (30, "scale", "float"),
      (31, "maxIter", "int"), (32, "bail", "float"))),
    (39, "main", "void", ()),
    (40, "mandelbulb", "vec3",
     ((13, "pos", "vec3"), (14, "n", "float"), (15, "maxIter", "int"),
      (16, "bail", "float"))),
    (41, "mandelcube", "vec3",
     ((24, "pos", "vec3"), (25, "scale", "float"), (26, "maxIter", "int"),
      (27, "bail", "float"))),
)

RESOURCES = (
    ("volumeSize", "noiseType", "power", "iterations", "bailout", "juliaX",
     "juliaY", "juliaZ", "colorMode"),
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
    ("juliaBulb", "75:14-75:29", 2),
    ("juliaBulb", "77:20-77:29", 2),
    ("mandelbulb", "37:14-37:29", 2),
    ("mandelbulb", "39:20-39:29", 2),
)

LOG_SITE_COUNT = 2
# (owner_id, owner_name, node span, argument span, statement span,
#  parent kind, (call sha, argument sha, statement sha))
LOG_SITES = (
    (37, "juliaBulb", "91:24-91:30", "91:28-91:29", "91:5-91:40", "binary",
     ("cb37bc093964e64fc7b5b0503c8792a7c2f0f41371fe5d72591c7fb2659aa6a6",
      "13ecb77cd7c814691e2dca41343311974e2c13592907f2605134a17ab7f7b69d",
      "81c641843dd61232745eccec3d90b2f5812c10639845e46cae51abe4c726dcb0")),
    (40, "mandelbulb", "53:24-53:30", "53:28-53:29", "53:5-53:40", "binary",
     ("538a3d4d95060469632d18797bf29ce1f05d230667059b68a797cb800651a7cd",
      "e13dc161393beb9c1caa7d28396d72010e8e6561f1d1b4564b230940786f6b3f",
      "66df880b7efd7239a3a503472cae2e20fecf81720c0c1928d309ca9c46b64b61")),
)
# Argument kind and type, result type per site -- the value tier the
# identity hashes alone would absorb.
LOG_SHAPE = (
    (37, "juliaBulb", "id", "float", "float", "binary", "91:24-91:30"),
    (40, "mandelbulb", "id", "float", "float", "binary", "53:24-53:30"),
)

# The two sites' two live nodes each and the two DISTINCT owner functions:
# 6 distinct objects, each consumed exactly once.
_CONSUMED_LEDGER = 6

_TOTAL_NODES = 656
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


def _authenticate_flythrough_log(program, source_hash, profile):
    def fail(message):
        return _profile_fail(FLYTHROUGH_PROFILE, message)

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if profile != FLYTHROUGH_PROFILE:
        raise fail("exact profile carrier required")
    if (source_hash != "e4288dfc3384f76e63eda968ad4ce3219a9b96989d8e6ff38755dbcf44f788f3"
            or len(raw) != 11404
            or hashlib.sha256(raw).hexdigest() != source_hash
            or len(normalized) != 7766
            or hashlib.sha256(normalized).hexdigest()
            != "b8ae9dac1d40943d7bd023fbd6bc26494c686fe62fecd2e26551367ea82eaa58"
            or _sha(clear_counted_loop_proofs(program.functions))
            != "6f3edced834a17851390e18356b9a4b6a5fb72edde48d69b50f95b8594b0e93a"
            or _whole_cleared(program)
            != "250d2cb9a66ad470c67489ba4e5af1f9036b9e21d5b0f8be39174df601e29258"
            or _interface(program)
            != "45e03760bdc51c6217d746b5fb329fe8c67e9f2b5301fb88660c79db93f32c8a"):
        raise fail("source or typed identity lock mismatch")
    summary = program.counted_loop_proof
    if summary is None or (
            summary.loop_count, summary.unproved_loop_count,
            summary.max_effective_depth, summary.max_lexical_product,
            summary.entrypoint_charge, summary.call_graph_acyclic) != (2, 0, 1, 24, 240, True):
        raise fail("counted-for closure summary mismatch")
    sites = _site_proofs(program)
    if (len(sites) != 1 or sites[0].record != (
            62, "mandelbulb", "211:25-211:31", "211:29-211:30",
            "211:5-211:41", "binary",
            ("163f0bdc62ba739b2e0b7ce8fcc24f4ed46a505f0e48e0acbbab09850f1bebc8",
             "92f13db83c4d3d74ef3bfa93dfc69b11c29b8efcf78f8ae88025db6bf2717f1c",
             "2b27095f78a8bb78b0e17ef6d21be30e3902aef7937a2dfc969c25fe39bc091d"))
            or sites[0].argument.kind != "id"
            or sites[0].argument.type.display() != "float"
            or sites[0].node.type.display() != "float"
            or _node_census(program) != (798, 34)
            or tuple(sum(1 for _, node, _ in _program_nodes(program)
                         if node.kind == "builtin" and node.callee == name)
                     for name in _ZERO_FAMILY) != (0, 0, 0, 0)):
        raise fail("log site or builtin census mismatch")
    consumed = (sites[0].node, sites[0].argument, sites[0].owner)
    if len({id(item) for item in consumed}) != 3:
        raise fail("log admission visitation ledger mismatch")
    return Fractal3dLogProof(sites, consumed)


def authenticate_fractal3d_log_admission(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> Fractal3dLogProof | None:
    """Authenticate the frozen log identity profile and return the two
    exact live call nodes for ``program.key``.

    Returns ``None`` when ``program.key`` is not a carrier and no profile
    was supplied; supplying a profile for a non-carrier key is a hard
    failure that names the sole admitted sites.
    """
    if program.key == FLYTHROUGH_KEY:
        return _authenticate_flythrough_log(program, source_hash, profile)
    if program.key != KEY:
        if profile is not None:
            raise _profile_fail(
                PROFILE,
                "program key is not an admitted fractal3d log admission "
                f"carrier; {KEY} has sites 91:24 and 53:24; "
                f"{FLYTHROUGH_KEY} has site 211:25")
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


def authenticate_fractal3d_value_copies(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    if program.key != KEY:
        raise _profile_fail(PROFILE, "value-copy program key mismatch")
    # The log proof binds raw source, normalized source, defines, the complete
    # typed tree, and the loop carrier before selecting these live nodes.
    authenticate_fractal3d_log_admission(program, source_hash, profile)
    expected = (
        (37, "juliaBulb", 45, 17, 60),
        (38, "juliaCube", 57, 28, 145),
        (40, "mandelbulb", 91, 13, 22),
        (41, "mandelcube", 103, 24, 102),
    )
    copies = []
    for owner_id, owner_name, target_id, source_id, line in expected:
        owners = [item for item in program.functions
                  if item.id == owner_id and item.name == owner_name]
        if len(owners) != 1 or not owners[0].body:
            raise _profile_fail(PROFILE, "value-copy owner mismatch")
        statement = owners[0].body[0]
        if statement.kind != "decl" or len(statement.expressions) != 1:
            raise _profile_fail(PROFILE, "value-copy statement mismatch")
        declaration = statement.expressions[0]
        source = declaration.children[0] if len(declaration.children) == 1 else None
        if (statement.span.start_line != line
                or declaration.kind != "declaration"
                or declaration.symbol_id != target_id
                or declaration.symbol is None
                or declaration.symbol.name != "z"
                or declaration.symbol.storage != "local"
                or declaration.type.display() != "vec3"
                or source is None or source.kind != "id"
                or source.symbol_id != source_id
                or source.symbol is None or source.symbol.name != "pos"
                or source.symbol.storage != "parameter"
                or source.type.display() != "vec3"):
            raise _profile_fail(PROFILE, "value-copy declaration mismatch")
        copies.append(declaration)
    if len({id(item) for item in copies}) != len(expected):
        raise _profile_fail(PROFILE, "value-copy identity mismatch")
    return tuple(copies)


def authenticate_fractal3d_pow_nan_sites(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the four exact bulb pow calls whose NaN input follows Math.pow."""
    if program.key != KEY:
        raise _profile_fail(PROFILE, "pow program key mismatch")
    authenticate_fractal3d_log_admission(program, source_hash, profile)
    expected = (
        (37, "juliaBulb", "75:14-75:29", 47, "binary"),
        (37, "juliaBulb", "77:20-77:29", 47, "id"),
        (40, "mandelbulb", "37:14-37:29", 93, "binary"),
        (40, "mandelbulb", "39:20-39:29", 93, "id"),
    )
    sites = [(owner, node) for owner, node, _ in _program_nodes(program)
             if node.kind == "builtin" and node.callee == "pow"]
    if len(sites) != len(expected):
        raise _profile_fail(PROFILE, "pow site count mismatch")
    for (owner, node), (owner_id, owner_name, span, r_id, exponent_kind) in zip(
            sites, expected):
        if (owner is None or owner.id != owner_id or owner.name != owner_name
                or _span(node) != span or node.type.display() != "float"
                or len(node.children) != 2
                or node.children[0].kind != "id"
                or node.children[0].symbol_id != r_id
                or node.children[0].symbol is None
                or node.children[0].symbol.name != "r"
                or node.children[0].type.display() != "float"
                or node.children[1].kind != exponent_kind
                or node.children[1].type.display() != "float"):
            raise _profile_fail(PROFILE, "pow typed site mismatch")
    nodes = tuple(node for _, node in sites)
    if len({id(node) for node in nodes}) != len(expected):
        raise _profile_fail(PROFILE, "pow node identity mismatch")
    return nodes


def allowed_row_fields(key: str) -> frozenset[str]:
    """The complete set of slice-row fields permitted for ``key``."""
    fields = ALLOWED_ROW_FIELDS.get(key)
    if fields is None:
        raise _profile_fail(
            PROFILE, f"{key} is not an admitted fractal3d log admission carrier")
    return fields


__all__ = (
    "KEY", "PROFILE", "FLYTHROUGH_KEY", "FLYTHROUGH_PROFILE",
    "KEYS", "PROFILES", "FRACTAL3D_LOG_KEYS",
    "ALLOWED_ROW_FIELDS", "allowed_row_fields",
    "RAW_BYTES", "RAW_SHA256", "NORMALIZED_BYTES", "NORMALIZED_SHA256",
    "FUNCTIONS_SHA256", "WHOLE_SHA256", "INTERFACE_SHA256",
    "COUNTED_LOOP_SUMMARY", "FUNCTION_COUNT", "FUNCTION_INVENTORY",
    "RESOURCES", "POW_SITES", "LOG_SITE_COUNT", "LOG_SITES", "LOG_SHAPE",
    "Fractal3dLogSite", "Fractal3dLogProof",
    "authenticate_fractal3d_log_admission", "apply_fractal3d_log_admission",
    "authenticate_fractal3d_value_copies",
    "authenticate_fractal3d_pow_nan_sites",
)
