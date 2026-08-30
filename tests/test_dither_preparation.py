from __future__ import annotations

import dataclasses
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import dither_frontend_profile as profile
from tools.glslcpp import generate_dither_native_oracle_include as materializer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl"
PACKAGE = ROOT / "docs/port-engineering/dither-parity"
GENERATOR = PACKAGE / "dither_oracle_generator.mjs"
ORACLE = PACKAGE / "dither-oracles.json"
REPORT = PACKAGE / "dither-oracle-report.md"
MATERIALIZER = ROOT / "tools/glslcpp/generate_dither_native_oracle_include.py"
INCLUDE = ROOT / "tests/oracles/dither_expected.inc"
GENERATOR_SIDEcar = GENERATOR.with_name(GENERATOR.name + ".sha256")
ORACLE_SIDEcar = ORACLE.with_name(ORACLE.name + ".sha256")
REPORT_SIDEcar = REPORT.with_name(REPORT.name + ".sha256")
INCLUDE_SIDEcar = INCLUDE.with_name(INCLUDE.name + ".sha256")

BASELINE_CASES = (
    ("bayer2-input", 4, 3, 0, 0, 4, 0, 1, 1, 1, 0, (0, 0), (4, 3)),
    ("bayer8-tiled", 7, 5, 2, 0, 5, .13, 2, 1, .85, .2, (3, 2), (24, 20)),
    ("dot-input", 6, 4, 3, 0, 4, -.2, 2, 1.25, 1, .4, (2, 1), (18, 14)),
    ("line-input", 5, 6, 4, 0, 4, .2, 3, .75, .6, .75, (4, 3), (20, 24)),
    ("crosshatch-input", 6, 5, 5, 0, 4, 0, 1, 1, 1, .1, (1, 4), (12, 10)),
    ("noise-input", 7, 4, 6, 0, 4, -.1, 2, 1, .9, 1.1, (5, 2), (28, 16)),
    ("fallback-type", 3, 3, 99, 0, 4, 0, 1, 1, 1, 0, (0, 0), (3, 3)),
    ("error-diffusion-input", 5, 5, 7, 0, 4, 0, 1, 1, 1, .33, (0, 0), (5, 5)),
    ("error-diffusion-input-tiled", 6, 4, 7, 0, 4, .1, 2, 1, .8, -.2, (2, 1), (18, 12)),
)
ADVERSARIAL_CASES = (
    "error-diffusion-negative-tile", "levels-2-boundary", "levels-16-boundary",
)
CASE_NAMES = tuple(item[0] for item in BASELINE_CASES) + ADVERSARIAL_CASES
MUTATION_NAMES = ("fallback-default", "quantize-levels", "error-diffusion-route")
EXPECTED_BLOCKER = {
    "route": "palette != PALETTE_INPUT",
    "error": "ditherWithPalette(...).reduce is not a function",
    "source_anchor": "ditherWithPalette(...).reduce((res,el,i)=>(res[i] = el, res), result)",
    "reproducible": True,
}
EXPECTED_TRACE_POINTS = (
    ((0, 0), (-8.5, 2.5), (-5, 1), (-4, 0)),
    ((1, 0), (-7.5, 2.5), (-4, 1), (-4, 0)),
    ((5, 0), (-3.5, 2.5), (-2, 1), (0, 0)),
)
EXPECTED_CLAMP_WITNESS = {
    "fragment": [0, 0],
    "block_origin": [-4, 0],
    "loop_offset": [-4, -4],
    "cell": [-8, -4],
    "global": [-15, -7],
    "raw_local": [-6, -9],
    "clamped_local": [0, 0],
    "visited": True,
}
EXPECTED_LEVEL2_ZERO = [0, 1, 4, 6, 13, 14, 17, 18, 21, 22, 28, 30, 32, 34, 36, 37, 41]
EXPECTED_LEVEL2_ONE = [2, 5, 8, 10, 12, 20, 24, 25, 38, 40, 44, 45, 46]
EXPECTED_LEVEL16_ZERO = [2, 5, 33]
EXPECTED_LEVEL16_ONE = [8, 25]
EXPECTED_MUTATION_WITNESSES = {
    "fallback-default": (
        ("fallback-type", 6, 4, 6, "0x3eaaaaab", "0x00000000", 6, 85, 0),
    ),
    "quantize-levels": (
        ("bayer2-input", 30, 26, 0, "0xbeaaaaab", "0xbe800000", 4, 255, 191),
    ),
    "error-diffusion-route": (
        ("error-diffusion-input", 25, 22, 5, "0x3f2aaaab", "0x3f800000", 5, 170, 255),
        ("error-diffusion-input-tiled", 13, 13, 2, "0x3f317e4b", "0x3f75c28f", 2, 177, 245),
    ),
}


def analyzed(raw: str | None = None, key: str = profile.KEY):
    text = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(text, key, {}), key)


def replace_expression(value, target, replacement):
    if value is target:
        return replacement
    return dataclasses.replace(value, children=tuple(
        replace_expression(child, target, replacement) for child in value.children))


def replace_statement(statement, target, replacement):
    return dataclasses.replace(
        statement,
        expressions=tuple(replace_expression(item, target, replacement)
                          for item in statement.expressions),
        children=tuple(replace_statement(child, target, replacement)
                       for child in statement.children))


def alter_rehashed_mutation(candidate):
    mutation = candidate["mutation_ledger"][0]
    mutation["replacement"] = "return 0.125;\n  };\n  function quantizeWithDither"
    mutation["replacement_sha256"] = hashlib.sha256(mutation["replacement"].encode()).hexdigest()


def alter_rehashed_anchor(candidate):
    mutation = candidate["mutation_ledger"][0]
    mutation["source_anchor"] = "return 0.375;\n  };\n  function quantizeWithDither"
    mutation["anchor_sha256"] = hashlib.sha256(mutation["source_anchor"].encode()).hexdigest()


def alter_rehashed_factory(candidate):
    candidate["mutation_ledger"][0]["mutated_factory_sha256"] = hashlib.sha256(b"altered factory").hexdigest()


class DitherPreparedFrontendTests(unittest.TestCase):
    def test_prepared_registry_and_runtime_contract(self):
        self.assertEqual((), profile.KEYS)
        self.assertEqual((profile.KEY,), profile.PREPARED_KEYS)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PROFILES)
        self.assertEqual({profile.KEY: profile.PROFILE}, profile.PREPARED_PROFILES)
        self.assertEqual(frozenset({"defines", "program_key", "dither_frontend_profile"}),
                         profile.ALLOWED_ROW_FIELDS[profile.KEY])
        self.assertEqual(profile.SAMPLER_RUNTIME_ABI,
                         ("inputTex", "sampler2D", "const Surface&"))
        self.assertEqual(len(profile.SOURCE_UNIFORMS), 11)

    def test_authentication_returns_source_bound_disjoint_live_proof(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, hashlib.sha256(program.raw_source.encode()).hexdigest(), profile.PROFILE)
        self.assertEqual(profile.KEY, proof.program_key)
        self.assertEqual(9, len(proof.bitwise_nodes))
        self.assertEqual(24, len(proof.indexed_nodes))
        self.assertEqual(len(proof.consumed_objects), len({id(x) for x in proof.consumed_objects}))
        self.assertIs(program, profile.apply_dither_frontend(program, profile.RAW_SHA256, profile.PROFILE))

    def test_source_bound_ledgers_are_exact_and_one_to_one(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        self.assertEqual(6, len(proof.loop_records))
        self.assertEqual(10, len(proof.array_records))
        self.assertEqual(3, len(proof.array_parameters))
        self.assertEqual(24, len(proof.index_records))
        self.assertEqual(9, len(proof.bitwise_records))
        self.assertEqual(tuple(item[0] for item in profile.LOOP_LEDGER),
                         tuple(item.record_id for item in proof.loop_records))
        self.assertEqual(tuple(item[0] for item in profile.ARRAY_LEDGER),
                         tuple(item.record_id for item in proof.array_records))
        self.assertEqual(tuple(item[0] for item in profile.ARRAY_PARAMETER_LEDGER),
                         tuple(item.record_id for item in proof.array_parameters))
        self.assertEqual(tuple(item[0] for item in profile.INDEX_LEDGER),
                         tuple(item.record_id for item in proof.index_records))
        self.assertEqual(tuple(item[0] for item in profile.BITWISE_LEDGER),
                         tuple(item.record_id for item in proof.bitwise_records))
        self.assertEqual(len(proof.consumed_objects),
                         len({id(item) for item in proof.consumed_objects}))
        self.assertEqual(6 + 10 + 3 + 24 + 9, len(proof.consumed_objects))
        for record in (*proof.loop_records, *proof.array_records,
                       *proof.array_parameters, *proof.index_records,
                       *proof.bitwise_records):
            self.assertIsNotNone(record.node)
            self.assertEqual(record.node_sha256,
                             hashlib.sha256(repr(record.node).encode()).hexdigest())

    def test_prepared_frontend_expansion_authenticates_all_source_bound_ledgers(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)

        self.assertEqual(tuple(f"C{index:02d}" for index in range(1, 31)),
                         tuple(record.record_id for record in proof.conversion_records))
        self.assertEqual(tuple(f"P{index:02d}" for index in range(1, 9)),
                         tuple(record.record_id for record in proof.pcg_order_records))
        self.assertEqual(tuple(f"F{index:02d}" for index in range(1, 50)),
                         tuple(record.record_id for record in proof.f32_materialization_records))
        self.assertEqual(tuple(f"AP{index:02d}" for index in range(1, 19)),
                         tuple(record.record_id for record in proof.parameter_copy_records))
        self.assertEqual(94, proof.authority_eager_count)
        self.assertEqual(48, proof.authority_pooled_count)
        self.assertEqual(18, proof.authority_err_row_lanes)
        self.assertEqual(153, len(proof.unique_consumed_objects))
        self.assertEqual(153, len({id(item) for item in proof.unique_consumed_objects}))
        self.assertEqual(profile.F32_STORE_VIEW, proof.f32_store_view)
        self.assertEqual(40, len(proof.f32_store_view))
        f49 = proof.f32_materialization_records[-1]
        self.assertEqual("runtime_adapter", f49.binding_kind)
        self.assertEqual("f32_return", f49.role)
        self.assertEqual("F48", f49.ref_to)

    def test_prepared_frontend_extension_rejects_ledger_mutation_and_f49_double_count(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)

        reordered = dataclasses.replace(
            proof,
            pcg_order_records=(proof.pcg_order_records[1], proof.pcg_order_records[0],
                               *proof.pcg_order_records[2:]),
        )
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(reordered, program)

        bad_f49 = dataclasses.replace(
            proof,
            f32_materialization_records=(*proof.f32_materialization_records[:-1],
                                         dataclasses.replace(
                                             proof.f32_materialization_records[-1],
                                             kind="source_ast")),
        )
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(bad_f49, program)

        bad_view = dataclasses.replace(
            proof,
            f32_store_view=proof.f32_store_view[:-1],
        )
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(bad_view, program)

    def test_ledger_clone_reorder_cardinality_and_root_symbol_fail_closed(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        cases = (
            dataclasses.replace(proof, index_records=proof.index_records[:-1]),
            dataclasses.replace(proof, index_records=(proof.index_records[1],
                                                       proof.index_records[0],
                                                       *proof.index_records[2:])),
            dataclasses.replace(
                proof,
                index_records=(dataclasses.replace(
                    proof.index_records[0], node=proof.index_records[1].node),
                    *proof.index_records[1:])),
            dataclasses.replace(
                proof,
                index_records=(dataclasses.replace(
                    proof.index_records[0], root_symbol_id=63),
                    *proof.index_records[1:])),
        )
        for forged in cases:
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.validate_dither_proof_ledgers(forged, program)

    def test_complete_deep_copy_of_proof_rejects_cloned_ast(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        cloned = copy.deepcopy(proof)
        self.assertIsNot(cloned.loop_records[0].node, proof.loop_records[0].node)
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(cloned, program)

    def test_loop_proof_presence_and_identity_mutations_fail_closed(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)

        bounded_without_proof = dataclasses.replace(
            proof,
            loop_records=(dataclasses.replace(
                proof.loop_records[0], proof=None), *proof.loop_records[1:]),
        )
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(bounded_without_proof, program)

        unproved_with_proof = dataclasses.replace(
            proof,
            loop_records=(*proof.loop_records[:3], dataclasses.replace(
                proof.loop_records[3], proof=dataclasses.replace(
                    proof.loop_records[0].proof,
                    induction_symbol_id=proof.loop_records[3].induction_symbol_id)),
                           *proof.loop_records[4:]),
        )
        with self.assertRaisesRegex(ValueError, profile.PROFILE):
            profile.validate_dither_proof_ledgers(unproved_with_proof, program)

    def test_every_ledger_category_rejects_node_forgery(self):
        program = analyzed()
        proof = profile.authenticate_dither_frontend(
            program, profile.RAW_SHA256, profile.PROFILE)
        forged = (
            dataclasses.replace(
                proof,
                loop_records=(dataclasses.replace(
                    proof.loop_records[0], node=proof.loop_records[1].node),
                    *proof.loop_records[1:])),
            dataclasses.replace(
                proof,
                array_records=(dataclasses.replace(
                    proof.array_records[0], node=proof.array_records[1].node),
                    *proof.array_records[1:])),
            dataclasses.replace(
                proof,
                array_parameters=(dataclasses.replace(
                    proof.array_parameters[0], node=proof.array_parameters[1].node),
                    *proof.array_parameters[1:])),
            dataclasses.replace(
                proof,
                bitwise_records=(dataclasses.replace(
                    proof.bitwise_records[0], operator="&"),
                    *proof.bitwise_records[1:])),
            dataclasses.replace(proof, consumed_objects=proof.consumed_objects[:-1]),
        )
        for candidate in forged:
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.validate_dither_proof_ledgers(candidate, program)

    def test_exact_counted_loop_blocker_is_exposed(self):
        program = analyzed()
        proof = program.counted_loop_proof
        self.assertIsNotNone(proof)
        self.assertEqual(profile.LOOP_PROOF, (proof.loop_count, proof.unproved_loop_count,
                                              proof.max_effective_depth, proof.max_lexical_product,
                                              proof.entrypoint_charge, proof.call_graph_acyclic))
        self.assertEqual(3, proof.unproved_loop_count)

    def test_wrong_identity_or_source_fails_closed(self):
        program = analyzed()
        for candidate, source_hash, selected in (
                (program, "0" * 64, profile.PROFILE),
                (program, profile.RAW_SHA256, "wrong-profile"),
                (dataclasses.replace(program, key="foreign:key"), profile.RAW_SHA256, profile.PROFILE)):
            with self.assertRaisesRegex(ValueError, profile.PROFILE):
                profile.authenticate_dither_frontend(candidate, source_hash, selected)

    def test_index_mutation_is_rejected_even_when_candidate_is_rebuilt(self):
        program = analyzed()
        target = next(item for item in profile._expressions(program)
                      if item.kind == "index")
        changed_index = dataclasses.replace(target, children=target.children[:-1])
        changed = dataclasses.replace(
            program,
            functions=tuple(dataclasses.replace(
                function,
                body=tuple(replace_statement(statement, target, changed_index)
                           for statement in function.body))
                for function in program.functions))
        with self.assertRaisesRegex(ValueError, "lock mismatch|aggregate|source"):
            profile.authenticate_dither_frontend(changed, profile.RAW_SHA256, profile.PROFILE)

    def test_oracle_package_has_authenticated_cases_and_mutation_witnesses(self):
        for path in (GENERATOR, ORACLE, REPORT, MATERIALIZER, INCLUDE,
                     ORACLE_SIDEcar, REPORT_SIDEcar, INCLUDE_SIDEcar):
            self.assertTrue(path.is_file(), path)
        for artifact, sidecar in ((GENERATOR, GENERATOR_SIDEcar),
                                  (ORACLE, ORACLE_SIDEcar), (REPORT, REPORT_SIDEcar),
                                  (INCLUDE, INCLUDE_SIDEcar)):
            self.assertEqual(f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}\n",
                             sidecar.read_text(encoding="utf-8"))
        document = json.loads(ORACLE.read_text(encoding="utf-8"))
        self.assertEqual("noisemaker-for-cpp.dither.pixel-parity.v1", document["schema"])
        self.assertEqual(profile.KEY, document["program_key"])
        self.assertEqual(CASE_NAMES, tuple(case["name"] for case in document["render_cases"]))
        self.assertEqual(MUTATION_NAMES, tuple(item["name"] for item in document["mutation_ledger"]))
        self.assertEqual(12, len(document["render_cases"]))
        self.assertEqual(3, len(document["mutation_ledger"]))
        self.assertEqual(
            (("error-diffusion-negative-tile", 7, .1, 2, 1, .8, -.2, (-9, 2), (18, 12)),
             ("levels-2-boundary", 0, 0, 1, 1, 1, 0, (0, 0), (4, 3)),
             ("levels-16-boundary", 0, 0, 1, 1, 1, 0, (0, 0), (4, 3))),
            tuple((case["name"], case["ditherType"], case["threshold"], case["matrixScale"],
                   case["renderScale"], case["mixAmount"], case["time"],
                   tuple(case["tileOffset"]), tuple(case["fullResolution"]))
                  for case in document["render_cases"][9:]))
        for case, expected in zip(document["render_cases"][:9], BASELINE_CASES):
            (name, width, height, dither_type, palette, levels, threshold,
             matrix_scale, render_scale, mix_amount, time, tile, full) = expected
            self.assertEqual((name, width, height, dither_type, palette, levels),
                             (case["name"], case["width"], case["height"],
                              case["ditherType"], case["palette"], case["levels"]))
            for key, value in (("threshold", threshold), ("matrixScale", matrix_scale),
                               ("renderScale", render_scale), ("mixAmount", mix_amount),
                               ("time", time)):
                self.assertAlmostEqual(value, case[key])
            self.assertEqual(list(tile), case["tileOffset"])
            self.assertEqual(list(full), case["fullResolution"])
        # The pre-port baseline snapshot is an external checkout like every
        # other authority in this suite, so its root arrives by env. It used to
        # be an absolute session scratch path, which meant the comparison below
        # was unreachable on every machine but the one that produced it. When
        # the env is unset the cross-check is skipped and the rest of this test
        # still runs; when it is set the snapshot must actually be there.
        baseline_root = os.environ.get("NOISEMAKER_DITHER_BASELINE_ROOT")
        if baseline_root:
            baseline_fixture = Path(baseline_root) / "docs/port-engineering/dither-parity/dither-oracles.json"
            self.assertTrue(baseline_fixture.is_file(),
                            "NOISEMAKER_DITHER_BASELINE_ROOT must contain "
                            f"docs/port-engineering/dither-parity/dither-oracles.json: {baseline_fixture}")
            baseline_document = json.loads(baseline_fixture.read_text(encoding="utf-8"))
            for index in range(9):
                self.assertEqual(json.dumps(baseline_document["render_cases"][index], separators=(",", ":")),
                                 json.dumps(document["render_cases"][index], separators=(",", ":")))
            self.assertEqual(json.dumps(baseline_document["mutation_ledger"], separators=(",", ":")),
                             json.dumps(document["mutation_ledger"], separators=(",", ":")))
        self.assertTrue(all(case["palette"] == 0 for case in document["render_cases"]))
        self.assertEqual(EXPECTED_BLOCKER, {
            key: document["upstream_runtime_blockers"][0][key]
            for key in EXPECTED_BLOCKER
        })
        blocker = document["negative_authority"]
        self.assertEqual(EXPECTED_BLOCKER, {
            key: blocker[key] for key in EXPECTED_BLOCKER
        })
        self.assertTrue(blocker["direct"]["throws"])
        self.assertTrue(blocker["public"]["throws"])
        self.assertEqual(2, blocker["palette"])
        self.assertEqual(EXPECTED_BLOCKER["error"], blocker["direct"]["message"])
        self.assertEqual(EXPECTED_BLOCKER["error"], blocker["public"]["message"])
        self.assertEqual(1, sum(case.get("signed_trace") is not None for case in document["render_cases"]))
        trace_case = next(case for case in document["render_cases"] if case.get("signed_trace"))
        trace = trace_case["signed_trace"]
        self.assertEqual("error-diffusion-negative-tile", trace_case["name"])
        self.assertEqual(4, trace["fs_block"])
        self.assertEqual("truncate_toward_zero", trace["signed_division"])
        self.assertEqual(2, trace["cell_size"])
        self.assertTrue(trace["negative_global_coordinate"])
        self.assertTrue(trace["negative_block_origin"])
        self.assertTrue(trace["clamp_witness"]["clamped"])
        self.assertEqual(EXPECTED_TRACE_POINTS, tuple(
            (tuple(point["fragment"]), tuple(point["global"]), tuple(point["cell"]),
             tuple(point["block_origin"])) for point in trace["points"]))
        self.assertEqual(EXPECTED_CLAMP_WITNESS, {
            key: trace["clamp_witness"][key] for key in EXPECTED_CLAMP_WITNESS
        })
        self.assertEqual("508-566", trace["source"]["block_span"])
        self.assertEqual("500-506", trace["source"]["fetch_span"])
        self.assertEqual("117a236679d1db3ab8f0e278230ece277b57564c",
                         document["provenance"]["upstream_revision"])
        self.assertEqual("src/effects/generated/canonical-kernels.js",
                         document["provenance"]["source"]["relative_path"])
        self.assertEqual(1713290, document["provenance"]["source"]["bytes"])
        self.assertEqual("66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
                         document["provenance"]["source"]["sha256"])
        self.assertEqual("canonicalFactory48", document["provenance"]["factory"]["name"])
        self.assertEqual("canonicalFactory48", document["provenance"]["factory"]["public_factory_name"])
        self.assertTrue(document["provenance"]["factory"]["public_factory_is_canonical_identity"])
        self.assertEqual("28a1c56b63d345eaa3c3e803b19397a546730020d456ed2c29eb39aec3a5c820",
                         document["provenance"]["factory"]["text_sha256"])
        for name, levels, zero, one in (
                ("levels-2-boundary", 2, EXPECTED_LEVEL2_ZERO, EXPECTED_LEVEL2_ONE),
                ("levels-16-boundary", 16, EXPECTED_LEVEL16_ZERO, EXPECTED_LEVEL16_ONE)):
            evidence = next(case for case in document["render_cases"] if case["name"] == name)["level_evidence"]
            self.assertEqual(levels, evidence["levels"])
            self.assertEqual({"zero": zero, "one": one}, evidence["rgb_endpoint_lanes"])
            self.assertEqual("0x3f800000", evidence["highest_level_word"])
            self.assertEqual(one, evidence["highest_level_rgb_lanes"])
        self.assertEqual(12, len(document["render_cases"]))
        self.assertEqual({"f32_words_exact", "rgba8_bytes_exact", "dimensions_before_data",
                          "signed_zero_exact", "input_bits_exact", "public_direct_exact",
                          "repeat_identity_exact"}, set(document["comparer_policy"]))
        self.assertTrue(all(document["comparer_policy"].values()))
        self.assertEqual(22, len(document["provenance"]["cpu_snapshot"]["import_closure"]))
        self.assertEqual(64, len(document["provenance"]["cpu_snapshot"]["closure_sha256"]))
        self.assertTrue(document["provenance"]["cpu_snapshot"]["immutable_snapshot"])
        self.assertTrue(document["provenance"]["cpu_snapshot"]["live_checkout_rejected"])
        self.assertTrue(all(document["comparer_self_tests"].values()))
        self.assertTrue(document["upstream_runtime_blockers"])
        for case in document["render_cases"]:
            count = case["width"] * case["height"] * 4
            for label in ("input", "expected", "public_expected"):
                self.assertEqual(count, len(case[label]["f32_words_le"]))
                self.assertEqual(count, len(case[label]["rgba8_bytes"]))
                self.assertTrue(all(((int(word, 16) >> 23) & 0xFF) != 0xFF
                                    for word in case[label]["f32_words_le"]))
            self.assertTrue(case["input_immutable_exact_bits"])
            self.assertTrue(case["public_direct_exact"])
            self.assertTrue(all(case["repeat"].values()))
        for mutation in document["mutation_ledger"]:
            self.assertTrue(mutation["required_witnesses"])
            self.assertTrue(all(item["mismatched_lanes"] > 0 and item["mismatched_bytes"] > 0
                                for item in mutation["required_witness_results"]))
            self.assertEqual(EXPECTED_MUTATION_WITNESSES[mutation["name"]], tuple(
                (item["case"], item["mismatched_lanes"], item["mismatched_bytes"],
                 item["first_mismatch"]["lane_index"], item["first_mismatch"]["reference"],
                 item["first_mismatch"]["candidate"], item["first_rgba8_mismatch"]["byte_index"],
                 item["first_rgba8_mismatch"]["reference"], item["first_rgba8_mismatch"]["candidate"])
                for item in mutation["required_witness_results"]))
        for mutate in (
                lambda candidate: candidate["render_cases"][0]["expected"].__setitem__("f32_sha256", "0" * 64),
                lambda candidate: candidate["render_cases"].__setitem__(slice(0, 2), candidate["render_cases"][:2][::-1]),
                lambda candidate: candidate["provenance"]["cpu_snapshot"].__setitem__("closure_sha256", "0" * 64),
                lambda candidate: candidate["mutation_ledger"][0].__setitem__("replacement_sha256", "0" * 64),
                lambda candidate: candidate["negative_authority"]["direct"].__setitem__("message", "forged"),
                lambda candidate: candidate["render_cases"][9]["signed_trace"].__setitem__("signed_division", "floor"),
                lambda candidate: candidate["render_cases"][9]["signed_trace"]["points"][0]["cell"].__setitem__(0, 0),
                lambda candidate: candidate["render_cases"][9]["signed_trace"]["clamp_witness"].__setitem__("cell", [0, -11]),
                lambda candidate: candidate["provenance"].__setitem__("upstream_revision", "wrong"),
                lambda candidate: candidate["provenance"]["factory"].__setitem__("text_sha256", "0" * 64),
                lambda candidate: candidate["mutation_ledger"][0]["required_witness_results"][0]["first_mismatch"].__setitem__("lane_index", 7),
                lambda candidate: candidate["mutation_ledger"][0]["required_witness_results"][0]["first_rgba8_mismatch"].__setitem__("candidate", 1),
                alter_rehashed_mutation,
                alter_rehashed_anchor,
                alter_rehashed_factory,
        ):
            candidate = json.loads(json.dumps(document))
            mutate(candidate)
            with self.assertRaises(materializer.MaterializationError):
                materializer.validate(candidate)

    def test_materialized_include_retains_exact_mutation_witnesses(self):
        document = json.loads(ORACLE.read_text(encoding="utf-8"))
        content = materializer.materialize(document)
        self.assertIn("reference_f32_word, candidate_f32_word", content)
        self.assertIn(
            'MutationResult{"fallback-type", "0x3eaaaaab", "0x00000000", 6u, 4u, 6u, 6u, 85u, 0u}',
            content)

    def test_oracle_generators_and_include_are_green(self):
        # Env-only, and a skip rather than a failure when unset: the frozen CPU
        # authority is an external checkout, so its absence is a missing input,
        # not a defect in the port. A configured-but-wrong root still fails.
        configured = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not configured:
            self.skipTest("NOISEMAKER_CPU_ROOT must be supplied for authority gates")
        authority = Path(configured)
        self.assertTrue(authority.is_dir(), "NOISEMAKER_CPU_ROOT must name a directory")
        self.assertFalse(authority.is_symlink(), "NOISEMAKER_CPU_ROOT must not be a symlink")
        for command in (
                ("node", str(GENERATOR), "--check", "--cpu-root", str(authority)),
                ("node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)),
                (sys.executable, "-B", str(MATERIALIZER), "--self-test"),
                (sys.executable, "-B", str(MATERIALIZER), "--check")):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        with tempfile.TemporaryDirectory(prefix="dither-authority-probes-") as raw:
            raw_root = Path(raw)
            identical = raw_root / "identical"
            shutil.copytree(authority, identical)
            identical_result = subprocess.run(
                ("node", str(GENERATOR), "--check", "--cpu-root", str(identical)),
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(0, identical_result.returncode,
                             identical_result.stdout + identical_result.stderr)
            mutated = raw_root / "mutated"
            shutil.copytree(authority, mutated)
            canonical = mutated / "src/effects/generated/canonical-kernels.js"
            canonical.write_bytes(canonical.read_bytes() + b"\n")
            mutated_result = subprocess.run(
                ("node", str(GENERATOR), "--check", "--cpu-root", str(mutated)),
                cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(0, mutated_result.returncode)
            live_result = subprocess.run(
                ("node", str(GENERATOR), "--check", "--cpu-root", str(authority)),
                cwd=ROOT, env={**os.environ, "NOISEMAKER_FOR_CPU": str(authority)},
                capture_output=True, text=True)
            self.assertNotEqual(0, live_result.returncode)
            escaping = raw_root / "escaping"
            shutil.copytree(authority, escaping)
            escaped_catalog = escaping / "src/effects/catalog.js"
            escaped_catalog.unlink()
            escaped_catalog.symlink_to(authority / "src/effects/catalog.js")
            escaping_result = subprocess.run(
                ("node", str(GENERATOR), "--check", "--cpu-root", str(escaping)),
                cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(0, escaping_result.returncode)
            linked = raw_root / "linked"
            linked.symlink_to(authority, target_is_directory=True)
            linked_result = subprocess.run(
                ("node", str(GENERATOR), "--check", "--cpu-root", str(linked)),
                cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(0, linked_result.returncode)

    def test_include_is_cxx20_wall_wextra_werror_smoke(self):
        compiler = shutil.which("c++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++ compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="dither-oracle-cxx-") as raw:
            unit = Path(raw) / "smoke.cpp"
            unit.write_text('''#include "tests/oracles/dither_expected.inc"
int main() {
  using namespace noisemaker_dither_oracle;
  static_assert(kCases.size() == 12U);
  static_assert(kCases[0].name == "bayer2-input");
  static_assert(kCases[1].name == "bayer8-tiled");
  static_assert(kCases[2].name == "dot-input");
  static_assert(kCases[3].name == "line-input");
  static_assert(kCases[4].name == "crosshatch-input");
  static_assert(kCases[5].name == "noise-input");
  static_assert(kCases[6].name == "fallback-type");
  static_assert(kCases[7].name == "error-diffusion-input");
  static_assert(kCases[8].name == "error-diffusion-input-tiled");
  static_assert(kCases[9].name == "error-diffusion-negative-tile");
  static_assert(kCases[10].name == "levels-2-boundary");
  static_assert(kCases[11].name == "levels-16-boundary");
  static_assert(kMutations.size() == 3U);
  static_assert(kMutations[0].name == "fallback-default");
  static_assert(kMutations[1].name == "quantize-levels");
  static_assert(kMutations[2].name == "error-diffusion-route");
  static_assert(kMutations[0].anchor_sha256 == "8e35a9b15829e194b90777d8f38e5709ec2e1f8cfa875d4294496fade9f67683");
  static_assert(kMutations[0].replacement_sha256 == "8fb42fd196d8a5e5bff6ba3a7a1dd24a87fe4dfb2b0f07a75146dc5bdcd1251b");
  static_assert(kMutations[0].mutated_factory_sha256 == "85c2335ba2395a5d80f05fff460de3ddf5779b39524a927ee506618c36e0f611");
  static_assert(kMutations[1].anchor_sha256 == "4af10b05bcf97c256bedc908d8fc491d9a7d53b3bd16508493a436d742f602ac");
  static_assert(kMutations[1].replacement_sha256 == "aa8311a86e4e743a9c84375b905a6c66581039145887910832a63625c2ef4b34");
  static_assert(kMutations[1].mutated_factory_sha256 == "c48b59a286a1178abe723287b9ea9869600425609971827b37bb4b2d5b6ea007");
  static_assert(kMutations[2].anchor_sha256 == "4d67d8c234a20ad7a01c31093fd192a8a78821d5414d115bbc1dfbb209586e3f");
  static_assert(kMutations[2].replacement_sha256 == "a379b9b2de4ff3d9bbc89b6f64472ac79af6d39b89ae7604f2cf529752d32788");
  static_assert(kMutations[2].mutated_factory_sha256 == "3937d5b5265b810304261dae07e087890cec8fcf755da6a17d82146aa0432be3");
  static_assert(kMutations[0].results.size() == 1U && kMutations[0].results[0].case_name == "fallback-type" && kMutations[0].results[0].mismatched_lanes == 6U && kMutations[0].results[0].mismatched_bytes == 4U);
  static_assert(kMutations[1].results.size() == 1U && kMutations[1].results[0].case_name == "bayer2-input" && kMutations[1].results[0].mismatched_lanes == 30U && kMutations[1].results[0].mismatched_bytes == 26U);
  static_assert(kMutations[2].results.size() == 2U && kMutations[2].results[0].case_name == "error-diffusion-input" && kMutations[2].results[0].mismatched_lanes == 25U && kMutations[2].results[0].mismatched_bytes == 22U && kMutations[2].results[1].case_name == "error-diffusion-input-tiled" && kMutations[2].results[1].mismatched_lanes == 13U && kMutations[2].results[1].mismatched_bytes == 13U);
  static_assert(kSchema == "noisemaker-for-cpp.dither.pixel-parity.v1");
  static_assert(kProgramKey == "filter/dither:dither");
  static_assert(kAuthorityNode == "v24.7.0");
  static_assert(kUpstreamRevision == "117a236679d1db3ab8f0e278230ece277b57564c");
  static_assert(kSourceRelativePath == "src/effects/generated/canonical-kernels.js");
  static_assert(kSourceSha256 == "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe");
  static_assert(kFactoryName == "canonicalFactory48");
  static_assert(kFactoryTextSha256 == "28a1c56b63d345eaa3c3e803b19397a546730020d456ed2c29eb39aec3a5c820");
  static_assert(kPublicFactoryName == "canonicalFactory48");
  static_assert(kPublicFactoryIsCanonicalIdentity);
  static_assert(kCorpusSourceRelativePath == "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl");
  static_assert(kCorpusSourceSha256 == "a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb");
  static_assert(kClosureSha256 == "b16cbd8716cab226271041751af6431bfe48fef1c0826bba89544a0f4bf525f5");
  static_assert(kImmutableSnapshot);
  static_assert(kLiveCheckoutRejected);
  static_assert(kRealpathContainmentChecked);
  static_assert(kSymlinkEscapeRejected);
  static_assert(kLevelEvidence.size() == 2U);
  static_assert(kLevelEvidence[0].case_name == "levels-2-boundary" && kLevelEvidence[0].levels == 2U);
  static_assert(kLevelEvidence[0].highest_level_word == "0x3f800000");
  static_assert(kLevelEvidence[0].zero_lanes.size() == 17U && kLevelEvidence[0].one_lanes.size() == 13U && kLevelEvidence[0].highest_level_rgb_lanes.size() == 13U);
  static_assert(kLevelEvidence[0].zero_lanes[0] == 0U && kLevelEvidence[0].zero_lanes[16] == 41U && kLevelEvidence[0].one_lanes[0] == 2U && kLevelEvidence[0].one_lanes[12] == 46U);
  static_assert(kLevelEvidence[1].case_name == "levels-16-boundary" && kLevelEvidence[1].levels == 16U);
  static_assert(kLevelEvidence[1].highest_level_word == "0x3f800000");
  static_assert(kLevelEvidence[1].zero_lanes.size() == 3U && kLevelEvidence[1].one_lanes.size() == 2U && kLevelEvidence[1].highest_level_rgb_lanes.size() == 2U);
  static_assert(kLevelEvidence[1].zero_lanes[0] == 2U && kLevelEvidence[1].zero_lanes[2] == 33U && kLevelEvidence[1].one_lanes[0] == 8U && kLevelEvidence[1].one_lanes[1] == 25U);
  static_assert(kLevelEvidence[0].zero_lanes[0] == 0U && kLevelEvidence[0].zero_lanes[1] == 1U && kLevelEvidence[0].zero_lanes[2] == 4U && kLevelEvidence[0].zero_lanes[3] == 6U && kLevelEvidence[0].zero_lanes[4] == 13U && kLevelEvidence[0].zero_lanes[5] == 14U && kLevelEvidence[0].zero_lanes[6] == 17U && kLevelEvidence[0].zero_lanes[7] == 18U && kLevelEvidence[0].zero_lanes[8] == 21U && kLevelEvidence[0].zero_lanes[9] == 22U && kLevelEvidence[0].zero_lanes[10] == 28U && kLevelEvidence[0].zero_lanes[11] == 30U && kLevelEvidence[0].zero_lanes[12] == 32U && kLevelEvidence[0].zero_lanes[13] == 34U && kLevelEvidence[0].zero_lanes[14] == 36U && kLevelEvidence[0].zero_lanes[15] == 37U && kLevelEvidence[0].zero_lanes[16] == 41U);
  static_assert(kLevelEvidence[0].one_lanes[0] == 2U && kLevelEvidence[0].one_lanes[1] == 5U && kLevelEvidence[0].one_lanes[2] == 8U && kLevelEvidence[0].one_lanes[3] == 10U && kLevelEvidence[0].one_lanes[4] == 12U && kLevelEvidence[0].one_lanes[5] == 20U && kLevelEvidence[0].one_lanes[6] == 24U && kLevelEvidence[0].one_lanes[7] == 25U && kLevelEvidence[0].one_lanes[8] == 38U && kLevelEvidence[0].one_lanes[9] == 40U && kLevelEvidence[0].one_lanes[10] == 44U && kLevelEvidence[0].one_lanes[11] == 45U && kLevelEvidence[0].one_lanes[12] == 46U);
  static_assert(kLevelEvidence[0].highest_level_rgb_lanes[0] == 2U && kLevelEvidence[0].highest_level_rgb_lanes[1] == 5U && kLevelEvidence[0].highest_level_rgb_lanes[2] == 8U && kLevelEvidence[0].highest_level_rgb_lanes[3] == 10U && kLevelEvidence[0].highest_level_rgb_lanes[4] == 12U && kLevelEvidence[0].highest_level_rgb_lanes[5] == 20U && kLevelEvidence[0].highest_level_rgb_lanes[6] == 24U && kLevelEvidence[0].highest_level_rgb_lanes[7] == 25U && kLevelEvidence[0].highest_level_rgb_lanes[8] == 38U && kLevelEvidence[0].highest_level_rgb_lanes[9] == 40U && kLevelEvidence[0].highest_level_rgb_lanes[10] == 44U && kLevelEvidence[0].highest_level_rgb_lanes[11] == 45U && kLevelEvidence[0].highest_level_rgb_lanes[12] == 46U);
  static_assert(kLevelEvidence[1].zero_lanes[0] == 2U && kLevelEvidence[1].zero_lanes[1] == 5U && kLevelEvidence[1].zero_lanes[2] == 33U);
  static_assert(kLevelEvidence[1].one_lanes[0] == 8U && kLevelEvidence[1].one_lanes[1] == 25U);
  static_assert(kLevelEvidence[1].highest_level_rgb_lanes[0] == 8U && kLevelEvidence[1].highest_level_rgb_lanes[1] == 25U);
  static_assert(kCases[9].width == 6U && kCases[9].height == 4U && kCases[9].dither_type == 7U && kCases[9].palette == 0U && kCases[9].levels == 4U);
  static_assert(kCases[9].threshold == 0.1f && kCases[9].matrix_scale == 2.0f && kCases[9].render_scale == 1.0f && kCases[9].mix_amount == 0.8f && kCases[9].time == -0.2f);
  static_assert(kCases[9].tile_offset[0] == -9.0f && kCases[9].tile_offset[1] == 2.0f && kCases[9].full_resolution[0] == 18.0f && kCases[9].full_resolution[1] == 12.0f && kCases[9].phase == 10U);
  static_assert(kSignedTraces.size() == 1U);
  static_assert(kSignedTraces[0].case_name == "error-diffusion-negative-tile");
  static_assert(kSignedTraces[0].method == "source-derived-error-diffusion-trace-v1");
  static_assert(kSignedTraces[0].source_path == "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/dither/dither.glsl");
  static_assert(kSignedTraces[0].source_sha256 == "a966f1746213c8206c5cb57a88cafd8033eb8f8cb08b207209eb31479a11abdb");
  static_assert(kSignedTraces[0].source_block_span == "508-566");
  static_assert(kSignedTraces[0].source_fetch_span == "500-506");
  static_assert(kSignedTraces[0].signed_division == "truncate_toward_zero");
  static_assert(kSignedTraces[0].fs_block == 4);
  static_assert(kSignedTraces[0].cell_size == 2.0f);
  static_assert(kSignedTraces[0].cell_size == kCases[9].matrix_scale * kCases[9].render_scale);
  static_assert(kSignedTraces[0].negative_global_coordinate);
  static_assert(kSignedTraces[0].negative_block_origin);
  static_assert(kSignedTraces[0].points[0].global[0] < 0.0f && kSignedTraces[0].points[0].cell[0] < 0 && kSignedTraces[0].points[0].block_origin[0] < 0);
  static_assert(kSignedTraces[0].points[0].fragment[0] == 0 && kSignedTraces[0].points[0].fragment[1] == 0);
  static_assert(kSignedTraces[0].points[0].global[0] == -8.5f && kSignedTraces[0].points[0].global[1] == 2.5f);
  static_assert(kSignedTraces[0].points[0].cell[0] == -5 && kSignedTraces[0].points[0].cell[1] == 1);
  static_assert(kSignedTraces[0].points[0].block_origin[0] == -4 && kSignedTraces[0].points[0].block_origin[1] == 0);
  static_assert(kSignedTraces[0].points[1].fragment[0] == 1 && kSignedTraces[0].points[1].fragment[1] == 0);
  static_assert(kSignedTraces[0].points[1].global[0] == -7.5f && kSignedTraces[0].points[1].global[1] == 2.5f);
  static_assert(kSignedTraces[0].points[1].cell[0] == -4 && kSignedTraces[0].points[1].cell[1] == 1);
  static_assert(kSignedTraces[0].points[1].block_origin[0] == -4 && kSignedTraces[0].points[1].block_origin[1] == 0);
  static_assert(kSignedTraces[0].points[2].fragment[0] == 5 && kSignedTraces[0].points[2].fragment[1] == 0);
  static_assert(kSignedTraces[0].points[2].global[0] == -3.5f && kSignedTraces[0].points[2].global[1] == 2.5f);
  static_assert(kSignedTraces[0].points[2].cell[0] == -2 && kSignedTraces[0].points[2].cell[1] == 1);
  static_assert(kSignedTraces[0].points[2].block_origin[0] == 0 && kSignedTraces[0].points[2].block_origin[1] == 0);
  static_assert(kSignedTraces[0].clamp_fragment[0] == 0 && kSignedTraces[0].clamp_fragment[1] == 0);
  static_assert(kSignedTraces[0].clamp_block_origin[0] == -4 && kSignedTraces[0].clamp_block_origin[1] == 0);
  static_assert(kSignedTraces[0].clamp_loop_offset[0] == -4 && kSignedTraces[0].clamp_loop_offset[1] == -4);
  static_assert(kSignedTraces[0].clamp_cell[0] == -8 && kSignedTraces[0].clamp_cell[1] == -4);
  static_assert(kSignedTraces[0].clamp_global[0] == -15.0f && kSignedTraces[0].clamp_global[1] == -7.0f);
  static_assert(kSignedTraces[0].clamp_raw_local[0] == -6 && kSignedTraces[0].clamp_raw_local[1] == -9);
  static_assert(kSignedTraces[0].clamp_clamped[0] == 0 && kSignedTraces[0].clamp_clamped[1] == 0);
  static_assert(kSignedTraces[0].clamp_fragment[0] >= 0 && kSignedTraces[0].clamp_fragment[0] < static_cast<int>(kCases[9].width) && kSignedTraces[0].clamp_fragment[1] >= 0 && kSignedTraces[0].clamp_fragment[1] < static_cast<int>(kCases[9].height));
  static_assert(kSignedTraces[0].clamp_witness && kSignedTraces[0].clamp_visited);
  static_assert(kAuthorityBlocker.route == "palette != PALETTE_INPUT");
  static_assert(kAuthorityBlocker.error == "ditherWithPalette(...).reduce is not a function");
  static_assert(kAuthorityBlocker.source_anchor == "ditherWithPalette(...).reduce((res,el,i)=>(res[i] = el, res), result)");
  static_assert(kAuthorityBlocker.case_name == "palette-blocker");
  static_assert(kAuthorityBlocker.direct_message == "ditherWithPalette(...).reduce is not a function");
  static_assert(kAuthorityBlocker.public_message == "ditherWithPalette(...).reduce is not a function");
  static_assert(kAuthorityBlocker.palette == 2U);
  static_assert(kAuthorityBlocker.reproducible && kAuthorityBlocker.direct_throws && kAuthorityBlocker.public_throws);
  static_assert(kComparerPolicy.f32_words_exact && kComparerPolicy.rgba8_bytes_exact && kComparerPolicy.dimensions_before_data && kComparerPolicy.signed_zero_exact && kComparerPolicy.input_bits_exact && kComparerPolicy.public_direct_exact && kComparerPolicy.repeat_identity_exact);
  static_assert(kComparerSelfTests.good_equal && kComparerSelfTests.dimensions_mismatch && kComparerSelfTests.short_lane_count && kComparerSelfTests.rgba8_mismatch && kComparerSelfTests.signed_zero);
  static_assert(kCpuClosure.size() == 22U);
  static_assert(kCpuClosure[0].relative_path == "src/csl/glsl-kernel.js" && kCpuClosure[0].sha256 == "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa");
  static_assert(kCpuClosure[1].relative_path == "src/csl/glsl-runtime.js" && kCpuClosure[1].sha256 == "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072");
  static_assert(kCpuClosure[2].relative_path == "src/csl/runtime.js" && kCpuClosure[2].sha256 == "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee");
  static_assert(kCpuClosure[3].relative_path == "src/effects/adapters/bit-effects.js" && kCpuClosure[3].sha256 == "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7");
  static_assert(kCpuClosure[4].relative_path == "src/effects/adapters/crt.js" && kCpuClosure[4].sha256 == "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc");
  static_assert(kCpuClosure[5].relative_path == "src/effects/adapters/f32-color.js" && kCpuClosure[5].sha256 == "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046");
  static_assert(kCpuClosure[6].relative_path == "src/effects/adapters/fractal.js" && kCpuClosure[6].sha256 == "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29");
  static_assert(kCpuClosure[7].relative_path == "src/effects/adapters/index.js" && kCpuClosure[7].sha256 == "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267");
  static_assert(kCpuClosure[8].relative_path == "src/effects/adapters/julia.js" && kCpuClosure[8].sha256 == "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5");
  static_assert(kCpuClosure[9].relative_path == "src/effects/adapters/median.js" && kCpuClosure[9].sha256 == "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583");
  static_assert(kCpuClosure[10].relative_path == "src/effects/adapters/palette.js" && kCpuClosure[10].sha256 == "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452");
  static_assert(kCpuClosure[11].relative_path == "src/effects/adapters/snow.js" && kCpuClosure[11].sha256 == "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366");
  static_assert(kCpuClosure[12].relative_path == "src/effects/catalog.js" && kCpuClosure[12].sha256 == "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4");
  static_assert(kCpuClosure[13].relative_path == "src/effects/definition.js" && kCpuClosure[13].sha256 == "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02");
  static_assert(kCpuClosure[14].relative_path == "src/effects/generated/canonical-adapter-data.js" && kCpuClosure[14].sha256 == "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab");
  static_assert(kCpuClosure[15].relative_path == "src/effects/generated/canonical-kernels.js" && kCpuClosure[15].sha256 == "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe");
  static_assert(kCpuClosure[16].relative_path == "src/effects/generated/kernels.js" && kCpuClosure[16].sha256 == "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01");
  static_assert(kCpuClosure[17].relative_path == "src/effects/generated/upstream-snapshot.js" && kCpuClosure[17].sha256 == "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090");
  static_assert(kCpuClosure[18].relative_path == "src/effects/registry.js" && kCpuClosure[18].sha256 == "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618");
  static_assert(kCpuClosure[19].relative_path == "src/runtime/pass-runner.js" && kCpuClosure[19].sha256 == "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa");
  static_assert(kCpuClosure[20].relative_path == "src/runtime/sampler.js" && kCpuClosure[20].sha256 == "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328");
  static_assert(kCpuClosure[21].relative_path == "src/runtime/surface.js" && kCpuClosure[21].sha256 == "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59");
  static_assert(kBaselineCaseCount == 9U);
  static_assert(kAdversarialCaseCount == 3U);
  return 0;
}
''', encoding="utf-8")
            result = subprocess.run((compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT), "-fsyntax-only", str(unit)), cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
