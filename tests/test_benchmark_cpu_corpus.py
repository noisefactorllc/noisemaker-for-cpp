"""Contract tests for the C++ CPU corpus benchmark driver.

The driver produces performance numbers, so nothing here asserts a timing
value: correctness blocks, performance only reports. What is asserted is the
shape of the protocol that makes a number trustworthy -- one compile, a fenced
render-only measurement, a mandatory untimed correctness execution before any
warmup, fail-closed refusals with no partial output, output paths that cannot
land inside the checkout, and a normalized plan relation that is identical to
the JS CPU authority's.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import (
    BENCHMARK_SAMPLES,
    BENCHMARK_SCHEMA,
    BENCHMARK_WARMUPS,
    JS_RUNNER,
    PASS_KEY_COUNTEREXAMPLE,
    RELATION_SCHEMA,
    admitted_records,
    contains_declared_tail,
    load_corpus,
    load_exclusions,
    record_flags,
    relation_field_diff,
    relation_sha256,
    resolve_cpu_root,
    resolve_driver,
)
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics

ROOT = pathlib.Path(__file__).resolve().parents[1]
DRIVER_SOURCES = (
    ROOT / "tools/benchmark/run_cpp_benchmark.cpp",
    ROOT / "tools/benchmark/corpus_case.cpp",
    ROOT / "tools/benchmark/corpus_case.hpp",
)

# A bounded cross-lane subset: a three-pass filter behind a starter with two
# distinct format spellings, the pass whose display name and census program
# disagree, a single-pass filter chain, and a multi-pass blur.
CROSS_LANE_SUBSET = (
    "filter/bloom",
    "classicNoisedeck/bitEffects",
    "filter/blur",
    "filter/invert",
)


def resolve_benchmark_driver() -> pathlib.Path:
    return resolve_driver("NOISEMAKER_DSL_CPU_BENCHMARK", "noisemaker-dsl-cpu-benchmark")


def find_record(effect_id: str) -> dict:
    for record in admitted_records(load_corpus()):
        if record["effectId"] == effect_id:
            return record
    raise AssertionError(f"{effect_id} is not an admitted corpus record")


class BenchmarkDriverCliTest(unittest.TestCase):
    """Flag-contract behaviour. None of these reach the executor."""

    def setUp(self) -> None:
        self.driver = resolve_benchmark_driver()

    def run_driver(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(self.driver), *args], capture_output=True, text=True)

    def test_describe_prints_the_frozen_contract_and_refuses_company(self) -> None:
        described = self.run_driver("--describe")
        self.assertEqual(described.returncode, 0, described.stderr)
        for expected in ("--timing-mode render_only|compile_and_render",
                         BENCHMARK_SCHEMA, RELATION_SCHEMA,
                         "no PNG, no screenshot, no epsilon"):
            self.assertIn(expected, described.stdout)
        self.assertEqual(self.run_driver("--describe", "--warmups", "5").returncode, 2)

    def test_unknown_duplicate_and_missing_flags_are_usage_violations(self) -> None:
        base = ["--source-file", str(pathlib.Path(tempfile.gettempdir()) / "noisemaker-nonexistent.dsl"), "--source-sha256", "0" * 64]
        self.assertEqual(self.run_driver(*base, "--tolerance", "0").returncode, 2)
        self.assertEqual(self.run_driver(*base, "--epsilon", "0").returncode, 2)
        # The admitted corpus carries no seed surfaces. A driver that accepted
        # one and rendered without it would silently answer a different case.
        self.assertEqual(self.run_driver(*base, "--seed-surface", "a.rgba8").returncode, 2)
        self.assertEqual(self.run_driver(*base, "--width", "17", "--width", "17").returncode, 2)
        self.assertEqual(self.run_driver("--width", "17").returncode, 2)

    def test_the_driver_binary_carries_no_png_encoder(self) -> None:
        # Not a substring check on the sources: the binary itself must carry no
        # PNG symbol, so no future edit can reach an encoder that exists in the
        # linked library.
        symbols = subprocess.run(["nm", str(self.driver)], capture_output=True, text=True)
        self.assertEqual(symbols.returncode, 0, symbols.stderr)
        self.assertEqual(
            [line for line in symbols.stdout.splitlines() if "png" in line.lower()], [])
        # There is no epsilon and no tolerance anywhere in the shared path
        # either: comparison is zero tolerance and lives in exact_compare.py.
        for source in DRIVER_SOURCES[1:]:
            body = source.read_text(encoding="utf-8").lower()
            self.assertNotIn("epsilon", body)
            self.assertNotIn("tolerance", body)

    def test_the_shared_path_hardcodes_the_executable_compile_spelling(self) -> None:
        # `require_executable` is inside the canonical plan payload, so a
        # compile through `Renderer::compile()` (which passes CompileOptions{})
        # yields a different planPayloadSha256 for identical source bytes --
        # a difference invisible in the rendered pixels.
        shared = (ROOT / "tools/benchmark/corpus_case.cpp").read_text(encoding="utf-8")
        self.assertIn("{.require_executable = true}", shared)
        self.assertEqual(shared.count("dsl::compile("), 1)
        self.assertEqual(shared.count("GraphExecutor{}.execute("), 1)
        for source in DRIVER_SOURCES[:1]:
            body = source.read_text(encoding="utf-8")
            self.assertNotIn("dsl::compile(", body)
            self.assertNotIn(".compile(", body)

    def test_the_pass_key_rule_pins_the_census_program_not_the_display_name(self) -> None:
        # The counter-example is carried in code so a refactor to `pass.name`
        # fails loudly instead of quietly diverging on all 166 records.
        self.assertEqual(
            f"{PASS_KEY_COUNTEREXAMPLE['effectId']}:{PASS_KEY_COUNTEREXAMPLE['program']}",
            PASS_KEY_COUNTEREXAMPLE["passKey"])
        self.assertNotEqual(PASS_KEY_COUNTEREXAMPLE["name"],
                            PASS_KEY_COUNTEREXAMPLE["program"])
        runner = JS_RUNNER.read_text(encoding="utf-8")
        self.assertIn("${definition.id}:${pass.program}", runner)


class BenchmarkDriverExecutionTest(unittest.TestCase):
    """Behaviour that reaches the real authenticated executor."""

    def setUp(self) -> None:
        self.driver = resolve_benchmark_driver()
        self.temporary = tempfile.TemporaryDirectory(
            prefix="noisemaker-cpu-benchmark-")
        self.addCleanup(self.temporary.cleanup)
        self.scratch = pathlib.Path(self.temporary.name)

    def invoke(self, record: dict, *, warmups: int = BENCHMARK_WARMUPS,
               samples: int = BENCHMARK_SAMPLES, timing_mode: str = "render_only",
               rgba8: pathlib.Path | None = None,
               benchmark: pathlib.Path | None = None,
               relation: pathlib.Path | None = None,
               overrides: dict[str, str] | None = None,
               repo_root: pathlib.Path = ROOT) -> subprocess.CompletedProcess[str]:
        name = record["effectId"].replace("/", "__")
        source = self.scratch / f"{name}.dsl"
        source.write_text(record["source"], encoding="utf-8")
        options = record["options"]
        flags = {
            "--record-id": record["id"],
            "--one-shot": str(options["oneShot"]),
            "--render-scale": repr(options["renderScale"]),
            "--timing-mode": timing_mode,
            "--warmups": str(warmups),
            "--samples": str(samples),
            "--repo-root": str(repo_root),
            "--rgba8-output": str(rgba8 or self.scratch / f"{name}.rgba8"),
            "--benchmark-output": str(benchmark or self.scratch / f"{name}.benchmark.json"),
        }
        if relation is not None:
            flags["--plan-relation-output"] = str(relation)
        flags.update(overrides or {})
        argv = [str(self.driver), *record_flags(record, source)]
        for key, value in flags.items():
            argv += [key, value]
        return subprocess.run(argv, capture_output=True, text=True)

    def test_a_rendered_record_emits_a_complete_parsable_record(self) -> None:
        record = find_record("filter/bloom")
        relation = self.scratch / "bloom.relation.json"
        result = self.invoke(record, relation=relation)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((self.scratch / "filter__bloom.benchmark.json").read_text())
        self.assertEqual(document["schema"], BENCHMARK_SCHEMA)
        self.assertEqual(document["mode"], "render_only")
        self.assertEqual(len(document["sampleNs"]), BENCHMARK_SAMPLES)
        self.assertTrue(all(isinstance(sample, int) and sample >= 0
                            for sample in document["sampleNs"]))
        self.assertEqual(document["output"]["format"], "rgba8")
        self.assertEqual(document["output"]["orientation"], "top-down")
        self.assertEqual(document["correctness"], {
            "status": "rendered", "finalRoute": "o0",
            "passCount": document["planRelation"]["passCount"]})
        # The std::quoted ADL hijack produces syntactically valid JSON with
        # empty arrays, so emptiness is checked, not just parsability.
        for field in ("stepKinds", "effectIds", "passKeys", "passFormats", "routes"):
            self.assertTrue(document["planRelation"][field],
                            f"{field} must not be empty")
        self.assertEqual(document["planRelation"],
                         json.loads(relation.read_text(encoding="utf-8")))
        self.assertEqual(relation_sha256(document["planRelation"]),
                         document["planRelation"]["relationSha256"])
        # `require_executable` is inside the canonical plan payload; reading it
        # true off the emitted plan is direct evidence the payload was built
        # with the render-path spelling.
        self.assertTrue(document["planIdentity"]["requireExecutable"])
        self.assertTrue(document["planIdentity"]["validated"])
        self.assertTrue(document["planIdentity"]["executable"])
        self.assertEqual(document["planIdentity"]["provenanceSourceSha256"],
                         record["sourceSha256"])
        self.assertEqual(document["platform"]["driver"], "cpp-cpu")
        self.assertIn("-ffp-contract=off", document["platform"]["flags"])

    def test_render_only_compiles_once_regardless_of_sample_count(self) -> None:
        record = find_record("filter/blur")
        for samples in (BENCHMARK_SAMPLES, BENCHMARK_SAMPLES * 2):
            result = self.invoke(record, samples=samples)
            self.assertEqual(result.returncode, 0, result.stderr)
            document = json.loads((self.scratch / "filter__blur.benchmark.json").read_text())
            self.assertEqual(document["compileCount"], 1)
            self.assertEqual(len(document["sampleNs"]), samples)
            # Registry construction is reported separately so it can never
            # hide inside a render number.
            self.assertGreater(document["setupNs"], 0)
            self.assertGreater(document["compileNs"], 0)

    def test_compile_and_render_recompiles_every_measured_iteration(self) -> None:
        record = find_record("filter/blur")
        result = self.invoke(record, timing_mode="compile_and_render")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((self.scratch / "filter__blur.benchmark.json").read_text())
        self.assertEqual(document["mode"], "compile_and_render")
        self.assertEqual(document["compileCount"],
                         BENCHMARK_WARMUPS + BENCHMARK_SAMPLES + 1)

    def test_warmup_and_sample_floors_are_enforced(self) -> None:
        record = find_record("filter/blur")
        self.assertEqual(self.invoke(record, warmups=BENCHMARK_WARMUPS - 1).returncode, 2)
        self.assertEqual(self.invoke(record, samples=BENCHMARK_SAMPLES - 1).returncode, 2)

    def test_one_shot_and_render_scale_are_asserted_never_dropped(self) -> None:
        record = find_record("filter/blur")
        self.assertEqual(
            self.invoke(record, overrides={"--one-shot": "continuous"}).returncode, 2)
        self.assertEqual(
            self.invoke(record, overrides={"--one-shot": "whenever"}).returncode, 2)
        self.assertEqual(
            self.invoke(record, overrides={"--render-scale": "0.5"}).returncode, 2)

    def test_a_source_digest_mismatch_stops_before_any_work(self) -> None:
        record = find_record("filter/blur")
        result = self.invoke(record, overrides={"--source-sha256": "0" * 64})
        # `record_flags` supplies the real digest first; the override appends a
        # second one, which the closed flag set rejects as a duplicate.
        self.assertEqual(result.returncode, 2)
        forged = dict(record, sourceSha256="0" * 64)
        self.assertEqual(self.invoke(forged).returncode, 3)
        self.assertFalse((self.scratch / "filter__blur.rgba8").exists())

    def test_an_in_repository_output_path_is_refused_and_writes_nothing(self) -> None:
        record = find_record("filter/blur")
        inside = ROOT / "tests/fixtures/dsl/should-never-exist.rgba8"
        result = self.invoke(record, rgba8=inside)
        self.assertEqual(result.returncode, 6, result.stdout)
        self.assertFalse(inside.exists())
        self.assertFalse((self.scratch / "filter__blur.benchmark.json").exists())

    def test_a_relative_output_path_is_refused(self) -> None:
        record = find_record("filter/blur")
        result = self.invoke(record, overrides={"--rgba8-output": "relative.rgba8"})
        self.assertEqual(result.returncode, 6, result.stdout)

    def test_refusals_are_structured_and_leave_no_partial_output(self) -> None:
        # Refusals are execute-time, never compile-time: both of these compile
        # cleanly and throw out of GraphExecutor::execute. Without the untimed
        # correctness execution the throw would land inside the timed region.
        exclusions = load_exclusions()
        for effect_id, expected_code in (("filter/median", "7"), ("filter/lighting", "5")):
            record = find_record(effect_id)
            name = effect_id.replace("/", "__")
            result = self.invoke(record)
            self.assertEqual(result.returncode, 4, result.stdout)
            refusal = json.loads(result.stdout)
            self.assertEqual(refusal["status"], "refused")
            self.assertEqual(refusal["code"], expected_code)
            self.assertTrue(refusal["detail"])
            if effect_id in exclusions["executorRefused"]:
                self.assertEqual(refusal["detail"], exclusions["executorRefused"][effect_id])
            self.assertFalse((self.scratch / f"{name}.rgba8").exists())
            self.assertFalse((self.scratch / f"{name}.benchmark.json").exists())
            self.assertNotIn("sampleNs", result.stdout)


class CrossLaneRelationTest(unittest.TestCase):
    """The benchmark driver and the JS CPU authority must agree exactly."""

    def setUp(self) -> None:
        self.driver = resolve_benchmark_driver()
        self.cpu_root = resolve_cpu_root()
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is required for the CPU authority runner")
        self.temporary = tempfile.TemporaryDirectory(
            prefix="noisemaker-cross-lane-")
        self.addCleanup(self.temporary.cleanup)
        self.scratch = pathlib.Path(self.temporary.name)

    def test_relations_and_bytes_agree_on_a_bounded_subset(self) -> None:
        for effect_id in CROSS_LANE_SUBSET:
            with self.subTest(effect=effect_id):
                record = find_record(effect_id)
                name = effect_id.replace("/", "__")
                source = self.scratch / f"{name}.dsl"
                source.write_text(record["source"], encoding="utf-8")
                case = self.scratch / f"{name}.case.json"
                case.write_text(json.dumps(record), encoding="utf-8")
                options = record["options"]

                js_raw = self.scratch / f"{name}.js.rgba8"
                js_relation = self.scratch / f"{name}.js.relation.json"
                js = subprocess.run(
                    [self.node, str(JS_RUNNER), "--cpu-root", str(self.cpu_root),
                     "--case", str(case), "--rgba8-output", str(js_raw),
                     "--metadata-output", str(self.scratch / f"{name}.js.json"),
                     "--plan-relation-output", str(js_relation)],
                    capture_output=True, text=True)
                self.assertEqual(js.returncode, 0, js.stderr)

                cpp_raw = self.scratch / f"{name}.cpp.rgba8"
                cpp_relation = self.scratch / f"{name}.cpp.relation.json"
                cpp = subprocess.run(
                    [str(self.driver), *record_flags(record, source),
                     "--record-id", record["id"],
                     "--one-shot", str(options["oneShot"]),
                     "--render-scale", repr(options["renderScale"]),
                     "--timing-mode", "render_only",
                     "--warmups", str(BENCHMARK_WARMUPS),
                     "--samples", str(BENCHMARK_SAMPLES),
                     "--repo-root", str(ROOT),
                     "--rgba8-output", str(cpp_raw),
                     "--benchmark-output", str(self.scratch / f"{name}.cpp.json"),
                     "--plan-relation-output", str(cpp_relation)],
                    capture_output=True, text=True)
                self.assertEqual(cpp.returncode, 0, cpp.stderr)

                left = json.loads(js_relation.read_text(encoding="utf-8"))
                right = json.loads(cpp_relation.read_text(encoding="utf-8"))
                self.assertEqual(relation_field_diff(left, right), [])
                self.assertEqual(left["relationSha256"], right["relationSha256"])
                # Both digests are re-derived here, so the agreement is three
                # independent canonical serializers rather than one trusted
                # implementation compared with itself.
                self.assertEqual(relation_sha256(left), left["relationSha256"])
                self.assertEqual(relation_sha256(right), right["relationSha256"])

                # The corpus record's own plan projection is a containment
                # oracle only: it omits the starter effect and hardcodes one
                # format spelling.
                for document in (left, right):
                    self.assertTrue(contains_declared_tail(
                        document["effectIds"], record["plan"]["effectIds"]))
                    self.assertTrue(contains_declared_tail(
                        document["passKeys"], record["plan"]["passKeys"]))

                result = compare_rgba8(options["width"], options["height"],
                                       js_raw.read_bytes(), cpp_raw.read_bytes())
                self.assertTrue(result["ok"], format_diagnostics(result))


class BenchmarkBuildContractTest(unittest.TestCase):
    def test_the_recorded_flag_string_comes_from_the_target_flag_list(self) -> None:
        # The record must never claim a flag set the target was not built with.
        text = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn(
            "set(NOISEMAKER_BENCHMARK_STRICT_FLAGS -Wall -Wextra -Wpedantic -Werror "
            "-ffp-contract=off)", text)
        self.assertIn(
            'string(JOIN " " NOISEMAKER_BENCHMARK_STRICT_FLAGS_TEXT '
            "${NOISEMAKER_BENCHMARK_STRICT_FLAGS})", text)
        self.assertIn("${NOISEMAKER_BENCHMARK_STRICT_FLAGS}>", text)
        # Shared with the parity driver by compilation, not by copy.
        self.assertEqual(text.count("tools/benchmark/corpus_case.cpp"), 2)
        # A measurement tool, never shipped library surface.
        self.assertNotIn("add_test(NAME noisemaker-dsl-cpu-benchmark", text)
        self.assertNotIn("install(TARGETS noisemaker-dsl-cpu-benchmark", text)


if __name__ == "__main__":
    unittest.main()
