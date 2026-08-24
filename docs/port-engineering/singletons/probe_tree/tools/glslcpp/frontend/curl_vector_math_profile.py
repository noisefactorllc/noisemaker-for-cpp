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

_RAW_BYTES = 7290
_RAW_SHA256 = "33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce"
_NORMALIZED_BYTES = 4673
_NORMALIZED_SHA256 = "405774c12a29bff814b92ffbe2cc5f3b267367aa40832befc59b509573be91e9"
_FUNCTIONS_SHA256 = "06632686b2a2a1938389722409a109a71b6fb66fb2e1afd9b459e4fedb8b16fe"
_WHOLE_SHA256 = "a7c44947e08fdf478857d1f9c400cd5072df99a14ae4d63aebcbd6d1fc1d9374"
_INTERFACE_SHA256 = "0ff5180a4e2bbbf81e9a2705e99a155d9e9c378fbcbe5729eaa43a941c0227ae"

_DEFINES = (("OCTAVES", "int", "1"), ("OUTPUT_MODE", "int", "3"),
            ("RIDGES", "bool", "true"))
_LOOP_PROOF = (1, 0, 1, 1, 12, True)

# Every function, so an added or renamed helper is a hard failure.
_FUNCTIONS = (
    (16, "curlNoise3D", "vec3", 1, 25, "137:1-181:2"),
    (17, "fbmSimplex3D", "float", 1, 6, "114:1-130:2"),
    (18, "main", "void", 0, 11, "183:1-208:2"),
    (19, "permute", "vec3", 1, 1, "31:1-33:2"),
    (20, "permute", "vec4", 1, 1, "34:1-36:2"),
    (21, "simplex3D", "float", 1, 41, "43:1-110:2"),
    (22, "taylorInvSqrt", "vec4", 1, 1, "38:1-40:2"),
)

# Exactly the four authenticated nodes, ordered by owning function id. Each row
# is (callee, owning function id, path, span, result type, node sha, parent
# kind, child type tuple, child sha tuple).
_NODES = (
    ("tanh", 18, (6, "e0", 1, 0, 0), "196:12-196:34", "vec3",
     "bc83ca6fd3369ed6ac8321eb38db83a78569233a404563f491eb95736c27c09a",
     "binary", ("vec3",),
     ("f4e778bb127f3924bc93fd0b7beea12879fbf17dfb3fb557d25bc097f848c7be",)),
    ("mod", 19, (0, "e0"), "32:12-32:47", "vec3",
     "9e296505e841a30c1211828e3bc255acf00250f53572c992fc948c4a953eb208",
     "None", ("vec3", "float"),
     ("0e3bf42a81dd8ac63534ced244edbc02e3910e8a8f34c70530951adbf61e0b5c",
      "428f06112f27901a71a78a75eea7ce4163e0bb3d60bf377232af739c2b084fe3")),
    ("mod", 20, (0, "e0"), "35:12-35:47", "vec4",
     "e0063fe65cbef6674dbb68fe752ddb24dfa7f419c15816227d24d24c8b3de39d",
     "None", ("vec4", "float"),
     ("1754c609d6ec486f066d9cc518c08ce3e870ed7bd4a38ce67285b51a2f52b75c",
      "a37a9afeb11211283c1314b5d163604986bf55f197f0dba043f40f7a201d73bb")),
    ("mod", 21, (12, "e0", 1), "65:9-65:22", "vec3",
     "5e8842bf171ffb0d63398609deaad1e1c6171bafed84b10e83f5967b337bc466",
     "assign", ("vec3", "float"),
     ("c2725ce361f7540980fe47e0e05f5703bb2353263f26e478a6a9ba1c6380730a",
      "45961f58255d5a42e2f1264ee759fc43cd4ee3fa4241262452e8f96c16dccd2f")),
)

# Every site sits directly under one statement; none is nested in the counted
# loop, unlike Extrude's.
_ANCESTORS = (
    (("expr",), ("196:5-196:47",)),
    (("return",), ("32:5-32:48",)),
    (("return",), ("35:5-35:48",)),
    (("expr",), ("65:5-65:23",)),
)

# The mod overload shapes already admitted generally. Curl's three calls must
# all be OUTSIDE this set, or the profile is authenticating nothing new.
_GENERAL_MOD_OVERLOADS = frozenset({("float", "float"), ("vec2", "float"),
                                    ("vec2", "vec2")})

_PROFILE_SHA256 = "c32f8b601aed72e9085d17f068eb5602c9fba8e4b1876c4aabbdc19ee4e53d93"
_FROZEN_PROFILE_TUPLE_REPR = """('curl-vector-math-tanh-wide-mod-v1', 'synth/curl:curl', '33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce', (('OCTAVES', 'int', '1'), ('OUTPUT_MODE', 'int', '3'), ('RIDGES', 'bool', 'true')), 'glsl-f32', '06632686b2a2a1938389722409a109a71b6fb66fb2e1afd9b459e4fedb8b16fe', 'a7c44947e08fdf478857d1f9c400cd5072df99a14ae4d63aebcbd6d1fc1d9374', '0ff5180a4e2bbbf81e9a2705e99a155d9e9c378fbcbe5729eaa43a941c0227ae', (1, 0, 1, 1, 12, True), ((16, 'curlNoise3D', 'vec3', 1, 25, '137:1-181:2'), (17, 'fbmSimplex3D', 'float', 1, 6, '114:1-130:2'), (18, 'main', 'void', 0, 11, '183:1-208:2'), (19, 'permute', 'vec3', 1, 1, '31:1-33:2'), (20, 'permute', 'vec4', 1, 1, '34:1-36:2'), (21, 'simplex3D', 'float', 1, 41, '43:1-110:2'), (22, 'taylorInvSqrt', 'vec4', 1, 1, '38:1-40:2')), (('tanh', 18, (6, 'e0', 1, 0, 0), '196:12-196:34', 'vec3', 'bc83ca6fd3369ed6ac8321eb38db83a78569233a404563f491eb95736c27c09a', 'binary', ('vec3',), ('f4e778bb127f3924bc93fd0b7beea12879fbf17dfb3fb557d25bc097f848c7be',)), ('mod', 19, (0, 'e0'), '32:12-32:47', 'vec3', '9e296505e841a30c1211828e3bc255acf00250f53572c992fc948c4a953eb208', 'None', ('vec3', 'float'), ('0e3bf42a81dd8ac63534ced244edbc02e3910e8a8f34c70530951adbf61e0b5c', '428f06112f27901a71a78a75eea7ce4163e0bb3d60bf377232af739c2b084fe3')), ('mod', 20, (0, 'e0'), '35:12-35:47', 'vec4', 'e0063fe65cbef6674dbb68fe752ddb24dfa7f419c15816227d24d24c8b3de39d', 'None', ('vec4', 'float'), ('1754c609d6ec486f066d9cc518c08ce3e870ed7bd4a38ce67285b51a2f52b75c', 'a37a9afeb11211283c1314b5d163604986bf55f197f0dba043f40f7a201d73bb')), ('mod', 21, (12, 'e0', 1), '65:9-65:22', 'vec3', '5e8842bf171ffb0d63398609deaad1e1c6171bafed84b10e83f5967b337bc466', 'assign', ('vec3', 'float'), ('c2725ce361f7540980fe47e0e05f5703bb2353263f26e478a6a9ba1c6380730a', '45961f58255d5a42e2f1264ee759fc43cd4ee3fa4241262452e8f96c16dccd2f'))), ((('expr',), ('196:5-196:47',)), (('return',), ('32:5-32:48',)), (('return',), ('35:5-35:48',)), (('expr',), ('65:5-65:23',))))"""

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
            != (("resolution", "tileOffset", "fullResolution", "time", "scale",
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
