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
import re
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


class _BothLanes:
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


class OscAutomationParityTest(_BothLanes, unittest.TestCase):
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


class UnsupportedRealtimeInputTest(unittest.TestCase):
    def test_unsupported_realtime_input_warns_and_uses_defaults(self) -> None:
        driver = resolve_driver("NOISEMAKER_DSL_CPU_CASE", "noisemaker-dsl-cpu-case")
        with tempfile.TemporaryDirectory(prefix="noisemaker-unsupported-input-") as temporary:
            scratch = pathlib.Path(temporary)
            def render(source):
                source_path = scratch / "case.dsl"
                source_path.write_text(source, encoding="utf-8")
                return subprocess.run([str(driver), *record_flags(_record(source, 0.25), source_path),
                    "--rgba8-output", str(scratch / "cpp.rgba8"),
                    "--metadata-output", str(scratch / "cpp.json"),
                    "--float32-output", str(scratch / "cpp.f32")],
                    capture_output=True, text=True, timeout=20)
            for call in ("midi(channel: 1, min: 0.8)", "audio(band: audioBand.low, min: 0.8)"):
                for binding in (False, True):
                    with self.subTest(call=call, binding=binding):
                        prefix = f"let input = {call}\n" if binding else ""
                        value = "input" if binding else call
                        source = f"search synth\n{prefix}noise(seed: 1, scaleX: {value}).write(o0)\nrender(o0)\n"
                        cpp = render(source)
                        self.assertEqual(0, cpp.returncode, cpp.stdout + cpp.stderr)
                        self.assertIn("is unsupported in CPU ports; real-time input is unavailable", cpp.stderr)
                        ignored = (scratch / "cpp.rgba8").read_bytes()
                        baseline = render("search synth\nnoise(seed: 1).write(o0)\nrender(o0)\n")
                        self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
                        self.assertEqual("", baseline.stderr)
                        self.assertEqual(ignored, (scratch / "cpp.rgba8").read_bytes())


# The five float `rotation` parameters declared on a GLSL `int` uniform
# (src/graph/executor.cpp kRawComparedIntUniforms). The authority binds the raw
# number (renderer.js buildBindings) and each kernel compares it with -1 and 1.
ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPATIBILITY = ROOT / "src/effects/generated/backend_compatibility.json"
CORPUS_SOURCES = ROOT / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d/sources"
EXECUTOR = ROOT / "src/graph/executor.cpp"
ROTATION_PROGRAMS = {
    "filter/historicPalette:historicPalette":
        "search filter, synth\nnoise(seed: 1, ridges: true, colorMode: mono).historicPalette(rotation: {value}).write(o0)\nrender(o0)\n",
    "filter/palette:palette":
        "search filter, synth\nnoise(seed: 1, ridges: true).palette(rotation: {value}).write(o0)\nrender(o0)\n",
    "filter/tetraColorArray:tetraColorArray":
        "search filter, synth\nnoise(seed: 1).tetraColorArray(smoothness: 0, rotation: {value}).write(o0)\nrender(o0)\n",
    "filter/tetraCosine:tetraCosine":
        "search filter, synth\nnoise(seed: 1).tetraCosine(rotation: {value}).write(o0)\nrender(o0)\n",
    "filter3d/palette3d:palette3d":
        "search synth3d, filter3d, render\nnoise3d(seed: 3, volumeSize: 8).palette3d(rotation: {value}).render3d().write(o0)\nrender(o0)\n",
}
# Choice names, integers (choice and non-choice), fractional and out-of-int32
# values of both signs, an expression that evaluates to 1, and oscillators
# (unscaled for a float parameter with choices, so fractional except where a
# square wave reaches exactly 0 or 1).
ROTATION_VALUES = ("none", "fwd", "back", "0", "1", "-1", "2", "-3", "0.5", "-0.5", "1.5", "-1.25",
                   "3000000000", "-3000000000", "0.5 * 2", "osc(sine)", "osc(square)")
ROTATION_TIME = 0.37


def _strip_glsl_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    return re.sub(r"//[^\n]*", " ", source)


class FloatOnIntUniformContractTest(unittest.TestCase):
    """The executor's raw-compared table names exactly what its comment claims."""

    def test_table_matches_the_executor(self) -> None:
        text = EXECUTOR.read_text(encoding="utf-8")
        block = re.search(r"kRawComparedIntUniforms\{\{(.*?)\}\};", text, flags=re.S)
        self.assertIsNotNone(block)
        entries = re.findall(r'\{"([^"]+)", "([^"]+)"\}', block.group(1))
        self.assertEqual(sorted(entries), sorted((key, "rotation") for key in ROTATION_PROGRAMS))

    def test_each_kernel_reads_rotation_only_in_comparisons_with_minus_one_and_one(self) -> None:
        rows = {row["program_key"]: row for row in json.loads(COMPATIBILITY.read_text(encoding="utf-8"))["canonical_programs"]}
        for key in ROTATION_PROGRAMS:
            with self.subTest(program=key):
                bindings = [item for item in rows[key]["uniforms"] if item["name"] == "rotation"]
                self.assertEqual([{"name": "rotation", "type": "int", "cpp_type": "std::int32_t",
                                   "source": "effect_parameter", "source_name": "rotation"}], bindings)
                source = _strip_glsl_comments((CORPUS_SOURCES / rows[key]["source"].removeprefix("sources/")).read_text(encoding="utf-8"))
                uses = re.findall(r"[^\n;{}]*\brotation\b[^\n;{}]*", source)
                self.assertEqual(1, sum(1 for use in uses if re.fullmatch(r"\s*uniform int rotation\s*", use)), uses)
                for use in uses:
                    if re.fullmatch(r"\s*uniform int rotation\s*", use):
                        continue
                    stripped = re.sub(r"\brotation\s*==\s*-?1\b", "", use)
                    self.assertNotRegex(stripped, r"\brotation\b", use)


class FloatOnIntUniformParityTest(_BothLanes, unittest.TestCase):
    """Every rotation value renders byte-exact on both lanes, as the authority binds it."""

    def test_only_these_float_parameters_bind_an_int_uniform(self) -> None:
        rows = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))["canonical_programs"]
        int_parameters = sorted({(row["effect_id"], item["source_name"], row["program_key"])
                                 for row in rows for item in row["uniforms"]
                                 if item["source"] == "effect_parameter" and item["cpp_type"] == "std::int32_t"})
        script = (
            "const [snapshot, input] = process.argv.slice(1)\n"
            "const { effectRecords } = await import(snapshot)\n"
            "const byId = new Map(effectRecords.map((record) => [record.id, record]))\n"
            "const rows = JSON.parse(input).filter(([id, name]) => byId.get(id)?.params?.[name]?.type === 'float')\n"
            "process.stdout.write(JSON.stringify(rows.map(([id, name, key]) => [key, name, Object.keys(byId.get(id).params[name].choices ?? {})])))\n")
        snapshot = (self.cpu_root / "src/effects/generated/upstream-snapshot.js").as_uri()
        result = subprocess.run([self.node, "--input-type=module", "-e", script, snapshot, json.dumps(int_parameters)],
                                check=True, capture_output=True, text=True)
        self.assertEqual(sorted([key, "rotation", ["none", "fwd", "back"]] for key in ROTATION_PROGRAMS),
                         sorted(json.loads(result.stdout)))

    def test_rotation_values_are_byte_exact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-float-int-uniform-") as temporary:
            scratch = pathlib.Path(temporary)
            for key, template in ROTATION_PROGRAMS.items():
                renders = {}
                for value in ROTATION_VALUES:
                    with self.subTest(program=key, rotation=value):
                        js, cpp = self._render(scratch, template.format(value=value), ROTATION_TIME)
                        self.assertEqual(0, js.returncode, js.stderr)
                        self.assertEqual(0, cpp.returncode, cpp.stdout + cpp.stderr)
                        for suffix in ("f32", "rgba8"):
                            self.assertEqual((scratch / f"js.{suffix}").read_bytes(),
                                             (scratch / f"cpp.{suffix}").read_bytes(), suffix)
                        renders[value] = (scratch / "js.rgba8").read_bytes()
                with self.subTest(program=key, check="rotation changes the output"):
                    self.assertEqual(3, len({renders["none"], renders["fwd"], renders["back"]}))


if __name__ == "__main__":
    unittest.main()
