"""Focused RED/GREEN proof for `filter/parallax`'s two-rung counted-for closure.

Written before ``tools/glslcpp/frontend/texture_lod_admission_profile.py``
existed; the first run of this file reported ``ModuleNotFoundError`` from
``_module`` for every test in it.

``filter/parallax:parallax`` is the counted-for bucket's cheapest program
(``counted-for-design.md`` section 2.1 / section 5, cost rank 1): measured
**two rungs from CLEAN at both authorities** behind only KNOWN mechanisms --

* rung 1 (mechanism A, the "const-global-literal" bound shape): the march
  loop ``for (int i = 1; i <= MARCH_STEPS; i++)`` is bounded by the const
  global ``const int MARCH_STEPS = 32;``. The bound proof rides the EXISTING
  dict-keyed module -- a new key in ``loop_proof.py``'s
  ``_SOURCE_GLOBAL_LITERAL_INT_PROFILES`` (the Task-23 shape, carrier
  auto-supplied from the key, row stays minimal). This module freezes the
  complete dict-entry data as ``counted_for_seed_contract`` and re-derives
  the seed-attached tree itself, so the record is the integration slice's
  one-move landing source.
* rung 2 (mechanism B): ``textureLod`` is not in the builtin vocabulary, and
  the validator rejects the first of the program's two sites at ``24:26``.
  The JavaScript authority is a measured pure alias --
  ``glsl-runtime.js:400``: ``textureLod: (surface, coord) =>
  this.#texture(surface, coord)`` -- the lod argument is DROPPED, so the
  admission is an identity arm over the existing texture path with a frozen
  lod-``0`` literal check and no mip machinery. This module is that arm's
  frontend home: it hands the authorities the two exact live call nodes.

The module is **PREPARED, not landed** (the ``mutable_global_array_profile``
landed/prepared split): ``KEYS`` is empty, ``PREPARED_KEYS`` carries the
parallax key, and nothing in ``generate_typed_slice.py`` /
``emit_typed_cpp.py`` references the module yet -- so no live schema census
moves until the integration slice lands the row, the dict key, and the two
authority arms together.

Testing rules inherited from the house pattern apply directly:

1. ``Symbol`` embeds its declaration span and every node embeds its
   children, so a value-level mutation shifts every enclosing node hash.
   The production module evaluates the value locks **ahead** of the
   node-identity locks, and each lock is proved load-bearing by *deleting
   the lock* in a scratch re-exec -- never by mutating the input and
   watching some coarse hash raise instead.
2. Every mutation test refreezes **only** the coarse hash fields (plus the
   census counters the mutation unavoidably moves) and asserts that no
   coarse message fired. Semantic fields keep their frozen originals.
3. The census walks global declaration initializers as well as function
   bodies (the standing blind-spot trap); here the initializer census is
   two literal nodes, and the walk is what proves no third textureLod can
   hide in one.
4. Every guard string this module raises gets a test asserting that exact
   message, enforced mechanically against the module's own AST.

Two census conventions were re-derived this session and DIVERGE from the
design's prose (recorded here so the next lane does not "fix" them back):

* the design's "165 nodes" counts function bodies only; the house census
  (initializers included) freezes **167** -- the two const global
  initializers are the difference;
* the design's "call edges 4" counts call NODES (main calls getHeight
  twice); the deduplicated sorted edge SET the house modules freeze has
  **3** edges;
* the design's "read at 58:26" cites the enclosing initializer span; the
  ``MARCH_STEPS`` id node itself is ``58:38-58:49`` (bound read
  ``59:30-59:41``), which is what the reads lock freezes.

Corrections made when this file was restored against the finished module
(each parked assertion contradicted a measured fact of the live tree and
was adjusted, never deleted):

* ``_expect`` now installs the forged lock table with
  ``mock.patch.object(module, "_LOCKS", locks)`` -- without it every
  refrozen lock was dead weight and each mutation died at the coarse gate.
* the dict-patch context in ``test_seed_contract_...`` also patches
  ``loop_proof.SOURCE_GLOBAL_LITERAL_INT_KEYS``: it is an import-time
  ``frozenset`` and ``mock.patch.dict`` on the profiles dict cannot move it.
* ``test_normalized_source_lock`` mutates ``MARCH_STEPS = 31`` instead of a
  comment: the normalizer strips comments, so the parked comment mutant
  never reaches the normalized source at all.
* ``test_seed_reads_lock`` mutates ``1.0 / float(MARCH_STEPS)`` to
  ``1.0 / 32.0`` instead of deleting the whole ``stepSize`` line: the line
  deletion leaves ``stepSize`` undefined and the analyzer refuses the
  source (``E_UNKNOWN_SYMBOL``), so the reads lock is unreachable that way.
* the three coarse fingerprint tests use ``_relocked_partial`` (the
  ``test_mutable_global_array`` house pattern): ``_delete_and_compare``
  refreezes every coarse field, so through it a coarse lock can never fire.
* ``test_defines_lock`` builds its forged define with the
  ``PreprocessorDefine`` constructor -- parallax's real ``defines`` tuple is
  empty, so the parked ``preprocessor_defines[0]`` indexing raised
  ``IndexError``.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib
import importlib.util
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
    clear_counted_loop_proofs, summarize_counted_loop_proofs)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine, TypedProgram


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.texture_lod_admission_profile"

KEY = "filter/parallax:parallax"
PROFILE = "texture-lod-admission-parallax-v1"
SOURCE_PATH = "filter/parallax/parallax.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642"
NORMALIZED_SHA256 = (
    "281c8163d7f5fd47dc2ebd258003b04e1d41f7687c52e3c99e5aa56c911bd5f0")

MARCH_SYMBOL_ID = 8
MARCH_VALUE = 32
MARCH_SPAN = "13:1-13:28"
HEIGHTMAP_SYMBOL_ID = 2
INPUTTEX_SYMBOL_ID = 1
LOD_SPANS = ("24:26-24:61", "30:12-30:46")
LOOP_SPAN = "59:9-71:10"
LIVE_SUMMARY = (0, 1, 0, 0, 0, True)
CLOSED_SUMMARY = (1, 0, 1, 32, 32, True)
LEDGER = 13

# The complete mechanism-A dict entry this module freezes for the integration
# slice (loop_proof.py's `_SOURCE_GLOBAL_LITERAL_INT_PROFILES` shape).
SEED_CONTRACT = {
    "raw": RAW_SHA256,
    "source": NORMALIZED_SHA256,
    "defines": (),
    "integer": ("MARCH_STEPS", 8, "32", 32),
    "globals": (("MARCH_STEPS", 8, "int", "32"),
                ("SHIFT_SCALE", 9, "float", "0.15")),
    "reads": (("main", 16, 58, 38, 58, 49), ("main", 16, 59, 30, 59, 41)),
    "pre_functions":
        "39bfbb083f4383209661da6248eecff353f3f1ff7257c828bc1ce62bcf821808",
    "post_functions":
        "7b13f5ae2cd5f75f179c601d57d5ea818919841a700c3400d3ccb40f8ab4b9d0",
    "pre_whole":
        "920fe71bb122690f2169d2ee27ab6a4f908a18bf55b6031cb44fe51ba50c5eff",
    "post_whole":
        "30e996fec218dfd0c92f0f706d1cde5b0da84b25421fedf6d9f08479421d8a16",
    "interface":
        "9ff15dc1fd4f97bd0d392bd40d1cab39a4c1fcb988c2d79d595f933235d39314",
}

FOREIGN_SOURCE = (
    "uniform sampler2D inputTex;\n"
    "out vec4 fragColor;\n"
    "void main() {\n"
    "    fragColor = textureLod(inputTex, vec2(0.5), 0.0);\n"
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
        raise AssertionError("textureLod admission profile module is absent")
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


def _seed_tuple(program: TypedProgram):
    """The mechanism-A seed, built exactly as semantic.py builds it."""
    march = next(item for item in program.declarations
                 if item.symbol.name == "MARCH_STEPS")
    return ((march.symbol.id, MARCH_VALUE,
             "source-global-const-literal", march.symbol),)


def _analyzed(raw: str | None = None, seeded: bool = True):
    """The analyzed parallax program; `seeded` attaches mechanism A's proof.

    The seed attachment is semantic.py's own call sequence (frontend/semantic
    .py:291-294): clear, authenticate, re-attach with the seed. It is the
    state the validator holds once the loop_proof dict key lands.
    """
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


def _expect(test, module, candidate, locks, expected, profile=PROFILE,
            key=KEY):
    with mock.patch.object(module, "_LOCKS", locks), \
            test.assertRaises(ValueError) as raised:
        module.authenticate_texture_lod_admission(
            candidate, locks[key]["raw_sha256"], profile)
    message = str(raised.exception)
    test.assertIn(f"{profile}: ", message)
    test.assertIn(expected, message)
    for coarse in COARSE:
        test.assertNotIn(coarse, message)
    return message


# The coarse gate, in the order the module evaluates it.
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
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen.

    Deliberately does **not** refreeze any semantic field: the seed record,
    the site records, the loop profile and every node hash keep their frozen
    originals. Refreezing those would hand the mutation to the very lock
    under test and make the experiment vacuous.
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
    """Every literal string fragment this module hands to ``fail``."""
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
    """Every string constant this file passes as an argument to a call."""
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
        self.assertEqual(PARALLAX_KEY := KEY, module.PARALLAX_KEY)
        self.assertEqual(PROFILE, module.PARALLAX_PROFILE)


class ParallaxFrozenFactTests(unittest.TestCase):
    """Every figure re-derived against the pinned corpus before freezing."""

    def test_pinned_source_bytes_and_hash(self):
        module = _module()
        raw = SOURCE.read_bytes()
        self.assertEqual(2430, len(raw))
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        lock = module._LOCKS[KEY]
        self.assertEqual(2430, lock["raw_bytes"])
        self.assertEqual(RAW_SHA256, lock["raw_sha256"])
        self.assertEqual("sources/filter/parallax/parallax.glsl",
                         lock["source_path"])

    def test_live_analysis_matches_frozen_identity(self):
        module = _module()
        program = _analyzed(seeded=False)
        normalized = program.source.encode("utf-8")
        self.assertEqual(1902, len(normalized))
        self.assertEqual(NORMALIZED_SHA256,
                         hashlib.sha256(normalized).hexdigest())
        self.assertEqual((), tuple((item.name, item.kind, item.canonical_value)
                                   for item in program.preprocessor_defines))
        self.assertEqual(
            (("inputTex", "heightMap", "tileOffset", "fullResolution",
              "direction", "pivot"),
             ("inputTex", "heightMap"), ("fragColor",), True, False),
            (program.resources.uniforms, program.resources.samplers,
             program.resources.outputs, program.resources.uses_texture,
             program.resources.uses_derivatives))
        # The live (rung 0) boundary: one loop, unproved.
        summary = program.counted_loop_proof
        self.assertEqual(LIVE_SUMMARY,
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))

    def test_rung0_is_answered_by_the_required_carrier_arm_now(self):
        program = _analyzed(seeded=False)
        # With the loop-proof dict key LANDED, the unseeded tree carrying no
        # carrier is answered by the required-carrier arm at the validator,
        # ahead of any construct gate. The PRE-wiring tree answered the
        # march loop itself here -- `59:9: unsupported counted-for program
        # proof`, both authorities -- and the seeded-but-unadmitted tree is
        # still answered one rung later by `24:26: unsupported builtin
        # textureLod` (pinned by the lane-extension tests and the
        # integration class).
        with self.assertRaises(generate_typed_slice.GeneratorError) as raised:
            generate_typed_slice.validate_capabilities(
                program, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        self.assertEqual(
            f"{KEY}: exact source-global literal-int carrier required",
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
        whole-program validator, and the next gate is textureLod at 24:26."""
        module = _module()
        contract = module.counted_for_seed_contract(KEY)
        entry = contract._asdict()
        program = _analyzed(seeded=False)
        cleared = clear_counted_loop_proofs(program.functions)
        pre = attach_counted_loop_proofs(cleared, KEY)
        # `SOURCE_GLOBAL_LITERAL_INT_KEYS` is an import-time frozenset, so
        # the key set is patched alongside the dict: with the entry present,
        # KEY is in the key census exactly as the landed dict will make it.
        with mock.patch.dict(loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES,
                             {KEY: entry}), \
                mock.patch.object(
                    loop_proof_module, "SOURCE_GLOBAL_LITERAL_INT_KEYS",
                    frozenset(
                        loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES)):
            self.assertIn(KEY, loop_proof_module.SOURCE_GLOBAL_LITERAL_INT_KEYS)
            # authenticate_source_global_literal_int itself accepts the entry.
            seeds = loop_proof_module.authenticate_source_global_literal_int(
                key=KEY, raw_source=program.raw_source,
                source=program.source,
                preprocessor_defines=program.preprocessor_defines,
                declarations=program.declarations, functions=pre,
                profile=SOURCE_GLOBAL_LITERAL_INT_CAPABILITY)
            self.assertEqual(((MARCH_SYMBOL_ID, MARCH_VALUE,
                               "source-global-const-literal",
                               program.declarations[7].symbol),),
                             tuple(seeds))
            # And the full analyze+validate path closes rung 1.
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
            # With the loop-proof key landed, rung 1 closes on the LIVE
            # dict (no patching needed) and the validator then demands the
            # textureLod carrier (rung 2's required-carrier arm); with BOTH
            # carriers the full validation passes -- the pre-wiring tree's
            # rung-2 message itself (`24:26: unsupported builtin textureLod`)
            # stays pinned by the lane-extension impostor test and the
            # integration class.
            with self.assertRaises(
                    generate_typed_slice.GeneratorError) as raised:
                generate_typed_slice.validate_capabilities(
                    post, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=RAW_SHA256,
                    source_global_literal_int_profile=(
                        SOURCE_GLOBAL_LITERAL_INT_CAPABILITY))
            self.assertEqual(
                f"{KEY}: exact textureLod admission profile carrier required",
                str(raised.exception))
            generate_typed_slice.validate_capabilities(
                post, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256,
                source_global_literal_int_profile=(
                    SOURCE_GLOBAL_LITERAL_INT_CAPABILITY),
                texture_lod_admission_profile=PROFILE)
        # LANDED: the dict now carries the key, and the entry IS the frozen
        # contract (the integration class pins field-for-field equality).
        self.assertIn(KEY,
                      loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES)
        self.assertEqual(
            entry,
            loop_proof_module._SOURCE_GLOBAL_LITERAL_INT_PROFILES[KEY])

    def test_node_census_uses_the_house_convention(self):
        """167 nodes, initializers included (the design's 165 counted
        function bodies only); 6 assigns."""
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual((167, 6), (total, assigns))
        self.assertEqual((167, 6),
                         (module._LOCKS[KEY]["total_nodes"],
                          module._LOCKS[KEY]["total_assigns"]))

    def test_call_graph_is_three_deduplicated_edges(self):
        """The design's 'call edges 4' counts call NODES (main calls
        getHeight twice); the frozen edge SET has three members."""
        module = _module()
        program = _analyzed()
        edges = module._call_graph(program)
        self.assertEqual(
            ((13, "getHeight", 15, "getLuminosity"),
             (16, "main", 13, "getHeight"),
             (16, "main", 14, "getInput")),
            edges)
        self.assertEqual(3, module._LOCKS[KEY]["call_edge_count"])

    def test_march_steps_reads_freeze_the_id_node_spans(self):
        """The design's '58:26' is the enclosing initializer span; the reads
        lock freezes the id nodes: 58:38-58:49 and 59:30-59:41."""
        module = _module()
        self.assertEqual(
            (("main", 16, 58, 38, 58, 49), ("main", 16, 59, 30, 59, 41)),
            module._LOCKS[KEY]["reads"])


class AdmissionGreenTests(unittest.TestCase):
    def test_post_seed_tree_authenticates_and_returns_both_sites(self):
        module = _module()
        program = _analyzed()
        proof = module.authenticate_texture_lod_admission(
            program, RAW_SHA256, PROFILE)
        self.assertEqual(2, len(proof.sites))
        self.assertEqual(("getHeight", "getInput"),
                         tuple(site.owner_name for site in proof.sites))
        self.assertEqual(LOD_SPANS, tuple(site.span for site in proof.sites))
        # The sites carry LIVE nodes out of the caller's own tree.
        tree_nodes = {id(item) for item in _nodes(program)}
        for site in proof.sites:
            for live in (site.node, site.sampler, site.coord, site.lod):
                self.assertIn(id(live), tree_nodes)
        self.assertEqual(HEIGHTMAP_SYMBOL_ID, proof.sites[0].sampler_symbol_id)
        self.assertEqual(INPUTTEX_SYMBOL_ID, proof.sites[1].sampler_symbol_id)
        self.assertEqual(LEDGER, len(proof.consumed_objects))
        self.assertEqual(len(proof.consumed_objects),
                         len({id(item) for item in proof.consumed_objects}))

    def test_apply_is_the_identity(self):
        module = _module()
        program = _analyzed()
        self.assertIs(program, module.apply_texture_lod_admission(
            program, RAW_SHA256, PROFILE))

    def test_live_pre_seed_tree_is_refused_at_the_summary_lock(self):
        """Rung 1 is not closed on a plain analyzed tree: the module demands
        the seed-attached state the authorities will actually hold."""
        module = _module()
        program = _analyzed(seeded=False)
        with self.assertRaises(ValueError) as raised:
            module.authenticate_texture_lod_admission(
                program, RAW_SHA256, PROFILE)
        self.assertIn(f"{PROFILE}: counted-for closure summary mismatch",
                      str(raised.exception))

    def test_foreign_key_without_profile_returns_none(self):
        module = _module()
        self.assertIsNone(module.authenticate_texture_lod_admission(
            _foreign(), _hash(FOREIGN_SOURCE), None))

    def test_foreign_key_with_profile_names_the_two_sites(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_texture_lod_admission(
                _foreign(), _hash(FOREIGN_SOURCE), PROFILE)
        self.assertEqual(
            f"{PROFILE}: program key is not an admitted textureLod admission "
            f"carrier; {KEY} 24:26 and 30:12 are the sole admitted "
            "textureLod sites",
            str(raised.exception))

    def test_wrong_profile_string_is_refused(self):
        module = _module()
        program = _analyzed()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_texture_lod_admission(
                program, RAW_SHA256, "texture-lod-admission-parallax-v2")
        self.assertIn(f"{PROFILE}: exact profile carrier required",
                      str(raised.exception))

    def test_mechanism_census_is_frozen_empty(self):
        """The design's mechanism census: 0 out/inout params, 0 bare void
        calls, 0 bit-ops, 0 index expressions -- parallax's 'no secondary
        mechanisms at all' fact, locked."""
        module = _module()
        program = _analyzed()
        self.assertEqual((0, 0, 0, 0), module._mechanism_census(program))
        self.assertEqual((0, 0, 0, 0),
                         module._LOCKS[KEY]["mechanism_census"])

    def test_texture_family_census_freezes_the_alias_boundary(self):
        """Two textureSize sites, ZERO plain texture and ZERO texelFetch:
        the program's only sampling sites are the two textureLod nodes the
        identity arm admits."""
        module = _module()
        program = _analyzed()
        self.assertEqual((), module._LOCKS[KEY]["plain_texture_and_fetch"])
        sizes = module._texture_size_census(program)
        self.assertEqual(2, len(sizes))
        self.assertEqual(((13, "getHeight"), (14, "getInput")),
                         tuple((item[0], item[1]) for item in sizes))


class PreparedDisciplineTests(unittest.TestCase):
    def test_parallax_is_landed_and_nothing_is_prepared(self):
        module = _module()
        self.assertEqual((KEY,), module.KEYS)
        self.assertEqual((), module.PREPARED_KEYS)
        self.assertEqual({KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({KEY}), module.TEXTURE_LOD_ADMISSION_KEYS)

    def test_landed_row_fields_are_frozen(self):
        module = _module()
        self.assertEqual(
            frozenset({"defines", "program_key", "texture_lod_admission_profile"}),
            module.allowed_row_fields(KEY))
        self.assertEqual({KEY}, set(module.ALLOWED_ROW_FIELDS))
        self.assertEqual({}, module.PREPARED_ROW_FIELDS)

    def test_allowed_row_fields_rejects_foreign_keys(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.allowed_row_fields("test:foreign")
        self.assertIn(
            f"{PROFILE}: test:foreign is not an admitted textureLod "
            "admission carrier",
            str(raised.exception))

    def test_both_authorities_reference_the_module_now(self):
        """LANDED by construction: both independent authorities import the
        module -- the wiring the integration slice (typed row 190) landed."""
        for name in ("generate_typed_slice.py", "emit_typed_cpp.py"):
            path = ROOT / "tools/glslcpp" / name
            self.assertIn("texture_lod_admission",
                          path.read_text(encoding="utf-8"), name)

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

    def test_optional_proof_fields_are_enumerated_from_the_dataclass(self):
        """The sibling-proof allowlist is every `fixed_*_proof` field a
        TypedProgram carries, re-derived here so a new proof field added
        elsewhere in the tree turns this red rather than slipping through."""
        module = _module()
        derived = tuple(sorted(
            field.name for field in dataclasses.fields(TypedProgram)
            if field.name.startswith("fixed_")))
        self.assertEqual(derived, tuple(module._OPTIONAL_PROOF_FIELDS))
        program = _analyzed()
        self.assertTrue(all(getattr(program, name) is None
                            for name in derived))
        with self.assertRaises(ValueError) as raised:
            module.authenticate_texture_lod_admission(
                dataclasses.replace(program, fixed_nine_table_proof=object()),
                RAW_SHA256, PROFILE)
        self.assertIn(f"{PROFILE}: unrelated proof carrier is not absent",
                      str(raised.exception))

    def test_corpus_texturelod_census_parallax_is_the_sole_carrier(self):
        """Source-level census over the pinned corpus: exactly one program
        contains textureLod, and it is parallax. The module's authenticatable
        set matches."""
        module = _module()
        carriers = sorted(
            path.relative_to(CORPUS).with_suffix("").as_posix().replace("/", ":")
            for path in CORPUS.rglob("*.glsl")
            if "textureLod" in path.read_text(encoding="utf-8"))
        self.assertEqual(["filter:parallax:parallax"], carriers)
        self.assertEqual(frozenset({KEY}), module._authenticatable_keys())


class JsAliasProvenanceTests(unittest.TestCase):
    """The alias contract, frozen as data at record time (the oracle lane
    re-verifies against the pinned snapshot)."""

    def test_the_runtime_alias_quote_is_frozen(self):
        module = _module()
        self.assertEqual(
            "textureLod: (surface, coord) => this.#texture(surface, coord)",
            module.JS_TEXTURE_LOD_ALIAS_LINE)
        self.assertEqual("src/csl/glsl-runtime.js:400", module.JS_ALIAS_SITE)

    def test_the_factory_sites_and_registration_are_frozen(self):
        module = _module()
        self.assertEqual(("canonicalFactory98", 16693),
                         module.JS_FACTORY)
        self.assertEqual((16714, 16720), module.JS_LOD_LITERAL_LINES)
        self.assertEqual(36278, module.JS_REGISTRATION_LINE)
        self.assertEqual(
            "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
            module.JS_CANONICAL_KERNELS_SHA256)


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
                scratch.authenticate_texture_lod_admission(
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
            module.authenticate_texture_lod_admission(
                _analyzed(), "0" * 64, PROFILE)
        scratch = _scratch(module, "_caller_source_hash_holds")
        scratch.authenticate_texture_lod_admission(
            _analyzed(), "0" * 64, PROFILE)

    def test_defines_lock(self):
        module = _module()
        program = _analyzed()
        defines = module._defines_hold(program, module._LOCKS[KEY])
        self.assertTrue(defines)
        # parallax's real defines tuple is empty, so the forged define is
        # built with the constructor -- indexing [0] would raise IndexError.
        fake = dataclasses.replace(program, preprocessor_defines=(
            PreprocessorDefine("NOISE_TYPE", "int", "10"),))
        self.assertFalse(module._defines_hold(fake, module._LOCKS[KEY]))
        scratch = _scratch(module, "_defines_hold")
        with self.assertRaises(ValueError):
            scratch.authenticate_texture_lod_admission(
                fake, "0" * 64, PROFILE)

    def _coarse_case(self, module, candidate, locks, expected,
                     predicate):
        """The coarse locks ARE the coarse messages, so they cannot route
        through _expect (which forbids coarse messages); the house pattern
        is assertRaisesRegex plus a scratch deletion of the predicate."""
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, expected):
            module.authenticate_texture_lod_admission(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
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
            "Pseudo-3D", "Pseudo 3D"))
        locks = _relocked_partial(module, candidate, "raw")
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")

    def test_raw_bytes_and_sha_are_a_pair(self):
        # The pair discipline needs a LENGTH-changing mutant: "Pseudo 3D" is
        # the same length as "Pseudo-3D", so refreezing the hash alone would
        # leave nothing for the byte count to catch.
        module = _module()
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "Pseudo-3D", "Pseudo-3D!"))
        locks = _relocked_partial(module, candidate, "raw")
        # Refreezing the hash alone leaves the byte count to catch it...
        locks[KEY]["raw_sha256"] = _hash(candidate.raw_source)
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")
        # ...and refreezing the count alone leaves the hash to catch it.
        locks = _relocked_partial(module, candidate, "raw")
        locks[KEY]["raw_bytes"] = len(candidate.raw_source.encode("utf-8"))
        self._coarse_case(module, candidate, locks, "raw source drift",
                          "_raw_source_holds")

    def test_normalized_source_lock(self):
        # A comment mutant never reaches the normalized source (comments are
        # stripped), so the mutation is a code-level one: MARCH_STEPS = 31.
        module = _module()
        candidate = _analyzed(raw=SOURCE.read_text(encoding="utf-8").replace(
            "const int MARCH_STEPS = 32;", "const int MARCH_STEPS = 31;"))
        locks = _relocked_partial(module, candidate, "normalized")
        self._coarse_case(module, candidate, locks, "normalized source drift",
                          "_normalized_source_holds")

    def test_functions_fingerprint_lock(self):
        # _delete_and_compare refreezes every coarse field, so a coarse lock
        # can only fire through a PARTIAL relock (the house pattern).
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
        # Break reachability: drop `main` (the last function) from the table
        # and forge a reachable set that still names it.
        broken = dataclasses.replace(program, functions=program.functions[:-1])
        locks = _relocked(module, broken, **_recount(module, broken))
        locks[KEY]["reachable"] = (13, 15, 16)
        _expect(self, module, broken, locks,
                "call graph or reachability profile mismatch")
        scratch = _scratch(module, "_call_graph_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
                    broken, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                "call graph or reachability profile mismatch", survived,
                "deleting _call_graph_holds did not remove its message")

    def test_binding_table_lock(self):
        # Drop a declaration from the binding table view.
        def mutate_drop(candidate):
            object.__setattr__(candidate, "declarations",
                               candidate.declarations[:-1])
        self._delete_and_compare(
            mutate_drop, "_binding_table_holds", "binding table mismatch")

    def test_node_census_lock(self):
        def mutate(candidate):
            main = next(f for f in candidate.functions if f.name == "main")
            extra = dataclasses.replace(main.body[-1])
            object.__setattr__(
                main, "body", (*main.body, extra))
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
        """The bound-value mutant: MARCH_STEPS 32 -> 31 (the design's
        satisfiability-note mutant; the ORACLE lane budgets its pixel
        discriminability, this lock is what makes it fail closed)."""
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const int MARCH_STEPS = 32;", "const int MARCH_STEPS = 31;")
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
            scratch.authenticate_texture_lod_admission(
                program, RAW_SHA256, PROFILE)

    def test_globals_census_lock(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "const float SHIFT_SCALE = 0.15;", "const float SHIFT_SCALE = 0.2;")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_globals_census_holds",
            "source global census mismatch", candidate=candidate)

    def test_seed_reads_lock(self):
        # Deleting the whole stepSize line leaves `stepSize` undefined and
        # the analyzer refuses the source (E_UNKNOWN_SYMBOL); replacing the
        # float(MARCH_STEPS) cast with a bare literal removes exactly the
        # 58:38 read and still analyzes.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "1.0 / float(MARCH_STEPS)", "1.0 / 32.0")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_seed_reads_holds",
            "counted-for bound seed read census mismatch", candidate=candidate,
            recount=True)

    def test_seed_write_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(
            module._no_seed_write_holds(program, {MARCH_SYMBOL_ID}))
        # A synthetic write to the seed symbol anywhere in the tree.
        writer = next(f for f in program.functions if f.name == "getLuminosity")
        statement = writer.body[0]
        assign = statement.expressions[0]
        forged = dataclasses.replace(
            assign, children=(dataclasses.replace(
                assign.children[0], symbol_id=MARCH_SYMBOL_ID),
                assign.children[1]))
        object.__setattr__(
            statement, "expressions", (forged,))
        self.assertFalse(
            module._no_seed_write_holds(program, {MARCH_SYMBOL_ID}))
        scratch = _scratch(module, "_no_seed_write_holds")
        self.assertTrue(
            scratch._no_seed_write_holds(program, {MARCH_SYMBOL_ID}))

    def test_march_loop_lock(self):
        # `!=` (not `<`): a shorter comparison shifts the bound read's span
        # and the reads lock would absorb the mutation; `!=` is the
        # same-length comparison-shape near-miss.
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "i <= MARCH_STEPS", "i != MARCH_STEPS")
        candidate = _analyzed(raw=raw)
        # recount freezes the mutant's true (1,0,1,31,31,True) summary so
        # the closure lock passes and the march lock itself fires.
        self._delete_and_compare(
            lambda program: None, "_march_loop_holds",
            "counted-for march loop profile mismatch", candidate=candidate,
            recount=True)

    def test_counted_summary_lock(self):
        module = _module()
        program = _analyzed()
        forged = dataclasses.replace(
            program.counted_loop_proof, unproved_loop_count=1)
        candidate = dataclasses.replace(
            program, counted_loop_proof=forged)
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for closure summary mismatch")
        scratch = _scratch(module, "_counted_summary_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
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
        summary = summarize_counted_loop_proofs(program.functions)
        # Claim the closed summary while the functions stay unproved.
        closed = dataclasses.replace(
            program.counted_loop_proof, loop_count=1,
            unproved_loop_count=0, max_effective_depth=1,
            max_lexical_product=32, entrypoint_charge=32)
        candidate = dataclasses.replace(program, counted_loop_proof=closed)
        self.assertEqual(CLOSED_SUMMARY, tuple(
            (closed.loop_count, closed.unproved_loop_count,
             closed.max_effective_depth, closed.max_lexical_product,
             closed.entrypoint_charge, closed.call_graph_acyclic)))
        del summary
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for proof tree does not match the seed-derived "
                "rebuild")
        scratch = _scratch(module, "_counted_rebuild_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
                    candidate, RAW_SHA256, PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                "counted-for proof tree does not match the seed-derived "
                "rebuild", survived,
                "deleting _counted_rebuild_holds did not remove its message")

    # --- mechanism B: the textureLod sites -----------------------------------

    def test_lod_census_lock(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "    return textureLod(inputTex, localUV, 0.0);",
            "    return texture(inputTex, localUV);")
        candidate = _analyzed(raw=raw)
        module = _module()
        overrides = _recount(module, candidate)
        overrides.update({"total_nodes": module._LOCKS[KEY]["total_nodes"]})
        self._delete_and_compare(
            lambda program: None, "_texture_lod_census_holds",
            "textureLod site census mismatch", candidate=candidate,
            recount=False, relock=lambda m, p, o: o.update(overrides))

    def test_lod_shape_lock_value(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "textureLod(inputTex, localUV, 0.0)",
            "textureLod(inputTex, localUV, 1.0)")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_lod_shape_holds",
            "textureLod site shape mismatch", candidate=candidate,
            recount=True,
            relock=lambda module, program, overrides: overrides.update(
                module._resite(program, {2: -1})))

    def test_lod_shape_lock_sampler_swap(self):
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "textureLod(heightMap, localUV, 0.0)",
            "textureLod(inputTex, localUV, 0.0)")
        candidate = _analyzed(raw=raw)
        self._delete_and_compare(
            lambda program: None, "_lod_shape_holds",
            "textureLod site shape mismatch", candidate=candidate,
            recount=True,
            relock=lambda module, program, overrides: overrides.update(
                module._resite(program, {1: 0})))

    def test_lod_identity_lock(self):
        module = _module()
        program = _analyzed()
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["lod_sites"] = tuple(
            (*site[:-1], site[-1] + ("0" * 64,))
            if isinstance(site[-1], tuple) else site
            for site in locks[KEY]["lod_sites"])
        _expect(self, module, program, locks,
                "textureLod site identity mismatch")
        scratch = _scratch(module, "_lod_identity_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_texture_lod_admission(
                program, RAW_SHA256, PROFILE)

    def test_lod_literal_checks_are_a_pair(self):
        """Sub-clause pair discipline: the lod check has a VALUE sub-clause
        (extracted literal-or-unary-minus == 0.0) and a TEXT sub-clause
        (literal == '0.0'). Deleting either alone leaves the other to catch
        a nonzero lod; deleting both together lets 1.0 through to the
        identity hash."""
        module = _module()
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "textureLod(inputTex, localUV, 0.0)",
            "textureLod(inputTex, localUV, 1.0)")
        candidate = _analyzed(raw=raw)
        overrides = {}
        overrides.update(_recount(module, candidate))
        overrides.update(module._resite(candidate, {2: -1}))
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks,
                "textureLod site shape mismatch")
        for pair in (("_lod_value_holds",), ("_lod_text_holds",),
                     ("_lod_value_holds", "_lod_text_holds")):
            with self.subTest(deleted=pair):
                scratch = _scratch(module, *pair)
                with mock.patch.object(scratch, "_LOCKS", locks):
                    try:
                        scratch.authenticate_texture_lod_admission(
                            candidate, locks[KEY]["raw_sha256"], PROFILE)
                        survived = None
                    except ValueError as error:
                        survived = str(error)
                if pair == ("_lod_value_holds", "_lod_text_holds"):
                    self.assertIsNotNone(
                        survived,
                        "deleting both lod sub-clauses must leave the "
                        "identity hash to catch the mutant")
                    self.assertIn("textureLod site identity mismatch",
                                  survived)
                else:
                    self.assertIn("textureLod site shape mismatch", survived)

    def test_texture_family_census_lock(self):
        module = _module()
        program = _analyzed()
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["texture_size_sites"] = locks[KEY][
            "texture_size_sites"][:-1]
        _expect(self, module, program, locks,
                "texture-family census mismatch")
        scratch = _scratch(module, "_texture_family_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_texture_lod_admission(
                program, RAW_SHA256, PROFILE)

    def test_mechanism_census_lock(self):
        module = _module()
        program = _analyzed()
        self.assertTrue(
            module._mechanism_census_holds(program, module._LOCKS[KEY]))
        locks = copy.deepcopy(module._LOCKS)
        locks[KEY]["mechanism_census"] = (0, 0, 0, 1)
        _expect(self, module, program, locks, "mechanism census mismatch")
        scratch = _scratch(module, "_mechanism_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            scratch.authenticate_texture_lod_admission(
                program, RAW_SHA256, PROFILE)


class LedgerSabotageTests(unittest.TestCase):
    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(LEDGER, module._CONSUMED_LEDGER)
        proof = module.authenticate_texture_lod_admission(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(2, len(proof.sites))
        for sabotage in (LEDGER - 1, LEDGER + 1):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "textureLod admission visitation ledger mismatch"):
                module.authenticate_texture_lod_admission(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(2, len(
            module.authenticate_texture_lod_admission(
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


class ParallaxLaneExtensionTests(unittest.TestCase):
    """The parallax lane's own additions on top of the restored parked file:
    the two guard messages the parked file never fired end-to-end (the
    defines lock and the seed-write lock), the march-loop start operand, the
    frozen alias/contract constants, the _resite companion contract, and the
    landed/prepared wiring sweep across the whole tool tree."""

    def test_define_drift_fails_the_exact_define_lock(self):
        module = _module()
        candidate = dataclasses.replace(
            _analyzed(),
            preprocessor_defines=(PreprocessorDefine("NOISE_TYPE", "int",
                                                     "10"),))
        _expect(self, module, candidate, _relocked(module, candidate),
                "exact preprocessor define lock mismatch")
        scratch = _scratch(module, "_defines_hold")
        with mock.patch.object(scratch, "_LOCKS", _relocked(module, candidate)):
            scratch.authenticate_texture_lod_admission(
                candidate, RAW_SHA256, PROFILE)

    def test_an_unanalyzed_body_status_fails_the_normalized_lock(self):
        """The `body_status == "analyzed"` sub-clause is its own arm: a
        program whose body was never analyzed must not authenticate even
        with byte-identical sources."""
        module = _module()
        candidate = dataclasses.replace(_analyzed(), body_status="parsed")
        locks = _relocked(module, candidate)
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_texture_lod_admission(
                candidate, RAW_SHA256, PROFILE)

    def test_seed_write_lock_fires_end_to_end(self):
        """The parked file proves the predicate directly; this drives the
        same forged seed reference through the full gate so the guard
        message itself is exercised (a seed id planted outside main's two
        frozen reads is refused before the reads census can absorb it)."""
        module = _module()
        candidate = _analyzed()
        writer = next(f for f in candidate.functions
                      if f.name == "getLuminosity")
        statement = writer.body[0]
        call = statement.expressions[0]
        forged = dataclasses.replace(
            call,
            children=(dataclasses.replace(call.children[0],
                                          symbol_id=MARCH_SYMBOL_ID),
                      call.children[1]))
        object.__setattr__(statement, "expressions", (forged,))
        locks = _relocked(module, candidate)
        _expect(self, module, candidate, locks,
                "counted-for bound seed write census mismatch")
        scratch = _scratch(module, "_no_seed_write_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn("counted-for bound seed write census mismatch",
                             survived,
                             "deleting _no_seed_write_holds did not remove "
                             "its message")

    def test_march_loop_start_lock(self):
        """The start operand `int i = 1` is load-bearing the same way the
        comparison is: 1 -> 2 shrinks the trip count to 31 while every span
        stays put (same length), so the march lock itself must catch it."""
        raw = SOURCE.read_text(encoding="utf-8").replace(
            "int i = 1;", "int i = 2;")
        candidate = _analyzed(raw=raw)
        summary = candidate.counted_loop_proof
        self.assertEqual((1, 0, 1, 31, 31, True),
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))
        self._delete_march_start(candidate)

    def _delete_march_start(self, candidate):
        module = _module()
        overrides = _recount(module, candidate)
        locks = _relocked(module, candidate, **overrides)
        _expect(self, module, candidate, locks,
                "counted-for march loop profile mismatch")
        scratch = _scratch(module, "_march_loop_holds")
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_texture_lod_admission(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn("counted-for march loop profile mismatch",
                             survived,
                             "deleting _march_loop_holds did not remove its "
                             "message")

    def test_the_alias_contract_and_invariant_note_are_frozen(self):
        module = _module()
        self.assertEqual(
            ("textureLod(sampler, coord, lod) == texture(sampler, coord)",),
            module.LOWERING_CONTRACT)
        self.assertEqual(
            "texture: (surface, coord) => this.#texture(surface, coord)",
            module.JS_TEXTURE_LINE)
        self.assertEqual("src/csl/glsl-runtime.js:399", module.JS_TEXTURE_SITE)
        self.assertEqual("source-global-literal-int-v1", module.SEED_CAPABILITY)
        self.assertIn("invariance witness", module.JS_LOD_INVARIANT_NOTE)
        self.assertIn("lod is dropped", module.JS_LOD_INVARIANT_NOTE)

    def test_resite_keeps_the_frozen_identity_hashes(self):
        """`_resite` is the site-value mutation tests' refreeze companion:
        semantic columns re-derived from the candidate, identity hashes kept
        frozen, sampler ids remapped only through the explicit map."""
        module = _module()
        program = _analyzed()
        frozen = module._LOCKS[KEY]["lod_sites"]
        self.assertEqual({"lod_sites": frozen}, module._resite(program, {}))
        resited = module._resite(program, {2: -1})["lod_sites"]
        self.assertEqual((-1, 1), tuple(site[3] for site in resited))
        self.assertEqual(tuple(site[-1] for site in frozen),
                         tuple(site[-1] for site in resited))

    def test_landed_wiring_is_exactly_the_two_authorities(self):
        """LANDED: exactly the two authorities under tools/glslcpp reference
        the module (never a third file), so a stray import cannot appear
        unnoticed."""
        module = _module()
        offenders = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "tools/glslcpp").rglob("*.py")
            if "__pycache__" not in path.parts
            and path.name != "texture_lod_admission_profile.py"
            and "texture_lod_admission" in path.read_text(encoding="utf-8")]
        self.assertEqual(
            ["tools/glslcpp/emit_typed_cpp.py",
             "tools/glslcpp/generate_typed_slice.py"],
            sorted(offenders))

    def test_seed_contract_refuses_a_foreign_key(self):
        module = _module()
        with self.assertRaises(ValueError) as raised:
            module.counted_for_seed_contract("test:foreign")
        self.assertIn(
            f"{PROFILE}: test:foreign is not an admitted textureLod "
            "admission carrier",
            str(raised.exception))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
