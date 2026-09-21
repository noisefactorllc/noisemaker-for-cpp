"""Historical reconstruction audits require complete comparison evidence."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "tools/resync/reconstruction_audit.py"
PROGRAM = "filter/example:example"


class ReconstructionAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name)
        self.old = self.root / "old"
        self.new = self.root / "new"
        self.old.mkdir()
        self.new.mkdir()
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"programs": [{
            "program_key": PROGRAM,
            "raw_sha256": "a" * 64,
            "normalized_sha256": "b" * 64,
        }]}), encoding="utf-8")

    def entry(self, cache: pathlib.Path, name: str, *, indexed: bool = False,
              body: str = "void kernel() {}\n") -> None:
        directory = cache / name / "entry" if indexed else cache / name
        directory.mkdir(parents=True)
        (directory / "spec.json").write_text(json.dumps({
            "revision": cache.name,
            "programs": [{"program_key": PROGRAM}],
            "profile": name,
        }), encoding="utf-8")
        filename = "src__typed_generated__typed_slice.cpp"
        manifest_name = "src__typed_generated__typed_manifest.json"
        (directory / filename).write_text(
            f"// Typed IR program: {PROGRAM}\n{body}", encoding="utf-8")
        (directory / manifest_name).write_text(json.dumps({
            "programs": [{"program_key": PROGRAM}],
        }), encoding="utf-8")
        if indexed:
            (directory / "index.json").write_text(json.dumps({
                "src/typed_generated/typed_slice.cpp": filename,
                "src/typed_generated/typed_manifest.json": manifest_name,
            }), encoding="utf-8")

    def audit(self, *allowed: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.old), str(self.new),
             str(self.manifest), str(self.manifest), *allowed],
            check=False, text=True, capture_output=True,
        )

    def test_empty_caches_do_not_count_as_successful_audit(self) -> None:
        result = self.audit()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)

    def test_paired_specs_require_both_generated_artifacts(self) -> None:
        for missing in (("typed_slice.cpp", "typed_manifest.json"),
                        ("typed_slice.cpp",), ("typed_manifest.json",)):
            with self.subTest(missing=missing):
                for cache in (self.old, self.new):
                    self.entry(cache, "shared")
                    for name in missing:
                        (cache / "shared" / ("src__typed_generated__" + name)).unlink()
                result = self.audit(PROGRAM)
                for cache in (self.old, self.new):
                    for file in (cache / "shared").iterdir():
                        file.unlink()
                    (cache / "shared").rmdir()
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("missing reconstruction artifact", result.stdout)

    def test_disjoint_specs_do_not_count_as_successful_audit(self) -> None:
        self.entry(self.old, "before")
        self.entry(self.new, "after", indexed=True)
        result = self.audit()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("before", result.stdout)
        self.assertIn("after", result.stdout)

    def test_paired_spec_does_not_hide_missing_new_comparison(self) -> None:
        self.entry(self.old, "shared")
        self.entry(self.new, "shared")
        self.entry(self.old, "missing")
        result = self.audit(PROGRAM)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("missing", result.stdout)

    def test_paired_spec_does_not_hide_missing_old_comparison(self) -> None:
        self.entry(self.old, "shared")
        self.entry(self.new, "shared")
        self.entry(self.new, "missing")
        result = self.audit(PROGRAM)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("missing", result.stdout)

    def test_matching_specs_across_cache_layouts_and_revisions_pass(self) -> None:
        self.entry(self.old, "shared")
        self.entry(self.new, "shared", indexed=True)
        result = self.audit()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("paired=1", result.stdout)

    def test_explained_and_unexplained_artifact_changes_still_distinguish(self) -> None:
        self.entry(self.old, "shared")
        self.entry(self.new, "shared", body="void kernel() { changed(); }\n")
        unexplained = self.audit()
        self.assertEqual(1, unexplained.returncode, unexplained.stdout + unexplained.stderr)
        allowed = self.audit(PROGRAM)
        self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

    def test_allowed_last_program_does_not_hide_shared_factory_route_change(self) -> None:
        for cache, factory in ((self.old, "correct"), (self.new, "wrong")):
            self.entry(cache, "shared", body=(
                "namespace typed_0 {}\n"
                "namespace {\n"
                "constexpr std::array<KernelFactory, 1> kCatalog{{\n"
                f'    {{"{PROGRAM}", &{factory}}},\n'
                "}};\n}\n"))
        result = self.audit(PROGRAM)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("<tail>", result.stdout)

    def test_program_local_const_and_static_declarations_stay_in_program_block(self) -> None:
        for cache, value in ((self.old, "1"), (self.new, "2")):
            self.entry(cache, "shared", body=(
                "namespace typed_0 {\n"
                f"const float constant = {value};\n"
                f"static const int table[] = {{{value}}};\n"
                "}\n"
                "namespace {\n"
                "constexpr std::array<KernelFactory, 1> kCatalog{{\n"
                f'    {{"{PROGRAM}", &correct}},\n'
                "}};\n}\n"))
        result = self.audit(PROGRAM)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
