from __future__ import annotations

import hashlib
import copy
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

from tests import corpus_census
from tools.dsl import generate_backend_compatibility as generator
from tools.dsl import mesh_render_contract


ROOT = pathlib.Path(__file__).resolve().parents[1]
# No defaults, and no import-time abort: the frozen CPU authority and the live
# shader checkout live outside the repository at machine-specific locations, so
# they must arrive by env. Raising here would break `unittest discover` for the
# entire suite on any checkout that lacks them, so the gate moved into
# setUpClass -- unset env skips, a set-but-wrong env still fails hard.
CPU_ENV = os.environ.get("NOISEMAKER_CPU_ROOT")
SHADER_ENV = os.environ.get("NOISEMAKER_SHADER_GIT")
CPU_ROOT = pathlib.Path(CPU_ENV or "/nonexistent")
SHADER_GIT = pathlib.Path(SHADER_ENV or "/nonexistent")
MANIFEST = ROOT / "src/effects/generated/backend_compatibility.json"


class BackendCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not CPU_ENV or not SHADER_ENV:
            raise unittest.SkipTest("NOISEMAKER_CPU_ROOT and NOISEMAKER_SHADER_GIT are required")
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
        whole_pass = [row for row in document["canonical_programs"]
                      if row["factory"]["route"]["kind"] == "whole_pass"]
        self.assertEqual([mesh_render_contract.KEY], [row["program_key"] for row in whole_pass])
        self.assertEqual(mesh_render_contract.compatibility_row(ROOT), whole_pass[0])
        self.assertEqual(corpus_census.typed_count() + len(whole_pass) + 2,
                         document["counts"]["fragment_rows"])
        self.assertEqual(corpus_census.typed_count() + len(whole_pass),
                         document["counts"]["unique_fragment_keys"])
        self.assertNotIn("semantic", whole_pass[0])
        self.assertNotIn("typed_manifest_output", whole_pass[0]["factory"])
        self.assertEqual(sorted(document["reference_key_closure"]),
                         [item["program_key"] for item in corpus_census.pending()["authority"]["programs"]])
        self.assertEqual(
            ["filter/invert:inv", "synth/solid:solid"],
            document["counts"]["duplicate_fragment_keys"],
        )
        self.assertEqual("filter/wormhole:deposit", document["scatter"]["program_key"])
        self.assertEqual("5976b7a6b77f69c47c41f4ee296a54d5318e1f9d", document["authority"]["upstream_revision"])
        self.assertEqual("b0729d2bf429e0e7307ff8f4fffe99422870c059", document["authority"]["upstream_tree"])
        self.assertEqual("c2e0c264dc20338b19a144ee0888bd2ca39edcf325315a7d7ae1f5ced920804d", document["authority"]["source_lock_sha256"])
        self.assertEqual(corpus_census.vendored_count(), document["counts"]["raw_exact"])
        self.assertEqual(0, document["counts"]["semantic_exact"])
        self.assertEqual([], document["counts"]["incompatible_keys"])
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

    def test_particle_family_scatter_contracts_are_registered(self) -> None:
        contracts = {item["program_key"]: item for item in self.document["scatter_contracts"]}
        self.assertEqual(
            {"points/physarum:deposit", "points/dla:depositGrid",
             "points/lenia:deposit", "filter3d/flow3d:deposit"},
            set(contracts))
        for key, item in contracts.items():
            self.assertEqual("registered", item["status"])
            self.assertEqual("noisemaker::scatter::resolve_scatter_adapter", item["registry"])
            self.assertEqual("in_place_accumulate", item["destination_mutation"])
            self.assertEqual("points", item["draw_mode"])
            self.assertEqual(item["output_route"], item["output_abi"]["logical_routes"][0])
        self.assertEqual(
            "noisemaker::scatter::physarum::adapter",
            contracts["points/physarum:deposit"]["adapter"])
        self.assertEqual(["xyzTex", "rgbaTex"],
                         contracts["points/physarum:deposit"]["samplers"])
        self.assertEqual([{"name": "depositAmount", "cpp_type": "double",
                           "source": "effect_parameter"}],
                         contracts["points/lenia:deposit"]["uniforms"])
        self.assertEqual("pass", contracts["filter3d/flow3d:deposit"]["count"])

    def test_particle_family_scatter_contract_mutants_fail_closed(self) -> None:
        for mutate in (
            lambda document: document["scatter_contracts"][0].update(status="compatible"),
            lambda document: document["scatter_contracts"][0].update(
                adapter="noisemaker::scatter::forged::adapter"),
            lambda document: document["scatter_contracts"].pop(),
        ):
            self._assert_fails_closed(mutate)

    def test_particle_family_scatter_authentication_fails_closed(self) -> None:
        import json as _json
        from tools.glslcpp import check_corpus
        metadata = _json.loads((ROOT / "tools/glslcpp/corpus" /
                                check_corpus.REVISION / "metadata.json").read_text())
        effect = metadata["effects"]["points/physarum"]
        raw = (ROOT / "tools/glslcpp/corpus" / check_corpus.REVISION /
               "sources/points/physarum/deposit.frag").read_bytes()
        generator.authenticate_scatter_contract("points/physarum:deposit", raw, effect)
        with self.assertRaises(ValueError):
            generator.authenticate_scatter_contract("filter/wormhole:deposit", raw, effect)
        deposit_index = next(index for index, item in enumerate(effect["passes"])
                             if item["program"] == "deposit")
        forged_pass = copy.deepcopy(effect)
        forged_pass["passes"][deposit_index]["outputs"] = {"fragColor": "global_forged"}
        with self.assertRaises(ValueError):
            generator.authenticate_scatter_contract("points/physarum:deposit", raw, forged_pass)
        forged_mode = copy.deepcopy(effect)
        forged_mode["passes"][deposit_index]["drawMode"] = "triangles"
        with self.assertRaises(ValueError):
            generator.authenticate_scatter_contract("points/physarum:deposit", raw, forged_mode)
        with self.assertRaises(ValueError):
            generator.authenticate_scatter_contract(
                "points/physarum:deposit", raw + b"\n", effect)

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

    def test_mesh_whole_pass_source_route_and_abi_forgery_fail_closed(self) -> None:
        for change in (
            lambda row: row["factory"]["route"].update(kind="typed_emitter"),
            lambda row: row["whole_pass_contract"].update(cpu_adapter_sha256="0" * 64),
            lambda row: row["whole_pass_contract"].update(vertex_sha256="0" * 64),
            lambda row: row["whole_pass_contract"].update(definition_sha256="0" * 64),
            lambda row: row["uniforms"].reverse(),
            lambda row: row["samplers"][0].update(resource="forged"),
            lambda row: row["output_abi"]["extent"].update(format="rgba32f"),
        ):
            def mutate(document, change=change):
                row = next(row for row in document["canonical_programs"]
                           if row["program_key"] == mesh_render_contract.KEY)
                change(row)
            self._assert_fails_closed(mutate)

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
