"""Focused RED/GREEN proof for the one Shapes rvalue compound assignment.

Written before ``tools/glslcpp/frontend/shapes_rvalue_assign_profile.py``
existed.

Two testing rules carried over from the review of this worker's first two
closures apply here directly:

1. ``Symbol`` embeds its declaration span, so an operator- or value-level
   mutation shifts every enclosing node hash. The production module therefore
   evaluates the operator / operand / target locks **ahead** of node identity,
   and each of those locks is proved load-bearing by *deleting the lock* in a
   scratch copy of the module and showing its message disappears -- not by
   mutating the source and hoping a hash was not what caught it.
2. The census walks global declaration initializers as well as function
   bodies, so a node hidden in one of Shapes' four ``mat3`` globals cannot
   escape into the coarse gate.
"""

from __future__ import annotations

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
MODULE = "tools.glslcpp.frontend.shapes_rvalue_assign_profile"

KEY = "classicNoisedeck/shapes:shapes"
PROFILE = "shapes-rvalue-assign-v1"
RAW_SHA256 = "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0"
SOURCE = CORPUS / "classicNoisedeck/shapes/shapes.glsl"
ASSIGN_SPAN = "42:19-42:39"
COARSE = "source, define, function, whole-program, or interface mismatch"

FOREIGN_SOURCE = (
    "out vec4 fragColor;\n"
    "float helper(float b) {\n"
    "    float a = b *= 2.0;\n"
    "    return a;\n"
    "}\n"
    "void main() {\n"
    "    fragColor = vec4(helper(1.0));\n"
    "}\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("Shapes rvalue-assign profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock predicates.

    A neutralized predicate always reports "holds", which is exactly what
    removing the lock from the source would do. The live module object is
    never touched, so these tests cannot leak state into each other.
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


def _owner(program):
    return next(item for item in program.functions if item.name == "rotate2D")


def _declaration(program):
    return _owner(program).body[0].expressions[0]


def _assign(program):
    return _declaration(program).children[0]


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


def _renode(module, candidate):
    """Refreeze only the *hash* fields the mutated subtree can shift.

    Deliberately does **not** refreeze any semantic field -- the operator, the
    literal text and value, or the target symbol identity keep their frozen
    originals. Refreezing those would hand the mutation to the very lock under
    test and make the deletion experiment vacuous.
    """
    assign = _assign(candidate)
    declaration = _declaration(candidate)
    target, operand = assign.children
    return {
        "_ASSIGN": (*module._ASSIGN[:3], module._sha(assign)),
        "_PARENT": (*module._PARENT[:7], module._sha(declaration)),
        "_TARGET": (*module._TARGET[:8], module._sha(target)),
        "_OPERAND": (*module._OPERAND[:6], module._sha(operand)),
    }


class ShapesRvalueAssignCarrierTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual(PROFILE, module.PROFILE)
        self.assertEqual(KEY, module.SHAPES_KEY)
        self.assertEqual(frozenset({KEY}), module.SHAPES_RVALUE_ASSIGN_KEYS)
        self.assertIsInstance(module.SHAPES_RVALUE_ASSIGN_KEYS, frozenset)
        for name in ("PROFILE", "SHAPES_KEY", "SHAPES_RVALUE_ASSIGN_KEYS",
                     "authenticate_shapes_rvalue_assign",
                     "apply_shapes_rvalue_assign"):
            self.assertIn(name, module.__all__)

    def test_authenticates_exactly_one_candidate_owned_rvalue_assign(self):
        module = _module()
        program = _analyzed()
        resolved = module.authenticate_shapes_rvalue_assign(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(resolved, tuple)
        self.assertEqual(1, len(resolved))
        node = resolved[0]
        self.assertIs(_assign(program), node)
        self.assertEqual("assign", node.kind)
        self.assertEqual("*=", node.operator)
        self.assertEqual(ASSIGN_SPAN, module._span(node))
        self.assertEqual("float", node.type.display())
        self.assertEqual(2, len(node.children))
        target, operand = node.children
        self.assertEqual("rot", target.symbol.name)
        self.assertEqual("parameter", target.symbol.storage)
        self.assertEqual("3.14159265359", operand.literal)
        self.assertIs(program, module.apply_shapes_rvalue_assign(
            program, RAW_SHA256, PROFILE))

    def test_the_dead_construct_claim_is_true_of_the_real_program(self):
        """The claim boundary is a fact about the tree, not a disclaimer.

        Walks global declaration initializers as well as function bodies: the
        test that establishes the claim must not have the very blind spot the
        census was widened to close.
        """
        program = _analyzed()
        owner = _owner(program)
        nodes = list(_walk_whole_program(program))
        self.assertEqual(
            4, sum(1 for item in program.declarations
                   if item.initializer is not None),
            "the four mat3 globals must be inside the walk")
        calls = [node for node in nodes
                 if node.kind == "call" and node.signature_id == owner.id]
        self.assertEqual([], calls, "rotate2D must have zero callers")
        references = [node for node in nodes
                      if node.symbol_id == owner.parameters[1].id]
        self.assertEqual(1, len(references))
        self.assertIs(_assign(program).children[0], references[0])

    def test_non_carrier_key_returns_empty_and_names_shapes_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_shapes_rvalue_assign(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "scalar-uint-xor-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted Shapes rvalue-assign carrier"):
                module.authenticate_shapes_rvalue_assign(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_new_rejection_at_the_widened_boundary_names_shapes(self):
        """The widened emitter arm is gated on identity, so a foreign program
        carrying the identical construct must never reach admission."""
        module = _module()
        foreign = _foreign()
        nested = [node for function in foreign.functions
                  for statement in function.body
                  for node, parent in _walk_parented(statement)
                  if node.kind == "assign" and parent is not None]
        self.assertEqual(1, len(nested), "fixture must carry the construct")
        self.assertEqual("*=", nested[0].operator)
        with self.assertRaises(ValueError) as raised:
            module.authenticate_shapes_rvalue_assign(
                foreign, _hash(FOREIGN_SOURCE), PROFILE)
        message = str(raised.exception)
        self.assertIn("classicNoisedeck/shapes:shapes", message)
        self.assertIn(ASSIGN_SPAN, message)
        self.assertEqual((), module.authenticate_shapes_rvalue_assign(
            foreign, _hash(FOREIGN_SOURCE), None))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "scalar-uint-xor-v1",
                        "shapes-float-bits-ingress-v1",
                        "linear-srgb-shapes-lane-index-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_shapes_rvalue_assign(
                    program, RAW_SHA256, carrier)

    def test_rejects_wrong_caller_source_hash_and_source_drift(self):
        module = _module()
        with self.assertRaisesRegex(ValueError, COARSE):
            module.authenticate_shapes_rvalue_assign(
                _analyzed(), "0" * 64, PROFILE)
        mutated = SOURCE.read_text(encoding="utf-8").replace(
            "float angle = rot *= PI;", "float angle = rot *= PI * 2.0;")
        with self.assertRaisesRegex(ValueError, COARSE):
            module.authenticate_shapes_rvalue_assign(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_shapes_rvalue_assign(
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
                        module.authenticate_shapes_rvalue_assign(
                            candidate, values["_RAW_SHA256"], PROFILE)
                message = str(raised.exception)
                self.assertNotIn(COARSE, message, label)
                self.assertIn(expected, message, label)


def _walk(statement):
    def expression(value):
        yield value
        for child in value.children:
            yield from expression(child)
    for item in statement.expressions:
        yield from expression(item)
    for child in statement.children:
        yield from _walk(child)


def _walk_parented(statement):
    def expression(value, parent=None):
        yield value, parent
        for child in value.children:
            yield from expression(child, value)
    for item in statement.expressions:
        yield from expression(item)
    for child in statement.children:
        yield from _walk_parented(child)


def _walk_whole_program(program):
    """Every expression node, global declaration initializers included."""
    def expression(value):
        yield value
        for child in value.children:
            yield from expression(child)
    for declaration in program.declarations:
        if declaration.initializer is not None:
            yield from expression(declaration.initializer)
    for function in program.functions:
        for statement in function.body:
            yield from _walk(statement)


class ShapesRvalueAssignCensusTests(unittest.TestCase):
    def test_census_counts_are_the_real_program_counts(self):
        module = _module()
        self.assertEqual(1, module._RVALUE_ASSIGN_CENSUS)
        self.assertEqual(58, module._TOTAL_ASSIGN_CENSUS)

    def test_a_second_rvalue_assignment_anywhere_is_a_hard_failure(self):
        module = _module()
        candidate = _analyzed()
        other = _owner(candidate).body[1].expressions[0]
        object.__setattr__(other, "children",
                           (other.children[0],
                            dataclasses.replace(_assign(candidate))))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("rvalue assignment census cardinality mismatch: 2",
                      str(raised.exception))

    def test_census_walks_global_declaration_initializers(self):
        """Shapes has four `mat3` globals with initializers; a node hidden in
        one must be censused, not left to the coarse gate."""
        module = _module()
        candidate = _analyzed()
        globals_with_initializers = [item for item in candidate.declarations
                                     if item.initializer is not None]
        self.assertEqual(
            ["fwdA", "fwdB", "invB", "invA"],
            [item.symbol.name for item in globals_with_initializers])
        initializer = globals_with_initializers[0].initializer
        object.__setattr__(initializer, "children",
                           (*initializer.children,
                            dataclasses.replace(_assign(candidate))))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("rvalue assignment census cardinality mismatch: 2",
                      message)

    def test_a_removed_statement_level_assignment_fails_the_total_census(self):
        module = _module()
        candidate = _analyzed()
        other = next(item for item in candidate.functions
                     if item.name == "sineNoise")
        self.assertEqual("assign", other.body[0].expressions[0].kind)
        object.__setattr__(other, "body", other.body[1:])
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("total assignment census mismatch: 57", message)

    def test_a_nested_assignment_in_another_function_hits_the_owner_guard(self):
        """Covers the `outside the owner function` branch, which a second node
        planted inside `rotate2D` never reaches -- that lands on cardinality."""
        module = _module()
        candidate = _analyzed()
        other = next(item for item in candidate.functions
                     if item.name == "sineNoise")
        host = other.body[0].expressions[0]
        self.assertEqual("assign", host.kind)
        object.__setattr__(host, "children",
                           (host.children[0],
                            dataclasses.replace(_assign(candidate))))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("rvalue assignment outside the owner function", message)

    def test_a_count_preserving_relocation_out_of_an_expr_statement_is_caught(self):
        """The census selects by "not statement-rooted", not by parent.

        Re-kinding an `expr` statement whose sole expression is an assignment
        leaves `_TOTAL_ASSIGN_CENSUS` at 58, so a parent-based census would
        have let this reach the emitter's expression dispatcher unadmitted,
        visible only to the refrozen function hash. It is caught here.
        """
        module = _module()
        candidate = _analyzed()
        other = next(item for item in candidate.functions
                     if item.name == "sineNoise")
        statement = other.body[0]
        self.assertEqual("expr", statement.kind)
        self.assertEqual(1, len(statement.expressions))
        self.assertEqual("assign", statement.expressions[0].kind)
        self.assertIsNone(
            next((node for node, parent in _walk_parented(statement)
                  if node.kind == "assign" and parent is not None), None),
            "the relocated node must have no expression parent")
        object.__setattr__(statement, "kind", "return")
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("rvalue assignment outside the owner function", message)

    def test_statement_rooted_predicate_agrees_with_the_frozen_counts(self):
        """The tightening must be a no-op on valid input."""
        module = _module()
        program = _analyzed()
        rooted = 0
        nested = 0
        for function in program.functions:
            for index, statement in enumerate(function.body):
                for item, parent, _, chain, expression_index in \
                        module._walk_statement(statement, (index,)):
                    if item.kind != "assign":
                        continue
                    if module._is_statement_rooted(parent, chain[-1],
                                                   expression_index):
                        rooted += 1
                    else:
                        nested += 1
        self.assertEqual(module._TOTAL_ASSIGN_CENSUS, rooted + nested)
        self.assertEqual(module._RVALUE_ASSIGN_CENSUS, nested)
        self.assertEqual(57, rooted)
        self.assertFalse(module._is_statement_rooted(None, None, 0),
                         "a global initializer root is never statement-rooted")

    def test_an_added_statement_level_assignment_fails_the_total_census(self):
        module = _module()
        candidate = _analyzed()
        other = next(item for item in candidate.functions
                     if item.name == "sineNoise")
        # A whole extra `expr` statement, so the added assignment is itself
        # statement-rooted and only the total census can see it.
        object.__setattr__(other, "body",
                           (*other.body,
                            dataclasses.replace(other.body[0])))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("total assignment census mismatch: 59", message)


class ShapesRvalueAssignLockDeletionTests(unittest.TestCase):
    """Each lock is proved load-bearing by deleting it, not by hoping.

    For every lock: mutate the tree, refreeze both the coarse hashes and every
    node hash the mutation shifts, then show (a) the real module rejects with
    that lock's message and (b) a scratch copy with only that predicate
    deleted no longer produces the message.
    """

    def _delete_and_compare(self, mutate, predicate, expected):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        values = _refrozen(module, candidate, **_renode(module, candidate))
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message,
                         f"{expected} was absorbed by the coarse gate")
        self.assertIn(expected, message)

        scratch = _scratch(module, predicate)
        for name, value in values.items():
            setattr(scratch, name, value)
        try:
            scratch.authenticate_shapes_rvalue_assign(
                candidate, values["_RAW_SHA256"], PROFILE)
            survived = None
        except ValueError as error:
            survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def test_operator_lock_is_the_sole_catcher_of_a_changed_operator(self):
        def mutate(candidate):
            object.__setattr__(_assign(candidate), "operator", "+=")
        survived = self._delete_and_compare(
            mutate, "_operator_holds", "compound assignment operator mismatch")
        self.assertIsNone(
            survived,
            "with the operator lock deleted nothing else rejects the mutant")

    def test_operand_lock_is_the_sole_catcher_of_a_changed_constant(self):
        def mutate(candidate):
            operand = _assign(candidate).children[1]
            object.__setattr__(operand, "literal", "3.0")
            object.__setattr__(operand, "literal_value", 3.0)
        survived = self._delete_and_compare(
            mutate, "_operand_holds", "compound assignment operand mismatch")
        self.assertIsNone(
            survived,
            "with the operand lock deleted nothing else rejects the mutant")

    def test_target_lock_catches_a_retargeted_assignment(self):
        def mutate(candidate):
            target = _assign(candidate).children[0]
            object.__setattr__(target, "symbol_id", 99999)
        survived = self._delete_and_compare(
            mutate, "_target_holds", "assignment target symbol mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("rot reference census mismatch", survived)

    def test_node_identity_lock_catches_a_span_only_forgery(self):
        module = _module()
        candidate = _analyzed()
        assign = _assign(candidate)
        object.__setattr__(assign, "span",
                           dataclasses.replace(assign.span, start_column=20))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("rvalue assignment node identity mismatch", message)

        scratch = _scratch(module, "_node_identity_holds")
        for name, value in values.items():
            setattr(scratch, name, value)
        with self.assertRaises(ValueError) as raised:
            scratch.authenticate_shapes_rvalue_assign(
                candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn("rvalue assignment node identity mismatch",
                         str(raised.exception))

    def test_relocated_declaration_fails_the_owner_body_shape(self):
        """Named for what it actually proves: a reordered owner body is caught
        by the body-shape lock, well before ancestry is consulted."""
        module = _module()
        candidate = _analyzed()
        owner = _owner(candidate)
        body = list(owner.body)
        body.insert(3, body.pop(0))
        object.__setattr__(owner, "body", tuple(body))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("rotate2D owner body shape mismatch",
                      str(raised.exception))

    def test_ancestry_lock_is_the_sole_catcher_of_a_shifted_expression_path(self):
        """Reaches `_ancestry_holds` for real.

        Prepending a non-assignment expression to the declaration statement
        shifts the assignment's expression path from ``(0,'e0',0)`` to
        ``(0,'e1',0)`` while leaving every earlier lock satisfied: the owner
        body's statement kinds and spans are unchanged, both census counts are
        unchanged, and the assignment, its operands and its declaration parent
        are the same objects with the same hashes.
        """
        module = _module()
        candidate = _analyzed()
        statement = _owner(candidate).body[0]
        planted = dataclasses.replace(_assign(candidate).children[1])
        object.__setattr__(statement, "expressions",
                           (planted, *statement.expressions))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message,
                         "ancestry was absorbed by the coarse gate")
        self.assertIn("rvalue assignment ancestry mismatch", message)

        scratch = _scratch(module, "_ancestry_holds")
        for name, value in values.items():
            setattr(scratch, name, value)
        scratch.authenticate_shapes_rvalue_assign(
            candidate, values["_RAW_SHA256"], PROFILE)

    def test_renamed_owner_fails_the_owner_identity(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(_owner(candidate).signature, "name", "rotate2Dx")
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("rotate2D owner identity mismatch",
                      str(raised.exception))

    def test_declaration_parent_identity_is_locked(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(_declaration(candidate), "symbol_id", 99999)
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("rvalue assignment declaration parent mismatch",
                      str(raised.exception))

    def test_operand_replaced_by_a_target_copy_fails_the_operand_lock(self):
        """Renamed from a reference-census claim it never made: replacing the
        operand trips `_operand_holds` long before the census is reached."""
        module = _module()
        candidate = _analyzed()
        assign = _assign(candidate)
        object.__setattr__(assign, "children",
                           (assign.children[0],
                            dataclasses.replace(assign.children[0])))
        values = _refrozen(module, candidate,
                           **{k: v for k, v in _renode(module, candidate).items()
                              if k in {"_ASSIGN", "_PARENT", "_OPERAND"}})
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        self.assertNotIn(COARSE, str(raised.exception))
        self.assertIn("compound assignment operand mismatch",
                      str(raised.exception))

    def test_reference_census_catches_a_rot_read_in_another_function(self):
        """Reaches `_reference_census_holds` directly.

        Planting a second `rot` reference outside `rotate2D` leaves the
        assignment subtree, both censuses and the ancestry untouched, so the
        reference census is the first and only lock that can fire.
        """
        module = _module()
        candidate = _analyzed()
        other = next(item for item in candidate.functions
                     if item.name == "sineNoise")
        host = other.body[0].expressions[0]
        self.assertEqual("assign", host.kind)
        planted = dataclasses.replace(_assign(candidate).children[0])
        # Planted *inside* the right-hand side, so the host assignment stays
        # the sole expression of its `expr` statement and both censuses hold.
        object.__setattr__(host, "children", (host.children[0], planted))
        values = _refrozen(module, candidate)
        with mock.patch.multiple(module, **values):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_shapes_rvalue_assign(
                    candidate, values["_RAW_SHA256"], PROFILE)
        message = str(raised.exception)
        self.assertNotIn(COARSE, message)
        self.assertIn("rot reference census mismatch", message)

        scratch = _scratch(module, "_reference_census_holds")
        for name, value in values.items():
            setattr(scratch, name, value)
        scratch.authenticate_shapes_rvalue_assign(
            candidate, values["_RAW_SHA256"], PROFILE)


class ShapesRvalueAssignLedgerTests(unittest.TestCase):
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
        self.assertEqual(6, module._CONSUMED_LEDGER)
        self.assertEqual(1, len(module.authenticate_shapes_rvalue_assign(
            _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (5, 7):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError, "rvalue-assign visitation ledger mismatch"):
                module.authenticate_shapes_rvalue_assign(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(1, len(module.authenticate_shapes_rvalue_assign(
            _analyzed(), RAW_SHA256, PROFILE)))


class ShapesRvalueAssignVocabularyTests(unittest.TestCase):
    def test_no_capability_type_or_operator_vocabulary_growth(self):
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
        self.assertIn("*=", generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS)
        # `assign` is a PRE-EXISTING token covering statement-level assignment;
        # this closure must not add an rvalue-flavoured one beside it.
        self.assertIn("assign", generate_typed_slice.APPROVED_CAPABILITIES)
        for token in (PROFILE, "rvalue-assign", "rvalue-assignment",
                      "assign-expression"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)


if __name__ == "__main__":
    unittest.main()
