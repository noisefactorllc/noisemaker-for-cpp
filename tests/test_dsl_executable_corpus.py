"""Tests for the authenticated, canonical executable DSL corpus."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/dsl/generate_executable_corpus.mjs"
FIXTURE = ROOT / "tests/fixtures/dsl/executable-corpus.json"
ORACLE = ROOT / "tests/oracles/dsl_executable_corpus.sha256"


def _temporary_root() -> str:
    """The platform's temporary root.

    Scratch trees used to be pinned to /private/tmp, which exists on Darwin
    and nowhere else; on Linux the pin turned a test that should have skipped
    for a missing authority into a FileNotFoundError.
    """
    return os.environ.get("TMPDIR") or tempfile.gettempdir()


class ExecutableCorpusTest(unittest.TestCase):
    def node(self) -> str:
        value = shutil.which("node")
        if value is None:
            self.skipTest("node is required for executable corpus generation")
        return value

    def authority(self) -> pathlib.Path:
        # No default: the immutable CPU authority lives outside the repository
        # and its location is machine-specific, so it must arrive by env.
        path = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", ""))
        if not path.is_absolute() or not path.is_dir():
            self.skipTest("NOISEMAKER_CPU_ROOT must identify the immutable CPU authority")
        return path

    def run_generator(self, output: pathlib.Path, authority: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.node(), str(GENERATOR), "--cpu-root", str(authority or self.authority()), "--output", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def external_input_records(self):
        script = f"""
import {{externalInputsFor}} from {json.dumps(GENERATOR.as_uri())};
import {{decodeMeshData}} from {json.dumps((ROOT / 'tools/benchmark/mesh_inputs.mjs').as_uri())};
import {{decodeAudioState}} from {json.dumps((ROOT / 'tools/benchmark/audio_inputs.mjs').as_uri())};
import {{decodeMidiState}} from {json.dumps((ROOT / 'tools/benchmark/midi_inputs.mjs').as_uri())};
const packed = value => {{
  const words = new Uint32Array(value.buffer, value.byteOffset, value.length);
  const bytes = Buffer.alloc(words.length * 4);
  for (let i = 0; i < words.length; ++i) bytes.writeUInt32LE(words[i], i * 4);
  return bytes.toString('hex');
}};
const records = {{}};
for (const effect of ['render/meshLoader', 'render/meshRender', 'synth/roll', 'synth/scope', 'synth/spectrum', 'synth/solid']) {{
  const inputs = externalInputsFor(effect);
  if (JSON.stringify(inputs) !== JSON.stringify(externalInputsFor(effect))) throw new Error('nondeterministic fixture');
  const decoded = {{}};
  if (inputs?.meshData) {{
    const mesh = decodeMeshData(inputs.meshData);
    decoded.positions = packed(mesh.positionData); decoded.normals = packed(mesh.normalData);
  }}
  if (inputs?.audioState) {{
    const audio = decodeAudioState(inputs.audioState);
    decoded.waveform = packed(audio.waveform); decoded.spectrum = packed(audio.spectrum);
  }}
  if (inputs?.midiState) {{
    const midi = decodeMidiState(inputs.midiState);
    decoded.midi = packed(midi.noteGrid); decoded.clock = midi.clockCount;
  }}
  records[effect] = {{inputs: inputs ?? null, decoded}};
}}
console.log(JSON.stringify(records));
"""
        result = subprocess.run([self.node(), "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_external_inputs_exercise_triangles_audio_and_midi(self) -> None:
        records = self.external_input_records()
        mesh = records["render/meshRender"]["inputs"]["meshData"]
        self.assertEqual((mesh["texWidth"], mesh["texHeight"]), (3, 2))
        positions = struct.unpack("<24f", bytes.fromhex(mesh["positionRgba32f"]))
        normals = struct.unpack("<24f", bytes.fromhex(mesh["normalRgba32f"]))
        for first in (0, 12):
            a, b, c = (positions[first + offset:first + offset + 4] for offset in (0, 4, 8))
            self.assertGreater((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]), 0)
            self.assertEqual([a[3], b[3], c[3]], [1, 1, 1])
        self.assertGreater(len(set(positions[2::4])), 1)
        self.assertGreater(len({normals[i:i + 3] for i in range(0, 24, 4)}), 1)
        for effect in ("synth/scope", "synth/spectrum"):
            audio = records[effect]["inputs"]["audioState"]
            self.assertNotEqual(audio["waveformFloat32"], audio["spectrumFloat32"])
            for field in ("waveformFloat32", "spectrumFloat32"):
                samples = struct.unpack("<128f", bytes.fromhex(audio[field]))
                self.assertGreater(max(samples), .9)
                self.assertLess(min(samples), .1)
                self.assertGreater(len(set(samples)), 100)
        midi = records["synth/roll"]["inputs"]["midiState"]
        grid = struct.unpack("<8192f", bytes.fromhex(midi["noteGridRgba32f"]))
        velocities = []
        for channel in range(16):
            notes = [grid[(channel * 128 + key) * 4:(channel * 128 + key) * 4 + 4] for key in range(128)]
            active = [note for note in notes if note[1] > .5]
            self.assertEqual(len(active), 1)
            velocities.append(active[0][0])
        self.assertEqual(len(set(velocities)), 16)
        self.assertTrue(all(0 < velocity <= 1 for velocity in velocities))
        self.assertEqual(midi["clockCount"], 48)
        self.assertIsNone(records["synth/solid"]["inputs"])

    def test_native_flags_and_cpu_decoders_receive_identical_input_words(self) -> None:
        from tools.benchmark.corpus_lane import record_flags
        records = self.external_input_records()
        with tempfile.TemporaryDirectory(prefix="external-input-transport-") as raw:
            for effect, item in records.items():
                if item["inputs"] is None:
                    continue
                record = {"sourceSha256": "a" * 64, "externalInputs": item["inputs"],
                          "options": {"width": 17, "height": 11, "time": .25,
                                      "frame": 0, "seed": 1}}
                source = pathlib.Path(raw) / (effect.replace("/", "_") + ".dsl")
                flags = record_flags(record, source)
                for field, flag in (("positions", "--mesh-positions-file"),
                                    ("normals", "--mesh-normals-file"),
                                    ("waveform", "--audio-waveform-file"),
                                    ("spectrum", "--audio-spectrum-file"),
                                    ("midi", "--midi-note-grid-file")):
                    if field in item["decoded"]:
                        payload = pathlib.Path(flags[flags.index(flag) + 1]).read_bytes()
                        self.assertEqual(payload.hex(), item["decoded"][field], (effect, field))
                if effect == "synth/roll":
                    self.assertEqual(float(flags[flags.index("--midi-clock") + 1]), item["decoded"]["clock"])

    def test_checked_external_inputs_match_the_generator(self) -> None:
        records = {row["effectId"]: row for row in json.loads(FIXTURE.read_text())["records"]}
        for effect, generated in self.external_input_records().items():
            if generated["inputs"] is None:
                self.assertNotIn("externalInputs", records[effect])
                continue
            with self.subTest(effect=effect):
                self.assertEqual(records[effect]["recordKind"], "admitted")
                self.assertEqual(records[effect]["externalInputs"], generated["inputs"])

    def test_checked_manifest_has_dynamic_counts_and_required_provenance(self) -> None:
        manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "noisemaker-cpp.dsl-executable-corpus.v1")
        self.assertEqual(manifest["manifestSha256"], ORACLE.read_text(encoding="utf-8").strip())
        compatibility = json.loads((ROOT / "src/effects/generated/backend_compatibility.json").read_text())
        expected_tree = compatibility["authority"]["upstream_tree"]
        self.assertEqual(manifest["provenance"]["upstreamTree"], expected_tree)
        records = manifest["records"]
        self.assertEqual(manifest["counts"]["admitted"], sum(r["recordKind"] == "admitted" for r in records))
        self.assertEqual(manifest["counts"]["excluded"], sum(r["recordKind"] == "excluded" for r in records))
        self.assertEqual(len({r["id"] for r in records}), len(records))
        self.assertGreater(manifest["counts"]["admitted"], 0)
        self.assertGreater(manifest["counts"]["excluded"], 0)
        self.assertTrue(any(r["effectId"] == "filter/blur" and r["recordKind"] == "admitted" for r in records))
        mesh = next(r for r in records if r["effectId"] == "render/meshLoader")
        self.assertEqual(mesh["recordKind"], "admitted")
        mesh_data = mesh["externalInputs"]["meshData"]
        self.assertEqual((mesh_data["texWidth"], mesh_data["texHeight"]), (2, 2))
        self.assertEqual(len(bytes.fromhex(mesh_data["positionRgba32f"])), 64)
        self.assertEqual(len(bytes.fromhex(mesh_data["normalRgba32f"])), 64)
        feedback = next(r for r in records if r["effectId"] == "filter/feedback")
        self.assertEqual(feedback["recordKind"], "excluded")
        self.assertEqual(feedback["firstFailure"]["code"], "unsupported_pass")
        for record in records:
            self.assertEqual(record["sourceSha256"], hashlib.sha256(record["source"].encode()).hexdigest())
            self.assertEqual(record["options"]["width"], 17)
            self.assertEqual(record["options"]["height"], 11)
            self.assertIn("coverage", record)
            self.assertIn("provenance", record)
            self.assertEqual(record["provenance"]["upstreamTree"], expected_tree)
            if record["recordKind"] == "admitted":
                self.assertIn("plan", record)
            else:
                self.assertTrue(record["allReasons"])

    def test_generation_is_deterministic_and_does_not_rewrite_fixture(self) -> None:
        authority = self.authority()
        fixture_before = FIXTURE.read_bytes()
        oracle_before = ORACLE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-corpus-", dir=_temporary_root()) as directory:
            first = pathlib.Path(directory) / "first.json"
            second = pathlib.Path(directory) / "second.json"
            for output in (first, second):
                result = self.run_generator(output, authority)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            generated = json.loads(first.read_text(encoding="utf-8"))
            checked = json.loads(FIXTURE.read_text(encoding="utf-8"))
            # Nothing is discarded before comparing: a pinned fixture the
            # generator cannot reproduce byte-for-byte is not a pin. Provenance
            # drift used to hide here.
            self.assertEqual(generated, checked)
            # And the recorded provenance has to describe this tree, not an
            # earlier one, so a typed-slice regeneration that forgets the
            # corpus is loud instead of silent.
            live_manifest = hashlib.sha256(
                (ROOT / "src/typed_generated/typed_manifest.json").read_bytes()).hexdigest()
            self.assertEqual(checked["provenance"]["typedManifestSha256"], live_manifest)
            for record in checked["records"]:
                self.assertEqual(record["provenance"]["typedManifestSha256"], live_manifest)
        self.assertEqual(FIXTURE.read_bytes(), fixture_before)
        self.assertEqual(ORACLE.read_bytes(), oracle_before)

    def test_generator_fails_closed_for_forged_authority_before_import(self) -> None:
        authority = self.authority()
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-corpus-forge-", dir=_temporary_root()) as directory:
            forged = pathlib.Path(directory) / "cpu"
            shutil.copytree(authority, forged, symlinks=True)
            marker = forged / "imported-marker"
            renderer = forged / "src/runtime/renderer.js"
            renderer.write_text(f"import fs from 'node:fs'; fs.writeFileSync({json.dumps(str(marker))}, 'imported');\n")
            result = self.run_generator(pathlib.Path(directory) / "output.json", forged)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertTrue("behavioral" in result.stderr or "sha256" in result.stderr or "symlink" in result.stderr)


if __name__ == "__main__":
    unittest.main()
