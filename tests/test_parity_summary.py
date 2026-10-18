"""The whole-port parity summary counts every case that closure needs.

`scripts/parity-summary` with no arguments must count the corpus lane, every
case of the two CI sweep gates, the define liveness of each claimed effect,
and kit effects that no case renders. These tests drive its counting and its
wiring with stand-in renders; the real renders run in the full CI lanes.
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import re
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/parity-summary"
CI = ROOT / ".github/workflows/ci.yml"


def load_summary():
    loader = importlib.machinery.SourceFileLoader("parity_summary_under_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    # The script's dataclasses resolve their module through sys.modules.
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def ci_sweep_commands() -> dict[str, list[str]]:
    """The arguments of each `tools/parity/sweep.py` step in ci.yml, by report name."""
    commands: dict[str, list[str]] = {}
    for line in CI.read_text(encoding="utf-8").splitlines():
        match = re.search(r"tools/parity/sweep\.py (.*)$", line)
        if not match:
            continue
        args = shlex.split(match.group(1))
        out = args.index("--out")
        name = pathlib.PurePosixPath(args[out + 1]).name
        commands[name] = args[:out] + args[out + 2:]
    return commands


def job(case_id: str, effect_id: str, kind: str = "sampled") -> dict:
    return {"case_id": case_id, "effect_id": effect_id, "kind": kind, "chain_effects": []}


def row(case_id: str, effect_id: str, classification: str, kind: str = "sampled", **extra) -> dict:
    rendered = classification in ("byte_exact", "divergent")
    return {"case_id": case_id, "effect_id": effect_id, "kind": kind, "chain_effects": [],
            "classification": classification, "js_returncode": 0,
            "cpp_returncode": 0 if rendered else 4, **extra}


class SweepGateFlagsTest(unittest.TestCase):
    def test_the_summary_runs_the_ci_sweep_gates_with_their_flags(self) -> None:
        summary = load_summary()
        ci = ci_sweep_commands()
        self.assertEqual({name for name, _, _ in summary.SWEEP_GATES}, set(ci))
        for name, flags, workers in summary.SWEEP_GATES:
            with self.subTest(gate=name):
                args = ci[name]
                index = args.index("--workers")
                self.assertEqual(workers, args[index + 1])
                self.assertEqual([*flags, *summary.SWEEP_LIMITS], args[:index] + args[index + 2:])

    def test_each_sweep_gate_uses_its_ci_worker_count_by_default(self) -> None:
        summary = load_summary()
        commands: list[list[str]] = []

        def run(command, **_kwargs):
            commands.append(command)
            return type("Completed", (), {"returncode": 2, "stderr": "", "stdout": ""})()

        environment = {key: value for key, value in os.environ.items() if key != summary.WORKERS_ENV}
        with tempfile.TemporaryDirectory(prefix="parity-summary-workers-") as directory, \
             patch.object(summary.subprocess, "run", run), \
             patch.dict("os.environ", environment, clear=True), \
             contextlib.redirect_stdout(io.StringIO()):
            summary.run_sweeps(pathlib.Path(directory) / "driver",
                               {"NOISEMAKER_CPU_ROOT": directory, "NOISEMAKER_CPU_AUTHORITY_LEDGER": directory},
                               pathlib.Path(directory), set(), summary.Tally())
        used = [command[command.index("--workers") + 1] for command in commands]
        self.assertEqual(used, [workers for _, _, workers in summary.SWEEP_GATES])


class SweepCountTest(unittest.TestCase):
    def setUp(self) -> None:
        self.summary = load_summary()

    def test_only_a_byte_exact_case_counts_as_exact(self) -> None:
        classes = ("byte_exact", "divergent", "cpp_refused_only", "both_refused", "timeout", "harness_error")
        jobs = [job(f"case{i}", "synth/solid") for i in range(len(classes))]
        rows = {f"case{i}": row(f"case{i}", "synth/solid", c) for i, c in enumerate(classes)}
        tally = self.summary.Tally()
        self.summary.count_sweep("sweep", jobs, rows, tally)
        self.assertEqual((tally.expected, tally.exact, tally.fail, tally.missing), (6, 1, 5, 0))
        self.assertEqual(tally.executed, 2)
        self.assertFalse(tally.passed())

    def test_a_case_without_a_result_is_missing(self) -> None:
        tally = self.summary.Tally()
        self.summary.count_sweep("sweep", [job("case0", "synth/solid")], {}, tally)
        self.assertEqual((tally.expected, tally.executed, tally.missing), (1, 0, 1))
        self.assertFalse(tally.passed())

    def test_each_claimed_define_parameter_adds_one_liveness_case(self) -> None:
        jobs, rows = [], {}
        for effect_id, hashes in (("synth/solid", ("a", "b")), ("synth/flat", ("a", "a")),
                                  ("unclaimed/effect", ("a", "a"))):
            for value, digest in enumerate(hashes):
                case_id = f"{effect_id.replace('/', '__')}__define__style__{value}__0"
                jobs.append(job(case_id, effect_id, "define_isolated"))
                rows[case_id] = row(case_id, effect_id, "byte_exact", "define_isolated", rgba8_sha256=digest)
        tally = self.summary.Tally()
        self.summary.count_liveness("sweep-defines", jobs, rows, {"synth/solid", "synth/flat"}, tally)
        self.assertEqual((tally.expected, tally.executed, tally.exact, tally.fail), (2, 2, 1, 1))
        self.assertIn("synth/flat `style`: NOT DEMONSTRATED", "\n".join(tally.failures))


class WholePortSummaryTest(unittest.TestCase):
    """A no-argument run counts the corpus, both sweeps, liveness and kit coverage."""

    def setUp(self) -> None:
        self.summary = load_summary()
        self.temporary = tempfile.TemporaryDirectory(prefix="parity-summary-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.kit = self.root / "compat-effects.json"
        self.kit.write_text(json.dumps(["synth/solid", "synth3d/noise3d", "filter/neverRendered"]))
        self.commands: list[list[str]] = []

    def corpus(self, records, authority_refused, driver, node, env, tally) -> None:
        for _record in records:
            tally.expected += 1
            tally.executed += 1
            tally.exact += 1

    def sweep(self, command, **_kwargs):
        self.commands.append(command)
        report = pathlib.Path(command[command.index("--out") + 1])
        report.mkdir(parents=True)
        if "--define-enum" in command:
            jobs = [job(f"synth3d__noise3d__define__octaves__{v}__0", "synth3d/noise3d", "define_isolated")
                    for v in (0, 1)]
            rows = [row(j["case_id"], j["effect_id"], "byte_exact", "define_isolated", rgba8_sha256=str(v))
                    for v, j in enumerate(jobs)]
        else:
            jobs = [job("synth__solid__default", "synth/solid", "default"),
                    job("synth3d__noise3d__default", "synth3d/noise3d", "default")]
            rows = [row(j["case_id"], j["effect_id"], "byte_exact", j["kind"]) for j in jobs]
        (report / "run-manifest.json").write_text(json.dumps({"jobs": jobs}))
        (report / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        stderr = "[sweep gate] kit: 0 failing of %d cases\n" % len(jobs)
        return type("Completed", (), {"returncode": 0, "stderr": stderr, "stdout": ""})()

    def run_main(self) -> tuple[int, str]:
        manifest = {"counts": {"admitted": 1},
                    "records": [{"recordKind": "admitted", "id": "synth/solid#default", "effectId": "synth/solid"}]}
        output = io.StringIO()
        with patch.object(sys, "argv", ["parity-summary"]), \
             patch.object(self.summary, "load_corpus", return_value=manifest), \
             patch.object(self.summary, "load_exclusions", return_value={"authorityRefused": []}), \
             patch.object(self.summary, "resolve_driver", return_value=self.root / "driver"), \
             patch.object(self.summary, "resolve_authority_env",
                          return_value={"NOISEMAKER_CPU_ROOT": str(self.root),
                                        "NOISEMAKER_CPU_AUTHORITY_LEDGER": str(self.root / "ledger")}), \
             patch.object(self.summary, "KIT", self.kit), \
             patch.object(self.summary, "run_corpus", self.corpus), \
             patch.object(self.summary.subprocess, "run", self.sweep), \
             patch.dict("os.environ", {"NOISEMAKER_PARITY_OUT": str(self.root / "reports")}), \
             contextlib.redirect_stdout(output):
            code = self.summary.main()
        return code, output.getvalue()

    def test_the_summary_counts_every_case_and_reports_an_unrendered_kit_effect(self) -> None:
        code, output = self.run_main()
        last = output.strip().splitlines()[-1]
        self.assertTrue(last.startswith("PARITY-SUMMARY "), last)
        counts = json.loads(last.split(" ", 1)[1])
        # 1 corpus record, 2 sweep cases, 2 define cases, 1 liveness case, and
        # filter/neverRendered, which the kit claims and no case renders.
        self.assertEqual(counts, {"expected": 7, "executed": 6, "exact": 6, "strict": 0, "near": 0,
                                  "defer": 0, "skip": 0, "fail": 0, "missing": 1})
        self.assertEqual(code, 1)
        self.assertIn("filter/neverRendered: the kit claims it, but no case renders it", output)
        self.assertEqual(len(self.commands), 2)
        self.assertIn("sweep: [sweep gate] kit: 0 failing of 2 cases", output)


if __name__ == "__main__":
    unittest.main()
