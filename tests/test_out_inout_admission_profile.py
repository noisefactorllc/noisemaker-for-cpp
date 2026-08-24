"""Focused RED/GREEN proof for the ``synth/newton`` out-parameter
admission profile, extended per-key with ``filter/lightLeak:lightLeak``.

RED state captured before ``tools/glslcpp/frontend/
out_inout_admission_profile.py`` existed: every test in this file
reported ``AssertionError`` from ``_module`` (module absent).

``synth/newton:newton`` carries two ``out``-parameter functions (four
parameters total): ``df64_cmul(vec2, vec2, vec2, vec2, out vec2 rr, out
vec2 ri)`` and ``transformCoords_df64(..., out vec2 re_df, out vec2
im_df)`` -- and three bare void-call statements in ``main`` that pass
plain local ``vec2`` variables as the trailing out arguments. The design's
§0.5 hazard is why this is its own carrier: the emitter has **no
direction gate**, so an out parameter admitted without this module's
frozen direction contract (``glsl::Vec2&``, by-value forbidden) would be
emitted by value -- compiles, runs, silently wrong.

The lightLeak section (``LightLeak*`` classes) was written before the
phase-1 registry landing; its captured RED covered absent/prepare-only
surface assertions and the staged loop-proof entry.

``filter/lightLeak:lightLeak`` is the counted-for design's cost-rank-2
program (section 2.2/section 5): measured **three rungs from CLEAN at
both authorities** behind mechanism A (the frozen
``CountedForSeedContract`` dict entry), mechanism C (this module's two
out parameters on ``voronoiCell``), and mechanism D (the program-wide
bare-call census -- exactly the two out-call statements). The lightLeak
lock is frozen over the SEED-ATTACHED tree (semantic.py's own sequence),
so the tests build that tree with ``_analyzed_lightleak`` the same way
the integration slice will hold it.

Testing rules inherited from the family (see
``test_struct_declaration_profile.py``):

1. Locks are proved load-bearing by *deleting the lock* in a scratch
   module copy, after refreezing only the coarse hashes plus the census
   fields the mutation unavoidably moves.
2. Value tiers run ahead of identity tiers (Symbols and nodes embed
   spans AND absolute source offsets; identity hashes would otherwise
   absorb value drift -- which is why the lightLeak seed locks run ahead
   of the out/inout identity tiers in the module, and why the
   comparison-shape near-miss must be length-preserving (``>``, not
   ``!=`` -- the parallax lesson).
3. newton's and mandelbrot's rows are PREPARED; LightLeak's minimal row is
   landed, while the typed authority row remains a separate integration
   gate.
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
from tools.glslcpp.frontend import loop_proof as loop_proof_module
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, attach_counted_loop_proofs,
    summarize_counted_loop_proofs)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine, TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.out_inout_admission_profile"

KEY = "synth/newton:newton"
PROFILE = "out-inout-admission-newton-v1"
SOURCE_PATH = "synth/newton/newton.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac"
NORMALIZED_SHA256 = (
    "c021c2f8c0e8df9b0fe92b97d24d532a5d3ccfe44c0e8a75bba4a11cabcc5af8")

DF64_CMUL_ID = 62
TRANSFORM_ID = 73
OUT_PARAM_IDS = (48, 49, 55, 56)
CALL_COUNT = 3
LEDGER = 26

COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)

FOREIGN_SOURCE = (
    "out vec4 fragColor;\n"
    "void split(float a, out float hi, out float lo) {\n"
    "  hi = a; lo = a - hi;\n"
    "}\n"
    "void main() {\n"
    "  float x, y;\n"
    "  split(1.0, x, y);\n"
    "  fragColor = vec4(x, y, 0.0, 1.0);\n"
    "}\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("out/inout admission profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
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


# --- filter/lightLeak:lightLeak (counted-for design section 2.2/5) -----------

LIGHTLEAK_KEY = "filter/lightLeak:lightLeak"
LIGHTLEAK_PROFILE = "out-inout-admission-lightleak-v1"
LIGHTLEAK_SOURCE_PATH = "filter/lightLeak/lightLeak.glsl"
LIGHTLEAK_SOURCE = CORPUS / LIGHTLEAK_SOURCE_PATH
LIGHTLEAK_RAW_SHA256 = (
    "61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb")
LIGHTLEAK_NORMALIZED_SHA256 = (
    "4568d0dd53883cfc1cb1ba8237a894e9c5740c4f1a045dff377221722f3eef72")

VORONOI_ID = 29
CELL_COLOR_ID = 20
CELL_DIST_ID = 21
BASE_CELL_ID = 45
BASE_DIST_ID = 46
WARP_CELL_ID = 51
WARP_DIST_ID = 52
POINT_COUNT_SYMBOL_ID = 2
POINT_COUNT_VALUE = 6
LIGHTLEAK_CALL_COUNT = 2
LIGHTLEAK_LEDGER = 15
LIGHTLEAK_LIVE_SUMMARY = (0, 1, 0, 0, 0, True)
LIGHTLEAK_CLOSED_SUMMARY = (1, 0, 1, 6, 12, True)

# --- mandelbrot (the mandelbrot frontend lane's extension) -------------------

MANDELBROT_KEY = "synth/mandelbrot:mandelbrot"
MANDELBROT_PROFILE = "out-inout-admission-mandelbrot-v1"
MANDELBROT_SOURCE_PATH = "synth/mandelbrot/mandelbrot.glsl"
MANDELBROT_SOURCE = CORPUS / MANDELBROT_SOURCE_PATH
MANDELBROT_RAW_SHA256 = (
    "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615")
MANDELBROT_NORMALIZED_SHA256 = (
    "c062ee7852d0bfab69ca1e2ead6ad68d95dfa5fda9cff8232254b38b34c311a9")

MAX_ITER_VALUE = 500
MANDELBROT_OUT_PARAM_COUNT = 10
MANDELBROT_STORE_COUNT = 33
MANDELBROT_READ_COUNT = 2
MANDELBROT_CALL_COUNT = 5
MANDELBROT_LEDGER = 109
MANDELBROT_LIVE_SUMMARY = (0, 1, 0, 0, 0, True)
MANDELBROT_CLOSED_SUMMARY = (1, 0, 1, 500, 1500, True)
MANDELBROT_MECHANISM_CENSUS = (10, 5, 0, 0)
VORONOI_LOOP_SPAN = "65:5-80:6"

# The complete mechanism-A dict entry the module freezes for the phase-1
# integration slice (loop_proof.py's `_SOURCE_GLOBAL_LITERAL_INT_PROFILES`
# shape; singular "integer"/"reads" schema like the first six keys).
LIGHTLEAK_SEED_CONTRACT = {
    "raw": LIGHTLEAK_RAW_SHA256,
    "source": LIGHTLEAK_NORMALIZED_SHA256,
    "defines": (),
    "integer": ("POINT_COUNT", 2, "6", 6),
    "globals": (("TAU", 1, "float", "6.28318530717958647692"),
                ("POINT_COUNT", 2, "int", "6")),
    "reads": (("voronoiCell", 29, 65, 25, 65, 36),),
    "pre_functions": (
        "f7274c863e2c65b6aa80160bb4d42ea06cd26a3a68e8508e4fc13bc1350fb9a3"),
    "post_functions": (
        "72db52007f289ea5cff3ef10cc2b5245a7bac958f1067729fdfd75d82515bf0d"),
    "pre_whole": (
        "9fc72ea8a4105bdfd38e58240bd0a1e4ae448c1f6ff954a31fd7967edfd991ae"),
    "post_whole": (
        "8f78928336444c53847458cb908ae2c3eeda6ae93c0ab0090fbf87207846397a"),
    "interface": (
        "e8032324cde699ade81d0920220709d5087d576f3dbaee828da74f6152719ec0"),
}

# Quote-verified JavaScript provenance (the pinned snapshot's
# canonical-kernels.js, SHA-256 below -- byte-identical to the pin the
# cellRefract/kaleido/effects/parallax oracles froze).
LIGHTLEAK_JS_FACTORY = ("canonicalFactory77", 14827)
LIGHTLEAK_JS_REGISTRATION_LINE = 36257
LIGHTLEAK_JS_KERNELS_SHA256 = (
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe")
# The factory's toString() SHA-256, with the derivation method cross-validated
# by reproducing the frozen smoothEdge pin (test_typed_generator.py:13861).
LIGHTLEAK_JS_FACTORY_TO_STRING_SHA256 = (
    "9cf716594f8d25347737104d2ec0658276ac5a11405eb878706dc8f429c9055f")
SMOOTH_EDGE_FACTORY_TO_STRING_SHA256 = (
    "732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e")


def _analyzed_lightleak(raw: str | None = None, seeded: bool = True):
    """The analyzed lightLeak program; ``seeded`` attaches mechanism A's proof.

    The seed attachment is semantic.py's own call sequence
    (frontend/semantic.py:291-301): canonical attach, authenticate, re-attach
    with the seed. It is the tree the module will hold once the loop_proof
    dict key lands; the lightLeak lock is frozen over THIS state.
    """
    raw = (LIGHTLEAK_SOURCE.read_text(encoding="utf-8")
           if raw is None else raw)
    program = analyze_program(
        parse_program(raw, LIGHTLEAK_KEY, {}), LIGHTLEAK_KEY)
    if not seeded:
        return program
    module = _module()
    functions = attach_counted_loop_proofs(
        program.functions, LIGHTLEAK_KEY,
        source_global_bounds=_seed_tuple_lightleak(program))
    return dataclasses.replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


def _seed_tuple_lightleak(program: TypedProgram):
    """The mechanism-A seed, built exactly as semantic.py builds it."""
    point_count = next(item for item in program.declarations
                       if item.symbol.name == "POINT_COUNT")
    return ((point_count.symbol.id, POINT_COUNT_VALUE,
             "source-global-const-literal", point_count.symbol),)


def _analyzed_mandelbrot(raw: str | None = None, seeded: bool = True):
    """The analyzed mandelbrot program with mechanism A's seed attached.

    The out_inout lock is frozen over the SEED-ATTACHED tree (the state
    the authorities hold once the loop-proof dict key, the row and BOTH
    mandelbrot carriers land together -- the seed contract itself is owned
    by log_admission_profile, mandelbrot's other carrier).
    """
    raw = (MANDELBROT_SOURCE.read_text(encoding="utf-8")
           if raw is None else raw)
    program = analyze_program(
        parse_program(raw, MANDELBROT_KEY, {}), MANDELBROT_KEY)
    if not seeded:
        return program
    max_iter = next(item for item in program.declarations
                    if item.symbol.name == "MAX_ITER")
    functions = attach_counted_loop_proofs(
        program.functions, MANDELBROT_KEY,
        source_global_bounds=(
            (max_iter.symbol.id, MAX_ITER_VALUE,
             "source-global-const-literal", max_iter.symbol),))
    return dataclasses.replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


def _recount_lightleak(module, candidate, key=LIGHTLEAK_KEY):
    total, assigns = module._node_census(candidate)
    edges = module._call_graph(candidate)
    reachable, unreachable = module._reachability(candidate)
    proof = candidate.counted_loop_proof
    return {
        "total_nodes": total, "total_assigns": assigns,
        "call_edge_count": len(edges),
        "call_graph_sha256": module._sha(edges),
        "reachable": reachable, "unreachable": unreachable,
        "counted_loop_proof": (proof.loop_count, proof.unproved_loop_count,
                               proof.max_effective_depth,
                               proof.max_lexical_product,
                               proof.entrypoint_charge,
                               proof.call_graph_acyclic),
    }



def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _fn(program, name):
    return next(item for item in program.functions if item.name == name)


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


def _reinventory(module, candidate, key=KEY):
    return {"declaration_count": len(candidate.declarations),
            "declaration_inventory": module._declaration_inventory(candidate)}


def _refunctions(module, candidate, key=KEY):
    return {"function_inventory": module._function_inventory(candidate)}


def _authenticate(module, candidate, locks, profile=PROFILE, key=KEY):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_out_inout_admission(
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


def _parameter(program, identifier):
    for function in program.functions:
        for parameter in function.parameters:
            if parameter.id == identifier:
                return function, parameter
    raise AssertionError(f"no parameter {identifier}")


class OutInoutPublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual((LIGHTLEAK_KEY, "synth/julia:julia",
                          MANDELBROT_KEY, KEY), module.KEYS)
        self.assertEqual({LIGHTLEAK_KEY: LIGHTLEAK_PROFILE,
                          "synth/julia:julia": "out-inout-admission-julia-v1",
                          KEY: PROFILE,
                          MANDELBROT_KEY: MANDELBROT_PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({LIGHTLEAK_KEY, "synth/julia:julia",
                                    KEY, MANDELBROT_KEY}),
                         module.OUT_INOUT_ADMISSION_KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual(KEY, module.NEWTON_KEY)
        self.assertEqual(PROFILE, module.NEWTON_PROFILE)
        self.assertEqual(LIGHTLEAK_KEY, module.LIGHTLEAK_KEY)
        self.assertEqual(LIGHTLEAK_PROFILE, module.LIGHTLEAK_PROFILE)
        self.assertEqual(MANDELBROT_KEY, module.MANDELBROT_KEY)
        self.assertEqual(MANDELBROT_PROFILE, module.MANDELBROT_PROFILE)
        self.assertEqual(
            (("struct_declaration_profile",
              "struct-declaration-newton-v1"),),
            module.REQUIRED_COMPANION_PROFILES[KEY])
        self.assertEqual(
            (("log_admission_profile",
              "log-admission-mandelbrot-v1"),),
            module.REQUIRED_COMPANION_PROFILES[MANDELBROT_KEY])
        for name in ("KEYS", "PROFILES", "PREPARED_KEYS", "NEWTON_KEY",
                     "NEWTON_PROFILE", "ALLOWED_ROW_FIELDS",
                     "PREPARED_ROW_FIELDS", "REQUIRED_COMPANION_PROFILES",
                     "allowed_row_fields", "OutParameterRecord",
                     "DirectionContract", "direction_contract",
                     "authenticate_out_inout_admission",
                     "apply_out_inout_admission"):
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

    def test_the_row_field_guard_is_the_shared_landed_allowlist(self):
        """Both newton struct-lane modules freeze the SAME row contract --
        the two carriers are mutually required companions. (lightLeak's
        landed row is this module's alone; the newton entry is what the
        two struct-lane modules must keep identical.)"""
        module = _module()
        other = importlib.import_module(
            "tools.glslcpp.frontend.struct_declaration_profile")
        self.assertEqual(
            {"defines", "program_key", "struct_declaration_profile",
             "out_inout_admission_profile"},
            set(module.allowed_row_fields(KEY)))
        self.assertIn(KEY, other.ALLOWED_ROW_FIELDS)
        self.assertEqual(module.ALLOWED_ROW_FIELDS[KEY],
                         other.ALLOWED_ROW_FIELDS[KEY])
        expected_lightleak = frozenset({
            "defines", "program_key", "out_inout_admission_profile"})
        self.assertEqual(expected_lightleak,
                         module.ALLOWED_ROW_FIELDS[LIGHTLEAK_KEY])
        self.assertEqual(expected_lightleak,
                         module.allowed_row_fields(LIGHTLEAK_KEY))
        self.assertNotIn(LIGHTLEAK_KEY, module.PREPARED_ROW_FIELDS)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("synth/shape:shape")

    def test_live_row_carries_only_lightleaks_landed_field(self):
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        out_carriers = [row for row in spec["programs"]
                        if "out_inout_admission_profile" in row]
        self.assertEqual([LIGHTLEAK_KEY, "synth/julia:julia",
                          MANDELBROT_KEY, KEY],
                         [row["program_key"] for row in out_carriers])
        self.assertEqual([LIGHTLEAK_PROFILE,
                          "out-inout-admission-julia-v1",
                          MANDELBROT_PROFILE, PROFILE],
                         [row["out_inout_admission_profile"]
                          for row in out_carriers])

    def test_the_optional_proof_absent_set_is_exactly_the_typedprogram_fields(self):
        module = _module()
        carried = {
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_") and field.name.endswith("_proof")}
        self.assertEqual(carried, set(module._OPTIONAL_PROOF_FIELDS))

    def test_the_direction_contract_forbids_by_value_emission(self):
        """The §0.5 hazard, frozen as data: reference ABI, by-value
        forbidden, the emitter gate required, and the quote-verified JS
        materialization notes."""
        module = _module()
        contract = module.direction_contract(KEY)
        self.assertEqual("glsl::Vec2&", contract.native_abi)
        self.assertEqual("reference", contract.pass_mechanism)
        self.assertEqual("forbidden", contract.by_value_emission)
        self.assertTrue(contract.emitter_direction_gate_required)
        self.assertIn(".reduce((res,el,i)=>(res[i] = el, res), rr)",
                      contract.js_body_tail)
        self.assertEqual("df64_cmul.__out__ = [rr, ri]",
                         contract.js_out_stash)
        self.assertIn("[tr, ti] = df64_cmul.__out__",
                      contract.js_call_shape)
        self.assertIn("PooledFloat32Array([0, 0])",
                      contract.js_out_allocation)
        self.assertIn("caller-local", contract.out_argument_native_shape)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.direction_contract("synth/shape:shape")

    def test_every_failure_names_the_profile_not_a_module_global(self):
        module = _module()
        prefix = re.escape(f"{PROFILE}: ")
        program = _analyzed()
        for caller, arguments in (
                ("carrier", (program, RAW_SHA256, "wrong")),
                ("non-carrier", (_foreign(), _hash(FOREIGN_SOURCE), PROFILE)),
                ("row fields", ("synth/shape:shape",)),
                ("direction contract", ("synth/shape:shape",))):
            with self.subTest(site=caller), self.assertRaises(ValueError) as ctx:
                if caller == "carrier":
                    module.authenticate_out_inout_admission(*arguments)
                elif caller == "non-carrier":
                    module.authenticate_out_inout_admission(*arguments)
                elif caller == "row fields":
                    module.allowed_row_fields(*arguments)
                else:
                    module.direction_contract(*arguments)
            self.assertRegex(str(ctx.exception), f"^{prefix}")


class OutInoutAdmissionTests(unittest.TestCase):
    def test_authenticates_the_out_identity(self):
        module = _module()
        program = _analyzed()
        result = module.authenticate_out_inout_admission(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(result, tuple)
        self.assertEqual(2, len(result))
        self.assertEqual(4, len(result[0]))
        self.assertEqual(CALL_COUNT, len(result[1]))
        self.assertEqual(OUT_PARAM_IDS,
                         tuple(parameter.id for parameter in result[0]))
        self.assertIs(program, module.apply_out_inout_admission(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "out-inout-admission-newton-v2",
                        "struct-declaration-newton-v1", "inout-vec3-swap-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_out_inout_admission(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_the_sites_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_out_inout_admission(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "not an admitted out/inout admission carrier"):
                module.authenticate_out_inout_admission(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_non_carrier_error_names_all_four_admitted_parameters(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        message = str(raised.exception)
        self.assertIn("df64_cmul out vec2 rr at 98:52", message)
        self.assertIn("transformCoords_df64 out vec2 re_df at 108:38",
                      message)
        self.assertIn("sole admitted parameters", message)

    def test_the_foreign_fixture_really_carries_out_parameters(self):
        foreign = _foreign()
        directions = [(parameter.name, parameter.direction)
                      for function in foreign.functions
                      for parameter in function.parameters
                      if parameter.direction != "in"]
        self.assertEqual([("hi", "out"), ("lo", "out")], directions)

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_out_inout_admission(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_out_inout_admission(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("6.28318530718", "6.28318530719")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_an_unanalyzed_body_status_fails_the_normalized_lock(self):
        module = _module()
        candidate = dataclasses.replace(_analyzed(), body_status="parsed")
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

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
            module.authenticate_out_inout_admission(
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
            module.authenticate_out_inout_admission(
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
            module.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_out_inout_admission(
                        candidate, RAW_SHA256, PROFILE)

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
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


class OutInoutCensusTests(unittest.TestCase):
    """Every figure re-derived from the parsed program."""

    def test_the_four_out_parameters_and_their_owners(self):
        module = _module()
        program = _analyzed()
        census = list(module._out_parameter_census(program))
        self.assertEqual(4, len(census))
        measured = [(function.id, function.name, ordinal, parameter.id,
                     parameter.name, parameter.type.display(),
                     parameter.direction)
                    for function, ordinal, parameter in census]
        self.assertEqual(
            [(DF64_CMUL_ID, "df64_cmul", 4, 48, "rr", "vec2", "out"),
             (DF64_CMUL_ID, "df64_cmul", 5, 49, "ri", "vec2", "out"),
             (TRANSFORM_ID, "transformCoords_df64", 5, 55, "re_df", "vec2",
              "out"),
             (TRANSFORM_ID, "transformCoords_df64", 6, 56, "im_df", "vec2",
              "out")],
            measured)
        spans = [module._span(parameter) for _, _, parameter in census]
        self.assertEqual(["98:52-98:63", "98:65-98:76",
                          "108:38-108:52", "108:54-108:68"], spans)
        self.assertEqual(["98:1-101:2", "98:1-101:2",
                          "107:1-119:2", "107:1-119:2"],
                         [module._span(function)
                          for function, _, _ in census])

    def test_the_inout_census_is_frozen_empty(self):
        module = _module()
        program = _analyzed()
        self.assertEqual((), tuple(
            parameter.name for function in program.functions
            for parameter in function.parameters
            if parameter.direction == "inout"))
        self.assertTrue(module._inout_parameter_census_holds(program))
        source = pathlib.Path(_module().__file__).read_text(encoding="utf-8")
        self.assertNotIn('"inout"', source.split('"""')[2],
                         "the module freezes no inout record (the mechanism "
                         "has no inout carrier here)")

    def test_every_out_parameter_is_written_once_as_a_whole_lhs(self):
        module = _module()
        program = _analyzed()
        references = list(module._out_reference_census(program))
        self.assertEqual(4, len(references))
        stores = [entry for entry in references if entry[-1]]
        others = [entry for entry in references if not entry[-1]]
        self.assertEqual([], others, "the write-once census")
        for function, node, parent, chain, index, is_store in stores:
            self.assertTrue(is_store)
            self.assertEqual("assign", parent.kind)
            self.assertEqual("=", parent.operator)
            self.assertIs(node, parent.children[0])
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(parent, statement.expressions[0])
            self.assertEqual(1, len(chain), "a top-level statement")
        measured = sorted(
            (function.id, node.symbol_id, index)
            for function, node, _, _, index, _ in stores)
        self.assertEqual(
            [(DF64_CMUL_ID, 48, 0), (DF64_CMUL_ID, 49, 1),
             (TRANSFORM_ID, 55, 8), (TRANSFORM_ID, 56, 9)],
            measured)

    def test_the_three_calls_are_bare_void_statements_with_local_out_args(self):
        module = _module()
        program = _analyzed()
        calls = list(module._out_call_census(
            program, frozenset({"df64_cmul", "transformCoords_df64"})))
        self.assertEqual(CALL_COUNT, len(calls))
        expected = [
            ("transformCoords_df64", 7, (5, 6), (104, 105), "197:5-198:56"),
            ("df64_cmul", 6, (4, 5), (121, 122), "230:13-230:55"),
            ("df64_cmul", 6, (4, 5), (123, 124), "237:9-237:53"),
        ]
        for (function, node, chain, index), (callee, arity, ordinals,
                                             arg_ids, stmt_span) in (
                zip(calls, expected)):
            self.assertEqual("main", function.name)
            self.assertEqual(callee, node.callee)
            self.assertEqual(arity, len(node.children))
            self.assertEqual("void", node.type.display())
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(node, statement.expressions[0])
            self.assertEqual(stmt_span, module._span(statement))
            for ordinal, identifier in zip(ordinals, arg_ids):
                argument = node.children[ordinal]
                self.assertEqual("id", argument.kind)
                self.assertEqual(identifier, argument.symbol_id)
                self.assertEqual("local", argument.symbol.storage)
                self.assertEqual("vec2", argument.type.display())
                self.assertEqual("lvalue", argument.category)

    def test_two_of_the_three_calls_live_inside_loops(self):
        """Bare means sole-expression, NOT unnested: the df64_cmul calls
        sit inside main's loops (the j-loop call is five statements deep).
        The lock must not demand a top-level statement (that was the first
        implementation's bug, and this test is what keeps it fixed)."""
        module = _module()
        program = _analyzed()
        calls = list(module._out_call_census(
            program, frozenset({"df64_cmul", "transformCoords_df64"})))
        depths = [len(chain) for _, _, chain, _ in calls]
        self.assertEqual([1, 5, 3], depths)
        kinds = [tuple(s.kind for s in chain) for _, _, chain, _ in calls]
        self.assertEqual([("expr",),
                          ("for", "block", "for", "block", "expr"),
                          ("for", "block", "expr")], kinds)

    def test_the_direction_inventory_agrees_with_the_struct_module(self):
        module = _module()
        other = importlib.import_module(
            "tools.glslcpp.frontend.struct_declaration_profile")
        self.assertEqual(module._function_inventory(program := _analyzed()),
                         other._function_inventory(program))

    def test_ledger_helper_rejects_duplicate_and_short_visitation(self):
        module = _module()
        marker = object(), object()
        self.assertIsNone(module._check_ledger(list(marker), 2, "probe"))
        with self.assertRaisesRegex(
                ValueError, "probe visitation ledger mismatch"):
            module._check_ledger([marker[0], marker[0]], 2, "probe")

    def test_ledger_arithmetic_is_twenty_six(self):
        """4 out Symbols + 2 owning functions + 4 store targets + 4
        assigns + 3 calls + 6 out arguments + 3 statements."""
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        self.assertEqual(4 + 2 + 4 + 4 + 3 + 6 + 3, module._CONSUMED_LEDGER)

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(2, len(module.authenticate_out_inout_admission(
            program, RAW_SHA256, PROFILE)))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "out-inout-admission-newton visitation ledger "
                        "mismatch"):
                module.authenticate_out_inout_admission(
                    program, RAW_SHA256, PROFILE)


class OutInoutLockDeletionTests(unittest.TestCase):
    """Every lock proved load-bearing by DELETING THE LOCK."""

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            refunctions=False, reinventory=False):
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
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_out_inout_admission(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def _store_node(self, program, identifier):
        for function, node, parent, chain, index, is_store in (
                _module()._out_reference_census(program)):
            if node.symbol_id == identifier:
                return function, node, parent, chain, index
        raise AssertionError(f"no store for {identifier}")

    # --- coarse gate -------------------------------------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            2, len(scratch.authenticate_out_inout_admission(
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
        self.assertIn("call graph or reachability", survived)

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources,
                                    uses_derivatives=True))
        self.assertIsNone(self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch"))

    def test_call_graph_lock(self):
        def mutate(candidate):
            module = _module()
            host = _fn(candidate, "df64_to_float").body[0].expressions[0]
            # A non-out call (df64_to_float) lifted out of main's n-loop
            # (the nested statements included), so the out-call census
            # stays at three and only the call graph sees the new edge.
            planted = None
            for statement in _fn(candidate, "main").body:
                for node, _, _, _, _ in module._walk_statement(statement):
                    if (planted is None and node.kind == "call"
                            and node.callee == "df64_to_float"):
                        planted = dataclasses.replace(node)
                if planted is not None:
                    break
            self.assertIsNotNone(planted)
            object.__setattr__(host, "children", (*host.children, planted))
        self.assertIsNone(self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True))

    def test_declaration_inventory_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[0]
            symbol = dataclasses.replace(declaration.symbol, id=9001,
                                         name="planted")
            extra = dataclasses.replace(declaration, symbol=symbol)
            object.__setattr__(candidate, "declarations",
                               (*candidate.declarations, extra))
        self.assertIsNone(self._delete_and_compare(
            mutate, "_declaration_inventory_holds",
            "global declaration inventory mismatch"))

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "df64_add").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        self.assertIsNone(self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch"))

    # --- the out/inout census ----------------------------------------------

    def test_inout_census_lock_is_the_fail_closed_boundary(self):
        """A planted ``inout`` on a helper no other record names: the
        inout gate answers FIRST (by design), and deleting it hands the
        message to the out census's cardinality arm."""
        def mutate(candidate):
            function = _fn(candidate, "df64_add")
            object.__setattr__(function.parameters[0], "direction", "inout")
        survived = self._delete_and_compare(
            mutate, "_inout_parameter_census_holds",
            "inout parameter census mismatch", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter census mismatch: 5", survived)

    def test_out_parameter_census_lock_catches_a_direction_flip(self):
        """The design's own mutation list: an out param flipped to in."""
        def mutate(candidate):
            _, parameter = _parameter(candidate, 48)
            object.__setattr__(parameter, "direction", "in")
        survived = self._delete_and_compare(
            mutate, "_out_parameter_census_holds",
            "out parameter census mismatch: 3", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter identity mismatch", survived)

    def test_out_parameter_census_lock_catches_a_retyped_parameter(self):
        def mutate(candidate):
            _, parameter = _parameter(candidate, 48)
            # retype out vec2 -> float (the `zoom` local's type)
            object.__setattr__(parameter, "type",
                               _fn(candidate, "main").body[12].expressions[0]
                               .symbol.type)
            self.assertEqual("float", parameter.type.display())
        survived = self._delete_and_compare(
            mutate, "_out_parameter_census_holds",
            "out parameter census mismatch", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter identity mismatch", survived)

    def test_out_parameter_identity_lock(self):
        """The identity tier: the frozen Symbol hash tampered while every
        value still matches."""
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        records = locks[KEY]["out_parameters"]
        locks[KEY]["out_parameters"] = (
            records[0]._replace(parameter_sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out parameter identity mismatch")
        scratch = _scratch(module, "_out_parameter_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    def test_out_write_shape_lock_catches_a_compound_operator(self):
        def mutate(candidate):
            _, node, parent, _, _ = self._store_node(candidate, 48)
            object.__setattr__(parent, "operator", "+=")
        survived = self._delete_and_compare(
            mutate, "_out_write_shape_holds",
            "out parameter store shape mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter store identity mismatch", survived)

    def test_out_write_shape_lock_catches_a_partial_target(self):
        """`.x = ...` instead of the whole vec2: the target is no longer
        the bare parameter id, so it is not even classified a store."""
        def mutate(candidate):
            function, node, parent, chain, index = self._store_node(
                candidate, 48)
            swizzle = dataclasses.replace(
                node, kind="swizzle", member="x",
                type=_fn(candidate, "main").body[12].expressions[0].symbol
                .type)
            object.__setattr__(parent, "children", (swizzle,
                                                    parent.children[1]))
        survived = self._delete_and_compare(
            mutate, "_out_write_shape_holds",
            "out parameter store shape mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter store identity mismatch", survived)

    def test_out_write_only_lock_catches_a_planted_read(self):
        """A read of ``re_df`` planted in a NON-store statement of its
        owner: the four frozen stores are untouched, so only the
        write-once census can see it."""
        def mutate(candidate):
            module = _module()
            function, node, _, _, _ = self._store_node(candidate, 55)
            planted = dataclasses.replace(node)
            host = _fn(candidate, "transformCoords_df64").body[0]
            object.__setattr__(host, "expressions", (
                dataclasses.replace(
                    host.expressions[0],
                    children=(*host.expressions[0].children, planted)),))
        survived = self._delete_and_compare(
            mutate, "_out_write_only_holds",
            "out parameter write-once census mismatch", recount=True)
        self.assertIsNone(survived)

    def test_out_store_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        records = locks[KEY]["out_stores"]
        locks[KEY]["out_stores"] = (
            records[0]._replace(assign_sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out parameter store identity mismatch")
        scratch = _scratch(module, "_out_write_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    def test_out_call_census_lock_catches_a_swapped_argument(self):
        """The out argument replaced by another local: only the census's
        frozen argument identity can see it."""
        def mutate(candidate):
            module = _module()
            calls = list(module._out_call_census(
                candidate, frozenset({"df64_cmul"})))
            node = calls[0][1]
            other = calls[1][1]
            object.__setattr__(
                node, "children",
                (*node.children[:-2], other.children[-2],
                 other.children[-1]))
        survived = self._delete_and_compare(
            mutate, "_out_call_census_holds",
            "out call-site census mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("out call-site identity mismatch", survived)

    def test_out_call_identity_lock(self):
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        records = locks[KEY]["out_calls"]
        locks[KEY]["out_calls"] = (
            records[0]._replace(sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out call-site identity mismatch")
        scratch = _scratch(module, "_out_call_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE))

    def test_void_statement_shape_lock_catches_a_shared_statement(self):
        """The call sharing its statement with another (non-call)
        expression: no longer a BARE void-call statement (the wcSimplify
        class), and invisible to the call census, which counts calls."""
        def mutate(candidate):
            module = _module()
            calls = list(module._out_call_census(
                candidate, frozenset({"transformCoords_df64"})))
            _, node, chain, index = calls[0]
            statement = chain[-1]
            extra = dataclasses.replace(node.children[0])
            self.assertEqual("id", extra.kind)
            object.__setattr__(statement, "expressions",
                               (node, extra))
        survived = self._delete_and_compare(
            mutate, "_void_statement_shape_holds",
            "bare void-call statement shape mismatch", recount=True)
        self.assertIsNone(survived)

    def test_direction_contract_lock(self):
        """The §0.5 hazard lock: relaxing the contract to a by-value ABI
        must fail by name, and deleting the lock must let it through."""
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        locks[KEY]["direction_contract"] = locks[KEY][
            "direction_contract"]._replace(native_abi="glsl::Vec2",
                                           by_value_emission="allowed")
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch")
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE))


class LightLeakFrozenFactTests(unittest.TestCase):
    """Every lightLeak figure re-derived against the pinned corpus before
    freezing (the design's section 2.2, re-measured: measure, never
    transcribe)."""

    def test_pinned_source_bytes_and_hash(self):
        module = _module()
        raw = LIGHTLEAK_SOURCE.read_bytes()
        self.assertEqual(5047, len(raw))
        self.assertEqual(LIGHTLEAK_RAW_SHA256,
                         hashlib.sha256(raw).hexdigest())
        lock = module._LOCKS[LIGHTLEAK_KEY]
        self.assertEqual(5047, lock["raw_bytes"])
        self.assertEqual(LIGHTLEAK_RAW_SHA256, lock["raw_sha256"])
        self.assertEqual(4360, lock["normalized_bytes"])
        self.assertEqual(LIGHTLEAK_NORMALIZED_SHA256,
                         lock["normalized_sha256"])
        self.assertEqual(LIGHTLEAK_SOURCE_PATH, lock["source_path"])

    def test_rung1_closes_and_lands_the_live_out_carrier(self):
        program = analyze_program(
            parse_program(
                LIGHTLEAK_SOURCE.read_text(encoding="utf-8"),
                LIGHTLEAK_KEY, {}),
            LIGHTLEAK_KEY, source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "exact out/inout admission profile carrier required"):
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=LIGHTLEAK_RAW_SHA256,
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
        self.assertIsNone(generate_typed_slice.validate_capabilities(
            program, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=LIGHTLEAK_RAW_SHA256,
            source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
            out_inout_admission_profile=LIGHTLEAK_PROFILE))

    def test_seed_contract_freezes_the_loop_proof_dict_entry(self):
        module = _module()
        contract = module.counted_for_seed_contract(LIGHTLEAK_KEY)
        self.assertEqual(
            tuple(sorted(LIGHTLEAK_SEED_CONTRACT)),
            tuple(sorted(contract._asdict())))
        for name, value in LIGHTLEAK_SEED_CONTRACT.items():
            self.assertEqual(value, getattr(contract, name), name)

    def test_landed_registry_and_loop_proof_are_exactly_live(self):
        module = _module()
        contract = module.counted_for_seed_contract(LIGHTLEAK_KEY)
        self.assertIn(LIGHTLEAK_KEY, module.KEYS)
        self.assertEqual(LIGHTLEAK_PROFILE, module.PROFILES[LIGHTLEAK_KEY])
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual(
            contract._asdict(),
            loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES[
                LIGHTLEAK_KEY])

    def test_seed_contract_authenticates_through_live_loop_proof(self):
        """The frozen contract IS the live dict entry: the
        loop_proof, and the analyzed program pass both authentication and
        whole-program validation once the landed out/inout profile is supplied."""
        module = _module()
        contract = module.counted_for_seed_contract(LIGHTLEAK_KEY)
        program = _analyzed_lightleak(seeded=False)
        self.assertIn(LIGHTLEAK_KEY,
                      loop_proof_module.SOURCE_GLOBAL_LITERAL_INT_KEYS)
        seeds = loop_proof_module.authenticate_source_global_literal_int(
            key=LIGHTLEAK_KEY, raw_source=program.raw_source,
            source=program.source,
            preprocessor_defines=program.preprocessor_defines,
            declarations=program.declarations,
            functions=attach_counted_loop_proofs(
                program.functions, LIGHTLEAK_KEY),
            profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
        self.assertEqual(
            ((POINT_COUNT_SYMBOL_ID, POINT_COUNT_VALUE,
              "source-global-const-literal",
              next(item for item in program.declarations
                   if item.symbol.name == "POINT_COUNT").symbol),),
            tuple(seeds))
        # And the full analyze+validate path closes rung 1.
        post = analyze_program(
            parse_program(
                LIGHTLEAK_SOURCE.read_text(encoding="utf-8"),
                LIGHTLEAK_KEY, {}),
            LIGHTLEAK_KEY, source_global_literal_int_profile=(
                SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
        summary = post.counted_loop_proof
        self.assertEqual(LIGHTLEAK_CLOSED_SUMMARY, (
            summary.loop_count, summary.unproved_loop_count,
            summary.max_effective_depth, summary.max_lexical_product,
            summary.entrypoint_charge, summary.call_graph_acyclic))
        with mock.patch.object(
                generate_typed_slice, "SOURCE_GLOBAL_LITERAL_INT_KEYS",
                {LIGHTLEAK_KEY}
                | generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_KEYS):
            with self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "exact out/inout admission profile carrier required"):
                generate_typed_slice.validate_capabilities(
                    post, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=LIGHTLEAK_RAW_SHA256,
                    source_global_literal_int_profile=(
                        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
            self.assertIsNone(generate_typed_slice.validate_capabilities(
                post, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=LIGHTLEAK_RAW_SHA256,
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
                out_inout_admission_profile=LIGHTLEAK_PROFILE))

    def test_node_census_uses_the_house_convention(self):
        """576 nodes, initializers included (the design's 574 counted
        function bodies only -- the parallax-class divergence); 19 assigns."""
        module = _module()
        program = _analyzed_lightleak()
        total, assigns = module._node_census(program)
        self.assertEqual((576, 19), (total, assigns))
        self.assertEqual(
            (576, 19),
            (module._LOCKS[LIGHTLEAK_KEY]["total_nodes"],
             module._LOCKS[LIGHTLEAK_KEY]["total_assigns"]))

    def test_call_graph_is_six_deduplicated_edges(self):
        """The design's 'edges 8' counts call NODES (main calls voronoiCell
        twice, voronoiCell calls hash33 twice); the frozen edge SET has six
        members."""
        module = _module()
        program = _analyzed_lightleak()
        edges = module._call_graph(program)
        self.assertEqual(
            ((24, "hash31", 28, "pcg"),
             (25, "hash33", 28, "pcg"),
             (27, "main", 23, "centerMask"),
             (27, "main", 26, "luminance"),
             (27, "main", 29, "voronoiCell"),
             (29, "voronoiCell", 25, "hash33")),
            edges)
        self.assertEqual(6, module._LOCKS[LIGHTLEAK_KEY]["call_edge_count"])
        self.assertEqual(
            (23, 25, 26, 27, 28, 29),
            module._LOCKS[LIGHTLEAK_KEY]["reachable"])
        self.assertEqual(
            (24,), module._LOCKS[LIGHTLEAK_KEY]["unreachable"])

    def test_the_seed_read_is_the_loop_bound_alone(self):
        """POINT_COUNT has exactly ONE id-node read: the loop bound itself
        (unlike parallax's two reads); the reads lock freezes its span."""
        module = _module()
        self.assertEqual(
            (("voronoiCell", 29, 65, 25, 65, 36),),
            module._LOCKS[LIGHTLEAK_KEY]["reads"])

    def test_the_two_out_parameters_and_their_owner(self):
        module = _module()
        program = _analyzed_lightleak()
        census = list(module._out_parameter_census(program))
        self.assertEqual(2, len(census))
        measured = [(function.id, function.name, ordinal, parameter.id,
                     parameter.name, parameter.type.display(),
                     parameter.direction)
                    for function, ordinal, parameter in census]
        self.assertEqual(
            [(VORONOI_ID, "voronoiCell", 3, CELL_COLOR_ID, "cell_color",
              "vec3", "out"),
             (VORONOI_ID, "voronoiCell", 4, CELL_DIST_ID, "cell_dist",
              "float", "out")],
            measured)
        self.assertEqual(
            ["60:50-60:69", "60:71-60:90"],
            [module._span(parameter) for _, _, parameter in census])
        self.assertEqual(
            ["60:1-85:2", "60:1-85:2"],
            [module._span(function) for function, _, _ in census])

    def test_the_inout_census_is_frozen_empty_for_lightleak(self):
        module = _module()
        program = _analyzed_lightleak()
        self.assertEqual((), tuple(
            parameter.name for function in program.functions
            for parameter in function.parameters
            if parameter.direction == "inout"))
        self.assertTrue(module._inout_parameter_census_holds(program))

    def test_both_out_parameters_are_written_once_as_a_whole_lhs(self):
        module = _module()
        program = _analyzed_lightleak()
        references = list(module._out_reference_census(program))
        self.assertEqual(2, len(references))
        stores = [entry for entry in references if entry[-1]]
        others = [entry for entry in references if not entry[-1]]
        self.assertEqual([], others, "the write-once census")
        measured = sorted(
            (function.id, node.symbol_id, index)
            for function, node, _, _, index, _ in stores)
        self.assertEqual(
            [(VORONOI_ID, CELL_COLOR_ID, 5), (VORONOI_ID, CELL_DIST_ID, 6)],
            measured)
        for function, node, parent, chain, index, is_store in stores:
            self.assertTrue(is_store)
            self.assertEqual("assign", parent.kind)
            self.assertEqual("=", parent.operator)
            self.assertIs(node, parent.children[0])
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(parent, statement.expressions[0])
            self.assertEqual(1, len(chain), "a top-level statement")

    def test_the_two_calls_are_bare_void_statements_with_local_out_args(self):
        module = _module()
        program = _analyzed_lightleak()
        calls = list(module._out_call_census(
            program, frozenset({"voronoiCell"})))
        self.assertEqual(LIGHTLEAK_CALL_COUNT, len(calls))
        expected = [
            (5, (3, 4), (BASE_CELL_ID, BASE_DIST_ID), "114:5-114:54", 12),
            (5, (3, 4), (WARP_CELL_ID, WARP_DIST_ID), "125:5-125:61", 19),
        ]
        for (function, node, chain, index), (arity, ordinals, arg_ids,
                                             stmt_span, stmt_index) in (
                zip(calls, expected)):
            self.assertEqual("main", function.name)
            self.assertEqual("voronoiCell", node.callee)
            self.assertEqual(VORONOI_ID, node.signature_id)
            self.assertEqual(arity, len(node.children))
            self.assertEqual("void", node.type.display())
            self.assertEqual(stmt_index, index)
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(node, statement.expressions[0])
            self.assertEqual(stmt_span, module._span(statement))
            for ordinal, identifier in zip(ordinals, arg_ids):
                argument = node.children[ordinal]
                self.assertEqual("id", argument.kind)
                self.assertEqual(identifier, argument.symbol_id)
                self.assertEqual("local", argument.symbol.storage)
                self.assertEqual("lvalue", argument.category)

    def test_both_calls_are_top_level_statements(self):
        """lightLeak's two bare calls sit at ``main``'s top level (unlike
        newton, where two of three live inside loops): chains are exactly
        ('expr',) -- the shape the emitter's bare-call arm sees."""
        module = _module()
        program = _analyzed_lightleak()
        calls = list(module._out_call_census(
            program, frozenset({"voronoiCell"})))
        self.assertEqual([("expr",), ("expr",)],
                         [tuple(s.kind for s in chain)
                          for _, _, chain, _ in calls])

    def test_the_bare_call_census_is_exactly_the_two_out_calls(self):
        """Mechanism D's program-wide census: exactly two bare void-call
        statements exist anywhere, both ``voronoiCell`` -- no other function
        is ever called as a bare statement, so the emitter arm has exactly
        the out-call sites to admit."""
        module = _module()
        program = _analyzed_lightleak()
        self.assertEqual(
            (("main", "114:5-114:54", "voronoiCell"),
             ("main", "125:5-125:61", "voronoiCell")),
            module._bare_call_census(program))
        self.assertEqual(
            (2, 2, 1, 0),
            module._LOCKS[LIGHTLEAK_KEY]["mechanism_census"])

    def test_the_single_bit_operation_is_the_admitted_vector_form(self):
        """The design's '1 uvec3>>uint (already-admitted vector form)': the
        pcg shift at 25:10-25:18, uvec3 shifted by uint."""
        module = _module()
        program = _analyzed_lightleak()
        sites = []
        for function, _, item, _, _, _, _ in module._program_nodes(program):
            if (item.kind == "binary"
                    and item.operator in ("&", "|", "^", "<<", ">>")):
                sites.append((function.name, item.operator,
                              module._span(item),
                              item.children[0].type.display(),
                              item.children[1].type.display()))
        self.assertEqual(
            [("pcg", ">>", "25:10-25:18", "uvec3", "uint")], sites)

    def test_no_fixed_proof_carriers_ride_the_seeded_tree(self):
        program = _analyzed_lightleak()
        for field in _module()._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                self.assertIsNone(getattr(program, field, None))

    def test_the_loop_proof_shape_is_frozen(self):
        """trips 6, product 6, charge 12 -- the design's section 2.2 figures,
        re-derived on the seed-attached tree."""
        module = _module()
        program = _analyzed_lightleak()
        summary = program.counted_loop_proof
        self.assertEqual(
            LIGHTLEAK_CLOSED_SUMMARY,
            (summary.loop_count, summary.unproved_loop_count,
             summary.max_effective_depth, summary.max_lexical_product,
             summary.entrypoint_charge, summary.call_graph_acyclic))
        self.assertEqual(
            LIGHTLEAK_CLOSED_SUMMARY,
            module._LOCKS[LIGHTLEAK_KEY]["counted_loop_proof"])
        lock = module._LOCKS[LIGHTLEAK_KEY]["voronoi_loop"]
        self.assertEqual((VORONOI_ID, "voronoiCell"), lock["owner"])
        self.assertEqual(VORONOI_LOOP_SPAN, lock["span"])
        self.assertEqual(70, lock["induction_symbol_id"])
        self.assertEqual((0, 6, "<", "++",
                          "source-global-const-literal", 6, 1, 6, 12),
                         (lock["start"], lock["bound"], lock["comparison"],
                          lock["update"], lock["bound_kind"], lock["trips"],
                          lock["depth"], lock["product"], lock["charge"]))

    def test_the_javascript_authority_is_quote_frozen(self):
        """canonicalFactory77: the __out__ stash as the voronoiCell body
        tail, comma-expression destructuring at both call sites, the MIXED
        out-argument allocation (vec3 pooled array, float plain scalar), and
        the toString pin cross-validated against the frozen smoothEdge
        hash."""
        module = _module()
        self.assertEqual(("canonicalFactory77", 14827), module.LIGHTLEAK_JS_FACTORY)
        self.assertEqual(36257, module.LIGHTLEAK_JS_REGISTRATION_LINE)
        self.assertEqual(LIGHTLEAK_JS_KERNELS_SHA256,
                         module.LIGHTLEAK_JS_CANONICAL_KERNELS_SHA256)
        self.assertEqual(LIGHTLEAK_JS_FACTORY_TO_STRING_SHA256,
                         module.LIGHTLEAK_JS_FACTORY_TO_STRING_SHA256)
        self.assertEqual(SMOOTH_EDGE_FACTORY_TO_STRING_SHA256,
                         module.SMOOTH_EDGE_FACTORY_TO_STRING_SHA256)
        contract = module.direction_contract(LIGHTLEAK_KEY)
        self.assertEqual("voronoiCell.__out__ = [cell_color, cell_dist]",
                         contract.js_out_stash)
        self.assertEqual(
            "(voronoiCell(uv, seed_f, t, base_cell, base_dist), "
            "[base_cell, base_dist] = voronoiCell.__out__, "
            "voronoiCell.__return__)",
            contract.js_call_shape)
        self.assertIn("PooledFloat32Array([0, 0, 0])",
                      contract.js_out_allocation)
        self.assertIn("var base_dist = 0", contract.js_out_allocation)
        self.assertIn(
            ".reduce((res,el,i)=>(res[i] = el, res), cell_color)",
            contract.js_body_tail)
        self.assertIn("cell_dist = best_dist", contract.js_body_tail)


class LightLeakAdmissionTests(unittest.TestCase):
    def test_authenticates_the_out_identity(self):
        module = _module()
        program = _analyzed_lightleak()
        result = module.authenticate_out_inout_admission(
            program, LIGHTLEAK_RAW_SHA256, LIGHTLEAK_PROFILE)
        self.assertIsInstance(result, tuple)
        self.assertEqual(2, len(result))
        self.assertEqual(2, len(result[0]))
        self.assertEqual(LIGHTLEAK_CALL_COUNT, len(result[1]))
        self.assertEqual(
            (CELL_COLOR_ID, CELL_DIST_ID),
            tuple(parameter.id for parameter in result[0]))
        self.assertEqual(
            ("voronoiCell", "voronoiCell"),
            tuple(node.callee for node in result[1]))
        self.assertIs(program, module.apply_out_inout_admission(
            program, LIGHTLEAK_RAW_SHA256, LIGHTLEAK_PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed_lightleak()
        for carrier in (None, "", "wrong",
                        "out-inout-admission-lightleak-v2",
                        "out-inout-admission-newton-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_out_inout_admission(
                    program, LIGHTLEAK_RAW_SHA256, carrier)

    def test_a_wrong_caller_source_hash_is_rejected(self):
        module = _module()
        with self.assertRaisesRegex(
                ValueError, "exact caller source hash required"):
            module.authenticate_out_inout_admission(
                _analyzed_lightleak(), "0" * 64, LIGHTLEAK_PROFILE)

    def test_the_pre_seed_live_tree_is_refused_at_the_coarse_gate(self):
        """The lightLeak lock is frozen over the SEED-ATTACHED tree (the
        state semantic.py produces once the dict key lands): today's live
        pre-seed tree dies at the function fingerprint, by design."""
        module = _module()
        program = _analyzed_lightleak(seeded=False)
        with self.assertRaisesRegex(
                ValueError, "typed function fingerprint drift"):
            module.authenticate_out_inout_admission(
                program, LIGHTLEAK_RAW_SHA256, LIGHTLEAK_PROFILE)

    def test_foreign_key_error_names_both_carriers_sites(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_out_inout_admission(
            foreign, _hash(FOREIGN_SOURCE), None))
        with self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                foreign, _hash(FOREIGN_SOURCE), LIGHTLEAK_PROFILE)
        message = str(raised.exception)
        self.assertIn("not an admitted out/inout admission carrier", message)
        self.assertIn("df64_cmul out vec2 rr at 98:52", message)
        self.assertIn("voronoiCell out vec3 cell_color at 60:50", message)
        self.assertIn("out float cell_dist at 60:71", message)
        self.assertIn("sole admitted parameters", message)


class LightLeakLandedSurfaceTests(unittest.TestCase):
    def test_lightleak_is_landed_with_the_minimal_row(self):
        """The row carries only this module's profile beside the base fields:
        the loop-proof dict key needs no row field (carrier auto-supplied
        from the key), and lightLeak has no companion carrier."""
        module = _module()
        self.assertNotIn(LIGHTLEAK_KEY, module.PREPARED_KEYS)
        self.assertIn(LIGHTLEAK_KEY, module.KEYS)
        self.assertIn(LIGHTLEAK_KEY, module.PROFILES)
        self.assertNotIn(LIGHTLEAK_KEY, module.REQUIRED_COMPANION_PROFILES)
        expected = {
            "defines", "program_key", "out_inout_admission_profile"}
        self.assertEqual(expected, set(module.allowed_row_fields(LIGHTLEAK_KEY)))
        self.assertEqual(expected, set(module.ALLOWED_ROW_FIELDS[LIGHTLEAK_KEY]))
        self.assertNotIn(LIGHTLEAK_KEY, module.PREPARED_ROW_FIELDS)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("filter/parallax:parallax")

    def test_seed_contract_refuses_a_foreign_key(self):
        module = _module()
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.counted_for_seed_contract("test:foreign")

    def test_lightleak_direction_contract_forbids_by_value_emission(self):
        """The mixed-ABI hazard, frozen as data: per-parameter reference
        ABIs (vec3 and float), by-value forbidden, the emitter gate
        required, and the quote-verified JS materialization notes."""
        module = _module()
        contract = module.direction_contract(LIGHTLEAK_KEY)
        self.assertEqual(
            (("cell_color", "glsl::Vec3&"), ("cell_dist", "float&")),
            contract.parameter_abis)
        self.assertEqual("reference", contract.pass_mechanism)
        self.assertEqual("forbidden", contract.by_value_emission)
        self.assertTrue(contract.emitter_direction_gate_required)
        self.assertIn("caller-local", contract.out_argument_native_shape)

    def test_typed_authority_row_is_landed_in_the_live_210_slice(self):
        """The profile and loop proof are now wired into the typed row."""
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        programs = spec["programs"]
        self.assertEqual(210, len(programs))
        keys = [row["program_key"] for row in programs]
        self.assertEqual(71, keys.index(LIGHTLEAK_KEY))
        self.assertEqual(
            {"defines": {}, "program_key": LIGHTLEAK_KEY,
             "out_inout_admission_profile": LIGHTLEAK_PROFILE},
            programs[keys.index(LIGHTLEAK_KEY)])
        for name in ("generate_typed_slice.py", "emit_typed_cpp.py"):
            path = ROOT / "tools/glslcpp" / name
            self.assertIn("out_inout_admission", path.read_text(encoding="utf-8"), name)
        self.assertIn(
            LIGHTLEAK_KEY,
            loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES)

    def test_the_newton_direction_contract_loses_no_fields(self):
        """Adding lightLeak's per-parameter ABI field must leave newton's
        frozen contract untouched: the default is empty and every newton
        figure still holds."""
        module = _module()
        newton = module.direction_contract(KEY)
        self.assertEqual((), newton.parameter_abis)
        self.assertEqual("glsl::Vec2&", newton.native_abi)
        self.assertEqual("forbidden", newton.by_value_emission)


class LightLeakLockDeletionTests(unittest.TestCase):
    """Every lightLeak lock proved load-bearing by DELETING THE LOCK (the
    refreeze discipline: only the coarse hashes and the census fields the
    mutation unavoidably moves are refrozen)."""

    def _delete_and_compare(self, mutate, predicate, expected,
                             candidate=None, recount=False,
                             refunctions=False, reinventory=False,
                             relock=None):
        module = _module()
        candidate = _analyzed_lightleak() if candidate is None else candidate
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount_lightleak(module, candidate))
        if refunctions:
            overrides.update(
                {"function_inventory": module._function_inventory(candidate)})
        if reinventory:
            overrides.update({
                "declaration_count": len(candidate.declarations),
                "declaration_inventory":
                    module._declaration_inventory(candidate)})
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY, **overrides)
        _expect(self, module, candidate, locks, expected,
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_out_inout_admission(
                    candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                    LIGHTLEAK_PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    # --- coarse gate, per-key over the seeded tree -------------------------

    def test_caller_source_hash_lock(self):
        module = _module()
        scratch = _scratch(module, "_caller_source_hash_holds")
        self.assertEqual(
            2, len(scratch.authenticate_out_inout_admission(
                _analyzed_lightleak(), "0" * 64, LIGHTLEAK_PROFILE)),
            "with the lock deleted nothing may reject a lying caller")

    def test_functions_fingerprint_lock_fires_on_a_pre_seed_tree(self):
        module = _module()
        candidate = _analyzed_lightleak(seeded=False)
        locks = _relocked_partial(module, candidate, "functions",
                                  key=LIGHTLEAK_KEY)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(
                    ValueError, "typed function fingerprint drift"):
            module.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE)

    def test_call_graph_lock_carries_the_closed_summary(self):
        """lightLeak's counted-loop summary (the CLOSED (1, 0, 1, 6, 12,
        True)) rides the call-graph lock: a planted call edge -- recounted
        node census aside -- dies there. (A forged SUMMARY alone is caught
        earlier, by the rebuild lock.)"""
        module = _module()

        def mutate(candidate):
            planted = None
            for statement in _fn(candidate, "voronoiCell").body:
                for node, _, _, _, _ in module._walk_statement(statement):
                    if (planted is None and node.kind == "call"
                            and node.callee == "hash33"):
                        planted = dataclasses.replace(node)
                if planted is not None:
                    break
            self.assertIsNotNone(planted)
            host = _fn(candidate, "luminance").body[0].expressions[0]
            object.__setattr__(host, "children", (*host.children, planted))

        def relock(module, program, overrides):
            # Refreeze ONLY the node census: the call-graph fields and the
            # summary are the lock under test and keep their frozen
            # originals.
            total, assigns = module._node_census(program)
            overrides.update({"total_nodes": total,
                              "total_assigns": assigns})

        candidate = _analyzed_lightleak()
        self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch",
            candidate=candidate, relock=relock)

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "luminance").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        self.assertIsNone(self._delete_and_compare(
            mutate, "_node_census_holds",
            "whole-program node census mismatch"))

    # --- the out/inout census ------------------------------------------------

    def test_inout_census_lock_is_the_fail_closed_boundary(self):
        def mutate(candidate):
            function = _fn(candidate, "pcg")
            object.__setattr__(function.parameters[0], "direction", "inout")
        survived = self._delete_and_compare(
            mutate, "_inout_parameter_census_holds",
            "inout parameter census mismatch", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter census mismatch: 3", survived)

    def test_out_parameter_census_lock_catches_a_direction_flip(self):
        def mutate(candidate):
            _, parameter = _parameter(candidate, CELL_COLOR_ID)
            object.__setattr__(parameter, "direction", "in")
        survived = self._delete_and_compare(
            mutate, "_out_parameter_census_holds",
            "out parameter census mismatch: 1", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter identity mismatch", survived)

    def test_out_parameter_identity_lock(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        records = locks[LIGHTLEAK_KEY]["out_parameters"]
        locks[LIGHTLEAK_KEY]["out_parameters"] = (
            records[0]._replace(parameter_sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out parameter identity mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_out_parameter_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_out_write_shape_lock_catches_a_compound_operator(self):
        def mutate(candidate):
            module = _module()
            for function, node, parent, _, _, _ in (
                    module._out_reference_census(candidate)):
                if node.symbol_id == CELL_COLOR_ID:
                    object.__setattr__(parent, "operator", "+=")
                    return
            raise AssertionError("no cell_color store")
        survived = self._delete_and_compare(
            mutate, "_out_write_shape_holds",
            "out parameter store shape mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("out parameter store identity mismatch", survived)

    def test_out_write_only_lock_catches_a_planted_read(self):
        def mutate(candidate):
            module = _module()
            for function, node, _, _, _, _ in (
                    module._out_reference_census(candidate)):
                if node.symbol_id == CELL_COLOR_ID:
                    planted = dataclasses.replace(node)
                    host = _fn(candidate, "voronoiCell").body[0]
                    object.__setattr__(host, "expressions", (
                        dataclasses.replace(
                            host.expressions[0],
                            children=(*host.expressions[0].children,
                                      planted)),))
                    return
            raise AssertionError("no cell_color reference")
        survived = self._delete_and_compare(
            mutate, "_out_write_only_holds",
            "out parameter write-once census mismatch", recount=True)
        self.assertIsNone(survived)

    def test_out_store_identity_lock(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        records = locks[LIGHTLEAK_KEY]["out_stores"]
        locks[LIGHTLEAK_KEY]["out_stores"] = (
            records[0]._replace(assign_sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out parameter store identity mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_out_write_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_out_call_census_lock_catches_a_swapped_argument(self):
        def mutate(candidate):
            module = _module()
            calls = list(module._out_call_census(
                candidate, frozenset({"voronoiCell"})))
            node = calls[0][1]
            other = calls[1][1]
            object.__setattr__(
                node, "children",
                (*node.children[:-2], other.children[-2],
                 other.children[-1]))
        survived = self._delete_and_compare(
            mutate, "_out_call_census_holds",
            "out call-site census mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("out call-site identity mismatch", survived)

    def test_out_call_identity_lock(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        records = locks[LIGHTLEAK_KEY]["out_calls"]
        locks[LIGHTLEAK_KEY]["out_calls"] = (
            records[0]._replace(sha256="0" * 64), *records[1:])
        _expect(self, module, candidate, locks,
                "out call-site identity mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_out_call_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_void_statement_shape_lock_catches_a_shared_statement(self):
        def mutate(candidate):
            module = _module()
            calls = list(module._out_call_census(
                candidate, frozenset({"voronoiCell"})))
            _, node, chain, _ = calls[0]
            statement = chain[-1]
            extra = dataclasses.replace(node.children[0])
            self.assertEqual("id", extra.kind)
            object.__setattr__(statement, "expressions", (node, extra))
        survived = self._delete_and_compare(
            mutate, "_void_statement_shape_holds",
            "bare void-call statement shape mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("mechanism census mismatch", survived)

    def test_direction_contract_lock(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        locks[LIGHTLEAK_KEY]["direction_contract"] = locks[LIGHTLEAK_KEY][
            "direction_contract"]._replace(
                parameter_abis=(("cell_color", "glsl::Vec3"),
                                ("cell_dist", "float")))
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_direction_contract_lock_catches_a_wrong_native_abi(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        locks[LIGHTLEAK_KEY]["direction_contract"] = locks[LIGHTLEAK_KEY][
            "direction_contract"]._replace(
                native_abi="glsl::Vec3&, float&-tampered")
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_direction_contract_lock_catches_an_altered_shape(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        locks[LIGHTLEAK_KEY]["direction_contract"] = locks[LIGHTLEAK_KEY][
            "direction_contract"]._replace(
                out_argument_native_shape="caller-local altered shape")
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_direction_contract_lock_catches_an_appended_body_tail(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        contract = locks[LIGHTLEAK_KEY]["direction_contract"]
        locks[LIGHTLEAK_KEY]["direction_contract"] = contract._replace(
            js_body_tail=contract.js_body_tail + " tampered")
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_direction_contract_lock_catches_an_appended_allocation(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        contract = locks[LIGHTLEAK_KEY]["direction_contract"]
        locks[LIGHTLEAK_KEY]["direction_contract"] = contract._replace(
            js_out_allocation=contract.js_out_allocation + " tampered")
        _expect(self, module, candidate, locks,
                "out direction emission contract mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    # --- the counted-for seed side (mechanism A) -----------------------------

    def test_counted_rebuild_lock(self):
        """A tree whose summary CLAIMS the closure but whose functions are
        the proof-cleared originals: the rebuild lock catches the forgery."""
        module = _module()
        program = _analyzed_lightleak(seeded=False)
        closed = dataclasses.replace(
            program.counted_loop_proof, loop_count=1,
            unproved_loop_count=0, max_effective_depth=1,
            max_lexical_product=6, entrypoint_charge=12)
        candidate = dataclasses.replace(
            program, counted_loop_proof=closed)
        self.assertEqual(LIGHTLEAK_CLOSED_SUMMARY, (
            closed.loop_count, closed.unproved_loop_count,
            closed.max_effective_depth, closed.max_lexical_product,
            closed.entrypoint_charge, closed.call_graph_acyclic))
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        _expect(self, module, candidate, locks,
                "counted-for proof tree does not match the seed-derived "
                "rebuild", profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_counted_rebuild_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_out_inout_admission(
                    candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                    LIGHTLEAK_PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                "counted-for proof tree does not match the seed-derived "
                "rebuild", survived,
                "deleting _counted_rebuild_holds did not remove its message")

    def test_seed_declaration_value_lock(self):
        """The bound-value mutant: POINT_COUNT 6 -> 7. The helper attaches
        the FROZEN seed (bound 6), so every proof figure stays closed -- the
        declaration's own literal drift is invisible to the bound machinery
        and only the seed declaration's value lock can catch it."""
        raw = LIGHTLEAK_SOURCE.read_text(encoding="utf-8").replace(
            "const int POINT_COUNT = 6;", "const int POINT_COUNT = 7;")
        self.assertIn("POINT_COUNT = 7", raw)
        candidate = _analyzed_lightleak(raw=raw)
        module = _module()
        summary = candidate.counted_loop_proof
        self.assertEqual(LIGHTLEAK_CLOSED_SUMMARY, (
            summary.loop_count, summary.unproved_loop_count,
            summary.max_effective_depth, summary.max_lexical_product,
            summary.entrypoint_charge, summary.call_graph_acyclic))
        declaration = next(item for item in candidate.declarations
                           if item.symbol.name == "POINT_COUNT")
        self.assertEqual(7, declaration.initializer.literal_value)
        self._delete_and_compare(
            lambda program: None, "_seed_declaration_holds",
            "counted-for bound seed declaration value profile mismatch",
            candidate=candidate, recount=True)

    def test_seed_identity_lock(self):
        module = _module()
        candidate = _analyzed_lightleak()
        locks = _relocked(module, candidate, key=LIGHTLEAK_KEY)
        locks[LIGHTLEAK_KEY]["seed"]["declaration_sha256"] = "0" * 64
        _expect(self, module, candidate, locks,
                "counted-for bound seed declaration identity mismatch",
                profile=LIGHTLEAK_PROFILE, key=LIGHTLEAK_KEY)
        scratch = _scratch(module, "_seed_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            self.assertIsNotNone(scratch.authenticate_out_inout_admission(
                candidate, locks[LIGHTLEAK_KEY]["raw_sha256"],
                LIGHTLEAK_PROFILE))

    def test_globals_census_lock(self):
        raw = LIGHTLEAK_SOURCE.read_text(encoding="utf-8").replace(
            "const float TAU = 6.28318530717958647692;",
            "const float TAU = 6.28318530717958647693;")
        candidate = _analyzed_lightleak(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_globals_census_holds",
            "source global census mismatch", candidate=candidate)

    def test_seed_write_lock(self):
        module = _module()
        program = _analyzed_lightleak()
        self.assertTrue(module._no_seed_write_holds(
            program, {POINT_COUNT_SYMBOL_ID}))
        # pcg's first statement carries a plain assign (`v = v * ...`):
        # forging its target to the seed symbol is a synthetic write.
        writer = _fn(program, "pcg")
        statement = writer.body[0]
        assign = statement.expressions[0]
        self.assertEqual("assign", assign.kind)
        forged = dataclasses.replace(
            assign, children=(dataclasses.replace(
                assign.children[0], symbol_id=POINT_COUNT_SYMBOL_ID),
                assign.children[1]))
        object.__setattr__(statement, "expressions", (forged,))
        self.assertFalse(module._no_seed_write_holds(
            program, {POINT_COUNT_SYMBOL_ID}))
        scratch = _scratch(module, "_no_seed_write_holds")
        self.assertTrue(scratch._no_seed_write_holds(
            program, {POINT_COUNT_SYMBOL_ID}))

    def test_seed_reads_lock(self):
        # Replacing the bound with a bare literal removes exactly the one
        # POINT_COUNT read (the loop then proves via the literal, which the
        # recount absorbs; the read census is what must fire).
        raw = LIGHTLEAK_SOURCE.read_text(encoding="utf-8").replace(
            "i < POINT_COUNT", "i < 6")
        candidate = _analyzed_lightleak(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_seed_reads_holds",
            "counted-for bound seed read census mismatch",
            candidate=candidate, recount=True)

    def test_voronoi_loop_lock(self):
        # `>` is the same-length comparison-shape near-miss (the prover
        # admits only < and <=, so the loop stays unproved and the loop
        # profile lock fires on the missing proof; `!=` would be one char
        # longer and shift the bound read's span into the reads lock --
        # the parallax lesson).
        raw = LIGHTLEAK_SOURCE.read_text(encoding="utf-8").replace(
            "i < POINT_COUNT", "i > POINT_COUNT")
        candidate = _analyzed_lightleak(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_voronoi_loop_holds",
            "counted-for voronoi loop profile mismatch",
            candidate=candidate, recount=True)

    def test_mechanism_census_lock(self):
        # A tree mutation on the pcg shift's operator (`>>` -> `+`): node
        # count, spans and every out/inout record stay intact, only the
        # census's bit-op column moves (a length-changing SOURCE mutation
        # would shift every absolute offset and be absorbed by an identity
        # hash before this lock could fire).
        module = _module()

        def mutate(candidate):
            for function, _, item, _, _, _, _ in (
                    module._program_nodes(candidate)):
                if (function is not None and function.name == "pcg"
                        and item.kind == "binary" and item.operator == ">>"):
                    object.__setattr__(item, "operator", "+")
                    return
            raise AssertionError("no pcg shift node")

        candidate = _analyzed_lightleak()
        mutate(candidate)
        self.assertEqual((2, 2, 0, 0), module._mechanism_census(candidate))
        self._delete_and_compare(
            lambda program: None, "_mechanism_census_holds",
            "mechanism census mismatch", candidate=candidate)

    # --- the visitation ledger ------------------------------------------------

    def test_ledger_arithmetic_is_fifteen(self):
        """2 out Symbols + 1 owning function + 2 store targets + 2 assigns +
        2 calls + 4 out arguments + 2 statements."""
        module = _module()
        self.assertEqual(
            LIGHTLEAK_LEDGER,
            module._LOCKS[LIGHTLEAK_KEY]["consumed_ledger"])
        self.assertEqual(2 + 1 + 2 + 2 + 2 + 4 + 2, LIGHTLEAK_LEDGER)

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        program = _analyzed_lightleak()
        self.assertEqual(2, len(module.authenticate_out_inout_admission(
            program, LIGHTLEAK_RAW_SHA256, LIGHTLEAK_PROFILE)))
        for sabotage in (LIGHTLEAK_LEDGER - 1, LIGHTLEAK_LEDGER + 1):
            with self.subTest(sabotage=sabotage):
                locks = copy.deepcopy(module._LOCKS)
                locks[LIGHTLEAK_KEY]["consumed_ledger"] = sabotage
                with mock.patch.object(module, "_LOCKS", locks), \
                        self.assertRaisesRegex(
                            ValueError,
                            "out-inout-admission-lightleak visitation "
                            "ledger mismatch"):
                    module.authenticate_out_inout_admission(
                        program, LIGHTLEAK_RAW_SHA256, LIGHTLEAK_PROFILE)


class MandelbrotOutInoutTests(unittest.TestCase):
    """The mandelbrot frontend lane's per-key extension: the corrected
    design figures, the multi-store/read census, the mixed-type direction
    contract, and the mutation/deletion proofs for every new lock."""

    def test_the_frozen_source_path_names_the_authenticated_file(self):
        module = _module()
        lock = module._LOCKS[MANDELBROT_KEY]
        self.assertEqual("synth/mandelbrot/mandelbrot.glsl",
                         lock["source_path"])
        raw = (CORPUS / lock["source_path"]).read_bytes()
        self.assertEqual(14855, len(raw))
        self.assertEqual(MANDELBROT_RAW_SHA256,
                         hashlib.sha256(raw).hexdigest())
        self.assertEqual(MANDELBROT_RAW_SHA256, lock["raw_sha256"])
        self.assertEqual(MANDELBROT_NORMALIZED_SHA256,
                         lock["normalized_sha256"])
        # The lock is frozen over the SEED-ATTACHED tree: the coarse
        # function/whole digests are the closed figures, not the live
        # pre-seed ones.
        program = _analyzed_mandelbrot(seeded=False)
        self.assertEqual(MANDELBROT_LIVE_SUMMARY, tuple(
            (program.counted_loop_proof.loop_count,
             program.counted_loop_proof.unproved_loop_count,
             program.counted_loop_proof.max_effective_depth,
             program.counted_loop_proof.max_lexical_product,
             program.counted_loop_proof.entrypoint_charge,
             program.counted_loop_proof.call_graph_acyclic)))
        seeded = _analyzed_mandelbrot()
        self.assertEqual(MANDELBROT_CLOSED_SUMMARY, tuple(
            (seeded.counted_loop_proof.loop_count,
             seeded.counted_loop_proof.unproved_loop_count,
             seeded.counted_loop_proof.max_effective_depth,
             seeded.counted_loop_proof.max_lexical_product,
             seeded.counted_loop_proof.entrypoint_charge,
             seeded.counted_loop_proof.call_graph_acyclic)))
        self.assertEqual(module._sha(seeded.functions),
                         lock["functions_sha256"])
        self.assertEqual(module._whole(seeded), lock["whole_sha256"])
        self.assertEqual(module._interface(seeded),
                         lock["interface_sha256"])

    def test_the_design_figures_were_re_derived_and_corrected(self):
        """The design's §2.3 decomposition, corrected by measurement: TEN
        out parameters across THREE functions with mandelbrot_df64
        carrying SIX (not seven), and FIVE bare void calls (not three --
        main's own transformCoords_df64 and mandelbrot_df64 calls were
        missed); 999 house-census nodes and 31 deduplicated edges; and the
        interface SHA typo (d->c at position 26) fixed."""
        module = _module()
        lock = module._LOCKS[MANDELBROT_KEY]
        program = _analyzed_mandelbrot()
        census = list(module._out_parameter_census(program))
        self.assertEqual(MANDELBROT_OUT_PARAM_COUNT, len(census))
        owners = {}
        for function, _, parameter in census:
            owners.setdefault(function.name, []).append(parameter.name)
        self.assertEqual(
            {"getPOI": ["cX_df", "cY_df"],
             "mandelbrot_df64": ["smoothIter", "rawIter", "z_final",
                                 "dz_final", "stripeAcc", "trapMin"],
             "transformCoords_df64": ["re_df", "im_df"]},
            owners)
        self.assertEqual(3, len(owners))
        self.assertEqual(MANDELBROT_MECHANISM_CENSUS,
                         module._mechanism_census(program))
        self.assertEqual(MANDELBROT_MECHANISM_CENSUS,
                         lock["mechanism_census"])
        self.assertEqual(31, lock["call_edge_count"])
        self.assertEqual(999, lock["total_nodes"])
        self.assertNotEqual("d" * 1, lock["interface_sha256"][26])
        self.assertEqual("c", lock["interface_sha256"][26])

    def test_authenticates_the_seed_attached_identity(self):
        module = _module()
        program = _analyzed_mandelbrot()
        result = module.authenticate_out_inout_admission(
            program, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        self.assertEqual(2, len(result))
        self.assertEqual(MANDELBROT_OUT_PARAM_COUNT, len(result[0]))
        self.assertEqual(MANDELBROT_CALL_COUNT, len(result[1]))
        self.assertIs(program, module.apply_out_inout_admission(
            program, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE))

    def test_the_live_pre_seed_tree_is_refused_at_the_coarse_gate(self):
        """The lock demands the seed-attached state; the plain analyzed
        tree dies at the function fingerprint (the unproved loop moves the
        coarse digest)."""
        module = _module()
        program = _analyzed_mandelbrot(seeded=False)
        with self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                program, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        self.assertIn(
            f"{MANDELBROT_PROFILE}: typed function fingerprint drift",
            str(raised.exception))

    def test_the_store_census_is_multistore_and_nested(self):
        """33 stores: getPOI's nine arms (depths 3..10), mandelbrot_df64's
        cardioid arm (6), tail (5) and smoothing if/else (2), and
        transformCoords_df64's pair (top-level). Every store is the whole
        LHS of a plain `=` assign, the sole expression of its expr
        statement, at its frozen depth."""
        module = _module()
        program = _analyzed_mandelbrot()
        references = list(module._out_reference_census(program))
        stores = [entry for entry in references if entry[-1]]
        others = [entry for entry in references if not entry[-1]]
        self.assertEqual(MANDELBROT_STORE_COUNT, len(stores))
        self.assertEqual(MANDELBROT_READ_COUNT, len(others))
        records = module._LOCKS[MANDELBROT_KEY]["out_stores"]
        self.assertEqual(MANDELBROT_STORE_COUNT, len(records))
        depths = [record.depth for record in records]
        self.assertEqual([1, 3, 4, 5, 6, 7, 8, 9, 10],
                         sorted(set(depths)))
        for (function, node, parent, chain, index, is_store), record in (
                zip(stores, records)):
            self.assertTrue(is_store)
            self.assertEqual(record.parameter_id, node.symbol_id)
            self.assertEqual("=", parent.operator)
            self.assertIs(node, parent.children[0])
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(parent, statement.expressions[0])
            self.assertEqual(record.depth, len(chain))
            self.assertEqual(record.statement_sha256,
                            module._sha(statement))

    def test_the_read_census_is_exactly_the_two_z_final_reads(self):
        module = _module()
        program = _analyzed_mandelbrot()
        references = list(module._out_reference_census(program))
        others = [entry for entry in references if not entry[-1]]
        self.assertEqual(
            [(111, "mandelbrot_df64", 63, "z_final",
              "271:22-271:29", "builtin", "271:5-271:40"),
             (111, "mandelbrot_df64", 63, "z_final",
              "271:31-271:38", "builtin", "271:5-271:40")],
            [(function.id, function.name, node.symbol_id,
              node.symbol.name, module._span(node), parent.kind,
              module._span(chain[-1]))
             for function, node, parent, chain, index, _ in others])

    def test_the_five_calls_are_bare_with_trailing_out_arguments(self):
        module = _module()
        program = _analyzed_mandelbrot()
        callees = frozenset({"getPOI", "transformCoords_df64",
                             "mandelbrot_df64"})
        calls = list(module._out_call_census(program, callees))
        self.assertEqual(MANDELBROT_CALL_COUNT, len(calls))
        expected = [
            ("computeValueAt_df64", "transformCoords_df64",
             (120, 121), "320:5-320:78"),
            ("computeValueAt_df64", "mandelbrot_df64",
             (122, 123, 124, 125, 126, 127), "324:5-324:69"),
            ("main", "getPOI", (154, 155), "374:5-374:31"),
            ("main", "transformCoords_df64", (163, 164), "388:9-388:85"),
            ("main", "mandelbrot_df64",
             (157, 158, 159, 160, 161, 162), "389:9-389:102"),
        ]
        for (function, node, chain, index), (owner, callee, arg_ids,
                                             stmt_span) in zip(calls, expected):
            self.assertEqual(owner, function.name)
            self.assertEqual(callee, node.callee)
            self.assertEqual("void", node.type.display())
            statement = chain[-1]
            self.assertEqual("expr", statement.kind)
            self.assertEqual(1, len(statement.expressions))
            self.assertIs(node, statement.expressions[0])
            self.assertEqual(stmt_span, module._span(statement))
            trailing = node.children[len(node.children) - len(arg_ids):]
            for argument, identifier in zip(trailing, arg_ids):
                self.assertEqual("id", argument.kind)
                self.assertEqual(identifier, argument.symbol_id)
                self.assertEqual("local", argument.symbol.storage)
                self.assertEqual("lvalue", argument.category)

    def test_the_direction_contract_is_the_mixed_type_shape(self):
        module = _module()
        contract = module.direction_contract(MANDELBROT_KEY)
        self.assertEqual("reference", contract.pass_mechanism)
        self.assertEqual("forbidden", contract.by_value_emission)
        self.assertTrue(contract.emitter_direction_gate_required)
        self.assertEqual(
            (("cX_df", "glsl::Vec2&"), ("cY_df", "glsl::Vec2&"),
             ("smoothIter", "double&"), ("rawIter", "double&"),
             ("z_final", "glsl::Vec2&"), ("dz_final", "glsl::Vec2&"),
             ("stripeAcc", "double&"), ("trapMin", "double&"),
             ("re_df", "glsl::Vec2&"), ("im_df", "glsl::Vec2&")),
            contract.parameter_abis)
        self.assertIn("PooledFloat32Array([0, 0])",
                      contract.js_out_allocation)
        self.assertIn("var smoothI = 0, rawI = 0",
                      contract.js_out_allocation)
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.direction_contract("synth/shape:shape")

    def test_the_js_provenance_is_frozen(self):
        module = _module()
        self.assertEqual(("canonicalFactory252", 30151), module.JS_FACTORY
                         if hasattr(module, "JS_FACTORY")
                         else module.MANDELBROT_JS_FACTORY)
        self.assertEqual(36432, module.MANDELBROT_JS_REGISTRATION_LINE)
        self.assertEqual(module.LIGHTLEAK_JS_CANONICAL_KERNELS_SHA256,
                         module.MANDELBROT_JS_CANONICAL_KERNELS_SHA256)
        self.assertEqual(13231, module.MANDELBROT_JS_FACTORY_TOSTRING_BYTES)
        self.assertEqual(
            "27b87c62a87c73d76e5a1d2d6096cecaa6714aeba"
            "3f26f72a03698592918ee29",
            module.MANDELBROT_JS_FACTORY_TO_STRING_SHA256)
        self.assertIn("[smoothIter, rawIter, z_final, dz_final, stripeAcc, "
                      "trapMin]", module.MANDELBROT_JS_OUT_STASH)
        self.assertEqual("getPOI.__out__ = [cX_df, cY_df]",
                         module.MANDELBROT_JS_GETPOI_STASH)
        self.assertEqual("transformCoords_df64.__out__ = [re_df, im_df]",
                         module.MANDELBROT_JS_TRANSFORM_STASH)
        self.assertIn("cX_df[0] = -1.7548776865005493",
                      module.MANDELBROT_JS_GETPOI_LANE_WRITE)

    def test_the_row_contract_matches_the_log_module(self):
        module = _module()
        other = importlib.import_module(
            "tools.glslcpp.frontend.log_admission_profile")
        self.assertEqual(module.ALLOWED_ROW_FIELDS[MANDELBROT_KEY],
                         other.ALLOWED_ROW_FIELDS[MANDELBROT_KEY])
        self.assertEqual(
            frozenset({"defines", "program_key", "log_admission_profile",
                       "out_inout_admission_profile"}),
            module.allowed_row_fields(MANDELBROT_KEY))
        # mandelbrot's lock carries NO seed: the seed contract stays
        # single-sourced in the log module.
        self.assertNotIn("seed", module._LOCKS[MANDELBROT_KEY])
        with self.assertRaisesRegex(ValueError, "not an admitted counted"):
            module.counted_for_seed_contract(MANDELBROT_KEY)

    def test_foreign_key_with_profile_names_mandelbrot_sites(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                _foreign(), _hash(FOREIGN_SOURCE), MANDELBROT_PROFILE)
        message = str(raised.exception)
        self.assertIn("getPOI out vec2 cX_df/cY_df at 116:24/116:40", message)
        self.assertIn("mandelbrot_df64 out float smoothIter", message)
        self.assertIn("are the sole admitted parameters", message)

    def test_live_row_carries_only_lightleaks_landed_field(self):
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        out_carriers = [row for row in spec["programs"]
                        if "out_inout_admission_profile" in row]
        log_carriers = [row["program_key"] for row in spec["programs"]
                        if "log_admission_profile" in row]
        self.assertEqual([LIGHTLEAK_KEY, "synth/julia:julia",
                          MANDELBROT_KEY, KEY],
                         [row["program_key"] for row in out_carriers])
        self.assertEqual([LIGHTLEAK_PROFILE,
                          "out-inout-admission-julia-v1",
                          MANDELBROT_PROFILE, PROFILE],
                         [row["out_inout_admission_profile"]
                          for row in out_carriers])
        self.assertEqual([MANDELBROT_KEY], log_carriers)

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        program = _analyzed_mandelbrot()
        for sabotage in (MANDELBROT_LEDGER - 1, MANDELBROT_LEDGER + 1):
            with self.subTest(sabotage=sabotage):
                locks = copy.deepcopy(module._LOCKS)
                locks[MANDELBROT_KEY]["consumed_ledger"] = sabotage
                with mock.patch.object(module, "_LOCKS", locks), \
                        self.assertRaisesRegex(
                            ValueError,
                            "out-inout-admission-mandelbrot visitation "
                            "ledger mismatch"):
                    module.authenticate_out_inout_admission(
                        program, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)

    def _delete_and_compare_m(self, mutate, predicate, expected,
                              recount=False, refunctions=False):
        module = _module()
        candidate = _analyzed_mandelbrot()
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount_lightleak(
                module, candidate, key=MANDELBROT_KEY))
        if refunctions:
            overrides.update(
                {"function_inventory": module._function_inventory(
                    candidate)})
        locks = _relocked(module, candidate, key=MANDELBROT_KEY,
                          **overrides)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        message = str(raised.exception)
        for coarse in COARSE:
            self.assertNotIn(coarse, message)
        self.assertIn(expected, message)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_out_inout_admission(
                    candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(expected, survived,
                             f"deleting {predicate} did not remove its "
                             "message")
        return survived

    def test_out_parameter_census_lock_catches_a_direction_flip(self):
        def mutate(candidate):
            _, parameter = _parameter(candidate, 43)
            object.__setattr__(parameter, "direction", "in")
        survived = self._delete_and_compare_m(
            mutate, "_out_parameter_census_holds",
            "out parameter census mismatch: 9", recount=True,
            refunctions=True)
        self.assertIsNotNone(survived)

    def test_out_write_shape_lock_catches_a_depth_change(self):
        """A store lifted out of its arm: nesting depth is a frozen column
        (the design's multi-store shape), so a chain change dies here even
        with every span refrozen by the coarse relock."""
        def mutate(candidate):
            # Swap transformCoords_df64's two store statements: every span
            # and hash is refrozen by the coarse relock, but the frozen
            # statement indices (and the positional parameter binding)
            # move -- the depth/index columns are what die.
            transform = next(f for f in candidate.functions
                             if f.name == "transformCoords_df64")
            body = transform.body
            object.__setattr__(
                transform, "body",
                (*body[:6], body[7], body[6], *body[8:]))
        self._delete_and_compare_m(
            mutate, "_out_write_shape_holds",
            "out parameter store shape mismatch", recount=True)

    def test_out_write_only_lock_catches_a_planted_read(self):
        def mutate(candidate):
            # Re-point mandelbrot_df64's first df64_to_float operand
            # (the `c_re` read) at z_final: the census is owner-derived,
            # so the planted reference must live inside z_final's OWNER
            # to count -- a genuine third non-store reference.
            core = next(f for f in candidate.functions
                        if f.name == "mandelbrot_df64")
            planted = False
            for statement in core.body:
                stack = [e for e in statement.expressions]
                while stack:
                    node = stack.pop()
                    if (not planted and node.kind == "call"
                            and node.callee == "df64_to_float"
                            and node.children):
                        object.__setattr__(
                            node, "children", (dataclasses.replace(
                                node.children[0], symbol_id=63),))
                        planted = True
                    stack.extend(node.children)
            self.assertTrue(planted)
        self._delete_and_compare_m(
            mutate, "_out_write_only_holds",
            "out parameter write-once census mismatch: 3 non-store "
            "reference(s)")

    def test_out_read_census_lock_catches_a_swapped_read(self):
        """One of the two frozen z_final reads re-pointed at dz_final:
        the count still matches, so the read census's value tier fires."""
        def mutate(candidate):
            core = next(f for f in candidate.functions
                        if f.name == "mandelbrot_df64")
            for statement in core.body:
                stack = [expression
                         for expression in statement.expressions]
                while stack:
                    node = stack.pop()
                    if (node.kind == "id" and node.symbol_id == 63
                            and node.span.start_line == 271
                            and node.span.start_column == 22):
                        object.__setattr__(node, "symbol_id", 64)
                    stack.extend(node.children)
        survived = self._delete_and_compare_m(
            mutate, "_out_read_shape_holds",
            "out parameter read census mismatch")
        self.assertIsNotNone(survived)

    def test_out_read_identity_lock(self):
        module = _module()
        candidate = _analyzed_mandelbrot()
        locks = copy.deepcopy(module._LOCKS)
        records = locks[MANDELBROT_KEY]["out_reads"]
        locks[MANDELBROT_KEY]["out_reads"] = (
            records[0]._replace(node_sha256="0" * 64), *records[1:])
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        self.assertIn("out parameter read identity mismatch",
                      str(raised.exception))
        scratch = _scratch(module, "_out_read_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)

    def test_out_call_census_lock_catches_a_foreign_owner(self):
        module = _module()
        candidate = _analyzed_mandelbrot()
        locks = copy.deepcopy(module._LOCKS)
        records = locks[MANDELBROT_KEY]["out_calls"]
        locks[MANDELBROT_KEY]["out_calls"] = (
            records[0]._replace(owner="planted"), *records[1:])
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        self.assertIn("out call-site census mismatch: 5",
                      str(raised.exception))
        scratch = _scratch(module, "_out_call_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)

    def test_direction_contract_lock_refuses_a_tampered_abi(self):
        module = _module()
        candidate = _analyzed_mandelbrot()
        locks = copy.deepcopy(module._LOCKS)
        tampered = locks[MANDELBROT_KEY][
            "direction_contract"]._replace(pass_mechanism="value")
        locks[MANDELBROT_KEY]["direction_contract"] = tampered
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            module.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)
        self.assertIn("out direction emission contract mismatch",
                      str(raised.exception))
        scratch = _scratch(module, "_direction_contract_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_out_inout_admission(
                candidate, MANDELBROT_RAW_SHA256, MANDELBROT_PROFILE)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
