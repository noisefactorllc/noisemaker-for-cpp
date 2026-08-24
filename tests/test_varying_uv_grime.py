"""Focused RED/GREEN proof for ``grime``'s per-key uv-alias varying record.

Written before ``filter/grime:grime`` existed in
``tools/glslcpp/frontend/varying_uv_profile.py``; the first run of this file
reported ``filter/grime:grime is not an admitted varying-uv carrier`` (and,
before the module carried any grime lock, the boundary below) for every test
in it.

``filter/grime:grime`` declares exactly one varying, ``in vec2 v_texCoord;``
at raw ``grime.glsl:19:1``, reads it exactly twice in ``main`` (normalized
``131:24-131:34`` -- ``vec2 globalCoord = v_texCoord * tileSize +
tileOffset;`` -- and ``134:41-134:51`` -- ``texture(inputTex, v_texCoord)``)
and never writes it. The JavaScript authority is the same three-slot map the
wobble record froze: ``canonicalFactory66`` (``canonical-kernels.js:13836``,
registered for ``filter/grime:grime`` at ``:36246``) carries the slot line
``var v_texCoord = new Float32Array([0, 0]);`` and the closure copy
``v_texCoord.set($runtime.varyings["v_texCoord"])`` after ``beginPixel``
(``:13983-13984``); its ``Function.prototype.toString`` SHA-256 is
``c5100a562df7d991381ed1be6e1bb9fd1f8b117f212b267ee23719734d80123f``
(8,413 bytes, byte-equal to the generated-file slice), cross-validated
against the wobble oracle's frozen cellRefract factory digest
``329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3`` on the
same snapshot and node.

Why grime's record may be frozen now (design 5.2, restated): the rule is
that a record must not be frozen before its program's whole closure behind
the varying is *identified and admitted-by-carrier* -- otherwise the frozen
"CLEAN behind the varying" census would be a lie. grime's whole closure is
exactly two mechanisms, both carried: the varying (this module) and the five
``floatBitsToUint`` sites (``grime_float_bits_ingress_profile.py``, the
fifth identity-admission carrier after caustic/scanlineError/shapes/
shapeMixer). Design 3 measured the ladder: with the varying admitted, the
next blocker is ``38:25 unsupported builtin floatBitsToUint`` and with those
five sites admitted the validator is CLEAN. The record is therefore PREPARED
-- frozen and authenticatable, its row landing in a later slice together
with the ingress carrier's field.
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
MODULE = "tools.glslcpp.frontend.varying_uv_profile"

WOBBLE_KEY = "filter/wobble:wobble"
KEY = "filter/grime:grime"
PROFILE = "varying-uv-admission-v1"
SOURCE_PATH = "filter/grime/grime.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "15a88fff0e951bf7fa01f4c982532cf79d835663cb2a81c2076c5fecbd9c351f"
NORMALIZED_SHA256 = (
    "692547b5193d0c03b3cb5fe86c570fff5ea74149affa6a5c88dac8c5b83eeba1")

VARYING_ID = 55
MAIN_ID = 47
READ_COUNT = 2
LEDGER = 3

# The real whole-file span of grime's varying Symbol (design 1.7: lock the
# whole-file span as it is; grime's normalized source is 169 lines).
SYMBOL_SPAN = "1:1-169:2"
RAW_DECLARATION = "in vec2 v_texCoord;"
RAW_DECLARATION_SITE = "grime.glsl:19:1"

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
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen."""
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


class GrimeVaryingRecordTests(unittest.TestCase):
    def test_the_module_carries_grime_as_its_second_landed_key(self):
        """grime made the one-line move out of PREPARED when its row landed
        as typed row 191, together with its ingress carrier's field -- the
        same move wobble made at row 189. The prepared set is now empty."""
        module = _module()
        self.assertEqual((WOBBLE_KEY, KEY), module.KEYS)
        self.assertEqual({WOBBLE_KEY: PROFILE, KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({WOBBLE_KEY, KEY}), module.VARYING_UV_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual({}, module.PREPARED_PROFILES)
        self.assertEqual(
            (WOBBLE_KEY, KEY), tuple([*module.KEYS, *module.PREPARED_KEYS]))
        self.assertIn(KEY, module._LOCKS)
        self.assertEqual(PROFILE, module._LOCKS[KEY]["profile"])
        self.assertIn(KEY, module.ALLOWED_ROW_FIELDS)
        self.assertNotIn(KEY, module.PREPARED_ROW_FIELDS)

    def test_the_landed_row_contract_names_both_carriers(self):
        """grime's landed row carries the universal two fields plus BOTH
        profile fields: the varying carrier and the float-bit ingress carrier
        (design 3: grime's whole closure is those two mechanisms). The set is
        an exact allowlist -- every other profile field is absent by
        construction."""
        module = _module()
        self.assertEqual(
            frozenset({"defines", "program_key", "varying_profile",
                       "grime_float_bits_ingress_profile"}),
            module.ALLOWED_ROW_FIELDS[KEY])
        self.assertEqual(frozenset(module.ALLOWED_ROW_FIELDS[KEY]),
                         module.allowed_row_fields(KEY))
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)

    def test_the_live_slice_carries_the_grime_row_with_both_carriers(self):
        """The RED state this record lifted: grime is now a typed row and
        carries BOTH its carriers. wobble and grime are the only two rows
        with `varying_profile`, and grime's row is exactly its allowlist."""
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        self.assertEqual(
            sorted([WOBBLE_KEY, KEY]),
            [row["program_key"] for row in spec["programs"]
             if "varying_profile" in row])
        row = next(row for row in spec["programs"]
                   if row["program_key"] == KEY)
        self.assertEqual(module.allowed_row_fields(KEY), frozenset(row))
        self.assertEqual(PROFILE, row["varying_profile"])

    def test_the_live_first_blockers_are_the_designs_table(self):
        """Design 2, grime row: the validator first-blocks on the varying
        (``1:1`` -- the whole-file Symbol span, design 1.7) and the emitter
        on ``floatBitsToUint`` at ``38:25`` (its function bodies sort ahead
        of ``main``). Both reproduced read-only against the live tree; the
        declared capabilities come from the module's frozen tuple, not
        ``load_slice`` -- the live slice is integration-lane territory and
        mid-flight under other lanes."""
        program = _analyzed()
        with self.assertRaises(Exception) as raised:
            generate_typed_slice.validate_capabilities(
                program,
                generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        # Both authorities now first-block on the CARRIER being absent
        # rather than on the construct itself: grime is a landed key, so an
        # uncarried render fails closed at the required-carrier arm before it
        # walks to the varying or the `floatBitsToUint` site. That IS the
        # design's table one rung further along -- the blockers it named are
        # what the carriers were built to lift, and they are lifted.
        self.assertIn("exact grime float-bit ingress profile carrier required",
                      str(raised.exception))
        # The emitter now first-blocks on the CARRIER being absent rather
        # than on the builtin: grime is a landed key, so an uncarried render
        # fails closed at the required-carrier arm before it ever walks to
        # the `floatBitsToUint` site. Supplying both carriers is the landed
        # path and is covered by the integration lane.
        with self.assertRaises(Exception) as raised:
            emit_typed_cpp.render_typed_cpp(program, KEY, RAW_SHA256)
        self.assertIn("exact grime float-bit ingress profile carrier required",
                      str(raised.exception))

    def test_the_frozen_source_path_names_the_authenticated_file(self):
        module = _module()
        self.assertEqual(SOURCE_PATH, module._LOCKS[KEY]["source_path"])
        raw = (CORPUS / module._LOCKS[KEY]["source_path"]).read_bytes()
        self.assertEqual(5776, module._LOCKS[KEY]["raw_bytes"])
        self.assertEqual(len(raw), module._LOCKS[KEY]["raw_bytes"])
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(RAW_SHA256, module._LOCKS[KEY]["raw_sha256"])
        self.assertEqual(5279, module._LOCKS[KEY]["normalized_bytes"])
        self.assertEqual(NORMALIZED_SHA256,
                         module._LOCKS[KEY]["normalized_sha256"])
        self.assertEqual((), module._LOCKS[KEY]["defines"])

    def test_every_failure_names_the_per_key_profile(self):
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


class GrimeVaryingAdmissionTests(unittest.TestCase):
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
        """The foreign-carrier sweep (design 6.3) for grime's key: every
        sibling profile string -- including grime's own ingress carrier and
        the other three float-bit precedents -- is rejected as the varying
        carrier; only the exact string admits."""
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong",
                        "mutable-global-frame-shape-v1",
                        "const-global-nine-table-v1",
                        "scalar-uint-xor-v1",
                        "mutable-global-nine-array-cellrefract-v1",
                        "scanline-error-float-bits-ingress-v1",
                        "shapes-float-bits-ingress-v1",
                        "caustic-float-bits-scalar-word-hash-v1",
                        "grime-float-bits-ingress-v1",
                        "varying-uv-admission-v2"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_varying_uv(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_grime_answers_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_varying_uv(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "grime-float-bits-ingress-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted varying-uv carrier"):
                module.authenticate_varying_uv(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_varying_uv(
                _analyzed(), "0" * 64, PROFILE)

    def test_define_drift_fails_the_defines_lock(self):
        def mutate(candidate):
            from tools.glslcpp.frontend.typed_ir import PreprocessorDefine
            object.__setattr__(
                candidate, "preprocessor_defines",
                (PreprocessorDefine("MODE", "int", "4"),))
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "exact preprocessor define lock mismatch")

    def test_raw_source_drift_fails_the_raw_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "raw_source",
                           candidate.raw_source + "// planted")
        locks = _relocked_partial(module, candidate, upto="raw")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, re.escape("raw source drift")):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "source", candidate.source + "\n")
        locks = _relocked_partial(module, candidate, upto="normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(
                    ValueError, re.escape("normalized source drift")):
            module.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)


class GrimeVaryingIdentityTests(unittest.TestCase):
    def _varying(self, candidate):
        return candidate.interface_symbols[0]

    def _read_nodes(self, candidate):
        return [item for item in _nodes(candidate)
                if item.kind == "id" and item.symbol_id == VARYING_ID]

    def test_renamed_to_vcolor_fails_the_alias_map_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._varying(candidate), "name", "vColor")
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying name is not in the runtime uv alias map")
        scratch = _scratch(module, "_uv_alias_name_holds")
        with mock.patch.object(scratch, "_LOCKS", locks), \
                self.assertRaisesRegex(
                    ValueError, "varying symbol identity mismatch"):
            scratch.authenticate_varying_uv(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_retyped_to_vec3_fails_the_type_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._varying(candidate), "type",
                           named_type("vec3", {}))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks, "varying type mismatch")

    def test_made_writable_fails_the_storage_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._varying(candidate), "writable", True)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying storage mutability or direction mismatch")

    def test_a_retyped_span_fails_the_whole_file_span_lock(self):
        """The whole-file span is ``1:1-169:2`` (grime's normalized source is
        169 lines); the raw declaration at line 19 must NOT be substituted."""
        module = _module()
        candidate = _analyzed()
        symbol = self._varying(candidate)
        object.__setattr__(
            symbol, "span",
            dataclasses.replace(symbol.span, start_line=19))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying symbol span is not the whole-file span")

    def test_a_moved_raw_declaration_line_fails_the_raw_site_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "raw_source",
                           candidate.raw_source.replace(
                               "in vec2 v_texCoord;",
                               "in  vec2 v_texCoord;"))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying raw-source declaration site mismatch")

    def test_symbol_id_drift_fails_the_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(self._varying(candidate), "id", 9001)
        locks = _relocked(module, candidate)
        survived = None
        message = _expect(self, module, candidate, locks,
                          "varying symbol identity mismatch")
        scratch = _scratch(module, "_varying_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_varying_uv(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
            except ValueError as error:
                survived = str(error)
        self.assertIsNotNone(survived)
        self.assertIn("varying read census mismatch", survived)

    def test_a_second_varying_fails_the_interface_cardinality_lock(self):
        module = _module()
        candidate = _analyzed()
        planted = dataclasses.replace(self._varying(candidate), id=9001,
                                      name="vUv")
        object.__setattr__(
            candidate, "interface_symbols",
            (*candidate.interface_symbols, planted))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying interface census mismatch")

    def test_a_third_read_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        statement = _main(candidate).body[6]
        object.__setattr__(
            statement.expressions[0], "children",
            (*statement.expressions[0].children,
             _id_clone(candidate, VARYING_ID)))
        locks = _relocked(module, candidate, **_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "varying read census mismatch")

    def test_a_missing_read_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        read = self._read_nodes(candidate)[1]
        object.__setattr__(read, "symbol_id", 4)  # tileOffset's uniform id
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying read census mismatch")

    def test_a_shifted_read_span_fails_the_read_census(self):
        module = _module()
        candidate = _analyzed()
        read = self._read_nodes(candidate)[0]
        object.__setattr__(
            read, "span", dataclasses.replace(read.span, start_column=25))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying read census mismatch")

    def test_the_read_moved_to_another_function_fails_the_owner(self):
        module = _module()
        candidate = _analyzed()
        statement = _main(candidate).body[1]
        object.__setattr__(
            _main(candidate), "body",
            tuple(item for item in _main(candidate).body if item is not statement))
        hash21 = _fn(candidate, "hash21")
        object.__setattr__(hash21, "body", (*hash21.body, statement))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying read census mismatch")

    def test_the_read_made_into_a_write_fails_the_write_census(self):
        module = _module()
        candidate = _analyzed()
        assign = _main(candidate).body[24].expressions[0]
        self.assertEqual("assign", assign.kind)
        object.__setattr__(
            assign, "children",
            (_id_clone(candidate, VARYING_ID), assign.children[1]))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "varying write census mismatch")

    def test_a_broken_contract_fails_the_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        # `alias_of` is owned by the contract lock alone (mutating the
        # raw_declaration_site field would trip the raw-site lock first,
        # which also consults the contract's site string).
        locks[KEY]["contract"] = locks[KEY]["contract"]._replace(
            alias_of="context.frag_coord")
        _expect(self, module, candidate, locks,
                "varying emission contract mismatch")


class GrimeVaryingCensusTests(unittest.TestCase):
    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        candidate = _analyzed()
        lock = module._LOCKS[KEY]
        self.assertEqual((645, 15), module._node_census(candidate))
        self.assertEqual(645, lock["total_nodes"])
        self.assertEqual(15, lock["total_assigns"])
        self.assertEqual(14, lock["function_count"])
        self.assertEqual(7, lock["declaration_count"])
        self.assertEqual((), lock["initializer_census"])
        self.assertEqual(1, lock["interface_cardinality"])
        self.assertEqual(22, lock["call_edge_count"])

    def test_the_call_graph_and_reachability_are_the_real_edges(self):
        module = _module()
        candidate = _analyzed()
        lock = module._LOCKS[KEY]
        edges = module._call_graph(candidate)
        reachable, unreachable = module._reachability(candidate)
        self.assertEqual(len(edges), lock["call_edge_count"])
        self.assertEqual(module._sha(edges), lock["call_graph_sha256"])
        self.assertEqual(reachable, lock["reachable"])
        self.assertEqual(unreachable, lock["unreachable"])
        self.assertEqual((40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
                          52, 53), lock["reachable"])
        self.assertEqual((), lock["unreachable"])

    def test_the_declaration_inventory_is_the_seven_real_rows(self):
        module = _module()
        candidate = _analyzed()
        lock = module._LOCKS[KEY]
        self.assertEqual(module._declaration_inventory(candidate),
                         lock["declaration_inventory"])
        self.assertEqual(7, len(lock["declaration_inventory"]))
        # resolution is declared-but-unread (design 1.1): it stays a required
        # ABI binding per the Shapes precedent -- nothing here drops it.
        self.assertIn("resolution",
                      candidate.resources.uniforms)

    def test_the_read_census_is_two_reads_in_main_at_the_exact_sites(self):
        module = _module()
        candidate = _analyzed()
        reads, writes = module._reference_census(
            candidate, {VARYING_ID: "v_texCoord"})
        self.assertEqual(2, len(reads))
        self.assertEqual([], writes)
        lock = module._LOCKS[KEY]
        self.assertEqual(
            (("131:24-131:34", "binary", "*", MAIN_ID),
             ("134:41-134:51", "builtin", None, MAIN_ID)),
            tuple((item.record.span, item.record.parent_kind,
                   item.record.parent_operator, item.record.owner_id)
                  for item in reads))
        self.assertEqual(tuple(item.record for item in reads), lock["reads"])

    def test_the_symbol_span_is_the_whole_file_and_the_raw_site_line_19(self):
        module = _module()
        candidate = _analyzed()
        symbol = candidate.interface_symbols[0]
        self.assertEqual((VARYING_ID, "v_texCoord", "vec2", "varying", False),
                         (symbol.id, symbol.name, symbol.type.display(),
                          symbol.storage, symbol.writable))
        self.assertEqual(SYMBOL_SPAN, module._span(symbol))
        self.assertEqual(SYMBOL_SPAN, module._LOCKS[KEY]["symbol_span"])
        self.assertEqual(
            ("filter/grime/grime.glsl", "in vec2 v_texCoord;", 19),
            module._LOCKS[KEY]["raw_declaration"])
        raw = candidate.raw_source.split("\n")
        self.assertEqual("in vec2 v_texCoord;", raw[18].strip())
        self.assertEqual(
            "filter/grime/grime.glsl:19:1",
            module._LOCKS[KEY]["contract"].raw_declaration_site)

    def test_the_varying_is_not_in_the_declaration_inventory(self):
        module = _module()
        candidate = _analyzed()
        self.assertTrue(all(
            item.symbol.id != VARYING_ID
            for item in candidate.declarations))

    def test_the_whole_corpus_still_carries_exactly_five_varying_programs(self):
        """Design 1.6 re-derived: the regex sweep over all corpus sources
        finds exactly the five programs, grime among them, one varying each."""
        pattern = re.compile(
            r"^[ \t]*(?:flat[ \t]+)?in[ \t]+(vec2|vec3|vec4)[ \t]+(\w+)[ \t]*;"
            r"[ \t]*$", re.MULTILINE)
        found: dict[str, list[tuple[str, str]]] = {}
        for path in sorted(CORPUS.rglob("*.glsl")) + sorted(CORPUS.rglob("*.frag")):
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                relative = path.relative_to(CORPUS).with_suffix("")
                parts = relative.parts
                key = "/".join(parts[:-1]) + ":" + parts[-1]
                found.setdefault(key, []).append(
                    (match.group(1), match.group(2)))
        self.assertEqual(
            {"filter/grime:grime", "filter/texture:texture",
             "filter/wobble:wobble", "filter/spookyTicker:spookyTicker",
             "filter/wormhole:deposit"},
            set(found))
        self.assertEqual([("vec2", "v_texCoord")], found[KEY])


class GrimeVaryingLedgerTests(unittest.TestCase):
    def test_the_ledger_counts_the_symbol_and_both_read_nodes(self):
        module = _module()
        self.assertEqual(1 + READ_COUNT,
                         module._LOCKS[KEY]["consumed_ledger"])
        self.assertEqual(LEDGER, module._LOCKS[KEY]["consumed_ledger"])

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            locks = copy.deepcopy(module._LOCKS)
            locks[KEY]["consumed_ledger"] = sabotage
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_LOCKS", locks), \
                    self.assertRaisesRegex(
                        ValueError,
                        "varying-uv visitation ledger mismatch"):
                module.authenticate_varying_uv(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(
            1, len(module.authenticate_varying_uv(
                _analyzed(), RAW_SHA256, PROFILE)))


class GrimeVaryingLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing for grime's key by DELETING THE
    LOCK: mutate the tree, refreeze only the coarse hashes (and the counters
    the mutation unavoidably moves), show the real module rejects with that
    lock's own message, then re-exec the module with exactly that predicate
    neutralized and show the message is gone."""

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
        for name in self._PREDICATES:
            with self.subTest(predicate=name):
                self.assertTrue(callable(getattr(module, name, None)),
                                f"{name} is not a module predicate")
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
                _main(candidate).body[7].expressions[0].children[0])
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
        self.assertIsNone(survived,
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
                dataclasses.replace(symbol.span, start_line=19))
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
            node = next(item for item in _nodes(candidate)
                        if item.kind == "id" and item.symbol_id == VARYING_ID)
            object.__setattr__(
                node, "span", dataclasses.replace(node.span, start_column=25))
        survived = self._delete_and_compare(
            mutate, "_read_census_holds", "varying read census mismatch")
        self.assertIsNone(survived)

    def test_write_census_lock(self):
        def mutate(candidate):
            assign = _main(candidate).body[24].expressions[0]
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


if __name__ == "__main__":
    unittest.main()
