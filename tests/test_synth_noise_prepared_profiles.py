"""Focused RED/GREEN proof for synth/noise's four counted-for carriers.

The four records (counted-for design §5 F/G/H/I, wave 2):

* ``runtime_loop_bound_profile`` -- LANDED in-module: ``synth/noise:noise`` is
  the module's fourth live key, a tetra-shaped parameter-bounded record whose
  loop census names *the one loop that is unproved or carries this record's
  runtime seed* -- fresh it must match the frozen span and node hash, seeded
  it must match the contract's exact eight-trip proof shape -- instead of
  requiring the program to contain exactly one loop, so canonically proved
  companions (classicNoisedeck/noise's two literal 3-trip sRGB loops) are
  admissible and re-application holds.
* ``mutable_global_frame_profile`` -- LANDED second key
  (``mutable-global-frame-noise-v1``), coupled to the runtime-loop and
  scalar-XOR profiles on the exact row.
* ``scalar_uint_xor_profile`` -- LANDED seventh record plus the program's
  one ``floatBitsToUint`` ingress (the kaleido in-module precedent shape).
  The live seven-key census and the ingress identity are both frozen.

Every figure below was re-derived this session against the pinned corpus and
the JS snapshot (``canonicalFactory265``, ``canonical-kernels.js:31929`` /
registered ``:36445``; ``Function.prototype.toString`` SHA-256
``392c3be9936855debc0956bc41e4b658896ccdd673674a2ad983101aac521e14``;
factory-scope ``var globalCoord = new Float32Array([0, 0]);`` at :31959,
main's first-statement per-lane write at :32388, the two reads at :32390 and
:diamonds :32265).  The frame, XOR and ingress records freeze the
POST-runtime-loop-bound tree because ``generate_typed_slice`` applies that
carrier first; the runtime record itself freezes the proof-free
cleared-function digests, exactly as tetra's does.

RED evidence: against a scratch copy of ``tools/glslcpp`` whose three profile
modules are reverted to ``HEAD``, every test in this file fails with
``AttributeError`` on the new module attributes (the lane's run log under
``$RUN_ROOT/workers/synthnoise`` records the output).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import unittest
from unittest import mock

from tools.glslcpp import check_corpus, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/noise:noise"
FRAME_PROFILE = "mutable-global-frame-noise-v1"

RAW_SHA256 = "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274"

# The coarse gate messages, in evaluation order. A local lock that fires with
# one of these did not test what its name claims.
COARSE = (
    "exact caller source hash required",
    "exact preprocessor define lock mismatch",
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
    "source, define, function, whole-program, or interface mismatch",
    "source or define profile mismatch",
    "interface, function, or call-graph profile mismatch",
)


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _manifest():
    corpus = check_corpus._corpus_root(REPOSITORY)
    return corpus, json.loads((corpus / "manifest.json").read_text())


def _entry(key: str = KEY):
    corpus, manifest = _manifest()
    return corpus, next(item for item in manifest["programs"]
                        if item["program_key"] == key)


def _raw() -> str:
    corpus, entry = _entry()
    return (corpus / entry["source"]).read_text()


def _program():
    raw = _raw()
    defines = generate_typed_slice._defaults(REPOSITORY, KEY)
    return (hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            analyze_program(parse_program(raw, KEY, defines), KEY))


def _attached():
    from tools.glslcpp.frontend.runtime_loop_bound_profile import (
        PROFILE, apply_runtime_loop_bound)
    source_hash, program = _program()
    return source_hash, apply_runtime_loop_bound(
        program, source_hash, PROFILE)


def _walk_expression(value):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _replace_expression(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(
        value, children=tuple(_replace_expression(child, target, replacement)
                              for child in value.children))


def _replace_statement(value, target, replacement):
    return dataclasses.replace(
        value,
        expressions=tuple(_replace_expression(item, target, replacement)
                          for item in value.expressions),
        children=tuple(_replace_statement(item, target, replacement)
                       for item in value.children))


def _replace_in_program(program, target, replacement):
    return dataclasses.replace(
        program,
        functions=tuple(dataclasses.replace(
            function,
            body=tuple(_replace_statement(item, target, replacement)
                       for item in function.body))
            for function in program.functions))


def _function(program, name):
    return next(item for item in program.functions if item.name == name)


def _foreign_proof():
    """A non-None fixed-array proof borrowed from cellRefract (presence only)."""
    from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
        attach_fixed_array_in_parameter_proof)
    corpus, entry = _entry("classicNoisedeck/cellRefract:cellRefract")
    raw = (corpus / entry["source"]).read_text()
    key = "classicNoisedeck/cellRefract:cellRefract"
    defines = generate_typed_slice._defaults(REPOSITORY, key)
    program = analyze_program(parse_program(raw, key, defines), key)
    proof = attach_fixed_array_in_parameter_proof(
        program).fixed_array_in_parameter_proof
    assert proof is not None
    return proof


def _frame_relocked(module, candidate, **overrides):
    """A fresh live lock with only the coarse digest fields refrozen."""
    import copy
    lock = copy.deepcopy(module._LOCKS[KEY])
    for name, value in (
            ("functions_sha256", module._sha(candidate.functions)),
            ("whole_sha256", module._whole(candidate)),
            ("interface_sha256", module._interface(candidate))):
        lock[name] = value
    lock.update(overrides)
    return {KEY: lock}


def _rlb_relocked(module, candidate, **overrides):
    """A fresh runtime record with the cleared-function digests refrozen."""
    import copy
    record = copy.deepcopy(module._NOISE_EXPECTED)
    functions = module._cleared_functions(candidate)
    whole = (candidate.key, candidate.source, candidate.raw_source,
             candidate.declarations, functions, candidate.resources,
             candidate.body_status, candidate.local_type_names,
             candidate.structs, candidate.uniform_blocks,
             candidate.interface_symbols, candidate.builtin_symbols,
             candidate.preprocessor_defines)
    interface = (candidate.declarations, candidate.resources,
                 candidate.local_type_names, candidate.structs,
                 candidate.uniform_blocks, candidate.interface_symbols,
                 candidate.builtin_symbols, candidate.preprocessor_defines)
    record["functions_sha256"] = module._sha(functions)
    record["whole_program_sha256"] = module._sha(whole)
    record["interface_sha256"] = module._sha(interface)
    record.update(overrides)
    return record


def _xor_relocked(module, candidate, keep=()):
    """Refreeze every digest the live XOR record checks, except ``keep``.

    ``keep`` names the fields that must STAY frozen at the authentic values --
    deleting them from the refreeze is how a test proves the corresponding
    exact lock is an independent barrier behind the coarse gate.
    """
    record = dict(module._PROFILES[KEY])
    xors, parents, owners, calls = module._collect(candidate)
    parent = parents.get(id(xors[0])) if xors else None
    owner = owners[id(xors[0])] if xors else None
    inventory = tuple(
        (f.signature.id, f.name, f.return_type.display(),
         len(f.parameters), len(f.body), module._span(f))
        for f in candidate.functions)
    parameters = tuple((q.id, q.name, q.type.display(), q.direction)
                       for q in owner.parameters)
    cg_calls = {f.signature.id: [] for f in candidate.functions}
    for f in candidate.functions:
        for statement in f.body:
            for value, _ in module._walk_statement(statement):
                if value.kind == "call" and value.signature_id is not None:
                    cg_calls[f.signature.id].append(value.signature_id)
    call_graph = tuple((f.signature.id, tuple(cg_calls[f.signature.id]))
                       for f in candidate.functions)
    values = {
        "functions_sha256": module._sha(candidate.functions),
        "whole_program_sha256": module._whole_program_fingerprint(candidate),
        "interface_sha256": module._interface_fingerprint(candidate),
        "function_inventory_sha256": module._sha(inventory),
        "owner": (owner.signature.id, owner.name,
                  owner.return_type.display(), len(owner.parameters),
                  len(owner.body), module._span(owner), module._sha(owner),
                  module._sha(parameters)),
        "parent": (module._span(parent), module._sha(parent)),
        "sites": tuple((module._span(v), module._sha(v),
                        module._sha(v.children[0]), module._sha(v.children[1]),
                        index) for index, v in enumerate(xors)),
        "scalar_census_sha256": module._scalar_census_fingerprint(
            candidate, parent),
        "call_graph_sha256": module._sha(call_graph),
    }
    for name in keep:
        values.pop(name, None)
    record.update(values)
    return record


class NoiseRuntimeLoopBoundRecordTests(unittest.TestCase):
    """The LANDED fourth key of runtime_loop_bound_profile."""

    def test_noise_is_a_live_carrier_and_the_module_surface_grew(self) -> None:
        from tools.glslcpp.frontend import runtime_loop_bound_profile as module
        self.assertEqual(KEY, module.NOISE_KEY)
        self.assertIn(module.NOISE_KEY, module.RUNTIME_LOOP_BOUND_KEYS)
        self.assertEqual((), module.PREPARED_RUNTIME_LOOP_BOUND_KEYS)
        self.assertEqual(frozenset({module.TETRA_KEY, module.STATS_KEY,
                                    module.NOISE_KEY, *module.BLUR_KEYS}),
                         module.RUNTIME_LOOP_BOUND_KEYS)
        for name in ("NOISE_KEY", "validate_noise_metadata"):
            self.assertIn(name, module.__all__)

    def test_fresh_analysis_is_unproved_and_the_seed_proves_eight_trips(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, apply_runtime_loop_bound)
        source_hash, program = _program()
        self.assertEqual((0, 1),
                         (program.counted_loop_proof.loop_count,
                          program.counted_loop_proof.unproved_loop_count))
        attached = apply_runtime_loop_bound(program, source_hash, PROFILE)
        summary = attached.counted_loop_proof
        self.assertEqual((1, 0, 1, 8, 8, True),
                         (summary.loop_count, summary.unproved_loop_count,
                          summary.max_effective_depth,
                          summary.max_lexical_product,
                          summary.entrypoint_charge,
                          summary.call_graph_acyclic))
        loop = None

        def statements(value):
            yield value
            for child in value.children:
                yield from statements(child)

        for statement in _function(attached, "multires").body:
            for value in statements(statement):
                if getattr(value, "loop_proof", None) is not None:
                    loop = value
        proof = loop.loop_proof
        self.assertEqual((1, 8, "<=", "++", 8,
                          "runtime-metadata-uniform-direct-parameter"),
                         (proof.start_value, proof.bound_value,
                          proof.comparison, proof.update, proof.trip_count,
                          proof.bound_kind))
        # The record reads the proof-cleared tree, so re-application holds.
        again = apply_runtime_loop_bound(attached, source_hash, PROFILE)
        self.assertEqual((1, 0, 1, 8, 8, True),
                         (again.counted_loop_proof.loop_count,
                          again.counted_loop_proof.unproved_loop_count,
                          again.counted_loop_proof.max_effective_depth,
                          again.counted_loop_proof.max_lexical_product,
                          again.counted_loop_proof.entrypoint_charge,
                          again.counted_loop_proof.call_graph_acyclic))

    def test_the_contract_and_guard_share_one_maximum(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound)
        source_hash, program = _program()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        self.assertEqual(KEY, contract.key)
        self.assertEqual(("integer-range", "octaves", 1, 8, 2, 8),
                         (contract.kind, contract.uniform_name,
                          contract.minimum, contract.uniform_maximum,
                          contract.default, contract.maximum))
        self.assertEqual(8, contract.seed.maximum)
        self.assertEqual("runtime-metadata-uniform-direct-parameter",
                         contract.seed.provenance)
        self.assertEqual(f"{KEY} octaves must be in [1,8]",
                         contract.binding_error)
        # The seeded parameter is multires' third of five.
        multires = _function(program, "multires")
        self.assertEqual((101, "oct"),
                         (contract.seed.symbol_id, contract.seed.symbol.name))
        self.assertIs(multires.parameters[2], contract.seed.symbol)

    def test_metadata_contract_is_exact(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            validate_noise_metadata)
        corpus, _ = _manifest()
        metadata = check_corpus._load_json(corpus / "metadata.json", "metadata")
        effect = metadata["effects"]["synth/noise"]
        validate_noise_metadata(effect)
        for field, value in (("type", "float"), ("min", 2), ("default", 3),
                             ("max", 7)):
            forged = json.loads(json.dumps(effect))
            forged["params"]["octaves"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "metadata contract mismatch"):
                validate_noise_metadata(forged)
        with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
            validate_noise_metadata({"params": {}})
        with self.assertRaisesRegex(ValueError, "metadata contract mismatch"):
            validate_noise_metadata(None)

    def test_carrier_boundaries_are_closed(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound)
        source_hash, program = _program()
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            authenticate_runtime_loop_bound(program, source_hash, None)
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            authenticate_runtime_loop_bound(program, source_hash, "wrong")
        with self.assertRaisesRegex(
                ValueError, "source or define profile mismatch"):
            authenticate_runtime_loop_bound(program, "0" * 64, PROFILE)
        with self.assertRaisesRegex(
                ValueError, "source or define profile mismatch"):
            authenticate_runtime_loop_bound(
                dataclasses.replace(program, preprocessor_defines=()),
                source_hash, PROFILE)
        with self.assertRaisesRegex(
                ValueError, "source or define profile mismatch"):
            authenticate_runtime_loop_bound(
                dataclasses.replace(program, raw_source="x" * 18131),
                source_hash, PROFILE)
        foreign = dataclasses.replace(program, key="foreign:key")
        with self.assertRaisesRegex(ValueError, "profile on foreign key"):
            authenticate_runtime_loop_bound(foreign, source_hash, PROFILE)

    def test_identity_mutations_fail_the_exact_locks_not_the_coarse_gate(self) -> None:
        from tools.glslcpp.frontend import runtime_loop_bound_profile as module
        source_hash, program = _program()
        call = None
        for statement in _function(program, "main").body:
            for value in _walk_statement(statement):
                if (value.kind == "call"
                        and _function(program, "multires").signature.id
                        == value.signature_id):
                    call = value
        # Argument swapped for its neighbour: octaves is no longer third.
        swapped = _replace_in_program(program, call.children[2],
                                      call.children[3])
        with mock.patch.dict({"x": 1}):  # keep context managers symmetric
            pass
        with mock.patch.object(module, "_NOISE_EXPECTED",
                               _rlb_relocked(module, swapped)):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_runtime_loop_bound(
                    swapped, source_hash, module.PROFILE)
        self.assertIn("call-site profile mismatch", str(raised.exception))
        for coarse in COARSE:
            self.assertNotIn(coarse, str(raised.exception))

        # A duplicate of the octaves argument in a foreign slot.
        duplicated = _replace_in_program(program, call.children[3],
                                         call.children[2])
        with mock.patch.object(module, "_NOISE_EXPECTED",
                               _rlb_relocked(module, duplicated)):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_runtime_loop_bound(
                    duplicated, source_hash, module.PROFILE)
        self.assertIn("call-site profile mismatch", str(raised.exception))

    def test_parameter_reassignment_fails_closed(self) -> None:
        from tools.glslcpp.frontend import runtime_loop_bound_profile as module
        source_hash, program = _program()
        multires = _function(program, "multires")
        main = _function(program, "main")
        loop = next(statement for statement in multires.body
                    if statement.kind == "for")
        oct_id = loop.expressions[0].children[1]
        write = next(value for statement in main.body
                     for value in _walk_statement(statement)
                     if value.kind == "assign"
                     and value.children[0].symbol_id == 15)
        graft = dataclasses.replace(write, children=(oct_id, write.children[1]))
        carrying = dataclasses.replace(
            program, functions=tuple(
                function if function is not multires
                else dataclasses.replace(function, body=(
                    *function.body,
                    dataclasses.replace(loop, kind="expr", children=(),
                                        expressions=(graft,))))
                for function in program.functions))
        with mock.patch.object(module, "_NOISE_EXPECTED",
                               _rlb_relocked(module, carrying)):
            with self.assertRaisesRegex(
                    ValueError, "helper parameter reassignment"):
                module.authenticate_runtime_loop_bound(
                    carrying, source_hash, module.PROFILE)

    def test_the_loop_census_names_the_unproved_loop(self) -> None:
        """A second unproved loop rejects behind fully refrozen coarse hashes.

        This is the lock the design said must generalize tetra's "exactly one
        loop in the program": classicNoisedeck/noise carries two PROVED loops
        beside its unproved one, which this census must tolerate, while a
        second unproved loop anywhere is fatal.
        """
        from tools.glslcpp.frontend import runtime_loop_bound_profile as module
        source_hash, program = _program()
        multires = _function(program, "multires")
        main = _function(program, "main")
        loop = next(statement for statement in multires.body
                    if statement.kind == "for")
        grafted = dataclasses.replace(
            program, functions=tuple(
                function if function is not main
                else dataclasses.replace(function, body=(
                    loop, *function.body))
                for function in program.functions))
        with mock.patch.object(module, "_NOISE_EXPECTED",
                               _rlb_relocked(module, grafted)):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_runtime_loop_bound(
                    grafted, source_hash, module.PROFILE)
        self.assertIn("loop-site profile mismatch", str(raised.exception))
        for coarse in COARSE:
            self.assertNotIn(coarse, str(raised.exception))

    def test_forged_contracts_fail_the_recheck(self) -> None:
        from tools.glslcpp.frontend.runtime_loop_bound_profile import (
            PROFILE, authenticate_runtime_loop_bound,
            validate_runtime_loop_contract)
        source_hash, program = _program()
        contract = authenticate_runtime_loop_bound(program, source_hash, PROFILE)
        validate_runtime_loop_contract(contract)
        for forged in (
                dataclasses.replace(contract, uniform_name="octave"),
                dataclasses.replace(contract, minimum=2),
                dataclasses.replace(contract, default=6),
                dataclasses.replace(contract, uniform_maximum=6),
                dataclasses.replace(contract, kind="blur-radius"),
                dataclasses.replace(
                    contract,
                    seed=dataclasses.replace(contract.seed, maximum=7))):
            with self.subTest(forged=forged), self.assertRaisesRegex(
                    ValueError, "malformed authenticated runtime contract"):
                validate_runtime_loop_contract(forged)


class NoiseLandedSliceTests(unittest.TestCase):
    def test_exact_row_and_live_key_lock_are_landed(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as frame
        from tools.glslcpp.frontend import scalar_uint_xor_profile as xor

        spec = generate_typed_slice.load_slice(REPOSITORY)
        keys = [row["program_key"] for row in spec["programs"]]
        # Live pin repinned 2026-08-25 from the tree: the DSL phase landed the
                # slice at 211 typed rows. Measured, never carried from a report; see
                # task-7-typed-generator-census-repair.md.
        self.assertEqual(211, len(keys))
        self.assertEqual(200, keys.index(KEY))
        self.assertEqual(
            "29a148b26cfe4f550ac82325810655eb0e5ffad2c3a4e5241e42600bac9f76c1",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            {"defines": {"LOOP_OFFSET": 300, "NOISE_TYPE": 10},
             "mutable_global_frame_profile": FRAME_PROFILE,
             "program_key": KEY,
             "runtime_define_profile": "runtime-defines-noise-v1",
             "runtime_loop_bound_profile": "runtime-loop-bound-v1",
             "scalar_uint_xor_profile": "scalar-uint-xor-v1"},
            spec["programs"][200])
        self.assertEqual(frozenset(), frame.PREPARED_MUTABLE_GLOBAL_FRAME_KEYS)
        self.assertEqual(frozenset(), xor.PREPARED_SCALAR_UINT_XOR_KEYS)


class LandedFrameNoiseTests(unittest.TestCase):
    """The landed second key of mutable_global_frame_profile."""

    def test_the_live_census_contains_shape_and_noise(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        self.assertEqual((module.SHAPE_KEY, module.NOISE_KEY), module.KEYS)
        self.assertEqual({module.SHAPE_KEY: module.SHAPE_PROFILE,
                          module.NOISE_KEY: module.NOISE_PROFILE},
                         module.PROFILES)
        self.assertEqual(frozenset({module.SHAPE_KEY, module.NOISE_KEY}),
                         module.MUTABLE_GLOBAL_FRAME_KEYS)
        self.assertEqual(frozenset({module.SHAPE_KEY, module.NOISE_KEY}),
                         frozenset(module.ALLOWED_ROW_FIELDS))
        self.assertEqual(frozenset({module.SHAPE_KEY, module.NOISE_KEY}),
                         frozenset(module.REQUIRED_COMPANION_PROFILES))
        self.assertEqual(frozenset(),
                         module.PREPARED_MUTABLE_GLOBAL_FRAME_KEYS)
        self.assertEqual(module.NOISE_PROFILE, FRAME_PROFILE)

    def test_the_frozen_source_path_names_the_authenticated_file(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        lock = module._LOCKS[KEY]
        corpus, _ = _manifest()
        raw = (corpus / "sources" / lock["source_path"]).read_bytes()
        self.assertEqual(lock["raw_bytes"], len(raw))
        self.assertEqual(RAW_SHA256, lock["raw_sha256"])
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())

    def test_authenticates_the_post_runtime_loop_bound_program(self) -> None:
        from tools.glslcpp.frontend.mutable_global_frame_profile import (
            authenticate_mutable_global_frame, frame_contract)
        source_hash, attached = _attached()
        admitted, = authenticate_mutable_global_frame(
            attached, source_hash, FRAME_PROFILE)
        self.assertEqual((15, "globalCoord", "vec2", "global", None),
                         (admitted.symbol.id, admitted.symbol.name,
                          admitted.type.display(), admitted.symbol.storage,
                          admitted.initializer))
        contract = frame_contract(KEY)
        field, = contract.fields
        self.assertEqual(
            ("globalCoord", "vec2", "glsl::Vec2", 2, "per-lane-f32",
             "new Float32Array([0, 0])", "float32-array"),
            (field.name, field.glsl_type, field.native_type,
             field.lane_count, field.narrowing, field.js_initializer,
             field.js_number_kind))
        self.assertEqual(("Frame", "frame", "pixel", True,
                          "const Frame& frame", "const Frame&", 2, "main"),
                         (contract.struct_name, contract.instance_name,
                          contract.instance_scope, contract.value_initialized,
                          contract.helper_parameter,
                          contract.helper_parameter_qualifier,
                          contract.helper_parameter_ordinal,
                          contract.writer_function))

    def test_the_write_is_mains_first_statement_and_the_reads_are_two(self) -> None:
        from tools.glslcpp.frontend.mutable_global_frame_profile import (
            _LOCKS)
        source_hash, attached = _attached()
        lock = _LOCKS[KEY]
        write, = lock["writes"]
        self.assertEqual((117, "main", 0, "expr", "279:5-279:16"),
                         (write.owner_id, write.owner_name,
                          write.statement_index, write.statement_kind,
                          write.target_span))
        self.assertEqual(2, len(lock["reads"]))
        self.assertEqual({("diamonds", "220:10-220:21"),
                          ("main", "281:15-281:26")},
                         {(read.owner_name, read.span) for read in lock["reads"]})
        for read in lock["reads"]:
            self.assertEqual(read.owner_id,
                             _function(attached, read.owner_name).id)
        # `diamonds` is unreachable at the frozen defines (dead-code class).
        self.assertIn(_function(attached, "diamonds").id, lock["unreachable"])
        self.assertEqual((1, 0, 1, 8, 8, True), lock["counted_loop_proof"])

    def test_boundaries_are_closed(self) -> None:
        from tools.glslcpp.frontend.mutable_global_frame_profile import (
            authenticate_mutable_global_frame)
        source_hash, attached = _attached()
        fresh_hash, fresh = _program()
        with self.assertRaisesRegex(
                ValueError, "typed function fingerprint drift"):
            authenticate_mutable_global_frame(
                fresh, fresh_hash, FRAME_PROFILE)
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            authenticate_mutable_global_frame(
                attached, source_hash, "mutable-global-frame-shape-v1")
        with self.assertRaisesRegex(
                ValueError, "exact caller source hash required"):
            authenticate_mutable_global_frame(
                attached, "0" * 64, FRAME_PROFILE)
        foreign = dataclasses.replace(attached, key="foreign:key")
        self.assertEqual((), authenticate_mutable_global_frame(
            foreign, source_hash, None))
        with self.assertRaisesRegex(
                ValueError, "not an admitted mutable-global frame carrier"):
            authenticate_mutable_global_frame(
                foreign, source_hash, FRAME_PROFILE)

    def test_unrelated_proof_carriers_are_rejected(self) -> None:
        from tools.glslcpp.frontend.mutable_global_frame_profile import (
            authenticate_mutable_global_frame)
        source_hash, attached = _attached()
        carrying = dataclasses.replace(
            attached, fixed_array_in_parameter_proof=_foreign_proof())
        with self.assertRaisesRegex(
                ValueError, "unrelated proof carrier is not absent"):
            authenticate_mutable_global_frame(
                carrying, source_hash, FRAME_PROFILE)

    def test_storage_initializer_and_adjacency_locks(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        source_hash, attached = _attached()
        record = module._LOCKS[KEY]["admitted"][0]
        decl = next(d for d in attached.declarations
                    if d.symbol.id == record.symbol_id)
        main = _function(attached, "main")
        write = next(value for statement in main.body
                     for value in _walk_statement(statement)
                     if value.kind == "assign"
                     and value.children[0].symbol_id == 15)

        initialized = dataclasses.replace(
            attached, declarations=tuple(
                dataclasses.replace(d, initializer=write)
                if d.symbol.id == 15 else d
                for d in attached.declarations))
        with mock.patch.object(module, "_LOCKS",
                               _frame_relocked(module, initialized)):
            with self.assertRaisesRegex(
                    ValueError, "carries an initializer"):
                module.authenticate_mutable_global_frame(
                    initialized, source_hash, FRAME_PROFILE)

        relocated = (attached.declarations[:13]
                     + (attached.declarations[14], attached.declarations[13]))
        moved = dataclasses.replace(attached, declarations=relocated)
        with mock.patch.object(module, "_LOCKS",
                               _frame_relocked(module, moved)):
            with self.assertRaisesRegex(
                    ValueError, "ordinal or adjacency mismatch"):
                module.authenticate_mutable_global_frame(
                    moved, source_hash, FRAME_PROFILE)

    def test_write_position_and_dominance_locks(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        source_hash, attached = _attached()
        main = _function(attached, "main")
        swapped = dataclasses.replace(
            attached, functions=tuple(
                function if function.name != "main"
                else dataclasses.replace(function, body=(
                    main.body[1], main.body[0], *main.body[2:]))
                for function in attached.functions))
        with mock.patch.object(module, "_LOCKS",
                               _frame_relocked(module, swapped)):
            with self.assertRaisesRegex(
                    ValueError, "write position mismatch"):
                module.authenticate_mutable_global_frame(
                    swapped, source_hash, FRAME_PROFILE)

    def test_read_identity_survives_a_coarse_hash_bypass(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        source_hash, attached = _attached()
        read = next(value for statement in _function(attached, "main").body
                    for value in _walk_statement(statement)
                    if value.symbol_id == 15 and value.kind == "id"
                    and _span(value).startswith("281:"))
        # A value-level mutation that shifts the node digest but nothing the
        # coarse gate owns: the house mutates `category` on rvalue nodes; an
        # `id` read is already an lvalue, so the equivalent field is
        # `literal`.
        mutated = _replace_in_program(
            attached, read, dataclasses.replace(read, literal="mutated"))
        with mock.patch.object(module, "_LOCKS",
                               _frame_relocked(module, mutated)):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_mutable_global_frame(
                    mutated, source_hash, FRAME_PROFILE)
        self.assertIn("read identity mismatch", str(raised.exception))
        for coarse in COARSE:
            self.assertNotIn(coarse, str(raised.exception))

    def test_the_consumed_ledger_runs_and_counts_seven(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        source_hash, attached = _attached()
        self.assertEqual(7, module._LOCKS[KEY]["consumed_ledger"])
        with mock.patch.object(module, "_LOCKS",
                               _frame_relocked(module, attached,
                                               consumed_ledger=6)):
            with self.assertRaisesRegex(
                    ValueError, "visitation ledger mismatch"):
                module.authenticate_mutable_global_frame(
                    attached, source_hash, FRAME_PROFILE)


class LandedScalarUintXorNoiseTests(unittest.TestCase):
    """The landed seventh record of scalar_uint_xor_profile."""

    def test_the_live_seven_key_census_contains_noise(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        self.assertEqual(7, len(module.SCALAR_UINT_XOR_KEYS))
        self.assertIn(KEY, module.SCALAR_UINT_XOR_KEYS)
        self.assertEqual(frozenset(),
                         module.PREPARED_SCALAR_UINT_XOR_KEYS)
        self.assertEqual(KEY, module.NOISE_INGRESS_KEY)

    def test_authenticates_three_lanes_in_order(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)
        source_hash, attached = _attached()
        sites = authenticate_scalar_uint_xor(
            attached, source_hash, PROFILE)
        self.assertEqual(3, len(sites))
        self.assertEqual(
            [("binary", "^", "rvalue", ["uint", "uint"])] * 3,
            [(site.kind, site.operator, site.category,
              [child.type.display() for child in site.children])
             for site in sites])
        self.assertEqual(("97:10", "98:10", "99:10"),
                         tuple(_span(site)[:5] for site in sites))
        owner = _function(attached, "constantFromLatticeWithOffset")
        for site in sites:
            found = False
            for statement in owner.body:
                for value in _walk_statement(statement):
                    if value is site:
                        found = True
            self.assertTrue(found)

    def test_the_owner_is_recorded_as_unreachable(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        record = module._PROFILES[KEY]
        self.assertEqual("unreachable", record["owner_reachability"])
        # ...and every sibling live carrier keeps the reachable default
        # implicitly. Noise is the one admitted unreachable-owner record.
        for key, live in module._PROFILES.items():
            if key == KEY:
                continue
            self.assertNotIn("owner_reachability", live)

    def test_boundaries_are_closed(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)
        source_hash, attached = _attached()
        fresh_hash, fresh = _program()
        with self.assertRaises(ValueError):
            authenticate_scalar_uint_xor(fresh, fresh_hash, PROFILE)
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            authenticate_scalar_uint_xor(attached, source_hash, None)
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            authenticate_scalar_uint_xor(attached, source_hash, "wrong")
        with self.assertRaises(ValueError):
            authenticate_scalar_uint_xor(attached, "0" * 64, PROFILE)
        foreign = dataclasses.replace(attached, key="foreign:key")
        self.assertEqual((), authenticate_scalar_uint_xor(
            foreign, source_hash, None))
        with self.assertRaises(ValueError):
            authenticate_scalar_uint_xor(foreign, source_hash, PROFILE)

    def test_absent_proof_carriers_are_rejected(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)
        source_hash, attached = _attached()
        proof = _foreign_proof()
        for field in ("fixed_nine_table_proof",
                      "fixed_grid_counter_store_proof",
                      "fixed_array_in_parameter_proof",
                      "fixed_affine_centers13_proof"):
            with self.subTest(field=field):
                carrying = dataclasses.replace(attached, **{field: proof})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    authenticate_scalar_uint_xor(
                        carrying, source_hash, PROFILE)

    def test_site_mutations_reject(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_scalar_uint_xor)
        from tools.glslcpp.frontend.semantic_types import INT
        source_hash, attached = _attached()
        sites = authenticate_scalar_uint_xor(
            attached, source_hash, PROFILE)
        parent = next(
            value for function in attached.functions
            for statement in function.body
            for value in _walk_statement(statement)
            if len(value.children) == 3
            and all(value.children[index] is sites[index]
                    for index in range(3)))
        mutations = {
            "missing": _replace_in_program(
                attached, sites[0], sites[0].children[0]),
            "duplicate": _replace_in_program(attached, sites[1], sites[0]),
            "reordered": _replace_in_program(
                attached, parent, dataclasses.replace(
                    parent, children=(sites[1], sites[0], sites[2]))),
            "operator": _replace_in_program(
                attached, sites[0], dataclasses.replace(sites[0], operator="|")),
            "category": _replace_in_program(
                attached, sites[0],
                dataclasses.replace(sites[0], category="lvalue")),
            "result-type": _replace_in_program(
                attached, sites[0], dataclasses.replace(sites[0], type=INT)),
            "left-type": _replace_in_program(
                attached, sites[0], dataclasses.replace(
                    sites[0], children=(dataclasses.replace(
                        sites[0].children[0], type=INT),
                        sites[0].children[1]))),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label), self.assertRaises(ValueError):
                authenticate_scalar_uint_xor(
                    mutated, source_hash, PROFILE)

    def test_site_mutation_survives_a_full_coarse_refreeze(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        source_hash, attached = _attached()
        first, _, _ = module.authenticate_scalar_uint_xor(
            attached, source_hash, module.PROFILE)
        mutated = _replace_in_program(
            attached, first, dataclasses.replace(first, category="lvalue"))
        # Every digest the module checks is refrozen to the mutant -- except
        # the three site records, which stay at the authentic values.
        with mock.patch.dict(module._PROFILES,
                             {KEY: _xor_relocked(module, mutated,
                                                 keep=("sites",))}):
            with self.assertRaises(ValueError) as raised:
                module.authenticate_scalar_uint_xor(
                    mutated, source_hash, module.PROFILE)
        self.assertIn("scalar XOR site mismatch", str(raised.exception))
        for coarse in COARSE:
            self.assertNotIn(coarse, str(raised.exception))


class LandedNoiseFloatBitsIngressTests(unittest.TestCase):
    """The landed one-node float-bit ingress riding the XOR record."""

    def test_returns_the_single_exact_node(self) -> None:
        from tools.glslcpp.frontend.scalar_uint_xor_profile import (
            PROFILE, authenticate_noise_float_bits_ingress)
        source_hash, attached = _attached()
        node, = authenticate_noise_float_bits_ingress(
            attached, source_hash, PROFILE)
        self.assertEqual(("builtin", "floatBitsToUint", "uint", "rvalue"),
                         (node.kind, node.callee, node.type.display(),
                          node.category))
        self.assertEqual("94:21-94:43", _span(node))
        operand, = node.children
        self.assertEqual((149, "sFrac", "float", "local"),
                         (operand.symbol_id, operand.symbol.name,
                          operand.type.display(), operand.symbol.storage))

    def test_the_fract_initializer_lock_rejects_drift(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        source_hash, attached = _attached()
        owner = _function(attached, "constantFromLatticeWithOffset")
        declaration = owner.body[module._NOISE_SFRAC_STATEMENT_INDEX]
        initializer = declaration.expressions[0].children[0]
        child = initializer.children[0]
        for label, mutated in (
                ("callee", _replace_in_program(
                    attached, initializer,
                    dataclasses.replace(initializer, callee="floor"))),
                ("operand", _replace_in_program(
                    attached, child, dataclasses.replace(child, literal="x")))):
            with self.subTest(mutation=label), mock.patch.dict(
                    module._PROFILES,
                    {KEY: _xor_relocked(module, mutated)}):
                with self.assertRaisesRegex(
                        ValueError, "sFrac fract-initializer mismatch"):
                    module.authenticate_noise_float_bits_ingress(
                        mutated, source_hash, module.PROFILE)

    def test_reference_census_rejects_a_mutated_operand(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        source_hash, attached = _attached()
        node, = module.authenticate_noise_float_bits_ingress(
            attached, source_hash, module.PROFILE)
        operand = node.children[0]
        mutated = _replace_in_program(
            attached, operand, dataclasses.replace(operand, literal="x"))
        with mock.patch.dict(module._PROFILES,
                             {KEY: _xor_relocked(module, mutated)}):
            with self.assertRaisesRegex(
                    ValueError,
                    "node identity mismatch|sFrac reference census mismatch"):
                module.authenticate_noise_float_bits_ingress(
                    mutated, source_hash, module.PROFILE)

    def test_downstream_ancestry_rejects_a_mutated_consumer(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        source_hash, attached = _attached()
        xors = module.authenticate_scalar_uint_xor(
            attached, source_hash, module.PROFILE)
        consumer = xors[0].children[0].children[0]
        mutated = _replace_in_program(
            attached, consumer, dataclasses.replace(consumer, literal="x"))
        with mock.patch.dict(module._PROFILES,
                             {KEY: _xor_relocked(module, mutated)}):
            with self.assertRaisesRegex(
                    ValueError, "downstream scalar XOR ancestry mismatch"):
                module.authenticate_noise_float_bits_ingress(
                    mutated, source_hash, module.PROFILE)

    def test_cardinality_and_carrier_gates(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        source_hash, attached = _attached()
        foreign = dataclasses.replace(attached, key="foreign:key")
        with self.assertRaisesRegex(
                ValueError, "noise float-bit ingress carrier"):
            module.authenticate_noise_float_bits_ingress(
                foreign, source_hash, module.PROFILE)
        with self.assertRaisesRegex(ValueError, "exact profile carrier"):
            module.authenticate_noise_float_bits_ingress(
                attached, source_hash, None)
        # A second floatBitsToUint anywhere breaks the whole-program census.
        node, = module.authenticate_noise_float_bits_ingress(
            attached, source_hash, module.PROFILE)
        clone = dataclasses.replace(node, children=node.children)
        duplicated = _replace_in_program(attached, node.children[0], clone)
        with mock.patch.dict(module._PROFILES,
                             {KEY: _xor_relocked(module, duplicated)}):
            with self.assertRaisesRegex(
                    ValueError, "cardinality mismatch"):
                module.authenticate_noise_float_bits_ingress(
                    duplicated, source_hash, module.PROFILE)

    def test_the_ledger_counts_nine_distinct_objects(self) -> None:
        from tools.glslcpp.frontend import scalar_uint_xor_profile as module
        self.assertEqual(9, module._NOISE_INGRESS_LEDGER)
        source_hash, attached = _attached()
        with mock.patch.object(
                module, "_NOISE_INGRESS_LEDGER", 8), self.assertRaisesRegex(
                ValueError, "visitation ledger mismatch"):
            module.authenticate_noise_float_bits_ingress(
                attached, source_hash, module.PROFILE)


class DeleteTheCheckNoiseSweepTests(unittest.TestCase):
    """The tabulated delete-the-check sweep for the frame record's locks.

    Each row deletes the named lock predicates in a scratch re-exec of the
    module (the house ``_scratch`` pattern) and shows the mutant those locks
    catch is then ADMITTED -- the strongest form of load-bearing-ness. The
    disable sets are exactly the locks each mutant trips; the runtime, XOR
    and ingress records check inline in one conditional chain rather than
    predicates, so their equivalent sweep is the field-level refreeze matrix
    in the classes above (matching those modules' own test files, which
    never had per-predicate deletion either).

    ======================  =====================================
    mutant                  locks whose deletion admits it
    ======================  =====================================
    write demoted to [1]    _write_position_holds, _dominance_holds,
                            _main_body_holds, _write_identity_holds
    initializer grafted      _uninitialized_holds,
                            _declaration_inventory_holds,
                            _initializer_census_holds,
                            _declaration_identity_holds,
                            _node_census_holds
    compound `+=` write      _no_indirect_write_holds,
                            _write_identity_holds
    pair reordered           _noise_ordinal_adjacency_holds
    extra 16th global        _declaration_inventory_holds
    read node digest         _read_identity_holds
    ======================  =====================================
    """

    def _scratch(self, module, *disable: str):
        import types
        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        scratch = types.ModuleType(f"{module.__name__}__scratch")
        scratch.__dict__.update({
            "__file__": module.__file__,
            "__package__": module.__package__,
        })
        exec(compile(source, module.__file__, "exec"), scratch.__dict__)
        for name in disable:
            self.assertTrue(callable(getattr(scratch, name, None)),
                            f"{name} is not a deletable lock predicate")
            setattr(scratch, name, lambda *args, **kwargs: True)
        return scratch

    def test_every_value_level_lock_is_load_bearing(self) -> None:
        from tools.glslcpp.frontend import mutable_global_frame_profile as module
        source_hash, attached = _attached()
        main = _function(attached, "main")
        decl = next(d for d in attached.declarations if d.symbol.id == 15)
        write = next(value for statement in main.body
                     for value in _walk_statement(statement)
                     if value.kind == "assign"
                     and value.children[0].symbol_id == 15)
        read = next(value for statement in main.body
                    for value in _walk_statement(statement)
                    if value.symbol_id == 15 and value.kind == "id"
                    and _span(value).startswith("281:"))

        swapped_body = dataclasses.replace(
            attached, functions=tuple(
                function if function.name != "main"
                else dataclasses.replace(function, body=(
                    main.body[1], main.body[0], *main.body[2:]))
                for function in attached.functions))
        # A neutral initializer (main's `vec2 freq = vec2(1.0);` construct):
        # referencing `globalCoord` here would add a second write, which is
        # the write-census lock's mutant, not the initializer lock's.
        freq_initializer = (_function(attached, "main").body[3]
                            .expressions[0].children[0])
        initialized = dataclasses.replace(
            attached, declarations=tuple(
                dataclasses.replace(d, initializer=freq_initializer)
                if d.symbol.id == 15 else d
                for d in attached.declarations))
        compound = _replace_in_program(
            attached, write, dataclasses.replace(write, operator="+="))
        reordered = dataclasses.replace(
            attached, declarations=(
                attached.declarations[:13]
                + (attached.declarations[14], attached.declarations[13])))
        extra_global = dataclasses.replace(
            attached, declarations=attached.declarations + (
                dataclasses.replace(decl, symbol=dataclasses.replace(
                    decl.symbol, id=99, name="extraGlobal")),))
        read_mutated = _replace_in_program(
            attached, read, dataclasses.replace(read, literal="mutated"))

        cases = [
            (swapped_body, ("_write_position_holds", "_dominance_holds",
                            "_main_body_holds", "_write_identity_holds")),
            (initialized, ("_uninitialized_holds",
                           "_declaration_inventory_holds",
                           "_initializer_census_holds",
                           "_declaration_identity_holds",
                           "_node_census_holds")),
            (compound, ("_no_indirect_write_holds", "_write_identity_holds")),
            (reordered, ("_noise_ordinal_adjacency_holds",)),
            (extra_global, ("_declaration_inventory_holds",)),
            (read_mutated, ("_read_identity_holds",)),
        ]
        for candidate, disable in cases:
            with self.subTest(disabled=disable):
                # Live: the refrozen mutant is rejected...
                with mock.patch.object(
                        module, "_LOCKS",
                        _frame_relocked(module, candidate)):
                    with self.assertRaises(ValueError):
                        module.authenticate_mutable_global_frame(
                            candidate, source_hash, FRAME_PROFILE)
                # ...and with exactly those locks deleted it is admitted.
                scratch = self._scratch(module, *disable)
                with mock.patch.object(
                        scratch, "_LOCKS",
                        _frame_relocked(scratch, candidate)):
                    scratch.authenticate_mutable_global_frame(
                        candidate, source_hash, FRAME_PROFILE)


if __name__ == "__main__":
    unittest.main()
