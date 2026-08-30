from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/port-engineering/julia-parity"
GENERATOR = PACKAGE / "julia_oracle_generator.mjs"
MATERIALIZER = ROOT / "tools/glslcpp/generate_julia_native_oracle_include.py"
ORACLE = PACKAGE / "julia-oracles.json"
REPORT = PACKAGE / "julia-oracle-report.md"
INCLUDE = ROOT / "tests/oracles/julia_expected.inc"
AUTHORITY_ENV = "NOISEMAKER_CPU_ROOT"
LIVE_ENV = "NOISEMAKER_FOR_CPU"


# Authority-variable contract.
#
# The julia generator requires --cpu-root, NOISEMAKER_CPU_ROOT and
# NOISEMAKER_FOR_CPU to resolve to one non-symlink pinned root. Other oracle
# suites in this tree give NOISEMAKER_FOR_CPU the opposite meaning: the emboss
# generator (docs/port-engineering/arrays/emboss-parity/
# emboss_parity_oracle_generator.mjs) reads it as the *live* mutable checkout
# and refuses a --cpu-root that overlaps it. One ambient value cannot satisfy
# both readings, so this module stops reading the ambient NOISEMAKER_FOR_CPU
# altogether: it derives its own authority from NOISEMAKER_CPU_ROOT and passes
# that same root as NOISEMAKER_FOR_CPU to every generator it launches.
#
# Nothing is relaxed by that. The generator's same-root requirement is still
# proved positively (every launch below sets both variables to the authority
# and must exit 0) and negatively, by
# test_authority_rejects_literal_dynamic_nonliteral_and_path_roots, which
# asserts the generator refuses a NOISEMAKER_FOR_CPU that is a symlink, that is
# missing, or that names a different real directory.
def _authority() -> pathlib.Path:
    value = os.environ.get(AUTHORITY_ENV)
    if not value:
        # Unset means the machine has no frozen authority (e.g. public CI):
        # skip visibly. A SET-but-wrong root still fails loudly below.
        raise unittest.SkipTest(f"{AUTHORITY_ENV} (the frozen CPU authority) is required")
    path = pathlib.Path(value)
    if not path.is_dir() or path.is_symlink():
        raise AssertionError(f"{AUTHORITY_ENV} must be a non-symlink directory")
    return path


def _sidecar(path: pathlib.Path) -> None:
    sidecar = pathlib.Path(f"{path}.sha256")
    if not sidecar.is_file():
        raise AssertionError(sidecar)
    expected = f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
    if sidecar.read_text() != expected:
        raise AssertionError(f"sidecar drift: {path}")


class JuliaOracleTests(unittest.TestCase):
    def test_package_contract_and_sidecars(self) -> None:
        for path in (GENERATOR, MATERIALIZER, ORACLE, REPORT, INCLUDE):
            self.assertTrue(path.is_file(), path)
            _sidecar(path)
        doc = json.loads(ORACLE.read_text())
        self.assertEqual("noisemaker-for-cpp.julia.pixel-parity.v1", doc["schema"])
        self.assertEqual("synth/julia:julia", doc["program_key"])
        self.assertEqual("juliaFactory", doc["factory"]["name"])
        self.assertTrue(doc["factory"]["adapter_own_key"])
        self.assertEqual(22, len(doc["provenance"]["cpu_snapshot"]["import_closure"]))
        self.assertEqual(18, len(doc["render_cases"]))
        self.assertEqual(25, doc["mutation_anchor_cardinality"]["total"])
        self.assertEqual(25, len(doc["mutation_ledger"]))
        self.assertEqual(1, len(doc["diagnostic_witnesses"]))
        clamp = doc["relations"]["clamp_1001_vs_1000"]
        self.assertEqual(1000, clamp["canonical_1000_loop_entries"])
        self.assertEqual(1000, clamp["canonical_1001_loop_entries"])
        self.assertEqual(1001, clamp["no_clamp_mutant_loop_entries"])
        self.assertTrue(clamp["instrumented_canonical_1001_pixel_identical"])
        self.assertTrue(clamp["instrumented_mutant_pixel_identical"])
        self.assertGreater(clamp["mutant_candidate_changed_float32_lanes"], 0)
        self.assertGreater(clamp["mutant_candidate_changed_rgba8_bytes"], 0)
        self.assertEqual(
            {
                "dimensions_before_access": True,
                "first_mismatch_reported": True,
                "raw_words_and_rgba8_independent": True,
                "cases": {"good": True, "dimensions": True, "short": True,
                           "long": True, "rgba8_count": True,
                           "rgba8_mismatch": True, "signed_zero": True,
                           "nan_payload": True},
            },
            doc["comparer_self_tests"],
        )
        self.assertEqual("vec2", doc["source_uniform_abi"]["resolution"])
        self.assertTrue(all(m["independent"] and (m["witness_cases"] or m["name"] == "result-trap-number")
                            for m in doc["mutation_ledger"]))
        trap_search = doc["result_trap_search"]
        self.assertEqual("poi-trap-first, then trap-search-000000 through trap-search-199999", trap_search["selection_rule"])
        self.assertEqual("trap-search-152217", trap_search["selected"]["binding"]["name"])
        self.assertGreater(trap_search["selected"]["changed_float32_lanes"], 0)
        self.assertGreater(trap_search["selected"]["changed_rgba8_bytes"], 0)
        self.assertEqual(
            len({m["result_sha256"] for m in doc["mutation_ledger"]}), 25)
        required = {
            "cross-lane-dz-assignment", "df64-re2-carrier", "df64-im2-carrier",
            "df64-product-carrier", "df64-next-re-carrier", "out-iteration",
            "out-z-magnitude2", "out-derivative-magnitude2", "out-stripe-sum",
            "out-stripe-count", "out-stripe-last", "out-trap-min",
            "transform-re-owner", "transform-im-owner", "loop-bound",
            "period-loop-bound", "log-smoothing", "log-distance", "log-stripe",
            "log-stripe-normalization", "normal-base", "normal-right", "normal-up",
            "loop-clamp-1001", "result-trap-number",
        }
        self.assertTrue(required <= {m["name"] for m in doc["mutation_ledger"]})
        self.assertEqual(1, doc["diagnostic_witnesses"][0]["period_hit_count"])
        trap = next(m for m in doc["mutation_ledger"] if m["name"] == "result-trap-number")
        self.assertEqual("julia.js:158:7-47", trap["source_span"])
        self.assertEqual([], trap["witness_cases"])
        self.assertTrue(all(row["changed_float32_lanes"] == 0 for row in trap["results"]))
        self.assertTrue(all(row["changed_rgba8_bytes"] == 0 for row in trap["results"]))

    def test_authority_generator_and_materializer(self) -> None:
        authority = _authority()
        env = {**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(authority)}
        commands = (
            ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
            ["node", str(GENERATOR), "--self-test", "--cpu-root", str(authority)],
            [sys.executable, str(MATERIALIZER), "--self-test"],
            [sys.executable, str(MATERIALIZER), "--check"],
        )
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    capture_output=True)
            self.assertEqual(0, result.returncode,
                             result.stdout + result.stderr)

    def test_materializer_rejects_coordinated_forgery_matrix(self) -> None:
        spec = importlib.util.spec_from_file_location("julia_materializer", MATERIALIZER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        original = json.loads(ORACLE.read_text())

        def mutate_input_words(doc):
            obj = doc["render_cases"][0]["input"]
            obj["f32_words_le"][0] = "0x80000000"
            obj["f32_sha256"] = hashlib.sha256(
                materializer._pack(obj["f32_words_le"])).hexdigest()

        def mutate_expected_words(doc):
            obj = doc["render_cases"][0]["expected"]
            obj["f32_words_le"][0] = "0x80000000"
            obj["f32_sha256"] = hashlib.sha256(
                materializer._pack(obj["f32_words_le"])).hexdigest()

        def mutate_rgba(doc):
            obj = doc["render_cases"][0]["expected"]
            obj["rgba8_bytes"][0] = (obj["rgba8_bytes"][0] + 1) % 256
            obj["rgba8_sha256"] = hashlib.sha256(
                bytes(obj["rgba8_bytes"])).hexdigest()

        def mutate_witness(doc):
            for row in doc["mutation_ledger"][0]["results"]:
                if row["float32_witness"] is not None:
                    row["float32_witness"]["actual"] = row["float32_witness"]["expected"]
                    return
            raise AssertionError("fixture has no witness")

        mutations = [
            lambda d: d.__setitem__("schema_version", 2),
            lambda d: d["provenance"]["cpu_snapshot"].__setitem__("argument", "/tmp/forged"),
            lambda d: d["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("sha256", "0" * 64),
            lambda d: d["factory"].__setitem__("text_sha256", "0" * 64),
            lambda d: d["runtime_binding_names"].__setitem__(0, "forged"),
            lambda d: d["exactness_contract"].__setitem__("tolerance", "1e-6"),
            lambda d: d["comparer_self_tests"]["cases"].__setitem__("good", False),
            lambda d: d["control_group"].__setitem__("adapter_own_key", False),
            lambda d: d["render_cases"][0].__setitem__("name", "forged"),
            lambda d: d["render_cases"][0].__setitem__("width", 99),
            lambda d: d["render_cases"][0]["bindings"].__setitem__("time", 99.0),
            mutate_input_words,
            mutate_expected_words,
            mutate_rgba,
            lambda d: d["render_cases"][0]["input"].__setitem__("extra", 1),
            lambda d: d["render_cases"][0]["expected"].__setitem__("extra", 1),
            lambda d: d["mutation_ledger"][0].__setitem__("extra", 1),
            lambda d: d["mutation_ledger"][0].__setitem__("mechanism", "uniform perturbation"),
            lambda d: d["mutation_ledger"][0].__setitem__("source_anchor", "forged"),
            lambda d: d["mutation_ledger"][-1].__setitem__("source_span", "julia.js:158:7-48"),
            lambda d: d["mutation_ledger"][0].__setitem__("anchor_sha256", "0" * 64),
            lambda d: d["mutation_ledger"][0].__setitem__("mutated_factory_text_sha256", "0" * 64),
            lambda d: d["mutation_ledger"][0].__setitem__("result_sha256", "0" * 64),
            mutate_witness,
            lambda d: d["cross_lane_assignment_profile"].__setitem__("contract", "forged"),
            lambda d: d["claim_boundaries"].__setitem__("authority", "forged"),
            lambda d: d["claim_boundaries"].__setitem__("authority", "/tmp/forged"),
            lambda d: d.setdefault("diagnostic_witnesses", [{"period_hit_count": 1}])[0].__setitem__("period_hit_count", 0),
        ]
        for mutate in mutations:
            candidate = json.loads(json.dumps(original))
            mutate(candidate)
            with self.assertRaises(materializer.MaterializationError):
                materializer.validate(candidate)

    def test_materializer_rejects_duplicate_json_keys_with_matching_sidecar(self) -> None:
        spec = importlib.util.spec_from_file_location("julia_materializer_strict", MATERIALIZER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        raw = ORACLE.read_bytes()
        marker = b'"schema": "noisemaker-for-cpp.julia.pixel-parity.v1",'
        forged = raw.replace(
            marker,
            b'"schema": "forged-first", "schema": "noisemaker-for-cpp.julia.pixel-parity.v1",',
            1,
        )
        with tempfile.TemporaryDirectory(prefix="julia-duplicate-") as raw_dir:
            path = pathlib.Path(raw_dir) / "forged.json"
            path.write_bytes(forged)
            pathlib.Path(f"{path}.sha256").write_text(
                f"{hashlib.sha256(forged).hexdigest()}  {path.name}\n")
            with self.assertRaises(materializer.MaterializationError):
                materializer._sidecar_hash(path)
                materializer.validate(materializer.strict_json(forged))

    def test_include_compiles_as_cxx20(self) -> None:
        compiler = shutil.which("c++") or shutil.which("clang++")
        self.assertIsNotNone(compiler, "C++20 compiler unavailable")
        with tempfile.TemporaryDirectory(prefix="julia-include-") as raw:
            unit = pathlib.Path(raw) / "smoke.cpp"
            unit.write_text(
                '#include "tests/oracles/julia_expected.inc"\n'
                'int main() {\n'
                '  using namespace julia_oracle;\n'
                '  static_assert(kBindingNames.size() == 21U);\n'
                '  static_assert(kBindingAbi.size() == kSourceBindingAbi.size());\n'
                '  static_assert(kCases.size() == 18U);\n'
                '  static_assert(kMutations.size() == 25U);\n'
                '  static_assert(kDiagnosticWitnesses.size() == 1U);\n'
                '  static_assert(kBindingAbi[0].runtime_abi.size() > 0U);\n'
                '  static_assert(kSourceBindingAbi[0].source_abi.size() > 0U);\n'
                '  static_assert(kCases[0].output_alpha_f32_word == "0x3f800000");\n'
                '  static_assert(kCases[0].output_alpha_rgba8_byte == 255U);\n'
                '  static_assert(kMutations[0].source_anchor.size() > 0U);\n'
                '  static_assert(kMutations[0].replacement.size() > 0U);\n'
                '  static_assert(kMutations[0].mechanism.size() > 0U);\n'
                '  static_assert(kMutations[0].results.size() == kCases.size());\n'
                '  static_assert(kMutations[0].results[1].float32_witness.index == 0);\n'
                '  static_assert(kMutations[0].results[1].rgba8_witness.index == 0);\n'
                '  static_assert(kDiagnosticWitnesses[0].period_hit_count >= 1U);\n'
                '  const auto& b = kCases.front().bindings;\n'
                '  return static_cast<int>(kBindingNames.size() + kBindingAbi.size() + '
                'kSourceBindingAbi.size() + kMutations[0].source_anchor.size() + '
                'kMutations[0].replacement_sha256.size() + b.iterations);\n'
                '}\n'
            )
            result = subprocess.run(
                [compiler, "-std=c++20", "-I", str(ROOT), "-fsyntax-only", str(unit)],
                cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_authority_rejects_literal_dynamic_nonliteral_and_path_roots(self) -> None:
        authority = _authority()
        with tempfile.TemporaryDirectory(prefix="julia-oracle-paths-") as raw:
            base = pathlib.Path(raw)
            escaped = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(ROOT)],
                cwd=ROOT, text=True, capture_output=True,
                env={**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(authority)},
            )
            self.assertNotEqual(0, escaped.returncode)
            self.assertIn("C++ repository", escaped.stderr)
            clone = base / "cpu"
            shutil.copytree(authority, clone)
            runtime = clone / "src/csl/runtime.js"
            runtime.write_text(runtime.read_text() + "\nvoid import(dynamicSpecifier)\n")
            snapshot_argument = clone
            private_tmp = pathlib.Path("/private/tmp")
            tmp_alias = pathlib.Path("/tmp")
            try:
                relative_clone = clone.relative_to(private_tmp)
            except ValueError:
                relative_clone = None
            if relative_clone is not None and tmp_alias.resolve() == private_tmp.resolve():
                snapshot_argument = tmp_alias / relative_clone
            dynamic = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(snapshot_argument)],
                cwd=ROOT, text=True, capture_output=True,
                env={**os.environ, AUTHORITY_ENV: str(clone), LIVE_ENV: str(clone)},
            )
            self.assertNotEqual(0, dynamic.returncode)
            self.assertIn("nonliteral dynamic import", dynamic.stderr)

            quoted = base / "quoted-cpu"
            shutil.copytree(authority, quoted)
            quoted_runtime = quoted / "src/csl/runtime.js"
            quoted_runtime.write_text(quoted_runtime.read_text() + "\nvoid import('./missing.js' + suffix)\n")
            quoted_result = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(quoted)],
                cwd=ROOT, text=True, capture_output=True,
                env={**os.environ, AUTHORITY_ENV: str(quoted), LIVE_ENV: str(quoted)},
            )
            self.assertNotEqual(0, quoted_result.returncode)
            self.assertIn("nonliteral dynamic import", quoted_result.stderr)

            snapshot_link = base / "snapshot-link"
            snapshot_link.symlink_to(authority, target_is_directory=True)
            symlink_snapshot = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(snapshot_link)],
                cwd=ROOT, env={**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(authority)},
                text=True, capture_output=True)
            self.assertNotEqual(0, symlink_snapshot.returncode)
            self.assertIn("must not be a symlink", symlink_snapshot.stderr)

            live_link = base / "live-link"
            live_link.symlink_to(authority, target_is_directory=True)
            symlink_live = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
                cwd=ROOT, env={**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(live_link)},
                text=True, capture_output=True)
            self.assertNotEqual(0, symlink_live.returncode)
            self.assertIn("same pinned authority", symlink_live.stderr)

            mismatched_pinned = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
                cwd=ROOT, env={**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(base / "missing-live")},
                text=True, capture_output=True)
            self.assertNotEqual(0, mismatched_pinned.returncode)
            self.assertIn("same pinned authority", mismatched_pinned.stderr)

            other_root = base / "other-real-root"
            other_root.mkdir()
            divergent_pinned = subprocess.run(
                ["node", str(GENERATOR), "--check", "--cpu-root", str(authority)],
                cwd=ROOT, env={**os.environ, AUTHORITY_ENV: str(authority), LIVE_ENV: str(other_root)},
                text=True, capture_output=True)
            self.assertNotEqual(0, divergent_pinned.returncode)
            self.assertIn("same pinned authority", divergent_pinned.stderr)

    def test_include_exposes_complete_typed_metadata_views(self) -> None:
        text = INCLUDE.read_text()
        for token in (
            "struct BindingView", "struct SourceBindingView", "struct MutationView",
            "struct DiagnosticWitnessView", "source_abi", "input_f32_sha256",
            "expected_f32_sha256", "expected_rgba8_sha256", "alpha_f32_word",
            "alpha_rgba8_byte", "output_alpha_f32_word", "output_alpha_rgba8_byte",
            "source_anchor", "source_span", "replacement", "result_sha256", "witness_cases",
            "control_cases", "float32_witness", "rgba8_witness",
            "period_hit_count", "diagnostic_witnesses",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
