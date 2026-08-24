"""Focused RED/GREEN proof for grime's five ``floatBitsToUint`` ingress
sites -- the dict-keyed fifth float-bit identity-admission carrier.

Written before ``tools/glslcpp/frontend/grime_float_bits_ingress_profile.py``
existed; the first run of this file reported ``ModuleNotFoundError`` from
``_module`` for every test in it.

The four paid-for precedents (design 3.2) are ``caustic_word_hash_profile``
(one site), ``scanline_error_float_bits_ingress_profile`` (three sites),
``shapes_float_bits_ingress_profile`` (one site) and
``shape_mixer_builtin_profile``; all four are **single-key** modules -- a
frozen module-level record plus a single-key authenticator, two of them with
a frozen ``_FROZEN_PROFILE_TUPLE_REPR`` self-hash of the module constants
themselves. Extending any of them per-key would churn landed frozen code
(shapes' carrier is welded to its scalar-XOR downstream ancestry and the
``seedFrac`` positive-zero initializer; scanline's is welded to its
single-parent three-node tuple), so grime's record is a NEW dict-keyed
module in the ``varying_uv_profile`` shape: per-key ``_LOCKS`` row, landed
``KEYS``/prepared ``PREPARED_KEYS`` split, and individually deletable lock
predicates.

grime reaches ``floatBitsToUint`` exactly five times, all in reachable code
(design 3): twice in ``hash21`` (normalized ``38:25-38:45`` and
``38:47-38:67`` -- the ``uvec3(floatBitsToUint(p.x), floatBitsToUint(p.y),
0u)`` constructor) and three times in ``hash31`` (``43:25-43:45``,
``43:47-43:67``, ``43:69-43:89``). Everything else grime needs is already
admitted: its ``pcg`` is the *vector* form and rides the existing
uint-vector-bitwise capability exactly as wobble's identical ``pcg`` does.

The JavaScript authority, quoted and cross-validated (design 4.4's method):
``canonicalFactory66`` (``canonical-kernels.js:13836``, registered for
``filter/grime:grime`` at ``:36246``) destructures ``floatBitsToUint`` once
from ``$runtime.stdlib`` (``:13837``) and calls it at exactly the five
sites -- ``:13871`` (hash21) and ``:13876`` (hash31). The runtime's
implementation (``glsl-runtime.js:411-414``) is an exact bit reinterpretation
through a shared ArrayBuffer view (``this.bitsFloat[0] = value; return
this.bitsUint[0]``). The factory's ``Function.prototype.toString`` SHA-256
is ``c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f``
(8,413 bytes, byte-equal to the generated-file slice), and the pinning
method reproduces the wobble oracle's frozen cellRefract digest
``329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`` on the
same snapshot and node -- measured by the grime frontend lane probe before
freezing.
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

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program, named_type


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.grime_float_bits_ingress_profile"
VARYING_MODULE = "tools.glslcpp.frontend.varying_uv_profile"

KEY = "filter/grime:grime"
PROFILE = "grime-float-bits-ingress-v1"
ROW_FIELD = "grime_float_bits_ingress_profile"
SOURCE_PATH = "filter/grime/grime.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "15a88fff0e951bf7fa01f4c982532cf79d835663cb2a81c2076c5fecbd9c351f"
NORMALIZED_SHA256 = (
    "692547b5193d0c03b3cb5fe86c570fff5ea74149affa6a5c88dac8c5b83eeba1")

HASH21_ID = 45
HASH31_ID = 46
SITE_COUNT = 5
LEDGER = 11  # both owners + five sites + both constructs + both statements

FACTORY_NAME = "canonicalFactory66"
FACTORY_TO_STRING_SHA256 = (
    "c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f")
CROSS_VALIDATION_DIGEST = (
    "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3")

COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)

FOREIGN_SOURCE = (
    "uniform float t;\n"
    "out vec4 fragColor;\n"
    "float h(float x) { return float(floatBitsToUint(x)) / 4294967296.0; }\n"
    "void main() { fragColor = vec4(h(t), 0.0, 0.0, 1.0); }\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("grime float-bits ingress profile module is absent")
    return importlib.import_module(MODULE)


def _varying_module():
    return importlib.import_module(VARYING_MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock predicates."""
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


def _fn(program, name):
    return next(item for item in program.functions if item.name == name)


def _sites(program):
    """Every floatBitsToUint builtin node, whole program, walk order."""
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
    for declaration in program.declarations:
        if declaration.initializer is not None:
            yield from expression(declaration.initializer)


def _float_bits_nodes(program):
    return [item for item in _sites(program)
            if item.kind == "builtin" and item.callee == "floatBitsToUint"]


def _construct(program, owner_name):
    """The uvec3 construct owning a given hash function's sites."""
    function = _fn(program, owner_name)
    return function.body[0].expressions[0].children[0].children[0]


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
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        locks[key].update(values[name])
    locks[key].update(overrides)
    return locks


def _relocked_partial(module, candidate, upto, key=KEY):
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


def _recallgraph(module, candidate, key=KEY):
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
        return module.authenticate_grime_float_bits_ingress(
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


class GrimeFloatBitsSurfaceTests(unittest.TestCase):
    def test_the_module_is_dict_keyed_with_grime_landed(self):
        """The landed/prepared split (the varying module's shape): grime's
        key moved into ``KEYS`` together with its row, the one-line move the
        design records. The registry and the slice stay in lockstep -- a key
        in ``KEYS`` without a row reddens the live schema census, and a row
        without the key reddens it the other way."""
        module = _module()
        self.assertEqual((KEY,), module.KEYS)
        self.assertEqual({KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({KEY}),
                         module.GRIME_FLOAT_BITS_INGRESS_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual({}, module.PREPARED_PROFILES)
        self.assertIn(KEY, module.ALLOWED_ROW_FIELDS)
        self.assertEqual((KEY,), tuple(module._LOCKS))

    def test_the_row_field_and_profile_names_follow_the_convention(self):
        """Module name == row field == the scanline/shapes convention; the
        profile string is the fifth float-bit identity-admission name."""
        module = _module()
        self.assertEqual(ROW_FIELD, module.GRIME_FLOAT_BITS_INGRESS_FIELD)
        self.assertEqual(
            pathlib.Path(module.__file__).name,
            f"{ROW_FIELD}.py")
        self.assertIn("float-bits-ingress-v1", PROFILE)

    def test_the_row_contract_matches_the_varying_module_for_grime(self):
        """One source of truth for grime's landed row: the varying module's
        ``ALLOWED_ROW_FIELDS`` imports this module's field name, so the two
        frozen contracts cannot drift apart."""
        module = _module()
        varying = _varying_module()
        self.assertEqual(
            varying.ALLOWED_ROW_FIELDS[KEY],
            module.ALLOWED_ROW_FIELDS[KEY])
        self.assertEqual(
            frozenset({"defines", "program_key", "varying_profile",
                       ROW_FIELD}),
            module.ALLOWED_ROW_FIELDS[KEY])
        self.assertEqual(frozenset(module.ALLOWED_ROW_FIELDS[KEY]),
                         module.allowed_row_fields(KEY))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("filter/texture:texture")

    def test_the_live_slice_carries_the_ingress_row(self):
        """The RED state this record lifted: exactly grime's row carries the
        field, and grime is a typed row."""
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        self.assertEqual(
            [KEY], [row["program_key"] for row in spec["programs"]
                    if ROW_FIELD in row])
        row = next(row for row in spec["programs"]
                   if row["program_key"] == KEY)
        self.assertEqual(PROFILE, row[ROW_FIELD])

    def test_the_emitter_first_blocker_is_the_float_bits_site(self):
        """Design 2 named ``38:25`` (grime's ``hash31`` sorts ahead of
        ``main``) as the emitter's first blocker. That blocker is LIFTED: the
        carrier admits the five sites, so an uncarried render now fails one
        rung earlier, at the required-carrier arm. Both facts are the same
        contract seen from either side of the landing."""
        program = _analyzed()
        with self.assertRaises(Exception) as raised:
            emit_typed_cpp.render_typed_cpp(program, KEY, RAW_SHA256)
        self.assertIn("exact grime float-bit ingress profile carrier required",
                      str(raised.exception))

    def test_no_capability_or_type_vocabulary_growth(self):
        module = _module()
        for token in (PROFILE, "floatBitsToUint", "grime"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)
                self.assertNotIn(token, generate_typed_slice.APPROVED_TYPES)
        before = (generate_typed_slice.APPROVED_CAPABILITIES,
                  generate_typed_slice.APPROVED_TYPES)
        module.authenticate_grime_float_bits_ingress(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(before[0],
                         generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)

    def test_every_failure_names_the_profile_not_a_module_global(self):
        module = _module()
        prefix = re.escape(f"{PROFILE}: ")
        for caller, arguments in (
                ("carrier", (_analyzed(), RAW_SHA256, "wrong")),
                ("non-carrier", (_foreign(), _hash(FOREIGN_SOURCE), PROFILE)),
                ("row fields", ("filter/texture:texture",))):
            with self.subTest(site=caller), self.assertRaises(ValueError) as ctx:
                if caller == "row fields":
                    module.allowed_row_fields(*arguments)
                else:
                    module.authenticate_grime_float_bits_ingress(*arguments)
            self.assertRegex(str(ctx.exception), f"^{prefix}")


class GrimeFloatBitsAdmissionTests(unittest.TestCase):
    def test_authenticates_the_five_sites_by_object_identity(self):
        module = _module()
        program = _analyzed()
        admitted = module.authenticate_grime_float_bits_ingress(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(admitted, tuple)
        self.assertEqual(SITE_COUNT, len(admitted))
        expected = _float_bits_nodes(program)
        self.assertEqual(len(expected), SITE_COUNT)
        for node, wanted in zip(admitted, expected):
            self.assertIs(wanted, node)
        self.assertEqual(
            ("38:25-38:45", "38:47-38:67", "43:25-43:45",
             "43:47-43:67", "43:69-43:89"),
            tuple(module._span(node) for node in admitted))
        self.assertIs(program, module.apply_grime_float_bits_ingress(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        """The foreign-carrier sweep (design 6.3): every sibling profile
        string -- including the varying carrier and the other float-bit
        precedents -- is rejected; only the exact string admits."""
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong",
                        "varying-uv-admission-v1",
                        "scanline-error-float-bits-ingress-v1",
                        "shapes-float-bits-ingress-v1",
                        "caustic-float-bits-scalar-word-hash-v1",
                        "scalar-uint-xor-v1",
                        "grime-float-bits-ingress-v2"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_grime_float_bits_ingress(
                    program, RAW_SHA256, carrier)

    def test_a_foreign_key_is_never_a_carrier(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_grime_float_bits_ingress(
            foreign, _hash(FOREIGN_SOURCE), None))
        with self.assertRaisesRegex(
                ValueError, "program key is not an admitted grime "
                            "float-bit ingress carrier"):
            module.authenticate_grime_float_bits_ingress(
                foreign, _hash(FOREIGN_SOURCE), PROFILE)

    def test_the_foreign_fixture_really_carries_the_construct(self):
        nodes = _float_bits_nodes(_foreign())
        self.assertEqual(1, len(nodes),
                         "the boundary rejection must not be about absence")

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_grime_float_bits_ingress(
                _analyzed(), "0" * 64, PROFILE)

    def test_define_drift_fails_the_defines_lock(self):
        module = _module()
        candidate = _analyzed()
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine
        object.__setattr__(
            candidate, "preprocessor_defines",
            (PreprocessorDefine("MODE", "int", "4"),))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "exact preprocessor define lock mismatch")


class GrimeFloatBitsSiteTests(unittest.TestCase):
    def test_a_sixth_site_fails_the_census(self):
        module = _module()
        candidate = _analyzed()
        construct = _construct(candidate, "hash21")
        object.__setattr__(
            construct, "children",
            (*construct.children, dataclasses.replace(construct.children[0])))
        locks = _relocked(module, candidate, **_recount(module, candidate))
        message = _expect(self, module, candidate, locks,
                          "float-bit ingress census mismatch")
        self.assertIn("6", message)

    def test_a_lost_site_fails_the_census(self):
        module = _module()
        candidate = _analyzed()
        node = _float_bits_nodes(candidate)[4]
        object.__setattr__(node, "callee", "uintBitsToFloat")
        locks = _relocked(module, candidate)
        message = _expect(self, module, candidate, locks,
                          "float-bit ingress census mismatch")
        self.assertIn("4", message)

    def test_a_retyped_site_fails_the_site_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        node = _float_bits_nodes(candidate)[0]
        object.__setattr__(node, "type", named_type("int", {}))
        locks = _relocked(module, candidate)
        survived = None
        _expect(self, module, candidate, locks,
                "ingress site identity mismatch")
        scratch = _scratch(module, "_site_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
            except ValueError as error:
                survived = str(error)
        self.assertIsNotNone(survived)
        self.assertIn("ingress construct parent mismatch", survived)

    def test_a_swapped_operand_fails_the_site_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        node = _float_bits_nodes(candidate)[0]
        sibling = _float_bits_nodes(candidate)[1]
        object.__setattr__(node, "children",
                           (sibling.children[0],))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "ingress site identity mismatch")

    def test_the_zero_literal_child_fails_the_parent_lock_when_mutated(self):
        """hash21's construct third lane is the ``0u`` literal (JS ``0``);
        ``1u`` must fail the parent lock, not any coarse gate."""
        module = _module()
        candidate = _analyzed()
        literal = _construct(candidate, "hash21").children[2]
        self.assertEqual("literal", literal.kind)
        object.__setattr__(literal, "literal", "1u")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "ingress construct parent mismatch")

    def test_an_owner_body_growth_fails_the_owner_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        hash21 = _fn(candidate, "hash21")
        object.__setattr__(
            hash21, "body", (*hash21.body, dataclasses.replace(hash21.body[0])))
        locks = _relocked(module, candidate, **_recount(module, candidate))
        survived = None
        _expect(self, module, candidate, locks,
                "ingress owner identity mismatch")
        scratch = _scratch(module, "_owner_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
            except ValueError as error:
                survived = str(error)
        self.assertIsNotNone(survived)
        self.assertIn("float-bit ingress census mismatch", survived)

    def test_a_statement_swap_fails_the_ancestry_lock(self):
        """Swapping hash21's decl and return statements moves every site's
        statement index from 0 to 1 without touching any node identity."""
        module = _module()
        candidate = _analyzed()
        hash21 = _fn(candidate, "hash21")
        object.__setattr__(hash21, "body", (hash21.body[1], hash21.body[0]))
        locks = _relocked(module, candidate)
        survived = None
        _expect(self, module, candidate, locks,
                "ingress statement ancestry mismatch")
        scratch = _scratch(module, "_statement_ancestry_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        self.assertIsNone(
            survived, "with the ancestry lock deleted the swap is unguarded")

    def test_a_broken_js_evidence_fails_the_evidence_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["js_evidence"] = (*locks[KEY]["js_evidence"][:-1],
                                     "planted")
        _expect(self, module, candidate, locks,
                "ingress JS evidence mismatch")
        scratch = _scratch(module, "_js_evidence_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertEqual(
                SITE_COUNT, len(scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)))


class GrimeFloatBitsCensusTests(unittest.TestCase):
    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        candidate = _analyzed()
        lock = module._LOCKS[KEY]
        self.assertEqual((645, 15), module._node_census(candidate))
        self.assertEqual(645, lock["total_nodes"])
        self.assertEqual(15, lock["total_assigns"])
        self.assertEqual(14, lock["function_count"])
        self.assertEqual(7, lock["declaration_count"])
        self.assertEqual((), module._initializer_census(candidate))
        self.assertEqual(22, len(module._call_graph(candidate)))

    def test_the_five_sites_are_two_plus_three_in_the_two_hash_owners(self):
        module = _module()
        candidate = _analyzed()
        lock = module._LOCKS[KEY]
        nodes = _float_bits_nodes(candidate)

        def owner_of(node):
            for function in candidate.functions:
                for statement in function.body:
                    def walk_expression(value):
                        if value is node:
                            return function
                        for child in value.children:
                            found = walk_expression(child)
                            if found is not None:
                                return found
                        return None
                    def walk_statement(item):
                        for expr in item.expressions:
                            found = walk_expression(expr)
                            if found is not None:
                                return found
                        for child in item.children:
                            found = walk_statement(child)
                            if found is not None:
                                return found
                        return None
                    found = walk_statement(statement)
                    if found is not None:
                        return found
            return None
        by_owner: dict[str, list] = {}
        for node in nodes:
            by_owner.setdefault(owner_of(node).name, []).append(node)
        self.assertEqual({"hash21": 2, "hash31": 3},
                         {name: len(items) for name, items in
                          by_owner.items()})
        self.assertEqual(
            ("38:25-38:45", "38:47-38:67"),
            tuple(module._span(item) for item in by_owner["hash21"]))
        self.assertEqual(
            ("43:25-43:45", "43:47-43:67", "43:69-43:89"),
            tuple(module._span(item) for item in by_owner["hash31"]))
        self.assertEqual(
            ((HASH21_ID, "hash21", "float", 2), (HASH31_ID, "hash31",
                                                 "float", 2)),
            tuple((row[0], row[1], row[2], row[4]) for row in lock["owners"]))

    def test_the_operands_are_swizzles_of_the_p_parameters(self):
        module = _module()
        candidate = _analyzed()
        for node in _float_bits_nodes(candidate):
            operand = node.children[0]
            self.assertEqual("swizzle", operand.kind)
            self.assertEqual("float", operand.type.display())
            base = operand.children[0]
            self.assertEqual("id", base.kind)
            self.assertEqual("p", base.symbol.name)
            self.assertIn(base.symbol_id, (13, 14))

    def test_the_parents_are_the_two_uvec3_constructs(self):
        module = _module()
        candidate = _analyzed()
        construct21 = _construct(candidate, "hash21")
        construct31 = _construct(candidate, "hash31")
        for construct, third in ((construct21, "0u"), (construct31, None)):
            self.assertEqual("construct", construct.kind)
            self.assertEqual("uvec3", construct.type.display())
            self.assertEqual(3, len(construct.children))
            for child in construct.children[:2 if third else 3]:
                self.assertEqual("builtin", child.kind)
                self.assertEqual("floatBitsToUint", child.callee)
        self.assertEqual("literal", construct21.children[2].kind)
        self.assertEqual("0u", construct21.children[2].literal)

    def test_the_js_evidence_quotes_the_authority(self):
        module = _module()
        evidence = module._LOCKS[KEY]["js_evidence"]
        self.assertEqual(module._JS_EVIDENCE, evidence)
        joined = "\n".join(evidence)
        self.assertIn(FACTORY_NAME, joined)
        self.assertIn(FACTORY_TO_STRING_SHA256, joined)
        self.assertIn(CROSS_VALIDATION_DIGEST, joined)
        for quote in (
                "var v = pcg(cpu_uvec3(floatBitsToUint(p[0]), "
                "floatBitsToUint(p[1]), 0));",
                "var v = pcg(cpu_uvec3_float_float_float(floatBitsToUint("
                "p[0]), floatBitsToUint(p[1]), floatBitsToUint(p[2])));",
                "this.bitsFloat[0] = value",
                "return this.bitsUint[0]"):
            self.assertIn(quote, joined)
        # every line cites its source location or carries a measured digest
        for line in evidence:
            self.assertTrue(
                re.search(r"canonical-kernels\.js:\d+"
                          r"|glsl-runtime\.js:\d+", line)
                or re.search(r"[0-9a-f]{64}", line),
                f"evidence line cites neither a location nor a digest: "
                f"{line[:60]}")


class GrimeFloatBitsLedgerTests(unittest.TestCase):
    def test_the_ledger_counts_every_consumed_object_once(self):
        module = _module()
        self.assertEqual(LEDGER, module._LOCKS[KEY]["consumed_ledger"])
        self.assertEqual(
            2 + SITE_COUNT + 2 + 2, module._LOCKS[KEY]["consumed_ledger"],
            "both owners + five sites + both constructs + both statements")

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(
            SITE_COUNT, len(module.authenticate_grime_float_bits_ingress(
                _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            locks = copy.deepcopy(module._LOCKS)
            locks[KEY]["consumed_ledger"] = sabotage
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_LOCKS", locks), \
                    self.assertRaisesRegex(
                        ValueError,
                        "float-bit ingress visitation ledger mismatch"):
                module.authenticate_grime_float_bits_ingress(
                    _analyzed(), RAW_SHA256, PROFILE)


class GrimeFloatBitsLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK (the tabulated
    sweep; the census below is the mechanical completeness claim)."""

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
        "_owner_identity_holds",
        "_ingress_census_holds",
        "_site_identity_holds",
        "_parent_identity_holds",
        "_statement_ancestry_holds",
        "_js_evidence_holds",
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
                            recallgraph=False, reinventory=False):
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
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_grime_float_bits_ingress(
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
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked_partial(module, candidate, upto)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, re.escape(expected)):
            module.authenticate_grime_float_bits_ingress(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                return None
            except ValueError as error:
                return str(error)

    # --- coarse gate -------------------------------------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            SITE_COUNT, len(scratch.authenticate_grime_float_bits_ingress(
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
            host = _fn(candidate, "clamp01").body[0].expressions[0]
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
            function = _fn(candidate, "clamp01")
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
                    _fn(candidate, "clamp01").body[0].expressions[0]))
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
            host = _fn(candidate, "clamp01").body[0].expressions[0]
            planted = dataclasses.replace(
                _fn(candidate, "main").body[7].expressions[0].children[0])
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
            host = _fn(candidate, "clamp01").body[0].expressions[0]
            object.__setattr__(host, "children",
                               (*host.children,
                                dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived,
                          "an added expression node is caught by the census alone")

    # --- the sites themselves ----------------------------------------------

    def test_owner_identity_lock(self):
        def mutate(candidate):
            hash21 = _fn(candidate, "hash21")
            object.__setattr__(
                hash21, "body",
                (*hash21.body, dataclasses.replace(hash21.body[0])))
        survived = self._delete_and_compare(
            mutate, "_owner_identity_holds", "ingress owner identity mismatch",
            recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("float-bit ingress census mismatch", survived)

    def test_ingress_census_lock(self):
        def mutate(candidate):
            construct = _construct(candidate, "hash21")
            object.__setattr__(
                construct, "children",
                (*construct.children,
                 dataclasses.replace(construct.children[0])))
        survived = self._delete_and_compare(
            mutate, "_ingress_census_holds",
            "float-bit ingress census mismatch", recount=True)
        # with the census deleted, the site-identity lock still catches the
        # sixth site (its record tuple no longer matches the frozen five)
        self.assertIsNotNone(survived)
        self.assertIn("ingress site identity mismatch", survived)

    def test_site_identity_lock(self):
        def mutate(candidate):
            node = _float_bits_nodes(candidate)[0]
            object.__setattr__(node, "type", named_type("int", {}))
        survived = self._delete_and_compare(
            mutate, "_site_identity_holds", "ingress site identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("ingress construct parent mismatch", survived)

    def test_parent_identity_lock(self):
        def mutate(candidate):
            literal = _construct(candidate, "hash21").children[2]
            object.__setattr__(literal, "literal", "1u")
        survived = self._delete_and_compare(
            mutate, "_parent_identity_holds",
            "ingress construct parent mismatch")
        self.assertIsNone(
            survived,
            "with the parent lock deleted nothing else names the 0u lane")

    def test_statement_ancestry_lock(self):
        def mutate(candidate):
            hash21 = _fn(candidate, "hash21")
            object.__setattr__(hash21, "body",
                               (hash21.body[1], hash21.body[0]))
        survived = self._delete_and_compare(
            mutate, "_statement_ancestry_holds",
            "ingress statement ancestry mismatch")
        self.assertIsNone(
            survived, "with the ancestry lock deleted the swap is unguarded")

    def test_js_evidence_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["js_evidence"] = (*locks[KEY]["js_evidence"][:-1],
                                     "planted")
        _expect(self, module, candidate, locks,
                "ingress JS evidence mismatch")
        scratch = _scratch(module, "_js_evidence_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertEqual(
                SITE_COUNT,
                len(scratch.authenticate_grime_float_bits_ingress(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)))


if __name__ == "__main__":
    unittest.main()
