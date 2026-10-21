from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/run_partitioned_checks.py"


class PartitionedCheckTests(unittest.TestCase):
    def run_checks(self, *arguments: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run([sys.executable, str(RUNNER), *arguments],
                                capture_output=True, text=True, timeout=30, cwd=ROOT)
        records = [line.removeprefix("PARTITIONED_CHECKS ") for line in result.stdout.splitlines()
                   if line.startswith("PARTITIONED_CHECKS ")]
        return result, json.loads(records[-1]) if records else {}

    def python_fixture(self, root: pathlib.Path, *, failure: bool = False,
                       timeout: bool = False, skip: bool = False) -> None:
        for index in range(8):
            body = "time.sleep(0.04)"
            if index == 0 and failure:
                body = "self.fail('synthetic failure')"
            if index == 0 and timeout:
                body = "time.sleep(2)"
            decoration = "    @unittest.skip('synthetic skip')\n" if index == 0 and skip else ""
            (root / f"test_part_{index}.py").write_text(
                "import time, unittest\nclass Example(unittest.TestCase):\n" + decoration +
                "    def test_case(self):\n        " + body + "\n")

    def test_python_partitions_cover_each_discovered_id_once_with_two_children(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.python_fixture(pathlib.Path(directory))
            result, report = self.run_checks("python", "--start-directory", directory)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(report["success"])
        self.assertEqual(8, report["discovered_count"])
        self.assertEqual(8, len(report["partitions"]))
        self.assertEqual(2, report["peak_children"])
        actual = [item for row in report["partitions"] for item in row["executed_ids"]]
        self.assertEqual(sorted(report["discovered_ids"]), sorted(actual))
        self.assertEqual(len(actual), len(set(actual)))

    def test_python_failure_is_not_masked_by_complete_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.python_fixture(pathlib.Path(directory), failure=True)
            result, report = self.run_checks("python", "--start-directory", directory)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertFalse(report["success"])
        self.assertEqual(8, sum(len(row["executed_ids"]) for row in report["partitions"]))
        self.assertEqual(1, sum(row["failure_count"] for row in report["partitions"]))
        self.assertTrue(all(row["coverage_valid"] for row in report["partitions"]))

    def test_python_skip_remains_visible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.python_fixture(pathlib.Path(directory), skip=True)
            result, report = self.run_checks("python", "--start-directory", directory)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(1, sum(row["skip_count"] for row in report["partitions"]))
        self.assertEqual(8, sum(len(row["executed_ids"]) for row in report["partitions"]))

    def test_python_class_and_module_skip_account_for_unstarted_ids_without_pass_claims(self) -> None:
        for scope in ("class", "module"):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                setup = ("def setUpModule(): raise unittest.SkipTest('missing module input')\n"
                         if scope == "module" else "")
                class_setup = ("    @classmethod\n"
                               "    def setUpClass(cls): raise unittest.SkipTest('missing class input')\n"
                               if scope == "class" else "")
                (root / "test_skipped.py").write_text(
                    "import unittest\n" + setup + "class Example(unittest.TestCase):\n" +
                    class_setup + "    def test_a(self): self.fail('must remain unrun')\n"
                    "    def test_b(self): self.fail('must remain unrun')\n")
                result, report = self.run_checks("python", "--start-directory", directory,
                                                 "--partitions", "1")
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                row = report["partitions"][0]
                self.assertEqual([], row["executed_ids"])
                self.assertEqual(report["discovered_ids"], sorted(row["accounted_ids"]))
                self.assertEqual(report["discovered_ids"], sorted(row["skipped_ids"]))
                self.assertEqual(1, row["skip_count"])
                self.assertTrue(row["coverage_valid"])

    def test_python_timeout_is_failed_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            marker = root / "attempts"
            (root / "test_timeout.py").write_text(
                "import pathlib,time,unittest\nclass Example(unittest.TestCase):\n"
                "    def test_case(self):\n"
                f"        with pathlib.Path({str(marker)!r}).open('a') as f: f.write('run\\n')\n"
                "        time.sleep(2)\n")
            result, report = self.run_checks("python", "--start-directory", directory,
                                             "--timeout-seconds", "0.3")
            attempts = marker.read_text().splitlines()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertFalse(report["success"])
        self.assertEqual(["run"], attempts)
        self.assertEqual(1, sum(row["timed_out"] for row in report["partitions"]))

    def test_python_duplicate_discovery_fails_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            marker = root / "executed"
            (root / "test_duplicate.py").write_text(
                "import pathlib,unittest\nclass Example(unittest.TestCase):\n"
                f"    def test_case(self): pathlib.Path({str(marker)!r}).touch()\n"
                "def load_tests(loader, tests, pattern):\n"
                "    return unittest.TestSuite([Example('test_case'), Example('test_case')])\n")
            result, report = self.run_checks("python", "--start-directory", directory)
            self.assertFalse(marker.exists())
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(report["success"])
        self.assertIn("duplicate", report["error"])

    def native_fixture(self, root: pathlib.Path, behavior: str = "pass") -> pathlib.Path:
        executable = root / "native-fixture"
        executable.write_text(f"#!{sys.executable}\n" + textwrap.dedent(f"""
            import pathlib,sys
            ids=[f'case_{{n}}' for n in range(8)]
            if sys.argv[1:]==['--list-tests']:
                print('\\n'.join(ids))
                raise SystemExit(0)
            selected=pathlib.Path(sys.argv[2]).read_text().splitlines()
            for item in selected:
                if {behavior!r}=='missing': continue
                print(('FAIL ' if {behavior!r}=='fail' else 'PASS ')+item)
                if {behavior!r}=='duplicate': print('PASS '+item)
            raise SystemExit(1 if {behavior!r}=='fail' else 0)
        """))
        executable.chmod(0o700)
        return executable

    def test_native_partitions_preserve_every_id_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = self.native_fixture(pathlib.Path(directory))
            result, report = self.run_checks("native", "--executable", str(executable))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(8, report["discovered_count"])
        self.assertEqual(sorted(report["discovered_ids"]), sorted(
            item for row in report["partitions"] for item in row["executed_ids"]))

    def test_native_missing_duplicate_or_failed_result_cannot_pass(self) -> None:
        for behavior in ("missing", "duplicate", "fail"):
            with self.subTest(behavior=behavior), tempfile.TemporaryDirectory() as directory:
                executable = self.native_fixture(pathlib.Path(directory), behavior)
                result, report = self.run_checks("native", "--executable", str(executable))
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertFalse(report["success"])
                if behavior != "fail":
                    self.assertTrue(any(not row["coverage_valid"] for row in report["partitions"]))
                else:
                    self.assertTrue(all(row["coverage_valid"] for row in report["partitions"]))

    def test_bounds_reject_more_than_two_children_or_300_seconds(self) -> None:
        for option, value in (("--workers", "3"), ("--timeout-seconds", "301")):
            with self.subTest(option=option):
                result, _ = self.run_checks("python", option, value)
                self.assertNotEqual(0, result.returncode)


class NativeSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.directory.name)
        stub = cls.root / "stub.cpp"
        stub.write_text('#include "test_harness.hpp"\n'
                        'TEST(alpha) { std::cout << "RAN alpha\\n"; }\n'
                        'TEST(beta) { std::cout << "RAN beta\\n"; }\n')
        cls.binary = cls.root / "tests"
        result = subprocess.run([os.environ.get("CXX", "c++"), "-std=c++20",
                                 "-I" + str(ROOT / "tests"), str(ROOT / "tests/test_main.cpp"),
                                 str(stub), "-o", str(cls.binary)], capture_output=True,
                                text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(self.binary), *arguments], capture_output=True,
                              text=True, timeout=5)

    def test_listing_runs_no_case(self) -> None:
        result = self.invoke("--list-tests")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["alpha", "beta"], result.stdout.splitlines())

    def test_selected_id_runs_once_and_ordinary_interface_is_preserved(self) -> None:
        selected = self.root / "selected.txt"
        selected.write_text("beta\n")
        result = self.invoke("--test-ids-file", str(selected))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["RAN beta", "PASS beta"], result.stdout.splitlines())
        ordinary = self.invoke()
        self.assertEqual(0, ordinary.returncode, ordinary.stderr)
        self.assertEqual(["RAN alpha", "PASS alpha", "RAN beta", "PASS beta"],
                         ordinary.stdout.splitlines())

    def test_unknown_duplicate_empty_or_unsupported_selection_executes_nothing(self) -> None:
        for contents in ("unknown\n", "alpha\nalpha\n", ""):
            with self.subTest(contents=contents):
                selected = self.root / "invalid.txt"
                selected.write_text(contents)
                result = self.invoke("--test-ids-file", str(selected))
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn("RAN", result.stdout)
        result = self.invoke("--unknown")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("RAN", result.stdout)
