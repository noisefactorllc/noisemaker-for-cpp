"""Fail-closed evidence handling for the parameter parity sweep."""

from __future__ import annotations

import contextlib
import concurrent.futures
import io
import json
import pathlib
import tempfile
import sys
import unittest
from unittest.mock import patch

from tools.parity import sweep


class SweepEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="parity-sweep-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.job = sweep.Job("solid__default", "synth/solid", "default",
                             "search synth\nsolid().write(o0)\nrender(o0)\n",
                             1, 1, 0.0, 1)
        sweep._init_worker(sweep.RunConfig(
            node="node", driver="cpp-driver", cpu_root="authority", ledger="ledger",
            scratch_root=str(self.root / "scratch"), timeout=1.0))

    def gate(self, rows: list[dict], mode: str = "all", ids: set[str] | None = None) -> int:
        with contextlib.redirect_stderr(io.StringIO()):
            return sweep.gate_failures(rows, mode, {self.job.case_id} if ids is None else ids)

    def row(self, classification: str, **extra) -> dict:
        return {"case_id": self.job.case_id, "effect_id": self.job.effect_id,
                "kind": "default", "chain_effects": [],
                "classification": classification, **extra}

    def test_worker_error_cannot_pass_either_gate(self) -> None:
        for mode in ("all", "kit"):
            for effect in ("synth/solid", "unclaimed/effect"):
                with self.subTest(mode=mode, effect=effect):
                    self.assertEqual(self.gate([self.row("harness_error", effect_id=effect)], mode), 1)

    def test_unknown_classification_cannot_pass(self) -> None:
        self.assertEqual(self.gate([self.row("unknown")]), 1)

    def test_mutual_refusal_cannot_prove_claimed_support(self) -> None:
        for effect in ("synth/solid", "unclaimed/effect"):
            row = self.row("both_refused", effect_id=effect)
            with self.subTest(effect=effect):
                self.assertEqual(self.gate([row], "all"), 1)
                self.assertEqual(self.gate([row], "kit"),
                                 1 if effect == "synth/solid" else 0)

    def test_empty_or_missing_results_cannot_pass(self) -> None:
        self.assertEqual(self.gate([]), 1)
        self.assertEqual(self.gate([], ids=set()), 1)

    def test_float32_outputs_are_required_on_both_lanes(self) -> None:
        for present in (set(), {"node"}, {"cpp-driver"}):
            with self.subTest(present=present):
                result = self.render(present)
                self.assertEqual(result["classification"], "harness_error")
                self.assertEqual(self.gate([result]), 1)

    def test_float32_length_and_content_must_match(self) -> None:
        for payload in (b"", b"\0" * 12, b"\0" * 20, b"\1" + b"\0" * 15):
            with self.subTest(length=len(payload)):
                result = self.render({"node", "cpp-driver"}, cpp_float=payload)
                self.assertEqual(result["classification"], "divergent")
                self.assertEqual(self.gate([result]), 1)

    def test_matching_complete_outputs_pass(self) -> None:
        result = self.render({"node", "cpp-driver"})
        self.assertEqual(result["classification"], "byte_exact")
        self.assertIs(result["float32_ok"], True)
        self.assertEqual(self.gate([result]), 0)

    def test_failed_processes_are_not_semantic_refusals(self) -> None:
        valid = json.dumps({"schema": "noisemaker-cpp.dsl-cpu-run.v1", "status": "refused",
                            "code": "exception", "detail": "invalid parameter"})
        cases = [(-9, 4, valid, "DslError: invalid parameter"),
                 (1, -11, "", "DslError: invalid parameter"),
                 (0, -11, "", ""),
                 (2, 4, valid, "usage: missing argument"),
                 (1, 2, valid, "DslError: invalid parameter"),
                 (1, 4, "not JSON", "DslError: invalid parameter"),
                 (1, 4, "{}", "DslError: invalid parameter"),
                 (1, 4, valid.replace('"noisemaker-cpp.dsl-cpu-run.v1"', '"other"'), "DslError: invalid parameter"),
                 (1, 4, valid.replace('"refused"', '"rendered"'), "DslError: invalid parameter"),
                 (1, 4, valid.replace('"exception"', '"unknown"'), "DslError: invalid parameter"),
                 (1, 4, valid.replace('"exception"', '"4"'), "DslError: invalid parameter"),
                 (1, 4, valid.replace('"invalid parameter"', '""'), "DslError: invalid parameter"),
                 (1, 4, valid, "TypeError: Cannot read properties of undefined"),
                 (1, 0, "{}", "TypeError: Cannot read properties of undefined"),
                 (1, 4, valid, "Error [ERR_MODULE_NOT_FOUND]: Missing runtime"),
                 (1, 4, valid, "RangeError: Maximum call stack size exceeded")]
        for values in cases:
            with self.subTest(values=values):
                result = self.failed_render(*values)
                self.assertEqual(result["classification"], "harness_error")
                self.assertEqual(self.gate([result]), 1)

    def test_dsl_refusals_pass_but_retired_dither_crash_is_a_harness_error(self) -> None:
        valid = {"schema": "noisemaker-cpp.dsl-cpu-run.v1", "status": "refused",
                 "code": "exception", "detail": "invalid parameter"}
        self.assertEqual(self.failed_render(1, 4, json.dumps(valid), "DslError: invalid parameter")
                         ["classification"], "both_refused")
        self.job.effect_id = "filter/dither"
        valid["detail"] = ('Parameter "palette" is not renderable by the authority: only input(0) '
                           'and monochrome(1) avoid its findClosestPaletteColor NaN-corruption bug '
                           '(canonical-kernels.js copy()/findClosest4-15-16)')
        self.assertEqual(self.failed_render(1, 4, json.dumps(valid),
                                           "TypeError: ditherWithPalette(...).reduce is not a function")
                         ["classification"], "harness_error")
        valid["detail"] = "an unrelated exception"
        self.assertEqual(self.failed_render(1, 4, json.dumps(valid),
                                           "TypeError: ditherWithPalette(...).reduce is not a function")
                         ["classification"], "harness_error")

    def test_valid_single_lane_refusals_retain_their_classification(self) -> None:
        refusal = json.dumps({"schema": "noisemaker-cpp.dsl-cpu-run.v1", "status": "refused",
                              "code": "4", "detail": "missing resource", "programKey": ""})
        self.assertEqual(self.failed_render(0, 4, refusal, "")["classification"], "cpp_refused_only")
        self.assertEqual(self.failed_render(1, 0, "{}", "DslError: invalid parameter")
                         ["classification"], "divergent")
        self.assertEqual(self.failed_render(1, 4, refusal, "Error: Surface o0 has not been written")
                         ["classification"], "both_refused")

    def failed_render(self, js_rc: int, cpp_rc: int, cpp_out: str, js_err: str) -> dict:
        def run(cmd, timeout):
            return (js_rc, "", js_err, False, 0.0) if cmd[0] == "node" else (cpp_rc, cpp_out, "", False, 0.0)
        with patch.object(sweep, "_run_proc", run):
            return sweep.run_job(vars(self.job))

    def render(self, float_lanes: set[str], cpp_float: bytes = b"\0" * 16) -> dict:
        # Replace only the two expensive external renders. Keep their file
        # contract and the actual comparison/classification/gate logic real.
        def run(cmd, timeout):
            pathlib.Path(cmd[cmd.index("--rgba8-output") + 1]).write_bytes(b"\0\0\0\xff")
            if cmd[0] in float_lanes:
                payload = b"\0" * 16 if cmd[0] == "node" else cpp_float
                pathlib.Path(cmd[cmd.index("--float32-output") + 1]).write_bytes(payload)
            return 0, "{}", "", False, 0.0

        with patch.object(sweep, "_run_proc", run):
            return sweep.run_job(vars(self.job))


class SweepResumeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="parity-resume-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.driver = self.root / "driver"
        self.ledger = self.root / "ledger"
        self.node = self.root / "node"
        for file in (self.driver, self.ledger, self.node):
            file.write_text("original input\n")
        self.catalog = [{"id": "synth/solid", "func": "solid", "namespace": "synth",
                         "domain": "image", "kind": "generator", "params": {}}]
        self.out = self.root / "out"

    def run_main(self, *extra: str, forbid_render: bool = False) -> int:
        def render(cmd, timeout):
            if forbid_render:
                raise AssertionError("unchanged resume attempted another render")
            # The single default case is 17x11 on both lanes.
            pathlib.Path(cmd[cmd.index("--rgba8-output") + 1]).write_bytes(b"\0" * 748)
            pathlib.Path(cmd[cmd.index("--float32-output") + 1]).write_bytes(b"\0" * 2992)
            return 0, "{}", "", False, 0.0

        argv = ["sweep.py", "--cpu-root", str(self.root), "--authority-ledger", str(self.ledger),
                "--cpp-driver", str(self.driver), "--out", str(self.out),
                "--workers", "1", "--variants", "1", "--no-chains", "--gate", "all", *extra]
        with patch.object(sys, "argv", argv), \
             patch.object(sweep, "load_catalog", return_value=self.catalog), \
             patch.object(sweep.shutil, "which", return_value=str(self.node)), \
             patch.object(sweep, "_run_proc", render), \
             patch.object(sweep.concurrent.futures, "ProcessPoolExecutor", concurrent.futures.ThreadPoolExecutor), \
             contextlib.redirect_stderr(io.StringIO()):
            return sweep.main()

    def test_legacy_results_without_provenance_require_force(self) -> None:
        self.out.mkdir()
        row = {"case_id": "synth__solid__default", "effect_id": "synth/solid", "kind": "default",
               "classification": "byte_exact", "chain_effects": []}
        (self.out / "results.jsonl").write_text(json.dumps(row) + "\n")
        with self.assertRaises(SystemExit) as failure:
            self.run_main()
        self.assertEqual(failure.exception.code, 2)

    def test_changed_inputs_cannot_reuse_success(self) -> None:
        for change in ("seed", "source", "driver", "ledger", "node", "timeout", "joint_samples"):
            with self.subTest(change=change):
                self.out = self.root / f"out-{change}"
                self.assertEqual(self.run_main(), 0)
                extra = ()
                if change == "seed":
                    extra = ("--seed", "42")
                elif change == "source":
                    self.catalog[0]["params"] = {"amount": {"type": "float", "default": 0.5}}
                elif change == "timeout":
                    extra = ("--max-seconds-per-case", "2")
                elif change == "joint_samples":
                    extra = ("--joint-samples", "3")
                else:
                    getattr(self, change).write_text("changed input\n")
                with self.assertRaises(SystemExit) as failure:
                    self.run_main(*extra)
                self.assertEqual(failure.exception.code, 2)

    def test_unchanged_resume_preserves_current_evidence(self) -> None:
        self.assertEqual(self.run_main(), 0)
        self.assertEqual(self.run_main(forbid_render=True), 0)

    def test_case_count_options_are_bound_to_manifest_and_summary(self) -> None:
        self.assertEqual(self.run_main("--joint-samples", "3"), 0)
        manifest = json.loads((self.out / "run-manifest.json").read_text())
        summary = json.loads((self.out / "results.json").read_text())
        for selection in (manifest["selection"], summary["meta"]):
            self.assertEqual(selection["joint_samples"], 3)
            self.assertIs(selection["no_chains"], True)

    def test_force_replaces_stale_results(self) -> None:
        self.assertEqual(self.run_main(), 0)
        old_seed = json.loads((self.out / "results.jsonl").read_text())["seed"]
        self.assertEqual(self.run_main("--seed", "42", "--force"), 0)
        rows = [json.loads(line) for line in (self.out / "results.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["seed"], old_seed)
        self.assertEqual(self.run_main("--seed", "42", forbid_render=True), 0)


class DefineLivenessGateTest(unittest.TestCase):
    """A define parameter passes only when its isolated cases change the output."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="parity-liveness-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        for name in ("driver", "ledger", "node"):
            (self.root / name).write_text("input\n")
        self.stderr = ""

    def catalog(self, effect_id: str) -> list[dict]:
        namespace, func = effect_id.split("/")
        return [{"id": effect_id, "func": func, "namespace": namespace, "domain": "image",
                 "kind": "generator", "params": {
                     "style": {"type": "int", "default": 0, "define": "STYLE",
                               "choices": {"plain": 0, "fancy": 1}}}}]

    def run_main(self, effect_id: str, gate: str, live: bool) -> int:
        def render(cmd, timeout):
            scratch = pathlib.Path(cmd[cmd.index("--rgba8-output") + 1]).parent
            options = json.loads((scratch / "case.json").read_text())["options"]
            pixels = options["width"] * options["height"]
            value = 1 if live and "style: 1" in (scratch / "case.dsl").read_text() else 0
            pathlib.Path(cmd[cmd.index("--rgba8-output") + 1]).write_bytes(bytes([value]) * pixels * 4)
            pathlib.Path(cmd[cmd.index("--float32-output") + 1]).write_bytes(bytes([value]) * pixels * 16)
            return 0, "{}", "", False, 0.0

        out = self.root / f"out-{effect_id.replace('/', '_')}-{gate}-{live}"
        argv = ["sweep.py", "--cpu-root", str(self.root), "--authority-ledger", str(self.root / "ledger"),
                "--cpp-driver", str(self.root / "driver"), "--out", str(out),
                "--workers", "1", "--define-enum", "--gate", gate]
        captured = io.StringIO()
        with patch.object(sys, "argv", argv), \
             patch.object(sweep, "load_catalog", return_value=self.catalog(effect_id)), \
             patch.object(sweep, "DEFINE_ENABLING_CONTEXTS", {}), \
             patch.object(sweep.shutil, "which", return_value=str(self.root / "node")), \
             patch.object(sweep, "_run_proc", render), \
             patch.object(sweep.concurrent.futures, "ProcessPoolExecutor", concurrent.futures.ThreadPoolExecutor), \
             contextlib.redirect_stderr(captured):
            code = sweep.main()
        self.stderr = captured.getvalue()
        return code

    def test_a_context_for_an_effect_missing_from_the_catalog_stops_the_run(self) -> None:
        argv = ["sweep.py", "--cpu-root", str(self.root), "--authority-ledger", str(self.root / "ledger"),
                "--cpp-driver", str(self.root / "driver"), "--out", str(self.root / "out-stale"),
                "--workers", "1", "--define-enum", "--gate", "kit"]
        with patch.object(sys, "argv", argv), \
             patch.object(sweep, "load_catalog", return_value=self.catalog("synth/solid")), \
             patch.object(sweep.shutil, "which", return_value=str(self.root / "node")), \
             contextlib.redirect_stderr(io.StringIO()), \
             self.assertRaises(SystemExit) as failure:
            sweep.main()
        self.assertEqual(failure.exception.code, 2)

    def test_a_define_that_never_changes_the_output_fails_the_gate(self) -> None:
        for gate in ("kit", "all"):
            with self.subTest(gate=gate):
                self.assertEqual(self.run_main("synth/solid", gate, live=False), 1)
                self.assertIn("NOT DEMONSTRATED: synth/solid `style`", self.stderr)

    def test_a_define_that_changes_the_output_passes_the_gate(self) -> None:
        for gate in ("kit", "all"):
            with self.subTest(gate=gate):
                self.assertEqual(self.run_main("synth/solid", gate, live=True), 0)
                self.assertNotIn("NOT DEMONSTRATED:", self.stderr)
                self.assertIn(f"{gate}: 0 define parameters NOT DEMONSTRATED of 1", self.stderr)

    def test_the_kit_gate_checks_only_claimed_effects(self) -> None:
        self.assertEqual(self.run_main("unclaimed/effect", "kit", live=False), 0)
        self.assertEqual(self.run_main("unclaimed/effect", "all", live=False), 1)


class DefineEnablingContextTest(unittest.TestCase):
    """Isolated define cases hold the parameter values that switch the define on."""

    # Each of these renders the same bytes for every value at the effect's
    # defaults (GAP-006), so its isolated cases need an enabling context.
    DEFAULT_DISABLED = {
        ("classicNoisedeck/bitEffects", "colorScheme"), ("classicNoisedeck/bitEffects", "formula"),
        ("classicNoisedeck/bitEffects", "interp"), ("classicNoisedeck/cellRefract", "kernel"),
        ("classicNoisedeck/kaleido", "kernel"), ("classicNoisedeck/noise", "metric"),
        ("classicNoisedeck/noise", "refractMode"), ("classicNoisedeck/shapeMixer", "loopOffset"),
        ("filter/halftone", "pattern"),
    }

    @staticmethod
    def effect(effect_id: str, kind: str, params: dict) -> dict:
        namespace, func = effect_id.split("/")
        return {"id": effect_id, "func": func, "namespace": namespace, "domain": "image",
                "kind": kind, "params": params}

    @staticmethod
    def isolated(jobs: list, name: str) -> list:
        return [job for job in jobs if job.kind == "define_isolated" and f"__define__{name}__" in job.case_id]

    def bit_effects(self) -> dict:
        choice = lambda default, define, *values: {  # noqa: E731
            "type": "int", "default": default, "define": define,
            "choices": {f"v{value}": value for value in values}}
        return self.effect("classicNoisedeck/bitEffects", "generator", {
            "mode": choice(1, "MODE", 0, 1),
            "interp": choice(0, "INTERP", 0, 1),
            "maskFormula": choice(10, "MASK_FORMULA", 10, 20),
            "scale": {"type": "float", "default": 75, "min": 1, "max": 100, "uniform": "scale"},
        })

    def test_every_default_disabled_define_has_an_enabling_context(self) -> None:
        self.assertLessEqual(self.DEFAULT_DISABLED, set(sweep.DEFINE_ENABLING_CONTEXTS))

    def test_the_context_applies_only_to_its_own_define(self) -> None:
        jobs = sweep.build_define_jobs(self.bit_effects(), 20260916)
        interp = self.isolated(jobs, "interp")
        self.assertEqual(len(interp), 2 * len(sweep.DEFINE_DRAWS))
        for job in interp:
            self.assertIn("mode: 0", job.source)
            self.assertIn("scale: 5", job.source)
        for job in self.isolated(jobs, "maskFormula"):
            self.assertIn("mode: 1", job.source)
            self.assertIn("scale: 75", job.source)

    def test_a_wired_context_source_feeds_the_surface_parameter(self) -> None:
        effect = self.effect("classicNoisedeck/shapeMixer", "mixer", {
            "tex": {"type": "surface", "default": "none"},
            "loopOffset": {"type": "int", "default": 10, "define": "LOOP_OFFSET",
                           "choices": {"circle": 10, "triangle": 30}},
        })
        jobs = self.isolated(sweep.build_define_jobs(effect, 20260916), "loopOffset")
        self.assertEqual(len(jobs), 2 * len(sweep.DEFINE_DRAWS))
        for job in jobs:
            self.assertIn("noise(seed: 3).write(o1)", job.source)
            self.assertIn("tex: o1", job.source)

    def test_contexts_are_checked_against_the_catalog(self) -> None:
        key = ("classicNoisedeck/bitEffects", "interp")
        effect = self.bit_effects()
        with patch.object(sweep, "DEFINE_ENABLING_CONTEXTS", {key: sweep.DEFINE_ENABLING_CONTEXTS[key]}):
            sweep.check_enabling_contexts([effect])
            with self.assertRaisesRegex(ValueError, "has no classicNoisedeck/bitEffects"):
                sweep.check_enabling_contexts([])
            broken = json.loads(json.dumps(effect))
            del broken["params"]["scale"]
            with self.assertRaisesRegex(ValueError, "`scale`"):
                sweep.check_enabling_contexts([broken])
            broken = json.loads(json.dumps(effect))
            del broken["params"]["interp"]["define"]
            with self.assertRaisesRegex(ValueError, "`interp` is not a define parameter"):
                sweep.check_enabling_contexts([broken])


if __name__ == "__main__":
    unittest.main()
