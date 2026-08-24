"""Focused RED/GREEN proof for the ``wobble`` uv-alias varying admission.

Written before ``tools/glslcpp/frontend/varying_uv_profile.py`` existed; the
first run of this file reported ``ModuleNotFoundError`` from ``_module`` for
every test in it.

``filter/wobble:wobble`` declares exactly one varying, ``in vec2 v_texCoord;``
at raw ``wobble.glsl:14``, reads it exactly once in ``main`` (normalized
``100:24-100:34``, ``vec2 sampleCoord = v_texCoord + offset;``), and never
writes it. The shipped JavaScript materializes the name as an **alias of the
pixel context's ``uv``** -- the runtime's three-slot map
(``glsl-runtime.js:95-99``) has no vertex stage and no interpolation, and
``beginPixel`` copies ``context.uv`` into ``v_texCoord`` element by element
(``glsl-runtime.js:148-151``). Admission is therefore pure expression
lowering to ``context.uv``: no Frame, no State field, no kernel-signature
change.

Testing rules inherited from the Shapes/cellRefract slices apply directly:

1. ``Symbol`` embeds its span, so a value-level mutation shifts every
   enclosing node hash. The production module evaluates the alias-name,
   storage, type and span locks **ahead** of the symbol-hash identity lock,
   and each lock is proved load-bearing by *deleting the lock* in a scratch
   copy -- never by mutating the input and watching something raise.
2. Every mutation test refreezes **only** the coarse hash fields (plus the
   specific counters the mutation unavoidably moves) and asserts that no
   coarse message fired. Semantic fields keep their frozen originals.
3. The census walks global declaration initializers as well as function
   bodies; the read/write censuses are what prove read-only-ness, and the
   write census is frozen empty rather than assumed.

Two facts specific to this mechanism shape the locks (design §1.7, §5.2):

* The varying ``Symbol``'s span is the **whole file** (``1:1-107:1`` for
  wobble) -- the preprocessor drops the declaration line from the normalized
  source entirely and the analyzer constructs the symbol before declarations
  are inventoried. The span is locked AS IT IS, and the raw-source
  declaration site is carried separately.
* The varying is **not** in ``typed.declarations`` at all; it exists only in
  ``typed.interface_symbols`` and as the resolution target of ``id`` nodes.
  A lock freezes that absence so the emitter's ``name()`` arm stays the only
  consumer path.

wobble's record is PREPARED, not landed: no slice row carries
``varying_profile`` yet (the integration slice wires the row), so the
module's landed registry is empty exactly like kaleido's array record before
its row landed -- registering a key without its row would redden the live
schema census.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import pathlib
import re
import struct
import types
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program, named_type
from tools.glslcpp.frontend.typed_ir import TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.varying_uv_profile"

KEY = "filter/wobble:wobble"
PROFILE = "varying-uv-admission-v1"
SOURCE_PATH = "filter/wobble/wobble.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "1bdd1e3bed9111743dfeb7e3418e14c42aa8d93ed4636167a99d17cb143a38cc"
NORMALIZED_SHA256 = (
    "c767dbef8eaa5c0730c6502053b7edf4af30d051de154425fd19860368e34545")

VARYING_ID = 24
MAIN_ID = 19
READ_COUNT = 1
LEDGER = 2

# The real whole-file span of the varying Symbol (design 1.7: the analyzer
# builds it at the whole-file span; lock it as it is, never "fix" it).
SYMBOL_SPAN = "1:1-107:1"
RAW_DECLARATION = "in vec2 v_texCoord;"
RAW_DECLARATION_SITE = "wobble.glsl:14:1"

# Every message the coarse gate can produce. A local lock that "fires" with one
# of these is not testing what its name claims.
COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)

FOREIGN_SOURCE = (
    "uniform sampler2D inputTex;\n"
    "in vec2 v_texCoord;\n"
    "out vec4 fragColor;\n"
    "void main() {\n"
    "    fragColor = vec4(v_texCoord, 0.0, 1.0);\n"
    "}\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("varying uv profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock predicates.

    A neutralized predicate always reports "holds", which is exactly what
    removing the lock from the module source would do. The live module object
    is never touched, so these tests cannot leak state into each other."""
    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    scratch = types.ModuleType(f"{module.__name__}__scratch")
    scratch.__dict__.update({
        "__file__": module.__file__,
        "__package__": module.__package__,
    })
    exec(compile(source, module.__file__, "exec"), scratch.__dict__)
    for name in disable:
        if not callable(getattr(scratch, name, None)):
            raise AssertionError(f"{name} is not a deletable lock predicate")
        setattr(scratch, name, lambda *args, **kwargs: True)
    return scratch


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _analyzed(raw: str | None = None, key: str = KEY,
              defines: dict | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, KEY)
               if defines is None else defines)
    return analyze_program(parse_program(raw, key, defines), key)


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _main(program):
    return next(item for item in program.functions if item.name == "main")


def _fn(program, name):
    return next(item for item in program.functions if item.name == name)


def _nodes(program):
    """Every expression node in every function body, in deterministic order."""
    def expression(value):
        yield value
        for child in value.children:
            yield from expression(child)
    for function in program.functions:
        for statement in function.body:
            def walk(item):
                for expr in item.expressions:
                    yield from expression(expr)
                for child in item.children:
                    yield from walk(child)
            yield from walk(statement)


def _id_clone(program, symbol_id):
    node = next(item for item in _nodes(program)
                if item.kind == "id" and item.symbol_id == symbol_id)
    return dataclasses.replace(node)


# The coarse gate, in the order the module evaluates it.
_COARSE_ORDER = ("raw", "normalized", "functions", "whole", "interface")


def _coarse_values(module, candidate):
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    return {
        "raw": {"raw_bytes": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest()},
        "normalized": {
            "normalized_bytes": len(normalized),
            "normalized_sha256": hashlib.sha256(normalized).hexdigest()},
        "functions": {"functions_sha256": module._sha(candidate.functions)},
        "whole": {"whole_sha256": module._whole(candidate)},
        "interface": {"interface_sha256": module._interface(candidate)},
    }


def _relocked(module, candidate, key=KEY, **overrides):
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen.

    Deliberately does **not** refreeze any semantic field: the declaration
    inventory, the varying identity, the read/write censuses and every node
    hash keep their frozen originals. Refreezing those would hand the mutation
    to the very lock under test and make the experiment vacuous."""
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        locks[key].update(values[name])
    locks[key].update(overrides)
    return locks


def _relocked_partial(module, candidate, upto, key=KEY):
    """Refreeze only the coarse fields the module checks *before* ``upto``."""
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        if name == upto:
            return locks
        locks[key].update(values[name])
    raise AssertionError(f"{upto} is not a coarse gate stage")


def _recount(module, candidate, key=KEY):
    """Refreeze only the two program-wide *cardinality* counters."""
    total, assigns = module._node_census(candidate)
    return {"total_nodes": total, "total_assigns": assigns}


def _recallgraph(module, candidate, key=KEY):
    """Refreeze the call-graph lock fields to the mutant."""
    edges = module._call_graph(candidate)
    reachable, unreachable = module._reachability(candidate)
    proof = candidate.counted_loop_proof
    return {
        "call_edge_count": len(edges),
        "call_graph_sha256": module._sha(edges),
        "reachable": reachable,
        "unreachable": unreachable,
        "counted_loop_proof": (
            None if proof is None else
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic)),
    }


def _reinventory(module, candidate, key=KEY):
    return {"declaration_count": len(candidate.declarations),
            "declaration_inventory": module._declaration_inventory(candidate)}


def _authenticate(module, candidate, locks, profile=PROFILE, key=KEY):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_varying_uv(
            candidate, locks[key]["raw_sha256"], profile)


def _expect(test, module, candidate, locks, expected, profile=PROFILE,
            key=KEY):
    with test.assertRaises(ValueError) as raised:
        _authenticate(module, candidate, locks, profile, key)
    message = str(raised.exception)
    for coarse in COARSE:
        test.assertNotIn(coarse, message,
                         f"{expected!r} was absorbed by the coarse gate")
    test.assertIn(expected, message)
    return message


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _batch_f32(values):
    return struct.unpack(f"<{len(values)}f",
                         struct.pack(f"<{len(values)}f", *values))


class VaryingUvPublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual((KEY, module.GRIME_KEY), module.KEYS,
                         "both rows carry varying_profile; the landed "
                         "registry holds exactly their two keys")
        self.assertEqual({KEY: PROFILE, module.GRIME_KEY: PROFILE},
                         module.PROFILES)
        self.assertEqual(frozenset({KEY, module.GRIME_KEY}),
                         module.VARYING_UV_KEYS)
        self.assertIsInstance(module.VARYING_UV_KEYS, frozenset)
        # grime landed as typed row 191 with its float-bit ingress
        # companion, emptying the prepared set (see the registry test).
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual(KEY, module.WOBBLE_KEY)
        self.assertEqual(PROFILE, module.WOBBLE_PROFILE)
        self.assertEqual({}, module.PREPARED_PROFILES)
        for name in ("KEYS", "PROFILES", "VARYING_UV_KEYS", "WOBBLE_KEY",
                     "WOBBLE_PROFILE", "GRIME_KEY", "GRIME_PROFILE",
                     "PREPARED_KEYS", "PREPARED_PROFILES",
                     "ALLOWED_ROW_FIELDS", "PREPARED_ROW_FIELDS",
                     "allowed_row_fields", "UV_ALIAS_NAMES",
                     "VaryingUvContract", "varying_uv_contract",
                     "authenticate_varying_uv", "apply_varying_uv"):
            with self.subTest(name=name):
                self.assertIn(name, module.__all__)
                self.assertTrue(hasattr(module, name))

    def test_the_frozen_source_path_names_the_authenticated_file(self):
        module = _module()
        self.assertEqual(SOURCE_PATH, module._LOCKS[KEY]["source_path"])
        raw = (CORPUS / module._LOCKS[KEY]["source_path"]).read_bytes()
        self.assertEqual(len(raw), module._LOCKS[KEY]["raw_bytes"])
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(RAW_SHA256, module._LOCKS[KEY]["raw_sha256"])
        self.assertEqual(NORMALIZED_SHA256,
                         module._LOCKS[KEY]["normalized_sha256"])

    def test_the_row_field_guard_is_an_exhaustive_allowlist(self):
        """Design 5.1/10: the row field is `varying_profile`, the capability
        string `varying-uv-admission-v1` -- pure expression lowering, no ABI
        change, so the row carries the universal two fields and exactly one
        profile field. Landed keys answer from ALLOWED_ROW_FIELDS; grime's
        PREPARED contract adds its float-bit ingress companion field (the
        only other mechanism in grime's measured closure, design 3)."""
        module = _module()
        self.assertEqual({"defines", "program_key", "varying_profile"},
                         set(module.allowed_row_fields(KEY)))
        self.assertEqual(
            {KEY: module.allowed_row_fields(KEY),
             module.GRIME_KEY: frozenset({
                 "defines", "program_key", "varying_profile",
                 "grime_float_bits_ingress_profile"})},
            module.ALLOWED_ROW_FIELDS)
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)
        self.assertIsInstance(module.ALLOWED_ROW_FIELDS[KEY], frozenset)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("synth/shape:shape")

    def test_the_live_slice_carries_the_carrier_on_exactly_one_row(self):
        """The durable positive census: exactly the wobble and grime rows
        carry `varying_profile`, and no other profile field may ride them
        beyond each key's own allowlist (exact set equality at the
        load_slice arm)."""
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        self.assertEqual(
            sorted([KEY, module.GRIME_KEY]),
            [row["program_key"] for row in spec["programs"]
             if "varying_profile" in row],
            "only the wobble and grime rows may carry the varying carrier")
        row = next(row for row in spec["programs"]
                   if row["program_key"] == KEY)
        self.assertEqual(module.allowed_row_fields(KEY), frozenset(row))
        universe = {field for row in spec["programs"] for field in row
                    if field.endswith("_profile")}
        self.assertGreaterEqual(len(universe), 20, "universe looks truncated")
        allowed = module.allowed_row_fields(KEY)
        self.assertEqual({"defines", "program_key"},
                         allowed - universe - {"varying_profile"})

    def test_the_optional_proof_allowlist_is_exactly_the_sibling_fields(self):
        """Design 5.1: unlike the cellRefract array carrier, this module
        allows NO sibling proof field -- wobble carries none, and all four
        optional `fixed_*_proof` fields a TypedProgram can carry are frozen
        absent. Enumerated from the dataclass, not hand-listed, so a new proof
        field added elsewhere in the tree turns this red."""
        module = _module()
        carried = {
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_") and field.name.endswith("_proof")}
        self.assertEqual(
            ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
             "fixed_array_in_parameter_proof",
             "fixed_affine_centers13_proof"),
            module._OPTIONAL_PROOF_FIELDS)
        self.assertEqual(carried, set(module._OPTIONAL_PROOF_FIELDS))

    def test_the_alias_map_is_the_runtime_three_slot_uv_pair(self):
        """The port-side mirror of the runtime's soundness bound (design
        4.2/5.2): only `vUv`/`v_texCoord` alias `context.uv`. `vColor` belongs
        to the caller-supplied class (5.5) and to no typed-slice program."""
        module = _module()
        self.assertEqual(frozenset({"vUv", "v_texCoord"}),
                         module.UV_ALIAS_NAMES)
        self.assertNotIn("vColor", module.UV_ALIAS_NAMES)

    def test_every_failure_names_the_profile_not_a_module_global(self):
        module = _module()
        prefix = re.escape(f"{PROFILE}: ")
        program = _analyzed()
        for caller, arguments in (
                ("carrier", (program, RAW_SHA256, "wrong")),
                ("non-carrier", (_foreign(), _hash(FOREIGN_SOURCE), PROFILE)),
                ("row fields", ("synth/shape:shape",)),
                ("contract", ("synth/shape:shape",))):
            with self.subTest(site=caller), self.assertRaises(ValueError) as ctx:
                if caller == "carrier":
                    module.authenticate_varying_uv(*arguments)
                elif caller == "non-carrier":
                    module.authenticate_varying_uv(*arguments)
                elif caller == "row fields":
                    module.allowed_row_fields(*arguments)
                else:
                    module.varying_uv_contract(*arguments)
            self.assertRegex(str(ctx.exception), f"^{prefix}")


class VaryingUvAdmissionTests(unittest.TestCase):
    def test_authenticates_the_single_varying_by_object_identity(self):
        module = _module()
        program = _analyzed()
        admitted = module.authenticate_varying_uv(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(admitted, tuple)
        self.assertEqual(1, len(admitted))
        self.assertIs(program.interface_symbols[0], admitted[0])
        symbol = admitted[0]
        self.assertEqual((VARYING_ID, "v_texCoord", "vec2", "varying"),
                         (symbol.id, symbol.name, symbol.type.display(),
                          symbol.storage))
        self.assertFalse(symbol.writable)
        self.assertIs(program, module.apply_varying_uv(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "mutable-global-frame-shape-v1",
                        "const-global-nine-table-v1", "scalar-uint-xor-v1",
                        "mutable-global-nine-array-cellrefract-v1",
                        "mutable-global-nine-array-kaleido-v1",
                        "varying-uv-admission-v2"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_varying_uv(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_wobble_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_varying_uv(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "const-global-nine-table-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted varying-uv carrier"):
                module.authenticate_varying_uv(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_non_carrier_error_names_the_sole_landed_declaration(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_varying_uv(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        message = str(raised.exception)
        self.assertIn(SOURCE_PATH, message)
        self.assertIn(RAW_DECLARATION, message)
        self.assertIn("landed", message)

    def test_the_foreign_fixture_really_carries_the_construct(self):
        """The rejection at the boundary must be about identity, not about the
        construct being absent from the foreign program."""
        foreign = _foreign()
        self.assertEqual(1, len(foreign.interface_symbols))
        symbol = foreign.interface_symbols[0]
        self.assertEqual(("v_texCoord", "vec2", "varying"),
                         (symbol.name, symbol.type.display(), symbol.storage))

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_varying_uv(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_fails_the_caller_hash_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original + "\n// planted\n"
        self.assertNotEqual(original, mutated)
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_varying_uv(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        """The caller-hash lock and the raw-source lock are different locks."""
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_varying_uv(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("TAU = 6.28318530717959;",
                                   "TAU = 6.2831853071796;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_an_unanalyzed_body_status_fails_the_normalized_lock(self):
        module = _module()
        candidate = dataclasses.replace(_analyzed(), body_status="parsed")
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_define_drift_fails_the_defines_lock(self):
        """wobble's defines tuple is empty; injecting `MODE=4` changes nothing
        else (no `#if` blocks exist, the normalized source is byte-identical),
        so only the defines lock can catch a lying define set."""
        module = _module()
        candidate = _analyzed(defines={"MODE": 4})
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "exact preprocessor define lock mismatch")

    def test_typed_function_drift_fails_the_function_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        host = _fn(candidate, "applyWrap").body[0].expressions[0]
        object.__setattr__(host, "children",
                           (*host.children,
                            dataclasses.replace(host.children[0])))
        locks = _relocked_partial(module, candidate, "functions")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "typed function fingerprint drift"):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_fails_the_whole_program_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(
            candidate.declarations[0], "span",
            dataclasses.replace(candidate.declarations[0].span, end_column=29))
        locks = _relocked_partial(module, candidate, "whole")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "whole-program fingerprint drift"):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_also_fails_the_interface_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(
            candidate.declarations[0], "span",
            dataclasses.replace(candidate.declarations[0].span, end_column=29))
        locks = _relocked_partial(module, candidate, "interface")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "interface fingerprint drift"):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_varying_uv(
                        candidate, RAW_SHA256, PROFILE)


class VaryingUvIdentityTests(unittest.TestCase):
    """The varying itself: value locks ahead of the Symbol-hash identity."""

    def _symbol(self, candidate):
        return candidate.interface_symbols[0]

    def test_renamed_to_vcolor_fails_the_alias_map_lock(self):
        """`vColor` is the caller-supplied class (design 5.5): the alias-map
        rejection fires -- ahead of identity, which it must not hide behind."""
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "name", "vColor")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying name is not in the runtime uv alias map")

    def test_renamed_to_vuv_passes_the_alias_map_but_fails_identity(self):
        """`vUv` IS an alias name (it occurs in no corpus program), so the
        alias map lets it through and only the identity lock refuses it --
        the two locks are a sub-clause pair, each green without the other's
        mutation."""
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "name", "vUv")
        locks = _relocked(module, candidate)
        message = _expect(self, module, candidate, locks,
                          "varying symbol identity mismatch")
        self.assertNotIn("uv alias map", message)

    def test_retyped_to_vec3_fails_the_type_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "type",
                           named_type("vec3", {}))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks, "varying type mismatch")

    def test_made_writable_fails_the_storage_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "writable", True)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying storage mutability or direction mismatch")

    def test_storage_mutated_to_uniform_fails_the_storage_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "storage", "uniform")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying storage mutability or direction mismatch")

    def test_direction_mutated_to_out_fails_the_storage_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "direction", "out")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying storage mutability or direction mismatch")

    def test_a_retyped_span_fails_the_whole_file_span_lock(self):
        """Design 1.7: the Symbol's span IS the whole file (`1:1-107:1`);
        the lock refuses a 'fixed' declaration-site span."""
        module = _module()
        candidate = _analyzed()
        symbol = self._symbol(candidate)
        object.__setattr__(
            symbol, "span",
            dataclasses.replace(symbol.span, start_line=14, start_column=1,
                                end_line=14, end_column=18))
        locks = _relocked(module, candidate)
        message = _expect(self, module, candidate, locks,
                          "varying symbol span is not the whole-file span")
        self.assertNotIn("identity mismatch", message)

    def test_symbol_id_drift_fails_the_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._symbol(candidate), "id", 9001)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying symbol identity mismatch")

    def test_a_moved_raw_declaration_line_fails_the_raw_site_lock(self):
        """Extra spacing inside the declaration line changes the raw bytes but
        not the normalized source (the preprocessor drops the line), so with
        the coarse hashes refrozen only the raw-site lock answers."""
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("in vec2 v_texCoord;",
                                   "in  vec2  v_texCoord ;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        self.assertEqual(candidate.source, _analyzed().source,
                         "the normalized source must be unchanged")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying raw-source declaration site mismatch")

    def test_a_second_varying_fails_the_interface_cardinality_lock(self):
        module = _module()
        candidate = _analyzed()
        planted = dataclasses.replace(self._symbol(candidate), id=9001,
                                      name="vUv")
        object.__setattr__(
            candidate, "interface_symbols",
            (*candidate.interface_symbols, planted))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying interface census mismatch")

    def test_the_varying_must_not_appear_in_the_declaration_inventory(self):
        """Design 1.7: the varying exists only in `interface_symbols`. A
        declaration carrying the symbol is refrozen past the inventory lock so
        the no-declaration lock itself answers."""
        module = _module()
        candidate = _analyzed()
        symbol = self._symbol(candidate)
        from tools.glslcpp.frontend.typed_ir import TypedDeclaration
        extra = TypedDeclaration(
            symbol, symbol.type, symbol.span, None)
        object.__setattr__(candidate, "declarations",
                           (*candidate.declarations, extra))
        locks = _relocked(module, candidate)
        locks[KEY].update(_reinventory(module, candidate))
        _expect(self, module, candidate, locks,
                "varying appears in the global declaration inventory")

    def test_a_second_read_fails_the_read_census(self):
        """A read planted in `applyWrap` moves both the cardinality and the
        owner fields of the read census (design 6.4's 'moved to a different
        function' mutation)."""
        module = _module()
        candidate = _analyzed()
        planted = _id_clone(candidate, VARYING_ID)
        host = _fn(candidate, "applyWrap").body[0].expressions[0]
        object.__setattr__(host, "children", (*host.children, planted))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks, "varying read census mismatch")

    def test_a_missing_read_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        statement = _main(candidate).body[6]
        binary = statement.expressions[0].children[0]
        self.assertEqual("id", binary.children[0].kind)
        object.__setattr__(
            binary, "children",
            (dataclasses.replace(binary.children[1]), binary.children[1]))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks, "varying read census mismatch")

    def test_a_shifted_read_span_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        statement = _main(candidate).body[6]
        read = statement.expressions[0].children[0].children[0]
        object.__setattr__(
            read, "span",
            dataclasses.replace(read.span, start_column=25, end_column=35))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks, "varying read census mismatch")

    def test_the_read_made_into_a_write_fails_the_write_census(self):
        """Replace `fragColor`'s assignment target with the varying: a write
        appears where the frozen census is empty. Node counts are unchanged
        (one id node replaces another), so nothing but the write census moves."""
        module = _module()
        candidate = _analyzed()
        statement = _main(candidate).body[9]
        assign = statement.expressions[0]
        self.assertEqual("assign", assign.kind)
        object.__setattr__(
            assign, "children",
            (_id_clone(candidate, VARYING_ID), assign.children[1]))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks, "varying write census mismatch")

    def test_a_broken_contract_fails_the_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["contract"] = locks[KEY]["contract"]._replace(
            alias_of="context.frag_coord")
        _expect(self, module, candidate, locks,
                "varying emission contract mismatch")


class VaryingUvCensusTests(unittest.TestCase):
    """Every frozen figure is re-derived here, never transcribed."""

    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual(370, total)
        self.assertEqual(11, assigns)
        self.assertEqual(total, module._LOCKS[KEY]["total_nodes"])
        self.assertEqual(assigns, module._LOCKS[KEY]["total_assigns"])
        self.assertEqual(6, len(program.functions))
        self.assertEqual(6, module._LOCKS[KEY]["function_count"])
        self.assertEqual(9, len(program.declarations))
        self.assertEqual(9, module._LOCKS[KEY]["declaration_count"])
        inventory = module._LOCKS[KEY]["function_inventory"]
        self.assertEqual(inventory, tuple(
            (item.id, item.name, item.return_type.display(),
             tuple((p.id, p.name, p.type.display()) for p in item.parameters))
            for item in program.functions))
        self.assertEqual(module._LOCKS[KEY]["declaration_inventory"],
                         module._declaration_inventory(program))
        self.assertEqual(module._LOCKS[KEY]["initializer_census"],
                         module._initializer_census(program))
        resources = program.resources
        self.assertEqual((resources.uniforms, resources.samplers,
                          resources.outputs, resources.uses_texture,
                          resources.uses_derivatives),
                         module._LOCKS[KEY]["resources"])

    def test_the_call_graph_and_reachability_are_the_real_five_edges(self):
        module = _module()
        program = _analyzed()
        edges = module._call_graph(program)
        reachable, unreachable = module._reachability(program)
        self.assertEqual(5, len(edges))
        self.assertEqual(5, module._LOCKS[KEY]["call_edge_count"])
        self.assertEqual(module._sha(edges),
                         module._LOCKS[KEY]["call_graph_sha256"])
        self.assertEqual(tuple(range(17, 23)), reachable)
        self.assertEqual((), unreachable)
        self.assertEqual((reachable, unreachable),
                         (module._LOCKS[KEY]["reachable"],
                          module._LOCKS[KEY]["unreachable"]))
        proof = program.counted_loop_proof
        self.assertEqual(
            (0, 0, 0, 0, 0, True),
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic))

    def test_the_varying_is_one_symbol_with_the_whole_file_span(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(1, len(program.interface_symbols))
        symbol = program.interface_symbols[0]
        self.assertEqual((VARYING_ID, "v_texCoord", "vec2", "varying", False),
                         (symbol.id, symbol.name, symbol.type.display(),
                          symbol.storage, symbol.writable))
        self.assertEqual(SYMBOL_SPAN,
                         f"{symbol.span.start_line}:{symbol.span.start_column}"
                         f"-{symbol.span.end_line}:{symbol.span.end_column}")
        self.assertEqual(SYMBOL_SPAN, module._LOCKS[KEY]["symbol_span"])
        # The whole-file span is shared with the injected builtin: both are
        # constructed at the file span before declarations are inventoried.
        self.assertEqual(f"{program.builtin_symbols[0].span.start_line}:"
                         f"{program.builtin_symbols[0].span.start_column}-"
                         f"{program.builtin_symbols[0].span.end_line}:"
                         f"{program.builtin_symbols[0].span.end_column}",
                         SYMBOL_SPAN)
        self.assertEqual([], [item for item in program.declarations
                              if item.symbol.id == VARYING_ID],
                         "the varying is not in typed.declarations at all")

    def test_the_raw_declaration_site_is_wobble_line_fourteen(self):
        module = _module()
        raw = SOURCE.read_text(encoding="utf-8")
        lines = raw.split("\n")
        self.assertEqual(RAW_DECLARATION, lines[13])
        self.assertEqual((SOURCE_PATH, RAW_DECLARATION, 14),
                         module._LOCKS[KEY]["raw_declaration"])

    def test_the_read_census_is_one_read_in_main_at_the_exact_site(self):
        module = _module()
        program = _analyzed()
        reads, writes = module._reference_census(
            program, {VARYING_ID: "v_texCoord"})
        self.assertEqual(1, len(reads))
        self.assertEqual([], writes)
        record = reads[0].record
        self.assertEqual((VARYING_ID, "v_texCoord", MAIN_ID, "main"),
                         (record.symbol_id, record.symbol_name,
                          record.owner_id, record.owner_name))
        self.assertEqual("100:24-100:34", record.span)
        self.assertEqual(("binary", "+", "100:24-100:43"),
                         (record.parent_kind, record.parent_operator,
                          record.parent_span))
        self.assertEqual((6, "decl", "100:5-100:44"),
                         (record.statement_index, record.statement_kind,
                          record.statement_span))
        self.assertEqual(module._LOCKS[KEY]["reads"],
                         tuple(item.record for item in reads))
        self.assertEqual((), module._LOCKS[KEY]["writes"])

    def test_the_census_counts_every_reference_program_wide(self):
        """The read/write split must account for every `id` node referencing
        the varying symbol -- every function body AND every declaration
        initializer (the three const globals have initializers here, and the
        census walks them)."""
        module = _module()
        program = _analyzed()
        symbols = {VARYING_ID: "v_texCoord"}
        total = sum(1 for node in _nodes(program)
                    if node.kind == "id" and node.symbol_id in symbols)
        for declaration in program.declarations:
            if declaration.initializer is None:
                continue
            def expression(value):
                yield value
                for child in value.children:
                    yield from expression(child)
            for node in expression(declaration.initializer):
                total += node.kind == "id" and node.symbol_id in symbols
        reads, writes = module._reference_census(program, symbols)
        self.assertEqual(1, total)
        self.assertEqual(total, len(reads) + len(writes))

    def test_the_whole_corpus_carries_exactly_five_varying_programs(self):
        """Design 1.6 frozen: a corpus-wide analyze census -- four
        `vec2 v_texCoord` programs plus `wormhole:deposit`'s `vec4 vColor`,
        one varying each, zero everywhere else."""
        from tools.glslcpp import check_corpus
        root = check_corpus._corpus_root(ROOT)
        manifest = check_corpus._load_json(root / "manifest.json", "manifest")
        programs = check_corpus._validate_manifest(manifest)
        self.assertEqual(212, len(programs))
        carriers = {}
        for entry in programs:
            key = entry["program_key"]
            raw = (root / entry["source"]).read_text()
            analyzed = analyze_program(
                parse_program(raw, key,
                              generate_typed_slice._defaults(ROOT, key)),
                key)
            if analyzed.interface_symbols:
                carriers[key] = tuple(
                    (s.name, s.type.display()) for s in
                    analyzed.interface_symbols)
        self.assertEqual(
            {"filter/grime:grime": (("v_texCoord", "vec2"),),
             "filter/texture:texture": (("v_texCoord", "vec2"),),
             "filter/wobble:wobble": (("v_texCoord", "vec2"),),
             "filter/spookyTicker:spookyTicker": (("v_texCoord", "vec2"),),
             "filter/wormhole:deposit": (("vColor", "vec4"),)},
            carriers)


class VaryingUvLedgerTests(unittest.TestCase):
    def test_ledger_helper_rejects_duplicate_and_short_visitation(self):
        module = _module()
        marker = (object(), object())
        self.assertIsNone(module._check_ledger(list(marker), 2, "probe"))
        for broken in ([marker[0], marker[0]], [marker[0]],
                       [*marker, marker[1]]):
            with self.subTest(broken=len(broken)), \
                    self.assertRaisesRegex(ValueError,
                                           "probe visitation ledger mismatch"):
                module._check_ledger(broken, 2, "probe")

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "varying-uv visitation ledger mismatch"):
                module.authenticate_varying_uv(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(), RAW_SHA256, PROFILE)))

    def test_the_ledger_counts_the_symbol_and_the_read_node(self):
        module = _module()
        self.assertEqual(1 + READ_COUNT, module._CONSUMED_LEDGER,
                         "the varying symbol and each read node, once each")


class VaryingUvVocabularyTests(unittest.TestCase):
    def test_no_capability_or_type_vocabulary_growth(self):
        _module()
        for token in (PROFILE, "varying-uv", "varying", "v_texCoord"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)
                self.assertNotIn(token, generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))

    def test_the_module_never_grows_the_vocabulary_by_import(self):
        before = (generate_typed_slice.APPROVED_CAPABILITIES,
                  generate_typed_slice.APPROVED_TYPES)
        module = _module()
        module.authenticate_varying_uv(_analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(before[0], generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)


class VaryingUvNumericContractTests(unittest.TestCase):
    """Design 5.4: the uv numeric identity is empirical, not proven -- it is
    re-verified here every run and the bound is recorded, not assumed."""

    def test_the_contract_is_the_pure_lowering_shape(self):
        module = _module()
        contract = module.varying_uv_contract(KEY)
        self.assertEqual(VARYING_ID, contract.symbol_id)
        self.assertEqual("v_texCoord", contract.name)
        self.assertEqual("vec2", contract.glsl_type)
        self.assertEqual("context.uv", contract.alias_of)
        self.assertEqual("context.uv", contract.lowering_target)
        self.assertEqual("glsl::Vec2", contract.native_type)
        self.assertEqual("none", contract.kernel_signature_change)
        self.assertEqual("per-lane f32, single narrowing, double product",
                         contract.numeric_contract)
        self.assertEqual(
            ("F32((x + 0.5) * (1.0 / width))",
             "F32((height - y - 0.5) * (1.0 / height))"),
            contract.lane_expressions)
        self.assertEqual(3, len(contract.js_alias_evidence))
        self.assertTrue(all("glsl-runtime.js" in item or
                            "pass-runner.js" in item
                            for item in contract.js_alias_evidence))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.varying_uv_contract("synth/shape:shape")

    def test_the_evidence_strings_quote_the_runtime_aliasing_lines(self):
        module = _module()
        evidence = "\n".join(module.varying_uv_contract(KEY).js_alias_evidence)
        self.assertIn("glsl-runtime.js:95-99", evidence)
        self.assertIn("v_texCoord: new Float32Array(2)", evidence)
        self.assertIn("vColor: new Float32Array(4)", evidence)
        self.assertIn("glsl-runtime.js:148-151", evidence)
        self.assertIn("this.varyings.v_texCoord[0] = uv[0]", evidence)

    def test_the_uv_identity_holds_exhaustively_over_the_stated_bound(self):
        """For every size 1..1024 and every pixel position, both lanes
        including the y-flip: the JS double-product form (narrowed once at
        the Float32Array store) equals the C++ float-division form
        (`make_context`, pass_runner.cpp:20-29). Spot-checked at 2048/4096."""
        widths = list(range(1, 1025)) + [2048, 4096]
        for size in widths:
            lanes = list(range(size))
            # x-lane: JS F32((x + 0.5) * (1.0 / w)) vs C++ F32((x + 0.5f) / w)
            js_x = _batch_f32([(x + 0.5) * (1.0 / size) for x in lanes])
            cpp_x = _batch_f32([(_f32(x) + 0.5) / _f32(size) for x in lanes])
            # y-lane: JS F32((h - y - 0.5) * (1.0 / h)) vs
            #         C++ F32((h - y) - 0.5f) / h
            js_y = _batch_f32([(size - y - 0.5) * (1.0 / size)
                               for y in lanes])
            cpp_y = _batch_f32([(_f32(size - y) - 0.5) / _f32(size)
                                for y in lanes])
            self.assertEqual(js_x, cpp_x,
                             f"x-lane double product != float division at "
                             f"width {size}")
            self.assertEqual(js_y, cpp_y,
                             f"y-lane double product != float division at "
                             f"height {size}")


class VaryingUvLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK.

    For each row: mutate the tree (or the frozen record the lock owns),
    refreeze only the coarse hashes and the counters the mutation unavoidably
    moves, show the real module rejects with that lock's own message, then
    re-exec the module with exactly that predicate neutralized and show the
    message is gone.

    The frozen predicate census below is the mechanical form of the sweep's
    completeness claim: a predicate added to the module without a matching
    deletion test here reddens the census first."""

    _PREDICATES = (
        "_caller_source_hash_holds",
        "_defines_hold",
        "_raw_source_holds",
        "_normalized_source_holds",
        "_functions_fingerprint_holds",
        "_whole_program_fingerprint_holds",
        "_interface_fingerprint_holds",
        "_unrelated_proof_absent_holds",
        "_function_cardinality_holds",
        "_function_inventory_holds",
        "_declaration_inventory_holds",
        "_initializer_census_holds",
        "_resources_hold",
        "_call_graph_holds",
        "_node_census_holds",
        "_interface_cardinality_holds",
        "_uv_alias_name_holds",
        "_varying_storage_holds",
        "_varying_type_holds",
        "_symbol_span_holds",
        "_raw_declaration_holds",
        "_varying_identity_holds",
        "_no_declaration_inventory_entry_holds",
        "_read_census_holds",
        "_write_census_holds",
        "_varying_contract_holds",
    )

    def test_every_lock_predicate_has_a_named_deletion_test(self):
        module = _module()
        predicates = {
            name for name in dir(module)
            if name.startswith("_") and name.endswith(("_holds", "_hold"))
            and callable(getattr(module, name))}
        self.assertEqual(set(self._PREDICATES), predicates,
                         "a lock predicate exists without a named deletion "
                         "test (or vice versa)")
        for name in self._PREDICATES:
            with self.subTest(predicate=name):
                test_name = "test_" + name.lstrip("_").replace(
                    "_holds", "_lock").replace("_hold", "_lock")
                self.assertTrue(
                    hasattr(self, test_name),
                    f"{name} needs a named deletion test: {test_name}")

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            recallgraph=False, reinventory=False,
                            relock=None):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount(module, candidate))
        if recallgraph:
            overrides.update(_recallgraph(module, candidate))
        if reinventory:
            overrides.update(_reinventory(module, candidate))
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_varying_uv(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def _delete_and_compare_coarse(self, mutate, predicate, expected, upto):
        """The coarse-gate form: a coarse lock cannot be tested through a
        full relock (the relock refreezes it, tautologically satisfying it),
        so only the stages *before* ``upto`` are refrozen, the real module
        must reject with this stage's own message, and the scratch copy with
        the predicate deleted must reject with a *different* named message
        (or pass, when nothing else guards the field)."""
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked_partial(module, candidate, upto)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, re.escape(expected)):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_varying_uv(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                return None
            except ValueError as error:
                return str(error)

    @staticmethod
    def _varying(candidate):
        return candidate.interface_symbols[0]

    @staticmethod
    def _read_node(candidate):
        return _main(candidate).body[6].expressions[0].children[0].children[0]

    # --- coarse gate -------------------------------------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            1, len(scratch.authenticate_varying_uv(
                _analyzed(), "0" * 64, PROFILE)),
            "with the lock deleted nothing may reject a lying caller")

    def test_defines_lock(self):
        def mutate(candidate):
            from tools.glslcpp.frontend.typed_ir import PreprocessorDefine
            object.__setattr__(
                candidate, "preprocessor_defines",
                (PreprocessorDefine("MODE", "int", "4"),))
        self._delete_and_compare(
            mutate, "_defines_hold", "exact preprocessor define lock mismatch")

    def test_raw_source_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "raw_source",
                               candidate.raw_source + "// planted")
        survived = self._delete_and_compare_coarse(
            mutate, "_raw_source_holds", "raw source drift", upto="raw")
        self.assertIsNotNone(survived)
        self.assertIn("whole-program fingerprint drift", survived)

    def test_normalized_source_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "source", candidate.source + "\n")
        survived = self._delete_and_compare_coarse(
            mutate, "_normalized_source_holds", "normalized source drift",
            upto="normalized")
        self.assertIsNotNone(survived)
        self.assertIn("whole-program fingerprint drift", survived)

    def test_functions_fingerprint_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "applyWrap").body[0].expressions[0]
            object.__setattr__(host, "children",
                               (*host.children,
                                dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare_coarse(
            mutate, "_functions_fingerprint_holds",
            "typed function fingerprint drift", upto="functions")
        self.assertIsNotNone(survived)
        self.assertIn("whole-program fingerprint drift", survived)

    def test_whole_program_fingerprint_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "local_type_names", (*candidate.local_type_names,
                                                "planted"))
        survived = self._delete_and_compare_coarse(
            mutate, "_whole_program_fingerprint_holds",
            "whole-program fingerprint drift", upto="whole")
        self.assertIsNotNone(survived)
        self.assertIn("interface fingerprint drift", survived)

    def test_interface_fingerprint_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "builtin_symbols",
                (*candidate.builtin_symbols,
                 dataclasses.replace(candidate.builtin_symbols[0], id=9001)))
        survived = self._delete_and_compare_coarse(
            mutate, "_interface_fingerprint_holds",
            "interface fingerprint drift", upto="interface")
        self.assertIsNone(
            survived,
            "nothing but the interface fingerprint guards builtin_symbols")

    def test_unrelated_proof_absent_lock(self):
        def mutate(candidate):
            return dataclasses.replace(
                candidate, fixed_nine_table_proof=object())
        # replace() returns a new program; _delete_and_compare mutates in
        # place, so plant the field via __setattr__ on a field that allows it.
        def mutate(candidate):
            object.__setattr__(candidate, "fixed_nine_table_proof", object())
        self._delete_and_compare(
            mutate, "_unrelated_proof_absent_holds",
            "unrelated proof carrier is not absent")

    def test_function_cardinality_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "functions",
                               candidate.functions[:-1])
        survived = self._delete_and_compare(
            mutate, "_function_cardinality_holds",
            "function cardinality mismatch", recount=True, recallgraph=True)
        self.assertIsNotNone(survived)
        self.assertIn("function inventory mismatch", survived)

    def test_function_inventory_lock(self):
        def mutate(candidate):
            function = _fn(candidate, "applyWrap")
            object.__setattr__(
                candidate, "functions",
                tuple(dataclasses.replace(item, signature=dataclasses.replace(
                    item.signature, name="planted"))
                      if item is function else item
                      for item in candidate.functions))
        survived = self._delete_and_compare(
            mutate, "_function_inventory_holds", "function inventory mismatch")
        self.assertIsNone(survived)

    def test_declaration_inventory_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[0]
            symbol = dataclasses.replace(declaration.symbol, id=9001,
                                         name="planted")
            extra = dataclasses.replace(declaration, symbol=symbol)
            object.__setattr__(candidate, "declarations",
                               (*candidate.declarations, extra))
        survived = self._delete_and_compare(
            mutate, "_declaration_inventory_holds",
            "global declaration inventory mismatch", recount=True)
        self.assertIsNone(survived)

    def test_initializer_census_lock(self):
        def mutate(candidate):
            host = candidate.declarations[0]
            object.__setattr__(
                host, "initializer",
                dataclasses.replace(
                    _fn(candidate, "applyWrap").body[0].expressions[0]))
        self._delete_and_compare(
            mutate, "_initializer_census_holds",
            "global declaration initializer census mismatch", recount=True,
            reinventory=True)

    def test_resources_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources, uses_texture=False))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "applyWrap").body[0].expressions[0]
            planted = dataclasses.replace(
                _main(candidate).body[7].expressions[0].children[1])
            self.assertEqual("call", planted.kind)
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(
            survived,
            "with the counters refrozen, the edge set is the only guard")

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "applyWrap").body[0].expressions[0]
            object.__setattr__(host, "children",
                               (*host.children,
                                dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(
            survived,
            "an added expression node is caught by the census alone")

    # --- the varying itself ------------------------------------------------

    def test_interface_cardinality_lock(self):
        def mutate(candidate):
            planted = dataclasses.replace(self._varying(candidate), id=9001,
                                          name="vUv")
            object.__setattr__(
                candidate, "interface_symbols",
                (*candidate.interface_symbols, planted))
        survived = self._delete_and_compare(
            mutate, "_interface_cardinality_holds",
            "varying interface census mismatch")
        self.assertIsNone(
            survived,
            "the census is the only guard against a second varying")

    def test_uv_alias_name_lock(self):
        def mutate(candidate):
            object.__setattr__(self._varying(candidate), "name", "vColor")
        survived = self._delete_and_compare(
            mutate, "_uv_alias_name_holds",
            "varying name is not in the runtime uv alias map")
        self.assertIsNotNone(survived)
        self.assertIn("varying symbol identity mismatch", survived)

    def test_varying_storage_lock(self):
        def mutate(candidate):
            object.__setattr__(self._varying(candidate), "writable", True)
        survived = self._delete_and_compare(
            mutate, "_varying_storage_holds",
            "varying storage mutability or direction mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("varying symbol identity mismatch", survived)

    def test_varying_type_lock(self):
        def mutate(candidate):
            object.__setattr__(self._varying(candidate), "type",
                               named_type("vec3", {}))
        survived = self._delete_and_compare(
            mutate, "_varying_type_holds", "varying type mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("varying symbol identity mismatch", survived)

    def test_symbol_span_lock(self):
        def mutate(candidate):
            symbol = self._varying(candidate)
            object.__setattr__(
                symbol, "span",
                dataclasses.replace(symbol.span, start_line=14))
        survived = self._delete_and_compare(
            mutate, "_symbol_span_holds",
            "varying symbol span is not the whole-file span")
        self.assertIsNotNone(survived)
        self.assertIn("varying symbol identity mismatch", survived)

    def test_raw_declaration_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "raw_source",
                               candidate.raw_source.replace(
                                   "in vec2 v_texCoord;",
                                   "in  vec2 v_texCoord;"))
        survived = self._delete_and_compare(
            mutate, "_raw_declaration_holds",
            "varying raw-source declaration site mismatch")
        self.assertIsNone(survived)

    def test_varying_identity_lock(self):
        def mutate(candidate):
            object.__setattr__(self._varying(candidate), "id", 9001)
        survived = self._delete_and_compare(
            mutate, "_varying_identity_holds",
            "varying symbol identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("varying read census mismatch", survived)

    def test_no_declaration_inventory_entry_lock(self):
        def mutate(candidate):
            symbol = self._varying(candidate)
            from tools.glslcpp.frontend.typed_ir import TypedDeclaration
            extra = TypedDeclaration(symbol, symbol.type, symbol.span, None)
            object.__setattr__(candidate, "declarations",
                               (*candidate.declarations, extra))
        survived = self._delete_and_compare(
            mutate, "_no_declaration_inventory_entry_holds",
            "varying appears in the global declaration inventory",
            reinventory=True)
        self.assertIsNone(survived)

    def test_read_census_lock(self):
        def mutate(candidate):
            object.__setattr__(
                self._read_node(candidate), "span",
                dataclasses.replace(self._read_node(candidate).span,
                                    start_column=25))
        survived = self._delete_and_compare(
            mutate, "_read_census_holds", "varying read census mismatch")
        self.assertIsNone(survived)

    def test_write_census_lock(self):
        def mutate(candidate):
            statement = _main(candidate).body[9]
            assign = statement.expressions[0]
            object.__setattr__(
                assign, "children",
                (_id_clone(candidate, VARYING_ID), assign.children[1]))
        survived = self._delete_and_compare(
            mutate, "_write_census_holds", "varying write census mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("visitation ledger mismatch", survived,
                      "the ledger is the write census's second guard")

    def test_varying_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["contract"] = locks[KEY]["contract"]._replace(
            alias_of="context.frag_coord")
        _expect(self, module, candidate, locks,
                "varying emission contract mismatch")
        scratch = _scratch(module, "_varying_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertEqual(
                1, len(scratch.authenticate_varying_uv(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)))


class VaryingUvPreparedKeyTests(unittest.TestCase):
    def test_wobble_and_grime_are_both_landed_and_nothing_is_prepared(self):
        """Both records are now LANDED. wobble moved out of the prepared set
        when its row landed as typed row 189; grime made the same one-line
        move when its row landed as typed row 191, together with its float-bit
        ingress companion -- the carrier's whole closure behind the varying.
        The prepared set is empty: texture and spookyTicker deliberately hold
        no record at all (design 5.2), so the varying being their FIRST
        reported blocker understates the three mechanisms they need."""
        module = _module()
        self.assertEqual((KEY, module.GRIME_KEY), module.KEYS)
        self.assertEqual({KEY: PROFILE, module.GRIME_KEY: PROFILE},
                         module.PROFILES)
        self.assertEqual(frozenset({KEY, module.GRIME_KEY}),
                         module.VARYING_UV_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual({}, module.PREPARED_PROFILES)
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)
        self.assertIn(KEY, module.ALLOWED_ROW_FIELDS)
        self.assertIn(module.GRIME_KEY, module.ALLOWED_ROW_FIELDS)
        self.assertIn(KEY, module._LOCKS)
        self.assertEqual(PROFILE, module._LOCKS[KEY]["profile"])
        self.assertEqual(
            (KEY, module.GRIME_KEY),
            tuple([*module.KEYS, *module.PREPARED_KEYS]))
        # both records authenticate their real programs right now
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(), RAW_SHA256, PROFILE)))
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(
                    raw=(CORPUS / "filter/grime/grime.glsl").read_text(
                        encoding="utf-8"),
                    key=module.GRIME_KEY),
                module._LOCKS[module.GRIME_KEY]["raw_sha256"], PROFILE)))

    def test_only_wobble_and_grime_are_frozen_and_the_rest_deferred(self):
        """Design 5.2: a record must not be frozen before its program's
        whole closure is admitted. grime's closure IS identified and carried
        (the five floatBitsToUint sites), so its record exists; texture's
        and spookyTicker's closures are three mechanisms deep and
        wormhole:deposit's vColor is the caller-supplied class -- none of
        them has a record."""
        module = _module()
        self.assertEqual((KEY, module.GRIME_KEY), tuple(module._LOCKS))
        self.assertNotIn("filter/texture:texture", module._LOCKS)
        self.assertNotIn("filter/spookyTicker:spookyTicker", module._LOCKS)
        self.assertNotIn("filter/wormhole:deposit", module._LOCKS)


if __name__ == "__main__":
    unittest.main()
