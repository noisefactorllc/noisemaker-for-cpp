"""Focused RED/GREEN proof for the shared ``linearToSrgb`` lane-index closure.

Written before the Shapes carrier existed in
``tools/glslcpp/frontend/linear_srgb_lane_index_profile.py``.  Every mutation
whose purpose is local structural logic refreezes the coarse
source/normalized/function/whole-program/interface hashes onto the mutant,
asserts the coarse message did **not** fire, and asserts the intended
node-level message.  A mutation caught only by a coarse hash is a failed test.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.linear_srgb_lane_index_profile"

SHAPES_KEY = "classicNoisedeck/shapes:shapes"
SHAPES_PROFILE = "linear-srgb-shapes-lane-index-v1"
SHAPES_RAW_SHA256 = (
    "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0")

SOURCES = {
    "classicNoisedeck/cellNoise:cellNoise":
        "classicNoisedeck/cellNoise/cellNoise.glsl",
    SHAPES_KEY: "classicNoisedeck/shapes/shapes.glsl",
    "filter/adjust:adjust": "filter/adjust/adjust.glsl",
    "filter/colorspace:colorspace": "filter/colorspace/colorspace.glsl",
}
EXISTING = {
    "classicNoisedeck/cellNoise:cellNoise":
        ("linear-srgb-cellnoise-lane-index-v1",
         ("125:13-125:22", "126:13-126:20", "126:23-126:32",
          "128:13-128:20", "128:35-128:44")),
    "filter/adjust:adjust":
        ("linear-srgb-adjust-lane-index-v1",
         ("78:13-78:22", "79:13-79:20", "79:23-79:32",
          "81:13-81:20", "81:35-81:44")),
    "filter/colorspace:colorspace":
        ("linear-srgb-colorspace-lane-index-v1",
         ("48:13-48:22", "49:13-49:20", "49:23-49:32",
          "51:13-51:20", "51:35-51:44")),
}
SHAPES_SPANS = ("576:13-576:22", "577:13-577:20", "577:23-577:32",
                "579:13-579:20", "579:35-579:44")
SHAPES_ROLES = ("read", "write", "read", "write", "read")
COARSE = "source, define, function, whole-program, or interface mismatch"


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("linear-srgb lane index profile module is absent")
    return importlib.import_module(MODULE)


def _raw(key: str) -> str:
    return (CORPUS / SOURCES[key]).read_text(encoding="utf-8")


def _analyzed(key: str = SHAPES_KEY, raw: str | None = None,
              defines: dict | None = None,
              parse_key: str | None = None):
    raw = _raw(key) if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, key)
               if defines is None else defines)
    parse_key = key if parse_key is None else parse_key
    return analyze_program(parse_program(raw, parse_key, defines), key)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _walk_expression(value, parent=None, child_index=None):
    yield value, parent, child_index
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, index)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _indexes(program):
    found = []
    for function in program.functions:
        for statement in function.body:
            for node, _, _ in _walk_statement(statement):
                if node.kind == "index":
                    found.append(node)
    return found


def _owner(program):
    return next(item for item in program.functions
                if item.name == "linearToSrgb")


def _loop(program):
    return _owner(program).body[1]


def _branch(program):
    return _loop(program).children[1].children[0]


def _sites(program):
    branch = _branch(program)
    condition = branch.expressions[0]
    then_assign = branch.children[0].children[0].expressions[0]
    else_assign = branch.children[1].children[0].expressions[0]
    return (condition.children[0],
            then_assign.children[0],
            then_assign.children[1].children[0],
            else_assign.children[0],
            else_assign.children[1].children[0].children[1].children[0])


def _refrozen(module, candidate, key=SHAPES_KEY, **overrides):
    lock = dict(module._LOCKS[key])
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    lock.update({
        "raw_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "normalized_bytes": len(normalized),
        "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
        "functions_sha256": module._sha(candidate.functions),
        "whole_sha256": module._whole_fingerprint(candidate),
        "interface_sha256": module._interface_fingerprint(candidate),
    })
    lock.update(overrides)
    return lock


class LinearSrgbLaneIndexCarrierTests(unittest.TestCase):
    def test_module_carries_exactly_four_sorted_keys_including_shapes(self):
        module = _module()
        self.assertEqual(("classicNoisedeck/cellNoise:cellNoise",
                          SHAPES_KEY,
                          "filter/adjust:adjust",
                          "filter/colorspace:colorspace"), module.KEYS)
        self.assertEqual(sorted(module.KEYS), list(module.KEYS))
        self.assertEqual({
            "classicNoisedeck/cellNoise:cellNoise":
                "linear-srgb-cellnoise-lane-index-v1",
            SHAPES_KEY: SHAPES_PROFILE,
            "filter/adjust:adjust": "linear-srgb-adjust-lane-index-v1",
            "filter/colorspace:colorspace":
                "linear-srgb-colorspace-lane-index-v1",
        }, module.PROFILES)
        self.assertEqual(set(module.KEYS), set(module._LOCKS))

    def test_shapes_authenticates_exactly_five_candidate_owned_indexes(self):
        module = _module()
        program = _analyzed()
        resolved = module.authenticate_linear_srgb_lane_index(
            program, SHAPES_RAW_SHA256, SHAPES_PROFILE)
        self.assertEqual(5, len(resolved))
        self.assertEqual(list(SHAPES_SPANS), [module._span(item)
                                              for item in resolved])
        self.assertEqual(list(_sites(program)), list(resolved))
        self.assertEqual(5, len(_indexes(program)))
        self.assertEqual(
            list(SHAPES_ROLES),
            [item.role for item in module._LOCKS[SHAPES_KEY]["sites"]])
        self.assertEqual(
            [("linear", "parameter"), ("srgb", "local"), ("linear", "parameter"),
             ("srgb", "local"), ("linear", "parameter")],
            [(item.children[0].symbol.name, item.children[0].symbol.storage)
             for item in resolved])
        for node in resolved:
            self.assertEqual("index", node.kind)
            self.assertEqual("float", node.type.display())
            self.assertEqual("lvalue", node.category)
            self.assertEqual("vec3", node.children[0].type.display())
            self.assertEqual("int", node.children[1].type.display())
        self.assertIs(program, module.apply_linear_srgb_lane_index(
            program, SHAPES_RAW_SHA256, SHAPES_PROFILE))

    def test_existing_three_carriers_authenticate_unchanged(self):
        module = _module()
        for key, (profile, spans) in EXISTING.items():
            with self.subTest(key=key):
                program = _analyzed(key)
                resolved = module.authenticate_linear_srgb_lane_index(
                    program, _hash(_raw(key)), profile)
                self.assertEqual(list(spans),
                                 [module._span(item) for item in resolved])
                self.assertEqual((), program.preprocessor_defines)

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong",
                        "linear-srgb-adjust-lane-index-v1",
                        "scalar-uint-xor-v1"):
            with self.subTest(carrier=carrier), \
                    self.assertRaisesRegex(ValueError,
                                           "exact profile carrier required"):
                module.authenticate_linear_srgb_lane_index(
                    program, SHAPES_RAW_SHA256, carrier)
        for key, (profile, _) in EXISTING.items():
            with self.subTest(existing=key), \
                    self.assertRaisesRegex(ValueError,
                                           "exact profile carrier required"):
                module.authenticate_linear_srgb_lane_index(
                    _analyzed(key), _hash(_raw(key)), SHAPES_PROFILE)
        foreign = _analyzed(raw=_raw(SHAPES_KEY), parse_key="test:foreign")
        foreign = dataclasses.replace(foreign, key="test:foreign")
        with self.assertRaisesRegex(
                ValueError, "not in the linear-srgb lane index cluster"):
            module.authenticate_linear_srgb_lane_index(
                foreign, SHAPES_RAW_SHA256, SHAPES_PROFILE)

    def test_rejects_wrong_caller_source_hash_and_source_drift(self):
        module = _module()
        program = _analyzed()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_linear_srgb_lane_index(
                program, "0" * 64, SHAPES_PROFILE)
        mutated = _raw(SHAPES_KEY).replace("12.92", "12.93")
        candidate = _analyzed(raw=mutated)
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_linear_srgb_lane_index(
                candidate, _hash(mutated), SHAPES_PROFILE)
        # Same tree, but the caller still presents the frozen corpus hash: the
        # coarse gate is what must catch the substituted source.
        with self.assertRaisesRegex(ValueError, COARSE):
            module.authenticate_linear_srgb_lane_index(
                candidate, SHAPES_RAW_SHA256, SHAPES_PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_linear_srgb_lane_index(
                        candidate, SHAPES_RAW_SHA256, SHAPES_PROFILE)


class LinearSrgbDefineLockTests(unittest.TestCase):
    """The per-key exact define lock replaces the old hardcoded ``!= ()``."""

    def test_shapes_requires_exactly_loop_a_40_and_loop_b_30(self):
        module = _module()
        self.assertEqual(
            (("LOOP_A_OFFSET", "int", "40"), ("LOOP_B_OFFSET", "int", "30")),
            module._LOCKS[SHAPES_KEY]["defines"])
        for key in EXISTING:
            self.assertEqual((), module._LOCKS[key]["defines"])

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        baseline = generate_typed_slice._defaults(ROOT, SHAPES_KEY)
        self.assertEqual({"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30}, baseline)
        cases = [
            ("value drift", _analyzed(defines={"LOOP_A_OFFSET": 41,
                                               "LOOP_B_OFFSET": 30})),
            ("name drift", _analyzed(defines={"LOOP_A_OFFSET_X": 40,
                                              "LOOP_B_OFFSET": 30})),
            ("extra define", _analyzed(defines={"LOOP_A_OFFSET": 40,
                                                "LOOP_B_OFFSET": 30,
                                                "EXTRA": 7})),
            ("defines erased", _analyzed(defines={})),
        ]
        reversed_defines = _analyzed()
        cases.append(("order drift", dataclasses.replace(
            reversed_defines,
            preprocessor_defines=tuple(
                reversed(reversed_defines.preprocessor_defines)))))
        for label, candidate in cases:
            with self.subTest(axis=label):
                lock = _refrozen(module, candidate)
                with mock.patch.dict(module._LOCKS, {SHAPES_KEY: lock}):
                    with self.assertRaises(ValueError) as raised:
                        module.authenticate_linear_srgb_lane_index(
                            candidate, lock["raw_sha256"], SHAPES_PROFILE)
                message = str(raised.exception)
                self.assertNotIn(COARSE, message, label)
                self.assertIn(expected, message, label)

    def test_existing_carrier_rejects_an_injected_define(self):
        module = _module()
        key = "filter/adjust:adjust"
        candidate = _analyzed(key, defines={"EXTRA": 7})
        lock = _refrozen(module, candidate, key=key)
        with mock.patch.dict(module._LOCKS, {key: lock}):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_linear_srgb_lane_index(
                    candidate, lock["raw_sha256"], EXISTING[key][0])
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("exact preprocessor define lock mismatch",
                      str(raised.exception))


class LinearSrgbNodeMutationTests(unittest.TestCase):
    """Single-axis structural mutations, each proved past the coarse gate."""

    def _assert_local(self, mutate, expected, site_overrides=None):
        module = _module()
        candidate = _analyzed()
        baseline_functions = module._sha(_analyzed().functions)
        mutate(candidate)
        self.assertNotEqual(baseline_functions,
                            module._sha(candidate.functions),
                            "mutation did not change the typed tree")
        overrides = {}
        if site_overrides is not None:
            sites = list(module._LOCKS[SHAPES_KEY]["sites"])
            for position, replacement in site_overrides(module, candidate):
                sites[position] = replacement
            overrides["sites"] = tuple(sites)
        lock = _refrozen(module, candidate, **overrides)
        with mock.patch.dict(module._LOCKS, {SHAPES_KEY: lock}):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_linear_srgb_lane_index(
                    candidate, lock["raw_sha256"], SHAPES_PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message,
                         f"{expected} was absorbed by the coarse gate")
        self.assertIn(expected, message)
        module.authenticate_linear_srgb_lane_index(
            _analyzed(), SHAPES_RAW_SHA256, SHAPES_PROFILE)

    def test_sixth_index_anywhere_is_a_hard_failure(self):
        def mutate(candidate):
            condition = _branch(candidate).expressions[0]
            extra = dataclasses.replace(_sites(candidate)[0])
            object.__setattr__(condition, "children",
                               (*condition.children, extra))
        self._assert_local(mutate, "index-node census cardinality mismatch")

    def test_removing_an_index_is_a_hard_failure(self):
        def mutate(candidate):
            condition = _branch(candidate).expressions[0]
            site = _sites(candidate)[0]
            object.__setattr__(condition, "children",
                               (site.children[0], condition.children[1]))
        self._assert_local(mutate, "index-node census cardinality mismatch")

    def test_retyped_index_node_fails_the_site_profile(self):
        def mutate(candidate):
            from tools.glslcpp.frontend.semantic_types import vector
            object.__setattr__(_sites(candidate)[1], "type", vector("float", 3))
        self._assert_local(mutate, "index site node profile mismatch")

    def test_write_site_downgraded_to_compound_assignment_fails_the_role(self):
        def mutate(candidate):
            assign = _branch(candidate).children[0].children[0].expressions[0]
            object.__setattr__(assign, "operator", "+=")
        self._assert_local(mutate, "index site role profile mismatch")

    def test_swapped_base_symbol_fails_the_base_profile(self):
        def mutate(candidate):
            site = _sites(candidate)[0]
            result = _owner(candidate).body[2].expressions[0]
            object.__setattr__(site, "children",
                               (dataclasses.replace(result), site.children[1]))

        def overrides(module, candidate):
            row = module._LOCKS[SHAPES_KEY]["sites"][0]
            return [(0, row._replace(
                node_sha256=module._sha(_sites(candidate)[0])))]
        self._assert_local(mutate, "index site base profile mismatch",
                           overrides)

    def test_swapped_induction_symbol_fails_the_induction_profile(self):
        def mutate(candidate):
            site = _sites(candidate)[2]
            object.__setattr__(
                site, "children",
                (site.children[0],
                 dataclasses.replace(site.children[1], symbol_id=99999)))

        def overrides(module, candidate):
            row = module._LOCKS[SHAPES_KEY]["sites"][2]
            return [(2, row._replace(
                node_sha256=module._sha(_sites(candidate)[2])))]
        self._assert_local(mutate, "index site induction-variable profile "
                                   "mismatch", overrides)

    def test_moved_pow_parent_fails_the_parent_profile(self):
        def mutate(candidate):
            assign = _branch(candidate).children[1].children[0].expressions[0]
            power = assign.children[1].children[0].children[1]
            self.assertEqual("pow", power.callee)
            object.__setattr__(power, "callee", "exp")
        self._assert_local(mutate, "index site parent profile mismatch")

    def test_relocated_else_branch_fails_the_ancestry_profile(self):
        def mutate(candidate):
            branch = _branch(candidate)
            then_block, else_block = branch.children
            object.__setattr__(then_block, "children",
                               (*then_block.children, *else_block.children))
            object.__setattr__(else_block, "children", ())
        self._assert_local(mutate, "index site ancestry profile mismatch")

    def test_renamed_owner_fails_the_owner_identity(self):
        def mutate(candidate):
            object.__setattr__(_owner(candidate).signature, "name",
                               "linearToSrgbX")
        self._assert_local(mutate, "linearToSrgb owner identity mismatch")

    def test_reordered_owner_body_fails_the_body_shape(self):
        def mutate(candidate):
            owner = _owner(candidate)
            object.__setattr__(owner, "body",
                               (owner.body[1], owner.body[0], owner.body[2]))
        self._assert_local(mutate, "linearToSrgb body shape mismatch")

    def test_initialized_result_local_fails_the_declaration_lock(self):
        def mutate(candidate):
            declaration = _owner(candidate).body[0].expressions[0]
            literal = _branch(candidate).expressions[0].children[1]
            object.__setattr__(declaration, "children",
                               (dataclasses.replace(literal),))
        self._assert_local(mutate, "srgb result local declaration mismatch")

    def test_loop_bound_drift_fails_the_counted_loop_lock(self):
        def mutate(candidate):
            loop = _loop(candidate)
            object.__setattr__(loop, "loop_proof", dataclasses.replace(
                loop.loop_proof, bound_value=2, trip_count=2))
        self._assert_local(mutate, "linearToSrgb counted loop profile mismatch")

    def test_returning_the_parameter_fails_the_return_identity(self):
        def mutate(candidate):
            result = _owner(candidate).body[2].expressions[0]
            object.__setattr__(result, "symbol_id",
                               _owner(candidate).parameters[0].id)
        self._assert_local(mutate, "srgb return identity mismatch")

    def test_third_if_branch_fails_lane_initialization_completeness(self):
        def mutate(candidate):
            branch = _branch(candidate)
            empty = dataclasses.replace(branch.children[0], children=(),
                                        expressions=())
            object.__setattr__(branch, "children", (*branch.children, empty))
        self._assert_local(
            mutate, "srgb lane initialization completeness mismatch")

    def test_extra_result_reference_fails_lane_initialization_completeness(self):
        def mutate(candidate):
            assign = _branch(candidate).children[0].children[0].expressions[0]
            product = assign.children[1]
            result = _owner(candidate).body[2].expressions[0]
            object.__setattr__(product, "children",
                               (product.children[0],
                                dataclasses.replace(result)))
        self._assert_local(
            mutate, "srgb lane initialization completeness mismatch")

    def test_extra_parameter_reference_fails_the_parameter_census(self):
        def mutate(candidate):
            condition = _branch(candidate).expressions[0]
            base = _sites(candidate)[0].children[0]
            object.__setattr__(condition, "children",
                               (condition.children[0],
                                dataclasses.replace(base)))
        self._assert_local(mutate,
                           "linear parameter reference census mismatch")

    def test_extra_induction_reference_fails_the_induction_census(self):
        def mutate(candidate):
            loop = _loop(candidate)
            condition = loop.expressions[0]
            induction = condition.children[0]
            object.__setattr__(condition, "children",
                               (induction, dataclasses.replace(induction)))
        self._assert_local(mutate,
                           "induction variable reference census mismatch")


class LinearSrgbVisitationLedgerTests(unittest.TestCase):
    def test_ledger_helper_rejects_duplicate_and_short_visitation(self):
        module = _module()
        marker = (object(), object(), object())
        self.assertIsNone(module._check_ledger(list(marker), 3, "probe"))
        for broken in ([marker[0], marker[0], marker[1]], list(marker[:2]),
                       [*marker, marker[2]]):
            with self.subTest(broken=len(broken)), \
                    self.assertRaisesRegex(ValueError,
                                           "probe visitation ledger mismatch"):
                module._check_ledger(broken, 3, "probe")

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(5, module._LANE_INDEX_LEDGER)
        self.assertEqual(5, len(module.authenticate_linear_srgb_lane_index(
            program, SHAPES_RAW_SHA256, SHAPES_PROFILE)))
        for sabotage in (4, 6):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_LANE_INDEX_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError, "lane-index visitation ledger mismatch"):
                module.authenticate_linear_srgb_lane_index(
                    _analyzed(), SHAPES_RAW_SHA256, SHAPES_PROFILE)
        self.assertEqual(5, len(module.authenticate_linear_srgb_lane_index(
            _analyzed(), SHAPES_RAW_SHA256, SHAPES_PROFILE)))


class LinearSrgbFrozenVocabularyTests(unittest.TestCase):
    def test_capability_vocabulary_remains_exactly_forty_four_entries(self):
        _module()
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(
            "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea",
            hashlib.sha256(repr(
                generate_typed_slice.APPROVED_CAPABILITIES).encode()).hexdigest())
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))
        self.assertEqual(
            "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7",
            hashlib.sha256(repr(
                generate_typed_slice.APPROVED_TYPES).encode()).hexdigest())
        self.assertNotIn("index", generate_typed_slice.APPROVED_CAPABILITIES)

    def test_shapes_profile_name_matches_the_designed_slice_row(self):
        """The slice row itself is the integration owner's file; this only
        pins the carrier name this module must publish for that row."""
        row = {
            "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
            "linear_srgb_lane_index_profile": SHAPES_PROFILE,
            "program_key": SHAPES_KEY,
            "scalar_uint_xor_profile": "scalar-uint-xor-v1",
            "shapes_float_bits_ingress_profile": "shapes-float-bits-ingress-v1",
        }
        module = _module()
        self.assertEqual(module.PROFILES[row["program_key"]],
                         row["linear_srgb_lane_index_profile"])
        self.assertEqual(
            [module.PROFILES[key] for key in module.KEYS],
            ["linear-srgb-cellnoise-lane-index-v1", SHAPES_PROFILE,
             "linear-srgb-adjust-lane-index-v1",
             "linear-srgb-colorspace-lane-index-v1"])


if __name__ == "__main__":
    unittest.main()
