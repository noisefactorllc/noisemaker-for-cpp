"""Grouped-MRT and seed-binding parity sweep for the point families.

The 2026-09-24 acceptance order's first action asks the three multi-output
point-family effects -- points/buddhabrot, points/hydraulic and
render/pointsEmit -- to execute complete graphs through the grouped-MRT
executor and seed binding and to match the pinned JS authority exactly in
every recorded RGBA8 and float32 output. The default corpus records already
execute byte-exact through the corpus lane; this module proves the remaining
acceptance dimensions the defaults never exercise:

* multiple iteration counts (1, 3, 7) and repeated executor calls,
* non-square screens with unequal state sizes (stateSize 64/256 vs 37x53),
* live and dead particles (attrition killing particles, resetState),
* explicit DSL seeds versus the render-level seed substitution,
* signed and float32-boundary render seeds (past-2^31 and uint32 wraps),
* accepted fractional and negative effect inputs (center, zoom, attrition,
  stride).

Every case renders both lanes from the same source bytes and options and
compares the RGBA8 bytes and the raw float32 backing surface at zero
tolerance. There is no tolerance and no refusal allowance: a C++ refusal is
a failure, not a skip, and nothing here rewrites fixtures or exclusion
tables.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import (
    JS_RUNNER,
    record_flags,
    resolve_cpu_root,
)
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/dsl/executable-corpus.json"

# The screen every sweep case renders at unless the case says otherwise:
# non-square, and unequal to the 64/256-square particle state textures the
# sources declare, so the grouped-MRT destination sizing and the seed binding
# never lean on the corpus defaults.
WIDTH, HEIGHT = 37, 53

RENDER_SEEDS = {
    "default-record": 723072186,
    "signed-negative": -5,
    "int32-boundary": 2147483648,
    "float32-past-2^31": 2453927936,
    "uint32-wrap": 4294967295,
}


def _base_records() -> dict:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    return {record["id"]: record for record in corpus["records"]}


class PointsMrtSeedParityTest(unittest.TestCase):
    """Every case must execute on both lanes and match byte for byte."""

    def driver(self):
        configured = os.environ.get("NOISEMAKER_DSL_CPU_CASE")
        if configured:
            candidate = pathlib.Path(configured)
            if not (candidate.is_file() and os.access(candidate, os.X_OK)):
                self.fail(f"NOISEMAKER_DSL_CPU_CASE is not an executable file: {candidate}")
            return candidate
        fallback = ROOT / "build/noisemaker-dsl-cpu-case"
        if fallback.is_file() and os.access(fallback, os.X_OK):
            return fallback
        raise unittest.SkipTest(
            "NOISEMAKER_DSL_CPU_CASE must point at the external noisemaker-dsl-cpu-case build")

    def node(self) -> str:
        value = shutil.which("node")
        if value is None:
            self.skipTest("node is required for the authority runner")
        return value

    def authority(self) -> pathlib.Path:
        return resolve_cpu_root()

    def sweep_case(self, record_id: str, source: str, seed: float,
                   width: int = WIDTH, height: int = HEIGHT) -> dict:
        record = json.loads(json.dumps(_base_records()[record_id]))
        record["source"] = source
        record["sourceSha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
        record["options"] = {**record["options"], "width": width, "height": height,
                             "seed": seed}
        record["width"] = width
        record["height"] = height
        return record

    @staticmethod
    def buddhabrot(iterations: int, **parameters) -> str:
        ordered = ", ".join(
            f"{name}: {value}" for name, value in
            (("mode", parameters.get("mode", 0)),
             ("maxIter", parameters.get("maxIter", 200)),
             ("minIter", parameters.get("minIter", 1)),
             ("centerX", parameters.get("centerX", -0.5)),
             ("centerY", parameters.get("centerY", 0)),
             ("zoom", parameters.get("zoom", 1)),
             ("iterationCount", iterations)))
        return ("search synth, points\n"
                f"solid(color: #3a7).buddhabrot(stateSize: 64, {ordered}).write(o0)\n"
                "render(o0)\n")

    @staticmethod
    def hydraulic(iterations: int, **parameters) -> str:
        ordered = ", ".join(
            f"{name}: {value}" for name, value in
            (("stride", parameters.get("stride", 10)),
             ("quantize", str(parameters.get("quantize", False)).lower()),
             ("inverse", str(parameters.get("inverse", False)).lower()),
             ("iterationCount", iterations)))
        return ("search synth, points\n"
                f"solid().hydraulic({ordered}).write(o0)\n"
                "render(o0)\n")

    @staticmethod
    def points_emit(iterations: int, explicit_seed: int | None, **parameters) -> str:
        fields = [("stateSize", parameters.get("stateSize", 64)),
                  ("layout", parameters.get("layout", 0))]
        if explicit_seed is not None:
            fields.append(("seed", explicit_seed))
        fields += [("attrition", parameters.get("attrition", 0)),
                   ("resetState", str(parameters.get("resetState", False)).lower()),
                   ("iterationCount", iterations)]
        ordered = ", ".join(f"{name}: {value}" for name, value in fields)
        return ("search synth, render\n"
                f"solid(color: #3a7).pointsEmit({ordered}).write(o0)\n"
                "render(o0)\n")

    def cases(self) -> list[tuple[str, dict]]:
        """The sweep, one (name, record) pair per acceptance dimension."""
        cases: list[tuple[str, dict]] = []
        add = cases.append

        # Buddhabrot: iteration counts, both modes, fractional/negative
        # centers and the zoom bounds.
        add(("buddhabrot-iters-1", self.sweep_case(
            "points/buddhabrot#default", self.buddhabrot(1), RENDER_SEEDS["default-record"])))
        add(("buddhabrot-iters-3", self.sweep_case(
            "points/buddhabrot#default", self.buddhabrot(3), RENDER_SEEDS["default-record"])))
        add(("buddhabrot-iters-7-anti-zoom-max", self.sweep_case(
            "points/buddhabrot#default", self.buddhabrot(7, mode=1, zoom=5),
            RENDER_SEEDS["default-record"])))
        add(("buddhabrot-fractional-negative-center", self.sweep_case(
            "points/buddhabrot#default",
            self.buddhabrot(3, centerX=-2.5, centerY=1.75, zoom=0.1),
            RENDER_SEEDS["default-record"])))
        add(("buddhabrot-tight-iter-window", self.sweep_case(
            "points/buddhabrot#default", self.buddhabrot(7, maxIter=20, minIter=19),
            RENDER_SEEDS["default-record"])))

        # Hydraulic: iteration counts, quantize/inverse, stride and
        # inputWeight extremes, fractional stride.
        add(("hydraulic-iters-1", self.sweep_case(
            "points/hydraulic#default", self.hydraulic(1), RENDER_SEEDS["default-record"])))
        add(("hydraulic-iters-3-quantize", self.sweep_case(
            "points/hydraulic#default", self.hydraulic(3, quantize=True),
            RENDER_SEEDS["default-record"])))
        add(("hydraulic-iters-7-stride-max", self.sweep_case(
            "points/hydraulic#default", self.hydraulic(7, stride=1000),
            RENDER_SEEDS["default-record"])))
        add(("hydraulic-inverse-fractional-stride-negative-seed", self.sweep_case(
            "points/hydraulic#default", self.hydraulic(3, stride=3.5, inverse=True),
            RENDER_SEEDS["signed-negative"])))
        add(("hydraulic-quantize-inverse", self.sweep_case(
            "points/hydraulic#default", self.hydraulic(3, quantize=True, inverse=True),
            RENDER_SEEDS["default-record"])))

        # pointsEmit: six-plus recorded cases spanning explicit versus
        # render-level seeds, every signed/float32 seed boundary, live and
        # dead particles, both layouts and unequal state sizes.
        add(("pointsEmit-explicit-seed-zero-iters-1", self.sweep_case(
            "render/pointsEmit#default", self.points_emit(1, 0), RENDER_SEEDS["default-record"])))
        add(("pointsEmit-explicit-seed-max-ring-fractional-attrition", self.sweep_case(
            "render/pointsEmit#default", self.points_emit(3, 100, layout=3, attrition=0.5),
            RENDER_SEEDS["default-record"])))
        add(("pointsEmit-explicit-seed-dead-particles-reset", self.sweep_case(
            "render/pointsEmit#default",
            self.points_emit(7, 7, attrition=10, resetState=True),
            RENDER_SEEDS["default-record"])))
        for name, seed in RENDER_SEEDS.items():
            add((f"pointsEmit-render-seed-{name}", self.sweep_case(
                "render/pointsEmit#default", self.points_emit(3, None),
                seed)))
        add(("pointsEmit-unequal-state-256-center-layout", self.sweep_case(
            "render/pointsEmit#default",
            self.points_emit(3, 42, stateSize=256, layout=2, attrition=10),
            RENDER_SEEDS["default-record"])))
        return cases

    def test_every_sweep_case_matches_both_outputs_byte_for_byte(self) -> None:
        driver = self.driver()
        node = self.node()
        cpu_root = self.authority()
        for name, record in self.cases():
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory(
                        prefix="noisemaker-points-mrt-seed-") as temporary:
                    scratch = pathlib.Path(temporary)
                    source = scratch / "case.dsl"
                    source.write_text(record["source"], encoding="utf-8", newline="")
                    case = scratch / "case.json"
                    case.write_text(json.dumps(record), encoding="utf-8")

                    js_raw = scratch / "js.rgba8"
                    js_f32 = scratch / "js.f32"
                    js = subprocess.run(
                        [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case),
                         "--rgba8-output", str(js_raw), "--float32-output", str(js_f32),
                         "--metadata-output", str(scratch / "js.json")],
                        capture_output=True, text=True)

                    # The C++ driver runs even when the authority refuses:
                    # bytes from an authority refusal must never pass.
                    cpp_raw = scratch / "cpp.rgba8"
                    cpp_f32 = scratch / "cpp.f32"
                    cpp = subprocess.run(
                        [str(driver), *record_flags(record, source),
                         "--rgba8-output", str(cpp_raw), "--float32-output", str(cpp_f32),
                         "--metadata-output", str(scratch / "cpp.json")],
                        capture_output=True, text=True)

                    if js.returncode != 0:
                        self.fail(f"the authority refuses this sweep case: "
                                  f"{(js.stderr or js.stdout).strip()[:400]}")
                    if cpp.returncode != 0:
                        self.fail(f"the executor refuses this sweep case: "
                                  f"{(cpp.stdout or cpp.stderr).strip()[:400]}")

                    result = compare_rgba8(record["options"]["width"], record["options"]["height"],
                                           js_raw.read_bytes(), cpp_raw.read_bytes())
                    self.assertTrue(
                        result["ok"],
                        f"rgba8 mismatch: {format_diagnostics(result)}")
                    self.assertEqual(
                        js_f32.read_bytes(), cpp_f32.read_bytes(),
                        "float32 backing surface mismatch")

    def test_repeated_executor_calls_render_identical_bytes(self) -> None:
        driver = self.driver()
        node = self.node()
        cpu_root = self.authority()
        record = self.sweep_case(
            "points/buddhabrot#default", self.buddhabrot(3), RENDER_SEEDS["default-record"])
        digests = []
        for _ in range(2):
            with tempfile.TemporaryDirectory(
                    prefix="noisemaker-points-mrt-seed-repeat-") as temporary:
                scratch = pathlib.Path(temporary)
                source = scratch / "case.dsl"
                source.write_text(record["source"], encoding="utf-8", newline="")
                case = scratch / "case.json"
                case.write_text(json.dumps(record), encoding="utf-8")
                cpp_raw = scratch / "cpp.rgba8"
                cpp_f32 = scratch / "cpp.f32"
                cpp = subprocess.run(
                    [str(driver), *record_flags(record, source),
                     "--rgba8-output", str(cpp_raw), "--float32-output", str(cpp_f32),
                     "--metadata-output", str(scratch / "cpp.json")],
                    capture_output=True, text=True)
                self.assertEqual(0, cpp.returncode, (cpp.stdout or cpp.stderr).strip()[:400])
                digests.append((hashlib.sha256(cpp_raw.read_bytes()).hexdigest(),
                                hashlib.sha256(cpp_f32.read_bytes()).hexdigest()))
        self.assertEqual(digests[0], digests[1],
                         "repeated executor calls rendered different bytes")


if __name__ == "__main__":
    unittest.main()
