"""Exact C++/JavaScript lexer stream comparison.

The CPU root is deliberately an explicit input. This test never imports the
live repository checkout and never permits the oracle to rewrite fixtures.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/dsl/frontend-cases.json"
EXPECTED = ROOT / "tests/oracles/dsl_frontend_expected.txt"
ORACLE_JS = ROOT / "tools/dsl/js_frontend_oracle.mjs"
COMPILER_FIXTURES = ROOT / "tests/fixtures/dsl/compiler-cases.json"
COMPILER_EXPECTED = ROOT / "tests/oracles/dsl_compiler_expected.txt"
COMPILER_ORACLE_JS = ORACLE_JS
COMPILER_FIXTURES_SHA256 = "2cddd52470fe345cd70936141316aeae1ccf0b1d259bc23bb2bdc26c318828b6"
COMPILER_EXPECTED_SHA256 = "98bb63e7fd20c713c7abac076ba36f9cc8a397874febdd97bdb96bd7b63a8041"
CPU_TOKENIZE_SHA256 = "83249cc23e612f6b2655ec2a1cdfcbdf1bbe83179793531b45c63fc8738f3cc2"


def resolve_cpp_oracle(candidates: list[pathlib.Path] | None = None) -> pathlib.Path:
    configured = os.environ.get("NOISEMAKER_DSL_CPP_ORACLE")
    if configured is not None and configured != "":
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_CPP_ORACLE is not an executable file: {candidate}")
    search = candidates if candidates is not None else [
        pathlib.Path("/private/tmp/noisemaker-cpp-task3-build/noisemaker-dsl-frontend-oracle"),
        pathlib.Path("/private/tmp/noisemaker-cpp-dsl-build/noisemaker-dsl-frontend-oracle"),
    ]
    for candidate in search:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise AssertionError("NOISEMAKER_DSL_CPP_ORACLE is unset and no documented external C++ oracle exists")


def resolve_parser_oracle() -> pathlib.Path:
    configured = os.environ.get("NOISEMAKER_DSL_PARSER_ORACLE")
    if configured:
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_PARSER_ORACLE is not an executable file: {candidate}")
    candidates = [
        pathlib.Path("/private/tmp/noisemaker-cpp-dsl-build/noisemaker-dsl-parser-oracle"),
        pathlib.Path("/private/tmp/noisemaker-cpp-task4-build/noisemaker-dsl-parser-oracle"),
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise AssertionError("NOISEMAKER_DSL_PARSER_ORACLE is unset and no documented external C++ parser oracle exists")


def resolve_compiler_oracle() -> pathlib.Path:
    configured = os.environ.get("NOISEMAKER_DSL_COMPILER_ORACLE")
    if configured:
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_COMPILER_ORACLE is not an executable file: {candidate}")
    candidates = [
        pathlib.Path("/private/tmp/noisemaker-cpp-task5-build/noisemaker-dsl-compiler-oracle"),
        pathlib.Path("/private/tmp/noisemaker-cpp-dsl-build/noisemaker-dsl-compiler-oracle"),
        pathlib.Path("/private/tmp/noisemaker-cpp-continuation.e033lt/build-task5c/noisemaker-dsl-compiler-oracle"),
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise AssertionError("NOISEMAKER_DSL_COMPILER_ORACLE is unset and no documented external C++ compiler oracle exists")


class DslFrontendOracleTest(unittest.TestCase):
    def test_catalog_registry_list_matches_locale_compare_census(self) -> None:
        cpu_root = pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"])
        node = shutil_which("node")
        cpp = resolve_compiler_oracle()
        js = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--list", "--cpu-root", str(cpu_root), "--fixtures", str(COMPILER_FIXTURES)], check=True, capture_output=True, text=True).stdout
        native = subprocess.run([str(cpp), "--list", "--mode", "catalog_records"], check=True, capture_output=True, text=True).stdout
        self.assertEqual(js, native)
        self.assertEqual(len(json.loads(js)), 205)

    def test_checked_compiler_stream_matches_node_cpp_and_is_deterministic(self) -> None:
        cpu_root_value = os.environ.get("NOISEMAKER_CPU_ROOT")
        self.assertTrue(cpu_root_value, "NOISEMAKER_CPU_ROOT must explicitly identify the frozen CPU authority")
        cpu_root = pathlib.Path(cpu_root_value)
        self.assertTrue(cpu_root.is_absolute())
        node = shutil_which("node")
        self.assertIsNotNone(node)
        cpp = resolve_compiler_oracle()
        self.assertEqual(hash_file(COMPILER_FIXTURES), COMPILER_FIXTURES_SHA256)
        self.assertEqual(hash_file(COMPILER_EXPECTED), COMPILER_EXPECTED_SHA256)
        fixtures = json.loads(COMPILER_FIXTURES.read_text(encoding="utf-8"))
        expected = COMPILER_EXPECTED.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-compiler-oracle-") as temporary:
            first = pathlib.Path(temporary) / "first.txt"
            second = pathlib.Path(temporary) / "second.txt"
            for output in (first, second):
                subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--cpu-root", str(cpu_root), "--fixtures", str(COMPILER_FIXTURES), "--output", str(output), "--check", str(COMPILER_EXPECTED)], check=True)
            self.assertEqual(first.read_text(encoding="utf-8"), expected)
            self.assertEqual(second.read_text(encoding="utf-8"), expected)
            self.assertEqual(hash_file(first), hash_file(second))
            cpp_records = []
            for fixture in fixtures:
                args = [str(cpp), "--name", fixture["name"], "--mode", fixture["registryMode"], "--source-name", fixture["sourceName"], "--source", fixture["source"]]
                if fixture.get("options", {}).get("requireExecutable"):
                    args.append("--require-executable")
                result = subprocess.run(args, check=True, capture_output=True, text=True)
                cpp_records.append(result.stdout)
            self.assertEqual("".join(cpp_records), expected)

    def test_compiler_oracle_rejects_mutated_fixture_even_with_updated_inner_hashes(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        authority_root = pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"])
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-compiler-fixture-forge-") as temporary:
            forged = pathlib.Path(temporary) / "compiler-cases.json"
            records = json.loads(COMPILER_FIXTURES.read_text(encoding="utf-8"))
            records[0]["source"] = records[0]["source"].replace("fixture", "forged", 1)
            import hashlib
            records[0]["sourceSha256"] = hashlib.sha256(records[0]["source"].encode("utf-8")).hexdigest()
            forged.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--cpu-root", str(authority_root), "--fixtures", str(forged)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fixture corpus sha256", result.stderr)

    def test_compiler_oracle_rejects_mutated_expected_stream(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        authority_root = pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"])
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-compiler-expected-forge-") as temporary:
            forged = pathlib.Path(temporary) / "expected.txt"
            forged.write_text(COMPILER_EXPECTED.read_text(encoding="utf-8") + "forged\n", encoding="utf-8")
            result = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--cpu-root", str(authority_root), "--fixtures", str(COMPILER_FIXTURES), "--check", str(forged)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected stream sha256", result.stderr)

    def test_compiler_oracle_rejects_unsupported_update_mode(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        result = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--update"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--update is unsupported", result.stderr)

    def test_compiler_oracle_rejects_forged_transitive_module_before_import(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        authority_root = pathlib.Path(os.environ["NOISEMAKER_CPU_ROOT"])
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-compiler-forge-") as temporary:
            root = pathlib.Path(temporary) / "root"
            for relative in ("src/dsl/compiler.js", "src/dsl/error.js", "src/dsl/parser.js", "src/dsl/tokenize.js", "src/effects/definition.js", "src/effects/registry.js", "src/effects/generated/upstream-snapshot.js"):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(authority_root / relative, destination)
            marker = root / "forged-imported"
            definition = root / "src/effects/definition.js"
            definition.write_text("import fs from 'node:fs'\nfs.writeFileSync(" + json.dumps(str(marker)) + ", 'imported')\n", encoding="utf-8")
            result = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--cpu-root", os.path.realpath(root), "--fixtures", str(COMPILER_FIXTURES)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sha256", result.stderr)
            self.assertFalse(marker.exists())
    def test_checked_stream_matches_authoritative_node_oracle_and_cpp(self) -> None:
        cpu_root_value = os.environ.get("NOISEMAKER_CPU_ROOT")
        if not cpu_root_value:
            self.fail("NOISEMAKER_CPU_ROOT must explicitly identify the frozen CPU authority")
        cpu_root = pathlib.Path(cpu_root_value)
        self.assertTrue(cpu_root.is_absolute(), "NOISEMAKER_CPU_ROOT must be absolute")
        self.assertEqual(cpu_root, pathlib.Path(os.path.realpath(cpu_root)), "NOISEMAKER_CPU_ROOT must be a real path")
        tokenize_path = cpu_root / "src/dsl/tokenize.js"
        self.assertTrue(tokenize_path.is_file())
        self.assertEqual(hash_file(tokenize_path), CPU_TOKENIZE_SHA256)
        node = shutil_which("node")
        self.assertIsNotNone(node, "node is required for the authority oracle")
        cpp = resolve_cpp_oracle()
        parser_cpp = resolve_parser_oracle()

        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-oracle-") as temporary:
            generated = pathlib.Path(temporary) / "expected.txt"
            subprocess.run(
                [node, str(ORACLE_JS), "--cpu-root", str(cpu_root), "--fixtures", str(FIXTURES), "--output", str(generated)],
                check=True,
                text=True,
            )
            self.assertEqual(generated.read_text(encoding="utf-8"), EXPECTED.read_text(encoding="utf-8"))
            fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
            cpp_records = []
            for fixture in fixtures:
                oracle = parser_cpp if fixture.get("parse") else cpp
                result = subprocess.run(
                    [str(oracle), "--name", fixture["name"], "--source", fixture["source"], "--source-name", fixture.get("sourceName", fixture["name"])],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                cpp_records.append(result.stdout)
            self.assertEqual("".join(cpp_records), EXPECTED.read_text(encoding="utf-8"))

    def test_authority_rejects_forged_module_wrong_hash_and_symlinks(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        authority_root_value = os.environ.get("NOISEMAKER_CPU_ROOT")
        self.assertTrue(authority_root_value, "NOISEMAKER_CPU_ROOT must explicitly identify the frozen CPU authority")
        authority_root = pathlib.Path(authority_root_value)
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-authority-") as temporary:
            root = pathlib.Path(os.path.realpath(temporary)) / "root"
            module = root / "src/dsl/tokenize.js"
            module.parent.mkdir(parents=True)
            marker = root / "imported"
            module.write_text(
                "import fs from 'node:fs'\n"
                f"fs.writeFileSync({json.dumps(str(marker))}, 'imported')\n"
                "export function tokenizeDsl() { return [] }\n",
                encoding="utf-8",
            )
            args = [node, str(ORACLE_JS), "--cpu-root", str(root), "--fixtures", str(FIXTURES)]
            forged = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(forged.returncode, 0)
            self.assertIn("sha256", forged.stderr)
            self.assertFalse(marker.exists(), "forged authority was imported before authentication")

            parser_root = pathlib.Path(os.path.realpath(temporary)) / "parser-forge-root"
            parser_tokenize = parser_root / "src/dsl/tokenize.js"
            parser_path = parser_root / "src/dsl/parser.js"
            parser_tokenize.parent.mkdir(parents=True)
            shutil.copy2(authority_root / "src/dsl/tokenize.js", parser_tokenize)
            shutil.copy2(authority_root / "src/dsl/error.js", parser_root / "src/dsl/error.js")
            parser_marker = parser_root / "parser-imported"
            parser_path.write_text(
                "import fs from 'node:fs'\n"
                f"fs.writeFileSync({json.dumps(str(parser_marker))}, 'imported')\n"
                "export function parseDsl() { return {} }\n",
                encoding="utf-8",
            )
            parser_result = subprocess.run(
                [node, str(ORACLE_JS), "--cpu-root", str(parser_root), "--fixtures", str(FIXTURES)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(parser_result.returncode, 0)
            self.assertIn("sha256", parser_result.stderr)
            self.assertFalse(parser_marker.exists(), "forged parser was imported before authentication")

            real_root = pathlib.Path(os.path.realpath(temporary)) / "real-root"
            real_module = real_root / "src/dsl/tokenize.js"
            real_module.parent.mkdir(parents=True)
            shutil.copy2(authority_root / "src/dsl/tokenize.js", real_module)
            symlink_root = pathlib.Path(temporary) / "symlink-root"
            symlink_root.symlink_to(real_root, target_is_directory=True)
            root_result = subprocess.run([*args[:2], "--cpu-root", str(symlink_root), "--fixtures", str(FIXTURES)], capture_output=True, text=True)
            self.assertNotEqual(root_result.returncode, 0)
            self.assertIn("symlink", root_result.stderr)

            module.unlink()
            module.symlink_to(real_module)
            module_result = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(module_result.returncode, 0)
            self.assertIn("symlink", module_result.stderr)

            closure_root = pathlib.Path(os.path.realpath(temporary)) / "closure-root"
            closure_tokenize = closure_root / "src/dsl/tokenize.js"
            closure_error = closure_root / "src/dsl/error.js"
            closure_tokenize.parent.mkdir(parents=True)
            shutil.copy2(authority_root / "src/dsl/tokenize.js", closure_tokenize)
            closure_marker = closure_root / "error-imported"
            closure_error.write_text(
                "import fs from 'node:fs'\n"
                f"fs.writeFileSync({json.dumps(str(closure_marker))}, 'imported')\n"
                "export class DslError extends SyntaxError {}\n",
                encoding="utf-8",
            )
            closure_result = subprocess.run(
                [node, str(ORACLE_JS), "--cpu-root", str(closure_root), "--fixtures", str(FIXTURES)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(closure_result.returncode, 0)
            self.assertIn("src/dsl/error.js", closure_result.stderr)
            self.assertFalse(closure_marker.exists(), "forged transitive authority was imported before authentication")

    def test_cpp_oracle_fallback_rejects_missing_env_clearly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-no-oracle-") as temporary:
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("NOISEMAKER_DSL_CPP_ORACLE", None)
                with self.assertRaisesRegex(AssertionError, "no documented external C\\+\\+ oracle"):
                    resolve_cpp_oracle([pathlib.Path(temporary) / "missing"])

    def test_parser_oracle_rejects_configured_non_executable_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-parser-no-oracle-") as temporary:
            missing = pathlib.Path(temporary) / "missing"
            with mock.patch.dict(os.environ, {"NOISEMAKER_DSL_PARSER_ORACLE": str(missing)}, clear=False):
                with self.assertRaisesRegex(AssertionError, "NOISEMAKER_DSL_PARSER_ORACLE is not an executable file"):
                    resolve_parser_oracle()

    def test_compiler_oracle_rejects_configured_non_executable_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-compiler-no-oracle-") as temporary:
            missing = pathlib.Path(temporary) / "missing"
            with mock.patch.dict(os.environ, {"NOISEMAKER_DSL_COMPILER_ORACLE": str(missing)}, clear=False):
                with self.assertRaisesRegex(AssertionError, "NOISEMAKER_DSL_COMPILER_ORACLE is not an executable file"):
                    resolve_compiler_oracle()


def hash_file(path: pathlib.Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def shutil_which(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = pathlib.Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


if __name__ == "__main__":
    unittest.main()
