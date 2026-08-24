"""Focused RED/GREEN proof for the five `cellRefract` mutable global arrays.

Written before ``tools/glslcpp/frontend/mutable_global_array_profile.py``
existed; the first run of this file reported ``ModuleNotFoundError`` from
``_module`` for every test in it.

``classicNoisedeck/cellRefract:cellRefract`` declares five mutable,
uninitialised, file-scope arrays one line apart, at frozen defines
``KERNEL=0``/``SHAPE=1``::

    32|float emboss[9];
    33|float sharpen[9];
    34|float blur[9];
    35|float edge[9];
    36|float edge2[9];

and a non-``main`` writer, ``loadKernels``, whose 45 literal element stores
are the program's kernel tables. The validator reports only the first line.
All five must be admitted.

Testing rules inherited from the Shapes slice apply directly:

1. ``Symbol`` embeds its declaration span, so a value-level mutation shifts
   every enclosing node hash. The production module evaluates storage,
   mutability, initialiser-absence and the element contracts **ahead** of node
   identity, and each lock is proved load-bearing by *deleting the lock* in a
   scratch copy -- never by mutating the input and watching something raise.
2. Every mutation test refreezes **only** the coarse hash fields (plus the
   specific census counters the mutation unavoidably moves) and asserts that
   no coarse message fired. Semantic fields keep their frozen originals.
3. The census walks global declaration initializers as well as function
   bodies, and the frozen initializer census is empty -- the walk is what
   proves no read can hide in a global initializer here.

Two facts specific to this mechanism shape the writer locks:

* 19 of the 45 store values are ``unary(-)`` nodes wrapping a float literal
  (design Amendment 14), so "all values literal" is asserted as
  literal-or-unary-minus-of-literal exactly as ``_number()`` extracts it.
* At the frozen defines the five globals are **write-only**: their only
  readers were stripped by normalization. The write-only census (45 ``id``
  references, every one a store base, zero reads, zero whole-array bases) is
  frozen as-is and must not grow a "reads allowed" switch.
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
from tools.glslcpp.frontend.typed_ir import TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.mutable_global_array_profile"

KEY = "classicNoisedeck/cellRefract:cellRefract"
PROFILE = "mutable-global-nine-array-cellrefract-v1"
SOURCE_PATH = "classicNoisedeck/cellRefract/cellRefract.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70"
NORMALIZED_SHA256 = (
    "31cce61e01275d44d46556bfc13edeea4383dcfbcfde024fd7c54a624933bd3c")

EMBOSS_ID = 17
SHARPEN_ID = 18
BLUR_ID = 19
EDGE_ID = 20
EDGE2_ID = 21
EMBOSS_ORDINAL = 16
WRITER_ID = 70
MAIN_ID = 71
FRAGCOLOR_ORDINAL = 15
WRITER_CALL_INDEX = 3
STORE_COUNT = 45
LEDGER = 193

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
    "float table[9];\n"
    "void loadKernels() { table[0] = 1.0; }\n"
    "void main() {\n"
    "    loadKernels();\n"
    "    fragColor = vec4(table[1], table[2], table[3], 1.0);\n"
    "}\n"
)

ARRAY_NAMES = ("emboss", "sharpen", "blur", "edge", "edge2")


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("mutable-global array profile module is absent")
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


KALEIDO_KEY = "classicNoisedeck/kaleido:kaleido"
KALEIDO_PROFILE = "mutable-global-nine-array-kaleido-v1"
EFFECTS_KEY = "classicNoisedeck/effects:effects"
EFFECTS_PROFILE = "mutable-global-nine-array-effects-v1"
KALEIDO_SOURCE_PATH = "classicNoisedeck/kaleido/kaleido.glsl"
KALEIDO_SOURCE = CORPUS / KALEIDO_SOURCE_PATH
KALEIDO_RAW_SHA256 = (
    "3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9")
KALEIDO_NORMALIZED_SHA256 = (
    "d31299ee69dd0c41965209860ef60a4ad2abf762229cc340383dce2646c6cc1d")

# kaleido: five float[9] globals at declaration indices 12-16 (symbols 13-17),
# immediately after the `fragColor` output at index 11.
KALEIDO_EMBOSS_ID = 13
KALEIDO_BLUR_ID = 15
KALEIDO_FIRST_ORDINAL = 12
KALEIDO_WRITER_ID = 126
KALEIDO_MAIN_ID = 127
KALEIDO_FRAGCOLOR_ORDINAL = 11
KALEIDO_WRITER_CALL_INDEX = 3
KALEIDO_STORE_COUNT = 45


def _analyzed_k(raw: str | None = None,
                defines: dict | None = None):
    raw = (KALEIDO_SOURCE.read_text(encoding="utf-8")
           if raw is None else raw)
    defines = (generate_typed_slice._defaults(ROOT, KALEIDO_KEY)
               if defines is None else defines)
    return analyze_program(parse_program(raw, KALEIDO_KEY, defines),
                           KALEIDO_KEY)


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
    inventory, the ordinals, the element contracts, the store census and every
    node hash keep their frozen originals. Refreezing those would hand the
    mutation to the very lock under test and make the experiment vacuous.
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


def _rewriterbody(module, candidate, key=KEY):
    writer = _fn(candidate, "loadKernels")
    return {"writer_body": tuple((item.kind, module._span(item))
                                 for item in writer.body)}


def _remainbody(module, candidate, key=KEY):
    main = _main(candidate)
    return {"main_body": tuple((item.kind, module._span(item))
                               for item in main.body)}


def _recallwriter(module, candidate, main=None, key=KEY):
    """Refreeze the writer-call site record and the state-consumer indices."""
    main = _main(candidate) if main is None else main
    lock = module._LOCKS[key]
    sites = module._writer_call_sites(main, lock)
    index, _, node, _, _ = sites[0]
    consumers = []
    ids = lock["state_consumer_ids"]
    for position, statement in enumerate(main.body):
        callees = tuple(sorted({
            item.callee
            for item, _, _, _, _ in module._walk_statement(statement, (position,))
            if item.kind == "call" and (item.callee, item.signature_id) in ids}))
        if callees:
            consumers.append((position, callees))
    return {"writer_call": dict(lock["writer_call"], statement_index=index,
                                span=module._span(node),
                                sha256=module._sha(node)),
            "state_consumers": tuple(consumers)}


def _authenticate(module, candidate, locks, profile=PROFILE, key=KEY):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_mutable_global_array(
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


class MutableGlobalArrayPublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        # Three carriers since the effects integration (row 188 -- the
        # family's first seven-array / three-carrier member).
        self.assertEqual((KEY, KALEIDO_KEY, EFFECTS_KEY), module.KEYS)
        self.assertEqual({KEY: PROFILE, KALEIDO_KEY: KALEIDO_PROFILE,
                          EFFECTS_KEY: EFFECTS_PROFILE},
                         module.PROFILES)
        self.assertEqual(frozenset({KEY, KALEIDO_KEY, EFFECTS_KEY}),
                         module.MUTABLE_GLOBAL_ARRAY_KEYS)
        self.assertIsInstance(module.MUTABLE_GLOBAL_ARRAY_KEYS, frozenset)
        self.assertEqual(KEY, module.CELLREFRACT_KEY)
        self.assertEqual(PROFILE, module.CELLREFRACT_PROFILE)
        for name in ("KEYS", "PROFILES", "MUTABLE_GLOBAL_ARRAY_KEYS",
                     "CELLREFRACT_KEY", "CELLREFRACT_PROFILE",
                     "ALLOWED_ROW_FIELDS", "allowed_row_fields",
                     "ArrayFrameField", "ArrayFrameContract", "frame_contract",
                     "authenticate_mutable_global_array",
                     "apply_mutable_global_array"):
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
        """An allowlist, not a denylist: equality with this set discharges
        "every other profile absent" by construction. The fixed-array
        parameter proof is a TypedProgram field auto-attached before
        validation, not a slice-row field, so it does not appear here.
        kaleido's entry is the one two-profile row: its XOR companion is
        required, not forbidden. effects' entry is the first THREE-profile
        row: its mat4 and ceil companions are required, not forbidden."""
        module = _module()
        self.assertEqual({"defines", "program_key",
                          "mutable_global_array_profile"},
                         set(module.allowed_row_fields(KEY)))
        self.assertEqual(
            {KEY: module.allowed_row_fields(KEY),
             KALEIDO_KEY: module.allowed_row_fields(KALEIDO_KEY),
             EFFECTS_KEY: module.allowed_row_fields(EFFECTS_KEY)},
            module.ALLOWED_ROW_FIELDS)
        self.assertIsInstance(module.ALLOWED_ROW_FIELDS[KEY], frozenset)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("synth/shape:shape")

    def test_the_allowlist_excludes_every_other_live_row_profile_field(self):
        """No other row in the live slice may carry any field this row allows
        beyond the universal two, and no row at all may carry the new field.
        The carrier rows are excluded from the universe so the test is
        durable across rows landing: kaleido (the mechanism's second
        carrier, and the one legitimate two-profile row) and effects (the
        third, the first three-profile row) are excluded the same way, and
        the positive carrier census below names ALL THREE keys."""
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        universe = {field for row in spec["programs"] for field in row
                    if field.endswith("_profile")
                    and row["program_key"]
                    not in (KEY, KALEIDO_KEY, EFFECTS_KEY)}
        self.assertGreaterEqual(len(universe), 20, "universe looks truncated")
        allowed = module.allowed_row_fields(KEY)
        self.assertEqual({"defines", "program_key"},
                         allowed - universe - {"mutable_global_array_profile"})
        self.assertEqual(set(), universe & allowed,
                         "the row carries no companion profile")
        self.assertNotIn("mutable_global_array_profile", universe,
                         "no other row may carry the array carrier")
        self.assertEqual(
            [KEY, EFFECTS_KEY, KALEIDO_KEY],
            [row["program_key"] for row in spec["programs"]
             if "mutable_global_array_profile" in row])

    def test_the_optional_proof_allowlist_is_exactly_the_sibling_fields(self):
        """Design Amendment 13.2: the program WILL carry
        ``fixed_array_in_parameter_proof`` (auto-attached at
        ``generate_typed_slice.py:5018`` before validation), so that field is
        deliberately allowed; every OTHER optional proof field a TypedProgram
        can carry must be frozen absent. Enumerated from the dataclass, not
        hand-listed, so a new proof field turns this red."""
        module = _module()
        carried = {
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_") and field.name.endswith("_proof")
            and field.name != "fixed_array_in_parameter_proof"}
        self.assertEqual(
            ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
             "fixed_affine_centers13_proof"),
            module._OPTIONAL_PROOF_FIELDS)
        self.assertEqual(carried, set(module._OPTIONAL_PROOF_FIELDS))
        self.assertNotIn("fixed_array_in_parameter_proof",
                         module._OPTIONAL_PROOF_FIELDS)
        self.assertIn("fixed_array_in_parameter_proof",
                      {field.name for field in dataclasses.fields(TypedProgram)})

    def test_frame_contract_is_the_pixel_scope_writer_relaxed_shape(self):
        module = _module()
        contract = module.frame_contract(KEY)
        self.assertEqual("Frame", contract.struct_name)
        self.assertEqual("frame", contract.instance_name)
        self.assertEqual("pixel", contract.instance_scope)
        self.assertTrue(contract.value_initialized)
        self.assertEqual("const Frame& frame", contract.helper_parameter)
        self.assertEqual(2, contract.helper_parameter_ordinal)
        self.assertEqual("Frame& frame", contract.writer_parameter)
        self.assertEqual("loadKernels", contract.writer_function)
        self.assertEqual(ARRAY_NAMES,
                         tuple(item.name for item in contract.fields))
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.frame_contract("synth/shape:shape")

    def test_every_failure_names_the_profile_not_a_module_global(self):
        """Amendment 2 hazard fix: messages carry the per-key profile name."""
        module = _module()
        prefix = re.escape(f"{PROFILE}: ")
        program = _analyzed()
        for caller, arguments in (
                ("carrier", (program, RAW_SHA256, "wrong")),
                ("non-carrier", (_foreign(), _hash(FOREIGN_SOURCE), PROFILE)),
                ("row fields", ("synth/shape:shape",)),
                ("frame contract", ("synth/shape:shape",))):
            with self.subTest(site=caller), self.assertRaises(ValueError) as ctx:
                if caller == "carrier":
                    module.authenticate_mutable_global_array(*arguments)
                elif caller == "non-carrier":
                    module.authenticate_mutable_global_array(*arguments)
                elif caller == "row fields":
                    module.allowed_row_fields(*arguments)
                else:
                    module.frame_contract(*arguments)
            self.assertRegex(str(ctx.exception), f"^{prefix}")


class MutableGlobalArrayAdmissionTests(unittest.TestCase):
    def test_authenticates_all_five_declarations_in_declaration_order(self):
        module = _module()
        program = _analyzed()
        admitted = module.authenticate_mutable_global_array(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(admitted, tuple)
        self.assertEqual(5, len(admitted),
                         "the validator reports one site; there are five")
        for ordinal, declaration in zip(range(16, 21), admitted):
            self.assertIs(program.declarations[ordinal], declaration)
        self.assertEqual(list(ARRAY_NAMES),
                         [item.symbol.name for item in admitted])
        self.assertEqual(["float[9]"] * 5,
                         [item.type.display() for item in admitted])
        for item in admitted:
            self.assertEqual("global", item.symbol.storage)
            self.assertTrue(item.symbol.writable)
            self.assertIsNone(item.initializer)
        self.assertIs(program, module.apply_mutable_global_array(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "mutable-global-frame-shape-v1",
                        "const-global-nine-table-v1", "scalar-uint-xor-v1",
                        "mutable-global-nine-array-cellrefract-v2",
                        "mutable-global-nine-array-kaleido-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_mutable_global_array(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_the_five_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_mutable_global_array(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "const-global-nine-table-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted mutable-global array carrier"):
                module.authenticate_mutable_global_array(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_non_carrier_error_names_the_five_sole_admitted_declarations(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_mutable_global_array(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        message = str(raised.exception)
        for name in ARRAY_NAMES:
            self.assertIn(name, message)
        self.assertIn("32:1 float emboss[9]", message)
        self.assertIn("33:1 float sharpen[9]", message)
        self.assertIn("34:1 float blur[9]", message)
        self.assertIn("35:1 float edge[9]", message)
        self.assertIn("36:1 float edge2[9]", message)
        self.assertIn("sole admitted declarations", message)

    def test_the_foreign_fixture_really_carries_the_construct(self):
        """The rejection at the boundary must be about identity, not about the
        construct being absent from the foreign program."""
        foreign = _foreign()
        mutable = [item for item in foreign.declarations
                   if item.symbol.storage == "global"
                   and item.initializer is None]
        self.assertEqual(["table"], [item.symbol.name for item in mutable])
        self.assertEqual("float[9]", mutable[0].type.display())
        self.assertTrue(mutable[0].symbol.writable)

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_array(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_fails_the_caller_hash_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original + "\n// planted\n"
        self.assertNotEqual(original, mutated)
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_array(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        """The caller-hash lock and the raw-source lock are different locks."""
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_mutable_global_array(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("emboss[8] = 2.0;", "emboss[8] = 2.5;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_an_unanalyzed_body_status_fails_the_normalized_lock(self):
        """The `body_status == "analyzed"` sub-clause is its own arm: a
        program whose body was never analyzed must not authenticate even
        with byte-identical sources."""
        module = _module()
        candidate = dataclasses.replace(_analyzed(), body_status="parsed")
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_a_loop_profile_drift_fails_the_call_graph_lock(self):
        """The counted-loop profile is a sub-clause of the call-graph lock and
        can drift independently of every edge: only it can catch a
        `counted_loop_proof` whose numbers lie."""
        module = _module()
        baseline = _analyzed()
        proof = dataclasses.replace(baseline.counted_loop_proof, loop_count=4)
        candidate = dataclasses.replace(baseline, counted_loop_proof=proof)
        _expect(self, module, candidate, _relocked(module, candidate),
                "call graph or reachability profile mismatch")

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
            module.authenticate_mutable_global_array(
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
            module.authenticate_mutable_global_array(
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
            module.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_mutable_global_array(
                        candidate, RAW_SHA256, PROFILE)

    def test_the_fixed_array_sibling_proof_is_allowed(self):
        """Amendment 13.2: ``fixed_array_in_parameter_proof`` is auto-attached
        before validation, so a carrier carrying it must still authenticate."""
        module = _module()
        candidate = dataclasses.replace(
            _analyzed(), fixed_array_in_parameter_proof=object())
        admitted = module.authenticate_mutable_global_array(
            candidate, RAW_SHA256, PROFILE)
        self.assertEqual(5, len(admitted))

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        baseline = _analyzed()
        cases = [
            ("kernel value drift", _analyzed(defines={"KERNEL": 1,
                                                      "SHAPE": 1})),
            ("shape value drift", _analyzed(defines={"KERNEL": 0,
                                                     "SHAPE": 2})),
            ("name drift", _analyzed(defines={"KERNEL_X": 0, "SHAPE": 1})),
            ("extra define", _analyzed(defines={"KERNEL": 0, "SHAPE": 1,
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


class MutableGlobalArrayDeclarationTests(unittest.TestCase):
    """Identity, order, type, mutability, uninitialisedness -- per array."""

    def test_the_five_admitted_records_are_the_real_declarations(self):
        module = _module()
        program = _analyzed()
        records = module._LOCKS[KEY]["admitted"]
        self.assertEqual(5, len(records))
        for record in records:
            declaration = program.declarations[record.ordinal]
            self.assertEqual(record.symbol_id, declaration.symbol.id)
            self.assertEqual(record.name, declaration.symbol.name)
            self.assertEqual(record.glsl_type, declaration.type.display())
            self.assertEqual(record.element_type,
                             declaration.type.element.display())
            self.assertEqual(record.extent, declaration.type.size)
            self.assertEqual("array", declaration.type.kind)
            self.assertEqual(record.storage, declaration.symbol.storage)
            self.assertEqual(record.writable, declaration.symbol.writable)
            self.assertIsNone(declaration.initializer)
            self.assertEqual(record.declaration_span, module._span(declaration))
            self.assertEqual(record.symbol_span,
                             module._span(declaration.symbol))
            self.assertEqual(record.declaration_sha256,
                             module._sha(declaration))
            self.assertEqual(record.symbol_sha256,
                             module._sha(declaration.symbol))
        self.assertEqual(tuple(range(16, 21)),
                         tuple(item.ordinal for item in records))
        self.assertEqual(tuple(range(17, 22)),
                         tuple(item.symbol_id for item in records))
        self.assertEqual(ARRAY_NAMES,
                         tuple(item.name for item in records))

    def test_adjacency_is_immediately_after_the_fragColor_output(self):
        module = _module()
        program = _analyzed()
        preceding = program.declarations[EMBOSS_ORDINAL - 1]
        self.assertEqual("fragColor", preceding.symbol.name)
        self.assertEqual("output", preceding.symbol.storage)
        self.assertEqual("vec4", preceding.type.display())
        self.assertEqual((FRAGCOLOR_ORDINAL, preceding.symbol.id),
                         module._LOCKS[KEY]["preceding"][:2])
        self.assertEqual("fragColor", module._LOCKS[KEY]["preceding_name"])

    def test_the_inventory_covers_all_twenty_one_declarations(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(21, len(program.declarations))
        self.assertEqual(21, module._LOCKS[KEY]["declaration_count"])
        self.assertEqual(21, len(module._LOCKS[KEY]["declaration_inventory"]))
        self.assertEqual(module._LOCKS[KEY]["declaration_inventory"],
                         module._declaration_inventory(program))
        mutable = [item.symbol.name for item in program.declarations
                   if item.symbol.storage == "global"]
        self.assertEqual(list(ARRAY_NAMES), mutable)
        writable = [item.symbol.name for item in program.declarations
                    if item.symbol.writable]
        self.assertEqual(["fragColor", *ARRAY_NAMES], writable)

    def test_uninitialisedness_is_the_defining_property_of_the_sub_shape(self):
        module = _module()
        program = _analyzed()
        without = [item.symbol.name for item in program.declarations
                   if item.initializer is None]
        for name in ARRAY_NAMES:
            self.assertIn(name, without)
        self.assertEqual(
            [], [item.symbol.name for item in program.declarations
                 if item.initializer is not None],
            "the program has no initializers at all; the census walks them")

    def test_reordering_two_arrays_fails_the_ordinal_lock(self):
        module = _module()
        candidate = _analyzed()
        declarations = list(candidate.declarations)
        declarations[16], declarations[17] = (declarations[17],
                                             declarations[16])
        object.__setattr__(candidate, "declarations", tuple(declarations))
        _expect(self, module, candidate, _relocked(module, candidate),
                "admitted array declaration ordinal or adjacency mismatch")

    def test_a_relocation_that_leaves_fragColor_behind_fails_adjacency(self):
        module = _module()
        candidate = _analyzed()
        declarations = list(candidate.declarations)
        declarations[FRAGCOLOR_ORDINAL], declarations[19] = (
            declarations[19], declarations[FRAGCOLOR_ORDINAL])
        object.__setattr__(candidate, "declarations", tuple(declarations))
        _expect(self, module, candidate, _relocked(module, candidate),
                "admitted array declaration ordinal or adjacency mismatch")

    def test_a_preceding_neighbour_swap_fails_only_the_adjacency_lock(self):
        """Swapping `fragColor` with a uniform leaves the five admitted
        ordinals untouched (so the ordinals sub-clause passes) and leaves the
        sorted inventory untouched (so the inventory lock passes); only the
        frozen preceding-declaration check can see it."""
        module = _module()
        candidate = _analyzed()
        declarations = list(candidate.declarations)
        declarations[0], declarations[FRAGCOLOR_ORDINAL] = (
            declarations[FRAGCOLOR_ORDINAL], declarations[0])
        object.__setattr__(candidate, "declarations", tuple(declarations))
        message = _expect(
            self, module, candidate, _relocked(module, candidate),
            "admitted array declaration ordinal or adjacency mismatch")
        self.assertNotIn("global declaration inventory mismatch", message)


class MutableGlobalArrayNumericContractTests(unittest.TestCase):
    """All five arrays share one element contract -- a plain JS double."""

    def test_every_field_is_an_unnarrowed_double_backed_by_kernel9(self):
        module = _module()
        fields = module.frame_contract(KEY).fields
        self.assertEqual(5, len(fields))
        for field in fields:
            with self.subTest(name=field.name):
                self.assertEqual("float[9]", field.glsl_type)
                self.assertEqual("Kernel9", field.native_type)
                self.assertEqual("float", field.element_type)
                self.assertEqual(9, field.extent)
                self.assertEqual("none", field.narrowing)
                self.assertEqual("0", field.js_initializer)
                self.assertEqual("double", field.js_number_kind)

    def test_the_native_alias_agrees_with_the_fixed_array_parameter_proof(self):
        """``Kernel9`` is the alias the refract-shape emitter already emits for
        ``std::array<double, 9>``; the profile asserts the mapping rather than
        inheriting it, so a future rename turns this red."""
        module = _module()
        fixed = importlib.import_module(
            "tools.glslcpp.frontend.fixed_array_in_parameter_proof")
        self.assertEqual("Kernel9", module._ARRAY_NATIVE_TYPE)
        source = pathlib.Path(fixed.__file__).read_text(encoding="utf-8")
        self.assertIn('native_alias="Kernel9"', source)

    def test_a_narrowed_contract_fails_the_element_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        broken = locks[KEY]["admitted"][0].field._replace(
            narrowing="per-lane-f32")
        locks[KEY]["admitted"] = (
            locks[KEY]["admitted"][0]._replace(field=broken),
            *locks[KEY]["admitted"][1:])
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            fields=(broken, *locks[KEY]["frame"].fields[1:]))
        message = _expect(self, module, candidate, locks,
                          "emboss element numeric contract mismatch")
        self.assertNotIn("sharpen element numeric contract mismatch", message)

    def test_a_native_type_drift_fails_the_element_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        broken = locks[KEY]["admitted"][3].field._replace(native_type="float")
        locks[KEY]["admitted"] = (
            *locks[KEY]["admitted"][:3],
            locks[KEY]["admitted"][3]._replace(field=broken),
            locks[KEY]["admitted"][4])
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            fields=(*locks[KEY]["frame"].fields[:3], broken,
                    locks[KEY]["frame"].fields[4]))
        message = _expect(self, module, candidate, locks,
                          "edge element numeric contract mismatch")
        self.assertNotIn("emboss element numeric contract mismatch", message)

    def test_a_retyped_declaration_fails_the_contract_before_identity(self):
        """Value checks run ahead of node identity: retyping the declaration
        must name the contract, not the identity hash that absorbs it."""
        module = _module()
        candidate = _analyzed()
        vec2 = candidate.declarations[1].type  # the `resolution` uniform
        object.__setattr__(candidate.declarations[18], "type", vec2)
        message = _expect(self, module, candidate,
                          _relocked(module, candidate),
                          "blur element numeric contract mismatch")
        self.assertNotIn("declaration identity mismatch", message)

    def test_a_mutable_reference_helper_parameter_fails_the_frame_contract(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            helper_parameter="Frame& frame")
        _expect(self, module, candidate, locks,
                "frame emission contract mismatch")

    def test_a_const_writer_parameter_fails_the_frame_contract(self):
        """Only ``loadKernels`` takes ``Frame&``; relaxing it the other way --
        making the writer's parameter const -- is equally a contract drift."""
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            writer_parameter="const Frame& frame")
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


class MutableGlobalArrayCensusTests(unittest.TestCase):
    def test_the_admitted_symbol_map_is_derived_per_key_not_at_import(self):
        module = _module()
        self.assertFalse(hasattr(module, "_ADMITTED_SYMBOLS"),
                         "no import-time global bound to CELLREFRACT_KEY")
        expected = {17: "emboss", 18: "sharpen", 19: "blur", 20: "edge",
                    21: "edge2"}
        self.assertEqual(expected,
                         module._admitted_symbols(module._LOCKS[KEY]))
        other = copy.deepcopy(module._LOCKS[KEY])
        other["admitted"] = (
            other["admitted"][0]._replace(symbol_id=77, ordinal=0),)
        self.assertEqual({77: "emboss"},
                         module._admitted_symbols(other))
        import inspect
        for name in ("_reference_census", "_no_indirect_write_holds"):
            with self.subTest(consumer=name):
                signature = inspect.signature(getattr(module, name))
                self.assertIn("symbols", signature.parameters)
                self.assertIs(inspect.Parameter.empty,
                              signature.parameters["symbols"].default)

    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual(1670, total)
        self.assertEqual(173, assigns)
        self.assertEqual(total, module._LOCKS[KEY]["total_nodes"])
        self.assertEqual(assigns, module._LOCKS[KEY]["total_assigns"])
        self.assertEqual(22, len(program.functions))
        self.assertEqual(22, module._LOCKS[KEY]["function_count"])
        inventory = module._LOCKS[KEY]["function_inventory"]
        self.assertEqual(22, len(inventory))
        self.assertEqual(inventory, tuple(
            (item.id, item.name, item.return_type.display(),
             tuple((p.id, p.name, p.type.display()) for p in item.parameters))
            for item in program.functions))

    def test_the_store_census_is_forty_five_plain_assignments_in_loadKernels(self):
        module = _module()
        program = _analyzed()
        stores, references = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        self.assertEqual(STORE_COUNT, len(stores))
        self.assertEqual([], references)
        self.assertEqual({WRITER_ID}, {item.owner_id for item in stores})
        self.assertEqual(["loadKernels"] * STORE_COUNT,
                         [item.owner_name for item in stores])
        self.assertEqual(["="] * STORE_COUNT,
                         [item.operator for item in stores])
        per_base = {}
        for item in stores:
            per_base.setdefault(item.base_id, []).append(item.index)
        self.assertEqual({17: list(range(9)), 18: list(range(9)),
                          19: list(range(9)), 20: list(range(9)),
                          21: list(range(9))}, per_base)
        self.assertEqual(module._LOCKS[KEY]["stores"],
                         tuple(item.record for item in stores))
        self.assertEqual(module._LOCKS[KEY]["store_triples"],
                         tuple((item.base_id, item.index, item.value_number)
                               for item in stores))

    def test_nineteen_store_values_are_unary_minus_of_literals(self):
        """Design Amendment 14: 19 of the 45 values are ``unary(-)`` nodes, so
        the writer lock must extract values as literal-or-unary-minus-of-
        literal, exactly like ``_number()`` in the fixed-array proof."""
        module = _module()
        program = _analyzed()
        stores, _ = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        unary = [item for item in stores if item.value.kind == "unary"]
        self.assertEqual(19, len(unary))
        self.assertEqual("-", unary[0].value.operator)
        fixed = importlib.import_module(
            "tools.glslcpp.frontend.fixed_array_in_parameter_proof")
        for item in stores:
            self.assertEqual(item.record.value, fixed._number(item.value))

    def test_the_write_only_census_counts_every_reference_program_wide(self):
        """45 ``id`` references to symbols 17-21 in the whole program -- every
        function body AND every declaration initializer (there are none, and
        the census is what proves that) -- zero reads, zero whole-array
        bases."""
        module = _module()
        program = _analyzed()
        symbols = module._admitted_symbols(module._LOCKS[KEY])
        total = sum(1 for node in _nodes(program)
                    if node.kind == "id" and node.symbol_id in symbols)
        stores, references = module._reference_census(program, symbols)
        self.assertEqual(45, total)
        self.assertEqual(total, len(stores) + len(references))
        self.assertEqual((), module._LOCKS[KEY]["references"])

    def test_the_writer_body_is_forty_five_sole_expression_expr_statements(self):
        module = _module()
        program = _analyzed()
        writer = _fn(program, "loadKernels")
        self.assertEqual(STORE_COUNT, len(writer.body))
        self.assertEqual(("expr",) * STORE_COUNT,
                         tuple(item.kind for item in writer.body))
        for statement in writer.body:
            self.assertEqual(1, len(statement.expressions))
            self.assertEqual(0, len(statement.children))
        self.assertEqual(module._LOCKS[KEY]["writer_body"],
                         tuple((item.kind, module._span(item))
                               for item in writer.body))
        stores, _ = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        for site in stores:
            statement = writer.body[site.statement_index]
            self.assertIs(statement, site.chain[0])
            self.assertEqual(1, len(site.chain), "the store is not nested")
            self.assertIs(statement.expressions[0], site.node)

    def test_main_calls_the_writer_once_before_every_state_consumer(self):
        """The crux. Re-derived here, not taken from the design."""
        module = _module()
        program = _analyzed()
        main = _main(program)
        lock = module._LOCKS[KEY]
        sites = module._writer_call_sites(main, lock)
        self.assertEqual(1, len(sites))
        index, statement, node, path, chain = sites[0]
        self.assertEqual(WRITER_CALL_INDEX, index)
        self.assertEqual(1, len(chain))
        self.assertIs(main.body[index], statement)
        self.assertEqual("expr", statement.kind)
        self.assertEqual(1, len(statement.expressions))
        self.assertIs(statement.expressions[0], node)
        self.assertEqual("loadKernels", node.callee)
        self.assertEqual(WRITER_ID, node.signature_id)
        self.assertEqual(0, len(node.children), "no arguments")
        self.assertEqual("void", node.type.display(), "void context")
        consumers = []
        for position, item in enumerate(main.body):
            callees = tuple(sorted({
                entry.callee
                for entry, _, _, _, _ in module._walk_statement(item,
                                                                (position,))
                if entry.kind == "call"
                and (entry.callee, entry.signature_id) in lock[
                    "state_consumer_ids"]}))
            if callees:
                consumers.append((position, callees))
        self.assertEqual(((5, ("map",)), (6, ("map",)), (7, ("cells",)),
                          (8, ("map",))), tuple(consumers))
        self.assertEqual(tuple(consumers), lock["state_consumers"])
        for position, _ in consumers:
            self.assertLess(index, position)

    def test_the_program_loop_and_call_graph_profile(self):
        module = _module()
        program = _analyzed()
        proof = program.counted_loop_proof
        self.assertEqual((3, 0, 2, 25, 30, True),
                         (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth,
                          proof.max_lexical_product,
                          proof.entrypoint_charge,
                          proof.call_graph_acyclic))
        self.assertEqual((3, 0, 2, 25, 30, True),
                         module._LOCKS[KEY]["counted_loop_proof"])
        edges = module._call_graph(program)
        self.assertEqual(16, len(edges))
        self.assertEqual(module._sha(edges),
                         module._LOCKS[KEY]["call_graph_sha256"])
        reachable, unreachable = module._reachability(program)
        self.assertEqual((64, 70, 71, 72, 74, 79, 83), reachable)
        self.assertEqual((65, 66, 67, 68, 69, 73, 75, 76, 77, 78, 80, 81, 82,
                          84, 85), unreachable)
        self.assertEqual(reachable, module._LOCKS[KEY]["reachable"])
        self.assertEqual(unreachable, module._LOCKS[KEY]["unreachable"])

    def test_the_resources_are_one_sampler_fourteen_uniforms_one_output(self):
        module = _module()
        program = _analyzed()
        resources = program.resources
        self.assertEqual(("inputTex",), resources.samplers)
        self.assertEqual(("fragColor",), resources.outputs)
        self.assertEqual(15, len(resources.uniforms))
        self.assertEqual(14, len(set(resources.uniforms) - set(
            resources.samplers)))
        self.assertTrue(resources.uses_texture)
        self.assertFalse(resources.uses_derivatives)
        self.assertEqual(((resources.uniforms, resources.samplers,
                           resources.outputs, resources.uses_texture,
                           resources.uses_derivatives)),
                         module._LOCKS[KEY]["resources"])

    def test_a_reference_hidden_in_a_global_initializer_is_censused(self):
        """A read planted in a declaration initializer is outside every walker
        that only descends ``function.body``. It must not escape."""
        module = _module()
        candidate = _analyzed()
        planted = _id_clone(candidate, EMBOSS_ID)
        host = candidate.declarations[0]
        object.__setattr__(host, "initializer", planted)
        locks = _relocked(module, candidate)
        locks[KEY].update(_reinventory(module, candidate))
        locks[KEY].update(_recount(module, candidate))
        message = _expect(self, module, candidate, locks,
                          "global declaration initializer census mismatch")
        self.assertNotIn("write-only reference census", message)


class MutableGlobalArrayLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK.

    For each row: mutate the tree (or the frozen record the lock owns),
    refreeze only the coarse hashes and the counters the mutation unavoidably
    moves, show the real module rejects with that lock's own message, then
    re-exec the module with exactly that predicate neutralized and show the
    message is gone.
    """

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            recallgraph=False, relock=None):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount(module, candidate))
        if recallgraph:
            overrides.update(_recallgraph(module, candidate))
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_mutable_global_array(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    # --- coarse gate -------------------------------------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_array(
                _analyzed(), "0" * 64, PROFILE)
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            5, len(scratch.authenticate_mutable_global_array(
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
            function = _fn(candidate, "wrapEdges")
            object.__setattr__(
                candidate, "functions",
                tuple(dataclasses.replace(item, signature=dataclasses.replace(
                    item.signature, name="planted"))
                    if item is function else item
                    for item in candidate.functions))
        survived = self._delete_and_compare(
            mutate, "_function_inventory_holds", "function inventory mismatch")
        self.assertIsNone(survived)

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources, uses_texture=False))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "hsv2rgb").body[0].expressions[0]
            planted = dataclasses.replace(
                _main(candidate).body[5].expressions[0].children[0])
            self.assertEqual("call", planted.kind)
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(survived)

    # --- declarations ------------------------------------------------------

    def test_ordinal_and_adjacency_lock(self):
        def mutate(candidate):
            declarations = list(candidate.declarations)
            declarations[17], declarations[18] = (declarations[18],
                                                  declarations[17])
            object.__setattr__(candidate, "declarations", tuple(declarations))
        survived = self._delete_and_compare(
            mutate, "_ordinal_adjacency_holds",
            "admitted array declaration ordinal or adjacency mismatch")
        self.assertIsNone(
            survived,
            "lookup is by symbol id, so only the ordinal lock sees a swap")

    def test_mutable_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[16]
            object.__setattr__(declaration.symbol, "storage", "const")
        survived = self._delete_and_compare(
            mutate, "_mutable_storage_holds",
            "admitted array storage or mutability mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("admitted array declaration identity mismatch", survived)

    def test_uninitialised_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[16]
            object.__setattr__(
                declaration, "initializer",
                dataclasses.replace(
                    _fn(candidate, "map").body[0].expressions[0].children[0]))
        survived = self._delete_and_compare(
            mutate, "_uninitialized_holds",
            "admitted array declaration carries an initializer", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("admitted array declaration identity mismatch", survived)

    def test_element_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        broken = locks[KEY]["admitted"][4].field._replace(js_initializer="0.0")
        locks[KEY]["admitted"] = (
            *locks[KEY]["admitted"][:4],
            locks[KEY]["admitted"][4]._replace(field=broken))
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            fields=(*locks[KEY]["frame"].fields[:4], broken))
        _expect(self, module, candidate, locks,
                "edge2 element numeric contract mismatch")
        scratch = _scratch(module, "_element_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    def test_declaration_identity_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[20]
            object.__setattr__(
                declaration, "span",
                dataclasses.replace(declaration.span, end_column=17))
        survived = self._delete_and_compare(
            mutate, "_declaration_identity_holds",
            "admitted array declaration identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("global declaration inventory mismatch", survived)

    def test_declaration_inventory_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[16]
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
            host = candidate.declarations[1]
            object.__setattr__(
                host, "initializer",
                dataclasses.replace(
                    _fn(candidate, "map").body[0].expressions[0].children[0]))
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked(module, candidate, **_recount(module, candidate),
                          **_reinventory(module, candidate))
        _expect(self, module, candidate, locks,
                "global declaration initializer census mismatch")
        scratch = _scratch(module, "_initializer_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_mutable_global_array(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        self.assertIsNone(survived)

    def test_frame_contract_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["frame"] = locks[KEY]["frame"]._replace(
            helper_parameter_ordinal=3)
        _expect(self, module, candidate, locks,
                "frame emission contract mismatch")
        scratch = _scratch(module, "_frame_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    # --- writer and stores -------------------------------------------------

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "map").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived)

    def test_writer_function_lock(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            object.__setattr__(
                writer, "span",
                dataclasses.replace(writer.span, end_line=65))
        survived = self._delete_and_compare(
            mutate, "_writer_function_holds", "writer function shape mismatch")
        self.assertIsNone(survived)

    def test_writer_body_lock(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            object.__setattr__(
                statement, "span",
                dataclasses.replace(statement.span, end_column=99))
        survived = self._delete_and_compare(
            mutate, "_writer_body_holds", "writer body shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("store identity mismatch", survived,
                      "the statement span is also frozen per store record")

    def test_store_cardinality_lock_deleting_a_store(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            object.__setattr__(writer, "body", writer.body[1:])

        def relock(module, candidate, overrides):
            overrides.update(_rewriterbody(module, candidate))
        survived = self._delete_and_compare(
            mutate, "_write_cardinality_holds",
            "store census cardinality mismatch: 44", recount=True,
            relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("store position mismatch", survived)

    def test_store_cardinality_lock_duplicating_a_store(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            object.__setattr__(
                writer, "body",
                (*writer.body, dataclasses.replace(writer.body[0])))

        def relock(module, candidate, overrides):
            overrides.update(_rewriterbody(module, candidate))
        survived = self._delete_and_compare(
            mutate, "_write_cardinality_holds",
            "store census cardinality mismatch: 46", recount=True,
            relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("store position mismatch", survived)

    def test_store_owner_lock(self):
        """Relocate a store into a helper. The count stays 45, so only the
        owner lock can see it."""
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            object.__setattr__(writer, "body", writer.body[1:])
            cells = _fn(candidate, "cells")
            object.__setattr__(cells, "body", (statement, *cells.body))

        def relock(module, candidate, overrides):
            overrides.update(_rewriterbody(module, candidate))
        survived = self._delete_and_compare(
            mutate, "_write_owner_holds",
            "mutable global array single-writer proof mismatch", relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("store position mismatch", survived)

    def test_store_position_lock(self):
        """Nest a store inside a block whose statement kind and span are those
        of the statement it replaces, so the writer's body shape is unchanged
        and only the position lock can see the nesting."""
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            inner = dataclasses.replace(statement)
            wrapper = dataclasses.replace(
                statement, kind="expr", expressions=(),
                children=(dataclasses.replace(statement, kind="block",
                                              expressions=(),
                                              children=(inner,)),))
            object.__setattr__(writer, "body",
                               (wrapper, *writer.body[1:]))
        survived = self._delete_and_compare(
            mutate, "_store_position_holds", "store position mismatch",
            recount=True)
        self.assertIsNone(
            survived,
            "nesting the store is invisible to every other lock, which is "
            "exactly why the position lock has to exist")

    def test_store_shape_lock_catches_a_compound_operator(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            object.__setattr__(node, "operator", "+=")
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("indirect partial or compound write present", survived,
                      "the indirect-write lock is the second line of defence "
                      "for compound operators")

    def test_store_shape_lock_catches_a_non_literal_index(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            target = node.children[0]
            planted = _id_clone(candidate, 3)  # the int uniform `seed`
            object.__setattr__(target, "children",
                               (target.children[0], planted))
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("kernel table payload mismatch", survived)

    def test_store_shape_lock_catches_a_non_literal_value(self):
        """Amendment 14: a value that is neither a literal nor the unary minus
        of a literal -- here an id reference to the float uniform `time`."""
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[2].expressions[0]
            planted = _id_clone(candidate, 2)
            object.__setattr__(node, "children",
                               (node.children[0], planted))
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("kernel table payload mismatch", survived)

    def test_store_triples_lock(self):
        """The 45 (base, index, value) triples are the program's kernel
        tables; flipping one constant must fail the payload lock."""
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            literal = node.children[1].children[0]
            self.assertEqual("unary", node.children[1].kind)
            object.__setattr__(literal, "literal_value", 3.0)
        survived = self._delete_and_compare(
            mutate, "_store_triples_holds", "kernel table payload mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("store identity mismatch", survived)

    def test_store_identity_lock(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[44].expressions[0]
            object.__setattr__(
                node, "span",
                dataclasses.replace(node.span, end_column=52))
        survived = self._delete_and_compare(
            mutate, "_write_identity_holds", "store identity mismatch")
        self.assertIsNone(survived)

    def test_no_indirect_write_lock_catches_a_whole_array_assignment(self):
        def mutate(candidate):
            target = _id_clone(candidate, EMBOSS_ID)
            value = _id_clone(candidate, 2)
            template = _main(candidate).body[10].expressions[0]
            planted = dataclasses.replace(template, operator="=",
                                          children=(target, value))
            main = _main(candidate)
            object.__setattr__(
                main, "body",
                (*main.body,
                 dataclasses.replace(main.body[3], expressions=(planted,))))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "indirect partial or compound write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("write-only reference census mismatch", survived)

    def test_no_indirect_write_lock_catches_a_POSTFIX_increment(self):
        """`post` is a distinct IR kind from `unary`, not an operator of it."""
        def mutate(candidate):
            template = _fn(candidate, "loadKernels").body[0].expressions[0]
            post = dataclasses.replace(
                template, kind="post", operator="++",
                children=(dataclasses.replace(template.children[0]),))
            main = _main(candidate)
            object.__setattr__(
                main, "body",
                (*main.body,
                 dataclasses.replace(main.body[3], expressions=(post,))))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "indirect partial or compound write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("write-only reference census mismatch", survived)

    def test_no_indirect_write_lock_catches_a_PREFIX_increment(self):
        def mutate(candidate):
            template = _fn(candidate, "loadKernels").body[0].expressions[0]
            unary = dataclasses.replace(
                template, kind="unary", operator="--",
                children=(dataclasses.replace(template.children[0]),))
            main = _main(candidate)
            object.__setattr__(
                main, "body",
                (*main.body,
                 dataclasses.replace(main.body[3], expressions=(unary,))))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "indirect partial or compound write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("write-only reference census mismatch", survived)

    def test_a_compound_write_is_caught_by_the_cardinality_first(self):
        """A *planted* compound write raises the store count, so the
        cardinality lock names it first; `_no_indirect_write_holds` is the
        second line of defence via its `operator != "="` branch -- shown here
        by deleting the three write locks that precede it."""
        module = _module()
        candidate = _analyzed()
        template = _fn(candidate, "loadKernels").body[0].expressions[0]
        planted = dataclasses.replace(
            template, operator="+=",
            children=(dataclasses.replace(template.children[0]),
                      template.children[1]))
        writer = _fn(candidate, "loadKernels")
        object.__setattr__(
            writer, "body",
            (*writer.body, dataclasses.replace(writer.body[0],
                                               expressions=(planted,))))
        locks = _relocked(module, candidate, **_recount(module, candidate),
                          **_rewriterbody(module, candidate))
        _expect(self, module, candidate, locks,
                "store census cardinality mismatch: 46")

        scratch = _scratch(module, "_write_cardinality_holds",
                           "_write_owner_holds", "_store_position_holds",
                           "_store_shape_holds", "_store_triples_holds")
        with mock.patch.object(scratch, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            scratch.authenticate_mutable_global_array(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        self.assertIn("indirect partial or compound write present",
                      str(raised.exception))

    def test_write_only_census_lock(self):
        """A read of any array inserted anywhere in the program must fail the
        write-only census, which is a property of the frozen KERNEL=0."""
        def mutate(candidate):
            planted = _id_clone(candidate, BLUR_ID)
            host = _main(candidate).body[10].expressions[0].children[1]
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_write_only_census_holds",
            "write-only reference census mismatch: 1", recount=True)
        self.assertIsNone(survived)

    def test_single_caller_lock(self):
        """A second caller of `loadKernels`: the call-graph lock is refrozen
        to the mutant, so only the explicit single-caller lock can see it."""
        def mutate(candidate):
            main = _main(candidate)
            statement = dataclasses.replace(main.body[3])
            cells = _fn(candidate, "cells")
            object.__setattr__(cells, "body", (*cells.body, statement))
        survived = self._delete_and_compare(
            mutate, "_single_caller_holds", "writer call site census mismatch",
            recount=True, recallgraph=True)
        self.assertIsNone(survived)

    def test_writer_call_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            call = dataclasses.replace(main.body[3].expressions[0])
            object.__setattr__(
                call, "span",
                dataclasses.replace(call.span, end_column=20))
            object.__setattr__(
                main, "body",
                (*main.body[:3],
                 dataclasses.replace(main.body[3], expressions=(call,)),
                 *main.body[4:]))
        survived = self._delete_and_compare(
            mutate, "_writer_call_holds", "writer call site in main mismatch")
        self.assertIsNone(survived)

    def test_moving_the_call_statement_fails_the_frozen_index(self):
        """Swapping the call with the following `decl` statement changes no
        node, span or hash -- only the statement index -- so the frozen index
        sub-clause is the one thing that can catch a relocated call."""
        def mutate(candidate):
            main = _main(candidate)
            body = list(main.body)
            body[3], body[4] = body[4], body[3]
            object.__setattr__(main, "body", tuple(body))

        def relock(module, candidate, overrides):
            overrides.update(_remainbody(module, candidate))
        survived = self._delete_and_compare(
            mutate, "_writer_call_holds", "writer call site in main mismatch",
            relock=relock)
        self.assertIsNone(survived)

    def test_dominance_lock_moving_the_call_after_cells(self):
        def mutate(candidate):
            main = _main(candidate)
            body = list(main.body)
            body[3], body[7] = body[7], body[3]
            object.__setattr__(main, "body", tuple(body))

        def relock(module, candidate, overrides):
            # Refreeze the call-site record, the consumer census and the body
            # shape to the mutant so ONLY the ordering premise can fire.
            overrides.update(_remainbody(module, candidate))
            overrides.update(_recallwriter(module, candidate))
        survived = self._delete_and_compare(
            mutate, "_writer_call_dominance_holds",
            "writer call dominance mismatch", relock=relock)
        self.assertIsNone(survived)

    def test_dominance_lock_catches_a_new_state_consumer_statement(self):
        """A `map` call grafted into a later statement keeps the ordering
        intact and changes no statement kind or span; only the frozen
        consumer census can see it."""
        def mutate(candidate):
            main = _main(candidate)
            planted = dataclasses.replace(
                main.body[5].expressions[0].children[0])
            self.assertEqual("call", planted.kind)
            host = main.body[9].expressions[0].children[0]
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_writer_call_dominance_holds",
            "writer call dominance mismatch", recount=True)
        self.assertIsNone(survived)

    def test_main_body_shape_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            object.__setattr__(main, "body",
                               (*main.body[:14], *main.body[15:]))
        survived = self._delete_and_compare(
            mutate, "_main_body_holds", "main body shape mismatch",
            recount=True)
        self.assertIsNone(survived)


class MutableGlobalArrayLedgerTests(unittest.TestCase):
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
        self.assertEqual(5, len(module.authenticate_mutable_global_array(
            _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "mutable-global-array visitation ledger mismatch"):
                module.authenticate_mutable_global_array(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(5, len(module.authenticate_mutable_global_array(
            _analyzed(), RAW_SHA256, PROFILE)))


class MutableGlobalArrayVocabularyTests(unittest.TestCase):
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
        # `float` is already an approved type and `float[9]` is that type in
        # array clothing: it is the STORAGE class, not the type, being admitted.
        self.assertIn("float", generate_typed_slice.APPROVED_TYPES)
        for token in (PROFILE, "mutable-global-array", "Kernel9",
                      "mutable-global-nine-array"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)
                self.assertNotIn(token, generate_typed_slice.APPROVED_TYPES)

    def test_the_module_never_grows_the_vocabulary_by_import(self):
        """Importing the module must not mutate either frozen tuple."""
        before = (generate_typed_slice.APPROVED_CAPABILITIES,
                  generate_typed_slice.APPROVED_TYPES)
        module = _module()
        module.authenticate_mutable_global_array(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(before[0], generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))


class KaleidoMutableGlobalArraySurfaceTests(unittest.TestCase):
    """The second carrier: same mechanism, its own per-key record.

    Every figure in these tests was measured against the pinned corpus by the
    same helpers the module uses (see docs/port-engineering/kaleido-parity/
    kaleido-design.md); none is transcribed from any other document.
    """

    def test_kaleido_is_the_second_key_with_its_own_profile(self):
        """kaleido's record was landed PREPARED (authenticatable, one step
        short of registration) and REGISTERED by the integration slice
        together with its row: `load_slice` enforces that the slice's array
        rows equal exactly the registered key census
        (generate_typed_slice.py, "typed slice mutable-global array profile
        drift"). The registry now holds both convolve-family keys; the
        prepared set is empty again, kept for the next prepared key."""
        module = _module()
        # effects (row 188) joined the registry after kaleido; kaleido
        # remains the SECOND key, effects the third.
        self.assertEqual((KEY, KALEIDO_KEY, EFFECTS_KEY), module.KEYS)
        self.assertEqual({KEY: PROFILE, KALEIDO_KEY: KALEIDO_PROFILE,
                          EFFECTS_KEY: EFFECTS_PROFILE},
                         module.PROFILES)
        self.assertEqual(frozenset({KEY, KALEIDO_KEY, EFFECTS_KEY}),
                         module.MUTABLE_GLOBAL_ARRAY_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual(KALEIDO_KEY, module.KALEIDO_KEY)
        self.assertEqual(KALEIDO_PROFILE, module.KALEIDO_PROFILE)
        self.assertIn(KALEIDO_KEY, module._LOCKS)
        self.assertEqual(KALEIDO_PROFILE, module._LOCKS[KALEIDO_KEY]["profile"])
        for name in ("KALEIDO_KEY", "KALEIDO_PROFILE", "PREPARED_KEYS"):
            self.assertIn(name, module.__all__)
            self.assertTrue(hasattr(module, name))
        # the one-line move the design records has happened: the registered
        # census is the complete authenticatable set.
        self.assertEqual((KEY, KALEIDO_KEY, EFFECTS_KEY),
                         tuple([*module.KEYS, *module.PREPARED_KEYS]))

    def test_kaleido_row_field_allowlist_names_the_required_xor_companion(self):
        """kaleido first-blocks on `exact scalar uint XOR profile carrier
        required` (measured against the live slice), so unlike cellRefract its
        row legitimately carries a SECOND profile -- the already-frozen
        `scalar-uint-xor-v1`. The allowlist is per key; cellRefract's
        three-field set is unchanged. Since integration, kaleido's contract
        answers from ALLOWED_ROW_FIELDS; PREPARED_ROW_FIELDS is empty."""
        module = _module()
        self.assertEqual(
            {"defines", "program_key", "mutable_global_array_profile",
             "scalar_uint_xor_profile"},
            set(module.allowed_row_fields(KALEIDO_KEY)))
        self.assertEqual(set(module.allowed_row_fields(KALEIDO_KEY)),
                         set(module.ALLOWED_ROW_FIELDS[KALEIDO_KEY]))
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)
        self.assertIn(KALEIDO_KEY, module.ALLOWED_ROW_FIELDS)
        self.assertNotEqual(module.allowed_row_fields(KEY),
                            module.allowed_row_fields(KALEIDO_KEY))
        self.assertEqual(
            {"defines", "program_key", "mutable_global_array_profile"},
            module.allowed_row_fields(KEY) & {"defines", "program_key",
                                              "mutable_global_array_profile",
                                              "scalar_uint_xor_profile"})
        contract = module.frame_contract(KALEIDO_KEY)
        self.assertEqual("loadKernels", contract.writer_function)
        self.assertEqual(ARRAY_NAMES,
                         tuple(item.name for item in contract.fields))

    def test_kaleido_frozen_source_path_and_hashes(self):
        module = _module()
        lock = module._LOCKS[KALEIDO_KEY]
        self.assertEqual(KALEIDO_SOURCE_PATH, lock["source_path"])
        raw = (CORPUS / lock["source_path"]).read_bytes()
        self.assertEqual(27567, len(raw))
        self.assertEqual(KALEIDO_RAW_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(KALEIDO_RAW_SHA256, lock["raw_sha256"])
        self.assertEqual(KALEIDO_NORMALIZED_SHA256, lock["normalized_sha256"])
        self.assertEqual(21817, lock["normalized_bytes"])
        # Cross-module consistency: the already-frozen scalar-uint-XOR lock for
        # kaleido pins the same raw source (verify, don't rebuild).
        from tools.glslcpp.frontend import scalar_uint_xor_profile
        self.assertEqual(
            KALEIDO_RAW_SHA256,
            scalar_uint_xor_profile._PROFILES[KALEIDO_KEY]["raw_sha256"])

    def test_kaleido_failures_name_the_kaleido_profile(self):
        module = _module()
        prefix = re.escape(f"{KALEIDO_PROFILE}: ")
        program = _analyzed_k()
        for carrier in ("wrong", "mutable-global-nine-array-cellrefract-v1",
                        "scalar-uint-xor-v1"):
            with self.subTest(carrier=carrier), self.assertRaises(ValueError) as ctx:
                module.authenticate_mutable_global_array(
                    program, KALEIDO_RAW_SHA256, carrier)
            self.assertRegex(str(ctx.exception), f"^{prefix}")
            self.assertIn("exact profile carrier required",
                          str(ctx.exception))


class KaleidoMutableGlobalArrayAdmissionTests(unittest.TestCase):
    def test_authenticates_all_five_declarations_in_declaration_order(self):
        module = _module()
        program = _analyzed_k()
        admitted = module.authenticate_mutable_global_array(
            program, KALEIDO_RAW_SHA256, KALEIDO_PROFILE)
        self.assertEqual(5, len(admitted))
        for ordinal, declaration in zip(range(KALEIDO_FIRST_ORDINAL,
                                              KALEIDO_FIRST_ORDINAL + 5),
                                        admitted):
            self.assertIs(program.declarations[ordinal], declaration)
        self.assertEqual(list(ARRAY_NAMES),
                         [item.symbol.name for item in admitted])
        self.assertEqual(["float[9]"] * 5,
                         [item.type.display() for item in admitted])
        for item in admitted:
            self.assertEqual("global", item.symbol.storage)
            self.assertTrue(item.symbol.writable)
            self.assertIsNone(item.initializer)
        self.assertIs(program, module.apply_mutable_global_array(
            program, KALEIDO_RAW_SHA256, KALEIDO_PROFILE))

    def test_a_missing_or_wrong_carrier_is_rejected(self):
        module = _module()
        program = _analyzed_k()
        for carrier in (None, "", "wrong", "mutable-global-frame-shape-v1",
                        "const-global-nine-table-v1",
                        "mutable-global-nine-array-cellrefract-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_mutable_global_array(
                    program, KALEIDO_RAW_SHA256, carrier)

    def test_a_wrong_caller_source_hash_is_rejected(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_array(
                _analyzed_k(), "0" * 64, KALEIDO_PROFILE)

    def test_define_drift_fails_the_exact_define_lock(self):
        module = _module()
        expected = "exact preprocessor define lock mismatch"
        cases = [
            ("kernel drift", _analyzed_k(defines={"DIRECTION": 2,
                                                  "KERNEL": 1,
                                                  "LOOP_OFFSET": 10,
                                                  "METRIC": 0})),
            ("direction drift", _analyzed_k(defines={"DIRECTION": 0,
                                                     "KERNEL": 0,
                                                     "LOOP_OFFSET": 10,
                                                     "METRIC": 0})),
            ("loop offset drift", _analyzed_k(defines={"DIRECTION": 2,
                                                       "KERNEL": 0,
                                                       "LOOP_OFFSET": 30,
                                                       "METRIC": 0})),
            ("metric drift", _analyzed_k(defines={"DIRECTION": 2,
                                                  "KERNEL": 0,
                                                  "LOOP_OFFSET": 10,
                                                  "METRIC": 1})),
            ("defines erased", _analyzed_k(defines={})),
            ("order drift", dataclasses.replace(
                _analyzed_k(), preprocessor_defines=tuple(reversed(
                    _analyzed_k().preprocessor_defines)))),
        ]
        for label, candidate in cases:
            with self.subTest(axis=label):
                _expect(self, module, candidate,
                        _relocked(module, candidate, key=KALEIDO_KEY),
                        expected, profile=KALEIDO_PROFILE, key=KALEIDO_KEY)

    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed_k()
        lock = module._LOCKS[KALEIDO_KEY]
        total, assigns = module._node_census(program)
        self.assertEqual(3178, total)
        self.assertEqual(179, assigns)
        self.assertEqual(total, lock["total_nodes"])
        self.assertEqual(assigns, lock["total_assigns"])
        self.assertEqual(43, len(program.functions))
        self.assertEqual(43, lock["function_count"])
        self.assertEqual(17, len(program.declarations))
        self.assertEqual(17, lock["declaration_count"])
        self.assertEqual(lock["declaration_inventory"],
                         module._declaration_inventory(program))
        self.assertEqual(lock["function_inventory"], tuple(
            (item.id, item.name, item.return_type.display(),
             tuple((p.id, p.name, p.type.display()) for p in item.parameters))
            for item in program.functions))

    def test_the_kaleido_reachability_and_call_graph_profile(self):
        module = _module()
        program = _analyzed_k()
        lock = module._LOCKS[KALEIDO_KEY]
        proof = program.counted_loop_proof
        self.assertEqual((1, 0, 1, 9, 0, True),
                         (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth,
                          proof.max_lexical_product,
                          proof.entrypoint_charge,
                          proof.call_graph_acyclic))
        self.assertEqual((1, 0, 1, 9, 0, True), lock["counted_loop_proof"])
        edges = module._call_graph(program)
        self.assertEqual(51, len(edges))
        self.assertEqual(module._sha(edges), lock["call_graph_sha256"])
        reachable, unreachable = module._reachability(program)
        self.assertEqual(30, len(reachable))
        self.assertEqual(13, len(unreachable))
        self.assertEqual(reachable, lock["reachable"])
        self.assertEqual(unreachable, lock["unreachable"])
        # The array machinery is unreachable at the frozen defines: convolve,
        # its four callers and convolutionKernel are all in the unreachable
        # set, exactly as cellRefract's were.
        by_name = {f.name: f.id for f in program.functions}
        for name in ("convolve", "derivatives", "sobel", "outline", "shadow",
                     "convolutionKernel"):
            self.assertIn(by_name[name], unreachable,
                          f"{name} must be unreachable at KERNEL=0")

    def test_the_resources_are_one_sampler_eleven_uniforms_one_output(self):
        module = _module()
        program = _analyzed_k()
        resources = program.resources
        self.assertEqual(("inputTex",), resources.samplers)
        self.assertEqual(("fragColor",), resources.outputs)
        self.assertEqual(11, len(resources.uniforms))
        # kaleido's `wrap` is a BOOL uniform; cellRefract's is an int.
        wrap = next(d for d in program.declarations
                    if d.symbol.name == "wrap")
        self.assertEqual("bool", wrap.type.display())
        self.assertTrue(resources.uses_texture)
        self.assertFalse(resources.uses_derivatives)
        self.assertEqual(((resources.uniforms, resources.samplers,
                           resources.outputs, resources.uses_texture,
                           resources.uses_derivatives)), 
                         module._LOCKS[KALEIDO_KEY]["resources"])

    def test_the_store_census_is_forty_five_plain_assignments(self):
        module = _module()
        program = _analyzed_k()
        stores, references = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KALEIDO_KEY]))
        self.assertEqual(KALEIDO_STORE_COUNT, len(stores))
        self.assertEqual([], references,
                         "kaleido is WRITE-ONLY at its frozen defines; the "
                         "readers were stripped by KERNEL=0 normalization")
        self.assertEqual({KALEIDO_WRITER_ID}, {item.owner_id for item in stores})
        self.assertEqual(["loadKernels"] * KALEIDO_STORE_COUNT,
                         [item.owner_name for item in stores])
        self.assertEqual(["="] * KALEIDO_STORE_COUNT,
                         [item.operator for item in stores])
        self.assertEqual(module._LOCKS[KALEIDO_KEY]["stores"],
                         tuple(item.record for item in stores))
        self.assertEqual(module._LOCKS[KALEIDO_KEY]["store_triples"],
                         tuple((item.base_id, item.index, item.value_number)
                               for item in stores))
        self.assertEqual((), module._LOCKS[KALEIDO_KEY]["references"])

    def test_the_kernel_table_payload_is_byte_identical_to_cellrefract(self):
        """The 45 (base, index, value) triples are the same kernel tables
        cellRefract freezes, under kaleido's own symbol ids 13-17 (cellRefract
        uses 17-21). Measured, not assumed."""
        module = _module()
        remapped = tuple(
            (base - (KALEIDO_EMBOSS_ID - EMBOSS_ID), index, value)
            for base, index, value
            in module._LOCKS[KALEIDO_KEY]["store_triples"])
        self.assertEqual(module._LOCKS[KEY]["store_triples"], remapped)

    def test_nineteen_kaleido_store_values_are_unary_minus_of_literals(self):
        module = _module()
        program = _analyzed_k()
        stores, _ = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KALEIDO_KEY]))
        unary = [item for item in stores if item.value.kind == "unary"]
        self.assertEqual(19, len(unary))
        self.assertEqual("-", unary[0].value.operator)
        fixed = importlib.import_module(
            "tools.glslcpp.frontend.fixed_array_in_parameter_proof")
        for item in stores:
            self.assertEqual(item.record.value, fixed._number(item.value))

    def test_the_writer_body_is_forty_five_sole_expression_statements(self):
        module = _module()
        program = _analyzed_k()
        writer = _fn(program, "loadKernels")
        self.assertEqual(KALEIDO_WRITER_ID, writer.id)
        self.assertEqual(0, len(writer.parameters))
        self.assertEqual("void", writer.return_type.display())
        self.assertEqual("39:1-65:2", module._span(writer))
        self.assertEqual(KALEIDO_STORE_COUNT, len(writer.body))
        self.assertEqual(("expr",) * KALEIDO_STORE_COUNT,
                         tuple(item.kind for item in writer.body))
        for statement in writer.body:
            self.assertEqual(1, len(statement.expressions))
            self.assertEqual(0, len(statement.children))
        self.assertEqual(module._LOCKS[KALEIDO_KEY]["writer_body"],
                         tuple((item.kind, module._span(item))
                               for item in writer.body))

    def test_main_calls_the_writer_once_before_every_user_call_statement(self):
        """kaleido's arrays are write-only, so nothing consumes their state;
        the frozen consumer census is instead every `main` statement bearing a
        user call -- map, offset, periodicFunction, kaleidoscope -- which the
        writer call must precede. Re-derived here, not taken from the design."""
        module = _module()
        program = _analyzed_k()
        main = _main(program)
        self.assertEqual(KALEIDO_MAIN_ID, main.id)
        self.assertEqual("813:1-833:2", module._span(main))
        self.assertEqual(11, len(main.body))
        lock = module._LOCKS[KALEIDO_KEY]
        sites = module._writer_call_sites(main, lock)
        self.assertEqual(1, len(sites))
        index, statement, node, path, chain = sites[0]
        self.assertEqual(KALEIDO_WRITER_CALL_INDEX, index)
        self.assertEqual(1, len(chain))
        self.assertIs(main.body[index], statement)
        self.assertEqual("expr", statement.kind)
        self.assertEqual(1, len(statement.expressions))
        self.assertIs(statement.expressions[0], node)
        self.assertEqual("loadKernels", node.callee)
        self.assertEqual(KALEIDO_WRITER_ID, node.signature_id)
        self.assertEqual(0, len(node.children), "no arguments")
        self.assertEqual("void", node.type.display(), "void context")
        consumers = []
        for position, item in enumerate(main.body):
            callees = tuple(sorted({
                entry.callee
                for entry, _, _, _, _ in module._walk_statement(item,
                                                                (position,))
                if entry.kind == "call"
                and (entry.callee, entry.signature_id) in lock[
                    "state_consumer_ids"]}))
            if callees:
                consumers.append((position, callees))
        self.assertEqual(((4, ("map",)), (6, ("offset",)),
                          (7, ("map", "periodicFunction")),
                          (8, ("kaleidoscope",))), tuple(consumers))
        self.assertEqual(tuple(consumers), lock["state_consumers"])
        for position, _ in consumers:
            self.assertLess(index, position)

    def test_the_initializer_census_is_empty_everywhere(self):
        module = _module()
        program = _analyzed_k()
        self.assertEqual(
            [], [item.symbol.name for item in program.declarations
                 if item.initializer is not None],
            "the program has no initializers at all; the census walks them")
        self.assertEqual((), module._LOCKS[KALEIDO_KEY]["initializer_census"])
        self.assertEqual((), module._initializer_census(program))

    def test_the_fixed_array_sibling_proof_is_allowed(self):
        module = _module()
        candidate = dataclasses.replace(
            _analyzed_k(), fixed_array_in_parameter_proof=object())
        admitted = module.authenticate_mutable_global_array(
            candidate, KALEIDO_RAW_SHA256, KALEIDO_PROFILE)
        self.assertEqual(5, len(admitted))

    def test_an_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed_k(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_mutable_global_array(
                        candidate, KALEIDO_RAW_SHA256, KALEIDO_PROFILE)

    def test_adjacency_is_immediately_after_the_fragColor_output(self):
        module = _module()
        program = _analyzed_k()
        preceding = program.declarations[KALEIDO_FIRST_ORDINAL - 1]
        self.assertEqual("fragColor", preceding.symbol.name)
        self.assertEqual("output", preceding.symbol.storage)
        self.assertEqual("vec4", preceding.type.display())
        self.assertEqual((KALEIDO_FRAGCOLOR_ORDINAL, preceding.symbol.id),
                         module._LOCKS[KALEIDO_KEY]["preceding"][:2])


class KaleidoMutableGlobalArrayLockDeletionTests(unittest.TestCase):
    """Every shared predicate is load-bearing FOR THE KALEIDO RECORD too.

    Same method as the cellRefract class: mutate the tree, refreeze only the
    coarse hashes and the counters the mutation unavoidably moves, show the
    module rejects with that lock's own message, then re-exec the module with
    exactly that predicate neutralized and show the message is gone."""

    KEY = KALEIDO_KEY
    PROFILE = KALEIDO_PROFILE

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            recallgraph=False, relock=None):
        module = _module()
        candidate = _analyzed_k()
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount(module, candidate, key=KALEIDO_KEY))
        if recallgraph:
            overrides.update(_recallgraph(module, candidate, key=KALEIDO_KEY))
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, key=KALEIDO_KEY, **overrides)
        _expect(self, module, candidate, locks, expected,
                profile=KALEIDO_PROFILE, key=KALEIDO_KEY)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_mutable_global_array(
                    candidate, locks[KALEIDO_KEY]["raw_sha256"],
                    KALEIDO_PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def test_caller_source_hash_lock(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_mutable_global_array(
                _analyzed_k(), "0" * 64, KALEIDO_PROFILE)
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            5, len(scratch.authenticate_mutable_global_array(
                _analyzed_k(), "0" * 64, KALEIDO_PROFILE)),
            "with the lock deleted nothing may reject a lying caller")

    def test_raw_source_lock(self):
        module = _module()
        mutated = KALEIDO_SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_mutable_global_array(
                _analyzed_k(raw=mutated), KALEIDO_RAW_SHA256, KALEIDO_PROFILE)

    def test_normalized_source_lock(self):
        module = _module()
        original = KALEIDO_SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("emboss[8] = 2.0;", "emboss[8] = 2.5;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed_k(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized",
                                  key=KALEIDO_KEY)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_mutable_global_array(
                candidate, locks[KALEIDO_KEY]["raw_sha256"], KALEIDO_PROFILE)

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
            function = _fn(candidate, "posterize")
            object.__setattr__(
                candidate, "functions",
                tuple(dataclasses.replace(item, signature=dataclasses.replace(
                    item.signature, name="planted"))
                    if item is function else item
                    for item in candidate.functions))
        survived = self._delete_and_compare(
            mutate, "_function_inventory_holds", "function inventory mismatch")
        self.assertIsNone(survived)

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources, uses_texture=False))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "hsv2rgb").body[0].expressions[0]
            planted = next(
                item for item in _nodes(candidate)
                if item.kind == "call" and item.callee == "periodicFunction")
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(survived)

    def test_ordinal_and_adjacency_lock(self):
        def mutate(candidate):
            declarations = list(candidate.declarations)
            declarations[13], declarations[14] = (declarations[14],
                                                 declarations[13])
            object.__setattr__(candidate, "declarations", tuple(declarations))
        survived = self._delete_and_compare(
            mutate, "_ordinal_adjacency_holds",
            "admitted array declaration ordinal or adjacency mismatch")
        self.assertIsNone(
            survived,
            "lookup is by symbol id, so only the ordinal lock sees a swap")

    def test_mutable_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[KALEIDO_FIRST_ORDINAL]
            object.__setattr__(declaration.symbol, "storage", "const")
        survived = self._delete_and_compare(
            mutate, "_mutable_storage_holds",
            "admitted array storage or mutability mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("admitted array declaration identity mismatch", survived)

    def test_uninitialised_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[KALEIDO_FIRST_ORDINAL]
            object.__setattr__(
                declaration, "initializer",
                dataclasses.replace(
                    _fn(candidate, "map").body[0].expressions[0].children[0]))
        survived = self._delete_and_compare(
            mutate, "_uninitialized_holds",
            "admitted array declaration carries an initializer", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("admitted array declaration identity mismatch", survived)

    def test_element_contract_lock(self):
        module = _module()
        candidate = _analyzed_k()
        locks = _relocked(module, candidate, key=KALEIDO_KEY)
        broken = locks[KALEIDO_KEY]["admitted"][4].field._replace(
            js_initializer="0.0")
        locks[KALEIDO_KEY]["admitted"] = (
            *locks[KALEIDO_KEY]["admitted"][:4],
            locks[KALEIDO_KEY]["admitted"][4]._replace(field=broken))
        locks[KALEIDO_KEY]["frame"] = locks[KALEIDO_KEY]["frame"]._replace(
            fields=(*locks[KALEIDO_KEY]["frame"].fields[:4], broken))
        _expect(self, module, candidate, locks,
                "edge2 element numeric contract mismatch",
                profile=KALEIDO_PROFILE, key=KALEIDO_KEY)
        scratch = _scratch(module, "_element_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_mutable_global_array(
                candidate, locks[KALEIDO_KEY]["raw_sha256"], KALEIDO_PROFILE))

    def test_declaration_identity_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[KALEIDO_FIRST_ORDINAL + 4]
            object.__setattr__(
                declaration, "span",
                dataclasses.replace(declaration.span, end_column=17))
        survived = self._delete_and_compare(
            mutate, "_declaration_identity_holds",
            "admitted array declaration identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("global declaration inventory mismatch", survived)

    def test_declaration_inventory_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[KALEIDO_FIRST_ORDINAL]
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
            host = candidate.declarations[1]
            object.__setattr__(
                host, "initializer",
                dataclasses.replace(
                    _fn(candidate, "map").body[0].expressions[0].children[0]))
        module = _module()
        candidate = _analyzed_k()
        mutate(candidate)
        locks = _relocked(module, candidate, key=KALEIDO_KEY,
                          **_recount(module, candidate, key=KALEIDO_KEY),
                          **_reinventory(module, candidate, key=KALEIDO_KEY))
        _expect(self, module, candidate, locks,
                "global declaration initializer census mismatch",
                profile=KALEIDO_PROFILE, key=KALEIDO_KEY)
        scratch = _scratch(module, "_initializer_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_mutable_global_array(
                    candidate, locks[KALEIDO_KEY]["raw_sha256"],
                    KALEIDO_PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        self.assertIsNone(survived)

    def test_frame_contract_lock(self):
        module = _module()
        candidate = _analyzed_k()
        locks = _relocked(module, candidate, key=KALEIDO_KEY)
        locks[KALEIDO_KEY]["frame"] = locks[KALEIDO_KEY]["frame"]._replace(
            helper_parameter_ordinal=3)
        _expect(self, module, candidate, locks,
                "frame emission contract mismatch",
                profile=KALEIDO_PROFILE, key=KALEIDO_KEY)
        scratch = _scratch(module, "_frame_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_mutable_global_array(
                candidate, locks[KALEIDO_KEY]["raw_sha256"], KALEIDO_PROFILE))

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "map").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived)

    def test_writer_function_lock(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            object.__setattr__(
                writer, "span",
                dataclasses.replace(writer.span, end_line=66))
        survived = self._delete_and_compare(
            mutate, "_writer_function_holds", "writer function shape mismatch")
        self.assertIsNone(survived)

    def test_writer_body_lock(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            object.__setattr__(
                statement, "span",
                dataclasses.replace(statement.span, end_column=99))
        survived = self._delete_and_compare(
            mutate, "_writer_body_holds", "writer body shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("store identity mismatch", survived,
                      "the statement span is also frozen per store record")

    def test_store_cardinality_lock_deleting_a_store(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            object.__setattr__(writer, "body", writer.body[1:])

        def relock(module, candidate, overrides):
            overrides.update(_rewriterbody(module, candidate, key=KALEIDO_KEY))
        survived = self._delete_and_compare(
            mutate, "_write_cardinality_holds",
            "store census cardinality mismatch: 44", recount=True,
            relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("store position mismatch", survived)

    def test_store_owner_lock(self):
        """Relocate a store into a helper. The count stays 45, so only the
        owner lock can see it."""
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            object.__setattr__(writer, "body", writer.body[1:])
            host = _fn(candidate, "map")
            object.__setattr__(host, "body", (statement, *host.body))

        def relock(module, candidate, overrides):
            overrides.update(_rewriterbody(module, candidate, key=KALEIDO_KEY))
        survived = self._delete_and_compare(
            mutate, "_write_owner_holds",
            "mutable global array single-writer proof mismatch", relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("store position mismatch", survived)

    def test_store_position_lock(self):
        def mutate(candidate):
            writer = _fn(candidate, "loadKernels")
            statement = writer.body[0]
            inner = dataclasses.replace(statement)
            wrapper = dataclasses.replace(
                statement, kind="expr", expressions=(),
                children=(dataclasses.replace(statement, kind="block",
                                              expressions=(),
                                              children=(inner,)),))
            object.__setattr__(writer, "body",
                               (wrapper, *writer.body[1:]))
        survived = self._delete_and_compare(
            mutate, "_store_position_holds", "store position mismatch",
            recount=True)
        self.assertIsNone(
            survived,
            "nesting the store is invisible to every other lock, which is "
            "exactly why the position lock has to exist")

    def test_store_shape_lock_catches_a_compound_operator(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            object.__setattr__(node, "operator", "+=")
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("indirect partial or compound write present", survived,
                      "the indirect-write lock is the second line of defence "
                      "for compound operators")

    def test_store_shape_lock_catches_a_non_literal_index(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            target = node.children[0]
            planted = _id_clone(candidate, 7)  # the int uniform `seed`
            object.__setattr__(target, "children",
                               (target.children[0], planted))
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("kernel table payload mismatch", survived)

    def test_store_shape_lock_catches_a_non_literal_value(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[2].expressions[0]
            planted = _id_clone(candidate, 5)  # the float uniform `time`
            object.__setattr__(node, "children",
                               (node.children[0], planted))
        survived = self._delete_and_compare(
            mutate, "_store_shape_holds", "store shape mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("kernel table payload mismatch", survived)

    def test_store_triples_lock(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[0].expressions[0]
            literal = node.children[1].children[0]
            self.assertEqual("unary", node.children[1].kind)
            object.__setattr__(literal, "literal_value", 3.0)
        survived = self._delete_and_compare(
            mutate, "_store_triples_holds", "kernel table payload mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("store identity mismatch", survived)

    def test_store_identity_lock(self):
        def mutate(candidate):
            node = _fn(candidate, "loadKernels").body[44].expressions[0]
            object.__setattr__(
                node, "span",
                dataclasses.replace(node.span, end_column=52))
        survived = self._delete_and_compare(
            mutate, "_write_identity_holds", "store identity mismatch")
        self.assertIsNone(survived)

    def test_no_indirect_write_lock_catches_a_whole_array_assignment(self):
        def mutate(candidate):
            target = _id_clone(candidate, KALEIDO_EMBOSS_ID)
            value = _id_clone(candidate, 5)
            template = _main(candidate).body[10].expressions[0]
            planted = dataclasses.replace(template, operator="=",
                                          children=(target, value))
            main = _main(candidate)
            object.__setattr__(
                main, "body",
                (*main.body,
                 dataclasses.replace(main.body[3], expressions=(planted,))))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "indirect partial or compound write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("write-only reference census mismatch", survived)

    def test_no_indirect_write_lock_catches_a_POSTFIX_increment(self):
        def mutate(candidate):
            template = _fn(candidate, "loadKernels").body[0].expressions[0]
            post = dataclasses.replace(
                template, kind="post", operator="++",
                children=(dataclasses.replace(template.children[0]),))
            main = _main(candidate)
            object.__setattr__(
                main, "body",
                (*main.body,
                 dataclasses.replace(main.body[3], expressions=(post,))))
        survived = self._delete_and_compare(
            mutate, "_no_indirect_write_holds",
            "indirect partial or compound write present", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("write-only reference census mismatch", survived)

    def test_write_only_census_lock(self):
        """A read of any array inserted anywhere must fail the write-only
        census, which is a property of the frozen KERNEL=0."""
        def mutate(candidate):
            planted = _id_clone(candidate, KALEIDO_BLUR_ID)
            host = _main(candidate).body[10].expressions[0].children[1]
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_write_only_census_holds",
            "write-only reference census mismatch: 1", recount=True)
        self.assertIsNone(survived)

    def test_single_caller_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            statement = dataclasses.replace(main.body[3])
            host = _fn(candidate, "map")
            object.__setattr__(host, "body", (*host.body, statement))
        survived = self._delete_and_compare(
            mutate, "_single_caller_holds", "writer call site census mismatch",
            recount=True, recallgraph=True)
        self.assertIsNone(survived)

    def test_writer_call_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            call = dataclasses.replace(main.body[3].expressions[0])
            object.__setattr__(
                call, "span",
                dataclasses.replace(call.span, end_column=20))
            object.__setattr__(
                main, "body",
                (*main.body[:3],
                 dataclasses.replace(main.body[3], expressions=(call,)),
                 *main.body[4:]))
        survived = self._delete_and_compare(
            mutate, "_writer_call_holds", "writer call site in main mismatch")
        self.assertIsNone(survived)

    def test_moving_the_call_statement_fails_the_frozen_index(self):
        """Swap the call with the PRECEDING `vec4 color` decl (index 2): unlike
        cellRefract, kaleido's statement 4 carries a `map` consumer, so moving
        the call past *that* neighbour is also a dominance violation. Swapping
        with the colour decl changes no node, span or hash -- only the
        statement index -- so the frozen index sub-clause is the one thing
        that can catch it."""
        def mutate(candidate):
            main = _main(candidate)
            body = list(main.body)
            body[2], body[3] = body[3], body[2]
            object.__setattr__(main, "body", tuple(body))

        def relock(module, candidate, overrides):
            overrides.update(_remainbody(module, candidate, key=KALEIDO_KEY))
        survived = self._delete_and_compare(
            mutate, "_writer_call_holds", "writer call site in main mismatch",
            relock=relock)
        self.assertIsNone(survived)

    def test_dominance_lock_moving_the_call_after_a_consumer(self):
        def mutate(candidate):
            main = _main(candidate)
            body = list(main.body)
            body[3], body[7] = body[7], body[3]
            object.__setattr__(main, "body", tuple(body))

        def relock(module, candidate, overrides):
            overrides.update(_remainbody(module, candidate, key=KALEIDO_KEY))
            overrides.update(_recallwriter(module, candidate,
                                           key=KALEIDO_KEY))
        survived = self._delete_and_compare(
            mutate, "_writer_call_dominance_holds",
            "writer call dominance mismatch", relock=relock)
        self.assertIsNone(survived)

    def test_dominance_lock_catches_a_new_state_consumer_statement(self):
        def mutate(candidate):
            main = _main(candidate)
            planted = next(
                item for item in _nodes(candidate)
                if item.kind == "call" and item.callee == "map")
            host = main.body[9].expressions[0].children[0]
            object.__setattr__(host, "children", (*host.children, planted))
        survived = self._delete_and_compare(
            mutate, "_writer_call_dominance_holds",
            "writer call dominance mismatch", recount=True)
        self.assertIsNone(survived)

    def test_main_body_shape_lock(self):
        def mutate(candidate):
            main = _main(candidate)
            object.__setattr__(main, "body",
                               (*main.body[:9], *main.body[10:]))
        survived = self._delete_and_compare(
            mutate, "_main_body_holds", "main body shape mismatch",
            recount=True)
        self.assertIsNone(survived)


class KaleidoMutableGlobalArrayLedgerTests(unittest.TestCase):
    def test_ledger_arithmetic_is_one_hundred_ninety_three(self):
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        self.assertEqual(
            5 + 5 + 1 + 1 + 4 * KALEIDO_STORE_COUNT + 1,
            module._CONSUMED_LEDGER,
            "five declarations, five symbols, the writer, main, the 45 "
            "stores' four nodes each, and the one writer call")

    def test_sabotaged_ledger_size_turns_a_valid_kaleido_red(self):
        module = _module()
        self.assertEqual(5, len(module.authenticate_mutable_global_array(
            _analyzed_k(), KALEIDO_RAW_SHA256, KALEIDO_PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "mutable-global-array visitation ledger mismatch"):
                module.authenticate_mutable_global_array(
                    _analyzed_k(), KALEIDO_RAW_SHA256, KALEIDO_PROFILE)

    def test_the_kaleido_ledger_failure_names_the_kaleido_profile(self):
        """Per-key profile prefixes: a kaleido ledger mismatch must name the
        kaleido profile, not the module's first key."""
        module = _module()
        with mock.patch.object(module, "_CONSUMED_LEDGER", LEDGER - 1), \
                self.assertRaises(ValueError) as raised:
            module.authenticate_mutable_global_array(
                _analyzed_k(), KALEIDO_RAW_SHA256, KALEIDO_PROFILE)
        self.assertTrue(
            str(raised.exception).startswith(f"{KALEIDO_PROFILE}: "),
            str(raised.exception))


class KaleidoMutableGlobalArrayVocabularyTests(unittest.TestCase):
    def test_no_capability_or_type_vocabulary_growth(self):
        _module()
        for token in (KALEIDO_PROFILE, "mutable-global-array", "Kernel9",
                      "mutable-global-nine-array"):
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
        module.authenticate_mutable_global_array(
            _analyzed_k(), KALEIDO_RAW_SHA256, KALEIDO_PROFILE)
        self.assertEqual(before[0], generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)


if __name__ == "__main__":
    unittest.main()
