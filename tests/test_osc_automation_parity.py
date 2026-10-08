"""`osc(...)` automation renders byte-exact against the CPU authority.

The authority resolves every `osc(...)` parameter per render at the normalized
loop time (src/runtime/automation.js) and binds the resulting number. These
programs cover every oscillator kind, nested fields, frequency-modulated speed
(the quadrature path), noise2d, `let`-bound oscillators, an int-with-choices
consumer (rounded) and float consumers, each at several times; both lanes must
agree to the byte. An int consumer without choices binds the raw fractional
value in the authority, which a typed int32 uniform cannot hold: the C++ lane
refuses that render rather than produce different bytes.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import JS_RUNNER, record_flags, resolve_cpu_root, resolve_driver

PROGRAMS = {
    "pattern-mixed": (
        "search synth\n"
        "pattern(scale: osc(sine, 0.2, 0.8, 2, 0.1, 7), "
        "rotation: osc(type: tri, speed: osc(noise, 0.25, 0.75)), type: osc(square)).write(o0)\n"
        "render(o0)\n"),
    "pattern-noise2d": (
        "search synth\n"
        "pattern(speed: osc(noise2d, 0, 1, 1.5, 0, 42), "
        "thickness: osc(sawInv, 0.1, 0.9, -3, 0.5)).write(o0)\nrender(o0)\n"),
    "pattern-bound-nested": (
        "search synth\n"
        "let wobble = osc(saw, 0, 1, osc(tri, 0.1, 0.4, 2), 0.25, 9)\n"
        "pattern(scale: wobble, smoothness: osc(noise1d, 0.3, 0.6, 1, 0, 5), "
        "skew: osc(type: oscKind.square, min: osc(sine), max: 1, speed: 4, offset: -0.3)).write(o0)\n"
        "render(o0)\n"),
}
TIMES = (0.0, 0.37, 0.91)
# synth/noise `octaves` is an int without choices: the authority binds the
# fractional resolved value, which the typed kernel's int32 cannot represent.
REFUSED = ("search synth\nnoise(octaves: osc(sine, 0, 1, 1)).write(o0)\nrender(o0)\n", 0.37,
           "octaves: expected int32")


def _record(source: str, time: float) -> dict:
    return {"recordKind": "admitted", "id": "osc-automation", "source": source,
            "sourceSha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "options": {"width": 33, "height": 21, "time": time, "frame": 0, "seed": 11,
                        "oneShot": "ready", "renderScale": 1},
            "plan": None}


class OscAutomationParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = resolve_driver("NOISEMAKER_DSL_CPU_CASE", "noisemaker-dsl-cpu-case")
        self.cpu_root = resolve_cpu_root()
        self.node = shutil.which("node")
        self.assertIsNotNone(self.node, "node is required for the authority runner")

    def _render(self, scratch: pathlib.Path, source: str, time: float):
        source_path = scratch / "case.dsl"
        source_path.write_text(source, encoding="utf-8", newline="")
        record = _record(source, time)
        case = scratch / "case.json"
        case.write_text(json.dumps(record), encoding="utf-8")
        js = subprocess.run(
            [self.node, str(JS_RUNNER), "--cpu-root", str(self.cpu_root), "--case", str(case),
             "--rgba8-output", str(scratch / "js.rgba8"), "--metadata-output", str(scratch / "js.json"),
             "--float32-output", str(scratch / "js.f32")],
            capture_output=True, text=True)
        cpp = subprocess.run(
            [str(self.driver), *record_flags(record, source_path),
             "--rgba8-output", str(scratch / "cpp.rgba8"), "--metadata-output", str(scratch / "cpp.json"),
             "--float32-output", str(scratch / "cpp.f32")],
            capture_output=True, text=True)
        return js, cpp

    def test_osc_programs_are_byte_exact_at_every_time(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-osc-parity-") as temporary:
            scratch = pathlib.Path(temporary)
            for name, source in PROGRAMS.items():
                for time in TIMES:
                    with self.subTest(program=name, time=time):
                        js, cpp = self._render(scratch, source, time)
                        self.assertEqual(0, js.returncode, js.stderr)
                        self.assertEqual(0, cpp.returncode, cpp.stdout + cpp.stderr)
                        for suffix in ("f32", "rgba8"):
                            self.assertEqual((scratch / f"js.{suffix}").read_bytes(),
                                             (scratch / f"cpp.{suffix}").read_bytes(), suffix)

    def test_fractional_int_without_choices_is_refused_not_approximated(self) -> None:
        source, time, detail = REFUSED
        with tempfile.TemporaryDirectory(prefix="noisemaker-osc-refusal-") as temporary:
            scratch = pathlib.Path(temporary)
            js, cpp = self._render(scratch, source, time)
            self.assertEqual(0, js.returncode, js.stderr)
            self.assertEqual(4, cpp.returncode, cpp.stdout + cpp.stderr)
            # A refusal is reported as the driver's structured stdout document.
            metadata = json.loads(cpp.stdout)
            self.assertEqual("refused", metadata["status"])
            self.assertEqual(detail, metadata["detail"])


if __name__ == "__main__":
    unittest.main()
