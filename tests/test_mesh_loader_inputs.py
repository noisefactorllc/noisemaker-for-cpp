from __future__ import annotations

import pathlib
import json
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.benchmark.corpus_lane import record_flags
from tools.parity import sweep


class MeshLoaderInputTests(unittest.TestCase):
    def test_js_decoder_preserves_signed_zero_and_nan_payload_words(self):
        module = pathlib.Path(__file__).resolve().parents[1] / "tools/benchmark/mesh_inputs.mjs"
        # Both NaN signs, signaling/quiet payloads, signed zero, and infinities.
        words = [0x00000000, 0x80000000, 0x7F800001, 0xFF800001,
                 0x7FC12345, 0xFFC54321, 0x7F800000, 0xFF800000]
        payload = struct.pack("<8I", *words).hex()
        script = f"""
import {{ decodeMeshData }} from {json.dumps(module.as_uri())};
const data = decodeMeshData({{texWidth: 1, texHeight: 2,
  positionRgba32f: {json.dumps(payload)}, normalRgba32f: ''}});
console.log(JSON.stringify([...new Uint32Array(data.positionData.buffer)]));
"""
        result = subprocess.run(["node", "--input-type=module", "-e", script],
                                capture_output=True, text=True, check=True)
        self.assertEqual(words, json.loads(result.stdout))

    def test_sweep_supplies_identical_mesh_words_to_both_drivers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            sweep._init_worker(sweep.RunConfig(node="node", driver="cpp-driver", cpu_root="authority",
                ledger="ledger", scratch_root=str(root), timeout=1.0))
            job = sweep.Job("mesh", "render/meshLoader", "default",
                           "search render\nmeshLoader().write(o0)\nrender(o0)\n", 1, 1, 0.0, 1)
            captured = {}
            def run(command, timeout):
                if command[0] == "node":
                    captured["record"] = json.loads(pathlib.Path(command[command.index("--case") + 1]).read_text())
                else:
                    captured["positions"] = pathlib.Path(command[command.index("--mesh-positions-file") + 1]).read_bytes()
                pathlib.Path(command[command.index("--rgba8-output") + 1]).write_bytes(bytes(4))
                pathlib.Path(command[command.index("--float32-output") + 1]).write_bytes(bytes(16))
                return 0, "{}", "", False, 0.0
            with patch.object(sweep, "_run_proc", run):
                result = sweep.run_job(vars(job))
            self.assertEqual("byte_exact", result["classification"])
            mesh = captured["record"]["externalInputs"]["meshData"]
            self.assertEqual(bytes.fromhex(mesh["positionRgba32f"]), captured["positions"])

    def test_driver_inputs_preserve_packed_float32_words(self):
        mesh = sweep.synthetic_mesh_data()
        record = {
            "sourceSha256": "a" * 64,
            "options": {"width": 17, "height": 11, "time": 0.25, "frame": 0, "seed": 1},
            "externalInputs": {"meshData": mesh},
        }
        with tempfile.TemporaryDirectory() as directory:
            flags = record_flags(record, pathlib.Path(directory) / "case.dsl")
            self.assertEqual(f"{mesh['texWidth']}x{mesh['texHeight']}", flags[flags.index("--mesh-size") + 1])
            for flag, field in (("--mesh-positions-file", "positionRgba32f"),
                                ("--mesh-normals-file", "normalRgba32f")):
                path = pathlib.Path(flags[flags.index(flag) + 1])
                self.assertEqual(bytes.fromhex(mesh[field]), path.read_bytes())
            values = struct.unpack("<" + "f" * (len(mesh["positionRgba32f"]) // 8),
                                   bytes.fromhex(mesh["positionRgba32f"]))
            self.assertTrue(any(value < 0 for value in values))
            self.assertTrue(any(value > 1 for value in values))

    def test_sweep_mesh_render_and_mixed_chains_share_triangle_words_in_both_drivers(self):
        meshes = []
        for effect, chain in (("render/meshRender", []),
                              ("render/meshLoader", ["render/meshRender"]),
                              ("render/meshRender", ["render/meshLoader"]),
                              ("chain", ["render/meshLoader", "render/meshRender"])):
            with self.subTest(effect=effect, chain=chain), tempfile.TemporaryDirectory() as directory:
                sweep._init_worker(sweep.RunConfig(node="node", driver="cpp-driver", cpu_root="authority",
                    ledger="ledger", scratch_root=directory, timeout=1.0))
                job = sweep.Job("mesh-triangles", effect, "default", "mesh fixture", 1, 1, 0.0, 1,
                                chain_effects=chain)
                captured = {}

                def run(command, timeout):
                    if command[0] == "node":
                        captured["record"] = json.loads(pathlib.Path(command[command.index("--case") + 1]).read_text())
                    else:
                        for flag in ("--mesh-positions-file", "--mesh-normals-file"):
                            if flag in command:
                                captured[flag] = pathlib.Path(command[command.index(flag) + 1]).read_bytes()
                        if "--mesh-size" in command:
                            captured["size"] = command[command.index("--mesh-size") + 1]
                    pathlib.Path(command[command.index("--rgba8-output") + 1]).write_bytes(bytes(4))
                    pathlib.Path(command[command.index("--float32-output") + 1]).write_bytes(bytes(16))
                    return 0, "{}", "", False, 0.0

                with patch.object(sweep, "_run_proc", run):
                    result = sweep.run_job(vars(job))
                self.assertEqual("byte_exact", result["classification"])
                self.assertIn("meshData", captured["record"].get("externalInputs", {}))
                mesh = captured["record"]["externalInputs"]["meshData"]
                self.assertEqual((mesh["texWidth"], mesh["texHeight"]), (3, 2))
                self.assertEqual(captured["size"], "3x2")
                for flag, field in (("--mesh-positions-file", "positionRgba32f"),
                                    ("--mesh-normals-file", "normalRgba32f")):
                    self.assertEqual(bytes.fromhex(mesh[field]), captured[flag])
                meshes.append(mesh)
        self.assertEqual(len(meshes), 4)
        self.assertTrue(all(mesh == meshes[0] for mesh in meshes))
        positions = struct.unpack("<24f", bytes.fromhex(meshes[0]["positionRgba32f"]))
        normals = struct.unpack("<24f", bytes.fromhex(meshes[0]["normalRgba32f"]))
        triangles = [[positions[first + offset:first + offset + 4] for offset in (0, 4, 8)]
                     for first in (0, 12)]
        for triangle in triangles:
            # Origin is strictly inside both CCW triangles, ensuring overlap.
            for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                self.assertGreater((b[0] - a[0]) * -a[1] - (b[1] - a[1]) * -a[0], 0)
            self.assertEqual([v[3] for v in triangle], [1, 1, 1])
        self.assertLess(max(v[2] for v in triangles[1]), min(v[2] for v in triangles[0]) + 1e-6)
        self.assertGreater(len({normals[i:i + 3] for i in range(0, 24, 4)}), 3)
        self.assertEqual(normals[3::4], (0,) * 6)

    def test_malformed_mesh_payload_is_rejected_before_driver_dispatch(self):
        record = {"sourceSha256": "a" * 64,
                  "options": {"width": 1, "height": 1, "time": 0, "frame": 0, "seed": 1},
                  "externalInputs": {"meshData": {"texWidth": 1, "texHeight": 1,
                      "positionRgba32f": "00", "normalRgba32f": "00"}}}
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            record_flags(record, pathlib.Path(directory) / "case.dsl")

    def test_empty_partial_and_extra_float_arrays_are_forwarded_without_padding(self):
        for values in ([], [0.125], [float(index) for index in range(9)]):
            payload = struct.pack("<" + "f" * len(values), *values)
            record = {"sourceSha256": "a" * 64,
                      "options": {"width": 1, "height": 1, "time": 0, "frame": 0, "seed": 1},
                      "externalInputs": {"meshData": {"texWidth": 1, "texHeight": 1,
                          "positionRgba32f": payload.hex(), "normalRgba32f": ""}}}
            with self.subTest(values=values), tempfile.TemporaryDirectory() as directory:
                flags = record_flags(record, pathlib.Path(directory) / "case.dsl")
                path = pathlib.Path(flags[flags.index("--mesh-positions-file") + 1])
                self.assertEqual(payload, path.read_bytes())

    def test_omitted_and_null_mesh_dimensions_use_authority_defaults(self):
        for dimensions in ({}, {"texWidth": None, "texHeight": None}):
            record = {"sourceSha256": "a" * 64,
                      "options": {"width": 1, "height": 1, "time": 0, "frame": 0, "seed": 1},
                      "externalInputs": {"meshData": {**dimensions,
                          "positionRgba32f": "", "normalRgba32f": ""}}}
            with self.subTest(dimensions=dimensions), tempfile.TemporaryDirectory() as directory:
                flags = record_flags(record, pathlib.Path(directory) / "case.dsl")
                self.assertEqual("256x256", flags[flags.index("--mesh-size") + 1])


if __name__ == "__main__":
    unittest.main()
