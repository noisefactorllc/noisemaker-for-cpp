"""Developer-only tests for deterministic GLSL-to-C++ generation."""

from __future__ import annotations

import pathlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from tools.glslcpp import generate_kernels
from tools.glslcpp.parser import GeneratorError, parse_program


class GeneratorTests(unittest.TestCase):
    def temporary_repository(self) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        shutil.copytree(REPOSITORY / "tools" / "glslcpp" / "fixtures",
                        root / "tools" / "glslcpp" / "fixtures")
        return temporary

    @staticmethod
    def fixture_manifest(root: pathlib.Path) -> pathlib.Path:
        return next((root / "tools" / "glslcpp" / "fixtures").glob("*/manifest.json"))

    @staticmethod
    def tree_bytes(root: pathlib.Path) -> dict[str, bytes]:
        return {str(path.relative_to(root)): path.read_bytes()
                for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()}

    def test_generation_is_repeatable_sorted_and_matches_committed_outputs(self) -> None:
        first = generate_kernels.generate_outputs(REPOSITORY)
        second = generate_kernels.generate_outputs(REPOSITORY)
        self.assertEqual(first, second)
        self.assertEqual(list(first), sorted(first))
        self.assertEqual(
            first["src/generated/synth_solid.cpp"],
            (REPOSITORY / "src/generated/synth_solid.cpp").read_bytes(),
        )
        self.assertEqual(
            first["src/generated/filter_invert.cpp"],
            (REPOSITORY / "src/generated/filter_invert.cpp").read_bytes(),
        )
        self.assertEqual(
            first["src/generated/manifest.json"],
            (REPOSITORY / "src/generated/manifest.json").read_bytes(),
        )

    def test_fixture_hash_rejection_and_unsupported_ast_errors_are_explicit(self) -> None:
        manifest = generate_kernels.load_fixture_manifest(REPOSITORY)
        entry = manifest["programs"][0]
        with self.assertRaisesRegex(GeneratorError, "fixture hash mismatch"):
            generate_kernels.verify_fixture_bytes(entry, b"not the pinned fixture")
        with self.assertRaisesRegex(GeneratorError, r"unsupported:1:.*unsupported call"):
            parse_program("void main() { unsupported(); }\n", "unsupported")

    def test_generated_sources_have_no_runtime_loader_or_nondeterministic_metadata(self) -> None:
        outputs = generate_kernels.generate_outputs(REPOSITORY)
        forbidden = ("UniformValue", "bindings.", "std::function", "Python", "Node", "/Users/", "timestamp")
        for path, source in outputs.items():
            if not path.endswith(".cpp"):
                continue
            text = source.decode("utf-8")
            pixel_body = text.split("void pixel", 1)[1].split("}  // namespace", 1)[0]
            for token in forbidden:
                self.assertNotIn(token, pixel_body)
            self.assertIn("struct State final", text)
            self.assertIn("const auto& state", pixel_body)
            if path.endswith("filter_invert.cpp"):
                self.assertIn("sample_texture", pixel_body)

    def test_legacy_texture_helper_stays_historical_and_delegates_to_runtime_seam(self) -> None:
        outputs = generate_kernels.generate_outputs(REPOSITORY)
        for name in ("filter_invert.cpp", "synth_solid.cpp"):
            text = outputs[f"src/generated/{name}"].decode("utf-8")
            helper = text.split("sample_texture", 1)[1].split("}", 1)[0]
            self.assertIn("sample_nearest_bottom_left", helper)
            self.assertNotIn("surface.filter()", helper)
            self.assertNotIn("sample_bilinear_bottom_left", helper)

    def test_manifest_output_paths_are_bare_unique_cpp_names_before_any_write(self) -> None:
        for invalid in ("../outside.cpp", "../../CMakeLists.txt", "nested\\outside.cpp",
                        "foo:bar.cpp", "CON.cpp", "NUL.cpp", "COM¹.cpp", "COM².cpp",
                        "COM³.cpp", "LPT¹.cpp", "LPT².cpp", "LPT³.cpp", "manifest.json"):
            with self.subTest(invalid=invalid), self.temporary_repository() as temporary:
                root = pathlib.Path(temporary)
                manifest_path = self.fixture_manifest(root)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["programs"][0]["output"] = invalid
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                before = self.tree_bytes(root)
                with self.assertRaisesRegex(GeneratorError, "output"):
                    generate_kernels.write_outputs(root)
                self.assertEqual(before, self.tree_bytes(root))
                self.assertFalse((root / "outside.cpp").exists())
                self.assertFalse((root / "CMakeLists.txt").exists())
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            manifest_path = self.fixture_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["programs"][0]["output"] = str(root / "absolute.cpp")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(GeneratorError, "output"):
                generate_kernels.write_outputs(root)
            self.assertFalse((root / "absolute.cpp").exists())
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            manifest_path = self.fixture_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["programs"][1]["output"] = manifest["programs"][0]["output"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(GeneratorError, "duplicate output"):
                generate_kernels.write_outputs(root)
            self.assertFalse((root / "src" / "generated").exists())

    def test_write_is_transactional_and_refuses_unexpected_existing_entries(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            generate_kernels.write_outputs(root)
            target = root / "src" / "generated"
            before = self.tree_bytes(target)
            real_replace = os.replace

            def fail_stage_swap(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
                if (pathlib.Path(source).name.startswith(".glslcpp-stage")
                        and pathlib.Path(destination).resolve() == target.resolve()):
                    raise OSError("injected stage swap failure")
                real_replace(source, destination)

            with mock.patch.object(generate_kernels.os, "replace", side_effect=fail_stage_swap):
                with self.assertRaisesRegex(OSError, "injected stage swap failure"):
                    generate_kernels.write_outputs(root)
            self.assertEqual(before, self.tree_bytes(target))

            (target / "user-note.txt").write_text("preserve me", encoding="utf-8")
            with self.assertRaisesRegex(GeneratorError, "file set drift"):
                generate_kernels.write_outputs(root)
            self.assertEqual(b"preserve me", (target / "user-note.txt").read_bytes())

        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            target = root / "src" / "generated"
            real_replace = os.replace

            def fail_new_stage_swap(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
                if (pathlib.Path(source).name.startswith(".glslcpp-stage")
                        and pathlib.Path(destination).resolve() == target.resolve()):
                    raise OSError("injected empty-target failure")
                real_replace(source, destination)

            with mock.patch.object(generate_kernels.os, "replace", side_effect=fail_new_stage_swap):
                with self.assertRaisesRegex(OSError, "injected empty-target failure"):
                    generate_kernels.write_outputs(root)
            self.assertFalse(target.exists())

    def test_check_rejects_nested_entries_and_symlinks(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            generate_kernels.write_outputs(root)
            target = root / "src" / "generated"
            nested = target / "nested"
            nested.mkdir()
            (nested / "extra.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(GeneratorError, "unexpected directory"):
                generate_kernels.check_outputs(root)
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            generate_kernels.write_outputs(root)
            target = root / "src" / "generated"
            link = target / "linked.cpp"
            try:
                link.symlink_to(target / "synth_solid.cpp")
            except (NotImplementedError, OSError):
                self.skipTest("symlink creation is unavailable")
            with self.assertRaisesRegex(GeneratorError, "symlink"):
                generate_kernels.check_outputs(root)

    def test_manifest_bindings_are_typed_authoritative_and_program_order_is_normalized(self) -> None:
        baseline = generate_kernels.generate_outputs(REPOSITORY)
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            manifest_path = self.fixture_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["programs"].reverse()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(baseline, generate_kernels.generate_outputs(root))
            for program in manifest["programs"]:
                program["pass_bindings"] = dict(reversed(list(program["pass_bindings"].items())))
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(baseline, generate_kernels.generate_outputs(root))
        for binding_name, binding_type in (("wrongName", "vec3"), ("color", "float")):
            with self.subTest(binding_name=binding_name, binding_type=binding_type), self.temporary_repository() as temporary:
                root = pathlib.Path(temporary)
                manifest_path = self.fixture_manifest(root)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["programs"][1]["pass_bindings"] = {binding_name: binding_type, "alpha": "float"}
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(GeneratorError, "pass bindings"):
                    generate_kernels.generate_outputs(root)


if __name__ == "__main__":
    unittest.main()
