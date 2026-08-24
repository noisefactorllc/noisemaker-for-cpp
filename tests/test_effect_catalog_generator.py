from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CPU = pathlib.Path(os.environ.get("NOISEMAKER_CPU_ROOT", "/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu"))
SHADER = pathlib.Path(os.environ.get("NOISEMAKER_SHADER_GIT", "/Users/aayars/platform/noisemaker"))
EXPORTER = ROOT / "tools/dsl/export_cpu_catalog.mjs"
GENERATOR = ROOT / "tools/dsl/generate_effect_catalog.py"


class EffectCatalogGeneratorTests(unittest.TestCase):
    def run_generator(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-B", str(GENERATOR), *args], cwd=ROOT, text=True,
            capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_requires_explicit_authority_paths(self) -> None:
        result = self.run_generator("--check")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--cpu-root", result.stderr)

    def test_exporter_preserves_order_and_raw_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-export-") as td:
            output = pathlib.Path(td) / "catalog.json"
            result = subprocess.run(
                ["node", str(EXPORTER), "--cpu-root", str(CPU), "--output", str(output)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            document = json.loads(output.read_text())
            self.assertEqual("noisemaker-cpp.cpu-effect-catalog.v1", document["schema"])
            self.assertEqual(205, len(document["records"]))
            self.assertEqual("classicNoisedeck/bitEffects", document["records"][0]["id"])
            self.assertEqual("synth3d/shape3d", document["records"][-1]["id"])
            self.assertEqual(
                ["id", "directoryName", "name", "namespace", "func", "kind", "domain", "tags",
                 "description", "paramAliases", "params", "passes", "textures", "externalTexture"],
                list(document["records"][0]),
            )

    def test_generation_is_deterministic_and_derives_status_counts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-generate-") as td:
            out = pathlib.Path(td)
            args = ("--cpu-root", str(CPU), "--shader-git", str(SHADER),
                    "--compatibility", str(ROOT / "src/effects/generated/backend_compatibility.json"),
                    "--output-dir", str(out))
            first = self.run_generator(*args)
            self.assertEqual(0, first.returncode, first.stderr)
            first_bytes = (out / "effect_catalog.cpp").read_bytes()
            first_provenance = (out / "effect_catalog.provenance.json").read_bytes()
            second = self.run_generator(*args)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(first_bytes, (out / "effect_catalog.cpp").read_bytes())
            self.assertEqual(first_provenance, (out / "effect_catalog.provenance.json").read_bytes())
            provenance = json.loads(first_provenance)
            self.assertEqual(205, provenance["counts"]["definitions"])
            self.assertEqual(305, provenance["counts"]["passes"])
            self.assertEqual(295, provenance["counts"]["reference_program_keys"])
            self.assertEqual(210, provenance["counts"]["compatible_programs"])
            self.assertEqual(1, provenance["counts"]["incompatible_programs"])
            self.assertEqual(93, provenance["counts"]["missing_passes"])
            self.assertEqual(1, provenance["counts"]["scatter_passes"])
            self.assertEqual(hashlib.sha256(first_bytes).hexdigest(), provenance["generated_sha256"])

    def test_unknown_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-unknown-") as td:
            exported = pathlib.Path(td) / "catalog.json"
            subprocess.run(["node", str(EXPORTER), "--cpu-root", str(CPU), "--output", str(exported)], check=True)
            document = json.loads(exported.read_text())
            document["records"][0]["unknownField"] = True
            exported.write_text(json.dumps(document))
            result = self.run_generator("--cpu-root", str(CPU), "--shader-git", str(SHADER),
                                        "--compatibility", str(ROOT / "src/effects/generated/backend_compatibility.json"),
                                        "--input", str(exported), "--output-dir", td)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unknown", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
