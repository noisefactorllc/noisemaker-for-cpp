"""Focused RED/GREEN proof for `synth/mandelbrot`'s four-rung counted-for
closure -- mechanism A (the seed contract) and mechanism E (the `log` sites).

Written before ``tools/glslcpp/frontend/log_admission_profile.py`` existed;
the first run of this file reported ``ModuleNotFoundError`` from ``_module``
for every test in it.

``synth/mandelbrot:mandelbrot`` is the counted-for bucket's third-cheapest
program (``counted-for-design.md`` §2.3 / §5, cost rank 3): measured **four
rungs from CLEAN at both authorities** behind only KNOWN mechanisms --

* rung 1 (mechanism A, the "const-global-literal" bound shape): the iteration
  loop ``for (int n = 0; n < MAX_ITER; n++)`` (normalized ``226:5-261:6``,
  owner ``mandelbrot_df64``) is bounded by the const global
  ``const int MAX_ITER = 500;``. The bound proof rides the EXISTING
  dict-keyed module -- a new key in ``loop_proof.py``'s
  ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES``. This module does NOT add that
  key; it freezes the complete dict-entry data as ``counted_for_seed_contract``
  (the parallax-lane pattern) so the integration slice has a one-move
  landing source. **The loop budget FITS the current caps**: trips 500,
  product 500, charge 1500 against 512/262144/262656 -- the loop-proof
  study's "needs budget increase" verdict is obsolete and must not be
  planned against.
* rung 2 (mechanism C): the validator rejects the first of the program's
  TEN ``out`` parameters at ``116:24`` (``getPOI``'s ``cX_df``); that
  mechanism's frontend home is ``out_inout_admission_profile`` (newton's
  module, extended per-key by this lane -- see
  ``test_out_inout_admission_profile.py``'s mandelbrot section).
* rung 3 (mechanism D): the emitter's bare-void-call gap fires at
  ``320:5``; the five call sites are frozen in the out/inout module's call
  census.
* rung 4 (mechanism E, THIS module's own mechanism): ``log`` is already
  VALIDATOR-approved (``APPROVED_CAPABILITIES`` carries it with the
  ``unary_float`` overload -- unlike ``tanh``, it is absent from no table),
  but the emitter has no ``log`` arm, so a ``log`` node falls through to the
  generic ``unsupported builtin log`` rejection. The **tanh precedent is
  frontend-side** (``curl_vector_math_profile`` authenticates the site and
  BOTH authorities consume node identity: the validator's
  ``authorized_curl_tanh`` and the emitter's ``proof.tanh_site`` arm), so
  this module freezes the three sites the same way -- as a frontend record
  handing the authorities the exact live nodes -- and the emitter-side arm
  is integration work that lands with the row.

The JavaScript authority (quote-verified against the pinned snapshot
``$RUN_ROOT/oracle/noisemaker-for-cpu``; ``canonical-kernels.js`` SHA-256
``66adc01c...`` byte-identical to the cellRefract/kaleido/effects/parallax
pins): ``canonicalFactory252`` destructures ``log`` from
``$runtime.stdlib``, and ``glsl-runtime.js:341`` is ``log:
unary(Math.log)`` -- **JS ``Math.log`` is the authority**, with the V8-vs-
libm routing risk the struct design flagged for log/log2 frozen here as
data (``MATH_LOG_ROUTING_NOTE``).

Figures re-derived this session that DIVERGE from the design's §2.3 prose
(recorded so nobody "fixes" them back):

* the design's "10 out params across 4 functions (... mandelbrot_df64 ×7)"
  decomposes wrong: the total is right but **mandelbrot_df64 carries SIX**
  out parameters (smoothIter/rawIter/stripeAcc/trapMin floats, z_final/
  dz_final vec2s) and the owners are **THREE** functions (getPOI ×2,
  mandelbrot_df64 ×6, transformCoords_df64 ×2);
* the design's "3 bare void-call statements" missed ``main``'s own
  ``transformCoords_df64`` (``388:9``) and ``mandelbrot_df64`` (``389:9``)
  calls: the true census is **FIVE** (the JS factory has five
  ``__out__``-destructuring call sites: 30427, 30431, 30463, 30472,
  30473), and mechanism D's "mandelbrot 3×" is really 5×;
* the design's interface SHA has a one-character transcription error:
  ``...ecbd6bb2d0a5...`` should be ``...ecbd6bb2c0a5...`` (the pre-whole
  fingerprint -- a strict superset of the interface tuple -- matches the
  design exactly, so the components agree and the design's prose string is
  the typo);
* the house node census (global initializers included) freezes **999**
  nodes where the design counted 994 (function bodies only; the five const
  initializers are the difference), and the deduplicated call-graph edge
  SET freezes **31** edges where the design counted 46 call NODES;
* the design's "log builtin in the df64 escape smoothing" places only two
  of the three sites: the third (``295:30``, ``outputDistance``'s
  ``log(mag)``) lives in the distance estimator.

The design's §8 open question -- "whether mandelbrot's ``iterations``
metadata maximum exceeds 500" -- is RESOLVED by measurement:
``src/effects/specs.js`` freezes ``iterations: i(500, 50, 2000)``, so the
``min(iterations, MAX_ITER)`` clamp's discriminating arm (iterations in
(500, 2000]) is reachable and an oracle case there is budgetable.

Corpus claim boundary: mandelbrot is NOT the only corpus ``log`` caller --
newton carries two sites (its own prepared lane's business) and julia
carries eight (adapter-only, ``check_corpus._ADAPTERS``); this module's
authenticatable set is mandelbrot alone.
"""

from __future__ import annotations

import ast
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
from tools.glslcpp.frontend import loop_proof as loop_proof_module
from tools.glslcpp.frontend.loop_proof import (
    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY, attach_counted_loop_proofs,
    clear_counted_loop_proofs, summarize_counted_loop_proofs)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine, TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.log_admission_profile"

KEY = "synth/mandelbrot:mandelbrot"
PROFILE = "log-admission-mandelbrot-v1"
SOURCE_PATH = "synth/mandelbrot/mandelbrot.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615"
NORMALIZED_SHA256 = (
    "c062ee7852d0bfab69ca1e2ead6ad68d95dfa5fda9cff8232254b38b34c311a9")

MAX_SYMBOL_ID = 24
MAX_VALUE = 500
MAX_SPAN = "31:1-31:26"
LOG_SPANS = ("273:24-273:33", "274:20-274:38", "295:30-295:38")
LOG_OWNERS = ("mandelbrot_df64", "mandelbrot_df64", "outputDistance")
LOOP_SPAN = "226:5-261:6"
LIVE_SUMMARY = (0, 1, 0, 0, 0, True)
CLOSED_SUMMARY = (1, 0, 1, 500, 1500, True)
LEDGER = 9
MECHANISM_CENSUS = (10, 5, 0, 0)

# The design §2.3 interface figure carried a one-character typo (d for c at
# position 26); the corrected measured value is frozen everywhere here.
INTERFACE_SHA256 = (
    "2f497a1fb59406d16decbd6bb2c0a5e4e7e5536774fa7ec56a34de12de657c43")
DESIGN_INTERFACE_TYPO = (
    "2f497a1fb59406d16decbd6bb2d0a5e4e7e5536774fa7ec56a34de12de657c43")

# The complete mechanism-A dict entry this module freezes for the integration
# slice (loop_proof.py's `_SOURCE_GLOBAL_LITERAL_INT_PROFILES` shape).
SEED_CONTRACT = {
    "raw": RAW_SHA256,
    "source": NORMALIZED_SHA256,
    "defines": (),
    "integer": ("MAX_ITER", 24, "500", 500),
    "globals": (("PI", 20, "float", "3.14159265359"),
                ("TAU", 21, "float", "6.28318530718"),
                ("BAILOUT", 22, "float", "256.0"),
                ("LOG2", 23, "float", "0.6931471805599453"),
                ("MAX_ITER", 24, "int", "500")),
    "reads": (("main", 110, 368, 35, 368, 43),
              ("mandelbrot_df64", 111, 226, 25, 226, 33)),
    "pre_functions":
        "5b24f4c4818b8ffee46ca02f752e4e19223ac97e677cccce310510af9a274a3d",
    "post_functions":
        "8240975403a5fe23b71b16799b7617dece132599ccfea69b24e717710f76f39b",
    "pre_whole":
        "d6a5840667d7293fa428a88eef00f8bcf4612a733958e738628c876ed210ebd3",
    "post_whole":
        "1ca045076337edb3bfcb5e618e0eb83f9633858eafb91176a2e713b4be28314e",
    "interface": INTERFACE_SHA256,
}

FOREIGN_SOURCE = (
    "uniform float time;\n"
    "out vec4 fragColor;\n"
    "void main() {\n"
    "    fragColor = vec4(log(time), 0.0, 0.0, 1.0);\n"
    "}\n"
)

# Every message the coarse gate can produce. A local lock that "fires" with
# one of these is not testing what its name claims.
COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("log admission profile module is absent")
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


def _seed_tuple(program: TypedProgram):
    """The mechanism-A seed, built exactly as semantic.py builds it -- with
    the FROZEN bound value (a value-mutant source must not self-supply)."""
    seed = next(item for item in program.declarations
                if item.symbol.name == "MAX_ITER")
    return ((seed.symbol.id, MAX_VALUE,
             "source-global-const-literal", seed.symbol),)


def _analyzed(raw: str | None = None, seeded: bool = True):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    program = analyze_program(parse_program(raw, KEY, {}), KEY)
    if not seeded:
        return program
    functions = attach_counted_loop_proofs(
        program.functions, KEY, source_global_bounds=_seed_tuple(program))
    return dataclasses.replace(
        program, functions=functions,
        counted_loop_proof=summarize_counted_loop_proofs(functions))


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _nodes(program):
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


def _expect(test, module, candidate, locks, expected, profile=PROFILE,
            key=KEY):
    with mock.patch.object(module, "_LOCKS", locks), \
            test.assertRaises(ValueError) as raised:
        module.authenticate_log_admission(
            candidate, locks[key]["raw_sha256"], profile)
    message = str(raised.exception)
    test.assertIn(f"{profile}: ", message)
    test.assertIn(expected, message)
    for coarse in COARSE:
        test.assertNotIn(coarse, message)
    return message


_COARSE_ORDER = ("raw", "normalized", "functions", "whole", "interface")


def _coarse_values(module, candidate):
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    cleared = module.clear_counted_loop_proofs(candidate.functions)
    return {
        "raw": {"raw_bytes": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest()},
        "normalized": {
            "normalized_bytes": len(normalized),
            "normalized_sha256": hashlib.sha256(normalized).hexdigest()},
        "functions": {"functions_sha256": module._sha(cleared)},
        "whole": {"whole_sha256": module._whole_cleared(candidate)},
        "interface": {"interface_sha256": module._interface(candidate)},
    }


def _recount(module, candidate, key=KEY):
    total, assigns = module._node_census(candidate)
    edges = module._call_graph(candidate)
    reachable, unreachable = module._reachability(candidate)
    proof = candidate.counted_loop_proof
    return {
        "total_nodes": total, "total_assigns": assigns,
        "call_edge_count": len(edges), "call_graph_sha256": module._sha(edges),
        "reachable": reachable, "unreachable": unreachable,
        "counted_loop_proof": (proof.loop_count, proof.unproved_loop_count,
                               proof.max_effective_depth,
                               proof.max_lexical_product,
                               proof.entrypoint_charge,
                               proof.call_graph_acyclic),
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
    for name in _COARSE_ORDER[:_COARSE_ORDER.index(upto)]:
        locks[key].update(values[name])
    return locks


def _literal_parts(node) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        found: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                found.append(value.value)
        return found
    return []


def _guard_messages(module) -> list[str]:
    tree = ast.parse(
        pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"fail", "_profile_fail"} and node.args):
            continue
        for part in _literal_parts(node.args[-1]):
            if len(part.strip()) >= 10:
                found.append(part)
    return sorted(set(found))


def _call_argument_strings(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for argument in (*node.args, *(item.value for item in node.keywords)):
            for item in ast.walk(argument):
                found.extend(_literal_parts(item))
    return found


class ModulePresenceTests(unittest.TestCase):
    def test_module_imports(self):
        module = _module()
        self.assertEqual(KEY, module.MANDELBROT_KEY)
        self.assertEqual(PROFILE, module.MANDELBROT_PROFILE)


class MandelbrotFrozenFactTests(unittest.TestCase):
    """Every figure re-derived against the pinned corpus before freezing."""

    def test_pinned_source_bytes_and_hash(self):
        module = _module()
        raw = SOURCE.read_bytes()
        self.assertEqual(14855, len(raw))
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        lock = module._LOCKS[KEY]
        self.assertEqual(14855, lock["raw_bytes"])
        self.assertEqual(RAW_SHA256, lock["raw_sha256"])
        self.assertEqual("sources/synth/mandelbrot/mandelbrot.glsl",
                         lock["source_path"])

    def test_live_analysis_matches_frozen_identity(self):
        module = _module()
        program = _analyzed(seeded=False)
        normalized = program.source.encode("utf-8")
        self.assertEqual(10414, len(normalized))
        self.assertEqual(NORMALIZED_SHA256,
                         hashlib.sha256(normalized).hexdigest())
        self.assertEqual((), tuple((item.name, item.kind, item.canonical_value)
                                   for item in program.preprocessor_defines))
        self.assertEqual(
            (("resolution", "tileOffset", "fullResolution", "time", "poi",
              "outputMode", "iterations", "centerHiX", "centerHiY",
              "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "invert",
              "stripeFreq", "trapShape", "lightAngle", "rotation"),
             (), ("fragColor",), False, False),
            (program.resources.uniforms, program.resources.samplers,
             program.resources.outputs, program.resources.uses_texture,
             program.resources.uses_derivatives))
        summary = program.counted_loop_proof
        self.assertEqual(LIVE_SUMMARY,
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))

    def test_the_design_interface_figure_was_a_one_character_typo(self):
        """The design's §2.3 interface SHA (d at position 26) does not
        reproduce; the measured value (c) is what every frozen record
        carries. pre_whole -- a strict superset of the interface tuple --
        matches the design exactly, so the components agree and the prose
        string is the transcription error."""
        module = _module()
        self.assertEqual(INTERFACE_SHA256, module._LOCKS[KEY][
            "interface_sha256"])
        self.assertEqual(INTERFACE_SHA256, SEED_CONTRACT["interface"])
        self.assertEqual("c", INTERFACE_SHA256[26])
        self.assertEqual("d", DESIGN_INTERFACE_TYPO[26])
        self.assertEqual(INTERFACE_SHA256[:26], DESIGN_INTERFACE_TYPO[:26])
        self.assertEqual(INTERFACE_SHA256[27:], DESIGN_INTERFACE_TYPO[27:])

    def test_rung0_rejects_at_the_iteration_loop_today(self):
        program = _analyzed(seeded=False)
        with self.assertRaises(generate_typed_slice.GeneratorError) as raised:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        self.assertEqual(
            f"{KEY}: exact Mandelbrot sequential-dz profile carrier required",
            str(raised.exception))

    def test_seed_contract_freezes_the_loop_proof_dict_entry(self):
        module = _module()
        contract = module.counted_for_seed_contract(KEY)
        self.assertEqual(
            tuple(sorted(SEED_CONTRACT)), tuple(sorted(contract._asdict())))
        for name, value in SEED_CONTRACT.items():
            self.assertEqual(value, getattr(contract, name), name)

    def test_seed_contract_authenticates_through_live_loop_proof(self):
        """The frozen contract IS the dict entry: patched into a scratch
        loop_proof, the analyzed program passes both authenticate and the
        whole-program validator, and the next gate is the out parameter at
        116:24 (mechanism C, the out/inout module's)."""
        module = _module()
        contract = module.counted_for_seed_contract(KEY)
        entry = contract._asdict()
        program = _analyzed(seeded=False)
        cleared = clear_counted_loop_proofs(program.functions)
        pre = attach_counted_loop_proofs(cleared, KEY)
        with mock.patch.dict(loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES,
                             {KEY: entry}), \
                mock.patch.object(
                    loop_proof_module, "SOURCE_GLOBAL_LITERAL_INT_KEYS",
                    frozenset(
                        loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES)):
            self.assertIn(KEY, loop_proof_module.SOURCE_GLOBAL_LITERAL_INT_KEYS)
            seeds = loop_proof_module.authenticate_source_global_literal_int(
                key=KEY, raw_source=program.raw_source,
                source=program.source,
                preprocessor_defines=program.preprocessor_defines,
                declarations=program.declarations, functions=pre,
                profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
            self.assertEqual(((MAX_SYMBOL_ID, MAX_VALUE,
                               "source-global-const-literal",
                               program.declarations[23].symbol),),
                             tuple(seeds))
            post = analyze_program(
                parse_program(SOURCE.read_text(encoding="utf-8"), KEY, {}),
                KEY, source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
            summary = post.counted_loop_proof
            self.assertEqual(CLOSED_SUMMARY,
                             (summary.loop_count, summary.unproved_loop_count,
                              summary.max_effective_depth,
                              summary.max_lexical_product,
                              summary.entrypoint_charge,
                              summary.call_graph_acyclic))
            with mock.patch.object(
                    generate_typed_slice, "SOURCE_GLOBAL_LITERAL_INT_KEYS",
                    {KEY} | generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_KEYS):
                self.assertIsNone(
                    generate_typed_slice.validate_capabilities(
                        post, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=RAW_SHA256,
                        source_global_literal_int_profile=(
                            SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
                        mandelbrot_sequential_dz_assignment_profile=(
                            "mandelbrot-sequential-dz-assignment-v1"),
                        log_admission_profile=PROFILE,
                        out_inout_admission_profile=(
                            "out-inout-admission-mandelbrot-v1")))
        self.assertIn(KEY,
                      loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES)

    def test_the_loop_budget_fits_the_current_caps(self):
        """trips 500 <= 512, product 500 <= 262144, charge 1500 <= 262656:
        the loop-proof study's 'needs budget increase' verdict is obsolete."""
        module = _module()
        loop = module._LOCKS[KEY]["iteration_loop"]
        self.assertEqual(500, loop["trips"])
        self.assertEqual(500, loop["product"])
        self.assertEqual(1500, loop["charge"])
        self.assertLessEqual(loop["trips"],
                             loop_proof_module.COUNTED_FOR_V1_MAX_TRIP_COUNT)
        self.assertLessEqual(
            loop["product"],
            loop_proof_module.COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT)
        self.assertLessEqual(
            loop["charge"],
            loop_proof_module.COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE)

    def test_node_census_uses_the_house_convention(self):
        """999 nodes, initializers included (the design's 994 counted
        function bodies only); 51 assigns."""
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual((999, 51), (total, assigns))
        self.assertEqual((999, 51),
                         (module._LOCKS[KEY]["total_nodes"],
                          module._LOCKS[KEY]["total_assigns"]))

    def test_call_graph_is_thirtyone_deduplicated_edges(self):
        """The design's 'call edges 46' counts call NODES; the frozen
        deduplicated edge SET has 31 members and every function is
        reachable."""
        module = _module()
        program = _analyzed()
        edges = module._call_graph(program)
        self.assertEqual(31, len(edges))
        self.assertEqual(31, module._LOCKS[KEY]["call_edge_count"])
        reachable, unreachable = module._reachability(program)
        self.assertEqual(24, len(reachable))
        self.assertEqual((), unreachable)

    def test_max_iter_reads_freeze_both_id_nodes(self):
        """The design's 'raw 381' cites the min(iterations, MAX_ITER) site;
        the frozen reads are the normalized id nodes -- the min() read in
        main (368:35) AND the loop bound in mandelbrot_df64 (226:25), the
        counted-for owner itself (unlike parallax, not every read is in
        main)."""
        module = _module()
        self.assertEqual(
            (("main", 110, 368, 35, 368, 43),
             ("mandelbrot_df64", 111, 226, 25, 226, 33)),
            module._LOCKS[KEY]["reads"])


class AdmissionGreenTests(unittest.TestCase):
    def test_post_seed_tree_authenticates_and_returns_all_three_sites(self):
        module = _module()
        program = _analyzed()
        proof = module.authenticate_log_admission(
            program, RAW_SHA256, PROFILE)
        self.assertEqual(3, len(proof.sites))
        self.assertEqual(LOG_OWNERS,
                         tuple(site.owner_name for site in proof.sites))
        self.assertEqual(LOG_SPANS, tuple(site.span for site in proof.sites))
        tree_nodes = {id(item) for item in _nodes(program)}
        for site in proof.sites:
            for live in (site.node, site.argument):
                self.assertIn(id(live), tree_nodes)
        self.assertEqual(LEDGER, len(proof.consumed_objects))
        self.assertEqual(len(proof.consumed_objects),
                         len({id(item) for item in proof.consumed_objects}))

    def test_apply_is_the_identity(self):
        module = _module()
        program = _analyzed()
        self.assertIs(program, module.apply_log_admission(
            program, RAW_SHA256, PROFILE))

    def test_live_pre_seed_tree_is_refused_at_the_summary_lock(self):
        """Rung 1 is not closed on a plain analyzed tree: the module demands
        the seed-attached state the authorities will actually hold."""
        module = _module()
        program = _analyzed(seeded=False)
        with self.assertRaises(ValueError) as raised:
            module.authenticate_log_admission(program, RAW_SHA256, PROFILE)
        self.assertIn(f"{PROFILE}: counted-for closure summary mismatch",
                      str(raised.exception))

    def test_foreign_key_without_profile_returns_none(self):
        module = _module()
        self.assertIsNone(module.authenticate_log_admission(
            _foreign(), _hash(FOREIGN_SOURCE), None))

    def test_foreign_key_with_profile_names_the_three_sites(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_log_admission(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        self.assertEqual(
            f"{PROFILE}: program key is not an admitted log admission "
            f"carrier; {KEY} 273:24, 274:20 and 295:30 are the sole "
            "admitted log sites",
            str(raised.exception))

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        program = _analyzed()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_log_admission(
                program, RAW_SHA256, "log-admission-mandelbrot-v2")
        self.assertIn(f"{PROFILE}: exact profile carrier required",
                      str(raised.exception))

    def test_mechanism_census_is_the_measured_decomposition(self):
        """10 out params, FIVE bare void calls (the design's '3' missed
        main's own two), 0 bit-ops, 0 index expressions."""
        module = _module()
        program = _analyzed()
        self.assertEqual(MECHANISM_CENSUS, module._mechanism_census(program))
        self.assertEqual(MECHANISM_CENSUS,
                         module._LOCKS[KEY]["mechanism_census"])

    def test_log_family_census_freezes_the_boundaries(self):
        """log2/exp/exp2/tanh are all zero; pow -- already approved -- has
        exactly the two getEffectiveZoom sites."""
        module = _module()
        program = _analyzed()
        self.assertEqual(
            ((105, "getEffectiveZoom", "357:16-357:47", 2),
             (105, "getEffectiveZoom", "359:12-359:31", 2)),
            module._pow_census(program))
        self.assertEqual((0, 0, 0, 0), module._zero_family_census(program))


class PreparedDisciplineTests(unittest.TestCase):
    def test_mandelbrot_is_landed(self):
        module = _module()
        self.assertEqual((KEY,), module.KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual({KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({KEY}), module.LOG_ADMISSION_KEYS)

    def test_landed_row_fields_are_frozen(self):
        module = _module()
        self.assertEqual(
            frozenset({"defines", "program_key", "log_admission_profile",
                       "out_inout_admission_profile"}),
            module.allowed_row_fields(KEY))
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)
        self.assertIn(KEY, module.ALLOWED_ROW_FIELDS)

    def test_the_row_contract_matches_the_out_inout_module(self):
        """The two mandelbrot carriers freeze the SAME row contract and are
        mutually required companions (the newton two-module pattern)."""
        module = _module()
        other = importlib.import_module(
            "tools.glslcpp.frontend.out_inout_admission_profile")
        self.assertEqual(module.ALLOWED_ROW_FIELDS[KEY],
                         other.ALLOWED_ROW_FIELDS[KEY])
        self.assertEqual(
            (("out_inout_admission_profile", "out-inout-admission-mandelbrot-v1"),),
            module.REQUIRED_COMPANION_PROFILES[KEY])
        self.assertEqual(
            (("log_admission_profile", PROFILE),),
            other.REQUIRED_COMPANION_PROFILES[KEY])

    def test_allowed_row_fields_rejects_foreign_keys(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.allowed_row_fields("test:foreign")
        self.assertIn(
            f"{PROFILE}: test:foreign is not an admitted log admission "
            "carrier",
            str(raised.exception))

    def test_both_authorities_reference_the_landed_module(self):
        for name in ("generate_typed_slice.py", "emit_typed_cpp.py"):
            path = ROOT / "tools/glslcpp" / name
            self.assertIn("log_admission", path.read_text(encoding="utf-8"),
                             name)

    def test_no_capability_or_type_vocabulary_growth(self):
        _module()
        frozen = {
            "capabilities": (
                44, generate_typed_slice.APPROVED_CAPABILITIES,
                "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea"),
            "types": (
                17, generate_typed_slice.APPROVED_TYPES,
                "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7"),
        }
        for name, (size, value, digest) in frozen.items():
            with self.subTest(vocabulary=name):
                self.assertEqual(size, len(value))
                self.assertEqual(
                    digest,
                    hashlib.sha256(repr(value).encode()).hexdigest())

    def test_log_is_analyzer_known_but_absent_from_both_vocabularies(self):
        """Exactly tanh's shape: the analyzer types `log` (body_semantic's
        unary_float overload) but the validator's APPROVED_CAPABILITIES and
        its derived _BUILTINS both reject it, and the emitter has no arm --
        so BOTH authority arms are integration work and the frozen
        44-entry vocabulary does not move."""
        from tools.glslcpp.frontend import body_semantic
        self.assertIn("log", body_semantic._BUILTIN_FAMILIES)
        self.assertEqual(("unary_float",),
                         body_semantic._BUILTIN_FAMILIES["log"])
        self.assertNotIn("log", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("log", generate_typed_slice._BUILTINS)
        self.assertNotIn("log", generate_typed_slice.APPROVED_TYPES)

    def test_optional_proof_fields_are_enumerated_from_the_dataclass(self):
        module = _module()
        derived = tuple(sorted(
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_")))
        self.assertEqual(derived, tuple(module._OPTIONAL_PROOF_FIELDS))
        program = _analyzed()
        self.assertTrue(all(getattr(program, name) is None
                            for name in derived))
        with self.assertRaises(ValueError) as raised:
            module.authenticate_log_admission(
                dataclasses.replace(program, fixed_nine_table_proof=object()),
                RAW_SHA256, PROFILE)
        self.assertIn(f"{PROFILE}: unrelated proof carrier is not absent",
                      str(raised.exception))

    def test_corpus_log_census_names_all_three_carriers(self):
        """Source-level census over the pinned corpus: exactly three
        programs contain a `log(` token -- newton (its own prepared lane),
        mandelbrot (this module's), and julia (adapter-only). The module's
        authenticatable set is mandelbrot alone."""
        module = _module()
        carriers = sorted(
            path.relative_to(CORPUS).with_suffix("").as_posix().replace("/", ":")
            for path in CORPUS.rglob("*.glsl")
            if "log(" in path.read_text(encoding="utf-8"))
        self.assertEqual(
            ["synth:julia:julia", "synth:mandelbrot:mandelbrot",
             "synth:newton:newton"],
            carriers)
        self.assertEqual(frozenset({KEY}), module._authenticatable_keys())
        from tools.glslcpp import check_corpus
        self.assertIn("synth/julia:julia", check_corpus._ADAPTERS)
        self.assertNotIn(KEY, check_corpus._ADAPTERS)


class JsProvenanceTests(unittest.TestCase):
    """The authority quotes, frozen as data at record time (quote-verified
    against the pinned snapshot this session)."""

    def test_the_factory_registration_and_pin_are_frozen(self):
        module = _module()
        self.assertEqual(("canonicalFactory252", 30151), module.JS_FACTORY)
        self.assertEqual(36432, module.JS_REGISTRATION_LINE)
        self.assertEqual(
            "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
            module.JS_CANONICAL_KERNELS_SHA256)

    def test_the_factory_tostring_sha_is_cross_validated(self):
        """Function.prototype.toString of canonicalFactory252 is 13,231
        bytes; the extraction method reproduces the frozen cellRefract/
        wobble (canonicalFactory3) and kaleido (canonicalFactory9) hashes
        exactly."""
        module = _module()
        self.assertEqual((13231,
                          "27b87c62a87c73d76e5a1d2d6096cecaa6714aeba"
                          "3f26f72a03698592918ee29"),
                         module.JS_FACTORY_TOSTRING)
        self.assertEqual(
            (("canonicalFactory3",
              "329d54732a502bc227c25faa3261ba42e599a53ceebb2193b484bec6b79013e3"),
             ("canonicalFactory9",
              "4ab626fda5e91e7f89b93c9d863cda497b85d79239183499785c03607cce19a3")),
            module.JS_CROSS_VALIDATION)

    def test_the_math_log_authority_is_frozen(self):
        """glsl-runtime.js:341 routes log to Math.log (the routing-risk
        note); log2 at :342 is the sibling mandelbrot never uses."""
        module = _module()
        self.assertEqual("log: unary(Math.log)", module.JS_LOG_AUTHORITY_LINE)
        self.assertEqual("src/csl/glsl-runtime.js:341",
                         module.JS_LOG_AUTHORITY_SITE)
        self.assertEqual("log2: unary(Math.log2)",
                         module.JS_LOG2_SIBLING_LINE)
        self.assertEqual("src/csl/glsl-runtime.js:342",
                         module.JS_LOG2_SIBLING_SITE)
        self.assertIn("Math.log", module.MATH_LOG_ROUTING_NOTE)
        self.assertIn("libm", module.MATH_LOG_ROUTING_NOTE)
        self.assertIn("not guaranteed", module.MATH_LOG_ROUTING_NOTE)

    def test_the_factory_log_materialization_is_frozen(self):
        module = _module()
        self.assertEqual(
            "const { sin, cos, atan, pow, log, sqrt, abs, floor, min, max, "
            "clamp, length, dot, normalize } = $runtime.stdlib",
            module.JS_STDLIB_DESTRUCTURING)
        self.assertEqual(
            (("var log_zn = log(mag2) * 0.5;", 30379),
             ("var nu = (log(log_zn / LOG2)) / LOG2;", 30380),
             ("var dist = (2 * mag) * log(mag) / dmag;", 30404)),
            module.JS_LOG_SITES)

    def test_the_narrowing_metadata_is_frozen(self):
        """The JS narrows LOG2 through f32; MAX_ITER stays 500; the
        iterations clamp (max 2000 > 500) has a reachable arm -- the
        design §8 open question, resolved by measurement."""
        module = _module()
        self.assertEqual("var LOG2 = 0.6931471824645996;",
                         module.JS_LOG2_NARROWED)
        self.assertEqual("var MAX_ITER = 500;", module.JS_MAX_ITER_LINE)
        self.assertEqual("var maxIter = min(iterations, MAX_ITER);",
                         module.JS_ITERATIONS_CLAMP)
        self.assertIn("i(500, 50, 2000)", module.JS_ITERATIONS_METADATA)
        self.assertIn("2000", module.JS_ITERATIONS_METADATA)

    def test_the_admission_verdict_cites_the_tanh_precedent(self):
        """The struct design's recommendation, executed: the tanh precedent
        is frontend-side (curl_vector_math_profile), so this record freezes
        the sites and the authorities consume node identity; log is already
        validator-approved, leaving only the emitter arm to integration."""
        module = _module()
        self.assertIn("curl_vector_math_profile", module.LOG_ADMISSION_VERDICT)
        self.assertIn("frontend record", module.LOG_ADMISSION_VERDICT)
        self.assertIn("emitter", module.LOG_ADMISSION_VERDICT)
        self.assertIn("tanh", module.LOG_ADMISSION_VERDICT)

    def test_the_lowering_contract_is_frozen(self):
        module = _module()
        self.assertEqual(
            ("log(float) == Math.log(float), scalar unary at all three "
             "sites",),
            module.LOWERING_CONTRACT)


class GuardMessageTests(unittest.TestCase):
    def test_every_guard_message_is_asserted_somewhere_in_this_file(self):
        module = _module()
        messages = _guard_messages(module)
        self.assertGreaterEqual(len(messages), 20,
                                "guard extraction looks broken")
        asserted = _call_argument_strings(pathlib.Path(__file__))
        self.assertGreaterEqual(len(asserted), 100,
                                "call-argument extraction looks broken")
        for message in messages:
            probe = message.strip()
            with self.subTest(message=probe):
                self.assertTrue(
                    any(probe in item for item in asserted),
                    f"guard string {probe!r} is not an argument to any call "
                    "in this file")

    def test_the_coverage_check_rejects_a_docstring_only_mention(self):
        probe = "a guard string that lives only in this docstring"
        here = pathlib.Path(__file__)
        self.assertIn(probe, here.read_text(encoding="utf-8"),
                      "the decoy has to really be in the file")
        self.assertFalse(
            any(probe in item for item in _call_argument_strings(here)),
            "prose must not be able to satisfy the coverage check")


class LockMutationTests(unittest.TestCase):
    """Per-lock RED/GREEN: mutate, refreeze only coarse fields, expect the
    lock's own message; then delete the predicate in a scratch re-exec and
    show the message is gone."""

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            relock=None, candidate=None):
        module = _module()
        candidate = _analyzed() if candidate is None else candidate
        mutate(candidate)
        overrides = {}
        if recount:
            overrides.update(_recount(module, candidate))
        if relock is not None:
            relock(module, candidate, overrides)
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
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
            module.authenticate_log_admission(_analyzed(), "0" * 64, PROFILE)
        scratch = _scratch(module, "_caller_source_hash_holds")
        scratch.authenticate_log_admission(_analyzed(), "0" * 64, PROFILE)

    def test_defines_lock(self):
        module = _module()
        candidate = dataclasses.replace(
            _analyzed(),
            preprocessor_defines=(PreprocessorDefine("NOISE_TYPE", "int",
                                                     "10"),))
        _expect(self, module, candidate, _relocked(module, candidate),
                "exact preprocessor define lock mismatch")
        scratch = _scratch(module, "_defines_hold")
        with mock.patch.object(scratch, "_LOCKS", _relocked(module, candidate)):
            scratch.authenticate_log_admission(
                candidate, RAW_SHA256, PROFILE)

    def _coarse_case(self, module, candidate, locks, expected, predicate):
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, expected):
            module.authenticate_log_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(expected, survived,
                             f"deleting {predicate} did not remove its message")

    def test_raw_source_lock(self):
        module = _module()
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "State-of-the-art", "State of the art"))
        locks = _relocked_partial(module, candidate, "raw")
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")

    def test_raw_bytes_and_sha_are_a_pair(self):
        module = _module()
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "Mandelelbrot", "Mandelbrot!"))
        # A length-changing mutant ("explorer!" for "explorer"):
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "explorer", "explorer!"))
        locks = _relocked_partial(module, candidate, "raw")
        locks[KEY]["raw_sha256"] = _hash(candidate.raw_source)
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")
        locks = _relocked_partial(module, candidate, "raw")
        locks[KEY]["raw_bytes"] = len(candidate.raw_source.encode("utf-8"))
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")

    def test_normalized_source_lock(self):
        module = _module()
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "const int MAX_ITER = 500;", "const int MAX_ITER = 499;"))
        locks = _relocked_partial(module, candidate, "normalized")
        self._coarse_case(module, candidate, locks, "normalized source drift",
                          "_normalized_source_holds")

    def test_functions_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "functions",
                           candidate.functions[:-1])
        locks = _relocked_partial(module, candidate, "functions")
        self._coarse_case(module, candidate, locks,
                          "typed function fingerprint drift",
                          "_functions_fingerprint_holds")

    def test_whole_program_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "local_type_names", ("sneaky",))
        locks = _relocked_partial(module, candidate, "whole")
        self._coarse_case(module, candidate, locks,
                          "whole-program fingerprint drift",
                          "_whole_program_fingerprint_holds")

    def test_interface_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(candidate, "local_type_names", ("sneaky",))
        locks = _relocked_partial(module, candidate, "interface")
        self._coarse_case(module, candidate, locks,
                          "interface fingerprint drift",
                          "_interface_fingerprint_holds")

    def test_unrelated_proof_absent_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "fixed_grid_counter_store_proof", object())
        self._delete_and_compare(
            mutate, "_unrelated_proof_absent_holds",
            "unrelated proof carrier is not absent")

    # --- program shape -----------------------------------------------------

    def test_function_cardinality_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "functions",
                               candidate.functions[:-1])
        self._delete_and_compare(
            mutate, "_function_cardinality_holds",
            "function cardinality mismatch", recount=True)

    def test_function_inventory_lock(self):
        def mutate(candidate):
            head, *rest = candidate.functions
            renamed = dataclasses.replace(
                head.signature, name="getAltitude")
            object.__setattr__(
                candidate, "functions",
                (dataclasses.replace(head, signature=renamed), *rest))
        self._delete_and_compare(
            mutate, "_function_inventory_holds",
            "typed function inventory mismatch", recount=True)

    def test_resources_lock(self):
        def mutate(candidate):
            resources = dataclasses.replace(
                candidate.resources, uses_derivatives=True)
            object.__setattr__(candidate, "resources", resources)
        self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")

    def test_call_graph_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(module._call_graph_holds(program, module._LOCKS[KEY]))
        # Break reachability by FORGING the reachable set (dropping a
        # function that is still present and still reached); recount alone
        # would re-freeze the true set and leave nothing to catch.
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["reachable"] = tuple(
            item for item in locks[KEY]["reachable"] if item != 117)
        _expect(self, module, program, locks,
                "call graph or reachability profile mismatch")
        scratch = _scratch(module, "_call_graph_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
                    program, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                "call graph or reachability profile mismatch", survived,
                "deleting _call_graph_holds did not remove its message")

    def test_binding_table_lock(self):
        def mutate_drop(candidate):
            object.__setattr__(candidate, "declarations",
                               candidate.declarations[:-1])
        self._delete_and_compare(
            mutate_drop, "_binding_table_holds", "binding table mismatch")

    def test_node_census_lock(self):
        def mutate(candidate):
            main = next(f for f in candidate.functions if f.name == "main")
            extra = dataclasses.replace(main.body[-1])
            object.__setattr__(main, "body", (*main.body, extra))
        self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch",
            recount=False)

    def test_main_body_lock(self):
        def mutate(candidate):
            main = next(f for f in candidate.functions if f.name == "main")
            object.__setattr__(main, "body", main.body[:-1])
        self._delete_and_compare(
            mutate, "_main_body_holds", "main body shape mismatch",
            recount=True)

    # --- mechanism A: the counted-for seed ----------------------------------

    def test_seed_value_lock(self):
        """The bound-value mutant: MAX_ITER 500 -> 499 (a same-length
        mutation; the oracle lane budgets the clamp-arm pixel
        discriminability, this lock is what makes it fail closed)."""
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const int MAX_ITER = 500;", "const int MAX_ITER = 499;")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_seed_declaration_holds",
            "counted-for bound seed declaration value profile mismatch",
            candidate=candidate,
            recount=True,
            relock=lambda module, program, overrides: overrides.update(
                {"counted_loop_proof": CLOSED_SUMMARY}))

    def test_seed_identity_lock(self):
        module = _module()
        program = _analyzed()
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["seed"]["declaration_sha256"] = "0" * 64
        _expect(self, module, program, locks,
                "counted-for bound seed declaration identity mismatch")
        scratch = _scratch(module, "_seed_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_log_admission(program, RAW_SHA256, PROFILE)

    def test_globals_census_lock(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const float PI = 3.14159265359;",
            "const float PI = 3.14159265358;")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_globals_census_holds",
            "source global census mismatch", candidate=candidate)

    def test_seed_reads_lock(self):
        # Replacing the min() site's MAX_ITER with a bare literal removes
        # exactly the 368:35 read (in main) and still analyzes.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "min(iterations, MAX_ITER)", "min(iterations, 500)")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_seed_reads_holds",
            "counted-for bound seed read census mismatch", candidate=candidate,
            recount=True)

    def _forge_seed_reference(self, candidate):
        """Plant an id node carrying the seed symbol id inside
        outputSmoothIteration (outside the two frozen read owners), on the
        `smoothIter / float(maxIter)` return's left operand -- a genuine
        id node the write census must catch."""
        writer = next(f for f in candidate.functions
                      if f.name == "outputSmoothIteration")
        statement = writer.body[0]
        host = statement.expressions[0]
        forged = dataclasses.replace(
            host,
            children=(dataclasses.replace(host.children[0],
                                          symbol_id=MAX_SYMBOL_ID),
                      host.children[1]))
        object.__setattr__(statement, "expressions", (forged,))

    def test_seed_write_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(
            module._no_seed_write_holds(program, {MAX_SYMBOL_ID}))
        self._forge_seed_reference(program)
        self.assertFalse(
            module._no_seed_write_holds(program, {MAX_SYMBOL_ID}))
        scratch = _scratch(module, "_no_seed_write_holds")
        self.assertTrue(
            scratch._no_seed_write_holds(program, {MAX_SYMBOL_ID}))

    def test_seed_write_lock_fires_end_to_end(self):
        module = _module()
        candidate = _analyzed()
        self._forge_seed_reference(candidate)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for bound seed write census mismatch")
        scratch = _scratch(module, "_no_seed_write_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn("counted-for bound seed write census mismatch",
                             survived,
                             "deleting _no_seed_write_holds did not remove "
                             "its message")

    def test_iteration_loop_lock_comparison(self):
        # `!=` (not `<`): the comparison-shape near-miss. It is one char
        # longer, so the bound read's span legitimately moves -- the relock
        # refreezes the mutant's true reads (and the recount its unproved
        # summary) so the closure and reads locks pass and the iteration
        # lock itself fires on the comparison.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "n < MAX_ITER", "n != MAX_ITER")
        candidate = _analyzed(raw=raw)

        def mutant_reads(module, program, overrides):
            overrides.update({"reads": tuple(
                (function.name, function.id,
                 node.span.start_line, node.span.start_column,
                 node.span.end_line, node.span.end_column)
                for function, node, _ in module._program_nodes(program)
                if node.kind == "id" and node.symbol_id == MAX_SYMBOL_ID)})

        self._delete_and_compare(
            lambda program: None, "_iteration_loop_holds",
            "counted-for iteration loop profile mismatch", candidate=candidate,
            recount=True, relock=mutant_reads)

    def test_iteration_loop_lock_start(self):
        # 0 -> 1 shrinks the trip count to 499 while every span stays put.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "int n = 0;", "int n = 1;")
        candidate = _analyzed(raw=raw)
        summary = candidate.counted_loop_proof
        self.assertEqual((1, 0, 1, 499, 1497, True),
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))
        self._delete_and_compare(
            lambda program: None, "_iteration_loop_holds",
            "counted-for iteration loop profile mismatch", candidate=candidate,
            recount=True)

    def test_counted_summary_lock(self):
        module = _module()
        program = _analyzed()
        forged = dataclasses.replace(
            program.counted_loop_proof, unproved_loop_count=1)
        candidate = dataclasses.replace(program, counted_loop_proof=forged)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for closure summary mismatch")
        scratch = _scratch(module, "_counted_summary_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
                    candidate, RAW_SHA256, PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn("counted-for closure summary mismatch", survived,
                             "deleting _counted_summary_holds did not remove "
                             "its message")

    def test_counted_rebuild_lock(self):
        """A tree whose summary CLAIMS the closure but whose functions are
        the proof-cleared originals: the rebuild lock catches the forgery."""
        module = _module()
        program = _analyzed(seeded=False)
        closed = dataclasses.replace(
            program.counted_loop_proof, loop_count=1,
            unproved_loop_count=0, max_effective_depth=1,
            max_lexical_product=500, entrypoint_charge=1500)
        candidate = dataclasses.replace(program, counted_loop_proof=closed)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for proof tree does not match the seed-derived "
                "rebuild")
        scratch = _scratch(module, "_counted_rebuild_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_log_admission(
                    candidate, RAW_SHA256, PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                "counted-for proof tree does not match the seed-derived "
                "rebuild", survived,
                "deleting _counted_rebuild_holds did not remove its message")

    # --- mechanism E: the log sites -----------------------------------------

    def test_log_census_lock(self):
        # sqrt is an approved same-arity same-type stand-in: removing one
        # log site leaves the census at two.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "log(mag2) * 0.5", "sqrt(mag2) * 0.5")
        candidate = _analyzed(raw=raw)
        module = _module()
        overrides = _recount(module, candidate)
        overrides["total_nodes"] = module._LOCKS[KEY]["total_nodes"]
        self._delete_and_compare(
            lambda program: None, "_log_census_holds",
            "log site census mismatch", candidate=candidate,
            recount=False, relock=lambda m, p, o: o.update(overrides))

    def test_log_shape_lock_argument_nesting(self):
        # log(log_zn / LOG2) -> log(log_zn): the child kind column flips
        # binary -> id; the resite companion re-derives the moved spans so
        # the SHAPE lock is the one that fires.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "log(log_zn / LOG2)", "log(log_zn)")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_log_shape_holds",
            "log site shape mismatch", candidate=candidate,
            recount=True,
            relock=lambda module, program, overrides: overrides.update(
                module._resite(program)))

    def test_log_identity_lock_argument_swap(self):
        # log(mag) -> log(dmag): every shape column survives (same kinds and
        # types); the resite companion re-derives the moved spans and the
        # identity hashes keep their frozen originals, so identity fires.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "log(mag) / dmag", "log(dmag) / dmag")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_log_identity_holds",
            "log site identity mismatch", candidate=candidate,
            recount=True,
            relock=lambda module, program, overrides: overrides.update(
                module._resite(program)))

    def test_log_identity_lock_tampered_hash(self):
        module = _module()
        program = _analyzed()
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["log_sites"] = tuple(
            (*site[:-1], ("0" * 64, *site[-1][1:]))
            for site in locks[KEY]["log_sites"])
        _expect(self, module, program, locks,
                "log site identity mismatch")
        scratch = _scratch(module, "_log_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_log_admission(program, RAW_SHA256, PROFILE)

    def test_log_family_census_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(
            module._log_family_census_holds(program, module._LOCKS[KEY]))
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["pow_sites"] = locks[KEY]["pow_sites"][:-1]
        _expect(self, module, program, locks, "log-family census mismatch")
        scratch = _scratch(module, "_log_family_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_log_admission(program, RAW_SHA256, PROFILE)

    def test_mechanism_census_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(
            module._mechanism_census_holds(program, module._LOCKS[KEY]))
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["mechanism_census"] = (10, 3, 0, 0)
        _expect(self, module, program, locks, "mechanism census mismatch")
        scratch = _scratch(module, "_mechanism_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_log_admission(program, RAW_SHA256, PROFILE)

    def test_resite_keeps_the_frozen_identity_hashes(self):
        """`_resite` is the site-value mutation tests' refreeze companion:
        positional columns re-derived from the candidate, identity hashes
        and value columns kept frozen. On the unmutated program it must
        reproduce both frozen tables exactly."""
        module = _module()
        program = _analyzed()
        frozen_sites = module._LOCKS[KEY]["log_sites"]
        frozen_shape = module._LOCKS[KEY]["log_shape"]
        resited = module._resite(program)
        self.assertEqual(
            {"log_sites": frozen_sites, "log_shape": frozen_shape}, resited)
        self.assertEqual(tuple(site[-1] for site in frozen_sites),
                         tuple(site[-1] for site in resited["log_sites"]))


class LedgerSabotageTests(unittest.TestCase):
    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        proof = module.authenticate_log_admission(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(3, len(proof.sites))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "log admission visitation ledger mismatch"):
                module.authenticate_log_admission(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(3, len(
            module.authenticate_log_admission(
                _analyzed(), RAW_SHA256, PROFILE).sites))


class DeleteTheCheckSweepTests(unittest.TestCase):
    """Mechanical completeness: every individually deletable predicate in
    the module source is exercised by a named test in this file."""

    def test_every_predicate_is_covered_by_a_named_test(self):
        module = _module()
        tree = ast.parse(
            pathlib.Path(module.__file__).read_text(encoding="utf-8"))
        predicates = sorted(
            node.name for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name.endswith("_holds"))
        self.assertGreaterEqual(len(predicates), 20,
                                "predicate extraction looks broken")
        text = pathlib.Path(__file__).read_text(encoding="utf-8")
        for name in predicates:
            with self.subTest(predicate=name):
                self.assertIn(name, text,
                              f"{name} has no delete-the-check coverage")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
