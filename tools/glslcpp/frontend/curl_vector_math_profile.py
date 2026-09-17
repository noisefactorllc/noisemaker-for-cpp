"""Exact vector-math closure profile for Curl.

This module does not add a general transcendental or wide-``mod`` capability.
It authenticates the one corpus program whose ``tanh(vec3)`` and three
vec3/vec4-by-scalar ``mod`` calls may be lowered, and returns the
candidate-owned IR objects consumed independently by the validator and the
emitter.

Two boundary facts matter for anyone extending this:

* ``mod`` is already one of the approved capabilities and already passes the
  builtin-name gate for every program.  What is NOT general is its overload
  shape: both authorities carry an identical inline literal admitting only
  ``(float,float)``, ``(vec2,float)`` and ``(vec2,vec2)``.  That tuple must
  stay untouched.  Curl's three wider calls are admitted by node identity
  through this profile, so no other program gains vec3/vec4 ``mod``.
* ``tanh`` is absent from every table and must never be added to one.  It
  follows the identity-scoped skip pattern used by ``round``, ``all``,
  ``lessThanEqual`` and ``floatBitsToUint``, so the capability vocabulary
  stays at 44 entries.

One of the four authenticated sites — the ``mod`` in the ``vec3`` overload of
``permute`` (function id 19) — is dead code at the authorized define map: it is
not reachable from ``main``.  It is authenticated, emitted and compiled, but no
rendering evidence discriminates it.  Any report must say so plainly.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "curl-vector-math-tanh-wide-mod-v1"
CURL_KEY = "synth/curl:curl"

# Relocked for the generic runtime-define contract: OCTAVES/OUTPUT_MODE/
# RIDGES moved from literal int/bool defines to dynamic uniforms, so
# normalize() prepends three `uniform` declaration lines ahead of everything
# else in the source. That single cause explains every field below that
# moved: every function id shifts +3 (16-22 -> 19-25), every span shifts by
# the same three prepended lines, `program.resources.uniforms` gains the
# three new uniform names ahead of the eight already there, and the entrypoint
# charge rises from 12 to 36 (OCTAVES's own loop trip count -- authenticated
# separately by runtime_loop_bound_profile's own CURL_KEY carrier -- multiplies
# curlNoise3D's twelve unrolled fbmSimplex3D calls: 3 * 12 = 36, matching the
# source's own "36 simplex3D inlines" comment). No site moved, was added, or
# was removed; recomputed mechanically with this module's own _sha/_span/
# _whole/_interface helpers against the dynamic tree, then round-trip
# verified through authenticate_curl_vector_math before landing.
_RAW_BYTES = 7290
_RAW_SHA256 = "33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce"
_NORMALIZED_BYTES = 5114
_NORMALIZED_SHA256 = "6a1392aefe3c9536deda3b2ff413596cf5e259046b537ae4c09b0cc928372b6d"
_FUNCTIONS_SHA256 = "b92fc0929b856b340ae11103c23a58e9e3834f6b5b02227f244d1b73170c7ff2"
_WHOLE_SHA256 = "52ce4382357c168e8806e379fe75fb71fb8afd071e3a8d766391b86246de0af8"
_INTERFACE_SHA256 = "2b00785b906ff64e016ea416d50e6106c2494dc34f3655f29037ff72bbb939af"

_DEFINES = (("OCTAVES", "str", "int"), ("OUTPUT_MODE", "str", "int"),
            ("RIDGES", "str", "bool"))
_LOOP_PROOF = (1, 0, 1, 3, 36, True)

# Every function, so an added or renamed helper is a hard failure.
_FUNCTIONS = (
    (19, "curlNoise3D", "vec3", 1, 25, "140:1-184:2"),
    (20, "fbmSimplex3D", "float", 1, 6, "117:1-133:2"),
    (21, "main", "void", 0, 11, "186:1-229:2"),
    (22, "permute", "vec3", 1, 1, "34:1-36:2"),
    (23, "permute", "vec4", 1, 1, "37:1-39:2"),
    (24, "simplex3D", "float", 1, 41, "46:1-113:2"),
    (25, "taylorInvSqrt", "vec4", 1, 1, "41:1-43:2"),
)

# Exactly the four authenticated nodes, ordered by owning function id. Each row
# is (callee, owning function id, path, span, result type, node sha, parent
# kind, child type tuple, child sha tuple).
_NODES = (
    ("tanh", 21, (6, "e0", 1, 0, 0), "199:12-199:34", "vec3",
     "65277325ba652ae7f6f918fa89c67e09b0d5b1b3f7869e35d5e126899ea8afbb",
     "binary", ("vec3",),
     ("ce00823e91c194aaf60f4a1ee7776c2428520bc5836dfb0b5aac519241eccda4",)),
    ("mod", 22, (0, "e0"), "35:12-35:47", "vec3",
     "53e130f2d7565914c75b80f240994ba52b76b1886aca4800ba0a6e14009810c2",
     "None", ("vec3", "float"),
     ("c234aaafca741a1524b395dfd56ebaabd3ac6c68cf55e1e61fe0d6d93dae2af3",
      "586ebb838e95f08141d35c9b498e42fccfecbe2c3165f6f86361037c1227e962")),
    ("mod", 23, (0, "e0"), "38:12-38:47", "vec4",
     "b85a4366c924a40674a36921bdf6faee9bd8a7bd435fcae9e68de25e671d885b",
     "None", ("vec4", "float"),
     ("823afbf3ac8d95a17912e085d80b51ddb1f707d32ce43eb1179f7bea07e20c7e",
      "653034c76f5bbecef25cda10ca6f681ad52d57cc82d81d8578192c6930574f04")),
    ("mod", 24, (12, "e0", 1), "68:9-68:22", "vec3",
     "bf8f941004345a0b2b801543add17510799ac31d3fec0cc765dfb200e2bc13c9",
     "assign", ("vec3", "float"),
     ("144bb779c287c434417940e95ec776b384368057252f86312fcfc7387e36e5aa",
      "be3987cbf82fa8cc4450fffa0aaca8cceaeff97349df42cf288f1ae822ec79d4")),
)

# Every site sits directly under one statement; none is nested in the counted
# loop, unlike Extrude's.
_ANCESTORS = (
    (("expr",), ("199:5-199:47",)),
    (("return",), ("35:5-35:48",)),
    (("return",), ("38:5-38:48",)),
    (("expr",), ("68:5-68:23",)),
)

# The mod overload shapes already admitted generally. Curl's three calls must
# all be OUTSIDE this set, or the profile is authenticating nothing new.
_GENERAL_MOD_OVERLOADS = frozenset({("float", "float"), ("vec2", "float"),
                                    ("vec2", "vec2")})

_PROFILE_SHA256 = "b067523ba841fdf0068778fc758d876f56d3eae50608438407938627ac3c76d6"
_FROZEN_PROFILE_TUPLE_REPR = """('curl-vector-math-tanh-wide-mod-v1', 'synth/curl:curl', '33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce', (('OCTAVES', 'str', 'int'), ('OUTPUT_MODE', 'str', 'int'), ('RIDGES', 'str', 'bool')), 'glsl-f32', 'b92fc0929b856b340ae11103c23a58e9e3834f6b5b02227f244d1b73170c7ff2', '52ce4382357c168e8806e379fe75fb71fb8afd071e3a8d766391b86246de0af8', '2b00785b906ff64e016ea416d50e6106c2494dc34f3655f29037ff72bbb939af', (1, 0, 1, 3, 36, True), ((19, 'curlNoise3D', 'vec3', 1, 25, '140:1-184:2'), (20, 'fbmSimplex3D', 'float', 1, 6, '117:1-133:2'), (21, 'main', 'void', 0, 11, '186:1-229:2'), (22, 'permute', 'vec3', 1, 1, '34:1-36:2'), (23, 'permute', 'vec4', 1, 1, '37:1-39:2'), (24, 'simplex3D', 'float', 1, 41, '46:1-113:2'), (25, 'taylorInvSqrt', 'vec4', 1, 1, '41:1-43:2')), (('tanh', 21, (6, 'e0', 1, 0, 0), '199:12-199:34', 'vec3', '65277325ba652ae7f6f918fa89c67e09b0d5b1b3f7869e35d5e126899ea8afbb', 'binary', ('vec3',), ('ce00823e91c194aaf60f4a1ee7776c2428520bc5836dfb0b5aac519241eccda4',)), ('mod', 22, (0, 'e0'), '35:12-35:47', 'vec3', '53e130f2d7565914c75b80f240994ba52b76b1886aca4800ba0a6e14009810c2', 'None', ('vec3', 'float'), ('c234aaafca741a1524b395dfd56ebaabd3ac6c68cf55e1e61fe0d6d93dae2af3', '586ebb838e95f08141d35c9b498e42fccfecbe2c3165f6f86361037c1227e962')), ('mod', 23, (0, 'e0'), '38:12-38:47', 'vec4', 'b85a4366c924a40674a36921bdf6faee9bd8a7bd435fcae9e68de25e671d885b', 'None', ('vec4', 'float'), ('823afbf3ac8d95a17912e085d80b51ddb1f707d32ce43eb1179f7bea07e20c7e', '653034c76f5bbecef25cda10ca6f681ad52d57cc82d81d8578192c6930574f04')), ('mod', 24, (12, 'e0', 1), '68:9-68:22', 'vec3', 'bf8f941004345a0b2b801543add17510799ac31d3fec0cc765dfb200e2bc13c9', 'assign', ('vec3', 'float'), ('144bb779c287c434417940e95ec776b384368057252f86312fcfc7387e36e5aa', 'be3987cbf82fa8cc4450fffa0aaca8cceaeff97349df42cf288f1ae822ec79d4'))), ((('expr',), ('199:5-199:47',)), (('return',), ('35:5-35:48',)), (('return',), ('38:5-38:48',)), (('expr',), ('68:5-68:23',))))"""


_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class CurlVectorMathProof:
    tanh_site: TypedExpression
    mod_sites: tuple[TypedExpression, TypedExpression, TypedExpression]
    owners: tuple[TypedFunction, ...]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]

    @property
    def nodes(self) -> tuple[TypedExpression, ...]:
        return (self.tanh_site, *self.mod_sites)

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.tanh_site, *self.mod_sites, *self.owners]
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "CURL_KEY", "CurlVectorMathProof",
           "authenticate_curl_vector_math", "apply_curl_vector_math")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _profile_tuple() -> tuple[object, ...]:
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        for item, parent, epath in _walk_expression(
                expression, None, (*path, f"e{index}")):
            yield item, parent, epath, chain
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def authenticate_curl_vector_math(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> CurlVectorMathProof:
    """Authenticate Curl and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != CURL_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or defines != _DEFINES
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")

    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if program.structs != () or program.uniform_blocks != ():
        raise _fail("struct or uniform block presence mismatch")

    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic) != _LOOP_PROOF):
        raise _fail("loop or call graph profile mismatch")

    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (("OCTAVES", "OUTPUT_MODE", "RIDGES",
                 "resolution", "tileOffset", "fullResolution", "time", "scale",
                 "seed", "speed", "intensity"),
                (), ("fragColor",), False, False)):
        raise _fail("resource or binding signature mismatch")

    functions = tuple(sorted(program.functions, key=lambda item: item.id))
    if tuple((item.id, item.name, item.return_type.display(),
              len(item.parameters), len(item.body), _span(item))
             for item in functions) != _FUNCTIONS:
        raise _fail("function inventory mismatch")
    by_id = {item.id: item for item in functions}

    # Census the WHOLE program: a fifth tanh or mod site anywhere is a hard
    # failure, not an unnoticed extra.
    located: list[tuple[str, int, tuple[object, ...], TypedExpression,
                        TypedExpression | None, tuple[TypedStatement, ...]]] = []
    for function in functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain in _walk_statement(statement, (index,)):
                if item.kind == "builtin" and item.callee in ("tanh", "mod"):
                    located.append((item.callee, function.id, path, item,
                                    parent, chain))

    if len(located) != len(_NODES):
        raise _fail(f"closure site cardinality mismatch: {len(located)}")

    actual = tuple(
        (callee, owner, path, _span(item),
         "" if item.type is None else item.type.display(), _sha(item),
         "None" if parent is None else parent.kind,
         tuple("" if child.type is None else child.type.display()
               for child in item.children),
         tuple(_sha(child) for child in item.children))
        for callee, owner, path, item, parent, _ in located)
    if actual != _NODES:
        raise _fail("closure node identity mismatch")

    tanh_sites = tuple(item for callee, _, _, item, _, _ in located
                       if callee == "tanh")
    mod_sites = tuple(item for callee, _, _, item, _, _ in located
                      if callee == "mod")
    if len(tanh_sites) != 1 or len(mod_sites) != 3:
        raise _fail("tanh or mod cardinality mismatch")

    if len(tanh_sites[0].children) != 1:
        raise _fail("tanh arity mismatch")
    for node in mod_sites:
        if len(node.children) != 2:
            raise _fail("mod arity mismatch")
        shape = tuple(child.type.display() for child in node.children)
        # Every authenticated mod call must lie OUTSIDE the generally admitted
        # overload set; otherwise this profile would be claiming authority it
        # does not need, and the narrow carve-out would be untested.
        if shape in _GENERAL_MOD_OVERLOADS:
            raise _fail("authenticated mod site is already generally admitted")
        if shape[1] != "float" or shape[0] not in ("vec3", "vec4"):
            raise _fail("mod overload outside the authorized widths")

    chains = tuple(chain for _, _, _, _, _, chain in located)
    if tuple((tuple(item.kind for item in chain),
              tuple(_span(item) for item in chain))
             for chain in chains) != _ANCESTORS:
        raise _fail("closure ancestry mismatch")

    owners = tuple(by_id[owner] for _, owner, _, _, _, _ in located)
    result = CurlVectorMathProof(tanh_sites[0], mod_sites, owners, chains)
    if len(result.consumed_objects) != 12:
        raise _fail(
            f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_curl_vector_math(program: TypedProgram, source_hash: str | None,
                           profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_curl_vector_math(program, source_hash, profile)
    return program
