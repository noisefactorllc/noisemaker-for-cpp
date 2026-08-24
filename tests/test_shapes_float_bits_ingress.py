"""Focused RED/GREEN proof for the one Shapes ``floatBitsToUint`` ingress.

Written before ``tools/glslcpp/frontend/shapes_float_bits_ingress_profile.py``
existed.  Structural mutations refreeze the coarse source/normalized/function/
whole-program/interface hashes onto the mutant, assert the coarse message did
**not** fire, and assert the intended local message; the focused
``float seedFrac = 0.0;`` -> ``-0.0`` mutant must fail the positive-zero
initializer lock rather than any coarse hash.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
import math
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.scalar_uint_xor_profile import (
    PROFILE as SCALAR_UINT_XOR_PROFILE)
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.shapes_float_bits_ingress_profile"

KEY = "classicNoisedeck/shapes:shapes"
PROFILE = "shapes-float-bits-ingress-v1"
RAW_SHA256 = "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0"
SOURCE = CORPUS / "classicNoisedeck/shapes/shapes.glsl"
FOREIGN = CORPUS / "classicNoisedeck/shapeMixer/shapeMixer.glsl"
INGRESS_SPAN = "119:21-119:46"
COARSE = "source, define, function, whole-program, or interface mismatch"


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("Shapes float-bit ingress profile module is absent")
    return importlib.import_module(MODULE)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _analyzed(raw: str | None = None, key: str = KEY,
              defines: dict | None = None, parse_key: str | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, KEY)
               if defines is None else defines)
    parse_key = key if parse_key is None else parse_key
    return analyze_program(parse_program(raw, parse_key, defines), key)


def _walk_expression(value, parent=None, child_index=None):
    yield value, parent, child_index
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, index)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _owner(program):
    return next(item for item in program.functions
                if item.name == "randomFromLatticeWithOffset")


def _declaration(program):
    return _owner(program).body[13].expressions[0]


def _ingress(program):
    return _declaration(program).children[0]


def _seed_frac_declaration(program):
    return _owner(program).body[5].expressions[0]


def _refrozen(module, candidate, **overrides):
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    values = {
        "_RAW_BYTES": len(raw),
        "_RAW_SHA256": hashlib.sha256(raw).hexdigest(),
        "_NORMALIZED_BYTES": len(normalized),
        "_NORMALIZED_SHA256": hashlib.sha256(normalized).hexdigest(),
        "_FUNCTIONS_SHA256": module._sha(candidate.functions),
        "_WHOLE_SHA256": module._whole(candidate),
        "_INTERFACE_SHA256": module._interface(candidate),
    }
    values.update(overrides)
    return values


class ShapesFloatBitsIngressCarrierTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual(PROFILE, module.PROFILE)
        self.assertEqual(KEY, module.SHAPES_KEY)
        self.assertEqual(frozenset({KEY}),
                         module.SHAPES_FLOAT_BITS_INGRESS_KEYS)
        self.assertIsInstance(module.SHAPES_FLOAT_BITS_INGRESS_KEYS, frozenset)
        for name in ("PROFILE", "SHAPES_KEY", "SHAPES_FLOAT_BITS_INGRESS_KEYS",
                     "authenticate_shapes_float_bits_ingress",
                     "apply_shapes_float_bits_ingress"):
            self.assertIn(name, module.__all__)

    def test_authenticates_exactly_one_candidate_owned_ingress(self):
        module = _module()
        program = _analyzed()
        resolved = module.authenticate_shapes_float_bits_ingress(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(resolved, tuple)
        self.assertEqual(1, len(resolved))
        node = resolved[0]
        self.assertIs(_ingress(program), node)
        self.assertEqual("builtin", node.kind)
        self.assertEqual("floatBitsToUint", node.callee)
        self.assertEqual(INGRESS_SPAN, module._span(node))
        self.assertEqual("uint", node.type.display())
        self.assertEqual("rvalue", node.category)
        self.assertEqual(1, len(node.children))
        self.assertEqual("float", node.children[0].type.display())
        self.assertEqual("seedFrac", node.children[0].symbol.name)
        self.assertIs(program, module.apply_shapes_float_bits_ingress(
            program, RAW_SHA256, PROFILE))

    def test_non_carrier_key_returns_empty_and_rejects_a_supplied_profile(self):
        module = _module()
        raw = FOREIGN.read_text(encoding="utf-8")
        other = analyze_program(
            parse_program(raw, "classicNoisedeck/shapeMixer:shapeMixer",
                          generate_typed_slice._defaults(
                              ROOT, "classicNoisedeck/shapeMixer:shapeMixer")),
            "classicNoisedeck/shapeMixer:shapeMixer")
        self.assertEqual((), module.authenticate_shapes_float_bits_ingress(
            other, _hash(raw), None))
        for carrier in (PROFILE, "wrong", SCALAR_UINT_XOR_PROFILE):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "not an admitted Shapes float-bit ingress "
                                "carrier"):
                module.authenticate_shapes_float_bits_ingress(
                    other, _hash(raw), carrier)

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", SCALAR_UINT_XOR_PROFILE,
                        "scanline-error-float-bits-ingress-v1",
                        "linear-srgb-shapes-lane-index-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_shapes_float_bits_ingress(
                    program, RAW_SHA256, carrier)

    def test_rejects_wrong_caller_source_hash_and_source_drift(self):
        module = _module()
        with self.assertRaisesRegex(ValueError, COARSE):
            module.authenticate_shapes_float_bits_ingress(
                _analyzed(), "0" * 64, PROFILE)
        mutated = SOURCE.read_text(encoding="utf-8").replace(
            "374761393u", "374761394u")
        with self.assertRaisesRegex(ValueError, COARSE):
            module.authenticate_shapes_float_bits_ingress(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_shapes_float_bits_ingress(
                        candidate, RAW_SHA256, PROFILE)

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        baseline = _analyzed()
        cases = [
            ("value drift", _analyzed(defines={"LOOP_A_OFFSET": 41,
                                               "LOOP_B_OFFSET": 30})),
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
                values = _refrozen(module, candidate)
                with mock.patch.multiple(module, **values):
                    with self.assertRaises(ValueError) as raised:
                        module.authenticate_shapes_float_bits_ingress(
                            candidate, values["_RAW_SHA256"], PROFILE)
                message = str(raised.exception)
                self.assertNotIn(COARSE, message, label)
                self.assertIn(expected, message, label)


class ShapesFloatBitsIngressMutationTests(unittest.TestCase):
    def _assert_local(self, mutate, expected, **overrides):
        module = _module()
        candidate = _analyzed()
        baseline = module._sha(_analyzed().functions)
        mutate(candidate)
        self.assertNotEqual(baseline, module._sha(candidate.functions),
                            "mutation did not change the typed tree")
        values = _refrozen(module, candidate, **overrides)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_float_bits_ingress(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message,
                         f"{expected} was absorbed by the coarse gate")
        self.assertIn(expected, message)
        module.authenticate_shapes_float_bits_ingress(
            _analyzed(), RAW_SHA256, PROFILE)

    def test_renamed_callee_empties_the_census(self):
        self._assert_local(
            lambda candidate: object.__setattr__(
                _ingress(candidate), "callee", "uintBitsToFloat"),
            "ingress cardinality mismatch: 0")

    def test_second_ingress_anywhere_is_a_hard_failure(self):
        def mutate(candidate):
            declaration = _declaration(candidate)
            object.__setattr__(declaration, "children",
                               (*declaration.children,
                                dataclasses.replace(_ingress(candidate))))
        self._assert_local(mutate, "ingress cardinality mismatch: 2")

    def test_ingress_moved_to_another_function_is_rejected(self):
        def mutate(candidate):
            other = next(item for item in candidate.functions
                         if item.name == "linearToSrgb")
            statement = _owner(candidate).body[13]
            object.__setattr__(other, "body", (*other.body, statement))
        self._assert_local(mutate,
                           "float-bit ingress outside the owner function")

    def test_vector_overload_fails_the_scalar_signature(self):
        def mutate(candidate):
            from tools.glslcpp.frontend.semantic_types import vector
            object.__setattr__(_ingress(candidate).children[0], "type",
                               vector("float", 2))
        self._assert_local(mutate, "ingress node identity mismatch")

    def test_inverse_conversion_result_type_is_rejected(self):
        def mutate(candidate):
            from tools.glslcpp.frontend.semantic_types import Type
            object.__setattr__(_ingress(candidate), "type",
                               Type("scalar", "float"))
        self._assert_local(mutate, "ingress node identity mismatch")

    def test_different_operand_is_rejected(self):
        def mutate(candidate):
            owner = _owner(candidate)
            replacement = None
            for statement in owner.body:
                for node, _, _ in _walk_statement(statement):
                    if (node.kind == "id" and node.symbol is not None
                            and node.symbol.name == "freq"):
                        replacement = dataclasses.replace(node)
                        break
                if replacement is not None:
                    break
            object.__setattr__(_ingress(candidate), "children", (replacement,))
        self._assert_local(mutate, "ingress node identity mismatch")

    def test_widened_arity_is_rejected(self):
        def mutate(candidate):
            node = _ingress(candidate)
            object.__setattr__(node, "children",
                               (*node.children,
                                dataclasses.replace(node.children[0])))
        self._assert_local(mutate, "ingress node identity mismatch")

    def test_other_declaration_parent_is_rejected(self):
        def mutate(candidate):
            declaration = _declaration(candidate)
            object.__setattr__(declaration, "symbol_id", 99999)
        self._assert_local(mutate, "ingress declaration parent mismatch")

    def test_relocated_statement_fails_the_ancestry_lock(self):
        def mutate(candidate):
            owner = _owner(candidate)
            body = list(owner.body)
            statement = body.pop(13)
            body.insert(16, statement)
            object.__setattr__(owner, "body", tuple(body))
        self._assert_local(mutate, "ingress statement ancestry mismatch")

    def test_renamed_owner_fails_the_owner_identity(self):
        self._assert_local(
            lambda candidate: object.__setattr__(
                _owner(candidate).signature, "name",
                "randomFromLatticeWithOffsetX"),
            "ingress owner identity mismatch")

    def test_unreachable_owner_substitution_is_rejected(self):
        def mutate(candidate):
            for function in candidate.functions:
                if function.name == "randomFromLatticeWithOffset":
                    continue
                calls = []
                for statement in function.body:
                    for node, _, _ in _walk_statement(statement):
                        if (node.kind == "call"
                                and node.signature_id == _owner(candidate).id):
                            calls.append(node)
                for node in calls:
                    object.__setattr__(node, "signature_id", None)
        self._assert_local(mutate, "ingress owner is not reachable from main")

    def test_negative_zero_initializer_fails_the_positive_zero_lock(self):
        module = _module()
        raw = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(1, raw.count("float seedFrac = 0.0;"))
        mutated = raw.replace("float seedFrac = 0.0;", "float seedFrac = -0.0;")
        candidate = _analyzed(raw=mutated)
        declaration = _seed_frac_declaration(candidate)
        self.assertEqual("seedFrac", declaration.symbol.name)
        self.assertEqual("local", declaration.symbol.storage)
        self.assertEqual("declaration", declaration.kind)
        self.assertEqual("float", declaration.type.display())
        self.assertEqual(1, len(declaration.children))
        self.assertEqual("unary", declaration.children[0].kind)
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_float_bits_ingress(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("seedFrac positive-zero initializer mismatch", message)

    def test_positive_zero_lock_reads_the_real_sign_bit(self):
        """Refreezes every span/hash record around the literal so only the
        ``math.copysign`` arm can still fire: the sign bit is load-bearing on
        its own, not a by-product of a node hash."""
        module = _module()
        program = _analyzed()
        declaration = _seed_frac_declaration(program)
        literal = declaration.children[0]
        self.assertEqual("literal", literal.kind)
        self.assertEqual("0.0", literal.literal)
        self.assertEqual(0.0, literal.literal_value)
        self.assertEqual(1.0, math.copysign(1.0, literal.literal_value))
        object.__setattr__(literal, "literal_value", -0.0)
        self.assertEqual(0.0, literal.literal_value)
        self.assertEqual("0.0", literal.literal)
        self.assertEqual(module._span(literal),
                         module._SEED_FRAC_INITIALIZER[1])
        operand = _ingress(program).children[0]
        values = _refrozen(
            module, program,
            _SEED_FRAC_INITIALIZER=(
                literal.kind, module._span(literal), literal.type.display(),
                literal.category, literal.literal, module._sha(literal)),
            _SEED_FRAC_DECLARATION=(
                declaration.kind, module._span(declaration),
                declaration.type.display(), declaration.symbol_id,
                declaration.symbol.name, declaration.symbol.storage,
                declaration.symbol.writable, module._sha(declaration)),
            _SEED_FRAC_REFERENCES=(
                (declaration.kind, module._span(declaration),
                 module._sha(declaration)),
                module._SEED_FRAC_REFERENCES[1],
                (operand.kind, module._span(operand), module._sha(operand))))
        with mock.patch.multiple(module, **values):
            with self.assertRaisesRegex(
                    ValueError, "seedFrac positive-zero initializer mismatch"):
                module.authenticate_shapes_float_bits_ingress(
                    program, values["_RAW_SHA256"], PROFILE)

    def test_extra_seed_frac_reference_fails_the_operand_census(self):
        def mutate(candidate):
            owner = _owner(candidate)
            product = owner.body[14].expressions[0].children[0].children[0]
            source = _ingress(candidate).children[0]
            object.__setattr__(product, "children",
                               (product.children[0],
                                dataclasses.replace(source)))
        self._assert_local(mutate, "seedFrac reference census mismatch")


class ShapesFloatBitsIngressAncestryTests(unittest.TestCase):
    def test_ancestry_binds_the_scalar_xor_authenticator_objects(self):
        module = _module()
        program = _analyzed()
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            authenticate_scalar_uint_xor)
        expected = authenticate_scalar_uint_xor(
            program, RAW_SHA256, SCALAR_UINT_XOR_PROFILE)
        self.assertEqual(3, len(expected))
        declared = _declaration(program).symbol_id
        for node in expected:
            consumer = node.children[0].children[0]
            self.assertEqual(declared, consumer.symbol_id)
        module.authenticate_shapes_float_bits_ingress(
            program, RAW_SHA256, PROFILE)

    def test_foreign_xor_candidate_objects_fail_the_ancestry_binding(self):
        module = _module()
        program = _analyzed()
        separate = _analyzed()
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            authenticate_scalar_uint_xor)
        foreign = authenticate_scalar_uint_xor(
            separate, RAW_SHA256, SCALAR_UINT_XOR_PROFILE)
        with mock.patch.object(module, "authenticate_scalar_uint_xor",
                               return_value=foreign), \
                self.assertRaisesRegex(
                    ValueError, "downstream scalar XOR ancestry mismatch"):
            module.authenticate_shapes_float_bits_ingress(
                program, RAW_SHA256, PROFILE)
        with mock.patch.object(module, "authenticate_scalar_uint_xor",
                               return_value=foreign[:2]), \
                self.assertRaisesRegex(
                    ValueError, "downstream scalar XOR ancestry mismatch"):
            module.authenticate_shapes_float_bits_ingress(
                program, RAW_SHA256, PROFILE)

    def test_broken_xor_operand_chain_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        owner = _owner(candidate)
        constructor = owner.body[14].expressions[0].children[0]
        product = constructor.children[0].children[0]
        object.__setattr__(product, "children",
                           (dataclasses.replace(product.children[1]),
                            product.children[1]))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values), \
                mock.patch.object(
                    module, "authenticate_scalar_uint_xor",
                    return_value=tuple(constructor.children)):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_float_bits_ingress(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("downstream scalar XOR ancestry mismatch",
                      str(raised.exception))

    def test_call_graph_drift_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        loop_proof = candidate.counted_loop_proof
        candidate = dataclasses.replace(
            candidate, counted_loop_proof=dataclasses.replace(
                loop_proof, call_graph_acyclic=False))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_float_bits_ingress(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("loop or call graph profile mismatch",
                      str(raised.exception))

    def test_resource_drift_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        resources = candidate.resources
        candidate = dataclasses.replace(
            candidate, resources=dataclasses.replace(
                resources, uniforms=resources.uniforms[:-1]))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_float_bits_ingress(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("resource or binding signature mismatch",
                      str(raised.exception))


class ShapesFloatBitsIngressLedgerTests(unittest.TestCase):
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
        self.assertEqual(9, module._CONSUMED_LEDGER)
        self.assertEqual(1, len(module.authenticate_shapes_float_bits_ingress(
            _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (8, 10):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError, "ingress visitation ledger mismatch"):
                module.authenticate_shapes_float_bits_ingress(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(1, len(module.authenticate_shapes_float_bits_ingress(
            _analyzed(), RAW_SHA256, PROFILE)))


class ShapesFloatBitsIngressVocabularyTests(unittest.TestCase):
    def test_no_new_capability_token_is_introduced(self):
        _module()
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(
            "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea",
            hashlib.sha256(repr(
                generate_typed_slice.APPROVED_CAPABILITIES).encode()).hexdigest())
        self.assertNotIn("floatBitsToUint",
                         generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("floatBitsToUint", generate_typed_slice._BUILTINS)


if __name__ == "__main__":
    unittest.main()
