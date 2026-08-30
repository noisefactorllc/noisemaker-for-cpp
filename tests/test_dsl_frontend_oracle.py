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
COMPILER_EXPECTED_SHA256 = "1eb8d0bb28cebf13ab84eac9af3cf4c3d3616654c377b0e82c811142ef3b4958"
CPU_TOKENIZE_SHA256 = "83249cc23e612f6b2655ec2a1cdfcbdf1bbe83179793531b45c63fc8738f3cc2"


def require_cpu_root(test: unittest.TestCase) -> pathlib.Path:
    """Return the frozen CPU authority root, skipping when it is not supplied.

    The authority lives outside the repository at a machine-specific location,
    so it arrives by NOISEMAKER_CPU_ROOT and by nothing else. A checkout that
    does not have it cannot run this lane at all; skipping says that, whereas a
    failure would read as a parity defect that is not there.
    """
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value:
        test.skipTest("NOISEMAKER_CPU_ROOT must explicitly identify the frozen CPU authority")
    return pathlib.Path(value)


def resolve_cpp_oracle(candidates: list[pathlib.Path] | None = None) -> pathlib.Path:
    # The env var is NOISEMAKER_DSL_CPP_ORACLE, not the *_FRONTEND_ORACLE a
    # reader would guess. Resolution is env-only: there is no fallback search
    # path, because a resolver that reaches into a build tree it was not told
    # about serves a stale binary and turns this lane into a report on whatever
    # someone compiled last (a stale noisemaker-cpp-task3-build oracle is what
    # emitted `number:1e-07` here). Point it at a fresh external build.
    # `candidates` exists only so the regression test below can pin the
    # unset-env message; nothing populates it in normal use.
    configured = os.environ.get("NOISEMAKER_DSL_CPP_ORACLE")
    if configured is not None and configured != "":
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_CPP_ORACLE is not an executable file: {candidate}")
    for candidate in candidates or []:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise AssertionError("NOISEMAKER_DSL_CPP_ORACLE is unset and no documented external C++ oracle exists")


def resolve_parser_oracle() -> pathlib.Path:
    # Env-only for the same stale-binary reason as resolve_cpp_oracle.
    configured = os.environ.get("NOISEMAKER_DSL_PARSER_ORACLE")
    if configured:
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_PARSER_ORACLE is not an executable file: {candidate}")
    raise AssertionError("NOISEMAKER_DSL_PARSER_ORACLE is unset and no documented external C++ parser oracle exists")


def resolve_compiler_oracle() -> pathlib.Path:
    # Env-only for the same stale-binary reason as resolve_cpp_oracle.
    configured = os.environ.get("NOISEMAKER_DSL_COMPILER_ORACLE")
    if configured:
        candidate = pathlib.Path(configured)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise AssertionError(f"NOISEMAKER_DSL_COMPILER_ORACLE is not an executable file: {candidate}")
    raise AssertionError("NOISEMAKER_DSL_COMPILER_ORACLE is unset and no documented external C++ compiler oracle exists")


class DslFrontendOracleTest(unittest.TestCase):
    def test_catalog_registry_list_matches_locale_compare_census(self) -> None:
        cpu_root = require_cpu_root(self)
        node = shutil_which("node")
        cpp = resolve_compiler_oracle()
        js = subprocess.run([node, str(COMPILER_ORACLE_JS), "--compiler", "--list", "--cpu-root", str(cpu_root), "--fixtures", str(COMPILER_FIXTURES)], check=True, capture_output=True, text=True).stdout
        native = subprocess.run([str(cpp), "--list", "--mode", "catalog_records"], check=True, capture_output=True, text=True).stdout
        self.assertEqual(js, native)
        self.assertEqual(len(json.loads(js)), 205)

    def test_checked_compiler_stream_matches_node_cpp_and_is_deterministic(self) -> None:
        cpu_root = require_cpu_root(self)
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
        authority_root = require_cpu_root(self)
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
        authority_root = require_cpu_root(self)
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
        authority_root = require_cpu_root(self)
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
        cpu_root = require_cpu_root(self)
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

    def test_number_serialization_matches_node_at_toString_boundaries(self) -> None:
        """Pin ECMAScript `Number::toString` at the boundaries the streams can carry.

        Every expectation here is produced by Node at test time -- Leg A by the
        authoritative generator itself, Leg B by `String(value)` -- because the
        C++ side is the one that moves. The regression this covers is a C++
        serializer that formatted the exponent the way iostream does
        (`1e-07`, `1e+20`) instead of the way JavaScript does (`1e-7`,
        `100000000000000000000`), which is invisible to a corpus whose numbers
        all sit inside the plain-decimal window.

        The lexer, parser and compiler oracles now share one serializer
        (`noisemaker/js_number.hpp`), so Leg A's coverage of the non-finite and
        signed-zero spellings is the compiler oracle's coverage too; Leg B adds
        the signed finite values the lexer cannot produce as a single token.
        """
        cpu_root = require_cpu_root(self)
        node = shutil_which("node")
        self.assertIsNotNone(node)
        cpp = resolve_cpp_oracle()
        compiler = resolve_compiler_oracle()

        # Inputs only. Exponent-window edges (1e-7/1e-6 below, 1e20/1e21 above),
        # denormal and finite-range ends, 17-significant-digit round-tripping,
        # integers past 2^53, and the overflow/underflow literals that reach the
        # non-finite and zero spellings.
        literals = [
            "0", "1", "100", "0.1", "0.3", "1234.5678", "0.0001", "0.00001",
            "0.000001", "1e-6", "1e-7", "1e-5", "1e20", "1e21", "1e22",
            "5e-324", "2.2250738585072014e-308", "1.7976931348623157e308",
            "1.2345678901234567", "9007199254740993", "1000000000000000100",
            "123456789012345678901", "1e999", "1e-999",
        ]

        with tempfile.TemporaryDirectory(prefix="noisemaker-dsl-number-boundaries-") as temporary:
            fixtures_path = pathlib.Path(temporary) / "number-boundary-cases.json"
            fixtures = [{"name": literal, "source": literal} for literal in literals]
            fixtures_path.write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            authority_path = pathlib.Path(temporary) / "authority.txt"
            subprocess.run(
                [node, str(ORACLE_JS), "--cpu-root", str(cpu_root), "--fixtures", str(fixtures_path), "--output", str(authority_path)],
                check=True,
                text=True,
            )
            authority = authority_path.read_text(encoding="utf-8")

            # Leg A: the whole checked stream, generator against C++, per literal.
            cpp_records = []
            for fixture in fixtures:
                result = subprocess.run(
                    [str(cpp), "--name", fixture["name"], "--source", fixture["source"], "--source-name", fixture["name"]],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                cpp_records.append(result.stdout)
            self.assertEqual("".join(cpp_records), authority)

            # The generator must actually have exercised the spellings that
            # regressed; a silently emptied literal list would pass Leg A.
            tagged = {}
            for line in authority.splitlines():
                record = json.loads(line)
                number_tokens = [token for token in record["tokens"] if token["type"] == "number"]
                self.assertEqual(len(number_tokens), 1, record["name"])
                tagged[record["name"]] = number_tokens[0]["value"]
            self.assertEqual(tagged["1e-7"], "number:1e-7")
            self.assertEqual(tagged["1e-6"], "number:0.000001")
            self.assertEqual(tagged["1e20"], "number:100000000000000000000")
            self.assertEqual(tagged["1e21"], "number:1e+21")
            self.assertEqual(tagged["1e999"], "number:+Infinity")
            self.assertEqual(tagged["5e-324"], "number:5e-324")

        # Leg B: the compiler oracle's plan serializer, including signed values
        # the lexer emits as an operator plus a magnitude. `1e999` is dropped
        # here because the registry rejects a non-finite parameter before any
        # serializer runs -- Leg A already pins that spelling.
        signed = ["-1e-7", "-1e-6", "-1e20", "-1e21", "-0.1", "-1.2345678901234567", "-5e-324"]
        subjects = [literal for literal in literals if literal != "1e999"] + signed
        expectations = json.loads(subprocess.run(
            [node, "-e",
             "const values = JSON.parse(process.argv[1]);"
             "console.log(JSON.stringify(values.map((text) => `number:${String(Number(text))}`)))",
             "--", json.dumps(subjects)],
            check=True, capture_output=True, text=True).stdout)
        for literal, expected in zip(subjects, expectations):
            source = "search fixture\nalias(amount: " + literal + ").write(o0)\nrender(o0)"
            result = subprocess.run(
                [str(compiler), "--name", literal, "--mode", "custom", "--source-name", "boundaries.dsl", "--source", source],
                check=True, capture_output=True, text=True)
            record = json.loads(result.stdout)
            self.assertNotIn("error", record, f"{literal}: {result.stdout}")
            parameters = record["plan"]["chains"][0]["steps"][0]["params"]
            self.assertEqual([item["name"] for item in parameters], ["amount"], literal)
            self.assertEqual(parameters[0]["value"]["value"], expected, literal)

    def test_authority_rejects_forged_module_wrong_hash_and_symlinks(self) -> None:
        node = shutil_which("node")
        self.assertIsNotNone(node)
        authority_root = require_cpu_root(self)
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
