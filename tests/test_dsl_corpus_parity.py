"""Exact RGBA8 parity between the C++ executor and the pinned JS CPU authority.

Every admitted corpus record is rendered twice from the same authenticated
source bytes and the same options: once through the JavaScript authority
runner and once through the C++ driver. Comparison is zero tolerance -- the
shared comparer checks dimensions and length first, then every byte, and
reports the mismatch count, the first (x, y, channel), the maximum delta, and
both hashes.

A program the C++ executor refuses is not a pass. It is recorded against a
frozen expected-exclusion table with its exact structured reason, so a refusal
can never silently widen and a repaired program cannot silently stay excluded.
Nothing here ever rewrites the fixture or the exclusion table.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/dsl/executable-corpus.json"
CORPUS_ORACLE = ROOT / "tests/oracles/dsl_executable_corpus.sha256"
JS_RUNNER = ROOT / "tools/benchmark/run_cpu_case.mjs"
EXCLUSIONS = ROOT / "tests/oracles/dsl_corpus_parity_exclusions.json"

# Records are compared in bounded batches so a failing run reports a bounded,
# readable diagnostic rather than 166 buffers.
BATCH_SIZE = 16


def resolve_cpp_driver() -> pathlib.Path:
    configured = os.environ.get("NOISEMAKER_DSL_CPU_CASE")
    if not configured:
        raise unittest.SkipTest(
            "NOISEMAKER_DSL_CPU_CASE must point at the external noisemaker-dsl-cpu-case build")
    candidate = pathlib.Path(configured)
    if not (candidate.is_file() and os.access(candidate, os.X_OK)):
        raise AssertionError(f"NOISEMAKER_DSL_CPU_CASE is not an executable file: {candidate}")
    return candidate


def resolve_cpu_root() -> pathlib.Path:
    value = os.environ.get("NOISEMAKER_CPU_ROOT")
    if not value:
        raise unittest.SkipTest("NOISEMAKER_CPU_ROOT must identify the frozen CPU authority")
    root = pathlib.Path(value)
    if not root.is_absolute() or not root.is_dir():
        raise AssertionError("NOISEMAKER_CPU_ROOT must be an absolute directory")
    return root


def load_corpus() -> dict:
    """Load the corpus only through its own authenticated manifest digest."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    expected = CORPUS_ORACLE.read_text(encoding="utf-8").strip()
    if manifest["manifestSha256"] != expected:
        raise AssertionError(
            f"corpus manifest digest drift: {manifest['manifestSha256']} != {expected}")
    return manifest


class CorpusParityTest(unittest.TestCase):
    def test_every_dispatched_corpus_program_is_byte_exact(self) -> None:
        driver = resolve_cpp_driver()
        cpu_root = resolve_cpu_root()
        node = shutil.which("node")
        self.assertIsNotNone(node, "node is required for the authority runner")
        corpus = load_corpus()
        records = [item for item in corpus["records"] if item["recordKind"] == "admitted"]
        self.assertEqual(len(records), 166)
        expected_exclusions = json.loads(EXCLUSIONS.read_text(encoding="utf-8"))

        exact: list[str] = []
        refused: dict[str, str] = {}
        authority_refused: list[str] = []
        divergent: list[str] = []

        with tempfile.TemporaryDirectory(prefix="noisemaker-corpus-parity-") as temporary:
            scratch = pathlib.Path(temporary)
            for start in range(0, len(records), BATCH_SIZE):
                for record in records[start:start + BATCH_SIZE]:
                    name = record["effectId"]
                    source = scratch / "case.dsl"
                    source.write_text(record["source"], encoding="utf-8")
                    case = scratch / "case.json"
                    case.write_text(json.dumps(record), encoding="utf-8")
                    options = record["options"]

                    js_raw = scratch / "js.rgba8"
                    js_meta = scratch / "js.json"
                    js = subprocess.run(
                        [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case),
                         "--rgba8-output", str(js_raw), "--metadata-output", str(js_meta)],
                        capture_output=True, text=True)

                    # The C++ driver runs for every record, including the ones
                    # the authority refuses: a program the authority rejects
                    # while the executor happily renders bytes must not be
                    # filed away as "authority refused" and pass.
                    cpp_raw = scratch / "cpp.rgba8"
                    cpp_meta = scratch / "cpp.json"
                    cpp = subprocess.run(
                        [str(driver), "--source-file", str(source),
                         "--source-sha256", record["sourceSha256"],
                         "--width", str(options["width"]), "--height", str(options["height"]),
                         "--time", repr(options["time"]), "--frame", str(options["frame"]),
                         "--seed", repr(options["seed"]),
                         "--rgba8-output", str(cpp_raw), "--metadata-output", str(cpp_meta)],
                        capture_output=True, text=True)
                    cpp_detail = ""
                    if cpp.returncode != 0:
                        try:
                            cpp_detail = json.loads(cpp.stdout or "{}").get("detail", "")
                        except json.JSONDecodeError:
                            cpp_detail = (cpp.stdout or cpp.stderr).strip()[:200]

                    if js.returncode != 0:
                        authority_refused.append(name)
                        if cpp.returncode == 0:
                            divergent.append(
                                f"{name}\nthe authority refuses this program but the "
                                f"executor rendered bytes")
                        continue

                    if cpp.returncode != 0:
                        refused[name] = cpp_detail
                        continue

                    result = compare_rgba8(options["width"], options["height"],
                                           js_raw.read_bytes(), cpp_raw.read_bytes())
                    if result["ok"]:
                        exact.append(name)
                    else:
                        divergent.append(f"{name}\n{format_diagnostics(result)}")

        # A dispatched program must be byte-exact. There is no tolerance and no
        # allowance for a "close" render.
        self.assertEqual(divergent, [], "\n\n".join(divergent[:4]))

        # Refusals are frozen: the reason text and the exact membership both
        # have to match, in either direction.
        self.assertEqual(sorted(refused), sorted(expected_exclusions["executorRefused"]),
                         f"executor refusal set drift: {json.dumps(refused, indent=2, sort_keys=True)}")
        for name, detail in refused.items():
            self.assertEqual(detail, expected_exclusions["executorRefused"][name], name)
        self.assertEqual(sorted(authority_refused),
                         sorted(expected_exclusions["authorityRefused"]))

        self.assertEqual(
            len(exact) + len(refused) + len(authority_refused), len(records))
        self.assertEqual(len(exact), expected_exclusions["byteExactCount"])


if __name__ == "__main__":
    unittest.main()
