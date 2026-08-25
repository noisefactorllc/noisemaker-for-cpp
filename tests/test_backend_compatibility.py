from __future__ import annotations

import hashlib
import copy
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

from tools.dsl import generate_backend_compatibility as generator


ROOT = pathlib.Path(__file__).resolve().parents[1]
CPU_ENV = os.environ.get("NOISEMAKER_CPU_ROOT")
SHADER_ENV = os.environ.get("NOISEMAKER_SHADER_GIT")
if not CPU_ENV or not SHADER_ENV:
    raise RuntimeError("NOISEMAKER_CPU_ROOT and NOISEMAKER_SHADER_GIT are required")
CPU_ROOT = pathlib.Path(CPU_ENV)
SHADER_GIT = pathlib.Path(SHADER_ENV)
MANIFEST = ROOT / "src/effects/generated/backend_compatibility.json"


class BackendCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not CPU_ROOT.is_dir() or not SHADER_GIT.is_dir():
            raise RuntimeError("authority paths must name existing directories")
        cls.document = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        typed = json.loads((ROOT / "src/typed_generated/typed_manifest.json").read_text(encoding="utf-8"))
        typed_rows = {item["program_key"]: item for item in typed["programs"]}
        rows = {row["program_key"]: row for row in cls.document["canonical_programs"]}
        rows[cls.document["scatter"]["program_key"]] = cls.document["scatter"]
        cls.factory_evidence = generator._factory_evidence(ROOT, typed_rows, rows)

    def test_authority_and_backend_census_are_authenticated(self) -> None:
        document = self.document
        self.assertEqual(213, document["counts"]["fragment_rows"])
        self.assertEqual(211, document["counts"]["unique_fragment_keys"])
        self.assertEqual(
            ["filter/invert:inv", "synth/solid:solid"],
            document["counts"]["duplicate_fragment_keys"],
        )
        self.assertEqual("filter/wormhole:deposit", document["scatter"]["program_key"])
        self.assertEqual("117a236679d1db3ab8f0e278230ece277b57564c", document["authority"]["upstream_revision"])
        self.assertEqual("a7a997dfdc807697adba008729dcdfdfcfbaf53c", document["authority"]["upstream_tree"])
        self.assertEqual("66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4", document["authority"]["source_lock_sha256"])
        self.assertEqual(205, document["counts"]["raw_exact"])
        self.assertEqual(6, document["counts"]["semantic_exact"])
        self.assertEqual(["filter/text:text"], document["counts"]["incompatible_keys"])
        bit = next(row for row in document["canonical_programs"]
                   if row["program_key"] == "classicNoisedeck/bitEffects:bitEffects")
        self.assertEqual("noisemaker::effects::bind_bit_effects", bit["factory"]["canonical"])
        self.assertEqual("custom_adapter", bit["factory"]["route"]["kind"])

    def test_output_extent_uses_authority_default_for_absent_and_explicit_formats(self) -> None:
        effect = {"textures": {"_blurTemp": {"width": "input", "height": "input", "format": "rgba8unorm"}}}
        current_pass = {"viewport": {"width": "screen", "height": "screen"}}
        self.assertEqual("rgba8unorm", generator._extent(effect, current_pass, "_blurTemp")["format"])
        self.assertEqual("rgba16f", generator._extent(effect, current_pass, "outputTex")["format"])

        declared_without_format = {"textures": {"outputTex": {"width": "screen", "height": "screen"}}}
        self.assertEqual("rgba16f", generator._extent(declared_without_format, {}, "outputTex")["format"])
        declared_explicit = {"textures": {"outputTex": {"width": "screen", "height": "screen", "format": "rgba8unorm"}}}
        self.assertEqual("rgba8unorm", generator._extent(declared_explicit, {}, "outputTex")["format"])

    def test_scatter_extent_comes_from_authenticated_effect_texture(self) -> None:
        entry = {"program_key": "filter/wormhole:deposit", "effect_id": "filter/wormhole",
                 "program": "deposit", "source": "sources/filter/wormhole/deposit.glsl"}
        effect = {"textures": {"wormhole_accum": {"width": "100%", "height": "100%", "format": "rgba16f"}},
                  "passes": [{"program": "deposit", "outputs": {"fragColor": "wormhole_accum"}}]}
        row = generator._scatter_source_entry(entry, effect, b"old", b"new")
        self.assertEqual({"width": "100%", "height": "100%", "format": "rgba16f"}, row["output_abi"]["extent"])
        forged_effect = {"textures": {"wormhole_accum": {"width": "screen", "height": "screen", "format": "rgba8unorm"}},
                         "passes": [{"program": "deposit", "outputs": {"fragColor": "wormhole_accum"}}]}
        forged = generator._scatter_source_entry(entry, forged_effect, b"old", b"new")
        self.assertEqual({"width": "screen", "height": "screen", "format": "rgba8unorm"}, forged["output_abi"]["extent"])

    def test_scatter_extent_mutants_fail_closed(self) -> None:
        for mutate in (
            lambda document: document["scatter"]["output_abi"]["extent"].update(width="screen"),
            lambda document: document["scatter"]["output_abi"]["extent"].update(height="screen"),
            lambda document: document["scatter"]["output_abi"]["extent"].update(format="rgba8unorm"),
        ):
            self._assert_fails_closed(mutate)

    def test_manifest_is_deterministic_and_checkable(self) -> None:
        first = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        second = generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        first_bytes = generator._encoded(first)
        second_bytes = generator._encoded(second)
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_bytes, MANIFEST.read_bytes())
        generator.check(cpu_root=CPU_ROOT, shader_git=SHADER_GIT, repository=ROOT)
        first = hashlib.sha256(first_bytes).hexdigest()
        second = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(first, second)

    def test_cli_requires_both_authority_paths(self) -> None:
        result = subprocess.run(
            ["python3", "-B", "tools/dsl/generate_backend_compatibility.py", "--check"],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True, capture_output=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--cpu-root", result.stderr)
        self.assertIn("--shader-git", result.stderr)

    def _assert_fails_closed(self, mutate) -> None:
        forged = copy.deepcopy(self.document)
        mutate(forged)
        with self.assertRaises(generator.CompatibilityError):
            generator.validate_document(
                forged,
                expected_source_hashes={
                    row["program_key"]: row["new_raw_sha256"]
                    for row in self.document["canonical_programs"]
                } | {self.document["scatter"]["program_key"]: self.document["scatter"]["new_raw_sha256"]},
                factory_evidence=self.factory_evidence,
                expected_scatter_extent=self.document["scatter"]["output_abi"]["extent"],
            )

    def test_forged_duplicate_program_fails_closed(self) -> None:
        self._assert_fails_closed(
            lambda document: document["canonical_programs"].append(
                copy.deepcopy(document["canonical_programs"][0])))

    def test_missing_scatter_registration_fails_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["scatter"].update(status="missing"))

    def test_unclassified_binding_fails_closed(self) -> None:
        def remove_source(document):
            document["canonical_programs"][0]["uniforms"][0]["source"] = None
        self._assert_fails_closed(remove_source)

    def test_output_mismatch_fails_closed(self) -> None:
        def change_cardinality(document):
            document["canonical_programs"][0]["output_abi"]["cardinality"] += 1
        self._assert_fails_closed(change_cardinality)

    def test_source_drift_fails_closed(self) -> None:
        self._assert_fails_closed(
            lambda document: document["canonical_programs"][0].update(new_raw_sha256="0" * 64))

    def test_draw_mode_and_dimensionality_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(draw_mode="points"))
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(dimensionality="volume"))

    def test_unknown_status_reason_and_reference_key_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0].update(status="maybe"))
        self._assert_fails_closed(lambda document: document["reference_passes"][0]["reasons"].append("not-structured"))
        self._assert_fails_closed(lambda document: document["reference_passes"][0].update(program_key="forged:key"))

    def test_output_names_routes_and_scatter_hash_fail_closed(self) -> None:
        self._assert_fails_closed(lambda document: document["canonical_programs"][0]["outputs"][0].update(physical_name="forged"))
        self._assert_fails_closed(lambda document: document["canonical_programs"][0]["outputs"][0].update(logical_route="forged"))
        self._assert_fails_closed(lambda document: document["scatter"].update(new_raw_sha256="forged"))

    def test_legacy_factory_evidence_is_independently_authenticated(self) -> None:
        for field in ("path", "source_sha256", "source_program_sha256", "body_sha256",
                      "binding_abi_sha256", "output_abi_sha256"):
            def forge(document, field=field):
                duplicate = next(row for row in document["fragments"]
                                 if row.get("row_kind") == "legacy_duplicate")
                duplicate["factory"]["legacy"][field] = "forged" if field in {"path", "source_program_sha256"} else "0" * 64
            self._assert_fails_closed(forge)

    def test_duplicate_rows_must_equal_canonical_projection(self) -> None:
        mutations = (
            lambda row: row.update(source="sources/forged.glsl"),
            lambda row: row.update(status="compatible" if row["status"] == "incompatible" else "incompatible"),
            lambda row: row["outputs"][0].update(cpp_type="forged"),
            lambda row: row["outputs"][0].update(logical_route="forged"),
            lambda row: row["uniforms"][0].update(cpp_type="forged"),
            lambda row: row["factory"]["route"].update(factory="forged::factory"),
            lambda row: row["factory"].update(legacy_public="forged::legacy"),
        )
        for mutate in mutations:
            def forge(document, mutate=mutate):
                duplicate = next(row for row in document["fragments"]
                                 if row.get("row_kind") == "legacy_duplicate")
                mutate(duplicate)
            self._assert_fails_closed(forge)

    def test_legacy_output_abi_is_scoped_to_bound_callback(self) -> None:
        body = (
            'BoundKernel bind_fixture(const glsl::Bindings& bindings) {\n'
            '  const auto state = bindings.get_or<std::int32_t>("mode", 0);\n'
            '  return BoundKernel(state, &pixel);\n'
            '}')
        text = (
            'void helper(const glsl::PixelContext&, glsl::Vec4& helper_output) {}\n'
            'void pixel(const glsl::PixelContext&, float& wrong_output) {}\n')
        with self.assertRaises(generator.CompatibilityError):
            generator._legacy_factory_abi(text, body, "fixture:key")

    def test_reordered_legacy_bindings_fail_generation(self) -> None:
        source_path = ROOT / "src/generated/synth_solid.cpp"
        source = source_path.read_text(encoding="utf-8")
        source = source.replace(
            'bindings.get_or<float>("alpha", 0.0f), bindings.get_or<glsl::Vec3>("color", glsl::Vec3(0.0f))',
            'bindings.get_or<glsl::Vec3>("color", glsl::Vec3(0.0f)), bindings.get_or<float>("alpha", 0.0f)')
        row = next(item for item in self.document["canonical_programs"]
                   if item["program_key"] == "synth/solid:solid")
        with tempfile.TemporaryDirectory(prefix="noisemaker-legacy-order-") as directory:
            generated = pathlib.Path(directory) / "src/generated"
            generated.mkdir(parents=True)
            (generated / source_path.name).write_text(source, encoding="utf-8")
            with self.assertRaises(generator.CompatibilityError):
                generator._legacy_factories(pathlib.Path(directory), {row["program_key"]: row})

    def test_selected_custom_factory_evidence_is_independently_authenticated(self) -> None:
        for mutate in (
            lambda route: route.update(factory="forged::factory"),
            lambda route: route.update(emitted_factory="forged::emitter"),
            lambda route: route.update(source="src/forged.cpp"),
            lambda route: route.update(source_sha256="0" * 64),
            lambda route: route["binding_abi"]["uniforms"][0].update(cpp_type="forged"),
            lambda route: route["output_abi"].update(cpp_type="forged"),
        ):
            def forge(document, mutate=mutate):
                row = next(item for item in document["canonical_programs"]
                           if item["program_key"] == "classicNoisedeck/bitEffects:bitEffects")
                mutate(row["factory"]["route"])
            self._assert_fails_closed(forge)

    def test_typed_manifest_requires_complete_authenticated_rows(self) -> None:
        corpus_root = generator.check_corpus._corpus_root(ROOT)
        entries = generator.check_corpus._validate_manifest(
            generator.check_corpus._load_json(corpus_root / "manifest.json", "manifest"))
        corpus_keys = {item["program_key"] for item in entries}
        typed_path = ROOT / "src/typed_generated/typed_manifest.json"
        typed = json.loads(typed_path.read_text(encoding="utf-8"))
        typed["programs"].pop()
        with self.assertRaises(generator.CompatibilityError):
            generator._typed_manifest(ROOT, typed, corpus_keys)
        typed = json.loads(typed_path.read_text(encoding="utf-8"))
        typed["programs"].append(copy.deepcopy(typed["programs"][0]))
        with self.assertRaises(generator.CompatibilityError):
            generator._typed_manifest(ROOT, typed, corpus_keys)

    def test_shader_repository_is_not_mutated(self) -> None:
        before = subprocess.run(["git", "-C", str(SHADER_GIT), "status", "--porcelain"],
                                check=True, text=True, capture_output=True).stdout
        generator.generate(cpu_root=CPU_ROOT, shader_git=SHADER_GIT)
        after = subprocess.run(["git", "-C", str(SHADER_GIT), "status", "--porcelain"],
                               check=True, text=True, capture_output=True).stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
