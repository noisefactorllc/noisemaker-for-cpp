"""Exact five-define runtime proof for Classic Noise."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from tools.glslcpp import check_corpus
from tools.glslcpp.frontend import dynamic_define_hoist, parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import noise_frontend_profile as profile

SOURCE = (Path(check_corpus.__file__).resolve().parents[2]
          / "tools/glslcpp/corpus" / check_corpus.REVISION
          / "sources/classicNoisedeck/noise/noise.glsl")
HISTORICAL_SOURCE = SOURCE.parents[4] / "32d8d3e6a6dbb3dee2dfbcc8d31bd1c52342eca3/sources/classicNoisedeck/noise/noise.glsl"
RUNTIME = {name: "int" for name, _, _ in profile.FIXED_DEFINES}
DEFAULT = {name: int(value) for name, _, value in profile.FIXED_DEFINES}


def candidate(raw: str, runtime: bool):
    source = (dynamic_define_hoist.transform_source(raw, profile.KEY)
              if runtime else raw)
    parsed = parse_program(source, profile.KEY,
                           RUNTIME if runtime else DEFAULT)
    parsed["raw_source"] = raw
    return analyze_program(parsed, profile.KEY)


class ClassicNoiseRuntimeProofTests(unittest.TestCase):
    def test_default_and_runtime_projection_keep_exact_closure(self):
        raw = SOURCE.read_text(encoding="utf-8")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        for runtime, expected_functions, expected_declarations, loop_count in (
                (False, 15, 25, 1), (True, 40, 32, 3)):
            with self.subTest(runtime=runtime):
                selected_raw = raw if runtime else HISTORICAL_SOURCE.read_text()
                digest = hashlib.sha256(selected_raw.encode()).hexdigest()
                program = candidate(selected_raw, runtime)
                frontend = profile.authenticate_noise_frontend(
                    program, digest, profile.PROFILE)
                profile.verify_noise_frontend(program, frontend)
                projected = profile.apply_noise_frontend(
                    program, digest, profile.PROFILE)
                proof = profile.authenticate_noise_projection(
                    projected, digest, profile.PROFILE)
                profile.verify_noise_projection(projected, proof)
                contract = profile.authenticate_noise_runtime(
                    projected, digest, profile.PROFILE)
                self.assertEqual(expected_functions, len(projected.functions))
                self.assertEqual(expected_declarations,
                                 len(projected.declarations))
                self.assertEqual(loop_count,
                                 projected.counted_loop_proof.loop_count)
                self.assertEqual(0,
                                 projected.counted_loop_proof.unproved_loop_count)
                self.assertEqual(8, contract.seed.maximum)
                self.assertTrue(any(contract.seed.symbol is parameter
                    for function in projected.functions
                    for parameter in function.parameters))
                if runtime:
                    self.assertEqual(6, len(frontend.dead_functions))
                    self.assertEqual({"fwdA", "fwdB"},
                        {item.symbol.name for item in projected.declarations
                         if item.type.display() == "mat3"})

    def test_runtime_forged_source_tree_and_record_reject(self):
        raw = SOURCE.read_text(encoding="utf-8")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        program = candidate(raw, True)
        forged = (
            ("raw", dataclasses.replace(program, raw_source=raw + "\n"),
             digest, profile.PROFILE),
            ("normalized", dataclasses.replace(program,
                source=program.source + "\n"), digest, profile.PROFILE),
            ("functions", dataclasses.replace(program,
                functions=program.functions[:-1]), digest, profile.PROFILE),
            ("declarations", dataclasses.replace(program,
                declarations=program.declarations[:-1]), digest,
                profile.PROFILE),
            ("caller hash", program, "0" * 64, profile.PROFILE),
            ("profile", program, digest, None),
            ("key", dataclasses.replace(program, key="forged:key"),
             digest, profile.PROFILE),
        )
        for name, changed, changed_digest, carrier in forged:
            with self.subTest(mutation=name):
                with self.assertRaises(ValueError):
                    profile.authenticate_noise_frontend(
                        changed, changed_digest, carrier)
        damaged = dict(profile._DYNAMIC_SOURCE_LOCKS[digest], _DYNAMIC_IDENTITY=())
        with mock.patch.dict(profile._DYNAMIC_SOURCE_LOCKS, {digest: damaged}):
            with self.assertRaises(ValueError):
                profile.authenticate_noise_frontend(
                    program, digest, profile.PROFILE)
        projected = profile.apply_noise_frontend(
            program, digest, profile.PROFILE)
        with self.assertRaises(ValueError):
            profile.authenticate_noise_projection(
                dataclasses.replace(projected,
                    declarations=projected.declarations[:-1]),
                digest, profile.PROFILE)


if __name__ == "__main__":
    unittest.main()
