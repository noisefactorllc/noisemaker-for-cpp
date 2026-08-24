from __future__ import annotations

import hashlib
import importlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = "synth/gradient:gradient"
PROFILE = "cross-lane-assignment-v1"
RAW = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6" / "sources/synth/gradient/gradient.glsl"
RAW_SHA256 = "308537be8f376750a2239be89a07e558e54ee1661a0ea360c6a3e48b8c6e7a75"
ORACLE = ROOT / "docs/port-engineering/cross-lane-parity/gradient_oracle.mjs"


def _analyzed(raw: str | None = None, key: str = KEY):
    source = RAW.read_text(encoding="utf-8") if raw is None else raw
    return analyze_program(parse_program(source, key, generate_typed_slice._defaults(ROOT, key)), key)


class CrossLaneAssignmentProfileTests(unittest.TestCase):
    def _oracle_env(self):
        env = os.environ.copy()
        worker_root = pathlib.Path(env.get(
            "NOISEMAKER_WORKER_ROOT",
            pathlib.Path(tempfile.gettempdir()) / "noisemaker-cpp-cross-lane"))
        env.update({
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(worker_root / "pycache"),
            "TMPDIR": str(worker_root / "tmp"),
            "NOISEMAKER_REGEN_CACHE": str(worker_root / "regen-cache"),
        })
        pathlib.Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
        return env

    def _authority_root(self):
        value = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not value:
            self.skipTest("authority-dependent oracle test skipped: NOISEMAKER_CPU_ROOT is unset")
        root = pathlib.Path(value)
        if not root.is_dir():
            self.skipTest(f"authority-dependent oracle test skipped: NOISEMAKER_CPU_ROOT is missing: {root}")
        return root

    def _assignment_parts(self, program):
        host = next(item for item in program.functions if item.id == 29)
        statement = next(item for item in host.body
                         if any(expression.kind == "assign"
                                and expression.children
                                and expression.children[0].symbol_id == 50
                                for expression in item.expressions))
        assignment = next(expression for expression in statement.expressions
                           if expression.kind == "assign"
                           and expression.children
                           and expression.children[0].symbol_id == 50)
        return host, statement, assignment

    def _replace_assignment(self, program, assignment):
        host, statement, _ = self._assignment_parts(program)
        expressions = tuple(assignment if expression.kind == "assign"
                            and expression.children
                            and expression.children[0].symbol_id in (49, 50)
                            else expression for expression in statement.expressions)
        new_statement = replace(statement, expressions=expressions)
        new_body = tuple(new_statement if item is statement else item
                         for item in host.body)
        new_host = replace(host, body=new_body)
        functions = tuple(new_host if item is host else item
                          for item in program.functions)
        return replace(program, functions=functions)

    def _replace_alias(self, program, alias):
        host = next(item for item in program.functions if item.id == 29)
        statement = next(item for item in host.body
                         if any(expression.kind == "declaration"
                                and expression.symbol_id == 50
                                for expression in item.expressions))
        expressions = tuple(alias if expression.kind == "declaration"
                            and expression.symbol_id == 50
                            else expression for expression in statement.expressions)
        new_statement = replace(statement, expressions=expressions)
        new_host = replace(host, body=tuple(new_statement if item is statement else item
                                            for item in host.body))
        return replace(program, functions=tuple(new_host if item is host else item
                                                for item in program.functions))

    def _assert_named_mutation(self, candidate, message):
        module = importlib.import_module("tools.glslcpp.frontend.cross_lane_assignment_profile")
        locks = {
            "_RAW_BYTES": len(candidate.raw_source.encode("utf-8")),
            "_RAW_SHA256": hashlib.sha256(candidate.raw_source.encode("utf-8")).hexdigest(),
            "_NORMALIZED_BYTES": len(candidate.source.encode("utf-8")),
            "_NORMALIZED_SHA256": hashlib.sha256(candidate.source.encode("utf-8")).hexdigest(),
            "_FUNCTIONS_SHA256": module._sha(candidate.functions),
            "_WHOLE_SHA256": module._whole(candidate),
            "_INTERFACE_SHA256": module._interface(candidate),
        }
        with mock.patch.multiple(module, **locks):
            with self.assertRaisesRegex(ValueError, rf"{PROFILE}: .*{message}"):
                module.authenticate_cross_lane_assignment(
                    candidate, locks["_RAW_SHA256"], PROFILE)

    def test_profile_authenticates_gradient_assignment_and_cross_lane_reads(self):
        module = importlib.import_module("tools.glslcpp.frontend.cross_lane_assignment_profile")
        proof = module.authenticate_cross_lane_assignment(_analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(KEY, proof._candidate.key)
        self.assertEqual("rotatedCentered", proof.target.symbol.name)
        self.assertEqual((0, 1), proof.source_lanes)
        self.assertEqual((0, 1), proof.destination_lanes)
        self.assertEqual(proof.rhs_source.symbol_id, proof.target_source.symbol_id)

    def test_gradient_requires_exact_profile_at_both_boundaries(self):
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"synth/gradient:gradient:.*exact cross-lane assignment profile carrier required"):
            generate_typed_slice.validate_capabilities(
                _analyzed(), generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=RAW_SHA256)
        with self.assertRaisesRegex(
                emit_typed_cpp.TypedEmissionError,
                r"synth/gradient:gradient:.*exact cross-lane assignment profile carrier required"):
            emit_typed_cpp.render_typed_cpp(
                _analyzed(), KEY, RAW_SHA256, "probe", "bind_probe")

    def test_shape_mask_is_not_admitted_by_gradient_profile(self):
        module = importlib.import_module("tools.glslcpp.frontend.cross_lane_assignment_profile")
        shape_key = "mixer/shapeMask:shapeMask"
        source = ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6" / "sources/mixer/shapeMask/shapeMask.glsl"
        raw = source.read_text(encoding="utf-8")
        candidate = analyze_program(parse_program(raw, shape_key, generate_typed_slice._defaults(ROOT, shape_key)), shape_key)
        with self.assertRaises(ValueError):
            module.authenticate_cross_lane_assignment(
                candidate, hashlib.sha256(raw.encode()).hexdigest(), PROFILE)

    def test_wrong_destination_fails_destination_lock(self):
        program = _analyzed()
        _, _, assignment = self._assignment_parts(program)
        target, rhs = assignment.children
        self._assert_named_mutation(
            self._replace_assignment(program, replace(assignment, children=(
                replace(target, symbol_id=49), rhs))),
            "wrong destination")

    def test_same_lane_only_rhs_fails_source_lock(self):
        program = _analyzed()
        _, _, assignment = self._assignment_parts(program)
        target, rhs = assignment.children
        def find_swizzle(value):
            if value.kind == "swizzle" and value.member == "x":
                return value
            for child in value.children:
                found = find_swizzle(child)
                if found is not None:
                    return found
            return None
        source_lane = next(find_swizzle(expression)
                           for function in program.functions
                           for statement in function.body
                           for expression in statement.expressions
                           if find_swizzle(expression) is not None)
        source = replace(rhs.children[1], kind="construct", symbol_id=None,
                         children=(source_lane, source_lane),
                         constructor_type=rhs.children[1].type)
        self._assert_named_mutation(
            self._replace_assignment(program, replace(assignment, children=(
                target, replace(rhs, children=(rhs.children[0], source))))),
            "missing or forged cross-lane source")

    def test_reordered_lanes_fail_matrix_route_lock(self):
        program = _analyzed()
        _, _, assignment = self._assignment_parts(program)
        target, rhs = assignment.children
        matrix = rhs.children[0]
        reordered = replace(matrix, children=(matrix.children[0], matrix.children[2],
                                               matrix.children[1], matrix.children[3]))
        self._assert_named_mutation(
            self._replace_assignment(program, replace(assignment, children=(
                target, replace(rhs, children=(reordered, rhs.children[1]))))),
            "reordered or forged matrix lane route")

    def test_missing_reads_fail_read_cardinality_lock(self):
        program = _analyzed()
        _, _, assignment = self._assignment_parts(program)
        target, rhs = assignment.children
        source = replace(rhs.children[1], kind="construct", symbol_id=None,
                         children=(), constructor_type=rhs.children[1].type)
        self._assert_named_mutation(
            self._replace_assignment(program, replace(assignment, children=(
                target, replace(rhs, children=(rhs.children[0], source))))),
            "missing or forged cross-lane source")

    def test_extra_reads_fail_read_cardinality_lock(self):
        program = _analyzed()
        _, _, assignment = self._assignment_parts(program)
        target, rhs = assignment.children
        matrix = rhs.children[0]
        forged_c = replace(matrix.children[0], children=(rhs.children[1],))
        extra = replace(matrix, children=(forged_c, *matrix.children[1:]))
        self._assert_named_mutation(
            self._replace_assignment(program, replace(assignment, children=(
                target, replace(rhs, children=(extra, rhs.children[1]))))),
            "missing or extra source-lane reads")

    def test_forged_alias_fails_alias_dependency_lock(self):
        program = _analyzed()
        host = next(item for item in program.functions if item.id == 29)
        statement = next(item for item in host.body
                         if any(expression.kind == "declaration"
                                and expression.symbol_id == 50
                                for expression in item.expressions))
        alias = next(expression for expression in statement.expressions
                     if expression.kind == "declaration" and expression.symbol_id == 50)
        initializer = replace(alias.children[0], symbol_id=50)
        self._assert_named_mutation(
            self._replace_alias(program, replace(alias, children=(initializer,))),
            "forged alias dependency")

    def test_wrong_key_and_partial_authorization_fail_exact_carrier_lock(self):
        module = importlib.import_module("tools.glslcpp.frontend.cross_lane_assignment_profile")
        with self.assertRaisesRegex(ValueError, r"selected key and exact caller source hash"):
            module.authenticate_cross_lane_assignment(
                replace(_analyzed(), key="foreign/gradient:gradient"), RAW_SHA256, PROFILE)
        with self.assertRaisesRegex(ValueError, r"exact profile carrier required"):
            module.authenticate_cross_lane_assignment(_analyzed(), RAW_SHA256, None)

    def test_authenticated_emitter_is_source_ordered_and_rejects_temporary(self):
        rendered = emit_typed_cpp.render_typed_cpp(
            _analyzed(), KEY, RAW_SHA256, "probe", "bind_probe",
            cross_lane_assignment_profile=PROFILE)
        lane0 = "glsl::set_swizzle<0>(rotatedCentered, (c * glsl::swizzle<0>(centered) + s * glsl::swizzle<1>(centered)));"
        lane1 = "glsl::set_swizzle<1>(rotatedCentered, ((-s) * glsl::swizzle<0>(rotatedCentered) + c * glsl::swizzle<1>(centered)));"
        self.assertIn(lane0, rendered)
        self.assertIn(lane1, rendered)
        self.assertLess(rendered.index(lane0), rendered.index(lane1))
        self.assertNotIn("rotatedCentered = glsl::Mat2", rendered)

    def test_executable_oracle_reruns_mutant_and_checks_recomputed_ledger(self):
        authority_root = self._authority_root()
        env = self._oracle_env()
        for mode in ("--check", "--self-test"):
            result = subprocess.run(
                ["node", str(ORACLE), "--cpu-root", str(authority_root), mode],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ok", result.stdout)
        record = json.loads((ORACLE.parent / "gradient_expected.json").read_text())
        ledger = record["mutant_ledger"]
        self.assertEqual(1, ledger["transform"]["match_count"])
        self.assertEqual(90, ledger["comparison"]["float32_word_difference_count"])
        self.assertEqual(6, ledger["comparison"]["rgba8_byte_difference_count"])
        self.assertIn("first_float32_mismatch", ledger["comparison"])
        self.assertIn("first_rgba8_mismatch", ledger["comparison"])

    def test_executable_oracle_rejects_zero_or_multiple_transform_matches(self):
        authority_root = self._authority_root()
        env = self._oracle_env()
        canonical = authority_root / "src/effects/generated/canonical-kernels.js"
        needle = "var rotatedCentered = centered;"
        with tempfile.TemporaryDirectory(prefix="gradient-zero-", dir=env["TMPDIR"]) as zero_dir:
            zero_root = pathlib.Path(zero_dir) / "cpu"
            shutil.copytree(authority_root, zero_root)
            zero_source = canonical.read_text()
            (zero_root / "src/effects/generated/canonical-kernels.js").write_text(
                zero_source.replace(needle, "var rotatedCentered = new $runtime.PooledFloat32Array(centered);", 1))
            result = subprocess.run(
                ["node", str(ORACLE), "--cpu-root", str(zero_root), "--check"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("found 0", result.stderr)
        with tempfile.TemporaryDirectory(prefix="gradient-multiple-", dir=env["TMPDIR"]) as multiple_dir:
            multiple_root = pathlib.Path(multiple_dir) / "cpu"
            shutil.copytree(authority_root, multiple_root)
            multiple_source = canonical.read_text()
            (multiple_root / "src/effects/generated/canonical-kernels.js").write_text(
                multiple_source.replace(needle, f"{needle}\n{needle}", 1))
            result = subprocess.run(
                ["node", str(ORACLE), "--cpu-root", str(multiple_root), "--check"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("found 2", result.stderr)

    def test_executable_oracle_rejects_forged_recomputed_ledger(self):
        authority_root = self._authority_root()
        env = self._oracle_env()
        with tempfile.TemporaryDirectory(prefix="gradient-ledger-", dir=env["TMPDIR"]) as ledger_dir:
            forged = pathlib.Path(ledger_dir) / "forged.json"
            record = json.loads((ORACLE.parent / "gradient_expected.json").read_text())
            record["mutant_ledger"]["comparison"]["float32_word_difference_count"] = 89
            forged.write_text(json.dumps(record, indent=2) + "\n")
            result = subprocess.run(
                ["node", str(ORACLE), "--cpu-root", str(authority_root), "--json", str(forged), "--check"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("gradient oracle check failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
