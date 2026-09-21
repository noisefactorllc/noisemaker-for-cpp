"""Local verification runners must propagate failures to their callers."""

import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ResyncRunnerTests(unittest.TestCase):
    def run_suite(self, runner: str, failing: bool) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="resync-runner-") as temporary:
            root = pathlib.Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            (tests / "__init__.py").write_text("", encoding="utf-8")
            # Different modules exercise both shards. A successful last shard
            # must not erase the first shard's failure.
            for name, passes in (("first", not failing), ("last", True)):
                (tests / f"test_{name}.py").write_text(
                    "import unittest\n"
                    "class Case(unittest.TestCase):\n"
                    "    def test_result(self):\n"
                    f"        self.assertTrue({passes!r})\n",
                    encoding="utf-8",
                )
            if runner == "ci-local.sh":
                args = [str(root), str(root), str(root / "logs"), "python"]
            else:
                args = [str(root), "2", str(root / "shards")]
            return subprocess.run(
                ["bash", str(ROOT / "tools/resync" / runner), *args],
                capture_output=True, text=True, timeout=30,
            )

    def test_ci_local_propagates_test_failure(self):
        result = self.run_suite("ci-local.sh", failing=True)
        self.assertIn("FAIL python-suite", result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ci_local_returns_success_for_passing_tests(self):
        result = self.run_suite("ci-local.sh", failing=False)
        self.assertIn("PASS python-suite", result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pyshards_propagates_any_shard_failure(self):
        result = self.run_suite("pyshards.sh", failing=True)
        self.assertIn("status=1", result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pyshards_returns_success_when_all_shards_pass(self):
        result = self.run_suite("pyshards.sh", failing=False)
        self.assertIn("status=0", result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
