from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import subprocess
import tempfile
import unittest

import tools.dsl.generate_effect_catalog as generator
from tools.dsl.generate_effect_catalog import CatalogError, _canonical_json_value, _decode, load_export

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
            self.assertEqual("string", document["records"][0]["id"]["$type"])
            self.assertEqual("synth3d/shape3d", load_export(output)[-1]["id"])
            first = load_export(output)[0]
            self.assertIn("externalTexture", first)
            self.assertIsNone(first["externalTexture"])
            self.assertNotIn("outputTex3d", first)
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
            self.assertEqual("6ced4d890dc665f5f3d1196286260b972ae6858ccc9d045ec94c4e81479bf996", provenance["normalized_record_stream_sha256"])
            self.assertIn("generated_payload_sha256", provenance)
            payload_hash = provenance["generated_payload_sha256"]
            marker = f'c.provenance.generated_payload_sha256 = "{payload_hash}";'.encode()
            self.assertEqual(1, first_bytes.count(marker))
            placeholder = first_bytes.replace(marker, b'c.provenance.generated_payload_sha256 = "";', 1)
            self.assertEqual(hashlib.sha256(placeholder).hexdigest(), payload_hash)

    def test_canonical_numeric_envelope_is_injective_and_round_trips(self) -> None:
        values = [math.nan, math.inf, -math.inf, -0.0,
                  "number:NaN", "number:+Infinity", "number:-Infinity", "number:-0"]
        encoded = [_canonical_json_value(value) for value in values]
        self.assertEqual(len({json.dumps(value, sort_keys=True) for value in encoded}), len(values))
        self.assertTrue(math.isnan(_decode(encoded[0])))
        self.assertTrue(math.isinf(_decode(encoded[1])) and _decode(encoded[1]) > 0)
        self.assertTrue(math.isinf(_decode(encoded[2])) and _decode(encoded[2]) < 0)
        self.assertTrue(math.copysign(1.0, _decode(encoded[3])) < 0)
        self.assertEqual(values[4:], [_decode(value) for value in encoded[4:]])

    def test_unknown_schema_is_rejected_without_authority_bypass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-unknown-") as td:
            exported = pathlib.Path(td) / "catalog.json"
            subprocess.run(["node", str(EXPORTER), "--cpu-root", str(CPU), "--output", str(exported)], check=True)
            document = json.loads(exported.read_text())
            document["records"][0]["unknownField"] = True
            exported.write_text(json.dumps(document))
            with self.assertRaises(CatalogError):
                load_export(exported)

    def test_numeric_envelope_round_trips_specials_and_sentinel_strings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-numbers-") as td:
            output = pathlib.Path(td) / "catalog.json"
            subprocess.run(["node", str(EXPORTER), "--cpu-root", str(CPU), "--output", str(output)], check=True)
            document = json.loads(output.read_text())
            # The authority contains no special values, so exercise the typed
            # envelope through the schema loader without changing production
            # authority input or generated output.
            record = document["records"][0]
            record["description"] = {"$type": "array", "items": [
                {"$type": "number", "value": "NaN"},
                {"$type": "number", "value": "+Infinity"},
                {"$type": "number", "value": "-Infinity"},
                {"$type": "number", "value": "-0"},
                {"$type": "string", "value": "number:NaN"},
                {"$type": "string", "value": "number:-0"},
            ]}
            output.write_text(json.dumps(document))
            values = load_export(output)[0]["description"]
            self.assertTrue(math.isnan(values[0]))
            self.assertTrue(math.isinf(values[1]) and values[1] > 0)
            self.assertTrue(math.isinf(values[2]) and values[2] < 0)
            self.assertTrue(math.copysign(1.0, values[3]) < 0)
            self.assertEqual("number:NaN", values[4])
            self.assertEqual("number:-0", values[5])

    def test_manifest_sha_and_forged_status_rows_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-manifest-") as td:
            manifest = pathlib.Path(td) / "backend.json"
            source = ROOT / "src/effects/generated/backend_compatibility.json"
            manifest.write_bytes(source.read_bytes())
            document = json.loads(manifest.read_text())
            document["canonical_programs"][0]["status"] = "incompatible"
            manifest.write_text(json.dumps(document))
            result = self.run_generator("--cpu-root", str(CPU), "--shader-git", str(SHADER),
                                        "--compatibility", str(manifest), "--output-dir", td)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("sha", result.stderr.lower())

    def test_structural_join_rejects_duplicate_missing_and_inconsistent_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="catalog-join-") as td:
            export = pathlib.Path(td) / "catalog.json"
            subprocess.run(["node", str(EXPORTER), "--cpu-root", str(CPU), "--output", str(export)], check=True)
            records = load_export(export)
            source = ROOT / "src/effects/generated/backend_compatibility.json"
            original_sha = generator.COMPATIBILITY_SHA256
            try:
                for mutate in (
                    lambda document: document["canonical_programs"].append(dict(document["canonical_programs"][0])),
                    lambda document: document["reference_key_closure"].pop(),
                    lambda document: document["reference_passes"][0].update(status="incompatible"),
                ):
                    document = json.loads(source.read_text())
                    mutate(document)
                    candidate = pathlib.Path(td) / "candidate.json"
                    candidate.write_text(json.dumps(document))
                    generator.COMPATIBILITY_SHA256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
                    with self.assertRaises(CatalogError):
                        generator._validate_compatibility(document, records, candidate)
            finally:
                generator.COMPATIBILITY_SHA256 = original_sha


if __name__ == "__main__":
    unittest.main()
