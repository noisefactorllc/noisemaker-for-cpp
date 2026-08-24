"""Tests for the pinned, offline GLSL corpus validator and frontend."""

from __future__ import annotations

import json
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))


class CorpusTests(unittest.TestCase):
    def temporary_repository(self) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        destination = root / "tools" / "glslcpp" / "corpus"
        destination.parent.mkdir(parents=True)
        shutil.copytree(REPOSITORY / "tools" / "glslcpp" / "corpus", destination)
        return temporary

    @staticmethod
    def manifest_path(root: pathlib.Path) -> pathlib.Path:
        return next((root / "tools" / "glslcpp" / "corpus").glob("*/manifest.json"))

    @staticmethod
    def write_manifest(path: pathlib.Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_committed_corpus_has_exact_stateless_gate_counts(self) -> None:
        from tools.glslcpp import check_corpus

        summary = check_corpus.validate_corpus()
        self.assertEqual(
            summary["counts"],
            {
                "effects": 167,
                "passes": 212,
                "sources": 212,
                "generated": 208,
                "adapter": 4,
                "keyed_runtime": 211,
                "draw_op_overrides": 1,
            },
        )

    def test_report_is_stable_and_has_no_absolute_paths(self) -> None:
        command = [sys.executable, str(REPOSITORY / "tools/glslcpp/check_corpus.py"), "--report"]
        first = subprocess.check_output(command, cwd="/tmp", text=True)
        second = subprocess.check_output(command, cwd="/tmp", text=True)
        self.assertEqual(first, second)
        self.assertNotIn(str(REPOSITORY), first)
        self.assertNotIn("timestamp", first.lower())
        self.assertEqual(167, json.loads(first)["counts"]["effects"])

    def test_frontend_reports_source_locations_and_rejects_bad_directives(self) -> None:
        from tools.glslcpp.frontend import FrontendError, parse_program

        program = parse_program("#version 300 es\nvoid main() { for (int i = 0; i < 2; ++i) {} }\n", "fixture")
        self.assertEqual("program", program["k"])
        with self.assertRaises(FrontendError) as context:
            parse_program("#if ???\n#endif\n", "bad")
        self.assertEqual(("bad", 1, 1), (context.exception.program_key, context.exception.line, context.exception.column))
        with self.assertRaisesRegex(FrontendError, "unconsumed or malformed token"):
            parse_program("void main() {} stray", "unconsumed")
        with self.assertRaises(FrontendError) as context:
            parse_program("\nvoid main() { @ }\n", "location")
        self.assertEqual(("location", 2, 15),
                         (context.exception.program_key, context.exception.line, context.exception.column))
        for key, source, line in (
            ("dangling", "#if 1\nvoid main() {}\n", 1),
            ("duplicate-else", "#if 1\n#else\n#else\n#endif\nvoid main() {}\n", 3),
        ):
            with self.subTest(key=key):
                with self.assertRaises(FrontendError) as context:
                    parse_program(source, key)
                self.assertEqual((key, line), (context.exception.program_key, context.exception.line))
        with self.assertRaisesRegex(FrontendError, "precision"):
            parse_program("precision nonsense whatever;\nvoid main() {}\n", "precision")

    def test_frontend_handles_the_full_admitted_syntax_shape(self) -> None:
        from tools.glslcpp.frontend import parse_program

        source = """
#version 300 es
#define COUNT 2
layout(std140) uniform Settings { mat3 basis; float values[COUNT]; } settings;
struct Item { vec3 color; int count; };
flat in vec2 uv;
out vec4 fragColor;
float helper(inout float value, out int count) { count = 0; return value; }
void main() {
  Item item; float value = 0.0; int count = 0;
  for (int i = 0; i < COUNT; ++i) { value += helper(value, count); }
  while (count < 1) { count++; }
  do { count--; } while (count > 0);
  item.color = vec3(value); fragColor = vec4(item.color.xy, value, 1.0);
  if (value > 0.0 ? true : false) { return; } else { discard; }
}
"""
        program = parse_program(source, "syntax")
        self.assertEqual(("fragColor",), program["outputs"])

    def test_fixture_sources_match_the_pinned_corpus(self) -> None:
        from tools.glslcpp import check_corpus

        manifest = json.loads((REPOSITORY / "tools/glslcpp/fixtures/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json").read_text())
        corpus = check_corpus._corpus_root(REPOSITORY)
        records = {record["program_key"]: record for record in check_corpus._validate_manifest(
            json.loads((corpus / "manifest.json").read_text()))}
        for fixture in manifest["programs"]:
            with self.subTest(fixture=fixture["program_key"]):
                record = records[fixture["program_key"]]
                self.assertEqual(
                    (REPOSITORY / "tools/glslcpp/fixtures/a024dc3a960cc44af454abc7aebce50456c194e6" / fixture["source"]).read_bytes(),
                    (corpus / record["source"]).read_bytes(),
                )

    def test_text_source_matches_the_pinned_coverage_provenance(self) -> None:
        """The canonical source is older than the current sibling working tree."""
        from tools.glslcpp import check_corpus

        source = check_corpus._corpus_root(REPOSITORY) / "sources/filter/text/text.glsl"
        content = source.read_bytes()
        self.assertEqual(1327, len(content))
        self.assertEqual("be62b513c1fb56f34d23ace109b76a525454f5a5dbac64239949d6faf16e7462",
                         hashlib.sha256(content).hexdigest())

    def test_validator_rejects_tampering_and_unsafe_records(self) -> None:
        from tools.glslcpp import check_corpus

        def mutate(root: pathlib.Path, callback) -> None:
            path = self.manifest_path(root)
            value = json.loads(path.read_text())
            callback(root, value)
            self.write_manifest(path, value)

        cases = {
            "raw": lambda root, value: (self.manifest_path(root).parent / next(iter(value["programs"]))["source"]).write_bytes(b"tampered"),
            "normalized": lambda root, value: value["programs"][0].__setitem__("normalized_sha256", "0" * 64),
            "duplicate": lambda root, value: value["programs"][1].__setitem__("program_key", value["programs"][0]["program_key"]),
            "duplicate-runtime-key": lambda root, value: value["programs"][1].__setitem__("runtime_key", value["programs"][0]["runtime_key"]),
            "duplicate-output": lambda root, value: value["programs"][0].__setitem__("outputs", ["fragColor", "fragColor"]),
            "traversal": lambda root, value: value["programs"][0].__setitem__("source", "sources/../outside.glsl"),
            "absolute": lambda root, value: value["programs"][0].__setitem__("source", "/outside.glsl"),
            "backslash": lambda root, value: value["programs"][0].__setitem__("source", "sources\\bad.glsl"),
            "colon": lambda root, value: value["programs"][0].__setitem__("source", "sources/C:bad.glsl"),
            "windows-device": lambda root, value: value["programs"][0].__setitem__("source", "sources/CON.glsl"),
            "adapter-drift": lambda root, value: value["programs"][0].__setitem__("status", "adapter"),
        }
        for name, callback in cases.items():
            with self.subTest(name=name), self.temporary_repository() as temporary:
                with self.assertRaises(check_corpus.CorpusError):
                    mutate(pathlib.Path(temporary), callback)
                    check_corpus.validate_corpus(pathlib.Path(temporary))

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            metadata_path = self.manifest_path(root).with_name("metadata.json")
            metadata = json.loads(metadata_path.read_text())
            del metadata["effects"][next(iter(metadata["effects"]))]
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(check_corpus.CorpusError, "hash mismatch"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            metadata_path = self.manifest_path(root).with_name("metadata.json")
            metadata = json.loads(metadata_path.read_text())
            del metadata["effects"]["filter/wormhole"]["passes"][1]
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            manifest_path = self.manifest_path(root)
            manifest = json.loads(manifest_path.read_text())
            manifest["metadata_sha256"] = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
            self.write_manifest(manifest_path, manifest)
            with self.assertRaisesRegex(check_corpus.CorpusError, "metadata pass relationship drift|draw-op override"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            source_root = self.manifest_path(root).parent / "sources"
            (source_root / "nested").mkdir()
            (source_root / "nested" / "extra.glsl").write_text("void main() {}", encoding="utf-8")
            with self.assertRaisesRegex(check_corpus.CorpusError, "file set drift"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            source = self.manifest_path(root).parent / "sources/classicNoisedeck/bitEffects/bitEffects.glsl"
            source.unlink()
            with self.assertRaisesRegex(check_corpus.CorpusError, "missing"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            source = self.manifest_path(root).parent / "sources/classicNoisedeck/bitEffects/bitEffects.glsl"
            replacement = source.with_name("replacement.glsl")
            replacement.write_text("void main() {}", encoding="utf-8")
            try:
                source.unlink()
                source.symlink_to(replacement)
            except (NotImplementedError, OSError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(check_corpus.CorpusError, "symlink"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            source_root = self.manifest_path(root).parent / "sources"
            linked = source_root / "linked"
            try:
                linked.symlink_to(source_root / "filter", target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(check_corpus.CorpusError, "symlink"):
                check_corpus.validate_corpus(root)

    def test_safe_path_accepts_ordinary_com10_and_reports_aggregate_failures(self) -> None:
        from tools.glslcpp import check_corpus

        root = check_corpus._corpus_root(REPOSITORY)
        self.assertEqual(root / "sources/COM10.glsl", check_corpus._safe_source_path(root, "sources/COM10.glsl", "safe"))
        with self.temporary_repository() as temporary:
            temporary_root = pathlib.Path(temporary)
            manifest = json.loads(self.manifest_path(temporary_root).read_text())
            corpus = self.manifest_path(temporary_root).parent
            first, second = manifest["programs"][:2]
            (corpus / first["source"]).write_bytes(b"one")
            (corpus / second["source"]).write_bytes(b"two")
            with self.assertRaises(check_corpus.CorpusError) as context:
                check_corpus.validate_corpus(temporary_root)
            self.assertIn(first["program_key"], str(context.exception))
            self.assertIn(second["program_key"], str(context.exception))

    def test_validator_rejects_noncanonical_json_and_corpus_top_level(self) -> None:
        from tools.glslcpp import check_corpus

        with tempfile.TemporaryDirectory() as temporary:
            duplicate = pathlib.Path(temporary) / "duplicate.json"
            duplicate.write_text('{"schema": 1, "schema": 1}', encoding="utf-8")
            with self.assertRaisesRegex(check_corpus.CorpusError, "duplicate JSON"):
                check_corpus._load_json(duplicate, "duplicate")

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            corpus = self.manifest_path(root).parent
            (corpus / "unexpected.txt").write_text("no", encoding="utf-8")
            with self.assertRaisesRegex(check_corpus.CorpusError, "top-level"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            corpus = self.manifest_path(root).parent
            manifest = corpus / "manifest.json"
            manifest.unlink()
            try:
                manifest.symlink_to("metadata.json")
            except (NotImplementedError, OSError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(check_corpus.CorpusError, "symlink"):
                check_corpus.validate_corpus(root)

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            path = self.manifest_path(root)
            manifest = json.loads(path.read_text())
            manifest["programs"][0]["source"] = manifest["programs"][0]["source"].replace("sources/", "sources//", 1)
            self.write_manifest(path, manifest)
            with self.assertRaisesRegex(check_corpus.CorpusError, "unsafe source path"):
                check_corpus.validate_corpus(root)


if __name__ == "__main__":
    unittest.main()
