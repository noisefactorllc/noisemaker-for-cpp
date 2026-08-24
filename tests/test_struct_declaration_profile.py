"""Focused RED/GREEN proof for the ``synth/newton`` struct declaration
profile.

RED state captured before ``tools/glslcpp/frontend/
struct_declaration_profile.py`` existed: every test in this file reported
``ModuleNotFoundError`` from ``_module``. The module then landed green.

``synth/newton:newton`` is the struct-declaration bucket's first carrier
(``docs/port-engineering/struct-parity/struct-design.md``): one struct
(``POIData``, normalized ``125:1-129:3``), seven constructors in
``getPOI`` statements 0-6, a struct-typed return, one struct local from a
call, two member-swizzle chains (``p.center.xy``/``.zw``) and two scalar
member reads (``p.deg``/``p.maxZoom``).

Testing rules inherited from the Shapes/mutable-global slices:

1. ``Symbol`` and every ``TypedExpression`` embed their declaration
   spans, so a value-level mutation shifts every enclosing node hash. The
   production module evaluates the value tiers AHEAD of the identity
   tiers, and each lock is proved load-bearing by *deleting the lock* in
   a scratch module copy -- never by mutating the input alone.
2. Every mutation test refreezes **only** the coarse hash fields (plus
   the specific census fields the mutation unavoidably moves) and asserts
   that no coarse message fired.
3. The censuses walk global declaration initializers as well as function
   bodies (newton has three: ``PI``/``TAU``/``PHI``).
4. newton's row is PREPARED, not landed: no row of the live slice may
   carry this module's field yet, and ``KEYS`` stays empty until the
   integration slice lands the row (the landed/prepared split).
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
import types
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine, TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.struct_declaration_profile"

KEY = "synth/newton:newton"
PROFILE = "struct-declaration-newton-v1"
SOURCE_PATH = "synth/newton/newton.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac"
NORMALIZED_SHA256 = (
    "c021c2f8c0e8df9b0fe92b97d24d532a5d3ccfe44c0e8a75bba4a11cabcc5af8")

STRUCT_ID = 1
FIELD_IDS = (57, 58, 59)
GETPOI_ID = 71
MAIN_ID = 72
STRUCT_LOCAL_ID = 101
CONSTRUCTOR_COUNT = 7
MEMBER_COUNT = 4
LEDGER = 26

# Every message the coarse gate can produce. A local lock that "fires"
# with one of these is not testing what its name claims.
COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)

FOREIGN_SOURCE = (
    "out vec4 fragColor;\n"
    "struct Data { vec4 a; float b; };\n"
    "Data make() { return Data(vec4(0.0), 1.0); }\n"
    "void main() { Data d = make(); fragColor = d.a; }\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("struct declaration profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock
    predicates. A neutralized predicate always reports "holds", which is
    exactly what removing the lock from the source would do."""
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


def _analyzed(raw: str | None = None, defines: dict | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, KEY)
               if defines is None else defines)
    return analyze_program(parse_program(raw, KEY, defines), KEY)


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


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


def _relocked(module, candidate, key=KEY, **overrides):
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen.

    Deliberately does **not** refreeze any semantic field: the struct
    records, the constructor payloads and every node hash keep their
    frozen originals.
    """
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
    total, assigns = module._node_census(candidate)
    return {"total_nodes": total, "total_assigns": assigns}


def _reinventory(module, candidate, key=KEY):
    return {"declaration_count": len(candidate.declarations),
            "declaration_inventory": module._declaration_inventory(candidate)}


def _refunctions(module, candidate, key=KEY):
    return {"function_inventory": module._function_inventory(candidate)}


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


def _authenticate(module, candidate, locks, profile=PROFILE, key=KEY):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_struct_declaration(
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


class StructDeclarationPublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual(("synth/julia:julia", KEY), module.KEYS)
        self.assertEqual(
            {"synth/julia:julia": "struct-declaration-julia-v1",
             KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({"synth/julia:julia", KEY}),
                         module.STRUCT_DECLARATION_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual(KEY, module.NEWTON_KEY)
        self.assertEqual(PROFILE, module.NEWTON_PROFILE)
        self.assertEqual(
            (("out_inout_admission_profile",
              "out-inout-admission-newton-v1"),),
            module.REQUIRED_COMPANION_PROFILES[KEY])
        for name in ("KEYS", "PROFILES", "PREPARED_KEYS", "NEWTON_KEY",
                     "NEWTON_PROFILE", "ALLOWED_ROW_FIELDS",
                     "PREPARED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
                     "allowed_row_fields", "StructDeclarationRecord",
                     "StructMaterialization", "materialization_contract",
                     "authenticate_struct_declaration",
                     "apply_struct_declaration"):
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

    def test_the_row_field_guard_is_an_exhaustive_prepared_allowlist(self):
        """An allowlist, not a denylist: the future row carries BOTH
        struct-lane carriers (this module and the out/inout companion) --
        the design's M3 hazard is that out parameters must never land
        without their direction contract, and the struct plumbing never
        without the out arms."""
        module = _module()
        self.assertEqual(
            {"defines", "program_key", "struct_declaration_profile",
             "out_inout_admission_profile"},
            set(module.allowed_row_fields(KEY)))
        self.assertEqual({KEY: module.allowed_row_fields(KEY),
                          "synth/julia:julia": module.allowed_row_fields(
                              "synth/julia:julia")}, module.ALLOWED_ROW_FIELDS)
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("synth/shape:shape")

    def test_no_live_row_carries_the_prepared_fields(self):
        """The landed/prepared split: nothing in the live slice schema may
        carry this module's field until the integration slice lands
        newton's row (this test asserts absence against the LIVE file and
        is the reason ``KEYS`` stays empty)."""
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        carriers = [row["program_key"] for row in spec["programs"]
                    if "struct_declaration_profile" in row]
        self.assertEqual(["synth/julia:julia", KEY], carriers)
        self.assertIn(KEY, {row["program_key"]
                            for row in spec["programs"]})

    def test_the_optional_proof_absent_set_is_exactly_the_typedprogram_fields(self):
        """newton carries NO auto-attached proof (measured; design §3.5),
        so every ``fixed_*_proof`` TypedProgram field is frozen absent.
        Enumerated from the dataclass, so a new proof field added
        elsewhere in the tree turns this red."""
        module = _module()
        carried = {
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_") and field.name.endswith("_proof")}
        self.assertEqual(carried, set(module._OPTIONAL_PROOF_FIELDS))

    def test_materialization_contract_is_the_f32_lane_double_scalar_shape(self):
        """The JS authority, quote-verified: the vec4 member is a pooled
        f32-lane array (the 7.7718e-9 spelling witness), the scalar
        members plain Numbers/doubles, the swizzle rewrite an authority
        note not an obligation."""
        module = _module()
        contract = module.materialization_contract(KEY)
        self.assertEqual("pooled-f32-array", contract.center_member)
        self.assertEqual("number-double", contract.scalar_members)
        self.assertEqual("glsl::Vec4", contract.center_native)
        self.assertEqual("double", contract.scalar_native)
        self.assertEqual(7.7718e-09, contract.center_witness_glsl)
        self.assertEqual(7.771800092370995e-09,
                         contract.center_witness_f32_spelling)
        self.assertEqual((3.0, 14.0), contract.scalar_witnesses)
        self.assertIn("vec2 constructors", contract.swizzle_authority_note)
        self.assertEqual('"synth/newton:newton": canonicalFactory264',
                         contract.factory_registration)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.materialization_contract("synth/shape:shape")

    def test_every_failure_names_the_profile_not_a_module_global(self):
        module = _module()
        prefix = re.escape(f"{PROFILE}: ")
        program = _analyzed()
        for caller, arguments in (
                ("carrier", (program, RAW_SHA256, "wrong")),
                ("non-carrier", (_foreign(), _hash(FOREIGN_SOURCE), PROFILE)),
                ("row fields", ("synth/shape:shape",)),
                ("materialization", ("synth/shape:shape",))):
            with self.subTest(site=caller), self.assertRaises(ValueError) as ctx:
                if caller == "carrier":
                    module.authenticate_struct_declaration(*arguments)
                elif caller == "non-carrier":
                    module.authenticate_struct_declaration(*arguments)
                elif caller == "row fields":
                    module.allowed_row_fields(*arguments)
                else:
                    module.materialization_contract(*arguments)
            self.assertRegex(str(ctx.exception), f"^{prefix}")


class StructDeclarationAdmissionTests(unittest.TestCase):
    def test_authenticates_the_struct_plumbing(self):
        module = _module()
        program = _analyzed()
        result = module.authenticate_struct_declaration(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(result, tuple)
        self.assertEqual(3, len(result))
        self.assertIs(program.structs[0], result[0])
        self.assertEqual(CONSTRUCTOR_COUNT, len(result[1]))
        self.assertEqual(MEMBER_COUNT, len(result[2]))
        self.assertIs(program, module.apply_struct_declaration(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "struct-declaration-newton-v2",
                        "out-inout-admission-newton-v1",
                        "inout-vec3-swap-v1", "mutable-global-nine-array-"
                        "cellrefract-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_struct_declaration(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_the_site_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_struct_declaration(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted struct-declaration carrier"):
                module.authenticate_struct_declaration(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_non_carrier_error_names_the_sole_admitted_declaration(self):
        """The rejection at the boundary must name the frozen site, so a
        future key's error can be told apart from this one's."""
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_struct_declaration(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        message = str(raised.exception)
        self.assertIn("struct POIData at 125:1-129:3", message)
        self.assertIn("center vec4 126:5", message)
        self.assertIn("sole admitted declaration", message)

    def test_the_foreign_fixture_really_carries_a_struct(self):
        foreign = _foreign()
        self.assertEqual(1, len(foreign.structs))
        self.assertEqual("Data", foreign.structs[0].name)

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_struct_declaration(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_struct_declaration(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("3.14159265359", "3.14159265358")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_an_unanalyzed_body_status_fails_the_normalized_lock(self):
        module = _module()
        candidate = dataclasses.replace(_analyzed(), body_status="parsed")
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_a_loop_profile_drift_fails_the_call_graph_lock(self):
        module = _module()
        baseline = _analyzed()
        proof = dataclasses.replace(baseline.counted_loop_proof, loop_count=5)
        candidate = dataclasses.replace(baseline, counted_loop_proof=proof)
        _expect(self, module, candidate, _relocked(module, candidate),
                "call graph or reachability profile mismatch")

    def test_typed_function_drift_fails_the_function_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        host = _fn(candidate, "df64_add").body[0].expressions[0]
        object.__setattr__(host, "children",
                           (*host.children,
                            dataclasses.replace(host.children[0])))
        locks = _relocked_partial(module, candidate, "functions")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "typed function fingerprint drift"):
            module.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_fails_the_whole_program_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(
            candidate.declarations[0], "span",
            dataclasses.replace(candidate.declarations[0].span, end_column=26))
        locks = _relocked_partial(module, candidate, "whole")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "whole-program fingerprint drift"):
            module.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_also_fails_the_interface_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(
            candidate.declarations[0], "span",
            dataclasses.replace(candidate.declarations[0].span, end_column=26))
        locks = _relocked_partial(module, candidate, "interface")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "interface fingerprint drift"):
            module.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_struct_declaration(
                        candidate, RAW_SHA256, PROFILE)

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        """newton's defines tuple is the canonical empty one; an extra
        define is a hard failure even behind refrozen coarse hashes."""
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        cases = [
            ("extra define", _analyzed(defines={"EXTRA": 7})),
            ("planted define record", dataclasses.replace(
                _analyzed(), preprocessor_defines=(
                    PreprocessorDefine("EXTRA", "int", "7"),))),
        ]
        for label, candidate in cases:
            with self.subTest(axis=label):
                _expect(self, module, candidate,
                        _relocked(module, candidate), expected)


class StructDeclarationCensusTests(unittest.TestCase):
    """Every figure re-derived here from the parsed program, never taken
    from the design or the frozen record alone."""

    def test_the_struct_declaration_and_its_three_fields(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(1, len(program.structs))
        declaration = program.structs[0]
        record = module._LOCKS[KEY]["struct"]
        self.assertEqual((1, "POIData"), (declaration.id, declaration.name))
        self.assertEqual("struct", declaration.type.kind)
        self.assertEqual("125:1-129:3", module._span(declaration))
        self.assertEqual((57, 58, 59),
                         tuple(field.id for field in declaration.fields))
        self.assertEqual(("center", "deg", "maxZoom"),
                         tuple(field.name for field in declaration.fields))
        self.assertEqual(("vec4", "float", "float"),
                         tuple(field.type.display()
                               for field in declaration.fields))
        self.assertEqual(("126:5-126:16", "127:5-127:14", "128:5-128:18"),
                         tuple(module._span(field)
                               for field in declaration.fields))
        self.assertEqual(record.fields, module._LOCKS[KEY]["struct"].fields)
        self.assertIn("POIData", program.local_type_names)

    def test_seven_constructors_in_getpoi_statements_0_to_6(self):
        module = _module()
        program = _analyzed()
        census = list(module._struct_constructor_census(program))
        self.assertEqual(CONSTRUCTOR_COUNT, len(census))
        getpoi = _fn(program, "getPOI")
        for (function, node, statement_index, _), record in (
                zip(census, module._LOCKS[KEY]["constructors"])):
            self.assertIs(getpoi, function)
            self.assertEqual(record.statement_index, statement_index)
            self.assertEqual("construct", node.kind)
            self.assertEqual("POIData", node.constructor_type.display())
            self.assertEqual(("vec4", "float", "float"),
                             tuple(child.type.display()
                                   for child in node.children))
            self.assertEqual(record.lane_counts, module._lane_counts(node))
            self.assertEqual(record.values,
                             module._constructor_values(node))
        spans = tuple(record.span
                      for record in module._LOCKS[KEY]["constructors"])
        self.assertEqual(("135:26-135:69", "136:26-136:92",
                          "137:26-137:69", "138:26-138:113",
                          "139:26-139:69", "140:26-140:69",
                          "141:12-141:40"), spans)

    def test_the_default_return_constructor_uses_the_one_lane_splat(self):
        """Six constructors build the vec4 from 4 literal lanes; the
        default ``return POIData(vec4(0.0), 3.0, 7.0)`` from ONE -- the
        splat form, frozen so an arity change cannot hide."""
        module = _module()
        records = module._LOCKS[KEY]["constructors"]
        self.assertEqual(((4, 1, 1),) * 6 + ((1, 1, 1),),
                         tuple(record.lane_counts for record in records))
        self.assertEqual(((0.0,), 3.0, 7.0), records[-1].values)

    def test_the_poi_table_payloads(self):
        """The seven POI payloads, value for value (the JS object
        literals' source of truth)."""
        module = _module()
        records = module._LOCKS[KEY]["constructors"]
        self.assertEqual(
            (((0.0, 0.0, 0.0, 0.0), 3.0, 7.0),
             ((0.25, 0.4330126941204071, 0.0, 7.7718e-09), 3.0, 14.0),
             ((0.0, 0.0, 0.0, 0.0), 5.0, 7.0),
             ((0.6545084714889526, 0.4755282700061798, 2.5699e-08,
               -1.1859e-08), 5.0, 14.0),
             ((0.0, 0.0, 0.0, 0.0), 6.0, 7.0),
             ((0.0, 0.0, 0.0, 0.0), 8.0, 7.0),
             ((0.0,), 3.0, 7.0)),
            tuple(record.values for record in records))

    def test_getpoi_returns_poidata_with_one_in_int(self):
        module = _module()
        program = _analyzed()
        getpoi = _fn(program, "getPOI")
        self.assertEqual(GETPOI_ID, getpoi.id)
        self.assertEqual("POIData", getpoi.return_type.display())
        self.assertEqual(1, len(getpoi.parameters))
        parameter = getpoi.parameters[0]
        self.assertEqual((60, "idx", "int", "in"),
                         (parameter.id, parameter.name,
                          parameter.type.display(), parameter.direction))
        self.assertEqual("131:1-142:2", module._span(getpoi))
        self.assertEqual(7, len(getpoi.body))
        self.assertEqual(("if",) * 6 + ("return",),
                         tuple(stmt.kind for stmt in getpoi.body))

    def test_the_struct_local_is_a_getpoi_call_nested_in_main(self):
        module = _module()
        program = _analyzed()
        node, statement, chain, function = module._find_struct_local(
            program, module._LOCKS[KEY])
        self.assertIs(_fn(program, "main"), function)
        self.assertEqual(101, node.symbol.id)
        self.assertEqual("p", node.symbol.name)
        self.assertEqual("POIData", node.symbol.type.display())
        self.assertEqual("local", node.symbol.storage)
        self.assertEqual("decl", statement.kind)
        self.assertEqual("175:9-175:36", module._span(statement))
        self.assertEqual(3, len(chain))
        self.assertEqual("block", chain[-2].kind)
        initializer = node.children[0]
        self.assertEqual("call", initializer.kind)
        self.assertEqual("getPOI", initializer.callee)
        self.assertEqual(GETPOI_ID, initializer.signature_id)

    def test_two_member_swizzles_and_two_scalar_member_reads(self):
        module = _module()
        program = _analyzed()
        census = list(module._member_site_census(program))
        self.assertEqual(MEMBER_COUNT, len(census))
        by_role = {"swizzled": [], "scalar-read": []}
        for node, parent, base, role in census:
            by_role[role].append((node, parent, base))
        self.assertEqual(2, len(by_role["swizzled"]))
        self.assertEqual(2, len(by_role["scalar-read"]))
        for node, parent, base in by_role["swizzled"]:
            self.assertEqual("center", node.member)
            self.assertEqual("vec4", node.type.display())
            self.assertEqual("swizzle", parent.kind)
            self.assertIn(parent.member, ("xy", "zw"))
            self.assertEqual("vec2", parent.type.display())
            self.assertIs(node, parent.children[0])
            self.assertEqual(101, base.symbol_id)
        letters = sorted(parent.member for _, parent, _
                         in by_role["swizzled"])
        self.assertEqual(["xy", "zw"], letters)
        scalar = {node.member: parent.kind
                  for node, parent, _ in by_role["scalar-read"]}
        self.assertEqual({"deg": "assign", "maxZoom": "builtin"}, scalar)

    def test_the_absent_sub_shapes_stay_absent(self):
        """S8 (whole-vec member read) and S5 (struct-typed parameter) are
        the palette family's shapes, not newton's; both censuses must
        answer empty and the locks must exist to keep them so."""
        module = _module()
        program = _analyzed()
        self.assertEqual((), tuple(
            parameter.name for function in program.functions
            for parameter in function.parameters
            if parameter.type.kind == "struct"))
        self.assertTrue(module._no_struct_parameters_holds(program))
        vec_whole = [node for node, parent, base, role
                     in module._member_site_census(program)
                     if role == "scalar-read"
                     and node.type.display() != "float"]
        self.assertEqual([], vec_whole)

    def test_the_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual(804, total)
        self.assertEqual(34, assigns)
        self.assertEqual((804, 34),
                         (module._LOCKS[KEY]["total_nodes"],
                          module._LOCKS[KEY]["total_assigns"]))
        self.assertEqual(26, len(program.declarations))
        self.assertEqual(13, len(program.functions))
        self.assertEqual(module._declaration_inventory(program),
                         module._LOCKS[KEY]["declaration_inventory"])
        self.assertEqual(module._function_inventory(program),
                         module._LOCKS[KEY]["function_inventory"])

    def test_the_frozen_directions_agree_with_the_out_module(self):
        """Both newton struct-lane modules freeze the same function
        inventory (directions included); a drift between them would be a
        silent disagreement, so assert the equality directly."""
        module = _module()
        other = importlib.import_module(
            "tools.glslcpp.frontend.out_inout_admission_profile")
        self.assertEqual(module._LOCKS[KEY]["function_inventory"],
                         other._LOCKS[KEY]["function_inventory"])

    def test_the_loop_and_call_graph_profile(self):
        module = _module()
        program = _analyzed()
        proof = program.counted_loop_proof
        self.assertEqual((4, 0, 2, 4000, 8008, True),
                         (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth,
                          proof.max_lexical_product,
                          proof.entrypoint_charge,
                          proof.call_graph_acyclic))
        reachable, unreachable = module._reachability(program)
        self.assertEqual(module._LOCKS[KEY]["reachable"], reachable)
        self.assertEqual((), unreachable,
                         "all thirteen functions are reachable")
        self.assertEqual((), module._LOCKS[KEY]["unreachable"])


class StructDeclarationLedgerTests(unittest.TestCase):
    def test_ledger_helper_rejects_duplicate_and_short_visitation(self):
        module = _module()
        marker = object(), object()
        self.assertIsNone(module._check_ledger(list(marker), 2, "probe"))
        broken = [marker[0], marker[0]]
        with self.assertRaisesRegex(
                ValueError, "probe visitation ledger mismatch"):
            module._check_ledger(broken, 2, "probe")
        with self.assertRaisesRegex(
                ValueError, "probe visitation ledger mismatch"):
            module._check_ledger(list(marker), 3, "probe")

    def test_ledger_arithmetic_is_twenty_six(self):
        """1 struct + 3 fields + 7 constructors + 4 members + 2 swizzles +
        4 member bases + the local declaration node + its initializer
        call + its Symbol + getPOI + main."""
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        self.assertEqual(
            1 + 3 + 7 + 4 + 2 + 4 + 1 + 1 + 1 + 1 + 1,
            module._CONSUMED_LEDGER)

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        """The sabotage test: the ledger is the only thing that can catch
        a census that consumes one object twice (or skips one), so
        sabotaging its size must turn the valid program red."""
        module = _module()
        program = _analyzed()
        self.assertEqual(3, len(module.authenticate_struct_declaration(
            program, RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "struct-declaration-newton visitation ledger "
                        "mismatch"):
                module.authenticate_struct_declaration(
                    program, RAW_SHA256, PROFILE)


class StructDeclarationLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK.

    For each row: mutate the tree (or the frozen record the lock owns),
    refreeze only the coarse hashes and the counters the mutation
    unavoidably moves, show the real module rejects with that lock's own
    message, then re-exec the module with exactly that predicate
    neutralized and show the message is gone.
    """

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            refunctions=False, reinventory=False,
                            recallgraph=False, relock=None):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount(module, candidate))
        if refunctions:
            overrides.update(_refunctions(module, candidate))
        if reinventory:
            overrides.update(_reinventory(module, candidate))
        if recallgraph:
            overrides.update(_recallgraph(module, candidate))
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_struct_declaration(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def _constructor(self, program, index):
        module = _module()
        return list(module._struct_constructor_census(program))[index][1]

    # --- coarse gate -------------------------------------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            3, len(scratch.authenticate_struct_declaration(
                _analyzed(), "0" * 64, PROFILE)),
            "with the lock deleted nothing may reject a lying caller")

    def test_function_cardinality_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "functions",
                               candidate.functions[:-1])
        survived = self._delete_and_compare(
            mutate, "_function_cardinality_holds",
            "function cardinality mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("function inventory mismatch", survived)

    def test_function_inventory_lock(self):
        def mutate(candidate):
            function = _fn(candidate, "df64_add")
            object.__setattr__(
                candidate, "functions",
                tuple(dataclasses.replace(item, signature=dataclasses.replace(
                    item.signature, name="planted"))
                    if item is function else item
                    for item in candidate.functions))
        survived = self._delete_and_compare(
            mutate, "_function_inventory_holds", "function inventory mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("call graph or reachability", survived,
                      "the rename also moves the call-graph edge names")

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources,
                                    uses_derivatives=True))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "df64_to_float").body[0].expressions[0]
            planted = dataclasses.replace(
                _fn(candidate, "main").body[15].expressions[0])
            self.assertEqual("call", planted.kind)
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(
            survived,
            "a planted call edge has no second witness besides the census "
            "counters, which this mutation refreezes")

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
            "global declaration inventory mismatch")
        self.assertIsNone(survived)

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "df64_add").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived)

    # --- the struct census --------------------------------------------------

    def test_struct_inventory_lock_catches_a_second_struct(self):
        def mutate(candidate):
            planted = dataclasses.replace(
                candidate.structs[0], id=2, name="Planted")
            object.__setattr__(candidate, "structs",
                               (candidate.structs[0], planted))
        survived = self._delete_and_compare(
            mutate, "_struct_inventory_holds", "struct inventory mismatch")
        self.assertIsNone(
            survived,
            "only the inventory lock can see a second struct: the frozen "
            "record still names structs[0], which is unchanged")

    def test_struct_declaration_identity_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate.structs[0], "span",
                dataclasses.replace(candidate.structs[0].span, end_line=130))
        survived = self._delete_and_compare(
            mutate, "_struct_declaration_identity_holds",
            "struct declaration identity mismatch")
        self.assertIsNone(survived)

    def test_struct_fields_lock_catches_a_retype_before_identity(self):
        """Value checks run ahead of node identity: retyping `deg` must
        name the field census, not the struct identity hash that would
        otherwise absorb it."""
        module = _module()
        candidate = _analyzed()
        field = candidate.structs[0].fields[1]
        object.__setattr__(field, "type",
                           candidate.structs[0].fields[0].type)
        locks = _relocked(module, candidate)
        message = _expect(self, module, candidate, locks,
                          "struct field census mismatch")
        self.assertNotIn("struct declaration identity mismatch", message)

    def test_struct_field_identity_lock(self):
        """The identity tier of the field lock: the record's frozen field
        hash tampered while every value still matches."""
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        fields = locks[KEY]["struct"].fields
        locks[KEY]["struct"] = locks[KEY]["struct"]._replace(fields=(
            fields[0]._replace(sha256="0" * 64), *fields[1:]))
        _expect(self, module, candidate, locks,
                "struct field identity mismatch")
        scratch = _scratch(module, "_struct_field_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    def test_getpoi_signature_lock(self):
        def mutate(candidate):
            getpoi = _fn(candidate, "getPOI")
            object.__setattr__(
                getpoi.signature, "return_type",
                _fn(candidate, "df64_add").return_type)
        survived = self._delete_and_compare(
            mutate, "_getpoi_signature_holds",
            "struct return signature mismatch", recount=True,
            refunctions=True)
        self.assertIsNone(survived)

    def test_getpoi_body_lock(self):
        def mutate(candidate):
            getpoi = _fn(candidate, "getPOI")
            object.__setattr__(
                getpoi.body[0], "span",
                dataclasses.replace(getpoi.body[0].span, end_column=71))
        survived = self._delete_and_compare(
            mutate, "_getpoi_body_holds", "getPOI body shape mismatch")
        self.assertIsNone(survived)

    def test_constructor_census_lock_catches_an_added_child(self):
        def mutate(candidate):
            node = self._constructor(candidate, 0)
            object.__setattr__(
                node, "children",
                (*node.children, dataclasses.replace(node.children[1])))
        survived = self._delete_and_compare(
            mutate, "_constructor_census_holds",
            "struct constructor census mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct constructor payload mismatch", survived)

    def test_constructor_census_lock_catches_an_eighth_constructor(self):
        """An eighth constructor planted in ``main``: only the census's
        cardinality and owner checks can see it (the payload and identity
        tiers would happily match a subset)."""
        def mutate(candidate):
            module = _module()
            node = self._constructor(candidate, 0)
            planted = dataclasses.replace(node)
            host = _fn(candidate, "main").body[16]
            object.__setattr__(
                host, "expressions", (host.expressions[0], planted))
        survived = self._delete_and_compare(
            mutate, "_constructor_census_holds",
            "struct constructor census mismatch: 8", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct constructor payload mismatch", survived)

    def test_constructor_payload_lock(self):
        """A literal perturbed: the POI table itself, value for value."""
        def mutate(candidate):
            node = self._constructor(candidate, 1)
            literal = node.children[0].children[1]
            self.assertEqual(0.4330126941204071, literal.literal_value)
            object.__setattr__(literal, "literal_value", 0.44)
        survived = self._delete_and_compare(
            mutate, "_constructor_values_hold",
            "struct constructor payload mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct constructor identity mismatch", survived)

    def test_constructor_identity_lock(self):
        def mutate(candidate):
            node = self._constructor(candidate, 3)
            object.__setattr__(
                node, "span",
                dataclasses.replace(node.span, end_column=114))
        survived = self._delete_and_compare(
            mutate, "_constructor_identity_holds",
            "struct constructor identity mismatch")
        self.assertIsNone(survived)

    def test_struct_local_shape_lock_catches_a_non_call_initializer(self):
        def mutate(candidate):
            module = _module()
            node, _, _, _ = module._find_struct_local(
                candidate, module._LOCKS[KEY])
            planted = dataclasses.replace(node.children[0], kind="id")
            object.__setattr__(node, "children", (planted,))
        survived = self._delete_and_compare(
            mutate, "_struct_local_shape_holds",
            "struct local census mismatch", recount=True, recallgraph=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct local identity mismatch", survived)

    def test_struct_local_identity_lock(self):
        def mutate(candidate):
            node, _, _, _ = _module()._find_struct_local(
                candidate, _module()._LOCKS[KEY])
            object.__setattr__(
                node, "span",
                dataclasses.replace(node.span, end_column=36))
        survived = self._delete_and_compare(
            mutate, "_struct_local_identity_holds",
            "struct local identity mismatch")
        self.assertIsNone(survived)

    def test_member_census_lock_catches_a_renamed_field(self):
        def mutate(candidate):
            census = list(_module()._member_site_census(candidate))
            node = census[2][0]
            self.assertEqual("deg", node.member)
            object.__setattr__(node, "member", "planted")
        survived = self._delete_and_compare(
            mutate, "_member_census_holds", "struct member census mismatch",
            recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct member identity mismatch", survived)

    def test_member_swizzle_lock_catches_a_changed_letter(self):
        def mutate(candidate):
            module = _module()
            census = list(module._member_site_census(candidate))
            parent = census[0][1]
            self.assertEqual("swizzle", parent.kind)
            self.assertEqual("xy", parent.member)
            object.__setattr__(parent, "member", "xx")
        survived = self._delete_and_compare(
            mutate, "_member_swizzle_holds",
            "member swizzle census mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("struct member identity mismatch", survived,
                      "the letter lives in the swizzle node's hash too")

    def test_member_identity_lock(self):
        def mutate(candidate):
            module = _module()
            census = list(module._member_site_census(candidate))
            node = census[3][0]
            object.__setattr__(
                node, "span",
                dataclasses.replace(node.span, end_column=49))
        survived = self._delete_and_compare(
            mutate, "_member_identity_holds",
            "struct member identity mismatch")
        self.assertIsNone(survived)

    def test_no_struct_parameters_lock(self):
        """S5 absent-set: a struct-typed parameter planted on a helper no
        other lock inspects -- only this census can see it."""
        def mutate(candidate):
            function = _fn(candidate, "df64_add")
            parameter = function.parameters[0]
            object.__setattr__(parameter, "type",
                               candidate.structs[0].type)
        survived = self._delete_and_compare(
            mutate, "_no_struct_parameters_holds",
            "struct-typed parameter census mismatch", recount=True,
            refunctions=True)
        self.assertIsNone(
            survived,
            "the struct-parameter absent-set has no second witness")

    def test_materialization_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["materialization"] = locks[KEY][
            "materialization"]._replace(scalar_native="float")
        _expect(self, module, candidate, locks,
                "struct materialization contract mismatch")
        scratch = _scratch(module, "_materialization_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_struct_declaration(
                candidate, locks[KEY]["raw_sha256"], PROFILE))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
