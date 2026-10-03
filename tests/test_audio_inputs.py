from __future__ import annotations

import json
import pathlib
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.benchmark.corpus_lane import record_flags
from tools.parity import sweep

ROOT = pathlib.Path(__file__).resolve().parents[1]


class AudioInputTests(unittest.TestCase):
    def test_sweep_routes_the_same_audio_words_into_both_driver_inputs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            sweep._init_worker(sweep.RunConfig(
                node="node", driver="cpp-driver", cpu_root="authority", ledger="ledger",
                scratch_root=str(root), timeout=1.0))
            captured = {}
            def run(command, timeout):
                if command[0] == "node":
                    record_path = pathlib.Path(command[command.index("--case") + 1])
                    captured["record"] = json.loads(record_path.read_text())
                else:
                    for name in ("waveform", "spectrum"):
                        flag = f"--audio-{name}-file"
                        captured[name] = pathlib.Path(command[command.index(flag) + 1]).read_bytes()
                pathlib.Path(command[command.index("--rgba8-output") + 1]).write_bytes(bytes(4))
                pathlib.Path(command[command.index("--float32-output") + 1]).write_bytes(bytes(16))
                return 0, "{}", "", False, 0.0
            for effect in ("scope", "spectrum"):
                job = sweep.Job(effect, f"synth/{effect}", "default",
                    f"search synth\n{effect}().write(o0)\nrender(o0)\n", 1, 1, 0.0, 1)
                with patch.object(sweep, "_run_proc", run):
                    result = sweep.run_job(vars(job))
                self.assertEqual(result["classification"], "byte_exact")
                audio = captured["record"]["externalInputs"]["audioState"]
                for name in ("waveform", "spectrum"):
                    self.assertEqual(bytes.fromhex(audio[name + "Float32"]), captured[name])
                    self.assertEqual(len(captured[name]), 512)

    def test_js_audio_decoder_owns_exact_float32_words_and_defaults_to_zero(self):
        words = [0x80000000, 0x7F800001, 0xFFC12345, 0x3F9E064B] + [0] * 124
        packed = struct.pack("<128I", *words).hex()
        script = f'''
import {{decodeAudioState}} from {json.dumps((ROOT / "tools/benchmark/audio_inputs.mjs").as_uri())};
const state = decodeAudioState({{waveformFloat32: {json.dumps(packed)}}});
const other = decodeAudioState({{}});
console.log(JSON.stringify({{words: [...new Uint32Array(state.waveform.buffer)],
  spectrum: [...state.spectrum], waveformDefault: [...other.waveform],
  independent: state.waveform.buffer !== other.waveform.buffer}}));
for (const bad of ['', '00', '0'.repeat(1016), '0'.repeat(1032), 'x'.repeat(1024)]) {{
  let rejected = false;
  try {{ decodeAudioState({{spectrumFloat32: bad}}); }} catch {{ rejected = true; }}
  if (!rejected) process.exit(3);
}}
'''
        result = subprocess.run(["node", "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        decoded = json.loads(result.stdout)
        self.assertEqual(decoded["words"], words)
        self.assertEqual(decoded["spectrum"], [0] * 128)
        self.assertEqual(decoded["waveformDefault"], [0] * 128)
        self.assertTrue(decoded["independent"])

    def test_record_flags_preserve_words_and_reject_inexact_lengths(self):
        words = [0x80000000, 0x7F800001] + [0] * 126
        payload = struct.pack("<128I", *words)
        record = {"sourceSha256": "a" * 64,
                  "options": {"width": 3, "height": 2, "time": 0, "frame": 0, "seed": 1},
                  "externalInputs": {"audioState": {"waveformFloat32": payload.hex()}}}
        with tempfile.TemporaryDirectory() as raw:
            source = pathlib.Path(raw) / "case.dsl"
            flags = record_flags(record, source)
            self.assertIn("--audio-waveform-file", flags)
            self.assertNotIn("--audio-spectrum-file", flags)
            path = pathlib.Path(flags[flags.index("--audio-waveform-file") + 1])
            self.assertEqual(path.read_bytes(), payload)
            for malformed in ("", "00", "0" * 1016, "0" * 1032, " " * 1024):
                record["externalInputs"]["audioState"]["waveformFloat32"] = malformed
                with self.assertRaises(ValueError):
                    record_flags(record, source)


if __name__ == "__main__":
    unittest.main()
