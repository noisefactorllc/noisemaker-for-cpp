from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import JS_RUNNER, record_flags, resolve_cpu_root


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ENV = "NOISEMAKER_TEST_PHYSARUM_CAPTURE"
SEAM = """                        iteration::GroupResourceMap& group_resources) {
  if (iteration::is_group_shared_resource_name(name)) {"""
CAPTURE = r'''
  if (const char* directory = std::getenv("NOISEMAKER_TEST_PHYSARUM_CAPTURE")) {
    static std::size_t ordinal = 0;
    const std::string base = std::string(directory) + "/" + std::to_string(ordinal++);
    std::ofstream meta(std::string(directory) + "/index.tsv", std::ios::app);
    meta << state.snapshot->definition.id << '\t' << name << '\t'
         << surface.width() << '\t' << surface.height() << '\n';
    std::ofstream raw(base + ".f32", std::ios::binary);
    raw.write(reinterpret_cast<const char*>(surface.data().data()),
              static_cast<std::streamsize>(surface.data().size_bytes()));
    const auto bytes = surface.to_rgba8();
    std::ofstream rgba(base + ".rgba8", std::ios::binary);
    rgba.write(reinterpret_cast<const char*>(bytes.data()),
               static_cast<std::streamsize>(bytes.size()));
    if (!meta || !raw || !rgba) throw std::runtime_error("capture write failed");
  }
'''


def instrument(source: str) -> str:
    if source.count(SEAM) != 1:
        raise ValueError("group output capture seam changed")
    return '#include <fstream>\n' + source.replace(
        SEAM, SEAM.split('  if (iteration::')[0] + CAPTURE
        + '  if (iteration::is_group_shared_resource_name(name)) {')


def captures(directory: Path) -> list[tuple[str, bytes, bytes]]:
    rows = (directory / "index.tsv").read_text().splitlines()
    result = []
    for index, row in enumerate(rows):
        _, _, width, height = row.split("\t")
        raw = (directory / f"{index}.f32").read_bytes()
        rgba = (directory / f"{index}.rgba8").read_bytes()
        if len(raw) != int(width) * int(height) * 16 or len(rgba) * 4 != len(raw):
            raise AssertionError("capture extent mismatch")
        result.append((row, raw, rgba))
    return result


def assert_capture_equal(expected, actual) -> None:
    if len(expected) != len(actual):
        raise AssertionError("capture census mismatch")
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left[0] != right[0]:
            raise AssertionError(f"capture route/order mismatch at {index}")
        for lane, a, b in zip(("float32", "RGBA8"), left[1:], right[1:]):
            if a != b:
                raise AssertionError(f"capture {lane} mismatch at {index}: {left[0]}")


class PhysarumCaptureContractTests(unittest.TestCase):
    def test_instrumentation_refuses_missing_or_duplicate_seam(self):
        for source in ("", SEAM + SEAM):
            with self.assertRaisesRegex(ValueError, "capture seam changed"):
                instrument(source)

    def test_comparison_rejects_missing_reordered_and_changed_outputs(self):
        rows = [("agent\tglobal_xyz\t1\t1", b"a" * 16, b"a" * 4),
                ("agent\tglobal_vel\t1\t1", b"b" * 16, b"b" * 4)]
        for candidate, error in ((rows[:1], "census"), (rows[::-1], "route/order"),
                                 ([rows[0], (rows[1][0], rows[0][1], rows[1][2])], "float32"),
                                 ([rows[0], (rows[1][0], rows[1][1], rows[0][2])], "RGBA8")):
            with self.assertRaisesRegex(AssertionError, error):
                assert_capture_equal(rows, candidate)


class PhysarumStateParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpu = resolve_cpu_root()
        cls.driver = Path(os.environ["NOISEMAKER_DSL_CPU_CASE"]).resolve(strict=True)
        cls.node = os.environ["NOISEMAKER_ORACLE_NODE"]
        cls.temporary = tempfile.TemporaryDirectory(prefix="physarum-state-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.scratch = Path(cls.temporary.name).resolve()
        build = cls.driver.parent
        cache = {}
        for line in (build / "CMakeCache.txt").read_text().splitlines():
            if "=" in line and not line.startswith(("#", "//")):
                key, value = line.split("=", 1)
                cache[key.split(":", 1)[0]] = value
        mode = cache["CMAKE_BUILD_TYPE"]
        if mode not in ("Debug", "Release"):
            raise AssertionError(f"Physarum parity requires Debug or Release, got {mode}")
        library = build / "libnoisemaker-cpu.a"
        if not library.is_file() or library.is_symlink():
            raise AssertionError("built regular static library is required")
        source = cls.scratch / "executor.cpp"
        source.write_text(instrument((ROOT / "src/graph/executor.cpp").read_text()))
        cls.captured_driver = cls.scratch / "captured-driver"
        command = [cache["CMAKE_CXX_COMPILER"], "-std=c++20", "-ffp-contract=off",
                   *shlex.split(cache["CMAKE_CXX_FLAGS"]),
                   *shlex.split(cache[f"CMAKE_CXX_FLAGS_{mode.upper()}"]),
                   "-I", str(ROOT / "include"), str(source),
                   str(ROOT / "tools/benchmark/run_cpp_case.cpp"),
                   str(ROOT / "tools/benchmark/corpus_case.cpp"), str(library),
                   cache["ZLIB_LIBRARY_RELEASE"], "-o", str(cls.captured_driver)]
        run = subprocess.run(command, capture_output=True, text=True, timeout=180)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)

    def run_lane(self, record, directory, lane, capture):
        directory.mkdir()
        source = directory / "case.dsl"
        source.write_text(record["source"])
        case = directory / "case.json"
        case.write_text(json.dumps(record))
        env = dict(os.environ)
        env.pop(CAPTURE_ENV, None)
        if capture:
            env[CAPTURE_ENV] = str(directory)
        if lane == "js":
            args = [self.node]
            if capture:
                args += ["--import", str(ROOT / "tests/physarum_state_capture.mjs")]
            args += [str(JS_RUNNER), "--cpu-root", str(self.cpu), "--case", str(case)]
        else:
            args = [str(self.captured_driver if capture else self.driver),
                    *record_flags(record, source)]
        args += ["--rgba8-output", str(directory / "final.rgba8"),
                 "--float32-output", str(directory / "final.f32"),
                 "--metadata-output", str(directory / "final.json")]
        run = subprocess.run(args, env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return tuple((directory / f"final.{extension}").read_bytes()
                     for extension in ("f32", "rgba8"))

    def test_chained_sampled_and_nonzero_intermediate_state_matches_authority(self):
        corpus = json.loads((ROOT / "tests/fixtures/dsl/executable-corpus.json").read_text())
        base = next(row for row in corpus["records"] if row["id"] == "points/physarum#default")
        cases = (("one", 1, "", True, 7),
                 ("feedback", 3, "", True, 2147483648),
                 ("sampled", 3, ", heightTex: perlin(seed: 4), diffuseTex: solid(color: #e52), inputWeight: 2", True, -5),
                 ("dead", 1, "", False, 7))
        for name, ticks, parameters, emitter, seed in cases:
            with self.subTest(case=name):
                record = json.loads(json.dumps(base))
                emit = f".pointsEmit(seed: 7, stateSize: x64, iterationCount: {ticks})" if emitter else ""
                record["source"] = ("search synth, points, render\nsolid(color: #3a7)"
                                    f"{emit}.physarum(iterationCount: {ticks}{parameters})"
                                    f".pointsRender(density: 1, iterationCount: {ticks}).write(o0)\nrender(o0)\n")
                record["sourceSha256"] = hashlib.sha256(record["source"].encode()).hexdigest()
                record["options"].update(width=19, height=13, seed=seed)
                record.update(width=19, height=13)
                directory = self.scratch / name
                directory.mkdir()
                final = {}
                for lane in ("js", "cpp"):
                    final[lane] = self.run_lane(record, directory / lane, lane, True)
                    ordinary = self.run_lane(record, directory / f"{lane}-ordinary", lane, False)
                    self.assertEqual(final[lane], ordinary, "capture changed ordinary execution")
                self.assertEqual(final["js"], final["cpp"])
                expected, actual = captures(directory / "js"), captures(directory / "cpp")
                assert_capture_equal(expected, actual)
                self.assertEqual(len(actual), ticks * (16 if emitter else 12))
                self.assert_state_witnesses(actual, ticks, emitter, name)
                if name == "feedback":
                    self.run_lane(record, directory / "cpp-repeat", "cpp", True)
                    assert_capture_equal(actual, captures(directory / "cpp-repeat"))
                    self.assert_capture_mutations(actual)

    def assert_state_witnesses(self, rows, ticks, emitter, name):
        physarum = [row for row in rows if row[0].startswith("points/physarum\t")]
        routes = ["global_physarum_pheromone", "global_xyz", "global_vel", "global_rgba",
                  "global_physarum_base_color", "global_physarum_pheromone",
                  "global_physarum_pheromone", "outputTex"]
        self.assertEqual([row[0].split("\t")[1] for row in physarum], routes * ticks)
        for offset in range(0, len(physarum), 8):
            frame = physarum[offset:offset + 8]
            self.assertEqual(frame[0][1:], frame[5][1:], "pheromone copy changed decay output")
            self.assertNotEqual(frame[5][1], frame[7][1], "passthrough resources aliased")
            xyz = struct.unpack(f"<{len(frame[1][1]) // 4}f", frame[1][1])
            self.assertTrue(all(value >= .5 if emitter else value < .5 for value in xyz[3::4]))
            if emitter:
                self.assertTrue(any(xyz[::4]), "particle position witness is zero")
        if name == "feedback":
            self.assertTrue(any(physarum[8][1]), "next tick must read nonzero pheromone")
            self.assertNotEqual(physarum[5][1], physarum[6][1], "deposit must change pheromone")
            self.assertNotEqual(physarum[1][1], physarum[9][1], "agent state must advance")
        if name == "sampled":
            self.assertTrue(any(physarum[4][1]), "sampled base color witness is zero")

    def assert_capture_mutations(self, rows):
        indices = [i for i, row in enumerate(rows) if row[0].startswith("points/physarum\t")]
        copy_index, output_index, state_index = indices[5], indices[7], indices[9]
        for target, replacement in ((copy_index, rows[output_index][1:]),
                                    (state_index, (bytes(len(rows[state_index][1])), rows[state_index][2]))):
            changed = list(rows)
            changed[target] = (rows[target][0], *replacement)
            with self.assertRaisesRegex(AssertionError, "float32 mismatch"):
                assert_capture_equal(rows, changed)
        changed = list(rows)
        changed[indices[5]], changed[indices[6]] = changed[indices[6]], changed[indices[5]]
        with self.assertRaisesRegex(AssertionError, "float32 mismatch"):
            assert_capture_equal(rows, changed)


if __name__ == "__main__":
    unittest.main()
