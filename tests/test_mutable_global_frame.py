"""Focused RED/GREEN proof for the two `synth/shape` mutable global frames.

Written before ``tools/glslcpp/frontend/mutable_global_frame_profile.py``
existed; the first run of this file reported ``ModuleNotFoundError`` from
``_module`` for every test in it.

``synth/shape:shape`` declares two mutable, uninitialised, file-scope globals
one line apart::

    31|float aspectRatio;
    32|vec2 globalCoord;

The validator reports only the first. Both must be admitted, and the two do
**not** share a numeric contract -- in the shipped JavaScript ``aspectRatio``
is a plain Number (a double, never narrowed to f32) while ``globalCoord`` is a
``Float32Array`` with per-lane f32 narrowing. Every lock below therefore treats
them separately, and two of the deletion experiments exist purely to prove that
the two contracts are not one lock wearing two names.

Three testing rules inherited from the Shapes slice apply directly:

1. ``Symbol`` embeds its declaration span, so a value-level mutation shifts
   every enclosing node hash. The production module evaluates storage,
   mutability, initialiser-absence and the numeric contracts **ahead** of node
   identity, and each lock is proved load-bearing by *deleting the lock* in a
   scratch copy -- never by mutating the input and watching something raise.
2. Every mutation test refreezes **only** the coarse hash fields and asserts
   that no coarse message fired. Semantic fields keep their frozen originals.
3. The census walks global declaration initializers as well as function
   bodies. For this mechanism that is the whole subject matter, so a node
   planted in ``PI``'s initializer must be caught by the census rather than by
   a refreezable coarse hash.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import pathlib
import types
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.mutable_global_frame_profile"

KEY = "synth/shape:shape"
PROFILE = "mutable-global-frame-shape-v1"
SOURCE_PATH = "synth/shape/shape.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "d917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f"
NORMALIZED_SHA256 = (
    "83bf41728f8e10ed08ec04a9899f35d60b476700703d4db851f57289cf6f1b00")

ASPECT_ID = 14
COORD_ID = 15
ASPECT_ORDINAL = 13
COORD_ORDINAL = 14
MAIN_ID = 105

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
    "out vec4 fragColor;\n"
    "float gain;\n"
    "void main() {\n"
    "    gain = 2.0;\n"
    "    fragColor = vec4(gain, gain, gain, 1.0);\n"
    "}\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("mutable-global frame profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock predicates.

    A neutralized predicate always reports "holds", which is exactly what
    removing the lock from the module source would do. The live module object
    is never touched, so these tests cannot leak state into each other.
    """
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
              defines: dict | None = None, parse_key: str | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, KEY)
               if defines is None else defines)
    parse_key = key if parse_key is None else parse_key
    return analyze_program(parse_program(raw, parse_key, defines), key)


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _main(program):
    return next(item for item in program.functions if item.name == "main")


def _fn(program, name):
    return next(item for item in program.functions if item.name == name)


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


def _relocked(module, candidate, **overrides):
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen.

    Deliberately does **not** refreeze any semantic field: the declaration
    inventory, the ordinals, the numeric contracts, the write/read censuses and
    every node hash keep their frozen originals. Refreezing those would hand
    the mutation to the very lock under test and make the experiment vacuous.
    """
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        locks[KEY].update(values[name])
    locks[KEY].update(overrides)
    return locks


def _relocked_partial(module, candidate, upto):
    """Refreeze only the coarse fields the module checks *before* ``upto``."""
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        if name == upto:
            return locks
        locks[KEY].update(values[name])
    raise AssertionError(f"{upto} is not a coarse gate stage")


def _recount(module, candidate):
    """Refreeze only the two program-wide *cardinality* counters."""
    total, assigns = module._node_census(candidate)
    return {"total_nodes": total, "total_assigns": assigns}


def _authenticate(module, candidate, locks, profile=PROFILE):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_mutable_global_frame(
            candidate, locks[KEY]["raw_sha256"], profile)


def _expect(test, module, candidate, locks, expected, profile=PROFILE):
    with test.assertRaises(ValueError) as raised:
        _authenticate(module, candidate, locks, profile)
    message = str(raised.exception)
    for coarse in COARSE:
        test.assertNotIn(coarse, message,
                         f"{expected!r} was absorbed by the coarse gate")
    test.assertIn(expected, message)
    return message


class MutableGlobalFramePublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual((KEY, module.NOISE_KEY), module.KEYS)
        self.assertEqual(
            {KEY: PROFILE, module.NOISE_KEY: module.NOISE_PROFILE},
            module.PROFILES)
        self.assertEqual(
            frozenset({KEY, module.NOISE_KEY}),
            module.MUTABLE_GLOBAL_FRAME_KEYS)
        self.assertIsInstance(module.MUTABLE_GLOBAL_FRAME_KEYS, frozenset)
        self.assertEqual(KEY, module.SHAPE_KEY)
        self.assertEqual(PROFILE, module.SHAPE_PROFILE)
        for name in ("KEYS", "PROFILES", "MUTABLE_GLOBAL_FRAME_KEYS",
                     "SHAPE_KEY", "SHAPE_PROFILE",
                     "REQUIRED_COMPANION_PROFILES", "ALLOWED_ROW_FIELDS",
                     "allowed_row_fields", "frame_contract",
                     "authenticate_mutable_global_frame",
                     "apply_mutable_global_frame"):
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

    def test_companion_carrier_data_is_the_reused_scalar_uint_xor_profile(self):
        module = _module()
        self.assertEqual(
            {KEY: (("scalar_uint_xor_profile", "scalar-uint-xor-v1"),),
             module.NOISE_KEY: (
                 ("runtime_loop_bound_profile", "runtime-loop-bound-v1"),
                 ("scalar_uint_xor_profile", "scalar-uint-xor-v1"))},
            module.REQUIRED_COMPANION_PROFILES)

    def test_the_row_field_guard_is_an_exhaustive_allowlist(self):
        """An allowlist, not a denylist.

        `generate_typed_slice`'s allowed-field arm compares
        `set(item) != expected`, so equality with this set discharges design
        §7.2 row 20's "every other profile absent" by construction. A denylist
        naming a handful of sibling profiles would silently admit every one it
        failed to name.
        """
        module = _module()
        self.assertEqual(
            {"defines", "program_key", "scalar_uint_xor_profile",
             "mutable_global_frame_profile"},
            set(module.allowed_row_fields(KEY)))
        self.assertEqual(
            {KEY: module.allowed_row_fields(KEY),
             module.NOISE_KEY: module.allowed_row_fields(module.NOISE_KEY)},
            module.ALLOWED_ROW_FIELDS)
        self.assertIsInstance(module.ALLOWED_ROW_FIELDS[KEY], frozenset)
        self.assertFalse(hasattr(module, "FORBIDDEN_COMPANION_FIELDS"),
                         "the denylist must not come back")
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("classicNoisedeck/shapes:shapes")

    def test_the_allowlist_excludes_every_other_live_row_profile_field(self):
        """Checked against the REAL row-field universe, not a hand-list.

        Every `*_profile` field any row in the live slice carries must be
        excluded, except the one companion Shape genuinely requires.
        """
        import json
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        # EVERY OTHER row -- Shape's own row is excluded, because it is now in
        # the live slice and contributes `mutable_global_frame_profile` to the
        # universe itself. Before the row landed this read `spec["programs"]`
        # whole and closed with "the new field must not already be in the
        # slice", which was a pre-landing precondition rather than a durable
        # contract. The durable form is the positive one below: no OTHER row
        # may carry the field, which is the single-carrier census.
        universe = {field for row in spec["programs"] for field in row
                    if field.endswith("_profile")
                    and row["program_key"] != KEY}
        self.assertGreaterEqual(len(universe), 20, "universe looks truncated")
        allowed = module.allowed_row_fields(KEY)
        self.assertEqual(
            {"mutable_global_frame_profile", "scalar_uint_xor_profile"},
            universe & allowed)
        for field in sorted(universe - allowed):
            with self.subTest(field=field):
                self.assertNotIn(field, allowed)
        # The two fields Shape's row does carry, one of them brand new.
        self.assertIn("scalar_uint_xor_profile", allowed)
        self.assertIn("mutable_global_frame_profile", allowed)
        self.assertEqual(
            [module.NOISE_KEY, KEY],
            [row["program_key"] for row in spec["programs"]
             if "mutable_global_frame_profile" in row])

    def test_frame_contract_is_the_const_reference_pixel_scope_shape(self):
        module = _module()
        contract = module.frame_contract(KEY)
        self.assertEqual("Frame", contract.struct_name)
        self.assertEqual("frame", contract.instance_name)
        self.assertEqual("pixel", contract.instance_scope)
        self.assertTrue(contract.value_initialized)
        self.assertEqual("const Frame&", contract.helper_parameter_qualifier)
        self.assertEqual(2, contract.helper_parameter_ordinal)
        self.assertEqual("main", contract.writer_function)
        self.assertEqual(("aspectRatio", "globalCoord"),
                         tuple(item.name for item in contract.fields))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.frame_contract("classicNoisedeck/shapes:shapes")


class MutableGlobalFrameAdmissionTests(unittest.TestCase):
    def test_authenticates_both_declarations_in_declaration_order(self):
        module = _module()
        program = _analyzed()
        admitted = module.authenticate_mutable_global_frame(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(admitted, tuple)
        self.assertEqual(2, len(admitted),
                         "the validator reports one site; there are two")
        self.assertIs(program.declarations[ASPECT_ORDINAL], admitted[0])
        self.assertIs(program.declarations[COORD_ORDINAL], admitted[1])
        self.assertEqual(["aspectRatio", "globalCoord"],
                         [item.symbol.name for item in admitted])
        self.assertEqual(["float", "vec2"],
                         [item.type.display() for item in admitted])
        for item in admitted:
            self.assertEqual("global", item.symbol.storage)
            self.assertTrue(item.symbol.writable)
            self.assertIsNone(item.initializer)
        self.assertIs(program, module.apply_mutable_global_frame(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "mutable-global-frame-noise-v1",
                        "scalar-uint-xor-v1", "shapes-rvalue-assign-v1",
                        "mutable-global-frame-shape-v2"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_mutable_global_frame(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_shape_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_mutable_global_frame(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "scalar-uint-xor-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted mutable-global frame carrier"):
                module.authenticate_mutable_global_frame(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_foreign_fixture_really_carries_the_construct(self):
        """The new rejection at the widened boundary must be about identity,
        not about the construct being absent from the foreign program."""
        foreign = _foreign()
        mutable = [item for item in foreign.declarations
                   if item.symbol.storage == "global"
                   and item.initializer is None]
        self.assertEqual(["gain"], [item.symbol.name for item in mutable])
        self.assertTrue(mutable[0].symbol.writable)

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_frame(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_fails_the_caller_hash_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original + "\n// planted\n"
        self.assertNotEqual(original, mutated)
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_frame(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        """The caller-hash lock and the raw-source lock are different locks.

        A caller that reports the frozen hash while handing over a drifted
        program gets past the first and must be stopped by the second.
        """
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_mutable_global_frame(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("const float PI = 3.14159265359;",
                                   "const float PI = 3.14159265358;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_mutable_global_frame(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_typed_function_drift_fails_the_function_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        host = _fn(candidate, "map").body[0].expressions[0]
        object.__setattr__(host, "children",
                           (*host.children,
                            dataclasses.replace(host.children[0])))
        locks = _relocked_partial(module, candidate, "functions")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "typed function fingerprint drift"):
            module.authenticate_mutable_global_frame(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_fails_the_whole_program_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate.declarations[11].initializer,
                           "literal", "3.0")
        locks = _relocked_partial(module, candidate, "whole")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "whole-program fingerprint drift"):
            module.authenticate_mutable_global_frame(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_also_fails_the_interface_lock(self):
        """The interface fingerprint is a subset of the whole-program one, so
        it can only be reached with the whole-program hash refrozen."""
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate.declarations[11].initializer,
                           "literal", "3.0")
        locks = _relocked_partial(module, candidate, "interface")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "interface fingerprint drift"):
            module.authenticate_mutable_global_frame(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_mutable_global_frame(
                        candidate, RAW_SHA256, PROFILE)

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        baseline = _analyzed()
        cases = [
            ("value drift", _analyzed(defines={"LOOP_A_OFFSET": 41,
                                               "LOOP_B_OFFSET": 30})),
            ("second value drift", _analyzed(defines={"LOOP_A_OFFSET": 40,
                                                      "LOOP_B_OFFSET": 31})),
            ("name drift", _analyzed(defines={"LOOP_A_OFFSET_X": 40,
                                              "LOOP_B_OFFSET": 30})),
            ("extra define", _analyzed(defines={"LOOP_A_OFFSET": 40,
                                                "LOOP_B_OFFSET": 30,
                                                "EXTRA": 7})),
            ("defines erased", _analyzed(defines={})),
            ("order drift", dataclasses.replace(
                baseline, preprocessor_defines=tuple(
                    reversed(baseline.preprocessor_defines)))),
        ]
        for label, candidate in cases:
            with self.subTest(axis=label):
                _expect(self, module, candidate,
                        _relocked(module, candidate), expected)


class MutableGlobalFrameDeclarationTests(unittest.TestCase):
    """Identity, order, type, mutability, uninitialisedness -- per field."""

    def test_the_two_admitted_records_are_the_real_declarations(self):
        module = _module()
        program = _analyzed()
        records = module._LOCKS[KEY]["admitted"]
        self.assertEqual(2, len(records))
        for record in records:
            declaration = program.declarations[record.ordinal]
            self.assertEqual(record.symbol_id, declaration.symbol.id)
            self.assertEqual(record.name, declaration.symbol.name)
            self.assertEqual(record.glsl_type, declaration.type.display())
            self.assertEqual(record.storage, declaration.symbol.storage)
            self.assertEqual(record.writable, declaration.symbol.writable)
            self.assertIsNone(declaration.initializer)
            self.assertEqual(record.declaration_span, module._span(declaration))
            self.assertEqual(record.symbol_span,
                             module._span(declaration.symbol))
            self.assertEqual(record.declaration_sha256, module._sha(declaration))
            self.assertEqual(record.symbol_sha256,
                             module._sha(declaration.symbol))
        self.assertEqual((ASPECT_ORDINAL, COORD_ORDINAL),
                         tuple(item.ordinal for item in records))
        self.assertEqual((ASPECT_ID, COORD_ID),
                         tuple(item.symbol_id for item in records))

    def test_adjacency_is_immediately_after_the_const_float_TAU(self):
        module = _module()
        program = _analyzed()
        preceding = program.declarations[ASPECT_ORDINAL - 1]
        self.assertEqual("TAU", preceding.symbol.name)
        self.assertEqual("const", preceding.symbol.storage)
        self.assertEqual("float", preceding.type.display())
        self.assertEqual((ASPECT_ORDINAL - 1, preceding.symbol.id),
                         module._LOCKS[KEY]["preceding"])

    def test_the_inventory_covers_all_fifteen_declarations(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(15, len(program.declarations))
        self.assertEqual(15, module._LOCKS[KEY]["declaration_count"])
        self.assertEqual(15, len(module._LOCKS[KEY]["declaration_inventory"]))
        self.assertEqual(module._LOCKS[KEY]["declaration_inventory"],
                         module._declaration_inventory(program))
        # Exactly two are mutable file-scope globals; the rest are uniforms,
        # the output, and two consts. `fragColor` is writable too -- storage,
        # not writability, is what selects the sub-shape.
        mutable = [item for item in program.declarations
                   if item.symbol.storage == "global"]
        self.assertEqual(["aspectRatio", "globalCoord"],
                         [item.symbol.name for item in mutable])
        writable = [item.symbol.name for item in program.declarations
                    if item.symbol.writable]
        self.assertEqual(["fragColor", "aspectRatio", "globalCoord"], writable)

    def test_uninitialisedness_is_the_defining_property_of_the_sub_shape(self):
        module = _module()
        program = _analyzed()
        without = [item.symbol.name for item in program.declarations
                   if item.initializer is None]
        self.assertIn("aspectRatio", without)
        self.assertIn("globalCoord", without)
        with_initializer = [item.symbol.name for item in program.declarations
                            if item.initializer is not None]
        self.assertEqual(["PI", "TAU"], with_initializer)

    def test_reordering_the_two_globals_fails_the_ordinal_lock(self):
        module = _module()
        candidate = _analyzed()
        declarations = list(candidate.declarations)
        declarations[ASPECT_ORDINAL], declarations[COORD_ORDINAL] = (
            declarations[COORD_ORDINAL], declarations[ASPECT_ORDINAL])
        object.__setattr__(candidate, "declarations", tuple(declarations))
        _expect(self, module, candidate, _relocked(module, candidate),
                "admitted global declaration ordinal or adjacency mismatch")

    def test_a_relocated_pair_that_leaves_TAU_behind_fails_adjacency(self):
        module = _module()
        candidate = _analyzed()
        declarations = list(candidate.declarations)
        # Swap TAU with the output so the pair is no longer preceded by TAU,
        # while both admitted ordinals stay at 13 and 14.
        declarations[10], declarations[12] = declarations[12], declarations[10]
        object.__setattr__(candidate, "declarations", tuple(declarations))
        _expect(self, module, candidate, _relocked(module, candidate),
                "admitted global declaration ordinal or adjacency mismatch")


class MutableGlobalFrameNumericContractTests(unittest.TestCase):
    """The two globals are one line apart and DO NOT share a contract."""

    def test_aspect_ratio_is_a_double_with_no_narrowing(self):
        module = _module()
        field = module.frame_contract(KEY).fields[0]
        self.assertEqual("aspectRatio", field.name)
        self.assertEqual("float", field.glsl_type)
        self.assertEqual("double", field.native_type)
        self.assertEqual(1, field.lane_count)
        self.assertEqual("none", field.narrowing)
        self.assertEqual("double", field.js_number_kind)
        self.assertEqual("0", field.js_initializer)

    def test_global_coord_is_a_vec2_with_per_lane_f32_narrowing(self):
        module = _module()
        field = module.frame_contract(KEY).fields[1]
        self.assertEqual("globalCoord", field.name)
        self.assertEqual("vec2", field.glsl_type)
        self.assertEqual("glsl::Vec2", field.native_type)
        self.assertEqual(2, field.lane_count)
        self.assertEqual("per-lane-f32", field.narrowing)
        self.assertEqual("float32-array", field.js_number_kind)
        self.assertEqual("new Float32Array([0, 0])", field.js_initializer)

    def test_the_two_contracts_are_not_the_same_lock_wearing_two_names(self):
        module = _module()
        first, second = module.frame_contract(KEY).fields
        for attribute in ("glsl_type", "native_type", "lane_count",
                          "narrowing", "js_number_kind", "js_initializer"):
            with self.subTest(attribute=attribute):
                self.assertNotEqual(getattr(first, attribute),
                                    getattr(second, attribute))

    def test_the_frozen_mapping_agrees_with_the_emitter_local_type(self):
        """`local_type()` is what makes the double contract correct by
        construction. The profile asserts the mapping instead of inheriting
        it, so a future change to `local_type()` turns this red."""
        module = _module()
        emit = importlib.import_module("tools.glslcpp.emit_typed_cpp")
        self.assertEqual("double", module._LOCAL_TYPE_CONTRACT["float"],
                         "the JS keeps aspectRatio a plain Number")
        self.assertEqual("glsl::Vec2", module._LOCAL_TYPE_CONTRACT["vec2"])
        self.assertEqual("glsl::Vec2", emit._TYPES["vec2"])
        self.assertIn('return "double" if value.display() == "float"',
                      pathlib.Path(emit.__file__).read_text(encoding="utf-8"))

    def test_a_narrowed_aspect_ratio_contract_fails_only_its_own_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        broken = locks[KEY]["admitted"][0].field._replace(
            narrowing="per-lane-f32")
        locks[KEY]["admitted"] = (
            locks[KEY]["admitted"][0]._replace(field=broken),
            locks[KEY]["admitted"][1])
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            fields=(broken, locks[KEY]["admitted"][1].field))
        message = _expect(self, module, candidate, locks,
                          "aspectRatio numeric contract mismatch")
        self.assertNotIn("globalCoord numeric contract mismatch", message)

    def test_an_unnarrowed_global_coord_contract_fails_only_its_own_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        broken = locks[KEY]["admitted"][1].field._replace(narrowing="none")
        locks[KEY]["admitted"] = (
            locks[KEY]["admitted"][0],
            locks[KEY]["admitted"][1]._replace(field=broken))
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            fields=(locks[KEY]["admitted"][0].field, broken))
        message = _expect(self, module, candidate, locks,
                          "globalCoord numeric contract mismatch")
        self.assertNotIn("aspectRatio numeric contract mismatch", message)

    def test_a_float_mapped_to_float_fails_only_the_aspect_ratio_lock(self):
        module = _module()
        candidate = _analyzed()
        contract = dict(module._LOCAL_TYPE_CONTRACT)
        contract["float"] = "float"
        with mock.patch.object(module, "_LOCAL_TYPE_CONTRACT", contract):
            message = _expect(self, module, candidate,
                              _relocked(module, candidate),
                              "aspectRatio numeric contract mismatch")
        self.assertNotIn("globalCoord numeric contract mismatch", message)

    def test_a_vec2_mapped_elsewhere_fails_only_the_global_coord_lock(self):
        module = _module()
        candidate = _analyzed()
        contract = dict(module._LOCAL_TYPE_CONTRACT)
        contract["vec2"] = "glsl::Vec3"
        with mock.patch.object(module, "_LOCAL_TYPE_CONTRACT", contract):
            message = _expect(self, module, candidate,
                              _relocked(module, candidate),
                              "globalCoord numeric contract mismatch")
        self.assertNotIn("aspectRatio numeric contract mismatch", message)

    def test_a_mutable_reference_helper_parameter_fails_the_frame_contract(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            helper_parameter_qualifier="Frame&", helper_parameter="Frame& frame")
        _expect(self, module, candidate, locks,
                "frame emission contract mismatch")

    def test_a_frame_that_is_not_value_initialised_fails_the_frame_contract(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            value_initialized=False)
        _expect(self, module, candidate, locks,
                "frame emission contract mismatch")


class MutableGlobalFrameCensusTests(unittest.TestCase):
    def test_the_admitted_symbol_map_is_derived_per_key_not_at_import(self):
        """The shared-module shape only pays off if the symbol map follows the
        selected key. Bound at import it would run Shape's ids 14/15 against
        `synth/noise:noise`'s tree once that key is added."""
        module = _module()
        self.assertFalse(hasattr(module, "_ADMITTED_SYMBOLS"),
                         "no import-time global bound to SHAPE_KEY")
        self.assertEqual({ASPECT_ID: "aspectRatio", COORD_ID: "globalCoord"},
                         module._admitted_symbols(module._LOCKS[KEY]))
        # A hypothetical second carrier gets its own map, not Shape's.
        other = copy.deepcopy(module._LOCKS[KEY])
        other["admitted"] = (
            other["admitted"][1]._replace(symbol_id=77, ordinal=0),)
        self.assertEqual({77: "globalCoord"}, module._admitted_symbols(other))
        # And every consumer takes it as an argument rather than a default.
        import inspect
        for name in ("_reference_census", "_no_indirect_write_holds",
                     "_dominance_holds"):
            with self.subTest(consumer=name):
                signature = inspect.signature(getattr(module, name))
                self.assertIn("symbols", signature.parameters)
                self.assertIs(inspect.Parameter.empty,
                              signature.parameters["symbols"].default)

    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual(2007, total)
        self.assertEqual(41, assigns)
        self.assertEqual(total, module._LOCKS[KEY]["total_nodes"])
        self.assertEqual(assigns, module._LOCKS[KEY]["total_assigns"])
        self.assertEqual(28, len(program.functions))
        self.assertEqual(28, module._LOCKS[KEY]["function_count"])

    def test_the_write_census_is_exactly_two_plain_assignments_in_main(self):
        module = _module()
        program = _analyzed()
        writes, reads = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        self.assertEqual(2, len(writes))
        self.assertEqual([COORD_ID, ASPECT_ID],
                         [item.symbol_id for item in writes])
        self.assertEqual(["=", "="], [item.operator for item in writes])
        self.assertEqual(["main", "main"], [item.owner_name for item in writes])
        self.assertEqual(["459:5-459:47", "461:5-461:54"],
                         [item.assign_span for item in writes])
        self.assertEqual([1, 3], [item.statement_index for item in writes])
        self.assertEqual(module._LOCKS[KEY]["writes"],
                         tuple(item.record for item in writes))

    def test_the_read_census_is_exactly_seven_across_five_functions(self):
        module = _module()
        program = _analyzed()
        writes, reads = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        self.assertEqual(7, len(reads))
        self.assertEqual(9, len(writes) + len(reads))
        self.assertEqual(
            [("circles", ASPECT_ID, "407:41-407:52"),
             ("diamonds", COORD_ID, "417:20-417:31"),
             ("diamonds", ASPECT_ID, "418:27-418:38"),
             ("main", COORD_ID, "460:15-460:26"),
             ("offset", ASPECT_ID, "439:34-439:45"),
             ("rings", ASPECT_ID, "412:41-412:52"),
             ("shape", ASPECT_ID, "424:26-424:37")],
            [(item.owner_name, item.symbol_id, item.span) for item in reads])
        self.assertEqual({"circles", "diamonds", "main", "offset", "rings",
                          "shape"},
                         {item.owner_name for item in reads})
        self.assertEqual(module._LOCKS[KEY]["reads"],
                         tuple(item.record for item in reads))

    def test_write_before_read_dominance_holds_on_the_real_program(self):
        """The crux. Re-derived here, not taken from the design."""
        module = _module()
        program = _analyzed()
        main = _main(program)
        writes, reads = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        # Both writes are unconditional top-level statements of `main`.
        for write in writes:
            statement = main.body[write.statement_index]
            self.assertIs(statement, write.chain[0])
            self.assertEqual(1, len(write.chain), "the write is not nested")
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(statement.expressions[0], write.node)
        self.assertEqual([1, 3], [item.statement_index for item in writes])
        # No call node exists anywhere in main.body[0..3].
        prefix = [kind for index in range(4)
                  for kind in module._statement_node_kinds(main.body[index],
                                                           index)]
        self.assertNotIn("call", prefix)
        self.assertEqual(
            [4, 6, 8, 9, 11, 13, 14, 15],
            sorted(module._call_statement_indices(main)))
        # The only read inside main follows its own write.
        in_main = [item for item in reads if item.owner_name == "main"]
        self.assertEqual(1, len(in_main))
        self.assertEqual(COORD_ID, in_main[0].symbol_id)
        self.assertEqual(2, in_main[0].statement_index)
        self.assertLess(1, in_main[0].statement_index)
        # Every other read is inside a helper, which cannot run before index 4.
        self.assertEqual(6, len([item for item in reads
                                 if item.owner_name != "main"]))

    def test_the_program_has_no_loops_and_an_acyclic_call_graph(self):
        module = _module()
        program = _analyzed()
        proof = program.counted_loop_proof
        self.assertEqual(0, proof.loop_count)
        self.assertEqual(0, proof.unproved_loop_count)
        self.assertTrue(proof.call_graph_acyclic)
        self.assertEqual((0, 0, 0, 0, 0, True),
                         module._LOCKS[KEY]["counted_loop_proof"])
        reachable, unreachable = module._reachability(program)
        self.assertEqual(tuple(range(95, 123)), reachable)
        self.assertEqual((), unreachable)
        self.assertEqual(reachable, module._LOCKS[KEY]["reachable"])
        self.assertEqual((), module._LOCKS[KEY]["unreachable"])

    def test_the_census_walks_global_declaration_initializers(self):
        """The whole subject matter is global declarations, so a node planted
        in `PI`'s initializer must be caught by the census rather than by a
        refreezable coarse hash."""
        module = _module()
        candidate = _analyzed()
        with_initializers = [item for item in candidate.declarations
                             if item.initializer is not None]
        self.assertEqual(["PI", "TAU"],
                         [item.symbol.name for item in with_initializers])
        initializer = with_initializers[0].initializer
        object.__setattr__(initializer, "children",
                           (*initializer.children,
                            dataclasses.replace(initializer)))
        _expect(self, module, candidate, _relocked(module, candidate),
                "global declaration initializer census mismatch")

    def test_a_reference_hidden_in_a_global_initializer_is_censused(self):
        """A read planted in `TAU`'s initializer is outside every walker that
        only descends `function.body`. It must not escape."""
        module = _module()
        candidate = _analyzed()
        planted = dataclasses.replace(
            _fn(candidate, "circles").body[0].expressions[0]
            .children[0].children[0].children[1].children[0].children[1])
        self.assertEqual(ASPECT_ID, planted.symbol_id)
        tau = candidate.declarations[12]
        object.__setattr__(tau.initializer, "children", (planted,))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "global declaration initializer census mismatch")

    def test_a_third_write_fails_the_write_census_not_a_coarse_hash(self):
        module = _module()
        candidate = _analyzed()
        planted = dataclasses.replace(
            _main(candidate).body[3].expressions[0])
        circles = _fn(candidate, "circles")
        object.__setattr__(circles, "body",
                           (dataclasses.replace(_main(candidate).body[3],
                                                expressions=(planted,)),
                            *circles.body))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "mutable global write census cardinality mismatch: 3")

    def test_an_eighth_read_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        host = _fn(candidate, "rings").body[0].expressions[0]
        planted = dataclasses.replace(
            host.children[0].children[0].children[1].children[0].children[1])
        self.assertEqual(ASPECT_ID, planted.symbol_id)
        object.__setattr__(host, "children", (*host.children, planted))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "mutable global read census cardinality mismatch: 8")


class MutableGlobalFrameLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK.

    For each row: mutate the tree (or the frozen record the lock owns),
    refreeze only the coarse hashes and the two program-wide counters, show the
    real module rejects with that lock's own message, then re-exec the module
    with exactly that predicate neutralized and show the message is gone.
    """

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            relock=None):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked(module, candidate)
        if recount:
            locks[KEY].update(_recount(module, candidate))
        if relock is not None:
            relock(locks)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_mutable_global_frame(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def test_function_cardinality_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "functions",
                               candidate.functions[:-1])
        survived = self._delete_and_compare(
            mutate, "_function_cardinality_holds",
            "function cardinality or inventory mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("call graph or reachability profile mismatch", survived)

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources, uses_texture=True))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "circles").body[0].expressions[0]
            planted = dataclasses.replace(
                _main(candidate).body[4].expressions[0].children[0])
            self.assertEqual("call", planted.kind)
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(survived)

    def test_ordinal_and_adjacency_lock(self):
        def mutate(candidate):
            declarations = list(candidate.declarations)
            declarations[ASPECT_ORDINAL], declarations[COORD_ORDINAL] = (
                declarations[COORD_ORDINAL], declarations[ASPECT_ORDINAL])
            object.__setattr__(candidate, "declarations", tuple(declarations))
        survived = self._delete_and_compare(
            mutate, "_ordinal_adjacency_holds",
            "admitted global declaration ordinal or adjacency mismatch")
        self.assertIsNone(
            survived,
            "lookup is by symbol id, so only the ordinal lock sees a swap")

    def test_mutable_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[ASPECT_ORDINAL]
            object.__setattr__(declaration.symbol, "storage", "const")
        survived = self._delete_and_compare(
            mutate, "_mutable_storage_holds",
            "admitted global storage or mutability mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("admitted global declaration identity mismatch", survived)

    def test_writability_is_part_of_the_mutable_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[COORD_ORDINAL]
            object.__setattr__(declaration.symbol, "writable", False)
        survived = self._delete_and_compare(
            mutate, "_mutable_storage_holds",
            "admitted global storage or mutability mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("admitted global declaration identity mismatch", survived)

    def test_uninitialised_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[ASPECT_ORDINAL]
            object.__setattr__(
                declaration, "initializer",
                dataclasses.replace(candidate.declarations[11].initializer))
        survived = self._delete_and_compare(
            mutate, "_uninitialized_holds",
            "admitted global declaration carries an initializer", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("admitted global declaration identity mismatch", survived)

    def test_declaration_identity_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[COORD_ORDINAL]
            object.__setattr__(
                declaration, "span",
                dataclasses.replace(declaration.span, end_column=19))
        survived = self._delete_and_compare(
            mutate, "_declaration_identity_holds",
            "admitted global declaration identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("global declaration inventory mismatch", survived)

    def test_declaration_inventory_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[ASPECT_ORDINAL]
            # A fresh Symbol: `dataclasses.replace` on the declaration alone
            # would share -- and so mutate -- the real aspectRatio symbol.
            symbol = dataclasses.replace(declaration.symbol, id=9001,
                                         name="planted")
            extra = dataclasses.replace(declaration, symbol=symbol)
            object.__setattr__(candidate, "declarations",
                               (*candidate.declarations, extra))
        survived = self._delete_and_compare(
            mutate, "_declaration_inventory_holds",
            "global declaration inventory mismatch")
        self.assertIsNone(survived)

    def test_initializer_census_lock(self):
        def mutate(candidate):
            initializer = candidate.declarations[11].initializer
            object.__setattr__(initializer, "literal", "3.0")
        survived = self._delete_and_compare(
            mutate, "_initializer_census_holds",
            "global declaration initializer census mismatch")
        self.assertIsNone(survived)

    def test_frame_contract_lock(self):
        def relock(locks):
            locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
                helper_parameter_qualifier="Frame&",
                helper_parameter="Frame& frame")
        survived = self._delete_and_compare(
            lambda candidate: None, "_frame_contract_holds",
            "frame emission contract mismatch", relock=relock)
        self.assertIsNone(survived)

    def test_aspect_ratio_numeric_contract_lock(self):
        def relock(locks):
            broken = locks[KEY]["admitted"][0].field._replace(
                native_type="float")
            locks[KEY]["admitted"] = (
                locks[KEY]["admitted"][0]._replace(field=broken),
                locks[KEY]["admitted"][1])
            locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
                fields=(broken, locks[KEY]["admitted"][1].field))
        survived = self._delete_and_compare(
            lambda candidate: None, "_aspect_ratio_contract_holds",
            "aspectRatio numeric contract mismatch", relock=relock)
        self.assertIsNone(
            survived,
            "the globalCoord lock must not double as the aspectRatio lock")

    def test_global_coord_numeric_contract_lock(self):
        def relock(locks):
            broken = locks[KEY]["admitted"][1].field._replace(
                native_type="glsl::Vec3")
            locks[KEY]["admitted"] = (
                locks[KEY]["admitted"][0],
                locks[KEY]["admitted"][1]._replace(field=broken))
            locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
                fields=(locks[KEY]["admitted"][0].field, broken))
        survived = self._delete_and_compare(
            lambda candidate: None, "_global_coord_contract_holds",
            "globalCoord numeric contract mismatch", relock=relock)
        self.assertIsNone(
            survived,
            "the aspectRatio lock must not double as the globalCoord lock")

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "map").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived)

    def test_write_cardinality_lock(self):
        def mutate(candidate):
            planted = dataclasses.replace(
                _main(candidate).body[3].expressions[0])
            circles = _fn(candidate, "circles")
            object.__setattr__(
                circles, "body",
                (dataclasses.replace(_main(candidate).body[3],
                                     expressions=(planted,)), *circles.body))
        survived = self._delete_and_compare(
            mutate, "_write_cardinality_holds",
            "mutable global write census cardinality mismatch: 3", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mutable global single-writer proof mismatch", survived)

    def test_single_writer_lock(self):
        """Relocate a write into a helper. The count stays two, so only the
        single-writer lock can see it."""
        def mutate(candidate):
            main = _main(candidate)
            statement = main.body[1]
            object.__setattr__(main, "body",
                               (*main.body[:1], *main.body[2:]))
            circles = _fn(candidate, "circles")
            object.__setattr__(circles, "body", (statement, *circles.body))
        survived = self._delete_and_compare(
            mutate, "_single_writer_holds",
            "mutable global single-writer proof mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("mutable global write position mismatch", survived)

    def test_no_indirect_write_lock(self):
        """A partial write through a swizzle keeps the direct-write count at
        two, so only the indirect-write lock can see it."""
        def mutate(candidate):
            main = _main(candidate)
            template = main.body[1].expressions[0]
            swizzle = next(node for node in _walk(main.body[1])
                           if node.kind == "swizzle")
            target = dataclasses.replace(
                swizzle,
                children=(dataclasses.replace(template.children[0]),))
            planted = dataclasses.replace(
                template, children=(target, template.children[1]))
            circles = _fn(candidate, "circles")
            object.__setattr__(
                circles, "body",
                (dataclasses.replace(main.body[1], expressions=(planted,)),
                 *circles.body))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "mutable global indirect or partial write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mutable global read census cardinality mismatch",
                      survived)

    def test_no_indirect_write_lock_catches_a_POSTFIX_increment(self):
        """`post` is a distinct IR kind from `unary`, not an operator of it.

        `body_semantic.py:210-212` builds `aspectRatio++` as kind `post`, so a
        predicate that tests only `unary` misses it entirely. Reproduced
        against the pre-fix module, which returned True for this mutant.
        """
        def mutate(candidate):
            main = _main(candidate)
            target = main.body[3].expressions[0].children[0]
            self.assertEqual(ASPECT_ID, target.symbol_id)
            post = dataclasses.replace(
                main.body[3].expressions[0], kind="post", operator="++",
                children=(dataclasses.replace(target),))
            self.assertEqual("post", post.kind)
            circles = _fn(candidate, "circles")
            object.__setattr__(
                circles, "body",
                (dataclasses.replace(main.body[3], expressions=(post,)),
                 *circles.body))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "mutable global indirect or partial write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mutable global read census cardinality mismatch: 8",
                      survived)

    def test_no_indirect_write_lock_catches_a_PREFIX_increment(self):
        def mutate(candidate):
            main = _main(candidate)
            target = main.body[3].expressions[0].children[0]
            unary = dataclasses.replace(
                main.body[3].expressions[0], kind="unary", operator="--",
                children=(dataclasses.replace(target),))
            circles = _fn(candidate, "circles")
            object.__setattr__(
                circles, "body",
                (dataclasses.replace(main.body[3], expressions=(unary,)),
                 *circles.body))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "mutable global indirect or partial write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mutable global read census cardinality mismatch: 8",
                      survived)

    def test_a_compound_assignment_is_caught_by_the_write_census_first(self):
        """Compound assignment needs no increment-operator entry.

        It is kind `assign` with a non-`=` operator, so the reference census
        still classifies it as a write and the cardinality lock names it
        first. `_no_indirect_write_holds` is the second line of defence, via
        its `operator != "="` branch -- shown here by deleting the four write
        locks that precede it.
        """
        module = _module()
        candidate = _analyzed()
        main = _main(candidate)
        template = main.body[3].expressions[0]
        planted = dataclasses.replace(
            template, operator="*=",
            children=(dataclasses.replace(template.children[0]),
                      template.children[1]))
        circles = _fn(candidate, "circles")
        object.__setattr__(
            circles, "body",
            (dataclasses.replace(main.body[3], expressions=(planted,)),
             *circles.body))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "mutable global write census cardinality mismatch: 3")

        scratch = _scratch(module, "_write_cardinality_holds",
                           "_single_writer_holds")
        with mock.patch.object(scratch, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            scratch.authenticate_mutable_global_frame(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        self.assertIn("mutable global indirect or partial write present",
                      str(raised.exception))

    def test_write_position_lock(self):
        """Nest the aspectRatio write inside an `if` whose kind and span are
        those of the statement it replaces, so main's body shape is unchanged
        and only the position lock can see the nesting."""
        def mutate(candidate):
            main = _main(candidate)
            statement = main.body[3]
            inner = dataclasses.replace(statement)
            wrapper = dataclasses.replace(
                statement, kind="expr", expressions=(),
                children=(dataclasses.replace(statement, kind="block",
                                              expressions=(),
                                              children=(inner,)),))
            object.__setattr__(main, "body",
                               (*main.body[:3], wrapper, *main.body[4:]))
        survived = self._delete_and_compare(
            mutate, "_write_position_holds",
            "mutable global write position mismatch", recount=True)
        self.assertIsNone(
            survived,
            "nesting the write is invisible to every other lock, which is "
            "exactly why the position lock has to exist")

    def test_write_identity_lock(self):
        def mutate(candidate):
            node = _main(candidate).body[1].expressions[0]
            object.__setattr__(node, "span",
                               dataclasses.replace(node.span, end_column=46))
        survived = self._delete_and_compare(
            mutate, "_write_identity_holds",
            "mutable global write identity mismatch")
        self.assertIsNone(survived)

    def test_read_cardinality_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "rings").body[0].expressions[0]
            planted = dataclasses.replace(
                host.children[0].children[0].children[1].children[0].children[1])
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_read_cardinality_holds",
            "mutable global read census cardinality mismatch: 8", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mutable global read identity mismatch", survived)

    def test_read_identity_lock(self):
        def mutate(candidate):
            node = (_fn(candidate, "shape").body[0].expressions[0]
                    .children[1].children[1].children[0])
            self.assertEqual(ASPECT_ID, node.symbol_id)
            object.__setattr__(node, "span",
                               dataclasses.replace(node.span, end_column=38))
        survived = self._delete_and_compare(
            mutate, "_read_identity_holds",
            "mutable global read identity mismatch")
        self.assertIsNone(survived)

    def test_dominance_lock(self):
        """Plant a call node inside `main.body[2]`, which breaks the premise
        that no helper can run before both writes complete."""
        def mutate(candidate):
            main = _main(candidate)
            call = dataclasses.replace(
                main.body[4].expressions[0].children[0])
            self.assertEqual("call", call.kind)
            host = main.body[2].expressions[0].children[0]
            object.__setattr__(host, "children", (*host.children, call))
        survived = self._delete_and_compare(
            mutate, "_dominance_holds",
            "mutable global write-before-read dominance mismatch",
            recount=True)
        self.assertIsNone(survived)

    def test_main_body_shape_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            object.__setattr__(main, "body",
                               (*main.body[:16], *main.body[17:]))
        survived = self._delete_and_compare(
            mutate, "_main_body_holds", "main body shape mismatch",
            recount=True)
        self.assertIsNone(survived)


def _walk(statement):
    def expression(value):
        yield value
        for child in value.children:
            yield from expression(child)
    for item in statement.expressions:
        yield from expression(item)
    for child in statement.children:
        yield from _walk(child)


class MutableGlobalFrameLedgerTests(unittest.TestCase):
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
        self.assertEqual(16, module._CONSUMED_LEDGER)
        self.assertEqual(2, len(module.authenticate_mutable_global_frame(
            _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (15, 17):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "mutable-global-frame visitation ledger mismatch"):
                module.authenticate_mutable_global_frame(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(2, len(module.authenticate_mutable_global_frame(
            _analyzed(), RAW_SHA256, PROFILE)))


class MutableGlobalFrameVocabularyTests(unittest.TestCase):
    def test_no_capability_or_type_vocabulary_growth(self):
        _module()
        frozen = {
            "capabilities": (
                44, generate_typed_slice.APPROVED_CAPABILITIES,
                "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea"),
            "types": (
                17, generate_typed_slice.APPROVED_TYPES,
                "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7"),
            "binary": (
                17, generate_typed_slice.APPROVED_BINARY_OPERATORS,
                "cceb35790b79fa895906c57d7e81f0056fac404cf7448eec9b8d9dbb49b705b0"),
            "assignment": (
                6, generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS,
                "99a6ede7544a02082e0b72d83690c3b68d8c846e221078e3e90ac10463d498e2"),
        }
        for name, (size, value, digest) in frozen.items():
            with self.subTest(vocabulary=name):
                self.assertEqual(size, len(value))
                self.assertEqual(
                    digest,
                    hashlib.sha256(repr(value).encode()).hexdigest())
        # `float` and `vec2` are already approved types: it is the STORAGE
        # class, not the type, that this mechanism admits.
        self.assertIn("float", generate_typed_slice.APPROVED_TYPES)
        self.assertIn("vec2", generate_typed_slice.APPROVED_TYPES)
        for token in (PROFILE, "mutable-global", "mutable-global-frame",
                      "global-declaration", "mutable-global-declaration",
                      "frame"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)
                self.assertNotIn(token, generate_typed_slice.APPROVED_TYPES)

    def test_the_module_never_grows_the_vocabulary_by_import(self):
        """Importing the module must not mutate either frozen tuple."""
        before = (generate_typed_slice.APPROVED_CAPABILITIES,
                  generate_typed_slice.APPROVED_TYPES)
        module = _module()
        module.authenticate_mutable_global_frame(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(before[0], generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))


if __name__ == "__main__":
    unittest.main()
